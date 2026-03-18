# Comprehensive Guide to Loop Selection

> *"Loops are not just control flow — they are the heartbeat of an algorithm. Choosing the wrong loop is like breathing backwards."*

---

## 📌 What is a Loop? (Foundation)

Before diving into loop types, let's anchor the concept deeply.

A **loop** is a mechanism that allows a block of code to be **repeated** — either a fixed number of times, until a condition changes, or indefinitely until explicitly stopped.

Mentally model a loop as a **contract** between you and the machine:

```
"Keep doing this work, under these conditions, until I tell you to stop."
```

Every loop in existence — regardless of language — has exactly **4 structural components**:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ANATOMY OF EVERY LOOP                       │
├───────────────┬─────────────────────────────────────────────────┤
│ 1. INIT       │ Starting state. What variable do we begin with? │
│               │ Example: i = 0, cursor = head, total = 0        │
├───────────────┼─────────────────────────────────────────────────┤
│ 2. CONDITION  │ The "keep going?" question.                      │
│               │ Evaluated BEFORE (or AFTER) each iteration.     │
│               │ Example: i < 10, node != NULL, !queue.empty()   │
├───────────────┼─────────────────────────────────────────────────┤
│ 3. BODY       │ The actual work done per iteration.              │
│               │ Example: sum += arr[i], process(node)            │
├───────────────┼─────────────────────────────────────────────────┤
│ 4. UPDATE     │ How state advances toward termination.           │
│               │ Example: i++, node = node->next, i -= 2         │
└───────────────┴─────────────────────────────────────────────────┘
```

If **any** of these 4 components is wrong, your loop is broken — either it terminates early, never terminates (infinite loop bug), or skips work.

---

## 🧠 The Loop Mindset (Expert Mental Model)

Before writing a loop, an expert asks **5 questions**:

```
┌─────────────────────────────────────────────────────────────┐
│              EXPERT PRE-LOOP CHECKLIST                      │
├─────┬───────────────────────────────────────────────────────┤
│  Q1 │ Do I know the number of iterations UPFRONT?           │
│     │ → YES: use a FOR loop (counting loop)                 │
│     │ → NO:  use a WHILE loop (condition loop)              │
├─────┼───────────────────────────────────────────────────────┤
│  Q2 │ Must the body execute AT LEAST ONCE before checking?  │
│     │ → YES: use DO-WHILE                                   │
│     │ → NO:  use WHILE                                      │
├─────┼───────────────────────────────────────────────────────┤
│  Q3 │ Am I iterating over a COLLECTION (array, list, map)?  │
│     │ → YES: use ITERATOR-BASED loop (for-each / range)     │
│     │ → NO:  use index-based or condition-based loop        │
├─────┼───────────────────────────────────────────────────────┤
│  Q4 │ Am I running a server / event pump with no end?       │
│     │ → YES: use INFINITE loop with explicit break          │
├─────┼───────────────────────────────────────────────────────┤
│  Q5 │ Do I need to exit MULTIPLE nested loops at once?      │
│     │ → YES: use labeled break/continue (Go/Rust)           │
└─────┴───────────────────────────────────────────────────────┘
```

---

## 🔷 PART 1: Types of Loops

---

### 1.1 The `for` Loop — "I Know the Count"

The `for` loop is used when the **number of repetitions is known** before entering the loop.

#### How it flows:

```
          ┌──────────────────────────────────┐
          │           FOR LOOP FLOW          │
          └──────────────────────────────────┘

   ┌──────────────┐
   │     INIT     │  ← runs ONCE at the very start
   │   (i = 0)    │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐    NO (false)    ┌──────────────┐
   │  CONDITION?  │ ─────────────── ▶│     EXIT     │
   │  (i < n)     │                  └──────────────┘
   └──────┬───────┘
          │ YES (true)
          ▼
   ┌──────────────┐
   │     BODY     │  ← your actual work
   │  (arr[i]...) │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │    UPDATE    │  ← i++ runs AFTER body, BEFORE re-checking
   │    (i++)     │
   └──────┬───────┘
          │
          └──────────────────────────── (loop back to CONDITION)
```

#### Real-World Scenario: Processing invoice line items

> You receive an invoice with a fixed set of line items. You know exactly how many there are. You want to calculate the total.

```c
// ─────────────────────────────────────────────────────────────
// C IMPLEMENTATION
// ─────────────────────────────────────────────────────────────
#include <stdio.h>

int main(void) {
    double prices[] = {29.99, 14.50, 5.00, 89.99, 12.00};
    int count = 5;  // known upfront!
    double total = 0.0;

    for (int i = 0; i < count; i++) {
        total += prices[i];
    }

    printf("Invoice total: $%.2f\n", total);
    return 0;
}
```

```rust
// ─────────────────────────────────────────────────────────────
// RUST IMPLEMENTATION
// ─────────────────────────────────────────────────────────────
fn main() {
    let prices = [29.99f64, 14.50, 5.00, 89.99, 12.00];
    let mut total = 0.0f64;

    // Range 0..prices.len() generates 0,1,2,3,4
    for i in 0..prices.len() {
        total += prices[i];
    }

    // Even more idiomatic Rust: iterate directly
    let total_idiomatic: f64 = prices.iter().sum();

    println!("Invoice total: ${:.2}", total);
    println!("Idiomatic total: ${:.2}", total_idiomatic);
}
```

```go
// ─────────────────────────────────────────────────────────────
// GO IMPLEMENTATION
// ─────────────────────────────────────────────────────────────
package main

import "fmt"

func main() {
    prices := []float64{29.99, 14.50, 5.00, 89.99, 12.00}
    total := 0.0

    for i := 0; i < len(prices); i++ {
        total += prices[i]
    }

    fmt.Printf("Invoice total: $%.2f\n", total)
}
```

#### Key Insight About `for` Loops:

```
MENTAL NOTE:
┌──────────────────────────────────────────────────────────┐
│ The for loop is syntactic sugar for a structured while.  │
│                                                          │
│   for (init; cond; update) { body }                      │
│                                                          │
│   is EXACTLY equivalent to:                              │
│                                                          │
│   init;                                                  │
│   while (cond) { body; update; }                         │
│                                                          │
│ They generate almost identical machine code.             │
│ The difference is ONLY about programmer intent/clarity.  │
└──────────────────────────────────────────────────────────┘
```

---

### 1.2 The `while` Loop — "I Don't Know When It Ends"

The `while` loop is used when termination depends on **a condition you cannot predict upfront**.

#### How it flows:

```
          ┌──────────────────────────────────┐
          │          WHILE LOOP FLOW         │
          └──────────────────────────────────┘

   ┌────────────────┐
   │   SETUP BEFORE │  ← your init happens OUTSIDE the loop
   │   (e.g. read   │
   │    first input)│
   └────────┬───────┘
            │
            ▼
   ┌────────────────┐   NO (false)   ┌─────────────┐
   │   CONDITION?   │ ─────────────▶ │    EXIT     │
   │ (checked FIRST)│                └─────────────┘
   └────────┬───────┘
            │ YES (true)
            ▼
   ┌────────────────┐
   │      BODY      │
   │  (do the work) │
   └────────┬───────┘
            │
            ▼
   ┌────────────────┐
   │  UPDATE STATE  │  ← must happen inside body to avoid
   │  (read next,   │    infinite loop
   │   advance ptr) │
   └────────┬───────┘
            │
            └──────────── (loop back to CONDITION)
```

#### Real-World Scenario: Reading user input until valid

> A banking ATM keeps asking for a PIN until the user enters one with exactly 4 digits. You cannot know how many attempts they'll make.

```c
// ─────────────────────────────────────────────────────────────
// C IMPLEMENTATION
// ─────────────────────────────────────────────────────────────
#include <stdio.h>
#include <string.h>

int is_valid_pin(const char *pin) {
    if (strlen(pin) != 4) return 0;
    for (int i = 0; i < 4; i++) {
        if (pin[i] < '0' || pin[i] > '9') return 0;
    }
    return 1;
}

int main(void) {
    char pin[100];
    int valid = 0;  // condition variable

    // We DON'T know how many attempts → while loop
    while (!valid) {
        printf("Enter 4-digit PIN: ");
        scanf("%s", pin);

        if (is_valid_pin(pin)) {
            valid = 1;
        } else {
            printf("Invalid PIN. Must be exactly 4 digits.\n");
        }
    }

    printf("PIN accepted.\n");
    return 0;
}
```

```rust
// ─────────────────────────────────────────────────────────────
// RUST IMPLEMENTATION
// ─────────────────────────────────────────────────────────────
use std::io::{self, BufRead};

fn is_valid_pin(pin: &str) -> bool {
    pin.len() == 4 && pin.chars().all(|c| c.is_ascii_digit())
}

fn main() {
    let stdin = io::stdin();

    loop {  // Rust idiom: 'loop' is preferred over 'while true'
        print!("Enter 4-digit PIN: ");
        let mut input = String::new();
        stdin.lock().read_line(&mut input).unwrap();
        let pin = input.trim();

        if is_valid_pin(pin) {
            println!("PIN accepted.");
            break;
        } else {
            println!("Invalid PIN. Must be exactly 4 digits.");
        }
    }
}
```

```go
// ─────────────────────────────────────────────────────────────
// GO IMPLEMENTATION
// ─────────────────────────────────────────────────────────────
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

func isValidPIN(pin string) bool {
    if len(pin) != 4 {
        return false
    }
    for _, c := range pin {
        if c < '0' || c > '9' {
            return false
        }
    }
    return true
}

func main() {
    scanner := bufio.NewScanner(os.Stdin)

    for { // Go has no 'while'; use 'for' with no condition = infinite loop
        fmt.Print("Enter 4-digit PIN: ")
        scanner.Scan()
        pin := strings.TrimSpace(scanner.Text())

        if isValidPIN(pin) {
            fmt.Println("PIN accepted.")
            break
        }
        fmt.Println("Invalid PIN. Must be exactly 4 digits.")
    }
}
```

---

### 1.3 The `do-while` Loop — "Run First, Ask Questions Later"

This is the **most misunderstood** loop. The key insight:

```
┌──────────────────────────────────────────────────────────────┐
│  do-while guarantees the body runs AT LEAST ONCE.            │
│                                                              │
│  The condition is checked AFTER the first execution,         │
│  not before.                                                 │
│                                                              │
│  Use when: "I must do it once and then decide to continue."  │
└──────────────────────────────────────────────────────────────┘
```

#### How it flows:

```
          ┌──────────────────────────────────┐
          │        DO-WHILE LOOP FLOW        │
          └──────────────────────────────────┘

   ┌────────────────┐
   │     ENTRY      │  ← no condition check here — go straight in!
   └────────┬───────┘
            │
            ▼
   ┌────────────────┐
   │      BODY      │  ← executes UNCONDITIONALLY on first pass
   │  (do the work) │
   └────────┬───────┘
            │
            ▼
   ┌────────────────┐   YES (true)
   │   CONDITION?   │ ──────────────── (loop back to BODY)
   └────────┬───────┘
            │ NO (false)
            ▼
   ┌────────────────┐
   │      EXIT      │
   └────────────────┘
```

#### The CRITICAL Difference — while vs do-while:

```
WHILE:                          DO-WHILE:
──────────────────────────────────────────────────────────────
  Condition FALSE at start?       Condition FALSE at start?
  → Body NEVER executes           → Body executes ONCE then stops

  Condition always TRUE?          Condition always TRUE?
  → Infinite loop                 → Infinite loop

  Use when 0 executions is fine   Use when ≥1 execution required
──────────────────────────────────────────────────────────────
```

#### Real-World Scenario: Game "Play Again?" menu

> A game must show the main menu at least once, then ask if the player wants to play again.

```c
// ─────────────────────────────────────────────────────────────
// C IMPLEMENTATION
// ─────────────────────────────────────────────────────────────
#include <stdio.h>

void play_game(void) {
    printf("[Game running...]\n");
}

int main(void) {
    char choice;

    do {
        play_game();
        printf("Play again? (y/n): ");
        scanf(" %c", &choice);  // space before %c skips whitespace
    } while (choice == 'y' || choice == 'Y');

    printf("Thanks for playing!\n");
    return 0;
}
```

```rust
// ─────────────────────────────────────────────────────────────
// RUST IMPLEMENTATION
// Rust has NO do-while syntax. Use loop + break pattern.
// ─────────────────────────────────────────────────────────────
use std::io::{self, BufRead};

fn play_game() {
    println!("[Game running...]");
}

fn main() {
    let stdin = io::stdin();

    loop {
        play_game();  // body executes first

        print!("Play again? (y/n): ");
        let mut input = String::new();
        stdin.lock().read_line(&mut input).unwrap();
        let choice = input.trim().to_lowercase();

        if choice != "y" {  // condition checked AFTER body
            break;
        }
    }

    println!("Thanks for playing!");
}
```

```go
// ─────────────────────────────────────────────────────────────
// GO IMPLEMENTATION
// Go has NO do-while syntax. Use for + break pattern.
// ─────────────────────────────────────────────────────────────
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

func playGame() {
    fmt.Println("[Game running...]")
}

