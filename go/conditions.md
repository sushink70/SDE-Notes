# 🧠 The Complete Mastery Guide to Conditions in Programming

> *"A condition is not just a line of code — it is a decision point, a fork in the river of execution. Master conditions, and you master the logic of all programs."*

---

## 📚 TABLE OF CONTENTS

```
1.  What Is a Condition? (The Philosophical Foundation)
2.  Boolean Logic — The Mathematics Behind Conditions
3.  Comparison Operators
4.  Logical Operators (AND, OR, NOT, XOR)
5.  Short-Circuit Evaluation
6.  if / else if / else — The Classical Decision Tree
7.  Nested Conditions
8.  Guard Clauses & Early Returns
9.  switch (C/Go) vs match (Rust)
10. Pattern Matching (Rust's Superpower)
11. Ternary / Inline Conditions
12. Bitwise Conditions
13. Truthy & Falsy — C vs Rust vs Go
14. Compound Conditions & Operator Precedence
15. Real-World Scenarios & Use Cases
16. Anti-Patterns & Common Mistakes
17. Mental Models & Cognitive Principles
```

---

## 1. 🌍 WHAT IS A CONDITION?

### The Real-World Mental Model

Before writing a single line of code, understand this:

> A **condition** is a **question** your program asks at runtime, and based on the answer (**true** or **false**), it decides **which path to follow**.

Think of it like a railway track switch:

```
                          [ QUESTION: Is it raining? ]
                                      |
               ┌─────────────────────┴─────────────────────┐
               │ YES (true)                                  │ NO (false)
               ▼                                             ▼
        [ Take umbrella ]                           [ Wear sunglasses ]
```

In every program you will ever write — games, operating systems, compilers, databases — **conditions are the intelligence**. They separate one program from another. A program without conditions is just a straight line; it does the same thing every time. Conditions give your program **awareness** of its environment.

---

## 2. 🔢 BOOLEAN LOGIC — THE MATHEMATICS BEHIND CONDITIONS

### What is a Boolean?

A **Boolean** (named after mathematician **George Boole**) is a value that is **either true or false**. Nothing in between. It is the binary atom of all decision-making.

```
Boolean Universe:
┌─────────────────────────────────────┐
│                                     │
│   Everything is either:             │
│                                     │
│   ┌─────────┐     ┌─────────┐      │
│   │  TRUE   │ or  │  FALSE  │      │
│   │    1    │     │    0    │      │
│   └─────────┘     └─────────┘      │
│                                     │
└─────────────────────────────────────┘
```

### The Three Fundamental Boolean Operations

These are the building blocks of all logic:

```
┌──────────────────────────────────────────────────────────────┐
│                   TRUTH TABLES                                │
├────────────────────────────────────────────────────────────  │
│  NOT (Negation) — Flips the value                            │
│  ┌───────┬────────┐                                          │
│  │  A    │  !A    │                                          │
│  ├───────┼────────┤                                          │
│  │ true  │ false  │                                          │
│  │ false │ true   │                                          │
│  └───────┴────────┘                                          │
│                                                               │
│  AND (Conjunction) — BOTH must be true                       │
│  ┌───────┬───────┬─────────┐                                 │
│  │  A    │  B    │  A && B │                                 │
│  ├───────┼───────┼─────────┤                                 │
│  │ true  │ true  │  true   │                                 │
│  │ true  │ false │  false  │                                 │
│  │ false │ true  │  false  │                                 │
│  │ false │ false │  false  │                                 │
│  └───────┴───────┴─────────┘                                 │
│                                                               │
│  OR (Disjunction) — AT LEAST ONE must be true                │
│  ┌───────┬───────┬─────────┐                                 │
│  │  A    │  B    │  A || B │                                 │
│  ├───────┼───────┼─────────┤                                 │
│  │ true  │ true  │  true   │                                 │
│  │ true  │ false │  true   │                                 │
│  │ false │ true  │  true   │                                 │
│  │ false │ false │  false  │                                 │
│  └───────┴───────┴─────────┘                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. ⚖️ COMPARISON OPERATORS

These are the tools that **produce** boolean values by comparing two things.

```
┌──────────────────────────────────────────────────────────────┐
│              COMPARISON OPERATORS                            │
├────────────┬──────────────────────────────────────────────── │
│ Operator   │ Meaning                                         │
├────────────┼─────────────────────────────────────────────────│
│  ==        │ Equal to                                        │
│  !=        │ Not equal to                                    │
│  >         │ Greater than                                    │
│  <         │ Less than                                       │
│  >=        │ Greater than or equal to                        │
│  <=        │ Less than or equal to                           │
└────────────┴─────────────────────────────────────────────────┘
```

### Real-World Scenario: Bank ATM

```
ATM Logic:
   User enters PIN
        │
        ▼
  [ entered_pin == stored_pin? ]
        │
   YES ─┼─ NO
        │         │
        ▼         ▼
   [Grant       [Deny
   Access]      Access]
```

### Code in C, Rust, Go

```c
// ─────────────────── C ───────────────────
#include <stdio.h>

