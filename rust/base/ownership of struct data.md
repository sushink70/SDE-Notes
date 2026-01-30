# Comprehensive Guide to Ownership of Struct Data in Rust

## Foundational Mental Model

Before diving into mechanics, understand this core principle: **Rust's ownership system treats structs as single ownership units, but their fields can have independent ownership semantics**. This creates a layered ownership model where the struct itself has an owner, and each field contributes to the struct's overall ownership behavior.

Think of it as **compositional ownership** — the whole inherits properties from its parts.

---

## 1. Basic Struct Ownership

### 1.1 Stack-Allocated Structs (Copy Types)

```rust
#[derive(Copy, Clone, Debug)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let p1 = Point { x: 10, y: 20 };
    let p2 = p1;  // Bitwise copy, p1 still valid
    
    println!("{:?} {:?}", p1, p2);  // Both accessible
}
```

**Key Insight**: A struct is `Copy` **if and only if** all its fields are `Copy`. This is Rust's compositional type system at work.

### 1.2 Heap-Allocated Structs (Move Semantics)

```rust
#[derive(Debug)]
struct User {
    username: String,  // String is NOT Copy
    age: u32,         // u32 IS Copy
}

fn main() {
    let u1 = User {
        username: String::from("alice"),
        age: 30,
    };
    
    let u2 = u1;  // MOVE occurs (String field prevents Copy)
    // println!("{:?}", u1);  // ERROR: value borrowed after move
    println!("{:?}", u2);     // OK
}
```

**Critical Understanding**: Even though `age` is `Copy`, the entire struct follows move semantics because `username` is not `Copy`. The **most restrictive** field determines the struct's behavior.

---

## 2. Partial Moves: The Hidden Complexity

This is where most intermediate Rust programmers stumble.

### 2.1 Moving Individual Fields

```rust
struct Container {
    data: String,
    count: i32,
}

fn main() {
    let c = Container {
        data: String::from("hello"),
        count: 42,
    };
    
    let s = c.data;   // Partial move: only `data` moved
    let n = c.count;  // Copy (i32 is Copy)
    
    // println!("{:?}", c);      // ERROR: c.data was moved
    // println!("{}", c.data);   // ERROR: data moved
    println!("{}", c.count);     // OK: count is Copy
}
```

**Mental Model**: After a partial move:
- The struct as a whole becomes **partially invalidated**
- Non-moved `Copy` fields remain accessible
- Non-moved `!Copy` fields become inaccessible (to prevent double-free)
- The struct itself cannot be used as a whole

### 2.2 Partial Moves in Pattern Matching

```rust
struct Packet {
    header: String,
    payload: Vec<u8>,
    id: u64,
}

fn process(packet: Packet) {
    let Packet { header, payload, id } = packet;
    
    // All fields moved out individually
    // `packet` is now fully moved and unusable
    
    println!("Processing: {}", header);
    println!("Payload size: {}", payload.len());
    println!("ID: {}", id);
}
```

**Pattern Insight**: Destructuring with `let` performs individual field moves. Use references to prevent this:

```rust
fn process_borrow(packet: &Packet) {
    let Packet { header, payload, id } = packet;
    // All are references: &String, &Vec<u8>, &u64
    
    // Original `packet` still valid
}
```

---

## 3. Struct Field Ownership Patterns

### 3.1 Owned Data (Full Control)

```rust
struct Document {
    title: String,
    content: String,
    tags: Vec<String>,
}

impl Document {
    fn new(title: String, content: String) -> Self {
        Document {
            title,
            content,
            tags: Vec::new(),
        }
    }
    
    // Consuming method: takes ownership
    fn into_archive(self) -> ArchivedDocument {
        ArchivedDocument {
            title: self.title,  // Move ownership to new struct
            summary: self.content[..100.min(self.content.len())].to_string(),
        }
    }
}

struct ArchivedDocument {
    title: String,
    summary: String,
}
```

**Design Principle**: Owned fields give you maximum flexibility but impose move semantics. Use when the struct should have exclusive ownership of its data.

### 3.2 Borrowed Data (Lifetimes Enter)

```rust
struct Excerpt<'a> {
    text: &'a str,
    author: &'a str,
}

impl<'a> Excerpt<'a> {
    fn new(text: &'a str, author: &'a str) -> Self {
        Excerpt { text, author }
    }
    
    fn display(&self) {
        println!("\"{}\" - {}", self.text, self.author);
    }
}

fn main() {
    let book = String::from("To be or not to be");
    let author = String::from("Shakespeare");
    
    let excerpt = Excerpt::new(&book, &author);
    excerpt.display();
    
    // book and author must outlive excerpt
}
```

**Lifetime Insight**: The `'a` lifetime parameter creates a constraint: `Excerpt` cannot outlive the data it borrows. This is **borrow-based ownership** — you don't own the data, but you have permission to use it.

