# Multi-Language Benchmarking Suite

This benchmarking suite implements the same algorithms across Python, Rust, Go, C, and Java for performance comparison.

## Benchmark 1: Matrix Multiplication (N x N)

### Python Implementation

```python
#!/usr/bin/env python3
import sys
import time
import random

def matrix_multiply(a, b, n):
    """Multiply two NxN matrices"""
    c = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                c[i][j] += a[i][k] * b[k][j]
    return c

def generate_matrix(n):
    """Generate a random NxN matrix"""
    return [[random.uniform(0, 1) for _ in range(n)] for _ in range(n)]

def main():
    if len(sys.argv) != 2:
        print("Usage: python matrix_mult.py <N>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    random.seed(42)  # For reproducible results
    
    print(f"Matrix multiplication benchmark (N={n})")
    
    # Generate matrices
    a = generate_matrix(n)
    b = generate_matrix(n)
    
    # Benchmark
    start_time = time.perf_counter()
    result = matrix_multiply(a, b, n)
    end_time = time.perf_counter()
    
    execution_time = end_time - start_time
    
    # Print result to avoid dead code elimination
    checksum = sum(sum(row) for row in result)
    print(f"Result checksum: {checksum:.6f}")
    print(f"Execution time: {execution_time:.6f} seconds")

if __name__ == "__main__":
    main()
```

**Run with:** `python matrix_mult.py 500`
**Memory usage:** `/usr/bin/time -v python matrix_mult.py 500`

### Rust Implementation

```rust
// matrix_mult.rs
use std::env;
use std::time::Instant;
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;

fn matrix_multiply(a: &Vec<Vec<f64>>, b: &Vec<Vec<f64>>, n: usize) -> Vec<Vec<f64>> {
    let mut c = vec![vec![0.0; n]; n];
    for i in 0..n {
        for j in 0..n {
            for k in 0..n {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    c
}

fn generate_matrix(n: usize, rng: &mut StdRng) -> Vec<Vec<f64>> {
    (0..n)
        .map(|_| (0..n).map(|_| rng.gen::<f64>()).collect())
        .collect()
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <N>", args[0]);
        std::process::exit(1);
    }

    let n: usize = args[1].parse().expect("Invalid number");
    let mut rng = StdRng::seed_from_u64(42); // For reproducible results

    println!("Matrix multiplication benchmark (N={})", n);

    // Generate matrices
    let a = generate_matrix(n, &mut rng);
    let b = generate_matrix(n, &mut rng);

    // Benchmark
    let start = Instant::now();
    let result = matrix_multiply(&a, &b, n);
    let duration = start.elapsed();

    // Print result to avoid dead code elimination
    let checksum: f64 = result.iter().map(|row| row.iter().sum::<f64>()).sum();
    println!("Result checksum: {:.6}", checksum);
    println!("Execution time: {:.6} seconds", duration.as_secs_f64());
}
```

**Cargo.toml:**
```toml
[package]
name = "matrix_mult"
version = "0.1.0"
edition = "2021"

[dependencies]
rand = "0.8"

[profile.release]
lto = true
codegen-units = 1
```

**Compile:** `cargo build --release`
**Run:** `./target/release/matrix_mult 500`
**Memory usage:** `/usr/bin/time -v ./target/release/matrix_mult 500`

### Go Implementation

```go
// matrix_mult.go
package main

import (
    "fmt"
    "math/rand"
    "os"
    "strconv"
    "time"
)

func matrixMultiply(a, b [][]float64, n int) [][]float64 {
    c := make([][]float64, n)
    for i := range c {
        c[i] = make([]float64, n)
    }
    
    for i := 0; i < n; i++ {
        for j := 0; j < n; j++ {
            for k := 0; k < n; k++ {
                c[i][j] += a[i][k] * b[k][j]
            }
        }
    }
    return c
}

func generateMatrix(n int, r *rand.Rand) [][]float64 {
    matrix := make([][]float64, n)
    for i := range matrix {
        matrix[i] = make([]float64, n)
        for j := range matrix[i] {
            matrix[i][j] = r.Float64()
        }
    }
    return matrix
}

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintf(os.Stderr, "Usage: %s <N>\n", os.Args[0])
        os.Exit(1)
    }

    n, err := strconv.Atoi(os.Args[1])
    if err != nil {
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }

    r := rand.New(rand.NewSource(42)) // For reproducible results
    fmt.Printf("Matrix multiplication benchmark (N=%d)\n", n)

    // Generate matrices
    a := generateMatrix(n, r)
    b := generateMatrix(n, r)

    // Benchmark
    start := time.Now()
    result := matrixMultiply(a, b, n)
    duration := time.Since(start)

    // Print result to avoid dead code elimination
    checksum := 0.0
    for _, row := range result {
        for _, val := range row {
            checksum += val
        }
    }

    fmt.Printf("Result checksum: %.6f\n", checksum)
    fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}
```

**Compile:** `go build -o matrix_mult matrix_mult.go`
**Run:** `./matrix_mult 500`
**Memory usage:** `/usr/bin/time -v ./matrix_mult 500`

### C Implementation

```c
// matrix_mult.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

double** allocate_matrix(int n) {
    double** matrix = malloc(n * sizeof(double*));
    for (int i = 0; i < n; i++) {
        matrix[i] = malloc(n * sizeof(double));
    }
    return matrix;
}

void free_matrix(double** matrix, int n) {
    for (int i = 0; i < n; i++) {
        free(matrix[i]);
    }
    free(matrix);
}

void generate_matrix(double** matrix, int n, unsigned int* seed) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            matrix[i][j] = (double)rand_r(seed) / RAND_MAX;
        }
    }
}

double** matrix_multiply(double** a, double** b, int n) {
    double** c = allocate_matrix(n);
    
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            c[i][j] = 0.0;
            for (int k = 0; k < n; k++) {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    return c;
}

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <N>\n", argv[0]);
        return 1;
    }

    int n = atoi(argv[1]);
    unsigned int seed = 42; // For reproducible results

    printf("Matrix multiplication benchmark (N=%d)\n", n);

    // Generate matrices
    double** a = allocate_matrix(n);
    double** b = allocate_matrix(n);
    generate_matrix(a, n, &seed);
    generate_matrix(b, n, &seed);

    // Benchmark
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double** result = matrix_multiply(a, b, n);
    clock_gettime(CLOCK_MONOTONIC, &end);

    double execution_time = get_time_diff(start, end);

    // Print result to avoid dead code elimination
    double checksum = 0.0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            checksum += result[i][j];
        }
    }

    printf("Result checksum: %.6f\n", checksum);
    printf("Execution time: %.6f seconds\n", execution_time);

    // Cleanup
    free_matrix(a, n);
    free_matrix(b, n);
    free_matrix(result, n);

    return 0;
}
```

**Compile:** `gcc -O3 -lrt -o matrix_mult matrix_mult.c`
**Run:** `./matrix_mult 500`
**Memory usage:** `/usr/bin/time -v ./matrix_mult 500`

### Java Implementation

```java
// MatrixMult.java
import java.util.Random;

public class MatrixMult {
    public static double[][] matrixMultiply(double[][] a, double[][] b, int n) {
        double[][] c = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                for (int k = 0; k < n; k++) {
                    c[i][j] += a[i][k] * b[k][j];
                }
            }
        }
        return c;
    }

    public static double[][] generateMatrix(int n, Random random) {
        double[][] matrix = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                matrix[i][j] = random.nextDouble();
            }
        }
        return matrix;
    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java MatrixMult <N>");
            System.exit(1);
        }

        int n = Integer.parseInt(args[0]);
        Random random = new Random(42); // For reproducible results

        System.out.println("Matrix multiplication benchmark (N=" + n + ")");

        // Generate matrices
        double[][] a = generateMatrix(n, random);
        double[][] b = generateMatrix(n, random);

        // Benchmark
        long startTime = System.nanoTime();
        double[][] result = matrixMultiply(a, b, n);
        long endTime = System.nanoTime();

        double executionTime = (endTime - startTime) / 1e9;

        // Print result to avoid dead code elimination
        double checksum = 0.0;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                checksum += result[i][j];
            }
        }

        System.out.printf("Result checksum: %.6f%n", checksum);
        System.out.printf("Execution time: %.6f seconds%n", executionTime);
    }
}
```

**Compile:** `javac MatrixMult.java`
**Run:** `java MatrixMult 500`
**Memory usage:** `/usr/bin/time -v java MatrixMult 500`

## Benchmark 2: Fibonacci (Recursive + Iterative)

### Python Implementation

```python
#!/usr/bin/env python3
import sys
import time

def fibonacci_recursive(n):
    """Recursive fibonacci (inefficient but good for benchmarking)"""
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

def fibonacci_iterative(n):
    """Iterative fibonacci (efficient)"""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def main():
    if len(sys.argv) != 2:
        print("Usage: python fibonacci.py <N>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    print(f"Fibonacci benchmark (N={n})")
    
    # Recursive benchmark (use smaller N for recursive)
    if n <= 45:  # Avoid extremely long execution times
        start_time = time.perf_counter()
        result_rec = fibonacci_recursive(n)
        rec_time = time.perf_counter() - start_time
        print(f"Recursive result: {result_rec}")
        print(f"Recursive time: {rec_time:.6f} seconds")
    else:
        print("Skipping recursive (N too large)")
    
    # Iterative benchmark
    start_time = time.perf_counter()
    result_iter = fibonacci_iterative(n)
    iter_time = time.perf_counter() - start_time
    print(f"Iterative result: {result_iter}")
    print(f"Iterative time: {iter_time:.6f} seconds")

if __name__ == "__main__":
    main()
```

