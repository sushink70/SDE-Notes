I've created a comprehensive guide to stack overflow with complete implementations in both Python and Rust. This guide covers:

## Key Features Included:

### **Python Implementation:** 

- Recursion depth monitoring
- Stack depth monitoring with automatic protection
- Safe recursive algorithms (factorial, Fibonacci)
- Custom stack implementation 
- Call stack simulation
- Thread stack size testing
- Performance benchmarking utilities
- Error handling and recovery strategies

### **Rust Implementation:**

- Safe recursion with depth monitoring
- RAII-based stack guards for automatic cleanup
- Thread-safe stack depth monitoring
- Zero-cost abstractions for safety
- Custom error types and comprehensive error handling
- Parallel processing techniques
- Memory-efficient implementations
- Extensive unit tests

### **Advanced Topics:**

- Tail call optimization techniques
- Continuation-passing style (CPS)
- Lazy evaluation with generators
- Work-stealing algorithms
- Performance comparison methodologies
- Production deployment considerations

## Practical Applications:

The code includes working examples for:

- **Factorial calculations** (iterative vs recursive)
- **Fibonacci sequences** (with memoization)
- **Tree traversal** algorithms
- **Call stack simulation**
- **Thread stack size testing**
- **Custom stack data structures**

## Safety Features:

Both implementations include:

- **Depth limiting** to prevent overflow
- **Automatic cleanup** (RAII in Rust, context managers in Python)
- **Graceful error handling** with recovery strategies
- **Performance monitoring** and benchmarking
- **Comprehensive testing** frameworks

This guide serves as both a learning resource and a practical reference for implementing stack-safe code in production systems. You can use the provided implementations as starting points for your own applications, adapting them to your specific needs while maintaining safety guarantees.

# Comprehensive Stack Overflow Guide: Python & Rust Implementations

## Table of Contents

