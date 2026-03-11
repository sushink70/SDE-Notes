Let me first audit your code deeply, then build the complete idiomatic extension.

**What you already got right:**
- Flat `[]float64` — row-major layout, CPU cache-friendly ✅
- `Row()` returning a slice view (zero allocation) ✅
- Pointer receiver consistency ✅

**What needs sharpening:**
- No error handling — Go's core philosophy is *errors are values*
- `Print()` should implement `fmt.Stringer` (the `String() string` interface)
- No bounds validation = silent corruption bugs
- `math` is imported but unused---

## Deep Analysis: Your Code vs Idiomatic Go

### 🔴 Critical Issue: No Error Handling

Your original `New(rows, cols int) *Matrix` — what happens when `rows = -1`? Silent panic somewhere deep in an allocation. Go's first commandment is:

> **Errors are values. Return them. Don't hide them.**

```go
// ❌ Your version — hides failure
func New(rows, cols int) *Matrix { ... }

// ✅ Idiomatic Go
func New(rows, cols int) (*Matrix, error) { ... }
```

The *only* place panic is acceptable is in package-internal code where the programmer (you) controls the inputs — that's the `must()` helper pattern shown in the file.

---

### 🟡 `Print()` vs `String() string`

```go
// ❌ Custom method — nothing else in Go can use it
func (m *Matrix) Print() { fmt.Printf(...) }

// ✅ Implement fmt.Stringer — now fmt.Println, log.Println, %v all work
func (m *Matrix) String() string { ... }
```

This is *interface satisfaction* — Go's composability model. When you implement `String() string`, your type plugs into the entire `fmt` ecosystem for free.

---

### 🔵 The `i-k-j` Loop Order — The Single Most Important Optimization

This deserves its own mental model. Naive matrix multiply:
```
for i: for j: for k:   dst[i][j] += m[i][k] * other[k][j]
```
The inner `other[k][j]` jumps **across rows** on every iteration — cache miss on every step.

The `i-k-j` rewrite holds `other.Row(k)` **warm in cache** for the entire inner loop. This is the same insight behind BLAS's dgemm. On a 1000×1000 matrix this is a **10–50× speedup** — from understanding memory, not algorithms.

---

## Architecture Decisions to Internalize

| Decision | Reason |
|---|---|
| `data []float64` unexported | Callers use `At/Set/Row` — internal layout is an implementation detail |
| `Row()` returns slice view | Hot path — zero alloc. Contract: caller may mutate |
| `Col()` copies | Honest API — columns *cannot* be zero-copy in row-major layout |
| `Scale()` returns `*Matrix` | Enables chaining: `m.Clone().Scale(2).Apply(f)` |
| `Apply(func)` | Functional composition over the flat array — ReLU, sigmoid, abs in one pattern |
| `Equal(other, eps)` | **Never** compare floats with `==`. Always tolerance. |

---

## The Mental Model: *Own Your Memory Contract*

Every function you write should have a clear answer to:
1. **Who allocates?** — `New`, `Clone`, `Mul` allocate. `Row`, `Scale`, `Apply` don't (or mutate in place).
2. **Who owns?** — The matrix owns its `data`. `Row()` *lends* a view.
3. **Is mutation visible?** — Yes for slice views, no for returned copies.

This maps directly to Rust's ownership model — Go just doesn't enforce it at compile time. Discipline must come from you.

---

## Next Steps to Build On This

1. **LU Decomposition** — implement Gaussian elimination with partial pivoting. This is where numerical stability becomes real.
2. **Blocked matrix multiply** — tile the inner loops for L1/L2 cache size. Measure with `go test -bench -benchmem`.
3. **BLAS binding** — use `gonum.org/v1/gonum/blas` and compare your implementation against it. The gap will show you exactly what SIMD and blocking buy.

The pattern you're building — flat allocation, zero-alloc views, interface satisfaction, error values — is the same pattern used in `gonum`, the Go standard for numerical computing. You're thinking in the right direction.

