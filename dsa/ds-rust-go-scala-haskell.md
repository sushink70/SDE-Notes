Here's a comprehensive overview of data structures available in Rust, Go, and Scala:

## Rust Data Structures

**Built-in Types:**

- **Scalars**: `i8`, `i16`, `i32`, `i64`, `i128`, `u8`, `u16`, `u32`, `u64`, `u128`, `f32`, `f64`, `bool`, `char`
- **Arrays**: `[T; N]` (fixed size)
- **Slices**: `&[T]` (view into arrays/vectors)
- **Tuples**: `(T1, T2, ...)`
- **Structs**: Custom data structures with named fields
- **Enums**: Algebraic data types with variants
- **References**: `&T`, `&mut T`

```rust
fn main() {
    // ========== SCALARS ==========
    
    // Signed integers
    let small_int: i8 = -128;        // 8-bit signed integer (-128 to 127)
    let medium_int: i16 = -32_000;   // 16-bit signed integer
    let normal_int: i32 = -2_000_000; // 32-bit signed integer (default)
    let big_int: i64 = -9_000_000_000; // 64-bit signed integer
    let huge_int: i128 = -170_141_183_460_469_231_731_687_303_715_884_105_728; // 128-bit
    
    // Unsigned integers
    let small_uint: u8 = 255;        // 8-bit unsigned (0 to 255)
    let medium_uint: u16 = 65_535;   // 16-bit unsigned
    let normal_uint: u32 = 4_000_000; // 32-bit unsigned
    let big_uint: u64 = 18_000_000_000; // 64-bit unsigned
    let huge_uint: u128 = 340_282_366_920_938_463_463_374_607_431_768_211_455; // 128-bit
    
    // Floating point numbers
    let small_float: f32 = 3.14159;  // 32-bit floating point
    let big_float: f64 = 3.141592653589793; // 64-bit floating point (default)
    
    // Boolean
    let is_rust_awesome: bool = true;
    let is_debugging_fun: bool = false;
    
    // Character (Unicode scalar value)
    let letter: char = 'A';
    let emoji: char = '🦀';  // Rust mascot!
    let chinese: char = '中';
    
    println!("Scalars: {}, {}, {}, {}", small_int, big_float, is_rust_awesome, emoji);
    
    
    // ========== ARRAYS ==========
    
    // Fixed-size arrays
    let numbers: [i32; 5] = [1, 2, 3, 4, 5];
    let zeros: [i32; 3] = [0; 3];  // [0, 0, 0] - shorthand for repeated values
    let mixed: [f64; 4] = [1.1, 2.2, 3.3, 4.4];
    
    println!("Array: {:?}", numbers);
    println!("First element: {}", numbers[0]);
    println!("Array length: {}", numbers.len());
    
    
    // ========== SLICES ==========
    
    // Slices are views into arrays or vectors
    let arr = [10, 20, 30, 40, 50];
    let slice: &[i32] = &arr[1..4];  // Elements at indices 1, 2, 3
    let full_slice: &[i32] = &arr;   // View of entire array
    
    println!("Slice: {:?}", slice);
    println!("Full slice: {:?}", full_slice);
    
    // String slices are common
    let text = "Hello, Rust!";
    let hello: &str = &text[0..5];   // "Hello"
    println!("String slice: {}", hello);
    
    
    // ========== TUPLES ==========
    
    // Tuples can hold different types
    let person: (String, i32, bool) = ("Alice".to_string(), 30, true);
    let coordinates: (f64, f64) = (3.14, 2.71);
    let rgb: (u8, u8, u8) = (255, 128, 0);  // Orange color
    let unit: () = ();  // Unit tuple (empty tuple)
    
    // Destructuring tuples
    let (name, age, is_active) = person;
    println!("Person: {} is {} years old, active: {}", name, age, is_active);
    
    // Accessing by index
    println!("X coordinate: {}", coordinates.0);
    println!("Y coordinate: {}", coordinates.1);
    
    
    // ========== STRUCTS ==========
    
    // Classic struct with named fields
    struct Point {
        x: f64,
        y: f64,
    }
    
    struct User {
        username: String,
        email: String,
        age: u32,
        is_admin: bool,
    }
    
    // Tuple struct (struct with unnamed fields)
    struct Color(u8, u8, u8);
    
    // Unit struct (no fields)
    struct Marker;
    
    // Creating struct instances
    let origin = Point { x: 0.0, y: 0.0 };
    let user = User {
        username: String::from("rustacean"),
        email: String::from("rust@example.com"),
        age: 25,
        is_admin: false,
    };
    let red = Color(255, 0, 0);
    let marker = Marker;
    
    println!("Point: ({}, {})", origin.x, origin.y);
    println!("User: {} ({})", user.username, user.email);
    println!("Red color: RGB({}, {}, {})", red.0, red.1, red.2);
    
    
    // ========== ENUMS ==========
    
    // Simple enum
    enum Direction {
        North,
        South,
        East,
        West,
    }
    
    // Enum with data
    enum Message {
        Quit,                       // No data
        Move { x: i32, y: i32 },   // Named fields
        Write(String),              // Tuple variant
        ChangeColor(u8, u8, u8),   // Multiple values
    }
    
    // Option enum (built into Rust)
    let some_number: Option<i32> = Some(42);
    let no_number: Option<i32> = None;
    
    // Result enum (built into Rust)
    let success: Result<i32, String> = Ok(100);
    let failure: Result<i32, String> = Err("Something went wrong".to_string());
    
    // Using enums
    let dir = Direction::North;
    let msg = Message::Write("Hello from enum!".to_string());
    
    // Pattern matching with enums
    match dir {
        Direction::North => println!("Heading north!"),
        Direction::South => println!("Heading south!"),
        Direction::East => println!("Heading east!"),
        Direction::West => println!("Heading west!"),
    }
    
    match some_number {
        Some(value) => println!("Got a number: {}", value),
        None => println!("No number available"),
    }
    
    
    // ========== REFERENCES ==========
    
    let x = 42;
    let y = String::from("Hello, world!");
    
    // Immutable references
    let x_ref: &i32 = &x;
    let y_ref: &String = &y;
    
    println!("Value of x through reference: {}", x_ref);
    println!("Value of y through reference: {}", y_ref);
    
    // Mutable references
    let mut z = 100;
    let z_mut_ref: &mut i32 = &mut z;
    *z_mut_ref += 50;  // Dereference and modify
    
    println!("Modified z: {}", z);  // Will print 150
    
    // String slice reference (very common)
    let text_ref: &str = "This is a string slice";
    println!("String slice: {}", text_ref);
    
    
    // ========== COMBINING TYPES ==========
    
    // Complex nested types
    let users: Vec<User> = vec![user];  // Vector of structs
    let coordinates_map: std::collections::HashMap<String, Point> = 
        std::collections::HashMap::new();  // HashMap with struct values
    
    // Tuple with various types
    let complex_tuple: (Vec<i32>, Option<String>, Result<f64, &str>) = (
        vec![1, 2, 3],
        Some("Optional text".to_string()),
        Ok(3.14159)
    );
    
    println!("Complex tuple vector: {:?}", complex_tuple.0);
    
    // Array of tuples
    let points_array: [(i32, i32); 3] = [(0, 0), (1, 1), (2, 4)];
    println!("Points: {:?}", points_array);
}
```

