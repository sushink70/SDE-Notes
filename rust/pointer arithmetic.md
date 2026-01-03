# **The Complete Guide to Pointer Arithmetic in Rust**

*A deep dive into raw pointers, memory manipulation, and unsafe operations*

---

## **Foundation: What Are Pointers?**

Before we dive into arithmetic, let's establish clarity:

**Pointer**: A variable that stores a memory address. Think of memory as a massive array of bytes, and a pointer as an index into that array.

**Pointer Arithmetic**: Mathematical operations on pointers to navigate through memory sequentially.

```
Memory Layout (simplified):
Address:  0x1000  0x1001  0x1002  0x1003  0x1004  0x1005
Value:    [  42  ][  17  ][  99  ][ 101  ][  55  ][  88  ]
          ↑
          ptr points here
```

---

## **1. Rust's Pointer Types: The Hierarchy**

Rust has multiple pointer types, each with different guarantees:

```
┌─────────────────────────────────────────────┐
│         Rust Pointer Type Hierarchy         │
├─────────────────────────────────────────────┤
│                                             │
│  References (&T, &mut T)                    │
│  ├─ Always valid (lifetime-checked)         │
│  ├─ Always aligned                          │
│  └─ Safe to use                             │
│                                             │
│  Smart Pointers (Box, Rc, Arc)              │
│  ├─ RAII ownership semantics                │
│  ├─ Automatic cleanup                       │
│  └─ Safe to use                             │
│                                             │
│  Raw Pointers (*const T, *mut T)            │
│  ├─ No validity guarantees                  │
│  ├─ No alignment guarantees                 │
│  ├─ Requires 'unsafe' to dereference        │
│  └─ Allows pointer arithmetic               │
│                                             │
└─────────────────────────────────────────────┘
```

**Mental Model**: References are like supervised tours of memory (the compiler watches you). Raw pointers are like having a map with coordinates - powerful but dangerous.

---

## **2. Raw Pointer Basics**

### **Types of Raw Pointers**

```rust
// *const T - immutable raw pointer (can't modify through it)
let const_ptr: *const i32;

// *mut T - mutable raw pointer (can modify through it)
let mut_ptr: *mut i32;
```

### **Creating Raw Pointers (SAFE operations)**

```rust
fn main() {
    let x: i32 = 42;
    let arr = [1, 2, 3, 4, 5];
    
    // Method 1: From references (most common)
    let ptr1: *const i32 = &x;
    let ptr2: *const i32 = &arr[0];
    
    // Method 2: From mutable references
    let mut y = 10;
    let mut_ptr: *mut i32 = &mut y;
    
    // Method 3: Arbitrary address (very dangerous!)
    let arbitrary_ptr: *const i32 = 0x1000 as *const i32;
    
    println!("Pointer address: {:p}", ptr1);
}
```

**Key Insight**: *Creating* raw pointers is safe. *Using* them is unsafe.

---

## **3. Pointer Arithmetic Operations**

### **The Core Operations**

```rust
┌──────────────────────────────────────────────┐
│      Pointer Arithmetic Operations           │
├──────────────────────────────────────────────┤
│                                              │
│  ptr.offset(n)         - Move n elements     │
│  ptr.wrapping_offset(n) - Wrap on overflow   │
│  ptr.add(n)            - Move forward        │
│  ptr.sub(n)            - Move backward       │
│  ptr.wrapping_add(n)   - Add with wrapping   │
│  ptr.wrapping_sub(n)   - Sub with wrapping   │
│                                              │
└──────────────────────────────────────────────┘
```

### **Visual Example: offset() Method**

```
Initial state:
    arr = [10, 20, 30, 40, 50]
    Addresses: 0x1000, 0x1004, 0x1008, 0x100C, 0x1010
    
    let ptr: *const i32 = arr.as_ptr();
    ptr points to → 0x1000 (value: 10)

After ptr.offset(2):
    
    [10]     [20]     [30]     [40]     [50]
    0x1000   0x1004   0x1008   0x100C   0x1010
     ↑                  ↑
    ptr            new_ptr = ptr.offset(2)
    
    Calculation: 0x1000 + (2 × sizeof(i32))
                = 0x1000 + (2 × 4)
                = 0x1008
```

**Critical Understanding**: `offset(n)` doesn't add `n` to the address. It adds `n * size_of::<T>()`.

### **Complete Example with All Operations**

