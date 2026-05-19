# ╔══════════════════════════════════════════════════════════════════╗
# ║         STACK MANIPULATION — COMPLETE MASTER GUIDE              ║
# ║     From First Principles to Expert-Level Understanding         ║
# ╚══════════════════════════════════════════════════════════════════╝

---

> **Mentor's Note:**  
> A stack is not just a data structure — it is a *thinking model*. Every time you push a task to your mind, work on it, then pop back to the previous thought, you're doing stack operations. Your brain uses a call stack. The universe itself stacks layers of abstraction. Mastering the stack means mastering *ordered, disciplined thought*.

---

# TABLE OF CONTENTS

```
1.  FOUNDATIONS — What Is a Stack?
2.  VOCABULARY & TERMINOLOGY (Every term explained)
3.  INTERNAL STRUCTURE — How Memory Looks
4.  CORE OPERATIONS — The 5 Pillars
5.  OPERATION COMPLEXITY ANALYSIS
6.  WHAT YOU CAN DO WITH A STACK (Complete Catalogue)
7.  WHAT YOU CANNOT DO WITH A STACK (Hard Limitations)
8.  COMMON MISTAKES & PITFALLS (With Diagrams)
9.  STACK VARIANTS
    9a. Min Stack
    9b. Max Stack
    9c. Monotonic Stack (Increasing & Decreasing)
    9d. Two-Stack Queue
    9e. Double-Ended Stack
10. ALGORITHM FLOW & DECISION TREES
11. IMPLEMENTATION — C (Array-based & Linked-list)
12. IMPLEMENTATION — Go (Slice-based & Generic)
13. IMPLEMENTATION — Rust (Safe, Idiomatic)
14. REAL-WORLD APPLICATIONS (Deep Dive)
15. MENTAL MODELS FOR STACK THINKING
16. DELIBERATE PRACTICE EXERCISES
```

---

# PART 1: FOUNDATIONS — WHAT IS A STACK?

## 1.1 The Concept

A **stack** is a linear data structure that follows the **LIFO** principle:

```
         L I F O
         |   |   |   |
         L = Last
         I = In
         F = First
         O = Out

     The LAST item you PUT IN is the FIRST item you GET OUT.
```

Think of a physical stack of plates in a cafeteria:

```
     ┌─────────────┐
     │   Plate 5   │  ← You can ONLY take from here (TOP)
     ├─────────────┤
     │   Plate 4   │
     ├─────────────┤
     │   Plate 3   │
     ├─────────────┤
     │   Plate 2   │
     ├─────────────┤
     │   Plate 1   │  ← First plate placed (BOTTOM)
     └─────────────┘
          ////         (Table surface)
```

You cannot take Plate 3 without first removing Plates 5 and 4.
This constraint is **intentional and powerful** — it enforces ordered access.

## 1.2 The Formal Definition

A stack is a collection of elements with two primary operations:
- **push(element)** — add element to the top
- **pop()** — remove and return the top element

All operations happen at **one end only**: the **TOP**.

---

# PART 2: VOCABULARY & TERMINOLOGY

> Every expert knows their vocabulary cold. Internalize these.

| Term | Definition | Analogy |
|------|-----------|---------|
| **Top** | The current highest element; the only accessible element | Surface of a stack of papers |
| **Bottom** | The first element ever pushed; cannot be accessed directly | Foundation of a building |
| **Push** | Insert an element onto the top | Place a plate on top |
| **Pop** | Remove and return the top element | Take the top plate |
| **Peek / Top** | Read the top element WITHOUT removing it | Look at the top plate label |
| **isEmpty** | Check if the stack has zero elements | Is the shelf empty? |
| **isFull** | Check if a fixed-size stack is at capacity (only for array stacks) | Shelf is full |
| **Overflow** | Pushing onto a full stack | Plate falls off |
| **Underflow** | Popping from an empty stack | Reaching for a plate that doesn't exist |
| **Stack Pointer (SP)** | An index or pointer tracking the top position | Your finger pointing to the top |
| **Capacity** | Maximum number of elements (fixed-size stacks only) | Shelf size |
| **Size / Count** | Current number of elements | How many plates are stacked |
| **Frame** | A unit of data on a call stack (used in recursion/function calls) | One function's workspace |
| **LIFO** | Last In, First Out — the ordering principle | Most recent is most accessible |
| **Monotonic** | A stack property where elements are in strictly increasing or decreasing order | Like a staircase |
| **Sentinel** | A dummy value placed at the bottom to simplify boundary checks | A floor marker |

---

# PART 3: INTERNAL STRUCTURE — HOW MEMORY LOOKS

## 3.1 Array-Based Stack (Static Size)

The most common implementation uses an **array** with a **top pointer** (index).

```
  MEMORY LAYOUT (Array of size 6):

  Index:  [0]    [1]    [2]    [3]    [4]    [5]
          ┌──────┬──────┬──────┬──────┬──────┬──────┐
  Array:  │  10  │  20  │  30  │  40  │  ░░░ │  ░░░ │
          └──────┴──────┴──────┴──────┴──────┴──────┘
                                  ▲
                                  │
                             top = 3
                    (points to last filled index)

  ░░░ = uninitialized / garbage memory (not part of stack)

  Stack contents (conceptually, bottom to top):
  BOTTOM [10, 20, 30, 40] TOP
```

### What the top pointer means:
```
  State          top value    Meaning
  ─────────────────────────────────────
  Empty stack      -1         No elements
  After push(10)    0         Index 0 has the only element
  After push(20)    1         Index 1 is top
  After push(30)    2         Index 2 is top
  After pop()       1         Index 1 is again the top
```

### Memory addresses (concrete example):

```
  Base address of array: 0x1000
  Each element: 4 bytes (int32)

  Address  Index  Value    Role
  ──────────────────────────────────────
  0x1000   [0]    10       Bottom of stack
  0x1004   [1]    20
  0x1008   [2]    30
  0x100C   [3]    40       ← top pointer = 3 (address 0x100C)
  0x1010   [4]    ???      Garbage (not part of stack)
  0x1014   [5]    ???      Garbage (not part of stack)
```

## 3.2 Linked-List-Based Stack (Dynamic Size)

Each element is a **node** with a value and a pointer to the node below it.

```
   TOP
    │
    ▼
  ┌──────┬──────┐     ┌──────┬──────┐     ┌──────┬──────┐
  │  40  │  ●───┼────▶│  30  │  ●───┼────▶│  20  │  ●───┼────▶ NULL
  └──────┴──────┘     └──────┴──────┘     └──────┴──────┘
  [Node 4: Top]        [Node 3]            [Node 2: ...Bottom]

  Each node:
  ┌───────────┬───────────┐
  │   value   │   *next   │
  └───────────┴───────────┘
       data       pointer to node below
```

### The push operation on a linked list:

```
  BEFORE push(50):
  top ──▶ [40│●]──▶[30│●]──▶[20│NULL]

  STEP 1: Create new node
          new_node = Node{value: 50, next: NULL}

  STEP 2: Set new_node.next = current top
          new_node ──▶ [40│●]──▶[30│●]──▶[20│NULL]
          [50│●]

  STEP 3: Update top = new_node
          top ──▶ [50│●]──▶[40│●]──▶[30│●]──▶[20│NULL]

  AFTER push(50):
  top ──▶ [50│●]──▶[40│●]──▶[30│●]──▶[20│NULL]
```

### The pop operation on a linked list:

```
  BEFORE pop():
  top ──▶ [50│●]──▶[40│●]──▶[30│●]──▶[20│NULL]

  STEP 1: Save top.value = 50 (to return)
  STEP 2: Save temp = top (the node to delete)
  STEP 3: Move top = top.next
          top ──▶ [40│●]──▶[30│●]──▶[20│NULL]
  STEP 4: Free temp (deallocate [50│●])

  AFTER pop() returns 50:
  top ──▶ [40│●]──▶[30│●]──▶[20│NULL]
```

## 3.3 Dynamic Array Stack (Vec / slice based)

Most practical implementations use a dynamic array (like Rust's `Vec<T>` or Go's slice):

```
  Initial capacity = 4:
  ┌────┬────┬────┬────┐
  │ 10 │ 20 │ 30 │ 40 │   len=4, cap=4
  └────┴────┴────┴────┘
                  ▲ top

  push(50) → capacity exceeded → GROW (typically 2x):
  ┌────┬────┬────┬────┬────┬────┬────┬────┐
  │ 10 │ 20 │ 30 │ 40 │ 50 │    │    │    │   len=5, cap=8
  └────┴────┴────┴────┴────┴────┴────┴────┘
                       ▲ top
  (old memory freed, new block allocated, data copied)
```

---

# PART 4: CORE OPERATIONS — THE 5 PILLARS

## 4.1 PUSH — Adding to the Stack

### Concept:
Place a new element on top. The new element becomes the new top.

```
  BEFORE push(99):         AFTER push(99):

  ┌─────┐                  ┌─────┐
  │  40 │ ← top            │  99 │ ← NEW top
  ├─────┤                  ├─────┤
  │  30 │                  │  40 │
  ├─────┤                  ├─────┤
  │  20 │                  │  30 │
  ├─────┤                  ├─────┤
  │  10 │ ← bottom         │  20 │
  └─────┘                  ├─────┤
                            │  10 │ ← bottom
                            └─────┘
```

### Algorithm (Array-based):
```
  push(value):
    1. Check if stack is FULL (top == capacity - 1)
       → If full: OVERFLOW error
    2. Increment top pointer: top = top + 1
    3. Store value at top position: array[top] = value
```

### Algorithm (Linked-list-based):
```
  push(value):
    1. Create new_node with given value
    2. Set new_node.next = current top (link to existing stack)
    3. Update top = new_node
```

---

## 4.2 POP — Removing from the Stack

### Concept:
Remove and return the top element. The element below becomes the new top.

