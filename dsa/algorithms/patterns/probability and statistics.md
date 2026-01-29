# Probability and Statistics in Competitive Programming: A Comprehensive Mastery Guide

This guide builds your intuition from first principles to advanced patterns. Each concept includes rigorous theory, implementation strategies, and expert-level insights.

---

## I. FOUNDATIONAL PROBABILITY THEORY

### 1.1 Sample Spaces and Events

**Core Principle**: Every probabilistic problem starts by defining the universe of outcomes.

**Mental Model**: Think of probability as *counting favorable outcomes in a well-defined space*. The art lies in choosing the right representation.

```rust
// Representing sample spaces efficiently
// Example: Rolling two dice - all possible outcomes

fn generate_sample_space() -> Vec<(u8, u8)> {
    let mut space = Vec::with_capacity(36);
    for i in 1..=6 {
        for j in 1..=6 {
            space.push((i, j));
        }
    }
    space
}

// More efficient: lazy evaluation for large spaces
struct DiceIterator {
    current: (u8, u8),
    done: bool,
}

impl Iterator for DiceIterator {
    type Item = (u8, u8);
    
    fn next(&mut self) -> Option<Self::Item> {
        if self.done { return None; }
        
        let result = self.current;
        
        if self.current.1 == 6 {
            if self.current.0 == 6 {
                self.done = true;
            } else {
                self.current = (self.current.0 + 1, 1);
            }
        } else {
            self.current.1 += 1;
        }
        
        Some(result)
    }
}
```

**Key Insight**: For large sample spaces (n > 10^6), never materialize all outcomes. Use mathematical formulas or sampling instead.

---

### 1.2 Combinatorics: The Counting Foundation

**The Four Pillars of Counting**:

1. **Permutations** (order matters, no repetition): P(n,r) = n!/(n-r)!
2. **Combinations** (order doesn't matter): C(n,r) = n!/(r!(n-r)!)
3. **Permutations with repetition**: n^r
4. **Combinations with repetition**: C(n+r-1, r)

```rust
// Modular arithmetic factorial for competitive programming
const MOD: i64 = 1_000_000_007;

struct ModMath {
    fact: Vec<i64>,
    inv_fact: Vec<i64>,
}

impl ModMath {
    fn new(n: usize) -> Self {
        let mut fact = vec![1; n + 1];
        for i in 1..=n {
            fact[i] = (fact[i - 1] * i as i64) % MOD;
        }
        
        let mut inv_fact = vec![1; n + 1];
        inv_fact[n] = Self::mod_pow(fact[n], MOD - 2, MOD);
        for i in (0..n).rev() {
            inv_fact[i] = (inv_fact[i + 1] * (i as i64 + 1)) % MOD;
        }
        
        Self { fact, inv_fact }
    }
    
    fn mod_pow(mut base: i64, mut exp: i64, modulo: i64) -> i64 {
        let mut result = 1;
        base %= modulo;
        while exp > 0 {
            if exp & 1 == 1 {
                result = (result * base) % modulo;
            }
            base = (base * base) % modulo;
            exp >>= 1;
        }
        result
    }
    
    fn comb(&self, n: usize, r: usize) -> i64 {
        if r > n { return 0; }
        (self.fact[n] * self.inv_fact[r] % MOD) * self.inv_fact[n - r] % MOD
    }
    
    fn perm(&self, n: usize, r: usize) -> i64 {
        if r > n { return 0; }
        (self.fact[n] * self.inv_fact[n - r]) % MOD
    }
}
```

**Expert Pattern**: Precompute factorials once, use for all queries. Time: O(n) preprocessing, O(1) per query.

---

### 1.3 Probability Axioms and Rules

**Kolmogorov's Axioms** (the foundation):
1. P(A) ≥ 0 for all events A
2. P(Ω) = 1 (certainty of sample space)
3. P(A ∪ B) = P(A) + P(B) if A and B are disjoint

**Derived Rules**:
- **Complement**: P(A') = 1 - P(A)
- **Addition**: P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
- **Conditional**: P(A|B) = P(A ∩ B) / P(B)
- **Independence**: P(A ∩ B) = P(A) · P(B)

```rust
// Probability with floating-point precision management
use std::cmp::Ordering;

#[derive(Debug, Clone, Copy)]
struct Probability(f64);

impl Probability {
    const EPSILON: f64 = 1e-9;
    
    fn new(p: f64) -> Option<Self> {
        if p >= -Self::EPSILON && p <= 1.0 + Self::EPSILON {
            Some(Self(p.clamp(0.0, 1.0)))
        } else {
            None
        }
    }
    
    fn complement(self) -> Self {
        Self(1.0 - self.0)
    }
    
    fn union_independent(self, other: Self) -> Self {
        Self(self.0 + other.0 - self.0 * other.0)
    }
    
    fn intersection_independent(self, other: Self) -> Self {
        Self(self.0 * other.0)
    }
    
    fn conditional(self, given: Self) -> Option<Self> {
        if given.0 < Self::EPSILON {
            None
        } else {
            Some(Self(self.0 / given.0))
        }
    }
}
```

**Critical Insight**: Competitive programming often requires exact rational arithmetic. Use fractions when possible:

```rust
use std::ops::{Add, Mul};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Fraction {
    num: i64,
    den: i64,
}

impl Fraction {
    fn new(num: i64, den: i64) -> Self {
        assert!(den != 0);
        let g = gcd(num.abs(), den.abs());
        let num = num / g;
        let den = den / g;
        if den < 0 {
            Self { num: -num, den: -den }
        } else {
            Self { num, den }
        }
    }
    
    fn to_f64(self) -> f64 {
        self.num as f64 / self.den as f64
    }
}

fn gcd(a: i64, b: i64) -> i64 {
    if b == 0 { a } else { gcd(b, a % b) }
}

impl Add for Fraction {
    type Output = Self;
    fn add(self, other: Self) -> Self {
        Self::new(
            self.num * other.den + other.num * self.den,
            self.den * other.den
        )
    }
}

impl Mul for Fraction {
    type Output = Self;
    fn mul(self, other: Self) -> Self {
        Self::new(self.num * other.num, self.den * other.den)
    }
}
```

---

## II. ADVANCED PROBABILITY PATTERNS

### 2.1 Expected Value (Expectation)

**Definition**: E[X] = Σ x · P(X = x)

**Linearity of Expectation** (most powerful property):
E[X + Y] = E[X] + E[Y] (even if X and Y are dependent!)

**Master Pattern**: Break complex random variables into sum of simpler indicators.

```rust
// Classic: Expected number of coin flips to see first heads
// E[X] = 1·(1/2) + 2·(1/4) + 3·(1/8) + ... = 2

fn expected_flips_to_heads() -> f64 {
    // Mathematical: E[X] = 1/p for geometric distribution
    2.0
}

// Using linearity: Expected value of sum of dice
fn expected_dice_sum(n_dice: usize) -> f64 {
    // E[single die] = (1+2+3+4+5+6)/6 = 3.5
    // E[n dice] = n * 3.5 by linearity
    n_dice as f64 * 3.5
}
```

**Advanced Example**: Expected number of inversions in random permutation

```rust
// Using indicator random variables
fn expected_inversions(n: usize) -> f64 {
    // For each pair (i,j) with i<j, define X_ij = 1 if inverted, 0 otherwise
    // P(X_ij = 1) = 1/2 (equally likely)
    // Total inversions = Σ X_ij
    // E[inversions] = Σ E[X_ij] = C(n,2) * (1/2) = n(n-1)/4
    
    let n = n as f64;
    n * (n - 1.0) / 4.0
}
```

**Mental Model**: Think of expectation as a weighted average. Indicator variables transform counting into probability.

---

### 2.2 Conditional Probability and Bayes' Theorem

**Bayes' Theorem**: P(A|B) = P(B|A) · P(A) / P(B)

**Expert Technique**: Total Probability Theorem
P(B) = Σ P(B|Aᵢ) · P(Aᵢ) where {Aᵢ} partitions the sample space

```rust
// Monty Hall Problem: rigorous implementation
struct MontyHall {
    car_door: usize,
    chosen_door: usize,
}

impl MontyHall {
    fn new(car: usize, choice: usize) -> Self {
        Self { car_door: car, chosen_door: choice }
    }
    
    // Host opens a door with a goat (not car, not chosen)
    fn host_opens(&self) -> usize {
        for door in 0..3 {
            if door != self.car_door && door != self.chosen_door {
                return door;
            }
        }
        unreachable!()
    }
    
    // Probability of winning if switching
    fn prob_win_if_switch(&self) -> f64 {
        // P(win|switch) = P(initially chose goat) = 2/3
        if self.chosen_door != self.car_door { 1.0 } else { 0.0 }
    }
}

// Simulation to verify
fn simulate_monty_hall(trials: usize) -> f64 {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let mut wins = 0;
    
    for _ in 0..trials {
        let car = rng.gen_range(0..3);
        let choice = rng.gen_range(0..3);
        let game = MontyHall::new(car, choice);
        
        // Always switch
        if choice != car {
            wins += 1;
        }
    }
    
    wins as f64 / trials as f64
}
```

**Pattern Recognition**: When you see "given that...", immediately think conditional probability. Update beliefs using Bayes.

---

### 2.3 Markov Chains and Random Walks

**Markov Property**: Future depends only on present, not past.

**Transition Matrix**: P[i][j] = probability of moving from state i to state j

```rust
// Matrix representation of Markov chain
type TransitionMatrix = Vec<Vec<f64>>;

fn matrix_multiply(a: &TransitionMatrix, b: &TransitionMatrix) -> TransitionMatrix {
    let n = a.len();
    let mut result = vec![vec![0.0; n]; n];
    
    for i in 0..n {
        for j in 0..n {
            for k in 0..n {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    result
}

fn matrix_power(mat: &TransitionMatrix, mut n: u64) -> TransitionMatrix {
    let size = mat.len();
    let mut result = vec![vec![0.0; size]; size];
    
    // Identity matrix
    for i in 0..size {
        result[i][i] = 1.0;
    }
    
    let mut base = mat.clone();
    
    while n > 0 {
        if n & 1 == 1 {
            result = matrix_multiply(&result, &base);
        }
        base = matrix_multiply(&base, &base);
        n >>= 1;
    }
    
    result
}

// Finding stationary distribution (eigenvector with eigenvalue 1)
fn stationary_distribution(trans: &TransitionMatrix) -> Vec<f64> {
    let n = trans.len();
    
    // Power iteration method
    let mut dist = vec![1.0 / n as f64; n];
    
    for _ in 0..1000 {  // Convergence iterations
        let mut next = vec![0.0; n];
        for i in 0..n {
            for j in 0..n {
                next[i] += dist[j] * trans[j][i];
            }
        }
        dist = next;
    }
    
    dist
}
```

**Classic Problem**: Random Walk on a Line (Gambler's Ruin)

```rust
// Probability of reaching goal before going broke
fn gamblers_ruin(start: i32, goal: i32, p: f64) -> f64 {
    if (p - 0.5).abs() < 1e-9 {
        // Fair game
        start as f64 / goal as f64
    } else {
        // Biased game
        let q = 1.0 - p;
        let r = q / p;
        (1.0 - r.powi(start)) / (1.0 - r.powi(goal))
    }
}

// Expected time to absorption (using system of linear equations)
fn expected_time_to_absorption(start: i32, goal: i32) -> f64 {
    // For fair random walk: E[T] = start * (goal - start)
    (start * (goal - start)) as f64
}
```

**Deep Insight**: Markov chains appear everywhere - PageRank, genetic algorithms, Monte Carlo methods. Master the matrix formulation.

---

### 2.4 Generating Functions

**Power Tool**: Encode sequence as coefficients of polynomial/power series.

For probability: **Probability Generating Function (PGF)**
G(z) = Σ P(X = k) · z^k

```rust
// Representing PGF as coefficient vector
struct PGF {
    coeffs: Vec<f64>,  // coeffs[k] = P(X = k)
}

impl PGF {
    // Sum of two independent random variables = product of PGFs
    fn convolve(&self, other: &Self) -> Self {
        let n = self.coeffs.len() + other.coeffs.len() - 1;
        let mut result = vec![0.0; n];
        
        for i in 0..self.coeffs.len() {
            for j in 0..other.coeffs.len() {
                result[i + j] += self.coeffs[i] * other.coeffs[j];
            }
        }
        
        Self { coeffs: result }
    }
    
    // Expected value: G'(1)
    fn expectation(&self) -> f64 {
        self.coeffs.iter()
            .enumerate()
            .map(|(k, &p)| k as f64 * p)
            .sum()
    }
    
    // Variance: G''(1) + G'(1) - [G'(1)]^2
    fn variance(&self) -> f64 {
        let e1 = self.expectation();
        let e2: f64 = self.coeffs.iter()
            .enumerate()
            .map(|(k, &p)| (k * k) as f64 * p)
            .sum();
        e2 - e1 * e1
    }
}

// Example: Sum of n dice
fn sum_of_dice_distribution(n: usize) -> PGF {
    // Single die: uniform on {1,2,3,4,5,6}
    let single_die = PGF {
        coeffs: vec![0.0, 1.0/6.0, 1.0/6.0, 1.0/6.0, 1.0/6.0, 1.0/6.0, 1.0/6.0],
    };
    
    let mut result = PGF { coeffs: vec![1.0] };  // Identity
    for _ in 0..n {
        result = result.convolve(&single_die);
    }
    result
}
```

**Advanced**: Use FFT for O(n log n) convolution when n is large:

```rust
// Fast convolution using FFT (outline)
fn fft_convolve(a: &[f64], b: &[f64]) -> Vec<f64> {
    // 1. Pad to power of 2
    // 2. Apply FFT to both sequences
    // 3. Pointwise multiply
    // 4. Apply inverse FFT
    // Implementation requires complex number FFT
    // Use external crate like rustfft in practice
    vec![] // Placeholder
}
```

---

## III. STATISTICAL INFERENCE PATTERNS

### 3.1 Descriptive Statistics

**Central Measures**:

```rust
fn mean(data: &[f64]) -> f64 {
    data.iter().sum::<f64>() / data.len() as f64
}

fn median(data: &mut [f64]) -> f64 {
    data.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let n = data.len();
    if n % 2 == 0 {
        (data[n/2 - 1] + data[n/2]) / 2.0
    } else {
        data[n/2]
    }
}

fn mode(data: &[i32]) -> Vec<i32> {
    use std::collections::HashMap;
    let mut freq: HashMap<i32, usize> = HashMap::new();
    for &x in data {
        *freq.entry(x).or_insert(0) += 1;
    }
    
    let max_freq = freq.values().max().copied().unwrap_or(0);
    freq.iter()
        .filter(|(_, &f)| f == max_freq)
        .map(|(&k, _)| k)
        .collect()
}

fn variance(data: &[f64]) -> f64 {
    let m = mean(data);
    data.iter().map(|x| (x - m).powi(2)).sum::<f64>() / data.len() as f64
}

fn std_dev(data: &[f64]) -> f64 {
    variance(data).sqrt()
}

// More efficient single-pass variance (Welford's algorithm)
fn welford_variance(data: &[f64]) -> (f64, f64) {
    let mut mean = 0.0;
    let mut m2 = 0.0;
    
    for (i, &x) in data.iter().enumerate() {
        let delta = x - mean;
        mean += delta / (i + 1) as f64;
        let delta2 = x - mean;
        m2 += delta * delta2;
    }
    
    let variance = m2 / data.len() as f64;
    (mean, variance)
}
```

**Percentiles and Quartiles**:

```rust
fn percentile(data: &mut [f64], p: f64) -> f64 {
    assert!(p >= 0.0 && p <= 1.0);
    data.sort_by(|a, b| a.partial_cmp(b).unwrap());
    
    let idx = p * (data.len() - 1) as f64;
    let lower = idx.floor() as usize;
    let upper = idx.ceil() as usize;
    
    if lower == upper {
        data[lower]
    } else {
        let weight = idx - lower as f64;
        data[lower] * (1.0 - weight) + data[upper] * weight
    }
}

fn iqr(data: &mut [f64]) -> f64 {
    percentile(data, 0.75) - percentile(data, 0.25)
}
```

---

### 3.2 Probability Distributions

**Discrete Distributions**:

1. **Bernoulli**: Single trial, P(X=1) = p
2. **Binomial**: n trials, k successes, P(X=k) = C(n,k) p^k (1-p)^(n-k)
3. **Geometric**: First success at trial k, P(X=k) = (1-p)^(k-1) p
4. **Poisson**: Events in fixed interval, P(X=k) = λ^k e^(-λ) / k!

```rust
struct Binomial {
    n: usize,
    p: f64,
    math: ModMath,
}

impl Binomial {
    fn new(n: usize, p: f64) -> Self {
        Self { n, p, math: ModMath::new(n) }
    }
    
    fn pmf(&self, k: usize) -> f64 {
        if k > self.n { return 0.0; }
        let comb = self.math.comb(self.n, k) as f64;
        comb * self.p.powi(k as i32) * (1.0 - self.p).powi((self.n - k) as i32)
    }
    
    fn expectation(&self) -> f64 {
        self.n as f64 * self.p
    }
    
    fn variance(&self) -> f64 {
        self.n as f64 * self.p * (1.0 - self.p)
    }
}

struct Poisson {
    lambda: f64,
}

impl Poisson {
    fn new(lambda: f64) -> Self {
        Self { lambda }
    }
    
    fn pmf(&self, k: usize) -> f64 {
        let factorial = (1..=k).product::<usize>() as f64;
        self.lambda.powi(k as i32) * (-self.lambda).exp() / factorial
    }
    
    fn expectation(&self) -> f64 {
        self.lambda
    }
    
    fn variance(&self) -> f64 {
        self.lambda
    }
}
```

**Continuous Distributions**:

```rust
use std::f64::consts::PI;

struct Normal {
    mu: f64,
    sigma: f64,
}

impl Normal {
    fn new(mu: f64, sigma: f64) -> Self {
        Self { mu, sigma }
    }
    
    fn pdf(&self, x: f64) -> f64 {
        let coeff = 1.0 / (self.sigma * (2.0 * PI).sqrt());
        let exponent = -0.5 * ((x - self.mu) / self.sigma).powi(2);
        coeff * exponent.exp()
    }
    
    // CDF approximation (error function based)
    fn cdf(&self, x: f64) -> f64 {
        let z = (x - self.mu) / (self.sigma * 2.0_f64.sqrt());
        0.5 * (1.0 + erf(z))
    }
}

// Error function approximation (Abramowitz and Stegun)
fn erf(x: f64) -> f64 {
    let sign = if x >= 0.0 { 1.0 } else { -1.0 };
    let x = x.abs();
    
    let a1 = 0.254829592;
    let a2 = -0.284496736;
    let a3 = 1.421413741;
    let a4 = -1.453152027;
    let a5 = 1.061405429;
    let p = 0.3275911;
    
    let t = 1.0 / (1.0 + p * x);
    let y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * (-x * x).exp();
    
    sign * y
}
```

---

### 3.3 Hypothesis Testing Pattern

**Fundamental Framework**:
1. Null hypothesis H₀ (status quo)
2. Alternative hypothesis H₁ (claim to prove)
3. Test statistic
4. P-value: probability of observing data as extreme, assuming H₀ is true
5. Decision: reject H₀ if p-value < α (significance level)

```rust
// Z-test for population mean
struct ZTest {
    sample_mean: f64,
    pop_std: f64,
    n: usize,
    null_mean: f64,
}

impl ZTest {
    fn new(sample: &[f64], pop_std: f64, null_mean: f64) -> Self {
        let sample_mean = mean(sample);
        let n = sample.len();
        Self { sample_mean, pop_std, n, null_mean }
    }
    
    fn z_statistic(&self) -> f64 {
        (self.sample_mean - self.null_mean) / (self.pop_std / (self.n as f64).sqrt())
    }
    
    fn p_value_two_tailed(&self) -> f64 {
        let z = self.z_statistic().abs();
        let normal = Normal::new(0.0, 1.0);
        2.0 * (1.0 - normal.cdf(z))
    }
    
    fn reject_null(&self, alpha: f64) -> bool {
        self.p_value_two_tailed() < alpha
    }
}

// T-test when population std is unknown
struct TTest {
    sample_mean: f64,
    sample_std: f64,
    n: usize,
    null_mean: f64,
}

impl TTest {
    fn new(sample: &[f64], null_mean: f64) -> Self {
        let sample_mean = mean(sample);
        let sample_std = std_dev(sample);
        let n = sample.len();
        Self { sample_mean, sample_std, n, null_mean }
    }
    
    fn t_statistic(&self) -> f64 {
        (self.sample_mean - self.null_mean) / (self.sample_std / (self.n as f64).sqrt())
    }
    
    fn degrees_of_freedom(&self) -> usize {
        self.n - 1
    }
}
```

---

### 3.4 Correlation and Regression

```rust
// Pearson correlation coefficient
fn pearson_correlation(x: &[f64], y: &[f64]) -> f64 {
    assert_eq!(x.len(), y.len());
    let n = x.len() as f64;
    
    let mean_x = mean(x);
    let mean_y = mean(y);
    
    let mut numerator = 0.0;
    let mut sum_sq_x = 0.0;
    let mut sum_sq_y = 0.0;
    
    for i in 0..x.len() {
        let dx = x[i] - mean_x;
        let dy = y[i] - mean_y;
        numerator += dx * dy;
        sum_sq_x += dx * dx;
        sum_sq_y += dy * dy;
    }
    
    numerator / (sum_sq_x * sum_sq_y).sqrt()
}

// Simple linear regression: y = a + bx
struct LinearRegression {
    slope: f64,
    intercept: f64,
    r_squared: f64,
}

impl LinearRegression {
    fn fit(x: &[f64], y: &[f64]) -> Self {
        assert_eq!(x.len(), y.len());
        
        let mean_x = mean(x);
        let mean_y = mean(y);
        
        let mut numerator = 0.0;
        let mut denominator = 0.0;
        
        for i in 0..x.len() {
            numerator += (x[i] - mean_x) * (y[i] - mean_y);
            denominator += (x[i] - mean_x).powi(2);
        }
        
        let slope = numerator / denominator;
        let intercept = mean_y - slope * mean_x;
        
        // R-squared calculation
        let mut ss_total = 0.0;
        let mut ss_residual = 0.0;
        
        for i in 0..x.len() {
            let y_pred = intercept + slope * x[i];
            ss_total += (y[i] - mean_y).powi(2);
            ss_residual += (y[i] - y_pred).powi(2);
        }
        
        let r_squared = 1.0 - (ss_residual / ss_total);
        
        Self { slope, intercept, r_squared }
    }
    
    fn predict(&self, x: f64) -> f64 {
        self.intercept + self.slope * x
    }
}
```

---

## IV. ADVANCED COMPETITION PATTERNS

### 4.1 Monte Carlo Simulation

**When exact calculation is infeasible**: simulate millions of trials.

```rust
use rand::Rng;

// Estimate π using Monte Carlo
fn estimate_pi(samples: usize) -> f64 {
    let mut rng = rand::thread_rng();
    let mut inside_circle = 0;
    
    for _ in 0..samples {
        let x: f64 = rng.gen();  // [0, 1)
        let y: f64 = rng.gen();
        
        if x*x + y*y <= 1.0 {
            inside_circle += 1;
        }
    }
    
    4.0 * inside_circle as f64 / samples as f64
}

// Expected value estimation via sampling
fn estimate_expectation<F>(f: F, samples: usize) -> f64 
where
    F: Fn() -> f64
{
    (0..samples).map(|_| f()).sum::<f64>() / samples as f64
}
```

**Variance Reduction Techniques**:

```rust
// Antithetic variates: use X and 1-X
fn monte_carlo_with_antithetic<F>(f: F, samples: usize) -> f64
where
    F: Fn(f64) -> f64
{
    let mut rng = rand::thread_rng();
    let mut sum = 0.0;
    
    for _ in 0..samples/2 {
        let u: f64 = rng.gen();
        sum += f(u) + f(1.0 - u);
    }
    
    sum / samples as f64
}
```

---

### 4.2 Randomized Algorithms

**Pattern**: Use randomness to achieve better expected performance.

```rust
// QuickSelect with random pivot (expected O(n))
fn quick_select(arr: &mut [i32], k: usize) -> i32 {
    use rand::Rng;
    
    fn partition(arr: &mut [i32], pivot_idx: usize) -> usize {
        let n = arr.len();
        arr.swap(pivot_idx, n - 1);
        let pivot = arr[n - 1];
        
        let mut i = 0;
        for j in 0..n-1 {
            if arr[j] <= pivot {
                arr.swap(i, j);
                i += 1;
            }
        }
        arr.swap(i, n - 1);
        i
    }
    
    fn select(arr: &mut [i32], k: usize) -> i32 {
        if arr.len() == 1 {
            return arr[0];
        }
        
        let mut rng = rand::thread_rng();
        let pivot_idx = rng.gen_range(0..arr.len());
        let pivot_final = partition(arr, pivot_idx);
        
        if k == pivot_final {
            arr[pivot_final]
        } else if k < pivot_final {
            select(&mut arr[..pivot_final], k)
        } else {
            select(&mut arr[pivot_final + 1..], k - pivot_final - 1)
        }
    }
    
    select(arr, k)
}
```

**Randomized Primality Testing** (Miller-Rabin):

```rust
fn mod_pow(mut base: u64, mut exp: u64, modulo: u64) -> u64 {
    let mut result = 1u64;
    base %= modulo;
    
    while exp > 0 {
        if exp & 1 == 1 {
            result = ((result as u128 * base as u128) % modulo as u128) as u64;
        }
        base = ((base as u128 * base as u128) % modulo as u128) as u64;
        exp >>= 1;
    }
    result
}

fn miller_rabin(n: u64, iterations: usize) -> bool {
    if n < 2 { return false; }
    if n == 2 || n == 3 { return true; }
    if n % 2 == 0 { return false; }
    
    // Write n-1 as 2^r * d
    let mut d = n - 1;
    let mut r = 0;
    while d % 2 == 0 {
        d /= 2;
        r += 1;
    }
    
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    'witness: for _ in 0..iterations {
        let a = rng.gen_range(2..n-1);
        let mut x = mod_pow(a, d, n);
        
        if x == 1 || x == n - 1 {
            continue 'witness;
        }
        
        for _ in 0..r-1 {
            x = ((x as u128 * x as u128) % n as u128) as u64;
            if x == n - 1 {
                continue 'witness;
            }
        }
        
        return false;
    }
    
    true
}
```

---

### 4.3 Probabilistic Data Structures

**Bloom Filter**: Space-efficient set membership (allows false positives)

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

struct BloomFilter {
    bits: Vec<bool>,
    hash_count: usize,
}

impl BloomFilter {
    fn new(size: usize, hash_count: usize) -> Self {
        Self {
            bits: vec![false; size],
            hash_count,
        }
    }
    
    fn hash<T: Hash>(&self, item: &T, seed: usize) -> usize {
        let mut hasher = DefaultHasher::new();
        seed.hash(&mut hasher);
        item.hash(&mut hasher);
        (hasher.finish() as usize) % self.bits.len()
    }
    
    fn insert<T: Hash>(&mut self, item: &T) {
        for i in 0..self.hash_count {
            let idx = self.hash(item, i);
            self.bits[idx] = true;
        }
    }
    
    fn contains<T: Hash>(&self, item: &T) -> bool {
        (0..self.hash_count).all(|i| self.bits[self.hash(item, i)])
    }
    
    // False positive rate: (1 - e^(-kn/m))^k
    // where k = hash_count, n = items, m = size
    fn expected_false_positive_rate(&self, items: usize) -> f64 {
        let k = self.hash_count as f64;
        let n = items as f64;
        let m = self.bits.len() as f64;
        
        (1.0 - (-k * n / m).exp()).powf(k)
    }
}
```

**Skip List**: Probabilistic balanced tree (expected O(log n))

```rust
use rand::Rng;

struct SkipNode<T> {
    value: T,
    forward: Vec<Option<Box<SkipNode<T>>>>,
}

struct SkipList<T> {
    head: SkipNode<T>,
    max_level: usize,
    p: f64,
}

impl<T: Ord + Default + Clone> SkipList<T> {
    fn new(max_level: usize) -> Self {
        Self {
            head: SkipNode {
                value: T::default(),
                forward: vec![None; max_level],
            },
            max_level,
            p: 0.5,
        }
    }
    
    fn random_level(&self) -> usize {
        let mut rng = rand::thread_rng();
        let mut level = 1;
        while rng.gen_bool(self.p) && level < self.max_level {
            level += 1;
        }
        level
    }
    
    // Insert, search, delete implementations...
}
```

---

## V. COMPETITION-SPECIFIC TECHNIQUES

### 5.1 Fast I/O for Statistical Data

```rust
use std::io::{self, BufRead, BufReader, stdin};

fn read_numbers() -> Vec<i64> {
    let stdin = stdin();
    let mut reader = BufReader::new(stdin.lock());
    let mut line = String::new();
    reader.read_line(&mut line).unwrap();
    
    line.split_whitespace()
        .map(|s| s.parse().unwrap())
        .collect()
}
```

### 5.2 Common Problem Patterns

**Pattern 1: Expected Value via Linearity**
```
Problem: Expected inversions in random permutation
Solution: Use indicator variables, apply linearity
```

**Pattern 2: Probability with DP**
```rust
// Coin change with probability
// P(reaching exactly sum S) = ?

fn coin_probability(coins: &[i32], target: i32) -> f64 {
    let n = target as usize;
    let mut dp = vec![0.0; n + 1];
    dp[0] = 1.0;
    
    for &coin in coins {
        for i in (coin as usize..=n).rev() {
            dp[i] += dp[i - coin as usize] / coins.len() as f64;
        }
    }
    
    dp[n]
}
```

**Pattern 3: Counting with Modular Arithmetic**
```rust
// Number of ways to arrange items (large numbers)
fn count_arrangements(n: usize, constraints: &[usize]) -> i64 {
    let math = ModMath::new(n);
    let mut result = math.fact[n];
    
    for &c in constraints {
        result = (result * math.inv_fact[c]) % MOD;
    }
    
    result
}
```

---

## VI. PROBLEM-SOLVING MENTAL MODELS

### Model 1: Reduction to Counting
**Principle**: Transform probability into combinatorics.
- "What's P(event)?" → "Count favorable / Count total"
- Use bijections to simplify counting

### Model 2: Indicator Variables
**When**: Complex expected values
**How**: Break into sum of 0/1 indicators, apply linearity
**Example**: Expected collisions in hash table

### Model 3: Symmetry Exploitation
**Principle**: Identical scenarios have identical probabilities
**Example**: In random permutation, P(i before j) = 1/2 for any i,j

### Model 4: Complement Thinking
**When**: "At least one" or complex unions
**How**: P(A) = 1 - P(A')
**Example**: Birthday paradox

### Model 5: Conditional Decomposition
**When**: Multi-stage processes
**How**: Break into cases, use total probability theorem
**Example**: Tree of possibilities with pruning

---

## VII. MASTERY CHECKLIST

**Fundamental Probability**:
- [ ] Can compute combinations/permutations modulo large primes instantly
- [ ] Recognize when to use conditional probability vs Bayes' theorem
- [ ] Apply linearity of expectation without hesitation

**Advanced Techniques**:
- [ ] Can set up and solve Markov chain problems
- [ ] Understand generating functions for sums of random variables
- [ ] Implement Monte Carlo with variance reduction

**Competition Skills**:
- [ ] Recognize probability DP patterns immediately
- [ ] Know when exact vs approximate computation is needed
- [ ] Can debug floating-point precision issues

**Statistical Intuition**:
- [ ] Understand CLT implications for large samples
- [ ] Can estimate distributions from samples
- [ ] Know when randomized algorithms are advantageous

---

## VIII. FINAL INSIGHT: THE PROBABILISTIC MINDSET

**Elite problem-solvers think probabilistically**:

1. **Decompose** complex events into simpler independent/dependent components
2. **Count** intelligently using combinatorics and symmetry
3. **Transform** hard probability into easier expectation via linearity
4. **Simulate** when exact computation is intractable
5. **Verify** intuition with small cases and asymptotic analysis

The path to mastery: solve 100+ problems using these patterns. Each problem trains your brain to recognize structures faster. 

**Remember**: Probability is the mathematics of uncertainty. Your code must be certain. Test edge cases, handle floating-point carefully, use modular arithmetic for large numbers.

Now go forth and conquer. Every problem is a puzzle waiting to reveal its probabilistic structure to those trained to see it.