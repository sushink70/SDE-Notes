Now let me create one more artifact showing ndarray usage in Rust:Perfect! I've created a comprehensive guide to matrices in Rust and Python with complete implementations. Here's what I've provided:

## Summary of Artifacts Created:

### 1. **Comprehensive Guide** (Markdown)
- Detailed comparison of manual vs library implementations
- Common errors and how to avoid them
- Correct vs incorrect usage patterns
- Performance comparisons
- When to use which approach

### 2. **Complete Python Implementation**
- Manual `Matrix` class with all operations
- `SafeMatrixNumPy` wrapper with proper error handling
- Demonstrations of common errors
- Performance comparison code
- Best practices examples

### 3. **Complete Rust Manual Implementation**
- Full `Matrix` struct with proper Result types
- Trait implementations (Add, Sub, Mul, Display)
- Comprehensive error handling
- Unit tests included
- Ownership and borrowing patterns

### 4. **Rust ndarray Implementation**
- `SafeMatrix` wrapper around ndarray
- Safe operations with dimension checking
- Comparison with direct ndarray usage
- Production-ready error handling
- Complete test suite

## Key Takeaways:

**Benefits of Manual Implementation:**
- Complete control and understanding
- No dependencies
- Educational value
- Custom optimizations possible

**Benefits of Using Libraries:**
- 10-100x faster performance (optimized backends)
- Battle-tested implementations
- Rich ecosystems
- Less code to maintain

**Control Tradeoffs:**
- Manual = More code, more control, slower
- Library = Less code, less control, faster

**Rust Advantages:**
- Memory safety without garbage collection
- Zero-cost abstractions
- Compile-time error catching
- No runtime overhead

**Python Advantages:**
- Rapid development
- Massive ecosystem (NumPy, SciPy)
- Easy prototyping

All implementations include proper error handling, dimension checking, and demonstrate both correct and incorrect usage patterns!

# Comprehensive Matrix Guide: Rust & Python

