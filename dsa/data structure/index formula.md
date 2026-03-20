# 📐 Index Formula — The Complete DSA Master Guide

> *"The difference between a novice and an expert is not just knowledge — it is the mental model they carry.  
> Index formulas are the skeleton of every data structure. Master them, and you master the architecture of computation."*

---

## 📋 Table of Contents

1. [What is an Index Formula?](#1-what-is-an-index-formula)
2. [Mental Model: Memory as a Tape](#2-mental-model-memory-as-a-tape)
3. [1D Array Indexing](#3-1d-array-indexing)
4. [2D Array Indexing — Row-Major & Column-Major](#4-2d-array-indexing)
5. [3D Array Indexing](#5-3d-array-indexing)
6. [Triangular Matrix Indexing](#6-triangular-matrix-indexing)
7. [Symmetric Matrix Compact Storage](#7-symmetric-matrix-compact-storage)
8. [Tridiagonal Matrix Indexing](#8-tridiagonal-matrix-indexing)
9. [Binary Heap Index Formulas](#9-binary-heap-index-formulas)
10. [K-ary Heap Index Formulas](#10-k-ary-heap-index-formulas)
11. [Segment Tree Indexing](#11-segment-tree-indexing)
12. [Fenwick Tree (BIT) Indexing](#12-fenwick-tree-bit-indexing)
13. [Sparse Table Indexing](#13-sparse-table-indexing)
14. [Binary Search Mid-Point Formula](#14-binary-search-mid-point-formula)
15. [Circular Buffer / Ring Queue Index](#15-circular-buffer--ring-queue-index)
16. [Hash Table Index Formula](#16-hash-table-index-formula)
17. [Trie Node Index Formula](#17-trie-node-index-formula)
18. [Skip List Level Index](#18-skip-list-level-index)
19. [Disjoint Set (Union-Find) Indexing](#19-disjoint-set-union-find-indexing)
20. [Van Emde Boas Tree Indexing](#20-van-emde-boas-tree-indexing)
21. [Off-by-One Errors — A Deep Study](#21-off-by-one-errors--a-deep-study)
22. [Integer Overflow in Index Computation](#22-integer-overflow-in-index-computation)
23. [Master Comparison Table](#23-master-comparison-table)
24. [Cognitive & Practice Strategies](#24-cognitive--practice-strategies)

---

## 1. What is an Index Formula?

### Definition

An **index formula** is a mathematical function that maps a **logical position** (e.g., row, column, level, key) to a **physical memory offset** (an integer position in a flat array or memory block).

```
index_formula: (logical_coordinates) → physical_address (integer)
```

### Why does it matter?

Modern CPUs access **contiguous memory** fastest (cache lines). Every complex data structure — heaps, trees, matrices, queues — is ultimately stored in a flat array. The index formula is the **bridge** between the logical structure you reason about and the physical memory your CPU touches.

```
┌─────────────────────────────────────────────────────────────┐
│  LOGICAL STRUCTURE          PHYSICAL MEMORY (flat array)    │
│                                                             │
│  Matrix [row][col]   ───►  array[row * cols + col]          │
│  Heap node at i      ───►  array[i]                         │
│  Circular queue      ───►  array[(front + i) % capacity]    │
│  Segment tree node   ───►  array[2*i], array[2*i+1]         │
└─────────────────────────────────────────────────────────────┘
```

### Three Properties a Good Index Formula Must Have

| Property | Meaning |
|---|---|
| **Injective** | Different logical positions → different physical indices (no collision) |
| **Surjective** | All physical slots are reachable (no wasted memory) |
| **Computable in O(1)** | Must be fast — ideally one multiply + one add |

---

## 2. Mental Model: Memory as a Tape

RAM (Random Access Memory) is physically a **single long tape of bytes**. Each cell has an address (index). When you declare `int arr[100]`, you get 100 consecutive slots.

```
Physical Memory (conceptual tape):
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │10 │11 │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
  ▲                   ▲               ▲
  │                   │               │
  └── arr[0]          └── arr[4]      └── arr[8]
```

**Key Insight**: A 2D matrix, a binary heap, a segment tree — all of them are stored in this tape. The index formula tells you **where** on the tape each logical element lives.

---

## 3. 1D Array Indexing

### What is a 1D Array?

A **1D array** is the most primitive structure — a sequence of `n` elements, indexed from `0` to `n-1` (0-based) or `1` to `n` (1-based).

### Formula

```
0-based:  element at position i  →  base_address + i * element_size
1-based:  element at position i  →  base_address + (i-1) * element_size
```

In code (using array notation), we simply write `arr[i]`. The compiler automatically multiplies by `sizeof(element)`.

### ASCII Diagram

```
Array:   [10, 20, 30, 40, 50]
Index:     0   1   2   3   4

Memory:
┌────┬────┬────┬────┬────┐
│ 10 │ 20 │ 30 │ 40 │ 50 │
└────┴────┴────┴────┴────┘
  [0]  [1]  [2]  [3]  [4]

Address of arr[i] = base + i * sizeof(T)
```

### Implementation

**C:**
```c
#include <stdio.h>

int main() {
    int arr[] = {10, 20, 30, 40, 50};
    int n = 5;

    // Access element at index i
    for (int i = 0; i < n; i++) {
        // arr[i] is syntactic sugar for *(arr + i)
        printf("arr[%d] = %d  |  address = %p\n",
               i, arr[i], (void*)&arr[i]);
    }
    return 0;
}
```

**Rust:**
```rust
fn main() {
    let arr = [10i32, 20, 30, 40, 50];
    let n = arr.len();

    for i in 0..n {
        // Rust enforces bounds checking at runtime in debug mode
        println!("arr[{}] = {}  |  address = {:p}", i, arr[i], &arr[i]);
    }
}
```

**Go:**
```go
package main

import "fmt"

func main() {
    arr := []int{10, 20, 30, 40, 50}

    for i := 0; i < len(arr); i++ {
        fmt.Printf("arr[%d] = %d\n", i, arr[i])
    }
}
```

### Key Insight: Pointer Arithmetic

`arr[i]` is literally `*(arr + i)` in C. This means the CPU computes:
```
physical_address = base_pointer + i * sizeof(element_type)
```
This is O(1) — constant time regardless of array size.

---

## 4. 2D Array Indexing

### Conceptual Problem

A 2D matrix has rows and columns. But memory is 1D (a tape). We must **flatten** 2D coordinates `(row, col)` to a single integer index.

There are two standard ways: **Row-Major** and **Column-Major**.

---

### 4.1 Row-Major Order (C, Rust, Go, Java)

In **row-major** order, all elements of row 0 come first, then row 1, then row 2, etc.

```
Matrix (3×4):
         col0  col1  col2  col3
row 0  [  1,    2,    3,    4  ]
row 1  [  5,    6,    7,    8  ]
row 2  [  9,   10,   11,   12  ]

Stored in memory (row-major):
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬────┬────┬────┐
│ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │ 10 │ 11 │ 12 │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴────┴────┴────┘
  0   1   2   3   4   5   6   7   8    9   10   11
  ◄── row 0 ──► ◄── row 1 ──► ◄──── row 2 ────►
```

### Formula (Row-Major)

```
index(row, col) = row * num_cols + col
```

**Derivation:** To reach row `r`, skip `r` full rows (each row has `num_cols` elements). Then move `col` steps inside that row.

```
Logical:  (row=1, col=2)
Formula:  1 * 4 + 2 = 6
Memory:   arr[6] = 7  ✓
```

---

### 4.2 Column-Major Order (Fortran, MATLAB, Julia)

In **column-major** order, all elements of column 0 come first, then column 1, etc.

```
Same Matrix (3×4):
         col0  col1  col2  col3
row 0  [  1,    2,    3,    4  ]
row 1  [  5,    6,    7,    8  ]
row 2  [  9,   10,   11,   12  ]

Stored in memory (column-major):
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬────┬────┬────┐
│ 1 │ 5 │ 9 │ 2 │ 6 │10 │ 3 │ 7 │11 │  4 │  8 │ 12 │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴────┴────┴────┘
  0   1   2   3   4   5   6   7   8    9   10   11
  ◄─ col0 ─► ◄─ col1 ─► ◄─ col2 ─► ◄── col3 ──►
```

### Formula (Column-Major)

```
index(row, col) = col * num_rows + row
```

---

### 4.3 Performance: Why Row-Major vs Column-Major Matters

**Cache lines**: CPUs load memory in chunks (~64 bytes). If you access memory sequentially, you get **cache hits**. If you jump around, you get **cache misses** (100x slower).

```
Iterating a 3×4 matrix row by row (outer=row, inner=col):
  Row-major:    Access pattern = 0,1,2,3,4,5,6,7,8,9,10,11  → SEQUENTIAL ✅ Fast
  Column-major: Access pattern = 0,4,8, 1,5,9, 2,6,10, ...   → JUMPING   ❌ Slow
```

**Decision Tree for Cache Performance:**

```
Is your inner loop iterating by column?
├── YES → Store row-major (C/Rust/Go default)   → cache-friendly ✅
└── NO  → Store column-major (Fortran/MATLAB)   → cache-friendly ✅

Always: inner loop stride = 1 for best performance
```

---

### C Implementation (2D Array)

```c
#include <stdio.h>
#define ROWS 3
#define COLS 4

int main() {
    // C stores 2D arrays in row-major order automatically
    int matrix[ROWS][COLS] = {
        { 1,  2,  3,  4},
        { 5,  6,  7,  8},
        { 9, 10, 11, 12}
    };

    // Manual index formula (for understanding)
    int flat[ROWS * COLS];
    for (int r = 0; r < ROWS; r++) {
        for (int c = 0; c < COLS; c++) {
            int index = r * COLS + c;   // <-- THE INDEX FORMULA
            flat[index] = matrix[r][c];
            printf("matrix[%d][%d] → flat[%d] = %d\n", r, c, index, flat[index]);
        }
    }
    return 0;
}
```

### Rust Implementation (2D Array)

```rust
fn main() {
    let rows = 3usize;
    let cols = 4usize;

    // Rust has no native 2D array dynamic allocation,
    // so we use a flat Vec with explicit index formula
    let matrix_data: Vec<i32> = vec![
         1,  2,  3,  4,
         5,  6,  7,  8,
         9, 10, 11, 12,
    ];

    // The index formula closure
    let idx = |r: usize, c: usize| -> usize { r * cols + c };

    for r in 0..rows {
        for c in 0..cols {
            println!(
                "matrix[{}][{}] = {} (flat index = {})",
                r, c,
                matrix_data[idx(r, c)],
                idx(r, c)
            );
        }
    }

    // Column-major access (for contrast)
    println!("\n--- Column-Major Access Order ---");
    for c in 0..cols {
        for r in 0..rows {
            print!("{:3} ", matrix_data[idx(r, c)]);
        }
        println!();
    }
}
```

### Go Implementation (2D Array)

```go
package main

import "fmt"

func main() {
    rows, cols := 3, 4

    // Flat storage with index formula
    matrix := []int{
         1,  2,  3,  4,
         5,  6,  7,  8,
         9, 10, 11, 12,
    }

    // Index formula as a function
    idx := func(r, c int) int {
        return r*cols + c
    }

    for r := 0; r < rows; r++ {
        for c := 0; c < cols; c++ {
            fmt.Printf("matrix[%d][%d] = %2d  (flat[%d])\n",
                r, c, matrix[idx(r, c)], idx(r, c))
        }
    }
}
```

---

## 5. 3D Array Indexing

### Concept

A 3D array has dimensions: **depth × rows × cols** (or layer × row × col).

Think of it as a book: depth = page number, row = line on page, col = character on line.

### ASCII Diagram

```
3D Array: depth=2, rows=3, cols=4

Layer 0 (depth=0):             Layer 1 (depth=1):
┌────┬────┬────┬────┐          ┌────┬────┬────┬────┐
│  1 │  2 │  3 │  4 │  row 0  │ 13 │ 14 │ 15 │ 16 │  row 0
├────┼────┼────┼────┤          ├────┼────┼────┼────┤
│  5 │  6 │  7 │  8 │  row 1  │ 17 │ 18 │ 19 │ 20 │  row 1
├────┼────┼────┼────┤          ├────┼────┼────┼────┤
│  9 │ 10 │ 11 │ 12 │  row 2  │ 21 │ 22 │ 23 │ 24 │  row 2
└────┴────┴────┴────┘          └────┴────┴────┴────┘
```

### Formula (Row-Major 3D)

```
index(depth, row, col) = depth * (rows * cols) + row * cols + col
```

**Derivation:**
- Each "layer" (depth slice) contains `rows * cols` elements → skip `depth * rows * cols`
- Within the layer, same as 2D: `row * cols + col`

```
Example: element at (depth=1, row=2, col=3)
  = 1 * (3 * 4) + 2 * 4 + 3
  = 12 + 8 + 3
  = 23
  → Value = 24 (1-indexed labels) ✓
```

### C Implementation

```c
#include <stdio.h>
#define D 2    // depth
#define R 3    // rows
#define C 4    // cols

int main() {
    // C handles 3D naturally, but let's see the formula
    int arr[D][R][C];
    int val = 1;
    for (int d = 0; d < D; d++)
        for (int r = 0; r < R; r++)
            for (int c = 0; c < C; c++)
                arr[d][r][c] = val++;

    // Manual flat representation
    // index formula: d*(R*C) + r*C + c
    printf("arr[1][2][3] = %d\n", arr[1][2][3]);
    int manual_idx = 1*(R*C) + 2*C + 3;
    printf("Manual index formula result: %d\n", manual_idx);
    // Both should give the same flat position
    return 0;
}
```

### Rust Implementation

```rust
fn main() {
    let d = 2usize; // depth
    let r = 3usize; // rows
    let c = 4usize; // cols

    // Initialize flat 3D array
    let mut arr: Vec<i32> = (1..=(d * r * c) as i32).collect();

    // Index formula
    let idx3d = |depth: usize, row: usize, col: usize| -> usize {
        depth * (r * c) + row * c + col
    };

    // Access element at (depth=1, row=2, col=3)
    println!("Element at (1,2,3) = {}", arr[idx3d(1, 2, 3)]);

    // Modify via formula
    arr[idx3d(0, 1, 2)] = 999;
    println!("After modification, (0,1,2) = {}", arr[idx3d(0, 1, 2)]);
}
```

---

## 6. Triangular Matrix Indexing

### What is a Triangular Matrix?

A **triangular matrix** is a square matrix where either the upper-right or lower-left portion is all zeros. We can save memory by storing only the non-zero triangle.

### 6.1 Lower Triangular Matrix

```
Lower Triangular (n=4):
┌                ┐
│ a00  0   0   0 │
│ a10 a11  0   0 │
│ a20 a21 a22  0 │
│ a30 a31 a32 a33│
└                ┘

Stored as a flat array (only the shaded region):
[ a00, a10, a11, a20, a21, a22, a30, a31, a32, a33 ]
   0    1    2    3    4    5    6    7    8    9

Row lengths: row 0 → 1 element, row 1 → 2, row 2 → 3, row 3 → 4
```

### Formula (Lower Triangular, 0-based)

To find the flat index of element `(row, col)` where `col <= row`:

```
Elements before row r = 0 + 1 + 2 + ... + r = r*(r+1)/2

index(row, col) = row*(row+1)/2 + col
```

**Derivation:**
- Rows 0 through row-1 have lengths 1, 2, ..., row → total = row*(row+1)/2
- Then within row `row`, element is at position `col`

```
Example: element (2, 1)
  = 2*(2+1)/2 + 1
  = 3 + 1
  = 4   → a21 ✓
```

**Memory savings:**
- Full matrix: n²
- Lower triangle: n*(n+1)/2
- For n=1000: 1,000,000 vs 500,500 → **~50% savings**

### 6.2 Upper Triangular Matrix

```
Upper Triangular (n=4):
┌                ┐
│ a00 a01 a02 a03│
│  0  a11 a12 a13│
│  0   0  a22 a23│
│  0   0   0  a33│
└                ┘

Stored flat (row by row, upper part only):
[ a00, a01, a02, a03, a11, a12, a13, a22, a23, a33 ]
   0    1    2    3    4    5    6    7    8    9
```

### Formula (Upper Triangular, 0-based)

For element `(row, col)` where `col >= row`:

```
Elements in rows 0..row-1 of upper triangle:
  Row 0 has n elements, row 1 has n-1, ..., row r-1 has n-(r-1)
  Total = n + (n-1) + ... + (n-r+1) = r*n - r*(r-1)/2

index(row, col) = row*n - row*(row-1)/2 + (col - row)
```

Simplified:
```
index(row, col) = row*(2n - row - 1)/2 + col
```

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

// Lower triangular matrix
int lower_tri_index(int row, int col) {
    // Only valid for col <= row
    if (col > row) return -1; // invalid
    return row * (row + 1) / 2 + col;
}

// Upper triangular matrix
int upper_tri_index(int row, int col, int n) {
    // Only valid for col >= row
    if (col < row) return -1; // invalid
    return row * (2 * n - row - 1) / 2 + col;
}

int main() {
    int n = 4;
    int lower_size = n * (n + 1) / 2;
    int* lower = (int*)calloc(lower_size, sizeof(int));

    // Fill lower triangle: a[i][j] = i*10 + j
    for (int r = 0; r < n; r++) {
        for (int c = 0; c <= r; c++) {
            lower[lower_tri_index(r, c)] = r * 10 + c;
        }
    }

    // Print
    printf("Lower Triangular Storage:\n");
    for (int i = 0; i < lower_size; i++)
        printf("%d ", lower[i]);
    printf("\n");

    printf("Element (2,1) = %d\n", lower[lower_tri_index(2, 1)]);

    free(lower);
    return 0;
}
```

### Rust Implementation

```rust
fn lower_tri_index(row: usize, col: usize) -> Option<usize> {
    if col > row {
        return None; // Not in lower triangle
    }
    Some(row * (row + 1) / 2 + col)
}

fn upper_tri_index(row: usize, col: usize, n: usize) -> Option<usize> {
    if col < row {
        return None; // Not in upper triangle
    }
    Some(row * (2 * n - row - 1) / 2 + col)
}

fn main() {
    let n = 4usize;
    let lower_size = n * (n + 1) / 2;
    let mut lower = vec![0i32; lower_size];

    // Fill lower triangle
    for r in 0..n {
        for c in 0..=r {
            if let Some(idx) = lower_tri_index(r, c) {
                lower[idx] = (r * 10 + c) as i32;
            }
        }
    }

    println!("Lower Triangular Flat Storage: {:?}", lower);
    println!("Element (2,1) = {}", lower[lower_tri_index(2, 1).unwrap()]);

    // Demonstrate upper triangular
    let upper_size = n * (n + 1) / 2;
    let mut upper = vec![0i32; upper_size];
    for r in 0..n {
        for c in r..n {
            if let Some(idx) = upper_tri_index(r, c, n) {
                upper[idx] = (r * 10 + c) as i32;
            }
        }
    }
    println!("Upper Triangular Flat Storage: {:?}", upper);
}
```

---

## 7. Symmetric Matrix Compact Storage

### Concept

A **symmetric matrix** satisfies: `A[i][j] == A[j][i]`. We only need to store the lower (or upper) triangle — half the elements.

```
Symmetric Matrix (n=3):
┌           ┐
│  1   5   9 │
│  5   2   6 │
│  9   6   3 │
└           ┘

Note: A[0][1] == A[1][0] == 5
      A[0][2] == A[2][0] == 9
      A[1][2] == A[2][1] == 6

Store only lower triangle:
[ 1, 5, 2, 9, 6, 3 ]
  (0,0)(1,0)(1,1)(2,0)(2,1)(2,2)
```

### Formula

Access `A[row][col]`:
```
if col <= row: index = row*(row+1)/2 + col
else:          index = col*(col+1)/2 + row   ← swap! because A[r][c] == A[c][r]
```

### C Implementation

```c
#include <stdio.h>

typedef struct {
    int* data;
    int  n;     // matrix dimension
} SymMatrix;

int sym_index(int row, int col) {
    // Always index into lower triangle
    if (col > row) {
        int tmp = row; row = col; col = tmp; // swap
    }
    return row * (row + 1) / 2 + col;
}

int sym_get(SymMatrix* m, int row, int col) {
    return m->data[sym_index(row, col)];
}

void sym_set(SymMatrix* m, int row, int col, int val) {
    // Setting one automatically sets both (because same storage)
    m->data[sym_index(row, col)] = val;
}

int main() {
    int n = 3;
    int size = n * (n + 1) / 2;
    int data[] = {1, 5, 2, 9, 6, 3};  // lower triangle

    SymMatrix m = {data, n};

    // Access A[0][2] and A[2][0] — should be identical
    printf("A[0][2] = %d\n", sym_get(&m, 0, 2));   // 9
    printf("A[2][0] = %d\n", sym_get(&m, 2, 0));   // 9 (same storage!)
    return 0;
}
```

---

## 8. Tridiagonal Matrix Indexing

### Concept

A **tridiagonal matrix** has non-zero elements only on:
- The **main diagonal** (i == j)
- The **super-diagonal** (j == i + 1)
- The **sub-diagonal** (j == i - 1)

```
Tridiagonal (n=5):
┌                    ┐
│ b0 c0  0  0  0    │
│ a1 b1 c1  0  0    │
│  0 a2 b2 c2  0    │
│  0  0 a3 b3 c3    │
│  0  0  0 a4 b4    │
└                    ┘

Store 3 arrays: a[] (sub), b[] (main), c[] (super)
Or store flat as: [a1,b0,c0, a2,b1,c1, a3,b2,c2, a4,b3,c3, b4]
```

### Compact Flat Storage Formula

Using **interleaved** storage (sub, main, super per row):

```
Total non-zeros = (n-1) + n + (n-1) = 3n - 2

For element (i, j):
  if j == i-1 (sub-diagonal):   index = 3*(j)     + 0
  if j == i   (main diagonal):  index = 3*(i)     + 1
  if j == i+1 (super-diagonal): index = 3*(i)     + 2
```

Memory savings vs full matrix (n=1000):
- Full: 1,000,000
- Tridiagonal: 2,997 (3n-3 elements)

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

// Tridiagonal matrix: store a (sub), b (main), c (super)
typedef struct {
    double* a;  // sub-diagonal,   size n-1 (indices 1..n-1)
    double* b;  // main diagonal,  size n
    double* c;  // super-diagonal, size n-1 (indices 0..n-2)
    int     n;
} TriMatrix;

double tri_get(TriMatrix* m, int i, int j) {
    if (j == i - 1 && i > 0)       return m->a[i];     // sub-diagonal
    if (j == i)                     return m->b[i];     // main diagonal
    if (j == i + 1 && i < m->n-1)  return m->c[i];     // super-diagonal
    return 0.0;                                         // zero elsewhere
}

int main() {
    int n = 5;
    double a[] = {0, 1, 2, 3, 4};   // a[1..4], a[0] unused
    double b[] = {10, 11, 12, 13, 14};  // main diagonal
    double c[] = {20, 21, 22, 23, 0};   // c[0..3], c[4] unused

    TriMatrix m = {a, b, c, n};

    printf("Element (2,1) [sub]   = %.1f\n", tri_get(&m, 2, 1));  // a[2] = 2
    printf("Element (2,2) [main]  = %.1f\n", tri_get(&m, 2, 2));  // b[2] = 12
    printf("Element (2,3) [super] = %.1f\n", tri_get(&m, 2, 3));  // c[2] = 22
    printf("Element (0,3) [zero]  = %.1f\n", tri_get(&m, 0, 3));  // 0
    return 0;
}
```

---

## 9. Binary Heap Index Formulas

### What is a Heap?

A **binary heap** is a complete binary tree stored in an array where:
- **Max-heap**: parent ≥ both children
- **Min-heap**: parent ≤ both children

**Complete binary tree**: all levels fully filled except possibly the last, which is filled left to right.

```
Binary Heap as Tree:
            10
          /    \
         9      8
        / \    / \
       7   6  5   4
      / \
     3   2

Stored as array (level-order, left to right):
[10, 9, 8, 7, 6, 5, 4, 3, 2]
  0  1  2  3  4  5  6  7  8
```

### 9.1 0-Based Index Formulas

For node at index `i`:

```
┌──────────────────────────────────────────────┐
│   0-BASED HEAP INDEX FORMULAS                │
├──────────────────────────────────────────────┤
│   Parent:       (i - 1) / 2                  │
│   Left child:   2 * i + 1                    │
│   Right child:  2 * i + 2                    │
│   Root:         index 0                      │
│   Last leaf:    n - 1                        │
│   Last non-leaf (last parent): (n/2) - 1     │
└──────────────────────────────────────────────┘
```

**Verification with diagram:**

```
Index:    0   1   2   3   4   5   6   7   8
Value:   [10,  9,  8,  7,  6,  5,  4,  3,  2]

Node at index 1 (value=9):
  Parent    = (1-1)/2 = 0     → value 10 ✓
  Left      = 2*1+1   = 3     → value 7  ✓
  Right     = 2*1+2   = 4     → value 6  ✓

Node at index 3 (value=7):
  Parent    = (3-1)/2 = 1     → value 9  ✓
  Left      = 2*3+1   = 7     → value 3  ✓
  Right     = 2*3+2   = 8     → value 2  ✓
```

### 9.2 1-Based Index Formulas

Many textbooks use 1-based indexing (wasting index 0):

```
┌──────────────────────────────────────────────┐
│   1-BASED HEAP INDEX FORMULAS                │
├──────────────────────────────────────────────┤
│   Parent:       i / 2                        │
│   Left child:   2 * i                        │
│   Right child:  2 * i + 1                    │
│   Root:         index 1                      │
│   Last non-leaf: n / 2                       │
└──────────────────────────────────────────────┘
```

**Why 1-based is simpler:** `left = 2*i` is beautiful — just a left-bit-shift. `right = 2*i+1` adds one bit. This is deeply elegant.

### 9.3 Bit-Shift Optimization

```
0-based:
  left(i)  = 2*i + 1  = (i << 1) | 1
  right(i) = 2*i + 2  = (i << 1) + 2

1-based:
  left(i)  = 2*i      = i << 1
  right(i) = 2*i + 1  = (i << 1) | 1
  parent(i)= i/2      = i >> 1
```

### Decision Tree: Are We Within Bounds?

```
Given heap of size n (0-based):

Has left child?
  └─ condition: 2*i + 1 < n

Has right child?
  └─ condition: 2*i + 2 < n

Is node a leaf?
  └─ condition: 2*i + 1 >= n  (no left child means no children)

Is node valid (in bounds)?
  └─ condition: 0 <= i < n
```

### C Implementation (Min-Heap with all formulas)

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct {
    int* data;
    int  size;
    int  capacity;
} MinHeap;

// 0-based index formulas
static inline int parent(int i)      { return (i - 1) / 2; }
static inline int left_child(int i)  { return 2 * i + 1; }
static inline int right_child(int i) { return 2 * i + 2; }
static inline bool has_left(int i, int n)  { return left_child(i) < n; }
static inline bool has_right(int i, int n) { return right_child(i) < n; }
static inline bool is_root(int i)    { return i == 0; }
static inline int last_non_leaf(int n) { return n / 2 - 1; }

void swap(int* a, int* b) { int t = *a; *a = *b; *b = t; }

void heapify_up(MinHeap* h, int i) {
    // Bubble up until parent is smaller or we reach root
    while (!is_root(i) && h->data[parent(i)] > h->data[i]) {
        swap(&h->data[parent(i)], &h->data[i]);
        i = parent(i);
    }
}

void heapify_down(MinHeap* h, int i) {
    int smallest = i;
    int l = left_child(i);
    int r = right_child(i);

    if (l < h->size && h->data[l] < h->data[smallest]) smallest = l;
    if (r < h->size && h->data[r] < h->data[smallest]) smallest = r;

    if (smallest != i) {
        swap(&h->data[i], &h->data[smallest]);
        heapify_down(h, smallest);
    }
}

void heap_insert(MinHeap* h, int val) {
    h->data[h->size++] = val;
    heapify_up(h, h->size - 1);
}

int heap_extract_min(MinHeap* h) {
    int min = h->data[0];
    h->data[0] = h->data[--h->size];
    heapify_down(h, 0);
    return min;
}

void print_heap(MinHeap* h) {
    printf("Heap [size=%d]: ", h->size);
    for (int i = 0; i < h->size; i++)
        printf("%d ", h->data[i]);
    printf("\n");
    printf("Parent-Child relationships:\n");
    for (int i = 0; i <= last_non_leaf(h->size); i++) {
        printf("  [%d]=%d → L:[%d]=%d",
               i, h->data[i],
               left_child(i), h->data[left_child(i)]);
        if (has_right(i, h->size))
            printf(", R:[%d]=%d", right_child(i), h->data[right_child(i)]);
        printf("\n");
    }
}

int main() {
    int cap = 20;
    int* data = (int*)malloc(cap * sizeof(int));
    MinHeap h = {data, 0, cap};

    int values[] = {10, 9, 8, 7, 6, 5, 4, 3, 2};
    for (int i = 0; i < 9; i++) heap_insert(&h, values[i]);

    print_heap(&h);

    printf("\nExtract min: %d\n", heap_extract_min(&h));
    print_heap(&h);

    free(data);
    return 0;
}
```

### Rust Implementation (Binary Heap)

```rust
pub struct MinHeap {
    data: Vec<i32>,
}

impl MinHeap {
    pub fn new() -> Self { MinHeap { data: Vec::new() } }

    // 0-based index formulas
    fn parent(i: usize) -> usize { (i - 1) / 2 }
    fn left(i: usize) -> usize { 2 * i + 1 }
    fn right(i: usize) -> usize { 2 * i + 2 }

    pub fn insert(&mut self, val: i32) {
        self.data.push(val);
        self.bubble_up(self.data.len() - 1);
    }

    fn bubble_up(&mut self, mut i: usize) {
        while i > 0 {
            let p = Self::parent(i);
            if self.data[p] > self.data[i] {
                self.data.swap(p, i);
                i = p;
            } else {
                break;
            }
        }
    }

    pub fn extract_min(&mut self) -> Option<i32> {
        if self.data.is_empty() { return None; }
        let n = self.data.len();
        self.data.swap(0, n - 1);
        let min = self.data.pop();
        if !self.data.is_empty() {
            self.sink_down(0);
        }
        min
    }

    fn sink_down(&mut self, mut i: usize) {
        let n = self.data.len();
        loop {
            let mut smallest = i;
            let l = Self::left(i);
            let r = Self::right(i);

            if l < n && self.data[l] < self.data[smallest] { smallest = l; }
            if r < n && self.data[r] < self.data[smallest] { smallest = r; }

            if smallest != i {
                self.data.swap(i, smallest);
                i = smallest;
            } else {
                break;
            }
        }
    }

    pub fn print_structure(&self) {
        println!("Heap: {:?}", self.data);
        let n = self.data.len();
        for i in 0..(n / 2) {
            let l = Self::left(i);
            let r = Self::right(i);
            print!("  [{}]={}", i, self.data[i]);
            if l < n { print!(" → L[{}]={}", l, self.data[l]); }
            if r < n { print!(", R[{}]={}", r, self.data[r]); }
            println!();
        }
    }
}

fn main() {
    let mut heap = MinHeap::new();
    for val in [10, 9, 8, 7, 6, 5, 4, 3, 2] {
        heap.insert(val);
    }
    heap.print_structure();

    println!("\nExtract: {:?}", heap.extract_min());
    heap.print_structure();
}
```

### Go Implementation (Binary Heap)

```go
package main

import "fmt"

type MinHeap struct {
    data []int
}

func (h *MinHeap) parent(i int) int    { return (i - 1) / 2 }
func (h *MinHeap) left(i int) int      { return 2*i + 1 }
func (h *MinHeap) right(i int) int     { return 2*i + 2 }

func (h *MinHeap) Insert(val int) {
    h.data = append(h.data, val)
    h.bubbleUp(len(h.data) - 1)
}

func (h *MinHeap) bubbleUp(i int) {
    for i > 0 {
        p := h.parent(i)
        if h.data[p] > h.data[i] {
            h.data[p], h.data[i] = h.data[i], h.data[p]
            i = p
        } else {
            break
        }
    }
}

func (h *MinHeap) ExtractMin() (int, bool) {
    if len(h.data) == 0 {
        return 0, false
    }
    n := len(h.data)
    min := h.data[0]
    h.data[0] = h.data[n-1]
    h.data = h.data[:n-1]
    if len(h.data) > 0 {
        h.sinkDown(0)
    }
    return min, true
}

func (h *MinHeap) sinkDown(i int) {
    n := len(h.data)
    for {
        smallest := i
        l, r := h.left(i), h.right(i)
        if l < n && h.data[l] < h.data[smallest] { smallest = l }
        if r < n && h.data[r] < h.data[smallest] { smallest = r }
        if smallest != i {
            h.data[i], h.data[smallest] = h.data[smallest], h.data[i]
            i = smallest
        } else {
            break
        }
    }
}

func main() {
    h := &MinHeap{}
    for _, v := range []int{10, 9, 8, 7, 6, 5, 4, 3, 2} {
        h.Insert(v)
    }
    fmt.Println("Heap:", h.data)

    if min, ok := h.ExtractMin(); ok {
        fmt.Println("Extracted min:", min)
    }
    fmt.Println("After extraction:", h.data)
}
```

---

## 10. K-ary Heap Index Formulas

### Concept

A **k-ary heap** is a generalization where each node has at most `k` children (instead of 2).

```
3-ary (Ternary) Heap Example (k=3):

              1
          /   |   \
         2    3    4
       / | \ / | \
      5  6  7  8  9  10

Array: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
Index:  0  1  2  3  4  5  6  7  8   9
```

### Formulas (0-based, k-ary)

```
┌─────────────────────────────────────────────────┐
│   K-ARY HEAP INDEX FORMULAS (0-based)           │
├─────────────────────────────────────────────────┤
│   j-th child (0-indexed) of node i:             │
│     child(i, j) = k * i + j + 1   (j = 0..k-1) │
│                                                  │
│   Parent of node i:                             │
│     parent(i) = (i - 1) / k                     │
│                                                  │
│   First child of node i:                        │
│     first_child(i) = k * i + 1                  │
│                                                  │
│   Last child of node i:                         │
│     last_child(i) = k * i + k = k*(i+1)         │
│                                                  │
│   Last non-leaf:                                 │
│     last_non_leaf = (n - 2) / k                  │
└─────────────────────────────────────────────────┘
```

**Verification (k=3, node at index 1):**
```
Children:
  j=0: 3*1 + 0 + 1 = 4  ✓
  j=1: 3*1 + 1 + 1 = 5  ✓
  j=2: 3*1 + 2 + 1 = 6  ✓

Parent of index 5: (5-1)/3 = 1  ✓
```

### When to Use k-ary Heaps?

| k | Trade-off |
|---|---|
| k=2 | Classic, simple formulas, O(log₂ n) height |
| k=4 | ~25% fewer comparisons for extract-min, better cache (4 children fit one cache line) |
| k=8+ | Used in Fibonacci-style priority queues |

**Key insight**: A 4-ary heap has height ~log₄(n) = log₂(n)/2. Insertions are faster (less bubbling up). Extract-min is slightly slower (more children to compare). For Dijkstra's algorithm, 4-ary beats binary heap.

### C Implementation (K-ary Heap)

```c
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

#define K 3  // ternary heap

int kary_parent(int i)        { return (i - 1) / K; }
int kary_child(int i, int j)  { return K * i + j + 1; }  // j = 0..K-1

// Find minimum child (for min-heap extract)
int min_child(int* arr, int i, int n) {
    int fc = kary_child(i, 0);
    if (fc >= n) return -1; // no children

    int min_c = fc;
    for (int j = 1; j < K; j++) {
        int c = kary_child(i, j);
        if (c < n && arr[c] < arr[min_c])
            min_c = c;
    }
    return min_c;
}

// Heapify down
void kary_heapify_down(int* arr, int i, int n) {
    while (1) {
        int mc = min_child(arr, i, n);
        if (mc == -1 || arr[mc] >= arr[i]) break;
        int tmp = arr[i]; arr[i] = arr[mc]; arr[mc] = tmp;
        i = mc;
    }
}

// Build heap from array (O(n))
void kary_build_heap(int* arr, int n) {
    // Start from last non-leaf
    for (int i = (n - 2) / K; i >= 0; i--)
        kary_heapify_down(arr, i, n);
}

int main() {
    int arr[] = {10, 4, 7, 2, 8, 1, 5, 3, 9, 6};
    int n = 10;

    kary_build_heap(arr, n);

    printf("%d-ary heap: ", K);
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");

    // Show children of root (index 0)
    printf("Root: %d\n", arr[0]);
    for (int j = 0; j < K; j++) {
        int c = kary_child(0, j);
        if (c < n) printf("  Child %d: arr[%d] = %d\n", j, c, arr[c]);
    }
    return 0;
}
```

---

## 11. Segment Tree Indexing

### What is a Segment Tree?

A **segment tree** is a binary tree where:
- Each **leaf** represents a single element of the array
- Each **internal node** represents a range (segment) of elements
- Used for range queries (sum, min, max) and point updates in O(log n)

### 11.1 1-Based Indexing (Classic)

The root is at index `1`. For node at index `i`:

```
┌─────────────────────────────────────────────────┐
│   SEGMENT TREE INDEX FORMULAS (1-based)         │
├─────────────────────────────────────────────────┤
│   Left child:   2 * i                           │
│   Right child:  2 * i + 1                       │
│   Parent:       i / 2                           │
│   Root:         index 1                         │
│   Array size needed: 4 * n (safe upper bound)   │
└─────────────────────────────────────────────────┘
```

### Why Array Size = 4*n?

```
For n elements, the segment tree can have at most 2 * (next_power_of_2(n)) nodes.
next_power_of_2(n) <= 2n (when n is just above a power of 2)
So: 2 * 2n = 4n.

Example: n=5
  next_power_of_2(5) = 8
  Tree size = 2 * 8 = 16 (indices 1..15, index 0 wasted)
  4*5 = 20 > 16  → safe ✓
```

### ASCII Tree Diagram

```
Array: [2, 4, 1, 7, 3]  (indices 0..4)

Segment Tree (sum queries):
                    [0..4] = 17
                  /              \
          [0..2] = 7          [3..4] = 10
          /       \            /       \
      [0..1]=6  [2..2]=1  [3..3]=7  [4..4]=3
      /     \
  [0..0]=2 [1..1]=4

Array storage (1-based):
Index: 1   2   3   4   5   6   7   8   9   10
Value: 17  7   10  6   1   7   3   2   4   0
       ^root
```

### C Implementation (Sum Segment Tree)

```c
#include <stdio.h>
#include <stdlib.h>
#define MAXN 100005

int tree[4 * MAXN];  // 4*n safe upper bound
int arr[MAXN];

// Build: node covers [l, r]
void build(int node, int l, int r) {
    if (l == r) {
        tree[node] = arr[l];   // leaf: store element
        return;
    }
    int mid = (l + r) / 2;
    build(2 * node, l, mid);          // left child
    build(2 * node + 1, mid + 1, r);  // right child
    tree[node] = tree[2*node] + tree[2*node + 1];  // merge
}

// Range sum query [ql, qr]
int query(int node, int l, int r, int ql, int qr) {
    if (ql <= l && r <= qr) return tree[node]; // fully inside
    if (qr < l || r < ql)  return 0;           // fully outside
    int mid = (l + r) / 2;
    return query(2*node, l, mid, ql, qr)
         + query(2*node+1, mid+1, r, ql, qr);
}

// Point update: arr[pos] = val
void update(int node, int l, int r, int pos, int val) {
    if (l == r) {
        tree[node] = val;
        return;
    }
    int mid = (l + r) / 2;
    if (pos <= mid) update(2*node, l, mid, pos, val);
    else            update(2*node+1, mid+1, r, pos, val);
    tree[node] = tree[2*node] + tree[2*node+1];
}

int main() {
    int n = 5;
    int data[] = {2, 4, 1, 7, 3};
    for (int i = 0; i < n; i++) arr[i] = data[i];

    build(1, 0, n - 1);  // root at node 1

    printf("Sum [0..4] = %d\n", query(1, 0, n-1, 0, 4));  // 17
    printf("Sum [1..3] = %d\n", query(1, 0, n-1, 1, 3));  // 12

    update(1, 0, n-1, 2, 10);  // arr[2] = 10 (was 1)
    printf("After update: Sum [0..4] = %d\n", query(1, 0, n-1, 0, 4)); // 26
    return 0;
}
```

### Rust Implementation (Segment Tree)

```rust
struct SegTree {
    tree: Vec<i64>,
    n: usize,
}

impl SegTree {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut st = SegTree {
            tree: vec![0; 4 * n],
            n,
        };
        if n > 0 {
            st.build(arr, 1, 0, n - 1);
        }
        st
    }

    fn build(&mut self, arr: &[i64], node: usize, l: usize, r: usize) {
        if l == r {
            self.tree[node] = arr[l];
            return;
        }
        let mid = (l + r) / 2;
        self.build(arr, 2 * node, l, mid);
        self.build(arr, 2 * node + 1, mid + 1, r);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn query(&self, node: usize, l: usize, r: usize, ql: usize, qr: usize) -> i64 {
        if ql <= l && r <= qr { return self.tree[node]; }
        if qr < l || r < ql  { return 0; }
        let mid = (l + r) / 2;
        self.query(2 * node, l, mid, ql, qr)
            + self.query(2 * node + 1, mid + 1, r, ql, qr)
    }

    fn update(&mut self, node: usize, l: usize, r: usize, pos: usize, val: i64) {
        if l == r {
            self.tree[node] = val;
            return;
        }
        let mid = (l + r) / 2;
        if pos <= mid { self.update(2 * node, l, mid, pos, val); }
        else          { self.update(2 * node + 1, mid + 1, r, pos, val); }
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    pub fn range_sum(&self, ql: usize, qr: usize) -> i64 {
        self.query(1, 0, self.n - 1, ql, qr)
    }

    pub fn point_update(&mut self, pos: usize, val: i64) {
        self.update(1, 0, self.n - 1, pos, val);
    }
}

fn main() {
    let arr = vec![2i64, 4, 1, 7, 3];
    let mut st = SegTree::new(&arr);

    println!("Sum [0..4] = {}", st.range_sum(0, 4));   // 17
    println!("Sum [1..3] = {}", st.range_sum(1, 3));   // 12

    st.point_update(2, 10);  // arr[2] = 10
    println!("After update, Sum [0..4] = {}", st.range_sum(0, 4)); // 26
}
```

### Go Implementation (Segment Tree)

```go
package main

import "fmt"

type SegTree struct {
    tree []int
    n    int
}

func NewSegTree(arr []int) *SegTree {
    n := len(arr)
    st := &SegTree{tree: make([]int, 4*n), n: n}
    if n > 0 {
        st.build(arr, 1, 0, n-1)
    }
    return st
}

func (st *SegTree) build(arr []int, node, l, r int) {
    if l == r {
        st.tree[node] = arr[l]
        return
    }
    mid := (l + r) / 2
    st.build(arr, 2*node, l, mid)
    st.build(arr, 2*node+1, mid+1, r)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) query(node, l, r, ql, qr int) int {
    if ql <= l && r <= qr { return st.tree[node] }
    if qr < l || r < ql  { return 0 }
    mid := (l + r) / 2
    return st.query(2*node, l, mid, ql, qr) +
           st.query(2*node+1, mid+1, r, ql, qr)
}

func (st *SegTree) RangeSum(ql, qr int) int {
    return st.query(1, 0, st.n-1, ql, qr)
}

func main() {
    arr := []int{2, 4, 1, 7, 3}
    st := NewSegTree(arr)
    fmt.Println("Sum [0..4]:", st.RangeSum(0, 4))  // 17
    fmt.Println("Sum [1..3]:", st.RangeSum(1, 3))  // 12
}
```

---

## 12. Fenwick Tree (BIT) Indexing

### What is a Fenwick Tree?

A **Fenwick Tree** (Binary Indexed Tree, BIT) is a clever array-based structure for prefix sums with O(log n) query and update. It uses a magical property of binary representations.

### The Core Insight: Lowest Set Bit (LSB)

The **lowest set bit** (also called LSB or `lowbit`) of an integer `i` is:
```
lowbit(i) = i & (-i)
```

**Why does this work?**
- In two's complement: `-i = ~i + 1`
- `i & (-i)` isolates the rightmost set bit

```
i = 6  =  0110
-i= -6 =  1010  (two's complement)
i & (-i) = 0010 = 2  ← rightmost set bit ✓

i = 12 = 1100
-i= -12= 0100
i & (-i) = 0100 = 4  ✓
```

### BIT Index Formula

Each BIT node `tree[i]` stores the **sum of a range** of the original array:

```
tree[i] covers the range:
  [i - lowbit(i) + 1,  i]
  
  i.e., it covers lowbit(i) elements ending at i.
```

**Visualization (n=8):**

```
Index (1-based):  1    2    3    4    5    6    7    8
Binary:         001  010  011  100  101  110  111 1000
lowbit:           1    2    1    4    1    2    1    8

tree[1] = arr[1]                     (covers 1 element)
tree[2] = arr[1] + arr[2]            (covers 2 elements)
tree[3] = arr[3]                     (covers 1 element)
tree[4] = arr[1]+arr[2]+arr[3]+arr[4](covers 4 elements)
tree[5] = arr[5]                     (covers 1 element)
tree[6] = arr[5] + arr[6]            (covers 2 elements)
tree[7] = arr[7]                     (covers 1 element)
tree[8] = arr[1]+...+arr[8]          (covers 8 elements)
```

### BIT Operations

**Prefix sum query [1..i]:**
```
Walk i DOWN by removing LSB:
  sum = 0
  while i > 0:
    sum += tree[i]
    i -= lowbit(i)   ← remove lowest set bit
```

**Point update at position i:**
```
Walk i UP by adding LSB:
  while i <= n:
    tree[i] += delta
    i += lowbit(i)   ← add lowest set bit
```

**Query trace (prefix sum up to index 6):**
```
i=6  (110): sum += tree[6], i -= lowbit(6)=2 → i=4
i=4  (100): sum += tree[4], i -= lowbit(4)=4 → i=0
i=0: stop
```

### C Implementation (Fenwick Tree)

```c
#include <stdio.h>
#define MAXN 100005

int bit[MAXN];
int n;

// Lowest set bit
static inline int lowbit(int i) { return i & (-i); }

// Prefix sum [1..i]
int query(int i) {
    int sum = 0;
    for (; i > 0; i -= lowbit(i))
        sum += bit[i];
    return sum;
}

// Range sum [l..r]
int range_query(int l, int r) {
    return query(r) - query(l - 1);
}

// Point update: arr[i] += delta
void update(int i, int delta) {
    for (; i <= n; i += lowbit(i))
        bit[i] += delta;
}

// Build BIT from array (1-indexed)
void build(int* arr, int size) {
    n = size;
    for (int i = 1; i <= n; i++)
        update(i, arr[i]);
}

int main() {
    int arr[] = {0, 2, 4, 1, 7, 3};  // 1-indexed, arr[0] unused
    n = 5;
    build(arr, n);

    printf("Prefix sum [1..5] = %d\n", query(5));   // 17
    printf("Range sum  [2..4] = %d\n", range_query(2, 4));  // 12

    update(3, 9);  // arr[3] += 9 (1 → 10)
    printf("After update: prefix sum [1..5] = %d\n", query(5));  // 26
    return 0;
}
```

### Rust Implementation (Fenwick Tree)

```rust
pub struct FenwickTree {
    tree: Vec<i64>,
    n: usize,
}

impl FenwickTree {
    pub fn new(n: usize) -> Self {
        FenwickTree { tree: vec![0; n + 1], n }
    }

    pub fn from_slice(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut ft = FenwickTree::new(n);
        for (i, &val) in arr.iter().enumerate() {
            ft.update(i + 1, val); // 1-indexed
        }
        ft
    }

    fn lowbit(i: usize) -> usize {
        i & i.wrapping_neg()  // i & (-i) in usize
    }

    // Prefix sum [1..=i]
    pub fn query(&self, mut i: usize) -> i64 {
        let mut sum = 0i64;
        while i > 0 {
            sum += self.tree[i];
            i -= Self::lowbit(i);
        }
        sum
    }

    // Range sum [l..=r] (1-indexed)
    pub fn range_query(&self, l: usize, r: usize) -> i64 {
        self.query(r) - if l > 1 { self.query(l - 1) } else { 0 }
    }

    // Point update: arr[i] += delta (1-indexed)
    pub fn update(&mut self, mut i: usize, delta: i64) {
        while i <= self.n {
            self.tree[i] += delta;
            i += Self::lowbit(i);
        }
    }
}

fn main() {
    let arr = vec![2i64, 4, 1, 7, 3];
    let mut ft = FenwickTree::from_slice(&arr);

    println!("Prefix sum [1..5] = {}", ft.query(5));        // 17
    println!("Range sum  [2..4] = {}", ft.range_query(2, 4)); // 12

    ft.update(3, 9);  // arr[3] += 9
    println!("After update: prefix sum [1..5] = {}", ft.query(5)); // 26
}
```

---

## 13. Sparse Table Indexing

### Concept

A **sparse table** pre-computes range minimum (or maximum) queries in O(n log n) time and answers them in **O(1)** time. It uses the idea that any range can be covered by two overlapping power-of-2 length intervals.

### What is "Sparse"?

We store answers for intervals of length `2^k` starting at every possible position. These intervals are **sparse** compared to all possible intervals.

### Index Formula

```
sparse[i][j] = answer for interval [i, i + 2^j - 1]

              ← 2^j elements →
              [i ........... i + 2^j - 1]
```

**Building the table:**

```
Base case (j=0): each element alone
  sparse[i][0] = arr[i]

Recurrence (j>0): combine two half-length intervals
  sparse[i][j] = min(sparse[i][j-1], sparse[i + 2^(j-1)][j-1])
  
  Visual for j=2 (interval of length 4):
  [i ..... i+3]
  = min( [i .. i+1], [i+2 .. i+3] )
       sparse[i][1]  sparse[i+2][1]
```

**Querying [l, r]:**

```
k = floor(log2(r - l + 1))   ← largest power of 2 fitting in range

Answer = min(sparse[l][k], sparse[r - 2^k + 1][k])

Two overlapping intervals fully cover [l, r]:
[l .... l + 2^k - 1]
        [r - 2^k + 1 .... r]

Note: Overlapping is fine for min/max (idempotent operations)
```

### Log Table Pre-computation

```
log2_table[1] = 0
log2_table[i] = log2_table[i/2] + 1  for i >= 2
```

### C Implementation (Sparse Table)

```c
#include <stdio.h>
#include <math.h>
#include <string.h>

#define MAXN 100005
#define LOG  17  // log2(100000) < 17

int sparse[MAXN][LOG];
int log2_table[MAXN];
int n;

int min2(int a, int b) { return a < b ? a : b; }

void build(int* arr) {
    // Base case
    for (int i = 0; i < n; i++)
        sparse[i][0] = arr[i];

    // Fill table: j from 1 to LOG-1
    for (int j = 1; (1 << j) <= n; j++) {
        for (int i = 0; i + (1 << j) - 1 < n; i++) {
            // Combine two intervals of length 2^(j-1)
            sparse[i][j] = min2(sparse[i][j-1],
                                sparse[i + (1 << (j-1))][j-1]);
        }
    }

    // Pre-compute log2 table
    log2_table[1] = 0;
    for (int i = 2; i <= n; i++)
        log2_table[i] = log2_table[i / 2] + 1;
}

// O(1) range minimum query
int query(int l, int r) {
    int k = log2_table[r - l + 1];
    return min2(sparse[l][k], sparse[r - (1 << k) + 1][k]);
}

int main() {
    int arr[] = {2, 4, 1, 7, 3, 5, 6};
    n = 7;
    build(arr);

    printf("Min [0..6] = %d\n", query(0, 6));  // 1
    printf("Min [2..5] = %d\n", query(2, 5));  // 1
    printf("Min [3..6] = %d\n", query(3, 6));  // 3
    return 0;
}
```

### Rust Implementation (Sparse Table)

```rust
pub struct SparseTable {
    table: Vec<Vec<i32>>,
    log2: Vec<usize>,
    n: usize,
}

impl SparseTable {
    pub fn new(arr: &[i32]) -> Self {
        let n = arr.len();
        let log_n = if n > 1 { (n as f64).log2() as usize + 1 } else { 1 };

        // Build log2 table
        let mut log2 = vec![0usize; n + 1];
        for i in 2..=n {
            log2[i] = log2[i / 2] + 1;
        }

        // Build sparse table
        let mut table = vec![arr.to_vec()]; // j=0
        for j in 1..=log_n {
            let prev = &table[j - 1];
            let half = 1 << (j - 1);
            let row: Vec<i32> = (0..n)
                .map(|i| {
                    if i + (1 << j) <= n {
                        prev[i].min(prev[i + half])
                    } else {
                        prev[i]
                    }
                })
                .collect();
            table.push(row);
        }

        SparseTable { table, log2, n }
    }

    // O(1) range minimum query [l..=r]
    pub fn query(&self, l: usize, r: usize) -> i32 {
        let k = self.log2[r - l + 1];
        self.table[k][l].min(self.table[k][r + 1 - (1 << k)])
    }
}

fn main() {
    let arr = vec![2i32, 4, 1, 7, 3, 5, 6];
    let st = SparseTable::new(&arr);

    println!("Min [0..6] = {}", st.query(0, 6));  // 1
    println!("Min [2..5] = {}", st.query(2, 5));  // 1
    println!("Min [3..6] = {}", st.query(3, 6));  // 3
}
```

---

## 14. Binary Search Mid-Point Formula

### The Classic Bug: Integer Overflow

The most famous index formula bug in computing history is the **binary search midpoint overflow**.

### The Wrong Formula (Used Everywhere for Decades)

```c
int mid = (low + high) / 2;  // ❌ OVERFLOW BUG
```

**Problem**: If `low = 2,000,000,000` and `high = 2,100,000,000`, then `low + high = 4,100,000,000` which **overflows** a 32-bit signed integer (max ~2.1 billion).

This bug was in the Java standard library until 2006!

### The Safe Formulas

```
Formula 1 (subtraction-based):
  mid = low + (high - low) / 2

  Proof: high - low ≤ INT_MAX (since high ≤ INT_MAX and low ≥ 0)
         (high - low) / 2 ≤ INT_MAX / 2
         low + small_value → no overflow ✓

Formula 2 (bit-shift, unsigned):
  mid = (low + high) >>> 1   (unsigned right shift, Java)
  mid = ((unsigned)low + (unsigned)high) / 2  (C)

Formula 3 (average trick):
  mid = low + ((high - low) >> 1)   // shift for speed
```

### Decision Tree for Midpoint

```
Binary Search Midpoint Choice:
├── Type is signed 32-bit?
│   └── Use: mid = low + (high - low) / 2   ✓
├── Type is unsigned?
│   └── Use: mid = low + (high - low) / 2   ✓  (unsigned subtraction safe)
├── Type is 64-bit (i64/long)?
│   └── low + high rarely overflows, but still use safe formula
└── Performance critical?
    └── Use: mid = low + ((high - low) >> 1)  (bit shift ~= /2)
```

### Advanced: Upper Mid vs Lower Mid

In some binary searches (finding last occurrence), you need the **upper mid**:

```
Lower mid: low + (high - low) / 2     → rounds toward low
Upper mid: low + (high - low + 1) / 2 → rounds toward high

Example: low=3, high=4
  Lower: 3 + (4-3)/2 = 3 + 0 = 3  → picks 3
  Upper: 3 + (4-3+1)/2 = 3 + 1 = 4 → picks 4
```

**When to use upper mid**: When your `low = mid` case (shrinking from the left) would cause infinite loop with lower mid.

### C Implementation

```c
#include <stdio.h>
#include <limits.h>

// Safe binary search (find first occurrence)
int binary_search(int* arr, int n, int target) {
    int low = 0, high = n - 1;
    int result = -1;

    while (low <= high) {
        // SAFE: no overflow
        int mid = low + (high - low) / 2;

        if (arr[mid] == target) {
            result = mid;
            high = mid - 1;  // continue left for first occurrence
        } else if (arr[mid] < target) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }
    return result;
}

// Demonstrate overflow scenario
void overflow_demo() {
    int low  = 2000000000;
    int high = 2100000000;

    // Wrong:
    // int mid = (low + high) / 2;  // OVERFLOW: 4,100,000,000 > INT_MAX

    // Correct:
    int mid_safe = low + (high - low) / 2;
    printf("Safe mid = %d\n", mid_safe);  // 2,050,000,000 ✓
}

int main() {
    int arr[] = {1, 3, 5, 7, 9, 11, 13, 15};
    int n = 8;

    printf("Search 7: index %d\n", binary_search(arr, n, 7));   // 3
    printf("Search 1: index %d\n", binary_search(arr, n, 1));   // 0
    printf("Search 15: index %d\n", binary_search(arr, n, 15)); // 7
    printf("Search 6: index %d\n", binary_search(arr, n, 6));   // -1

    overflow_demo();
    return 0;
}
```

### Rust Implementation

```rust
fn binary_search_first(arr: &[i32], target: i32) -> Option<usize> {
    let mut low = 0usize;
    let mut high = arr.len();  // exclusive upper bound (half-open: [low, high))
    // Using half-open interval avoids many off-by-one errors

    while low < high {
        let mid = low + (high - low) / 2;  // safe from overflow
        if arr[mid] < target {
            low = mid + 1;
        } else {
            high = mid;  // shrink from right
        }
    }

    if low < arr.len() && arr[low] == target {
        Some(low)
    } else {
        None
    }
}

fn main() {
    let arr = vec![1, 3, 5, 7, 7, 7, 9, 11];
    println!("First 7 at: {:?}", binary_search_first(&arr, 7)); // Some(3)
    println!("First 6 at: {:?}", binary_search_first(&arr, 6)); // None

    // Rust's standard library also uses safe mid:
    // usize addition can't overflow the same way as i32 in practice,
    // but the pattern is still the correct one
}
```

---

## 15. Circular Buffer / Ring Queue Index

### What is a Circular Buffer?

A **circular buffer** (ring buffer) is a fixed-size array where the end wraps around to the beginning. It avoids the O(n) cost of shifting elements in a regular queue.

```
Circular Buffer (capacity=5):

State: front=2, rear=4, size=3
       (holds elements at indices 2, 3, 4)

Physical array:
┌────┬────┬────┬────┬────┐
│    │    │ A  │ B  │ C  │
└────┴────┴────┴────┴────┘
  0    1    2    3    4
             ▲         ▲
           front      rear

After enqueue(D):
  rear = (rear + 1) % 5 = 0

┌────┬────┬────┬────┬────┐
│ D  │    │ A  │ B  │ C  │
└────┴────┴────┴────┴────┘
  0    1    2    3    4
  ▲         ▲
rear      front
```

### Index Formula

```
Physical index of i-th logical element (0-indexed from front):
  physical = (front + i) % capacity

Enqueue (add to rear):
  rear = (rear + 1) % capacity

Dequeue (remove from front):
  front = (front + 1) % capacity

Is full?  size == capacity   OR   (rear + 1) % capacity == front
Is empty? size == 0
```

### Why Modulo?

The modulo operation `% capacity` performs the **wraparound**. When `rear + 1` exceeds the last index, it wraps back to 0.

```
Modulo visualization (capacity=5):
  0 % 5 = 0
  1 % 5 = 1
  2 % 5 = 2
  3 % 5 = 3
  4 % 5 = 4
  5 % 5 = 0  ← WRAP
  6 % 5 = 1  ← WRAP
  7 % 5 = 2  ← WRAP
```

### Power-of-2 Optimization

If `capacity` is a power of 2, replace `% capacity` with `& (capacity - 1)`:

```
capacity = 8 (2^3)
(rear + 1) % 8    →  (rear + 1) & 7
Why? For power-of-2 N: x % N == x & (N-1)

Example: rear = 7
  (7 + 1) % 8 = 0
  (7 + 1) & 7 = 8 & 7 = 1000 & 0111 = 0000 = 0  ✓

Bitwise AND is 2-5x faster than modulo division!
```

### C Implementation

```c
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>

typedef struct {
    int* data;
    int  front;
    int  rear;
    int  size;
    int  capacity;
} RingQueue;

RingQueue* rq_create(int cap) {
    RingQueue* q = (RingQueue*)malloc(sizeof(RingQueue));
    q->data     = (int*)malloc(cap * sizeof(int));
    q->front    = 0;
    q->rear     = 0;
    q->size     = 0;
    q->capacity = cap;
    return q;
}

bool rq_is_full(RingQueue* q)  { return q->size == q->capacity; }
bool rq_is_empty(RingQueue* q) { return q->size == 0; }

bool rq_enqueue(RingQueue* q, int val) {
    if (rq_is_full(q)) return false;
    q->data[q->rear] = val;
    q->rear = (q->rear + 1) % q->capacity;  // THE INDEX FORMULA
    q->size++;
    return true;
}

int rq_dequeue(RingQueue* q, bool* ok) {
    if (rq_is_empty(q)) { *ok = false; return -1; }
    int val = q->data[q->front];
    q->front = (q->front + 1) % q->capacity;  // THE INDEX FORMULA
    q->size--;
    *ok = true;
    return val;
}

// Access i-th logical element (0 = front)
int rq_get(RingQueue* q, int i) {
    return q->data[(q->front + i) % q->capacity];
}

void rq_print(RingQueue* q) {
    printf("Queue [size=%d, front=%d, rear=%d]: ", q->size, q->front, q->rear);
    for (int i = 0; i < q->size; i++)
        printf("%d ", rq_get(q, i));
    printf("\n");
}

int main() {
    RingQueue* q = rq_create(5);
    rq_enqueue(q, 10);
    rq_enqueue(q, 20);
    rq_enqueue(q, 30);
    rq_print(q);

    bool ok;
    printf("Dequeued: %d\n", rq_dequeue(q, &ok));
    rq_enqueue(q, 40);
    rq_enqueue(q, 50);
    rq_enqueue(q, 60);
    rq_print(q);

    free(q->data);
    free(q);
    return 0;
}
```

### Rust Implementation

```rust
pub struct RingQueue<T> {
    data: Vec<Option<T>>,
    front: usize,
    size: usize,
    capacity: usize,
}

impl<T: Copy + std::fmt::Debug> RingQueue<T> {
    pub fn new(capacity: usize) -> Self {
        RingQueue {
            data: (0..capacity).map(|_| None).collect(),
            front: 0,
            size: 0,
            capacity,
        }
    }

    pub fn is_full(&self)  -> bool { self.size == self.capacity }
    pub fn is_empty(&self) -> bool { self.size == 0 }

    // rear index (where next enqueue goes)
    fn rear(&self) -> usize { (self.front + self.size) % self.capacity }

    pub fn enqueue(&mut self, val: T) -> bool {
        if self.is_full() { return false; }
        let r = self.rear();
        self.data[r] = Some(val);
        self.size += 1;
        true
    }

    pub fn dequeue(&mut self) -> Option<T> {
        if self.is_empty() { return None; }
        let val = self.data[self.front].take();
        self.front = (self.front + 1) % self.capacity; // INDEX FORMULA
        self.size -= 1;
        val
    }

    // i-th logical element (0 = front)
    pub fn get(&self, i: usize) -> Option<T> {
        if i >= self.size { return None; }
        self.data[(self.front + i) % self.capacity]
    }

    pub fn print(&self) {
        print!("Queue: [");
        for i in 0..self.size {
            if let Some(v) = self.get(i) { print!("{:?} ", v); }
        }
        println!("]");
    }
}

fn main() {
    let mut q: RingQueue<i32> = RingQueue::new(5);
    q.enqueue(10); q.enqueue(20); q.enqueue(30);
    q.print();

    println!("Dequeued: {:?}", q.dequeue());
    q.enqueue(40); q.enqueue(50); q.enqueue(60);
    q.print();
}
```

### Go Implementation

```go
package main

import "fmt"

type RingQueue struct {
    data     []int
    front    int
    size     int
    capacity int
}

func NewRingQueue(cap int) *RingQueue {
    return &RingQueue{data: make([]int, cap), capacity: cap}
}

func (q *RingQueue) rear() int { return (q.front + q.size) % q.capacity }

func (q *RingQueue) Enqueue(val int) bool {
    if q.size == q.capacity { return false }
    q.data[q.rear()] = val
    q.size++
    return true
}

func (q *RingQueue) Dequeue() (int, bool) {
    if q.size == 0 { return 0, false }
    val := q.data[q.front]
    q.front = (q.front + 1) % q.capacity // INDEX FORMULA
    q.size--
    return val, true
}

func (q *RingQueue) Get(i int) (int, bool) {
    if i >= q.size { return 0, false }
    return q.data[(q.front+i)%q.capacity], true
}

func main() {
    q := NewRingQueue(5)
    q.Enqueue(10); q.Enqueue(20); q.Enqueue(30)
    fmt.Printf("Queue size: %d\n", q.size)

    v, _ := q.Dequeue()
    fmt.Printf("Dequeued: %d\n", v)
    q.Enqueue(40); q.Enqueue(50); q.Enqueue(60)
    fmt.Printf("Queue size: %d\n", q.size)
}
```

---

## 16. Hash Table Index Formula

### What is Hashing?

A **hash function** maps a key (any type) to an integer index in a fixed-size array (the **hash table**).

```
hash_index = hash_function(key) % table_size
```

### The Core Formula

```
index = hash(key) mod m

where:
  hash(key) = some integer derived from key
  m = table size (ideally prime)
```

### Common Hash Functions

**Division Method:**
```
hash(k) = k mod m
```

**Multiplication Method (Knuth):**
```
hash(k) = floor(m * (k * A mod 1))
where A ≈ 0.6180339887 (golden ratio - 1)
```

**FNV-1a (for strings, popular in C/Rust):**
```
hash = FNV_offset_basis (2166136261 for 32-bit)
for each byte b in string:
    hash = hash XOR b
    hash = hash * FNV_prime (16777619 for 32-bit)
```

### Why Prime Table Size?

```
If table_size = 10 (not prime):
  Keys: 10, 20, 30, 40 → all hash to 0  (collision!)

If table_size = 11 (prime):
  10 % 11 = 10
  20 % 11 = 9
  30 % 11 = 8  → spread out ✓
```

**Key Insight**: Prime numbers don't share factors with most hash codes, preventing systematic clustering.

### Load Factor and Rehashing

```
load_factor = n / m   (n = stored elements, m = table size)

When load_factor > threshold (typically 0.7):
  → Rehash: create new table of size ~2m, re-insert all elements
  → New index formula: hash(key) % (2m)
```

### Collision Resolution Index Formulas

**Linear Probing:**
```
probe sequence: (hash(k) + i) % m   for i = 0, 1, 2, ...
```

**Quadratic Probing:**
```
probe sequence: (hash(k) + i²) % m  for i = 0, 1, 2, ...
```

**Double Hashing:**
```
probe sequence: (hash1(k) + i * hash2(k)) % m
where hash2(k) = 1 + (k % (m-1))  (must be coprime with m)
```

### C Implementation (Hash Table with Linear Probing)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TABLE_SIZE 11  // prime

typedef struct {
    int   key;
    int   value;
    bool  occupied;
} Slot;

typedef struct {
    Slot* slots;
    int   size;
    int   count;
} HashMap;

HashMap* hm_create() {
    HashMap* m = (HashMap*)malloc(sizeof(HashMap));
    m->slots = (Slot*)calloc(TABLE_SIZE, sizeof(Slot));
    m->size  = TABLE_SIZE;
    m->count = 0;
    return m;
}

// Division hash function
int hash_fn(int key, int m) {
    return ((key % m) + m) % m;  // handles negative keys
}

// Insert key-value
void hm_put(HashMap* m, int key, int value) {
    int idx = hash_fn(key, m->size);

    // Linear probing: (hash(k) + i) % m
    for (int i = 0; i < m->size; i++) {
        int probe = (idx + i) % m->size;  // INDEX FORMULA
        if (!m->slots[probe].occupied || m->slots[probe].key == key) {
            m->slots[probe].key      = key;
            m->slots[probe].value    = value;
            m->slots[probe].occupied = true;
            m->count++;
            return;
        }
    }
    fprintf(stderr, "Table full!\n");
}

// Get value by key
int hm_get(HashMap* m, int key, bool* found) {
    int idx = hash_fn(key, m->size);
    for (int i = 0; i < m->size; i++) {
        int probe = (idx + i) % m->size;
        if (!m->slots[probe].occupied) { *found = false; return -1; }
        if (m->slots[probe].key == key) { *found = true; return m->slots[probe].value; }
    }
    *found = false;
    return -1;
}

void hm_print(HashMap* m) {
    printf("Hash Table:\n");
    for (int i = 0; i < m->size; i++) {
        if (m->slots[i].occupied)
            printf("  [%2d] key=%d, val=%d\n", i, m->slots[i].key, m->slots[i].value);
        else
            printf("  [%2d] (empty)\n", i);
    }
}

int main() {
    HashMap* m = hm_create();
    hm_put(m, 10, 100);
    hm_put(m, 21, 210);  // 21 % 11 = 10 → collision → probe to [1]
    hm_put(m, 5,  50);
    hm_put(m, 16, 160); // 16 % 11 = 5 → collision → probe to [6]

    hm_print(m);

    bool found;
    printf("\nhm_get(21) = %d\n", hm_get(m, 21, &found)); // 210
    printf("hm_get(99) = %d, found=%d\n", hm_get(m, 99, &found), found);

    free(m->slots);
    free(m);
    return 0;
}
```

---

## 17. Trie Node Index Formula

### What is a Trie?

A **trie** (prefix tree) stores strings character by character. Each node has up to 26 children (for lowercase English letters).

### Array-Based Trie Index Formula

Instead of using pointers, store the trie in a flat array:

```
node_id: each node gets an integer ID (0, 1, 2, ...)
children[node_id][char_index]  →  child node ID

char_index = character - 'a'   (0 for 'a', 1 for 'b', ..., 25 for 'z')
```

**Visual:**

```
Trie storing "cat", "car", "card":

Node 0 (root):
  c → Node 1

Node 1 ('c'):
  a → Node 2

Node 2 ('ca'):
  t → Node 3 (end: "cat")
  r → Node 4 (end: "car")

Node 4 ('car'):
  d → Node 5 (end: "card")

children[0]['c'-'a'] = children[0][2] = 1
children[1]['a'-'a'] = children[1][0] = 2
children[2]['t'-'a'] = children[2][19] = 3
children[2]['r'-'a'] = children[2][17] = 4
children[4]['d'-'a'] = children[4][3] = 5
```

### C Implementation (Array-Based Trie)

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>

#define ALPHA  26
#define MAXNODES 10000

int  children[MAXNODES][ALPHA];  // children[node][char_idx] = child_node
bool is_end[MAXNODES];           // is this node end of a word?
int  node_count = 1;             // root is node 0

void trie_init() {
    memset(children, -1, sizeof(children));
    memset(is_end, false, sizeof(is_end));
    node_count = 1;
}

void trie_insert(const char* word) {
    int cur = 0;  // start at root
    for (int i = 0; word[i]; i++) {
        int ci = word[i] - 'a';  // INDEX FORMULA: char to index
        if (children[cur][ci] == -1) {
            children[cur][ci] = node_count++;  // allocate new node
        }
        cur = children[cur][ci];
    }
    is_end[cur] = true;
}

bool trie_search(const char* word) {
    int cur = 0;
    for (int i = 0; word[i]; i++) {
        int ci = word[i] - 'a';
        if (children[cur][ci] == -1) return false;
        cur = children[cur][ci];
    }
    return is_end[cur];
}

bool trie_starts_with(const char* prefix) {
    int cur = 0;
    for (int i = 0; prefix[i]; i++) {
        int ci = prefix[i] - 'a';
        if (children[cur][ci] == -1) return false;
        cur = children[cur][ci];
    }
    return true;
}

int main() {
    trie_init();
    trie_insert("cat");
    trie_insert("car");
    trie_insert("card");
    trie_insert("care");
    trie_insert("careful");

    printf("Search 'cat':      %s\n", trie_search("cat")      ? "FOUND" : "NOT FOUND");
    printf("Search 'ca':       %s\n", trie_search("ca")        ? "FOUND" : "NOT FOUND");
    printf("Search 'card':     %s\n", trie_search("card")      ? "FOUND" : "NOT FOUND");
    printf("Prefix 'car':      %s\n", trie_starts_with("car")  ? "YES"   : "NO");
    printf("Prefix 'cat':      %s\n", trie_starts_with("cat")  ? "YES"   : "NO");
    printf("Prefix 'dog':      %s\n", trie_starts_with("dog")  ? "YES"   : "NO");
    printf("Node count: %d\n", node_count);
    return 0;
}
```

### Rust Implementation

```rust
const ALPHA: usize = 26;
const MAXN: usize = 10_000;

pub struct Trie {
    children: [[i32; ALPHA]; MAXN],
    is_end:   [bool; MAXN],
    count:    usize,
}

impl Trie {
    pub fn new() -> Self {
        Trie {
            children: [[-1i32; ALPHA]; MAXN],
            is_end:   [false; MAXN],
            count:    1, // root = 0
        }
    }

    pub fn insert(&mut self, word: &str) {
        let mut cur = 0usize;
        for ch in word.bytes() {
            let ci = (ch - b'a') as usize; // INDEX FORMULA
            if self.children[cur][ci] == -1 {
                self.children[cur][ci] = self.count as i32;
                self.count += 1;
            }
            cur = self.children[cur][ci] as usize;
        }
        self.is_end[cur] = true;
    }

    pub fn search(&self, word: &str) -> bool {
        let mut cur = 0usize;
        for ch in word.bytes() {
            let ci = (ch - b'a') as usize;
            if self.children[cur][ci] == -1 { return false; }
            cur = self.children[cur][ci] as usize;
        }
        self.is_end[cur]
    }

    pub fn starts_with(&self, prefix: &str) -> bool {
        let mut cur = 0usize;
        for ch in prefix.bytes() {
            let ci = (ch - b'a') as usize;
            if self.children[cur][ci] == -1 { return false; }
            cur = self.children[cur][ci] as usize;
        }
        true
    }
}

fn main() {
    let mut trie = Trie::new();
    for word in ["cat", "car", "card", "care", "careful"] {
        trie.insert(word);
    }

    println!("'cat' found: {}", trie.search("cat"));       // true
    println!("'ca' found: {}",  trie.search("ca"));        // false
    println!("'card' found: {}", trie.search("card"));     // true
    println!("Prefix 'car': {}", trie.starts_with("car")); // true
    println!("Prefix 'dog': {}", trie.starts_with("dog")); // false
}
```

---

## 18. Skip List Level Index

### Concept

A **skip list** is a probabilistic data structure with multiple levels of linked lists. Level 0 contains all elements; higher levels contain fewer elements (each element promoted with probability p, usually 0.5).

### Index Formula

The level of a node is determined **randomly**:

```
level(node) = geometric distribution with parameter p

While random() < p: level++

Expected level of a node = 1/(1-p)
Expected max level       = log_{1/p}(n)
```

### Level-Based Access

```
Access structure:
Level 3: ─────────────────────────→ 50 ──────────────────────→ NULL
Level 2: ──────────→ 20 ──────────→ 50 ──────────→ 80 ──────→ NULL
Level 1: ──→ 10 ──→ 20 ──→ 30 ──→ 50 ──→ 60 ──→ 80 ──→ 90 → NULL
Level 0: →5→10→15→20→25→30→35→50→55→60→65→80→85→90→95→NULL

Search 60: Start at highest level
  Level 3: 60 > 50? YES, advance. 60 > NULL? NO, drop down.
  Level 2: 60 > 50? YES, advance. 60 > 80? NO, drop down.
  Level 1: 60 == 60? YES, FOUND!
```

### C Implementation (Skip List with Level Indexing)

```c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define MAX_LEVEL 4
#define PROB 0.5

typedef struct SkipNode {
    int              key;
    struct SkipNode* forward[MAX_LEVEL]; // level index: forward[0]=level0, etc.
} SkipNode;

typedef struct {
    SkipNode* header;
    int       level;
} SkipList;

SkipNode* new_node(int key, int level) {
    SkipNode* n = (SkipNode*)calloc(1, sizeof(SkipNode));
    n->key = key;
    return n;
}

int random_level() {
    int lvl = 0;
    while ((double)rand()/RAND_MAX < PROB && lvl < MAX_LEVEL - 1)
        lvl++;
    return lvl;
}

SkipList* sl_create() {
    SkipList* sl = (SkipList*)malloc(sizeof(SkipList));
    sl->header   = new_node(INT_MIN, MAX_LEVEL);
    sl->level    = 0;
    return sl;
}

void sl_insert(SkipList* sl, int key) {
    SkipNode* update[MAX_LEVEL];
    SkipNode* cur = sl->header;

    // Find insertion point at each level
    for (int i = sl->level; i >= 0; i--) {
        while (cur->forward[i] && cur->forward[i]->key < key)
            cur = cur->forward[i];
        update[i] = cur;  // update[level] = rightmost node at level before insertion
    }

    int lvl = random_level();
    if (lvl > sl->level) {
        for (int i = sl->level + 1; i <= lvl; i++)
            update[i] = sl->header;
        sl->level = lvl;
    }

    SkipNode* n = new_node(key, lvl);
    for (int i = 0; i <= lvl; i++) {
        n->forward[i]      = update[i]->forward[i];  // INDEX: level i pointer
        update[i]->forward[i] = n;
    }
}

bool sl_search(SkipList* sl, int key) {
    SkipNode* cur = sl->header;
    for (int i = sl->level; i >= 0; i--) {  // high level to low
        while (cur->forward[i] && cur->forward[i]->key < key)
            cur = cur->forward[i];
    }
    cur = cur->forward[0];  // level 0 = ground level
    return cur && cur->key == key;
}

int main() {
    srand(42);
    SkipList* sl = sl_create();
    int keys[] = {5, 20, 50, 10, 60, 80, 30, 90};
    for (int i = 0; i < 8; i++) sl_insert(sl, keys[i]);

    printf("Search 50: %s\n", sl_search(sl, 50) ? "FOUND" : "NOT FOUND");
    printf("Search 25: %s\n", sl_search(sl, 25) ? "FOUND" : "NOT FOUND");
    return 0;
}
```

---

## 19. Disjoint Set (Union-Find) Indexing

### Concept

**Union-Find** represents a partition of `{0, 1, ..., n-1}` into disjoint sets. Each element has a **parent** pointer.

### Index Formula

```
parent[i] = parent of element i
            (if parent[i] == i, then i is the root of its set)

Find root of i:
  while parent[i] != i:
    i = parent[i]     ← FOLLOW THE INDEX

With path compression:
  parent[i] = find_root(parent[i])   ← direct link to root
```

### Union by Rank

```
rank[i] = approximate height of tree rooted at i

Union(a, b):
  ra = find(a), rb = find(b)
  if ra == rb: already same set
  if rank[ra] < rank[rb]: parent[ra] = rb
  elif rank[ra] > rank[rb]: parent[rb] = ra
  else: parent[rb] = ra; rank[ra]++
```

### C Implementation

```c
#include <stdio.h>
#define MAXN 100005

int parent[MAXN];
int rank_arr[MAXN];

void init(int n) {
    for (int i = 0; i < n; i++) {
        parent[i] = i;    // INDEX: each element is its own root
        rank_arr[i] = 0;
    }
}

// Find with path compression
int find(int x) {
    if (parent[x] != x)
        parent[x] = find(parent[x]);  // compress: redirect to root
    return parent[x];
}

// Union by rank
void unite(int a, int b) {
    int ra = find(a), rb = find(b);
    if (ra == rb) return;
    if (rank_arr[ra] < rank_arr[rb]) { int t = ra; ra = rb; rb = t; }
    parent[rb] = ra;
    if (rank_arr[ra] == rank_arr[rb]) rank_arr[ra]++;
}

bool same_set(int a, int b) { return find(a) == find(b); }

int main() {
    int n = 6;
    init(n);

    // Initial: {0},{1},{2},{3},{4},{5}
    unite(0, 1);  // {0,1},{2},{3},{4},{5}
    unite(2, 3);  // {0,1},{2,3},{4},{5}
    unite(0, 2);  // {0,1,2,3},{4},{5}

    printf("same_set(1,3) = %s\n", same_set(1,3) ? "YES" : "NO");  // YES
    printf("same_set(1,4) = %s\n", same_set(1,4) ? "YES" : "NO");  // NO
    printf("same_set(4,5) = %s\n", same_set(4,5) ? "YES" : "NO");  // NO

    unite(4, 5);
    printf("After unite(4,5):\n");
    printf("same_set(4,5) = %s\n", same_set(4,5) ? "YES" : "NO");  // YES

    // Show parent array
    printf("Parent array: ");
    for (int i = 0; i < n; i++) printf("p[%d]=%d ", i, parent[i]);
    printf("\n");
    return 0;
}
```

### Rust Implementation

```rust
pub struct UnionFind {
    parent: Vec<usize>,
    rank:   Vec<usize>,
}

impl UnionFind {
    pub fn new(n: usize) -> Self {
        UnionFind {
            parent: (0..n).collect(), // parent[i] = i (self-loop = root)
            rank:   vec![0; n],
        }
    }

    pub fn find(&mut self, mut x: usize) -> usize {
        // Path compression (iterative)
        while self.parent[x] != x {
            self.parent[x] = self.parent[self.parent[x]]; // path halving
            x = self.parent[x];
        }
        x
    }

    pub fn union(&mut self, a: usize, b: usize) -> bool {
        let (ra, rb) = (self.find(a), self.find(b));
        if ra == rb { return false; } // already same set

        // Union by rank
        match self.rank[ra].cmp(&self.rank[rb]) {
            std::cmp::Ordering::Less    => self.parent[ra] = rb,
            std::cmp::Ordering::Greater => self.parent[rb] = ra,
            std::cmp::Ordering::Equal   => {
                self.parent[rb] = ra;
                self.rank[ra] += 1;
            }
        }
        true
    }

    pub fn same_set(&mut self, a: usize, b: usize) -> bool {
        self.find(a) == self.find(b)
    }
}

fn main() {
    let mut uf = UnionFind::new(6);
    uf.union(0, 1);
    uf.union(2, 3);
    uf.union(0, 2);

    println!("same_set(1,3) = {}", uf.same_set(1, 3)); // true
    println!("same_set(1,4) = {}", uf.same_set(1, 4)); // false

    uf.union(4, 5);
    println!("same_set(4,5) = {}", uf.same_set(4, 5)); // true
}
```

---

## 20. Van Emde Boas Tree Indexing

### Concept (Advanced)

A **Van Emde Boas (vEB) tree** achieves O(log log U) operations where U is the universe size. It uses a recursive structure that splits the universe into √U "clusters."

### Index Formulas

For universe size U = 2^k (always a power of 2):

```
√U = 2^(k/2)  (called "sqrt(U)" or "high bits")

high(x) = x / √U = x >> (k/2)     ← which cluster
low(x)  = x % √U = x &  (√U - 1)  ← position within cluster
index(high, low) = high * √U + low  ← reconstruct from (cluster, position)
```

**This is the core vEB indexing formula**: every element `x` in [0, U) is decomposed into:
- `cluster = x / √U` — which of the √U sub-trees it belongs to
- `position = x % √U` — its position within that sub-tree

The recursion works because each sub-tree itself has universe size √U, and √U = 2^(k/2) is again a power of 2.

```
Universe [0, 15]:   U=16, √U=4

x=10:   high(10) = 10/4 = 2  (cluster 2)
         low(10) = 10%4 = 2  (position 2 in cluster 2)

Clusters:      0      1      2      3
Universe: [0..3] [4..7] [8..11] [12..15]

x=10 is in cluster 2, at local position 2:
  global 8 + local 2 = 10 ✓
```

### C Implementation (vEB index functions)

```c
#include <stdio.h>
#include <math.h>

// Universe size must be a power of 2: U = 2^k
typedef struct {
    int U;       // universe size
    int sqrtU;   // sqrt(U)
} VEBConfig;

// high(x): which cluster
int veb_high(VEBConfig* c, int x) {
    return x / c->sqrtU;  // equivalently: x >> (log2(sqrtU))
}

// low(x): position within cluster
int veb_low(VEBConfig* c, int x) {
    return x % c->sqrtU;  // equivalently: x & (sqrtU - 1)
}

// Reconstruct index from (cluster, position)
int veb_index(VEBConfig* c, int high, int low) {
    return high * c->sqrtU + low;
}

int main() {
    VEBConfig cfg = {16, 4};  // U=16, √16=4

    for (int x = 0; x < cfg.U; x++) {
        int h = veb_high(&cfg, x);
        int l = veb_low(&cfg, x);
        int reconstructed = veb_index(&cfg, h, l);
        printf("x=%2d → cluster=%d, pos=%d → reconstructed=%d %s\n",
               x, h, l, reconstructed, reconstructed==x ? "✓" : "✗");
    }
    return 0;
}
```

---

## 21. Off-by-One Errors — A Deep Study

### Definition

An **off-by-one error** (OBOE) is the most common bug in index-based programming. The boundary of a loop or range is wrong by exactly 1.

### Common Sources

```
1. Loop boundary:
   for (int i = 0; i <= n; i++)    // ❌ should be i < n
   for (int i = 1; i < n; i++)     // ❌ misses i=0

2. Array access:
   arr[n]    // ❌ last valid index is arr[n-1]
   arr[-1]   // ❌ before start

3. Range endpoints:
   [low, high)  vs  [low, high]  — exclusive vs inclusive

4. Binary search:
   high = n     // ❌ if using arr[high] inside loop
   high = n-1   // ✓

5. Heap last non-leaf:
   last = n/2      // ❌ for 0-based (should be n/2 - 1)
   last = n/2 - 1  // ✓ for 0-based
   last = n/2      // ✓ for 1-based
```

### Decision Framework for Off-by-One

```
When setting a loop/range bound, ask:
├── Is the upper bound INCLUSIVE or EXCLUSIVE?
│   ├── Inclusive [0, n-1]: use i <= n-1  or  i < n
│   └── Exclusive [0, n):  use i < n
│
├── 0-based or 1-based indexing?
│   ├── 0-based: first=0, last=n-1, count=n
│   └── 1-based: first=1, last=n,  count=n
│
└── Am I building a heap from array?
    ├── 0-based: start heapify at (n/2 - 1), go to 0
    └── 1-based: start heapify at (n/2),     go to 1
```

### Mental Model: Fence Post Problem

```
Fence with 5 panels needs 6 posts:
|  |  |  |  |  |
P  P  P  P  P  P
1  2  3  4  5  6

If you have n items in a range, you have n+1 boundaries!
Array of n elements: positions 0..n-1, boundaries at 0 and n
```

### Rust's Approach (Safer by Design)

```rust
// Rust prevents off-by-one with half-open ranges [low, high)
// and panics on out-of-bounds access in debug mode

let arr = [1, 2, 3, 4, 5];

// These all work correctly:
for x in &arr {}               // all elements
for x in &arr[1..4] {}         // elements at indices 1, 2, 3 (NOT 4)
for x in &arr[1..=4] {}        // elements at indices 1, 2, 3, 4

// This panics at runtime (debug) or UB (release):
// let _ = arr[5];  // index out of bounds!
```

---

## 22. Integer Overflow in Index Computation

### The Problem

When computing indices, intermediate results can overflow the integer type.

### Common Overflow Points

```
1. Binary search midpoint:     low + high  → overflow
2. Triangle index:             row*(row+1) → overflow for large row
3. 2D index:                   row * cols  → overflow for large matrices
4. Heap child:                 2 * i + 1   → overflow for i near INT_MAX/2
5. Segment tree size:          4 * n       → overflow for n near INT_MAX/4
```

### Safe Pattern (always use)

```c
// Instead of:    int idx = a * b + c;
// Use:           (cast to larger type first)

// C:
long long idx = (long long)row * cols + col;

// Rust (use usize or i64 explicitly):
let idx: usize = row * cols + col;  // usize never overflows in valid bounds

// Go (int is 64-bit on modern systems, but be explicit):
idx := int64(row)*int64(cols) + int64(col)
```

### Rust's Overflow Safety

```rust
fn main() {
    // Rust panics on overflow in debug mode:
    // let x: i32 = i32::MAX + 1;  // thread 'main' panicked: attempt to add with overflow

    // Use checked arithmetic when needed:
    let a: i32 = i32::MAX;
    match a.checked_add(1) {
        Some(val) => println!("Result: {}", val),
        None => println!("Overflow detected!"),
    }

    // Or wrapping (explicit modular arithmetic):
    let b = a.wrapping_add(1);  // silently wraps: -2147483648
    println!("Wrapping: {}", b);

    // Or saturating:
    let c = a.saturating_add(1); // stays at i32::MAX
    println!("Saturating: {}", c);
}
```

---

## 23. Master Comparison Table

| Structure | Index Formula | Time | Space | Key Property |
|---|---|---|---|---|
| **1D Array** | `i` | O(1) | O(n) | Direct access |
| **2D Array (row-major)** | `r*cols + c` | O(1) | O(r*c) | Row-contiguous in memory |
| **2D Array (col-major)** | `c*rows + r` | O(1) | O(r*c) | Column-contiguous |
| **3D Array** | `d*(r*c) + r*c + c` | O(1) | O(d*r*c) | Generalized flat |
| **Lower Triangle** | `r*(r+1)/2 + c` | O(1) | O(n²/2) | Half storage |
| **Upper Triangle** | `r*(2n-r-1)/2 + c` | O(1) | O(n²/2) | Half storage |
| **Symmetric** | `min(r,c)*(min+1)/2 + max` | O(1) | O(n²/2) | Mirror access |
| **Binary Heap (0-based)** | parent=(i-1)/2, left=2i+1 | O(1) | O(n) | Complete binary tree |
| **Binary Heap (1-based)** | parent=i/2, left=2i | O(1) | O(n) | Elegant bit-shift |
| **K-ary Heap** | child=k*i+j+1, parent=(i-1)/k | O(1) | O(n) | k children per node |
| **Segment Tree** | left=2i, right=2i+1 | O(1) | O(4n) | Range queries |
| **Fenwick Tree** | lowbit = i & (-i) | O(1) | O(n) | Prefix sums |
| **Sparse Table** | table[i][j] = range [i, i+2^j-1] | O(1) query | O(n log n) | Idempotent RMQ |
| **Binary Search Mid** | low + (high-low)/2 | O(1) | O(1) | Overflow-safe |
| **Circular Buffer** | (front+i) % cap | O(1) | O(cap) | Wrapping |
| **Hash Table** | hash(k) % m | O(1) avg | O(m) | Collision handling |
| **Trie** | children[node][c-'a'] | O(1) | O(ALPHA*n) | Prefix navigation |
| **vEB Tree** | high=x/√U, low=x%√U | O(1) | O(U) | Bitwise split |
| **Union-Find** | parent[i] follow chain | O(α(n)) | O(n) | Path compression |

*α(n) = inverse Ackermann function, practically O(1)*

---

## 24. Cognitive & Practice Strategies

### Mental Models for Index Formulas

**Model 1: The Grid-to-Tape Mental Mapping**
Always ask: *"If I flatten this structure into a tape, where does element X land?"*

**Model 2: The Elimination Count**
*"How many elements come BEFORE this one?"* — That count is the index.
- Lower triangle index = # elements before row `r` + position in row = `r*(r+1)/2 + c`
- Heap left child = skip 2i elements, so left starts at 2i+1

**Model 3: The Modular Wrapping Intuition**
Circular structures always use `% capacity`. Think of a clock: after 12, it wraps to 1. After index `cap-1`, it wraps to 0.

**Model 4: The Bit Manipulation View**
Heap navigation = tree traversal using bit shifts:
- `i << 1` = go to left child (double the index)
- `(i << 1) | 1` = go to right child
- `i >> 1` = go to parent (halve the index)

---

### Deliberate Practice Protocol

**Phase 1: Derivation (Not Memorization)**
Never memorize `2*i+1`. Instead, *derive it every time* until it becomes muscle memory.
- Draw the heap tree on paper
- Number nodes level by level
- Observe the pattern

**Phase 2: Verification Habit**
After writing any index formula:
1. Plug in `i=0` (root/start) — does it give root?
2. Plug in `i=1` — correct first child?
3. Plug in `i=n-1` (last) — valid?

**Phase 3: Boundary Testing**
Always test:
- `i = 0` (first element)
- `i = n-1` (last element)
- `i = n` (one past end — should be invalid)
- `i = -1` (before start — should be invalid)

**Phase 4: Cross-Check with Structure**
For heaps: verify parent-child invariant holds.
For circular buffer: verify wrap-around is correct.
For hash: verify collision handling is correct.

---

### Chunking Strategy (Cognitive Science)

Group related formulas into **chunks** in your memory:

```
Chunk 1: POWER-OF-2 STRUCTURES
  Heap 0-based: left=2i+1, right=2i+2, parent=(i-1)/2
  Heap 1-based: left=2i,   right=2i+1, parent=i/2
  Remember: "Double, double+1, halve"

Chunk 2: TRIANGULAR FORMULAS
  Triangle numbers: 0, 1, 3, 6, 10, 15, ...  = n*(n+1)/2
  Lower tri at (r,c): T(r) + c  where T(r) = r*(r+1)/2
  Upper tri at (r,c): r*(2n-r-1)/2 + c

Chunk 3: MODULAR WRAPPING
  Ring queue: (front + i) % cap
  Hash table: hash(k) % m
  Circular advance: (ptr + 1) % cap
  Remember: "% is the wrap"

Chunk 4: TREE SPLIT FORMULAS (vEB, Segment Tree)
  vEB: high = x >> k/2,  low = x & (√U - 1)
  SegTree: left = 2*node,  right = 2*node + 1
  Remember: "Multiply to go down, divide to go up"
```

---

### The Expert's Pre-Coding Checklist

Before writing any index-heavy code, mentally answer:

```
□ What is my indexing base? (0-based or 1-based)
□ Are all indices within bounds? (prove it)
□ Can any intermediate computation overflow?
□ Am I accessing adjacent memory? (cache performance)
□ Do boundary elements (first, last) work correctly?
□ Is my loop range correct? ([0,n) vs [0,n] vs [1,n])
□ If circular, does wraparound work at capacity-1 → 0?
□ For heaps: does the last non-leaf formula match my base?
```

---

### The Three Layers of Mastery

```
Layer 1 — KNOW IT (Beginner)
  Can write the formula when given a reference.

Layer 2 — DERIVE IT (Intermediate)  
  Can re-derive the formula from first principles
  in under 30 seconds.

Layer 3 — FEEL IT (Expert / Top 1%)
  Sees the index formula as a geometric truth.
  Spots overflow bugs and off-by-one errors instantly.
  Knows when to use each structure without thinking.
  Optimizes for cache behavior intuitively.
```

**Your practice goal**: For every formula in this document, be able to:
1. Draw the logical structure from memory
2. Derive the formula
3. Write the code in any of your languages
4. Identify and fix bugs in a buggy implementation

*"An expert is someone for whom every step of a derivation is obvious — not because they memorized it, but because they understand why it must be so."*

---

## Summary Flow Chart

```
WHICH INDEX FORMULA DO I NEED?
│
├─ Storing a matrix?
│   ├─ Dense (all elements needed)?
│   │   ├─ 2D → row*cols + col (row-major) or col*rows + row (col-major)
│   │   └─ 3D → depth*(rows*cols) + row*cols + col
│   └─ Sparse pattern?
│       ├─ Lower triangle → row*(row+1)/2 + col
│       ├─ Upper triangle → row*(2n-row-1)/2 + col
│       ├─ Symmetric      → index lower triangle, swap if needed
│       └─ Tridiagonal    → use 3 arrays: a, b, c
│
├─ Implementing a priority queue (heap)?
│   ├─ 0-based → left=2i+1, right=2i+2, parent=(i-1)/2
│   ├─ 1-based → left=2i, right=2i+1, parent=i/2
│   └─ k-ary   → child=k*i+j+1, parent=(i-1)/k
│
├─ Range queries on array?
│   ├─ Updates needed? → Segment Tree (left=2i, right=2i+1)
│   ├─ Prefix sums?    → Fenwick Tree (lowbit = i & -i)
│   └─ Static RMQ?     → Sparse Table (table[i][j] for 2^j ranges)
│
├─ Search / navigation?
│   ├─ Sorted array?   → Binary search (mid = low + (high-low)/2)
│   ├─ String prefix?  → Trie (children[node][c - 'a'])
│   └─ Connectivity?   → Union-Find (parent[i] with path compression)
│
└─ Queue with wrapping?
    └─ Circular buffer → (front + i) % capacity
```

---

*End of Guide. The path to the top 1% is not speed — it is depth. Master each formula not as a fact to recall, but as a truth you can reconstruct, explain, and extend.*

Now I'll create a truly comprehensive `.md` guide on Index Formulas in DSA. This will take a moment to build out fully.Here is your complete **Index Formula Master Guide** — 24 deeply connected sections, fully implemented in C, Rust, and Go.

---

### What's covered, and *why* it matters:

**Foundation Layer**
The guide opens with the core mental model: RAM is a tape. Every index formula is just a mathematical bridge from *logical coordinates* to *physical tape position*. This framing makes every subsequent formula feel inevitable rather than arbitrary.

**Matrix Formulas (2D → 3D → Specialized)**
You'll see why row-major vs column-major is not just an academic distinction — it's the difference between a cache-friendly and a cache-thrashing loop. Triangular, symmetric, and tridiagonal indexing show how to cut memory usage by 50% or more on structured matrices.

**Tree-Based Index Formulas**
The heap formulas (`left = 2i+1`, `parent = (i-1)/2`) are derived, not stated — so you understand *why* the root at index 0 forces the `+1` offset. The segment tree, Fenwick tree, and sparse table each have a distinct index "personality" that flows from their structural constraints.

**Overflow & Off-by-One (Critical)**
The binary search midpoint overflow is arguably the most famous index bug in computing history (it was in Java's standard library for 9 years). The guide gives you a decision framework and Rust's three overflow-safe operations (`checked`, `wrapping`, `saturating`).

**Cognitive Strategy**
The final section gives you the **chunking approach** — grouping formulas into 4 mental clusters so your brain stores them efficiently — and the **Three Layers of Mastery** framework (Know It → Derive It → Feel It).