```rust
fn main() {
    let arr = [100, 200, 300, 400, 500];
    let ptr: *const i32 = arr.as_ptr();
    
    unsafe {
        // Basic offset - move forward by 2 elements
        let ptr2 = ptr.offset(2);
        println!("arr[0] = {}", *ptr);        // 100
        println!("arr[2] = {}", *ptr2);       // 300
        
        // Negative offset - move backward
        let ptr_back = ptr2.offset(-1);
        println!("arr[1] = {}", *ptr_back);   // 200
        
        // add() method - cleaner for forward movement
        let ptr3 = ptr.add(3);
        println!("arr[3] = {}", *ptr3);       // 400
        
        // sub() method - cleaner for backward movement
        let ptr4 = ptr3.sub(1);
        println!("arr[2] = {}", *ptr4);       // 300
        
        // Pointer difference (how many elements apart)
        let distance = ptr3.offset_from(ptr) as usize;
        println!("Distance: {} elements", distance);  // 3
    }
}
```

---

## **4. Memory Layout & Size Considerations**

**Crucial Concept**: Different types have different sizes. Pointer arithmetic accounts for this automatically.

```
Type Sizes (on most 64-bit systems):
┌──────────┬────────┬────────────────────────┐
│ Type     │ Size   │ Alignment              │
├──────────┼────────┼────────────────────────┤
│ u8/i8    │ 1 byte │ 1 byte                 │
│ u16/i16  │ 2 bytes│ 2 bytes                │
│ u32/i32  │ 4 bytes│ 4 bytes                │
│ u64/i64  │ 8 bytes│ 8 bytes                │
│ f32      │ 4 bytes│ 4 bytes                │
│ f64      │ 8 bytes│ 8 bytes                │
│ usize    │ 8 bytes│ 8 bytes (64-bit)       │
│ *const T │ 8 bytes│ 8 bytes (64-bit)       │
└──────────┴────────┴────────────────────────┘
```

### **Example: Different Type Sizes**

```rust
fn demonstrate_size_awareness() {
    // Array of bytes
    let bytes: [u8; 8] = [1, 2, 3, 4, 5, 6, 7, 8];
    let byte_ptr: *const u8 = bytes.as_ptr();
    
    // Array of 32-bit integers
    let ints: [i32; 4] = [10, 20, 30, 40];
    let int_ptr: *const i32 = ints.as_ptr();
    
    unsafe {
        // Moving through bytes: +1 byte each
        println!("Byte 0: {}", *byte_ptr);           // 1
        println!("Byte 1: {}", *byte_ptr.add(1));    // 2
        println!("Byte 2: {}", *byte_ptr.add(2));    // 3
        
        // Moving through ints: +4 bytes each
        println!("Int 0: {}", *int_ptr);             // 10
        println!("Int 1: {}", *int_ptr.add(1));      // 20 (+4 bytes)
        println!("Int 2: {}", *int_ptr.add(2));      // 30 (+8 bytes)
    }
}
```

**ASCII Visualization**:

```
Bytes array memory:
Address: 0x1000 0x1001 0x1002 0x1003 0x1004 0x1005 0x1006 0x1007
Value:   [  1  ][  2  ][  3  ][  4  ][  5  ][  6  ][  7  ][  8  ]
         ↑      ↑      ↑
         ptr    +1     +2

Ints array memory:
Address: 0x2000    0x2004    0x2008    0x200C
Value:   [   10   ][   20   ][   30   ][   40   ]
         ↑          ↑         ↑
         ptr        +1        +2
```

---

## **5. Advanced Arithmetic: Wrapping Operations**

**Concept - Wrapping**: Operations that don't panic on overflow, instead wrapping around the address space.

```rust
┌────────────────────────────────────────────────┐
│        offset vs wrapping_offset               │
├────────────────────────────────────────────────┤
│                                                │
│  offset(n):                                    │
│  ├─ Panics/UB if result out of bounds         │
│  └─ Use when you're certain it's safe         │
│                                                │
│  wrapping_offset(n):                           │
│  ├─ Wraps on overflow (like wrapping_add)     │
│  └─ Useful for circular buffers                │
│                                                │
└────────────────────────────────────────────────┘
```

