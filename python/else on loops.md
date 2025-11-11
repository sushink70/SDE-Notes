# Comprehensive Guide to `else` Clauses on Loops

## Python: `else` with Loops

Python has a unique feature where loops (`for` and `while`) can have an `else` clause. This is often misunderstood but very powerful.

### How it Works

**The `else` block executes when the loop completes normally** (without encountering a `break` statement).

### `for...else` Examples

```python
# Example 1: Basic for...else (else WILL execute)
print("Example 1: Normal loop completion")
for i in range(5):
    print(f"  Iteration {i}")
else:
    print("  Loop completed normally!")
    # This runs because we never hit a 'break'

print("\n" + "="*50 + "\n")

# Example 2: for...else with break (else will NOT execute)
print("Example 2: Loop with break")
for i in range(5):
    print(f"  Iteration {i}")
    if i == 2:
        print("  Breaking at i=2")
        break  # Exit the loop early
else:
    print("  This will NOT print - we hit a break!")

print("\n" + "="*50 + "\n")

# Example 3: Practical use - Searching for a value
print("Example 3: Searching in a list")
numbers = [1, 3, 5, 7, 9]
search_for = 4

for num in numbers:
    if num == search_for:
        print(f"  Found {search_for}!")
        break
else:
    # This executes only if we never found the number
    print(f"  {search_for} not found in the list")

print("\n" + "="*50 + "\n")

# Example 4: Checking if a number is prime
print("Example 4: Prime number checker")
def is_prime(n):
    if n < 2:
        return False
    
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            print(f"  {n} is divisible by {i}")
            return False  # Found a divisor, not prime
    else:
        # Loop completed without finding divisors
        print(f"  No divisors found for {n}")
        return True

print(f"Is 17 prime? {is_prime(17)}")
print(f"Is 15 prime? {is_prime(15)}")
```

### `while...else` Examples

```python
# Example 5: while...else (else WILL execute)
print("\nExample 5: Normal while loop")
count = 0
while count < 3:
    print(f"  Count: {count}")
    count += 1
else:
    print("  While loop finished normally!")

print("\n" + "="*50 + "\n")

# Example 6: while...else with break (else will NOT execute)
print("Example 6: While loop with break")
count = 0
while count < 10:
    print(f"  Count: {count}")
    if count == 2:
        print("  Breaking early!")
        break
    count += 1
else:
    print("  This won't print - we broke out!")

print("\n" + "="*50 + "\n")

# Example 7: Practical use - User input validation
print("Example 7: Password validation (simulated)")
def validate_password(password, max_attempts=3):
    attempts = 0
    correct_password = "secret123"
    
    while attempts < max_attempts:
        # In real code, you'd get user input here
        if password == correct_password:
            print("  Password correct!")
            break
        attempts += 1
        print(f"  Attempt {attempts} failed")
    else:
        # Executed only if all attempts exhausted without break
        print("  Maximum attempts reached. Account locked.")
        return False
    
    return True

validate_password("wrong", 3)  # Will exhaust attempts
print()
validate_password("secret123", 3)  # Will break early
```

### Common Pitfalls

```python
# Pitfall 1: 'continue' does NOT prevent else execution
print("\nPitfall: continue vs break")
for i in range(5):
    if i == 2:
        continue  # Skip this iteration, but keep looping
    print(f"  i = {i}")
else:
    print("  Else STILL executes with 'continue'!")
    # The loop completed normally, just skipped some iterations

print("\n" + "="*50 + "\n")

# Pitfall 2: Empty loops still trigger else
print("Empty loop:")
for i in range(0):  # Loop body never executes
    print("This never runs")
else:
    print("  Else DOES execute - loop completed 'normally' (just zero iterations)")
```

---

## Rust: NO `else` Clause on Loops

**Rust does not have `else` clauses for loops.** You need to use different patterns to achieve similar functionality.

### Rust Alternatives

```rust
// Example 1: Using a flag variable (most common approach)
fn search_with_flag() {
    let numbers = vec![1, 3, 5, 7, 9];
    let search_for = 4;
    let mut found = false;  // Flag to track if we found it
    
    for num in &numbers {
        if *num == search_for {
            println!("Found {}!", search_for);
            found = true;
            break;
        }
    }
    
    // Check the flag after the loop
    if !found {
        println!("{} not found in the list", search_for);
    }
}

// Example 2: Using iterator methods (more idiomatic Rust)
fn search_with_iterator() {
    let numbers = vec![1, 3, 5, 7, 9];
    let search_for = 4;
    
    // Use 'any' to check if any element matches
    if numbers.iter().any(|&x| x == search_for) {
        println!("Found {}!", search_for);
    } else {
        println!("{} not found", search_for);
    }
}

// Example 3: Prime checker using a flag
fn is_prime(n: u32) -> bool {
    if n < 2 {
        return false;
    }
    
    let mut is_prime = true;  // Assume prime until proven otherwise
    
    for i in 2..=(n as f64).sqrt() as u32 {
        if n % i == 0 {
            println!("{} is divisible by {}", n, i);
            is_prime = false;
            break;
        }
    }
    
    if is_prime {
        println!("No divisors found for {}", n);
    }
    
    is_prime
}

// Example 4: Using a block expression that returns a value
fn search_with_block() {
    let numbers = vec![1, 3, 5, 7, 9];
    let search_for = 4;
    
    // The entire block evaluates to a boolean
    let found = {
        let mut result = false;
        for num in &numbers {
            if *num == search_for {
                result = true;
                break;
            }
        }
        result  // Return the result
    };
    
    if found {
        println!("Found {}", search_for);
    } else {
        println!("{} not found", search_for);
    }
}

// Example 5: More idiomatic - using find()
fn search_idiomatic() {
    let numbers = vec![1, 3, 5, 7, 9];
    let search_for = 4;
    
    // find() returns Option<&T>
    match numbers.iter().find(|&&x| x == search_for) {
        Some(_) => println!("Found {}!", search_for),
        None => println!("{} not found", search_for),
    }
}

fn main() {
    search_with_flag();
    search_with_iterator();
    println!("Is 17 prime? {}", is_prime(17));
    println!("Is 15 prime? {}", is_prime(15));
    search_with_block();
    search_idiomatic();
}
```