### 3.3 Reference-Counted Data (Shared Ownership)

```rust
use std::rc::Rc;

#[derive(Clone)]
struct Node {
    value: i32,
    parent: Option<Rc<Node>>,
}

fn main() {
    let root = Rc::new(Node {
        value: 1,
        parent: None,
    });
    
    let child1 = Node {
        value: 2,
        parent: Some(Rc::clone(&root)),  // Shared ownership
    };
    
    let child2 = Node {
        value: 3,
        parent: Some(Rc::clone(&root)),  // Multiple owners
    };
    
    println!("Root refcount: {}", Rc::strong_count(&root));  // 3
}
```

**Pattern Recognition**: Use `Rc<T>` when:
- Multiple parts of your program need to read the same data
- Ownership relationships form a DAG (not strict tree)
- Single-threaded context only

For multi-threaded: `Arc<T>` (Atomic Reference Counted)

---

## 4. Advanced Ownership Patterns

### 4.1 Interior Mutability with RefCell

```rust
use std::cell::RefCell;

struct Cache {
    data: RefCell<Vec<String>>,  // Mutable through shared reference
    max_size: usize,
}

impl Cache {
    fn new(max_size: usize) -> Self {
        Cache {
            data: RefCell::new(Vec::new()),
            max_size,
        }
    }
    
    fn add(&self, item: String) {  // Note: &self, not &mut self
        let mut data = self.data.borrow_mut();
        
        if data.len() >= self.max_size {
            data.remove(0);
        }
        data.push(item);
    }
    
    fn get(&self, index: usize) -> Option<String> {
        let data = self.data.borrow();
        data.get(index).cloned()
    }
}
```

**Mental Model**: `RefCell<T>` moves borrow checking from **compile-time to runtime**. Use when:
- You need mutability through shared references
- You're certain the borrow rules won't be violated at runtime
- Implementing patterns like observer, cache, or complex data structures

**Warning**: Runtime borrow violations cause panics, not compile errors.

### 4.2 Combining Rc and RefCell (Shared Mutable Ownership)

```rust
use std::rc::Rc;
use std::cell::RefCell;

type Link = Option<Rc<RefCell<Node>>>;

struct Node {
    value: i32,
    next: Link,
}

struct LinkedList {
    head: Link,
}

impl LinkedList {
    fn new() -> Self {
        LinkedList { head: None }
    }
    
    fn push_front(&mut self, value: i32) {
        let new_node = Rc::new(RefCell::new(Node {
            value,
            next: self.head.take(),
        }));
        self.head = Some(new_node);
    }
    
    fn modify_head(&self, new_value: i32) {
        if let Some(ref node) = self.head {
            node.borrow_mut().value = new_value;
        }
    }
}
```

**Pattern**: `Rc<RefCell<T>>` is the idiomatic Rust pattern for shared, mutable ownership in single-threaded contexts. Think of it as Rust's "managed pointer."

---

## 5. Zero-Cost Abstractions: Performance Implications

### 5.1 Size and Layout

```rust
use std::mem;

struct Compact {
    a: u8,
    b: u32,
    c: u16,
}

struct Optimized {
    b: u32,  // Reordered for alignment
    c: u16,
    a: u8,
}

fn main() {
    println!("Compact: {}", mem::size_of::<Compact>());    // 12 bytes (padding)
    println!("Optimized: {}", mem::size_of::<Optimized>());  // 8 bytes
}
```

**Optimization Insight**: Field order matters for memory efficiency. Rust doesn't reorder fields automatically (unlike C compilers with `-O3`). Put larger types first.

### 5.2 Move vs Copy Performance

```rust
struct Large {
    data: [u8; 1024],
}

struct Referenced {
    data: Box<[u8; 1024]>,  // Heap allocation
}

fn move_large(l: Large) {
    // Copies 1024 bytes on the stack
}

fn move_boxed(r: Referenced) {
    // Copies only 8 bytes (pointer size)
}
```

**Performance Model**:
- Stack moves copy the entire struct (cheap for small structs)
- Heap allocations (`Box`, `String`, `Vec`) move only the pointer
- Choose based on size and usage patterns

---

## 6. Ownership and Methods: self, &self, &mut self

### 6.1 Consuming Self (Ownership Transfer)

```rust
struct Builder {
    config: String,
}

impl Builder {
    fn build(self) -> Product {  // Consumes self
        Product {
            config: self.config,  // Move ownership into Product
        }
    }
}

struct Product {
    config: String,
}

fn main() {
    let builder = Builder {
        config: String::from("settings"),
    };
    
    let product = builder.build();
    // builder is now moved, unusable
}
```

**Use Case**: Builder pattern, state transitions, transformations.

### 6.2 Shared Borrow (&self)

