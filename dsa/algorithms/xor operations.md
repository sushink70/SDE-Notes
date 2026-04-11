# XOR Operations — Complete & Comprehensive Guide
### From Fundamentals to Expert-Level Mastery | C · Go · Rust

---

## Table of Contents

1. [What Is XOR? — The Foundation](#1-what-is-xor--the-foundation)
2. [Binary & Bit Representation](#2-binary--bit-representation)
3. [XOR Truth Table](#3-xor-truth-table)
4. [XOR Properties — The Laws That Make It Powerful](#4-xor-properties--the-laws-that-make-it-powerful)
5. [Bitwise XOR in Code](#5-bitwise-xor-in-code)
6. [XOR as a Toggle Switch](#6-xor-as-a-toggle-switch)
7. [Swapping Without Temporary Variable](#7-swapping-without-temporary-variable)
8. [Finding the Unique Element (Single Number)](#8-finding-the-unique-element-single-number)
9. [Finding Two Unique Elements](#9-finding-two-unique-elements)
10. [Finding Missing Number](#10-finding-missing-number)
11. [XOR and Bit Masking](#11-xor-and-bit-masking)
12. [XOR Checksum and Error Detection](#12-xor-checksum-and-error-detection)
13. [XOR Cipher (Simple Encryption)](#13-xor-cipher-simple-encryption)
14. [XOR in Power Set Generation](#14-xor-in-power-set-generation)
15. [XOR Linked List (Memory Trick)](#15-xor-linked-list-memory-trick)
16. [XOR on Arrays — Prefix XOR](#16-xor-on-arrays--prefix-xor)
17. [XOR Trie (Binary Trie for Maximum XOR)](#17-xor-trie-binary-trie-for-maximum-xor)
18. [Classic DSA Problems with XOR](#18-classic-dsa-problems-with-xor)
19. [XOR Bitmask DP](#19-xor-bitmask-dp)
20. [XOR Patterns Cheat Sheet](#20-xor-patterns-cheat-sheet)
21. [Cognitive Models for XOR Mastery](#21-cognitive-models-for-xor-mastery)

---

## 1. What Is XOR? — The Foundation

**XOR** stands for **eXclusive OR**. It is a **binary logical operation** (works on bits — the 0s and 1s that form everything in a computer).

### Vocabulary You Must Know First

| Term | Meaning |
|------|---------|
| **Bit** | The smallest unit of data: either `0` or `1` |
| **Binary** | Base-2 number system using only `0` and `1` |
| **Bitwise operation** | Applying a logical operation to each pair of corresponding bits of two numbers |
| **Operand** | The values on which an operation acts (in `a XOR b`, `a` and `b` are operands) |
| **Mask** | A bit pattern used to isolate, set, or clear specific bits |
| **Toggle** | Flip a bit: turn `0` into `1`, or `1` into `0` |

### The Core Idea

> XOR asks: **"Are these two bits DIFFERENT?"**
> - If YES (one is 0, one is 1) → result is **1**
> - If NO (both same: 0,0 or 1,1) → result is **0**

Think of it as: **"Odd number of 1s wins."**

---

## 2. Binary & Bit Representation

Before using XOR on real numbers, you must understand how numbers look in binary.

```
Decimal  Binary (8-bit)
──────── ──────────────
  0      0000 0000
  1      0000 0001
  2      0000 0010
  3      0000 0011
  4      0000 0100
  5      0000 0101
  9      0000 1001
 10      0000 1010
255      1111 1111
```

### How to Read Binary

Each position (bit) has a value that is a power of 2:

```
Position:  7    6    5    4    3    2    1    0
Value:    128   64   32   16    8    4    2    1

Example: 0000 1010 = 0+0+0+0+8+0+2+0 = 10 (decimal)
Example: 0000 1001 = 0+0+0+0+8+0+0+1 = 9  (decimal)
```

---

## 3. XOR Truth Table

The **truth table** shows every possible input combination and the result:

```
┌───────┬───────┬─────────┐
│   A   │   B   │  A XOR B │
├───────┼───────┼─────────┤
│   0   │   0   │    0    │   ← Same → 0
│   0   │   1   │    1    │   ← Different → 1
│   1   │   0   │    1    │   ← Different → 1
│   1   │   1   │    0    │   ← Same → 0
└───────┴───────┴─────────┘
```

### Full 8-bit Example: 9 XOR 10

```
  9  →  0000 1001
 10  →  0000 1010
         ─────────  (XOR each column)
  3  →  0000 0011
```

Step-by-step per column (right to left):
```
Bit 0: 1 XOR 0 = 1
Bit 1: 0 XOR 1 = 1
Bit 2: 0 XOR 0 = 0
Bit 3: 1 XOR 1 = 0
Bits 4-7: 0 XOR 0 = 0
Result: 0000 0011 = 3
```

---

## 4. XOR Properties — The Laws That Make It Powerful

These are the mathematical laws behind XOR. Memorize them; they are the engine for all XOR tricks.

### Property 1: Commutative
```
A XOR B = B XOR A
Order does NOT matter.

5 XOR 3 = 3 XOR 5 = 6
```

### Property 2: Associative
```
(A XOR B) XOR C = A XOR (B XOR C)
Grouping does NOT matter.

(5 XOR 3) XOR 2 = 5 XOR (3 XOR 2)
      6   XOR 2 = 5 XOR    1
          4    =     4     ✓
```

### Property 3: Identity Element
```
A XOR 0 = A
XOR with zero changes nothing.

7 XOR 0 = 7
```

### Property 4: Self-Inverse (The Most Important)
```
A XOR A = 0
Any number XOR itself = 0.

9 XOR 9 = 0
42 XOR 42 = 0
```

**WHY?** Because every bit XOR with itself is 0:
```
1 XOR 1 = 0
0 XOR 0 = 0
∴ all bits become 0
```

### Property 5: Involution (Reversibility)
```
(A XOR B) XOR B = A
If you XOR B twice, you get back A.

Let A=5, B=3:
5 XOR 3 = 6
6 XOR 3 = 5   ← we recovered A!
```

This is the basis for XOR encryption and the swap trick.

### Combined Law (Cancellation)
```
A XOR A XOR B = 0 XOR B = B
Duplicate values cancel out.
```

---

## 5. Bitwise XOR in Code

In C, Go, and Rust, the XOR operator symbol is `^`.

### C

```c
#include <stdio.h>
#include <stdint.h>

int main(void) {
    uint8_t a = 9;   /* 0000 1001 */
    uint8_t b = 10;  /* 0000 1010 */
    uint8_t c = a ^ b; /* 0000 0011 = 3 */

    printf("a       = %d  (binary: %08b)\n", a, a);
    printf("b       = %d  (binary: %08b)\n", b, b);
    printf("a XOR b = %d  (binary: %08b)\n", c, c);

    /* Self-inverse property */
    printf("a ^ a   = %d\n", a ^ a);   /* 0 */
    printf("a ^ 0   = %d\n", a ^ 0);   /* 9 */

    /* Reversibility: (a^b)^b == a */
    printf("(a^b)^b = %d\n", (a ^ b) ^ b); /* 9 */

    return 0;
}
```

### Go

```go
package main

import "fmt"

func main() {
    var a uint8 = 9   // 0000 1001
    var b uint8 = 10  // 0000 1010
    c := a ^ b        // 0000 0011 = 3

    fmt.Printf("a       = %d  (binary: %08b)\n", a, a)
    fmt.Printf("b       = %d  (binary: %08b)\n", b, b)
    fmt.Printf("a XOR b = %d  (binary: %08b)\n", c, c)

    // Self-inverse property
    fmt.Printf("a ^ a   = %d\n", a^a) // 0
    fmt.Printf("a ^ 0   = %d\n", a^0) // 9

    // Reversibility
    fmt.Printf("(a^b)^b = %d\n", (a^b)^b) // 9
}
```

### Rust

```rust
fn main() {
    let a: u8 = 9;   // 0000 1001
    let b: u8 = 10;  // 0000 1010
    let c = a ^ b;   // 0000 0011 = 3

    println!("a       = {:3}  (binary: {:08b})", a, a);
    println!("b       = {:3}  (binary: {:08b})", b, b);
    println!("a XOR b = {:3}  (binary: {:08b})", c, c);

    // Self-inverse property
    println!("a ^ a   = {}", a ^ a); // 0
    println!("a ^ 0   = {}", a ^ 0); // 9

    // Reversibility
    println!("(a^b)^b = {}", (a ^ b) ^ b); // 9
}
```

**Output (all three):**
```
a       =   9  (binary: 00001001)
b       =  10  (binary: 00001010)
a XOR b =   3  (binary: 00000011)
a ^ a   = 0
a ^ 0   = 9
(a^b)^b = 9
```

---

## 6. XOR as a Toggle Switch

XOR with a **mask** lets you flip specific bits ON or OFF without affecting others.

### Mental Model

```
Bit XOR 1 → flips the bit   (1→0, 0→1)
Bit XOR 0 → keeps the bit   (unchanged)
```

### Use Case: Toggle the k-th bit

To toggle bit at position `k` (0-indexed from right):
- Create mask = `1 << k`  (shifts 1 left by k positions)
- Apply `number ^ mask`

```
Toggle bit 3 of 0101 1010 (= 90):

mask for bit 3:   0000 1000  (= 1 << 3 = 8)
  90:             0101 1010
  mask:           0000 1000
  90 ^ mask:      0101 0010  (= 82)
                      ↑
                  bit 3 flipped (1 → 0)
```

### C

```c
#include <stdio.h>

/* Toggle the k-th bit (0-indexed from right) */
int toggle_bit(int n, int k) {
    return n ^ (1 << k);
}

/* Check if k-th bit is set */
int is_bit_set(int n, int k) {
    return (n >> k) & 1;
}

int main(void) {
    int n = 90; /* 0101 1010 */

    printf("Original:      %d  (binary: %08b)\n", n, n);

    /* Toggle bit 3 */
    int toggled = toggle_bit(n, 3);
    printf("Toggle bit 3:  %d  (binary: %08b)\n", toggled, toggled);

    /* Toggle back */
    int restored = toggle_bit(toggled, 3);
    printf("Toggle back:   %d  (binary: %08b)\n", restored, restored);

    /* Toggle bits 0,1,2,3 using mask 0b00001111 = 15 */
    int multi_toggled = n ^ 0x0F;
    printf("Toggle bits 0-3: %d  (binary: %08b)\n", multi_toggled, multi_toggled);

    return 0;
}
```

### Go

```go
package main

import "fmt"

// Toggle the k-th bit (0-indexed from right)
func toggleBit(n, k int) int {
    return n ^ (1 << k)
}

// Check if k-th bit is set
func isBitSet(n, k int) bool {
    return (n>>k)&1 == 1
}

func main() {
    n := 90 // 0101 1010

    fmt.Printf("Original:       %d  (binary: %08b)\n", n, n)

    toggled := toggleBit(n, 3)
    fmt.Printf("Toggle bit 3:   %d  (binary: %08b)\n", toggled, toggled)

    restored := toggleBit(toggled, 3)
    fmt.Printf("Toggle back:    %d  (binary: %08b)\n", restored, restored)

    // Toggle bits 0-3 using mask 0x0F
    multiToggled := n ^ 0x0F
    fmt.Printf("Toggle bits 0-3:%d  (binary: %08b)\n", multiToggled, multiToggled)
}
```

### Rust

```rust
fn toggle_bit(n: u32, k: u32) -> u32 {
    n ^ (1 << k)
}

fn is_bit_set(n: u32, k: u32) -> bool {
    (n >> k) & 1 == 1
}

fn main() {
    let n: u32 = 90; // 0101 1010

    println!("Original:       {:3}  (binary: {:08b})", n, n);

    let toggled = toggle_bit(n, 3);
    println!("Toggle bit 3:   {:3}  (binary: {:08b})", toggled, toggled);

    let restored = toggle_bit(toggled, 3);
    println!("Toggle back:    {:3}  (binary: {:08b})", restored, restored);

    // Toggle bits 0-3
    let multi_toggled = n ^ 0x0F;
    println!("Toggle bits 0-3:{:3}  (binary: {:08b})", multi_toggled, multi_toggled);
}
```

---

## 7. Swapping Without Temporary Variable

This is the classic XOR trick. You can swap two variables using XOR and **zero extra memory**.

### The Logic

```
Step 1: a = a XOR b
Step 2: b = b XOR a       (b XOR (a XOR b)) = a
Step 3: a = a XOR b       ((a XOR b) XOR a) = b

Proof:
Let a=5 (0101), b=3 (0011)

Step 1: a = 5^3 = 6        (0110)
Step 2: b = 3^6 = 5        (b is now 5 ✓)  [original a]
Step 3: a = 6^5 = 3        (a is now 3 ✓)  [original b]
```

**WARNING:** If `a` and `b` point to the same memory location (same variable), XOR swap makes the value 0. Always guard against this.

### C

```c
#include <stdio.h>

/* XOR swap — ONLY for distinct memory locations */
void xor_swap(int *a, int *b) {
    if (a == b) return; /* Guard: same pointer would zero out the value */
    *a ^= *b;
    *b ^= *a;
    *a ^= *b;
}

int main(void) {
    int x = 5, y = 3;
    printf("Before swap: x=%d, y=%d\n", x, y);
    xor_swap(&x, &y);
    printf("After swap:  x=%d, y=%d\n", x, y);

    /* Danger: same variable — guard protects us */
    xor_swap(&x, &x);
    printf("After self-swap (guarded): x=%d\n", x);
    return 0;
}
```

### Go

```go
package main

import "fmt"

// XOR swap for integers (Go passes by value, so we return both)
func xorSwap(a, b int) (int, int) {
    a ^= b
    b ^= a
    a ^= b
    return a, b
}

func main() {
    x, y := 5, 3
    fmt.Printf("Before: x=%d, y=%d\n", x, y)
    x, y = xorSwap(x, y)
    fmt.Printf("After:  x=%d, y=%d\n", x, y)

    // In Go, idiomatic swap is: x, y = y, x
    // The XOR version is a demonstration of the principle.
}
```

### Rust

```rust
fn xor_swap(a: &mut i32, b: &mut i32) {
    // Rust's borrow checker prevents aliasing, so same-pointer issue can't happen
    *a ^= *b;
    *b ^= *a;
    *a ^= *b;
}

fn main() {
    let mut x = 5i32;
    let mut y = 3i32;
    println!("Before: x={}, y={}", x, y);
    xor_swap(&mut x, &mut y);
    println!("After:  x={}, y={}", x, y);

    // Rust idiomatic: use std::mem::swap(a, b) in production
}
```

---

## 8. Finding the Unique Element (Single Number)

**Problem:** In an array where every element appears **exactly twice** except one, find the unique element.

### The Insight

```
If every number appears twice:
  n XOR n = 0  (pairs cancel)
  0 XOR unique = unique  (identity)

So: XOR of all elements = unique element
```

**Example:**
```
Array: [4, 1, 2, 1, 2]

4 ^ 1 = 5
5 ^ 2 = 7
7 ^ 1 = 6   (1 cancels with earlier 1)
6 ^ 2 = 4   (2 cancels with earlier 2)
Result: 4  ← the unique element ✓
```

**Time:** O(n) | **Space:** O(1)

### C

```c
#include <stdio.h>

int single_number(int *arr, int n) {
    int result = 0;
    for (int i = 0; i < n; i++) {
        result ^= arr[i];
    }
    return result;
}

int main(void) {
    int arr[] = {4, 1, 2, 1, 2};
    int n = sizeof(arr) / sizeof(arr[0]);
    printf("Unique element: %d\n", single_number(arr, n)); /* 4 */

    int arr2[] = {2, 2, 1};
    int n2 = sizeof(arr2) / sizeof(arr2[0]);
    printf("Unique element: %d\n", single_number(arr2, n2)); /* 1 */
    return 0;
}
```

### Go

```go
package main

import "fmt"

func singleNumber(nums []int) int {
    result := 0
    for _, v := range nums {
        result ^= v
    }
    return result
}

func main() {
    fmt.Println(singleNumber([]int{4, 1, 2, 1, 2})) // 4
    fmt.Println(singleNumber([]int{2, 2, 1}))        // 1
    fmt.Println(singleNumber([]int{1}))               // 1
}
```

### Rust

```rust
fn single_number(nums: &[i32]) -> i32 {
    nums.iter().fold(0, |acc, &x| acc ^ x)
}

fn main() {
    println!("{}", single_number(&[4, 1, 2, 1, 2])); // 4
    println!("{}", single_number(&[2, 2, 1]));        // 1
    println!("{}", single_number(&[1]));               // 1
}
```

> **Expert Note:** `fold` is the functional idiom for accumulation in Rust. Here we fold all elements with XOR — elegant, zero-branch, cache-friendly.

---

## 9. Finding Two Unique Elements

**Problem:** In an array where every element appears **exactly twice** except **two**, find both unique elements.

### The Strategy (Step-by-Step Expert Thinking)

```
Step 1: XOR all elements → result = a XOR b
        (all pairs cancel, leaving only the two uniques)

Step 2: Find any set bit in (a XOR b).
        A set bit means a and b DIFFER at that bit.
        We call this the "rightmost set bit" (any works).

        rightmost_set_bit = (a ^ b) & (-(a ^ b))
        This isolates the lowest set bit.

Step 3: Partition the array into two groups:
        Group 1: elements where that bit is SET
        Group 2: elements where that bit is NOT SET

        a is in one group, b is in the other.
        XOR all of group 1 → gives a (pairs cancel within group)
        XOR all of group 2 → gives b

Step 4: Done.
```

**Why does partitioning work?**
```
Both a and b differ at the chosen bit.
So a and b end up in different groups.
All paired elements (appearing twice) cancel within their group.
So each group's XOR = one of the two unique elements.
```

### Example

```
Array: [1, 2, 1, 3, 2, 5]

Step 1: 1^2^1^3^2^5 = 3^5 = 6   (011 ^ 101 = 110)

Step 2: rightmost_set_bit of 6 (110) = 010 = 2
        (bit position 1 is set)

Step 3: Group by bit 1:
        - Bit 1 is SET (value & 2 != 0): [2, 3, 2] → 2^3^2 = 3
        - Bit 1 is NOT set (value & 2 == 0): [1, 1, 5] → 1^1^5 = 5

Result: 3 and 5 ✓
```

### C

```c
#include <stdio.h>

void find_two_unique(int *arr, int n, int *out_a, int *out_b) {
    int xor_all = 0;
    for (int i = 0; i < n; i++) xor_all ^= arr[i];

    /* Isolate the rightmost set bit */
    /* (xor_all & -xor_all) works due to two's complement arithmetic */
    int diff_bit = xor_all & (-xor_all);

    *out_a = 0;
    *out_b = 0;
    for (int i = 0; i < n; i++) {
        if (arr[i] & diff_bit) {
            *out_a ^= arr[i]; /* group: bit is set */
        } else {
            *out_b ^= arr[i]; /* group: bit is not set */
        }
    }
}

int main(void) {
    int arr[] = {1, 2, 1, 3, 2, 5};
    int n = sizeof(arr) / sizeof(arr[0]);
    int a, b;
    find_two_unique(arr, n, &a, &b);
    printf("Two unique elements: %d and %d\n", a, b); /* 3 and 5 */
    return 0;
}
```

### Go

```go
package main

import "fmt"

func findTwoUnique(nums []int) (int, int) {
    xorAll := 0
    for _, v := range nums {
        xorAll ^= v
    }

    // Isolate rightmost set bit
    diffBit := xorAll & (-xorAll)

    a, b := 0, 0
    for _, v := range nums {
        if v&diffBit != 0 {
            a ^= v
        } else {
            b ^= v
        }
    }
    return a, b
}

func main() {
    a, b := findTwoUnique([]int{1, 2, 1, 3, 2, 5})
    fmt.Printf("Two unique: %d and %d\n", a, b) // 3 and 5
}
```

### Rust

```rust
fn find_two_unique(nums: &[i32]) -> (i32, i32) {
    let xor_all = nums.iter().fold(0, |acc, &x| acc ^ x);

    // Isolate the rightmost set bit using two's complement negation
    let diff_bit = xor_all & (-xor_all);

    let (mut a, mut b) = (0i32, 0i32);
    for &v in nums {
        if v & diff_bit != 0 {
            a ^= v;
        } else {
            b ^= v;
        }
    }
    (a, b)
}

fn main() {
    let (a, b) = find_two_unique(&[1, 2, 1, 3, 2, 5]);
    println!("Two unique: {} and {}", a, b); // 3 and 5
}
```

---

## 10. Finding Missing Number

**Problem:** Given array `[0, 1, 2, ..., n]` with one number missing, find it.

### Method 1: XOR Expected vs Actual

```
XOR all numbers from 0 to n → expected
XOR all elements in array → actual
expected XOR actual = missing number

(All present numbers cancel, missing one remains)
```

### Example
```
n=3, Array: [3, 0, 1]
Expected XOR: 0^1^2^3 = 0
Actual XOR:   3^0^1   = 2
0 XOR 2 = 2   ← missing number ✓
```

### C

```c
#include <stdio.h>

int find_missing(int *arr, int n) {
    /* n = length of array, actual values in [0..n] with one missing */
    int xor_expected = 0;
    int xor_actual = 0;

    for (int i = 0; i <= n; i++) xor_expected ^= i;
    for (int i = 0; i < n; i++)  xor_actual  ^= arr[i];

    return xor_expected ^ xor_actual;
}

int main(void) {
    int arr[] = {3, 0, 1}; /* missing 2, n=3 */
    int n = sizeof(arr) / sizeof(arr[0]);
    printf("Missing: %d\n", find_missing(arr, n)); /* 2 */
    return 0;
}
```

### Go

```go
package main

import "fmt"

func missingNumber(nums []int) int {
    n := len(nums)
    xorExpected, xorActual := 0, 0
    for i := 0; i <= n; i++ {
        xorExpected ^= i
    }
    for _, v := range nums {
        xorActual ^= v
    }
    return xorExpected ^ xorActual
}

func main() {
    fmt.Println(missingNumber([]int{3, 0, 1})) // 2
    fmt.Println(missingNumber([]int{0, 1}))    // 2
    fmt.Println(missingNumber([]int{9, 6, 4, 2, 3, 5, 7, 0, 1})) // 8
}
```

### Rust

```rust
fn missing_number(nums: &[usize]) -> usize {
    let n = nums.len();
    let expected: usize = (0..=n).fold(0, |acc, x| acc ^ x);
    let actual: usize = nums.iter().fold(0, |acc, &x| acc ^ x);
    expected ^ actual
}

fn main() {
    println!("{}", missing_number(&[3, 0, 1])); // 2
    println!("{}", missing_number(&[9,6,4,2,3,5,7,0,1])); // 8
}
```

---

## 11. XOR and Bit Masking

A **mask** is a carefully crafted bit pattern used to:
- **Read** specific bits (AND mask)
- **Set** specific bits (OR mask)
- **Toggle** specific bits (XOR mask)
- **Clear** specific bits (AND NOT mask)

### Reading a Bit Range with XOR

XOR with a mask is used to **toggle** a range of bits.

```
Toggle bits 4-7 (upper nibble) of 10101010:

Mask:   11110000
Value:  10101010
Result: 01011010
        ────────
        Upper nibble flipped, lower nibble unchanged
```

### Extracting Specific Bits

```
To extract bits 2-4 from 0b11011010:

Step 1: Shift right by 2: 0b00110110
Step 2: AND with mask 0b00000111: 0b00000110 = 6

The 3 bits (positions 2,3,4) of value 11011010 = 110 (binary) = 6
```

### C — Comprehensive Bit Masking

```c
#include <stdio.h>
#include <stdint.h>

/* Extract bits from position 'start' for 'len' bits */
uint32_t extract_bits(uint32_t value, int start, int len) {
    /* Create mask: len consecutive 1s */
    uint32_t mask = (1u << len) - 1;
    return (value >> start) & mask;
}

/* Toggle bits from position 'start' for 'len' bits */
uint32_t toggle_bits(uint32_t value, int start, int len) {
    uint32_t mask = ((1u << len) - 1) << start;
    return value ^ mask;
}

/* Set bit at position k */
uint32_t set_bit(uint32_t value, int k) {
    return value | (1u << k);
}

/* Clear bit at position k */
uint32_t clear_bit(uint32_t value, int k) {
    return value & ~(1u << k);
}

/* Check parity: 1 if odd number of set bits, 0 if even */
int parity(uint32_t value) {
    int p = 0;
    while (value) {
        p ^= (value & 1);
        value >>= 1;
    }
    return p;
}

int main(void) {
    uint32_t n = 0b11011010; /* 218 */

    printf("Value:            %3u  (binary: %08b)\n", n, n);
    printf("Extract bits 2-4: %3u\n", extract_bits(n, 2, 3));
    printf("Toggle bits 4-7:  %3u  (binary: %08b)\n", toggle_bits(n, 4, 4), toggle_bits(n, 4, 4));
    printf("Set bit 0:        %3u  (binary: %08b)\n", set_bit(n, 0), set_bit(n, 0));
    printf("Clear bit 1:      %3u  (binary: %08b)\n", clear_bit(n, 1), clear_bit(n, 1));
    printf("Parity:           %d\n", parity(n));

    return 0;
}
```

### Go

```go
package main

import "fmt"

func extractBits(value uint32, start, length int) uint32 {
    mask := uint32((1 << length) - 1)
    return (value >> start) & mask
}

func toggleBits(value uint32, start, length int) uint32 {
    mask := uint32(((1 << length) - 1) << start)
    return value ^ mask
}

func parity(value uint32) int {
    p := 0
    for value != 0 {
        p ^= int(value & 1)
        value >>= 1
    }
    return p
}

func main() {
    n := uint32(0b11011010) // 218

    fmt.Printf("Value:           %3d  (binary: %08b)\n", n, n)
    fmt.Printf("Extract bits 2-4:%3d\n", extractBits(n, 2, 3))
    fmt.Printf("Toggle bits 4-7: %3d  (binary: %08b)\n",
        toggleBits(n, 4, 4), toggleBits(n, 4, 4))
    fmt.Printf("Parity:          %d\n", parity(n))
}
```

### Rust

```rust
fn extract_bits(value: u32, start: u32, length: u32) -> u32 {
    let mask = (1u32 << length) - 1;
    (value >> start) & mask
}

fn toggle_bits(value: u32, start: u32, length: u32) -> u32 {
    let mask = ((1u32 << length) - 1) << start;
    value ^ mask
}

fn parity(mut value: u32) -> u32 {
    let mut p = 0u32;
    while value != 0 {
        p ^= value & 1;
        value >>= 1;
    }
    p
}

fn main() {
    let n: u32 = 0b11011010; // 218

    println!("Value:           {:3}  (binary: {:08b})", n, n);
    println!("Extract bits 2-4:{:3}", extract_bits(n, 2, 3));
    let toggled = toggle_bits(n, 4, 4);
    println!("Toggle bits 4-7: {:3}  (binary: {:08b})", toggled, toggled);
    println!("Parity:          {}", parity(n));
}
```

---

## 12. XOR Checksum and Error Detection

A **checksum** is a value computed from data to detect errors. XOR checksum is the simplest form.

### Concept

```
Transmit data: [0x4A, 0x37, 0xB2, 0xF1]
Compute XOR checksum: 0x4A ^ 0x37 ^ 0xB2 ^ 0xF1 = some byte

Append checksum to transmission.
Receiver XORs all bytes including checksum.
If result == 0 → no error.
If result != 0 → error detected.
```

### Why Does This Work?

```
Let C = a ^ b ^ c ^ d  (checksum)
Receiver computes: a ^ b ^ c ^ d ^ C
                 = C ^ C
                 = 0   ← correct

If byte b got corrupted to b':
Receiver computes: a ^ b' ^ c ^ d ^ C
                 = (a ^ b ^ c ^ d ^ C) ^ b ^ b'
                 =       0             ^ b ^ b'
                 = b ^ b'  ≠ 0  ← error!
```

### C

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>

uint8_t compute_checksum(const uint8_t *data, size_t len) {
    uint8_t checksum = 0;
    for (size_t i = 0; i < len; i++) {
        checksum ^= data[i];
    }
    return checksum;
}

int verify(const uint8_t *data, size_t len, uint8_t checksum) {
    /* XOR all bytes including checksum — should be 0 if intact */
    uint8_t result = compute_checksum(data, len) ^ checksum;
    return result == 0;
}

int main(void) {
    uint8_t data[] = {0x4A, 0x37, 0xB2, 0xF1};
    size_t len = sizeof(data);

    uint8_t checksum = compute_checksum(data, len);
    printf("Checksum: 0x%02X\n", checksum);
    printf("Verify (no error):      %s\n", verify(data, len, checksum) ? "OK" : "FAIL");

    /* Simulate bit error in data[1] */
    data[1] ^= 0x01;
    printf("Verify (with error):    %s\n", verify(data, len, checksum) ? "OK" : "FAIL");

    return 0;
}
```

### Go

```go
package main

import "fmt"

func computeChecksum(data []byte) byte {
    var cs byte
    for _, b := range data {
        cs ^= b
    }
    return cs
}

func verify(data []byte, checksum byte) bool {
    return computeChecksum(data)^checksum == 0
}

func main() {
    data := []byte{0x4A, 0x37, 0xB2, 0xF1}
    cs := computeChecksum(data)
    fmt.Printf("Checksum: 0x%02X\n", cs)
    fmt.Printf("Verify OK:     %v\n", verify(data, cs))

    // Inject error
    data[1] ^= 0x01
    fmt.Printf("Verify error:  %v\n", verify(data, cs))
}
```

### Rust

```rust
fn compute_checksum(data: &[u8]) -> u8 {
    data.iter().fold(0u8, |acc, &b| acc ^ b)
}

fn verify(data: &[u8], checksum: u8) -> bool {
    compute_checksum(data) ^ checksum == 0
}

fn main() {
    let mut data = vec![0x4Au8, 0x37, 0xB2, 0xF1];
    let cs = compute_checksum(&data);
    println!("Checksum: {:#04X}", cs);
    println!("Verify OK:     {}", verify(&data, cs));

    // Inject error
    data[1] ^= 0x01;
    println!("Verify error:  {}", verify(&data, cs));
}
```

---

## 13. XOR Cipher (Simple Encryption)

XOR is the basis for stream ciphers. The same operation both encrypts and decrypts (due to involution property).

```
Encrypt: ciphertext = plaintext XOR key
Decrypt: plaintext  = ciphertext XOR key
                    = (plaintext XOR key) XOR key
                    = plaintext XOR (key XOR key)
                    = plaintext XOR 0
                    = plaintext  ✓
```

### C

```c
#include <stdio.h>
#include <string.h>

void xor_cipher(char *text, size_t len, char key) {
    for (size_t i = 0; i < len; i++) {
        text[i] ^= key;
    }
}

int main(void) {
    char message[] = "Hello, World!";
    char key = 0x5A; /* Arbitrary key byte */
    size_t len = strlen(message);

    printf("Original:  %s\n", message);

    xor_cipher(message, len, key);
    printf("Encrypted (hex): ");
    for (size_t i = 0; i < len; i++) printf("%02X ", (unsigned char)message[i]);
    printf("\n");

    xor_cipher(message, len, key); /* Decrypt: same operation */
    printf("Decrypted: %s\n", message);

    return 0;
}
```

### Go

```go
package main

import "fmt"

func xorCipher(data []byte, key byte) []byte {
    result := make([]byte, len(data))
    for i, b := range data {
        result[i] = b ^ key
    }
    return result
}

func main() {
    plaintext := []byte("Hello, World!")
    key := byte(0x5A)

    encrypted := xorCipher(plaintext, key)
    fmt.Printf("Encrypted: % X\n", encrypted)

    decrypted := xorCipher(encrypted, key)
    fmt.Printf("Decrypted: %s\n", decrypted)
}
```

### Rust

```rust
fn xor_cipher(data: &[u8], key: u8) -> Vec<u8> {
    data.iter().map(|&b| b ^ key).collect()
}

fn main() {
    let plaintext = b"Hello, World!";
    let key = 0x5Au8;

    let encrypted = xor_cipher(plaintext, key);
    print!("Encrypted: ");
    for b in &encrypted { print!("{:02X} ", b); }
    println!();

    let decrypted = xor_cipher(&encrypted, key);
    println!("Decrypted: {}", String::from_utf8(decrypted).unwrap());
}
```

> **Security Note:** One-byte XOR cipher is easily broken (frequency analysis). Production cryptography uses XOR as a building block within much more complex ciphers (e.g., AES, ChaCha20).

---

## 14. XOR in Power Set Generation

A **power set** is the set of all possible subsets of a given set, including the empty set.

For a set of `n` elements, there are `2^n` subsets. Each integer `i` from `0` to `2^n - 1` encodes a subset via its bit pattern.

```
Set: {A, B, C}  (n=3)

i=0: 000 → {}
i=1: 001 → {C}
i=2: 010 → {B}
i=3: 011 → {B, C}
i=4: 100 → {A}
i=5: 101 → {A, C}
i=6: 110 → {A, B}
i=7: 111 → {A, B, C}
```

XOR is used here to iterate through Gray codes (each consecutive pair differs by exactly one bit), useful in Hamiltonian path problems.

### C

```c
#include <stdio.h>

void print_power_set(int *set, int n) {
    int total = 1 << n; /* 2^n subsets */
    printf("Power set (%d elements, %d subsets):\n", n, total);
    for (int mask = 0; mask < total; mask++) {
        printf("  { ");
        for (int j = 0; j < n; j++) {
            if (mask & (1 << j)) { /* Is bit j set in mask? */
                printf("%d ", set[j]);
            }
        }
        printf("}\n");
    }
}

int main(void) {
    int set[] = {10, 20, 30};
    print_power_set(set, 3);
    return 0;
}
```

### Go

```go
package main

import "fmt"

func powerSet(set []int) [][]int {
    n := len(set)
    total := 1 << n
    result := make([][]int, 0, total)

    for mask := 0; mask < total; mask++ {
        subset := []int{}
        for j := 0; j < n; j++ {
            if mask&(1<<j) != 0 {
                subset = append(subset, set[j])
            }
        }
        result = append(result, subset)
    }
    return result
}

func main() {
    subsets := powerSet([]int{10, 20, 30})
    for _, s := range subsets {
        fmt.Println(s)
    }
}
```

### Rust

```rust
fn power_set(set: &[i32]) -> Vec<Vec<i32>> {
    let n = set.len();
    let total = 1usize << n;
    let mut result = Vec::with_capacity(total);

    for mask in 0..total {
        let subset: Vec<i32> = (0..n)
            .filter(|&j| mask & (1 << j) != 0)
            .map(|j| set[j])
            .collect();
        result.push(subset);
    }
    result
}

fn main() {
    let subsets = power_set(&[10, 20, 30]);
    for s in &subsets {
        println!("{:?}", s);
    }
}
```

---

## 15. XOR Linked List (Memory Trick)

A standard doubly linked list stores two pointers per node: `prev` and `next`.

An **XOR linked list** stores only one pointer per node: `prev XOR next`.

```
Normal doubly linked:
  Node A:  prev=NULL, next=B
  Node B:  prev=A,    next=C
  Node C:  prev=B,    next=NULL

XOR linked list:
  Node A:  both = NULL ^ addr(B) = addr(B)
  Node B:  both = addr(A) ^ addr(C)
  Node C:  both = addr(B) ^ NULL = addr(B)

To traverse from A to B to C:
  At A: next = both(A) ^ prev(A) = addr(B) ^ NULL = addr(B)
  At B: next = both(B) ^ addr(A) = (addr(A)^addr(C)) ^ addr(A) = addr(C)
  At C: next = both(C) ^ addr(B) = addr(B) ^ addr(B) = NULL  ← end
```

### Why?

```
prev ^ both = prev ^ (prev ^ next) = next
```

**Space savings:** 50% reduction in pointer storage.

### C (only C supports raw pointer arithmetic like this)

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef struct Node {
    int data;
    struct Node *both; /* prev XOR next */
} Node;

/* XOR two pointers */
Node* xor_ptr(Node *a, Node *b) {
    return (Node*)((uintptr_t)a ^ (uintptr_t)b);
}

Node* new_node(int data) {
    Node *n = (Node*)malloc(sizeof(Node));
    n->data = data;
    n->both = NULL;
    return n;
}

/* Insert at front */
Node* insert_front(Node *head, int data) {
    Node *node = new_node(data);
    node->both = xor_ptr(NULL, head);
    if (head != NULL) {
        head->both = xor_ptr(node, xor_ptr(NULL, head->both));
    }
    return node;
}

/* Traverse forward */
void traverse(Node *head) {
    Node *curr = head;
    Node *prev = NULL;
    printf("XOR List: ");
    while (curr != NULL) {
        printf("%d ", curr->data);
        Node *next = xor_ptr(prev, curr->both);
        prev = curr;
        curr = next;
    }
    printf("\n");
}

int main(void) {
    Node *head = NULL;
    head = insert_front(head, 10);
    head = insert_front(head, 20);
    head = insert_front(head, 30);
    traverse(head);
    return 0;
}
```

> **Note:** XOR linked lists are primarily a C/C++ trick since they require raw pointer arithmetic. Go and Rust don't natively support this pattern (Rust's type system disallows unsafe pointer XOR in safe code).

---

## 16. XOR on Arrays — Prefix XOR

**Prefix XOR** is analogous to prefix sums, but for XOR operations.

### Vocabulary

| Term | Meaning |
|------|---------|
| **Prefix** | Everything from the beginning up to (and including) a given index |
| **Prefix XOR** | XOR of all elements from index 0 to i |

### Definition

```
prefix[0] = arr[0]
prefix[i] = prefix[i-1] ^ arr[i]

Range XOR query: xor(l, r) = prefix[r] ^ prefix[l-1]
(when l > 0)
```

### Why Does Range XOR Work?

```
prefix[r] = arr[0] ^ arr[1] ^ ... ^ arr[l-1] ^ arr[l] ^ ... ^ arr[r]
prefix[l-1] = arr[0] ^ arr[1] ^ ... ^ arr[l-1]

prefix[r] ^ prefix[l-1]:
= (arr[0]^...^arr[l-1]) ^ (arr[l]^...^arr[r]) ^ (arr[0]^...^arr[l-1])
= arr[l] ^ arr[l+1] ^ ... ^ arr[r]   ← pairs cancel!
```

### C

```c
#include <stdio.h>

void build_prefix_xor(int *arr, int *prefix, int n) {
    prefix[0] = arr[0];
    for (int i = 1; i < n; i++) {
        prefix[i] = prefix[i-1] ^ arr[i];
    }
}

/* XOR of arr[l..r] inclusive (0-indexed) */
int range_xor(int *prefix, int l, int r) {
    if (l == 0) return prefix[r];
    return prefix[r] ^ prefix[l-1];
}

int main(void) {
    int arr[] = {3, 8, 1, 6, 9, 2, 5};
    int n = sizeof(arr) / sizeof(arr[0]);
    int prefix[n];

    build_prefix_xor(arr, prefix, n);

    printf("Array:   ");
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");

    printf("Prefix:  ");
    for (int i = 0; i < n; i++) printf("%d ", prefix[i]);
    printf("\n");

    /* Query: XOR of elements from index 2 to 5 */
    printf("XOR [2..5] = %d\n", range_xor(prefix, 2, 5)); /* 1^6^9^2=14 */
    printf("XOR [0..4] = %d\n", range_xor(prefix, 0, 4)); /* 3^8^1^6^9=11 */
    return 0;
}
```

### Go

```go
package main

import "fmt"

func buildPrefixXOR(arr []int) []int {
    n := len(arr)
    prefix := make([]int, n)
    prefix[0] = arr[0]
    for i := 1; i < n; i++ {
        prefix[i] = prefix[i-1] ^ arr[i]
    }
    return prefix
}

func rangeXOR(prefix []int, l, r int) int {
    if l == 0 {
        return prefix[r]
    }
    return prefix[r] ^ prefix[l-1]
}

func main() {
    arr := []int{3, 8, 1, 6, 9, 2, 5}
    prefix := buildPrefixXOR(arr)

    fmt.Println("Array:  ", arr)
    fmt.Println("Prefix: ", prefix)
    fmt.Println("XOR [2..5]:", rangeXOR(prefix, 2, 5)) // 14
    fmt.Println("XOR [0..4]:", rangeXOR(prefix, 0, 4)) // 11
}
```

### Rust

```rust
fn build_prefix_xor(arr: &[i32]) -> Vec<i32> {
    let mut prefix = vec![0i32; arr.len()];
    prefix[0] = arr[0];
    for i in 1..arr.len() {
        prefix[i] = prefix[i-1] ^ arr[i];
    }
    prefix
}

fn range_xor(prefix: &[i32], l: usize, r: usize) -> i32 {
    if l == 0 {
        prefix[r]
    } else {
        prefix[r] ^ prefix[l-1]
    }
}

fn main() {
    let arr = [3, 8, 1, 6, 9, 2, 5];
    let prefix = build_prefix_xor(&arr);

    println!("Array:  {:?}", arr);
    println!("Prefix: {:?}", prefix);
    println!("XOR [2..5]: {}", range_xor(&prefix, 2, 5)); // 14
    println!("XOR [0..4]: {}", range_xor(&prefix, 0, 4)); // 11
}
```

---

## 17. XOR Trie (Binary Trie for Maximum XOR)

**Problem:** Given an array, find the pair of elements with the **maximum XOR value**.

### Vocabulary

| Term | Meaning |
|------|---------|
| **Trie** | A tree data structure where each node represents a prefix of values |
| **Binary Trie** | A trie with only 2 branches per node (0 and 1) |
| **MSB** | Most Significant Bit — the leftmost (highest-value) bit |

### Strategy

```
Insight: To maximize XOR of (a, b), we want each bit of a^b to be 1.
So for each bit of 'a' (from MSB to LSB), we greedily pick the OPPOSITE bit in 'b' from the trie.

Build a trie of all numbers (bit by bit, MSB first).
For each number, traverse the trie greedily choosing the opposite bit.
Track the maximum.
```

### Example

```
Array: [3, 10, 5, 25, 2, 8]
Expected maximum XOR: 28 (from 5 XOR 25 = 0101 ^ 11001 = 11100 = 28)
```

### C

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_BITS 32

typedef struct TrieNode {
    struct TrieNode *children[2];
} TrieNode;

TrieNode* new_trie_node(void) {
    TrieNode *n = (TrieNode*)calloc(1, sizeof(TrieNode));
    return n;
}

void insert(TrieNode *root, int num) {
    TrieNode *curr = root;
    for (int i = MAX_BITS - 1; i >= 0; i--) {
        int bit = (num >> i) & 1;
        if (!curr->children[bit]) {
            curr->children[bit] = new_trie_node();
        }
        curr = curr->children[bit];
    }
}

int max_xor_with(TrieNode *root, int num) {
    TrieNode *curr = root;
    int max_xor = 0;
    for (int i = MAX_BITS - 1; i >= 0; i--) {
        int bit = (num >> i) & 1;
        int want = 1 - bit; /* Want the opposite bit to maximize XOR */
        if (curr->children[want]) {
            max_xor |= (1 << i); /* This bit contributes to XOR */
            curr = curr->children[want];
        } else {
            curr = curr->children[bit]; /* Settle for same bit */
        }
    }
    return max_xor;
}

int find_maximum_xor(int *nums, int n) {
    TrieNode *root = new_trie_node();
    for (int i = 0; i < n; i++) insert(root, nums[i]);

    int result = 0;
    for (int i = 0; i < n; i++) {
        int x = max_xor_with(root, nums[i]);
        if (x > result) result = x;
    }
    return result;
}

int main(void) {
    int nums[] = {3, 10, 5, 25, 2, 8};
    int n = sizeof(nums) / sizeof(nums[0]);
    printf("Maximum XOR: %d\n", find_maximum_xor(nums, n)); /* 28 */
    return 0;
}
```

### Go

```go
package main

import "fmt"

const maxBits = 32

type TrieNode struct {
    children [2]*TrieNode
}

func insert(root *TrieNode, num int) {
    curr := root
    for i := maxBits - 1; i >= 0; i-- {
        bit := (num >> i) & 1
        if curr.children[bit] == nil {
            curr.children[bit] = &TrieNode{}
        }
        curr = curr.children[bit]
    }
}

func maxXorWith(root *TrieNode, num int) int {
    curr := root
    result := 0
    for i := maxBits - 1; i >= 0; i-- {
        bit := (num >> i) & 1
        want := 1 - bit
        if curr.children[want] != nil {
            result |= 1 << i
            curr = curr.children[want]
        } else {
            curr = curr.children[bit]
        }
    }
    return result
}

func findMaximumXOR(nums []int) int {
    root := &TrieNode{}
    for _, n := range nums {
        insert(root, n)
    }
    result := 0
    for _, n := range nums {
        if x := maxXorWith(root, n); x > result {
            result = x
        }
    }
    return result
}

func main() {
    fmt.Println(findMaximumXOR([]int{3, 10, 5, 25, 2, 8})) // 28
}
```

### Rust

```rust
#[derive(Default)]
struct TrieNode {
    children: [Option<Box<TrieNode>>; 2],
}

struct XorTrie {
    root: TrieNode,
}

impl XorTrie {
    fn new() -> Self {
        XorTrie { root: TrieNode::default() }
    }

    fn insert(&mut self, num: i32) {
        let mut curr = &mut self.root;
        for i in (0..32).rev() {
            let bit = ((num >> i) & 1) as usize;
            if curr.children[bit].is_none() {
                curr.children[bit] = Some(Box::new(TrieNode::default()));
            }
            curr = curr.children[bit].as_mut().unwrap();
        }
    }

    fn max_xor_with(&self, num: i32) -> i32 {
        let mut curr = &self.root;
        let mut result = 0i32;
        for i in (0..32).rev() {
            let bit = ((num >> i) & 1) as usize;
            let want = 1 - bit;
            if curr.children[want].is_some() {
                result |= 1 << i;
                curr = curr.children[want].as_ref().unwrap();
            } else if curr.children[bit].is_some() {
                curr = curr.children[bit].as_ref().unwrap();
            } else {
                break;
            }
        }
        result
    }
}

fn find_maximum_xor(nums: &[i32]) -> i32 {
    let mut trie = XorTrie::new();
    for &n in nums { trie.insert(n); }
    nums.iter().map(|&n| trie.max_xor_with(n)).max().unwrap_or(0)
}

fn main() {
    println!("{}", find_maximum_xor(&[3, 10, 5, 25, 2, 8])); // 28
}
```

**Time Complexity:** O(n × 32) = O(n) | **Space:** O(n × 32) = O(n)

---

## 18. Classic DSA Problems with XOR

### Problem 1: Count Pairs with XOR in a Given Range

**Problem:** Count pairs (i, j) where i < j and `arr[i] XOR arr[j]` lies within [L, R].

**Strategy:** Use prefix XOR + counting. For each element, XOR it against all previous elements and count those in [L, R].

### C

```c
#include <stdio.h>

int count_pairs_xor_range(int *arr, int n, int L, int R) {
    int count = 0;
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            int xval = arr[i] ^ arr[j];
            if (xval >= L && xval <= R) count++;
        }
    }
    return count;
}

int main(void) {
    int arr[] = {1, 2, 3, 4};
    int n = sizeof(arr) / sizeof(arr[0]);
    printf("Pairs with XOR in [2,3]: %d\n",
           count_pairs_xor_range(arr, n, 2, 3)); /* 2: (1^2=3), (1^3=2) */
    return 0;
}
```

---

### Problem 2: Longest Subarray with XOR = 0

**Problem:** Find the longest subarray whose XOR equals 0.

**Strategy:** Use prefix XOR and a hash map. If prefix[i] == prefix[j], then XOR of arr[i+1..j] == 0.

### Go

```go
package main

import "fmt"

func longestSubarrayXorZero(arr []int) int {
    // Map: prefix_xor → first index where this prefix occurred
    firstSeen := map[int]int{0: -1} // XOR of empty prefix is 0, at index -1
    prefXOR := 0
    maxLen := 0

    for i, v := range arr {
        prefXOR ^= v
        if j, ok := firstSeen[prefXOR]; ok {
            if i-j > maxLen {
                maxLen = i - j
            }
        } else {
            firstSeen[prefXOR] = i
        }
    }
    return maxLen
}

func main() {
    arr := []int{1, 2, 3, 1, 2, 3, 4}
    fmt.Println("Longest subarray with XOR=0:", longestSubarrayXorZero(arr)) // 6
}
```

---

### Problem 3: Find Subarray with Given XOR

**Problem:** Count subarrays with XOR equal to a target K.

**Strategy:** Prefix XOR + hashmap. If `prefix[j] ^ prefix[i-1] = K`, then `prefix[i-1] = prefix[j] ^ K`.

### Rust

```rust
use std::collections::HashMap;

fn count_subarrays_with_xor(arr: &[i32], k: i32) -> i32 {
    let mut freq: HashMap<i32, i32> = HashMap::new();
    freq.insert(0, 1); // Empty prefix has XOR 0
    let mut prefix_xor = 0;
    let mut count = 0;

    for &v in arr {
        prefix_xor ^= v;
        // Look for prefix_xor ^ k in the map
        let needed = prefix_xor ^ k;
        count += freq.get(&needed).copied().unwrap_or(0);
        *freq.entry(prefix_xor).or_insert(0) += 1;
    }
    count
}

fn main() {
    let arr = [4, 2, 2, 6, 4];
    println!("Subarrays with XOR=6: {}", count_subarrays_with_xor(&arr, 6)); // 4
}
```

---

## 19. XOR Bitmask DP

**Bitmask DP** uses an integer as a set of flags (a bitmask) to represent which elements have been "used." XOR is central to many such problems.

### Vocabulary

| Term | Meaning |
|------|---------|
| **Bitmask** | An integer whose bits encode a set of chosen elements |
| **State** | A (mask, index) pair encoding which elements are used and current position |
| **Transition** | Moving from one DP state to another by making a choice |

### Problem: Maximum XOR Subset Sum

**Problem:** Among all subsets, find the subset with the maximum possible XOR value.

**Strategy (Gaussian Elimination / Linear Basis):**
```
Maintain a "basis" of numbers. A basis is a set of numbers such that
any XOR combination of the original set can be built from them.

The largest XOR reachable is found by greedily picking basis elements.
```

### C — Linear Basis (XOR Basis)

```c
#include <stdio.h>
#include <string.h>

#define BITS 30

int basis[BITS];
int sz = 0;

void insert_basis(int x) {
    for (int i = BITS - 1; i >= 0; i--) {
        if (!((x >> i) & 1)) continue; /* Skip if this bit is 0 */
        if (!basis[i]) {
            basis[i] = x;
            sz++;
            return;
        }
        x ^= basis[i]; /* Reduce x using existing basis element */
    }
    /* x became 0: already representable by current basis */
}

int max_xor_subset(int *arr, int n) {
    memset(basis, 0, sizeof(basis));
    sz = 0;
    for (int i = 0; i < n; i++) insert_basis(arr[i]);

    int result = 0;
    for (int i = BITS - 1; i >= 0; i--) {
        if ((result ^ basis[i]) > result) {
            result ^= basis[i];
        }
    }
    return result;
}

int main(void) {
    int arr[] = {3, 7, 90, 1, 4};
    int n = sizeof(arr) / sizeof(arr[0]);
    printf("Max XOR subset: %d\n", max_xor_subset(arr, n)); /* 95 */
    return 0;
}
```

### Go

```go
package main

import "fmt"

const bits = 30

type XORBasis struct {
    basis [bits]int
}

func (b *XORBasis) Insert(x int) {
    for i := bits - 1; i >= 0; i-- {
        if (x>>i)&1 == 0 {
            continue
        }
        if b.basis[i] == 0 {
            b.basis[i] = x
            return
        }
        x ^= b.basis[i]
    }
}

func (b *XORBasis) MaxXOR() int {
    result := 0
    for i := bits - 1; i >= 0; i-- {
        if result^b.basis[i] > result {
            result ^= b.basis[i]
        }
    }
    return result
}

func main() {
    arr := []int{3, 7, 90, 1, 4}
    var basis XORBasis
    for _, v := range arr {
        basis.Insert(v)
    }
    fmt.Println("Max XOR subset:", basis.MaxXOR()) // 95
}
```

### Rust

```rust
const BITS: usize = 30;

struct XorBasis {
    basis: [i32; BITS],
}

impl XorBasis {
    fn new() -> Self {
        XorBasis { basis: [0; BITS] }
    }

    fn insert(&mut self, mut x: i32) {
        for i in (0..BITS).rev() {
            if (x >> i) & 1 == 0 { continue; }
            if self.basis[i] == 0 {
                self.basis[i] = x;
                return;
            }
            x ^= self.basis[i];
        }
    }

    fn max_xor(&self) -> i32 {
        let mut result = 0i32;
        for i in (0..BITS).rev() {
            if result ^ self.basis[i] > result {
                result ^= self.basis[i];
            }
        }
        result
    }
}

fn main() {
    let arr = [3, 7, 90, 1, 4];
    let mut basis = XorBasis::new();
    for &v in &arr { basis.insert(v); }
    println!("Max XOR subset: {}", basis.max_xor()); // 95
}
```

---

## 20. XOR Patterns Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────────┐
│                        XOR PATTERNS                                 │
├──────────────────────────┬──────────────────────────────────────────┤
│ Pattern                  │ Formula / Use                            │
├──────────────────────────┼──────────────────────────────────────────┤
│ Toggle bit k             │ n ^ (1 << k)                            │
│ Check bit k              │ (n >> k) & 1                            │
│ Swap two vars            │ a^=b; b^=a; a^=b                        │
│ Self-cancel              │ n ^ n = 0                               │
│ Identity                 │ n ^ 0 = n                               │
│ Reversibility            │ (a^b)^b = a                             │
│ Unique in pairs          │ XOR all → unique remains                │
│ Missing number           │ XOR expected ^ XOR actual               │
│ Rightmost set bit        │ n & (-n)                                │
│ Remove rightmost set bit │ n & (n - 1)                             │
│ All bits set (n bits)    │ (1 << n) - 1                            │
│ Range XOR [l..r]         │ prefix[r] ^ prefix[l-1]                 │
│ Parity (odd bits set?)   │ fold ^ all bits                         │
│ Bit count trick (parity) │ n ^ (n >> 1) (Gray code)                │
│ Encrypt/Decrypt          │ text ^ key (same op for both)           │
│ Power set mask           │ for mask in 0..2^n                      │
│ XOR basis (max subset)   │ Gaussian elimination over GF(2)         │
│ Two uniques              │ XOR all → diff_bit → two groups         │
└──────────────────────────┴──────────────────────────────────────────┘
```

### Common Bit Tricks That Use XOR

```c
/* 1. Check if n is a power of 2 */
int is_power_of_2 = n > 0 && (n & (n - 1)) == 0;

/* 2. Isolate rightmost set bit */
int rightmost = n & (-n);

/* 3. Gray code: convert index to gray code */
int gray = n ^ (n >> 1);

/* 4. Inverse gray: gray code to index */
int inverse_gray(int gray) {
    int n = gray;
    while (gray >>= 1) n ^= gray;
    return n;
}

/* 5. Count set bits (Brian Kernighan's) */
int count_bits = 0;
while (n) { n &= n - 1; count_bits++; }
```

---

## 21. Cognitive Models for XOR Mastery

### Mental Model 1: The "Difference Detector"

> XOR = "Are these different?"

Apply this mental model to **any** XOR question. When you see XOR, ask: "What differences are we detecting and what cancels out?"

### Mental Model 2: The Parity Counter

> XOR across many values = "Is the count of 1s in this bit position odd or even?"

For each bit position independently, XOR counts parity. This is why pairs cancel and uniques survive.

### Mental Model 3: The Reversible Door

> XOR is a door: open it twice and you're back where you started.

Encryption, swap, and range queries all exploit this reversibility.

### Mental Model 4: The Partition Tool

> A single differing bit divides the world into two camps.

When you have `a XOR b` and need to separate them, find the differing bit and use it to partition the array. This is the two-uniques pattern.

### Chunking Strategy for XOR Problems

When you see a XOR problem, run through this mental checklist:

```
1. What cancels?  (pairs, duplicates, repeated elements)
2. What survives? (uniques, missing, different)
3. Can I use prefix XOR for range queries?
4. Should I build a trie for maximum XOR?
5. Is there a basis/linear algebra angle (max XOR subset)?
6. Can I use bitmask to represent subsets?
```

### The "Think in Bits" Discipline

The top 1% of competitive programmers mentally simulate bit columns **independently**. Train yourself to look at any XOR expression and immediately visualize a table of bit positions and how each one behaves independently.

```
When you see: a ^ b ^ c ^ d

Think:
  Bit 0: (a₀ XOR b₀ XOR c₀ XOR d₀) = ?
  Bit 1: (a₁ XOR b₁ XOR c₁ XOR d₁) = ?
  ...
  Each bit is an independent story.
```

---

## Summary Table: Time & Space Complexities

```
┌────────────────────────────────────────┬─────────────┬────────────┐
│ Algorithm                              │ Time        │ Space      │
├────────────────────────────────────────┼─────────────┼────────────┤
│ XOR of array (single unique)           │ O(n)        │ O(1)       │
│ Two unique elements                    │ O(n)        │ O(1)       │
│ Missing number                         │ O(n)        │ O(1)       │
│ Range XOR (after O(n) preprocessing)   │ O(1)        │ O(n)       │
│ Maximum XOR pair (trie)                │ O(n × 32)   │ O(n × 32) │
│ Max XOR subset (linear basis)          │ O(n × 30)   │ O(30)     │
│ Subarray XOR = K (hashmap)             │ O(n)        │ O(n)       │
│ Longest XOR=0 subarray                 │ O(n)        │ O(n)       │
│ Power set enumeration                  │ O(2ⁿ × n)   │ O(2ⁿ)     │
└────────────────────────────────────────┴─────────────┴────────────┘
```

---

*"Mastery is not about memorizing tricks — it is about seeing the single principle (cancellation through identity) expressed in a thousand different forms."*

---

**End of Guide** | C · Go · Rust | XOR Operations — Complete Reference

Now let me create the comprehensive XOR guide:Here is your complete XOR guide — 21 chapters, fully structured. Here's what's covered:

**Foundations → Properties → Tricks → DSA Patterns → Expert Algorithms**

The guide is built in this progression:

1. **Foundations** — what a bit is, what XOR means, truth table, binary representation
2. **The 5 Laws** — commutative, associative, identity, self-inverse, involution — these are the engine of every XOR trick
3. **Classic Tricks** — toggle, swap, toggle-mask
4. **Single/Two Uniques & Missing Number** — the cancellation pattern (O(n) time, O(1) space)
5. **Prefix XOR** — analogous to prefix sums; enables O(1) range XOR queries
6. **XOR Trie** — binary trie for maximum XOR pair in O(n × 32)
7. **XOR Linear Basis** — Gaussian elimination over GF(2) for max XOR subset
8. **Bitmask DP patterns** — power sets, subset enumeration
9. **Practical Applications** — checksum/error detection, XOR cipher
10. **Cheat Sheet + Complexity Table** — for rapid recall

**One core insight to internalize:**
> Every XOR problem is either about *what cancels* (pairs → 0) or *what survives* (the difference, the unique, the missing). Once you see that, patterns unlock themselves.