**Standard Library Collections:**

- **Vec<T>**: Dynamic arrays (growable)
- **VecDeque<T>**: Double-ended queue
- **LinkedList<T>**: Doubly-linked list
- **HashMap<K, V>**: Hash table
- **BTreeMap<K, V>**: Sorted map (B-tree)
- **HashSet<T>**: Hash set
- **BTreeSet<T>**: Sorted set (B-tree)
- **BinaryHeap<T>**: Priority queue (max-heap)
- **String**: UTF-8 encoded strings
- **&str**: String slices

use std::collections::{HashMap, BTreeMap, HashSet, BTreeSet, BinaryHeap, VecDeque, LinkedList};

```rust
fn main() {
    println!("=== Rust Standard Library Collections Examples ===\n");

    // 1. Vec<T> - Dynamic arrays (growable)
    println!("1. Vec<T> - Dynamic Array:");
    let mut numbers = Vec::new();
    numbers.push(1);
    numbers.push(2);
    numbers.push(3);
    
    let mut colors = vec!["red", "green", "blue"]; // vec! macro
    colors.push("yellow");
    
    println!("Numbers: {:?}", numbers);
    println!("Colors: {:?}", colors);
    println!("First color: {}", colors[0]);
    println!("Length: {}\n", colors.len());

    // 2. VecDeque<T> - Double-ended queue
    println!("2. VecDeque<T> - Double-ended Queue:");
    let mut deque = VecDeque::new();
    deque.push_back(1);
    deque.push_back(2);
    deque.push_front(0);
    
    println!("Deque: {:?}", deque);
    println!("Pop front: {:?}", deque.pop_front());
    println!("Pop back: {:?}", deque.pop_back());
    println!("Remaining: {:?}\n", deque);

    // 3. LinkedList<T> - Doubly-linked list
    println!("3. LinkedList<T> - Doubly-linked List:");
    let mut list = LinkedList::new();
    list.push_back("first");
    list.push_back("second");
    list.push_front("zero");
    
    println!("List: {:?}", list);
    println!("Front: {:?}", list.front());
    println!("Back: {:?}\n", list.back());

    // 4. HashMap<K, V> - Hash table
    println!("4. HashMap<K, V> - Hash Table:");
    let mut scores = HashMap::new();
    scores.insert("Alice", 95);
    scores.insert("Bob", 87);
    scores.insert("Carol", 92);
    
    println!("Scores: {:?}", scores);
    println!("Alice's score: {:?}", scores.get("Alice"));
    
    // Update or insert
    scores.entry("David").or_insert(85);
    *scores.entry("Alice").or_insert(0) += 5; // Add 5 to Alice's score
    println!("Updated scores: {:?}\n", scores);

    // 5. BTreeMap<K, V> - Sorted map (B-tree)
    println!("5. BTreeMap<K, V> - Sorted Map:");
    let mut ages = BTreeMap::new();
    ages.insert("Charlie", 30);
    ages.insert("Alice", 25);
    ages.insert("Bob", 35);
    
    println!("Ages (sorted by key): {:?}", ages);
    for (name, age) in &ages {
        println!("{}: {}", name, age);
    }
    println!();

    // 6. HashSet<T> - Hash set
    println!("6. HashSet<T> - Hash Set:");
    let mut languages = HashSet::new();
    languages.insert("Rust");
    languages.insert("Python");
    languages.insert("JavaScript");
    languages.insert("Rust"); // Duplicates are ignored
    
    println!("Languages: {:?}", languages);
    println!("Contains Rust: {}", languages.contains("Rust"));
    println!("Contains Go: {}\n", languages.contains("Go"));

    // Set operations
    let set1: HashSet<i32> = [1, 2, 3, 4].into();
    let set2: HashSet<i32> = [3, 4, 5, 6].into();
    
    println!("Set1: {:?}", set1);
    println!("Set2: {:?}", set2);
    println!("Intersection: {:?}", set1.intersection(&set2).collect::<Vec<_>>());
    println!("Union: {:?}", set1.union(&set2).collect::<Vec<_>>());
    println!("Difference: {:?}", set1.difference(&set2).collect::<Vec<_>>());

    // 7. BTreeSet<T> - Sorted set (B-tree)
    println!("\n7. BTreeSet<T> - Sorted Set:");
    let mut sorted_numbers = BTreeSet::new();
    sorted_numbers.insert(5);
    sorted_numbers.insert(2);
    sorted_numbers.insert(8);
    sorted_numbers.insert(1);
    sorted_numbers.insert(5); // Duplicate ignored
    
    println!("Sorted numbers: {:?}", sorted_numbers);
    println!("Range 2..=5: {:?}", sorted_numbers.range(2..=5).collect::<Vec<_>>());

    // 8. BinaryHeap<T> - Priority queue (max-heap)
    println!("\n8. BinaryHeap<T> - Priority Queue (Max-Heap):");
    let mut heap = BinaryHeap::new();
    heap.push(3);
    heap.push(1);
    heap.push(4);
    heap.push(1);
    heap.push(5);
    
    println!("Heap: {:?}", heap);
    println!("Peek max: {:?}", heap.peek());
    
    println!("Popping elements in order:");
    while let Some(max) = heap.pop() {
        println!("  {}", max);
    }

    // 9. String - UTF-8 encoded strings
    println!("\n9. String - UTF-8 Encoded Strings:");
    let mut greeting = String::new();
    greeting.push_str("Hello");
    greeting.push(' ');
    greeting.push_str("World");
    greeting.push('!');
    
    let name = String::from("Alice");
    let message = format!("{}, {}", greeting, name);
    
    println!("Greeting: {}", greeting);
    println!("Name: {}", name);
    println!("Message: {}", message);
    println!("Length: {} bytes", message.len());
    println!("Characters: {} chars", message.chars().count());
    
    // String manipulation
    let mut text = String::from("  hello world  ");
    text = text.trim().to_string();
    text = text.replace("world", "Rust");
    println!("Processed text: '{}'", text);

    // 10. &str - String slices
    println!("\n10. &str - String Slices:");
    let text = "Hello, Rust programming!";
    let hello = &text[0..5];
    let rust = &text[7..11];
    
    println!("Full text: {}", text);
    println!("Slice 'hello': {}", hello);
    println!("Slice 'rust': {}", rust);
    
    // String slice methods
    let words: Vec<&str> = text.split_whitespace().collect();
    println!("Words: {:?}", words);
    
    println!("Starts with 'Hello': {}", text.starts_with("Hello"));
    println!("Contains 'Rust': {}", text.contains("Rust"));
    
    // Working with lines
    let multiline = "Line 1\nLine 2\nLine 3";
    println!("\nMultiline text:");
    for (i, line) in multiline.lines().enumerate() {
        println!("  {}: {}", i + 1, line);
    }

    println!("\n=== Performance and Use Case Notes ===");
    println!("Vec<T>: O(1) append, O(1) access by index");
    println!("VecDeque<T>: O(1) push/pop at both ends");
    println!("LinkedList<T>: O(1) insert/remove at cursor, but rarely the best choice");
    println!("HashMap<K, V>: O(1) average insert/lookup, unordered");
    println!("BTreeMap<K, V>: O(log n) insert/lookup, always sorted");
    println!("HashSet<T>: O(1) average insert/lookup, unordered");
    println!("BTreeSet<T>: O(log n) insert/lookup, always sorted");
    println!("BinaryHeap<T>: O(log n) insert, O(1) peek max, O(log n) pop max");
    println!("String: Owned, growable UTF-8 text");
    println!("&str: Borrowed string slice, very efficient");
}
```

