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

## Step-by-Step: How `m.Set()` Works and Type System Behavior

### 1. Memory Layout — The Foundation

When you call `New(3, 4)`, this is what Go allocates:

```
Data = make([]float64, 3*4)  →  12 contiguous float64 values in memory

Index:  [0]  [1]  [2]  [3]  [4]  [5]  [6]  [7]  [8]  [9]  [10] [11]
         ↑————————— row 0 —————————↑ ↑——— row 1 ———↑ ↑——— row 2 ———↑
```

This is **row-major order** — each row is laid out consecutively. The formula `i*Cols + j` maps a 2D coordinate to this 1D flat index.

**Visualized:**

```
Logical 2D:          Flat 1D index (Cols=4):
 (0,0)(0,1)(0,2)(0,3)    0   1   2   3
 (1,0)(1,1)(1,2)(1,3) →  4   5   6   7
 (2,0)(2,1)(2,2)(2,3)    8   9  10  11
```

---

### 2. Tracing Every `m.Set()` Call

```go
m := New(3, 4)   // Rows=3, Cols=4, Data=[0,0,0,0, 0,0,0,0, 0,0,0,0]
```

| Call | Formula `i*Cols+j` | Flat Index | Valid? | Effect |
|---|---|---|---|---|
| `Set(0, 3, 4)` | `0*4+3 = 3` | `Data[3] = 4.0` | ✅ | row 0, col 3 |
| `Set(0, 2, 4)` | `0*4+2 = 2` | `Data[2] = 4.0` | ✅ | row 0, col 2 |
| `Set(0, 3, 4)` | `0*4+3 = 3` | `Data[3] = 4.0` | ✅ | row 0, col 3 (repeat) |
| `Set(0, 4, 4)` | `0*4+4 = 4` | `Data[4] = 4.0` | ⚠️ **SILENT BUG** | logically row 1, col 0! |
| `Set(0, 5, 4)` | `0*4+5 = 5` | `Data[5] = 4.0` | ⚠️ **SILENT BUG** | logically row 1, col 1! |
| `Set(0, 3, 2)` | `0*4+3 = 3` | `Data[3] = 2.0` | ✅ | overwrites earlier value |

**Final memory state:**
```
Data = [0, 0, 4, 2,  4, 4, 0, 0,  0, 0, 0, 0]
        ←— row 0 —→  ←— row 1 →   ←— row 2 →
```

**Print output:**
```
   0.000    0.000    4.000    2.000 
   4.000    4.000    0.000    0.000 
   0.000    0.000    0.000    0.000 
```

---

### 3. How the Type System Behaves — The Critical Insight

This is where it gets deep. There are **two different kinds of bounds checks** at play:

```
          Go Runtime (slice bounds)       Your Logic (matrix bounds)
               ↓                                   ↓
Set(0, 4, 4) → Data[4] → index 4 < len(12) → ✅ NO PANIC
                                  but col 4 > Cols-1 (3) → ❌ SILENT CORRUPTION
```

**Go's type system does NOT know about your matrix abstraction.** From Go's perspective:

```go
func (m *Matrix) Set(i, j int, v float64) {
    m.Data[i*m.Cols+j] = v   // Go only checks: is (i*Cols+j) < len(Data)?
}                              // It has zero knowledge of what "row" and "col" mean
```

Go's runtime will only panic if the computed flat index goes **outside the slice bounds entirely**. Example — this *would* panic:

```go
m.Set(3, 0, 9)   // 3*4+0 = 12 → Data[12] → index out of range [12] with length 12 → PANIC ✅
m.Set(0, 13, 9)  // 0*4+13 = 13 → Data[13] → PANIC ✅
```

But `Set(0, 4, 4)` silently bleeds into the next logical row — **no panic, no warning, no error**.

---

### 4. The Expert Fix — Bounds Validation at the Abstraction Layer

You must enforce your logical invariants yourself:

```go
func (m *Matrix) Set(i, j int, v float64) {
    if i < 0 || i >= m.Rows || j < 0 || j >= m.Cols {
        panic(fmt.Sprintf("matrix: Set(%d,%d) out of bounds [%d×%d]", i, j, m.Rows, m.Cols))
    }
    m.Data[i*m.Cols+j] = v
}

// Same for At():
func (m *Matrix) At(i, j int) float64 {
    if i < 0 || i >= m.Rows || j < 0 || j >= m.Cols {
        panic(fmt.Sprintf("matrix: At(%d,%d) out of bounds [%d×%d]", i, j, m.Rows, m.Cols))
    }
    return m.Data[i*m.Cols+j]
}
```

