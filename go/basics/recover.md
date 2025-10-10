# Comprehensive Guide to `recover` in Go

## Table of Contents
1. Introduction to Panic and Recover
2. Complete Implementations
3. Using vs Not Using Recover
4. Errors and Warnings
5. Correct and Incorrect Usage
6. Benefits and Control Flow

---

## 1. Introduction to Panic and Recover

In Go, `recover` is a built-in function used to regain control of a panicking goroutine. It works in conjunction with `panic` and `defer`.

**Key Concepts:**
- `panic`: Stops normal execution and begins panicking
- `defer`: Schedules a function call to be run after the function completes
- `recover`: Catches a panic and resumes normal execution

---

## 2. Complete Implementations---

package main

import (
	"errors"
	"fmt"
	"log"
)

// ============================================
// 1. BASIC RECOVER USAGE
// ============================================

// Example 1: Basic recover in a deferred function
func basicRecoverExample() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Recovered from panic:", r)
		}
	}()

	fmt.Println("About to panic...")
	panic("something went wrong!")
	fmt.Println("This line will never execute")
}

// ============================================
// 2. WITHOUT RECOVER - PROGRAM CRASHES
// ============================================

// Example 2: No recover - program will crash
func noPanicHandling() {
	fmt.Println("Starting function without recover...")
	panic("unhandled panic - program will crash!")
	fmt.Println("This will never print")
}

// ============================================
// 3. RECOVER WITH ERROR CONVERSION
// ============================================

// Example 3: Converting panic to error
func divideWithRecover(a, b int) (result int, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("panic recovered: %v", r)
		}
	}()

	if b == 0 {
		panic("division by zero")
	}
	return a / b, nil
}

// Example 4: Same function without recover
func divideWithoutRecover(a, b int) int {
	return a / b // Will crash if b is 0
}

// ============================================
// 4. NESTED FUNCTION CALLS WITH RECOVER
// ============================================

// Example 5: Panic in nested calls
func level3() {
	panic("panic at level 3!")
}

func level2() {
	level3()
}

func level1WithRecover() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Caught panic from nested call:", r)
		}
	}()
	level2()
}

func level1WithoutRecover() {
	level2() // Will crash when level3 panics
}

// ============================================
// 5. RECOVER IN GOROUTINES
// ============================================

// Example 6: Recover in goroutines (IMPORTANT!)
func safeGoroutine() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Goroutine recovered from panic:", r)
		}
	}()

	// Simulating some work that might panic
	panic("panic in goroutine!")
}

func unsafeGoroutine() {
	// No recover - if this panics, entire program crashes
	panic("unhandled panic in goroutine - program will crash!")
}

// ============================================
// 6. SELECTIVE PANIC HANDLING
// ============================================

// Example 7: Only recovering specific panic types
func selectiveRecover() {
	defer func() {
		if r := recover(); r != nil {
			// Only handle string panics, re-panic others
			if err, ok := r.(string); ok {
				fmt.Println("Handled string panic:", err)
			} else {
				// Re-panic if it's not a string
				panic(r)
			}
		}
	}()

	panic("this is a string panic") // Will be caught
	// panic(42) // Would be re-panicked
}

// ============================================
// 7. RECOVER WITH CLEANUP
// ============================================

// Example 8: Recover with resource cleanup
type Resource struct {
	name   string
	closed bool
}

func (r *Resource) Close() {
	r.closed = true
	fmt.Printf("Resource %s closed\n", r.name)
}

func processWithRecover() error {
	resource := &Resource{name: "database"}

	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Panic occurred, cleaning up...")
			resource.Close()
			fmt.Printf("Recovered from: %v\n", r)
		}
	}()

	defer resource.Close() // Always close resource

	// Simulating work that might panic
	panic("unexpected error during processing")

	return nil
}

func processWithoutRecover() {
	resource := &Resource{name: "database"}
	defer resource.Close() // This will run, but program still crashes

	panic("unexpected error - program crashes!")
}

// ============================================
// 8. INCORRECT USAGE EXAMPLES
// ============================================

