Excellent question — and this goes right to the heart of **how Go (and similar compiled languages)** handle *compile-time constant expressions*.

Let’s analyze what’s really going on when you ask if `[call_sum() + call_add()]int` is valid.

---

### 1. What the grammar *allows*

You’re correct that, grammatically, this line:

```
ArrayLength = Expression .
```

says that **any valid `Expression`** can appear as the array length.
So, syntactically, `[call_sum() + call_add()]int` *fits* the grammar: it’s a `[` token, followed by an `Expression` (`call_sum() + call_add()`), then `]` and an `ElementType` (`int`).

In other words — **the parser** won’t immediately reject this.

---

### 2. But then the **semantic analyzer** steps in

Once parsing succeeds, the compiler moves to **semantic analysis**, where it checks *meaning and constraints* that syntax alone can’t enforce.

The Go spec says this clearly:

> *“The length of an array type must be a constant expression that can be evaluated at compile time.”*

So even though the grammar allows any `Expression`, the **semantic rules restrict it** to constant values.

---

### 3. What counts as a *constant expression*?

In Go (and many systems languages like C, Rust, etc.), a **constant expression** means:

* It can be evaluated at compile time.
* It doesn’t depend on any runtime state.
* It doesn’t involve function calls, heap memory, I/O, or mutable variables.

For instance:

```go
[5]int         // ✅ valid: 5 is a constant
[len([1]int)]int  // ❌ invalid: len() here is runtime, not constant
[2 + 3]int     // ✅ valid: constant arithmetic
[call_sum()]int  // ❌ invalid: function call
```

---

### 4. Why this restriction exists

The compiler must know **array size** at compile time so it can:

* allocate static memory correctly,
* determine stack frame layout, and
* generate type information.

If array length were runtime-computed, the array would need **heap allocation or dynamic dispatch** — which is a *slice*, not an array, in Go.

So `[call_sum() + call_add()]int` fails **semantically**, not **syntactically**.

---

### 5. The runtime equivalent

If you want runtime sizing, you use **slices**, not arrays:

```go
n := call_sum() + call_add()
arr := make([]int, n)
```

This creates a dynamic-length slice backed by heap memory.

---

### Summary

| Stage                 | What happens                    | Verdict    |
| --------------------- | ------------------------------- | ---------- |
| **Parsing**           | Grammar accepts `Expression`    | ✅ allowed  |
| **Semantic Analysis** | Must be a compile-time constant | ❌ rejected |
| **Fix**               | Use slice (`make([]int, n)`)    | ✅ works    |

---

You’ve basically spotted the subtle but crucial difference between **syntactic validity** and **semantic validity** — the same distinction that makes compiler front-ends and back-ends such different beasts.

Would you like me to show how the Go compiler’s front-end (`go/parser` + `go/types`) would process and reject that code internally? It’s a fascinating look under the hood.
