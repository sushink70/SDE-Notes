# Comprehensive Matrix Guide for DSA Mastery
> From fundamentals to elite-level algorithms — implementations in C, Go, and Rust

---

## Table of Contents
1. [Mental Model & Memory Layout](#1-mental-model--memory-layout)
2. [Matrix Representation Strategies](#2-matrix-representation-strategies)
3. [Basic Operations](#3-basic-operations)
4. [Matrix Multiplication & Strassen's Algorithm](#4-matrix-multiplication--strassens-algorithm)
5. [Gaussian Elimination & LU Decomposition](#5-gaussian-elimination--lu-decomposition)
6. [Determinant & Matrix Inverse](#6-determinant--matrix-inverse)
7. [DSA Classics: Traversal Patterns](#7-dsa-classics-traversal-patterns)
8. [Rotation & Reflection](#8-rotation--reflection)
9. [Search in Sorted Matrix](#9-search-in-sorted-matrix)
10. [Dynamic Programming on Matrices](#10-dynamic-programming-on-matrices)
11. [Sparse Matrix Representations](#11-sparse-matrix-representations)
12. [Graph as Adjacency Matrix](#12-graph-as-adjacency-matrix)
13. [Matrix Exponentiation (Fast Power)](#13-matrix-exponentiation-fast-power)
14. [Complexity Reference](#14-complexity-reference)

---

## 1. Mental Model & Memory Layout

### The Expert's First Principle
Before writing a single line of code, internalize this: **a matrix is not a 2D grid — it is a 1D array with an indexing convention**. This insight drives every performance optimization.

```
Row-major layout (C, Go, Rust default):
Matrix[i][j] = flat_array[i * COLS + j]

Col-major layout (Fortran, MATLAB):
Matrix[i][j] = flat_array[j * ROWS + i]
```

**Why does this matter?** Cache lines. A modern CPU loads ~64 bytes per cache miss. Iterating in the wrong order (column-first in a row-major layout) causes **N cache misses** instead of **N/8**. For a 1024×1024 matrix multiply, this is a 10–100× performance difference.

### Cache-Aware Access Pattern
```
GOOD — row-major traversal (sequential memory):
for i in rows:
    for j in cols:        ← j is the inner loop → sequential reads
        process(M[i][j])

BAD — column-major traversal in row-major storage:
for j in cols:
    for i in rows:        ← i is the inner loop → stride = COLS = cache thrashing
        process(M[i][j])
```

**Mental model for matrix multiply**: the naive ijk order is cache-friendly for A and C but not B. The ikj order makes B access sequential → significant speedup with zero algorithmic change.

---

## 2. Matrix Representation Strategies

### Strategy 1: Flat Array (Best Performance)

**C Implementation:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct {
    double *data;
    int rows;
    int cols;
} Matrix;

// Allocate: single contiguous block — cache friendly
Matrix mat_new(int rows, int cols) {
    Matrix m;
    m.rows = rows;
    m.cols = cols;
    m.data = (double *)calloc(rows * cols, sizeof(double));
    return m;
}

void mat_free(Matrix *m) {
    free(m->data);
    m->data = NULL;
}

// Access macro: avoids function call overhead
#define MAT(m, i, j) ((m).data[(i) * (m).cols + (j)])

void mat_print(const Matrix *m) {
    for (int i = 0; i < m->rows; i++) {
        for (int j = 0; j < m->cols; j++) {
            printf("%8.3f ", MAT(*m, i, j));
        }
        printf("\n");
    }
}

Matrix mat_identity(int n) {
    Matrix m = mat_new(n, n);
    for (int i = 0; i < n; i++) MAT(m, i, i) = 1.0;
    return m;
}

Matrix mat_copy(const Matrix *src) {
    Matrix dst = mat_new(src->rows, src->cols);
    memcpy(dst.data, src->data, src->rows * src->cols * sizeof(double));
    return dst;
}
```

**Go Implementation:**
```go
package matrix

import (
    "fmt"
    "math"
)

// Matrix uses a flat slice for cache efficiency
type Matrix struct {
    Data []float64
    Rows int
    Cols int
}

func New(rows, cols int) *Matrix {
    return &Matrix{
        Data: make([]float64, rows*cols),
        Rows: rows,
        Cols: cols,
    }
}

func Identity(n int) *Matrix {
    m := New(n, n)
    for i := 0; i < n; i++ {
        m.Set(i, i, 1.0)
    }
    return m
}

func (m *Matrix) At(i, j int) float64 {
    return m.Data[i*m.Cols+j]
}

func (m *Matrix) Set(i, j int, v float64) {
    m.Data[i*m.Cols+j] = v
}

func (m *Matrix) Clone() *Matrix {
    dst := New(m.Rows, m.Cols)
    copy(dst.Data, m.Data)
    return dst
}

func (m *Matrix) Print() {
    for i := 0; i < m.Rows; i++ {
        for j := 0; j < m.Cols; j++ {
            fmt.Printf("%8.3f ", m.At(i, j))
        }
        fmt.Println()
    }
}

// Row returns a slice view into row i — zero allocation
func (m *Matrix) Row(i int) []float64 {
    return m.Data[i*m.Cols : (i+1)*m.Cols]
}
```

**Rust Implementation:**
```rust
use std::fmt;
use std::ops::{Index, IndexMut, Add, Mul, Sub, Neg};

#[derive(Debug, Clone, PartialEq)]
pub struct Matrix {
    pub data: Vec<f64>,
    pub rows: usize,
    pub cols: usize,
}

impl Matrix {
    pub fn new(rows: usize, cols: usize) -> Self {
        Matrix {
            data: vec![0.0; rows * cols],
            rows,
            cols,
        }
    }

    pub fn identity(n: usize) -> Self {
        let mut m = Self::new(n, n);
        for i in 0..n {
            m[(i, i)] = 1.0;
        }
        m
    }

    pub fn from_vec(rows: usize, cols: usize, data: Vec<f64>) -> Self {
        assert_eq!(data.len(), rows * cols, "Data length mismatch");
        Matrix { data, rows, cols }
    }

    #[inline(always)]
    pub fn idx(&self, i: usize, j: usize) -> usize {
        i * self.cols + j
    }

    // Zero-copy row slice
    pub fn row(&self, i: usize) -> &[f64] {
        &self.data[i * self.cols..(i + 1) * self.cols]
    }

    pub fn row_mut(&mut self, i: usize) -> &mut [f64] {
        &mut self.data[i * self.cols..(i + 1) * self.cols]
    }
}

impl Index<(usize, usize)> for Matrix {
    type Output = f64;
    fn index(&self, (i, j): (usize, usize)) -> &f64 {
        &self.data[i * self.cols + j]
    }
}

impl IndexMut<(usize, usize)> for Matrix {
    fn index_mut(&mut self, (i, j): (usize, usize)) -> &mut f64 {
        &mut self.data[i * self.cols + j]
    }
}

impl fmt::Display for Matrix {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        for i in 0..self.rows {
            for j in 0..self.cols {
                write!(f, "{:8.3} ", self[(i, j)])?;
            }
            writeln!(f)?;
        }
        Ok(())
    }
}
```

---

## 3. Basic Operations

### Transpose

**Key insight**: naive transpose is cache-unfriendly on writes. Blocked transpose fixes this by working in cache-sized tiles.

**C:**
```c
// Naive transpose: O(n²) time, O(n²) space
Matrix mat_transpose(const Matrix *a) {
    Matrix t = mat_new(a->cols, a->rows);
    for (int i = 0; i < a->rows; i++)
        for (int j = 0; j < a->cols; j++)
            MAT(t, j, i) = MAT(*a, i, j);
    return t;
}

// In-place transpose (square matrices only)
void mat_transpose_inplace(Matrix *a) {
    // assert a->rows == a->cols
    for (int i = 0; i < a->rows; i++)
        for (int j = i + 1; j < a->cols; j++) {
            double tmp = MAT(*a, i, j);
            MAT(*a, i, j) = MAT(*a, j, i);
            MAT(*a, j, i) = tmp;
        }
}

// Blocked (cache-oblivious) transpose
#define BLOCK 32
Matrix mat_transpose_blocked(const Matrix *a) {
    Matrix t = mat_new(a->cols, a->rows);
    for (int ii = 0; ii < a->rows; ii += BLOCK)
        for (int jj = 0; jj < a->cols; jj += BLOCK)
            for (int i = ii; i < ii + BLOCK && i < a->rows; i++)
                for (int j = jj; j < jj + BLOCK && j < a->cols; j++)
                    MAT(t, j, i) = MAT(*a, i, j);
    return t;
}
```

**Go:**
```go
func (m *Matrix) Transpose() *Matrix {
    t := New(m.Cols, m.Rows)
    for i := 0; i < m.Rows; i++ {
        for j := 0; j < m.Cols; j++ {
            t.Set(j, i, m.At(i, j))
        }
    }
    return t
}

// TransposeInPlace: only for square matrices
func (m *Matrix) TransposeInPlace() {
    for i := 0; i < m.Rows; i++ {
        for j := i + 1; j < m.Cols; j++ {
            m.Data[i*m.Cols+j], m.Data[j*m.Cols+i] =
                m.Data[j*m.Cols+i], m.Data[i*m.Cols+j]
        }
    }
}
```

**Rust:**
```rust
impl Matrix {
    pub fn transpose(&self) -> Matrix {
        let mut t = Matrix::new(self.cols, self.rows);
        for i in 0..self.rows {
            for j in 0..self.cols {
                t[(j, i)] = self[(i, j)];
            }
        }
        t
    }

    pub fn transpose_inplace(&mut self) {
        assert_eq!(self.rows, self.cols, "Only square matrices");
        for i in 0..self.rows {
            for j in i + 1..self.cols {
                let a = self.idx(i, j);
                let b = self.idx(j, i);
                self.data.swap(a, b);
            }
        }
    }
}
```

### Addition & Subtraction

**C:**
```c
Matrix mat_add(const Matrix *a, const Matrix *b) {
    // assert a->rows == b->rows && a->cols == b->cols
    Matrix c = mat_new(a->rows, a->cols);
    int n = a->rows * a->cols;
    for (int k = 0; k < n; k++) c.data[k] = a->data[k] + b->data[k];
    return c;
}

Matrix mat_sub(const Matrix *a, const Matrix *b) {
    Matrix c = mat_new(a->rows, a->cols);
    int n = a->rows * a->cols;
    for (int k = 0; k < n; k++) c.data[k] = a->data[k] - b->data[k];
    return c;
}

Matrix mat_scale(const Matrix *a, double s) {
    Matrix c = mat_copy(a);
    int n = a->rows * a->cols;
    for (int k = 0; k < n; k++) c.data[k] *= s;
    return c;
}
```

**Go:**
```go
func Add(a, b *Matrix) *Matrix {
    c := New(a.Rows, a.Cols)
    for k := range a.Data {
        c.Data[k] = a.Data[k] + b.Data[k]
    }
    return c
}

func Sub(a, b *Matrix) *Matrix {
    c := New(a.Rows, a.Cols)
    for k := range a.Data {
        c.Data[k] = a.Data[k] - b.Data[k]
    }
    return c
}

func Scale(a *Matrix, s float64) *Matrix {
    c := a.Clone()
    for k := range c.Data {
        c.Data[k] *= s
    }
    return c
}
```

**Rust:**
```rust
impl Add for &Matrix {
    type Output = Matrix;
    fn add(self, rhs: &Matrix) -> Matrix {
        assert_eq!((self.rows, self.cols), (rhs.rows, rhs.cols));
        let data = self.data.iter().zip(&rhs.data).map(|(a, b)| a + b).collect();
        Matrix::from_vec(self.rows, self.cols, data)
    }
}

impl Sub for &Matrix {
    type Output = Matrix;
    fn sub(self, rhs: &Matrix) -> Matrix {
        assert_eq!((self.rows, self.cols), (rhs.rows, rhs.cols));
        let data = self.data.iter().zip(&rhs.data).map(|(a, b)| a - b).collect();
        Matrix::from_vec(self.rows, self.cols, data)
    }
}

impl Matrix {
    pub fn scale(&self, s: f64) -> Matrix {
        let data = self.data.iter().map(|x| x * s).collect();
        Matrix::from_vec(self.rows, self.cols, data)
    }
}
```

---

## 4. Matrix Multiplication & Strassen's Algorithm

### Expert Thinking Before Coding

The naive O(n³) multiply has three orders: ijk, ikj, jik, jki, kij, kji. They are **algorithmically equivalent but performance-wise different**:
- **ikj** is fastest in practice: A[i][k] is a scalar (broadcast), B[k][j] is sequential (cache hit), C[i][j] is sequential.
- **ijk** is second: C row sequential, but B column access = stride = cache miss.

For large matrices, true cache-oblivious or BLAS-level blocked multiplication dominates.

**C — Naive ikj (best cache order):**
```c
Matrix mat_mul(const Matrix *a, const Matrix *b) {
    // assert a->cols == b->rows
    Matrix c = mat_new(a->rows, b->cols);
    for (int i = 0; i < a->rows; i++) {
        for (int k = 0; k < a->cols; k++) {
            double aik = MAT(*a, i, k);
            if (aik == 0.0) continue;      // sparsity optimization
            for (int j = 0; j < b->cols; j++) {
                MAT(c, i, j) += aik * MAT(*b, k, j);
            }
        }
    }
    return c;
}

// Blocked matrix multiply: cache-oblivious, practical for large N
#define BSIZE 64
Matrix mat_mul_blocked(const Matrix *a, const Matrix *b) {
    Matrix c = mat_new(a->rows, b->cols);
    for (int ii = 0; ii < a->rows; ii += BSIZE)
        for (int kk = 0; kk < a->cols; kk += BSIZE)
            for (int jj = 0; jj < b->cols; jj += BSIZE)
                for (int i = ii; i < ii+BSIZE && i < a->rows; i++)
                    for (int k = kk; k < kk+BSIZE && k < a->cols; k++) {
                        double aik = MAT(*a, i, k);
                        for (int j = jj; j < jj+BSIZE && j < b->cols; j++)
                            MAT(c, i, j) += aik * MAT(*b, k, j);
                    }
    return c;
}
```

**Go:**
```go
// Mul: ikj order for cache efficiency
func Mul(a, b *Matrix) *Matrix {
    c := New(a.Rows, b.Cols)
    for i := 0; i < a.Rows; i++ {
        for k := 0; k < a.Cols; k++ {
            aik := a.At(i, k)
            if aik == 0 {
                continue
            }
            bRow := b.Row(k)
            cRow := c.Row(i)
            for j, bkj := range bRow {
                cRow[j] += aik * bkj
            }
        }
    }
    return c
}
```

**Rust:**
```rust
impl Mul for &Matrix {
    type Output = Matrix;
    fn mul(self, rhs: &Matrix) -> Matrix {
        assert_eq!(self.cols, rhs.rows, "Dimension mismatch");
        let mut c = Matrix::new(self.rows, rhs.cols);
        for i in 0..self.rows {
            for k in 0..self.cols {
                let aik = self[(i, k)];
                if aik == 0.0 { continue; }
                let b_row = rhs.row(k);
                let c_row = c.row_mut(i);
                for (j, &bkj) in b_row.iter().enumerate() {
                    c_row[j] += aik * bkj;
                }
            }
        }
        c
    }
}
```

### Strassen's Algorithm — O(n^2.807)

**The insight**: naive multiply uses 8 recursive multiplications. Strassen uses 7, trading multiplications for additions. For large n, multiplications dominate.

**Only practical for n > ~256 in real systems (overhead of additions + memory)**

**C — Strassen (conceptual, square power-of-2):**
```c
// Strassen: A and B must be n×n, n a power of 2
// Returns C = A*B using 7 multiplications
Matrix strassen(const Matrix *a, const Matrix *b) {
    int n = a->rows;
    if (n <= 64) return mat_mul(a, b); // base case: revert to ikj

    int h = n / 2;

    // Extract quadrants
    // A = [A11 A12; A21 A22],  B = [B11 B12; B21 B22]
    Matrix A11 = mat_new(h, h), A12 = mat_new(h, h);
    Matrix A21 = mat_new(h, h), A22 = mat_new(h, h);
    Matrix B11 = mat_new(h, h), B12 = mat_new(h, h);
    Matrix B21 = mat_new(h, h), B22 = mat_new(h, h);

    for (int i = 0; i < h; i++) {
        for (int j = 0; j < h; j++) {
            MAT(A11, i, j) = MAT(*a, i, j);
            MAT(A12, i, j) = MAT(*a, i, j+h);
            MAT(A21, i, j) = MAT(*a, i+h, j);
            MAT(A22, i, j) = MAT(*a, i+h, j+h);
            MAT(B11, i, j) = MAT(*b, i, j);
            MAT(B12, i, j) = MAT(*b, i, j+h);
            MAT(B21, i, j) = MAT(*b, i+h, j);
            MAT(B22, i, j) = MAT(*b, i+h, j+h);
        }
    }

    // 7 Strassen sub-problems
    Matrix tmp1, tmp2;
    tmp1 = mat_add(&A11, &A22); tmp2 = mat_add(&B11, &B22);
    Matrix M1 = strassen(&tmp1, &tmp2); mat_free(&tmp1); mat_free(&tmp2);

    tmp1 = mat_add(&A21, &A22);
    Matrix M2 = strassen(&tmp1, &B11); mat_free(&tmp1);

    tmp1 = mat_sub(&B12, &B22);
    Matrix M3 = strassen(&A11, &tmp1); mat_free(&tmp1);

    tmp1 = mat_sub(&B21, &B11);
    Matrix M4 = strassen(&A22, &tmp1); mat_free(&tmp1);

    tmp1 = mat_add(&A11, &A12);
    Matrix M5 = strassen(&tmp1, &B22); mat_free(&tmp1);

    tmp1 = mat_sub(&A21, &A11); tmp2 = mat_add(&B11, &B12);
    Matrix M6 = strassen(&tmp1, &tmp2); mat_free(&tmp1); mat_free(&tmp2);

    tmp1 = mat_sub(&A12, &A22); tmp2 = mat_add(&B21, &B22);
    Matrix M7 = strassen(&tmp1, &tmp2); mat_free(&tmp1); mat_free(&tmp2);

    // Compose result quadrants
    // C11 = M1 + M4 - M5 + M7
    // C12 = M3 + M5
    // C21 = M2 + M4
    // C22 = M1 - M2 + M3 + M6
    Matrix C = mat_new(n, n);
    for (int i = 0; i < h; i++) {
        for (int j = 0; j < h; j++) {
            MAT(C, i,   j)   = MAT(M1,i,j)+MAT(M4,i,j)-MAT(M5,i,j)+MAT(M7,i,j);
            MAT(C, i,   j+h) = MAT(M3,i,j)+MAT(M5,i,j);
            MAT(C, i+h, j)   = MAT(M2,i,j)+MAT(M4,i,j);
            MAT(C, i+h, j+h) = MAT(M1,i,j)-MAT(M2,i,j)+MAT(M3,i,j)+MAT(M6,i,j);
        }
    }

    // Free all temporaries
    mat_free(&A11); mat_free(&A12); mat_free(&A21); mat_free(&A22);
    mat_free(&B11); mat_free(&B12); mat_free(&B21); mat_free(&B22);
    mat_free(&M1); mat_free(&M2); mat_free(&M3); mat_free(&M4);
    mat_free(&M5); mat_free(&M6); mat_free(&M7);
    return C;
}
```

---

## 5. Gaussian Elimination & LU Decomposition

### Expert Mental Model
Gaussian elimination is the foundation of linear algebra computation. Every subsequent algorithm (inverse, determinant, solving systems) builds on it.

**LU decomposition**: factor A = L * U where L is lower-triangular (1s on diagonal) and U is upper-triangular. Once factored, solving Ax = b becomes two O(n²) triangular solves instead of O(n³).

**Partial pivoting** is mandatory for numerical stability — without it, small pivots cause catastrophic floating-point errors.

**C:**
```c
// LU decomposition with partial pivoting
// Returns L and U in-place (combined), perm = permutation array
// Returns sign of permutation (+1 or -1) for determinant calculation
int lu_decompose(Matrix *a, int *perm) {
    int n = a->rows;
    int sign = 1;

    for (int i = 0; i < n; i++) perm[i] = i;

    for (int col = 0; col < n; col++) {
        // Find pivot: max absolute value in current column
        double max_val = fabs(MAT(*a, col, col));
        int max_row = col;
        for (int row = col + 1; row < n; row++) {
            double v = fabs(MAT(*a, row, col));
            if (v > max_val) { max_val = v; max_row = row; }
        }

        if (max_val < 1e-12) {
            fprintf(stderr, "Singular matrix detected\n");
            return 0;
        }

        // Swap rows
        if (max_row != col) {
            for (int j = 0; j < n; j++) {
                double tmp = MAT(*a, col, j);
                MAT(*a, col, j) = MAT(*a, max_row, j);
                MAT(*a, max_row, j) = tmp;
            }
            int tmp = perm[col]; perm[col] = perm[max_row]; perm[max_row] = tmp;
            sign = -sign;
        }

        // Elimination
        double pivot = MAT(*a, col, col);
        for (int row = col + 1; row < n; row++) {
            double factor = MAT(*a, row, col) / pivot;
            MAT(*a, row, col) = factor;  // Store L below diagonal
            for (int j = col + 1; j < n; j++)
                MAT(*a, row, j) -= factor * MAT(*a, col, j);
        }
    }
    return sign;
}

// Forward substitution: solve Ly = b (L has 1s on diagonal)
void forward_sub(const Matrix *lu, const int *perm, const double *b, double *y, int n) {
    for (int i = 0; i < n; i++) {
        y[i] = b[perm[i]];
        for (int j = 0; j < i; j++)
            y[i] -= MAT(*lu, i, j) * y[j];
    }
}

// Back substitution: solve Ux = y
void back_sub(const Matrix *lu, const double *y, double *x, int n) {
    for (int i = n - 1; i >= 0; i--) {
        x[i] = y[i];
        for (int j = i + 1; j < n; j++)
            x[i] -= MAT(*lu, i, j) * x[j];
        x[i] /= MAT(*lu, i, i);
    }
}

// Solve Ax = b
int mat_solve(Matrix *a, double *b, double *x) {
    int n = a->rows;
    int *perm = malloc(n * sizeof(int));
    double *y = malloc(n * sizeof(double));

    if (!lu_decompose(a, perm)) { free(perm); free(y); return 0; }
    forward_sub(a, perm, b, y, n);
    back_sub(a, y, x, n);

    free(perm); free(y);
    return 1;
}
```

**Go:**
```go
// LUDecompose performs in-place LU with partial pivoting
// Returns permutation slice and sign (+1/-1), or error on singular
func LUDecompose(a *Matrix) (perm []int, sign int, err error) {
    n := a.Rows
    perm = make([]int, n)
    for i := range perm { perm[i] = i }
    sign = 1

    for col := 0; col < n; col++ {
        // Find pivot
        maxVal, maxRow := math.Abs(a.At(col, col)), col
        for row := col + 1; row < n; row++ {
            if v := math.Abs(a.At(row, col)); v > maxVal {
                maxVal, maxRow = v, row
            }
        }
        if maxVal < 1e-12 {
            return nil, 0, fmt.Errorf("singular matrix")
        }

        // Swap rows
        if maxRow != col {
            for j := 0; j < n; j++ {
                a.Data[col*n+j], a.Data[maxRow*n+j] =
                    a.Data[maxRow*n+j], a.Data[col*n+j]
            }
            perm[col], perm[maxRow] = perm[maxRow], perm[col]
            sign = -sign
        }

        // Eliminate
        pivot := a.At(col, col)
        for row := col + 1; row < n; row++ {
            factor := a.At(row, col) / pivot
            a.Set(row, col, factor)
            for j := col + 1; j < n; j++ {
                a.Set(row, j, a.At(row, j)-factor*a.At(col, j))
            }
        }
    }
    return perm, sign, nil
}

func ForwardSub(lu *Matrix, perm []int, b []float64) []float64 {
    n := lu.Rows
    y := make([]float64, n)
    for i := 0; i < n; i++ {
        y[i] = b[perm[i]]
        for j := 0; j < i; j++ {
            y[i] -= lu.At(i, j) * y[j]
        }
    }
    return y
}

func BackSub(lu *Matrix, y []float64) []float64 {
    n := lu.Rows
    x := make([]float64, n)
    for i := n - 1; i >= 0; i-- {
        x[i] = y[i]
        for j := i + 1; j < n; j++ {
            x[i] -= lu.At(i, j) * x[j]
        }
        x[i] /= lu.At(i, i)
    }
    return x
}
```

**Rust:**
```rust
#[derive(Debug)]
pub enum MatrixError {
    Singular,
    DimensionMismatch,
}

impl Matrix {
    /// LU decomposition with partial pivoting.
    /// Returns (LU combined, permutation, sign) or MatrixError::Singular
    pub fn lu_decompose(&self) -> Result<(Matrix, Vec<usize>, i32), MatrixError> {
        let n = self.rows;
        let mut lu = self.clone();
        let mut perm: Vec<usize> = (0..n).collect();
        let mut sign = 1i32;

        for col in 0..n {
            // Find max pivot
            let (max_val, max_row) = (col..n)
                .map(|r| (lu[(r, col)].abs(), r))
                .fold((0.0f64, col), |(mv, mr), (v, r)| if v > mv { (v, r) } else { (mv, mr) });

            if max_val < 1e-12 {
                return Err(MatrixError::Singular);
            }

            if max_row != col {
                for j in 0..n {
                    let a = lu.idx(col, j);
                    let b = lu.idx(max_row, j);
                    lu.data.swap(a, b);
                }
                perm.swap(col, max_row);
                sign = -sign;
            }

            let pivot = lu[(col, col)];
            for row in col + 1..n {
                let factor = lu[(row, col)] / pivot;
                lu[(row, col)] = factor;
                for j in col + 1..n {
                    let v = lu[(row, j)] - factor * lu[(col, j)];
                    lu[(row, j)] = v;
                }
            }
        }
        Ok((lu, perm, sign))
    }

    pub fn forward_sub(lu: &Matrix, perm: &[usize], b: &[f64]) -> Vec<f64> {
        let n = lu.rows;
        let mut y = vec![0.0; n];
        for i in 0..n {
            y[i] = b[perm[i]];
            for j in 0..i {
                y[i] -= lu[(i, j)] * y[j];
            }
        }
        y
    }

    pub fn back_sub(lu: &Matrix, y: &[f64]) -> Vec<f64> {
        let n = lu.rows;
        let mut x = vec![0.0; n];
        for i in (0..n).rev() {
            x[i] = y[i];
            for j in i + 1..n {
                x[i] -= lu[(i, j)] * x[j];
            }
            x[i] /= lu[(i, i)];
        }
        x
    }

    pub fn solve(&self, b: &[f64]) -> Result<Vec<f64>, MatrixError> {
        let (lu, perm, _) = self.lu_decompose()?;
        let y = Self::forward_sub(&lu, &perm, b);
        Ok(Self::back_sub(&lu, &y))
    }
}
```

---

## 6. Determinant & Matrix Inverse

**C:**
```c
double mat_determinant(const Matrix *a) {
    Matrix tmp = mat_copy(a);
    int *perm = malloc(a->rows * sizeof(int));
    int sign = lu_decompose(&tmp, perm);
    double det = sign;
    for (int i = 0; i < a->rows; i++) det *= MAT(tmp, i, i);
    mat_free(&tmp);
    free(perm);
    return det;
}

Matrix mat_inverse(const Matrix *a) {
    int n = a->rows;
    Matrix lu = mat_copy(a);
    int *perm = malloc(n * sizeof(int));
    lu_decompose(&lu, perm);

    Matrix inv = mat_new(n, n);
    double *b = calloc(n, sizeof(double));
    double *y = malloc(n * sizeof(double));
    double *x = malloc(n * sizeof(double));

    for (int col = 0; col < n; col++) {
        memset(b, 0, n * sizeof(double));
        b[col] = 1.0;  // b = e_col (standard basis vector)
        forward_sub(&lu, perm, b, y, n);
        back_sub(&lu, y, x, n);
        for (int row = 0; row < n; row++) MAT(inv, row, col) = x[row];
    }

    mat_free(&lu); free(perm); free(b); free(y); free(x);
    return inv;
}
```

**Go:**
```go
func Determinant(a *Matrix) (float64, error) {
    tmp := a.Clone()
    perm, sign, err := LUDecompose(tmp)
    _ = perm
    if err != nil { return 0, err }
    det := float64(sign)
    for i := 0; i < tmp.Rows; i++ { det *= tmp.At(i, i) }
    return det, nil
}

func Inverse(a *Matrix) (*Matrix, error) {
    n := a.Rows
    lu := a.Clone()
    perm, _, err := LUDecompose(lu)
    if err != nil { return nil, err }

    inv := New(n, n)
    b := make([]float64, n)
    for col := 0; col < n; col++ {
        for k := range b { b[k] = 0 }
        b[col] = 1.0
        y := ForwardSub(lu, perm, b)
        x := BackSub(lu, y)
        for row := 0; row < n; row++ { inv.Set(row, col, x[row]) }
    }
    return inv, nil
}
```

**Rust:**
```rust
impl Matrix {
    pub fn determinant(&self) -> Result<f64, MatrixError> {
        let (lu, _, sign) = self.lu_decompose()?;
        let det = (0..self.rows).fold(sign as f64, |acc, i| acc * lu[(i, i)]);
        Ok(det)
    }

    pub fn inverse(&self) -> Result<Matrix, MatrixError> {
        let n = self.rows;
        let (lu, perm, _) = self.lu_decompose()?;
        let mut inv = Matrix::new(n, n);
        let mut b = vec![0.0; n];

        for col in 0..n {
            b.iter_mut().for_each(|x| *x = 0.0);
            b[col] = 1.0;
            let y = Self::forward_sub(&lu, &perm, &b);
            let x = Self::back_sub(&lu, &y);
            for row in 0..n { inv[(row, col)] = x[row]; }
        }
        Ok(inv)
    }
}
```

---

## 7. DSA Classics: Traversal Patterns

### Spiral Traversal

**Expert pattern recognition**: Spiral = boundary-shrinking simulation. Track four boundaries (top, bottom, left, right), peel one layer per iteration.

**C:**
```c
// Returns spiral order in allocated array (caller frees)
int* spiral_order(int **matrix, int rows, int cols, int *out_size) {
    *out_size = rows * cols;
    int *result = malloc(*out_size * sizeof(int));
    int idx = 0;
    int top = 0, bottom = rows - 1, left = 0, right = cols - 1;

    while (top <= bottom && left <= right) {
        for (int j = left; j <= right; j++)   result[idx++] = matrix[top][j];
        top++;
        for (int i = top; i <= bottom; i++)   result[idx++] = matrix[i][right];
        right--;
        if (top <= bottom) {
            for (int j = right; j >= left; j--) result[idx++] = matrix[bottom][j];
            bottom--;
        }
        if (left <= right) {
            for (int i = bottom; i >= top; i--) result[idx++] = matrix[i][left];
            left++;
        }
    }
    return result;
}
```

**Go:**
```go
func SpiralOrder(matrix [][]int) []int {
    if len(matrix) == 0 { return nil }
    rows, cols := len(matrix), len(matrix[0])
    result := make([]int, 0, rows*cols)
    top, bottom, left, right := 0, rows-1, 0, cols-1

    for top <= bottom && left <= right {
        for j := left; j <= right; j++ { result = append(result, matrix[top][j]) }
        top++
        for i := top; i <= bottom; i++ { result = append(result, matrix[i][right]) }
        right--
        if top <= bottom {
            for j := right; j >= left; j-- { result = append(result, matrix[bottom][j]) }
            bottom--
        }
        if left <= right {
            for i := bottom; i >= top; i-- { result = append(result, matrix[i][left]) }
            left++
        }
    }
    return result
}
```

**Rust:**
```rust
pub fn spiral_order(matrix: &[Vec<i32>]) -> Vec<i32> {
    if matrix.is_empty() { return vec![]; }
    let (rows, cols) = (matrix.len(), matrix[0].len());
    let mut result = Vec::with_capacity(rows * cols);
    let (mut top, mut bottom, mut left, mut right) = (0, rows - 1, 0, cols - 1);

    while top <= bottom && left <= right {
        (left..=right).for_each(|j| result.push(matrix[top][j]));
        top += 1;
        if top <= bottom {
            (top..=bottom).for_each(|i| result.push(matrix[i][right]));
        }
        if right >= left + 1 { right -= 1; } else { break; }
        if top <= bottom {
            (left..=right).rev().for_each(|j| result.push(matrix[bottom][j]));
            if bottom == 0 { break; }
            bottom -= 1;
        }
        if left <= right {
            (top..=bottom).rev().for_each(|i| result.push(matrix[i][left]));
            left += 1;
        }
    }
    result
}
```

### Diagonal Traversal

```go
// DiagonalTraverse: zigzag diagonals
// Pattern: diagonals indexed 0..rows+cols-2
// Even diagonal d: traverse bottom-left to top-right
// Odd diagonal d: traverse top-right to bottom-left
func DiagonalTraverse(matrix [][]int) []int {
    if len(matrix) == 0 { return nil }
    rows, cols := len(matrix), len(matrix[0])
    result := make([]int, 0, rows*cols)

    for d := 0; d < rows+cols-1; d++ {
        if d%2 == 0 {
            // Going up: row decreases
            r := min(d, rows-1)
            c := d - r
            for r >= 0 && c < cols {
                result = append(result, matrix[r][c])
                r--; c++
            }
        } else {
            // Going down: row increases
            c := min(d, cols-1)
            r := d - c
            for c >= 0 && r < rows {
                result = append(result, matrix[r][c])
                r++; c--
            }
        }
    }
    return result
}

func min(a, b int) int { if a < b { return a }; return b }
```

---

## 8. Rotation & Reflection

### 90° Clockwise Rotation In-Place

**The mathematical insight**:
- 90° CW: `[i][j] → [j][n-1-i]`
- Equivalently: Transpose, then reverse each row
- 90° CCW: Transpose, then reverse each column
- 180°: Reverse each row, then reverse all rows

**C:**
```c
void rotate_90_cw(int **mat, int n) {
    // Step 1: Transpose
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++) {
            int tmp = mat[i][j]; mat[i][j] = mat[j][i]; mat[j][i] = tmp;
        }
    // Step 2: Reverse each row
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n / 2; j++) {
            int tmp = mat[i][j]; mat[i][j] = mat[i][n-1-j]; mat[i][n-1-j] = tmp;
        }
}

void rotate_90_ccw(int **mat, int n) {
    // Transpose then reverse each column (reverse row order)
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++) {
            int tmp = mat[i][j]; mat[i][j] = mat[j][i]; mat[j][i] = tmp;
        }
    for (int j = 0; j < n; j++)
        for (int i = 0; i < n / 2; i++) {
            int tmp = mat[i][j]; mat[i][j] = mat[n-1-i][j]; mat[n-1-i][j] = tmp;
        }
}
```

**Go:**
```go
func Rotate90CW(matrix [][]int) {
    n := len(matrix)
    // Transpose
    for i := 0; i < n; i++ {
        for j := i + 1; j < n; j++ {
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        }
    }
    // Reverse rows
    for i := 0; i < n; i++ {
        for j, k := 0, n-1; j < k; j, k = j+1, k-1 {
            matrix[i][j], matrix[i][k] = matrix[i][k], matrix[i][j]
        }
    }
}
```

**Rust:**
```rust
pub fn rotate_90_cw(matrix: &mut Vec<Vec<i32>>) {
    let n = matrix.len();
    // Transpose
    for i in 0..n {
        for j in i + 1..n {
            let tmp = matrix[i][j];
            matrix[i][j] = matrix[j][i];
            matrix[j][i] = tmp;
        }
    }
    // Reverse each row
    for row in matrix.iter_mut() {
        row.reverse();
    }
}
```

---

## 9. Search in Sorted Matrix

### Problem: Matrix where rows and columns are sorted

**Brute force**: O(n²)
**Binary search each row**: O(n log n)
**Optimal — Staircase search**: O(n + m) — **the elegant insight**

**Insight**: Start from top-right corner. If current > target: move left. If current < target: move down. Each step eliminates one row or one column.

**C:**
```c
// Searches in matrix where each row and column is sorted ascending
// Returns 1 if found, 0 otherwise; sets *ri, *rj to position
int search_sorted_matrix(int **mat, int rows, int cols, int target, int *ri, int *rj) {
    int r = 0, c = cols - 1;
    while (r < rows && c >= 0) {
        if (mat[r][c] == target) { *ri = r; *rj = c; return 1; }
        else if (mat[r][c] > target) c--;
        else r++;
    }
    return 0;
}

// Binary search for Leetcode 74 (completely sorted: each row continues from last)
int search_sorted_matrix2(int **mat, int rows, int cols, int target) {
    int lo = 0, hi = rows * cols - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        int val = mat[mid / cols][mid % cols];
        if (val == target) return 1;
        else if (val < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return 0;
}
```

**Go:**
```go
// SearchSortedMatrix: O(m+n) staircase — LC 240
func SearchSortedMatrix(matrix [][]int, target int) bool {
    if len(matrix) == 0 { return false }
    r, c := 0, len(matrix[0])-1
    for r < len(matrix) && c >= 0 {
        switch {
        case matrix[r][c] == target: return true
        case matrix[r][c] > target: c--
        default: r++
        }
    }
    return false
}

// SearchMatrix2: completely sorted — O(log(m*n)) — LC 74
func SearchMatrix(matrix [][]int, target int) bool {
    rows, cols := len(matrix), len(matrix[0])
    lo, hi := 0, rows*cols-1
    for lo <= hi {
        mid := (lo + hi) / 2
        val := matrix[mid/cols][mid%cols]
        if val == target { return true }
        if val < target { lo = mid + 1 } else { hi = mid - 1 }
    }
    return false
}
```

**Rust:**
```rust
pub fn search_sorted_matrix(matrix: &[Vec<i32>], target: i32) -> bool {
    if matrix.is_empty() { return false; }
    let (mut r, mut c) = (0usize, matrix[0].len() - 1);
    while r < matrix.len() {
        match matrix[r][c].cmp(&target) {
            std::cmp::Ordering::Equal => return true,
            std::cmp::Ordering::Greater => {
                if c == 0 { break; }
                c -= 1;
            }
            std::cmp::Ordering::Less => r += 1,
        }
    }
    false
}
```

---

## 10. Dynamic Programming on Matrices

### Minimum Path Sum (LC 64)

**State**: `dp[i][j]` = min cost to reach cell (i,j)
**Transition**: `dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])`
**Optimization**: modify in place, O(1) extra space

```go
func MinPathSum(grid [][]int) int {
    rows, cols := len(grid), len(grid[0])
    // Fill first row and column
    for j := 1; j < cols; j++ { grid[0][j] += grid[0][j-1] }
    for i := 1; i < rows; i++ { grid[i][0] += grid[i-1][0] }
    // Fill rest
    for i := 1; i < rows; i++ {
        for j := 1; j < cols; j++ {
            if grid[i-1][j] < grid[i][j-1] {
                grid[i][j] += grid[i-1][j]
            } else {
                grid[i][j] += grid[i][j-1]
            }
        }
    }
    return grid[rows-1][cols-1]
}
```

### Maximal Rectangle (LC 85) — Expert Level

**Insight**: Treat each row as a histogram base. For each row, compute max rectangle in histogram (LC 84) using a stack. Time O(mn), Space O(n).

```go
func MaximalRectangle(matrix [][]byte) int {
    if len(matrix) == 0 { return 0 }
    cols := len(matrix[0])
    heights := make([]int, cols)
    maxArea := 0

    for _, row := range matrix {
        // Build histogram heights
        for j := 0; j < cols; j++ {
            if row[j] == '1' { heights[j]++ } else { heights[j] = 0 }
        }
        maxArea = max(maxArea, largestRectangleInHistogram(heights))
    }
    return maxArea
}

func largestRectangleInHistogram(heights []int) int {
    stack := []int{}  // indices, maintains increasing heights
    maxArea := 0
    n := len(heights)

    for i := 0; i <= n; i++ {
        h := 0
        if i < n { h = heights[i] }
        for len(stack) > 0 && heights[stack[len(stack)-1]] > h {
            top := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            width := i
            if len(stack) > 0 { width = i - stack[len(stack)-1] - 1 }
            maxArea = max(maxArea, heights[top]*width)
        }
        stack = append(stack, i)
    }
    return maxArea
}

func max(a, b int) int { if a > b { return a }; return b }
```

### Count Islands (LC 200) — DFS / BFS on Matrix

```rust
pub fn num_islands(grid: &mut Vec<Vec<char>>) -> i32 {
    let mut count = 0;
    for i in 0..grid.len() {
        for j in 0..grid[0].len() {
            if grid[i][j] == '1' {
                dfs_sink(grid, i, j);
                count += 1;
            }
        }
    }
    count
}

fn dfs_sink(grid: &mut Vec<Vec<char>>, i: usize, j: usize) {
    if i >= grid.len() || j >= grid[0].len() || grid[i][j] != '1' { return; }
    grid[i][j] = '0';  // Sink visited cells
    if i > 0 { dfs_sink(grid, i - 1, j); }
    dfs_sink(grid, i + 1, j);
    if j > 0 { dfs_sink(grid, i, j - 1); }
    dfs_sink(grid, i, j + 1);
}
```

---

## 11. Sparse Matrix Representations

When density < ~10%, dense storage wastes memory. Three standard representations:

### COO (Coordinate Format)
Simple for construction. Poor for arithmetic.

### CSR (Compressed Sparse Row)
Industry standard. O(1) row access, efficient SpMV (sparse matrix-vector multiply).

**C:**
```c
typedef struct {
    int *row_ptr;   // size: rows+1 — row_ptr[i] to row_ptr[i+1] = range in col/val
    int *col_idx;   // column indices of non-zeros
    double *values; // non-zero values
    int rows, cols, nnz;
} CSRMatrix;

CSRMatrix csr_new(int rows, int cols, int nnz) {
    CSRMatrix m;
    m.rows = rows; m.cols = cols; m.nnz = nnz;
    m.row_ptr = calloc(rows + 1, sizeof(int));
    m.col_idx = malloc(nnz * sizeof(int));
    m.values  = malloc(nnz * sizeof(double));
    return m;
}

// Sparse matrix-vector multiply: y = A*x, O(nnz)
void csr_spmv(const CSRMatrix *A, const double *x, double *y) {
    for (int i = 0; i < A->rows; i++) {
        y[i] = 0.0;
        for (int k = A->row_ptr[i]; k < A->row_ptr[i+1]; k++)
            y[i] += A->values[k] * x[A->col_idx[k]];
    }
}
```

**Go:**
```go
type CSRMatrix struct {
    RowPtr []int
    ColIdx []int
    Values []float64
    Rows, Cols, NNZ int
}

func (A *CSRMatrix) SpMV(x []float64) []float64 {
    y := make([]float64, A.Rows)
    for i := 0; i < A.Rows; i++ {
        for k := A.RowPtr[i]; k < A.RowPtr[i+1]; k++ {
            y[i] += A.Values[k] * x[A.ColIdx[k]]
        }
    }
    return y
}

// Convert dense to CSR
func DenseToCSR(m *Matrix) *CSRMatrix {
    csr := &CSRMatrix{Rows: m.Rows, Cols: m.Cols}
    csr.RowPtr = make([]int, m.Rows+1)
    for i := 0; i < m.Rows; i++ {
        for j := 0; j < m.Cols; j++ {
            if v := m.At(i, j); v != 0 {
                csr.ColIdx = append(csr.ColIdx, j)
                csr.Values = append(csr.Values, v)
                csr.NNZ++
            }
        }
        csr.RowPtr[i+1] = csr.NNZ
    }
    return csr
}
```

**Rust:**
```rust
pub struct CSRMatrix {
    pub row_ptr: Vec<usize>,
    pub col_idx: Vec<usize>,
    pub values:  Vec<f64>,
    pub rows: usize,
    pub cols: usize,
}

impl CSRMatrix {
    pub fn spmv(&self, x: &[f64]) -> Vec<f64> {
        let mut y = vec![0.0; self.rows];
        for i in 0..self.rows {
            for k in self.row_ptr[i]..self.row_ptr[i + 1] {
                y[i] += self.values[k] * x[self.col_idx[k]];
            }
        }
        y
    }

    pub fn from_dense(m: &Matrix) -> Self {
        let mut row_ptr = vec![0usize; m.rows + 1];
        let mut col_idx = Vec::new();
        let mut values  = Vec::new();

        for i in 0..m.rows {
            for j in 0..m.cols {
                if m[(i, j)] != 0.0 {
                    col_idx.push(j);
                    values.push(m[(i, j)]);
                }
            }
            row_ptr[i + 1] = values.len();
        }
        CSRMatrix { row_ptr, col_idx, values, rows: m.rows, cols: m.cols }
    }
}
```

---

## 12. Graph as Adjacency Matrix

```go
type Graph struct {
    Adj  *Matrix
    N    int
}

func NewGraph(n int) *Graph {
    return &Graph{Adj: New(n, n), N: n}
}

func (g *Graph) AddEdge(u, v int, weight float64) {
    g.Adj.Set(u, v, weight)
    g.Adj.Set(v, u, weight) // undirected; remove for directed
}

// Floyd-Warshall: all-pairs shortest paths, O(n³)
func (g *Graph) FloydWarshall() *Matrix {
    dist := g.Adj.Clone()
    n := g.N

    // Initialize: 0 on diagonal, inf where no edge
    for i := 0; i < n; i++ {
        for j := 0; j < n; j++ {
            if i == j { dist.Set(i, j, 0) }
            if i != j && dist.At(i, j) == 0 { dist.Set(i, j, math.Inf(1)) }
        }
    }

    for k := 0; k < n; k++ {
        for i := 0; i < n; i++ {
            for j := 0; j < n; j++ {
                if through := dist.At(i, k) + dist.At(k, j); through < dist.At(i, j) {
                    dist.Set(i, j, through)
                }
            }
        }
    }
    return dist
}

// Transitive closure (reachability), O(n³)
func (g *Graph) TransitiveClosure() [][]bool {
    n := g.N
    reach := make([][]bool, n)
    for i := range reach {
        reach[i] = make([]bool, n)
        for j := 0; j < n; j++ {
            reach[i][j] = g.Adj.At(i, j) != 0 || i == j
        }
    }
    for k := 0; k < n; k++ {
        for i := 0; i < n; i++ {
            for j := 0; j < n; j++ {
                reach[i][j] = reach[i][j] || (reach[i][k] && reach[k][j])
            }
        }
    }
    return reach
}
```

---

## 13. Matrix Exponentiation (Fast Power)

**The crown jewel of matrix DSA**: Any linear recurrence can be expressed as matrix multiplication. Matrix exponentiation computes M^n in O(k³ log n) where k is the matrix dimension.

**Classic use cases**: Fibonacci in O(log n), counting paths of length n in a graph, solving linear recurrences.

**The Key Insight**: Fibonacci satisfies:
```
[F(n+1)]   [1 1]^n   [F(1)]
[F(n)  ] = [1 0]   * [F(0)]
```

**C:**
```c
Matrix mat_pow(Matrix base, long long exp) {
    int n = base.rows;
    Matrix result = mat_identity(n);
    while (exp > 0) {
        if (exp & 1) {
            Matrix tmp = mat_mul(&result, &base);
            mat_free(&result);
            result = tmp;
        }
        Matrix tmp = mat_mul(&base, &base);
        mat_free(&base);
        base = tmp;
        exp >>= 1;
    }
    return result;
}

long long fibonacci(long long n) {
    if (n <= 1) return n;
    Matrix base = mat_new(2, 2);
    MAT(base, 0, 0) = 1; MAT(base, 0, 1) = 1;
    MAT(base, 1, 0) = 1; MAT(base, 1, 1) = 0;
    Matrix result = mat_pow(base, n - 1);
    long long fib = (long long)MAT(result, 0, 0);
    mat_free(&result);
    return fib;
}
```

**Go:**
```go
func MatPow(base *Matrix, exp int) *Matrix {
    n := base.Rows
    result := Identity(n)
    for exp > 0 {
        if exp&1 == 1 {
            result = Mul(result, base)
        }
        base = Mul(base, base)
        exp >>= 1
    }
    return result
}

func Fibonacci(n int) int64 {
    if n <= 1 { return int64(n) }
    base := New(2, 2)
    base.Set(0, 0, 1); base.Set(0, 1, 1)
    base.Set(1, 0, 1); base.Set(1, 1, 0)
    result := MatPow(base, n-1)
    return int64(result.At(0, 0))
}
```

**Rust:**
```rust
impl Matrix {
    pub fn pow(&self, mut exp: u64) -> Matrix {
        let n = self.rows;
        let mut result = Matrix::identity(n);
        let mut base = self.clone();
        while exp > 0 {
            if exp & 1 == 1 {
                result = &result * &base;
            }
            base = &base * &base;
            exp >>= 1;
        }
        result
    }
}

pub fn fibonacci(n: u64) -> i64 {
    if n <= 1 { return n as i64; }
    let base = Matrix::from_vec(2, 2, vec![1.0, 1.0, 1.0, 0.0]);
    let result = base.pow(n - 1);
    result[(0, 0)] as i64
}
```

---

## 14. Complexity Reference

| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| Access M[i][j] | O(1) | — | Flat array |
| Transpose | O(mn) | O(mn) | Out-of-place |
| Transpose in-place | O(n²) | O(1) | Square only |
| Add/Sub | O(mn) | O(mn) | |
| Multiply (naive ikj) | O(n³) | O(n²) | Best cache order |
| Multiply (Strassen) | O(n^2.807) | O(n²) | n > 256 practical |
| LU Decompose | O(n³) | O(n²) | In-place possible |
| Solve Ax=b | O(n³) | O(n²) | Via LU |
| Determinant | O(n³) | O(n²) | Via LU |
| Inverse | O(n³) | O(n²) | Via LU |
| Matrix Power | O(k³ log n) | O(k²) | k=dim, n=exponent |
| Floyd-Warshall | O(n³) | O(n²) | All-pairs SP |
| Spiral traversal | O(mn) | O(1) | Boundary shrink |
| Search sorted | O(m+n) | O(1) | Staircase |
| Maximal Rectangle | O(mn) | O(n) | Histogram stack |
| CSR SpMV | O(nnz) | O(nnz) | Sparse mul |

---

## Cognitive Synthesis: Pattern Recognition Map

```
MATRIX PROBLEM TYPE → TECHNIQUE

"traverse in pattern"         → Boundary simulation (spiral, layers)
"rotate/flip"                 → Transpose + reverse
"find in sorted"              → Staircase O(m+n) or binary O(log mn)
"count connected regions"     → DFS/BFS sink visited
"max area rectangle"          → Histogram stack per row
"path optimization"           → DP, dp[i][j] from neighbors
"nth Fibonacci / recurrence"  → Matrix exponentiation O(log n)
"all-pairs shortest path"     → Floyd-Warshall O(n³)
"linear system Ax=b"          → LU decomposition + triangular solve
"large sparse matrix"         → CSR + SpMV
"matrix multiply large n"     → Cache-blocked ikj or Strassen
```

**The monk's final principle**: Matrix problems reduce to two fundamental operations — **traversal** (which boundary/direction/pattern?) and **transformation** (which algebraic structure maps input to output?). Train your eye to see these immediately. The code follows naturally.

Here's your complete matrix guide — 14 topics, all three languages (C, Go, Rust), covering every layer from memory layout to elite algorithms.

**What's inside and why it's structured this way:**

The guide is ordered by *abstraction depth* — memory layout → basic ops → numerical linear algebra → DSA patterns → advanced algorithms. This mirrors how world-class engineers think: foundation first, then application.

**The three most important ideas to internalize:**

**1. Memory is everything.** The flat array + row-major indexing insight (`M[i][j] = data[i*cols+j]`) is not a detail — it's the difference between a matrix multiply that runs in 2s vs 20s. The `ikj` loop order in multiplication exploits this directly.

**2. LU decomposition is the master key.** Determinant, inverse, and linear system solving all reduce to a single LU factorization. Once you have LU, every subsequent operation is O(n²) instead of O(n³). Partial pivoting is non-negotiable for numerical stability.

**3. Matrix exponentiation is the hidden weapon.** Every time you see "compute the nth term of a recurrence in O(log n)" — that's matrix exponentiation. It converts Fibonacci, path counting, and linear recurrences from O(n) to O(log n). This appears frequently in competitive programming.

**Pattern recognition table** at the bottom is the synthesis — memorize the problem-type-to-technique mappings. That's what separates top 1% solvers from the rest: instant pattern recognition before touching the keyboard.