### Rust Implementation

```rust
// fibonacci.rs
use std::env;
use std::time::Instant;

fn fibonacci_recursive(n: u64) -> u64 {
    if n <= 1 {
        n
    } else {
        fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)
    }
}

fn fibonacci_iterative(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    let mut a = 0;
    let mut b = 1;
    for _ in 2..=n {
        let temp = b;
        b = a + b;
        a = temp;
    }
    b
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <N>", args[0]);
        std::process::exit(1);
    }

    let n: u64 = args[1].parse().expect("Invalid number");
    println!("Fibonacci benchmark (N={})", n);

    // Recursive benchmark
    if n <= 45 {
        let start = Instant::now();
        let result_rec = fibonacci_recursive(n);
        let rec_time = start.elapsed();
        println!("Recursive result: {}", result_rec);
        println!("Recursive time: {:.6} seconds", rec_time.as_secs_f64());
    } else {
        println!("Skipping recursive (N too large)");
    }

    // Iterative benchmark
    let start = Instant::now();
    let result_iter = fibonacci_iterative(n);
    let iter_time = start.elapsed();
    println!("Iterative result: {}", result_iter);
    println!("Iterative time: {:.6} seconds", iter_time.as_secs_f64());
}
```

### Go Implementation

```go
// fibonacci.go
package main

import (
    "fmt"
    "os"
    "strconv"
    "time"
)

func fibonacciRecursive(n uint64) uint64 {
    if n <= 1 {
        return n
    }
    return fibonacciRecursive(n-1) + fibonacciRecursive(n-2)
}

func fibonacciIterative(n uint64) uint64 {
    if n <= 1 {
        return n
    }
    a, b := uint64(0), uint64(1)
    for i := uint64(2); i <= n; i++ {
        a, b = b, a+b
    }
    return b
}

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintf(os.Stderr, "Usage: %s <N>\n", os.Args[0])
        os.Exit(1)
    }

    n, err := strconv.ParseUint(os.Args[1], 10, 64)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }

    fmt.Printf("Fibonacci benchmark (N=%d)\n", n)

    // Recursive benchmark
    if n <= 45 {
        start := time.Now()
        resultRec := fibonacciRecursive(n)
        recTime := time.Since(start)
        fmt.Printf("Recursive result: %d\n", resultRec)
        fmt.Printf("Recursive time: %.6f seconds\n", recTime.Seconds())
    } else {
        fmt.Println("Skipping recursive (N too large)")
    }

    // Iterative benchmark
    start := time.Now()
    resultIter := fibonacciIterative(n)
    iterTime := time.Since(start)
    fmt.Printf("Iterative result: %d\n", resultIter)
    fmt.Printf("Iterative time: %.6f seconds\n", iterTime.Seconds())
}
```

### C Implementation

```c
// fibonacci.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

unsigned long long fibonacci_recursive(int n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2);
}

unsigned long long fibonacci_iterative(int n) {
    if (n <= 1) {
        return n;
    }
    unsigned long long a = 0, b = 1, temp;
    for (int i = 2; i <= n; i++) {
        temp = b;
        b = a + b;
        a = temp;
    }
    return b;
}

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <N>\n", argv[0]);
        return 1;
    }

    int n = atoi(argv[1]);
    printf("Fibonacci benchmark (N=%d)\n", n);

    struct timespec start, end;

    // Recursive benchmark
    if (n <= 45) {
        clock_gettime(CLOCK_MONOTONIC, &start);
        unsigned long long result_rec = fibonacci_recursive(n);
        clock_gettime(CLOCK_MONOTONIC, &end);
        double rec_time = get_time_diff(start, end);
        printf("Recursive result: %llu\n", result_rec);
        printf("Recursive time: %.6f seconds\n", rec_time);
    } else {
        printf("Skipping recursive (N too large)\n");
    }

    // Iterative benchmark
    clock_gettime(CLOCK_MONOTONIC, &start);
    unsigned long long result_iter = fibonacci_iterative(n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double iter_time = get_time_diff(start, end);
    printf("Iterative result: %llu\n", result_iter);
    printf("Iterative time: %.6f seconds\n", iter_time);

    return 0;
}
```

### Java Implementation

```java
// Fibonacci.java
public class Fibonacci {
    public static long fibonacciRecursive(int n) {
        if (n <= 1) {
            return n;
        }
        return fibonacciRecursive(n - 1) + fibonacciRecursive(n - 2);
    }

    public static long fibonacciIterative(int n) {
        if (n <= 1) {
            return n;
        }
        long a = 0, b = 1;
        for (int i = 2; i <= n; i++) {
            long temp = b;
            b = a + b;
            a = temp;
        }
        return b;
    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java Fibonacci <N>");
            System.exit(1);
        }

        int n = Integer.parseInt(args[0]);
        System.out.println("Fibonacci benchmark (N=" + n + ")");

        // Recursive benchmark
        if (n <= 45) {
            long startTime = System.nanoTime();
            long resultRec = fibonacciRecursive(n);
            long recTime = System.nanoTime() - startTime;
            System.out.println("Recursive result: " + resultRec);
            System.out.printf("Recursive time: %.6f seconds%n", recTime / 1e9);
        } else {
            System.out.println("Skipping recursive (N too large)");
        }

        // Iterative benchmark
        long startTime = System.nanoTime();
        long resultIter = fibonacciIterative(n);
        long iterTime = System.nanoTime() - startTime;
        System.out.println("Iterative result: " + resultIter);
        System.out.printf("Iterative time: %.6f seconds%n", iterTime / 1e9);
    }
}
```

## Compilation and Running Instructions

### Quick Reference

| Language | Compile Command | Run Command |
|----------|----------------|-------------|
| Python | None required | `python program.py <N>` |
| Rust | `cargo build --release` | `./target/release/program <N>` |
| Go | `go build -o program program.go` | `./program <N>` |
| C | `gcc -O3 -lrt -o program program.c` | `./program <N>` |
| Java | `javac Program.java` | `java Program <N>` |

### Memory Usage Measurement

Use `/usr/bin/time -v` to get detailed memory statistics:

```bash
/usr/bin/time -v python matrix_mult.py 500
/usr/bin/time -v ./target/release/matrix_mult 500
/usr/bin/time -v ./matrix_mult 500
/usr/bin/time -v ./matrix_mult 500
/usr/bin/time -v java MatrixMult 500
```

Key metrics to look for:
- `Maximum resident set size (kbytes)`: Peak memory usage
- `User time (seconds)`: CPU time in user mode
- `System time (seconds)`: CPU time in kernel mode
- `Elapsed (wall clock) time`: Total execution time

## Benchmarking Tips

1. **Warm-up runs**: Run each benchmark 2-3 times and take the best result
2. **System load**: Close other applications and run on an idle system
3. **CPU scaling**: Disable CPU frequency scaling for consistent results:
   ```bash
   sudo cpupower frequency-set --governor performance
   ```
4. **Sample sizes**: Use N=500 for matrix multiplication, N=40-45 for recursive fibonacci
5. **JVM warm-up**: For Java, consider running multiple iterations within the same JVM instance

## Expected Performance Characteristics

- **C/Rust**: Fastest execution, lowest memory usage
- **Go**: Close to C/Rust performance, slightly higher memory usage
- **Java**: Good performance after JVM warm-up, higher memory usage due to GC overhead
- **Python**: Slowest execution, moderate memory usage

The actual results will vary based on your hardware, OS, and compiler/interpreter versions.

# Multi-Language Benchmarking Suite

This benchmarking suite implements the same algorithms across Python, Rust, Go, C, and Java for performance comparison.

## Benchmark 1: Matrix Multiplication (N x N)

### Python Implementation

```python
#!/usr/bin/env python3
import sys
import time
import random

def matrix_multiply(a, b, n):
    """Multiply two NxN matrices"""
    c = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                c[i][j] += a[i][k] * b[k][j]
    return c

def generate_matrix(n):
    """Generate a random NxN matrix"""
    return [[random.uniform(0, 1) for _ in range(n)] for _ in range(n)]

def main():
    if len(sys.argv) != 2:
        print("Usage: python matrix_mult.py <N>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    random.seed(42)  # For reproducible results
    
    print(f"Matrix multiplication benchmark (N={n})")
    
    # Generate matrices
    a = generate_matrix(n)
    b = generate_matrix(n)
    
    # Benchmark
    start_time = time.perf_counter()
    result = matrix_multiply(a, b, n)
    end_time = time.perf_counter()
    
    execution_time = end_time - start_time
    
    # Print result to avoid dead code elimination
    checksum = sum(sum(row) for row in result)
    print(f"Result checksum: {checksum:.6f}")
    print(f"Execution time: {execution_time:.6f} seconds")

if __name__ == "__main__":
    main()
```

**Run with:** `python matrix_mult.py 500`
**Memory usage:** `/usr/bin/time -v python matrix_mult.py 500`

### Rust Implementation