func main() {
    scanner := bufio.NewScanner(os.Stdin)

    for {
        playGame() // body executes first (do-while simulation)

        fmt.Print("Play again? (y/n): ")
        scanner.Scan()
        choice := strings.TrimSpace(scanner.Text())

        if strings.ToLower(choice) != "y" {
            break // condition checked AFTER
        }
    }

    fmt.Println("Thanks for playing!")
}
```

---

### 1.4 The Infinite Loop — "Run Forever Until Told to Stop"

```
┌──────────────────────────────────────────────────────────────┐
│  An INFINITE LOOP intentionally has no termination           │
│  condition in the loop header itself.                        │
│                                                              │
│  Termination happens via INTERNAL LOGIC:                     │
│    → break                                                   │
│    → return                                                  │
│    → panic / exception                                       │
│    → signal/interrupt (OS level)                             │
│                                                              │
│  Use cases:                                                  │
│    → Servers (HTTP, TCP) listening forever                   │
│    → Event loops (GUI, game engines)                         │
│    → Background workers / daemons                            │
│    → Read-eval-print loops (REPL)                            │
└──────────────────────────────────────────────────────────────┘
```

#### How it flows:

```
   ┌────────────────┐
   │  loop / for {} │◄─────────────────────┐
   └────────┬───────┘                      │
            │                              │
            ▼                              │
   ┌────────────────┐                      │
   │  WAIT/RECEIVE  │  ← block for event   │
   │  (accept conn, │                      │
   │   read stdin)  │                      │
   └────────┬───────┘                      │
            │                              │
            ▼                              │
   ┌────────────────┐   NO (continue)      │
   │  EXIT signal?  │ ──────────────────── ┘
   └────────┬───────┘
            │ YES
            ▼
   ┌────────────────┐
   │   CLEANUP &    │
   │     BREAK      │
   └────────────────┘
```

#### Real-World Scenario: TCP server accepting connections

```c
// ─────────────────────────────────────────────────────────────
// C IMPLEMENTATION — simplified server event loop
// ─────────────────────────────────────────────────────────────
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>

static volatile int running = 1;

void handle_signal(int sig) {
    running = 0;  // graceful shutdown flag
}

int main(void) {
    signal(SIGINT, handle_signal);

    printf("Server started. Press Ctrl+C to stop.\n");

    // Infinite loop — the server runs until a signal
    while (running) {
        // In real code: accept() blocks here
        printf("Waiting for connection...\n");
        sleep(1); // simulate blocking wait
    }

    printf("Server shutting down gracefully.\n");
    return 0;
}
```

```rust
// ─────────────────────────────────────────────────────────────
// RUST IMPLEMENTATION — Rust's 'loop' keyword is the
// idiomatic infinite loop. It's not while(true) — it's a
// first-class construct with special compiler optimizations.
// ─────────────────────────────────────────────────────────────
use std::io::{self, BufRead};

fn main() {
    println!("REPL started. Type 'exit' to quit.");
    let stdin = io::stdin();

    loop {
        print!("> ");
        let mut line = String::new();
        match stdin.lock().read_line(&mut line) {
            Ok(0) => break,  // EOF
            Ok(_) => {
                let input = line.trim();
                match input {
                    "exit" | "quit" => break,
                    "" => continue,
                    cmd => println!("You typed: {}", cmd),
                }
            }
            Err(e) => {
                eprintln!("Error: {}", e);
                break;
            }
        }
    }

    println!("Goodbye.");
}
```

```go
// ─────────────────────────────────────────────────────────────
// GO IMPLEMENTATION — channel-based graceful shutdown
// This is the idiomatic Go pattern for infinite service loops
// ─────────────────────────────────────────────────────────────
package main

import (
    "fmt"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func main() {
    // Create channel to receive OS signals
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

    tick := time.NewTicker(1 * time.Second)
    defer tick.Stop()

    fmt.Println("Service running. Press Ctrl+C to stop.")

    for { // infinite loop
        select {
        case <-tick.C:
            fmt.Println("Processing heartbeat...")
        case sig := <-quit:
            fmt.Printf("\nReceived signal: %v. Shutting down.\n", sig)
            return // exits the loop and main()
        }
    }
}
```

---

### 1.5 Iterator-Based Loops — "Walk the Collection"

This is the **highest-level** loop — you describe **what** to iterate, not **how**.

```
┌──────────────────────────────────────────────────────────────┐
│  An iterator abstracts away the index, pointer arithmetic,   │
│  and bounds checking. You just say "give me the next item."  │
│                                                              │
│  Think of it like a conveyor belt: items come to YOU,        │
│  you don't go fetch them by index.                           │
│                                                              │
│  ITERATOR PATTERN:                                           │
│    cursor → [item1] → [item2] → [item3] → DONE              │
│              ↑ here    ↑ next    ↑ next   ↑ None/null/end   │
└──────────────────────────────────────────────────────────────┘
```

#### Iterator Flow:

```
   ┌──────────────────────────┐
   │  COLLECTION exists?      │
   │  (array, list, map...)   │
   └──────────┬───────────────┘
              │
              ▼
   ┌──────────────────────────┐
   │  GET ITERATOR/CURSOR     │
   │  (auto in for-each/range)│
   └──────────┬───────────────┘
              │
              ▼
   ┌──────────────────────────┐    NO    ┌─────────────┐
   │  HAS NEXT ELEMENT?       │ ────────▶│    DONE     │
   └──────────┬───────────────┘          └─────────────┘
              │ YES
              ▼
   ┌──────────────────────────┐
   │  YIELD ELEMENT           │
   │  (bind to variable)      │
   └──────────┬───────────────┘
              │
              ▼
   ┌──────────────────────────┐
   │  EXECUTE BODY            │
   │  with current element    │
   └──────────┬───────────────┘
              │
              └──────────── (advance cursor, loop back to HAS NEXT)
```

#### Real-World Scenario: Processing a list of orders

```c
// ─────────────────────────────────────────────────────────────
// C — no built-in foreach, but we simulate it cleanly
// ─────────────────────────────────────────────────────────────
#include <stdio.h>

typedef struct {
    int id;
    double amount;
    const char *status;
} Order;

int main(void) {
    Order orders[] = {
        {1001, 250.00, "shipped"},
        {1002, 99.50,  "pending"},
        {1003, 420.00, "delivered"},
        {1004, 15.75,  "pending"},
    };

    // sizeof trick to get count without a magic number
    int n = sizeof(orders) / sizeof(orders[0]);

    // Iterate over the collection
    for (int i = 0; i < n; i++) {
        Order *o = &orders[i];  // pointer to current element
        if (o->amount > 100.0) {
            printf("Order %d: $%.2f (%s)\n", o->id, o->amount, o->status);
        }
    }
    return 0;
}
```

```rust
// ─────────────────────────────────────────────────────────────
// RUST — iterators are a first-class feature with zero-cost
// abstraction. The compiler optimizes iterator chains into
// machine code equivalent to hand-written loops.
// ─────────────────────────────────────────────────────────────
struct Order {
    id: u32,
    amount: f64,
    status: &'static str,
}

fn main() {
    let orders = vec![
        Order { id: 1001, amount: 250.00, status: "shipped" },
        Order { id: 1002, amount: 99.50,  status: "pending" },
        Order { id: 1003, amount: 420.00, status: "delivered" },
        Order { id: 1004, amount: 15.75,  status: "pending" },
    ];

    // ── Style 1: for-in (most readable, idiomatic Rust)
    for order in &orders {
        if order.amount > 100.0 {
            println!("Order {}: ${:.2} ({})", order.id, order.amount, order.status);
        }
    }

    // ── Style 2: Iterator chain (functional, zero-cost)
    orders.iter()
        .filter(|o| o.amount > 100.0)
        .for_each(|o| println!("Order {}: ${:.2} ({})", o.id, o.amount, o.status));

    // ── Style 3: Collect filtered results
    let high_value: Vec<&Order> = orders.iter()
        .filter(|o| o.amount > 100.0)
        .collect();

    println!("High value order count: {}", high_value.len());
}
```

```go
// ─────────────────────────────────────────────────────────────
// GO — range keyword iterates over arrays, slices, maps,
// channels, and strings. It's Go's foreach.
// ─────────────────────────────────────────────────────────────
package main

import "fmt"

type Order struct {
    ID     int
    Amount float64
    Status string
}

func main() {
    orders := []Order{
        {1001, 250.00, "shipped"},
        {1002, 99.50,  "pending"},
        {1003, 420.00, "delivered"},
        {1004, 15.75,  "pending"},
    }

    // range returns (index, value) for slices
    for i, order := range orders {
        if order.Amount > 100.0 {
            fmt.Printf("[%d] Order %d: $%.2f (%s)\n",
                i, order.ID, order.Amount, order.Status)
        }
    }

    // Discard index with blank identifier _
    for _, order := range orders {
        if order.Status == "pending" {
            fmt.Printf("Pending: Order %d\n", order.ID)
        }
    }
}
```

---

## 🔷 PART 2: Loop Control Mechanisms

These are the **escape hatches and shortcuts** inside loops.

```
┌─────────────────────────────────────────────────────────────────┐
│                   LOOP CONTROL SUMMARY                          │
├──────────────┬──────────────────────────────────────────────────┤
│  break       │ EXIT the loop immediately                        │
│              │ "I found what I need. Stop."                     │
├──────────────┼──────────────────────────────────────────────────┤
│  continue    │ SKIP the current iteration, go to next           │
│              │ "This item is not relevant. Skip it."            │
├──────────────┼──────────────────────────────────────────────────┤
│  return      │ EXIT the entire function (loop dies too)         │
│              │ "Result found. Leave everything."                │
├──────────────┼──────────────────────────────────────────────────┤
│  labeled     │ break/continue on a SPECIFIC outer loop          │
│  break/cont  │ (Rust: 'label; Go: label:)                       │
│              │ "Break out of the OUTER loop, not just inner."   │
└──────────────┴──────────────────────────────────────────────────┘
```

### 2.1 `break` — Early Exit

```
LOOP ITERATION TRACE WITH break:

  Iteration 1: [ BODY ] → condition not met → CONTINUE
  Iteration 2: [ BODY ] → condition not met → CONTINUE
  Iteration 3: [ BODY ] → BREAK CONDITION MET → ──────┐
  Iteration 4: (never executed)                        │
  Iteration 5: (never executed)                        │
                                                        ▼
                                                  [ AFTER LOOP ]
```

#### Real-World Scenario: Linear search — find first match

```c
// C: find first order over $300
int found_idx = -1;
for (int i = 0; i < n; i++) {
    if (orders[i].amount > 300.0) {
        found_idx = i;
        break;  // stop searching — we have what we need
    }
}
// After loop: found_idx is -1 (not found) or the index
```

```rust
// Rust: break can return a VALUE from a loop (unique feature!)
let found = 'search: loop {
    for order in &orders {
        if order.amount > 300.0 {
            break 'search Some(order);  // returns the value!
        }
    }
    break 'search None;
};

// More idiomatic:
let found = orders.iter().find(|o| o.amount > 300.0);
```

```go
// Go: break exits the innermost loop
found := -1
for i, order := range orders {
    if order.Amount > 300.0 {
        found = i
        break
    }
}
```

---

### 2.2 `continue` — Skip Current Iteration

```
LOOP ITERATION TRACE WITH continue:

  Iteration 1: [ BODY fully ] → no continue → UPDATE → next
  Iteration 2: [ BODY partly ] → CONTINUE → UPDATE → next ←──┐
               (rest of body is SKIPPED)                       │
               ↑                                               │
               └──── jumps to UPDATE (for) or condition (while)┘
  Iteration 3: [ BODY fully ] → normal
```

#### Real-World Scenario: Skip invalid records in a CSV pipeline

```c
// C: skip empty/null records
for (int i = 0; i < row_count; i++) {
    if (rows[i].name == NULL || rows[i].amount <= 0) {
        continue;  // skip bad data
    }
    // process valid row
    process_row(&rows[i]);
}
```

```rust
// Rust: continue in iterators = filter()
// Manual:
for row in &rows {
    if row.name.is_empty() || row.amount <= 0.0 {
        continue;
    }
    process_row(row);
}

// Idiomatic — filter expresses intent better:
rows.iter()
    .filter(|r| !r.name.is_empty() && r.amount > 0.0)
    .for_each(|r| process_row(r));
```

```go
// Go: continue works exactly like C
for _, row := range rows {
    if row.Name == "" || row.Amount <= 0 {
        continue
    }
    processRow(row)
}
```

---

### 2.3 Labeled Break / Continue — Escape Nested Loops

This is where most programmers struggle. When you have nested loops, plain `break` only exits the **innermost** loop.

```
NESTED LOOP PROBLEM:

  for outer {
      for inner {
          if (found) {
              break;  ← This only breaks INNER loop!
                        Outer loop continues!
          }
      }
  }

SOLUTION → labeled break:

  'outer: for outer {          // Go: outer: for
      for inner {
          if (found) {
              break 'outer;   // Go: break outer
          }                    // Exits BOTH loops!
      }
  }
```

#### Real-World Scenario: 2D grid search (find a target cell)

```c
// ─────────────────────────────────────────────────────────────
// C: No labeled break. Use a flag or goto.
// goto is legitimate here — it's exactly what labeled break compiles to.
// ─────────────────────────────────────────────────────────────
#include <stdio.h>

