
```rust
// ============================================
// COMPREHENSIVE RUST SYNTAX GUIDE
// ============================================

// 1. VARIABLES AND MUTABILITY
// ============================================

fn variables_demo() {
    // Immutable by default
    let x = 5;
    // x = 6; // Error: cannot assign twice to immutable variable
    
    // Mutable variables
    let mut y = 10;
    y = 20; // OK
    
    // Constants (must have type annotation)
    const MAX_POINTS: u32 = 100_000;
    
    // Shadowing
    let z = 5;
    let z = z + 1; // This creates a new variable
    let z = z * 2;
}

// 2. DATA TYPES
// ============================================

fn data_types_demo() {
    // Integers: i8, i16, i32, i64, i128, isize (signed)
    //           u8, u16, u32, u64, u128, usize (unsigned)
    let int: i32 = 42;
    let unsigned: u32 = 100;
    
    // Floating point: f32, f64
    let float: f64 = 3.14;
    
    // Boolean
    let boolean: bool = true;
    
    // Character (4 bytes, Unicode)
    let character: char = '🦀';
    
    // Tuples
    let tuple: (i32, f64, char) = (500, 6.4, 'x');
    let (a, b, c) = tuple; // Destructuring
    let first = tuple.0; // Access by index
    
    // Arrays (fixed size)
    let array: [i32; 5] = [1, 2, 3, 4, 5];
    let repeated = [3; 5]; // [3, 3, 3, 3, 3]
    let first_element = array[0];
}

// 3. FUNCTIONS
// ============================================

// Basic function
fn greet(name: &str) {
    println!("Hello, {}!", name);
}

// Function with return value
fn add(x: i32, y: i32) -> i32 {
    x + y // Expression without semicolon returns the value
}

// Multiple return values via tuple
fn swap(x: i32, y: i32) -> (i32, i32) {
    (y, x)
}

// Early return
fn check_number(n: i32) -> &'static str {
    if n < 0 {
        return "negative";
    }
    "positive or zero"
}

// 4. CONTROL FLOW
// ============================================

fn control_flow_demo() {
    // if/else
    let number = 6;
    if number % 4 == 0 {
        println!("divisible by 4");
    } else if number % 3 == 0 {
        println!("divisible by 3");
    } else {
        println!("not divisible by 4 or 3");
    }
    
    // if as expression
    let condition = true;
    let value = if condition { 5 } else { 6 };
    
    // match (pattern matching)
    let number = 13;
    match number {
        1 => println!("One"),
        2 | 3 | 5 | 7 | 11 => println!("Prime"),
        13..=19 => println!("Teen"),
        _ => println!("Other"), // _ is catch-all
    }
    
    // match with return value
    let dice_roll = 9;
    let result = match dice_roll {
        3 => "You won!",
        7 => "You lost!",
        _ => "Try again",
    };
}

// 5. LOOPS
// ============================================

fn loops_demo() {
    // loop (infinite loop)
    let mut counter = 0;
    let result = loop {
        counter += 1;
        if counter == 10 {
            break counter * 2; // break with value
        }
    };
    
    // while loop
    let mut number = 3;
    while number != 0 {
        println!("{}!", number);
        number -= 1;
    }
    
    // for loop (most common)
    let array = [10, 20, 30, 40, 50];
    for element in array {
        println!("{}", element);
    }
    
    // Range
    for number in 1..4 { // 1, 2, 3 (exclusive end)
        println!("{}", number);
    }
    
    for number in 1..=4 { // 1, 2, 3, 4 (inclusive end)
        println!("{}", number);
    }
    
    // Loop labels (for nested loops)
    'outer: loop {
        loop {
            break 'outer; // Breaks the outer loop
        }
    }
}

// 6. OWNERSHIP AND BORROWING
// ============================================

fn ownership_demo() {
    // Ownership: each value has one owner
    let s1 = String::from("hello");
    let s2 = s1; // s1 is moved to s2, s1 is no longer valid
    // println!("{}", s1); // Error: value borrowed after move
    
    // Clone for deep copy
    let s3 = s2.clone();
    
    // Borrowing (immutable reference)
    let s4 = String::from("hello");
    let len = calculate_length(&s4); // &s4 is a reference
    println!("Length of '{}' is {}", s4, len); // s4 still valid
    
    // Mutable borrowing
    let mut s5 = String::from("hello");
    change(&mut s5);
}

fn calculate_length(s: &String) -> usize {
    s.len()
}

fn change(s: &mut String) {
    s.push_str(", world");
}

// 7. STRUCTS
// ============================================

// Classic struct
struct User {
    username: String,
    email: String,
    sign_in_count: u64,
    active: bool,
}

// Tuple struct
struct Color(i32, i32, i32);
struct Point(i32, i32, i32);

// Unit struct (no fields)
struct Unit;

fn struct_demo() {
    // Creating instances
    let mut user1 = User {
        email: String::from("user@example.com"),
        username: String::from("user123"),
        active: true,
        sign_in_count: 1,
    };
    
    // Accessing fields
    user1.email = String::from("newemail@example.com");
    
    // Struct update syntax
    let user2 = User {
        email: String::from("another@example.com"),
        ..user1 // Use remaining fields from user1
    };
    
    // Tuple struct
    let black = Color(0, 0, 0);
    let origin = Point(0, 0, 0);
}

// Methods and Associated Functions
impl User {
    // Associated function (like static method)
    fn new(email: String, username: String) -> User {
        User {
            email,
            username,
            active: true,
            sign_in_count: 1,
        }
    }
    
    // Method (takes &self)
    fn is_active(&self) -> bool {
        self.active
    }
    
    // Mutable method
    fn deactivate(&mut self) {
        self.active = false;
    }
    
    // Method that takes ownership
    fn into_email(self) -> String {
        self.email
    }
}

// 8. ENUMS
// ============================================

enum IpAddr {
    V4(u8, u8, u8, u8),
    V6(String),
}

enum Message {
    Quit,
    Move { x: i32, y: i32 }, // Anonymous struct
    Write(String),
    ChangeColor(i32, i32, i32),
}

impl Message {
    fn call(&self) {
        match self {
            Message::Quit => println!("Quit"),
            Message::Move { x, y } => println!("Move to ({}, {})", x, y),
            Message::Write(text) => println!("Write: {}", text),
            Message::ChangeColor(r, g, b) => println!("Color: ({}, {}, {})", r, g, b),
        }
    }
}

// Option enum (built-in)
fn option_demo() {
    let some_number = Some(5);
    let no_number: Option<i32> = None;
    
    match some_number {
        Some(n) => println!("Number is {}", n),
        None => println!("No number"),
    }
    
    // if let (concise pattern matching)
    if let Some(n) = some_number {
        println!("Number is {}", n);
    }
    
    // Result enum (for error handling)
    let result: Result<i32, &str> = Ok(42);
    let error: Result<i32, &str> = Err("Something went wrong");
}

// 9. COLLECTIONS
// ============================================

use std::collections::HashMap;

fn collections_demo() {
    // Vector (dynamic array)
    let mut v: Vec<i32> = Vec::new();
    let mut v2 = vec![1, 2, 3]; // Macro for initialization
    
    v2.push(4);
    v2.push(5);
    let third = v2[2];
    let third_safe = v2.get(2); // Returns Option<&T>
    
    // Iterate
    for i in &v2 {
        println!("{}", i);
    }
    
    // Mutable iteration
    for i in &mut v2 {
        *i += 50;
    }
    
    // String
    let mut s = String::from("hello");
    s.push_str(", world");
    s.push('!');
    let combined = format!("{} {}", "hello", "world");
    
    // HashMap
    let mut scores = HashMap::new();
    scores.insert(String::from("Blue"), 10);
    scores.insert(String::from("Red"), 50);
    
    let team_name = String::from("Blue");
    let score = scores.get(&team_name); // Returns Option<&V>
    
    // Iterate
    for (key, value) in &scores {
        println!("{}: {}", key, value);
    }
    
    // Update
    scores.entry(String::from("Yellow")).or_insert(50);
}

// 10. ERROR HANDLING
// ============================================

use std::fs::File;
use std::io::ErrorKind;

fn error_handling_demo() {
    // panic! for unrecoverable errors
    // panic!("crash and burn");
    
    // Result for recoverable errors
    let f = File::open("hello.txt");
    
    let f = match f {
        Ok(file) => file,
        Err(error) => match error.kind() {
            ErrorKind::NotFound => match File::create("hello.txt") {
                Ok(fc) => fc,
                Err(e) => panic!("Problem creating file: {:?}", e),
            },
            other_error => panic!("Problem opening file: {:?}", other_error),
        },
    };
    
    // Shortcut: unwrap and expect
    // let f = File::open("hello.txt").unwrap();
    // let f = File::open("hello.txt").expect("Failed to open file");
}

// ? operator for propagating errors
fn read_username_from_file() -> Result<String, std::io::Error> {
    let mut s = String::new();
    File::open("hello.txt")?.read_to_string(&mut s)?;
    Ok(s)
}

// 11. GENERICS
// ============================================

// Generic function
fn largest<T: PartialOrd>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list {
        if item > largest {
            largest = item;
        }
    }
    largest
}

// Generic struct
struct Point2D<T> {
    x: T,
    y: T,
}

impl<T> Point2D<T> {
    fn x(&self) -> &T {
        &self.x
    }
}

// Multiple type parameters
struct Point3D<T, U> {
    x: T,
    y: U,
}

// 12. TRAITS (similar to interfaces)
// ============================================

trait Summary {
    fn summarize(&self) -> String;
    
    // Default implementation
    fn summarize_author(&self) -> String {
        String::from("(Read more...)")
    }
}

struct NewsArticle {
    headline: String,
    content: String,
}

impl Summary for NewsArticle {
    fn summarize(&self) -> String {
        format!("{}: {}", self.headline, self.content)
    }
}

// Trait bounds
fn notify<T: Summary>(item: &T) {
    println!("Breaking news! {}", item.summarize());
}

// Multiple trait bounds
fn notify_multiple<T: Summary + Clone>(item: &T) {
    // ...
}

// Where clause (cleaner syntax)
fn some_function<T, U>(t: &T, u: &U) -> i32
where
    T: Summary + Clone,
    U: Clone + std::fmt::Debug,
{
    42
}

// 13. LIFETIMES
// ============================================

// Lifetime annotations
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() {
        x
    } else {
        y
    }
}

// Struct with lifetime
struct ImportantExcerpt<'a> {
    part: &'a str,
}

// 14. CLOSURES
// ============================================

fn closures_demo() {
    // Basic closure
    let add_one = |x| x + 1;
    let result = add_one(5);
    
    // With type annotations
    let add = |x: i32, y: i32| -> i32 { x + y };
    
    // Capturing environment
    let x = 4;
    let equal_to_x = |z| z == x; // Captures x
    
    // move keyword (takes ownership)
    let s = String::from("hello");
    let print_string = move || println!("{}", s);
    // s is no longer valid here
    
    // Using closures with iterators
    let v = vec![1, 2, 3];
    let v2: Vec<_> = v.iter().map(|x| x + 1).collect();
}

// 15. ITERATORS
// ============================================

fn iterators_demo() {
    let v = vec![1, 2, 3];
    
    // Creating iterators
    let iter = v.iter(); // Immutable references
    let iter_mut = v.clone().iter_mut(); // Mutable references
    let into_iter = v.clone().into_iter(); // Takes ownership
    
    // Common iterator methods
    let v2: Vec<i32> = v.iter().map(|x| x + 1).collect();
    let sum: i32 = v.iter().sum();
    let filtered: Vec<&i32> = v.iter().filter(|x| **x > 1).collect();
    
    // Chaining
    let result: Vec<i32> = v.iter()
        .filter(|x| **x > 1)
        .map(|x| x * 2)
        .collect();
}

// 16. SMART POINTERS
// ============================================

use std::rc::Rc;
use std::cell::RefCell;

fn smart_pointers_demo() {
    // Box<T> - heap allocation
    let b = Box::new(5);
    
    // Rc<T> - reference counting (multiple owners)
    let a = Rc::new(5);
    let b = Rc::clone(&a);
    let count = Rc::strong_count(&a); // 2
    
    // RefCell<T> - interior mutability
    let value = RefCell::new(5);
    *value.borrow_mut() += 1;
}

// 17. CONCURRENCY
// ============================================

use std::thread;
use std::sync::{Arc, Mutex};
use std::time::Duration;

fn concurrency_demo() {
    // Creating threads
    let handle = thread::spawn(|| {
        for i in 1..10 {
            println!("Thread: {}", i);
            thread::sleep(Duration::from_millis(1));
        }
    });
    
    handle.join().unwrap(); // Wait for thread to finish
    
    // Moving data into threads
    let v = vec![1, 2, 3];
    let handle = thread::spawn(move || {
        println!("Vector: {:?}", v);
    });
    
    // Shared state with Mutex
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
}

// 18. MACROS
// ============================================

// Using built-in macros
fn macros_demo() {
    println!("Hello"); // Print with newline
    print!("Hello"); // Print without newline
    eprintln!("Error"); // Print to stderr
    
    let v = vec![1, 2, 3]; // vec! macro
    
    // Debug printing
    let user = User::new(
        String::from("test@example.com"),
        String::from("testuser")
    );
    // println!("{:?}", user); // Requires #[derive(Debug)]
    
    // Formatting
    let s = format!("Hello, {}!", "world");
}

// Declarative macro
macro_rules! say_hello {
    () => {
        println!("Hello!");
    };
}

// 19. MODULES AND VISIBILITY
// ============================================

mod front_of_house {
    pub mod hosting {
        pub fn add_to_waitlist() {}
        
        fn seat_at_table() {} // Private
    }
    
    mod serving {
        fn take_order() {}
    }
}

// Using modules
use front_of_house::hosting;

pub fn eat_at_restaurant() {
    hosting::add_to_waitlist();
}

// 20. TESTING
// ============================================

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
    
    #[test]
    fn another_test() {
        assert!(true);
        assert_ne!(2, 3);
    }
    
    #[test]
    #[should_panic]
    fn test_panic() {
        panic!("This test should panic");
    }
}

// Main function
fn main() {
    println!("Rust Syntax Guide - Run individual demo functions to see examples");
}
```

