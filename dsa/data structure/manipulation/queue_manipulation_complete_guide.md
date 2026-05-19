# Queue Manipulation: A Complete In-Depth Guide

> **Goal of this document:** Build a correct, deep mental model of queues — every variant, every operation, every internal layout, every real mistake — with working implementations in C, Go, and Rust.

---

## Table of Contents

1. [What Is a Queue?](#1-what-is-a-queue)
2. [The Abstract Data Type (ADT) Contract](#2-the-abstract-data-type-adt-contract)
3. [Queue Variants and Their Internals](#3-queue-variants-and-their-internals)
   - 3.1 Simple Array Queue (fixed-size)
   - 3.2 Circular Buffer Queue
   - 3.3 Dynamic Array Queue
   - 3.4 Singly Linked-List Queue
   - 3.5 Doubly Linked-List Queue (Deque)
   - 3.6 Priority Queue (Binary Heap)
   - 3.7 Lock-Free / Concurrent Queue
   - 3.8 Monotonic Queue / Deque
4. [Memory Layout and Internal State Diagrams](#4-memory-layout-and-internal-state-diagrams)
5. [Every Operation, Explained Deeply](#5-every-operation-explained-deeply)
6. [Complexity Reference Table](#6-complexity-reference-table)
7. [Queue Manipulation Techniques](#7-queue-manipulation-techniques)
   - 7.1 Enqueue (push_back)
   - 7.2 Dequeue (pop_front)
   - 7.3 Peek / Front / Back
   - 7.4 Reverse a Queue
   - 7.5 Sort a Queue
   - 7.6 Interleave Two Halves
   - 7.7 Generate Binary Numbers
   - 7.8 BFS with a Queue
   - 7.9 Sliding Window Maximum (Monotonic Deque)
   - 7.10 Queue from Two Stacks
   - 7.11 Stack from Two Queues
   - 7.12 Circular Tour Problem
   - 7.13 Serialize and Deserialize Queue State
8. [Common Mistakes (The Real Ones)](#8-common-mistakes-the-real-ones)
9. [C Implementation](#9-c-implementation)
10. [Go Implementation](#10-go-implementation)
11. [Rust Implementation](#11-rust-implementation)
12. [Concurrency Considerations](#12-concurrency-considerations)
13. [Choosing the Right Queue Variant](#13-choosing-the-right-queue-variant)
14. [Mental Models Summary](#14-mental-models-summary)

---

## 1. What Is a Queue?

A queue is a **linear, ordered collection** that enforces a strict access discipline: elements enter at one end and leave from the other. The two ends have canonical names:

- **Back (rear / tail):** where new elements are inserted.
- **Front (head):** where elements are removed.

This discipline is called **FIFO — First In, First Out.** The element that has been waiting the longest is always the next to be served. This is the defining behavioral contract; everything else is implementation detail.

```
Enqueue -->  [ e4 | e3 | e2 | e1 ]  --> Dequeue
              BACK                   FRONT
              (rear/tail)            (head)
```

Queues model real-world waiting lines, CPU scheduling, network packet buffering, message brokers, BFS traversal, event loops — almost any system where order of arrival must be preserved.

---

## 2. The Abstract Data Type (ADT) Contract

Regardless of implementation, a queue must support:

| Operation      | Meaning                                              | Precondition     |
|----------------|------------------------------------------------------|------------------|
| `enqueue(x)`   | Add element `x` to the back                         | (none)           |
| `dequeue()`    | Remove and return element from the front             | Queue non-empty  |
| `peek()`       | Return front element without removing it             | Queue non-empty  |
| `is_empty()`   | Return true if no elements present                   | (none)           |
| `size()`       | Return count of elements                             | (none)           |

Optional but common:

| Operation      | Meaning                                              |
|----------------|------------------------------------------------------|
| `clear()`      | Remove all elements                                  |
| `contains(x)`  | Search for element (O(n), breaks FIFO abstraction)   |
| `to_array()`   | Snapshot of elements front-to-back                   |

The ADT says **nothing** about how memory is managed, how elements are stored, or what happens at capacity. Those are implementation choices.

---

## 3. Queue Variants and Their Internals

### 3.1 Simple Array Queue (fixed-size, naive)

The most intuitive implementation: a fixed array, a `front` index, and a `back` index.

**Concept:**
- `front` starts at 0
- On enqueue: write to `arr[back]`, increment `back`
- On dequeue: read `arr[front]`, increment `front`

**The critical flaw:** elements never physically move. After many enqueue/dequeue cycles, `front` marches rightward and the usable portion of the array shrinks — even if logically the queue is empty. Space is permanently wasted at the left.

```
Initial state:
   idx:  0    1    2    3    4    5    6    7
        [ -- | -- | -- | -- | -- | -- | -- | -- ]
         ^front
         ^back

After enqueue(A), enqueue(B), enqueue(C):
   idx:  0    1    2    3    4    5    6    7
        [ A  | B  | C  | -- | -- | -- | -- | -- ]
         ^front        ^back

After dequeue(), dequeue():
   idx:  0    1    2    3    4    5    6    7
        [ A  | B  | C  | -- | -- | -- | -- | -- ]
                    ^front
                    ^back (still points at 2)

   front=2, back=2
   The A and B slots are DEAD — never reused.
```

This is why a naive array queue runs out of space even when logically empty. It's only suitable if you enqueue once and drain completely.

---

### 3.2 Circular Buffer Queue (Ring Buffer)

**The fix for the wasted-space problem.** Indices wrap around using modular arithmetic.

```
capacity = 8
head = 0, tail = 0, size = 0

After enqueue(A,B,C,D):
   idx:  0    1    2    3    4    5    6    7
        [ A  | B  | C  | D  | -- | -- | -- | -- ]
          ^                   ^
         head                tail   (tail is next-write position)

After dequeue(), dequeue():
   idx:  0    1    2    3    4    5    6    7
        [ -- | -- | C  | D  | -- | -- | -- | -- ]
                    ^         ^
                   head      tail

After enqueue(E,F,G,H,I):
   idx:  0    1    2    3    4    5    6    7
        [ I  | -- | C  | D  | E  | F  | G  | H  ]
              ^    ^
             tail head   <--- wrapped around!

head=2, tail=1, size=7
```

**Key invariants:**
- `head` = index of front element
- `tail` = index of NEXT write slot (not last written)
- `size` = count of live elements
- Enqueue: `arr[tail] = x; tail = (tail + 1) % capacity; size++`
- Dequeue: `x = arr[head]; head = (head + 1) % capacity; size--`
- Full condition: `size == capacity` (NOT `tail == head` alone — that's ambiguous)
- Empty condition: `size == 0`

**Why track `size` separately?** Because when `head == tail`, you cannot tell if the buffer is full or empty without additional state. The `size` field resolves this unambiguously. Alternatively you can leave one slot always empty (capacity - 1 usable slots) to distinguish full from empty by index comparison alone.

---

### 3.3 Dynamic Array Queue

Extends the circular buffer with automatic resize when full.

**Resize procedure:**
1. Allocate new array of size `2 * capacity`
2. Copy elements from `head` to `head + size - 1` (wrapping), laid out linearly starting at index 0
3. Reset `head = 0`, `tail = size`, `capacity = new_capacity`

```
Before resize (capacity=4, size=4, head=2, tail=2):

   idx:  0    1    2    3
        [ C  | D  | A  | B ]
                    ^
                 head/tail (ambiguous without size counter)

Unwrap to new array (capacity=8):
   idx:  0    1    2    3    4    5    6    7
        [ A  | B  | C  | D  | -- | -- | -- | -- ]
          ^              ^
         head           tail
```

The unwrapping step is crucial. Many bugs arise from copying the raw backing array without accounting for the wrap-around, resulting in elements in the wrong order.

---

### 3.4 Singly Linked-List Queue

No capacity limit. Each node carries a value and a pointer to the next node.

```
    HEAD (front)                              TAIL (back)
      |                                         |
      v                                         v
   +------+------+   +------+------+   +------+------+
   |  A   | next-+-->|  B   | next-+-->|  C   | NULL |
   +------+------+   +------+------+   +------+------+

Enqueue(D): allocate new node, tail->next = new_node, tail = new_node

   +------+------+   +------+------+   +------+------+   +------+------+
   |  A   | next-+-->|  B   | next-+-->|  C   | next-+-->|  D   | NULL |
   +------+------+   +------+------+   +------+------+   +------+------+
     ^head                                                  ^tail

Dequeue(): return head->val, advance head = head->next, free old node

   +------+------+   +------+------+   +------+------+
   |  B   | next-+-->|  C   | next-+-->|  D   | NULL |
   +------+------+   +------+------+   +------+------+
     ^head                               ^tail
```

**Two pointers are essential:** `head` for O(1) dequeue, `tail` for O(1) enqueue. With only `head`, enqueue would be O(n) (must traverse to find tail).

**Memory layout note:** Nodes are heap-allocated individually. They are NOT contiguous in memory. This has cache performance implications — traversing a linked list causes frequent cache misses, whereas iterating a contiguous array is cache-friendly.

---

### 3.5 Doubly Linked-List Queue (Deque — Double-Ended Queue)

Allows O(1) insertion and deletion at BOTH ends. Each node has `prev` and `next` pointers.

```
   FRONT                                                   BACK
     |                                                        |
     v                                                        v
  +------+--------+--------+   +------+--------+--------+   +------+--------+--------+
  | NULL |   A    |  next -+-->| prev |   B    |  next -+-->| prev |   C    |  NULL  |
  +------+--------+--------+   +------+--------+--------+   +------+--------+--------+
                  ^prev=NULL                    ^                             ^
                                               (each node links both ways)
```

A deque supports:
- `push_front(x)`, `push_back(x)` — O(1)
- `pop_front()`, `pop_back()` — O(1)
- `peek_front()`, `peek_back()` — O(1)

This makes it the most flexible queue structure — you can use it as a stack (push/pop back) or a queue (push back, pop front) simultaneously.

---

### 3.6 Priority Queue (Binary Max/Min Heap)

**Not FIFO.** Elements leave in order of priority, not insertion order. The underlying data structure is a **binary heap**, stored in a flat array.

**Heap array layout:**
```
Logical tree:         Array representation:
       10             idx: 0   1   2   3   4   5   6
      /  \                [10 | 8 | 6 | 3 | 4 | 5 | 2]
     8    6
    / \  / \
   3   4 5   2

Parent of node i:  (i - 1) / 2
Left child of i:   2*i + 1
Right child of i:  2*i + 2
```

**Heap invariant (max-heap):** Every parent is >= its children. The maximum element is always at index 0.

**Enqueue (heapify-up / sift-up):**
```
Insert 9 at the end:
[10 | 8 | 6 | 3 | 4 | 5 | 2 | 9]
                              idx=7, parent=(7-1)/2=3, arr[3]=3

9 > 3, swap:
[10 | 8 | 6 | 9 | 4 | 5 | 2 | 3]
              idx=3, parent=(3-1)/2=1, arr[1]=8

9 > 8, swap:
[10 | 9 | 6 | 8 | 4 | 5 | 2 | 3]
       idx=1, parent=(1-1)/2=0, arr[0]=10

9 < 10, STOP. Heap restored.
```

**Dequeue (heapify-down / sift-down):**
```
Remove max (10):
1. Swap root with last element:
   [3 | 9 | 6 | 8 | 4 | 5 | 2 | 10]
2. Remove last:
   [3 | 9 | 6 | 8 | 4 | 5 | 2]
3. Sift-down from root:
   idx=0 (val=3), children idx=1(9), idx=2(6), max_child=1(9)
   3 < 9, swap: [9 | 3 | 6 | 8 | 4 | 5 | 2]
   idx=1 (val=3), children idx=3(8), idx=4(4), max_child=3(8)
   3 < 8, swap: [9 | 8 | 6 | 3 | 4 | 5 | 2]
   idx=3 (val=3), children idx=7,8 — out of bounds. STOP.
   Result: [9 | 8 | 6 | 3 | 4 | 5 | 2]
```

**Min-heap:** same structure, parent <= children, minimum at index 0.

---

### 3.7 Lock-Free / Concurrent Queue (Michael-Scott Queue)

For multi-threaded environments, the standard solution is the Michael-Scott queue (1996), a lock-free singly linked list using Compare-And-Swap (CAS) atomic operations.

```
Sentinel (dummy) node pattern:

   head                         tail
     |                            |
     v                            v
  +--------+------+   +--------+------+   +--------+------+
  |sentinel| next-+-->|   A    | next-+-->|   B    | NULL |
  +--------+------+   +--------+------+   +--------+------+

- head always points to the dummy node (one behind the actual front)
- dequeue reads head->next (the real front)
- enqueue CAS's tail->next from NULL to new node
- tail may lag — threads help advance it (helping protocol)
```

The sentinel node is critical: it decouples head and tail updates so that concurrent enqueues and dequeues don't contend on the same node when the queue has one element.

**The ABA problem:** A CAS succeeds because a pointer looks the same as before, but the node was actually removed and a *new* node was allocated at the same address. The solution is tagged pointers (pair the pointer with a version counter) or hazard pointers for memory reclamation.

---

### 3.8 Monotonic Queue / Deque

A specialized deque that maintains elements in monotonically increasing or decreasing order. Used for O(n) sliding window maximum/minimum.

```
Monotonic decreasing deque (keeps potential maximums):

Window: [2, 3, 1, 4, 2], window_size=3

Process 2: deque=[2]
Process 3: 3>2, remove 2 from back. deque=[3]
Process 1: 1<3, just append. deque=[3,1]
   Window [2,3,1]: max = front = 3 ✓

Process 4: 4>1, remove 1. 4>3, remove 3. deque=[4]
   Window [3,1,4]: max = front = 4 ✓

Process 2: 2<4, just append. deque=[4,2]
   Window [1,4,2]: max = front = 4 ✓

Key property: front is ALWAYS the window maximum.
Back holds candidates for future windows.
```

---

## 4. Memory Layout and Internal State Diagrams

### Circular Buffer — Complete State Machine

```
EMPTY STATE:
   capacity=8, head=0, tail=0, size=0
   +----+----+----+----+----+----+----+----+
   | -- | -- | -- | -- | -- | -- | -- | -- |
   +----+----+----+----+----+----+----+----+
     ^h,t

AFTER enqueue(A,B,C,D,E):
   capacity=8, head=0, tail=5, size=5
   +----+----+----+----+----+----+----+----+
   | A  | B  | C  | D  | E  | -- | -- | -- |
   +----+----+----+----+----+----+----+----+
     ^h                  ^t

AFTER dequeue() x3 (removes A,B,C):
   capacity=8, head=3, tail=5, size=2
   +----+----+----+----+----+----+----+----+
   | -- | -- | -- | D  | E  | -- | -- | -- |
   +----+----+----+----+----+----+----+----+
                    ^h        ^t

AFTER enqueue(F,G,H,I,J,K) [wrap around]:
   capacity=8, head=3, tail=3, size=8  <-- FULL
   +----+----+----+----+----+----+----+----+
   | I  | J  | K  | D  | E  | F  | G  | H  |
   +----+----+----+----+----+----+----+----+
                    ^h,t  (head==tail BUT size=8, so FULL not EMPTY)

Logical order (front to back): D E F G H I J K
```

### Linked-List Node Memory (C struct layout)

```
struct Node {         
    int   value;      // 4 bytes
    // [padding]      // 4 bytes (on 64-bit, pointer alignment)
    Node* next;       // 8 bytes
};                    // Total: 16 bytes per node

Memory addresses (hypothetical):
0x1000: [  D  |  pad  | 0x1010 ]  --> head points here
0x1010: [  E  |  pad  | 0x1020 ]
0x1020: [  F  |  pad  | NULL   ]  --> tail points here

Each node is a SEPARATE heap allocation.
They are scattered in memory — NOT contiguous.
```

### Binary Heap — Array vs. Tree Mapping

```
Array: [100 | 90 | 80 | 70 | 60 | 50 | 40 | 30 | 20 | 10]
idx:      0    1    2    3    4    5    6    7    8    9

Tree view:
                      100 [0]
                     /         \
               90 [1]           80 [2]
              /      \         /       \
          70 [3]    60 [4]  50 [5]   40 [6]
          /    \    /
       30[7] 20[8] 10[9]

Navigation (zero-indexed):
  parent(i)       = (i - 1) / 2   (integer division)
  left_child(i)   = 2 * i + 1
  right_child(i)  = 2 * i + 2
  last_parent     = (n / 2) - 1   (first index with at least one child)
```

### Deque (VecDeque in Rust, ring-buffer backed)

```
Internal ring buffer for Deque:
   capacity=8, head=5, len=5

   raw:   [  E  |  -- |  -- |  -- |  -- |  A  |  B  |  C  | D ]
   idx:     0      1     2     3     4     5     6     7    (8=capacity)
                                           ^head

Logical order (front to back): A B C D E
   A is at raw[5], B at raw[6], C at raw[7], D at raw[0], E at raw[1]
   (wraps around)

push_front(Z): head = (head - 1 + capacity) % capacity = 4
   raw:   [  E  |  -- |  -- |  -- |  Z  |  A  |  B  |  C  | D ]
   head now at 4, len=6

push_back(W): tail = (head + len) % capacity = (4+6)%8 = 2
   raw:   [  E  |  -- |  W  |  -- |  Z  |  A  |  B  |  C  | D ]
   len=7
```

---

## 5. Every Operation, Explained Deeply

### Enqueue

**Linked list version:**
1. Allocate new node with `value = x`, `next = NULL`
2. If queue is empty: `head = tail = new_node`
3. Otherwise: `tail->next = new_node; tail = new_node`
4. Increment `size`

The tail pointer is the key. Without it, you'd have to walk from `head` to find the last node — O(n) instead of O(1).

**Circular buffer version:**
1. Check: if `size == capacity`, either error (fixed) or resize (dynamic)
2. `buffer[tail] = x`
3. `tail = (tail + 1) % capacity`
4. `size++`

The modulo operation `% capacity` is the mechanism that makes it circular. When `tail` reaches `capacity`, it wraps back to 0.

**Performance subtlety:** Integer modulo (`%`) involves division, which can be slow on some architectures. If capacity is always a power of two, `% capacity` can be replaced with `& (capacity - 1)` (bitwise AND), which is a single instruction. This is why most production ring buffers keep capacity as a power of two.

### Dequeue

**Linked list version:**
1. If `head == NULL`: error or return sentinel
2. `value = head->value`
3. `old_head = head`
4. `head = head->next`
5. If `head == NULL`: also set `tail = NULL` (queue is now empty)
6. Free `old_head`
7. Decrement `size`, return `value`

Step 5 is a common omission. If you forget to null `tail` when the list becomes empty, `tail` dangles to freed memory. The next enqueue will write `tail->next = new_node` into freed heap — undefined behavior.

**Circular buffer version:**
1. If `size == 0`: error
2. `value = buffer[head]`
3. `head = (head + 1) % capacity`
4. `size--`
5. Return `value`

Optionally zero out `buffer[old_head]` to drop references (important if storing pointers to avoid memory leaks in GC languages).

### Peek (Front)

Return `head->value` (linked list) or `buffer[head]` (ring buffer) **without** modifying any state. Never advance `head`. This is O(1) in all implementations.

### is_empty / size

For linked list: `head == NULL` means empty; maintain an explicit `size` counter (O(1)) vs. counting nodes (O(n)).

For ring buffer: `size == 0` means empty. Do **not** use `head == tail` as the empty check unless you reserve one slot — see Section 8 for why this is a common bug.

### Clear

**Linked list:** Traverse from `head`, freeing each node. O(n). Then set `head = tail = NULL`, `size = 0`. In languages with GC, just set `head = tail = NULL`.

**Ring buffer:** Set `head = tail = size = 0`. O(1) — you don't need to wipe the array (the size counter makes old data unreachable). Exception: if elements are pointers in a GC language, you must null them out to let the GC collect them.

### Resize (Dynamic Ring Buffer)

```
Before resize:
   capacity=4, head=2, tail=2, size=4  [FULL]
   raw: [ C | D | A | B ]
              ^h,t (wrapping state)

Step 1: allocate new_buf of size 8

Step 2: copy in logical order
   for i in 0..size:
       new_buf[i] = old_buf[(head + i) % old_capacity]
   new_buf: [ A | B | C | D | - | - | - | - ]

Step 3: free old_buf
   head=0, tail=4, capacity=8

After resize:
   new_buf: [ A | B | C | D | - | - | - | - ]
              ^h          ^t
```

The copy must iterate logically (from `head`, wrapping), NOT `memcpy` the raw array directly. Raw `memcpy` would copy `[C|D|A|B]` and interpret it as `[C|D|A|B]` with `head=0`, scrambling the order.

---

## 6. Complexity Reference Table

| Operation          | Linked List | Circular Buffer | Priority Queue | Deque (ring) |
|--------------------|-------------|-----------------|----------------|--------------|
| enqueue            | O(1)        | O(1) amortized  | O(log n)       | O(1) amortized|
| dequeue            | O(1)        | O(1)            | O(log n)       | O(1)         |
| peek front         | O(1)        | O(1)            | O(1)           | O(1)         |
| peek back          | O(1)*       | O(1)            | O(n)           | O(1)         |
| search / contains  | O(n)        | O(n)            | O(n)           | O(n)         |
| size               | O(1)**      | O(1)            | O(1)           | O(1)         |
| clear              | O(n)        | O(1)            | O(1)           | O(1)†        |
| merge two queues   | O(1)        | O(n)            | O(n log n)     | O(n)         |

\* Requires tail pointer maintained
\*\* Requires explicit size counter
† O(n) if elements need nulling for GC

**Amortized O(1) for ring buffer enqueue:** Individual enqueues are O(1). Resize is O(n) but happens exponentially less often. Over n operations: total cost = n * O(1) + O(n) for resize = O(n) total → O(1) amortized per operation.

---

## 7. Queue Manipulation Techniques

### 7.1 Enqueue and Dequeue (Fundamentals)

Already covered in Section 5. The key insight for manipulation: **every transformation of a queue must preserve the FIFO property** unless you are explicitly building a different structure (like a priority queue).

### 7.2 Reverse a Queue

You cannot reverse a queue in-place using only queue operations. You need O(n) auxiliary space.

**Using a stack (natural approach):**
```
Original queue: front [A B C D E] back

Step 1 — Dequeue all into a stack:
   stack (top to bottom): E D C B A
   queue: empty

Step 2 — Pop stack back into queue:
   queue: front [E D C B A] back

Algorithm:
   push all elements onto stack while dequeueing
   enqueue all elements from stack back into queue
```

**Using recursion (implicit call stack acts as explicit stack):**
```
reverse(queue):
    if queue.is_empty(): return
    x = queue.dequeue()
    reverse(queue)        // recursive call
    queue.enqueue(x)      // x goes back AFTER the reversed rest
```

The recursion depth equals queue size — O(n) stack space.

**In-place reversal of circular buffer (if you have direct array access):**
Use two pointers at the logical front and back positions, swap elements, move inward. But this is no longer a pure queue operation — it's array manipulation on the backing store.

### 7.3 Sort a Queue

Queues are not sorted structures, but you can sort the contents:

**Method 1: Dequeue all → sort array → enqueue back**
O(n log n) time, O(n) space. Straightforward.

**Method 2: Selection sort using only queue operations**
```
for i in 0..n:
    // Find minimum in remaining queue
    min_val = INFINITY
    temp_queue = empty
    for j in 0..(n-i):
        x = queue.dequeue()
        if x < min_val: min_val = x
        temp_queue.enqueue(x)
    // Put non-minimum elements back, in order
    while not temp_queue.is_empty():
        x = temp_queue.dequeue()
        if x == min_val and not placed:
            // place at back of result section
            placed = true
        else:
            queue.enqueue(x)
    queue.enqueue(min_val)  // place minimum at back

O(n^2) time, O(n) space — but only uses queue operations
```

### 7.4 Interleave Two Halves of a Queue

Given queue `[1 2 3 4 5 6]`, produce `[1 4 2 5 3 6]` — elements from first half and second half interleaved.

```
Original: [1 2 3 4 5 6]  (n=6, half=3)

Step 1: Move first half to auxiliary queue:
   aux: [1 2 3]
   main: [4 5 6]

Step 2: Interleave — alternately dequeue from aux and main, enqueue to main:
   Take 1 from aux, 4 from main, enqueue both: main=[5 6 1 4]
   Take 2 from aux, 5 from main, enqueue both: main=[6 2 5 1 4] ... 

Better approach with a queue of queues or careful indexing.
Simpler: dequeue into array, interleave, re-enqueue.
```

### 7.5 Generate Binary Numbers Using a Queue

Generate binary representations of 1..n using a queue.

```
Queue starts: [1]

Iteration:
   Dequeue "1", print "1"
   Enqueue "10" (1+"0"), enqueue "11" (1+"1")
   Queue: [10, 11]

   Dequeue "10", print "10"
   Enqueue "100", enqueue "101"
   Queue: [11, 100, 101]

   Dequeue "11", print "11"
   Enqueue "110", enqueue "111"
   Queue: [100, 101, 110, 111]

Output: 1, 10, 11, 100, 101, 110, 111 ...
```

This works because BFS on a binary tree where each node `s` has children `s+"0"` and `s+"1"` naturally generates binary numbers in order.

### 7.6 BFS (Breadth-First Search) with a Queue

The canonical use of a queue in algorithms. BFS explores a graph level by level.

```
Graph:
   A --- B --- D
   |         /
   C --------

BFS from A:
   Level 0: queue=[A], visited={A}
   Dequeue A, neighbors=[B,C], enqueue both: queue=[B,C], visited={A,B,C}
   Level 1:
   Dequeue B, neighbors=[A,D], A visited, enqueue D: queue=[C,D], visited={A,B,C,D}
   Dequeue C, neighbors=[A,D], all visited: queue=[D]
   Level 2:
   Dequeue D, no unvisited neighbors: queue=[]

Visit order: A, B, C, D (level order, not depth order)
```

**Why a queue and not a stack?** A stack gives DFS — it explores one branch deep before backtracking. A queue explores all nodes at distance k before any node at distance k+1.

### 7.7 Sliding Window Maximum (Monotonic Deque)

Given array `arr` and window size `k`, find the maximum in each window.

```
arr = [1, 3, -1, -3, 5, 3, 6, 7], k = 3

Use a monotonic decreasing deque of INDICES (not values):

i=0, arr[0]=1:  deque=[] -> push 0.  deque=[0]
i=1, arr[1]=3:  arr[1]>arr[0]=1, pop 0, push 1. deque=[1]
i=2, arr[2]=-1: arr[2]<arr[1]=3, push 2. deque=[1,2]
   window [0,2] complete, max = arr[deque.front()] = arr[1] = 3 ✓

i=3, arr[3]=-3: arr[3]<arr[2]=-1, push 3. deque=[1,2,3]
   front still in window (i-k+1=1, front=1 >= 1 ✓)
   max = arr[1] = 3 ✓

i=4, arr[4]=5:  arr[4]>arr[3]=-3, pop 3. arr[4]>arr[2]=-1, pop 2.
   arr[4]>arr[1]=3, pop 1. push 4. deque=[4]
   front=4 >= i-k+1=2 ✓
   max = arr[4] = 5 ✓

i=5, arr[5]=3:  arr[5]<arr[4]=5, push 5. deque=[4,5]
   front=4 >= 3 ✓, max=arr[4]=5 ✓

i=6, arr[6]=6:  arr[6]>arr[5]=3, pop 5. arr[6]>arr[4]=5, pop 4. push 6. deque=[6]
   max=arr[6]=6 ✓

i=7, arr[7]=7:  arr[7]>arr[6]=6, pop 6. push 7. deque=[7]
   max=arr[7]=7 ✓

Results: [3, 3, 5, 5, 6, 7]
O(n) time — each element enters and leaves deque at most once.
```

### 7.8 Queue from Two Stacks

Implement a queue using two stacks (a classic interview problem, but also used in functional languages where stacks are natural).

```
inbox  (stack) -- where enqueue pushes
outbox (stack) -- where dequeue pops

Enqueue: push to inbox. O(1)
Dequeue:
   if outbox is NOT empty: pop from outbox. O(1)
   else: pop ALL from inbox, push to outbox, then pop. O(n) worst case

Why it works:
   inbox = [A B C] (C is top, last pushed)
   outbox = []

   Dequeue: outbox empty, reverse inbox into outbox:
   outbox = [C B A] (A is now top — the oldest element!)
   Pop A. Correct FIFO.

   Next dequeue: outbox=[C B], pop B. Correct.
   Enqueue D: inbox=[D]
   Next dequeue: outbox=[C], pop C. Correct.
   Next dequeue: outbox empty, reverse inbox:
   outbox=[D], pop D. Correct.

Amortized O(1) per operation — each element moves at most twice (inbox->outbox once).
```

### 7.9 Stack from Two Queues

```
Method 1 (expensive push):
   push(x): enqueue x to q1, then rotate all existing elements through q1
             (dequeue from q1, enqueue back to q1, until x is at front)
   pop(): dequeue from q1

Method 2 (expensive pop):
   push(x): enqueue to q1
   pop(): move all but last element from q1 to q2, remove last from q1
          swap q1 and q2

Both methods have O(n) for either push or pop, O(1) for the other.
```

### 7.10 Circular Tour Problem (Gas Station)

Given `n` petrol pumps in a circle, each with `petrol[i]` available and `dist[i]` needed to reach the next, find a starting pump that completes the circuit.

```
Key insight: If total petrol >= total distance, a solution always exists.
The greedy algorithm finds it in O(n):

start = 0, curr_petrol = 0, total_deficit = 0

for i in 0..n:
    curr_petrol += petrol[i] - dist[i]
    if curr_petrol < 0:
        // Can't start from current 'start', or anywhere up to i
        start = i + 1
        total_deficit += curr_petrol
        curr_petrol = 0

if (curr_petrol + total_deficit) >= 0:
    return start
else:
    return -1  // no solution

Why correct: when curr_petrol < 0 at station i, no station in [start..i]
can be the starting station (they would all run out before reaching i+1).
So we jump start to i+1 and carry the deficit forward for final validation.
```

### 7.11 Serialize and Deserialize Queue State

For persistence or network transfer:

```
Circular buffer serialization:
   1. Write header: [capacity | head | tail | size | element_type]
   2. Write elements in LOGICAL order: for i in 0..size: write buf[(head+i)%cap]
   (NOT the raw array — that would encode the internal layout, not the logical state)

Deserialization:
   1. Read header
   2. Allocate buffer of 'capacity'
   3. Read elements sequentially into buf[0..size-1]
   4. Set head=0, tail=size

This produces an equivalent queue regardless of the original head/tail positions.
```

---

## 8. Common Mistakes (The Real Ones)

### Mistake 1: `head == tail` as the Empty/Full Condition for Ring Buffers

```
// WRONG: Ambiguous!
bool is_empty() { return head == tail; }
bool is_full()  { return head == tail; }  // SAME CONDITION!

// When head==tail, are we empty or full?
// If you only look at indices, you cannot tell.

// CORRECT: Use a size counter
bool is_empty() { return size == 0; }
bool is_full()  { return size == capacity; }

// OR: Reserve one slot — full means (tail+1)%cap == head
// (sacrifices one slot but avoids the size field)
bool is_empty() { return head == tail; }
bool is_full()  { return (tail + 1) % capacity == head; }
```

### Mistake 2: Forgetting to Null the Tail on Last Dequeue

```c
// WRONG:
Node* dequeue(Queue* q) {
    if (!q->head) return NULL;
    Node* old = q->head;
    q->head = q->head->next;
    // BUG: if queue is now empty, q->tail still points to freed node!
    free(old);
    return old; // another bug: returning freed memory
}

// CORRECT:
int dequeue(Queue* q, int* out) {
    if (!q->head) return 0;  // empty
    Node* old = q->head;
    *out = old->value;
    q->head = q->head->next;
    if (!q->head) q->tail = NULL;  // <-- critical
    q->size--;
    free(old);
    return 1;
}
```

### Mistake 3: Off-by-One in Circular Index Calculation

```c
// WRONG — misplaced modulo
tail = tail + 1 % capacity;  // operator precedence: reads as tail = tail + (1 % capacity) = tail + 1 ALWAYS
                              // modulo never actually applies to tail

// CORRECT
tail = (tail + 1) % capacity;
```

### Mistake 4: Wrong Order During Resize Copy

```c
// WRONG: memcpy copies the raw array, not logical order
memcpy(new_buf, old_buf, old_capacity * sizeof(int));
// If head=3, this copies [arr[0]..arr[cap-1]] — garbled logical order.

// CORRECT: copy in logical order
for (int i = 0; i < q->size; i++) {
    new_buf[i] = old_buf[(q->head + i) % q->capacity];
}
q->head = 0;
q->tail = q->size;
```

### Mistake 5: Returning Value After Free (Use-After-Free)

```c
// WRONG:
Node* dequeue() {
    Node* old = head;
    head = head->next;
    free(old);          // freed!
    return old->value;  // reading freed memory — UB
}

// CORRECT: capture value BEFORE freeing
int dequeue() {
    int val = head->value;  // capture first
    Node* old = head;
    head = head->next;
    if (!head) tail = NULL;
    free(old);
    return val;             // return captured value
}
```

### Mistake 6: Not Handling the Empty Queue in Peek

```c
// WRONG: no empty check
int peek(Queue* q) {
    return q->head->value;  // segfault if q->head == NULL
}

// CORRECT:
int peek(Queue* q, int* out) {
    if (!q->head) return 0;  // indicate failure
    *out = q->head->value;
    return 1;
}
// Or use an Option/Result type in Rust, error code in C, panic/error in Go
```

### Mistake 7: Enqueue Into a Full Fixed Buffer Without Checking

```c
// WRONG:
void enqueue(Queue* q, int val) {
    q->buf[q->tail] = val;
    q->tail = (q->tail + 1) % q->capacity;
    // No overflow check! Overwrites oldest element silently.
}

// CORRECT:
int enqueue(Queue* q, int val) {
    if (q->size == q->capacity) return -1;  // or resize
    q->buf[q->tail] = val;
    q->tail = (q->tail + 1) % q->capacity;
    q->size++;
    return 0;
}
```

### Mistake 8: Confusing a Deque with a Queue API

A deque is a superset of a queue, but using `push_back` for enqueue and `pop_back` (instead of `pop_front`) for dequeue gives you stack behavior, not queue behavior. This mistake is common when using `std::deque` in C++ or `VecDeque` in Rust.

```rust
// WRONG (stack behavior, not queue):
deque.push_back(x);
let front = deque.pop_back();  // removes from BACK — LIFO!

// CORRECT (queue behavior):
deque.push_back(x);            // enqueue at back
let front = deque.pop_front(); // dequeue from front — FIFO ✓
```

### Mistake 9: Thread-Unsafe Queue Without Synchronization

```go
// WRONG: concurrent access to a simple queue without locks
go func() { q.Enqueue(1) }()
go func() { q.Enqueue(2) }()
// Data race on head, tail, size fields — undefined behavior

// CORRECT: use a mutex or a lock-free queue
type SafeQueue struct {
    mu    sync.Mutex
    items []int
}
func (q *SafeQueue) Enqueue(v int) {
    q.mu.Lock()
    defer q.mu.Unlock()
    q.items = append(q.items, v)
}
```

### Mistake 10: Modifying a Queue While Iterating

```go
// WRONG: modifying queue during range/iteration
for i := 0; i < q.Size(); i++ {
    v := q.Dequeue()
    if someCondition(v) {
        q.Enqueue(transformedValue)  // size changes mid-loop!
    }
}
// This can cause infinite loops or missed elements.

// CORRECT: collect first, then process
snapshot := q.ToSlice()
for _, v := range snapshot {
    if someCondition(v) {
        q.Enqueue(transformedValue)
    }
}
```

### Mistake 11: Heap Invariant Violation in Priority Queue

```
// WRONG: modify element priority without re-heapifying
pq.items[3].priority = newPriority
// The heap invariant is now broken silently.
// Subsequent dequeues may return wrong elements.

// CORRECT: 
// 1. Remove the element (decrease-key / increase-key)
// 2. Re-heapify (sift up or down depending on new priority)
// OR: Use a lazy deletion pattern with a version tag.
```

### Mistake 12: Integer Overflow in Index Arithmetic

```c
// WRONG on 32-bit systems with large queues:
int tail = 2147483646;  // INT_MAX - 1
tail = (tail + 1) % capacity;  // tail + 1 overflows to INT_MIN — wrong index!

// CORRECT: use unsigned types or check before arithmetic
unsigned int tail = ...;
tail = (tail + 1) % capacity;  // unsigned overflow is well-defined in C, wraps to 0
```

### Mistake 13: Memory Leak — Forgetting to Free Nodes in C

```c
// WRONG:
void clear_queue(Queue* q) {
    q->head = NULL;
    q->tail = NULL;
    q->size = 0;
    // All nodes are leaked! Their memory is never returned to the OS.
}

// CORRECT:
void clear_queue(Queue* q) {
    while (q->head) {
        Node* next = q->head->next;
        free(q->head);
        q->head = next;
    }
    q->tail = NULL;
    q->size = 0;
}
```

### Mistake 14: Shallow Copy of Queue State

```c
// WRONG: copying queue struct copies pointers, not nodes
Queue q2 = q1;  // q2.head == q1.head — both point to same list!
// Modifying q2 modifies q1's data.

// CORRECT: deep copy — duplicate each node
Queue deep_copy(Queue* src) {
    Queue dst = {0};
    Node* curr = src->head;
    while (curr) {
        enqueue(&dst, curr->value);
        curr = curr->next;
    }
    return dst;
}
```

### Mistake 15: Assuming Deque Is Sorted

A deque is a double-ended queue, not a sorted structure. Using `front()` of a deque to get the minimum/maximum only works for a monotonic deque where you explicitly maintain that invariant.

---

## 9. C Implementation

A complete, production-quality implementation of three queue types.

### 9.1 Circular Buffer Queue (Fixed Capacity)

```c
/* circular_queue.h */
#ifndef CIRCULAR_QUEUE_H
#define CIRCULAR_QUEUE_H

#include <stddef.h>
#include <stdbool.h>

typedef struct {
    int*   buf;
    size_t head;
    size_t tail;
    size_t size;
    size_t capacity;
} CircularQueue;

/* Returns 0 on success, -1 on allocation failure */
int  cq_init(CircularQueue* q, size_t capacity);
void cq_destroy(CircularQueue* q);
bool cq_enqueue(CircularQueue* q, int val);
bool cq_dequeue(CircularQueue* q, int* out);
bool cq_peek(const CircularQueue* q, int* out);
bool cq_is_empty(const CircularQueue* q);
bool cq_is_full(const CircularQueue* q);
size_t cq_size(const CircularQueue* q);

#endif

/* circular_queue.c */
#include "circular_queue.h"
#include <stdlib.h>
#include <string.h>

int cq_init(CircularQueue* q, size_t capacity) {
    if (!q || capacity == 0) return -1;
    q->buf = (int*)malloc(capacity * sizeof(int));
    if (!q->buf) return -1;
    q->head     = 0;
    q->tail     = 0;
    q->size     = 0;
    q->capacity = capacity;
    return 0;
}

void cq_destroy(CircularQueue* q) {
    if (!q) return;
    free(q->buf);
    q->buf  = NULL;
    q->size = q->capacity = 0;
}

bool cq_is_empty(const CircularQueue* q) { return q->size == 0; }
bool cq_is_full(const CircularQueue* q)  { return q->size == q->capacity; }
size_t cq_size(const CircularQueue* q)   { return q->size; }

bool cq_enqueue(CircularQueue* q, int val) {
    if (cq_is_full(q)) return false;
    q->buf[q->tail] = val;
    q->tail = (q->tail + 1) % q->capacity;
    q->size++;
    return true;
}

bool cq_dequeue(CircularQueue* q, int* out) {
    if (cq_is_empty(q) || !out) return false;
    *out    = q->buf[q->head];
    q->head = (q->head + 1) % q->capacity;
    q->size--;
    return true;
}

bool cq_peek(const CircularQueue* q, int* out) {
    if (cq_is_empty(q) || !out) return false;
    *out = q->buf[q->head];
    return true;
}
```

### 9.2 Dynamic Linked-List Queue

```c
/* ll_queue.h */
#ifndef LL_QUEUE_H
#define LL_QUEUE_H

#include <stddef.h>
#include <stdbool.h>

typedef struct Node {
    int         value;
    struct Node* next;
} Node;

typedef struct {
    Node*  head;  /* front — dequeue end */
    Node*  tail;  /* back  — enqueue end */
    size_t size;
} LinkedQueue;

void   lq_init(LinkedQueue* q);
void   lq_destroy(LinkedQueue* q);
bool   lq_enqueue(LinkedQueue* q, int val);
bool   lq_dequeue(LinkedQueue* q, int* out);
bool   lq_peek(const LinkedQueue* q, int* out);
bool   lq_is_empty(const LinkedQueue* q);
size_t lq_size(const LinkedQueue* q);

#endif

/* ll_queue.c */
#include "ll_queue.h"
#include <stdlib.h>

void lq_init(LinkedQueue* q) {
    q->head = NULL;
    q->tail = NULL;
    q->size = 0;
}

void lq_destroy(LinkedQueue* q) {
    Node* curr = q->head;
    while (curr) {
        Node* next = curr->next;
        free(curr);
        curr = next;
    }
    q->head = NULL;
    q->tail = NULL;
    q->size = 0;
}

bool lq_is_empty(const LinkedQueue* q) { return q->size == 0; }
size_t lq_size(const LinkedQueue* q)   { return q->size; }

bool lq_enqueue(LinkedQueue* q, int val) {
    Node* node = (Node*)malloc(sizeof(Node));
    if (!node) return false;  /* OOM */
    node->value = val;
    node->next  = NULL;
    if (q->tail) {
        q->tail->next = node;
    } else {
        q->head = node;  /* first element */
    }
    q->tail = node;
    q->size++;
    return true;
}

bool lq_dequeue(LinkedQueue* q, int* out) {
    if (lq_is_empty(q) || !out) return false;
    Node* old  = q->head;
    *out        = old->value;
    q->head     = old->next;
    if (!q->head) q->tail = NULL;  /* queue now empty */
    q->size--;
    free(old);
    return true;
}

bool lq_peek(const LinkedQueue* q, int* out) {
    if (lq_is_empty(q) || !out) return false;
    *out = q->head->value;
    return true;
}
```

### 9.3 Dynamic Circular Buffer (Auto-Resize)

```c
/* dynamic_queue.h */
#ifndef DYNAMIC_QUEUE_H
#define DYNAMIC_QUEUE_H

#include <stddef.h>
#include <stdbool.h>

#define DQ_INITIAL_CAPACITY 8

typedef struct {
    int*   buf;
    size_t head;
    size_t size;
    size_t capacity;
} DynamicQueue;

int    dq_init(DynamicQueue* q);
void   dq_destroy(DynamicQueue* q);
bool   dq_enqueue(DynamicQueue* q, int val);
bool   dq_dequeue(DynamicQueue* q, int* out);
bool   dq_peek(const DynamicQueue* q, int* out);
bool   dq_is_empty(const DynamicQueue* q);
size_t dq_size(const DynamicQueue* q);

#endif

/* dynamic_queue.c */
#include "dynamic_queue.h"
#include <stdlib.h>
#include <string.h>

int dq_init(DynamicQueue* q) {
    q->buf = (int*)malloc(DQ_INITIAL_CAPACITY * sizeof(int));
    if (!q->buf) return -1;
    q->head     = 0;
    q->size     = 0;
    q->capacity = DQ_INITIAL_CAPACITY;
    return 0;
}

void dq_destroy(DynamicQueue* q) {
    free(q->buf);
    q->buf = NULL;
    q->size = q->capacity = 0;
}

bool dq_is_empty(const DynamicQueue* q) { return q->size == 0; }
size_t dq_size(const DynamicQueue* q)   { return q->size; }

/* Internal: grow to double capacity, preserving logical order */
static bool dq_grow(DynamicQueue* q) {
    size_t new_cap = q->capacity * 2;
    int*   new_buf = (int*)malloc(new_cap * sizeof(int));
    if (!new_buf) return false;
    /* Copy in logical order — MUST NOT use raw memcpy */
    for (size_t i = 0; i < q->size; i++) {
        new_buf[i] = q->buf[(q->head + i) % q->capacity];
    }
    free(q->buf);
    q->buf      = new_buf;
    q->head     = 0;
    q->capacity = new_cap;
    /* tail is implicitly q->head + q->size = q->size (since head=0) */
    return true;
}

bool dq_enqueue(DynamicQueue* q, int val) {
    if (q->size == q->capacity) {
        if (!dq_grow(q)) return false;
    }
    size_t tail    = (q->head + q->size) % q->capacity;
    q->buf[tail]   = val;
    q->size++;
    return true;
}

bool dq_dequeue(DynamicQueue* q, int* out) {
    if (dq_is_empty(q) || !out) return false;
    *out    = q->buf[q->head];
    q->head = (q->head + 1) % q->capacity;
    q->size--;
    return true;
}

bool dq_peek(const DynamicQueue* q, int* out) {
    if (dq_is_empty(q) || !out) return false;
    *out = q->buf[q->head];
    return true;
}
```

### 9.4 Min Priority Queue (Binary Heap)

```c
/* min_heap_queue.h */
#ifndef MIN_HEAP_QUEUE_H
#define MIN_HEAP_QUEUE_H

#include <stddef.h>
#include <stdbool.h>

typedef struct {
    int*   data;
    size_t size;
    size_t capacity;
} MinHeap;

int    mh_init(MinHeap* h, size_t capacity);
void   mh_destroy(MinHeap* h);
bool   mh_push(MinHeap* h, int val);
bool   mh_pop(MinHeap* h, int* out);
bool   mh_peek(const MinHeap* h, int* out);
bool   mh_is_empty(const MinHeap* h);
size_t mh_size(const MinHeap* h);

#endif

/* min_heap_queue.c */
#include "min_heap_queue.h"
#include <stdlib.h>

int mh_init(MinHeap* h, size_t cap) {
    h->data = (int*)malloc(cap * sizeof(int));
    if (!h->data) return -1;
    h->size = 0;
    h->capacity = cap;
    return 0;
}

void mh_destroy(MinHeap* h) { free(h->data); h->data = NULL; }
bool mh_is_empty(const MinHeap* h) { return h->size == 0; }
size_t mh_size(const MinHeap* h)   { return h->size; }

static void swap(int* a, int* b) { int t = *a; *a = *b; *b = t; }

/* Sift element at idx UP toward the root to restore heap invariant */
static void sift_up(MinHeap* h, size_t idx) {
    while (idx > 0) {
        size_t parent = (idx - 1) / 2;
        if (h->data[parent] <= h->data[idx]) break;
        swap(&h->data[parent], &h->data[idx]);
        idx = parent;
    }
}

/* Sift element at idx DOWN away from root to restore heap invariant */
static void sift_down(MinHeap* h, size_t idx) {
    for (;;) {
        size_t smallest = idx;
        size_t left     = 2 * idx + 1;
        size_t right    = 2 * idx + 2;
        if (left  < h->size && h->data[left]  < h->data[smallest]) smallest = left;
        if (right < h->size && h->data[right] < h->data[smallest]) smallest = right;
        if (smallest == idx) break;
        swap(&h->data[idx], &h->data[smallest]);
        idx = smallest;
    }
}

bool mh_push(MinHeap* h, int val) {
    if (h->size == h->capacity) return false;  /* or grow */
    h->data[h->size++] = val;
    sift_up(h, h->size - 1);
    return true;
}

bool mh_pop(MinHeap* h, int* out) {
    if (mh_is_empty(h) || !out) return false;
    *out = h->data[0];
    h->data[0] = h->data[--h->size];
    if (h->size > 0) sift_down(h, 0);
    return true;
}

bool mh_peek(const MinHeap* h, int* out) {
    if (mh_is_empty(h) || !out) return false;
    *out = h->data[0];
    return true;
}
```

---

## 10. Go Implementation

### 10.1 Generic Queue with Circular Buffer (Go 1.18+ generics)

```go
package queue

import "fmt"

// CircularQueue is a generic FIFO queue backed by a circular buffer.
// It grows automatically when full (amortized O(1) enqueue).
type CircularQueue[T any] struct {
    buf  []T
    head int
    size int
}

const initialCapacity = 8

// New creates an empty CircularQueue.
func New[T any]() *CircularQueue[T] {
    return &CircularQueue[T]{buf: make([]T, initialCapacity)}
}

// NewWithCapacity pre-allocates space for at least n elements.
func NewWithCapacity[T any](n int) *CircularQueue[T] {
    if n < 1 {
        n = 1
    }
    return &CircularQueue[T]{buf: make([]T, n)}
}

// Len returns the number of elements currently in the queue.
func (q *CircularQueue[T]) Len() int { return q.size }

// IsEmpty returns true if the queue has no elements.
func (q *CircularQueue[T]) IsEmpty() bool { return q.size == 0 }

// cap returns the current backing array capacity.
func (q *CircularQueue[T]) cap() int { return len(q.buf) }

// tail returns the index where the next element will be written.
func (q *CircularQueue[T]) tail() int {
    return (q.head + q.size) % q.cap()
}

// grow doubles the capacity, rewriting elements in logical order.
func (q *CircularQueue[T]) grow() {
    newCap := q.cap() * 2
    newBuf := make([]T, newCap)
    // Copy in logical order — handles wrap-around correctly
    for i := 0; i < q.size; i++ {
        newBuf[i] = q.buf[(q.head+i)%q.cap()]
    }
    q.buf  = newBuf
    q.head = 0
    // q.size unchanged; tail is now at q.size
}

// Enqueue adds val to the back of the queue. O(1) amortized.
func (q *CircularQueue[T]) Enqueue(val T) {
    if q.size == q.cap() {
        q.grow()
    }
    q.buf[q.tail()] = val
    q.size++
}

// Dequeue removes and returns the front element.
// Returns (zero, false) if the queue is empty.
func (q *CircularQueue[T]) Dequeue() (T, bool) {
    var zero T
    if q.IsEmpty() {
        return zero, false
    }
    val    := q.buf[q.head]
    q.buf[q.head] = zero // clear reference (important for GC with pointer types)
    q.head  = (q.head + 1) % q.cap()
    q.size--
    return val, true
}

// Peek returns the front element without removing it.
// Returns (zero, false) if the queue is empty.
func (q *CircularQueue[T]) Peek() (T, bool) {
    var zero T
    if q.IsEmpty() {
        return zero, false
    }
    return q.buf[q.head], true
}

// PeekBack returns the rear element without removing it.
func (q *CircularQueue[T]) PeekBack() (T, bool) {
    var zero T
    if q.IsEmpty() {
        return zero, false
    }
    backIdx := (q.head + q.size - 1) % q.cap()
    return q.buf[backIdx], true
}

// ToSlice returns all elements in front-to-back order.
func (q *CircularQueue[T]) ToSlice() []T {
    s := make([]T, q.size)
    for i := 0; i < q.size; i++ {
        s[i] = q.buf[(q.head+i)%q.cap()]
    }
    return s
}

// String returns a human-readable representation.
func (q *CircularQueue[T]) String() string {
    return fmt.Sprintf("Queue%v", q.ToSlice())
}
```

### 10.2 Linked-List Queue

```go
package queue

// node is an internal singly-linked list node.
type node[T any] struct {
    val  T
    next *node[T]
}

// LinkedQueue is a FIFO queue backed by a singly linked list.
// No capacity limit. O(1) enqueue and dequeue.
type LinkedQueue[T any] struct {
    head *node[T]
    tail *node[T]
    size int
}

func NewLinked[T any]() *LinkedQueue[T] {
    return &LinkedQueue[T]{}
}

func (q *LinkedQueue[T]) Len() int     { return q.size }
func (q *LinkedQueue[T]) IsEmpty() bool { return q.size == 0 }

// Enqueue adds val to the back. O(1).
func (q *LinkedQueue[T]) Enqueue(val T) {
    n := &node[T]{val: val}
    if q.tail != nil {
        q.tail.next = n
    } else {
        q.head = n // first element: head and tail both point to it
    }
    q.tail = n
    q.size++
}

// Dequeue removes and returns the front element. O(1).
func (q *LinkedQueue[T]) Dequeue() (T, bool) {
    var zero T
    if q.IsEmpty() {
        return zero, false
    }
    val    := q.head.val
    q.head  = q.head.next
    if q.head == nil {
        q.tail = nil // queue is now empty — must nil the tail pointer
    }
    q.size--
    return val, true
}

// Peek returns front element without removing it. O(1).
func (q *LinkedQueue[T]) Peek() (T, bool) {
    var zero T
    if q.IsEmpty() {
        return zero, false
    }
    return q.head.val, true
}
```

### 10.3 Priority Queue (Min-Heap, container/heap interface)

```go
package queue

import "container/heap"

// intHeap implements heap.Interface for a min-heap of ints.
type intHeap []int

func (h intHeap) Len() int           { return len(h) }
func (h intHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h intHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *intHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *intHeap) Pop() any {
    old := *h
    n   := len(old)
    x   := old[n-1]
    *h   = old[:n-1]
    return x
}

// MinPQ is a min-priority queue for ints.
type MinPQ struct{ h *intHeap }

func NewMinPQ() *MinPQ {
    h := &intHeap{}
    heap.Init(h)
    return &MinPQ{h: h}
}

func (pq *MinPQ) Push(val int) { heap.Push(pq.h, val) }

func (pq *MinPQ) Pop() (int, bool) {
    if pq.h.Len() == 0 {
        return 0, false
    }
    return heap.Pop(pq.h).(int), true
}

func (pq *MinPQ) Peek() (int, bool) {
    if pq.h.Len() == 0 {
        return 0, false
    }
    return (*pq.h)[0], true
}

func (pq *MinPQ) Len() int { return pq.h.Len() }
```

### 10.4 Thread-Safe Queue

```go
package queue

import "sync"

// SafeQueue is a concurrency-safe FIFO queue.
// Uses a mutex + condition variable for blocking dequeue.
type SafeQueue[T any] struct {
    mu    sync.Mutex
    cond  *sync.Cond
    items []T
}

func NewSafe[T any]() *SafeQueue[T] {
    q := &SafeQueue[T]{}
    q.cond = sync.NewCond(&q.mu)
    return q
}

// Enqueue adds val to the back and wakes one blocked Dequeue. O(1) amortized.
func (q *SafeQueue[T]) Enqueue(val T) {
    q.mu.Lock()
    q.items = append(q.items, val)
    q.cond.Signal() // wake one waiter
    q.mu.Unlock()
}

// Dequeue blocks until an element is available, then removes and returns it.
func (q *SafeQueue[T]) Dequeue() T {
    q.mu.Lock()
    defer q.mu.Unlock()
    for len(q.items) == 0 {
        q.cond.Wait() // atomically unlocks mu and suspends goroutine
    }
    val    := q.items[0]
    var zero T
    q.items[0] = zero  // clear GC reference
    q.items     = q.items[1:]
    return val
}

// TryDequeue returns immediately — (val, true) if available, (zero, false) if empty.
func (q *SafeQueue[T]) TryDequeue() (T, bool) {
    q.mu.Lock()
    defer q.mu.Unlock()
    var zero T
    if len(q.items) == 0 {
        return zero, false
    }
    val    := q.items[0]
    q.items[0] = zero
    q.items     = q.items[1:]
    return val, true
}

// Len returns the current number of elements.
func (q *SafeQueue[T]) Len() int {
    q.mu.Lock()
    defer q.mu.Unlock()
    return len(q.items)
}
```

### 10.5 Monotonic Deque (Sliding Window Maximum)

```go
package queue

// MonotonicDeque maintains indices into a slice for an O(n) sliding window max.
type MonotonicDeque struct {
    indices []int // stores indices into the source array, front is max
}

func NewMonotonicDeque() *MonotonicDeque {
    return &MonotonicDeque{}
}

// PushBack adds index i to the deque for a decreasing deque.
// All indices with smaller values are removed from the back.
func (d *MonotonicDeque) PushBack(i int, arr []int) {
    for len(d.indices) > 0 && arr[d.indices[len(d.indices)-1]] <= arr[i] {
        d.indices = d.indices[:len(d.indices)-1]
    }
    d.indices = append(d.indices, i)
}

// PopFrontIfOutOfWindow removes the front index if it is before 'limit'.
func (d *MonotonicDeque) PopFrontIfOutOfWindow(limit int) {
    if len(d.indices) > 0 && d.indices[0] < limit {
        d.indices = d.indices[1:]
    }
}

// Front returns the index of the maximum element in the current window.
func (d *MonotonicDeque) Front() (int, bool) {
    if len(d.indices) == 0 {
        return 0, false
    }
    return d.indices[0], true
}

// SlidingWindowMax returns the maximum in each window of size k.
// O(n) time, O(k) space.
func SlidingWindowMax(arr []int, k int) []int {
    n := len(arr)
    if n == 0 || k <= 0 {
        return nil
    }
    d      := NewMonotonicDeque()
    result := make([]int, 0, n-k+1)
    for i := 0; i < n; i++ {
        d.PushBack(i, arr)                  // maintain decreasing invariant
        d.PopFrontIfOutOfWindow(i - k + 1)  // evict out-of-window indices
        if i >= k-1 {
            front, _ := d.Front()
            result = append(result, arr[front])
        }
    }
    return result
}
```

---

## 11. Rust Implementation

### 11.1 Ring Buffer Queue (Safe, no unsafe)

```rust
/// A FIFO queue backed by a circular buffer.
/// Grows automatically (amortized O(1) enqueue).
pub struct CircularQueue<T> {
    buf:  Vec<Option<T>>,
    head: usize,
    size: usize,
}

impl<T> CircularQueue<T> {
    const INITIAL_CAPACITY: usize = 8;

    /// Creates a new empty queue.
    pub fn new() -> Self {
        Self {
            buf:  (0..Self::INITIAL_CAPACITY).map(|_| None).collect(),
            head: 0,
            size: 0,
        }
    }

    /// Creates a queue with pre-allocated capacity.
    pub fn with_capacity(cap: usize) -> Self {
        let cap = cap.max(1);
        Self {
            buf:  (0..cap).map(|_| None).collect(),
            head: 0,
            size: 0,
        }
    }

    /// Returns the number of elements.
    pub fn len(&self) -> usize { self.size }

    /// Returns true if the queue has no elements.
    pub fn is_empty(&self) -> bool { self.size == 0 }

    /// Returns current backing capacity.
    fn capacity(&self) -> usize { self.buf.len() }

    /// Returns the index of the next write slot.
    fn tail(&self) -> usize {
        (self.head + self.size) % self.capacity()
    }

    /// Grows the buffer to double capacity, linearizing logical order.
    fn grow(&mut self) {
        let old_cap = self.capacity();
        let new_cap = old_cap * 2;
        let mut new_buf: Vec<Option<T>> = (0..new_cap).map(|_| None).collect();
        // Move elements in logical order
        for i in 0..self.size {
            let src = (self.head + i) % old_cap;
            new_buf[i] = self.buf[src].take();
        }
        self.buf  = new_buf;
        self.head = 0;
        // self.size unchanged
    }

    /// Adds an element to the back. O(1) amortized.
    pub fn enqueue(&mut self, val: T) {
        if self.size == self.capacity() {
            self.grow();
        }
        let tail = self.tail();
        self.buf[tail] = Some(val);
        self.size += 1;
    }

    /// Removes and returns the front element. O(1).
    pub fn dequeue(&mut self) -> Option<T> {
        if self.is_empty() { return None; }
        let val  = self.buf[self.head].take();
        self.head = (self.head + 1) % self.capacity();
        self.size -= 1;
        val
    }

    /// Returns a reference to the front element without removing it. O(1).
    pub fn peek(&self) -> Option<&T> {
        self.buf[self.head].as_ref()
    }

    /// Returns a reference to the back element without removing it. O(1).
    pub fn peek_back(&self) -> Option<&T> {
        if self.is_empty() { return None; }
        let back = (self.head + self.size - 1) % self.capacity();
        self.buf[back].as_ref()
    }

    /// Returns an iterator over elements from front to back.
    pub fn iter(&self) -> impl Iterator<Item = &T> {
        (0..self.size).filter_map(move |i| {
            self.buf[(self.head + i) % self.capacity()].as_ref()
        })
    }
}

impl<T> Default for CircularQueue<T> {
    fn default() -> Self { Self::new() }
}

impl<T: std::fmt::Debug> std::fmt::Debug for CircularQueue<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let v: Vec<&T> = self.iter().collect();
        write!(f, "CircularQueue({:?})", v)
    }
}
```

### 11.2 Linked-List Queue (Using Box)

```rust
type Link<T> = Option<Box<Node<T>>>;

struct Node<T> {
    val:  T,
    next: Link<T>,
}

/// A FIFO queue backed by a singly linked list.
/// head is the front (dequeue end); tail is a raw pointer to the last node.
pub struct LinkedQueue<T> {
    head: Link<T>,
    tail: *mut Node<T>,   // raw pointer to avoid lifetime issues
    size: usize,
}

// SAFETY: LinkedQueue owns all nodes exclusively. No shared access.
unsafe impl<T: Send> Send for LinkedQueue<T> {}

impl<T> LinkedQueue<T> {
    /// Creates a new empty linked queue.
    pub fn new() -> Self {
        Self { head: None, tail: std::ptr::null_mut(), size: 0 }
    }

    pub fn len(&self) -> usize     { self.size }
    pub fn is_empty(&self) -> bool { self.size == 0 }

    /// Adds val to the back. O(1).
    pub fn enqueue(&mut self, val: T) {
        let mut node = Box::new(Node { val, next: None });
        let raw: *mut Node<T> = &mut *node;
        if self.tail.is_null() {
            // Queue was empty: head and tail both point to new node
            self.head = Some(node);
        } else {
            // SAFETY: tail is valid and owned by head's chain
            unsafe { (*self.tail).next = Some(node); }
        }
        self.tail = raw;
        self.size += 1;
    }

    /// Removes and returns the front element. O(1).
    pub fn dequeue(&mut self) -> Option<T> {
        self.head.take().map(|mut node| {
            self.head = node.next.take();
            if self.head.is_none() {
                self.tail = std::ptr::null_mut(); // queue now empty
            }
            self.size -= 1;
            node.val
        })
    }

    /// Returns a reference to the front element. O(1).
    pub fn peek(&self) -> Option<&T> {
        self.head.as_ref().map(|n| &n.val)
    }
}

impl<T> Drop for LinkedQueue<T> {
    fn drop(&mut self) {
        // Iteratively drop all nodes to avoid stack overflow for large queues
        while self.dequeue().is_some() {}
    }
}

impl<T> Default for LinkedQueue<T> {
    fn default() -> Self { Self::new() }
}
```

### 11.3 Priority Queue (Min-Heap)

```rust
use std::cmp::Reverse;
use std::collections::BinaryHeap;

/// A min-priority queue wrapping std::collections::BinaryHeap.
/// Rust's BinaryHeap is a MAX-heap, so we wrap values in Reverse<T>.
pub struct MinPriorityQueue<T: Ord> {
    heap: BinaryHeap<Reverse<T>>,
}

impl<T: Ord> MinPriorityQueue<T> {
    pub fn new() -> Self {
        Self { heap: BinaryHeap::new() }
    }

    pub fn with_capacity(cap: usize) -> Self {
        Self { heap: BinaryHeap::with_capacity(cap) }
    }

    /// Inserts a value. O(log n).
    pub fn push(&mut self, val: T) {
        self.heap.push(Reverse(val));
    }

    /// Removes and returns the minimum value. O(log n).
    pub fn pop(&mut self) -> Option<T> {
        self.heap.pop().map(|Reverse(v)| v)
    }

    /// Returns a reference to the minimum value without removing it. O(1).
    pub fn peek(&self) -> Option<&T> {
        self.heap.peek().map(|Reverse(v)| v)
    }

    pub fn len(&self) -> usize     { self.heap.len() }
    pub fn is_empty(&self) -> bool { self.heap.is_empty() }
}

impl<T: Ord> Default for MinPriorityQueue<T> {
    fn default() -> Self { Self::new() }
}
```

### 11.4 VecDeque Usage (Rust Standard Library)

```rust
use std::collections::VecDeque;

/// Demonstrates VecDeque as a double-ended queue.
/// VecDeque is a ring-buffer-backed deque in Rust's standard library.
pub fn vecdeque_demo() {
    let mut deque: VecDeque<i32> = VecDeque::new();

    // Use as a standard queue (FIFO)
    deque.push_back(1);    // enqueue
    deque.push_back(2);
    deque.push_back(3);
    let front = deque.pop_front(); // dequeue -> Some(1)
    assert_eq!(front, Some(1));

    // Use as a stack (LIFO) from the back
    deque.push_back(4);
    let back = deque.pop_back();   // -> Some(4)
    assert_eq!(back, Some(4));

    // Add to the front (O(1) amortized)
    deque.push_front(0);
    // deque is now: [0, 2, 3]

    // Index access (O(1))
    let mid = deque[1]; // -> 2

    // Convert to vec in logical order
    let v: Vec<i32> = deque.into_iter().collect();
    // v = [0, 2, 3]
    
    println!("mid={}, v={:?}", mid, v);
}

/// Sliding window maximum using VecDeque as a monotonic deque.
/// O(n) time. Each element is pushed and popped at most once.
pub fn sliding_window_max(arr: &[i32], k: usize) -> Vec<i32> {
    let n = arr.len();
    if n == 0 || k == 0 { return vec![]; }

    let mut deque: VecDeque<usize> = VecDeque::new(); // stores indices
    let mut result = Vec::with_capacity(n - k + 1);

    for i in 0..n {
        // Remove indices that are out of the current window
        while deque.front().map_or(false, |&j| j + k <= i) {
            deque.pop_front();
        }
        // Maintain decreasing order: remove smaller values from back
        while deque.back().map_or(false, |&j| arr[j] <= arr[i]) {
            deque.pop_back();
        }
        deque.push_back(i);

        // Window is complete
        if i + 1 >= k {
            result.push(arr[*deque.front().unwrap()]);
        }
    }
    result
}
```

### 11.5 Queue Reversal in Rust

```rust
use std::collections::VecDeque;

/// Reverses a VecDeque in-place.
/// Uses an auxiliary stack (Vec) — O(n) time and space.
pub fn reverse_queue<T>(q: &mut VecDeque<T>) {
    let mut stack: Vec<T> = Vec::with_capacity(q.len());
    // Drain queue into stack
    while let Some(val) = q.pop_front() {
        stack.push(val);
    }
    // Drain stack back into queue — reversal happens here
    while let Some(val) = stack.pop() {
        q.push_back(val);
    }
}

/// Reversal using recursion (uses call stack as implicit stack).
/// O(n) space on the call stack — avoid for large queues.
pub fn reverse_queue_recursive<T>(q: &mut VecDeque<T>) {
    if q.is_empty() { return; }
    let front = q.pop_front().unwrap();
    reverse_queue_recursive(q);
    q.push_back(front);
}
```

### 11.6 Queue from Two Stacks

```rust
/// Implements a FIFO queue using two stacks (Vecs).
/// Amortized O(1) per operation — each element moves at most twice.
pub struct TwoStackQueue<T> {
    inbox:  Vec<T>, // push end
    outbox: Vec<T>, // pop end
}

impl<T> TwoStackQueue<T> {
    pub fn new() -> Self {
        Self { inbox: Vec::new(), outbox: Vec::new() }
    }

    /// Enqueues a value. O(1).
    pub fn enqueue(&mut self, val: T) {
        self.inbox.push(val);
    }

    /// Dequeues the front value. Amortized O(1).
    pub fn dequeue(&mut self) -> Option<T> {
        if self.outbox.is_empty() {
            // Transfer all from inbox to outbox (reverses order)
            while let Some(v) = self.inbox.pop() {
                self.outbox.push(v);
            }
        }
        self.outbox.pop()
    }

    /// Peeks at the front value without removing it.
    pub fn peek(&mut self) -> Option<&T> {
        if self.outbox.is_empty() {
            while let Some(v) = self.inbox.pop() {
                self.outbox.push(v);
            }
        }
        self.outbox.last()
    }

    pub fn is_empty(&self) -> bool {
        self.inbox.is_empty() && self.outbox.is_empty()
    }

    pub fn len(&self) -> usize {
        self.inbox.len() + self.outbox.len()
    }
}

impl<T> Default for TwoStackQueue<T> {
    fn default() -> Self { Self::new() }
}
```

---

## 12. Concurrency Considerations

### The Fundamental Problem

A queue accessed by multiple goroutines/threads concurrently without synchronization is a data race. Even a simple `size++` is not atomic — it compiles to a read, add, and write, any of which can be interleaved.

### Mutex-Protected Queue

The simplest correct solution. A single mutex guards all operations. Works well when contention is low (few threads, infrequent access).

```
Thread A: enqueue(1)     Thread B: dequeue()
         lock mutex               wait for mutex
         write buf[tail]          (blocked)
         tail++                   (blocked)
         size++
         unlock mutex
                                  acquire mutex
                                  read buf[head]
                                  head++
                                  size--
                                  unlock mutex
```

**Bottleneck:** Only one thread can access the queue at a time. Under high contention, threads spend significant time waiting.

### Condition Variables (Blocking Dequeue)

For a producer-consumer model, a blocking dequeue that sleeps when the queue is empty is more efficient than spin-waiting.

```
Consumer thread:
   lock mutex
   while queue.is_empty():
       cond.wait(mutex)   // atomically: releases mutex, suspends thread
   // resumed by signal
   val = dequeue()
   unlock mutex

Producer thread:
   lock mutex
   enqueue(x)
   cond.signal()           // wake one waiting consumer
   unlock mutex
```

### Channel-Based Queue in Go

Go's built-in channels are queues. A buffered channel is a fixed-capacity FIFO queue with built-in synchronization.

```go
// Buffered channel = fixed-capacity concurrent queue
ch := make(chan int, 100)

// Enqueue (may block if full):
ch <- value

// Dequeue (may block if empty):
val := <-ch

// Non-blocking dequeue:
select {
case val := <-ch:
    // got value
default:
    // queue was empty
}
```

For unbounded concurrent queues in Go, use `sync.Mutex` + slice (as shown in Section 10.4), or a channel-of-channels pattern with dynamic sizing.

### Lock-Free Queue (Michael-Scott, conceptual)

```
Enqueue (CAS on tail):
1. Allocate new node
2. Read current tail (call it 'last')
3. Read last.next
4. If last.next == NULL:
     CAS(last.next, NULL, new_node)   // link new node
     CAS(tail, last, new_node)         // advance tail
   else:
     CAS(tail, last, last.next)        // help advance stale tail
     retry

Dequeue (CAS on head):
1. Read head (sentinel)
2. Read first = head.next (the actual front)
3. If first == NULL: queue is empty
4. Read value from first
5. CAS(head, head, first)              // advance head (first becomes new sentinel)
   if success: return value
   else: retry
```

Lock-free queues have better throughput under high contention because threads never block — they retry using CAS. However, they are harder to implement correctly and suffer from the ABA problem.

In Rust, `crossbeam::SegQueue` and `crossbeam::ArrayQueue` are production lock-free queues. In Go, the standard library uses lock-free queues internally for goroutine scheduling.

---

## 13. Choosing the Right Queue Variant

| Scenario                                          | Best Choice                              | Why                                                   |
|---------------------------------------------------|------------------------------------------|-------------------------------------------------------|
| Known max size, performance critical               | Circular buffer (power-of-2 capacity)    | Cache-friendly, no allocation, O(1) all ops           |
| Unknown max size, simple usage                    | Linked-list queue or dynamic ring buffer | Linked: O(1) guaranteed; ring buffer: cache friendlier|
| Elements must be processed by priority            | Binary heap (priority queue)             | O(log n) push/pop, O(1) peek-min                      |
| Need front AND back O(1) operations               | Deque (VecDeque in Rust, ring-backed)    | O(1) push/pop at both ends                            |
| Sliding window max/min                            | Monotonic deque                          | O(n) total, O(1) per element                          |
| BFS, level-order traversal                        | Any FIFO queue                           | Algorithm requires FIFO; use simplest option          |
| Multi-threaded producer-consumer                  | Mutex + condition variable               | Simple, correct, sufficient for most workloads        |
| Very high concurrency (many threads, high rate)   | Lock-free queue (crossbeam, etc.)        | Avoids mutex contention; higher throughput            |
| Functional programming (no mutable state)         | Two-stack queue (persistent)             | Amortized O(1) using immutable list pairs             |
| Event loop / async runtime                        | Bounded channel or ring buffer           | Backpressure (bounded) prevents unbounded memory use  |
| Cache-line sensitive (NUMA, embedded)             | Disruptor pattern (LMAX)                 | Single-producer, single-consumer, no false sharing    |

---

## 14. Mental Models Summary

### Model 1: The Pipe

Think of a queue as a pipe. Elements enter one end and exit the other. The pipe can be long or short, but you can only add at one end and remove at the other. You cannot skip elements or reach into the middle (pure queue). This model helps remember FIFO and the invariant that order is always preserved.

### Model 2: The Index Pair (Circular Buffer)

Two cursors, `head` and `tail`, chasing each other around a fixed circle. `tail` is always "ahead" of `head` in the direction of travel. The distance between them (modulo capacity) is the queue's current size. When they coincide, the queue is either empty or full — you need the `size` counter to know which.

### Model 3: The Two-Ended Caterpillar (Deque)

A deque is a caterpillar that can grow or shrink from both its head and tail. Adding to the front elongates the head; removing from the front shrinks it. Same for the tail. The order of body segments is always preserved.

### Model 4: The Tournament Tree (Heap)

A priority queue is a tournament. Each round, the better competitor wins. The winner of all rounds sits at the top (index 0). Inserting a new competitor places them at the bottom and they bubble up until they lose. Removing the champion promotes the last-placed entrant to the top and they sink down until they find their level.

### Model 5: The Lazy Accountant (Amortized O(1))

Resize is expensive when it happens, but it happens rarely. Think of it as a lazy accountant who does one hour of work occasionally to save many hours later. Over the course of n operations, the total work is O(n), so each operation "costs" O(1) on average even though some individual operations cost O(n).

### Model 6: The Decaying Candidates (Monotonic Deque)

The monotonic deque keeps only elements that could possibly be the window maximum. Anything smaller than a newly arrived element is redundant — it can never be the answer while the newcomer is in the window. Old elements expire from the front as the window slides. The front is always the current answer.

---

*This guide covers every significant aspect of queue data structures and manipulation. For production usage, always prefer well-tested library implementations (Rust's `std::collections::VecDeque`, Go's `container/heap`, C++'s `std::queue`) over hand-rolled versions, except when you need specific properties (custom allocators, lock-free behavior, bounded capacity with backpressure) that the standard library does not provide.*
