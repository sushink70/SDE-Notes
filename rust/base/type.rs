I'll provide you with all the main types in Rust with examples and simple explanations.I've created a comprehensive guide to all Rust types with examples and explanations. Here's a summary of what's covered:

**Primitive Types:**
- Integer types (i8, i16, i32, i64, i128, u8, u16, u32, u64, u128, isize, usize)
- Floating point types (f32, f64)
- Boolean type (bool)
- Character type (char)

**Compound Types:**
- Tuples - group different types together
- Arrays - fixed-size collections of same type
- Slices - views into arrays/vectors

**String Types:**
- String slices (&str) - immutable string views
- String - owned, growable strings

**Collection Types:**
- Vec - growable arrays
- HashMap - key-value storage
- HashSet - unique value collections

**Special Types:**
- Option<T> - handles nullable values safely
- Result<T, E> - handles errors without exceptions
- Unit type (()) - represents "no value"
- Never type (!) - for computations that never complete

**User-Defined Types:**
- Structs - custom data structures
- Enums - types with multiple variants
- Trait objects - for dynamic dispatch

**Memory Management Types:**
- References (&T, &mut T) - borrowing values
- Box<T> - heap-allocated values
- Raw pointers (*const T, *mut T) - unsafe pointers

**Advanced Types:**
- Function pointers and closures
- Generic types with type parameters
- Lifetime annotations for memory safety

Each type includes practical examples showing how to declare, initialize, and use them. The code demonstrates Rust's focus on memory safety, zero-cost abstractions, and expressive type system.

// ==================== RUST TYPES COMPLETE GUIDE ====================

