# Comprehensive Guide to Basic Mathematics

## 1. Number Systems and Fundamentals

### Natural Numbers (ℕ)
The counting numbers: 1, 2, 3, 4, ...

### Integers (ℤ)
All whole numbers including negatives: ..., -2, -1, 0, 1, 2, ...

### Rational Numbers (ℚ)
Numbers expressible as p/q where p, q ∈ ℤ and q ≠ 0

### Real Numbers (ℝ)
All rational and irrational numbers (√2, π, e, etc.)

---

## 2. Core Operations

### Addition & Subtraction
```
   347
 + 256
-------
   603

Carry mechanism:
   ¹¹
   347
 + 256
-------
   603
   
Step-by-step:
7 + 6 = 13 → write 3, carry 1
4 + 5 + 1 = 10 → write 0, carry 1
3 + 2 + 1 = 6
```

### Multiplication
```
Lattice Method Visualization:

    1   2
  ┌───┬───┐
3 │0 0│0 0│
  │ 3 │ 6 │
  ├───┼───┤
4 │0 0│0 0│
  │ 4 │ 8 │
  └───┴───┘

12 × 34 = 408

Standard Algorithm:
      12
    × 34
    ----
      48  (12 × 4)
    360   (12 × 30)
    ----
    408
```

### Division with Remainders
```
Long Division: 157 ÷ 12

     13 r 1
   --------
12 | 157
     12↓     (12 × 1 = 12)
     ---
      37
      36     (12 × 3 = 36)
      --
       1     (remainder)

Result: 13 remainder 1, or 13 + 1/12
```

---

## 3. Fractions

### Fraction Multiplication (Visual Proof)

**Why 1/2 × 1/2 = 1/4 = 0.25**

```
Area Model:

Original Unit Square (1 × 1 = 1):
┌─────────────────────┐
│                     │
│                     │
│        1.0          │
│                     │
│                     │
└─────────────────────┘

Take 1/2 horizontally:
┌──────────┬──────────┐
│          │          │
│   1/2    │   1/2    │
│          │          │
└──────────┴──────────┘

Now take 1/2 of that 1/2 vertically:
┌──────────┬──────────┐
│   1/4    │   1/4    │
├──────────┼──────────┤
│   1/4    │   1/4    │
└──────────┴──────────┘

Shaded region = 1/4 of total area
1/2 × 1/2 = 1/4 = 0.25
```

**General Rule: a/b × c/d = (a×c)/(b×d)**

```
Example: 2/3 × 3/4

Numerators: 2 × 3 = 6
Denominators: 3 × 4 = 12

Result: 6/12 = 1/2 (after simplification)
```

### Fraction Addition (Requires Common Denominator)

```
1/4 + 1/6 = ?

Step 1: Find LCM of denominators (4, 6)
        LCM(4, 6) = 12

Step 2: Convert to equivalent fractions
        1/4 = 3/12  (multiply by 3/3)
        1/6 = 2/12  (multiply by 2/2)

Step 3: Add numerators
        3/12 + 2/12 = 5/12

Visual:
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ ■ │ ■ │ ■ │   │   │   │   │   │   │   │   │   │  1/4 = 3/12
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ ● │ ● │   │   │   │   │   │   │   │   │   │   │  1/6 = 2/12
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ X │ X │ X │ X │ X │   │   │   │   │   │   │   │  Sum = 5/12
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
```

---

## 4. Decimals and Place Value

```
Number: 3,456.789

Position:  1000s 100s 10s 1s . 1/10 1/100 1/1000
           ───── ──── ─── ── ─ ──── ───── ──────
Value:       3     4    5   6 .  7     8      9

= 3×10³ + 4×10² + 5×10¹ + 6×10⁰ + 7×10⁻¹ + 8×10⁻² + 9×10⁻³
= 3000 + 400 + 50 + 6 + 0.7 + 0.08 + 0.009
```

### Decimal to Binary Conversion

```
Convert 13.625₁₀ to binary:

Integer part (13):
13 ÷ 2 = 6 remainder 1  ↑
 6 ÷ 2 = 3 remainder 0  │
 3 ÷ 2 = 1 remainder 1  │ Read
 1 ÷ 2 = 0 remainder 1  │ upward
                         
13₁₀ = 1101₂

Fractional part (0.625):
0.625 × 2 = 1.25  → 1  ↓
0.25  × 2 = 0.5   → 0  │ Read
0.5   × 2 = 1.0   → 1  │ downward
                       ↓
0.625₁₀ = 0.101₂

Result: 13.625₁₀ = 1101.101₂
```

