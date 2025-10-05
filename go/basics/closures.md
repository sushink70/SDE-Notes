# Comprehensive Guide to Closures in Go

## Table of Contents
1. [Introduction to Closures](#introduction)
2. [How Closures Work](#how-closures-work)
3. [Practical Examples](#practical-examples)
4. [Common Patterns](#common-patterns)
5. [Advanced Techniques](#advanced-techniques)
6. [Gotchas and Best Practices](#gotchas)

## Introduction to Closures {#introduction}

A **closure** is a function value that references variables from outside its body. The function may access and assign to the referenced variables; in this sense, the function is "bound" to the variables.

In Go, closures are created when you define an anonymous function (or any function) that captures variables from its surrounding scope.

## How Closures Work {#how-closures-work}### Key Characteristics:

1. **Variable Capture**: Closures capture variables by reference, not by value
2. **State Preservation**: The captured variables persist between function calls
3. **Scope**: Closures can access variables from their enclosing scope

## Practical Examples {#practical-examples}## Common Patterns {#common-patterns}## Advanced Techniques {#advanced-techniques}## Gotchas and Best Practices {#gotchas}## Summary

### Key Takeaways:

**What Closures Are:**
- Functions that capture and reference variables from their enclosing scope
- Variables are captured by reference, not by value
- State persists between function calls

**Common Use Cases:**
1. **Encapsulation**: Hide internal state and expose only specific operations
2. **Factory Functions**: Generate specialized functions with pre-configured parameters
3. **Callbacks**: Pass behavior with context to other functions
4. **Iterators**: Maintain iteration state across multiple calls
5. **Memoization**: Cache expensive computations
6. **Middleware**: Wrap functions with additional behavior

**Critical Gotchas:**
1. **Loop Variable Capture**: Always create new variables in loops (automatic in Go 1.22+ `for` loops)
2. **Race Conditions**: Use mutexes when closures are accessed by multiple goroutines
3. **Memory Leaks**: Closures keep all captured variables in memory; copy only what you need
4. **Goroutine Traps**: Be careful when launching goroutines with closures in loops

**Best Practices:**
1. Document closure behavior, especially captured state
2. Use mutexes for thread-safe closures
3. Minimize captured variables to avoid memory leaks
4. Consider returning structs with closures for complex state management
5. Use closures for dependency injection and configuration

Closures are a powerful feature in Go that enable elegant solutions to many programming problems. Understanding how they work and their potential pitfalls will help you write more efficient and maintainable code.

package main

import "fmt"

func main() {
	// Example 1: Basic closure
	x := 10
	
	// This anonymous function is a closure because it references 'x'
	increment := func() int {
		x++
		return x
	}
	
	fmt.Println("Initial x:", x)           // 10
	fmt.Println("After increment:", increment()) // 11
	fmt.Println("After increment:", increment()) // 12
	fmt.Println("Current x:", x)           // 12
	
	// Example 2: Closure with parameter
	multiplier := func(factor int) int {
		return x * factor
	}
	
	fmt.Println("x * 5:", multiplier(5))   // 60 (12 * 5)
}

package main

import (
	"fmt"
	"strings"
)

// Example 1: Counter generator
func makeCounter() func() int {
	count := 0
	return func() int {
		count++
		return count
	}
}

// Example 2: Function factory with parameters
func makeMultiplier(factor int) func(int) int {
	return func(x int) int {
		return x * factor
	}
}

// Example 3: Closure for filtering
func makeFilter(prefix string) func(string) bool {
	return func(s string) bool {
		return strings.HasPrefix(s, prefix)
	}
}

// Example 4: Accumulator pattern
func makeAccumulator(initial int) func(int) int {
	sum := initial
	return func(x int) int {
		sum += x
		return sum
	}
}

func main() {
	fmt.Println("=== Counter Example ===")
	counter1 := makeCounter()
	counter2 := makeCounter()
	
	fmt.Println("Counter1:", counter1()) // 1
	fmt.Println("Counter1:", counter1()) // 2
	fmt.Println("Counter2:", counter2()) // 1 (independent state)
	fmt.Println("Counter1:", counter1()) // 3
	
	fmt.Println("\n=== Multiplier Example ===")
	double := makeMultiplier(2)
	triple := makeMultiplier(3)
	
	fmt.Println("Double 5:", double(5))   // 10
	fmt.Println("Triple 5:", triple(5))   // 15
	
	fmt.Println("\n=== Filter Example ===")
	words := []string{"apple", "banana", "apricot", "cherry", "avocado"}
	filterA := makeFilter("a")
	
	fmt.Println("Words starting with 'a':")
	for _, word := range words {
		if filterA(word) {
			fmt.Println("-", word)
		}
	}
	
	fmt.Println("\n=== Accumulator Example ===")
	acc := makeAccumulator(100)
	fmt.Println("Add 10:", acc(10))  // 110
	fmt.Println("Add 20:", acc(20))  // 130
	fmt.Println("Add 5:", acc(5))    // 135
}

package main

import (
	"fmt"
	"sync"
	"time"
)

// Pattern 1: Iterator
func makeIterator(slice []int) func() (int, bool) {
	index := -1
	return func() (int, bool) {
		index++
		if index < len(slice) {
			return slice[index], true
		}
		return 0, false
	}
}

// Pattern 2: Memoization
func memoize(fn func(int) int) func(int) int {
	cache := make(map[int]int)
	return func(n int) int {
		if result, found := cache[n]; found {
			fmt.Println("  (cached)")
			return result
		}
		result := fn(n)
		cache[n] = result
		return result
	}
}

// Expensive computation example
func fibonacci(n int) int {
	if n <= 1 {
		return n
	}
	return fibonacci(n-1) + fibonacci(n-2)
}

// Pattern 3: Debouncing
func debounce(d time.Duration, fn func()) func() {
	var timer *time.Timer
	var mu sync.Mutex
	
	return func() {
		mu.Lock()
		defer mu.Unlock()
		
		if timer != nil {
			timer.Stop()
		}
		
		timer = time.AfterFunc(d, fn)
	}
}

// Pattern 4: Middleware/Decorator
func logExecutionTime(fn func(int) int) func(int) int {
	return func(n int) int {
		start := time.Now()
		result := fn(n)
		elapsed := time.Since(start)
		fmt.Printf("Execution time: %v\n", elapsed)
		return result
	}
}

// Pattern 5: Partial Application
func partial(fn func(int, int) int, x int) func(int) int {
	return func(y int) int {
		return fn(x, y)
	}
}

func main() {
	fmt.Println("=== Iterator Pattern ===")
	numbers := []int{10, 20, 30, 40, 50}
	iter := makeIterator(numbers)
	
	for {
		value, ok := iter()
		if !ok {
			break
		}
		fmt.Println("Value:", value)
	}
	
	fmt.Println("\n=== Memoization Pattern ===")
	memoFib := memoize(fibonacci)
	
	fmt.Println("fib(10):", memoFib(10))
	fmt.Println("fib(10):", memoFib(10)) // Will use cache
	fmt.Println("fib(15):", memoFib(15))
	
	fmt.Println("\n=== Debouncing Pattern ===")
	action := func() {
		fmt.Println("Action executed at:", time.Now().Format("15:04:05.000"))
	}
	debouncedAction := debounce(500*time.Millisecond, action)
	
	fmt.Println("Triggering multiple times quickly...")
	for i := 0; i < 5; i++ {
		debouncedAction()
		time.Sleep(100 * time.Millisecond)
	}
	time.Sleep(600 * time.Millisecond) // Wait for debounced action
	
	fmt.Println("\n=== Decorator Pattern ===")
	timedFib := logExecutionTime(fibonacci)
	result := timedFib(20)
	fmt.Println("Result:", result)
	
	fmt.Println("\n=== Partial Application ===")
	add := func(a, b int) int { return a + b }
	add5 := partial(add, 5)
	
	fmt.Println("add5(10):", add5(10)) // 15
	fmt.Println("add5(20):", add5(20)) // 25
}

package main

import (
	"fmt"
	"sync"
)

// Technique 1: Closure with methods (returning struct with closures)
type Calculator struct {
	Add      func(int) int
	Subtract func(int) int
	GetValue func() int
	Reset    func()
}

func newCalculator(initial int) Calculator {
	value := initial
	var mu sync.Mutex
	
	return Calculator{
		Add: func(n int) int {
			mu.Lock()
			defer mu.Unlock()
			value += n
			return value
		},
		Subtract: func(n int) int {
			mu.Lock()
			defer mu.Unlock()
			value -= n
			return value
		},
		GetValue: func() int {
			mu.Lock()
			defer mu.Unlock()
			return value
		},
		Reset: func() {
			mu.Lock()
			defer mu.Unlock()
			value = initial
		},
	}
}

// Technique 2: Closure composition
func compose(f, g func(int) int) func(int) int {
	return func(x int) int {
		return f(g(x))
	}
}

// Technique 3: Closure-based event system
type EventHandler func(string)

type EventEmitter struct {
	handlers map[string][]EventHandler
	mu       sync.RWMutex
}

func newEventEmitter() *EventEmitter {
	return &EventEmitter{
		handlers: make(map[string][]EventHandler),
	}
}

func (e *EventEmitter) On(event string, handler EventHandler) func() {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	e.handlers[event] = append(e.handlers[event], handler)
	
	// Return unsubscribe function (closure)
	return func() {
		e.mu.Lock()
		defer e.mu.Unlock()
		
		handlers := e.handlers[event]
		for i, h := range handlers {
			// Compare function pointers
			if &h == &handler {
				e.handlers[event] = append(handlers[:i], handlers[i+1:]...)
				break
			}
		}
	}
}

func (e *EventEmitter) Emit(event string, data string) {
	e.mu.RLock()
	handlers := e.handlers[event]
	e.mu.RUnlock()
	
	for _, handler := range handlers {
		handler(data)
	}
}

// Technique 4: Recursive closures
func makeFibonacciGenerator() func() int {
	a, b := 0, 1
	
	return func() int {
		result := a
		a, b = b, a+b
		return result
	}
}

// Technique 5: Closure-based state machine
type State string

const (
	StateIdle    State = "idle"
	StateRunning State = "running"
	StatePaused  State = "paused"
	StateStopped State = "stopped"
)

func newStateMachine(initial State) (
	getState func() State,
	setState func(State) error,
) {
	currentState := initial
	validTransitions := map[State][]State{
		StateIdle:    {StateRunning},
		StateRunning: {StatePaused, StateStopped},
		StatePaused:  {StateRunning, StateStopped},
		StateStopped: {StateIdle},
	}
	
	getState = func() State {
		return currentState
	}
	
	setState = func(newState State) error {
		allowed := validTransitions[currentState]
		for _, s := range allowed {
			if s == newState {
				currentState = newState
				return nil
			}
		}
		return fmt.Errorf("invalid transition from %s to %s", currentState, newState)
	}
	
	return
}

func main() {
	fmt.Println("=== Calculator with Closures ===")
	calc := newCalculator(100)
	fmt.Println("Initial:", calc.GetValue())
	fmt.Println("Add 50:", calc.Add(50))
	fmt.Println("Subtract 30:", calc.Subtract(30))
	fmt.Println("Current:", calc.GetValue())
	calc.Reset()
	fmt.Println("After reset:", calc.GetValue())
	
	fmt.Println("\n=== Function Composition ===")
	double := func(x int) int { return x * 2 }
	addTen := func(x int) int { return x + 10 }
	
	doubleAndAddTen := compose(addTen, double)
	fmt.Println("doubleAndAddTen(5):", doubleAndAddTen(5)) // (5*2)+10 = 20
	
	fmt.Println("\n=== Event Emitter ===")
	emitter := newEventEmitter()
	
	unsubscribe := emitter.On("data", func(msg string) {
		fmt.Println("Handler 1 received:", msg)
	})
	
	emitter.On("data", func(msg string) {
		fmt.Println("Handler 2 received:", msg)
	})
	
	emitter.Emit("data", "Hello, World!")
	
	unsubscribe() // Remove first handler
	fmt.Println("\nAfter unsubscribe:")
	emitter.Emit("data", "Second message")
	
	fmt.Println("\n=== Fibonacci Generator ===")
	fib := makeFibonacciGenerator()
	fmt.Print("First 10 Fibonacci numbers: ")
	for i := 0; i < 10; i++ {
		fmt.Print(fib(), " ")
	}
	fmt.Println()
	
	fmt.Println("\n=== State Machine ===")
	getState, setState := newStateMachine(StateIdle)
	
	fmt.Println("Initial state:", getState())
	
	if err := setState(StateRunning); err != nil {
		fmt.Println("Error:", err)
	} else {
		fmt.Println("Transitioned to:", getState())
	}
	
	if err := setState(StateIdle); err != nil {
		fmt.Println("Error:", err) // This will error
	}
	
	if err := setState(StatePaused); err != nil {
		fmt.Println("Error:", err)
	} else {
		fmt.Println("Transitioned to:", getState())
	}
}

package main

import (
	"fmt"
	"sync"
)

// GOTCHA 1: Loop variable capture
func loopVariableProblem() {
	fmt.Println("=== Loop Variable Gotcha ===")
	
	// WRONG: All closures reference the same variable
	var funcs []func()
	for i := 0; i < 5; i++ {
		funcs = append(funcs, func() {
			fmt.Print(i, " ") // All will print 5
		})
	}
	
	fmt.Print("Wrong way: ")
	for _, f := range funcs {
		f()
	}
	fmt.Println()
	
	// CORRECT: Create a new variable in each iteration
	funcs = nil
	for i := 0; i < 5; i++ {
		i := i // Create new variable (Go 1.22+ does this automatically in for loops)
		funcs = append(funcs, func() {
			fmt.Print(i, " ")
		})
	}
	
	fmt.Print("Correct way: ")
	for _, f := range funcs {
		f()
	}
	fmt.Println()
	
	// ALTERNATIVE: Pass as parameter
	funcs = nil
	for i := 0; i < 5; i++ {
		funcs = append(funcs, func(val int) func() {
			return func() {
				fmt.Print(val, " ")
			}
		}(i))
	}
	
	fmt.Print("Parameter way: ")
	for _, f := range funcs {
		f()
	}
	fmt.Println()
}

// GOTCHA 2: Goroutine closure capture
func goroutineProblem() {
	fmt.Println("\n=== Goroutine Closure Gotcha ===")
	
	// WRONG: Race condition
	fmt.Println("Wrong way (may have race condition):")
	count := 0
	var wg sync.WaitGroup
	
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			count++ // Race condition!
		}()
	}
	wg.Wait()
	fmt.Println("Count:", count, "(may be incorrect)")
	
	// CORRECT: Use mutex
	fmt.Println("\nCorrect way (with mutex):")
	count = 0
	var mu sync.Mutex
	
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			mu.Lock()
			count++
			mu.Unlock()
		}()
	}
	wg.Wait()
	fmt.Println("Count:", count)
}

// GOTCHA 3: Memory leaks with closures
func memoryLeakExample() {
	fmt.Println("\n=== Memory Leak Gotcha ===")
	
	// WRONG: Closure keeps large slice in memory
	type Handler func()
	
	createHandler := func(data []int) Handler {
		// This closure captures the entire 'data' slice
		return func() {
			// Only using one element, but entire slice stays in memory
			fmt.Println("First element:", data[0])
		}
	}
	
	largeSlice := make([]int, 1000000)
	largeSlice[0] = 42
	handler := createHandler(largeSlice)
	// largeSlice stays in memory as long as handler exists!
	
	handler()
	
	// CORRECT: Only capture what you need
	createHandlerOptimized := func(data []int) Handler {
		firstElement := data[0] // Copy only what we need
		return func() {
			fmt.Println("First element:", firstElement)
		}
	}
	
	largeSlice2 := make([]int, 1000000)
	largeSlice2[0] = 42
	handlerOptimized := createHandlerOptimized(largeSlice2)
	// largeSlice2 can be garbage collected now
	
	handlerOptimized()
}

// BEST PRACTICE 1: Explicit closure state
type Counter struct {
	increment func() int
	decrement func() int
	value     func() int
}

func newCounter() Counter {
	val := 0
	var mu sync.Mutex
	
	return Counter{
		increment: func() int {
			mu.Lock()
			defer mu.Unlock()
			val++
			return val
		},
		decrement: func() int {
			mu.Lock()
			defer mu.Unlock()
			val--
			return val
		},
		value: func() int {
			mu.Lock()
			defer mu.Unlock()
			return val
		},
	}
}

// BEST PRACTICE 2: Document closure behavior
// NewRateLimiter returns a function that implements rate limiting.
// The returned function returns true if the action is allowed, false otherwise.
// It allows 'maxCalls' invocations per 'window' duration.
func newRateLimiter(maxCalls int) func() bool {
	calls := 0
	
	return func() bool {
		calls++
		if calls > maxCalls {
			return false
		}
		return true
	}
}

// BEST PRACTICE 3: Use closures for dependency injection
type Logger interface {
	Log(string)
}

type consoleLogger struct{}

func (c consoleLogger) Log(msg string) {
	fmt.Println("[LOG]", msg)
}

// Service accepts a logger via closure
func createService(log Logger) func(string) {
	return func(action string) {
		log.Log(fmt.Sprintf("Action performed: %s", action))
	}
}

func main() {
	loopVariableProblem()
	goroutineProblem()
	memoryLeakExample()
	
	fmt.Println("\n=== Best Practice: Explicit State ===")
	counter := newCounter()
	fmt.Println("Increment:", counter.increment())
	fmt.Println("Increment:", counter.increment())
	fmt.Println("Decrement:", counter.decrement())
	fmt.Println("Value:", counter.value())
	
	fmt.Println("\n=== Best Practice: Rate Limiter ===")
	limiter := newRateLimiter(3)
	for i := 1; i <= 5; i++ {
		if limiter() {
			fmt.Printf("Request %d: Allowed\n", i)
		} else {
			fmt.Printf("Request %d: Rate limited\n", i)
		}
	}
	
	fmt.Println("\n=== Best Practice: Dependency Injection ===")
	logger := consoleLogger{}
	service := createService(logger)
	service("User login")
	service("Data saved")
}

# Go Closures: Step-by-Step Memory & Value Semantics

## Part 1: Basic Closure - Capturing by Value

```go
func makeCounter() func() int {
    count := 0  // Local variable
    return func() int {
        count++
        return count
    }
}

counter := makeCounter()
```

### Memory Layout - Step 1: Initial State

```
STACK (makeCounter frame)                    HEAP
┌─────────────────────────┐                  
│  makeCounter()          │                  
│  ┌─────────────────┐   │                  
│  │ count: 0        │   │                  
│  │ (local var)     │   │                  
│  └─────────────────┘   │                  
│                         │                  
│  return → closure       │                  
└─────────────────────────┘                  
          │                                   
          │ (closure created, count escapes to heap)
          ▼                                   
                                    ┌─────────────────────┐
                                    │ CLOSURE OBJECT      │
                                    │ ┌─────────────────┐ │
                                    │ │ func() int {...}│ │
                                    │ │                 │ │
                                    │ │ Captured:       │ │
                                    │ │ count: 0 ──────┼─┼──► (pointer to heap)
                                    │ │                 │ │
                                    │ └─────────────────┘ │
                                    └─────────────────────┘
```

### Memory Layout - Step 2: After makeCounter() Returns

```
STACK (main frame)                           HEAP
┌─────────────────────────┐        ┌─────────────────────────┐
│  main()                 │        │ count: 0                │
│  ┌─────────────────┐   │        │ (escaped variable)      │
│  │ counter ────────┼───┼────┐   └─────────────────────────┘
│  └─────────────────┘   │    │              ▲
└─────────────────────────┘    │              │
                               │   ┌─────────────────────┐
                               └──►│ CLOSURE OBJECT      │
                                   │ ┌─────────────────┐ │
                                   │ │ func() int      │ │
                                   │ │ count: &heap ───┼─┘
                                   │ └─────────────────┘ │
                                   └─────────────────────┘

// makeCounter's stack frame is destroyed, but count survives on heap!
```

### Memory Layout - Step 3: Calling counter()

```
STACK                                        HEAP
┌─────────────────────────┐        ┌─────────────────────────┐
│  counter() execution    │        │ count: 1  (modified!)   │
│  (reads from heap)      │        │                         │
└─────────────────────────┘        └─────────────────────────┘
         │                                    ▲
         └────────────────────────────────────┘
              (closure accesses heap)
```

---

## Part 2: Call by Value vs Call by Reference

### Example Code:
```go
func demonstrateValueSemantics() {
    // Primitive types - Call by Value
    x := 10
    
    // Slice - Call by Value (but slice header contains pointer)
    s := []int{1, 2, 3}
    
    // Pointer - Call by Value (copying pointer value)
    p := &x
    
    closure := func() {
        x++      // Captures x by reference (pointer)
        s[0] = 99  // Slice header copied, but points to same array
        *p++     // Pointer copied, but points to same memory
    }
}
```

### Memory Diagram:

```
STACK (demonstrateValueSemantics)            HEAP
┌──────────────────────────────┐   
│  x: 10                       │   
│  ┌─────────┐                 │             ┌─────────────────┐
│  │ s (slice header)          │             │ Array: [1,2,3]  │
│  │ ┌────────────────┐        │             │                 │
│  │ │ ptr ───────────┼────────┼─────────────►                 │
│  │ │ len: 3         │        │             └─────────────────┘
│  │ │ cap: 3         │        │   
│  │ └────────────────┘        │   
│  └─────────┐                 │   
│            │                 │   
│  p: ───────┼─────────┐       │   
└────────────┼─────────┼───────┘   
             │         │
             │         └──────► points to x
             │
             ▼
    When closure is created:

HEAP (Closure Environment)
┌──────────────────────────────────────┐
│  CLOSURE CAPTURES:                   │
│                                      │
│  &x ────────► (pointer to x on heap)│  ← x ESCAPES to heap
│                                      │     because closure outlives
│  slice header (COPY):                │     the stack frame
│  ┌────────────────┐                  │
│  │ ptr ──────────►│  [1,2,3] array  │  ← Points to SAME array
│  │ len: 3         │                  │
│  │ cap: 3         │                  │
│  └────────────────┘                  │
│                                      │
│  pointer p (COPY): ──────► &x       │  ← Copy of pointer value
│                                      │     points to same location
└──────────────────────────────────────┘
```

---

## Part 3: Multiple Closures Sharing State

### Example Code:
```go
func makeCounters() (func(), func() int) {
    count := 0
    
    increment := func() {
        count++
    }
    
    getValue := func() int {
        return count
    }
    
    return increment, getValue
}

inc, get := makeCounters()
```

### Memory Diagram:

```
HEAP
┌────────────────────────────────────────────┐
│  SHARED CAPTURED VARIABLE:                 │
│  ┌────────────┐                            │
│  │ count: 0   │  ← Both closures reference │
│  └────────────┘     the SAME variable      │
│       ▲  ▲                                  │
│       │  │                                  │
│  ┌────┘  └────┐                            │
│  │            │                            │
│ ┌▼──────────┐ ┌▼──────────┐               │
│ │ CLOSURE 1 │ │ CLOSURE 2 │               │
│ │ increment │ │ getValue  │               │
│ │ func()    │ │ func()int │               │
│ └───────────┘ └───────────┘               │
└────────────────────────────────────────────┘
     ▲              ▲
     │              │
STACK│              │
┌────┴──────────────┴───┐
│  inc ───────────►│    │
│  get ───────────►│    │
└────────────────────────┘
```

---

## Part 4: Loop Variable Capture (Common Gotcha)

### Problematic Code:
```go
funcs := []func(){}
for i := 0; i < 3; i++ {
    funcs = append(funcs, func() {
        fmt.Println(i)  // Captures i by reference!
    })
}
```

### Memory Diagram - What Actually Happens:

```
HEAP
┌────────────────────────────────────────┐
│  Loop variable i: 3  (final value!)   │  ← ALL closures
│       ▲   ▲   ▲                        │     reference the
│       │   │   │                        │     SAME variable!
│  ┌────┘   │   └────┐                  │
│  │        │        │                  │
│ ┌▼──────┐┌▼──────┐┌▼──────┐          │
│ │func() ││func() ││func() │          │
│ │print i││print i││print i│          │
│ └───────┘└───────┘└───────┘          │
└────────────────────────────────────────┘

// When called: ALL print "3" !
```

### Correct Version:
```go
for i := 0; i < 3; i++ {
    i := i  // Create new variable in loop scope
    funcs = append(funcs, func() {
        fmt.Println(i)
    })
}
```

### Memory Diagram - Correct Behavior:

```
HEAP
┌────────────────────────────────────────┐
│  i_copy_0: 0  ← Closure 0              │
│       ▲                                 │
│  ┌────┘                                │
│ ┌▼──────┐                              │
│ │func() │                              │
│ │print 0│                              │
│ └───────┘                              │
│                                        │
│  i_copy_1: 1  ← Closure 1              │
│       ▲                                 │
│  ┌────┘                                │
│ ┌▼──────┐                              │
│ │func() │                              │
│ │print 1│                              │
│ └───────┘                              │
│                                        │
│  i_copy_2: 2  ← Closure 2              │
│       ▲                                 │
│  ┌────┘                                │
│ ┌▼──────┐                              │
│ │func() │                              │
│ │print 2│                              │
│ └───────┘                              │
└────────────────────────────────────────┘

// Each closure has its own copy!
```

---

## Part 5: Stack vs Heap Allocation Decision

### Go Compiler's Escape Analysis:

```
┌─────────────────────────────────────────────────────┐
│  ESCAPE ANALYSIS DECISION TREE                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Variable Created                                   │
│         │                                           │
│         ▼                                           │
│    Does it escape?                                  │
│    ┌─────────────┐                                  │
│    │             │                                  │
│   YES            NO                                 │
│    │             │                                  │
│    ▼             ▼                                  │
│  HEAP          STACK                                │
│                                                     │
│  Variable escapes if:                               │
│  • Returned from function                           │
│  • Captured by closure that outlives function       │
│  • Assigned to pointer that escapes                 │
│  • Passed to interface that escapes                 │
│  • Too large for stack                              │
└─────────────────────────────────────────────────────┘
```

### Example with Escape Analysis:

```go
func noEscape() {
    x := 42        // Stays on STACK
    println(x)
}

func escapes() *int {
    x := 42        // ESCAPES to HEAP
    return &x      // Because pointer is returned
}

func closureEscape() func() int {
    x := 42        // ESCAPES to HEAP
    return func() int {  // Because closure outlives function
        return x
    }
}
```

### Memory Layout:

```
SCENARIO 1: noEscape()
┌──────────────┐
│ STACK        │
│ ┌──────────┐ │
│ │ x: 42    │ │  ← Lives and dies on stack
│ └──────────┘ │
└──────────────┘

SCENARIO 2: escapes()
┌──────────────┐        ┌──────────────┐
│ STACK        │        │ HEAP         │
│ ┌──────────┐ │        │ ┌──────────┐ │
│ │ &x ──────┼─┼───────►│ │ x: 42    │ │
│ └──────────┘ │        │ └──────────┘ │
└──────────────┘        └──────────────┘
                        ↑
                        └─ Allocated here because
                           pointer escapes

SCENARIO 3: closureEscape()
┌──────────────┐        ┌──────────────────────┐
│ STACK        │        │ HEAP                 │
│ ┌──────────┐ │        │ ┌────────────────┐   │
│ │ closure ─┼─┼───────►│ │ CLOSURE        │   │
│ └──────────┘ │        │ │  captures: &x ─┼─┐ │
└──────────────┘        │ └────────────────┘ │ │
                        │          ┌─────────┘ │
                        │          ▼           │
                        │      ┌──────────┐    │
                        │      │ x: 42    │    │
                        │      └──────────┘    │
                        └──────────────────────┘
```

---

## Summary: Key Concepts

### 1. Closure Creation
- Closures capture variables from their enclosing scope
- Captured variables are accessed by **reference** (pointer)
- If closure outlives function, variables escape to heap

### 2. Call Semantics
- **Call by Value**: Go passes copies (primitives, structs, arrays)
- **Reference Types**: Slices, maps, channels contain pointers (copy header, share data)
- **Pointers**: Copied by value, but point to same memory

### 3. Memory Allocation
- **Stack**: Fast, automatic cleanup, function-scoped
- **Heap**: Slower, garbage collected, survives function return
- **Escape Analysis**: Compiler decides stack vs heap automatically

### 4. Common Patterns
- ✅ Capture loop variable: `i := i` creates new copy
- ✅ Multiple closures can share state
- ⚠️ Closures extend variable lifetime (heap allocation)
- ⚠️ Be aware of what you're capturing (value vs reference)

I'll create a comprehensive ASCII diagram showing how closures work in Go, covering call by value, call by reference, and memory allocation concepts.I've created a comprehensive ASCII diagram that covers all the key concepts you requested:

**What's included:**

1. **Basic Closure Mechanics** - Shows how variables escape from stack to heap when captured by closures

2. **Call by Value vs Call by Reference** - Demonstrates how Go's value semantics work with closures, including how slices and pointers behave

3. **Stack vs Heap Memory** - Detailed diagrams showing when variables are allocated on the stack versus when they escape to the heap

4. **Multiple Closures Sharing State** - Shows how multiple closures can reference the same captured variable

5. **Loop Variable Capture** - The classic gotcha with a before/after showing the correct solution

6. **Escape Analysis** - Decision tree and examples showing when Go moves variables to the heap

Each section includes both code examples and detailed ASCII memory diagrams showing the exact memory layout and pointer relationships. The diagrams progress step-by-step to show how memory changes as closures are created and executed.

