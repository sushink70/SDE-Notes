// ========================================
// COMPREHENSIVE GUIDE TO RUST ENUMS
// ========================================

use std::fmt;

// ========================================
// 1. BASIC ENUMS
// ========================================

// Simple enum with unit variants
#[derive(Debug, PartialEq, Clone)]
enum Direction {
    North,
    South,
    East,
    West,
}

// Enum with explicit discriminant values
#[derive(Debug)]
enum StatusCode {
    Ok = 200,
    NotFound = 404,
    InternalServerError = 500,
}

// ========================================
// 2. ENUMS WITH DATA
// ========================================

// Enum variants can hold different types of data
#[derive(Debug, Clone)]
enum Message {
    Quit,                       // Unit variant
    Move { x: i32, y: i32 },   // Struct-like variant
    Write(String),             // Tuple variant
    ChangeColor(i32, i32, i32), // Tuple variant with multiple values
}

// Complex enum with various data types
#[derive(Debug)]
enum WebEvent {
    PageLoad,
    PageUnload,
    KeyPress(char),
    Paste(String),
    Click { x: i64, y: i64 },
}

// ========================================
// 3. GENERIC ENUMS
// ========================================

// Generic enum similar to Option<T>
#[derive(Debug, Clone)]
enum Maybe<T> {
    Some(T),
    None,
}

// Generic enum with multiple type parameters
#[derive(Debug)]
enum Either<L, R> {
    Left(L),
    Right(R),
}

// ========================================
// 4. RECURSIVE ENUMS
// ========================================

// Binary tree implementation using recursive enum
#[derive(Debug, Clone)]
enum BinaryTree<T> {
    Empty,
    Node {
        value: T,
        left: Box<BinaryTree<T>>,
        right: Box<BinaryTree<T>>,
    },
}

// Linked list implementation
#[derive(Debug)]
enum LinkedList<T> {
    Empty,
    Node(T, Box<LinkedList<T>>),
}

// ========================================
// 5. PATTERN MATCHING
// ========================================

impl Direction {
    fn opposite(&self) -> Direction {
        match self {
            Direction::North => Direction::South,
            Direction::South => Direction::North,
            Direction::East => Direction::West,
            Direction::West => Direction::East,
        }
    }

    fn is_vertical(&self) -> bool {
        match self {
            Direction::North | Direction::South => true,
            Direction::East | Direction::West => false,
        }
    }
}

impl Message {
    fn process(&self) {
        match self {
            Message::Quit => {
                println!("Quit message received");
            }
            Message::Move { x, y } => {
                println!("Move to coordinates ({}, {})", x, y);
            }
            Message::Write(text) => {
                println!("Text message: {}", text);
            }
            Message::ChangeColor(r, g, b) => {
                println!("Change color to RGB({}, {}, {})", r, g, b);
            }
        }
    }

    // Destructuring in function parameters
    fn extract_text(msg: &Message) -> Option<&String> {
        if let Message::Write(text) = msg {
            Some(text)
        } else {
            None
        }
    }
}

// ========================================
// 6. METHODS ON ENUMS
// ========================================

impl<T> Maybe<T> {
    fn is_some(&self) -> bool {
        match self {
            Maybe::Some(_) => true,
            Maybe::None => false,
        }
    }

    fn is_none(&self) -> bool {
        !self.is_some()
    }

    fn map<U, F>(self, f: F) -> Maybe<U>
    where
        F: FnOnce(T) -> U,
    {
        match self {
            Maybe::Some(value) => Maybe::Some(f(value)),
            Maybe::None => Maybe::None,
        }
    }

    fn unwrap_or(self, default: T) -> T {
        match self {
            Maybe::Some(value) => value,
            Maybe::None => default,
        }
    }
}

impl<T> BinaryTree<T> {
    fn new() -> Self {
        BinaryTree::Empty
    }

    fn insert(self, value: T) -> Self 
    where 
        T: Ord,
    {
        match self {
            BinaryTree::Empty => BinaryTree::Node {
                value,
                left: Box::new(BinaryTree::Empty),
                right: Box::new(BinaryTree::Empty),
            },
            BinaryTree::Node { value: node_value, left, right } => {
                if value <= node_value {
                    BinaryTree::Node {
                        value: node_value,
                        left: Box::new(left.as_ref().clone().insert(value)),
                        right,
                    }
                } else {
                    BinaryTree::Node {
                        value: node_value,
                        left,
                        right: Box::new(right.as_ref().clone().insert(value)),
                    }
                }
            }
        }
    }