```go
// Package matrix provides a cache-efficient, idiomatic Go matrix library.
//
// Design philosophy:
//   - Errors are values — never panic on bad input, always return errors.
//   - Flat []float64 storage (row-major) — one allocation, CPU cache-friendly.
//   - Zero-allocation hot paths (Row, Col views).
//   - Interfaces for composability (fmt.Stringer).
//   - Caller owns memory — mutation methods are explicit.
package matrix

import (
	"fmt"
	"math"
	"strings"
)

// ── Core Type ────────────────────────────────────────────────────────────────

// Matrix is a dense, row-major matrix backed by a single flat slice.
//
// Memory layout for a 3×3 matrix:
//
//	[a00 a01 a02 | a10 a11 a12 | a20 a21 a22]
//	 ^row 0        ^row 1        ^row 2
//
// This means iterating row-by-row is cache-optimal (sequential reads).
// Column-wise iteration crosses cache-line boundaries — avoid it in hot loops.
type Matrix struct {
	data []float64
	rows int
	cols int
}

// New allocates a zero-valued rows×cols matrix.
// Returns an error if dimensions are non-positive.
func New(rows, cols int) (*Matrix, error) {
	if rows <= 0 || cols <= 0 {
		return nil, fmt.Errorf("matrix.New: invalid dimensions %d×%d", rows, cols)
	}
	return &Matrix{
		data: make([]float64, rows*cols),
		rows: rows,
		cols: cols,
	}, nil
}

// must is a package-internal helper for cases where dimensions are guaranteed
// correct (e.g., constructors like Identity). Never expose this to callers.
func must(rows, cols int) *Matrix {
	m, err := New(rows, cols)
	if err != nil {
		// This is a programming error — panic is acceptable here
		// because the caller (our own code) passed bad constants.
		panic(err)
	}
	return m
}

// Identity returns an n×n identity matrix.
func Identity(n int) (*Matrix, error) {
	if n <= 0 {
		return nil, fmt.Errorf("matrix.Identity: n must be positive, got %d", n)
	}
	m := must(n, n)
	for i := range n { // Go 1.22+ range-over-int
		m.data[i*n+i] = 1.0
	}
	return m, nil
}

// Rows returns the number of rows.
func (m *Matrix) Rows() int { return m.rows }

// Cols returns the number of columns.
func (m *Matrix) Cols() int { return m.cols }

// ── Element Access ────────────────────────────────────────────────────────────

// At returns element (i, j). Panics on out-of-bounds.
//
// Mental model: treat At/Set like array indexing — callers are responsible
// for valid indices, just as with slices. This avoids error-return overhead
// on the hottest path (inner loops). Use InBounds for safe access.
func (m *Matrix) At(i, j int) float64 {
	m.checkBounds(i, j)
	return m.data[i*m.cols+j]
}

// Set assigns v to element (i, j). Panics on out-of-bounds.
func (m *Matrix) Set(i, j int, v float64) {
	m.checkBounds(i, j)
	m.data[i*m.cols+j] = v
}

// InBounds reports whether (i, j) is a valid index.
func (m *Matrix) InBounds(i, j int) bool {
	return i >= 0 && i < m.rows && j >= 0 && j < m.cols
}

func (m *Matrix) checkBounds(i, j int) {
	if !m.InBounds(i, j) {
		panic(fmt.Sprintf("matrix: index (%d,%d) out of bounds for %d×%d matrix",
			i, j, m.rows, m.cols))
	}
}

// ── Slice Views (zero allocation) ────────────────────────────────────────────

// Row returns a slice view of row i — no allocation, direct memory access.
//
// WARNING: Mutating the returned slice mutates the matrix.
// This is intentional — it enables high-performance in-place operations.
//
//	row := m.Row(0)
//	for j := range row { row[j] *= 2 } // scales row 0 in-place, no alloc
func (m *Matrix) Row(i int) []float64 {
	if i < 0 || i >= m.rows {
		panic(fmt.Sprintf("matrix.Row: row %d out of bounds [0, %d)", i, m.rows))
	}
	return m.data[i*m.cols : (i+1)*m.cols]
}

// Col copies column j into dst and returns it.
// If dst is nil or too small, a new slice is allocated.
//
// Why copy instead of view? Columns are non-contiguous in row-major layout.
// There is no zero-cost column view — a copy is the honest contract.
func (m *Matrix) Col(j int, dst []float64) []float64 {
	if j < 0 || j >= m.cols {
		panic(fmt.Sprintf("matrix.Col: col %d out of bounds [0, %d)", j, m.cols))
	}
	if len(dst) < m.rows {
		dst = make([]float64, m.rows)
	}
	for i := range m.rows {
		dst[i] = m.data[i*m.cols+j]
	}
	return dst[:m.rows]
}

// Data returns the raw backing slice. Use for interop with BLAS/LAPACK-style
// routines. Mutating this slice mutates the matrix — you have been warned.
func (m *Matrix) Data() []float64 { return m.data }

// ── Construction Helpers ──────────────────────────────────────────────────────

// Clone returns a deep copy.
func (m *Matrix) Clone() *Matrix {
	dst := must(m.rows, m.cols)
	copy(dst.data, m.data)
	return dst
}

// FromSlice constructs a matrix from a row-major flat slice.
// The slice is copied — the matrix owns its memory.
func FromSlice(rows, cols int, data []float64) (*Matrix, error) {
	if rows <= 0 || cols <= 0 {
		return nil, fmt.Errorf("matrix.FromSlice: invalid dimensions %d×%d", rows, cols)
	}
	if len(data) != rows*cols {
		return nil, fmt.Errorf("matrix.FromSlice: data length %d ≠ %d×%d=%d",
			len(data), rows, cols, rows*cols)
	}
	m := must(rows, cols)
	copy(m.data, data)
	return m, nil
}

// ── Arithmetic ────────────────────────────────────────────────────────────────

// Add computes m + other, returning a new matrix.
// Returns error if shapes differ.
func (m *Matrix) Add(other *Matrix) (*Matrix, error) {
	if err := shapeMustMatch(m, other, "Add"); err != nil {
		return nil, err
	}
	dst := must(m.rows, m.cols)
	for i, v := range m.data {
		dst.data[i] = v + other.data[i]
	}
	return dst, nil
}

// Sub computes m - other, returning a new matrix.
func (m *Matrix) Sub(other *Matrix) (*Matrix, error) {
	if err := shapeMustMatch(m, other, "Sub"); err != nil {
		return nil, err
	}
	dst := must(m.rows, m.cols)
	for i, v := range m.data {
		dst.data[i] = v - other.data[i]
	}
	return dst, nil
}

// Scale multiplies every element by scalar s in-place and returns m.
// Returning m enables method chaining: m.Scale(2).Transpose()
func (m *Matrix) Scale(s float64) *Matrix {
	for i := range m.data {
		m.data[i] *= s
	}
	return m
}

// Mul computes matrix product m × other (standard O(n³) algorithm).
//
// Cache insight: the naive triple loop has poor locality on the inner
// column access of `other`. The loop order i-k-j (below) is the standard
// cache-friendly rewrite — it keeps both m.Row(i) and other.Row(k) warm
// while accumulating into dst.Row(i).
//
// For production use at scale, this is where you'd call BLAS dgemm.
func (m *Matrix) Mul(other *Matrix) (*Matrix, error) {
	if m.cols != other.rows {
		return nil, fmt.Errorf("matrix.Mul: shape mismatch %d×%d · %d×%d",
			m.rows, m.cols, other.rows, other.cols)
	}
	dst := must(m.rows, other.cols)

	// i-k-j loop order: cache-friendly inner loop
	//
	//  for each row i of m:
	//    for each row k of other (= col k of m):
	//      scalar = m[i][k]
	//      for each col j of other:
	//        dst[i][j] += scalar * other[k][j]   ← sequential in both rows
	for i := range m.rows {
		dstRow := dst.Row(i)
		mRow := m.Row(i)
		for k := range m.cols {
			scalar := mRow[k]
			otherRow := other.Row(k)
			for j, v := range otherRow {
				dstRow[j] += scalar * v
			}
		}
	}
	return dst, nil
}

// Transpose returns a new matrix that is the transpose of m.
//
// Note: for large matrices a cache-oblivious blocked transpose (tiling)
// dramatically reduces cache misses. This is the simple O(n²) version.
func (m *Matrix) Transpose() *Matrix {
	dst := must(m.cols, m.rows)
	for i := range m.rows {
		for j := range m.cols {
			dst.data[j*m.rows+i] = m.data[i*m.cols+j]
		}
	}
	return dst
}

// Apply calls f on every element in-place and returns m.
//
// This is Go's answer to array map — first-class functions, no generics
// overhead for float64. Useful for activation functions, clamping, etc.
//
//	m.Apply(math.Abs)           // absolute value
//	m.Apply(func(x float64) float64 { return math.Max(0, x) }) // ReLU
func (m *Matrix) Apply(f func(float64) float64) *Matrix {
	for i, v := range m.data {
		m.data[i] = f(v)
	}
	return m
}

// ── Norms ─────────────────────────────────────────────────────────────────────

// FrobeniusNorm returns ‖m‖_F = sqrt(Σ aᵢⱼ²).
// This is the most natural matrix norm — analogous to Euclidean vector length.
func (m *Matrix) FrobeniusNorm() float64 {
	var sum float64
	for _, v := range m.data {
		sum += v * v
	}
	return math.Sqrt(sum)
}

// MaxAbsElement returns the element with the largest absolute value.
// This is the ‖·‖_max (Chebyshev) norm — useful for numerical stability checks.
func (m *Matrix) MaxAbsElement() float64 {
	var max float64
	for _, v := range m.data {
		if a := math.Abs(v); a > max {
			max = a
		}
	}
	return max
}

// ── Shape Utilities ───────────────────────────────────────────────────────────

// IsSquare reports whether m is an n×n matrix.
func (m *Matrix) IsSquare() bool { return m.rows == m.cols }

// Shape returns (rows, cols) as a convenience.
func (m *Matrix) Shape() (int, int) { return m.rows, m.cols }

// Equal reports whether m and other are element-wise equal within tolerance eps.
// Never use == on floats in numerical code — always compare with a tolerance.
func (m *Matrix) Equal(other *Matrix, eps float64) bool {
	if m.rows != other.rows || m.cols != other.cols {
		return false
	}
	for i, v := range m.data {
		if math.Abs(v-other.data[i]) > eps {
			return false
		}
	}
	return true
}

// ── fmt.Stringer ──────────────────────────────────────────────────────────────

// String implements fmt.Stringer — this means fmt.Println(m) works naturally.
//
// Go philosophy: implement standard interfaces, not custom Print methods.
// Any function accepting fmt.Stringer will now work with Matrix for free.
func (m *Matrix) String() string {
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("Matrix(%d×%d):\n", m.rows, m.cols))
	for i := range m.rows {
		sb.WriteString("  [")
		for j := range m.cols {
			if j > 0 {
				sb.WriteString("  ")
			}
			fmt.Fprintf(&sb, "%8.3f", m.data[i*m.cols+j])
		}
		sb.WriteString(" ]\n")
	}
	return sb.String()
}

// ── Internal Helpers ──────────────────────────────────────────────────────────

func shapeMustMatch(a, b *Matrix, op string) error {
	if a.rows != b.rows || a.cols != b.cols {
		return fmt.Errorf("matrix.%s: shape mismatch %d×%d vs %d×%d",
			op, a.rows, a.cols, b.rows, b.cols)
	}
	return nil
}
```

