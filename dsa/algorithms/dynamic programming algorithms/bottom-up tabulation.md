**Bottom-Up Tabulation** is a **Dynamic Programming (DP)** technique where we solve a problem **iteratively**, starting from the **base cases** and building up the solution to larger subproblems — ultimately reaching the **final answer**.

It’s called **“bottom-up”** because we begin from the *smallest possible inputs* (the bottom of the problem) and *build up* the table toward the desired result (the top).

---

### 🧩 Core Idea

Instead of using recursion (like in **Top-Down Memoization**), we **fill a table iteratively** — usually an array or matrix — to store the results of subproblems.
Each entry depends only on previously computed values, which means we **avoid recursion and repeated computation**.

---

### 🧠 Intuitive Example — Fibonacci Numbers

#### Top-Down (Recursive + Memoization)

You compute `fib(n)` by calling `fib(n-1)` and `fib(n-2)` recursively.
You store (memoize) results so you don’t recompute them.

#### Bottom-Up (Tabulation)

You start from the smallest known cases:

```
fib(0) = 0  
fib(1) = 1
```

Then you *iteratively* compute all values up to `fib(n)`.

---

### 💻 Example in Python

```python
def fibonacci_bottom_up(n):
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[0], dp[1] = 0, 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    
    return dp[n]
```

✅ **How this works:**

* `dp[i]` represents the value of `fib(i)`.
* Each iteration uses only `dp[i-1]` and `dp[i-2]` (already computed).
* No recursion → no stack overhead.

---

### 🧮 Space Optimization Trick

Since Fibonacci only needs the last two values, we can reduce space from **O(n)** to **O(1)**:

```python
def fibonacci_optimized(n):
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    for _ in range(2, n + 1):
        curr = prev1 + prev2
        prev2, prev1 = prev1, curr
    
    return prev1
```

---

### ⚙️ Memory & Performance

| Aspect               | Top-Down (Memoization)    | Bottom-Up (Tabulation)                        |
| -------------------- | ------------------------- | --------------------------------------------- |
| **Approach**         | Recursive                 | Iterative                                     |
| **Space**            | O(n) for recursion + memo | O(n) for table (can optimize to O(1))         |
| **Speed**            | Similar (O(n))            | Often slightly faster (no recursion overhead) |
| **Order of Solving** | Demand-driven             | Sequential (from base cases up)               |

---

### 🧩 When to Use Bottom-Up

* When subproblem dependencies are **known and straightforward**.
* When recursion depth could cause **stack overflow**.
* When you want **tight control** over time and space usage.

---

### 🪜 Quick Analogy

Think of **Top-Down** as *looking up a recipe when you need it*, caching the results,
and **Bottom-Up** as *preparing all ingredients in advance* so you can instantly serve the dish.

---

Would you like me to show how **Bottom-Up Tabulation** works **step by step** in the call flow — with stack/heap memory visualization — for Fibonacci or another DP problem like **0/1 Knapsack**?

Yes, you can absolutely use a **memo** (a table or array to store computed results) in bottom-up DP — in fact, it's the standard way bottom-up DP is implemented. 

The confusion often comes from terminology:
- **Top-down DP** uses recursion + memoization (caching results of recursive calls).
- **Bottom-up DP** uses iteration + tabulation (filling a table iteratively from smaller subproblems to larger ones).

That table in bottom-up DP *is* a memo — it stores previously computed values to avoid recomputation. So bottom-up DP does use a memo, just in an iterative rather than recursive fashion.

### Example: Fibonacci
**Bottom-up with memo (table):**
```python
def fib(n):
    memo = [0] * (n+1)
    memo[1] = 1
    for i in range(2, n+1):
        memo[i] = memo[i-1] + memo[i-2]
    return memo[n]
```
Here `memo` is the DP table.

### Key takeaway
- If by "memo" you mean *any data structure that stores solved subproblem results*, then bottom-up DP always uses one.
- If you specifically mean *the recursive caching technique* (calling the function recursively and storing results), then bottom-up doesn't use recursion, so that exact technique doesn't apply — but the underlying idea of remembering past computations is identical.

So the short answer: **Yes, it's not only possible but standard.**