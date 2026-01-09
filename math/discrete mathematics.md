# The Foundation of Computational Thought: A Comprehensive Guide to Discrete Mathematics

*"Mathematics is the language in which the universe is written, but discrete mathematics is the grammar of computation itself."*

---

## Preface: Why Discrete Mathematics is Your Algorithmic Bedrock

Before we begin, understand this: **every sophisticated algorithm you'll master stands on discrete mathematics**. While continuous mathematics deals with smooth curves and infinitesimals, discrete mathematics operates on the countable, the distinct, the *computational*. It's the difference between measuring water flow (calculus) and counting individual water molecules (discrete math).

Your journey to the top 1% requires you to think in discrete structures instinctively. Let's build that foundation with monk-like precision.

---

## I. Logic and Proof Techniques: The Language of Rigorous Thought

### 1.1 Propositional Logic

**Core Concept**: Propositions are statements that are either true or false, never both.

**Fundamental Operators**:
- **Negation (¬)**: NOT
- **Conjunction (∧)**: AND
- **Disjunction (∨)**: OR
- **Implication (→)**: IF...THEN
- **Biconditional (↔)**: IF AND ONLY IF

**Truth Tables** are your first mental model for evaluating logical expressions:

```
P | Q | P∧Q | P∨Q | P→Q | P↔Q
--|---|-----|-----|-----|-----
T | T |  T  |  T  |  T  |  T
T | F |  F  |  T  |  F  |  F
F | T |  F  |  T  |  T  |  F
F | F |  F  |  F  |  T  |  T
```

**Critical Insight**: The implication P→Q is only false when P is true and Q is false. This counterintuitive fact underlies proof by contrapositive.

**Algorithmic Application**:
- **Short-circuit evaluation** in conditionals exploits conjunction/disjunction properties
- **Branch prediction** in modern CPUs relies on logical expression patterns
- **SAT solvers** (used in verification, AI planning) operate on propositional logic

