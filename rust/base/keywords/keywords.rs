Appendix A: Keywords

The following list contains keywords that are reserved for current or future use by the Rust language. As such, they cannot be used as identifiers (except as raw identifiers as we’ll discuss in the “Raw Identifiers” section). Identifiers are names of functions, variables, parameters, struct fields, modules, crates, constants, macros, static values, attributes, types, traits, or lifetimes.
Keywords Currently in Use

The following is a list of keywords currently in use, with their functionality described.

    as - perform primitive casting, disambiguate the specific trait containing an item, or rename items in use statements
    async - return a Future instead of blocking the current thread
    await - suspend execution until the result of a Future is ready
    break - exit a loop immediately
    const - define constant items or constant raw pointers
    continue - continue to the next loop iteration
    crate - in a module path, refers to the crate root
    dyn - dynamic dispatch to a trait object
    else - fallback for if and if let control flow constructs
    enum - define an enumeration
    extern - link an external function or variable
    false - Boolean false literal
    fn - define a function or the function pointer type
    for - loop over items from an iterator, implement a trait, or specify a higher-ranked lifetime
    if - branch based on the result of a conditional expression
    impl - implement inherent or trait functionality
    in - part of for loop syntax
    let - bind a variable
    loop - loop unconditionally
    match - match a value to patterns
    mod - define a module
    move - make a closure take ownership of all its captures
    mut - denote mutability in references, raw pointers, or pattern bindings
    pub - denote public visibility in struct fields, impl blocks, or modules
    ref - bind by reference
    return - return from function
    Self - a type alias for the type we are defining or implementing
    self - method subject or current module
    static - global variable or lifetime lasting the entire program execution
    struct - define a structure
    super - parent module of the current module
    trait - define a trait
    true - Boolean true literal
    type - define a type alias or associated type
    union - define a union; is only a keyword when used in a union declaration
    unsafe - denote unsafe code, functions, traits, or implementations
    use - bring symbols into scope; specify precise captures for generic and lifetime bounds
    where - denote clauses that constrain a type
    while - loop conditionally based on the result of an expression

Keywords Reserved for Future Use

The following keywords do not yet have any functionality but are reserved by Rust for potential future use.

    abstract
    become
    box
    do
    final
    gen
    macro
    override
    priv
    try
    typeof
    unsized
    virtual
    yield


Here is a complete list of **Rust keywords**, categorized for clarity:

---

### **Strict Keywords (reserved for language features)**

These **cannot** be used as identifiers:

```
as          break       const       continue    crate
else        enum        extern      false       fn
for         if          impl        in          let
loop        match       mod         move        mut
pub         ref         return      self        Self
static      struct      super       trait       true
type        unsafe      use         where       while
async       await       dyn
```

---

### **Reserved Keywords (not currently used but reserved for future use)**

These cannot be used either, to avoid breaking future Rust versions:

```
abstract    become      box         do
final       macro       override    priv
try         typeof      unsized     virtual
yield
```

---

### **Strict Contextual Keywords (have meaning only in specific contexts)**

These **can be used as identifiers** unless in specific syntactic positions:

```
union       'static     macro_rules
```

---

### **Other Contextual Keywords**

Used in particular scenarios, but otherwise allowed as identifiers:

```
auto        default     union       catch       async
await       dyn
```

---

### Bonus: **Primitive Types as Keywords**

These types are reserved names:

```
bool        char        str
u8  u16 u32 u64 u128 usize
i8  i16 i32 i64 i128 isize
f32 f64
```

---

### Summary

* **Strict keywords**: Always reserved.
* **Reserved keywords**: Future-proof, reserved but not yet used.
* **Contextual keywords**: Special meaning in certain syntax only.
* **Primitive types**: Treated as keywords.

Let me know if you want explanations or examples of any specific keyword!

Here’s a **meaning and usage guide for the most important Rust keywords**, categorized for better understanding:

---

## 🟩 **Control Flow**