With this fix:
```go
m.Set(0, 4, 4)  // → panic: matrix: Set(0,4) out of bounds [3×4]
```

---

### 5. Mental Model: Two Layers of Reality

```
Your abstraction (Matrix):     the "truth" you care about
      ↕  mapping via i*Cols+j
Go's reality ([]float64):      a dumb flat array of bytes
```

Go's type system is **nominal and structural, not semantic**. It enforces *what type a value is*, not *what invariants it satisfies*. A `*Matrix` is just a pointer to a struct — Go doesn't understand that column 4 is invalid for a 4-column matrix. **You are the compiler for your own invariants.**

This is the fundamental lesson: **in systems programming languages (Go, Rust, C), the abstraction boundary is only as safe as you make it.** Rust's type system can enforce more of this (e.g., const generics for compile-time matrix dimensions), but Go requires runtime guards.

---

### Key Takeaway

The bug in your `main()` is a classic **index aliasing / boundary bleed** bug — calling `Set(0, 4, ...)` and `Set(0, 5, ...)` on a 4-column matrix silently corrupts row 1. The flat-index arithmetic never saw a problem; only your logical layer could have caught it. Always validate at the abstraction boundary, not the memory boundary.

## Step-by-Step: How `m.Set()` Works and Type System Behavior

### 1. Memory Layout — The Foundation

When you call `New(3, 4)`, this is what Go allocates:

```
Data = make([]float64, 3*4)  →  12 contiguous float64 values in memory

Index:  [0]  [1]  [2]  [3]  [4]  [5]  [6]  [7]  [8]  [9]  [10] [11]
         ↑————————— row 0 —————————↑ ↑——— row 1 ———↑ ↑——— row 2 ———↑
```

This is **row-major order** — each row is laid out consecutively. The formula `i*Cols + j` maps a 2D coordinate to this 1D flat index.

**Visualized:**

```
Logical 2D:          Flat 1D index (Cols=4):
 (0,0)(0,1)(0,2)(0,3)    0   1   2   3
 (1,0)(1,1)(1,2)(1,3) →  4   5   6   7
 (2,0)(2,1)(2,2)(2,3)    8   9  10  11
```

---

### 2. Tracing Every `m.Set()` Call

```go
m := New(3, 4)   // Rows=3, Cols=4, Data=[0,0,0,0, 0,0,0,0, 0,0,0,0]
```

| Call | Formula `i*Cols+j` | Flat Index | Valid? | Effect |
|---|---|---|---|---|
| `Set(0, 3, 4)` | `0*4+3 = 3` | `Data[3] = 4.0` | ✅ | row 0, col 3 |
| `Set(0, 2, 4)` | `0*4+2 = 2` | `Data[2] = 4.0` | ✅ | row 0, col 2 |
| `Set(0, 3, 4)` | `0*4+3 = 3` | `Data[3] = 4.0` | ✅ | row 0, col 3 (repeat) |
| `Set(0, 4, 4)` | `0*4+4 = 4` | `Data[4] = 4.0` | ⚠️ **SILENT BUG** | logically row 1, col 0! |
| `Set(0, 5, 4)` | `0*4+5 = 5` | `Data[5] = 4.0` | ⚠️ **SILENT BUG** | logically row 1, col 1! |
| `Set(0, 3, 2)` | `0*4+3 = 3` | `Data[3] = 2.0` | ✅ | overwrites earlier value |

**Final memory state:**
```
Data = [0, 0, 4, 2,  4, 4, 0, 0,  0, 0, 0, 0]
        ←— row 0 —→  ←— row 1 →   ←— row 2 →
```

**Print output:**
```
   0.000    0.000    4.000    2.000 
   4.000    4.000    0.000    0.000 
   0.000    0.000    0.000    0.000 
```

---

### 3. How the Type System Behaves — The Critical Insight

This is where it gets deep. There are **two different kinds of bounds checks** at play:

```
          Go Runtime (slice bounds)       Your Logic (matrix bounds)
               ↓                                   ↓
Set(0, 4, 4) → Data[4] → index 4 < len(12) → ✅ NO PANIC
                                  but col 4 > Cols-1 (3) → ❌ SILENT CORRUPTION
```