```go
package matrix

import (
	"math"
	"testing"
)

// Go testing philosophy:
//   - Table-driven tests: declare cases as data, not code duplication.
//   - Test behavior, not implementation.
//   - Sub-tests (t.Run) give you fine-grained failure reporting.
//   - Benchmarks live in the same file — go test -bench=. -benchmem

// ── Construction ──────────────────────────────────────────────────────────────

func TestNew(t *testing.T) {
	cases := []struct {
		name    string
		rows    int
		cols    int
		wantErr bool
	}{
		{"valid 3x3", 3, 3, false},
		{"valid 1x1", 1, 1, false},
		{"zero rows", 0, 3, true},
		{"zero cols", 3, 0, true},
		{"negative rows", -1, 3, true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			m, err := New(tc.rows, tc.cols)
			if (err != nil) != tc.wantErr {
				t.Fatalf("New(%d,%d): wantErr=%v, got err=%v", tc.rows, tc.cols, tc.wantErr, err)
			}
			if err == nil && len(m.data) != tc.rows*tc.cols {
				t.Errorf("data length: want %d, got %d", tc.rows*tc.cols, len(m.data))
			}
		})
	}
}

func TestIdentity(t *testing.T) {
	m, err := Identity(3)
	if err != nil {
		t.Fatal(err)
	}
	for i := range 3 {
		for j := range 3 {
			want := 0.0
			if i == j {
				want = 1.0
			}
			if got := m.At(i, j); got != want {
				t.Errorf("Identity[%d][%d] = %f, want %f", i, j, got, want)
			}
		}
	}
}

// ── Arithmetic ────────────────────────────────────────────────────────────────

func TestAdd(t *testing.T) {
	a, _ := FromSlice(2, 2, []float64{1, 2, 3, 4})
	b, _ := FromSlice(2, 2, []float64{5, 6, 7, 8})
	got, err := a.Add(b)
	if err != nil {
		t.Fatal(err)
	}
	want, _ := FromSlice(2, 2, []float64{6, 8, 10, 12})
	if !got.Equal(want, 1e-9) {
		t.Errorf("Add mismatch:\ngot:\n%v\nwant:\n%v", got, want)
	}
}

func TestMulIdentity(t *testing.T) {
	// A × I = A — fundamental property, good sanity check
	a, _ := FromSlice(3, 3, []float64{
		1, 2, 3,
		4, 5, 6,
		7, 8, 9,
	})
	id, _ := Identity(3)
	got, err := a.Mul(id)
	if err != nil {
		t.Fatal(err)
	}
	if !got.Equal(a, 1e-9) {
		t.Errorf("A × I ≠ A:\ngot:\n%v\nwant:\n%v", got, a)
	}
}

func TestMulShapeMismatch(t *testing.T) {
	a, _ := New(2, 3)
	b, _ := New(4, 2)
	_, err := a.Mul(b)
	if err == nil {
		t.Error("expected error for shape mismatch, got nil")
	}
}

func TestTranspose(t *testing.T) {
	a, _ := FromSlice(2, 3, []float64{
		1, 2, 3,
		4, 5, 6,
	})
	got := a.Transpose()
	want, _ := FromSlice(3, 2, []float64{
		1, 4,
		2, 5,
		3, 6,
	})
	if !got.Equal(want, 1e-9) {
		t.Errorf("Transpose mismatch:\ngot:\n%v\nwant:\n%v", got, want)
	}
}

func TestTransposeInvolution(t *testing.T) {
	// (Aᵀ)ᵀ = A — transpose is its own inverse
	a, _ := FromSlice(3, 4, []float64{
		1, 2, 3, 4,
		5, 6, 7, 8,
		9, 10, 11, 12,
	})
	if !a.Transpose().Transpose().Equal(a, 1e-9) {
		t.Error("(Aᵀ)ᵀ ≠ A")
	}
}

func TestFrobeniusNorm(t *testing.T) {
	// Identity n×n has norm = sqrt(n)
	n := 4
	id, _ := Identity(n)
	got := id.FrobeniusNorm()
	want := math.Sqrt(float64(n))
	if math.Abs(got-want) > 1e-9 {
		t.Errorf("FrobeniusNorm(I₄) = %f, want %f", got, want)
	}
}

func TestApply(t *testing.T) {
	// ReLU: max(0, x)
	a, _ := FromSlice(2, 2, []float64{-1, 2, -3, 4})
	a.Clone().Apply(func(x float64) float64 { return math.Max(0, x) })
	// original should be unchanged
	if a.At(0, 0) != -1 {
		t.Error("Apply mutated original via Clone — logic error")
	}
	// apply to clone
	b := a.Clone()
	b.Apply(func(x float64) float64 { return math.Max(0, x) })
	want, _ := FromSlice(2, 2, []float64{0, 2, 0, 4})
	if !b.Equal(want, 1e-9) {
		t.Errorf("ReLU mismatch:\ngot:\n%v\nwant:\n%v", b, want)
	}
}

// ── Benchmarks ────────────────────────────────────────────────────────────────
// Run with: go test -bench=. -benchmem -count=3

func BenchmarkMul100(b *testing.B) {
	a, _ := New(100, 100)
	id, _ := Identity(100)
	b.ResetTimer()
	for range b.N {
		_, _ = a.Mul(id)
	}
}

func BenchmarkTranspose1000(b *testing.B) {
	m, _ := New(1000, 1000)
	b.ResetTimer()
	for range b.N {
		_ = m.Transpose()
	}
}

func BenchmarkRow(b *testing.B) {
	m, _ := New(1000, 1000)
	b.ResetTimer()
	for range b.N {
		_ = m.Row(500) // zero-allocation hot path
	}
}
```
## What `New` Is For

