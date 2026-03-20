# The Complete Guide: Stack & Heap — Memory and Data Structures

> *"To understand the machine is to understand the mind of computation itself."*

---

## Table of Contents

1. [Mental Model First: What IS Memory?](#1-mental-model-first-what-is-memory)
2. [Stack Memory — The Call Stack](#2-stack-memory--the-call-stack)
3. [Heap Memory — Dynamic Allocation](#3-heap-memory--dynamic-allocation)
4. [Stack Memory vs Heap Memory — Deep Comparison](#4-stack-memory-vs-heap-memory--deep-comparison)
5. [Stack Data Structure — Theory](#5-stack-data-structure--theory)
6. [Stack — Implementations (C, Rust, Go)](#6-stack--implementations-c-rust-go)
7. [Stack — Applications & Patterns](#7-stack--applications--patterns)
8. [Heap Data Structure — Theory](#8-heap-data-structure--theory)
9. [Heap — Implementations (C, Rust, Go)](#9-heap--implementations-c-rust-go)
10. [Heap Sort](#10-heap-sort)
11. [Priority Queue via Heap](#11-priority-queue-via-heap)
12. [Complexity Master Reference](#12-complexity-master-reference)
13. [Mental Models for Mastery](#13-mental-models-for-mastery)

---

## 1. Mental Model First: What IS Memory?

### What is RAM?

RAM (Random Access Memory) is a giant, flat array of **bytes**. Each byte has a unique **address** (a number). When your program runs, the operating system (OS) carves up this physical RAM into segments assigned to your process.

```
Physical RAM (simplified view)
+--------+--------+--------+--------+--------+--------+
| 0x0000 | 0x0001 | 0x0002 | 0x0003 | ......  | 0xFFFF |
+--------+--------+--------+--------+--------+--------+
   1 byte   1 byte   1 byte   1 byte           1 byte
```

Your running program (process) sees a **virtual address space** — a private, isolated view of memory that the OS maps to real physical RAM. This virtual address space is divided into **segments**:

```
Virtual Address Space of a Process
+-------------------------------+  High Address (e.g., 0xFFFFFFFF)
|         Kernel Space          |  (OS, not accessible by user code)
+-------------------------------+
|           Stack               |  Grows DOWNWARD  ↓
|             |                 |
|             v                 |
|                               |
|         (unused)              |
|                               |
|             ^                 |
|             |                 |
|           Heap                |  Grows UPWARD    ↑
+-------------------------------+
|     Uninitialized Data (BSS)  |  Global/static vars (zero-initialized)
+-------------------------------+
|     Initialized Data          |  Global/static vars (with values)
+-------------------------------+
|        Text / Code            |  Your compiled program instructions
+-------------------------------+  Low Address (e.g., 0x00000000)
```

**Key insight:** Stack and Heap are both regions in the SAME RAM — they differ in HOW they are managed.

---

## 2. Stack Memory — The Call Stack

### What is the Stack (Memory)?

The **call stack** is a region of memory that the CPU and OS automatically manage for you. It follows **LIFO** (Last In, First Out) order — the most recently allocated memory is the first to be freed.

Every time a function is called, a **stack frame** (also called an **activation record**) is pushed onto the stack. When the function returns, its frame is popped off.

### Anatomy of a Stack Frame

A **stack frame** contains:
- **Return address** — where execution should resume after this function ends
- **Parameters** — the arguments passed to the function
- **Local variables** — variables declared inside the function
- **Saved registers** — CPU register values to restore when this function returns

```
         Stack grows DOWNWARD in memory
         
High Address
+------------------------------+
|      main() stack frame      |
|  - return addr               |
|  - local var: x = 10         |
|  - local var: y = 20         |
+------------------------------+  <-- Stack Pointer was here before foo() called
|      foo() stack frame       |
|  - return addr (back to main)|
|  - param: a = 5              |
|  - local var: result = 0     |
+------------------------------+  <-- Stack Pointer (SP) now here
|      bar() stack frame       |
|  - return addr (back to foo) |
|  - local var: tmp = 99       |
+------------------------------+  <-- SP after bar() is called
|         (free stack)         |
|                              |
Low Address
```

### The Stack Pointer (SP)

The CPU has a special register called the **Stack Pointer (SP)**. It always points to the **top of the stack** (which is actually the lowest address, since stack grows down).

```
PUSH operation:  SP = SP - size_of_frame   (moves down)
POP  operation:  SP = SP + size_of_frame   (moves up)
```

This is O(1) — it's literally just arithmetic on a register. This is why stack allocation is **blazing fast**.

### Step-by-Step: What Happens During a Function Call

```
Step 1: Caller pushes arguments onto stack (or uses registers)
Step 2: CPU executes CALL instruction
         → Pushes return address onto stack
         → Jumps to function's code
Step 3: Function prologue:
         → Saves old base pointer (BP/FP)
         → Sets BP = SP (new frame base)
         → Reserves space for local vars: SP = SP - local_size
Step 4: Function executes
Step 5: Function epilogue:
         → SP = BP (restore to frame base)
         → Pop old BP
         → RET instruction: pops return address, jumps there
Step 6: Stack is back to exactly how it was before the call
```

### Stack in C — Concrete Example

```c
#include <stdio.h>

// Each function call creates a new stack frame
int add(int a, int b) {
    // 'a', 'b', 'result' all live on the STACK
    int result = a + b;     // stack allocated, auto-freed on return
    return result;
}

int main(void) {
    int x = 10;             // on stack
    int y = 20;             // on stack
    int z = add(x, y);      // on stack
    printf("z = %d\n", z);
    return 0;
    // x, y, z all freed automatically when main() exits
}
```

```
Stack state when add() is executing:

+------------------+
| main frame       |
|  x = 10          |
|  y = 20          |
|  z = ???         |  (not yet assigned)
|  return_addr     |
+------------------+
| add frame        |
|  a = 10          |  (copy of x)
|  b = 20          |  (copy of y)
|  result = 30     |
|  return_addr     |  (back to main)
+------------------+  <-- SP (top of stack right now)
```

### Stack in Rust — Stack vs Box

```rust
fn add(a: i32, b: i32) -> i32 {
    let result = a + b;  // 'result' is on the stack
    result               // copied back to caller's stack frame
}

fn main() {
    let x: i32 = 10;     // Stack allocated — 4 bytes on stack
    let y: i32 = 20;     // Stack allocated
    let z = add(x, y);   // z is stack allocated
    println!("z = {}", z);
    
    // Rust's ownership system knows EXACTLY when to free stack memory
    // No garbage collector needed for stack data
    // When a variable goes out of scope (}), it's dropped automatically
}
```

```rust
// Rust: stack vs heap comparison
fn stack_vs_heap() {
    // STACK: fixed size, lives in current frame
    let arr_stack: [i32; 5] = [1, 2, 3, 4, 5];  // 20 bytes on stack
    
    // HEAP: dynamic, lives until explicitly freed (or Box drops)
    let arr_heap: Box<[i32; 5]> = Box::new([1, 2, 3, 4, 5]);  // 20 bytes on HEAP
    //                  ^                                           pointer on stack
    //                  Box<T> = pointer to heap + ownership
    
    println!("Stack arr: {:?}", arr_stack);
    println!("Heap arr: {:?}", arr_heap);
    // arr_heap is automatically freed here (Box implements Drop)
}
```

### Stack in Go

```go
package main

import "fmt"

// Go's compiler uses "escape analysis" to decide:
// does this variable stay on the stack, or must it escape to the heap?

func add(a, b int) int {
    result := a + b  // local variable: stack
    return result    // value is copied back
}

func returnsPointer() *int {
    // This variable ESCAPES to heap because its address outlives the function
    x := 42
    return &x   // x must be on heap — Go moves it there via escape analysis
}

func main() {
    a := 10            // stack
    b := 20            // stack
    c := add(a, b)     // stack
    fmt.Println(c)
    
    ptr := returnsPointer()  // ptr is on stack, but *ptr is on heap
    fmt.Println(*ptr)        // safe: Go's GC keeps it alive
}
```

**Go Escape Analysis Insight:** Run `go build -gcflags="-m"` to see which variables escape to heap. This is crucial for performance-sensitive Go code.

### Stack Overflow — What Happens?

```
When stack exceeds its limit (usually 1MB - 8MB on most systems):

+------------------+
| frame 1          |
+------------------+
| frame 2          |
+------------------+
| frame 3          |
...
+------------------+
| frame N          |
+------------------+
| GUARD PAGE       |  <-- OS puts a protected page here
+==================+  STACK OVERFLOW! Segmentation fault / panic
| Other memory     |
```

**Common cause:** Infinite or very deep recursion.

```c
// This will crash with a stack overflow:
int infinite(int n) {
    return infinite(n + 1);  // never returns, keeps pushing frames
}
```

```rust
// Rust: same issue
fn infinite(n: u64) -> u64 {
    infinite(n + 1)  // thread 'main' has overflowed its stack
}
// Rust's default stack: 8MB per thread
```

---

## 3. Heap Memory — Dynamic Allocation

### What is the Heap (Memory)?

The **heap** is a large pool of memory used for **dynamic allocation** — allocating memory at runtime when you don't know the size at compile time, or when data needs to outlive the function that created it.

Unlike the stack (managed by CPU/OS automatically), heap memory is managed by:
- **C:** You manually (`malloc`, `free`)
- **Rust:** Ownership system + `Box`, `Vec`, `String`, etc.
- **Go:** Garbage Collector (GC)

```
Heap memory layout (conceptual)
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
| A | A | A | . | B | B | . | . | C | C | C | C | . | . |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  ^allocated  ^free  ^alloc  ^free    ^allocated         ^free
  
  A, B, C = different heap allocations
  . = free blocks
```

### malloc / free in C

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    // malloc: allocate n bytes on heap, returns void* pointer
    // returns NULL if allocation fails
    int *arr = (int *)malloc(5 * sizeof(int));
    
    if (arr == NULL) {
        fprintf(stderr, "malloc failed!\n");
        return 1;
    }
    
    // Fill the array
    for (int i = 0; i < 5; i++) {
        arr[i] = i * 10;
    }
    
    for (int i = 0; i < 5; i++) {
        printf("arr[%d] = %d\n", i, arr[i]);
    }
    
    // MUST free heap memory manually
    free(arr);
    arr = NULL;  // Best practice: null the pointer after freeing
    
    // calloc: allocate AND zero-initialize
    int *zeros = (int *)calloc(5, sizeof(int));
    // zeros[0..4] == 0
    free(zeros);
    
    // realloc: resize a heap allocation
    int *dynamic = (int *)malloc(3 * sizeof(int));
    dynamic[0] = 1; dynamic[1] = 2; dynamic[2] = 3;
    
    dynamic = (int *)realloc(dynamic, 6 * sizeof(int));  // expand to 6 ints
    dynamic[3] = 4; dynamic[4] = 5; dynamic[5] = 6;
    free(dynamic);
    
    return 0;
}
```

```
Memory picture after malloc(5 * sizeof(int)):

STACK:
+------------------+
| main frame       |
|  arr = 0x7f3c10  |  <-- pointer value (address of heap block)
+------------------+

HEAP:
Address 0x7f3c10:
+----+----+----+----+----+
| 0  | 10 | 20 | 30 | 40 |   (5 ints = 20 bytes)
+----+----+----+----+----+
```

### Heap in Rust — Ownership & Box<T>

```rust
fn main() {
    // Box<T>: allocates T on the heap, gives you ownership
    let boxed_int: Box<i32> = Box::new(42);
    println!("Boxed value: {}", *boxed_int);  // dereference to get the value
    // When boxed_int goes out of scope: heap memory freed automatically (no GC!)
    // Rust calls the Drop trait, which calls the allocator's free()
    
    // Vec<T>: dynamic array on the heap
    let mut v: Vec<i32> = Vec::new();
    v.push(1);
    v.push(2);
    v.push(3);
    // Vec internally: [pointer to heap | length | capacity]
    //                  stack (3 words)    heap (the actual data)
    
    // String: heap-allocated, growable string
    let mut s = String::from("hello");
    s.push_str(", world");
    // String internally: [pointer | length | capacity]  (same as Vec<u8>)
    
    println!("{}", s);
    // All freed when they go out of scope
}

// Rust's ownership rules PREVENT:
// 1. Use-after-free: can't use value after it's dropped
// 2. Double-free: ownership ensures only one owner can drop
// 3. Memory leaks (in safe code)
// 4. Data races (enforced at compile time)
```

### Heap in Go — GC Managed

```go
package main

import "fmt"

func createSlice() []int {
    // This slice ESCAPES to heap (returned to caller)
    s := make([]int, 5)   // heap allocation
    for i := range s {
        s[i] = i * 10
    }
    return s  // safe: GC keeps it alive as long as something references it
}

func main() {
    s := createSlice()
    fmt.Println(s)   // [0 10 20 30 40]
    
    // map: always on heap in Go
    m := make(map[string]int)
    m["one"] = 1
    m["two"] = 2
    fmt.Println(m)
    
    // When s and m go out of scope:
    // Go's GC will eventually free them (not immediately)
    // GC runs periodically (tricolor mark-and-sweep in Go)
}
```

### How the Heap Allocator Works (Simplified)

```
Memory Allocator (e.g., ptmalloc, jemalloc, tcmalloc) internals:

Free List concept:
+--------+     +--------+     +--------+
| Block  | --> | Block  | --> | Block  | --> NULL
| size:8 |     | size:16|     | size:32|
+--------+     +--------+     +--------+

When you call malloc(10):
1. Find a free block >= 10 bytes (first-fit or best-fit search)
2. Mark it as allocated
3. Return pointer to usable region
4. Time: O(1) amortized (with slab allocators) or O(log n)

When you call free(ptr):
1. Mark block as free
2. Coalesce adjacent free blocks (prevent fragmentation)
3. Return to free list

Heap fragmentation:
+----+----+----+----+----+----+----+----+
| A  | fr | B  | fr | C  | fr | fr | fr |
+----+----+----+----+----+----+----+----+
 (fr = freed blocks, but they're not contiguous)
 
Even though total free = 4 blocks, you can't allocate a 4-block chunk!
This is EXTERNAL FRAGMENTATION — a key heap challenge.
```

---

## 4. Stack Memory vs Heap Memory — Deep Comparison

```
+===========================+========================+========================+
|       PROPERTY            |   STACK MEMORY         |   HEAP MEMORY          |
+===========================+========================+========================+
| Management                | Automatic (CPU/OS)     | Manual / GC / Ownership|
+---------------------------+------------------------+------------------------+
| Allocation speed          | O(1) — just move SP    | O(1) amortized,        |
|                           |                        | slower due to bookkeep |
+---------------------------+------------------------+------------------------+
| Deallocation speed        | O(1) — just move SP    | O(1) amortized,        |
|                           |                        | GC adds latency        |
+---------------------------+------------------------+------------------------+
| Size limit                | Small (1–8 MB typical) | Large (GB range)       |
+---------------------------+------------------------+------------------------+
| Size at compile time?     | Must be known          | Not required           |
+---------------------------+------------------------+------------------------+
| Lifetime                  | Tied to scope/function | As long as referenced  |
+---------------------------+------------------------+------------------------+
| Cache performance         | Excellent (spatial     | Worse (fragmented,     |
|                           | locality, LIFO order)  | pointer chasing)       |
+---------------------------+------------------------+------------------------+
| Fragmentation             | None                   | Yes (external/internal)|
+---------------------------+------------------------+------------------------+
| Thread safety             | Each thread has own    | Shared — needs locks   |
|                           | stack (isolated)       | or atomics             |
+---------------------------+------------------------+------------------------+
| Errors possible           | Stack overflow         | Memory leak,           |
|                           |                        | use-after-free,        |
|                           |                        | double-free            |
+---------------------------+------------------------+------------------------+
| Language control          | Implicit               | Explicit (C), RAII     |
|                           |                        | (Rust), GC (Go)        |
+===========================+========================+========================+
```

### When to prefer each?

```
USE STACK WHEN:
  ✓ Size is known at compile time
  ✓ Data only needed within function scope
  ✓ Performance is critical (cache-hot, no allocator overhead)
  ✓ Data is small (arrays of fixed size, primitives, structs)

USE HEAP WHEN:
  ✓ Size is unknown at compile time (user input, dynamic collections)
  ✓ Data needs to outlive its creating function
  ✓ Data is large (can't fit on small stack)
  ✓ Data shared between multiple parts of program
  ✓ Building recursive or dynamic data structures (trees, linked lists)
```

---

## 5. Stack Data Structure — Theory

### What is the Stack (Data Structure)?

The **Stack** is an Abstract Data Type (ADT) that follows the **LIFO** principle:
- **L**ast **I**n, **F**irst **O**ut

Think of a stack of plates:
- You can only add (push) to the top
- You can only remove (pop) from the top

```
STACK VISUALIZATION:

Push 1, Push 2, Push 3:

  Step 1:    Step 2:    Step 3:
  +---+      +---+      +---+
  | 1 | TOP  | 2 | TOP  | 3 | TOP
  +---+      +---+      +---+
             | 1 |      | 2 |
             +---+      +---+
                        | 1 |
                        +---+

Pop twice from Step 3:

  After pop:  After pop:
  +---+       +---+
  | 2 | TOP   | 1 | TOP
  +---+       +---+
  | 1 |
  +---+
```

### Core Operations

| Operation | Description                          | Time Complexity |
|-----------|--------------------------------------|-----------------|
| `push(x)` | Add element x to the top            | O(1)            |
| `pop()`   | Remove & return top element          | O(1)            |
| `peek()`  | Look at top element (no remove)      | O(1)            |
| `isEmpty()`| Check if stack has no elements      | O(1)            |
| `size()`  | Number of elements                   | O(1)            |

### Decision Tree: Array-Based vs Linked-List-Based Stack

```
Which implementation to choose?

                    +----------------------------+
                    |  Do you know max size      |
                    |  of stack in advance?      |
                    +----------------------------+
                           /          \
                         YES           NO
                         /               \
          +------------------+     +--------------------+
          | Array-based stack|     | Linked-list stack  |
          | - Simpler        |     | - Dynamic size     |
          | - Cache-friendly |     | - Extra memory per |
          | - Fixed capacity |     |   node (pointer)   |
          | - Faster         |     | - Heap allocation  |
          +------------------+     +--------------------+
```

### Array-Based Stack — Internals

```
Array stack with capacity 5:

Initial:
+-----------+-----------+-----------+-----------+-----------+
|           |           |           |           |           |
+-----------+-----------+-----------+-----------+-----------+
  [0]          [1]          [2]          [3]          [4]
  
  top = -1 (empty)

After push(10), push(20), push(30):
+-----------+-----------+-----------+-----------+-----------+
|    10     |    20     |    30     |           |           |
+-----------+-----------+-----------+-----------+-----------+
  [0]          [1]          [2]          [3]          [4]
                               ^
                             top = 2

After pop() returns 30:
+-----------+-----------+-----------+-----------+-----------+
|    10     |    20     |           |           |           |
+-----------+-----------+-----------+-----------+-----------+
                  ^
                top = 1
```

### Linked-List-Based Stack — Internals

```
Each node: [data | next_ptr]

After push(10), push(20), push(30):

top
 |
 v
[30 | --->] [20 | --->] [10 | NULL]

After pop() returns 30:

top
 |
 v
[20 | --->] [10 | NULL]
```

---

## 6. Stack — Implementations (C, Rust, Go)

### 6.1 Stack in C — Array-Based

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define MAX_CAPACITY 1000

// Stack structure
typedef struct {
    int data[MAX_CAPACITY];
    int top;      // index of top element (-1 = empty)
    int capacity;
} Stack;

// Initialize stack
void stack_init(Stack *s) {
    s->top = -1;
    s->capacity = MAX_CAPACITY;
}

// Check if stack is empty
bool stack_is_empty(const Stack *s) {
    return s->top == -1;
}

// Check if stack is full
bool stack_is_full(const Stack *s) {
    return s->top == s->capacity - 1;
}

// Push element (returns false if full)
bool stack_push(Stack *s, int value) {
    if (stack_is_full(s)) {
        fprintf(stderr, "Stack overflow!\n");
        return false;
    }
    s->data[++(s->top)] = value;  // increment top, then assign
    return true;
}

// Pop element (returns false if empty)
bool stack_pop(Stack *s, int *out_value) {
    if (stack_is_empty(s)) {
        fprintf(stderr, "Stack underflow!\n");
        return false;
    }
    *out_value = s->data[(s->top)--];  // read top, then decrement
    return true;
}

// Peek at top element without removing
bool stack_peek(const Stack *s, int *out_value) {
    if (stack_is_empty(s)) {
        return false;
    }
    *out_value = s->data[s->top];
    return true;
}

// Return number of elements
int stack_size(const Stack *s) {
    return s->top + 1;
}

void stack_print(const Stack *s) {
    printf("Stack (top -> bottom): ");
    for (int i = s->top; i >= 0; i--) {
        printf("%d ", s->data[i]);
    }
    printf("\n");
}

int main(void) {
    Stack s;
    stack_init(&s);
    
    stack_push(&s, 10);
    stack_push(&s, 20);
    stack_push(&s, 30);
    stack_print(&s);  // Stack (top -> bottom): 30 20 10
    
    int val;
    stack_pop(&s, &val);
    printf("Popped: %d\n", val);  // Popped: 30
    stack_print(&s);              // Stack (top -> bottom): 20 10
    
    stack_peek(&s, &val);
    printf("Peek: %d\n", val);    // Peek: 20
    printf("Size: %d\n", stack_size(&s));  // Size: 2
    
    return 0;
}
```

### 6.2 Stack in C — Dynamic (Linked List Based)

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

// Node in the linked list
typedef struct Node {
    int data;
    struct Node *next;
} Node;

// Stack: just a pointer to the top node
typedef struct {
    Node *top;
    int size;
} LinkedStack;

void lstack_init(LinkedStack *s) {
    s->top = NULL;
    s->size = 0;
}

bool lstack_is_empty(const LinkedStack *s) {
    return s->top == NULL;
}

// Push: allocate new node, point to old top
bool lstack_push(LinkedStack *s, int value) {
    Node *new_node = (Node *)malloc(sizeof(Node));
    if (new_node == NULL) return false;
    
    new_node->data = value;
    new_node->next = s->top;  // new node points to old top
    s->top = new_node;         // update top to new node
    s->size++;
    return true;
}

// Pop: remove top node, return its value
bool lstack_pop(LinkedStack *s, int *out_value) {
    if (lstack_is_empty(s)) return false;
    
    Node *old_top = s->top;
    *out_value = old_top->data;
    s->top = old_top->next;  // top is now the previous node
    free(old_top);            // free the node
    s->size--;
    return true;
}

// Cleanup: free all nodes
void lstack_destroy(LinkedStack *s) {
    int dummy;
    while (!lstack_is_empty(s)) {
        lstack_pop(s, &dummy);
    }
}

int main(void) {
    LinkedStack s;
    lstack_init(&s);
    
    lstack_push(&s, 1);
    lstack_push(&s, 2);
    lstack_push(&s, 3);
    
    int val;
    while (!lstack_is_empty(&s)) {
        lstack_pop(&s, &val);
        printf("Popped: %d\n", val);  // 3, 2, 1
    }
    
    lstack_destroy(&s);
    return 0;
}
```

### 6.3 Stack in Rust — Generic Stack

```rust
// A generic, type-safe, memory-safe Stack in Rust
// No unsafe code needed — ownership handles everything

#[derive(Debug)]
pub struct Stack<T> {
    data: Vec<T>,   // Vec is a heap-allocated dynamic array
}

impl<T> Stack<T> {
    /// Create a new empty stack
    pub fn new() -> Self {
        Stack { data: Vec::new() }
    }
    
    /// Create with a pre-allocated capacity (avoids reallocations)
    pub fn with_capacity(cap: usize) -> Self {
        Stack { data: Vec::with_capacity(cap) }
    }
    
    /// Push an element onto the stack — O(1) amortized
    pub fn push(&mut self, value: T) {
        self.data.push(value);
    }
    
    /// Pop the top element — O(1)
    /// Returns None if empty (Rust's way of safe "optional" return)
    pub fn pop(&mut self) -> Option<T> {
        self.data.pop()
    }
    
    /// Peek at the top element without removing — O(1)
    /// Returns a shared reference (&T) — no ownership transfer
    pub fn peek(&self) -> Option<&T> {
        self.data.last()
    }
    
    /// Mutable peek — O(1)
    pub fn peek_mut(&mut self) -> Option<&mut T> {
        self.data.last_mut()
    }
    
    /// Check if stack is empty
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }
    
    /// Number of elements — O(1)
    pub fn size(&self) -> usize {
        self.data.len()
    }
    
    /// Clear all elements
    pub fn clear(&mut self) {
        self.data.clear();
    }
}

// Implement Display for nice printing
use std::fmt;
impl<T: fmt::Display> fmt::Display for Stack<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Stack (top -> bottom): ")?;
        for item in self.data.iter().rev() {
            write!(f, "{} ", item)?;
        }
        Ok(())
    }
}

fn main() {
    let mut stack: Stack<i32> = Stack::new();
    
    stack.push(10);
    stack.push(20);
    stack.push(30);
    println!("{}", stack);  // Stack (top -> bottom): 30 20 10
    
    println!("Peek: {:?}", stack.peek());   // Some(30)
    println!("Pop: {:?}", stack.pop());     // Some(30)
    println!("Size: {}", stack.size());     // 2
    println!("Empty: {}", stack.is_empty()); // false
    
    // Type safety: this would be a compile-time error:
    // stack.push("hello");  // ERROR: expected i32, found &str
    
    // Rust-specific: iterating without consuming
    let stack2: Stack<&str> = {
        let mut s = Stack::new();
        s.push("alpha");
        s.push("beta");
        s.push("gamma");
        s
    };  // stack2 is owned here
    
    println!("{}", stack2);  // Stack (top -> bottom): gamma beta alpha
}  // stack, stack2 automatically freed here — no free() needed!
```

### 6.4 Stack in Go — Using Slice

```go
package main

import (
    "errors"
    "fmt"
)

// Generic Stack using Go 1.18+ generics
type Stack[T any] struct {
    data []T
}

// NewStack creates an empty stack
func NewStack[T any]() *Stack[T] {
    return &Stack[T]{data: make([]T, 0)}
}

// Push adds an element to the top — O(1) amortized
func (s *Stack[T]) Push(val T) {
    s.data = append(s.data, val)
}

// Pop removes and returns the top element — O(1)
func (s *Stack[T]) Pop() (T, error) {
    var zero T  // zero value of T (0 for int, "" for string, etc.)
    if s.IsEmpty() {
        return zero, errors.New("stack underflow: pop on empty stack")
    }
    n := len(s.data)
    top := s.data[n-1]
    s.data = s.data[:n-1]  // re-slice: shrink by 1 (no copy needed)
    return top, nil
}

// Peek returns the top element without removing — O(1)
func (s *Stack[T]) Peek() (T, error) {
    var zero T
    if s.IsEmpty() {
        return zero, errors.New("peek on empty stack")
    }
    return s.data[len(s.data)-1], nil
}

// IsEmpty checks if stack has no elements
func (s *Stack[T]) IsEmpty() bool {
    return len(s.data) == 0
}

// Size returns the number of elements
func (s *Stack[T]) Size() int {
    return len(s.data)
}

func main() {
    s := NewStack[int]()
    s.Push(10)
    s.Push(20)
    s.Push(30)
    
    top, err := s.Peek()
    if err == nil {
        fmt.Printf("Peek: %d\n", top)  // 30
    }
    
    val, err := s.Pop()
    if err == nil {
        fmt.Printf("Pop: %d\n", val)   // 30
    }
    
    fmt.Printf("Size: %d\n", s.Size())  // 2
    
    // String stack — same generic type
    ss := NewStack[string]()
    ss.Push("hello")
    ss.Push("world")
    w, _ := ss.Pop()
    fmt.Println(w)  // world
}
```

---

## 7. Stack — Applications & Patterns

### Application 1: Balanced Parentheses

**Problem:** Given a string of brackets, check if they are balanced.
`"({[]})"` → valid | `"({[}])"` → invalid

**Why stack?** When you see a closing bracket, it must match the MOST RECENTLY SEEN opening bracket — that's LIFO!

```
Algorithm Flow:

For each character c in string:
    +------------------+
    | Is c an opener?  |  [, (, {
    | YES → push c     |
    +------------------+
           |
           v NO
    +------------------------+
    | Is c a closer?         |  ], ), }
    | YES:                   |
    |   if stack empty:      |
    |     return false       |
    |   pop top              |
    |   if top doesn't match |
    |     return false       |
    +------------------------+
           |
           v
    Continue to next char
    
At end: return stack.isEmpty()
```

```c
// C implementation
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

bool is_matching(char open, char close) {
    return (open == '(' && close == ')') ||
           (open == '[' && close == ']') ||
           (open == '{' && close == '}');
}

bool is_balanced(const char *str) {
    int len = strlen(str);
    char stack[len + 1];  // VLA — variable length array (C99)
    int top = -1;
    
    for (int i = 0; i < len; i++) {
        char c = str[i];
        if (c == '(' || c == '[' || c == '{') {
            stack[++top] = c;          // push opener
        } else if (c == ')' || c == ']' || c == '}') {
            if (top == -1) return false;  // no matching opener
            if (!is_matching(stack[top--], c)) return false;  // pop and check
        }
    }
    
    return top == -1;  // stack must be empty at end
}

int main(void) {
    printf("%s\n", is_balanced("({[]})") ? "VALID" : "INVALID"); // VALID
    printf("%s\n", is_balanced("({[}])") ? "VALID" : "INVALID"); // INVALID
    printf("%s\n", is_balanced("((("   ) ? "VALID" : "INVALID"); // INVALID
    return 0;
}
```

```rust
// Rust implementation
fn is_balanced(s: &str) -> bool {
    let mut stack: Vec<char> = Vec::new();
    
    for c in s.chars() {
        match c {
            '(' | '[' | '{' => stack.push(c),
            ')' => if stack.pop() != Some('(') { return false; },
            ']' => if stack.pop() != Some('[') { return false; },
            '}' => if stack.pop() != Some('{') { return false; },
            _ => {}
        }
    }
    stack.is_empty()
}

fn main() {
    println!("{}", is_balanced("({[]})"));  // true
    println!("{}", is_balanced("({[}])"));  // false
    println!("{}", is_balanced(""));        // true
}
```

### Application 2: Evaluating Postfix (RPN) Expressions

**What is Postfix?** Normal math is **infix**: `3 + 4`. Postfix is: `3 4 +` (operator comes AFTER operands).

Why useful? No need for parentheses or precedence rules. Calculators and compilers use this.

```
Example: Evaluate "3 4 + 2 *"
(means: (3 + 4) * 2 = 14)

Process: "3 4 + 2 *"

Token: 3 → push(3)    stack: [3]
Token: 4 → push(4)    stack: [3, 4]
Token: + → pop 4, pop 3, push(3+4=7)   stack: [7]
Token: 2 → push(2)    stack: [7, 2]
Token: * → pop 2, pop 7, push(7*2=14)  stack: [14]

Result: pop() = 14 ✓
```

```c
// C: Postfix evaluator
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

double eval_postfix(const char *expr) {
    double stack[100];
    int top = -1;
    
    char *token;
    char buf[256];
    strcpy(buf, expr);
    
    token = strtok(buf, " ");
    while (token != NULL) {
        if (isdigit(token[0]) || (token[0] == '-' && isdigit(token[1]))) {
            stack[++top] = atof(token);  // push number
        } else {
            double b = stack[top--];     // second operand
            double a = stack[top--];     // first operand
            switch (token[0]) {
                case '+': stack[++top] = a + b; break;
                case '-': stack[++top] = a - b; break;
                case '*': stack[++top] = a * b; break;
                case '/': stack[++top] = a / b; break;
            }
        }
        token = strtok(NULL, " ");
    }
    
    return stack[top];
}

int main(void) {
    printf("%.1f\n", eval_postfix("3 4 + 2 *"));   // 14.0
    printf("%.1f\n", eval_postfix("5 1 2 + 4 * + 3 -")); // 14.0
    return 0;
}
```

### Application 3: Function Call Stack (Recursion Simulation)

You can always convert recursion to iteration using an explicit stack — important for avoiding stack overflow in deep recursion.

```rust
// Recursive factorial — uses CALL STACK
fn factorial_recursive(n: u64) -> u64 {
    if n == 0 { 1 } else { n * factorial_recursive(n - 1) }
}

// Iterative factorial with explicit stack — uses HEAP STACK
fn factorial_iterative(n: u64) -> u64 {
    let mut stack: Vec<u64> = Vec::new();
    let mut result = 1u64;
    
    // Push all values
    for i in 1..=n {
        stack.push(i);
    }
    
    // Pop and multiply
    while let Some(val) = stack.pop() {
        result *= val;
    }
    result
}

fn main() {
    println!("{}", factorial_recursive(10));   // 3628800
    println!("{}", factorial_iterative(10));   // 3628800
}
```

---

## 8. Heap Data Structure — Theory

### What is a Heap (Data Structure)?

A **Heap** is a specialized **complete binary tree** that satisfies the **heap property**:

- **Max-Heap:** Every parent node is **greater than or equal to** its children. The maximum element is always at the root.
- **Min-Heap:** Every parent node is **less than or equal to** its children. The minimum element is always at the root.

### Prerequisite: Complete Binary Tree

A **binary tree** is a tree where each node has **at most 2 children** (left and right).

A **complete binary tree** is a binary tree where:
1. All levels are fully filled **except possibly the last level**
2. The last level has all nodes **as far left as possible**

```
Complete Binary Tree:         NOT Complete (gap in last level):
        1                              1
       / \                            / \
      2   3                          2   3
     / \ /                          / \   \
    4  5 6                         4   5   7
       ^                                 ^
    All levels full, last level left-filled    Missing node in middle
```

### The Heap Property (Visual)

```
MAX-HEAP example:
           100           ← Root = Maximum element
          /    \
        50       80
       /  \     /  \
     40    30  60   70
    /  \
   10   20

Property: Every parent >= its children
100 >= 50, 100 >= 80  ✓
50 >= 40, 50 >= 30    ✓
80 >= 60, 80 >= 70    ✓
40 >= 10, 40 >= 20    ✓


MIN-HEAP example:
           1             ← Root = Minimum element
          / \
        10    5
       /  \  / \
      30  20 8   7

Property: Every parent <= its children
1 <= 10, 1 <= 5   ✓
10 <= 30, 10 <= 20 ✓
5 <= 8, 5 <= 7    ✓
```

### Key Insight: Heap Stored as Array!

The elegant secret of heaps: **a complete binary tree can be stored compactly in an array**, without any pointers.

For a node at index `i` (0-indexed):
- **Left child:**  `2*i + 1`
- **Right child:** `2*i + 2`
- **Parent:**      `(i - 1) / 2` (integer division)

```
Max-Heap tree:
           100
          /    \
        50       80
       /  \     /  \
     40    30  60   70

Array representation:
Index:  [0]  [1]  [2]  [3]  [4]  [5]  [6]
Value:  100   50   80   40   30   60   70

Verify relationships:
- Node at index 0 (100): left=data[1]=50, right=data[2]=80 ✓
- Node at index 1 (50):  left=data[3]=40, right=data[4]=30 ✓
- Node at index 2 (80):  left=data[5]=60, right=data[6]=70 ✓
- Node at index 3 (40):  parent=data[(3-1)/2]=data[1]=50 ✓
```

This array storage means:
- No memory wasted on pointers
- Excellent cache locality (sequential access)
- Simple index arithmetic instead of pointer traversal

### The Two Critical Heap Operations: Heapify Up & Heapify Down

#### Heapify Up (Bubble Up / Sift Up)
Used after **inserting** a new element. The new element is added at the end and bubbles up until heap property is restored.

```
Heapify Up for Max-Heap:

Insert 90 into:           After adding 90 at end:
       100                       100
      /    \                    /    \
    50       80               50       80
   /  \     /  \             /  \     /  \
  40   30  60   70          40   30  60   70
                                /
                               90

Array: [100, 50, 80, 40, 30, 60, 70, 90]
       90 is at index 7, parent at (7-1)/2 = 3, value = 40

Step 1: 90 > 40 (parent)? YES → swap
       100
      /    \
    50       80
   /  \     /  \
  90   30  60   70
  /
 40
Array: [100, 50, 80, 90, 30, 60, 70, 40]

Step 2: 90 is now at index 3, parent at (3-1)/2 = 1, value = 50
90 > 50? YES → swap
       100
      /    \
    90       80
   /  \     /  \
  50   30  60   70
  /
 40
Array: [100, 90, 80, 50, 30, 60, 70, 40]

Step 3: 90 is now at index 1, parent at (1-1)/2 = 0, value = 100
90 > 100? NO → STOP

Final heap is valid. ✓
```

#### Heapify Down (Bubble Down / Sift Down)
Used after **removing the root** (extracting max/min). The last element replaces the root, then sifts down.

```
Extract Max (100) from heap:
       100
      /    \
    90       80
   /  \     /  \
  50   30  60   70
  /
 40

Step 1: Remove root (100), move last element (40) to root:
        40
      /    \
    90       80
   /  \     /  \
  50   30  60   70

Array: [40, 90, 80, 50, 30, 60, 70]

Step 2: 40 at index 0. Children: left=data[1]=90, right=data[2]=80
        Max child = 90. 40 < 90 → swap with left child
        90
      /    \
    40       80
   /  \     /  \
  50   30  60   70
Array: [90, 40, 80, 50, 30, 60, 70]

Step 3: 40 at index 1. Children: left=data[3]=50, right=data[4]=30
        Max child = 50. 40 < 50 → swap with left child
        90
      /    \
    50       80
   /  \     /  \
  40   30  60   70
Array: [90, 50, 80, 40, 30, 60, 70]

Step 4: 40 at index 3. Children: left=data[7]=doesn't exist.
        No children → STOP

Final heap is valid. ✓  Max extracted = 100
```

### Algorithm Flowcharts

```
=== HEAPIFY UP (for Max-Heap, after insert) ===

     Start: new element at index i
            |
            v
     +------------------+
     | i == 0?          | YES → Done (reached root)
     | (root reached?)  |------>
     +------------------+
            | NO
            v
     parent_i = (i - 1) / 2
            |
            v
     +----------------------------------------+
     | data[i] > data[parent_i]?              |
     | (violates max-heap property?)          |
     +----------------------------------------+
            |YES                    |NO
            v                       v
     swap(data[i], data[parent_i])  Done (heap property restored)
            |
            v
     i = parent_i
            |
            v
     (loop back to top)


=== HEAPIFY DOWN (for Max-Heap, after extract) ===

     Start: element at index i (usually root = 0)
            |
            v
     left  = 2*i + 1
     right = 2*i + 2
            |
            v
     +-------------------------------------------+
     | left < size? (left child exists?)         |
     +-------------------------------------------+
            |YES                    |NO
            v                       v
     largest = left               Done (no children, leaf node)
            |
            v
     +-------------------------------------------+
     | right < size AND data[right] > data[left] |
     | (right child exists and is bigger?)       |
     +-------------------------------------------+
            |YES                    |NO
            v                       v
     largest = right           (keep largest = left)
            |                       |
            +----------+------------+
                       v
     +-------------------------------------------+
     | data[largest] > data[i]?                  |
     | (largest child bigger than current?)      |
     +-------------------------------------------+
            |YES                    |NO
            v                       v
     swap(data[i], data[largest])  Done (heap property holds)
            |
            v
     i = largest
            |
            v
     (loop back to top)
```

### Building a Heap from an Array (Heapify / Build-Heap)

**Naive approach:** Insert elements one by one → O(n log n)

**Smart approach:** Start from last non-leaf and heapify down each node → **O(n)!**

```
Why O(n) and not O(n log n)?

Key insight: Most nodes are near the BOTTOM of the tree (leaves).
Leaves don't need any heapify work (they have no children).

In a tree of height h:
- Level h (leaves): n/2 nodes, each do 0 work
- Level h-1:        n/4 nodes, each do 1 swap (height 1)
- Level h-2:        n/8 nodes, each do 2 swaps (height 2)
- ...
- Level 0 (root):   1 node,    does h swaps

Total work = n/4 * 1 + n/8 * 2 + n/16 * 3 + ... = O(n)  (geometric series)

Last non-leaf node index = (n/2) - 1  (0-indexed)

Build-Heap algorithm:
for i from (n/2 - 1) down to 0:
    heapify_down(arr, n, i)
```

```
Example: Build max-heap from [4, 10, 3, 5, 1]

Array: [4, 10, 3, 5, 1]
         0   1  2  3  4

Tree view:
      4
     / \
   10    3
   / \
  5    1

n=5, last non-leaf = 5/2 - 1 = 1

Step 1: heapify_down at index 1 (value=10)
  Children: left=data[3]=5, right=data[4]=1
  max child = 5. 10 > 5, no swap needed.

Step 2: heapify_down at index 0 (value=4)
  Children: left=data[1]=10, right=data[2]=3
  max child = 10. 4 < 10 → swap(0, 1)
  Array: [10, 4, 3, 5, 1]
  
  Continue at index 1 (value=4):
  Children: left=data[3]=5, right=data[4]=1
  max child = 5. 4 < 5 → swap(1, 3)
  Array: [10, 5, 3, 4, 1]
  
  Continue at index 3 (value=4): no children. Done.

Final max-heap: [10, 5, 3, 4, 1]
      10
     /  \
    5     3
   / \
  4    1  ✓
```

---

## 9. Heap — Implementations (C, Rust, Go)

### 9.1 Max-Heap in C

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct {
    int *data;
    int size;
    int capacity;
} MaxHeap;

// Helper: swap two integers
static void swap(int *a, int *b) {
    int tmp = *a;
    *a = *b;
    *b = tmp;
}

// Initialize heap
MaxHeap* heap_create(int capacity) {
    MaxHeap *h = (MaxHeap *)malloc(sizeof(MaxHeap));
    h->data = (int *)malloc(capacity * sizeof(int));
    h->size = 0;
    h->capacity = capacity;
    return h;
}

void heap_destroy(MaxHeap *h) {
    free(h->data);
    free(h);
}

// Index helpers
static int parent(int i)  { return (i - 1) / 2; }
static int left(int i)    { return 2 * i + 1; }
static int right(int i)   { return 2 * i + 2; }

// Sift up: restore heap property after insert
static void sift_up(MaxHeap *h, int i) {
    // While not root AND current > parent: swap upward
    while (i > 0 && h->data[i] > h->data[parent(i)]) {
        swap(&h->data[i], &h->data[parent(i)]);
        i = parent(i);
    }
}

// Sift down: restore heap property after extract
static void sift_down(MaxHeap *h, int i) {
    int largest = i;
    int l = left(i);
    int r = right(i);
    
    // Find the largest among node, left child, right child
    if (l < h->size && h->data[l] > h->data[largest])
        largest = l;
    if (r < h->size && h->data[r] > h->data[largest])
        largest = r;
    
    if (largest != i) {
        swap(&h->data[i], &h->data[largest]);
        sift_down(h, largest);  // recurse down
    }
}

// Insert: add element and sift up — O(log n)
bool heap_insert(MaxHeap *h, int value) {
    if (h->size >= h->capacity) {
        // Grow the array (double capacity)
        h->capacity *= 2;
        h->data = (int *)realloc(h->data, h->capacity * sizeof(int));
        if (!h->data) return false;
    }
    h->data[h->size] = value;      // place at end
    sift_up(h, h->size);           // bubble up
    h->size++;
    return true;
}

// Extract max: remove root, put last at root, sift down — O(log n)
bool heap_extract_max(MaxHeap *h, int *out) {
    if (h->size == 0) return false;
    
    *out = h->data[0];                     // save root (max)
    h->data[0] = h->data[h->size - 1];    // move last to root
    h->size--;
    if (h->size > 0) sift_down(h, 0);     // restore heap
    return true;
}

// Peek at max — O(1)
bool heap_peek(const MaxHeap *h, int *out) {
    if (h->size == 0) return false;
    *out = h->data[0];
    return true;
}

// Build heap from array — O(n)
MaxHeap* heap_build(int *arr, int n) {
    MaxHeap *h = heap_create(n);
    // Copy array into heap
    for (int i = 0; i < n; i++) {
        h->data[i] = arr[i];
    }
    h->size = n;
    
    // Heapify from last non-leaf to root
    for (int i = n / 2 - 1; i >= 0; i--) {
        sift_down(h, i);
    }
    return h;
}

void heap_print(const MaxHeap *h) {
    printf("Heap [size=%d]: ", h->size);
    for (int i = 0; i < h->size; i++) {
        printf("%d ", h->data[i]);
    }
    printf("\n");
}

int main(void) {
    // Test insert
    MaxHeap *h = heap_create(10);
    heap_insert(h, 10);
    heap_insert(h, 50);
    heap_insert(h, 30);
    heap_insert(h, 80);
    heap_insert(h, 20);
    
    heap_print(h);  // Heap [size=5]: 80 50 30 10 20
    
    int max_val;
    heap_extract_max(h, &max_val);
    printf("Extracted max: %d\n", max_val);  // 80
    heap_print(h);  // Heap [size=4]: 50 20 30 10
    
    // Test build-heap
    int arr[] = {4, 10, 3, 5, 1, 8};
    MaxHeap *h2 = heap_build(arr, 6);
    heap_print(h2);  // Heap [size=6]: 10 5 8 4 1 3
    
    heap_destroy(h);
    heap_destroy(h2);
    return 0;
}
```

### 9.2 Min-Heap in Rust — Full Generic Implementation

```rust
use std::cmp::Ordering;

/// A generic Min-Heap (smallest element at top)
/// T must implement Ord for comparison
#[derive(Debug)]
pub struct MinHeap<T: Ord> {
    data: Vec<T>,
}

impl<T: Ord> MinHeap<T> {
    pub fn new() -> Self {
        MinHeap { data: Vec::new() }
    }
    
    pub fn with_capacity(cap: usize) -> Self {
        MinHeap { data: Vec::with_capacity(cap) }
    }
    
    pub fn size(&self) -> usize { self.data.len() }
    pub fn is_empty(&self) -> bool { self.data.is_empty() }
    
    /// Peek at minimum element — O(1)
    pub fn peek(&self) -> Option<&T> {
        self.data.first()
    }
    
    /// Insert element — O(log n)
    pub fn insert(&mut self, value: T) {
        self.data.push(value);
        self.sift_up(self.data.len() - 1);
    }
    
    /// Extract minimum element — O(log n)
    pub fn extract_min(&mut self) -> Option<T> {
        if self.data.is_empty() { return None; }
        
        let n = self.data.len();
        self.data.swap(0, n - 1);         // swap root with last
        let min = self.data.pop();        // remove last (was root = min)
        if !self.data.is_empty() {
            self.sift_down(0);            // restore heap from root
        }
        min
    }
    
    /// Build heap from a Vec — O(n)
    pub fn from_vec(mut vec: Vec<T>) -> Self {
        let n = vec.len();
        // Apply sift_down from last non-leaf to root
        // We do this manually since we can't call self methods easily during construction
        let mut heap = MinHeap { data: vec };
        if n > 1 {
            let start = n / 2;
            for i in (0..start).rev() {
                heap.sift_down(i);
            }
        }
        heap
    }
    
    // === Private helpers ===
    
    fn parent(i: usize) -> usize { (i - 1) / 2 }
    fn left(i: usize) -> usize   { 2 * i + 1 }
    fn right(i: usize) -> usize  { 2 * i + 2 }
    
    fn sift_up(&mut self, mut i: usize) {
        // While i is not root AND current < parent: swap upward (min-heap)
        while i > 0 {
            let p = Self::parent(i);
            if self.data[i] < self.data[p] {
                self.data.swap(i, p);
                i = p;
            } else {
                break;
            }
        }
    }
    
    fn sift_down(&mut self, mut i: usize) {
        let n = self.data.len();
        loop {
            let l = Self::left(i);
            let r = Self::right(i);
            let mut smallest = i;
            
            // Find smallest among node, left, right
            if l < n && self.data[l] < self.data[smallest] {
                smallest = l;
            }
            if r < n && self.data[r] < self.data[smallest] {
                smallest = r;
            }
            
            if smallest == i { break; }  // heap property satisfied
            
            self.data.swap(i, smallest);
            i = smallest;
        }
    }
}

// Drain the heap in sorted order (ascending for min-heap)
impl<T: Ord + Clone> MinHeap<T> {
    pub fn drain_sorted(&mut self) -> Vec<T> {
        let mut result = Vec::with_capacity(self.data.len());
        while let Some(val) = self.extract_min() {
            result.push(val);
        }
        result
    }
}

fn main() {
    let mut heap: MinHeap<i32> = MinHeap::new();
    
    heap.insert(50);
    heap.insert(10);
    heap.insert(30);
    heap.insert(80);
    heap.insert(1);
    
    println!("Min (peek): {:?}", heap.peek());      // Some(1)
    println!("Size: {}", heap.size());              // 5
    
    while let Some(val) = heap.extract_min() {
        print!("{} ", val);  // 1 10 30 50 80 (sorted!)
    }
    println!();
    
    // Build from vec — O(n)
    let nums = vec![9, 3, 7, 1, 5, 2, 8];
    let mut heap2 = MinHeap::from_vec(nums);
    println!("Heap from vec, min: {:?}", heap2.peek()); // Some(1)
    
    // Drain sorted
    let sorted = heap2.drain_sorted();
    println!("{:?}", sorted); // [1, 2, 3, 5, 7, 8, 9]
}
```

### 9.3 Min-Heap in Go

```go
package main

import (
    "fmt"
    "errors"
)

// MinHeap stores integers in min-heap order
type MinHeap struct {
    data []int
}

func NewMinHeap() *MinHeap {
    return &MinHeap{data: make([]int, 0)}
}

func (h *MinHeap) Size() int  { return len(h.data) }
func (h *MinHeap) IsEmpty() bool { return len(h.data) == 0 }

func (h *MinHeap) Peek() (int, error) {
    if h.IsEmpty() {
        return 0, errors.New("heap is empty")
    }
    return h.data[0], nil
}

func parent(i int) int { return (i - 1) / 2 }
func left(i int) int   { return 2*i + 1 }
func right(i int) int  { return 2*i + 2 }

func (h *MinHeap) siftUp(i int) {
    for i > 0 {
        p := parent(i)
        if h.data[i] < h.data[p] {
            h.data[i], h.data[p] = h.data[p], h.data[i]
            i = p
        } else {
            break
        }
    }
}

func (h *MinHeap) siftDown(i int) {
    n := h.Size()
    for {
        smallest := i
        l, r := left(i), right(i)
        if l < n && h.data[l] < h.data[smallest] {
            smallest = l
        }
        if r < n && h.data[r] < h.data[smallest] {
            smallest = r
        }
        if smallest == i {
            break
        }
        h.data[i], h.data[smallest] = h.data[smallest], h.data[i]
        i = smallest
    }
}

// Insert: O(log n)
func (h *MinHeap) Insert(val int) {
    h.data = append(h.data, val)
    h.siftUp(len(h.data) - 1)
}

// ExtractMin: O(log n)
func (h *MinHeap) ExtractMin() (int, error) {
    if h.IsEmpty() {
        return 0, errors.New("heap underflow")
    }
    n := h.Size()
    min := h.data[0]
    h.data[0] = h.data[n-1]
    h.data = h.data[:n-1]
    if !h.IsEmpty() {
        h.siftDown(0)
    }
    return min, nil
}

// BuildHeap: O(n) - build from an existing slice
func BuildMinHeap(arr []int) *MinHeap {
    h := &MinHeap{data: make([]int, len(arr))}
    copy(h.data, arr)
    n := len(h.data)
    for i := n/2 - 1; i >= 0; i-- {
        h.siftDown(i)
    }
    return h
}

func main() {
    h := NewMinHeap()
    for _, v := range []int{50, 10, 30, 80, 1, 25} {
        h.Insert(v)
    }
    
    fmt.Printf("Size: %d\n", h.Size())
    
    min, _ := h.Peek()
    fmt.Printf("Min: %d\n", min)  // 1
    
    // Extract all in sorted order
    fmt.Print("Sorted: ")
    for !h.IsEmpty() {
        val, _ := h.ExtractMin()
        fmt.Printf("%d ", val)
    }
    fmt.Println()  // 1 10 25 30 50 80
    
    // Build-heap O(n)
    h2 := BuildMinHeap([]int{9, 3, 7, 1, 5})
    top, _ := h2.Peek()
    fmt.Printf("Built heap min: %d\n", top)  // 1
}
```

---

## 10. Heap Sort

**Heap Sort** is a comparison-based sorting algorithm that uses a heap.

**Steps:**
1. Build a Max-Heap from the array — O(n)
2. Repeatedly extract the max (swap root with last, reduce size, heapify) — O(n log n)

```
Heap Sort — In-place:

Array: [4, 10, 3, 5, 1]

Phase 1: Build Max-Heap (O(n))
Result: [10, 5, 3, 4, 1]

Phase 2: Extract max n times:

Iteration 1: swap(0, 4), size=4, siftDown(0)
[1, 5, 3, 4, | 10]  → siftDown → [5, 4, 3, 1, | 10]

Iteration 2: swap(0, 3), size=3, siftDown(0)
[1, 4, 3, | 5, 10]  → siftDown → [4, 1, 3, | 5, 10]

Iteration 3: swap(0, 2), size=2, siftDown(0)
[3, 1, | 4, 5, 10]  → siftDown → [3, 1, | 4, 5, 10]

Iteration 4: swap(0, 1), size=1
[1, | 3, 4, 5, 10]

Final sorted: [1, 3, 4, 5, 10] ✓
```

```c
// In-place heap sort in C — O(n log n), O(1) extra space
#include <stdio.h>

void swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }

// Max-heapify subtree rooted at index i, with heap size n
void heapify(int *arr, int n, int i) {
    int largest = i;
    int l = 2 * i + 1;
    int r = 2 * i + 2;
    
    if (l < n && arr[l] > arr[largest]) largest = l;
    if (r < n && arr[r] > arr[largest]) largest = r;
    
    if (largest != i) {
        swap(&arr[i], &arr[largest]);
        heapify(arr, n, largest);  // recurse down
    }
}

void heap_sort(int *arr, int n) {
    // Phase 1: Build max-heap — O(n)
    for (int i = n / 2 - 1; i >= 0; i--) {
        heapify(arr, n, i);
    }
    
    // Phase 2: Extract elements one by one — O(n log n)
    for (int i = n - 1; i > 0; i--) {
        swap(&arr[0], &arr[i]);  // move current max to end
        heapify(arr, i, 0);      // heapify reduced heap
    }
}

int main(void) {
    int arr[] = {12, 11, 13, 5, 6, 7};
    int n = sizeof(arr) / sizeof(arr[0]);
    
    heap_sort(arr, n);
    
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");  // 5 6 7 11 12 13
    return 0;
}
```

```rust
// Heap sort in Rust — in-place, O(n log n), O(1) space
fn heapify(arr: &mut Vec<i32>, n: usize, i: usize) {
    let mut largest = i;
    let l = 2 * i + 1;
    let r = 2 * i + 2;
    
    if l < n && arr[l] > arr[largest] { largest = l; }
    if r < n && arr[r] > arr[largest] { largest = r; }
    
    if largest != i {
        arr.swap(i, largest);
        heapify(arr, n, largest);
    }
}

fn heap_sort(arr: &mut Vec<i32>) {
    let n = arr.len();
    
    // Build max-heap
    for i in (0..n / 2).rev() {
        heapify(arr, n, i);
    }
    
    // Extract elements
    for i in (1..n).rev() {
        arr.swap(0, i);
        heapify(arr, i, 0);
    }
}

fn main() {
    let mut data = vec![12, 11, 13, 5, 6, 7];
    heap_sort(&mut data);
    println!("{:?}", data);  // [5, 6, 7, 11, 12, 13]
}
```

```go
// Heap sort in Go
package main

import "fmt"

func heapify(arr []int, n, i int) {
    largest := i
    l, r := 2*i+1, 2*i+2
    if l < n && arr[l] > arr[largest] { largest = l }
    if r < n && arr[r] > arr[largest] { largest = r }
    if largest != i {
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)
    }
}

func heapSort(arr []int) {
    n := len(arr)
    for i := n/2 - 1; i >= 0; i-- { heapify(arr, n, i) }
    for i := n - 1; i > 0; i-- {
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    }
}

func main() {
    arr := []int{12, 11, 13, 5, 6, 7}
    heapSort(arr)
    fmt.Println(arr)  // [5 6 7 11 12 13]
}
```

---

## 11. Priority Queue via Heap

A **Priority Queue** is an ADT where each element has a **priority**. The element with the highest (or lowest) priority is always served first.

**Heap IS the perfect implementation** of a priority queue.

```
Priority Queue — Min Priority (smallest = highest priority):

Insert (task, priority):
[("email", 3), ("deploy", 1), ("meeting", 2)]

Internal min-heap (by priority):
       (deploy, 1)
       /           \
 (meeting, 2)   (email, 3)

ExtractMin() → ("deploy", 1)   ← highest priority served first
```

```c
// Priority Queue in C using Min-Heap
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_SIZE 100

typedef struct {
    char name[50];
    int priority;   // lower number = higher priority
} Task;

typedef struct {
    Task data[MAX_SIZE];
    int size;
} PriorityQueue;

void pq_init(PriorityQueue *pq) { pq->size = 0; }

static void swap_tasks(Task *a, Task *b) { Task t = *a; *a = *b; *b = t; }

static void sift_up(PriorityQueue *pq, int i) {
    while (i > 0) {
        int p = (i - 1) / 2;
        if (pq->data[i].priority < pq->data[p].priority) {
            swap_tasks(&pq->data[i], &pq->data[p]);
            i = p;
        } else break;
    }
}

static void sift_down(PriorityQueue *pq, int i) {
    int smallest = i, l = 2*i+1, r = 2*i+2;
    if (l < pq->size && pq->data[l].priority < pq->data[smallest].priority)
        smallest = l;
    if (r < pq->size && pq->data[r].priority < pq->data[smallest].priority)
        smallest = r;
    if (smallest != i) {
        swap_tasks(&pq->data[i], &pq->data[smallest]);
        sift_down(pq, smallest);
    }
}

void pq_insert(PriorityQueue *pq, const char *name, int priority) {
    Task t;
    strncpy(t.name, name, 49);
    t.priority = priority;
    pq->data[pq->size] = t;
    sift_up(pq, pq->size++);
}

Task pq_extract_min(PriorityQueue *pq) {
    Task min = pq->data[0];
    pq->data[0] = pq->data[--pq->size];
    if (pq->size > 0) sift_down(pq, 0);
    return min;
}

int main(void) {
    PriorityQueue pq;
    pq_init(&pq);
    
    pq_insert(&pq, "Deploy to production", 1);
    pq_insert(&pq, "Team meeting",          2);
    pq_insert(&pq, "Reply to email",        3);
    pq_insert(&pq, "Fix critical bug",      1);
    pq_insert(&pq, "Code review",           2);
    
    printf("Processing tasks by priority:\n");
    while (pq.size > 0) {
        Task t = pq_extract_min(&pq);
        printf("  Priority %d: %s\n", t.priority, t.name);
    }
    // Priority 1: Deploy to production
    // Priority 1: Fix critical bug
    // Priority 2: Team meeting
    // Priority 2: Code review
    // Priority 3: Reply to email
    
    return 0;
}
```

---

## 12. Complexity Master Reference

### Stack Data Structure

```
+====================+================+=================+
|   Operation        | Array Stack    | Linked Stack    |
+====================+================+=================+
| push               | O(1) amortized | O(1)            |
| pop                | O(1)           | O(1)            |
| peek               | O(1)           | O(1)            |
| isEmpty / size     | O(1)           | O(1)            |
| Space (n elements) | O(n)           | O(n) + overhead |
+====================+================+=================+
```

### Heap Data Structure

```
+==========================+=============+===================+
|   Operation              | Time        | Notes             |
+==========================+=============+===================+
| insert                   | O(log n)    | sift up           |
| extract_max / min        | O(log n)    | sift down         |
| peek (find max/min)      | O(1)        | root access       |
| build_heap (from array)  | O(n)        | smart heapify     |
| heap_sort                | O(n log n)  | best+avg+worst    |
| delete arbitrary element | O(log n)    | need index        |
| increase/decrease key    | O(log n)    | sift up or down   |
| merge two heaps          | O(n)        | rebuild           |
| Space                    | O(n)        | array storage     |
+==========================+=============+===================+
```

### Memory: Stack vs Heap

```
+========================+====================+=====================+
| Operation              | Stack Memory       | Heap Memory         |
+========================+====================+=====================+
| Allocate               | O(1) — SP adjust  | O(1) amortized      |
| Deallocate             | O(1) — SP adjust  | O(1) amortized      |
| Access                 | O(1)              | O(1)                |
| Find free space        | O(1) — always top | O(1) to O(n)        |
+========================+====================+=====================+
```

---

## 13. Mental Models for Mastery

### Mental Model 1: The Two Heaps (Median Finding)

**Problem:** Find the running median of a stream of numbers.

**Solution:** Use two heaps!
- Max-Heap: stores the lower half of numbers
- Min-Heap: stores the upper half of numbers
- Median = root of larger heap (or average of both roots)

```
Stream: 5, 3, 8, 1, 9, 2

After inserting 5:
  max_heap: [5]       min_heap: []
  Median = 5

After inserting 3:
  max_heap: [5, 3]    min_heap: []   → rebalance
  max_heap: [3]       min_heap: [5]
  Median = (3+5)/2 = 4

After inserting 8:
  max_heap: [3]       min_heap: [5, 8]  → rebalance
  max_heap: [5, 3]    min_heap: [8]
  Median = 5

This pattern is an interview classic.
```

### Mental Model 2: Heap as a "Smart Queue"

Normal Queue: FIFO (first in, first out)
Stack:        LIFO (last in, first out)
Heap/PQ:      **Priority-out** (highest priority out first, regardless of insertion order)

This abstraction is everywhere:
- OS scheduling (process priorities)
- Dijkstra's shortest path (min-heap)
- A* search (heuristic-based priority)
- Event simulation (process earliest event first)
- Huffman coding (merge smallest frequencies first)

### Mental Model 3: Deliberate Practice Framework

```
MASTERY LEVELS for Stack/Heap:

Level 1 — Recognition:
  Can you identify when a problem needs a stack or heap?
  ✓ Balanced brackets → Stack
  ✓ Top-K elements → Heap
  ✓ Undo/Redo → Stack
  ✓ Shortest path → Min-Heap (priority queue)

Level 2 — Implementation:
  Can you implement from scratch in 20 minutes?
  ✓ Array stack
  ✓ Min/Max heap with all operations
  ✓ Heap sort

Level 3 — Adaptation:
  Can you modify the structure for new constraints?
  ✓ Stack with min/max in O(1)
  ✓ Heap with arbitrary deletion
  ✓ Two heaps for median

Level 4 — Invention:
  Can you combine structures for novel problems?
  ✓ Heap + HashMap for O(log n) delete
  ✓ Stack + Heap for scheduling
  ✓ Monotonic stack for "next greater element"
```

### Mental Model 4: Performance Intuition Table

```
If you need:                    Use:
──────────────────────────────────────────────────────
LIFO access pattern           → Stack (O(1) all ops)
Smallest/largest K elements   → Heap (O(n log k))
Merge K sorted lists          → Min-Heap (O(n log k))
Running median                → Two Heaps
Process highest priority      → Max/Min Heap (Priority Queue)
Sort in O(n log n) O(1) space → Heap Sort
Undo/Redo operations          → Stack
DFS traversal                 → Stack (or recursion)
Function call tracking        → Call Stack (stack memory)
Dynamic sized data            → Heap memory (Vec, Box, etc.)
```

### Cognitive Principle: Chunking

When studying heap operations, don't memorize steps — **chunk them** into meaningful units:
- `insert` = "add to end + bubble up"
- `extract` = "swap root with end + remove end + bubble down"
- `build` = "heapify from middle to start"

Each operation has a **single sentence description**. When you can describe all operations in one sentence each without thinking, you've achieved **chunked mastery**.

### The Monk's Practice Schedule

```
Week 1: Stack (Memory) + Stack (DS)
  Day 1-2: Understand stack memory (stack frames, SP, overflow)
  Day 3-4: Implement array stack + linked stack in C
  Day 5-6: Implement in Rust + Go
  Day 7:   Solve: balanced brackets, RPN evaluator, min-stack

Week 2: Heap (DS)
  Day 1-2: Master sift_up and sift_down (draw on paper)
  Day 3-4: Implement full min-heap in C
  Day 5:   Implement in Rust + Go
  Day 6:   Implement heap sort
  Day 7:   Solve: top-K elements, merge K sorted arrays

Week 3: Advanced Patterns
  Day 1-2: Two heaps for median
  Day 3-4: Priority queue applications (Dijkstra)
  Day 5-7: Contest problems (LeetCode: 295, 347, 23, 502)
```

---

## Final Summary

```
=== WHAT YOU NOW KNOW ===

STACK MEMORY:
  • LIFO region managed by CPU — stack frames, SP register
  • Fast (O(1)), limited size, auto-managed
  • Stack overflow from infinite recursion
  • Each thread has its own stack

HEAP MEMORY:
  • Dynamic pool — manual(C), ownership(Rust), GC(Go)
  • Flexible size, slower, shared between threads
  • Fragmentation is a real concern
  • Rust's ownership eliminates memory bugs at compile time

STACK DATA STRUCTURE:
  • LIFO — push/pop/peek in O(1)
  • Implemented via array or linked list
  • Core to: recursion, expression eval, DFS, undo/redo

HEAP DATA STRUCTURE:
  • Complete binary tree stored as array
  • Heap property: parent ≥ children (max) or ≤ (min)
  • Insert: sift up O(log n)
  • Extract: sift down O(log n)
  • Build from array: O(n) — the genius algorithm
  • Heap sort: O(n log n) in-place
  • Foundation of Priority Queue
```

---

*"Mastery is not a destination — it is the quality of attention you bring to each repetition."*

*Keep your stack shallow and your heap disciplined.*

Now I'll craft the full in-depth markdown document. This will be extensive — covering memory model fundamentals, stack data structure, and heap data structure with full implementations.Here's what your guide covers, structured like training with a world-class mentor:

---

## What's Inside (13 Deep Sections)

**Part I — Memory Architecture**
- What RAM actually is (virtual address space, process segments)
- Stack Memory — stack frames, the Stack Pointer register, function call lifecycle step-by-step, stack overflow mechanics
- Heap Memory — `malloc`/`free`/`realloc` in C, `Box<T>`/`Vec` in Rust with ownership semantics, Go's escape analysis and GC
- Full comparison table: speed, fragmentation, thread safety, lifetime, errors

**Part II — Stack Data Structure**
- LIFO concept, array vs linked-list decision tree with tradeoffs
- All operations with internals visualized in ASCII
- Full implementations: C (array + linked-list), Rust (generic with `Option<T>`), Go (generic with Go 1.18+)
- Applications: Balanced parentheses, RPN evaluator, recursion→iteration conversion

**Part III — Heap Data Structure**
- Complete binary tree prerequisite explained
- Max-heap and min-heap with heap property proven visually
- **The array trick** — why a heap needs no pointers, with index formulas
- Sift-Up and Sift-Down with full step-by-step ASCII walkthroughs
- Build-Heap in O(n) — with the mathematical proof of why it's not O(n log n)
- Full implementations: C (MaxHeap), Rust (generic `MinHeap<T: Ord>`), Go (MinHeap)
- Heap Sort in all 3 languages, Priority Queue with task scheduling

**Part IV — Mastery Framework**
- Two-Heap pattern for running median
- Heap as "Smart Queue" mental model
- 4-level mastery ladder (Recognition → Invention)
- Chunking strategy for internalizing operations
- 3-week deliberate practice schedule with LeetCode targets

---

**Key insight to carry forward:** The heap's O(n) build is one of the most elegant results in CS — most people assume it's O(n log n). Internalize *why* it's O(n) (most nodes are leaves doing zero work) and you'll think like a top 1% engineer.