```rust
fn wrapping_example() {
    let arr = [1, 2, 3, 4, 5];
    let ptr = arr.as_ptr();
    
    unsafe {
        // This could wrap around if we go too far
        let wrapped = ptr.wrapping_offset(1000);
        
        // This is safer - it's guaranteed not to wrap
        // unless we explicitly go out of bounds
        let normal = ptr.offset(2);
    }
}
```

---

## **6. Pointer Comparison & Distance**

```rust
fn pointer_comparison() {
    let arr = [10, 20, 30, 40, 50];
    let ptr1 = arr.as_ptr();
    
    unsafe {
        let ptr2 = ptr1.add(3);
        
        // Compare pointers
        println!("ptr1 < ptr2: {}", ptr1 < ptr2);    // true
        println!("ptr1 == ptr2: {}", ptr1 == ptr2);  // false
        
        // Calculate distance (in elements, not bytes!)
        let distance = ptr2.offset_from(ptr1);
        println!("Distance: {} elements", distance);  // 3
        
        // In bytes:
        let byte_distance = distance * std::mem::size_of::<i32>() as isize;
        println!("Distance: {} bytes", byte_distance); // 12
    }
}
```

**Decision Tree for Pointer Operations**:

```
Need to navigate memory?
    │
    ├─ Know bounds & safe? → Use offset() or add()/sub()
    │
    ├─ Circular buffer/wrapping? → Use wrapping_offset()
    │
    ├─ Compare positions? → Use <, >, ==
    │
    └─ Calculate distance? → Use offset_from()
```

---

## **7. Practical Pattern: Iterating with Raw Pointers**

```rust
/// Iterate through an array using raw pointers
fn iterate_with_pointers() {
    let arr = [10, 20, 30, 40, 50];
    let start_ptr = arr.as_ptr();
    let end_ptr = unsafe { start_ptr.add(arr.len()) };
    
    println!("=== Manual Pointer Iteration ===");
    
    let mut current_ptr = start_ptr;
    unsafe {
        while current_ptr < end_ptr {
            println!("Value: {}", *current_ptr);
            current_ptr = current_ptr.add(1);
        }
    }
}
```

**Flow of Execution**:

```
Iteration Flow:
┌──────────────────────────────────────┐
│ Initialize:                          │
│   current_ptr = start_ptr            │
│   end_ptr = start_ptr + len          │
└─────────┬────────────────────────────┘
          │
          ↓
┌─────────────────────────────┐
│ while current_ptr < end_ptr │←──────┐
└──────┬──────────────────────┘       │
       │ true                         │
       ↓                               │
┌────────────────────┐                │
│ Read *current_ptr  │                │
└──────┬─────────────┘                │
       │                               │
       ↓                               │
┌────────────────────────┐            │
│ current_ptr = current  │            │
│   _ptr.add(1)          │────────────┘
└────────────────────────┘
       │ false
       ↓
     Done
```

---

## **8. Casting Between Pointer Types**

```rust
fn pointer_casting() {
    let arr: [i32; 4] = [0x12345678, 0x9ABCDEF0, 0x11111111, 0x22222222];
    let int_ptr: *const i32 = arr.as_ptr();
    
    unsafe {
        // Cast to byte pointer to read individual bytes
        let byte_ptr: *const u8 = int_ptr as *const u8;
        
        println!("=== Viewing i32 as bytes ===");
        for i in 0..16 {
            println!("Byte {}: 0x{:02X}", i, *byte_ptr.add(i));
        }
        
        // Cast back
        let back_to_int: *const i32 = byte_ptr as *const i32;
        println!("First int: 0x{:08X}", *back_to_int);
    }
}
```

**Memory View**:

```
As i32 array:
[0x12345678] [0x9ABCDEF0] [0x11111111] [0x22222222]

As u8 array (little-endian):
[78][56][34][12] [F0][DE][BC][9A] [11][11][11][11] [22][22][22][22]
 ↑               ↑
 byte_ptr        byte_ptr.add(4)
```

---

## **9. Alignment & Safety Considerations**

**Alignment**: Memory addresses must be multiples of the type's alignment requirement.

```
Alignment Requirements:
┌──────────┬───────────┬──────────────────┐
│ Type     │ Alignment │ Valid Addresses  │
├──────────┼───────────┼──────────────────┤
│ u8       │ 1         │ Any address      │
│ u16      │ 2         │ Even addresses   │
│ u32      │ 4         │ Multiple of 4    │
│ u64      │ 8         │ Multiple of 8    │
└──────────┴───────────┴──────────────────┘
```