**Smart Pointers:**

- **Box<T>**: Heap allocation
- **Rc<T>**: Reference counting
- **Arc<T>**: Atomic reference counting
- **RefCell<T>**: Interior mutability
- **Mutex<T>**, **RwLock<T>**: Thread-safe containers

```rust
use std::rc::Rc;
use std::sync::{Arc, Mutex, RwLock};
use std::cell::RefCell;
use std::thread;
use std::time::Duration;

// Example struct for demonstrations
#[derive(Debug, Clone)]
struct Person {
    name: String,
    age: u32,
}

impl Person {
    fn new(name: &str, age: u32) -> Self {
        Person {
            name: name.to_string(),
            age,
        }
    }
    
    fn celebrate_birthday(&mut self) {
        self.age += 1;
        println!("{} is now {} years old!", self.name, self.age);
    }
}

// Recursive data structure example for Box<T>
#[derive(Debug)]
enum List {
    Node(i32, Box<List>),
    Nil,
}

impl List {
    fn new() -> List {
        List::Nil
    }
    
    fn prepend(self, value: i32) -> List {
        List::Node(value, Box::new(self))
    }
    
    fn len(&self) -> usize {
        match self {
            List::Node(_, tail) => 1 + tail.len(),
            List::Nil => 0,
        }
    }
}
```