## Table of Contents
1. [Introduction](#introduction)
2. [Python Implementation](#python-implementation)
3. [Rust Implementation](#rust-implementation)
4. [Comparison & Best Practices](#comparison)

---

## Introduction

This guide covers matrix operations in Rust and Python, comparing manual implementations versus using specialized libraries. We'll explore benefits, drawbacks, common errors, and control tradeoffs.

---

## Python Implementation

### 1. Manual Implementation (Without Libraries)

#### Basic Matrix Class

```python
class Matrix:
    def __init__(self, data):
        """Initialize matrix from 2D list"""
        if not data or not data[0]:
            raise ValueError("Matrix cannot be empty")
        
        # Validate rectangular shape
        cols = len(data[0])
        for row in data:
            if len(row) != cols:
                raise ValueError("All rows must have same length")
        
        self.data = [row[:] for row in data]  # Deep copy
        self.rows = len(data)
        self.cols = len(data[0])
    
    def __repr__(self):
        return f"Matrix({self.rows}x{self.cols})"
    
    def __str__(self):
        return '\n'.join([' '.join(map(str, row)) for row in self.data])
    
    def __getitem__(self, key):
        """Access elements: matrix[i, j]"""
        if isinstance(key, tuple):
            i, j = key
            return self.data[i][j]
        return self.data[key]
    
    def __setitem__(self, key, value):
        """Set elements: matrix[i, j] = value"""
        if isinstance(key, tuple):
            i, j = key
            self.data[i][j] = value
        else:
            self.data[key] = value
    
    def __add__(self, other):
        """Matrix addition"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(f"Dimension mismatch: {self.rows}x{self.cols} + {other.rows}x{other.cols}")
        
        result = [[self.data[i][j] + other.data[i][j] 
                   for j in range(self.cols)] 
                  for i in range(self.rows)]
        return Matrix(result)
    
    def __sub__(self, other):
        """Matrix subtraction"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(f"Dimension mismatch: {self.rows}x{self.cols} - {other.rows}x{other.cols}")
        
        result = [[self.data[i][j] - other.data[i][j] 
                   for j in range(self.cols)] 
                  for i in range(self.rows)]
        return Matrix(result)
    
    def __mul__(self, other):
        """Matrix multiplication or scalar multiplication"""
        if isinstance(other, (int, float)):
            # Scalar multiplication
            result = [[self.data[i][j] * other 
                       for j in range(self.cols)] 
                      for i in range(self.rows)]
            return Matrix(result)
        
        # Matrix multiplication
        if self.cols != other.rows:
            raise ValueError(f"Cannot multiply: {self.rows}x{self.cols} @ {other.rows}x{other.cols}")
        
        result = [[sum(self.data[i][k] * other.data[k][j] 
                      for k in range(self.cols))
                   for j in range(other.cols)]
                  for i in range(self.rows)]
        return Matrix(result)
    
    def transpose(self):
        """Return transposed matrix"""
        result = [[self.data[i][j] for i in range(self.rows)] 
                  for j in range(self.cols)]
        return Matrix(result)
    
    def determinant(self):
        """Calculate determinant (only for square matrices)"""
        if self.rows != self.cols:
            raise ValueError("Determinant only defined for square matrices")
        
        if self.rows == 1:
            return self.data[0][0]
        
        if self.rows == 2:
            return self.data[0][0] * self.data[1][1] - self.data[0][1] * self.data[1][0]
        
        # Recursive cofactor expansion
        det = 0
        for j in range(self.cols):
            minor = self._get_minor(0, j)
            cofactor = ((-1) ** j) * self.data[0][j] * minor.determinant()
            det += cofactor
        return det
    
    def _get_minor(self, row, col):
        """Get minor matrix by removing specified row and column"""
        minor_data = []
        for i in range(self.rows):
            if i == row:
                continue
            minor_row = []
            for j in range(self.cols):
                if j == col:
                    continue
                minor_row.append(self.data[i][j])
            minor_data.append(minor_row)
        return Matrix(minor_data)
```

#### Common Errors Without Libraries

```python
# ERROR 1: Dimension Mismatch
try:
    m1 = Matrix([[1, 2], [3, 4]])
    m2 = Matrix([[1, 2, 3]])
    result = m1 + m2  # ValueError: Dimension mismatch
except ValueError as e:
    print(f"Error: {e}")

# ERROR 2: Invalid Matrix Multiplication
try:
    m1 = Matrix([[1, 2]])  # 1x2
    m2 = Matrix([[1, 2]])  # 1x2
    result = m1 * m2  # ValueError: Cannot multiply 1x2 @ 1x2
except ValueError as e:
    print(f"Error: {e}")

# ERROR 3: Non-rectangular Matrix
try:
    m = Matrix([[1, 2], [3]])  # ValueError: All rows must have same length
except ValueError as e:
    print(f"Error: {e}")

# ERROR 4: Numerical Instability
m = Matrix([[0.1, 0.2], [0.3, 0.4]])
for _ in range(1000):
    m = m * m  # Can lead to overflow or precision loss
```

### 2. Using NumPy (Standard Library Approach)

```python
import numpy as np

# Creating matrices
m1 = np.array([[1, 2], [3, 4]])
m2 = np.array([[5, 6], [7, 8]])

# Operations
addition = m1 + m2
subtraction = m1 - m2
multiplication = m1 @ m2  # Matrix multiplication
element_wise = m1 * m2    # Element-wise multiplication
scalar_mult = m1 * 2

# Transpose
transpose = m1.T

# Determinant
det = np.linalg.det(m1)

# Inverse
inv = np.linalg.inv(m1)

# Eigenvalues and eigenvectors
eigenvalues, eigenvectors = np.linalg.eig(m1)

# Solve linear system Ax = b
A = np.array([[3, 1], [1, 2]])
b = np.array([9, 8])
x = np.linalg.solve(A, b)
```

#### Warnings When Using NumPy

```python
# WARNING 1: Shape Broadcasting (Can be unexpected)
m1 = np.array([[1, 2], [3, 4]])
v = np.array([10, 20])
result = m1 + v  # Broadcasting adds v to each row
print(result)
# [[11 22]
#  [13 24]]

# WARNING 2: Matrix vs Element-wise multiplication
m1 = np.array([[1, 2], [3, 4]])
m2 = np.array([[5, 6], [7, 8]])
wrong = m1 * m2      # Element-wise (often not what you want)
correct = m1 @ m2    # Matrix multiplication

# WARNING 3: Integer overflow
m = np.array([[1000, 1000], [1000, 1000]], dtype=np.int8)
result = m @ m  # Overflow with small integer types

# WARNING 4: Singular matrices
try:
    m = np.array([[1, 2], [2, 4]])  # Singular matrix
    inv = np.linalg.inv(m)  # LinAlgError
except np.linalg.LinAlgError as e:
    print(f"Cannot invert: {e}")
```

### 3. Correct vs Incorrect Usage

#### Incorrect Usage Examples

```python
# INCORRECT: Not checking dimensions
def bad_multiply(A, B):
    return A @ B  # May crash if dimensions incompatible

# INCORRECT: Modifying original array
def bad_transpose(matrix):
    matrix = matrix.T  # Doesn't modify original
    return matrix

original = np.array([[1, 2], [3, 4]])
bad_transpose(original)
print(original)  # Still [[1, 2], [3, 4]]

# INCORRECT: Using wrong multiplication operator
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
wrong = A * B  # Element-wise, not matrix multiplication

# INCORRECT: Not handling numerical errors
def bad_inverse(A):
    return np.linalg.inv(A)  # Doesn't check if singular
```

#### Correct Usage Examples

```python
# CORRECT: Dimension checking
def safe_multiply(A, B):
    if A.shape[1] != B.shape[0]:
        raise ValueError(f"Cannot multiply {A.shape} @ {B.shape}")
    return A @ B

# CORRECT: Explicit copy when needed
def safe_transpose(matrix):
    return matrix.T.copy()

# CORRECT: Using @ for matrix multiplication
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
correct = A @ B

# CORRECT: Error handling
def safe_inverse(A):
    try:
        det = np.linalg.det(A)
        if abs(det) < 1e-10:
            raise ValueError("Matrix is singular or near-singular")
        return np.linalg.inv(A)
    except np.linalg.LinAlgError:
        raise ValueError("Matrix inversion failed")
```

---

## Rust Implementation

### 1. Manual Implementation (Without Libraries)

```rust
use std::fmt;
use std::ops::{Add, Sub, Mul, Index, IndexMut};

#[derive(Debug, Clone, PartialEq)]
pub struct Matrix {
    data: Vec<Vec<f64>>,
    rows: usize,
    cols: usize,
}

impl Matrix {
    pub fn new(data: Vec<Vec<f64>>) -> Result<Self, String> {
        if data.is_empty() || data[0].is_empty() {
            return Err("Matrix cannot be empty".to_string());
        }

        let cols = data[0].len();
        for row in &data {
            if row.len() != cols {
                return Err("All rows must have same length".to_string());
            }
        }

        let rows = data.len();
        Ok(Matrix { data, rows, cols })
    }

    pub fn zeros(rows: usize, cols: usize) -> Self {
        Matrix {
            data: vec![vec![0.0; cols]; rows],
            rows,
            cols,
        }
    }

    pub fn identity(size: usize) -> Self {
        let mut data = vec![vec![0.0; size]; size];
        for i in 0..size {
            data[i][i] = 1.0;
        }
        Matrix {
            data,
            rows: size,
            cols: size,
        }
    }

    pub fn get(&self, row: usize, col: usize) -> Option<f64> {
        if row < self.rows && col < self.cols {
            Some(self.data[row][col])
        } else {
            None
        }
    }

    pub fn set(&mut self, row: usize, col: usize, value: f64) -> Result<(), String> {
        if row < self.rows && col < self.cols {
            self.data[row][col] = value;
            Ok(())
        } else {
            Err("Index out of bounds".to_string())
        }
    }

    pub fn transpose(&self) -> Self {
        let mut result = Matrix::zeros(self.cols, self.rows);
        for i in 0..self.rows {
            for j in 0..self.cols {
                result.data[j][i] = self.data[i][j];
            }
        }
        result
    }

    pub fn determinant(&self) -> Result<f64, String> {
        if self.rows != self.cols {
            return Err("Determinant only defined for square matrices".to_string());
        }

        if self.rows == 1 {
            return Ok(self.data[0][0]);
        }

        if self.rows == 2 {
            return Ok(self.data[0][0] * self.data[1][1] - 
                     self.data[0][1] * self.data[1][0]);
        }

        let mut det = 0.0;
        for j in 0..self.cols {
            let minor = self.get_minor(0, j)?;
            let cofactor = if j % 2 == 0 { 1.0 } else { -1.0 };
            det += cofactor * self.data[0][j] * minor.determinant()?;
        }
        Ok(det)
    }

    fn get_minor(&self, row: usize, col: usize) -> Result<Self, String> {
        let mut minor_data = Vec::new();
        for i in 0..self.rows {
            if i == row {
                continue;
            }
            let mut minor_row = Vec::new();
            for j in 0..self.cols {
                if j == col {
                    continue;
                }
                minor_row.push(self.data[i][j]);
            }
            minor_data.push(minor_row);
        }
        Matrix::new(minor_data)
    }
}

// Implement Add trait
impl Add for Matrix {
    type Output = Result<Matrix, String>;

    fn add(self, other: Matrix) -> Self::Output {
        if self.rows != other.rows || self.cols != other.cols {
            return Err(format!(
                "Dimension mismatch: {}x{} + {}x{}",
                self.rows, self.cols, other.rows, other.cols
            ));
        }

        let mut result = Matrix::zeros(self.rows, self.cols);
        for i in 0..self.rows {
            for j in 0..self.cols {
                result.data[i][j] = self.data[i][j] + other.data[i][j];
            }
        }
        Ok(result)
    }
}

// Implement Sub trait
impl Sub for Matrix {
    type Output = Result<Matrix, String>;

    fn sub(self, other: Matrix) -> Self::Output {
        if self.rows != other.rows || self.cols != other.cols {
            return Err(format!(
                "Dimension mismatch: {}x{} - {}x{}",
                self.rows, self.cols, other.rows, other.cols
            ));
        }

        let mut result = Matrix::zeros(self.rows, self.cols);
        for i in 0..self.rows {
            for j in 0..self.cols {
                result.data[i][j] = self.data[i][j] - other.data[i][j];
            }
        }
        Ok(result)
    }
}

// Implement Mul trait for matrix multiplication
impl Mul for Matrix {
    type Output = Result<Matrix, String>;

    fn mul(self, other: Matrix) -> Self::Output {
        if self.cols != other.rows {
            return Err(format!(
                "Cannot multiply: {}x{} @ {}x{}",
                self.rows, self.cols, other.rows, other.cols
            ));
        }

        let mut result = Matrix::zeros(self.rows, other.cols);
        for i in 0..self.rows {
            for j in 0..other.cols {
                let mut sum = 0.0;
                for k in 0..self.cols {
                    sum += self.data[i][k] * other.data[k][j];
                }
                result.data[i][j] = sum;
            }
        }
        Ok(result)
    }
}

// Implement Display trait
impl fmt::Display for Matrix {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        for row in &self.data {
            writeln!(f, "{:?}", row)?;
        }
        Ok(())
    }
}
```

#### Common Errors Without Libraries in Rust

```rust
// ERROR 1: Dimension mismatch (Compile-time safe, Runtime error)
fn error_example_1() {
    let m1 = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
    let m2 = Matrix::new(vec![vec![1.0, 2.0, 3.0]]).unwrap();
    
    match m1 + m2 {
        Ok(_) => println!("Success"),
        Err(e) => println!("Error: {}", e), // Dimension mismatch
    }
}

// ERROR 2: Index out of bounds
fn error_example_2() {
    let mut m = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
    
    match m.set(5, 5, 10.0) {
        Ok(_) => println!("Set value"),
        Err(e) => println!("Error: {}", e), // Index out of bounds
    }
}

// ERROR 3: Non-rectangular matrix
fn error_example_3() {
    let m = Matrix::new(vec![vec![1.0, 2.0], vec![3.0]]);
    
    match m {
        Ok(_) => println!("Created matrix"),
        Err(e) => println!("Error: {}", e), // All rows must have same length
    }
}

// ERROR 4: Ownership issues (Rust-specific)
fn error_example_4() {
    let m1 = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
    let m2 = m1.clone(); // Need to clone for reuse
    
    let result1 = m1 + m2; // m1 and m2 moved here
    // let result2 = m1 + m2; // ERROR: value used after move
}
```

### 2. Using ndarray Crate (Standard Library Approach)

Add to `Cargo.toml`:
```toml
[dependencies]
ndarray = "0.15"
ndarray-linalg = "0.16"
```

```rust
use ndarray::{Array2, arr2};
use ndarray_linalg::Solve;

fn ndarray_examples() {
    // Creating matrices
    let m1 = arr2(&[[1.0, 2.0], [3.0, 4.0]]);
    let m2 = arr2(&[[5.0, 6.0], [7.0, 8.0]]);

    // Operations
    let addition = &m1 + &m2;
    let subtraction = &m1 - &m2;
    let multiplication = m1.dot(&m2);  // Matrix multiplication
    let element_wise = &m1 * &m2;      // Element-wise multiplication
    let scalar_mult = &m1 * 2.0;

    // Transpose
    let transpose = m1.t();

    // Identity and zeros
    let identity = Array2::<f64>::eye(3);
    let zeros = Array2::<f64>::zeros((3, 3));

    println!("Addition:\n{}", addition);
    println!("Multiplication:\n{}", multiplication);
}
```

#### Warnings When Using ndarray

```rust
// WARNING 1: Borrowing vs Ownership
fn warning_1() {
    let m1 = arr2(&[[1.0, 2.0], [3.0, 4.0]]);
    let m2 = arr2(&[[5.0, 6.0], [7.0, 8.0]]);
    
    // WRONG: Moves values
    // let result = m1 + m2; // m1 and m2 moved
    
    // CORRECT: Use references
    let result = &m1 + &m2; // Borrows values
    println!("{}", result);
    println!("{}", m1); // Still accessible
}

// WARNING 2: Dimension mismatch (Runtime panic)
fn warning_2() {
    let m1 = arr2(&[[1.0, 2.0], [3.0, 4.0]]);
    let m2 = arr2(&[[1.0], [2.0], [3.0]]);
    
    // This will panic at runtime
    // let result = m1.dot(&m2);
}

// WARNING 3: Element-wise vs Matrix multiplication
fn warning_3() {
    let m1 = arr2(&[[1.0, 2.0], [3.0, 4.0]]);
    let m2 = arr2(&[[5.0, 6.0], [7.0, 8.0]]);
    
    let wrong = &m1 * &m2;      // Element-wise
    let correct = m1.dot(&m2);  // Matrix multiplication
}
```

### 3. Correct vs Incorrect Usage

#### Incorrect Usage Examples

```rust
// INCORRECT: Not handling Result types
fn bad_multiply(a: Matrix, b: Matrix) -> Matrix {
    (a * b).unwrap() // Panics on error!
}

// INCORRECT: Moving values unnecessarily
fn bad_add(a: Matrix, b: Matrix) -> Matrix {
    (a + b).unwrap() // a and b are moved, can't be reused
}

// INCORRECT: Not checking dimensions
fn bad_transpose(mut m: Matrix) {
    m = m.transpose(); // Doesn't return the transposed matrix
}

// INCORRECT: Index access without bounds checking
fn bad_get(m: &Matrix, i: usize, j: usize) -> f64 {
    m.data[i][j] // Panics if out of bounds
}
```

#### Correct Usage Examples

```rust
// CORRECT: Proper error handling
fn safe_multiply(a: &Matrix, b: &Matrix) -> Result<Matrix, String> {
    if a.cols != b.rows {
        return Err(format!("Cannot multiply {}x{} @ {}x{}", 
                          a.rows, a.cols, b.rows, b.cols));
    }
    a.clone() * b.clone()
}

// CORRECT: Using references to avoid moves
fn safe_add(a: &Matrix, b: &Matrix) -> Result<Matrix, String> {
    a.clone() + b.clone()
}

// CORRECT: Returning new value
fn safe_transpose(m: &Matrix) -> Matrix {
    m.transpose()
}

// CORRECT: Safe index access
fn safe_get(m: &Matrix, i: usize, j: usize) -> Option<f64> {
    m.get(i, j)
}

// CORRECT: Pattern matching for Results
fn use_safe_multiply() {
    let m1 = Matrix::identity(3);
    let m2 = Matrix::identity(3);
    
    match safe_multiply(&m1, &m2) {
        Ok(result) => println!("Result: {}", result),
        Err(e) => eprintln!("Error: {}", e),
    }
}
```

---

## Comparison & Best Practices

### Benefits of Manual Implementation

**Python:**
- Full control over algorithm implementation
- Educational value - understand operations deeply
- No external dependencies
- Can optimize for specific use cases
- Custom error messages and behavior

**Rust:**
- Same benefits as Python, plus:
- Memory safety guarantees
- Zero-cost abstractions
- No garbage collection overhead
- Compile-time error checking

### Benefits of Using Libraries

**NumPy (Python):**
- Highly optimized C/Fortran backend
- 10-100x faster for large matrices
- Extensive ecosystem (SciPy, scikit-learn)
- Battle-tested implementations
- GPU acceleration available (CuPy)
- Broadcasting for concise code

**ndarray (Rust):**
- Similar performance to NumPy
- Memory safety with zero overhead
- BLAS/LAPACK integration
- Parallel operations
- Compile-time optimizations
- Interoperability with other Rust crates

### Control Tradeoffs

| Aspect | Manual | Library |
|--------|--------|---------|
| **Performance** | Slower (10-100x) | Optimized |
| **Code Length** | Longer | Concise |
| **Flexibility** | Complete | Limited to API |
| **Maintenance** | High | Low |
| **Debugging** | Easier (your code) | Harder (black box) |
| **Learning Curve** | Lower | Higher |
| **Safety** | Manual checks | Built-in |

### When to Use Manual Implementation

1. **Educational purposes** - Learning algorithms
2. **Specific constraints** - Unusual requirements
3. **Minimal dependencies** - Embedded systems
4. **Custom operations** - Not in standard libraries
5. **Small matrices** - Performance not critical

### When to Use Libraries

1. **Production code** - Reliability matters
2. **Large matrices** - Performance critical
3. **Standard operations** - Well-supported
4. **Rapid development** - Time constraints
5. **Scientific computing** - Complex algorithms

### Best Practices Summary

**Python:**
```python
# ✓ Use NumPy for production
import numpy as np

# ✓ Check dimensions before operations
if A.shape[1] != B.shape[0]:
    raise ValueError("Incompatible dimensions")

# ✓ Use @ for matrix multiplication
C = A @ B

# ✓ Handle numerical errors
if abs(np.linalg.det(A)) < 1e-10:
    raise ValueError("Matrix is singular")

# ✓ Prefer vectorization over loops
result = np.sum(A * B, axis=1)  # Fast
# NOT: [sum(A[i] * B[i]) for i in range(len(A))]  # Slow
```

**Rust:**
```rust
// ✓ Use Result for error handling
fn matrix_op() -> Result<Matrix, String> { ... }

// ✓ Use references to avoid moves
fn add(a: &Matrix, b: &Matrix) -> Result<Matrix, String>

// ✓ Implement appropriate traits
impl Add for Matrix { ... }

// ✓ Use ndarray for heavy computation
use ndarray::Array2;

// ✓ Handle errors with match or ?
match matrix.determinant() {
    Ok(det) => println!("Det: {}", det),
    Err(e) => eprintln!("Error: {}", e),
}
```

---

## Performance Comparison

### Matrix Multiplication (1000x1000)

| Implementation | Time | Memory |
|----------------|------|--------|
| Python manual | ~30s | High |
| NumPy | ~0.2s | Low |
| Rust manual | ~15s | Low |
| ndarray | ~0.2s | Low |

### Conclusion

- **Use libraries** for production and performance
- **Manual implementation** for learning and special cases
- **Rust** offers safety without performance cost
- **Python** offers rapid development with NumPy
- **Choose based on**: requirements, constraints, and goals

"""
Complete Matrix Implementation in Python
Demonstrates both manual and NumPy approaches with error handling
"""

import numpy as np
from typing import List, Union

# ============================================================================
# MANUAL IMPLEMENTATION
# ============================================================================

class Matrix:
    """Manual matrix implementation without external libraries"""
    
    def __init__(self, data: List[List[float]]):
        """Initialize matrix from 2D list"""
        if not data or not data[0]:
            raise ValueError("Matrix cannot be empty")
        
        # Validate rectangular shape
        cols = len(data[0])
        for row in data:
            if len(row) != cols:
                raise ValueError("All rows must have same length")
        
        self.data = [row[:] for row in data]  # Deep copy
        self.rows = len(data)
        self.cols = len(data[0])
    
    def __repr__(self):
        return f"Matrix({self.rows}x{self.cols})"
    
    def __str__(self):
        max_width = max(len(str(val)) for row in self.data for val in row)
        lines = []
        for row in self.data:
            line = " ".join(f"{val:>{max_width}}" for val in row)
            lines.append(f"[{line}]")
        return "\n".join(lines)
    
    def __getitem__(self, key):
        """Access elements: matrix[i, j]"""
        if isinstance(key, tuple):
            i, j = key
            return self.data[i][j]
        return self.data[key]
    
    def __setitem__(self, key, value):
        """Set elements: matrix[i, j] = value"""
        if isinstance(key, tuple):
            i, j = key
            self.data[i][j] = value
        else:
            self.data[key] = value
    
    def __add__(self, other):
        """Matrix addition"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(
                f"Dimension mismatch: {self.rows}x{self.cols} + "
                f"{other.rows}x{other.cols}"
            )
        
        result = [[self.data[i][j] + other.data[i][j] 
                   for j in range(self.cols)] 
                  for i in range(self.rows)]
        return Matrix(result)
    
    def __sub__(self, other):
        """Matrix subtraction"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(
                f"Dimension mismatch: {self.rows}x{self.cols} - "
                f"{other.rows}x{other.cols}"
            )
        
        result = [[self.data[i][j] - other.data[i][j] 
                   for j in range(self.cols)] 
                  for i in range(self.rows)]
        return Matrix(result)
    
    def __mul__(self, other):
        """Matrix multiplication or scalar multiplication"""
        if isinstance(other, (int, float)):
            # Scalar multiplication
            result = [[self.data[i][j] * other 
                       for j in range(self.cols)] 
                      for i in range(self.rows)]
            return Matrix(result)
        
        # Matrix multiplication
        if self.cols != other.rows:
            raise ValueError(
                f"Cannot multiply: {self.rows}x{self.cols} @ "
                f"{other.rows}x{other.cols}"
            )
        
        result = [[sum(self.data[i][k] * other.data[k][j] 
                      for k in range(self.cols))
                   for j in range(other.cols)]
                  for i in range(self.rows)]
        return Matrix(result)
    
    def __eq__(self, other):
        """Check equality"""
        if self.rows != other.rows or self.cols != other.cols:
            return False
        for i in range(self.rows):
            for j in range(self.cols):
                if abs(self.data[i][j] - other.data[i][j]) > 1e-9:
                    return False
        return True
    
    def transpose(self):
        """Return transposed matrix"""
        result = [[self.data[i][j] for i in range(self.rows)] 
                  for j in range(self.cols)]
        return Matrix(result)
    
    def determinant(self):
        """Calculate determinant (only for square matrices)"""
        if self.rows != self.cols:
            raise ValueError("Determinant only defined for square matrices")
        
        if self.rows == 1:
            return self.data[0][0]
        
        if self.rows == 2:
            return (self.data[0][0] * self.data[1][1] - 
                   self.data[0][1] * self.data[1][0])
        
        # Recursive cofactor expansion
        det = 0
        for j in range(self.cols):
            minor = self._get_minor(0, j)
            cofactor = ((-1) ** j) * self.data[0][j] * minor.determinant()
            det += cofactor
        return det
    
    def _get_minor(self, row, col):
        """Get minor matrix by removing specified row and column"""
        minor_data = []
        for i in range(self.rows):
            if i == row:
                continue
            minor_row = []
            for j in range(self.cols):
                if j == col:
                    continue
                minor_row.append(self.data[i][j])
            minor_data.append(minor_row)
        return Matrix(minor_data)
    
    def inverse(self):
        """Calculate matrix inverse (for square matrices)"""
        if self.rows != self.cols:
            raise ValueError("Inverse only defined for square matrices")
        
        det = self.determinant()
        if abs(det) < 1e-10:
            raise ValueError("Matrix is singular (determinant near zero)")
        
        if self.rows == 2:
            # Direct formula for 2x2
            a, b = self.data[0]
            c, d = self.data[1]
            return Matrix([[d/det, -b/det], [-c/det, a/det]])
        
        # Adjugate method for larger matrices
        cofactors = []
        for i in range(self.rows):
            cofactor_row = []
            for j in range(self.cols):
                minor = self._get_minor(i, j)
                cofactor = ((-1) ** (i + j)) * minor.determinant()
                cofactor_row.append(cofactor)
            cofactors.append(cofactor_row)
        
        # Transpose cofactor matrix and divide by determinant
        adjugate = Matrix(cofactors).transpose()
        return adjugate * (1 / det)
    
    @staticmethod
    def identity(size):
        """Create identity matrix"""
        data = [[1.0 if i == j else 0.0 for j in range(size)] 
                for i in range(size)]
        return Matrix(data)
    
    @staticmethod
    def zeros(rows, cols):
        """Create zero matrix"""
        return Matrix([[0.0 for _ in range(cols)] for _ in range(rows)])


# ============================================================================
# NUMPY WRAPPER WITH SAFE OPERATIONS
# ============================================================================

class SafeMatrixNumPy:
    """NumPy-based matrix with safe operations and error checking"""
    
    def __init__(self, data: Union[List[List[float]], np.ndarray]):
        """Initialize from list or NumPy array"""
        self.data = np.array(data, dtype=np.float64)
        if self.data.ndim != 2:
            raise ValueError("Matrix must be 2-dimensional")
        self.rows, self.cols = self.data.shape
    
    def __repr__(self):
        return f"SafeMatrixNumPy({self.rows}x{self.cols})"
    
    def __str__(self):
        return str(self.data)
    
    def __add__(self, other):
        """Matrix addition with dimension checking"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(
                f"Dimension mismatch: {self.rows}x{self.cols} + "
                f"{other.rows}x{other.cols}"
            )
        return SafeMatrixNumPy(self.data + other.data)
    
    def __sub__(self, other):
        """Matrix subtraction with dimension checking"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(
                f"Dimension mismatch: {self.rows}x{self.cols} - "
                f"{other.rows}x{other.cols}"
            )
        return SafeMatrixNumPy(self.data - other.data)
    
    def __matmul__(self, other):
        """Matrix multiplication with dimension checking"""
        if self.cols != other.rows:
            raise ValueError(
                f"Cannot multiply: {self.rows}x{self.cols} @ "
                f"{other.rows}x{other.cols}"
            )
        return SafeMatrixNumPy(self.data @ other.data)
    
    def __mul__(self, scalar):
        """Scalar multiplication"""
        if not isinstance(scalar, (int, float)):
            raise TypeError("Can only multiply matrix by scalar")
        return SafeMatrixNumPy(self.data * scalar)
    
    def transpose(self):
        """Return transposed matrix"""
        return SafeMatrixNumPy(self.data.T)
    
    def determinant(self):
        """Calculate determinant with singularity check"""
        if self.rows != self.cols:
            raise ValueError("Determinant only defined for square matrices")
        return np.linalg.det(self.data)
    
    def inverse(self):
        """Calculate inverse with singularity check"""
        if self.rows != self.cols:
            raise ValueError("Inverse only defined for square matrices")
        
        det = np.linalg.det(self.data)
        if abs(det) < 1e-10:
            raise ValueError(
                f"Matrix is singular or near-singular (det={det:.2e})"
            )
        
        try:
            return SafeMatrixNumPy(np.linalg.inv(self.data))
        except np.linalg.LinAlgError as e:
            raise ValueError(f"Matrix inversion failed: {e}")
    
    def eigenvalues(self):
        """Calculate eigenvalues"""
        if self.rows != self.cols:
            raise ValueError("Eigenvalues only defined for square matrices")
        return np.linalg.eigvals(self.data)
    
    def solve(self, b):
        """Solve linear system Ax = b"""
        if isinstance(b, SafeMatrixNumPy):
            b = b.data
        else:
            b = np.array(b)
        
        if self.rows != self.cols:
            raise ValueError("System must be square")
        if self.rows != len(b):
            raise ValueError("Dimension mismatch in linear system")
        
        try:
            return np.linalg.solve(self.data, b)
        except np.linalg.LinAlgError as e:
            raise ValueError(f"Cannot solve system: {e}")
    
    @staticmethod
    def identity(size):
        """Create identity matrix"""
        return SafeMatrixNumPy(np.eye(size))
    
    @staticmethod
    def zeros(rows, cols):
        """Create zero matrix"""
        return SafeMatrixNumPy(np.zeros((rows, cols)))


# ============================================================================
# DEMONSTRATION AND TESTING
# ============================================================================

def demonstrate_errors():
    """Show common errors and how to handle them"""
    print("=" * 60)
    print("COMMON ERRORS DEMONSTRATION")
    print("=" * 60)
    
    # Error 1: Dimension mismatch in addition
    print("\n1. Dimension Mismatch in Addition:")
    try:
        m1 = Matrix([[1, 2], [3, 4]])
        m2 = Matrix([[1, 2, 3]])
        result = m1 + m2
    except ValueError as e:
        print(f"   ✗ Error caught: {e}")
    
    # Error 2: Invalid matrix multiplication
    print("\n2. Invalid Matrix Multiplication:")
    try:
        m1 = Matrix([[1, 2]])  # 1x2
        m2 = Matrix([[1, 2]])  # 1x2
        result = m1 * m2
    except ValueError as e:
        print(f"   ✗ Error caught: {e}")
    
    # Error 3: Non-rectangular matrix
    print("\n3. Non-Rectangular Matrix:")
    try:
        m = Matrix([[1, 2], [3]])
    except ValueError as e:
        print(f"   ✗ Error caught: {e}")
    
    # Error 4: Singular matrix inverse
    print("\n4. Singular Matrix Inverse:")
    try:
        m = Matrix([[1, 2], [2, 4]])  # Singular
        inv = m.inverse()
    except ValueError as e:
        print(f"   ✗ Error caught: {e}")


def demonstrate_correct_usage():
    """Show correct usage patterns"""
    print("\n" + "=" * 60)
    print("CORRECT USAGE DEMONSTRATION")
    print("=" * 60)
    
    # Manual implementation
    print("\n--- MANUAL IMPLEMENTATION ---")
    m1 = Matrix([[1, 2], [3, 4]])
    m2 = Matrix([[5, 6], [7, 8]])
    
    print(f"\nMatrix 1:\n{m1}")
    print(f"\nMatrix 2:\n{m2}")
    
    print(f"\nAddition:\n{m1 + m2}")
    print(f"\nSubtraction:\n{m1 - m2}")
    print(f"\nMultiplication:\n{m1 * m2}")
    print(f"\nScalar multiplication (m1 * 2):\n{m1 * 2}")
    print(f"\nTranspose of m1:\n{m1.transpose()}")
    print(f"\nDeterminant of m1: {m1.determinant()}")
    
    # NumPy implementation
    print("\n--- NUMPY IMPLEMENTATION ---")
    n1 = SafeMatrixNumPy([[1, 2], [3, 4]])
    n2 = SafeMatrixNumPy([[5, 6], [7, 8]])
    
    print(f"\nMatrix 1:\n{n1}")
    print(f"\nMatrix 2:\n{n2}")
    
    print(f"\nAddition:\n{n1 + n2}")
    print(f"\nMatrix multiplication:\n{n1 @ n2}")
    print(f"\nTranspose:\n{n1.transpose()}")
    print(f"\nDeterminant: {n1.determinant()}")
    print(f"\nEigenvalues: {n1.eigenvalues()}")


def compare_performance():
    """Compare performance between manual and NumPy"""
    import time
    
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    
    size = 100
    data = [[float(i * size + j) for j in range(size)] for i in range(size)]
    
    # Manual implementation
    print(f"\nManual implementation ({size}x{size} matrix multiplication):")
    m1 = Matrix(data)
    m2 = Matrix(data)
    start = time.time()
    result = m1 * m2
    manual_time = time.time() - start
    print(f"   Time: {manual_time:.4f} seconds")
    
    # NumPy implementation
    print(f"\nNumPy implementation ({size}x{size} matrix multiplication):")
    n1 = SafeMatrixNumPy(data)
    n2 = SafeMatrixNumPy(data)
    start = time.time()
    result = n1 @ n2
    numpy_time = time.time() - start
    print(f"   Time: {numpy_time:.4f} seconds")
    
    print(f"\nSpeedup: {manual_time / numpy_time:.1f}x faster with NumPy")


if __name__ == "__main__":
    demonstrate_errors()
    demonstrate_correct_usage()
    compare_performance()

// Complete Matrix Implementation in Rust
// Demonstrates both manual and ndarray approaches with error handling
//
// Cargo.toml dependencies:
// [dependencies]
// ndarray = "0.15"

use std::fmt;
use std::ops::{Add, Sub, Mul};

// ============================================================================
// MANUAL IMPLEMENTATION
// ============================================================================

#[derive(Debug, Clone, PartialEq)]
pub struct Matrix {
    data: Vec<Vec<f64>>,
    rows: usize,
    cols: usize,
}

impl Matrix {
    /// Create a new matrix from 2D vector
    pub fn new(data: Vec<Vec<f64>>) -> Result<Self, String> {
        if data.is_empty() || data[0].is_empty() {
            return Err("Matrix cannot be empty".to_string());
        }

        let cols = data[0].len();
        for (i, row) in data.iter().enumerate() {
            if row.len() != cols {
                return Err(format!(
                    "All rows must have same length. Row {} has {} elements, expected {}",
                    i, row.len(), cols
                ));
            }
        }

        let rows = data.len();
        Ok(Matrix { data, rows, cols })
    }

    /// Create a zero matrix
    pub fn zeros(rows: usize, cols: usize) -> Self {
        Matrix {
            data: vec![vec![0.0; cols]; rows],
            rows,
            cols,
        }
    }

    /// Create an identity matrix
    pub fn identity(size: usize) -> Self {
        let mut data = vec![vec![0.0; size]; size];
        for i in 0..size {
            data[i][i] = 1.0;
        }
        Matrix {
            data,
            rows: size,
            cols: size,
        }
    }

    /// Get element at position (row, col)
    pub fn get(&self, row: usize, col: usize) -> Result<f64, String> {
        if row < self.rows && col < self.cols {
            Ok(self.data[row][col])
        } else {
            Err(format!(
                "Index ({}, {}) out of bounds for {}x{} matrix",
                row, col, self.rows, self.cols
            ))
        }
    }

    /// Set element at position (row, col)
    pub fn set(&mut self, row: usize, col: usize, value: f64) -> Result<(), String> {
        if row < self.rows && col < self.cols {
            self.data[row][col] = value;
            Ok(())
        } else {
            Err(format!(
                "Index ({}, {}) out of bounds for {}x{} matrix",
                row, col, self.rows, self.cols
            ))
        }
    }

    /// Return matrix dimensions
    pub fn shape(&self) -> (usize, usize) {
        (self.rows, self.cols)
    }

    /// Transpose the matrix
    pub fn transpose(&self) -> Self {
        let mut result = Matrix::zeros(self.cols, self.rows);
        for i in 0..self.rows {
            for j in 0..self.cols {
                result.data[j][i] = self.data[i][j];
            }
        }
        result
    }

    /// Calculate determinant (only for square matrices)
    pub fn determinant(&self) -> Result<f64, String> {
        if self.rows != self.cols {
            return Err(format!(
                "Determinant only defined for square matrices, got {}x{}",
                self.rows, self.cols
            ));
        }

        if self.rows == 1 {
            return Ok(self.data[0][0]);
        }

        if self.rows == 2 {
            return Ok(self.data[0][0] * self.data[1][1] - 
                     self.data[0][1] * self.data[1][0]);
        }

        // Cofactor expansion along first row
        let mut det = 0.0;
        for j in 0..self.cols {
            let minor = self.get_minor(0, j)?;
            let cofactor = if j % 2 == 0 { 1.0 } else { -1.0 };
            det += cofactor * self.data[0][j] * minor.determinant()?;
        }
        Ok(det)
    }

    /// Get minor matrix by removing specified row and column
    fn get_minor(&self, row: usize, col: usize) -> Result<Self, String> {
        let mut minor_data = Vec::new();
        for i in 0..self.rows {
            if i == row {
                continue;
            }
            let mut minor_row = Vec::new();
            for j in 0..self.cols {
                if j == col {
                    continue;
                }
                minor_row.push(self.data[i][j]);
            }
            minor_data.push(minor_row);
        }
        Matrix::new(minor_data)
    }

    /// Calculate matrix inverse
    pub fn inverse(&self) -> Result<Self, String> {
        if self.rows != self.cols {
            return Err("Inverse only defined for square matrices".to_string());
        }

        let det = self.determinant()?;
        if det.abs() < 1e-10 {
            return Err(format!(
                "Matrix is singular or near-singular (determinant = {:.2e})",
                det
            ));
        }

        if self.rows == 2 {
            // Direct formula for 2x2
            let a = self.data[0][0];
            let b = self.data[0][1];
            let c = self.data[1][0];
            let d = self.data[1][1];
            
            return Matrix::new(vec![
                vec![d / det, -b / det],
                vec![-c / det, a / det],
            ]);
        }

        // Adjugate method for larger matrices
        let mut cofactors = vec![vec![0.0; self.cols]; self.rows];
        for i in 0..self.rows {
            for j in 0..self.cols {
                let minor = self.get_minor(i, j)?;
                let sign = if (i + j) % 2 == 0 { 1.0 } else { -1.0 };
                cofactors[i][j] = sign * minor.determinant()?;
            }
        }

        // Transpose cofactor matrix and divide by determinant
        let adjugate = Matrix::new(cofactors)?.transpose();
        Ok(adjugate.scalar_multiply(1.0 / det))
    }

    /// Multiply matrix by scalar
    pub fn scalar_multiply(&self, scalar: f64) -> Self {
        let result = self.data.iter()
            .map(|row| row.iter().map(|&x| x * scalar).collect())
            .collect();
        Matrix::new(result).unwrap()
    }

    /// Element-wise multiplication
    pub fn element_wise_multiply(&self, other: &Matrix) -> Result<Self, String> {
        if self.rows != other.rows || self.cols != other.cols {
            return Err(format!(
                "Dimension mismatch: {}x{} * {}x{}",
                self.rows, self.cols, other.rows, other.cols
            ));
        }

        let result = (0..self.rows)
            .map(|i| {
                (0..self.cols)
                    .map(|j| self.data[i][j] * other.data[i][j])
                    .collect()
            })
            .collect();
        Matrix::new(result)
    }
}

/// Implement Add trait for Matrix + Matrix
impl Add for &Matrix {
    type Output = Result<Matrix, String>;

    fn add(self, other: &Matrix) -> Self::Output {
        if self.rows != other.rows || self.cols != other.cols {
            return Err(format!(
                "Dimension mismatch: {}x{} + {}x{}",
                self.rows, self.cols, other.rows, other.cols
            ));
        }

        let result = (0..self.rows)
            .map(|i| {
                (0..self.cols)
                    .map(|j| self.data[i][j] + other.data[i][j])
                    .collect()
            })
            .collect();
        Matrix::new(result)
    }
}

/// Implement Sub trait for Matrix - Matrix
impl Sub for &Matrix {
    type Output = Result<Matrix, String>;

    fn sub(self, other: &Matrix) -> Self::Output {
        if self.rows != other.rows || self.cols != other.cols {
            return Err(format!(
                "Dimension mismatch: {}x{} - {}x{}",
                self.rows, self.cols, other.rows, other.cols
            ));
        }

        let result = (0..self.rows)
            .map(|i| {
                (0..self.cols)
                    .map(|j| self.data[i][j] - other.data[i][j])
                    .collect()
            })
            .collect();
        Matrix::new(result)
    }
}

/// Implement Mul trait for Matrix @ Matrix (matrix multiplication)
impl Mul for &Matrix {
    type Output = Result<Matrix, String>;

    fn mul(self, other: &Matrix) -> Self::Output {
        if self.cols != other.rows {
            return Err(format!(
                "Cannot multiply: {}x{} @ {}x{}",
                self.rows, self.cols, other.rows, other.cols
            ));
        }

        let result = (0..self.rows)
            .map(|i| {
                (0..other.cols)
                    .map(|j| {
                        (0..self.cols)
                            .map(|k| self.data[i][k] * other.data[k][j])
                            .sum()
                    })
                    .collect()
            })
            .collect();
        Matrix::new(result)
    }
}

/// Implement Display trait for pretty printing
impl fmt::Display for Matrix {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        for (i, row) in self.data.iter().enumerate() {
            write!(f, "[")?;
            for (j, val) in row.iter().enumerate() {
                if j > 0 {
                    write!(f, ", ")?;
                }
                write!(f, "{:8.3}", val)?;
            }
            write!(f, "]")?;
            if i < self.rows - 1 {
                writeln!(f)?;
            }
        }
        Ok(())
    }
}

// ============================================================================
// DEMONSTRATION AND TESTING
// ============================================================================

fn demonstrate_errors() {
    println!("{}", "=".repeat(60));
    println!("COMMON ERRORS DEMONSTRATION");
    println!("{}", "=".repeat(60));

    // Error 1: Dimension mismatch in addition
    println!("\n1. Dimension Mismatch in Addition:");
    let m1 = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
    let m2 = Matrix::new(vec![vec![1.0, 2.0, 3.0]]).unwrap();
    match &m1 + &m2 {
        Ok(_) => println!("   ✓ Success"),
        Err(e) => println!("   ✗ Error caught: {}", e),
    }

    // Error 2: Invalid matrix multiplication
    println!("\n2. Invalid Matrix Multiplication:");
    let m1 = Matrix::new(vec![vec![1.0, 2.0]]).unwrap();  // 1x2
    let m2 = Matrix::new(vec![vec![1.0, 2.0]]).unwrap();  // 1x2
    match &m1 * &m2 {
        Ok(_) => println!("   ✓ Success"),
        Err(e) => println!("   ✗ Error caught: {}", e),
    }

    // Error 3: Non-rectangular matrix
    println!("\n3. Non-Rectangular Matrix:");
    match Matrix::new(vec![vec![1.0, 2.0], vec![3.0]]) {
        Ok(_) => println!("   ✓ Created matrix"),
        Err(e) => println!("   ✗ Error caught: {}", e),
    }

    // Error 4: Singular matrix inverse
    println!("\n4. Singular Matrix Inverse:");
    let m = Matrix::new(vec![vec![1.0, 2.0], vec![2.0, 4.0]]).unwrap();
    match m.inverse() {
        Ok(_) => println!("   ✓ Inverse computed"),
        Err(e) => println!("   ✗ Error caught: {}", e),
    }

    // Error 5: Index out of bounds
    println!("\n5. Index Out of Bounds:");
    let m = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
    match m.get(5, 5) {
        Ok(val) => println!("   ✓ Got value: {}", val),
        Err(e) => println!("   ✗ Error caught: {}", e),
    }
}

fn demonstrate_correct_usage() {
    println!("\n{}", "=".repeat(60));
    println!("CORRECT USAGE DEMONSTRATION");
    println!("{}", "=".repeat(60));

    println!("\n--- MANUAL IMPLEMENTATION ---");

    let m1 = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
    let m2 = Matrix::new(vec![vec![5.0, 6.0], vec![7.0, 8.0]]).unwrap();

    println!("\nMatrix 1:\n{}", m1);
    println!("\nMatrix 2:\n{}", m2);

    println!("\nAddition:");
    println!("{}", (&m1 + &m2).unwrap());

    println!("\nSubtraction:");
    println!("{}", (&m1 - &m2).unwrap());

    println!("\nMatrix Multiplication:");
    println!("{}", (&m1 * &m2).unwrap());

    println!("\nScalar Multiplication (m1 * 2):");
    println!("{}", m1.scalar_multiply(2.0));

    println!("\nTranspose of m1:");
    println!("{}", m1.transpose());

    println!("\nDeterminant of m1: {:.3}", m1.determinant().unwrap());

    println!("\nIdentity Matrix (3x3):");
    println!("{}", Matrix::identity(3));

    // Inverse example
    let m3 = Matrix::new(vec![vec![4.0, 7.0], vec![2.0, 6.0]]).unwrap();
    println!("\nOriginal matrix:");
    println!("{}", m3);
    println!("\nInverse:");
    println!("{}", m3.inverse().unwrap());
}

fn main() {
    demonstrate_errors();
    demonstrate_correct_usage();
    
    println!("\n{}", "=".repeat(60));
    println!("Program completed successfully!");
    println!("{}", "=".repeat(60));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_matrix_creation() {
        let m = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]);
        assert!(m.is_ok());
        let m = m.unwrap();
        assert_eq!(m.shape(), (2, 2));
    }

    #[test]
    fn test_matrix_addition() {
        let m1 = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
        let m2 = Matrix::new(vec![vec![5.0, 6.0], vec![7.0, 8.0]]).unwrap();
        let result = (&m1 + &m2).unwrap();
        assert_eq!(result.get(0, 0).unwrap(), 6.0);
        assert_eq!(result.get(1, 1).unwrap(), 12.0);
    }

    #[test]
    fn test_matrix_multiplication() {
        let m1 = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
        let m2 = Matrix::new(vec![vec![5.0, 6.0], vec![7.0, 8.0]]).unwrap();
        let result = (&m1 * &m2).unwrap();
        assert_eq!(result.get(0, 0).unwrap(), 19.0);
        assert_eq!(result.get(0, 1).unwrap(), 22.0);
        assert_eq!(result.get(1, 0).unwrap(), 43.0);
        assert_eq!(result.get(1, 1).unwrap(), 50.0);
    }

    #[test]
    fn test_transpose() {
        let m = Matrix::new(vec![vec![1.0, 2.0, 3.0], vec![4.0, 5.0, 6.0]]).unwrap();
        let t = m.transpose();
        assert_eq!(t.shape(), (3, 2));
        assert_eq!(t.get(0, 0).unwrap(), 1.0);
        assert_eq!(t.get(1, 0).unwrap(), 2.0);
        assert_eq!(t.get(2, 1).unwrap(), 6.0);
    }

    #[test]
    fn test_determinant() {
        let m = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
        let det = m.determinant().unwrap();
        assert!((det - (-2.0)).abs() < 1e-10);
    }

    #[test]
    fn test_inverse() {
        let m = Matrix::new(vec![vec![4.0, 7.0], vec![2.0, 6.0]]).unwrap();
        let inv = m.inverse().unwrap();
        let identity = (&m * &inv).unwrap();
        
        // Check if result is close to identity matrix
        assert!((identity.get(0, 0).unwrap() - 1.0).abs() < 1e-10);
        assert!((identity.get(0, 1).unwrap()).abs() < 1e-10);
        assert!((identity.get(1, 0).unwrap()).abs() < 1e-10);
        assert!((identity.get(1, 1).unwrap() - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_dimension_mismatch() {
        let m1 = Matrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
        let m2 = Matrix::new(vec![vec![1.0, 2.0, 3.0]]).unwrap();
        assert!((&m1 + &m2).is_err());
    }

    #[test]
    fn test_singular_matrix() {
        let m = Matrix::new(vec![vec![1.0, 2.0], vec![2.0, 4.0]]).unwrap();
        assert!(m.inverse().is_err());
    }

    #[test]
    fn test_identity_matrix() {
        let id = Matrix::identity(3);
        assert_eq!(id.get(0, 0).unwrap(), 1.0);
        assert_eq!(id.get(1, 1).unwrap(), 1.0);
        assert_eq!(id.get(2, 2).unwrap(), 1.0);
        assert_eq!(id.get(0, 1).unwrap(), 0.0);
    }
}

// Rust Matrix Implementation using ndarray
// This demonstrates the library approach with proper error handling
//
// Cargo.toml:
// [dependencies]
// ndarray = "0.15"
// ndarray-linalg = { version = "0.16", features = ["openblas-static"] }

use ndarray::{Array2, ArrayBase, Dim, OwnedRepr, arr2};

// ============================================================================
// SAFE NDARRAY WRAPPER
// ============================================================================

#[derive(Clone)]
pub struct SafeMatrix {
    data: Array2<f64>,
}

impl SafeMatrix {
    /// Create a new matrix from 2D vector
    pub fn new(data: Vec<Vec<f64>>) -> Result<Self, String> {
        if data.is_empty() || data[0].is_empty() {
            return Err("Matrix cannot be empty".to_string());
        }

        let rows = data.len();
        let cols = data[0].len();
        
        // Validate rectangular shape
        for (i, row) in data.iter().enumerate() {
            if row.len() != cols {
                return Err(format!(
                    "All rows must have same length. Row {} has {} elements, expected {}",
                    i, row.len(), cols
                ));
            }
        }

        // Flatten data and create array
        let flat: Vec<f64> = data.into_iter().flatten().collect();
        let array = Array2::from_shape_vec((rows, cols), flat)
            .map_err(|e| format!("Failed to create array: {}", e))?;

        Ok(SafeMatrix { data: array })
    }

    /// Create from ndarray Array2
    pub fn from_array(data: Array2<f64>) -> Self {
        SafeMatrix { data }
    }

    /// Create zero matrix
    pub fn zeros(rows: usize, cols: usize) -> Self {
        SafeMatrix {
            data: Array2::zeros((rows, cols)),
        }
    }

    /// Create identity matrix
    pub fn identity(size: usize) -> Self {
        SafeMatrix {
            data: Array2::eye(size),
        }
    }

    /// Get shape as (rows, cols)
    pub fn shape(&self) -> (usize, usize) {
        let shape = self.data.shape();
        (shape[0], shape[1])
    }

    /// Get element at position
    pub fn get(&self, row: usize, col: usize) -> Result<f64, String> {
        self.data.get((row, col))
            .copied()
            .ok_or_else(|| format!("Index ({}, {}) out of bounds", row, col))
    }

    /// Matrix addition with dimension checking
    pub fn add(&self, other: &SafeMatrix) -> Result<Self, String> {
        let (rows1, cols1) = self.shape();
        let (rows2, cols2) = other.shape();
        
        if rows1 != rows2 || cols1 != cols2 {
            return Err(format!(
                "Dimension mismatch: {}x{} + {}x{}",
                rows1, cols1, rows2, cols2
            ));
        }

        Ok(SafeMatrix {
            data: &self.data + &other.data,
        })
    }

    /// Matrix subtraction with dimension checking
    pub fn sub(&self, other: &SafeMatrix) -> Result<Self, String> {
        let (rows1, cols1) = self.shape();
        let (rows2, cols2) = other.shape();
        
        if rows1 != rows2 || cols1 != cols2 {
            return Err(format!(
                "Dimension mismatch: {}x{} - {}x{}",
                rows1, cols1, rows2, cols2
            ));
        }

        Ok(SafeMatrix {
            data: &self.data - &other.data,
        })
    }

    /// Matrix multiplication with dimension checking
    pub fn matmul(&self, other: &SafeMatrix) -> Result<Self, String> {
        let (rows1, cols1) = self.shape();
        let (rows2, cols2) = other.shape();
        
        if cols1 != rows2 {
            return Err(format!(
                "Cannot multiply: {}x{} @ {}x{}",
                rows1, cols1, rows2, cols2
            ));
        }

        Ok(SafeMatrix {
            data: self.data.dot(&other.data),
        })
    }

    /// Element-wise multiplication
    pub fn element_wise_mul(&self, other: &SafeMatrix) -> Result<Self, String> {
        let (rows1, cols1) = self.shape();
        let (rows2, cols2) = other.shape();
        
        if rows1 != rows2 || cols1 != cols2 {
            return Err(format!(
                "Dimension mismatch: {}x{} * {}x{}",
                rows1, cols1, rows2, cols2
            ));
        }

        Ok(SafeMatrix {
            data: &self.data * &other.data,
        })
    }

    /// Scalar multiplication
    pub fn scalar_mul(&self, scalar: f64) -> Self {
        SafeMatrix {
            data: &self.data * scalar,
        }
    }

    /// Transpose
    pub fn transpose(&self) -> Self {
        SafeMatrix {
            data: self.data.t().to_owned(),
        }
    }

    /// Calculate sum of all elements
    pub fn sum(&self) -> f64 {
        self.data.sum()
    }

    /// Calculate mean of all elements
    pub fn mean(&self) -> f64 {
        let total = self.data.len();
        if total == 0 {
            return 0.0;
        }
        self.data.sum() / (total as f64)
    }

    /// Get reference to underlying array
    pub fn as_array(&self) -> &Array2<f64> {
        &self.data
    }
}

impl std::fmt::Display for SafeMatrix {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{}", self.data)
    }
}

impl std::fmt::Debug for SafeMatrix {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        let (rows, cols) = self.shape();
        write!(f, "SafeMatrix({}x{})", rows, cols)
    }
}