**Example in Rust** (demonstrating De Morgan's Laws):
```rust
// De Morgan's Law: ¬(P ∧ Q) ≡ (¬P ∨ ¬Q)
fn validate_input(x: i32, y: i32) -> bool {
    // Instead of: !(x > 0 && y > 0)
    // Equivalent: x <= 0 || y <= 0
    x <= 0 || y <= 0  // More readable, same logic
}
```

### 1.2 Predicate Logic (First-Order Logic)

**Extension**: Adds quantifiers and predicates over domains.

**Quantifiers**:
- **Universal (∀)**: "for all"
- **Existential (∃)**: "there exists"

**Example**: ∀x ∈ ℕ, ∃y ∈ ℕ such that y > x
("For every natural number, there exists a larger natural number")

**Algorithmic Connection**:
```python
# Universal quantifier → all()
def all_positive(arr: list[int]) -> bool:
    return all(x > 0 for x in arr)  # ∀x ∈ arr, x > 0

# Existential quantifier → any()
def has_even(arr: list[int]) -> bool:
    return any(x % 2 == 0 for x in arr)  # ∃x ∈ arr, x is even
```

### 1.3 Proof Techniques: The Warrior's Arsenal

**1. Direct Proof**
- Assume premises, apply logical steps, reach conclusion
- *Example*: Prove that the sum of two even integers is even
  - Let a = 2m, b = 2n (definition of even)
  - a + b = 2m + 2n = 2(m + n)
  - Therefore even by definition ∎

**2. Proof by Contrapositive**
- To prove P→Q, prove ¬Q→¬P (logically equivalent)
- *Powerful when the contrapositive is simpler*

**3. Proof by Contradiction**
- Assume ¬Q, derive a contradiction
- *Example*: Prove √2 is irrational (classic)

**4. Mathematical Induction** (detailed in Section II)

**5. Proof by Construction**
- Prove existence by building the object
- *Common in algorithm correctness proofs*

**Mental Model**: Think of proofs as **deterministic algorithms that transform axioms into theorems**. Each step must be justified, like each line of code must compile.

---

## II. Mathematical Induction: The Recursive Proof Paradigm

**Philosophy**: Induction is to proofs what recursion is to algorithms. Master one, master both.

### 2.1 Principle of Mathematical Induction

To prove P(n) is true for all n ≥ n₀:

1. **Base Case**: Prove P(n₀) is true
2. **Inductive Hypothesis**: Assume P(k) is true for arbitrary k ≥ n₀
3. **Inductive Step**: Prove P(k+1) is true using P(k)

**Why it works**: Like dominos falling. If the first falls (base case) and each falling domino knocks the next (inductive step), all fall.

### 2.2 Example: Sum of First n Natural Numbers

**Claim**: 1 + 2 + 3 + ... + n = n(n+1)/2

**Proof**:
- *Base*: n=1, sum = 1 = 1(2)/2 ✓
- *Hypothesis*: Assume true for k: 1+2+...+k = k(k+1)/2
- *Step*: Prove for k+1:
  ```
  1+2+...+k+(k+1) = [k(k+1)/2] + (k+1)    [by hypothesis]
                   = (k+1)[k/2 + 1]
                   = (k+1)(k+2)/2 ✓
  ```

**Algorithmic Parallel**:
```rust
fn sum_iterative(n: u64) -> u64 {
    (n * (n + 1)) / 2  // O(1) using formula
}

fn sum_recursive(n: u64) -> u64 {
    match n {
        0 => 0,                          // Base case
        k => k + sum_recursive(k - 1)    // Inductive step
    }
}
```

### 2.3 Strong Induction

**Difference**: Assume P(1), P(2), ..., P(k) all true when proving P(k+1).

**When to use**: When proving P(k+1) needs multiple previous cases (like Fibonacci).

**Example**: Every integer n ≥ 2 is expressible as a product of primes.
- Base: 2 is prime ✓
- Strong hypothesis: True for all m where 2 ≤ m ≤ k
- Step: If k+1 is prime, done. Else k+1 = ab where 2 ≤ a,b ≤ k. By hypothesis, both are products of primes, so k+1 is too ✓

---

## III. Set Theory: The Universe of Discrete Objects

### 3.1 Fundamental Concepts

**Set**: An unordered collection of distinct elements.

**Notation**:
- A = {1, 2, 3} (enumeration)
- B = {x ∈ ℤ | x² < 10} (set-builder)
- ∅ = {} (empty set)

**Operations**:
- **Union**: A ∪ B = {x | x ∈ A ∨ x ∈ B}
- **Intersection**: A ∩ B = {x | x ∈ A ∧ x ∈ B}
- **Difference**: A \ B = {x | x ∈ A ∧ x ∉ B}
- **Complement**: Ā = {x ∈ U | x ∉ A} (U is universal set)
- **Cartesian Product**: A × B = {(a,b) | a ∈ A, b ∈ B}

**Power Set**: P(A) = set of all subsets of A
- |P(A)| = 2^|A|

### 3.2 Set Identities (Laws of Set Algebra)

Master these like muscle memory:

1. **Commutative**: A ∪ B = B ∪ A, A ∩ B = B ∩ A
2. **Associative**: (A ∪ B) ∪ C = A ∪ (B ∪ C)
3. **Distributive**: A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)
4. **De Morgan's**: (A ∪ B)' = A' ∩ B', (A ∩ B)' = A' ∪ B'
5. **Absorption**: A ∪ (A ∩ B) = A

**Algorithmic Implementation** (Python):
```python
# Sets in Python provide O(1) average-case membership testing
A = {1, 2, 3, 4}
B = {3, 4, 5, 6}

union = A | B           # {1, 2, 3, 4, 5, 6}
intersection = A & B    # {3, 4}
difference = A - B      # {1, 2}
symmetric_diff = A ^ B  # {1, 2, 5, 6} (elements in exactly one set)
```

### 3.3 Relations and Functions

**Relation**: R ⊆ A × B (subset of Cartesian product)

**Properties of Relations on a Set A**:
1. **Reflexive**: ∀a ∈ A, (a,a) ∈ R
2. **Symmetric**: (a,b) ∈ R → (b,a) ∈ R
3. **Transitive**: (a,b) ∈ R ∧ (b,c) ∈ R → (a,c) ∈ R
4. **Antisymmetric**: (a,b) ∈ R ∧ (b,a) ∈ R → a = b

**Equivalence Relation**: Reflexive + Symmetric + Transitive
- *Creates partitions* (disjoint union of equivalence classes)
- **Algorithm**: Union-Find exploits equivalence relations