---

## 5. Exponents and Powers

### Laws of Exponents
```
1. aᵐ × aⁿ = aᵐ⁺ⁿ
   Example: 2³ × 2² = 2⁵ = 32

2. aᵐ ÷ aⁿ = aᵐ⁻ⁿ
   Example: 5⁴ ÷ 5² = 5² = 25

3. (aᵐ)ⁿ = aᵐⁿ
   Example: (3²)³ = 3⁶ = 729

4. a⁰ = 1 (for a ≠ 0)

5. a⁻ⁿ = 1/aⁿ
   Example: 2⁻³ = 1/2³ = 1/8 = 0.125
```

### Visual Proof of a⁰ = 1
```
Pattern recognition:
2⁴ = 16
2³ = 8    (÷ 2)
2² = 4    (÷ 2)
2¹ = 2    (÷ 2)
2⁰ = ?    (÷ 2) → must be 1
```

---

## 6. Roots and Radicals

### Square Root Visualization
```
√16 = 4 because 4² = 16

Area representation:
┌────────────────┐
│ ■■■■■■■■■■■■■■ │
│ ■■■■■■■■■■■■■■ │
│ ■■■■■■■■■■■■■■ │  Area = 16 sq units
│ ■■■■■■■■■■■■■■ │  Side = 4 units
└────────────────┘
   4 units wide
```

### nth Root Definition
```
ⁿ√a = b  ⟺  bⁿ = a

Examples:
³√27 = 3  because 3³ = 27
⁴√16 = 2  because 2⁴ = 16
⁵√32 = 2  because 2⁵ = 32
```

---

## 7. Order of Operations (PEMDAS/BODMAS)

```
Hierarchy:
1. Parentheses/Brackets
2. Exponents/Orders
3. Multiplication & Division (left to right)
4. Addition & Subtraction (left to right)

Example: 2 + 3 × (4² - 2) ÷ 7

Step-by-step evaluation tree:
                    2 + 3 × (4² - 2) ÷ 7
                    │
        ┌───────────┴────────────┐
        │                        │
        2              3 × (4² - 2) ÷ 7
                       │
                ┌──────┴──────┐
                │             │
             3 × (16 - 2) ÷ 7
                │
             3 × 14 ÷ 7
                │
        ┌───────┴────────┐
        │                │
      42 ÷ 7 = 6
        │
    2 + 6 = 8

Final answer: 8
```

---

## 8. Percentages

### Percent as Parts per Hundred
```
25% = 25/100 = 1/4 = 0.25

Visual representation:
┌────┬────┬────┬────┬────┐
│ ■■ │ ■■ │ ■■ │ ■■ │ ■■ │
│ ■■ │ ■■ │ ■■ │ ■■ │ ■■ │  100 squares total
├────┼────┼────┼────┼────┤  25 shaded = 25%
│ ▓▓ │ ▓▓ │ ▓▓ │ ▓▓ │ ▓▓ │
│ ▓▓ │ ▓▓ │ ▓▓ │ ▓▓ │ ▓▓ │
└────┴────┴────┴────┴────┘
```

### Percentage Calculations
```
Find 30% of 200:
200 × 0.30 = 60

What percent is 45 of 180?
(45 ÷ 180) × 100 = 25%

80 is 40% of what number?
80 ÷ 0.40 = 200
```

---

## 9. Ratios and Proportions

### Ratio Representation
```
Ratio 3:2 means for every 3 units of A, there are 2 units of B

A: ■■■■■■■■■
B: ■■■■■■

If total = 15, then:
A = (3/5) × 15 = 9
B = (2/5) × 15 = 6
```

### Proportional Reasoning
```
If 3 apples cost $4.50, what do 7 apples cost?

Set up proportion:
3 apples     7 apples
─────────  = ─────────
 $4.50          x

Cross multiply:
3x = 7 × 4.50
3x = 31.50
x = $10.50
```

---

## 10. Prime Numbers and Factorization