int main(void) {
    int grid[4][4] = {
        {1,  2,  3,  4},
        {5,  6,  7,  8},
        {9, 10, 99, 12},   // 99 is what we want
        {13,14, 15, 16}
    };

    int target = 99;
    int found_row = -1, found_col = -1;

    for (int r = 0; r < 4; r++) {
        for (int c = 0; c < 4; c++) {
            if (grid[r][c] == target) {
                found_row = r;
                found_col = c;
                goto found;  // idiomatic C for labeled break
            }
        }
    }

found:
    if (found_row >= 0) {
        printf("Found %d at [%d][%d]\n", target, found_row, found_col);
    } else {
        printf("Not found.\n");
    }
    return 0;
}
```

```rust
// ─────────────────────────────────────────────────────────────
// RUST: labeled loops with tick-prefix 'label
// ─────────────────────────────────────────────────────────────
fn main() {
    let grid = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9, 10, 99, 12],
        [13, 14, 15, 16],
    ];

    let target = 99;
    let mut position: Option<(usize, usize)> = None;

    'outer: for (r, row) in grid.iter().enumerate() {
        for (c, &val) in row.iter().enumerate() {
            if val == target {
                position = Some((r, c));
                break 'outer;  // exits both loops!
            }
        }
    }

    match position {
        Some((r, c)) => println!("Found {} at [{r}][{c}]", target),
        None         => println!("Not found."),
    }
}
```

```go
// ─────────────────────────────────────────────────────────────
// GO: labeled loops with label followed by colon
// ─────────────────────────────────────────────────────────────
package main

import "fmt"

func main() {
    grid := [4][4]int{
        {1,  2,  3,  4},
        {5,  6,  7,  8},
        {9, 10, 99, 12},
        {13, 14, 15, 16},
    }

    target := 99
    foundRow, foundCol := -1, -1

outer: // label on the outer loop
    for r, row := range grid {
        for c, val := range row {
            if val == target {
                foundRow, foundCol = r, c
                break outer // exits both loops!
            }
        }
    }

    if foundRow >= 0 {
        fmt.Printf("Found %d at [%d][%d]\n", target, foundRow, foundCol)
    } else {
        fmt.Println("Not found.")
    }
}
```

---

## 🔷 PART 3: The Loop Selection Decision Tree

This is the **master flowchart** you run in your head before writing any loop.

```
                 ┌─────────────────────────────────────┐
                 │         NEED REPETITION?             │
                 └──────────────┬──────────────────────┘
                                │ YES
                                ▼
               ┌────────────────────────────────┐
               │   Am I iterating a COLLECTION? │
               │  (array, list, map, string...) │
               └────────────┬───────────────────┘
                             │
               ┌─────────────┴──────────────────┐
               YES                               NO
               │                                 │
               ▼                                 ▼
  ┌────────────────────────┐      ┌──────────────────────────┐
  │  for-each / range      │      │  Do I KNOW the iteration │
  │  for item in list      │      │  COUNT before the loop?  │
  │  (Rust: for x in xs)   │      └──────────┬───────────────┘
  │  (Go: for _, v := range│                  │
  │  (C: for i < len)      │     ┌────────────┴────────────┐
  └────────────────────────┘     YES                        NO
                                  │                          │
                                  ▼                          ▼
                     ┌───────────────────────┐  ┌────────────────────────┐
                     │  C-style for loop     │  │ Must body run          │
                     │  for(i=0; i<n; i++)   │  │ AT LEAST ONCE?         │
                     │  (Rust: for i in 0..n)│  └──────────┬─────────────┘
                     │  (Go: for i:=0;i<n;)  │             │
                     └───────────────────────┘  ┌──────────┴──────────┐
                                                 YES                    NO
                                                 │                      │
                                                 ▼                      ▼
                                    ┌────────────────────┐  ┌────────────────────┐
                                    │  do { ... }        │  │  while (condition) │
                                    │  while (condition) │  │  for {} (Go/Rust)  │
                                    │                    │  │  loop {} (Rust)    │
                                    │  (Rust: loop +     │  └────────────────────┘
                                    │   break pattern)   │
                                    │  (Go: for + break) │
                                    └────────────────────┘
                                    
                    ┌──────────────────────────────────────────┐
                    │  SPECIAL CASE: No natural end condition?  │
                    │  (server, daemon, event loop)             │
                    │                                          │
                    │  → Use INFINITE loop + internal break    │
                    │    while(1) / for{} / loop{}             │
                    └──────────────────────────────────────────┘
```

---

## 🔷 PART 4: Nested Loops — Complexity and Patterns

Understanding nested loops is critical for analyzing algorithm complexity.

### 4.1 Complexity Analysis

```
NESTING DEPTH vs COMPLEXITY:

  1 loop  →  O(n)        linear
  2 loops →  O(n²)       quadratic
  3 loops →  O(n³)       cubic
  k loops →  O(nᵏ)       polynomial

VISUALIZATION (n=4):

  1 loop:  ████████████████  (16 steps = O(n) = O(4))
  
  2 loops: ████████████████  ←─ outer iteration 1
           ████████████████  ←─ outer iteration 2
           ████████████████  ←─ outer iteration 3
           ████████████████  ←─ outer iteration 4
           Total: 16 × 4 = 16 = O(n²) = O(16)

  3 loops: 4 × 4 × 4 = 64 iterations = O(n³)
```

### 4.2 Common Nested Loop Patterns

#### Pattern 1: Matrix Traversal (Row-Major Order)

```
MEMORY LAYOUT (row-major = row elements are contiguous):

  matrix[0][0] matrix[0][1] matrix[0][2]  ← row 0 in memory
  matrix[1][0] matrix[1][1] matrix[1][2]  ← row 1 in memory

  ✅ CORRECT (cache-friendly — row-major):
     for r in rows:
       for c in cols:
         access matrix[r][c]

  ❌ WRONG (cache-unfriendly — column-major):
     for c in cols:
       for r in rows:
         access matrix[r][c]  ← jumps across memory!

CACHE BEHAVIOR:
  Cache line loads: 64 bytes at a time
  Row-major:    [1][2][3][4] loaded together → 1 cache miss per row
  Column-major: [1] in one row, [1] in next row → n cache misses per column!
```

```c
// C: matrix multiplication — demonstrating row-major access
void matrix_multiply(int A[][3], int B[][3], int C[][3], int n) {
    // Reset C
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            C[i][j] = 0;

    // O(n³) — standard matrix multiplication
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            for (int k = 0; k < n; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}
```

```rust
// Rust: matrix traversal with bounds safety
fn print_matrix(matrix: &Vec<Vec<i32>>) {
    let rows = matrix.len();
    let cols = if rows > 0 { matrix[0].len() } else { 0 };

    for r in 0..rows {
        for c in 0..cols {
            print!("{:4}", matrix[r][c]);
        }
        println!();
    }
}
```

```go
// Go: initialize and traverse a 2D grid
func newGrid(rows, cols int) [][]int {
    grid := make([][]int, rows)
    for i := range grid {
        grid[i] = make([]int, cols)
        for j := range grid[i] {
            grid[i][j] = i*cols + j  // fill with sequence
        }
    }
    return grid
}
```

---

#### Pattern 2: Triangle / Half-Matrix (Comparing All Pairs)

```
VISUALIZATION: comparing all unique pairs in [A, B, C, D]

     A B C D
  A  . X X X     ← compare A with B, C, D
  B    . X X     ← compare B with C, D
  C      . X     ← compare C with D
  D        .     ← D has no one left to compare
  
  Total comparisons = n*(n-1)/2 = O(n²)
  But inner loop starts AFTER outer → we skip duplicates!
```

```c
// C: find all duplicate values in an array
#include <stdio.h>

void find_duplicates(int *arr, int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = i + 1; j < n; j++) {  // j starts at i+1 ← triangle!
            if (arr[i] == arr[j]) {
                printf("Duplicate found: %d at positions %d and %d\n",
                       arr[i], i, j);
            }
        }
    }
}
```

```rust
fn find_duplicates(arr: &[i32]) {
    for i in 0..arr.len() {
        for j in (i + 1)..arr.len() {  // j starts at i+1
            if arr[i] == arr[j] {
                println!("Duplicate: {} at [{i}] and [{j}]", arr[i]);
            }
        }
    }
}
```

```go
func findDuplicates(arr []int) {
    for i := 0; i < len(arr)-1; i++ {
        for j := i + 1; j < len(arr); j++ {
            if arr[i] == arr[j] {
                fmt.Printf("Duplicate: %d at [%d] and [%d]\n", arr[i], i, j)
            }
        }
    }
}
```

---

## 🔷 PART 5: Advanced Loop Patterns

### 5.1 The Sentinel Pattern

A **sentinel value** is a special value that signals "end of data." It's used when you don't know the collection size upfront but data ends with a recognizable marker.

```
CONCEPT:

  [ data ] [ data ] [ data ] [ data ] [ SENTINEL ] → stop

  Example: C strings end with '\0' (null terminator)
  Example: linked lists end with NULL pointer
  Example: user input ends with specific command

  The loop runs UNTIL the sentinel is seen.
```

```c
// C: the strlen() function — finding string length via sentinel
size_t my_strlen(const char *s) {
    const char *p = s;
    while (*p != '\0') {  // '\0' is the sentinel
        p++;
    }
    return p - s;  // pointer arithmetic = length
}

// Null-terminated linked list traversal
typedef struct Node {
    int data;
    struct Node *next;
} Node;

void print_list(Node *head) {
    Node *curr = head;
    while (curr != NULL) {  // NULL is the sentinel for linked lists
        printf("%d ", curr->data);
        curr = curr->next;
    }
    printf("\n");
}
```

```rust
// Rust: Option<T> is the safe sentinel (no null pointers!)
struct Node {
    data: i32,
    next: Option<Box<Node>>,
}

fn print_list(head: &Option<Box<Node>>) {
    let mut current = head;
    while let Some(node) = current {
        print!("{} ", node.data);
        current = &node.next;  // None is the sentinel
    }
    println!();
}
```

```go
// Go: nil is the sentinel for pointers
type Node struct {
    Data int
    Next *Node
}

func printList(head *Node) {
    for curr := head; curr != nil; curr = curr.Next {
        fmt.Printf("%d ", curr.Data)
    }
    fmt.Println()
}
```

---

### 5.2 The Two-Pointer Pattern

A powerful technique where **two loop variables** move through the same data structure simultaneously. Reduces O(n²) problems to O(n).

```
VISUALIZATION: Two Sum problem
  Target: 9
  Array:  [2, 4, 5, 7, 8, 11]
  
  left=0                right=5
  [2, 4, 5, 7, 8, 11]
   L                R
  2 + 11 = 13 > 9  → move right inward

  left=0         right=4
  [2, 4, 5, 7, 8, 11]
   L           R
  2 + 8 = 10 > 9  → move right inward

  left=0      right=3
  [2, 4, 5, 7, 8, 11]
   L        R
  2 + 7 = 9 ✓ FOUND!