**Partial Order**: Reflexive + Antisymmetric + Transitive
- **Algorithm**: Topological sort operates on partial orders

**Function**: f: A → B where each a ∈ A maps to exactly one b ∈ B
- **Injective** (one-to-one): f(a₁) = f(a₂) → a₁ = a₂
- **Surjective** (onto): ∀b ∈ B, ∃a ∈ A such that f(a) = b
- **Bijective**: Both injective and surjective (perfect pairing)

---

## IV. Combinatorics: The Art of Counting

*"If you can count it, you can optimize it."*

### 4.1 Fundamental Counting Principles

**1. Rule of Sum**: If A and B are disjoint, |A ∪ B| = |A| + |B|

**2. Rule of Product**: |A × B| = |A| × |B|

**Example**: Counting binary strings of length n
- At each position: 2 choices (0 or 1)
- Total: 2 × 2 × ... × 2 = 2ⁿ

### 4.2 Permutations and Combinations

**Permutation**: Ordered arrangement
- P(n, r) = n!/(n-r)! (r items from n, order matters)
- P(n, n) = n! (all items)

**Combination**: Unordered selection
- C(n, r) = n!/(r!(n-r)!) = (n choose r)

**Mnemonic**: **P**ermutation → **P**osition matters, **C**ombination → **C**ollection (order doesn't matter)

**Example in C++** (computing combinations):
```cpp
// Efficient computation using Pascal's Triangle property
// C(n,r) = C(n-1,r-1) + C(n-1,r)
long long binomial(int n, int r) {
    if (r > n - r) r = n - r;  // C(n,r) = C(n,n-r), optimize
    long long result = 1;
    for (int i = 0; i < r; ++i) {
        result *= (n - i);
        result /= (i + 1);
    }
    return result;  // O(min(r, n-r))
}
```

### 4.3 Advanced Counting: The Pigeonhole Principle

**Statement**: If n pigeons occupy m holes and n > m, at least one hole contains ≥ 2 pigeons.

**Generalized**: If n pigeons in m holes, at least one hole has ≥ ⌈n/m⌉ pigeons.

**Algorithmic Applications**:
1. **Hash collisions** are inevitable (pigeons = keys, holes = buckets)
2. **Birthday paradox**: In a group of 23 people, >50% chance two share a birthday
3. **Finding duplicates**: In array of n+1 elements from [1,n], at least one duplicate exists

**Example Problem**: In any sequence of n²+1 distinct integers, there exists either an increasing or decreasing subsequence of length n+1.

### 4.4 Inclusion-Exclusion Principle

**Formula**: |A₁ ∪ A₂ ∪ ... ∪ Aₙ| = Σ|Aᵢ| - Σ|Aᵢ ∩ Aⱼ| + Σ|Aᵢ ∩ Aⱼ ∩ Aₖ| - ...

**Two sets**: |A ∪ B| = |A| + |B| - |A ∩ B|

**Application**: Count integers in [1,100] divisible by 2 or 3
- |A| = 50 (divisible by 2)
- |B| = 33 (divisible by 3)
- |A ∩ B| = 16 (divisible by 6)
- |A ∪ B| = 50 + 33 - 16 = 67

**Algorithm**: Used in sieve methods, counting distinct elements

---

## V. Graph Theory: The Science of Connections

### 5.1 Fundamental Definitions

**Graph G = (V, E)**: 
- V = set of vertices (nodes)
- E = set of edges (connections)

**Types**:
- **Undirected**: Edges have no direction
- **Directed** (Digraph): Edges have direction
- **Weighted**: Edges have numerical values
- **Simple**: No self-loops or multiple edges

**Representations**:
```rust
// Adjacency Matrix: O(V²) space, O(1) edge lookup
type AdjMatrix = Vec<Vec<bool>>;

// Adjacency List: O(V+E) space, O(degree) neighbor iteration
type AdjList = Vec<Vec<usize>>;

// Edge List: O(E) space, good for sparse graphs
type EdgeList = Vec<(usize, usize)>;

// Example: Adjacency list for undirected graph
fn create_graph(n: usize, edges: &[(usize, usize)]) -> AdjList {
    let mut graph = vec![vec![]; n];
    for &(u, v) in edges {
        graph[u].push(v);
        graph[v].push(u);  // Bidirectional
    }
    graph
}
```

### 5.2 Graph Properties

**Degree**:
- Undirected: deg(v) = number of edges incident to v
- Directed: in-degree + out-degree

**Handshaking Lemma**: Σ deg(v) = 2|E| (sum of degrees is even)

**Path**: Sequence of vertices where consecutive pairs are connected
- **Simple path**: No repeated vertices
- **Cycle**: Path that starts and ends at same vertex

**Connectivity**:
- **Connected graph** (undirected): Path exists between any two vertices
- **Strongly connected** (directed): Directed path exists between any two vertices

### 5.3 Special Graph Classes

**1. Trees**: Connected acyclic graph
- **Properties**: |E| = |V| - 1, exactly one path between any two vertices
- **Binary Search Tree, Segment Tree, Trie** all exploit tree structure

**2. Bipartite Graph**: Vertices partitionable into two sets (no edges within sets)
- **2-coloring test**: Graph is bipartite iff it contains no odd-length cycles
- **Application**: Matching problems (job assignments, stable marriages)

```python
# Check if graph is bipartite using BFS (2-coloring)
def is_bipartite(graph: list[list[int]]) -> bool:
    n = len(graph)
    color = [-1] * n
    
    for start in range(n):
        if color[start] != -1:
            continue
        
        queue = [start]
        color[start] = 0
        
        while queue:
            u = queue.pop(0)
            for v in graph[u]:
                if color[v] == -1:
                    color[v] = 1 - color[u]  # Alternate color
                    queue.append(v)
                elif color[v] == color[u]:
                    return False  # Odd cycle found
    
    return True
```

**3. Complete Graph (Kₙ)**: Every pair of vertices connected
- |E| = n(n-1)/2

**4. Planar Graph**: Can be drawn without edge crossings
- **Euler's formula**: V - E + F = 2 (F = faces)

### 5.4 Graph Traversals: The Foundation

**DFS (Depth-First Search)**:
- Stack-based (or recursion)
- **Applications**: Cycle detection, topological sort, strongly connected components
- **Time**: O(V + E)

**BFS (Breadth-First Search)**:
- Queue-based
- **Applications**: Shortest path (unweighted), level-order traversal
- **Time**: O(V + E)

**Go Implementation** (DFS recursive and iterative):
```go
// Recursive DFS
func dfsRecursive(graph [][]int, v int, visited []bool) {
    visited[v] = true
    // Process vertex v
    
    for _, neighbor := range graph[v] {
        if !visited[neighbor] {
            dfsRecursive(graph, neighbor, visited)
        }
    }
}

// Iterative DFS using stack
func dfsIterative(graph [][]int, start int) {
    visited := make([]bool, len(graph))
    stack := []int{start}
    
    for len(stack) > 0 {
        v := stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        
        if visited[v] {
            continue
        }
        visited[v] = true
        // Process vertex v
        
        for _, neighbor := range graph[v] {
            if !visited[neighbor] {
                stack = append(stack, neighbor)
            }
        }
    }
}
```

### 5.5 Advanced Graph Algorithms

**Dijkstra's Algorithm**: Shortest path from source (non-negative weights)
- **Time**: O((V + E) log V) with min-heap
- **Key insight**: Greedy approach, always expand closest unvisited vertex

**Bellman-Ford**: Shortest path (handles negative weights)
- **Time**: O(VE)
- **Detects negative cycles**

**Floyd-Warshall**: All-pairs shortest path
- **Time**: O(V³)
- **Uses dynamic programming**

**Minimum Spanning Tree**:
- **Kruskal's**: Sort edges, use Union-Find → O(E log E)
- **Prim's**: Greedy, expand from one vertex → O(E log V)

**Topological Sort**: Linear ordering of vertices in DAG
- **Applications**: Task scheduling, dependency resolution

---

## VI. Recurrence Relations: The Mathematics of Recursion

### 6.1 Understanding Recurrences

**Definition**: Equation defining sequence in terms of previous terms

**Classic Examples**:
1. **Fibonacci**: F(n) = F(n-1) + F(n-2), F(0)=0, F(1)=1
2. **Tower of Hanoi**: T(n) = 2T(n-1) + 1, T(1)=1
3. **Merge Sort**: T(n) = 2T(n/2) + n

### 6.2 Solving Techniques

**1. Iteration/Expansion Method**

Example: T(n) = T(n-1) + n, T(1) = 1
```
T(n) = T(n-1) + n
     = [T(n-2) + (n-1)] + n
     = [T(n-3) + (n-2)] + (n-1) + n
     = T(1) + 2 + 3 + ... + n
     = 1 + 2 + 3 + ... + n = n(n+1)/2
```

**2. Substitution Method**

Guess solution, prove by induction.

Example: T(n) = 2T(n/2) + n
- Guess: T(n) = O(n log n)
- Prove: T(n) ≤ cn log n for some c

**3. Master Theorem** (for divide-and-conquer)

For T(n) = aT(n/b) + f(n):

- **Case 1**: f(n) = O(n^(log_b(a) - ε)) → T(n) = Θ(n^log_b(a))
- **Case 2**: f(n) = Θ(n^log_b(a)) → T(n) = Θ(n^log_b(a) log n)
- **Case 3**: f(n) = Ω(n^(log_b(a) + ε)) and regularity → T(n) = Θ(f(n))

**Example**: Merge Sort: T(n) = 2T(n/2) + n
- a=2, b=2, f(n)=n
- n^log₂(2) = n
- f(n) = Θ(n) → **Case 2** → T(n) = Θ(n log n)

### 6.3 Generating Functions (Advanced)

**Technique**: Encode sequence as power series, manipulate algebraically

**Fibonacci Example**:
```
G(x) = Σ F(n)x^n
     = x/(1 - x - x²)

Closed form (using partial fractions):
F(n) = (φⁿ - ψⁿ)/√5
where φ = (1+√5)/2, ψ = (1-√5)/2
```

---

## VII. Number Theory: The Atoms of Mathematics

### 7.1 Divisibility and Primes

**Division Algorithm**: For a, b ∈ ℤ, b > 0:
a = bq + r, where 0 ≤ r < b (q = quotient, r = remainder)

**Greatest Common Divisor (GCD)**:
- gcd(a, b) = largest d such that d|a and d|b

**Euclidean Algorithm**:
```rust
fn gcd(mut a: i64, mut b: i64) -> i64 {
    while b != 0 {
        let temp = b;
        b = a % b;
        a = temp;
    }
    a.abs()
}
// Time: O(log min(a,b))
```

**Extended Euclidean Algorithm**: Finds x, y such that ax + by = gcd(a,b)
- **Application**: Modular multiplicative inverse

**Prime Numbers**:
- **Fundamental Theorem of Arithmetic**: Every n > 1 has unique prime factorization
- **Sieve of Eratosthenes**: Generate primes up to n in O(n log log n)

```python
def sieve_of_eratosthenes(n: int) -> list[int]:
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    
    return [i for i in range(n + 1) if is_prime[i]]
```

### 7.2 Modular Arithmetic

**Definition**: a ≡ b (mod m) iff m | (a - b)

**Properties** (all operations preserve congruence):
- (a + b) mod m = ((a mod m) + (b mod m)) mod m
- (a × b) mod m = ((a mod m) × (b mod m)) mod m
- a^n mod m can be computed efficiently using **modular exponentiation**

**Fast Exponentiation** (repeated squaring):
```cpp
long long mod_pow(long long base, long long exp, long long mod) {
    long long result = 1;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) result = (result * base) % mod;
        base = (base * base) % mod;
        exp >>= 1;
    }
    return result;
}
// Time: O(log exp)
```

**Fermat's Little Theorem**: If p is prime and a not divisible by p:
a^(p-1) ≡ 1 (mod p)

**Application**: Modular inverse of a is a^(p-2) (mod p)

**Chinese Remainder Theorem**: System of congruences with coprime moduli has unique solution

### 7.3 Cryptographic Applications

- **RSA**: Based on difficulty of factoring large semiprimes
- **Diffie-Hellman**: Relies on discrete logarithm problem
- **Hash functions**: Use modular arithmetic for distribution

---

## VIII. Boolean Algebra and Digital Logic

### 8.1 Boolean Algebra Axioms

**Operations**: AND (·), OR (+), NOT (')

**Laws**:
1. Identity: A + 0 = A, A · 1 = A
2. Null: A + 1 = 1, A · 0 = 0
3. Idempotent: A + A = A, A · A = A
4. Complement: A + A' = 1, A · A' = 0
5. De Morgan's: (A + B)' = A' · B', (A · B)' = A' + B'

### 8.2 Bitwise Operations

**Algorithmic Gold**: Bit manipulation is often O(1) vs O(n)

```c
// Check if number is power of 2
bool is_power_of_2(int n) {
    return n > 0 && (n & (n - 1)) == 0;
}

// Count set bits (Kernighan's algorithm)
int count_bits(unsigned int n) {
    int count = 0;
    while (n) {
        n &= (n - 1);  // Clear rightmost set bit
        count++;
    }
    return count;
}

// Swap without temp variable
void swap(int* a, int* b) {
    *a ^= *b;
    *b ^= *a;
    *a ^= *b;
}
```

**Bitmasks for Subset Enumeration**:
```python
def enumerate_subsets(arr: list[int]):
    n = len(arr)
    for mask in range(1 << n):  # 2^n subsets
        subset = [arr[i] for i in range(n) if mask & (1 << i)]
        print(subset)
```

---

## IX. Probability Theory: Quantifying Uncertainty

### 9.1 Fundamental Concepts

**Sample Space (Ω)**: Set of all possible outcomes
**Event (E)**: Subset of sample space
**Probability**: P: E → [0, 1]

**Axioms**:
1. P(E) ≥ 0
2. P(Ω) = 1
3. P(E₁ ∪ E₂) = P(E₁) + P(E₂) if disjoint

**Conditional Probability**: P(A|B) = P(A ∩ B) / P(B)

**Bayes' Theorem**: P(A|B) = P(B|A) · P(A) / P(B)
- **Foundation of machine learning and Bayesian inference**

### 9.2 Random Variables and Expected Value

**Expected Value**: E[X] = Σ x · P(X = x)

**Linearity**: E[X + Y] = E[X] + E[Y] (always holds)

**Application in Algorithms**:
- **Randomized QuickSort**: E[comparisons] = O(n log n)
- **Skip Lists**: Expected search time O(log n)
- **Hash Tables**: Expected operations O(1)

---

## X. Mental Models for Mastery

### 10.1 The Abstraction Ladder

**Level 1**: Concrete examples (5 + 3 = 8)
**Level 2**: Patterns (sum formula)
**Level 3**: Structures (group theory)
**Level 4**: Meta-structures (category theory)

**Practice**: Always move up and down this ladder. Test abstract understanding with concrete cases.

### 10.2 Chunking and Pattern Recognition

**Cognitive Principle**: Expert chess players recognize ~50,000 patterns. You need to build your "discrete math pattern library."

**Deliberate Practice Protocol**:
1. Identify pattern (e.g., "combinatorial argument")
2. Practice variations (permutations, combinations, multinomial)
3. Test transfer (apply to new problem)
4. Reflect on why it worked

### 10.3 Proof as Program

**Deep Insight**: Curry-Howard Correspondence shows proofs and programs are isomorphic.

- Proposition ↔ Type
- Proof ↔ Program
- Proof by induction ↔ Recursion

**Mental shift**: When writing recursive algorithms, think "Am I proving something by induction?"

---

## XI. Your Training Regimen

### Daily Practice (Monk Mode):

**Morning (60 min)**:
- 3 proof exercises (vary techniques)
- 2 graph problems
- 1 combinatorics challenge

**Afternoon (45 min)**:
- Implement one algorithm from scratch
- Analyze time/space complexity formally
- Optimize using discrete math insights

**Evening (30 min)**:
- Review notes, create mental models
- Spaced repetition (Anki for theorems)
- Meta-reflection: What patterns emerged today?

### Progressive Difficulty:
1. **Weeks 1-4**: Logic, proofs, basic combinatorics
2. **Weeks 5-8**: Graph algorithms, recurrences
3. **Weeks 9-12**: Number theory, advanced counting
4. **Months 4-6**: Competition problems (Codeforces, USACO)
5. **Ongoing**: Research papers, contribute to open source

---
