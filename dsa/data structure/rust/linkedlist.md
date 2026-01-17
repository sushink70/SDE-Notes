# Building a Linked List in Rust: A Deep Dive

I'll teach you how to build a linked list in Rust from scratch, explaining every decision, keyword, and concept along the way.

## Step 1: Understanding What We're Building

A linked list is a collection of nodes where each node contains:
- Data (the value we're storing)
- A pointer/reference to the next node

Let's start coding and I'll explain every single line.

## Step 2: Creating the Basic Structure

```rust
// This is a generic type parameter declaration
// T means "Type" - any type the user wants to store
pub struct LinkedList<T> {
    head: Option<Box<Node<T>>>,
    length: usize,
}
```

**Let me break this down:**

### `pub` keyword
- **What**: Visibility modifier
- **Why**: Makes the struct public so code outside this module can use it
- **Alternative**: Without `pub`, it's private (only accessible in the same module)

### `struct` keyword
- **What**: Defines a custom data type
- **Why**: We need to group related data together
- **How Rust differs**: Structs don't have inheritance like OOP languages

### `<T>` - Generic Type Parameter
- **What**: A placeholder for any type
- **Why**: So our list can store `i32`, `String`, custom types, anything!
- **Example**: `LinkedList<i32>` or `LinkedList<String>`
- **Constraint**: We could add `<T: Clone>` if we need T to be cloneable

### `Option<Box<Node<T>>>`
Let me unpack this complex type:

**`Option<T>`**
- **What**: An enum from Rust's standard library
- **Why**: Represents a value that might exist (`Some(value)`) or not exist (`None`)
- **Usage**: Instead of null pointers (which cause crashes), Rust uses Option
- **Definition**:
  ```rust
  enum Option<T> {
      Some(T),
      None,
  }
  ```

**`Box<T>`**
- **What**: A smart pointer that allocates data on the heap
- **Why**: Rust needs to know the size of types at compile time. Without Box, our Node would contain another Node, which contains another Node... infinite size!
- **How it works**: Box stores a pointer (fixed size) on the stack, actual data goes on heap
- **Memory**: When Box goes out of scope, it automatically deallocates the heap memory

**Why `Box` inside `Option`?**
- `None` = no next node (end of list)
- `Some(Box<Node>)` = there is a next node, allocated on heap

### `usize` type
- **What**: Unsigned integer, size depends on architecture (32-bit or 64-bit)
- **Why**: Perfect for sizes, lengths, indices (never negative)
- **Alternative**: Could use `u32`, but `usize` is idiomatic for collection sizes

## Step 3: Creating the Node Structure

```rust
struct Node<T> {
    data: T,
    next: Option<Box<Node<T>>>,
}
```

**Why no `pub`?**
- Nodes are internal implementation details
- Users interact with LinkedList, not Nodes directly
- This is **encapsulation**

**Recursive structure:**
- `next` has the same type as the struct itself
- Only possible because of `Box` (indirection breaks infinite size problem)

## Step 4: Implementing Methods

```rust
impl<T> LinkedList<T> {
    // ... methods go here
}
```

### `impl` keyword
- **What**: Implementation block - where we define methods
- **Why**: Separates data (struct) from behavior (methods)
- **Pattern**: Can have multiple `impl` blocks for the same struct

### `<T>` after impl
- **What**: Tells Rust this implementation is for the generic version
- **Why**: Methods can use the generic type T
- **Constraint example**: `impl<T: Display> LinkedList<T>` would only work for types that can be displayed

## Step 5: Constructor Method

```rust
pub fn new() -> Self {
    LinkedList {
        head: None,
        length: 0,
    }
}
```

### `pub fn`
- **pub**: Public function, callable from outside
- **fn**: Function keyword

### `new()` convention
- **What**: Rust convention (not enforced) for constructors
- **Why**: Familiar pattern across Rust code
- **Alternative**: Could name it anything, but `new` is idiomatic

### `-> Self`
- **Self**: Type alias for `LinkedList<T>` (the type we're implementing)
- **Why Self**: Less typing, works even if we rename the struct
- **Return**: `->` indicates return type

### Struct initialization syntax
```rust
LinkedList {
    head: None,
    length: 0,
}
```
- **Pattern**: `field: value`
- **No `new` keyword**: Unlike other languages, just use struct name
- **Implicit return**: Last expression without `;` is returned

## Step 6: Push Front Method

```rust
pub fn push_front(&mut self, data: T) {
    let new_node = Box::new(Node {
        data: data,
        next: self.head.take(),
    });
    
    self.head = Some(new_node);
    self.length += 1;
}
```

### `&mut self`
- **What**: Mutable reference to self
- **Why**: We need to modify the list
- **Borrowing rules**: Only one mutable reference at a time
- **Alternatives**:
  - `&self`: Immutable reference (read-only)
  - `self`: Takes ownership (consumes the value)
  - `&mut self`: Mutable reference (can modify)

### `Box::new()`
- **What**: Associated function (like static method)
- **Syntax**: `Type::function()`
- **Why**: Creates a Box, allocating on heap

### `self.head.take()`
- **What**: Method on Option that takes the value out, leaving `None`
- **Why**: We need to move the old head into the new node's `next`
- **Before**: `self.head` is `Some(old_node)` or `None`
- **After**: `self.head` is `None`, and we get ownership of the old value
- **Signature**: `fn take(&mut self) -> Option<T>`

**Why not just assign?**
```rust
// This won't work:
next: self.head  // Error! Can't move out of borrowed content
```
We have `&mut self`, so we borrowed the LinkedList. Rust won't let us move `head` out because that would leave the struct in an invalid state. `take()` solves this by replacing with `None`.

### Field initialization shorthand
If you have a variable with the same name as the field:
```rust
let data = 5;
Node { data }  // Same as: Node { data: data }
```

## Step 7: Pop Front Method

```rust
pub fn pop_front(&mut self) -> Option<T> {
    self.head.take().map(|node| {
        self.head = node.next;
        self.length -= 1;
        node.data
    })
}
```

### Return type `Option<T>`
- **Why**: List might be empty (return `None`)
- **Pattern**: Rust loves using Option instead of exceptions

### `.map()` method
- **What**: Method on Option that transforms Some values
- **Signature**: `fn map<U, F>(self, f: F) -> Option<U> where F: FnOnce(T) -> U`
- **How it works**:
  - If `None`: returns `None`
  - If `Some(value)`: runs closure on value, returns `Some(result)`

### `|node| { ... }` - Closure syntax
- **What**: Anonymous function
- **Syntax**: `|params| body`
- **Type inference**: Rust figures out `node` is `Box<Node<T>>`
- **Alternatives**:
  - `|node| expression` - single expression
  - `|node| { statements; expression }` - multiple statements

### Why `map` instead of `match`?

**Using map** (functional style):
```rust
self.head.take().map(|node| {
    self.head = node.next;
    self.length -= 1;
    node.data
})
```

**Using match** (explicit style):
```rust
match self.head.take() {
    Some(node) => {
        self.head = node.next;
        self.length -= 1;
        Some(node.data)
    }
    None => None,
}
```

Both work! `map` is more concise when you want to transform Some and pass through None.

## Step 8: Implementing Display Trait

```rust
use std::fmt;

impl<T: fmt::Display> LinkedList<T> {
    pub fn display(&self) {
        let mut current = &self.head;
        print!("[");
        
        while let Some(node) = current {
            print!("{}", node.data);
            current = &node.next;
            if current.is_some() {
                print!(" -> ");
            }
        }
        
        println!("]");
    }
}
```

### `use std::fmt`
- **What**: Import statement
- **Why**: Brings `fmt` module into scope
- **std**: Standard library
- **Alternative**: Could write `std::fmt::Display` everywhere

### `impl<T: fmt::Display>`
- **What**: Trait bound
- **Why**: This implementation only works if T implements Display
- **Meaning**: `T` must be printable
- **Effect**: Can't call `display()` on `LinkedList<MyStruct>` unless MyStruct implements Display

### `&self.head`
- **What**: Reference to the head field
- **Type**: `&Option<Box<Node<T>>>`
- **Why reference**: We don't want to move/take the value

### `while let` pattern
- **What**: Pattern matching in a loop
- **Syntax**: `while let PATTERN = EXPRESSION { ... }`
- **How**: Runs while the pattern matches
- **Stops**: When pattern doesn't match (when we hit None)

**Breaking it down:**
```rust
while let Some(node) = current {
    // node is &Box<Node<T>> here
}
```

- **Iteration 1**: `current` is `&Some(first_node)`, pattern matches, `node` is `&first_node`
- **Iteration 2**: `current` is `&Some(second_node)`, pattern matches, `node` is `&second_node`
- **End**: `current` is `&None`, pattern fails, loop exits

### `print!` and `println!` macros
- **What**: Macros (not functions)
- **Syntax**: `!` indicates macro
- **Difference**: `println!` adds newline, `print!` doesn't
- **Why macros**: Variable number of arguments, compile-time formatting checks

### `is_some()` method
- **What**: Returns true if Option is Some
- **Alternative**: `is_none()` returns true if None
- **Usage**: Checking without unwrapping the value

## Step 9: Complete Implementation

```rust
use std::fmt;

// Generic linked list structure
// T is a type parameter - can be any type
pub struct LinkedList<T> {
    head: Option<Box<Node<T>>>,  // First node (or None if empty)
    length: usize,                // Number of elements
}

// Node is private - users don't interact with it directly
struct Node<T> {
    data: T,                      // The actual value stored
    next: Option<Box<Node<T>>>,   // Pointer to next node
}

// Core implementation - works for any type T
impl<T> LinkedList<T> {
    // Constructor - creates an empty list
    pub fn new() -> Self {
        LinkedList {
            head: None,
            length: 0,
        }
    }

    // Add element to the front - O(1) time complexity
    pub fn push_front(&mut self, data: T) {
        let new_node = Box::new(Node {
            data,
            next: self.head.take(),  // Take old head, leaving None
        });
        
        self.head = Some(new_node);
        self.length += 1;
    }

    // Remove and return front element - O(1) time complexity
    pub fn pop_front(&mut self) -> Option<T> {
        self.head.take().map(|node| {
            self.head = node.next;   // Second node becomes head
            self.length -= 1;
            node.data                // Return the data
        })
    }

    // Add element to the back - O(n) time complexity
    pub fn push_back(&mut self, data: T) {
        let new_node = Box::new(Node {
            data,
            next: None,
        });

        match self.head.as_mut() {
            None => {
                // Empty list - new node becomes head
                self.head = Some(new_node);
            }
            Some(mut current) => {
                // Traverse to the end
                while let Some(ref mut next_node) = current.next {
                    current = next_node;
                }
                current.next = Some(new_node);
            }
        }
        self.length += 1;
    }

    // Get the length of the list - O(1)
    pub fn len(&self) -> usize {
        self.length
    }

    // Check if list is empty - O(1)
    pub fn is_empty(&self) -> bool {
        self.length == 0
    }

    // Peek at the front element without removing - O(1)
    pub fn peek_front(&self) -> Option<&T> {
        self.head.as_ref().map(|node| &node.data)
    }

    // Clear the entire list - O(1)
    // Box's Drop trait handles recursive deallocation
    pub fn clear(&mut self) {
        self.head = None;
        self.length = 0;
    }
}

// Specialized implementation - only for types that can be displayed
impl<T: fmt::Display> LinkedList<T> {
    pub fn display(&self) {
        let mut current = &self.head;
        print!("[");
        
        while let Some(node) = current {
            print!("{}", node.data);
            current = &node.next;
            if current.is_some() {
                print!(" -> ");
            }
        }
        
        println!("]");
    }
}

// Iterator implementation - allows using for loops
pub struct LinkedListIterator<'a, T> {
    current: Option<&'a Box<Node<T>>>,
}

impl<'a, T> Iterator for LinkedListIterator<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        self.current.map(|node| {
            self.current = node.next.as_ref();
            &node.data
        })
    }
}

impl<T> LinkedList<T> {
    pub fn iter(&self) -> LinkedListIterator<T> {
        LinkedListIterator {
            current: self.head.as_ref(),
        }
    }
}

// Implementing Drop to show custom cleanup (optional - Box already handles this)
impl<T> Drop for LinkedList<T> {
    fn drop(&mut self) {
        let mut current = self.head.take();
        while let Some(mut node) = current {
            current = node.next.take();
            // node is dropped here
        }
    }
}

// Example usage
fn main() {
    // Create a list of integers
    let mut list = LinkedList::new();
    
    println!("=== Testing LinkedList ===\n");
    
    // Push elements
    list.push_front(3);
    list.push_front(2);
    list.push_front(1);
    println!("After pushing 1, 2, 3 to front:");
    list.display();
    println!("Length: {}\n", list.len());
    
    // Push to back
    list.push_back(4);
    list.push_back(5);
    println!("After pushing 4, 5 to back:");
    list.display();
    println!("Length: {}\n", list.len());
    
    // Peek
    if let Some(front) = list.peek_front() {
        println!("Front element: {}\n", front);
    }
    
    // Pop
    if let Some(value) = list.pop_front() {
        println!("Popped: {}", value);
        println!("After pop:");
        list.display();
        println!();
    }
    
    // Iterate
    println!("Iterating through list:");
    for (i, value) in list.iter().enumerate() {
        println!("  Element {}: {}", i, value);
    }
    println!();
    
    // Create a list of strings
    let mut str_list = LinkedList::new();
    str_list.push_front("World".to_string());
    str_list.push_front("Hello".to_string());
    println!("String list:");
    str_list.display();
    
    // Clear
    list.clear();
    println!("\nAfter clear:");
    list.display();
    println!("Is empty: {}", list.is_empty());
}
```

## Additional Concepts Explained

### 1. **Ownership System**

Rust's most unique feature:

```rust
let x = Box::new(5);  // x owns the Box
let y = x;            // Ownership moves to y
// println!("{}", x); // ERROR! x no longer owns the value
```

**Rules:**
1. Each value has exactly one owner
2. When owner goes out of scope, value is dropped
3. You can borrow (reference) but not own multiple times

### 2. **Borrowing & References**

```rust
&T      // Immutable reference (can have many)
&mut T  // Mutable reference (can have only one)
```

**Example:**
```rust
fn print_list(list: &LinkedList<i32>) {  // Borrows, doesn't take ownership
    list.display();
}  // list reference ends, but original owner still has it
```

### 3. **Lifetimes** (in Iterator)

```rust
pub struct LinkedListIterator<'a, T> {
    current: Option<&'a Box<Node<T>>>,
}
```

- **`'a`**: Lifetime parameter
- **Meaning**: "The reference is valid for lifetime 'a"
- **Why**: Tells Rust the iterator can't outlive the list it's iterating
- **Borrow checker**: Ensures no use-after-free bugs

### 4. **Traits**

Think of traits as interfaces:

```rust
impl<T> Iterator for LinkedListIterator<T>
```

- **Iterator**: A trait from std library
- **type Item**: Associated type - what the iterator produces
- **fn next()**: Required method

### 5. **Pattern Matching**

Rust's powerful matching:

```rust
match self.head {
    Some(node) => { /* handle node */ },
    None => { /* handle empty */ },
}
```

**Variants:**
- `if let`: Match one pattern
- `while let`: Loop while pattern matches
- `match`: Exhaustive matching (must cover all cases)

### 6. **Smart Pointers**

Rust has several:

- **Box<T>**: Heap allocation, single owner
- **Rc<T>**: Reference counted, multiple owners, immutable
- **Arc<T>**: Atomic Rc, thread-safe
- **RefCell<T>**: Interior mutability, runtime borrow checking

For linked list, `Box` is perfect because each node has one owner.

### 7. **The Drop Trait**

```rust
impl<T> Drop for LinkedList<T> {
    fn drop(&mut self) { /* cleanup */ }
}
```

- **What**: Called automatically when value goes out of scope
- **Why**: Custom cleanup (like destructors in C++)
- **Box**: Already implements Drop, so our implementation is optional

### 8. **Type Inference**

Rust is smart about types:

```rust
let mut list = LinkedList::new();  // Type unknown
list.push_front(5);                // Now Rust knows: LinkedList<i32>
```

### 9. **Memory Layout**

```
Stack:                          Heap:
LinkedList                      Node { data: 1, next: Box }
├─ head: Some(Box) ─────────────> │
├─ length: 3                      ├─ data: 1
                                  └─ next: Some(Box) ───> Node { data: 2, ... }
```

### 10. **Common Rust Conventions**

- `new()`: Constructor
- `len()`: Get length
- `is_empty()`: Check if empty
- `iter()`: Get iterator
- `_front`, `_back`: Indicate position
- Snake_case for functions/variables
- PascalCase for types

## Why Each Choice?

**Why Option instead of null?**
- Compile-time null safety
- Forces you to handle the "no value" case

**Why Box instead of raw pointers?**
- Automatic memory management
- No manual malloc/free
- No memory leaks

**Why separate impl blocks?**
- Trait bounds (T: Display) only apply where needed
- Better organization

**Why usize for length?**
- Idiomatic for collection sizes
- Matches array indexing type

## Common Pitfalls for Beginners

1. **Forgetting `&mut self`**: If you need to modify, use `&mut`
2. **Moving when you meant to borrow**: Use `&` or `.as_ref()`
3. **Fighting the borrow checker**: Usually means your design needs rethinking
4. **Not using take()**: When you need to move out of borrowed content

This is a complete, production-quality linked list implementation. You've learned structs, enums, generics, traits, ownership, borrowing, lifetimes, pattern matching, and more!