---

## Go: NO `else` Clause on Loops

**Go also does not have `else` clauses for loops.** Similar to Rust, you use flags or other patterns.

### Go Alternatives

```go
package main

import (
    "fmt"
    "math"
)

// Example 1: Using a flag variable (most common approach)
func searchWithFlag() {
    numbers := []int{1, 3, 5, 7, 9}
    searchFor := 4
    found := false  // Flag to track if we found it
    
    for _, num := range numbers {
        if num == searchFor {
            fmt.Printf("Found %d!\n", searchFor)
            found = true
            break
        }
    }
    
    // Check the flag after the loop
    if !found {
        fmt.Printf("%d not found in the list\n", searchFor)
    }
}

// Example 2: Using a function that returns early
func searchInList(numbers []int, target int) bool {
    for _, num := range numbers {
        if num == target {
            fmt.Printf("Found %d!\n", target)
            return true  // Found it, return early
        }
    }
    
    // Only reaches here if not found
    fmt.Printf("%d not found\n", target)
    return false
}

// Example 3: Prime checker using a flag
func isPrime(n int) bool {
    if n < 2 {
        return false
    }
    
    isPrime := true  // Assume prime until proven otherwise
    limit := int(math.Sqrt(float64(n)))
    
    for i := 2; i <= limit; i++ {
        if n%i == 0 {
            fmt.Printf("%d is divisible by %d\n", n, i)
            isPrime = false
            break
        }
    }
    
    if isPrime {
        fmt.Printf("No divisors found for %d\n", n)
    }
    
    return isPrime
}

// Example 4: Using labeled break for nested loops
func findInMatrix() {
    matrix := [][]int{
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9},
    }
    searchFor := 5
    found := false
    
    // Label the outer loop
OuterLoop:
    for i, row := range matrix {
        for j, val := range row {
            if val == searchFor {
                fmt.Printf("Found %d at position [%d][%d]\n", searchFor, i, j)
                found = true
                break OuterLoop  // Break out of both loops
            }
        }
    }
    
    if !found {
        fmt.Printf("%d not found in matrix\n", searchFor)
    }
}

// Example 5: Using defer to ensure cleanup (advanced pattern)
func processWithCleanup() {
    completed := false
    
    // Defer runs after the function exits
    defer func() {
        if !completed {
            fmt.Println("Processing was interrupted (did not complete)")
        } else {
            fmt.Println("Processing completed successfully")
        }
    }()
    
    for i := 0; i < 5; i++ {
        fmt.Printf("Processing item %d\n", i)
        if i == 2 {
            // Early return - completed stays false
            return
        }
    }
    
    // Mark as completed if we get here
    completed = true
}

func main() {
    fmt.Println("Example 1: Search with flag")
    searchWithFlag()
    
    fmt.Println("\nExample 2: Search with function")
    searchInList([]int{1, 3, 5, 7, 9}, 7)
    
    fmt.Println("\nExample 3: Prime checker")
    fmt.Printf("Is 17 prime? %v\n", isPrime(17))
    fmt.Printf("Is 15 prime? %v\n", isPrime(15))
    
    fmt.Println("\nExample 4: Find in matrix")
    findInMatrix()
    
    fmt.Println("\nExample 5: Process with cleanup")
    processWithCleanup()
}
```

---

## Summary Comparison

| Feature | Python | Rust | Go |
|---------|--------|------|-----|
| **`else` on loops** | ✅ Yes (`for`/`while`) | ❌ No | ❌ No |
| **When `else` runs** | When loop completes without `break` | N/A | N/A |
| **Alternative pattern** | Not needed | Flag variables or iterator methods | Flag variables or early returns |
| **Most idiomatic** | Use `else` directly | Use iterator methods (`.find()`, `.any()`) | Use flag variables or functions with early returns |

### Key Takeaways

1. **Python's `else` on loops** is unique and runs only when the loop completes normally (no `break`)
2. **`continue` does NOT prevent `else`** - only `break` does
3. **Rust and Go** don't have this feature, but you can achieve the same logic with:
   - Flag variables
   - Iterator methods (Rust)
   - Early returns from functions
   - Block expressions that return values