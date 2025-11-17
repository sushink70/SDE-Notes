# Built-in Go Functions for DSA Problems

Go provides several built-in functions that are extremely useful for solving data structure and algorithm problems. Here's an in-depth guide:

## 1. `len()` - Get Length

**Purpose**: Returns the number of elements in a collection or the number of bytes in a string.

**How to Use**:
```go
arr := []int{1, 2, 3, 4, 5}
length := len(arr)  // returns 5

str := "hello"
strLen := len(str)  // returns 5 (bytes, not characters!)
```

**Applicable to**:
- Arrays
- Slices
- Maps
- Strings (returns byte count)
- Channels

**Not Applicable to**:
- Integers, floats, booleans
- Structs
- Pointers (unless pointing to applicable types)

**Where to Use**:
- Loop boundaries: `for i := 0; i < len(arr); i++`
- Checking empty collections: `if len(slice) == 0`
- Array bound validation
- **Warning**: Don't call `len()` inside loop conditions repeatedly for slices that don't change - cache it for performance

## 2. `cap()` - Get Capacity

**Purpose**: Returns the capacity of a slice or channel (maximum number of elements it can hold without reallocation).

**How to Use**:
```go
slice := make([]int, 5, 10)  // length 5, capacity 10
fmt.Println(len(slice))  // 5
fmt.Println(cap(slice))  // 10
```

**Applicable to**:
- Slices
- Channels

**Not Applicable to**:
- Arrays (capacity equals length)
- Maps
- Strings

**Where to Use**:
- Memory optimization checks
- Understanding when slice will reallocate
- Pre-allocating slices: `slice := make([]int, 0, expectedSize)`
- Useful in problems where you know the final size beforehand

## 3. `append()` - Add Elements

**Purpose**: Adds elements to the end of a slice and returns the modified slice.

**How to Use**:
```go
slice := []int{1, 2, 3}
slice = append(slice, 4)        // [1, 2, 3, 4]
slice = append(slice, 5, 6, 7)  // [1, 2, 3, 4, 5, 6, 7]

// Append another slice
other := []int{8, 9}
slice = append(slice, other...)  // [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

**Critical**: Always assign the result back! `append()` may return a new slice if reallocation happens.

**Applicable to**:
- Slices only

**Where to Use**:
- Building dynamic arrays
- Stack implementations (push operation)
- Queue implementations
- Collecting results in recursion
- **In loops**: When collecting filtered or transformed elements

**Common Patterns**:
```go
// Stack push
stack = append(stack, element)

// Building result
result := []int{}
for _, v := range input {
    if condition(v) {
        result = append(result, v)
    }
}
```

## 4. `copy()` - Copy Slices

**Purpose**: Copies elements from source slice to destination slice.

**How to Use**:
```go
src := []int{1, 2, 3, 4, 5}
dst := make([]int, len(src))
n := copy(dst, src)  // returns number of elements copied

// Partial copy
dst2 := make([]int, 3)
copy(dst2, src)  // copies only first 3 elements
```

**Applicable to**:
- Slices only (both source and destination must be slices)

**Key Behavior**:
- Copies minimum of `len(src)` and `len(dst)` elements
- Returns number of elements copied
- Doesn't allocate new memory - destination must be pre-allocated

**Where to Use**:
- Cloning slices to avoid aliasing
- Implementing algorithms that need original data preserved
- Sliding window problems (shifting elements)
- **Important**: When you need independent copies to avoid mutation

**Example with Sliding Window**:
```go
// Removing element at index i
result := make([]int, 0, len(arr)-1)
result = append(result, arr[:i]...)
result = append(result, arr[i+1:]...)

// Or using copy
result := make([]int, len(arr)-1)
copy(result[:i], arr[:i])
copy(result[i:], arr[i+1:])
```

## 5. `delete()` - Remove from Map

**Purpose**: Removes a key-value pair from a map.

**How to Use**:
```go
m := map[string]int{"a": 1, "b": 2, "c": 3}
delete(m, "b")  // removes key "b"
delete(m, "z")  // safe even if key doesn't exist
```

**Applicable to**:
- Maps only

**Where to Use**:
- Hash table problems
- Frequency counting with cleanup
- Graph adjacency list modifications
- **In loops**: When you need to remove processed keys

**Pattern Example**:
```go
// Two Sum with map
func twoSum(nums []int, target int) []int {
    seen := make(map[int]int)
    for i, num := range nums {
        complement := target - num
        if j, ok := seen[complement]; ok {
            return []int{j, i}
        }
        seen[num] = i
    }
    return nil
}
```

## 6. `make()` - Allocate Memory

**Purpose**: Creates slices, maps, and channels with allocated memory.

**How to Use**:
```go
// Slice: make([]Type, length, capacity)
slice1 := make([]int, 5)      // length 5, capacity 5, all zeros
slice2 := make([]int, 0, 10)  // length 0, capacity 10

// Map: make(map[KeyType]ValueType, hint)
m := make(map[string]int)     // empty map
m2 := make(map[string]int, 100)  // with size hint

// Channel: make(chan Type, buffer)
ch := make(chan int)      // unbuffered
ch2 := make(chan int, 10) // buffered
```

**Applicable to**:
- Slices
- Maps
- Channels

**Where to Use**:
- **Pre-allocation for performance**: When you know the size
- Avoiding nil pointer issues with maps and slices
- **DP tables**: `dp := make([][]int, rows)`
- **Frequency maps**: `freq := make(map[rune]int)`

**Performance Tip**:
```go
// Good: Pre-allocate if size is known
result := make([]int, 0, n)
for i := 0; i < n; i++ {
    result = append(result, i)
}