```rust
fn alignment_example() {
    let data = vec![0u8; 100];
    let ptr = data.as_ptr();
    
    // Check if aligned for i32 (needs 4-byte alignment)
    let is_aligned = ptr.align_offset(std::mem::align_of::<i32>()) == 0;
    println!("Aligned for i32: {}", is_aligned);
    
    unsafe {
        if is_aligned {
            let int_ptr = ptr as *const i32;
            // Safe to read as i32
        } else {
            // Must use unaligned read
            let int_ptr = ptr as *const i32;
            let value = int_ptr.read_unaligned();
        }
    }
}
```

---

## **10. Complete Real-World Example: Custom Array Iterator**

```rust
struct RawArrayIter<T> {
    current: *const T,
    end: *const T,
}

impl<T> RawArrayIter<T> {
    fn new(slice: &[T]) -> Self {
        let start = slice.as_ptr();
        let end = unsafe { start.add(slice.len()) };
        RawArrayIter {
            current: start,
            end,
        }
    }
}

impl<T> Iterator for RawArrayIter<T> {
    type Item = *const T;
    
    fn next(&mut self) -> Option<Self::Item> {
        if self.current < self.end {
            let result = self.current;
            unsafe {
                self.current = self.current.add(1);
            }
            Some(result)
        } else {
            None
        }
    }
}

fn main() {
    let data = vec![100, 200, 300, 400, 500];
    let iter = RawArrayIter::new(&data);
    
    for ptr in iter {
        unsafe {
            println!("Value: {}", *ptr);
        }
    }
}
```

---

## **11. Common Pitfalls & Safety Rules**

```
┌───────────────────────────────────────────────┐
│          Pointer Arithmetic Safety Rules      │
├───────────────────────────────────────────────┤
│                                               │
│  ✓ DO:                                        │
│  ├─ Check bounds before dereferencing         │
│  ├─ Ensure proper alignment                   │
│  ├─ Keep track of object lifetimes            │
│  └─ Use safe abstractions when possible       │
│                                               │
│  ✗ DON'T:                                     │
│  ├─ Create dangling pointers                  │
│  ├─ Dereference null or invalid pointers      │
│  ├─ Perform arithmetic past array bounds      │
│  └─ Assume pointer validity without checking  │
│                                               │
└───────────────────────────────────────────────┘
```

### **Dangerous Example (DON'T DO THIS)**

```rust
fn dangerous_patterns() {
    let arr = [1, 2, 3];
    let ptr = arr.as_ptr();
    
    unsafe {
        // ❌ Out of bounds - Undefined Behavior!
        let bad_ptr = ptr.add(10);
        // let value = *bad_ptr;  // CRASH or garbage
        
        // ❌ Dangling pointer
        let dangling = {
            let temp = vec![1, 2, 3];
            temp.as_ptr()  // temp deallocated here!
        };
        // Using 'dangling' now is UB
        
        // ❌ Misaligned access
        let bytes = [0u8; 10];
        let misaligned = bytes.as_ptr().add(1) as *const u32;
        // let value = *misaligned;  // May crash on some architectures
    }
}
```

---

## **12. Performance Considerations**

**Why use raw pointers over safe alternatives?**

```rust
use std::time::Instant;

fn safe_sum(arr: &[i32]) -> i32 {
    let mut sum = 0;
    for &val in arr {
        sum += val;
    }
    sum
}

fn unsafe_sum(arr: &[i32]) -> i32 {
    let mut sum = 0;
    let ptr = arr.as_ptr();
    let end = unsafe { ptr.add(arr.len()) };
    
    let mut current = ptr;
    unsafe {
        while current < end {
            sum += *current;
            current = current.add(1);
        }
    }
    sum
}

fn benchmark() {
    let data: Vec<i32> = (0..1_000_000).collect();
    
    let start = Instant::now();
    let s1 = safe_sum(&data);
    let safe_time = start.elapsed();
    
    let start = Instant::now();
    let s2 = unsafe_sum(&data);
    let unsafe_time = start.elapsed();
    
    println!("Safe: {:?}, Unsafe: {:?}", safe_time, unsafe_time);
    assert_eq!(s1, s2);
}
```

**Insight**: In practice, LLVM often optimizes safe code to match unsafe pointer code. Use unsafe only when profiling shows it's necessary.