| Keyword    | Meaning / Usage                 | Example                                  |
| ---------- | ------------------------------- | ---------------------------------------- |
| `if`       | Conditional branching           | `if x > 0 { ... }`                       |
| `else`     | Alternative branch              | `if x > 0 { ... } else { ... }`          |
| `match`    | Pattern matching                | `match num { 1 => "one", _ => "other" }` |
| `loop`     | Infinite loop                   | `loop { ... }`                           |
| `while`    | Conditional loop                | `while x < 10 { ... }`                   |
| `for`      | Iterator loop                   | `for i in 0..5 { ... }`                  |
| `break`    | Exit a loop early               | `break;`                                 |
| `continue` | Skip to the next loop iteration | `continue;`                              |
| `return`   | Return from a function          | `return 42;`                             |

---

## 🟩 **Variable Binding**

| Keyword  | Meaning / Usage                                              | Example                       |   |                         |
| -------- | ------------------------------------------------------------ | ----------------------------- | - | ----------------------- |
| `let`    | Declare a variable                                           | `let x = 5;`                  |   |                         |
| `mut`    | Make a variable mutable                                      | `let mut x = 5;`              |   |                         |
| `const`  | Declare a constant                                           | `const PI: f64 = 3.14;`       |   |                         |
| `static` | Declare a static variable (global, fixed location in memory) | `static NAME: &str = "Rust";` |   |                         |
| `move`   | Transfer ownership                                           | \`let closure = move          |   | println!("{}", name);\` |

---

## 🟩 **Functions and Types**

| Keyword  | Meaning / Usage                    | Example                                      |
| -------- | ---------------------------------- | -------------------------------------------- |
| `fn`     | Define a function                  | `fn add(x: i32, y: i32) -> i32 { x + y }`    |
| `impl`   | Implement methods for a type       | `impl MyStruct { fn new() -> Self { ... } }` |
| `struct` | Define a struct                    | `struct Point { x: i32, y: i32 }`            |
| `enum`   | Define an enum                     | `enum Direction { North, South }`            |
| `trait`  | Define a trait (like an interface) | `trait Speak { fn speak(&self); }`           |
| `type`   | Create a type alias                | `type Kilometers = i32;`                     |
| `dyn`    | Dynamic dispatch for trait objects | `let x: &dyn Speak = ...;`                   |

---

## 🟩 **Modules and Visibility**

| Keyword | Meaning / Usage              | Example                        |
| ------- | ---------------------------- | ------------------------------ |
| `mod`   | Define a module              | `mod math { pub fn add() {} }` |
| `pub`   | Make an item public          | `pub fn open() {}`             |
| `use`   | Import modules or items      | `use std::io;`                 |
| `crate` | Reference the current crate  | `crate::utils::helper();`      |
| `super` | Reference the parent module  | `super::parent_func();`        |
| `self`  | Reference the current module | `self::inner();`               |

---

## 🟩 **Error Handling**

| Keyword  | Meaning / Usage                            | Example                   |
| -------- | ------------------------------------------ | ------------------------- |
| `unsafe` | Allow operations that bypass safety checks | `unsafe { dangerous(); }` |
| `as`     | Type casting                               | `let y = x as f64;`       |
| `ref`    | Bind by reference in patterns              | `let ref x = y;`          |

---

## 🟩 **Concurrency and Asynchronous Programming**

| Keyword | Meaning / Usage                          | Example               |
| ------- | ---------------------------------------- | --------------------- |
| `async` | Define an asynchronous function or block | `async fn fetch() {}` |
| `await` | Wait for an async operation to complete  | `fetch().await;`      |

---

## 🟩 **Boolean Values**

| Keyword | Meaning / Usage | Example             |
| ------- | --------------- | ------------------- |
| `true`  | Boolean true    | `let flag = true;`  |
| `false` | Boolean false   | `let flag = false;` |

---

## 🟩 **Generics and Constraints**

| Keyword | Meaning / Usage             | Example                                    |
| ------- | --------------------------- | ------------------------------------------ |
| `where` | Add constraints to generics | `fn foo<T: Clone>(x: T) where T: Debug {}` |

---

## 🟩 **Special Keywords**

| Keyword | Meaning / Usage           | Example                                         |
| ------- | ------------------------- | ----------------------------------------------- |
| `Self`  | Refers to the type itself | `impl MyStruct { fn create() -> Self { ... } }` |

---

## ✅ **Summary**

Rust keywords help with:

* **Control flow:** `if`, `else`, `match`, `loop`, etc.
* **Variable and memory management:** `let`, `mut`, `move`, `ref`
* **Type and trait definition:** `struct`, `enum`, `trait`, `impl`
* **Modules and scope:** `mod`, `pub`, `use`, `self`, `super`, `crate`
* **Concurrency:** `async`, `await`
* **Safety and low-level control:** `unsafe`, `as`

---

If you want **examples with code for each keyword**, I can generate a complete guide — just let me know!

I'll provide a comprehensive overview of Rust keywords and their usage with real-world examples that align with your backend development experience.I've created a comprehensive Rust keywords reference guide tailored to your backend development experience with Django, TypeScript, and security-focused development.

## Key Highlights for Your Background:

**Memory Safety & Performance**: Rust's ownership system (`let`, `mut`, `move`) provides compile-time memory safety without garbage collection - making it excellent for high-performance web services that complement your Django backend.

**Type System**: Similar to TypeScript's type safety but at the system level. The `struct`, `enum`, `trait`, and `impl` keywords create a powerful type system that prevents many runtime errors.

**Async Programming**: The `async`/`await` pattern works similarly to your TypeScript/JavaScript experience but with zero-cost abstractions and better performance than Python's asyncio.

**Security by Design**: Rust's compiler prevents buffer overflows, null pointer dereferences, and race conditions - addressing security concerns at compile time rather than runtime.

## Real-World Applications for Your Stack:

1. **High-Performance API Gateway**: Replace nginx with a Rust-based proxy for better performance
2. **Microservices**: Build fast, secure microservices that complement your Django monolith
3. **WebSocket Servers**: Replace Django Channels with Rust for better WebSocket performance
4. **CLI Tools**: Build deployment and database migration tools
5. **System Services**: Background job processors, message queues, caching layers

The ownership model and pattern matching (`match`) are Rust's unique features that provide both performance and safety guarantees your current stack can benefit from. Would you like me to dive deeper into any specific keyword or show how to integrate Rust services with your existing Django/NextJS architecture?

# Rust Keywords Reference Guide

## Memory Management & Ownership Keywords

### `let` - Variable Binding
```rust
// Immutable by default (similar to const in TypeScript)
let user_id = 123;
let username = "john_doe";