fn main() {
    println!("=== RUST TYPES GUIDE ===\n");

    // ==================== PRIMITIVE TYPES ====================
    println!("1. PRIMITIVE TYPES:");
    
    // Integer Types
    let byte: i8 = -128;           // 8-bit signed (-128 to 127)
    let unsigned_byte: u8 = 255;   // 8-bit unsigned (0 to 255)
    let short: i16 = -32768;       // 16-bit signed
    let unsigned_short: u16 = 65535; // 16-bit unsigned
    let int: i32 = -2147483648;    // 32-bit signed (default)
    let unsigned_int: u32 = 4294967295; // 32-bit unsigned
    let long: i64 = -9223372036854775808; // 64-bit signed
    let unsigned_long: u64 = 18446744073709551615; // 64-bit unsigned
    let very_long: i128 = 170141183460469231731687303715884105727; // 128-bit signed
    let unsigned_very_long: u128 = 340282366920938463463374607431768211455; // 128-bit unsigned
    let arch_int: isize = -1000;   // Architecture-dependent signed
    let arch_uint: usize = 1000;   // Architecture-dependent unsigned
    
    println!("  Integers: i8={}, u8={}, i32={}, u64={}", byte, unsigned_byte, int, unsigned_long);
    
    // Floating Point Types
    let float32: f32 = 3.14159;    // 32-bit float
    let float64: f64 = 2.718281828; // 64-bit float (default)
    println!("  Floats: f32={}, f64={}", float32, float64);
    
    // Boolean Type
    let is_true: bool = true;
    let is_false: bool = false;
    println!("  Boolean: true={}, false={}", is_true, is_false);
    
    // Character Type (Unicode scalar)
    let letter: char = 'A';
    let emoji: char = '😀';
    let unicode: char = '\u{1F600}'; // Another way to write emoji
    println!("  Characters: '{}', '{}', '{}'", letter, emoji, unicode);

    // ==================== COMPOUND TYPES ====================
    println!("\n2. COMPOUND TYPES:");
    
    // Tuple Type
    let tuple: (i32, f64, bool, char) = (42, 3.14, true, 'R');
    let (x, y, z, w) = tuple; // Destructuring
    println!("  Tuple: {:?}, first element: {}", tuple, tuple.0);
    
    // Array Type (fixed size, same type)
    let array: [i32; 5] = [1, 2, 3, 4, 5];
    let filled_array: [i32; 3] = [0; 3]; // [0, 0, 0]
    println!("  Array: {:?}, length: {}", array, array.len());
    
    // Slice Type (view into array/vector)
    let slice: &[i32] = &array[1..4]; // Elements 1, 2, 3
    println!("  Slice: {:?}", slice);

    // ==================== STRING TYPES ====================
    println!("\n3. STRING TYPES:");
    
    // String slice (&str) - immutable view
    let string_slice: &str = "Hello, World!";
    let string_literal = "This is also &str";
    println!("  String slice: {}", string_slice);
    
    // String - growable, heap-allocated
    let mut owned_string: String = String::from("Hello");
    owned_string.push_str(", Rust!");
    let another_string: String = "Created from literal".to_string();
    println!("  Owned String: {}", owned_string);

    // ==================== COLLECTION TYPES ====================
    println!("\n4. COLLECTION TYPES:");
    
    // Vector - growable array
    let mut vector: Vec<i32> = vec![1, 2, 3];
    vector.push(4);
    println!("  Vector: {:?}", vector);
    
    // HashMap - key-value pairs
    use std::collections::HashMap;
    let mut map: HashMap<String, i32> = HashMap::new();
    map.insert("apple".to_string(), 5);
    map.insert("banana".to_string(), 3);
    println!("  HashMap: {:?}", map);
    
    // HashSet - unique values
    use std::collections::HashSet;
    let mut set: HashSet<i32> = HashSet::new();
    set.insert(1);
    set.insert(2);
    set.insert(1); // Won't be added again
    println!("  HashSet: {:?}", set);

    // ==================== OPTION TYPE ====================
    println!("\n5. OPTION TYPE (for nullable values):");
    
    let some_value: Option<i32> = Some(42);
    let no_value: Option<i32> = None;
    
    match some_value {
        Some(value) => println!("  Found value: {}", value),
        None => println!("  No value found"),
    }
    
    // Using if let
    if let Some(value) = some_value {
        println!("  Value using if let: {}", value);
    }

    // ==================== RESULT TYPE ====================
    println!("\n6. RESULT TYPE (for error handling):");
    
    fn divide(a: f64, b: f64) -> Result<f64, &'static str> {
        if b == 0.0 {
            Err("Division by zero")
        } else {
            Ok(a / b)
        }
    }
    
    let success: Result<f64, &str> = divide(10.0, 2.0);
    let failure: Result<f64, &str> = divide(10.0, 0.0);
    
    match success {
        Ok(value) => println!("  Division result: {}", value),
        Err(error) => println!("  Error: {}", error),
    }

    // ==================== STRUCT TYPES ====================
    println!("\n7. STRUCT TYPES:");
    
    // Named struct
    struct Person {
        name: String,
        age: u32,
        email: String,
    }
    
    let person = Person {
        name: "Alice".to_string(),
        age: 30,
        email: "alice@example.com".to_string(),
    };
    println!("  Person: {} is {} years old", person.name, person.age);
    
    // Tuple struct
    struct Point(i32, i32);
    let origin = Point(0, 0);
    println!("  Point: ({}, {})", origin.0, origin.1);
    
    // Unit struct (no fields)
    struct Unit;
    let _unit = Unit;

    // ==================== ENUM TYPES ====================
    println!("\n8. ENUM TYPES:");
    
    // Simple enum
    enum Color {
        Red,
        Green,
        Blue,
    }
    
    let favorite_color = Color::Blue;
    
    // Enum with data
    enum Message {
        Quit,
        Move { x: i32, y: i32 },
        Write(String),
        ChangeColor(i32, i32, i32),
    }
    
    let msg = Message::Write("Hello from enum!".to_string());
    
    match msg {
        Message::Quit => println!("  Quit message"),
        Message::Move { x, y } => println!("  Move to ({}, {})", x, y),
        Message::Write(text) => println!("  Message: {}", text),
        Message::ChangeColor(r, g, b) => println!("  Change color to RGB({}, {}, {})", r, g, b),
    }

    // ==================== REFERENCE TYPES ====================
    println!("\n9. REFERENCE TYPES:");
    
    let value = 42;
    let reference: &i32 = &value;         // Immutable reference
    let mut mutable_value = 100;
    let mutable_ref: &mut i32 = &mut mutable_value; // Mutable reference
    
    println!("  Value: {}, Reference: {}", value, *reference);
    *mutable_ref += 1;
    println!("  Mutable reference changed value to: {}", mutable_value);

    // ==================== POINTER TYPES ====================
    println!("\n10. POINTER TYPES:");
    
    // Box - heap allocation
    let boxed: Box<i32> = Box::new(42);
    println!("  Boxed value: {}", *boxed);
    
    // Raw pointers (unsafe)
    let raw_ptr: *const i32 = &value;
    unsafe {
        println!("  Raw pointer value: {}", *raw_ptr);
    }

    // ==================== FUNCTION TYPES ====================
    println!("\n11. FUNCTION TYPES:");
    
    fn add(a: i32, b: i32) -> i32 {
        a + b
    }
    
    // Function pointer
    let func_ptr: fn(i32, i32) -> i32 = add;
    println!("  Function result: {}", func_ptr(5, 3));
    
    // Closure
    let closure = |x: i32| x * 2;
    println!("  Closure result: {}", closure(5));
    
    // Closure that captures environment
    let multiplier = 3;
    let capturing_closure = |x: i32| x * multiplier;
    println!("  Capturing closure result: {}", capturing_closure(4));

    // ==================== TRAIT OBJECTS ====================
    println!("\n12. TRAIT OBJECTS (Dynamic dispatch):");
    
    trait Drawable {
        fn draw(&self);
    }
    
    struct Circle {
        radius: f64,
    }
    
    impl Drawable for Circle {
        fn draw(&self) {
            println!("  Drawing circle with radius: {}", self.radius);
        }
    }
    
    let circle = Circle { radius: 5.0 };
    let drawable: &dyn Drawable = &circle;
    drawable.draw();
    
    // Box<dyn Trait> for owned trait objects
    let boxed_drawable: Box<dyn Drawable> = Box::new(Circle { radius: 3.0 });
    boxed_drawable.draw();

    // ==================== GENERIC TYPES ====================
    println!("\n13. GENERIC TYPES:");
    
    // Generic struct
    struct Container<T> {
        value: T,
    }
    
    let int_container = Container { value: 42 };
    let string_container = Container { value: "Hello".to_string() };
    
    println!("  Int container: {}", int_container.value);
    println!("  String container: {}", string_container.value);
    
    // Generic function
    fn print_type<T: std::fmt::Display>(value: T) {
        println!("  Generic value: {}", value);
    }
    
    print_type(123);
    print_type("Generic string");

    // ==================== LIFETIME TYPES ====================
    println!("\n14. LIFETIME ANNOTATIONS:");
    
    // Function with lifetime annotation
    fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
        if x.len() > y.len() { x } else { y }
    }
    
    let string1 = "Hello";
    let string2 = "World!";
    let result = longest(string1, string2);
    println!("  Longest string: {}", result);
    
    // Struct with lifetime
    struct ImportantExcerpt<'a> {
        part: &'a str,
    }
    
    let novel = String::from("Call me Ishmael. Some years ago...");
    let first_sentence = novel.split('.').next().expect("Could not find a '.'");
    let excerpt = ImportantExcerpt { part: first_sentence };
    println!("  Excerpt: {}", excerpt.part);

    // ==================== UNIT TYPE ====================
    println!("\n15. UNIT TYPE:");
    
    let unit: () = ();  // Unit type, represents "no meaningful value"
    println!("  Unit type: {:?}", unit);
    
    // Functions that don't return a value actually return ()
    fn print_hello() {
        println!("  Hello from unit function!");
    }
    
    let _result: () = print_hello();

    // ==================== NEVER TYPE ====================
    println!("\n16. NEVER TYPE (!):");
    
    // The never type represents computations that never complete
    fn divergent_function() -> ! {
        panic!("This function never returns!");
    }
    
    // Uncommenting this would cause the program to panic:
    // divergent_function();
    
    println!("  Never type exists but calling it would panic!");

    println!("\n=== END OF RUST TYPES GUIDE ===");
}

