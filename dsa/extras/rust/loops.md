# Tracking Loops in Rust

Rust has several loop constructs, each with distinct characteristics for handling values, conditions, and control flow.

## Loop Types

**`loop`** - Infinite loop that runs until explicitly broken
```rust
let mut count = 0;
loop {
    count += 1;
    if count == 5 {
        break;
    }
}
```

**`while`** - Conditional loop
```rust
let mut n = 0;
while n < 5 {
    n += 1;
}
```

**`for`** - Iterator-based loop
```rust
for i in 0..5 {
    println!("{}", i);
}
```

## How Values Work

Rust loops handle values through ownership and borrowing rules:

**Returning values from loops:**
```rust
let result = loop {
    counter += 1;
    if counter == 10 {
        break counter * 2;  // returns 20
    }
};
```

**Variable scope:**
```rust
let mut x = 5;
for i in 0..3 {
    let y = i * 2;  // y exists only in loop scope
    x += y;         // x persists outside loop
}
// y is not accessible here
```

**Moving vs borrowing:**
```rust
let vec = vec![1, 2, 3];

// Borrowing - vec still usable after
for item in &vec {
    println!("{}", item);
}

// Moving - vec consumed, can't use after
for item in vec {
    println!("{}", item);
}
```

## Iterators and Methods

Rust provides powerful iterator methods that transform loops:

```rust
let numbers = vec![1, 2, 3, 4, 5];

// map, filter, collect
let doubled: Vec<i32> = numbers.iter()
    .filter(|&&x| x % 2 == 0)
    .map(|&x| x * 2)
    .collect();

// enumerate for index tracking
for (index, value) in numbers.iter().enumerate() {
    println!("Index {}: {}", index, value);
}

// zip for parallel iteration
let names = vec!["Alice", "Bob"];
let ages = vec![30, 25];
for (name, age) in names.iter().zip(ages.iter()) {
    println!("{} is {} years old", name, age);
}
```

## Loop Labels and Control

Labels allow breaking/continuing outer loops:

```rust
'outer: for x in 0..3 {
    for y in 0..3 {
        if x == 1 && y == 1 {
            break 'outer;  // breaks outer loop
        }
    }
}
```

## Common Patterns

**Range iteration:**
```rust
for i in 0..10 {}        // 0 to 9
for i in 0..=10 {}       // 0 to 10 (inclusive)
for i in (0..10).rev() {} // 9 to 0
```

**Mutable iteration:**
```rust
let mut vec = vec![1, 2, 3];
for item in &mut vec {
    *item *= 2;  // dereference to modify
}
```

**Infinite loop with conditions:**
```rust
loop {
    if condition {
        break;
    }
    if other_condition {
        continue;
    }
}
```

The key distinctions in Rust are the ownership system (whether iteration borrows or moves), the rich iterator ecosystem that often eliminates explicit loops, and the type safety that ensures variables are properly scoped and tracked at compile time.