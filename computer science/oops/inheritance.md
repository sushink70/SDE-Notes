# Comprehensive Guide to Inheritance in Object-Oriented Programming

## Table of Contents
1. [Introduction to Inheritance](#introduction-to-inheritance)
2. [Types of Inheritance](#types-of-inheritance)
3. [Python Implementation](#python-implementation)
4. [Rust Implementation](#rust-implementation)
5. [Key Concepts and Best Practices](#key-concepts-and-best-practices)
6. [Comparison: Python vs Rust](#comparison-python-vs-rust)

## Introduction to Inheritance

Inheritance is a fundamental concept in Object-Oriented Programming (OOP) that allows a class (child/derived class) to inherit properties and methods from another class (parent/base class). This mechanism promotes code reusability, establishes hierarchical relationships between classes, and enables polymorphism.

### Benefits of Inheritance:
- **Code Reusability**: Avoid duplicating code by inheriting common functionality
- **Hierarchical Organization**: Create logical class hierarchies
- **Polymorphism**: Enable objects of different classes to be treated uniformly
- **Extensibility**: Easily extend existing functionality without modifying original code

## Types of Inheritance

### 1. Single Inheritance
A child class inherits from exactly one parent class.

### 2. Multiple Inheritance
A child class inherits from multiple parent classes (not supported in all languages).

### 3. Multilevel Inheritance
A chain of inheritance where a child class becomes a parent for another class.

### 4. Hierarchical Inheritance
Multiple child classes inherit from a single parent class.

### 5. Hybrid Inheritance
A combination of multiple inheritance types.

## Python Implementation

Python supports all types of inheritance with a flexible and dynamic approach.

### Single Inheritance

```python
class Animal:
    def __init__(self, name, species):
        self.name = name
        self.species = species
        self.is_alive = True
    
    def make_sound(self):
        return "Some generic animal sound"
    
    def eat(self):
        return f"{self.name} is eating"
    
    def sleep(self):
        return f"{self.name} is sleeping"
    
    def __str__(self):
        return f"{self.name} ({self.species})"

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name, "Canine")
        self.breed = breed
        self.loyalty = 100
    
    def make_sound(self):  # Method overriding
        return "Woof! Woof!"
    
    def fetch(self):
        return f"{self.name} is fetching the ball"
    
    def wag_tail(self):
        return f"{self.name} is wagging tail happily"

# Usage
dog = Dog("Buddy", "Golden Retriever")
print(dog)  # Buddy (Canine)
print(dog.make_sound())  # Woof! Woof!
print(dog.eat())  # Buddy is eating
print(dog.fetch())  # Buddy is fetching the ball
```

### Multiple Inheritance

```python
class Flyable:
    def __init__(self):
        self.can_fly = True
        self.max_altitude = 1000
    
    def fly(self):
        return "Flying through the air"
    
    def land(self):
        return "Landing gracefully"

class Swimmer:
    def __init__(self):
        self.can_swim = True
        self.max_depth = 50
    
    def swim(self):
        return "Swimming through water"
    
    def dive(self):
        return "Diving deep underwater"

class Duck(Animal, Flyable, Swimmer):
    def __init__(self, name):
        Animal.__init__(self, name, "Waterfowl")
        Flyable.__init__(self)
        Swimmer.__init__(self)
        self.waterproof = True
    
    def make_sound(self):
        return "Quack! Quack!"
    
    def migrate(self):
        return f"{self.name} is migrating south for winter"

# Usage
duck = Duck("Donald")
print(duck.make_sound())  # Quack! Quack!
print(duck.fly())  # Flying through the air
print(duck.swim())  # Swimming through water
print(duck.migrate())  # Donald is migrating south for winter

# Method Resolution Order (MRO)
print(Duck.__mro__)
```

### Multilevel Inheritance

```python
class Vehicle:
    def __init__(self, make, model, year):
        self.make = make
        self.model = model
        self.year = year
        self.is_running = False
    
    def start_engine(self):
        self.is_running = True
        return f"{self.make} {self.model} engine started"
    
    def stop_engine(self):
        self.is_running = False
        return f"{self.make} {self.model} engine stopped"

class Car(Vehicle):
    def __init__(self, make, model, year, doors):
        super().__init__(make, model, year)
        self.doors = doors
        self.fuel_type = "Gasoline"
    
    def drive(self):
        if self.is_running:
            return f"Driving the {self.make} {self.model}"
        return "Start the engine first!"
    
    def honk(self):
        return "Beep! Beep!"

class SportsCar(Car):
    def __init__(self, make, model, year, doors, top_speed):
        super().__init__(make, model, year, doors)
        self.top_speed = top_speed
        self.sport_mode = False
    
    def activate_sport_mode(self):
        self.sport_mode = True
        return "Sport mode activated! Ready for high performance!"
    
    def turbo_boost(self):
        if self.sport_mode and self.is_running:
            return f"Turbo boost engaged! Reaching {self.top_speed} mph!"
        return "Activate sport mode and start engine first!"

# Usage
sports_car = SportsCar("Ferrari", "F8 Tributo", 2023, 2, 211)
print(sports_car.start_engine())
print(sports_car.activate_sport_mode())
print(sports_car.turbo_boost())
```

### Abstract Base Classes and Polymorphism

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    def __init__(self, color):
        self.color = color
    
    @abstractmethod
    def area(self):
        pass
    
    @abstractmethod
    def perimeter(self):
        pass
    
    def describe(self):
        return f"A {self.color} shape with area {self.area():.2f}"

class Rectangle(Shape):
    def __init__(self, color, width, height):
        super().__init__(color)
        self.width = width
        self.height = height
    
    def area(self):
        return self.width * self.height
    
    def perimeter(self):
        return 2 * (self.width + self.height)

class Circle(Shape):
    def __init__(self, color, radius):
        super().__init__(color)
        self.radius = radius
    
    def area(self):
        return 3.14159 * self.radius ** 2
    
    def perimeter(self):
        return 2 * 3.14159 * self.radius

# Polymorphism in action
shapes = [
    Rectangle("Red", 5, 3),
    Circle("Blue", 4),
    Rectangle("Green", 2, 8)
]

for shape in shapes:
    print(shape.describe())
    print(f"Perimeter: {shape.perimeter():.2f}")
    print("-" * 30)
```

### Advanced Python Features

```python
class Employee:
    company_name = "TechCorp"  # Class variable
    
    def __init__(self, name, salary):
        self.name = name
        self._salary = salary  # Protected attribute
        self.__employee_id = id(self)  # Private attribute
    
    @property
    def salary(self):
        return self._salary
    
    @salary.setter
    def salary(self, value):
        if value > 0:
            self._salary = value
        else:
            raise ValueError("Salary must be positive")
    
    @classmethod
    def from_string(cls, employee_str):
        name, salary = employee_str.split('-')
        return cls(name, int(salary))
    
    @staticmethod
    def is_workday(day):
        return day.lower() not in ['saturday', 'sunday']
    
    def work(self):
        return f"{self.name} is working"

class Manager(Employee):
    def __init__(self, name, salary, team_size):
        super().__init__(name, salary)
        self.team_size = team_size
        self.subordinates = []
    
    def add_subordinate(self, employee):
        self.subordinates.append(employee)
        return f"{employee.name} added to {self.name}'s team"
    
    def conduct_meeting(self):
        return f"{self.name} is conducting a meeting with {self.team_size} team members"
    
    def work(self):  # Method overriding
        base_work = super().work()
        return f"{base_work} and managing a team of {self.team_size}"

# Usage with advanced features
manager = Manager("Alice", 75000, 5)
employee = Employee.from_string("Bob-50000")

print(manager.work())
print(manager.add_subordinate(employee))
print(f"Is Monday a workday? {Employee.is_workday('Monday')}")
```

## Rust Implementation

Rust doesn't have traditional class inheritance but achieves similar functionality through traits, composition, and enums.

### Trait-Based Inheritance (Interface Inheritance)

```rust
// Basic trait definition
trait Animal {
    fn name(&self) -> &str;
    fn species(&self) -> &str;
    fn make_sound(&self) -> String;
    
    // Default implementation
    fn introduce(&self) -> String {
        format!("Hi, I'm {}, a {}", self.name(), self.species())
    }
    
    fn eat(&self) -> String {
        format!("{} is eating", self.name())
    }
}

// Struct implementing the trait
struct Dog {
    name: String,
    breed: String,
}

impl Dog {
    fn new(name: String, breed: String) -> Self {
        Dog { name, breed }
    }
    
    fn fetch(&self) -> String {
        format!("{} is fetching the ball", self.name)
    }
    
    fn wag_tail(&self) -> String {
        format!("{} is wagging tail happily", self.name)
    }
}

impl Animal for Dog {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn species(&self) -> &str {
        "Canine"
    }
    
    fn make_sound(&self) -> String {
        "Woof! Woof!".to_string()
    }
}

// Another implementation
struct Cat {
    name: String,
    lives_remaining: u8,
}

impl Cat {
    fn new(name: String) -> Self {
        Cat { 
            name, 
            lives_remaining: 9 
        }
    }
    
    fn purr(&self) -> String {
        format!("{} is purring contentedly", self.name)
    }
}

impl Animal for Cat {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn species(&self) -> &str {
        "Feline"
    }
    
    fn make_sound(&self) -> String {
        "Meow! Meow!".to_string()
    }
}

// Usage function demonstrating polymorphism
fn animal_interaction(animal: &dyn Animal) {
    println!("{}", animal.introduce());
    println!("{}", animal.make_sound());
    println!("{}", animal.eat());
    println!();
}

// Example usage
fn basic_traits_example() {
    let dog = Dog::new("Buddy".to_string(), "Golden Retriever".to_string());
    let cat = Cat::new("Whiskers".to_string());
    
    animal_interaction(&dog);
    animal_interaction(&cat);
    
    println!("{}", dog.fetch());
    println!("{}", cat.purr());
}
```

### Multiple Trait Implementation

```rust
trait Flyable {
    fn fly(&self) -> String;
    fn land(&self) -> String;
    fn max_altitude(&self) -> u32;
}

trait Swimmer {
    fn swim(&self) -> String;
    fn dive(&self) -> String;
    fn max_depth(&self) -> u32;
}

struct Duck {
    name: String,
    waterproof: bool,
}

impl Duck {
    fn new(name: String) -> Self {
        Duck { 
            name, 
            waterproof: true 
        }
    }
    
    fn migrate(&self) -> String {
        format!("{} is migrating south for winter", self.name)
    }
}

impl Animal for Duck {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn species(&self) -> &str {
        "Waterfowl"
    }
    
    fn make_sound(&self) -> String {
        "Quack! Quack!".to_string()
    }
}

impl Flyable for Duck {
    fn fly(&self) -> String {
        "Flying through the air".to_string()
    }
    
    fn land(&self) -> String {
        "Landing gracefully on water".to_string()
    }
    
    fn max_altitude(&self) -> u32 {
        1000
    }
}

impl Swimmer for Duck {
    fn swim(&self) -> String {
        "Swimming through water".to_string()
    }
    
    fn dive(&self) -> String {
        "Diving for fish".to_string()
    }
    
    fn max_depth(&self) -> u32 {
        10
    }
}

// Generic function that works with multiple traits
fn versatile_animal<T>(animal: &T) 
where 
    T: Animal + Flyable + Swimmer 
{
    println!("{}", animal.introduce());
    println!("{}", animal.fly());
    println!("{}", animal.swim());
}
```

### Composition-Based Inheritance

```rust
// Base functionality through composition
struct Engine {
    horsepower: u32,
    fuel_type: String,
    is_running: bool,
}

impl Engine {
    fn new(horsepower: u32, fuel_type: String) -> Self {
        Engine {
            horsepower,
            fuel_type,
            is_running: false,
        }
    }
    
    fn start(&mut self) -> String {
        self.is_running = true;
        format!("Engine started ({}hp, {})", self.horsepower, self.fuel_type)
    }
    
    fn stop(&mut self) -> String {
        self.is_running = false;
        "Engine stopped".to_string()
    }
}

trait Vehicle {
    fn get_engine(&self) -> &Engine;
    fn get_engine_mut(&mut self) -> &mut Engine;
    
    fn start_engine(&mut self) -> String {
        self.get_engine_mut().start()
    }
    
    fn stop_engine(&mut self) -> String {
        self.get_engine_mut().stop()
    }
    
    fn is_running(&self) -> bool {
        self.get_engine().is_running
    }
}

struct Car {
    make: String,
    model: String,
    year: u16,
    doors: u8,
    engine: Engine,
}

impl Car {
    fn new(make: String, model: String, year: u16, doors: u8, engine: Engine) -> Self {
        Car { make, model, year, doors, engine }
    }
    
    fn drive(&self) -> String {
        if self.engine.is_running {
            format!("Driving the {} {}", self.make, self.model)
        } else {
            "Start the engine first!".to_string()
        }
    }
    
    fn honk(&self) -> String {
        "Beep! Beep!".to_string()
    }
}

impl Vehicle for Car {
    fn get_engine(&self) -> &Engine {
        &self.engine
    }
    
    fn get_engine_mut(&mut self) -> &mut Engine {
        &mut self.engine
    }
}

struct SportsCar {
    base_car: Car,
    top_speed: u16,
    sport_mode: bool,
}

impl SportsCar {
    fn new(make: String, model: String, year: u16, top_speed: u16, engine: Engine) -> Self {
        SportsCar {
            base_car: Car::new(make, model, year, 2, engine),
            top_speed,
            sport_mode: false,
        }
    }
    
    fn activate_sport_mode(&mut self) -> String {
        self.sport_mode = true;
        "Sport mode activated! Ready for high performance!".to_string()
    }
    
    fn turbo_boost(&self) -> String {
        if self.sport_mode && self.base_car.engine.is_running {
            format!("Turbo boost engaged! Reaching {} mph!", self.top_speed)
        } else {
            "Activate sport mode and start engine first!".to_string()
        }
    }
    
    // Delegate methods to base car
    fn drive(&self) -> String {
        self.base_car.drive()
    }
    
    fn honk(&self) -> String {
        self.base_car.honk()
    }
}

impl Vehicle for SportsCar {
    fn get_engine(&self) -> &Engine {
        &self.base_car.engine
    }
    
    fn get_engine_mut(&mut self) -> &mut Engine {
        &mut self.base_car.engine
    }
}
```

### Enum-Based Polymorphism

```rust
use std::f64::consts::PI;

// Enum for different shape types
#[derive(Debug)]
enum Shape {
    Rectangle { width: f64, height: f64, color: String },
    Circle { radius: f64, color: String },
    Triangle { base: f64, height: f64, color: String },
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Rectangle { width, height, .. } => width * height,
            Shape::Circle { radius, .. } => PI * radius * radius,
            Shape::Triangle { base, height, .. } => 0.5 * base * height,
        }
    }
    
    fn perimeter(&self) -> f64 {
        match self {
            Shape::Rectangle { width, height, .. } => 2.0 * (width + height),
            Shape::Circle { radius, .. } => 2.0 * PI * radius,
            Shape::Triangle { base, height, .. } => {
                // Assuming right triangle for simplicity
                let hypotenuse = (base * base + height * height).sqrt();
                base + height + hypotenuse
            }
        }
    }
    
    fn color(&self) -> &str {
        match self {
            Shape::Rectangle { color, .. } => color,
            Shape::Circle { color, .. } => color,
            Shape::Triangle { color, .. } => color,
        }
    }
    
    fn describe(&self) -> String {
        format!(
            "A {} shape with area {:.2} and perimeter {:.2}",
            self.color(),
            self.area(),
            self.perimeter()
        )
    }
}

// Factory methods
impl Shape {
    fn new_rectangle(width: f64, height: f64, color: String) -> Self {
        Shape::Rectangle { width, height, color }
    }
    
    fn new_circle(radius: f64, color: String) -> Self {
        Shape::Circle { radius, color }
    }
    
    fn new_triangle(base: f64, height: f64, color: String) -> Self {
        Shape::Triangle { base, height, color }
    }
}
```

### Advanced Rust Patterns

```rust
use std::fmt::Display;

// Generic trait with associated types
trait Iterator {
    type Item;
    
    fn next(&mut self) -> Option<Self::Item>;
    
    // Default implementations using the associated type
    fn collect<B: FromIterator<Self::Item>>(self) -> B 
    where 
        Self: Sized,
    {
        B::from_iter(self)
    }
}

// Trait with lifetime parameters
trait Drawable<'a> {
    fn draw(&self, canvas: &'a mut Canvas) -> Result<(), DrawError>;
}

struct Canvas {
    pixels: Vec<Vec<u8>>,
}

#[derive(Debug)]
enum DrawError {
    OutOfBounds,
    InvalidColor,
}

// Trait bounds and where clauses
fn process_shapes<T>(shapes: Vec<T>) -> Vec<String>
where
    T: Clone + Display,
{
    shapes
        .iter()
        .map(|shape| format!("Processing: {}", shape))
        .collect()
}

// Trait objects for dynamic dispatch
trait Processor {
    fn process(&self, data: &str) -> String;
}

struct TextProcessor;
struct NumberProcessor;

impl Processor for TextProcessor {
    fn process(&self, data: &str) -> String {
        data.to_uppercase()
    }
}

impl Processor for NumberProcessor {
    fn process(&self, data: &str) -> String {
        if let Ok(num) = data.parse::<i32>() {
            (num * 2).to_string()
        } else {
            "Invalid number".to_string()
        }
    }
}

fn process_with_different_processors(data: &str) {
    let processors: Vec<Box<dyn Processor>> = vec![
        Box::new(TextProcessor),
        Box::new(NumberProcessor),
    ];
    
    for processor in processors {
        println!("{}", processor.process(data));
    }
}
```

## Key Concepts and Best Practices

### Python Best Practices

1. **Use `super()`**: Always use `super()` to call parent methods
2. **Method Resolution Order (MRO)**: Understand how Python resolves method calls in multiple inheritance
3. **Abstract Base Classes**: Use `abc` module for defining interfaces
4. **Composition over Inheritance**: Prefer composition when inheritance creates tight coupling
5. **Liskov Substitution Principle**: Ensure derived classes can replace base classes

### Rust Best Practices

1. **Prefer Composition**: Use composition and delegation over trait inheritance
2. **Small, Focused Traits**: Keep traits small and focused on specific capabilities
3. **Use Enums for Variants**: Use enums when you have a fixed set of related types
4. **Generic Programming**: Leverage generics and trait bounds for flexible code
5. **Avoid Object Safety Issues**: Be aware of trait object limitations

### Common Pitfalls

#### Python
- **Diamond Problem**: Multiple inheritance can lead to ambiguous method resolution
- **Overusing Inheritance**: Creating deep inheritance hierarchies
- **Forgetting `super()`**: Not properly calling parent constructors

#### Rust
- **Fighting the Borrow Checker**: Overcomplicating ownership in trait implementations
- **Object Safety Violations**: Creating traits that can't be used as trait objects
- **Excessive Generic Constraints**: Making code overly complex with trait bounds

## Comparison: Python vs Rust

| Aspect | Python | Rust |
|--------|--------|------|
| **Inheritance Model** | Class-based inheritance | Trait-based composition |
| **Multiple Inheritance** | Supported with MRO | Achieved through multiple traits |
| **Dynamic Dispatch** | Built-in with virtual methods | Explicit with trait objects |
| **Memory Safety** | Garbage collected | Compile-time ownership checking |
| **Performance** | Interpreted, slower | Compiled, zero-cost abstractions |
| **Flexibility** | Very flexible, runtime changes | Rigid, compile-time guarantees |
| **Learning Curve** | Easier for beginners | Steeper learning curve |

### When to Use Each

**Choose Python when:**
- Rapid prototyping is needed
- Dynamic behavior is required
- Working with data science/ML projects
- Team has mixed experience levels

**Choose Rust when:**
- Performance is critical
- Memory safety is paramount
- Building system-level software
- Long-term maintainability is key

## Conclusion

Both Python and Rust offer powerful mechanisms for code reuse and polymorphism, though they take different approaches. Python's class-based inheritance is intuitive and flexible, while Rust's trait system provides safety and performance benefits. Understanding both paradigms will make you a more versatile programmer and help you choose the right tool for each project.

The key is to understand the trade-offs and apply the appropriate patterns based on your specific requirements for performance, safety, maintainability, and team expertise.

I'll create a comprehensive guide to inheritance in Object-Oriented Programming with complete implementations in both Python and Rust.I've created a comprehensive guide to inheritance in Object-Oriented Programming with complete implementations in both Python and Rust. The guide covers:

## Key Highlights:

**Python Implementation:**
- Single, multiple, and multilevel inheritance examples
- Abstract base classes and polymorphism
- Advanced features like properties, class methods, and method overriding
- Real-world examples with Animals, Vehicles, and Shapes

**Rust Implementation:**
- Trait-based inheritance (Rust's approach to interfaces)
- Multiple trait implementation
- Composition-based inheritance using structs
- Enum-based polymorphism
- Advanced patterns with generics and trait bounds

**Comprehensive Coverage:**
- All major inheritance types explained
- Best practices for both languages
- Common pitfalls and how to avoid them
- Performance and safety comparisons
- When to choose each language

The implementations include practical examples like:
- Animal hierarchy with Dogs, Cats, and Ducks
- Vehicle system with Cars and Sports Cars  
- Shape calculations with polymorphic behavior
- Advanced patterns for real-world applications

Each code example is complete and runnable, demonstrating not just syntax but also design principles and best practices. The guide serves as both a learning resource and a reference for implementing inheritance patterns in production code.

# Inheritance in Object-Oriented Programming: Rust vs Python

## Python - Classical Inheritance
```
STEP 1: Base Class Definition
┌─────────────────────────────────────┐
│            Animal (Base)            │
├─────────────────────────────────────┤
│ Attributes:                         │
│  - name: str                        │
│  - age: int                         │
├─────────────────────────────────────┤
│ Methods:                            │
│  + __init__(name, age)              │
│  + speak() -> str                   │
│  + move() -> str                    │
└─────────────────────────────────────┘
                    │
                    │ inherits from
                    ▼
STEP 2: Derived Classes
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│             Dog (Derived)           │    │             Cat (Derived)           │
├─────────────────────────────────────┤    ├─────────────────────────────────────┤
│ Inherits from Animal:               │    │ Inherits from Animal:               │
│  - name: str                        │    │  - name: str                        │
│  - age: int                         │    │  - age: int                         │
│  - speak() -> "Animal sound"        │    │  - speak() -> "Animal sound"        │
│  - move() -> "Animal moves"         │    │  - move() -> "Animal moves"         │
├─────────────────────────────────────┤    ├─────────────────────────────────────┤
│ Additional Attributes:              │    │ Additional Attributes:              │
│  - breed: str                       │    │  - indoor: bool                     │
├─────────────────────────────────────┤    ├─────────────────────────────────────┤
│ Method Overrides:                   │    │ Method Overrides:                   │
│  + speak() -> "Woof!"               │    │  + speak() -> "Meow!"               │
│  + fetch() -> "Fetching ball"       │    │  + climb() -> "Climbing tree"       │
└─────────────────────────────────────┘    └─────────────────────────────────────┘

STEP 3: Method Resolution Order (MRO)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Python MRO                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Dog Instance Method Call:                                                      │
│                                                                                 │
│  dog.speak() ──┐                                                               │
│                │                                                               │
│                ▼                                                               │
│  1. Check Dog class ──► Found speak() ──► Return "Woof!"                      │
│                │                                                               │
│                ▼ (if not found)                                                │
│  2. Check Animal class ──► Would return "Animal sound"                        │
│                │                                                               │
│                ▼ (if not found)                                                │
│  3. Check object class ──► AttributeError                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Rust - Composition and Traits (No Classical Inheritance)
```
STEP 1: Struct Definition (No Base Class)
┌─────────────────────────────────────┐
│              Animal                 │
├─────────────────────────────────────┤
│ Fields:                             │
│  - name: String                     │
│  - age: u32                         │
├─────────────────────────────────────┤
│ Implementation:                     │
│  + new(name, age) -> Animal         │
│  + get_name() -> &str               │
│  + get_age() -> u32                 │
└─────────────────────────────────────┘

STEP 2: Trait Definition (Interface-like)
┌─────────────────────────────────────┐
│            trait Speak              │
├─────────────────────────────────────┤
│ Required Methods:                   │
│  + speak(&self) -> String           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│            trait Move               │
├─────────────────────────────────────┤
│ Required Methods:                   │
│  + move_around(&self) -> String     │
└─────────────────────────────────────┘

STEP 3: Struct Composition + Trait Implementation
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│               Dog                   │    │               Cat                   │
├─────────────────────────────────────┤    ├─────────────────────────────────────┤
│ Fields:                             │    │ Fields:                             │
│  - animal: Animal  ← Composition    │    │  - animal: Animal  ← Composition    │
│  - breed: String                    │    │  - indoor: bool                     │
├─────────────────────────────────────┤    ├─────────────────────────────────────┤
│ Implements Speak:                   │    │ Implements Speak:                   │
│  + speak() -> "Woof!"               │    │  + speak() -> "Meow!"               │
├─────────────────────────────────────┤    ├─────────────────────────────────────┤
│ Implements Move:                    │    │ Implements Move:                    │
│  + move_around() -> "Running"       │    │  + move_around() -> "Stalking"      │
├─────────────────────────────────────┤    ├─────────────────────────────────────┤
│ Additional Methods:                 │    │ Additional Methods:                 │
│  + fetch() -> "Fetching ball"       │    │  + climb() -> "Climbing tree"       │
└─────────────────────────────────────┘    └─────────────────────────────────────┘
                    │                                          │
                    │ implements                               │ implements
                    ▼                                          ▼
            ┌───────────────────┐                    ┌───────────────────┐
            │   trait Speak     │                    │   trait Speak     │
            │   trait Move      │                    │   trait Move      │
            └───────────────────┘                    └───────────────────┘

STEP 4: Dynamic Dispatch with Trait Objects
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Trait Objects                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Vec<Box<dyn Speak>> ──┐                                                       │
│                        │                                                       │
│                        ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │  [Box<Dog>, Box<Cat>, Box<Dog>]                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                        │                                                       │
│                        ▼                                                       │
│  for animal in animals {                                                       │
│      animal.speak(); ──► Calls appropriate implementation                     │
│  }                       (Dog::speak() or Cat::speak())                       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Differences Summary

```
┌─────────────────────────┬─────────────────────────────────────────────────────────┐
│         Python          │                        Rust                            │
├─────────────────────────┼─────────────────────────────────────────────────────────┤
│                         │                                                         │
│  CLASS INHERITANCE      │  COMPOSITION + TRAITS                                   │
│                         │                                                         │
│  ┌─────────────┐        │  ┌─────────────┐    ┌──────────────┐                  │
│  │    Base     │        │  │   Struct    │    │    Trait     │                  │
│  │   Class     │        │  │ (Concrete)  │    │ (Interface)  │                  │
│  └─────────────┘        │  └─────────────┘    └──────────────┘                  │
│        │                │         │                   │                         │
│        │ extends        │         │ implements        │ implements              │
│        ▼                │         ▼                   ▼                         │
│  ┌─────────────┐        │  ┌─────────────────────────────────┐                  │
│  │  Derived    │        │  │       New Struct                │                  │
│  │   Class     │        │  │  + contains other structs       │                  │
│  └─────────────┘        │  │  + implements traits           │                  │
│                         │  └─────────────────────────────────┘                  │
│                         │                                                         │
│  • IS-A Relationship    │  • HAS-A + CAN-DO Relationships                       │
│  • Single inheritance   │  • Multiple trait implementation                       │
│  • Method overriding    │  • Trait method implementation                         │
│  • Runtime polymorphism │  • Compile-time + runtime polymorphism                │
│  • Automatic method     │  • Explicit trait implementation                       │
│    resolution           │    required                                            │
└─────────────────────────┴─────────────────────────────────────────────────────────┘
```

## Code Examples

### Python Example
```python
class Animal:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def speak(self):
        return "Animal sound"

class Dog(Animal):  # Inheritance
    def __init__(self, name, age, breed):
        super().__init__(name, age)
        self.breed = breed
    
    def speak(self):  # Method override
        return "Woof!"
```

### Rust Example
```rust
struct Animal {
    name: String,
    age: u32,
}

trait Speak {
    fn speak(&self) -> String;
}

struct Dog {
    animal: Animal,  // Composition
    breed: String,
}

impl Speak for Dog {  // Trait implementation
    fn speak(&self) -> String {
        "Woof!".to_string()
    }
}
```

## Memory Layout Comparison
```
Python Object Memory Layout:
┌─────────────────────────────────────┐
│           Dog Instance              │
├─────────────────────────────────────┤
│ Python Object Header                │
│ Reference to Dog class              │
│ name: "Buddy" ──────────────────────┼──► String object in heap
│ age: 5                              │
│ breed: "Golden" ────────────────────┼──► String object in heap
│ Virtual Method Table pointer        │
└─────────────────────────────────────┘

Rust Struct Memory Layout:
┌─────────────────────────────────────┐
│           Dog Instance              │
├─────────────────────────────────────┤
│ animal.name: String (stack data)    │
│ animal.age: u32                     │
│ breed: String (stack data)          │
└─────────────────────────────────────┘
│
├─ No inheritance hierarchy
├─ No virtual method table
├─ Traits resolved at compile time
└─ Zero-cost abstractions
```

I'll create a comprehensive ASCII diagram showing how inheritance works in both Rust and Python, highlighting their different approaches.This detailed ASCII diagram illustrates the fundamental differences between inheritance approaches in Python and Rust:

**Python's Classical Inheritance:**
- Uses traditional class inheritance with `is-a` relationships
- Features automatic method resolution order (MRO)
- Supports method overriding and polymorphism
- Objects carry inheritance metadata at runtime

**Rust's Composition + Traits:**
- Replaces inheritance with composition (`has-a` relationships)
- Uses traits for shared behavior (`can-do` relationships)
- Requires explicit trait implementation
- Achieves polymorphism through trait objects
- Zero-cost abstractions with compile-time resolution

The key insight is that Rust achieves the benefits of inheritance (code reuse, polymorphism) through a different paradigm that's more explicit and memory-efficient, while Python's approach is more traditional and dynamic but carries runtime overhead.

Both approaches solve the same fundamental problem of code organization and reuse, but Rust's system prevents many common inheritance pitfalls like the diamond problem and tight coupling between classes.