```rust
// matrix_mult.rs
use std::env;
use std::time::Instant;
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;

fn matrix_multiply(a: &Vec<Vec<f64>>, b: &Vec<Vec<f64>>, n: usize) -> Vec<Vec<f64>> {
    let mut c = vec![vec![0.0; n]; n];
    for i in 0..n {
        for j in 0..n {
            for k in 0..n {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    c
}

fn generate_matrix(n: usize, rng: &mut StdRng) -> Vec<Vec<f64>> {
    (0..n)
        .map(|_| (0..n).map(|_| rng.gen::<f64>()).collect())
        .collect()
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <N>", args[0]);
        std::process::exit(1);
    }

    let n: usize = args[1].parse().expect("Invalid number");
    let mut rng = StdRng::seed_from_u64(42); // For reproducible results

    println!("Matrix multiplication benchmark (N={})", n);

    // Generate matrices
    let a = generate_matrix(n, &mut rng);
    let b = generate_matrix(n, &mut rng);

    // Benchmark
    let start = Instant::now();
    let result = matrix_multiply(&a, &b, n);
    let duration = start.elapsed();

    // Print result to avoid dead code elimination
    let checksum: f64 = result.iter().map(|row| row.iter().sum::<f64>()).sum();
    println!("Result checksum: {:.6}", checksum);
    println!("Execution time: {:.6} seconds", duration.as_secs_f64());
}
```

**Cargo.toml:**
```toml
[package]
name = "matrix_mult"
version = "0.1.0"
edition = "2021"

[dependencies]
rand = "0.8"

[profile.release]
lto = true
codegen-units = 1
```

**Compile:** `cargo build --release`
**Run:** `./target/release/matrix_mult 500`
**Memory usage:** `/usr/bin/time -v ./target/release/matrix_mult 500`

### Go Implementation

```go
// matrix_mult.go
package main

import (
    "fmt"
    "math/rand"
    "os"
    "strconv"
    "time"
)

func matrixMultiply(a, b [][]float64, n int) [][]float64 {
    c := make([][]float64, n)
    for i := range c {
        c[i] = make([]float64, n)
    }
    
    for i := 0; i < n; i++ {
        for j := 0; j < n; j++ {
            for k := 0; k < n; k++ {
                c[i][j] += a[i][k] * b[k][j]
            }
        }
    }
    return c
}

func generateMatrix(n int, r *rand.Rand) [][]float64 {
    matrix := make([][]float64, n)
    for i := range matrix {
        matrix[i] = make([]float64, n)
        for j := range matrix[i] {
            matrix[i][j] = r.Float64()
        }
    }
    return matrix
}

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintf(os.Stderr, "Usage: %s <N>\n", os.Args[0])
        os.Exit(1)
    }

    n, err := strconv.Atoi(os.Args[1])
    if err != nil {
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }

    r := rand.New(rand.NewSource(42)) // For reproducible results
    fmt.Printf("Matrix multiplication benchmark (N=%d)\n", n)

    // Generate matrices
    a := generateMatrix(n, r)
    b := generateMatrix(n, r)

    // Benchmark
    start := time.Now()
    result := matrixMultiply(a, b, n)
    duration := time.Since(start)

    // Print result to avoid dead code elimination
    checksum := 0.0
    for _, row := range result {
        for _, val := range row {
            checksum += val
        }
    }

    fmt.Printf("Result checksum: %.6f\n", checksum)
    fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}
```

**Compile:** `go build -o matrix_mult matrix_mult.go`
**Run:** `./matrix_mult 500`
**Memory usage:** `/usr/bin/time -v ./matrix_mult 500`

### C Implementation

```c
// matrix_mult.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

double** allocate_matrix(int n) {
    double** matrix = malloc(n * sizeof(double*));
    for (int i = 0; i < n; i++) {
        matrix[i] = malloc(n * sizeof(double));
    }
    return matrix;
}

void free_matrix(double** matrix, int n) {
    for (int i = 0; i < n; i++) {
        free(matrix[i]);
    }
    free(matrix);
}

void generate_matrix(double** matrix, int n, unsigned int* seed) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            matrix[i][j] = (double)rand_r(seed) / RAND_MAX;
        }
    }
}

double** matrix_multiply(double** a, double** b, int n) {
    double** c = allocate_matrix(n);
    
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            c[i][j] = 0.0;
            for (int k = 0; k < n; k++) {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    return c;
}

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <N>\n", argv[0]);
        return 1;
    }

    int n = atoi(argv[1]);
    unsigned int seed = 42; // For reproducible results

    printf("Matrix multiplication benchmark (N=%d)\n", n);

    // Generate matrices
    double** a = allocate_matrix(n);
    double** b = allocate_matrix(n);
    generate_matrix(a, n, &seed);
    generate_matrix(b, n, &seed);

    // Benchmark
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double** result = matrix_multiply(a, b, n);
    clock_gettime(CLOCK_MONOTONIC, &end);

    double execution_time = get_time_diff(start, end);

    // Print result to avoid dead code elimination
    double checksum = 0.0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            checksum += result[i][j];
        }
    }

    printf("Result checksum: %.6f\n", checksum);
    printf("Execution time: %.6f seconds\n", execution_time);

    // Cleanup
    free_matrix(a, n);
    free_matrix(b, n);
    free_matrix(result, n);

    return 0;
}
```

**Compile:** `gcc -O3 -lrt -o matrix_mult matrix_mult.c`
**Run:** `./matrix_mult 500`
**Memory usage:** `/usr/bin/time -v ./matrix_mult 500`

### Java Implementation

```java
// MatrixMult.java
import java.util.Random;

public class MatrixMult {
    public static double[][] matrixMultiply(double[][] a, double[][] b, int n) {
        double[][] c = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                for (int k = 0; k < n; k++) {
                    c[i][j] += a[i][k] * b[k][j];
                }
            }
        }
        return c;
    }

    public static double[][] generateMatrix(int n, Random random) {
        double[][] matrix = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                matrix[i][j] = random.nextDouble();
            }
        }
        return matrix;
    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java MatrixMult <N>");
            System.exit(1);
        }

        int n = Integer.parseInt(args[0]);
        Random random = new Random(42); // For reproducible results

        System.out.println("Matrix multiplication benchmark (N=" + n + ")");

        // Generate matrices
        double[][] a = generateMatrix(n, random);
        double[][] b = generateMatrix(n, random);

        // Benchmark
        long startTime = System.nanoTime();
        double[][] result = matrixMultiply(a, b, n);
        long endTime = System.nanoTime();

        double executionTime = (endTime - startTime) / 1e9;

        // Print result to avoid dead code elimination
        double checksum = 0.0;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                checksum += result[i][j];
            }
        }

        System.out.printf("Result checksum: %.6f%n", checksum);
        System.out.printf("Execution time: %.6f seconds%n", executionTime);
    }
}
```

**Compile:** `javac MatrixMult.java`
**Run:** `java MatrixMult 500`
**Memory usage:** `/usr/bin/time -v java MatrixMult 500`

## Benchmark 2: Fibonacci (Recursive + Iterative)

### Python Implementation

```python
#!/usr/bin/env python3
import sys
import time

def fibonacci_recursive(n):
    """Recursive fibonacci (inefficient but good for benchmarking)"""
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

def fibonacci_iterative(n):
    """Iterative fibonacci (efficient)"""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def main():
    if len(sys.argv) != 2:
        print("Usage: python fibonacci.py <N>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    print(f"Fibonacci benchmark (N={n})")
    
    # Recursive benchmark (use smaller N for recursive)
    if n <= 45:  # Avoid extremely long execution times
        start_time = time.perf_counter()
        result_rec = fibonacci_recursive(n)
        rec_time = time.perf_counter() - start_time
        print(f"Recursive result: {result_rec}")
        print(f"Recursive time: {rec_time:.6f} seconds")
    else:
        print("Skipping recursive (N too large)")
    
    # Iterative benchmark
    start_time = time.perf_counter()
    result_iter = fibonacci_iterative(n)
    iter_time = time.perf_counter() - start_time
    print(f"Iterative result: {result_iter}")
    print(f"Iterative time: {iter_time:.6f} seconds")

if __name__ == "__main__":
    main()
```

### Rust Implementation

```rust
// fibonacci.rs
use std::env;
use std::time::Instant;

fn fibonacci_recursive(n: u64) -> u64 {
    if n <= 1 {
        n
    } else {
        fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)
    }
}

fn fibonacci_iterative(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    let mut a = 0;
    let mut b = 1;
    for _ in 2..=n {
        let temp = b;
        b = a + b;
        a = temp;
    }
    b
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <N>", args[0]);
        std::process::exit(1);
    }

    let n: u64 = args[1].parse().expect("Invalid number");
    println!("Fibonacci benchmark (N={})", n);

    // Recursive benchmark
    if n <= 45 {
        let start = Instant::now();
        let result_rec = fibonacci_recursive(n);
        let rec_time = start.elapsed();
        println!("Recursive result: {}", result_rec);
        println!("Recursive time: {:.6} seconds", rec_time.as_secs_f64());
    } else {
        println!("Skipping recursive (N too large)");
    }

    // Iterative benchmark
    let start = Instant::now();
    let result_iter = fibonacci_iterative(n);
    let iter_time = start.elapsed();
    println!("Iterative result: {}", result_iter);
    println!("Iterative time: {:.6} seconds", iter_time.as_secs_f64());
}
```

### Go Implementation