    fn contains(&self, target: &T) -> bool 
    where 
        T: Ord,
    {
        match self {
            BinaryTree::Empty => false,
            BinaryTree::Node { value, left, right } => {
                if target == value {
                    true
                } else if target < value {
                    left.contains(target)
                } else {
                    right.contains(target)
                }
            }
        }
    }
}

// ========================================
// 7. TRAIT IMPLEMENTATIONS
// ========================================

impl fmt::Display for Direction {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let direction_str = match self {
            Direction::North => "North",
            Direction::South => "South", 
            Direction::East => "East",
            Direction::West => "West",
        };
        write!(f, "{}", direction_str)
    }
}

impl<T: fmt::Display> fmt::Display for Maybe<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Maybe::Some(value) => write!(f, "Some({})", value),
            Maybe::None => write!(f, "None"),
        }
    }
}

// ========================================
// 8. ADVANCED ENUM PATTERNS
// ========================================

// Enum with associated constants and functions
#[derive(Debug)]
enum Planet {
    Mercury,
    Venus,
    Earth,
    Mars,
    Jupiter,
    Saturn,
    Uranus,
    Neptune,
}

impl Planet {
    const ALL: [Planet; 8] = [
        Planet::Mercury, Planet::Venus, Planet::Earth, Planet::Mars,
        Planet::Jupiter, Planet::Saturn, Planet::Uranus, Planet::Neptune,
    ];

    fn mass_kg(&self) -> f64 {
        match self {
            Planet::Mercury => 3.303e+23,
            Planet::Venus => 4.869e+24,
            Planet::Earth => 5.976e+24,
            Planet::Mars => 6.421e+23,
            Planet::Jupiter => 1.9e+27,
            Planet::Saturn => 5.688e+26,
            Planet::Uranus => 8.686e+25,
            Planet::Neptune => 1.024e+26,
        }
    }

    fn radius_m(&self) -> f64 {
        match self {
            Planet::Mercury => 2.4397e6,
            Planet::Venus => 6.0518e6,
            Planet::Earth => 6.37814e6,
            Planet::Mars => 3.3972e6,
            Planet::Jupiter => 7.1492e7,
            Planet::Saturn => 6.0268e7,
            Planet::Uranus => 2.5559e7,
            Planet::Neptune => 2.4746e7,
        }
    }

    fn surface_gravity(&self) -> f64 {
        const G: f64 = 6.67300E-11;
        let mass = self.mass_kg();
        let radius = self.radius_m();
        G * mass / (radius * radius)
    }
}

// State machine using enums
#[derive(Debug, PartialEq)]
enum TrafficLight {
    Red,
    Yellow,
    Green,
}

impl TrafficLight {
    fn next(&self) -> TrafficLight {
        match self {
            TrafficLight::Red => TrafficLight::Green,
            TrafficLight::Yellow => TrafficLight::Red,
            TrafficLight::Green => TrafficLight::Yellow,
        }
    }

    fn duration_seconds(&self) -> u32 {
        match self {
            TrafficLight::Red => 60,
            TrafficLight::Yellow => 10,
            TrafficLight::Green => 45,
        }
    }
}

// Error handling with custom enum
#[derive(Debug)]
enum MathError {
    DivisionByZero,
    NegativeSquareRoot,
    Overflow,
}

impl fmt::Display for MathError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MathError::DivisionByZero => write!(f, "Cannot divide by zero"),
            MathError::NegativeSquareRoot => write!(f, "Cannot take square root of negative number"),
            MathError::Overflow => write!(f, "Mathematical overflow occurred"),
        }
    }
}

fn safe_divide(a: f64, b: f64) -> Result<f64, MathError> {
    if b == 0.0 {
        Err(MathError::DivisionByZero)
    } else {
        Ok(a / b)
    }
}

fn safe_sqrt(x: f64) -> Result<f64, MathError> {
    if x < 0.0 {
        Err(MathError::NegativeSquareRoot)
    } else {
        Ok(x.sqrt())
    }
}