int main() {
    int user_pin = 1234;
    int stored_pin = 1234;
    int balance = 5000;
    int withdraw = 200;

    if (user_pin == stored_pin) {
        printf("Access granted.\n");

        if (withdraw <= balance) {
            printf("Dispensing %d\n", withdraw);
        } else {
            printf("Insufficient funds.\n");
        }
    } else {
        printf("Wrong PIN. Access denied.\n");
    }

    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
fn main() {
    let user_pin: u32 = 1234;
    let stored_pin: u32 = 1234;
    let balance: u32 = 5000;
    let withdraw: u32 = 200;

    // In Rust, if is an EXPRESSION — it returns a value
    if user_pin == stored_pin {
        println!("Access granted.");

        if withdraw <= balance {
            println!("Dispensing {}", withdraw);
        } else {
            println!("Insufficient funds.");
        }
    } else {
        println!("Wrong PIN. Access denied.");
    }
}
```

```go
// ─────────────────── Go ───────────────────
package main

import "fmt"

func main() {
    userPin := 1234
    storedPin := 1234
    balance := 5000
    withdraw := 200

    if userPin == storedPin {
        fmt.Println("Access granted.")

        if withdraw <= balance {
            fmt.Printf("Dispensing %d\n", withdraw)
        } else {
            fmt.Println("Insufficient funds.")
        }
    } else {
        fmt.Println("Wrong PIN. Access denied.")
    }
}
```

---

## 4. 🔗 LOGICAL OPERATORS (AND, OR, NOT, XOR)

### Visual Mental Model

```
AND — The Strict Gate (BOTH keys needed)
╔═══════╗   ╔═══════╗       ╔════════╗
║ Key A ║ + ║ Key B ║  ──►  ║  OPEN  ║  (only if BOTH)
╚═══════╝   ╚═══════╝       ╚════════╝

OR — The Lenient Gate (EITHER key works)
╔═══════╗   ╔═══════╗       ╔════════╗
║ Key A ║ + ║ Key B ║  ──►  ║  OPEN  ║  (if ANY one)
╚═══════╝   ╚═══════╝       ╚════════╝

NOT — The Inverter (flips the lock)
╔════════╗              ╔════════╗
║  OPEN  ║  ──[NOT]──►  ║ CLOSED ║
╚════════╝              ╚════════╝
```

### XOR (Exclusive OR) — Extra Concept

XOR means **one or the other, but NOT both**. Useful in cryptography, toggle logic, etc.

```
XOR Truth Table:
┌───────┬───────┬─────────┐
│  A    │  B    │  A ^ B  │
├───────┼───────┼─────────┤
│ true  │ true  │  false  │  ← both true = false (exclusive)
│ true  │ false │  true   │
│ false │ true  │  true   │
│ false │ false │  false  │
└───────┴───────┴─────────┘
```

### Real-World Scenario: Login System

```
Login Condition Logic:

  [ Has valid email? ]  AND  [ Has valid password? ]
            │                          │
            └──────────┬───────────────┘
                       │
              [ BOTH TRUE? ]
                   │      │
                  YES      NO
                   │      │
               [Login]  [Reject]

  [ Is admin? ]  OR  [ Is super_user? ]
       │                    │
       └────────┬───────────┘
                │
      [ EITHER TRUE? ]
            │      │
           YES      NO
            │      │
      [Show admin  [Hide
        panel]    panel]
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

int main() {
    // Simulated user data
    char email[] = "user@example.com";
    char password[] = "secret123";
    bool is_admin = false;
    bool is_super_user = true;
    int age = 17;
    bool has_parental_consent = true;

    // AND: Both conditions must be true
    bool login_valid = (strlen(email) > 0) && (strlen(password) >= 8);

    // OR: At least one must be true
    bool can_access_admin = is_admin || is_super_user;

    // NOT: Invert
    bool is_blocked = false;
    bool can_proceed = !is_blocked;

    // XOR (simulated in C using !=)
    bool only_one_privilege = is_admin != is_super_user;

    // Compound: minor with consent can access
    bool can_register = (age >= 18) || (age >= 13 && has_parental_consent);

    printf("Login valid: %s\n", login_valid ? "yes" : "no");
    printf("Admin access: %s\n", can_access_admin ? "yes" : "no");
    printf("Can proceed: %s\n", can_proceed ? "yes" : "no");
    printf("Can register: %s\n", can_register ? "yes" : "no");

    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
fn main() {
    let email = "user@example.com";
    let password = "secret123";
    let is_admin = false;
    let is_super_user = true;
    let age: u8 = 17;
    let has_parental_consent = true;

    // AND
    let login_valid = !email.is_empty() && password.len() >= 8;

    // OR
    let can_access_admin = is_admin || is_super_user;

    // NOT
    let is_blocked = false;
    let can_proceed = !is_blocked;

    // XOR (Rust uses ^ for bool XOR)
    let only_one_privilege = is_admin ^ is_super_user;

    // Compound
    let can_register = (age >= 18) || (age >= 13 && has_parental_consent);

    println!("Login valid: {}", login_valid);
    println!("Admin access: {}", can_access_admin);
    println!("Can proceed: {}", can_proceed);
    println!("XOR privilege: {}", only_one_privilege);
    println!("Can register: {}", can_register);
}
```

```go
// ─────────────────── Go ───────────────────
package main

import "fmt"

func main() {
    email := "user@example.com"
    password := "secret123"
    isAdmin := false
    isSuperUser := true
    age := 17
    hasParentalConsent := true

    loginValid := len(email) > 0 && len(password) >= 8
    canAccessAdmin := isAdmin || isSuperUser
    isBlocked := false
    canProceed := !isBlocked
    onlyOnePrivilege := isAdmin != isSuperUser // XOR in Go
    canRegister := (age >= 18) || (age >= 13 && hasParentalConsent)

    fmt.Println("Login valid:", loginValid)
    fmt.Println("Admin access:", canAccessAdmin)
    fmt.Println("Can proceed:", canProceed)
    fmt.Println("XOR privilege:", onlyOnePrivilege)
    fmt.Println("Can register:", canRegister)
}
```

---

## 5. ⚡ SHORT-CIRCUIT EVALUATION

### The Most Important Hidden Behavior of Conditions

This is one of the **most powerful and most misunderstood** concepts in conditions.

**Definition:** When evaluating `A && B`, if `A` is **false**, the computer **does NOT evaluate B at all**. Why check the second condition if the first already decided the result? Same for `A || B` — if `A` is **true**, B is skipped.

```
SHORT-CIRCUIT DECISION TREE:

  A && B:
  ┌─────────────────────────────────────┐
  │ Evaluate A                          │
  │    │                                │
  │  false ──► STOP. Result = false     │
  │    │       (B never evaluated)      │
  │  true                               │
  │    │                                │
  │  Evaluate B                         │
  │    │                                │
  │  false ──► Result = false           │
  │  true  ──► Result = true            │
  └─────────────────────────────────────┘

  A || B:
  ┌─────────────────────────────────────┐
  │ Evaluate A                          │
  │    │                                │
  │  true  ──► STOP. Result = true      │
  │    │       (B never evaluated)      │
  │  false                              │
  │    │                                │
  │  Evaluate B                         │
  │    │                                │
  │  true  ──► Result = true            │
  │  false ──► Result = false           │
  └─────────────────────────────────────┘
```

### Why This Matters — The Null Pointer Problem

This is used **defensively** to avoid crashes. Classic scenario: check if a pointer is valid **before** dereferencing it.

```c
// ─────────────────── C ───────────────────
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char *name = NULL;  // NULL pointer — no memory allocated

    // DANGEROUS — crashes if name is NULL
    // if (strlen(name) > 0) { ... }

    // SAFE — short-circuit saves us
    // If name == NULL, the second part is NEVER evaluated
    if (name != NULL && strlen(name) > 0) {
        printf("Name: %s\n", name);
    } else {
        printf("No name provided.\n");
    }

    // ── Another use: avoiding division by zero ──
    int divisor = 0;
    int value = 100;

    // If divisor == 0, the division is NEVER attempted
    if (divisor != 0 && (value / divisor) > 10) {
        printf("Large quotient.\n");
    } else {
        printf("Safe: division skipped or result small.\n");
    }

    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
// Rust makes null safety explicit via Option<T>
// But short-circuit still applies to booleans

fn get_username(id: u32) -> Option<String> {
    if id == 1 {
        Some("Alice".to_string())
    } else {
        None
    }
}

fn is_long_name(name: &str) -> bool {
    println!("  [checking name length...]"); // shows if this runs
    name.len() > 3
}

fn main() {
    let user = get_username(99); // returns None

    // Short-circuit: if is_some() is false, is_long_name() is NEVER called
    if user.is_some() && is_long_name(user.as_deref().unwrap_or("")) {
        println!("User has a long name.");
    } else {
        println!("No user or short name.");
    }

    // Idiomatic Rust: use if let instead
    if let Some(name) = get_username(1) {
        println!("Found user: {}", name);
    }
}
```

```go
// ─────────────────── Go ───────────────────
package main

import "fmt"

func divide(a, b int) int {
    return a / b
}

func main() {
    b := 0

    // Short-circuit prevents divide-by-zero panic
    if b != 0 && divide(10, b) > 2 {
        fmt.Println("Large result")
    } else {
        fmt.Println("Safe: b was zero, divide never called")
    }

    // Nil check pattern in Go
    var s *string = nil

    // Without short-circuit, *s would panic
    if s != nil && len(*s) > 0 {
        fmt.Println("Non-empty string:", *s)
    } else {
        fmt.Println("String pointer is nil — safely skipped.")
    }
}
```

---

## 6. 🌿 if / else if / else — THE CLASSICAL DECISION TREE

### Full Execution Flow

```
┌─────────────────────────────────────────────────────────┐
│                  if/else if/else FLOW                   │
│                                                         │
│    START                                                │
│      │                                                  │
│      ▼                                                  │
│   [ condition_1 true? ] ──YES──► [Execute Block 1]     │
│      │                                  │               │
│      NO                                 │               │
│      │                                  │               │
│      ▼                                  │               │
│   [ condition_2 true? ] ──YES──► [Execute Block 2]     │
│      │                                  │               │
│      NO                                 │               │
│      │                                  │               │
│      ▼                                  │               │
│   [ condition_3 true? ] ──YES──► [Execute Block 3]     │
│      │                                  │               │
│      NO                                 │               │
│      │                                  │               │
│      ▼                                  │               │
│   [Execute else Block] ◄────────────────┘               │
│      │                                                  │
│      ▼                                                  │
│     END (only ONE block executes)                       │
└─────────────────────────────────────────────────────────┘
```

### Real-World Scenario: Traffic Light System

```
Traffic Light Decision:
         [ color? ]
         /    |    \
      RED  YELLOW  GREEN
       |      |      |
     STOP   SLOW    GO
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>
#include <string.h>

// Grade classification system
void classify_grade(int score) {
    if (score >= 90) {
        printf("Grade: A — Excellent\n");
    } else if (score >= 80) {
        printf("Grade: B — Good\n");
    } else if (score >= 70) {
        printf("Grade: C — Average\n");
    } else if (score >= 60) {
        printf("Grade: D — Below Average\n");
    } else {
        printf("Grade: F — Failed\n");
    }
}

// Traffic light
void traffic_light(const char *color) {
    if (strcmp(color, "red") == 0) {
        printf("STOP\n");
    } else if (strcmp(color, "yellow") == 0) {
        printf("SLOW DOWN\n");
    } else if (strcmp(color, "green") == 0) {
        printf("GO\n");
    } else {
        printf("Unknown signal — halt for safety\n");
    }
}

int main() {
    classify_grade(95);
    classify_grade(72);
    classify_grade(45);

    traffic_light("green");
    traffic_light("red");
    traffic_light("purple"); // unknown

    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
// KEY INSIGHT: In Rust, if is an EXPRESSION
// This means it RETURNS a value — very powerful

fn classify_grade(score: u32) -> &'static str {
    if score >= 90 {
        "A — Excellent"
    } else if score >= 80 {
        "B — Good"
    } else if score >= 70 {
        "C — Average"
    } else if score >= 60 {
        "D — Below Average"
    } else {
        "F — Failed"
    }
}

fn main() {
    // if as an expression — assigns result to variable
    let score = 85;
    let grade = if score >= 90 { "A" } else if score >= 80 { "B" } else { "C" };
    println!("Score {} → Grade {}", score, grade);

    // Function-based
    println!("{}", classify_grade(95));
    println!("{}", classify_grade(55));

    // Go-style: Go has init statement in if
    // Rust equivalent: use let bindings
    let raw_input = "  hello  ";
    let trimmed = raw_input.trim();
    if trimmed.is_empty() {
        println!("Empty input");
    } else {
        println!("Input: {}", trimmed);
    }
}
```

```go
// ─────────────────── Go ───────────────────
package main

import (
    "fmt"
    "strings"
)

func classifyGrade(score int) string {
    if score >= 90 {
        return "A — Excellent"
    } else if score >= 80 {
        return "B — Good"
    } else if score >= 70 {
        return "C — Average"
    } else if score >= 60 {
        return "D — Below Average"
    } else {
        return "F — Failed"
    }
}

// Go's SPECIAL FEATURE: if with init statement
// The variable declared here is scoped to the if block
func processInput(raw string) {
    // 'trimmed' exists only inside this if/else block
    if trimmed := strings.TrimSpace(raw); trimmed == "" {
        fmt.Println("Empty input after trimming")
    } else {
        fmt.Printf("Processed: '%s'\n", trimmed)
    }
    // trimmed is NOT accessible here — scoped to the if block
}

func main() {
    fmt.Println(classifyGrade(95))
    fmt.Println(classifyGrade(72))
    fmt.Println(classifyGrade(45))

    processInput("  hello world  ")
    processInput("   ")
}
```

---

## 7. 🪆 NESTED CONDITIONS

### The Concept

Nesting means placing one condition **inside another**. This creates a **multi-level decision tree**.

```
NESTED CONDITION TREE (E-commerce Discount):

     [ Is user logged in? ]
        /           \
      YES             NO
       |               |
       |           [Show login prompt]
       |
  [ Is premium member? ]
       /           \
     YES             NO
      |               |
   [ Order > $100? ]  [ Order > $200? ]
    /       \          /          \
  YES        NO      YES           NO
   |          |       |             |
 [30%       [20%    [10%          [5%
 off]       off]    off]          off]
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>
#include <stdbool.h>

void apply_discount(bool is_logged_in, bool is_premium, double order_total) {
    double discount = 0.0;

    if (is_logged_in) {
        if (is_premium) {
            if (order_total > 100.0) {
                discount = 0.30;
            } else {
                discount = 0.20;
            }
        } else {
            if (order_total > 200.0) {
                discount = 0.10;
            } else {
                discount = 0.05;
            }
        }
    } else {
        printf("Please log in to receive discounts.\n");
        return;
    }

    printf("Order: $%.2f | Discount: %.0f%% | Final: $%.2f\n",
           order_total,
           discount * 100,
           order_total * (1 - discount));
}

int main() {
    apply_discount(true, true, 150.0);   // premium, large order
    apply_discount(true, false, 250.0);  // regular, large order
    apply_discount(true, false, 50.0);   // regular, small order
    apply_discount(false, false, 100.0); // not logged in
    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
fn apply_discount(is_logged_in: bool, is_premium: bool, order_total: f64) {
    if !is_logged_in {
        println!("Please log in to receive discounts.");
        return; // early return — we'll cover this in Guard Clauses section
    }

    // Cleaner nested logic using if expressions
    let discount = if is_premium {
        if order_total > 100.0 { 0.30 } else { 0.20 }
    } else {
        if order_total > 200.0 { 0.10 } else { 0.05 }
    };

    println!(
        "Order: ${:.2} | Discount: {:.0}% | Final: ${:.2}",
        order_total,
        discount * 100.0,
        order_total * (1.0 - discount)
    );
}

fn main() {
    apply_discount(true, true, 150.0);
    apply_discount(true, false, 250.0);
    apply_discount(true, false, 50.0);
    apply_discount(false, false, 100.0);
}
```

```go
// ─────────────────── Go ───────────────────
package main

import "fmt"

func applyDiscount(isLoggedIn, isPremium bool, orderTotal float64) {
    if !isLoggedIn {
        fmt.Println("Please log in to receive discounts.")
        return
    }

    var discount float64
    if isPremium {
        if orderTotal > 100.0 {
            discount = 0.30
        } else {
            discount = 0.20
        }
    } else {
        if orderTotal > 200.0 {
            discount = 0.10
        } else {
            discount = 0.05
        }
    }

    fmt.Printf("Order: $%.2f | Discount: %.0f%% | Final: $%.2f\n",
        orderTotal, discount*100, orderTotal*(1-discount))
}

func main() {
    applyDiscount(true, true, 150.0)
    applyDiscount(true, false, 250.0)
    applyDiscount(true, false, 50.0)
    applyDiscount(false, false, 100.0)
}
```

---

## 8. 🛡️ GUARD CLAUSES & EARLY RETURNS

### The Concept — Inverting Your Nesting

**Guard Clause** = Check for the **error/invalid** case first, then return immediately. This **eliminates deep nesting** and makes code read like plain English.

```
WITHOUT Guard Clauses (Arrow Anti-Pattern):

if (valid_user) {
    if (has_permission) {
        if (not_expired) {
            if (has_balance) {
                // actual logic  ← buried 4 levels deep
            }
        }
    }
}

╔══════╗
║  if  ║
║ ╔══════╗
║ ║  if  ║
║ ║ ╔══════╗
║ ║ ║  if  ║
║ ║ ║ ╔══════╗
║ ║ ║ ║LOGIC ║  ← THE ARROW OF DOOM
║ ║ ║ ╚══════╝
║ ║ ╚══════╝
║ ╚══════╝
╚══════╝

WITH Guard Clauses (Flat & Clean):

if (!valid_user) return error;
if (!has_permission) return error;
if (expired) return error;
if (!has_balance) return error;

// actual logic ← clean, at the top level
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OK = 0,
    ERR_INVALID_USER,
    ERR_NO_PERMISSION,
    ERR_EXPIRED,
    ERR_INSUFFICIENT_FUNDS
} Status;

// WITHOUT guard clauses — deeply nested (BAD)
Status process_payment_bad(bool valid_user, bool has_perm,
                           bool not_expired, double balance, double amount) {
    if (valid_user) {
        if (has_perm) {
            if (not_expired) {
                if (balance >= amount) {
                    printf("[BAD] Payment of $%.2f processed.\n", amount);
                    return OK;
                } else {
                    return ERR_INSUFFICIENT_FUNDS;
                }
            } else {
                return ERR_EXPIRED;
            }
        } else {
            return ERR_NO_PERMISSION;
        }
    } else {
        return ERR_INVALID_USER;
    }
}

// WITH guard clauses — flat and clean (GOOD)
Status process_payment_good(bool valid_user, bool has_perm,
                            bool not_expired, double balance, double amount) {
    // Guards: reject early
    if (!valid_user)       return ERR_INVALID_USER;
    if (!has_perm)         return ERR_NO_PERMISSION;
    if (!not_expired)      return ERR_EXPIRED;
    if (balance < amount)  return ERR_INSUFFICIENT_FUNDS;

    // Happy path — the real logic is clear and unindented
    printf("[GOOD] Payment of $%.2f processed.\n", amount);
    return OK;
}

int main() {
    process_payment_bad(true, true, true, 500.0, 100.0);
    process_payment_good(true, true, true, 500.0, 100.0);
    process_payment_good(false, true, true, 500.0, 100.0); // invalid user
    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
#[derive(Debug)]
enum PaymentError {
    InvalidUser,
    NoPermission,
    TokenExpired,
    InsufficientFunds,
}

fn process_payment(
    valid_user: bool,
    has_perm: bool,
    not_expired: bool,
    balance: f64,
    amount: f64,
) -> Result<f64, PaymentError> {
    // Guard clauses using Rust's Result/? pattern
    if !valid_user   { return Err(PaymentError::InvalidUser); }
    if !has_perm     { return Err(PaymentError::NoPermission); }
    if !not_expired  { return Err(PaymentError::TokenExpired); }
    if balance < amount { return Err(PaymentError::InsufficientFunds); }

    // Happy path
    let new_balance = balance - amount;
    println!("Payment of ${:.2} processed. New balance: ${:.2}", amount, new_balance);
    Ok(new_balance)
}

fn main() {
    match process_payment(true, true, true, 500.0, 100.0) {
        Ok(bal) => println!("Success! Balance: ${:.2}", bal),
        Err(e)  => println!("Error: {:?}", e),
    }

    match process_payment(true, false, true, 500.0, 100.0) {
        Ok(_)  => println!("Success!"),
        Err(e) => println!("Error: {:?}", e),
    }
}
```

```go
// ─────────────────── Go ───────────────────
package main

import (
    "errors"
    "fmt"
)

var (
    ErrInvalidUser   = errors.New("invalid user")
    ErrNoPermission  = errors.New("no permission")
    ErrExpired       = errors.New("token expired")
    ErrInsufficientFunds = errors.New("insufficient funds")
)

func processPayment(validUser, hasPerm, notExpired bool, balance, amount float64) (float64, error) {
    // Guard clauses — Go idiom: check errors early
    if !validUser   { return 0, ErrInvalidUser }
    if !hasPerm     { return 0, ErrNoPermission }
    if !notExpired  { return 0, ErrExpired }
    if balance < amount { return 0, ErrInsufficientFunds }

    newBalance := balance - amount
    fmt.Printf("Payment of $%.2f processed. New balance: $%.2f\n", amount, newBalance)
    return newBalance, nil
}

func main() {
    if bal, err := processPayment(true, true, true, 500.0, 100.0); err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Printf("Success! Balance: $%.2f\n", bal)
    }

    if _, err := processPayment(true, false, true, 500.0, 100.0); err != nil {
        fmt.Println("Error:", err) // Error: no permission
    }
}
```

---

## 9. 🔀 switch (C/Go) vs match (Rust)

### What is a switch/match?

When you have **many specific values** to check, writing `else if` repeatedly is ugly. `switch`/`match` is the **elegant alternative** — it says: "Compare this value against a list of known patterns."

```
switch FLOW (C/Go):

     [ value ]
         │
    ┌────┴────┐
    │  match  │
    └────┬────┘
         │
    ┌────▼────┐
    │ case 1? │──YES──► [Block 1] ──► [break/end]
    └────┬────┘
         │ NO
    ┌────▼────┐
    │ case 2? │──YES──► [Block 2] ──► [break/end]
    └────┬────┘
         │ NO
    ┌────▼────┐
    │ case 3? │──YES──► [Block 3] ──► [break/end]
    └────┬────┘
         │ NO
    ┌────▼────┐
    │ default │──────► [Default Block]
    └─────────┘
```

### Critical Concept: Fallthrough

In C, if you **forget `break`**, execution **falls through** to the next case. This is a famous source of bugs — and also occasionally used intentionally.

```
FALLTHROUGH DANGER (C):

  value = 2
      │
  case 1? NO
  case 2? YES ──► execute case 2
                       │
                  [no break!]
                       │
              ──► execute case 3 too!  ← BUG
                       │
                  [no break!]
                       │
              ──► execute case 4 too!  ← BUG
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>

// Real-world: HTTP Status Codes
void describe_http_status(int code) {
    switch (code) {
        case 200:
            printf("200 OK — Request succeeded\n");
            break;
        case 201:
            printf("201 Created — Resource created\n");
            break;
        case 301:
            printf("301 Moved Permanently\n");
            break;
        case 400:
            printf("400 Bad Request — Client error\n");
            break;
        case 401:
            printf("401 Unauthorized\n");
            break;
        case 403:
            printf("403 Forbidden\n");
            break;
        case 404:
            printf("404 Not Found\n");
            break;
        case 500:
            printf("500 Internal Server Error\n");
            break;
        default:
            printf("Unknown status code: %d\n", code);
            break;
    }
}

// Intentional fallthrough: group cases together
void classify_day(int day) {
    switch (day) {
        case 1: // Monday
        case 2: // Tuesday
        case 3: // Wednesday
        case 4: // Thursday
        case 5: // Friday
            printf("Day %d: Weekday\n", day);
            break;
        case 6: // Saturday
        case 7: // Sunday
            printf("Day %d: Weekend\n", day);
            break;
        default:
            printf("Invalid day\n");
    }
}

int main() {
    describe_http_status(200);
    describe_http_status(404);
    describe_http_status(500);
    describe_http_status(999);

    classify_day(3);
    classify_day(6);
    return 0;
}
```

```go
// ─────────────────── Go ───────────────────
// KEY DIFFERENCE: Go switch does NOT fallthrough by default
// Each case automatically breaks — opposite of C
// You must explicitly use 'fallthrough' keyword to fall through

package main

import "fmt"

func describeHTTPStatus(code int) {
    switch code {
    case 200:
        fmt.Println("200 OK")
    case 201:
        fmt.Println("201 Created")
    case 400:
        fmt.Println("400 Bad Request")
    case 401, 403: // Multiple values in one case (no fallthrough needed)
        fmt.Println("Authentication/Authorization error")
    case 404:
        fmt.Println("404 Not Found")
    case 500:
        fmt.Println("500 Internal Server Error")
    default:
        fmt.Printf("Unknown: %d\n", code)
    }
}

// Go: switch with no expression = switch true (like if/else chain)
func classifyTemperature(temp float64) string {
    switch {
    case temp < 0:
        return "Freezing"
    case temp < 10:
        return "Very Cold"
    case temp < 20:
        return "Cold"
    case temp < 30:
        return "Comfortable"
    default:
        return "Hot"
    }
}

// Go: switch with init statement
func processCommand(rawInput string) {
    switch cmd := rawInput; cmd {
    case "start":
        fmt.Println("Starting system...")
    case "stop", "quit", "exit":
        fmt.Println("Shutting down...")
    case "status":
        fmt.Println("System running.")
    default:
        fmt.Printf("Unknown command: %s\n", cmd)
    }
}

func main() {
    describeHTTPStatus(200)
    describeHTTPStatus(401)
    describeHTTPStatus(404)

    fmt.Println(classifyTemperature(-5))
    fmt.Println(classifyTemperature(25))

    processCommand("stop")
    processCommand("status")
}
```

```rust
// ─────────────────── Rust ───────────────────
// Rust's match is FAR more powerful than switch
// It is exhaustive (compiler forces you to cover all cases)
// It is also an expression (returns a value)
// No fallthrough at all — each arm is independent

fn describe_http_status(code: u16) -> &'static str {
    match code {
        200 => "OK",
        201 => "Created",
        301 => "Moved Permanently",
        400 => "Bad Request",
        401 | 403 => "Auth error",  // Multiple values with |
        404 => "Not Found",
        500..=599 => "Server Error", // Range pattern — covers 500,501,...,599
        _ => "Unknown",              // Wildcard (like default)
    }
}

// match as an expression
fn classify_temperature(temp: f64) -> &'static str {
    match temp as i32 {
        i32::MIN..=-1 => "Freezing",
        0..=9         => "Very Cold",
        10..=19       => "Cold",
        20..=29       => "Comfortable",
        _             => "Hot",
    }
}