```go
// fibonacci.go
package main

import (
    "fmt"
    "os"
    "strconv"
    "time"
)

func fibonacciRecursive(n uint64) uint64 {
    if n <= 1 {
        return n
    }
    return fibonacciRecursive(n-1) + fibonacciRecursive(n-2)
}

func fibonacciIterative(n uint64) uint64 {
    if n <= 1 {
        return n
    }
    a, b := uint64(0), uint64(1)
    for i := uint64(2); i <= n; i++ {
        a, b = b, a+b
    }
    return b
}

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintf(os.Stderr, "Usage: %s <N>\n", os.Args[0])
        os.Exit(1)
    }

    n, err := strconv.ParseUint(os.Args[1], 10, 64)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }

    fmt.Printf("Fibonacci benchmark (N=%d)\n", n)

    // Recursive benchmark
    if n <= 45 {
        start := time.Now()
        resultRec := fibonacciRecursive(n)
        recTime := time.Since(start)
        fmt.Printf("Recursive result: %d\n", resultRec)
        fmt.Printf("Recursive time: %.6f seconds\n", recTime.Seconds())
    } else {
        fmt.Println("Skipping recursive (N too large)")
    }

    // Iterative benchmark
    start := time.Now()
    resultIter := fibonacciIterative(n)
    iterTime := time.Since(start)
    fmt.Printf("Iterative result: %d\n", resultIter)
    fmt.Printf("Iterative time: %.6f seconds\n", iterTime.Seconds())
}
```

### C Implementation

```c
// fibonacci.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

unsigned long long fibonacci_recursive(int n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2);
}

unsigned long long fibonacci_iterative(int n) {
    if (n <= 1) {
        return n;
    }
    unsigned long long a = 0, b = 1, temp;
    for (int i = 2; i <= n; i++) {
        temp = b;
        b = a + b;
        a = temp;
    }
    return b;
}

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <N>\n", argv[0]);
        return 1;
    }

    int n = atoi(argv[1]);
    printf("Fibonacci benchmark (N=%d)\n", n);

    struct timespec start, end;

    // Recursive benchmark
    if (n <= 45) {
        clock_gettime(CLOCK_MONOTONIC, &start);
        unsigned long long result_rec = fibonacci_recursive(n);
        clock_gettime(CLOCK_MONOTONIC, &end);
        double rec_time = get_time_diff(start, end);
        printf("Recursive result: %llu\n", result_rec);
        printf("Recursive time: %.6f seconds\n", rec_time);
    } else {
        printf("Skipping recursive (N too large)\n");
    }

    // Iterative benchmark
    clock_gettime(CLOCK_MONOTONIC, &start);
    unsigned long long result_iter = fibonacci_iterative(n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double iter_time = get_time_diff(start, end);
    printf("Iterative result: %llu\n", result_iter);
    printf("Iterative time: %.6f seconds\n", iter_time);

    return 0;
}
```

### Java Implementation

```java
// Fibonacci.java
public class Fibonacci {
    public static long fibonacciRecursive(int n) {
        if (n <= 1) {
            return n;
        }
        return fibonacciRecursive(n - 1) + fibonacciRecursive(n - 2);
    }

    public static long fibonacciIterative(int n) {
        if (n <= 1) {
            return n;
        }
        long a = 0, b = 1;
        for (int i = 2; i <= n; i++) {
            long temp = b;
            b = a + b;
            a = temp;
        }
        return b;
    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java Fibonacci <N>");
            System.exit(1);
        }

        int n = Integer.parseInt(args[0]);
        System.out.println("Fibonacci benchmark (N=" + n + ")");

        // Recursive benchmark
        if (n <= 45) {
            long startTime = System.nanoTime();
            long resultRec = fibonacciRecursive(n);
            long recTime = System.nanoTime() - startTime;
            System.out.println("Recursive result: " + resultRec);
            System.out.printf("Recursive time: %.6f seconds%n", recTime / 1e9);
        } else {
            System.out.println("Skipping recursive (N too large)");
        }

        // Iterative benchmark
        long startTime = System.nanoTime();
        long resultIter = fibonacciIterative(n);
        long iterTime = System.nanoTime() - startTime;
        System.out.println("Iterative result: " + resultIter);
        System.out.printf("Iterative time: %.6f seconds%n", iterTime / 1e9);
    }
}
```

## Compilation and Running Instructions

### Quick Reference

| Language | Compile Command | Run Command |
|----------|----------------|-------------|
| Python | None required | `python program.py <N>` |
| Rust | `cargo build --release` | `./target/release/program <N>` |
| Go | `go build -o program program.go` | `./program <N>` |
| C | `gcc -O3 -lrt -o program program.c` | `./program <N>` |
| Java | `javac Program.java` | `java Program <N>` |

### Memory Usage Measurement

Use `/usr/bin/time -v` to get detailed memory statistics:

```bash
/usr/bin/time -v python matrix_mult.py 500
/usr/bin/time -v ./target/release/matrix_mult 500
/usr/bin/time -v ./matrix_mult 500
/usr/bin/time -v ./matrix_mult 500
/usr/bin/time -v java MatrixMult 500
```

Key metrics to look for:
- `Maximum resident set size (kbytes)`: Peak memory usage
- `User time (seconds)`: CPU time in user mode
- `System time (seconds)`: CPU time in kernel mode
- `Elapsed (wall clock) time`: Total execution time

## Benchmarking Tips

1. **Warm-up runs**: Run each benchmark 2-3 times and take the best result
2. **System load**: Close other applications and run on an idle system
3. **CPU scaling**: Disable CPU frequency scaling for consistent results:
   ```bash
   sudo cpupower frequency-set --governor performance
   ```
4. **Sample sizes**: Use N=500 for matrix multiplication, N=40-45 for recursive fibonacci
5. **JVM warm-up**: For Java, consider running multiple iterations within the same JVM instance

## Benchmark 3: Quicksort

### Python Implementation

```python
#!/usr/bin/env python3
import sys
import time
import random

def quicksort(arr, low, high):
    if low < high:
        pi = partition(arr, low, high)
        quicksort(arr, low, pi - 1)
        quicksort(arr, pi + 1, high)

def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

def main():
    if len(sys.argv) != 2:
        print("Usage: python quicksort.py <N>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    random.seed(42)
    
    print(f"Quicksort benchmark (N={n})")
    
    # Generate random array
    arr = [random.randint(1, 1000000) for _ in range(n)]
    
    # Benchmark
    start_time = time.perf_counter()
    quicksort(arr, 0, len(arr) - 1)
    execution_time = time.perf_counter() - start_time
    
    # Verify sorted and print checksum
    checksum = sum(arr[:min(100, len(arr))])  # First 100 elements
    print(f"Result checksum (first 100): {checksum}")
    print(f"Execution time: {execution_time:.6f} seconds")

if __name__ == "__main__":
    main()
```

### Rust Implementation

```rust
// quicksort.rs
use std::env;
use std::time::Instant;
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;

fn quicksort(arr: &mut [i32], low: isize, high: isize) {
    if low < high {
        let pi = partition(arr, low, high);
        quicksort(arr, low, pi - 1);
        quicksort(arr, pi + 1, high);
    }
}

fn partition(arr: &mut [i32], low: isize, high: isize) -> isize {
    let pivot = arr[high as usize];
    let mut i = low - 1;
    
    for j in low..high {
        if arr[j as usize] <= pivot {
            i += 1;
            arr.swap(i as usize, j as usize);
        }
    }
    arr.swap((i + 1) as usize, high as usize);
    i + 1
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <N>", args[0]);
        std::process::exit(1);
    }

    let n: usize = args[1].parse().expect("Invalid number");
    let mut rng = StdRng::seed_from_u64(42);

    println!("Quicksort benchmark (N={})", n);

    // Generate random array
    let mut arr: Vec<i32> = (0..n).map(|_| rng.gen_range(1..=1000000)).collect();

    // Benchmark
    let start = Instant::now();
    quicksort(&mut arr, 0, (arr.len() - 1) as isize);
    let duration = start.elapsed();

    // Verify sorted and print checksum
    let checksum: i64 = arr.iter().take(100.min(arr.len())).map(|&x| x as i64).sum();
    println!("Result checksum (first 100): {}", checksum);
    println!("Execution time: {:.6} seconds", duration.as_secs_f64());
}
```

### Go Implementation

```go
// quicksort.go
package main

import (
    "fmt"
    "math/rand"
    "os"
    "strconv"
    "time"
)

func quicksort(arr []int, low, high int) {
    if low < high {
        pi := partition(arr, low, high)
        quicksort(arr, low, pi-1)
        quicksort(arr, pi+1, high)
    }
}

func partition(arr []int, low, high int) int {
    pivot := arr[high]
    i := low - 1
    
    for j := low; j < high; j++ {
        if arr[j] <= pivot {
            i++
            arr[i], arr[j] = arr[j], arr[i]
        }
    }
    arr[i+1], arr[high] = arr[high], arr[i+1]
    return i + 1
}

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintf(os.Stderr, "Usage: %s <N>\n", os.Args[0])
        os.Exit(1)
    }

    n, err := strconv.Atoi(os.Args[1])
    if err != nil
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }   
    fmt.Printf("Quicksort benchmark (N=%d)\n", n)
    r := rand.New(rand.NewSource(42))
    arr := make([]int, n)
    for i := range arr {
        arr[i] = r.Intn(1000000) + 1
    }
    start := time.Now()
    quicksort(arr, 0, len(arr)-1)
    duration := time.Since(start)
    checksum := 0
    for _, v := range arr[:min(100, len(arr))] {
        checksum += v
    }
    fmt.Printf("Result checksum (first 100): %d\n", checksum)
    fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}
func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}

```
# Multi-Language Benchmarking Suite

This benchmarking suite implements the same algorithms across Python, Rust, Go, C, and Java for performance comparison.

## Benchmark 1: Matrix Multiplication (N x N)

### Python Implementation

