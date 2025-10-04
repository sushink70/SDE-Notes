// ============================================================================
// CONTROL BENEFITS: Using Self vs NOT Using Self in Rust
// ============================================================================

// This demonstrates the PRACTICAL CONTROL DIFFERENCES between using Self
// and explicit type names in Rust code.

// ============================================================================
// 1. TYPE SAFETY & REFACTORING CONTROL
// ============================================================================

// Scenario: You need to rename a type

// WITHOUT Self - Manual tracking required
mod without_self {
    #[derive(Debug)]
    pub struct UserAccount {
        id: u64,
        name: String,
    }
    
    impl UserAccount {
        pub fn new(id: u64, name: String) -> UserAccount {
            UserAccount { id, name }
        }
        
        pub fn clone_account(&self) -> UserAccount {
            UserAccount {
                id: self.id,
                name: self.name.clone(),
            }
        }
        
        pub fn with_name(mut self, name: String) -> UserAccount {
            self.name = name;
            self
        }
        
        // If you rename UserAccount to User, you must change:
        // - 5 occurrences in this impl block alone!
    }
}

// WITH Self - Automatic type tracking
mod with_self {
    #[derive(Debug)]
    pub struct UserAccount {  // Rename this to User...
        id: u64,
        name: String,
    }
    
    impl UserAccount {  // ...and here...
        pub fn new(id: u64, name: String) -> Self {
            Self { id, name }
        }
        
        pub fn clone_account(&self) -> Self {
            Self {
                id: self.id,
                name: self.name.clone(),
            }
        }
        
        pub fn with_name(mut self, name: String) -> Self {
            self.name = name;
            self
        }
        
        // ...and you're done! Only 2 changes needed instead of 7.
    }
}

// ============================================================================
// 2. GENERIC TYPE CONTROL
// ============================================================================

// WITHOUT Self - Must maintain generic parameters everywhere
mod generic_without_self {
    pub struct Cache<K, V> {
        data: std::collections::HashMap<K, V>,
    }
    
    impl<K, V> Cache<K, V> 
    where 
        K: std::hash::Hash + Eq,
    {
        // ❌ LOSE CONTROL: Easy to make mistakes with generic parameters
        pub fn new() -> Cache<K, V> {
            Cache {
                data: std::collections::HashMap::new(),
            }
        }
        
        // ❌ What if you add a third generic parameter W?
        // You must update EVERY occurrence!
        pub fn empty() -> Cache<K, V> {
            Cache {
                data: std::collections::HashMap::new(),
            }
        }
        
        pub fn with_capacity(cap: usize) -> Cache<K, V> {
            Cache {
                data: std::collections::HashMap::with_capacity(cap),
            }
        }
    }
}

// WITH Self - Automatic generic parameter management
mod generic_with_self {
    pub struct Cache<K, V> {
        data: std::collections::HashMap<K, V>,
    }
    
    impl<K, V> Cache<K, V> 
    where 
        K: std::hash::Hash + Eq,
    {
        // ✅ GAIN CONTROL: Add/remove generic parameters in one place
        pub fn new() -> Self {
            Self {
                data: std::collections::HashMap::new(),
            }
        }
        
        // ✅ Add a third generic parameter W? Just change the struct definition!
        pub fn empty() -> Self {
            Self {
                data: std::collections::HashMap::new(),
            }
        }
        
        pub fn with_capacity(cap: usize) -> Self {
            Self {
                data: std::collections::HashMap::with_capacity(cap),
            }
        }
    }
}

// ============================================================================
// 3. VISIBILITY & ENCAPSULATION CONTROL
// ============================================================================

// WITHOUT Self - Type leakage in complex scenarios
mod visibility_without_self {
    pub struct Database {
        connection: String,
    }
    
    // Private internal type
    struct DatabaseBuilder {
        connection: Option<String>,
    }
    
    impl DatabaseBuilder {
        fn new() -> DatabaseBuilder {
            DatabaseBuilder { connection: None }
        }
        