### Sieve of Eratosthenes (Finding Primes)
```
Numbers 2-30, cross out multiples:

2  3  4  5  6  7  8  9  10
11 12 13 14 15 16 17 18 19 20
21 22 23 24 25 26 27 28 29 30

After sieving (X = composite):
2  3  X  5  X  7  X  X  X
11 X  13 X  X  X  17 X  19 X
X  X  23 X  X  X  X  X  29 X

Primes: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29
```

### Prime Factorization Tree
```
Factor 60:
           60
         /    \
       2       30
             /    \
           2       15
                 /    \
               3       5

60 = 2² × 3 × 5
```

---

## 11. Greatest Common Divisor (GCD) & Least Common Multiple (LCM)

### Euclidean Algorithm for GCD
```
Find GCD(48, 18):

48 = 18 × 2 + 12
18 = 12 × 1 + 6
12 = 6 × 2 + 0

GCD(48, 18) = 6 (last non-zero remainder)

Visualization:
48: ■■■■■■ ■■■■■■ ■■■■■■ ■■■■■■ ■■■■■■ ■■■■■■ ■■■■■■ ■■■■■■
18: ■■■■■■ ■■■■■■ ■■■■■■
GCD: ■■■■■■ (divides both evenly)
```

### LCM Calculation
```
LCM(12, 18) = (12 × 18) ÷ GCD(12, 18)
            = 216 ÷ 6
            = 36

Using prime factorization:
12 = 2² × 3
18 = 2 × 3²

LCM = 2² × 3² = 4 × 9 = 36
(take highest power of each prime)
```

---

## 12. Negative Numbers

### Number Line
```
        ←─────────────────────────────────→
  -5  -4  -3  -2  -1   0   1   2   3   4   5
   │   │   │   │   │   │   │   │   │   │   │

Addition: Move right
Subtraction: Move left
```

### Multiplication Rules
```
Sign Rules:
(+) × (+) = (+)    2 × 3 = 6
(+) × (-) = (-)    2 × (-3) = -6
(-) × (+) = (-)    (-2) × 3 = -6
(-) × (-) = (+)    (-2) × (-3) = 6

Intuition: (-1) × (-1) = 1
Think: "opposite of opposite"
```

---

## 13. Absolute Value

```
|x| = distance from 0 on number line

Examples:
|5| = 5
|-5| = 5
|0| = 0

Graph:
    │
  5 │     ╱│╲
  4 │    ╱ │ ╲
  3 │   ╱  │  ╲
  2 │  ╱   │   ╲
  1 │ ╱    │    ╲
    └─────────────────
       -5  0  5
```

---

## 14. Scientific Notation

```
Large number: 3,400,000 = 3.4 × 10⁶
Small number: 0.000056 = 5.6 × 10⁻⁵

General form: a × 10ⁿ where 1 ≤ |a| < 10

Multiplication:
(2 × 10³) × (3 × 10⁴) = (2 × 3) × 10³⁺⁴
                       = 6 × 10⁷
```

---

## 15. Basic Algebra Principles

### Solving Linear Equations
```
Solve: 3x + 7 = 22

Visual balance:
    ╭─────────────╮
    │   3x + 7    │
    ╰─────────────╯
          ║
    ╭─────────────╮
    │     22      │
    ╰─────────────╯

Steps:
3x + 7 = 22
3x = 22 - 7     (subtract 7 from both sides)
3x = 15
x = 15 ÷ 3      (divide both sides by 3)
x = 5
```

### Distributive Property
```
a(b + c) = ab + ac

Example: 3(x + 4) = 3x + 12

Visual:
┌─────────────────────┐
│  x      4           │
│ ┌───┬────────┐      │
│3│ 3x│   12   │      │
│ └───┴────────┘      │
└─────────────────────┘
Total area = 3x + 12
```

This guide covers the foundational mathematics from arithmetic through basic algebra, with visual proofs and diagrams where concepts benefit from geometric intuition.

# Advanced Mathematics for DSA and Computer Science

## 1. Modular Arithmetic

### Fundamental Properties
```
(a + b) mod m = ((a mod m) + (b mod m)) mod m
(a × b) mod m = ((a mod m) × (b mod m)) mod m
(a - b) mod m = ((a mod m) - (b mod m) + m) mod m

Key insight: Work with reduced values to prevent overflow
```