// INCORRECT: Recover outside defer (won't work!)
func incorrectRecoverUsage1() {
	if r := recover(); r != nil { // This does NOTHING!
		fmt.Println("This will never execute")
	}
	panic("panic!")
}

// INCORRECT: Recover in wrong goroutine
func incorrectRecoverUsage2() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Won't catch panic from other goroutine")
		}
	}()

	go func() {
		panic("panic in different goroutine") // Won't be caught!
	}()
}

// INCORRECT: Nested defer without recover propagation
func incorrectRecoverUsage3() {
	defer func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Println("Inner recover:", r)
				// Panic is handled here but not propagated
			}
		}()
	}()

	panic("nested defer issue")
}

// ============================================
// 9. CORRECT USAGE PATTERNS
// ============================================

// CORRECT: Proper recover with logging
func correctRecoverPattern1() (err error) {
	defer func() {
		if r := recover(); r != nil {
			// Log the panic
			log.Printf("Panic occurred: %v", r)
			// Convert to error
			err = fmt.Errorf("recovered from panic: %v", r)
		}
	}()

	// Code that might panic
	panic("something went wrong")
}

// CORRECT: Recover in each goroutine
func correctRecoverPattern2() {
	go func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Println("Goroutine 1 recovered:", r)
			}
		}()
		panic("panic in goroutine 1")
	}()

	go func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Println("Goroutine 2 recovered:", r)
			}
		}()
		panic("panic in goroutine 2")
	}()
}

// CORRECT: Recover with stack trace
func correctRecoverPattern3() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("Panic: %v\n", r)
			// In real code, use runtime.Stack() for stack trace
			fmt.Println("Stack trace would be logged here")
		}
	}()

	panic("critical error")
}

// ============================================
// 10. REAL-WORLD USE CASES
// ============================================

// Use Case 1: HTTP Handler protection
func httpHandlerWithRecover(handler func()) {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("Handler panic: %v", r)
			// In real code: send 500 response to client
			fmt.Println("Sending 500 Internal Server Error")
		}
	}()

	handler()
}

// Use Case 2: Worker pool with panic protection
func workerWithRecover(id int, jobs <-chan int) {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("Worker %d recovered from panic: %v", id, r)
			// Worker can continue processing other jobs
		}
	}()

	for job := range jobs {
		// Process job (might panic)
		if job == 13 { // Unlucky number
			panic(fmt.Sprintf("worker %d panicked on job %d", id, job))
		}
		fmt.Printf("Worker %d processed job %d\n", id, job)
	}
}

// Use Case 3: Validation with panic recovery
func validateDataWithRecover(data map[string]interface{}) error {
	defer func() {
		if r := recover(); r != nil {
			// Convert panic to validation error
			fmt.Printf("Validation panic recovered: %v\n", r)
		}
	}()

	// Code that might panic on invalid data
	name := data["name"].(string) // Type assertion might panic
	if len(name) == 0 {
		panic("name cannot be empty")
	}

	return nil
}

// ============================================
// 11. COMPARISON: WITH VS WITHOUT RECOVER
// ============================================

// Comparison example: Array access
func safeArrayAccess(arr []int, index int) (value int, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = errors.New("index out of bounds")
		}
	}()

	return arr[index], nil
}

func unsafeArrayAccess(arr []int, index int) int {
	return arr[index] // Will panic if index out of bounds
}

// ============================================
// MAIN FUNCTION - DEMONSTRATION
// ============================================

