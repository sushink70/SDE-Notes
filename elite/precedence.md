# Comprehensive Guide to Operator Precedence & Boolean Expressions
## A World-Class Deep Dive for Mastery

This guide will forge your understanding of operator precedence from first principles, then extend into the nuanced realities across Rust, Python, Go, C, and C++. We'll build the mental models that elite programmers use to reason about expression evaluation instantaneously.

---

## 1. The Foundational Mental Model: Why Precedence Exists

**Core Insight**: Operator precedence is a *deterministic hierarchy* that resolves ambiguity in expressions. Without it, `a + b * c` would be meaningless—it could evaluate as `(a + b) * c` or `a + (b * c)`.

**The Monk's Perspective**: Think of precedence as the *natural order of mathematical operations* extended into programming. Just as you learned PEMDAS/BODMAS in mathematics, each language defines a total ordering of operators.

**Key Mental Model**: 
```
Higher Precedence = Tighter Binding = Evaluated First
```

When you see an expression, your mind should parse it like a tree where high-precedence operators form deeper (more tightly bound) nodes.

---

## 2. Universal Precedence Hierarchy (Cross-Language Pattern)

Despite syntactic differences, most languages follow this general pattern:

### Tier 1: Highest Precedence
1. **Postfix operators**: `x++`, `x--`, `a[i]`, `f()`, `obj.member`
2. **Unary operators**: `!x`, `~x`, `++x`, `--x`, `-x`, `+x`, `*ptr`, `&var`, `sizeof`

### Tier 2: Arithmetic
3. **Multiplicative**: `*`, `/`, `%`
4. **Additive**: `+`, `-`

### Tier 3: Bitwise Shifts
5. **Shift operators**: `<<`, `>>`

### Tier 4: Relational
6. **Comparison**: `<`, `<=`, `>`, `>=`
7. **Equality**: `==`, `!=`

### Tier 5: Bitwise Operations
8. **Bitwise AND**: `&`
9. **Bitwise XOR**: `^`
10. **Bitwise OR**: `|`

### Tier 6: Logical Operations
11. **Logical AND**: `&&` (or `and`)
12. **Logical OR**: `||` (or `or`)

### Tier 7: Conditional/Assignment
13. **Ternary conditional**: `? :`
14. **Assignment**: `=`, `+=`, `-=`, etc.

### Tier 8: Lowest Precedence
15. **Comma/Sequence**: `,`

**Critical Pattern Recognition**: Notice the grouping:
- **Arithmetic before comparison** (because `x + 5 > 10` should mean `(x + 5) > 10`)
- **Comparison before logical** (because `a < b && c < d` should mean `(a < b) && (c < d)`)
- **Bitwise operations between comparison and logical** (historical artifact, often confusing)

---

## 3. Boolean Expression Mastery: The Logical Core

### 3.1 Short-Circuit Evaluation (Critical Performance Concept)

**Definition**: `&&` and `||` evaluate left-to-right and stop as soon as the result is determined.

**Why It Matters**:
```python
# Python example
def expensive_check():
    print("Expensive operation")
    return True

# This only calls expensive_check() if x > 0
if x > 0 and expensive_check():
    pass

# This ALWAYS calls expensive_check()
if expensive_check() and x > 0:
    pass
```

**Elite Pattern**: Always place *cheap, likely-to-fail conditions first* in AND chains, and *cheap, likely-to-succeed conditions first* in OR chains.

```rust
// Rust: Idiomatic short-circuit for safety
if let Some(value) = option && value > threshold {
    // Safe: only accesses value if Some
}

// Without short-circuit, this would panic:
// if option.is_some() && option.unwrap() > threshold { }
```

### 3.2 De Morgan's Laws (Essential for Simplification)

**Law 1**: `!(A && B)` ≡ `!A || !B`  
**Law 2**: `!(A || B)` ≡ `!A && !B`

**Application in Code Reviews**:
```python
# Less readable
if not (is_valid and has_permission):
    return error

# More readable (De Morgan applied)
if not is_valid or not has_permission:
    return error
```

