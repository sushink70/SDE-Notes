# Comprehensive Guide to Polymorphism in Object-Oriented Programming

## Table of Contents
1. [Introduction to Polymorphism](#introduction-to-polymorphism)
2. [Types of Polymorphism](#types-of-polymorphism)
3. [Python Implementation](#python-implementation)
4. [Rust Implementation](#rust-implementation)
5. [Comparison and Best Practices](#comparison-and-best-practices)

## Introduction to Polymorphism

Polymorphism is a fundamental concept in object-oriented programming that allows objects of different types to be treated as instances of the same type through a common interface. The word "polymorphism" comes from Greek, meaning "many forms."

### Key Benefits:
- **Code Reusability**: Write code that works with multiple types
- **Extensibility**: Add new types without modifying existing code
- **Maintainability**: Reduce code duplication and coupling
- **Flexibility**: Runtime behavior selection based on object type

## Types of Polymorphism

### 1. Runtime Polymorphism (Dynamic Dispatch)
- Method calls are resolved at runtime
- Achieved through inheritance and method overriding
- Also known as "late binding"

### 2. Compile-time Polymorphism (Static Dispatch)
- Method calls are resolved at compile time
- Achieved through method overloading and generics
- Also known as "early binding"

### 3. Parametric Polymorphism
- Functions/classes work with different types through generics
- Type parameters allow code to be generic over types

### 4. Ad-hoc Polymorphism
- Different implementations for different types
- Achieved through method overloading and type classes/traits

## Python Implementation

### Basic Inheritance and Method Overriding

```python
from abc import ABC, abstractmethod
import math

# Abstract base class defining the interface
class Shape(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def area(self) -> float:
        """Calculate the area of the shape"""
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        """Calculate the perimeter of the shape"""
        pass
    
    def display_info(self) -> str:
        """Common method for all shapes"""
        return f"{self.name}: Area = {self.area():.2f}, Perimeter = {self.perimeter():.2f}"

# Concrete implementations
class Circle(Shape):
    def __init__(self, radius: float):
        super().__init__("Circle")
        self.radius = radius
    
    def area(self) -> float:
        return math.pi * self.radius ** 2
    
    def perimeter(self) -> float:
        return 2 * math.pi * self.radius

class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        super().__init__("Rectangle")
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height
    
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

class Triangle(Shape):
    def __init__(self, a: float, b: float, c: float):
        super().__init__("Triangle")
        self.a = a
        self.b = b
        self.c = c
    
    def area(self) -> float:
        # Using Heron's formula
        s = (self.a + self.b + self.c) / 2
        return math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))
    
    def perimeter(self) -> float:
        return self.a + self.b + self.c

# Polymorphic function
def calculate_total_area(shapes: list[Shape]) -> float:
    """Calculate total area of all shapes - demonstrates polymorphism"""
    return sum(shape.area() for shape in shapes)

def print_shape_details(shapes: list[Shape]) -> None:
    """Print details of all shapes - demonstrates polymorphism"""
    for shape in shapes:
        print(shape.display_info())
```

### Duck Typing (Python's Unique Approach)

```python
# Duck typing - "If it walks like a duck and quacks like a duck, it's a duck"
class Duck:
    def make_sound(self):
        return "Quack!"
    
    def move(self):
        return "Waddles"

class Dog:
    def make_sound(self):
        return "Woof!"
    
    def move(self):
        return "Runs"

class Robot:
    def make_sound(self):
        return "Beep!"
    
    def move(self):
        return "Rolls"

def interact_with_entity(entity):
    """Works with any object that has make_sound() and move() methods"""
    print(f"Sound: {entity.make_sound()}")
    print(f"Movement: {entity.move()}")

# Usage example
entities = [Duck(), Dog(), Robot()]
for entity in entities:
    interact_with_entity(entity)
```

### Method Overloading Simulation

```python
from functools import singledispatch

# Python doesn't have built-in method overloading, but we can simulate it
class MathOperations:
    @singledispatch
    @staticmethod
    def add(x):
        raise NotImplementedError("Unsupported type")
    
    @add.register(int)
    @staticmethod
    def _(x: int, y: int = 0) -> int:
        return x + y
    
    @add.register(float)
    @staticmethod
    def _(x: float, y: float = 0.0) -> float:
        return x + y
    
    @add.register(str)
    @staticmethod
    def _(x: str, y: str = "") -> str:
        return x + y
    
    @add.register(list)
    @staticmethod
    def _(x: list, y: list = None) -> list:
        if y is None:
            y = []
        return x + y

# Generic function with type hints
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self):
        self._items: List[T] = []
    
    def add(self, item: T) -> None:
        self._items.append(item)
    
    def get_all(self) -> List[T]:
        return self._items.copy()
    
    def find(self, predicate) -> T | None:
        for item in self._items:
            if predicate(item):
                return item
        return None

# Usage examples
def demonstrate_python_polymorphism():
    print("=== Python Polymorphism Examples ===\n")
    
    # 1. Runtime polymorphism with shapes
    shapes = [
        Circle(5),
        Rectangle(4, 6),
        Triangle(3, 4, 5)
    ]
    
    print("Shape Details:")
    print_shape_details(shapes)
    print(f"\nTotal Area: {calculate_total_area(shapes):.2f}\n")
    
    # 2. Duck typing
    print("Duck Typing:")
    entities = [Duck(), Dog(), Robot()]
    for entity in entities:
        interact_with_entity(entity)
        print()
    
    # 3. Method overloading simulation
    print("Method Overloading Simulation:")
    print(f"add(5, 3) = {MathOperations.add(5, 3)}")
    print(f"add(2.5, 3.7) = {MathOperations.add(2.5, 3.7)}")
    print(f"add('Hello', ' World') = {MathOperations.add('Hello', ' World')}")
    print(f"add([1, 2], [3, 4]) = {MathOperations.add([1, 2], [3, 4])}")
    
    # 4. Generic containers
    print("\nGeneric Container:")
    int_container = Container[int]()
    int_container.add(1)
    int_container.add(2)
    int_container.add(3)
    print(f"Integer container: {int_container.get_all()}")
    
    str_container = Container[str]()
    str_container.add("hello")
    str_container.add("world")
    print(f"String container: {str_container.get_all()}")

if __name__ == "__main__":
    demonstrate_python_polymorphism()
```

## Rust Implementation

### Trait-based Polymorphism

```rust
use std::f64::consts::PI;

// Define a trait (similar to interface in other languages)
trait Shape {
    fn area(&self) -> f64;
    fn perimeter(&self) -> f64;
    fn name(&self) -> &str;
    
    // Default implementation
    fn display_info(&self) -> String {
        format!("{}: Area = {:.2}, Perimeter = {:.2}", 
                self.name(), self.area(), self.perimeter())
    }
}

// Concrete implementations
struct Circle {
    radius: f64,
}

impl Circle {
    fn new(radius: f64) -> Self {
        Circle { radius }
    }
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        PI * self.radius * self.radius
    }
    
    fn perimeter(&self) -> f64 {
        2.0 * PI * self.radius
    }
    
    fn name(&self) -> &str {
        "Circle"
    }
}

struct Rectangle {
    width: f64,
    height: f64,
}

impl Rectangle {
    fn new(width: f64, height: f64) -> Self {
        Rectangle { width, height }
    }
}

impl Shape for Rectangle {
    fn area(&self) -> f64 {
        self.width * self.height
    }
    
    fn perimeter(&self) -> f64 {
        2.0 * (self.width + self.height)
    }
    
    fn name(&self) -> &str {
        "Rectangle"
    }
}

struct Triangle {
    a: f64,
    b: f64,
    c: f64,
}

impl Triangle {
    fn new(a: f64, b: f64, c: f64) -> Self {
        Triangle { a, b, c }
    }
}

impl Shape for Triangle {
    fn area(&self) -> f64 {
        // Heron's formula
        let s = (self.a + self.b + self.c) / 2.0;
        (s * (s - self.a) * (s - self.b) * (s - self.c)).sqrt()
    }
    
    fn perimeter(&self) -> f64 {
        self.a + self.b + self.c
    }
    
    fn name(&self) -> &str {
        "Triangle"
    }
}

// Polymorphic functions using trait objects
fn calculate_total_area(shapes: &[Box<dyn Shape>]) -> f64 {
    shapes.iter().map(|shape| shape.area()).sum()
}

fn print_shape_details(shapes: &[Box<dyn Shape>]) {
    for shape in shapes {
        println!("{}", shape.display_info());
    }
}
```

### Generic Programming

```rust
use std::fmt::Display;
use std::ops::Add;

// Generic function with trait bounds
fn add_and_display<T>(a: T, b: T) -> T 
where 
    T: Add<Output = T> + Display + Copy 
{
    let result = a + b;
    println!("{} + {} = {}", a, b, result);
    result
}

// Generic struct
#[derive(Debug)]
struct Container<T> {
    items: Vec<T>,
}

impl<T> Container<T> {
    fn new() -> Self {
        Container {
            items: Vec::new(),
        }
    }
    
    fn add(&mut self, item: T) {
        self.items.push(item);
    }
    
    fn get_all(&self) -> &Vec<T> {
        &self.items
    }
    
    fn find<F>(&self, predicate: F) -> Option<&T>
    where
        F: Fn(&T) -> bool,
    {
        self.items.iter().find(|&item| predicate(item))
    }
}

// Trait for different animal behaviors
trait Animal {
    fn make_sound(&self) -> &str;
    fn move_style(&self) -> &str;
}

struct Dog;
struct Cat;
struct Bird;

impl Animal for Dog {
    fn make_sound(&self) -> &str { "Woof!" }
    fn move_style(&self) -> &str { "Runs" }
}

impl Animal for Cat {
    fn make_sound(&self) -> &str { "Meow!" }
    fn move_style(&self) -> &str { "Prowls" }
}

impl Animal for Bird {
    fn make_sound(&self) -> &str { "Tweet!" }
    fn move_style(&self) -> &str { "Flies" }
}

fn interact_with_animal(animal: &dyn Animal) {
    println!("Sound: {}", animal.make_sound());
    println!("Movement: {}", animal.move_style());
}
```

### Advanced Polymorphism with Enums

```rust
// Enum-based polymorphism (sum types)
#[derive(Debug)]
enum ShapeEnum {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
    Triangle { a: f64, b: f64, c: f64 },
}

impl ShapeEnum {
    fn area(&self) -> f64 {
        match self {
            ShapeEnum::Circle { radius } => PI * radius * radius,
            ShapeEnum::Rectangle { width, height } => width * height,
            ShapeEnum::Triangle { a, b, c } => {
                let s = (a + b + c) / 2.0;
                (s * (s - a) * (s - b) * (s - c)).sqrt()
            }
        }
    }
    
    fn perimeter(&self) -> f64 {
        match self {
            ShapeEnum::Circle { radius } => 2.0 * PI * radius,
            ShapeEnum::Rectangle { width, height } => 2.0 * (width + height),
            ShapeEnum::Triangle { a, b, c } => a + b + c,
        }
    }
    
    fn name(&self) -> &str {
        match self {
            ShapeEnum::Circle { .. } => "Circle",
            ShapeEnum::Rectangle { .. } => "Rectangle", 
            ShapeEnum::Triangle { .. } => "Triangle",
        }
    }
}

// Complete example function
fn demonstrate_rust_polymorphism() {
    println!("=== Rust Polymorphism Examples ===\n");
    
    // 1. Trait objects (dynamic dispatch)
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle::new(5.0)),
        Box::new(Rectangle::new(4.0, 6.0)),
        Box::new(Triangle::new(3.0, 4.0, 5.0)),
    ];
    
    println!("Shape Details (Dynamic Dispatch):");
    print_shape_details(&shapes);
    println!("Total Area: {:.2}\n", calculate_total_area(&shapes));
    
    // 2. Generic programming
    println!("Generic Programming:");
    add_and_display(5, 3);
    add_and_display(2.5, 3.7);
    add_and_display("Hello", " World");
    
    // 3. Generic containers
    println!("\nGeneric Container:");
    let mut int_container = Container::<i32>::new();
    int_container.add(1);
    int_container.add(2);
    int_container.add(3);
    println!("Integer container: {:?}", int_container.get_all());
    
    let mut str_container = Container::<String>::new();
    str_container.add("hello".to_string());
    str_container.add("world".to_string());
    println!("String container: {:?}", str_container.get_all());
    
    // 4. Animal traits
    println!("\nAnimal Behaviors:");
    let animals: Vec<Box<dyn Animal>> = vec![
        Box::new(Dog),
        Box::new(Cat),
        Box::new(Bird),
    ];
    
    for animal in &animals {
        interact_with_animal(animal.as_ref());
        println!();
    }
    
    // 5. Enum-based polymorphism (static dispatch)
    println!("Enum-based Polymorphism (Static Dispatch):");
    let enum_shapes = vec![
        ShapeEnum::Circle { radius: 5.0 },
        ShapeEnum::Rectangle { width: 4.0, height: 6.0 },
        ShapeEnum::Triangle { a: 3.0, b: 4.0, c: 5.0 },
    ];
    
    for shape in &enum_shapes {
        println!("{}: Area = {:.2}, Perimeter = {:.2}", 
                shape.name(), shape.area(), shape.perimeter());
    }
}

fn main() {
    demonstrate_rust_polymorphism();
}
```

## Comparison and Best Practices

### Python vs Rust Polymorphism

| Aspect | Python | Rust |
|--------|--------|------|
| **Type System** | Dynamic typing with optional hints | Static typing with inference |
| **Runtime Polymorphism** | Duck typing, inheritance | Trait objects (dyn Trait) |
| **Compile-time Polymorphism** | Limited (generics via typing) | Monomorphization, zero-cost |
| **Method Dispatch** | Always dynamic | Static by default, dynamic with trait objects |
| **Memory Safety** | Garbage collected | Zero-cost abstractions, ownership |
| **Performance** | Runtime overhead | Compile-time optimization |

### Best Practices

#### Python Best Practices
1. **Use Abstract Base Classes** for formal interfaces
2. **Leverage Duck Typing** for flexible APIs
3. **Type Hints** improve code clarity and IDE support
4. **Composition over Inheritance** when possible
5. **Use `@singledispatch`** for method overloading patterns

#### Rust Best Practices
1. **Prefer Static Dispatch** (generics) for performance
2. **Use Dynamic Dispatch** (trait objects) when needed for flexibility
3. **Enums for Sum Types** provide excellent pattern matching
4. **Trait Bounds** ensure type safety with generics
5. **Zero-Cost Abstractions** - abstractions shouldn't sacrifice performance

### When to Use Each Approach

#### Use Python When:
- Rapid prototyping is needed
- Duck typing provides sufficient flexibility
- Runtime introspection is valuable
- Development speed is prioritized

#### Use Rust When:
- Performance is critical
- Memory safety is paramount
- Compile-time guarantees are needed
- Systems programming is required

### Common Pitfalls and Solutions

#### Python Pitfalls:
- **Runtime Errors**: Type mismatches discovered at runtime
  - *Solution*: Use type hints and mypy
- **Performance**: Dynamic dispatch overhead
  - *Solution*: Profile and optimize hot paths
- **Method Resolution**: Complex inheritance hierarchies
  - *Solution*: Keep hierarchies simple, prefer composition

#### Rust Pitfalls:
- **Trait Object Limitations**: Not all traits can be objects
  - *Solution*: Design traits carefully, use associated types wisely
- **Lifetime Complexity**: Complex lifetime requirements
  - *Solution*: Simplify ownership patterns, use owned types when needed
- **Compilation Time**: Monomorphization can slow builds
  - *Solution*: Balance generics usage, consider dynamic dispatch for less critical paths

### Conclusion

Polymorphism is a powerful concept that both Python and Rust implement effectively, albeit with different approaches:

- **Python** emphasizes flexibility and ease of use through duck typing and dynamic features
- **Rust** prioritizes performance and safety through its trait system and compile-time optimizations

Understanding both approaches allows you to choose the right tool for your specific use case and leverage the strengths of each language's polymorphic features.

I'll create a comprehensive guide to polymorphism in object-oriented programming with complete implementations in both Python and Rust.I've created a comprehensive guide to polymorphism in object-oriented programming with complete implementations in both Python and Rust. The guide covers:

## Key Features:

**Conceptual Coverage:**
- Introduction to polymorphism and its benefits
- Four main types: runtime, compile-time, parametric, and ad-hoc polymorphism
- Detailed comparisons between Python and Rust approaches

**Python Implementation:**
- Abstract base classes and method overriding
- Duck typing (Python's unique strength)
- Method overloading simulation using `@singledispatch`
- Generic programming with TypeVar
- Complete working examples

**Rust Implementation:**
- Trait-based polymorphism (similar to interfaces)
- Generic programming with trait bounds
- Dynamic dispatch with trait objects (`dyn Trait`)
- Static dispatch with enums and pattern matching
- Zero-cost abstractions demonstration

**Practical Insights:**
- Side-by-side comparison table
- Best practices for each language
- When to use each approach
- Common pitfalls and their solutions

The implementations include real-world examples like geometric shapes, animal behaviors, and generic containers that demonstrate different polymorphic patterns. Each code example is fully functional and includes detailed comments explaining the concepts.

Would you like me to expand on any particular aspect of polymorphism or add more specific examples for certain use cases?

# Polymorphism in Rust and Python - Step by Step

## Overview: What is Polymorphism?
```
Polymorphism = "Many Forms"
┌─────────────────────────────────────────────────────────────┐
│ Same interface → Different implementations → Different behavior │
└─────────────────────────────────────────────────────────────┘
```

---

## PYTHON POLYMORPHISM (Duck Typing)

### Step 1: Define Different Classes with Same Method Names
```python
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   class Dog:    │    │   class Cat:    │    │  class Robot:   │
│                 │    │                 │    │                 │
│  def make_sound │    │  def make_sound │    │  def make_sound │
│      return     │    │      return     │    │      return     │
│      "Woof!"    │    │      "Meow!"    │    │     "Beep!"     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Step 2: Python's Duck Typing in Action
```
"If it walks like a duck and quacks like a duck, it's a duck"

┌─────────────────────────────────────────────────────────────┐
│ def animal_sound(creature):                                 │
│     return creature.make_sound()  # ← No type checking!    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Runtime Dispatch:                                           │
│                                                             │
│ dog = Dog()                                                 │
│ cat = Cat()                                                 │
│ robot = Robot()                                             │
│                                                             │
│ animal_sound(dog)    → "Woof!"                             │
│ animal_sound(cat)    → "Meow!"                             │
│ animal_sound(robot)  → "Beep!"                             │
└─────────────────────────────────────────────────────────────┘
```

### Step 3: Python Memory Model During Polymorphic Call
```
Memory Layout:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   dog object    │    │   cat object    │    │  robot object   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │__class__    │─┼────┼→│   Dog       │ │    │ │   Robot     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │make_sound() │ │    │ │make_sound() │ │    │ │make_sound() │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘

When animal_sound(creature) is called:
1. Python looks up creature.__class__
2. Finds the make_sound method in that class
3. Calls the appropriate implementation
```

---

## RUST POLYMORPHISM (Trait Objects)

### Step 1: Define a Common Trait
```rust
┌─────────────────────────────────────────────────────────────┐
│ trait MakeSound {                                           │
│     fn make_sound(&self) -> &'static str;                  │
│ }                                                           │
│                                                             │
│ ↑ This is the "contract" all types must implement          │
└─────────────────────────────────────────────────────────────┘
```

### Step 2: Implement Trait for Different Types
```rust
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ struct Dog;     │    │ struct Cat;     │    │ struct Robot;   │
│                 │    │                 │    │                 │
│ impl MakeSound  │    │ impl MakeSound  │    │ impl MakeSound  │
│ for Dog {       │    │ for Cat {       │    │ for Robot {     │
│   fn make_sound │    │   fn make_sound │    │   fn make_sound │
│   (&self) ->    │    │   (&self) ->    │    │   (&self) ->    │
│   &'static str  │    │   &'static str  │    │   &'static str  │
│   { "Woof!" }   │    │   { "Meow!" }   │    │   { "Beep!" }   │
│ }               │    │ }               │    │ }               │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Step 3: Using Trait Objects for Polymorphism
```rust
┌─────────────────────────────────────────────────────────────┐
│ fn animal_sound(creature: &dyn MakeSound) -> &'static str { │
│     creature.make_sound()                                   │
│ }                                                           │
│                                                             │
│ ↑ &dyn MakeSound = "any type that implements MakeSound"    │
└─────────────────────────────────────────────────────────────┘
```

### Step 4: Rust's vtable (Virtual Function Table) System
```
Compile Time: Rust creates vtables for each type

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dog vtable    │    │   Cat vtable    │    │  Robot vtable   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │make_sound   │ │    │ │make_sound   │ │    │ │make_sound   │ │
│ │   ptr ──────┼─┼────┼→│Dog::make_so─┼─┼────┼→│Robot::make_─┼ │
│ └─────────────┘ │    │ │und          │ │    │ │sound        │ │
│                 │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │                 │    │                 │
│ │drop_in_place│ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   ptr       │ │    │ │drop_in_place│ │    │ │drop_in_place│ │
│ └─────────────┘ │    │ │   ptr       │ │    │ │   ptr       │ │
│                 │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │                 │    │                 │
│ │size         │ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │align        │ │    │ │size         │ │    │ │size         │ │
│ └─────────────┘ │    │ │align        │ │    │ │align        │ │
└─────────────────┘    │ └─────────────┘ │    │ └─────────────┘ │
                       └─────────────────┘    └─────────────────┘

Runtime: Trait objects contain data pointer + vtable pointer

┌─────────────────────────────────────────────────────────────┐
│ &dyn MakeSound                                              │
│ ┌─────────────┐  ┌─────────────┐                          │
│ │ data_ptr ───┼──┼→ actual Dog │                          │
│ │             │  │  instance   │                          │
│ └─────────────┘  └─────────────┘                          │
│ ┌─────────────┐  ┌─────────────┐                          │
│ │ vtable_ptr ─┼──┼→ Dog vtable  │                          │
│ │             │  │             │                          │
│ └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Step 5: Runtime Dispatch Process
```
1. Function Call:
   animal_sound(&dog)
   
2. Trait Object Creation:
   ┌─────────────────┐
   │ &dyn MakeSound  │
   │ ┌─────────────┐ │    ┌─────────────┐
   │ │ data_ptr ───┼─┼────┼→ &dog       │
   │ └─────────────┘ │    └─────────────┘
   │ ┌─────────────┐ │    ┌─────────────┐
   │ │ vtable_ptr ─┼─┼────┼→ Dog vtable  │
   │ └─────────────┘ │    └─────────────┘
   └─────────────────┘

3. Method Call Resolution:
   creature.make_sound()
   ↓
   (*creature.vtable.make_sound)(creature.data_ptr)
   ↓
   Dog::make_sound(&dog) → "Woof!"
```

---

## KEY DIFFERENCES COMPARISON

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│      ASPECT         │       PYTHON        │        RUST         │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ Polymorphism Type   │ Duck Typing         │ Trait Objects       │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ Type Safety         │ Runtime checking    │ Compile-time safety │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ Performance         │ Slower (attribute   │ Fast (vtable        │
│                     │ lookup)             │ dispatch)           │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ Memory Overhead     │ Higher (object      │ Lower (just 2       │
│                     │ dictionaries)       │ pointers)           │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ Flexibility         │ Very flexible       │ More restrictive    │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ Error Detection     │ Runtime errors      │ Compile-time errors │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

## STEP-BY-STEP EXECUTION FLOW

### Python Execution:
```
Step 1: animal_sound(dog) called
         ↓
Step 2: Python interpreter looks up 'make_sound' attribute on dog object
         ↓
Step 3: Finds make_sound method in Dog class
         ↓
Step 4: Calls Dog.make_sound(dog)
         ↓
Step 5: Returns "Woof!"
```

### Rust Execution:
```
Step 1: animal_sound(&dog) called
         ↓
Step 2: Rust creates trait object &dyn MakeSound from &dog
         ↓
Step 3: Stores pointer to dog data + pointer to Dog's vtable
         ↓
Step 4: creature.make_sound() dereferences vtable pointer
         ↓
Step 5: Calls function pointer from vtable with data pointer
         ↓
Step 6: Returns "Woof!"
```

## Real-World Example Usage

### Python:
```python
def process_creatures(creatures):
    for creature in creatures:
        print(f"The creature says: {creature.make_sound()}")

# Works with any object that has make_sound method
creatures = [Dog(), Cat(), Robot(), Duck(), Alien()]
process_creatures(creatures)  # Duck typing magic!
```

### Rust:
```rust
fn process_creatures(creatures: Vec<Box<dyn MakeSound>>) {
    for creature in creatures {
        println!("The creature says: {}", creature.make_sound());
    }
}

// Only works with types that implement MakeSound trait
let creatures: Vec<Box<dyn MakeSound>> = vec![
    Box::new(Dog),
    Box::new(Cat), 
    Box::new(Robot),
];
process_creatures(creatures); // Trait-based polymorphism!
```

Both approaches achieve the same goal but with different trade-offs between flexibility, performance, and safety!

I'll create a detailed ASCII diagram showing how polymorphism works in both Rust and Python, with step-by-step explanations.This comprehensive ASCII diagram shows how polymorphism works in both Python and Rust, highlighting the key differences:

**Python's Duck Typing:**
- Uses dynamic attribute lookup at runtime
- Very flexible - any object with the right method works
- Runtime type checking and potential errors
- Higher memory overhead due to object dictionaries

**Rust's Trait Objects:**
- Uses compile-time trait bounds with runtime vtable dispatch
- Type-safe - only types implementing the trait can be used
- Faster execution with predictable performance
- Lower memory overhead with just two pointers per trait object

The diagram shows the step-by-step process for both languages, including how memory is organized and how method calls are resolved. Python's approach prioritizes flexibility and ease of use, while Rust's approach prioritizes performance and safety through compile-time guarantees.

Both achieve the same polymorphic behavior - calling the same method name on different types and getting type-specific behavior - but through very different mechanisms under the hood.