It's a **constructor function** — Go's idiomatic way of creating a value that needs initialization logic beyond just `{}`.

---

### The Problem It Solves

In Go, you *can* create a struct directly:

```go
m := &Matrix{}  // rows=0, cols=0, data=nil
```

But now `m` is in an **invalid, unusable state**. Any call to `m.At(0,0)` panics immediately. Nothing stopped you from creating garbage.

`New` is the **single controlled entry point** that guarantees:

```
"If New returned a *Matrix, it is valid. Always."
```

---

### Line by Line

```go
func New(rows, cols int) (*Matrix, error) {
```
Returns two values — the matrix **and** the possibility of failure. This is Go's core error contract.

```go
    if rows <= 0 || cols <= 0 {
        return nil, fmt.Errorf("matrix.New: invalid dimensions %d×%d", rows, cols)
    }
```
The **guard clause** — reject nonsense before touching memory. A 0×5 or -3×2 matrix is mathematically meaningless. Catch it at the boundary, not silently deep inside some computation later.

```go
    return &Matrix{
        data: make([]float64, rows*cols),
        rows: rows,
        cols: cols,
    }, nil
```
`make([]float64, rows*cols)` — allocates one **flat contiguous block** of memory. This is the core cache-efficiency decision. `nil` as the second return means *no error occurred*.

