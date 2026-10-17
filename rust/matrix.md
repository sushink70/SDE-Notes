# How the matrix is stored

## 1. The core idea: a 2D grid stored as a flat 1D array

Both implementations store a matrix as three things: the row count, the column count, and one flat buffer. Rows are laid end to end (**row-major** order).

```
Logical view (2 x 3):              Physical memory (flat, contiguous):

        col0 col1 col2               index:   0    1    2    3    4    5
       ┌────┬────┬────┐                     ┌────┬────┬────┬────┬────┬────┐
 row0  │ 1  │ 2  │ 3  │                     │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │
       ├────┼────┼────┤                     └────┴────┴────┴────┴────┴────┘
 row1  │ 4  │ 5  │ 6  │                      └── row 0 ──┘└── row 1 ──┘
       └────┴────┴────┘
```

The index of element `(r, c)` is:

```
index = r * cols + c

(0,0) → 0*3+0 = 0  → 1        (1,0) → 1*3+0 = 3  → 4
(0,2) → 0*3+2 = 2  → 3        (1,2) → 1*3+2 = 5  → 6
```

The formula uses `cols`, not `rows`. To skip a whole row you jump `cols` elements.

---

## 2. What it looks like in memory

### Go

```
 STACK / caller                         HEAP
┌──────────────┐        ┌───────────────────────────────────────┐
│ a  (*Matrix) │───────►│ Matrix struct                         │
│  8-byte ptr  │        │  rows : int  = 2                      │
└──────────────┘        │  cols : int  = 3                      │
                        │  data : []float64  (slice header)     │
                        │     ├─ ptr ───────────┐               │
                        │     ├─ len = 6        │               │
                        │     └─ cap = 6        │               │
                        └───────────────────────┼───────────────┘
                                                ▼
                        ┌─────┬─────┬─────┬─────┬─────┬─────┐
                        │ 1.0 │ 2.0 │ 3.0 │ 4.0 │ 5.0 │ 6.0 │  backing array
                        └─────┴─────┴─────┴─────┴─────┴─────┘  (6 × 8 bytes = 48 B)
```

A Go slice is a small header (pointer, length, capacity) that points at a backing array. `New` returns `*Matrix`, so the struct itself is also on the heap. Go's escape analysis decides this, and callers share one struct instead of copying it.

### Rust

```
 STACK (the Matrix value lives right here)           HEAP
┌──────────────────────────────────┐
│ a : Matrix                       │
│   rows : usize = 2               │
│   cols : usize = 3               │
│   data : Vec<f64>                │
│      ├─ ptr ─────────────────────┼───►┌─────┬─────┬─────┬─────┬─────┬─────┐
│      ├─ cap = 6                  │    │ 1.0 │ 2.0 │ 3.0 │ 4.0 │ 5.0 │ 6.0 │
│      └─ len = 6                  │    └─────┴─────┴─────┴─────┴─────┴─────┘
└──────────────────────────────────┘
```

