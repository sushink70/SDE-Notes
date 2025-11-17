I'll explain how loops work in Go, covering all the key aspects you mentioned.

## Loop Basics in Go

Go has only **one loop construct**: the `for` loop. It's surprisingly versatile and replaces `while`, `do-while`, and traditional `for` loops from other languages.

## Basic Forms

### 1. Traditional Three-Component Loop
```go
for i := 0; i < 10; i++ {
    fmt.Println(i)
}
```
- **Initialization** (`i := 0`): Runs once before the loop starts
- **Condition** (`i < 10`): Checked before each iteration
- **Post statement** (`i++`): Runs after each iteration
- Variable `i` is scoped to the loop only

### 2. While-Style Loop
```go
i := 0
for i < 10 {
    fmt.Println(i)
    i++
}
```
- Only has a condition
- Variable must be declared outside

### 3. Infinite Loop
```go
for {
    // runs forever unless you break
    if someCondition {
        break
    }
}
```

### 4. Range Loop (Iterating Collections)
```go
nums := []int{10, 20, 30}
for index, value := range nums {
    fmt.Printf("Index: %d, Value: %d\n", index, value)
}
```

## How Variables Are Handled

### Scope and Lifetime
```go
// i is scoped to the loop
for i := 0; i < 3; i++ {
    fmt.Println(i)
}
// i is not accessible here

// But if declared outside:
j := 0
for j < 3 {
    j++
}
// j is still accessible here (value is 3)
```

### Important Gotcha: Loop Variable Reuse
```go
var funcs []func()
for i := 0; i < 3; i++ {
    // Before Go 1.22, this captured the same variable
    // Now each iteration gets its own copy
    funcs = append(funcs, func() {
        fmt.Println(i)
    })
}

for _, f := range funcs {
    f() // Prints: 0, 1, 2 (in Go 1.22+)
}
```

**Note**: In Go 1.22+, loop variables are per-iteration. In older versions, you needed to create a copy manually.

## Range Loop Details

### How Range Works

**Slices and Arrays:**
```go
nums := []int{10, 20, 30}

// Both index and value
for i, v := range nums {
    fmt.Println(i, v)
}

// Index only
for i := range nums {
    fmt.Println(i)
}

// Value only (ignore index with _)
for _, v := range nums {
    fmt.Println(v)
}
```

**Maps:**
```go
m := map[string]int{"a": 1, "b": 2}

for key, value := range m {
    fmt.Println(key, value)
}
// Note: Map iteration order is randomized!
```

**Strings:**
```go
s := "Hello, 世界"
for i, r := range s {
    // i is byte position, r is rune (Unicode code point)
    fmt.Printf("%d: %c\n", i, r)
}
```

**Channels:**
```go
ch := make(chan int)
go func() {
    ch <- 1
    ch <- 2
    close(ch)
}()

for v := range ch {
    fmt.Println(v) // Receives until channel is closed
}
```

### Range Creates Copies
```go
type Point struct {
    X, Y int
}

points := []Point{{1, 2}, {3, 4}}

// v is a COPY of each point
for _, v := range points {
    v.X = 100 // This doesn't modify the original!
}

// To modify originals, use indices:
for i := range points {
    points[i].X = 100
}
```

## Control Flow Statements

### break
```go
for i := 0; i < 10; i++ {
    if i == 5 {
        break // Exit the loop immediately
    }
}
```

### continue
```go
for i := 0; i < 10; i++ {
    if i%2 == 0 {
        continue // Skip to next iteration
    }
    fmt.Println(i) // Only prints odd numbers
}
```

### Labels (for nested loops)
```go
outer:
for i := 0; i < 3; i++ {
    for j := 0; j < 3; j++ {
        if i == 1 && j == 1 {
            break outer // Breaks out of outer loop
        }
        fmt.Println(i, j)
    }
}
```

## Common Patterns

### Iterating with Multiple Variables
```go
for i, j := 0, 10; i < j; i, j = i+1, j-1 {
    fmt.Println(i, j)
}
```

### Conditional Loops
```go
scanner := bufio.NewScanner(os.Stdin)
for scanner.Scan() {
    line := scanner.Text()
    if line == "quit" {
        break
    }
    fmt.Println(line)
}
```

### Counter with Condition
```go
count := 0
for count < 100 && someOtherCondition() {
    count += processSomething()
}
```

## Performance Considerations

1. **Range over slice is efficient** - Go optimizes this well
2. **Pre-allocate slices when size is known:**
   ```go
   result := make([]int, 0, expectedSize)
   for i := 0; i < n; i++ {
       result = append(result, i)
   }
   ```

3. **Avoid unnecessary allocations in loops:**
   ```go
   // Bad: creates new slice every iteration
   for i := 0; i < n; i++ {
       temp := []int{i}
       process(temp)
   }
   
   // Good: reuse
   temp := make([]int, 1)
   for i := 0; i < n; i++ {
       temp[0] = i
       process(temp)
   }
   ```

## Key Takeaways

- Go has **only `for`**, but it's flexible enough for all loop needs
- Loop variables in `for i := ...` are **scoped to the loop**
- `range` creates **copies** of values - use indices to modify originals
- Map iteration order is **randomized** for security reasons
- Use `break` and `continue` with **labels** for nested loops
- Since Go 1.22, loop variables are **per-iteration** (fixes common closure bugs)

The simplicity of having just one loop construct makes Go loops easy to understand, while `range` makes iterating over collections clean and idiomatic.