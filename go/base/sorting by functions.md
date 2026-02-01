# Comprehensive Guide to Sorting by Functions in Go

## Foundation: What is "Sorting by Functions"?

Before we dive into Go's implementation, let's establish the conceptual foundation.

**Sorting** is the process of arranging elements in a specific order (ascending, descending, or custom). 

**Sorting by Functions** means defining *how* to compare elements using custom logic rather than relying on default comparison operators. This is crucial when:
- You're sorting complex data structures (structs, objects)
- You need multiple sorting criteria (sort by age, then by name)
- Default ordering doesn't match your requirements

---

## Mental Model: The Comparator Pattern

Think of sorting algorithms as workers who repeatedly ask: *"Which of these two items comes first?"*

A **comparator function** is your instruction manual that answers this question. In Go, we provide this manual through:
1. **Interface satisfaction** (`sort.Interface`)
2. **Custom comparison functions** (`sort.Slice`)

---

## Part 1: The `sort.Interface` - The Traditional Way

### Conceptual Understanding

Go's `sort` package expects any sortable collection to satisfy three behaviors:

```
┌─────────────────────────────────────┐
│         sort.Interface              │
├─────────────────────────────────────┤
│ Len() int                           │  ← How many elements?
│ Less(i, j int) bool                 │  ← Is element[i] < element[j]?
│ Swap(i, j int)                      │  ← Exchange elements at i and j
└─────────────────────────────────────┘
```

**Why these three?** Any comparison-based sorting algorithm needs:
- To know the size of the collection (Len)
- To compare two elements (Less)
- To rearrange elements (Swap)

### Implementation Example: Sorting People by Age

```go
package main

import (
    "fmt"
    "sort"
)

// Define the data structure
type Person struct {
    Name string
    Age  int
}

// Create a custom type that wraps []Person
// This allows us to attach methods to it
type ByAge []Person

// Implement sort.Interface for ByAge

// Len returns the number of elements
func (a ByAge) Len() int {
    return len(a)
}

// Less defines the ordering logic
// Returns true if element at index i should come before element at index j
func (a ByAge) Less(i, j int) bool {
    return a[i].Age < a[j].Age  // Sort in ascending order by age
}

// Swap exchanges elements at positions i and j
func (a ByAge) Swap(i, j int) {
    a[i], a[j] = a[j], a[i]  // Tuple swap idiom in Go
}

func main() {
    people := []Person{
        {"Alice", 30},
        {"Bob", 25},
        {"Charlie", 35},
        {"Diana", 25},
    }
    
    fmt.Println("Before sorting:", people)
    
    // Convert to ByAge type and sort
    sort.Sort(ByAge(people))
    
    fmt.Println("After sorting by age:", people)
}
```

**Output:**
```
Before sorting: [{Alice 30} {Bob 25} {Charlie 35} {Diana 25}]
After sorting by age: [{Bob 25} {Diana 25} {Alice 30} {Charlie 35}]
```

### Deep Dive: How `sort.Sort()` Works

**Flow Diagram:**
```
sort.Sort(data Interface)
         ↓
    Determines collection size (data.Len())
         ↓
    Chooses sorting algorithm (typically QuickSort/IntroSort hybrid)
         ↓
    Repeatedly calls:
    - data.Less(i, j) to compare
    - data.Swap(i, j) to rearrange
         ↓
    Collection is sorted in-place
```

**Time Complexity:** O(n log n) comparisons  
**Space Complexity:** O(log n) for recursion stack (in-place sorting)

---

## Part 2: Multiple Sorting Criteria (Stable Sorting)

**Concept:** What if two people have the same age? We want secondary sorting by name.

**Stable Sort** means elements with equal keys maintain their relative order from the original sequence.