---

### The Mental Model

Think of it as a **contract enforcer**:

```
Caller provides → (rows, cols)
New guarantees → valid matrix OR explicit error
Nothing in between
```

This pattern appears everywhere in production Go — `os.Open`, `net.Listen`, `sql.Open`. Every resource that requires initialization follows it. When you see `func NewX(...) (*X, error)`, you are looking at the same pattern. Internalise it — you will write it hundreds of times.

## `*Matrix` and `&Matrix` — Pointers in Go

These are two sides of the same coin. One is a **type**, the other is an **operator**.

---

### `*Matrix` — A Type

It means: *"a pointer to a Matrix"* — an address in memory where a Matrix lives.

```go
var m *Matrix    // m holds a memory address, not the Matrix itself
```

Think of it like a **house address written on paper**. The paper is not the house — it just tells you where the house is.

---

### `&Matrix{...}` — An Operator

`&` means: *"give me the address of this thing"*

```go
&Matrix{
    data: make([]float64, 6),
    rows: 2,
    cols: 3,
}
```

This does two things in one step:
1. Allocates a `Matrix` in memory
2. Returns its **address** (a pointer to it)

---

### Together in `New`

```go
func New(rows, cols int) (*Matrix, error) {   // returns an address
    return &Matrix{                            // here is that address
        data: make([]float64, rows*cols),
        rows: rows,
        cols: cols,
    }, nil
}
```