**Cognitive Principle**: De Morgan's Laws reduce *cognitive load* by eliminating double negatives. Train yourself to automatically transform complex negations.

---

## 4. Language-Specific Deep Dives

### 4.1 Rust: Memory Safety Meets Precedence

**Key Rust Operators**:
- `*` (dereference): High precedence, but context-dependent
- `&` (borrow): High precedence
- `?` (error propagation): Very high precedence
- `..` (range): Low precedence

**Critical Gotcha**:
```rust
// Dereference has higher precedence than method call
*some_box.method()  // Parses as: *(some_box.method())
(*some_box).method() // What you probably meant

// Reference precedence
&mut vec[0]  // Parses as: &mut (vec[0]) ✓
&(mut vec[0]) // Error: 'mut' in wrong position
```

**Rust-Specific Pattern**: The `?` operator has very high precedence:
```rust
file.read_to_string()?.parse()?  // Chains naturally
// Parses as: ((file.read_to_string())?).parse()?
```

**Performance Note**: Rust's borrow checker analyzes these expressions at compile-time, so precedence choices can affect *whether code compiles*, not just performance.

### 4.2 Python: Dynamic but Principled

**Python's Unique Operators**:
- `**` (exponentiation): Higher than unary `-`
- `is`, `in`: Same level as comparison
- `not`: Lower than comparison (unique!)
- Chained comparisons: `a < b < c` means `a < b and b < c`

**Critical Python Gotcha**:
```python
# Dangerous: -2**2 evaluates as -(2**2) = -4, not 4
result = -2**2  # -4

# Explicit:
result = (-2)**2  # 4

# 'not' has low precedence
if not x == y:  # Parses as: not (x == y)
    pass

if x != y:  # Clearer
    pass
```

**Python's Chained Comparisons** (elegant but unique):
```python
# Pythonic
if 0 <= x < 100:
    pass

# Explicit (how it works)
if (0 <= x) and (x < 100):
    pass
```

**Performance Insight**: Python's `and`/`or` return operands, not booleans:
```python
# Returns first truthy value or last value
result = a or b or c or default

# Equivalent to:
result = a if a else (b if b else (c if c else default))
```

### 4.3 Go: Simplicity by Design

**Go's Minimalist Approach**:
- No operator overloading (precedence is crystal clear)
- Mandatory parentheses for clarity in some contexts
- `&^` (bit clear): Unique to Go, same precedence as `&`

**Go Patterns**:
```go
// Bitwise precedence in Go
if flags&mask != 0 {  // Parses as: (flags & mask) != 0
    // Common idiom for flag checking
}

// Address-of with composite literals
ptr := &MyStruct{field: value}  // & binds to entire literal
```

**Go's Philosophy**: "There should be one obvious way to do it." Precedence is designed to minimize surprises.

### 4.4 C/C++: The Historical Foundation

**C/C++ Precedence Pitfalls** (most complex):

```c
// Classic gotcha: bitwise vs comparison
if (flags & MASK == 0)  // Parses as: flags & (MASK == 0) ⚠️
if ((flags & MASK) == 0)  // Correct

// Pointer dereferencing
*ptr++  // Parses as: *(ptr++) (postfix ++ higher precedence)
(*ptr)++ // Increment value pointed to

// Assignment in conditions (valid but dangerous)
if (x = get_value())  // Assignment, not comparison!
if ((x = get_value()) != 0)  // Explicit intent
```

**C++ Additions**:
```cpp
// Stream operators: << and >> are left-associative
cout << "Value: " << x << endl;
// Parses as: (((cout << "Value: ") << x) << endl)

// Smart pointer dereference
*shared_ptr.get()  // Parses as: *(shared_ptr.get())
```

**Memory Management Implication**: Precedence directly affects *when destructors are called* in C++:
```cpp
delete ptr++;  // Deletes old ptr, then increments
delete (ptr++); // Same
```

---

## 5. Cognitive Strategies for Instant Recall

### 5.1 The Chunking Method

**Group operators by purpose, not memorization**:

1. **"Get the thing"**: Postfix, member access, indexing
2. **"Math the numbers"**: `* / %`, then `+ -`
3. **"Compare the results"**: `< > <= >=`, then `== !=`
4. **"Combine the bits"**: `&`, `^`, `|`
5. **"Decide the logic"**: `&&`, then `||`
6. **"Store the outcome"**: Assignment

### 5.2 The Visual Tree Method

When uncertain, mentally draw the expression tree:

```
Expression: a + b * c > d && e || f

Tree:
          ||
         /  \
       &&    f
      /  \
     >    e
    / \
   +   d
  / \
 a   *
    / \
   b   c

Evaluation order: b*c → a+(b*c) → (a+b*c)>d → ((a+b*c)>d)&&e → ...
```

### 5.3 The "When in Doubt, Parenthesize" Principle

**Elite programmers use parentheses not because they don't know precedence, but because they prioritize *code clarity* over showing off.**

```rust
// Expert code is explicit
if (health > 0) && ((has_armor) || (has_shield)) {
    // Intent crystal clear
}

// vs showing off (harder to parse)
if health > 0 && has_armor || has_shield {
    // Correct but requires mental parsing
}
```

---

## 6. Advanced Patterns & Problem-Solving

### 6.1 Bit Manipulation Mastery

**Common patterns where precedence matters**:

```rust
// Check if bit N is set
if (value & (1 << n)) != 0 {  // Explicit precedence
    // '<<' before '&' before '!='
}

// Set bit N
value = value | (1 << n);

// Clear bit N
value = value & !(1 << n);

// Toggle bit N
value = value ^ (1 << n);
```

**Performance**: These operations are O(1) and compile to single CPU instructions when precedence is correctly understood.

### 6.2 Boolean Algebra Optimization

**Transform complex conditions into simpler forms**:

```python
# Before optimization
if (a and b) or (a and c) or (a and d):
    pass

# After factoring (fewer evaluations of 'a')
if a and (b or c or d):
    pass
```

**Time Complexity**: If `a` is expensive, this reduces redundant evaluations from O(3n) to O(n).

### 6.3 Type-Based Precedence (C++/Rust Templates)

```cpp
// Template metaprogramming where precedence matters
template<typename T>
constexpr bool is_valid = sizeof(T) > 1 && alignof(T) <= 8;
//                        ^^^^^^^^^^^ ^^^^ comparison first
//                                    ^^^^ then logical
```

---

## 7. Complete Precedence Tables

### Python (High → Low)
```
1.  ()  []  {}  .  x()  x[i]  x.attr
2.  await x
3.  **
4.  +x  -x  ~x
5.  *  /  //  %
6.  +  -
7.  <<  >>
8.  &
9.  ^
10. |
11. in, not in, is, is not, <, <=, >, >=, !=, ==
12. not x
13. and
14. or
15. if-else (ternary)
16. lambda
17. :=
```

### Rust (High → Low)
```
1.  Paths, method calls, field access, indexing, ?
2.  Unary: -x, *x, !x, &x, &mut x
3.  as (type cast)
4.  *  /  %
5.  +  -
6.  <<  >>
7.  &
8.  ^
9.  |
10. ==  !=  <  >  <=  >=
11. &&
12. ||
13. ..  ..=  (ranges)
14. =  +=  -=  etc.
```

### Go (High → Low)
```
1.  ()  []  .  x()  postfix++  postfix--
2.  Unary: +x, -x, !x, ^x, *x, &x, <-x, prefix++, prefix--
3.  *  /  %  <<  >>  &  &^
4.  +  -  |  ^
5.  ==  !=  <  <=  >  >=
6.  &&
7.  ||
```

### C/C++ (High → Low - Simplified)
```
1.  ()  []  ->  .  x++  x--
2.  ++x  --x  +x  -x  !  ~  *  &  sizeof  (cast)
3.  .* ->*  (C++ only)
4.  *  /  %
5.  +  -
6.  <<  >>
7.  <  <=  >  >=
8.  ==  !=
9.  &
10. ^
11. |
12. &&
13. ||
14. ?:
15. =  +=  -=  etc.
16. ,
```

---