```rust
fn main() {
    println!("=== Rust Smart Pointers Examples ===\n");

    // 1. Box<T> - Heap allocation
    println!("1. Box<T> - Heap Allocation:");
    
    // Simple heap allocation
    let boxed_int = Box::new(42);
    println!("Boxed integer: {}", boxed_int);
    
    // Large data on heap
    let large_array = Box::new([0; 1000000]); // 1M elements on heap
    println!("Large array length: {}", large_array.len());
    
    // Recursive data structures (classic use case)
    let list = List::new()
        .prepend(1)
        .prepend(2)
        .prepend(3);
    println!("Linked list: {:?}", list);
    println!("List length: {}", list.len());
    
    // Trait objects
    let shapes: Vec<Box<dyn std::fmt::Display>> = vec![
        Box::new("Circle"),
        Box::new(42),
        Box::new(3.14),
    ];
    
    println!("Trait objects:");
    for shape in &shapes {
        println!("  {}", shape);
    }
    println!();

    // 2. Rc<T> - Reference counting (single-threaded)
    println!("2. Rc<T> - Reference Counting (Single-threaded):");
    
    let person = Rc::new(Person::new("Alice", 25));
    println!("Initial reference count: {}", Rc::strong_count(&person));
    
    {
        let person_ref1 = Rc::clone(&person);
        let person_ref2 = Rc::clone(&person);
        
        println!("Reference count with clones: {}", Rc::strong_count(&person));
        println!("Person 1: {:?}", person_ref1);
        println!("Person 2: {:?}", person_ref2);
    } // person_ref1 and person_ref2 dropped here
    
    println!("Reference count after scope: {}", Rc::strong_count(&person));
    
    // Shared ownership in data structures
    let shared_data = Rc::new(vec![1, 2, 3, 4, 5]);
    let list1 = vec![shared_data.clone(), Rc::new(vec![6, 7, 8])];
    let list2 = vec![shared_data.clone(), Rc::new(vec![9, 10, 11])];
    
    println!("Shared data reference count: {}", Rc::strong_count(&shared_data));
    println!("List1 first element: {:?}", list1[0]);
    println!("List2 first element: {:?}", list2[0]);
    println!();

    // 3. RefCell<T> - Interior mutability (single-threaded)
    println!("3. RefCell<T> - Interior Mutability:");
    
    let person_cell = RefCell::new(Person::new("Bob", 30));
    
    // Immutable borrow
    {
        let borrowed = person_cell.borrow();
        println!("Borrowed person: {:?}", *borrowed);
    } // Borrow dropped here
    
    // Mutable borrow
    {
        let mut borrowed_mut = person_cell.borrow_mut();
        borrowed_mut.celebrate_birthday();
    } // Mutable borrow dropped here
    
    println!("Person after birthday: {:?}", person_cell.borrow());
    
    // Combining Rc and RefCell for shared mutable data
    let shared_person = Rc::new(RefCell::new(Person::new("Charlie", 28)));
    let person_ref1 = shared_person.clone();
    let person_ref2 = shared_person.clone();
    
    // Modify through first reference
    person_ref1.borrow_mut().age = 29;
    
    // Access through second reference
    println!("Modified person through shared reference: {:?}", person_ref2.borrow());
    println!();

    // 4. Arc<T> - Atomic reference counting (thread-safe)
    println!("4. Arc<T> - Atomic Reference Counting (Thread-safe):");
    
    let shared_data = Arc::new(vec![1, 2, 3, 4, 5]);
    let mut handles = vec![];
    
    for i in 0..3 {
        let data = shared_data.clone();
        let handle = thread::spawn(move || {
            println!("Thread {}: Data = {:?}", i, data);
            println!("Thread {}: Sum = {}", i, data.iter().sum::<i32>());
            thread::sleep(Duration::from_millis(100));
        });
        handles.push(handle);
    }
    
    // Wait for all threads to complete
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Final reference count: {}", Arc::strong_count(&shared_data));
    println!();

    // 5. Mutex<T> - Mutual exclusion (thread-safe mutable access)
    println!("5. Mutex<T> - Thread-safe Mutual Exclusion:");
    
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];
    
    for i in 0..5 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for j in 0..3 {
                let mut num = counter.lock().unwrap();
                *num += 1;
                println!("Thread {} increment {}: counter = {}", i, j, *num);
                thread::sleep(Duration::from_millis(50));
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Final counter value: {}", *counter.lock().unwrap());
    println!();

    // 6. RwLock<T> - Read-Write lock (multiple readers OR single writer)
    println!("6. RwLock<T> - Read-Write Lock:");
    
    let data = Arc::new(RwLock::new(Person::new("Diana", 35)));
    let mut handles = vec![];
    
    // Spawn reader threads
    for i in 0..3 {
        let data = Arc::clone(&data);
        let handle = thread::spawn(move || {
            let person = data.read().unwrap();
            println!("Reader {}: {:?}", i, *person);
            thread::sleep(Duration::from_millis(100));
        });
        handles.push(handle);
    }
    
    // Spawn a writer thread
    let data_writer = Arc::clone(&data);
    let writer_handle = thread::spawn(move || {
        thread::sleep(Duration::from_millis(150)); // Let readers go first
        let mut person = data_writer.write().unwrap();
        person.celebrate_birthday();
        println!("Writer modified the data");
    });
    handles.push(writer_handle);
    
    // Another reader after writer
    let data_reader = Arc::clone(&data);
    let final_reader = thread::spawn(move || {
        thread::sleep(Duration::from_millis(250));
        let person = data_reader.read().unwrap();
        println!("Final reader: {:?}", *person);
    });
    handles.push(final_reader);
    
    for handle in handles {
        handle.join().unwrap();
    }
    println!();

    // 7. Practical example: Thread-safe cache
    println!("7. Practical Example - Thread-safe Cache:");
    
    use std::collections::HashMap;
    
    let cache = Arc::new(RwLock::new(HashMap::<String, i32>::new()));
    let mut handles = vec![];
    
    // Writer thread - populates cache
    let cache_writer = Arc::clone(&cache);
    let writer = thread::spawn(move || {
        for i in 1..=5 {
            let mut cache = cache_writer.write().unwrap();
            let key = format!("key{}", i);
            cache.insert(key.clone(), i * 10);
            println!("Cached: {} = {}", key, i * 10);
            thread::sleep(Duration::from_millis(100));
        }
    });
    handles.push(writer);
    
    // Reader threads - read from cache
    for thread_id in 0..2 {
        let cache_reader = Arc::clone(&cache);
        let reader = thread::spawn(move || {
            thread::sleep(Duration::from_millis(250)); // Let writer populate some data
            
            for i in 1..=6 {
                let cache = cache_reader.read().unwrap();
                let key = format!("key{}", i);
                match cache.get(&key) {
                    Some(value) => println!("Thread {} read: {} = {}", thread_id, key, value),
                    None => println!("Thread {} miss: {} not found", thread_id, key),
                }
                thread::sleep(Duration::from_millis(50));
            }
        });
        handles.push(reader);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }

    println!("\n=== Smart Pointer Use Cases Summary ===");
    println!("Box<T>: Heap allocation, recursive types, trait objects");
    println!("Rc<T>: Single-threaded shared ownership");
    println!("Arc<T>: Multi-threaded shared ownership");
    println!("RefCell<T>: Single-threaded interior mutability");
    println!("Mutex<T>: Multi-threaded exclusive access");
    println!("RwLock<T>: Multi-threaded shared read OR exclusive write");
    println!("\nCommon Combinations:");
    println!("Rc<RefCell<T>>: Single-threaded shared mutable data");
    println!("Arc<Mutex<T>>: Multi-threaded shared mutable data");
    println!("Arc<RwLock<T>>: Multi-threaded shared data with frequent reads");
}
```