```
Memory:
┌─────────────────────────────┐
│  Matrix{ data, rows, cols } │  ← actual data lives here, at address 0xc000018090
└─────────────────────────────┘
         ↑
         │
    m *Matrix  →  holds  0xc000018090
```

`m` is not the Matrix. `m` is a piece of paper with the Matrix's address written on it.

---

### Why Return a Pointer Instead of a Value?

```go
// Value — copies the entire struct on every return
func New(...) Matrix { return Matrix{...} }

// Pointer — passes only the address (8 bytes), no copy
func New(...) *Matrix { return &Matrix{...} }
```

For a large matrix (1000×1000 = 8MB of data), returning a value would **copy 8MB** every time. Returning a pointer copies **8 bytes** — just the address.

---

### The Three Symbols to Lock In

| Symbol | Name | Meaning |
|---|---|---|
| `*Matrix` | pointer type | "a variable that holds an address of a Matrix" |
| `&x` | address-of | "give me the address of x" |
| `*p` | dereference | "give me the value at address p" |

```go
m := &Matrix{rows: 2, cols: 2}   // m holds the address

fmt.Println(m)    // prints the address  → &{[] 2 2}
fmt.Println(*m)   // dereferences it     → {[] 2 2}  (the actual Matrix)
```

This is the foundation of all of Go's memory model. Every method receiver, every `New` constructor, every data structure you will build — all of it rests on understanding these three symbols.

## Method on a Type — `func (m *Matrix) Rows() int`

This is a **method** — a function that belongs to a specific type.

---

### Anatomy of the Line

```go
func (m *Matrix) Rows() int { return m.rows }
│    │           │      │
│    │           │      └── return type
│    │           └── method name
│    └── receiver: "this method belongs to *Matrix"
└── keyword
```

The part `(m *Matrix)` is called the **receiver**. It is what makes this a method instead of a plain function.

---

### Receiver — The Core Idea

```go
// Plain function — no owner, you must pass the matrix in
func Rows(m *Matrix) int {
    return m.rows
}

// Method — Matrix owns it, m is implicit
func (m *Matrix) Rows() int {
    return m.rows
}
```

Both do the exact same thing. The difference is **who calls it**:

```go
// Plain function
rows := Rows(m)

// Method
rows := m.Rows()
```

The receiver `m` inside the method body is just the matrix you called it on. When you write `m.Rows()`, Go automatically passes `m` as the receiver.

---

### Why `m.rows` and not just `rows`

`rows` is an **unexported field** inside the struct:

```go
type Matrix struct {
    data []float64
    rows int        // lowercase = private, only this package can touch it
    cols int
}
```

Because `rows` is private, outside code **cannot** do this:

```go
m.rows  // ❌ compile error from outside the package
```

So `Rows()` is a **getter** — a method that safely exposes the private field:

```go
m.Rows()  // ✅ works from anywhere
```

---

### The Full Picture

```
┌─────────────────────────────┐
│  Matrix                     │
│  ├── data []float64  (private) │
│  ├── rows int        (private) │
│  └── cols int        (private) │
│                             │
│  Methods (public interface) │
│  ├── Rows() int             │
│  ├── Cols() int             │
│  ├── At(i,j) float64        │
│  └── ...                    │
└─────────────────────────────┘
```

Private fields, public methods. **You control access.** This is encapsulation — one of the most important design principles in Go.

## Method vs Plain Function in Go

---

### The One-Line Answer

A **function** belongs to a package. A **method** belongs to a **type**.

---

### Side by Side

```go
// Plain function — lives in the package, free-standing
func Add(a, b int) int {
    return a + b
}

// Method — lives on a type, owned by it
func (m *Matrix) Add(other *Matrix) (*Matrix, error) {
    ...
}
```

Calling them:

```go
// Function — you bring the data to it
result := Add(1, 2)

// Method — the data owns the behavior
result, err := m.Add(other)
```

---

### Three Real Differences

**1. Receiver vs Argument**

```go
// Function — matrix is just another argument
func Scale(m *Matrix, factor float64) *Matrix { ... }

// Method — matrix is the owner, factor is the argument
func (m *Matrix) Scale(factor float64) *Matrix { ... }
```

They compile to nearly identical machine code. The difference is **conceptual ownership** — does the matrix *have* a Scale behavior, or is Scale just a utility that *uses* a matrix?

---

**2. Methods Enable Interfaces**

