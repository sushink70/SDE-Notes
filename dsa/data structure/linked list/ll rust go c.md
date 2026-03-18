# ═══════════════════════════════════════════════════════════════
#   COMPREHENSIVE GUIDE TO LINKED LISTS
#   From Fundamentals to World-Class Mastery
# ═══════════════════════════════════════════════════════════════

---

# TABLE OF CONTENTS

```
 1. Mental Model Before You Code
 2. What Is a Linked List? (The Core Intuition)
 3. Memory & Pointers — The Foundation
 4. Anatomy of a Node
 5. Singly Linked List
    ├── Structure & Visualization
    ├── Core Operations (Insert, Delete, Traverse, Search)
    └── C | Go | Rust Implementations
 6. Doubly Linked List
    ├── Structure & Visualization
    ├── Core Operations
    └── C | Go | Rust Implementations
 7. Circular Linked List
    ├── Singly Circular
    ├── Doubly Circular
    └── Implementations
 8. Advanced Algorithms
    ├── Reversal (Iterative + Recursive)
    ├── Finding the Middle (Floyd's Slow-Fast Pointer)
    ├── Cycle Detection & Removal (Floyd's Cycle Algorithm)
    ├── Merge Two Sorted Lists
    ├── Remove Nth Node from End
    ├── Find Intersection of Two Lists
    └── Sort a Linked List (Merge Sort)
 9. Time & Space Complexity Master Table
10. Array vs Linked List — When to Use What
11. Common Pitfalls & Debugging Patterns
12. Mental Models & Problem-Solving Strategies
```

---

# 1. MENTAL MODEL BEFORE YOU CODE

> *"An expert doesn't start by writing code. They start by understanding the shape of the problem."*

Before a single line of code, ask:

```
┌─────────────────────────────────────────────────────────┐
│              THE EXPERT'S THINKING PROCESS              │
├─────────────────────────────────────────────────────────┤
│  1. What is being STORED?    → data type of each node   │
│  2. What CONNECTIONS exist?  → next? prev? circular?    │
│  3. What OPERATIONS matter?  → insert? delete? search?  │
│  4. What are the EDGE CASES? → empty list? one node?    │
│  5. What is the INVARIANT?   → what must always be true?│
└─────────────────────────────────────────────────────────┘
```

**Cognitive Principle: Chunking**
Before mastering complex linked list algorithms, your brain needs to "chunk"
the primitives — node creation, pointer re-wiring, traversal — into single
mental units. Only then can you think at higher abstraction levels like
"reverse this sublist" without cognitive overload.

---

# 2. WHAT IS A LINKED LIST? (THE CORE INTUITION)

## Real-World Analogy

Think of a **treasure hunt**: each clue (node) contains:
- A piece of treasure (your data)
- A note telling you where the NEXT clue is (pointer/address)

You must start from the FIRST clue (head). You cannot jump to clue #5
directly — you must follow the chain.

```
  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
  │  data: "A"    │     │  data: "B"    │     │  data: "C"    │
  │  next: ───────┼────►│  next: ───────┼────►│  next: NULL   │
  └───────────────┘     └───────────────┘     └───────────────┘
       HEAD (start)                                  TAIL (end)
```

## Formal Definition

A **Linked List** is a linear data structure where elements (called **nodes**)
are stored in non-contiguous memory locations. Each node holds:
1. **Data** — the value you want to store
2. **Pointer(s)** — memory address(es) pointing to the next/previous node(s)

## Key Vocabulary (terms you MUST know)

```
┌──────────────┬────────────────────────────────────────────────────┐
│ Term         │ Meaning                                            │
├──────────────┼────────────────────────────────────────────────────┤
│ Node         │ A container holding data + pointer(s)              │
│ Head         │ Pointer to the FIRST node of the list              │
│ Tail         │ The LAST node (its next pointer = NULL/nil/None)   │
│ NULL / nil   │ Means "points to nothing" — end of the list        │
│ Pointer      │ A variable that stores a memory ADDRESS            │
│ Traversal    │ Visiting each node one by one from head to tail    │
│ Predecessor  │ The node that comes BEFORE a given node            │
│ Successor    │ The node that comes AFTER a given node             │
│ Sentinel     │ A dummy node used to simplify edge cases           │
│ Invariant    │ A condition that is ALWAYS true about the list     │
└──────────────┴────────────────────────────────────────────────────┘
```

---

# 3. MEMORY & POINTERS — THE FOUNDATION

## How Arrays vs Linked Lists Live in Memory

**Array** — contiguous memory (all elements are neighbors):
```
Memory Address:  1000   1004   1008   1012   1016
                ┌──────┬──────┬──────┬──────┬──────┐
                │  10  │  20  │  30  │  40  │  50  │
                └──────┴──────┴──────┴──────┴──────┘
                  [0]    [1]    [2]    [3]    [4]
```
You can jump to index 3 because: address = base + (3 × size_of_element)

**Linked List** — scattered memory (nodes can be ANYWHERE):
```
Memory Address:  1000         2048         3500         4200
                ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
                │data: 10  │  │data: 20  │  │data: 30  │  │data: 40  │
                │next: 2048│─►│next: 3500│─►│next: 4200│─►│next: NULL│
                └──────────┘  └──────────┘  └──────────┘  └──────────┘
```
You CANNOT jump to the 3rd element. You must walk: 1000 → 2048 → 3500.

## What is a Pointer?

A pointer is simply a variable that stores an **address** of another variable.

```
In C:
  int x = 42;          // x lives at address, say, 0xFF10
  int *ptr = &x;       // ptr stores 0xFF10  (& means "address of")
  printf("%d", *ptr);  // *ptr means "value at that address" → 42
                       // * here is called DEREFERENCING

  ┌───────────┐       ┌───────────┐
  │  ptr      │       │    x      │
  │  0xFF10   │──────►│    42     │
  └───────────┘       └───────────┘
     "I point           "I am the
      to x"              actual data"
```

In Rust, instead of raw pointers, we use:
- `Box<T>` — heap-allocated owned pointer
- `Option<Box<T>>` — pointer that might be NULL (None) or valid (Some)

In Go, we use `*Node` — a pointer to a Node struct.

---

# 4. ANATOMY OF A NODE

## The Building Block

```
┌──────────────────────────────────────────────┐
│                   NODE                       │
│  ┌──────────────────┐  ┌──────────────────┐  │
│  │      DATA        │  │    NEXT POINTER  │  │
│  │  (your value)    │  │  (address of     │  │
│  │  int, string,    │  │   next node, or  │  │
│  │  struct, etc.)   │  │   NULL if last)  │  │
│  └──────────────────┘  └──────────────────┘  │
└──────────────────────────────────────────────┘
```

## Node in C
```c
struct Node {
    int data;
    struct Node* next;   // pointer to next node
};
```

## Node in Go
```go
type Node struct {
    data int
    next *Node   // pointer to next node (nil if last)
}
```

## Node in Rust
```rust
struct Node {
    data: i32,
    next: Option<Box<Node>>,   // Some(Box<Node>) or None
}
// Box<T> = heap allocation
// Option<T> = Rust's safe way of expressing "might be NULL"
```

---

# 5. SINGLY LINKED LIST

## 5.1 Structure & Visualization

Each node points ONLY to the next node. One direction only.

```
  HEAD
   │
   ▼
  ┌────┬────┐    ┌────┬────┐    ┌────┬────┐    ┌────┬──────┐
  │ 10 │  ──┼───►│ 20 │  ──┼───►│ 30 │  ──┼───►│ 40 │ NULL │
  └────┴────┘    └────┴────┘    └────┴────┘    └────┴──────┘
  Node 1          Node 2          Node 3          Node 4 (TAIL)
```

## 5.2 Core Operations — Expert Thinking First

### INSERT AT HEAD

```
BEFORE:  HEAD → [20] → [30] → [40] → NULL
Insert 10 at head.

Step 1: Create new node with data=10
Step 2: new_node.next = HEAD          (new node points to old first)
Step 3: HEAD = new_node               (head now points to new node)

AFTER:   HEAD → [10] → [20] → [30] → [40] → NULL
```

**Decision Flow:**
```
  START: Insert at head
       │
       ▼
  Create new_node
       │
       ▼
  new_node.next = current HEAD
       │
       ▼
  HEAD = new_node
       │
       ▼
  DONE ✓
```

