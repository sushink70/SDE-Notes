# Building a Tree Data Structure in Rust: A Complete Guide

I'll teach you how to build a tree from scratch, explaining every decision and keyword along the way.

## Step 1: Understanding What We're Building

A tree is a hierarchical data structure where each **node** contains:
- Some data (like a number or string)
- References to child nodes

Let's build a **binary tree** (each node has at most 2 children).

## Step 2: Choosing Types and Ownership Strategy

**First decision: How to represent node references?**

In Rust, we have several options:
- `Box<T>` - owned pointer (heap allocation)
- `Rc<T>` - reference counted (shared ownership)
- `&T` - borrowed reference (requires lifetimes)

**I choose `Box<T>` because:**
- Each node owns its children (clear ownership)
- Simple memory management
- No runtime overhead of reference counting

**Second decision: How to represent "no child"?**

Use `Option<Box<Node>>` because:
- `Some(box)` = child exists
- `None` = no child
- This is Rust's idiomatic way to represent "nullable" values

## Step 3: Defining the Node Structure

```rust
// The `struct` keyword defines a new type
// We use generic type `T` so our tree can hold any data type
struct Node<T> {
    // Each field needs a name and type
    value: T,  // The data this node holds
    
    // Option<Box<Node<T>>> means:
    // - Option = might be Some or None
    // - Box = heap-allocated pointer
    // - Node<T> = another node of the same type
    left: Option<Box<Node<T>>>,
    right: Option<Box<Node<T>>>,
}
```

**Why `<T>` (generics)?**
- Makes our tree work with any type: numbers, strings, custom types
- Rust will generate specialized code for each type we use
- Alternative would be to hardcode like `value: i32`, but that's inflexible

## Step 4: Implementing Methods

The `impl` keyword lets us add methods to our struct:

```rust
// impl<T> means "implementation for any type T"
impl<T> Node<T> {
    // `fn` declares a function
    // `new` is a convention for constructors (not a keyword)
    // `Self` is an alias for `Node<T>` (the type we're implementing for)
    fn new(value: T) -> Self {
        // We return a Node with the value and no children
        Node {
            value,  // Shorthand for `value: value`
            left: None,   // No left child initially
            right: None,  // No right child initially
        }
    }
    
    // Methods that take `&mut self` can modify the node
    // `&mut` = mutable reference (we can change the node)
    fn insert_left(&mut self, value: T) {
        // Box::new() allocates on the heap
        // We wrap it in Some() to make it an Option
        self.left = Some(Box::new(Node::new(value)));
    }
    
    fn insert_right(&mut self, value: T) {
        self.right = Some(Box::new(Node::new(value)));
    }
}
```

**Key concepts:**
- `self` = the instance being called on
- `&self` = immutable borrow (read-only)
- `&mut self` = mutable borrow (can modify)
- `Self` = the type itself (capitalized)

## Step 5: Creating a Tree Wrapper

Let's make a wrapper to represent the whole tree:

```rust
struct BinaryTree<T> {
    root: Option<Box<Node<T>>>,
}

impl<T> BinaryTree<T> {
    // Creates an empty tree
    fn new() -> Self {
        BinaryTree { root: None }
    }
    
    // Sets the root node
    fn set_root(&mut self, value: T) {
        self.root = Some(Box::new(Node::new(value)));
    }
    
    // Returns a reference to the root (if it exists)
    // The `&` before Option means we're returning a reference
    // We use `as_ref()` to convert from `Option<Box<T>>` to `Option<&Box<T>>`
    fn get_root(&self) -> Option<&Box<Node<T>>> {
        self.root.as_ref()
    }
    
    // Returns a mutable reference to the root
    fn get_root_mut(&mut self) -> Option<&mut Box<Node<T>>> {
        self.root.as_mut()
    }
}
```

## Step 6: Traversal - Using Recursion

Let's add tree traversal (visiting all nodes):