func main() {
	fmt.Println("=== GO RECOVER COMPREHENSIVE EXAMPLES ===\n")

	// Example 1: Basic recover
	fmt.Println("1. Basic Recover:")
	basicRecoverExample()
	fmt.Println()

	// Example 3: Divide with recover
	fmt.Println("2. Divide with Recover:")
	result, err := divideWithRecover(10, 0)
	if err != nil {
		fmt.Println("Error:", err)
	} else {
		fmt.Println("Result:", result)
	}
	fmt.Println()

	// Example 5: Nested calls with recover
	fmt.Println("3. Nested Calls with Recover:")
	level1WithRecover()
	fmt.Println()

	// Example 6: Safe goroutine
	fmt.Println("4. Goroutine with Recover:")
	go safeGoroutine()
	fmt.Println("Main continues executing...")
	// time.Sleep(100 * time.Millisecond) // Wait for goroutine
	fmt.Println()

	// Example 7: Selective recover
	fmt.Println("5. Selective Recover:")
	selectiveRecover()
	fmt.Println()

	// Example 8: Recover with cleanup
	fmt.Println("6. Recover with Cleanup:")
	processWithRecover()
	fmt.Println()

	// Example 9: Correct pattern
	fmt.Println("7. Correct Pattern with Error Return:")
	err = correctRecoverPattern1()
	fmt.Println("Returned error:", err)
	fmt.Println()

	// Example 11: Safe array access
	fmt.Println("8. Safe Array Access:")
	arr := []int{1, 2, 3}
	val, err := safeArrayAccess(arr, 10)
	if err != nil {
		fmt.Println("Error:", err)
	} else {
		fmt.Println("Value:", val)
	}
	fmt.Println()

	// HTTP handler example
	fmt.Println("9. HTTP Handler with Recover:")
	httpHandlerWithRecover(func() {
		panic("handler panic!")
	})
	fmt.Println()

	fmt.Println("=== ALL EXAMPLES COMPLETED SUCCESSFULLY ===")

	// Uncomment to see crashes:
	// fmt.Println("\n=== EXAMPLES THAT WOULD CRASH ===")
	// noPanicHandling() // This will crash the program
	// divideWithoutRecover(10, 0) // This will crash
	// level1WithoutRecover() // This will crash
}

## 3. Using vs Not Using Recover

### **With Recover:**
```go
func withRecover() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("Recovered:", r)
        }
    }()
    panic("error!")
    // Program continues
}
```

### **Without Recover:**
```go
func withoutRecover() {
    panic("error!")
    // Program CRASHES
}
```

---

## 4. Errors and Warnings When Not Using Recover

### **What Happens Without Recover:**

1. **Program Termination**: The entire program crashes immediately
2. **Lost Resources**: Resources may not be cleaned up properly
3. **Stack Unwinding**: All defers run, but program still exits
4. **Goroutine Impact**: If panic occurs in a goroutine, entire program crashes
5. **No Error Handling**: Cannot convert panic to error for graceful handling

### **Common Scenarios:**

```go
// Scenario 1: Division by zero
func divide(a, b int) int {
    return a / b  // CRASHES if b == 0
}

// Scenario 2: Nil pointer dereference
func process(data *Data) {
    value := data.Value  // CRASHES if data is nil
}

// Scenario 3: Index out of bounds
func getElement(arr []int, idx int) int {
    return arr[idx]  // CRASHES if idx >= len(arr)
}

// Scenario 4: Type assertion failure
func getName(i interface{}) string {
    return i.(string)  // CRASHES if i is not string
}
```

---

## 5. Correct and Incorrect Usage

### **✅ CORRECT Usage:**

1. **Always use recover inside defer:**
```go
defer func() {
    if r := recover(); r != nil {
        // Handle panic
    }
}()
```

2. **Recover in each goroutine:**
```go
go func() {
    defer func() {
        if r := recover(); r != nil {
            log.Println("Goroutine panic:", r)
        }
    }()
    // Work here
}()
```

3. **Convert panic to error:**
```go
func safe() (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("error: %v", r)
        }
    }()
    // Work here
    return nil
}
```

4. **Clean up resources:**
```go
defer func() {
    if r := recover(); r != nil {
        closeResources()
        log.Println("Panic:", r)
    }
}()
```

### **❌ INCORRECT Usage:**