I'll provide you with advanced Rust types that go beyond the basics, focusing on complex type system features and advanced patterns.I've created a comprehensive guide to advanced Rust types that covers sophisticated type system features. Here's what's included:

## Advanced Type Categories Covered:

**1. Phantom Types** - Types that carry compile-time information without runtime data
- Used for type-safe APIs and preventing mixing incompatible units

**2. Associated Types** - Types associated with traits for cleaner generic interfaces
- More ergonomic than generic parameters in many cases

**3. Higher-Ranked Trait Bounds (HRTB)** - Work with closures across any lifetime
- Essential for advanced generic programming

**4. Existential Types (impl Trait)** - Hide concrete types behind trait boundaries
- Return complex types without exposing implementation details

**5. Const Generics** - Generic parameters that are values, not types
- Enable compile-time array sizes and numeric computations

**6. Generic Associated Types (GAT)** - Associated types that are themselves generic
- Enable advanced iterator and streaming patterns

**7. Advanced Smart Pointers** - Rc, Arc, Weak references for complex ownership
- Enable shared ownership and prevent cycles

**8. Interior Mutability** - Cell, RefCell for mutating immutable data
- Break Rust's normal borrowing rules safely

**9. Pin and Unpin** - Prevent moving data that contains self-references
- Critical for async programming and unsafe code