        fn connection(mut self, conn: String) -> DatabaseBuilder {
            self.connection = Some(conn);
            self
        }
        
        fn build(self) -> Database {
            Database {
                connection: self.connection.unwrap_or_default(),
            }
        }
    }
    
    impl Database {
        pub fn builder() -> DatabaseBuilder {
            DatabaseBuilder::new()
        }
    }
}

// WITH Self - Better encapsulation
mod visibility_with_self {
    pub struct Database {
        connection: String,
    }
    
    struct DatabaseBuilder {
        connection: Option<String>,
    }
    
    impl DatabaseBuilder {
        fn new() -> Self {  // Type is clear but not exposed
            Self { connection: None }
        }
        
        fn connection(mut self, conn: String) -> Self {
            self.connection = Some(conn);
            self
        }
        
        fn build(self) -> Database {
            Database {
                connection: self.connection.unwrap_or_default(),
            }
        }
    }
    
    impl Database {
        pub fn builder() -> DatabaseBuilder {
            DatabaseBuilder::new()
        }
    }
}

// ============================================================================
// 4. METHOD CHAINING CONTROL (Builder Pattern)
// ============================================================================

// WITHOUT Self - Fragile method chains
mod chaining_without_self {
    #[derive(Debug)]
    pub struct HttpClient {
        base_url: String,
        timeout: u64,
        retries: u32,
    }
    
    impl HttpClient {
        pub fn new(base_url: String) -> HttpClient {
            HttpClient {
                base_url,
                timeout: 30,
                retries: 3,
            }
        }
        
        // ❌ If you change return type, chain breaks
        pub fn timeout(mut self, timeout: u64) -> HttpClient {
            self.timeout = timeout;
            self
        }
        
        pub fn retries(mut self, retries: u32) -> HttpClient {
            self.retries = retries;
            self
        }
    }
}

// WITH Self - Robust method chains
mod chaining_with_self {
    #[derive(Debug)]
    pub struct HttpClient {
        base_url: String,
        timeout: u64,
        retries: u32,
    }
    
    impl HttpClient {
        pub fn new(base_url: String) -> Self {
            Self {
                base_url,
                timeout: 30,
                retries: 3,
            }
        }
        
        // ✅ Return type is consistent and maintainable
        pub fn timeout(mut self, timeout: u64) -> Self {
            self.timeout = timeout;
            self
        }
        
        pub fn retries(mut self, retries: u32) -> Self {
            self.retries = retries;
            self
        }
    }
}

// ============================================================================
// 5. TRAIT IMPLEMENTATION CONTROL
// ============================================================================

// WITHOUT Self - Must repeat type with all constraints
mod trait_without_self {
    pub trait Drawable {
        fn draw(&self);
    }
    
    #[derive(Debug)]
    pub struct Shape<T: std::fmt::Display> {
        data: T,
    }
    
    impl<T: std::fmt::Display> Drawable for Shape<T> {
        fn draw(&self) {
            println!("Drawing: {}", self.data);
        }
    }
    
    impl<T: std::fmt::Display> Shape<T> {
        // ❌ Must repeat <T: std::fmt::Display> every time
        pub fn new(data: T) -> Shape<T> {
            Shape { data }
        }
        
        pub fn clone_shape(&self) -> Shape<T> 
        where
            T: Clone,
        {
            Shape {
                data: self.data.clone(),
            }
        }
    }
}

// WITH Self - Cleaner trait implementations
mod trait_with_self {
    pub trait Drawable {
        fn draw(&self);
    }
    
    #[derive(Debug)]
    pub struct Shape<T: std::fmt::Display> {
        data: T,
    }
    
    impl<T: std::fmt::Display> Drawable for Shape<T> {
        fn draw(&self) {
            println!("Drawing: {}", self.data);
        }
    }
    
    impl<T: std::fmt::Display> Shape<T> {
        // ✅ Self inherits all the generic constraints
        pub fn new(data: T) -> Self {
            Self { data }
        }
        