#[derive(Debug)]
enum Command {
    Start,
    Stop,
    Status,
    Unknown(String),
}

// match on an enum — exhaustive
fn process_command(cmd: Command) {
    match cmd {
        Command::Start            => println!("Starting..."),
        Command::Stop             => println!("Stopping..."),
        Command::Status           => println!("Running."),
        Command::Unknown(text)    => println!("Unknown command: {}", text),
        // Compiler ERROR if you forget any variant — safety net!
    }
}

fn main() {
    println!("{}", describe_http_status(200));
    println!("{}", describe_http_status(503));
    println!("{}", describe_http_status(404));

    println!("{}", classify_temperature(-5.0));
    println!("{}", classify_temperature(25.0));

    process_command(Command::Start);
    process_command(Command::Unknown("fly".to_string()));
}
```

---

## 10. 🦾 PATTERN MATCHING (Rust's Superpower)

### What is Pattern Matching?

Pattern matching is a **generalization of switch** that can match not just values, but **shapes**, **types**, **ranges**, **structures**, and **nested data**. Rust's `match` is the most powerful pattern-matching tool in systems programming.

```
PATTERN MATCHING CAPABILITIES:

  match value {
      Literal    ── 42, "hello", true
      Range      ── 1..=10
      Multiple   ── 1 | 2 | 3
      Binding    ── x @ 1..=10  (name the value AND test it)
      Destructure── Point { x, y }
      Tuple      ── (a, b, c)
      Enum       ── Some(v), None, Ok(v), Err(e)
      Guard      ── x if x > 5  (conditional pattern)
      Wildcard   ── _  (ignore)
  }