**Go's type system does NOT know about your matrix abstraction.** From Go's perspective:

```go
func (m *Matrix) Set(i, j int, v float64) {
    m.Data[i*m.Cols+j] = v   // Go only checks: is (i*Cols+j) < len(Data)?
}                              // It has zero knowledge of what "row" and "col" mean
```

Go's runtime will only panic if the computed flat index goes **outside the slice bounds entirely**. Example — this *would* panic:

```go
m.Set(3, 0, 9)   // 3*4+0 = 12 → Data[12] → index out of range [12] with length 12 → PANIC ✅
m.Set(0, 13, 9)  // 0*4+13 = 13 → Data[13] → PANIC ✅
```

But `Set(0, 4, 4)` silently bleeds into the next logical row — **no panic, no warning, no error**.

---

### 4. The Expert Fix — Bounds Validation at the Abstraction Layer

You must enforce your logical invariants yourself:

```go
func (m *Matrix) Set(i, j int, v float64) {
    if i < 0 || i >= m.Rows || j < 0 || j >= m.Cols {
        panic(fmt.Sprintf("matrix: Set(%d,%d) out of bounds [%d×%d]", i, j, m.Rows, m.Cols))
    }
    m.Data[i*m.Cols+j] = v
}

// Same for At():
func (m *Matrix) At(i, j int) float64 {
    if i < 0 || i >= m.Rows || j < 0 || j >= m.Cols {
        panic(fmt.Sprintf("matrix: At(%d,%d) out of bounds [%d×%d]", i, j, m.Rows, m.Cols))
    }
    return m.Data[i*m.Cols+j]
}
```

With this fix:
```go
m.Set(0, 4, 4)  // → panic: matrix: Set(0,4) out of bounds [3×4]
```

---

### 5. Mental Model: Two Layers of Reality

```
Your abstraction (Matrix):     the "truth" you care about
      ↕  mapping via i*Cols+j
Go's reality ([]float64):      a dumb flat array of bytes
```

Go's type system is **nominal and structural, not semantic**. It enforces *what type a value is*, not *what invariants it satisfies*. A `*Matrix` is just a pointer to a struct — Go doesn't understand that column 4 is invalid for a 4-column matrix. **You are the compiler for your own invariants.**

This is the fundamental lesson: **in systems programming languages (Go, Rust, C), the abstraction boundary is only as safe as you make it.** Rust's type system can enforce more of this (e.g., const generics for compile-time matrix dimensions), but Go requires runtime guards.

---

### Key Takeaway

The bug in your `main()` is a classic **index aliasing / boundary bleed** bug — calling `Set(0, 4, ...)` and `Set(0, 5, ...)` on a 4-column matrix silently corrupts row 1. The flat-index arithmetic never saw a problem; only your logical layer could have caught it. Always validate at the abstraction boundary, not the memory boundary.

## Deep Dissection: `func (m *Matrix) Set(i, j int, v float64)`

---

### 1. Anatomy of the Function Signature

```go
func (m *Matrix) Set(i, j int, v float64) {
//   ↑receiver  ↑name ↑params         ↑no return value
```

Break every token down:

```
func          → keyword: declares a function
(m *Matrix)   → RECEIVER: this is what makes it a METHOD, not a free function
Set           → method name
(i, j int     → two ints declared together (Go shorthand: same type, comma-separated)
v float64)    → the value to write
              → no return type → returns nothing (void equivalent)
```

---

### 2. The Receiver `(m *Matrix)` — What Actually Happens

This is the most important part. Go has **no `this` or `self` keyword**. Instead, the receiver is an **explicit first parameter** with a special syntax.

```go
// These two are IDENTICAL in what the compiler produces:
func (m *Matrix) Set(i, j int, v float64) { ... }   // method syntax
func Set(m *Matrix, i, j int, v float64)  { ... }   // free function syntax
```

The compiler **rewrites** your method call:

```go
m.Set(0, 3, 4.0)
// becomes internally:
Set(m, 0, 3, 4.0)   // m is just the first argument
```

**Why pointer receiver `*Matrix` and not value receiver `Matrix`?**