        pub fn clone_shape(&self) -> Self 
        where
            T: Clone,
        {
            Self {
                data: self.data.clone(),
            }
        }
    }
}

// ============================================================================
// 6. ERROR DETECTION CONTROL
// ============================================================================

// WITHOUT Self - Errors are less obvious
mod error_without_self {
    pub struct Point<T> {
        x: T,
        y: T,
    }
    
    impl<T> Point<T> {
        pub fn new(x: T, y: T) -> Point<T> {
            Point { x, y }
        }
        
        // ❌ SUBTLE BUG: What if you accidentally type Point<i32>?
        // pub fn origin() -> Point<i32> {  // Wrong! Should be Point<T>
        //     Point { x: 0, y: 0 }  // This compiles but limits the function!
        // }
    }
    
    impl Point<i32> {
        pub fn manhattan_distance(&self, other: &Point<i32>) -> i32 {
            (self.x - other.x).abs() + (self.y - other.y).abs()
        }
    }
}

// WITH Self - Compiler catches more errors
mod error_with_self {
    pub struct Point<T> {
        x: T,
        y: T,
    }
    
    impl<T> Point<T> {
        pub fn new(x: T, y: T) -> Self {
            Self { x, y }
        }
        
        // ✅ SAFE: Self can only refer to Point<T> in this context
        // You cannot accidentally narrow the type
    }
    
    impl Point<i32> {
        pub fn manhattan_distance(&self, other: &Self) -> i32 {
            (self.x - other.x).abs() + (self.y - other.y).abs()
        }
    }
}

// ============================================================================
// 7. CODE GENERATION & MACRO CONTROL
// ============================================================================

// WITHOUT Self - Macros are more complex
macro_rules! impl_new_without_self {
    ($type:ident) => {
        impl $type {
            pub fn new(value: i32) -> $type {  // Must use $type
                $type { value }
            }
        }
    };
}

// WITH Self - Macros are simpler
macro_rules! impl_new_with_self {
    ($type:ident) => {
        impl $type {
            pub fn new(value: i32) -> Self {  // Self is always correct
                Self { value }
            }
        }
    };
}

struct MyType1 { value: i32 }
struct MyType2 { value: i32 }

impl_new_with_self!(MyType1);
impl_new_with_self!(MyType2);

// ============================================================================
// 8. DOCUMENTATION CONTROL
// ============================================================================

// WITHOUT Self - Docs must specify exact types
mod docs_without_self {
    /// Creates a new UserProfile
    /// Returns: UserProfile
    pub struct UserProfile {
        name: String,
    }
    
    impl UserProfile {
        /// Returns a new UserProfile instance
        pub fn new(name: String) -> UserProfile {
            UserProfile { name }
        }
        
        /// Clones this UserProfile
        pub fn clone_profile(&self) -> UserProfile {
            UserProfile {
                name: self.name.clone(),
            }
        }
    }
}

// WITH Self - Docs are more flexible
mod docs_with_self {
    /// Creates a new UserProfile
    /// Returns: Self (the current type)
    pub struct UserProfile {
        name: String,
    }
    
    impl UserProfile {
        /// Returns a new instance of this type
        pub fn new(name: String) -> Self {
            Self { name }
        }
        
        /// Clones this instance
        pub fn clone_profile(&self) -> Self {
            Self {
                name: self.name.clone(),
            }
        }
    }
}

// ============================================================================
// 9. PRACTICAL COMPARISON: Real-World Scenario
// ============================================================================

// Scenario: A configurable client that evolves over time

// WITHOUT Self - High maintenance
mod without_self_example {
    pub struct ApiClient {
        base_url: String,
        api_key: String,
        timeout: u64,
    }
    
    impl ApiClient {
        pub fn new(base_url: String, api_key: String) -> ApiClient {
            ApiClient {
                base_url,
                api_key,
                timeout: 30,
            }
        }
        
