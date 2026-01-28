# The Complete Number Theory Arsenal for Competitive Programming

Number Theory is the mathematical foundation that transforms seemingly impossible problems into elegant solutions. Let me build your understanding from absolute zero to mastery.

---

## **Foundation: What is Number Theory?**

**Number Theory** studies properties and relationships of integers (whole numbers: ..., -2, -1, 0, 1, 2, ...). In competitive programming, we leverage patterns in divisibility, primes, modular arithmetic, and multiplicative structures to solve problems efficiently.

---

## **I. DIVISIBILITY & FACTORS**

### **Concept: Divisor (Factor)**
A **divisor** of `n` is any integer `d` where `n % d == 0`.

**Example:** Divisors of 12 are: 1, 2, 3, 4, 6, 12

### **Mental Model: Why Care?**
Many problems reduce to "find all divisors" or "count numbers with specific divisor properties."

### **Pattern 1: Efficient Divisor Enumeration**

**Naive approach:** Check every number from 1 to n → O(n)

**Optimized insight:** Divisors come in pairs! If `d` divides `n`, then `n/d` also divides `n`.

```
12 = 1 × 12
12 = 2 × 6
12 = 3 × 4
```

We only need to check up to √n.

**Rust Implementation:**
```rust
fn get_divisors(n: i64) -> Vec<i64> {
    let mut divisors = Vec::new();
    let mut i = 1_i64;
    
    // Only iterate until sqrt(n)
    while i * i <= n {
        if n % i == 0 {
            divisors.push(i);
            // Add the paired divisor (avoid duplicates when i*i == n)
            if i != n / i {
                divisors.push(n / i);
            }
        }
        i += 1;
    }
    
    divisors.sort_unstable(); // O(d log d) where d = divisor count
    divisors
}
```

**Time Complexity:** O(√n)  
**Space Complexity:** O(d) where d ≈ 2√n in worst case

**Go Implementation:**
```go
func getDivisors(n int64) []int64 {
    divisors := make([]int64, 0)
    
    for i := int64(1); i*i <= n; i++ {
        if n%i == 0 {
            divisors = append(divisors, i)
            if i != n/i {
                divisors = append(divisors, n/i)
            }
        }
    }
    
    // Sort for consistency
    sort.Slice(divisors, func(i, j int) bool {
        return divisors[i] < divisors[j]
    })
    
    return divisors
}
```

**C Implementation:**
```c
#include <stdlib.h>
#include <math.h>

// Returns array of divisors, count stored in *size
int64_t* get_divisors(int64_t n, int* size) {
    int capacity = 128;
    int64_t* divisors = malloc(capacity * sizeof(int64_t));
    int count = 0;
    
    for (int64_t i = 1; i * i <= n; i++) {
        if (n % i == 0) {
            if (count >= capacity) {
                capacity *= 2;
                divisors = realloc(divisors, capacity * sizeof(int64_t));
            }
            divisors[count++] = i;
            if (i != n / i) {
                if (count >= capacity) {
                    capacity *= 2;
                    divisors = realloc(divisors, capacity * sizeof(int64_t));
                }
                divisors[count++] = n / i;
            }
        }
    }
    
    *size = count;
    return divisors;
}
```

---

### **Pattern 2: Greatest Common Divisor (GCD)**

**Definition:** The **GCD** of two numbers is the largest number that divides both.

**Example:** GCD(48, 18) = 6

**Euclidean Algorithm - The Elegant Approach:**

**Insight:** GCD(a, b) = GCD(b, a mod b)

**Why?** Any common divisor of `a` and `b` also divides `a - kb` for any integer `k`. When we take `a mod b`, we're essentially doing repeated subtraction.

**Visual Flow:**
```
GCD(48, 18)
= GCD(18, 48 % 18)
= GCD(18, 12)
= GCD(12, 18 % 12)
= GCD(12, 6)
= GCD(6, 12 % 6)
= GCD(6, 0)
= 6
```