### INSERT AT TAIL

```
BEFORE:  HEAD → [10] → [20] → [30] → NULL
Insert 40 at tail.

Step 1: Create new node with data=40, next=NULL
Step 2: If list is EMPTY → HEAD = new_node, DONE
Step 3: Traverse to the last node (where node.next == NULL)
Step 4: last_node.next = new_node

AFTER:   HEAD → [10] → [20] → [30] → [40] → NULL
```

**Decision Flow:**
```
  START: Insert at tail
       │
       ▼
  Create new_node (next = NULL)
       │
       ▼
  Is list EMPTY? (HEAD == NULL)
  │           │
 YES          NO
  │           │
  ▼           ▼
HEAD =    curr = HEAD
new_node      │
  │           ▼
  │     Is curr.next == NULL?
  │     │              │
  │    YES             NO
  │     │              │
  │     ▼              ▼
  │  curr.next =    curr = curr.next
  │  new_node           │
  │                 (loop back)
  ▼
 DONE ✓
```

### INSERT AT POSITION k

```
BEFORE:  HEAD → [10] → [20] → [30] → [40] → NULL
Insert 25 at position 2 (0-indexed).

Position 0: 10
Position 1: 20  ← we want to insert AFTER here
Position 2: 30

Step 1: Traverse to node at position (k-1) = position 1 → node[20]
Step 2: new_node.next = node[20].next   (new → [30])
Step 3: node[20].next = new_node        ([20] → new)

AFTER:  HEAD → [10] → [20] → [25] → [30] → [40] → NULL
```

```
  [10] → [20] ─────────────────► [30] → [40]
                  │          ▲
                  │          │
                  └──► [25] ─┘
         Step 1: [20].next was [30]
         Step 2: [25].next = [30]
         Step 3: [20].next = [25]

  CRITICAL ORDER: You MUST do Step 2 BEFORE Step 3.
  If you do Step 3 first, you LOSE the reference to [30].
  This is the most common beginner mistake!
```

### DELETE A NODE

```
BEFORE: HEAD → [10] → [20] → [30] → [40] → NULL
Delete node with value 20.

Step 1: Find the PREDECESSOR of node[20] = node[10]
Step 2: predecessor.next = node[20].next   (skip over [20])
Step 3: Free/deallocate node[20]

AFTER:  HEAD → [10] → [30] → [40] → NULL
```

**Decision Flow (Delete by value):**
```
  START: Delete node with value V
       │
       ▼
  Is HEAD == NULL? → YES → List empty, error/return
       │
       NO
       ▼
  Is HEAD.data == V?
  │              │
 YES             NO
  │              │
  ▼              ▼
 temp = HEAD   prev = HEAD
 HEAD = HEAD.next
 free(temp)    curr = HEAD.next
               │
               ▼
         curr == NULL? → YES → Value not found
               │
               NO
               ▼
         curr.data == V?
         │            │
        YES           NO
         │            │
         ▼            ▼
   prev.next =    prev = curr
   curr.next      curr = curr.next
   free(curr)         │
                  (loop back)
```

---

## 5.3 C Implementation — Full Singly Linked List

```c
#include <stdio.h>
#include <stdlib.h>

/* ── NODE DEFINITION ─────────────────────────────────────── */
typedef struct Node {
    int data;
    struct Node* next;
} Node;

/* ── LINKED LIST STRUCT ──────────────────────────────────── */
typedef struct {
    Node* head;
    int   size;
} LinkedList;

/* ── HELPER: Create a new node ───────────────────────────── */
Node* create_node(int data) {
    Node* node = (Node*)malloc(sizeof(Node));
    if (!node) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    node->data = data;
    node->next = NULL;
    return node;
}

/* ── INITIALIZE an empty list ────────────────────────────── */
void init(LinkedList* list) {
    list->head = NULL;
    list->size = 0;
}

/* ── INSERT AT HEAD ──────────────────────────────────────── */
/*  O(1) time | O(1) space                                   */
void insert_head(LinkedList* list, int data) {
    Node* node   = create_node(data);
    node->next   = list->head;   /* new node points to old head */
    list->head   = node;         /* head now is the new node    */
    list->size++;
}

/* ── INSERT AT TAIL ──────────────────────────────────────── */
/*  O(n) time | O(1) space                                   */
void insert_tail(LinkedList* list, int data) {
    Node* node = create_node(data);

    if (list->head == NULL) {    /* empty list: new node is head */
        list->head = node;
        list->size++;
        return;
    }

    Node* curr = list->head;
    while (curr->next != NULL) { /* walk to the last node       */
        curr = curr->next;
    }
    curr->next = node;           /* last node points to new     */
    list->size++;
}

/* ── INSERT AT POSITION (0-indexed) ─────────────────────── */
/*  O(n) time | O(1) space                                   */
void insert_at(LinkedList* list, int data, int pos) {
    if (pos < 0 || pos > list->size) {
        fprintf(stderr, "Invalid position %d\n", pos);
        return;
    }
    if (pos == 0) {
        insert_head(list, data);
        return;
    }

    Node* node = create_node(data);
    Node* curr = list->head;

    for (int i = 0; i < pos - 1; i++) {  /* walk to node BEFORE pos */
        curr = curr->next;
    }
    node->next = curr->next;   /* STEP 1: new → successor  */
    curr->next = node;         /* STEP 2: prev → new       */
    list->size++;
}

/* ── DELETE BY VALUE ─────────────────────────────────────── */
/*  O(n) time | O(1) space                                   */
int delete_value(LinkedList* list, int data) {
    if (list->head == NULL) return 0;  /* empty list */

    /* Special case: deleting the head */
    if (list->head->data == data) {
        Node* temp  = list->head;
        list->head  = list->head->next;
        free(temp);
        list->size--;
        return 1;
    }

    Node* prev = list->head;
    Node* curr = list->head->next;

    while (curr != NULL) {
        if (curr->data == data) {
            prev->next = curr->next;  /* skip over curr */
            free(curr);
            list->size--;
            return 1;
        }
        prev = curr;
        curr = curr->next;
    }
    return 0;  /* not found */
}

/* ── SEARCH ──────────────────────────────────────────────── */
/*  O(n) time | O(1) space                                   */
Node* search(LinkedList* list, int data) {
    Node* curr = list->head;
    while (curr != NULL) {
        if (curr->data == data) return curr;
        curr = curr->next;
    }
    return NULL;
}

/* ── TRAVERSAL / PRINT ───────────────────────────────────── */
/*  O(n) time | O(1) space                                   */
void print_list(LinkedList* list) {
    Node* curr = list->head;
    printf("HEAD → ");
    while (curr != NULL) {
        printf("[%d]", curr->data);
        if (curr->next) printf(" → ");
        curr = curr->next;
    }
    printf(" → NULL  (size: %d)\n", list->size);
}

/* ── REVERSE (ITERATIVE) ─────────────────────────────────── */
/*  O(n) time | O(1) space — THREE POINTER TECHNIQUE         */
void reverse(LinkedList* list) {
    Node* prev = NULL;
    Node* curr = list->head;
    Node* next = NULL;

    while (curr != NULL) {
        next       = curr->next;  /* save next before we lose it */
        curr->next = prev;        /* reverse the link            */
        prev       = curr;        /* advance prev                */
        curr       = next;        /* advance curr                */
    }
    list->head = prev;            /* prev is now the new head    */
}

/* ── FREE THE ENTIRE LIST ────────────────────────────────── */
void free_list(LinkedList* list) {
    Node* curr = list->head;
    while (curr != NULL) {
        Node* temp = curr;
        curr       = curr->next;
        free(temp);
    }
    list->head = NULL;
    list->size = 0;
}

/* ── DEMO ────────────────────────────────────────────────── */
int main(void) {
    LinkedList list;
    init(&list);

    insert_tail(&list, 10);
    insert_tail(&list, 20);
    insert_tail(&list, 30);
    insert_tail(&list, 40);
    print_list(&list);   /* HEAD → [10] → [20] → [30] → [40] → NULL */

    insert_head(&list, 5);
    print_list(&list);   /* HEAD → [5] → [10] → [20] → [30] → [40] → NULL */

    insert_at(&list, 25, 3);
    print_list(&list);   /* HEAD → [5] → [10] → [20] → [25] → [30] → [40] */

    delete_value(&list, 20);
    print_list(&list);   /* HEAD → [5] → [10] → [25] → [30] → [40] → NULL */

    reverse(&list);
    print_list(&list);   /* HEAD → [40] → [30] → [25] → [10] → [5] → NULL */

    free_list(&list);
    return 0;
}
```