// ============================================================================
// DEMONSTRATIONS
// ============================================================================

fn demonstrate_basic_operations() {
    println!("{}", "=".repeat(60));
    println!("BASIC OPERATIONS WITH NDARRAY");
    println!("{}", "=".repeat(60));

    // Create matrices
    let m1 = SafeMatrix::new(vec![
        vec![1.0, 2.0],
        vec![3.0, 4.0],
    ]).unwrap();

    let m2 = SafeMatrix::new(vec![
        vec![5.0, 6.0],
        vec![7.0, 8.0],
    ]).unwrap();

    println!("\nMatrix 1:\n{}", m1);
    println!("\nMatrix 2:\n{}", m2);

    // Addition
    println!("\nAddition (m1 + m2):");
    match m1.add(&m2) {
        Ok(result) => println!("{}", result),
        Err(e) => println!("Error: {}", e),
    }

    // Subtraction
    println!("\nSubtraction (m1 - m2):");
    match m1.sub(&m2) {
        Ok(result) => println!("{}", result),
        Err(e) => println!("Error: {}", e),
    }

    // Matrix multiplication
    println!("\nMatrix Multiplication (m1 @ m2):");
    match m1.matmul(&m2) {
        Ok(result) => println!("{}", result),
        Err(e) => println!("Error: {}", e),
    }

    // Element-wise multiplication
    println!("\nElement-wise Multiplication (m1 * m2):");
    match m1.element_wise_mul(&m2) {
        Ok(result) => println!("{}", result),
        Err(e) => println!("Error: {}", e),
    }

    // Scalar multiplication
    println!("\nScalar Multiplication (m1 * 2):");
    println!("{}", m1.scalar_mul(2.0));

    // Transpose
    println!("\nTranspose of m1:");
    println!("{}", m1.transpose());

    // Identity matrix
    println!("\nIdentity Matrix (3x3):");
    println!("{}", SafeMatrix::identity(3));
}

