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