package main

import "fmt"

func main() {

    if 7%2 == 0 {
        fmt.Println("7 is even")
    } else {
        fmt.Println("7 is odd")
    }

    if 8%4 == 0 {
        fmt.Println("8 is divisible by 4")
    }

    if 8%2 == 0 || 7%2 == 0 {
        fmt.Println("either 8 or 7 are even")
    }

    if num := 9; num < 0 {
        fmt.Println(num, "is negative")
    } else if num < 10 {
        fmt.Println(num, "has 1 digit")
    } else {
        fmt.Println(num, "has multiple digits")
    }
}

Excellent question — this is one of Go’s elegant syntax tricks that often confuses newcomers at first. Let’s break it down clearly 👇

---

### 🔹 The syntax: `if <init-statement>; <condition> { ... }`

In Go, an `if` statement can have an **optional short statement** before the condition — separated by a semicolon (`;`).

The general pattern looks like this:

```go
if initialization; condition {
    // body
}
```

So your code:

```go
if num := 9; num < 0 {
    fmt.Println(num, "is negative")
} else if num < 10 {
    fmt.Println(num, "has 1 digit")
} else {
    fmt.Println(num, "has multiple digits")
}
```

means:

1. `num := 9` → this **creates and initializes a new variable** `num` with value `9`.
2. Then `num < 0` → this **evaluates the condition** using that `num`.
3. The semicolon (`;`) just **separates** the short statement from the condition.
4. The scope of `num` exists **only within** the entire `if–else if–else` block.

---

### 🔸 What’s really happening

Think of it like:

```go
{
    num := 9
    if num < 0 {
        fmt.Println(num, "is negative")
    } else if num < 10 {
        fmt.Println(num, "has 1 digit")
    } else {
        fmt.Println(num, "has multiple digits")
    }
}
```

The only difference is that Go lets you do it inline using `if num := 9; num < 0`.

---

### ✅ Why it’s useful

* It **keeps variables local** to the `if` block (clean scope, no pollution).
* Great for things like parsing or checking errors.

For example:

```go
if err := doSomething(); err != nil {
    fmt.Println("Error:", err)
}
```

Here, `err` exists **only inside the if block**, not outside — a common Go idiom.

---

### 🧠 Summary

| Part       | Meaning                                               |
| ---------- | ----------------------------------------------------- |
| `num := 9` | Short variable declaration                            |
| `;`        | Separates declaration from condition                  |
| `num < 0`  | Condition to check                                    |
| Scope      | Limited to the entire `if` / `else if` / `else` chain |

---

Would you like me to show you what happens if you try to use `num` **outside** that `if` block?