```

```rust
// ─────────────────── Rust ───────────────────

// ── 1. Matching tuples: coordinate system ──
fn describe_point(point: (i32, i32)) -> &'static str {
    match point {
        (0, 0)        => "Origin",
        (x, 0) if x > 0 => "Positive X axis",
        (x, 0) if x < 0 => "Negative X axis",
        (0, y) if y > 0 => "Positive Y axis",
        (0, y) if y < 0 => "Negative Y axis",
        (x, y) if x > 0 && y > 0 => "Quadrant I",
        (x, y) if x < 0 && y > 0 => "Quadrant II",
        (x, y) if x < 0 && y < 0 => "Quadrant III",
        _ => "Quadrant IV",
    }
}

// ── 2. Matching enums with data (Option<T>) ──
fn safe_divide(a: f64, b: f64) -> Option<f64> {
    if b == 0.0 { None } else { Some(a / b) }
}

// ── 3. Matching Result<T, E> ──
fn parse_age(s: &str) -> Result<u8, String> {
    match s.trim().parse::<u8>() {
        Ok(n) if n >= 1 && n <= 150 => Ok(n),
        Ok(n) => Err(format!("Age {} is unrealistic", n)),
        Err(e) => Err(format!("Parse error: {}", e)),
    }
}

// ── 4. Struct destructuring ──
#[derive(Debug)]
struct Rgb {
    r: u8,
    g: u8,
    b: u8,
}