```
  BEFORE pop():            AFTER pop() returns 40:

  ┌─────┐                  ┌─────┐
  │  40 │ ← top            │  30 │ ← NEW top
  ├─────┤                  ├─────┤
  │  30 │                  │  20 │
  ├─────┤                  ├─────┤
  │  20 │                  │  10 │ ← bottom
  ├─────┤                  └─────┘
  │  10 │ ← bottom
  └─────┘
```

### Algorithm (Array-based):
```
  pop():
    1. Check if stack is EMPTY (top == -1)
       → If empty: UNDERFLOW error
    2. Save value = array[top]
    3. Decrement top: top = top - 1
    4. Return value

  NOTE: The value at array[top+1] still exists in memory!
        But the stack LOGICALLY no longer contains it.
        (This is important for security-sensitive code.)
```

### The Phantom Value Problem:
```
  After pop(), the old data lingers in memory:

  Index:  [0]    [1]    [2]    [3]    [4]
          ┌──────┬──────┬──────┬──────┬──────┐
  Array:  │  10  │  20  │  30  │  40  │  ░░░ │
          └──────┴──────┴──────┴──────┴──────┘
                           ▲
                        top = 2
                  (40 still in memory at index 3,
                   but top pointer says stack ends at 2)

  The value 40 is a "phantom" — it's in RAM but
  not logically accessible through stack operations.
```

---

## 4.3 PEEK / TOP — Reading Without Removing

### Concept:
Look at the top element **without modifying** the stack.

```
  BEFORE peek():           AFTER peek() returns 40:

  ┌─────┐                  ┌─────┐
  │  40 │ ← top            │  40 │ ← top   ← UNCHANGED
  ├─────┤                  ├─────┤
  │  30 │                  │  30 │
  ├─────┤                  ├─────┤
  │  20 │                  │  20 │
  └─────┘                  └─────┘

  Stack is IDENTICAL before and after peek()
```

### Algorithm:
```
  peek():
    1. Check if stack is EMPTY
       → If empty: error
    2. Return array[top]   (do NOT change top)
```

---

## 4.4 isEmpty — Checking Empty State

```
  isEmpty():
    Return (top == -1)      // Array-based
    Return (top == NULL)    // Linked-list-based
    Return (len == 0)       // Dynamic array

  Visual:
  Empty Stack:              Non-Empty Stack:
  ┌─────┐                  ┌─────┐
  │     │  top = -1         │  30 │  top = 2
  │     │  isEmpty: TRUE    ├─────┤  isEmpty: FALSE
  │     │                   │  20 │
  └─────┘                   ├─────┤
                             │  10 │
                             └─────┘
```

---

## 4.5 isFull — Checking Full State (Array-based only)

```
  isFull():
    Return (top == capacity - 1)

  Example (capacity = 4):
  ┌────┬────┬────┬────┐
  │ 10 │ 20 │ 30 │ 40 │   top = 3, capacity = 4
  └────┴────┴────┴────┘   3 == 4-1 → isFull: TRUE
```

---

# PART 5: OPERATION COMPLEXITY ANALYSIS

```
  ┌────────────────────┬──────────────┬─────────────────────────────────┐
  │ Operation          │ Time         │ Notes                           │
  ├────────────────────┼──────────────┼─────────────────────────────────┤
  │ push               │ O(1)*        │ *Amortized for dynamic arrays.  │
  │                    │              │  Worst case O(n) on resize.     │
  ├────────────────────┼──────────────┼─────────────────────────────────┤
  │ pop                │ O(1)         │ Always constant                 │
  ├────────────────────┼──────────────┼─────────────────────────────────┤
  │ peek / top         │ O(1)         │ Always constant                 │
  ├────────────────────┼──────────────┼─────────────────────────────────┤
  │ isEmpty            │ O(1)         │ Simple comparison               │
  ├────────────────────┼──────────────┼─────────────────────────────────┤
  │ isFull             │ O(1)         │ Simple comparison               │
  ├────────────────────┼──────────────┼─────────────────────────────────┤
  │ Search element     │ O(n)         │ NOT a native stack op.          │
  │                    │              │ Must pop to reach an element.   │
  ├────────────────────┼──────────────┼─────────────────────────────────┤
  │ Access by index    │ O(1)*        │ *Only if using array internally │
  │                    │              │  and you bypass stack interface  │
  └────────────────────┴──────────────┴─────────────────────────────────┘

  Space Complexity:
  ┌────────────────────┬──────────────┬─────────────────────────────────┐
  │ Array (static)     │ O(capacity)  │ Fixed allocation, may waste     │
  │ Array (dynamic)    │ O(n)         │ Grows as needed                 │
  │ Linked list        │ O(n)         │ Each node has pointer overhead  │
  └────────────────────┴──────────────┴─────────────────────────────────┘
```

### Amortized O(1) Explained:
```
  Push operations on a dynamic array (like Vec in Rust):

  Capacity: 1 → 2 → 4 → 8 → 16

  push 1: O(1)    [just insert]
  push 2: O(2)    [resize + copy 1 + insert 1]
  push 3: O(1)    [just insert]
  push 4: O(4)    [resize + copy 3 + insert 1]
  push 5: O(1)    [just insert]
  push 6: O(1)    [just insert]
  push 7: O(1)    [just insert]
  push 8: O(8)    [resize + copy 7 + insert 1]
  ...

  Total work for n pushes: O(n)
  Work per push: O(n)/n = O(1) amortized

  The expensive resizes are "amortized" (spread) across all pushes.
```

---

# PART 6: WHAT YOU CAN DO WITH A STACK

## ✅ CAN-DO #1: Reverse a Sequence

Pushing all elements then popping reverses order.

```
  Input:  [1, 2, 3, 4, 5]

  After pushing all:
  ┌─────┐
  │  5  │ ← top
  ├─────┤
  │  4  │
  ├─────┤
  │  3  │
  ├─────┤
  │  2  │
  ├─────┤
  │  1  │ ← bottom
  └─────┘

  Pop all: 5, 4, 3, 2, 1

  Output: [5, 4, 3, 2, 1]  ← Reversed!
```

## ✅ CAN-DO #2: Check Balanced Parentheses / Brackets

```
  Input: "({[]})"

  Processing character by character:

  Char  Stack State     Action
  ────────────────────────────────────────────
  (     [ ( ]           Opening → PUSH
  {     [ ( { ]         Opening → PUSH
  [     [ ( { [ ]       Opening → PUSH
  ]     [ ( { ]         Closing ] matches top [ → POP
  }     [ ( ]           Closing } matches top { → POP
  )     [ ]             Closing ) matches top ( → POP

  Stack empty at end? YES → BALANCED ✓

  ─────────────────────────────────────────────

  Input: "({[})"  ← UNBALANCED

  Char  Stack State     Action
  ────────────────────────────────────────────
  (     [ ( ]           PUSH
  {     [ ( { ]         PUSH
  [     [ ( { [ ]       PUSH
  }     MISMATCH!       Top is [ but closing char is } → ERROR!
```

## ✅ CAN-DO #3: Evaluate Postfix (Reverse Polish Notation)

```
  Normal (Infix):   3 + 4 * 2
  Postfix (RPN):    3 4 2 * +

  Evaluation:
  Token  Action            Stack
  ─────────────────────────────────────
  3      Push 3            [ 3 ]
  4      Push 4            [ 3, 4 ]
  2      Push 2            [ 3, 4, 2 ]
  *      Pop 2, Pop 4      [ 3, 8 ]
         Push (4*2=8)
  +      Pop 8, Pop 3      [ 11 ]
         Push (3+8=11)

  Result: 11 ✓
```

## ✅ CAN-DO #4: Convert Infix to Postfix (Shunting Yard)

```
  Infix:    A + B * C

  Algorithm uses operator precedence:
  * has higher precedence than +

  Char  Action              Output       Operator Stack
  ────────────────────────────────────────────────────
  A     Output              A
  +     Push to op stack    A            [ + ]
  B     Output              A B          [ + ]
  *     * > + precedence    A B          [ + * ]
        Push to op stack
  C     Output              A B C        [ + * ]
  End   Pop all ops         A B C * +    [ ]

  Result: "A B C * +" ✓
  Verify: B*C first, then +A → Correct!
```

## ✅ CAN-DO #5: Undo/Redo Mechanism

```
  UNDO STACK       REDO STACK

  User types "Hello":
  ┌──────────┐     ┌──────────┐
  │  "Hello" │     │  (empty) │
  └──────────┘     └──────────┘

  User types " World":
  ┌──────────────┐  ┌──────────┐
  │ "Hello World"│  │  (empty) │
  ├──────────────┤  │          │
  │  "Hello"     │  │          │
  └──────────────┘  └──────────┘

  User presses UNDO:
  Pop "Hello World" from UNDO → Push to REDO
  ┌──────────┐     ┌──────────────┐
  │  "Hello" │     │ "Hello World"│
  └──────────┘     └──────────────┘

  User presses REDO:
  Pop "Hello World" from REDO → Push to UNDO
  ┌──────────────┐  ┌──────────┐
  │ "Hello World"│  │  (empty) │
  ├──────────────┤  │          │
  │  "Hello"     │  │          │
  └──────────────┘  └──────────┘
```

## ✅ CAN-DO #6: Function Call Stack (Recursion)

```
  factorial(3):

  CALL STACK GROWS:
  ┌─────────────────┐
  │ factorial(0)    │ ← top (base case, returns 1)
  ├─────────────────┤
  │ factorial(1)    │ (waits for factorial(0))
  ├─────────────────┤
  │ factorial(2)    │ (waits for factorial(1))
  ├─────────────────┤
  │ factorial(3)    │ ← bottom (original call)
  └─────────────────┘

  CALL STACK UNWINDS:
  factorial(0) returns 1
  factorial(1) returns 1 * 1 = 1
  factorial(2) returns 2 * 1 = 2
  factorial(3) returns 3 * 2 = 6
```

## ✅ CAN-DO #7: DFS (Depth-First Search)

