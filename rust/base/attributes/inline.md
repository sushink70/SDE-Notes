// === WHAT #[inline] DOES ===

```rust
// Without #[inline] - Normal function call
fn add_normal(a: i32, b: i32) -> i32 {
    a + b
}

// With #[inline] - Suggests inlining
#[inline]
fn add_inline(a: i32, b: i32) -> i32 {
    a + b
}

// With #[inline(always)] - Forces inlining
#[inline(always)]
fn add_always_inline(a: i32, b: i32) -> i32 {
    a + b
}

// With #[inline(never)] - Prevents inlining
#[inline(never)]
fn add_never_inline(a: i32, b: i32) -> i32 {
    a + b
}

fn main() {
    println!("=== FUNCTION CALL OVERHEAD DEMONSTRATION ===\n");
    
    // What happens WITHOUT inlining:
    // 1. Push arguments onto stack
    // 2. Jump to function address
    // 3. Execute function
    // 4. Pop return value from stack
    // 5. Jump back to caller
    
    let result1 = add_normal(5, 3);
    println!("Normal function result: {}", result1);
    
    // What happens WITH inlining:
    // The function call is replaced with the actual code:
    // let result2 = 5 + 3;  // No function call overhead!
    
    let result2 = add_inline(5, 3);
    println!("Inline function result: {}", result2);
    
    demonstrate_real_world_impact();
    demonstrate_derive_inline_usage();
}

fn demonstrate_real_world_impact() {
    println!("\n=== PERFORMANCE IMPACT DEMONSTRATION ===");
    
    const ITERATIONS: usize = 10_000_000;
    
    // Test normal function calls
    let start = std::time::Instant::now();
    let mut sum = 0;
    for i in 0..ITERATIONS {
        sum += add_normal(i as i32, 1);
    }
    let normal_time = start.elapsed();
    println!("Normal function calls: {:?}, sum: {}", normal_time, sum);
    
    // Test inline function calls
    let start = std::time::Instant::now();
    let mut sum = 0;
    for i in 0..ITERATIONS {
        sum += add_inline(i as i32, 1);
    }
    let inline_time = start.elapsed();
    println!("Inline function calls: {:?}, sum: {}", inline_time, sum);
    
    if normal_time > inline_time {
        let speedup = normal_time.as_nanos() as f64 / inline_time.as_nanos() as f64;
        println!("Speedup from inlining: {:.2}x faster", speedup);
    }
}

// === WHY DERIVE MACROS USE #[inline] ===

#[derive(Clone, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

// The generated code looks like this:
impl Clone for Point {
    #[inline]  // ← This is why it's here!
    fn clone(&self) -> Point {
        Point {
            x: self.x,  // Simple field copy
            y: self.y,  // Simple field copy
        }
    }
}

impl PartialEq for Point {
    #[inline]  // ← And here too!
    fn eq(&self, other: &Point) -> bool {
        self.x == other.x && self.y == other.y  // Simple comparison
    }
}

fn demonstrate_derive_inline_usage() {
    println!("\n=== WHY DERIVES USE #[inline] ===");
    
    let point1 = Point { x: 10, y: 20 };
    let point2 = Point { x: 10, y: 20 };
    
    // Without #[inline], this would be:
    // 1. Call Point::clone() function
    // 2. Function copies x and y
    // 3. Return new Point
    // 4. Function call overhead
    
    let cloned = point1.clone();
    
    // With #[inline], the compiler replaces the call with:
    // let cloned = Point { x: point1.x, y: point1.y };
    // No function call overhead!
    
    println!("Cloned point: {:?}", cloned);
    
    // Same with equality:
    // Without #[inline]: function call overhead
    // With #[inline]: direct comparison in place
    let are_equal = point1 == point2;
    println!("Points equal: {}", are_equal);
    
    demonstrate_inline_in_loops();
}

fn demonstrate_inline_in_loops() {
    println!("\n=== INLINE IMPACT IN LOOPS ===");
    
    let points: Vec<Point> = (0..1000)
        .map(|i| Point { x: i, y: i * 2 })
        .collect();
    
    // This loop benefits HUGELY from inlining
    let start = std::time::Instant::now();
    let mut cloned_points = Vec::new();
    for point in &points {
        // If clone() wasn't inlined, this would be 1000 function calls
        // With inlining, it becomes direct field copies
        cloned_points.push(point.clone());
    }
    let clone_time = start.elapsed();
    println!("Cloning 1000 points: {:?}", clone_time);
    
    // Equality checks in loops also benefit
    let start = std::time::Instant::now();
    let mut equal_count = 0;
    for (i, point) in points.iter().enumerate() {
        if i < cloned_points.len() {
            // Without inlining: 1000 function calls
            // With inlining: direct field comparisons
            if *point == cloned_points[i] {
                equal_count += 1;
            }
        }
    }
    let eq_time = start.elapsed();
    println!("Equality checks: {:?}, equal count: {}", eq_time, equal_count);
}

// === DIFFERENT INLINE VARIANTS ===

struct InlineExamples;

impl InlineExamples {
    // Default: compiler decides based on optimization level
    fn method_default(&self) -> i32 { 42 }
    
    // Suggest inlining (most common in derives)
    #[inline]
    fn method_inline(&self) -> i32 { 42 }
    
    // Force inlining (use carefully!)
    #[inline(always)]
    fn method_always(&self) -> i32 { 42 }
    
    // Prevent inlining (for debugging or code size)
    #[inline(never)]
    fn method_never(&self) -> i32 { 42 }
    
    // Complex function - inlining might hurt performance
    #[inline(never)]  // Large functions shouldn't be inlined
    fn complex_calculation(&self, data: &[i32]) -> i32 {
        let mut result = 0;
        for &value in data {
            result += value * value;
            result %= 1000000;
            // ... lots of complex logic
        }
        result
    }
    
    // Simple accessor - perfect for inlining
    #[inline]
    fn get_value(&self) -> i32 {
        42  // Trivial function, great candidate for inlining
    }
}

// === WHEN TO USE EACH VARIANT ===

fn inline_guidelines() {
    println!("\n=== INLINE USAGE GUIDELINES ===");
    
    println!("✅ Good candidates for #[inline]:");
    println!("   - Simple getters/setters");
    println!("   - Mathematical operations");
    println!("   - Trait methods with simple implementations");
    println!("   - Functions called in tight loops");
    
    println!("\n❌ Bad candidates for #[inline]:");
    println!("   - Large functions (increase code size)");
    println!("   - Recursive functions");
    println!("   - Functions with complex control flow");
    println!("   - Rarely called functions");
    
    println!("\n🔧 Compiler optimization levels:");
    println!("   - Debug builds: Less aggressive inlining");
    println!("   - Release builds: More aggressive inlining");
    println!("   - LTO (Link Time Optimization): Even more inlining");
}

// === REAL ASSEMBLY COMPARISON ===

// You can see the difference with:
// cargo rustc --release -- --emit asm
// or use: https://godbolt.org/

#[no_mangle]
pub fn call_normal_function() -> i32 {
    add_normal(5, 3)
}

#[no_mangle] 
pub fn call_inline_function() -> i32 {
    add_inline(5, 3)
}

// The assembly for call_normal_function will show:
//   call add_normal
//   
// The assembly for call_inline_function will show:
//   mov eax, 8    ; Direct result, no function call!

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_inline_behavior() {
        // These should produce identical results
        assert_eq!(add_normal(10, 20), add_inline(10, 20));
        assert_eq!(add_normal(10, 20), add_always_inline(10, 20));
        assert_eq!(add_normal(10, 20), add_never_inline(10, 20));
        
        // But potentially different performance characteristics
        println!("All inline variants produce same results");
    }
}

fn main() {
    main();
    inline_guidelines();
}
```

