# Matrix Manipulation — Complete In-Depth Guide
### From Fundamentals to Expert-Level Mastery

---

## Table of Contents

1. [What Is a Matrix? — The Mental Model](#1-what-is-a-matrix--the-mental-model)
2. [Memory Layout Internals — How Computers Actually Store Matrices](#2-memory-layout-internals--how-computers-actually-store-matrices)
3. [Indexing and Addressing — The Math Behind Access](#3-indexing-and-addressing--the-math-behind-access)
4. [Matrix Representation in Code](#4-matrix-representation-in-code)
5. [Basic Traversal Patterns](#5-basic-traversal-patterns)
6. [Transpose](#6-transpose)
7. [Rotation (90°, 180°, 270°)](#7-rotation-90-180-270)
8. [Spiral Traversal](#8-spiral-traversal)
9. [Diagonal Traversal](#9-diagonal-traversal)
10. [Layer-by-Layer / Onion Peeling](#10-layer-by-layer--onion-peeling)
11. [Matrix Search — Sorted Matrix Techniques](#11-matrix-search--sorted-matrix-techniques)
12. [Matrix Multiplication](#12-matrix-multiplication)
13. [Submatrix Operations](#13-submatrix-operations)
14. [Prefix Sum Matrix (2D Prefix Sum)](#14-prefix-sum-matrix-2d-prefix-sum)
15. [Flipping and Reflecting](#15-flipping-and-reflecting)
16. [Set Zeroes (Marking and Propagation)](#16-set-zeroes-marking-and-propagation)
17. [Island and Region Problems (DFS/BFS on Matrix)](#17-island-and-region-problems-dfsbfs-on-matrix)
18. [Dynamic Programming on Matrix](#18-dynamic-programming-on-matrix)
19. [Zigzag, Anti-Diagonal, and Snake Traversal](#19-zigzag-anti-diagonal-and-snake-traversal)
20. [Matrix as Graph — Adjacency Thinking](#20-matrix-as-graph--adjacency-thinking)
21. [Common Mistakes — What You Cannot Do and Why](#21-common-mistakes--what-you-cannot-do-and-why)
22. [Expert Mental Models for Matrix Problems](#22-expert-mental-models-for-matrix-problems)

---

## 1. What Is a Matrix? — The Mental Model

A **matrix** is a 2-dimensional rectangular grid of elements arranged in **rows** and **columns**.

```
         Column 0   Column 1   Column 2
        +----------+----------+----------+
Row 0   |   a[0][0]|   a[0][1]|   a[0][2]|
        +----------+----------+----------+
Row 1   |   a[1][0]|   a[1][1]|   a[1][2]|
        +----------+----------+----------+
Row 2   |   a[2][0]|   a[2][1]|   a[2][2]|
        +----------+----------+----------+

  Shape: 3 rows x 3 cols  (written as M x N or R x C)
```

### Terminology You Must Know

| Term | Meaning |
|------|---------|
| **Row** | Horizontal line of elements. Index = first bracket `[i]` |
| **Column** | Vertical line of elements. Index = second bracket `[j]` |
| **Element** | Single cell at `[row][col]` |
| **Shape / Dimension** | `M x N` means M rows, N columns |
| **Square Matrix** | M == N |
| **Rectangular Matrix** | M != N |
| **Main Diagonal** | Elements where `row == col` (top-left to bottom-right) |
| **Anti-Diagonal** | Elements where `row + col == N-1` (top-right to bottom-left) |
| **Transpose** | Flip along main diagonal: swap `[i][j]` with `[j][i]` |
| **In-place** | Modify the matrix without using extra space |

### Visualizing the Diagonals

```
  Main Diagonal (row == col):        Anti-Diagonal (row+col == N-1):

  [*][ ][ ][ ]                       [ ][ ][ ][*]
  [ ][*][ ][ ]                       [ ][ ][*][ ]
  [ ][ ][*][ ]                       [ ][*][ ][ ]
  [ ][ ][ ][*]                       [*][ ][ ][ ]

  (0,0),(1,1),(2,2),(3,3)            (0,3),(1,2),(2,1),(3,0)
```

---

## 2. Memory Layout Internals — How Computers Actually Store Matrices

Computers use **linear (1D) memory** — RAM is a flat array of bytes. A 2D matrix must be "flattened" into this 1D space. There are two strategies:

### Row-Major Order (C, Rust, Go — Most Common)

Elements of each **row** are stored **contiguously** in memory.

```
Logical 2D:                 Physical 1D Memory:
                            Index:  0    1    2    3    4    5    6    7    8
  [1][2][3]                        [1]  [2]  [3]  [4]  [5]  [6]  [7]  [8]  [9]
  [4][5][6]                         ^-Row 0--^    ^----Row 1----^  ^---Row 2---^
  [7][8][9]

  Formula: address(i, j) = base + (i * num_cols + j) * element_size
```

```
Memory diagram (3x3, int32, each block = 4 bytes):

Address: 0x00  0x04  0x08  0x0C  0x10  0x14  0x18  0x1C  0x20
         +-----+-----+-----+-----+-----+-----+-----+-----+-----+
Value:   |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  |
         +-----+-----+-----+-----+-----+-----+-----+-----+-----+
          [0,0] [0,1] [0,2] [1,0] [1,1] [1,2] [2,0] [2,1] [2,2]
          <---- Row 0 ----> <---- Row 1 ----> <---- Row 2 ---->
```

### Column-Major Order (Fortran, MATLAB, Julia)

Elements of each **column** are stored contiguously.

```
Logical 2D:                 Physical 1D Memory:
                            Index:  0    1    2    3    4    5    6    7    8
  [1][2][3]                        [1]  [4]  [7]  [2]  [5]  [8]  [3]  [6]  [9]
  [4][5][6]                         ^-Col 0--^    ^----Col 1----^  ^---Col 2---^
  [7][8][9]

  Formula: address(i, j) = base + (j * num_rows + i) * element_size
```

### Why This Matters: Cache Performance

```
Cache Line = 64 bytes (holds 16 int32 values)

ROW-MAJOR traversal (row by row) = GOOD:
  Access pattern: [0,0] [0,1] [0,2] [1,0] [1,1] [1,2] ...
                   sequential in memory -> cache line already loaded!

COLUMN-MAJOR traversal in Row-Major matrix = BAD:
  Access pattern: [0,0] [1,0] [2,0] [3,0] ...
                   jumps by (num_cols * 4) bytes -> cache miss every time!

  3x3:  [0,0] is at 0x00
        [1,0] is at 0x0C  <- 12 bytes jump
        [2,0] is at 0x18  <- 12 bytes jump
  Each access may evict the previous cache line!
```

**Rule of thumb**: Always traverse in the order that matches your language's storage order. In C, Rust, Go — traverse row by row (outer loop = rows, inner loop = cols).

---

## 3. Indexing and Addressing — The Math Behind Access

### Coordinate System

```
    j=0  j=1  j=2  j=3
   +----+----+----+----+
i=0| (0,0)(0,1)(0,2)(0,3)|
   +----+----+----+----+
i=1| (1,0)(1,1)(1,2)(1,3)|
   +----+----+----+----+
i=2| (2,0)(2,1)(2,2)(2,3)|
   +----+----+----+----+

  i = row index  (0 to M-1)
  j = col index  (0 to N-1)
```

### Key Index Relationships (Memorize These)

```
For an M x N matrix:

  Total elements         : M * N
  Last row index         : M - 1
  Last col index         : N - 1
  Main diagonal element  : (i, i)    where i in [0, min(M,N)-1]
  Anti-diagonal element  : (i, N-1-i) where i in [0, M-1]
  Transpose coord        : (i, j) -> (j, i)  [only valid for square or reshaped]

  1D flat index -> 2D    : flat = i*N + j
                           i = flat / N
                           j = flat % N

  2D -> 1D flat index    : flat = i*N + j
```

### Boundary Checks (Critical!)

```
Valid cell (i, j) requires:
  0 <= i < M   AND   0 <= j < N

This is the most common source of bugs — off-by-one errors!

WRONG:  i <= M  (accesses out of bounds)
RIGHT:  i < M

WRONG:  j >= 0 && j <= N  (wrong upper bound)
RIGHT:  j >= 0 && j < N
```

---

## 4. Matrix Representation in Code

### In C — 2D Array (Stack), Pointer of Pointers (Heap), Flat 1D Array

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ── METHOD 1: Stack-allocated 2D array (fixed size at compile time) ──
void method1_stack() {
    int mat[3][4] = {
        {1,  2,  3,  4},
        {5,  6,  7,  8},
        {9, 10, 11, 12}
    };
    // Access: mat[i][j]
    // Memory: contiguous, row-major
    printf("mat[1][2] = %d\n", mat[1][2]); // 7
}

// ── METHOD 2: Heap-allocated pointer-of-pointers ──
// Each row is a separate malloc — NOT contiguous across rows!
int** alloc_matrix_pp(int rows, int cols) {
    int** mat = (int**)malloc(rows * sizeof(int*));
    for (int i = 0; i < rows; i++) {
        mat[i] = (int*)malloc(cols * sizeof(int));
        memset(mat[i], 0, cols * sizeof(int));
    }
    return mat;
}

void free_matrix_pp(int** mat, int rows) {
    for (int i = 0; i < rows; i++) free(mat[i]);
    free(mat);
}

// ── METHOD 3: Flat 1D array with manual indexing (BEST for performance) ──
// Fully contiguous in memory — cache friendly
int* alloc_matrix_flat(int rows, int cols) {
    return (int*)calloc(rows * cols, sizeof(int));
}

// Macro for clean access: MAT(arr, i, j, num_cols)
#define MAT(arr, i, j, cols) ((arr)[(i) * (cols) + (j)])

void method3_flat_demo() {
    int rows = 3, cols = 4;
    int* mat = alloc_matrix_flat(rows, cols);
    MAT(mat, 1, 2, cols) = 7;
    printf("mat[1][2] = %d\n", MAT(mat, 1, 2, cols)); // 7
    free(mat);
}

int main() {
    method1_stack();
    method3_flat_demo();
    return 0;
}
```

### Memory Layout Comparison (C)

```
METHOD 2 (pointer-of-pointers) — NON-contiguous:

  mat -> [ptr0][ptr1][ptr2]    <- one malloc
          |     |     |
          v     v     v
        [1,2,3,4] [5,6,7,8] [9,10,11,12]  <- three separate mallocs
        scattered anywhere in heap!

METHOD 3 (flat array) — CONTIGUOUS:

  mat -> [1][2][3][4][5][6][7][8][9][10][11][12]
          ^ single malloc, all contiguous ^
```

### In Rust — Vec<Vec<T>> vs Vec<T> with stride

```rust
// ── METHOD 1: Vec<Vec<T>> — easy but not contiguous ──
fn method1_vec_of_vec() {
    let rows = 3;
    let cols = 4;

    // Initialize 3x4 matrix with zeros
    let mut mat: Vec<Vec<i32>> = vec![vec![0i32; cols]; rows];

    mat[1][2] = 7;
    println!("mat[1][2] = {}", mat[1][2]); // 7

    // Iteration
    for i in 0..rows {
        for j in 0..cols {
            print!("{:4}", mat[i][j]);
        }
        println!();
    }
}

// ── METHOD 2: Flat Vec<T> with manual indexing — BEST PERFORMANCE ──
struct Matrix {
    data: Vec<i32>,
    rows: usize,
    cols: usize,
}

impl Matrix {
    fn new(rows: usize, cols: usize) -> Self {
        Matrix {
            data: vec![0; rows * cols],
            rows,
            cols,
        }
    }

    // Inline indexing — zero overhead
    #[inline(always)]
    fn get(&self, i: usize, j: usize) -> i32 {
        self.data[i * self.cols + j]
    }

    #[inline(always)]
    fn set(&mut self, i: usize, j: usize, val: i32) {
        self.data[i * self.cols + j] = val;
    }

    fn print(&self) {
        for i in 0..self.rows {
            for j in 0..self.cols {
                print!("{:4}", self.get(i, j));
            }
            println!();
        }
    }
}

fn main() {
    method1_vec_of_vec();

    let mut mat = Matrix::new(3, 4);
    mat.set(1, 2, 7);
    println!("mat[1][2] = {}", mat.get(1, 2));
    mat.print();
}
```

### In Go — Slice of Slices vs Flat Slice

```go
package main

import "fmt"

// ── METHOD 1: [][]int — idiomatic Go, non-contiguous rows ──
func newMatrix2D(rows, cols int) [][]int {
    mat := make([][]int, rows)
    for i := range mat {
        mat[i] = make([]int, cols)
    }
    return mat
}

// ── METHOD 2: Flat []int with stride — contiguous, faster ──
type Matrix struct {
    data []int
    rows int
    cols int
}

func NewMatrix(rows, cols int) *Matrix {
    return &Matrix{
        data: make([]int, rows*cols),
        rows: rows,
        cols: cols,
    }
}

func (m *Matrix) Get(i, j int) int {
    return m.data[i*m.cols+j]
}

func (m *Matrix) Set(i, j, val int) {
    m.data[i*m.cols+j] = val
}

func (m *Matrix) Print() {
    for i := 0; i < m.rows; i++ {
        for j := 0; j < m.cols; j++ {
            fmt.Printf("%4d", m.Get(i, j))
        }
        fmt.Println()
    }
}

// ── METHOD 3: Allocate contiguous backing array for [][]int ──
// Trick: single allocation, rows slice into it
func newContiguousMatrix(rows, cols int) [][]int {
    backing := make([]int, rows*cols)   // ONE allocation
    mat := make([][]int, rows)
    for i := range mat {
        mat[i] = backing[i*cols : (i+1)*cols] // slice into backing
    }
    return mat
    // Now mat[i][j] accesses contiguous memory!
}

func main() {
    m := NewMatrix(3, 4)
    m.Set(1, 2, 7)
    fmt.Println(m.Get(1, 2)) // 7
    m.Print()

    // Contiguous slice-of-slices
    mat := newContiguousMatrix(3, 4)
    mat[1][2] = 7
    fmt.Println(mat[1][2]) // 7
}
```

---

## 5. Basic Traversal Patterns

### Row-by-Row (Most Common)

```
  → → → →
  → → → →
  → → → →

  Order: (0,0)(0,1)(0,2)(0,3) | (1,0)(1,1)(1,2)(1,3) | (2,0)...
```

```c
// C
void traverse_rowwise(int* mat, int M, int N) {
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            printf("%d ", MAT(mat, i, j, N));
        }
        printf("\n");
    }
}
```

```rust
// Rust
fn traverse_rowwise(mat: &Matrix) {
    for i in 0..mat.rows {
        for j in 0..mat.cols {
            print!("{} ", mat.get(i, j));
        }
        println!();
    }
}
```

```go
// Go
func traverseRowwise(mat [][]int, M, N int) {
    for i := 0; i < M; i++ {
        for j := 0; j < N; j++ {
            fmt.Printf("%d ", mat[i][j])
        }
        fmt.Println()
    }
}
```

### Column-by-Column

```
  ↓ ↓ ↓ ↓
  ↓ ↓ ↓ ↓
  ↓ ↓ ↓ ↓

  Order: (0,0)(1,0)(2,0) | (0,1)(1,1)(2,1) | ...
  ⚠ Cache-unfriendly in row-major languages!
```

```rust
// Rust
fn traverse_colwise(mat: &Matrix) {
    for j in 0..mat.cols {      // outer = columns
        for i in 0..mat.rows {  // inner = rows
            print!("{} ", mat.get(i, j));
        }
        println!();
    }
}
// Note: In competitive programming this is sometimes unavoidable,
// but understand you're paying a cache-miss penalty.
```

### Main Diagonal Traversal

```
  [*][ ][ ][ ]
  [ ][*][ ][ ]
  [ ][ ][*][ ]
  [ ][ ][ ][*]

  Elements: (0,0), (1,1), (2,2), (3,3)
  Condition: i == j
```

```c
// C
void traverse_main_diagonal(int* mat, int N) { // square N x N
    for (int i = 0; i < N; i++) {
        printf("%d ", MAT(mat, i, i, N));
    }
}
```

### Anti-Diagonal Traversal

```
  [ ][ ][ ][*]
  [ ][ ][*][ ]
  [ ][*][ ][ ]
  [*][ ][ ][ ]

  Elements: (0, N-1), (1, N-2), (2, N-3), ...
  Condition: i + j == N - 1
```

```c
// C
void traverse_anti_diagonal(int* mat, int N) {
    for (int i = 0; i < N; i++) {
        printf("%d ", MAT(mat, i, N - 1 - i, N));
    }
}
```

---

## 6. Transpose

### What Is Transpose?

Transposing a matrix means **reflecting it along its main diagonal**. Every element at position `(i, j)` moves to `(j, i)`.

```
Original:                 Transposed:
  1   2   3                 1   4   7
  4   5   6      →→→        2   5   8
  7   8   9                 3   6   9

  (0,1)=2 goes to (1,0)=2
  (0,2)=3 goes to (2,0)=3
  etc.
```

### In-Place Transpose (Square Matrix Only)

The key insight: only swap elements **above** the main diagonal (where `j > i`). If you swap both `(i,j)` and `(j,i)` you undo your own work!

```
Swap plan — only upper triangle:

  i\j  0    1    2
  0   [skip][SWAP][SWAP]
  1   [skip][skip][SWAP]
  2   [skip][skip][skip]

  For i in 0..N:
    For j in i+1..N:   ← start from i+1, NOT 0!
      swap(mat[i][j], mat[j][i])
```

```c
// C — In-place transpose (square matrix)
void transpose_inplace(int* mat, int N) {
    for (int i = 0; i < N; i++) {
        for (int j = i + 1; j < N; j++) {   // j starts from i+1 — critical!
            int tmp = MAT(mat, i, j, N);
            MAT(mat, i, j, N) = MAT(mat, j, i, N);
            MAT(mat, j, i, N) = tmp;
        }
    }
}
// Time: O(N^2)  Space: O(1)
```

```rust
// Rust — In-place transpose (square matrix)
fn transpose_inplace(mat: &mut Matrix) {
    assert_eq!(mat.rows, mat.cols, "Must be square for in-place transpose");
    let n = mat.rows;
    for i in 0..n {
        for j in (i + 1)..n {               // j starts from i+1
            let tmp = mat.get(i, j);
            let val_ji = mat.get(j, i);
            mat.set(i, j, val_ji);
            mat.set(j, i, tmp);
        }
    }
}
// Time: O(N^2)  Space: O(1)
```

```go
// Go — In-place transpose (square matrix)
func transposeInPlace(mat [][]int, N int) {
    for i := 0; i < N; i++ {
        for j := i + 1; j < N; j++ {        // j starts from i+1
            mat[i][j], mat[j][i] = mat[j][i], mat[i][j]
        }
    }
}
// Time: O(N^2)  Space: O(1)
```

### Out-of-Place Transpose (Rectangular Matrix, M x N → N x M)

```
Original M x N:           Transposed N x M:
  1  2  3  4               1  5  9
  5  6  7  8       →→→     2  6 10
  9 10 11 12               3  7 11
                           4  8 12
  (3 rows, 4 cols)         (4 rows, 3 cols)
```

```c
// C — Out-of-place transpose (M x N -> N x M)
int* transpose_outplace(int* mat, int M, int N) {
    int* result = (int*)malloc(N * M * sizeof(int));
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            // (i,j) in original -> (j,i) in result
            // result is N x M, so result[j][i] -> flat: j*M + i
            result[j * M + i] = MAT(mat, i, j, N);
        }
    }
    return result;
}
// Time: O(M*N)  Space: O(M*N)
```

```rust
// Rust — Out-of-place transpose
fn transpose_outplace(mat: &Matrix) -> Matrix {
    let mut result = Matrix::new(mat.cols, mat.rows); // N rows, M cols
    for i in 0..mat.rows {
        for j in 0..mat.cols {
            result.set(j, i, mat.get(i, j));
        }
    }
    result
}
```

```go
// Go — Out-of-place transpose
func transposeOutPlace(mat [][]int, M, N int) [][]int {
    result := newMatrix2D(N, M)
    for i := 0; i < M; i++ {
        for j := 0; j < N; j++ {
            result[j][i] = mat[i][j]
        }
    }
    return result
}
```

---

## 7. Rotation (90°, 180°, 270°)

### Conceptual Understanding — What Does Rotation Mean?

```
Original:         90° Clockwise:     180°:             270° Clockwise
                                                        (= 90° Counter-CW):
 1  2  3           7  4  1            9  8  7             3  6  9
 4  5  6    →CW→   8  5  2    →CW→   6  5  4    →CW→    2  5  8
 7  8  9           9  6  3            3  2  1             1  4  7
```

### The Key Formula for 90° Clockwise

```
For element at (i, j) in N x N matrix:
  After 90° clockwise, it goes to (j, N-1-i)

  Proof: Think of columns becoming rows.
  - Column 0 becomes Row 0 (reading bottom to top)
  - Column 1 becomes Row 1
  - (i,j) → new_row = j, new_col = N-1-i

  Example: (0,0)=1 → (0, 2)    (reads as: row 0, col N-1-0=2)
           (0,1)=2 → (1, 2)
           (0,2)=3 → (2, 2)
           (2,0)=7 → (0, 0)
```

### In-Place 90° Clockwise = Transpose + Horizontal Flip

```
Step 1 — Transpose:           Step 2 — Reverse each row:
 1  2  3     1  4  7           1  4  7     7  4  1
 4  5  6  →  2  5  8    →→    2  5  8  →  8  5  2
 7  8  9     3  6  9           3  6  9     9  6  3

  swap(i,j) with (j,i)         reverse each row
```

```c
// C — 90° Clockwise in-place (square matrix)
void reverse_row(int* mat, int row, int N) {
    int left = 0, right = N - 1;
    while (left < right) {
        int tmp = MAT(mat, row, left, N);
        MAT(mat, row, left, N) = MAT(mat, row, right, N);
        MAT(mat, row, right, N) = tmp;
        left++;
        right--;
    }
}

void rotate90_clockwise(int* mat, int N) {
    // Step 1: Transpose
    for (int i = 0; i < N; i++)
        for (int j = i + 1; j < N; j++) {
            int tmp = MAT(mat, i, j, N);
            MAT(mat, i, j, N) = MAT(mat, j, i, N);
            MAT(mat, j, i, N) = tmp;
        }
    // Step 2: Reverse each row
    for (int i = 0; i < N; i++)
        reverse_row(mat, i, N);
}
// Time: O(N^2)  Space: O(1)
```

```rust
// Rust — 90° Clockwise in-place
fn rotate90_clockwise(mat: &mut Matrix) {
    let n = mat.rows;
    // Step 1: Transpose
    for i in 0..n {
        for j in (i + 1)..n {
            let tmp = mat.get(i, j);
            let v = mat.get(j, i);
            mat.set(i, j, v);
            mat.set(j, i, tmp);
        }
    }
    // Step 2: Reverse each row
    for i in 0..n {
        let mut left = 0usize;
        let mut right = n - 1;
        while left < right {
            let l = mat.get(i, left);
            let r = mat.get(i, right);
            mat.set(i, left, r);
            mat.set(i, right, l);
            left += 1;
            right -= 1;
        }
    }
}
```

```go
// Go — 90° Clockwise in-place
func rotate90Clockwise(mat [][]int, N int) {
    // Step 1: Transpose
    for i := 0; i < N; i++ {
        for j := i + 1; j < N; j++ {
            mat[i][j], mat[j][i] = mat[j][i], mat[i][j]
        }
    }
    // Step 2: Reverse each row
    for i := 0; i < N; i++ {
        left, right := 0, N-1
        for left < right {
            mat[i][left], mat[i][right] = mat[i][right], mat[i][left]
            left++
            right--
        }
    }
}
```

### 90° Counter-Clockwise = Transpose + Vertical Flip

```
Step 1 — Transpose:           Step 2 — Reverse each column:
 1  2  3     1  4  7           1  4  7     3  6  9
 4  5  6  →  2  5  8    →→    2  5  8  →  2  5  8
 7  8  9     3  6  9           3  6  9     1  4  7
```

```rust
// Rust — 90° Counter-Clockwise in-place
fn rotate90_counter_clockwise(mat: &mut Matrix) {
    let n = mat.rows;
    // Step 1: Transpose
    for i in 0..n {
        for j in (i + 1)..n {
            let tmp = mat.get(i, j);
            let v = mat.get(j, i);
            mat.set(i, j, v);
            mat.set(j, i, tmp);
        }
    }
    // Step 2: Reverse each COLUMN (not row)
    for j in 0..n {
        let mut top = 0usize;
        let mut bot = n - 1;
        while top < bot {
            let t = mat.get(top, j);
            let b = mat.get(bot, j);
            mat.set(top, j, b);
            mat.set(bot, j, t);
            top += 1;
            bot -= 1;
        }
    }
}
```

### 180° Rotation = Reverse All Rows + Reverse Row Order

```
Or equivalently: Rotate 90° twice, or:
  Reverse each row, then reverse the entire row order.

Step 1: reverse each row      Step 2: reverse row order
 1  2  3     3  2  1           3  2  1     9  8  7
 4  5  6  →  6  5  4    →→    6  5  4  →  6  5  4
 7  8  9     9  8  7           9  8  7     3  2  1
```

---

## 8. Spiral Traversal

### What Is Spiral Traversal?

Visiting every element in a matrix starting from the outer boundary and spiraling inward, like peeling an onion layer by layer.

```
  Matrix:              Spiral Order:
  1   2   3   4        1→2→3→4
  5   6   7   8               ↓
  9  10  11  12        12←11←10←9
 13  14  15  16               ↑         Then inner:
                       5→6→7→8  ...wait, let's trace:
                       13→14→15→16

  Full order:
  1,2,3,4 → 8,12,16 → 15,14,13 → 9,5 → 6,7 → 11,10
```

### The Four-Boundary Approach

```
  top    = 0     (first unvisited row)
  bottom = M-1   (last unvisited row)
  left   = 0     (first unvisited col)
  right  = N-1   (last unvisited col)

  Round 1:                       Round 2:
  +--+--+--+--+                  +--+--+--+--+
  |→ |→ |→ |→ |  top row         |  |→ |→ |  |  top row (shrunk)
  |  |  |  |↓ |  right col       |  |  |  |↓ |  right col (shrunk)
  |  |  |  |↓ |                  |  |  |  |  |
  |← |← |← |↓ |  bottom row     |  |← |← |  |
  |↑ |  |  |  |  left col        |  |  |  |  |
  +--+--+--+--+                  +--+--+--+--+
  top++  bottom--  left++  right--

  Continue until top > bottom OR left > right
```

```c
// C — Spiral traversal
void spiral_order(int* mat, int M, int N, int* result, int* result_size) {
    int top = 0, bottom = M - 1, left = 0, right = N - 1;
    int idx = 0;

    while (top <= bottom && left <= right) {
        // → Traverse top row left to right
        for (int j = left; j <= right; j++)
            result[idx++] = MAT(mat, top, j, N);
        top++;

        // ↓ Traverse right column top to bottom
        for (int i = top; i <= bottom; i++)
            result[idx++] = MAT(mat, i, right, N);
        right--;

        // ← Traverse bottom row right to left (if row still exists)
        if (top <= bottom) {
            for (int j = right; j >= left; j--)
                result[idx++] = MAT(mat, bottom, j, N);
            bottom--;
        }

        // ↑ Traverse left column bottom to top (if col still exists)
        if (left <= right) {
            for (int i = bottom; i >= top; i--)
                result[idx++] = MAT(mat, i, left, N);
            left++;
        }
    }
    *result_size = idx;
}
// Time: O(M*N)  Space: O(1) extra (result array not counted)
```

```rust
// Rust — Spiral traversal
fn spiral_order(mat: &Matrix) -> Vec<i32> {
    let mut result = Vec::with_capacity(mat.rows * mat.cols);
    let (mut top, mut bottom) = (0i32, mat.rows as i32 - 1);
    let (mut left, mut right) = (0i32, mat.cols as i32 - 1);

    while top <= bottom && left <= right {
        // → top row
        for j in left..=right {
            result.push(mat.get(top as usize, j as usize));
        }
        top += 1;

        // ↓ right col
        for i in top..=bottom {
            result.push(mat.get(i as usize, right as usize));
        }
        right -= 1;

        // ← bottom row
        if top <= bottom {
            for j in (left..=right).rev() {
                result.push(mat.get(bottom as usize, j as usize));
            }
            bottom -= 1;
        }

        // ↑ left col
        if left <= right {
            for i in (top..=bottom).rev() {
                result.push(mat.get(i as usize, left as usize));
            }
            left += 1;
        }
    }
    result
}
```

```go
// Go — Spiral traversal
func spiralOrder(mat [][]int, M, N int) []int {
    result := make([]int, 0, M*N)
    top, bottom, left, right := 0, M-1, 0, N-1

    for top <= bottom && left <= right {
        // → top row
        for j := left; j <= right; j++ {
            result = append(result, mat[top][j])
        }
        top++

        // ↓ right col
        for i := top; i <= bottom; i++ {
            result = append(result, mat[i][right])
        }
        right--

        // ← bottom row
        if top <= bottom {
            for j := right; j >= left; j-- {
                result = append(result, mat[bottom][j])
            }
            bottom--
        }

        // ↑ left col
        if left <= right {
            for i := bottom; i >= top; i-- {
                result = append(result, mat[i][left])
            }
            left++
        }
    }
    return result
}
```

### Generating a Spiral Matrix (Fill Outward to Inward)

```
Fill 1..N^2 in spiral order:

  n=4:
   1   2   3   4
  12  13  14   5
  11  16  15   6
  10   9   8   7
```

```rust
// Rust — Generate spiral matrix
fn generate_spiral(n: usize) -> Matrix {
    let mut mat = Matrix::new(n, n);
    let (mut top, mut bottom) = (0i32, n as i32 - 1);
    let (mut left, mut right) = (0i32, n as i32 - 1);
    let mut num = 1i32;

    while top <= bottom && left <= right {
        for j in left..=right { mat.set(top as usize, j as usize, num); num += 1; }
        top += 1;
        for i in top..=bottom { mat.set(i as usize, right as usize, num); num += 1; }
        right -= 1;
        if top <= bottom {
            for j in (left..=right).rev() { mat.set(bottom as usize, j as usize, num); num += 1; }
            bottom -= 1;
        }
        if left <= right {
            for i in (top..=bottom).rev() { mat.set(i as usize, left as usize, num); num += 1; }
            left += 1;
        }
    }
    mat
}
```

---

## 9. Diagonal Traversal

### Understanding All Diagonals

```
A 4x4 matrix has 2*N-1 = 7 diagonals (top-right to bottom-left):

  Diagonal index = i + j:

  i+j=0  i+j=1  i+j=2  i+j=3  i+j=4  i+j=5  i+j=6
  (0,0)  (0,1)  (0,2)  (0,3)  (1,3)  (2,3)  (3,3)
         (1,0)  (1,1)  (1,2)  (2,2)  (3,2)
                (2,0)  (2,1)  (3,1)
                       (3,0)

  For each diagonal d = i + j:
    Elements on this diagonal share the same value of (i + j)
    i ranges from max(0, d-N+1) to min(d, M-1)
    j = d - i
```

```
Main diagonals (top-left to bottom-right):
  Diagonal index = j - i  (or i - j, depending on direction)

  j-i = -3: (3,0)
  j-i = -2: (2,0),(3,1)
  j-i = -1: (1,0),(2,1),(3,2)
  j-i =  0: (0,0),(1,1),(2,2),(3,3)   ← main diagonal
  j-i =  1: (0,1),(1,2),(2,3)
  j-i =  2: (0,2),(1,3)
  j-i =  3: (0,3)
```

```c
// C — Print all anti-diagonals (zigzag order)
void diagonal_traverse(int* mat, int M, int N) {
    // Total diagonals = M + N - 1
    int total_diags = M + N - 1;

    for (int d = 0; d < total_diags; d++) {
        if (d % 2 == 0) {
            // Even diagonal: go upward (↑)
            int r = (d < N) ? 0 : d - N + 1;
            int c = (d < N) ? d : N - 1;
            while (r < M && c >= 0) {
                printf("%d ", MAT(mat, r, c, N));
                r++;
                c--;
            }
        } else {
            // Odd diagonal: go downward (↓)
            int r = (d < M) ? d : M - 1;
            int c = (d < M) ? 0 : d - M + 1;
            while (c < N && r >= 0) {
                printf("%d ", MAT(mat, r, c, N));
                r--;
                c++;
            }
        }
    }
}
```

---

## 10. Layer-by-Layer / Onion Peeling

### Concept

Think of the matrix as concentric "rings" or "layers". Layer 0 is the outermost ring, layer 1 is the next, etc.

```
  4x4 matrix — 2 layers:

  Layer 0 (outermost):    Layer 1 (inner):
  +--+--+--+--+           +--+--+--+--+
  |xx|xx|xx|xx|           |  |  |  |  |
  |xx|  |  |xx|           |  |xx|xx|  |
  |xx|  |  |xx|           |  |xx|xx|  |
  |xx|xx|xx|xx|           |  |  |  |  |
  +--+--+--+--+           +--+--+--+--+

  Number of layers = N / 2  (for N x N matrix)
  Layer k occupies rows [k, N-1-k] and cols [k, N-1-k]
```

### Rotate Layer-by-Layer (Four-Element Cycle)

```
For each layer, rotate 4 elements at a time:

  Layer 0, offset 0 (example 4x4):
  (0,0) → (0,3) → (3,3) → (3,0) → (0,0)   ← cycle of 4

  Step-by-step for one cycle:
  1. Save top-left:  tmp = mat[0][0]
  2. top-left  ← bottom-left:  mat[0][0] = mat[3][0]
  3. bottom-left ← bottom-right: mat[3][0] = mat[3][3]
  4. bottom-right ← top-right:  mat[3][3] = mat[0][3]
  5. top-right ← saved:         mat[0][3] = tmp
```

```c
// C — Rotate 90° clockwise using layer-by-layer four-cycle swap
void rotate90_layer(int* mat, int N) {
    for (int layer = 0; layer < N / 2; layer++) {
        int first = layer;
        int last  = N - 1 - layer;
        for (int i = first; i < last; i++) {
            int offset = i - first;
            // Save top
            int top = MAT(mat, first, i, N);
            // top ← left
            MAT(mat, first, i, N) = MAT(mat, last - offset, first, N);
            // left ← bottom
            MAT(mat, last - offset, first, N) = MAT(mat, last, last - offset, N);
            // bottom ← right
            MAT(mat, last, last - offset, N) = MAT(mat, i, last, N);
            // right ← saved top
            MAT(mat, i, last, N) = top;
        }
    }
}
```

---

## 11. Matrix Search — Sorted Matrix Techniques

### Fully Sorted Matrix — Binary Search

If the matrix is row-sorted AND all rows are connected (last of row i < first of row i+1), treat it as a 1D sorted array.

```
  1   3   5   7
  10  11  16  20
  23  30  34  60

  Flat index <-> 2D:
    mid = (lo + hi) / 2
    row = mid / cols
    col = mid % cols
```

```rust
// Rust — Binary search in fully sorted matrix
fn search_matrix_bs(mat: &Matrix, target: i32) -> bool {
    let (m, n) = (mat.rows, mat.cols);
    let (mut lo, mut hi) = (0i32, (m * n) as i32 - 1);

    while lo <= hi {
        let mid = lo + (hi - lo) / 2;
        let val = mat.get((mid as usize) / n, (mid as usize) % n);
        match val.cmp(&target) {
            std::cmp::Ordering::Equal => return true,
            std::cmp::Ordering::Less  => lo = mid + 1,
            std::cmp::Ordering::Greater => hi = mid - 1,
        }
    }
    false
}
// Time: O(log(M*N))  Space: O(1)
```

### Row-Sorted + Column-Sorted Matrix — Staircase Search

Each row is sorted left→right, each column sorted top→bottom. Use the "staircase" technique starting from **top-right corner**.

```
  1   4   7  11  15
  2   5   8  12  19
  3   6   9  16  22
  10  13  14  17  24
  18  21  23  26  30

  Start at top-right: (0, N-1)
    If mat[i][j] == target: FOUND
    If mat[i][j] >  target: move LEFT  (j--)
    If mat[i][j] <  target: move DOWN  (i++)

  Why top-right? It's the only corner where:
    - Moving left DECREASES the value
    - Moving down INCREASES the value
    → Eliminates one element per step (no backtracking needed)
```

```c
// C — Staircase search
int search_sorted_matrix(int* mat, int M, int N, int target) {
    int i = 0, j = N - 1;   // Start top-right

    while (i < M && j >= 0) {
        int val = MAT(mat, i, j, N);
        if (val == target) return 1;       // Found
        else if (val > target) j--;        // Move left
        else i++;                          // Move down
    }
    return 0;  // Not found
}
// Time: O(M + N)  Space: O(1)
// ⚠ Note: Top-left start does NOT work — both neighbors are larger!
```

```go
// Go — Staircase search
func searchSortedMatrix(mat [][]int, M, N, target int) bool {
    i, j := 0, N-1  // top-right corner
    for i < M && j >= 0 {
        switch {
        case mat[i][j] == target: return true
        case mat[i][j] > target:  j--
        default:                  i++
        }
    }
    return false
}
```

---

## 12. Matrix Multiplication

### What Is It?

Multiplying matrix A (M×K) by matrix B (K×N) produces matrix C (M×N) where:

```
  C[i][j] = sum of (A[i][k] * B[k][j]) for k in 0..K

  For 2x2 example:
  A = [a b]    B = [e f]    C = [ae+bg  af+bh]
      [c d]        [g h]        [ce+dg  cf+dh]

  Dimensions: A is M×K, B is K×N → C is M×N
  Inner dimensions MUST match: cols(A) == rows(B) == K
```

```
  Visualization of dot product for C[i][j]:

  Row i of A:  [ a[i][0]  a[i][1]  a[i][2] ]
                     ×         ×         ×
  Col j of B:  [ b[0][j]  b[1][j]  b[2][j] ]
               ↑ element-wise multiply and sum ↑
```

```c
// C — Naive matrix multiplication O(M*K*N)
// A: M x K,  B: K x N,  C: M x N (pre-allocated, zeroed)
void matmul(int* A, int* B, int* C, int M, int K, int N) {
    // Zero out C
    memset(C, 0, M * N * sizeof(int));

    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < K; k++) {
                // C[i][j] += A[i][k] * B[k][j]
                C[i * N + j] += A[i * K + k] * B[k * N + j];
                // Note: B[k][j] access is column-wise — cache unfriendly!
            }
        }
    }
}
// Time: O(M*K*N)  Space: O(1) extra
```

### Cache-Optimized: ikj Loop Order

```
Problem with ijk: B[k][j] access jumps by N elements each step.

Better: ikj order — A[i][k] is fixed for inner loop,
        B[k][j] is sequential (row access) — cache friendly!

  for i in 0..M:
    for k in 0..K:
      a_ik = A[i][k]        ← load once, reuse N times
      for j in 0..N:
        C[i][j] += a_ik * B[k][j]   ← B[k][j] sequential!
```

```rust
// Rust — Cache-optimized matrix multiplication (ikj order)
fn matmul_optimized(a: &Matrix, b: &Matrix) -> Matrix {
    assert_eq!(a.cols, b.rows, "Incompatible dimensions");
    let (m, k, n) = (a.rows, a.cols, b.cols);
    let mut c = Matrix::new(m, n);

    for i in 0..m {
        for kk in 0..k {
            let a_ik = a.get(i, kk);   // loaded once per (i,k)
            if a_ik == 0 { continue; } // optimization: skip zeros
            for j in 0..n {
                // c[i][j] += a[i][kk] * b[kk][j]
                let prev = c.get(i, j);
                c.set(i, j, prev + a_ik * b.get(kk, j));
            }
        }
    }
    c
}
// Time: O(M*K*N)  Space: O(M*N) for result
// Cache behavior: b.get(kk,j) is sequential in j → cache friendly
```

```go
// Go — Cache-optimized matrix multiplication
func matmul(a, b [][]int, M, K, N int) [][]int {
    c := newMatrix2D(M, N)
    for i := 0; i < M; i++ {
        for k := 0; k < K; k++ {
            aik := a[i][k]
            if aik == 0 { continue }
            for j := 0; j < N; j++ {
                c[i][j] += aik * b[k][j]
            }
        }
    }
    return c
}
```

---

## 13. Submatrix Operations

### Extracting a Submatrix

```
  Original 5x5:               Submatrix rows[1..3], cols[1..3]:
  a b c d e                   f g h
  f g h i j     →→→           k l m
  k l m n o                   p q r
  p q r s t
  u v w x y
```

```rust
// Rust — Extract submatrix
fn extract_submatrix(
    mat: &Matrix,
    row_start: usize, row_end: usize,  // exclusive end
    col_start: usize, col_end: usize,
) -> Matrix {
    let new_rows = row_end - row_start;
    let new_cols = col_end - col_start;
    let mut sub = Matrix::new(new_rows, new_cols);
    for i in 0..new_rows {
        for j in 0..new_cols {
            sub.set(i, j, mat.get(row_start + i, col_start + j));
        }
    }
    sub
}
```

### Maximum Sum Submatrix of Size k×k

```
  For each possible top-left corner (i,j):
  Sum = sum of elements in rows[i..i+k-1], cols[j..j+k-1]

  Naive: O(M*N*k^2) — recomputes overlapping sums
  Optimized: Use 2D prefix sums → O(M*N) preprocessing, O(1) per query
```

---

## 14. Prefix Sum Matrix (2D Prefix Sum)

### Concept — Rectangle Sum in O(1)

**Prefix Sum** (also called a **cumulative sum table**): a precomputed array where `prefix[i][j]` = sum of all elements in the rectangle from `(0,0)` to `(i,j)`.

```
  Original:                   Prefix Sum:
   1   2   3   4                1   3   6  10
   5   6   7   8      →→→       6  14  24  36
   9  10  11  12               15  33  54  78

  prefix[i][j] = mat[i][j]
               + prefix[i-1][j]      (above)
               + prefix[i][j-1]      (left)
               - prefix[i-1][j-1]    (subtract overlap)
```

```
  Query: sum of rectangle (r1,c1) to (r2,c2):

  sum = prefix[r2][c2]
      - prefix[r1-1][c2]    (remove top part)
      - prefix[r2][c1-1]    (remove left part)
      + prefix[r1-1][c1-1]  (add back doubly-removed corner)

  Inclusion-Exclusion diagram:
  +---+---+---+---+
  |###|###|###|###|    ← prefix[r2][c2] = whole rectangle
  |###|   |   |   |    - prefix[r1-1][c2] = top strip
  |###|   |   |   |    - prefix[r2][c1-1] = left strip
  |###|   |   |   |    + prefix[r1-1][c1-1] = overcounted corner
  +---+---+---+---+
```

```c
// C — 2D Prefix Sum
void build_prefix(int* mat, int* prefix, int M, int N) {
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            int val = MAT(mat, i, j, N);
            int above = (i > 0) ? MAT(prefix, i-1, j, N) : 0;
            int left  = (j > 0) ? MAT(prefix, i, j-1, N) : 0;
            int corner = (i > 0 && j > 0) ? MAT(prefix, i-1, j-1, N) : 0;
            MAT(prefix, i, j, N) = val + above + left - corner;
        }
    }
}

int range_sum(int* prefix, int N, int r1, int c1, int r2, int c2) {
    int total = MAT(prefix, r2, c2, N);
    int top   = (r1 > 0) ? MAT(prefix, r1-1, c2, N) : 0;
    int left  = (c1 > 0) ? MAT(prefix, r2, c1-1, N) : 0;
    int corner = (r1 > 0 && c1 > 0) ? MAT(prefix, r1-1, c1-1, N) : 0;
    return total - top - left + corner;
}
// Build: O(M*N)  Query: O(1)
```

```rust
// Rust — 2D Prefix Sum
fn build_prefix(mat: &Matrix) -> Matrix {
    let (m, n) = (mat.rows, mat.cols);
    let mut prefix = Matrix::new(m, n);
    for i in 0..m {
        for j in 0..n {
            let val    = mat.get(i, j);
            let above  = if i > 0 { prefix.get(i-1, j) } else { 0 };
            let left   = if j > 0 { prefix.get(i, j-1) } else { 0 };
            let corner = if i > 0 && j > 0 { prefix.get(i-1, j-1) } else { 0 };
            prefix.set(i, j, val + above + left - corner);
        }
    }
    prefix
}

fn range_sum(prefix: &Matrix, r1: usize, c1: usize, r2: usize, c2: usize) -> i32 {
    let total  = prefix.get(r2, c2);
    let top    = if r1 > 0 { prefix.get(r1-1, c2) } else { 0 };
    let left   = if c1 > 0 { prefix.get(r2, c1-1) } else { 0 };
    let corner = if r1 > 0 && c1 > 0 { prefix.get(r1-1, c1-1) } else { 0 };
    total - top - left + corner
}
```

```go
// Go — 2D Prefix Sum
func buildPrefix(mat [][]int, M, N int) [][]int {
    prefix := newMatrix2D(M, N)
    for i := 0; i < M; i++ {
        for j := 0; j < N; j++ {
            val := mat[i][j]
            above, left, corner := 0, 0, 0
            if i > 0 { above = prefix[i-1][j] }
            if j > 0 { left  = prefix[i][j-1] }
            if i > 0 && j > 0 { corner = prefix[i-1][j-1] }
            prefix[i][j] = val + above + left - corner
        }
    }
    return prefix
}

func rangeSum(prefix [][]int, r1, c1, r2, c2 int) int {
    total := prefix[r2][c2]
    top, left, corner := 0, 0, 0
    if r1 > 0 { top    = prefix[r1-1][c2] }
    if c1 > 0 { left   = prefix[r2][c1-1] }
    if r1 > 0 && c1 > 0 { corner = prefix[r1-1][c1-1] }
    return total - top - left + corner
}
```

---

## 15. Flipping and Reflecting

### Horizontal Flip (Left-Right Mirror)

```
  Original:             Flipped Horizontally:
   1  2  3  4            4  3  2  1
   5  6  7  8    →→→     8  7  6  5
   9 10 11 12            12 11 10  9

  (i, j) → (i, N-1-j)
  Implementation: reverse each row
```

```rust
// Rust — Flip horizontally
fn flip_horizontal(mat: &mut Matrix) {
    for i in 0..mat.rows {
        let mut left = 0;
        let mut right = mat.cols - 1;
        while left < right {
            let l = mat.get(i, left);
            let r = mat.get(i, right);
            mat.set(i, left, r);
            mat.set(i, right, l);
            left += 1;
            right -= 1;
        }
    }
}
```

### Vertical Flip (Up-Down Mirror)

```
  Original:             Flipped Vertically:
   1  2  3  4            9 10 11 12
   5  6  7  8    →→→     5  6  7  8
   9 10 11 12             1  2  3  4

  (i, j) → (M-1-i, j)
  Implementation: swap rows from outside in
```

```go
// Go — Flip vertically
func flipVertical(mat [][]int, M int) {
    top, bottom := 0, M-1
    for top < bottom {
        mat[top], mat[bottom] = mat[bottom], mat[top]
        top++
        bottom--
    }
}
```

---

## 16. Set Zeroes (Marking and Propagation)

### Problem: If an element is 0, set its entire row and column to 0.

```
  Input:               Output:
   1  1  1              1  0  1
   1  0  1      →→→     0  0  0
   1  1  1              1  0  1
```

### Naive Approach — WRONG

```
  ❌ Scan matrix, whenever you see 0, immediately zero out row and col.
     Problem: newly placed zeros will trigger MORE zeroing!
     This cascades and zeroes everything out incorrectly.
```

### Correct Two-Pass Approach

```
  Pass 1: Mark which rows and columns need to be zeroed.
           Use a separate boolean array (rows[] and cols[])
           DO NOT modify the matrix yet!

  Pass 2: Zero out the marked rows and columns.

  Memory: O(M + N) for marker arrays
```

### In-Place O(1) Space — Use First Row/Col as Markers

```
  Use mat[0][j] as marker for column j
  Use mat[i][0] as marker for row i
  Special case: handle mat[0][0] separately (it's shared)

  Step 1: Check if row 0 and col 0 themselves contain zeros
  Step 2: Scan rest of matrix, mark mat[0][j] and mat[i][0]
  Step 3: Zero out based on markers (skip row 0, col 0)
  Step 4: Zero out row 0 and col 0 if needed

  ⚠ Order matters! Don't zero first row/col before using them as markers.
```

```c
// C — Set zeroes in-place O(1) space
void set_zeroes(int* mat, int M, int N) {
    int first_row_zero = 0, first_col_zero = 0;

    // Check if first row has zero
    for (int j = 0; j < N; j++)
        if (MAT(mat, 0, j, N) == 0) { first_row_zero = 1; break; }

    // Check if first col has zero
    for (int i = 0; i < M; i++)
        if (MAT(mat, i, 0, N) == 0) { first_col_zero = 1; break; }

    // Use first row and col as markers (skip [0][0] ambiguity)
    for (int i = 1; i < M; i++)
        for (int j = 1; j < N; j++)
            if (MAT(mat, i, j, N) == 0) {
                MAT(mat, i, 0, N) = 0;  // mark row
                MAT(mat, 0, j, N) = 0;  // mark col
            }

    // Zero out based on markers
    for (int i = 1; i < M; i++)
        for (int j = 1; j < N; j++)
            if (MAT(mat, i, 0, N) == 0 || MAT(mat, 0, j, N) == 0)
                MAT(mat, i, j, N) = 0;

    // Zero first row if needed
    if (first_row_zero)
        for (int j = 0; j < N; j++) MAT(mat, 0, j, N) = 0;

    // Zero first col if needed
    if (first_col_zero)
        for (int i = 0; i < M; i++) MAT(mat, i, 0, N) = 0;
}
// Time: O(M*N)  Space: O(1)
```

---

## 17. Island and Region Problems (DFS/BFS on Matrix)

### The 4-Directional and 8-Directional Neighbors

```
  4-directional (up/down/left/right):      8-directional (includes diagonals):
       [ ]                                  [*][*][*]
  [ ] [x] [ ]                              [*][x][*]
       [ ]                                  [*][*][*]

  Deltas (4-dir): {(-1,0),(+1,0),(0,-1),(0,+1)}
  Deltas (8-dir): {(-1,-1),(-1,0),(-1,+1),
                   ( 0,-1),      ( 0,+1),
                   (+1,-1),(+1,0),(+1,+1)}
```

### Number of Islands — DFS Approach

```
  Grid:                    After DFS from (0,0):
  1 1 0 0 0                 * * 0 0 0
  1 1 0 0 0    Island 1 →   * * 0 0 0
  0 0 1 0 0                 0 0 * 0 0  Island 2
  0 0 0 1 1                 0 0 0 * *  Island 3

  count = 3 islands
```

```rust
// Rust — Count islands (DFS)
fn num_islands(grid: &mut Vec<Vec<u8>>) -> i32 {
    let m = grid.len();
    if m == 0 { return 0; }
    let n = grid[0].len();
    let mut count = 0;

    fn dfs(grid: &mut Vec<Vec<u8>>, i: usize, j: usize) {
        let m = grid.len();
        let n = grid[0].len();
        if grid[i][j] != b'1' { return; }
        grid[i][j] = b'0'; // mark visited
        // 4-directional neighbors
        if i > 0     { dfs(grid, i-1, j); }
        if i+1 < m   { dfs(grid, i+1, j); }
        if j > 0     { dfs(grid, i, j-1); }
        if j+1 < n   { dfs(grid, i, j+1); }
    }

    for i in 0..m {
        for j in 0..n {
            if grid[i][j] == b'1' {
                count += 1;
                dfs(grid, i, j);
            }
        }
    }
    count
}
// Time: O(M*N)  Space: O(M*N) recursion stack worst case
```

```go
// Go — Count islands (BFS — avoids recursion stack overflow)
func numIslands(grid [][]byte) int {
    if len(grid) == 0 { return 0 }
    M, N := len(grid), len(grid[0])
    count := 0
    dirs := [][2]int{{-1,0},{1,0},{0,-1},{0,1}}

    type Point struct{ r, c int }

    for i := 0; i < M; i++ {
        for j := 0; j < N; j++ {
            if grid[i][j] != '1' { continue }
            count++
            queue := []Point{{i, j}}
            grid[i][j] = '0'
            for len(queue) > 0 {
                p := queue[0]
                queue = queue[1:]
                for _, d := range dirs {
                    nr, nc := p.r+d[0], p.c+d[1]
                    if nr >= 0 && nr < M && nc >= 0 && nc < N && grid[nr][nc] == '1' {
                        grid[nr][nc] = '0'
                        queue = append(queue, Point{nr, nc})
                    }
                }
            }
        }
    }
    return count
}
```

---

## 18. Dynamic Programming on Matrix

### Longest Increasing Path in Matrix

```
  Each cell can move to any 4-neighbor with a strictly larger value.
  Find the longest such path.

  Grid:
  9  9  4
  6  6  8
  2  1  1

  Longest path: 1→2→6→9 (length 4)
```

### Minimum Path Sum (Top-Left to Bottom-Right)

```
  Can only move RIGHT or DOWN.

  Grid:
  1  3  1
  1  5  1
  4  2  1

  DP table (dp[i][j] = min cost to reach (i,j)):
  1  4  5
  2  7  6
  6  8  7

  dp[i][j] = mat[i][j] + min(dp[i-1][j], dp[i][j-1])
```

```c
// C — Minimum path sum
int min_path_sum(int* mat, int M, int N) {
    int* dp = (int*)malloc(M * N * sizeof(int));

    MAT(dp, 0, 0, N) = MAT(mat, 0, 0, N);

    // Fill first row
    for (int j = 1; j < N; j++)
        MAT(dp, 0, j, N) = MAT(dp, 0, j-1, N) + MAT(mat, 0, j, N);

    // Fill first column
    for (int i = 1; i < M; i++)
        MAT(dp, i, 0, N) = MAT(dp, i-1, 0, N) + MAT(mat, i, 0, N);

    // Fill rest
    for (int i = 1; i < M; i++) {
        for (int j = 1; j < N; j++) {
            int from_top  = MAT(dp, i-1, j, N);
            int from_left = MAT(dp, i, j-1, N);
            MAT(dp, i, j, N) = MAT(mat, i, j, N) + (from_top < from_left ? from_top : from_left);
        }
    }

    int result = MAT(dp, M-1, N-1, N);
    free(dp);
    return result;
}
// Time: O(M*N)  Space: O(M*N) — can optimize to O(N) with 1D dp
```

```rust
// Rust — Unique paths (count paths from top-left to bottom-right)
fn unique_paths(m: usize, n: usize) -> u64 {
    let mut dp = vec![vec![0u64; n]; m];
    // Base: first row and col = 1 (only one way to reach each)
    for i in 0..m { dp[i][0] = 1; }
    for j in 0..n { dp[0][j] = 1; }

    for i in 1..m {
        for j in 1..n {
            dp[i][j] = dp[i-1][j] + dp[i][j-1];
        }
    }
    dp[m-1][n-1]
}
// Can also be solved with combinatorics: C(M+N-2, M-1)
// dp approach avoids overflow issues for small grids
```

### Maximal Square of 1s

```
  Grid:                 DP table (size of largest square ending here):
  1 0 1 0 0              1 0 1 0 0
  1 0 1 1 1    →→→       1 0 1 1 1
  1 1 1 1 1              1 1 1 2 2
  1 0 0 1 0              1 0 0 1 0

  dp[i][j] = side length of largest all-1 square with bottom-right at (i,j)

  If mat[i][j] == 1:
    dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1
  Else:
    dp[i][j] = 0

  Answer = max(dp[i][j])^2
```

```rust
// Rust — Maximal square
fn maximal_square(matrix: &Vec<Vec<char>>) -> i32 {
    let m = matrix.len();
    if m == 0 { return 0; }
    let n = matrix[0].len();
    let mut dp = vec![vec![0i32; n]; m];
    let mut max_side = 0;

    for i in 0..m {
        for j in 0..n {
            if matrix[i][j] == '1' {
                dp[i][j] = if i == 0 || j == 0 {
                    1
                } else {
                    dp[i-1][j].min(dp[i][j-1]).min(dp[i-1][j-1]) + 1
                };
                max_side = max_side.max(dp[i][j]);
            }
        }
    }
    max_side * max_side
}
```

---

## 19. Zigzag, Anti-Diagonal, and Snake Traversal

### Zigzag (Diagonal Traversal — LeetCode Style)

```
  Matrix:                Zigzag order:
  1  2  3               1  2  4  7  5  3  6  8  9
  4  5  6    →→→
  7  8  9

  Even diagonal (d even): go UP-RIGHT  ↗
  Odd diagonal (d odd):   go DOWN-LEFT ↙
```

### Snake Traversal (Boustrophedon)

```
  Even rows left→right, odd rows right→left:

  → → → →
  ← ← ← ←
  → → → →
  ← ← ← ←
```

```c
// C — Snake/Boustrophedon traversal
void snake_traverse(int* mat, int M, int N) {
    for (int i = 0; i < M; i++) {
        if (i % 2 == 0) {
            // Even rows: left to right
            for (int j = 0; j < N; j++)
                printf("%d ", MAT(mat, i, j, N));
        } else {
            // Odd rows: right to left
            for (int j = N - 1; j >= 0; j--)
                printf("%d ", MAT(mat, i, j, N));
        }
    }
}
```

---

## 20. Matrix as Graph — Adjacency Thinking

### Every Matrix IS a Graph

```
  Each cell (i,j) = a node
  Edges connect adjacent cells (4-dir or 8-dir)
  Edge weight can be based on cell values

  This mental model unlocks:
  - BFS for shortest path in unweighted grid
  - Dijkstra for weighted grid (e.g., cost to traverse)
  - DFS for connectivity (islands, components)
  - Union-Find for disjoint regions
```

### Shortest Path in Binary Matrix (BFS)

```
  0 = passable, 1 = blocked
  Find shortest 8-directional path from (0,0) to (N-1,N-1)

  BFS guarantees shortest path in unweighted graph!
  Each BFS level = one more step from source
```

```rust
// Rust — Shortest path in binary matrix (BFS)
use std::collections::VecDeque;

fn shortest_path_binary_matrix(grid: Vec<Vec<i32>>) -> i32 {
    let n = grid.len();
    if grid[0][0] == 1 || grid[n-1][n-1] == 1 { return -1; }

    let mut dist = vec![vec![i32::MAX; n]; n];
    dist[0][0] = 1;
    let mut queue = VecDeque::new();
    queue.push_back((0usize, 0usize));

    let dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)];

    while let Some((r, c)) = queue.pop_front() {
        if r == n-1 && c == n-1 { return dist[r][c]; }
        for (dr, dc) in &dirs {
            let nr = r as i32 + dr;
            let nc = c as i32 + dc;
            if nr >= 0 && nr < n as i32 && nc >= 0 && nc < n as i32 {
                let (nr, nc) = (nr as usize, nc as usize);
                if grid[nr][nc] == 0 && dist[nr][nc] == i32::MAX {
                    dist[nr][nc] = dist[r][c] + 1;
                    queue.push_back((nr, nc));
                }
            }
        }
    }
    -1
}
```

---

## 21. Common Mistakes — What You Cannot Do and Why

### Mistake 1: Wrong Loop Bounds (Off-by-One)

```
  ❌ WRONG:
  for (int i = 0; i <= M; i++)      // i == M is OUT OF BOUNDS
  for (int j = 0; j <= N; j++)      // j == N is OUT OF BOUNDS

  ✅ CORRECT:
  for (int i = 0; i < M; i++)
  for (int j = 0; j < N; j++)

  The boundary is EXCLUSIVE — the last valid index is M-1 and N-1.
```

### Mistake 2: Transposing Rectangular Matrix In-Place

```
  ❌ WRONG: Applying in-place transpose to a non-square matrix.
     A 3x4 matrix's transpose is 4x3 — different shape!
     You CANNOT do this without allocating a new matrix.

  ✅ CORRECT: Only in-place transpose for SQUARE (N x N) matrices.
     For M x N where M != N: allocate new N x M matrix.
```

### Mistake 3: Confusing Row/Column in Matrix Notation

```
  ❌ Common confusion:
     matrix[col][row]  ← wrong order
     matrix[j][i]      ← when you meant matrix[i][j]

  ✅ Convention: ALWAYS matrix[row][col] = matrix[i][j]
     i = row index   (vertical position, counts DOWN)
     j = col index   (horizontal position, counts RIGHT)

  This is especially dangerous in 2D arrays with non-square shapes!
  If M != N, swapping i/j gives wrong size index.
```

### Mistake 4: Modifying Matrix During Iteration

```
  ❌ WRONG (Set Zeroes problem):
  for each cell:
      if cell == 0:
          zero out its row and col  ← immediately modifies matrix
          This creates new zeros that wrongly trigger more zeroing!

  ✅ CORRECT:
  Pass 1: Collect all positions that are zero.
  Pass 2: Zero out rows and cols based on collected positions.
```

### Mistake 5: Column-Wise Traversal in Row-Major Language

```
  ❌ SLOW (cache-unfriendly):
  for j in 0..N:           // outer = col
      for i in 0..M:       // inner = row
          process(mat[i][j])
  Each mat[i][j] jumps N elements in memory → cache miss!

  ✅ FAST (cache-friendly):
  for i in 0..M:           // outer = row
      for j in 0..N:       // inner = col
          process(mat[i][j])
  Sequential access → cache line reuse!
```

### Mistake 6: Double-Swapping in Transpose

```
  ❌ WRONG:
  for i in 0..N:
      for j in 0..N:        // ← starts from 0, NOT i+1
          swap(mat[i][j], mat[j][i])
  This swaps (0,1) and (1,0), then swaps them BACK when i=1,j=0!

  ✅ CORRECT:
  for i in 0..N:
      for j in (i+1)..N:    // ← only upper triangle
          swap(mat[i][j], mat[j][i])
```

### Mistake 7: Rotation Formula Errors

```
  ❌ Common wrong formula for 90° CW:
     (i, j) → (j, i)         ← This is just transpose, not rotation!
     (i, j) → (N-1-j, i)     ← This is 90° CCW, not CW!

  ✅ Correct formulas:
     90° CW:   (i, j) → (j, N-1-i)
     90° CCW:  (i, j) → (N-1-j, i)
     180°:     (i, j) → (N-1-i, N-1-j)

  Mnemonic for 90° CW:
    "Row becomes column from the bottom"
    New row = old col (j)
    New col = N-1 - old row (N-1-i)
```

### Mistake 8: Prefix Sum Out-of-Bounds

```
  ❌ WRONG (accessing prefix[-1][j]):
  int above = prefix[i-1][j];   // crashes when i == 0!

  ✅ CORRECT:
  int above = (i > 0) ? prefix[i-1][j] : 0;

  Always guard i-1 and j-1 accesses with boundary checks.
```

### Mistake 9: Spiral Traversal — Missing Inner Boundary Check

```
  ❌ WRONG: Missing guard for bottom-row and left-col traversal.
  After traversing top and right, if you've consumed all rows,
  the "bottom" row traversal will retrace already-visited cells!

  ✅ CORRECT: Always check:
  if (top <= bottom): before traversing bottom row
  if (left <= right): before traversing left column

  Single-row or single-col matrices are edge cases that break
  naive spiral implementations.
```

### Mistake 10: DFS Without Visited Marking

```
  ❌ WRONG: DFS on matrix without marking cells as visited.
  Results in infinite loops: cell A visits B, B revisits A...

  ✅ CORRECT: Mark cell visited BEFORE pushing/recursing,
  not after. Use a visited array OR modify the grid (if allowed).

  Also common mistake: using visited[i][j] = true AFTER recursive call.
  This allows re-entry before the call returns!
```

### Mistake 11: Pointer-of-Pointers vs Flat Array Confusion (C)

```
  ❌ WRONG: Using flat-array formula on pointer-of-pointer matrix:
  int** mat = alloc_matrix_pp(3, 4);
  int val = mat[0][1 * 4 + 2];   ← WRONG: tries to index into mat[0][6]
                                    mat[0] only has 4 elements!

  ✅ CORRECT: With pointer-of-pointers, use mat[i][j].
              With flat array, use mat[i * N + j] (or the MAT macro).
```

### Mistake 12: Integer Overflow in Matrix Multiplication

```
  ❌ WRONG: Using int32 for intermediate products of large matrices:
  int C[N][N];
  C[i][j] += A[i][k] * B[k][j];  // A[i][k] and B[k][j] both ~10^4
  Product ~ 10^8, sum of K products ~ K * 10^8 → overflows int32!

  ✅ CORRECT: Use int64/long long for accumulation:
  long long sum = 0;
  for (k) sum += (long long)A[i][k] * B[k][j];
  C[i][j] = (int)sum;
```

### Mistake 13: Allocating Output Matrix with Wrong Dimensions

```
  ❌ WRONG:
  // Transpose of M x N should be N x M
  int* transposed = alloc_matrix(M, N);   ← wrong! Should be (N, M)

  // Matmul of (M x K) * (K x N) should be M x N
  int* C = alloc_matrix(M, K);            ← wrong! Should be (M, N)

  ✅ Think about dimensions before every matrix operation.
```

---

## 22. Expert Mental Models for Matrix Problems

### Model 1 — "What Changes When I Transform?"

Before writing any code, ask: "If I rotate/transpose/flip this matrix, what happens to the coordinate `(i,j)`?" Work out the formula on paper first. This prevents formula errors.

```
  Transformation cheat sheet:
  Transpose:      (i, j) → (j, i)
  Flip Horiz:     (i, j) → (i, N-1-j)
  Flip Vert:      (i, j) → (M-1-i, j)
  Rotate 90 CW:   (i, j) → (j, N-1-i)
  Rotate 90 CCW:  (i, j) → (N-1-j, i)
  Rotate 180:     (i, j) → (M-1-i, N-1-j)
```

### Model 2 — "Reduce to Known Problem"

Many complex matrix problems reduce to known primitives:
- Matrix rotation = transpose + flip
- Spiral = four boundary sweeps
- Island count = connected components in graph (DFS/BFS)
- Max submatrix sum = reduce to 1D Kadane's algorithm column by column
- Count paths = DP with simple recurrence

**Ask**: Can I decompose this into operations I already know?

### Model 3 — "Think in Layers / Rings"

For problems involving concentric boundaries (rotation, spiral), think in layers. Layer `k` spans rows `[k, M-1-k]` and cols `[k, N-1-k]`. Process each layer independently.

### Model 4 — "Precompute for O(1) Queries"

If you're asked many "sum of this rectangle" queries, the answer is almost always 2D prefix sums. Precompute O(M*N) once, answer each query O(1).

### Model 5 — "Reduce 2D to 1D"

Many 2D problems can be reduced to 1D:
- **Max sum submatrix**: Fix left and right column boundaries → reduce to max subarray (Kadane) on row sums
- **Sorted matrix search**: Treat entire matrix as 1D array if fully sorted
- **Matrix DP**: Sometimes you only need the previous row (optimize space to O(N))

```
  Max sum submatrix (fix left col L, right col R):

  Compress each row to a 1D sum:
  rowsum[i] = sum(mat[i][L..R])

  Now find max subarray of rowsum[] using Kadane's!
  This gives max sum submatrix with columns exactly [L,R].
  Run for all (L,R) pairs: O(N^2 * M) total.
```

### Model 6 — "Direction Arrays"

For grid BFS/DFS, always define direction arrays upfront and loop through them. This makes code clean, extensible (4-dir → 8-dir is one change), and less error-prone.

```rust
// Rust — Direction arrays
const DIR4: [(i32, i32); 4] = [(-1,0),(1,0),(0,-1),(0,1)];
const DIR8: [(i32, i32); 8] = [
    (-1,-1),(-1,0),(-1,1),
    ( 0,-1),       (0,1),
    ( 1,-1),(1,0), (1,1),
];

fn neighbors_4(r: i32, c: i32, m: i32, n: i32) -> impl Iterator<Item=(usize, usize)> {
    DIR4.iter().filter_map(move |(dr, dc)| {
        let (nr, nc) = (r + dr, c + dc);
        if nr >= 0 && nr < m && nc >= 0 && nc < n {
            Some((nr as usize, nc as usize))
        } else {
            None
        }
    })
}
```

### Model 7 — "Two-Pointer / Shrinking Window"

For problems with boundaries (spiral traversal, layer processing, sorted matrix search), think of shrinking window pointers: `top`, `bottom`, `left`, `right`. The window shrinks inward as you consume each boundary.

### Model 8 — "Visualize Before Coding"

For every matrix problem, draw a small 4×4 example on paper:
1. Mark which cells you visit and in what order
2. Identify the invariant at each step
3. Write the recurrence or loop logic from the visualization
4. Then code

This is how expert competitive programmers work. The code is the last step, not the first.

---

## Complexity Summary Table

| Operation | Time | Space | Notes |
|---|---|---|---|
| Traverse (row/col) | O(M×N) | O(1) | Row-wise is cache-friendly |
| Transpose (square, in-place) | O(N²) | O(1) | Only upper triangle |
| Transpose (rect, out-place) | O(M×N) | O(M×N) | New array needed |
| Rotate 90° CW (in-place) | O(N²) | O(1) | Transpose + flip |
| Spiral traversal | O(M×N) | O(1) | Four pointer shrink |
| Binary search (sorted) | O(log MN) | O(1) | Flat index trick |
| Staircase search | O(M+N) | O(1) | Start top-right |
| Matrix multiply (naive) | O(M×K×N) | O(M×N) | |
| Matrix multiply (ikj order) | O(M×K×N) | O(M×N) | Better cache |
| 2D Prefix Sum build | O(M×N) | O(M×N) | One-time cost |
| 2D Prefix Sum query | O(1) | O(1) | After build |
| BFS/DFS on grid | O(M×N) | O(M×N) | Visited array |
| Set Zeroes (in-place) | O(M×N) | O(1) | Use row/col as markers |
| Max Submatrix Sum | O(N²×M) | O(M) | Reduce to Kadane |
| Maximal Square | O(M×N) | O(M×N) | DP (can do O(N)) |

---

*End of Guide — Matrix Manipulation Complete Reference*