```rust
impl<T> Node<T> {
    // In-order traversal: left -> root -> right
    // Where clause `T: std::fmt::Display` means T must be printable
    fn inorder(&self) 
    where 
        T: std::fmt::Display  // Trait bound: T must implement Display
    {
        // If left child exists, traverse it
        // `if let` is pattern matching - extracts value if Some
        if let Some(left_node) = &self.left {
            left_node.inorder();  // Recursive call
        }
        
        // Print this node's value
        println!("{}", self.value);
        
        // Traverse right child
        if let Some(right_node) = &self.right {
            right_node.inorder();
        }
    }
}
```

**Why `where T: std::fmt::Display`?**
- We use `println!` which needs to know how to display `T`
- This is a **trait bound** - a requirement on the generic type
- Only types that implement `Display` can be used with this method

## Step 7: Advanced Features - Finding Nodes

```rust
// We add `PartialEq` trait bound so we can compare values with `==`
impl<T: PartialEq> Node<T> {
    // Returns true if value exists in tree
    // `&T` means we borrow the value (don't take ownership)
    fn contains(&self, target: &T) -> bool {
        // Check if this node matches
        if &self.value == target {
            return true;
        }
        
        // Check left subtree using match expression
        // `match` is like switch but more powerful
        let left_contains = match &self.left {
            Some(node) => node.contains(target),  // Recurse if exists
            None => false,  // No node = can't contain target
        };
        
        // Short-circuit: if found in left, return true
        if left_contains {
            return true;
        }
        
        // Check right subtree
        match &self.right {
            Some(node) => node.contains(target),
            None => false,
        }
    }
}
```

## Complete Working Example

```rust
// Define the Node structure
// <T> makes it generic - works with any type
struct Node<T> {
    value: T,                      // The data stored in this node
    left: Option<Box<Node<T>>>,    // Left child (optional)
    right: Option<Box<Node<T>>>,   // Right child (optional)
}

// Implementation block for Node
impl<T> Node<T> {
    // Constructor - creates a new node with no children
    fn new(value: T) -> Self {
        Node {
            value,
            left: None,
            right: None,
        }
    }
    
    // Add a left child
    fn insert_left(&mut self, value: T) {
        self.left = Some(Box::new(Node::new(value)));
    }
    
    // Add a right child
    fn insert_right(&mut self, value: T) {
        self.right = Some(Box::new(Node::new(value)));
    }
    
    // Get mutable reference to left child if it exists
    fn left_mut(&mut self) -> Option<&mut Box<Node<T>>> {
        self.left.as_mut()
    }
    
    // Get mutable reference to right child if it exists
    fn right_mut(&mut self) -> Option<&mut Box<Node<T>>> {
        self.right.as_mut()
    }
}

// Additional methods that require T to be displayable
impl<T: std::fmt::Display> Node<T> {
    // In-order traversal: left -> root -> right
    fn inorder(&self) {
        if let Some(left) = &self.left {
            left.inorder();
        }
        println!("{}", self.value);
        if let Some(right) = &self.right {
            right.inorder();
        }
    }
    
    // Pre-order traversal: root -> left -> right
    fn preorder(&self) {
        println!("{}", self.value);
        if let Some(left) = &self.left {
            left.preorder();
        }
        if let Some(right) = &self.right {
            right.preorder();
        }
    }
    
    // Post-order traversal: left -> right -> root
    fn postorder(&self) {
        if let Some(left) = &self.left {
            left.postorder();
        }
        if let Some(right) = &self.right {
            right.postorder();
        }
        println!("{}", self.value);
    }
}

// Methods that require T to be comparable
impl<T: PartialEq> Node<T> {
    // Check if value exists in tree
    fn contains(&self, target: &T) -> bool {
        if &self.value == target {
            return true;
        }
        
        let left_contains = match &self.left {
            Some(node) => node.contains(target),
            None => false,
        };
        
        if left_contains {
            return true;
        }
        
        match &self.right {
            Some(node) => node.contains(target),
            None => false,
        }
    }
}

// Tree wrapper structure
struct BinaryTree<T> {
    root: Option<Box<Node<T>>>,
}

impl<T> BinaryTree<T> {
    // Create an empty tree
    fn new() -> Self {
        BinaryTree { root: None }
    }
    
    // Set the root node
    fn set_root(&mut self, value: T) {
        self.root = Some(Box::new(Node::new(value)));
    }
    
    // Get mutable reference to root
    fn root_mut(&mut self) -> Option<&mut Box<Node<T>>> {
        self.root.as_mut()
    }
    
    // Check if tree is empty
    fn is_empty(&self) -> bool {
        self.root.is_none()
    }
}

// Traversal methods for BinaryTree
impl<T: std::fmt::Display> BinaryTree<T> {
    fn inorder(&self) {
        if let Some(root) = &self.root {
            root.inorder();
        }
    }
    
    fn preorder(&self) {
        if let Some(root) = &self.root {
            root.preorder();
        }
    }
    
    fn postorder(&self) {
        if let Some(root) = &self.root {
            root.postorder();
        }
    }
}

// Search method for BinaryTree
impl<T: PartialEq> BinaryTree<T> {
    fn contains(&self, target: &T) -> bool {
        match &self.root {
            Some(root) => root.contains(target),
            None => false,
        }
    }
}

// Example usage
fn main() {
    // Create a new tree
    let mut tree = BinaryTree::new();
    
    // Build tree structure:
    //       1
    //      / \
    //     2   3
    //    / \
    //   4   5
    
    tree.set_root(1);
    
    // Get root and add children
    if let Some(root) = tree.root_mut() {
        root.insert_left(2);
        root.insert_right(3);
        
        // Add children to node 2
        if let Some(left) = root.left_mut() {
            left.insert_left(4);
            left.insert_right(5);
        }
    }
    
    println!("In-order traversal:");
    tree.inorder();
    
    println!("\nPre-order traversal:");
    tree.preorder();
    
    println!("\nPost-order traversal:");
    tree.postorder();
    
    println!("\nSearching for values:");
    println!("Contains 3? {}", tree.contains(&3));
    println!("Contains 7? {}", tree.contains(&7));
}
```