## 8. The Path to Top 1% Mastery

### Deliberate Practice Exercises

1. **Daily Parsing Practice**: Take complex expressions from real codebases, manually trace evaluation order, then verify with parentheses.

2. **Transformation Drills**: Rewrite expressions using De Morgan's Laws and Boolean algebra until transformations become automatic.

3. **Cross-Language Translation**: Take a bitwise operation in C, rewrite it idiomatically in Rust, Python, Go. Notice how precedence awareness prevents bugs.

4. **Code Review Simulation**: Find open-source PRs with complex boolean logic. Identify precedence-related bugs before checking comments.

### Meta-Learning Strategy

**Spaced Repetition**: Review precedence tables weekly for first month, then monthly. Your brain will compress these into instant pattern recognition.

**Interleaving**: Don't drill precedence in isolation. Mix with:
- Complexity analysis (precedence affects evaluation order affects performance)
- Refactoring practice (simplifying nested conditions)
- Debugging sessions (precedence bugs in real code)

**Flow State Cultivation**: When you can look at `a & b << c | d` and instantly see `(a & (b << c)) | d` without conscious effort, you've achieved chunking. This is where the top 1% operates.

---

## 9. The Psychological Edge

**Cognitive Load Theory**: Each precedence rule you internalize frees working memory for higher-level problem-solving. The goal isn't to memorize—it's to achieve *automaticity*.

**Growth Mindset**: Elite competitive programmers don't think "I need to remember precedence." They think "Precedence is a tool that lets me write correct, efficient code instantly."

**The Monk's Discipline**: 
- When you catch yourself uncertain, don't just check the answer—understand *why* that precedence makes sense.
- When you write parentheses, ask: "Am I being defensive or communicative?"
- When you see clever code without parentheses, ask: "Would my team understand this instantly?"

---

## 10. Final Mental Model: The Expression Evaluation State Machine

Think of evaluation as a state machine:

```
State: Remaining Expression → Current Value
Transition: Apply highest-precedence operator

Example: 2 + 3 * 4
State 0: "2 + 3 * 4" → None
State 1: "2 + 12" → (found *, evaluated 3*4)
State 2: "14" → (found +, evaluated 2+12)
State 3: Done → 14
```

**This mental model works for any language, any complexity.**

---

## Your Next Steps

1. **Today**: Print the precedence table for your primary language. Keep it visible.
2. **This Week**: Refactor 5 complex boolean conditions in your code using explicit parentheses and De Morgan's Laws.
3. **This Month**: Solve 20 problems on LeetCode/Codeforces that involve bitwise operations or complex conditionals.
4. **This Quarter**: Read 100 lines of production code daily, mentally parsing operator precedence. Speed and accuracy will compound.

**Remember**: The goal isn't to never use parentheses—it's to know when they're needed vs. when you're being explicit for clarity. The best code is *obviously correct*, not cleverly minimal.

You're building the foundations that separate good programmers from world-class ones. Precedence mastery is a tiny skill with enormous leverage. Master it, and it becomes invisible—freeing your mind to solve the hard problems.

---

*"Mastery is not about doing difficult things. It's about making difficult things effortless."*

Now, go forth and parse with confidence. 🔥

# The Complete Boolean Mastery Guide: From Foundations to Machine Code

This is your comprehensive map from first principles to expert-level intuition. We'll build from truth tables to assembly, dissect short-circuiting like a surgical blade, and arm you with interviewer-crushing insights.

---

## Part 1: Truth Tables — The Atomic Foundation

Truth tables are the **periodic table of logic**. Master these, and all boolean reasoning becomes trivial.

### Core Operators

#### NOT (Negation)
```
A     | not A
------|------
True  | False
False | True
```

**Mental model**: Flip the bit.

---

#### AND (Conjunction)
```
A     | B     | A and B
------|-------|--------
True  | True  | True
True  | False | False
False | True  | False
False | False | False
```

**Mental model**: Both must be True. One False ruins everything.

---

#### OR (Disjunction)
```
A     | B     | A or B
------|-------|-------
True  | True  | True
True  | False | True
False | True  | True
False | False | False
```