1. **Recover outside defer (doesn't work!):**
```go
func wrong() {
    if r := recover(); r != nil {  // WRONG! Does nothing
        fmt.Println("Won't catch anything")
    }
    panic("error")
}
```

2. **Trying to catch panic from another goroutine:**
```go
func wrong() {
    defer func() {
        recover()  // Won't catch panic from other goroutine
    }()
    
    go func() {
        panic("error")  // This crashes the program!
    }()
}
```

3. **Not checking recover return value:**
```go
defer func() {
    recover()  // Ignoring return value is useless
}()
```

4. **Using recover for control flow:**
```go
// DON'T DO THIS - use errors instead
func bad() {
    defer func() {
        if r := recover(); r != nil {
            // Using panic/recover as goto
        }
    }()
    
    if condition {
        panic("jump")
    }
}
```

---

## 6. Benefits and Control Flow

### **Benefits of Using Recover:**

1. **Graceful Degradation**: Program can continue running after recovering from panic
2. **Resource Cleanup**: Ensure proper cleanup even when panicking
3. **Error Conversion**: Convert panics to errors for API consistency
4. **Debugging**: Log panic information for debugging
5. **Goroutine Safety**: Prevent one goroutine crash from killing entire program
6. **User Experience**: Return meaningful errors instead of crashes

### **Control Flow With Recover:**

```
Normal Flow:
Function Start → Code Execution → Return → Continue

With Panic (No Recover):
Function Start → Code Execution → PANIC → Stack Unwind → CRASH

With Panic (With Recover):
Function Start → Code Execution → PANIC → Defer Functions → 
Recover Catches → Handle Error → Return/Continue
```

### **Detailed Control Flow Example:**

```go
func demonstrateControlFlow() {
    fmt.Println("1. Function starts")
    
    defer func() {
        fmt.Println("3. Deferred function runs")
        if r := recover(); r != nil {
            fmt.Println("4. Panic caught:", r)
            fmt.Println("5. Control restored")
        }
    }()
    
    fmt.Println("2. About to panic")
    panic("error occurred")
    fmt.Println("NEVER REACHED")
}

// Output:
// 1. Function starts
// 2. About to panic
// 3. Deferred function runs
// 4. Panic caught: error occurred
// 5. Control restored
```

### **Control Flow WITHOUT Recover:**

```go
func withoutRecoverFlow() {
    fmt.Println("1. Function starts")
    
    defer func() {
        fmt.Println("3. Deferred function runs")
        // No recover - program will still crash
    }()
    
    fmt.Println("2. About to panic")
    panic("error occurred")
    fmt.Println("NEVER REACHED")
}

// Output:
// 1. Function starts
// 2. About to panic
// 3. Deferred function runs
// panic: error occurred
// [Program exits with stack trace]
```

---

## 7. Best Practices

### **When to Use Recover:**

✅ **DO use recover for:**
- Web server handlers (prevent one request from crashing server)
- Worker pools (prevent one task from killing all workers)
- Goroutines (prevent goroutine panic from crashing program)
- Library boundaries (convert panics to errors at API boundaries)
- Resource cleanup (ensure cleanup even on panic)

❌ **DON'T use recover for:**
- Normal error handling (use errors instead)
- Control flow (use if/else, loops)
- Expected failures (use error returns)
- Silencing all panics (some panics indicate serious bugs)

### **Guidelines:**

1. **Prefer errors over panics** for expected failures
2. **Use panic only for unrecoverable errors** or programmer mistakes
3. **Always recover in goroutines** to prevent program crashes
4. **Log recovered panics** for debugging
5. **Don't recover from all panics blindly** - some indicate serious problems
6. **Clean up resources** in defer before recovering
7. **Convert panics to errors** at API boundaries

### **Performance Note:**

Panic and recover are relatively expensive operations compared to regular error handling. Use them sparingly for truly exceptional situations, not for normal control flow.

---

## Summary

`recover` in Go is a powerful mechanism for handling panics, but it must be used correctly:

- **Must be called inside a deferred function**
- **Only catches panics in the same goroutine**
- **Should convert panics to errors for API consistency**
- **Essential for goroutine safety**
- **Not a replacement for proper error handling**

The code artifact above provides complete, runnable examples demonstrating all these concepts. You can run it to see the behavior of different recovery patterns!

# Go Recover() Mechanism - Complete Guide

## Part 1: Call by Value vs Call by Reference in Go

```
CALL BY VALUE (Default in Go)
===============================
                                    
main()                              function(x int)
  |                                       |
  v                                       v
┌─────────────┐                    ┌─────────────┐
│ a = 5       │                    │ x = 5       │
│ (addr:0x100)│ ---copy value----> │ (addr:0x200)│
└─────────────┘                    └─────────────┘
                                         |
                                         v
                                   x = x + 1
                                   x = 6
                                         
main() sees: a = 5 (unchanged)


CALL BY REFERENCE (Using Pointers)
====================================

main()                              function(x *int)
  |                                       |
  v                                       v
┌─────────────┐                    ┌─────────────┐
│ a = 5       │                    │ x = 0x100   │
│ (addr:0x100)│ ---copy address--> │ (pointer)   │
│             │                    │  |          │
│             │<---points to-------┘  |          │
└─────────────┘                    └──────────────┘
                                         |
                                         v
                                   *x = *x + 1
                                         
main() sees: a = 6 (changed!)
```

## Part 2: Stack vs Heap Memory

```
MEMORY LAYOUT IN GO
===================

┌──────────────────────────────────────────────┐
│              HEAP MEMORY                     │  <- Garbage Collected
│  • Dynamic allocations                       │  <- Grows upward
│  • Objects escaping scope                    │  
│  • Large objects                             │  
│  • Shared across goroutines                  │
│                                              │
│  Example:                                    │
│  ┌──────────────┐                           │
│  │ slice data   │  (make([]int, 1000))     │
│  ├──────────────┤                           │
│  │ map buckets  │  (map[string]int{})      │
│  ├──────────────┤                           │
│  │ *user        │  (new(User))             │
│  └──────────────┘                           │
└──────────────────────────────────────────────┘
                    ↑
                    | Escape Analysis decides
                    ↓
┌──────────────────────────────────────────────┐
│              STACK MEMORY                    │  <- Per Goroutine
│  • Function call frames                      │  <- Grows downward
│  • Local variables                           │  <- Fast allocation
│  • Function parameters                       │  <- Auto cleanup
│  • Return addresses                          │
│                                              │
│  Goroutine Stack (2KB initial, can grow)    │
│  ┌──────────────────────────┐              │
│  │ main() frame             │              │
│  │  - local vars            │              │
│  │  - return address        │              │
│  ├──────────────────────────┤              │
│  │ helper() frame           │              │
│  │  - parameters            │              │
│  │  - local vars            │              │
│  ├──────────────────────────┤              │
│  │ currentFunc() frame      │  <- SP       │
│  └──────────────────────────┘              │
└──────────────────────────────────────────────┘
```

## Part 3: Panic and Recover Mechanism - Step by Step

```
STEP 1: NORMAL EXECUTION
========================

Stack:
┌────────────────────────┐
│ main()                 │
│  - starts execution    │
└────────────────────────┘

Code:
func main() {
    fmt.Println("Start")
    riskyOperation()    // <-- about to call
    fmt.Println("End")
}


STEP 2: CALLING DEFERRED FUNCTION
==================================

Stack:
┌────────────────────────┐
│ main()                 │
│  - defer registered    │  Defer List: [handlePanic]
│                        │              (LIFO queue)
├────────────────────────┤
│ riskyOperation()       │
│  - executing           │
└────────────────────────┘

Code:
func riskyOperation() {
    defer handlePanic()  // <-- registered but NOT executed yet
    causeError()         // <-- about to call
}


STEP 3: PANIC OCCURS!
=====================

Stack:
┌────────────────────────┐
│ main()                 │
│                        │
├────────────────────────┤
│ riskyOperation()       │
│  - panic triggered!    │  ⚠️ PANIC: "something went wrong"
├────────────────────────┤
│ causeError()           │
│  - panic()             │  <-- PANIC INITIATED HERE
└────────────────────────┘

Panic State:
• Normal execution STOPS
• Unwinding begins
• Defer chain starts executing

Code:
func causeError() {
    panic("something went wrong")  // <-- BOOM!
}


STEP 4: STACK UNWINDING - Execute Defers
=========================================

Stack Unwinding Direction: ↑↑↑

┌────────────────────────┐
│ main()                 │
│  - waiting...          │
├────────────────────────┤
│ riskyOperation()       │
│  - unwinding           │  Defer: handlePanic() executing now!
│  - defer runs          │  ↓↓↓
└────────────────────────┘
     ↑ causeError() frame DESTROYED

Defer Execution:
┌──────────────────────────────────┐
│ handlePanic() is called          │
│ (deferred function executes)     │
└──────────────────────────────────┘


STEP 5: RECOVER() CAPTURES PANIC
=================================

Stack:
┌────────────────────────┐
│ main()                 │
│  - waiting...          │
├────────────────────────┤
│ riskyOperation()       │
│  - handlePanic()       │
│    executing           │
└────────────────────────┘

Inside handlePanic():
┌──────────────────────────────────────┐
│ func handlePanic() {                 │
│     if r := recover(); r != nil {    │ <-- recover() ACTIVE
│         // r = "something went wrong"│     Returns panic value
│         fmt.Println("Recovered:", r) │     Panic is CAUGHT
│     }                                 │
│ }                                     │
└──────────────────────────────────────┘

Panic State:
⚠️ PANIC STOPPED → ✅ RECOVERED
• Panic value captured in 'r'
• Unwinding stops
• Control returns to caller


STEP 6: NORMAL EXECUTION RESUMES
=================================

Stack:
┌────────────────────────┐
│ main()                 │
│  - execution continues │  ✅ Back to normal!
└────────────────────────┘

Code:
func main() {
    fmt.Println("Start")        // Executed
    riskyOperation()             // Panicked but recovered
    fmt.Println("End")           // ❌ WILL NOT EXECUTE
}                                 // riskyOperation() returned normally
                                  // but execution does NOT continue
                                  // after the function that panicked

Output:
Start
Panic occurred: something went wrong
Recovered in riskyOperation
// "End" is NOT printed - execution stops at riskyOperation


STEP 7: COMPLETE FLOW DIAGRAM
==============================

Time →
     
┌──────┐   ┌──────────────┐   ┌──────────┐   ┌──────────┐
│START │-->│ Call Func    │-->│Register  │-->│ Execute  │
│      │   │ with defer   │   │ Defers   │   │ Code     │
└──────┘   └──────────────┘   └──────────┘   └──────────┘
                                                    |
                                              ┌─────┴─────┐
                                              │           │
                                         (no panic)  (panic!)
                                              │           │
                                              ↓           ↓
                                         ┌────────┐  ┌────────────┐
                                         │Continue│  │  Unwind    │
                                         │ Normal │  │   Stack    │
                                         └────────┘  └────────────┘
                                                           |
                                                           ↓
                                                    ┌──────────────┐
                                                    │Execute Defers│
                                                    │   (LIFO)     │
                                                    └──────────────┘
                                                           |
                                                     ┌─────┴─────┐
                                                     │           │
                                              (no recover)  (recover!)
                                                     │           │
                                                     ↓           ↓
                                              ┌──────────┐  ┌──────────┐
                                              │ Program  │  │ Resume   │
                                              │  Crash   │  │ Caller   │
                                              └──────────┘  └──────────┘
```

## Part 4: Memory Behavior During Panic

```
STACK FRAMES DURING PANIC & RECOVER
====================================

BEFORE PANIC:
┌────────────────────────────────┐ ← Stack Top (SP)
│ causeError()                   │
│  - local: msg = "error"        │ (on stack)
│  - return addr: 0x1234         │
├────────────────────────────────┤
│ riskyOperation()               │
│  - defer: handlePanic          │ (defer list stored)
│  - local: x = 42               │ (on stack)
│  - return addr: 0x5678         │
├────────────────────────────────┤
│ main()                         │
│  - local: result = nil         │ (on stack)
│  - return addr: runtime        │
└────────────────────────────────┘ ← Stack Base

DURING PANIC (Unwinding):
┌────────────────────────────────┐
│ handlePanic()                  │ ← Defer executing
│  - r = recover()               │   (captures panic value)
│  - panic value: interface{}    │   (may be on heap if escapes)
├────────────────────────────────┤
│ riskyOperation()               │
│  - x = 42 still exists         │ (frame preserved during defer)
│  - return addr: 0x5678         │
├────────────────────────────────┤
│ main()                         │
│  - result = nil                │
└────────────────────────────────┘
     ↑ causeError() frame POPPED

AFTER RECOVERY:
┌────────────────────────────────┐
│ main()                         │ ← Back to normal
│  - result = nil                │   execution
└────────────────────────────────┘
     ↑ All other frames cleaned up
```

## Part 5: Key Rules

```
RECOVER() RULES:
================

1. ✅ WORKS:
   func example() {
       defer func() {
           if r := recover(); r != nil {  // Direct call in defer
               // Handles panic
           }
       }()
       panic("oops")
   }

2. ❌ DOES NOT WORK:
   func example() {
       defer helper()  // recover() called indirectly
       panic("oops")
   }
   func helper() {
       recover()  // TOO LATE! Not in the deferred function
   }

3. ❌ DOES NOT WORK:
   func example() {
       recover()  // Called outside defer context
       panic("oops")
   }

MEMORY RULES:
=============

STACK:
• Local variables
• Function parameters (copied by value)
• Pointers (address value on stack, pointee may be on heap)
• Small objects (<64KB typically)

HEAP:
• make(), new() often allocate here
• Variables that escape function scope
• Shared data between goroutines
• Large objects
• Panic values (interface{} may escape)

CALL SEMANTICS:
===============

BY VALUE (default):
• Primitives: int, float, bool
• Structs (entire copy)
• Arrays (entire copy)
• Pointers (address copied, pointee shared)

BY REFERENCE (using pointers):
• *T passes address
• Slices, maps, channels (reference types with headers on stack)
```

## Part 6: Complete Example

```go
package main

import "fmt"

func main() {
    fmt.Println("1. Start")
    
    // Stack: main() frame created
    
    result := processData(42)  // Call by value
    
    fmt.Println("6. Result:", result)
    fmt.Println("7. End")
}

func processData(x int) (result int) {  // x copied to stack
    // Stack: processData() frame created
    // x is a local copy (value = 42)
    
    defer func() {  // Registered in defer list
        if r := recover(); r != nil {
            fmt.Println("4. Recovered:", r)
            result = -1  // Named return value
        }
        fmt.Println("5. Defer completed")
    }()
    
    fmt.Println("2. Processing:", x)
    
    if x > 40 {
        panic("3. Value too large!")  // Panic starts unwinding
    }
    
    return x * 2  // Never reached
}

// Output:
// 1. Start
// 2. Processing: 42
// 3. Value too large!
// 4. Recovered: 3. Value too large!
// 5. Defer completed
// 6. Result: -1
// 7. End
```

I'll create a comprehensive ASCII diagram showing how `recover()` works in Go, including call semantics and memory concepts.I've created a comprehensive ASCII diagram that covers:

1. **Call by Value vs Reference**: Shows how Go copies values by default and how pointers enable reference semantics
2. **Stack vs Heap Memory**: Illustrates the memory layout and what goes where
3. **Recover Mechanism**: Step-by-step visualization of how panic triggers, stack unwinding occurs, and recover() captures the panic
4. **Memory Behavior**: Shows exactly what happens to stack frames during panic and recovery
5. **Key Rules**: Critical guidelines for proper use of recover()
6. **Complete Example**: Working code with detailed comments

The diagram uses ASCII art to show:
- Memory addresses and layouts
- Stack frame creation/destruction
- The defer list (LIFO queue)
- Panic propagation and recovery flow
- The difference between value and pointer semantics

Key insights:
- `recover()` must be called directly in a deferred function
- Stack unwinding executes defers in LIFO order
- After recovery, execution returns to the function that deferred the recovering function
- Go defaults to call-by-value, but pointers enable sharing data semantics