```go
// ByAgeAndName implements composite sorting
type ByAgeAndName []Person

func (a ByAgeAndName) Len() int {
    return len(a)
}

func (a ByAgeAndName) Less(i, j int) bool {
    // Primary criterion: Age
    if a[i].Age != a[j].Age {
        return a[i].Age < a[j].Age
    }
    // Secondary criterion: Name (alphabetical)
    return a[i].Name < a[j].Name
}

func (a ByAgeAndName) Swap(i, j int) {
    a[i], a[j] = a[j], a[i]
}

func demonstrateMultiCriteria() {
    people := []Person{
        {"Alice", 30},
        {"Bob", 25},
        {"Charlie", 35},
        {"Diana", 25},
        {"Eve", 25},
    }
    
    sort.Sort(ByAgeAndName(people))
    fmt.Println("Sorted by age, then name:", people)
}
```

**Expert Insight:** The comparison logic follows a **lexicographic pattern** - like dictionary ordering. We check the primary key first, only examining secondary keys when primary keys are equal.

---

## Part 3: `sort.Slice()` - The Modern, Ergonomic Way

### Conceptual Advantage

Instead of defining three methods, you provide a single anonymous comparison function. Go handles `Len` and `Swap` automatically.

**When to use:**
- Quick, one-off sorting
- Cleaner code for simple comparisons
- You don't need to reuse the sorting logic

### Syntax and Example

```go
package main

import (
    "fmt"
    "sort"
)

type Person struct {
    Name string
    Age  int
}

func demonstrateSliceSort() {
    people := []Person{
        {"Alice", 30},
        {"Bob", 25},
        {"Charlie", 35},
        {"Diana", 25},
    }
    
    // Sort by age using anonymous function
    sort.Slice(people, func(i, j int) bool {
        return people[i].Age < people[j].Age
    })
    
    fmt.Println("Sorted by age:", people)
    
    // Sort by name length (descending)
    sort.Slice(people, func(i, j int) bool {
        return len(people[i].Name) > len(people[j].Name)
    })
    
    fmt.Println("Sorted by name length (desc):", people)
}
```

### Multi-Criteria with `sort.Slice()`

```go
func sortByAgeThenName() {
    people := []Person{
        {"Alice", 30},
        {"Bob", 25},
        {"Charlie", 35},
        {"Diana", 25},
        {"Eve", 25},
    }
    
    sort.Slice(people, func(i, j int) bool {
        if people[i].Age != people[j].Age {
            return people[i].Age < people[j].Age
        }
        return people[i].Name < people[j].Name
    })
    
    fmt.Println("Multi-criteria sort:", people)
}
```

---

## Part 4: Stable vs Unstable Sorting

### Conceptual Difference