```go
// Value receiver — receives a COPY
func (m Matrix) Set(...) {
    m.Data[...] = v   // writes to the COPY, original unchanged ❌
}

// Pointer receiver — receives the ADDRESS
func (m *Matrix) Set(...) {
    m.Data[...] = v   // writes through the pointer, original mutated ✅
}
```

Memory picture:

```
Value receiver:
  caller's m  ──→  [Matrix struct in memory]
  method's m  ──→  [COPY of Matrix struct]   ← writes here, caller never sees it

Pointer receiver:
  caller's m  ──→  [Matrix struct in memory]
                          ↑
  method's m  ────────────┘                  ← same address, writes ARE visible
```

---

### 3. What `*Matrix` Actually Is in Memory

```go
type Matrix struct {
    Data []float64   // 24 bytes: ptr(8) + len(8) + cap(8)
    Rows int         //  8 bytes
    Cols int         //  8 bytes
}
// Total struct size: 40 bytes (on 64-bit)
```

A `*Matrix` is just an **8-byte pointer** (on 64-bit systems) holding the memory address of this 40-byte struct.

```
Stack (inside Set):          Heap (allocated by New()):
┌─────────────────┐          ┌────────────────────────┐
│ m   = 0xc0001a  │──────→   │ Data.ptr = 0xc0002b    │──→ [actual float64 array]
│ i   = 0         │          │ Data.len = 12          │
│ j   = 3         │          │ Data.cap = 12          │
│ v   = 4.0       │          │ Rows     = 3           │
└─────────────────┘          │ Cols     = 4           │
                             └────────────────────────┘
```

---

### 4. The Expression `i*m.Cols+j` — Step by Step

```go
m.Data[i*m.Cols+j] = v
```

The compiler evaluates this **strictly left to right**, respecting operator precedence:

```
Step 1:  m.Cols          → dereference pointer m, read field Cols → integer 4
Step 2:  i * m.Cols      → 0 * 4 = 0           (multiplication first, higher precedence)
Step 3:  (i*m.Cols) + j  → 0 + 3 = 3           (addition second)
Step 4:  m.Data[3]       → dereference m, get Data slice header, index into its backing array
Step 5:  = v             → write float64 value 4.0 at that memory location
```

**Operator precedence matters critically here:**

```go
i*m.Cols+j    // parsed as (i*m.Cols)+j  ← CORRECT row-major index
i*(m.Cols+j)  // completely different!   ← WRONG, parentheses change meaning entirely
```

---

### 5. How `m.Data[index]` Works Internally

`Data` is a **slice**, not a raw array. A slice in Go is a 3-word struct:

```
Data slice header:
┌─────────────────────────────┐
│ ptr  → *float64  (8 bytes)  │  points to first element of backing array
│ len  → int       (8 bytes)  │  number of elements accessible
│ cap  → int       (8 bytes)  │  total allocated capacity
└─────────────────────────────┘
```

When you write `m.Data[3] = v`, the compiler generates roughly:

```
1. Load m.Data.ptr  → base address of float64 array
2. Load m.Data.len  → for bounds check
3. Check: 3 < len?  → if NO → panic (runtime bounds check)
4. Address = base_ptr + (3 * sizeof(float64))
           = base_ptr + (3 * 8)
           = base_ptr + 24 bytes
5. Write v (float64, 8 bytes) at that address
```

**In pseudo-assembly:**

```
MOV  RAX, [m + 0]        ; load Data.ptr (offset 0 in struct)
MOV  RCX, [m + 8]        ; load Data.len (offset 8 in struct)
CMP  3, RCX              ; bounds check: index < len?
JGE  panic               ; if not, panic
MOVSD [RAX + 24], XMM0   ; write float64 at base + 3*8
```

---

### 6. Type System Behavior — The Full Picture

```go
v float64
```

`float64` is an **IEEE 754 double-precision** value — 8 bytes, always. When you pass `4` (an untyped integer literal) to a `float64` parameter:

```go
m.Set(0, 3, 4)    // you wrote integer literal 4
```

Go's type system performs **implicit untyped constant conversion**:

```
4  →  untyped int constant
         ↓ assignable to float64? YES (untyped constants are flexible)
       4.0 (float64)
```

But this only works for **untyped constants**. This would fail:

```go
x := 4          // x is now typed as int
m.Set(0, 3, x)  // COMPILE ERROR: cannot use x (int) as float64
```

---

### 7. Complete Call Trace: `m.Set(0, 3, 4.0)`