I'll create a comprehensive Rust syntax guide covering all the essential language features.I've created a comprehensive guide covering all major Rust syntax features! The guide includes:

1. **Variables & Mutability** - let, mut, const, shadowing
2. **Data Types** - integers, floats, booleans, chars, tuples, arrays
3. **Functions** - parameters, return values, expressions
4. **Control Flow** - if/else, match statements
5. **Loops** - loop, while, for, ranges, loop labels
6. **Ownership & Borrowing** - Rust's core memory safety features
7. **Structs** - classic, tuple, and unit structs with methods
8. **Enums** - including Option and Result types
9. **Collections** - Vec, String, HashMap
10. **Error Handling** - Result, panic!, ? operator
11. **Generics** - generic functions and structs
12. **Traits** - Rust's interface system
13. **Lifetimes** - reference lifetime annotations
14. **Closures** - anonymous functions with environment capture
15. **Iterators** - map, filter, collect, and more
16. **Smart Pointers** - Box, Rc, RefCell
17. **Concurrency** - threads, Arc, Mutex
18. **Macros** - println!, vec!, and custom macros
19. **Modules** - organizing code with visibility
20. **Testing** - unit tests with assertions

Each section includes practical examples showing real usage patterns. You can copy sections individually or use the entire guide as a reference while learning Rust!