## Go Data Structures

**Built-in Types:**

- **Numeric**: `int`, `int8`, `int16`, `int32`, `int64`, `uint`, `uint8`, `uint16`, `uint32`, `uint64`, `float32`, `float64`, `complex64`, `complex128`
- **Boolean**: `bool`
- **String**: `string`
- **Arrays**: `[n]T` (fixed size)
- **Slices**: `[]T` (dynamic arrays)
- **Maps**: `map[K]V` (hash tables)
- **Channels**: `chan T` (communication between goroutines)
- **Pointers**: `*T`
- **Interfaces**: `interface{}`
- **Structs**: Custom types with fields
- **Functions**: `func` types

**Standard Library:**

- **container/list**: Doubly-linked list
- **container/ring**: Circular list
- **container/heap**: Heap operations (priority queue)
- **sync.Map**: Concurrent map
- **sync.Pool**: Object pool
- **bufio**: Buffered I/O structures

## Scala Data Structures

**Immutable Collections (scala.collection.immutable):**

- **List**: Linked list
- **Vector**: Indexed sequence (trie-based)
- **Array**: Mutable arrays (from Java)
- **Set**: Hash set
- **Map**: Hash map
- **TreeSet**: Sorted set (red-black tree)
- **TreeMap**: Sorted map (red-black tree)
- **Queue**: FIFO queue
- **Stack**: LIFO stack
- **Stream**: Lazy sequences
- **LazyList**: Lazy linked list
- **Range**: Arithmetic sequences

