Perfect 👍 let’s start with the **basic counting principles** in combinatorics that form the foundation for DSA problems.

---

## 🔹 1. Factorials

Factorial (`n!`) means the product of all positive integers from `1` to `n`.

$$
n! = n \times (n-1) \times (n-2) \times \dots \times 1
$$

* **Use:** Counting the number of ways to **arrange** or **order** objects.
* **Examples:**

  * `3! = 3 × 2 × 1 = 6` → number of ways to arrange 3 books.
  * `5! = 120` → number of ways to arrange 5 students in a line.

👉 Factorials show up directly in **permutations** and indirectly in **combinations**.

---

## 🔹 2. Fundamental Counting Principle (Multiplication Rule)

If one event can occur in `m` ways, and another independent event can occur in `n` ways, then both events together can occur in:

$$
m \times n \text{ ways}
$$

* **Example 1:**
  Choosing clothes:

  * 3 shirts, 2 pants → total = `3 × 2 = 6` outfits.Perfect 👍 let’s start with the **basic counting principles** in combinatorics that form the foundation for DSA problems.

---

## 🔹 1. Factorials

Factorial (`n!`) means the product of all positive integers from `1` to `n`.

$$
n! = n \times (n-1) \times (n-2) \times \dots \times 1
$$

* **Use:** Counting the number of ways to **arrange** or **order** objects.
* **Examples:**

  * `3! = 3 × 2 × 1 = 6` → number of ways to arrange 3 books.
  * `5! = 120` → number of ways to arrange 5 students in a line.

👉 Factorials show up directly in **permutations** and indirectly in **combinations**.

---

## 🔹 2. Fundamental Counting Principle (Multiplication Rule)

If one event can occur in `m` ways, and another independent event can occur in `n` ways, then both events together can occur in:

$$
m \times n \text{ ways}
$$

* **Example 1:**
  Choosing clothes:

  * 3 shirts, 2 pants → total = `3 × 2 = 6` outfits.

* **Example 2:**
  Password of length 3 using digits (0–9):

  * Each digit has 10 choices → `10 × 10 × 10 = 1000` passwords.

---

## 🔹 3. Addition Rule

If event A can occur in `m` ways, and event B can occur in `n` ways, and they **cannot happen together**, then the total number of ways is:

$$
m + n
$$

* **Example:**
  Choosing either a fruit or a vegetable:

  * 4 fruits, 5 vegetables → total = `4 + 5 = 9` choices.

---

## 🔹 4. Combining the Rules

You often mix **multiplication + addition**:

* **Example:**
  License plate:

  * 2 letters (26 choices each) + 2 digits (10 choices each).
  * Total = `26 × 26 × 10 × 10 = 67,600`.

---

## 🔹 Quick Coding Angle (Factorial in Code – Rust)

Since you’re practicing Rust 🚀:

```rust
fn factorial(n: u64) -> u64 {
    (1..=n).product()
}

fn main() {
    println!("5! = {}", factorial(5)); // Output: 120
}
```

Factorials are the **building block** for permutations (`n! / (n-r)!`) and combinations (`n! / (r! * (n-r)!)`).

---

👉 Next step after this would be: **Permutations and Combinations**, which extend these principles to selection/arrangement problems.

Do you want me to continue into **permutations and combinations** with simple-to-advanced examples (like subset problems, arranging letters, choosing teams)?


* **Example 2:**
  Password of length 3 using digits (0–9):

  * Each digit has 10 choices → `10 × 10 × 10 = 1000` passwords.

---

## 🔹 3. Addition Rule

If event A can occur in `m` ways, and event B can occur in `n` ways, and they **cannot happen together**, then the total number of ways is:

$$
m + n
$$

* **Example:**
  Choosing either a fruit or a vegetable:

  * 4 fruits, 5 vegetables → total = `4 + 5 = 9` choices.

---

## 🔹 4. Combining the Rules

You often mix **multiplication + addition**:

* **Example:**
  License plate:

  * 2 letters (26 choices each) + 2 digits (10 choices each).
  * Total = `26 × 26 × 10 × 10 = 67,600`.