```
  Graph:
       A
      / \
     B   C
    / \
   D   E

  DFS using a stack:

  Step  Stack         Visited
  ─────────────────────────────────
  Init  [ A ]         {}
  1     [ B, C ]      {A}        (pop A, push neighbors B, C)
  2     [ D, E, C ]   {A,B}      (pop B, push neighbors D, E)
  3     [ E, C ]      {A,B,D}    (pop D, no unvisited neighbors)
  4     [ C ]         {A,B,D,E}  (pop E, no unvisited neighbors)
  5     [ ]           {A,B,D,E,C}(pop C, no unvisited neighbors)

  Order visited: A → B → D → E → C
```

## ✅ CAN-DO #8: Browser History Navigation

```
  BACK STACK           FORWARD STACK     CURRENT PAGE
  ─────────────────────────────────────────────────────

  Visit google.com:
  [ google.com ]       [ ]               google.com

  Visit anthropic.com:
  [ google.com         [ ]               anthropic.com
    anthropic.com ]

  Visit claude.ai:
  [ google.com         [ ]               claude.ai
    anthropic.com
    claude.ai     ]

  Press BACK:
  [ google.com         [ claude.ai ]     anthropic.com
    anthropic.com ]

  Press FORWARD:
  [ google.com         [ ]               claude.ai
    anthropic.com
    claude.ai     ]
```

## ✅ CAN-DO #9: Next Greater Element (Monotonic Stack)

```
  Input: [2, 1, 2, 4, 3, 1]
  Find the next greater element for each index.

  Process right-to-left with a decreasing monotonic stack:

  i=5, val=1: stack=[]       NGE[5]=-1   push 1    stack=[1]
  i=4, val=3: stack=[1]      pop 1(1<3)  NGE[4]=-1 push 3   stack=[3]
  i=3, val=4: stack=[3]      pop 3(3<4)  NGE[3]=-1 push 4   stack=[4]
  i=2, val=2: stack=[4]      NGE[2]=4    push 2    stack=[4,2]
  i=1, val=1: stack=[4,2]    NGE[1]=2    push 1    stack=[4,2,1]
  i=0, val=2: stack=[4,2,1]  pop 1(1<2) pop 2(2≤2) NGE[0]=4 stack=[4,2]

  Result: [4, 2, 4, -1, -1, -1]
```

## ✅ CAN-DO #10: Sort a Stack

```
  You can sort a stack using a temporary stack.

  Input stack: [3, 1, 4, 1, 5]  (top = 5)

  Algorithm:
  - Pop from input
  - While temp is not empty AND temp.top > current:
      pop from temp → push back to input
  - Push current to temp

  Visual trace:
  Input    Temp     Current
  [3,1,4,1] [5]      -
  [3,1,4]   [5,1]    -  ← 1 < 5, just push
  [3,1]     [5,4,1]  -  ← pop 1 back, 1<4, push 4... complex
  ...
  Final temp (bottom to top): [1,1,3,4,5]  ← sorted ascending
```

---

# PART 7: WHAT YOU CANNOT DO WITH A STACK

> Understanding limitations is just as important as understanding capabilities.
> These are **hard constraints** by the LIFO interface — not bugs.

## ❌ CANNOT #1: Random Access by Index

```
  You CANNOT do:  stack[2]  (reach element at position 2 directly)

  WHY:
  ┌─────┐
  │  40 │ ← top   (accessible)
  ├─────┤
  │  30 │          YOU CANNOT ACCESS THIS WITHOUT POPPING 40 FIRST
  ├─────┤
  │  20 │          YOU CANNOT ACCESS THIS WITHOUT POPPING 40 AND 30
  ├─────┤
  │  10 │ ← bottom  YOU CANNOT ACCESS THIS WITHOUT EMPTYING THE STACK
  └─────┘

  To "access" 20: pop 40, pop 30, peek 20 — destroying the order!

  Exception: If you know the underlying array, you CAN do array[i],
             but this BYPASSES the stack abstraction and is wrong.
```

## ❌ CANNOT #2: Search Efficiently

```
  Searching for value 20 in stack [10, 20, 30, 40]:

  The ONLY legal way:
  1. Pop 40 — is it 20? NO
  2. Pop 30 — is it 20? NO
  3. Pop 20 — is it 20? YES! — found at step 3

  Problem: You've destroyed the top 3 elements!
  Fix: Save popped elements, then push them back → O(n) either way

  A stack offers NO mechanism for direct search.
  It is not designed for search — use a hash map or sorted array instead.
```

## ❌ CANNOT #3: Insert in the Middle

```
  Stack: [10, 20, 40, 50]  (missing 30 between 20 and 40)

  You CANNOT do:  stack.insert(position=2, value=30)

  To insert 30 between 20 and 40:
  1. Pop 50 → temp_store [50]
  2. Pop 40 → temp_store [50, 40]
  3. Push 30
  4. Push 40
  5. Push 50

  Time: O(n) — proportional to how deep you need to go.
  This is NOT a stack operation; you're using it as a general array.
```

## ❌ CANNOT #4: Delete from the Middle or Bottom

```
  Stack: [10, 20, 30, 40, 50]

  You CANNOT directly remove 20 (not at top).

  Same workaround: pop above, remove target, push back.
  Same O(n) cost and awkwardness.
```

## ❌ CANNOT #5: Access Both Ends

```
  A standard stack gives you ONE end: the TOP.

  You CANNOT pop from the BOTTOM without traversing the entire structure.

  TOP     →  Accessible  ✅
  BOTTOM  →  Inaccessible ❌

  (If you need access to both ends, use a DEQUE — Double-Ended Queue)
```

## ❌ CANNOT #6: Peek Below the Top Without Popping

```
  You CANNOT do: second_from_top = stack.peek(2)

  To see the second element:
  val1 = stack.pop()   // remove top temporarily
  val2 = stack.peek()  // now see what was below top
  stack.push(val1)     // put top back

  Correct, but requires 3 operations and temporarily mutates the stack.
```

## ❌ CANNOT #7: Merge Two Stacks in O(1)

```
  Stack A: [1, 2, 3] (top=3)
  Stack B: [4, 5, 6] (top=6)

  Goal: Merge into [1, 2, 3, 4, 5, 6]

  There is NO way to do this in O(1) while maintaining LIFO semantics
  and the original order of both stacks.

  With a linked list: you CAN do O(1) by pointing the bottom of one
  to the top of another, BUT this only works if you're okay with the
  elements of B all being "above" elements of A.

  True order-preserving merge: O(n).
```

## ❌ CANNOT #8: Iterate Without Destruction (Standard Stack Interface)

```
  You CANNOT "forEach" or loop through a stack without popping.

  The standard interface has no "iteration" concept.

  Workaround: Use an array with a top pointer (gives you iteration
  over the underlying array), but this is peeking under the hood.
```

## ❌ CANNOT #9: Know the Size in O(1) Without a Counter Variable

```
  If you only use a linked list without storing a size variable,
  counting elements requires traversal: O(n).

  Good implementations ALWAYS maintain a size/count variable updated
  on every push/pop to provide O(1) size queries.

  Lesson: Augment your data structure proactively!
```

---

# PART 8: COMMON MISTAKES & PITFALLS

## 🚫 MISTAKE #1: Off-by-One Error with Top Pointer

```
  TWO conventions exist — pick ONE and be consistent:

  Convention A: top points to the LAST FILLED slot
  ─────────────────────────────────────────────────
  Empty:   top = -1
  push(x): top = top + 1; array[top] = x
  pop():   val = array[top]; top = top - 1; return val
  peek():  return array[top]

  Convention B: top points to the NEXT EMPTY slot
  ────────────────────────────────────────────────
  Empty:   top = 0
  push(x): array[top] = x; top = top + 1
  pop():   top = top - 1; val = array[top]; return val
  peek():  return array[top - 1]

  MISTAKE: Mixing conventions mid-implementation!

  Mixed code (WRONG):
  push uses: array[top] = x; top++    // Convention B style
  pop uses:  val = array[top]; top--  // Convention A style
  → This reads uninitialized memory! Off-by-one!

  ALWAYS choose one convention and document it.
```

## 🚫 MISTAKE #2: Stack Overflow (Push on Full Stack)

```
  Capacity = 3, current state:
  ┌────┬────┬────┐
  │ 10 │ 20 │ 30 │   top = 2, capacity = 3, FULL
  └────┴────┴────┘

  push(40) without checking isFull:
  top becomes 3, array[3] is OUTSIDE the array!

  Memory:
  Address:   [0x100] [0x104] [0x108] [0x10C]
             │  10  │  20  │  30  │  ????  │ ← WRITING HERE!
                                              (corrupting other memory)

  C/C++ result: Undefined behavior, memory corruption, crash.
  Rust result:  Compile-time or runtime panic (safe).
  Go result:    Index out of range panic.

  ALWAYS check bounds before push:
  if (top == capacity - 1) { handle_overflow(); return; }
```

## 🚫 MISTAKE #3: Stack Underflow (Pop on Empty Stack)

```
  Empty stack (top = -1):

  pop() without checking isEmpty:
  val = array[-1]  ← INVALID MEMORY ACCESS

  In C: May read memory before the array → garbage or crash
  In Rust: Will panic (bounds check)
  In Go: Will panic (index out of range)

  ALWAYS check before pop:
  if (top == -1) { handle_underflow(); return; }
```

## 🚫 MISTAKE #4: Memory Leak in Linked-List Stack (C)

```
  In C, when you pop from a linked-list stack,
  you MUST free the node. Forgetting to free causes memory leaks.

  WRONG:
  pop():
    if (top == NULL) return ERROR;
    val = top->value;
    top = top->next;    // ← The old node is LEAKED! Never freed!
    return val;

  CORRECT:
  pop():
    if (top == NULL) return ERROR;
    val = top->value;
    Node* old = top;
    top = top->next;
    free(old);          // ← FREE the old node
    return val;

  Visual of the leak:
  Before pop:  top ──▶ [40│●]──▶[30│●]──▶[20│NULL]
  After WRONG: top ──▶ [30│●]──▶[20│NULL]
               [40│●] is still in heap — lost pointer, never freed!
```