### Modular Exponentiation (Fast Power)
```cpp
// Compute (base^exp) % mod in O(log exp)
long long modpow(long long base, long long exp, long long mod) {
    long long result = 1;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) result = (result * base) % mod;
        base = (base * base) % mod;
        exp >>= 1;
    }
    return result;
}
```

**Binary Exponentiation Visualization:**
```
Compute 3^13 mod 1000:

13 in binary: 1101₂ = 8 + 4 + 1

3^13 = 3^8 × 3^4 × 3^1

Step-by-step:
Bit  Exp  Power       Result
1    1    3^1 = 3     result = 3
0    2    3^2 = 9     result = 3
1    4    3^4 = 81    result = 3×81 = 243
1    8    3^8 = 6561  result = 243×6561 mod 1000 = 683

Answer: 683
```

### Modular Multiplicative Inverse

**Extended Euclidean Algorithm:**
```
Find x such that (a × x) ≡ 1 (mod m)

Example: Inverse of 3 mod 11

GCD calculation with Bézout coefficients:
11 = 3 × 3 + 2     →  2 = 11 - 3×3
3  = 2 × 1 + 1     →  1 = 3 - 2×1
2  = 1 × 2 + 0     →  1 = 3 - (11 - 3×3)×1
                   →  1 = 3×4 - 11×1

Therefore: 3 × 4 ≡ 1 (mod 11)
Inverse of 3 mod 11 = 4

Verification: (3 × 4) mod 11 = 12 mod 11 = 1 ✓
```