fn demonstrate_errors() {
    println!("\n{}", "=".repeat(60));
    println!("ERROR HANDLING DEMONSTRATION");
    println!("{}", "=".repeat(60));

    // Error 1: Dimension mismatch in addition
    println!("\n1. Dimension Mismatch in Addition:");
    let m1 = SafeMatrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
    let m2 = SafeMatrix::new(vec![vec![1.0, 2.0, 3.0]]).unwrap();
    match m1.add(&m2) {
        Ok(_) => println!("   ✓ Success"),
        Err(e) => println!("   ✗ Error caught: {}", e),
    }

    // Error 2: Invalid matrix multiplication
    println!("\n2. Invalid Matrix Multiplication:");
    let m1 = SafeMatrix::new(vec![vec![1.0, 2.0]]).unwrap();  // 1x2
    let m2 = SafeMatrix::new(vec![vec![1.0, 2.0]]).unwrap();  // 1x2
    match m1.matmul(&m2) {
        Ok(_) => println!("   ✓ Success"),
        Err(e) => println!("   ✗ Error caught: {}", e),
    }

    // Error 3: Non-rectangular matrix
    println!("\n3. Non-Rectangular Matrix:");
    match SafeMatrix::new(vec![vec![1.0, 2.0], vec![3.0]]) {
        Ok(_) => println!("   ✓ Created matrix"),
        Err(e) => println!("   ✗ Error caught: {}", e),
    }

    // Error 4: Index out of bounds
    println!("\n4. Index Out of Bounds:");
    let m = SafeMatrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
    match m.get(5, 5) {
        Ok(val) => println!("   ✓ Got value: {}", val),
        Err(e) => println!("   ✗ Error caught: {}", e),
    }
}