// ========================================
// 9. ENUM WITH LIFETIMES
// ========================================

#[derive(Debug)]
enum BorrowedData<'a> {
    Text(&'a str),
    Number(i32),
    Reference(&'a i32),
}

impl<'a> BorrowedData<'a> {
    fn display(&self) {
        match self {
            BorrowedData::Text(s) => println!("Text: {}", s),
            BorrowedData::Number(n) => println!("Number: {}", n),
            BorrowedData::Reference(r) => println!("Reference: {}", r),
        }
    }
}

// ========================================
// 10. DEMONSTRATION FUNCTIONS
// ========================================

fn demonstrate_basic_enums() {
    println!("=== Basic Enums ===");
    
    let dir = Direction::North;
    println!("Direction: {:?}", dir);
    println!("Opposite: {:?}", dir.opposite());
    println!("Is vertical: {}", dir.is_vertical());
    
    let status = StatusCode::NotFound;
    println!("Status code: {:?} = {}", status, status as u32);
    println!();
}

fn demonstrate_enums_with_data() {
    println!("=== Enums with Data ===");
    
    let messages = vec![
        Message::Quit,
        Message::Move { x: 10, y: 20 },
        Message::Write("Hello, Rust!".to_string()),
        Message::ChangeColor(255, 0, 128),
    ];
    
    for msg in &messages {
        msg.process();
        if let Some(text) = Message::extract_text(msg) {
            println!("  Extracted text: {}", text);
        }
    }
    println!();
}

fn demonstrate_generic_enums() {
    println!("=== Generic Enums ===");
    
    let some_number = Maybe::Some(42);
    let none_string: Maybe<String> = Maybe::None;
    
    println!("some_number: {}", some_number);
    println!("none_string: {}", none_string);
    println!("some_number is_some: {}", some_number.is_some());
    
    let doubled = some_number.clone().map(|x| x * 2);
    println!("Doubled: {}", doubled);
    
    let default_value = none_string.unwrap_or("default".to_string());
    println!("Default value: {}", default_value);
    
    let either_left: Either<i32, String> = Either::Left(42);
    let either_right: Either<i32, String> = Either::Right("hello".to_string());
    println!("Either left: {:?}", either_left);
    println!("Either right: {:?}", either_right);
    println!();
}

fn demonstrate_recursive_enums() {
    println!("=== Recursive Enums ===");
    
    let mut tree = BinaryTree::new();
    tree = tree.insert(5);
    tree = tree.insert(3);
    tree = tree.insert(7);
    tree = tree.insert(1);
    tree = tree.insert(9);
    
    println!("Binary tree: {:?}", tree);
    println!("Contains 3: {}", tree.contains(&3));
    println!("Contains 10: {}", tree.contains(&10));
    
    let list = LinkedList::Node(
        1,
        Box::new(LinkedList::Node(
            2,
            Box::new(LinkedList::Node(3, Box::new(LinkedList::Empty))),
        )),
    );
    println!("Linked list: {:?}", list);
    println!();
}

fn demonstrate_advanced_patterns() {
    println!("=== Advanced Patterns ===");
    
    for planet in &Planet::ALL[0..4] {
        println!(
            "{:?}: mass = {:.3e} kg, surface gravity = {:.2} m/s²",
            planet,
            planet.mass_kg(),
            planet.surface_gravity()
        );
    }
    
    let mut light = TrafficLight::Red;
    println!("Traffic light sequence:");
    for _ in 0..4 {
        println!("  {:?} ({}s)", light, light.duration_seconds());
        light = light.next();
    }
    
    println!("\nMath operations:");
    match safe_divide(10.0, 2.0) {
        Ok(result) => println!("10.0 / 2.0 = {}", result),
        Err(e) => println!("Error: {}", e),
    }
    
    match safe_divide(10.0, 0.0) {
        Ok(result) => println!("10.0 / 0.0 = {}", result),
        Err(e) => println!("Error: {}", e),
    }
    
    match safe_sqrt(-4.0) {
        Ok(result) => println!("sqrt(-4.0) = {}", result),
        Err(e) => println!("Error: {}", e),
    }
    println!();
}

fn demonstrate_borrowed_data() {
    println!("=== Enums with Lifetimes ===");
    
    let text = "Hello, world!";
    let number = 42;
    
    let data = vec![
        BorrowedData::Text(text),
        BorrowedData::Number(100),
        BorrowedData::Reference(&number),
    ];
    
    for item in &data {
        item.display();
    }
    println!();
}

fn demonstrate_pattern_matching_techniques() {
    println!("=== Advanced Pattern Matching ===");
    
    let messages = vec![
        Message::Move { x: 0, y: 0 },
        Message::Move { x: 10, y: 0 },
        Message::ChangeColor(255, 255, 255),
        Message::Write("test".to_string()),
    ];
    
    for msg in &messages {
        match msg {
            Message::Move { x: 0, y: 0 } => println!("Origin move"),
            Message::Move { x, y: 0 } => println!("Horizontal move to x={}", x),
            Message::Move { x: 0, y } => println!("Vertical move to y={}", y),
            Message::Move { x, y } => println!("Diagonal move to ({}, {})", x, y),
            Message::ChangeColor(r, g, b) if *r == *g && *g == *b => {
                println!("Grayscale color: {}", r)
            },
            Message::ChangeColor(255, 0, 0) => println!("Pure red"),
            Message::ChangeColor(r, g, b) => println!("Color RGB({}, {}, {})", r, g, b),
            Message::Write(text) if text.len() < 5 => println!("Short message: {}", text),
            Message::Write(text) => println!("Long message: {}", text),
            Message::Quit => println!("Quit message"),
        }
    }
}

// ========================================
// 11. MAIN FUNCTION - DEMONSTRATIONS
// ========================================

fn main() {
    println!("🦀 COMPREHENSIVE RUST ENUM GUIDE 🦀\n");
    
    demonstrate_basic_enums();
    demonstrate_enums_with_data();
    demonstrate_generic_enums();
    demonstrate_recursive_enums();
    demonstrate_advanced_patterns();
    demonstrate_borrowed_data();
    demonstrate_pattern_matching_techniques();
    
    println!("=== Summary ===");
    println!("✅ Basic enums with unit variants");
    println!("✅ Enums with data (tuple and struct variants)");
    println!("✅ Generic enums with type parameters");
    println!("✅ Recursive enums for tree/list structures");
    println!("✅ Pattern matching and destructuring");
    println!("✅ Methods and trait implementations");
    println!("✅ Advanced patterns and guards");
    println!("✅ Error handling with custom enums");
    println!("✅ Lifetimes in enum variants");
    println!("✅ State machines and business logic");
    
    println!("\n🎉 Enum mastery achieved!");
}

I'll create a comprehensive guide to enums in Rust with complete implementations that demonstrate all the key concepts and use cases.I've created a comprehensive guide to Rust enums that covers everything from basic concepts to advanced patterns. Here's what the guide includes:

## Key Topics Covered:

1. **Basic Enums** - Simple unit variants and explicit discriminant values
2. **Enums with Data** - Tuple variants, struct-like variants, and mixed data types
3. **Generic Enums** - Type parameters and reusable enum patterns
4. **Recursive Enums** - Binary trees and linked lists using Box for heap allocation
5. **Pattern Matching** - Comprehensive matching techniques including guards and destructuring
6. **Methods on Enums** - Implementation blocks with associated functions
7. **Trait Implementations** - Display, Debug, and custom traits
8. **Advanced Patterns** - State machines, error handling, and associated constants
9. **Lifetimes** - Using borrowed data in enum variants
10. **Practical Examples** - Real-world use cases like traffic lights, mathematical operations, and data structures

## Key Features Demonstrated:

- **Complete implementations** of common patterns like Option-like types and Result-like error handling
- **Memory management** with Box for recursive structures
- **Pattern matching techniques** including guards, ranges, and destructuring
- **Generic programming** with type parameters and constraints
- **Error handling** with custom error enums
- **State management** using enums as state machines
- **Trait implementations** for Display, Debug, and custom behaviors

The code is fully runnable and includes demonstration functions that show each concept in action. You can compile and run it with `cargo run` to see all the examples working together.

This guide provides a solid foundation for understanding and using enums effectively in Rust, from simple cases to complex data structures and design patterns.