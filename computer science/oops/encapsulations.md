# Comprehensive Guide to Encapsulation in Object-Oriented Programming

## Table of Contents
1. [What is Encapsulation?](#what-is-encapsulation)
2. [Why Encapsulation Matters](#why-encapsulation-matters)
3. [Levels of Access Control](#levels-of-access-control)
4. [Python Implementation](#python-implementation)
5. [Rust Implementation](#rust-implementation)
6. [Advanced Patterns](#advanced-patterns)
7. [Best Practices](#best-practices)
8. [Common Pitfalls](#common-pitfalls)

## What is Encapsulation?

Encapsulation is one of the four fundamental principles of Object-Oriented Programming (along with Inheritance, Polymorphism, and Abstraction). It refers to the bundling of data (attributes) and methods (functions) that operate on that data into a single unit (class), while restricting direct access to some of the object's components.

### Core Concepts:
- **Data Hiding**: Concealing internal implementation details from the outside world
- **Access Control**: Controlling how data and methods can be accessed and modified
- **Interface Design**: Providing a clean, controlled way to interact with objects

## Why Encapsulation Matters

### 1. **Data Integrity**
Prevents external code from putting objects into invalid states by controlling how data is modified.

### 2. **Maintainability** 
Internal implementation can be changed without affecting external code that uses the class.

### 3. **Security**
Sensitive data and operations can be hidden from unauthorized access.

### 4. **Code Organization**
Related data and methods are grouped together logically.

### 5. **Debugging**
Easier to track down bugs when data access is controlled and predictable.

## Levels of Access Control

### Public
- Accessible from anywhere
- Forms the public interface of the class

### Protected
- Accessible within the class and its subclasses
- Used for inheritance-related functionality

### Private
- Accessible only within the same class
- Used for internal implementation details

## Python Implementation

Python uses naming conventions to indicate access levels, as it doesn't have strict access modifiers like some other languages.

### Basic Encapsulation Example

```python
class BankAccount:
    def __init__(self, account_holder, initial_balance=0):
        self.account_holder = account_holder  # Public
        self._account_number = self._generate_account_number()  # Protected
        self.__balance = initial_balance  # Private
        self.__transaction_history = []  # Private
    
    def _generate_account_number(self):
        """Protected method - indicated by single underscore"""
        import random
        return f"ACC{random.randint(100000, 999999)}"
    
    def __validate_amount(self, amount):
        """Private method - indicated by double underscore"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return True
    
    def deposit(self, amount):
        """Public method"""
        self.__validate_amount(amount)
        self.__balance += amount
        self.__transaction_history.append(f"Deposited: ${amount}")
        return f"Deposited ${amount}. New balance: ${self.__balance}"
    
    def withdraw(self, amount):
        """Public method"""
        self.__validate_amount(amount)
        if amount > self.__balance:
            raise ValueError("Insufficient funds")
        self.__balance -= amount
        self.__transaction_history.append(f"Withdrew: ${amount}")
        return f"Withdrew ${amount}. New balance: ${self.__balance}"
    
    def get_balance(self):
        """Public method to access private balance"""
        return self.__balance
    
    def get_transaction_history(self):
        """Public method to access private transaction history"""
        return self.__transaction_history.copy()  # Return copy to prevent modification
    
    @property
    def account_info(self):
        """Property for read-only access to account information"""
        return {
            'holder': self.account_holder,
            'account_number': self._account_number,
            'balance': self.__balance
        }

# Usage Example
account = BankAccount("John Doe", 1000)
print(account.deposit(500))  # Deposited $500. New balance: $1500
print(account.withdraw(200))  # Withdrew $200. New balance: $1300
print(f"Current balance: ${account.get_balance()}")  # Current balance: $1300

# Accessing protected member (possible but discouraged)
print(f"Account Number: {account._account_number}")

# Accessing private member (name mangling makes it difficult)
# print(account.__balance)  # This would cause an AttributeError
# But you can still access it with name mangling:
# print(account._BankAccount__balance)  # Not recommended!
```

### Advanced Python Encapsulation with Properties

```python
class Temperature:
    def __init__(self, celsius=0):
        self.__celsius = celsius
    
    @property
    def celsius(self):
        """Getter for celsius temperature"""
        return self.__celsius
    
    @celsius.setter
    def celsius(self, value):
        """Setter for celsius with validation"""
        if value < -273.15:
            raise ValueError("Temperature cannot be below absolute zero")
        self.__celsius = value
    
    @property
    def fahrenheit(self):
        """Calculated property for fahrenheit"""
        return (self.__celsius * 9/5) + 32
    
    @fahrenheit.setter
    def fahrenheit(self, value):
        """Setter for fahrenheit that converts to celsius"""
        if value < -459.67:
            raise ValueError("Temperature cannot be below absolute zero")
        self.__celsius = (value - 32) * 5/9
    
    @property
    def kelvin(self):
        """Calculated property for kelvin"""
        return self.__celsius + 273.15
    
    @kelvin.setter
    def kelvin(self, value):
        """Setter for kelvin that converts to celsius"""
        if value < 0:
            raise ValueError("Temperature cannot be below absolute zero")
        self.__celsius = value - 273.15
    
    def __str__(self):
        return f"Temperature: {self.__celsius}°C ({self.fahrenheit}°F, {self.kelvin}K)"

# Usage
temp = Temperature(25)
print(temp)  # Temperature: 25°C (77.0°F, 298.15K)

temp.fahrenheit = 86
print(temp)  # Temperature: 30.0°C (86.0°F, 303.15K)

temp.kelvin = 300
print(temp)  # Temperature: 26.85°C (80.33°F, 300.0K)
```

### Encapsulation with Context Managers

```python
class DatabaseConnection:
    def __init__(self, host, port, database):
        self.__host = host
        self.__port = port
        self.__database = database
        self.__connection = None
        self.__is_connected = False
    
    def __connect(self):
        """Private method to establish connection"""
        # Simulate database connection
        print(f"Connecting to {self.__database} at {self.__host}:{self.__port}")
        self.__connection = f"Connection to {self.__database}"
        self.__is_connected = True
        return self.__connection
    
    def __disconnect(self):
        """Private method to close connection"""
        if self.__is_connected:
            print(f"Disconnecting from {self.__database}")
            self.__connection = None
            self.__is_connected = False
    
    def __enter__(self):
        """Context manager entry"""
        return self.__connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.__disconnect()
        if exc_type:
            print(f"Error occurred: {exc_val}")
        return False  # Don't suppress exceptions
    
    def execute_query(self, query):
        """Public method that requires active connection"""
        if not self.__is_connected:
            raise RuntimeError("No active database connection")
        return f"Executing: {query} on {self.__connection}"

# Usage with context manager
with DatabaseConnection("localhost", 5432, "mydb") as db:
    result = db.execute_query("SELECT * FROM users")
    print(result)
# Connection automatically closed after the with block
```

## Rust Implementation

Rust uses explicit visibility modifiers and has a strong module system that supports encapsulation.

### Basic Encapsulation Example

```rust
// File: bank_account.rs
use std::fmt;

pub struct BankAccount {
    pub account_holder: String,        // Public field
    account_number: String,            // Private field (default)
    balance: f64,                      // Private field
    transaction_history: Vec<String>,  // Private field
}

impl BankAccount {
    // Public constructor
    pub fn new(account_holder: String, initial_balance: f64) -> Result<Self, String> {
        if initial_balance < 0.0 {
            return Err("Initial balance cannot be negative".to_string());
        }
        
        Ok(BankAccount {
            account_holder,
            account_number: Self::generate_account_number(),
            balance: initial_balance,
            transaction_history: Vec::new(),
        })
    }
    
    // Private method (default visibility)
    fn generate_account_number() -> String {
        use rand::Rng;
        let mut rng = rand::thread_rng();
        format!("ACC{:06}", rng.gen_range(100000..999999))
    }
    
    // Private validation method
    fn validate_amount(amount: f64) -> Result<(), String> {
        if amount <= 0.0 {
            return Err("Amount must be positive".to_string());
        }
        if !amount.is_finite() {
            return Err("Amount must be a finite number".to_string());
        }
        Ok(())
    }
    
    // Public method
    pub fn deposit(&mut self, amount: f64) -> Result<String, String> {
        Self::validate_amount(amount)?;
        self.balance += amount;
        let transaction = format!("Deposited: ${:.2}", amount);
        self.transaction_history.push(transaction);
        Ok(format!("Deposited ${:.2}. New balance: ${:.2}", amount, self.balance))
    }
    
    // Public method
    pub fn withdraw(&mut self, amount: f64) -> Result<String, String> {
        Self::validate_amount(amount)?;
        if amount > self.balance {
            return Err("Insufficient funds".to_string());
        }
        self.balance -= amount;
        let transaction = format!("Withdrew: ${:.2}", amount);
        self.transaction_history.push(transaction);
        Ok(format!("Withdrew ${:.2}. New balance: ${:.2}", amount, self.balance))
    }
    
    // Public getter for private field
    pub fn get_balance(&self) -> f64 {
        self.balance
    }
    
    // Public getter returning owned data to prevent modification
    pub fn get_transaction_history(&self) -> Vec<String> {
        self.transaction_history.clone()
    }
    
    // Public getter for account number
    pub fn get_account_number(&self) -> &str {
        &self.account_number
    }
}

// Implementing Display trait for pretty printing
impl fmt::Display for BankAccount {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Account: {} | Holder: {} | Balance: ${:.2}",
            self.account_number, self.account_holder, self.balance
        )
    }
}

// Usage example
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut account = BankAccount::new("John Doe".to_string(), 1000.0)?;
    
    println!("{}", account.deposit(500.0)?);
    println!("{}", account.withdraw(200.0)?);
    println!("Current balance: ${:.2}", account.get_balance());
    println!("Account: {}", account);
    
    // Accessing public field
    println!("Account holder: {}", account.account_holder);
    
    // Private fields are not accessible:
    // println!("{}", account.balance);  // Compile error!
    // println!("{}", account.account_number);  // Compile error!
    
    Ok(())
}
```

### Advanced Rust Encapsulation with Builder Pattern

```rust
// Temperature struct with encapsulated conversion logic
#[derive(Debug, Clone)]
pub struct Temperature {
    celsius: f64,
}

impl Temperature {
    // Constructor that validates input
    pub fn from_celsius(celsius: f64) -> Result<Self, String> {
        if celsius < -273.15 {
            return Err("Temperature cannot be below absolute zero".to_string());
        }
        Ok(Temperature { celsius })
    }
    
    pub fn from_fahrenheit(fahrenheit: f64) -> Result<Self, String> {
        if fahrenheit < -459.67 {
            return Err("Temperature cannot be below absolute zero".to_string());
        }
        let celsius = (fahrenheit - 32.0) * 5.0 / 9.0;
        Ok(Temperature { celsius })
    }
    
    pub fn from_kelvin(kelvin: f64) -> Result<Self, String> {
        if kelvin < 0.0 {
            return Err("Temperature cannot be below absolute zero".to_string());
        }
        let celsius = kelvin - 273.15;
        Ok(Temperature { celsius })
    }
    
    // Getter methods
    pub fn celsius(&self) -> f64 {
        self.celsius
    }
    
    pub fn fahrenheit(&self) -> f64 {
        (self.celsius * 9.0 / 5.0) + 32.0
    }
    
    pub fn kelvin(&self) -> f64 {
        self.celsius + 273.15
    }
    
    // Setter methods that return Result for validation
    pub fn set_celsius(&mut self, celsius: f64) -> Result<(), String> {
        if celsius < -273.15 {
            return Err("Temperature cannot be below absolute zero".to_string());
        }
        self.celsius = celsius;
        Ok(())
    }
    
    pub fn set_fahrenheit(&mut self, fahrenheit: f64) -> Result<(), String> {
        if fahrenheit < -459.67 {
            return Err("Temperature cannot be below absolute zero".to_string());
        }
        self.celsius = (fahrenheit - 32.0) * 5.0 / 9.0;
        Ok(())
    }
    
    pub fn set_kelvin(&mut self, kelvin: f64) -> Result<(), String> {
        if kelvin < 0.0 {
            return Err("Temperature cannot be below absolute zero".to_string());
        }
        self.celsius = kelvin - 273.15;
        Ok(())
    }
}

impl fmt::Display for Temperature {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Temperature: {:.2}°C ({:.2}°F, {:.2}K)",
            self.celsius,
            self.fahrenheit(),
            self.kelvin()
        )
    }
}
```

### Rust Module System for Encapsulation

```rust
// File: lib.rs
pub mod database {
    use std::collections::HashMap;
    
    // Private struct - not accessible outside the module
    struct Connection {
        host: String,
        port: u16,
        database: String,
        connected: bool,
    }
    
    // Public struct that encapsulates the private connection
    pub struct DatabaseManager {
        connection: Option<Connection>,
        connection_pool: HashMap<String, Connection>,
    }
    
    impl DatabaseManager {
        pub fn new() -> Self {
            DatabaseManager {
                connection: None,
                connection_pool: HashMap::new(),
            }
        }
        
        // Public method
        pub fn connect(&mut self, host: String, port: u16, database: String) -> Result<(), String> {
            let connection = Connection::new(host, port, database)?;
            self.connection = Some(connection);
            Ok(())
        }
        
        // Public method
        pub fn execute_query(&self, query: &str) -> Result<String, String> {
            match &self.connection {
                Some(conn) if conn.connected => {
                    Ok(format!("Executing '{}' on {}", query, conn.database))
                }
                Some(_) => Err("Connection not established".to_string()),
                None => Err("No connection available".to_string()),
            }
        }
        
        // Public method
        pub fn disconnect(&mut self) {
            if let Some(mut conn) = self.connection.take() {
                conn.disconnect();
            }
        }
        
        // Public method that provides read-only access to private data
        pub fn connection_info(&self) -> Option<String> {
            self.connection.as_ref().map(|conn| {
                format!("{}:{}/{}", conn.host, conn.port, conn.database)
            })
        }
    }
    
    impl Connection {
        fn new(host: String, port: u16, database: String) -> Result<Self, String> {
            if port == 0 {
                return Err("Invalid port number".to_string());
            }
            
            println!("Connecting to {}:{}/{}", host, port, database);
            Ok(Connection {
                host,
                port,
                database,
                connected: true,
            })
        }
        
        fn disconnect(&mut self) {
            if self.connected {
                println!("Disconnecting from {}", self.database);
                self.connected = false;
            }
        }
    }
    
    // Private helper function
    fn validate_connection_string(conn_str: &str) -> bool {
        conn_str.contains(':') && conn_str.contains('/')
    }
}

// Usage example
use database::DatabaseManager;

fn main() -> Result<(), String> {
    let mut db = DatabaseManager::new();
    
    db.connect("localhost".to_string(), 5432, "mydb".to_string())?;
    
    let result = db.execute_query("SELECT * FROM users")?;
    println!("{}", result);
    
    if let Some(info) = db.connection_info() {
        println!("Connected to: {}", info);
    }
    
    db.disconnect();
    
    // Private struct Connection is not accessible:
    // let conn = database::Connection::new(...);  // Compile error!
    
    Ok(())
}
```

## Advanced Patterns

### 1. Immutable Encapsulation (Rust)

```rust
pub struct ImmutableCounter {
    value: u32,
}

impl ImmutableCounter {
    pub fn new(initial_value: u32) -> Self {
        ImmutableCounter { value: initial_value }
    }
    
    pub fn get(&self) -> u32 {
        self.value
    }
    
    // Returns a new instance instead of modifying self
    pub fn increment(&self) -> Self {
        ImmutableCounter { value: self.value + 1 }
    }
    
    pub fn add(&self, amount: u32) -> Self {
        ImmutableCounter { value: self.value + amount }
    }
}
```

### 2. Encapsulation with Interior Mutability (Rust)

```rust
use std::cell::RefCell;
use std::rc::Rc;

pub struct SharedCounter {
    value: Rc<RefCell<u32>>,
}

impl SharedCounter {
    pub fn new(initial_value: u32) -> Self {
        SharedCounter {
            value: Rc::new(RefCell::new(initial_value)),
        }
    }
    
    pub fn get(&self) -> u32 {
        *self.value.borrow()
    }
    
    pub fn increment(&self) {
        *self.value.borrow_mut() += 1;
    }
    
    pub fn clone_handle(&self) -> Self {
        SharedCounter {
            value: Rc::clone(&self.value),
        }
    }
}
```

## Best Practices

### 1. **Principle of Least Privilege**
Only expose what's necessary. Start with private/internal access and make things public only when needed.

### 2. **Consistent Interface Design**
- Use clear, descriptive method names
- Group related functionality together
- Provide meaningful error messages

### 3. **Validation at Boundaries**
Always validate input at public method boundaries to maintain object invariants.

### 4. **Immutability When Possible**
Prefer immutable objects or provide immutable views of mutable data.

### 5. **Documentation**
Document the public interface clearly, including any constraints or side effects.

### Python Best Practices:
```python
# Use properties for computed values and validation
# Use single underscore for "protected" members
# Use double underscore sparingly for truly private implementation details
# Provide clear error messages
# Return copies of mutable data structures when appropriate
```

### Rust Best Practices:
```rust
// Use the module system effectively
// Prefer returning Result<T, E> for operations that can fail
// Use borrowing (&self) when possible, mutable borrowing (&mut self) when necessary
// Make structs and their fields private by default
// Use type system to enforce invariants at compile time
```

## Common Pitfalls

### 1. **Over-Encapsulation**
Making everything private can lead to overly complex interfaces and reduced flexibility.

### 2. **Leaky Abstractions**
Exposing internal implementation details through the public interface.

### 3. **Inconsistent Access Patterns**
Mixing direct field access with getter/setter methods inconsistently.

### 4. **Mutable References to Internal Data**
Returning mutable references to internal data structures that could be modified externally.

### Python Pitfalls:
```python
# Don't return mutable references to internal data
def get_data(self):
    return self._data  # BAD: External code can modify _data
    return self._data.copy()  # GOOD: Return a copy

# Don't abuse name mangling
self.__private_method()  # Use sparingly
```

### Rust Pitfalls:
```rust
// Don't expose internal implementation through public fields
pub struct BadExample {
    pub internal_vec: Vec<String>,  // BAD: Internal structure exposed
}

// Don't ignore the borrow checker
fn get_mut_ref(&mut self) -> &mut Vec<String> {
    &mut self.data  // Consider if this is really necessary
}
```

## Conclusion

Encapsulation is a powerful tool for creating maintainable, secure, and robust software. Both Python and Rust provide excellent mechanisms for implementing encapsulation, each with their own strengths:

- **Python**: Flexible with conventions-based access control and powerful property system
- **Rust**: Compile-time enforced privacy with excellent module system and type safety

The key to effective encapsulation is finding the right balance between hiding implementation details and providing a useful, flexible interface for your objects. Always consider the needs of the code that will use your classes and design your encapsulation accordingly.

Remember: Encapsulation is not about hiding everything, but about controlling access to maintain object integrity and provide a clean, understandable interface.

I'll create a comprehensive guide to Encapsulation in Object-Oriented Programming with complete implementations in both Python and Rust.I've created a comprehensive guide to Encapsulation in Object-Oriented Programming with detailed implementations in both Python and Rust. The guide covers:

## Key Highlights:

**Core Concepts:**
- What encapsulation is and why it matters
- Data integrity, maintainability, and security benefits
- Different levels of access control (public, protected, private)

**Python Implementation Features:**
- Basic encapsulation with naming conventions (`_protected`, `__private`)
- Advanced use of properties and setters for controlled access
- Context managers for resource management
- Practical examples with bank accounts and temperature conversion

**Rust Implementation Features:**
- Explicit visibility modifiers and compile-time enforcement
- Module system for fine-grained access control
- Error handling with `Result<T, E>` types
- Builder patterns and interior mutability examples

**Advanced Patterns:**
- Immutable encapsulation
- Shared state with interior mutability
- Database connection management

**Best Practices & Pitfalls:**
- When and how to use different access levels
- Common mistakes to avoid
- Language-specific recommendations

The guide provides working code examples that demonstrate real-world applications of encapsulation principles. Each example includes proper error handling, validation, and follows idiomatic patterns for both languages.

Would you like me to expand on any particular section or add more specific examples for certain use cases?

# Encapsulation in Object-Oriented Programming: Rust vs Python

## Overview Diagram

```
ENCAPSULATION CONCEPT
=====================

┌─────────────────────────────────────┐
│          PUBLIC INTERFACE          │
│  ┌─────────────────────────────┐    │
│  │    Accessible Methods       │    │
│  │    & Properties             │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│         PRIVATE INTERNALS           │
│  ┌─────────────────────────────┐    │
│  │    Hidden Implementation    │    │
│  │    Details & Data           │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘

Benefits:
• Data hiding and protection
• Interface abstraction
• Implementation flexibility
• Reduced coupling
```

## Python Encapsulation

### Step 1: Basic Class Structure
```
PYTHON CLASS ANATOMY
====================

class BankAccount:
    ┌─────────────────────────────┐
    │      PUBLIC MEMBERS         │
    │  • __init__()              │
    │  • deposit()               │
    │  • get_balance()           │
    └─────────────────────────────┘
    ┌─────────────────────────────┐
    │     PROTECTED MEMBERS       │
    │  • _account_number         │
    │  • _validate_amount()      │
    └─────────────────────────────┘
    ┌─────────────────────────────┐
    │      PRIVATE MEMBERS        │
    │  • __balance              │
    │  • __pin                  │
    └─────────────────────────────┘
```

### Step 2: Python Implementation Details
```
PYTHON ENCAPSULATION LEVELS
============================

PUBLIC (no underscore)
┌─────────────────────────────┐
│ account.deposit(100)        │
│ ✓ Accessible from anywhere │
└─────────────────────────────┘

PROTECTED (single underscore)
┌─────────────────────────────┐
│ account._account_number     │
│ ⚠ Convention only - still   │
│   accessible but indicates │
│   internal use              │
└─────────────────────────────┘

PRIVATE (double underscore)
┌─────────────────────────────┐
│ account.__balance           │
│ 🔒 Name mangling applied    │
│    becomes _ClassName__attr │
│    Harder to access         │
└─────────────────────────────┘
```

### Step 3: Python Code Example
```python
class BankAccount:
    def __init__(self, account_number, initial_balance=0):
        self._account_number = account_number  # Protected
        self.__balance = initial_balance       # Private
        self.__pin = None                      # Private
    
    # Public interface
    def deposit(self, amount):
        if self._validate_amount(amount):
            self.__balance += amount
            return True
        return False
    
    def get_balance(self):
        return self.__balance
    
    # Protected method
    def _validate_amount(self, amount):
        return amount > 0
    
    # Private method (name mangling)
    def __set_pin(self, pin):
        self.__pin = pin

# Usage demonstration:
account = BankAccount("12345", 1000)
```

### Step 4: Python Access Patterns
```
PYTHON ACCESS DEMONSTRATION
============================

✓ ALLOWED ACCESS:
┌─────────────────────────────┐
│ account.deposit(500)        │
│ account.get_balance()       │
│ account._account_number     │
└─────────────────────────────┘

⚠ DISCOURAGED BUT POSSIBLE:
┌─────────────────────────────┐
│ account._validate_amount()  │
│ (protected method access)   │
└─────────────────────────────┘

🔒 BLOCKED/DIFFICULT ACCESS:
┌─────────────────────────────┐
│ account.__balance           │
│ → AttributeError            │
│                             │
│ account._BankAccount__balance│
│ → 1000 (name mangling)      │
└─────────────────────────────┘
```

## Rust Encapsulation

### Step 1: Module and Struct System
```
RUST ENCAPSULATION ARCHITECTURE
================================

mod bank {
    ┌─────────────────────────────┐
    │         MODULE SCOPE        │
    │                             │
    │  pub struct BankAccount {   │
    │    ┌─────────────────────┐   │
    │    │   PUBLIC FIELDS     │   │
    │    │                     │   │
    │    └─────────────────────┘   │
    │    ┌─────────────────────┐   │
    │    │   PRIVATE FIELDS    │   │
    │    │   balance: f64      │   │
    │    │   pin: String       │   │
    │    └─────────────────────┘   │
    │  }                          │
    │                             │
    │  impl BankAccount {         │
    │    ┌─────────────────────┐   │
    │    │   PUBLIC METHODS    │   │
    │    │   pub fn deposit()  │   │
    │    └─────────────────────┘   │
    │    ┌─────────────────────┐   │
    │    │   PRIVATE METHODS   │   │
    │    │   fn validate()     │   │
    │    └─────────────────────┘   │
    │  }                          │
    └─────────────────────────────┘
}
```

### Step 2: Rust Visibility Rules
```
RUST VISIBILITY SYSTEM
=======================

DEFAULT (private)
┌─────────────────────────────┐
│ struct Field { value: i32 } │
│ fn helper() { }             │
│ 🔒 Only visible within      │
│    current module           │
└─────────────────────────────┘

PUB (public)
┌─────────────────────────────┐
│ pub struct Account { }      │
│ pub fn deposit() { }        │
│ ✓ Visible to external       │
│   modules                   │
└─────────────────────────────┘

PUB(CRATE) (crate-wide)
┌─────────────────────────────┐
│ pub(crate) fn internal() {} │
│ 🏢 Visible within entire    │
│    crate only               │
└─────────────────────────────┘

PUB(SUPER) (parent module)
┌─────────────────────────────┐
│ pub(super) fn parent_fn(){} │
│ ⬆ Visible to parent         │
│   module only               │
└─────────────────────────────┘
```

### Step 3: Rust Implementation
```rust
pub struct BankAccount {
    account_number: String,     // Private field
    balance: f64,              // Private field  
    pin: Option<String>,       // Private field
}

impl BankAccount {
    // Public constructor
    pub fn new(account_number: String, initial_balance: f64) -> Self {
        BankAccount {
            account_number,
            balance: initial_balance,
            pin: None,
        }
    }
    
    // Public methods
    pub fn deposit(&mut self, amount: f64) -> bool {
        if self.validate_amount(amount) {
            self.balance += amount;
            true
        } else {
            false
        }
    }
    
    pub fn get_balance(&self) -> f64 {
        self.balance
    }
    
    pub fn get_account_number(&self) -> &str {
        &self.account_number
    }
    
    // Private method
    fn validate_amount(&self, amount: f64) -> bool {
        amount > 0.0
    }
    
    // Private method
    fn set_pin(&mut self, pin: String) {
        self.pin = Some(pin);
    }
}
```

### Step 4: Rust Access Control Enforcement
```
RUST ACCESS ENFORCEMENT
=======================

✓ ALLOWED ACCESS:
┌─────────────────────────────┐
│ let mut account =           │
│   BankAccount::new(...);    │
│ account.deposit(500.0);     │
│ account.get_balance();      │
└─────────────────────────────┘

🚫 COMPILE-TIME BLOCKED:
┌─────────────────────────────┐
│ account.balance             │
│ → field `balance` of struct │
│   `BankAccount` is private  │
│                             │
│ account.validate_amount()   │
│ → method `validate_amount`  │
│   is private                │
└─────────────────────────────┘
```

## Key Differences Comparison

### Access Control Enforcement
```
ENFORCEMENT COMPARISON
======================

PYTHON                          RUST
┌─────────────────────┐        ┌─────────────────────┐
│    RUNTIME BASED    │        │   COMPILE-TIME      │
│                     │        │      ENFORCED       │
│ • Convention-based  │   VS   │                     │
│ • Name mangling     │        │ • Strict visibility │
│ • Still bypassable  │        │ • Zero-cost         │
│ • Runtime overhead  │        │ • Impossible bypass │
└─────────────────────┘        └─────────────────────┘
```

### Memory Safety & Performance
```
SAFETY & PERFORMANCE
====================

PYTHON                          RUST
┌─────────────────────┐        ┌─────────────────────┐
│ • Reference counted │        │ • Zero-cost         │
│ • Garbage collected │   VS   │   abstractions      │
│ • Runtime checks    │        │ • Compile-time      │
│ • Dynamic typing    │        │   guarantees        │
│ • Flexible but slow │        │ • Static typing     │
└─────────────────────┘        └─────────────────────┘
```

### Usage Patterns
```
TYPICAL USAGE FLOW
==================

PYTHON WORKFLOW:
┌─────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐
│Write│ -> │Run Code │ -> │Runtime   │ -> │Discover │
│Code │    │         │    │Error?    │    │Issues   │
└─────┘    └─────────┘    └──────────┘    └─────────┘

RUST WORKFLOW:
┌─────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐
│Write│ -> │Compile  │ -> │Compiler  │ -> │Safe     │
│Code │    │Code     │    │Checks    │    │Runtime  │
└─────┘    └─────────┘    └──────────┘    └─────────┘
```

## Summary

| Aspect | Python | Rust |
|--------|---------|------|
| **Enforcement** | Runtime conventions | Compile-time strict |
| **Performance** | Runtime overhead | Zero-cost abstraction |
| **Flexibility** | High (can bypass) | Moderate (safe by design) |
| **Learning Curve** | Gentle | Steeper |
| **Safety** | Developer discipline | Compiler guaranteed |

Both languages support encapsulation but with different philosophies:
- **Python**: "We're all consenting adults" - relies on developer discipline
- **Rust**: "Prevention over cure" - compiler enforces safety at compile time

I'll create a comprehensive ASCII diagram showing how encapsulation works in both Rust and Python with step-by-step examples.I've created a comprehensive ASCII diagram that illustrates how encapsulation works in both Rust and Python. The diagram covers:

**Key Sections:**
1. **Overview** - Basic encapsulation concept
2. **Python Implementation** - Shows the three levels (public, protected, private) with naming conventions
3. **Rust Implementation** - Demonstrates module-based visibility with strict compile-time enforcement
4. **Step-by-step examples** - Actual code implementations in both languages
5. **Access patterns** - What's allowed, discouraged, or blocked in each language
6. **Comparison** - Direct side-by-side analysis of the differences

**Main Differences Highlighted:**
- **Python** uses naming conventions (`_protected`, `__private`) with runtime enforcement
- **Rust** uses explicit visibility keywords (`pub`, `pub(crate)`, etc.) with compile-time enforcement
- **Python** allows bypassing encapsulation (though discouraged)
- **Rust** makes it impossible to access private members from outside the module

The diagram shows how Python's approach is more flexible but relies on developer discipline, while Rust's approach is more rigid but provides stronger safety guarantees through the compiler. Both achieve encapsulation but through very different mechanisms!