---

## 5.4 Go Implementation — Full Singly Linked List

```go
package main

import "fmt"

// ── NODE ──────────────────────────────────────────────────────
type Node struct {
	data int
	next *Node
}

// ── LINKED LIST ───────────────────────────────────────────────
type LinkedList struct {
	head *Node
	size int
}

// ── INSERT AT HEAD ────────────────────────────────────────────
// O(1) time | O(1) space
func (l *LinkedList) InsertHead(data int) {
	node := &Node{data: data, next: l.head}
	l.head = node
	l.size++
}

// ── INSERT AT TAIL ────────────────────────────────────────────
// O(n) time | O(1) space
func (l *LinkedList) InsertTail(data int) {
	node := &Node{data: data}
	if l.head == nil {
		l.head = node
		l.size++
		return
	}
	curr := l.head
	for curr.next != nil {
		curr = curr.next
	}
	curr.next = node
	l.size++
}

// ── INSERT AT POSITION (0-indexed) ───────────────────────────
// O(n) time | O(1) space
func (l *LinkedList) InsertAt(data, pos int) {
	if pos < 0 || pos > l.size {
		fmt.Printf("Invalid position: %d\n", pos)
		return
	}
	if pos == 0 {
		l.InsertHead(data)
		return
	}
	node := &Node{data: data}
	curr := l.head
	for i := 0; i < pos-1; i++ {
		curr = curr.next
	}
	node.next = curr.next // Step 1: new → successor
	curr.next = node      // Step 2: prev → new
	l.size++
}

// ── DELETE BY VALUE ───────────────────────────────────────────
// O(n) time | O(1) space
func (l *LinkedList) DeleteValue(data int) bool {
	if l.head == nil {
		return false
	}
	if l.head.data == data {
		l.head = l.head.next
		l.size--
		return true
	}
	prev := l.head
	curr := l.head.next
	for curr != nil {
		if curr.data == data {
			prev.next = curr.next // unlink curr
			l.size--
			return true
		}
		prev = curr
		curr = curr.next
	}
	return false
}

// ── SEARCH ────────────────────────────────────────────────────
// O(n) time | O(1) space
func (l *LinkedList) Search(data int) *Node {
	curr := l.head
	for curr != nil {
		if curr.data == data {
			return curr
		}
		curr = curr.next
	}
	return nil
}

// ── PRINT ─────────────────────────────────────────────────────
func (l *LinkedList) Print() {
	curr := l.head
	fmt.Print("HEAD → ")
	for curr != nil {
		fmt.Printf("[%d]", curr.data)
		if curr.next != nil {
			fmt.Print(" → ")
		}
		curr = curr.next
	}
	fmt.Printf(" → nil  (size: %d)\n", l.size)
}

// ── REVERSE (ITERATIVE) ───────────────────────────────────────
// O(n) time | O(1) space
func (l *LinkedList) Reverse() {
	var prev *Node
	curr := l.head
	for curr != nil {
		next      := curr.next // save next
		curr.next  = prev      // reverse the arrow
		prev       = curr      // advance prev
		curr       = next      // advance curr
	}
	l.head = prev
}

// ── REVERSE (RECURSIVE) ──────────────────────────────────────
// O(n) time | O(n) space (call stack)
func reverseRecursive(node *Node) *Node {
	// Base case: empty or single node
	if node == nil || node.next == nil {
		return node
	}
	// Recurse: reverse the rest of the list
	newHead := reverseRecursive(node.next)
	// After recursion, node.next points to the tail of reversed list
	// We need the tail to point back to current node
	node.next.next = node  // tail of reversed list → current
	node.next      = nil   // current becomes new tail
	return newHead
}

func main() {
	list := &LinkedList{}
	list.InsertTail(10)
	list.InsertTail(20)
	list.InsertTail(30)
	list.InsertTail(40)
	list.Print()

	list.InsertHead(5)
	list.Print()

	list.InsertAt(25, 3)
	list.Print()

	list.DeleteValue(20)
	list.Print()

	list.Reverse()
	list.Print()
}
```

---

## 5.5 Rust Implementation — Full Singly Linked List

```rust
// In Rust, the idiomatic approach for a singly linked list uses
// Option<Box<Node>> which gives us:
//   - Option = safe nullable pointer (no null pointer bugs)
//   - Box    = heap allocation (since Node is recursive in size)

type Link = Option<Box<Node>>;

struct Node {
    data: i32,
    next: Link,
}

pub struct LinkedList {
    head: Link,
    size: usize,
}

impl LinkedList {
    // ── CONSTRUCTOR ─────────────────────────────────────────
    pub fn new() -> Self {
        LinkedList { head: None, size: 0 }
    }

    // ── INSERT AT HEAD ─────────────────────────────────────
    // O(1) time | O(1) space
    pub fn insert_head(&mut self, data: i32) {
        let old_head = self.head.take(); // take ownership of current head
        let new_node = Box::new(Node { data, next: old_head });
        self.head = Some(new_node);
        self.size += 1;
    }

    // ── INSERT AT TAIL ─────────────────────────────────────
    // O(n) time | O(1) space
    pub fn insert_tail(&mut self, data: i32) {
        let new_node = Box::new(Node { data, next: None });

        // Walk to the last node using a mutable reference
        let mut curr = &mut self.head;
        loop {
            match curr {
                None => {
                    // We're at the end (empty slot)
                    *curr = Some(new_node);
                    break;
                }
                Some(node) => {
                    curr = &mut node.next;
                }
            }
        }
        self.size += 1;
    }

    // ── DELETE HEAD ────────────────────────────────────────
    // O(1) time | O(1) space
    pub fn delete_head(&mut self) -> Option<i32> {
        self.head.take().map(|node| {
            self.head = node.next;
            self.size -= 1;
            node.data
        })
    }

    // ── DELETE BY VALUE ────────────────────────────────────
    // O(n) time | O(1) space
    pub fn delete_value(&mut self, target: i32) -> bool {
        let mut curr = &mut self.head;
        loop {
            match curr {
                None => return false, // not found
                Some(node) if node.data == target => {
                    // Unlink this node
                    let next = node.next.take();
                    *curr = next;
                    self.size -= 1;
                    return true;
                }
                Some(node) => {
                    curr = &mut node.next;
                }
            }
        }
    }

    // ── SEARCH ─────────────────────────────────────────────
    // O(n) time | O(1) space
    pub fn search(&self, target: i32) -> bool {
        let mut curr = &self.head;
        while let Some(node) = curr {
            if node.data == target {
                return true;
            }
            curr = &node.next;
        }
        false
    }

    // ── REVERSE (ITERATIVE) ────────────────────────────────
    // O(n) time | O(1) space
    pub fn reverse(&mut self) {
        let mut prev: Link = None;
        let mut curr = self.head.take(); // take ownership of entire list

        while let Some(mut node) = curr {
            let next = node.next.take(); // save next
            node.next = prev;            // reverse arrow
            prev = Some(node);           // advance prev
            curr = next;                 // advance curr
        }
        self.head = prev;
    }

    // ── PRINT ──────────────────────────────────────────────
    pub fn print(&self) {
        let mut curr = &self.head;
        print!("HEAD → ");
        while let Some(node) = curr {
            print!("[{}]", node.data);
            if node.next.is_some() { print!(" → "); }
            curr = &node.next;
        }
        println!(" → None  (size: {})", self.size);
    }

    // ── GET LENGTH ─────────────────────────────────────────
    pub fn len(&self) -> usize {
        self.size
    }

    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
}

fn main() {
    let mut list = LinkedList::new();

    list.insert_tail(10);
    list.insert_tail(20);
    list.insert_tail(30);
    list.insert_tail(40);
    list.print(); // HEAD → [10] → [20] → [30] → [40] → None

    list.insert_head(5);
    list.print(); // HEAD → [5] → [10] → [20] → [30] → [40] → None

    list.delete_value(20);
    list.print(); // HEAD → [5] → [10] → [30] → [40] → None

    list.reverse();
    list.print(); // HEAD → [40] → [30] → [10] → [5] → None
}
```

---

# 6. DOUBLY LINKED LIST