A `Vec<f64>` is also pointer, capacity and length, but it **owns** its heap buffer. When `a` goes out of scope, Rust drops the `Vec` and frees the buffer automatically, with no garbage collector. The `Matrix` struct is a plain stack value, and only the numbers are on the heap. (Rust doesn't guarantee field order in memory; the diagram shows the logical layout.)

---

## 3. Construction

### `New(rows, cols)`: zero-filled

```
New(2,3):   rows=2  cols=3  data=[0 0 0 0 0 0]
                                  └─ one allocation of rows*cols floats
```

### `FromSlice` / `from_vec`: flattening nested input

The input is a slice of slices, which is scattered in memory:

```
 input [][]float64                       
┌────────┐   ┌───────────────┐
│ hdr0 ──┼──►│ 1.0  2.0  3.0 │   separate allocation
├────────┤   └───────────────┘
│ hdr1 ──┼──►┌───────────────┐
└────────┘   │ 4.0  5.0  6.0 │   another separate allocation
             └───────────────┘
                    │ copy each row into position i*cols
                    ▼
             ┌─────┬─────┬─────┬─────┬─────┬─────┐
             │ 1.0 │ 2.0 │ 3.0 │ 4.0 │ 5.0 │ 6.0 │  one contiguous buffer
             └─────┴─────┴─────┴─────┴─────┴─────┘
```

- In Go: `copy(m.data[i*m.cols:], row)` copies row `i` to its slot.
- In Rust: `v.into_iter().flatten().collect()` concatenates the rows.
- Both first check that every row has the same length (rejecting "ragged" input), because the flat layout can't represent uneven rows.

### `Identity(n)`: ones on the diagonal

```
n=3:  index = i*3 + i  →  0, 4, 8

 ┌───┬───┬───┐       flat:  1 0 0 0 1 0 0 0 1
 │ 1 │ 0 │ 0 │              ▲       ▲       ▲
 │ 0 │ 1 │ 0 │              0       4       8
 │ 0 │ 0 │ 1 │
 └───┴───┴───┘
```

---

## 4. Access and modification

```go
// Go
func (m *Matrix) At(r, c int) float64     { return m.data[r*m.cols+c] }
func (m *Matrix) Set(r, c int, v float64) { m.data[r*m.cols+c] = v }
```

```rust
// Rust: m[(r, c)] calls Index::index / IndexMut::index_mut
&self.data[r * self.cols + c]
```

Step by step for `m.Set(1, 1, 99)` on the 2×3 matrix:

```
1. compute index:  1*3 + 1 = 4
2. write to data[4]

before: │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │
                          ▲
                          └─ index 4
after:  │ 1 │ 2 │ 3 │ 4 │99 │ 6 │
```

Rust's `m[(1,1)]` is syntax sugar over the `Index` and `IndexMut` traits:

```
m[(1,1)]        read   → *Index::index(&m, (1,1))
m[(1,1)] = 9.0  write  → *IndexMut::index_mut(&mut m, (1,1)) = 9.0
```

`index` returns a shared reference (`&f64`) and `index_mut` returns an exclusive one (`&mut f64`). The borrow checker enforces that you can't read and write the same matrix at the same time.

### ⚠️ Gotcha: bounds checking is only on the flat array

Go and Rust both check the flat index against `len`, not each coordinate:

```
2x3 matrix, At(0, 5):   index = 0*3 + 5 = 5   → within len 6 → no panic!
                        returns data[5] = 6, which is really (1, 2)

At(2, 0):               index = 6 → out of range → panic
```

So an out-of-range column can silently wrap into the next row. For production code, add explicit checks (`if r >= m.rows || c >= m.cols { panic }`).

---

## 5. Operations

### Add: element-wise, one flat loop

Both matrices have the same shape and the same layout, so there's no need for nested loops:

```
  A: │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │
  B: │ 7 │ 8 │ 9 │10 │11 │12 │
       +   +   +   +   +   +
  C: │ 8 │10 │12 │14 │16 │18 │      res.data[i] = a.data[i] + b.data[i]
```

The dimension check comes first. Adding 2×3 to 3×2 is mathematically undefined, so it returns an error.

### Scale

Same idea, one loop, with each element multiplied by `s`.

### Transpose: swap rows and columns

```
A (2x3)                         Aᵀ (3x2)
┌───┬───┬───┐                   ┌───┬───┐
│ 1 │ 2 │ 3 │                   │ 1 │ 4 │
├───┼───┼───┤        ──►        ├───┼───┤
│ 4 │ 5 │ 6 │                   │ 2 │ 5 │
└───┴───┴───┘                   ├───┼───┤
                                │ 3 │ 6 │
                                └───┴───┘

Rule:  Aᵀ(j, i) = A(i, j)

A  flat: 1 2 3 4 5 6
Aᵀ flat: 1 4 2 5 3 6     ← a NEW buffer; elements are physically rearranged
```

Walking through one element, `A(0,2) = 3`:

```
source index:  0*3 + 2 = 2
dest   (2, 0): 2*2 + 0 = 4   (Aᵀ has cols = 2)
→ Aᵀ.data[4] = A.data[2] = 3
```

The dimensions swap (`New(m.cols, m.rows)`), and the result is a fresh allocation. This implementation doesn't create a lazy "view".

### Multiply: `C = A × B`

Rule: `C(i,j) = Σₖ A(i,k) · B(k,j)`. Each output cell is a dot product of a row of A and a column of B. Here `A` is 2×3, `B` is 3×2, and the result is 2×2. Only the inner dimension (`A.cols == B.rows`) has to match:

```
        B (3x2)
        ┌────┬────┐
        │  7 │  8 │
        │  9 │ 10 │
        │ 11 │ 12 │
        └────┴────┘
A (2x3)         C (2x2)
┌───┬───┬───┐   ┌─────────────┬─────────────┐
│ 1 │ 2 │ 3 │   │ 1·7+2·9+3·11│ 1·8+2·10+3·12│
├───┼───┼───┤   │     = 58    │     = 64     │
│ 4 │ 5 │ 6 │   ├─────────────┼──────────────┤
└───┴───┴───┘   │ 4·7+5·9+6·11│ 4·8+5·10+6·12│
                │     = 139   │     = 154    │
                └─────────────┴──────────────┘
```

The loop order matters for performance:

```go
for i := 0; i < m.rows; i++ {          // row of A / row of C
    for k := 0; k < m.cols; k++ {      // shared dimension
        a := m.At(i, k)                // loaded once, reused in the inner loop
        for j := 0; j < o.cols; j++ {  // column of B / column of C
            res[i][j] += a * o.At(k, j)
        }
    }
}
```

This is the **i-k-j** order. The inner loop walks `o` and `res` along a row, which is sequential memory, so it's cache-friendly:

```
inner loop (j varies), i and k fixed:

 B row k:    ▶ │ B(k,0) │ B(k,1) │ B(k,2) │ ...   adjacent → fast
 C row i:    ▶ │ C(i,0) │ C(i,1) │ C(i,2) │ ...   adjacent → fast

naive i-j-k order would walk B DOWN a column instead:
 B col j:    B(0,j) ····· B(1,j) ····· B(2,j)      strided → cache misses
```

---

## 6. Ownership and copying: Go vs Rust

```
Go:                                         Rust:

b := a            // copies the POINTER     let b = a;        // MOVE: a is now invalid
a ─┐                                        a ──► (moved)
   ├──► [same Matrix] ──► [same data]       b ──► Matrix ──► data
b ─┘    modifying via b changes a            
                                            let b = a.clone(); // deep copy, new heap buffer
Operations (Add, Mul, ...) allocate         a ──► Matrix ──► data₁
a new Matrix and leave the inputs alone.    b ──► Matrix ──► data₂

                                            Operators take references (&a * &b) so
                                            the inputs are borrowed, not consumed.
```

A few practical consequences:

- In Go, `*Matrix` values are shared by default. Mutating through one pointer is visible through all of them, and nothing stops two goroutines racing on it.
- In Rust, you can't have a `&mut Matrix` while any `&Matrix` exists. This prevents that class of bug at compile time.
- Every op (`Add`, `Mul`, `Transpose`, `Scale`) returns a **new** matrix. The inputs are never mutated.

---

## 7. Summary

```
┌─────────────────────────────────────────────────────────────┐
│ Matrix { rows, cols, data[ rows*cols ] }                    │
├───────────────┬─────────────────────────────────────────────┤
│ access (r,c)  │ data[r*cols + c]                            │
│ add / scale   │ single loop over flat data                  │
│ transpose     │ new buffer, (i,j) → (j,i), dims swapped     │
│ multiply      │ triple loop i-k-j, inner dims must match    │
│ memory        │ one contiguous block → cache-friendly       │
│ errors        │ dims checked before ops (error / Result)    │
└───────────────┴─────────────────────────────────────────────┘
```

The one-flat-buffer design is simple and fast, and it matches how C libraries like BLAS and NumPy's default arrays lay out data. The tradeoff is that rows can't differ in length, and transpose copies instead of reinterpreting the same memory.

If it would help, I can add bounds-checked accessors, an in-place `transpose_in_place` for square matrices, or a version with a `stride` field that makes transpose a free "view".

```go
package main

import (
	"errors"
	"fmt"
	"strings"
)

// Matrix is a dense row-major matrix of float64.
type Matrix struct {
	rows, cols int
	data       []float64
}

// New creates a rows x cols matrix filled with zeros.
func New(rows, cols int) *Matrix {
	return &Matrix{rows: rows, cols: cols, data: make([]float64, rows*cols)}
}

// FromSlice builds a matrix from a 2D slice (all rows must have equal length).
func FromSlice(v [][]float64) (*Matrix, error) {
	if len(v) == 0 || len(v[0]) == 0 {
		return nil, errors.New("empty input")
	}
	m := New(len(v), len(v[0]))
	for i, row := range v {
		if len(row) != m.cols {
			return nil, errors.New("ragged rows")
		}
		copy(m.data[i*m.cols:], row)
	}
	return m, nil
}

// Identity returns an n x n identity matrix.
func Identity(n int) *Matrix {
	m := New(n, n)
	for i := 0; i < n; i++ {
		m.Set(i, i, 1)
	}
	return m
}

func (m *Matrix) At(r, c int) float64     { return m.data[r*m.cols+c] }
func (m *Matrix) Set(r, c int, v float64) { m.data[r*m.cols+c] = v }
func (m *Matrix) Dims() (int, int)        { return m.rows, m.cols }

// Add returns m + o.
func (m *Matrix) Add(o *Matrix) (*Matrix, error) {
	if m.rows != o.rows || m.cols != o.cols {
		return nil, fmt.Errorf("dimension mismatch: %dx%d vs %dx%d", m.rows, m.cols, o.rows, o.cols)
	}
	res := New(m.rows, m.cols)
	for i := range m.data {
		res.data[i] = m.data[i] + o.data[i]
	}
	return res, nil
}

// Mul returns the matrix product m * o.
func (m *Matrix) Mul(o *Matrix) (*Matrix, error) {
	if m.cols != o.rows {
		return nil, fmt.Errorf("dimension mismatch: %dx%d * %dx%d", m.rows, m.cols, o.rows, o.cols)
	}
	res := New(m.rows, o.cols)
	for i := 0; i < m.rows; i++ {
		for k := 0; k < m.cols; k++ {
			a := m.At(i, k)
			for j := 0; j < o.cols; j++ {
				res.data[i*res.cols+j] += a * o.At(k, j)
			}
		}
	}
	return res, nil
}

// Scale returns m multiplied by scalar s.
func (m *Matrix) Scale(s float64) *Matrix {
	res := New(m.rows, m.cols)
	for i, v := range m.data {
		res.data[i] = v * s
	}
	return res
}

// Transpose returns the transpose of m.
func (m *Matrix) Transpose() *Matrix {
	res := New(m.cols, m.rows)
	for i := 0; i < m.rows; i++ {
		for j := 0; j < m.cols; j++ {
			res.Set(j, i, m.At(i, j))
		}
	}
	return res
}

func (m *Matrix) String() string {
	var sb strings.Builder
	for i := 0; i < m.rows; i++ {
		sb.WriteString("[")
		for j := 0; j < m.cols; j++ {
			if j > 0 {
				sb.WriteString(", ")
			}
			fmt.Fprintf(&sb, "%6.2f", m.At(i, j))
		}
		sb.WriteString("]\n")
	}
	return sb.String()
}

func main() {
	a, _ := FromSlice([][]float64{{1, 2, 3}, {4, 5, 6}})
	b, _ := FromSlice([][]float64{{7, 8}, {9, 10}, {11, 12}})

	fmt.Println("A:")
	fmt.Print(a)
	fmt.Println("B:")
	fmt.Print(b)

	p, err := a.Mul(b)
	if err != nil {
		panic(err)
	}
	fmt.Println("A * B:")
	fmt.Print(p)

	fmt.Println("A transposed:")
	fmt.Print(a.Transpose())

	fmt.Println("Identity(3):")
	fmt.Print(Identity(3))

	if _, err := a.Add(b); err != nil {
		fmt.Println("Error:", err)
	}
}
```

```rust

use std::fmt;
use std::ops::{Add, Index, IndexMut, Mul};

/// Dense row-major matrix of f64.
#[derive(Debug, Clone, PartialEq)]
pub struct Matrix {
    rows: usize,
    cols: usize,
    data: Vec<f64>,
}

impl Matrix {
    /// rows x cols matrix of zeros.
    pub fn new(rows: usize, cols: usize) -> Self {
        Matrix { rows, cols, data: vec![0.0; rows * cols] }
    }

    /// Build from a Vec of rows; all rows must have equal length.
    pub fn from_vec(v: Vec<Vec<f64>>) -> Result<Self, String> {
        if v.is_empty() || v[0].is_empty() {
            return Err("empty input".into());
        }
        let cols = v[0].len();
        if v.iter().any(|r| r.len() != cols) {
            return Err("ragged rows".into());
        }
        let rows = v.len();
        Ok(Matrix { rows, cols, data: v.into_iter().flatten().collect() })
    }

    pub fn identity(n: usize) -> Self {
        let mut m = Matrix::new(n, n);
        for i in 0..n {
            m[(i, i)] = 1.0;
        }
        m
    }

    pub fn dims(&self) -> (usize, usize) {
        (self.rows, self.cols)
    }

    pub fn transpose(&self) -> Matrix {
        let mut t = Matrix::new(self.cols, self.rows);
        for i in 0..self.rows {
            for j in 0..self.cols {
                t[(j, i)] = self[(i, j)];
            }
        }
        t
    }

    pub fn scale(&self, s: f64) -> Matrix {
        Matrix {
            rows: self.rows,
            cols: self.cols,
            data: self.data.iter().map(|x| x * s).collect(),
        }
    }

    /// Checked addition.
    pub fn try_add(&self, o: &Matrix) -> Result<Matrix, String> {
        if self.dims() != o.dims() {
            return Err(format!("dimension mismatch: {:?} vs {:?}", self.dims(), o.dims()));
        }
        let data = self.data.iter().zip(&o.data).map(|(a, b)| a + b).collect();
        Ok(Matrix { rows: self.rows, cols: self.cols, data })
    }

    /// Checked multiplication.
    pub fn try_mul(&self, o: &Matrix) -> Result<Matrix, String> {
        if self.cols != o.rows {
            return Err(format!("dimension mismatch: {:?} * {:?}", self.dims(), o.dims()));
        }
        let mut res = Matrix::new(self.rows, o.cols);
        for i in 0..self.rows {
            for k in 0..self.cols {
                let a = self[(i, k)];
                for j in 0..o.cols {
                    res[(i, j)] += a * o[(k, j)];
                }
            }
        }
        Ok(res)
    }
}

impl Index<(usize, usize)> for Matrix {
    type Output = f64;
    fn index(&self, (r, c): (usize, usize)) -> &f64 {
        &self.data[r * self.cols + c]
    }
}

impl IndexMut<(usize, usize)> for Matrix {
    fn index_mut(&mut self, (r, c): (usize, usize)) -> &mut f64 {
        &mut self.data[r * self.cols + c]
    }
}

// Operator versions (panic on dimension mismatch; use try_* to handle errors).
impl Add for &Matrix {
    type Output = Matrix;
    fn add(self, o: &Matrix) -> Matrix {
        self.try_add(o).expect("matrix add")
    }
}

impl Mul for &Matrix {
    type Output = Matrix;
    fn mul(self, o: &Matrix) -> Matrix {
        self.try_mul(o).expect("matrix mul")
    }
}

impl fmt::Display for Matrix {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        for i in 0..self.rows {
            let row: Vec<String> = (0..self.cols).map(|j| format!("{:6.2}", self[(i, j)])).collect();
            writeln!(f, "[{}]", row.join(", "))?;
        }
        Ok(())
    }
}

fn main() {
    let a = Matrix::from_vec(vec![vec![1.0, 2.0, 3.0], vec![4.0, 5.0, 6.0]]).unwrap();
    let b = Matrix::from_vec(vec![vec![7.0, 8.0], vec![9.0, 10.0], vec![11.0, 12.0]]).unwrap();

    println!("A:\n{}", a);
    println!("B:\n{}", b);
    println!("A * B:\n{}", &a * &b);
    println!("A transposed:\n{}", a.transpose());
    println!("Identity(3):\n{}", Matrix::identity(3));

    if let Err(e) = a.try_add(&b) {
        println!("Error: {}", e);
    }
}
```