// Type annotation (like TypeScript)
let balance: f64 = 100.50;
```

### `mut` - Mutable Variables
```rust
// Similar to let in TypeScript/JavaScript
let mut balance = 100.0;
balance += 50.0; // Now we can modify it

// Real-world: Django session modification
let mut session_data = HashMap::new();
session_data.insert("user_id", "123");
```

### `const` - Compile-time Constants
```rust
// Similar to const in TypeScript but evaluated at compile time
const MAX_CONNECTIONS: u32 = 1000;
const API_VERSION: &str = "v1";

// Usage in web server config (like nginx.conf constants)
const REQUEST_TIMEOUT: u64 = 30; // seconds
```

### `static` - Static Variables
```rust
// Global state (like Django settings)
static mut GLOBAL_CONFIG: Option<Config> = None;
static DATABASE_URL: &str = "postgresql://localhost/mydb";
```

## Control Flow Keywords

### `if`, `else` - Conditionals
```rust
// Similar to TypeScript but expressions return values
let status = if user.is_authenticated() {
    "authenticated"
} else {
    "guest"
};

// Real-world: API response logic
let response = if user.has_permission("read") {
    HttpResponse::Ok().json(&data)
} else {
    HttpResponse::Forbidden().json("Access denied")
};
```

### `match` - Pattern Matching
```rust
// Like switch in TypeScript but more powerful
match user.role {
    Role::Admin => grant_full_access(),
    Role::User => grant_limited_access(),
    Role::Guest => deny_access(),
}