        pub fn timeout(mut self, timeout: u64) -> ApiClient {
            self.timeout = timeout;
            self
        }
        
        pub fn clone_client(&self) -> ApiClient {
            ApiClient {
                base_url: self.base_url.clone(),
                api_key: self.api_key.clone(),
                timeout: self.timeout,
            }
        }
    }
    
    // Later, you decide to add generics for different auth types...
    // NOW you must change EVERY ApiClient to ApiClient<A>!
}

// WITH Self - Low maintenance
mod with_self_example {
    pub struct ApiClient {
        base_url: String,
        api_key: String,
        timeout: u64,
    }
    
    impl ApiClient {
        pub fn new(base_url: String, api_key: String) -> Self {
            Self {
                base_url,
                api_key,
                timeout: 30,
            }
        }
        
        pub fn timeout(mut self, timeout: u64) -> Self {
            self.timeout = timeout;
            self
        }
        
        pub fn clone_client(&self) -> Self {
            Self {
                base_url: self.base_url.clone(),
                api_key: self.api_key.clone(),
                timeout: self.timeout,
            }
        }
    }
    
    // Later, you can easily refactor to:
    // pub struct ApiClient<A: AuthProvider> { ... }
    // And all the Self references still work!
}

// ============================================================================
// MAIN: DEMONSTRATION
// ============================================================================

fn main() {
    println!("=== REFACTORING CONTROL ===");
    println!("With Self: Change type name in 2 places");
    println!("Without Self: Change type name in 7+ places");
    
    println!("\n=== GENERIC CONTROL ===");
    let cache = generic_with_self::Cache::<String, i32>::new();
    println!("Cache created with automatic generic tracking");
    
    println!("\n=== METHOD CHAINING ===");
    let client = chaining_with_self::HttpClient::new("https://api.example.com".to_string())
        .timeout(60)
        .retries(5);
    println!("Client: {:?}", client);
    
    println!("\n=== MACRO GENERATION ===");
    let obj1 = MyType1::new(42);
    let obj2 = MyType2::new(100);
    println!("Generated types: {} and {}", obj1.value, obj2.value);
}

// ============================================================================
// SUMMARY: CONTROL BENEFITS
// ============================================================================

/*
USING Self GIVES YOU CONTROL OVER:

1. ✅ REFACTORING
   - Change type names in one place
   - Automatic propagation through impl blocks
   
2. ✅ GENERICS
   - Add/remove generic parameters easily
   - No need to update every method signature
   
3. ✅ MAINTENANCE
   - Less code to update
   - Fewer chances for typos
   
4. ✅ TYPE SAFETY
   - Compiler enforces correct type usage
   - Prevents accidental type narrowing
   
5. ✅ CONSISTENCY
   - All methods guaranteed to use correct type
   - Builder patterns work reliably
   
6. ✅ READABILITY
   - Intent is clearer: "returns this type"
   - Less visual clutter
   
7. ✅ MACROS & CODEGEN
   - Simpler macro implementations
   - More flexible code generation

NOT USING Self GIVES YOU:

1. ❌ MORE WORK
   - Manual tracking of type names
   - Update many locations for changes
   
2. ❌ MORE ERRORS
   - Easy to make typos
   - Possible type mismatches
   
3. ❌ LESS FLEXIBILITY
   - Hard to refactor
   - Difficult to add generics later
   
4. ⚠️ EXPLICITNESS (sometimes useful)
   - When you intentionally want different return types
   - When implementing conversion methods
   - When documentation needs very explicit types

VERDICT: Use Self in 95% of cases. Only use explicit types when you
specifically need a different type or for very specific documentation.
*/

I've created a comprehensive comparison showing the **control benefits** of using `Self` vs not using it! Here's the breakdown:

## **Key Control Benefits:**

### **1. Refactoring Control** 🔄
- **With Self**: Change type name in 2 places
- **Without Self**: Change type name in 7+ places (every method signature)