Great question! The `#[inline]` attribute is a compiler hint that's crucial for performance optimization. Let me break it down in detail:## Key Points About `#[inline]`:

### **What It Does**
1. **Suggests to the compiler**: "Replace function calls with the actual function body"
2. **Eliminates call overhead**: No stack frame setup, no jump instructions
3. **Enables further optimizations**: The compiler can optimize across the inlined boundary

### **Why Derive Macros Use It**
The generated methods from `#[derive()]` are typically:
- **Very simple** (just field operations)
- **Called frequently** (in loops, comparisons)
- **Small code size** (won't bloat the binary much)

Perfect candidates for inlining!

### **Performance Impact**
```rust
// Without inlining:
let result = point1.clone();
// Becomes: call clone_function, setup stack, copy fields, return, cleanup

// With inlining:
let result = point1.clone();  
// Becomes: Point { x: point1.x, y: point1.y }  (direct copy)
```

### **The Variants**
- `#[inline]` - "Please inline if it makes sense"
- `#[inline(always)]` - "Always inline, even if it seems bad"
- `#[inline(never)]` - "Never inline this function"
- No attribute - "Compiler decides based on optimization level"

### **Trade-offs**
- ✅ **Pros**: Faster execution, enables more optimizations
- ❌ **Cons**: Larger binary size, longer compile times, potential instruction cache pressure

The reason derive macros use `#[inline]` is that the generated methods are almost always simple, frequently called operations that benefit significantly from inlining with minimal downsides.