// Real-world: HTTP status handling
match response.status() {
    200..=299 => process_success(response),
    400..=499 => handle_client_error(response),
    500..=599 => handle_server_error(response),
    _ => handle_unknown_error(response),
}
```

### `loop` - Infinite Loop
```rust
// WebSocket connection handler (like Django Channels)
loop {
    match websocket.receive().await {
        Ok(message) => process_message(message).await,
        Err(_) => break, // Connection lost
    }
}
```

### `while` - Conditional Loop
```rust
// Processing queue (like Redis job queue)
while let Some(job) = job_queue.pop() {
    process_job(job).await;
}
```

### `for` - Iterator Loop
```rust
// Similar to Python for loop
for user in users {
    send_notification(&user).await;
}

// Real-world: Processing Django queryset equivalent
for order in Order::find_pending() {
    process_payment(&order).await;
}
```

### `break`, `continue` - Loop Control
```rust
// Same as Python/TypeScript
for request in incoming_requests {
    if !request.is_valid() {
        continue; // Skip invalid requests
    }
    if should_stop_processing() {
        break; // Stop processing
    }
    handle_request(request).await;
}
```

## Function & Method Keywords

### `fn` - Function Definition
```rust
// Similar to function in TypeScript
fn calculate_tax(amount: f64) -> f64 {
    amount * 0.1
}

// Real-world: API endpoint handler
async fn create_user(user_data: CreateUserRequest) -> ApiResponse {
    // Like Django REST framework view
    let user = User::create(user_data).await?;
    ApiResponse::created(user)
}
```

### `return` - Early Return
```rust
fn validate_user(token: &str) -> Result<User, AuthError> {
    if token.is_empty() {
        return Err(AuthError::InvalidToken);
    }
    
    // Similar to Django authentication
    decode_jwt_token(token)
}
```

## Module & Visibility Keywords

### `mod` - Module Declaration
```rust
// Similar to modules in TypeScript
mod database {
    pub mod models;
    pub mod migrations;
}

// Real-world: Django app structure
mod users {
    pub mod models;
    pub mod views;
    pub mod serializers;
}
```

### `use` - Import Items
```rust
// Similar to import in TypeScript
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

// Real-world: Django-like imports
use crate::models::User;
use crate::auth::middleware::AuthMiddleware;
```

### `pub` - Public Visibility
```rust
// Similar to export in TypeScript
pub struct User {
    pub id: u64,
    pub username: String,
    email: String, // Private field
}

// Real-world: API response model
#[derive(Serialize)]
pub struct UserResponse {
    pub id: u64,
    pub username: String,
    // email excluded for security
}
```

### `crate` - Crate Root Reference
```rust
// Reference to current crate root
use crate::models::User;
use crate::utils::hash_password;

// Like absolute imports in Django
```

### `super` - Parent Module Reference
```rust
// Similar to ../  in relative imports
use super::models::User;
use super::super::config::DATABASE_URL;
```

### `self` - Current Module/Instance Reference
```rust
// Current module
use self::models::User;

// Instance method (like self in Python)
impl User {
    pub fn update_email(&mut self, new_email: String) {
        self.email = new_email;
    }
}
```

## Type Definition Keywords

### `struct` - Structure Definition
```rust
// Similar to interface in TypeScript
#[derive(Serialize, Deserialize)]
struct User {
    id: u64,
    username: String,
    email: String,
    created_at: DateTime<Utc>,
}

// Real-world: Django model equivalent
struct Order {
    id: Uuid,
    user_id: u64,
    amount: Decimal,
    status: OrderStatus,
}
```

### `enum` - Enumeration
```rust
// More powerful than TypeScript enums
#[derive(Serialize, Deserialize)]
enum OrderStatus {
    Pending,
    Processing,
    Completed,
    Cancelled,
}

// Real-world: API response types
enum ApiResponse<T> {
    Success(T),
    Error { code: u16, message: String },
    ValidationError(Vec<String>),
}
```

### `impl` - Implementation Block
```rust
// Like class methods in TypeScript
impl User {
    // Constructor (like Django model manager)
    pub fn new(username: String, email: String) -> Self {
        User {
            id: generate_id(),
            username,
            email,
            created_at: Utc::now(),
        }
    }
    