### **2. Generic Type Control** 🎯
- **With Self**: Add/remove generic parameters in ONE place (struct definition)
- **Without Self**: Update EVERY method signature manually

### **3. Maintenance Control** 🛠️
- **With Self**: Automatic type tracking, less prone to errors
- **Without Self**: Manual tracking, more typos and inconsistencies

### **4. Type Safety Control** 🔒
- **With Self**: Compiler prevents accidental type narrowing
- **Without Self**: Easy to accidentally use wrong generic type

### **5. Builder Pattern Control** ⛓️
- **With Self**: Method chains guaranteed to work
- **Without Self**: Fragile chains that break with type changes

### **6. Macro/Codegen Control** 🤖
- **With Self**: Simpler, more maintainable macros
- **Without Self**: Complex macros that must track type names

## **Real-World Impact:**

Imagine you have:
```rust
struct ApiClient { ... }
```

And later decide to make it generic:
```rust
struct ApiClient<A: AuthProvider> { ... }
```

- **With Self**: Change works automatically, all methods still compile ✅
- **Without Self**: Must manually update 10+ method signatures ❌

## **When NOT to use Self:**

- Converting between different types
- When you specifically need explicit documentation
- Intentionally returning a different type

**Bottom line**: Using `Self` gives you ~95% more control over your codebase evolution!

// ============================================================================
// COMPREHENSIVE GUIDE TO `Self` KEYWORD IN RUST
// ============================================================================

// `Self` is a type alias that refers to the type being implemented or defined.
// It's used in impl blocks, trait definitions, and trait implementations.

// ============================================================================
// 1. BASIC USAGE: Self in Struct Implementation
// ============================================================================

#[derive(Debug, Clone)]
struct Point {
    x: f64,
    y: f64,
}

impl Point {
    // ✅ CORRECT: Using Self as return type
    fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }
    
    // ❌ WITHOUT Self (still valid but verbose)
    fn new_verbose(x: f64, y: f64) -> Point {
        Point { x, y }
    }
    
    // ✅ CORRECT: Self as parameter type
    fn distance(&self, other: &Self) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }
    
    // ❌ WITHOUT Self (verbose)
    fn distance_verbose(&self, other: &Point) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }
    
    // ✅ CORRECT: Returning Self from method (builder pattern)
    fn translate(mut self, dx: f64, dy: f64) -> Self {
        self.x += dx;
        self.y += dy;
        self
    }
    
    // ✅ CORRECT: Self in associated functions
    fn origin() -> Self {
        Self { x: 0.0, y: 0.0 }
    }
}

// ============================================================================
// 2. Self IN GENERIC CONTEXTS
// ============================================================================

#[derive(Debug)]
struct Container<T> {
    value: T,
}

impl<T> Container<T> {
    // ✅ CORRECT: Self automatically includes the generic parameter
    fn new(value: T) -> Self {
        Self { value }
    }
    
    // ❌ WITHOUT Self (must explicitly specify generic)
    fn new_verbose(value: T) -> Container<T> {
        Container { value }
    }
    
    // ✅ CORRECT: Self in methods with generics
    fn map<U, F>(self, f: F) -> Container<U>
    where
        F: FnOnce(T) -> U,
    {
        Container {
            value: f(self.value),
        }
    }
    
    // ✅ CORRECT: Returning Self preserves the generic type
    fn replace(mut self, value: T) -> Self {
        self.value = value;
        self
    }
}

// ============================================================================
// 3. Self IN TRAIT DEFINITIONS
// ============================================================================

trait Cloneable {
    // ✅ CORRECT: Self represents the implementing type
    fn clone_self(&self) -> Self;
}

trait Builder {
    // ✅ CORRECT: Self as return type for builder pattern
    fn set_name(self, name: String) -> Self;
    fn set_age(self, age: u32) -> Self;
    fn build(self) -> Self;
}

// Implementing traits using Self
#[derive(Debug)]
struct Person {
    name: String,
    age: u32,
}