## 🚫 MISTAKE #5: Forgetting to Handle the Empty Case After Multiple Pops

```
  Common pattern in algorithms: pop in a loop

  while (!stack.isEmpty()) {
      process(stack.pop());
  }

  MISTAKE: Checking isEmpty only at the start, then popping multiple:

  // Bug: What if the stack has exactly 1 element?
  a = stack.pop();  // OK
  b = stack.pop();  // UNDERFLOW! Stack is now empty after first pop!
  result = a + b;

  CORRECT:
  if (stack.size() < 2) { return error; }
  b = stack.pop();
  a = stack.pop();
  result = a + b;

  Note: b is popped first (it was on top), a was below b.
  ORDER MATTERS in the pop sequence!
```

## 🚫 MISTAKE #6: Confusing LIFO Order When Reconstructing

```
  Push sequence:  push(1), push(2), push(3)

  Stack internals (top at right conceptually):
  Bottom → [1, 2, 3] ← Top

  Pop sequence: 3, 2, 1  (REVERSED from push order)

  MISTAKE: Assuming pop order = push order

  Example: Reversing a string "ABC"
  Push: A, B, C
  Stack: A(bottom) → B → C(top)
  Pop: C, B, A → Output "CBA"  ← Correct reversal

  But if you wrote:
  Output first pop = 'A'  ← WRONG! First pop = 'C'!

  Mental model: The stack is a mirror in time.
  What goes in LAST comes out FIRST.
```

## 🚫 MISTAKE #7: Not Resetting Popped Slots (Security)

```
  In security-sensitive applications, after popping:

  Array: [10, 20, 30, 40, ...]
                        ↑ top (just decremented, 40 "popped")

  The value 40 STILL EXISTS at array[3] in memory.
  If this array holds sensitive data (passwords, keys),
  that data lingers until overwritten.

  SECURE pop():
    val = array[top];
    array[top] = 0;    // ← Zero out before decrementing
    top--;
    return val;

  In Rust, Vec::pop() handles this correctly for owned types.
  In Go, you should manually zero the slot.
  In C, you must manually zero the slot.
```

## 🚫 MISTAKE #8: Stack Overflow in Recursion

```
  Every function call pushes a FRAME onto the OS call stack.

  factorial(100000):
  ┌──────────────────────┐
  │ factorial(100000)    │
  ├──────────────────────┤
  │ factorial(99999)     │
  ├──────────────────────┤
  │ factorial(99998)     │
  ├──────────────────────┤
  │ ...                  │ ← OS stack is limited (~1-8 MB typically)
  ├──────────────────────┤
  │ factorial(1)         │ ← This may NEVER be reached!
  └──────────────────────┘
        STACK OVERFLOW!

  Fix: Use iteration + explicit stack, or tail recursion + TCO.
  In Rust: The compiler can do tail-call optimization (TCO) in some cases.
  In Go: Goroutine stacks grow dynamically (segmented stacks) but still limited.
  In C: No TCO guarantee; use iterative approach.
```

## 🚫 MISTAKE #9: Monotonic Stack Direction Error

```
  MISTAKE: Using a monotonic increasing stack when decreasing is needed.

  Problem: "Find the previous smaller element for each element"

  Input: [3, 1, 2]

  With a DECREASING stack (WRONG for this problem):
  Process 3: push 3        stack=[3]
  Process 1: 3>1, pop 3,   stack=[], push 1  PSE[1]=NONE ✓
  Process 2: 1<2, don't pop, push 2  PSE[2]=1 ✓
  Hmm, this actually works...

  BUT with a deliberately WRONG setup for "next greater":
  The mistake is often popping when you should be preserving
  or vice versa. Rule to internalize:

  FIND NEXT GREATER    → Monotonic DECREASING stack (pop when smaller)
  FIND NEXT SMALLER    → Monotonic INCREASING stack (pop when larger)
  FIND PREV GREATER    → Same as next greater but process differently
  FIND PREV SMALLER    → Same as next smaller but process differently

  Always DRAW the stack state on paper before coding!
```

## 🚫 MISTAKE #10: Shallow Copy of Stack

```
  In Go:
  stack1 := []int{1, 2, 3}
  stack2 := stack1           // WRONG! Shallow copy!
  stack2 = append(stack2, 4) // Modifies underlying array!

  stack1 may now see {1, 2, 3, 4} depending on capacity.

  CORRECT (deep copy):
  stack2 := make([]int, len(stack1))
  copy(stack2, stack1)

  In Rust:
  let stack1 = vec![1, 2, 3];
  let stack2 = stack1;          // MOVE — stack1 no longer valid
  let stack2 = stack1.clone();  // DEEP COPY — both valid
```

---

# PART 9: STACK VARIANTS

## 9a. MIN STACK

A stack that supports O(1) retrieval of the **minimum element**.

```
  Naive: To find minimum, pop everything and find min → O(n). BAD.

  Smart Design: Use TWO stacks — one for values, one for minimums.

  push(5): val_stack=[5]    min_stack=[5]   (5 is new min)
  push(3): val_stack=[5,3]  min_stack=[5,3] (3 < 5, 3 is new min)
  push(7): val_stack=[5,3,7] min_stack=[5,3,3] (7 > 3, min stays 3)
  push(1): val_stack=[5,3,7,1] min_stack=[5,3,3,1] (1 < 3, new min)

  get_min() = min_stack.top() = 1  → O(1) ✓

  After pop():
  val_stack=[5,3,7] min_stack=[5,3,3]
  get_min() = 3  → still correct ✓

  ┌──────────────────────────────────────────────┐
  │ val_stack        │ min_stack                 │
  │ ┌───┐            │ ┌───┐                     │
  │ │ 1 │ ← top      │ │ 1 │ ← top (global min) │
  │ ├───┤            │ ├───┤                     │
  │ │ 7 │            │ │ 3 │ (min ignoring top)  │
  │ ├───┤            │ ├───┤                     │
  │ │ 3 │            │ │ 3 │ (min of bottom 2)   │
  │ ├───┤            │ ├───┤                     │
  │ │ 5 │            │ │ 5 │                     │
  │ └───┘            │ └───┘                     │
  └──────────────────────────────────────────────┘
```

## 9b. MAX STACK

Same concept as Min Stack but tracking maximum:

```
  push(3): val=[3] max=[3]
  push(7): val=[3,7] max=[3,7]  (7 > 3)
  push(2): val=[3,7,2] max=[3,7,7]  (7 >= 2, max stays 7)
  get_max() = 7 → O(1) ✓
```

## 9c. MONOTONIC STACK

A stack that maintains a **sorted invariant** (increasing or decreasing) among its elements.

```
  MONOTONIC INCREASING STACK:
  (Bottom to top: values are increasing)

  push(3): stack = [3]
  push(5): 5 > 3, push   stack = [3, 5]
  push(2): 2 < 5, pop 5   stack = [3]
              2 < 3, pop 3   stack = []
              push 2         stack = [2]
  push(4): 4 > 2, push   stack = [2, 4]
  push(6): 6 > 4, push   stack = [2, 4, 6]

  Final: [2, 4, 6]  ← Increasing from bottom to top ✓

  ─────────────────────────────────────────────────

  MONOTONIC DECREASING STACK:
  (Bottom to top: values are decreasing)

  push(6): stack = [6]
  push(4): 4 < 6, push   stack = [6, 4]
  push(7): 7 > 4, pop 4   stack = [6]
              7 > 6, pop 6   stack = []
              push 7         stack = [7]
  push(2): 2 < 7, push   stack = [7, 2]

  Final: [7, 2]  ← Decreasing from bottom to top ✓
```

### When to use which:
```
  Problem                            Stack Type
  ─────────────────────────────────────────────────────────
  Next Greater Element               Monotonic Decreasing
  Next Smaller Element               Monotonic Increasing
  Previous Greater Element           Monotonic Decreasing (R to L)
  Largest Rectangle in Histogram     Monotonic Increasing
  Trapping Rainwater                 Monotonic Decreasing
  Stock Span Problem                 Monotonic Decreasing
```

## 9d. TWO-STACK QUEUE

Implement a QUEUE (FIFO) using TWO STACKS (LIFO).

```
  Queue operations: enqueue (add to back), dequeue (remove from front)

  Use two stacks: INBOX and OUTBOX

  ENQUEUE(x):  push x onto INBOX

  DEQUEUE():
    If OUTBOX is empty:
      Move ALL elements from INBOX to OUTBOX (reverses order)
    Pop from OUTBOX

  Example:
  enqueue(1): INBOX=[1]   OUTBOX=[]
  enqueue(2): INBOX=[1,2] OUTBOX=[]
  enqueue(3): INBOX=[1,2,3] OUTBOX=[]

  dequeue():
    OUTBOX empty → move all from INBOX:
    INBOX=[]  OUTBOX=[3,2,1]  (top=1, which was enqueued first)
    pop OUTBOX → returns 1 ✓ (FIFO!)

  dequeue():
    OUTBOX not empty → pop directly
    INBOX=[]  OUTBOX=[3,2]  → returns 2 ✓

  enqueue(4): INBOX=[4]   OUTBOX=[3,2]

  dequeue():
    OUTBOX not empty → pop → returns 2... wait:
    OUTBOX=[3,2] top=2, pop → returns 2 ✓

  Amortized O(1) per operation!
  Each element is moved at most ONCE from INBOX to OUTBOX.
```

## 9e. DOUBLE-ENDED STACK (Deque-like behavior)

Two stacks sharing a single array:

```
  Array of size 8:
  ┌────┬────┬────┬────┬────┬────┬────┬────┐
  │ A  │ B  │    │    │    │    │ Y  │ Z  │
  └────┴────┴────┴────┴────┴────┴────┴────┘
    ↑                              ↑
  top1=1                         top2=6
  (Stack1 grows →)              (Stack2 grows ←)

  Stack1 (left):  [A, B]  (top1 = 1)
  Stack2 (right): [Z, Y]  (top2 = 6, Y is top of stack2)

  Free space: indices 2-5 (4 slots)

  Overflow only when top1 + 1 == top2 (they collide in the middle)
  Efficient use of space!
```

---

# PART 10: ALGORITHM FLOW & DECISION TREES

## 10.1 General Stack Operation Flowchart

```
  ┌─────────────────────────────────────────────────────────────┐
  │                    STACK OPERATION                          │
  └─────────────────────────────┬───────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                   ▼
          [ PUSH ]           [ POP ]            [ PEEK ]
              │                  │                   │
              ▼                  ▼                   ▼
       ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
       │ isFull()?   │    │ isEmpty()?  │    │ isEmpty()?  │
       └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
          YES │  NO           YES │  NO           YES │  NO
              │   │               │   │               │   │
              ▼   ▼               ▼   ▼               ▼   ▼
           ERROR  │            ERROR  │            ERROR  │
                  │                   │                   │
                  ▼                   ▼                   ▼
           top = top + 1       val = arr[top]      return arr[top]
           arr[top] = val      top = top - 1
           (done)              return val
```

## 10.2 Balanced Brackets Decision Tree

```
  For each character c in the string:
  ┌──────────────────────────────┐
  │   Is c an opening bracket?  │
  │   ( or [ or {                │
  └──────────────┬───────────────┘
             YES │         NO
                 ▼          ▼
           PUSH c       Is c a closing bracket?
                        ) or ] or }
                              │
                         YES  │
                              ▼
                    ┌──────────────────┐
                    │ Is stack empty?  │
                    └───────┬──────────┘
                        YES │     NO
                            ▼      ▼
                         RETURN  does stack.top match c?
                         FALSE    (  ↔ )
                                  [  ↔ ]
                                  {  ↔ }
                                  │
                              YES │     NO
                                  ▼      ▼
                               POP     RETURN FALSE
                                │
                                ▼
                    Continue to next character

  After processing all characters:
  ┌──────────────────┐
  │ Is stack empty?  │
  └──────┬───────────┘
     YES │      NO
         ▼       ▼
      BALANCED  UNBALANCED
```

## 10.3 Monotonic Stack Decision Tree

```
  For each element x in array (processing left to right):
  ┌────────────────────────────────────────────────────┐
  │ What type of monotonic stack are we maintaining?   │
  └────────────────────┬───────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
     [INCREASING]            [DECREASING]
            │                       │
            ▼                       ▼
  ┌──────────────────┐    ┌──────────────────┐
  │ while !empty AND │    │ while !empty AND │
  │ stack.top >= x   │    │ stack.top <= x   │
  └────────┬─────────┘    └────────┬─────────┘
           │                       │
           ▼                       ▼
        POP top                 POP top
        (record result          (record result
         if needed)              if needed)
           │                       │
           └───────────┬───────────┘
                        ▼
                    PUSH x onto stack
                        │
                        ▼
                 Continue to next element
```

---

# PART 11: IMPLEMENTATION IN C

## 11.1 Array-Based Stack in C

```c
/*
 * stack_array.c
 *
 * A fixed-capacity stack implemented with an array.
 * All operations are O(1) except error handling.
 *
 * Memory Layout:
 *   data[]:  [bottom, ..., top, garbage, ...]
 *   top:     index of the topmost element (-1 if empty)
 *   capacity: maximum number of elements
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>  /* for memset in secure_pop */

#define STACK_CAPACITY 100

/* ─── Data Structure ─────────────────────────────────────────── */

typedef struct {
    int   data[STACK_CAPACITY];  /* storage array                */
    int   top;                   /* index of topmost element     */
    int   capacity;              /* maximum allowed elements     */
} Stack;

/* ─── Initialization ─────────────────────────────────────────── */

/*
 * Initialize stack to empty state.
 * top = -1 means "no elements".
 */
void stack_init(Stack *s) {
    s->top      = -1;
    s->capacity = STACK_CAPACITY;
}

/* ─── State Queries ──────────────────────────────────────────── */

bool stack_is_empty(const Stack *s) {
    return s->top == -1;
}

bool stack_is_full(const Stack *s) {
    return s->top == s->capacity - 1;
}

int stack_size(const Stack *s) {
    return s->top + 1;
}

/* ─── Core Operations ────────────────────────────────────────── */

/*
 * push: Add element to the top.
 * Returns true on success, false on overflow.
 */
bool stack_push(Stack *s, int value) {
    if (stack_is_full(s)) {
        fprintf(stderr, "[ERROR] Stack overflow: cannot push %d\n", value);
        return false;
    }
    s->top++;            /* Step 1: move top pointer up          */
    s->data[s->top] = value; /* Step 2: store value at new top  */
    return true;
}

/*
 * pop: Remove and return the top element.
 * Returns true on success, false on underflow.
 * Value is written to *out.
 */
bool stack_pop(Stack *s, int *out) {
    if (stack_is_empty(s)) {
        fprintf(stderr, "[ERROR] Stack underflow: cannot pop from empty\n");
        return false;
    }
    *out = s->data[s->top];  /* Step 1: read top value           */
    s->data[s->top] = 0;     /* Step 2: zero out (security)      */
    s->top--;                /* Step 3: move top pointer down     */
    return true;
}

/*
 * peek: Read top element without removing it.
 * Returns true on success, false if empty.
 * Value is written to *out.
 */
bool stack_peek(const Stack *s, int *out) {
    if (stack_is_empty(s)) {
        fprintf(stderr, "[ERROR] Cannot peek empty stack\n");
        return false;
    }
    *out = s->data[s->top];
    return true;
}

/* ─── Debug / Display ────────────────────────────────────────── */

void stack_print(const Stack *s) {
    printf("Stack [size=%d, capacity=%d]:\n", stack_size(s), s->capacity);
    if (stack_is_empty(s)) {
        printf("  (empty)\n");
        return;
    }
    /* Print from top to bottom for readability */
    for (int i = s->top; i >= 0; i--) {
        if (i == s->top) {
            printf("  [%d] %d  ← top\n", i, s->data[i]);
        } else if (i == 0) {
            printf("  [%d] %d  ← bottom\n", i, s->data[i]);
        } else {
            printf("  [%d] %d\n", i, s->data[i]);
        }
    }
}

/* ─── Example Usage ──────────────────────────────────────────── */

int main(void) {
    Stack s;
    stack_init(&s);

    /* Push elements */
    stack_push(&s, 10);
    stack_push(&s, 20);
    stack_push(&s, 30);
    stack_push(&s, 40);
    stack_print(&s);

    /* Peek */
    int top_val;
    stack_peek(&s, &top_val);
    printf("Peek: %d\n", top_val);

    /* Pop */
    int popped;
    stack_pop(&s, &popped);
    printf("Popped: %d\n", popped);
    stack_print(&s);

    /* Underflow test */
    Stack empty;
    stack_init(&empty);
    int dummy;
    stack_pop(&empty, &dummy);  /* Should print error */

    return 0;
}

/*
 * OUTPUT:
 * Stack [size=4, capacity=100]:
 *   [3] 40  ← top
 *   [2] 30
 *   [1] 20
 *   [0] 10  ← bottom
 * Peek: 40
 * Popped: 40
 * Stack [size=3, capacity=100]:
 *   [2] 30  ← top
 *   [1] 20
 *   [0] 10  ← bottom
 * [ERROR] Stack underflow: cannot pop from empty
 */
```

## 11.2 Linked-List-Based Stack in C

```c
/*
 * stack_linked.c
 *
 * Dynamic stack using singly linked list.
 * No fixed capacity — grows until heap is exhausted.
 * Each push: malloc one Node. Each pop: free one Node.
 *
 * Memory Layout (top to bottom):
 *   top ──▶ [val│●]──▶[val│●]──▶[val│NULL]
 *            newest       ...      oldest
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

/* ─── Node Structure ─────────────────────────────────────────── */

typedef struct Node {
    int         value;  /* payload                               */
    struct Node *next;  /* pointer to node below (towards bottom) */
} Node;

/* ─── Stack Structure ────────────────────────────────────────── */

typedef struct {
    Node *top;    /* pointer to topmost node, NULL if empty      */
    int   size;   /* current number of elements, O(1) query      */
} LinkedStack;

/* ─── Initialization ─────────────────────────────────────────── */

void linked_stack_init(LinkedStack *s) {
    s->top  = NULL;
    s->size = 0;
}

/* ─── State Queries ──────────────────────────────────────────── */

bool linked_stack_is_empty(const LinkedStack *s) {
    return s->top == NULL;
}

int linked_stack_size(const LinkedStack *s) {
    return s->size;
}

/* ─── Core Operations ────────────────────────────────────────── */

bool linked_stack_push(LinkedStack *s, int value) {
    Node *new_node = (Node *)malloc(sizeof(Node));
    if (new_node == NULL) {
        fprintf(stderr, "[ERROR] Out of memory on push(%d)\n", value);
        return false;
    }
    new_node->value = value;
    new_node->next  = s->top;   /* link new node to current top  */
    s->top          = new_node; /* update top to new node        */
    s->size++;
    return true;
}

bool linked_stack_pop(LinkedStack *s, int *out) {
    if (linked_stack_is_empty(s)) {
        fprintf(stderr, "[ERROR] Stack underflow on pop()\n");
        return false;
    }
    *out       = s->top->value;  /* capture value before freeing */
    Node *old  = s->top;         /* save pointer for freeing     */
    s->top     = s->top->next;   /* advance top to node below    */
    free(old);                   /* free the memory!             */
    s->size--;
    return true;
}

bool linked_stack_peek(const LinkedStack *s, int *out) {
    if (linked_stack_is_empty(s)) {
        fprintf(stderr, "[ERROR] Cannot peek empty stack\n");
        return false;
    }
    *out = s->top->value;
    return true;
}

/*
 * Free all nodes: must be called to avoid memory leaks.
 * Traverses from top to bottom, freeing each node.
 */
void linked_stack_destroy(LinkedStack *s) {
    Node *current = s->top;
    while (current != NULL) {
        Node *next = current->next;
        free(current);
        current = next;
    }
    s->top  = NULL;
    s->size = 0;
}

/* ─── Debug / Display ────────────────────────────────────────── */

void linked_stack_print(const LinkedStack *s) {
    printf("LinkedStack [size=%d]:\n", s->size);
    if (linked_stack_is_empty(s)) {
        printf("  (empty)\n");
        return;
    }
    Node *curr = s->top;
    bool is_top = true;
    while (curr != NULL) {
        if (is_top) {
            printf("  %d  ← top\n", curr->value);
            is_top = false;
        } else if (curr->next == NULL) {
            printf("  %d  ← bottom\n", curr->value);
        } else {
            printf("  %d\n", curr->value);
        }
        curr = curr->next;
    }
}

/* ─── Example Usage ──────────────────────────────────────────── */

int main(void) {
    LinkedStack s;
    linked_stack_init(&s);

    linked_stack_push(&s, 100);
    linked_stack_push(&s, 200);
    linked_stack_push(&s, 300);
    linked_stack_print(&s);

    int val;
    linked_stack_pop(&s, &val);
    printf("Popped: %d\n", val);
    linked_stack_print(&s);

    linked_stack_destroy(&s);  /* ALWAYS clean up! */
    printf("After destroy, size = %d\n", linked_stack_size(&s));

    return 0;
}

/*
 * OUTPUT:
 * LinkedStack [size=3]:
 *   300  ← top
 *   200
 *   100  ← bottom
 * Popped: 300
 * LinkedStack [size=2]:
 *   200  ← top
 *   100  ← bottom
 * After destroy, size = 0
 */
```