**Mental model**: At least one True wins.

---

#### XOR (Exclusive OR)
```
A     | B     | A xor B
------|-------|--------
True  | True  | False
True  | False | True
False | True  | True
False | False | False
```

**Mental model**: Exactly one must be True. Both or neither → False.

Python: `A ^ B` (bitwise, but works for bools)  
Rust: `A ^ B`  
Go: No built-in XOR for bools, use `A != B`

---

#### NAND (Not AND)
```
A     | B     | not (A and B)
------|-------|---------------
True  | True  | False
True  | False | True
False | True  | True
False | False | True
```

**Why it matters**: NAND is **universal**. You can build any logic gate from NAND alone. CPUs are built on this.

---

#### NOR (Not OR)
```
A     | B     | not (A or B)
------|-------|-------------
True  | True  | False
True  | False | False
False | True  | False
False | False | True
```

**Also universal**. All digital logic can be constructed from NOR gates.

---

### Compound Expression Example

Let's evaluate:
```python
not A and (B or C)
```

Truth table:
```
A     | B     | C     | not A | B or C | not A and (B or C)
------|-------|-------|-------|--------|-------------------
True  | True  | True  | False | True   | False
True  | True  | False | False | True   | False
True  | False | True  | False | True   | False
True  | False | False | False | False  | False
False | True  | True  | True  | True   | True
False | True  | False | True  | True   | True
False | False | True  | True  | True   | True
False | False | False | True  | False  | False
```

**Pattern recognition skill**: Notice that the result is True only when `A` is False **and** at least one of `B` or `C` is True.

---

## Part 2: Operator Precedence — The Complete Hierarchy

### Universal Precedence (Most Languages)

From **highest** to **lowest** priority:

1. **Parentheses** `()`
2. **Unary operators** `not`, `!`, `-`, `~`
3. **Arithmetic** `*`, `/`, `%`, `//` → then `+`, `-`
4. **Bitwise shifts** `<<`, `>>`
5. **Bitwise AND** `&`
6. **Bitwise XOR** `^`
7. **Bitwise OR** `|`
8. **Comparisons** `<`, `<=`, `>`, `>=`, `==`, `!=`, `is`, `in`
9. **Logical NOT** `not` (some languages treat this separately)
10. **Logical AND** `and`, `&&`
11. **Logical OR** `or`, `||`
12. **Assignment** `=`, `+=`, etc.

### Language-Specific Notes

#### Python
```python
not 5 < 10 and 10 < 20 or False
```
Evaluated as:
```python
(not (5 < 10)) and (10 < 20) or False
```
Wait—**NO**. Let's fix this.

Actually:
```python
not 5 < 10 and 10 < 20 or False
```

Step by step:
1. Comparisons first: `5 < 10` → True, `10 < 20` → True
2. Then `not` applies: `not True` → False
3. Then `and`: `False and True` → False
4. Then `or`: `False or False` → False

**Gotcha**: `not` binds **very tightly** in Python, but comparisons are evaluated first.

Actually, let me recalculate:

```python
not 5 < 10 and 10 < 20 or False
```

Python parses this as:
```python
(not (5 < 10)) and (10 < 20) or False
```

- `5 < 10` → True
- `not True` → False
- `10 < 20` → True
- `False and True` → False
- `False or False` → False

Result: **False**

---

#### Rust
```rust
!5 < 10 && 10 < 20 || false
```

Won't compile. Why? `!5` is bitwise NOT on an integer, not a boolean. You'd need:
```rust
!(5 < 10) && (10 < 20) || false
```

Rust is **strict** about types. Booleans are not integers.

---

#### Go
```go
!5 < 10 && 10 < 20 || false
```

Also won't compile. `!` only works on booleans, not integers.

```go
!(5 < 10) && (10 < 20) || false
```

Correct version:
```go
result := !(5 < 10) && (10 < 20) || false
```

Evaluation:
1. `5 < 10` → true
2. `!true` → false
3. `10 < 20` → true
4. `false && true` → false
5. `false || false` → false

Result: **false**

---