**Mutable Collections (scala.collection.mutable):**

- **ArrayBuffer**: Resizable array
- **ListBuffer**: Mutable list builder
- **LinkedList**: Mutable linked list
- **DoubleLinkedList**: Doubly-linked list
- **MutableList**: General mutable list
- **Set**: Mutable hash set
- **Map**: Mutable hash map
- **TreeSet**: Mutable sorted set
- **TreeMap**: Mutable sorted map
- **Queue**: Mutable queue
- **Stack**: Mutable stack
- **PriorityQueue**: Priority queue
- **StringBuilder**: Efficient string building

**Specialized Types:**

- **Option[T]**: Optional values (Some/None)
- **Either[A, B]**: Union types (Left/Right)
- **Try[T]**: Success/Failure handling
- **Future[T]**: Asynchronous computations
- **Tuple**: Product types (Tuple2, Tuple3, etc.)
- **Case Classes**: Immutable data classes
- **Sealed Traits**: Algebraic data types

**Concurrent Collections:**

- **TrieMap**: Lock-free concurrent map
- **Concurrent collections** in `scala.collection.concurrent`

Each language has different philosophies: Rust emphasizes memory safety and zero-cost abstractions, Go focuses on simplicity and built-in concurrency primitives, while Scala provides rich functional programming constructs with both mutable and immutable options.