```
1. Caller pushes arguments onto stack:
   m = pointer to Matrix (8 bytes)
   i = 0  (int, 8 bytes)
   j = 3  (int, 8 bytes)
   v = 4.0 (float64, 8 bytes)

2. CPU jumps to Set() function body

3. Inside Set():
   a. Dereference m → reach Matrix struct on heap
   b. Read m.Cols → 4
   c. Compute i*m.Cols+j → 0*4+3 → 3
   d. Access m.Data:
      - Dereference m → reach Matrix struct
      - Read Data.ptr → base address of float64 array
      - Read Data.len → 12 (for bounds check)
   e. Bounds check: 3 < 12 → PASS
   f. Compute target address: Data.ptr + 3*8
   g. Write 4.0 (64-bit float) at that address

4. Function returns (no return value)
5. Stack frame cleaned up
```

---

### Core Mental Model

```
*Matrix  →  pointer  →  struct  →  slice header  →  backing array  →  raw bytes
  8B          8B          40B           24B              n*8B
```

Every `.` dereferences one level. Every `[]` indexes into memory. The type system ensures **what** you're accessing; **you** ensure the logical validity of **where**.

## Why the Panic Happened — Full Trace

### The Matrix You Created

```go
m := New(3, 3)
// Rows=3, Cols=3
// Data = make([]float64, 9)  →  indices 0..8 only
```

```
Valid logical grid:        Valid flat indices:
(0,0)(0,1)(0,2)            0  1  2
(1,0)(1,1)(1,2)    →       3  4  5
(2,0)(2,1)(2,2)            6  7  8
                                    ↑ index 8 is the LAST valid address
```

---

### Tracing Every `Set()` Call

```
m.Set(i, j, v)  →  computes  i*Cols+j  =  i*3+j
```

| Call | Formula `i*3+j` | Flat Index | len=9? | Result |
|---|---|---|---|---|
| `Set(2, 3, 6)` | `2*3+3 = 9` | `Data[9]` | 9 is NOT < 9 | 💥 **PANIC HERE** |
| `Set(5, 2, 10)` | `5*3+2 = 17` | `Data[17]` | — | never reached |
| `Set(7, 3, 21)` | `7*3+3 = 24` | `Data[24]` | — | never reached |
| `Set(8, 4, 4)` | `8*3+4 = 28` | `Data[28]` | — | never reached |
| `Set(9, 5, 4)` | `9*3+5 = 32` | `Data[32]` | — | never reached |
| `Set(2, 3, 2)` | `2*3+3 = 9` | `Data[9]` | — | never reached |

**The first call `Set(2, 3, 6)` kills the program immediately.** All others are equally invalid but never execute.

---

### Why Exactly Index `[9]` With Length `9`

```
Data has 9 elements  →  valid indices: 0, 1, 2, 3, 4, 5, 6, 7, 8
                                                                  ↑
                                                            last valid = 8

Set(2, 3, 6):
  i=2, j=3, Cols=3
  flat = 2 * 3 + 3 = 9
  Data[9] → Go checks: 9 < 9?  → FALSE → panic
```

The panic message tells you **exactly** what happened:

```
panic: runtime error: index out of range [9] with length 9
//                                        ↑              ↑
//                               attempted index    slice length
```

---

### The Root Bug — Column Index Exceeds Matrix Width

```go
m := New(3, 3)    // 3 columns → valid j values: 0, 1, 2 ONLY

m.Set(2, 3, 6)    // j=3 → column 3 doesn't exist in a 3-column matrix
//          ↑
//     this is the 4th column (0-indexed), but you only have 3
```

You are telling the matrix "write to row 2, column 3" — but column 3 does not exist. The flat index arithmetic doesn't know this — it just blindly computes `2*3+3=9` and then Go's runtime catches it at the slice boundary.

---

### What Valid Calls Would Look Like

```go
m := New(3, 3)   // valid i: 0,1,2 — valid j: 0,1,2

m.Set(0, 0, 1.0)  // ✅ flat=0
m.Set(1, 1, 5.0)  // ✅ flat=4
m.Set(2, 2, 9.0)  // ✅ flat=8  ← largest valid index
m.Set(2, 3, 6.0)  // ❌ flat=9  ← ONE past the end → panic
```

---

### The Permanent Fix

Guard both dimensions independently at the abstraction layer:

```go
func (m *Matrix) Set(i, j int, v float64) {
    if i < 0 || i >= m.Rows {
        panic(fmt.Sprintf("row index %d out of range [0, %d)", i, m.Rows))
    }
    if j < 0 || j >= m.Cols {
        panic(fmt.Sprintf("col index %d out of range [0, %d)", j, m.Cols))
    }
    m.Data[i*m.Cols+j] = v
}
```

Now `Set(2, 3, 6)` gives you a **meaningful error**:

```
panic: col index 3 out of range [0, 3)
```

Instead of the cryptic raw slice panic — your abstraction speaks its own language, not the runtime's language.

---

### Core Mental Model

```
Go runtime guards:   "is flat index within slice bounds?"      ← memory layer
Your guard:          "is (i,j) within matrix dimensions?"      ← logic layer

Both are needed. The runtime saved you from a memory corruption.
Your guard tells you WHY it was wrong.
```

For `New(3, 3)` — valid range is `i ∈ {0,1,2}` and `j ∈ {0,1,2}`:

```go
m.Set(2, 3, 6)   // ❌  j=3 doesn't exist → fix: m.Set(2, 2, 6)
m.Set(5, 2, 10)  // ❌  i=5 doesn't exist → fix: m.Set(1, 2, 10)
m.Set(7, 3, 21)  // ❌  i=7, j=3 both gone → fix: m.Set(2, 1, 21)
m.Set(8, 4, 4)   // ❌  i=8, j=4 both gone → fix: m.Set(0, 1, 4)
m.Set(9, 5, 4)   // ❌  i=9, j=5 both gone → fix: m.Set(1, 0, 4)
m.Set(2, 3, 2)   // ❌  j=3 doesn't exist → fix: m.Set(2, 2, 2)
```

The rule is simple:

```
New(rows, cols)
  valid i  →  0  to  rows-1
  valid j  →  0  to  cols-1

New(3, 3):
  valid i  →  0, 1, 2
  valid j  →  0, 1, 2
```

So the entire valid space for `New(3,3)` looks like this:

```
        j=0   j=1   j=2
i=0  →  (0,0) (0,1) (0,2)
i=1  →  (1,0) (1,1) (1,2)
i=2  →  (2,0) (2,1) (2,2)
```

Any coordinate outside this grid → panic. That's the only boundary that exists.

## Why That Valid Range Exists

It comes from one single line:

```go
func New(rows, cols int) *Matrix {
    return &Matrix{
        Data: make([]float64, rows*cols),  // ← this line decides everything
        Rows: rows,
        Cols: cols,
    }
}
```

When you call `New(3, 3)`:

```go
make([]float64, 3*3)
make([]float64, 9)
// creates exactly 9 slots
```

---

### 9 Slots Means Indices 0 Through 8

```
Slots created:   1   2   3   4   5   6   7   8   9
Index:          [0] [1] [2] [3] [4] [5] [6] [7] [8]
                 ↑                                 ↑
              first                              last
```

Go arrays and slices are **zero-based**. You have 9 slots, so valid indices are `0..8`. Index `9` does not exist. This is not a matrix rule — this is how every array in Go (and C, Rust) works.

```
n slots  →  valid indices: 0 to n-1
9 slots  →  valid indices: 0 to 8
```

---

### Now Map That Back to 2D

Your matrix is 3 rows × 3 cols. Those 9 flat slots are divided equally:

```
Row 0 → slots [0, 1, 2]   → j can be 0, 1, 2
Row 1 → slots [3, 4, 5]   → j can be 0, 1, 2
Row 2 → slots [6, 7, 8]   → j can be 0, 1, 2
```

3 rows means rows `0, 1, 2` — not row `3`, because a 3-row matrix has no 4th row.
3 cols means cols `0, 1, 2` — not col `3`, because a 3-col matrix has no 4th column.

```
n rows  →  valid i: 0 to n-1
n cols  →  valid j: 0 to n-1

3 rows  →  valid i: 0, 1, 2
3 cols  →  valid j: 0, 1, 2
```

---

### The Root Reason — Zero-Based Indexing

```
Human counting:   1, 2, 3   (starts at 1, last = n)
Computer memory:  0, 1, 2   (starts at 0, last = n-1)
```