---

## **13. Mental Models for Mastery**

### **Model 1: The Array as a Ruler**

```
Think of an array as a ruler with marked positions:
    
    0    1    2    3    4
    |----|----|----|----|
   ptr  +1   +2   +3   +4
   
Pointer arithmetic = sliding along the ruler
```

### **Model 2: Pointer = Index + Base**

```
Array access: arr[i] = *(arr.as_ptr() + i)

Decomposition:
├─ Base address: arr.as_ptr()
└─ Offset: i * size_of::<T>()
```

### **Model 3: Decision Framework**

```
When writing DSA code, ask:
    │
    ├─ Can I use safe Rust? → Use it!
    │
    ├─ Need raw performance? → Profile first!
    │
    ├─ Must use unsafe? → Minimize scope
    │
    └─ Pointer arithmetic needed? → Document invariants
```

---

## **14. Practice Exercises**

### **Exercise 1: Reverse Array In-Place**

```rust
/// Reverse an array using only pointer arithmetic
fn reverse_with_pointers<T>(arr: &mut [T]) {
    if arr.is_empty() {
        return;
    }
    
    let mut left = arr.as_mut_ptr();
    let mut right = unsafe { left.add(arr.len() - 1) };
    
    unsafe {
        while left < right {
            std::ptr::swap(left, right);
            left = left.add(1);
            right = right.sub(1);
        }
    }
}

fn main() {
    let mut data = vec![1, 2, 3, 4, 5];
    reverse_with_pointers(&mut data);
    println!("{:?}", data);  // [5, 4, 3, 2, 1]
}
```

### **Exercise 2: Find Element**

```rust
/// Find first occurrence of value using pointers
fn find_with_pointers<T: PartialEq>(arr: &[T], target: &T) -> Option<usize> {
    let start = arr.as_ptr();
    let end = unsafe { start.add(arr.len()) };
    
    let mut current = start;
    unsafe {
        while current < end {
            if *current == *target {
                return Some(current.offset_from(start) as usize);
            }
            current = current.add(1);
        }
    }
    None
}
```

---

## **15. Connection to DSA Mastery**

**Where pointer arithmetic appears in competitive programming**:

1. **Array manipulation**: In-place algorithms (Dutch National Flag, partition schemes)
2. **String processing**: KMP, Z-algorithm implementations
3. **Memory pools**: Custom allocators for speed
4. **Cache optimization**: Data structure layout for performance
5. **Low-level bit manipulation**: Working with packed data

**Pro Tip**: In most DSA problems, use safe Rust. Reserve unsafe pointer arithmetic for:
- Performance-critical hot paths (after profiling)
- Implementing low-level data structures (allocators, intrusive collections)
- Interfacing with C libraries (FFI)

---

## **16. Progression Path**

```
Your Learning Journey:
┌─────────────────────────────────────────────┐
│ Stage 1: Understanding (You are here)       │
│ ├─ Know syntax and operations               │
│ └─ Understand memory layout                 │
│                                             │
│ Stage 2: Safe Alternatives                  │
│ ├─ Master iterators & slices                │
│ └─ Know when NOT to use raw pointers        │
│                                             │
│ Stage 3: Careful Application                │
│ ├─ Use in controlled scenarios              │
│ └─ Document safety invariants               │
│                                             │
│ Stage 4: Advanced Patterns                  │
│ ├─ Custom collections                       │
│ └─ Zero-cost abstractions                   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## **Summary: Key Takeaways**

1. **Pointer arithmetic is about elements, not bytes** - `ptr.add(n)` moves by `n * sizeof(T)`
2. **Creating pointers is safe, using them is unsafe** - wrap dereferences in `unsafe` blocks
3. **Alignment matters** - misaligned access can crash
4. **Bounds checking is your responsibility** - compiler won't save you
5. **Safe alternatives usually suffice** - use unsafe only when necessary
6. **Profile before optimizing** - unsafe doesn't always mean faster

---

**Next Steps in Your Journey**:
- Practice the exercises above
- Implement a simple arena allocator using raw pointers
- Study how `Vec` uses raw pointers internally
- Read Rust's Nomicon for deep unsafe knowledge

Remember: *"With raw pointers comes great responsibility. Use them wisely, document thoroughly, and always question if there's a safer way."*

You're building foundational knowledge that top 1% engineers possess. Keep this disciplined approach! 🧠