Here's a comprehensive overview of data structures in Haskell, along with the previous languages:

## Haskell Data Structures

**Basic Types:**

- **Int**: Fixed-precision integers
- **Integer**: Arbitrary-precision integers
- **Float**, **Double**: Floating-point numbers
- **Bool**: Boolean values
- **Char**: Characters
- **String**: `[Char]` (list of characters)
- **Unit**: `()` (empty tuple)

**Built-in Algebraic Data Types:**

- **Maybe a**: Optional values (`Nothing | Just a`)
- **Either a b**: Union types (`Left a | Right b`)
- **Ordering**: `LT | EQ | GT`
- **IO a**: I/O actions

**Lists and Sequences:**

- **List [a]**: Singly-linked lists (fundamental structure)
- **Data.Sequence**: Finger trees (efficient random access)
- **Data.Vector**: Boxed vectors (array-like)
- **Data.Vector.Unboxed**: Unboxed vectors (primitive types)
- **Data.Vector.Storable**: Storable vectors (C-compatible)
- **Data.ByteString**: Packed byte strings
- **Data.Text**: Efficient Unicode text

**Tuples:**

- **Tuples**: `(a, b)`, `(a, b, c)`, etc. (up to large arities)
- **Data.Tuple**: Tuple utilities

**Trees:**