This is why `New(3,3)` gives you rows `0,1,2` and not `1,2,3`. The moment you call `New(3,3)`, you are saying **"allocate 9 slots starting from address 0"** — and slot 0 is row 0, col 0. There is no slot 9, so there is no row 3 or col 3.

**One sentence:** you allocated `n` things, things are counted from `0`, so the last one is always at `n-1`.

That depends on your intent. Let me ask first:Both answers, so you understand both paths:

---

### Option A — Resize the Matrix to Fit the Calls

Find the **largest i and j** used, then set `rows = max_i + 1`, `cols = max_j + 1`:

```
m.Set(2, 3, 6)   → i=2, j=3
m.Set(5, 2, 10)  → i=5, j=2
m.Set(7, 3, 21)  → i=7, j=3
m.Set(8, 4, 4)   → i=8, j=4
m.Set(9, 5, 4)   → i=9, j=5  ← largest i=9, largest j=5
m.Set(2, 3, 2)   → i=2, j=3
```

```go
// max i = 9  →  rows = 9+1 = 10
// max j = 5  →  cols = 5+1 = 6

m := New(10, 6)   // now all calls are valid

m.Set(2, 3, 6)
m.Set(5, 2, 10)
m.Set(7, 3, 21)
m.Set(8, 4, 4)
m.Set(9, 5, 4)
m.Set(2, 3, 2)   // overwrites the first Set(2,3,6)
```

---

### Option B — Fix the Indices to Fit `New(3,3)`

Clamp every `i` into `{0,1,2}` and every `j` into `{0,1,2}`:

```go
m := New(3, 3)

m.Set(2, 2, 6)   // was Set(2,3) → j clamped from 3 to 2
m.Set(2, 2, 10)  // was Set(5,2) → i clamped from 5 to 2
m.Set(2, 2, 21)  // was Set(7,3) → both clamped
m.Set(2, 1, 4)   // was Set(8,4) → both clamped
m.Set(2, 2, 4)   // was Set(9,5) → both clamped
m.Set(2, 2, 2)   // was Set(2,3) → j clamped from 3 to 2
```

---

### The Real Lesson

```
Option A → the data defines the matrix size   (matrix adapts to your data)
Option B → the matrix size defines valid data  (your data adapts to the matrix)
```

Option A is almost always the correct design. You should **know your data first, then allocate**. Writing `New(3,3)` and then calling `Set(9,5,...)` means you didn't think about size before allocating — that is the real bug.

### Rule to Fix Every Call

```
if i >= rows  →  clamp to rows-1  (max valid row = 2)
if j >= cols  →  clamp to cols-1  (max valid col = 2)
```

---

### Fix Each Line

```go
m.Set(2, 3, 6)   // i=2 ✅  j=3 ❌ → j clamped: 3 → 2 → m.Set(2, 2, 6)
m.Set(5, 2, 10)  // i=5 ❌  j=2 ✅ → i clamped: 5 → 2 → m.Set(2, 2, 10)
m.Set(7, 3, 21)  // i=7 ❌  j=3 ❌ → both clamped      → m.Set(2, 2, 21)
m.Set(8, 4, 4)   // i=8 ❌  j=4 ❌ → both clamped      → m.Set(2, 2, 4)
m.Set(9, 5, 4)   // i=9 ❌  j=5 ❌ → both clamped      → m.Set(2, 2, 4)
m.Set(2, 3, 2)   // i=2 ✅  j=3 ❌ → j clamped: 3 → 2 → m.Set(2, 2, 2)
```

---

### Fixed Code

```go
m := New(3, 3)

m.Set(2, 2, 6)
m.Set(2, 2, 10)
m.Set(2, 2, 21)
m.Set(2, 2, 4)
m.Set(2, 2, 4)
m.Set(2, 2, 2)   // ← this is the final value at (2,2) — all others overwritten

m.Print()
```

---

### What the Matrix Looks Like After Print

```
   0.000    0.000    0.000
   0.000    0.000    0.000
   0.000    0.000    2.000   ← only (2,2) was ever written, final value = 2
```

---

### The Deeper Problem Here

After clamping, **every single call lands on `(2,2)`** — each one overwrites the previous. That tells you these indices were never designed for a 3×3 matrix. The real fix is **Option A** — `New(10, 6)` — which is why knowing your data before allocating is the correct mental order:

```
Think about data shape first → then allocate → then write
```

Not the other way around.