This is the biggest difference. Plain functions cannot satisfy interfaces. Only methods can.

```go
// This interface requires a String() method
type Stringer interface {
    String() string
}

// Matrix satisfies Stringer because it has this method
func (m *Matrix) String() string {
    return fmt.Sprintf("Matrix(%d×%d)", m.rows, m.cols)
}

// Now this works automatically — no extra code
fmt.Println(m)  // Go calls m.String() internally
```

A plain function `func MatrixString(m *Matrix) string` would **never** satisfy that interface. Interfaces are the reason methods exist.

---

**3. Method Chaining**

Methods enable a fluent style because the receiver is always the same type:

```go
// With methods — reads like a sentence
result := m.Clone().Scale(2.0).Apply(math.Abs)

// With functions — reads inside-out, harder to follow
result := Apply(Scale(Clone(m), 2.0), math.Abs)
```

---

### When to Use Which

| Situation | Use |
|---|---|
| Behavior belongs to a type | Method |
| Need to satisfy an interface | Method |
| Utility logic with no clear owner | Function |
| Operating on two equal things | Function |

A good example of the last point — `matrix.Multiply(a, b)` as a function makes more sense than `a.Multiply(b)` because neither matrix is more "the owner" than the other. But `a.Scale(2.0)` clearly belongs to `a`.

---

### The Mental Model

> A **function** is a verb in the package's vocabulary.
> A **method** is a verb in the **type's** vocabulary.

When you write `m.Rows()`, you are saying *"ask the matrix how many rows it has"*. The matrix knows its own shape — that knowledge belongs to it. That is the instinct that separates idiomatic Go from code that merely compiles.

## Resolving the Confusion Around Go's Type System

The confusion is normal. It happens because Go's type system looks simple on the surface but has **four distinct layers** that beginners see all at once without a map.

Here is the map.

---

### Layer 1 — Basic Types (Data)

These just hold values. Nothing special.

```go
int
float64
bool
string
```

You already understand these. They are the atoms.

---

### Layer 2 — Composite Types (Structure)

Ways to **group** basic types together.

```go
// Array — fixed size, same type
[3]int{1, 2, 3}

// Slice — dynamic size, same type
[]float64{1.0, 2.0, 3.0}

// Map — key-value pairs
map[string]int{"age": 30}

// Struct — named fields, mixed types
type Matrix struct {
    data []float64
    rows int
    cols int
}
```

A struct is just a **named container** for related data. Nothing more yet.

---

### Layer 3 — Pointer Types (Indirection)

Instead of holding a value, hold an **address** of a value.

```go
int       → holds a number
*int      → holds an address where a number lives

Matrix    → holds the actual struct (all fields, all data)
*Matrix   → holds an address where a Matrix lives
```

The rule is simple:

```
Put * in front of any type → now it's a pointer to that type
Put & in front of any value → gives you its address
```

```go
x := 42        // x is int
p := &x        // p is *int — holds address of x
fmt.Println(*p) // * dereferences — prints 42
```

---

### Layer 4 — Interfaces (Behavior)

This is where most confusion lives. An interface is **not data**. It is a **contract of behavior**.

```go
type Stringer interface {
    String() string
}
```

This says: *"any type that has a `String() string` method satisfies this interface."*

No declaration needed. No `implements` keyword. If you have the method, you satisfy the interface automatically.

```go
// Matrix has this method
func (m *Matrix) String() string {
    return fmt.Sprintf("Matrix(%d×%d)", m.rows, m.cols)
}

// Therefore *Matrix automatically satisfies fmt.Stringer
// Go figures this out at compile time
fmt.Println(m)  // works — Go calls m.String()
```

---

### The Map — All Four Layers Together

```
┌─────────────────────────────────────────────┐
│              Go Type System                 │
│                                             │
│  Layer 1 — BASIC TYPES                      │
│  int, float64, bool, string                 │
│  "atoms — just hold values"                 │
│                                             │
│  Layer 2 — COMPOSITE TYPES                  │
│  struct, slice, map, array                  │
│  "structure — group data together"          │
│                                             │
│  Layer 3 — POINTER TYPES                    │
│  *int, *Matrix, *anything                   │
│  "indirection — hold an address"            │
│                                             │
│  Layer 4 — INTERFACES                       │
│  interface{ Method() }                      │
│  "contract — describe behavior"             │
└─────────────────────────────────────────────┘
```

---

### The Three Questions to Ask Every Time You See a Type

When you see any type in Go code, ask these in order:

**1. Is there a `*` in front?**
Yes → it's a pointer. The variable holds an address, not the value itself.

**2. Is the word `interface` involved?**
Yes → it describes behavior, not data. It's a contract.

**3. Otherwise — what does it group?**
`struct` groups named fields. `[]T` groups same-type values. `map[K]V` groups key-value pairs.