---

# PART 12: IMPLEMENTATION IN GO

## 12.1 Slice-Based Stack in Go

```go
// stack_slice.go
//
// Idiomatic Go stack using a slice.
// Go slices are dynamic arrays — perfect for stacks.
// This implementation is simple, clean, and performant.

package main

import (
    "errors"
    "fmt"
)

// ─── Sentinel errors ─────────────────────────────────────────────────────────
// Using sentinel errors lets callers check with errors.Is().

var (
    ErrStackUnderflow = errors.New("stack underflow: pop from empty stack")
    ErrStackEmpty     = errors.New("stack is empty")
)

// ─── Stack Structure ──────────────────────────────────────────────────────────

// Stack is a LIFO container backed by a Go slice.
// The "top" is always the last element (highest index).
//
// Memory layout:
//   data: [bottom, ..., top]
//          data[0]     data[len-1]
type Stack[T any] struct {
    data []T // underlying slice; len(data) == size
}

// NewStack creates an empty stack with optional pre-allocated capacity.
// Pre-allocating avoids reallocations if you know the expected size.
func NewStack[T any](initialCap int) *Stack[T] {
    return &Stack[T]{
        data: make([]T, 0, initialCap),
    }
}

// ─── State Queries ────────────────────────────────────────────────────────────

func (s *Stack[T]) IsEmpty() bool {
    return len(s.data) == 0
}

func (s *Stack[T]) Size() int {
    return len(s.data)
}

// ─── Core Operations ──────────────────────────────────────────────────────────

// Push adds value to the top of the stack.
// Time: O(1) amortized — append may reallocate backing array.
//
// Internals of append:
//   If len < cap: place value at data[len], len++       → O(1)
//   If len == cap: allocate 2x slice, copy, then append → O(n) rarely
func (s *Stack[T]) Push(value T) {
    s.data = append(s.data, value)
}

// Pop removes and returns the top element.
// Returns ErrStackUnderflow if stack is empty.
// Time: O(1)
//
// IMPORTANT: We set data[len-1] to zero value before shrinking.
// This releases references for GC (critical for pointer/interface types).
func (s *Stack[T]) Pop() (T, error) {
    if s.IsEmpty() {
        var zero T
        return zero, ErrStackUnderflow
    }
    top := len(s.data) - 1
    val := s.data[top]     // capture value

    var zero T
    s.data[top] = zero     // zero out for GC friendliness (important for pointers!)
    s.data = s.data[:top]  // shrink slice length by 1 (no dealloc)

    return val, nil
}

// Peek returns the top element without removing it.
// Returns ErrStackEmpty if stack is empty.
// Time: O(1)
func (s *Stack[T]) Peek() (T, error) {
    if s.IsEmpty() {
        var zero T
        return zero, ErrStackEmpty
    }
    return s.data[len(s.data)-1], nil
}

// ─── Debug / Display ──────────────────────────────────────────────────────────

func (s *Stack[T]) Print() {
    fmt.Printf("Stack [size=%d, cap=%d]:\n", len(s.data), cap(s.data))
    if s.IsEmpty() {
        fmt.Println("  (empty)")
        return
    }
    // Print top to bottom
    for i := len(s.data) - 1; i >= 0; i-- {
        switch i {
        case len(s.data) - 1:
            fmt.Printf("  %v  ← top\n", s.data[i])
        case 0:
            fmt.Printf("  %v  ← bottom\n", s.data[i])
        default:
            fmt.Printf("  %v\n", s.data[i])
        }
    }
}

// ─── Example Usage ────────────────────────────────────────────────────────────

func main() {
    // Integer stack
    s := NewStack[int](8)
    s.Push(10)
    s.Push(20)
    s.Push(30)
    s.Push(40)
    s.Print()

    if val, err := s.Peek(); err == nil {
        fmt.Printf("Peek: %d\n", val)
    }

    if val, err := s.Pop(); err == nil {
        fmt.Printf("Popped: %d\n", val)
    }
    s.Print()

    // Underflow test
    empty := NewStack[int](4)
    _, err := empty.Pop()
    if errors.Is(err, ErrStackUnderflow) {
        fmt.Println("Caught underflow:", err)
    }

    // String stack (generics in action)
    strStack := NewStack[string](4)
    strStack.Push("hello")
    strStack.Push("world")
    strStack.Print()
}

/*
 * OUTPUT:
 * Stack [size=4, cap=8]:
 *   40  ← top
 *   30
 *   20
 *   10  ← bottom
 * Peek: 40
 * Popped: 40
 * Stack [size=3, cap=8]:
 *   30  ← top
 *   20
 *   10  ← bottom
 * Caught underflow: stack underflow: pop from empty stack
 * Stack [size=2, cap=4]:
 *   world  ← top
 *   hello  ← bottom
 */
```

## 12.2 Min Stack in Go

```go
// min_stack.go
//
// A stack that supports O(1) retrieval of the minimum element.
// Uses a parallel "min tracker" slice.

package main

import (
    "errors"
    "fmt"
)

var ErrMinStackEmpty = errors.New("min stack is empty")

// MinStack tracks both values and running minimums.
//
// Invariant:
//   mins[i] = minimum of all elements from 0 to i in values
//   i.e., the minimum of the entire stack when size = i+1
type MinStack struct {
    values []int
    mins   []int
}

func NewMinStack() *MinStack {
    return &MinStack{}
}

func (ms *MinStack) Push(val int) {
    ms.values = append(ms.values, val)

    if len(ms.mins) == 0 || val < ms.mins[len(ms.mins)-1] {
        ms.mins = append(ms.mins, val)    // new minimum
    } else {
        // Repeat current minimum (maintain parallel structure)
        ms.mins = append(ms.mins, ms.mins[len(ms.mins)-1])
    }
}

func (ms *MinStack) Pop() (int, error) {
    if len(ms.values) == 0 {
        return 0, ErrMinStackEmpty
    }
    top := len(ms.values) - 1
    val := ms.values[top]

    ms.values = ms.values[:top]
    ms.mins = ms.mins[:top]     // keep both in sync!

    return val, nil
}

func (ms *MinStack) Peek() (int, error) {
    if len(ms.values) == 0 {
        return 0, ErrMinStackEmpty
    }
    return ms.values[len(ms.values)-1], nil
}

func (ms *MinStack) GetMin() (int, error) {
    if len(ms.mins) == 0 {
        return 0, ErrMinStackEmpty
    }
    return ms.mins[len(ms.mins)-1], nil  // O(1)!
}

func main() {
    ms := NewMinStack()
    ms.Push(5)
    ms.Push(3)
    ms.Push(7)
    ms.Push(1)
    ms.Push(4)

    min, _ := ms.GetMin()
    fmt.Println("Min:", min)  // 1

    ms.Pop()  // remove 4
    ms.Pop()  // remove 1
    min, _ = ms.GetMin()
    fmt.Println("Min after 2 pops:", min)  // 3
}
```

---

# PART 13: IMPLEMENTATION IN RUST

## 13.1 Safe, Idiomatic Rust Stack

```rust
//! stack.rs
//!
//! A complete, production-quality stack in idiomatic Rust.
//! Uses Vec<T> internally — the most idiomatic choice.
//!
//! Design decisions:
//!   - Generic over T with no unnecessary bounds
//!   - Returns Option<T> — Rust's idiomatic way to signal absence
//!   - No panics in the public API (unlike Vec::pop which returns Option)
//!   - Implements standard traits: Display, Debug, Iterator, Default

use std::fmt;

/// A LIFO stack backed by a Vec<T>.
///
/// # Memory Layout
/// ```text
/// data: [bottom, ..., top]
///        data[0]   data[len-1]
/// ```
///
/// # Examples
/// ```
/// let mut s: Stack<i32> = Stack::new();
/// s.push(10);
/// s.push(20);
/// assert_eq!(s.pop(), Some(20));
/// assert_eq!(s.peek(), Some(&10));
/// ```
#[derive(Debug, Default, Clone)]
pub struct Stack<T> {
    data: Vec<T>,
}