impl Builder for Person {
    fn set_name(mut self, name: String) -> Self {
        self.name = name;
        self
    }
    
    fn set_age(mut self, age: u32) -> Self {
        self.age = age;
        self
    }
    
    fn build(self) -> Self {
        self
    }
}

// ============================================================================
// 4. COMMON ERRORS AND WARNINGS
// ============================================================================

// ❌ ERROR: Cannot use Self outside impl block
// fn standalone_function() -> Self {  // ERROR: can't use `Self` outside of impl
//     Self { x: 0.0, y: 0.0 }
// }

struct Rectangle {
    width: f64,
    height: f64,
}

impl Rectangle {
    // ⚠️ WARNING: This compiles but Self is ambiguous in nested contexts
    fn create_nested() -> Self {
        struct Inner {
            value: i32,
        }
        
        // ✅ CORRECT: Self here refers to Rectangle, not Inner
        Self { width: 10.0, height: 20.0 }
    }
    
    // ❌ INCORRECT: Cannot use Self in a closure's return type annotation
    // fn with_closure() -> impl Fn() -> Self {
    //     || Self { width: 1.0, height: 1.0 }  // This works!
    // }
}

// ============================================================================
// 5. Self vs self (IMPORTANT DISTINCTION)
// ============================================================================

struct Counter {
    count: u32,
}

impl Counter {
    // `Self` (capital S) = the type Counter
    // `self` (lowercase s) = the instance of Counter
    
    fn new() -> Self {  // Self = Counter (type)
        Self { count: 0 }
    }
    
    fn increment(&mut self) {  // self = instance
        self.count += 1;
    }
    
    fn get(&self) -> u32 {  // &self = borrowed instance
        self.count
    }
    
    fn consume(self) -> u32 {  // self = owned instance
        self.count
    }
    
    // ✅ CORRECT: Using both Self and self
    fn reset(mut self) -> Self {
        self.count = 0;
        self
    }
}

// ============================================================================
// 6. Self IN TRAIT OBJECTS (ADVANCED)
// ============================================================================

trait Animal {
    fn make_sound(&self) -> String;
    
    // ❌ ERROR: Self cannot be used in trait object methods
    // fn clone_animal(&self) -> Self;  // ERROR: cannot be made into an object
}

// ✅ CORRECT: Use Box<dyn Trait> for trait objects
trait CloneableAnimal {
    fn make_sound(&self) -> String;
    fn clone_boxed(&self) -> Box<dyn CloneableAnimal>;
}

struct Dog;

impl CloneableAnimal for Dog {
    fn make_sound(&self) -> String {
        "Woof!".to_string()
    }
    
    fn clone_boxed(&self) -> Box<dyn CloneableAnimal> {
        Box::new(Dog)
    }
}

// ============================================================================
// 7. Self WITH ASSOCIATED TYPES
// ============================================================================

trait Graph {
    type Node;
    type Edge;
    
    fn add_node(&mut self, node: Self::Node);
    fn add_edge(&mut self, edge: Self::Edge);
    
    // ✅ CORRECT: Self refers to the implementing type
    fn clone_graph(&self) -> Self where Self: Sized;
}

// ============================================================================
// 8. PRACTICAL EXAMPLES: BUILDER PATTERN
// ============================================================================

#[derive(Debug)]
struct HttpRequest {
    url: String,
    method: String,
    headers: Vec<(String, String)>,
    body: Option<String>,
}

impl HttpRequest {
    // ✅ BEST PRACTICE: Using Self for fluent builder pattern
    fn new(url: String) -> Self {
        Self {
            url,
            method: "GET".to_string(),
            headers: Vec::new(),
            body: None,
        }
    }
    
    fn method(mut self, method: String) -> Self {
        self.method = method;
        self
    }
    
    fn header(mut self, key: String, value: String) -> Self {
        self.headers.push((key, value));
        self
    }
    
    fn body(mut self, body: String) -> Self {
        self.body = Some(body);
        self
    }
}