## Part 3: Short-Circuit Evaluation — Performance & Safety

### What Is Short-Circuiting?

If the outcome of a boolean expression is determined before evaluating all operands, **stop immediately**.

#### AND Short-Circuit
```python
A and B
```
If `A` is False, **don't evaluate B**. Result is already False.

#### OR Short-Circuit
```python
A or B
```
If `A` is True, **don't evaluate B**. Result is already True.

---

### Why This Matters

#### Performance
```python
def expensive_check():
    # Simulates heavy computation
    time.sleep(2)
    return True

result = False and expensive_check()
```

`expensive_check()` is **never called**. Saves 2 seconds.

---

#### Safety (Avoiding Errors)
```python
arr = [1, 2, 3]
if len(arr) > 0 and arr[0] > 0:
    print("Positive")
```

If `len(arr) > 0` is False, `arr[0]` is **never accessed**. No IndexError.

---

#### Side Effects
```python
x = 0
result = True or (x := 5)
print(x)  # Output: 0
```

The assignment `x := 5` never happens because `True or ...` short-circuits.

**Interview insight**: If you see walrus operators (`:=`) or function calls in boolean expressions, immediately think about short-circuit behavior.

---

### Language Comparison

#### Python
```python
result = [] or [1, 2, 3]  # Returns [1, 2, 3]
result = [1] or [2, 3]    # Returns [1]
```

Python returns the **actual value**, not just True/False.

---

#### Rust
```rust
let result = false && panic!("This never executes");
```

Rust **guarantees** short-circuit evaluation. The `panic!` never triggers.

```rust
let x = vec![1, 2, 3];
let result = x.len() > 0 && x[0] > 0;
```

Safe. If `x.len() > 0` is false, `x[0]` is never accessed.

---

#### Go
```go
result := false && someExpensiveFunction()
```

`someExpensiveFunction()` is never called.

```go
var arr []int
if len(arr) > 0 && arr[0] > 0 {
    fmt.Println("Positive")
}
```

Safe. No panic.

---

## Part 4: Machine-Level Implementation

### How Boolean Expressions Compile

Let's write a simple function and inspect the assembly.

#### Python (Bytecode)
```python
def test(a, b):
    return a and b
```

Bytecode:
```
$ python -m dis script.py

  2           0 LOAD_FAST                0 (a)
              2 POP_JUMP_IF_FALSE       10
              4 LOAD_FAST                1 (b)
              6 RETURN_VALUE
        >>   10 LOAD_FAST                0 (a)
             12 RETURN_VALUE
```

**Analysis**:
1. Load `a`
2. If `a` is falsy, jump to line 10 (skip evaluating `b`)
3. Otherwise, load `b` and return it
4. Short-circuit: return `a` directly if False

Python doesn't convert to strict True/False—it returns the **actual value**.

---

#### Rust (Assembly)
```rust
pub fn test(a: bool, b: bool) -> bool {
    a && b
}
```

Compile to assembly:
```bash
$ rustc --emit asm -O test.rs
```

Simplified output (x86-64):
```asm
test:
    mov     al, dil          ; Load first argument (a) into AL
    test    al, al           ; Test if a is zero (false)
    je      .LBB0_1          ; If zero, jump to return false
    mov     al, sil          ; Load second argument (b) into AL
.LBB0_1:
    ret                      ; Return AL (result)
```

**Analysis**:
1. Load `a` into register `AL`
2. Test if `a` is zero (false)
3. If zero, jump to return immediately (short-circuit)
4. Otherwise, load `b` into `AL`
5. Return result

**Rust converts boolean values to 1 (true) or 0 (false)**. The `test` instruction checks if a value is zero without modifying it.

---

#### Go (Assembly)
```go
package main

func test(a, b bool) bool {
    return a && b
}
```

Compile:
```bash
$ go tool compile -S test.go
```