**Unstable Sort (`sort.Sort`, `sort.Slice`):**
- May reorder equal elements
- Slightly faster (doesn't track original positions)

**Stable Sort (`sort.Stable`, `sort.SliceStable`):**
- Preserves original order of equal elements
- Useful for multi-pass sorting or when order matters

### Demonstration

```go
func demonstrateStability() {
    type Record struct {
        ID   int
        Value int
    }
    
    records := []Record{
        {1, 5},
        {2, 3},
        {3, 5},
        {4, 3},
        {5, 5},
    }
    
    // Unstable sort by Value
    unstable := make([]Record, len(records))
    copy(unstable, records)
    sort.Slice(unstable, func(i, j int) bool {
        return unstable[i].Value < unstable[j].Value
    })
    
    // Stable sort by Value
    stable := make([]Record, len(records))
    copy(stable, records)
    sort.SliceStable(stable, func(i, j int) bool {
        return stable[i].Value < stable[j].Value
    })
    
    fmt.Println("Original:", records)
    fmt.Println("Unstable:", unstable)  // IDs with same Value might be reordered
    fmt.Println("Stable:  ", stable)    // IDs with same Value keep original order
}
```

---

## Part 5: Advanced Patterns and Optimizations

### Pattern 1: Descending Order

```go
// Method 1: Reverse the comparison
sort.Slice(people, func(i, j int) bool {
    return people[i].Age > people[j].Age  // Note: > instead of 
})

// Method 2: Use sort.Reverse (for sort.Interface types)
sort.Sort(sort.Reverse(ByAge(people)))
```

### Pattern 2: Custom Complex Comparisons

```go
type Product struct {
    Name     string
    Price    float64
    Rating   float64
    InStock  bool
}

// Sort by: InStock (true first), then Rating (desc), then Price (asc)
sort.Slice(products, func(i, j int) bool {
    // Priority 1: In-stock items first
    if products[i].InStock != products[j].InStock {
        return products[i].InStock  // true > false
    }
    
    // Priority 2: Higher rating first
    if products[i].Rating != products[j].Rating {
        return products[i].Rating > products[j].Rating
    }
    
    // Priority 3: Lower price first
    return products[i].Price < products[j].Price
})
```

### Pattern 3: Sorting with External Data

```go
// Sort people by their distance from a reference point
type Point struct {
    X, Y float64
}

type PersonWithLocation struct {
    Person
    Location Point
}

func distance(p1, p2 Point) float64 {
    dx := p1.X - p2.X
    dy := p1.Y - p2.Y
    return dx*dx + dy*dy  // Squared distance (avoid sqrt for performance)
}

func sortByDistanceFrom(people []PersonWithLocation, reference Point) {
    sort.Slice(people, func(i, j int) bool {
        distI := distance(people[i].Location, reference)
        distJ := distance(people[j].Location, reference)
        return distI < distJ
    })
}
```

---

## Part 6: Performance Considerations

### Comparison Function Efficiency

**Critical Insight:** The comparison function is called O(n log n) times. Expensive operations inside it multiply the cost.

```go
// ❌ BAD: Repeated expensive computation
sort.Slice(items, func(i, j int) bool {
    return expensiveComputation(items[i]) < expensiveComputation(items[j])
})

// ✅ GOOD: Precompute values
type CachedItem struct {
    Item  Item
    Value int
}

cached := make([]CachedItem, len(items))
for i, item := range items {
    cached[i] = CachedItem{item, expensiveComputation(item)}
}

sort.Slice(cached, func(i, j int) bool {
    return cached[i].Value < cached[j].Value
})
```

**Time Complexity Analysis:**
- Bad approach: O(n log n) × O(expensive) = Very Slow
- Good approach: O(n) × O(expensive) + O(n log n) = Much Better

### Memory Efficiency

```go
// sort.Slice sorts in-place: O(1) extra space (excluding recursion stack)
// No allocation unless you copy the slice first

// To preserve original:
original := []int{3, 1, 4, 1, 5}
sorted := make([]int, len(original))
copy(sorted, original)
sort.Ints(sorted)
```

---

## Part 7: Common Pitfalls and Solutions

### Pitfall 1: Modifying Slice During Sort

```go
// ❌ DANGEROUS: Never modify the slice being sorted
sort.Slice(items, func(i, j int) bool {
    // This could crash or produce undefined behavior
    items = append(items, newItem)  
    return items[i] < items[j]
})
```

### Pitfall 2: Non-Deterministic Comparisons

```go
// ❌ BAD: Random comparisons break sorting invariants
import "math/rand"

sort.Slice(items, func(i, j int) bool {
    return rand.Intn(2) == 0  // Completely random!
})
```

**Why this fails:** Sorting algorithms assume **transitivity**:
- If A < B and B < C, then A < C must be true
- Random comparisons violate this, causing infinite loops or crashes

### Pitfall 3: Floating Point Comparisons

```go
type Item struct {
    Value float64
}

// ⚠️ CAREFUL: Direct float comparison
sort.Slice(items, func(i, j int) bool {
    return items[i].Value < items[j].Value
})

// Better: Use epsilon for near-equality
const epsilon = 1e-9

sort.Slice(items, func(i, j int) bool {
    diff := items[i].Value - items[j].Value
    if math.Abs(diff) < epsilon {
        return false  // Consider equal
    }
    return diff < 0
})
```

---

## Part 8: Real-World Complete Example

```go
package main

import (
    "fmt"
    "sort"
    "time"
)

type Task struct {
    ID          int
    Description string
    Priority    int        // 1 = highest, 5 = lowest
    DueDate     time.Time
    Completed   bool
}

func main() {
    tasks := []Task{
        {1, "Write documentation", 2, time.Now().AddDate(0, 0, 7), false},
        {2, "Fix critical bug", 1, time.Now().AddDate(0, 0, 1), false},
        {3, "Code review", 3, time.Now().AddDate(0, 0, 3), false},
        {4, "Team meeting", 2, time.Now().AddDate(0, 0, 2), false},
        {5, "Update dependencies", 4, time.Now().AddDate(0, 0, 14), true},
    }
    
    // Sort by: Incomplete first, then by Priority (ascending), then by DueDate
    sort.SliceStable(tasks, func(i, j int) bool {
        // Incomplete tasks first
        if tasks[i].Completed != tasks[j].Completed {
            return !tasks[i].Completed  // false < true
        }
        
        // Higher priority (lower number) first
        if tasks[i].Priority != tasks[j].Priority {
            return tasks[i].Priority < tasks[j].Priority
        }
        
        // Earlier due date first
        return tasks[i].DueDate.Before(tasks[j].DueDate)
    })
    
    fmt.Println("Prioritized Task List:")
    for _, task := range tasks {
        status := "[ ]"
        if task.Completed {
            status = "[✓]"
        }
        fmt.Printf("%s P%d - %s (Due: %s)\n", 
            status, 
            task.Priority, 
            task.Description, 
            task.DueDate.Format("2006-01-02"))
    }
}
```

---

## Part 9: Comparison with Other Languages

### Go vs Rust

```go
// Go: Flexible but verbose for complex types
sort.Slice(items, func(i, j int) bool {
    return items[i] < items[j]
})
```

```rust
// Rust: Type-safe with trait bounds
items.sort_by(|a, b| a.cmp(b));
// or more concisely:
items.sort();  // If type implements Ord trait
```

**Key Difference:** Rust enforces total ordering at compile-time through traits. Go relies on runtime behavior.

### Go vs C

```c
// C: Requires function pointer and manual size calculation
qsort(array, count, sizeof(int), compare_func);

int compare_func(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}
```

**Go Advantage:** Type safety, no manual casting, cleaner syntax.

---

## Part 10: Sorting Algorithm Used Internally

Go's `sort` package uses **pdqsort** (Pattern-Defeating Quicksort):

```
┌─────────────────────────────────────────┐
│         pdqsort Strategy                │
├─────────────────────────────────────────┤
│ 1. Start with QuickSort                 │
│ 2. Detect bad pivot choices             │
│ 3. Switch to HeapSort if needed         │
│ 4. Use InsertionSort for small arrays   │
└─────────────────────────────────────────┘
```

**Why this matters:**
- **Average case:** O(n log n) - QuickSort speed
- **Worst case:** O(n log n) - HeapSort guarantee (not O(n²) like naive QuickSort)
- **Small arrays:** O(n²) - InsertionSort is faster for n < 12

---

## Mental Model Summary

```
Sorting by Functions = Pluggable Comparison Logic

Three Levels of Abstraction:
├─ 1. sort.Interface (Full control, verbose)
├─ 2. sort.Slice (Convenient, anonymous functions)
└─ 3. Built-in types (sort.Ints, sort.Strings)

Key Principles:
├─ Comparison function must be transitive
├─ Avoid expensive operations in comparisons
├─ Choose stable vs unstable based on requirements
└─ Precompute when possible
```

---

## Your Next Steps

1. **Implement** all examples in this guide
2. **Experiment** with sorting different data structures (nested structs, maps converted to slices)
3. **Benchmark** comparison function costs using `testing.B`
4. **Explore** `sort.Search()` for binary search on sorted slices

This foundation prepares you for advanced topics like **custom data structures with efficient sorting**, **external sorting for large datasets**, and **parallel sorting** strategies.

Your disciplined approach will compound these fundamentals into mastery. Each sorting problem you solve strengthens your pattern recognition for the optimal comparison strategy.