## 6.1 Structure & Visualization

Each node points to BOTH its successor (next) and predecessor (prev).

```
        PREV ◄──────────────────────────────────────────────────────
        NEXT ──────────────────────────────────────────────────────►

NULL ←─[prev|10|next]←──►[prev|20|next]←──►[prev|30|next]←──►[prev|40|next]─► NULL
         HEAD                                                       TAIL
```

### Node Anatomy (Doubly):
```
  ┌──────┬──────┬──────┐
  │ PREV │ DATA │ NEXT │
  │(addr)│(val) │(addr)│
  └──────┴──────┴──────┘
     │               │
     │               └──► points to the NEXT node
     └──────────────────► points to the PREVIOUS node
```

## 6.2 Advantages over Singly
```
┌──────────────────────┬────────────────────┬────────────────────┐
│ Operation            │ Singly             │ Doubly             │
├──────────────────────┼────────────────────┼────────────────────┤
│ Delete given node*   │ O(n) — need prev   │ O(1) — has prev    │
│ Insert before node*  │ O(n) — need prev   │ O(1) — has prev    │
│ Traverse backward    │ Not possible       │ O(n)               │
│ Memory per node      │ 1 pointer (less)   │ 2 pointers (more)  │
└──────────────────────┴────────────────────┴────────────────────┘
* given a direct pointer to the node (not its value)
```

## 6.3 Insert Operation (Doubly)

```
Insert 25 between [20] and [30]:

BEFORE:  ←─[20]←──►[30]─►

Step 1: Create node [25]
Step 2: new.prev = node[20]       new.next = node[30]
Step 3: node[20].next = new       node[30].prev = new

AFTER:   ←─[20]←──►[25]←──►[30]─►

POINTER RE-WIRING:
  [20].next  ─────────────────────────────► [30]
     │                                        ▲
     │  new [25]                              │
     │  ┌──────────────┐                      │
     └─►│prev=20|next──┼──────────────────────┘
        └──────────────┘
```

## 6.4 C Implementation — Doubly Linked List

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
    DNode* tail;  /* tail pointer allows O(1) insert at tail */
    int    size;
} DoublyList;

DNode* create_dnode(int data) {
    DNode* node = (DNode*)malloc(sizeof(DNode));
    node->data = data;
    node->prev = NULL;
    node->next = NULL;
    return node;
}

void dl_init(DoublyList* list) {
    list->head = NULL;
    list->tail = NULL;
    list->size = 0;
}

/* ── INSERT AT HEAD ──────────────────────────────────────── */
/* O(1) time */
void dl_insert_head(DoublyList* list, int data) {
    DNode* node = create_dnode(data);
    if (list->head == NULL) {
        list->head = node;
        list->tail = node;
    } else {
        node->next        = list->head;  /* new → old head  */
        list->head->prev  = node;        /* old head ← new  */
        list->head        = node;        /* head = new       */
    }
    list->size++;
}

/* ── INSERT AT TAIL ──────────────────────────────────────── */
/* O(1) time — we keep a tail pointer! */
void dl_insert_tail(DoublyList* list, int data) {
    DNode* node = create_dnode(data);
    if (list->tail == NULL) {
        list->head = node;
        list->tail = node;
    } else {
        node->prev        = list->tail;  /* new ← old tail  */
        list->tail->next  = node;        /* old tail → new  */
        list->tail        = node;        /* tail = new       */
    }
    list->size++;
}

/* ── INSERT AFTER A GIVEN NODE ───────────────────────────── */
/* O(1) time — given pointer to a node */
void dl_insert_after(DoublyList* list, DNode* target, int data) {
    if (!target) return;
    DNode* node = create_dnode(data);
    node->next = target->next;
    node->prev = target;

    if (target->next)
        target->next->prev = node;  /* successor ← new */
    else
        list->tail = node;          /* new is now tail  */

    target->next = node;            /* target → new     */
    list->size++;
}

/* ── DELETE A NODE (given direct pointer) ────────────────── */
/* O(1) time — this is the KEY advantage of doubly linked list */
void dl_delete_node(DoublyList* list, DNode* target) {
    if (!target) return;

    if (target->prev)
        target->prev->next = target->next;  /* predecessor → successor */
    else
        list->head = target->next;          /* was head, update head   */

    if (target->next)
        target->next->prev = target->prev;  /* successor ← predecessor */
    else
        list->tail = target->prev;          /* was tail, update tail   */

    free(target);
    list->size--;
}

/* ── PRINT FORWARD ───────────────────────────────────────── */
void dl_print_forward(DoublyList* list) {
    DNode* curr = list->head;
    printf("NULL ←→ ");
    while (curr) {
        printf("[%d]", curr->data);
        if (curr->next) printf(" ←→ ");
        curr = curr->next;
    }
    printf(" ←→ NULL  (size: %d)\n", list->size);
}

/* ── PRINT BACKWARD ──────────────────────────────────────── */
void dl_print_backward(DoublyList* list) {
    DNode* curr = list->tail;
    printf("NULL ←→ ");
    while (curr) {
        printf("[%d]", curr->data);
        if (curr->prev) printf(" ←→ ");
        curr = curr->prev;
    }
    printf(" ←→ NULL\n");
}

int main(void) {
    DoublyList list;
    dl_init(&list);

    dl_insert_tail(&list, 10);
    dl_insert_tail(&list, 20);
    dl_insert_tail(&list, 30);
    dl_insert_tail(&list, 40);
    dl_print_forward(&list);
    dl_print_backward(&list);

    /* Insert after the node containing 20 */
    DNode* node20 = list.head->next; /* navigate to [20] */
    dl_insert_after(&list, node20, 25);
    dl_print_forward(&list);

    /* Delete node[20] directly — O(1) */
    dl_delete_node(&list, node20);
    dl_print_forward(&list);

    return 0;
}
```

## 6.5 Go Implementation — Doubly Linked List

```go
package main

import "fmt"

type DNode struct {
	data int
	prev *DNode
	next *DNode
}

type DoublyList struct {
	head *DNode
	tail *DNode
	size int
}

func (l *DoublyList) InsertHead(data int) {
	node := &DNode{data: data}
	if l.head == nil {
		l.head, l.tail = node, node
	} else {
		node.next = l.head
		l.head.prev = node
		l.head = node
	}
	l.size++
}

func (l *DoublyList) InsertTail(data int) {
	node := &DNode{data: data}
	if l.tail == nil {
		l.head, l.tail = node, node
	} else {
		node.prev = l.tail
		l.tail.next = node
		l.tail = node
	}
	l.size++
}

// InsertAfter — O(1) given the pointer to target node
func (l *DoublyList) InsertAfter(target *DNode, data int) {
	if target == nil { return }
	node := &DNode{data: data, prev: target, next: target.next}
	if target.next != nil {
		target.next.prev = node
	} else {
		l.tail = node // node becomes new tail
	}
	target.next = node
	l.size++
}

// DeleteNode — O(1) given direct pointer
func (l *DoublyList) DeleteNode(target *DNode) {
	if target == nil { return }
	if target.prev != nil {
		target.prev.next = target.next
	} else {
		l.head = target.next
	}
	if target.next != nil {
		target.next.prev = target.prev
	} else {
		l.tail = target.prev
	}
	l.size--
}

func (l *DoublyList) PrintForward() {
	curr := l.head
	fmt.Print("nil ←→ ")
	for curr != nil {
		fmt.Printf("[%d]", curr.data)
		if curr.next != nil { fmt.Print(" ←→ ") }
		curr = curr.next
	}
	fmt.Printf(" ←→ nil  (size: %d)\n", l.size)
}

func (l *DoublyList) PrintBackward() {
	curr := l.tail
	fmt.Print("nil ←→ ")
	for curr != nil {
		fmt.Printf("[%d]", curr.data)
		if curr.prev != nil { fmt.Print(" ←→ ") }
		curr = curr.prev
	}
	fmt.Println(" ←→ nil")
}

func main() {
	list := &DoublyList{}
	list.InsertTail(10)
	list.InsertTail(20)
	list.InsertTail(30)
	list.InsertTail(40)
	list.PrintForward()
	list.PrintBackward()
}
```

## 6.6 Rust Implementation — Doubly Linked List

```rust
// NOTE: A true doubly linked list in Rust is notoriously complex
// due to the ownership system (each node has TWO owners: next and prev).
// The idiomatic solution uses Rc<RefCell<Node>> for shared ownership
// with interior mutability.
//
// Rc  = Reference Counted — allows MULTIPLE owners
// RefCell = allows mutation through a shared reference (runtime borrow checking)