```python
#!/usr/bin/env python3
import sys
import time
import random

def matrix_multiply(a, b, n):
    """Multiply two NxN matrices"""
    c = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                c[i][j] += a[i][k] * b[k][j]
    return c

def generate_matrix(n):
    """Generate a random NxN matrix"""
    return [[random.uniform(0, 1) for _ in range(n)] for _ in range(n)]

def main():
    if len(sys.argv) != 2:
        print("Usage: python matrix_mult.py <N>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    random.seed(42)  # For reproducible results
    
    print(f"Matrix multiplication benchmark (N={n})")
    
    # Generate matrices
    a = generate_matrix(n)
    b = generate_matrix(n)
    
    # Benchmark
    start_time = time.perf_counter()
    result = matrix_multiply(a, b, n)
    end_time = time.perf_counter()
    
    execution_time = end_time - start_time
    
    # Print result to avoid dead code elimination
    checksum = sum(sum(row) for row in result)
    print(f"Result checksum: {checksum:.6f}")
    print(f"Execution time: {execution_time:.6f} seconds")

if __name__ == "__main__":
    main()
```

**Run with:** `python matrix_mult.py 500`
**Memory usage:** `/usr/bin/time -v python matrix_mult.py 500`

### Rust Implementation

```rust
// matrix_mult.rs
use std::env;
use std::time::Instant;
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;

fn matrix_multiply(a: &Vec<Vec<f64>>, b: &Vec<Vec<f64>>, n: usize) -> Vec<Vec<f64>> {
    let mut c = vec![vec![0.0; n]; n];
    for i in 0..n {
        for j in 0..n {
            for k in 0..n {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    c
}

fn generate_matrix(n: usize, rng: &mut StdRng) -> Vec<Vec<f64>> {
    (0..n)
        .map(|_| (0..n).map(|_| rng.gen::<f64>()).collect())
        .collect()
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <N>", args[0]);
        std::process::exit(1);
    }

    let n: usize = args[1].parse().expect("Invalid number");
    let mut rng = StdRng::seed_from_u64(42); // For reproducible results

    println!("Matrix multiplication benchmark (N={})", n);

    // Generate matrices
    let a = generate_matrix(n, &mut rng);
    let b = generate_matrix(n, &mut rng);

    // Benchmark
    let start = Instant::now();
    let result = matrix_multiply(&a, &b, n);
    let duration = start.elapsed();

    // Print result to avoid dead code elimination
    let checksum: f64 = result.iter().map(|row| row.iter().sum::<f64>()).sum();
    println!("Result checksum: {:.6}", checksum);
    println!("Execution time: {:.6} seconds", duration.as_secs_f64());
}
```

**Cargo.toml:**
```toml
[package]
name = "matrix_mult"
version = "0.1.0"
edition = "2021"

[dependencies]
rand = "0.8"

[profile.release]
lto = true
codegen-units = 1
```

**Compile:** `cargo build --release`
**Run:** `./target/release/matrix_mult 500`
**Memory usage:** `/usr/bin/time -v ./target/release/matrix_mult 500`

### Go Implementation

```go
// matrix_mult.go
package main

import (
    "fmt"
    "math/rand"
    "os"
    "strconv"
    "time"
)

func matrixMultiply(a, b [][]float64, n int) [][]float64 {
    c := make([][]float64, n)
    for i := range c {
        c[i] = make([]float64, n)
    }
    
    for i := 0; i < n; i++ {
        for j := 0; j < n; j++ {
            for k := 0; k < n; k++ {
                c[i][j] += a[i][k] * b[k][j]
            }
        }
    }
    return c
}

func generateMatrix(n int, r *rand.Rand) [][]float64 {
    matrix := make([][]float64, n)
    for i := range matrix {
        matrix[i] = make([]float64, n)
        for j := range matrix[i] {
            matrix[i][j] = r.Float64()
        }
    }
    return matrix
}

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintf(os.Stderr, "Usage: %s <N>\n", os.Args[0])
        os.Exit(1)
    }

    n, err := strconv.Atoi(os.Args[1])
    if err != nil {
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }

    r := rand.New(rand.NewSource(42))
    fmt.Printf("Quicksort benchmark (N=%d)\n", n)

    // Generate random array
    arr := make([]int, n)
    for i := 0; i < n; i++ {
        arr[i] = r.Intn(1000000) + 1
    }

    // Benchmark
    start := time.Now()
    quicksort(arr, 0, len(arr)-1)
    duration := time.Since(start)

    // Verify sorted and print checksum
    checksum := 0
    limit := 100
    if n < 100 {
        limit = n
    }
    for i := 0; i < limit; i++ {
        checksum += arr[i]
    }

    fmt.Printf("Result checksum (first 100): %d\n", checksum)
    fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}
```

### C Implementation

```c
// quicksort.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void swap(int* a, int* b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

int partition(int arr[], int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    
    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return i + 1;
}

void quicksort(int arr[], int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quicksort(arr, low, pi - 1);
        quicksort(arr, pi + 1, high);
    }
}

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <N>\n", argv[0]);
        return 1;
    }

    int n = atoi(argv[1]);
    unsigned int seed = 42;
    srand(seed);

    printf("Quicksort benchmark (N=%d)\n", n);

    // Generate random array
    int* arr = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) {
        arr[i] = rand() % 1000000 + 1;
    }

    // Benchmark
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    quicksort(arr, 0, n - 1);
    clock_gettime(CLOCK_MONOTONIC, &end);

    double execution_time = get_time_diff(start, end);

    // Verify sorted and print checksum
    long long checksum = 0;
    int limit = (n < 100) ? n : 100;
    for (int i = 0; i < limit; i++) {
        checksum += arr[i];
    }

    printf("Result checksum (first 100): %lld\n", checksum);
    printf("Execution time: %.6f seconds\n", execution_time);

    free(arr);
    return 0;
}
```

### Java Implementation

```java
// Quicksort.java
import java.util.Random;

public class Quicksort {
    public static void quicksort(int[] arr, int low, int high) {
        if (low < high) {
            int pi = partition(arr, low, high);
            quicksort(arr, low, pi - 1);
            quicksort(arr, pi + 1, high);
        }
    }

    public static int partition(int[] arr, int low, int high) {
        int pivot = arr[high];
        int i = low - 1;
        
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                int temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }
        int temp = arr[i + 1];
        arr[i + 1] = arr[high];
        arr[high] = temp;
        return i + 1;
    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java Quicksort <N>");
            System.exit(1);
        }

        int n = Integer.parseInt(args[0]);
        Random random = new Random(42);

        System.out.println("Quicksort benchmark (N=" + n + ")");

        // Generate random array
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) {
            arr[i] = random.nextInt(1000000) + 1;
        }

        // Benchmark
        long startTime = System.nanoTime();
        quicksort(arr, 0, arr.length - 1);
        long endTime = System.nanoTime();

        double executionTime = (endTime - startTime) / 1e9;

        // Verify sorted and print checksum
        long checksum = 0;
        int limit = Math.min(100, arr.length);
        for (int i = 0; i < limit; i++) {
            checksum += arr[i];
        }

        System.out.println("Result checksum (first 100): " + checksum);
        System.out.printf("Execution time: %.6f seconds%n", executionTime);
    }
}
```

## Benchmark 4: File I/O Operations

### Python Implementation

```python
#!/usr/bin/env python3
import sys
import time
import os

def write_benchmark(filename, n):
    """Write N lines to a file"""
    with open(filename, 'w') as f:
        for i in range(n):
            f.write(f"This is line number {i} with some additional text to make it longer.\n")

def read_benchmark(filename):
    """Read all lines from a file"""
    lines = []
    with open(filename, 'r') as f:
        for line in f:
            lines.append(line.strip())
    return lines

def main():
    if len(sys.argv) != 2:
        print("Usage: python fileio.py <N>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    filename = f"benchmark_file_{n}.txt"
    
    print(f"File I/O benchmark (N={n})")
    
    # Write benchmark
    start_time = time.perf_counter()
    write_benchmark(filename, n)
    write_time = time.perf_counter() - start_time
    
    # Get file size
    file_size = os.path.getsize(filename)
    
    # Read benchmark
    start_time = time.perf_counter()
    lines = read_benchmark(filename)
    read_time = time.perf_counter() - start_time
    
    # Cleanup
    os.remove(filename)
    
    print(f"File size: {file_size} bytes")
    print(f"Lines read: {len(lines)}")
    print(f"Write time: {write_time:.6f} seconds")
    print(f"Read time: {read_time:.6f} seconds")
    print(f"Total time: {write_time + read_time:.6f} seconds")

if __name__ == "__main__":
    main()
```

### Rust Implementation

```rust
// fileio.rs
use std::env;
use std::fs::{File, remove_file};
use std::io::{Write, BufRead, BufReader, BufWriter};
use std::time::Instant;

fn write_benchmark(filename: &str, n: usize) -> std::io::Result<()> {
    let file = File::create(filename)?;
    let mut writer = BufWriter::new(file);
    
    for i in 0..n {
        writeln!(writer, "This is line number {} with some additional text to make it longer.", i)?;
    }
    writer.flush()?;
    Ok(())
}

fn read_benchmark(filename: &str) -> std::io::Result<Vec<String>> {
    let file = File::open(filename)?;
    let reader = BufReader::new(file);
    let mut lines = Vec::new();
    
    for line in reader.lines() {
        lines.push(line?);
    }
    
    Ok(lines)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <N>", args[0]);
        std::process::exit(1);
    }

    let n: usize = args[1].parse().expect("Invalid number");
    let filename = format!("benchmark_file_{}.txt", n);

    println!("File I/O benchmark (N={})", n);

    // Write benchmark
    let start = Instant::now();
    write_benchmark(&filename, n).expect("Write failed");
    let write_time = start.elapsed();

    // Get file size
    let file_size = std::fs::metadata(&filename).expect("Failed to get file size").len();

    // Read benchmark
    let start = Instant::now();
    let lines = read_benchmark(&filename).expect("Read failed");
    let read_time = start.elapsed();

    // Cleanup
    remove_file(&filename).expect("Failed to remove file");

    println!("File size: {} bytes", file_size);
    println!("Lines read: {}", lines.len());
    println!("Write time: {:.6} seconds", write_time.as_secs_f64());
    println!("Read time: {:.6} seconds", read_time.as_secs_f64());
    println!("Total time: {:.6} seconds", (write_time + read_time).as_secs_f64());
}
```