fn demonstrate_advanced_operations() {
    println!("\n{}", "=".repeat(60));
    println!("ADVANCED OPERATIONS");
    println!("{}", "=".repeat(60));

    let m = SafeMatrix::new(vec![
        vec![1.0, 2.0, 3.0],
        vec![4.0, 5.0, 6.0],
        vec![7.0, 8.0, 9.0],
    ]).unwrap();

    println!("\nMatrix:");
    println!("{}", m);

    println!("\nSum of all elements: {}", m.sum());
    println!("Mean of all elements: {:.2}", m.mean());

    println!("\nShape: {:?}", m.shape());

    // Chain operations
    println!("\nChained Operations: (m * 2) + identity");
    let identity = SafeMatrix::identity(3);
    let scaled = m.scalar_mul(2.0);
    match scaled.add(&identity) {
        Ok(result) => println!("{}", result),
        Err(e) => println!("Error: {}", e),
    }
}

fn compare_with_direct_ndarray() {
    println!("\n{}", "=".repeat(60));
    println!("DIRECT NDARRAY USAGE (Without Wrapper)");
    println!("{}", "=".repeat(60));

    // Direct ndarray usage - more concise but less safe
    let a = arr2(&[[1.0, 2.0], [3.0, 4.0]]);
    let b = arr2(&[[5.0, 6.0], [7.0, 8.0]]);

    println!("\nMatrix a:\n{}", a);
    println!("\nMatrix b:\n{}", b);

    // Operations - note the different syntax
    println!("\nAddition:");
    println!("{}", &a + &b);

    println!("\nMatrix multiplication:");
    println!("{}", a.dot(&b));

    println!("\nElement-wise multiplication:");
    println!("{}", &a * &b);

    println!("\nScalar multiplication:");
    println!("{}", &a * 2.0);

    println!("\nTranspose:");
    println!("{}", a.t());

    // WARNING: No dimension checking at compile time!
    println!("\n⚠️  WARNING: Direct ndarray can panic on dimension mismatch!");
    println!("Always use proper error handling in production code.");
}