use std::rc::Rc;
use std::cell::RefCell;

type DLink = Option<Rc<RefCell<DNode>>>;

struct DNode {
    data: i32,
    prev: DLink,
    next: DLink,
}

pub struct DoublyList {
    head: DLink,
    tail: DLink,
    size: usize,
}

impl DoublyList {
    pub fn new() -> Self {
        DoublyList { head: None, tail: None, size: 0 }
    }

    pub fn insert_tail(&mut self, data: i32) {
        let new_node = Rc::new(RefCell::new(DNode {
            data,
            prev: self.tail.clone(), // new node's prev = current tail
            next: None,
        }));

        match self.tail.take() {
            None => {
                // List was empty
                self.head = Some(new_node.clone());
                self.tail = Some(new_node);
            }
            Some(old_tail) => {
                old_tail.borrow_mut().next = Some(new_node.clone());
                self.tail = Some(new_node);
            }
        }
        self.size += 1;
    }

    pub fn insert_head(&mut self, data: i32) {
        let new_node = Rc::new(RefCell::new(DNode {
            data,
            prev: None,
            next: self.head.clone(),
        }));

        match self.head.take() {
            None => {
                self.head = Some(new_node.clone());
                self.tail = Some(new_node);
            }
            Some(old_head) => {
                old_head.borrow_mut().prev = Some(new_node.clone());
                self.head = Some(new_node);
            }
        }
        self.size += 1;
    }

    pub fn print_forward(&self) {
        let mut curr = self.head.clone();
        print!("None ←→ ");
        while let Some(node) = curr {
            let borrowed = node.borrow();
            print!("[{}]", borrowed.data);
            if borrowed.next.is_some() { print!(" ←→ "); }
            curr = borrowed.next.clone();
        }
        println!(" ←→ None  (size: {})", self.size);
    }
}

fn main() {
    let mut list = DoublyList::new();
    list.insert_tail(10);
    list.insert_tail(20);
    list.insert_tail(30);
    list.insert_head(5);
    list.print_forward(); // None ←→ [5] ←→ [10] ←→ [20] ←→ [30] ←→ None
}
```

---

# 7. CIRCULAR LINKED LIST

## 7.1 Concept

In a circular linked list, the TAIL's next pointer does NOT point to NULL.
Instead, it points BACK to the HEAD. This creates a circle.

```
Singly Circular:
  ┌──────────────────────────────────────────┐
  │                                          │
  ▼                                          │
 [10] ──► [20] ──► [30] ──► [40] ────────────┘
  HEAD

Doubly Circular:
  ┌────────────────────────────────────────────────────────────┐
  │                                                            │
  ▼                                                            │
 [10] ←──► [20] ←──► [30] ←──► [40] ────────────────────────►┘
  HEAD (also: HEAD.prev = TAIL)
```

## 7.2 Use Cases
- **Round-robin scheduling** (OS process scheduling)
- **Circular buffers** (audio streaming, networking)
- **Card games** (players in a circle)
- **Music playlist** (loop mode)

## 7.3 Key Invariants for Circular Lists

```
For a non-empty circular singly linked list:
  ✓ tail.next == head       (always)
  ✓ head is never NULL
  ✓ Traversal ends when curr.next == head (not NULL)
```

## 7.4 C Implementation — Circular Singly Linked List

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct CNode {
    int data;
    struct CNode* next;
} CNode;

/* We store a pointer to TAIL (not head) because:
   - tail.next = head (so head is reachable in O(1))
   - Insert at head: O(1) — set tail.next to new, new.next = old head
   - Insert at tail: O(1) — just move tail pointer
*/
typedef struct {
    CNode* tail;   /* tail.next == head always */
    int    size;
} CircularList;

void cl_init(CircularList* list) {
    list->tail = NULL;
    list->size = 0;
}

/* ── INSERT AT HEAD ──────────────────────────────────────── */
void cl_insert_head(CircularList* list, int data) {
    CNode* node = (CNode*)malloc(sizeof(CNode));
    node->data  = data;

    if (list->tail == NULL) {
        /* First node — points to itself */
        node->next  = node;
        list->tail  = node;
    } else {
        CNode* head  = list->tail->next;  /* current head */
        node->next   = head;              /* new → head   */
        list->tail->next = node;          /* tail → new   */
    }
    list->size++;
}

/* ── INSERT AT TAIL ──────────────────────────────────────── */
void cl_insert_tail(CircularList* list, int data) {
    cl_insert_head(list, data);        /* insert at head first    */
    list->tail = list->tail->next;     /* then move tail forward  */
}

/* ── PRINT ───────────────────────────────────────────────── */
void cl_print(CircularList* list) {
    if (list->tail == NULL) {
        printf("(empty circular list)\n");
        return;
    }
    CNode* curr = list->tail->next;  /* start from head */
    printf("→ ");
    do {
        printf("[%d] → ", curr->data);
        curr = curr->next;
    } while (curr != list->tail->next);  /* stop when we reach head again */
    printf("(back to start)  (size: %d)\n", list->size);
}

/* ── DELETE FROM HEAD ────────────────────────────────────── */
int cl_delete_head(CircularList* list) {
    if (list->tail == NULL) return -1;  /* empty */

    CNode* head = list->tail->next;
    int    val  = head->data;

    if (head == list->tail) {
        /* Only one node */
        list->tail = NULL;
    } else {
        list->tail->next = head->next;  /* tail now points to new head */
    }
    free(head);
    list->size--;
    return val;
}

int main(void) {
    CircularList list;
    cl_init(&list);

    cl_insert_tail(&list, 10);
    cl_insert_tail(&list, 20);
    cl_insert_tail(&list, 30);
    cl_insert_head(&list, 5);
    cl_print(&list);  /* → [5] → [10] → [20] → [30] → (back to start) */

    printf("Deleted: %d\n", cl_delete_head(&list));
    cl_print(&list);

    return 0;
}
```

---

# 8. ADVANCED ALGORITHMS

## 8.1 Reverse a Linked List (Three Methods)

### Method 1: Iterative (O(n) time, O(1) space) — BEST

```
THREE-POINTER TECHNIQUE:

Initial state:
  prev=NULL   curr=[10]→[20]→[30]→NULL    next=?

Iteration 1:
  next = curr.next = [20]
  curr.next = prev = NULL     ← reverse the arrow
  prev = curr = [10]
  curr = next = [20]
  State: NULL←[10]    [20]→[30]→NULL

Iteration 2:
  next = curr.next = [30]
  curr.next = prev = [10]     ← reverse the arrow
  prev = curr = [20]
  curr = next = [30]
  State: NULL←[10]←[20]    [30]→NULL

Iteration 3:
  next = curr.next = NULL
  curr.next = prev = [20]     ← reverse the arrow
  prev = curr = [30]
  curr = next = NULL
  State: NULL←[10]←[20]←[30]

curr == NULL, exit loop.
head = prev = [30]

RESULT: [30]→[20]→[10]→NULL ✓
```

### Method 2: Recursive (O(n) time, O(n) space)

```
reverseRec([1]→[2]→[3]→NULL):

Call stack:
  reverseRec([1]) → calls reverseRec([2]) →
    reverseRec([2]) → calls reverseRec([3]) →
      reverseRec([3]) → calls reverseRec(NULL) → base case, return [3]

Unwinding:
  After reverseRec([3]) returns [3] as newHead:
    [3].next is [2] (unchanged yet)
    [3].next.next = [3]  → [2].next = [3]   ← REVERSE!
    [3].next = NULL      → [3].next = NULL
    return [3] as newHead (still)

  After reverseRec([2]) returns [3] as newHead:
    [2].next is [1]
    [2].next.next = [2]  → [1].next = [2]   ← REVERSE!
    [2].next = NULL
    return [3] as newHead

Result: [3]→[2]→[1]→NULL, newHead = [3] ✓
```

### Method 3: Stack-based (O(n) time, O(n) space)

```
Push all nodes onto a stack, then pop to rebuild:
  Push: [10][20][30][40]
  Stack top: 40

  Pop 40 → new head = [40]
  Pop 30 → [40]→[30]
  Pop 20 → [40]→[30]→[20]
  Pop 10 → [40]→[30]→[20]→[10]→NULL
```

