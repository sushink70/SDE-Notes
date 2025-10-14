# The Complete Discrete Mathematics Guide
## A Journey from Zero to Hero (Explained So Anyone Can Understand!)

---

## Table of Contents
1. Introduction: What is Discrete Math?
2. Logic and Proofs
3. Sets and Set Theory
4. Functions and Relations
5. Counting and Combinatorics
6. Probability
7. Graph Theory
8. Trees
9. Number Theory
10. Algorithms and Complexity
11. Boolean Algebra
12. Sequences and Recurrence Relations

---

## 1. Introduction: What is Discrete Math?

### What Does "Discrete" Mean?

Imagine you're counting apples. You can have 1 apple, 2 apples, 3 apples, but you can't have 2.5 apples (well, unless you cut one in half, but that's cheating!). That's **discrete** - things that are separate and distinct.

Now think about water in a glass. You can have any amount - 1.5 cups, 2.73 cups, π cups. That's **continuous** - things that flow smoothly.

Discrete math studies things that are separate and countable, like:
- Whole numbers (1, 2, 3...)
- Networks of friends on social media
- Steps in a computer program
- Arrangements of objects

### Why Should You Care?

Discrete math is the foundation of:
- **Computer Science**: Every app, game, and website
- **Cryptography**: Keeping your messages secret
- **Network Design**: How the internet works
- **Optimization**: Finding the best solution to problems
- **Game Theory**: Strategy in games and real life

---

## 2. Logic and Proofs

### What is Logic?

Logic is the art of reasoning correctly. It's about figuring out what's true based on what you already know.

### Statements (Propositions)

A **statement** is a sentence that is either TRUE or FALSE (but not both!).

**Examples:**
- "It is raining." ✓ (This is a statement)
- "2 + 2 = 4" ✓ (This is a statement - and it's TRUE)
- "Is it cold outside?" ✗ (Not a statement - it's a question)
- "Close the door!" ✗ (Not a statement - it's a command)

### Logical Connectives

These are ways to combine statements:

**1. NOT (¬ or ~)**
- Flips the truth value
- "It is NOT raining"
- If something is TRUE, NOT makes it FALSE

**2. AND (∧)**
- Both things must be true
- "It is raining AND it is cold"
- TRUE only if both parts are TRUE

**3. OR (∨)**
- At least one thing must be true
- "It is raining OR it is sunny"
- TRUE if either part (or both) is TRUE

**4. IF...THEN (→)**
- "IF it rains, THEN the ground is wet"
- This is called an **implication**
- FALSE only when the first part is TRUE but the second is FALSE

**5. IF AND ONLY IF (↔)**
- Both things are either TRUE together or FALSE together
- "You pass IF AND ONLY IF you score 50% or more"

### Truth Tables

A truth table shows all possible combinations of truth values:

**Example: AND (∧)**
```
P     Q     P ∧ Q
T     T       T
T     F       F
F     T       F
F     F       F
```

**Example: OR (∨)**
```
P     Q     P ∨ Q
T     T       T
T     F       T
F     T       T
F     F       F
```

**Example: IF...THEN (→)**
```
P     Q     P → Q
T     T       T
T     F       F
F     T       T
F     F       T
```

Why is F → F true? Think of it like a promise: "If it rains, I'll bring an umbrella." If it doesn't rain, I didn't break my promise whether I brought an umbrella or not!

### Proof Techniques

A **proof** is a logical argument that shows something is definitely true.

**1. Direct Proof**
- Start with what you know
- Use logical steps
- Arrive at what you want to prove

**Example:** Prove that the sum of two even numbers is even.
- Let a and b be even numbers
- That means a = 2m and b = 2n (for some whole numbers m and n)
- a + b = 2m + 2n = 2(m + n)
- Since (m + n) is a whole number, 2(m + n) is even
- Therefore, a + b is even! ✓

**2. Proof by Contradiction**
- Assume the opposite of what you want to prove
- Show this leads to something impossible
- Therefore, your original statement must be true!

**Example:** Prove √2 is irrational (can't be written as a fraction).
- Assume √2 = a/b (in simplest form)
- Then 2 = a²/b², so a² = 2b²
- This means a² is even, so a is even
- Write a = 2k
- Then (2k)² = 2b², so 4k² = 2b², meaning 2k² = b²
- So b² is even, meaning b is even
- But if both a and b are even, the fraction wasn't in simplest form!
- Contradiction! Therefore √2 is irrational. ✓

**3. Mathematical Induction**
- Like dominoes: knock down the first one, show each knocks down the next
- Prove it works for the first case (base case)
- Prove that if it works for n, it works for n+1 (inductive step)

**Example:** Prove 1 + 2 + 3 + ... + n = n(n+1)/2

*Base case:* n = 1: Left side = 1, Right side = 1(2)/2 = 1 ✓

*Inductive step:* Assume it's true for n. Prove for n+1:
- 1 + 2 + ... + n + (n+1)
- = [n(n+1)/2] + (n+1)  [using our assumption]
- = [n(n+1) + 2(n+1)]/2
- = (n+1)(n+2)/2
- This is exactly the formula with n+1 plugged in! ✓

---

## 3. Sets and Set Theory

### What is a Set?

A **set** is simply a collection of things. Think of it like a bag containing objects.

**Examples:**
- A = {1, 2, 3, 4, 5} - a set of numbers
- B = {apple, orange, banana} - a set of fruits
- C = {red, blue, green} - a set of colors

### Set Notation

- **∈** means "is an element of": 2 ∈ A (2 is in set A)
- **∉** means "is not an element of": 6 ∉ A (6 is not in set A)
- **{ }** or **∅** is the empty set (a set with nothing in it)
- **|A|** means the size (cardinality) of set A: |A| = 5

### Ways to Describe Sets

**1. Roster Method** - Just list everything:
- A = {1, 2, 3, 4, 5}

**2. Set-Builder Notation** - Give a rule:
- A = {x | x is a whole number and 1 ≤ x ≤ 5}
- Read as: "A is the set of all x such that x is a whole number between 1 and 5"

**3. Interval Notation** (for numbers):
- [1, 5] means all numbers from 1 to 5, including 1 and 5
- (1, 5) means all numbers from 1 to 5, NOT including 1 and 5
- [1, 5) means including 1 but not 5

### Special Sets

- **Natural Numbers (ℕ)**: {1, 2, 3, 4, ...}
- **Integers (ℤ)**: {..., -2, -1, 0, 1, 2, ...}
- **Rational Numbers (ℚ)**: All fractions
- **Real Numbers (ℝ)**: All numbers on the number line
- **Universal Set (U)**: Everything we're currently considering

### Set Operations

**1. Union (A ∪ B)**
- Everything in A OR B (or both)
- Like combining two bags
- Example: {1, 2, 3} ∪ {3, 4, 5} = {1, 2, 3, 4, 5}

**2. Intersection (A ∩ B)**
- Only things in BOTH A AND B
- The overlap
- Example: {1, 2, 3} ∩ {3, 4, 5} = {3}

**3. Difference (A - B or A \ B)**
- Things in A but NOT in B
- Example: {1, 2, 3} - {3, 4, 5} = {1, 2}

**4. Complement (A' or Ā)**
- Everything NOT in A (but in the universal set)
- Example: If U = {1, 2, 3, 4, 5} and A = {1, 2}, then A' = {3, 4, 5}

**5. Cartesian Product (A × B)**
- All possible pairs (a, b) where a ∈ A and b ∈ B
- Example: {1, 2} × {a, b} = {(1,a), (1,b), (2,a), (2,b)}

### Subsets

Set A is a **subset** of set B (A ⊆ B) if every element of A is also in B.

**Examples:**
- {1, 2} ⊆ {1, 2, 3, 4} ✓
- {1, 5} ⊆ {1, 2, 3, 4} ✗ (5 is not in the second set)

**Proper Subset (A ⊂ B)**: A is a subset of B, but A ≠ B

### Power Set

The **power set** of A (written as P(A) or 2^A) is the set of all possible subsets of A.

**Example:** A = {1, 2}
- P(A) = {∅, {1}, {2}, {1, 2}}
- Notice: |P(A)| = 4 = 2²

**General Rule:** If |A| = n, then |P(A)| = 2^n

### Venn Diagrams

Venn diagrams are pictures that show relationships between sets:

```
     A          B
   ┌───┐      ┌───┐
   │   └──┬───┘   │
   │      │       │
   └──────┴───────┘
```

The overlapping region is A ∩ B.

### Set Identities (Laws)

These always work:

1. **Commutative Laws:**
   - A ∪ B = B ∪ A
   - A ∩ B = B ∩ A

2. **Associative Laws:**
   - (A ∪ B) ∪ C = A ∪ (B ∪ C)
   - (A ∩ B) ∩ C = A ∩ (B ∩ C)

3. **Distributive Laws:**
   - A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)
   - A ∪ (B ∩ C) = (A ∪ B) ∩ (A ∪ C)

4. **De Morgan's Laws:**
   - (A ∪ B)' = A' ∩ B'
   - (A ∩ B)' = A' ∪ B'

Think of De Morgan's Laws like this: "NOT (this OR that) = (NOT this) AND (NOT that)"

---

## 4. Functions and Relations

### What is a Relation?

A **relation** between two sets is just a way of connecting elements from one set to elements of another.

**Example:** "Is a friend of" is a relation between people.
- If A = {Alice, Bob} and B = {Carol, Dave}
- We might have: Alice is a friend of Carol, Bob is a friend of Dave

Formally, a relation is a set of ordered pairs: {(Alice, Carol), (Bob, Dave)}

### What is a Function?

A **function** is a special relation where each input has exactly ONE output.

Think of a function as a machine:
- You put something in (input)
- It processes it
- You get exactly one thing out (output)

**Examples:**
- f(x) = 2x is a function: input 3, output 6
- "Mother of" is a function: each person has exactly one biological mother
- "Sibling of" is NOT a function: you might have 0, 1, or many siblings

### Function Notation

- **f: A → B** means f is a function from set A to set B
- **f(x) = y** means "f maps x to y" or "when you input x, you get y"
- **Domain**: all possible inputs (set A)
- **Codomain**: all possible outputs (set B)
- **Range**: actual outputs that occur (a subset of B)

**Example:** f: {1, 2, 3} → {a, b, c, d}
- f(1) = a, f(2) = b, f(3) = b
- Domain = {1, 2, 3}
- Codomain = {a, b, c, d}
- Range = {a, b} (only a and b are actually used)

### Types of Functions

**1. Injective (One-to-One)**
- Different inputs always give different outputs
- No two inputs map to the same output
- Example: f(x) = 2x (if you double different numbers, you get different results)

**2. Surjective (Onto)**
- Every element in the codomain is an output for some input
- The range equals the codomain
- Example: f: ℝ → ℝ where f(x) = x³ (every real number is a cube of something)

**3. Bijective (One-to-One and Onto)**
- Both injective AND surjective
- Perfect pairing between domain and codomain
- Example: f(x) = 2x + 1 from ℝ to ℝ

**Why do these matter?**
- Bijective functions can be "undone" (they have inverses)
- They create perfect matchings between sets

### Composition of Functions

You can chain functions together: do one function, then do another.

**Notation:** (g ∘ f)(x) = g(f(x))

**Example:**
- f(x) = x + 1
- g(x) = 2x
- (g ∘ f)(3) = g(f(3)) = g(4) = 8

Think of it like a factory: raw material → machine f → intermediate product → machine g → final product

### Inverse Functions

An **inverse function** undoes what the original function did.

**Notation:** f⁻¹

If f(a) = b, then f⁻¹(b) = a

**Example:**
- f(x) = 2x (doubling function)
- f⁻¹(x) = x/2 (halving function)
- f(3) = 6, and f⁻¹(6) = 3 ✓

**Important:** Only bijective functions have inverses!

### Floor and Ceiling Functions

**Floor function** ⌊x⌋: Round down to nearest integer
- ⌊3.7⌋ = 3
- ⌊5⌋ = 5
- ⌊-2.3⌋ = -3

**Ceiling function** ⌈x⌉: Round up to nearest integer
- ⌈3.2⌉ = 4
- ⌈5⌉ = 5
- ⌈-2.3⌉ = -2

---

## 5. Counting and Combinatorics

### Why Counting Matters

Combinatorics is the art of counting things cleverly. Instead of listing everything (which might take forever), we use smart techniques.

### The Basic Rules

**1. The Addition Rule (OR)**
If you can do task A in m ways OR task B in n ways (but not both), you can do either task in m + n ways.

**Example:** You have 3 shirts and 2 hats. If you wear EITHER a shirt OR a hat (not both), you have 3 + 2 = 5 choices.

**2. The Multiplication Rule (AND)**
If you can do task A in m ways AND task B in n ways, you can do both in m × n ways.

**Example:** You have 3 shirts and 2 pants. If you wear a shirt AND pants, you have 3 × 2 = 6 outfits.

### Permutations

A **permutation** is an arrangement where ORDER MATTERS.

**Example:** How many ways can you arrange 3 books on a shelf?
- First position: 3 choices
- Second position: 2 choices (one book is already placed)
- Third position: 1 choice (two books are already placed)
- Total: 3 × 2 × 1 = 6 ways

**Formula for n things taken all at once:**
- P(n, n) = n! = n × (n-1) × (n-2) × ... × 2 × 1

**What is n! (n factorial)?**
- 5! = 5 × 4 × 3 × 2 × 1 = 120
- 3! = 3 × 2 × 1 = 6
- 1! = 1
- 0! = 1 (by definition)

**Formula for n things taken r at a time:**
- P(n, r) = n!/(n-r)!

**Example:** How many ways can you arrange 3 books chosen from 5?
- P(5, 3) = 5!/(5-3)! = 5!/2! = (5 × 4 × 3 × 2 × 1)/(2 × 1) = 60

### Combinations

A **combination** is a selection where ORDER DOESN'T MATTER.

**Example:** Choose 2 friends from {Alice, Bob, Carol}:
- Alice & Bob
- Alice & Carol
- Bob & Carol
- That's it! Just 3 ways (we don't count "Bob & Alice" as different from "Alice & Bob")

**Formula:**
- C(n, r) = n! / (r!(n-r)!)
- Also written as (n choose r) or ⁿCᵣ

**Example:** Choose 2 books from 5:
- C(5, 2) = 5! / (2! × 3!) = (5 × 4 × 3!) / (2 × 1 × 3!) = 20/2 = 10

### Permutations vs Combinations - The Key Difference

**Does order matter?**
- **YES → Permutations**: Arranging books on a shelf (position matters)
- **NO → Combinations**: Picking team members (who's picked matters, not the order)

### The Pigeonhole Principle

**Simple version:** If you put n+1 pigeons into n holes, at least one hole has more than one pigeon.

**Example:** In any group of 13 people, at least 2 were born in the same month. (13 people, 12 months)

**Generalized version:** If you put n items into k containers, at least one container has at least ⌈n/k⌉ items.

### Inclusion-Exclusion Principle

How many elements are in A ∪ B?

**Formula:** |A ∪ B| = |A| + |B| - |A ∩ B|

Why subtract? Because we counted the overlap twice!

**Example:** In a class of 30 students:
- 20 like pizza
- 15 like burgers
- 10 like both
- How many like at least one? 20 + 15 - 10 = 25

**For three sets:**
|A ∪ B ∪ C| = |A| + |B| + |C| - |A ∩ B| - |A ∩ C| - |B ∩ C| + |A ∩ B ∩ C|

### Stars and Bars

A technique for counting distributions.

**Problem:** How many ways can you distribute n identical objects into k distinct bins?

**Formula:** C(n + k - 1, k - 1)

**Example:** Distribute 5 identical candies to 3 children:
- C(5 + 3 - 1, 3 - 1) = C(7, 2) = 21 ways

**Visualization:** Use stars for objects and bars to separate bins:
- ★★|★|★★ means: child 1 gets 2, child 2 gets 1, child 3 gets 2

### Binomial Theorem

**(a + b)ⁿ = Σ C(n, k) × aⁿ⁻ᵏ × bᵏ** (for k from 0 to n)

**Example:** (a + b)³ = C(3,0)a³b⁰ + C(3,1)a²b¹ + C(3,2)a¹b² + C(3,3)a⁰b³
= 1a³ + 3a²b + 3ab² + 1b³

The coefficients (1, 3, 3, 1) form **Pascal's Triangle**:
```
       1
      1 1
     1 2 1
    1 3 3 1
   1 4 6 4 1
```
Each number is the sum of the two above it!

---

## 6. Probability

### What is Probability?

Probability measures how likely something is to happen, from 0 (impossible) to 1 (certain).

**Think of it as:** (favorable outcomes) / (total possible outcomes)

### Basic Probability

**Example:** What's the probability of rolling a 4 on a standard die?
- Favorable outcomes: 1 (just rolling a 4)
- Total outcomes: 6 (numbers 1 through 6)
- P(rolling a 4) = 1/6 ≈ 0.167 or 16.7%

### Key Terms

**1. Sample Space (S)**
- All possible outcomes
- Example: Rolling a die, S = {1, 2, 3, 4, 5, 6}

**2. Event (E)**
- A subset of the sample space
- Example: Rolling an even number, E = {2, 4, 6}

**3. Probability of an Event**
- P(E) = |E| / |S|
- Example: P(even) = 3/6 = 1/2

### Probability Rules

**1. Basic Properties:**
- 0 ≤ P(E) ≤ 1 for any event E
- P(S) = 1 (something must happen)
- P(∅) = 0 (impossible event)

**2. Complement Rule:**
- P(not E) = 1 - P(E)
- Example: P(not rolling a 4) = 1 - 1/6 = 5/6

**3. Addition Rule (OR):**
- For mutually exclusive events: P(A or B) = P(A) + P(B)
- For any events: P(A or B) = P(A) + P(B) - P(A and B)

**Example:** Drawing a card:
- P(King or Queen) = P(King) + P(Queen) = 4/52 + 4/52 = 8/52 = 2/13
- These are mutually exclusive (a card can't be both)

**4. Multiplication Rule (AND):**
- For independent events: P(A and B) = P(A) × P(B)

**Example:** Flipping two coins:
- P(Heads on first AND Heads on second) = 1/2 × 1/2 = 1/4

### Independent vs Dependent Events

**Independent:** One event doesn't affect the other
- Example: Flipping a coin twice

**Dependent:** One event affects the other
- Example: Drawing two cards without replacement

**For dependent events:**
- P(A and B) = P(A) × P(B|A)
- P(B|A) means "probability of B given that A happened"

### Conditional Probability

**P(A|B) = P(A and B) / P(B)**

**Example:** In a class:
- 60% are girls
- 40% of girls play sports
- What's the probability someone plays sports given they're a girl?
- P(sports|girl) = 0.40 or 40%

### Bayes' Theorem

**P(A|B) = [P(B|A) × P(A)] / P(B)**

This lets you flip conditional probabilities!

**Example:** Disease testing:
- 1% of people have a disease
- Test is 95% accurate (true positive rate)
- Test has 10% false positive rate
- You test positive. What's the probability you actually have the disease?

Using Bayes' Theorem:
- P(disease|positive) = [0.95 × 0.01] / P(positive)
- P(positive) = P(positive|disease) × P(disease) + P(positive|no disease) × P(no disease)
- P(positive) = 0.95 × 0.01 + 0.10 × 0.99 = 0.0095 + 0.099 = 0.1085
- P(disease|positive) = 0.0095 / 0.1085 ≈ 0.088 or 8.8%

Surprising, right? Even with a positive test, you probably don't have the disease!

### Expected Value

The **expected value** is the average outcome if you repeat something many times.

**Formula:** E(X) = Σ [value × probability]

**Example:** A game costs $1 to play:
- 50% chance to win $0 (lose)
- 30% chance to win $1 (break even)
- 20% chance to win $5 (win big!)

Expected value = 0.5($0) + 0.3($1) + 0.2($5) = $0 + $0.30 + $1.00 = $1.30

But you paid $1, so your expected profit is $1.30 - $1.00 = $0.30 per game.

---

## 7. Graph Theory

### What is a Graph?

In math, a **graph** is NOT a chart or plot. It's a collection of:
- **Vertices** (or nodes): dots representing things
- **Edges**: lines connecting the dots

**Examples of graphs in real life:**
- Social networks: people are vertices, friendships are edges
- Road maps: cities are vertices, roads are edges
- Web pages: pages are vertices, links are edges

### Basic Definitions

**1. Vertex (Node)**
- A point in the graph
- Usually drawn as a circle with a label

**2. Edge**
- A connection between two vertices
- Can be drawn as a line

**3. Degree**
- The number of edges connected to a vertex
- Example: If vertex A connects to 3 other vertices, degree(A) = 3

**4. Adjacent Vertices**
- Vertices connected by an edge
- They're "neighbors"

### Types of Graphs

**1. Undirected Graph**
- Edges have no direction
- Like mutual friendship: if A is friends with B, then B is friends with A
- Example: Facebook friendships

**2. Directed Graph (Digraph)**
- Edges have direction (arrows)
- Like following on Twitter: A might follow B, but B might not follow A
- Example: Instagram followers

**3. Weighted Graph**
- Each edge has a number (weight)
- Example: Road map where weights are distances

**4. Simple Graph**
- No loops (edge from a vertex to itself)
- No multiple edges between the same pair of vertices

**5. Multigraph**
- Can have multiple edges between the same vertices
- Example: Multiple flights between two cities

**6. Complete Graph (Kₙ)**
- Every vertex connects to every other vertex
- Example: K₄ has 4 vertices and 6 edges

**7. Bipartite Graph**
- Vertices can be divided into two groups
- Edges only connect vertices from different groups
- Example: Students and classes (students take classes, but students don't connect to students)

### Paths and Cycles

**1. Path**
- A sequence of vertices where each connects to the next
- No vertex appears twice
- Example: A → B → C → D

**2. Cycle**
- A path that starts and ends at the same vertex
- Example: A → B → C → A

**3. Simple Path/Cycle**
- No repeated vertices (except start/end in a cycle)

**4. Length of a Path**
- Number of edges in the path

### Connectivity

**1. Connected Graph**
- There's a path between every pair of vertices
- You can get from anywhere to anywhere

**2. Disconnected Graph**
- Some vertices can't reach others
- Like islands with no bridges

**3. Component**
- A maximal connected subgraph
- Think of it as an island of connectivity

**4. Bridge**
- An edge whose removal disconnects the graph
- Critical connection!

### Special Types of Graphs

**1. Tree**
- Connected graph with no cycles
- Like a family tree or file system
- We'll explore these more later!

**2. Forest**
- Collection of trees (multiple disconnected trees)

**3. Regular Graph**
- Every vertex has the same degree
- Example: Every person has exactly 3 friends

**4. Planar Graph**
- Can be drawn on paper without edges crossing
- Example: K₄ is planar, but K₅ is not

### Graph Representation

**1. Adjacency Matrix**
- A table showing connections
- Example: For vertices {A, B, C}:
```
    A  B  C
A   0  1  1
B   1  0  1
C   1  1  0
```
1 means connected, 0 means not connected

**2. Adjacency List**
- For each vertex, list its neighbors
- Example:
  - A: [B, C]
  - B: [A, C]
  - C: [A, B]

### Euler Paths and Circuits

**Euler Path:**
- A path that uses every edge exactly once
- Example: Drawing a shape without lifting your pen

**Euler Circuit:**
- An Euler path that starts and ends at the same vertex

**Euler's Theorem:**
- A graph has an Euler circuit if and only if:
  - It's connected
  - Every vertex has even degree

- A graph has an Euler path (but not circuit) if and only if:
  - It's connected
  - Exactly two vertices have odd degree

**Example:** Can you draw a square with an X inside without lifting your pen?
- Count degrees: corner vertices have degree 4, center has degree 4
- All even! Yes, you can (it has an Euler circuit)

### Hamilton Paths and Circuits

**Hamilton Path:**
- A path that visits every vertex exactly once

**Hamilton Circuit:**
- A Hamilton path that returns to the start

**Note:** Unlike Euler paths, there's no easy test for Hamilton paths. This is a hard problem!

### Graph Coloring

**Vertex Coloring:**
- Assign colors to vertices so no two adjacent vertices have the same color
- **Chromatic number**: minimum number of colors needed

**Example:** Map coloring (countries sharing a border must have different colors)
- Famous theorem: Any map needs at most 4 colors!

**Applications:**
- Scheduling: If two classes share students (adjacent), schedule at different times (different colors)
- Register allocation in compilers

### Important Theorems

**1. Handshaking Lemma**
- The sum of all vertex degrees equals twice the number of edges
- Why? Each edge contributes 2 to the total degree count
- Σ deg(v) = 2|E|

**2. Every graph has an even number of vertices with odd degree**
- Follows from the handshaking lemma!

---

## 8. Trees

### What is a Tree?

A **tree** is a special type of graph that:
- Is connected (you can get from any vertex to any other)
- Has NO cycles (no loops)
- Looks like... well, a tree! (though often drawn upside down)

Think of:
- Family trees
- File systems on your computer
- Organization charts
- Decision trees

### Key Properties of Trees

**Important Facts:**
1. A tree with n vertices has exactly n-1 edges
2. There's exactly ONE path between any two vertices
3. Removing any edge disconnects the tree
4. Adding any edge creates a cycle

**Why n-1 edges?** Start with n isolated vertices (0 edges). To connect them without creating cycles, you need exactly n-1 edges.

### Tree Terminology

**1. Root**
- A special vertex at the "top" (though trees can be drawn many ways)
- Like the CEO in an org chart

**2. Parent and Child**
- If there's an edge from A to B (going down from root), A is the parent of B
- B is a child of A

**3. Siblings**
- Vertices with the same parent
- Like brothers and sisters

**4. Leaf (Terminal Node)**
- A vertex with no children
- The "end" of a branch

**5. Internal Node**
- A vertex that has children
- Not a leaf

**6. Ancestor and Descendant**
- If you can go down from A to reach B, A is an ancestor of B
- B is a descendant of A

**7. Subtree**
- A tree formed by a vertex and all its descendants

**8. Level (Depth)**
- The root is at level 0
- Each step down increases the level by 1

**9. Height**
- The maximum level in the tree
- The longest path from root to any leaf

**Example Tree:**
```
        A (root, level 0)
       /|\
      B C D (level 1)
     /|   |
    E F   G (level 2)
```
- Height = 2
- Leaves: E, F, C, G
- Internal nodes: A, B, D
- B's children: E, F
- A's descendants: everyone else

### Binary Trees

A **binary tree** is a tree where each vertex has AT MOST 2 children.

**Children are labeled:**
- **Left child**
- **Right child**

**Types of Binary Trees:**

**1. Full Binary Tree**
- Every node has either 0 or 2 children
- No node has just 1 child

**2. Complete Binary Tree**
- All levels are fully filled except possibly the last
- The last level is filled from left to right

**3. Perfect Binary Tree**
- All internal nodes have 2 children
- All leaves are at the same level
- Beautiful symmetry!

**4. Balanced Binary Tree**
- For each node, the heights of left and right subtrees differ by at most 1
- Keeps the tree from getting too "lopsided"

### Properties of Binary Trees

**For a binary tree with height h:**
- Maximum nodes at level i: 2^i
- Maximum total nodes: 2^(h+1) - 1
- Minimum height for n nodes: ⌈log₂(n+1)⌉ - 1

**For a full binary tree with n internal nodes:**
- Number of leaves = n + 1

### Tree Traversals

**Traversal** means visiting every node in some order. For binary trees, there are several ways:

**1. Preorder Traversal (Root → Left → Right)**
- Visit the root first
- Then traverse left subtree
- Then traverse right subtree
- **Use:** Creating a copy of the tree

**2. Inorder Traversal (Left → Root → Right)**
- Traverse left subtree first
- Visit the root
- Then traverse right subtree
- **Use:** Getting sorted order from a binary search tree

**3. Postorder Traversal (Left → Right → Root)**
- Traverse left subtree first
- Then right subtree
- Visit root last
- **Use:** Deleting a tree (delete children before parent)

**4. Level-order Traversal (Breadth-First)**
- Visit nodes level by level, left to right
- Use a queue!
- **Use:** Finding shortest paths

**Example:**
```
      A
     / \
    B   C
   / \
  D   E
```

- Preorder: A, B, D, E, C
- Inorder: D, B, E, A, C
- Postorder: D, E, B, C, A
- Level-order: A, B, C, D, E

### Binary Search Trees (BST)

A **binary search tree** is a binary tree where:
- Left subtree of a node contains only values LESS than the node
- Right subtree contains only values GREATER than the node
- Both subtrees are also BSTs

**Example:**
```
       8
      / \
     3   10
    / \    \
   1   6   14
      / \  /
     4  7 13
```

**Why are BSTs useful?**
- **Search:** Average O(log n) time (like binary search!)
- **Insert:** Average O(log n) time
- **Delete:** Average O(log n) time

**Searching in a BST:**
1. Start at root
2. If target equals current node, found it!
3. If target < current, go left
4. If target > current, go right
5. Repeat until found or reach a null

**Example:** Search for 6 in the tree above:
- Start at 8: 6 < 8, go left to 3
- At 3: 6 > 3, go right to 6
- Found it!

### Spanning Trees

A **spanning tree** of a graph G is a subgraph that:
- Is a tree
- Contains all vertices of G

**Example:** Given a graph of cities with roads, a spanning tree shows one way to connect all cities without any redundant roads.

**Minimum Spanning Tree (MST)**
- A spanning tree with the smallest total edge weight
- Used in network design (minimize cable length)

**Two Famous Algorithms for MST:**

**1. Kruskal's Algorithm**
- Sort all edges by weight (smallest first)
- Keep adding the smallest edge that doesn't create a cycle
- Stop when you have n-1 edges

**2. Prim's Algorithm**
- Start with any vertex
- Repeatedly add the smallest edge connecting the tree to a new vertex
- Stop when all vertices are included

**Example:** Connect 4 cities with minimum road length:
```
Cities: A, B, C, D
Roads (with distances):
A-B: 5, A-C: 3, A-D: 7
B-C: 4, B-D: 2, C-D: 6
```

Using Kruskal's:
1. Sort edges: B-D(2), A-C(3), B-C(4), A-B(5), C-D(6), A-D(7)
2. Add B-D (2)
3. Add A-C (3)
4. Add B-C (4) - connects B and C to A-C-D
5. Done! Total: 2+3+4 = 9

### Expression Trees

**Expression trees** represent mathematical expressions:
- Leaves are operands (numbers/variables)
- Internal nodes are operators (+, -, ×, ÷)

**Example:** (3 + 5) × (4 - 2)
```
       ×
      / \
     +   -
    / \ / \
   3  5 4  2
```

**Evaluating:** Use postorder traversal!
- Evaluate left subtree → 3 + 5 = 8
- Evaluate right subtree → 4 - 2 = 2
- Apply root operation → 8 × 2 = 16

### Huffman Coding Trees

**Huffman trees** create efficient codes for data compression:
- Frequent characters get short codes
- Rare characters get long codes

**Example:** Encode "ABRACADABRA"
- Count frequencies: A:5, B:2, R:2, C:1, D:1
- Build tree by combining lowest frequencies
- Assign 0 for left, 1 for right

Result: A might be '0', B might be '110', etc.

This is how file compression works!

---

## 9. Number Theory

### What is Number Theory?

Number theory studies properties of integers (whole numbers). It's called "the queen of mathematics" because it's both beautiful and useful (especially in cryptography!).

### Divisibility

**Definition:** a divides b (written a|b) if b = ka for some integer k.

**Examples:**
- 3|15 because 15 = 3 × 5 ✓
- 4|20 because 20 = 4 × 5 ✓
- 5∤12 because 12 ≠ 5k for any integer k ✗

**Properties:**
1. If a|b and b|c, then a|c (transitive)
2. If a|b and a|c, then a|(b+c) and a|(b-c)
3. If a|b, then a|bc for any integer c

### Division Algorithm

For any integers a and b (b > 0), there exist unique integers q (quotient) and r (remainder) such that:

**a = bq + r, where 0 ≤ r < b**

**Example:** Divide 17 by 5:
- 17 = 5 × 3 + 2
- q = 3 (quotient), r = 2 (remainder)

This is what happens when you do long division!

### Prime Numbers

A **prime number** is a natural number greater than 1 that has exactly two divisors: 1 and itself.

**Primes:** 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, ...

**Composite numbers** have more than two divisors: 4, 6, 8, 9, 10, 12, ...

**Special case:** 1 is neither prime nor composite.

**Fundamental Theorem of Arithmetic:**
Every integer greater than 1 can be written as a unique product of primes (up to order).

**Example:**
- 60 = 2² × 3 × 5
- 100 = 2² × 5²
- 17 = 17 (already prime)

### Finding Primes: Sieve of Eratosthenes

An ancient algorithm to find all primes up to n:

**Steps:**
1. List all numbers from 2 to n
2. Start with 2 (first prime)
3. Cross out all multiples of 2 (except 2 itself)
4. Find next uncrossed number (that's prime!)
5. Cross out all its multiples
6. Repeat until you've processed all numbers up to √n

**Example:** Find primes up to 30:
- Start: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30
- Cross multiples of 2: 2, 3, ~~4~~, 5, ~~6~~, 7, ~~8~~, 9, ~~10~~, 11, ~~12~~, 13, ~~14~~, 15, ~~16~~, 17, ~~18~~, 19, ~~20~~, 21, ~~22~~, 23, ~~24~~, 25, ~~26~~, 27, ~~28~~, 29, ~~30~~
- Cross multiples of 3: 2, 3, 5, 7, ~~9~~, 11, 13, ~~15~~, 17, 19, ~~21~~, 23, 25, ~~27~~, 29
- Cross multiples of 5: 2, 3, 5, 7, 11, 13, 17, 19, 23, ~~25~~, 29
- Done! Primes: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29

### Greatest Common Divisor (GCD)

The **GCD** of two numbers is the largest number that divides both.

**Example:** GCD(12, 18) = 6

**Finding GCD: Euclidean Algorithm**
- Super efficient algorithm from ancient Greece!

**Method:**
1. GCD(a, b) = GCD(b, a mod b)
2. Repeat until b = 0
3. Answer is the last non-zero remainder

**Example:** GCD(48, 18)
- 48 = 18 × 2 + 12, so GCD(48, 18) = GCD(18, 12)
- 18 = 12 × 1 + 6, so GCD(18, 12) = GCD(12, 6)
- 12 = 6 × 2 + 0, so GCD(12, 6) = GCD(6, 0)
- Answer: 6

**Why does this work?** Any common divisor of a and b also divides (a mod b).

### Least Common Multiple (LCM)

The **LCM** of two numbers is the smallest number that both divide.

**Example:** LCM(4, 6) = 12

**Formula:**
**LCM(a, b) = (a × b) / GCD(a, b)**

**Example:** LCM(12, 18)
- GCD(12, 18) = 6
- LCM(12, 18) = (12 × 18) / 6 = 216 / 6 = 36

### Modular Arithmetic

**a ≡ b (mod m)** means a and b have the same remainder when divided by m.

**Example:**
- 17 ≡ 5 (mod 12) because 17 = 12 × 1 + 5 and 5 = 12 × 0 + 5
- Both have remainder 5

**Think of it as "clock arithmetic":**
- 15 hours after 10:00 is 1:00 (because 10 + 15 ≡ 1 (mod 12))

**Properties:**
1. If a ≡ b (mod m) and c ≡ d (mod m), then:
   - a + c ≡ b + d (mod m)
   - a - c ≡ b - d (mod m)
   - a × c ≡ b × d (mod m)

2. If a ≡ b (mod m), then a^n ≡ b^n (mod m)

### Congruence Classes

All numbers with the same remainder mod m form a **congruence class**.

**Example (mod 3):**
- Class [0]: {..., -6, -3, 0, 3, 6, 9, ...}
- Class [1]: {..., -5, -2, 1, 4, 7, 10, ...}
- Class [2]: {..., -4, -1, 2, 5, 8, 11, ...}

Every integer belongs to exactly one class!

### Fermat's Little Theorem

If p is prime and a is not divisible by p, then:

**a^(p-1) ≡ 1 (mod p)**

**Example:** 2^6 ≡ 1 (mod 7)
- Check: 2^6 = 64 = 7 × 9 + 1 ✓

**Use:** Fast exponentiation in cryptography!

### Euler's Phi Function φ(n)

**φ(n)** counts how many numbers from 1 to n are coprime to n (GCD = 1).

**Examples:**
- φ(8) = 4, because 1, 3, 5, 7 are coprime to 8
- φ(7) = 6, because 1, 2, 3, 4, 5, 6 are coprime to 7 (7 is prime!)

**Formula for prime p:**
- φ(p) = p - 1

**Formula for prime powers:**
- φ(p^k) = p^k - p^(k-1) = p^(k-1)(p - 1)

**For coprime numbers:**
- φ(mn) = φ(m) × φ(n)

**Example:** φ(12) = φ(4 × 3) = φ(4) × φ(3) = 2 × 2 = 4

### Chinese Remainder Theorem (CRT)

If you know the remainders of x when divided by several coprime numbers, you can find x!

**Example:**
- x ≡ 2 (mod 3)
- x ≡ 3 (mod 5)
- x ≡ 2 (mod 7)

What is x?

Using CRT, we can find x = 23 (and x = 23 + 105k for any integer k).

**Why is this useful?**
- Breaking large problems into smaller ones
- Used in RSA cryptography
- Distributed computing

### RSA Cryptography (Simple Version)

**Setup:**
1. Pick two large primes p and q
2. Compute n = p × q
3. Compute φ(n) = (p-1)(q-1)
4. Pick e coprime to φ(n) (public key)
5. Find d such that ed ≡ 1 (mod φ(n)) (private key)

**Encrypt message M:**
- C = M^e (mod n)

**Decrypt cipher C:**
- M = C^d (mod n)

**Example (small numbers):**
- p = 3, q = 11, so n = 33
- φ(33) = 2 × 10 = 20
- Choose e = 3 (coprime to 20)
- Find d: 3d ≡ 1 (mod 20), so d = 7
- Encrypt message M = 5: C = 5³ mod 33 = 125 mod 33 = 26
- Decrypt: M = 26^7 mod 33 = 5 ✓

---

## 10. Algorithms and Complexity

### What is an Algorithm?

An **algorithm** is a step-by-step procedure to solve a problem. Like a recipe!

**Good algorithms are:**
- **Correct:** Always give the right answer
- **Efficient:** Don't waste time or space
- **Clear:** Easy to understand and implement

### Algorithm Analysis

We measure efficiency using **Big O notation**, which describes how running time grows as input size increases.

**Why not just measure in seconds?**
- Different computers run at different speeds
- We care about the growth rate, not exact time

### Big O Notation

**O(f(n))** means the algorithm's time grows at most as fast as f(n).

**Common complexities (from best to worst):**

**1. O(1) - Constant Time**
- Same time regardless of input size
- Example: Accessing an array element by index
- arr[5] takes the same time whether the array has 10 or 10,000 elements

**2. O(log n) - Logarithmic Time**
- Time grows very slowly
- Example: Binary search
- Doubling input size only adds one step!

**3. O(n) - Linear Time**
- Time grows proportionally to input size
- Example: Finding max in unsorted array
- Double the input, double the time

**4. O(n log n) - Linearithmic Time**
- Slightly worse than linear
- Example: Efficient sorting (merge sort, quicksort)
- Best possible for comparison-based sorting!

**5. O(n²) - Quadratic Time**
- Time grows with square of input
- Example: Bubble sort, nested loops
- Double the input, quadruple the time!

**6. O(n³) - Cubic Time**
- Example: Multiplying two n×n matrices (naive method)

**7. O(2^n) - Exponential Time**
- Time doubles with each additional input
- Example: Trying all subsets
- Gets unusably slow very quickly!

**8. O(n!) - Factorial Time**
- Example: Trying all permutations
- Only works for tiny inputs!

**Comparison:** For n = 20:
- O(log n) ≈ 4 steps
- O(n) = 20 steps
- O(n²) = 400 steps
- O(2^n) = 1,048,576 steps!
- O(n!) = 2,432,902,008,176,640,000 steps!!!

### Searching Algorithms

**1. Linear Search**
- Check each element one by one
- **Time:** O(n)
- **Space:** O(1)

```
Algorithm LinearSearch(arr, target):
    for i from 0 to arr.length - 1:
        if arr[i] == target:
            return i
    return -1  // not found
```

**2. Binary Search**
- Only works on SORTED arrays
- Check middle element
- Eliminate half the remaining elements each time
- **Time:** O(log n)
- **Space:** O(1)

```
Algorithm BinarySearch(arr, target):
    left = 0
    right = arr.length - 1
    
    while left ≤ right:
        mid = (left + right) / 2
        
        if arr[mid] == target:
            return mid
        else if arr[mid] < target:
            left = mid + 1  // search right half
        else:
            right = mid - 1  // search left half
    
    return -1  // not found
```

**Example:** Search for 7 in [1, 3, 5, 7, 9, 11, 13]
- Check middle (7): Found it!

**Example:** Search for 6 in [1, 3, 5, 7, 9, 11, 13]
- Check 7: too big, search left [1, 3, 5]
- Check 3: too small, search right [5]
- Check 5: too small, no more elements
- Not found!

### Sorting Algorithms

**1. Bubble Sort**
- Repeatedly swap adjacent elements if they're in wrong order
- **Time:** O(n²)
- **Space:** O(1)

```
Algorithm BubbleSort(arr):
    for i from 0 to arr.length - 1:
        for j from 0 to arr.length - i - 2:
            if arr[j] > arr[j+1]:
                swap arr[j] and arr[j+1]
```

**Example:** Sort [5, 2, 8, 1]
- Pass 1: [2, 5, 1, 8] (8 bubbles to end)
- Pass 2: [2, 1, 5, 8] (5 moves)
- Pass 3: [1, 2, 5, 8] (done!)

**2. Selection Sort**
- Find minimum, move it to front
- Repeat for remaining elements
- **Time:** O(n²)
- **Space:** O(1)

```
Algorithm SelectionSort(arr):
    for i from 0 to arr.length - 1:
        minIndex = i
        for j from i+1 to arr.length - 1:
            if arr[j] < arr[minIndex]:
                minIndex = j
        swap arr[i] and arr[minIndex]
```

**3. Insertion Sort**
- Build sorted portion one element at a time
- Like sorting playing cards in your hand
- **Time:** O(n²) worst case, O(n) best case
- **Space:** O(1)

```
Algorithm InsertionSort(arr):
    for i from 1 to arr.length - 1:
        key = arr[i]
        j = i - 1
        while j ≥ 0 and arr[j] > key:
            arr[j+1] = arr[j]
            j = j - 1
        arr[j+1] = key
```

**4. Merge Sort**
- Divide array in half recursively
- Sort each half
- Merge sorted halves
- **Time:** O(n log n)
- **Space:** O(n)

```
Algorithm MergeSort(arr):
    if arr.length ≤ 1:
        return arr
    
    mid = arr.length / 2
    left = MergeSort(arr[0...mid])
    right = MergeSort(arr[mid+1...end])
    
    return Merge(left, right)

Algorithm Merge(left, right):
    result = []
    while left and right are not empty:
        if left[0] ≤ right[0]:
            append left[0] to result
            remove left[0]
        else:
            append right[0] to result
            remove right[0]
    
    append remaining elements to result
    return result
```

**5. Quick Sort**
- Pick a "pivot" element
- Partition: smaller elements left, larger right
- Recursively sort partitions
- **Time:** O(n log n) average, O(n²) worst case
- **Space:** O(log n)

```
Algorithm QuickSort(arr, low, high):
    if low < high:
        pivotIndex = Partition(arr, low, high)
        QuickSort(arr, low, pivotIndex - 1)
        QuickSort(arr, pivotIndex + 1, high)

Algorithm Partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    for j from low to high - 1:
        if arr[j] < pivot:
            i = i + 1
            swap arr[i] and arr[j]
    swap arr[i+1] and arr[high]
    return i + 1
```

### Graph Algorithms

**1. Breadth-First Search (BFS)**
- Explore level by level
- Use a queue
- **Time:** O(V + E) where V = vertices, E = edges
- **Use:** Shortest path in unweighted graph

```
Algorithm BFS(graph, start):
    create queue Q
    mark start as visited
    Q.enqueue(start)
    
    while Q is not empty:
        vertex = Q.dequeue()
        for each neighbor of vertex:
            if neighbor not visited:
                mark neighbor as visited
                Q.enqueue(neighbor)
```

**2. Depth-First Search (DFS)**
- Explore as deep as possible before backtracking
- Use a stack (or recursion)
- **Time:** O(V + E)
- **Use:** Detecting cycles, topological sort

```
Algorithm DFS(graph, vertex):
    mark vertex as visited
    for each neighbor of vertex:
        if neighbor not visited:
            DFS(graph, neighbor)
```

**3. Dijkstra's Algorithm**
- Find shortest paths from a source to all vertices
- Works on weighted graphs with non-negative weights
- **Time:** O((V + E) log V) with priority queue

```
Algorithm Dijkstra(graph, source):
    for each vertex v:
        distance[v] = infinity
        previous[v] = null
    distance[source] = 0
    
    create priority queue Q with all vertices
    
    while Q is not empty:
        u = vertex with minimum distance in Q
        remove u from Q
        
        for each neighbor v of u:
            alt = distance[u] + weight(u, v)
            if alt < distance[v]:
                distance[v] = alt
                previous[v] = u
    
    return distance
```

### Greedy Algorithms

**Greedy strategy:** Make the locally optimal choice at each step, hoping for a global optimum.

**Examples:**
1. **Making change:** Use largest coins first
2. **Activity selection:** Choose activities that finish earliest
3. **Huffman coding:** Combine lowest frequency symbols first

**Note:** Greedy doesn't always work! But when it does, it's usually efficient.

### Dynamic Programming

**Strategy:** Break problem into subproblems, solve each once, store results.

**Key idea:** Avoid recalculating the same thing multiple times!

**Example: Fibonacci Numbers**

**Naive recursion (slow):**
```
fib(n):
    if n ≤ 1:
        return n
    return fib(n-1) + fib(n-2)
```
**Time:** O(2^n) - terrible!

**Dynamic programming (fast):**
```
fib(n):
    if n ≤ 1:
        return n
    dp[0] = 0
    dp[1] = 1
    for i from 2 to n:
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
```
**Time:** O(n) - much better!

### P vs NP (The Million Dollar Question!)

**P (Polynomial time):**
- Problems solvable in polynomial time: O(n^k) for some k
- Example: Sorting, shortest path

**NP (Nondeterministic Polynomial time):**
- Problems where solutions can be VERIFIED in polynomial time
- Example: Sudoku (easy to check if a solution is correct)

**NP-Complete:**
- Hardest problems in NP
- If you can solve one efficiently, you can solve ALL NP problems efficiently!
- Examples: Traveling salesman, graph coloring, Sudoku

**The Question:** Is P = NP?
- Can every problem whose solution is quickly verifiable also be quickly solvable?
- Nobody knows! It's one of the biggest unsolved problems in computer science.
- Worth $1,000,000 if you solve it!

---

## 11. Boolean Algebra

### What is Boolean Algebra?

Boolean algebra deals with values that are either TRUE (1) or FALSE (0). It's the foundation of all digital circuits and computer logic!

Named after George Boole (1815-1864).

### Basic Operations

**1. NOT (¬ or ')**
- Flips the value
- ¬0 = 1
- ¬1 = 0

**2. AND (·  or ∧)**
- True only if both are true
- 0 · 0 = 0
- 0 · 1 = 0
- 1 · 0 = 0
- 1 · 1 = 1

**3. OR (+ or ∨)**
- True if at least one is true
- 0 + 0 = 0
- 0 + 1 = 1
- 1 + 0 = 1
- 1 + 1 = 1

**Note:** In Boolean algebra, 1 + 1 = 1 (not 2!). It means "true OR true = true".

### Additional Operations

**4. XOR (⊕) - Exclusive OR**
- True if exactly one is true
- 0 ⊕ 0 = 0
- 0 ⊕ 1 = 1
- 1 ⊕ 0 = 1
- 1 ⊕ 1 = 0

**5. NAND - NOT AND**
- Opposite of AND
- A NAND B = ¬(A · B)

**6. NOR - NOT OR**
- Opposite of OR
- A NOR B = ¬(A + B)

### Boolean Laws

**Identity Laws:**
- A + 0 = A
- A · 1 = A

**Null Laws:**
- A + 1 = 1
- A · 0 = 0

**Idempotent Laws:**
- A + A = A
- A · A = A

**Complement Laws:**
- A + ¬A = 1
- A · ¬A = 0
- ¬(¬A) = A

**Commutative Laws:**
- A + B = B + A
- A · B = B · A

**Associative Laws:**
- (A + B) + C = A + (B + C)
- (A · B) · C = A · (B · C)

**Distributive Laws:**
- A · (B + C) = (A · B) + (A · C)
- A + (B · C) = (A + B) · (A + C)

**De Morgan's Laws:**
- ¬(A + B) = ¬A · ¬B
- ¬(A · B) = ¬A + ¬B

"NOT (this OR that) = NOT this AND NOT that"

(NOT this) AND (NOT that)"

**Absorption Laws:**
- A + (A · B) = A
- A · (A + B) = A

### Boolean Expressions

A **Boolean expression** combines variables and operations.

**Example:** F = (A · B) + (¬A · C)

This means: F is true if (A and B are both true) OR (A is false and C is true)

### Truth Tables for Boolean Expressions

**Example:** F = (A + B) · C

```
A  B  C  | A+B | F=(A+B)·C
0  0  0  |  0  |    0
0  0  1  |  0  |    0
0  1  0  |  1  |    0
0  1  1  |  1  |    1
1  0  0  |  1  |    0
1  0  1  |  1  |    1
1  1  0  |  1  |    0
1  1  1  |  1  |    1
```

### Simplifying Boolean Expressions

Use the laws to make expressions simpler!

**Example 1:**
- F = A · B + A · ¬B
- F = A · (B + ¬B)  [Distributive law]
- F = A · 1  [Complement law]
- F = A  [Identity law]

**Example 2:**
- F = (A + B) · (A + C)
- F = A + (B · C)  [Distributive law]

**Why simplify?**
- Fewer operations = faster circuits
- Less hardware = cheaper computers
- Simpler expressions = easier to understand

### Karnaugh Maps (K-Maps)

A **Karnaugh map** is a visual tool for simplifying Boolean expressions.

**For 2 variables:**
```
     B'  B
A'  [ ][ ]
A   [ ][ ]
```

**For 3 variables (A, B, C):**
```
      B'C' B'C BC BC'
A'   [ ] [ ][ ][ ]
A    [ ] [ ][ ][ ]
```

**How to use:**
1. Fill in 1s where the function is true
2. Group adjacent 1s in powers of 2 (1, 2, 4, 8...)
3. Each group gives you a simpler term
4. Combine all terms with OR

**Example:** F(A,B,C) is true for minterms 0,2,5,7
```
      B'C' B'C BC BC'
A'    1    0  0  1
A     0    1  1  0
```

Groups:
- Top row (A'B'C' and A'BC'): gives A'C'
- Right column middle entries (ABC' and ABC): gives AB

Result: F = A'C' + AB

### Canonical Forms

**1. Sum of Products (SOP)**
- OR of ANDs
- Example: F = AB + A'C + BC'

**2. Product of Sums (POS)**
- AND of ORs
- Example: F = (A+B) · (A'+C) · (B+C')

**Minterms:** Products where each variable appears once
- For 3 variables: A'B'C' is minterm 0, A'B'C is minterm 1, etc.

**Maxterms:** Sums where each variable appears once
- For 3 variables: A+B+C is maxterm 0, A+B+C' is maxterm 1, etc.

### Logic Gates

**Physical implementations of Boolean operations:**

**NOT Gate (Inverter):**
```
A --[>o-- ¬A
```

**AND Gate:**
```
A --\
     )--- A·B
B --/
```

**OR Gate:**
```
A --\
     )--- A+B
B --/
```

**NAND Gate:**
```
A --\
     )o-- ¬(A·B)
B --/
```

**NOR Gate:**
```
A --\
     )o-- ¬(A+B)
B --/
```

**XOR Gate:**
```
A --\
     )=-- A⊕B
B --/
```

**Fun Fact:** NAND and NOR are **universal gates** - you can build ANY circuit using only NAND gates (or only NOR gates)!

### Combinational Circuits

Circuits where output depends only on current inputs (no memory).

**Examples:**

**1. Half Adder** (adds two bits):
- Inputs: A, B
- Outputs: Sum = A ⊕ B, Carry = A · B

**2. Full Adder** (adds three bits):
- Inputs: A, B, Carry_in
- Outputs: Sum = A ⊕ B ⊕ Carry_in
- Carry_out = (A·B) + (B·Carry_in) + (A·Carry_in)

**3. Multiplexer (MUX)** - selects one input:
- 2-to-1 MUX: Output = (¬S · A) + (S · B)
- When S=0, output A; when S=1, output B

**4. Decoder** - activates one output line:
- 2-to-4 decoder: 2 input bits select which of 4 outputs is active

### Sequential Circuits

Circuits with memory - output depends on inputs AND history.

**Examples:**
- **Flip-flops:** Store one bit
- **Registers:** Store multiple bits
- **Counters:** Count events
- **State machines:** Control sequences

---

## 12. Sequences and Recurrence Relations

### What is a Sequence?

A **sequence** is an ordered list of numbers: a₁, a₂, a₃, ...

**Examples:**
- 2, 4, 6, 8, 10, ... (even numbers)
- 1, 1, 2, 3, 5, 8, 13, ... (Fibonacci)
- 1, 4, 9, 16, 25, ... (perfect squares)

### Types of Sequences

**1. Arithmetic Sequence**
- Each term differs from the previous by a constant (common difference d)
- aₙ = a₁ + (n-1)d

**Example:** 3, 7, 11, 15, 19, ...
- First term a₁ = 3
- Common difference d = 4
- Formula: aₙ = 3 + (n-1)×4 = 4n - 1

**2. Geometric Sequence**
- Each term is the previous multiplied by a constant (common ratio r)
- aₙ = a₁ × rⁿ⁻¹

**Example:** 2, 6, 18, 54, 162, ...
- First term a₁ = 2
- Common ratio r = 3
- Formula: aₙ = 2 × 3ⁿ⁻¹

### Series (Sums of Sequences)

A **series** is the sum of terms in a sequence.

**1. Arithmetic Series**
- Sum of first n terms: Sₙ = n(a₁ + aₙ)/2
- Or: Sₙ = n[2a₁ + (n-1)d]/2

**Example:** Sum of 1 + 2 + 3 + ... + 100
- S₁₀₀ = 100(1 + 100)/2 = 100(101)/2 = 5050

**Famous story:** Young Gauss solved this in seconds by noticing pairs sum to 101!

**2. Geometric Series**
- Sum of first n terms: Sₙ = a₁(1 - rⁿ)/(1 - r) for r ≠ 1

**Example:** 2 + 6 + 18 + 54 + 162
- S₅ = 2(1 - 3⁵)/(1 - 3) = 2(1 - 243)/(-2) = 2(242)/2 = 242

**Infinite Geometric Series (|r| < 1):**
- S∞ = a₁/(1 - r)

**Example:** 1 + 1/2 + 1/4 + 1/8 + ...
- S∞ = 1/(1 - 1/2) = 1/(1/2) = 2

### Recurrence Relations

A **recurrence relation** defines each term using previous terms.

**General form:** aₙ = f(aₙ₋₁, aₙ₋₂, ..., a₁)

**Example:** aₙ = 2aₙ₋₁ + 3 with a₁ = 1
- a₁ = 1
- a₂ = 2(1) + 3 = 5
- a₃ = 2(5) + 3 = 13
- a₄ = 2(13) + 3 = 29

### Famous Recurrence Relations

**1. Fibonacci Sequence**
- Fₙ = Fₙ₋₁ + Fₙ₋₂ with F₁ = 1, F₂ = 1
- 1, 1, 2, 3, 5, 8, 13, 21, 34, ...

**Closed form (Binet's formula):**
- Fₙ = [φⁿ - (-φ)⁻ⁿ]/√5
- Where φ = (1 + √5)/2 ≈ 1.618 (golden ratio!)

**2. Tower of Hanoi**
- Tₙ = 2Tₙ₋₁ + 1 with T₁ = 1
- Solution: Tₙ = 2ⁿ - 1

**3. Factorial**
- n! = n × (n-1)! with 0! = 1
- 1, 1, 2, 6, 24, 120, 720, ...

### Solving Recurrence Relations

**Method 1: Iteration (Unrolling)**

Expand the recurrence repeatedly until you see a pattern.

**Example:** aₙ = 2aₙ₋₁ with a₁ = 3
- aₙ = 2aₙ₋₁
- aₙ = 2(2aₙ₋₂) = 2²aₙ₋₂
- aₙ = 2²(2aₙ₋₃) = 2³aₙ₋₃
- Pattern: aₙ = 2ⁿ⁻¹a₁ = 2ⁿ⁻¹ × 3 = 3 × 2ⁿ⁻¹

**Method 2: Characteristic Equation**

For linear homogeneous recurrences: aₙ = c₁aₙ₋₁ + c₂aₙ₋₂

**Steps:**
1. Write characteristic equation: r² = c₁r + c₂
2. Solve for roots r₁, r₂
3. General solution: aₙ = A × r₁ⁿ + B × r₂ⁿ
4. Use initial conditions to find A and B

**Example:** aₙ = 5aₙ₋₁ - 6aₙ₋₂ with a₀ = 1, a₁ = 2

Characteristic equation: r² = 5r - 6
- r² - 5r + 6 = 0
- (r - 2)(r - 3) = 0
- r₁ = 2, r₂ = 3

General solution: aₙ = A × 2ⁿ + B × 3ⁿ

Using initial conditions:
- a₀ = 1: A + B = 1
- a₁ = 2: 2A + 3B = 2

Solving: A = 1, B = 0
Therefore: aₙ = 2ⁿ

**Method 3: Generating Functions**

Create a function whose coefficients are the sequence terms. Advanced but powerful!

### Common Sequence Patterns

**1. Triangular Numbers**
- 1, 3, 6, 10, 15, 21, ...
- aₙ = n(n+1)/2
- Number of dots in a triangle of size n

**2. Square Numbers**
- 1, 4, 9, 16, 25, 36, ...
- aₙ = n²

**3. Cube Numbers**
- 1, 8, 27, 64, 125, ...
- aₙ = n³

**4. Prime Numbers**
- 2, 3, 5, 7, 11, 13, 17, 19, 23, ...
- No simple formula! That's what makes them special.

**5. Catalan Numbers**
- 1, 1, 2, 5, 14, 42, 132, ...
- Cₙ = (2n)! / [(n+1)! × n!]
- Count many things: binary trees, parenthesizations, paths

**6. Powers of 2**
- 1, 2, 4, 8, 16, 32, 64, ...
- aₙ = 2ⁿ⁻¹

### Applications of Sequences

**1. Computer Science**
- Algorithm analysis: recurrences describe running time
- Data structures: array indexing uses sequences
- Dynamic programming: builds solutions sequentially

**2. Finance**
- Compound interest: geometric sequence
- Loan payments: involves arithmetic and geometric series

**3. Biology**
- Population growth: Fibonacci and other sequences
- DNA sequences

**4. Physics**
- Wave patterns
- Harmonic series in music

---

## Putting It All Together: Real-World Applications

### Cryptography (RSA)
Uses: Number theory (primes, modular arithmetic, Euler's phi function)

**How it works:**
1. Choose two large primes (number theory)
2. Compute products and phi function
3. Use modular exponentiation (algorithms)
4. Encrypt/decrypt using Boolean operations at hardware level

### Internet Routing
Uses: Graph theory, algorithms

**How it works:**
1. Model internet as a graph (routers = vertices, connections = edges)
2. Find shortest path (Dijkstra's algorithm)
3. Handle failures (alternative paths, spanning trees)

### Social Networks
Uses: Graph theory, combinatorics, probability

**Applications:**
1. Friend recommendations (graph algorithms)
2. Counting connections (combinatorics)
3. Predicting behavior (probability)
4. Detecting communities (graph clustering)

### Search Engines
Uses: Graph theory, logic, sets, algorithms

**How Google works:**
1. Web as a graph (PageRank algorithm)
2. Boolean logic for queries (AND, OR, NOT)
3. Set operations for results
4. Efficient data structures (trees, hash tables)

### Data Compression
Uses: Trees (Huffman coding), information theory

**How ZIP files work:**
1. Build frequency table (counting)
2. Create Huffman tree
3. Assign codes (shorter for frequent characters)
4. Encode data using Boolean operations

### Game Theory
Uses: Logic, probability, combinatorics, graphs

**Applications:**
1. Chess AI: game trees, minimax algorithm
2. Poker: probability, expected value
3. Strategy games: graph search, optimization

### Machine Learning
Uses: Everything!

**Components:**
1. Algorithms for learning
2. Probability for predictions
3. Linear algebra (vectors, matrices)
4. Graph theory for neural networks
5. Optimization

---

## Practice Problems (By Topic)

### Logic and Proofs
1. Prove: If n² is even, then n is even
2. Use truth tables to show: (A → B) ≡ (¬A ∨ B)
3. Prove by induction: 1² + 2² + ... + n² = n(n+1)(2n+1)/6

### Sets
1. Given A = {1,2,3,4}, B = {3,4,5,6}, find:
   - A ∪ B, A ∩ B, A - B, B - A
2. How many subsets does {a, b, c, d, e} have?
3. Prove: A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)

### Counting
1. How many 4-digit PIN codes are possible if digits can repeat?
2. How many ways can you arrange 5 books on a shelf?
3. From 10 students, choose 3 for a team. How many ways?
4. How many 5-card poker hands are possible?

### Probability
1. Two dice are rolled. What's P(sum = 7)?
2. A bag has 5 red, 3 blue marbles. Draw 2 without replacement. P(both red)?
3. Given P(A) = 0.6, P(B) = 0.4, P(A ∩ B) = 0.2, find P(A ∪ B)

### Graph Theory
1. Draw K₄ (complete graph with 4 vertices)
2. Does this graph have an Euler circuit: vertices with degrees 2,2,3,3?
3. Find shortest path in a weighted graph using Dijkstra's algorithm

### Trees
1. How many edges in a tree with 15 vertices?
2. Draw a binary search tree for: 8, 3, 10, 1, 6, 14, 4, 7
3. Give preorder, inorder, and postorder traversals

### Number Theory
1. Find GCD(48, 180) using Euclidean algorithm
2. Find all solutions: 3x ≡ 5 (mod 7)
3. Is 91 prime? If not, find its prime factorization

### Algorithms
1. Use binary search to find 42 in [5,12,18,27,42,55,67,89]
2. Sort [5,2,8,1,9] using bubble sort (show all steps)
3. What's the time complexity of nested loops from 1 to n?

### Boolean Algebra
1. Simplify: A·B + A·¬B
2. Convert to SOP: (A+B)·(B+C)
3. Draw truth table for: F = A⊕B⊕C

### Sequences
1. Find the 10th term: 3, 7, 11, 15, ...
2. Sum: 1 + 2 + 4 + 8 + ... + 512
3. Solve: aₙ = 3aₙ₋₁ - 2aₙ₋₂ with a₀ = 1, a₁ = 2

---

## Tips for Success in Discrete Math

### 1. Practice, Practice, Practice
- Work through problems yourself
- Don't just read solutions - solve them!
- Do extra problems beyond homework

### 2. Draw Pictures
- Venn diagrams for sets
- Graphs and trees
- Truth tables
- Visual representations help understanding!

### 3. Check Your Work
- Test with small examples
- Verify edge cases
- Make sure logic is sound

### 4. Understand, Don't Memorize
- Focus on WHY formulas work
- Understand the reasoning
- Memorization alone won't help with new problems

### 5. Make Connections
- See how topics relate
- Graph theory uses sets
- Algorithms use counting
- Everything connects!

### 6. Start Simple
- Test ideas with small numbers
- Build up to complex cases
- Simple examples reveal patterns

### 7. Learn from Mistakes
- Wrong answers teach you!
- Figure out where you went wrong
- Mistakes are part of learning

### 8. Form Study Groups
- Explain concepts to others
- Teaching helps you learn
- Different perspectives help

---

## Final Thoughts

Discrete mathematics is the foundation of computer science and has applications everywhere in the digital world. Every time you:
- Send a secure message (cryptography)
- Use GPS (graph algorithms)
- Search the web (Boolean logic, algorithms)
- Play a video game (trees, graphs, algorithms)
- Use social media (graph theory)

...you're using discrete math!

The beauty of discrete math is that it's:
- **Concrete:** No infinitesimals or limits - just clear, distinct objects
- **Logical:** Every statement can be proven true or false
- **Applicable:** Powers the entire digital revolution
- **Accessible:** Anyone can learn it with practice

Remember: Mathematics is not about memorizing formulas. It's about:
- **Understanding patterns**
- **Solving problems creatively**
- **Thinking logically**
- **Building on simple ideas to reach complex solutions**

Start with the basics, practice regularly, and don't be afraid to make mistakes. Every expert was once a beginner!

**You now have a comprehensive foundation in discrete mathematics. Go forth and solve problems!** 🎉

---

## Quick Reference: Key Formulas

**Combinatorics:**
- Permutations: P(n,r) = n!/(n-r)!
- Combinations: C(n,r) = n!/[r!(n-r)!]
- Binomial: (a+b)ⁿ = Σ C(n,k)aⁿ⁻ᵏbᵏ

**Probability:**
- P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
- P(A|B) = P(A ∩ B)/P(B)
- Expected value: E(X) = Σ xᵢP(xᵢ)

**Sequences:**
- Arithmetic: aₙ = a₁ + (n-1)d
- Geometric: aₙ = a₁rⁿ⁻¹
- Arithmetic sum: Sₙ = n(a₁+aₙ)/2
- Geometric sum: Sₙ = a₁(1-rⁿ)/(1-r)

**Number Theory:**
- Euclidean algorithm: GCD(a,b) = GCD(b, a mod b)
- LCM(a,b) = ab/GCD(a,b)
- Fermat's Little Theorem: aᵖ⁻¹ ≡ 1 (mod p)

**Graph Theory:**
- Handshaking Lemma: Σ deg(v) = 2|E|
- Tree edges: |E| = |V| - 1

**Boolean Algebra:**
- De Morgan's: ¬(A∨B) = ¬A∧¬B, ¬(A∧B) = ¬A∨¬B
- Distributive: A∧(B∨C) = (A∧B)∨(A∧C)

Happy learning! 🚀