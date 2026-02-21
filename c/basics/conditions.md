Here is a **clear, practical guide** to using **multiple conditions in C** — especially inside `if`, `while`, and `for` statements.

---

# ✅ Multiple Conditions in C — Complete Guide

In C, **multiple conditions are combined using logical operators**, *not commas*.

---

## 1️⃣ Logical Operators (Core Tools)

These are the **only correct way** to combine conditions.

| Operator | Meaning | Example           |    |                   |
| -------- | ------- | ----------------- | -- | ----------------- |
| `&&`     | AND     | both must be true |    |                   |
| `        |         | `                 | OR | at least one true |
| `!`      | NOT     | reverse result    |    |                   |

---

## ✅ AND (`&&`) — All Conditions Must Be True

### Syntax

```c
if (condition1 && condition2)
```

### Example

```c
int age = 25;
int salary = 50000;

if (age > 18 && salary > 30000) {
    printf("Eligible\n");
}
```

✔ Runs only if **both** are true.

---

## ✅ OR (`||`) — Any Condition True

```c
if (condition1 || condition2)
```

### Example

```c
if (day == 6 || day == 7) {
    printf("Weekend\n");
}
```

✔ Runs if **either** matches.

---

## ✅ NOT (`!`) — Negation

```c
if (!logged_in)
```

Example:

```c
if (!(x > 10)) {
    printf("x <= 10\n");
}
```

---

# 2️⃣ Multiple Conditions in `for` Loop

### ✅ Correct Way

```c
for (int i = 0, j = 10; i < 5 && j > 0; i++, j--)
```

Meaning:

* continue while **both conditions hold**

---

### ❌ Wrong Way (Common Mistake)

```c
for (... ; i < 5, j > 0 ; ...)
```

This uses **comma operator**, NOT multiple conditions.

Equivalent to:

```c
j > 0
```

Only last condition matters.

---

# 3️⃣ Multiple Conditions in `while`

```c
while (x > 0 && y < 100)
```

Example:

```c
while (i < n && arr[i] != target) {
    i++;
}
```

Stops when:

* end reached OR
* target found

---

# 4️⃣ Combining Many Conditions

You can chain indefinitely.

```c
if (a > 0 && b > 0 && c > 0)
```

or mixed:

```c
if ((age > 18 && citizen) || special_permission)
```

---

# 5️⃣ Use Parentheses (Best Practice)

Operator precedence can confuse logic.

✅ Recommended:

```c
if ((a > b && c > d) || e == 1)
```

Avoid:

```c
if (a > b && c > d || e == 1)
```

---

# 6️⃣ Short-Circuit Evaluation (VERY IMPORTANT)

C stops evaluation early.

---

## AND (`&&`)

If first condition is false → rest skipped.

```c
if (ptr != NULL && ptr->value == 10)
```

Safe because:

* NULL checked first
* prevents crash

---

## OR (`||`)

If first condition true → rest skipped.

```c
if (cached || expensive_function())
```

Function may never run.

---

# 7️⃣ Multiple Variable Control Pattern (Two Pointers)

Very common in algorithms.

```c
for (int left = 0, right = n - 1;
     left < right;
     left++, right--)
{
}
```

Used in:

* reversing arrays
* palindrome check
* binary search variants

---

# 8️⃣ Truth Table Mental Model

### AND

| A | B | Result |
| - | - | ------ |
| T | T | T      |
| T | F | F      |
| F | T | F      |
| F | F | F      |

---

### OR

| A | B | Result |
| - | - | ------ |
| T | T | T      |
| T | F | T      |
| F | T | T      |
| F | F | F      |

---

# 9️⃣ Advanced: Mixing Arithmetic + Conditions

Valid:

```c
if ((x + y > 10) && (z % 2 == 0))
```

---

# 🚨 Golden Rules

✅ Use:

```c
&&   ||
!
```

❌ Never rely on:

```c
,
```

for conditions.

---

# ✅ Professional Rule (Used in Systems Programming)

Always order conditions:

```c
if (pointer != NULL && pointer->field == value)
```

**Safety check first** → prevents undefined behavior.

---

If you want next, I can show:

✅ Compiler-level evaluation order
✅ Common bugs in multi-condition logic
✅ Linux kernel–style condition writing
✅ Interview-grade condition patterns

Just tell me.