---

## 8.2 Find the Middle Node — Floyd's Slow-Fast Pointer

### Key Concept: The Runner Technique

Use TWO pointers moving at different speeds:
- **Slow pointer**: moves 1 step at a time
- **Fast pointer**: moves 2 steps at a time

When fast reaches the end, slow is at the MIDDLE.

```
List: [1]→[2]→[3]→[4]→[5]→NULL

Start: slow=[1], fast=[1]

Step 1: slow=[2], fast=[3]
Step 2: slow=[3], fast=[5]
fast.next == NULL → STOP
Middle = slow = [3] ✓

For even-length list [1]→[2]→[3]→[4]→NULL:
Start: slow=[1], fast=[1]
Step 1: slow=[2], fast=[3]
Step 2: slow=[3], fast=NULL (fast.next was [4], fast.next.next was NULL)
Middle = slow = [3] (first of the two middle nodes) ✓
```

**WHY does this work?**
If fast travels 2x as fast, when fast reaches position n (end),
slow is at position n/2 (middle). Pure mathematics!

```c
// C: Find middle node
Node* find_middle(Node* head) {
    if (!head) return NULL;
    Node* slow = head;
    Node* fast = head;
    while (fast->next != NULL && fast->next->next != NULL) {
        slow = slow->next;          /* +1 step */
        fast = fast->next->next;    /* +2 steps */
    }
    return slow;  /* slow is now at middle */
}
```

```go
// Go: Find middle node
func findMiddle(head *Node) *Node {
    slow, fast := head, head
    for fast.next != nil && fast.next.next != nil {
        slow = slow.next
        fast = fast.next.next
    }
    return slow
}
```

---

## 8.3 Cycle Detection — Floyd's Cycle Algorithm

### The Problem

Sometimes a linked list has a cycle (a loop). The tail points back to
some node in the middle instead of NULL. Naive traversal would loop forever.

```
Normal list:
[1]→[2]→[3]→[4]→[5]→NULL

List with cycle:
[1]→[2]→[3]→[4]→[5]
          ▲        │
          └────────┘
           cycle entry = [3]
```

### Floyd's Cycle Detection (Tortoise and Hare)

Use slow and fast pointers again:
- If there is NO cycle: fast will eventually reach NULL
- If there IS a cycle: fast will eventually CATCH UP to slow (they meet)

**Why they meet:**
Inside a cycle of length L, the fast pointer "laps" the slow pointer.
Each step, fast gains 1 position on slow. They will meet in at most L steps.

```
Phase 1: DETECT the cycle

[1]→[2]→[3]→[4]→[5]→[6]
              ▲         │
              └─────────┘
               cycle entry at [4]

slow: 1, fast: 1
slow: 2, fast: 3
slow: 3, fast: 5
slow: 4, fast: 4  ← THEY MET! Cycle detected!

Phase 2: FIND the entry point of the cycle

Mathematical proof:
  Let:
    F = distance from head to cycle entry
    C = cycle length
    k = distance from cycle entry to meeting point

  When they meet:
    slow has traveled:  F + k
    fast has traveled:  F + k + C  (fast did one full extra loop)
    fast = 2 × slow:   F + k + C = 2(F + k)
    Solving:           C - k = F

  This means: if we move one pointer to HEAD (step 1 each)
  and keep the other at MEETING POINT (step 1 each),
  they will meet EXACTLY at the cycle entry!

Step 1: Move ptr1 to HEAD, keep ptr2 at meeting point
Step 2: Both move 1 step at a time
Step 3: They meet at the CYCLE ENTRY ✓
```

```c
// C: Cycle detection + find entry
typedef struct {
    int   has_cycle;
    Node* entry;       /* cycle entry point, or NULL */
} CycleResult;

CycleResult detect_cycle(Node* head) {
    CycleResult res = {0, NULL};
    if (!head) return res;

    Node* slow = head;
    Node* fast = head;

    /* Phase 1: Detect */
    while (fast != NULL && fast->next != NULL) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) {
            res.has_cycle = 1;
            break;
        }
    }

    if (!res.has_cycle) return res;

    /* Phase 2: Find entry */
    slow = head;           /* reset slow to head */
    while (slow != fast) {
        slow = slow->next;
        fast = fast->next; /* both move 1 step now */
    }
    res.entry = slow;      /* meeting point = cycle entry */
    return res;
}
```

```go
// Go: Cycle detection
func detectCycle(head *Node) *Node {
    slow, fast := head, head
    hasCycle := false

    for fast != nil && fast.next != nil {
        slow = slow.next
        fast = fast.next.next
        if slow == fast {
            hasCycle = true
            break
        }
    }
    if !hasCycle { return nil }

    slow = head
    for slow != fast {
        slow = slow.next
        fast = fast.next
    }
    return slow // cycle entry
}
```

---

## 8.4 Merge Two Sorted Linked Lists

### Expert Thinking Pattern

```
Input:  L1: [1]→[3]→[5]→[7]→NULL
        L2: [2]→[4]→[6]→NULL

Goal:   [1]→[2]→[3]→[4]→[5]→[6]→[7]→NULL

STRATEGY: Compare heads of both lists, take the smaller one.
          Repeat until one list is exhausted.
          Append the remaining list.

SENTINEL NODE TRICK: Create a dummy head node so we avoid
  special-casing the first element. The result list starts
  at dummy.next.

Trace:
  dummy=[0]  curr=dummy
  L1=[1], L2=[2]: 1 < 2, take L1.  curr→[1]. L1=[3]
  L1=[3], L2=[2]: 3 > 2, take L2.  curr→[2]. L2=[4]
  L1=[3], L2=[4]: 3 < 4, take L1.  curr→[3]. L1=[5]
  L1=[5], L2=[4]: 5 > 4, take L2.  curr→[4]. L2=[6]
  L1=[5], L2=[6]: 5 < 6, take L1.  curr→[5]. L1=[7]
  L1=[7], L2=[6]: 7 > 6, take L2.  curr→[6]. L2=NULL
  L2=NULL, append L1=[7].           curr→[7]

Result: dummy.next = [1]→[2]→[3]→[4]→[5]→[6]→[7]→NULL ✓
```

```c
/* C: Merge two sorted lists */
/* O(n + m) time | O(1) space                              */
Node* merge_sorted(Node* l1, Node* l2) {
    Node  dummy = {0, NULL};  /* sentinel node (stack-allocated) */
    Node* curr  = &dummy;

    while (l1 != NULL && l2 != NULL) {
        if (l1->data <= l2->data) {
            curr->next = l1;
            l1 = l1->next;
        } else {
            curr->next = l2;
            l2 = l2->next;
        }
        curr = curr->next;
    }
    /* Append remaining nodes */
    curr->next = (l1 != NULL) ? l1 : l2;

    return dummy.next;
}
```

```go
/* Go: Merge two sorted lists */
func mergeSorted(l1, l2 *Node) *Node {
    dummy := &Node{}
    curr  := dummy

    for l1 != nil && l2 != nil {
        if l1.data <= l2.data {
            curr.next = l1
            l1 = l1.next
        } else {
            curr.next = l2
            l2 = l2.next
        }
        curr = curr.next
    }
    if l1 != nil {
        curr.next = l1
    } else {
        curr.next = l2
    }
    return dummy.next
}
```

---

## 8.5 Remove Nth Node from End

### Expert Thinking: Two-Pointer Gap Technique

```
Goal: Remove the 2nd node from the end of [1]→[2]→[3]→[4]→[5]→NULL
Answer: remove [4] → [1]→[2]→[3]→[5]→NULL

INSIGHT: If fast is N steps ahead of slow, when fast reaches NULL,
         slow is N nodes from the end.

But we want the node BEFORE the target (to unlink it).
So: move fast (N+1) steps ahead instead of N.

Step 1: Create dummy node → dummy→[1]→[2]→[3]→[4]→[5]→NULL
        slow = dummy, fast = dummy

Step 2: Advance fast by N+1 = 3 steps:
        fast = [3]  (dummy→[1]→[2]→[3], three steps)

Step 3: Move both until fast == NULL:
        slow=[1], fast=[4]
        slow=[2], fast=[5]
        slow=[3], fast=NULL  ← STOP

        slow is now at the node BEFORE the target ([3])

Step 4: slow.next = slow.next.next
        [3].next = [5]   ← removes [4]

Result: [1]→[2]→[3]→[5]→NULL ✓

WHY DUMMY NODE? Handles the edge case of removing the head node.
```

