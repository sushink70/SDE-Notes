# Circular Queue — Complete, In-Depth Guide
> *"Master the ring, and you master time."*

---

## Table of Contents

1. [Why Study Circular Queue?](#1-why-study-circular-queue)
2. [Prerequisite Concepts Explained](#2-prerequisite-concepts-explained)
3. [What Is a Queue? (Foundation)](#3-what-is-a-queue-foundation)
4. [The Problem with a Linear Queue](#4-the-problem-with-a-linear-queue)
5. [What Is a Circular Queue?](#5-what-is-a-circular-queue)
6. [Core Terminology](#6-core-terminology)
7. [Mental Model — The Ring Buffer](#7-mental-model--the-ring-buffer)
8. [Internal State Machine](#8-internal-state-machine)
9. [The Modulo Magic — How the Ring Works](#9-the-modulo-magic--how-the-ring-works)
10. [Detailed ASCII Visualizations](#10-detailed-ascii-visualizations)
11. [Operations — Deep Dive](#11-operations--deep-dive)
12. [Edge Cases & Tricky Scenarios](#12-edge-cases--tricky-scenarios)
13. [Full-vs-Empty Disambiguation Strategies](#13-full-vs-empty-disambiguation-strategies)
14. [Time & Space Complexity Analysis](#14-time--space-complexity-analysis)
15. [Implementation in C](#15-implementation-in-c)
16. [Implementation in Rust](#16-implementation-in-rust)
17. [Implementation in Go](#17-implementation-in-go)
18. [Variants of Circular Queue](#18-variants-of-circular-queue)
19. [Real-World Applications](#19-real-world-applications)
20. [Common Mistakes & How to Avoid Them](#20-common-mistakes--how-to-avoid-them)
21. [Expert Mental Models & Patterns](#21-expert-mental-models--patterns)
22. [Comparison Table](#22-comparison-table)

---

## 1. Why Study Circular Queue?

A Circular Queue (also called **Ring Buffer** or **Circular Buffer**) is one of the most elegant
and practically important data structures in computer science. It appears everywhere:

- **Operating Systems** — CPU scheduling (Round Robin), I/O buffering
- **Networking** — Packet buffers, sliding window protocols (TCP)
- **Audio/Video** — Real-time streaming buffers
- **Embedded Systems** — UART/serial communication buffers
- **Producer-Consumer** — The backbone of concurrent programming

Understanding the circular queue deeply builds your intuition for:
- **Modular arithmetic** (wrapping indices)
- **Pointer manipulation** (head/tail logic)
- **State machine thinking** (empty/full/partial states)
- **Amortized O(1) operations**

---

## 2. Prerequisite Concepts Explained

Before diving in, let's define every term you'll encounter:

### Array (Static Memory Block)
An array is a contiguous block of memory where each element is accessible by an index (0, 1, 2...).

```
Index:  [0] [1] [2] [3] [4]
Value:  [A] [B] [C] [D] [E]
         ^-- base address
```

### Index
A number used to point to a specific position in the array. Think of it as a "finger pointing to a slot."

### Pointer / Cursor
In the context of queues, "pointer" usually means an **index variable** (not a memory pointer) that tracks a specific position — like HEAD and TAIL.

### Modulo (%)
The remainder after division.
- `7 % 3 = 1` (because 7 = 2×3 + 1)
- `6 % 3 = 0`
- **Key use**: `(index + 1) % capacity` wraps an index back to 0 after reaching the end.

```
Capacity = 5
Index 4 → (4+1) % 5 = 0   ← wraps to beginning!
Index 3 → (3+1) % 5 = 4
Index 0 → (0+1) % 5 = 1
```

### FIFO (First In, First Out)
The first element added is the first element removed. Like a real-world queue at a ticket counter.

### Enqueue
Adding an element to the **rear (tail)** of the queue.

### Dequeue
Removing an element from the **front (head)** of the queue.

### Head (Front)
The position of the **oldest element** — the next one to be removed.

### Tail (Rear)
The position where the **next element will be inserted**.

### Capacity
The maximum number of elements the queue can hold (fixed at creation time).

### Size / Count
The **current** number of elements in the queue (varies between 0 and capacity).

---

## 3. What Is a Queue? (Foundation)

A queue is an abstract data structure that follows the **FIFO** principle.

```
ENQUEUE →  [  D  |  C  |  B  |  A  ]  → DEQUEUE
           (rear)              (front)

Insert at rear, remove from front.
```

Think of it like a line of people waiting:
- New people join at the **back**
- People leave from the **front**

A **linear (simple) queue** uses an array with two pointers:
- `front`: index of the element to remove next
- `rear`: index where the next element will go

---

## 4. The Problem with a Linear Queue

### The Wasted Space Problem

Consider a linear queue with capacity 5:

```
Step 1: Enqueue A, B, C
front=0, rear=3

[ A | B | C |   |   ]
  0   1   2   3   4
  ^front       ^rear

Step 2: Dequeue A, B
front=2, rear=3

[   |   | C |   |   ]
  0   1   2   3   4
          ^front  ^rear

Step 3: Enqueue D, E, F
front=2, rear=5 → rear is OUT OF BOUNDS!

[   |   | C | D | E ]
  0   1   2   3   4
          ^front      ^rear (= 5, beyond array!)

Now we try to add F... but rear = 5 = capacity.
Queue reports FULL even though slots 0 and 1 are empty!
```

**This is the fundamental flaw of a linear queue:**
- Slots 0 and 1 are empty but **unreachable**
- The queue falsely reports "full"
- Memory is wasted forever

### Solutions Attempted
1. **Shift all elements left** after dequeue → O(n) per dequeue, terrible performance
2. **Circular Queue** → The elegant O(1) solution

---

## 5. What Is a Circular Queue?

A circular queue **wraps around**: when the tail pointer reaches the end of the array, it circles back to index 0 — provided there's space there.

```
Linear view:    [ 0 | 1 | 2 | 3 | 4 ]

Circular view:
                    0
                 ┌──┴──┐
              4  │     │  1
                 │  ●  │
              3  │     │  2
                 └──┬──┘
                    3

The array is treated as a ring.
After index 4 comes index 0 again.
```

The key insight: **there is no "end" of the array**. Indices wrap around using modulo arithmetic.

---

## 6. Core Terminology

| Term | Meaning |
|------|---------|
| `capacity` | Max number of elements the queue can hold |
| `size` / `count` | Current number of elements |
| `head` (front) | Index of the oldest element (next to dequeue) |
| `tail` (rear) | Index where the next element will be enqueued |
| `empty` | `size == 0` |
| `full` | `size == capacity` |
| Ring Buffer | Another name for circular queue |
| Wrap-around | When an index exceeds capacity and resets to 0 |

---

## 7. Mental Model — The Ring Buffer

**Imagine a circular conveyor belt** at a sushi restaurant:

```
          [EMPTY]
      ┌────────────┐
[D]   │            │  [EMPTY]
      │   RING     │
[C]   │  BUFFER    │  [A] ← head (oldest, will be served next)
      │            │
      └────────────┘
          [B]
           ↑
          tail (next dish placed here)

Chef places dishes at TAIL.
Customer takes dishes from HEAD.
Belt keeps rotating — never hits a "wall".
```

**Key Insight**: Head and tail chase each other around the ring.
- When head == tail AND size > 0 → FULL
- When head == tail AND size == 0 → EMPTY

---

## 8. Internal State Machine

A circular queue is always in one of three states:

```
┌─────────────────────────────────────────────────────────────┐
│                    CIRCULAR QUEUE STATES                    │
└─────────────────────────────────────────────────────────────┘

         ┌──────────┐
         │  EMPTY   │◄──────────────────────────────┐
         │ size = 0 │                               │
         └────┬─────┘                               │
              │ enqueue()                           │
              ▼                                     │
         ┌──────────┐    enqueue() when         ┌──┴──────┐
         │ PARTIAL  │──── size < capacity ──────►│  FULL   │
         │ 0<size<N │◄─── dequeue() when ────────│ size=N  │
         └────┬─────┘    size == capacity        └─────────┘
              │
              │ dequeue() when size == 1
              ▼
           returns to EMPTY

TRANSITIONS:
  EMPTY   --[enqueue]--> PARTIAL
  PARTIAL --[enqueue]--> PARTIAL or FULL
  PARTIAL --[dequeue]--> PARTIAL or EMPTY
  FULL    --[dequeue]--> PARTIAL
  EMPTY   --[dequeue]--> ERROR (underflow)
  FULL    --[enqueue]--> ERROR (overflow)
```

---

## 9. The Modulo Magic — How the Ring Works

The entire circular behavior rests on **one formula**:

```
new_index = (current_index + 1) % capacity
```

Let's trace through with capacity = 5:

```
current_index  →  new_index
     0         →  (0+1)%5 = 1
     1         →  (1+1)%5 = 2
     2         →  (2+1)%5 = 3
     3         →  (3+1)%5 = 4
     4         →  (4+1)%5 = 0  ← WRAP AROUND!
     0         →  (0+1)%5 = 1  ← continues normally
```

Visual wrap-around:

```
Array indices:     0    1    2    3    4
                   ↓    ↓    ↓    ↓    ↓
                 ┌───┬────┬────┬────┬────┐
                 │   │    │    │    │    │
                 └───┴────┴────┴────┴────┘
Circular path:    0 → 1 → 2 → 3 → 4 → 0 → 1 → ...
                  ↑___________________________|
                  (wraps back)
```

### Why Does This Work?

Modulo gives you the **remainder**, which is always in range `[0, capacity-1]`.
No matter how large the index grows, `% capacity` always brings it back into bounds.

This is the same math used in:
- Clock arithmetic (12 o'clock + 3 hours = 3 o'clock, not 15 o'clock)
- Hash tables (hash % table_size)
- Day-of-week calculations

---

## 10. Detailed ASCII Visualizations

### 10.1 — Starting State (Empty Queue, capacity=6)

```
capacity = 6, size = 0

Index:  [0]  [1]  [2]  [3]  [4]  [5]
        [ ]  [ ]  [ ]  [ ]  [ ]  [ ]
         ↑
       head=0
       tail=0

head == tail AND size == 0  →  EMPTY
```

### 10.2 — After Enqueue(10), Enqueue(20), Enqueue(30)

```
capacity = 6, size = 3

Index:  [0]  [1]  [2]  [3]  [4]  [5]
        [10] [20] [30] [ ]  [ ]  [ ]
         ↑              ↑
       head=0         tail=3

head=0 (10 is the oldest, next to leave)
tail=3 (next element goes here)
```

### 10.3 — After Dequeue() × 2 → removes 10 and 20

```
capacity = 6, size = 1

Index:  [0]  [1]  [2]  [3]  [4]  [5]
        [ ]  [ ]  [30] [ ]  [ ]  [ ]
                   ↑    ↑
                 head=2 tail=3

head moved forward to 2.
Slots 0 and 1 are now FREE.
```

### 10.4 — Enqueue(40), (50), (60), (70), (80)

```
capacity = 6, size = 6  → FULL

After enqueue 40 → tail = 4
After enqueue 50 → tail = 5
After enqueue 60 → tail = (5+1)%6 = 0  ← WRAP AROUND
After enqueue 70 → tail = 1
After enqueue 80 → tail = 2 = head  → FULL!

Index:  [0]  [1]  [2]  [3]  [4]  [5]
        [60] [70] [30] [40] [50] [???]
```

Wait — let me redo this carefully with size tracking:

```
State: head=2, tail=3, size=1, data=[_,_,30,_,_,_]

Enqueue(40): data[3]=40, tail=(3+1)%6=4, size=2
Enqueue(50): data[4]=50, tail=(4+1)%6=5, size=3
Enqueue(60): data[5]=60, tail=(5+1)%6=0, size=4  ← tail wraps!
Enqueue(70): data[0]=70, tail=(0+1)%6=1, size=5
Enqueue(80): data[1]=80, tail=(1+1)%6=2, size=6  ← FULL (size==capacity)

Index:  [0]  [1]  [2]  [3]  [4]  [5]
        [70] [80] [30] [40] [50] [60]
                   ↑              
                 head=2          
                        ↑
                      tail=2  (points to head, but size=6 tells us FULL)

Circular visualization:
        ┌─────────────────────────────────────┐
        │  [70]  [80]  [30]  [40]  [50]  [60] │
        │    0     1     2     3     4     5   │
        │                ↑                    │
        │          head=2, tail=2             │
        │          size=6 → FULL             │
        └─────────────────────────────────────┘

Reading order (FIFO): 30→40→50→60→70→80
```

### 10.5 — The Ring Diagram (Full Queue)

```
              [30]  ← head (oldest)
           /        \
        [80]         [40]
         |    FULL    |
        [70]         [50]
           \        /
              [60]

Clockwise from head: 30 → 40 → 50 → 60 → 70 → 80
```

### 10.6 — The Wrap-Around Moment

```
BEFORE wrap (tail at index 5):

[  ][  ][30][40][50][60]
 0   1   2   3   4   5
             ↑           ↑
           head=2      tail=5

Enqueue(70):
  - Store 70 at data[5]? No wait...
  - Store 70 at data[tail=5], then tail=(5+1)%6 = 0

[  ][  ][30][40][50][60]... wait, we haven't used 5 yet.

Let me be precise:

head=2, tail=5, size=3

Enqueue(60):
  data[tail=5] = 60
  tail = (5+1)%6 = 0   ← WRAP!
  size = 4

State: head=2, tail=0, size=4
[  ][  ][30][40][50][60]
 0   1   2   3   4   5
 ↑           ↑
tail=0      head=2

Now tail is BEHIND head in array terms, but that's perfectly fine!
The queue is: 30 → 40 → 50 → 60
```

---

## 11. Operations — Deep Dive

### 11.1 — ENQUEUE (Insert)

**Goal**: Add an element at the tail.

**Algorithm**:
```
ENQUEUE(value):
  1. Check if FULL → if size == capacity, ERROR (overflow)
  2. Store value at data[tail]
  3. Advance tail: tail = (tail + 1) % capacity
  4. Increment size: size++
```

**Decision Tree**:
```
enqueue(val)
     │
     ▼
Is size == capacity?
     │
  YES│                    NO
     │                    │
     ▼                    ▼
  OVERFLOW!          data[tail] = val
  return error       tail = (tail+1) % cap
                     size++
                     return SUCCESS
```

**Step-by-step trace** (capacity=4):
```
Initial: head=0, tail=0, size=0, data=[_,_,_,_]

enqueue(A):
  size(0) != cap(4) → OK
  data[tail=0] = A
  tail = (0+1)%4 = 1
  size = 1
  → [A, _, _, _], head=0, tail=1

enqueue(B):
  data[1] = B, tail=2, size=2
  → [A, B, _, _], head=0, tail=2

enqueue(C):
  data[2] = C, tail=3, size=3
  → [A, B, C, _], head=0, tail=3

enqueue(D):
  data[3] = D, tail=(3+1)%4=0, size=4
  → [A, B, C, D], head=0, tail=0
  SIZE=4=CAPACITY → FULL
```

### 11.2 — DEQUEUE (Remove)

**Goal**: Remove and return the element at the head.

**Algorithm**:
```
DEQUEUE():
  1. Check if EMPTY → if size == 0, ERROR (underflow)
  2. Save value at data[head]
  3. Advance head: head = (head + 1) % capacity
  4. Decrement size: size--
  5. Return saved value
```

**Decision Tree**:
```
dequeue()
     │
     ▼
Is size == 0?
     │
  YES│                    NO
     │                    │
     ▼                    ▼
 UNDERFLOW!           val = data[head]
 return error         head = (head+1) % cap
                      size--
                      return val
```

**Step-by-step trace** (continuing from above, full queue):
```
State: [A, B, C, D], head=0, tail=0, size=4

dequeue():
  size(4) != 0 → OK
  val = data[head=0] = A
  head = (0+1)%4 = 1
  size = 3
  return A
  → [_, B, C, D], head=1, tail=0

dequeue():
  val = data[1] = B, head=2, size=2
  → [_, _, C, D], head=2, tail=0

Now enqueue(E):
  data[tail=0] = E, tail=1, size=3
  → [E, _, C, D], head=2, tail=1
  Note: slot 0 was reused! This is the circular magic.

Reading order: C → D → E  (correct FIFO)
```

### 11.3 — PEEK (Front Without Removing)

```
PEEK():
  1. Check if EMPTY → ERROR
  2. Return data[head] (do NOT modify head or size)
```

### 11.4 — IS_EMPTY

```
IS_EMPTY():
  return size == 0
```

### 11.5 — IS_FULL

```
IS_FULL():
  return size == capacity
```

### 11.6 — SIZE

```
SIZE():
  return size  (or count the elements via formula)
```

---

## 12. Edge Cases & Tricky Scenarios

### Case 1: Single-Element Queue

```
Enqueue(X): head=0, tail=1, size=1
             [X, _, _, _]

Dequeue():   val = data[0] = X
             head=1, tail=1, size=0
             [_, _, _, _]   ← EMPTY again (head == tail, size == 0)
```

### Case 2: Enqueue on Full Queue

```
capacity=3, head=0, tail=0, size=3 (FULL)
Enqueue(Y):
  size == capacity → OVERFLOW ERROR
  Do NOT modify any state.
```

### Case 3: Dequeue on Empty Queue

```
capacity=3, head=0, tail=0, size=0 (EMPTY)
Dequeue():
  size == 0 → UNDERFLOW ERROR
  Do NOT modify any state.
```

### Case 4: head == tail (Ambiguous!)

```
head == tail can mean either EMPTY or FULL:

EMPTY:  head=2, tail=2, size=0
FULL:   head=2, tail=2, size=4 (if capacity=4)

This is WHY we need a separate `size` variable
(or use one of the disambiguation strategies in Section 13).
```

### Case 5: Multiple Wrap-arounds

```
capacity=3

Enqueue A,B,C → [A,B,C], head=0, tail=0, size=3 (FULL)
Dequeue A,B,C  → [_,_,_], head=0, tail=0, size=0 (EMPTY)
Enqueue X,Y,Z  → [X,Y,Z], head=0, tail=0, size=3 (FULL)
Dequeue X      → [_,Y,Z], head=1, tail=0, size=2
Enqueue W      → data[tail=0]=W, tail=1, size=3 (FULL)
              → [W,Y,Z], head=1, tail=1

Dequeue: Y, Z, W   (correct FIFO order)
```

---

## 13. Full-vs-Empty Disambiguation Strategies

Since `head == tail` is ambiguous, there are three common strategies:

### Strategy 1: Explicit Size Counter (Recommended)

Keep a `size` variable (or `count`).

```
empty: size == 0
full:  size == capacity
```

**Pros**: Simple logic, no wasted slot, O(1) size query.
**Cons**: Extra variable to maintain.

### Strategy 2: Sacrifice One Slot

Keep one slot permanently empty. The queue is full when `(tail + 1) % capacity == head`.

```
capacity=5, but only 4 elements can be stored.

empty:  head == tail
full:   (tail + 1) % capacity == head
```

```
Example (capacity=5, max 4 elements):

Empty:   [_, _, _, _, _]  head=tail=0

Enqueue A,B,C,D:
  data[0]=A, tail=1
  data[1]=B, tail=2
  data[2]=C, tail=3
  data[3]=D, tail=4
  Check full: (4+1)%5=0 == head=0? YES → FULL

State: [A, B, C, D, _]
                    ↑
              empty slot (sacrificed)
```

**Pros**: No extra variable needed.
**Cons**: Wastes one slot; capacity is effectively `n-1`.

### Strategy 3: Use a Boolean Flag

```
is_full: boolean flag, set to true on enqueue that fills the queue,
         set to false on any dequeue.

empty:  head == tail && !is_full
full:   is_full
```

**Pros**: No wasted slot, no size variable.
**Cons**: Slightly more complex flag management.

### Comparison Table

```
┌───────────────────┬─────────────┬─────────────┬──────────────┐
│ Strategy          │ Extra Space │ Usable Slots │ Complexity   │
├───────────────────┼─────────────┼─────────────┼──────────────┤
│ Size Counter      │ O(1) int    │ N           │ Low          │
│ Sacrifice Slot    │ None        │ N-1         │ Low          │
│ Boolean Flag      │ O(1) bool   │ N           │ Medium       │
└───────────────────┴─────────────┴─────────────┴──────────────┘
```

**Expert recommendation**: Use **Strategy 1 (size counter)** for clarity and correctness. Strategy 2 is used in kernel/embedded code to avoid any extra variable.

---

## 14. Time & Space Complexity Analysis

### Time Complexity

```
┌──────────────┬─────────────┬────────────────────────────────┐
│ Operation    │ Complexity  │ Reason                         │
├──────────────┼─────────────┼────────────────────────────────┤
│ Enqueue      │ O(1)        │ Direct index access + modulo   │
│ Dequeue      │ O(1)        │ Direct index access + modulo   │
│ Peek/Front   │ O(1)        │ Direct index access            │
│ Is_Empty     │ O(1)        │ Single comparison              │
│ Is_Full      │ O(1)        │ Single comparison              │
│ Size         │ O(1)        │ Return stored counter          │
│ Search       │ O(N)        │ Must scan all elements         │
└──────────────┴─────────────┴────────────────────────────────┘
```

### Space Complexity

```
Space for queue itself:  O(N)  where N = capacity
Overhead:                O(1)  (head, tail, size variables)
Total:                   O(N)
```

### Why Is It O(1) And Not Amortized?

Unlike dynamic arrays (which occasionally resize), a circular queue has **fixed capacity**. Every operation is exactly O(1) — no amortization needed. This makes it ideal for **real-time systems** where you cannot afford occasional spikes.

---

## 15. Implementation in C

### 15.1 — Design Decisions

- Use Strategy 1 (explicit `count` field)
- Static array (fixed capacity defined at compile time via macro)
- Error codes returned (no exceptions in C)
- Clean separation of concerns

```c
/*
 * circular_queue.c
 *
 * A complete, production-quality circular queue implementation in C.
 *
 * Design:
 *   - Fixed-capacity array-based ring buffer
 *   - Uses explicit `count` to disambiguate full vs empty
 *   - All operations are O(1)
 *   - Thread-unsafe (add mutex for concurrent use)
 *
 * Author: DSA Monk
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

/* ─────────────────────────────────────────────
 *  Configuration
 * ───────────────────────────────────────────── */
#define MAX_CAPACITY 1024

/* ─────────────────────────────────────────────
 *  Error Codes
 * ───────────────────────────────────────────── */
typedef enum {
    CQ_OK         = 0,
    CQ_OVERFLOW   = -1,   /* enqueue on full queue  */
    CQ_UNDERFLOW  = -2,   /* dequeue on empty queue */
    CQ_NULL_PTR   = -3,   /* null queue pointer     */
} CQStatus;

/* ─────────────────────────────────────────────
 *  Data Type
 *  Change this to store any type you need.
 * ───────────────────────────────────────────── */
typedef int CQData;

/* ─────────────────────────────────────────────
 *  Circular Queue Structure
 * ───────────────────────────────────────────── */
typedef struct {
    CQData  data[MAX_CAPACITY];  /* internal storage array           */
    int     head;                /* index of oldest element (front)  */
    int     tail;                /* index where next element goes    */
    int     count;               /* current number of elements       */
    int     capacity;            /* maximum elements (≤ MAX_CAPACITY)*/
} CircularQueue;

/* ─────────────────────────────────────────────
 *  Initialize
 *
 *  Sets up a circular queue with the given capacity.
 *  capacity must be > 0 and <= MAX_CAPACITY.
 *
 *  Example:
 *    CircularQueue q;
 *    cq_init(&q, 8);
 * ───────────────────────────────────────────── */
CQStatus cq_init(CircularQueue *q, int capacity) {
    if (!q) return CQ_NULL_PTR;
    if (capacity <= 0 || capacity > MAX_CAPACITY) {
        fprintf(stderr, "Invalid capacity: %d\n", capacity);
        return CQ_OVERFLOW;
    }

    q->head     = 0;
    q->tail     = 0;
    q->count    = 0;
    q->capacity = capacity;

    /* Optional: zero out data array for clean debugging */
    memset(q->data, 0, sizeof(CQData) * capacity);
    return CQ_OK;
}

/* ─────────────────────────────────────────────
 *  Is Empty
 * ───────────────────────────────────────────── */
bool cq_is_empty(const CircularQueue *q) {
    return q->count == 0;
}

/* ─────────────────────────────────────────────
 *  Is Full
 * ───────────────────────────────────────────── */
bool cq_is_full(const CircularQueue *q) {
    return q->count == q->capacity;
}

/* ─────────────────────────────────────────────
 *  Size
 * ───────────────────────────────────────────── */
int cq_size(const CircularQueue *q) {
    return q->count;
}

/* ─────────────────────────────────────────────
 *  Enqueue
 *
 *  Adds `val` to the rear of the queue.
 *
 *  Algorithm:
 *    1. Check full
 *    2. Store at data[tail]
 *    3. tail = (tail + 1) % capacity
 *    4. count++
 *
 *  O(1) time.
 * ───────────────────────────────────────────── */
CQStatus cq_enqueue(CircularQueue *q, CQData val) {
    if (!q)             return CQ_NULL_PTR;
    if (cq_is_full(q))  return CQ_OVERFLOW;

    q->data[q->tail] = val;
    q->tail = (q->tail + 1) % q->capacity;
    q->count++;

    return CQ_OK;
}

/* ─────────────────────────────────────────────
 *  Dequeue
 *
 *  Removes and returns the front element.
 *
 *  Algorithm:
 *    1. Check empty
 *    2. Save data[head]
 *    3. head = (head + 1) % capacity
 *    4. count--
 *    5. Return saved value
 *
 *  O(1) time.
 * ───────────────────────────────────────────── */
CQStatus cq_dequeue(CircularQueue *q, CQData *out) {
    if (!q)              return CQ_NULL_PTR;
    if (cq_is_empty(q))  return CQ_UNDERFLOW;

    *out = q->data[q->head];
    q->head = (q->head + 1) % q->capacity;
    q->count--;

    return CQ_OK;
}

/* ─────────────────────────────────────────────
 *  Peek (Front)
 *
 *  Returns the front element WITHOUT removing it.
 * ───────────────────────────────────────────── */
CQStatus cq_peek(const CircularQueue *q, CQData *out) {
    if (!q)              return CQ_NULL_PTR;
    if (cq_is_empty(q))  return CQ_UNDERFLOW;

    *out = q->data[q->head];
    return CQ_OK;
}

/* ─────────────────────────────────────────────
 *  Peek Rear
 *
 *  Returns the most recently enqueued element.
 *  tail - 1 with wrap-around.
 * ───────────────────────────────────────────── */
CQStatus cq_peek_rear(const CircularQueue *q, CQData *out) {
    if (!q)              return CQ_NULL_PTR;
    if (cq_is_empty(q))  return CQ_UNDERFLOW;

    /* tail points to NEXT free slot, so rear is at tail-1 */
    int rear_idx = (q->tail - 1 + q->capacity) % q->capacity;
    *out = q->data[rear_idx];
    return CQ_OK;
}

/* ─────────────────────────────────────────────
 *  Clear / Reset
 *
 *  Empties the queue without deallocating.
 * ───────────────────────────────────────────── */
void cq_clear(CircularQueue *q) {
    q->head  = 0;
    q->tail  = 0;
    q->count = 0;
}

/* ─────────────────────────────────────────────
 *  Print (Debug Utility)
 *
 *  Prints the queue contents in FIFO order.
 *  Does NOT modify queue state.
 * ───────────────────────────────────────────── */
void cq_print(const CircularQueue *q) {
    if (!q || cq_is_empty(q)) {
        printf("[EMPTY QUEUE]\n");
        return;
    }

    printf("Queue (front→rear): [");
    for (int i = 0; i < q->count; i++) {
        int idx = (q->head + i) % q->capacity;
        printf("%d", q->data[idx]);
        if (i < q->count - 1) printf(", ");
    }
    printf("] | head=%d, tail=%d, count=%d, cap=%d\n",
           q->head, q->tail, q->count, q->capacity);
}

/* ─────────────────────────────────────────────
 *  Print Internal Array (Debug)
 *
 *  Shows the raw array with head/tail markers.
 * ───────────────────────────────────────────── */
void cq_print_raw(const CircularQueue *q) {
    printf("Raw array: [");
    for (int i = 0; i < q->capacity; i++) {
        if (i == q->head && i == q->tail && q->count > 0) {
            printf("H/T:%d", q->data[i]);
        } else if (i == q->head) {
            printf("H:%d", q->data[i]);
        } else if (i == q->tail) {
            printf("T:_");
        } else {
            /* check if this slot is in the queue */
            bool in_queue = false;
            for (int j = 0; j < q->count; j++) {
                if ((q->head + j) % q->capacity == i) {
                    in_queue = true;
                    break;
                }
            }
            if (in_queue) printf("%d", q->data[i]);
            else          printf("_");
        }
        if (i < q->capacity - 1) printf("|");
    }
    printf("]\n");
}

/* ─────────────────────────────────────────────
 *  MAIN — Demonstration
 * ───────────────────────────────────────────── */
int main(void) {
    CircularQueue q;
    CQData val;
    CQStatus status;

    printf("========================================\n");
    printf("     CIRCULAR QUEUE DEMO (C)\n");
    printf("========================================\n\n");

    /* Initialize with capacity 5 */
    cq_init(&q, 5);
    printf("[INIT] Capacity = 5\n");
    cq_print(&q);
    cq_print_raw(&q);

    /* Enqueue 5 elements */
    printf("\n[ENQUEUE] 10, 20, 30, 40, 50\n");
    cq_enqueue(&q, 10);
    cq_enqueue(&q, 20);
    cq_enqueue(&q, 30);
    cq_enqueue(&q, 40);
    cq_enqueue(&q, 50);
    cq_print(&q);
    cq_print_raw(&q);

    /* Try enqueue on full */
    printf("\n[ENQUEUE on FULL] Attempt to add 99\n");
    status = cq_enqueue(&q, 99);
    printf("Status: %s\n", status == CQ_OVERFLOW ? "OVERFLOW (correct!)" : "unexpected");

    /* Dequeue 3 elements */
    printf("\n[DEQUEUE x3]\n");
    cq_dequeue(&q, &val); printf("Dequeued: %d\n", val);
    cq_dequeue(&q, &val); printf("Dequeued: %d\n", val);
    cq_dequeue(&q, &val); printf("Dequeued: %d\n", val);
    cq_print(&q);
    cq_print_raw(&q);

    /* Enqueue 3 more (wraps around) */
    printf("\n[ENQUEUE with WRAP] 60, 70, 80\n");
    cq_enqueue(&q, 60);
    cq_enqueue(&q, 70);
    cq_enqueue(&q, 80);
    cq_print(&q);
    cq_print_raw(&q);

    /* Peek */
    cq_peek(&q, &val);
    printf("\n[PEEK front] = %d\n", val);
    cq_peek_rear(&q, &val);
    printf("[PEEK rear]  = %d\n", val);

    /* Drain the queue */
    printf("\n[DRAIN all elements]\n");
    while (!cq_is_empty(&q)) {
        cq_dequeue(&q, &val);
        printf("Dequeued: %d\n", val);
    }
    cq_print(&q);

    /* Try dequeue on empty */
    printf("\n[DEQUEUE on EMPTY]\n");
    status = cq_dequeue(&q, &val);
    printf("Status: %s\n", status == CQ_UNDERFLOW ? "UNDERFLOW (correct!)" : "unexpected");

    return 0;
}
```

### 15.2 — C: Key Design Points

```
Memory Layout (capacity=5):
  struct CircularQueue {
    int data[1024]; ← static array, stack or global allocation
    int head;       ← 4 bytes
    int tail;       ← 4 bytes
    int count;      ← 4 bytes
    int capacity;   ← 4 bytes
  }

Cache behavior: data[] is contiguous → cache-friendly access.
No heap allocation → no malloc/free overhead.
```

### 15.3 — C: Dynamic Allocation Version

```c
/* For truly variable capacity, use heap allocation: */

typedef struct {
    CQData  *data;     /* heap-allocated array */
    int      head;
    int      tail;
    int      count;
    int      capacity;
} CQDynamic;

CQDynamic* cqd_create(int capacity) {
    CQDynamic *q = malloc(sizeof(CQDynamic));
    if (!q) return NULL;
    q->data = malloc(sizeof(CQData) * capacity);
    if (!q->data) { free(q); return NULL; }
    q->head = q->tail = q->count = 0;
    q->capacity = capacity;
    return q;
}

void cqd_destroy(CQDynamic *q) {
    if (q) {
        free(q->data);
        free(q);
    }
}
/* All other operations are identical to static version */
```

---

## 16. Implementation in Rust

### 16.1 — Rust Design Philosophy

Rust's ownership system makes data structures interesting:
- No null pointers → use `Option<T>`
- No runtime errors → use `Result<T, E>`
- Generics → works with any data type
- Zero-cost abstractions → as fast as C

```rust
// circular_queue.rs
//
// A complete, idiomatic Rust circular queue implementation.
//
// Design decisions:
//   - Generic over element type T
//   - Uses Vec<Option<T>> internally (handles uninitialized slots)
//   - Returns Result for fallible operations
//   - Implements standard traits: Debug, Display, Iterator
//   - Thread-unsafe (add Arc<Mutex<>> for concurrent use)

use std::fmt;

// ─────────────────────────────────────────────
//  Error Type
// ─────────────────────────────────────────────

#[derive(Debug, PartialEq, Clone)]
pub enum CQError {
    Overflow,   // enqueue on full queue
    Underflow,  // dequeue/peek on empty queue
}

impl fmt::Display for CQError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CQError::Overflow  => write!(f, "CircularQueue: overflow (queue is full)"),
            CQError::Underflow => write!(f, "CircularQueue: underflow (queue is empty)"),
        }
    }
}

// ─────────────────────────────────────────────
//  CircularQueue<T>
// ─────────────────────────────────────────────

pub struct CircularQueue<T> {
    data:     Vec<Option<T>>,  // internal storage; Option handles empty slots
    head:     usize,           // index of oldest element
    tail:     usize,           // index where next element will be stored
    count:    usize,           // current number of elements
    capacity: usize,           // maximum number of elements
}

impl<T> CircularQueue<T> {
    // ─────────────────────────────────────────
    //  Constructor
    //
    //  Creates a new CircularQueue with the given capacity.
    //  Panics if capacity == 0.
    //
    //  Example:
    //    let mut q: CircularQueue<i32> = CircularQueue::new(8);
    // ─────────────────────────────────────────
    pub fn new(capacity: usize) -> Self {
        assert!(capacity > 0, "CircularQueue capacity must be > 0");

        // Pre-allocate Vec filled with None
        // None = "this slot is empty"
        let data = (0..capacity).map(|_| None).collect();

        CircularQueue {
            data,
            head:     0,
            tail:     0,
            count:    0,
            capacity,
        }
    }

    // ─────────────────────────────────────────
    //  State Queries
    // ─────────────────────────────────────────

    pub fn is_empty(&self) -> bool {
        self.count == 0
    }

    pub fn is_full(&self) -> bool {
        self.count == self.capacity
    }

    pub fn len(&self) -> usize {
        self.count
    }

    pub fn capacity(&self) -> usize {
        self.capacity
    }

    // ─────────────────────────────────────────
    //  Enqueue
    //
    //  Adds an element to the rear.
    //  Returns Err(CQError::Overflow) if full.
    //
    //  Algorithm:
    //    1. Check full
    //    2. Store value at data[tail]
    //    3. tail = (tail + 1) % capacity
    //    4. count += 1
    //
    //  O(1) time, O(1) space.
    // ─────────────────────────────────────────
    pub fn enqueue(&mut self, val: T) -> Result<(), CQError> {
        if self.is_full() {
            return Err(CQError::Overflow);
        }

        self.data[self.tail] = Some(val);
        self.tail = (self.tail + 1) % self.capacity;
        self.count += 1;

        Ok(())
    }

    // ─────────────────────────────────────────
    //  Dequeue
    //
    //  Removes and returns the front element.
    //  Returns Err(CQError::Underflow) if empty.
    //
    //  Algorithm:
    //    1. Check empty
    //    2. Take value from data[head] (replaces with None)
    //    3. head = (head + 1) % capacity
    //    4. count -= 1
    //    5. Return value
    //
    //  O(1) time.
    // ─────────────────────────────────────────
    pub fn dequeue(&mut self) -> Result<T, CQError> {
        if self.is_empty() {
            return Err(CQError::Underflow);
        }

        // .take() replaces data[head] with None and returns the Option<T>
        // .unwrap() is safe here because we checked is_empty above
        let val = self.data[self.head].take().unwrap();
        self.head = (self.head + 1) % self.capacity;
        self.count -= 1;

        Ok(val)
    }

    // ─────────────────────────────────────────
    //  Peek Front
    //
    //  Returns a reference to the front element without removing it.
    //  Returns Err if empty.
    //
    //  Why reference? We don't want to clone or move the value.
    //  Lifetime is tied to the queue's lifetime.
    // ─────────────────────────────────────────
    pub fn peek_front(&self) -> Result<&T, CQError> {
        if self.is_empty() {
            return Err(CQError::Underflow);
        }

        // as_ref() converts &Option<T> to Option<&T>
        // unwrap() is safe (we checked is_empty)
        Ok(self.data[self.head].as_ref().unwrap())
    }

    // ─────────────────────────────────────────
    //  Peek Rear
    //
    //  Returns a reference to the most recently added element.
    //  tail - 1 with wrap-around (add capacity to avoid underflow on usize).
    // ─────────────────────────────────────────
    pub fn peek_rear(&self) -> Result<&T, CQError> {
        if self.is_empty() {
            return Err(CQError::Underflow);
        }

        // tail points to next free slot, so rear = tail - 1
        // Adding capacity before subtracting prevents usize underflow
        let rear_idx = (self.tail + self.capacity - 1) % self.capacity;
        Ok(self.data[rear_idx].as_ref().unwrap())
    }

    // ─────────────────────────────────────────
    //  Clear
    //
    //  Empties the queue. For Copy types this is fast.
    //  For non-Copy types, existing values are dropped.
    // ─────────────────────────────────────────
    pub fn clear(&mut self) {
        // Drop all existing values properly
        for slot in self.data.iter_mut() {
            *slot = None;
        }
        self.head  = 0;
        self.tail  = 0;
        self.count = 0;
    }

    // ─────────────────────────────────────────
    //  Iter
    //
    //  Returns an iterator over references in FIFO order.
    //  Does not consume the queue.
    // ─────────────────────────────────────────
    pub fn iter(&self) -> CQIter<'_, T> {
        CQIter {
            queue:   self,
            current: self.head,
            visited: 0,
        }
    }

    // ─────────────────────────────────────────
    //  Print Debug (internal layout)
    // ─────────────────────────────────────────
    pub fn print_raw(&self) where T: fmt::Debug {
        print!("Raw: [");
        for (i, slot) in self.data.iter().enumerate() {
            match slot {
                Some(v) => {
                    if i == self.head && i == self.tail {
                        print!("H/T:{:?}", v);
                    } else if i == self.head {
                        print!("H:{:?}", v);
                    } else if i == self.tail && self.count < self.capacity {
                        print!("T:_");
                    } else {
                        print!("{:?}", v);
                    }
                },
                None => {
                    if i == self.tail {
                        print!("T:_");
                    } else {
                        print!("_");
                    }
                },
            }
            if i < self.capacity - 1 { print!("|"); }
        }
        println!("] head={}, tail={}, count={}, cap={}",
                 self.head, self.tail, self.count, self.capacity);
    }
}

// ─────────────────────────────────────────────
//  Iterator Implementation
// ─────────────────────────────────────────────

pub struct CQIter<'a, T> {
    queue:   &'a CircularQueue<T>,
    current: usize,
    visited: usize,
}

impl<'a, T> Iterator for CQIter<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        if self.visited >= self.queue.count {
            return None;
        }
        let val = self.queue.data[self.current].as_ref().unwrap();
        self.current = (self.current + 1) % self.queue.capacity;
        self.visited += 1;
        Some(val)
    }
}

// ─────────────────────────────────────────────
//  Display Trait (human-readable output)
// ─────────────────────────────────────────────

impl<T: fmt::Debug> fmt::Display for CircularQueue<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Queue(front→rear): [")?;
        for (i, val) in self.iter().enumerate() {
            if i > 0 { write!(f, ", ")?; }
            write!(f, "{:?}", val)?;
        }
        write!(f, "] | size={}/{}", self.count, self.capacity)
    }
}

// ─────────────────────────────────────────────
//  Debug Trait (structural info)
// ─────────────────────────────────────────────

impl<T: fmt::Debug> fmt::Debug for CircularQueue<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("CircularQueue")
            .field("head", &self.head)
            .field("tail", &self.tail)
            .field("count", &self.count)
            .field("capacity", &self.capacity)
            .field("data", &self.data)
            .finish()
    }
}

// ─────────────────────────────────────────────
//  MAIN — Demonstration
// ─────────────────────────────────────────────

fn main() {
    println!("========================================");
    println!("     CIRCULAR QUEUE DEMO (Rust)");
    println!("========================================\n");

    let mut q: CircularQueue<i32> = CircularQueue::new(5);
    println!("[INIT] Capacity = 5");
    println!("{q}");
    q.print_raw();

    // Enqueue 5 elements
    println!("\n[ENQUEUE] 10, 20, 30, 40, 50");
    for &val in &[10, 20, 30, 40, 50] {
        q.enqueue(val).expect("enqueue failed");
    }
    println!("{q}");
    q.print_raw();

    // Try enqueue on full
    println!("\n[ENQUEUE on FULL] Attempt to add 99");
    match q.enqueue(99) {
        Err(CQError::Overflow) => println!("Got Overflow error ✓"),
        _ => println!("Unexpected result"),
    }

    // Dequeue 3 elements
    println!("\n[DEQUEUE x3]");
    for _ in 0..3 {
        match q.dequeue() {
            Ok(val) => println!("Dequeued: {val}"),
            Err(e)  => println!("Error: {e}"),
        }
    }
    println!("{q}");
    q.print_raw();

    // Enqueue more (wrap-around)
    println!("\n[ENQUEUE with WRAP] 60, 70, 80");
    for &val in &[60, 70, 80] {
        q.enqueue(val).expect("enqueue failed");
    }
    println!("{q}");
    q.print_raw();

    // Peek
    println!("\n[PEEK front] = {:?}", q.peek_front());
    println!("[PEEK rear]  = {:?}", q.peek_rear());

    // Iterate without consuming
    println!("\n[ITERATE without consuming]");
    for val in q.iter() {
        print!("{val} ");
    }
    println!();
    println!("Queue still intact: {q}");

    // Drain
    println!("\n[DRAIN all elements]");
    while !q.is_empty() {
        println!("Dequeued: {}", q.dequeue().unwrap());
    }
    println!("{q}");

    // Try dequeue on empty
    println!("\n[DEQUEUE on EMPTY]");
    match q.dequeue() {
        Err(CQError::Underflow) => println!("Got Underflow error ✓"),
        _ => println!("Unexpected result"),
    }

    // Works with any type — demo with String
    println!("\n[GENERIC — String queue]");
    let mut sq: CircularQueue<String> = CircularQueue::new(3);
    sq.enqueue(String::from("alpha")).unwrap();
    sq.enqueue(String::from("beta")).unwrap();
    sq.enqueue(String::from("gamma")).unwrap();
    println!("{sq}");
}
```

### 16.2 — Rust: Key Design Points

```
Why Vec<Option<T>> instead of Vec<T>?

  Vec<T> requires T to be initialized everywhere.
  Option<T> lets us distinguish "occupied" from "empty" slots.
  Using .take() cleanly moves ownership out of the slot,
  replacing it with None. This properly drops values and
  respects Rust's ownership rules.

Why (self.tail + self.capacity - 1) % self.capacity for rear?

  usize cannot be negative.
  self.tail - 1 would panic if tail == 0 (usize underflow).
  Adding capacity before subtracting keeps the value positive:
    tail=0, capacity=5: (0 + 5 - 1) % 5 = 4 ✓
    tail=3, capacity=5: (3 + 5 - 1) % 5 = 2 ✓

Lifetime 'a in CQIter<'a, T>:
  The iterator borrows from the queue.
  'a ensures the queue outlives the iterator.
  This is zero-cost — no cloning.
```

---

## 17. Implementation in Go

### 17.1 — Go Design Philosophy

Go favors:
- Interfaces over inheritance
- Composition over embedding complexity
- Explicit error handling
- Generics (since Go 1.18)

```go
// circular_queue.go
//
// A complete, idiomatic Go circular queue implementation.
// Uses generics (Go 1.18+) for type safety without interface{}.
//
// Design:
//   - Generic type parameter T (any comparable type)
//   - Returns error for fallible operations
//   - Implements fmt.Stringer for clean output
//   - Thread-unsafe; wrap with sync.Mutex for concurrency

package main

import (
	"errors"
	"fmt"
	"strings"
)

// ─────────────────────────────────────────────
//  Sentinel Errors
// ─────────────────────────────────────────────

var (
	ErrOverflow  = errors.New("circular queue: overflow (queue is full)")
	ErrUnderflow = errors.New("circular queue: underflow (queue is empty)")
)

// ─────────────────────────────────────────────
//  CircularQueue[T any]
//
//  T any: T can be any type (no constraint needed
//         since we don't compare or order elements).
// ─────────────────────────────────────────────

type CircularQueue[T any] struct {
	data     []T   // internal ring array
	occupied []bool // tracks which slots hold valid data
	head     int   // index of oldest element (front)
	tail     int   // index where next element will go
	count    int   // current number of elements
	capacity int   // maximum number of elements
}

// ─────────────────────────────────────────────
//  NewCircularQueue
//
//  Creates a CircularQueue with the given capacity.
//  Panics if capacity <= 0.
//
//  Example:
//    q := NewCircularQueue[int](8)
// ─────────────────────────────────────────────

func NewCircularQueue[T any](capacity int) *CircularQueue[T] {
	if capacity <= 0 {
		panic(fmt.Sprintf("circular queue: capacity must be > 0, got %d", capacity))
	}
	return &CircularQueue[T]{
		data:     make([]T, capacity),
		occupied: make([]bool, capacity),
		head:     0,
		tail:     0,
		count:    0,
		capacity: capacity,
	}
}

// ─────────────────────────────────────────────
//  State Queries
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) IsEmpty() bool {
	return q.count == 0
}

func (q *CircularQueue[T]) IsFull() bool {
	return q.count == q.capacity
}

func (q *CircularQueue[T]) Len() int {
	return q.count
}

func (q *CircularQueue[T]) Capacity() int {
	return q.capacity
}

// ─────────────────────────────────────────────
//  Enqueue
//
//  Adds val to the rear of the queue.
//  Returns ErrOverflow if queue is full.
//
//  Algorithm:
//    1. Check full
//    2. data[tail] = val; occupied[tail] = true
//    3. tail = (tail + 1) % capacity
//    4. count++
//
//  O(1) time.
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) Enqueue(val T) error {
	if q.IsFull() {
		return ErrOverflow
	}

	q.data[q.tail] = val
	q.occupied[q.tail] = true
	q.tail = (q.tail + 1) % q.capacity
	q.count++

	return nil
}

// ─────────────────────────────────────────────
//  Dequeue
//
//  Removes and returns the front element.
//  Returns zero value + ErrUnderflow if empty.
//
//  Algorithm:
//    1. Check empty
//    2. Save data[head]
//    3. occupied[head] = false (mark slot as empty)
//    4. head = (head + 1) % capacity
//    5. count--
//    6. Return saved value
//
//  O(1) time.
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) Dequeue() (T, error) {
	var zero T // zero value for type T

	if q.IsEmpty() {
		return zero, ErrUnderflow
	}

	val := q.data[q.head]
	q.occupied[q.head] = false
	// Reset to zero value to allow GC of pointers/interfaces
	q.data[q.head] = zero
	q.head = (q.head + 1) % q.capacity
	q.count--

	return val, nil
}

// ─────────────────────────────────────────────
//  PeekFront
//
//  Returns the front element without removing it.
//  Returns zero value + ErrUnderflow if empty.
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) PeekFront() (T, error) {
	var zero T
	if q.IsEmpty() {
		return zero, ErrUnderflow
	}
	return q.data[q.head], nil
}

// ─────────────────────────────────────────────
//  PeekRear
//
//  Returns the most recently added element.
//  tail - 1 with wrap-around.
//
//  Note: (tail - 1 + capacity) % capacity avoids negative index.
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) PeekRear() (T, error) {
	var zero T
	if q.IsEmpty() {
		return zero, ErrUnderflow
	}
	rearIdx := (q.tail - 1 + q.capacity) % q.capacity
	return q.data[rearIdx], nil
}

// ─────────────────────────────────────────────
//  ToSlice
//
//  Returns all elements in FIFO order as a slice.
//  Does not modify the queue.
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) ToSlice() []T {
	result := make([]T, q.count)
	for i := 0; i < q.count; i++ {
		result[i] = q.data[(q.head+i)%q.capacity]
	}
	return result
}

// ─────────────────────────────────────────────
//  ForEach
//
//  Applies function fn to each element in FIFO order.
//  Does not modify the queue.
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) ForEach(fn func(index int, val T)) {
	for i := 0; i < q.count; i++ {
		idx := (q.head + i) % q.capacity
		fn(i, q.data[idx])
	}
}

// ─────────────────────────────────────────────
//  Clear
//
//  Empties the queue. Zero values fill old slots
//  to allow garbage collection.
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) Clear() {
	var zero T
	for i := range q.data {
		q.data[i] = zero
		q.occupied[i] = false
	}
	q.head  = 0
	q.tail  = 0
	q.count = 0
}

// ─────────────────────────────────────────────
//  String (fmt.Stringer interface)
//
//  Human-readable output in FIFO order.
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) String() string {
	if q.IsEmpty() {
		return fmt.Sprintf("Queue[] | size=0/%d", q.capacity)
	}

	parts := make([]string, q.count)
	for i := 0; i < q.count; i++ {
		idx := (q.head + i) % q.capacity
		parts[i] = fmt.Sprintf("%v", q.data[idx])
	}

	return fmt.Sprintf("Queue(front→rear): [%s] | size=%d/%d",
		strings.Join(parts, ", "), q.count, q.capacity)
}

// ─────────────────────────────────────────────
//  PrintRaw — Debug internal array layout
// ─────────────────────────────────────────────

func (q *CircularQueue[T]) PrintRaw() {
	parts := make([]string, q.capacity)
	for i := 0; i < q.capacity; i++ {
		marker := ""
		if i == q.head && i == q.tail {
			marker = "H/T"
		} else if i == q.head {
			marker = "H"
		} else if i == q.tail {
			marker = "T"
		}

		if q.occupied[i] {
			if marker != "" {
				parts[i] = fmt.Sprintf("%s:%v", marker, q.data[i])
			} else {
				parts[i] = fmt.Sprintf("%v", q.data[i])
			}
		} else {
			if marker != "" {
				parts[i] = fmt.Sprintf("%s:_", marker)
			} else {
				parts[i] = "_"
			}
		}
	}
	fmt.Printf("Raw: [%s] | head=%d, tail=%d, count=%d, cap=%d\n",
		strings.Join(parts, "|"), q.head, q.tail, q.count, q.capacity)
}

// ─────────────────────────────────────────────
//  MAIN — Demonstration
// ─────────────────────────────────────────────

func main() {
	fmt.Println("========================================")
	fmt.Println("     CIRCULAR QUEUE DEMO (Go)")
	fmt.Println("========================================\n")

	// Create an int queue with capacity 5
	q := NewCircularQueue[int](5)
	fmt.Println("[INIT] Capacity = 5")
	fmt.Println(q)
	q.PrintRaw()

	// Enqueue 5 elements
	fmt.Println("\n[ENQUEUE] 10, 20, 30, 40, 50")
	for _, v := range []int{10, 20, 30, 40, 50} {
		if err := q.Enqueue(v); err != nil {
			fmt.Printf("Error: %v\n", err)
		}
	}
	fmt.Println(q)
	q.PrintRaw()

	// Try enqueue on full
	fmt.Println("\n[ENQUEUE on FULL] Attempt to add 99")
	if err := q.Enqueue(99); err == ErrOverflow {
		fmt.Println("Got ErrOverflow ✓")
	}

	// Dequeue 3 elements
	fmt.Println("\n[DEQUEUE x3]")
	for i := 0; i < 3; i++ {
		val, err := q.Dequeue()
		if err != nil {
			fmt.Printf("Error: %v\n", err)
		} else {
			fmt.Printf("Dequeued: %d\n", val)
		}
	}
	fmt.Println(q)
	q.PrintRaw()

	// Enqueue more (wrap-around)
	fmt.Println("\n[ENQUEUE with WRAP] 60, 70, 80")
	for _, v := range []int{60, 70, 80} {
		q.Enqueue(v)
	}
	fmt.Println(q)
	q.PrintRaw()

	// Peek
	if front, err := q.PeekFront(); err == nil {
		fmt.Printf("\n[PEEK front] = %d\n", front)
	}
	if rear, err := q.PeekRear(); err == nil {
		fmt.Printf("[PEEK rear]  = %d\n", rear)
	}

	// ToSlice
	fmt.Printf("\n[ToSlice] = %v\n", q.ToSlice())

	// ForEach
	fmt.Println("\n[ForEach]")
	q.ForEach(func(i int, val int) {
		fmt.Printf("  [%d] = %d\n", i, val)
	})

	// Drain
	fmt.Println("\n[DRAIN all elements]")
	for !q.IsEmpty() {
		val, _ := q.Dequeue()
		fmt.Printf("Dequeued: %d\n", val)
	}
	fmt.Println(q)

	// Try dequeue on empty
	fmt.Println("\n[DEQUEUE on EMPTY]")
	_, err := q.Dequeue()
	if err == ErrUnderflow {
		fmt.Println("Got ErrUnderflow ✓")
	}

	// Works with any type — demo with string
	fmt.Println("\n[GENERIC — String queue]")
	sq := NewCircularQueue[string](3)
	sq.Enqueue("alpha")
	sq.Enqueue("beta")
	sq.Enqueue("gamma")
	fmt.Println(sq)

	// Demo with struct type
	type Point struct{ X, Y int }
	fmt.Println("\n[GENERIC — Struct queue]")
	pq := NewCircularQueue[Point](3)
	pq.Enqueue(Point{1, 2})
	pq.Enqueue(Point{3, 4})
	fmt.Println(pq)
}
```

### 17.2 — Go: Key Design Points

```
Why q.data[q.head] = zero after dequeue?

  In Go, the garbage collector traces pointers in arrays.
  If T is a pointer, interface, or slice, not zeroing the slot
  means the GC still sees the old reference → memory leak.
  Setting to zero value (nil, 0, "") releases the reference.

Why occupied []bool?

  In Go generics, we can't check if T is "zero" to determine
  if a slot is empty (zero might be a valid value: 0, "", false).
  The occupied array is a clean parallel boolean array.

Why (q.tail - 1 + q.capacity) % q.capacity for rear index?

  In Go, int can be negative, so q.tail - 1 could be -1.
  Adding q.capacity first ensures positive modulo:
  tail=0, cap=5: (0 - 1 + 5) % 5 = 4 ✓
  tail=3, cap=5: (3 - 1 + 5) % 5 = 2 ✓
```

---

## 18. Variants of Circular Queue

### 18.1 — Double-Ended Circular Queue (Deque)

A **Deque** (Double-Ended Queue) supports insert/remove from **both ends**.

```
   ← remove                    remove →
   ← insert   [A | B | C | D]   insert →
              front           rear

Operations:
  push_front(x)  → add to front
  push_rear(x)   → add to rear
  pop_front()    → remove from front
  pop_rear()     → remove from rear
  peek_front()   → view front
  peek_rear()    → view rear
```

**Head movement for push_front**:
```
head = (head - 1 + capacity) % capacity
```
(Move head backwards — i.e., head wraps to end of array.)

```
Before: [..., _, A, B, C, _, ...]
                 ↑
               head=2

push_front(X):
  head = (2 - 1 + cap) % cap = 1
  data[1] = X
  count++

After: [..., X, A, B, C, _, ...]
              ↑
            head=1
```

### 18.2 — Priority Circular Queue

Elements have priorities; higher priority dequeued first.
Implemented as a **min/max heap** — NOT a simple ring buffer.
Still circular in memory layout but uses heap ordering.

### 18.3 — Blocking Circular Queue (Concurrent)

Used in producer-consumer problems:
- **Enqueue blocks** when full (waits for space)
- **Dequeue blocks** when empty (waits for element)

```
Producer Thread        Consumer Thread
     │                       │
     ▼                       ▼
Enqueue(x)             Dequeue()
     │                       │
  Full? ──YES──► WAIT     Empty? ──YES──► WAIT
     │                       │
     NO                      NO
     │                       │
  Store at tail           Take from head
  Signal consumer         Signal producer
```

Implementation uses **mutex + condition variables** (or channels in Go):

```go
// Go: Blocking circular queue using channels
// The channel IS the circular buffer — Go's built-in buffered channel

ch := make(chan int, 5)  // capacity 5

// Enqueue (blocks if full):
ch <- 42

// Dequeue (blocks if empty):
val := <-ch

// Non-blocking:
select {
case ch <- 42:
    // enqueued
default:
    // full
}
```

### 18.4 — Lock-Free Circular Queue (Advanced)

Uses **atomic compare-and-swap (CAS)** operations instead of locks.
Suitable for high-performance concurrent systems.

```
Architecture:
  head: atomic integer
  tail: atomic integer

Enqueue:
  1. Load tail (atomic)
  2. Compute next_tail = (tail + 1) % cap
  3. CAS(tail, tail, next_tail) — if someone else changed tail, retry
  4. Store value

This is the basis of LMAX Disruptor, Kafka internals, etc.
```

---

## 19. Real-World Applications

### 19.1 — CPU Scheduling (Round Robin)

```
CPU Scheduler uses a circular queue of processes:

┌────────────────────────────────────────────┐
│  Process Queue (Circular)                  │
│                                            │
│  [P1] → [P2] → [P3] → [P4] → back to [P1]│
│                                            │
│  Each process gets a TIME QUANTUM (e.g. 10ms)│
│  After quantum: move to end of queue       │
│  CPU picks from front                      │
└────────────────────────────────────────────┘

Algorithm:
  while (processes exist):
    p = dequeue()
    run p for time_quantum
    if p not finished:
      enqueue(p)  ← goes to back
```

### 19.2 — Keyboard Input Buffer

```
Keyboard → generates key events → stored in ring buffer
Application → reads from ring buffer when ready

Ring buffer prevents key loss during burst typing.

[K][E][Y][B][O][A][R][D] ← producer (ISR / interrupt)
 ↑                   ↑
head                tail

Application reads at head (consumer).
ISR writes at tail (producer).
```

### 19.3 — Audio Streaming

```
Audio Card          Ring Buffer           Speaker Output
(Producer)    →    [sample][sample]...  →    (Consumer)
                   [sample][sample]

Buffer prevents audio glitches when producer/consumer
run at slightly different rates.
```

### 19.4 — Network Packet Buffers

```
Network → packets arrive → ring buffer → application reads

If ring buffer fills (burst traffic):
  Old packets may be overwritten (in overwrite mode)
  Or new packets dropped (in strict mode)
```

### 19.5 — Undo/Redo History (Limited)

```
Keep last N actions in a ring buffer:
  [action1][action2][action3]...[actionN]

When buffer is full, oldest action is overwritten.
This gives a fixed-size undo history window.
```

---

## 20. Common Mistakes & How to Avoid Them

### Mistake 1: Integer Overflow / Unsigned Wrap-around

```c
// BUG in C (if head/tail are unsigned int and start decrement):
unsigned int head = 0;
head = head - 1;  // OVERFLOW → becomes 4294967295!

// Fix:
head = (head - 1 + capacity) % capacity;
```

```rust
// BUG in Rust (usize underflow):
let rear = (self.tail - 1) % self.capacity; // PANIC if tail == 0

// Fix:
let rear = (self.tail + self.capacity - 1) % self.capacity;
```

### Mistake 2: Using head == tail for both empty and full

```
WRONG:
  is_empty() { return head == tail; }
  is_full()  { return head == tail; }

Both return same result → WRONG!

CORRECT (Strategy 1):
  is_empty() { return count == 0; }
  is_full()  { return count == capacity; }
```

### Mistake 3: Advancing tail BEFORE storing value

```c
// BUG:
q->tail = (q->tail + 1) % q->capacity;  // advance first
q->data[q->tail] = val;                  // now tail is WRONG index!

// CORRECT:
q->data[q->tail] = val;                  // store first
q->tail = (q->tail + 1) % q->capacity;  // then advance
```

### Mistake 4: Off-by-one in capacity check

```c
// BUG (allows one extra element):
if (q->count < q->capacity + 1) { ... }

// CORRECT:
if (q->count < q->capacity) { ... }
// Or:
if (!cq_is_full(q)) { ... }
```

### Mistake 5: Not handling the returned error

```go
// BAD Go code:
q.Enqueue(val)  // silently ignores error

// CORRECT:
if err := q.Enqueue(val); err != nil {
    log.Printf("enqueue failed: %v", err)
}
```

### Mistake 6: Accessing raw array instead of logical order

```
Queue state: head=3, tail=1, count=4
data = [D, E, _, _, A, B, C]   (capacity=7)
               ↑tail  ↑head

Logical order: A → B → C → D → E

WRONG iteration:
  for i := 0 to count-1: data[i] → gives D, E, _, _ (WRONG!)

CORRECT iteration:
  for i := 0 to count-1: data[(head + i) % capacity]
  → data[3], data[4], data[5], data[6], data[0] → A, B, C, D, E ✓
```

---

## 21. Expert Mental Models & Patterns

### Mental Model 1: The Chase

> "Tail chases Head around the ring. They can never overlap while
> the queue is partially filled. When they meet, the queue is
> either empty or full — and only the count tells you which."

```
EMPTY (head catches tail):
  T
  H ──── they coincide, count=0

FULL (tail catches head from behind):
  H ←──── T approaches H from behind
  They coincide, count=capacity
```

### Mental Model 2: Clock Arithmetic

A circular queue is exactly like a clock:
- 12 positions (capacity)
- Hour hand = head (oldest)
- Minute hand = tail (newest)
- The hands move clockwise, never backward (for basic queue)

```
       12 (0)
    11      1
  10          2
   9    ●    3
  8           4
    7       5
       6

If head = 9 and tail = 3: queue contains positions 9, 10, 11, 0, 1, 2
Size = distance from head to tail (clockwise) = 6
```

### Mental Model 3: The Modulo Is a Lens

Modulo doesn't change the underlying value — it **projects** an infinite
number line onto a finite ring:

```
Number line: 0  1  2  3  4  5  6  7  8  9  10  11  ...
                                                         ↓ % 5
Ring:        0  1  2  3  4  0  1  2  3  4   0    1  ...

The ring repeats. The modulo folds infinity onto a circle.
```

### Mental Model 4: Producer-Consumer Harmony

Think of head and tail as two workers on opposite sides of a conveyor belt:
- **Producer** (tail) loads items
- **Consumer** (head) unloads items
- Belt runs in a circle
- Full = producer must wait; Empty = consumer must wait

### Pattern: Sliding Window via Circular Buffer

```
Problem: Find max in every window of size k in array.
  Window slides forward one step at a time.
  Use a deque (double-ended circular queue) for O(n) solution.

Window [1,3,5,7,9]:
  Insert → [9]
           ↑ max

Window shifts → [3,5,7,9,11]:
  Insert 11 → [11]
              ↑ max

Monotonic deque maintains decreasing order.
Front is always the maximum.
```

### Cognitive Principle: Chunking

When you understand modulo as "wrap-around on a ring", you've **chunked**
a complex behavior into one simple operation. Expert programmers
see `(i + 1) % n` and instantly think "ring step" — not arithmetic.

This is deliberate practice: **compress understanding into fast-activating patterns**.

---

## 22. Comparison Table

```
┌─────────────────────┬──────────────┬──────────────┬──────────────────┐
│ Property            │ Linear Queue │ Circular Q.  │ Linked List Q.   │
├─────────────────────┼──────────────┼──────────────┼──────────────────┤
│ Memory              │ O(N) static  │ O(N) static  │ O(N) dynamic     │
│ Enqueue             │ O(1)*        │ O(1)         │ O(1)             │
│ Dequeue             │ O(1)*        │ O(1)         │ O(1)             │
│ Space waste         │ HIGH         │ NONE         │ pointer overhead │
│ Cache friendliness  │ High         │ High         │ Low (scattered)  │
│ Max size            │ Fixed        │ Fixed        │ Dynamic          │
│ Memory allocation   │ Upfront      │ Upfront      │ Per node         │
│ Wrap-around         │ NO           │ YES          │ N/A              │
│ Use in OS/embedded  │ Rare         │ Very common  │ Less common      │
└─────────────────────┴──────────────┴──────────────┴──────────────────┘

* Linear queue Enqueue is O(1) but Dequeue may need O(N) shifting
  if implemented naively (without separate front pointer).
```

---

## Summary: The Essence of Circular Queue

```
┌─────────────────────────────────────────────────────────────────┐
│                  CIRCULAR QUEUE ESSENCE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. FIXED ARRAY + MODULO ARITHMETIC = LOGICAL RING              │
│                                                                 │
│  2. TWO POINTERS: head (front) and tail (rear)                  │
│     Both advance using: ptr = (ptr + 1) % capacity             │
│                                                                 │
│  3. THREE STATES: empty, partial, full                          │
│     Disambiguated by: count variable (recommended)             │
│                                                                 │
│  4. ALL CORE OPERATIONS ARE O(1):                               │
│     enqueue, dequeue, peek, is_empty, is_full                   │
│                                                                 │
│  5. SPACE EFFICIENT: no wasted slots, no shifting               │
│                                                                 │
│  6. WIDELY USED: OS schedulers, I/O buffers, streaming,         │
│     networking, producer-consumer                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*End of Circular Queue Complete Guide*
*— Study it like a monk, implement it like a craftsman.*

Here's your complete, in-depth Circular Queue guide. Here's what's covered across 22 sections:

**Conceptual Foundation**
- Every prerequisite term defined from scratch (modulo, index, FIFO, head/tail, wrap-around)
- The core problem with linear queues and exactly why circular fixes it
- The ring buffer mental model with sushi restaurant analogy

**Deep Mechanics**
- The internal state machine (Empty → Partial → Full transitions) with decision trees
- Modulo arithmetic explained as "clock math" — the single formula that powers everything
- All three Full-vs-Empty disambiguation strategies with tradeoffs
- 6 detailed ASCII step-by-step state traces showing wrap-around moment precisely

**All Operations with Decision Trees**
- Enqueue, Dequeue, Peek Front/Rear, IsEmpty, IsFull — each with algorithm, trace, and diagram

**Implementations**
- **C** — static + dynamic allocation variants, error codes, raw debug printer
- **Rust** — generic `CircularQueue<T>`, `Vec<Option<T>>`, Iterator trait, Display/Debug traits, ownership-correct `.take()`
- **Go** — generic `CircularQueue[T any]`, sentinel errors, `ForEach`, `ToSlice`, GC-safe zeroing

**Advanced Topics**
- Deque (Double-Ended), Blocking Queue, Lock-Free Queue variants
- Real applications: Round Robin scheduling, keyboard ISR buffer, audio streaming, TCP sliding window
- 6 common implementation mistakes with buggy vs correct code

**Mental Models**
- The Chase, Clock Arithmetic, Modulo as a Lens, Producer-Consumer Harmony
- Pattern: Sliding window via monotonic deque