fn classify_color(color: &Rgb) -> &'static str {
    match color {
        Rgb { r: 255, g: 0,   b: 0   } => "Pure Red",
        Rgb { r: 0,   g: 255, b: 0   } => "Pure Green",
        Rgb { r: 0,   g: 0,   b: 255 } => "Pure Blue",
        Rgb { r: 255, g: 255, b: 255 } => "White",
        Rgb { r: 0,   g: 0,   b: 0   } => "Black",
        Rgb { r, g, b } if r == g && g == b => "Grayscale",
        _ => "Mixed Color",
    }
}

fn main() {
    println!("{}", describe_point((0, 0)));
    println!("{}", describe_point((3, 4)));
    println!("{}", describe_point((-1, 0)));

    match safe_divide(10.0, 3.0) {
        Some(result) => println!("Result: {:.4}", result),
        None         => println!("Cannot divide by zero"),
    }

    match safe_divide(5.0, 0.0) {
        Some(result) => println!("Result: {:.4}", result),
        None         => println!("Cannot divide by zero"),
    }

    match parse_age("25") {
        Ok(age)  => println!("Valid age: {}", age),
        Err(msg) => println!("Error: {}", msg),
    }

    match parse_age("999") {
        Ok(age)  => println!("Valid age: {}", age),
        Err(msg) => println!("Error: {}", msg),
    }

    let red = Rgb { r: 255, g: 0, b: 0 };
    let gray = Rgb { r: 128, g: 128, b: 128 };
    println!("{:?} is: {}", red, classify_color(&red));
    println!("{:?} is: {}", gray, classify_color(&gray));
}
```

---

## 11. 🎯 TERNARY / INLINE CONDITIONS

### The Concept

A **ternary operator** (or inline condition) is a compact way to write a simple if/else that **produces a value**.

```
Syntax:
condition ? value_if_true : value_if_false

   [ condition ]
       /    \
    true    false
      |       |
   [value1] [value2]
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>