// Less efficient: Multiple reallocations
result := []int{}
for i := 0; i < n; i++ {
    result = append(result, i)
}
```

## 7. `new()` - Allocate and Zero

**Purpose**: Allocates zeroed memory and returns a pointer.

**How to Use**:
```go
p := new(int)     // *int, points to 0
*p = 42

type Node struct {
    Val  int
    Next *Node
}
node := new(Node)  // All fields zeroed
```

**Applicable to**:
- Any type

**Difference from `make()`**:
- `new(T)` returns `*T` (pointer)
- `make(T)` returns `T` (initialized value) and only works with slices, maps, channels

**Where to Use**:
- Creating linked list nodes
- Tree nodes
- **Less common in DSA**: Usually prefer composite literals

**Better Pattern**:
```go
// Instead of new()
node := new(Node)
node.Val = 5

// Prefer this
node := &Node{Val: 5}
```

## 8. `panic()` and `recover()` - Error Handling

**Purpose**: `panic()` stops normal execution, `recover()` regains control.

**How to Use**:
```go
func divide(a, b int) int {
    if b == 0 {
        panic("division by zero")
    }
    return a / b
}

func safeDivide(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered: %v", r)
        }
    }()
    result = divide(a, b)
    return
}
```

**Where to Use in DSA**:
- **Rarely!** Most DSA problems don't need panic/recover
- Debugging: To catch unexpected states
- **Better**: Use proper error handling with return values

**Not Recommended for**:
- Normal control flow
- Expected errors (use error return values)
- Competitive programming (usually just handle cases)

## 9. Map Access with Comma-OK Idiom

**Purpose**: Check if a key exists in a map.

**How to Use**:
```go
m := map[string]int{"a": 1, "b": 0}

// Check existence
val, exists := m["a"]  // val=1, exists=true
val, exists = m["c"]   // val=0, exists=false

// Quick check
if val, ok := m["key"]; ok {
    // key exists, use val
}
```

**Where to Use**:
- Graph adjacency checks
- Frequency counting
- Duplicate detection
- Cache lookup (memoization)

**Pattern Examples**:
```go
// Check if number seen before
if _, seen := visited[num]; seen {
    return true
}
visited[num] = true

// Memoization
if result, cached := memo[key]; cached {
    return result
}
```

## 10. Range Loop

**Purpose**: Iterate over arrays, slices, maps, strings, channels.

**How to Use**:
```go
// Slice/Array: index, value
for i, v := range slice {
    fmt.Println(i, v)
}

// Map: key, value
for key, val := range m {
    fmt.Println(key, val)
}

// String: index, rune (not byte!)
for i, char := range "hello" {
    fmt.Println(i, char)  // char is rune
}

// Ignore index or value
for _, v := range slice {}  // ignore index
for i := range slice {}     // ignore value
```

**Applicable to**:
- Arrays
- Slices
- Maps
- Strings (iterates by rune, not byte!)
- Channels

**Critical Points**:
- **Value is a copy**: Modifying `v` doesn't change the original
- **Map iteration order is random**: Don't rely on order
- **String range**: Gives runes (Unicode code points), not bytes

**Where to Use**:
```go
// Correct: Modify by index
for i := range slice {
    slice[i] *= 2
}

// Wrong: This doesn't modify original
for _, v := range slice {
    v *= 2  // only modifies the copy!
}

// Map iteration (order undefined)
for key := range graph {
    // Process nodes
}
```

## 11. Slicing Operations

**Purpose**: Create sub-slices from arrays or slices.

**Syntax**: `slice[low:high:max]`

**How to Use**:
```go
arr := []int{0, 1, 2, 3, 4, 5}

arr[1:4]      // [1, 2, 3] - from index 1 to 3
arr[:3]       // [0, 1, 2] - from start to index 2
arr[3:]       // [3, 4, 5] - from index 3 to end
arr[:]        // [0, 1, 2, 3, 4, 5] - entire slice

// Full slice expression (controls capacity)
arr[1:3:4]    // [1, 2] with cap=3
```

**Where to Use**:
- Divide and conquer algorithms
- Two pointers technique
- Sliding window problems
- **Warning**: Slices share underlying array!

**Common Patterns**:
```go
// Binary Search - divide
mid := len(arr) / 2
left := arr[:mid]
right := arr[mid:]

// Remove element at index i (creates new underlying array)
arr = append(arr[:i], arr[i+1:]...)

// Sliding window
for i := 0; i <= len(arr)-k; i++ {
    window := arr[i:i+k]
    // process window
}
```

**Critical Memory Consideration**:
```go
// This keeps the entire original array in memory!
huge := make([]byte, 1000000)
small := huge[:5]  // small still references huge array

// To truly create independent slice
small := make([]byte, 5)
copy(small, huge[:5])  // Now huge can be garbage collected
```

## Best Practices for DSA Problems

1. **Pre-allocate when size is known**: `make([]int, 0, expectedSize)`
2. **Always assign append result**: `slice = append(slice, val)`
3. **Use comma-ok for map access**: `if val, ok := m[key]; ok {}`
4. **Cache `len()` in hot loops** if slice doesn't change
5. **Be careful with slice aliasing**: Use `copy()` when needed
6. **Remember map iteration is random**: Don't rely on order
7. **Use range for readability**: But modify by index when needed
8. **Avoid panic/recover**: Use proper error handling

These built-in functions form the foundation of implementing efficient algorithms in Go. Understanding when and how to use them properly is crucial for solving DSA problems effectively!