---

## 🔹 Quick Coding Angle (Factorial in Code – Rust)

Since you’re practicing Rust 🚀:

```rust
fn factorial(n: u64) -> u64 {
    (1..=n).product()
}

fn main() {
    println!("5! = {}", factorial(5)); // Output: 120
}
```

Factorials are the **building block** for permutations (`n! / (n-r)!`) and combinations (`n! / (r! * (n-r)!)`).

---

👉 Next step after this would be: **Permutations and Combinations**, which extend these principles to selection/arrangement problems.

Do you want me to continue into **permutations and combinations** with simple-to-advanced examples (like subset problems, arranging letters, choosing teams)?

Great 🚀 Let’s go step by step into **Permutations and Combinations**, starting simple and moving toward how they’re used in **DSA problems**.

---

# 🔹 1. Permutations (Order Matters)

A **permutation** is an arrangement of objects in a specific order.

### Formula:

$$
P(n, r) = \frac{n!}{(n-r)!}
$$

* `n` = total objects
* `r` = number of objects chosen
* Order **matters**.

### Examples:

1. Number of ways to arrange 3 books on a shelf from 5 books:

$$
P(5, 3) = \frac{5!}{(5-3)!} = \frac{120}{2} = 60
$$

2. Number of 3-digit PINs (digits 0–9, no repetition):

$$
P(10, 3) = \frac{10!}{7!} = 720
$$

---

# 🔹 2. Combinations (Order Doesn’t Matter)

A **combination** is a selection of objects where order does **not** matter.

### Formula:

$$
C(n, r) = \frac{n!}{r!(n-r)!}
$$

### Examples:

1. Choosing 2 friends out of 5:

$$
C(5, 2) = \frac{5!}{2! \cdot 3!} = \frac{120}{12} = 10
$$

2. Lottery: Choosing 6 numbers out of 49 (order doesn’t matter):

$$
C(49, 6) \approx 13,983,816
$$

---

# 🔹 3. Relation Between Permutations and Combinations

$$
P(n, r) = C(n, r) \times r!
$$

👉 Meaning: First **choose** `r` objects (combination), then **arrange** them in all possible ways (factorial).

---

# 🔹 4. DSA Applications

1. **Subsets of a set (Power Set Problem)**

   * For `n` elements → `2^n` subsets.
   * Example: `{a, b, c}` → 8 subsets.

2. **String/Array permutations**

   * Generate all permutations of `"ABC"` → `"ABC", "ACB", "BAC", "BCA", "CAB", "CBA"`.

3. **Combinatorial DP Problems**

   * Ways to climb stairs (like Fibonacci).
   * Ways to partition an integer.
   * Coin change problem.

4. **Graph Algorithms**

   * Counting Hamiltonian paths (permutations).
   * Counting spanning trees (Cayley’s formula → `n^(n-2)`).

---

# 🔹 5. Coding Examples (Rust)

### Factorial Helper

```rust
fn factorial(n: u64) -> u64 {
    (1..=n).product()
}
```

### Permutations Function

```rust
fn permutation(n: u64, r: u64) -> u64 {
    factorial(n) / factorial(n - r)
}

fn main() {
    println!("P(5, 3) = {}", permutation(5, 3)); // Output: 60
}
```

### Combinations Function

```rust
fn combination(n: u64, r: u64) -> u64 {
    factorial(n) / (factorial(r) * factorial(n - r))
}

fn main() {
    println!("C(5, 2) = {}", combination(5, 2)); // Output: 10
}
```

---

✅ **Summary so far:**

* **Permutations → order matters.**
* **Combinations → order doesn’t matter.**
* Both built on **factorials** and **counting principles**.
* Extremely common in **DSA problems** (subsets, arrangements, counting paths, DP).

---

Would you like me to now take you into **classic coding interview problems** that directly use permutations & combinations (like *nCr modulo m*, *subset generation*, *arranging strings*, *binomial coefficients with DP*)?
