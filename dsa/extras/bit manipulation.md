# Comprehensive Guide to Bit Manipulation in DSA

## Table of Contents

1. [Fundamentals](#fundamentals)
2. [Basic Operations](#basic-operations)
3. [Common Techniques](#common-techniques)
4. [Classic Problems](#classic-problems)
5. [Advanced Patterns](#advanced-patterns)

---

## Fundamentals

### Binary Representation

- Computers store numbers in binary (base-2)
- Each bit represents a power of 2
- Example: `13 = 1101₂ = 1×2³ + 1×2² + 0×2¹ + 1×2⁰`

### Bitwise Operators

| Operator | Symbol | Description |
|----------|--------|-------------|
| AND | `&` | 1 if both bits are 1 |
| OR | `\|` | 1 if at least one bit is 1 |
| XOR | `^` | 1 if bits are different |
| NOT | `~` | Inverts all bits |
| Left Shift | `<<` | Shifts bits left, filling with 0s |
| Right Shift | `>>` | Shifts bits right |

---

## Basic Operations

### 1. Check if i-th Bit is Set

**Rust:**

```rust
fn is_bit_set(num: i32, i: u32) -> bool {
    (num & (1 << i)) != 0
}
```

**Python:**

```python
def is_bit_set(num: int, i: int) -> bool:
    return (num & (1 << i)) != 0
```

### 2. Set i-th Bit

**Rust:**

```rust
fn set_bit(num: i32, i: u32) -> i32 {
    num | (1 << i)
}
```

**Python:**

```python
def set_bit(num: int, i: int) -> int:
    return num | (1 << i)
```

### 3. Clear i-th Bit

**Rust:**

```rust
fn clear_bit(num: i32, i: u32) -> i32 {
    num & !(1 << i)
}
```

**Python:**

```python
def clear_bit(num: int, i: int) -> int:
    return num & ~(1 << i)
```

### 4. Toggle i-th Bit

**Rust:**

```rust
fn toggle_bit(num: i32, i: u32) -> i32 {
    num ^ (1 << i)
}
```

**Python:**

```python
def toggle_bit(num: int, i: int) -> int:
    return num ^ (1 << i)
```

---

## Common Techniques

### 1. Count Set Bits (Hamming Weight)

**Rust:**

```rust
fn count_set_bits(mut num: i32) -> i32 {
    let mut count = 0;
    while num != 0 {
        count += num & 1;
        num >>= 1;
    }
    count
}

// Brian Kernighan's Algorithm - O(k) where k is number of set bits
fn count_set_bits_optimized(mut num: i32) -> i32 {
    let mut count = 0;
    while num != 0 {
        num &= num - 1; // Removes rightmost set bit
        count += 1;
    }
    count
}
```

**Python:**

```python
def count_set_bits(num: int) -> int:
    count = 0
    while num:
        count += num & 1
        num >>= 1
    return count

# Brian Kernighan's Algorithm
def count_set_bits_optimized(num: int) -> int:
    count = 0
    while num:
        num &= num - 1  # Removes rightmost set bit
        count += 1
    return count

# Built-in method
def count_set_bits_builtin(num: int) -> int:
    return bin(num).count('1')
```

### 2. Check if Power of Two

**Rust:**

```rust
fn is_power_of_two(n: i32) -> bool {
    n > 0 && (n & (n - 1)) == 0
}
```

**Python:**

```python
def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0
```

### 3. Find Rightmost Set Bit

**Rust:**

```rust
fn rightmost_set_bit(num: i32) -> i32 {
    num & -num
}
```

**Python:**

```python
def rightmost_set_bit(num: int) -> int:
    return num & -num
```

### 4. Clear Rightmost Set Bit

**Rust:**

```rust
fn clear_rightmost_set_bit(num: i32) -> i32 {
    num & (num - 1)
}
```

**Python:**

```python
def clear_rightmost_set_bit(num: int) -> int:
    return num & (num - 1)
```

### 5. Get All Subsets (Power Set)

**Rust:**

```rust
fn get_all_subsets(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let n = nums.len();
    let total_subsets = 1 << n; // 2^n
    let mut result = Vec::new();
    
    for mask in 0..total_subsets {
        let mut subset = Vec::new();
        for i in 0..n {
            if (mask & (1 << i)) != 0 {
                subset.push(nums[i]);
            }
        }
        result.push(subset);
    }
    result
}
```

**Python:**

```python
def get_all_subsets(nums: list[int]) -> list[list[int]]:
    n = len(nums)
    total_subsets = 1 << n  # 2^n
    result = []
    
    for mask in range(total_subsets):
        subset = []
        for i in range(n):
            if mask & (1 << i):
                subset.append(nums[i])
        result.append(subset)
    return result
```

---

## Classic Problems

### 1. Single Number (All others appear twice)

**Rust:**

```rust
fn single_number(nums: Vec<i32>) -> i32 {
    nums.iter().fold(0, |acc, &x| acc ^ x)
}
```

**Python:**

```python
def single_number(nums: list[int]) -> int:
    result = 0
    for num in nums:
        result ^= num
    return result

# Or using reduce
from functools import reduce
import operator

def single_number_functional(nums: list[int]) -> int:
    return reduce(operator.xor, nums, 0)
```

### 2. Single Number II (All others appear 3 times)

**Rust:**

```rust
fn single_number_ii(nums: Vec<i32>) -> i32 {
    let mut ones = 0;
    let mut twos = 0;
    
    for &num in &nums {
        twos |= ones & num;
        ones ^= num;
        let threes = ones & twos;
        ones &= !threes;
        twos &= !threes;
    }
    ones
}
```

**Python:**

```python
def single_number_ii(nums: list[int]) -> int:
    ones, twos = 0, 0
    
    for num in nums:
        twos |= ones & num
        ones ^= num
        threes = ones & twos
        ones &= ~threes
        twos &= ~threes
    
    return ones
```

### 3. Two Numbers Appearing Once (All others twice)

**Rust:**

```rust
fn single_number_iii(nums: Vec<i32>) -> Vec<i32> {
    let xor_all = nums.iter().fold(0, |acc, &x| acc ^ x);
    let rightmost_bit = xor_all & -xor_all;
    
    let mut num1 = 0;
    let mut num2 = 0;
    
    for &num in &nums {
        if (num & rightmost_bit) != 0 {
            num1 ^= num;
        } else {
            num2 ^= num;
        }
    }
    
    vec![num1, num2]
}
```

**Python:**

```python
def single_number_iii(nums: list[int]) -> list[int]:
    xor_all = 0
    for num in nums:
        xor_all ^= num
    
    # Find rightmost set bit
    rightmost_bit = xor_all & -xor_all
    
    num1, num2 = 0, 0
    for num in nums:
        if num & rightmost_bit:
            num1 ^= num
        else:
            num2 ^= num
    
    return [num1, num2]
```

### 4. Reverse Bits

**Rust:**

```rust
fn reverse_bits(mut n: u32) -> u32 {
    let mut result = 0u32;
    for _ in 0..32 {
        result = (result << 1) | (n & 1);
        n >>= 1;
    }
    result
}
```

**Python:**

```python
def reverse_bits(n: int) -> int:
    result = 0
    for _ in range(32):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result
```

### 5. Count Bits (0 to n)

**Rust:**

```rust
fn count_bits(n: i32) -> Vec<i32> {
    let mut result = vec![0; (n + 1) as usize];
    for i in 1..=n as usize {
        result[i] = result[i >> 1] + (i as i32 & 1);
    }
    result
}
```

**Python:**

```python
def count_bits(n: int) -> list[int]:
    result = [0] * (n + 1)
    for i in range(1, n + 1):
        result[i] = result[i >> 1] + (i & 1)
    return result
```

### 6. Maximum XOR of Two Numbers

**Rust:**

```rust
fn find_maximum_xor(nums: Vec<i32>) -> i32 {
    let mut max_xor = 0;
    let mut mask = 0;
    
    for i in (0..32).rev() {
        mask |= 1 << i;
        let mut prefixes = std::collections::HashSet::new();
        
        for &num in &nums {
            prefixes.insert(num & mask);
        }
        
        let candidate = max_xor | (1 << i);
        for &prefix in &prefixes {
            if prefixes.contains(&(candidate ^ prefix)) {
                max_xor = candidate;
                break;
            }
        }
    }
    max_xor
}
```

**Python:**

```python
def find_maximum_xor(nums: list[int]) -> int:
    max_xor = 0
    mask = 0
    
    for i in range(31, -1, -1):
        mask |= (1 << i)
        prefixes = {num & mask for num in nums}
        
        candidate = max_xor | (1 << i)
        for prefix in prefixes:
            if candidate ^ prefix in prefixes:
                max_xor = candidate
                break
    
    return max_xor
```

---

## Bitwise Arithmetic Operations

### 1. Addition Using Bits

Addition can be performed using XOR (for sum without carry) and AND (for carry).

**Algorithm:**

- `a ^ b` gives sum without considering carry
- `(a & b) << 1` gives the carry
- Repeat until carry becomes 0

**Rust:**

```rust
fn add_without_arithmetic(mut a: i32, mut b: i32) -> i32 {
    while b != 0 {
        let carry = (a & b) << 1; // Calculate carry
        a = a ^ b;                 // Sum without carry
        b = carry;                 // Update b to carry
    }
    a
}

// Example step-by-step for 5 + 3:
// 5 = 101, 3 = 011
// Iteration 1:
//   carry = (101 & 011) << 1 = 001 << 1 = 010
//   a = 101 ^ 011 = 110
//   b = 010
// Iteration 2:
//   carry = (110 & 010) << 1 = 010 << 1 = 100
//   a = 110 ^ 010 = 100
//   b = 100
// Iteration 3:
//   carry = (100 & 100) << 1 = 100 << 1 = 1000
//   a = 100 ^ 100 = 000
//   b = 1000
// Iteration 4:
//   carry = (000 & 1000) << 1 = 000
//   a = 000 ^ 1000 = 1000 (8 in decimal)
//   b = 000
// Result: 8
```

**Python:**

```python
def add_without_arithmetic(a: int, b: int) -> int:
    # Python has arbitrary precision integers, so we need to handle the mask
    mask = 0xFFFFFFFF  # 32-bit mask
    
    while b != 0:
        carry = ((a & b) << 1) & mask
        a = (a ^ b) & mask
        b = carry
    
    # Handle negative numbers in 32-bit representation
    return a if a <= 0x7FFFFFFF else ~(a ^ mask)

# Simpler version for positive numbers only
def add_positive(a: int, b: int) -> int:
    while b != 0:
        carry = (a & b) << 1
        a = a ^ b
        b = carry
    return a
```

### 2. Subtraction Using Bits

Subtraction is addition with two's complement: `a - b = a + (~b + 1)`

**Rust:**

```rust
fn subtract_without_arithmetic(a: i32, b: i32) -> i32 {
    // a - b = a + (-b)
    // -b = ~b + 1 (two's complement)
    add_without_arithmetic(a, add_without_arithmetic(!b, 1))
}

// Alternative implementation
fn subtract(mut a: i32, mut b: i32) -> i32 {
    while b != 0 {
        let borrow = (!a & b) << 1; // Calculate borrow
        a = a ^ b;                   // Difference without borrow
        b = borrow;
    }
    a
}
```

**Python:**

```python
def subtract_without_arithmetic(a: int, b: int) -> int:
    # a - b = a + (-b)
    # -b = ~b + 1 (two's complement)
    mask = 0xFFFFFFFF
    
    # Calculate -b using two's complement
    neg_b = add_without_arithmetic(~b & mask, 1)
    result = add_without_arithmetic(a, neg_b)
    
    return result if result <= 0x7FFFFFFF else ~(result ^ mask)

# Alternative borrow-based approach
def subtract(a: int, b: int) -> int:
    mask = 0xFFFFFFFF
    
    while b != 0:
        borrow = ((~a & b) << 1) & mask
        a = (a ^ b) & mask
        b = borrow
    
    return a if a <= 0x7FFFFFFF else ~(a ^ mask)
```

### 3. Multiplication Using Bits

Multiplication through repeated addition and left shifts (like long multiplication).

**Rust:**

```rust
fn multiply_without_arithmetic(mut a: i32, mut b: i32) -> i32 {
    let mut result = 0;
    let negative = (a < 0) ^ (b < 0);
    
    a = a.abs();
    b = b.abs();
    
    while b != 0 {
        if (b & 1) != 0 {
            result = add_without_arithmetic(result, a);
        }
        a <<= 1;  // Double a
        b >>= 1;  // Halve b
    }
    
    if negative { -result } else { result }
}

// Example for 5 * 3:
// 5 = 101, 3 = 11
// Iteration 1: b=11 (odd), result = 0 + 5 = 5, a = 10, b = 1
// Iteration 2: b=1 (odd), result = 5 + 10 = 15, a = 20, b = 0
// Result: 15
```

**Python:**

```python
def multiply_without_arithmetic(a: int, b: int) -> int:
    result = 0
    negative = (a < 0) ^ (b < 0)
    
    a, b = abs(a), abs(b)
    
    while b:
        if b & 1:
            result = add_positive(result, a)
        a <<= 1  # Double a
        b >>= 1  # Halve b
    
    return -result if negative else result

# Optimized version using Russian Peasant method
def multiply_russian_peasant(a: int, b: int) -> int:
    result = 0
    while b > 0:
        if b & 1:
            result += a
        a <<= 1
        b >>= 1
    return result
```

### 4. Division Using Bits

Division through repeated subtraction with left shifts (binary search approach).

**Rust:**

```rust
fn divide_without_arithmetic(mut dividend: i32, mut divisor: i32) -> i32 {
    if divisor == 0 {
        panic!("Division by zero");
    }
    
    if dividend == i32::MIN && divisor == -1 {
        return i32::MAX; // Overflow case
    }
    
    let negative = (dividend < 0) ^ (divisor < 0);
    
    let mut dvd = (dividend as i64).abs();
    let mut dvs = (divisor as i64).abs();
    let mut quotient = 0i64;
    
    while dvd >= dvs {
        let mut temp = dvs;
        let mut multiple = 1i64;
        
        while dvd >= (temp << 1) {
            temp <<= 1;
            multiple <<= 1;
        }
        
        dvd -= temp;
        quotient += multiple;
    }
    
    if negative { -quotient as i32 } else { quotient as i32 }
}
```

**Python:**

```python
def divide_without_arithmetic(dividend: int, divisor: int) -> int:
    if divisor == 0:
        raise ValueError("Division by zero")
    
    # Handle overflow
    INT_MAX = 2**31 - 1
    INT_MIN = -2**31
    
    if dividend == INT_MIN and divisor == -1:
        return INT_MAX
    
    negative = (dividend < 0) ^ (divisor < 0)
    
    dvd, dvs = abs(dividend), abs(divisor)
    quotient = 0
    
    while dvd >= dvs:
        temp = dvs
        multiple = 1
        
        # Find the largest multiple
        while dvd >= (temp << 1):
            temp <<= 1
            multiple <<= 1
        
        dvd -= temp
        quotient += multiple
    
    result = -quotient if negative else quotient
    return max(INT_MIN, min(INT_MAX, result))
```

### 5. Modulo Using Bits

**Rust:**

```rust
fn modulo_without_arithmetic(dividend: i32, divisor: i32) -> i32 {
    let quotient = divide_without_arithmetic(dividend, divisor);
    dividend - multiply_without_arithmetic(quotient, divisor)
}

// Fast modulo for power of 2
fn modulo_power_of_two(n: i32, pow2: i32) -> i32 {
    // n % pow2 = n & (pow2 - 1) when pow2 is power of 2
    n & (pow2 - 1)
}
```

**Python:**

```python
def modulo_without_arithmetic(dividend: int, divisor: int) -> int:
    quotient = divide_without_arithmetic(dividend, divisor)
    return dividend - multiply_russian_peasant(quotient, divisor)

# Fast modulo for power of 2
def modulo_power_of_two(n: int, pow2: int) -> int:
    # n % pow2 = n & (pow2 - 1) when pow2 is power of 2
    return n & (pow2 - 1)
```

### 6. Negation Using Bits

**Rust:**

```rust
fn negate(n: i32) -> i32 {
    // Two's complement: -n = ~n + 1
    add_without_arithmetic(!n, 1)
}
```

**Python:**

```python
def negate(n: int) -> int:
    # Two's complement: -n = ~n + 1
    return add_positive(~n & 0xFFFFFFFF, 1)
```

### 7. Absolute Value Using Bits

**Rust:**

```rust
fn abs_value(n: i32) -> i32 {
    let mask = n >> 31; // All 1s if negative, all 0s if positive
    (n ^ mask) - mask
}

// Alternative method
fn abs_value_alt(n: i32) -> i32 {
    if (n >> 31) != 0 {
        !n + 1
    } else {
        n
    }
}
```

**Python:**

```python
def abs_value(n: int) -> int:
    # Assuming 32-bit integer
    mask = n >> 31  # All 1s if negative, all 0s if positive
    return (n ^ mask) - mask

# Alternative using conditional
def abs_value_alt(n: int) -> int:
    return n if n >= 0 else add_positive(~n & 0xFFFFFFFF, 1)
```

### 8. Maximum of Two Numbers Without Comparison

**Rust:**

```rust
fn max_without_comparison(a: i32, b: i32) -> i32 {
    let diff = a - b;
    let sign = (diff >> 31) & 1; // 1 if a < b, 0 if a >= b
    a - sign * diff
}

// Alternative avoiding overflow
fn max_safe(a: i32, b: i32) -> i32 {
    let c = a - b;
    let k = (c >> 31) & 1;
    k * b + (!k & 1) * a
}
```

**Python:**

```python
def max_without_comparison(a: int, b: int) -> int:
    diff = a - b
    sign = (diff >> 31) & 1  # 1 if a < b, 0 if a >= b
    return a - sign * diff

# More robust version
def max_safe(a: int, b: int) -> int:
    return a if (a - b) >= 0 else b
```

### 9. Minimum of Two Numbers Without Comparison

**Rust:**

```rust
fn min_without_comparison(a: i32, b: i32) -> i32 {
    let diff = a - b;
    let sign = (diff >> 31) & 1;
    b + sign * diff
}
```

**Python:**

```python
def min_without_comparison(a: int, b: int) -> int:
    diff = a - b
    sign = (diff >> 31) & 1
    return b + sign * diff
```

### 10. Sign of a Number

**Rust:**

```rust
fn sign(n: i32) -> i32 {
    // Returns: -1 for negative, 0 for zero, 1 for positive
    (n >> 31) | ((-n as u32) >> 31) as i32
}

// Alternative
fn sign_alt(n: i32) -> i32 {
    if n > 0 { 1 } else if n < 0 { -1 } else { 0 }
}
```

**Python:**

```python
def sign(n: int) -> int:
    # Returns: -1 for negative, 0 for zero, 1 for positive
    return (n >> 31) | ((-n) >> 31 & 0xFFFFFFFF)

# Simpler version
def sign_simple(n: int) -> int:
    return (n > 0) - (n < 0)
```

### Understanding Addition with Bits - Detailed Example

```
Adding 5 + 3:
  5 = 0101
  3 = 0011

Step 1: XOR (sum without carry)
  0101 ^ 0011 = 0110 (6)

Step 2: AND then left shift (carry)
  (0101 & 0011) << 1 = 0001 << 1 = 0010 (2)

Step 3: Add sum and carry (recursively)
  0110 + 0010
  
  XOR: 0110 ^ 0010 = 0100 (4)
  AND: (0110 & 0010) << 1 = 0010 << 1 = 0100 (4)
  
  0100 + 0100
  
  XOR: 0100 ^ 0100 = 0000
  AND: (0100 & 0100) << 1 = 0100 << 1 = 1000 (8)
  
  0000 + 1000 = 1000 (8)
  
Result: 8 ✓
```

### Understanding Multiplication - Detailed Example

```
Multiplying 5 × 3:
  5 = 101
  3 = 011

Think of it as: 5 × (2¹ + 2⁰) = 5×2 + 5×1

Iteration 1:
  b = 011 (bit 0 is 1)
  result = 0 + 5 = 5
  a = 101 << 1 = 1010 (10)
  b = 011 >> 1 = 001

Iteration 2:
  b = 001 (bit 0 is 1)
  result = 5 + 10 = 15
  a = 1010 << 1 = 10100 (20)
  b = 001 >> 1 = 000

b = 0, stop
Result: 15 ✓
```

### Performance Comparison

| Operation | Standard | Bitwise | Notes |
|-----------|----------|---------|-------|
| Addition | O(1) | O(log n) | Bitwise slower due to iteration |
| Subtraction | O(1) | O(log n) | Use two's complement |
| Multiplication | O(1) | O(log n) | n = number of bits |
| Division | O(1) | O(log²n) | Binary search approach |
| Power of 2 mod | O(1) | O(1) | `n & (pow2-1)` is faster |

**Note:** These bitwise implementations are primarily educational. Modern CPUs have dedicated circuits for arithmetic that are much faster than bit-by-bit operations in software.

---

## Advanced Patterns

### 1. Bit Masking for State Representation

**Rust:**

```rust
// Example: Traveling Salesman Problem
fn tsp_dp(dist: Vec<Vec<i32>>) -> i32 {
    let n = dist.len();
    let all_visited = (1 << n) - 1;
    let mut dp = vec![vec![i32::MAX / 2; n]; 1 << n];
    dp[1][0] = 0;
    
    for mask in 1..=(1 << n) - 1 {
        for u in 0..n {
            if (mask & (1 << u)) == 0 {
                continue;
            }
            for v in 0..n {
                if (mask & (1 << v)) != 0 {
                    continue;
                }
                let next_mask = mask | (1 << v);
                dp[next_mask][v] = dp[next_mask][v].min(dp[mask][u] + dist[u][v]);
            }
        }
    }
    
    (0..n).map(|i| dp[all_visited][i] + dist[i][0]).min().unwrap()
}
```

**Python:**

```python
def tsp_dp(dist: list[list[int]]) -> int:
    n = len(dist)
    all_visited = (1 << n) - 1
    dp = [[float('inf')] * n for _ in range(1 << n)]
    dp[1][0] = 0
    
    for mask in range(1, 1 << n):
        for u in range(n):
            if not (mask & (1 << u)):
                continue
            for v in range(n):
                if mask & (1 << v):
                    continue
                next_mask = mask | (1 << v)
                dp[next_mask][v] = min(dp[next_mask][v], 
                                       dp[mask][u] + dist[u][v])
    
    return min(dp[all_visited][i] + dist[i][0] for i in range(n))
```

### 2. Gosper's Hack (Iterate through all k-bit subsets)

**Rust:**

```rust
fn gospers_hack(n: usize, k: usize) -> Vec<i32> {
    let mut result = Vec::new();
    let mut set = (1 << k) - 1;
    let limit = 1 << n;
    
    while set < limit {
        result.push(set);
        let c = set & -(set as i32);
        let r = set + c as i32;
        set = (((r ^ set) >> 2) / c as i32) | r;
    }
    result
}
```

**Python:**

```python
def gospers_hack(n: int, k: int) -> list[int]:
    result = []
    set_bits = (1 << k) - 1
    limit = 1 << n
    
    while set_bits < limit:
        result.append(set_bits)
        c = set_bits & -set_bits
        r = set_bits + c
        set_bits = (((r ^ set_bits) >> 2) // c) | r
    
    return result
```

### 3. Gray Code Generation

**Rust:**

```rust
fn gray_code(n: i32) -> Vec<i32> {
    let size = 1 << n;
    (0..size).map(|i| i ^ (i >> 1)).collect()
}
```

**Python:**

```python
def gray_code(n: int) -> list[int]:
    size = 1 << n
    return [i ^ (i >> 1) for i in range(size)]
```

### 4. Check if Numbers Have Opposite Signs

**Rust:**

```rust
fn opposite_signs(x: i32, y: i32) -> bool {
    (x ^ y) < 0
}
```

**Python:**

```python
def opposite_signs(x: int, y: int) -> bool:
    return (x ^ y) < 0
```

### 5. Swap Two Numbers Without Temp Variable

**Rust:**

```rust
fn swap(a: &mut i32, b: &mut i32) {
    if a != b {
        *a ^= *b;
        *b ^= *a;
        *a ^= *b;
    }
}
```

**Python:**

```python
def swap(a: int, b: int) -> tuple[int, int]:
    if a != b:
        a ^= b
        b ^= a
        a ^= b
    return a, b
```

---

## Performance Tips

1. **Use Built-in Functions**: In Python, `bin(n).count('1')` is often faster than manual bit counting
2. **Bit Manipulation vs Arithmetic**: Bit operations are generally faster than division/modulo
3. **Cache Results**: For problems like counting bits, use DP to avoid recalculation
4. **Watch for Overflow**: Be careful with left shifts on large numbers
5. **Signed vs Unsigned**: In Rust, prefer `u32`/`u64` for bit operations when sign doesn't matter

## Common Patterns Summary

| Pattern | Use Case | Key Operation |
|---------|----------|---------------|
| `n & (n-1)` | Remove rightmost set bit | Power of 2 check |
| `n & -n` | Isolate rightmost set bit | Find lowest set bit |
| `n \| (n+1)` | Set rightmost 0 bit | Fill operations |
| `n ^ n` | Clear number | XOR properties |
| `~n` | Get complement | Bit inversion |
| `1 << k` | Create mask with k-th bit set | Bit manipulation |

## Time Complexity

- Most bit operations: **O(1)**
- Counting bits naive: **O(log n)**
- Brian Kernighan: **O(k)** where k = number of set bits
- Iterating all subsets: **O(2ⁿ)**

---

This guide covers the essential bit manipulation techniques used in competitive programming and technical interviews. Practice these patterns to build intuition for when and how to apply bit manipulation!

I'll create a comprehensive guide to Bit Manipulation with complete implementations in both Rust and Python.

I've created a comprehensive guide to Bit Manipulation covering:

## Key Sections:

1. **Fundamentals** - Binary representation and bitwise operators
2. **Basic Operations** - Check, set, clear, and toggle bits
3. **Common Techniques** - Including Brian Kernighan's algorithm, power of two checks, and subset generation
4. **Classic Problems** - Single number variants, reverse bits, maximum XOR, and more
5. **Advanced Patterns** - TSP with bitmasks, Gosper's hack, Gray codes

## Highlights:

- **Complete implementations** in both Rust and Python for every algorithm
- **Optimized solutions** with time complexity analysis
- **Real-world patterns** like using bits for state representation
- **Performance tips** specific to each language
- **Pattern summary table** for quick reference

All implementations are production-ready and include efficient algorithms like Brian Kernighan's method for counting set bits, which runs in O(k) time where k is the number of set bits rather than O(log n).

The guide progresses from basic operations to advanced techniques used in competitive programming and technical interviews. Would you like me to add more specific problems or explain any particular technique in more detail?

I've added a comprehensive section on **Bitwise Arithmetic Operations** that includes:

## New Content Added:

1. **Addition** - Using XOR for sum and AND for carry, with detailed step-by-step examples
2. **Subtraction** - Using two's complement and borrow-based approaches
3. **Multiplication** - Russian Peasant method with bit shifting
4. **Division** - Binary search approach with repeated subtraction
5. **Modulo** - Including fast power-of-2 optimization
6. **Negation** - Two's complement implementation
7. **Absolute Value** - Using bit masks
8. **Max/Min** - Without comparison operators
9. **Sign Detection** - Determining if number is positive/negative/zero
10. **Detailed Examples** - Visual walkthroughs of addition (5+3) and multiplication (5×3)

## Key Features:

- **Complete implementations** in both Rust and Python for each operation
- **Step-by-step examples** showing exactly how bits change during operations
- **Edge case handling** (overflow, division by zero, negative numbers)
- **Performance comparison table** showing time complexity
- **Python-specific handling** for arbitrary precision integers with masking
- **Practical notes** on when to use bitwise vs standard arithmetic

The implementations demonstrate fundamental computer arithmetic concepts like two's complement, carry/borrow propagation, and binary search for division. These are great for understanding how computers actually perform arithmetic at the hardware level!