---

### The Single Root Cause of Confusion

Go lets you **add methods to any named type** — not just structs. This surprises people.

```go
// This is valid Go
type Celsius float64

func (c Celsius) ToFahrenheit() float64 {
    return float64(c)*9/5 + 32
}

temp := Celsius(100)
fmt.Println(temp.ToFahrenheit()) // 212
```

`Celsius` is just `float64` underneath. But it has its own identity, its own methods, its own interface satisfaction. This is the insight:

> **In Go, a type is not just data. A type is data plus behavior.**

---

### A Concrete Mental Model

Think of it like this:

```
Type    = blueprint of what something IS
Methods = blueprint of what something CAN DO
Interface = description of what something MUST DO
Pointer = directions to where something LIVES
```

A `Matrix` **is** rows, cols, and data.
A `Matrix` **can** multiply, transpose, scale.
A `Stringer` **must** have `String() string`.
A `*Matrix` is **directions** to where a Matrix lives in memory.

Once these four roles are distinct in your mind, the confusion dissolves. Every line of Go type-related code falls into one of these four roles — no exceptions.

## What Happens When You Violate an Interface Contract

The answer is simple: **the compiler stops you. Immediately.**

Go's interface satisfaction is checked at **compile time**, not at runtime. You cannot ship broken code.

---

### Example — Violating the Contract

```go
type Stringer interface {
    String() string
}

type Matrix struct {
    rows, cols int
}

// We forgot to implement String() string
// Matrix does NOT satisfy Stringer
```

Now try to use it as a Stringer:

```go
func Print(s Stringer) {
    fmt.Println(s.String())
}

m := &Matrix{rows: 3, cols: 3}
Print(m)  // ❌ compile error
```

The compiler says:

```
cannot use m (type *Matrix) as type Stringer:
*Matrix does not implement Stringer
(missing String method)
```

The program **never runs**. The violation is caught before execution.

---

### Three Ways to Violate + What the Compiler Says

**1. Missing the method entirely**

```go
type Stringer interface {
    String() string
}

type Matrix struct{}

// String() not defined at all
var _ Stringer = &Matrix{}  // ❌
// cannot use &Matrix{} as Stringer: missing String method
```

---

**2. Wrong return type**

```go
// Interface demands string
// You return int — wrong contract
func (m *Matrix) String() int {
    return 42
}

var _ Stringer = &Matrix{}  // ❌
// cannot use &Matrix{} as Stringer:
// String method has wrong return type
```

---

**3. Wrong receiver — value vs pointer**

This one is subtle and catches many people:

```go
// Method defined on value receiver
func (m Matrix) String() string {
    return "matrix"
}

var _ Stringer = &Matrix{}  // ✅ pointer satisfies it
var _ Stringer = Matrix{}   // ✅ value satisfies it

// ─────────────────────────────────────

// Method defined on pointer receiver
func (m *Matrix) String() string {
    return "matrix"
}

var _ Stringer = &Matrix{}  // ✅ pointer satisfies it
var _ Stringer = Matrix{}   // ❌ value does NOT
// Matrix does not implement Stringer
// (String method has pointer receiver)
```

The rule:

```
Value receiver  → both Matrix and *Matrix satisfy the interface
Pointer receiver → only *Matrix satisfies the interface
```

---

### The Compiler Assertion — Your Best Tool

Go has a deliberate pattern for **forcing** the compiler to check interface satisfaction:

```go
// This line does nothing at runtime
// It exists purely to make the compiler verify the contract
var _ Stringer = (*Matrix)(nil)
```

If `*Matrix` does not satisfy `Stringer`, this line **fails at compile time**. Put this near the top of your file, right after your type definition. It is a self-documenting contract:

```go
type Matrix struct { ... }

// Compile-time assertion — fails here if contract is broken
var _ fmt.Stringer = (*Matrix)(nil)
var _ io.Writer    = (*Matrix)(nil)
```

This is how production Go code is written. The Go standard library itself uses this pattern extensively.

---

### Runtime Violation — The One Exception

There is **one** case where interface violation surfaces at runtime — the **nil interface**:

```go
var s Stringer  // s is nil — holds no concrete type

s.String()  // ❌ runtime panic: nil pointer dereference
```

But this is not really a contract violation — it is using a variable before assigning it. The fix is always:

```go
if s != nil {
    s.String()
}
```

---

### The Mental Model

```
Compile-time check → "Does this type have all required methods?"
Runtime check      → "Is this interface variable actually holding something?"

Go protects you from the first completely.
You protect yourself from the second with nil checks.
```

The compiler is your first line of defense. In Go, if the code compiles and your interface assertions are in place — the contract is honored. That guarantee is one of the most powerful things Go gives you.