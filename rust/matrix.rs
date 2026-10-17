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
