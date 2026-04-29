```
package main

import "fmt"

type Error interface {
    Error() string
}

type NetworkError struct {
    Code    int
    Message string
}

func (e *NetworkError) Error() string {
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}

// CLASSIC BUG: returning typed nil from interface-returning function
func badFunction() error {
    var err *NetworkError = nil // typed nil pointer
    // This looks like nil, but...
    return err // returns interface{type=*NetworkError, value=nil}
    // The interface is NOT nil! It has a type!
}

func goodFunction() error {
    // Explicitly return untyped nil when there's no error
    return nil
}

func main() {
    err := badFunction()
    if err != nil { // This evaluates to TRUE — the bug!
        fmt.Println("Bug: returned typed nil, but interface is not nil")
        fmt.Printf("Type: %T, Value: %v\n", err, err)
    }

    err2 := goodFunction()
    if err2 == nil {
        fmt.Println("Correct: genuine nil interface")
    }
}
```

```
func (e *NetworkError) Error() string {
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}
```

# Understanding `*NetworkError` as a Pointer Receiver

Let me build this from absolute zero.

---

## 🧱 Foundation: What is a Pointer?

A **pointer** is a variable that **stores a memory address** — not the actual data, but the **location** of the data in memory.

```
Normal variable:          Pointer variable:
┌──────────────┐          ┌──────────────┐
│  value: 404  │          │  addr: 0x01  │──────► ┌──────────────┐
│  addr: 0x01  │          │  addr: 0x05  │        │  value: 404  │
└──────────────┘          └──────────────┘        │  addr: 0x01  │
                                                   └──────────────┘
  holds data directly       holds address            actual data
                            (points to data)         lives here
```

In Go:
```go
x := 404          // x holds the VALUE 404
p := &x           // p holds the ADDRESS of x  ← & means "address of"
fmt.Println(*p)   // *p means "go to that address, get the value" → 404
```

```
&  →  "give me the address of"
*  →  "go to that address and give me what's there"
```

---

## 🔬 What is a Method Receiver?

When you define a method on a type, you write:

```go
func (e NetworkError) Error() string { ... }
//    ↑
//    this is the RECEIVER
//    it's like saying "this method belongs to NetworkError"
//    e is the variable name you use inside the method
```

The receiver is how Go knows **which type owns this method**.

---

## 🔀 Two Kinds of Receivers

```
┌────────────────────────────────────────────────────────┐
│                   METHOD RECEIVERS                     │
│                                                        │
│   Value Receiver          Pointer Receiver             │
│   ──────────────          ────────────────             │
│   func (e NetworkError)   func (e *NetworkError)       │
│                                   ↑                    │
│                                   * = pointer          │
│                                                        │
│   Gets a COPY of the      Gets the ACTUAL object       │
│   struct                  (via its address)            │
└────────────────────────────────────────────────────────┘
```

---

## 📦 ASCII: Value vs Pointer Receiver — Memory Picture

```
Your struct in memory:
┌─────────────────────────┐
│   NetworkError          │
│   ┌──────┬───────────┐  │
│   │ Code │  Message  │  │
│   │  404 │ "timeout" │  │
│   └──────┴───────────┘  │
│   address: 0xA1         │
└─────────────────────────┘


VALUE RECEIVER:                    POINTER RECEIVER:
func (e NetworkError) ...          func (e *NetworkError) ...

┌─────────────────────┐            e = 0xA1 (address)
│  COPY of struct     │                 │
│  ┌──────┬────────┐  │                 ▼
│  │  404 │timeout │  │       ┌─────────────────────────┐
│  └──────┴────────┘  │       │   ORIGINAL struct       │
│  (new memory)       │       │   ┌──────┬───────────┐  │
└─────────────────────┘       │   │  404 │  timeout  │  │
                               │   └──────┴───────────┘  │
e works on the COPY            │   address: 0xA1         │
changes don't affect           └─────────────────────────┘
the original                   e works on the ORIGINAL
                                changes DO affect original
```

---

## 🔬 Your Code — Dissected Line by Line