```rust
struct Database {
    records: Vec<String>,
}

impl Database {
    fn count(&self) -> usize {  // Read-only access
        self.records.len()
    }
    
    fn contains(&self, item: &str) -> bool {
        self.records.iter().any(|r| r == item)
    }
}
```

**Use Case**: Query operations, getters, non-mutating computations.

### 6.3 Mutable Borrow (&mut self)

```rust
impl Database {
    fn insert(&mut self, record: String) {
        self.records.push(record);
    }
    
    fn clear(&mut self) {
        self.records.clear();
    }
}
```

**Use Case**: Mutations, updates, state changes.

---

## 7. Common Ownership Pitfalls and Solutions

### 7.1 The "Cannot Move Out of Borrowed Content" Error

```rust
struct Container {
    items: Vec<String>,
}

impl Container {
    fn get_first(&self) -> String {
        // self.items[0]  // ERROR: cannot move out of indexed content
        self.items[0].clone()  // Solution 1: Clone
    }
    
    fn get_first_ref(&self) -> &str {
        &self.items[0]  // Solution 2: Return reference
    }
    
    fn take_first(&mut self) -> Option<String> {
        if self.items.is_empty() {
            None
        } else {
            Some(self.items.remove(0))  // Solution 3: Actual removal
        }
    }
}
```

**Diagnostic Thinking**:
1. Why does the error occur? You're trying to move owned data through a shared reference.
2. What are your options? Clone, borrow, or take ownership.
3. Which fits your use case? Depends on whether you need ownership or just access.

### 7.2 The "Field Already Borrowed" Error with RefCell

```rust
use std::cell::RefCell;

struct Counter {
    value: RefCell<i32>,
}

impl Counter {
    fn increment_and_get(&self) -> i32 {
        let mut val = self.value.borrow_mut();
        *val += 1;
        *val
        // borrow_mut() is dropped here
    }
    
    fn bad_example(&self) {
        let mut val1 = self.value.borrow_mut();
        // let mut val2 = self.value.borrow_mut();  // PANIC at runtime
        *val1 += 1;
    }
}
```

**Prevention Strategy**: Keep `RefCell` borrows as short as possible. Drop them explicitly if needed:

```rust
fn good_example(&self) {
    {
        let mut val = self.value.borrow_mut();
        *val += 1;
    }  // val dropped, borrow released
    
    // Now safe to borrow again
    let val = self.value.borrow();
    println!("{}", *val);
}
```

---

## 8. Advanced Pattern: Self-Referential Structs

This is one of the hardest problems in Rust.

### 8.1 The Problem

```rust
// This won't compile:
// struct SelfRef {
//     data: String,
//     ptr: &str,  // Wants to point into `data`
// }
```

**Why It Fails**: When `SelfRef` moves, `data` moves to a new memory location, but `ptr` still points to the old location (dangling pointer).

### 8.2 Solution: Pin and Unsafe

```rust
use std::pin::Pin;
use std::marker::PhantomPinned;

struct SelfReferential {
    data: String,
    pointer: *const String,  // Raw pointer
    _pin: PhantomPinned,
}

impl SelfReferential {
    fn new(data: String) -> Pin<Box<Self>> {
        let mut boxed = Box::pin(SelfReferential {
            data,
            pointer: std::ptr::null(),
            _pin: PhantomPinned,
        });
        
        let ptr: *const String = &boxed.data;
        unsafe {
            let mut_ref = Pin::as_mut(&mut boxed);
            Pin::get_unchecked_mut(mut_ref).pointer = ptr;
        }
        
        boxed
    }
    
    fn get_data(&self) -> &str {
        &self.data
    }
    
    fn get_pointer_data(&self) -> &str {
        unsafe { &*self.pointer }
    }
}
```

**Advanced Insight**: `Pin<T>` prevents a value from being moved in memory, enabling self-referential structures. This is crucial for async/await implementation in Rust.

**When to Use**: Rarely. Only for advanced scenarios like async state machines, intrusive data structures, or FFI.

---

## 9. Optimization Patterns

### 9.1 Cow (Clone on Write)

```rust
use std::borrow::Cow;

fn process_data(input: &str) -> Cow<str> {
    if input.contains("bad") {
        // Need to modify: allocate new String
        Cow::Owned(input.replace("bad", "good"))
    } else {
        // No modification: borrow original
        Cow::Borrowed(input)
    }
}

fn main() {
    let s1 = "hello world";
    let s2 = "bad input";
    
    let r1 = process_data(s1);  // No allocation
    let r2 = process_data(s2);  // Allocates
    
    println!("{}, {}", r1, r2);
}
```

**Performance Principle**: Defer allocation until necessary. `Cow` is perfect for functions that sometimes need to modify data and sometimes don't.

### 9.2 Small String Optimization Pattern