**10. Function Trait Objects** - Dynamic dispatch for closures
- FnOnce, FnMut, Fn trait objects

**11. Zero-Sized Types** - Types that take no memory but carry meaning
- Efficient marker types and phantom data

**12. Type-Level Programming** - Computation at the type level
- Peano numbers and type-level lists

**13. Branded Types** - Prevent mixing similar but distinct types
- Type safety for IDs and similar values

**14. Never Type (!)** - Represents computations that never complete
- Used with diverging functions and error handling

These advanced types enable:
- **Zero-cost abstractions** - No runtime overhead for type safety
- **Compile-time guarantees** - Catch errors at compile time
- **Memory safety** - Prevent data races and use-after-free
- **Expressive APIs** - Create intuitive and hard-to-misuse interfaces

The examples show practical applications of each concept, demonstrating how Rust's type system enables both safety and performance through sophisticated compile-time checking.

// ==================== ADVANCED RUST TYPES GUIDE ====================

use std::marker::PhantomData;
use std::ptr::NonNull;
use std::sync::{Arc, Mutex, RwLock};
use std::rc::{Rc, Weak};
use std::cell::{Cell, RefCell};
use std::pin::Pin;
use std::future::Future;
use std::ops::{Deref, DerefMut};

fn main() {
    println!("=== ADVANCED RUST TYPES GUIDE ===\n");

    // ==================== PHANTOM TYPES ====================
    println!("1. PHANTOM TYPES:");
    
    // Phantom types carry type information at compile time but no runtime data
    struct Kilometers;
    struct Miles;
    
    struct Distance<Unit> {
        value: f64,
        _marker: PhantomData<Unit>,
    }
    
    impl<Unit> Distance<Unit> {
        fn new(value: f64) -> Self {
            Distance {
                value,
                _marker: PhantomData,
            }
        }
        
        fn value(&self) -> f64 {
            self.value
        }
    }
    
    // Type-safe conversion
    impl Distance<Miles> {
        fn to_kilometers(self) -> Distance<Kilometers> {
            Distance::new(self.value * 1.609344)
        }
    }
    
    let distance_miles = Distance::<Miles>::new(10.0);
    let distance_km = distance_miles.to_kilometers();
    println!("  10 miles = {:.2} km", distance_km.value());

    // ==================== ASSOCIATED TYPES ====================
    println!("\n2. ASSOCIATED TYPES:");
    
    trait Iterator2 {
        type Item;  // Associated type
        fn next(&mut self) -> Option<Self::Item>;
    }
    
    struct Counter {
        current: u32,
        max: u32,
    }
    
    impl Counter {
        fn new(max: u32) -> Counter {
            Counter { current: 0, max }
        }
    }
    
    impl Iterator2 for Counter {
        type Item = u32;  // Concrete associated type
        
        fn next(&mut self) -> Option<Self::Item> {
            if self.current < self.max {
                let current = self.current;
                self.current += 1;
                Some(current)
            } else {
                None
            }
        }
    }
    
    let mut counter = Counter::new(3);
    while let Some(value) = counter.next() {
        println!("  Counter: {}", value);
    }

    // ==================== HIGHER-RANKED TRAIT BOUNDS (HRTB) ====================
    println!("\n3. HIGHER-RANKED TRAIT BOUNDS:");
    
    // HRTB allows working with closures that work for any lifetime
    fn apply_to_all<F>(strings: &[String], mut f: F) 
    where
        F: for<'a> FnMut(&'a str) -> bool,
    {
        for s in strings {
            if f(s) {
                println!("  Matched: {}", s);
            }
        }
    }
    
    let strings = vec!["hello".to_string(), "world".to_string(), "rust".to_string()];
    apply_to_all(&strings, |s| s.len() > 4);

    // ==================== TYPE ALIASES ====================
    println!("\n4. TYPE ALIASES:");
    
    type UserId = u64;
    type UserName = String;
    type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
    
    struct User {
        id: UserId,
        name: UserName,
    }
    
    fn get_user(id: UserId) -> Result<User> {
        Ok(User {
            id,
            name: "Alice".to_string(),
        })
    }
    
    match get_user(123) {
        Ok(user) => println!("  User: {} (ID: {})", user.name, user.id),
        Err(e) => println!("  Error: {}", e),
    }

    // ==================== EXISTENTIAL TYPES ====================
    println!("\n5. EXISTENTIAL TYPES (impl Trait):");
    
    // Return position impl Trait
    fn get_iterator() -> impl Iterator<Item = u32> {
        (0..5).map(|x| x * 2)
    }
    
    let iter = get_iterator();
    for value in iter {
        println!("  Iterator value: {}", value);
    }
    
    // Argument position impl Trait
    fn process_display(item: impl std::fmt::Display) {
        println!("  Processing: {}", item);
    }
    
    process_display(42);
    process_display("Hello");

    // ==================== CONST GENERICS ====================
    println!("\n6. CONST GENERICS:");
    
    struct Array<T, const N: usize> {
        data: [T; N],
    }
    
    impl<T, const N: usize> Array<T, N> {
        fn new(data: [T; N]) -> Self {
            Array { data }
        }
        
        fn len(&self) -> usize {
            N
        }
        
        fn get(&self, index: usize) -> Option<&T> {
            self.data.get(index)
        }
    }
    
    let arr = Array::new([1, 2, 3, 4, 5]);
    println!("  Array length: {}", arr.len());
    if let Some(value) = arr.get(2) {
        println!("  Array[2]: {}", value);
    }

    // ==================== GAT (Generic Associated Types) ====================
    println!("\n7. GENERIC ASSOCIATED TYPES:");
    
    trait StreamingIterator {
        type Item<'a> where Self: 'a;
        fn next<'a>(&'a mut self) -> Option<Self::Item<'a>>;
    }
    
    struct WindowsIterator<T> {
        data: Vec<T>,
        window_size: usize,
        position: usize,
    }
    
    impl<T> WindowsIterator<T> {
        fn new(data: Vec<T>, window_size: usize) -> Self {
            WindowsIterator {
                data,
                window_size,
                position: 0,
            }
        }
    }
    
    impl<T> StreamingIterator for WindowsIterator<T> {
        type Item<'a> = &'a [T] where Self: 'a;
        
        fn next<'a>(&'a mut self) -> Option<Self::Item<'a>> {
            if self.position + self.window_size <= self.data.len() {
                let window = &self.data[self.position..self.position + self.window_size];
                self.position += 1;
                Some(window)
            } else {
                None
            }
        }
    }
    
    let mut windows = WindowsIterator::new(vec![1, 2, 3, 4, 5], 3);
    while let Some(window) = windows.next() {
        println!("  Window: {:?}", window);
    }

    // ==================== SMART POINTERS ====================
    println!("\n8. SMART POINTERS:");
    
    // Rc<T> - Reference counted
    let data = Rc::new(vec![1, 2, 3, 4]);
    let data1 = Rc::clone(&data);
    let data2 = Rc::clone(&data);
    println!("  Rc strong count: {}", Rc::strong_count(&data));
    
    // Weak references
    let weak_ref: Weak<Vec<i32>> = Rc::downgrade(&data);
    if let Some(upgraded) = weak_ref.upgrade() {
        println!("  Weak reference still valid: {:?}", upgraded);
    }
    
    // Arc<T> - Atomic reference counted (thread-safe)
    let shared_data = Arc::new(Mutex::new(0));
    let shared_data_clone = Arc::clone(&shared_data);
    
    // In a real scenario, you'd use threads here
    {
        let mut data = shared_data.lock().unwrap();
        *data += 1;
    }
    
    {
        let data = shared_data_clone.lock().unwrap();
        println!("  Shared data: {}", *data);
    }

    // ==================== INTERIOR MUTABILITY ====================
    println!("\n9. INTERIOR MUTABILITY:");
    
    // Cell<T> - Copy types only
    let cell = Cell::new(10);
    println!("  Cell before: {}", cell.get());
    cell.set(20);
    println!("  Cell after: {}", cell.get());
    
    // RefCell<T> - Runtime borrow checking
    let ref_cell = RefCell::new(vec![1, 2, 3]);
    {
        let mut borrowed = ref_cell.borrow_mut();
        borrowed.push(4);
    } // Mutable borrow dropped here
    
    {
        let borrowed = ref_cell.borrow();
        println!("  RefCell contents: {:?}", *borrowed);
    }

    // ==================== PIN AND UNPIN ====================
    println!("\n10. PIN AND UNPIN:");
    
    // Pin prevents moving of data
    struct SelfReferential {
        data: String,
        pointer: *const u8,
    }
    
    impl SelfReferential {
        fn new(data: String) -> Pin<Box<Self>> {
            let mut boxed = Box::pin(SelfReferential {
                pointer: std::ptr::null(),
                data,
            });
            
            let self_ptr: *const u8 = boxed.data.as_ptr();
            unsafe {
                let mut_ref = Pin::as_mut(&mut boxed);
                Pin::get_unchecked_mut(mut_ref).pointer = self_ptr;
            }
            
            boxed
        }
        
        fn data(&self) -> &str {
            &self.data
        }
    }
    
    let pinned = SelfReferential::new("pinned data".to_string());
    println!("  Pinned data: {}", pinned.data());

    // ==================== ASYNC TYPES ====================
    println!("\n11. ASYNC TYPES:");
    
    // Future trait (simplified)
    async fn async_computation(x: i32) -> i32 {
        // In real code, this might involve async I/O
        x * 2
    }
    
    // Pin<Box<dyn Future<Output = T>>>
    fn boxed_future(x: i32) -> Pin<Box<dyn Future<Output = i32>>> {
        Box::pin(async move { x * 3 })
    }
    
    // Note: In main(), we can't actually await these futures
    // They would need to be run in an async runtime like tokio
    println!("  Async functions return impl Future");

    // ==================== FUNCTION TRAIT OBJECTS ====================
    println!("\n12. FUNCTION TRAIT OBJECTS:");
    
    // Different closure types
    let fn_once: Box<dyn FnOnce(i32) -> i32> = Box::new(|x| x + 1);
    let result = fn_once(5);
    println!("  FnOnce result: {}", result);
    
    let fn_mut: Box<dyn FnMut(i32) -> i32> = {
        let mut counter = 0;
        Box::new(move |x| {
            counter += 1;
            x + counter
        })
    };
    
    // Note: Can't use fn_mut here because it's moved into the box
    println!("  FnMut created (would need mutable access to call)");

    // ==================== NEVER TYPE IN PRACTICE ====================
    println!("\n13. NEVER TYPE IN PRACTICE:");
    
    fn handle_result(result: Result<i32, !>) -> i32 {
        match result {
            Ok(value) => value,
            Err(never) => never, // ! can coerce to any type
        }
    }
    
    // This function signature means it can never return an error
    let success_result: Result<i32, !> = Ok(42);
    let value = handle_result(success_result);
    println!("  Infallible result: {}", value);

    // ==================== ZERO-SIZED TYPES ====================
    println!("\n14. ZERO-SIZED TYPES:");
    
    struct ZeroSized;
    
    let _zst1 = ZeroSized;
    let _zst2 = ZeroSized;
    
    // Both instances have the same address because they take no space
    println!("  ZST size: {} bytes", std::mem::size_of::<ZeroSized>());
    
    // Unit struct as a marker type
    struct DatabaseConnection;
    struct FileConnection;
    
    trait Connection {
        fn connect(&self) -> String;
    }
    
    impl Connection for DatabaseConnection {
        fn connect(&self) -> String {
            "Connected to database".to_string()
        }
    }
    
    impl Connection for FileConnection {
        fn connect(&self) -> String {
            "Connected to file".to_string()
        }
    }
    
    fn establish_connection<T: Connection>(conn: T) -> String {
        conn.connect()
    }
    
    let db_result = establish_connection(DatabaseConnection);
    println!("  {}", db_result);

    // ==================== TYPE-LEVEL PROGRAMMING ====================
    println!("\n15. TYPE-LEVEL PROGRAMMING:");
    
    // Compile-time computation using types
    trait Peano {
        const VALUE: usize;
    }
    
    struct Zero;
    struct Succ<T: Peano>(PhantomData<T>);
    
    impl Peano for Zero {
        const VALUE: usize = 0;
    }
    
    impl<T: Peano> Peano for Succ<T> {
        const VALUE: usize = T::VALUE + 1;
    }
    
    type One = Succ<Zero>;
    type Two = Succ<One>;
    type Three = Succ<Two>;
    
    println!("  Type-level Three: {}", Three::VALUE);
    
    // Type-level list
    trait TypeList {
        const LEN: usize;
    }
    
    struct Nil;
    struct Cons<H, T: TypeList>(PhantomData<(H, T)>);
    
    impl TypeList for Nil {
        const LEN: usize = 0;
    }
    
    impl<H, T: TypeList> TypeList for Cons<H, T> {
        const LEN: usize = T::LEN + 1;
    }
    
    type MyList = Cons<i32, Cons<String, Cons<bool, Nil>>>;
    println!("  Type-level list length: {}", MyList::LEN);

    // ==================== BRANDED TYPES ====================
    println!("\n16. BRANDED TYPES:");
    
    // Prevent mixing up similar types
    mod branded {
        use std::marker::PhantomData;
        
        pub struct Brand<T, B> {
            value: T,
            _brand: PhantomData<B>,
        }
        
        impl<T, B> Brand<T, B> {
            pub fn new(value: T) -> Self {
                Brand {
                    value,
                    _brand: PhantomData,
                }
            }
            
            pub fn into_inner(self) -> T {
                self.value
            }
        }
        
        impl<T, B> std::ops::Deref for Brand<T, B> {
            type Target = T;
            fn deref(&self) -> &Self::Target {
                &self.value
            }
        }
    }
    
    use branded::Brand;
    
    struct UserId;
    struct OrderId;
    
    type BrandedUserId = Brand<u64, UserId>;
    type BrandedOrderId = Brand<u64, OrderId>;
    
    fn process_user(user_id: BrandedUserId) {
        println!("  Processing user: {}", *user_id);
    }
    
    fn process_order(order_id: BrandedOrderId) {
        println!("  Processing order: {}", *order_id);
    }
    
    let user_id = BrandedUserId::new(123);
    let order_id = BrandedOrderId::new(456);
    
    process_user(user_id);
    process_order(order_id);
    
    // This would cause a compile error:
    // process_user(order_id); // Type mismatch!

    println!("\n=== END OF ADVANCED RUST TYPES GUIDE ===");
}

// ==================== ASYNC TRAIT (requires async-trait crate in real code) ====================
// #[async_trait::async_trait]
// trait AsyncTrait {
//     async fn async_method(&self) -> i32;
// }

// ==================== CUSTOM DST (Dynamically Sized Types) ====================
// Example of a custom slice-like type
struct CustomSlice<T> {
    len: usize,
    data: [T], // Unsized field must be last
}

impl<T> CustomSlice<T> {
    fn len(&self) -> usize {
        self.len
    }
}

// ==================== VARIANCE EXAMPLES ====================
// Covariance, Contravariance, and Invariance examples would go here
// but are quite complex and require careful lifetime management