// ============================================================================
// 9. INCORRECT USAGE EXAMPLES
// ============================================================================

struct BadExample {
    value: i32,
}

impl BadExample {
    // ❌ INCORRECT: Mixing Self and explicit type unnecessarily
    fn confusing(self) -> BadExample {  // Should use Self
        Self { value: self.value }  // Inconsistent style
    }
    
    // ❌ INCORRECT: Cannot use Self in type parameters directly
    // fn with_vec() -> Vec<Self> {  // This actually works!
    //     vec![Self { value: 1 }]
    // }
}

// ============================================================================
// 10. BENEFITS OF USING Self
// ============================================================================

// Benefits:
// 1. DRY (Don't Repeat Yourself): Changes to type name don't require updating methods
// 2. Clarity: Makes it clear the method returns the same type
// 3. Generics: Automatically includes generic parameters
// 4. Refactoring: Easier to rename types

#[derive(Debug)]
struct LongComplexTypeName<T, U, V> {
    first: T,
    second: U,
    third: V,
}

impl<T, U, V> LongComplexTypeName<T, U, V> {
    // ✅ GOOD: Using Self is concise
    fn new(first: T, second: U, third: V) -> Self {
        Self { first, second, third }
    }
    
    // ❌ BAD: Without Self, very verbose
    fn new_verbose(first: T, second: U, third: V) -> LongComplexTypeName<T, U, V> {
        LongComplexTypeName { first, second, third }
    }
}

// ============================================================================
// MAIN: DEMONSTRATION
// ============================================================================

fn main() {
    println!("=== BASIC USAGE ===");
    let p1 = Point::new(3.0, 4.0);
    let p2 = Point::origin();
    println!("Distance: {}", p1.distance(&p2));
    
    println!("\n=== GENERICS ===");
    let container = Container::new(42);
    let mapped = container.map(|x| x * 2);
    println!("Mapped container: {:?}", mapped);
    
    println!("\n=== BUILDER PATTERN ===");
    let person = Person {
        name: String::new(),
        age: 0,
    }
    .set_name("Alice".to_string())
    .set_age(30)
    .build();
    println!("Person: {:?}", person);
    
    println!("\n=== HTTP REQUEST BUILDER ===");
    let request = HttpRequest::new("https://api.example.com".to_string())
        .method("POST".to_string())
        .header("Content-Type".to_string(), "application/json".to_string())
        .body("{\"key\": \"value\"}".to_string());
    println!("Request: {:?}", request);
    
    println!("\n=== Self vs self ===");
    let counter = Counter::new();  // Self used here
    let counter = counter.reset();  // self used here
    println!("Counter: {}", counter.get());
}

// ============================================================================
// KEY TAKEAWAYS
// ============================================================================

/*
1. `Self` (capital S) = Type alias for the implementing type
2. `self` (lowercase s) = Instance of the type

3. Use Self for:
   - Return types in constructors and methods
   - Parameter types
   - Generic type inference
   - Builder patterns

4. Cannot use Self:
   - Outside impl blocks
   - In trait object methods (non-object-safe)
   - In standalone functions

5. Benefits:
   - Less verbose, especially with generics
   - Easier refactoring
   - Clearer intent
   - Better maintainability

6. Self automatically includes all generic parameters
7. Self and explicit type names can be mixed, but consistency is better
*/

I'll create a comprehensive guide to the `Self` keyword in Rust with complete implementations and examples.

I've created a comprehensive guide to the `Self` keyword in Rust! Here's what's covered:

## **Contents:**

1. **Basic Usage** - Using `Self` in struct implementations vs. verbose explicit types
2. **Generic Contexts** - How `Self` automatically includes generic parameters
3. **Trait Definitions** - Using `Self` in trait methods
4. **Common Errors & Warnings** - What doesn't work and why
5. **Self vs self** - Critical distinction between type (Self) and instance (self)
6. **Trait Objects** - Why `Self` can't be used with trait objects
7. **Associated Types** - Using `Self` with associated types
8. **Builder Pattern** - Practical implementation using `Self`
9. **Incorrect Usage** - Anti-patterns to avoid
10. **Benefits** - Why you should use `Self`

