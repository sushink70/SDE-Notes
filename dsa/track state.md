# The Complete State-Tracking Mastery Guide
## Recursion · Dynamic Programming · Backtracking

> *"The master programmer does not write code — they command state machines."*

---

## Table of Contents

1. [What Is "State"?](#1-what-is-state)
2. [The CPU Stack — What Actually Happens on Real Hardware](#2-the-cpu-stack)
3. [Mental Models for State Tracking](#3-mental-models)
4. [Recursion — Deep State Tracking](#4-recursion)
   - 4.1 Activation Frames
   - 4.2 The Three Phases of Every Recursive Call
   - 4.3 Tracing Method: The Execution Table
   - 4.4 Full Example: Fibonacci with Frame-by-Frame Trace
   - 4.5 Full Example: Tree Traversal
   - 4.6 Tail Recursion vs Head Recursion
   - 4.7 Implementation: Go, C, Rust
5. [Dynamic Programming — State Tracking](#5-dynamic-programming)
   - 5.1 What Is "State" in DP?
   - 5.2 The DP State Machine Model
   - 5.3 Top-Down (Memoization) — Tracing the Memo Table
   - 5.4 Bottom-Up (Tabulation) — Tracing the DP Table
   - 5.5 State Transition Equations — How to Read and Write Them
   - 5.6 Full Example: Longest Common Subsequence (LCS) with Table Evolution
   - 5.7 Full Example: 0/1 Knapsack with State Evolution
   - 5.8 Implementation: Go, C, Rust
6. [Backtracking — State Tracking](#6-backtracking)
   - 6.1 The Choose-Explore-Unchoose (CEU) Model
   - 6.2 The Implicit Decision Tree
   - 6.3 State Restoration: The Critical Insight
   - 6.4 Full Example: N-Queens with State Trace
   - 6.5 Full Example: Permutations with Pruning
   - 6.6 Implementation: Go, C, Rust
7. [Combined: Backtracking + DP (Path Reconstruction)](#7-combined)
8. [Debugging Techniques for State](#8-debugging)
9. [Performance: Cache Behavior and Memory Reality](#9-performance)
10. [The Expert's Toolkit: Mental Models That Compound](#10-mental-models-toolkit)

---

## 1. What Is "State"?

Before writing a single line of code, you must understand what "state" means at a fundamental level.

**State** is the *complete snapshot of all information* needed to describe where your computation is at any moment in time.

Think of it like a photograph of your program: if you could freeze time and look at every variable, every stack frame, every data structure — that photograph is the **state**.

### State Has Three Dimensions

```
┌─────────────────────────────────────────────────────────────────┐
│                        PROGRAM STATE                            │
│                                                                 │
│  EXPLICIT STATE          IMPLICIT STATE         DERIVED STATE   │
│  ─────────────────        ────────────────        ────────────  │
│  Variables you wrote      The call stack          Computed      │
│  Arrays you maintain      Return addresses         results      │
│  Hash maps / tables       CPU registers            Memos        │
│  Flags (visited[])        Stack depth              Paths found  │
└─────────────────────────────────────────────────────────────────┘
```

### Why Tracking State Is Difficult

The human mind can hold approximately 7±2 chunks of information at once (Miller's Law). When recursion depth is 10, backtracking has 8 choices, and DP has a 2D table — you overflow your mental working memory instantly.

The solution is not "thinking harder." The solution is **having a systematic method** that externalizes state tracking.

---

## 2. The CPU Stack — What Actually Happens on Real Hardware

Understanding the real hardware behavior is essential for world-class programmers. Every recursive call has a physical cost.

### The Call Stack (Physical Reality)

When you call a function, the CPU:
1. Pushes the **return address** onto the stack (8 bytes on 64-bit)
2. Pushes the **base pointer** (frame pointer) — 8 bytes
3. Allocates space for **local variables** on the stack
4. The stack grows **downward** in memory (from high to low addresses)

```
HIGH ADDRESS
┌──────────────────────────┐
│   main() frame           │  ← Initial stack frame
│   local vars             │
│   return address         │
├──────────────────────────┤
│   fib(5) frame           │  ← First recursive call
│   n=5, local vars        │
│   saved base pointer     │
│   return address         │
├──────────────────────────┤
│   fib(4) frame           │  ← Second recursive call
│   n=4, local vars        │
│   saved base pointer     │
│   return address         │
├──────────────────────────┤
│   fib(3) frame           │  Stack pointer (SP) ─→ grows down
│   ...                    │
└──────────────────────────┘
LOW ADDRESS
```

### Stack Frame Size Matters for Performance

Each stack frame is typically 16–128 bytes (aligned to 16 bytes on x86-64). A recursive call with depth 1000 uses:
- `1000 × 64 bytes = 64 KB` — well within typical stack size (8 MB on Linux)
- A depth of 100,000 causes **stack overflow**

This is why iterative DP always beats recursive DP at depth: **no stack overhead, no function call overhead, better cache locality**.

### Cache Line Behavior

When you access `dp[i]` sequentially (bottom-up DP), you get **cache hits** because the CPU loads 64 bytes (a cache line) at once — consecutive array elements are already in cache. When recursion jumps around the array randomly, you get **cache misses** — 100–200 CPU cycles wasted per miss vs 1–4 cycles for a cache hit.

---

## 3. Mental Models for State Tracking

Before we dive into specific techniques, here are the master models that apply everywhere.

### Model 1: The Photograph Model
At any point during execution, you should be able to "take a photograph" and answer:
- What is the current value of every variable?
- What calls are on the stack? In what order?
- What has been chosen/committed? What is still undecided?

### Model 2: The Decision Tree Model
Every algorithm with branching (recursion, backtracking, DP) makes **decisions**. A decision tree shows:
- **Nodes** = states (snapshots)
- **Edges** = transitions (choices made)
- **Leaves** = terminal states (base cases or solutions)

### Model 3: The Undo Stack Model (Critical for Backtracking)
Any state change that might need to be reversed should be thought of as a **push/pop** operation:
- **Push** = make a choice (modify state)
- **Pop** = undo the choice (restore state)

### Model 4: The Memo Table as a Cache
In DP, the memo table is a **cache** of sub-problems you've already solved. State tracking in DP means tracking which cells of this table have been filled and in what order.

### Model 5: The Wave Front Model (Bottom-Up DP)
Imagine solutions spreading like a wave. Each cell in the DP table is computed only after all cells it depends on are already computed. Tracking state = tracking the wave front.

---

## 4. Recursion — Deep State Tracking

### 4.1 Activation Frames

An **activation frame** (also called a **stack frame** or **activation record**) is the collection of all data belonging to a single function call:

```
┌─────────────────────────────────────┐
│         ACTIVATION FRAME            │
│                                     │
│  Parameters:   n = 5                │
│  Local vars:   left = ?, right = ?  │
│  Return addr:  → caller location    │
│  Saved regs:   (CPU registers)      │
│  Return value: (will be set)        │
└─────────────────────────────────────┘
```

**Key insight**: Each recursive call creates a **new, independent activation frame**. The `n` in `fib(5)` and the `n` in `fib(4)` are **different variables** in different frames, even though they have the same name.

### 4.2 The Three Phases of Every Recursive Call

Every recursive function goes through exactly three phases:

```
Phase 1: DESCENT (going down)
─────────────────────────────
Make the recursive call(s).
State is being BUILT UP on the stack.
Nothing is returned yet.

Phase 2: BASE CASE (hitting bottom)
────────────────────────────────────
Return a concrete value.
The descent stops.
The ascent begins.

Phase 3: ASCENT (coming back up)
─────────────────────────────────
Process return values from sub-calls.
Combine results.
Return upward.
State is being CLEANED UP from the stack.
```

### 4.3 Tracing Method: The Execution Table

This is the systematic tool to track recursion manually. For every call, record:

| Call # | Function Call | Phase | Local State | Returns |
|--------|--------------|-------|-------------|---------|
| 1      | fib(4)       | Desc  | n=4         | —       |
| 2      | fib(3)       | Desc  | n=3         | —       |
| 3      | fib(2)       | Desc  | n=2         | —       |
| 4      | fib(1)       | Base  | n=1         | 1       |
| 5      | fib(0)       | Base  | n=0         | 0       |
| 6      | fib(2)       | Asc   | n=2, l=1,r=0| 1      |
| ...    | ...          | ...   | ...         | ...     |

### 4.4 Full Example: Fibonacci — Complete Frame-by-Frame Trace

**Problem**: Compute fib(4) = fib(3) + fib(2) = 3

```
Call Tree:
                fib(4)
               /      \
           fib(3)      fib(2)
          /     \      /    \
       fib(2)  fib(1) fib(1) fib(0)
       /   \
    fib(1) fib(0)
```

**Stack Evolution (reading top = newest frame):**

```
TIME 1: Call fib(4)
Stack: [fib(4): n=4]

TIME 2: Call fib(3) from fib(4)
Stack: [fib(3): n=3] ← TOP
       [fib(4): n=4, waiting for left]

TIME 3: Call fib(2) from fib(3)
Stack: [fib(2): n=2] ← TOP
       [fib(3): n=3, waiting for left]
       [fib(4): n=4, waiting for left]

TIME 4: Call fib(1) from fib(2) — BASE CASE
Stack: [fib(1): n=1] ← TOP, returns 1
       [fib(2): n=2, waiting for left]
       [fib(3): n=3, waiting for left]
       [fib(4): n=4, waiting for left]

TIME 5: fib(1) returns 1, fib(2) now calls fib(0)
Stack: [fib(0): n=0] ← TOP, returns 0
       [fib(2): n=2, left=1, waiting for right]
       [fib(3): n=3, waiting for left]
       [fib(4): n=4, waiting for left]

TIME 6: fib(0) returns 0, fib(2) computes 1+0=1, returns 1
Stack: [fib(3): n=3, left=1, waiting for right] ← TOP
       [fib(4): n=4, waiting for left]

TIME 7: fib(3) calls fib(1) — BASE CASE
Stack: [fib(1): n=1] ← TOP, returns 1
       [fib(3): n=3, left=1, waiting for right]
       [fib(4): n=4, waiting for left]

TIME 8: fib(1) returns 1, fib(3) computes 1+1=2, returns 2
Stack: [fib(4): n=4, left=2, waiting for right] ← TOP

... (right subtree fib(2) similarly returns 1)

TIME FINAL: fib(4) computes 2+1=3, returns 3
Stack: [] EMPTY
```

**Critical Observation**: Notice how `fib(2)` is computed TWICE (once in left subtree of fib(3), once as right child of fib(4)). This is **redundant computation** — the core motivation for memoization.

### 4.5 Full Example: Tree Traversal with State Trace

Tree traversal is the purest form of recursion because the data structure itself IS the recursive structure.

**In-order traversal** (Left → Node → Right):

```
        4
       / \
      2   6
     / \ / \
    1  3 5  7
```

**State trace for in-order:**

```
Call inorder(4)
  Call inorder(2)        ← go left first
    Call inorder(1)
      Call inorder(nil)  ← base case, return
      VISIT 1            ← print 1
      Call inorder(nil)  ← base case, return
    ← inorder(1) returns
    VISIT 2              ← print 2
    Call inorder(3)
      Call inorder(nil)  ← base case
      VISIT 3            ← print 3
      Call inorder(nil)  ← base case
    ← inorder(3) returns
  ← inorder(2) returns
  VISIT 4                ← print 4
  Call inorder(6)
    (mirrors left side...)
  ← inorder(6) returns
← inorder(4) returns

Output: 1 2 3 4 5 6 7
```

**The key state to track**: Which node am I currently visiting? Have I visited its left child yet? Have I visited its right child yet? This is encoded implicitly in the call stack.

### 4.6 Tail Recursion vs Head Recursion

**Head recursion**: The recursive call happens BEFORE other work in the current frame.
```
fib(n) = fib(n-1) + fib(n-2)
         ↑ recursive first, then add
```
State accumulates UPWARD — you can't compute the result until all sub-calls return.

**Tail recursion**: The recursive call is the LAST operation.
```
factorial_tail(n, acc) = factorial_tail(n-1, acc * n)
                         ↑ recursive IS the last op
```
Compilers can optimize tail recursion into a LOOP — no new stack frame needed! The accumulator `acc` carries the state forward instead of building it on the stack.

**Tail Recursion State Model**:
```
Instead of:           Tail recursive:
fib(5) waits          fib_tail(5, 0, 1)
  fib(4) waits          fib_tail(4, 1, 1)   ← no waiting!
    fib(3) waits          fib_tail(3, 1, 2)
      ...                   fib_tail(2, 2, 3)
                              fib_tail(1, 3, 5)
                                return 5
```

The state is carried **forward** in the accumulator, not **backward** through return values.

### 4.7 Implementation: Fibonacci in Go, C, Rust

#### Go Implementation

```go
package main

import "fmt"

// ─────────────────────────────────────────────────────────────────────────────
// NAIVE RECURSION — Illustrates the problem of redundant computation
// Time: O(2^n), Space: O(n) stack depth
// ─────────────────────────────────────────────────────────────────────────────

func fibNaive(n int) int {
    // Base cases: these are the "leaves" of our recursion tree
    if n <= 0 {
        return 0
    }
    if n == 1 {
        return 1
    }
    // HEAD recursion: both sub-calls must complete before we can add
    return fibNaive(n-1) + fibNaive(n-2)
}

// ─────────────────────────────────────────────────────────────────────────────
// TRACED RECURSION — Shows frame-by-frame state (for learning/debugging)
// Same algorithm, but we print each activation frame explicitly
// ─────────────────────────────────────────────────────────────────────────────

func fibTraced(n, depth int) int {
    indent := ""
    for i := 0; i < depth; i++ {
        indent += "  "
    }
    fmt.Printf("%s→ fib(%d) called [depth=%d]\n", indent, n, depth)

    if n <= 0 {
        fmt.Printf("%s← fib(%d) returns 0 [BASE CASE]\n", indent, n)
        return 0
    }
    if n == 1 {
        fmt.Printf("%s← fib(%d) returns 1 [BASE CASE]\n", indent, n)
        return 1
    }

    left := fibTraced(n-1, depth+1)
    right := fibTraced(n-2, depth+1)
    result := left + right

    fmt.Printf("%s← fib(%d) returns %d [left=%d, right=%d]\n",
        indent, n, result, left, right)
    return result
}

// ─────────────────────────────────────────────────────────────────────────────
// TAIL RECURSIVE — Compiler can optimize to a loop
// State carried forward in (a, b) accumulators, not backward via return
// Time: O(n), Space: O(1) if compiler optimizes, O(n) worst case
// ─────────────────────────────────────────────────────────────────────────────

// fibTail is the exported wrapper — hides the accumulator from callers
func fibTail(n int) int {
    return fibTailHelper(n, 0, 1)
}

// fibTailHelper carries state FORWARD: a=fib(i), b=fib(i+1)
func fibTailHelper(n, a, b int) int {
    if n == 0 {
        return a // No waiting — immediate return
    }
    // The recursive call is the LAST operation — tail position
    return fibTailHelper(n-1, b, a+b)
}

// ─────────────────────────────────────────────────────────────────────────────
// IN-ORDER TREE TRAVERSAL — Shows recursive state on a data structure
// ─────────────────────────────────────────────────────────────────────────────

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

// newNode is a constructor — idiomatic Go
func newNode(val int) *TreeNode {
    return &TreeNode{Val: val}
}

// inOrder visits Left → Current → Right
// State tracked: which subtree has been visited (implicit in call stack)
func inOrder(node *TreeNode, result *[]int) {
    if node == nil {
        return // Base case: empty tree
    }
    inOrder(node.Left, result)   // Phase 1: explore left
    *result = append(*result, node.Val) // Phase 2: visit current
    inOrder(node.Right, result)  // Phase 3: explore right
}

func main() {
    // Test naive fib
    fmt.Println("=== NAIVE FIB(6) ===")
    fmt.Printf("fib(6) = %d\n\n", fibNaive(6))

    // Test traced fib — observe the call tree
    fmt.Println("=== TRACED FIB(4) ===")
    fibTraced(4, 0)
    fmt.Println()

    // Test tail fib
    fmt.Println("=== TAIL FIB(10) ===")
    fmt.Printf("fib(10) = %d\n\n", fibTail(10))

    // Test tree traversal
    //       4
    //      / \
    //     2   6
    //    / \ / \
    //   1  3 5  7
    root := newNode(4)
    root.Left = newNode(2)
    root.Right = newNode(6)
    root.Left.Left = newNode(1)
    root.Left.Right = newNode(3)
    root.Right.Left = newNode(5)
    root.Right.Right = newNode(7)

    result := []int{}
    inOrder(root, &result)
    fmt.Println("In-order:", result) // [1 2 3 4 5 6 7]
}
```

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ─────────────────────────────────────────────────────────────────────────────
 * CONSTANTS — Never use magic numbers
 * ───────────────────────────────────────────────────────────────────────────*/
#define MAX_DEPTH       50
#define INDENT_SIZE     2
#define TREE_VAL_NONE   -1

/* ─────────────────────────────────────────────────────────────────────────────
 * NAIVE FIBONACCI — Pure recursion, shows redundant computation
 * Time: O(2^n), Space: O(n) stack depth
 * ───────────────────────────────────────────────────────────────────────────*/
long long fib_naive(int n) {
    if (n < 0) return 0;    /* guard: negative input */
    if (n == 0) return 0;
    if (n == 1) return 1;
    return fib_naive(n - 1) + fib_naive(n - 2);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * TRACED FIBONACCI — Shows activation frames explicitly
 * ───────────────────────────────────────────────────────────────────────────*/
long long fib_traced(int n, int depth) {
    /* Print indent proportional to depth */
    for (int i = 0; i < depth * INDENT_SIZE; i++) putchar(' ');
    printf("→ fib(%d) called [depth=%d]\n", n, depth);

    long long result;
    if (n <= 0) {
        result = 0;
        for (int i = 0; i < depth * INDENT_SIZE; i++) putchar(' ');
        printf("← fib(%d) returns %lld [BASE]\n", n, result);
        return result;
    }
    if (n == 1) {
        result = 1;
        for (int i = 0; i < depth * INDENT_SIZE; i++) putchar(' ');
        printf("← fib(%d) returns %lld [BASE]\n", n, result);
        return result;
    }

    long long left  = fib_traced(n - 1, depth + 1);
    long long right = fib_traced(n - 2, depth + 1);
    result = left + right;

    for (int i = 0; i < depth * INDENT_SIZE; i++) putchar(' ');
    printf("← fib(%d) returns %lld [left=%lld, right=%lld]\n",
           n, result, left, right);
    return result;
}

/* ─────────────────────────────────────────────────────────────────────────────
 * TAIL RECURSIVE FIBONACCI — State carried forward in accumulators
 * Note: C compilers (with -O2) may optimize tail calls, but it's NOT
 * guaranteed unlike in functional languages. Use iteration for certainty.
 * ───────────────────────────────────────────────────────────────────────────*/
static long long fib_tail_helper(int n, long long a, long long b) {
    if (n == 0) return a;
    return fib_tail_helper(n - 1, b, a + b); /* tail position */
}

long long fib_tail(int n) {
    if (n < 0) return 0;
    return fib_tail_helper(n, 0LL, 1LL);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * BINARY TREE — In-order traversal with state trace
 * ───────────────────────────────────────────────────────────────────────────*/
typedef struct TreeNode {
    int            val;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

/* Allocate a new tree node — caller owns the memory */
static TreeNode *tree_node_new(int val) {
    TreeNode *node = malloc(sizeof(TreeNode));
    if (node == NULL) {
        fprintf(stderr, "ERROR: malloc failed in tree_node_new\n");
        exit(EXIT_FAILURE);
    }
    node->val   = val;
    node->left  = NULL;
    node->right = NULL;
    return node;
}

/* Free the entire tree recursively — caller must call this */
static void tree_free(TreeNode *node) {
    if (node == NULL) return;
    tree_free(node->left);
    tree_free(node->right);
    free(node);
}

/* In-order traversal: Left → Current → Right
 * out_arr: caller-provided array to store results
 * out_len: pointer to current fill index (caller must zero-initialize)
 * capacity: size of out_arr
 */
static void in_order(const TreeNode *node,
                     int *out_arr,
                     int *out_len,
                     int capacity)
{
    if (node == NULL) return; /* base case */
    if (*out_len >= capacity) {
        fprintf(stderr, "ERROR: output array overflow in in_order\n");
        return;
    }

    in_order(node->left,  out_arr, out_len, capacity); /* Phase 1: Left  */
    out_arr[(*out_len)++] = node->val;                 /* Phase 2: Visit */
    in_order(node->right, out_arr, out_len, capacity); /* Phase 3: Right */
}

/* ─────────────────────────────────────────────────────────────────────────────
 * MAIN — Test driver
 * ───────────────────────────────────────────────────────────────────────────*/
int main(void) {
    /* Naive fib */
    printf("=== NAIVE FIB(6) ===\n");
    printf("fib(6) = %lld\n\n", fib_naive(6));

    /* Traced fib */
    printf("=== TRACED FIB(4) ===\n");
    fib_traced(4, 0);
    printf("\n");

    /* Tail fib */
    printf("=== TAIL FIB(10) ===\n");
    printf("fib(10) = %lld\n\n", fib_tail(10));

    /* Tree traversal */
    /*
     *       4
     *      / \
     *     2   6
     *    / \ / \
     *   1  3 5  7
     */
    TreeNode *root = tree_node_new(4);
    root->left               = tree_node_new(2);
    root->right              = tree_node_new(6);
    root->left->left         = tree_node_new(1);
    root->left->right        = tree_node_new(3);
    root->right->left        = tree_node_new(5);
    root->right->right       = tree_node_new(7);

    int results[16] = {0};
    int results_len = 0;
    in_order(root, results, &results_len, 16);

    printf("In-order: [");
    for (int i = 0; i < results_len; i++) {
        printf("%d%s", results[i], (i + 1 < results_len) ? ", " : "");
    }
    printf("]\n");

    tree_free(root); /* Always free what you allocate */
    return EXIT_SUCCESS;
}
```

#### Rust Implementation

```rust
//! State Tracking in Recursion — Rust Implementation
//! 
//! Rust's ownership system makes state tracking explicit:
//! - Borrowed state: shared references (&T) — read-only snapshot
//! - Mutable borrowed state: (&mut T) — exclusive modification
//! - Owned state: (T) — moved into the recursive call
//! 
//! The compiler enforces correct state management at compile time.

use std::fmt;

// ─────────────────────────────────────────────────────────────────────────────
// NAIVE FIBONACCI
// Time: O(2^n), Space: O(n) stack
// ─────────────────────────────────────────────────────────────────────────────

fn fib_naive(n: u64) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => fib_naive(n - 1) + fib_naive(n - 2),
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// TRACED FIBONACCI — Explicit activation frame logging
// In Rust, depth is passed by value (copy) — each frame has its own copy
// ─────────────────────────────────────────────────────────────────────────────

fn fib_traced(n: u64, depth: usize) -> u64 {
    let indent = "  ".repeat(depth);
    println!("{}→ fib({}) called [depth={}]", indent, n, depth);

    let result = match n {
        0 => {
            println!("{}← fib({}) returns 0 [BASE CASE]", indent, n);
            0
        }
        1 => {
            println!("{}← fib({}) returns 1 [BASE CASE]", indent, n);
            1
        }
        _ => {
            let left  = fib_traced(n - 1, depth + 1);
            let right = fib_traced(n - 2, depth + 1);
            let val   = left + right;
            println!(
                "{}← fib({}) returns {} [left={}, right={}]",
                indent, n, val, left, right
            );
            val
        }
    };
    result
}

// ─────────────────────────────────────────────────────────────────────────────
// TAIL RECURSIVE FIBONACCI
// Note: Rust does NOT guarantee TCO (Tail Call Optimization) in the general case.
// For guaranteed O(1) stack, convert to iterative.
// But the pattern teaches forward state accumulation.
// ─────────────────────────────────────────────────────────────────────────────

fn fib_tail(n: u64) -> u64 {
    fn helper(n: u64, a: u64, b: u64) -> u64 {
        match n {
            0 => a,                           // State in `a` — return directly
            _ => helper(n - 1, b, a + b),    // Carry state forward
        }
    }
    helper(n, 0, 1)
}

// ─────────────────────────────────────────────────────────────────────────────
// BINARY TREE — In-order traversal
// Box<T> = heap-allocated node (Rust requires known size at compile time)
// Option<Box<TreeNode>> = either a node or None (no null pointers in Rust!)
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug)]
struct TreeNode {
    val:   i32,
    left:  Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

impl TreeNode {
    /// Constructor — idiomatic Rust uses `new` associated function
    fn new(val: i32) -> Self {
        TreeNode {
            val,
            left:  None,
            right: None,
        }
    }

    /// Wraps self in Box and Option — convenience for building trees
    fn boxed(val: i32) -> Option<Box<Self>> {
        Some(Box::new(Self::new(val)))
    }
}

/// In-order traversal: Left → Current → Right
/// 
/// `result` is passed as &mut — we borrow it mutably through all frames.
/// The borrow checker ensures only ONE frame can mutate it at a time.
/// Since recursion is sequential (not concurrent), this is safe.
fn in_order(node: &Option<Box<TreeNode>>, result: &mut Vec<i32>) {
    // Pattern matching on Option<Box<T>> — idiomatic Rust
    if let Some(n) = node {
        in_order(&n.left, result);    // Phase 1: Left subtree
        result.push(n.val);           // Phase 2: Visit current node
        in_order(&n.right, result);   // Phase 3: Right subtree
    }
    // If None: base case — do nothing (implicit return)
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────────────────────

fn main() {
    // Naive fib
    println!("=== NAIVE FIB(6) ===");
    println!("fib(6) = {}\n", fib_naive(6));

    // Traced fib
    println!("=== TRACED FIB(4) ===");
    fib_traced(4, 0);
    println!();

    // Tail fib
    println!("=== TAIL FIB(10) ===");
    println!("fib(10) = {}\n", fib_tail(10));

    // Tree:     4
    //          / \
    //         2   6
    //        / \ / \
    //       1  3 5  7
    let mut root = Box::new(TreeNode::new(4));
    root.left = Some(Box::new(TreeNode {
        val:   2,
        left:  TreeNode::boxed(1),
        right: TreeNode::boxed(3),
    }));
    root.right = Some(Box::new(TreeNode {
        val:   6,
        left:  TreeNode::boxed(5),
        right: TreeNode::boxed(7),
    }));

    let mut result = Vec::new();
    in_order(&Some(root), &mut result);
    println!("In-order: {:?}", result); // [1, 2, 3, 4, 5, 6, 7]
}
```

---

## 5. Dynamic Programming — State Tracking

### 5.1 What Is "State" in DP?

In DP, **state** is a precise description of a sub-problem. It answers: *"What exactly do I need to know to solve this particular sub-problem?"*

**Key terminology**:
- **Sub-problem**: A smaller instance of the original problem
- **State variable**: A parameter that uniquely identifies a sub-problem (e.g., `i`, `j`, `capacity`)
- **State space**: The set of all possible sub-problems (all combinations of state variables)
- **Optimal substructure**: The optimal solution to the big problem can be built from optimal solutions to sub-problems
- **Overlapping sub-problems**: The same sub-problem is computed many times in naive recursion — DP caches it

### 5.2 The DP State Machine Model

Think of DP as a **directed acyclic graph (DAG)**:
- Each **node** = one sub-problem (one state)
- Each **edge** = one state transition (a recurrence relation)
- **Topological order** = the order in which we must solve sub-problems
- The **answer** = the value at the final node

```
State Space for fib(4):
(each node is a sub-problem, arrow = "depends on")

fib(0) ←── fib(2) ←── fib(4)
fib(1) ←──/     \←── fib(3) ←──/
         \──── fib(3)
              ↑
              fib(1)
```

We solve in topological order: fib(0), fib(1), fib(2), fib(3), fib(4).

### 5.3 Top-Down (Memoization) — Tracing the Memo Table

**Memoization** = recursion + caching. You write the recursion naturally, then add a cache.

**State of the memo table over time** (for fib(5)):

```
CALL SEQUENCE:        MEMO TABLE STATE AFTER EACH CALL:
─────────────────────────────────────────────────────────
fib(5) called         {}: empty
  fib(4) called       {}: still empty
    fib(3) called     {}: still empty  
      fib(2) called   {}: still empty
        fib(1) returns 1: {1:1}
        fib(0) returns 0: {1:1, 0:0}
      fib(2) = 1+0=1  {1:1, 0:0, 2:1}  ← STORED
      fib(1) is CACHED: {1:1, 0:0, 2:1} (lookup, no compute)
    fib(3) = 1+1=2    {1:1, 0:0, 2:1, 3:2}  ← STORED
      fib(2) is CACHED: {1:1, 0:0, 2:1, 3:2} (lookup)
  fib(4) = 2+1=3      {1:1, 0:0, 2:1, 3:2, 4:3}  ← STORED
    fib(3) is CACHED: (lookup)
fib(5) = 3+2=5        {1:1, 0:0, 2:1, 3:2, 4:3, 5:5}  ← STORED

FINAL MEMO TABLE:
┌───┬───┐
│ n │ v │
├───┼───┤
│ 0 │ 0 │
│ 1 │ 1 │
│ 2 │ 1 │
│ 3 │ 2 │
│ 4 │ 3 │
│ 5 │ 5 │
└───┴───┘
```

Each value is computed EXACTLY ONCE and then reused. Total computation: O(n) instead of O(2^n).

### 5.4 Bottom-Up (Tabulation) — Tracing the DP Table

**Tabulation** = fill the DP table iteratively, from base cases upward.

**State of table, wave by wave, for fib(6):**

```
INITIALIZATION:
dp = [0, 1, ?, ?, ?, ?, ?]
      ↑  ↑
   base base

WAVE 1 (i=2): dp[2] = dp[1] + dp[0] = 1 + 0 = 1
dp = [0, 1, 1, ?, ?, ?, ?]

WAVE 2 (i=3): dp[3] = dp[2] + dp[1] = 1 + 1 = 2
dp = [0, 1, 1, 2, ?, ?, ?]

WAVE 3 (i=4): dp[4] = dp[3] + dp[2] = 2 + 1 = 3
dp = [0, 1, 1, 2, 3, ?, ?]

WAVE 4 (i=5): dp[5] = dp[4] + dp[3] = 3 + 2 = 5
dp = [0, 1, 1, 2, 3, 5, ?]

WAVE 5 (i=6): dp[6] = dp[5] + dp[4] = 5 + 3 = 8
dp = [0, 1, 1, 2, 3, 5, 8]
              ↑             ↑
           computed       ANSWER
```

The "wave front" moves left to right. Each cell is computed exactly once. No stack overhead. Perfect cache locality (sequential memory access).

**Space Optimization Insight**: Notice that `dp[i]` only depends on `dp[i-1]` and `dp[i-2]`. We don't need the full array — just the last two values! This reduces O(n) space to O(1) space.

### 5.5 State Transition Equations — How to Read and Write Them

The **state transition equation** (also called the **recurrence relation**) is the heart of DP.

How to read: `dp[i][j] = max(dp[i-1][j], dp[i-1][j-w[i]] + v[i])`

- `dp[i][j]` = "the answer for the sub-problem with state (i, j)"
- `max(...)` = we choose the best option
- `dp[i-1][j]` = "if we DON'T include item i"
- `dp[i-1][j-w[i]] + v[i]` = "if we DO include item i"

The transition tells us: **what was the decision made at this state?** This is the connection between state tracking and optimal decision-making.

### 5.6 Full Example: Longest Common Subsequence (LCS) — 2D State Trace

**Problem**: Given strings `s1 = "ABCD"` and `s2 = "ACD"`, find the length of their longest common subsequence.

**State definition**: `dp[i][j]` = length of LCS of `s1[0..i]` and `s2[0..j]`

**Recurrence**:
```
if s1[i-1] == s2[j-1]:  dp[i][j] = dp[i-1][j-1] + 1
else:                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```

**Table evolution** (2D state — trace the filling order):

```
Initial state (all zeros):
       ""  A   C   D
    "" [0][ 0][ 0][ 0]
     A [0][ ?][ ?][ ?]
     B [0][ ?][ ?][ ?]
     C [0][ ?][ ?][ ?]
     D [0][ ?][ ?][ ?]

After row 1 (i=1, considering 'A' from s1):
       ""  A   C   D
    "" [0][ 0][ 0][ 0]
     A [0][ 1][ 1][ 1]   ← s1[0]='A'==s2[0]='A' → dp[1][1]=dp[0][0]+1=1
     B [0][ ?][ ?][ ?]
     C [0][ ?][ ?][ ?]
     D [0][ ?][ ?][ ?]

After row 2 (i=2, considering 'B' from s1):
       ""  A   C   D
    "" [0][ 0][ 0][ 0]
     A [0][ 1][ 1][ 1]
     B [0][ 1][ 1][ 1]   ← 'B' doesn't match 'A','C','D' → take max from above/left
     C [0][ ?][ ?][ ?]
     D [0][ ?][ ?][ ?]

After row 3 (i=3, considering 'C' from s1):
       ""  A   C   D
    "" [0][ 0][ 0][ 0]
     A [0][ 1][ 1][ 1]
     B [0][ 1][ 1][ 1]
     C [0][ 1][ 2][ 2]   ← s1[2]='C'==s2[1]='C' → dp[3][2]=dp[2][1]+1=2
     D [0][ ?][ ?][ ?]

After row 4 (i=4, considering 'D' from s1):
       ""  A   C   D
    "" [0][ 0][ 0][ 0]
     A [0][ 1][ 1][ 1]
     B [0][ 1][ 1][ 1]
     C [0][ 1][ 2][ 2]
     D [0][ 1][ 2][ 3]   ← s1[3]='D'==s2[2]='D' → dp[4][3]=dp[3][2]+1=3
                    ↑
                ANSWER = 3 (LCS = "ACD")
```

**Backtracking the path** (to find the actual LCS, not just its length):
Start at `dp[4][3]`:
- `s1[3]='D' == s2[2]='D'` → include 'D', go to `dp[3][2]`
- `s1[2]='C' == s2[1]='C'` → include 'C', go to `dp[2][1]`
- `s1[1]='B' != s2[0]='A'` → `dp[1][1] > dp[2][0]`, go UP to `dp[1][1]`
- `s1[0]='A' == s2[0]='A'` → include 'A', go to `dp[0][0]`
- At (0,0): done

Reading collected chars in reverse: "ACD" ✓

### 5.7 Full Example: 0/1 Knapsack — State Evolution

**Problem**: Items with weights [2, 3, 4] and values [3, 4, 5]. Capacity = 5.

**State**: `dp[i][w]` = max value using first `i` items with weight capacity `w`

```
Items: (weight=2, value=3), (weight=3, value=4), (weight=4, value=5)
Capacity = 5

Initial (all zeros):
         w=0  w=1  w=2  w=3  w=4  w=5
item 0:  [ 0][ 0][ 0][ 0][ 0][ 0]   ← no items
item 1:  [ 0][ ?][ ?][ ?][ ?][ ?]   ← consider item 1 (w=2, v=3)
item 2:  [ 0][ ?][ ?][ ?][ ?][ ?]   ← consider item 2 (w=3, v=4)
item 3:  [ 0][ ?][ ?][ ?][ ?][ ?]   ← consider item 3 (w=4, v=5)

After item 1 (w=2, v=3):
         w=0  w=1  w=2  w=3  w=4  w=5
item 0:  [ 0][ 0][ 0][ 0][ 0][ 0]
item 1:  [ 0][ 0][ 3][ 3][ 3][ 3]
                 ↑ at w=2: can fit item1, value=3

After item 2 (w=3, v=4):
         w=0  w=1  w=2  w=3  w=4  w=5
item 0:  [ 0][ 0][ 0][ 0][ 0][ 0]
item 1:  [ 0][ 0][ 3][ 3][ 3][ 3]
item 2:  [ 0][ 0][ 3][ 4][ 4][ 7]
                      ↑       ↑
                   only i2  i1+i2=3+4=7

After item 3 (w=4, v=5):
         w=0  w=1  w=2  w=3  w=4  w=5
item 0:  [ 0][ 0][ 0][ 0][ 0][ 0]
item 1:  [ 0][ 0][ 3][ 3][ 3][ 3]
item 2:  [ 0][ 0][ 3][ 4][ 4][ 7]
item 3:  [ 0][ 0][ 3][ 4][ 5][ 7]
                              ↑  ↑
                           i3   i1+i2 still wins!
                                 ANSWER = 7
```

**Decision tracking**: At `dp[3][5]=7`, why is it 7?
- `dp[2][5]=7` is greater than `dp[2][5-4]+5 = dp[2][1]+5 = 0+5 = 5`
- So we did NOT take item 3
- Go to `dp[2][5]=7`: `dp[1][5]=3 < dp[1][2]+4=3+4=7` → took item 2
- Go to `dp[1][2]=3`: took item 1 (weight 2 fits)
- Result: items 1 and 2 selected (total weight=5, total value=7) ✓

### 5.8 Implementation: DP in Go, C, Rust

#### Go Implementation

```go
package main

import "fmt"

// ─────────────────────────────────────────────────────────────────────────────
// FIBONACCI — Three DP approaches compared
// ─────────────────────────────────────────────────────────────────────────────

// Top-down: memoization with a map
// The memo map IS the state tracker — inspect it at any point to see progress
func fibMemo(n int, memo map[int]int) int {
    if n <= 0 {
        return 0
    }
    if n == 1 {
        return 1
    }
    if v, found := memo[n]; found {
        return v // State already computed — cache hit!
    }
    // State not yet computed — recurse and store
    result := fibMemo(n-1, memo) + fibMemo(n-2, memo)
    memo[n] = result // Store state for future use
    return result
}

// Bottom-up: tabulation, O(n) space
// dp[i] IS the state — inspect it after filling to see the whole picture
func fibTabulate(n int) int {
    if n <= 0 {
        return 0
    }
    if n == 1 {
        return 1
    }

    dp := make([]int, n+1) // Allocate state table
    dp[0] = 0              // Base state 0
    dp[1] = 1              // Base state 1

    for i := 2; i <= n; i++ {
        dp[i] = dp[i-1] + dp[i-2] // State transition
        // DEBUG: fmt.Printf("dp[%d] = %d\n", i, dp[i])
    }
    return dp[n]
}

// Space-optimized: O(1) space — only track the last 2 states
func fibOptimized(n int) int {
    if n <= 0 {
        return 0
    }
    if n == 1 {
        return 1
    }
    prev2, prev1 := 0, 1 // State: only last 2 values
    for i := 2; i <= n; i++ {
        curr    := prev1 + prev2 // New state
        prev2    = prev1         // Advance state window
        prev1    = curr
    }
    return prev1
}

// ─────────────────────────────────────────────────────────────────────────────
// LCS — Longest Common Subsequence (2D state table)
// ─────────────────────────────────────────────────────────────────────────────

// LCSResult holds both the length and the actual subsequence
type LCSResult struct {
    Length int
    Subseq string
}

func lcs(s1, s2 string) LCSResult {
    m, n := len(s1), len(s2)

    // State table: dp[i][j] = LCS length of s1[0..i-1] and s2[0..j-1]
    // Using (m+1)×(n+1) to handle empty-string base cases with index 0
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
        // dp[i][0] = 0 and dp[0][j] = 0 automatically (zero-initialized)
    }

    // Fill state table bottom-up (wave front: row by row, left to right)
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                // Characters match: extend LCS from diagonal
                dp[i][j] = dp[i-1][j-1] + 1
            } else {
                // No match: take best of excluding s1[i-1] or s2[j-1]
                if dp[i-1][j] > dp[i][j-1] {
                    dp[i][j] = dp[i-1][j]
                } else {
                    dp[i][j] = dp[i][j-1]
                }
            }
        }
    }

    // Backtrack through state table to reconstruct the actual LCS
    // This traces the DECISIONS made at each state
    result := make([]byte, 0, dp[m][n])
    i, j := m, n
    for i > 0 && j > 0 {
        if s1[i-1] == s2[j-1] {
            result = append(result, s1[i-1]) // This character was chosen
            i--
            j--
        } else if dp[i-1][j] > dp[i][j-1] {
            i-- // Came from above — didn't use s1[i-1]
        } else {
            j-- // Came from left — didn't use s2[j-1]
        }
    }

    // Reverse (we collected chars from end to start)
    for lo, hi := 0, len(result)-1; lo < hi; lo, hi = lo+1, hi-1 {
        result[lo], result[hi] = result[hi], result[lo]
    }

    return LCSResult{Length: dp[m][n], Subseq: string(result)}
}

// ─────────────────────────────────────────────────────────────────────────────
// 0/1 KNAPSACK — Classic 2D DP with decision tracking
// ─────────────────────────────────────────────────────────────────────────────

type Item struct {
    Weight int
    Value  int
    Name   string
}

type KnapsackResult struct {
    MaxValue    int
    ChosenItems []string
}

func knapsack(items []Item, capacity int) KnapsackResult {
    n := len(items)

    // State table: dp[i][w] = max value using first i items with capacity w
    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, capacity+1)
    }

    // Fill state table bottom-up
    for i := 1; i <= n; i++ {
        item := items[i-1]
        for w := 0; w <= capacity; w++ {
            // Option 1: Don't take item i
            dp[i][w] = dp[i-1][w]
            // Option 2: Take item i (only if it fits)
            if item.Weight <= w {
                withItem := dp[i-1][w-item.Weight] + item.Value
                if withItem > dp[i][w] {
                    dp[i][w] = withItem
                }
            }
        }
    }

    // Backtrack to find which items were chosen
    chosen := []string{}
    w := capacity
    for i := n; i > 0; i-- {
        // If state changed by adding item i, then item i was taken
        if dp[i][w] != dp[i-1][w] {
            chosen = append([]string{items[i-1].Name}, chosen...) // Prepend
            w -= items[i-1].Weight
        }
    }

    return KnapsackResult{MaxValue: dp[n][capacity], ChosenItems: chosen}
}

func main() {
    // Fibonacci DP comparison
    fmt.Println("=== FIBONACCI DP ===")
    memo := make(map[int]int)
    fmt.Printf("Top-down  fib(10) = %d\n", fibMemo(10, memo))
    fmt.Printf("Bottom-up fib(10) = %d\n", fibTabulate(10))
    fmt.Printf("Optimized fib(10) = %d\n\n", fibOptimized(10))

    // LCS
    fmt.Println("=== LCS ===")
    result := lcs("ABCD", "ACD")
    fmt.Printf("LCS(ABCD, ACD): length=%d, seq=%q\n\n", result.Length, result.Subseq)

    // Knapsack
    fmt.Println("=== KNAPSACK ===")
    items := []Item{
        {Weight: 2, Value: 3, Name: "item-A"},
        {Weight: 3, Value: 4, Name: "item-B"},
        {Weight: 4, Value: 5, Name: "item-C"},
    }
    kr := knapsack(items, 5)
    fmt.Printf("Max value: %d, Items: %v\n", kr.MaxValue, kr.ChosenItems)
}
```

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ─────────────────────────────────────────────────────────────────────────────
 * CONSTANTS
 * ───────────────────────────────────────────────────────────────────────────*/
#define DP_UNSET   (-1)
#define MAX_ITEMS   64
#define MAX_STR_LEN 256

/* ─────────────────────────────────────────────────────────────────────────────
 * FIBONACCI — Top-down with explicit memo array
 * State: memo[n] = -1 means "not yet computed"
 * ───────────────────────────────────────────────────────────────────────────*/
static long long fib_memo_helper(int n, long long *memo) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    if (memo[n] != DP_UNSET) {
        return memo[n]; /* Cache hit — state already computed */
    }
    memo[n] = fib_memo_helper(n - 1, memo) + fib_memo_helper(n - 2, memo);
    return memo[n];
}

long long fib_top_down(int n) {
    if (n < 0) return 0;
    long long *memo = malloc((size_t)(n + 1) * sizeof(long long));
    if (memo == NULL) { fprintf(stderr, "ERROR: malloc failed\n"); exit(EXIT_FAILURE); }
    for (int i = 0; i <= n; i++) memo[i] = DP_UNSET; /* Initialize state table */
    long long result = fib_memo_helper(n, memo);
    free(memo);
    return result;
}

/* Bottom-up: state table built iteratively */
long long fib_bottom_up(int n) {
    if (n < 0) return 0;
    if (n <= 1) return (long long)n;
    long long *dp = calloc((size_t)(n + 1), sizeof(long long));
    if (dp == NULL) { fprintf(stderr, "ERROR: calloc failed\n"); exit(EXIT_FAILURE); }
    dp[0] = 0;
    dp[1] = 1;
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i-1] + dp[i-2]; /* State transition */
    }
    long long result = dp[n];
    free(dp);
    return result;
}

/* ─────────────────────────────────────────────────────────────────────────────
 * LCS — 2D State Table
 * ───────────────────────────────────────────────────────────────────────────*/
typedef struct {
    int   length;
    char  subseq[MAX_STR_LEN];
} LCSResult;

/* dp is a 2D array stored as 1D (row-major) for cache efficiency */
#define DP_AT(dp, cols, i, j)  ((dp)[(i) * (cols) + (j)])

LCSResult lcs(const char *s1, const char *s2) {
    int m = (int)strlen(s1);
    int n = (int)strlen(s2);

    /* Allocate (m+1)×(n+1) state table, zero-initialized */
    int *dp = calloc((size_t)(m + 1) * (size_t)(n + 1), sizeof(int));
    if (dp == NULL) { fprintf(stderr, "ERROR: calloc failed in lcs\n"); exit(EXIT_FAILURE); }

    /* Fill state table bottom-up */
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (s1[i-1] == s2[j-1]) {
                DP_AT(dp, n+1, i, j) = DP_AT(dp, n+1, i-1, j-1) + 1;
            } else {
                int from_above = DP_AT(dp, n+1, i-1, j);
                int from_left  = DP_AT(dp, n+1, i,   j-1);
                DP_AT(dp, n+1, i, j) = (from_above > from_left) ? from_above : from_left;
            }
        }
    }

    /* Backtrack through state table to reconstruct LCS */
    LCSResult result;
    result.length = DP_AT(dp, n+1, m, n);

    char buf[MAX_STR_LEN];
    int  buf_len = 0;
    int  i = m, j = n;
    while (i > 0 && j > 0 && buf_len < MAX_STR_LEN - 1) {
        if (s1[i-1] == s2[j-1]) {
            buf[buf_len++] = s1[i-1]; /* This char was in LCS */
            i--; j--;
        } else if (DP_AT(dp, n+1, i-1, j) > DP_AT(dp, n+1, i, j-1)) {
            i--;
        } else {
            j--;
        }
    }
    buf[buf_len] = '\0';

    /* Reverse buf into result.subseq */
    for (int lo = 0, hi = buf_len - 1; lo < hi; lo++, hi--) {
        char tmp = buf[lo]; buf[lo] = buf[hi]; buf[hi] = tmp;
    }
    strncpy(result.subseq, buf, MAX_STR_LEN - 1);
    result.subseq[MAX_STR_LEN - 1] = '\0';

    free(dp);
    return result;
}

/* ─────────────────────────────────────────────────────────────────────────────
 * 0/1 KNAPSACK — 2D DP with decision tracking
 * ───────────────────────────────────────────────────────────────────────────*/
typedef struct {
    int weight;
    int value;
    const char *name;
} Item;

typedef struct {
    int  max_value;
    int  chosen[MAX_ITEMS];   /* chosen[i]=1 if item i is selected */
    int  num_chosen;
} KnapsackResult;

KnapsackResult knapsack(const Item *items, int n, int capacity) {
    /* Allocate (n+1)×(capacity+1) state table */
    int *dp = calloc((size_t)(n + 1) * (size_t)(capacity + 1), sizeof(int));
    if (dp == NULL) { fprintf(stderr, "ERROR: calloc failed in knapsack\n"); exit(EXIT_FAILURE); }

    /* Fill state table bottom-up */
    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= capacity; w++) {
            /* Option 1: skip item i */
            int skip = DP_AT(dp, capacity+1, i-1, w);
            /* Option 2: take item i if it fits */
            int take = 0;
            if (items[i-1].weight <= w) {
                take = DP_AT(dp, capacity+1, i-1, w - items[i-1].weight)
                       + items[i-1].value;
            }
            DP_AT(dp, capacity+1, i, w) = (take > skip) ? take : skip;
        }
    }

    /* Backtrack to find decisions */
    KnapsackResult result = { .max_value = DP_AT(dp, capacity+1, n, capacity),
                              .num_chosen = 0 };
    int w = capacity;
    for (int i = n; i > 0; i--) {
        if (DP_AT(dp, capacity+1, i, w) != DP_AT(dp, capacity+1, i-1, w)) {
            result.chosen[result.num_chosen++] = i - 1; /* 0-indexed item */
            w -= items[i-1].weight;
        }
    }

    free(dp);
    return result;
}

/* ─────────────────────────────────────────────────────────────────────────────
 * MAIN
 * ───────────────────────────────────────────────────────────────────────────*/
int main(void) {
    /* Fibonacci */
    printf("=== FIBONACCI DP ===\n");
    printf("Top-down  fib(10) = %lld\n", fib_top_down(10));
    printf("Bottom-up fib(10) = %lld\n\n", fib_bottom_up(10));

    /* LCS */
    printf("=== LCS ===\n");
    LCSResult lr = lcs("ABCD", "ACD");
    printf("LCS(ABCD, ACD): length=%d, seq=%s\n\n", lr.length, lr.subseq);

    /* Knapsack */
    printf("=== KNAPSACK ===\n");
    Item items[] = {
        {2, 3, "item-A"},
        {3, 4, "item-B"},
        {4, 5, "item-C"},
    };
    int n_items   = (int)(sizeof(items) / sizeof(items[0]));
    int capacity  = 5;
    KnapsackResult kr = knapsack(items, n_items, capacity);
    printf("Max value: %d\nChosen: ", kr.max_value);
    for (int i = kr.num_chosen - 1; i >= 0; i--) { /* reverse — backtrack goes backward */
        printf("%s ", items[kr.chosen[i]].name);
    }
    printf("\n");

    return EXIT_SUCCESS;
}
```

#### Rust Implementation

```rust
//! Dynamic Programming State Tracking — Rust
//! 
//! Key Rust-specific patterns for DP:
//! - Use Vec<Vec<T>> for 2D tables (avoid raw pointer arithmetic)
//! - Or use a flat Vec<T> with index arithmetic for cache efficiency
//! - HashMap for sparse memoization (when state space is huge but few states are visited)
//! - Use Option<T> as the "uncomputed" sentinel (not -1 magic numbers)

use std::collections::HashMap;

// ─────────────────────────────────────────────────────────────────────────────
// FIBONACCI — Top-down with HashMap memo
// Option<u64> naturally represents "computed" vs "not computed"
// ─────────────────────────────────────────────────────────────────────────────

fn fib_memo(n: u64, memo: &mut HashMap<u64, u64>) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => {
            if let Some(&v) = memo.get(&n) {
                return v; // Cache hit — state already computed
            }
            let val = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
            memo.insert(n, val); // Store state
            val
        }
    }
}

// Bottom-up: Vec IS the state table
fn fib_bottom_up(n: usize) -> u64 {
    if n == 0 { return 0; }
    if n == 1 { return 1; }

    let mut dp = vec![0u64; n + 1];
    dp[0] = 0;
    dp[1] = 1;
    for i in 2..=n {
        dp[i] = dp[i-1] + dp[i-2]; // State transition
    }
    dp[n]
}

// Space-optimized: O(1) — only previous two states kept
fn fib_optimized(n: usize) -> u64 {
    if n == 0 { return 0; }
    if n == 1 { return 1; }
    let (mut prev2, mut prev1) = (0u64, 1u64);
    for _ in 2..=n {
        let curr = prev1 + prev2;
        prev2     = prev1;
        prev1     = curr;
    }
    prev1
}

// ─────────────────────────────────────────────────────────────────────────────
// LCS — Longest Common Subsequence (2D State Table)
// ─────────────────────────────────────────────────────────────────────────────

struct LCSResult {
    length: usize,
    subseq: String,
}

fn lcs(s1: &[u8], s2: &[u8]) -> LCSResult {
    let (m, n) = (s1.len(), s2.len());

    // Flat 2D table stored as row-major Vec for cache efficiency
    // Index: dp[i * (n+1) + j]
    let mut dp = vec![0usize; (m + 1) * (n + 1)];

    // Fill state table bottom-up
    for i in 1..=m {
        for j in 1..=n {
            dp[i * (n+1) + j] = if s1[i-1] == s2[j-1] {
                dp[(i-1) * (n+1) + (j-1)] + 1 // Match: extend diagonal
            } else {
                // No match: take best from above or left
                dp[(i-1) * (n+1) + j].max(dp[i * (n+1) + (j-1)])
            };
        }
    }

    // Backtrack through state table
    let mut result = Vec::with_capacity(dp[m * (n+1) + n]);
    let (mut i, mut j) = (m, n);
    while i > 0 && j > 0 {
        if s1[i-1] == s2[j-1] {
            result.push(s1[i-1]);
            i -= 1; j -= 1;
        } else if dp[(i-1) * (n+1) + j] > dp[i * (n+1) + (j-1)] {
            i -= 1;
        } else {
            j -= 1;
        }
    }
    result.reverse(); // Collected end-to-start

    LCSResult {
        length: dp[m * (n+1) + n],
        subseq: String::from_utf8(result).unwrap_or_default(),
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 0/1 KNAPSACK — 2D DP with decision reconstruction
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug)]
struct Item {
    weight: usize,
    value:  usize,
    name:   &'static str,
}

struct KnapsackResult {
    max_value:    usize,
    chosen_names: Vec<&'static str>,
}

fn knapsack(items: &[Item], capacity: usize) -> KnapsackResult {
    let n = items.len();

    // State table: dp[i][w] = max value with first i items and capacity w
    // Flat representation for cache-friendly row-major access
    let cols = capacity + 1;
    let mut dp = vec![0usize; (n + 1) * cols];

    // Fill state table
    for i in 1..=n {
        let item = &items[i - 1];
        for w in 0..=capacity {
            let skip = dp[(i-1) * cols + w];
            let take = if item.weight <= w {
                dp[(i-1) * cols + (w - item.weight)] + item.value
            } else {
                0
            };
            dp[i * cols + w] = skip.max(take);
        }
    }

    // Backtrack: trace which decisions led to the optimal state
    let mut chosen = Vec::new();
    let mut w = capacity;
    for i in (1..=n).rev() {
        if dp[i * cols + w] != dp[(i-1) * cols + w] {
            chosen.push(items[i-1].name);
            w -= items[i-1].weight;
        }
    }
    chosen.reverse();

    KnapsackResult {
        max_value:    dp[n * cols + capacity],
        chosen_names: chosen,
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────────────────────

fn main() {
    // Fibonacci
    println!("=== FIBONACCI DP ===");
    let mut memo = HashMap::new();
    println!("Top-down  fib(10) = {}", fib_memo(10, &mut memo));
    println!("Bottom-up fib(10) = {}", fib_bottom_up(10));
    println!("Optimized fib(10) = {}\n", fib_optimized(10));

    // LCS
    println!("=== LCS ===");
    let result = lcs(b"ABCD", b"ACD");
    println!("LCS(ABCD, ACD): length={}, seq={}\n", result.length, result.subseq);

    // Knapsack
    println!("=== KNAPSACK ===");
    let items = vec![
        Item { weight: 2, value: 3, name: "item-A" },
        Item { weight: 3, value: 4, name: "item-B" },
        Item { weight: 4, value: 5, name: "item-C" },
    ];
    let kr = knapsack(&items, 5);
    println!("Max value: {}", kr.max_value);
    println!("Chosen: {:?}", kr.chosen_names);
}
```

---

## 6. Backtracking — State Tracking

### 6.1 The Choose-Explore-Unchoose (CEU) Model

Backtracking is the art of **systematic exploration with state restoration**. Every backtracking algorithm follows this exact pattern:

```
function backtrack(state, choices):
    if is_solution(state):
        record(state)
        return

    for each choice in choices:
        ┌─── CHOOSE ───────────────────────────────────────────┐
        │  make_choice(choice)      // Modify state            │
        │  mark_as_used(choice)     // Update tracking         │
        └───────────────────────────────────────────────────────┘

        ┌─── EXPLORE ──────────────────────────────────────────┐
        │  backtrack(state, remaining_choices)                 │
        └───────────────────────────────────────────────────────┘

        ┌─── UNCHOOSE (Undo/Restore) ───────────────────────────┐
        │  undo_choice(choice)      // Restore state           │
        │  mark_as_unused(choice)   // Restore tracking        │
        └───────────────────────────────────────────────────────┘
```

**The crucial invariant**: After the UNCHOOSE step, state must be *identical* to what it was before the CHOOSE step. This is called **state restoration** or **backtracking**.

### 6.2 The Implicit Decision Tree

Every backtracking problem has an implicit decision tree. You never build this tree explicitly — the call stack IS the tree.

For permutations of [1, 2, 3]:

```
                         []
                    /    |    \
                 [1]    [2]    [3]
                /  \   / \   /  \
            [1,2][1,3][2,1][2,3][3,1][3,2]
              |   |   |   |   |   |
           [1,2,3][1,3,2]...  (leaves = solutions)
```

At each **node** in this tree, the algorithm's **state** is:
- `current` = the partial permutation built so far
- `used[]` = which numbers have been chosen

### 6.3 State Restoration: The Critical Insight

**Why state restoration is necessary**: When you backtrack from a dead end, you need to try different choices. But you can only try different choices from the SAME state you started at. If state wasn't restored, you'd be exploring from a corrupted state.

**Two approaches to state restoration**:

```
APPROACH 1: EXPLICIT UNDO
──────────────────────────
choose:    path.append(x)
explore:   recurse(...)
unchoose:  path.pop()       ← Must be exact reverse of choose

APPROACH 2: COPY STATE (expensive but safe)
────────────────────────────────────────────
choose:    new_path = path.copy() + [x]
explore:   recurse(new_path, ...)
unchoose:  (nothing needed — original path untouched)
```

**Expert practitioners prefer Approach 1** (explicit undo) because it avoids O(n) copies at each level. But it requires being PRECISE about what was modified and undoing it exactly.

**Common mistakes in state restoration**:

```
WRONG (state leak):
path.append(x)
recurse(...)
path.clear()    ← Wrong! If path had elements before, they're gone

CORRECT:
path.append(x)
recurse(...)
path.pop()      ← Exact inverse of append
```

### 6.4 Full Example: N-Queens — State Trace

**Problem**: Place N queens on an N×N chessboard so no two queens attack each other.

**State to track**:
- `row`: current row being filled (we place one queen per row — already a pruning)
- `cols[]`: which column is occupied in each row
- `diag1[]` (diagonal /): tracks occupied diagonals of type (row - col)
- `diag2[]` (diagonal \): tracks occupied diagonals of type (row + col)

**State trace for N=4, first few steps**:

```
Initial state: row=0, cols=[], diag1={}, diag2={}
Board:
. . . .
. . . .
. . . .
. . . .

CALL backtrack(row=0):
  Try col=0:
    CHOOSE: place queen at (0,0)
    State: cols=[0], diag1={0-0=0}, diag2={0+0=0}
    Board:
    Q . . .
    . . . .
    . . . .
    . . . .

    CALL backtrack(row=1):
      Try col=0: PRUNED (col 0 used)
      Try col=1: PRUNED (diag2: 1+1=2? No. diag1: 1-1=0 ✓ used!)
      Try col=2:
        CHOOSE: place queen at (1,2)
        State: cols=[0,2], diag1={0,-1}, diag2={0,3}
        Board:
        Q . . .
        . . Q .
        . . . .
        . . . .

        CALL backtrack(row=2):
          Try col=0: PRUNED (col 0 used)
          Try col=1: diag1: 2-1=1 OK, diag2: 2+1=3 PRUNED (used!)
          Try col=2: PRUNED (col 2 used)
          Try col=3: diag1: 2-3=-1 PRUNED (used!)
          → NO VALID PLACEMENT! Return.

        UNCHOOSE: remove queen from (1,2)
        State restored: cols=[0], diag1={0}, diag2={0}

      Try col=3:
        CHOOSE: place queen at (1,3)
        State: cols=[0,3], diag1={0,-2}, diag2={0,4}
        ... (continues)
```

**Pruning**: The PRUNED annotations show where we cut branches early — we don't explore a column if a queen already attacks it. Good pruning is what makes backtracking practical.

### 6.5 Full Example: Permutations — State Trace

**Problem**: Generate all permutations of [1, 2, 3].

**State trace**:

```
Call backtrack(current=[], used={})

  CHOOSE 1: current=[1], used={1}
  Call backtrack(current=[1], used={1})

    CHOOSE 2: current=[1,2], used={1,2}
    Call backtrack(current=[1,2], used={1,2})

      CHOOSE 3: current=[1,2,3], used={1,2,3}
      Call backtrack(current=[1,2,3], used={1,2,3})
        → SOLUTION FOUND: [1,2,3]
      UNCHOOSE 3: current=[1,2], used={1,2}

    UNCHOOSE 2: current=[1], used={1}

    CHOOSE 3: current=[1,3], used={1,3}
    Call backtrack(current=[1,3], used={1,3})

      CHOOSE 2: current=[1,3,2], used={1,2,3}
      → SOLUTION FOUND: [1,3,2]
      UNCHOOSE 2: current=[1,3], used={1,3}

    UNCHOOSE 3: current=[1], used={1}

  UNCHOOSE 1: current=[], used={}

  CHOOSE 2: current=[2], used={2}
  ... (continues symmetrically)
```

**Notice**: The `used` set is modified in CHOOSE and restored in UNCHOOSE. The `current` array is similarly push/pop maintained. The STACK (implicit in the call sequence) shows us exactly where we are in the decision tree.

### 6.6 Implementation: Backtracking in Go, C, Rust

#### Go Implementation

```go
package main

import "fmt"

// ─────────────────────────────────────────────────────────────────────────────
// PERMUTATIONS — Classic backtracking with explicit state restoration
// State: current partial permutation, used[] flag array
// ─────────────────────────────────────────────────────────────────────────────

func permutations(nums []int) [][]int {
    results := [][]int{}
    used := make([]bool, len(nums)) // used[i] = true if nums[i] is in current path
    current := make([]int, 0, len(nums))

    var backtrack func()
    backtrack = func() {
        // Base case: current is a complete permutation
        if len(current) == len(nums) {
            // CRITICAL: copy the current state — don't store a reference!
            // If we store the slice directly, future modifications will corrupt it
            perm := make([]int, len(current))
            copy(perm, current)
            results = append(results, perm)
            return
        }

        for i := 0; i < len(nums); i++ {
            if used[i] {
                continue // PRUNE: already in current path
            }

            // ─── CHOOSE ───────────────────────────────────
            used[i] = true
            current = append(current, nums[i])

            // ─── EXPLORE ──────────────────────────────────
            backtrack()

            // ─── UNCHOOSE (state restoration) ─────────────
            current = current[:len(current)-1] // Pop last element
            used[i] = false
        }
    }

    backtrack()
    return results
}

// ─────────────────────────────────────────────────────────────────────────────
// N-QUEENS — Advanced state tracking with multiple constraints
// ─────────────────────────────────────────────────────────────────────────────

const N_QUEENS = 4

type QueensState struct {
    cols   [N_QUEENS]bool // cols[c] = true if column c is occupied
    diag1  [2*N_QUEENS]bool // diag1[r-c+N] = true (tracks \ diagonals)
    diag2  [2*N_QUEENS]bool // diag2[r+c]   = true (tracks / diagonals)
    board  [N_QUEENS]int    // board[r] = column of queen in row r
}

func solveNQueens() [][]string {
    var solutions [][]string
    var state QueensState

    var backtrack func(row int)
    backtrack = func(row int) {
        // Base case: all N rows have a queen placed
        if row == N_QUEENS {
            // Convert board state to string representation
            solution := make([]string, N_QUEENS)
            for r := 0; r < N_QUEENS; r++ {
                rowStr := make([]byte, N_QUEENS)
                for c := 0; c < N_QUEENS; c++ {
                    if state.board[r] == c {
                        rowStr[c] = 'Q'
                    } else {
                        rowStr[c] = '.'
                    }
                }
                solution[r] = string(rowStr)
            }
            solutions = append(solutions, solution)
            return
        }

        for col := 0; col < N_QUEENS; col++ {
            // Check all three constraints (prune invalid choices)
            d1 := row - col + N_QUEENS // Offset to make index non-negative
            d2 := row + col
            if state.cols[col] || state.diag1[d1] || state.diag2[d2] {
                continue // PRUNE: this position is attacked
            }

            // ─── CHOOSE ───────────────────────────────────
            state.board[row]  = col
            state.cols[col]   = true
            state.diag1[d1]   = true
            state.diag2[d2]   = true

            // ─── EXPLORE ──────────────────────────────────
            backtrack(row + 1)

            // ─── UNCHOOSE ─────────────────────────────────
            state.cols[col]   = false
            state.diag1[d1]   = false
            state.diag2[d2]   = false
            // Note: state.board[row] doesn't need explicit reset because
            // it will be overwritten before being read again
        }
    }

    backtrack(0)
    return solutions
}

// ─────────────────────────────────────────────────────────────────────────────
// SUBSETS — All subsets of a set (power set)
// Demonstrates the "include/exclude" decision pattern
// ─────────────────────────────────────────────────────────────────────────────

func subsets(nums []int) [][]int {
    results := [][]int{}
    current := []int{}

    var backtrack func(start int)
    backtrack = func(start int) {
        // EVERY state of current is a valid subset (not just base case!)
        perm := make([]int, len(current))
        copy(perm, current)
        results = append(results, perm)

        for i := start; i < len(nums); i++ {
            current = append(current, nums[i]) // CHOOSE
            backtrack(i + 1)                   // EXPLORE (i+1 prevents reuse)
            current = current[:len(current)-1] // UNCHOOSE
        }
    }

    backtrack(0)
    return results
}

func main() {
    // Permutations
    fmt.Println("=== PERMUTATIONS of [1,2,3] ===")
    perms := permutations([]int{1, 2, 3})
    for _, p := range perms {
        fmt.Println(p)
    }
    fmt.Printf("Total: %d permutations\n\n", len(perms))

    // N-Queens
    fmt.Printf("=== %d-QUEENS ===\n", N_QUEENS)
    solutions := solveNQueens()
    for i, sol := range solutions {
        fmt.Printf("Solution %d:\n", i+1)
        for _, row := range sol {
            fmt.Println(row)
        }
        fmt.Println()
    }

    // Subsets
    fmt.Println("=== SUBSETS of [1,2,3] ===")
    subs := subsets([]int{1, 2, 3})
    for _, s := range subs {
        fmt.Println(s)
    }
}
```

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

/* ─────────────────────────────────────────────────────────────────────────────
 * CONSTANTS
 * ───────────────────────────────────────────────────────────────────────────*/
#define MAX_N        8
#define MAX_RESULTS  10000
#define MAX_RESULT_LEN 64

/* ─────────────────────────────────────────────────────────────────────────────
 * PERMUTATIONS — Backtracking with explicit state restoration
 * ───────────────────────────────────────────────────────────────────────────*/
typedef struct {
    int data[MAX_N][MAX_N]; /* Stored permutations */
    int count;              /* How many found */
    int n;                  /* Length of each permutation */
} PermResults;

/* Recursive backtracking engine */
static void permute_helper(int *nums, int n,
                           bool *used,
                           int *current, int current_len,
                           PermResults *results)
{
    /* Base case: complete permutation found */
    if (current_len == n) {
        if (results->count < MAX_RESULTS) {
            memcpy(results->data[results->count], current, (size_t)n * sizeof(int));
            results->count++;
        }
        return;
    }

    for (int i = 0; i < n; i++) {
        if (used[i]) continue; /* PRUNE */

        /* ─── CHOOSE ──────────────────────────────────────────────── */
        used[i]                   = true;
        current[current_len]      = nums[i];

        /* ─── EXPLORE ─────────────────────────────────────────────── */
        permute_helper(nums, n, used, current, current_len + 1, results);

        /* ─── UNCHOOSE ────────────────────────────────────────────── */
        used[i] = false;
        /* current[current_len] doesn't need reset — overwritten next iteration */
    }
}

PermResults permutations(int *nums, int n) {
    PermResults results = { .count = 0, .n = n };
    bool used[MAX_N]    = { false };
    int  current[MAX_N] = { 0 };
    permute_helper(nums, n, used, current, 0, &results);
    return results;
}

/* ─────────────────────────────────────────────────────────────────────────────
 * N-QUEENS — Multi-constraint state tracking
 * State: cols[], diag1[], diag2[] boolean arrays
 * ───────────────────────────────────────────────────────────────────────────*/
#define QUEENS_N 4

typedef struct {
    char boards[MAX_RESULTS][QUEENS_N][QUEENS_N + 1]; /* +1 for '\0' */
    int  count;
} QueensResults;

static bool cols_used [QUEENS_N];              /* Shared mutable state */
static bool diag1_used[2 * QUEENS_N];         /* Tracks \ diagonals   */
static bool diag2_used[2 * QUEENS_N];         /* Tracks / diagonals   */
static int  board     [QUEENS_N];             /* board[r] = col of queen */

static void queens_helper(int row, QueensResults *results) {
    if (row == QUEENS_N) {
        if (results->count < MAX_RESULTS) {
            for (int r = 0; r < QUEENS_N; r++) {
                for (int c = 0; c < QUEENS_N; c++) {
                    results->boards[results->count][r][c] =
                        (board[r] == c) ? 'Q' : '.';
                }
                results->boards[results->count][r][QUEENS_N] = '\0';
            }
            results->count++;
        }
        return;
    }

    for (int col = 0; col < QUEENS_N; col++) {
        int d1 = row - col + QUEENS_N; /* Offset to prevent negative index */
        int d2 = row + col;

        if (cols_used[col] || diag1_used[d1] || diag2_used[d2]) {
            continue; /* PRUNE */
        }

        /* ─── CHOOSE ──────────────────────────────────────────────── */
        board[row]        = col;
        cols_used[col]    = true;
        diag1_used[d1]    = true;
        diag2_used[d2]    = true;

        /* ─── EXPLORE ─────────────────────────────────────────────── */
        queens_helper(row + 1, results);

        /* ─── UNCHOOSE ────────────────────────────────────────────── */
        cols_used[col]    = false;
        diag1_used[d1]    = false;
        diag2_used[d2]    = false;
    }
}

QueensResults solve_n_queens(void) {
    QueensResults results = { .count = 0 };
    memset(cols_used,  0, sizeof(cols_used));
    memset(diag1_used, 0, sizeof(diag1_used));
    memset(diag2_used, 0, sizeof(diag2_used));
    queens_helper(0, &results);
    return results;
}

/* ─────────────────────────────────────────────────────────────────────────────
 * MAIN
 * ───────────────────────────────────────────────────────────────────────────*/
int main(void) {
    /* Permutations of [1, 2, 3] */
    printf("=== PERMUTATIONS of [1,2,3] ===\n");
    int nums[] = {1, 2, 3};
    PermResults pr = permutations(nums, 3);
    for (int i = 0; i < pr.count; i++) {
        printf("[");
        for (int j = 0; j < pr.n; j++) {
            printf("%d%s", pr.data[i][j], (j + 1 < pr.n) ? ", " : "");
        }
        printf("]\n");
    }
    printf("Total: %d\n\n", pr.count);

    /* N-Queens */
    printf("=== %d-QUEENS ===\n", QUEENS_N);
    QueensResults qr = solve_n_queens();
    for (int i = 0; i < qr.count; i++) {
        printf("Solution %d:\n", i + 1);
        for (int r = 0; r < QUEENS_N; r++) {
            printf("%s\n", qr.boards[i][r]);
        }
        printf("\n");
    }

    return EXIT_SUCCESS;
}
```

#### Rust Implementation

```rust
//! Backtracking State Tracking — Rust
//! 
//! Rust's ownership model enforces correct state management:
//! - Mutable borrows (&mut) ensure exclusive state modification
//! - The borrow checker prevents state from being read while it's being modified
//! - No hidden state sharing between recursive calls

// ─────────────────────────────────────────────────────────────────────────────
// PERMUTATIONS — State tracked in `current` Vec and `used` Vec<bool>
// ─────────────────────────────────────────────────────────────────────────────

fn permutations(nums: &[i32]) -> Vec<Vec<i32>> {
    let n = nums.len();
    let mut results = Vec::new();
    let mut current = Vec::with_capacity(n);
    let mut used    = vec![false; n];

    fn backtrack(
        nums:    &[i32],
        current: &mut Vec<i32>,
        used:    &mut Vec<bool>,
        results: &mut Vec<Vec<i32>>,
    ) {
        if current.len() == nums.len() {
            results.push(current.clone()); // Snapshot the current state
            return;
        }

        for i in 0..nums.len() {
            if used[i] { continue; } // PRUNE

            // ─── CHOOSE ─────────────────────────────────────────────
            used[i] = true;
            current.push(nums[i]);

            // ─── EXPLORE ────────────────────────────────────────────
            backtrack(nums, current, used, results);

            // ─── UNCHOOSE ───────────────────────────────────────────
            current.pop();    // Exact inverse of push
            used[i] = false;  // Exact inverse of setting true
        }
    }

    backtrack(nums, &mut current, &mut used, &mut results);
    results
}

// ─────────────────────────────────────────────────────────────────────────────
// N-QUEENS
// ─────────────────────────────────────────────────────────────────────────────

const QUEENS_N: usize = 4;

fn solve_n_queens() -> Vec<Vec<String>> {
    let mut solutions = Vec::new();

    // All state is tracked in these three bool arrays + board
    let mut cols_used  = [false; QUEENS_N];
    let mut diag1_used = [false; 2 * QUEENS_N]; // row - col + N (\ diagonals)
    let mut diag2_used = [false; 2 * QUEENS_N]; // row + col     (/ diagonals)
    let mut board      = [0usize; QUEENS_N];     // board[r] = col of queen in row r

    fn backtrack(
        row:        usize,
        board:      &mut [usize; QUEENS_N],
        cols_used:  &mut [bool; QUEENS_N],
        diag1_used: &mut [bool; 2 * QUEENS_N],
        diag2_used: &mut [bool; 2 * QUEENS_N],
        solutions:  &mut Vec<Vec<String>>,
    ) {
        if row == QUEENS_N {
            // Convert board state to string
            let solution: Vec<String> = board
                .iter()
                .map(|&col| {
                    (0..QUEENS_N)
                        .map(|c| if c == col { 'Q' } else { '.' })
                        .collect()
                })
                .collect();
            solutions.push(solution);
            return;
        }

        for col in 0..QUEENS_N {
            let d1 = row + QUEENS_N - col; // Offset to prevent underflow
            let d2 = row + col;

            if cols_used[col] || diag1_used[d1] || diag2_used[d2] {
                continue; // PRUNE
            }

            // ─── CHOOSE ─────────────────────────────────────────────
            board[row]        = col;
            cols_used[col]    = true;
            diag1_used[d1]    = true;
            diag2_used[d2]    = true;

            // ─── EXPLORE ────────────────────────────────────────────
            backtrack(row + 1, board, cols_used, diag1_used, diag2_used, solutions);

            // ─── UNCHOOSE ───────────────────────────────────────────
            cols_used[col]    = false;
            diag1_used[d1]    = false;
            diag2_used[d2]    = false;
        }
    }

    backtrack(0, &mut board, &mut cols_used, &mut diag1_used, &mut diag2_used, &mut solutions);
    solutions
}

// ─────────────────────────────────────────────────────────────────────────────
// SUBSETS (Power Set) — Include/exclude decision at each element
// ─────────────────────────────────────────────────────────────────────────────

fn subsets(nums: &[i32]) -> Vec<Vec<i32>> {
    let mut results = Vec::new();
    let mut current = Vec::new();

    fn backtrack(nums: &[i32], start: usize, current: &mut Vec<i32>, results: &mut Vec<Vec<i32>>) {
        results.push(current.clone()); // Every partial state is a valid subset

        for i in start..nums.len() {
            current.push(nums[i]);     // CHOOSE
            backtrack(nums, i + 1, current, results); // EXPLORE
            current.pop();             // UNCHOOSE
        }
    }

    backtrack(nums, 0, &mut current, &mut results);
    results
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────────────────────

fn main() {
    // Permutations
    println!("=== PERMUTATIONS of [1,2,3] ===");
    let perms = permutations(&[1, 2, 3]);
    for p in &perms { println!("{:?}", p); }
    println!("Total: {}\n", perms.len());

    // N-Queens
    println!("=== {}-QUEENS ===", QUEENS_N);
    let solutions = solve_n_queens();
    for (i, sol) in solutions.iter().enumerate() {
        println!("Solution {}:", i + 1);
        for row in sol { println!("{}", row); }
        println!();
    }

    // Subsets
    println!("=== SUBSETS of [1,2,3] ===");
    let subs = subsets(&[1, 2, 3]);
    for s in &subs { println!("{:?}", s); }
    println!("Total: {} (should be 2^3=8)", subs.len());
}
```

---

## 7. Combined: Backtracking + DP (Path Reconstruction)

This is where mastery lies — understanding that DP computes *values* and backtracking through the DP table reconstructs the *path* (sequence of decisions) that achieved those values.

### The Pattern

```
Phase 1 — DP FORWARD PASS:
    Fill dp table from base cases to final state.
    Store ONLY values (or also decisions for faster reconstruction).

Phase 2 — BACKTRACKING BACKWARD PASS:
    Start at dp[final_state].
    At each state, ask: "What decision was made here?"
    Reconstruct by following the decision trail backward.
    Reverse the path at the end.
```

### Decision Storage Variants

**Variant A** — Recompute decisions during backtrack (simpler, uses existing dp table):
```
At state (i, j), check which neighbor it came from by testing transitions.
Slightly slower, but no extra memory.
```

**Variant B** — Store decisions in a `choice[][]` table during forward pass:
```
During forward pass: if taking item i was better, choice[i][w] = TAKE
During backward pass: just read choice[][] — O(n) reconstruction.
```

### Go Example: LCS Path Reconstruction with Decision Table

```go
package main

import "fmt"

// Decision types stored in the choice table
const (
    MATCH = iota // Characters matched — move diagonal
    SKIP1        // Skip from s1 (move up)
    SKIP2        // Skip from s2 (move left)
)

type LCSTracked struct {
    length int
    choice [][]int // decision at each state
}

func lcsWithChoices(s1, s2 string) (int, string) {
    m, n := len(s1), len(s2)

    dp     := make([][]int, m+1)
    choice := make([][]int, m+1)
    for i := range dp {
        dp[i]     = make([]int, n+1)
        choice[i] = make([]int, n+1)
    }

    // Forward pass: fill DP and record decisions
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                dp[i][j]     = dp[i-1][j-1] + 1
                choice[i][j] = MATCH
            } else if dp[i-1][j] >= dp[i][j-1] {
                dp[i][j]     = dp[i-1][j]
                choice[i][j] = SKIP1
            } else {
                dp[i][j]     = dp[i][j-1]
                choice[i][j] = SKIP2
            }
        }
    }

    // Backward pass: follow choice table (backtracking through DP)
    result := []byte{}
    i, j   := m, n
    for i > 0 && j > 0 {
        switch choice[i][j] {
        case MATCH:
            result = append(result, s1[i-1])
            i--; j--
        case SKIP1:
            i--
        case SKIP2:
            j--
        }
    }

    // Reverse
    for lo, hi := 0, len(result)-1; lo < hi; lo, hi = lo+1, hi-1 {
        result[lo], result[hi] = result[hi], result[lo]
    }

    return dp[m][n], string(result)
}

func main() {
    length, seq := lcsWithChoices("AGGTAB", "GXTXAYB")
    fmt.Printf("LCS length: %d, sequence: %s\n", length, seq)
    // LCS length: 4, sequence: GTAB
}
```

---

## 8. Debugging Techniques for State

When recursion/DP/backtracking breaks, these are your weapons.

### Technique 1: The State Logger

Add a logging function that prints the FULL state at each decision point:

```go
// Go: Instrument your backtracking
func debugState(label string, depth int, current []int, used []bool) {
    indent := strings.Repeat("  ", depth)
    fmt.Printf("%s[%s] current=%v, used=%v\n", indent, label, current, used)
}
```

### Technique 2: The Invariant Checker

An **invariant** is a condition that must ALWAYS be true. Check it before and after every modify operation:

```go
// After UNCHOOSE, verify state was correctly restored
func checkInvariant(expected, actual []int, msg string) {
    for i := range expected {
        if expected[i] != actual[i] {
            panic(fmt.Sprintf("INVARIANT VIOLATED at %s: expected %v, got %v",
                msg, expected, actual))
        }
    }
}
```

### Technique 3: Small Input Exhaustive Testing

Before running on n=100, verify your algorithm on n=3 where you can manually enumerate ALL answers and compare.

### Technique 4: DP Table Printing

Print the entire DP table after filling:

```go
func printDPTable(dp [][]int, s1, s2 string) {
    fmt.Printf("    \"\" ")
    for _, c := range s2 { fmt.Printf(" %c ", c) }
    fmt.Println()
    for i, row := range dp {
        if i == 0 { fmt.Printf("\"\" ") } else { fmt.Printf(" %c ", s1[i-1]) }
        for _, v := range row { fmt.Printf("%2d ", v) }
        fmt.Println()
    }
}
```

### Technique 5: The "What Should This Be?" Method

Before running code, manually compute what `dp[2][3]` should be. Then add an assertion:

```go
if dp[2][3] != expectedValue {
    panic(fmt.Sprintf("dp[2][3] expected %d, got %d", expectedValue, dp[2][3]))
}
```

### Technique 6: Recursion Depth Counter

Add a depth counter to detect stack overflows or infinite recursion early:

```go
const MAX_RECURSION_DEPTH = 1000

func backtrack(depth int, ...) {
    if depth > MAX_RECURSION_DEPTH {
        panic(fmt.Sprintf("recursion depth %d exceeded limit", depth))
    }
    // ...
}
```

---

## 9. Performance: Cache Behavior and Memory Reality

### Recursion Performance Reality

| Approach | Stack Usage | Cache Behavior | Function Call Overhead |
|----------|-------------|----------------|------------------------|
| Naive recursion | O(n) frames | Random (cache miss) | Yes (push/pop frame) |
| Memoized recursion | O(n) frames | Scattered (hash map) | Yes |
| Bottom-up DP | O(1) | Sequential (cache hit) | No |
| Space-opt DP | O(1) | Sequential, minimal | No |

**The Rule**: For performance-critical code, always prefer **bottom-up DP** over memoized recursion. The sequential memory access pattern of bottom-up DP is 5–50x faster in practice due to cache efficiency.

### Memory Allocation Pattern Comparison

```
RECURSIVE MEMO (HashMap):
- Each unique state = 1 hash map insertion = heap allocation
- HashMap has ~10ns overhead per lookup (hash computation + pointer chase)
- Cache unfriendly (hash buckets scattered in memory)

BOTTOM-UP TABLE (Array):
- One contiguous allocation: O(n*m) integers
- Array lookup = single pointer arithmetic = 1–4 CPU cycles
- Sequential access = stays in L1/L2 cache
```

### Backtracking Performance

Backtracking is exponential in the worst case, but **pruning** is what makes it practical.

**Pruning effectiveness** — for N-Queens:
- Without pruning: N^N states explored
- With column + diagonal pruning: ~O(N!) states
- With constraint propagation: much less

**Key insight**: Prune as EARLY as possible. A check at depth 1 eliminates an entire subtree. This is the "fail fast" principle.

### Rust-Specific: Stack vs Heap for Recursion State

In Rust, prefer keeping state on the stack when possible:
- Stack allocation: 0 CPU cycles (just decrement SP)
- Heap allocation (`Box::new`, `Vec::push`): ~10–50ns (system allocator)

For deep recursion with large local state, consider switching to an **explicit stack** (Vec as a stack) to avoid stack overflow and control memory layout.

---

## 10. The Expert's Toolkit: Mental Models That Compound

### Model 1: The State-Space Graph

Always ask: "What is my state space?" Draw it before coding.
- Recursion: nodes = (function, arguments), edges = recursive calls
- DP: nodes = sub-problems, edges = transitions
- Backtracking: nodes = partial solutions, edges = choices made

### Model 2: The Three Questions Before Coding

1. **What is the state?** (What variables completely describe where I am?)
2. **What are the transitions?** (How do I move from one state to another?)
3. **What is the base case?** (When do I stop transitioning?)

### Model 3: The "Last Step" Technique

For DP, think: "What was the LAST decision made to reach the optimal solution?"
- For LCS: was the last char matched or skipped?
- For Knapsack: was the last item taken or not?
This last decision defines your recurrence relation.

### Model 4: Chunking Complex State

Human working memory is limited (7±2 items). When state is complex, **chunk** related variables into a struct/record. Instead of tracking 6 separate boolean arrays for N-Queens, package them as a `QueensState` struct. Your mind handles 1 chunk instead of 6 separate items.

### Model 5: The "Undo Stack" Mental Model

Whenever you make a change that must be reversible, ask: "Am I pushing an operation onto an undo stack?" If yes, ensure your undo operation is the EXACT mathematical inverse:
- `push(x)` → undo with `pop()`
- `used[i] = true` → undo with `used[i] = false`
- `count += x` → undo with `count -= x`
- `path.add(node)` → undo with `path.remove(node)`

### Model 6: Deliberate Practice Protocol for These Topics

To master state tracking, use this protocol:
1. **Trace before you run**: For every new algorithm, manually trace 3–5 steps before executing
2. **Draw the state**: Use a table, grid, or tree on paper
3. **Instrument and verify**: Add print statements, run small cases, compare to manual trace
4. **Remove scaffolding**: Once confident, remove traces and run at scale
5. **Re-derive from scratch**: A week later, solve the same problem without looking at your solution

This follows the **spaced repetition** and **retrieval practice** principles of cognitive science — the most effective way to build long-term algorithmic intuition.

### The Monk's Summary

```
RECURSION:   "I am building a tower of frames.
              Each frame knows nothing of the others.
              Results flow UPWARD through return values."

DP:          "I am filling a table of truths.
              Each cell is a sub-problem.
              I never compute the same truth twice."

BACKTRACKING: "I am walking a forest of choices.
               When I step forward, I mark my path.
               When I step back, I erase my mark."
```

---

*This document is a living reference. Every time you solve a problem, return to the relevant section and ask: "Which model did I use? Did I track state systematically? What would the expert do differently?"*

---

**Complexity Quick Reference**

| Algorithm | Time (typical) | Space | State to Track |
|-----------|---------------|-------|----------------|
| Naive Recursion | O(branching^depth) | O(depth) | Call stack only |
| Memoized Recursion | O(unique states) | O(unique states) | Call stack + memo map |
| Bottom-up DP 1D | O(n) | O(n) or O(1) | DP array |
| Bottom-up DP 2D | O(n×m) | O(n×m) | 2D DP table |
| Backtracking | O(b^d) worst case | O(d) | current path + used set |
| Backtracking + Pruning | Much less in practice | O(d) | current path + constraint sets |

*b = branching factor, d = depth, n/m = problem dimensions*

Now I'll create the comprehensive guide as a `.md` file. This will be extensive and production-grade.Here is your complete mastery guide. Let me give you the **essential mental map** of what's inside:

---

## What This Guide Covers (Section by Section)

**Section 1–2: Foundation** — "State" is defined precisely as a *complete snapshot* of computation. You learn what physically happens on the CPU: stack frames, memory addresses, cache lines. This is the hardware reality most programmers never see.

**Section 3: Mental Models** — Five universal models (Photograph, Decision Tree, Undo Stack, Memo Cache, Wave Front) that apply across *all three* paradigms. Learn these deeply — they transfer everywhere.

**Section 4: Recursion** — You get the *Activation Frame* model (each call = its own isolated variable world), the three-phase framework (Descent → Base Case → Ascent), and a step-by-step **Execution Table** method you can use on paper. Full Fibonacci trace with stack snapshots at every time step. Tail recursion state model. Full implementations in Go, C, Rust.

**Section 5: Dynamic Programming** — "State" in DP is precisely defined as *what uniquely identifies a sub-problem*. You see the memo table evolving cell by cell (top-down), and the wave-front filling pattern (bottom-up). **LCS and Knapsack** are traced completely — every cell computed in order, with the backtracking path reconstructed.

**Section 6: Backtracking** — The **Choose-Explore-Unchoose (CEU)** template is the master pattern. N-Queens is traced with full state snapshots showing which constraint sets are modified and restored. The critical insight about *state restoration being the exact inverse of state modification* is hammered home.

**Section 7: Combined** — DP forward pass + backtracking backward pass. The `choice[][]` decision table pattern.

**Section 8: Debugging** — Six concrete techniques: state logger, invariant checker, small input testing, table printer, assertion method, depth counter.

**Section 9: Performance** — Why bottom-up DP is 5–50x faster than memoized recursion (cache locality), why pruning in backtracking is the difference between practical and impossible, Rust stack vs heap tradeoffs.

**Section 10: Expert Toolkit** — The Three Questions before every problem, the Last Step technique, cognitive chunking, the Monk's Summary.