fn main() {
    demonstrate_basic_operations();
    demonstrate_errors();
    demonstrate_advanced_operations();
    compare_with_direct_ndarray();

    println!("\n{}", "=".repeat(60));
    println!("Program completed successfully!");
    println!("{}", "=".repeat(60));
}

// ============================================================================
// UNIT TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_creation() {
        let m = SafeMatrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]);
        assert!(m.is_ok());
        assert_eq!(m.unwrap().shape(), (2, 2));
    }

    #[test]
    fn test_addition() {
        let m1 = SafeMatrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
        let m2 = SafeMatrix::new(vec![vec![5.0, 6.0], vec![7.0, 8.0]]).unwrap();
        let result = m1.add(&m2).unwrap();
        assert_eq!(result.get(0, 0).unwrap(), 6.0);
        assert_eq!(result.get(1, 1).unwrap(), 12.0);
    }

    #[test]
    fn test_multiplication() {
        let m1 = SafeMatrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
        let m2 = SafeMatrix::new(vec![vec![5.0, 6.0], vec![7.0, 8.0]]).unwrap();
        let result = m1.matmul(&m2).unwrap();
        assert_eq!(result.get(0, 0).unwrap(), 19.0);
        assert_eq!(result.get(0, 1).unwrap(), 22.0);
    }

    #[test]
    fn test_transpose() {
        let m = SafeMatrix::new(vec![vec![1.0, 2.0, 3.0], vec![4.0, 5.0, 6.0]]).unwrap();
        let t = m.transpose();
        assert_eq!(t.shape(), (3, 2));
        assert_eq!(t.get(0, 1).unwrap(), 4.0);
    }

    #[test]
    fn test_dimension_mismatch() {
        let m1 = SafeMatrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
        let m2 = SafeMatrix::new(vec![vec![1.0, 2.0, 3.0]]).unwrap();
        assert!(m1.add(&m2).is_err());
    }

    #[test]
    fn test_identity() {
        let id = SafeMatrix::identity(3);
        assert_eq!(id.get(0, 0).unwrap(), 1.0);
        assert_eq!(id.get(1, 1).unwrap(), 1.0);
        assert_eq!(id.get(0, 1).unwrap(), 0.0);
    }

    #[test]
    fn test_scalar_multiplication() {
        let m = SafeMatrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
        let result = m.scalar_mul(2.0);
        assert_eq!(result.get(0, 0).unwrap(), 2.0);
        assert_eq!(result.get(1, 1).unwrap(), 8.0);
    }

    #[test]
    fn test_sum_and_mean() {
        let m = SafeMatrix::new(vec![vec![1.0, 2.0], vec![3.0, 4.0]]).unwrap();
        assert_eq!(m.sum(), 10.0);
        assert_eq!(m.mean(), 2.5);
    }
}