```rust
enum SmallString {
    Inline([u8; 23], u8),  // 23 bytes + 1 length byte = 24 bytes
    Heap(String),          // 24 bytes (pointer + len + cap)
}

impl SmallString {
    fn new(s: &str) -> Self {
        if s.len() <= 23 {
            let mut arr = [0u8; 23];
            arr[..s.len()].copy_from_slice(s.as_bytes());
            SmallString::Inline(arr, s.len() as u8)
        } else {
            SmallString::Heap(String::from(s))
        }
    }
    
    fn as_str(&self) -> &str {
        match self {
            SmallString::Inline(arr, len) => {
                std::str::from_utf8(&arr[..*len as usize]).unwrap()
            }
            SmallString::Heap(s) => s.as_str(),
        }
    }
}
```

**Insight**: Many strings in real programs are short. Avoid heap allocation for small strings by storing them inline. This is what `SmallVec` and similar crates do.

---

## 10. Mental Models for Mastery

### 10.1 The Ownership Tree

```
Program
├── Stack Frame
│   ├── Owned Value (root of ownership tree)
│   │   ├── Field 1 (owned)
│   │   └── Field 2 (owned)
│   └── Reference (borrow from tree)
└── Heap
    └── Allocated Data (owned by Box/Rc/Arc)
```

Every piece of data has **exactly one owner** at the root. References are temporary permissions to access that data.

### 10.2 The Three Questions

When designing a struct, ask:

1. **Who owns the data?** (This struct, caller, shared?)
2. **How long does it live?** (Lifetime `'a`, `'static`, owned?)
3. **Can it change?** (Immutable, `&mut`, `RefCell`?)

These three questions determine your ownership strategy.

### 10.3 Cognitive Chunking Strategy

**Beginner Level**: Think in terms of "owned vs borrowed"

**Intermediate Level**: Think in patterns (builder, RAII, smart pointers)

**Advanced Level**: Think in invariants (what guarantees does my ownership model provide?)

---

## 11. Comparison with Go and C

### Rust vs Go

```rust
// Rust: Explicit ownership
struct Data {
    values: Vec<i32>,  // Owned
}

fn process(d: Data) {  // Takes ownership
    // d is moved here
}
```

```go
// Go: Garbage collected, implicit sharing
type Data struct {
    values []int
}

func process(d Data) {  // Copies struct (shallow), but slice is shared
    // d.values points to same underlying array
}
```

**Key Difference**: Go's GC means you don't think about ownership. Rust forces explicit decisions, giving you control over allocation and lifetime.

### Rust vs C

```c
// C: Manual memory management
struct Data {
    int* values;
    size_t len;
};

void process(struct Data* d) {
    // Who frees d->values? Unclear.
    // When does d become invalid? Unclear.
}
```

```rust
// Rust: Ownership makes responsibility clear
struct Data {
    values: Vec<i32>,
}

fn process(d: Data) {
    // d owns values
    // When d goes out of scope, values is freed
    // Compiler prevents use-after-free
}
```

**Key Difference**: C gives you full control but no safety. Rust gives you control *and* safety through ownership.

---

## 12. Practice Challenges (Ranked by Difficulty)

### Level 1: Implement a Stack with Owned Data
```rust
struct Stack<T> {
    items: Vec<T>,
}

// Implement: push, pop, peek, len
// Constraints: No cloning, optimal memory usage
```

### Level 2: Implement a Binary Tree with Rc
```rust
use std::rc::Rc;

enum Tree<T> {
    Leaf,
    Node(Rc<Tree<T>>, T, Rc<Tree<T>>),
}

// Implement: insert, contains, depth
// Challenge: Handle shared subtrees
```

### Level 3: Implement a Graph with Arena Allocation
```rust
struct Arena<T> {
    nodes: Vec<T>,
}

struct GraphNode<'a> {
    value: i32,
    neighbors: Vec<&'a GraphNode<'a>>,
}

// Challenge: All nodes in one Vec, use indices instead of pointers
// This avoids Rc and is more cache-friendly
```

### Level 4: Implement LRU Cache with Rc<RefCell<>>
```rust
// Doubly-linked list + HashMap
// Requirements:
// - O(1) get and put
// - Shared ownership of nodes
// - Interior mutability for reordering
```

---

## Final Wisdom

**Ownership is not a constraint—it's a design tool.** Every ownership decision you make defines:
- Performance characteristics (stack vs heap, cache locality)
- API ergonomics (move vs borrow)
- Safety guarantees (no use-after-free, no data races)

The master doesn't fight the borrow checker; the master designs structures that align with Rust's ownership model.

**Your next step**: Implement each pattern above from scratch. Not just reading—building. That's where ownership becomes intuition.

The path to the top 1% is paved with ownership mistakes, borrow checker battles, and lifetimes that don't compile. Embrace them. Each error is a teacher.

Now go build something that owns its data perfectly.