    // Method (like Django model method)
    pub fn is_admin(&self) -> bool {
        self.username == "admin"
    }
}
```

### `trait` - Interface Definition
```rust
// Similar to interface in TypeScript
trait Authenticatable {
    fn authenticate(&self, password: &str) -> bool;
    fn generate_token(&self) -> String;
}

// Real-world: Django-like authentication
impl Authenticatable for User {
    fn authenticate(&self, password: &str) -> bool {
        verify_password(password, &self.password_hash)
    }
    
    fn generate_token(&self) -> String {
        create_jwt_token(self.id)
    }
}
```

### `type` - Type Alias
```rust
// Similar to type in TypeScript
type UserId = u64;
type Result<T> = std::result::Result<T, ApiError>;

// Real-world: Database types
type DatabaseConnection = diesel::PgConnection;
type ApiResult<T> = Result<T, ApiError>;
```

## Async/Concurrency Keywords

### `async` - Asynchronous Function
```rust
// Similar to async in TypeScript
async fn fetch_user(id: UserId) -> Result<User> {
    let connection = get_db_connection().await?;
    User::find_by_id(&connection, id).await
}

// Real-world: API endpoint
async fn create_order(order_data: CreateOrderRequest) -> ApiResponse {
    let user = authenticate_user(&order_data.token).await?;
    let order = Order::create(user.id, order_data).await?;
    ApiResponse::created(order)
}
```

### `await` - Await Future
```rust
// Same as await in TypeScript
let user = User::find_by_id(123).await?;
let orders = user.get_orders().await?;

// Real-world: Multiple async operations
let user_future = fetch_user(user_id);
let orders_future = fetch_orders(user_id);
let (user, orders) = tokio::join!(user_future, orders_future);
```

## Memory Safety Keywords

### `unsafe` - Unsafe Code Block
```rust
// Bypasses Rust's safety checks (use carefully)
unsafe {
    // Raw pointer operations
    let raw_ptr = ptr::null_mut();
    // FFI calls to C libraries
    let result = some_c_function(raw_ptr);
}

// Real-world: Interfacing with system libraries
unsafe fn allocate_buffer(size: usize) -> *mut u8 {
    libc::malloc(size) as *mut u8
}
```

### `ref` - Reference Patterns
```rust
// Pattern matching with references
match &user.role {
    ref admin_role if admin_role == &Role::Admin => {
        // Handle admin
    }
    _ => {}
}
```

## Macro Keywords

### `macro_rules!` - Macro Definition
```rust
// Define reusable code patterns
macro_rules! create_api_response {
    ($status:expr, $data:expr) => {
        ApiResponse {
            status: $status,
            data: $data,
            timestamp: Utc::now(),
        }
    };
}

// Usage
let response = create_api_response!("success", user);
```

## Error Handling Keywords

### `Result` Type with `?` Operator
```rust
// Built-in error handling (like try-catch but functional)
fn process_payment(order: &Order) -> Result<Payment, PaymentError> {
    let user = User::find_by_id(order.user_id)?; // Early return on error
    let payment_method = user.get_payment_method()?;
    charge_payment(payment_method, order.amount)
}

// Real-world: API endpoint error handling
async fn handle_request(req: HttpRequest) -> Result<HttpResponse, ApiError> {
    let auth_token = extract_token(&req)?;
    let user = authenticate(auth_token).await?;
    let data = process_request(&user, req).await?;
    Ok(HttpResponse::Ok().json(data))
}
```

## Advanced Keywords

### `where` - Generic Constraints
```rust
// Type constraints (like generic constraints in TypeScript)
fn save_entity<T>(entity: T) -> Result<()>
where
    T: Serialize + Send + Sync,
{
    let json = serde_json::to_string(&entity)?;
    database::save(&json).await
}
```

### `dyn` - Dynamic Trait Objects
```rust
// Runtime polymorphism
fn process_payment(processor: Box<dyn PaymentProcessor>) -> Result<Payment> {
    processor.charge()
}

// Real-world: Multiple payment gateways (like Stripe integration)
let processor: Box<dyn PaymentProcessor> = match gateway {
    "stripe" => Box::new(StripeProcessor::new()),
    "paypal" => Box::new(PaypalProcessor::new()),
    _ => return Err("Unsupported gateway"),
};
```

### `move` - Move Closure
```rust
// Transfer ownership to closure (important for async tasks)
let user_id = 123;
tokio::spawn(move || async move {
    // user_id is moved into this async block
    process_user_data(user_id).await;
});