```go
func (e *NetworkError) Error() string {
//    ↑  ↑
//    │  └── the TYPE: *NetworkError = pointer to a NetworkError
//    └───── the NAME: e (you can use e inside the function body)

    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
    //                             ↑         ↑
    //                   Go auto-dereferences the pointer
    //                   e.Code is actually (*e).Code behind the scenes
}
```

When you write `e *NetworkError`:
- `e` is NOT a `NetworkError` struct
- `e` IS a **pointer** — it holds the **memory address** of a `NetworkError`

---

## 🧪 Concrete Memory Walk-Through

```go
n := &NetworkError{Code: 404, Message: "timeout"}
//   ↑ & gives the address of the newly created struct
//   n is now a *NetworkError (pointer to NetworkError)

n.Error()  // calling the method
```

```
Step 1: struct created in memory
        ┌──────────────────────────┐
        │  NetworkError            │
        │  Code:    404            │
        │  Message: "timeout"      │
        │  @ address: 0xA1         │
        └──────────────────────────┘

Step 2: n = &NetworkError{...}
        n holds: 0xA1  (just the address, not the struct)

Step 3: n.Error() is called
        Go passes 0xA1 as the receiver e
        ┌─────────────────────────────────────────┐
        │  func (e *NetworkError) Error() string  │
        │  e = 0xA1                               │
        │  e.Code    →  (*e).Code    →  404       │
        │  e.Message →  (*e).Message →  "timeout" │
        │  returns "[404] timeout"                │
        └─────────────────────────────────────────┘
```

---

## ⚠️ Critical: Pointer Receiver Changes Interface Satisfaction

This is where your original bug code connects.

```
Value Receiver:                     Pointer Receiver:
func (e NetworkError) Error()       func (e *NetworkError) Error()

Who satisfies the error interface?  Who satisfies the error interface?

NetworkError    ✅                  NetworkError    ❌
*NetworkError   ✅                  *NetworkError   ✅
```

**Rule:**
```
┌──────────────────────────────────────────────────────────┐
│  If method is on VALUE receiver   → both T and *T satisfy │
│  If method is on POINTER receiver → only *T satisfies     │
└──────────────────────────────────────────────────────────┘
```

In your code, since the receiver is `*NetworkError`:

```go
// ✅ This works — *NetworkError satisfies error
var e error = &NetworkError{404, "timeout"}

// ❌ This FAILS to compile — NetworkError (non-pointer) does NOT satisfy error
var e error = NetworkError{404, "timeout"}
```

---

## 🔄 Decision Tree: Which Receiver to Use?

```
Do you need to MODIFY the struct inside the method?
            │
     YES ───┤         NO ──→ Is the struct large?
            │                       │
            │              YES ─────┤    NO ──→ Value receiver is fine
            │                       │           (small copy is cheap)
            │                       ▼
            ▼                Pointer receiver
     Pointer receiver        (avoid expensive copy)
     (must modify original)


In your case:
Error() only READS Code and Message → no modification needed
But *NetworkError is still used → likely for consistency
(if any OTHER method on NetworkError modifies it,
 all methods should use pointer receiver for consistency)
```

---

## 🧭 Summary Table

| Syntax | Name | What `e` is | Modifies original? |
|---|---|---|---|
| `func (e NetworkError)` | Value receiver | Copy of struct | ❌ No |
| `func (e *NetworkError)` | Pointer receiver | Address of struct | ✅ Yes |

---

## 🔗 Connecting Back to Your Bug

```go
var err *NetworkError = nil   // typed nil pointer
return err                    // returns as error interface
```

```
Interface internal representation:
┌────────────────────────────────┐
│  type:  *NetworkError          │  ← NOT nil (type is known)
│  value: nil                    │  ← nil (no actual struct)
└────────────────────────────────┘

err != nil  →  TRUE  ← because type slot is filled
```

The pointer receiver is **exactly why** the type information exists in the interface — because `*NetworkError` (not `NetworkError`) is what satisfied the interface.

---

**Next natural step:** We can go into `*T` vs `T` method sets rigorously, or dive into how Go's auto-dereference (`e.Code` instead of `(*e).Code`) works under the hood. Both are deep and important.