# The Complete Linked List Manipulation Guide
## From Fundamentals to Mastery — Rust · C · Go

---

> **Mental Model Principle:** Before you write a single line of code, draw the boxes and arrows.
> Every linked list bug is fundamentally a *pointer/reference confusion* bug. Internalize the
> memory layout first. Code second.

---

## Table of Contents

1. [What Is a Linked List? — First Principles](#1-what-is-a-linked-list)
2. [Memory Internals — The Real Picture](#2-memory-internals)
3. [Types of Linked Lists](#3-types-of-linked-lists)
4. [Node Structure — Rust · C · Go](#4-node-structure)
5. [All Operations — What You CAN Do](#5-all-operations)
   - 5.1 Traversal
   - 5.2 Insertion (Head / Tail / Middle)
   - 5.3 Deletion (Head / Tail / Middle / By Value)
   - 5.4 Search
   - 5.5 Reversal (Iterative + Recursive)
   - 5.6 Find the Middle (Floyd's Tortoise & Hare)
   - 5.7 Cycle Detection & Removal
   - 5.8 Merge Two Sorted Lists
   - 5.9 Sort a Linked List (Merge Sort)
   - 5.10 Rotate a List
   - 5.11 Find Intersection of Two Lists
   - 5.12 Palindrome Check
   - 5.13 Remove Nth Node from End
   - 5.14 Flatten a Multilevel List
   - 5.15 Clone a List with Random Pointers
   - 5.16 Partition / Reorder
   - 5.17 Doubly Linked List Operations
   - 5.18 Circular Linked List Operations
6. [What You CANNOT Do — Hard Limits & Constraints](#6-what-you-cannot-do)
7. [Common Mistakes — The Mistake Encyclopedia](#7-common-mistakes)
8. [Two-Pointer Technique — The Master Pattern](#8-two-pointer-technique)
9. [Sentinel / Dummy Node Pattern](#9-sentinel-dummy-node-pattern)
10. [Time & Space Complexity Reference](#10-complexity-reference)
11. [Mental Models for Expert Thinking](#11-mental-models)
12. [Language-Specific Pitfalls — Rust · C · Go](#12-language-specific-pitfalls)

---

## 1. What Is a Linked List?

### First Principles — Starting from Zero

An **array** stores elements in contiguous memory:

```
Array:   [10][20][30][40][50]
          ^   ^   ^   ^   ^
          0   1   2   3   4   (indices)
All adjacent in RAM — index means "base address + index * element_size"
```

The entire array lives as one block. To find element `i`, the CPU jumps directly.
But insertion/deletion in the *middle* forces shifting every element after it.

A **linked list** says: *"I don't need to be contiguous. Each element knows where the next one is."*

```
Node 1          Node 2          Node 3
+--------+      +--------+      +--------+
| data:10|  --> | data:20|  --> | data:30| --> NULL
| next:  |      | next:  |      | next:  |
+--------+      +--------+      +--------+
 at addr 0x100   at addr 0x500   at addr 0x240
```

Nodes can be **anywhere** in RAM. The `next` pointer is the chain.

### The Fundamental Trade-off

```
                 Array           Linked List
                 -----           -----------
Random Access:   O(1)            O(n)        ← Linked list loses
Insert/Delete:   O(n) shift      O(1)*       ← Linked list wins
Memory layout:   Contiguous      Scattered
Cache friendly:  YES             NO
Size fixed?:     Often yes       No (dynamic)

* O(1) only IF you already have the pointer to that node.
  Getting to that node is still O(n).
```

> **Key Insight:** A linked list is a *trade of random access for flexible insertion/deletion.*
> If your problem doesn't need middle insertions/deletions, an array is almost always better.

---

## 2. Memory Internals

### What a Node Actually Looks Like in RAM

Let's say we have this list: `10 -> 20 -> 30 -> NULL`

```
RAM (simplified view):

Address  | Content
---------|----------------------------------------------------------
0x1000   | [data: 10] [next: 0x2000]    <- Node A (head)
...
0x2000   | [data: 20] [next: 0x3500]    <- Node B
...
0x3500   | [data: 30] [next: 0x0000]    <- Node C (tail, next=NULL)
```

The **head** variable itself is just a pointer:

```
head = 0x1000   (a variable that holds the address of Node A)
```

When we say `head.next`, we:
1. Look at `head` → get address `0x1000`
2. Go to `0x1000` in RAM
3. Read the `next` field → get `0x2000`
4. Go to `0x2000` → that is Node B

This is called **pointer dereferencing** — following the arrow.

### ASCII Diagram Convention Used Throughout This Guide

```
+------+------+       +------+------+       +------+------+
| val  | next | ----> | val  | next | ----> | val  | next | ----> NULL
+------+------+       +------+------+       +------+------+
  head                                        tail

[HEAD] = variable storing pointer to first node
[NULL] = no next node (end of list)
```

For doubly linked:
```
NULL <-- +------+------+------+ <--> +------+------+------+ <--> +------+------+------+ --> NULL
         | prev | val  | next |      | prev | val  | next |      | prev | val  | next |
         +------+------+------+      +------+------+------+      +------+------+------+
           head                                                     tail
```

### Size in Memory

For a singly linked list node (64-bit system):
```
+------------------+------------------+
|   data (8 bytes) |  next (8 bytes)  |  = 16 bytes per node
+------------------+------------------+

Plus heap allocation overhead (malloc header ~8-16 bytes on most allocators)

So each "logical" node = 24-32 bytes in practice
vs array element = exactly sizeof(T)
```

This is why linked lists have **poor cache performance**: loading Node A into CPU cache
does NOT help load Node B — it's elsewhere in RAM.

---

## 3. Types of Linked Lists

### 3.1 Singly Linked List

```
+---+----+    +---+----+    +---+----+    +---+------+
| 1 | *--+--> | 2 | *--+--> | 3 | *--+--> | 4 | NULL |
+---+----+    +---+----+    +---+----+    +---+------+
  HEAD

- Each node has ONE pointer: next
- Can only traverse FORWARD
- Cannot go back without re-traversal from head
```

### 3.2 Doubly Linked List

```
         +------+---+----+    +----+---+------+    +----+---+------+
NULL <---+ NULL | 1 | *--+--> +--* | 2 | *----+--> +--* | 3 | NULL |
         +------+---+----+    +----+---+------+    +----+---+------+
           HEAD                                       TAIL

- Each node has TWO pointers: prev and next
- Can traverse both FORWARD and BACKWARD
- Deletion is O(1) if you have the node (no need to find previous node)
- Costs twice the pointer memory
```

### 3.3 Circular Singly Linked List

```
    +---+----+    +---+----+    +---+----+
--> | 1 | *--+--> | 2 | *--+--> | 3 | *--+---+
|   +---+----+    +---+----+    +---+----+   |
|                                             |
+---------------------------------------------+

- Tail's next points back to HEAD (not NULL)
- No NULL terminator
- Useful for: round-robin scheduling, circular buffers
- DANGER: Naive traversal loops forever
```

### 3.4 Circular Doubly Linked List

```
    +------+---+----+    +----+---+------+    +----+---+------+
+---+--* | 1 | *----+--> +--* | 2 | *----+--> +--* | 3 | *--+-+-+
|   +------+---+----+    +----+---+------+    +----+---+------+ | |
|                                                                 | |
+-----------------------------------------------------------------+ |
+-------------------------------------------------------------------+

- Both ends connect circularly
- Used in: OS process scheduling (Linux CFS), deques
```

### 3.5 Multilevel / Unrolled / Skip List (Advanced)

```
Multilevel (used in flatten problem):
Node has: val, next, child
child points to another sublist

Level 1: 1 -> 2 -> 3 -> 4 -> NULL
              |
Level 2:      5 -> 6 -> NULL
                   |
Level 3:           7 -> NULL
```

---

## 4. Node Structure

### Terminology to Know First

- **Node**: A container holding data + pointer(s) to neighbor(s)
- **Head**: Pointer/reference to the first node
- **Tail**: Pointer/reference to the last node
- **NULL / nil / None**: Represents "no node here" — the absence of a pointer
- **Pointer**: In C, a raw memory address. In Rust, a `Box<T>` or raw ptr. In Go, `*Node`.
- **Heap allocation**: `malloc` in C, `Box::new()` in Rust, `new(Node)` in Go — puts node in heap memory

---

### 4.1 C Implementation

```c
/* ============================================================
   SINGLY LINKED LIST — C
   ============================================================ */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

/* Node definition */
typedef struct Node {
    int data;           /* the value stored */
    struct Node *next;  /* pointer to next node, NULL if last */
} Node;

/* List wrapper (optional but good practice) */
typedef struct {
    Node *head;
    Node *tail;
    size_t length;
} LinkedList;

/* Create a new node on the heap */
Node *node_create(int data) {
    Node *n = (Node *)malloc(sizeof(Node));
    if (!n) {
        fprintf(stderr, "malloc failed\n");
        exit(EXIT_FAILURE);
    }
    n->data = data;
    n->next = NULL;
    return n;
}

void list_init(LinkedList *list) {
    list->head = NULL;
    list->tail = NULL;
    list->length = 0;
}

/* DOUBLY LINKED LIST NODE */
typedef struct DNode {
    int data;
    struct DNode *prev;
    struct DNode *next;
} DNode;
```

### 4.2 Rust Implementation

```rust
// ============================================================
// SINGLY LINKED LIST — Rust
// ============================================================
// Rust's ownership model makes linked lists famously tricky.
// The idiomatic approach uses Option<Box<T>> for ownership.
//
// Box<T>  = heap-allocated T, owned by exactly one owner
// Option  = Some(value) or None (replaces NULL)

#[derive(Debug)]
pub struct Node {
    pub data: i32,
    pub next: Option<Box<Node>>,
}

impl Node {
    pub fn new(data: i32) -> Self {
        Node { data, next: None }
    }
}

// The list itself just holds the head
#[derive(Debug)]
pub struct LinkedList {
    head: Option<Box<Node>>,
    length: usize,
}

impl LinkedList {
    pub fn new() -> Self {
        LinkedList { head: None, length: 0 }
    }
}

// ---- WHY Option<Box<Node>> and not just *mut Node? ----
//
// Raw pointers (*mut Node) bypass Rust's safety guarantees.
// Option<Box<Node>> means:
//   - None  = NULL (no next node)
//   - Some(box_node) = owned pointer to next node
//   - Box ensures: exactly one owner, automatic deallocation
//
// For competitive programming or interview practice, you often
// see people use Rc<RefCell<Node>> for shared ownership or
// raw pointers for speed. We show the idiomatic way here.
//
// DOUBLY LINKED LIST in Rust requires Rc<RefCell<>>:

use std::rc::Rc;
use std::cell::RefCell;

type Link<T> = Option<Rc<RefCell<DNode<T>>>>;

#[derive(Debug)]
pub struct DNode<T> {
    pub data: T,
    pub prev: Link<T>,
    pub next: Link<T>,
}
```

### 4.3 Go Implementation

```go
// ============================================================
// SINGLY LINKED LIST — Go
// ============================================================
// Go uses nil (not NULL) to represent absence.
// Pointers are automatic (no manual malloc/free).
// Garbage collector handles memory.

package linkedlist

import "fmt"

// Node for singly linked list
type Node struct {
    Data int
    Next *Node  // nil if last node
}

// Node constructor
func NewNode(data int) *Node {
    return &Node{Data: data, Next: nil}
}

// LinkedList wrapper
type LinkedList struct {
    Head   *Node
    Tail   *Node
    Length int
}

func NewLinkedList() *LinkedList {
    return &LinkedList{}
}

// DNode for doubly linked list
type DNode struct {
    Data int
    Prev *DNode
    Next *DNode
}
```

---

## 5. All Operations — What You CAN Do

---

### 5.1 Traversal

**Concept:** Walk through every node from head to tail, visiting each once.

```
Traversal Flow:

  curr = head
     |
     v
  [is curr NULL?] --YES--> STOP
     |
     NO
     |
     v
  [visit/process curr.data]
     |
     v
  [curr = curr.next]
     |
     v
  (loop back to NULL check)
```

```
ASCII Walk:
  head
   |
   v
 [10|*]-->[20|*]-->[30|*]-->[40|NULL]
   ^        ^        ^        ^
 curr=10  curr=20  curr=30  curr=40 → next=NULL → stop
```

**C:**
```c
void list_traverse(Node *head) {
    Node *curr = head;
    while (curr != NULL) {
        printf("%d -> ", curr->data);
        curr = curr->next;
    }
    printf("NULL\n");
}

/* Recursive traversal */
void list_traverse_recursive(Node *node) {
    if (node == NULL) return;
    printf("%d -> ", node->data);
    list_traverse_recursive(node->next);
}
```

**Rust:**
```rust
impl LinkedList {
    pub fn traverse(&self) {
        let mut curr = &self.head;
        while let Some(node) = curr {
            print!("{} -> ", node.data);
            curr = &node.next;
        }
        println!("None");
    }
}
```

**Go:**
```go
func (ll *LinkedList) Traverse() {
    curr := ll.Head
    for curr != nil {
        fmt.Printf("%d -> ", curr.Data)
        curr = curr.Next
    }
    fmt.Println("nil")
}
```

> **Complexity:** O(n) time, O(1) space (iterative), O(n) space (recursive — call stack).

---

### 5.2 Insertion

#### Three positions: HEAD · TAIL · MIDDLE (after a given node)

```
INSERTION AT HEAD:
------------------
Before: [20|*]-->[30|*]-->NULL    head=20

New node: [10|*]
Step 1: new->next = head           [10|*]-->[20|*]-->[30|*]-->NULL
Step 2: head = new                  ^head

After:  [10|*]-->[20|*]-->[30|*]-->NULL   head=10


INSERTION AT TAIL:
------------------
Before: [10|*]-->[20|*]-->[30|NULL]    tail=30

New node: [40|NULL]
Step 1: tail->next = new           [10|*]-->[20|*]-->[30|*]-->[40|NULL]
Step 2: tail = new                                              ^tail

After:  [10|*]-->[20|*]-->[30|*]-->[40|NULL]   tail=40


INSERTION IN MIDDLE (after node with value 20):
------------------------------------------------
Before: [10|*]-->[20|*]-->[30|*]-->NULL
                  ^
                 prev

New node: [25|NULL]
Step 1: new->next = prev->next     [25|*]-->[30|*]-->NULL
Step 2: prev->next = new           [20|*]-->[25|*]-->[30|*]-->NULL

After:  [10|*]-->[20|*]-->[25|*]-->[30|*]-->NULL

CRITICAL ORDER: Step 1 MUST happen before Step 2.
If you do Step 2 first, you LOSE the reference to [30|*].
```

**C:**
```c
/* Insert at head — O(1) */
void insert_head(LinkedList *list, int data) {
    Node *new_node = node_create(data);
    new_node->next = list->head;
    list->head = new_node;
    if (list->tail == NULL) {
        list->tail = new_node; /* first node is also tail */
    }
    list->length++;
}

/* Insert at tail — O(1) with tail pointer, O(n) without */
void insert_tail(LinkedList *list, int data) {
    Node *new_node = node_create(data);
    if (list->tail == NULL) {
        list->head = new_node;
        list->tail = new_node;
    } else {
        list->tail->next = new_node;
        list->tail = new_node;
    }
    list->length++;
}

/* Insert after a given node — O(1) given the node, O(n) to find it */
void insert_after(LinkedList *list, Node *prev, int data) {
    if (prev == NULL) return;
    Node *new_node = node_create(data);
    new_node->next = prev->next;
    prev->next = new_node;
    if (prev == list->tail) {
        list->tail = new_node;
    }
    list->length++;
}

/* Insert at position (0-indexed) */
void insert_at(LinkedList *list, int pos, int data) {
    if (pos < 0 || (size_t)pos > list->length) return;
    if (pos == 0) { insert_head(list, data); return; }
    Node *curr = list->head;
    for (int i = 0; i < pos - 1; i++) {
        curr = curr->next;
    }
    insert_after(list, curr, data);
}
```

**Rust:**
```rust
impl LinkedList {
    /* Insert at head — O(1) */
    pub fn push_front(&mut self, data: i32) {
        let mut new_node = Box::new(Node::new(data));
        // Take ownership of current head, link it as next
        new_node.next = self.head.take();
        self.head = Some(new_node);
        self.length += 1;
    }

    /* Insert at tail — O(n): must traverse to end */
    pub fn push_back(&mut self, data: i32) {
        let new_node = Box::new(Node::new(data));
        // Walk to the last node
        let mut curr = &mut self.head;
        loop {
            match curr {
                None => {
                    *curr = Some(new_node);
                    break;
                }
                Some(node) => {
                    curr = &mut node.next;
                }
            }
        }
        self.length += 1;
    }
}
// NOTE: For O(1) tail insertion in Rust, you need unsafe code
// or a different data structure (VecDeque, etc.)
```

**Go:**
```go
/* Insert at head — O(1) */
func (ll *LinkedList) PushFront(data int) {
    newNode := NewNode(data)
    newNode.Next = ll.Head
    ll.Head = newNode
    if ll.Tail == nil {
        ll.Tail = newNode
    }
    ll.Length++
}

/* Insert at tail — O(1) with tail pointer */
func (ll *LinkedList) PushBack(data int) {
    newNode := NewNode(data)
    if ll.Tail == nil {
        ll.Head = newNode
        ll.Tail = newNode
    } else {
        ll.Tail.Next = newNode
        ll.Tail = newNode
    }
    ll.Length++
}

/* Insert after a specific node — O(1) */
func (ll *LinkedList) InsertAfter(prev *Node, data int) {
    if prev == nil {
        return
    }
    newNode := NewNode(data)
    newNode.Next = prev.Next
    prev.Next = newNode
    if prev == ll.Tail {
        ll.Tail = newNode
    }
    ll.Length++
}
```

---

### 5.3 Deletion

```
DELETE HEAD:
------------
Before: [10|*]-->[20|*]-->[30|NULL]   head=10
Step 1: temp = head                   temp points to [10]
Step 2: head = head->next             head now points to [20]
Step 3: free(temp)                    [10] is freed
After:  [20|*]-->[30|NULL]   head=20


DELETE TAIL:
------------
Before: [10|*]-->[20|*]-->[30|NULL]   tail=30
Step 1: Traverse to second-to-last:   curr = [20]
Step 2: curr->next = NULL             break the link
Step 3: free(tail)                    [30] is freed
Step 4: tail = curr                   tail now = [20]

PROBLEM: Without tail, this is O(n). With doubly linked list, it's O(1).


DELETE MIDDLE (node with value 20):
------------------------------------
Before: [10|*]-->[20|*]-->[30|*]-->NULL
         ^prev    ^target   ^next_node

Step 1: Find prev (node before target): prev = [10]
Step 2: prev->next = target->next        [10|*]-->[30|*]-->NULL
Step 3: free(target)                     [20] is freed

After:  [10|*]-->[30|*]-->NULL

ALTERNATIVE — "Copy and Skip" trick (if you only have target pointer):
----------------------------------------------------------------------
target->data = target->next->data   (copy next node's data into target)
temp = target->next
target->next = temp->next           (skip the next node)
free(temp)

This effectively "deletes" the target by overwriting it with next's data.
ONLY works if target is NOT the tail.
```

**C:**
```c
/* Delete head — O(1) */
int delete_head(LinkedList *list) {
    if (list->head == NULL) return -1; /* or handle error */
    Node *temp = list->head;
    int val = temp->data;
    list->head = list->head->next;
    if (list->head == NULL) {
        list->tail = NULL; /* list is now empty */
    }
    free(temp);
    list->length--;
    return val;
}

/* Delete tail — O(n) for singly linked */
int delete_tail(LinkedList *list) {
    if (list->head == NULL) return -1;
    if (list->head == list->tail) { /* single node */
        int val = list->head->data;
        free(list->head);
        list->head = list->tail = NULL;
        list->length--;
        return val;
    }
    /* Find second-to-last */
    Node *curr = list->head;
    while (curr->next != list->tail) {
        curr = curr->next;
    }
    int val = list->tail->data;
    free(list->tail);
    list->tail = curr;
    list->tail->next = NULL;
    list->length--;
    return val;
}

/* Delete node by value — O(n) */
bool delete_by_value(LinkedList *list, int target) {
    if (list->head == NULL) return false;

    /* Special case: head is the target */
    if (list->head->data == target) {
        delete_head(list);
        return true;
    }

    /* Find the node before target */
    Node *prev = list->head;
    while (prev->next != NULL && prev->next->data != target) {
        prev = prev->next;
    }
    if (prev->next == NULL) return false; /* not found */

    Node *to_delete = prev->next;
    prev->next = to_delete->next;
    if (to_delete == list->tail) {
        list->tail = prev;
    }
    free(to_delete);
    list->length--;
    return true;
}

/* Delete by position (0-indexed) — O(n) */
int delete_at(LinkedList *list, int pos) {
    if (pos < 0 || (size_t)pos >= list->length) return -1;
    if (pos == 0) return delete_head(list);
    Node *curr = list->head;
    for (int i = 0; i < pos - 1; i++) {
        curr = curr->next;
    }
    Node *to_delete = curr->next;
    int val = to_delete->data;
    curr->next = to_delete->next;
    if (to_delete == list->tail) {
        list->tail = curr;
    }
    free(to_delete);
    list->length--;
    return val;
}
```

**Rust:**
```rust
impl LinkedList {
    /* Pop from front — O(1) */
    pub fn pop_front(&mut self) -> Option<i32> {
        self.head.take().map(|node| {
            self.head = node.next;
            self.length -= 1;
            node.data
        })
    }

    /* Remove by value — O(n) */
    pub fn remove(&mut self, target: i32) -> bool {
        // Use a mutable reference to walk down "slots" (Option<Box<Node>>)
        let mut curr = &mut self.head;
        loop {
            match curr {
                None => return false,
                Some(node) if node.data == target => {
                    *curr = node.next.take();
                    self.length -= 1;
                    return true;
                }
                Some(node) => {
                    curr = &mut node.next;
                }
            }
        }
    }
}
```

**Go:**
```go
/* Pop from front — O(1) */
func (ll *LinkedList) PopFront() (int, bool) {
    if ll.Head == nil {
        return 0, false
    }
    val := ll.Head.Data
    ll.Head = ll.Head.Next
    if ll.Head == nil {
        ll.Tail = nil
    }
    ll.Length--
    return val, true
}

/* Delete by value — O(n) */
func (ll *LinkedList) DeleteByValue(target int) bool {
    if ll.Head == nil {
        return false
    }
    if ll.Head.Data == target {
        ll.PopFront()
        return true
    }
    prev := ll.Head
    for prev.Next != nil {
        if prev.Next.Data == target {
            if prev.Next == ll.Tail {
                ll.Tail = prev
            }
            prev.Next = prev.Next.Next
            ll.Length--
            return true
        }
        prev = prev.Next
    }
    return false
}
```

---

### 5.4 Search

```
Search Flow:

  curr = head, pos = 0
       |
       v
  [curr == NULL?] --YES--> return NOT FOUND
       |
       NO
       |
       v
  [curr.data == target?] --YES--> return curr (or pos)
       |
       NO
       |
       v
  curr = curr.next
  pos++
       |
       v
  (loop back)
```

**C:**
```c
/* Search by value — returns pointer to node or NULL */
Node *search(Node *head, int target) {
    Node *curr = head;
    while (curr != NULL) {
        if (curr->data == target) return curr;
        curr = curr->next;
    }
    return NULL;
}

/* Search and return index (0-based), -1 if not found */
int search_index(Node *head, int target) {
    int idx = 0;
    while (head != NULL) {
        if (head->data == target) return idx;
        head = head->next;
        idx++;
    }
    return -1;
}
```

**Go:**
```go
func (ll *LinkedList) Search(target int) (*Node, int) {
    curr := ll.Head
    idx := 0
    for curr != nil {
        if curr.Data == target {
            return curr, idx
        }
        curr = curr.Next
        idx++
    }
    return nil, -1
}
```

> **Complexity:** O(n) time. No way around it — no indexing, no binary search possible
> (unless you maintain sorted order AND use skip list or augmented structure).

---

### 5.5 Reversal

This is one of the most important operations. Master it deeply.

```
ITERATIVE REVERSAL:
-------------------
Before: head -> [1|*] -> [2|*] -> [3|*] -> [4|NULL]

We need three pointers:
  prev = NULL  (the new "tail" connector)
  curr = head  (current node being processed)
  next = NULL  (saves next before we break the link)

Step 0: prev=NULL, curr=[1], next=?
        [NULL] <- [1] -> [2] -> [3] -> [4|NULL]

Step 1: next = curr->next = [2]
        curr->next = prev = NULL
        prev = curr = [1]
        curr = next = [2]
        State: NULL<-[1]  [2]->[3]->[4]

Step 2: next = curr->next = [3]
        curr->next = prev = [1]
        prev = curr = [2]
        curr = next = [3]
        State: NULL<-[1]<-[2]  [3]->[4]

Step 3: next = curr->next = [4]
        curr->next = prev = [2]
        prev = curr = [3]
        curr = next = [4]
        State: NULL<-[1]<-[2]<-[3]  [4]

Step 4: next = curr->next = NULL
        curr->next = prev = [3]
        prev = curr = [4]
        curr = next = NULL
        State: NULL<-[1]<-[2]<-[3]<-[4]

Loop ends (curr == NULL).
new head = prev = [4]

After: head -> [4|*] -> [3|*] -> [2|*] -> [1|NULL]
```

```
RECURSIVE REVERSAL:
-------------------
Call stack visualization for [1]->[2]->[3]->[4]->NULL

reverse(1) calls reverse(2)
  reverse(2) calls reverse(3)
    reverse(3) calls reverse(4)
      reverse(4) calls reverse(NULL) -- BASE CASE, return [4]
      [4].next.next = [4]  (i.e., [3]->next = [4]... wait no)
      Actually: head=[3], head->next=[4]
      head->next->next = head means [4]->next = [3]
      head->next = NULL
      return [4] as new_head

Unwinding:
  At [3]: [4]->next=[3], [3]->next=NULL    result: [4]->[3]->NULL
  At [2]: [3]->next=[2], [2]->next=NULL    result: [4]->[3]->[2]->NULL
  At [1]: [2]->next=[1], [1]->next=NULL    result: [4]->[3]->[2]->[1]->NULL
```

**C:**
```c
/* Iterative reverse — O(n) time, O(1) space */
Node *reverse_iterative(Node *head) {
    Node *prev = NULL;
    Node *curr = head;
    while (curr != NULL) {
        Node *next = curr->next;  /* SAVE next before breaking link */
        curr->next = prev;        /* reverse the link */
        prev = curr;              /* move prev forward */
        curr = next;              /* move curr forward */
    }
    return prev; /* prev is the new head */
}

/* Recursive reverse — O(n) time, O(n) space (call stack) */
Node *reverse_recursive(Node *head) {
    if (head == NULL || head->next == NULL) {
        return head; /* base case: empty or single node */
    }
    Node *new_head = reverse_recursive(head->next);
    head->next->next = head;  /* node after head now points back */
    head->next = NULL;        /* head becomes the tail */
    return new_head;
}
```

**Rust:**
```rust
impl LinkedList {
    /* Iterative reverse — O(n) time, O(1) extra space */
    pub fn reverse(&mut self) {
        let mut prev: Option<Box<Node>> = None;
        let mut curr = self.head.take();
        while let Some(mut node) = curr {
            let next = node.next.take();
            node.next = prev;
            prev = Some(node);
            curr = next;
        }
        self.head = prev;
    }
}
```

**Go:**
```go
/* Iterative reverse — O(n) time, O(1) space */
func (ll *LinkedList) Reverse() {
    var prev *Node
    curr := ll.Head
    ll.Tail = ll.Head // old head becomes new tail
    for curr != nil {
        next := curr.Next
        curr.Next = prev
        prev = curr
        curr = next
    }
    ll.Head = prev
}
```

---

### 5.6 Find the Middle — Floyd's Tortoise & Hare

**Concept — What is Floyd's Algorithm?**

Named after computer scientist Robert Floyd. The idea: use two pointers moving at different speeds.
- **Slow pointer** (tortoise): moves 1 step at a time
- **Fast pointer** (hare): moves 2 steps at a time

When fast reaches the end, slow is at the middle.

```
WHY IT WORKS (mathematical intuition):
If list has n nodes:
  fast moves n steps total
  slow moves n/2 steps total
  When fast is at end, slow is at n/2 = middle

For n=5: [1]->[2]->[3]->[4]->[5]->NULL

Step 0: slow=[1], fast=[1]
Step 1: slow=[2], fast=[3]    (slow+1, fast+2)
Step 2: slow=[3], fast=[5]    (slow+1, fast+2)
Step 3: fast->next = NULL → STOP
        slow = [3] = MIDDLE ✓

For n=6: [1]->[2]->[3]->[4]->[5]->[6]->NULL
Step 0: slow=[1], fast=[1]
Step 1: slow=[2], fast=[3]
Step 2: slow=[3], fast=[5]
Step 3: slow=[4], fast=NULL (fast moved to 6, then next=NULL) → STOP
        slow = [4] = SECOND middle (upper middle)

Note: For even-length lists, there are TWO middles.
Convention: slow lands on the SECOND middle with standard code.
Adjust condition to get first middle.
```

**C:**
```c
/* Find middle node — O(n) time, O(1) space */
Node *find_middle(Node *head) {
    if (head == NULL) return NULL;
    Node *slow = head;
    Node *fast = head;
    while (fast != NULL && fast->next != NULL) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}

/* For even n: returns FIRST middle (lower middle) */
Node *find_middle_lower(Node *head) {
    if (head == NULL) return NULL;
    Node *slow = head;
    Node *fast = head->next; /* fast starts one ahead */
    while (fast != NULL && fast->next != NULL) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}
```

**Go:**
```go
func (ll *LinkedList) FindMiddle() *Node {
    if ll.Head == nil {
        return nil
    }
    slow := ll.Head
    fast := ll.Head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    return slow
}
```

---

### 5.7 Cycle Detection & Removal

**What is a Cycle?**

A cycle (loop) in a linked list means some node's `next` pointer points back to a
*previous* node in the list, creating an infinite loop.

```
LIST WITH CYCLE:

[1]-->[2]-->[3]-->[4]-->[5]
              ^           |
              |           |
              +-----------+
              (5's next points back to 3)

Naive traversal NEVER terminates — it loops: 3->4->5->3->4->5->...
```

**Detection: Floyd's Cycle Detection**

```
PHASE 1: DETECTION
-------------------
Use slow (1 step) and fast (2 steps).
If they MEET, there is a cycle.
If fast reaches NULL, there is no cycle.

WHY THEY MEET (intuition):
Imagine a circular track. A fast runner and slow runner.
Eventually the fast runner "laps" the slow runner — they meet.

[1]-->[2]-->[3]-->[4]-->[5]
              ^           |
              +-----------+

Step 0: slow=1, fast=1
Step 1: slow=2, fast=3
Step 2: slow=3, fast=5
Step 3: slow=4, fast=4   ← THEY MEET at node [4]

Cycle detected!

PHASE 2: FIND CYCLE START
--------------------------
Mathematical result: After detection, place one pointer at HEAD,
keep the other at the meeting point.
Move BOTH one step at a time.
Where they meet = start of cycle.

Proof sketch:
Let:
  F = distance from head to cycle start
  C = cycle length
  K = distance from cycle start to meeting point

When they meet:
  slow has traveled: F + K
  fast has traveled: F + K + m*C (went around m times extra)
  fast = 2 * slow:
  F + K + m*C = 2(F + K)
  m*C = F + K
  F = m*C - K

So: starting one ptr at head (distance F to cycle start)
    and another at meeting point (distance m*C - K to cycle start)
    they travel the same distance F to meet at cycle start. ✓
```

**C:**
```c
/* Detect cycle — returns meeting node or NULL */
Node *detect_cycle(Node *head) {
    Node *slow = head;
    Node *fast = head;
    while (fast != NULL && fast->next != NULL) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return slow; /* cycle detected */
    }
    return NULL;
}

/* Find start of cycle — O(n) time, O(1) space */
Node *find_cycle_start(Node *head) {
    Node *meeting = detect_cycle(head);
    if (meeting == NULL) return NULL; /* no cycle */
    Node *ptr1 = head;
    Node *ptr2 = meeting;
    while (ptr1 != ptr2) {
        ptr1 = ptr1->next;
        ptr2 = ptr2->next;
    }
    return ptr1; /* cycle start */
}

/* Remove cycle — O(n) */
void remove_cycle(Node *head) {
    Node *cycle_start = find_cycle_start(head);
    if (cycle_start == NULL) return;
    /* Find the node just before cycle_start (the tail of the cycle) */
    Node *curr = cycle_start;
    while (curr->next != cycle_start) {
        curr = curr->next;
    }
    curr->next = NULL; /* break the cycle */
}
```

**Go:**
```go
func DetectCycle(head *Node) *Node {
    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
        if slow == fast {
            return slow
        }
    }
    return nil
}

func FindCycleStart(head *Node) *Node {
    meeting := DetectCycle(head)
    if meeting == nil {
        return nil
    }
    ptr1 := head
    ptr2 := meeting
    for ptr1 != ptr2 {
        ptr1 = ptr1.Next
        ptr2 = ptr2.Next
    }
    return ptr1
}
```

---

### 5.8 Merge Two Sorted Lists

**Concept:**

Given two sorted lists, produce one sorted merged list WITHOUT extra memory allocation
(reuse existing nodes by relinking pointers).

```
List A: [1]-->[3]-->[5]-->NULL
List B: [2]-->[4]-->[6]-->NULL

MERGE PROCESS (compare heads, pick smaller):

Step 1: compare 1 vs 2 → pick 1
  merged: [1]-->...   advance A's pointer
  A points to [3], B still at [2]

Step 2: compare 3 vs 2 → pick 2
  merged: [1]-->[2]-->...   advance B
  A at [3], B at [4]

Step 3: compare 3 vs 4 → pick 3
  merged: [1]-->[2]-->[3]-->...   advance A
  A at [5], B at [4]

Step 4: compare 5 vs 4 → pick 4
  merged: [1]-->[2]-->[3]-->[4]-->...   advance B
  A at [5], B at [6]

Step 5: compare 5 vs 6 → pick 5
  merged: [1]-->[2]-->[3]-->[4]-->[5]-->...   advance A
  A = NULL, B at [6]

Step 6: A is NULL → attach remaining B
  merged: [1]-->[2]-->[3]-->[4]-->[5]-->[6]-->NULL

DUMMY HEAD TRICK: Use a sentinel/dummy node to avoid special-casing
the first element. Always append to dummy->next.
```

**C:**
```c
/* Merge two sorted lists — O(n+m) time, O(1) space */
Node *merge_sorted(Node *a, Node *b) {
    /* Dummy head trick — avoids special cases */
    Node dummy;
    dummy.next = NULL;
    Node *tail = &dummy;

    while (a != NULL && b != NULL) {
        if (a->data <= b->data) {
            tail->next = a;
            a = a->next;
        } else {
            tail->next = b;
            b = b->next;
        }
        tail = tail->next;
    }
    /* Attach remaining list */
    tail->next = (a != NULL) ? a : b;
    return dummy.next;
}

/* Recursive version — O(n+m) time, O(n+m) call stack */
Node *merge_sorted_recursive(Node *a, Node *b) {
    if (a == NULL) return b;
    if (b == NULL) return a;
    if (a->data <= b->data) {
        a->next = merge_sorted_recursive(a->next, b);
        return a;
    } else {
        b->next = merge_sorted_recursive(a, b->next);
        return b;
    }
}
```

**Rust:**
```rust
fn merge_sorted(a: Option<Box<Node>>, b: Option<Box<Node>>) -> Option<Box<Node>> {
    match (a, b) {
        (None, b) => b,
        (a, None) => a,
        (Some(mut a_node), Some(mut b_node)) => {
            if a_node.data <= b_node.data {
                a_node.next = merge_sorted(a_node.next.take(), Some(b_node));
                Some(a_node)
            } else {
                b_node.next = merge_sorted(Some(a_node), b_node.next.take());
                Some(b_node)
            }
        }
    }
}
```

**Go:**
```go
func MergeSorted(a, b *Node) *Node {
    dummy := &Node{}
    tail := dummy
    for a != nil && b != nil {
        if a.Data <= b.Data {
            tail.Next = a
            a = a.Next
        } else {
            tail.Next = b
            b = b.Next
        }
        tail = tail.Next
    }
    if a != nil {
        tail.Next = a
    } else {
        tail.Next = b
    }
    return dummy.Next
}
```

---

### 5.9 Sort a Linked List — Merge Sort

**Why Merge Sort (not Quick Sort or Bubble Sort)?**

```
Sorting Algorithm Comparison for Linked Lists:

Bubble Sort:   O(n²) — bad, avoid
Quick Sort:    O(n log n) avg, O(n²) worst — random access for pivot selection is O(n)
Insertion Sort: O(n²) — ok for small/nearly-sorted lists
Merge Sort:    O(n log n) GUARANTEED, O(log n) space — BEST for linked lists

Merge Sort is natural for linked lists because:
1. Splitting at middle is O(n) with slow/fast pointer
2. Merging is O(n) with pointer relinking (no extra array)
3. No random access needed
```

```
MERGE SORT FLOW:

sort([3,1,4,1,5,9,2,6]):
         |
  split at middle
  /              \
sort([3,1,4,1])   sort([5,9,2,6])
  /      \          /       \
[3,1]  [4,1]     [5,9]    [2,6]
  |       |        |         |
[1,3]  [1,4]     [5,9]    [2,6]
  \       /        \         /
  merge([1,3],[1,4]) merge([5,9],[2,6])
       [1,1,3,4]         [2,5,6,9]
             \           /
           merge(...)
           [1,1,2,3,4,5,6,9]
```

**C:**
```c
/* Sort linked list using merge sort — O(n log n), O(log n) */
Node *merge_sort(Node *head) {
    /* Base case: 0 or 1 node */
    if (head == NULL || head->next == NULL) return head;

    /* Split into two halves */
    Node *mid = find_middle_lower(head); /* use lower-middle version */
    Node *second_half = mid->next;
    mid->next = NULL; /* CUT the list */

    /* Recursively sort both halves */
    Node *left = merge_sort(head);
    Node *right = merge_sort(second_half);

    /* Merge and return */
    return merge_sorted(left, right);
}
```

**Go:**
```go
func MergeSort(head *Node) *Node {
    if head == nil || head.Next == nil {
        return head
    }
    // Split
    slow, fast := head, head.Next
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    mid := slow.Next
    slow.Next = nil // cut
    // Recurse
    left := MergeSort(head)
    right := MergeSort(mid)
    return MergeSorted(left, right)
}
```

---

### 5.10 Rotate a List

**Concept:** Rotating by `k` means moving the last `k` nodes to the front.

```
Rotate [1]->[2]->[3]->[4]->[5] by k=2:

After rotation: [4]->[5]->[1]->[2]->[3]

Algorithm:
1. Find length n
2. k = k % n (handle k > n)
3. New tail is at position (n - k - 1)
4. New head is at position (n - k)
5. Connect: old_tail->next = old_head, new_tail->next = NULL

Step by step:
n=5, k=2
new_tail position = 5 - 2 - 1 = 2 (0-indexed) → node [3]
new_head = node [4]

[1]->[2]->[3]->[4]->[5]->NULL
             ^new_tail  ^old_tail

old_tail->next = old_head:
[1]->[2]->[3]->[4]->[5]->[1]->... (now circular)

new_tail->next = NULL:
[4]->[5]->[1]->[2]->[3]->NULL  ✓
```

**C:**
```c
Node *rotate_right(Node *head, int k) {
    if (head == NULL || head->next == NULL || k == 0) return head;

    /* Find length and tail */
    int n = 1;
    Node *tail = head;
    while (tail->next != NULL) {
        tail = tail->next;
        n++;
    }

    k = k % n;
    if (k == 0) return head;

    /* Find new tail: (n - k - 1) steps from head */
    Node *new_tail = head;
    for (int i = 0; i < n - k - 1; i++) {
        new_tail = new_tail->next;
    }

    Node *new_head = new_tail->next;
    new_tail->next = NULL;
    tail->next = head;
    return new_head;
}
```

---

### 5.11 Find Intersection of Two Lists

**Concept — What is "intersection"?**

Two lists "intersect" when they share the same node (same memory address, not just same value)
from some point onward. Like two rivers merging into one.

```
List A: [1]->[3]->[5]
                     \
                      [8]->[10]->NULL   (shared nodes)
                     /
List B: [2]->[4]
```

**Algorithm — Two Pointer Equalization:**

```
Key insight: If we make both pointers travel the SAME total distance,
they will meet at the intersection.

Total distance = len(A) + len(B) [for pointer starting on A then B]
              = len(B) + len(A) [for pointer starting on B then A]

Both pointers travel same total → if intersection exists, they meet there.
If no intersection → both reach NULL at same time.

len(A) = 5, len(B) = 3, shared = 2
ptr1 traverses: A(5) then B(3) = 8 steps
ptr2 traverses: B(3) then A(5) = 8 steps
They meet at intersection after len(A)+len(B)-shared steps.
```

**C:**
```c
Node *find_intersection(Node *headA, Node *headB) {
    if (headA == NULL || headB == NULL) return NULL;
    Node *a = headA;
    Node *b = headB;
    /* When a pointer reaches NULL, redirect it to the OTHER list's head */
    while (a != b) {
        a = (a == NULL) ? headB : a->next;
        b = (b == NULL) ? headA : b->next;
    }
    return a; /* NULL if no intersection */
}
```

**Go:**
```go
func FindIntersection(headA, headB *Node) *Node {
    a, b := headA, headB
    for a != b {
        if a == nil {
            a = headB
        } else {
            a = a.Next
        }
        if b == nil {
            b = headA
        } else {
            b = b.Next
        }
    }
    return a
}
```

---

### 5.12 Palindrome Check

**Concept:** A list is a palindrome if it reads the same forwards and backwards.
Example: `[1]->[2]->[3]->[2]->[1]` is a palindrome.

**Algorithm — O(n) time, O(1) space:**

```
Step 1: Find middle using slow/fast pointers
Step 2: Reverse the second half
Step 3: Compare first half with reversed second half
Step 4: (Optionally restore the list)

[1]->[2]->[3]->[2]->[1]->NULL

After step 1: mid = [3]
After step 2: second half reversed = [1]->[2]->[3]
              first half: [1]->[2]->[3]

Compare: 1==1, 2==2, 3==3 → PALINDROME ✓
```

**C:**
```c
bool is_palindrome(Node *head) {
    if (head == NULL || head->next == NULL) return true;

    /* Find middle */
    Node *slow = head, *fast = head;
    while (fast->next != NULL && fast->next->next != NULL) {
        slow = slow->next;
        fast = fast->next->next;
    }

    /* Reverse second half */
    Node *second_half = reverse_iterative(slow->next);
    Node *p1 = head;
    Node *p2 = second_half;

    bool result = true;
    while (p2 != NULL) {
        if (p1->data != p2->data) {
            result = false;
            break;
        }
        p1 = p1->next;
        p2 = p2->next;
    }

    /* Restore the list (good practice) */
    slow->next = reverse_iterative(second_half);
    return result;
}
```

---

### 5.13 Remove Nth Node from End

```
Remove 2nd from end of [1]->[2]->[3]->[4]->[5]:
Answer: [1]->[2]->[3]->[5]

TWO POINTER TRICK:
Move fast pointer n steps ahead.
Then move both slow and fast together.
When fast reaches NULL, slow is at the node BEFORE the target.

n=2:
Step 0: dummy->[1]->[2]->[3]->[4]->[5]->NULL
        slow=dummy, fast=dummy

Step 1 (advance fast n=2 steps):
        slow=dummy, fast=[2]

Step 2 (move both until fast=NULL):
        slow=[1], fast=[3]
        slow=[2], fast=[4]
        slow=[3], fast=[5]
        slow=[4], fast=NULL  ← STOP
Wait, let me redo: advance fast n+1 steps from dummy to make it cleaner:
        fast starts at dummy, move n+1 steps:
        fast = [3] (after 3 steps: dummy→[1]→[2]→[3])
        wait — different implementations vary.

CLEAN VERSION: Move fast (n+1) steps first from dummy node:
After n+1 steps: fast=[3], slow=dummy
Move both: slow=[1], fast=[4]
           slow=[2], fast=[5]
           slow=[3], fast=NULL
slow->next is [4] (the target)
slow->next = slow->next->next  → deletes [4]

Result: [1]->[2]->[3]->[5]->NULL ✓
```

**C:**
```c
Node *remove_nth_from_end(Node *head, int n) {
    /* Use dummy node to handle edge case of removing head */
    Node dummy;
    dummy.next = head;
    dummy.data = 0;

    Node *fast = &dummy;
    Node *slow = &dummy;

    /* Move fast n+1 steps ahead */
    for (int i = 0; i <= n; i++) {
        if (fast == NULL) return head; /* n > length, invalid */
        fast = fast->next;
    }

    /* Move both until fast is NULL */
    while (fast != NULL) {
        slow = slow->next;
        fast = fast->next;
    }

    /* slow->next is the node to delete */
    Node *to_delete = slow->next;
    slow->next = to_delete->next;
    free(to_delete);

    return dummy.next;
}
```

**Go:**
```go
func RemoveNthFromEnd(head *Node, n int) *Node {
    dummy := &Node{Next: head}
    fast, slow := dummy, dummy
    for i := 0; i <= n; i++ {
        if fast == nil {
            return head
        }
        fast = fast.Next
    }
    for fast != nil {
        slow = slow.Next
        fast = fast.Next
    }
    slow.Next = slow.Next.Next
    return dummy.Next
}
```

---

### 5.14 Flatten a Multilevel Doubly Linked List

**Concept:** A multilevel list has nodes with both `next` and `child` pointers.
Flatten means: convert it into a single-level list where child lists are
inserted after their parent node.

```
Input:
1 --> 2 --> 3 --> 4 --> NULL
           |
           5 --> 6 --> NULL
                 |
                 7 --> NULL

Output (DFS order):
1 --> 2 --> 3 --> 5 --> 7 --> 6 --> 4 --> NULL

Algorithm (iterative with stack):
Use a stack. When we see a child, push next onto stack and follow child.
When current->next is NULL and stack non-empty, pop and continue.

Or simpler: For each node with a child:
  1. Save node->next as next_node
  2. Connect node->next = node->child
  3. Find tail of child sublist
  4. tail->next = next_node
  5. node->child = NULL
```

**C:**
```c
typedef struct MLNode {
    int val;
    struct MLNode *prev;
    struct MLNode *next;
    struct MLNode *child;
} MLNode;

MLNode *flatten(MLNode *head) {
    MLNode *curr = head;
    while (curr != NULL) {
        if (curr->child != NULL) {
            MLNode *child = curr->child;
            MLNode *next = curr->next;

            /* Insert child list */
            curr->next = child;
            child->prev = curr;
            curr->child = NULL;

            /* Find tail of child list */
            MLNode *tail = child;
            while (tail->next != NULL) tail = tail->next;

            /* Connect tail to saved next */
            tail->next = next;
            if (next != NULL) next->prev = tail;
        }
        curr = curr->next;
    }
    return head;
}
```

---

### 5.15 Clone a List with Random Pointers

**Concept — What is a Random Pointer?**

Each node has: `data`, `next`, and `random` (points to any arbitrary node in the list, or NULL).
Cloning naively is hard because when you create node copies, the `random` pointers
of copies need to point to the *correct copies*, not the originals.

```
Algorithm using interweaving (O(n) time, O(1) space):

Phase 1: Weave copies between originals
Original: [1]->[2]->[3]->NULL
After:    [1]->[1']->[2]->[2']->[3]->[3']->NULL

Phase 2: Set random pointers for copies
copy.random = original.random.next  (the copy of original's random)

Phase 3: Separate the two lists
```

**C:**
```c
typedef struct RNode {
    int data;
    struct RNode *next;
    struct RNode *random;
} RNode;

RNode *clone_list(RNode *head) {
    if (head == NULL) return NULL;

    /* Phase 1: Insert copies */
    RNode *curr = head;
    while (curr != NULL) {
        RNode *copy = (RNode *)malloc(sizeof(RNode));
        copy->data = curr->data;
        copy->random = NULL;
        copy->next = curr->next;
        curr->next = copy;
        curr = copy->next;
    }

    /* Phase 2: Set random pointers */
    curr = head;
    while (curr != NULL) {
        if (curr->random != NULL) {
            curr->next->random = curr->random->next;
        }
        curr = curr->next->next;
    }

    /* Phase 3: Separate lists */
    RNode dummy;
    dummy.next = NULL;
    RNode *tail = &dummy;
    curr = head;
    while (curr != NULL) {
        RNode *copy = curr->next;
        curr->next = copy->next;
        tail->next = copy;
        tail = copy;
        curr = curr->next;
    }
    return dummy.next;
}
```

---

### 5.16 Partition / Reorder

**Partition (Leetcode 86 style):** Rearrange so all nodes less than x come before nodes >= x,
preserving relative order.

```
Input:  [3]->[1]->[5]->[4]->[2]->[6], x=3
Output: [1]->[2]->[3]->[5]->[4]->[6]

Algorithm: Two lists — "less" and "greater_equal"
Iterate: if node.val < x → append to "less"
         else            → append to "greater_equal"
Connect: less_tail->next = greater_head

less:     dummy1->[1]->[2]
greater:  dummy2->[3]->[5]->[4]->[6]
Connect:  [1]->[2]->[3]->[5]->[4]->[6]->NULL ✓
```

**C:**
```c
Node *partition(Node *head, int x) {
    Node less_dummy, greater_dummy;
    less_dummy.next = NULL;
    greater_dummy.next = NULL;
    Node *less_tail = &less_dummy;
    Node *greater_tail = &greater_dummy;

    Node *curr = head;
    while (curr != NULL) {
        if (curr->data < x) {
            less_tail->next = curr;
            less_tail = curr;
        } else {
            greater_tail->next = curr;
            greater_tail = curr;
        }
        curr = curr->next;
    }
    greater_tail->next = NULL;
    less_tail->next = greater_dummy.next;
    return less_dummy.next;
}
```

---

### 5.17 Doubly Linked List Operations

```
DOUBLY LINKED LIST INTERNALS:

NULL <--[prev|1|next]--> <--[prev|2|next]--> <--[prev|3|next]--> NULL
         ^head                                       ^tail

Insert node X after node B:
Before: A <--> B <--> C
After:  A <--> B <--> X <--> C

Steps:
1. X->prev = B
2. X->next = B->next (= C)
3. B->next->prev = X  (C->prev = X)  [DO THIS BEFORE STEP 4]
4. B->next = X

Delete node B (where A <--> B <--> C):
1. B->prev->next = B->next  (A->next = C)
2. B->next->prev = B->prev  (C->prev = A)
3. free(B)
This is O(1) if you have the node! No need to find predecessor.
```

**C:**
```c
/* Doubly linked list insert after — O(1) */
void dl_insert_after(DNode **head, DNode **tail, DNode *prev, int data) {
    DNode *new_node = (DNode *)malloc(sizeof(DNode));
    new_node->data = data;

    if (prev == NULL) { /* insert at head */
        new_node->prev = NULL;
        new_node->next = *head;
        if (*head) (*head)->prev = new_node;
        *head = new_node;
        if (*tail == NULL) *tail = new_node;
        return;
    }

    new_node->next = prev->next;
    new_node->prev = prev;
    if (prev->next != NULL) {
        prev->next->prev = new_node;
    } else {
        *tail = new_node; /* new node is new tail */
    }
    prev->next = new_node;
}

/* Doubly linked list delete — O(1) given the node */
void dl_delete(DNode **head, DNode **tail, DNode *node) {
    if (node->prev != NULL) {
        node->prev->next = node->next;
    } else {
        *head = node->next; /* deleting head */
    }
    if (node->next != NULL) {
        node->next->prev = node->prev;
    } else {
        *tail = node->prev; /* deleting tail */
    }
    free(node);
}
```

---

### 5.18 Circular Linked List Operations

```
CIRCULAR LIST — key rules:
1. Tail->next = HEAD (not NULL)
2. Traversal: stop when you return to head (use do-while or flag)
3. Never check for NULL as termination — check for head

INSERT AT HEAD (circular):
Before: tail -> [1] -> [2] -> [3] -> (back to [1])
New node: [0]
1. new->next = head
2. tail->next = new
3. head = new

INSERT AT TAIL (circular):
1. new->next = head
2. tail->next = new
3. tail = new
```

**C:**
```c
typedef struct CNode {
    int data;
    struct CNode *next;
} CNode;

/* Insert at head of circular list */
CNode *circular_insert_head(CNode *tail, int data) {
    CNode *new_node = (CNode *)malloc(sizeof(CNode));
    new_node->data = data;
    if (tail == NULL) { /* empty list */
        new_node->next = new_node;
        return new_node; /* tail = new_node */
    }
    new_node->next = tail->next; /* new->next = head */
    tail->next = new_node;       /* tail->next = new head */
    return tail;
}

/* Insert at tail */
CNode *circular_insert_tail(CNode *tail, int data) {
    CNode *new_node = (CNode *)malloc(sizeof(CNode));
    new_node->data = data;
    if (tail == NULL) {
        new_node->next = new_node;
        return new_node;
    }
    new_node->next = tail->next; /* new->next = head */
    tail->next = new_node;       /* old tail -> new node */
    return new_node;             /* new node is new tail */
}

/* Traverse circular list */
void circular_traverse(CNode *tail) {
    if (tail == NULL) return;
    CNode *head = tail->next;
    CNode *curr = head;
    do {
        printf("%d -> ", curr->data);
        curr = curr->next;
    } while (curr != head);
    printf("(back to head)\n");
}
```

---

## 6. What You CANNOT Do

These are **hard limitations** of linked lists — things that are either impossible or
require significant workarounds.

### 6.1 CANNOT: Random Access in O(1)

```
Array:  arr[5] → O(1). CPU computes: base_address + 5 * sizeof(int). Done.

Linked list: get_node(5) → O(n). Must walk node 0→1→2→3→4→5.
             There is NO mathematical shortcut.

WHY: Nodes are not contiguous. No formula exists to compute an address.

IMPLICATION:
- Binary search on a linked list is O(n log n) not O(log n)
  (because finding mid is O(n) each time)
- Indexing is O(n)
- Quick sort with random pivot is O(n²) for linked lists

WORKAROUND: Skip list (probabilistic data structure) gives O(log n) average
search. But that's a different structure built ON TOP of linked lists.
```

### 6.2 CANNOT: Efficiently Traverse Backwards (Singly Linked)

```
Singly linked list: [1]->[2]->[3]->[4]->[5]->NULL

You CANNOT go from [3] back to [2] directly.
To get to [2] from [3]: go back to head and traverse to [2]. O(n).

Workaround: Use a doubly linked list.
Workaround2: Reverse the list first (destructs original).
```

### 6.3 CANNOT: Delete a Node in O(1) Without Previous Node (Singly Linked)

```
To delete [3] in [1]->[2]->[3]->[4]->[5]:

You need [2] (predecessor) to do: [2]->next = [4].
If you only have a pointer to [3], you cannot reach [2] in O(1).

Workaround: "Copy and Skip" trick (if not tail):
  [3].data = [4].data  (copy [4]'s data into [3])
  [3].next = [4].next  (skip [4])
  free([4])

This works but changes node identity — doesn't work if other pointers
reference [4] specifically (e.g., other code has a pointer to [4]).

Proper fix: Use doubly linked list → O(1) deletion with just the node.
```

### 6.4 CANNOT: Binary Search Effectively

```
Even if your linked list is sorted:
Binary search requires O(1) midpoint access.
Linked list midpoint = O(n).

So binary search on linked list = O(n log n) vs O(log n) on sorted array.

NEVER use linked list when you need fast search by value.
Use: Hash map, BST, sorted array + binary search.
```

### 6.5 CANNOT: Cache-Friendly Access

```
Array: elements sit side by side in memory.
       CPU loads a "cache line" (64 bytes) at once.
       Accessing arr[0] loads arr[0]...arr[15] (for int32).
       Next accesses are free (already in cache). ← CACHE HIT

Linked list: node->next could be ANYWHERE in RAM.
             Following a pointer likely triggers a cache miss each time.
             CPU must fetch from main RAM: ~100-300 cycles per miss.

Benchmark reality: A linked list with 1 million nodes can be
5-10x SLOWER than an array for sequential traversal, solely due to
cache effects, even though both are O(n).

IMPLICATION: Prefer arrays/vectors for performance-critical traversal.
Use linked lists when the benefit (O(1) middle insert/delete) outweighs
the cache cost.
```

### 6.6 CANNOT: Safely Traverse a Circular List with Simple NULL Check

```
Circular list: [1]->[2]->[3]->(back to [1])

BAD code:
Node *curr = head;
while (curr != NULL) {  // BUG: curr is NEVER NULL
    process(curr);
    curr = curr->next;
}
// This loops FOREVER

CORRECT:
Node *curr = head;
do {
    process(curr);
    curr = curr->next;
} while (curr != head);

// OR use a visited flag/counter
```

### 6.7 CANNOT: Know Length in O(1) Without Tracking It

```
Linked list has no built-in length.
Computing length = O(n) traversal.

WORKAROUND: Maintain a `length` field in the list wrapper struct/struct.
Update it on every insert (+1) and delete (-1).
Then length is O(1).

But this requires discipline — forgetting to update breaks everything.
```

### 6.8 CANNOT: Easily Check If a Node Belongs to a List

```
Given a node pointer, you CANNOT tell which list it belongs to
(if any) without traversal.

Array: pointer arithmetic tells you if a pointer is within array bounds.
Linked list: no such check possible.

This matters for: merge operations, split, and when sharing nodes
between lists (which you should generally avoid).
```

---

## 7. Common Mistakes — The Mistake Encyclopedia

This section is critical. These are the mistakes that cause 90% of linked list bugs.

---

### MISTAKE 1: Off-By-One in the Stop Condition

```
WRONG (stops one early):
Node *curr = head;
while (curr->next != NULL) {  // stops at last node
    curr = curr->next;
}
// curr is now at TAIL — good if you want tail
// BAD if you want to process every node including tail's data

RIGHT (processes all nodes):
while (curr != NULL) {
    process(curr->data);
    curr = curr->next;
}
```

```
When to use each:
  curr != NULL        → process all nodes
  curr->next != NULL  → stop at tail (useful for: append to end, find tail)
  curr->next->next != NULL → stop one before last (find second-to-last)
```

---

### MISTAKE 2: Losing Reference Before Saving It

```
This is THE #1 linked list bug.

WRONG insertion (loses rest of list):
prev->next = new_node;    // Step 1: prev now points to new_node
new_node->next = prev->next; // BUG: prev->next IS new_node now!
                              // new_node->next = new_node (circular!)

CORRECT order:
new_node->next = prev->next; // Step 1: SAVE where prev was pointing
prev->next = new_node;       // Step 2: THEN relink

Rule: When changing a pointer, first save what it was pointing to.
```

---

### MISTAKE 3: Not Handling NULL / Empty List

```
CRASH scenario:
void do_something(Node *head) {
    printf("%d\n", head->data); // CRASH if head is NULL!
}

Every function must check:
if (head == NULL) return; // or handle accordingly
if (head == NULL || head->next == NULL) return head; // single element

Common places to check:
- Start of every function
- After getting curr->next (is it NULL before dereferencing?)
- When list is expected to have at least 2 elements
```

---

### MISTAKE 4: Memory Leak — Not Freeing Deleted Nodes (C)

```
WRONG (memory leak):
void delete_node(Node **head, int val) {
    // ... find and unlink node ...
    prev->next = curr->next;
    // curr is now unlinked but NOT freed — memory leak!
}

CORRECT:
prev->next = curr->next;
free(curr);     // ALWAYS free in C
curr = NULL;    // Optional but good practice (prevents use-after-free)

In Go: GC handles this automatically (but you should still nil pointers)
In Rust: Box<T> drops automatically when ownership is released (no manual free)
```

---

### MISTAKE 5: Use-After-Free (C)

```
CRASH scenario:
Node *temp = curr;
free(temp);
printf("%d\n", curr->data); // BUG: curr and temp point to freed memory!

Or even more subtle:
Node *saved = curr->next;
free(curr);
process(saved);  // OK IF saved was saved BEFORE free
// but:
free(curr);
Node *saved = curr->next; // BUG: curr is freed, dereferencing is UB!

Rule: Free last. Save everything you need BEFORE freeing.
```

---

### MISTAKE 6: Infinite Loop in Cycle/Circular Operations

```
Scenario: You removed a cycle but forgot to set tail->next = NULL.

Or: You're iterating a circular list:
CNode *curr = head;
while (curr != NULL) {  // NULL never happens in circular list
    ...
}
// INFINITE LOOP

Fix: Use a counter or compare with head:
int count = 0;
while (count < known_length) { ... }
// OR
do { ... } while (curr != head);
```

---

### MISTAKE 7: Incorrect Two-Pointer Setup

```
Find kth from end:
Wrong: advance fast k steps (leads to off-by-one)
Right: advance fast k+1 steps from a dummy node

Wrong for finding middle of even-length list:
Using fast = head->next vs fast = head gives DIFFERENT midpoints.
Know which one you want:
  fast = head:       returns UPPER (second) middle for even n
  fast = head->next: returns LOWER (first) middle for even n
```

---

### MISTAKE 8: Not Handling the Tail in Insertions/Deletions

```
Scenario: You maintain both head and tail pointers.
You insert or delete but forget to update tail.

Classic bug:
void delete_node(LinkedList *list, Node *node) {
    // ... unlink node ...
    // FORGOT: if (node == list->tail) list->tail = prev;
}

After this, list->tail points to freed memory → undefined behavior.

Rule: Any time you modify the last node (or a node might be last),
update tail.
```

---

### MISTAKE 9: Deep Copy vs Shallow Copy Confusion

```
Scenario: You want a copy of a list.

WRONG (shallow copy):
Node *copy = original_head; // just copies the pointer, NOT the list!
// "copy" and "original_head" point to THE SAME NODES
// Modifying one "list" modifies the other

CORRECT (deep copy):
Node *copy_head = NULL;
Node *curr = original_head;
while (curr != NULL) {
    // create a brand new node for each element
    append(copy_head, curr->data);
    curr = curr->next;
}

Special case: Lists with random pointers need the interweaving technique.
```

---

### MISTAKE 10: Reversing in Blocks — Forgetting to Connect Groups

```
Reverse in k-groups, e.g., k=3:
[1]->[2]->[3]->[4]->[5]->[6]->NULL
          becomes
[3]->[2]->[1]->[6]->[5]->[4]->NULL

Bug: After reversing [1,2,3], the new tail [1] still points to [4].
You must: after reversing a group, connect the tail of that group
to the HEAD of the next group.

Also: the PREV group's tail must connect to the NEW HEAD of the current group.
This requires carefully saving: prev_tail, group_head (becomes new tail),
and new_head (becomes new front of group after reversal).
```

---

### MISTAKE 11: Modifying List While Iterating

```
Concurrent modification bug:
Node *curr = head;
while (curr != NULL) {
    if (should_delete(curr)) {
        delete_node(list, curr); // modifies list structure
    }
    curr = curr->next; // BUG: curr might be freed/invalid!
}

CORRECT: Save next BEFORE potential deletion:
Node *curr = head;
while (curr != NULL) {
    Node *next = curr->next; // SAVE BEFORE MODIFYING
    if (should_delete(curr)) {
        delete_node(list, curr);
    }
    curr = next; // use saved next
}
```

---

### MISTAKE 12: Doubly Linked List — Partial Pointer Update

```
Inserting X after B in A <-> B <-> C:

WRONG (4 links to update, but only updating 3):
X->prev = B;         ✓
X->next = B->next;   ✓ (X->next = C)
B->next = X;         ✓
// FORGOT: C->prev = X

Result:
A <-> B <-> X -> C  (X's forward link ok)
             X <- C  WRONG: C->prev still points to B!

The "prev" direction is broken.
Rule: In doubly linked, ALWAYS update ALL 4 affected pointers.
```

---

### MISTAKE 13: Merging / Splitting — Not Null-Terminating

```
When splitting a list in half for merge sort:
Node *mid = find_middle(head);
Node *second = mid->next;
// FORGOT: mid->next = NULL;
// Result: The "first half" still connects to second half!
// Merge sort recurses on a list that's not actually split!

Always cut the link: mid->next = NULL;
before recursing.
```

---

### MISTAKE 14: Stack Overflow in Deep Recursion

```
Recursive traversal/reversal on a list of 100,000 nodes:
Each function call uses stack space (~100-200 bytes).
100,000 * 150 bytes = ~15 MB of stack
Default stack size: 1-8 MB on most systems.

Result: Stack overflow (segfault in C, panic in Rust/Go).

Rule: For large lists, ALWAYS prefer iterative over recursive.
Reserve recursion for: small lists, tree structures, or when
tail-call optimization is guaranteed.
```

---

## 8. Two-Pointer Technique

This is the **master pattern** for solving 80% of linked list interview problems.

```
THE TWO-POINTER MENTAL MODEL:
==============================

Two pointers move through the list at different speeds or different starting
positions to detect relationships or find specific positions.

FAST/SLOW (Tortoise and Hare):
  slow: moves 1 step
  fast: moves 2 steps
  Use for: middle finding, cycle detection, palindrome

K-GAP (Two pointers with K distance apart):
  Advance one pointer K steps, then move both together.
  When far pointer hits end, near pointer is K from end.
  Use for: Nth from end, split list

SAME-SPEED (Two pointers, different start):
  Both move 1 step, but one starts at a different position.
  Use for: intersection detection, removing duplicates

MEET-IN-THE-MIDDLE:
  One starts at head, one at tail (doubly linked).
  Move toward each other.
  Use for: palindrome check in doubly linked list

DECISION TREE:
==============
Problem type?
 |
 +---> Find middle? .................. Fast/slow (2:1 speed)
 |
 +---> Detect cycle? ................. Fast/slow (2:1 speed)
 |
 +---> Kth from end? ................. K-gap technique
 |
 +---> Intersection? ................. Same-speed, different start
 |
 +---> Palindrome? ................... Fast/slow to find mid + reverse
 |
 +---> Remove duplicates? ............ Two pointers same list
 |
 +---> Merge sorted lists? ........... Compare heads (two pointers)
```

---

## 9. Sentinel / Dummy Node Pattern

**Concept:** A "dummy" or "sentinel" node is a fake node inserted at the beginning
(and sometimes end) of a list to simplify edge cases.

```
WHY USE A DUMMY NODE?
======================

Without dummy:
  insert_head requires: if (head == NULL) {...} else {...}
  delete requires: if (node == head) {...} else {...}
  Many if-else branches for "is this the head?" case.

With dummy node:
  The dummy is always there. head = dummy.next (could be NULL).
  All operations work uniformly — no special head case.

ASCII:
  [dummy|*] -> [1|*] -> [2|*] -> [3|NULL]
    ^
    This node is never user-visible, just a sentinel.

MERGE SORTED LISTS WITH DUMMY:
================================
Without dummy:
  if (result_head == NULL) {
      result_head = node;
      result_tail = node;
  } else {
      result_tail->next = node;
      result_tail = node;
  }

With dummy:
  Node dummy; dummy.next = NULL;
  Node *tail = &dummy;
  // In loop:
  tail->next = node;  // always works, no special case
  tail = tail->next;
  // At end:
  return dummy.next;  // skip the dummy

Pattern: Use dummy nodes whenever you find yourself writing
special cases for empty list or head modifications.
```

**C:**
```c
/* Partition using dummy nodes — cleaner code */
Node *partition_clean(Node *head, int x) {
    /* Two dummy nodes — no special cases needed */
    Node less_dummy = {0, NULL};
    Node gte_dummy  = {0, NULL};
    Node *less = &less_dummy;
    Node *gte  = &gte_dummy;

    while (head != NULL) {
        if (head->data < x) { less->next = head; less = less->next; }
        else                 { gte->next  = head; gte  = gte->next; }
        head = head->next;
    }
    gte->next = NULL;
    less->next = gte_dummy.next;
    return less_dummy.next;
}
```

---

## 10. Complexity Reference

### Per-Operation Complexity Table

```
+-------------------------------+----------------+----------------+---------------+
| Operation                     | Singly Linked  | Doubly Linked  | Array (ref)   |
+-------------------------------+----------------+----------------+---------------+
| Access by index               | O(n)           | O(n)           | O(1)          |
| Search by value               | O(n)           | O(n)           | O(n)          |
| Insert at HEAD                | O(1)           | O(1)           | O(n)          |
| Insert at TAIL (w/ tail ptr)  | O(1)           | O(1)           | O(1) amort.   |
| Insert at TAIL (no tail ptr)  | O(n)           | O(n)           | O(1) amort.   |
| Insert at middle (given node) | O(1)           | O(1)           | O(n)          |
| Insert at middle (by index)   | O(n)           | O(n)           | O(n)          |
| Delete HEAD                   | O(1)           | O(1)           | O(n)          |
| Delete TAIL (w/ tail ptr)     | O(n)*          | O(1)           | O(1)          |
| Delete middle (given node)    | O(n)**         | O(1)           | O(n)          |
| Delete middle (by index)      | O(n)           | O(n)           | O(n)          |
| Reversal                      | O(n)           | O(n)           | O(n)          |
| Find middle                   | O(n)           | O(n)           | O(1)          |
| Cycle detection               | O(n)           | O(n)           | N/A           |
| Merge two sorted lists        | O(n+m)         | O(n+m)         | O(n+m)        |
| Sort (merge sort)             | O(n log n)     | O(n log n)     | O(n log n)    |
+-------------------------------+----------------+----------------+---------------+

*  Singly linked tail delete: O(n) because you need predecessor
** Singly linked delete given node: O(n) to find predecessor
   (O(1) only with the "copy-and-skip" trick, with caveats)
```

### Space Complexity

```
+---------------------------+-------------------+
| Structure                 | Space per node    |
+---------------------------+-------------------+
| Singly linked node        | data + 1 pointer  |
| Doubly linked node        | data + 2 pointers |
| Singly + tail pointer     | data + 2 ptrs     |
| Node on 64-bit system     |                   |
|   int data (4 bytes)      |                   |
|   next pointer (8 bytes)  | = 12 bytes raw    |
|   + padding (4 bytes)     | = 16 bytes struct |
|   + malloc overhead       | ~ 24-32 bytes     |
+---------------------------+-------------------+

Algorithms:
  Iterative traversal:     O(1) extra space
  Recursive traversal:     O(n) call stack
  Cycle detection:         O(1) (Floyd's)
  Cycle detection (hash):  O(n)
  Clone with random ptrs:  O(1) (interweaving), O(n) (hashmap)
```

---

## 11. Mental Models for Expert Thinking

### 11.1 The "Draw It First" Rule

Before coding ANY linked list problem:
1. Draw 3-4 nodes with arrows.
2. Label which pointer is `curr`, `prev`, `next`.
3. Execute each line of your algorithm on the drawing.
4. Ask: "What happens for 0 nodes? 1 node? 2 nodes?"

This catches 80% of bugs before you write a line of code.

### 11.2 The "What Gets Lost?" Check

Every time you change a pointer, ask: *"What was this pointer pointing to before?
Do I still need it? Did I save it?"*

```
Pattern recognition:
X->next = Y;   ← DANGER: what was X->next before? Save it if needed.

Safe pattern:
temp = X->next; // SAVE first
X->next = Y;    // THEN change
// now use temp
```

### 11.3 The "State Machine" View

A linked list operation is a state machine. Each step transitions the pointers
from one valid state to another.

```
REVERSAL STATE MACHINE:
========================
State = (prev, curr, next)

Initial: (NULL, head, head->next)
Each step:
  1. Save: next = curr->next
  2. Reverse: curr->next = prev
  3. Advance: prev = curr, curr = next
Terminal: curr = NULL
Output: prev (new head)

If you can describe each state precisely,
you can NEVER get lost in the algorithm.
```

### 11.4 The "Invariant" Mental Model

An **invariant** is something that is ALWAYS true at a certain point in your code.
Define invariants explicitly:

```
In merge sort:
  INVARIANT before merging: both halves are already sorted
  INVARIANT after splitting: mid->next = NULL (lists are disconnected)

In traversal:
  INVARIANT at loop start: curr points to the node we haven't processed yet

If your invariant ever becomes false → you found the bug.
```

### 11.5 Chunking: Reduce to Known Sub-problems

Expert problem solvers mentally decompose:
- "Sort a linked list" → "I need merge sort" → "I need: find_middle, split, merge_sorted"
- "Palindrome check" → "I need: find_middle, reverse_second_half, compare"
- "Copy list with random pointers" → "I need: create copies, link randoms, separate lists"

Build a mental library of these sub-problem → algorithm mappings.
Each new problem is a combination of familiar pieces.

### 11.6 The "Boundary Thinking" Discipline

Always verify these cases:
```
Empty list:          head == NULL
Single node:         head->next == NULL
Two nodes:           (special for reversal, middle finding, palindrome)
Even/Odd length:     (matters for middle finding)
All same value:      (matters for deduplication, search)
Already sorted:      (matters for sort correctness check)
Reverse sorted:      (matters for worst-case behavior)
```

---

## 12. Language-Specific Pitfalls

### 12.1 C — Memory Management Pitfalls

```
1. FORGETTING free():
   Every malloc() must have a corresponding free().
   Use valgrind to detect leaks: valgrind --leak-check=full ./program

2. DOUBLE FREE:
   free(p); free(p);  // undefined behavior, usually crash
   After free: p = NULL; (makes double free a null deref instead of UB)

3. STACK-ALLOCATED NODE ADDRESSES:
   Node create_node(int data) {
       Node n = {data, NULL};
       return &n;   // BUG: returns address of local variable!
       // n is on the stack, destroyed when function returns
   }
   // Always use malloc() for nodes that must outlive the function.

4. POINTER-TO-POINTER (Node **) CONFUSION:
   Needed when: you want to modify the HEAD pointer from inside a function.
   void insert_head(Node **head, int data) {
       Node *n = malloc(sizeof(Node));
       n->next = *head;   // dereference to get current head
       *head = n;         // dereference to update head
   }
   // Call: insert_head(&list_head, 42);
   // Without **: the function gets a COPY of head, modifying it
   // has no effect outside the function.
```

### 12.2 Rust — Ownership & Borrow Checker Pitfalls

```
1. THE "CANNOT BORROW AS MUTABLE MORE THAN ONCE" ERROR:
   The borrow checker prevents two simultaneous mutable references.
   This is why doubly linked lists require Rc<RefCell<>> or unsafe code.

2. Option::take() IS YOUR FRIEND:
   // Move the value out of Option, leaving None
   let next = node.next.take();
   // This is how you "unlink" nodes without fighting the borrow checker.

3. CANNOT HOLD REFERENCE AND MUTATE:
   let ref_to_node = list.get_node(5); // immutable borrow of list
   list.insert(3);  // ERROR: mutable borrow while immutable borrow exists
   // Solution: finish using ref_to_node before mutating list

4. LINKED LISTS IN RUST — WHEN TO USE unsafe:
   For performance-critical, production-grade linked lists:
   Use *mut Node raw pointers inside an unsafe block.
   Wrap in a safe API. The std::collections::LinkedList does this.
   
   For learning/interviews: Option<Box<Node>> is fine and idiomatic.

5. THE CLASSIC LEARN-RUST-THE-HARD-WAY:
   "Learn Rust With Entirely Too Many Linked Lists" by Alexis Beingessner
   is the canonical resource for understanding WHY Rust makes this hard.
```

### 12.3 Go — Nil and Interface Pitfalls

```
1. NIL POINTER DEREFERENCE:
   var node *Node  // node is nil
   fmt.Println(node.Data)  // PANIC: nil pointer dereference
   Always check: if node == nil { return }

2. NIL INTERFACE VS NIL POINTER (subtle):
   var n *Node = nil
   var i interface{} = n
   i == nil   // FALSE! (typed nil vs untyped nil)
   // This catches people off guard when using interfaces.
   // In linked lists: stick to concrete *Node types, avoid interface{}.

3. GO'S GARBAGE COLLECTOR — NOT A LICENSE TO BE CARELESS:
   In Go you don't free memory, but you CAN cause memory leaks
   if you hold references to nodes you're "done" with.
   When you delete a node, set its Next/Prev to nil:
   node.Next = nil
   node.Prev = nil
   // This lets the GC collect them sooner.

4. VALUE SEMANTICS SURPRISE:
   func modifyHead(head *Node) {
       head = head.Next  // only modifies the LOCAL copy of head
       // does NOT change the caller's head variable!
   }
   // To modify head from outside: pass **Node or return new head
   func modifyHead(head *Node) *Node {
       return head.Next  // caller must: head = modifyHead(head)
   }
```

---

## Appendix: Quick Reference — Algorithm Patterns

```
PROBLEM                    →   TECHNIQUE
-----------------------------------------
Find middle                →   Slow/fast pointers (2:1 speed)
Detect cycle               →   Slow/fast pointers, meet = cycle exists
Find cycle start           →   Meet point + head, both 1-step → meet at start
Kth from end               →   Gap-of-k technique with dummy node
Intersection of two lists  →   Two pointers, swap to other list at NULL
Palindrome                 →   Find mid + reverse second half + compare
Merge two sorted           →   Dummy head + compare heads
Sort list                  →   Merge sort (find mid + split + merge)
Reverse list               →   Three pointers: prev, curr, next
Reverse in k-groups        →   Reverse k nodes, connect groups, recurse/iterate
Remove Nth from end        →   Gap of n+1 from dummy node
Detect start of cycle      →   Floyd's phase 2 (put ptr at head after detect)
Clone with random ptrs     →   Weave copies → set randoms → separate
Flatten multilevel         →   For each node with child: splice child list in
Partition by value         →   Two dummy lists: less + gte, connect at end
```

---

## Appendix: Complete Rust Singly Linked List

```rust
use std::fmt;

#[derive(Debug)]
pub struct Node {
    pub data: i32,
    pub next: Option<Box<Node>>,
}

#[derive(Debug)]
pub struct LinkedList {
    pub head: Option<Box<Node>>,
    pub length: usize,
}

impl LinkedList {
    pub fn new() -> Self { LinkedList { head: None, length: 0 } }

    pub fn push_front(&mut self, data: i32) {
        let mut node = Box::new(Node { data, next: None });
        node.next = self.head.take();
        self.head = Some(node);
        self.length += 1;
    }

    pub fn pop_front(&mut self) -> Option<i32> {
        self.head.take().map(|node| {
            self.head = node.next;
            self.length -= 1;
            node.data
        })
    }

    pub fn push_back(&mut self, data: i32) {
        let new_node = Box::new(Node { data, next: None });
        let mut curr = &mut self.head;
        loop {
            match curr {
                None => { *curr = Some(new_node); break; }
                Some(node) => { curr = &mut node.next; }
            }
        }
        self.length += 1;
    }

    pub fn reverse(&mut self) {
        let mut prev: Option<Box<Node>> = None;
        let mut curr = self.head.take();
        while let Some(mut node) = curr {
            let next = node.next.take();
            node.next = prev;
            prev = Some(node);
            curr = next;
        }
        self.head = prev;
    }

    pub fn len(&self) -> usize { self.length }
    pub fn is_empty(&self) -> bool { self.head.is_none() }
}

impl fmt::Display for LinkedList {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let mut curr = &self.head;
        while let Some(node) = curr {
            write!(f, "{} -> ", node.data)?;
            curr = &node.next;
        }
        write!(f, "None")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic() {
        let mut list = LinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        assert_eq!(list.len(), 3);
        list.reverse();
        assert_eq!(list.pop_front(), Some(3));
        assert_eq!(list.pop_front(), Some(2));
        assert_eq!(list.pop_front(), Some(1));
    }
}
```

---

## Appendix: Complete Go Singly Linked List

```go
package linkedlist

import (
    "fmt"
    "strings"
)

type Node struct {
    Data int
    Next *Node
}

type LinkedList struct {
    Head   *Node
    Tail   *Node
    Length int
}

func New() *LinkedList { return &LinkedList{} }

func (ll *LinkedList) PushFront(data int) {
    n := &Node{Data: data, Next: ll.Head}
    ll.Head = n
    if ll.Tail == nil { ll.Tail = n }
    ll.Length++
}

func (ll *LinkedList) PushBack(data int) {
    n := &Node{Data: data}
    if ll.Tail == nil {
        ll.Head = n
        ll.Tail = n
    } else {
        ll.Tail.Next = n
        ll.Tail = n
    }
    ll.Length++
}

func (ll *LinkedList) PopFront() (int, bool) {
    if ll.Head == nil { return 0, false }
    v := ll.Head.Data
    ll.Head = ll.Head.Next
    if ll.Head == nil { ll.Tail = nil }
    ll.Length--
    return v, true
}

func (ll *LinkedList) Reverse() {
    var prev *Node
    curr := ll.Head
    ll.Tail = ll.Head
    for curr != nil {
        next := curr.Next
        curr.Next = prev
        prev = curr
        curr = next
    }
    ll.Head = prev
}

func (ll *LinkedList) FindMiddle() *Node {
    slow, fast := ll.Head, ll.Head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    return slow
}

func (ll *LinkedList) String() string {
    var sb strings.Builder
    curr := ll.Head
    for curr != nil {
        sb.WriteString(fmt.Sprintf("%d -> ", curr.Data))
        curr = curr.Next
    }
    sb.WriteString("nil")
    return sb.String()
}
```

---

*This guide covers all fundamental and advanced linked list manipulation
operations, constraints, common mistakes, and implementation patterns
in C, Rust, and Go. Master each section, draw every diagram by hand,
and implement each algorithm from scratch in all three languages.
The deepest understanding comes from fighting the compiler — especially
in Rust, where the borrow checker will force you to think precisely
about ownership and lifetime, which is exactly the mental model you need
for world-class systems programming.*