// Real-world: Background job processing
let notification_data = NotificationData::new();
tokio::spawn(move || async move {
    send_email_notification(notification_data).await;
});
```

## Real-World Architecture Examples

### Web Server Setup (Similar to Django + DRF)
```rust
// Main application structure
#[tokio::main]
async fn main() -> Result<()> {
    let app = Router::new()
        .route("/api/users", post(create_user))
        .route("/api/users/:id", get(get_user))
        .layer(AuthMiddleware::new());
    
    let listener = TcpListener::bind("0.0.0.0:8000").await?;
    serve(listener, app).await
}

// Middleware (like Django middleware)
async fn auth_middleware(
    req: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    let token = extract_bearer_token(&req)?;
    let user = authenticate_token(token).await?;
    
    // Add user to request context
    req.extensions_mut().insert(user);
    Ok(next.run(req).await)
}
```

### Database Integration (PostgreSQL like Django ORM)
```rust
// Model definition
#[derive(Queryable, Insertable, Serialize)]
struct User {
    pub id: i32,
    pub username: String,
    pub email: String,
    pub created_at: NaiveDateTime,
}

// Repository pattern (like Django managers)
impl User {
    pub async fn create(conn: &mut PgConnection, data: CreateUserData) -> Result<User> {
        diesel::insert_into(users::table)
            .values(&data)
            .get_result(conn)
            .await
    }
    
    pub async fn find_by_email(conn: &mut PgConnection, email: &str) -> Result<Option<User>> {
        users::table
            .filter(users::email.eq(email))
            .first(conn)
            .await
            .optional()
    }
}
```

## Security Best Practices (Your Priority)

### Input Validation
```rust
// Strict type checking prevents many security issues
#[derive(Deserialize, Validate)]
struct CreateUserRequest {
    #[validate(length(min = 3, max = 50))]
    pub username: String,
    
    #[validate(email)]
    pub email: String,
    
    #[validate(length(min = 8))]
    pub password: String,
}

// Validation in handler
async fn create_user(Json(data): Json<CreateUserRequest>) -> Result<ApiResponse> {
    data.validate()?; // Automatic validation
    
    // Hash password before storing (like Django's make_password)
    let hashed_password = hash_password(&data.password)?;
    
    let user = User::create(CreateUserData {
        username: data.username,
        email: data.email,
        password_hash: hashed_password,
    }).await?;
    
    Ok(ApiResponse::created(user))
}
```

### SQL Injection Prevention
```rust
// Diesel ORM prevents SQL injection automatically
let users = users::table
    .filter(users::email.eq(email)) // Parameterized query
    .load::<User>(&mut conn)
    .await?;

// Raw queries are still safe with parameters
let result = sql_query("SELECT * FROM users WHERE email = $1")
    .bind::<Text, _>(email)
    .load::<User>(&mut conn)
    .await?;