## **Key Points:**

- **`Self`** (capital S) = Type alias for the implementing type
- **`self`** (lowercase s) = Instance of the type

The guide includes working examples you can compile and run, showing both correct and incorrect usage patterns. Each section has clear markers (✅ CORRECT, ❌ ERROR, ⚠️ WARNING) to help you understand best practices.

The main function demonstrates all concepts in action, including builder patterns, generics, and method chaining - all common patterns where `Self` shines!

===========================================================================

That's a concise and accurate description! `Self` is indeed a type alias that refers to the current type being defined or implemented. This is a common feature in many programming languages, particularly those with strong type systems.

Here are some key aspects of how `Self` typically works:

**In trait/interface implementations:**
```rust
// Rust example
trait Clone {
    fn clone(&self) -> Self;  // Self refers to the implementing type
}

impl Clone for MyStruct {
    fn clone(&self) -> Self {  // Self = MyStruct here
        MyStruct { /* ... */ }
    }
}
```

**In class definitions:**
```python
# Python example
class Builder:
    def add_item(self, item: str) -> Self:  # Self refers to Builder
        self.items.append(item)
        return self  # Enables method chaining
```

**Key benefits:**
- **DRY principle**: Avoids repeating the type name
- **Refactoring safety**: If you rename the type, `Self` automatically updates
- **Generic flexibility**: Works correctly in inheritance hierarchies
- **Method chaining**: Common in builder patterns where methods return `Self`

The exact syntax and capabilities vary by language (Rust, Python, Swift, etc.), but the core concept remains consistent: `Self` is a placeholder that gets resolved to whatever type is currently being defined or implemented.

Exactly ✅

In Rust, **`Self`** (with capital **S**) is a **type alias** inside an `impl` block or trait definition that refers to **the type currently being implemented or defined**.

---

## 1. Basic Example with `impl`

```rust
struct Point {
    x: i32,
    y: i32,
}

impl Point {
    fn new(x: i32, y: i32) -> Self {
        Self { x, y }
    }

    fn move_x(self, dx: i32) -> Self {
        Self { x: self.x + dx, y: self.y }
    }
}
```

Here:

* `Self` = `Point` (the struct being implemented).
* `Self { x, y }` is just shorthand for `Point { x, y }`.

---

## 2. Inside Traits

```rust
trait Double {
    fn double(self) -> Self;  // returns the same type
}

impl Double for i32 {
    fn double(self) -> Self {
        self * 2
    }
}
```

* In the trait: `Self` = “the type that implements this trait.”
* In the impl for `i32`: `Self` = `i32`.

---

## 3. Associated Types with `Self`

```rust
trait IntoIterator {
    type Item;

    fn next(&mut self) -> Option<Self::Item>;
}
```

Here:

* `Self` refers to the **type implementing `IntoIterator`**.
* `Self::Item` is an associated type belonging to that implementer.

---

## 4. Difference: `Self` vs `self`

* **`Self`** = the **type** being defined (e.g., `Point`, `i32`, etc.).
* **`self`** = the **current instance** of that type (a method argument).

```rust
impl Point {
    fn print(&self) { // <-- lowercase self (the value)
        println!("({}, {})", self.x, self.y);
    }

    fn new(x: i32, y: i32) -> Self { // <-- uppercase Self (the type)
        Self { x, y }
    }
}
```

---

## 🌳 Summary

* **`Self`** = type alias for the type being implemented.
* **`self`** = instance of that type in methods.
* Useful for:

  * Returning the same type (`fn new() -> Self`)
  * Referring to associated types (`Self::Item`)
  * Reducing repetition in `impl` blocks.

---

👉 Want me to also show how `Self` is used in **recursive types** (like `Box<Self>` in linked lists)? That’s a classic place where it becomes important.