# Matrix Memory Model: Python vs Rust
## Comprehensive ASCII Diagram

---

## 1. PYTHON MATRIX MEMORY MODEL

### Step 1: Matrix Creation (List of Lists)
```
CODE: matrix = [[1, 2], [3, 4]]

STACK MEMORY                    HEAP MEMORY
┌──────────────┐               ┌─────────────────────────────────┐
│              │               │                                 │
│  matrix  ────┼──────────────>│  List Object (outer)            │
│  (reference) │               │  ┌───────────────────┐          │
│              │               │  │ ob_refcount: 1    │          │
└──────────────┘               │  │ ob_type: list     │          │
                               │  │ ob_size: 2        │          │
                               │  └───────────────────┘          │
                               │  │ item[0] ──┐                  │
                               │  │ item[1] ──┼─┐                │
                               │  └───────────┼─┼────┘           │
                               │              │ │                │
                               │    ┌─────────┘ └────────┐       │
                               │    ▼                     ▼       │
                               │  ┌──────────────┐  ┌──────────────┐
                               │  │ List [1, 2]  │  │ List [3, 4]  │
                               │  │ refcount: 1  │  │ refcount: 1  │
                               │  │ ┌──┐  ┌──┐  │  │ ┌──┐  ┌──┐  │
                               │  │ │1 │  │2 │  │  │ │3 │  │4 │  │
                               │  │ └──┘  └──┘  │  │ └──┘  └──┘  │
                               │  └──────────────┘  └──────────────┘
                               └─────────────────────────────────┘
```

### Step 2: Assignment (Reference Semantics)
```
CODE: matrix2 = matrix

STACK MEMORY                    HEAP MEMORY
┌──────────────┐               ┌─────────────────────────────────┐
│              │               │                                 │
│  matrix  ────┼──────────┐    │  List Object (outer)            │
│  (reference) │          │    │  ┌───────────────────┐          │
│              │          │    │  │ ob_refcount: 2  ←─┼─ Both    │
│  matrix2 ────┼──────────┘    │  │ ob_type: list     │   point  │
│  (reference) │               │  │ ob_size: 2        │   here!  │
│              │               │  └───────────────────┘          │
└──────────────┘               │  │ item[0] ──┐                  │
                               │  │ item[1] ──┼─┐                │
                               │  └───────────┼─┼────┘           │
                               │              │ │                │
                               │    ┌─────────┘ └────────┐       │
                               │    ▼                     ▼       │
                               │  ┌──────────────┐  ┌──────────────┐
                               │  │ List [1, 2]  │  │ List [3, 4]  │
                               │  │ refcount: 2  │  │ refcount: 2  │
                               │  └──────────────┘  └──────────────┘
                               └─────────────────────────────────┘

NOTE: matrix2 is NOT a copy! It's another reference to the SAME object.
      Changes through matrix2 will affect matrix!
```

### Step 3: Function Call (Call by Object Reference)
```
CODE: 
def modify_matrix(mat):
    mat[0][0] = 99

modify_matrix(matrix)

STACK MEMORY                    HEAP MEMORY
┌──────────────┐               ┌─────────────────────────────────┐
│ Main Frame   │               │                                 │
│              │               │  List Object (outer)            │
│  matrix  ────┼───────┐       │  ┌───────────────────┐          │
│              │       │       │  │ ob_refcount: 2    │          │
├──────────────┤       │       │  └───────────────────┘          │
│ modify_matrix│       │       │  │ item[0] ──┐                  │
│ Frame        │       │       │  │ item[1] ──┼─┐                │
│              │       └──────>│  └───────────┼─┼────┘           │
│  mat     ────┼───────────────┘              │ │                │
│  (parameter) │                  ┌───────────┘ └────────┐       │
└──────────────┘                  ▼                      ▼       │
                               │  ┌──────────────┐  ┌──────────────┐
                               │  │ List [99, 2] │  │ List [3, 4]  │
                               │  │ refcount: 2  │  │ refcount: 2  │
                               │  │   ▲          │  │              │
                               │  │   │ MODIFIED!│  │              │
                               │  └───┼──────────┘  └──────────────┘
                               └──────┼──────────────────────────────┘
                                      └─ Original matrix is changed!

PYTHON USES "CALL BY OBJECT REFERENCE":
- The reference is passed (not the object itself)
- Mutable objects (lists) can be modified in-place
- Reassigning the parameter doesn't affect the original
```

### Step 4: NumPy Arrays (Contiguous Memory)
```
CODE: import numpy as np
      np_matrix = np.array([[1, 2], [3, 4]])

STACK MEMORY                    HEAP MEMORY
┌──────────────┐               ┌─────────────────────────────────┐
│              │               │ NumPy Array Object              │
│ np_matrix ───┼──────────────>│ ┌─────────────────────┐         │
│  (reference) │               │ │ PyArrayObject        │         │
│              │               │ │ - refcount          │         │
└──────────────┘               │ │ - dtype: int64      │         │
                               │ │ - shape: (2, 2)     │         │
                               │ │ - strides: (16, 8)  │         │
                               │ │ - data pointer ─────┼────┐    │
                               │ └─────────────────────┘    │    │
                               │                            │    │
                               │ CONTIGUOUS DATA BUFFER     │    │
                               │ ┌──────────────────────┐◄──┘    │
                               │ │  1  │  2  │  3  │  4  │       │
                               │ └──────────────────────┘        │
                               │  Row 0    Row 1                 │
                               │  [0,0][0,1][1,0][1,1]           │
                               └─────────────────────────────────┘

NumPy arrays store data in CONTIGUOUS memory blocks for efficiency!
```

---

## 2. RUST MATRIX MEMORY MODEL

### Step 1: Matrix Creation (Vec of Vecs)
```
CODE: let matrix = vec![vec![1, 2], vec![3, 4]];

STACK MEMORY                    HEAP MEMORY
┌──────────────────────┐       ┌─────────────────────────────────┐
│                      │       │                                 │
│  matrix              │       │  Vec Buffer (outer vec)         │
│  ┌────────────────┐  │       │  ┌───┬───┬────┐                │
│  │ ptr        ────┼──┼──────>│  │ │ │ │ │    │ (capacity: 2)  │
│  │ len: 2         │  │       │  └─┼─┴─┼─┴────┘                │
│  │ capacity: 2    │  │       │    │   │                        │
│  └────────────────┘  │       │    │   │                        │
│ (24 bytes on stack)  │       │    │   │                        │
└──────────────────────┘       │    │   │                        │
                               │    ▼   ▼                        │
                               │  ┌──────────┐  ┌──────────┐    │
                               │  │Vec[1, 2] │  │Vec[3, 4] │    │
                               │  │ ┌──┬──┐  │  │ ┌──┬──┐  │    │
                               │  │ │1 │2 │  │  │ │3 │4 │  │    │
                               │  │ └──┴──┘  │  │ └──┴──┘  │    │
                               │  └──────────┘  └──────────┘    │
                               └─────────────────────────────────┘

OWNERSHIP: 'matrix' OWNS the outer Vec, which OWNS the inner Vecs
```