int main() {
    int age = 20;
    int score = 85;
    double temperature = -5.0;

    // Basic ternary
    const char *status = (age >= 18) ? "adult" : "minor";
    printf("Status: %s\n", status);

    // Nested ternary (use sparingly — hard to read)
    const char *grade = (score >= 90) ? "A" :
                        (score >= 80) ? "B" :
                        (score >= 70) ? "C" : "F";
    printf("Grade: %s\n", grade);

    // In function call
    printf("Weather: %s\n", (temperature < 0) ? "freezing" : "above zero");

    // In assignment
    int max_val = (10 > 5) ? 10 : 5;
    printf("Max: %d\n", max_val);

    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
// Rust has NO ternary operator
// Instead, if is an EXPRESSION — even more powerful

fn main() {
    let age = 20;
    let score = 85;

    // Rust's "ternary" — if expression
    let status = if age >= 18 { "adult" } else { "minor" };
    println!("Status: {}", status);

    // Chained if expression
    let grade = if score >= 90 { "A" }
                else if score >= 80 { "B" }
                else if score >= 70 { "C" }
                else { "F" };
    println!("Grade: {}", grade);

    // In a function call argument
    println!("Label: {}", if score > 50 { "pass" } else { "fail" });

    // In a let binding with block
    let message = {
        let base = "Score is ";
        let result = if score >= 60 { "passing" } else { "failing" };
        format!("{}{}", base, result) // last expression is the block's value
    };
    println!("{}", message);
}
```

```go
// ─────────────────── Go ───────────────────
// Go also has NO ternary operator (intentional design decision)
// You must use if/else — Go values explicitness over brevity

package main

import "fmt"

// Helper: Go programmers often write tiny helper functions
func ternaryStr(cond bool, a, b string) string {
    if cond { return a }
    return b
}

func main() {
    age := 20
    score := 85

    // Go way — explicit if/else
    var status string
    if age >= 18 {
        status = "adult"
    } else {
        status = "minor"
    }
    fmt.Println("Status:", status)

    // Using helper function (idiomatic Go workaround)
    grade := ternaryStr(score >= 90, "A", ternaryStr(score >= 80, "B", "C"))
    fmt.Println("Grade:", grade)
}
```

---

## 12. 🔢 BITWISE CONDITIONS

### The Concept — Conditions at the Bit Level

**Bitwise operators** operate on individual **bits** (0s and 1s) of integers. They enable ultra-fast conditions especially useful in:
- **Permission systems** (Unix file permissions)
- **Hardware flags**
- **Game state** (multiple flags in one integer)
- **Networking** (subnet masks, protocol flags)

```
Bitwise Operators:
┌──────────┬────────────────────────────────────────────┐
│ Operator │ Meaning                                    │
├──────────┼────────────────────────────────────────────┤
│  &       │ AND (both bits must be 1)                  │
│  |       │ OR  (at least one bit must be 1)           │
│  ^       │ XOR (bits must differ)                     │
│  ~       │ NOT (flip all bits)                        │
│  <<      │ Left shift (multiply by 2)                 │
│  >>      │ Right shift (divide by 2)                  │
└──────────┴────────────────────────────────────────────┘

Example: Checking if a flag is set
  permissions = 0b00000111  (binary: rwx = read+write+execute)
  READ_FLAG   = 0b00000100  (bit 2 = read)

  permissions & READ_FLAG:
    00000111
  & 00000100
  ----------
    00000100  ← non-zero means READ is set!
```

### Real-World Scenario: Unix File Permissions

```
Unix Permission Bits:
  Bit 2 (4) = READ
  Bit 1 (2) = WRITE
  Bit 0 (1) = EXECUTE

  rwx = 4+2+1 = 7
  rw- = 4+2+0 = 6
  r-x = 4+0+1 = 5
  r-- = 4+0+0 = 4
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>

// Define flags as bit positions
#define PERM_EXECUTE  (1 << 0)   // bit 0 = 001 = 1
#define PERM_WRITE    (1 << 1)   // bit 1 = 010 = 2
#define PERM_READ     (1 << 2)   // bit 2 = 100 = 4

// Game state flags
#define FLAG_RUNNING   (1 << 0)
#define FLAG_PAUSED    (1 << 1)
#define FLAG_MUTED     (1 << 2)
#define FLAG_FULLSCREEN (1 << 3)

void check_permissions(uint8_t perms) {
    printf("Permissions: %d\n", perms);
    printf("  Can Read:    %s\n", (perms & PERM_READ)    ? "yes" : "no");
    printf("  Can Write:   %s\n", (perms & PERM_WRITE)   ? "yes" : "no");
    printf("  Can Execute: %s\n", (perms & PERM_EXECUTE) ? "yes" : "no");
}

void game_status(uint8_t flags) {
    printf("\nGame State Flags: 0b%d%d%d%d\n",
           (flags >> 3) & 1, (flags >> 2) & 1,
           (flags >> 1) & 1, (flags >> 0) & 1);
    printf("  Running:    %s\n", (flags & FLAG_RUNNING)    ? "yes" : "no");
    printf("  Paused:     %s\n", (flags & FLAG_PAUSED)     ? "yes" : "no");
    printf("  Muted:      %s\n", (flags & FLAG_MUTED)      ? "yes" : "no");
    printf("  Fullscreen: %s\n", (flags & FLAG_FULLSCREEN) ? "yes" : "no");
}

int main() {
    // Unix: rwx = 7
    check_permissions(7);   // read + write + execute
    check_permissions(6);   // read + write only
    check_permissions(4);   // read only

    // Set multiple game flags using OR
    uint8_t state = FLAG_RUNNING | FLAG_FULLSCREEN; // = 1001 in binary
    game_status(state);

    // Toggle mute using XOR
    state ^= FLAG_MUTED;
    printf("\nAfter toggling mute:\n");
    game_status(state);

    // Clear (turn off) a flag using AND NOT
    state &= ~FLAG_FULLSCREEN;
    printf("\nAfter exiting fullscreen:\n");
    game_status(state);

    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
// Rust: use bitflags crate in practice, but let's do it manually

const PERM_EXECUTE: u8  = 1 << 0;
const PERM_WRITE: u8    = 1 << 1;
const PERM_READ: u8     = 1 << 2;

const FLAG_RUNNING: u8    = 1 << 0;
const FLAG_PAUSED: u8     = 1 << 1;
const FLAG_MUTED: u8      = 1 << 2;
const FLAG_FULLSCREEN: u8 = 1 << 3;

fn check_permissions(perms: u8) {
    println!("Permissions: {}", perms);
    println!("  Can Read:    {}", if perms & PERM_READ    != 0 { "yes" } else { "no" });
    println!("  Can Write:   {}", if perms & PERM_WRITE   != 0 { "yes" } else { "no" });
    println!("  Can Execute: {}", if perms & PERM_EXECUTE != 0 { "yes" } else { "no" });
}

fn main() {
    check_permissions(7); // rwx
    check_permissions(6); // rw-
    check_permissions(4); // r--

    // Combine flags
    let mut state: u8 = FLAG_RUNNING | FLAG_FULLSCREEN;

    println!("\nInitial state: {:04b}", state);
    println!("Running:    {}", state & FLAG_RUNNING    != 0);
    println!("Fullscreen: {}", state & FLAG_FULLSCREEN != 0);

    // Toggle mute with XOR
    state ^= FLAG_MUTED;
    println!("\nAfter mute toggle: {:04b}", state);
    println!("Muted: {}", state & FLAG_MUTED != 0);

    // Clear fullscreen with AND NOT
    state &= !FLAG_FULLSCREEN;
    println!("\nAfter clearing fullscreen: {:04b}", state);
    println!("Fullscreen: {}", state & FLAG_FULLSCREEN != 0);
}
```

---

## 13. 🌀 TRUTHY & FALSY — C vs Rust vs Go

### What Does "Truthy" Mean?

**Truthy/Falsy** = Some languages allow non-boolean values to be used directly as conditions. Understanding each language's rules is essential.

```
┌──────────────────────────────────────────────────────────────┐
│              TRUTHY / FALSY COMPARISON                       │
├────────────────────────────────────────────────────────────  │
│                                                              │
│  C — Very permissive                                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Falsy:  0 (int), 0.0 (float), NULL (pointer)        │    │
│  │ Truthy: ANY non-zero value                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Go — Strict                                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Conditions MUST be bool — no integer tricks         │    │
│  │ if 1 { }  ← COMPILE ERROR                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Rust — Strict                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Conditions MUST be bool — no integer tricks         │    │
│  │ if 1 { }  ← COMPILE ERROR                          │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>
#include <stdlib.h>

int main() {
    int x = 0;
    int y = 42;
    int *ptr = NULL;
    int val = 10;
    int *ptr2 = &val;

    // In C, 0 is false, everything else is true
    if (x)    printf("x is truthy\n");   // NOT printed
    else      printf("x is falsy (0)\n");// printed

    if (y)    printf("y is truthy (%d)\n", y);  // printed
    if (!y)   printf("This won't print\n");

    // Pointer truthiness: NULL = false, non-NULL = true
    if (ptr)  printf("ptr points somewhere\n");
    else      printf("ptr is NULL (falsy)\n");   // printed

    if (ptr2) printf("ptr2 is valid, value = %d\n", *ptr2); // printed

    // Common C idiom: function returns 0 on success, non-zero on failure
    // int result = some_function();
    // if (!result) { /* success */ }
    // if (result)  { /* failure */ }

    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
fn main() {
    let x: i32 = 0;
    // if x { ... }  ← COMPILE ERROR: expected bool, found i32

    // Must be explicit:
    if x == 0 {
        println!("x is zero");
    }
    if x != 0 {
        println!("x is non-zero");
    }

    // Option<T> truthiness — use is_some()/is_none()
    let maybe: Option<i32> = Some(42);
    let nothing: Option<i32> = None;

    if maybe.is_some() {
        println!("Has a value: {}", maybe.unwrap());
    }
    if nothing.is_none() {
        println!("No value");
    }
}
```

```go
// ─────────────────── Go ───────────────────
package main

import "fmt"

func main() {
    x := 0
    // if x { ... }  ← COMPILE ERROR

    // Must be explicit
    if x == 0 {
        fmt.Println("x is zero")
    }

    // Nil check in Go (for pointers, interfaces, slices, maps, channels)
    var p *int = nil
    if p == nil {
        fmt.Println("p is nil")
    }

    val := 42
    p = &val
    if p != nil {
        fmt.Println("p is not nil, value:", *p)
    }
}
```

---

## 14. 📐 COMPOUND CONDITIONS & OPERATOR PRECEDENCE

### Why Precedence Matters

When you write `a || b && c`, does the `&&` or `||` bind first? Getting this wrong produces **silent bugs** — the code runs but gives wrong answers.

```
Operator Precedence (Highest to Lowest):

  Precedence  │ Operator   │ Example
  ────────────┼────────────┼────────────────────
  1 (highest) │  !         │  !a
  2           │  >, <,     │  a > b
              │  >=, <=    │
  3           │  ==, !=    │  a == b
  4           │  &&        │  a && b
  5 (lowest)  │  ||        │  a || b

So: a || b && c  is interpreted as  a || (b && c)
    NOT as (a || b) && c
```

```
PRECEDENCE TRAP EXAMPLE:

  int x = 5, y = 3, z = 7;
  Result = x > 0 || y == 3 && z < 2

  Step 1: Resolve && first (higher precedence)
          y == 3 && z < 2
        = true  && false
        = false

  Step 2: Resolve ||
          x > 0  || false
        = true   || false
        = TRUE

  If you intended: (x > 0 || y == 3) && z < 2
                 = (true  || true  ) && false
                 = true && false
                 = FALSE   ← DIFFERENT ANSWER!
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>
#include <stdbool.h>

int main() {
    int x = 5, y = 3, z = 7;

    // Without parentheses: && binds first
    bool r1 = x > 0 || y == 3 && z < 2;   // x > 0 || (y==3 && z<2)
    // = true || (true && false) = true || false = TRUE

    // With explicit parentheses: change meaning
    bool r2 = (x > 0 || y == 3) && z < 2; // (true || true) && false
    // = true && false = FALSE

    printf("r1 (no parens): %s\n", r1 ? "true" : "false");  // true
    printf("r2 (parens):    %s\n", r2 ? "true" : "false");  // false

    // Real-world: access control
    bool is_admin = false;
    bool is_owner = true;
    bool is_active = true;
    int clearance_level = 3;

    // Without parens: might not mean what you think
    bool buggy   = is_admin || is_owner && is_active && clearance_level >= 3;
    // is_admin || (is_owner && is_active && clearance_level >= 3)
    // = false  || (true && true && true)
    // = false  || true = TRUE

    // With parens: make intent explicit
    bool correct = (is_admin || is_owner) && is_active && clearance_level >= 3;
    // = (false || true) && true && true
    // = true && true && true = TRUE (same here, but intent is clear)

    printf("buggy:   %s\n",   buggy   ? "access" : "denied");
    printf("correct: %s\n",   correct ? "access" : "denied");

    // TIP: Always use parentheses when mixing && and ||
    // It costs nothing and prevents bugs
    return 0;
}
```

```rust
// ─────────────────── Rust ───────────────────
fn main() {
    let x = 5i32;
    let y = 3i32;
    let z = 7i32;

    // Same precedence rules apply
    let r1 = x > 0 || y == 3 && z < 2;    // x > 0 || (y==3 && z<2)
    let r2 = (x > 0 || y == 3) && z < 2;  // explicit grouping

    println!("r1: {}", r1); // true
    println!("r2: {}", r2); // false

    // Rust tip: clippy will warn about confusing precedence in some cases
    // The compiler is your friend — use explicit parentheses always
}
```

---

## 15. 🏭 REAL-WORLD SCENARIOS & USE CASES

### Scenario 1: Rate Limiter (API Server)

```
Rate Limiter Decision:
         [ Request arrives ]
               │
     [ requests_in_window <= limit? ]
               │
         YES ──┼── NO
         │          │
  [Allow request]  [Is premium user?]
                        │
                  YES ──┼── NO
                  │          │
            [Higher limit]  [Block + 429]
```

```c
// ─────────────────── C ───────────────────
#include <stdio.h>
#include <stdbool.h>
#include <time.h>

#define FREE_LIMIT    100
#define PREMIUM_LIMIT 1000

typedef struct {
    int request_count;
    time_t window_start;
    bool is_premium;
    const char *user_id;
} RateLimiter;

bool should_allow_request(RateLimiter *rl) {
    time_t now = time(NULL);
    int window_seconds = 60; // 1 minute window

    // Reset window if expired
    if (difftime(now, rl->window_start) > window_seconds) {
        rl->request_count = 0;
        rl->window_start = now;
    }

    int limit = rl->is_premium ? PREMIUM_LIMIT : FREE_LIMIT;

    if (rl->request_count >= limit) {
        printf("BLOCKED: %s exceeded %d req/min\n", rl->user_id, limit);
        return false;
    }

    rl->request_count++;
    return true;
}

int main() {
    RateLimiter user1 = {
        .request_count = 99,
        .window_start  = time(NULL),
        .is_premium    = false,
        .user_id       = "alice"
    };

    // 100th request — allowed
    printf("Request: %s\n", should_allow_request(&user1) ? "ALLOWED" : "BLOCKED");
    // 101st request — blocked
    printf("Request: %s\n", should_allow_request(&user1) ? "ALLOWED" : "BLOCKED");

    return 0;
}
```

### Scenario 2: Validation Pipeline (Form Input)

```rust
// ─────────────────── Rust ───────────────────
#[derive(Debug)]
struct RegistrationForm {
    username: String,
    email: String,
    password: String,
    age: u8,
}

#[derive(Debug)]
enum ValidationError {
    UsernameTooShort,
    UsernameHasSpaces,
    InvalidEmail,
    WeakPassword,
    UnderAge,
}

fn validate(form: &RegistrationForm) -> Result<(), Vec<ValidationError>> {
    let mut errors = Vec::new();

    // All conditions evaluated independently — collect all errors
    if form.username.len() < 3 {
        errors.push(ValidationError::UsernameTooShort);
    }
    if form.username.contains(' ') {
        errors.push(ValidationError::UsernameHasSpaces);
    }
    if !form.email.contains('@') || !form.email.contains('.') {
        errors.push(ValidationError::InvalidEmail);
    }
    if form.password.len() < 8 {
        errors.push(ValidationError::WeakPassword);
    }
    if form.age < 13 {
        errors.push(ValidationError::UnderAge);
    }

    if errors.is_empty() { Ok(()) } else { Err(errors) }
}

fn main() {
    let good_form = RegistrationForm {
        username: "alice_99".to_string(),
        email: "alice@example.com".to_string(),
        password: "securepass123".to_string(),
        age: 25,
    };

    let bad_form = RegistrationForm {
        username: "ab".to_string(),
        email: "not-an-email".to_string(),
        password: "pass".to_string(),
        age: 10,
    };

    match validate(&good_form) {
        Ok(())     => println!("✓ Registration valid!"),
        Err(errs)  => println!("✗ Errors: {:?}", errs),
    }

    match validate(&bad_form) {
        Ok(())     => println!("✓ Registration valid!"),
        Err(errs)  => println!("✗ Errors: {:?}", errs),
    }
}
```

### Scenario 3: Traffic Signal Controller (Embedded Systems)

```go
// ─────────────────── Go ───────────────────
package main

import (
    "fmt"
    "time"
)

type TrafficState int

const (
    Red TrafficState = iota
    Yellow
    Green
)

func (s TrafficState) String() string {
    switch s {
    case Red:
        return "RED"
    case Yellow:
        return "YELLOW"
    case Green:
        return "GREEN"
    default:
        return "UNKNOWN"
    }
}

type Intersection struct {
    State       TrafficState
    Duration    time.Duration
    PedestrianWaiting bool
    EmergencyVehicle  bool
}

func (i *Intersection) NextState() TrafficState {
    // Emergency vehicle overrides everything
    if i.EmergencyVehicle {
        fmt.Println("  [EMERGENCY OVERRIDE] → All RED")
        return Red
    }

    switch i.State {
    case Green:
        if i.PedestrianWaiting || i.Duration >= 45*time.Second {
            return Yellow
        }
        return Green
    case Yellow:
        return Red
    case Red:
        return Green
    default:
        return Red
    }
}

func (i *Intersection) Tick(elapsed time.Duration) {
    i.Duration += elapsed
    next := i.NextState()

    if next != i.State {
        fmt.Printf("  Transition: %s → %s\n", i.State, next)
        i.State = next
        i.Duration = 0
    } else {
        fmt.Printf("  Holding: %s (%s elapsed)\n", i.State, i.Duration)
    }
}

func main() {
    light := &Intersection{State: Green}

    fmt.Println("Normal flow:")
    light.Tick(20 * time.Second)
    light.Tick(30 * time.Second) // triggers Yellow

    light.PedestrianWaiting = true
    light.Tick(5 * time.Second)  // Yellow → Red

    light.PedestrianWaiting = false
    light.Tick(5 * time.Second)  // Red → Green

    fmt.Println("\nEmergency vehicle:")
    light.EmergencyVehicle = true
    light.Tick(1 * time.Second)  // Override → Red
}
```

---

## 16. ⚠️ ANTI-PATTERNS & COMMON MISTAKES

```
TOP CONDITIONAL ANTI-PATTERNS:

  1. Comparing booleans to true/false explicitly:
     BAD:  if (is_valid == true)
     GOOD: if (is_valid)

  2. Double negation (confusion):
     BAD:  if (!is_not_valid)
     GOOD: if (is_valid)

  3. Returning boolean expression wrapped in if/else:
     BAD:
       if (a > b) { return true; }
       else { return false; }
     GOOD:
       return a > b;

  4. Magic numbers in conditions (unreadable):
     BAD:  if (status == 3)
     GOOD: if (status == STATUS_ACTIVE)

  5. Side effects inside conditions (unpredictable):
     BAD:  if ((x = get_value()) > 0)
     GOOD: x = get_value(); if (x > 0)

  6. Not using short-circuit for safety:
     BAD:  if (ptr->value > 0)
     GOOD: if (ptr != NULL && ptr->value > 0)
```

```c
// ─────────────────── C — Anti-patterns fixed ───────────────────
#include <stdio.h>
#include <stdbool.h>

typedef enum { INACTIVE = 0, ACTIVE = 1, BANNED = 2 } UserStatus;

bool is_valid_age(int age) {
    return age >= 18 && age <= 120; // Clean: returns expression directly
}

void check_user(UserStatus status, bool is_verified, int *score_ptr) {
    // Guard: check pointer safety with short-circuit
    if (score_ptr == NULL || *score_ptr < 0) {
        printf("Invalid score pointer or negative score\n");
        return;
    }

    // Use named constant, not magic number
    if (status == ACTIVE && is_verified) {
        printf("User is active and verified. Score: %d\n", *score_ptr);
    } else if (status == BANNED) {
        printf("User is banned.\n");
    } else {
        printf("User is inactive or unverified.\n");
    }
}

int main() {
    printf("Age 20 valid: %s\n", is_valid_age(20) ? "yes" : "no");
    printf("Age 15 valid: %s\n", is_valid_age(15) ? "yes" : "no");

    int score = 95;
    check_user(ACTIVE, true, &score);
    check_user(BANNED, false, &score);
    check_user(ACTIVE, true, NULL); // safe due to guard
    return 0;
}
```

---

## 17. 🧘 MENTAL MODELS & COGNITIVE PRINCIPLES

### Mental Model 1: The Decision Tree

Always visualize conditions as a tree **before** coding. Draw it on paper. Every branch is a `if`, every leaf is an outcome.

```
   Problem → Draw tree → Simplify tree → Code
```

### Mental Model 2: The Guard Clause Inversion

When you find yourself nesting, ask: *"What are the conditions under which I should NOT proceed?"* List those first as guards. What remains is the happy path.

### Mental Model 3: Condition → Predicate Function

When a condition becomes complex, **extract it into a named function**. This improves readability and testability.

```
BAD:
  if (user.age >= 18 && user.is_verified && !user.is_banned
      && user.subscription == ACTIVE && user.balance > 0.0) { ... }

GOOD:
  if (can_make_purchase(&user)) { ... }

  bool can_make_purchase(const User *u) {
      return u->age >= 18
          && u->is_verified
          && !u->is_banned
          && u->subscription == ACTIVE
          && u->balance > 0.0;
  }
```

### Cognitive Principles for Mastery

```
┌──────────────────────────────────────────────────────────────┐
│          DELIBERATE PRACTICE FOR CONDITIONS                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. CHUNKING                                                 │
│     Don't see each operator in isolation.                    │
│     Train your brain to see "guard clause pattern",         │
│     "short-circuit safety pattern", "flag bit pattern"      │
│     as single mental chunks.                                 │
│                                                              │
│  2. TRUTH TABLE HABIT                                        │
│     For any complex compound condition,                      │
│     mentally or physically write the truth table.            │
│     This prevents logical bugs.                              │
│                                                              │
│  3. INVERSION THINKING                                       │
│     For every condition, ask: "What is the complement?"      │
│     This trains you to naturally write guards.               │
│                                                              │
│  4. NAMING DISCIPLINE                                        │
│     Conditions with names are documentation.                 │
│     bool is_eligible = ...                                   │
│     makes the code self-explaining.                          │
│                                                              │
│  5. META-LEARNING: COMPARE LANGUAGES                         │
│     Rust's exhaustive match, Go's init-if, C's truthy ints  │
│     — seeing the same concept across languages deepens       │
│     the underlying mental model.                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🏁 FINAL SUMMARY — CONDITION MASTERY CHECKLIST

```
┌─────────────────────────────────────────────────────────────────┐
│                   MASTERY CHECKLIST                             │
├─────────────────────────────────────────────────────────────────┤
│  ✓ Understand boolean algebra & truth tables                    │
│  ✓ Know all comparison and logical operators                    │
│  ✓ Leverage short-circuit evaluation defensively               │
│  ✓ Write if/else if/else with proper logical flow              │
│  ✓ Eliminate deep nesting with guard clauses                    │
│  ✓ Use switch/match for multi-value dispatch                    │
│  ✓ Exploit Rust's match for exhaustive pattern matching        │
│  ✓ Apply bitwise conditions for flags and permissions           │
│  ✓ Know truthy/falsy rules per language                         │
│  ✓ Use parentheses to make precedence explicit                  │
│  ✓ Name complex conditions with predicate functions             │
│  ✓ Think in decision trees before coding                        │
│  ✓ Avoid anti-patterns: bare booleans, magic numbers, etc.     │
└─────────────────────────────────────────────────────────────────┘

Language Quick Reference:
  C    → Truthy ints, manual short-circuit safety, switch needs break
  Rust → if is expression, match is exhaustive & powerful, bool strict
  Go   → Bool strict, switch auto-breaks, if with init statement
```

> *"Every expert was once a beginner who refused to stop practicing. The deepest insights in programming come not from memorizing syntax, but from understanding why — why short-circuit exists, why guards are cleaner, why match must be exhaustive. When you understand the 'why', the 'how' becomes effortless."*