```

This comprehensive guide covers all Rust keywords with practical examples relevant to your Django/NextJS/TypeScript background. The ownership system and type safety in Rust provides even stronger security guarantees than your current stack, making it excellent for system-level programming and high-performance web services.

Here’s a **clear explanation of all Rust keywords**, with practical insights to help you actually understand their role—not just memorize them.

---

## 🛑 **Strict Keywords** (Always Reserved)

These are the backbone of Rust’s syntax. You **cannot** use them as variable names or identifiers.

| **Keyword** | **Meaning / Purpose**                               |
| ----------- | --------------------------------------------------- |
| `as`        | Type casting. Example: `x as u32`.                  |
| `break`     | Exit a loop early.                                  |
| `const`     | Define constants. Example: `const MAX: u32 = 100;`. |
| `continue`  | Skip current loop iteration.                        |
| `crate`     | Refers to the current library or binary package.    |
| `else`      | Used with `if` for alternatives.                    |
| `enum`      | Define enumerated types (like C enums).             |
| `extern`    | Link to external code (like C libraries).           |
| `false`     | Boolean false literal.                              |
| `fn`        | Declare a function.                                 |
| `for`       | Loop through iterators.                             |
| `if`        | Conditional branching.                              |
| `impl`      | Implement methods or traits for a type.             |
| `in`        | Used in `for` loops, like `for x in y`.             |
| `let`       | Bind a variable.                                    |
| `loop`      | Infinite loop.                                      |
| `match`     | Pattern matching (like switch-case).                |
| `mod`       | Define a module.                                    |
| `move`      | Capture variables by value in closures.             |
| `mut`       | Make variables mutable.                             |
| `pub`       | Make functions, structs, etc., public.              |
| `ref`       | Create a reference inside pattern matching.         |
| `return`    | Exit a function and return a value.                 |
| `self`      | Current instance (like `this` in other languages).  |
| `Self`      | Refers to the implementing type itself.             |
| `static`    | Static variable or lifetime.                        |
| `struct`    | Define a structure.                                 |
| `super`     | Parent module path.                                 |
| `trait`     | Define shared behavior (interfaces).                |
| `true`      | Boolean true literal.                               |
| `type`      | Define type aliases.                                |
| `unsafe`    | Enable unsafe code (manual memory control, etc.).   |
| `use`       | Bring modules, traits, or types into scope.         |
| `where`     | Add constraints to generics.                        |
| `while`     | While loops.                                        |
| `async`     | Declare asynchronous functions.                     |
| `await`     | Wait for an async operation to complete.            |
| `dyn`       | Used with dynamic dispatch (e.g., `dyn Trait`).     |

---

## 🕑 **Reserved for Future Use**

These words are reserved but **not yet implemented**. Rust prevents you from using them to avoid breaking future features.

```
abstract, become, box, do, final, macro, override, priv,
try, typeof, unsized, virtual, yield
```

> Example: You cannot write:
>
> ```rust
> let try = 5;  // Error! 'try' is reserved.
> ```

---

## ⚙️ **Strict Contextual Keywords**

Only act like keywords in **certain contexts**. Outside those, you can use them as normal variable names.

| **Keyword**    | **Meaning**                                            |
| -------------- | ------------------------------------------------------ |
| `union`        | Define a union (C-style data structure).               |
| `'static`      | A special lifetime meaning "lives for entire program". |
| `macro_rules!` | Used to define declarative macros.                     |

---

## ⚙️ **Other Contextual Keywords**

Used specifically in some places. Generally safe to use as identifiers elsewhere.

| **Keyword** | **Meaning**                             |
| ----------- | --------------------------------------- |
| `auto`      | Related to trait implementation (rare). |
| `default`   | Set default trait implementations.      |
| `catch`     | Used in error handling (future use).    |
| `union`     | (Same as above.)                        |
| `async`     | (As explained.)                         |
| `await`     | (As explained.)                         |
| `dyn`       | (As explained.)                         |

---

## 📦 **Primitive Types (Treated Like Keywords)**

These are **primitive types** but treated like keywords:

* **Booleans:** `bool`
* **Characters:** `char`
* **String slices:** `str`
* **Unsigned Integers:** `u8`, `u16`, `u32`, `u64`, `u128`, `usize`
* **Signed Integers:** `i8`, `i16`, `i32`, `i64`, `i128`, `isize`
* **Floating Points:** `f32`, `f64`

Example:

```rust
let age: u32 = 25;
let pi: f64 = 3.1415;
let letter: char = 'A';
```

---

## ✅ **Summary**

| **Category**      | **Can Be Used as Variable?** | **Purpose** |
| ----------------- | ---------------------------- | ----------- |
| Strict Keywords   | ❌ No                         | Core syntax |
| Reserved Keywords | ❌ No                         | Future use  |
| Strict Contextual | ⚠️ Depends                   | Contextual  |
| Other Contextual  | ⚠️ Depends                   | Contextual  |
| Primitive Types   | ❌ No                         | Types       |

---

## 📌 Want practical code examples for any of these?

Let me know what you’re focusing on (functions, traits, lifetimes, etc.), and I’ll walk you through real use cases.