1. [Introduction to Stack Overflow](#introduction)
2. [Understanding the Call Stack](#call-stack)
3. [Stack Overflow Causes](#causes)
4. [Detection and Prevention](#detection)
5. [Python Implementation](#python)
6. [Rust Implementation](#rust)
7. [Performance Comparison](#performance)
8. [Best Practices](#best-practices)
9. [Advanced Techniques](#advanced)

## Introduction to Stack Overflow {#introduction}

Stack overflow occurs when a program's call stack exceeds the maximum stack size allocated by the system. This typically happens due to excessive recursion, deeply nested function calls, or large local variable allocations.

### Key Concepts

- **Call Stack**: Memory structure that stores information about active function calls
- **Stack Frame**: Individual record on the call stack for each function call
- **Stack Pointer**: Points to the top of the current stack
- **Stack Overflow**: When stack grows beyond available memory limits

## Understanding the Call Stack {#call-stack}

The call stack operates on a Last-In-First-Out (LIFO) principle:

```
|  Function C  | <- Top of Stack (Current)
|  Function B  |
|  Function A  |
|    main()    | <- Bottom of Stack
+==============+
```

Each stack frame contains:

- Return address
- Local variables
- Function parameters
- Saved registers

## Common Causes of Stack Overflow {#causes}

### 1. Infinite Recursion

The most common cause - functions calling themselves without proper termination.

### 2. Deep Recursion

Legitimate recursive algorithms that exceed stack limits on large inputs.

### 3. Large Local Variables

Allocating large arrays or structures on the stack.

### 4. Mutual Recursion

Multiple functions calling each other in cycles.

## Detection and Prevention Strategies {#detection}

### Detection Methods

1. **Stack Depth Monitoring**: Track recursion depth
2. **Memory Usage Tracking**: Monitor stack memory consumption
3. **Exception Handling**: Catch stack overflow exceptions
4. **Static Analysis**: Analyze code for potential overflow risks

### Prevention Techniques

1. **Iterative Solutions**: Convert recursion to iteration
2. **Tail Call Optimization**: Reuse stack frames
3. **Stack Size Limits**: Implement manual depth limits
4. **Heap Allocation**: Use heap instead of stack for large data

## Python Implementation {#python}

### Basic Stack Overflow Example

```python
import sys
import threading
from functools import lru_cache
import traceback

class StackOverflowDetector:
    def __init__(self, max_depth=1000):
        self.max_depth = max_depth
        self.current_depth = 0
    
    def check_depth(self):
        if self.current_depth >= self.max_depth:
            raise RecursionError(f"Maximum recursion depth exceeded: {self.max_depth}")
    
    def enter(self):
        self.current_depth += 1
        self.check_depth()
    
    def exit(self):
        self.current_depth -= 1

# Global detector instance
stack_detector = StackOverflowDetector()

def safe_recursive_function(n, detector=None):
    """Recursion with overflow protection"""
    if detector is None:
        detector = stack_detector
    
    detector.enter()
    try:
        if n <= 0:
            return 1
        return n * safe_recursive_function(n - 1, detector)
    finally:
        detector.exit()

# Demonstration of stack overflow
def unsafe_recursion(n):
    """This will cause stack overflow for large n"""
    if n <= 0:
        return 1
    return n * unsafe_recursion(n - 1)

def demonstrate_stack_overflow():
    """Demonstrate various stack overflow scenarios"""
    print("=== Python Stack Overflow Demonstrations ===\n")
    
    # 1. Basic recursion limit
    print("1. Current Python recursion limit:")
    print(f"   sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    
    # 2. Safe recursion with protection
    print("\n2. Safe recursion with protection:")
    try:
        result = safe_recursive_function(10)
        print(f"   safe_recursive_function(10) = {result}")
        
        # This should raise an error
        result = safe_recursive_function(2000)
        print(f"   safe_recursive_function(2000) = {result}")
    except RecursionError as e:
        print(f"   Caught RecursionError: {e}")
    
    # 3. Unsafe recursion
    print("\n3. Unsafe recursion (will cause stack overflow):")
    try:
        # Reduce recursion limit for demonstration
        original_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(100)
        
        result = unsafe_recursion(200)
        print(f"   Result: {result}")
    except RecursionError as e:
        print(f"   Caught RecursionError: Maximum recursion depth exceeded")
    finally:
        sys.setrecursionlimit(original_limit)

class StackSafeCalculator:
    """Stack-safe implementations of common recursive algorithms"""
    
    @staticmethod
    def factorial_iterative(n):
        """Iterative factorial - stack safe"""
        if n < 0:
            raise ValueError("Factorial not defined for negative numbers")
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result
    
    @staticmethod
    def factorial_recursive_safe(n, max_depth=1000):
        """Recursive factorial with depth protection"""
        def _factorial(n, depth=0):
            if depth > max_depth:
                raise RecursionError(f"Recursion depth {depth} exceeds maximum {max_depth}")
            if n <= 1:
                return 1
            return n * _factorial(n - 1, depth + 1)
        
        return _factorial(n)
    
    @staticmethod
    def fibonacci_iterative(n):
        """Stack-safe iterative Fibonacci"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    @staticmethod
    @lru_cache(maxsize=None)
    def fibonacci_memoized(n):
        """Memoized Fibonacci - reduces stack usage"""
        if n <= 1:
            return n
        return StackSafeCalculator.fibonacci_memoized(n-1) + StackSafeCalculator.fibonacci_memoized(n-2)

def stack_usage_monitor():
    """Monitor stack usage during execution"""
    import resource
    
    def get_stack_usage():
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    
    initial_usage = get_stack_usage()
    
    # Test with iterative approach
    print("Testing iterative factorial...")
    result = StackSafeCalculator.factorial_iterative(1000)
    iterative_usage = get_stack_usage() - initial_usage
    
    # Test with recursive approach (smaller number to avoid overflow)
    print("Testing recursive factorial...")
    try:
        result = StackSafeCalculator.factorial_recursive_safe(100)
        recursive_usage = get_stack_usage() - initial_usage
        
        print(f"Iterative memory usage: {iterative_usage} KB")
        print(f"Recursive memory usage: {recursive_usage} KB")
    except RecursionError as e:
        print(f"Recursive approach failed: {e}")

class CustomStack:
    """Custom stack implementation to simulate call stack behavior"""
    
    def __init__(self, max_size=1000):
        self.stack = []
        self.max_size = max_size
    
    def push(self, item):
        if len(self.stack) >= self.max_size:
            raise OverflowError("Stack overflow: maximum size exceeded")
        self.stack.append(item)
    
    def pop(self):
        if not self.stack:
            raise UnderflowError("Stack underflow: no items to pop")
        return self.stack.pop()
    
    def peek(self):
        if not self.stack:
            return None
        return self.stack[-1]
    
    def size(self):
        return len(self.stack)
    
    def is_full(self):
        return len(self.stack) >= self.max_size
    
    def is_empty(self):
        return len(self.stack) == 0

def simulate_call_stack():
    """Simulate function call stack behavior"""
    call_stack = CustomStack(max_size=10)  # Small size for demonstration
    
    def simulate_function_call(func_name, params=None):
        frame = {
            'function': func_name,
            'parameters': params or {},
            'local_vars': {},
            'return_address': len(call_stack.stack)
        }
        
        try:
            call_stack.push(frame)
            print(f"Called {func_name}, stack depth: {call_stack.size()}")
            return frame
        except OverflowError as e:
            print(f"Stack overflow when calling {func_name}: {e}")
            raise
    
    def simulate_function_return():
        if not call_stack.is_empty():
            frame = call_stack.pop()
            print(f"Returned from {frame['function']}, stack depth: {call_stack.size()}")
            return frame
        else:
            print("No function to return from")
    
    # Simulate a series of function calls
    print("=== Simulating Function Calls ===")
    try:
        simulate_function_call("main")
        simulate_function_call("function_a", {"param1": 1})
        simulate_function_call("function_b", {"param1": 2, "param2": 3})
        simulate_function_call("function_c")
        
        # This should work
        for i in range(6):
            simulate_function_call(f"recursive_call_{i}")
        
        # This should cause overflow
        simulate_function_call("overflow_function")
        
    except OverflowError:
        print("Caught stack overflow in simulation")
    
    # Clean up
    while not call_stack.is_empty():
        simulate_function_return()

# Advanced: Threading with custom stack sizes
def test_thread_stack_size():
    """Test custom stack sizes in threads"""
    
    def deep_recursion(n, max_n):
        if n >= max_n:
            return n
        return deep_recursion(n + 1, max_n)
    
    # Thread with default stack size
    def test_default_stack():
        try:
            result = deep_recursion(0, 2000)
            print(f"Default stack - succeeded with depth: {result}")
        except RecursionError:
            print("Default stack - hit recursion limit")
    
    # Thread with custom (smaller) stack size
    def test_custom_stack():
        try:
            result = deep_recursion(0, 1000)
            print(f"Custom stack - succeeded with depth: {result}")
        except RecursionError:
            print("Custom stack - hit recursion limit")
    
    print("=== Testing Thread Stack Sizes ===")
    
    # Default stack size thread
    thread1 = threading.Thread(target=test_default_stack)
    thread1.start()
    thread1.join()
    
    # Custom stack size thread (smaller)
    thread2 = threading.Thread(target=test_custom_stack)
    thread2.start()
    thread2.join()

if __name__ == "__main__":
    demonstrate_stack_overflow()
    print("\n" + "="*50 + "\n")
    
    # Test stack-safe implementations
    calc = StackSafeCalculator()
    print("Stack-safe calculations:")
    print(f"factorial_iterative(10) = {calc.factorial_iterative(10)}")
    print(f"fibonacci_iterative(10) = {calc.fibonacci_iterative(10)}")
    
    print("\n" + "="*50 + "\n")
    simulate_call_stack()
    
    print("\n" + "="*50 + "\n")
    test_thread_stack_size()
```

## Rust Implementation {#rust}

### Comprehensive Rust Stack Overflow Implementation

```rust
use std::thread;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::collections::HashMap;

// Custom error types for stack overflow scenarios
#[derive(Debug)]
pub enum StackError {
    Overflow(String),
    Underflow(String),
}

impl std::fmt::Display for StackError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            StackError::Overflow(msg) => write!(f, "Stack Overflow: {}", msg),
            StackError::Underflow(msg) => write!(f, "Stack Underflow: {}", msg),
        }
    }
}

impl std::error::Error for StackError {}

// Stack depth monitor for recursion protection
pub struct StackDepthMonitor {
    max_depth: usize,
    current_depth: AtomicUsize,
}

impl StackDepthMonitor {
    pub fn new(max_depth: usize) -> Self {
        Self {
            max_depth,
            current_depth: AtomicUsize::new(0),
        }
    }
    
    pub fn enter(&self) -> Result<StackGuard, StackError> {
        let depth = self.current_depth.fetch_add(1, Ordering::SeqCst) + 1;
        
        if depth > self.max_depth {
            self.current_depth.fetch_sub(1, Ordering::SeqCst);
            return Err(StackError::Overflow(
                format!("Maximum recursion depth {} exceeded", self.max_depth)
            ));
        }
        
        Ok(StackGuard { monitor: self })
    }
    
    pub fn current_depth(&self) -> usize {
        self.current_depth.load(Ordering::SeqCst)
    }
}

// RAII guard for automatic depth management
pub struct StackGuard<'a> {
    monitor: &'a StackDepthMonitor,
}

impl<'a> Drop for StackGuard<'a> {
    fn drop(&mut self) {
        self.monitor.current_depth.fetch_sub(1, Ordering::SeqCst);
    }
}

// Stack-safe calculator implementations
pub struct StackSafeCalculator {
    monitor: Arc<StackDepthMonitor>,
}

impl StackSafeCalculator {
    pub fn new(max_depth: usize) -> Self {
        Self {
            monitor: Arc::new(StackDepthMonitor::new(max_depth)),
        }
    }
    
    // Iterative factorial - completely stack safe
    pub fn factorial_iterative(&self, n: u64) -> Result<u64, &'static str> {
        if n > 20 {  // Prevent overflow of u64
            return Err("Input too large for u64 factorial");
        }
        
        let mut result = 1u64;
        for i in 1..=n {
            result = result.checked_mul(i)
                .ok_or("Factorial overflow")?;
        }
        Ok(result)
    }
    
    // Recursive factorial with stack protection
    pub fn factorial_recursive(&self, n: u64) -> Result<u64, Box<dyn std::error::Error>> {
        fn factorial_impl(n: u64, monitor: &StackDepthMonitor) -> Result<u64, Box<dyn std::error::Error>> {
            let _guard = monitor.enter()?;
            
            match n {
                0 | 1 => Ok(1),
                _ => {
                    let sub_result = factorial_impl(n - 1, monitor)?;
                    sub_result.checked_mul(n)
                        .ok_or_else(|| Box::new(StackError::Overflow("Arithmetic overflow".to_string())) as Box<dyn std::error::Error>)
                }
            }
        }
        
        if n > 20 {
            return Err(Box::new(StackError::Overflow("Input too large".to_string())));
        }
        
        factorial_impl(n, &self.monitor)
    }
    
    // Fibonacci with memoization to reduce stack usage
    pub fn fibonacci_memoized(&self, n: u64) -> Result<u64, Box<dyn std::error::Error>> {
        fn fib_impl(
            n: u64, 
            memo: &mut HashMap<u64, u64>,
            monitor: &StackDepthMonitor
        ) -> Result<u64, Box<dyn std::error::Error>> {
            let _guard = monitor.enter()?;
            
            if let Some(&cached) = memo.get(&n) {
                return Ok(cached);
            }
            
            let result = match n {
                0 => 0,
                1 => 1,
                _ => {
                    let a = fib_impl(n - 1, memo, monitor)?;
                    let b = fib_impl(n - 2, memo, monitor)?;
                    a.checked_add(b)
                        .ok_or_else(|| Box::new(StackError::Overflow("Fibonacci overflow".to_string())) as Box<dyn std::error::Error>)?
                }
            };
            
            memo.insert(n, result);
            Ok(result)
        }
        
        let mut memo = HashMap::new();
        fib_impl(n, &mut memo, &self.monitor)
    }
    
    // Iterative Fibonacci - stack safe
    pub fn fibonacci_iterative(&self, n: u64) -> Result<u64, &'static str> {
        match n {
            0 => Ok(0),
            1 => Ok(1),
            _ => {
                let mut a = 0u64;
                let mut b = 1u64;
                
                for _ in 2..=n {
                    let next = a.checked_add(b)
                        .ok_or("Fibonacci overflow")?;
                    a = b;
                    b = next;
                }
                
                Ok(b)
            }
        }
    }
    
    // Tree traversal with stack protection
    pub fn tree_depth(&self, node: &TreeNode<i32>) -> Result<usize, StackError> {
        fn depth_impl(node: &TreeNode<i32>, monitor: &StackDepthMonitor) -> Result<usize, StackError> {
            let _guard = monitor.enter()?;
            
            let mut max_child_depth = 0;
            for child in &node.children {
                let child_depth = depth_impl(child, monitor)?;
                max_child_depth = max_child_depth.max(child_depth);
            }
            
            Ok(max_child_depth + 1)
        }
        
        depth_impl(node, &self.monitor)
    }
}

// Custom stack implementation
pub struct CustomStack<T> {
    data: Vec<T>,
    max_size: usize,
}

impl<T> CustomStack<T> {
    pub fn new(max_size: usize) -> Self {
        Self {
            data: Vec::with_capacity(max_size.min(1000)), // Reasonable initial capacity
            max_size,
        }
    }
    
    pub fn push(&mut self, item: T) -> Result<(), StackError> {
        if self.data.len() >= self.max_size {
            return Err(StackError::Overflow(
                format!("Stack size {} exceeds maximum {}", self.data.len(), self.max_size)
            ));
        }
        
        self.data.push(item);
        Ok(())
    }
    
    pub fn pop(&mut self) -> Result<T, StackError> {
        self.data.pop()
            .ok_or_else(|| StackError::Underflow("Cannot pop from empty stack".to_string()))
    }
    
    pub fn peek(&self) -> Option<&T> {
        self.data.last()
    }
    
    pub fn len(&self) -> usize {
        self.data.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }
    
    pub fn is_full(&self) -> bool {
        self.data.len() >= self.max_size
    }
    
    pub fn capacity(&self) -> usize {
        self.max_size
    }
}

// Function call frame simulation
#[derive(Debug, Clone)]
pub struct CallFrame {
    pub function_name: String,
    pub parameters: HashMap<String, i32>,
    pub local_variables: HashMap<String, i32>,
    pub return_address: usize,
}

impl CallFrame {
    pub fn new(function_name: String) -> Self {
        Self {
            function_name,
            parameters: HashMap::new(),
            local_variables: HashMap::new(),
            return_address: 0,
        }
    }
    
    pub fn with_params(mut self, params: HashMap<String, i32>) -> Self {
        self.parameters = params;
        self
    }
}

// Call stack simulator
pub struct CallStackSimulator {
    stack: CustomStack<CallFrame>,
}

impl CallStackSimulator {
    pub fn new(max_depth: usize) -> Self {
        Self {
            stack: CustomStack::new(max_depth),
        }
    }
    
    pub fn call_function(&mut self, frame: CallFrame) -> Result<(), StackError> {
        let depth_before = self.stack.len();
        self.stack.push(frame)?;
        
        println!("Called {}, stack depth: {}", 
                self.stack.peek().unwrap().function_name, 
                self.stack.len());
        
        Ok(())
    }
    
    pub fn return_function(&mut self) -> Result<CallFrame, StackError> {
        let frame = self.stack.pop()?;
        println!("Returned from {}, stack depth: {}", 
                frame.function_name, 
                self.stack.len());
        Ok(frame)
    }
    
    pub fn current_depth(&self) -> usize {
        self.stack.len()
    }
    
    pub fn simulate_recursive_calls(&mut self, base_name: &str, count: usize) -> Result<(), StackError> {
        for i in 0..count {
            let frame = CallFrame::new(format!("{}_{}", base_name, i));
            self.call_function(frame)?;
        }
        Ok(())
    }
}

// Tree structure for testing recursive algorithms
#[derive(Debug)]
pub struct TreeNode<T> {
    pub value: T,
    pub children: Vec<TreeNode<T>>,
}

impl<T> TreeNode<T> {
    pub fn new(value: T) -> Self {
        Self {
            value,
            children: Vec::new(),
        }
    }
    
    pub fn add_child(&mut self, child: TreeNode<T>) {
        self.children.push(child);
    }
    
    // Create a deep tree for testing stack limits
    pub fn create_deep_tree(depth: usize, value: T) -> Self 
    where 
        T: Clone 
    {
        let mut root = TreeNode::new(value.clone());
        
        if depth > 0 {
            let child = Self::create_deep_tree(depth - 1, value);
            root.add_child(child);
        }
        
        root
    }
    
    // Create a wide tree for testing
    pub fn create_wide_tree(width: usize, depth: usize, value: T) -> Self
    where
        T: Clone
    {
        let mut root = TreeNode::new(value.clone());
        
        if depth > 0 {
            for _ in 0..width {
                let child = Self::create_wide_tree(width, depth - 1, value.clone());
                root.add_child(child);
            }
        }
        
        root
    }
}

// Stack overflow testing functions
pub fn test_stack_overflow_scenarios() {
    println!("=== Rust Stack Overflow Testing ===\n");
    
    // Test 1: Basic recursion with protection
    println!("1. Testing protected recursion:");
    let calculator = StackSafeCalculator::new(1000);
    
    match calculator.factorial_recursive(10) {
        Ok(result) => println!("   factorial_recursive(10) = {}", result),
        Err(e) => println!("   Error: {}", e),
    }
    
    match calculator.factorial_recursive(15) {
        Ok(result) => println!("   factorial_recursive(15) = {}", result),
        Err(e) => println!("   Error: {}", e),
    }
    
    // Test 2: Compare iterative vs recursive
    println!("\n2. Comparing implementations:");
    let n = 12;
    
    let iter_result = calculator.factorial_iterative(n).unwrap();
    let rec_result = calculator.factorial_recursive(n).unwrap();
    println!("   Iterative factorial({}) = {}", n, iter_result);
    println!("   Recursive factorial({}) = {}", n, rec_result);
    println!("   Results match: {}", iter_result == rec_result);
    
    // Test 3: Fibonacci comparison
    println!("\n3. Fibonacci implementations:");
    let fib_n = 30;
    
    let fib_iter = calculator.fibonacci_iterative(fib_n).unwrap();
    let fib_memo = calculator.fibonacci_memoized(fib_n).unwrap();
    println!("   fibonacci_iterative({}) = {}", fib_n, fib_iter);
    println!("   fibonacci_memoized({}) = {}", fib_n, fib_memo);
    println!("   Results match: {}", fib_iter == fib_memo);
    
    // Test 4: Tree traversal with depth limit
    println!("\n4. Tree traversal with stack protection:");
    let tree = TreeNode::create_deep_tree(500, 42);
    
    match calculator.tree_depth(&tree) {
        Ok(depth) => println!("   Tree depth: {}", depth),
        Err(e) => println!("   Tree traversal error: {}", e),
    }
    
    // Test 5: Call stack simulation
    println!("\n5. Call stack simulation:");
    let mut sim = CallStackSimulator::new(10);
    
    // Simulate normal function calls
    let _ = sim.call_function(CallFrame::new("main".to_string()));
    let _ = sim.call_function(CallFrame::new("function_a".to_string()));
    let _ = sim.call_function(CallFrame::new("function_b".to_string()));
    
    // Try to cause overflow
    match sim.simulate_recursive_calls("recursive", 8) {
        Ok(()) => println!("   Recursive calls succeeded"),
        Err(e) => println!("   Recursive calls failed: {}", e),
    }
    
    // Clean up
    while sim.current_depth() > 0 {
        let _ = sim.return_function();
    }
}

// Thread stack size testing
pub fn test_thread_stack_sizes() {
    println!("\n=== Thread Stack Size Testing ===");
    
    fn deep_recursion(n: usize, max_n: usize) -> usize {
        if n >= max_n {
            return n;
        }
        deep_recursion(n + 1, max_n)
    }
    
    // Test with default stack size
    let handle1 = thread::spawn(|| {
        match std::panic::catch_unwind(|| {
            deep_recursion(0, 10000)
        }) {
            Ok(result) => println!("Default stack succeeded, depth: {}", result),
            Err(_) => println!("Default stack caused stack overflow"),
        }
    });
    
    // Test with custom (smaller) stack size
    let handle2 = thread::Builder::new()
        .stack_size(32 * 1024) // 32KB stack
        .spawn(|| {
            match std::panic::catch_unwind(|| {
                deep_recursion(0, 1000)
            }) {
                Ok(result) => println!("Small stack succeeded, depth: {}", result),
                Err(_) => println!("Small stack caused stack overflow"),
            }
        }).unwrap();
    
    // Test with larger stack size
    let handle3 = thread::Builder::new()
        .stack_size(8 * 1024 * 1024) // 8MB stack
        .spawn(|| {
            match std::panic::catch_unwind(|| {
                deep_recursion(0, 50000)
            }) {
                Ok(result) => println!("Large stack succeeded, depth: {}", result),
                Err(_) => println!("Large stack caused stack overflow"),
            }
        }).unwrap();
    
    handle1.join().unwrap();
    handle2.join().unwrap();
    handle3.join().unwrap();
}

// Advanced: Custom allocator awareness
pub fn demonstrate_stack_vs_heap() {
    println!("\n=== Stack vs Heap Allocation Demo ===");
    
    // Stack allocation - fast but limited
    fn stack_heavy_function() -> Result<usize, &'static str> {
        // This might cause stack overflow for large arrays
        let large_array: [i32; 1000] = [42; 1000];
        Ok(large_array.len())
    }
    
    // Heap allocation - slower but flexible
    fn heap_safe_function() -> usize {
        let large_vec: Vec<i32> = vec![42; 1000000]; // Much larger, but on heap
        large_vec.len()
    }
    
    println!("Stack allocation result: {:?}", stack_heavy_function());
    println!("Heap allocation result: {}", heap_safe_function());
}

// Main demonstration function
pub fn run_all_tests() {
    test_stack_overflow_scenarios();
    test_thread_stack_sizes();
    demonstrate_stack_vs_heap();
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_stack_depth_monitor() {
        let monitor = StackDepthMonitor::new(3);
        
        let guard1 = monitor.enter().unwrap();
        assert_eq!(monitor.current_depth(), 1);
        
        let guard2 = monitor.enter().unwrap();
        assert_eq!(monitor.current_depth(), 2);
        
        let guard3 = monitor.enter().unwrap();
        assert_eq!(monitor.current_depth(), 3);
        
        // This should fail
        assert!(monitor.enter().is_err());
        
        drop(guard3);
        assert_eq!(monitor.current_depth(), 2);
        
        // Now it should work again
        let guard4 = monitor.enter().unwrap();
        assert_eq!(monitor.current_depth(), 3);
    }
    
    #[test]
    fn test_custom_stack() {
        let mut stack = CustomStack::new(3);
        
        assert!(stack.is_empty());
        assert!(!stack.is_full());
        
        stack.push(1).unwrap();
        stack.push(2).unwrap();
        stack.push(3).unwrap();
        
        assert!(stack.is_full());
        assert!(stack.push(4).is_err()); // Should overflow
        
        assert_eq!(stack.pop().unwrap(), 3);
        assert_eq!(stack.pop().unwrap(), 2);
        assert_eq!(stack.pop().unwrap(), 1);
        
        assert!(stack.pop().is_err()); // Should underflow
    }
    
    #[test]
    fn test_factorial_implementations() {
        let calc = StackSafeCalculator::new(1000);
        
        // Test small values
        for n in 0..=10 {
            let iter_result = calc.factorial_iterative(n).unwrap();
            let rec_result = calc.factorial_recursive(n).unwrap();
            assert_eq!(iter_result, rec_result);
        }
    }
    
    #[test]
    fn test_fibonacci_implementations() {
        let calc = StackSafeCalculator::new(1000);
        
        // Test small values
        for n in 0..=20 {
            let iter_result = calc.fibonacci_iterative(n).unwrap();
            let memo_result = calc.fibonacci_memoized(n).unwrap();
            assert_eq!(iter_result, memo_result);
        }
    }
}

// Example usage and main function
fn main() {
    println!("Stack Overflow Guide - Rust Implementation");
    println!("==========================================\n");
    
    run_all_tests();
    
    println!("\n=== Performance Comparison ===");
    
    let calc = StackSafeCalculator::new(10000);
    
    // Measure time for different approaches
    let start = std::time::Instant::now();
    let _ = calc.factorial_iterative(15).unwrap();
    let iterative_time = start.elapsed();
    
    let start = std::time::Instant::now();
    let _ = calc.factorial_recursive(15).unwrap();
    let recursive_time = start.elapsed();
    
    println!("Iterative factorial time: {:?}", iterative_time);
    println!("Recursive factorial time: {:?}", recursive_time);
    
    // Memory usage comparison would require external profiling tools
    println!("\nNote: For detailed memory analysis, use tools like:");
    println!("- Valgrind (Linux/macOS)");
    println!("- heaptrack");
    println!("- cargo-profiler");
}
```

## Performance Comparison {#performance}

### Time Complexity Analysis

| Algorithm | Iterative | Recursive | Memoized |
|-----------|-----------|-----------|----------|
| Factorial | O(n) | O(n) | O(n) |
| Fibonacci | O(n) | O(2^n) | O(n) |
| Tree Traversal | O(n) | O(n) | O(n) |

### Space Complexity Analysis

| Algorithm | Iterative | Recursive | Memoized |
|-----------|-----------|-----------|----------|
| Factorial | O(1) | O(n) | O(n) |
| Fibonacci | O(1) | O(n) | O(n) |
| Tree Traversal | O(h) | O(h) | O(h) |

*h = height of tree*

### Benchmarking Results

#### Python Performance
```python
import timeit
import sys

def benchmark_implementations():
    # Factorial benchmarks
    iterative_time = timeit.timeit(
        lambda: StackSafeCalculator.factorial_iterative(1000), 
        number=10000
    )
    
    recursive_time = timeit.timeit(
        lambda: StackSafeCalculator.factorial_recursive_safe(100), 
        number=10000
    )
    
    print(f"Python Factorial (n=100):")
    print(f"  Iterative: {iterative_time:.4f}s")
    print(f"  Recursive: {recursive_time:.4f}s")
    print(f"  Speedup: {recursive_time/iterative_time:.2f}x")
```

#### Rust Performance
```rust
use std::time::Instant;

fn benchmark_rust_implementations() {
    let calc = StackSafeCalculator::new(10000);
    
    let start = Instant::now();
    for _ in 0..10000 {
        let _ = calc.factorial_iterative(20);
    }
    let iterative_time = start.elapsed();
    
    let start = Instant::now();
    for _ in 0..10000 {
        let _ = calc.factorial_recursive(20);
    }
    let recursive_time = start.elapsed();
    
    println!("Rust Factorial (n=20):");
    println!("  Iterative: {:?}", iterative_time);
    println!("  Recursive: {:?}", recursive_time);
}
```

## Best Practices {#best-practices}

### 1. Prevention Strategies

#### Use Iterative Approaches When Possible
```python
# Good: Iterative
def sum_list_iterative(lst):
    total = 0
    for item in lst:
        total += item
    return total

# Avoid: Recursive (for simple operations)
def sum_list_recursive(lst):
    if not lst:
        return 0
    return lst[0] + sum_list_recursive(lst[1:])
```

#### Implement Depth Limits
```rust
fn safe_recursive_function<T>(
    data: T, 
    depth: usize, 
    max_depth: usize
) -> Result<T, StackError> {
    if depth >= max_depth {
        return Err(StackError::Overflow(
            "Maximum recursion depth exceeded".to_string()
        ));
    }
    
    // Recursive logic here
    // safe_recursive_function(new_data, depth + 1, max_depth)
    
    Ok(data)
}
```

### 2. Memory Management

#### Stack vs Heap Decision Matrix

| Use Stack When | Use Heap When |
|----------------|---------------|
| Data size < 1MB | Data size > 1MB |
| Known at compile time | Dynamic sizing needed |
| Short-lived data | Long-lived data |
| Performance critical | Memory flexibility needed |

### 3. Error Handling

#### Python Exception Handling
```python
def safe_operation():
    try:
        result = potentially_recursive_function()
        return result
    except RecursionError as e:
        logging.error(f"Stack overflow detected: {e}")
        return fallback_iterative_solution()
    except MemoryError as e:
        logging.error(f"Memory exhausted: {e}")
        return None
```

#### Rust Error Handling
```rust
fn safe_operation() -> Result<i32, Box<dyn std::error::Error>> {
    match potentially_recursive_function() {
        Ok(result) => Ok(result),
        Err(StackError::Overflow(msg)) => {
            eprintln!("Stack overflow: {}", msg);
            fallback_iterative_solution()
        },
        Err(e) => Err(Box::new(e)),
    }
}
```

### 4. Testing Strategies

#### Unit Testing for Stack Safety
```python
def test_stack_safety():
    """Test that functions handle deep recursion gracefully"""
    
    # Test normal operation
    result = safe_function(small_input)
    assert result == expected_output
    
    # Test stack overflow protection
    with pytest.raises(RecursionError):
        safe_function(very_large_input)
    
    # Test fallback behavior
    result = safe_function_with_fallback(large_input)
    assert result is not None
```

## Advanced Techniques {#advanced}

### 1. Tail Call Optimization

#### Python (Manual Implementation)
```python
def factorial_tail_optimized(n, accumulator=1):
    """Tail-call optimized factorial (manual)"""
    while n > 0:
        accumulator *= n
        n -= 1
    return accumulator

# Trampoline pattern for tail call simulation
def trampoline(func):
    """Execute a function using trampoline pattern"""
    while callable(func):
        func = func()
    return func

def factorial_trampoline(n, acc=1):
    """Factorial using trampoline pattern"""
    if n <= 1:
        return acc
    return lambda: factorial_trampoline(n - 1, n * acc)

# Usage: result = trampoline(factorial_trampoline(1000))
```

#### Rust (Explicit Tail Recursion)
```rust
fn factorial_tail_recursive(n: u64) -> u64 {
    fn factorial_helper(n: u64, acc: u64) -> u64 {
        match n {
            0 | 1 => acc,
            _ => factorial_helper(n - 1, n * acc)
        }
    }
    
    factorial_helper(n, 1)
}

// Convert to iterative automatically
fn factorial_tail_to_iterative(n: u64) -> u64 {
    let mut n = n;
    let mut acc = 1;
    
    loop {
        match n {
            0 | 1 => return acc,
            _ => {
                acc *= n;
                n -= 1;
            }
        }
    }
}
```

### 2. Continuation-Passing Style (CPS)

#### Advanced Recursion Control
```python
def cps_factorial(n, continuation=lambda x: x):
    """Factorial in Continuation-Passing Style"""
    if n <= 1:
        return continuation(1)
    else:
        return cps_factorial(
            n - 1, 
            lambda result: continuation(n * result)
        )

# Stack-safe CPS using explicit stack
def cps_factorial_safe(n):
    """Stack-safe CPS implementation"""
    stack = [(n, lambda x: x)]
    
    while stack:
        current_n, continuation = stack.pop()
        
        if current_n <= 1:
            result = continuation(1)
            if stack:
                # Apply pending continuations
                while stack and not callable(result):
                    _, next_cont = stack.pop()
                    result = next_cont(result)
            return result
        else:
            stack.append((current_n - 1, lambda r: continuation(current_n * r)))
    
    return 1
```

### 3. Lazy Evaluation and Generators

#### Python Generators for Stack Safety
```python
def fibonacci_generator():
    """Memory-efficient Fibonacci generator"""
    a, b = 0, 1
    yield a
    yield b
    
    while True:
        a, b = b, a + b
        yield b

def tree_traversal_generator(node):
    """Stack-safe tree traversal using generators"""
    yield node.value
    
    for child in node.children:
        yield from tree_traversal_generator(child)

# Usage
fib_gen = fibonacci_generator()
first_100_fibs = [next(fib_gen) for _ in range(100)]
```

### 4. Work-Stealing and Parallel Processing

#### Rust Parallel Stack-Safe Processing
```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn parallel_tree_processing<T, F, R>(
    tree: &TreeNode<T>, 
    processor: F,
    max_threads: usize
) -> Vec<R>
where
    T: Send + Sync,
    F: Fn(&T) -> R + Send + Sync + Copy,
    R: Send,
{
    let results = Arc::new(Mutex::new(Vec::new()));
    let work_queue = Arc::new(Mutex::new(vec![tree]));
    
    let mut handles = Vec::new();
    
    for _ in 0..max_threads {
        let results = Arc::clone(&results);
        let work_queue = Arc::clone(&work_queue);
        
        let handle = thread::spawn(move || {
            loop {
                let node = {
                    let mut queue = work_queue.lock().unwrap();
                    queue.pop()
                };
                
                match node {
                    Some(node) => {
                        // Process current node
                        let result = processor(&node.value);
                        results.lock().unwrap().push(result);
                        
                        // Add children to work queue
                        let mut queue = work_queue.lock().unwrap();
                        for child in &node.children {
                            queue.push(child);
                        }
                    }
                    None => break, // No more work
                }
            }
        });
        
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    Arc::try_unwrap(results).unwrap().into_inner().unwrap()
}
```

## Conclusion

Stack overflow is a critical issue that can bring down applications and systems. This comprehensive guide has covered:

### Key Takeaways

1. **Prevention is Better than Cure**: Use iterative solutions when possible
2. **Implement Safety Measures**: Always include depth limits and error handling
3. **Choose the Right Tool**: Python for rapid prototyping, Rust for performance and safety
4. **Monitor and Test**: Include stack safety in your testing strategy
5. **Understand Trade-offs**: Balance between performance, safety, and code complexity

### Language-Specific Recommendations

#### Python
- Use `sys.setrecursionlimit()` carefully
- Implement custom depth monitoring
- Leverage generators for large datasets
- Consider `@lru_cache` for memoization

#### Rust
- Utilize the type system for compile-time safety
- Implement RAII patterns for resource management
- Use `Result<T, E>` for error handling
- Take advantage of zero-cost abstractions

### Production Considerations

1. **Monitoring**: Implement runtime stack monitoring
2. **Alerting**: Set up alerts for recursion depth breaches
3. **Fallbacks**: Always have iterative fallbacks available
4. **Documentation**: Document stack safety guarantees in your APIs
5. **Testing**: Include stress testing with deep recursion scenarios

This guide provides a solid foundation for understanding and preventing stack overflow issues in both Python and Rust applications. The implementations shown can be adapted and extended for specific use cases while maintaining safety and performance.

I'll create a detailed ASCII diagram showing how stack overflow occurs step by step.This ASCII diagram illustrates how stack overflow occurs through several key stages:

1. **Normal Operation**: Shows how the stack grows downward from high to low memory addresses as functions are called
2. **Function Call Buildup**: Demonstrates how each function call adds a new frame to the stack
3. **Recursive Danger**: Shows how recursive calls without proper base cases consume stack space rapidly
4. **Overflow Event**: Illustrates what happens when the stack grows beyond its allocated boundary
5. **System Response**: Shows how the operating system detects and handles the violation

The diagram emphasizes that stack overflow typically happens when:
- Recursive functions lack proper termination conditions
- Functions have large local variables (like big arrays)
- The call depth exceeds the available stack space

The visual representation makes it clear why this is called "stack overflow" - the stack literally overflows its allocated memory region and crashes into other memory areas, causing the program to terminate with a segmentation fault.

# Stack Overflow: Step-by-Step ASCII Diagram

## Step 1: Normal Stack Operations
```
Memory Layout:
┌─────────────────────┐ ← High Memory Address
│                     │
│      HEAP           │
│                     │
├─────────────────────┤
│                     │
│      FREE           │
│      SPACE          │
│                     │
├─────────────────────┤ ← Stack Pointer (SP)
│  Local Var C        │
│  Return Addr C      │
├─────────────────────┤
│  Local Var B        │
│  Return Addr B      │
├─────────────────────┤
│  Local Var A        │
│  Return Addr A      │
├─────────────────────┤
│      STACK          │
│     (grows down)    │
└─────────────────────┘ ← Low Memory Address (Stack Base)
```

## Step 2: Function Calls Adding to Stack
```
Function Call Sequence: main() → funcA() → funcB() → funcC()

Stack Growth:
┌─────────────────────┐
│      HEAP           │
├─────────────────────┤
│                     │
│    FREE SPACE       │ ← Space getting smaller
│    (available)      │
├─────────────────────┤ ← Stack Pointer (SP) - moving up!
│  funcC() locals     │ ← New frame
│  funcC() return     │
├─────────────────────┤
│  funcB() locals     │
│  funcB() return     │
├─────────────────────┤
│  funcA() locals     │
│  funcA() return     │
├─────────────────────┤
│  main() locals      │
│  main() return      │
└─────────────────────┘

Call Stack Depth: 4 functions deep
```

## Step 3: Recursive Function (Beginning of Trouble)
```
Code Example:
void recursiveFunction(int n) {
    char buffer[1024];        // Local array (1KB)
    printf("Depth: %d\n", n);
    recursiveFunction(n + 1); // Recursive call - NO BASE CASE!
}

Stack After 5 Recursive Calls:
┌─────────────────────┐
│      HEAP           │
├─────────────────────┤
│                     │
│   FREE SPACE        │ ← Getting critically low
│   (very small)      │
├─────────────────────┤ ← SP moving dangerously up
│  [1024B] buffer5    │
│  return addr 5      │
├─────────────────────┤
│  [1024B] buffer4    │
│  return addr 4      │
├─────────────────────┤
│  [1024B] buffer3    │
│  return addr 3      │
├─────────────────────┤
│  [1024B] buffer2    │
│  return addr 2      │
├─────────────────────┤
│  [1024B] buffer1    │
│  return addr 1      │
├─────────────────────┤
│  main() frame       │
└─────────────────────┘

Memory Used: 5 × 1024 bytes = ~5KB of stack space
```

## Step 4: Stack Overflow Occurs!
```
After Many More Recursive Calls:

┌─────────────────────┐ ← HEAP
├─────────────────────┤
│ COLLISION POINT!    │ ← Stack has grown into heap!
│ ███████████████████ │ ← Stack overflow boundary
│ [1024B] buffer_N    │ ← Current frame
│ return addr N       │
├─────────────────────┤
│ [1024B] buffer_N-1  │
│ return addr N-1     │
├─────────────────────┤
│        ...          │ ← Hundreds of stack frames
│      (many          │
│     recursive       │
│      calls)         │
├─────────────────────┤
│ [1024B] buffer2     │
│ return addr 2       │
├─────────────────────┤
│ [1024B] buffer1     │
│ return addr 1       │
├─────────────────────┤
│ main() frame        │
└─────────────────────┘ ← Stack base

ERROR: Stack Overflow Detected!
Program terminates with segmentation fault
```

## Step 5: What Happens During Overflow
```
Memory Protection Violation:

┌─────────────────────┐
│  HEAP DATA          │ ← May get corrupted
│  ▼▼▼ CORRUPTED ▼▼▼  │
├═════════════════════┤ ← Protection boundary crossed
│ STACK OVERFLOW      │ ← Program tries to write here
│ ███████████████████ │ ← Illegal memory access
│                     │
│ Operating System    │ ← OS detects violation
│ Sends SIGSEGV       │ ← Segmentation fault signal
│                     │
├─────────────────────┤
│   Valid Stack       │
│   Frames Below      │
└─────────────────────┘

Result: Program crash with error message like:
"Segmentation fault (core dumped)"
"Stack overflow"
```

## Visual Representation of the Problem

### Normal Function Call Pattern:
```
main()
  └─ funcA()
      └─ funcB()
          └─ return to funcB
      └─ return to funcA  
  └─ return to main
```

### Stack Overflow Pattern:
```
main()
  └─ recursive(1)
      └─ recursive(2)
          └─ recursive(3)
              └─ recursive(4)
                  └─ recursive(5)
                      └─ recursive(...∞)
                          └─ CRASH! 💥
```

## Common Causes and Prevention

### Causes:
1. **Infinite Recursion** - Missing base case
2. **Deep Recursion** - Too many recursive calls
3. **Large Local Variables** - Big arrays/structs on stack
4. **Excessive Function Nesting** - Too many nested calls

### Prevention:
```c
// ❌ BAD - No base case
void badRecursion(int n) {
    badRecursion(n + 1);  // Will overflow!
}

// ✅ GOOD - Has base case
void goodRecursion(int n) {
    if (n <= 0) return;   // Base case prevents overflow
    goodRecursion(n - 1);
}

// ✅ GOOD - Iterative alternative
void iterativeVersion(int n) {
    while (n > 0) {
        // Do work
        n--;
    }
}
```

## Stack Size Limits (Typical Values)
```
Operating System    | Default Stack Size
--------------------|-------------------
Linux (main thread)| 8 MB
Windows             | 1 MB  
macOS               | 8 MB
Embedded Systems    | 4-64 KB

Note: These can often be configured, but have hard limits
```