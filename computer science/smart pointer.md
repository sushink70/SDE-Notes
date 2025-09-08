# Smart Pointers Complete Guide: Python and Rust

I've completed the comprehensive guide to smart pointer implementations in both Python and Rust. This guide covers:

## Key Sections Included:

1. **Introduction** - Core concepts and characteristics of smart pointers
2. **Python Implementations** - Custom implementations including:
   - SharedPtr (reference counting)
   - UniquePtr (exclusive ownership)  
   - WeakPtr (non-owning references)
   - Practical usage examples

3. **Rust Smart Pointers** - Built-in types with examples:
   - Box<T> for heap allocation
   - Rc<T>/Arc<T> for reference counting
   - RefCell<T>/Cell<T> for interior mutability
   - Weak<T> for breaking cycles
   - Custom smart pointer implementations

4. **Comparative Analysis** - Performance, safety, and use case comparisons

5. **Best Practices** - Recommended patterns for both languages

6. **Advanced Patterns** - Including:
   - Copy-on-Write (COW) implementations
   - Memory-mapped smart pointers
   - Atomic smart pointers for lock-free data structures
   - Cycle-detecting garbage collection patterns

## Key Differences Highlighted:

- **Python**: Focuses on resource management and explicit ownership patterns since GC handles memory
- **Rust**: Smart pointers are fundamental to the ownership system with compile-time safety guarantees
- **Performance**: Rust offers zero-cost abstractions while Python has runtime overhead
- **Thread Safety**: Rust provides built-in thread-safe options (Arc<T>), Python requires manual synchronization

The guide includes complete, working code examples for both languages that demonstrate practical implementations and common patterns like observer systems, resource pools, and graph structures with cycle prevention.

## Smart Pointers Complete Guide: Python and Rust

## Table of Contents