impl<T> Stack<T> {
    // ─── Constructors ───────────────────────────────────────────────

    /// Creates an empty stack.
    pub fn new() -> Self {
        Stack { data: Vec::new() }
    }

    /// Creates a stack with a pre-allocated capacity.
    /// Use this when you know the approximate maximum size.
    /// Avoids reallocations → better performance.
    pub fn with_capacity(cap: usize) -> Self {
        Stack {
            data: Vec::with_capacity(cap),
        }
    }

    // ─── State Queries ───────────────────────────────────────────────

    /// Returns true if the stack contains no elements.
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    /// Returns the number of elements in the stack.
    pub fn len(&self) -> usize {
        self.data.len()
    }

    // ─── Core Operations ─────────────────────────────────────────────

    /// Pushes a value onto the top of the stack.
    ///
    /// # Time Complexity
    /// O(1) amortized. Occasionally O(n) when Vec reallocates.
    ///
    /// # Memory
    /// When Vec reallocates, it doubles capacity.
    /// The old allocation is freed, a new 2x one is used.
    pub fn push(&mut self, value: T) {
        self.data.push(value);
        // Vec::push handles all capacity logic:
        // - if len < cap: place at data[len], increment len  → O(1)
        // - if len == cap: allocate 2x, copy, push           → O(n) rarely
    }

    /// Removes and returns the top element.
    ///
    /// Returns `Some(value)` if the stack is non-empty.
    /// Returns `None` if the stack is empty (never panics).
    ///
    /// # Time Complexity
    /// O(1) — Vec::pop simply decrements len.
    pub fn pop(&mut self) -> Option<T> {
        self.data.pop()
        // Vec::pop internally:
        //   - if empty: returns None
        //   - otherwise: decrements len, returns Some(data[old_len-1])
        //   - The dropped T is properly destructor-called (Drop trait)
    }

    /// Returns a reference to the top element without removing it.
    ///
    /// Returns `Some(&value)` if non-empty, `None` if empty.
    ///
    /// # Time Complexity
    /// O(1)
    pub fn peek(&self) -> Option<&T> {
        self.data.last()
    }

    /// Returns a mutable reference to the top element.
    /// Useful for modifying the top in-place.
    pub fn peek_mut(&mut self) -> Option<&mut T> {
        self.data.last_mut()
    }

    // ─── Advanced Operations ─────────────────────────────────────────

    /// Clears all elements from the stack.
    /// Each element's Drop impl is called in LIFO order.
    pub fn clear(&mut self) {
        self.data.clear();
    }

    /// Returns an iterator from top to bottom (LIFO order).
    ///
    /// Does NOT consume the stack — borrows it.
    pub fn iter(&self) -> impl Iterator<Item = &T> {
        self.data.iter().rev()
    }

    /// Drains the stack from top to bottom, consuming it.
    pub fn into_iter_lifo(self) -> impl Iterator<Item = T> {
        self.data.into_iter().rev()
    }
}

// ─── Display ──────────────────────────────────────────────────────────────────

impl<T: fmt::Display> fmt::Display for Stack<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Stack[")?;
        for (i, item) in self.data.iter().rev().enumerate() {
            if i > 0 {
                write!(f, ", ")?;
            }
            write!(f, "{}", item)?;
        }
        write!(f, "] (top → bottom)")
    }
}

// ─── From iterator ────────────────────────────────────────────────────────────

impl<T> FromIterator<T> for Stack<T> {
    /// Build a stack from an iterator.
    /// The last element of the iterator becomes the top.
    fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self {
        Stack {
            data: Vec::from_iter(iter),
        }
    }
}

// ─── Min Stack in Rust ────────────────────────────────────────────────────────

/// A stack that additionally supports O(1) minimum retrieval.
///
/// Uses two parallel Vecs:
///   values: the actual data
///   mins:   mins[i] = minimum of values[0..=i]
pub struct MinStack<T: Ord + Clone> {
    values: Vec<T>,
    mins: Vec<T>,
}

impl<T: Ord + Clone> MinStack<T> {
    pub fn new() -> Self {
        MinStack {
            values: Vec::new(),
            mins: Vec::new(),
        }
    }

    pub fn push(&mut self, val: T) {
        let new_min = match self.mins.last() {
            Some(current_min) => {
                if val < *current_min {
                    val.clone()
                } else {
                    current_min.clone()
                }
            }
            None => val.clone(),  // first element is always the min
        };
        self.values.push(val);
        self.mins.push(new_min);
    }

    pub fn pop(&mut self) -> Option<T> {
        if self.values.is_empty() {
            return None;
        }
        self.mins.pop();          // keep mins in sync
        self.values.pop()
    }

    pub fn peek(&self) -> Option<&T> {
        self.values.last()
    }

    /// Returns the minimum element in O(1).
    pub fn get_min(&self) -> Option<&T> {
        self.mins.last()
    }

    pub fn is_empty(&self) -> bool {
        self.values.is_empty()
    }
}

// ─── Monotonic Stack utility ──────────────────────────────────────────────────

/// Finds the "Next Greater Element" for each index using a monotonic stack.
///
/// Returns a Vec where result[i] = the index of the next element
/// greater than arr[i], or -1 if none exists.
///
/// Algorithm:
///   Maintain a monotonically decreasing stack of INDICES.
///   For each element x at index i:
///     While stack is not empty AND arr[stack.top()] < x:
///       pop j from stack → arr[i] is the NGE for index j
///       result[j] = i
///     push i
///   Remaining elements in stack have no NGE → result[j] = -1
pub fn next_greater_element(arr: &[i32]) -> Vec<i32> {
    let n = arr.len();
    let mut result = vec![-1i32; n];  // default: no greater element
    let mut stack: Vec<usize> = Vec::new();  // stores INDICES

    for i in 0..n {
        // While the current element is greater than arr[stack.top()]:
        while let Some(&top_idx) = stack.last() {
            if arr[top_idx] < arr[i] {
                stack.pop();
                result[top_idx] = i as i32;  // arr[i] is NGE for top_idx
            } else {
                break;  // monotonicity maintained, stop popping
            }
        }
        stack.push(i);
    }
    // Elements remaining in stack have no NGE → result already -1

    result
}

/// Checks if brackets in a string are balanced.
///
/// Supported pairs: () [] {}
pub fn is_balanced(s: &str) -> bool {
    let mut stack: Vec<char> = Vec::new();

    for ch in s.chars() {
        match ch {
            '(' | '[' | '{' => stack.push(ch),
            ')' => {
                if stack.pop() != Some('(') {
                    return false;
                }
            }
            ']' => {
                if stack.pop() != Some('[') {
                    return false;
                }
            }
            '}' => {
                if stack.pop() != Some('{') {
                    return false;
                }
            }
            _ => {} // ignore non-bracket characters
        }
    }

    stack.is_empty()  // balanced only if stack is fully emptied
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_operations() {
        let mut s: Stack<i32> = Stack::new();
        assert!(s.is_empty());

        s.push(10);
        s.push(20);
        s.push(30);

        assert_eq!(s.len(), 3);
        assert_eq!(s.peek(), Some(&30));
        assert_eq!(s.pop(), Some(30));
        assert_eq!(s.pop(), Some(20));
        assert_eq!(s.len(), 1);
        assert_eq!(s.pop(), Some(10));
        assert!(s.is_empty());
        assert_eq!(s.pop(), None);  // no panic, returns None
    }

    #[test]
    fn test_min_stack() {
        let mut ms = MinStack::new();
        ms.push(5);
        ms.push(3);
        ms.push(7);
        ms.push(1);

        assert_eq!(ms.get_min(), Some(&1));
        ms.pop();  // remove 1
        assert_eq!(ms.get_min(), Some(&3));  // min is now 3
        ms.pop();  // remove 7
        assert_eq!(ms.get_min(), Some(&3));
    }

    #[test]
    fn test_next_greater_element() {
        assert_eq!(
            next_greater_element(&[4, 5, 2, 25]),
            vec![1, -1, 3, -1]
            // 4's NGE is at index 1 (value 5)
            // 5 has no NGE
            // 2's NGE is at index 3 (value 25)
            // 25 has no NGE
        );
    }

    #[test]
    fn test_balanced_brackets() {
        assert!(is_balanced("({[]})"));
        assert!(is_balanced(""));
        assert!(!is_balanced("({[}])"));
        assert!(!is_balanced("((("));
        assert!(!is_balanced(")"));
    }

    #[test]
    fn test_iteration() {
        let s: Stack<i32> = [1, 2, 3, 4, 5].iter().copied().collect();
        let top_to_bottom: Vec<i32> = s.iter().copied().collect();
        assert_eq!(top_to_bottom, vec![5, 4, 3, 2, 1]);
    }
}

// ─── Main ─────────────────────────────────────────────────────────────────────

fn main() {
    // Basic stack demo
    let mut s: Stack<i32> = Stack::with_capacity(8);
    s.push(10);
    s.push(20);
    s.push(30);
    println!("{}", s);

    println!("Peek: {:?}", s.peek());
    println!("Pop: {:?}", s.pop());
    println!("{}", s);

    // NGE demo
    let arr = [4, 5, 2, 25, 1, 3];
    let nge = next_greater_element(&arr);
    println!("\nArray:           {:?}", arr);
    println!("Next Greater Idx:{:?}", nge);

    // Balanced brackets
    let tests = ["({[]})", "({[}])", "(((", ""];
    for t in &tests {
        println!("'{}' balanced: {}", t, is_balanced(t));
    }
}

/*
 * OUTPUT:
 * Stack[30, 20, 10] (top → bottom)
 * Peek: Some(30)
 * Pop: Some(30)
 * Stack[20, 10] (top → bottom)
 *
 * Array:           [4, 5, 2, 25, 1, 3]
 * Next Greater Idx:[1, 3, 3, -1, 5, -1]
 * '({[]})' balanced: true
 * '({[}])' balanced: false
 * '(((' balanced: false
 * '' balanced: true
 */