**Application: Computing nCr mod p (Lucas' Theorem)**

---

## 2. Bit Manipulation Fundamentals

### Bitwise Operations Truth Tables
```
x   y  | x&y  x|y  x^y  ~x
--------|------------------
0   0  |  0    0    0    1
0   1  |  0    1    1    1
1   0  |  0    1    1    0
1   1  |  1    1    0    0
```

### Key Bit Tricks
```
Operation                 Code              Binary View
------------------------------------------------------------
Check if power of 2:      n & (n-1) == 0
  8:  1000                                  8:    1000
  7:  0111                                  7:    0111
  &:  0000 ✓                                &:    0000

Get rightmost set bit:    n & (-n)
  12: 0000 1100                             12:   0000 1100
 -12: 1111 0100 (2's complement)           -12:   1111 0100
  &:  0000 0100 = 4                         &:    0000 0100

Turn off rightmost bit:   n & (n-1)
  10: 0000 1010                             10:   0000 1010
   9: 0000 1001                              9:   0000 1001
  &:  0000 1000 = 8                         &:    0000 1000

Count set bits (popcount): __builtin_popcount(n)
  23: 0001 0111 → 4 set bits

Isolate lowest 0 bit:     ~n & (n+1)
```

### Brian Kernighan's Algorithm (Count Set Bits)
```
Count set bits in O(number of set bits):

n = 13 (1101):
Iteration 1: n = 1101 & 1100 = 1100  (count = 1)
Iteration 2: n = 1100 & 1011 = 1000  (count = 2)
Iteration 3: n = 1000 & 0111 = 0000  (count = 3)

while (n) {
    n &= (n - 1);
    count++;
}
```

### Bit Masks and Subsets
```
Generate all subsets of set {0,1,2}:

mask  Binary  Subset
  0   000     {}
  1   001     {0}
  2   010     {1}
  3   011     {0,1}
  4   100     {2}
  5   101     {0,2}
  6   110     {1,2}
  7   111     {0,1,2}

for (int mask = 0; mask < (1 << n); mask++) {
    for (int i = 0; i < n; i++) {
        if (mask & (1 << i)) {
            // Element i is in subset
        }
    }
}
```

### XOR Properties (Critical for DSA)
```
a ^ a = 0          (self-canceling)
a ^ 0 = a          (identity)
a ^ b = b ^ a      (commutative)
(a ^ b) ^ c = a ^ (b ^ c)  (associative)

Application: Find single non-duplicate
arr = [2, 3, 5, 4, 5, 3, 4]

2 ^ 3 ^ 5 ^ 4 ^ 5 ^ 3 ^ 4 = 2
(duplicates cancel out)

XOR cumulative property:
prefix_xor[i] = arr[0] ^ arr[1] ^ ... ^ arr[i]
Range XOR [L,R] = prefix_xor[R] ^ prefix_xor[L-1]
```

---

## 3. Number Theory for Competitive Programming

### Prime Sieve (Optimized)
```
Segmented Sieve for primes in range [L, R]:

Step 1: Generate primes up to √R
Step 2: Use them to sieve [L, R]

Time: O(R log log R)
Space: O(√R + (R-L))

For R = 10^12, L = 10^12 - 10^6:
Only need primes up to 10^6 to sieve the range
```

### Euler's Totient Function φ(n)
```
φ(n) = count of numbers ≤ n that are coprime to n

For n = 12:
Numbers: 1  2  3  4  5  6  7  8  9  10  11  12
Coprime: ✓  ✗  ✗  ✗  ✓  ✗  ✓  ✗  ✗  ✗  ✓   ✗
φ(12) = 4  (1, 5, 7, 11)

Formula: φ(n) = n × ∏(1 - 1/p) for all prime factors p

φ(12) = 12 × (1 - 1/2) × (1 - 1/3)
      = 12 × 1/2 × 2/3 = 4

Efficient computation:
int phi(int n) {
    int result = n;
    for (int p = 2; p * p <= n; p++) {
        if (n % p == 0) {
            while (n % p == 0) n /= p;
            result -= result / p;
        }
    }
    if (n > 1) result -= result / n;
    return result;
}
```

### Chinese Remainder Theorem (CRT)
```
System of congruences:
x ≡ a₁ (mod m₁)
x ≡ a₂ (mod m₂)
...
x ≡ aₖ (mod mₖ)

where m₁, m₂, ..., mₖ are pairwise coprime

Example:
x ≡ 2 (mod 3)
x ≡ 3 (mod 5)
x ≡ 2 (mod 7)

M = 3 × 5 × 7 = 105
M₁ = 105/3 = 35,  y₁: 35y₁ ≡ 1 (mod 3) → y₁ = 2
M₂ = 105/5 = 21,  y₂: 21y₂ ≡ 1 (mod 5) → y₂ = 1
M₃ = 105/7 = 15,  y₃: 15y₃ ≡ 1 (mod 7) → y₃ = 1

x = (2×35×2 + 3×21×1 + 2×15×1) mod 105
  = (140 + 63 + 30) mod 105
  = 233 mod 105 = 23

Application: Computing factorials modulo products of primes
```

---

## 4. Combinatorics

### Binomial Coefficients
```
C(n,k) = n! / (k!(n-k)!)

Pascal's Triangle:
                    1
                  1   1
                1   2   1
              1   3   3   1
            1   4   6   4   1
          1   5  10  10   5   1
        1   6  15  20  15   6   1

Property: C(n,k) = C(n-1,k-1) + C(n-1,k)

Computing with DP to avoid overflow:
C[0][0] = 1
for i = 1 to n:
    C[i][0] = 1
    for j = 1 to min(i,k):
        C[i][j] = (C[i-1][j-1] + C[i-1][j]) % MOD
```

### Stars and Bars
```
Distribute n identical items into k bins:
Answer = C(n+k-1, k-1)

Example: Place 5 balls in 3 bins
Representation: **|*|**
Pattern: n stars and k-1 bars
Total arrangements: C(5+3-1, 3-1) = C(7,2) = 21

Visual:
Bin1  Bin2  Bin3
  **    *     **    (one valid distribution)
```

### Catalan Numbers
```
Cₙ = C(2n,n)/(n+1) = (2n)! / ((n+1)!n!)

First few: 1, 1, 2, 5, 14, 42, 132, 429...

Recurrence: Cₙ = Σ(i=0 to n-1) Cᵢ × Cₙ₋₁₋ᵢ

Applications:
1. Valid parentheses sequences of length 2n
2. Binary trees with n+1 leaves
3. Ways to triangulate a convex (n+2)-gon
4. Paths on grid that don't cross diagonal

Example: Valid parentheses for n=3
()()()  (())()  ()(())  (()())  ((()))
All 5 = C₃
```

### Inclusion-Exclusion Principle
```
|A₁ ∪ A₂ ∪ ... ∪ Aₙ| = 
    Σ|Aᵢ| - Σ|Aᵢ∩Aⱼ| + Σ|Aᵢ∩Aⱼ∩Aₖ| - ... + (-1)ⁿ⁺¹|A₁∩...∩Aₙ|

Example: Count integers ≤ 100 divisible by 2, 3, or 5

|A₂| = 50, |A₃| = 33, |A₅| = 20
|A₂∩A₃| = 16, |A₂∩A₅| = 10, |A₃∩A₅| = 6
|A₂∩A₃∩A₅| = 3

Answer = 50 + 33 + 20 - 16 - 10 - 6 + 3 = 74

Derangements formula (no fixed points):
Dₙ = n! × Σ(i=0 to n) (-1)ⁱ/i!
```

---

## 5. Probability for Algorithmic Analysis

### Expected Value and Linearity
```
E[X + Y] = E[X] + E[Y]  (always true, even if dependent)

Example: Expected number of inversions in random array of n elements
For each pair (i,j) where i<j:
  P(aᵢ > aⱼ) = 1/2
  Expected inversions per pair = 1/2
  
Total pairs = C(n,2) = n(n-1)/2
E[inversions] = n(n-1)/4

QuickSort average case analysis:
E[comparisons] = 2n ln n ≈ 1.39n log₂ n
```

### Geometric Distribution
```
P(X = k) = (1-p)^(k-1) × p

Expected value: E[X] = 1/p

Example: Expected coin flips until first heads
E[X] = 1/0.5 = 2

Application: Expected time in randomized algorithms
```

### Balls and Bins (Birthday Paradox)
```
Throw m balls into n bins randomly:

Expected empty bins: n(1 - 1/n)^m
Expected bin with max balls: Θ(log n / log log n)  when m=n

Hash table collision analysis:
Load factor α = m/n
Expected collisions ≈ m²/(2n)  [Birthday paradox]

For m = √n, expect Θ(1) collision
For m = n, expect Θ(n) collisions
```

---

## 6. Recurrence Relations and Master Theorem

### Solving Recurrences

**1. Substitution Method**
```
T(n) = 2T(n/2) + n

Guess: T(n) = O(n log n)
Prove: T(n) ≤ cn log n for some c

T(n) = 2T(n/2) + n
     ≤ 2(c(n/2)log(n/2)) + n
     = cn log(n/2) + n
     = cn log n - cn + n
     ≤ cn log n  (if c ≥ 1)
```

**2. Recursion Tree**
```
T(n) = T(n/3) + T(2n/3) + n

Level 0:                n                    Cost: n
                       / \
Level 1:            n/3   2n/3              Cost: n
                    / \   / \
Level 2:         n/9 2n/9 2n/9 4n/9        Cost: n
                 ...

Height: log₃/₂(n)  [longest path]
Each level costs ≤ n
Total: O(n log n)
```

**3. Master Theorem**
```
For T(n) = aT(n/b) + f(n) where a≥1, b>1:

Case 1: f(n) = O(n^(log_b(a) - ε)) for ε>0
        → T(n) = Θ(n^(log_b a))

Case 2: f(n) = Θ(n^(log_b a))
        → T(n) = Θ(n^(log_b a) log n)

Case 3: f(n) = Ω(n^(log_b(a) + ε)) and a×f(n/b) ≤ c×f(n) for c<1
        → T(n) = Θ(f(n))

Examples:
T(n) = 9T(n/3) + n         → log₃ 9 = 2, Case 1 → O(n²)
T(n) = T(2n/3) + 1         → log₃/₂ 1 = 0, Case 2 → O(log n)
T(n) = 3T(n/4) + n log n   → log₄ 3 ≈ 0.79, Case 3 → O(n log n)
T(n) = 2T(n/2) + n log n   → Can't apply (not polynomial difference)
```

**4. Akra-Bazzi Method** (Generalization)
```
T(n) = Σ aᵢT(n/bᵢ) + f(n)

Find p such that Σ aᵢ/bᵢᵖ = 1

T(n) = Θ(n^p × (1 + ∫₁ⁿ f(u)/u^(p+1) du))

Example: T(n) = T(n/3) + T(2n/3) + n
1/3^p + (2/3)^p = 1 → p = 1
T(n) = Θ(n log n)
```

---

## 7. Graph Theory Mathematics

### Matrix Representation
```
Adjacency Matrix for graph with 4 vertices:

    0  1  2  3
  ┌──────────────┐
0 │ 0  1  1  0  │
1 │ 1  0  1  1  │
2 │ 1  1  0  1  │
3 │ 0  1  1  0  │
  └──────────────┘

A² gives paths of length 2
A³ gives paths of length 3
...
Aᵏ gives paths of length k
```

### Cayley's Formula
```
Number of labeled spanning trees on n vertices = n^(n-2)

For n=4: 4² = 16 spanning trees

Proof sketch via Prüfer sequences:
Each tree ↔ unique sequence of (n-2) numbers in [1,n]
Total sequences = n^(n-2)
```

### Graph Coloring and Independence
```
Chromatic Number χ(G):
Minimum colors needed to color vertices (no adjacent same color)

Brooks' Theorem:
χ(G) ≤ Δ(G)  except for complete graphs and odd cycles
where Δ(G) = maximum degree

Greedy coloring bound:
χ(G) ≤ Δ(G) + 1  (always)

Independence number α(G):
Maximum size of independent set

Ramsey Number R(r,s):
Minimum n such that any 2-coloring of Kₙ contains
a monochromatic Kᵣ or Kₛ

R(3,3) = 6  (proven)
R(4,4) = 18  (proven)
R(5,5) ∈ [43, 48]  (not yet determined!)
```

### Network Flow Properties
```
Max-Flow Min-Cut Theorem:
Maximum flow = Minimum cut capacity

Visualization:
Source ──→ [Network] ──→ Sink

Menger's Theorem:
Minimum vertex cut = Maximum vertex-disjoint paths

Application: Computing number of edge-disjoint paths
→ Run max-flow with all capacities = 1
→ Flow value = number of disjoint paths
```

---

## 8. Information Theory Basics

### Entropy
```
H(X) = -Σ p(x) log₂ p(x)

Example: Fair coin (p=0.5, q=0.5)
H(X) = -0.5 log₂(0.5) - 0.5 log₂(0.5)
     = 1 bit  (maximum uncertainty)

Biased coin (p=0.9, q=0.1)
H(X) = -0.9 log₂(0.9) - 0.1 log₂(0.1)
     ≈ 0.469 bits  (less uncertainty)

Application: Optimal encoding length
Expected bits needed = H(X)
```

### Huffman Coding Mathematics
```
Given probabilities: A=0.5, B=0.25, C=0.125, D=0.125

Build tree:
              1.0
             /   \
          0.5     0.5
          (A)    /   \
              0.25   0.25
              (B)   /   \
                 0.125 0.125
                  (C)   (D)

Codes: A=0, B=10, C=110, D=111
Average length = 0.5×1 + 0.25×2 + 0.125×3 + 0.125×3 = 1.75

Entropy = 1.75 bits (matches average code length!)
```

---

## 9. Linear Algebra for Algorithms

### Matrix Exponentiation
```
Compute Fibonacci F(n) in O(log n):

[ F(n+1) ]   [ 1 1 ]ⁿ   [ 1 ]
[ F(n)   ] = [ 1 0 ]  × [ 0 ]

Use fast exponentiation on matrices:
Time: O(log n) multiplications
Each multiplication: O(k³) for k×k matrix

Application: Linear recurrences
T(n) = c₁T(n-1) + c₂T(n-2) + ... + cₖT(n-k)
```

### Gaussian Elimination for XOR Systems
```
Solve system of XOR equations:
x₁ ⊕ x₂ = 1
x₂ ⊕ x₃ = 0
x₁ ⊕ x₃ = 1

Matrix representation (GF(2)):
[ 1 1 0 | 1 ]
[ 0 1 1 | 0 ]
[ 1 0 1 | 1 ]

Row reduction using XOR:
[ 1 1 0 | 1 ]
[ 0 1 1 | 0 ]
[ 0 1 1 | 0 ]  (R3 ⊕= R1)

Solution: x₁=1, x₂=0, x₃=0
```

### Determinant and Graph Counting
```
Matrix-Tree Theorem:
Number of spanning trees = any cofactor of Laplacian matrix

For graph:  0──1
            │\/│
            │/\│
            2──3

Laplacian L:
[ 2 -1 -1  0]
[-1  3 -1 -1]
[-1 -1  3 -1]
[ 0 -1 -1  2]

det(L₀₀) = 16 = number of spanning trees
(L₀₀ is L with row 0 and column 0 removed)
```

---

## 10. Generating Functions

### Ordinary Generating Functions
```
Sequence: a₀, a₁, a₂, ...
GF: A(x) = Σ aₙxⁿ

Example: Fibonacci
F(x) = Σ Fₙxⁿ = x/(1-x-x²)

Closed form from GF:
Fₙ = (φⁿ - ψⁿ)/√5
where φ = (1+√5)/2, ψ = (1-√5)/2
```

### Operations on Generating Functions
```
Convolution:
If A(x) = Σaₙxⁿ and B(x) = Σbₙxⁿ
Then A(x)B(x) = Σcₙxⁿ where cₙ = Σaᵢbₙ₋ᵢ

Application: Count ways to make change
Coins: 1, 2, 5
GF = (1+x+x²+...)×(1+x²+x⁴+...)×(1+x⁵+x¹⁰+...)
   = 1/((1-x)(1-x²)(1-x⁵))

Coefficient of xⁿ = ways to make n cents
```

---

## 11. Amortized Analysis

### Accounting Method
```
Binary Counter incrementing from 0 to n:

Operation costs:
Flip rightmost 0→1: 1 unit
Flip all trailing 1s→0: k units (for k trailing 1s)

Worst case per increment: O(log n)
But amortized cost: O(1)

Proof:
Charge 2 credits per bit flip 0→1
  - 1 credit pays for the flip
  - 1 credit saved for future 1→0 flip
  
Each increment:
  - Flips one 0→1 (costs 2 credits)
  - Flips ≤k 1→0 (paid by saved credits)
  
Amortized cost = 2 credits = O(1)
```

### Potential Method
```
Define potential function Φ(Dᵢ)

Amortized cost = actual cost + ΔΦ

Dynamic array doubling:
Φ(D) = 2×size - capacity

Insert when not full: cost=1, ΔΦ=2 → amortized=3
Insert when full (size=n): 
  cost = n+1 (copy all + insert)
  ΔΦ = 2(n+1) - 2n - n = -n+2
  amortized = n+1 - n + 2 = 3

All operations: O(1) amortized
```

---

## 12. Probabilistic Methods

### Randomized Algorithms Analysis
```
QuickSelect expected time:

T(n) = T(3n/4) + O(n)  (expected, good pivot)

Solving:
T(n) = O(n) + O(3n/4) + O(9n/16) + ...
     = O(n × Σ(3/4)ⁱ)
     = O(n × 4)
     = O(n)

Expected time: O(n)
Worst case: O(n²)  but probability: (1/2)ⁿ
```

### Las Vegas vs Monte Carlo
```
Las Vegas: Always correct, random runtime
  - QuickSort with random pivot
  - Randomized primality testing (deterministic correct)

Monte Carlo: Random answer, bounded time
  - Miller-Rabin with fixed iterations
  - May give wrong answer with probability ε

Converting Monte Carlo → Las Vegas:
Run k independent trials
Return majority answer
Error probability: ε^k
```

---

## 13. Advanced Number Theory

### Pollard's Rho Factorization
```
Find factor of n using f(x) = (x² + c) mod n

Heuristic time: O(√p) where p is smallest prime factor

Why it works:
Birthday paradox in cyclic group
Sequence eventually enters cycle
Length ≈ √p

Code pattern:
x = x₀, y = x₀
while true:
    x = f(x)
    y = f(f(y))
    d = gcd(|x-y|, n)
    if 1 < d < n: return d
```

### Fast Fourier Transform for Multiplication
```
Multiply two n-digit numbers in O(n log n):

Karatsuba: T(n) = 3T(n/2) + O(n) → O(n^1.585)
FFT: O(n log n)

Idea: Represent as polynomials
A(x) = a₀ + a₁x + a₂x² + ...
B(x) = b₀ + b₁x + b₂x² + ...

C(x) = A(x)B(x)

FFT: Evaluate at n points in O(n log n)
Multiply pointwise: O(n)
Inverse FFT: Interpolate in O(n log n)
```

This covers advanced mathematics crucial for competitive programming, systems design, and algorithm analysis at companies like Google, Meta, and in ICPC competitions.