### Step 2: Move Semantics (Transfer Ownership)
```
CODE: let matrix2 = matrix;  // matrix is MOVED, not copied!

BEFORE MOVE:
STACK MEMORY                    HEAP MEMORY
┌──────────────────────┐       ┌─────────────────────────────────┐
│  matrix              │       │                                 │
│  ┌────────────────┐  │       │  Vec Buffer                     │
│  │ ptr        ────┼──┼──────>│  ┌───┬───┬────┐                │
│  │ len: 2         │  │       │  │ │ │ │ │    │                │
│  │ capacity: 2    │  │       │  └─┼─┴─┼─┴────┘                │
│  └────────────────┘  │       │    ▼   ▼                        │
└──────────────────────┘       │  Inner Vecs...                  │
                               └─────────────────────────────────┘

AFTER MOVE:
STACK MEMORY                    HEAP MEMORY
┌──────────────────────┐       ┌─────────────────────────────────┐
│  matrix (INVALID!)   │       │                                 │
│  ┌────────────────┐  │       │  Vec Buffer                     │
│  │ ⚠ MOVED! ⚠    │  │       │  ┌───┬───┬────┐                │
│  │ Cannot use!    │  │       │  │ │ │ │ │    │                │
│  └────────────────┘  │       │  └─┼─┴─┼─┴────┘                │
│                      │       │    ▼   ▼                        │
│  matrix2             │       │  Inner Vecs...                  │
│  ┌────────────────┐  │       │                                 │
│  │ ptr        ────┼──┼──────>│  (Same heap location!)          │
│  │ len: 2         │  │       │                                 │
│  │ capacity: 2    │  │       │                                 │
│  └────────────────┘  │       │                                 │
└──────────────────────┘       └─────────────────────────────────┘

RUST MOVE SEMANTICS:
- Ownership transferred from 'matrix' to 'matrix2'
- 'matrix' is now INVALID and cannot be used
- NO reference counting needed!
- Prevents double-free errors at compile time
```

### Step 3: Borrowing (Reference Without Ownership Transfer)
```
CODE: 
fn modify_matrix(mat: &mut Vec<Vec<i32>>) {
    mat[0][0] = 99;
}

let mut matrix = vec![vec![1, 2], vec![3, 4]];
modify_matrix(&mut matrix);  // Borrow mutably

STACK MEMORY                    HEAP MEMORY
┌──────────────────────┐       ┌─────────────────────────────────┐
│ Main Frame           │       │                                 │
│                      │       │  Vec Buffer                     │
│  matrix (OWNER)      │       │  ┌───┬───┬────┐                │
│  ┌────────────────┐  │       │  │ │ │ │ │    │                │
│  │ ptr        ────┼──┼──────>│  └─┼─┴─┼─┴────┘                │
│  │ len: 2         │  │   │   │    ▼   ▼                        │
│  │ capacity: 2    │  │   │   │  ┌──────────┐  ┌──────────┐    │
│  └────────────────┘  │   │   │  │Vec[99,2] │  │Vec[3, 4] │    │
├──────────────────────┤   │   │  │   ▲      │  │          │    │
│ modify_matrix Frame  │   │   │  └───┼──────┘  └──────────┘    │
│                      │   │   └──────┼──────────────────────────┘
│  mat: &mut           │   │          │                           
│  ┌────────────────┐  │   │          │                           
│  │ ptr (ref)  ────┼──┼───┼──────────┘                           
│  └────────────────┘  │   │    Borrowed reference               
│  (8 bytes)           │   └──> points to matrix's ptr            
└──────────────────────┘

RUST BORROWING RULES:
1. Either ONE mutable reference OR multiple immutable references
2. References must always be valid (no dangling pointers)
3. Borrow checker enforces at compile time!

&matrix      → Immutable borrow (read-only)
&mut matrix  → Mutable borrow (read-write, exclusive)
```

### Step 4: Clone (Deep Copy)
```
CODE: let matrix2 = matrix.clone();

STACK MEMORY                    HEAP MEMORY
┌──────────────────────┐       ┌─────────────────────────────────┐
│                      │       │  ORIGINAL DATA                  │
│  matrix              │       │  ┌───┬───┐                      │
│  ┌────────────────┐  │       │  │ │ │ │ │                      │
│  │ ptr        ────┼──┼──────>│  └─┼─┴─┼─┘                      │
│  │ len: 2         │  │       │    ▼   ▼                        │
│  │ capacity: 2    │  │       │  Vec[1,2]  Vec[3,4]            │
│  └────────────────┘  │       │                                 │
│                      │       │                                 │
│  matrix2             │       │  CLONED DATA (separate!)        │
│  ┌────────────────┐  │       │  ┌───┬───┐                      │
│  │ ptr        ────┼──┼──────>│  │ │ │ │ │                      │
│  │ len: 2         │  │       │  └─┼─┴─┼─┘                      │
│  │ capacity: 2    │  │       │    ▼   ▼                        │
│  └────────────────┘  │       │  Vec[1,2]  Vec[3,4]            │
└──────────────────────┘       │  (Complete deep copy)           │
                               └─────────────────────────────────┘

CLONE creates a DEEP COPY:
- Separate heap allocations
- Independent ownership
- Changes to one don't affect the other
```

### Step 5: Array on Stack (Fixed Size)
```
CODE: let matrix: [[i32; 2]; 2] = [[1, 2], [3, 4]];

STACK MEMORY                    HEAP MEMORY
┌──────────────────────┐       ┌─────────────────────────────────┐
│                      │       │                                 │
│  matrix              │       │  (Nothing allocated here!)      │
│  ┌────────────────┐  │       │                                 │
│  │ [1, 2]         │  │       │                                 │
│  │ [3, 4]         │  │       │                                 │
│  └────────────────┘  │       │                                 │
│  (16 bytes total)    │       │                                 │
│  All data on stack!  │       │                                 │
│                      │       │                                 │
└──────────────────────┘       └─────────────────────────────────┘

FIXED-SIZE ARRAYS:
- Size known at compile time
- Stored entirely on stack
- NO heap allocation
- Very fast access
- Cannot grow or shrink
```

---

## 3. KEY DIFFERENCES SUMMARY

```
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON vs RUST                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ASPECT           │  PYTHON              │  RUST                │
│  ────────────────┼──────────────────────┼──────────────────────┤
│  Assignment       │  Reference copy      │  Move (ownership     │
│                   │  (shared reference)  │   transfer)          │
│  ────────────────┼──────────────────────┼──────────────────────┤
│  Function calls   │  Pass reference to   │  Move, borrow, or    │
│                   │  object              │  copy (explicit)     │
│  ────────────────┼──────────────────────┼──────────────────────┤
│  Memory           │  Garbage collected   │  Compile-time        │
│  management       │  (ref counting + GC) │  (ownership rules)   │
│  ────────────────┼──────────────────────┼──────────────────────┤
│  Aliasing         │  Multiple refs to    │  Prevented by borrow │
│                   │  same object OK      │  checker             │
│  ────────────────┼──────────────────────┼──────────────────────┤
│  Copy cost        │  Explicit .copy()    │  Explicit .clone()   │
│                   │  needed              │  needed              │
│  ────────────────┼──────────────────────┼──────────────────────┤
│  Safety           │  Runtime errors      │  Compile-time safety │
│                   │  possible            │  guaranteed          │
│  ────────────────┼──────────────────────┼──────────────────────┤
│  Stack data       │  Only references     │  Can store entire    │
│                   │  stored on stack     │  arrays on stack     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. MEMORY ALLOCATION COMPARISON

```
PYTHON LIST OVERHEAD:
┌──────────────────────────────────────────────┐
│  List object: ~64 bytes                      │
│  + 8 bytes per element (pointer)             │
│  + Individual int objects (28 bytes each)    │
│                                              │
│  [[1,2],[3,4]] uses ~300+ bytes!             │
└──────────────────────────────────────────────┘

RUST Vec<Vec<i32>>:
┌──────────────────────────────────────────────┐
│  Outer Vec: 24 bytes (ptr, len, cap)        │
│  Inner Vecs: 24 bytes each × 2               │
│  i32 data: 4 bytes each × 4                  │
│                                              │
│  Total: ~88 bytes                            │
└──────────────────────────────────────────────┘

RUST [[i32; 2]; 2] (stack array):
┌──────────────────────────────────────────────┐
│  Stack allocation only: 16 bytes             │
│  No heap allocation, no overhead!            │
└──────────────────────────────────────────────┘
```

---

## 5. CALL BY VALUE VS CALL BY REFERENCE

```
CALL BY VALUE (copying):
┌────────────┐        ┌────────────┐
│ Original   │  copy  │   Copy     │
│  data: 5   │───────>│  data: 5   │
└────────────┘        └────────────┘
Modifying copy doesn't affect original

CALL BY REFERENCE (aliasing):
┌────────────┐        
│  Data: 5   │◄───────reference 1
│            │◄───────reference 2
└────────────┘        
Both references point to SAME data

PYTHON: "Call by object reference"
- Pass reference to object
- Mutable objects can be modified
- Immutable objects can't be changed

RUST: Explicit control
- Move: Transfer ownership (default)
- Borrow: Temporary reference (&, &mut)
- Copy: Duplicate data (requires Copy trait)
```

This comprehensive diagram shows how Python uses reference semantics with garbage collection, while Rust uses ownership and borrowing for memory safety without runtime overhead!

I'll create a comprehensive ASCII diagram showing how matrices work in Python and Rust, covering call by reference/value and stack/heap memory concepts.I've created a comprehensive ASCII diagram showing how matrices work in Python and Rust with detailed coverage of:

**Key Topics Covered:**

1. **Python Matrix Memory Model**
   - List of lists creation and heap allocation
   - Reference semantics (multiple variables pointing to same object)
   - Call by object reference in functions
   - NumPy arrays with contiguous memory

2. **Rust Matrix Memory Model**
   - Vec of Vecs with ownership
   - Move semantics (ownership transfer)
   - Borrowing rules (immutable & mutable references)
   - Clone for deep copying
   - Stack-allocated fixed-size arrays

3. **Stack vs Heap Memory**
   - Python: References on stack, objects on heap
   - Rust: Can choose stack or heap storage
   - Memory overhead comparisons

4. **Call by Value vs Call by Reference**
   - Python's "call by object reference" semantics
   - Rust's explicit move/borrow/copy mechanisms
   - How modifications propagate (or don't)

The diagrams show step-by-step memory layout changes as operations are performed, making it clear how each language handles memory differently!