## Key Rust Concepts Explained

### 1. **Ownership & Borrowing**
- **Owned** (`T`): The value belongs to you, you can move/consume it
- **Borrowed** (`&T`): You can read it, but don't own it
- **Mutable borrow** (`&mut T`): You can modify it temporarily

### 2. **Pattern Matching**
```rust
// if let - extracts value if pattern matches
if let Some(x) = option_value {
    // x is available here
}

// match - handles all cases
match option_value {
    Some(x) => { /* use x */ },
    None => { /* handle empty */ },
}
```

### 3. **Generic Types (`<T>`)**
Makes code reusable for different types. The compiler generates specialized versions for each type you use.

### 4. **Trait Bounds**
```rust
fn print<T: Display>(val: T)  // T must implement Display
where T: Display + Clone      // Can require multiple traits
```

### 5. **Smart Pointers**
- `Box<T>` - heap allocation, single owner
- `Rc<T>` - reference counted (multiple owners)
- `RefCell<T>` - runtime borrow checking

### 6. **Common Patterns**
- `new()` - constructor by convention
- `as_ref()` - converts `&Option<T>` to `Option<&T>`
- `as_mut()` - mutable version of `as_ref()`
- `is_none()`, `is_some()` - check Option state

## Why These Choices?

1. **`Box` instead of `Rc`**: Simpler, faster, clear ownership
2. **`Option` for children**: Rust has no null, Option is safe
3. **Generics `<T>`**: Maximum flexibility without runtime cost
4. **Trait bounds**: Ensures type safety at compile time
5. **Separate `impl` blocks**: Organize methods by their requirements

The code I provided is fully working - you can run it with `cargo run` and see tree traversals in action!