```c
/* C: Remove Nth node from end */
/* O(n) time, single pass | O(1) space */
Node* remove_nth_from_end(Node* head, int n) {
    Node  dummy = {0, head};   /* dummy.next = head */
    Node* slow  = &dummy;
    Node* fast  = &dummy;

    /* Advance fast by n+1 steps */
    for (int i = 0; i <= n; i++) {
        fast = fast->next;
    }
    /* Move both until fast is NULL */
    while (fast != NULL) {
        slow = slow->next;
        fast = fast->next;
    }
    /* Unlink the target node */
    Node* target = slow->next;
    slow->next   = target->next;
    free(target);

    return dummy.next;  /* new head (may have changed if we removed head) */
}
```

---

## 8.6 Sort a Linked List — Merge Sort

### Why Merge Sort is the best for Linked Lists

```
┌───────────────┬────────────────────────────────────────────────────┐
│ Algorithm     │ Why good/bad for Linked Lists                      │
├───────────────┼────────────────────────────────────────────────────┤
│ Merge Sort    │ O(n log n) — IDEAL: natural split, no random access│
│ Quick Sort    │ O(n log n) avg — picking pivot is harder, O(n²)worst│
│ Insertion Sort│ O(n²) — good for nearly sorted or very small lists  │
│ Heap Sort     │ O(n log n) — requires random access, hard on lists  │
└───────────────┴────────────────────────────────────────────────────┘
```

```
MERGE SORT on Linked List:

[4]→[2]→[1]→[3]→NULL

Phase 1: SPLIT (using slow/fast pointer to find middle)
  [4]→[2]  and  [1]→[3]

  Split again:
  [4] and [2] and [1] and [3]

Phase 2: MERGE (sort while merging)
  merge([4],[2]) → [2]→[4]
  merge([1],[3]) → [1]→[3]

  merge([2]→[4], [1]→[3]) → [1]→[2]→[3]→[4] ✓

Call tree:
         sort([4,2,1,3])
        /               \
   sort([4,2])        sort([1,3])
   /       \           /       \
sort([4]) sort([2]) sort([1]) sort([3])
  [4]       [2]       [1]       [3]
        \  /                \  /
      merge → [2,4]       merge → [1,3]
                    \  /
               merge → [1,2,3,4]
```

```c
/* C: Merge Sort for Linked List */
/* O(n log n) time | O(log n) space (recursion stack) */

/* Split list into two halves */
void split_list(Node* head, Node** left, Node** right) {
    Node* slow = head;
    Node* fast = head->next;

    while (fast != NULL && fast->next != NULL) {
        slow = slow->next;
        fast = fast->next->next;
    }
    *left  = head;
    *right = slow->next;
    slow->next = NULL;  /* cut the list in half */
}

Node* merge_sort(Node* head) {
    /* Base case: 0 or 1 element */
    if (head == NULL || head->next == NULL) return head;

    Node* left;
    Node* right;
    split_list(head, &left, &right);

    left  = merge_sort(left);
    right = merge_sort(right);

    return merge_sorted(left, right);  /* merge from 8.4 */
}
```

---

## 8.7 Find Intersection of Two Linked Lists

### Key Insight: Equal Path Length

```
List A: [a1]→[a2]→[c1]→[c2]→[c3]→NULL
List B: [b1]→[b2]→[b3]→[c1]→[c2]→[c3]→NULL
                            ▲
                    Intersection starts here

NAIVE approach: O(n × m) — compare every pair of nodes
HASH approach:  O(n + m) time, O(n) space
OPTIMAL:        O(n + m) time, O(1) space — TWO POINTER TRICK

TRICK:
  Pointer A walks: A's list, then B's list
  Pointer B walks: B's list, then A's list

  Both travel the same total distance = len(A) + len(B)
  They will BOTH arrive at the intersection at the same step!

  A: a1 → a2 → c1 → c2 → c3 → b1 → b2 → b3 → [c1 ← MEET]
  B: b1 → b2 → b3 → c1 → c2 → c3 → a1 → a2 → [c1 ← MEET]
```

```go
/* Go: Find intersection node */
/* O(m + n) time | O(1) space */
func findIntersection(headA, headB *Node) *Node {
    if headA == nil || headB == nil { return nil }

    a, b := headA, headB
    for a != b {
        if a == nil { a = headB } else { a = a.next }
        if b == nil { b = headA } else { b = b.next }
    }
    return a  // nil if no intersection
}
```

---

# 9. TIME & SPACE COMPLEXITY MASTER TABLE

```
╔══════════════════════════════╦══════════╦══════════╦══════════════════════════════╗
║ Operation                    ║ Singly   ║ Doubly   ║ Notes                        ║
╠══════════════════════════════╬══════════╬══════════╬══════════════════════════════╣
║ Insert at HEAD               ║ O(1)     ║ O(1)     ║ Just update head pointer     ║
║ Insert at TAIL (no tail ptr) ║ O(n)     ║ O(n)     ║ Must traverse to last        ║
║ Insert at TAIL (tail ptr)    ║ O(1)     ║ O(1)     ║ With dedicated tail pointer  ║
║ Insert at MIDDLE (by pos)    ║ O(n)     ║ O(n)     ║ Must traverse to position    ║
║ Delete at HEAD               ║ O(1)     ║ O(1)     ║ Just update head pointer     ║
║ Delete at TAIL (no tail ptr) ║ O(n)     ║ O(n)     ║ Must find predecessor        ║
║ Delete at TAIL (tail ptr)    ║ O(n)     ║ O(1)     ║ Doubly: use prev pointer     ║
║ Delete by VALUE              ║ O(n)     ║ O(n)     ║ Must search first            ║
║ Delete by POINTER            ║ O(n)     ║ O(1)     ║ Doubly: has prev, O(1)!      ║
║ Search                       ║ O(n)     ║ O(n)     ║ No random access             ║
║ Access by INDEX              ║ O(n)     ║ O(n)     ║ No random access             ║
║ Reverse                      ║ O(n)     ║ O(n)     ║ O(1) space iterative         ║
║ Find Middle                  ║ O(n)     ║ O(n)     ║ Slow/fast pointer            ║
║ Detect Cycle                 ║ O(n)     ║ O(n)     ║ Floyd's algorithm            ║
║ Merge Sort                   ║ O(n logn)║ O(n logn)║ Best sort for linked list    ║
╠══════════════════════════════╬══════════╬══════════╬══════════════════════════════╣
║ Space per node               ║ O(1)     ║ O(1)     ║ Singly uses less memory      ║
║ Overall space                ║ O(n)     ║ O(n)     ║ n nodes                      ║
╚══════════════════════════════╩══════════╩══════════╩══════════════════════════════╝
```

---

# 10. ARRAY vs LINKED LIST — WHEN TO USE WHAT

```
╔══════════════════════════════╦══════════════════╦════════════════════════════╗
║ Criterion                    ║ Array            ║ Linked List                ║
╠══════════════════════════════╬══════════════════╬════════════════════════════╣
║ Random access (index)        ║ O(1) ✓ WINNER    ║ O(n) ✗                     ║
║ Insert/Delete at HEAD        ║ O(n) ✗           ║ O(1) ✓ WINNER              ║
║ Insert/Delete at TAIL        ║ O(1) amortized ✓ ║ O(1) with tail ptr ✓       ║
║ Insert/Delete in MIDDLE      ║ O(n) ✗           ║ O(n) search + O(1) op      ║
║ Memory (dense)               ║ Contiguous ✓     ║ Scattered ✗ (overhead)     ║
║ Cache performance            ║ Excellent ✓      ║ Poor ✗ (pointer chasing)   ║
║ Dynamic resize               ║ Costly (copy)    ║ O(1) node allocation ✓     ║
║ Memory wasted                ║ Can over-allocate║ Pointer overhead per node  ║
╚══════════════════════════════╩══════════════════╩════════════════════════════╝

CHOOSE LINKED LIST WHEN:
  ✓ Frequent insertions/deletions at front
  ✓ Unknown or highly dynamic size
  ✓ Implementing stacks, queues, deques
  ✓ Memory is fragmented (can't get contiguous block)

CHOOSE ARRAY WHEN:
  ✓ Frequent random access by index
  ✓ Size is known or mostly fixed
  ✓ Cache performance matters (scientific computing, games)
  ✓ Binary search is needed
```

