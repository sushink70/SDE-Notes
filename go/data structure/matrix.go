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