- **Data.Tree**: Rose trees (multi-way trees)
- **Data.Map**: Balanced binary trees (size-balanced trees)
- **Data.IntMap**: Maps with Int keys (Patricia trees)
- **Data.Set**: Balanced binary search trees
- **Data.IntSet**: Sets of Ints (Patricia trees)

**Hash-based Structures:**

- **Data.HashMap.Strict/Lazy**: Hash array mapped tries
- **Data.HashSet**: Hash sets
- **Data.Hashtable**: Mutable hash tables (ST/IO)

**Queues and Deques:**

- **Data.Sequence**: Double-ended queues (finger trees)
- **Data.Queue**: Simple queues
- **Data.Dequeue**: Double-ended queues
- **Data.PSQueue**: Priority search queues

**Heaps:**

- **Data.Heap**: Min/max heaps
- **Data.PQueue**: Priority queues

**Graphs:**

- **Data.Graph**: Basic graph representation
- **Data.Tree**: Tree structures from graphs

**Mutable Structures (ST/IO):**

- **Data.Array.ST**: Mutable arrays in ST
- **Data.Array.IO**: Mutable arrays in IO
- **Data.Vector.Mutable**: Mutable vectors
- **Data.HashTable**: Mutable hash tables
- **Data.STRef**: Mutable references in ST
- **Data.IORef**: Mutable references in IO

**Specialized Arrays:**

- **Data.Array**: Immutable arrays
- **Data.Array.Unboxed**: Unboxed arrays
- **Data.Array.IArray**: Array interface
- **Data.Array.MArray**: Mutable array interface

**Functional Data Structures:**

- **Data.DList**: Difference lists (efficient append)
- **Data.Edison**: Collection of functional data structures
- **Data.FingerTree**: 2-3 finger trees
- **Data.Trie**: Trie structures

**Concurrent/Parallel Structures:**

- **Control.Concurrent.STM**: Software transactional memory
- **Data.Concurrent.Queue**: Lock-free queues
- **Control.Concurrent.MVar**: Mutable variables
- **Control.Concurrent.Chan**: Channels

**Custom Algebraic Data Types:**

```haskell
data Tree a = Leaf | Node a (Tree a) (Tree a)
data Rose a = Rose a [Rose a]
data List a = Nil | Cons a (List a)
```

**Newtypes and Type Synonyms:**

```haskell
newtype Identity a = Identity a
type String = [Char]
type FilePath = String
```

**Record Types:**

```haskell
data Person = Person 
  { name :: String
  , age :: Int
  , email :: String
  }
```

## Complete Comparison Summary

**Rust**: Focuses on zero-cost abstractions, memory safety, and ownership. Rich type system with traits, extensive standard library collections, and smart pointers for memory management.

**Go**: Emphasizes simplicity and built-in concurrency. Limited but practical set of built-in types (slices, maps, channels). Standard library provides additional containers.

**Scala**: Hybrid functional/OOP approach with rich collections library. Distinguishes between mutable and immutable collections. Strong type system with algebraic data types and monadic types.

**Haskell**: Purely functional with lazy evaluation. Extensive ecosystem of functional data structures. Strong emphasis on algebraic data types, immutability, and mathematical abstractions. Rich type system with type classes and higher-kinded types.

Each language reflects its design philosophy: Haskell's mathematical purity, Rust's systems programming focus, Go's pragmatic simplicity, and Scala's expressiveness for complex domains.