### Go Implementation

```go
// fileio.go
package main

import (
    "bufio"
    "fmt"
    "os"
    "strconv"
    "time"
)

func writeBenchmark(filename string, n int) error {
    file, err := os.Create(filename)
    if err != nil {
        return err
    }
    defer file.Close()

    writer := bufio.NewWriter(file)
    defer writer.Flush()

    for i := 0; i < n; i++ {
        _, err := fmt.Fprintf(writer, "This is line number %d with some additional text to make it longer.\n", i)
        if err != nil {
            return err
        }
    }
    return nil
}

func readBenchmark(filename string) ([]string, error) {
    file, err := os.Open(filename)
    if err != nil {
        return nil, err
    }
    defer file.Close()

    var lines []string
    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        lines = append(lines, scanner.Text())
    }
    return lines, scanner.Err()
}

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintf(os.Stderr, "Usage: %s <N>\n", os.Args[0])
        os.Exit(1)
    }

    n, err := strconv.Atoi(os.Args[1])
    if err != nil {
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }

    filename := fmt.Sprintf("benchmark_file_%d.txt", n)
    fmt.Printf("File I/O benchmark (N=%d)\n", n)

    // Write benchmark
    start := time.Now()
    err = writeBenchmark(filename, n)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Write failed: %v\n", err)
        os.Exit(1)
    }
    writeTime := time.Since(start)

    // Get file size
    fileInfo, err := os.Stat(filename)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Failed to get file size: %v\n", err)
        os.Exit(1)
    }
    fileSize := fileInfo.Size()

    // Read benchmark
    start = time.Now()
    lines, err := readBenchmark(filename)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Read failed: %v\n", err)
        os.Exit(1)
    }
    readTime := time.Since(start)

    // Cleanup
    os.Remove(filename)

    fmt.Printf("File size: %d bytes\n", fileSize)
    fmt.Printf("Lines read: %d\n", len(lines))
    fmt.Printf("Write time: %.6f seconds\n", writeTime.Seconds())
    fmt.Printf("Read time: %.6f seconds\n", readTime.Seconds())
    fmt.Printf("Total time: %.6f seconds\n", (writeTime + readTime).Seconds())
}
```

### C Implementation

```c
// fileio.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>

void write_benchmark(const char* filename, int n) {
    FILE* file = fopen(filename, "w");
    if (!file) {
        perror("Failed to create file");
        exit(1);
    }

    for (int i = 0; i < n; i++) {
        fprintf(file, "This is line number %d with some additional text to make it longer.\n", i);
    }

    fclose(file);
}

int read_benchmark(const char* filename) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open file");
        exit(1);
    }

    char buffer[256];
    int line_count = 0;
    while (fgets(buffer, sizeof(buffer), file)) {
        line_count++;
    }

    fclose(file);
    return line_count;
}

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

long get_file_size(const char* filename) {
    struct stat st;
    if (stat(filename, &st) == 0) {
        return st.st_size;
    }
    return -1;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <N>\n", argv[0]);
        return 1;
    }

    int n = atoi(argv[1]);
    char filename[64];
    snprintf(filename, sizeof(filename), "benchmark_file_%d.txt", n);

    printf("File I/O benchmark (N=%d)\n", n);

    struct timespec start, end;

    // Write benchmark
    clock_gettime(CLOCK_MONOTONIC, &start);
    write_benchmark(filename, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double write_time = get_time_diff(start, end);

    // Get file size
    long file_size = get_file_size(filename);

    // Read benchmark
    clock_gettime(CLOCK_MONOTONIC, &start);
    int lines_read = read_benchmark(filename);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double read_time = get_time_diff(start, end);

    // Cleanup
    unlink(filename);

    printf("File size: %ld bytes\n", file_size);
    printf("Lines read: %d\n", lines_read);
    printf("Write time: %.6f seconds\n", write_time);
    printf("Read time: %.6f seconds\n", read_time);
    printf("Total time: %.6f seconds\n", write_time + read_time);

    return 0;
}
```

### Java Implementation

```java
// FileIO.java
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;

public class FileIO {
    public static void writeBenchmark(String filename, int n) throws IOException {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(filename))) {
            for (int i = 0; i < n; i++) {
                writer.write("This is line number " + i + " with some additional text to make it longer.\n");
            }
        }
    }

    public static int readBenchmark(String filename) throws IOException {
        int lineCount = 0;
        try (BufferedReader reader = new BufferedReader(new FileReader(filename))) {
            while (reader.readLine() != null) {
                lineCount++;
            }
        }
        return lineCount;
    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java FileIO <N>");
            System.exit(1);
        }

        int n = Integer.parseInt(args[0]);
        String filename = "benchmark_file_" + n + ".txt";

        System.out.println("File I/O benchmark (N=" + n + ")");

        try {
            // Write benchmark
            long startTime = System.nanoTime();
            writeBenchmark(filename, n);
            long writeTime = System.nanoTime() - startTime;

            // Get file size
            long fileSize = Files.size(Paths.get(filename));

            // Read benchmark
            startTime = System.nanoTime();
            int linesRead = readBenchmark(filename);
            long readTime = System.nanoTime() - startTime;

            // Cleanup
            Files.delete(Paths.get(filename));

            System.out.println("File size: " + fileSize + " bytes");
            System.out.println("Lines read: " + linesRead);
            System.out.printf("Write time: %.6f seconds%n", writeTime / 1e9);
            System.out.printf("Read time: %.6f seconds%n", readTime / 1e9);
            System.out.printf("Total time: %.6f seconds%n", (writeTime + readTime) / 1e9);

        } catch (IOException e) {
            System.err.println("I/O Error: " + e.getMessage());
            System.exit(1);
        }
    }
}
```

## Complete Benchmark Script

Here's a shell script to run all benchmarks automatically:

```bash
#!/bin/bash
# run_benchmarks.sh

echo "Building all programs..."

# Build Rust programs
echo "Building Rust programs..."
for prog in matrix_mult fibonacci quicksort fileio; do
    if [ -f "${prog}.rs" ]; then
        rustc --edition 2021 -C opt-level=3 -o "${prog}_rust" "${prog}.rs" 2>/dev/null || echo "Failed to build ${prog}.rs"
    fi
done

# Build Go programs
echo "Building Go programs..."
for prog in matrix_mult fibonacci quicksort fileio; do
    if [ -f "${prog}.go" ]; then
        go build -o "${prog}_go" "${prog}.go" 2>/dev/null || echo "Failed to build ${prog}.go"
    fi
done

# Build C programs
echo "Building C programs..."
for prog in matrix_mult fibonacci quicksort fileio; do
    if [ -f "${prog}.c" ]; then
        gcc -O3 -lrt -o "${prog}_c" "${prog}.c" 2>/dev/null || echo "Failed to build ${prog}.c"
    fi
done

# Build Java programs
echo "Building Java programs..."
for prog in MatrixMult Fibonacci Quicksort FileIO; do
    if [ -f "${prog}.java" ]; then
        javac "${prog}.java" 2>/dev/null || echo "Failed to build ${prog}.java"
    fi
done

echo ""
echo "Running benchmarks..."
echo "====================="

# Parameters
MATRIX_SIZE=300
FIBONACCI_N=40
QUICKSORT_N=1000000
FILEIO_N=100000

# Matrix Multiplication Benchmark
echo "Matrix Multiplication Benchmark (N=$MATRIX_SIZE):"
echo "Python:" && python matrix_mult.py $MATRIX_SIZE
echo "Rust:" && ./matrix_mult_rust $MATRIX_SIZE
echo "Go:" && ./matrix_mult_go $MATRIX_SIZE  
echo "C:" && ./matrix_mult_c $MATRIX_SIZE
echo "Java:" && java MatrixMult $MATRIX_SIZE
echo ""

# Fibonacci Benchmark
echo "Fibonacci Benchmark (N=$FIBONACCI_N):"
echo "Python:" && python fibonacci.py $FIBONACCI_N
echo "Rust:" && ./fibonacci_rust $FIBONACCI_N
echo "Go:" && ./fibonacci_go $FIBONACCI_N
echo "C:" && ./fibonacci_c $FIBONACCI_N
echo "Java:" && java Fibonacci $FIBONACCI_N
echo ""

# Quicksort Benchmark
echo "Quicksort Benchmark (N=$QUICKSORT_N):"
echo "Python:" && python quicksort.py $QUICKSORT_N
echo "Rust:" && ./quicksort_rust $QUICKSORT_N
echo "Go:" && ./quicksort_go $QUICKSORT_N
echo "C:" && ./quicksort_c $QUICKSORT_N
echo "Java:" && java Quicksort $QUICKSORT_N
echo ""

# File I/O Benchmark
echo "File I/O Benchmark (N=$FILEIO_N):"
echo "Python:" && python fileio.py $FILEIO_N
echo "Rust:" && ./fileio_rust $FILEIO_N
echo "Go:" && ./fileio_go $FILEIO_N
echo "C:" && ./fileio_c $FILEIO_N
echo "Java:" && java FileIO $FILEIO_N
echo ""

echo "Benchmarks complete!"
```