```

---

# PART 14: REAL-WORLD APPLICATIONS (DEEP DIVE)

```
  ┌──────────────────────────────────────────────────────────────┐
  │            WHERE STACKS APPEAR IN THE REAL WORLD             │
  └──────────────────────────────────────────────────────────────┘

  1. COMPILERS & INTERPRETERS
     ─────────────────────────────────────────────────────────────
     • Call stack: tracks function calls and local variables
     • Expression parsing: infix → postfix conversion
     • Syntax checking: bracket matching, XML tag validation
     • Abstract Syntax Tree (AST) traversal (DFS)

  2. OPERATING SYSTEMS
     ─────────────────────────────────────────────────────────────
     • Every thread has its own call stack (OS-managed)
     • Interrupt handling: current state pushed, ISR runs, state popped
     • Context switching: registers pushed to stack, restored on switch

  3. TEXT EDITORS & IDEs
     ─────────────────────────────────────────────────────────────
     • Undo/redo history
     • Bracket matching highlighting
     • Code folding (nested block tracking)

  4. WEB BROWSERS
     ─────────────────────────────────────────────────────────────
     • Back/forward navigation history
     • JavaScript execution uses a call stack
     • DOM rendering (nested element traversal)

  5. GRAPH ALGORITHMS
     ─────────────────────────────────────────────────────────────
     • DFS traversal (explicit or implicit via recursion)
     • Topological sort (post-order DFS)
     • Finding strongly connected components (Tarjan's algorithm)
     • Cycle detection

  6. ARITHMETIC & EXPRESSION EVALUATION
     ─────────────────────────────────────────────────────────────
     • Scientific calculators (RPN mode)
     • Spreadsheet formula engines
     • SQL query execution plans

  7. MEMORY MANAGEMENT
     ─────────────────────────────────────────────────────────────
     • Stack-based memory allocation for local variables
     • Rust's ownership model is essentially stack-based
     • Arena allocators use stack-like push/pop

  8. GAME DEVELOPMENT
     ─────────────────────────────────────────────────────────────
     • Game state management (menu → gameplay → pause → menu)
     • Recursive path-finding algorithms
     • Undo systems (chess move history)
```

---

# PART 15: MENTAL MODELS FOR STACK THINKING

## 15.1 The "Last Worker Standing" Model

```
  Imagine a busy office:
  Every NEW task is placed on top of the pile.
  You ALWAYS work on the TOP task first.
  You cannot start an older task until all newer ones are done.

  This is exactly how recursive functions work:
  Each function call is a task on the pile.
  The most RECENTLY called function runs first.
  When it returns, you go back to the PREVIOUS task.
```

## 15.2 The "Nesting Depth" Mental Model

```
  Whenever you see NESTING in a problem, think STACK.

  HTML:   <div><p><span>text</span></p></div>
  Code:   if (a) { for (b) { while (c) { ... } } }
  Math:   ((2 + 3) * (4 - 1)) / 2
  Files:  /home/user/documents/projects/code/

  All of these are nested structures.
  A stack naturally tracks depth: push on open, pop on close.
```

## 15.3 The "Time Reversal" Mental Model

```
  A stack REVERSES the order of operations.
  - What you did LAST is undone FIRST (undo systems)
  - The most RECENT call finishes FIRST (recursion)
  - The LAST element in is the FIRST element out (string reversal)

  When you need to "undo" or "reverse", think stack immediately.
```

## 15.4 The "Pending Work" Mental Model (DFS)

```
  In DFS, the stack represents "work I haven't done yet."

  Start: push root
  Loop:
    pop → process → push unvisited neighbors

  The stack = a list of nodes whose subtrees you haven't explored.
  Deeper nodes are on top (last in) and explored first.
```

## 15.5 Pattern Recognition Table

```
  IF YOU SEE THIS IN A PROBLEM...    THINK THIS...
  ─────────────────────────────────────────────────────────────────
  "balanced parentheses"             Stack (push open, pop on close)
  "undo/redo"                        Two stacks (undo + redo)
  "convert infix to postfix"         Shunting-yard with a stack
  "evaluate expression"              Two stacks (operand + operator)
  "next greater/smaller element"     Monotonic stack
  "previous greater/smaller"         Same, different direction
  "largest rectangle"                Monotonic increasing stack
  "trapping rainwater"               Two-pointer OR monotonic stack
  "implement queue with stacks"      Two-stack queue
  "DFS iterative"                    Explicit stack (not recursion)
  "recursive solution"               Implicit stack (call stack)
  "navigate back/forward"            Two stacks (back + forward)
  "minimum/maximum at any time"      Min/Max stack (parallel tracking)
  "stock span problem"               Monotonic decreasing stack
  "asteroid collision"               Stack simulation
  "simplify path"                    Stack (push dirs, pop on ..)
```

---

# PART 16: DELIBERATE PRACTICE EXERCISES

> **Cognitive Principle: Deliberate Practice**
> Mere repetition does not build mastery. You must practice at the *edge* of your ability, with immediate feedback.
> Each exercise below is progressively harder. Solve them in order.

## Level 1: Foundation (Understand the interface)
```
  1. Implement a stack from scratch (array-based) in your language.
  2. Implement a stack using a linked list.
  3. Implement isEmpty, isFull, push, pop, peek with proper error handling.
  4. Reverse a string using a stack.
  5. Check if a string of brackets is balanced.
```

## Level 2: Application (Use the interface)
```
  6.  Evaluate a postfix expression: "3 4 2 * +"
  7.  Convert an infix expression to postfix (Shunting-Yard).
  8.  Implement a Min Stack (get_min in O(1)).
  9.  Implement a Max Stack (get_max in O(1)).
  10. Implement a Queue using two Stacks.
```

## Level 3: Algorithmic (Monotonic patterns)
```
  11. Next Greater Element for each array element.
  12. Previous Greater Element for each array element.
  13. Stock Span Problem: for each day, how many consecutive
      days before it had a smaller or equal price?
  14. Largest Rectangle in a Histogram.
  15. Trapping Rainwater (stack-based approach).
```

## Level 4: Advanced (System-level thinking)
```
  16. Sort a stack using only one additional stack.
  17. Implement a browser history simulation (back/forward).
  18. Simplify a Unix file path: "/home/./user/../docs/file"
  19. Decode a string: "3[a2[bc]]" → "abcbcabcbcabcbc"
  20. Implement a basic calculator that handles +, -, (, ).
```

## Level 5: Expert (Synthesis)
```
  21. Remove k digits from a number to make it smallest (greedy + stack).
  22. 132 Pattern problem (requires nested monotonic reasoning).
  23. Maximum Width Ramp using a monotonic stack.
  24. Sum of Subarray Minimums.
  25. Implement Tarjan's SCC algorithm (uses a stack + DFS).
```

---

# APPENDIX: QUICK REFERENCE CARD

```
  ╔══════════════════════════════════════════════════════════════════╗
  ║                    STACK CHEAT SHEET                            ║
  ╠══════════════════════════════════════════════════════════════════╣
  ║  Principle    : LIFO (Last In, First Out)                       ║
  ║  Access point : TOP only                                        ║
  ╠══════════════════╦═══════════════╦══════════════════════════════╣
  ║  Operation       ║  Time         ║  Notes                       ║
  ╠══════════════════╬═══════════════╬══════════════════════════════╣
  ║  push(x)         ║  O(1)*        ║  *Amortized for dynamic arr  ║
  ║  pop()           ║  O(1)         ║                              ║
  ║  peek()          ║  O(1)         ║                              ║
  ║  isEmpty()       ║  O(1)         ║                              ║
  ║  size()          ║  O(1)         ║  If size counter maintained  ║
  ║  search(x)       ║  O(n)         ║  Not a native stack op       ║
  ╠══════════════════╩═══════════════╩══════════════════════════════╣
  ║  CAN DO                          CANNOT DO                      ║
  ║  ─────────────────────────────   ─────────────────────────────  ║
  ║  ✅ Reverse a sequence           ❌ Random access by index      ║
  ║  ✅ Track nested depth           ❌ Search in O(1)              ║
  ║  ✅ Undo/redo                    ❌ Insert in middle            ║
  ║  ✅ DFS traversal                ❌ Delete from middle          ║
  ║  ✅ Expression evaluation        ❌ Access both ends            ║
  ║  ✅ Balanced brackets            ❌ Merge in O(1)               ║
  ║  ✅ Function call tracking       ❌ Iterate without popping*    ║
  ╠══════════════════════════════════════════════════════════════════╣
  ║  Common Mistakes                                                ║
  ║  ──────────────────────────────────────────────────────────     ║
  ║  🚫 Off-by-one error in top pointer                            ║
  ║  🚫 No overflow/underflow check                                ║
  ║  🚫 Memory leak in C (forgot free on pop)                      ║
  ║  🚫 Assuming pop order == push order                           ║
  ║  🚫 Shallow copy of Go slice stack                             ║
  ║  🚫 Wrong monotonic direction (increasing vs decreasing)       ║
  ╠══════════════════════════════════════════════════════════════════╣
  ║  Pattern Recognition                                            ║
  ║  ──────────────────────────────────────────────────────────     ║
  ║  Nesting?            → Stack                                    ║
  ║  Reversal?           → Stack                                    ║
  ║  Next greater/less?  → Monotonic Stack                         ║
  ║  Min/Max tracking?   → Parallel min/max stack                  ║
  ║  FIFO from LIFO?     → Two stacks                              ║
  ╚══════════════════════════════════════════════════════════════════╝
```

---

*"Mastery is not about how much you know — it is about how deeply you understand the few things that matter most. The stack is one of those things."*

*Study it until you dream in push and pop. Then you will see stacks everywhere.*