1. [Introduction to Smart Pointers](#introduction)
2. [Python Smart Pointer Implementations](#python-implementations)
3. [Rust Smart Pointer Types](#rust-smart-pointers)
4. [Comparative Analysis](#comparative-analysis)
5. [Best Practices and Use Cases](#best-practices)
6. [Advanced Patterns](#advanced-patterns)

## Introduction to Smart Pointers {#introduction}

Smart pointers are objects that act like traditional pointers but provide additional functionality such as automatic memory management, reference counting, and ownership semantics. They help prevent common memory-related bugs like memory leaks, dangling pointers, and double-free errors.

### Key Characteristics:

- **Automatic memory management**: Handle allocation and deallocation automatically
- **Ownership semantics**: Clear rules about who owns and can modify data
- **Reference counting**: Track how many references point to the same data
- **Thread safety**: Some variants provide thread-safe operations

## Python Smart Pointer Implementations {#python-implementations}

Python's garbage collector handles most memory management automatically, but smart pointer patterns can still be useful for resource management and explicit ownership semantics.

### 1. Reference Counting with `weakref`

Python's built-in `weakref` module provides weak reference functionality:

```python
import weakref
import gc

class Resource:
    def __init__(self, name):
        self.name = name
    
    def __del__(self):
        print(f"Resource {self.name} is being destroyed")

# Strong reference
resource = Resource("MyResource")

# Weak reference - doesn't prevent garbage collection
weak_ref = weakref.ref(resource)

print(f"Resource exists: {weak_ref() is not None}")

# Remove strong reference
del resource
gc.collect()  # Force garbage collection

print(f"Resource exists after deletion: {weak_ref() is not None}")
```

### 2. Custom Shared Pointer Implementation

```python
import weakref
from typing import TypeVar, Generic, Optional, Callable
import threading

T = TypeVar('T')

class SharedPtr(Generic[T]):
    """Thread-safe reference-counted smart pointer implementation"""
    
    def __init__(self, obj: T):
        self._obj = obj
        self._ref_count = 1
        self._lock = threading.RLock()
        self._deleter: Optional[Callable[[T], None]] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
    
    def get(self) -> Optional[T]:
        """Get the managed object"""
        with self._lock:
            return self._obj if self._ref_count > 0 else None
    
    def reset(self, new_obj: Optional[T] = None):
        """Reset the pointer to manage a new object or None"""
        with self._lock:
            self._decrease_ref_count()
            if new_obj is not None:
                self._obj = new_obj
                self._ref_count = 1
            else:
                self._obj = None
                self._ref_count = 0
    
    def copy(self) -> 'SharedPtr[T]':
        """Create a new SharedPtr sharing the same object"""
        with self._lock:
            if self._ref_count > 0:
                new_ptr = SharedPtr.__new__(SharedPtr)
                new_ptr._obj = self._obj
                new_ptr._ref_count = self._ref_count + 1
                new_ptr._lock = self._lock
                new_ptr._deleter = self._deleter
                self._ref_count += 1
                return new_ptr
            else:
                return SharedPtr(None)
    
    def use_count(self) -> int:
        """Get the current reference count"""
        with self._lock:
            return self._ref_count
    
    def unique(self) -> bool:
        """Check if this is the only reference"""
        return self.use_count() == 1
    
    def set_deleter(self, deleter: Callable[[T], None]):
        """Set a custom deleter function"""
        self._deleter = deleter
    
    def _decrease_ref_count(self):
        """Decrease reference count and cleanup if needed"""
        self._ref_count -= 1
        if self._ref_count == 0 and self._obj is not None:
            if self._deleter:
                self._deleter(self._obj)
            self._obj = None
    
    def __del__(self):
        if hasattr(self, '_lock'):
            with self._lock:
                self._decrease_ref_count()
    
    def __bool__(self) -> bool:
        return self.get() is not None
    
    def __getattr__(self, name):
        obj = self.get()
        if obj is None:
            raise ValueError("SharedPtr is empty")
        return getattr(obj, name)

# Usage example
class FileResource:
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'w')
        print(f"Opened file: {filename}")
    
    def write(self, data):
        self.file.write(data)
    
    def close(self):
        if self.file:
            self.file.close()
            print(f"Closed file: {self.filename}")

# Custom deleter
def file_deleter(resource):
    resource.close()

# Create shared pointer
ptr1 = SharedPtr(FileResource("test.txt"))
ptr1.set_deleter(file_deleter)

# Share the resource
ptr2 = ptr1.copy()
print(f"Reference count: {ptr1.use_count()}")  # Should be 2

# Use the resource
ptr1.write("Hello, World!")
ptr2.write("From shared pointer!")

# Reset one pointer
ptr1.reset()
print(f"Reference count: {ptr2.use_count()}")  # Should be 1

# Reset the last pointer - resource will be cleaned up
ptr2.reset()
```

### 3. Unique Pointer Implementation

```python
from typing import TypeVar, Generic, Optional, Callable

T = TypeVar('T')

class UniquePtr(Generic[T]):
    """Exclusive ownership smart pointer"""
    
    def __init__(self, obj: Optional[T] = None):
        self._obj = obj
        self._deleter: Optional[Callable[[T], None]] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
    
    def get(self) -> Optional[T]:
        """Get the managed object"""
        return self._obj
    
    def release(self) -> Optional[T]:
        """Release ownership and return the object"""
        obj = self._obj
        self._obj = None
        return obj
    
    def reset(self, new_obj: Optional[T] = None):
        """Reset to manage a new object"""
        if self._obj is not None:
            if self._deleter:
                self._deleter(self._obj)
        self._obj = new_obj
    
    def move(self) -> 'UniquePtr[T]':
        """Move ownership to a new UniquePtr"""
        new_ptr = UniquePtr(self._obj)
        new_ptr._deleter = self._deleter
        self._obj = None
        self._deleter = None
        return new_ptr
    
    def set_deleter(self, deleter: Callable[[T], None]):
        """Set a custom deleter function"""
        self._deleter = deleter
    
    def __bool__(self) -> bool:
        return self._obj is not None
    
    def __getattr__(self, name):
        if self._obj is None:
            raise ValueError("UniquePtr is empty")
        return getattr(self._obj, name)
    
    def __del__(self):
        self.reset()

# Usage example
class Database:
    def __init__(self, name):
        self.name = name
        print(f"Database {name} connected")
    
    def query(self, sql):
        print(f"Executing: {sql}")
    
    def close(self):
        print(f"Database {self.name} disconnected")

def db_deleter(db):
    db.close()

# Create unique pointer
db_ptr = UniquePtr(Database("MyDB"))
db_ptr.set_deleter(db_deleter)

# Use the database
db_ptr.query("SELECT * FROM users")

# Move ownership
new_ptr = db_ptr.move()
print(f"Original pointer valid: {bool(db_ptr)}")  # False
print(f"New pointer valid: {bool(new_ptr)}")      # True

# Automatic cleanup when new_ptr goes out of scope
```

### 4. Weak Pointer Implementation

```python
import weakref
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class WeakPtr(Generic[T]):
    """Non-owning weak reference smart pointer"""
    
    def __init__(self, shared_ptr: Optional['SharedPtr[T]'] = None):
        if shared_ptr is None:
            self._weak_ref = None
        else:
            obj = shared_ptr.get()
            if obj is not None:
                self._weak_ref = weakref.ref(obj)
            else:
                self._weak_ref = None
    
    def expired(self) -> bool:
        """Check if the referenced object has been destroyed"""
        if self._weak_ref is None:
            return True
        return self._weak_ref() is None
    
    def lock(self) -> Optional['SharedPtr[T]']:
        """Attempt to create a SharedPtr from this weak reference"""
        if self.expired():
            return None
        
        obj = self._weak_ref()
        if obj is not None:
            return SharedPtr(obj)
        return None
    
    def reset(self):
        """Reset the weak pointer"""
        self._weak_ref = None
    
    def __bool__(self) -> bool:
        return not self.expired()

# Usage example with observer pattern
class Subject:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer_ptr: WeakPtr):
        self._observers.append(observer_ptr)
    
    def notify(self, message):
        # Remove expired observers
        self._observers = [obs for obs in self._observers if not obs.expired()]
        
        # Notify remaining observers
        for weak_observer in self._observers:
            observer_ptr = weak_observer.lock()
            if observer_ptr:
                observer_ptr.update(message)

class Observer:
    def __init__(self, name):
        self.name = name
    
    def update(self, message):
        print(f"Observer {self.name} received: {message}")

# Create subject and observers
subject = Subject()
observer1_ptr = SharedPtr(Observer("Observer1"))
observer2_ptr = SharedPtr(Observer("Observer2"))

# Attach observers using weak pointers
subject.attach(WeakPtr(observer1_ptr))
subject.attach(WeakPtr(observer2_ptr))

# Notify observers
subject.notify("Hello observers!")

# Remove one observer
observer1_ptr.reset()

# Notify again - only one observer should receive the message
subject.notify("Second message")
```

## Rust Smart Pointer Types {#rust-smart-pointers}

Rust provides several built-in smart pointer types as part of its ownership system. These are fundamental to Rust's memory safety guarantees.

### 1. Box<T> - Heap Allocation

`Box<T>` provides heap allocation with exclusive ownership:

```rust
use std::fmt::Debug;

// Basic Box usage
fn basic_box_example() {
    // Allocate an integer on the heap
    let boxed_int = Box::new(42);
    println!("Boxed value: {}", *boxed_int);
    
    // Box is automatically dropped when it goes out of scope
}

// Recursive data structures with Box
#[derive(Debug)]
enum List {
    Cons(i32, Box<List>),
    Nil,
}

use List::{Cons, Nil};

fn recursive_structure_example() {
    let list = Cons(1, Box::new(Cons(2, Box::new(Cons(3, Box::new(Nil))))));
    println!("List: {:?}", list);
}

// Custom smart pointer behavior
struct CustomBox<T> {
    data: T,
}

impl<T> CustomBox<T> {
    fn new(data: T) -> CustomBox<T> {
        CustomBox { data }
    }
}

// Implement Deref to act like a pointer
use std::ops::Deref;

impl<T> Deref for CustomBox<T> {
    type Target = T;
    
    fn deref(&self) -> &Self::Target {
        &self.data
    }
}

// Implement Drop for cleanup
impl<T> Drop for CustomBox<T> {
    fn drop(&mut self) {
        println!("Dropping CustomBox");
    }
}

fn custom_box_example() {
    let custom = CustomBox::new(String::from("Hello"));
    println!("Custom box contains: {}", *custom);
    // CustomBox is automatically dropped here
}
```

### 2. Rc<T> - Reference Counting

`Rc<T>` provides shared ownership through reference counting (single-threaded):

```rust
use std::rc::Rc;
use std::cell::RefCell;

// Basic Rc usage
fn basic_rc_example() {
    let data = Rc::new(String::from("Shared data"));
    
    let data1 = Rc::clone(&data);
    let data2 = Rc::clone(&data);
    
    println!("Reference count: {}", Rc::strong_count(&data));
    println!("Data: {}", *data1);
    
    // All Rc instances are dropped automatically
}

// Graph structure with Rc
#[derive(Debug)]
struct Node {
    value: i32,
    children: RefCell<Vec<Rc<Node>>>,
    parent: RefCell<Option<Rc<Node>>>,
}

impl Node {
    fn new(value: i32) -> Rc<Node> {
        Rc::new(Node {
            value,
            children: RefCell::new(Vec::new()),
            parent: RefCell::new(None),
        })
    }
    
    fn add_child(parent: &Rc<Node>, child: Rc<Node>) {
        child.parent.borrow_mut().replace(Rc::clone(parent));
        parent.children.borrow_mut().push(child);
    }
}

fn graph_example() {
    let root = Node::new(1);
    let child1 = Node::new(2);
    let child2 = Node::new(3);
    
    Node::add_child(&root, Rc::clone(&child1));
    Node::add_child(&root, Rc::clone(&child2));
    
    println!("Root has {} children", root.children.borrow().len());
    println!("Child1 reference count: {}", Rc::strong_count(&child1));
}

// Rc with interior mutability
struct Counter {
    count: RefCell<usize>,
}

impl Counter {
    fn new() -> Rc<Counter> {
        Rc::new(Counter {
            count: RefCell::new(0),
        })
    }
    
    fn increment(&self) {
        *self.count.borrow_mut() += 1;
    }
    
    fn get(&self) -> usize {
        *self.count.borrow()
    }
}

fn shared_counter_example() {
    let counter = Counter::new();
    let counter1 = Rc::clone(&counter);
    let counter2 = Rc::clone(&counter);
    
    counter1.increment();
    counter2.increment();
    
    println!("Final count: {}", counter.get());
}
```

### 3. Arc<T> - Atomic Reference Counting

`Arc<T>` provides thread-safe shared ownership:

```rust
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

// Basic Arc usage
fn basic_arc_example() {
    let data = Arc::new(String::from("Shared across threads"));
    let mut handles = vec![];
    
    for i in 0..5 {
        let data_clone = Arc::clone(&data);
        let handle = thread::spawn(move || {
            println!("Thread {}: {}", i, data_clone);
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
}

// Thread-safe counter with Arc and Mutex
struct ThreadSafeCounter {
    count: Arc<Mutex<usize>>,
}

impl ThreadSafeCounter {
    fn new() -> Self {
        ThreadSafeCounter {
            count: Arc::new(Mutex::new(0)),
        }
    }
    
    fn increment(&self) {
        let mut count = self.count.lock().unwrap();
        *count += 1;
    }
    
    fn get(&self) -> usize {
        *self.count.lock().unwrap()
    }
    
    fn clone_counter(&self) -> Arc<Mutex<usize>> {
        Arc::clone(&self.count)
    }
}

fn threaded_counter_example() {
    let counter = ThreadSafeCounter::new();
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter_clone = counter.clone_counter();
        let handle = thread::spawn(move || {
            for _ in 0..100 {
                let mut count = counter_clone.lock().unwrap();
                *count += 1;
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Final count: {}", counter.get());
}

// Producer-consumer pattern with Arc
use std::sync::mpsc;

fn producer_consumer_example() {
    let data = Arc::new(Mutex::new(Vec::<i32>::new()));
    let (tx, rx) = mpsc::channel();
    
    // Producer
    let producer_data = Arc::clone(&data);
    let producer_tx = tx.clone();
    thread::spawn(move || {
        for i in 0..10 {
            {
                let mut vec = producer_data.lock().unwrap();
                vec.push(i);
            }
            producer_tx.send(i).unwrap();
            thread::sleep(Duration::from_millis(100));
        }
    });
    
    // Consumer
    let consumer_data = Arc::clone(&data);
    thread::spawn(move || {
        while let Ok(value) = rx.recv() {
            let vec = consumer_data.lock().unwrap();
            println!("Consumed: {}, Vector length: {}", value, vec.len());
        }
    });
    
    thread::sleep(Duration::from_secs(2));
}
```

### 4. RefCell<T> and Cell<T> - Interior Mutability

These types provide interior mutability patterns:

```rust
use std::cell::{RefCell, Cell};
use std::rc::Rc;

// RefCell for complex types
#[derive(Debug)]
struct MockObject {
    data: RefCell<Vec<String>>,
    call_count: Cell<usize>,
}

impl MockObject {
    fn new() -> Self {
        MockObject {
            data: RefCell::new(Vec::new()),
            call_count: Cell::new(0),
        }
    }
    
    fn add_data(&self, item: String) {
        self.call_count.set(self.call_count.get() + 1);
        self.data.borrow_mut().push(item);
    }
    
    fn get_data(&self) -> Vec<String> {
        self.call_count.set(self.call_count.get() + 1);
        self.data.borrow().clone()
    }
    
    fn call_count(&self) -> usize {
        self.call_count.get()
    }
}

fn interior_mutability_example() {
    let mock = MockObject::new();
    
    mock.add_data("First".to_string());
    mock.add_data("Second".to_string());
    
    let data = mock.get_data();
    println!("Data: {:?}", data);
    println!("Call count: {}", mock.call_count());
}

// Shared mutable state with Rc<RefCell<T>>
fn shared_mutable_example() {
    let shared_list = Rc::new(RefCell::new(Vec::<i32>::new()));
    
    let list1 = Rc::clone(&shared_list);
    let list2 = Rc::clone(&shared_list);
    
    list1.borrow_mut().push(1);
    list1.borrow_mut().push(2);
    
    list2.borrow_mut().push(3);
    list2.borrow_mut().push(4);
    
    println!("Shared list: {:?}", *shared_list.borrow());
}
```

### 5. Weak<T> - Weak References

`Weak<T>` provides non-owning references to prevent reference cycles:

```rust
use std::rc::{Rc, Weak};
use std::cell::RefCell;

// Tree structure with parent-child relationships
#[derive(Debug)]
struct TreeNode {
    value: i32,
    children: RefCell<Vec<Rc<TreeNode>>>,
    parent: RefCell<Option<Weak<TreeNode>>>,
}

impl TreeNode {
    fn new(value: i32) -> Rc<TreeNode> {
        Rc::new(TreeNode {
            value,
            children: RefCell::new(Vec::new()),
            parent: RefCell::new(None),
        })
    }
    
    fn add_child(parent: &Rc<TreeNode>, child: &Rc<TreeNode>) {
        child.parent.borrow_mut().replace(Rc::downgrade(parent));
        parent.children.borrow_mut().push(Rc::clone(child));
    }
    
    fn get_parent(&self) -> Option<Rc<TreeNode>> {
        self.parent.borrow().as_ref()?.upgrade()
    }
}

fn weak_reference_example() {
    let root = TreeNode::new(1);
    let child1 = TreeNode::new(2);
    let child2 = TreeNode::new(3);
    
    TreeNode::add_child(&root, &child1);
    TreeNode::add_child(&root, &child2);
    
    println!("Root strong count: {}", Rc::strong_count(&root));
    println!("Root weak count: {}", Rc::weak_count(&root));
    
    // Access parent from child
    if let Some(parent) = child1.get_parent() {
        println!("Child1's parent value: {}", parent.value);
    }
    
    // Child nodes are dropped first, then root
    // No reference cycles, so everything is cleaned up properly
}

// Observer pattern with weak references
trait Observer {
    fn update(&self, message: &str);
}

struct Subject {
    observers: RefCell<Vec<Weak<dyn Observer>>>,
}

impl Subject {
    fn new() -> Self {
        Subject {
            observers: RefCell::new(Vec::new()),
        }
    }
    
    fn attach(&self, observer: Weak<dyn Observer>) {
        self.observers.borrow_mut().push(observer);
    }
    
    fn notify(&self, message: &str) {
        self.observers.borrow_mut().retain(|weak_obs| {
            if let Some(observer) = weak_obs.upgrade() {
                observer.update(message);
                true // Keep this observer
            } else {
                false // Remove expired observer
            }
        });
    }
}

struct ConcreteObserver {
    name: String,
}

impl ConcreteObserver {
    fn new(name: String) -> Rc<Self> {
        Rc::new(ConcreteObserver { name })
    }
}

impl Observer for ConcreteObserver {
    fn update(&self, message: &str) {
        println!("Observer {} received: {}", self.name, message);
    }
}

fn observer_pattern_example() {
    let subject = Subject::new();
    
    let observer1 = ConcreteObserver::new("Observer1".to_string());
    let observer2 = ConcreteObserver::new("Observer2".to_string());
    
    subject.attach(Rc::downgrade(&observer1));
    subject.attach(Rc::downgrade(&observer2));
    
    subject.notify("First message");
    
    // Drop observer1
    drop(observer1);
    
    subject.notify("Second message"); // Only observer2 will receive this
}
```

### 6. Custom Smart Pointers in Rust

```rust
use std::ops::Deref;
use std::fmt::{self, Debug, Formatter};

// Custom unique pointer with logging
struct LoggedBox<T> {
    data: Box<T>,
    name: String,
}

impl<T> LoggedBox<T> {
    fn new(data: T, name: String) -> Self {
        println!("Creating LoggedBox: {}", name);
        LoggedBox {
            data: Box::new(data),
            name,
        }
    }
}

impl<T> Deref for LoggedBox<T> {
    type Target = T;
    
    fn deref(&self) -> &Self::Target {
        println!("Accessing LoggedBox: {}", self.name);
        &self.data
    }
}

impl<T> Drop for LoggedBox<T> {
    fn drop(&mut self) {
        println!("Dropping LoggedBox: {}", self.name);
    }
}

impl<T: Debug> Debug for LoggedBox<T> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "LoggedBox({}, {:?})", self.name, self.data)
    }
}

// Copy-on-write smart pointer
use std::borrow::Cow;
use std::sync::Arc;

struct CowPtr<T: Clone> {
    data: Arc<T>,
}

impl<T: Clone> CowPtr<T> {
    fn new(data: T) -> Self {
        CowPtr {
            data: Arc::new(data),
        }
    }
    
    fn get(&self) -> &T {
        &self.data
    }
    
    fn get_mut(&mut self) -> &mut T {
        Arc::make_mut(&mut self.data)
    }
    
    fn clone_ptr(&self) -> Self {
        CowPtr {
            data: Arc::clone(&self.data),
        }
    }
}

fn custom_smart_pointer_example() {
    // LoggedBox example
    let logged = LoggedBox::new(vec![1, 2, 3], "my_vector".to_string());
    println!("Vector length: {}", logged.len());
    
    // CowPtr example
    let mut cow1 = CowPtr::new(vec![1, 2, 3]);
    let cow2 = cow1.clone_ptr();
    
    println!("Before modification - Arc strong count: {}", Arc::strong_count(&cow1.data));
    
    // This will clone the data due to shared ownership
    cow1.get_mut().push(4);
    
    println!("After modification:");
    println!("cow1: {:?}", cow1.get());
    println!("cow2: {:?}", cow2.get());
}

fn main() {
    println!("=== Basic Box Example ===");
    basic_box_example();
    
    println!("\n=== Recursive Structure Example ===");
    recursive_structure_example();
    
    println!("\n=== Custom Box Example ===");
    custom_box_example();
    
    println!("\n=== Basic Rc Example ===");
    basic_rc_example();
    
    println!("\n=== Graph Example ===");
    graph_example();
    
    println!("\n=== Shared Counter Example ===");
    shared_counter_example();
    
    println!("\n=== Basic Arc Example ===");
    basic_arc_example();
    
    println!("\n=== Threaded Counter Example ===");
    threaded_counter_example();
    
    println!("\n=== Producer Consumer Example ===");
    producer_consumer_example();
    
    println!("\n=== Interior Mutability Example ===");
    interior_mutability_example();
    
    println!("\n=== Shared Mutable Example ===");
    shared_mutable_example();
    
    println!("\n=== Weak Reference Example ===");
    weak_reference_example();
    
    println!("\n=== Observer Pattern Example ===");
    observer_pattern_example();
    
    println!("\n=== Custom Smart Pointer Example ===");
    custom_smart_pointer_example();
}
```

## Comparative Analysis {#comparative-analysis}

### Memory Management Philosophy

| Aspect | Python | Rust |
|--------|--------|------|
| **Memory Management** | Garbage Collection + Manual patterns | Ownership system with compile-time checks |
| **Performance** | Runtime overhead | Zero-cost abstractions |
| **Safety** | Runtime errors possible | Compile-time memory safety guarantees |
| **Flexibility** | High, but with potential pitfalls | High within ownership rules |

### Smart Pointer Capabilities

| Feature | Python Implementation | Rust Built-in |
|---------|----------------------|---------------|
| **Reference Counting** | Custom `SharedPtr` | `Rc<T>` / `Arc<T>` |
| **Unique Ownership** | Custom `UniquePtr` | `Box<T>` |
| **Weak References** | `weakref` / Custom `WeakPtr` | `Weak<T>` |
| **Thread Safety** | Manual synchronization needed | `Arc<T>` is thread-safe |
| **Interior Mutability** | Python's mutable objects | `RefCell<T>` / `Cell<T>` |

### Performance Characteristics

**Python:**
- Runtime reference counting overhead
- GIL limitations for true parallelism
- Dynamic typing overhead
- Flexible but potentially slower

**Rust:**
- Compile-time optimization
- Zero-cost abstractions
- Native threading support
- Maximum performance with safety

### Use Case Suitability

| Use Case | Python | Rust |
|----------|--------|------|
| **Rapid Prototyping** | ✅ Excellent | ❌ More verbose |
| **System Programming** | ❌ Not ideal | ✅ Excellent |
| **High Performance** | ❌ Limited | ✅ Excellent |
| **Memory-Critical Applications** | ❌ GC overhead | ✅ Precise control |
| **Concurrent Programming** | ⚠️ GIL limitations | ✅ Excellent |
| **Learning/Educational** | ✅ Good for concepts | ⚠️ Steep learning curve |

## Best Practices and Use Cases {#best-practices}

### Python Best Practices

1. **Use built-in `weakref` for observer patterns**:
   ```python
   import weakref
   
   class Publisher:
       def __init__(self):
           self._subscribers = weakref.WeakSet()
       
       def subscribe(self, callback):
           self._subscribers.add(callback)
       
       def publish(self, event):
           for callback in self._subscribers:
               callback(event)
   ```

2. **Implement context managers for automatic cleanup**:
   ```python
   class ManagedResource:
       def __init__(self, resource):
           self.resource = resource
       
       def __enter__(self):
           return self.resource
       
       def __exit__(self, exc_type, exc_val, exc_tb):
           if hasattr(self.resource, 'close'):
               self.resource.close()
   
   # Usage
   with ManagedResource(open('file.txt')) as f:
       f.write('data')
   # File automatically closed
   ```

3. **Use custom deleters for resource cleanup**:
   ```python
   def create_shared_file(filename):
       def file_deleter(file_obj):
           file_obj.close()
           print(f"Closed {filename}")
       
       file_ptr = SharedPtr(open(filename, 'w'))
       file_ptr.set_deleter(file_deleter)
       return file_ptr
   ```

4. **Avoid circular references with weak pointers**:
   ```python
   class Parent:
       def __init__(self):
           self.children = []
       
       def add_child(self, child):
           self.children.append(child)
           child.parent = weakref.ref(self)  # Weak reference
   
   class Child:
       def __init__(self):
           self.parent = None
   ```

### Rust Best Practices

1. **Choose the right smart pointer for your use case**:
   ```rust
   // Use Box<T> for heap allocation with single ownership
   let data = Box::new(expensive_computation());
   
   // Use Rc<T> for shared ownership in single-threaded contexts
   let shared_data = Rc::new(data);
   
   // Use Arc<T> for shared ownership across threads
   let thread_safe_data = Arc::new(Mutex::new(data));
   
   // Use Weak<T> to break reference cycles
   let weak_ref = Rc::downgrade(&shared_data);
   ```

2. **Combine smart pointers with interior mutability patterns**:
   ```rust
   // Shared mutable state
   type SharedState = Arc<Mutex<HashMap<String, i32>>>;
   
   // Single-threaded shared mutable state
   type LocalState = Rc<RefCell<Vec<String>>>;
   ```

3. **Use `Weak<T>` to prevent memory leaks**:
   ```rust
   struct Node {
       children: Vec<Rc<Node>>,
       parent: Option<Weak<Node>>, // Weak reference to prevent cycles
   }
   ```

4. **Prefer `Arc<T>` over `Rc<T>` for future-proof thread safety**:
   ```rust
   // Even if currently single-threaded, Arc allows easy migration
   let data = Arc::new(MyData::new());
   ```

### Common Use Cases

#### 1. Observer Pattern Implementation

**Python:**
```python
class EventSystem:
    def __init__(self):
        self._observers = weakref.WeakSet()
    
    def subscribe(self, observer):
        self._observers.add(observer)
    
    def notify(self, event):
        # Automatically removes dead observers
        for observer in list(self._observers):
            observer.handle_event(event)

class Observer:
    def __init__(self, name):
        self.name = name
    
    def handle_event(self, event):
        print(f"{self.name} received {event}")

# Usage
event_system = EventSystem()
obs1 = Observer("Observer1")
event_system.subscribe(obs1)

event_system.notify("test_event")
del obs1  # Observer automatically removed from weak set
```

**Rust:**
```rust
use std::rc::{Rc, Weak};
use std::cell::RefCell;

trait EventHandler {
    fn handle_event(&self, event: &str);
}

struct EventSystem {
    observers: RefCell<Vec<Weak<dyn EventHandler>>>,
}

impl EventSystem {
    fn new() -> Self {
        EventSystem {
            observers: RefCell::new(Vec::new()),
        }
    }
    
    fn subscribe(&self, observer: Weak<dyn EventHandler>) {
        self.observers.borrow_mut().push(observer);
    }
    
    fn notify(&self, event: &str) {
        self.observers.borrow_mut().retain(|weak_observer| {
            if let Some(observer) = weak_observer.upgrade() {
                observer.handle_event(event);
                true
            } else {
                false // Remove expired observer
            }
        });
    }
}
```

#### 2. Resource Pool Management

**Python:**
```python
class ResourcePool:
    def __init__(self, create_resource, max_size=10):
        self._create_resource = create_resource
        self._pool = []
        self._active = weakref.WeakSet()
        self._max_size = max_size
    
    def acquire(self):
        if self._pool:
            resource = self._pool.pop()
        else:
            resource = self._create_resource()
        
        self._active.add(resource)
        return resource
    
    def release(self, resource):
        if resource in self._active and len(self._pool) < self._max_size:
            self._pool.append(resource)

# Database connection pool example
def create_db_connection():
    return DatabaseConnection("localhost:5432")

pool = ResourcePool(create_db_connection, max_size=5)
```

**Rust:**
```rust
use std::sync::{Arc, Mutex};
use std::collections::VecDeque;

struct ResourcePool<T> {
    pool: Arc<Mutex<VecDeque<T>>>,
    factory: Box<dyn Fn() -> T + Send + Sync>,
    max_size: usize,
}

impl<T> ResourcePool<T> {
    fn new<F>(factory: F, max_size: usize) -> Self 
    where 
        F: Fn() -> T + Send + Sync + 'static,
    {
        ResourcePool {
            pool: Arc::new(Mutex::new(VecDeque::new())),
            factory: Box::new(factory),
            max_size,
        }
    }
    
    fn acquire(&self) -> T {
        let mut pool = self.pool.lock().unwrap();
        pool.pop_front().unwrap_or_else(|| (self.factory)())
    }
    
    fn release(&self, resource: T) {
        let mut pool = self.pool.lock().unwrap();
        if pool.len() < self.max_size {
            pool.push_back(resource);
        }
    }
}
```

#### 3. Graph Structures with Cycles

**Python:**
```python
class GraphNode:
    def __init__(self, value):
        self.value = value
        self.edges = []  # Strong references to children
        self._back_edges = weakref.WeakSet()  # Weak references to prevent cycles
    
    def add_edge(self, target):
        self.edges.append(target)
        target._back_edges.add(self)
    
    def get_back_references(self):
        return list(self._back_edges)

# Create a cycle-safe graph
node_a = GraphNode("A")
node_b = GraphNode("B") 
node_c = GraphNode("C")

node_a.add_edge(node_b)
node_b.add_edge(node_c)
node_c.add_edge(node_a)  # This would create a cycle, but back_edges are weak
```

**Rust:**
```rust
use std::rc::{Rc, Weak};
use std::cell::RefCell;

struct GraphNode {
    value: String,
    edges: RefCell<Vec<Rc<GraphNode>>>,
    back_edges: RefCell<Vec<Weak<GraphNode>>>,
}

impl GraphNode {
    fn new(value: String) -> Rc<Self> {
        Rc::new(GraphNode {
            value,
            edges: RefCell::new(Vec::new()),
            back_edges: RefCell::new(Vec::new()),
        })
    }
    
    fn add_edge(from: &Rc<GraphNode>, to: &Rc<GraphNode>) {
        from.edges.borrow_mut().push(Rc::clone(to));
        to.back_edges.borrow_mut().push(Rc::downgrade(from));
    }
    
    fn get_edges(&self) -> Vec<Rc<GraphNode>> {
        self.edges.borrow().clone()
    }
    
    fn get_back_edges(&self) -> Vec<Rc<GraphNode>> {
        self.back_edges
            .borrow()
            .iter()
            .filter_map(|weak| weak.upgrade())
            .collect()
    }
}
```

## Advanced Patterns {#advanced-patterns}

### 1. Copy-on-Write (COW) Pattern

**Python Implementation:**
```python
import copy
from typing import TypeVar, Generic, Union

T = TypeVar('T')

class CowPtr(Generic[T]):
    """Copy-on-Write smart pointer"""
    
    def __init__(self, data: T):
        self._data = data
        self._ref_count = 1
        self._is_unique = True
    
    def clone(self) -> 'CowPtr[T]':
        """Create a new reference sharing the same data"""
        new_ptr = CowPtr.__new__(CowPtr)
        new_ptr._data = self._data
        new_ptr._ref_count = self._ref_count + 1
        new_ptr._is_unique = False
        
        self._ref_count += 1
        self._is_unique = False
        return new_ptr
    
    def get_immutable(self) -> T:
        """Get read-only access to the data"""
        return self._data
    
    def get_mutable(self) -> T:
        """Get mutable access, copying if necessary"""
        if not self._is_unique:
            self._data = copy.deepcopy(self._data)
            self._ref_count = 1
            self._is_unique = True
        return self._data
    
    def is_unique(self) -> bool:
        return self._is_unique

# Usage example
original_data = [1, 2, 3, 4, 5]
cow1 = CowPtr(original_data)
cow2 = cow1.clone()

print("Before modification:")
print(f"cow1 data: {cow1.get_immutable()}")
print(f"cow2 data: {cow2.get_immutable()}")
print(f"Same object: {cow1.get_immutable() is cow2.get_immutable()}")

# Modify cow1 - this triggers a copy
cow1.get_mutable().append(6)

print("\nAfter modification:")
print(f"cow1 data: {cow1.get_immutable()}")
print(f"cow2 data: {cow2.get_immutable()}")
print(f"Same object: {cow1.get_immutable() is cow2.get_immutable()}")
```

**Rust COW with Arc:**
```rust
use std::sync::Arc;

struct CowData<T: Clone> {
    data: Arc<T>,
}

impl<T: Clone> CowData<T> {
    fn new(data: T) -> Self {
        CowData {
            data: Arc::new(data),
        }
    }
    
    fn get(&self) -> &T {
        &self.data
    }
    
    fn get_mut(&mut self) -> &mut T {
        Arc::make_mut(&mut self.data)
    }
    
    fn clone_handle(&self) -> Self {
        CowData {
            data: Arc::clone(&self.data),
        }
    }
    
    fn is_unique(&self) -> bool {
        Arc::strong_count(&self.data) == 1
    }
}

fn cow_example() {
    let mut cow1 = CowData::new(vec![1, 2, 3, 4, 5]);
    let cow2 = cow1.clone_handle();
    
    println!("Before modification:");
    println!("cow1: {:?}", cow1.get());
    println!("cow2: {:?}", cow2.get());
    println!("Strong count: {}", Arc::strong_count(&cow1.data));
    
    // This will trigger copy-on-write
    cow1.get_mut().push(6);
    
    println!("\nAfter modification:");
    println!("cow1: {:?}", cow1.get());
    println!("cow2: {:?}", cow2.get());
}
```

### 2. Smart Pointer with Custom Allocators

**Python Custom Memory Management:**
```python
import mmap
import os
from typing import Optional, TypeVar, Generic

T = TypeVar('T')

class MmapPtr(Generic[T]):
    """Smart pointer using memory-mapped storage"""
    
    def __init__(self, data: T, filename: Optional[str] = None):
        import pickle
        
        if filename is None:
            # Anonymous memory mapping
            self._data_bytes = pickle.dumps(data)
            self._mmap = mmap.mmap(-1, len(self._data_bytes))
            self._mmap.write(self._data_bytes)
            self._mmap.seek(0)
            self._file = None
        else:
            # File-backed memory mapping
            self._data_bytes = pickle.dumps(data)
            self._file = open(filename, 'w+b')
            self._file.write(self._data_bytes)
            self._file.flush()
            self._mmap = mmap.mmap(self._file.fileno(), 0)
    
    def get(self) -> T:
        import pickle
        self._mmap.seek(0)
        return pickle.loads(self._mmap.read())
    
    def set(self, data: T):
        import pickle
        new_data = pickle.dumps(data)
        
        if len(new_data) > len(self._mmap):
            # Need to resize
            self._mmap.close()
            if self._file:
                self._file.seek(0)
                self._file.write(new_data)
                self._file.flush()
                self._mmap = mmap.mmap(self._file.fileno(), 0)
            else:
                self._mmap = mmap.mmap(-1, len(new_data))
                self._mmap.write(new_data)
                self._mmap.seek(0)
        else:
            self._mmap.seek(0)
            self._mmap.write(new_data)
    
    def __del__(self):
        if hasattr(self, '_mmap'):
            self._mmap.close()
        if hasattr(self, '_file') and self._file:
            self._file.close()

# Usage
large_data = list(range(10000))
mmap_ptr = MmapPtr(large_data, "temp_data.bin")

# Data persists across program runs
retrieved_data = mmap_ptr.get()
print(f"Retrieved {len(retrieved_data)} items")
```

### 3. Atomic Operations with Smart Pointers

**Rust Atomic Smart Pointers:**
```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::sync::Arc;
use std::ptr;

struct AtomicSharedPtr<T> {
    ptr: AtomicPtr<T>,
}

impl<T> AtomicSharedPtr<T> {
    fn new(data: T) -> Self {
        let boxed = Box::new(data);
        AtomicSharedPtr {
            ptr: AtomicPtr::new(Box::into_raw(boxed)),
        }
    }
    
    fn load(&self) -> Option<&T> {
        let ptr = self.ptr.load(Ordering::Acquire);
        if ptr.is_null() {
            None
        } else {
            unsafe { Some(&*ptr) }
        }
    }
    
    fn store(&self, data: T) {
        let new_ptr = Box::into_raw(Box::new(data));
        let old_ptr = self.ptr.swap(new_ptr, Ordering::AcqRel);
        
        if !old_ptr.is_null() {
            unsafe {
                Box::from_raw(old_ptr);
            }
        }
    }
    
    fn compare_and_swap(&self, current: *mut T, new_data: T) -> Result<(), T> {
        let new_ptr = Box::into_raw(Box::new(new_data));
        
        match self.ptr.compare_exchange_weak(
            current,
            new_ptr,
            Ordering::AcqRel,
            Ordering::Acquire
        ) {
            Ok(_) => {
                if !current.is_null() {
                    unsafe { Box::from_raw(current); }
                }
                Ok(())
            }
            Err(_) => {
                unsafe { 
                    let data = Box::from_raw(new_ptr);
                    Err(*data)
                }
            }
        }
    }
}

impl<T> Drop for AtomicSharedPtr<T> {
    fn drop(&mut self) {
        let ptr = self.ptr.load(Ordering::Acquire);
        if !ptr.is_null() {
            unsafe {
                Box::from_raw(ptr);
            }
        }
    }
}

// Lock-free stack using atomic pointers
struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}

struct Node<T> {
    data: T,
    next: *mut Node<T>,
}

impl<T> LockFreeStack<T> {
    fn new() -> Self {
        LockFreeStack {
            head: AtomicPtr::new(ptr::null_mut()),
        }
    }
    
    fn push(&self, data: T) {
        let new_node = Box::into_raw(Box::new(Node {
            data,
            next: ptr::null_mut(),
        }));
        
        loop {
            let current_head = self.head.load(Ordering::Acquire);
            unsafe { (*new_node).next = current_head; }
            
            match self.head.compare_exchange_weak(
                current_head,
                new_node,
                Ordering::Release,
                Ordering::Relaxed,
            ) {
                Ok(_) => break,
                Err(_) => continue,
            }
        }
    }
    
    fn pop(&self) -> Option<T> {
        loop {
            let current_head = self.head.load(Ordering::Acquire);
            if current_head.is_null() {
                return None;
            }
            
            let next = unsafe { (*current_head).next };
            
            match self.head.compare_exchange_weak(
                current_head,
                next,
                Ordering::Release,
                Ordering::Relaxed,
            ) {
                Ok(_) => {
                    let node = unsafe { Box::from_raw(current_head) };
                    return Some(node.data);
                }
                Err(_) => continue,
            }
        }
    }
}

impl<T> Drop for LockFreeStack<T> {
    fn drop(&mut self) {
        while self.pop().is_some() {}
    }
}
```

### 4. Smart Pointers with Garbage Collection

**Python Cycle-Detecting Smart Pointer:**
```python
import weakref
import gc
from typing import Set, Optional, TypeVar, Generic, Dict, Any

T = TypeVar('T')

class GcPtr(Generic[T]):
    """Garbage collection aware smart pointer"""
    
    _registry: Dict[int, 'GcPtr'] = {}
    
    def __init__(self, obj: T):
        self._obj = obj
        self._id = id(self)
        self._references: Set[weakref.ref] = set()
        GcPtr._registry[self._id] = self
    
    def get(self) -> Optional[T]:
        return self._obj
    
    def add_reference(self, other: 'GcPtr'):
        """Add a reference to another GcPtr"""
        ref = weakref.ref(other, self._cleanup_reference)
        self._references.add(ref)
    
    def _cleanup_reference(self, ref):
        """Clean up dead references"""
        self._references.discard(ref)
    
    @classmethod
    def collect_cycles(cls):
        """Detect and break reference cycles"""
        # Simple cycle detection using DFS
        visited = set()
        in_cycle = set()
        
        def dfs(ptr_id, path):
            if ptr_id in path:
                # Found a cycle
                cycle_start = path.index(ptr_id)
                cycle_ptrs = path[cycle_start:]
                in_cycle.update(cycle_ptrs)
                return True
            
            if ptr_id in visited:
                return False
            
            visited.add(ptr_id)
            path.append(ptr_id)
            
            ptr = cls._registry.get(ptr_id)
            if ptr:
                for ref in ptr._references:
                    target = ref()
                    if target and dfs(target._id, path):
                        return True
            
            path.pop()
            return False
        
        # Check all pointers for cycles
        for ptr_id in list(cls._registry.keys()):
            if ptr_id not in visited:
                dfs(ptr_id, [])
        
        # Break cycles by converting strong references to weak ones
        for ptr_id in in_cycle:
            ptr = cls._registry.get(ptr_id)
            if ptr:
                ptr._break_cycles()
        
        return len(in_cycle)
    
    def _break_cycles(self):
        """Convert strong references to weak references"""
        # This is a simplified cycle breaking strategy
        if len(self._references) > 1:
            # Keep only the first reference, make others weak
            refs_list = list(self._references)
            self._references = {refs_list[0]}
    
    def __del__(self):
        if hasattr(self, '_id') and self._id in GcPtr._registry:
            del GcPtr._registry[self._id]

# Usage example
class CircularNode:
    def __init__(self, value):
        self.value = value
        self.next_ptr = None

# Create circular reference
node1_ptr = GcPtr(CircularNode(1))
node2_ptr = GcPtr(CircularNode(2))
node3_ptr = GcPtr(CircularNode(3))

node1_ptr.add_reference(node2_ptr)
node2_ptr.add_reference(node3_ptr)
node3_ptr.add_reference(node1_ptr)  # Creates cycle

print(f"Pointers before cycle collection: {len(GcPtr._registry)}")
cycles_found = GcPtr.collect_cycles()
print(f"Cycles found and broken: {cycles_found}")
```

## Conclusion

Smart pointers are essential tools for managing memory and resources safely and efficiently. While Python provides garbage collection and doesn't strictly need smart pointers for memory management, implementing smart pointer patterns can be valuable for resource management, explicit ownership semantics, and breaking reference cycles.

Rust's ownership system makes smart pointers fundamental to the language, providing compile-time guarantees about memory safety while enabling flexible sharing and borrowing patterns.

### Key Takeaways:

1. **Python**: Use smart pointer patterns for resource management, explicit ownership, and cycle prevention. Built-in `weakref` is often sufficient for basic needs.

2. **Rust**: Smart pointers are integral to the language. Choose `Box<T>` for owned data, `Rc<T>`/`Arc<T>` for shared ownership, and `Weak<T>` to break cycles.

3. **Performance**: Rust's zero-cost abstractions provide better performance, while Python's implementations have runtime overhead.

4. **Safety**: Rust provides compile-time safety guarantees, while Python patterns help prevent common errors but don't eliminate them entirely.

5. **Complexity**: Start with simple patterns and gradually adopt more complex ones as needed. Both languages benefit from understanding the underlying ownership and lifetime concepts.

The choice between Python and Rust smart pointer implementations depends on your specific requirements for performance, safety, development speed, and system constraints.

I've completed the comprehensive ASCII diagram for Rust smart pointer implementations! This extensive diagram covers:

**Complete Coverage:**
1. **Box<T>** - Heap allocation with RAII and move semantics
2. **Rc<T>** - Single-threaded reference counting with detailed lifecycle
3. **Arc<T>** - Thread-safe atomic reference counting 
4. **RefCell<T>** - Interior mutability with runtime borrow checking
5. **Weak<T>** - Non-owning references to break circular dependencies
6. **Mutex<T>** - Thread-safe mutability with blocking synchronization

**Advanced Topics:**
- **Common Combinations** like `Rc<RefCell<T>>` and `Arc<Mutex<T>>`
- **Dynamic Dispatch** with `Box<dyn Trait>` and vtables
- **Performance Analysis** with time/space complexity
- **Memory Layouts** showing stack vs heap organization
- **State Machines** for borrow checking and reference counting

**Practical Aspects:**
- **Decision Tree** for choosing the right smart pointer
- **Common Pitfalls** and their solutions
- **Real-world Examples** including web servers and tree structures
- **Debugging Techniques** with reference count tracking
- **Safety Guarantees** provided by Rust's type system

**Key Features Illustrated:**
- Step-by-step memory operations
- Thread safety mechanisms
- RAII (Resource Acquisition Is Initialization)
- Compile-time vs runtime safety checks
- Circular reference prevention
- Zero-cost abstractions where possible

The diagram uses ASCII art to show memory layouts, state transitions, and relationships between different smart pointer types, making it easy to understand how Rust's ownership system works at both compile-time and runtime levels.

RUST SMART POINTER COMPLETE IMPLEMENTATIONS
============================================

1. BOX<T> - HEAP ALLOCATION & OWNERSHIP
=======================================

Basic Structure:
---------------
Stack:                     Heap:
┌─────────────────────┐   ┌─────────────────────┐
│ Box<i32>            │──→│ Value: 42           │
│ ptr: *mut T         │   │ Size: 4 bytes       │
│ _marker: PhantomData│   │ Align: 4 bytes      │
└─────────────────────┘   └─────────────────────┘
Address: 0x7fff...        Address: 0x600000...

Implementation Internals:
------------------------
pub struct Box<T> {
    ptr: Unique<T>,          // Non-null, owned pointer
    _marker: PhantomData<T>, // For drop check
}

Memory Layout:
┌─────────────────────────────────────────────────────────┐
│                 Box<T> Memory Model                     │
├─────────────────────────────────────────────────────────┤
│ Stack Frame:        │ Heap Allocation:                  │
│ ┌─────────────┐    │ ┌─────────────────────────────────┐│
│ │    Box      │────┼→│         T (actual data)         ││
│ │  8 bytes    │    │ │      (size_of::<T>() bytes)     ││
│ │ (on 64-bit) │    │ └─────────────────────────────────┘│
│ └─────────────┘    │                                    │
└─────────────────────────────────────────────────────────┘

Step-by-Step Operations:
-----------------------

Step 1: Creation with Box::new()
┌─────────────────────────────────────────────────────────┐
│ let b = Box::new(42);                                   │
│                                                         │
│ 1. Allocate memory on heap: malloc(size_of::<i32>())   │
│ 2. Write value 42 to heap location                     │
│ 3. Create Box with pointer to heap location             │
│ 4. Return Box to stack                                  │
└─────────────────────────────────────────────────────────┘

Before:                    After:
Stack: [empty]            Stack:              Heap:
Heap:  [empty]            ┌─────────────┐    ┌─────────────┐
                          │ Box<i32>    │───→│ 42          │
                          │ ptr: 0x1000 │    │             │
                          └─────────────┘    └─────────────┘

Step 2: Move Semantics
┌─────────────────────────────────────────────────────────┐
│ let b1 = Box::new(42);                                  │
│ let b2 = b1;  // Move, not copy                        │
└─────────────────────────────────────────────────────────┘

Before Move:               After Move:
┌─────────────┐ Heap:     ┌─────────────┐ Heap:
│ b1: Box     │───→42     │ b1: MOVED   │ 
│ ptr: 0x1000 │           │ (invalid)   │ 
└─────────────┘           └─────────────┘ 
                          ┌─────────────┐    ┌─────────────┐
                          │ b2: Box     │───→│ 42          │
                          │ ptr: 0x1000 │    │             │
                          └─────────────┘    └─────────────┘

Step 3: Automatic Drop (RAII)
┌─────────────────────────────────────────────────────────┐
│ // When Box goes out of scope:                          │
│ impl<T> Drop for Box<T> {                               │
│     fn drop(&mut self) {                                │
│         unsafe {                                        │
│             drop_in_place(self.ptr.as_ptr());          │
│             alloc::dealloc(self.ptr.as_ptr());         │
│         }                                               │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘


2. RC<T> - REFERENCE COUNTING
=============================

Internal Structure:
------------------
┌─────────────────────────────────────────────────────────┐
│                 Rc<T> Memory Layout                     │
├─────────────────────────────────────────────────────────┤
│ Stack:              │ Heap:                             │
│ ┌─────────────┐    │ ┌─────────────────────────────────┐│
│ │ Rc<i32>     │────┼→│ RcBox<T> {                      ││
│ │ ptr: NonNull│    │ │   strong: Cell<usize>,  // 2    ││
│ └─────────────┘    │ │   weak: Cell<usize>,    // 0    ││
│                    │ │   value: T,             // 42   ││
│                    │ │ }                               ││
│                    │ └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘

Reference Counting Lifecycle:
----------------------------

Step 1: First Rc Creation
┌─────────────────────────────────────────────────────────┐
│ let rc1 = Rc::new(42);                                  │
└─────────────────────────────────────────────────────────┘

Stack:                     Heap:
┌─────────────┐           ┌─────────────────────────────────┐
│ rc1: Rc     │──────────→│ RcBox {                         │
│ ptr: 0x1000 │           │   strong: 1,  ← Initial count  │
└─────────────┘           │   weak: 0,                      │
                          │   value: 42                     │
                          │ }                               │
                          └─────────────────────────────────┘

Step 2: Clone (Increment Reference)
┌─────────────────────────────────────────────────────────┐
│ let rc2 = Rc::clone(&rc1);  // or rc1.clone()          │
│                                                         │
│ impl<T> Clone for Rc<T> {                               │
│     fn clone(&self) -> Rc<T> {                          │
│         self.inner().strong.set(                        │
│             self.inner().strong.get() + 1);            │
│         Rc { ptr: self.ptr, _marker: PhantomData }      │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘

Stack:                     Heap:
┌─────────────┐           ┌─────────────────────────────────┐
│ rc1: Rc     │──────────→│ RcBox {                         │
│ ptr: 0x1000 │     ┌────→│   strong: 2,  ← Incremented    │
└─────────────┘     │     │   weak: 0,                      │
┌─────────────┐     │     │   value: 42                     │
│ rc2: Rc     │─────┘     │ }                               │
│ ptr: 0x1000 │           └─────────────────────────────────┘
└─────────────┘

Step 3: Drop (Decrement Reference)
┌─────────────────────────────────────────────────────────┐
│ // rc1 goes out of scope                                │
│ impl<T> Drop for Rc<T> {                                │
│     fn drop(&mut self) {                                │
│         let strong = self.inner().strong.get() - 1;     │
│         self.inner().strong.set(strong);                │
│         if strong == 0 {                                │
│             drop_in_place(&mut self.ptr.as_mut().value);│
│             // Check weak count for full deallocation   │
│         }                                               │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘

After rc1 drops:           Heap:
Stack:                     ┌─────────────────────────────────┐
┌─────────────┐           │ RcBox {                         │
│ rc2: Rc     │──────────→│   strong: 1,  ← Decremented    │
│ ptr: 0x1000 │           │   weak: 0,                      │
└─────────────┘           │   value: 42   ← Still alive    │
                          │ }                               │
                          └─────────────────────────────────┘


3. ARC<T> - ATOMIC REFERENCE COUNTING (THREAD-SAFE)
===================================================

Atomic Structure:
----------------
┌─────────────────────────────────────────────────────────┐
│                Arc<T> vs Rc<T> Comparison               │
├─────────────────────────────────────────────────────────┤
│ Rc<T> (Single-threaded):   │ Arc<T> (Multi-threaded):   │
│ ┌─────────────────────────┐│ ┌─────────────────────────┐ │
│ │ RcBox {                 ││ │ ArcInner {              │ │
│ │   strong: Cell<usize>,  ││ │   strong: AtomicUsize,  │ │
│ │   weak: Cell<usize>,    ││ │   weak: AtomicUsize,    │ │
│ │   value: T,             ││ │   data: T,              │ │
│ │ }                       ││ │ }                       │ │
│ └─────────────────────────┘│ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

Thread Safety Operations:
------------------------
┌─────────────────────────────────────────────────────────┐
│ impl<T> Clone for Arc<T> {                              │
│     fn clone(&self) -> Arc<T> {                         │
│         let old_size = self.inner().strong.fetch_add(   │
│             1, Ordering::Relaxed);                      │
│         if old_size > MAX_REFCOUNT {                    │
│             abort();  // Prevent overflow               │
│         }                                               │
│         Arc { ptr: self.ptr, phantom: PhantomData }     │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘

Multi-threaded Scenario:
-----------------------
Thread 1:                  Thread 2:                  Heap:
┌─────────────┐           ┌─────────────┐           ┌─────────────────┐
│ arc1: Arc   │──────────→│ arc2: Arc   │──────────→│ ArcInner {      │
│ ptr: 0x1000 │     ┌────→│ ptr: 0x1000 │           │   strong: 2,    │
└─────────────┘     │     └─────────────┘           │   weak: 0,      │
                    │                               │   data: 42      │
                    └─────────────────────────────→ │ }               │
                                                    └─────────────────┘

Atomic Operations Visualization:
-------------------------------
┌─────────────────────────────────────────────────────────┐
│ Time  │ Thread 1      │ Thread 2      │ strong count    │
│-------│--------------│--------------│-----------------│
│ t1    │ Arc::new(42) │               │ 1               │
│ t2    │ send to T2   │               │ 1               │
│ t3    │              │ receives arc  │ 1               │
│ t4    │ clone()      │               │ 2 (atomic inc)  │
│ t5    │              │ clone()       │ 3 (atomic inc)  │
│ t6    │ drop()       │               │ 2 (atomic dec)  │
│ t7    │              │ drop()        │ 1 (atomic dec)  │
│ t8    │              │ drop()        │ 0 → deallocate  │
└─────────────────────────────────────────────────────────┘


4. REFCELL<T> - INTERIOR MUTABILITY
===================================

Runtime Borrow Checking:
-----------------------
┌─────────────────────────────────────────────────────────┐
│                RefCell<T> Internal State                │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ RefCell<i32> {                                      │ │
│ │   value: UnsafeCell<T>,        // 42                │ │
│ │   borrow: Cell<BorrowFlag>,    // Runtime state     │ │
│ │ }                                                   │ │
│ │                                                     │ │
│ │ BorrowFlag states:                                  │ │
│ │ • UNUSED = 0                                        │ │
│ │ • READING = 1, 2, 3, ... (multiple readers)        │ │
│ │ • WRITING = isize::MIN (exclusive writer)           │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

Borrow State Machine:
--------------------
┌─────────────────────────────────────────────────────────┐
│                   State Transitions                     │
│                                                         │
│         ┌─────────┐                                     │
│    ┌───→│ UNUSED  │←──── drop all borrows              │
│    │    │ (0)     │                                     │
│    │    └─────────┘                                     │
│    │         │                                          │
│    │         │ borrow()                                 │
│    │         ▼                                          │
│    │    ┌─────────┐     borrow()      ┌─────────┐      │
│    │    │READING  │◄─────────────────►│READING  │      │
│    └────│ (1)     │                   │ (2,3...)│      │
│         └─────────┘                   └─────────┘      │
│              │                             │            │
│              │ borrow_mut()                │            │
│              ▼           ┌─────────────────┘            │
│          [PANIC]         │                              │
│                          │                              │
│         ┌─────────┐      │                              │
│    ┌───→│WRITING  │◄─────┘                              │
│    │    │(isize   │                                     │
│    │    │::MIN)   │                                     │
│    │    └─────────┘                                     │
│    │         │                                          │
│    │         │ Any borrow attempt                       │
│    │         ▼                                          │
│    └─────[PANIC]                                        │
└─────────────────────────────────────────────────────────┘

RefCell Operations:
------------------

Step 1: Creating RefCell
┌─────────────────────────────────────────────────────────┐
│ let cell = RefCell::new(42);                            │
└─────────────────────────────────────────────────────────┘

Stack:
┌─────────────────────────┐
│ RefCell<i32> {          │
│   value: UnsafeCell(42),│
│   borrow: Cell(UNUSED), │
│ }                       │
└─────────────────────────┘

Step 2: Immutable Borrow
┌─────────────────────────────────────────────────────────┐
│ let borrowed = cell.borrow();  // Returns Ref<i32>      │
│                                                         │
│ impl<T> RefCell<T> {                                    │
│     pub fn borrow(&self) -> Ref<T> {                    │
│         match BorrowRef::new(&self.borrow) {            │
│             Some(b) => Ref { value: &self.value, b },   │
│             None => panic!("already mutably borrowed"), │
│         }                                               │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘

Stack:                                    RefCell State:
┌─────────────────────────┐              ┌─────────────────┐
│ borrowed: Ref<i32> {    │─────────────→│ borrow: READING │
│   value: *const i32,    │              │ (count = 1)     │
│   borrow: BorrowRef,    │              └─────────────────┘
│ }                       │
└─────────────────────────┘

Step 3: Multiple Immutable Borrows (OK)
┌─────────────────────────────────────────────────────────┐
│ let borrow1 = cell.borrow();   // count = 1             │
│ let borrow2 = cell.borrow();   // count = 2             │
│ let borrow3 = cell.borrow();   // count = 3             │
└─────────────────────────────────────────────────────────┘

Step 4: Mutable Borrow (After immutable borrows dropped)
┌─────────────────────────────────────────────────────────┐
│ let mut_borrowed = cell.borrow_mut(); // RefMut<i32>    │
│                                                         │
│ impl<T> RefCell<T> {                                    │
│     pub fn borrow_mut(&self) -> RefMut<T> {             │
│         match BorrowRefMut::new(&self.borrow) {         │
│             Some(b) => RefMut {                         │
│                 value: &mut *self.value.get(),          │
│                 borrow: b                               │
│             },                                          │
│             None => panic!("already borrowed"),         │
│         }                                               │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘

Stack:                                    RefCell State:
┌─────────────────────────┐              ┌─────────────────┐
│ mut_borrowed: RefMut    │─────────────→│ borrow: WRITING │
│ <i32> {                 │              │ (exclusive)     │
│   value: *mut i32,      │              └─────────────────┘
│   borrow: BorrowRefMut, │
│ }                       │
└─────────────────────────┘


5. RC<REFCELL<T>> - SHARED MUTABLE OWNERSHIP
============================================

Combined Pattern:
----------------
┌─────────────────────────────────────────────────────────┐
│           Rc<RefCell<T>> Memory Layout                  │
├─────────────────────────────────────────────────────────┤
│ Stack 1:        Stack 2:        Heap:                  │
│ ┌─────────┐    ┌─────────┐     ┌─────────────────────┐ │
│ │ Rc      │───→│ Rc      │────→│ RcBox {             │ │
│ │ clone   │    │ clone   │     │   strong: 2,        │ │
│ └─────────┘    └─────────┘     │   value: RefCell {  │ │
│                                │     value: T,       │ │
│                                │     borrow: state   │ │
│                                │   }                 │ │
│                                │ }                   │ │
│                                └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘

Usage Example:
-------------
┌─────────────────────────────────────────────────────────┐
│ use std::rc::Rc;                                        │
│ use std::cell::RefCell;                                 │
│                                                         │
│ let shared_data = Rc::new(RefCell::new(vec![1, 2, 3]));│
│ let clone1 = Rc::clone(&shared_data);                  │
│ let clone2 = Rc::clone(&shared_data);                  │
│                                                         │
│ // From clone1:                                         │
│ clone1.borrow_mut().push(4);  // Modify shared data    │
│                                                         │
│ // From clone2:                                         │
│ println!("{:?}", clone2.borrow());  // [1, 2, 3, 4]    │
└─────────────────────────────────────────────────────────┘


6. WEAK<T> - WEAK REFERENCES (BREAK CYCLES)
===========================================

Weak Reference Structure:
------------------------
┌─────────────────────────────────────────────────────────┐
│                 Weak<T> Memory Model                    │
├─────────────────────────────────────────────────────────┤
│ Strong Refs:         Weak Refs:         Heap:          │
│ ┌─────────┐         ┌─────────┐        ┌─────────────┐  │
│ │ Rc<T>   │────────→│ Weak<T> │───────→│ RcBox {     │  │
│ │ (owner) │         │ (observer)       │   strong: 1 │  │
│ └─────────┘         └─────────┘        │   weak: 1   │  │
│                                        │   value: T  │  │
│                                        │ }           │  │
│                                        └─────────────┘  │
└─────────────────────────────────────────────────────────┘

Weak Reference Lifecycle:
------------------------

Step 1: Create Weak from Rc
┌─────────────────────────────────────────────────────────┐
│ let rc = Rc::new(42);                                   │
│ let weak = Rc::downgrade(&rc);                          │
└─────────────────────────────────────────────────────────┘

Stack:                     Heap:
┌─────────────┐           ┌─────────────────────────────────┐
│ rc: Rc      │──────────→│ RcBox {                         │
│ ptr: 0x1000 │           │   strong: 1,  ← Rc exists      │
└─────────────┘           │   weak: 1,    ← Weak exists    │
┌─────────────┐           │   value: 42                     │
│ weak: Weak  │──────────→│ }                               │
│ ptr: 0x1000 │           └─────────────────────────────────┘
└─────────────┘

Step 2: Strong Reference Dropped
┌─────────────────────────────────────────────────────────┐
│ drop(rc);  // Strong count goes to 0                    │
│            // Value is dropped, but RcBox remains       │
└─────────────────────────────────────────────────────────┘

Stack:                     Heap:
┌─────────────┐           ┌─────────────────────────────────┐
│ weak: Weak  │──────────→│ RcBox {                         │
│ ptr: 0x1000 │           │   strong: 0,  ← Value dropped  │
└─────────────┘           │   weak: 1,                      │
                          │   value: [dropped]              │
                          │ }                               │
                          └─────────────────────────────────┘

Step 3: Weak::upgrade() Attempt
┌─────────────────────────────────────────────────────────┐
│ match weak.upgrade() {                                  │
│     Some(rc) => println!("Still alive!"),              │
│     None => println!("Value was dropped"),  ← This     │
│ }                                                       │
│                                                         │
│ impl<T> Weak<T> {                                       │
│     pub fn upgrade(&self) -> Option<Rc<T>> {            │
│         if self.inner().strong.get() == 0 {             │
│             None  // Value already dropped              │
│         } else {                                        │
│             // Increment strong count and return Some   │
│             Some(Rc { ptr: self.ptr, ... })             │
│         }                                               │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘


7. MUTEX<T> & ARC<MUTEX<T>> - THREAD-SAFE MUTABILITY
====================================================

Mutex Structure:
---------------
┌─────────────────────────────────────────────────────────┐
│                  Mutex<T> Internal                      │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Mutex<i32> {                                        │ │
│ │   inner: sys::Mutex,      // OS-level mutex         │ │
│ │   poison: Flag,           // Panic detection        │ │
│ │   data: UnsafeCell<T>,    // Protected data          │ │
│ │ }                                                   │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

Arc<Mutex<T>> Multi-threaded Pattern:
------------------------------------

Thread 1:                  Thread 2:                  Shared Data:
┌─────────────┐           ┌─────────────┐           ┌─────────────────┐
│ Arc<Mutex>  │──────────→│ Arc<Mutex>  │──────────→│ ArcInner {      │
│ (clone)     │     ┌────→│ (clone)     │           │   strong: 2,    │
└─────────────┘     │     └─────────────┘           │   data: Mutex { │
                    │                               │     inner: ..., │
                    │                               │     data: T     │
                    └─────────────────────────────→ │   }             │
                                                    │ }               │
                                                    └─────────────────┘

Mutex Lock/Unlock Cycle:
-----------------------
┌─────────────────────────────────────────────────────────┐
│ Time │ Thread 1        │ Thread 2        │ Mutex State │
│------│----------------│----------------│-------------│
│ t1   │ lock()         │                 │ LOCKED (T1) │
│ t2   │ modify data    │ lock() [BLOCK]  │ LOCKED (T1) │
│ t3   │ unlock()       │ [BLOCKED]       │ UNLOCKED    │
│ t4   │                │ acquire lock    │ LOCKED (T2) │
│ t5   │ lock() [BLOCK] │ modify data     │ LOCKED (T2) │
│ t6   │ [BLOCKED]      │ unlock()        │ UNLOCKED    │
│ t7   │ acquire lock   │                 │ LOCKED (T1) │
└─────────────────────────────────────────────────────────┘

MutexGuard RAII Pattern:
-----------------------
┌─────────────────────────────────────────────────────────┐
│ {                                                       │
│     let guard = mutex.lock().unwrap();                  │
│     // MutexGuard created, mutex locked                 │
│     *guard = 42;  // Modify protected data              │
│ }  ← guard goes out of scope                            │
│    ← Drop trait automatically unlocks mutex             │
│                                                         │
│ impl<T> Drop for MutexGuard<'_, T> {                    │
│     fn drop(&mut self) {                                │
│         unsafe { self.lock.inner.unlock(); }            │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘


8. COMPLETE SMART POINTER DECISION TREE
=======================================

┌─────────────────────────────────────────────────────────┐
│                 Smart Pointer Selection                 │
│                                                         │
│ Single Owner? ──── YES ─────→ Box<T>                   │
│     │                                                   │
│     NO                                                  │
│     │                                                   │
│     ▼                                                   │
│ Multiple Owners? ── YES ─┐                             │
│     │                    │                             │
│     NO                   │                             │
│     │                    ▼                             │
│     │              Thread Safe? ─── YES ───→ Arc<T>    │
│     │                    │                             │
│     │                    NO                            │
│     │                    │                             │
│     │                    ▼                             │
│     │              Single Thread ────→ Rc<T>          │
│     │                                                   │
│     ▼                                                   │
│ Interior Mutability? ─ YES ─┐                         │
│     │                        │                         │
│     NO                       ▼                         │
│     │                Thread Safe? ─ YES ─→ Mutex<T>    │
│     │                        │                         │
│     │                        NO                        │
│     │                        │                         │
│     │                        ▼                         │
│     │                Single Thread ──→ RefCell<T>      │
│     │                                                   │
│     ▼                                                   │
│ Break Cycles? ──── YES ─────→ Weak<T>                 │
│     │                                                   │
│     NO                                                  │
│     │                                                   │
│     ▼                                                   │
│ Use References (&T, &mut T)                        │
└─────────────────────────────────────────────────────────┘


9. COMMON COMBINATIONS & PATTERNS
=================================

Pattern 1: Rc<RefCell<T>> - Shared Mutable Data (Single Thread)
---------------------------------------------------------------
┌─────────────────────────────────────────────────────────┐
│ use std::rc::Rc;                                        │
│ use std::cell::RefCell;                                 │
│                                                         │
│ struct Node {                                           │
│     value: i32,                                         │
│     children: Vec<Rc<RefCell<Node>>>,                   │
│     parent: Option<Weak<RefCell<Node>>>,                │
│ }                                                       │
│                                                         │
│ // Create tree structure:                               │
│ let root = Rc::new(RefCell::new(Node {                  │
│     value: 1,                                           │
│     children: vec![],                                   │
│     parent: None,                                       │
│ }));                                                    │
│                                                         │
│ let child = Rc::new(RefCell::new(Node {                 │
│     value: 2,                                           │
│     children: vec![],                                   │
│     parent: Some(Rc::downgrade(&root)),                 │
│ }));                                                    │
│                                                         │
│ root.borrow_mut().children.push(Rc::clone(&child));    │
└─────────────────────────────────────────────────────────┘

Memory Layout:
             Stack:                   Heap:
┌─────────────────────┐              ┌─────────────────────────┐
│ root: Rc<RefCell>   │─────────────→│ RcBox {                 │
└─────────────────────┘              │   strong: 2,            │
┌─────────────────────┐              │   value: RefCell {      │
│ child: Rc<RefCell>  │──────────────┼─→   borrow: UNUSED,     │
└─────────────────────┘              │     value: Node {       │
                                     │       value: 1,         │
                                     │       children: [───────┼─┐
                                     │       parent: None      │ │
                                     │     }                   │ │
                                     │   }                     │ │
                                     │ }                       │ │
                                     └─────────────────────────┘ │
                                                                 │
                                     ┌─────────────────────────┐ │
                                     │ RcBox {                 │ │
                                     │   strong: 1,            │◄┘
                                     │   weak: 1,              │
                                     │   value: RefCell {      │
                                     │     borrow: UNUSED,     │
                                     │     value: Node {       │
                                     │       value: 2,         │
                                     │       children: [],     │
                                     │       parent: Weak ─────┼──┐
                                     │     }                   │  │
                                     │   }                     │  │
                                     │ }                       │  │
                                     └─────────────────────────┘  │
                                            ▲                     │
                                            └─────────────────────┘

Pattern 2: Arc<Mutex<T>> - Shared Mutable Data (Multi-thread)
-------------------------------------------------------------
┌─────────────────────────────────────────────────────────┐
│ use std::sync::{Arc, Mutex};                            │
│ use std::thread;                                        │
│                                                         │
│ let counter = Arc::new(Mutex::new(0));                  │
│ let mut handles = vec![];                               │
│                                                         │
│ for i in 0..10 {                                        │
│     let counter_clone = Arc::clone(&counter);           │
│     let handle = thread::spawn(move || {                │
│         let mut num = counter_clone.lock().unwrap();    │
│         *num += 1;                                      │
│     });                                                 │
│     handles.push(handle);                               │
│ }                                                       │
│                                                         │
│ for handle in handles {                                 │
│     handle.join().unwrap();                             │
│ }                                                       │
│                                                         │
│ println!("Result: {}", *counter.lock().unwrap());      │
└─────────────────────────────────────────────────────────┘

Multi-thread Execution:
Thread 1: Arc::clone  ┌─────────────────────────────────┐
Thread 2: Arc::clone  │         Shared Memory           │
Thread 3: Arc::clone  │   ┌─────────────────────────┐   │
    ...       ───────→│   │ ArcInner {              │   │
Thread 10: Arc::clone │   │   strong: 10,           │   │
                      │   │   data: Mutex {         │   │
                      │   │     inner: ...,         │   │
                      │   │     data: 0 → 1 → ... 10│   │
                      │   │   }                     │   │
                      │   │ }                       │   │
                      │   └─────────────────────────┘   │
                      └─────────────────────────────────┘

Pattern 3: Box<dyn Trait> - Dynamic Dispatch
--------------------------------------------
┌─────────────────────────────────────────────────────────┐
│ trait Draw {                                            │
│     fn draw(&self);                                     │
│ }                                                       │
│                                                         │
│ struct Circle { radius: f64 }                           │
│ struct Rectangle { width: f64, height: f64 }            │
│                                                         │
│ impl Draw for Circle {                                  │
│     fn draw(&self) { println!("Drawing circle"); }     │
│ }                                                       │
│                                                         │
│ impl Draw for Rectangle {                               │
│     fn draw(&self) { println!("Drawing rectangle"); }  │
│ }                                                       │
│                                                         │
│ let shapes: Vec<Box<dyn Draw>> = vec![                  │
│     Box::new(Circle { radius: 5.0 }),                  │
│     Box::new(Rectangle { width: 3.0, height: 4.0 }),   │
│ ];                                                      │
│                                                         │
│ for shape in &shapes {                                  │
│     shape.draw(); // Dynamic dispatch                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘

Fat Pointer Layout:
Stack:                         Heap:
┌─────────────────────────────┐ ┌─────────────────────────┐
│ shapes: Vec<Box<dyn Draw>>  │ │ Circle { radius: 5.0 }  │
│ ┌─────────────────────────┐ │ └─────────────────────────┘
│ │ Box<dyn Draw> {         │ │           ▲
│ │   data_ptr: ────────────┼─┼───────────┘
│ │   vtable_ptr: ──────────┼─┼─┐ ┌─────────────────────────┐
│ │ }                       │ │ └→│ VTable for Circle       │
│ └─────────────────────────┘ │   │ - size: 8               │
│ ┌─────────────────────────┐ │   │ - align: 8              │
│ │ Box<dyn Draw> {         │ │   │ - destructor: drop_Circle│
│ │   data_ptr: ────────────┼─┼─┐ │ - draw: Circle::draw    │
│ │   vtable_ptr: ──────────┼─┼─┼─└─────────────────────────┘
│ │ }                       │ │ │
│ └─────────────────────────┘ │ │ ┌─────────────────────────┐
└─────────────────────────────┘ │ │Rectangle{width:3,height:4}│
                                └→└─────────────────────────┘
                                  ┌─────────────────────────┐
                                  │ VTable for Rectangle    │
                                  │ - size: 16              │
                                  │ - align: 8              │
                                  │ - destructor: drop_Rect │
                                  │ - draw: Rectangle::draw │
                                  └─────────────────────────┘


10. PERFORMANCE CHARACTERISTICS
===============================

Time Complexity Analysis:
------------------------
┌─────────────────────────────────────────────────────────┐
│ Smart Pointer │ Creation │ Clone  │ Access │ Drop      │
│──────────────│─────────│───────│───────│──────────│
│ Box<T>        │ O(1)     │ N/A    │ O(1)   │ O(1)      │
│ Rc<T>         │ O(1)     │ O(1)   │ O(1)   │ O(1)*     │
│ Arc<T>        │ O(1)     │ O(1)   │ O(1)   │ O(1)*     │
│ RefCell<T>    │ O(1)     │ O(1)   │ O(1)** │ O(1)      │
│ Mutex<T>      │ O(1)     │ O(1)   │ O(1)***│ O(1)      │
│ Weak<T>       │ O(1)     │ O(1)   │ O(1)** │ O(1)      │
└─────────────────────────────────────────────────────────┘
*  = O(1) unless last reference (then O(drop(T)))
** = O(1) unless borrow check fails (then panic)
*** = O(1) unless lock contention (then blocks)

Memory Overhead:
---------------
┌─────────────────────────────────────────────────────────┐
│ Smart Pointer │ Overhead (64-bit)   │ Notes             │
│──────────────│────────────────────│──────────────────│
│ Box<T>        │ 8 bytes (ptr)       │ Minimal overhead  │
│ Rc<T>         │ 8 bytes + 16 bytes  │ ptr + control blk │
│ Arc<T>        │ 8 bytes + 16 bytes  │ ptr + atomic ctrl │
│ RefCell<T>    │ size_of::<T>() + 8  │ value + borrow    │
│ Mutex<T>      │ size_of::<T>() + OS │ platform specific │
│ Weak<T>       │ 8 bytes             │ just a pointer    │
└─────────────────────────────────────────────────────────┘

Cache Performance:
-----------------
┌─────────────────────────────────────────────────────────┐
│                 Memory Layout Impact                    │
│                                                         │
│ Box<T>: ████ (excellent - data inline on heap)         │
│ Rc<T>:  ███░ (good - control block adjacent)           │
│ Arc<T>: ███░ (good - atomic overhead minimal)          │
│ RefCell<T>: ████ (excellent - no indirection)          │
│ Mutex<T>: ██░░ (fair - OS synchronization overhead)    │
│                                                         │
│ ████ = Excellent   ███░ = Good                         │
│ ██░░ = Fair        █░░░ = Poor                         │
└─────────────────────────────────────────────────────────┘


11. COMMON PITFALLS & SOLUTIONS
===============================

Pitfall 1: RefCell Borrow Panics
--------------------------------
┌─────────────────────────────────────────────────────────┐
│ // ❌ WRONG - Will panic!                               │
│ let cell = RefCell::new(42);                            │
│ let borrow1 = cell.borrow_mut();                        │
│ let borrow2 = cell.borrow();     // PANIC!             │
│                                                         │
│ // ✅ CORRECT - Control borrow scope                    │
│ let cell = RefCell::new(42);                            │
│ {                                                       │
│     let mut borrow = cell.borrow_mut();                 │
│     *borrow = 24;                                       │
│ } // borrow dropped here                                │
│ let read_borrow = cell.borrow(); // OK!                 │
└─────────────────────────────────────────────────────────┘

Pitfall 2: Circular References with Rc
--------------------------------------
┌─────────────────────────────────────────────────────────┐
│ // ❌ WRONG - Memory leak!                              │
│ struct Node {                                           │
│     children: Vec<Rc<RefCell<Node>>>,                   │
│     parent: Option<Rc<RefCell<Node>>>, // Strong cycle! │
│ }                                                       │
│                                                         │
│ // ✅ CORRECT - Use Weak for parent                     │
│ struct Node {                                           │
│     children: Vec<Rc<RefCell<Node>>>,                   │
│     parent: Option<Weak<RefCell<Node>>>, // Weak ref!   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘

Pitfall 3: Deadlock with Multiple Mutexes
-----------------------------------------
┌─────────────────────────────────────────────────────────┐
│ // ❌ WRONG - Potential deadlock!                       │
│ let mutex1 = Arc::new(Mutex::new(1));                   │
│ let mutex2 = Arc::new(Mutex::new(2));                   │
│                                                         │
│ // Thread 1: lock mutex1 then mutex2                    │
│ // Thread 2: lock mutex2 then mutex1  ← Deadlock!      │
│                                                         │
│ // ✅ CORRECT - Always acquire in same order            │
│ // Both threads: always lock mutex1 before mutex2      │
│ let _guard1 = mutex1.lock().unwrap();                   │
│ let _guard2 = mutex2.lock().unwrap();                   │
└─────────────────────────────────────────────────────────┘


12. COMPILE-TIME VS RUNTIME CHECKS
==================================

Ownership System Summary:
------------------------
┌─────────────────────────────────────────────────────────┐
│                    Compile Time                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ • Box<T>     - Ownership transfer                   │ │
│ │ • &T, &mut T - Borrowing rules                      │ │
│ │ • Rc<T>      - Single-threaded sharing             │ │
│ │ • Arc<T>     - Multi-threaded sharing              │ │
│ │ • Move semantics enforcement                        │ │
│ │ • Lifetime checking                                 │ │
│ └─────────────────────────────────────────────────────┘ │
│                         │                               │
│                         ▼                               │
│                    Runtime                              │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ • RefCell<T> - Dynamic borrow checking              │ │
│ │ • Mutex<T>   - Thread synchronization               │ │
│ │ • Weak<T>    - Upgrade/downgrade operations         │ │
│ │ • Reference counting (Rc/Arc)                       │ │
│ │ • Panic on borrow violations                        │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

Safety Guarantees:
-----------------
┌─────────────────────────────────────────────────────────┐
│ Memory Safety:                                          │
│ ✓ No null pointer dereference                          │
│ ✓ No buffer overflows                                   │
│ ✓ No use-after-free                                     │
│ ✓ No double-free                                        │
│ ✓ No data races                                         │
│                                                         │
│ Thread Safety:                                          │
│ ✓ Send/Sync traits enforce thread safety               │
│ ✓ Arc<T> provides atomic reference counting             │
│ ✓ Mutex<T> provides mutual exclusion                    │
│ ✓ Channels provide message passing                      │
│                                                         │
│ Type Safety:                                            │
│ ✓ No invalid type casts                                 │
│ ✓ No uninitialized memory access                       │
│ ✓ Strong type checking at compile time                  │
└─────────────────────────────────────────────────────────┘


13. REAL-WORLD USAGE PATTERNS
=============================

Web Server Example:
------------------
┌─────────────────────────────────────────────────────────┐
│ use std::sync::{Arc, Mutex};                            │
│ use std::collections::HashMap;                          │
│ use std::thread;                                        │
│                                                         │
│ // Shared application state                             │
│ struct AppState {                                       │
│     connections: Mutex<HashMap<u32, Connection>>,       │
│     config: Config,  // Immutable after startup        │
│ }                                                       │
│                                                         │
│ fn main() {                                             │
│     let state = Arc::new(AppState {                     │
│         connections: Mutex::new(HashMap::new()),        │
│         config: Config::load(),                         │
│     });                                                 │
│                                                         │
│     for _ in 0..num_cpus::get() {                       │
│         let state_clone = Arc::clone(&state);           │
│         thread::spawn(move || {                         │
│             // Worker thread with shared state access   │
│             handle_requests(state_clone);               │
│         });                                             │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘

Memory Layout:
Main Thread:                Worker Threads:
┌─────────────┐              ┌─────────────┐
│ state: Arc  │─────────────→│ Arc clones  │
└─────────────┘              └─────────────┘
       │                            │
       ▼                            ▼
┌─────────────────────────────────────────────┐
│            Shared AppState                  │
│ ┌─────────────────────────────────────────┐ │
│ │ connections: Mutex<HashMap>             │ │
│ │ config: Config (read-only)              │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘

Graph/Tree Structures:
---------------------
┌─────────────────────────────────────────────────────────┐
│ // Binary Tree with parent pointers                     │
│ struct TreeNode {                                       │
│     value: i32,                                         │
│     left: Option<Rc<RefCell<TreeNode>>>,                │
│     right: Option<Rc<RefCell<TreeNode>>>,               │
│     parent: Option<Weak<RefCell<TreeNode>>>,            │
│ }                                                       │
│                                                         │
│ impl TreeNode {                                         │
│     fn new(value: i32) -> Rc<RefCell<Self>> {           │
│         Rc::new(RefCell::new(TreeNode {                 │
│             value,                                      │
│             left: None,                                 │
│             right: None,                                │
│             parent: None,                               │
│         }))                                             │
│     }                                                   │
│                                                         │
│     fn add_child(&mut self, child: Rc<RefCell<TreeNode>>) {│
│         child.borrow_mut().parent =                     │
│             Some(Rc::downgrade(&Rc::new(RefCell::new(*self))));│
│         if self.left.is_none() {                        │
│             self.left = Some(child);                    │
│         } else {                                        │
│             self.right = Some(child);                   │
│         }                                               │
│     }                                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘


14. DEBUGGING SMART POINTERS
============================

Debug Output Examples:
---------------------
┌─────────────────────────────────────────────────────────┐
│ #[derive(Debug)]                                        │
│ struct Data { value: i32 }                              │
│                                                         │
│ let boxed = Box::new(Data { value: 42 });               │
│ println!("{:?}", boxed);                                │
│ // Output: Data { value: 42 }                           │
│                                                         │
│ let rc = Rc::new(Data { value: 42 });                   │
│ println!("{:?}", rc);                                   │
│ // Output: Data { value: 42 }                           │
│ println!("Strong count: {}", Rc::strong_count(&rc));    │
│ // Output: Strong count: 1                              │
│                                                         │
│ let weak = Rc::downgrade(&rc);                          │
│ println!("Weak count: {}", Rc::weak_count(&rc));        │
│ // Output: Weak count: 1                                │
│                                                         │
│ let cell = RefCell::new(Data { value: 42 });            │
│ println!("{:?}", cell);                                 │
│ // Output: RefCell { value: Data { value: 42 } }        │
└─────────────────────────────────────────────────────────┘

Reference Count Tracking:
-------------------------
┌─────────────────────────────────────────────────────────┐
│ let rc1 = Rc::new(42);                                  │
│ println!("Count after creation: {}", Rc::strong_count(&rc1));│
│ // Output: Count after creation: 1                      │
│                                                         │
│ {                                                       │
│     let rc2 = Rc::clone(&rc1);                          │
│     let rc3 = Rc::clone(&rc1);                          │
│     println!("Count with clones: {}", Rc::strong_count(&rc1));│
│     // Output: Count with clones: 3                     │
│ } // rc2 and rc3 dropped here                           │
│                                                         │
│ println!("Count after scope: {}", Rc::strong_count(&rc1));│
│ // Output: Count after scope: 1                         │
└─────────────────────────────────────────────────────────┘

This comprehensive diagram covers all major Rust smart pointer implementations, their internal workings, memory layouts, common patterns, performance characteristics, and real-world usage examples. Each section builds upon the previous ones to give you a complete understanding of Rust's memory management system through smart pointers.