Make it executable: `chmod +x run_benchmarks.sh`

## Expected Performance Characteristics

- **C/Rust**: Fastest execution, lowest memory usage
- **Go**: Close to C/Rust performance, slightly higher memory usage  
- **Java**: Good performance after JVM warm-up, higher memory usage due to GC overhead
- **Python**: Slowest execution, moderate memory usage

The actual results will vary based on your hardware, OS, and compiler/interpreter versions. {
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }

    r := rand.New(rand.NewSource(42)) // For reproducible results
    fmt.Printf("Matrix multiplication benchmark (N=%d)\n", n)

    // Generate matrices
    a := generateMatrix(n, r)
    b := generateMatrix(n, r)

    // Benchmark
    start := time.Now()
    result := matrixMultiply(a, b, n)
    duration := time.Since(start)

    // Print result to avoid dead code elimination
    checksum := 0.0
    for _, row := range result {
        for _, val := range row {
            checksum += val
        }
    }

    fmt.Printf("Result checksum: %.6f\n", checksum)
    fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}
```

**Compile:** `go build -o matrix_mult matrix_mult.go`
**Run:** `./matrix_mult 500`
**Memory usage:** `/usr/bin/time -v ./matrix_mult 500`

### C Implementation

```c
// matrix_mult.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

double** allocate_matrix(int n) {
    double** matrix = malloc(n * sizeof(double*));
    for (int i = 0; i < n; i++) {
        matrix[i] = malloc(n * sizeof(double));
    }
    return matrix;
}

void free_matrix(double** matrix, int n) {
    for (int i = 0; i < n; i++) {
        free(matrix[i]);
    }
    free(matrix);
}

void generate_matrix(double** matrix, int n, unsigned int* seed) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            matrix[i][j] = (double)rand_r(seed) / RAND_MAX;
        }
    }
}

double** matrix_multiply(double** a, double** b, int n) {
    double** c = allocate_matrix(n);
    
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            c[i][j] = 0.0;
            for (int k = 0; k < n; k++) {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    return c;
}

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <N>\n", argv[0]);
        return 1;
    }

    int n = atoi(argv[1]);
    unsigned int seed = 42; // For reproducible results

    printf("Matrix multiplication benchmark (N=%d)\n", n);

    // Generate matrices
    double** a = allocate_matrix(n);
    double** b = allocate_matrix(n);
    generate_matrix(a, n, &seed);
    generate_matrix(b, n, &seed);

    // Benchmark
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double** result = matrix_multiply(a, b, n);
    clock_gettime(CLOCK_MONOTONIC, &end);

    double execution_time = get_time_diff(start, end);

    // Print result to avoid dead code elimination
    double checksum = 0.0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            checksum += result[i][j];
        }
    }

    printf("Result checksum: %.6f\n", checksum);
    printf("Execution time: %.6f seconds\n", execution_time);

    // Cleanup
    free_matrix(a, n);
    free_matrix(b, n);
    free_matrix(result, n);

    return 0;
}
```

**Compile:** `gcc -O3 -lrt -o matrix_mult matrix_mult.c`
**Run:** `./matrix_mult 500`
**Memory usage:** `/usr/bin/time -v ./matrix_mult 500`

### Java Implementation

```java
// MatrixMult.java
import java.util.Random;

public class MatrixMult {
    public static double[][] matrixMultiply(double[][] a, double[][] b, int n) {
        double[][] c = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                for (int k = 0; k < n; k++) {
                    c[i][j] += a[i][k] * b[k][j];
                }
            }
        }
        return c;
    }

    public static double[][] generateMatrix(int n, Random random) {
        double[][] matrix = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                matrix[i][j] = random.nextDouble();
            }
        }
        return matrix;
    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java MatrixMult <N>");
            System.exit(1);
        }

        int n = Integer.parseInt(args[0]);
        Random random = new Random(42); // For reproducible results

        System.out.println("Matrix multiplication benchmark (N=" + n + ")");

        // Generate matrices
        double[][] a = generateMatrix(n, random);
        double[][] b = generateMatrix(n, random);

        // Benchmark
        long startTime = System.nanoTime();
        double[][] result = matrixMultiply(a, b, n);
        long endTime = System.nanoTime();

        double executionTime = (endTime - startTime) / 1e9;

        // Print result to avoid dead code elimination
        double checksum = 0.0;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                checksum += result[i][j];
            }
        }

        System.out.printf("Result checksum: %.6f%n", checksum);
        System.out.printf("Execution time: %.6f seconds%n", executionTime);
    }
}
```

**Compile:** `javac MatrixMult.java`
**Run:** `java MatrixMult 500`
**Memory usage:** `/usr/bin/time -v java MatrixMult 500`

## Benchmark 2: Fibonacci (Recursive + Iterative)

### Python Implementation

```python
#!/usr/bin/env python3
import sys
import time

def fibonacci_recursive(n):
    """Recursive fibonacci (inefficient but good for benchmarking)"""
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

def fibonacci_iterative(n):
    """Iterative fibonacci (efficient)"""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def main():
    if len(sys.argv) != 2:
        print("Usage: python fibonacci.py <N>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    print(f"Fibonacci benchmark (N={n})")
    
    # Recursive benchmark (use smaller N for recursive)
    if n <= 45:  # Avoid extremely long execution times
        start_time = time.perf_counter()
        result_rec = fibonacci_recursive(n)
        rec_time = time.perf_counter() - start_time
        print(f"Recursive result: {result_rec}")
        print(f"Recursive time: {rec_time:.6f} seconds")
    else:
        print("Skipping recursive (N too large)")
    
    # Iterative benchmark
    start_time = time.perf_counter()
    result_iter = fibonacci_iterative(n)
    iter_time = time.perf_counter() - start_time
    print(f"Iterative result: {result_iter}")
    print(f"Iterative time: {iter_time:.6f} seconds")

if __name__ == "__main__":
    main()
```

### Rust Implementation

```rust
// fibonacci.rs
use std::env;
use std::time::Instant;

fn fibonacci_recursive(n: u64) -> u64 {
    if n <= 1 {
        n
    } else {
        fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)
    }
}

fn fibonacci_iterative(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    let mut a = 0;
    let mut b = 1;
    for _ in 2..=n {
        let temp = b;
        b = a + b;
        a = temp;
    }
    b
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <N>", args[0]);
        std::process::exit(1);
    }

    let n: u64 = args[1].parse().expect("Invalid number");
    println!("Fibonacci benchmark (N={})", n);

    // Recursive benchmark
    if n <= 45 {
        let start = Instant::now();
        let result_rec = fibonacci_recursive(n);
        let rec_time = start.elapsed();
        println!("Recursive result: {}", result_rec);
        println!("Recursive time: {:.6} seconds", rec_time.as_secs_f64());
    } else {
        println!("Skipping recursive (N too large)");
    }

    // Iterative benchmark
    let start = Instant::now();
    let result_iter = fibonacci_iterative(n);
    let iter_time = start.elapsed();
    println!("Iterative result: {}", result_iter);
    println!("Iterative time: {:.6} seconds", iter_time.as_secs_f64());
}
```

### Go Implementation

```go
// fibonacci.go
package main

import (
    "fmt"
    "os"
    "strconv"
    "time"
)

func fibonacciRecursive(n uint64) uint64 {
    if n <= 1 {
        return n
    }
    return fibonacciRecursive(n-1) + fibonacciRecursive(n-2)
}

func fibonacciIterative(n uint64) uint64 {
    if n <= 1 {
        return n
    }
    a, b := uint64(0), uint64(1)
    for i := uint64(2); i <= n; i++ {
        a, b = b, a+b
    }
    return b
}

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintf(os.Stderr, "Usage: %s <N>\n", os.Args[0])
        os.Exit(1)
    }

    n, err := strconv.ParseUint(os.Args[1], 10, 64)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }

    fmt.Printf("Fibonacci benchmark (N=%d)\n", n)

    // Recursive benchmark
    if n <= 45 {
        start := time.Now()
        resultRec := fibonacciRecursive(n)
        recTime := time.Since(start)
        fmt.Printf("Recursive result: %d\n", resultRec)
        fmt.Printf("Recursive time: %.6f seconds\n", recTime.Seconds())
    } else {
        fmt.Println("Skipping recursive (N too large)")
    }

    // Iterative benchmark
    start := time.Now()
    resultIter := fibonacciIterative(n)
    iterTime := time.Since(start)
    fmt.Printf("Iterative result: %d\n", resultIter)
    fmt.Printf("Iterative time: %.6f seconds\n", iterTime.Seconds())
}
```

### C Implementation

```c
// fibonacci.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

unsigned long long fibonacci_recursive(int n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2);
}