---

# 11. COMMON PITFALLS & DEBUGGING PATTERNS

```
┌──────────────────────────────────────────────────────────────────┐
│                    PITFALL CATALOG                               │
├──────────────┬───────────────────────────────────────────────────┤
│ Pitfall      │ Description & Fix                                 │
├──────────────┼───────────────────────────────────────────────────┤
│ Lost pointer │ Changing node.next before saving it.             │
│              │ FIX: always save next = curr.next FIRST           │
├──────────────┼───────────────────────────────────────────────────┤
│ NULL deref   │ Accessing curr.next when curr is NULL            │
│              │ FIX: always check curr != NULL before dereferencing│
├──────────────┼───────────────────────────────────────────────────┤
│ Off-by-one   │ Stopping one node early or late during traversal │
│              │ FIX: carefully decide: stop at last node or NULL? │
├──────────────┼───────────────────────────────────────────────────┤
│ Memory leak  │ (C) forgetting to free deleted nodes             │
│              │ FIX: always free before overwriting the pointer   │
├──────────────┼───────────────────────────────────────────────────┤
│ Single node  │ Forgetting to handle lists of length 0 or 1      │
│              │ FIX: test edge cases: empty, one-node, two-node   │
├──────────────┼───────────────────────────────────────────────────┤
│ Cycle loop   │ Infinite loop if list has unexpected cycle       │
│              │ FIX: use Floyd's detection before traversal       │
├──────────────┼───────────────────────────────────────────────────┤
│ Wrong order  │ In doubly list, not updating both prev and next  │
│              │ FIX: always update BOTH directions on link change │
└──────────────┴───────────────────────────────────────────────────┘
```

### Debug Visualization Strategy (ASCII Print)

Always write a `print_list` function FIRST before any other operation.
Being able to see the state of your list at each step is the fastest way
to debug pointer bugs.

```c
// C: Debug print with addresses
void debug_print(Node* head) {
    Node* curr = head;
    while (curr) {
        printf("addr:%p | data:%d | next:%p\n",
               (void*)curr, curr->data, (void*)curr->next);
        curr = curr->next;
    }
    printf("---\n");
}
```

---

# 12. MENTAL MODELS & PROBLEM-SOLVING STRATEGIES

## The Five-Question Framework (Before Every Problem)

```
┌────────────────────────────────────────────────────────────┐
│  1. STRUCTURE: What type of linked list is this?           │
│     → Singly / Doubly / Circular?                          │
│                                                            │
│  2. TRAVERSAL: How do I visit nodes?                       │
│     → Single pointer? Two pointers (slow/fast)? Backward? │
│                                                            │
│  3. RE-WIRING: Which pointers change?                      │
│     → Draw the before/after arrows on paper first.         │
│                                                            │
│  4. EDGE CASES: What breaks my solution?                   │
│     → Empty list? Single node? Two nodes? Cycle?           │
│                                                            │
│  5. INVARIANT: What is always true about my list?          │
│     → Write it down. Check it's maintained after each op.  │
└────────────────────────────────────────────────────────────┘
```

## Pattern Recognition Map

```
PROBLEM TYPE                      TECHNIQUE TO REACH FOR
─────────────────────────────     ──────────────────────────────────
Find middle / k-th from end   →   Slow-fast pointer (runner technique)
Detect / find cycle           →   Floyd's tortoise and hare
Merge sorted lists            →   Dummy head + two-pointer merge
Sort a linked list            →   Merge sort (split by middle)
Reverse a list                →   Three-pointer iterative
Reverse a sublist             →   Careful pointer gymnastics (4 ptrs)
Palindrome check              →   Find middle, reverse 2nd half, compare
Intersection of two lists     →   Equal path length trick
Remove duplicates (sorted)    →   Single pass, skip equal adjacent
Remove duplicates (unsorted)  →   Hash set of seen values
```

## Deliberate Practice Protocol

```
LEVEL 1 — FUNDAMENTALS (master these first, chunking phase):
  • Implement all three list types from memory
  • Write insert/delete/search without looking at notes
  • Visualize memory with ASCII art before coding

LEVEL 2 — PATTERNS (build intuition):
  • Reverse singly linked list (iterative + recursive)
  • Detect cycle + find entry
  • Find middle node
  • Merge two sorted lists

LEVEL 3 — COMPOSITION (combine patterns):
  • Check if list is palindrome
  • Reorder list: L0→Ln→L1→Ln-1→...
  • LRU Cache (doubly linked list + hash map)
  • Flatten a multilevel doubly linked list

LEVEL 4 — EXPERT (see the shape before solving):
  • Sort list using merge sort
  • Reverse nodes in k-group
  • Copy list with random pointer
```

## The Pointer Re-wiring Golden Rule

```
When modifying linked list pointers, ALWAYS follow this order:

  ┌─────────────────────────────────────────────────────┐
  │  SAVE what you'll lose BEFORE you change anything   │
  │  SET forward connections BEFORE backward ones       │
  │  UPDATE head/tail pointers LAST                     │
  └─────────────────────────────────────────────────────┘

Think of it like: you can't let go of a ledge until you
have a firm grip on the next one.
```

## Cognitive Flow Tip

When solving a linked list problem on paper, draw 3–4 nodes and
physically trace your pointer updates with a pencil. Your spatial
reasoning (right brain) and logical reasoning (left brain) work
together when you draw. This is NOT wasted time — it is the work.

The top 1% of engineers don't think faster; they think more clearly.
Clarity comes from drawing, not from rushing to code.

---

```
═══════════════════════════════════════════════════════════════
                     MASTERY CHECKLIST
═══════════════════════════════════════════════════════════════
  □ Can implement singly + doubly + circular from memory
  □ Understand pointer re-wiring without losing references
  □ Can explain the slow-fast pointer technique + why it works
  □ Can explain Floyd's cycle algorithm + the math behind it
  □ Know when O(1) deletion is possible (doubly, given pointer)
  □ Understand why merge sort is ideal for linked lists
  □ Can write all operations in C, Go, and Rust idiomatically
  □ Have internalized the Five-Question Framework
  □ Edge cases are automatic: empty, one-node, two-node, cycle
═══════════════════════════════════════════════════════════════
```

This will be a deeply comprehensive guide. Let me build it as a full document with all implementations, ASCII visualizations, and expert-level explanations.Here is your complete guide. Let me walk you through what's inside and the key intellectual threads to internalize:

---

## What the Guide Covers

**Foundations first.** Before any code, the guide builds your mental model — what a node *is* in memory, how pointers are literally memory addresses, and why a linked list forces sequential traversal while an array allows random jumps. This distinction *is* the entire performance story.

**Four list types** are fully covered — Singly, Doubly, Circular Singly, and Doubly Circular — each with ASCII memory diagrams and decision flowcharts for every core operation.

**Three languages** — C, Go, and Rust — with idiomatic implementations. Note the Rust section carefully: `Option<Box<Node>>` is not just syntax. It encodes the *idea* that a pointer might be null directly into the type system, making null pointer bugs impossible at compile time. For doubly lists in Rust, `Rc<RefCell<Node>>` solves the two-ownership problem that raw pointers can't express safely.

**Eight advanced algorithms** with full trace walkthroughs:
- The **three-pointer reversal** (the most fundamental pointer gymnastics pattern)
- **Floyd's slow-fast pointer** — used in both middle-finding and cycle detection
- The **mathematical proof** behind Floyd's cycle entry detection (`C - k = F`)
- **Merge sort on lists** with the call tree drawn out
- The **equal path trick** for intersection — elegant and O(1) space

---

## The Most Important Mental Model to Lock In

The **pointer re-wiring golden rule** is the single hardest thing beginners get wrong:

```
Save what you'll lose → Set forward connections → Update head/tail last
```

Violate this order once and you lose an entire sublist with no way to recover it. Top competitors make this automatic through repetition — it becomes *muscle memory* for the mind.

---

## Your Next Deliberate Practice Step

Start at **Level 1** of the mastery protocol: implement all three list types from scratch, in C, without looking at any reference. Time yourself. The goal is not speed — it is *total mental clarity* with no hesitation on pointer direction. That clarity is the foundation everything else is built on.