```

```c
// C: Two-pointer for sorted two-sum
// O(n) time vs O(n²) brute force
int two_sum_sorted(int *arr, int n, int target,
                   int *out_i, int *out_j) {
    int left = 0;
    int right = n - 1;

    while (left < right) {
        int sum = arr[left] + arr[right];
        if (sum == target) {
            *out_i = left;
            *out_j = right;
            return 1;  // found
        } else if (sum < target) {
            left++;   // need larger sum → move left forward
        } else {
            right--;  // need smaller sum → move right inward
        }
    }
    return 0;  // not found
}
```

```rust
fn two_sum_sorted(arr: &[i32], target: i32) -> Option<(usize, usize)> {
    let mut left = 0;
    let mut right = arr.len() - 1;

    while left < right {
        let sum = arr[left] + arr[right];
        match sum.cmp(&target) {
            std::cmp::Ordering::Equal   => return Some((left, right)),
            std::cmp::Ordering::Less    => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    None
}
```

```go
func twoSumSorted(arr []int, target int) (int, int, bool) {
    left, right := 0, len(arr)-1

    for left < right {
        sum := arr[left] + arr[right]
        switch {
        case sum == target:
            return left, right, true
        case sum < target:
            left++
        default:
            right--
        }
    }
    return -1, -1, false
}
```

---

### 5.3 The Sliding Window Pattern

Move a **fixed-size window** over data without recomputing from scratch each step.

```
VISUALIZATION: Max sum of 3 consecutive elements
  [2, 1, 5, 1, 3, 2]

  Window 1: [2, 1, 5] = 8
  Window 2:    [1, 5, 1] = 7   ← slide: remove 2, add 1
  Window 3:       [5, 1, 3] = 9 ← slide: remove 1, add 3
  Window 4:          [1, 3, 2] = 6

  Answer: 9

  KEY INSIGHT: sum of window [i..i+k] = 
               sum of window [i-1..i+k-1] - arr[i-1] + arr[i+k]
  
  O(n) instead of O(n*k)!
```

```c
// C: maximum sum subarray of size k
int max_sum_window(int *arr, int n, int k) {
    if (n < k) return -1;

    // Compute sum of first window
    int window_sum = 0;
    for (int i = 0; i < k; i++) {
        window_sum += arr[i];
    }

    int max_sum = window_sum;

    // Slide the window forward
    for (int i = k; i < n; i++) {
        window_sum += arr[i];       // add new element
        window_sum -= arr[i - k];   // remove leftmost element
        if (window_sum > max_sum) {
            max_sum = window_sum;
        }
    }
    return max_sum;
}
```

```rust
fn max_sum_window(arr: &[i32], k: usize) -> Option<i32> {
    if arr.len() < k { return None; }

    // First window
    let mut window_sum: i32 = arr[..k].iter().sum();
    let mut max_sum = window_sum;

    // Slide
    for i in k..arr.len() {
        window_sum += arr[i];
        window_sum -= arr[i - k];
        max_sum = max_sum.max(window_sum);
    }
    Some(max_sum)
}
```

```go
func maxSumWindow(arr []int, k int) (int, bool) {
    if len(arr) < k {
        return 0, false
    }

    windowSum := 0
    for i := 0; i < k; i++ {
        windowSum += arr[i]
    }
    maxSum := windowSum

    for i := k; i < len(arr); i++ {
        windowSum += arr[i]
        windowSum -= arr[i-k]
        if windowSum > maxSum {
            maxSum = windowSum
        }
    }
    return maxSum, true
}
```

---

## 🔷 PART 6: Performance and Common Pitfalls

### 6.1 Off-By-One Errors (OBOE) — The Most Common Bug

```
OBOE TAXONOMY:

  ┌─────────────────────────────────────────────────────────┐
  │               OFF-BY-ONE REFERENCE CARD                 │
  ├─────────────────┬───────────────────────────────────────┤
  │ 0-indexed array │ Valid indices: 0 .. n-1               │
  │                 │ Loop: i < n   ← correct               │
  │                 │ Loop: i <= n  ← WRONG! accesses n     │
  │                 │ Loop: i < n-1 ← WRONG! misses last    │
  ├─────────────────┼───────────────────────────────────────┤
  │ Comparing pairs │ arr[i] vs arr[i+1]                    │
  │ (bubble sort)   │ Outer loop: i < n-1  ← correct        │
  │                 │ i < n → i+1 = n → OUT OF BOUNDS!      │
  ├─────────────────┼───────────────────────────────────────┤
  │ Reverse loop    │ for(i = n-1; i >= 0; i--)  ← correct  │
  │                 │ for(i = n; i > 0; i--)    ← WRONG!    │
  │                 │ for(i = n; i >= 0; i--)   ← WRONG if  │
  │                 │    i is unsigned! (wraps to MAX_UINT)  │
  └─────────────────┴───────────────────────────────────────┘
```

```c
// C: DANGEROUS reverse loop with unsigned index!
int arr[] = {1, 2, 3, 4, 5};
int n = 5;

// ❌ BUG: size_t is unsigned — (size_t)0 - 1 = SIZE_MAX!
for (size_t i = n - 1; i >= 0; i--) {  // infinite loop!
    printf("%d ", arr[i]);
}

// ✅ CORRECT: use signed int for reverse loops
for (int i = n - 1; i >= 0; i--) {
    printf("%d ", arr[i]);
}
```

```rust
// Rust prevents this at compile time with saturating arithmetic!
let arr = [1, 2, 3, 4, 5];

// Idiomatic reverse iteration — no index needed
for val in arr.iter().rev() {
    print!("{} ", val);
}

// If you need index:
for i in (0..arr.len()).rev() {
    print!("{} ", arr[i]);
}
// Rust's range (0..n).rev() is always correct — no OBOE possible
```

---

### 6.2 Loop-Invariant Code Motion (Optimization)

```
CONCEPT: "Don't compute the same thing inside a loop if it 
          doesn't change between iterations."

BEFORE (inefficient):
  for i in 0..n {
      let threshold = compute_threshold();  // computed n times!
      if data[i] > threshold { ... }
  }

AFTER (optimized):
  let threshold = compute_threshold();  // computed ONCE
  for i in 0..n {
      if data[i] > threshold { ... }
  }
```

```c
// C: cache strlen outside loop (classic C mistake)
char *str = "Hello, World";

// ❌ SLOW: strlen is O(n), called n times → O(n²) total
for (int i = 0; i < strlen(str); i++) { ... }

// ✅ FAST: compute length once → O(n) total
int len = strlen(str);
for (int i = 0; i < len; i++) { ... }
```

```rust
// Rust: iterators are lazy — computed once, not re-evaluated
let data = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
let threshold = 5;

// The filter closure captures threshold once
let count = data.iter()
    .filter(|&&x| x > threshold)
    .count();

println!("Elements above {}: {}", threshold, count);
```

```go
// Go: precompute expensive function calls before loops
rows := getRows()  // expensive DB call or something

// ❌ len() in Go is O(1), but getRows() might not be
for i := 0; i < len(getRows()); i++ { ... }  // calls getRows() each iteration!

// ✅ cache result
n := len(rows)
for i := 0; i < n; i++ {
    process(rows[i])
}
```

---

### 6.3 Break Early vs Exhaustive — When to Stop

```
STRATEGY DECISION:

  "Search" loops → break on first match (stop early)
  "Validate" loops → break on first FAILURE (fail fast)
  "Accumulate" loops → always run to end (must see all)
  "Transform" loops → always run to end (produce all outputs)

  ┌───────────────────────────────────────────────────────┐
  │  FAIL-FAST principle: Reject bad input EARLY.         │
  │  Don't validate 1000 elements if element 1 is wrong.  │
  └───────────────────────────────────────────────────────┘
```

```c
// C: validating all elements — fail fast with break
int is_all_positive(int *arr, int n) {
    for (int i = 0; i < n; i++) {
        if (arr[i] <= 0) {
            return 0;  // FAIL FAST — return immediately
        }
    }
    return 1;  // all passed
}
```

```rust
// Rust: iterators make this elegant
fn all_positive(arr: &[i32]) -> bool {
    arr.iter().all(|&x| x > 0)   // stops at first false
}

fn any_negative(arr: &[i32]) -> bool {
    arr.iter().any(|&x| x < 0)   // stops at first true
}

fn find_first_negative(arr: &[i32]) -> Option<i32> {
    arr.iter().copied().find(|&x| x < 0)  // stops at first match
}
```

```go
// Go: equivalent using a helper function
func allPositive(arr []int) bool {
    for _, v := range arr {
        if v <= 0 {
            return false  // fail fast
        }
    }
    return true
}
```

---

## 🔷 PART 7: Language-Specific Idioms and Differences

### 7.1 Side-by-Side Comparison

```
┌─────────────────────────────────────────────────────────────────────┐
│             LOOP FEATURE COMPARISON MATRIX                          │
├─────────────────────┬───────────────┬───────────────┬───────────────┤
│ Feature             │     C         │     Rust      │      Go       │
├─────────────────────┼───────────────┼───────────────┼───────────────┤
│ C-style for         │ ✅ for(;;)    │ ❌ (use range) │ ✅ for(;;)    │
│ while loop          │ ✅ while      │ ✅ while       │ for (no cond) │
│ do-while            │ ✅ do-while   │ ❌ use loop{}  │ ❌ use for{}  │
│ Infinite loop       │ while(1)      │ loop {}       │ for {}        │
│ for-each            │ ❌ manual     │ for x in xs   │ for _, v:=range│
│ Labeled break       │ ❌ (use goto) │ break 'label  │ break label   │
│ Labeled continue    │ ❌            │ continue 'lab │ continue label│
│ Loop return value   │ ❌            │ ✅ loop {}     │ ❌            │
│ Range step          │ i+=step       │ (0..n).step_by│ manual i+=step│
│ Parallel iter       │ manual        │ rayon crate   │ goroutines    │
│ Bounds checking     │ ❌ manual     │ ✅ always      │ ✅ slices      │
└─────────────────────┴───────────────┴───────────────┴───────────────┘
```

### 7.2 Rust's Unique `loop` → Value Trick

```rust
// Rust's loop can RETURN a value — like a function!
// Use this to avoid mutable variables outside the loop.

// ❌ Verbose (two separate concerns):
let mut result = None;
loop {
    let input = get_input();
    if is_valid(&input) {
        result = Some(input);
        break;
    }
}
let value = result.unwrap();

// ✅ Elegant (loop IS the expression):
let value = loop {
    let input = get_input();
    if is_valid(&input) {
        break input;  // 'input' becomes the loop's value!
    }
};
// value is directly the valid input — no Option wrapper needed
```

### 7.3 Go's `range` over Different Types

```go
package main

import "fmt"

func main() {
    // ── range over SLICE → (index, value)
    nums := []int{10, 20, 30}
    for i, v := range nums {
        fmt.Printf("[%d] = %d\n", i, v)
    }

    // ── range over MAP → (key, value) [UNORDERED!]
    scores := map[string]int{"Alice": 95, "Bob": 87}
    for name, score := range scores {
        fmt.Printf("%s: %d\n", name, score)
    }

    // ── range over STRING → (byte_index, rune/unicode_codepoint)
    for i, r := range "Hello, 世界" {
        fmt.Printf("%d: %c (U+%04X)\n", i, r, r)
    }

    // ── range over CHANNEL → receive until closed
    ch := make(chan int, 3)
    ch <- 1; ch <- 2; ch <- 3
    close(ch)
    for v := range ch {
        fmt.Println(v)
    }
}
```

---

## 🔷 PART 8: Real-World Use Case Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LOOP SELECTION BY USE CASE                           │
├────────────────────────────┬──────────────┬─────────────────────────────┤
│ Scenario                   │ Loop Type    │ Reason                      │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Retry HTTP request 3 times │ for (i<3)    │ Fixed max attempts          │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Wait for lock to release   │ while (busy) │ Unknown wait time           │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Read file line by line     │ while (EOF)  │ File length unknown         │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Menu → must show once      │ do-while     │ Show before asking "again?" │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ HTTP server accept loop    │ infinite     │ Runs until signal           │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Sum all elements in vec    │ for-each/    │ Visit every element once    │
│                            │ iterator     │                             │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Binary search              │ while(lo<=hi)│ Condition-based shrinking   │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Generate N fibonacci nums  │ for (i<N)    │ Known count                 │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Bubble sort pass           │ for + for    │ Nested, known bounds        │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ BFS/DFS (tree/graph)       │ while (queue │ Process until queue empty   │
│                            │ not empty)   │                             │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Rate limit: process only   │ for (i<limit)│ Hard cap per window         │
│ 100 req/sec                │              │                             │
├────────────────────────────┼──────────────┼─────────────────────────────┤
│ Drain a work queue         │ while(!empty)│ Empty when done             │
└────────────────────────────┴──────────────┴─────────────────────────────┘
```

---

## 🔷 PART 9: A Complete Real-World Example — Log Processor

This integrates everything: multiple loop types, early exit, iterators, and labeled breaks.

```c
// ─────────────────────────────────────────────────────────────
// C: Production-grade log file processor
// Demonstrates: for loop, while loop, sentinel, break, continue
// ─────────────────────────────────────────────────────────────
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define MAX_LINE   256
#define MAX_ERRORS 100

typedef struct {
    int line_num;
    char message[MAX_LINE];
} ErrorEntry;

int process_logs(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Cannot open: %s\n", filename);
        return -1;
    }

    char line[MAX_LINE];
    ErrorEntry errors[MAX_ERRORS];
    int error_count = 0;
    int line_num = 0;
    int total_lines = 0;

    // WHILE loop: read until EOF (unknown line count)
    while (fgets(line, sizeof(line), fp) != NULL) {
        line_num++;
        total_lines++;

        // Skip empty lines → continue
        if (line[0] == '\n' || line[0] == '\0') {
            continue;
        }

        // Skip comment lines → continue
        if (line[0] == '#') {
            continue;
        }

        // ERROR LIMIT reached → break (stop processing)
        if (error_count >= MAX_ERRORS) {
            fprintf(stderr, "Error limit reached. Stopping.\n");
            break;
        }

        // Check if line contains "ERROR"
        if (strstr(line, "ERROR") != NULL) {
            errors[error_count].line_num = line_num;
            strncpy(errors[error_count].message, line, MAX_LINE - 1);
            errors[error_count].message[MAX_LINE - 1] = '\0';
            error_count++;
        }
    }

    fclose(fp);

    // FOR loop: fixed count of collected errors
    printf("=== Error Report: %d errors in %d lines ===\n",
           error_count, total_lines);

    for (int i = 0; i < error_count; i++) {
        printf("[Line %d] %s", errors[i].line_num, errors[i].message);
    }

    return error_count;
}
```

```rust
// ─────────────────────────────────────────────────────────────
// RUST: Same log processor — idiomatic style
// ─────────────────────────────────────────────────────────────
use std::fs::File;
use std::io::{BufRead, BufReader};

const MAX_ERRORS: usize = 100;

struct ErrorEntry {
    line_num: usize,
    message: String,
}

fn process_logs(filename: &str) -> std::io::Result<Vec<ErrorEntry>> {
    let file = File::open(filename)?;
    let reader = BufReader::new(file);

    // Iterator chain — expressive and zero-cost
    let errors: Vec<ErrorEntry> = reader
        .lines()                                    // iterate lines
        .enumerate()                                // add line numbers
        .filter_map(|(i, line_result)| {            // handle errors
            let line = line_result.ok()?;           // skip IO errors
            Some((i + 1, line))
        })
        .filter(|(_, line)| {                       // skip comments/empty
            !line.is_empty() && !line.starts_with('#')
        })
        .filter(|(_, line)| line.contains("ERROR")) // only errors
        .take(MAX_ERRORS)                            // hard cap
        .map(|(num, msg)| ErrorEntry {
            line_num: num,
            message: msg,
        })
        .collect();

    println!("=== Error Report: {} errors ===", errors.len());
    for e in &errors {
        println!("[Line {}] {}", e.line_num, e.message);
    }

    Ok(errors)
}
```

```go
// ─────────────────────────────────────────────────────────────
// GO: Same log processor — Go idioms
// ─────────────────────────────────────────────────────────────
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

const maxErrors = 100

type ErrorEntry struct {
    LineNum int
    Message string
}

func processLogs(filename string) ([]ErrorEntry, error) {
    file, err := os.Open(filename)
    if err != nil {
        return nil, fmt.Errorf("open %s: %w", filename, err)
    }
    defer file.Close()

    var errors []ErrorEntry
    scanner := bufio.NewScanner(file)
    lineNum := 0

    // WHILE-style loop: scan until EOF
    for scanner.Scan() {
        lineNum++
        line := scanner.Text()

        // Skip empty and comment lines
        if line == "" || strings.HasPrefix(line, "#") {
            continue
        }

        // Enforce max error cap
        if len(errors) >= maxErrors {
            fmt.Fprintln(os.Stderr, "Max error limit reached.")
            break
        }

        if strings.Contains(line, "ERROR") {
            errors = append(errors, ErrorEntry{
                LineNum: lineNum,
                Message: line,
            })
        }
    }

    // FOR loop: iterate collected errors (known count)
    fmt.Printf("=== Error Report: %d errors in %d lines ===\n",
        len(errors), lineNum)

    for i, e := range errors {
        fmt.Printf("[%d] Line %d: %s\n", i+1, e.LineNum, e.Message)
    }

    return errors, scanner.Err()
}
```

---

## 🔷 PART 10: Psychological & Cognitive Principles for Mastery

```
┌─────────────────────────────────────────────────────────────────┐
│              DELIBERATE PRACTICE FRAMEWORK FOR LOOPS            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CHUNKING: Learn loop types as standalone "chunks" first.       │
│  Then combine chunks into nested patterns. Your brain forms     │
│  a single cognitive unit for "for-loop" after ~50 uses —       │
│  you stop thinking about its mechanics and just use it.         │
│                                                                 │
│  PATTERN MATCHING: The true DSA skill is not syntax —          │
│  it's instantly recognizing "this problem needs two-pointer"    │
│  or "this is a sliding window." Train this by solving 5+        │
│  problems of each pattern, not 1 problem of 20 patterns.        │
│                                                                 │
│  META-LEARNING: After solving each problem, ask:               │
│    1. Which loop type did I use? Was it the right one?         │
│    2. Can I reduce the nesting depth?                           │
│    3. Did I compute anything wastefully inside the loop?        │
│    4. What is the time complexity? Can I prove it?              │
│                                                                 │
│  FLOW STATE: Loops are mechanical but complexity is creative.   │
│  The choice of which loop to use is intuition — built by        │
│  thousands of deliberate repetitions.                           │
│                                                                 │
│  "Expert programmers don't think about loop syntax.             │
│   They think about the SHAPE of the iteration."                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔷 Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════╗
║              LOOP SELECTION QUICK REFERENCE                   ║
╠═══════════════════════╦═══════════════════════════════════════╣
║  SITUATION            ║  LOOP TO USE                          ║
╠═══════════════════════╬═══════════════════════════════════════╣
║ Known count           ║ for (i = 0; i < n; i++)               ║
║ Unknown count         ║ while (condition)                     ║
║ Run at least once     ║ do-while (C) / loop+break (Rust/Go)   ║
║ Collection traversal  ║ for-each / range                      ║
║ Infinite service      ║ while(1) / loop{} / for{}             ║
║ Exit nested loops     ║ labeled break (Rust 'l / Go l:)       ║
║ Skip bad items        ║ continue                              ║
║ Stop on first match   ║ break / .find() / return              ║
║ Count backwards       ║ for (i = n-1; i >= 0; i--)           ║
║                       ║ (use SIGNED int — never unsigned!)    ║
╚═══════════════════════╩═══════════════════════════════════════╝

COMPLEXITY CHEATSHEET:
  1 loop = O(n)
  2 loops (nested) = O(n²)
  2 loops (sequential) = O(n + m)
  loop with bisection = O(log n)
  loop + inner bisection = O(n log n)

GOLDEN RULES:
  ① Never compute inside a loop what can be computed outside
  ② Break early when you have your answer
  ③ Prefer iterators over index arithmetic when possible
  ④ Always check: can the loop be infinite? Prove it terminates.
  ⑤ Off-by-one: draw it out. Trace 0, 1, n-1, n manually.
```

---

This guide covers the complete foundation of loop selection. The next level of mastery is applying these patterns to sorting algorithms, graph traversal, dynamic programming, and concurrent iteration — all of which are built on exactly these primitives you've just mastered. Each DSA algorithm you study will call back to one or more of these loop shapes. Recognize the shape, and the algorithm reveals itself.

# 🔁 The Ultimate Guide to Loops — Rust, Go & C

> *"Repetition is the mother of mastery. Loops are repetition distilled into logic."*

---

## 📌 TABLE OF CONTENTS

```
1.  What Is a Loop? — The Core Mental Model
2.  Why Loops Exist — Real World Motivation
3.  Anatomy of a Loop
4.  Types of Loops
    ├── 4.1 The `for` Loop
    ├── 4.2 The `while` Loop
    ├── 4.3 The `do-while` Loop (C) / Emulation (Rust, Go)
    ├── 4.4 The Infinite Loop
    └── 4.5 Nested Loops
5.  Loop Control Statements
    ├── 5.1 break
    ├── 5.2 continue
    └── 5.3 Labels (Named Loops)
6.  Range-Based & Iterator Loops
7.  Loop Patterns — Expert Mental Models
    ├── 7.1 Accumulation Pattern
    ├── 7.2 Search Pattern
    ├── 7.3 Counting Pattern
    ├── 7.4 Two-Pointer Pattern
    └── 7.5 Sliding Window Pattern
8.  Complexity Analysis of Loops
9.  Loop Optimizations
10. Decision Tree — Which Loop to Use?
11. Real-World Use Cases
12. Psychological Framework — How Experts Think About Loops
```

---

## 1. 🧠 What Is a Loop? — The Core Mental Model

### Plain English First

> A **loop** is a mechanism that tells the computer: *"Repeat this block of instructions until a certain condition is met (or forever)."*

Before writing a single line of code, internalize this mental model:

```
A loop has THREE fundamental questions:
┌─────────────────────────────────────────────────────┐
│  1. WHERE do I start?       → Initialization        │
│  2. WHEN do I stop?         → Condition             │
│  3. HOW do I move forward?  → Update / Increment    │
└─────────────────────────────────────────────────────┘
```

If any of these three is missing or wrong — your loop either **never runs**, **runs forever**, or **produces wrong results**.

### Real World Analogy

Think of a **factory conveyor belt**:

```
Raw Material                    Finished Product
    │                               │
    ▼                               ▼
┌───────────────────────────────────────────┐
│  [Item 1] → [Process] → [Output]          │
│  [Item 2] → [Process] → [Output]          │
│  [Item 3] → [Process] → [Output]          │
│  ...                                      │
│  [Last Item] → [Process] → STOP BELT      │
└───────────────────────────────────────────┘

→ The belt STARTS when items arrive (initialization)
→ The belt STOPS when no more items (condition)
→ Each cycle MOVES to the next item (update)
```

---

## 2. 🌍 Why Loops Exist — Real World Motivation

Without loops, to print numbers 1–1000, you'd write 1000 print statements. That's absurd. Loops give you:

```
┌──────────────────────────────────────────────────────────┐
│  USE CASE               │  WITHOUT LOOP  │  WITH LOOP    │
│─────────────────────────│────────────────│───────────────│
│  Print 1 to 1,000,000   │  1M lines      │  3 lines      │
│  Search in a database   │  Impossible    │  Trivial      │
│  Process each pixel     │  Impossible    │  Nested loop  │
│  Retry network request  │  Manual        │  while loop   │
│  Build a game loop      │  Impossible    │  Infinite loop│
└──────────────────────────────────────────────────────────┘
```

---

## 3. 🔬 Anatomy of a Loop — Every Part Explained

```
         ┌─────────── INITIALIZATION ────────────┐
         │  Set starting state before loop begins │
         │  e.g., i = 0, sum = 0                 │
         └───────────────────────────────────────┘
                           │
                           ▼
         ┌─────────── CONDITION CHECK ───────────┐
         │  Is the loop allowed to continue?      │◄──────┐
         │  e.g., i < 10, sum < 100              │       │
         └───────────────────────────────────────┘       │
                  │               │                       │
               TRUE             FALSE                     │
                  │               │                       │
                  ▼               ▼                       │
         ┌──────────────┐   ┌──────────┐                  │
         │  LOOP BODY   │   │  EXIT    │                  │
         │  (your code) │   │  (done!) │                  │
         └──────────────┘   └──────────┘                  │
                  │                                        │
                  ▼                                        │
         ┌─────────── UPDATE ────────────────────┐        │
         │  Advance toward termination condition  │────────┘
         │  e.g., i++, i += 2, i *= 2            │
         └───────────────────────────────────────┘
```

---

## 4. 📦 Types of Loops

---

### 4.1 The `for` Loop

**What it is:** The most structured loop. You know (or can express) the start, condition, and update all in one place.

**When to use:** When you know the number of iterations, OR when iterating over a range/collection.

#### 🔷 General Flow

```
for (init; condition; update) {
    body
}

Step-by-step execution trace for: for(i=0; i<3; i++)
┌────────┬────────────┬───────┬────────┐
│  Step  │  Action    │   i   │  Body  │
├────────┼────────────┼───────┼────────┤
│   1    │  init      │   0   │   -    │
│   2    │  check 0<3 │   0   │  runs  │
│   3    │  update    │   1   │   -    │
│   4    │  check 1<3 │   1   │  runs  │
│   5    │  update    │   2   │   -    │
│   6    │  check 2<3 │   2   │  runs  │
│   7    │  update    │   3   │   -    │
│   8    │  check 3<3 │   3   │  EXIT  │
└────────┴────────────┴───────┴────────┘
```

#### 🔷 C Implementation

```c
#include <stdio.h>

int main() {
    // Classic for loop: sum 1 to N
    int n = 10;
    int sum = 0;

    for (int i = 1; i <= n; i++) {
        sum += i;
    }
    // sum = 55

    printf("Sum 1 to %d = %d\n", n, sum);

    // --- Iterating over an array ---
    int arr[] = {10, 20, 30, 40, 50};
    int len = sizeof(arr) / sizeof(arr[0]); // sizeof trick to get length

    for (int i = 0; i < len; i++) {
        printf("arr[%d] = %d\n", i, arr[i]);
    }

    // --- Decrement loop (reverse traversal) ---
    for (int i = len - 1; i >= 0; i--) {
        printf("%d ", arr[i]); // 50 40 30 20 10
    }

    // --- Step-by-2 loop (even numbers) ---
    for (int i = 0; i <= 20; i += 2) {
        printf("%d ", i); // 0 2 4 6 8 10 12 14 16 18 20
    }

    // --- Multiple variables in for loop ---
    for (int i = 0, j = 10; i < j; i++, j--) {
        printf("i=%d j=%d\n", i, j);
        // converging from both ends
    }

    return 0;
}
```

#### 🔷 Go Implementation

```go
package main

import "fmt"

func main() {
    // Go only has one loop keyword: `for`
    // It serves as for, while, and do-while

    // Classic C-style for loop
    sum := 0
    for i := 1; i <= 10; i++ {
        sum += i
    }
    fmt.Println("Sum:", sum) // 55

    // Iterating over a slice (Go's dynamic array)
    arr := []int{10, 20, 30, 40, 50}

    // Index-only loop
    for i := 0; i < len(arr); i++ {
        fmt.Printf("arr[%d] = %d\n", i, arr[i])
    }

    // Range-based loop (idiomatic Go)
    // range returns (index, value) pairs
    for i, v := range arr {
        fmt.Printf("Index: %d, Value: %d\n", i, v)
    }

    // When you only need values, discard index with _
    for _, v := range arr {
        fmt.Println(v)
    }

    // When you only need indices
    for i := range arr {
        fmt.Println(i)
    }
}
```

> **Key Insight — Go:** Go's `for` is the **only** loop construct. It's intentional — the designers of Go wanted simplicity. The `for` loop in Go can behave like C's `for`, `while`, or even `do-while` based on how you write it.

#### 🔷 Rust Implementation

```rust
fn main() {
    // Rust: for loop works with iterators/ranges

    // Range loop: 1..=10 means 1 to 10 inclusive
    // 1..10 means 1 to 9 (exclusive end)
    let mut sum = 0;
    for i in 1..=10 {
        sum += i;
    }
    println!("Sum: {}", sum); // 55

    // Array iteration
    let arr = [10, 20, 30, 40, 50];

    // By value (copies the element)
    for val in arr {
        println!("{}", val);
    }

    // By reference (borrows each element)
    for val in &arr {
        println!("{}", val);
    }

    // With index using enumerate()
    // enumerate() wraps each element as (index, value)
    for (i, val) in arr.iter().enumerate() {
        println!("arr[{}] = {}", i, val);
    }

    // Reverse iteration
    for val in arr.iter().rev() {
        println!("{}", val); // 50 40 30 20 10
    }

    // Step iteration using step_by()
    for i in (0..=20).step_by(2) {
        print!("{} ", i); // 0 2 4 6 8 ... 20
    }
}
```

> **Key Insight — Rust:** Rust's `for` loop works exclusively with **iterators**. A range like `1..10` is itself an iterator. This design is deeply intentional — Rust's iterator model is zero-cost (the compiler optimizes them to raw loops), and it prevents off-by-one errors that plague C loops.

---

### 4.2 The `while` Loop

**What it is:** Loop that keeps running **as long as** a condition is `true`. No built-in init/update — you manage those yourself.

**When to use:** When you DON'T know exactly how many iterations you'll need. Common in: waiting for user input, reading until end-of-file, retrying until success.

#### 🔷 Flow Diagram

```
              ┌─────────────────────────┐
              │  Setup state before     │
              │  entering loop          │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
         ┌───►│   CHECK CONDITION       │
         │    └────────────┬────────────┘
         │           ┌─────┴─────┐
         │         TRUE        FALSE
         │           │           │
         │           ▼           ▼
         │    ┌──────────┐   ┌───────┐
         │    │   BODY   │   │  END  │
         │    └──────────┘   └───────┘
         │           │
         │           ▼
         │    ┌──────────────────────┐
         └────│  UPDATE (manual!)    │
              │  (you must do this   │
              │   or loop = infinite)│
              └──────────────────────┘
```

#### 🔷 C Implementation

```c
#include <stdio.h>

int main() {
    // Basic while: count down from 5
    int count = 5;
    while (count > 0) {
        printf("%d ", count); // 5 4 3 2 1
        count--;              // <-- Manual update. Forget this = infinite loop!
    }

    // Real-world: Read until sentinel value
    // (Simulated: process numbers until -1)
    int input[] = {10, 20, 35, -1}; // -1 is our "stop" signal (sentinel)
    int idx = 0;
    int total = 0;

    while (input[idx] != -1) {
        total += input[idx];
        idx++;
    }
    printf("\nTotal: %d\n", total); // 65

    // Real-world: Binary search (manual iteration)
    int sorted[] = {1, 3, 7, 12, 19, 24, 31};
    int target = 19;
    int lo = 0, hi = 6;
    int result = -1;

    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2; // safe midpoint (avoids overflow)
        if (sorted[mid] == target) {
            result = mid;
            break;
        } else if (sorted[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    printf("Found at index: %d\n", result); // 4

    return 0;
}
```

#### 🔷 Go Implementation

```go
package main

import "fmt"

func main() {
    // Go's while loop is just: for condition { }
    // No init, no update clause — it's a while!

    count := 5
    for count > 0 {
        fmt.Print(count, " ") // 5 4 3 2 1
        count--
    }
    fmt.Println()

    // Real-world: Collatz Conjecture
    // Keep halving (even) or 3n+1 (odd) until we reach 1
    // We don't know how many steps this takes!
    n := 27
    steps := 0
    for n != 1 {
        if n%2 == 0 {
            n /= 2
        } else {
            n = 3*n + 1
        }
        steps++
    }
    fmt.Printf("Steps to reach 1: %d\n", steps) // 111

    // Real-world: Retry loop (network/IO operations)
    maxRetries := 3
    attempt := 0
    success := false

    for attempt < maxRetries && !success {
        // Simulate a connection attempt
        attempt++
        fmt.Printf("Attempt %d...\n", attempt)
        if attempt == 3 { // Succeeds on 3rd try
            success = true
        }
    }
    fmt.Println("Success:", success)
}
```

#### 🔷 Rust Implementation

```rust
fn main() {
    // Rust while loop
    let mut count = 5;
    while count > 0 {
        print!("{} ", count); // 5 4 3 2 1
        count -= 1;
    }
    println!();

    // Real-world: Newton's method for square root approximation
    // Keep iterating until the guess is "good enough"
    let target = 2.0_f64;
    let mut guess = 1.0_f64;
    let epsilon = 1e-10; // our "good enough" threshold

    while (guess * guess - target).abs() > epsilon {
        guess = (guess + target / guess) / 2.0; // Newton's formula
    }
    println!("√2 ≈ {:.10}", guess); // 1.4142135624

    // while let: Loop while pattern matching succeeds
    // Very Rust-idiomatic for handling Option<T>
    let mut stack = vec![1, 2, 3, 4, 5];

    // stack.pop() returns Some(value) until empty, then None
    while let Some(top) = stack.pop() {
        print!("{} ", top); // 5 4 3 2 1
    }
    println!();
}
```

> **Rust Exclusive — `while let`:** This is pattern-matching inside a loop condition. It keeps looping as long as the pattern matches. This is deeply useful when working with `Option<T>` (Rust's null-safety type) and `Result<T, E>`.

---

### 4.3 The `do-while` Loop — Execute First, Check Later

**What it is:** The body executes **at least once**, THEN the condition is checked.

**When to use:** Menu-driven programs, input validation (ask first, then validate), retry-with-initial-attempt.

#### 🔷 Flow Comparison

```
  while loop:                    do-while loop:
  ─────────────                  ──────────────
  CHECK condition                EXECUTE body
       │                              │
    FALSE → EXIT               CHECK condition
    TRUE  → BODY                    │
       │                         FALSE → EXIT
  UPDATE                         TRUE  → BODY (again)
       │                              │
  back to CHECK                  UPDATE
                                       │
                                  back to CHECK

KEY DIFFERENCE:
  while:    body may NEVER execute (if condition false initially)
  do-while: body ALWAYS executes at least ONCE
```

#### 🔷 C Implementation

```c
#include <stdio.h>

int main() {
    // Classic do-while: menu prompt
    int choice;

    // Without do-while, you'd need to prime the loop awkwardly.
    // do-while is clean: show menu, then validate, loop if invalid.
    do {
        printf("\n--- MENU ---\n");
        printf("1. Option A\n");
        printf("2. Option B\n");
        printf("3. Exit\n");
        printf("Enter choice: ");

        // For demo, simulate input
        static int inputs[] = {5, 2}; // 5 is invalid, 2 is valid
        static int idx = 0;
        choice = inputs[idx++];
        printf("%d\n", choice);

    } while (choice < 1 || choice > 3); // Repeat if invalid

    printf("You chose: %d\n", choice); // 2

    // do-while: Execute exactly once even when condition is false
    int x = 10;
    do {
        printf("This prints ONCE even though x > 5\n");
        x++;
    } while (x < 5); // Condition is false from the start

    // Contrast: while loop with same condition
    x = 10;
    while (x < 5) {
        printf("This NEVER prints\n"); // Skipped entirely
    }

    return 0;
}
```

#### 🔷 Go — Emulating do-while

Go has no `do-while`. You emulate it using an infinite loop with a break:

```go
package main

import "fmt"

func main() {
    // Pattern 1: for { ... ; if !cond { break } }
    x := 0
    for {
        fmt.Println("Body executes:", x)
        x++
        if x >= 3 {
            break // Exit condition at the END
        }
    }
    // Output: 0, 1, 2 — runs 3 times

    // Pattern 2: Using a bool flag
    validated := false
    attempt := 0
    for !validated {
        attempt++
        fmt.Printf("Attempt %d\n", attempt)
        if attempt >= 2 {
            validated = true
        }
    }
}
```

#### 🔷 Rust — Emulating do-while

```rust
fn main() {
    // Rust has no do-while but `loop` + `break` is idiomatic

    // Pattern: loop { body; if !condition { break; } }
    let mut x = 0;
    loop {
        println!("x = {}", x); // Executes at least once
        x += 1;
        if x >= 3 {
            break;
        }
    }

    // Rust loop can RETURN a value — unique feature!
    let mut counter = 0;
    let result = loop {
        counter += 1;
        if counter == 10 {
            break counter * 2; // loop expression evaluates to this
        }
    };
    println!("Result: {}", result); // 20
    // This is ONLY possible in Rust. Loops are expressions here.
}
```

> **Rust Unique Power:** `loop` is an **expression** that can return a value via `break value`. This is used extensively in Rust programs to initialize variables from retry logic.

---

### 4.4 The Infinite Loop

**What it is:** A loop with no terminating condition — it runs forever until explicitly broken.

**When to use:** Game loops, server/daemon processes, event listeners, REPLs (Read-Eval-Print Loops), embedded system main loops.

#### 🔷 Flow

```
           ┌──────────────────────────────┐
           │        INFINITE LOOP         │
           │                              │
           │  ┌──────────────────────┐    │
           │  │  BODY                │    │
           │  │  ┌────────────────┐  │    │
           │  │  │  if condition  │  │    │
           │  │  │    break ──────┼──┼────┼──► EXIT
           │  │  └────────────────┘  │    │
           │  └──────────┬───────────┘    │
           │             │ (loop forever) │
           └─────────────┘────────────────┘
```

#### 🔷 C Implementation

```c
#include <stdio.h>
#include <stdbool.h>

int main() {
    // C infinite loop: while(1) or for(;;)
    int tick = 0;

    // Server simulation: process requests forever
    while (1) {  // or: for(;;) — both are idiomatic C
        tick++;
        printf("Processing request #%d\n", tick);

        // In real code, this could be:
        // - accept() for network server
        // - read() for event loop
        // - poll() for GUI event handling

        if (tick >= 5) {
            printf("Shutting down.\n");
            break; // Controlled exit
        }
    }

    return 0;
}
```

#### 🔷 Go Implementation

```go
package main

import "fmt"

func main() {
    // Go infinite loop
    tick := 0

    for { // No condition = infinite loop in Go
        tick++
        fmt.Printf("Server tick #%d\n", tick)

        if tick >= 5 {
            fmt.Println("Shutdown signal received.")
            break
        }
    }

    // Real-world: Event loop pattern
    events := []string{"click", "scroll", "keypress", "quit"}
    i := 0
    for {
        event := events[i]
        i++
        fmt.Println("Handling event:", event)
        if event == "quit" {
            break
        }
    }
}
```

#### 🔷 Rust Implementation

```rust
fn main() {
    // Rust's `loop` keyword = infinite loop
    let mut tick = 0;

    loop {
        tick += 1;
        println!("Server tick #{}", tick);

        if tick >= 5 {
            println!("Shutdown.");
            break;
        }
    }

    // Real embedded systems pattern:
    // The main() of many Rust embedded programs is literally:
    //   loop { read_sensor(); process(); transmit(); }
    // because microcontrollers run forever.
}
```

---

### 4.5 Nested Loops — Loops Inside Loops

**What it is:** One loop placed inside another. The inner loop completes ALL its iterations for EACH single iteration of the outer loop.

**When to use:** 2D data structures (matrices, grids, images), combinations/permutations, pattern printing, multi-dimensional traversal.

#### 🔷 Execution Model

```
Outer loop i: 0, 1, 2
Inner loop j: 0, 1, 2

Execution trace:
┌──────────────────────────────────────────┐
│  i=0 │ j=0 → (0,0)                       │
│      │ j=1 → (0,1)                       │
│      │ j=2 → (0,2)   ← inner completes   │
│  i=1 │ j=0 → (1,0)                       │
│      │ j=1 → (1,1)                       │
│      │ j=2 → (1,2)   ← inner completes   │
│  i=2 │ j=0 → (2,0)                       │
│      │ j=1 → (2,1)                       │
│      │ j=2 → (2,2)   ← inner completes   │
└──────────────────────────────────────────┘
Total iterations = 3 × 3 = 9
For N×M nested loops → O(N×M) complexity
```

#### 🔷 C Implementation

```c
#include <stdio.h>

int main() {
    int rows = 5;

    // Pattern printing: right triangle of stars
    for (int i = 1; i <= rows; i++) {        // outer: controls row
        for (int j = 1; j <= i; j++) {       // inner: controls column
            printf("* ");
        }
        printf("\n");
    }
    /*
    *
    * *
    * * *
    * * * *
    * * * * *
    */

    // Matrix multiplication (classic O(n³) nested loop)
    int A[2][2] = {{1, 2}, {3, 4}};
    int B[2][2] = {{5, 6}, {7, 8}};
    int C[2][2] = {0};
    int n = 2;

    for (int i = 0; i < n; i++) {         // rows of A
        for (int j = 0; j < n; j++) {     // cols of B
            for (int k = 0; k < n; k++) { // inner dimension
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
    // C = {{19, 22}, {43, 50}}
    printf("C[0][0]=%d C[0][1]=%d\n", C[0][0], C[0][1]);
    printf("C[1][0]=%d C[1][1]=%d\n", C[1][0], C[1][1]);

    return 0;
}
```

#### 🔷 Go Implementation

```go
package main

import "fmt"

func main() {
    // 2D grid traversal
    grid := [][]int{
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9},
    }

    for i, row := range grid {
        for j, val := range row {
            fmt.Printf("grid[%d][%d] = %d\n", i, j, val)
        }
    }

    // Finding max element in 2D grid
    max := grid[0][0]
    for _, row := range grid {
        for _, val := range row {
            if val > max {
                max = val
            }
        }
    }
    fmt.Println("Max:", max) // 9
}
```

#### 🔷 Rust Implementation

```rust
fn main() {
    // Nested range loops
    let rows = 4;
    let cols = 4;

    // Print multiplication table
    for i in 1..=rows {
        for j in 1..=cols {
            print!("{:4}", i * j); // :4 = pad to 4 chars wide
        }
        println!();
    }
    /*
       1   2   3   4
       2   4   6   8
       3   6   9  12
       4   8  12  16
    */

    // 2D Vec traversal
    let matrix = vec![
        vec![1, 2, 3],
        vec![4, 5, 6],
        vec![7, 8, 9],
    ];

    // Sum of all elements
    let sum: i32 = matrix.iter()
        .flat_map(|row| row.iter()) // flatten 2D to 1D iterator
        .sum();
    println!("Sum: {}", sum); // 45
}
```

---

## 5. 🎮 Loop Control Statements

### 5.1 `break` — Escape the Loop

**What it is:** Immediately exits the innermost loop when executed.

**When to use:** Found what you're looking for, error encountered, user requested stop.

```
Loop execution with break:

  Iteration 1: normal
  Iteration 2: normal
  Iteration 3: break hit → ─────────────────────► EXITS LOOP
  Iteration 4: (NEVER REACHED)
  Iteration 5: (NEVER REACHED)
```

#### All Three Languages

```c
// C: break exits the innermost loop
for (int i = 0; i < 10; i++) {
    if (i == 5) break; // stops at 5
    printf("%d ", i); // 0 1 2 3 4
}
```

```go
// Go: same behavior
for i := 0; i < 10; i++ {
    if i == 5 {
        break
    }
    fmt.Print(i, " ") // 0 1 2 3 4
}
```

```rust
// Rust: same behavior
for i in 0..10 {
    if i == 5 { break; }
    print!("{} ", i); // 0 1 2 3 4
}
```

---

### 5.2 `continue` — Skip This Iteration

**What it is:** Skips the REST of the current iteration and jumps to the UPDATE step (for loops) or condition check (while loops).

**When to use:** Skip invalid/irrelevant items, filter data inline.

```
Loop execution with continue at i=3:

  Iteration 1: runs fully
  Iteration 2: runs fully
  Iteration 3: hits continue → skips rest → goes to UPDATE (i=4)
  Iteration 4: runs fully
  ...

┌─────────────────────────────────────────────┐
│  for (int i=0; i<6; i++) {                  │
│      if (i == 3) continue; // skip 3        │
│      print(i);                              │
│  }                                          │
│  Output: 0 1 2 4 5   (3 is skipped!)        │
└─────────────────────────────────────────────┘
```

#### All Three Languages

```c
// C: Print only even numbers
for (int i = 0; i < 10; i++) {
    if (i % 2 != 0) continue; // skip odd numbers
    printf("%d ", i); // 0 2 4 6 8
}
```

```go
// Go: Skip negative numbers in a slice
nums := []int{3, -1, 7, -4, 2}
for _, v := range nums {
    if v < 0 {
        continue // Skip negatives
    }
    fmt.Print(v, " ") // 3 7 2
}
```

```rust
// Rust: Filter and process
for i in 0..10 {
    if i % 3 == 0 { continue; } // skip multiples of 3
    print!("{} ", i); // 1 2 4 5 7 8
}
```

---

### 5.3 Labels — Breaking/Continuing Outer Loops

**What it is:** When you have nested loops, `break` only exits the INNERMOST loop. Labels let you break/continue an OUTER loop directly.

**When to use:** Matrix search where you want to exit ALL loops once target is found.

```
Nested loop without label:
  Outer loop i=0:
    Inner loop j: 0, 1, 2, break(j=2)  ← only inner exits
  Outer loop i=1:        ← outer continues!
    Inner loop j: ...

Nested loop WITH label:
  OUTER: for i ...
    for j ...
      break OUTER;   ← exits BOTH loops at once!
```

#### C — Uses `goto` (the traditional way)

```c
#include <stdio.h>

int main() {
    // C doesn't have labeled loops.
    // Use goto (carefully!) or a flag variable.

    // Method 1: flag variable (clean, recommended)
    int matrix[3][3] = {{1,2,3},{4,5,6},{7,8,9}};
    int target = 5;
    int found = 0;
    int fi = -1, fj = -1;

    for (int i = 0; i < 3 && !found; i++) {
        for (int j = 0; j < 3; j++) {
            if (matrix[i][j] == target) {
                fi = i; fj = j;
                found = 1;
                break; // exits inner, flag stops outer
            }
        }
    }

    if (found) printf("Found at (%d,%d)\n", fi, fj); // (1,1)

    // Method 2: goto (valid in C, but use with discipline)
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            if (matrix[i][j] == 5) {
                printf("Found via goto at (%d,%d)\n", i, j);
                goto done; // jumps to label 'done'
            }
        }
    }
    done: // label
    printf("Search complete.\n");

    return 0;
}
```

#### Go — First-class labeled loops

```go
package main

import "fmt"

func main() {
    matrix := [][]int{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}
    target := 5

// Label is placed BEFORE the loop it refers to
OUTER:
    for i, row := range matrix {
        for j, val := range row {
            if val == target {
                fmt.Printf("Found %d at (%d,%d)\n", target, i, j)
                break OUTER // Exits BOTH loops!
            }
        }
    }
    fmt.Println("Search complete.")

    // continue with label: skip rest of outer iteration
LOOP:
    for i := 0; i < 3; i++ {
        for j := 0; j < 3; j++ {
            if j == 1 {
                continue LOOP // skip to next i iteration
            }
            fmt.Printf("(%d,%d) ", i, j)
        }
    }
    // Output: (0,0) (1,0) (2,0)
}
```

#### Rust — Labeled loops with `'label:`

```rust
fn main() {
    let matrix = vec![vec![1,2,3], vec![4,5,6], vec![7,8,9]];
    let target = 5;

    // Rust label syntax: 'name_with_apostrophe:
    'outer: for (i, row) in matrix.iter().enumerate() {
        for (j, &val) in row.iter().enumerate() {
            if val == target {
                println!("Found {} at ({},{})", target, i, j);
                break 'outer; // Break the outer loop
            }
        }
    }
    println!("Done.");

    // Rust: loop label can also return a value!
    let result = 'search: loop {
        for i in 0..10 {
            if i * i > 50 {
                break 'search i; // Return 'i' from the labeled loop
            }
        }
        break 'search -1; // Default if not found
    };
    println!("First i where i²>50: {}", result); // 8
}
```

---

## 6. 🔄 Range-Based & Iterator Loops (Deep Dive)

### What is an Iterator?

> An **iterator** is an object that produces a sequence of values one at a time. Think of it as a "lazy" sequence — it only computes the next value when you ask.

```
Collection: [10, 20, 30, 40, 50]
                │
        ┌───────▼────────┐
        │   Iterator     │
        │  ┌───────────┐ │
        │  │  cursor ──┼─┼──► points to current item
        │  └───────────┘ │
        │  .next()       │──► returns next item, advances cursor
        │  .has_more()   │──► checks if more items exist
        └────────────────┘

Each call to .next():
  call 1 → Some(10), cursor → 1
  call 2 → Some(20), cursor → 2
  call 3 → Some(30), cursor → 3
  call 4 → Some(40), cursor → 4
  call 5 → Some(50), cursor → 5
  call 6 → None (exhausted)
```

#### 🔷 Rust — Iterator Chaining (Powerful!)

```rust
fn main() {
    let numbers = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

    // map: transform each element
    // filter: keep only elements matching predicate
    // sum: reduce to single value
    let result: i32 = numbers.iter()
        .filter(|&&x| x % 2 == 0)  // keep evens: [2,4,6,8,10]
        .map(|&x| x * x)             // square them: [4,16,36,64,100]
        .sum();                       // add up: 220

    println!("Sum of squares of evens: {}", result); // 220

    // Key: This compiles to a single loop under the hood!
    // No intermediate vectors are created.
    // This is "zero-cost abstraction."

    // Equivalent manual loop (what the compiler generates):
    let mut manual_result = 0;
    for &x in &numbers {
        if x % 2 == 0 {
            manual_result += x * x;
        }
    }
    println!("Manual: {}", manual_result); // 220 — identical!

    // collect(): materialize iterator into a collection
    let squares: Vec<i32> = (1..=5).map(|x| x * x).collect();
    println!("{:?}", squares); // [1, 4, 9, 16, 25]

    // zip: combine two iterators element-by-element
    let names = vec!["Alice", "Bob", "Carol"];
    let scores = vec![95, 87, 92];
    for (name, score) in names.iter().zip(scores.iter()) {
        println!("{}: {}", name, score);
    }

    // take(n): only take first n items from (potentially infinite) iterator
    let first_five: Vec<u64> = (0..).take(5).collect(); // 0..infinity, take 5
    println!("{:?}", first_five); // [0, 1, 2, 3, 4]
}
```

#### 🔷 Go — Range over Different Types

```go
package main

import "fmt"

func main() {
    // range over slice
    fruits := []string{"apple", "banana", "cherry"}
    for i, f := range fruits {
        fmt.Printf("%d: %s\n", i, f)
    }

    // range over map (unordered!)
    // Important: Go maps have NO guaranteed iteration order
    ages := map[string]int{"Alice": 30, "Bob": 25, "Carol": 35}
    for name, age := range ages {
        fmt.Printf("%s is %d\n", name, age)
    }

    // range over string (iterates over RUNES, not bytes!)
    // A rune is a Unicode code point
    word := "Hello, 世界" // contains multi-byte UTF-8 characters
    for i, r := range word {
        fmt.Printf("index %d: %c (rune %d)\n", i, r, r)
    }
    // Notice: index jumps are non-uniform for multi-byte chars

    // range over channel (advanced: receives until channel closed)
    ch := make(chan int, 3)
    ch <- 10
    ch <- 20
    ch <- 30
    close(ch)

    for val := range ch { // receives until channel is drained and closed
        fmt.Println(val) // 10 20 30
    }
}
```

---

## 7. 🧩 Loop Patterns — Expert Mental Models

### 7.1 Accumulation Pattern

**Problem:** Aggregate all elements into a single result (sum, product, string concat, max, min).

```
Input: [3, 1, 4, 1, 5, 9, 2]
         │
         ▼
┌─────────────────────────────────────────┐
│  accumulator = identity_value           │
│  (0 for sum, 1 for product, "" for str) │
│                                         │
│  for each element:                      │
│      accumulator = combine(acc, elem)   │
│                                         │
│  return accumulator                     │
└─────────────────────────────────────────┘
         │
         ▼
Output: single value
```

```rust
fn main() {
    let data = vec![3, 1, 4, 1, 5, 9, 2];

    // Sum
    let sum: i32 = data.iter().sum();

    // Manual accumulation
    let mut product = 1i32;
    for &x in &data {
        product *= x;
    }

    // Max
    let max = data.iter().max().unwrap();

    // Min
    let min = data.iter().min().unwrap();

    println!("Sum={} Product={} Max={} Min={}", sum, product, max, min);
    // Sum=25 Product=1080 Max=9 Min=1
}
```

---

### 7.2 Search Pattern

**Problem:** Find a target element in a collection.

```
Linear Search:
  Check element 0 → match? → yes → return, no → continue
  Check element 1 → match? → ...
  ...
  Check element n-1 → match? → yes → return, no → not found

Time: O(n) worst case

Binary Search (requires SORTED data):
  ┌──────────────────────────────────────────────┐
  │  lo=0, hi=n-1                                │
  │  while lo <= hi:                             │
  │      mid = (lo+hi)/2                         │
  │      if arr[mid] == target → FOUND           │
  │      if arr[mid] < target  → lo = mid+1      │
  │      if arr[mid] > target  → hi = mid-1      │
  └──────────────────────────────────────────────┘

Time: O(log n) — halves search space each step
```

```c
// C: Linear search
int linear_search(int arr[], int n, int target) {
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) return i;
    }
    return -1; // not found
}

// C: Binary search
int binary_search(int arr[], int n, int target) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2; // prevents integer overflow
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}
```

---

### 7.3 Two-Pointer Pattern

**What it is:** Use TWO index variables (pointers), typically starting from opposite ends or both from the start, moving toward each other or forward.

**Why it works:** Instead of checking all pairs O(n²), you eliminate impossible candidates intelligently → O(n).

```
Problem: Find two numbers in sorted array that sum to target.
Array: [1, 3, 5, 7, 9, 11], target = 12

Two-pointer approach:
  L=0 (→)                R=5 (←)
  [1, 3, 5, 7, 9, 11]    sum = 1+11 = 12 ✓ FOUND!

If sum < target: move L right (increase sum)
If sum > target: move R left (decrease sum)
If sum = target: found!

Visual trace:
Step 1: L→1, R→11, sum=12 = target → DONE
(In worst case, L and R meet in the middle)
```

```go
package main

import "fmt"

func twoSum(arr []int, target int) (int, int) {
    l, r := 0, len(arr)-1
    for l < r {
        sum := arr[l] + arr[r]
        if sum == target {
            return l, r
        } else if sum < target {
            l++ // need bigger sum, move left pointer right
        } else {
            r-- // need smaller sum, move right pointer left
        }
    }
    return -1, -1
}

func main() {
    arr := []int{1, 3, 5, 7, 9, 11}
    i, j := twoSum(arr, 12)
    fmt.Printf("Indices: %d, %d → Values: %d, %d\n", i, j, arr[i], arr[j])
    // Indices: 0, 5 → Values: 1, 11
}
```

---

### 7.4 Sliding Window Pattern

**What it is:** A "window" of fixed or variable size slides over the array. You maintain a running computation over the window without recomputing from scratch.

```
Array: [2, 1, 5, 1, 3, 2], window size k=3
Find max sum of any contiguous subarray of size k.

Window slides:
  [2, 1, 5] | 1, 3, 2   sum = 8
   2, [1, 5, 1] | 3, 2  sum = 7
   2, 1, [5, 1, 3] | 2  sum = 9  ← MAX
   2, 1, 5, [1, 3, 2]   sum = 6

Key insight:
  New window sum = Old sum - element leaving + element entering
  (One subtraction + one addition vs recomputing entire window)

  O(n) instead of O(n*k)
```

```rust
fn max_window_sum(arr: &[i32], k: usize) -> i32 {
    if arr.len() < k { return 0; }

    // Compute first window
    let mut window_sum: i32 = arr[..k].iter().sum();
    let mut max_sum = window_sum;

    // Slide the window
    for i in k..arr.len() {
        // Add new element (entering), subtract old element (leaving)
        window_sum += arr[i] - arr[i - k];
        if window_sum > max_sum {
            max_sum = window_sum;
        }
    }
    max_sum
}

fn main() {
    let arr = vec![2, 1, 5, 1, 3, 2];
    println!("Max sum (k=3): {}", max_window_sum(&arr, 3)); // 9
}
```

---

## 8. 📊 Complexity Analysis of Loops

### Time Complexity Rules

```
┌─────────────────────────────────────────────────────────────┐
│  LOOP STRUCTURE              │  TIME COMPLEXITY             │
│──────────────────────────────│──────────────────────────────│
│  Single loop 0..n            │  O(n)                        │
│  Single loop 0..n, step k    │  O(n/k) = O(n)               │
│  Two nested loops 0..n each  │  O(n²)                       │
│  Three nested loops          │  O(n³)                       │
│  Loop that halves each iter  │  O(log n)  ← binary search   │
│  Loop 0..n, inner 0..i       │  O(n²/2) = O(n²)             │
│  Loop 0..n, inner 0..log n   │  O(n log n) ← merge sort     │
└─────────────────────────────────────────────────────────────┘
```

### Visual Complexity Growth

```
n = 1,000

O(log n)  →          10 operations
O(n)      →       1,000 operations
O(n log n)→      10,000 operations
O(n²)     →   1,000,000 operations
O(n³)     → 1,000,000,000 operations ← DANGER ZONE

Graph (relative):
O(1)      │█
O(log n)  │██
O(n)      │█████████████
O(n log n)│██████████████████████████
O(n²)     │████████████████████████████████████████████████████
O(n³)     │(off the chart)
```

### Counting Iterations — The Expert Technique

```c
// How many times does the body execute?

// Example 1: Single loop
for (int i = 0; i < n; i++)  // n times → O(n)

// Example 2: Halving
for (int i = n; i > 0; i /= 2) // log₂(n) times → O(log n)
// i: n → n/2 → n/4 → ... → 1

// Example 3: Triangular
for (int i = 0; i < n; i++)
    for (int j = 0; j < i; j++) // 0+1+2+...+(n-1) = n(n-1)/2 → O(n²)

// Example 4: Independent inner loop
for (int i = 0; i < n; i++)
    for (int j = 0; j < m; j++) // n*m → O(n*m)
```

---

## 9. ⚡ Loop Optimizations

### 9.1 Loop Invariant Code Motion

**Concept:** If a computation inside the loop doesn't change across iterations, move it OUTSIDE.

```c
// SLOW: recomputes strlen every iteration
for (int i = 0; i < strlen(s); i++) { ... }

// FAST: compute once, cache it
int len = strlen(s);
for (int i = 0; i < len; i++) { ... }

// The compiler MIGHT do this automatically, but never rely on it.
// Explicit is better.
```

### 9.2 Loop Unrolling (Conceptual)

**Concept:** Process multiple elements per iteration to reduce loop overhead (branch predictions, counter updates).

```c
// Normal: 4 iterations, 4 condition checks
for (int i = 0; i < 4; i++) {
    arr[i] *= 2;
}

// Unrolled: 1 iteration, 1 condition check (for tiny fixed arrays)
arr[0] *= 2;
arr[1] *= 2;
arr[2] *= 2;
arr[3] *= 2;

// Compilers (especially with -O2/-O3) do this automatically.
// In Rust, LLVM's optimizer does this aggressively.
// Manual unrolling is rarely needed; understand the concept.
```

### 9.3 Cache Locality — The Hidden Performance Factor

```
Memory hierarchy:
  L1 Cache: ~1ns
  L2 Cache: ~4ns
  L3 Cache: ~10ns
  RAM:      ~100ns

Row-major vs Column-major traversal of a 2D array:

C stores arrays ROW by ROW in memory:
  matrix[0][0], matrix[0][1], matrix[0][2],
  matrix[1][0], matrix[1][1], ...

GOOD (row-major, cache-friendly):
  for i → for j: matrix[i][j]
  Accesses: consecutive memory → cache hit ✓

BAD (column-major, cache-unfriendly):
  for j → for i: matrix[i][j]
  Accesses: jumps by row_size bytes → cache miss ✗
  Can be 10x SLOWER on large matrices!
```

```c
// Cache-friendly matrix traversal
int matrix[1000][1000];
long sum = 0;

// FAST: row-major (iterate row by row)
for (int i = 0; i < 1000; i++)
    for (int j = 0; j < 1000; j++)
        sum += matrix[i][j];  // sequential memory access

// SLOW: column-major (iterate column by column)
for (int j = 0; j < 1000; j++)
    for (int i = 0; i < 1000; i++)
        sum += matrix[i][j];  // jumps 1000 ints each access
```

---

## 10. 🗺️ Decision Tree — Which Loop to Use?

```
                    You need repetition
                           │
                           ▼
         ┌─────────────────────────────────┐
         │  Do you know the exact number   │
         │  of iterations beforehand?      │
         └─────────────────────────────────┘
                  │              │
                YES             NO
                  │              │
                  ▼              ▼
           ┌──────────┐   ┌────────────────────────────┐
           │ for loop │   │ Do you need the body to    │
           │ (or range│   │ execute at least ONCE?     │
           │  in Rust)│   └────────────────────────────┘
           └──────────┘             │           │
                                   YES          NO
                                    │            │
                                    ▼            ▼
                             ┌──────────┐  ┌──────────────────┐
                             │ do-while │  │ while loop       │
                             │ (C)      │  │ (for in Go/Rust  │
                             │ loop{}   │  │  with condition) │
                             │ (Rust)   │  └──────────────────┘
                             └──────────┘
                                              │
                                              ▼
                               Does the loop ever terminate?
                                    │           │
                                   YES          NO
                                    │            │
                                    ▼            ▼
                             Normal while   Infinite loop
                                           (loop{} / for{} / while(1))
                                           with explicit break
```

---

## 11. 🌐 Real-World Use Cases

```
┌─────────────────────────────────────────────────────────────┐
│  DOMAIN            │  LOOP TYPE    │  WHAT IT DOES          │
│────────────────────│───────────────│────────────────────────│
│  Web Server        │  Infinite     │  Accept connections     │
│  Game Engine       │  Infinite     │  Game loop tick        │
│  Database          │  for/while    │  Scan rows/pages       │
│  File Processing   │  while/for    │  Read line by line     │
│  Image Rendering   │  Nested for   │  Process each pixel    │
│  Sorting Algorithm │  Nested for   │  Compare & swap        │
│  Network Retry     │  while/do-whi │  Retry on failure      │
│  String Processing │  for          │  Char by char parsing  │
│  Machine Learning  │  for          │  Gradient descent      │
│  Embedded Systems  │  Infinite     │  Sensor polling        │
│  Crypto Mining     │  Infinite     │  Hash computation      │
│  DNS Resolver      │  while        │  Traverse record chain │
└─────────────────────────────────────────────────────────────┘
```

### Full Real-World Example: Line-by-Line File Processing (C)

```c
#include <stdio.h>
#include <string.h>

int main() {
    FILE *file = fopen("data.txt", "r");
    if (!file) {
        perror("Cannot open file");
        return 1;
    }

    char line[256];
    int line_count = 0;
    int word_count = 0;

    // while(fgets(...)) reads until EOF — classic C pattern
    // fgets returns NULL at end of file → loop terminates naturally
    while (fgets(line, sizeof(line), file) != NULL) {
        line_count++;

        // Count words (spaces indicate word boundaries)
        int in_word = 0;
        for (int i = 0; line[i] != '\0'; i++) {
            if (line[i] != ' ' && line[i] != '\n') {
                if (!in_word) {
                    word_count++;
                    in_word = 1;
                }
            } else {
                in_word = 0;
            }
        }
    }

    printf("Lines: %d, Words: %d\n", line_count, word_count);
    fclose(file);
    return 0;
}
```

### Full Real-World Example: HTTP Server Main Loop (Go)

```go
package main

import (
    "fmt"
    "net"
    "bufio"
)

func main() {
    listener, _ := net.Listen("tcp", ":8080")
    fmt.Println("Server listening on :8080")

    // Infinite loop: accept new connections forever
    for {
        conn, err := listener.Accept() // blocks until connection arrives
        if err != nil {
            fmt.Println("Error:", err)
            continue // skip this iteration, keep serving
        }

        // Handle each connection in a goroutine (concurrently)
        go func(c net.Conn) {
            defer c.Close()
            scanner := bufio.NewScanner(c)

            // Inner loop: read all lines from this connection
            for scanner.Scan() {
                line := scanner.Text()
                fmt.Println("Received:", line)
                c.Write([]byte("ACK: " + line + "\n"))
            }
        }(conn)
    }
}
```

---

## 12. 🧠 Psychological Framework — How Experts Think About Loops

### Before Writing Code — The Expert's Internal Monologue

```
Step 1: IDENTIFY THE REPETITIVE PATTERN
  "What action am I repeating?"
  "What changes each time? What stays the same?"

Step 2: DEFINE THE BOUNDS
  "When do I start?"
  "When do I stop?"
  "What's my stopping condition?"

Step 3: CHOOSE THE LOOP TYPE
  (Use the decision tree above)

Step 4: TRACE A SMALL EXAMPLE
  Never code a loop without mentally tracing 3-5 iterations.
  This catches off-by-one errors BEFORE they become bugs.

Step 5: CHECK EDGE CASES
  "What if the input is empty?"
  "What if n=0? n=1? n=INT_MAX?"
  "Can this loop run forever?"
  "Can this loop underflow (i becomes negative when i is unsigned)?"
```

### The Three Most Common Loop Bugs

```
BUG 1: OFF-BY-ONE ERROR
  Should loop n times, loops n-1 or n+1 times.
  Fix: Use <= vs < carefully. Trace first and last iterations.

  WRONG: for(i=1; i<n; i++)   // misses index n-1
  RIGHT: for(i=0; i<n; i++)   // covers 0 to n-1

BUG 2: INFINITE LOOP
  Update step never brings condition to false.
  Fix: Ensure every path through the loop advances state.

  WRONG:
    while (i < n) {
        if (arr[i] % 2 == 0) i++; // never increments for odd!
    }
  RIGHT:
    while (i < n) {
        if (arr[i] % 2 == 0) process(arr[i]);
        i++; // ALWAYS advance
    }

BUG 3: LOOP VARIABLE OVERFLOW
  In C: unsigned int i counting DOWN to 0, then i-- wraps to UINT_MAX.
  Fix: Use signed integers for loop counters, or restructure condition.

  WRONG (C): for(unsigned int i = n-1; i >= 0; i--)  // infinite!
  RIGHT (C): for(int i = n-1; i >= 0; i--)
```

### Deliberate Practice Prescription

```
WEEK 1: Master for/while/do-while in all 3 languages.
        Write 10 loops per day from scratch without IDE help.

WEEK 2: Master nested loops + complexity analysis.
        For every nested loop you write, state its Big-O.

WEEK 3: Master loop patterns (accumulation, search, two-pointer).
        Implement binary search from memory 5 days in a row.

WEEK 4: Implement classic algorithms using only loops:
        - Bubble sort, selection sort, insertion sort
        - Linear search, binary search
        - Reverse an array in-place
        - Check palindrome
        - Find all primes (Sieve of Eratosthenes)

META-LEARNING PRINCIPLE — "Interleaving":
  Don't practice one loop type exhaustively then move on.
  Mix them in practice sessions. Interleaved practice is
  harder but produces deeper retention (cognitive science).

CHUNKING PRINCIPLE:
  Once you truly internalize the 3-question model
  (start/stop/advance), all loop variants become
  trivial variations of the same mental chunk.
  This is how experts see loops — as ONE concept,
  not five separate constructs.
```

---

## 📋 Final Summary Cheatsheet

```
┌──────────────────────────────────────────────────────────────┐
│              LOOP QUICK REFERENCE                            │
├────────────┬──────────────────┬────────────────┬────────────┤
│  LOOP TYPE │  C               │  Go            │  Rust      │
├────────────┼──────────────────┼────────────────┼────────────┤
│  for       │ for(i=0;i<n;i++) │ for i:=0;i<n.. │ for i in.. │
│  while     │ while(cond){}    │ for cond {}    │ while cond │
│  do-while  │ do{}while(cond)  │ for{..;if!c{b}}│ loop{..;b} │
│  infinite  │ while(1) /for(;;)│ for {}         │ loop {}    │
│  range     │ N/A (manual idx) │ for i,v:=range │ for v in.. │
│  labeled   │ goto / flag      │ LABEL: for...  │ 'lbl: loop │
├────────────┼──────────────────┼────────────────┼────────────┤
│  break     │ break            │ break          │ break      │
│  continue  │ continue         │ continue       │ continue   │
│  labeled   │ goto label       │ break LABEL    │ break 'lbl │
│  break     │                  │                │            │
└────────────┴──────────────────┴────────────────┴────────────┘
```

---

> *"The expert has failed more times than the beginner has tried. Every bug in a loop is a rep in your mental gym — embrace them."*

Master loops and you've mastered the heartbeat of every algorithm that exists. Every sort, every search, every graph traversal, every ML training run — all loops, all the way down.