**Rust Implementation:**
```rust
fn gcd(mut a: i64, mut b: i64) -> i64 {
    while b != 0 {
        let temp = b;
        b = a % b;
        a = temp;
    }
    a
}

// Recursive version (cleaner but uses stack)
fn gcd_recursive(a: i64, b: i64) -> i64 {
    if b == 0 { a } else { gcd_recursive(b, a % b) }
}
```

**Time Complexity:** O(log(min(a, b)))  
**Why logarithmic?** Each step reduces the larger number by at least half in at most two iterations (proven by Lamé's theorem).

**Go Implementation:**
```go
func gcd(a, b int64) int64 {
    for b != 0 {
        a, b = b, a%b
    }
    return a
}
```

**C Implementation:**
```c
int64_t gcd(int64_t a, int64_t b) {
    while (b != 0) {
        int64_t temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}
```

---

### **Pattern 3: Least Common Multiple (LCM)**

**Definition:** The **LCM** is the smallest number divisible by both numbers.

**Mathematical Relationship:**
```
LCM(a, b) = (a × b) / GCD(a, b)
```

**⚠️ Critical Pitfall:** Multiply first → overflow! Always divide first.

**Correct Implementation (Rust):**
```rust
fn lcm(a: i64, b: i64) -> i64 {
    // Divide first to prevent overflow
    (a / gcd(a, b)) * b
}
```

**Why this order?** 
- `a / gcd(a, b)` removes common factors from `a`
- Then multiply by `b` → gives LCM without intermediate overflow

---

## **II. PRIME NUMBERS**

### **Concept: Prime Number**
A **prime** is a natural number > 1 with exactly two divisors: 1 and itself.

**Examples:** 2, 3, 5, 7, 11, 13...

**Why Primes Matter:**
- Building blocks of all integers (fundamental theorem of arithmetic)
- Many problems involve prime factorization or counting primes

---

### **Pattern 4: Primality Testing**

**Naive Approach:** Check divisibility by all numbers from 2 to n-1 → O(n)

**Optimized Insight:** Only check up to √n (if n has a factor > √n, it must have a corresponding factor < √n)

**Rust Implementation:**
```rust
fn is_prime(n: i64) -> bool {
    if n <= 1 {
        return false;
    }
    if n <= 3 {
        return true;
    }
    // Eliminate even numbers and multiples of 3
    if n % 2 == 0 || n % 3 == 0 {
        return false;
    }
    
    // Check only numbers of form 6k ± 1
    // Why? All primes > 3 are of form 6k ± 1
    let mut i = 5;
    while i * i <= n {
        if n % i == 0 || n % (i + 2) == 0 {
            return false;
        }
        i += 6;
    }
    
    true
}
```

**Time Complexity:** O(√n)

**Deep Insight - Why 6k ± 1?**

All integers can be expressed as:
- 6k
- 6k + 1
- 6k + 2 = 2(3k + 1) → divisible by 2
- 6k + 3 = 3(2k + 1) → divisible by 3
- 6k + 4 = 2(3k + 2) → divisible by 2
- 6k + 5 = 6k - 1

So primes > 3 must be 6k ± 1!

---

### **Pattern 5: Sieve of Eratosthenes (Bulk Prime Generation)**

**Problem:** Find all primes up to n.

**Mental Model:** Start with all numbers, systematically eliminate composites.

**Algorithm Flow:**
```
1. Create array: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, ...]
2. Start with 2 (first prime)
   - Mark all multiples: 4, 6, 8, 10... as composite
3. Move to next unmarked (3)
   - Mark multiples: 6, 9, 12, 15...
4. Continue until √n
```

**Rust Implementation:**
```rust
fn sieve_of_eratosthenes(n: usize) -> Vec<bool> {
    let mut is_prime = vec![true; n + 1];
    is_prime[0] = false;
    is_prime[1] = false;
    
    let mut i = 2;
    while i * i <= n {
        if is_prime[i] {
            // Mark all multiples as composite
            let mut j = i * i; // Start from i² (optimization)
            while j <= n {
                is_prime[j] = false;
                j += i;
            }
        }
        i += 1;
    }
    
    is_prime
}

// Get actual prime numbers
fn get_primes(n: usize) -> Vec<usize> {
    let is_prime = sieve_of_eratosthenes(n);
    is_prime.iter()
        .enumerate()
        .filter_map(|(num, &prime)| if prime { Some(num) } else { None })
        .collect()
}
```

**Time Complexity:** O(n log log n)  
**Space Complexity:** O(n)

**Go Implementation:**
```go
func sieveOfEratosthenes(n int) []bool {
    isPrime := make([]bool, n+1)
    for i := range isPrime {
        isPrime[i] = true
    }
    isPrime[0], isPrime[1] = false, false
    
    for i := 2; i*i <= n; i++ {
        if isPrime[i] {
            for j := i * i; j <= n; j += i {
                isPrime[j] = false
            }
        }
    }
    
    return isPrime
}
```

---

## **III. PRIME FACTORIZATION**

### **Concept: Prime Factorization**
Every integer can be uniquely expressed as a product of prime powers.

**Example:**  
```
360 = 2³ × 3² × 5¹
```

### **Pattern 6: Prime Factorization Algorithm**

**Rust Implementation:**
```rust
use std::collections::HashMap;

fn prime_factorization(mut n: i64) -> HashMap<i64, i32> {
    let mut factors = HashMap::new();
    
    // Handle factor 2 separately (only even prime)
    while n % 2 == 0 {
        *factors.entry(2).or_insert(0) += 1;
        n /= 2;
    }
    
    // Check odd factors up to √n
    let mut i = 3;
    while i * i <= n {
        while n % i == 0 {
            *factors.entry(i).or_insert(0) += 1;
            n /= i;
        }
        i += 2; // Skip even numbers
    }
    
    // If n > 1, then it's a prime factor
    if n > 1 {
        *factors.entry(n).or_insert(0) += 1;
    }
    
    factors
}
```

**Time Complexity:** O(√n)

**Usage Example:**
```rust
fn main() {
    let factors = prime_factorization(360);
    // factors = {2: 3, 3: 2, 5: 1}
    
    // Reconstruct number
    let mut result = 1_i64;
    for (prime, power) in factors {
        result *= prime.pow(power as u32);
    }
    println!("{}", result); // 360
}
```

---

## **IV. MODULAR ARITHMETIC**

### **Concept: Modulo Operation**
`a mod m` gives the **remainder** when `a` is divided by `m`.

**Examples:**
- 17 mod 5 = 2
- -3 mod 5 = 2 (careful with negatives!)

**Why Essential?** Many problems ask for "answer modulo 10⁹+7" to prevent overflow.

---

### **Pattern 7: Modular Addition, Subtraction, Multiplication**

**Properties:**
```
(a + b) mod m = ((a mod m) + (b mod m)) mod m
(a - b) mod m = ((a mod m) - (b mod m) + m) mod m  // +m handles negatives
(a × b) mod m = ((a mod m) × (b mod m)) mod m
```

**Rust Implementation:**
```rust
const MOD: i64 = 1_000_000_007;

fn mod_add(a: i64, b: i64, m: i64) -> i64 {
    ((a % m) + (b % m)) % m
}

fn mod_sub(a: i64, b: i64, m: i64) -> i64 {
    ((a % m) - (b % m) + m) % m
}

fn mod_mul(a: i64, b: i64, m: i64) -> i64 {
    ((a % m) * (b % m)) % m
}
```

**⚠️ Division is NOT distributive!** (a/b) mod m ≠ usual formula

---

### **Pattern 8: Modular Exponentiation (Power)**

**Problem:** Compute a^b mod m efficiently.

**Naive:** Multiply `a` by itself `b` times → O(b) → TLE for large b

**Binary Exponentiation (Exponentiation by Squaring):**

**Insight:** 
```
a^8 = ((a²)²)²  → Only 3 multiplications instead of 7!
```

**Algorithm:**
```
If b is even: a^b = (a²)^(b/2)
If b is odd:  a^b = a × a^(b-1)
```

**Rust Implementation:**
```rust
fn mod_pow(mut base: i64, mut exp: i64, m: i64) -> i64 {
    let mut result = 1;
    base %= m;
    
    while exp > 0 {
        // If exp is odd, multiply current base
        if exp % 2 == 1 {
            result = (result * base) % m;
        }
        
        // Square the base
        base = (base * base) % m;
        exp /= 2;
    }
    
    result
}
```

**Time Complexity:** O(log b)

**Visual Example:** Compute 2^13 mod 1000
```
13 in binary: 1101

2^13 = 2^8 × 2^4 × 2^1
     = 256 × 16 × 2
     = 8192 mod 1000 = 192
```

**C Implementation:**
```c
int64_t mod_pow(int64_t base, int64_t exp, int64_t m) {
    int64_t result = 1;
    base %= m;
    
    while (exp > 0) {
        if (exp % 2 == 1) {
            result = (result * base) % m;
        }
        base = (base * base) % m;
        exp /= 2;
    }
    
    return result;
}
```

---

### **Pattern 9: Modular Multiplicative Inverse**

**Concept:** The **modular inverse** of `a` modulo `m` is a number `x` such that:
```
(a × x) mod m = 1
```

**Notation:** x = a⁻¹ (mod m)

**When does it exist?** Only when GCD(a, m) = 1 (a and m are **coprime**)

**Why needed?** To compute (a/b) mod m = (a × b⁻¹) mod m

---

**Method 1: Using Fermat's Little Theorem**

**Theorem:** If `m` is prime and GCD(a, m) = 1:
```
a^(m-1) ≡ 1 (mod m)
Therefore: a^(m-2) ≡ a⁻¹ (mod m)
```

**Rust Implementation:**
```rust
fn mod_inverse_fermat(a: i64, m: i64) -> i64 {
    // Only works when m is prime
    mod_pow(a, m - 2, m)
}
```

**Time Complexity:** O(log m)

---

**Method 2: Extended Euclidean Algorithm (Works for any coprime pair)**

**Algorithm:** Finds integers x, y such that:
```
ax + my = GCD(a, m)
```

When GCD(a, m) = 1:
```
ax + my = 1
ax = 1 - my
ax ≡ 1 (mod m)  → x is the inverse!
```

**Rust Implementation:**
```rust
fn extended_gcd(a: i64, b: i64) -> (i64, i64, i64) {
    if b == 0 {
        return (a, 1, 0); // gcd, x, y
    }
    
    let (gcd, x1, y1) = extended_gcd(b, a % b);
    let x = y1;
    let y = x1 - (a / b) * y1;
    
    (gcd, x, y)
}

fn mod_inverse_extended(a: i64, m: i64) -> Option<i64> {
    let (gcd, x, _) = extended_gcd(a, m);
    
    if gcd != 1 {
        return None; // Inverse doesn't exist
    }
    
    // Ensure positive result
    Some((x % m + m) % m)
}
```

---

## **V. COMBINATORICS & NUMBER THEORY**

### **Pattern 10: Computing nCr (Binomial Coefficients) mod m**

**Formula:**
```
C(n, r) = n! / (r! × (n-r)!)
```

**Challenge:** Factorials overflow quickly!

**Solution with Modular Inverse:**

**Rust Implementation:**
```rust
const MOD: i64 = 1_000_000_007;

// Precompute factorials
fn precompute_factorials(n: usize) -> Vec<i64> {
    let mut fact = vec![1; n + 1];
    for i in 1..=n {
        fact[i] = (fact[i - 1] * i as i64) % MOD;
    }
    fact
}

fn ncr_mod(n: usize, r: usize, fact: &[i64]) -> i64 {
    if r > n {
        return 0;
    }
    
    let numerator = fact[n];
    let denominator = (fact[r] * fact[n - r]) % MOD;
    
    // C(n, r) = numerator / denominator mod MOD
    //         = numerator × denominator^(-1) mod MOD
    let inv_denominator = mod_pow(denominator, MOD - 2, MOD);
    (numerator * inv_denominator) % MOD
}
```

**Time Complexity:**
- Precomputation: O(n)
- Each query: O(log MOD)

---

## **VI. ADVANCED PATTERNS**

### **Pattern 11: Chinese Remainder Theorem (CRT)**

**Problem:** Solve system of congruences:
```
x ≡ a₁ (mod m₁)
x ≡ a₂ (mod m₂)
...
x ≡ aₖ (mod mₖ)
```

**When applicable:** When all moduli are pairwise coprime (GCD(mᵢ, mⱼ) = 1 for i ≠ j)

**Go Implementation (Basic CRT for 2 equations):**
```go
func crt(a1, m1, a2, m2 int64) int64 {
    _, x, y := extendedGCD(m1, m2)
    
    // x = a1 + m1 × k
    // Substitute into second equation
    result := a1 + m1*((a2-a1)*x)
    M := m1 * m2
    
    return ((result % M) + M) % M
}
```

---

### **Pattern 12: Euler's Totient Function φ(n)**

**Definition:** φ(n) = count of numbers ≤ n that are coprime with n

**Examples:**
- φ(9) = 6 → {1, 2, 4, 5, 7, 8}
- φ(7) = 6 → {1, 2, 3, 4, 5, 6} (all, since 7 is prime)

**Formula using prime factorization:**
```
If n = p₁^a₁ × p₂^a₂ × ... × pₖ^aₖ
Then φ(n) = n × (1 - 1/p₁) × (1 - 1/p₂) × ... × (1 - 1/pₖ)
```

**Rust Implementation:**
```rust
fn euler_totient(mut n: i64) -> i64 {
    let mut result = n;
    
    // Process factor 2
    if n % 2 == 0 {
        result -= result / 2;
        while n % 2 == 0 {
            n /= 2;
        }
    }
    
    // Process odd factors
    let mut i = 3;
    while i * i <= n {
        if n % i == 0 {
            result -= result / i;
            while n % i == 0 {
                n /= i;
            }
        }
        i += 2;
    }
    
    // If n > 1, it's a prime factor
    if n > 1 {
        result -= result / n;
    }
    
    result
}
```

**Time Complexity:** O(√n)

---

## **VII. PROBLEM-SOLVING FLOW**

```
┌─────────────────────────────────────────┐
│  Read Problem                           │
│  ↓                                      │
│  Identify Number Theory Pattern         │
│  ↓                                      │
│  Choose Algorithm                       │
│  ├─ Divisors? → O(√n) enumeration      │
│  ├─ Primes? → Sieve or primality test  │
│  ├─ Large powers? → Modular exp        │
│  ├─ Combinations? → nCr with mod inv   │
│  └─ System of equations? → CRT         │
│  ↓                                      │
│  Implement                              │
│  ↓                                      │
│  Test edge cases:                       │
│    - n = 0, 1, 2                        │
│    - Large numbers (overflow?)          │
│    - Negative numbers                   │
│    - Modulo operations correct?         │
└─────────────────────────────────────────┘
```

---

## **VIII. COMMON LEETCODE NUMBER THEORY PROBLEMS**

### **Pattern Recognition Guide:**

| **Problem Type** | **Key Indicator** | **Algorithm** |
|------------------|-------------------|---------------|
| Count divisors | "factors", "divisible by" | O(√n) iteration |
| Prime checking | "prime number" | Primality test or Sieve |
| Large computations | "modulo 10⁹+7" | Modular arithmetic |
| Powers | "a^b", "exponent" | Binary exponentiation |
| Combinations | "choose r from n" | nCr with inverse |
| GCD/LCM | "common", "multiple" | Euclidean algorithm |

---

## **Final Mental Models**

### **1. Square Root Boundary**
Most number theory algorithms exploit the √n boundary:
- Divisors come in pairs across √n
- Primality only needs checking up to √n
- Factorization terminates at √n

### **2. Modular Thinking**
When numbers get large:
- Apply mod at each step (prevent overflow)
- Use inverse for division
- Binary exponentiation for powers

### **3. Prime as Building Blocks**
Every integer is uniquely determined by its prime factorization → many problems reduce to manipulating prime factors.

---

This forms your complete number theory foundation. Each pattern builds on previous ones—master them sequentially, implement in your target language, and solve increasingly complex problems to develop expert intuition.

Would you like me to dive deeper into any specific pattern or work through concrete LeetCode problems applying these concepts?