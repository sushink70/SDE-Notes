# The Complete Guide to Constraint Handling in Systems Programming
## C · Go · Rust

> **Scope:** Every mechanism used to enforce, validate, and communicate constraints — from raw null checks to type-system invariants — across three systems languages with fundamentally different safety philosophies.

---

## Table of Contents

1. [Philosophy of Constraints](#1-philosophy-of-constraints)
2. [Null / Nil / None Checks — The Baseline Guard](#2-null--nil--none-checks--the-baseline-guard)
3. [Guard Clauses and Early Return](#3-guard-clauses-and-early-return)
4. [Assertions — Runtime Contract Verification](#4-assertions--runtime-contract-verification)
5. [Error Propagation Patterns](#5-error-propagation-patterns)
6. [Option and Result Types](#6-option-and-result-types)
7. [Boundary and Range Constraints](#7-boundary-and-range-constraints)
8. [Type System Constraints](#8-type-system-constraints)
9. [Ownership and Lifetime Constraints (Rust)](#9-ownership-and-lifetime-constraints-rust)
10. [Invariant Enforcement via Constructors](#10-invariant-enforcement-via-constructors)
11. [Panic vs. Recoverable Error — When to Use Each](#11-panic-vs-recoverable-error--when-to-use-each)
12. [Defensive Programming Patterns](#12-defensive-programming-patterns)
13. [Contract-Based Programming (Design by Contract)](#13-contract-based-programming-design-by-contract)
14. [Memory Safety Constraints](#14-memory-safety-constraints)
15. [Concurrency Constraints](#15-concurrency-constraints)
16. [Static Analysis and Compiler-Level Constraints](#16-static-analysis-and-compiler-level-constraints)
17. [Testing as Constraint Verification](#17-testing-as-constraint-verification)
18. [Summary: Decision Matrix](#18-summary-decision-matrix)

---

## 1. Philosophy of Constraints

A **constraint** is any rule that restricts the set of valid program states. Every bug is — at its root — a violated constraint that the program did not detect early enough. The earlier a violation is caught, the cheaper it is to fix:

```
Compile time  <  Program startup  <  First-call validation  <  Deep runtime  <  Production
(cheapest)                                                                     (most expensive)
```

The three languages occupy very different positions on the "trust vs. safety" spectrum:

| Language | Default Trust Level | Primary Safety Mechanism | Cost |
|----------|---------------------|--------------------------|------|
| **C** | Maximum trust | Manual discipline, runtime checks | Zero overhead but no safety net |
| **Go** | Moderate trust | Interface nil checks, explicit errors, `panic`/`recover` | Minimal runtime overhead |
| **Rust** | Minimum trust | Ownership, type system, `Option`/`Result` | Zero-cost abstractions at compile time |

Understanding *why* each language makes its choices is more important than memorising syntax.

---

## 2. Null / Nil / None Checks — The Baseline Guard

The null pointer is Tony Hoare's famous "billion dollar mistake." Each language handles it differently.

### 2.1 C — Manual Null Checks

In C, any pointer can be `NULL`. There is no language enforcement; discipline is entirely the programmer's responsibility.

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================
 * PATTERN 1: Simple null guard (the baseline you already know)
 * ============================================================ */
void traverse(BinaryNode *node) {
    if (node == NULL) return;           // Base constraint: do nothing on NULL
    traverse(node->left);
    printf("%d ", node->data);
    traverse(node->right);
}

/* ============================================================
 * PATTERN 2: Null check on allocation — fail fast
 * ============================================================
 * Never silently continue after a failed malloc.
 * Returning NULL silently propagates corrupt state upward. */
BinaryNode *new_node(int data) {
    BinaryNode *node = malloc(sizeof(BinaryNode));
    if (!node) {
        /* Option A: Abort with diagnostic (appropriate for CLI tools) */
        fprintf(stderr, "[FATAL] malloc failed at %s:%d\n", __FILE__, __LINE__);
        exit(EXIT_FAILURE);

        /* Option B: Return NULL and let caller decide (library code)
         * return NULL; */
    }
    node->data  = data;
    node->left  = NULL;     // Always initialise — uninitialised pointers are
    node->right = NULL;     // worse than NULL; they point to garbage.
    return node;
}

/* ============================================================
 * PATTERN 3: Function contracts via null checks on parameters
 * ============================================================
 * Every function that receives a pointer should document and
 * enforce its nullability contract. */
int tree_height(const BinaryNode *node) {
    /* Contract: returns -1 for NULL (empty tree has height -1) */
    if (node == NULL) return -1;

    int left_h  = tree_height(node->left);
    int right_h = tree_height(node->right);
    return 1 + (left_h > right_h ? left_h : right_h);
}

/* ============================================================
 * PATTERN 4: Checked pointer dereference helper macro
 * ============================================================
 * In production C, wrapping repetitive patterns in macros
 * reduces noise and enforces consistency. */
#define CHECK_NULL_RET(ptr, retval)         \
    do {                                    \
        if ((ptr) == NULL) {                \
            fprintf(stderr,                 \
                "NULL pointer: %s at %s:%d\n", \
                #ptr, __FILE__, __LINE__);  \
            return (retval);                \
        }                                   \
    } while (0)

/* Usage */
int safe_get_data(const BinaryNode *node) {
    CHECK_NULL_RET(node, -1);
    return node->data;
}

/* ============================================================
 * PATTERN 5: Sentinel values as an alternative to NULL
 * ============================================================
 * Sometimes you can design away NULL entirely by using
 * a sentinel node (common in doubly-linked list implementations). */
static BinaryNode SENTINEL = {.data = 0, .left = NULL, .right = NULL};
#define EMPTY &SENTINEL

int sentinel_height(const BinaryNode *node) {
    if (node == EMPTY) return -1;   // Check against sentinel, not NULL
    int l = sentinel_height(node->left);
    int r = sentinel_height(node->right);
    return 1 + (l > r ? l : r);
}
```

**Key rules for C null handling:**
- Initialise every pointer to `NULL` at declaration.
- Check *before* you dereference, not after the crash.
- Library code should return `NULL` on failure and document it; application code should abort.
- Use `const` to express read-only semantics and prevent accidental mutation.

---

### 2.2 Go — Nil Interfaces and the Nil Interface Pitfall

Go has `nil` for pointers, slices, maps, channels, functions, and interfaces. The most dangerous case is the **nil interface**, which is distinct from a nil concrete type inside an interface.

```go
package tree

import "fmt"

// BinaryNode represents a node in a binary tree.
type BinaryNode struct {
    Data  int
    Left  *BinaryNode
    Right *BinaryNode
}

// NewNode allocates and initialises a node.
// Go convention: return (value, error) — never silently return nil.
func NewNode(data int) *BinaryNode {
    return &BinaryNode{Data: data} // Left/Right are zero-valued (nil)
}

// ============================================================
// PATTERN 1: Nil receiver — Go's elegant safe recursion
// ============================================================
// Methods can be called on nil receivers. This is idiomatic
// and avoids explicit nil checks at call sites.
func (n *BinaryNode) Inorder() {
    if n == nil {
        return // The nil check lives inside the method, not at every call site
    }
    n.Left.Inorder()   // Safe: calls nil.Inorder() which returns immediately
    fmt.Printf("%d ", n.Data)
    n.Right.Inorder()
}

func (n *BinaryNode) Height() int {
    if n == nil {
        return -1
    }
    l, r := n.Left.Height(), n.Right.Height()
    if l > r {
        return l + 1
    }
    return r + 1
}

// ============================================================
// PATTERN 2: The nil interface trap
// ============================================================
// This is Go's most subtle constraint violation.
// A non-nil interface value can hold a nil concrete pointer,
// which causes a panic on method dispatch.

type Traversable interface {
    Inorder()
}

func badFactory(useTree bool) Traversable {
    var n *BinaryNode // n is a typed nil pointer

    if useTree {
        n = NewNode(42)
    }
    // BUG: Returns a non-nil interface wrapping a nil *BinaryNode.
    // Callers doing `if result != nil` will not catch this.
    return n // interface{type=*BinaryNode, value=nil} != nil interface
}

func goodFactory(useTree bool) Traversable {
    if useTree {
        return NewNode(42)
    }
    return nil // Returns a true nil interface
}

// Safe consumer pattern — always check before calling
func useTree(t Traversable) {
    if t == nil {
        fmt.Println("no tree provided")
        return
    }
    t.Inorder()
}

// ============================================================
// PATTERN 3: Optional values via pointer semantics
// ============================================================
// Go lacks an Option<T> type. Use *T as "optional T".
type Config struct {
    MaxDepth *int // nil means "use default"
    Name     string
}

func buildTree(cfg Config) *BinaryNode {
    depth := 3 // default
    if cfg.MaxDepth != nil {
        depth = *cfg.MaxDepth // safe dereference after nil check
    }
    _ = depth
    return NewNode(1)
}

// ============================================================
// PATTERN 4: Zero-value safety by design
// ============================================================
// Go's zero values allow structs to be usable without explicit init.
// Design your types so the zero value is valid.
type SafeTree struct {
    root *BinaryNode
    size int // zero value 0 is correct for an empty tree
}

func (t *SafeTree) Insert(data int) {
    // No nil check needed on t — methods on nil struct pointers
    // work as long as you don't dereference t (but caller should not pass nil here)
    t.root = insertBST(t.root, data)
    t.size++
}

func insertBST(node *BinaryNode, data int) *BinaryNode {
    if node == nil {
        return NewNode(data)
    }
    if data < node.Data {
        node.Left = insertBST(node.Left, data)
    } else if data > node.Data {
        node.Right = insertBST(node.Right, data)
    }
    return node
}
```

---

### 2.3 Rust — Option<T>: Making Nullability a Type

Rust eliminates null pointers entirely. The absence of a value is represented by `Option<T>`, a sum type in the standard library. You **cannot** dereference an optional value without explicitly handling the None case — the compiler enforces this.

```rust
use std::fmt;

// ============================================================
// Tree definition — Box<T> for heap-allocated recursive types
// ============================================================
#[derive(Debug)]
pub struct BinaryNode {
    pub data:  i32,
    pub left:  Option<Box<BinaryNode>>,
    pub right: Option<Box<BinaryNode>>,
}

impl BinaryNode {
    pub fn new(data: i32) -> Self {
        BinaryNode { data, left: None, right: None }
    }

    // ============================================================
    // PATTERN 1: Pattern matching — exhaustive by definition
    // ============================================================
    // The compiler forces you to handle both Some and None.
    pub fn height(&self) -> i32 {
        let left_h = match &self.left {
            Some(node) => node.height(),
            None       => -1,
        };
        let right_h = match &self.right {
            Some(node) => node.height(),
            None       => -1,
        };
        1 + left_h.max(right_h)
    }

    // ============================================================
    // PATTERN 2: if let — sugar for single-arm match
    // ============================================================
    pub fn print_left(&self) {
        if let Some(left) = &self.left {
            println!("Left child: {}", left.data);
        } else {
            println!("No left child");
        }
    }

    // ============================================================
    // PATTERN 3: Option combinators — functional style
    // ============================================================
    // map, and_then, unwrap_or, unwrap_or_else, filter, etc.
    pub fn left_data(&self) -> i32 {
        self.left
            .as_ref()                       // Option<Box<T>> → Option<&Box<T>>
            .map(|node| node.data)          // Option<&Box<T>> → Option<i32>
            .unwrap_or(-1)                  // i32 (with default)
    }

    // ============================================================
    // PATTERN 4: ? operator for early return of None
    // ============================================================
    // Returns Option<i32>: Some(data) if left-left exists, None otherwise.
    pub fn left_left_data(&self) -> Option<i32> {
        let ll = self.left.as_ref()?.left.as_ref()?;
        Some(ll.data)
        // The ? operator short-circuits: returns None if any step is None.
    }

    // ============================================================
    // PATTERN 5: Inorder traversal with Option
    // ============================================================
    pub fn inorder(&self, result: &mut Vec<i32>) {
        if let Some(left) = &self.left {
            left.inorder(result);
        }
        result.push(self.data);
        if let Some(right) = &self.right {
            right.inorder(result);
        }
    }
}

// ============================================================
// PATTERN 6: Option in public APIs — constructors that can fail
// ============================================================
pub fn find(root: &Option<Box<BinaryNode>>, target: i32) -> Option<&BinaryNode> {
    let node = root.as_ref()?;       // Unwrap or return None
    match target.cmp(&node.data) {
        std::cmp::Ordering::Equal   => Some(node),
        std::cmp::Ordering::Less    => find(&node.left, target),
        std::cmp::Ordering::Greater => find(&node.right, target),
    }
}

// ============================================================
// PATTERN 7: unwrap() — when and why NOT to use it in production
// ============================================================
fn demo_unwrap_danger() {
    let opt: Option<i32> = None;

    // These will PANIC at runtime — only use in tests or
    // when you have a logical guarantee the value exists:
    // let _ = opt.unwrap();
    // let _ = opt.expect("should always have a value here");

    // PRODUCTION-SAFE alternatives:
    let _ = opt.unwrap_or(0);                           // static default
    let _ = opt.unwrap_or_default();                    // type's Default value
    let _ = opt.unwrap_or_else(|| expensive_default()); // lazy default
}

fn expensive_default() -> i32 { 42 }
```

---

## 3. Guard Clauses and Early Return

Guard clauses are the single most effective structural pattern for reducing constraint-related bugs. They invert nested `if-else` into flat, readable code where violations exit immediately.

### The Anti-Pattern: Arrow Code

```c
/* BAD — deeply nested, hard to reason about invariants */
int process_node(BinaryNode *node, int *out) {
    if (node != NULL) {
        if (out != NULL) {
            if (node->data > 0) {
                if (node->data < INT_MAX) {
                    *out = node->data * 2;
                    return 0;
                }
            }
        }
    }
    return -1;
}
```

### 3.1 C — Guard Clauses via Early Return

```c
#include <limits.h>
#include <errno.h>

/* GOOD — each guard expresses a distinct precondition */
int process_node(BinaryNode *node, int *out) {
    /* Precondition: inputs must not be NULL */
    if (node == NULL || out == NULL) {
        errno = EINVAL;
        return -1;
    }

    /* Precondition: data must be positive */
    if (node->data <= 0) {
        errno = ERANGE;
        return -1;
    }

    /* Precondition: result must not overflow */
    if (node->data > INT_MAX / 2) {
        errno = EOVERFLOW;
        return -1;
    }

    /* Happy path — only reachable if all constraints satisfied */
    *out = node->data * 2;
    return 0;
}

/* ============================================================
 * Guard clause on resource acquisition (RAII equivalent in C)
 * ============================================================ */
int write_tree_to_file(BinaryNode *root, const char *path) {
    if (root == NULL) return -1;    // Guard: non-null tree
    if (path == NULL) return -1;    // Guard: non-null path

    FILE *f = fopen(path, "w");
    if (f == NULL) return -1;       // Guard: file opened successfully

    /* All guards passed — work begins */
    /* ... write tree ... */

    fclose(f);  // Cleanup always happens (or use goto-cleanup pattern)
    return 0;
}

/* ============================================================
 * goto-cleanup pattern — C's structured resource release
 * ============================================================
 * When multiple resources need cleanup, goto is the idiomatic C approach.
 * It avoids duplicated cleanup code while keeping guards flat. */
int complex_operation(const char *input_path, const char *output_path) {
    int   result    = -1;
    FILE *input     = NULL;
    FILE *output    = NULL;
    char *buffer    = NULL;

    if (!input_path || !output_path) goto cleanup;

    input = fopen(input_path, "r");
    if (!input) goto cleanup;

    output = fopen(output_path, "w");
    if (!output) goto cleanup;

    buffer = malloc(4096);
    if (!buffer) goto cleanup;

    /* Work */
    result = 0;  // Mark success

cleanup:
    free(buffer);
    if (output) fclose(output);
    if (input)  fclose(input);
    return result;
}
```

### 3.2 Go — Guard Clauses with Idiomatic Error Returns

```go
package tree

import (
    "errors"
    "fmt"
    "math"
)

// Sentinel errors — declare once, compare with errors.Is()
var (
    ErrNilNode    = errors.New("tree: nil node")
    ErrNilOutput  = errors.New("tree: nil output parameter")
    ErrNegative   = errors.New("tree: data must be positive")
    ErrOverflow   = errors.New("tree: result would overflow int")
)

// ProcessNode demonstrates guard clauses in Go.
// Go convention: error is the last return value.
func ProcessNode(node *BinaryNode, out *int) error {
    // Guard clauses — each handles exactly one precondition violation
    if node == nil {
        return ErrNilNode
    }
    if out == nil {
        return ErrNilOutput
    }
    if node.Data <= 0 {
        return fmt.Errorf("processNode: %w (got %d)", ErrNegative, node.Data)
    }
    if node.Data > math.MaxInt/2 {
        return fmt.Errorf("processNode: %w (data=%d)", ErrOverflow, node.Data)
    }

    // Happy path
    *out = node.Data * 2
    return nil
}

// ============================================================
// Guard clauses with multiple return values
// ============================================================
func SafeDivide(a, b int) (int, error) {
    if b == 0 {
        return 0, fmt.Errorf("safeDivide: division by zero (a=%d)", a)
    }
    return a / b, nil
}

// ============================================================
// Guard clauses for struct method receivers
// ============================================================
// Go allows methods on nil receivers — be explicit about your contract.
func (t *SafeTree) Find(data int) (*BinaryNode, error) {
    if t == nil {
        return nil, errors.New("find: called on nil tree")
    }
    if t.root == nil {
        return nil, nil // Empty tree — not an error, but no result
    }
    return findBST(t.root, data), nil
}

func findBST(node *BinaryNode, data int) *BinaryNode {
    if node == nil {
        return nil
    }
    switch {
    case data == node.Data:
        return node
    case data < node.Data:
        return findBST(node.Left, data)
    default:
        return findBST(node.Right, data)
    }
}
```

### 3.3 Rust — Guard Clauses with ? and Type Safety

```rust
use std::num::TryFromIntError;

#[derive(Debug, thiserror::Error)]  // thiserror crate for ergonomic errors
pub enum TreeError {
    #[error("node data must be positive, got {0}")]
    NegativeData(i32),
    #[error("result would overflow i32")]
    Overflow,
    #[error("tree is empty")]
    EmptyTree,
    #[error("value {0} not found in tree")]
    NotFound(i32),
}

// ============================================================
// PATTERN: Guard clauses using Result<T, E>
// ============================================================
pub fn process_node(node: &BinaryNode) -> Result<i32, TreeError> {
    // Guard: positive data
    if node.data <= 0 {
        return Err(TreeError::NegativeData(node.data));
    }

    // Guard: no overflow — using checked arithmetic
    node.data
        .checked_mul(2)
        .ok_or(TreeError::Overflow)
    // Returns Ok(result) or Err(TreeError::Overflow)
}

// ============================================================
// PATTERN: ? operator as guard clause for early return
// ============================================================
pub fn double_left_data(root: &BinaryNode) -> Result<i32, TreeError> {
    let left = root.left.as_ref().ok_or(TreeError::EmptyTree)?;  // Guard: left exists
    let doubled = left.data.checked_mul(2).ok_or(TreeError::Overflow)?; // Guard: no overflow
    Ok(doubled)
    // Each ? is a guard: if the preceding expression is Err/None, return immediately.
}

// ============================================================
// PATTERN: Panicking guards for truly unrecoverable preconditions
// ============================================================
// Use assert! / assert_eq! / unreachable! / panic! for
// programming errors (not expected runtime failures).
pub fn insert_sorted(sorted_vec: &mut Vec<i32>, value: i32) {
    assert!(
        sorted_vec.windows(2).all(|w| w[0] <= w[1]),
        "insert_sorted: precondition violated — input is not sorted: {:?}",
        sorted_vec
    );
    let pos = sorted_vec.partition_point(|&x| x <= value);
    sorted_vec.insert(pos, value);
}

// ============================================================
// PATTERN: debug_assert! — guards only in debug builds
// ============================================================
// Zero cost in release builds. Use for expensive invariant checks.
pub fn heavy_tree_operation(node: &BinaryNode) -> i32 {
    debug_assert!(
        is_valid_bst(node, i32::MIN, i32::MAX),
        "heavy_tree_operation: BST invariant violated"
    );
    node.data // ... actual work ...
}

fn is_valid_bst(node: &BinaryNode, min: i32, max: i32) -> bool {
    node.data > min && node.data < max
        && node.left.as_ref().map_or(true,  |l| is_valid_bst(l, min, node.data))
        && node.right.as_ref().map_or(true, |r| is_valid_bst(r, node.data, max))
}
```

---

## 4. Assertions — Runtime Contract Verification

Assertions verify **invariants that must never be false if the code is correct**. They are not for handling expected failures (use errors for that) — they are for detecting *bugs in your own code*.

### 4.1 C — assert.h and Custom Assertions

```c
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

/* ============================================================
 * Standard assert — disabled by defining NDEBUG
 * ============================================================ */
void merge_sorted(int *a, int n, int *b, int m, int *out) {
    assert(a   != NULL);   // Precondition
    assert(b   != NULL);
    assert(out != NULL);
    assert(n   >= 0);
    assert(m   >= 0);

    /* Verify sorted invariant in debug builds */
    for (int i = 0; i < n - 1; i++) assert(a[i] <= a[i+1]);
    for (int i = 0; i < m - 1; i++) assert(b[i] <= b[i+1]);

    int i = 0, j = 0, k = 0;
    while (i < n && j < m) {
        out[k++] = (a[i] <= b[j]) ? a[i++] : b[j++];
    }
    while (i < n) out[k++] = a[i++];
    while (j < m) out[k++] = b[j++];

    /* Postcondition */
    for (int x = 0; x < n + m - 1; x++) assert(out[x] <= out[x+1]);
}

/* ============================================================
 * Custom assertion macro with context
 * ============================================================ */
#define ASSERT(cond, msg)                                              \
    do {                                                               \
        if (!(cond)) {                                                 \
            fprintf(stderr,                                            \
                "[ASSERT FAILED] %s\n  Condition: %s\n  File: %s\n  Line: %d\n", \
                (msg), #cond, __FILE__, __LINE__);                     \
            abort();                                                   \
        }                                                              \
    } while (0)

/* ============================================================
 * Static assertions — compile-time constraints
 * ============================================================ */
_Static_assert(sizeof(int) >= 4, "int must be at least 32 bits");
_Static_assert(sizeof(void*) == 8, "This code requires 64-bit pointers");

typedef struct {
    char magic[4];
    int  version;
} FileHeader;

_Static_assert(sizeof(FileHeader) == 8, "FileHeader must be exactly 8 bytes (check padding)");

/* ============================================================
 * Defensive invariant check function (useful for complex structs)
 * ============================================================ */
typedef struct {
    int  *data;
    int   size;
    int   capacity;
} DynArray;

void dynarray_check_invariants(const DynArray *a) {
#ifndef NDEBUG
    ASSERT(a != NULL,           "DynArray pointer must not be NULL");
    ASSERT(a->size >= 0,        "size must be non-negative");
    ASSERT(a->capacity >= 0,    "capacity must be non-negative");
    ASSERT(a->size <= a->capacity, "size must not exceed capacity");
    ASSERT(a->capacity == 0 || a->data != NULL,
           "data must not be NULL when capacity > 0");
#endif
}
```

### 4.2 Go — Panic as Assertion

Go has no `assert` keyword. The idiomatic equivalent is a targeted `panic` for programmer errors.

```go
package tree

import "fmt"

// ============================================================
// PATTERN: Custom assert function
// ============================================================
func assert(condition bool, format string, args ...any) {
    if !condition {
        panic(fmt.Sprintf("[ASSERT FAILED] "+format, args...))
    }
}

// mergeSorted demonstrates assertion-as-documentation.
func mergeSorted(a, b []int) []int {
    // Preconditions — these are programmer errors, not caller errors
    assert(isSorted(a), "mergeSorted: first argument is not sorted: %v", a)
    assert(isSorted(b), "mergeSorted: second argument is not sorted: %v", b)

    result := make([]int, 0, len(a)+len(b))
    i, j := 0, 0
    for i < len(a) && j < len(b) {
        if a[i] <= b[j] {
            result = append(result, a[i]); i++
        } else {
            result = append(result, b[j]); j++
        }
    }
    result = append(result, a[i:]...)
    result = append(result, b[j:]...)

    // Postcondition
    assert(isSorted(result), "mergeSorted: postcondition violated — result not sorted")
    return result
}

func isSorted(s []int) bool {
    for i := 1; i < len(s); i++ {
        if s[i] < s[i-1] {
            return false
        }
    }
    return true
}

// ============================================================
// PATTERN: Invariant checker as a method
// ============================================================
type SafeTree struct {
    root *BinaryNode
    size int
}

func (t *SafeTree) checkInvariants() {
    if t == nil {
        panic("checkInvariants: called on nil SafeTree")
    }
    count := countNodes(t.root)
    if count != t.size {
        panic(fmt.Sprintf(
            "SafeTree invariant violated: size field=%d but actual count=%d",
            t.size, count,
        ))
    }
}

func countNodes(n *BinaryNode) int {
    if n == nil { return 0 }
    return 1 + countNodes(n.Left) + countNodes(n.Right)
}
```

### 4.3 Rust — assert!, debug_assert!, and Static Assertions

```rust
// ============================================================
// assert! — always active (debug and release)
// debug_assert! — only active in debug builds (zero cost in release)
// ============================================================
fn merge_sorted(a: &[i32], b: &[i32]) -> Vec<i32> {
    // Preconditions — programmer errors, always check
    assert!(a.windows(2).all(|w| w[0] <= w[1]), "a must be sorted: {:?}", a);
    assert!(b.windows(2).all(|w| w[0] <= w[1]), "b must be sorted: {:?}", b);

    let mut result = Vec::with_capacity(a.len() + b.len());
    let (mut i, mut j) = (0, 0);

    while i < a.len() && j < b.len() {
        if a[i] <= b[j] { result.push(a[i]); i += 1; }
        else             { result.push(b[j]); j += 1; }
    }
    result.extend_from_slice(&a[i..]);
    result.extend_from_slice(&b[j..]);

    // Postcondition — expensive check only in debug
    debug_assert!(
        result.windows(2).all(|w| w[0] <= w[1]),
        "merge_sorted postcondition violated"
    );
    result
}

// ============================================================
// Static (compile-time) assertions
// ============================================================
const _: () = assert!(std::mem::size_of::<u32>() == 4, "u32 must be 4 bytes");
const _: () = assert!(std::mem::size_of::<usize>() >= 4, "usize must be at least 32 bits");

// Using static_assertions crate for richer compile-time checks:
// static_assertions::assert_eq_size!(u32, i32);
// static_assertions::assert_impl_all!(String: Send, Sync);

// ============================================================
// unreachable! — assert that a code path cannot be reached
// ============================================================
pub fn classify(x: i32) -> &'static str {
    match x.cmp(&0) {
        std::cmp::Ordering::Less    => "negative",
        std::cmp::Ordering::Equal   => "zero",
        std::cmp::Ordering::Greater => "positive",
        // The compiler knows this is exhaustive, but if you extend
        // a non-exhaustive enum:
        // _ => unreachable!("unexpected ordering variant"),
    }
}

// ============================================================
// todo! and unimplemented! — soft constraint markers
// ============================================================
pub fn future_feature() -> i32 {
    todo!("implement balanced tree rotation")
    // Compiles, but panics with a clear message if called
}

pub fn not_supported() -> i32 {
    unimplemented!("this method is not applicable to this tree type")
}
```

---

## 5. Error Propagation Patterns

How errors flow through a call stack is itself a constraint design decision. Poor propagation obscures root causes; good propagation maintains the original context.

### 5.1 C — Return Codes and errno

```c
#include <errno.h>
#include <string.h>

/* ============================================================
 * PATTERN 1: Integer return code (POSIX style)
 * ============================================================
 * 0 = success, negative = error code */
typedef enum {
    TREE_OK         =  0,
    TREE_ERR_NULL   = -1,
    TREE_ERR_NOENT  = -2,
    TREE_ERR_RANGE  = -3,
    TREE_ERR_MEM    = -4,
} TreeResult;

const char *tree_strerror(TreeResult err) {
    switch (err) {
        case TREE_OK:        return "success";
        case TREE_ERR_NULL:  return "null pointer";
        case TREE_ERR_NOENT: return "not found";
        case TREE_ERR_RANGE: return "value out of range";
        case TREE_ERR_MEM:   return "memory allocation failure";
        default:             return "unknown error";
    }
}

/* ============================================================
 * PATTERN 2: Output parameter for richer errors
 * ============================================================ */
typedef struct {
    int  code;
    char message[128];
    char file[64];
    int  line;
} Error;

#define MAKE_ERROR(e, code, msg) do {          \
    (e)->code = (code);                        \
    strncpy((e)->message, (msg), 127);         \
    strncpy((e)->file, __FILE__, 63);          \
    (e)->line = __LINE__;                      \
} while(0)

TreeResult insert_bst(BinaryNode **root, int data, Error *err) {
    if (root == NULL) {
        MAKE_ERROR(err, TREE_ERR_NULL, "root pointer is NULL");
        return TREE_ERR_NULL;
    }
    if (data < INT_MIN/2 || data > INT_MAX/2) {
        MAKE_ERROR(err, TREE_ERR_RANGE, "data out of safe range");
        return TREE_ERR_RANGE;
    }
    BinaryNode *node = malloc(sizeof(BinaryNode));
    if (!node) {
        MAKE_ERROR(err, TREE_ERR_MEM, "malloc failed");
        return TREE_ERR_MEM;
    }
    node->data  = data;
    node->left  = node->right = NULL;
    /* BST insert logic omitted for brevity */
    return TREE_OK;
}
```

### 5.2 Go — Wrapping Errors with Context

```go
package tree

import (
    "errors"
    "fmt"
)

// ============================================================
// PATTERN 1: Custom error types carry structured data
// ============================================================
type TreeError struct {
    Op      string // operation that failed
    Data    int    // relevant data value
    Wrapped error  // underlying cause
}

func (e *TreeError) Error() string {
    if e.Wrapped != nil {
        return fmt.Sprintf("tree.%s(data=%d): %v", e.Op, e.Data, e.Wrapped)
    }
    return fmt.Sprintf("tree.%s(data=%d): unknown error", e.Op, e.Data)
}

func (e *TreeError) Unwrap() error { return e.Wrapped }

// Sentinel errors for errors.Is() comparisons
var ErrNotFound = errors.New("not found")
var ErrDuplicate = errors.New("duplicate value")

// ============================================================
// PATTERN 2: Error wrapping with fmt.Errorf %w
// ============================================================
func (t *SafeTree) InsertChecked(data int) error {
    if t == nil {
        return fmt.Errorf("SafeTree.Insert: %w", ErrNilNode)
    }
    if data < -1000 || data > 1000 {
        return &TreeError{Op: "Insert", Data: data,
            Wrapped: fmt.Errorf("data %d out of range [-1000, 1000]", data)}
    }
    // Propagate error from lower level with added context
    if err := validateBSTInvariant(t.root, data); err != nil {
        return fmt.Errorf("SafeTree.Insert(data=%d): %w", data, err)
    }
    t.root = insertBST(t.root, data)
    t.size++
    return nil
}

func validateBSTInvariant(node *BinaryNode, data int) error {
    if node == nil { return nil }
    if data == node.Data {
        return fmt.Errorf("%w: %d already exists", ErrDuplicate, data)
    }
    return nil
}

// ============================================================
// PATTERN 3: errors.Is and errors.As for type-safe error handling
// ============================================================
func handleInsertError(err error) {
    if err == nil {
        return
    }
    // Check for a specific sentinel error anywhere in the chain
    if errors.Is(err, ErrDuplicate) {
        fmt.Println("Ignoring duplicate insert")
        return
    }
    // Extract a specific concrete error type from the chain
    var te *TreeError
    if errors.As(err, &te) {
        fmt.Printf("Tree operation %q failed on data %d\n", te.Op, te.Data)
        return
    }
    // Fallback
    fmt.Printf("Unexpected error: %v\n", err)
}
```

### 5.3 Rust — Result<T, E> and the ? Operator

```rust
use std::fmt;

// ============================================================
// PATTERN 1: Rich error types with thiserror
// ============================================================
#[derive(Debug, thiserror::Error)]
pub enum TreeError {
    #[error("node data {data} out of range [{min}, {max}]")]
    OutOfRange { data: i32, min: i32, max: i32 },

    #[error("value {0} not found in tree")]
    NotFound(i32),

    #[error("duplicate value {0}")]
    Duplicate(i32),

    #[error("allocation error: {0}")]
    Alloc(#[from] std::collections::TryReserveError),

    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
}

// ============================================================
// PATTERN 2: ? for clean propagation
// ============================================================
pub fn insert_validated(
    root: &mut Option<Box<BinaryNode>>,
    data: i32,
) -> Result<(), TreeError> {
    // Validate first — all constraints up front
    if data < -1000 || data > 1000 {
        return Err(TreeError::OutOfRange { data, min: -1000, max: 1000 });
    }
    if find(root, data).is_some() {
        return Err(TreeError::Duplicate(data));
    }
    *root = Some(Box::new(BinaryNode::new(data)));
    Ok(())
}

// ============================================================
// PATTERN 3: Chaining Results with map_err for context
// ============================================================
use std::fs;
use std::path::Path;

pub fn load_tree_from_file(path: &Path) -> Result<BinaryNode, TreeError> {
    let content = fs::read_to_string(path)   // Result<String, io::Error>
        .map_err(TreeError::Io)?;            // Convert io::Error → TreeError::Io

    let data: i32 = content.trim()
        .parse()
        .map_err(|_| TreeError::NotFound(0))?; // or a parse error variant

    Ok(BinaryNode::new(data))
}

// ============================================================
// PATTERN 4: collect::<Result<Vec<_>, _>>() — fail-fast over iterators
// ============================================================
pub fn insert_many(
    root: &mut Option<Box<BinaryNode>>,
    values: &[i32],
) -> Result<(), TreeError> {
    // This fails on the FIRST error and returns it immediately.
    values.iter()
          .map(|&v| insert_validated(root, v))
          .collect::<Result<Vec<_>, _>>()?;
    Ok(())
}

// ============================================================
// PATTERN 5: anyhow for application-level error handling
// ============================================================
// In binary crates (not libraries), anyhow::Result is ergonomic:
//
// use anyhow::{Result, Context, bail, ensure};
//
// fn run() -> Result<()> {
//     let data = fs::read_to_string("tree.txt")
//         .context("failed to read tree.txt")?;
//     ensure!(!data.is_empty(), "tree file is empty");
//     Ok(())
// }
```

---

## 6. Option and Result Types

These are foundational to constraint handling in modern systems programming.

### 6.1 Go — Emulating Option with Pointers and ok-idiom

```go
package tree

// ============================================================
// The ok-idiom: multi-return (value, bool) as Option<T>
// ============================================================
func (t *SafeTree) FindMin() (int, bool) {
    if t.root == nil {
        return 0, false // No value, not ok
    }
    node := t.root
    for node.Left != nil {
        node = node.Left
    }
    return node.Data, true // Value exists, ok
}

// Consumer — must handle both cases
func printMin(t *SafeTree) {
    if min, ok := t.FindMin(); ok {
        fmt.Printf("Minimum: %d\n", min)
    } else {
        fmt.Println("Tree is empty")
    }
}

// ============================================================
// Generic Option using Go 1.18+ generics
// ============================================================
type Option[T any] struct {
    value  T
    hasVal bool
}

func Some[T any](v T) Option[T]    { return Option[T]{value: v, hasVal: true} }
func None[T any]() Option[T]       { return Option[T]{} }
func (o Option[T]) IsSome() bool   { return o.hasVal }
func (o Option[T]) IsNone() bool   { return !o.hasVal }

func (o Option[T]) Unwrap() T {
    if !o.hasVal {
        panic("Option.Unwrap: called on None value")
    }
    return o.value
}

func (o Option[T]) UnwrapOr(def T) T {
    if o.hasVal { return o.value }
    return def
}

// ============================================================
// Generic Result type
// ============================================================
type Result[T any] struct {
    value T
    err   error
}

func Ok[T any](v T) Result[T]   { return Result[T]{value: v} }
func Err[T any](e error) Result[T] { return Result[T]{err: e} }
func (r Result[T]) IsOk() bool  { return r.err == nil }

func (r Result[T]) Unwrap() (T, error) {
    return r.value, r.err
}
```

### 6.2 Rust — Deep Dive into Option and Result Combinators

```rust
// ============================================================
// Option<T> combinator reference
// ============================================================
fn option_combinators(node: Option<Box<BinaryNode>>) {
    // --- Querying ---
    let _ = node.is_some();                      // bool
    let _ = node.is_none();                      // bool

    // --- Extracting (safe) ---
    let _ = node.as_ref();                       // Option<&BinaryNode>
    let _ = node.as_deref();                     // Option<&BinaryNode> (if Deref)

    // --- Transforming ---
    let _ = node.as_ref().map(|n| n.data);       // Option<i32>
    let _ = node.as_ref().filter(|n| n.data > 0);// Option<&Box<BinaryNode>>
    let _ = node.as_ref().and_then(|n| n.left.as_ref()); // Option<&Box<BinaryNode>>

    // --- Defaulting ---
    let default_node = BinaryNode::new(0);
    let _ = node.as_ref().unwrap_or(&default_node);
    let _ = node.as_ref().unwrap_or_else(|| &default_node);
    let _ = node.as_ref().unwrap_or_default(); // Requires BinaryNode: Default

    // --- Converting to Result ---
    let _ = node.as_ref().ok_or("no node");             // Result<&Box<BinaryNode>, &str>
    let _ = node.as_ref().ok_or_else(|| "no node");     // lazy version

    // --- Boolean ops ---
    let other: Option<Box<BinaryNode>> = None;
    let _ = node.as_ref().or(other.as_ref());    // first Some
    let _ = node.as_ref().and(other.as_ref());   // second if both Some
}

// ============================================================
// Result<T, E> combinator reference
// ============================================================
fn result_combinators(result: Result<BinaryNode, TreeError>) {
    // --- Querying ---
    let _ = result.is_ok();
    let _ = result.is_err();

    // --- Transforming ---
    let _ = result.as_ref().map(|n| n.data);          // Result<i32, &TreeError>
    let _ = result.as_ref().map_err(|e| e.to_string());// Result<&BinaryNode, String>
    let _ = result.as_ref().and_then(|n| {
        if n.data > 0 { Ok(n) } else { Err(&TreeError::NotFound(0)) }
    });

    // --- Defaulting ---
    let default_node = BinaryNode::new(0);
    let _ = result.as_ref().unwrap_or(&default_node);
    let _ = result.as_ref().unwrap_or_else(|_| &default_node);

    // --- Combining Results ---
    let r2: Result<i32, TreeError> = Ok(42);
    // If both Ok, return second; if either Err, return first Err
    // let _ = result.as_ref().and(r2.as_ref());
}

// ============================================================
// Transposing Option<Result> ↔ Result<Option>
// ============================================================
fn transpose_example() {
    let opt_res: Option<Result<i32, TreeError>> = Some(Ok(42));
    let res_opt: Result<Option<i32>, TreeError> = opt_res.transpose();
    // Some(Ok(x)) → Ok(Some(x))
    // Some(Err(e)) → Err(e)
    // None → Ok(None)
}
```

---

## 7. Boundary and Range Constraints

Buffer overflows are the number one source of security vulnerabilities in C. Range checking is non-negotiable in production code.

### 7.1 C — Manual Bounds Checking

```c
#include <stddef.h>

/* ============================================================
 * PATTERN: Safe array access with explicit bounds check
 * ============================================================ */
typedef struct {
    int   *data;
    size_t size;
    size_t capacity;
} IntArray;

/* Safe getter — returns 0 and sets errno on out-of-bounds */
int array_get(const IntArray *a, size_t index) {
    if (a == NULL || index >= a->size) {
        errno = EINVAL;
        return 0;
    }
    return a->data[index];
}

/* Safe setter — returns false on failure */
int array_set(IntArray *a, size_t index, int value) {
    if (a == NULL || index >= a->size) return 0;
    a->data[index] = value;
    return 1;
}

/* ============================================================
 * PATTERN: Checked arithmetic — prevent integer overflow
 * ============================================================ */
#include <limits.h>

int safe_add(int a, int b, int *result) {
    /* Integer overflow is undefined behaviour in C — check before it happens */
    if ((b > 0 && a > INT_MAX - b) ||
        (b < 0 && a < INT_MIN - b)) {
        return 0; // overflow would occur
    }
    *result = a + b;
    return 1;
}

size_t safe_size_add(size_t a, size_t b) {
    if (a > SIZE_MAX - b) {
        fprintf(stderr, "size_t overflow: %zu + %zu\n", a, b);
        exit(EXIT_FAILURE);
    }
    return a + b;
}

/* ============================================================
 * PATTERN: String length constraints
 * ============================================================ */
#include <string.h>
#define MAX_NAME_LEN 255

int set_name(char *dest, size_t dest_size, const char *src) {
    if (!dest || !src)               return -1;
    if (dest_size == 0)              return -1;
    size_t src_len = strlen(src);
    if (src_len > MAX_NAME_LEN)      return -1; // Reject, don't truncate silently
    if (src_len >= dest_size)        return -1; // Won't fit
    memcpy(dest, src, src_len + 1);  // +1 for null terminator
    return 0;
}
```

### 7.2 Go — Slice Bounds and Overflow Safety

```go
package tree

import "math"

// ============================================================
// Go slices have built-in bounds checking — out-of-range panics
// ============================================================
// But you should still validate before access in library code.

func SafeGet(s []int, i int) (int, bool) {
    if i < 0 || i >= len(s) {
        return 0, false
    }
    return s[i], true
}

// ============================================================
// Safe slice operations
// ============================================================
func SafeSlice(s []int, low, high int) ([]int, error) {
    if low < 0 || high > len(s) || low > high {
        return nil, fmt.Errorf(
            "slice [%d:%d] out of bounds for length %d", low, high, len(s))
    }
    return s[low:high], nil
}

// ============================================================
// Integer overflow — Go doesn't panic on overflow (wraps around)
// ============================================================
func SafeAdd(a, b int) (int, error) {
    result := a + b
    // Detect overflow: sign change when adding same-sign numbers
    if (b > 0 && result < a) || (b < 0 && result > a) {
        return 0, fmt.Errorf("integer overflow: %d + %d", a, b)
    }
    return result, nil
}

// ============================================================
// Range constraint via custom type
// ============================================================
type Percentage float64

func NewPercentage(v float64) (Percentage, error) {
    if v < 0 || v > 100 {
        return 0, fmt.Errorf("percentage must be in [0, 100], got %f", v)
    }
    return Percentage(v), nil
}
```

### 7.3 Rust — Range Constraints via Type System

```rust
// ============================================================
// PATTERN 1: Newtype with invariant enforcement
// ============================================================
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
pub struct Percentage(f64); // private field — cannot construct directly

impl Percentage {
    pub fn new(value: f64) -> Result<Self, TreeError> {
        if !(0.0..=100.0).contains(&value) {
            return Err(TreeError::OutOfRange {
                data: value as i32, min: 0, max: 100,
            });
        }
        Ok(Percentage(value))
    }

    pub fn value(self) -> f64 { self.0 }
}

// ============================================================
// PATTERN 2: Checked arithmetic in std
// ============================================================
fn checked_arithmetic_demo() {
    let a: i32 = i32::MAX;

    // checked_* — returns Option<T>
    let _ = a.checked_add(1);                // None (overflow)
    let _ = a.checked_mul(2);                // None

    // saturating_* — clamps to min/max
    let _ = a.saturating_add(1);             // i32::MAX (no panic)

    // wrapping_* — wraps around (C-style)
    let _ = a.wrapping_add(1);               // i32::MIN

    // overflowing_* — returns (result, did_overflow)
    let (result, overflowed) = a.overflowing_add(1);
    assert!(overflowed);

    // For production: prefer checked_* and handle None explicitly
}

// ============================================================
// PATTERN 3: Slice bounds — Rust panics on index out of bounds
// Use .get() for safe access returning Option<&T>
// ============================================================
fn safe_array_access(arr: &[i32], index: usize) -> Option<i32> {
    arr.get(index).copied()    // Option<i32>
}

fn safe_slice(arr: &[i32], start: usize, end: usize) -> Option<&[i32]> {
    arr.get(start..end)        // Option<&[i32]>
}

// ============================================================
// PATTERN 4: const generic constraints
// ============================================================
// Enforce array size at compile time — no runtime cost.
fn sum_fixed<const N: usize>(arr: [i32; N]) -> i32 {
    arr.iter().sum()
}

// The type system prevents calling this with wrong size:
// sum_fixed([1, 2, 3]);      // [i32; 3] ✓
// sum_fixed([1, 2, 3, 4]);   // [i32; 4] — different type, compile error if signature mismatch
```

---

## 8. Type System Constraints

The most powerful constraint is one that is impossible to violate because the type system prevents it from compiling.

### 8.1 C — Typedef, Enum, and const for Type Safety

```c
/* ============================================================
 * PATTERN 1: Typedef for semantic clarity (poor man's newtype)
 * ============================================================ */
typedef int NodeId;      // Different semantic type, same underlying type
typedef int Depth;       // Compiler won't catch swaps — it's documentation only

/* ============================================================
 * PATTERN 2: Opaque types — hide implementation details
 * ============================================================
 * Callers cannot inspect or modify the struct's internals.
 * Header file only exposes: typedef struct Tree Tree; */
typedef struct InternalTree InternalTree;

struct InternalTree {
    BinaryNode *root;
    int         size;
    int         max_depth;
};

// Only the .c file can access the struct layout.
// Callers are forced through the API.
InternalTree *tree_create(void);
void          tree_destroy(InternalTree *t);
int           tree_insert(InternalTree *t, int data);

/* ============================================================
 * PATTERN 3: enum for exhaustive case handling
 * ============================================================ */
typedef enum {
    NODE_LEAF,
    NODE_INTERNAL,
    NODE_ROOT,
} NodeType;

const char *describe_node(NodeType type) {
    switch (type) {
        case NODE_LEAF:     return "leaf";
        case NODE_INTERNAL: return "internal";
        case NODE_ROOT:     return "root";
        /* Adding a new enum value without updating this switch
         * triggers -Wswitch-enum with -Wall — the compiler becomes
         * your exhaustiveness checker. */
    }
    return "unknown"; // Should never reach here
}

/* ============================================================
 * PATTERN 4: const-correctness
 * ============================================================ */
// 'const BinaryNode *' — cannot modify the node through this pointer
// 'BinaryNode * const' — cannot reassign the pointer itself
// 'const BinaryNode * const' — neither

int tree_depth(const BinaryNode *node) {  // Promises: won't modify tree
    if (node == NULL) return 0;
    int l = tree_depth(node->left);
    int r = tree_depth(node->right);
    return 1 + (l > r ? l : r);
}
```

### 8.2 Go — Interface Constraints and Type Assertions

```go
package tree

import "io"

// ============================================================
// PATTERN 1: Interface as constraint contract
// ============================================================
// Interfaces define the minimum required behaviour.
// A type that does not satisfy the interface does not compile.

type TreeWriter interface {
    WriteTree(w io.Writer) error
}

type TreeReader interface {
    ReadTree(r io.Reader) error
}

// Compile-time interface satisfaction check
var _ TreeWriter = (*SafeTree)(nil)
// If SafeTree does not implement WriteTree, this line fails to compile.

func (t *SafeTree) WriteTree(w io.Writer) error {
    _, err := fmt.Fprintf(w, "tree(size=%d)", t.size)
    return err
}

// ============================================================
// PATTERN 2: Type assertions with safety check
// ============================================================
func processTreeWriter(t any) error {
    // Safe type assertion — never panics
    tw, ok := t.(TreeWriter)
    if !ok {
        return fmt.Errorf("processTreeWriter: %T does not implement TreeWriter", t)
    }
    return tw.WriteTree(io.Discard)
}

// ============================================================
// PATTERN 3: Generics for type-safe containers (Go 1.18+)
// ============================================================
type Ordered interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64 |
    ~uint | ~float32 | ~float64 | ~string
}

type BST[T Ordered] struct {
    data  T
    left  *BST[T]
    right *BST[T]
}

func (b *BST[T]) Insert(value T) *BST[T] {
    if b == nil {
        return &BST[T]{data: value}
    }
    if value < b.data {
        b.left = b.left.Insert(value)
    } else if value > b.data {
        b.right = b.right.Insert(value)
    }
    return b
}
// Type system now prevents inserting a string into an int BST.
```

### 8.3 Rust — Newtype, Phantom Types, and Trait Bounds

```rust
use std::marker::PhantomData;

// ============================================================
// PATTERN 1: Newtype — zero-cost type distinction
// ============================================================
// The compiler treats NodeId and UserId as different types.
// You cannot accidentally pass one where the other is expected.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct NodeId(u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct UserId(u64);

impl NodeId {
    pub fn new(id: u64) -> Self { NodeId(id) }
    pub fn value(self) -> u64 { self.0 }
}

// This function cannot accept a UserId:
pub fn find_by_node_id(id: NodeId) -> Option<BinaryNode> { None }

// ============================================================
// PATTERN 2: Phantom types — encode state in the type system
// ============================================================
// A connection that can only be used in the correct state.
pub struct Unvalidated;
pub struct Validated;

pub struct TreeData<State> {
    values: Vec<i32>,
    _state: PhantomData<State>,
}

impl TreeData<Unvalidated> {
    pub fn new(values: Vec<i32>) -> Self {
        TreeData { values, _state: PhantomData }
    }

    // Validation is the ONLY way to move to Validated state
    pub fn validate(self) -> Result<TreeData<Validated>, TreeError> {
        if self.values.is_empty() {
            return Err(TreeError::EmptyTree);
        }
        if self.values.iter().any(|&v| v < -1000 || v > 1000) {
            return Err(TreeError::OutOfRange { data: 0, min: -1000, max: 1000 });
        }
        Ok(TreeData { values: self.values, _state: PhantomData })
    }
}

impl TreeData<Validated> {
    // Only callable after validation — the type proves it
    pub fn build_tree(&self) -> BinaryNode {
        BinaryNode::new(self.values[0]) // Safe: we know it's non-empty and valid
    }
}

// ============================================================
// PATTERN 3: Trait bounds as function constraints
// ============================================================
use std::fmt::{Debug, Display};

// This function CANNOT be called with a type that doesn't implement Debug + Display
pub fn debug_print<T: Debug + Display>(value: T) {
    println!("Display: {}", value);
    println!("Debug: {:?}", value);
}

// ============================================================
// PATTERN 4: Sealed traits — prevent external implementation
// ============================================================
mod private { pub trait Sealed {} }

pub trait TreeNode: private::Sealed {
    fn data(&self) -> i32;
}

impl private::Sealed for BinaryNode {}
impl TreeNode for BinaryNode {
    fn data(&self) -> i32 { self.data }
}
// External code cannot implement TreeNode for their types.
```

---

## 9. Ownership and Lifetime Constraints (Rust)

Rust's most distinctive feature: the borrow checker enforces memory and concurrency safety at compile time with zero runtime cost.

```rust
// ============================================================
// PATTERN 1: Ownership — a value has exactly one owner
// ============================================================
fn ownership_demo() {
    let node = BinaryNode::new(5);   // node owns the value
    let _other = node;               // ownership moves to _other
    // println!("{}", node.data);    // COMPILE ERROR: node is moved
}

// ============================================================
// PATTERN 2: Immutable borrows — many readers, no writers
// ============================================================
fn print_node(node: &BinaryNode) {        // borrows, does not own
    println!("{}", node.data);
    // node is still valid after this function returns
}

// ============================================================
// PATTERN 3: Mutable borrows — exactly one writer at a time
// ============================================================
fn increment(node: &mut BinaryNode) {
    node.data += 1;
    // No other code can read or write node.data during this borrow
}

// ============================================================
// PATTERN 4: Lifetime annotations — constrain reference validity
// ============================================================
// This tells the compiler: the returned reference lives as long as
// the shorter of 'a and 'b. Without this annotation, the compiler
// cannot prove the returned reference is valid.
pub fn longest_data<'a>(x: &'a BinaryNode, y: &'a BinaryNode) -> &'a BinaryNode {
    if x.data >= y.data { x } else { y }
}

// ============================================================
// PATTERN 5: Rc<RefCell<T>> — shared mutable ownership with
// runtime borrow checking (the "escape hatch")
// ============================================================
use std::rc::Rc;
use std::cell::RefCell;

pub struct SharedNode {
    pub data:  i32,
    pub left:  Option<Rc<RefCell<SharedNode>>>,
    pub right: Option<Rc<RefCell<SharedNode>>>,
}

fn shared_tree_demo() {
    let node = Rc::new(RefCell::new(SharedNode { data: 1, left: None, right: None }));
    let node_ref = Rc::clone(&node);      // Shared ownership

    node.borrow_mut().data = 42;          // Runtime borrow check
    println!("{}", node_ref.borrow().data);
    // RefCell panics at runtime if you try to borrow_mut while borrowed —
    // same rules as the borrow checker, but enforced at runtime.
}

// ============================================================
// PATTERN 6: Arc<Mutex<T>> — thread-safe shared mutation
// ============================================================
use std::sync::{Arc, Mutex};

pub struct ConcurrentTree {
    root: Arc<Mutex<Option<BinaryNode>>>,
}

impl ConcurrentTree {
    pub fn insert(&self, data: i32) -> Result<(), TreeError> {
        let mut root = self.root.lock()
            .map_err(|_| TreeError::NotFound(data))?; // Mutex poisoning guard
        *root = Some(BinaryNode::new(data));
        Ok(())
    }
}
```

---

## 10. Invariant Enforcement via Constructors

The "make illegal states unrepresentable" principle: design types so that valid construction is the only option.

### 10.1 C — Opaque Constructor Pattern

```c
/* ============================================================
 * tree.h — public API only. Internal layout is hidden.
 * ============================================================ */
typedef struct BSTree BSTree;  // Forward declaration — size unknown to callers

/* Constructor — only way to create a valid tree */
BSTree *bstree_create(int min_val, int max_val);
void    bstree_destroy(BSTree *t);
int     bstree_insert(BSTree *t, int data);
int     bstree_find(const BSTree *t, int data);

/* ============================================================
 * tree.c — internal implementation with invariant enforcement
 * ============================================================ */
struct BSTree {
    BinaryNode *root;
    int         size;
    int         min_val;     // Enforced constraint
    int         max_val;     // Enforced constraint
};

BSTree *bstree_create(int min_val, int max_val) {
    /* Constructor invariant: min must be less than max */
    if (min_val >= max_val) {
        errno = EINVAL;
        return NULL;
    }
    BSTree *t = malloc(sizeof(BSTree));
    if (!t) return NULL;
    t->root    = NULL;
    t->size    = 0;
    t->min_val = min_val;
    t->max_val = max_val;
    return t;
}

int bstree_insert(BSTree *t, int data) {
    if (t == NULL)                    return -1;
    if (data < t->min_val)            return -1;  // Invariant enforced on every mutation
    if (data > t->max_val)            return -1;
    /* ... insert logic ... */
    return 0;
}
```

### 10.2 Go — Constructor Functions as Invariant Gates

```go
package tree

// RangedTree enforces that all values lie within [min, max].
// The zero value is intentionally invalid — force use of NewRangedTree.
type RangedTree struct {
    root     *BinaryNode
    size     int
    minVal   int
    maxVal   int
    isValid  bool // sentinel: was this created by the constructor?
}

// NewRangedTree is the ONLY valid constructor.
func NewRangedTree(minVal, maxVal int) (*RangedTree, error) {
    if minVal >= maxVal {
        return nil, fmt.Errorf("NewRangedTree: minVal (%d) must be less than maxVal (%d)",
            minVal, maxVal)
    }
    return &RangedTree{
        minVal:  minVal,
        maxVal:  maxVal,
        isValid: true,
    }, nil
}

func (t *RangedTree) Insert(data int) error {
    if t == nil || !t.isValid {
        return errors.New("RangedTree.Insert: uninitialised tree — use NewRangedTree")
    }
    if data < t.minVal || data > t.maxVal {
        return fmt.Errorf("RangedTree.Insert: %d outside range [%d, %d]",
            data, t.minVal, t.maxVal)
    }
    t.root = insertBST(t.root, data)
    t.size++
    return nil
}
```

### 10.3 Rust — Type-State Pattern and Private Fields

```rust
// ============================================================
// Private fields + constructor = enforced invariants forever
// ============================================================
#[derive(Debug)]
pub struct RangedTree {
    root:    Option<Box<BinaryNode>>,
    size:    usize,
    min_val: i32,   // private — callers can never change these
    max_val: i32,   // private
}

impl RangedTree {
    // Constructor is the invariant gate
    pub fn new(min_val: i32, max_val: i32) -> Result<Self, TreeError> {
        if min_val >= max_val {
            return Err(TreeError::OutOfRange {
                data: min_val,
                min: i32::MIN,
                max: max_val - 1,
            });
        }
        Ok(RangedTree { root: None, size: 0, min_val, max_val })
    }

    pub fn insert(&mut self, data: i32) -> Result<(), TreeError> {
        if data < self.min_val || data > self.max_val {
            return Err(TreeError::OutOfRange {
                data, min: self.min_val, max: self.max_val,
            });
        }
        // Invariant holds: data is in range
        self.root = Some(Box::new(BinaryNode::new(data)));
        self.size += 1;
        Ok(())
    }

    // Read-only accessors — callers cannot bypass the constraints
    pub fn size(&self)    -> usize { self.size }
    pub fn min_val(&self) -> i32   { self.min_val }
    pub fn max_val(&self) -> i32   { self.max_val }
}

// ============================================================
// Builder pattern — incremental construction with validation
// ============================================================
#[derive(Default)]
pub struct TreeBuilder {
    values:  Vec<i32>,
    min_val: Option<i32>,
    max_val: Option<i32>,
}

impl TreeBuilder {
    pub fn new() -> Self { Default::default() }

    pub fn min(mut self, val: i32) -> Self { self.min_val = Some(val); self }
    pub fn max(mut self, val: i32) -> Self { self.max_val = Some(val); self }
    pub fn value(mut self, val: i32) -> Self { self.values.push(val); self }

    pub fn build(self) -> Result<RangedTree, TreeError> {
        let min = self.min_val.unwrap_or(i32::MIN);
        let max = self.max_val.unwrap_or(i32::MAX);
        let mut tree = RangedTree::new(min, max)?;
        for v in self.values {
            tree.insert(v)?;
        }
        Ok(tree)
    }
}

// Usage:
// let tree = TreeBuilder::new().min(-100).max(100).value(42).value(7).build()?;
```

---

## 11. Panic vs. Recoverable Error — When to Use Each

This is one of the most consequential architectural decisions in constraint handling.

| Situation | C | Go | Rust |
|-----------|---|----|----|
| **Programmer bug** (invalid args to internal func) | `assert()` / `abort()` | `panic()` | `panic!()` / `assert!()` |
| **Expected runtime failure** (file not found, bad input) | Return code / errno | `return error` | `return Err(...)` |
| **Unrecoverable state** (OOM, corrupted data structure) | `exit()` | `panic()` or `log.Fatal()` | `panic!()` |
| **Library code** | Return error code | Return `error` | Return `Result<T, E>` |
| **Application entry point** | Check exit codes | `log.Fatal` on startup errors | `fn main() -> Result<()>` |

### C — Abort vs. Return

```c
/* Use abort() for programming errors — it produces a core dump */
void *safe_malloc(size_t size) {
    assert(size > 0);         // Programmer error: calling malloc(0) is suspicious
    void *ptr = malloc(size);
    if (!ptr) {
        /* OOM is an environment failure, not a programming error.
         * But for many embedded/server apps, you cannot recover from OOM. */
        fprintf(stderr, "FATAL: malloc(%zu) failed\n", size);
        abort();  // Dump core, let the OS kill the process
    }
    return ptr;
}

/* Return -1 for recoverable runtime failures */
int read_config(const char *path, Config *out) {
    if (!path || !out) { errno = EINVAL; return -1; } // Programming error in caller
    FILE *f = fopen(path, "r");
    if (!f) return -1; // File not found — caller can handle this
    /* parse ... */
    fclose(f);
    return 0;
}
```

### Go — Panic vs. Error

```go
// Panic for programming errors — bugs that should never occur if code is correct.
// Error for runtime failures — things that can fail even in correct programs.

func (t *SafeTree) insert(data int) {
    // This is a private function — if it receives nil, that's a bug in THIS package.
    // A panic is appropriate: it signals a bug to the developer.
    if t == nil {
        panic("internal error: insert called on nil SafeTree")
    }
    t.root = insertBST(t.root, data)
}

// Public API: return error — let the caller decide what to do.
func (t *SafeTree) Insert(data int) (err error) {
    // recover() converts a panic in a public API into an error
    // Use this only at API boundaries, not inside packages.
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("Insert recovered from panic: %v", r)
        }
    }()
    t.insert(data)
    return nil
}
```

### Rust — panic! vs Result

```rust
// panic! = "this is a bug in my code, stop now"
// Err  = "this is an expected failure, let the caller handle it"

pub fn safe_index(arr: &[i32], i: usize) -> i32 {
    // Don't use panic for expected out-of-bounds in a library
    // The caller should use .get() and handle None.
    // But for internal invariants that must hold:
    assert!(i < arr.len(), "safe_index: index {} >= len {}", i, arr.len());
    arr[i]
}

// Application entry point — propagate all errors to main
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let tree = RangedTree::new(-100, 100)?;   // ? propagates to main, prints error
    println!("Tree created: {:?}", tree);
    Ok(())
}
```

---

## 12. Defensive Programming Patterns

Defensive programming assumes that callers will make mistakes and designs systems to fail safely.

### 12.1 C — Defensive Initialisation and Zeroing

```c
/* ============================================================
 * PATTERN: Always zero-initialise structs
 * ============================================================ */
BinaryNode *new_node_safe(int data) {
    /* Using calloc instead of malloc — zeroes all bytes.
     * NULL pointers are guaranteed to be all-zero bits on POSIX. */
    BinaryNode *node = calloc(1, sizeof(BinaryNode));
    if (!node) return NULL;
    node->data = data;
    /* left and right are already NULL from calloc */
    return node;
}

/* ============================================================
 * PATTERN: Poison freed memory in debug builds
 * ============================================================
 * This catches use-after-free bugs immediately. */
void free_node(BinaryNode **node_ptr) {
    if (!node_ptr || !*node_ptr) return;
#ifndef NDEBUG
    /* Fill with 0xDD ("dead memory") — dereference will be obvious */
    memset(*node_ptr, 0xDD, sizeof(BinaryNode));
#endif
    free(*node_ptr);
    *node_ptr = NULL;  // Prevent double-free
}

/* ============================================================
 * PATTERN: Canary values for buffer overflow detection
 * ============================================================ */
#define CANARY 0xDEADBEEF

typedef struct {
    unsigned int canary_start;
    int          data[64];
    unsigned int canary_end;
} ProtectedBuffer;

void init_protected(ProtectedBuffer *b) {
    b->canary_start = CANARY;
    b->canary_end   = CANARY;
    memset(b->data, 0, sizeof(b->data));
}

int check_canaries(const ProtectedBuffer *b) {
    return b->canary_start == CANARY && b->canary_end == CANARY;
}
```

### 12.2 Go — Defensive Copies and Immutable Patterns

```go
// ============================================================
// PATTERN: Defensive copy — prevent caller from mutating internal state
// ============================================================
func (t *SafeTree) Snapshot() []int {
    result := make([]int, 0, t.size)
    // Collect all values into a new slice
    var collect func(*BinaryNode)
    collect = func(n *BinaryNode) {
        if n == nil { return }
        collect(n.Left)
        result = append(result, n.Data)
        collect(n.Right)
    }
    collect(t.root)
    // Caller gets a copy — they cannot corrupt t's internal state
    return result
}

// ============================================================
// PATTERN: Copy-on-write semantics for shared config
// ============================================================
type TreeConfig struct {
    MaxDepth int
    AllowDup bool
}

func (c TreeConfig) WithMaxDepth(d int) TreeConfig {
    c.MaxDepth = d  // Modifies the copy, not the original
    return c
}
```

---

## 13. Contract-Based Programming (Design by Contract)

Design by Contract (DbC) formalises the relationship between callers and callees via preconditions, postconditions, and invariants.

```
Precondition:  what the caller must guarantee before calling
Postcondition: what the callee guarantees if the precondition holds
Invariant:     what is always true about the object's state
```

### C — Manual DbC via Macros

```c
/* DbC macros */
#define REQUIRES(cond)  assert(cond)      // Precondition  — caller's fault if violated
#define ENSURES(cond)   assert(cond)      // Postcondition — callee's fault if violated
#define INVARIANT(cond) assert(cond)      // Must hold at all times

int binary_search(const int *arr, int n, int target) {
    /* Contract: */
    REQUIRES(arr != NULL);                // Precondition: array must exist
    REQUIRES(n >= 0);                     // Precondition: non-negative length
    // Precondition: array is sorted (expensive to check, document it)
    // REQUIRES(is_sorted(arr, n));

    int lo = 0, hi = n - 1, result = -1;

    while (lo <= hi) {
        INVARIANT(lo >= 0 && hi < n);    // Loop invariant

        int mid = lo + (hi - lo) / 2;   // Avoids overflow vs (lo+hi)/2
        if      (arr[mid] == target) { result = mid; break; }
        else if (arr[mid] < target)  { lo = mid + 1; }
        else                          { hi = mid - 1; }
    }

    /* Postcondition: result is -1 or a valid index containing target */
    ENSURES(result == -1 || (result >= 0 && result < n && arr[result] == target));
    return result;
}
```

### Go — DbC via Functions

```go
// ============================================================
// DbC in Go — function wrappers that enforce pre/postconditions
// ============================================================

type Precondition  func() error
type Postcondition func(returnValue any) error

func contract(pre Precondition, fn func() any, post Postcondition) (any, error) {
    if err := pre(); err != nil {
        return nil, fmt.Errorf("precondition violated: %w", err)
    }
    result := fn()
    if err := post(result); err != nil {
        return nil, fmt.Errorf("postcondition violated: %w", err)
    }
    return result, nil
}

func BinarySearchContracted(arr []int, target int) (int, error) {
    return -1, nil // placeholder — contracts shown below

    // Idiomatic Go approach: explicit validation
    if arr == nil {
        return 0, errors.New("binarySearch: arr must not be nil")
    }
    for i := 1; i < len(arr); i++ {
        if arr[i] < arr[i-1] {
            return 0, fmt.Errorf("binarySearch: arr not sorted at index %d", i)
        }
    }

    lo, hi := 0, len(arr)-1
    for lo <= hi {
        mid := lo + (hi-lo)/2
        switch {
        case arr[mid] == target:
            // Postcondition: arr[result] == target
            if arr[mid] != target {
                panic("postcondition violated")
            }
            return mid, nil
        case arr[mid] < target:
            lo = mid + 1
        default:
            hi = mid - 1
        }
    }
    return -1, nil
}
```

### Rust — DbC via Type System and Contracts

```rust
// ============================================================
// DbC in Rust — the type system IS the contract system
// ============================================================

// Preconditions as type invariants (cannot construct invalid input)
pub struct SortedSlice<'a>(&'a [i32]);

impl<'a> SortedSlice<'a> {
    pub fn new(slice: &'a [i32]) -> Result<Self, TreeError> {
        // Validate the precondition ONCE at construction
        if !slice.windows(2).all(|w| w[0] <= w[1]) {
            return Err(TreeError::NotFound(0)); // or a Unsorted error
        }
        Ok(SortedSlice(slice))
    }
}

// Binary search: precondition (sorted) encoded in the type.
// No runtime check needed inside this function.
pub fn binary_search(sorted: &SortedSlice, target: i32) -> Option<usize> {
    let slice = sorted.0;
    let (mut lo, mut hi) = (0usize, slice.len());

    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        match slice[mid].cmp(&target) {
            std::cmp::Ordering::Equal   => return Some(mid),
            std::cmp::Ordering::Less    => lo = mid + 1,
            std::cmp::Ordering::Greater => hi = mid,
        }
    }

    // Postcondition encoded in return type: Some(idx) or None — no invalid state
    None
}

// Usage:
// let sorted = SortedSlice::new(&[1, 3, 5, 7, 9])?;
// let pos = binary_search(&sorted, 5); // Some(2)
```

---

## 14. Memory Safety Constraints

### C — Tools to Enforce Memory Safety

```c
/* ============================================================
 * C itself has no memory safety. Use these tools:
 *
 * Compile-time:
 *   -Wall -Wextra -Wpedantic -Warray-bounds -Wshadow
 *   -fsanitize=address,undefined  (ASan + UBSan)
 *
 * Runtime (build with -fsanitize flags):
 *   AddressSanitizer  — detects heap/stack overflow, use-after-free
 *   UndefinedBehaviorSanitizer — detects signed overflow, misaligned access
 *   MemorySanitizer   — detects uninitialised reads
 *   Valgrind          — comprehensive memory checking (slower)
 *
 * Static analysis:
 *   clang-tidy, cppcheck, Coverity, CodeSonar
 * ============================================================ */

/* ============================================================
 * PATTERN: RAII-style cleanup via cleanup attribute (GCC/Clang)
 * ============================================================ */
static void cleanup_file(FILE **f) {
    if (*f) { fclose(*f); *f = NULL; }
}

static void cleanup_ptr(void **p) {
    free(*p); *p = NULL;
}

/* Usage: cleanup happens automatically at scope exit */
void safe_file_operation(const char *path) {
    __attribute__((cleanup(cleanup_file))) FILE *f = fopen(path, "r");
    __attribute__((cleanup(cleanup_ptr))) char  *buf = malloc(256);

    if (!f || !buf) return; // cleanup still runs here

    /* ... use f and buf ... */
    /* cleanup runs automatically here, even on return or goto */
}
```

### Go — Memory Safety by Design

```go
// Go is memory-safe by design:
// - Garbage collected — no manual free()
// - Bounds-checked arrays and slices — panics on out-of-bounds
// - No pointer arithmetic
// - No uninitialised variables (zero values)
// - No use-after-free

// The remaining unsafe operations:
// 1. Data races — use -race detector
// 2. Nil pointer dereference — use nil checks
// 3. Integer overflow — check arithmetic

// ============================================================
// The go race detector: go run -race main.go
// ============================================================
import "sync"

type SafeCounter struct {
    mu    sync.Mutex
    value int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.value
}
```

### Rust — Compile-Time Memory Safety

```rust
// ============================================================
// Rust's memory safety guarantees (enforced by compiler):
//
// 1. No null pointer dereferences    → Option<T>
// 2. No use-after-free               → ownership system
// 3. No double-free                  → ownership system (Drop runs once)
// 4. No dangling pointers            → lifetime system
// 5. No data races                   → Send/Sync traits + borrow checker
// 6. No buffer overflows             → bounds-checked indexing
// 7. No uninitialised memory reads   → all variables must be initialised
// ============================================================

// The only way to violate these rules is with `unsafe`:
pub fn raw_pointer_demo() {
    let x: i32 = 42;
    let raw: *const i32 = &x as *const i32;

    // SAFE: raw pointer from a valid reference
    unsafe {
        println!("{}", *raw); // Must be inside unsafe block — you're taking responsibility
    }

    // Rule: keep unsafe blocks minimal and document WHY it's safe
    // Rule: encapsulate unsafe in safe abstractions
    // Rule: never expose raw pointers across API boundaries
}

// ============================================================
// PATTERN: Safe abstraction over unsafe code
// ============================================================
pub struct AlignedBuffer {
    ptr: *mut u8,
    len: usize,
}

impl AlignedBuffer {
    pub fn new(size: usize, align: usize) -> Option<Self> {
        let layout = std::alloc::Layout::from_size_align(size, align).ok()?;
        let ptr = unsafe { std::alloc::alloc(layout) };
        if ptr.is_null() { return None; }
        Some(AlignedBuffer { ptr, len: size })
    }

    // Safe API — callers never touch the raw pointer
    pub fn as_slice(&self) -> &[u8] {
        unsafe { std::slice::from_raw_parts(self.ptr, self.len) }
    }
}

impl Drop for AlignedBuffer {
    fn drop(&mut self) {
        let layout = std::alloc::Layout::from_size_align(self.len, 8).unwrap();
        unsafe { std::alloc::dealloc(self.ptr, layout); }
    }
}
```

---

## 15. Concurrency Constraints

Concurrent code introduces a new class of constraint violations: data races, deadlocks, and ordering violations.

### C — POSIX Mutex and Atomic Constraints

```c
#include <pthread.h>
#include <stdatomic.h>

/* ============================================================
 * PATTERN: Mutex-protected invariants
 * ============================================================ */
typedef struct {
    pthread_mutex_t lock;
    BinaryNode     *root;
    int             size;
} ConcurrentTree;

int ctree_insert(ConcurrentTree *t, int data) {
    if (t == NULL) return -1;

    pthread_mutex_lock(&t->lock);
    /* Critical section — invariant: size == actual node count */
    /* ... insert ... */
    t->size++;
    pthread_mutex_unlock(&t->lock);
    return 0;
}

/* ============================================================
 * PATTERN: Lock-free counter with atomics
 * ============================================================ */
typedef struct {
    atomic_int  count;
    atomic_bool shutdown;
} Stats;

void stats_increment(Stats *s) {
    /* atomic_fetch_add is sequentially consistent — no race condition */
    atomic_fetch_add(&s->count, 1);
}

int stats_get(const Stats *s) {
    return atomic_load(&s->count);
}
```

### Go — Goroutine Safety Patterns

```go
package tree

import "sync"

// ============================================================
// PATTERN: sync.RWMutex for read-heavy workloads
// ============================================================
type ConcurrentTree struct {
    mu   sync.RWMutex
    root *BinaryNode
    size int
}

func (t *ConcurrentTree) Insert(data int) {
    t.mu.Lock()           // Exclusive write lock
    defer t.mu.Unlock()
    t.root = insertBST(t.root, data)
    t.size++
}

func (t *ConcurrentTree) Find(data int) *BinaryNode {
    t.mu.RLock()          // Shared read lock — multiple readers allowed
    defer t.mu.RUnlock()
    return findBST(t.root, data)
}

// ============================================================
// PATTERN: Channel-based serialisation
// ============================================================
type TreeOp struct {
    data   int
    result chan *BinaryNode
}

type SerialTree struct {
    root   *BinaryNode
    insert chan int
    find   chan TreeOp
}

func NewSerialTree() *SerialTree {
    t := &SerialTree{
        insert: make(chan int, 16),
        find:   make(chan TreeOp),
    }
    go t.run()
    return t
}

func (t *SerialTree) run() {
    for {
        select {
        case data := <-t.insert:
            t.root = insertBST(t.root, data) // Serialised — no race possible
        case op := <-t.find:
            op.result <- findBST(t.root, op.data)
        }
    }
}

func (t *SerialTree) Insert(data int) { t.insert <- data }

func (t *SerialTree) Find(data int) *BinaryNode {
    result := make(chan *BinaryNode, 1)
    t.find <- TreeOp{data: data, result: result}
    return <-result
}
```

### Rust — Send/Sync and the Fearless Concurrency Model

```rust
use std::sync::{Arc, Mutex, RwLock};
use std::thread;

// ============================================================
// Send: safe to transfer ownership to another thread
// Sync: safe to share a reference between threads
// The compiler REFUSES to compile code that violates these.
// ============================================================

// Arc<T> — shared ownership across threads (T must be Send + Sync)
// Mutex<T> — exclusive mutable access
// RwLock<T> — multiple readers OR one writer

pub struct ThreadSafeTree {
    inner: Arc<RwLock<Option<BinaryNode>>>,
}

impl ThreadSafeTree {
    pub fn new() -> Self {
        ThreadSafeTree { inner: Arc::new(RwLock::new(None)) }
    }

    pub fn insert(&self, data: i32) -> Result<(), TreeError> {
        let mut guard = self.inner.write()
            .map_err(|_| TreeError::NotFound(data))?; // Poisoning guard
        *guard = Some(BinaryNode::new(data));
        Ok(())
    }

    pub fn find(&self, data: i32) -> Result<bool, TreeError> {
        let guard = self.inner.read()
            .map_err(|_| TreeError::NotFound(data))?;
        Ok(guard.as_ref().map_or(false, |n| n.data == data))
    }

    // Clone the handle — not the data
    pub fn clone_handle(&self) -> Self {
        ThreadSafeTree { inner: Arc::clone(&self.inner) }
    }
}

// Compiler proves this is safe to use across threads:
// fn require_send_sync<T: Send + Sync>(_: T) {}
// require_send_sync(ThreadSafeTree::new()); // Compiles only if Send + Sync

fn concurrency_demo() {
    let tree = ThreadSafeTree::new();
    let tree2 = tree.clone_handle();

    let writer = thread::spawn(move || {
        tree2.insert(42).unwrap();
    });

    let result = tree.find(42);
    writer.join().unwrap();
}
```

---

## 16. Static Analysis and Compiler-Level Constraints

Shift constraints left — catch them before the program runs.

### C — Compiler Warnings as Constraint Enforcement

```c
/* Minimum recommended flags for production C:
 *
 * -std=c11 -Wall -Wextra -Wpedantic
 * -Wshadow              (variable shadows outer scope)
 * -Wstrict-prototypes   (all function prototypes must specify types)
 * -Wmissing-prototypes  (no function without a prior declaration)
 * -Wnull-dereference    (possible null dereference detected)
 * -Warray-bounds        (out-of-bounds array access)
 * -Wformat=2            (strict printf/scanf format checking)
 * -Wconversion          (implicit type conversions that may lose data)
 * -Werror               (treat all warnings as errors in CI)
 *
 * For security-sensitive code add:
 * -D_FORTIFY_SOURCE=2   (runtime buffer overflow detection in libc)
 * -fstack-protector-strong
 * -fsanitize=address,undefined  (in development builds)
 */

/* ============================================================
 * PATTERN: __attribute__ annotations for constraint hints
 * ============================================================ */

/* Tells the compiler this function never returns NULL */
__attribute__((returns_nonnull))
void *xmalloc(size_t size) {
    void *p = malloc(size);
    if (!p) { abort(); }
    return p;
}

/* Tells the compiler these parameters must not be NULL */
__attribute__((nonnull(1, 2)))
int copy_node(BinaryNode *dst, const BinaryNode *src) {
    /* The compiler can warn if a NULL is passed here */
    dst->data  = src->data;
    dst->left  = src->left;
    dst->right = src->right;
    return 0;
}

/* Mark unused parameters to suppress -Wunused-parameter */
void callback(int event, void *user_data __attribute__((unused))) {
    printf("event: %d\n", event);
}

/* Warn if return value is ignored */
__attribute__((warn_unused_result))
int must_check(void) { return 42; }
```

### Go — go vet, staticcheck, and golangci-lint

```go
// go vet catches:
//   - incorrect format verbs in Printf calls
//   - unreachable code after return/panic
//   - misuse of sync primitives (unlock not deferred)
//   - copying of sync.Mutex
//
// staticcheck (honnef.co/go/tools) catches:
//   - ineffective code (assigning to _ when error should be checked)
//   - deprecated API usage
//   - always-true/false conditions
//
// golangci-lint aggregates 50+ linters:
//   errcheck, gocritic, gosec, revive, unused, etc.

// Example of what go vet catches:
func badUsage(t *SafeTree) {
    var mu sync.Mutex
    // go vet: copies lock value
    // mu2 := mu  // BUG: Mutex must not be copied after first use
    mu.Lock()
    defer mu.Unlock()
    _ = t
}
```

### Rust — Clippy and the Type System as Static Analyser

```rust
// Rust's type system catches at compile time what other languages
// catch at runtime (or miss entirely):
//
// rustc:
//   - All ownership/lifetime errors
//   - All type mismatches
//   - Dead code, unused variables (warnings)
//   - Exhaustiveness of match expressions
//
// cargo clippy (300+ lints):
//   - Idiomatic issues: map(|x| x.clone()) → cloned()
//   - Performance: unnecessary allocations
//   - Correctness: integer overflow in literals, panicking unwrap()
//   - Complexity: overly nested if/else chains

// Example: clippy catches redundant clone
fn clippy_example(opt: Option<String>) -> Option<String> {
    opt.map(|s| s.clone())  // clippy: use .cloned() instead
    // Better: opt  (Option<String> is already moved)
}

// Rustdoc tests — constraints verified via documentation examples
/// Inserts a value into the tree.
///
/// # Errors
/// Returns [`TreeError::OutOfRange`] if `data` is outside `[-1000, 1000]`.
///
/// # Examples
/// ```
/// # use mylib::{RangedTree, TreeError};
/// let mut tree = RangedTree::new(-100, 100).unwrap();
/// assert!(tree.insert(50).is_ok());
/// assert!(matches!(tree.insert(200), Err(TreeError::OutOfRange { .. })));
/// ```
pub fn documented_insert(/* ... */) { }
```

---

## 17. Testing as Constraint Verification

Tests are executable specifications. They verify that constraints hold across the full range of inputs.

### C — Unit Testing with Assertions

```c
#include <assert.h>
#include <stdio.h>

/* Simple test runner — or use Unity, Check, or cmocka */
#define TEST(name) void test_##name(void)
#define RUN_TEST(name) do { \
    printf("  %-40s", #name); \
    test_##name(); \
    printf("PASS\n"); \
} while(0)

TEST(new_node_initialises_correctly) {
    BinaryNode *n = new_node(42);
    assert(n != NULL);
    assert(n->data  == 42);
    assert(n->left  == NULL);
    assert(n->right == NULL);
    free_tree(n);
}

TEST(inorder_empty_tree) {
    /* Constraint: inorder on NULL must not crash */
    inorder(NULL);  /* If this crashes, constraint is violated */
}

TEST(tree_height_leaf) {
    BinaryNode *n = new_node(1);
    assert(tree_height(n) == 0);
    free_tree(n);
}

TEST(tree_height_null) {
    /* Constraint: height of empty tree is -1 */
    assert(tree_height(NULL) == -1);
}

int main(void) {
    printf("Running tree tests...\n");
    RUN_TEST(new_node_initialises_correctly);
    RUN_TEST(inorder_empty_tree);
    RUN_TEST(tree_height_leaf);
    RUN_TEST(tree_height_null);
    printf("All tests passed.\n");
    return 0;
}
```

### Go — Table-Driven Tests and Property Tests

```go
package tree_test

import (
    "testing"
    "github.com/yourpkg/tree"
)

// ============================================================
// Table-driven tests — idiomatic Go
// ============================================================
func TestTreeHeight(t *testing.T) {
    tests := []struct {
        name     string
        build    func() *tree.SafeTree
        expected int
    }{
        {
            name:     "empty tree",
            build:    func() *tree.SafeTree { return &tree.SafeTree{} },
            expected: -1,
        },
        // ... more cases
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            tr := tt.build()
            got := tr.Height()
            if got != tt.expected {
                t.Errorf("Height() = %d, want %d", got, tt.expected)
            }
        })
    }
}

// ============================================================
// Property-based testing with rapid
// ============================================================
// go get github.com/leanovate/gopter
//
// func TestBSTInsertProperty(t *testing.T) {
//     properties := gopter.NewProperties(nil)
//     properties.Property("all inserted values are findable", prop.ForAll(
//         func(values []int) bool {
//             tr := &SafeTree{}
//             for _, v := range values { tr.Insert(v) }
//             for _, v := range values {
//                 if n, _ := tr.Find(v); n == nil { return false }
//             }
//             return true
//         },
//         gen.SliceOf(gen.Int()),
//     ))
//     properties.TestingRun(t)
// }
```

### Rust — Built-in Tests, Property Tests, and Fuzzing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // ============================================================
    // Unit tests — built into the language
    // ============================================================
    #[test]
    fn new_node_has_no_children() {
        let n = BinaryNode::new(42);
        assert_eq!(n.data, 42);
        assert!(n.left.is_none());
        assert!(n.right.is_none());
    }

    #[test]
    fn height_of_single_node_is_zero() {
        assert_eq!(BinaryNode::new(1).height(), 0);
    }

    #[test]
    fn ranged_tree_rejects_out_of_range() {
        let mut t = RangedTree::new(-10, 10).unwrap();
        let err = t.insert(100).unwrap_err();
        assert!(matches!(err, TreeError::OutOfRange { data: 100, .. }));
    }

    #[test]
    #[should_panic(expected = "insert_sorted: precondition violated")]
    fn insert_sorted_panics_on_unsorted_input() {
        let mut v = vec![3, 1, 2]; // unsorted
        insert_sorted(&mut v, 0);
    }

    // ============================================================
    // Property tests with proptest crate
    // ============================================================
    // use proptest::prelude::*;
    //
    // proptest! {
    //     #[test]
    //     fn bst_find_after_insert(data in -1000_i32..1000) {
    //         let mut t = RangedTree::new(-1001, 1001).unwrap();
    //         t.insert(data).unwrap();
    //         prop_assert!(t.contains(data));
    //     }
    // }
}
```

---

## 18. Summary: Decision Matrix

Use this matrix to choose the right constraint mechanism for any situation.

| Constraint Type | C | Go | Rust |
|---|---|---|---|
| **Value is absent** | `NULL` pointer + null check | `nil` check or `(value, bool)` | `Option<T>` |
| **Operation may fail** | Return code + `errno` | `return value, error` | `Result<T, E>` |
| **Programmer bug** | `assert()` / `abort()` | `panic()` | `assert!()` / `panic!()` |
| **Precondition on args** | `assert()` or guard + return | Guard clause + return error | Guard clause + `Err(...)` |
| **Type range constraint** | Typedef + runtime check | Custom type + constructor | Newtype + constructor |
| **Illegal state** | Opaque struct + constructor | Unexported fields + constructor | Private fields + constructor |
| **Compile-time shape check** | `_Static_assert` | Compile-time interface check | `const {}` / `static_assertions` |
| **Memory safety** | ASan + Valgrind + discipline | Built-in (GC + bounds checks) | Borrow checker (compile time) |
| **Thread safety** | `pthread_mutex` + discipline | `sync.Mutex` + `-race` flag | `Arc<Mutex<T>>` + `Send`/`Sync` |
| **Exhaustive branching** | `-Wswitch-enum` warning | `switch` (not enforced) | `match` (compiler enforced) |
| **API contract** | Header comments + assert | Interface + documentation | Trait + type + doc tests |
| **Performance-free safety** | Impossible in C | Mostly (except GC) | Zero-cost abstractions |

### Key Principles (Language-Agnostic)

1. **Make illegal states unrepresentable** — design your types so invalid values cannot be constructed.
2. **Fail fast, fail loudly** — a panic or abort near the root cause is better than silent corruption propagated through 10 stack frames.
3. **Separate programming errors from runtime failures** — assertions are for bugs; errors are for expected failures.
4. **Guard clauses flatten your code** — validate constraints at entry, then write the happy path.
5. **The earlier the constraint is checked, the cheaper the fix** — prefer compile time over runtime, startup over deep runtime.
6. **Constraints are documentation** — an assert, a type annotation, or an error return communicates the contract to every future reader.
7. **Test the boundaries** — unit tests should specifically target the edges of each constraint: at, just below, and just above the valid range.

Now let me write the comprehensive guide as a `.md` file.The guide is ~1,800 lines covering every layer of the constraint stack across all three languages. Here's the conceptual map of what's inside:

**Foundational patterns (Sections 2–4)**
The document starts exactly where your code snippet does — the `if (node == NULL) return` guard — and explains *why* it works, then shows the equivalent in Go (nil receiver methods, the nil interface trap) and Rust (`Option<T>` with exhaustive pattern matching and combinators like `map`, `and_then`, `?`).

**Propagation architecture (Sections 5–6)**
How errors travel through a call stack: C's `errno`/return-code pattern, Go's `(value, error)` multi-return with `fmt.Errorf("%w", ...)` wrapping chains, and Rust's `Result<T, E>` with `?` chaining, `map_err`, and `collect::<Result<>>()` for iterator pipelines.

**Type-system constraints (Sections 7–10)**
The real power comes from making violations impossible to compile. Newtypes in Rust, phantom types (encoding validated/unvalidated state), sealed traits, const-generics for array sizes, opaque structs in C, and the builder pattern with validation gates.

**When to panic vs. return error (Section 11)** — the matrix that matters most for API design.

**Compile-time enforcement (Section 16)**
Compiler flags for C (`-fsanitize=address,undefined`, `-Wnull-dereference`), Go tooling (`go vet`, `staticcheck`, the race detector), and Rust's clippy + the borrow checker as a built-in static analyser.

The key architectural takeaway is the shift in each language's philosophy: C requires you to *manually reproduce* the constraint everywhere; Go lets you *propagate* it structurally; Rust lets you *encode* it into the type so the compiler verifies it for free.