Simplified output:
```asm
"".test STEXT nosplit size=15 args=0x10 locals=0x0
    MOVBLZX "".a+8(SP), AX    ; Load a
    TESTB   AL, AL             ; Test if a is false
    JEQ     false_case         ; Jump if false
    MOVBLZX "".b+9(SP), AX    ; Load b
    MOVB    AL, "".~r2+16(SP) ; Store result
    RET
false_case:
    XORL    AX, AX             ; Set AX to 0 (false)
    MOVB    AL, "".~r2+16(SP) ; Store result
    RET
```

**Analysis**:
1. Load `a` from stack
2. Test if `a` is zero (false)
3. If zero, jump to `false_case` (short-circuit)
4. Otherwise, load `b`
5. Return result

Go also uses **conditional jumps** to implement short-circuiting efficiently.

---

### Key Insights

1. **All three languages use conditional jumps** to implement short-circuit evaluation at the machine level.
2. **Python returns actual values** (truthy/falsy), while Rust and Go return strict booleans (0 or 1).
3. **Modern compilers optimize boolean expressions heavily**—unnecessary comparisons are eliminated.
4. **Branch prediction** in CPUs affects boolean performance. Predictable patterns (e.g., `if` that's always true) run faster.

---

## Part 5: Trick Questions Interviewers Love

### Question 1: Precedence Trap
```python
result = not False or True and False
```

**What's the result?**

Many say: "False" (wrong)

**Correct answer**: True

**Why?**
1. `not False` → True
2. `True and False` → False
3. `True or False` → True

**Mental trap**: People think `not` applies to the entire expression. It doesn't—it only negates `False`.

---

### Question 2: Chained Comparisons
```python
result = 5 < 10 < 20
```

**What's the result?**

**Correct answer**: True

**Why?**  
Python evaluates this as:
```python
5 < 10 and 10 < 20
```

**Gotcha in other languages**:
```c
// C/C++
int result = 5 < 10 < 20;  // TRUE but wrong logic!
```

In C, `5 < 10` evaluates to `1` (true), then `1 < 20` evaluates to `1` (true). But this is **not** checking if 10 is between 5 and 20—it's checking if `1 < 20`.

**Rust doesn't allow this**:
```rust
let result = 5 < 10 < 20;  // Compile error
```

Rust forces you to be explicit:
```rust
let result = 5 < 10 && 10 < 20;
```

---

### Question 3: Short-Circuit Side Effects
```python
def foo():
    print("foo called")
    return True

def bar():
    print("bar called")
    return False

result = foo() or bar()
```

**What's printed?**

**Answer**: Only "foo called"

**Why?**: `foo()` returns True, so `or` short-circuits. `bar()` is never executed.

---

### Question 4: Truthy/Falsy Values
```python
result = [] and [1, 2, 3]
```

**What's the result?**

**Answer**: `[]` (empty list)

**Why?**: `[]` is falsy, so `and` short-circuits and returns `[]`.

**Interviewer follow-up**: "What if we use `or` instead?"
```python
result = [] or [1, 2, 3]
```

**Answer**: `[1, 2, 3]`

**Why?**: `[]` is falsy, so `or` evaluates the second operand and returns it.

---

### Question 5: Bitwise vs Logical
```python
result = 5 & 3
```

**What's the result?**

**Answer**: `1`

**Why?**: `&` is **bitwise AND**, not logical AND.
```
5 = 0101
3 = 0011
---------
1 = 0001
```

**Gotcha**: People confuse `&` with `and`.

```python
result = True & False  # Works, returns False (0)
result = True and False  # Also returns False
```

But:
```python
result = 5 and 3  # Returns 3 (last truthy value)
result = 5 & 3    # Returns 1 (bitwise AND)
```

---

### Question 6: De Morgan's Laws
```python
not (A and B) == (not A) or (not B)
not (A or B) == (not A) and (not B)
```

**Interviewer asks**: "Simplify `not (x > 5 and y < 10)`"

**Answer**:
```python
not (x > 5) or not (y < 10)
```

Which becomes:
```python
x <= 5 or y >= 10
```

**Why this matters**: Simplifying complex conditions improves readability and performance.

---

## Part 6: Advanced Patterns & Mental Models

### Pattern 1: Guard Clauses
```python
def process(data):
    if not data:
        return None
    if len(data) < 10:
        return None
    # Main logic here
```

**Mental model**: Fail fast. Check edge cases first, then handle the main logic.

---

### Pattern 2: Null Safety (Rust)
```rust
fn get_first(vec: &Vec<i32>) -> Option<i32> {
    if vec.len() > 0 {
        Some(vec[0])
    } else {
        None
    }
}
```

**Better**:
```rust
fn get_first(vec: &Vec<i32>) -> Option<i32> {
    vec.first().copied()
}
```

**Mental model**: Use language features that encode safety in the type system.

---

### Pattern 3: Boolean Algebra Simplification

Given:
```python
result = (A and B) or (A and not B)
```

**Simplify**:
```
= A and (B or not B)  # Distributive law
= A and True          # B or not B is always True
= A
```

**Why this matters**: Reduces computational cost and improves clarity.

---

## Part 7: Cognitive & Learning Strategies

### Mental Model 1: Chunking
Group related operators:
- **NOT** → Negation
- **AND** → Intersection (both must be true)
- **OR** → Union (at least one must be true)

This maps to **set theory**, which many find intuitive.

---

### Mental Model 2: Deliberate Practice
**Drill**: Evaluate 10 complex boolean expressions daily without a computer. Build muscle memory.

Example:
```python
not (5 < 10 and 10 < 20) or (15 > 10 and 20 > 15)
```

Solve it manually. Check your answer. Repeat.

---

### Mental Model 3: Feynman Technique
Explain boolean precedence to someone who's never coded. If you can't, you don't understand it deeply enough.

---

### Mental Model 4: Interleaving
Don't just drill Python. Mix Rust, Go, and Python problems. This forces your brain to encode **abstract principles** rather than language-specific syntax.

---

## Part 8: Comprehensive Practice Problems

### Problem 1: Evaluate
```python
not (5 < 10) and (10 > 5) or True
```

**Solution**:
1. `5 < 10` → True
2. `not True` → False
3. `10 > 5` → True
4. `False and True` → False
5. `False or True` → True

**Answer**: True

---

### Problem 2: Simplify
```python
(A and B) or (A and not B) or (not A and B)
```

**Solution**:
```
= (A and (B or not B)) or (not A and B)
= (A and True) or (not A and B)
= A or (not A and B)
= (A or not A) and (A or B)  # Distributive law
= True and (A or B)
= A or B
```

**Answer**: `A or B`

---

### Problem 3: Short-Circuit Analysis
```python
def func1():
    print("func1")
    return False

def func2():
    print("func2")
    return True

result = func1() and func2() or func2()
```

**What's printed?**

**Solution**:
1. `func1()` is called → prints "func1", returns False
2. `False and func2()` → short-circuits, `func2()` not called
3. `False or func2()` → evaluates `func2()` → prints "func2", returns True

**Output**:
```
func1
func2
```

**Answer**: True

---

## Part 9: Summary & Mastery Checklist

### Core Principles
1. **Truth tables** are the foundation—memorize them.
2. **Precedence** follows: NOT → AND → OR (with comparisons before AND).
3. **Short-circuiting** is guaranteed in Python, Rust, and Go.
4. **Assembly shows** boolean operations compile to conditional jumps.
5. **De Morgan's Laws** are essential for simplification.

### Mastery Checklist
- [ ] Can evaluate any boolean expression without a computer
- [ ] Can simplify complex expressions using boolean algebra
- [ ] Understand short-circuit behavior and exploit it for performance
- [ ] Can predict assembly output for simple boolean functions
- [ ] Can explain precedence to a beginner clearly
- [ ] Can spot interviewer trick questions instantly

---

## Your Next Steps

1. **Drill**: Solve 10 boolean expressions daily for 30 days.
2. **Read assembly**: Compile simple Rust/Go functions and study the output.
3. **Teach**: Explain one concept to someone else this week.
4. **Build**: Write a boolean expression parser/evaluator in Rust.

You're not just learning boolean logic—you're **rewiring your brain** to think in terms of logical rigor, optimization, and machine-level understanding.

This is the path to the top 1%. 

Ready to continue?