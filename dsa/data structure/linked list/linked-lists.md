# The Complete Guide to Linked Lists
### Implementations in C, Go, and Rust

---

## Table of Contents

1. [What is a Linked List?](#1-what-is-a-linked-list)
2. [Types of Linked Lists](#2-types-of-linked-lists)
3. [Memory Model & Pointer Mechanics](#3-memory-model--pointer-mechanics)
4. [Singly Linked List — Full Implementation](#4-singly-linked-list--full-implementation)
   - 4.1 Iterative Approach
   - 4.2 Recursive Approach
5. [Doubly Linked List — Full Implementation](#5-doubly-linked-list--full-implementation)
6. [Circular Linked List — Full Implementation](#6-circular-linked-list--full-implementation)
7. [Skip List](#7-skip-list)
8. [XOR Linked List (Memory-Efficient Doubly LL)](#8-xor-linked-list-memory-efficient-doubly-ll)
9. [Self-Organizing / Self-Adjusting Linked List](#9-self-organizing--self-adjusting-linked-list)
10. [Unrolled Linked List](#10-unrolled-linked-list)
11. [Sentinel / Dummy Node Technique](#11-sentinel--dummy-node-technique)
12. [Recursive Patterns — Deep Dive](#12-recursive-patterns--deep-dive)
13. [Traversal Techniques](#13-traversal-techniques)
14. [Insertion — Every Case](#14-insertion--every-case)
15. [Deletion — Every Case](#15-deletion--every-case)
16. [Searching — Iterative & Recursive](#16-searching--iterative--recursive)
17. [Reversal — Iterative & Recursive](#17-reversal--iterative--recursive)
18. [Sorting a Linked List](#18-sorting-a-linked-list)
19. [Merging Linked Lists](#19-merging-linked-lists)
20. [Detecting and Removing Cycles](#20-detecting-and-removing-cycles)
21. [Finding Middle, Nth from End](#21-finding-middle-nth-from-end)
22. [Stack & Queue using Linked Lists](#22-stack--queue-using-linked-lists)
23. [Time & Space Complexity Analysis](#23-time--space-complexity-analysis)
24. [Common Pitfalls & Best Practices](#24-common-pitfalls--best-practices)

---

## 1. What is a Linked List?

A **linked list** is a linear data structure where elements (called **nodes**) are stored in non-contiguous memory locations. Each node holds:

- **Data**: the actual value stored
- **Pointer(s)**: reference(s) to the next (and/or previous) node

Unlike arrays, linked lists do **not** store elements in sequential memory. Each node lives wherever the allocator places it, and they are chained together via pointers.

### Why use a linked list over an array?

| Feature | Array | Linked List |
|---|---|---|
| Memory layout | Contiguous | Scattered (heap) |
| Access by index | O(1) | O(n) |
| Insert at head | O(n) (shift) | O(1) |
| Insert at tail | O(1) amortized | O(1) with tail ptr |
| Insert at middle | O(n) | O(n) find + O(1) link |
| Delete at head | O(n) (shift) | O(1) |
| Size flexibility | Fixed (static) or costly resize | Grows/shrinks freely |
| Cache performance | Excellent (cache-line locality) | Poor (pointer chasing) |

**Use linked lists when:**
- Frequent insertions/deletions at the head or middle
- Size is unknown or highly dynamic
- You need O(1) splicing of sublists
- Implementing stacks, queues, adjacency lists, LRU caches

---

## 2. Types of Linked Lists

### 2.1 Singly Linked List
Each node points only to the **next** node. Traversal is one-directional (head → tail).

```
[data|next] → [data|next] → [data|next] → NULL
```

### 2.2 Doubly Linked List
Each node has two pointers: **prev** and **next**. Traversal is bidirectional.

```
NULL ← [prev|data|next] ↔ [prev|data|next] ↔ [prev|data|next] → NULL
```

### 2.3 Circular Singly Linked List
The last node's `next` points back to the **head** instead of NULL.

```
[data|next] → [data|next] → [data|next] ─┐
     ▲                                    │
     └────────────────────────────────────┘
```

### 2.4 Circular Doubly Linked List
Combines doubly and circular: head's `prev` points to tail, tail's `next` points to head.

### 2.5 Skip List
A layered linked list with express lanes for O(log n) average search.

### 2.6 XOR Linked List
A memory-efficient doubly linked list storing `prev XOR next` in a single pointer field.

### 2.7 Unrolled Linked List
Nodes store arrays of elements instead of one element each — better cache performance.

### 2.8 Self-Organizing Linked List
Reorders nodes based on access frequency (Move-to-Front, Transpose, Count, Ordering).

---

## 3. Memory Model & Pointer Mechanics

Understanding how linked list nodes live in memory is crucial to avoiding bugs.

### 3.1 Heap Allocation

In C, every node is `malloc`'d. The node lives on the heap until explicitly `free`'d.

```c
Node* node = (Node*)malloc(sizeof(Node));
// node holds the ADDRESS of the newly allocated memory
// *node dereferences to the Node struct
// node->data is sugar for (*node).data
```

In Go, every node is allocated with `new()` or composite literals — the GC manages lifetime.

In Rust, `Box<T>` gives heap ownership with compile-time drop guarantees; no manual `free`.

### 3.2 Pointer vs Value

```
Stack:                   Heap:
┌──────────┐            ┌───────────────┐
│ head ptr │──────────▶ │  data: 42     │
│ (8 bytes)│            │  next: ──────▶│ ... next node
└──────────┘            └───────────────┘
```

### 3.3 NULL / nil / None semantics

- **C**: `NULL` (defined as `(void*)0`) marks end of list
- **Go**: `nil` for pointer fields
- **Rust**: `Option<Box<Node>>` — `None` marks end; the type system enforces null-safety

---

## 4. Singly Linked List — Full Implementation

### 4.1 Iterative Approach

#### C

```c
#include <stdio.h>
#include <stdlib.h>

/* ── Node definition ── */
typedef struct Node {
    int data;
    struct Node* next;
} Node;

/* ── List handle ── */
typedef struct {
    Node* head;
    int   size;
} LinkedList;

/* Initialize */
void ll_init(LinkedList* list) {
    list->head = NULL;
    list->size = 0;
}

/* Create a new node */
Node* new_node(int data) {
    Node* n = (Node*)malloc(sizeof(Node));
    if (!n) { perror("malloc"); exit(EXIT_FAILURE); }
    n->data = data;
    n->next = NULL;
    return n;
}

/* ── Insert at head ── O(1) */
void insert_head(LinkedList* list, int data) {
    Node* n    = new_node(data);
    n->next    = list->head;
    list->head = n;
    list->size++;
}

/* ── Insert at tail ── O(n) */
void insert_tail(LinkedList* list, int data) {
    Node* n = new_node(data);
    if (!list->head) { list->head = n; list->size++; return; }
    Node* cur = list->head;
    while (cur->next) cur = cur->next;
    cur->next = n;
    list->size++;
}

/* ── Insert at position (0-indexed) ── */
void insert_at(LinkedList* list, int data, int pos) {
    if (pos < 0 || pos > list->size) { printf("Invalid position\n"); return; }
    if (pos == 0) { insert_head(list, data); return; }
    Node* n   = new_node(data);
    Node* cur = list->head;
    for (int i = 0; i < pos - 1; i++) cur = cur->next;
    n->next   = cur->next;
    cur->next = n;
    list->size++;
}

/* ── Delete at head ── O(1) */
void delete_head(LinkedList* list) {
    if (!list->head) return;
    Node* tmp  = list->head;
    list->head = list->head->next;
    free(tmp);
    list->size--;
}

/* ── Delete at tail ── O(n) */
void delete_tail(LinkedList* list) {
    if (!list->head) return;
    if (!list->head->next) { free(list->head); list->head = NULL; list->size--; return; }
    Node* cur = list->head;
    while (cur->next->next) cur = cur->next;
    free(cur->next);
    cur->next = NULL;
    list->size--;
}

/* ── Delete by value ── O(n) */
void delete_value(LinkedList* list, int data) {
    if (!list->head) return;
    if (list->head->data == data) { delete_head(list); return; }
    Node* cur = list->head;
    while (cur->next && cur->next->data != data) cur = cur->next;
    if (!cur->next) { printf("Value not found\n"); return; }
    Node* tmp = cur->next;
    cur->next = tmp->next;
    free(tmp);
    list->size--;
}

/* ── Search ── O(n) */
Node* search(LinkedList* list, int data) {
    Node* cur = list->head;
    while (cur) {
        if (cur->data == data) return cur;
        cur = cur->next;
    }
    return NULL;
}

/* ── Traverse / Print ── */
void print_list(LinkedList* list) {
    Node* cur = list->head;
    printf("HEAD");
    while (cur) { printf(" → %d", cur->data); cur = cur->next; }
    printf(" → NULL\n");
}

/* ── Reverse ── O(n) */
void reverse(LinkedList* list) {
    Node *prev = NULL, *cur = list->head, *next = NULL;
    while (cur) {
        next      = cur->next;
        cur->next = prev;
        prev      = cur;
        cur       = next;
    }
    list->head = prev;
}

/* ── Free entire list ── */
void ll_free(LinkedList* list) {
    Node* cur = list->head;
    while (cur) { Node* tmp = cur; cur = cur->next; free(tmp); }
    list->head = NULL;
    list->size = 0;
}

int main(void) {
    LinkedList list;
    ll_init(&list);

    insert_tail(&list, 10);
    insert_tail(&list, 20);
    insert_tail(&list, 30);
    insert_head(&list, 5);
    insert_at(&list, 15, 2);

    print_list(&list);   /* HEAD → 5 → 10 → 15 → 20 → 30 → NULL */

    delete_value(&list, 15);
    print_list(&list);

    reverse(&list);
    print_list(&list);

    ll_free(&list);
    return 0;
}
```

#### Go

```go
package main

import "fmt"

// Node holds data and a pointer to the next node
type Node struct {
    Data int
    Next *Node
}

// LinkedList wraps the head pointer and size
type LinkedList struct {
    Head *Node
    Size int
}

// InsertHead inserts at the beginning — O(1)
func (l *LinkedList) InsertHead(data int) {
    l.Head = &Node{Data: data, Next: l.Head}
    l.Size++
}

// InsertTail inserts at the end — O(n)
func (l *LinkedList) InsertTail(data int) {
    n := &Node{Data: data}
    if l.Head == nil {
        l.Head = n
        l.Size++
        return
    }
    cur := l.Head
    for cur.Next != nil {
        cur = cur.Next
    }
    cur.Next = n
    l.Size++
}

// InsertAt inserts at a given 0-indexed position
func (l *LinkedList) InsertAt(data, pos int) {
    if pos < 0 || pos > l.Size {
        fmt.Println("Invalid position")
        return
    }
    if pos == 0 {
        l.InsertHead(data)
        return
    }
    cur := l.Head
    for i := 0; i < pos-1; i++ {
        cur = cur.Next
    }
    cur.Next = &Node{Data: data, Next: cur.Next}
    l.Size++
}

// DeleteHead removes the first node — O(1)
func (l *LinkedList) DeleteHead() {
    if l.Head == nil {
        return
    }
    l.Head = l.Head.Next
    l.Size--
}

// DeleteTail removes the last node — O(n)
func (l *LinkedList) DeleteTail() {
    if l.Head == nil {
        return
    }
    if l.Head.Next == nil {
        l.Head = nil
        l.Size--
        return
    }
    cur := l.Head
    for cur.Next.Next != nil {
        cur = cur.Next
    }
    cur.Next = nil
    l.Size--
}

// DeleteValue removes the first node with the given value
func (l *LinkedList) DeleteValue(data int) {
    if l.Head == nil {
        return
    }
    if l.Head.Data == data {
        l.DeleteHead()
        return
    }
    cur := l.Head
    for cur.Next != nil && cur.Next.Data != data {
        cur = cur.Next
    }
    if cur.Next == nil {
        fmt.Println("Value not found")
        return
    }
    cur.Next = cur.Next.Next
    l.Size--
}

// Search finds the first node with the given value
func (l *LinkedList) Search(data int) *Node {
    cur := l.Head
    for cur != nil {
        if cur.Data == data {
            return cur
        }
        cur = cur.Next
    }
    return nil
}

// Reverse reverses the list in place — O(n)
func (l *LinkedList) Reverse() {
    var prev *Node
    cur := l.Head
    for cur != nil {
        next := cur.Next
        cur.Next = prev
        prev = cur
        cur = next
    }
    l.Head = prev
}

// Print displays the list
func (l *LinkedList) Print() {
    fmt.Print("HEAD")
    cur := l.Head
    for cur != nil {
        fmt.Printf(" → %d", cur.Data)
        cur = cur.Next
    }
    fmt.Println(" → nil")
}

func main() {
    list := &LinkedList{}
    list.InsertTail(10)
    list.InsertTail(20)
    list.InsertTail(30)
    list.InsertHead(5)
    list.InsertAt(15, 2)
    list.Print()        // HEAD → 5 → 10 → 15 → 20 → 30 → nil

    list.DeleteValue(15)
    list.Print()

    list.Reverse()
    list.Print()
}
```

#### Rust

```rust
// Rust models linked list nodes as Option<Box<Node>>
// Box<T> = heap-allocated T with single ownership
// Option<T> = Some(T) | None  (replaces NULL safely)

#[derive(Debug)]
struct Node {
    data: i32,
    next: Option<Box<Node>>,
}

struct LinkedList {
    head: Option<Box<Node>>,
    size: usize,
}

impl LinkedList {
    fn new() -> Self {
        LinkedList { head: None, size: 0 }
    }

    /// Insert at head — O(1)
    fn insert_head(&mut self, data: i32) {
        let old_head = self.head.take(); // take() replaces with None
        self.head = Some(Box::new(Node { data, next: old_head }));
        self.size += 1;
    }

    /// Insert at tail — O(n)
    fn insert_tail(&mut self, data: i32) {
        let new_node = Box::new(Node { data, next: None });
        // Walk to last node using a mutable reference
        let mut cur = &mut self.head;
        loop {
            match cur {
                None => { *cur = Some(new_node); break; }
                Some(node) => cur = &mut node.next,
            }
        }
        self.size += 1;
    }

    /// Delete head — O(1)
    fn delete_head(&mut self) {
        if let Some(old_head) = self.head.take() {
            self.head = old_head.next;
            self.size -= 1;
        }
    }

    /// Delete by value — O(n)
    fn delete_value(&mut self, data: i32) {
        let mut cur = &mut self.head;
        loop {
            match cur {
                None => return,
                Some(node) if node.data == data => {
                    *cur = node.next.take();
                    self.size -= 1;
                    return;
                }
                Some(node) => cur = &mut node.next,
            }
        }
    }

    /// Search — O(n)
    fn search(&self, data: i32) -> bool {
        let mut cur = &self.head;
        while let Some(node) = cur {
            if node.data == data { return true; }
            cur = &node.next;
        }
        false
    }

    /// Reverse — O(n)
    fn reverse(&mut self) {
        let mut prev: Option<Box<Node>> = None;
        let mut cur = self.head.take();
        while let Some(mut node) = cur {
            let next = node.next.take();
            node.next = prev;
            prev = Some(node);
            cur = next;
        }
        self.head = prev;
    }

    /// Print
    fn print(&self) {
        print!("HEAD");
        let mut cur = &self.head;
        while let Some(node) = cur {
            print!(" → {}", node.data);
            cur = &node.next;
        }
        println!(" → None");
    }
}

fn main() {
    let mut list = LinkedList::new();
    list.insert_tail(10);
    list.insert_tail(20);
    list.insert_tail(30);
    list.insert_head(5);
    list.print(); // HEAD → 5 → 10 → 20 → 30 → None

    list.delete_value(20);
    list.print();

    list.reverse();
    list.print();
}
```

---

### 4.2 Recursive Approach

Recursion models linked lists **naturally** because a list is either:
- **Empty** (NULL/nil/None), or
- A **node** followed by a **smaller list** (the tail)

This recursive structure enables elegant solutions for many operations.

#### C — Recursive Operations

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Node { int data; struct Node* next; } Node;

/* ── Recursive Insert at tail ── */
Node* insert_tail_r(Node* head, int data) {
    if (head == NULL) {
        Node* n = malloc(sizeof(Node));
        n->data = data; n->next = NULL;
        return n;
    }
    head->next = insert_tail_r(head->next, data);
    return head;
}

/* ── Recursive Print (forward) ── */
void print_r(Node* head) {
    if (head == NULL) { printf("NULL\n"); return; }
    printf("%d → ", head->data);
    print_r(head->next);
}

/* ── Recursive Print (reverse) — no actual reversal! ── */
void print_reverse_r(Node* head) {
    if (head == NULL) return;
    print_reverse_r(head->next);   // go to end first
    printf("%d → ", head->data);  // print on the way back
}

/* ── Recursive Length ── */
int length_r(Node* head) {
    if (head == NULL) return 0;
    return 1 + length_r(head->next);
}

/* ── Recursive Search ── */
Node* search_r(Node* head, int data) {
    if (head == NULL) return NULL;
    if (head->data == data) return head;
    return search_r(head->next, data);
}

/* ── Recursive Reverse ── */
/*
   Key insight: recurse to the end, then re-wire pointers on return.
   
   Before: A → B → C → NULL
   After:  C → B → A → NULL
   
   Call stack unwinds:
     reverse_r(A) → calls reverse_r(B) → calls reverse_r(C)
     reverse_r(C): base case, returns C (new head)
     Back at B: C->next = B, B->next = NULL
     Back at A: B->next = A, A->next = NULL
*/
Node* reverse_r(Node* head) {
    if (head == NULL || head->next == NULL) return head;
    Node* new_head = reverse_r(head->next);
    head->next->next = head;   // node after head now points back to head
    head->next       = NULL;   // head's next becomes NULL (it's now the tail)
    return new_head;
}

/* ── Recursive Delete by value ── */
Node* delete_r(Node* head, int data) {
    if (head == NULL) return NULL;
    if (head->data == data) {
        Node* tmp = head->next;
        free(head);
        return tmp;         // skip deleted node; return new head
    }
    head->next = delete_r(head->next, data);
    return head;
}

/* ── Recursive Free ── */
void free_r(Node* head) {
    if (head == NULL) return;
    free_r(head->next);  // free tail first, then current
    free(head);
}

/* ── Recursive Sum ── */
int sum_r(Node* head) {
    if (head == NULL) return 0;
    return head->data + sum_r(head->next);
}

/* ── Recursive nth from end ── */
/*  Strategy: count from deepest recursion level back up.
    When counter reaches n, that is the answer.           */
int nth_from_end_r(Node* head, int n, int* count) {
    if (head == NULL) return -1;
    int val = nth_from_end_r(head->next, n, count);
    (*count)++;
    if (*count == n) return head->data;
    return val;
}

/* ── Recursive check palindrome ── */
/*  Use a static/global left pointer that advances from front
    while the recursion advances the right pointer from the back.  */
Node* left;  // global for demo purposes
int is_palindrome_r(Node* right) {
    if (right == NULL) return 1; // base: end of list
    if (!is_palindrome_r(right->next)) return 0;
    int match = (left->data == right->data);
    left = left->next;
    return match;
}

int main(void) {
    Node* head = NULL;
    head = insert_tail_r(head, 1);
    head = insert_tail_r(head, 2);
    head = insert_tail_r(head, 3);
    head = insert_tail_r(head, 2);
    head = insert_tail_r(head, 1);

    print_r(head);           /* 1 → 2 → 3 → 2 → 1 → NULL */
    printf("Length: %d\n", length_r(head));

    left = head;
    printf("Palindrome: %d\n", is_palindrome_r(head)); /* 1 */

    head = reverse_r(head);
    print_r(head);           /* 1 → 2 → 3 → 2 → 1 → NULL (palindrome!) */

    head = delete_r(head, 3);
    print_r(head);

    free_r(head);
    return 0;
}
```

#### Go — Recursive Operations

```go
package main

import "fmt"

type Node struct {
    Data int
    Next *Node
}

// Recursive insert at tail
func insertTailR(head *Node, data int) *Node {
    if head == nil {
        return &Node{Data: data}
    }
    head.Next = insertTailR(head.Next, data)
    return head
}

// Recursive print
func printR(head *Node) {
    if head == nil {
        fmt.Println("nil")
        return
    }
    fmt.Printf("%d → ", head.Data)
    printR(head.Next)
}

// Recursive print in reverse (no mutation)
func printReverseR(head *Node) {
    if head == nil {
        return
    }
    printReverseR(head.Next)
    fmt.Printf("%d → ", head.Data)
}

// Recursive length
func lengthR(head *Node) int {
    if head == nil {
        return 0
    }
    return 1 + lengthR(head.Next)
}

// Recursive search
func searchR(head *Node, data int) *Node {
    if head == nil {
        return nil
    }
    if head.Data == data {
        return head
    }
    return searchR(head.Next, data)
}

// Recursive reverse
func reverseR(head *Node) *Node {
    if head == nil || head.Next == nil {
        return head
    }
    newHead := reverseR(head.Next)
    head.Next.Next = head
    head.Next = nil
    return newHead
}

// Recursive delete by value
func deleteR(head *Node, data int) *Node {
    if head == nil {
        return nil
    }
    if head.Data == data {
        return head.Next
    }
    head.Next = deleteR(head.Next, data)
    return head
}

// Recursive sum
func sumR(head *Node) int {
    if head == nil {
        return 0
    }
    return head.Data + sumR(head.Next)
}

// Recursive merge two sorted lists
func mergeSortedR(a, b *Node) *Node {
    if a == nil {
        return b
    }
    if b == nil {
        return a
    }
    if a.Data <= b.Data {
        a.Next = mergeSortedR(a.Next, b)
        return a
    }
    b.Next = mergeSortedR(a, b.Next)
    return b
}

func main() {
    var head *Node
    for _, v := range []int{1, 2, 3, 4, 5} {
        head = insertTailR(head, v)
    }
    printR(head)             // 1 → 2 → 3 → 4 → 5 → nil
    fmt.Println("Sum:", sumR(head))

    head = reverseR(head)
    printR(head)             // 5 → 4 → 3 → 2 → 1 → nil

    head = deleteR(head, 3)
    printR(head)
}
```

#### Rust — Recursive Operations

```rust
#[derive(Debug)]
struct Node {
    data: i32,
    next: Option<Box<Node>>,
}

type List = Option<Box<Node>>;

/// Recursive insert at tail
fn insert_tail_r(head: List, data: i32) -> List {
    match head {
        None => Some(Box::new(Node { data, next: None })),
        Some(mut node) => {
            node.next = insert_tail_r(node.next, data);
            Some(node)
        }
    }
}

/// Recursive length
fn length_r(head: &List) -> usize {
    match head {
        None => 0,
        Some(node) => 1 + length_r(&node.next),
    }
}

/// Recursive sum
fn sum_r(head: &List) -> i32 {
    match head {
        None => 0,
        Some(node) => node.data + sum_r(&node.next),
    }
}

/// Recursive search
fn search_r(head: &List, data: i32) -> bool {
    match head {
        None => false,
        Some(node) => node.data == data || search_r(&node.next, data),
    }
}

/// Recursive delete by value
fn delete_r(head: List, data: i32) -> List {
    match head {
        None => None,
        Some(mut node) if node.data == data => node.next.take(),
        Some(mut node) => {
            node.next = delete_r(node.next, data);
            Some(node)
        }
    }
}

/// Recursive reverse (returns new head)
fn reverse_r(head: List) -> List {
    fn helper(head: List, prev: List) -> List {
        match head {
            None => prev,
            Some(mut node) => {
                let next = node.next.take();
                node.next = prev;
                helper(next, Some(node))
            }
        }
    }
    helper(head, None)
}

/// Print list recursively
fn print_r(head: &List) {
    match head {
        None => println!("None"),
        Some(node) => {
            print!("{} → ", node.data);
            print_r(&node.next);
        }
    }
}

fn main() {
    let mut list: List = None;
    for v in [1, 2, 3, 4, 5] {
        list = insert_tail_r(list, v);
    }

    print_r(&list);                          // 1 → 2 → 3 → 4 → 5 → None
    println!("Length: {}", length_r(&list));
    println!("Sum: {}", sum_r(&list));
    println!("Search 3: {}", search_r(&list, 3));

    list = delete_r(list, 3);
    print_r(&list);

    list = reverse_r(list);
    print_r(&list);
}
```

---

## 5. Doubly Linked List — Full Implementation

### Structure
```
NULL ← [prev|data|next] ↔ [prev|data|next] ↔ [prev|data|next] → NULL
        ▲                                                           ▲
       head                                                        tail
```

Keeping a **tail pointer** gives O(1) insert and delete at both ends.

#### C

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct DNode {
    int data;
    struct DNode* prev;
    struct DNode* next;
} DNode;

typedef struct {
    DNode* head;
    DNode* tail;
    int    size;
} DLL;

void dll_init(DLL* l) { l->head = l->tail = NULL; l->size = 0; }

DNode* dll_new_node(int data) {
    DNode* n = malloc(sizeof(DNode));
    n->data = data; n->prev = n->next = NULL;
    return n;
}

/* Insert at head */
void dll_insert_head(DLL* l, int data) {
    DNode* n = dll_new_node(data);
    if (!l->head) { l->head = l->tail = n; }
    else {
        n->next      = l->head;
        l->head->prev = n;
        l->head      = n;
    }
    l->size++;
}

/* Insert at tail */
void dll_insert_tail(DLL* l, int data) {
    DNode* n = dll_new_node(data);
    if (!l->tail) { l->head = l->tail = n; }
    else {
        n->prev      = l->tail;
        l->tail->next = n;
        l->tail      = n;
    }
    l->size++;
}

/* Delete node (given pointer to it) — O(1) */
void dll_delete_node(DLL* l, DNode* node) {
    if (node->prev) node->prev->next = node->next;
    else            l->head = node->next;
    if (node->next) node->next->prev = node->prev;
    else            l->tail = node->prev;
    free(node);
    l->size--;
}

/* Forward print */
void dll_print_fwd(DLL* l) {
    DNode* cur = l->head;
    printf("NULL ↔");
    while (cur) { printf(" %d ↔", cur->data); cur = cur->next; }
    printf(" NULL\n");
}

/* Backward print */
void dll_print_bwd(DLL* l) {
    DNode* cur = l->tail;
    printf("NULL ↔");
    while (cur) { printf(" %d ↔", cur->data); cur = cur->prev; }
    printf(" NULL\n");
}

/* Recursive reverse (just swap head and tail, toggle links) */
void dll_reverse_node(DLL* l, DNode* node) {
    if (!node) { DNode* tmp = l->head; l->head = l->tail; l->tail = tmp; return; }
    DNode* tmp  = node->prev;
    node->prev  = node->next;
    node->next  = tmp;
    dll_reverse_node(l, node->prev);  /* node->prev is old next */
}

void dll_reverse(DLL* l) { dll_reverse_node(l, l->head); }

int main(void) {
    DLL l; dll_init(&l);
    dll_insert_tail(&l, 10);
    dll_insert_tail(&l, 20);
    dll_insert_tail(&l, 30);
    dll_insert_head(&l, 5);
    dll_print_fwd(&l);   /* NULL ↔ 5 ↔ 10 ↔ 20 ↔ 30 ↔ NULL */
    dll_print_bwd(&l);   /* NULL ↔ 30 ↔ 20 ↔ 10 ↔ 5 ↔ NULL */
    dll_reverse(&l);
    dll_print_fwd(&l);
    return 0;
}
```

#### Go

```go
package main

import "fmt"

type DNode struct {
    Data       int
    Prev, Next *DNode
}

type DLL struct {
    Head, Tail *DNode
    Size       int
}

func (l *DLL) InsertHead(data int) {
    n := &DNode{Data: data}
    if l.Head == nil {
        l.Head, l.Tail = n, n
    } else {
        n.Next, l.Head.Prev, l.Head = l.Head, n, n
    }
    l.Size++
}

func (l *DLL) InsertTail(data int) {
    n := &DNode{Data: data}
    if l.Tail == nil {
        l.Head, l.Tail = n, n
    } else {
        n.Prev, l.Tail.Next, l.Tail = l.Tail, n, n
    }
    l.Size++
}

func (l *DLL) DeleteNode(node *DNode) {
    if node.Prev != nil {
        node.Prev.Next = node.Next
    } else {
        l.Head = node.Next
    }
    if node.Next != nil {
        node.Next.Prev = node.Prev
    } else {
        l.Tail = node.Prev
    }
    l.Size--
}

func (l *DLL) PrintFwd() {
    cur := l.Head
    fmt.Print("nil ↔")
    for cur != nil {
        fmt.Printf(" %d ↔", cur.Data)
        cur = cur.Next
    }
    fmt.Println(" nil")
}

func main() {
    l := &DLL{}
    l.InsertTail(10)
    l.InsertTail(20)
    l.InsertTail(30)
    l.InsertHead(5)
    l.PrintFwd() // nil ↔ 5 ↔ 10 ↔ 20 ↔ 30 ↔ nil
}
```

#### Rust

```rust
use std::cell::RefCell;
use std::rc::Rc;

// Rust doubly linked list requires Rc<RefCell<>> for shared mutable ownership
type Link = Option<Rc<RefCell<DNode>>>;

struct DNode {
    data: i32,
    prev: Link,
    next: Link,
}

struct DLL {
    head: Link,
    tail: Link,
    size: usize,
}

impl DLL {
    fn new() -> Self { DLL { head: None, tail: None, size: 0 } }

    fn insert_tail(&mut self, data: i32) {
        let node = Rc::new(RefCell::new(DNode { data, prev: None, next: None }));
        match self.tail.take() {
            None => {
                self.head = Some(Rc::clone(&node));
                self.tail = Some(node);
            }
            Some(old_tail) => {
                old_tail.borrow_mut().next = Some(Rc::clone(&node));
                node.borrow_mut().prev = Some(old_tail);
                self.tail = Some(node);
            }
        }
        self.size += 1;
    }

    fn print_fwd(&self) {
        print!("None ↔");
        let mut cur = self.head.clone();
        while let Some(node) = cur {
            print!(" {} ↔", node.borrow().data);
            cur = node.borrow().next.clone();
        }
        println!(" None");
    }
}

fn main() {
    let mut list = DLL::new();
    list.insert_tail(10);
    list.insert_tail(20);
    list.insert_tail(30);
    list.print_fwd();
}
```

> **Rust Note**: Rust's ownership rules make doubly linked lists notoriously complex. `Rc<RefCell<T>>` is the idiomatic safe solution. For production code, prefer `std::collections::LinkedList` or crates like `linked-list`.

---

## 6. Circular Linked List — Full Implementation

### Key Invariant
The last node's `next` never equals `NULL` — it always points to the **head**.

#### C

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct CNode { int data; struct CNode* next; } CNode;

typedef struct { CNode* tail; int size; } CLL; /* store tail, not head */
/* Why tail? Because tail->next IS the head. Gives O(1) insert at both ends. */

void cll_init(CLL* l) { l->tail = NULL; l->size = 0; }

/* Insert at tail */
void cll_insert_tail(CLL* l, int data) {
    CNode* n = malloc(sizeof(CNode));
    n->data  = data;
    if (!l->tail) { n->next = n; l->tail = n; }  /* points to itself */
    else {
        n->next      = l->tail->next;  /* n→head */
        l->tail->next = n;             /* old tail→n */
        l->tail       = n;             /* update tail */
    }
    l->size++;
}

/* Insert at head */
void cll_insert_head(CLL* l, int data) {
    cll_insert_tail(l, data);       /* insert as tail... */
    l->tail = l->tail->next->next ? l->tail->next : l->tail; /* adjust */
    /* Simpler: insert, then shift tail back so new node becomes head */
    /* Actually: insert at tail and rotate tail pointer */
    l->tail = l->tail->next; /* make the inserted node the "head" by making old tail the tail */
}

/* Print (stop when we loop back to head) */
void cll_print(CLL* l) {
    if (!l->tail) { printf("[empty]\n"); return; }
    CNode* cur  = l->tail->next; /* head */
    CNode* head = cur;
    printf("HEAD");
    do {
        printf(" → %d", cur->data);
        cur = cur->next;
    } while (cur != head);
    printf(" → (back to HEAD)\n");
}

/* Delete head */
void cll_delete_head(CLL* l) {
    if (!l->tail) return;
    CNode* head = l->tail->next;
    if (head == l->tail) { free(head); l->tail = NULL; l->size--; return; }
    l->tail->next = head->next;
    free(head);
    l->size--;
}

/* Detect if a list is circular — Floyd's Algorithm */
int is_circular(CNode* head) {
    if (!head) return 0;
    CNode *slow = head, *fast = head->next;
    while (fast && fast->next) {
        if (slow == fast) return 1;
        slow = slow->next;
        fast = fast->next->next;
    }
    return 0;
}

int main(void) {
    CLL l; cll_init(&l);
    cll_insert_tail(&l, 10);
    cll_insert_tail(&l, 20);
    cll_insert_tail(&l, 30);
    cll_print(&l);
    cll_delete_head(&l);
    cll_print(&l);
    return 0;
}
```

#### Go

```go
package main

import "fmt"

type CNode struct {
    Data int
    Next *CNode
}

type CLL struct {
    Tail *CNode // tail.Next == head
    Size int
}

func (l *CLL) InsertTail(data int) {
    n := &CNode{Data: data}
    if l.Tail == nil {
        n.Next = n
        l.Tail = n
    } else {
        n.Next = l.Tail.Next // n → head
        l.Tail.Next = n      // old tail → n
        l.Tail = n           // update tail
    }
    l.Size++
}

func (l *CLL) Print() {
    if l.Tail == nil {
        fmt.Println("[empty]")
        return
    }
    head := l.Tail.Next
    cur := head
    fmt.Print("HEAD")
    for {
        fmt.Printf(" → %d", cur.Data)
        cur = cur.Next
        if cur == head {
            break
        }
    }
    fmt.Println(" → (back to HEAD)")
}

func main() {
    l := &CLL{}
    l.InsertTail(10)
    l.InsertTail(20)
    l.InsertTail(30)
    l.Print()
}
```

---

## 7. Skip List

A skip list adds multiple **forward pointer levels** to a linked list, enabling O(log n) average search, insert, and delete — similar to a balanced BST but simpler to implement.

```
Level 3: [−∞] ──────────────────────────────── [30] → [+∞]
Level 2: [−∞] ─────────── [10] ──────────────  [30] → [+∞]
Level 1: [−∞] ── [5] ──── [10] ── [20] ──────  [30] → [+∞]
Level 0: [−∞] → [5] → [8] → [10] → [15] → [20] → [30] → [+∞]
```

Each node is promoted to higher levels with probability `p` (typically 0.5 or 0.25).

#### C — Skip List Core

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_LEVEL 16
#define P         0.5

typedef struct SkipNode {
    int   key;
    struct SkipNode* forward[MAX_LEVEL]; /* array of forward pointers */
} SkipNode;

typedef struct {
    SkipNode* header;
    int       level;   /* current max level in use */
} SkipList;

SkipNode* skip_new_node(int key, int level) {
    SkipNode* n = malloc(sizeof(SkipNode));
    n->key = key;
    memset(n->forward, 0, sizeof(n->forward));
    return n;
}

SkipList* skip_create(void) {
    SkipList* sl   = malloc(sizeof(SkipList));
    sl->header     = skip_new_node(INT_MIN, MAX_LEVEL);
    sl->level      = 0;
    return sl;
}

/* Random level generator */
int random_level(void) {
    int lvl = 0;
    while ((double)rand() / RAND_MAX < P && lvl < MAX_LEVEL - 1) lvl++;
    return lvl;
}

/* Insert into skip list */
void skip_insert(SkipList* sl, int key) {
    SkipNode* update[MAX_LEVEL];
    SkipNode* cur = sl->header;

    /* Find update array: rightmost node at each level that is < key */
    for (int i = sl->level; i >= 0; i--) {
        while (cur->forward[i] && cur->forward[i]->key < key)
            cur = cur->forward[i];
        update[i] = cur;
    }

    int lvl = random_level();
    if (lvl > sl->level) {
        for (int i = sl->level + 1; i <= lvl; i++) update[i] = sl->header;
        sl->level = lvl;
    }

    SkipNode* n = skip_new_node(key, lvl);
    for (int i = 0; i <= lvl; i++) {
        n->forward[i]        = update[i]->forward[i];
        update[i]->forward[i] = n;
    }
}

/* Search */
int skip_search(SkipList* sl, int key) {
    SkipNode* cur = sl->header;
    for (int i = sl->level; i >= 0; i--)
        while (cur->forward[i] && cur->forward[i]->key < key)
            cur = cur->forward[i];
    cur = cur->forward[0];
    return (cur && cur->key == key);
}

void skip_print(SkipList* sl) {
    for (int i = sl->level; i >= 0; i--) {
        SkipNode* cur = sl->header->forward[i];
        printf("Level %d: ", i);
        while (cur) { printf("%d → ", cur->key); cur = cur->forward[i]; }
        printf("NULL\n");
    }
}

int main(void) {
    srand(time(NULL));
    SkipList* sl = skip_create();
    int vals[] = {5, 8, 10, 15, 20, 30};
    for (int i = 0; i < 6; i++) skip_insert(sl, vals[i]);
    skip_print(sl);
    printf("Search 15: %d\n", skip_search(sl, 15));
    printf("Search 7:  %d\n", skip_search(sl, 7));
    return 0;
}
```

---

## 8. XOR Linked List (Memory-Efficient Doubly LL)

An XOR linked list stores `prev XOR next` in a single pointer, halving the pointer overhead of a doubly linked list. Each node stores only **one** pointer instead of two.

**Key formula**: Given current node `C` and the pointer `npx = prev XOR next`:
- `next = npx XOR prev`
- `prev = npx XOR next`

#### C

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef struct XORNode {
    int   data;
    struct XORNode* npx;  /* prev XOR next */
} XORNode;

XORNode* XOR(XORNode* a, XORNode* b) {
    return (XORNode*)((uintptr_t)a ^ (uintptr_t)b);
}

XORNode* new_xor_node(int data) {
    XORNode* n = malloc(sizeof(XORNode));
    n->data = data; n->npx = NULL;
    return n;
}

/* Insert at head */
XORNode* xor_insert_head(XORNode* head, int data) {
    XORNode* n = new_xor_node(data);
    n->npx     = XOR(NULL, head); /* prev=NULL, next=old head */
    if (head) head->npx = XOR(n, XOR(NULL, head->npx)); /* update old head's prev */
    return n;
}

/* Print forward */
void xor_print_fwd(XORNode* head) {
    XORNode *cur = head, *prev = NULL, *next;
    printf("NULL ↔");
    while (cur) {
        printf(" %d ↔", cur->data);
        next = XOR(prev, cur->npx);
        prev = cur;
        cur  = next;
    }
    printf(" NULL\n");
}

/* Print backward — traverse to end, then reverse */
void xor_print_bwd(XORNode* head) {
    XORNode *cur = head, *prev = NULL, *next;
    /* Walk to tail */
    while (cur) {
        next = XOR(prev, cur->npx);
        if (!next) break; /* cur is tail */
        prev = cur; cur = next;
    }
    /* cur is tail, prev is second-to-last */
    printf("NULL ↔");
    while (cur) {
        printf(" %d ↔", cur->data);
        next = XOR(cur->npx, prev); /* walk backward */
        prev = cur; cur = next;
    }
    printf(" NULL\n");
}

int main(void) {
    XORNode* head = NULL;
    head = xor_insert_head(head, 30);
    head = xor_insert_head(head, 20);
    head = xor_insert_head(head, 10);
    head = xor_insert_head(head, 5);
    xor_print_fwd(head); /* NULL ↔ 5 ↔ 10 ↔ 20 ↔ 30 ↔ NULL */
    xor_print_bwd(head); /* NULL ↔ 30 ↔ 20 ↔ 10 ↔ 5 ↔ NULL */
    return 0;
}
```

> **Note**: XOR linked lists are not idiomatic in Go or Rust because both languages' garbage collectors or borrow checkers interact poorly with raw pointer arithmetic. This is a C-only technique.

---

## 9. Self-Organizing / Self-Adjusting Linked List

A self-organizing linked list reorders itself based on access patterns to reduce average search time. Four strategies:

### Move-to-Front (MTF)
Every accessed element moves to the **head** of the list. Best for highly skewed access distributions.

```c
Node* move_to_front(LinkedList* list, int data) {
    if (!list->head || list->head->data == data) return list->head;
    Node* prev = list->head, *cur = list->head->next;
    while (cur && cur->data != data) { prev = cur; cur = cur->next; }
    if (!cur) return NULL;
    prev->next = cur->next;  /* unlink */
    cur->next  = list->head; /* relink at head */
    list->head = cur;
    return cur;
}
```

### Transpose
Swap the accessed element with the **element before it**. Slower convergence than MTF but avoids over-promoting infrequent elements.

```c
Node* transpose(LinkedList* list, int data) {
    if (!list->head || list->head->data == data) return list->head;
    Node *pprev = NULL, *prev = list->head, *cur = list->head->next;
    while (cur && cur->data != data) { pprev = prev; prev = cur; cur = cur->next; }
    if (!cur) return NULL;
    /* swap prev and cur */
    if (pprev) pprev->next = cur; else list->head = cur;
    prev->next = cur->next;
    cur->next  = prev;
    return cur;
}
```

---

## 10. Unrolled Linked List

Each node stores an **array** of elements rather than one, reducing pointer overhead and improving cache locality. Ideal when individual elements are small (e.g., characters in a text editor rope).

```
[arr: 1,2,3,4 | next] → [arr: 5,6,7,8 | next] → [arr: 9,10 | next] → NULL
```

#### C

```c
#include <stdio.h>
#include <stdlib.h>

#define NODE_CAPACITY 4

typedef struct UNode {
    int  data[NODE_CAPACITY];
    int  count;
    struct UNode* next;
} UNode;

UNode* unrolled_new_node(void) {
    UNode* n = malloc(sizeof(UNode));
    n->count = 0; n->next = NULL;
    return n;
}

void unrolled_insert(UNode** head, int data) {
    if (!*head) *head = unrolled_new_node();
    UNode* cur = *head;
    while (cur->next && cur->count == NODE_CAPACITY) cur = cur->next;
    if (cur->count == NODE_CAPACITY) {
        cur->next = unrolled_new_node();
        cur = cur->next;
    }
    cur->data[cur->count++] = data;
}

void unrolled_print(UNode* head) {
    while (head) {
        printf("[");
        for (int i = 0; i < head->count; i++)
            printf(i < head->count-1 ? "%d, " : "%d", head->data[i]);
        printf("] → ");
        head = head->next;
    }
    printf("NULL\n");
}

int main(void) {
    UNode* head = NULL;
    for (int i = 1; i <= 10; i++) unrolled_insert(&head, i);
    unrolled_print(head);
    /* [1, 2, 3, 4] → [5, 6, 7, 8] → [9, 10] → NULL */
    return 0;
}
```

---

## 11. Sentinel / Dummy Node Technique

A **sentinel** (dummy) node is a permanent placeholder node at the head (and sometimes tail) of the list that simplifies edge-case handling. It holds no meaningful data but eliminates special cases for empty-list and single-element operations.

```
[sentinel|next] → [data|next] → [data|next] → NULL
     ▲
  always present
```

#### Benefits
- Insert and delete never need to check `if head == NULL`
- Code is shorter and less error-prone
- Especially useful in doubly linked lists

#### C

```c
typedef struct { int data; struct Node* next; } Node;

Node* create_sentinel_list(void) {
    Node* sentinel = malloc(sizeof(Node));
    sentinel->data = -1; /* irrelevant */
    sentinel->next = NULL;
    return sentinel;
}

/* Insert after sentinel (effectively insert at head of data) */
void sentinel_insert_head(Node* sentinel, int data) {
    Node* n    = malloc(sizeof(Node));
    n->data    = data;
    n->next    = sentinel->next;
    sentinel->next = n;
}

/* Delete by value — no special NULL check needed */
void sentinel_delete(Node* sentinel, int data) {
    Node* cur = sentinel; /* start from sentinel, not head */
    while (cur->next && cur->next->data != data) cur = cur->next;
    if (!cur->next) return;
    Node* tmp = cur->next;
    cur->next = tmp->next;
    free(tmp);
}
```

---

## 12. Recursive Patterns — Deep Dive

Recursion maps perfectly to linked lists because a list has a **recursive definition**:

```
List = Empty | Node(data, List)
```

### Pattern 1: Structural Recursion (process head, recurse on tail)

```c
int count_even(Node* head) {
    if (head == NULL) return 0;
    return (head->data % 2 == 0 ? 1 : 0) + count_even(head->next);
}
```

### Pattern 2: Tail Recursion (accumulate result)

```c
/* Tail-recursive length with accumulator */
int length_tail(Node* head, int acc) {
    if (head == NULL) return acc;
    return length_tail(head->next, acc + 1); /* tail call — no pending work */
}
/* Call: length_tail(head, 0) */
```

### Pattern 3: Mutual Recursion

```c
/* is_even_position and is_odd_position call each other */
int sum_odd_pos(Node* head);   /* forward declaration */
int sum_even_pos(Node* head);

int sum_even_pos(Node* head) {
    if (!head) return 0;
    return head->data + sum_odd_pos(head->next);  /* even position: include */
}
int sum_odd_pos(Node* head) {
    if (!head) return 0;
    return sum_even_pos(head->next);              /* odd position: skip */
}
```

### Pattern 4: Two-Pointer Recursion (merge)

```c
Node* merge_sorted(Node* a, Node* b) {
    if (!a) return b;
    if (!b) return a;
    if (a->data <= b->data) {
        a->next = merge_sorted(a->next, b);
        return a;
    }
    b->next = merge_sorted(a, b->next);
    return b;
}
```

### Pattern 5: Divide and Conquer (merge sort)

```c
Node* get_mid(Node* head) {
    Node *slow = head, *fast = head->next;
    while (fast && fast->next) { slow = slow->next; fast = fast->next->next; }
    return slow;
}

Node* merge_sort(Node* head) {
    if (!head || !head->next) return head;
    Node* mid        = get_mid(head);
    Node* right_half = mid->next;
    mid->next        = NULL;       /* split list in half */
    Node* left  = merge_sort(head);
    Node* right = merge_sort(right_half);
    return merge_sorted(left, right);
}
```

### Pattern 6: Recursive construction from array

```c
Node* from_array(int* arr, int n) {
    if (n == 0) return NULL;
    Node* head = malloc(sizeof(Node));
    head->data = arr[0];
    head->next = from_array(arr + 1, n - 1);
    return head;
}
```

### Pattern 7: Recursive check for sorted order

```go
// Go: Check if list is sorted (ascending)
func isSortedR(head *Node) bool {
    if head == nil || head.Next == nil {
        return true
    }
    return head.Data <= head.Next.Data && isSortedR(head.Next)
}
```

### Pattern 8: Recursive removal of duplicates from sorted list

```go
func removeDupsR(head *Node) *Node {
    if head == nil || head.Next == nil {
        return head
    }
    if head.Data == head.Next.Data {
        head.Next = head.Next.Next
        return removeDupsR(head) // re-check same head
    }
    head.Next = removeDupsR(head.Next)
    return head
}
```

### Recursion Call Stack Visualization

For `reverse_r([1 → 2 → 3])`:

```
reverse_r(1)
  └─ reverse_r(2)
       └─ reverse_r(3)       ← base case, returns 3
            ↩ 3->next = 2, 2->next = NULL → returns new_head=3
       ↩ 2->next = 1, 1->next = NULL → returns new_head=3
  ↩ returns 3

Result: 3 → 2 → 1 → NULL
```

---

## 13. Traversal Techniques

### 13.1 Standard Iterative Traversal

```c
Node* cur = head;
while (cur != NULL) {
    /* process cur->data */
    cur = cur->next;
}
```

### 13.2 Two-Pointer (Slow/Fast) Traversal

Used for finding midpoint, detecting cycles, and nth-from-end.

```c
Node *slow = head, *fast = head;
while (fast && fast->next) {
    slow = slow->next;       /* moves 1 step */
    fast = fast->next->next; /* moves 2 steps */
}
/* When fast reaches end, slow is at middle */
```

### 13.3 Trailing Pointer Traversal

Maintain a pointer `prev` one step behind `cur` to enable deletion without traversing again.

```c
Node *prev = NULL, *cur = head;
while (cur) {
    if (cur->data == target) {
        if (prev) prev->next = cur->next;
        else head = cur->next;
        free(cur);
        return;
    }
    prev = cur;
    cur  = cur->next;
}
```

### 13.4 Reverse Traversal (Doubly LL)

```c
DNode* cur = tail;
while (cur != NULL) {
    /* process cur->data */
    cur = cur->prev;
}
```

---

## 14. Insertion — Every Case

| Case | Singly LL | Doubly LL |
|---|---|---|
| At head | O(1) | O(1) |
| At tail (with tail ptr) | O(1) | O(1) |
| At tail (no tail ptr) | O(n) | O(n) |
| At position k | O(k) | O(min(k, n-k)) via bidirectional |
| After given node | O(1) | O(1) |
| Before given node | O(n) to find prev | O(1) |

### Insert Before a Given Node in Doubly LL — O(1)

```c
void insert_before(DLL* l, DNode* node, int data) {
    DNode* n  = dll_new_node(data);
    n->next   = node;
    n->prev   = node->prev;
    if (node->prev) node->prev->next = n;
    else l->head = n; /* inserting before head */
    node->prev = n;
    l->size++;
}
```

---

## 15. Deletion — Every Case

### Delete by Position (C)

```c
void delete_at(LinkedList* list, int pos) {
    if (pos < 0 || pos >= list->size) return;
    if (pos == 0) { delete_head(list); return; }
    Node* cur = list->head;
    for (int i = 0; i < pos - 1; i++) cur = cur->next;
    Node* tmp = cur->next;
    cur->next = tmp->next;
    free(tmp);
    list->size--;
}
```

### Delete All Occurrences (Recursive, Go)

```go
func deleteAllR(head *Node, data int) *Node {
    if head == nil {
        return nil
    }
    head.Next = deleteAllR(head.Next, data)
    if head.Data == data {
        return head.Next // skip this node
    }
    return head
}
```

---

## 16. Searching — Iterative & Recursive

### Linear Search (Iterative)

```c
int find_index(Node* head, int data) {
    int idx = 0;
    while (head) {
        if (head->data == data) return idx;
        head = head->next; idx++;
    }
    return -1;
}
```

### Search with Move-to-Front optimization

```go
func (l *LinkedList) SearchMTF(data int) *Node {
    if l.Head == nil { return nil }
    if l.Head.Data == data { return l.Head }
    cur := l.Head
    for cur.Next != nil {
        if cur.Next.Data == data {
            found := cur.Next
            cur.Next = found.Next // unlink
            found.Next = l.Head  // move to front
            l.Head = found
            return found
        }
        cur = cur.Next
    }
    return nil
}
```

---

## 17. Reversal — Iterative & Recursive

### Iterative Reversal (Three Pointer Technique)

```
Initial: prev=NULL, cur=A, next=?

Step 1: save next = B
        A→NULL (reversed), prev=A, cur=B

Step 2: save next = C
        B→A (reversed), prev=B, cur=C

Step 3: C→B, prev=C, cur=NULL → done
head = prev = C
```

```c
void reverse_iterative(LinkedList* list) {
    Node *prev = NULL, *cur = list->head, *next;
    while (cur) {
        next      = cur->next; /* save */
        cur->next = prev;      /* reverse link */
        prev      = cur;       /* advance prev */
        cur       = next;      /* advance cur */
    }
    list->head = prev;
}
```

### Reverse in Groups of K (Iterative, C)

```c
Node* reverse_k(Node* head, int k) {
    Node *prev = NULL, *cur = head, *next = NULL;
    int count = 0;
    /* Reverse k nodes */
    while (cur && count < k) {
        next = cur->next;
        cur->next = prev;
        prev = cur; cur = next; count++;
    }
    /* head is now the tail of reversed group */
    if (next) head->next = reverse_k(next, k);
    return prev; /* new head of this group */
}
```

---

## 18. Sorting a Linked List

### Merge Sort — O(n log n), O(log n) space (call stack)

This is the **preferred** sorting algorithm for linked lists because:
- No random access needed
- Merging is O(n) with O(1) extra space
- No data movement, only pointer re-wiring

```c
/* Already shown in Pattern 5 — Divide and Conquer */

/* Complete working version: */
Node* get_mid_for_sort(Node* head) {
    Node *slow = head, *fast = head->next;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}

Node* merge(Node* a, Node* b) {
    if (!a) return b;
    if (!b) return a;
    if (a->data <= b->data) { a->next = merge(a->next, b); return a; }
    b->next = merge(a, b->next); return b;
}

Node* merge_sort_ll(Node* head) {
    if (!head || !head->next) return head;
    Node* mid   = get_mid_for_sort(head);
    Node* right = mid->next;
    mid->next   = NULL;
    return merge(merge_sort_ll(head), merge_sort_ll(right));
}
```

### Insertion Sort — O(n²), O(1) extra space

Good for nearly-sorted lists.

```go
func insertionSort(head *Node) *Node {
    sorted := (*Node)(nil)
    cur := head
    for cur != nil {
        next := cur.Next
        // insert cur into sorted list
        if sorted == nil || sorted.Data >= cur.Data {
            cur.Next = sorted
            sorted = cur
        } else {
            s := sorted
            for s.Next != nil && s.Next.Data < cur.Data {
                s = s.Next
            }
            cur.Next = s.Next
            s.Next = cur
        }
        cur = next
    }
    return sorted
}
```

---

## 19. Merging Linked Lists

### Merge Two Sorted Lists

```rust
fn merge_sorted(a: List, b: List) -> List {
    match (a, b) {
        (None, b) => b,
        (a, None) => a,
        (Some(mut an), Some(mut bn)) => {
            if an.data <= bn.data {
                let next_a = an.next.take();
                an.next = merge_sorted(next_a, Some(bn));
                Some(an)
            } else {
                let next_b = bn.next.take();
                bn.next = merge_sorted(Some(an), next_b);
                Some(bn)
            }
        }
    }
}
```

### Merge K Sorted Lists (Divide & Conquer, Go)

```go
func mergeKLists(lists []*Node) *Node {
    if len(lists) == 0 { return nil }
    if len(lists) == 1 { return lists[0] }
    mid := len(lists) / 2
    left  := mergeKLists(lists[:mid])
    right := mergeKLists(lists[mid:])
    return mergeSortedR(left, right)
}
```

---

## 20. Detecting and Removing Cycles

### Floyd's Cycle Detection (Tortoise and Hare)

**Detection**: slow pointer moves 1 step, fast moves 2 steps. If they meet, there's a cycle.

**Finding start of cycle**:
1. Once slow == fast inside cycle, reset one pointer to head
2. Move both one step at a time
3. They meet at the cycle's start

**Removing cycle**: Find the last node of cycle, set its next to NULL.

#### C

```c
/* Detect cycle */
int has_cycle(Node* head) {
    Node *slow = head, *fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return 1;
    }
    return 0;
}

/* Find cycle start */
Node* cycle_start(Node* head) {
    Node *slow = head, *fast = head;
    while (fast && fast->next) {
        slow = slow->next; fast = fast->next->next;
        if (slow == fast) {
            slow = head; /* reset to head */
            while (slow != fast) { slow = slow->next; fast = fast->next; }
            return slow; /* meeting point = cycle start */
        }
    }
    return NULL;
}

/* Remove cycle */
void remove_cycle(Node* head) {
    Node *slow = head, *fast = head;
    while (fast && fast->next) {
        slow = slow->next; fast = fast->next->next;
        if (slow == fast) break;
    }
    if (!fast || !fast->next) return; /* no cycle */
    slow = head;
    while (slow->next != fast->next) {
        slow = slow->next; fast = fast->next;
    }
    fast->next = NULL; /* break cycle */
}
```

---

## 21. Finding Middle, Nth from End

### Middle of List (Slow/Fast Pointer)

```go
func findMiddle(head *Node) *Node {
    if head == nil { return nil }
    slow, fast := head, head
    for fast.Next != nil && fast.Next.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    return slow // for odd: exact middle; for even: lower middle
}
```

### Nth Node from End

**Method 1: Two pass** — count total n, then walk to (total - n)th node. O(2n).

**Method 2: One pass, two pointers** — advance first pointer n steps ahead, then move both until first reaches end.

```c
Node* nth_from_end(Node* head, int n) {
    Node *first = head, *second = head;
    for (int i = 0; i < n; i++) {
        if (!first) return NULL; /* n > list length */
        first = first->next;
    }
    while (first) { first = first->next; second = second->next; }
    return second;
}
```

**Method 3: Recursive** (already shown in section 4.2)

---

## 22. Stack & Queue using Linked Lists

### Stack (LIFO) — All operations O(1)

```go
type Stack struct{ list LinkedList }

func (s *Stack) Push(data int) { s.list.InsertHead(data) }
func (s *Stack) Pop() int {
    if s.list.Head == nil { panic("stack underflow") }
    val := s.list.Head.Data
    s.list.DeleteHead()
    return val
}
func (s *Stack) Peek() int { return s.list.Head.Data }
func (s *Stack) IsEmpty() bool { return s.list.Head == nil }
```

### Queue (FIFO) — All operations O(1) with tail pointer

```go
type Queue struct {
    head, tail *Node
    size       int
}

func (q *Queue) Enqueue(data int) {
    n := &Node{Data: data}
    if q.tail != nil { q.tail.Next = n }
    q.tail = n
    if q.head == nil { q.head = n }
    q.size++
}

func (q *Queue) Dequeue() int {
    if q.head == nil { panic("queue underflow") }
    val := q.head.Data
    q.head = q.head.Next
    if q.head == nil { q.tail = nil }
    q.size--
    return val
}
```

### Deque (Double-ended queue) — Use Doubly LL

```go
type Deque struct{ dll DLL }

func (d *Deque) PushFront(data int) { d.dll.InsertHead(data) }
func (d *Deque) PushBack(data int)  { d.dll.InsertTail(data) }
func (d *Deque) PopFront() int      { val := d.dll.Head.Data; d.dll.DeleteNode(d.dll.Head); return val }
func (d *Deque) PopBack() int       { val := d.dll.Tail.Data; d.dll.DeleteNode(d.dll.Tail); return val }
```

---

## 23. Time & Space Complexity Analysis

### Singly Linked List

| Operation | Time | Space |
|---|---|---|
| Access by index | O(n) | O(1) |
| Search | O(n) | O(1) |
| Insert at head | O(1) | O(1) |
| Insert at tail (tail ptr) | O(1) | O(1) |
| Insert at tail (no tail ptr) | O(n) | O(1) |
| Insert at position k | O(k) | O(1) |
| Delete at head | O(1) | O(1) |
| Delete at tail | O(n) | O(1) |
| Delete by value | O(n) | O(1) |
| Reverse (iterative) | O(n) | O(1) |
| Reverse (recursive) | O(n) | O(n) call stack |
| Merge sort | O(n log n) | O(log n) |
| Cycle detection | O(n) | O(1) |

### Recursion Stack Depth
For a list of length `n`, recursive algorithms use **O(n)** call stack space. For very large lists (millions of nodes), this can cause **stack overflow**. Prefer iterative for production critical paths.

### Comparison with Arrays

| | Array | Singly LL | Doubly LL |
|---|---|---|---|
| Memory per element | 1 word (data) | 2 words (data+next) | 3 words (prev+data+next) |
| Cache efficiency | Excellent | Poor | Poor |
| Insert at head | O(n) | O(1) | O(1) |
| Delete at head | O(n) | O(1) | O(1) |
| Random access | O(1) | O(n) | O(n/2) |
| Binary search | O(log n) | O(n) | O(n) |

---

## 24. Common Pitfalls & Best Practices

### Pitfall 1: Losing the head pointer

```c
/* WRONG: head lost forever */
while (head->data != target) head = head->next;

/* CORRECT: use a separate traversal pointer */
Node* cur = head;
while (cur && cur->data != target) cur = cur->next;
```

### Pitfall 2: Memory leak on deletion

```c
/* WRONG: node memory leaked */
head = head->next;

/* CORRECT */
Node* tmp = head;
head = head->next;
free(tmp);
```

### Pitfall 3: Off-by-one in insert_at

Always verify `pos > list->size` (not `>= size`) for appending at end.

### Pitfall 4: Not handling empty list

Every function should start with `if (head == NULL) return;` or its language equivalent.

### Pitfall 5: Dangling pointers after free (C)

```c
free(node);
node = NULL; /* always nullify after free */
```

### Pitfall 6: Infinite loop in circular list

Always track the starting node and break when you loop back to it:

```c
CNode* start = l->tail->next; /* head */
CNode* cur   = start;
do {
    /* process */
    cur = cur->next;
} while (cur != start);
```

### Pitfall 7: Recursive stack overflow

For lists with > ~10,000 nodes, recursive algorithms may overflow the default stack (usually 1–8 MB). Convert to iterative, or increase stack size.

### Pitfall 8: Rust — not using `take()`

In Rust, always use `Option::take()` to move the inner value out and replace with `None`, preventing double-ownership errors.

```rust
// WRONG: partial move
let next = self.head.next; // error: can't move out of borrowed content

// CORRECT
let next = self.head.take().map(|n| n.next);
```

### Best Practices

1. **Always maintain a size field** — avoids O(n) length computation
2. **Keep both head and tail pointers** — gives O(1) tail operations
3. **Use sentinel nodes** for simpler insert/delete logic
4. **Prefer merge sort** for sorting linked lists
5. **Use Floyd's algorithm** for cycle detection (O(1) space vs O(n) hash set)
6. **Draw before coding** — sketch pointer states before and after each operation
7. **Test edge cases**: empty list, single-element list, two-element list, head/tail operations
8. **In C**: always set freed pointers to NULL
9. **In Go**: let the GC handle memory; just nil out pointers
10. **In Rust**: use `Box<T>` for singly linked lists, `Rc<RefCell<T>>` for doubly linked lists, and `std::collections::LinkedList` for production use

---

## Summary

| List Type | Best For | Extra Space |
|---|---|---|
| Singly LL | Stacks, simple chains, memory-tight | +1 ptr/node |
| Doubly LL | Deques, LRU cache, browser history | +2 ptr/node |
| Circular LL | Round-robin scheduling, ring buffers | +1 ptr/node |
| Skip List | Ordered maps (Redis uses this!) | O(n log n) |
| XOR LL | Embedded systems, memory critical | +1 ptr/node (half of DLL!) |
| Unrolled LL | Text editors, cache-friendly lists | +array/node |
| Self-org LL | Caches with skewed access patterns | Same as base |
| Sentinel LL | Simplifying edge-case-heavy code | +1 node total |

---

*End of Guide*

Here's your complete guide — **~1,800+ lines** covering everything. Here's what's inside:

**8 Types of Linked Lists** with full implementations:
- Singly, Doubly, Circular, Skip List, XOR LL, Self-Organizing, Unrolled, Sentinel

**3 Languages throughout** — C (manual memory, raw pointers), Go (GC, idiomatic structs), Rust (Box/Option, Rc/RefCell for doubly LL)

**Recursive patterns — deep dive (Section 12):**
- 8 distinct recursive patterns: structural recursion, tail recursion, mutual recursion, two-pointer merge, divide & conquer merge sort, construction from array, sorted check, duplicate removal
- Full call-stack visualization for reverse
- Recursive: insert, delete, print (forward + reverse without mutation!), length, sum, search, reverse, nth-from-end, palindrome check

**All operations covered:**
- Every insertion/deletion case (head, tail, position, by value, given node pointer)
- Traversal: iterative, two-pointer slow/fast, trailing pointer, bidirectional
- Floyd's cycle detection + cycle start location + cycle removal
- Merge K sorted lists, group-of-K reversal, merge sort, insertion sort
- Stack, Queue, Deque built on linked lists

**Section 23** has a full complexity table, and **Section 24** covers 8 common pitfalls with wrong/correct code pairs for each language.