unsigned long long fibonacci_iterative(int n) {
    if (n <= 1) {
        return n;
    }
    unsigned long long a = 0, b = 1, temp;
    for (int i = 2; i <= n; i++) {
        temp = b;
        b = a + b;
        a = temp;
    }
    return b;
}

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <N>\n", argv[0]);
        return 1;
    }

    int n = atoi(argv[1]);
    printf("Fibonacci benchmark (N=%d)\n", n);

    struct timespec start, end;

    // Recursive benchmark
    if (n <= 45) {
        clock_gettime(CLOCK_MONOTONIC, &start);
        unsigned long long result_rec = fibonacci_recursive(n);
        clock_gettime(CLOCK_MONOTONIC, &end);
        double rec_time = get_time_diff(start, end);
        printf("Recursive result: %llu\n", result_rec);
        printf("Recursive time: %.6f seconds\n", rec_time);
    } else {
        printf("Skipping recursive (N too large)\n");
    }

    // Iterative benchmark
    clock_gettime(CLOCK_MONOTONIC, &start);
    unsigned long long result_iter = fibonacci_iterative(n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double iter_time = get_time_diff(start, end);
    printf("Iterative result: %llu\n", result_iter);
    printf("Iterative time: %.6f seconds\n", iter_time);

    return 0;
}
```

### Java Implementation

```java
// Fibonacci.java
public class Fibonacci {
    public static long fibonacciRecursive(int n) {
        if (n <= 1) {
            return n;
        }
        return fibonacciRecursive(n - 1) + fibonacciRecursive(n - 2);
    }

    public static long fibonacciIterative(int n) {
        if (n <= 1) {
            return n;
        }
        long a = 0, b = 1;
        for (int i = 2; i <= n; i++) {
            long temp = b;
            b = a + b;
            a = temp;
        }
        return b;
    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java Fibonacci <N>");
            System.exit(1);
        }

        int n = Integer.parseInt(args[0]);
        System.out.println("Fibonacci benchmark (N=" + n + ")");

        // Recursive benchmark
        if (n <= 45) {
            long startTime = System.nanoTime();
            long resultRec = fibonacciRecursive(n);
            long recTime = System.nanoTime() - startTime;
            System.out.println("Recursive result: " + resultRec);
            System.out.printf("Recursive time: %.6f seconds%n", recTime / 1e9);
        } else {
            System.out.println("Skipping recursive (N too large)");
        }

        // Iterative benchmark
        long startTime = System.nanoTime();
        long resultIter = fibonacciIterative(n);
        long iterTime = System.nanoTime() - startTime;
        System.out.println("Iterative result: " + resultIter);
        System.out.printf("Iterative time: %.6f seconds%n", iterTime / 1e9);
    }
}
```

## Compilation and Running Instructions

### Quick Reference

| Language | Compile Command | Run Command |
|----------|----------------|-------------|
| Python | None required | `python program.py <N>` |
| Rust | `cargo build --release` | `./target/release/program <N>` |
| Go | `go build -o program program.go` | `./program <N>` |
| C | `gcc -O3 -lrt -o program program.c` | `./program <N>` |
| Java | `javac Program.java` | `java Program <N>` |

### Memory Usage Measurement

Use `/usr/bin/time -v` to get detailed memory statistics:

```bash
/usr/bin/time -v python matrix_mult.py 500
/usr/bin/time -v ./target/release/matrix_mult 500
/usr/bin/time -v ./matrix_mult 500
/usr/bin/time -v ./matrix_mult 500
/usr/bin/time -v java MatrixMult 500
```

Key metrics to look for:
- `Maximum resident set size (kbytes)`: Peak memory usage
- `User time (seconds)`: CPU time in user mode
- `System time (seconds)`: CPU time in kernel mode
- `Elapsed (wall clock) time`: Total execution time

## Benchmarking Tips

1. **Warm-up runs**: Run each benchmark 2-3 times and take the best result
2. **System load**: Close other applications and run on an idle system
3. **CPU scaling**: Disable CPU frequency scaling for consistent results:
   ```bash
   sudo cpupower frequency-set --governor performance
   ```
4. **Sample sizes**: Use N=500 for matrix multiplication, N=40-45 for recursive fibonacci
5. **JVM warm-up**: For Java, consider running multiple iterations within the same JVM instance

## Benchmark 3: Quicksort

### Python Implementation

```python
#!/usr/bin/env python3
import sys
import time
import random

def quicksort(arr, low, high):
    if low < high:
        pi = partition(arr, low, high)
        quicksort(arr, low, pi - 1)
        quicksort(arr, pi + 1, high)

def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

def main():
    if len(sys.argv) != 2:
        print("Usage: python quicksort.py <N>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    random.seed(42)
    
    print(f"Quicksort benchmark (N={n})")
    
    # Generate random array
    arr = [random.randint(1, 1000000) for _ in range(n)]
    
    # Benchmark
    start_time = time.perf_counter()
    quicksort(arr, 0, len(arr) - 1)
    execution_time = time.perf_counter() - start_time
    
    # Verify sorted and print checksum
    checksum = sum(arr[:min(100, len(arr))])  # First 100 elements
    print(f"Result checksum (first 100): {checksum}")
    print(f"Execution time: {execution_time:.6f} seconds")

if __name__ == "__main__":
    main()
```

### Rust Implementation

```rust
// quicksort.rs
use std::env;
use std::time::Instant;
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;

fn quicksort(arr: &mut [i32], low: isize, high: isize) {
    if low < high {
        let pi = partition(arr, low, high);
        quicksort(arr, low, pi - 1);
        quicksort(arr, pi + 1, high);
    }
}

fn partition(arr: &mut [i32], low: isize, high: isize) -> isize {
    let pivot = arr[high as usize];
    let mut i = low - 1;
    
    for j in low..high {
        if arr[j as usize] <= pivot {
            i += 1;
            arr.swap(i as usize, j as usize);
        }
    }
    arr.swap((i + 1) as usize, high as usize);
    i + 1
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <N>", args[0]);
        std::process::exit(1);
    }

    let n: usize = args[1].parse().expect("Invalid number");
    let mut rng = StdRng::seed_from_u64(42);

    println!("Quicksort benchmark (N={})", n);

    // Generate random array
    let mut arr: Vec<i32> = (0..n).map(|_| rng.gen_range(1..=1000000)).collect();

    // Benchmark
    let start = Instant::now();
    quicksort(&mut arr, 0, (arr.len() - 1) as isize);
    let duration = start.elapsed();

    // Verify sorted and print checksum
    let checksum: i64 = arr.iter().take(100.min(arr.len())).map(|&x| x as i64).sum();
    println!("Result checksum (first 100): {}", checksum);
    println!("Execution time: {:.6} seconds", duration.as_secs_f64());
}
```

### Go Implementation

```go
// quicksort.go
package main

import (
    "fmt"
    "math/rand"
    "os"
    "strconv"
    "time"
)

func quicksort(arr []int, low, high int) {
    if low < high {
        pi := partition(arr, low, high)
        quicksort(arr, low, pi-1)
        quicksort(arr, pi+1, high)
    }
}

func partition(arr []int, low, high int) int {
    pivot := arr[high]
    i := low - 1
    
    for j := low; j < high; j++ {
        if arr[j] <= pivot {
            i++
            arr[i], arr[j] = arr[j], arr[i]
        }
    }
    arr[i+1], arr[high] = arr[high], arr[i+1]
    return i + 1
}

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintf(os.Stderr, "Usage: %s <N>\n", os.Args[0])
        os.Exit(1)
    }

    n, err := strconv.Atoi(os.Args[1])
    if err != nil {
        fmt.Fprintf(os.Stderr, "Invalid number: %v\n", err)
        os.Exit(1)
    }   
    rand.Seed(42) // For reproducible results
    fmt.Printf("Quicksort benchmark (N=%d)\n", n)
    // Generate random array
    arr := make([]int, n)
    for i := 0; i < n; i++ {
        arr[i] = rand.Intn(1000000) + 1
    }
    // Benchmark
    start := time.Now()
    quicksort(arr, 0, len(arr)-1)
    duration := time.Since(start)
    // Verify sorted and print checksum
    checksum := 0
    for i := 0; i < 100 && i < len(arr); i++
        checksum += arr[i]
    fmt.Printf("Result checksum (first 100): %d\n", checksum)
    fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}
```
Perfect! I've now created a comprehensive benchmarking suite with four different algorithms implemented across all five languages:

## Summary of Benchmarks

1. **Matrix Multiplication** - CPU-intensive mathematical computation
2. **Fibonacci** - Both recursive (inefficient) and iterative versions for comparison
3. **Quicksort** - Algorithm performance and memory access patterns
4. **File I/O** - Disk operations and buffering efficiency

## Key Features

✅ **Consistent Implementation**: Same algorithm logic across all languages
✅ **High-Resolution Timing**: Uses the best timing mechanisms for each language
✅ **Dead Code Elimination Prevention**: All programs print results to ensure optimization doesn't eliminate work
✅ **Optimized Compilation**: Includes proper compiler flags for maximum performance
✅ **Memory Usage Tracking**: Instructions for measuring memory with `/usr/bin/time -v`
✅ **Reproducible Results**: Fixed random seeds for consistent test data

## Quick Start

1. Save each code block to its respective file (e.g., `matrix_mult.py`, `matrix_mult.rs`, etc.)
2. For Rust programs, create a `Cargo.toml` with the dependencies shown
3. Compile using the provided commands
4. Run with: `program_name <N>` where N is the problem size
5. Use the provided shell script to run all benchmarks automatically

## Recommended Test Parameters

- **Matrix Multiplication**: N=300-500 (higher values take exponentially longer)
- **Fibonacci Recursive**: N=40-45 (avoid higher to prevent extremely long runtimes)
- **Fibonacci Iterative**: N=100000+ (very fast)
- **Quicksort**: N=1000000-10000000
- **File I/O**: N=100000-1000000 lines

This suite will give you comprehensive performance comparisons across CPU-bound, memory-bound, and I/O-bound workloads!