# Comprehensive Mental Framework for Problem-Solving in Software Engineering & DSA

## I. Initial Problem Analysis Phase

### 1. **Understanding the Problem Deeply**
Before writing any code, invest time in comprehension:

- **Read multiple times**: First pass for general understanding, second for constraints, third for edge cases
- **Restate in your own words**: Can you explain this to someone else?
- **Identify the core challenge**: Strip away the story/context to find the fundamental problem
- **Question ambiguities**: What happens when X? Is Y always guaranteed? Can Z be negative?

### 2. **Input Analysis Framework**

**Type Classification:**
- Primitive types: integers, floats, booleans, characters
- Collections: arrays, strings, lists, matrices, trees, graphs
- Custom objects: What fields? What invariants?

**Constraint Analysis:**
- Range: Min/max values? Can they be zero, negative, or exceed limits?
- Size: Empty collections? Single element? Maximum size that affects time/space?
- Format: Sorted? Unique elements? Contains nulls/special values?
- Relationships: Dependencies between inputs? Mutual constraints?

### 3. **Output Requirements**
- Exact format needed: single value, collection, modified input, boolean
- Multiple valid answers or unique solution?
- Return vs modify in-place?
- What to return for impossible cases?

## II. Edge Case Systematic Checklist

### **A. Numerical Edge Cases**

```
INTEGER BOUNDARIES:
□ Zero (often special case in division, modulo, counting)
□ Negative numbers (if allowed)
□ Integer overflow/underflow (MAX_INT, MIN_INT)
□ Powers of 2 (binary representations matter)
□ Prime numbers vs composites
□ Odd vs even numbers (when it affects logic)

FLOATING POINT:
□ 0.0, -0.0 (they're different!)
□ Infinity, -Infinity
□ NaN (Not a Number)
□ Very small numbers (underflow)
□ Very large numbers (overflow)
□ Precision errors (0.1 + 0.2 ≠ 0.3)
```

### **B. Collection Edge Cases**

```
ARRAYS/LISTS:
□ Empty array []
□ Single element [x]
□ Two elements [x, y] (minimum for comparison/swap)
□ All elements identical [5, 5, 5, 5]
□ Already sorted (ascending/descending)
□ Reverse sorted
□ Contains duplicates
□ No duplicates when expected
□ Contains null/None values
□ Maximum size constraints

STRINGS:
□ Empty string ""
□ Single character "a"
□ All same character "aaaa"
□ No matches found
□ All elements match
□ Special characters: spaces, newlines, tabs
□ Unicode/emoji characters
□ Case sensitivity issues
□ Leading/trailing whitespace
```

### **C. Pointer/Reference Edge Cases**

```
□ Null/None pointers
□ Self-referencing (node points to itself)
□ Circular references (A→B→C→A)
□ Dangling pointers
□ Shared references (two pointers to same object)
```

### **D. Data Structure Specific**

```
LINKED LISTS:
□ Empty list (head = null)
□ Single node
□ Two nodes (test direction)
□ Operation at head
□ Operation at tail
□ Operation in middle
□ Circular list
□ List with cycle

TREES:
□ Empty tree (root = null)
□ Single node tree
□ Only left children (degenerates to list)
□ Only right children
□ Perfectly balanced
□ Completely unbalanced
□ Target at root, leaf, or middle
□ Multiple nodes with same value

GRAPHS:
□ Empty graph
□ Single node (no edges)
□ Disconnected components
□ Cyclic vs acyclic
□ Self-loops
□ Multiple edges between same nodes
□ Directed vs undirected considerations
```

### **E. Algorithm-Specific Edge Cases**

```
SEARCHING:
□ Target not present
□ Multiple occurrences of target
□ Target at boundaries (first/last position)
□ All elements are target

SORTING:
□ Already sorted
□ Reverse sorted
□ All equal elements
□ Two distinct values only

DYNAMIC PROGRAMMING:
□ Base case (dp[0], dp[1])
□ No valid solution exists
□ Multiple optimal solutions
□ Negative indices/values if applicable

RECURSION:
□ Base case immediately triggered
□ Maximum recursion depth
□ Stack overflow potential
□ Memoization cache hits
```

### **F. Boundary Conditions**

```
□ First element/iteration
□ Last element/iteration
□ Middle element (for arrays with odd/even length)
□ n-1 vs n confusion (off-by-one errors)
□ Index out of bounds
□ Empty range (start > end)
□ Single element range (start == end)
```

### **G. Logical Edge Cases**

```
□ Vacuous truth (empty set satisfies all conditions)
□ Short-circuit evaluation consequences
□ Boolean edge cases (true, false, null/undefined)
□ Division by zero
□ Modulo by zero or negative numbers
□ Bitwise operations with zero
□ Empty result sets when aggregating
```

## III. Problem-Solving Mental Process

### **Step 1: Pattern Recognition**

**Ask yourself:**
- Have I solved something similar before?
- What category does this fall into?
  - Two pointers (sorted arrays, palindromes)
  - Sliding window (contiguous subarrays)
  - Binary search (sorted, monotonic)
  - BFS/DFS (traversal, shortest path)
  - Dynamic programming (optimal substructure)
  - Greedy (local optimum → global)
  - Divide and conquer (merge sort style)
  - Hash map (frequency, lookup)
  - Stack (matching, monotonic)
  - Heap (k-th element, merge k lists)

### **Step 2: Brute Force First**

Always start here mentally:
- What's the naive solution?
- What's its time/space complexity?
- Why is it slow? What repeated work exists?
- Can I optimize by avoiding that repeated work?

### **Step 3: Optimization Strategies**

```
TIME OPTIMIZATION:
→ Preprocessing: Can I sort first? Build a hash map?
→ Caching: Am I recomputing the same values? (memoization)
→ Better data structure: Array → Hash set for O(1) lookup?
→ Mathematical insight: Closed form formula instead of iteration?
→ Pruning: Can I skip branches that won't lead to answers?

SPACE OPTIMIZATION:
→ Can I modify input in-place?
→ Do I need all previous states or just last few?
→ Can I use bit manipulation instead of arrays?
→ Can I use two pointers instead of extra memory?
```

### **Step 4: Implementation Strategy**

**Write defensive code:**
```python
# 1. Validate inputs immediately
if not array or len(array) == 0:
    return default_value

# 2. Handle edge cases explicitly before main logic
if len(array) == 1:
    return special_case_result

# 3. Use clear variable names
left_pointer, right_pointer  # not l, r
max_sum_so_far  # not mx

# 4. Add assertions for invariants
assert left <= right, "Pointers crossed!"

# 5. Document non-obvious logic
# We use XOR because a^a = 0 and a^0 = a
```

## IV. Testing Mental Checklist

### **Before Submitting:**

```
□ Did I test the empty case?
□ Did I test single element?
□ Did I test two elements?
□ Did I test all same elements?
□ Did I test the minimum constraint?
□ Did I test the maximum constraint?
□ Did I test negative values?
□ Did I test zero?
□ Did I walk through the algorithm line by line?
□ Did I check boundary conditions (0, n-1)?
□ Could integer overflow occur?
□ Did I handle null/None properly?
□ Are my loop conditions correct (< vs <=)?
□ Do I return the right type?
```

### **Test Case Generation Template:**

```
1. Normal case (typical input)
2. Empty/null case
3. Single element
4. All elements identical
5. Minimum constraint values
6. Maximum constraint values
6. Boundary values (0, -1, MAX)
7. No solution exists case
8. Multiple solutions case
9. Best case for algorithm
10. Worst case for algorithm
```

## V. Common Pitfall Patterns

### **1. Off-by-One Errors**
- Is it `i < n` or `i <= n`?
- Is it `arr[mid]` or `arr[mid+1]`?
- Slicing: `arr[i:j]` includes i but excludes j

### **2. Integer Division**
- `5 / 2 = 2.5` (Python 3) but `5 // 2 = 2`
- Negative division: `-5 // 2 = -3` (floors toward negative infinity)
- Use `(a + b) // 2` cautiously with large numbers (overflow)
- Better: `a + (b - a) // 2`

### **3. Comparison Chains**
- `a < b < c` is valid in Python but not all languages
- Watch for `a == b == c` vs `a == b and b == c`

### **4. Mutable Default Arguments**
```python
# WRONG
def func(arr=[]):  # This list is created once!
    arr.append(1)
    return arr

# RIGHT
def func(arr=None):
    if arr is None:
        arr = []
    arr.append(1)
    return arr
```

### **5. Reference vs Value**
- Copying: shallow vs deep copy
- Modifying slices doesn't modify original
- Lists are passed by reference in Python

### **6. String Immutability**
- Concatenating strings in loop: O(n²)
- Use list and join: O(n)

### **7. Hash Map Keys**
- Lists can't be keys (unhashable)
- Use tuples for composite keys
- Watch for float equality as keys

## VI. Debugging Mental Framework

When stuck or getting wrong answers:

### **1. Trace Execution**
- Pick the simplest failing test case
- Write out variable values at each step
- Don't trust your assumptions—verify them

### **2. Binary Search Your Logic**
- Comment out half the code
- Which half has the bug?
- Recurse into that half

### **3. Print-Driven Development**
```python
print(f"At iteration {i}, value is {val}, condition is {condition}")
print(f"Input: {input_data}")
print(f"Expected: {expected}, Got: {actual}")
```

### **4. Rubber Duck Debugging**
- Explain your code line by line out loud
- Often you'll catch the error while explaining

### **5. Question Your Assumptions**
- "This array is sorted" — is it really?
- "These values are positive" — always?
- "The input is valid" — prove it

## VII. Time/Space Complexity Analysis

### **Quick Reference:**

```
O(1)      - Constant: hash lookup, array access
O(log n)  - Logarithmic: binary search, balanced tree ops
O(n)      - Linear: single pass through array
O(n log n)- Linearithmic: efficient sorting, divide & conquer
O(n²)     - Quadratic: nested loops over same data
O(n³)     - Cubic: triple nested loops
O(2ⁿ)     - Exponential: naive recursive Fibonacci
O(n!)     - Factorial: generating all permutations

Space:
O(1)      - Constant extra space (few variables)
O(n)      - Proportional to input (hash map, recursion stack)
O(n²)     - Matrix, 2D DP table
```

### **Analysis Checklist:**
```
□ Count nested loops
□ Identify recursion depth (space)
□ Account for auxiliary data structures
□ Consider input modification vs copying
□ Hidden costs (sorting, slicing, string concat)
□ Best, average, worst case differences
```

## VIII. Final Pre-Code Checklist

```
Before writing any code:

□ Do I fully understand the problem?
□ Have I identified all constraints?
□ Do I know what edge cases exist?
□ Have I thought of a brute force solution?
□ Do I have an optimization strategy?
□ What's my expected time/space complexity?
□ Have I considered alternative approaches?
□ Do I know how to handle invalid inputs?
□ Have I mentally traced through 2-3 examples?

After writing code:

□ Does it handle all edge cases?
□ Are there any off-by-one errors?
□ Could anything overflow/underflow?
□ Are null/None values handled?
□ Is the return type correct?
□ Have I tested it mentally?
□ Is the code readable?
□ Are variable names clear?
```

## IX. Growth Mindset Reminders

- **Every bug is a learning opportunity**: What pattern caused this? How do I avoid it next time?
- **Edge cases aren't annoying**: They're the difference between good and excellent code
- **Complexity isn't skill**: Simple, correct code > complex, buggy code
- **Test, don't hope**: Assume nothing works until proven otherwise
- **Iterate rapidly**: Brute force → optimize, don't wait for perfect solution
- **Learn from failures**: Keep a "bug journal" of recurring mistakes

---

**Remember**: The goal isn't to memorize this list, but to internalize the *habit* of systematic thinking. With practice, this mental framework becomes automatic, and you'll naturally ask the right questions before, during, and after coding.

# Comprehensive Debugging & Troubleshooting Guide for VSCode & RustRover

## I. IDE-Specific Debugging Setup

### **A. VSCode Configuration**

#### 1. **Python Debugging Setup**

**Install Required Extensions:**
```bash
# Essential extensions
- Python (Microsoft)
- Pylance
- Python Debugger
- Error Lens (shows errors inline)
```

**launch.json for Python:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false,  // Debug into libraries
            "args": []  // Add command-line arguments here
        },
        {
            "name": "Python: Debug Tests",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["-v", "${file}"]
        }
    ]
}
```

#### 2. **Go Debugging Setup**

**Install Extension:**
```bash
- Go (Google)
```

**launch.json for Go:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Launch Package",
            "type": "go",
            "request": "launch",
            "mode": "debug",
            "program": "${fileDirname}",
            "env": {},
            "args": [],
            "showLog": true
        },
        {
            "name": "Debug Test",
            "type": "go",
            "request": "launch",
            "mode": "test",
            "program": "${workspaceFolder}",
            "args": ["-test.run", "TestName"]
        }
    ]
}
```

#### 3. **Rust Debugging Setup**

**Install Extensions:**
```bash
- rust-analyzer
- CodeLLDB (for debugging)
- crates (dependency management)
```

**launch.json for Rust:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "type": "lldb",
            "request": "launch",
            "name": "Debug executable",
            "cargo": {
                "args": [
                    "build",
                    "--bin=your_binary_name",
                    "--package=your_package_name"
                ],
                "filter": {
                    "name": "your_binary_name",
                    "kind": "bin"
                }
            },
            "args": [],
            "cwd": "${workspaceFolder}"
        },
        {
            "type": "lldb",
            "request": "launch",
            "name": "Debug unit tests",
            "cargo": {
                "args": [
                    "test",
                    "--no-run",
                    "--lib"
                ]
            },
            "args": [],
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

#### 4. **C/C++ Debugging Setup**

**Install Extensions:**
```bash
- C/C++ (Microsoft)
- C/C++ Extension Pack
```

**launch.json for C/C++:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "gcc - Build and debug active file",
            "type": "cppdbg",
            "request": "launch",
            "program": "${fileDirname}/${fileBasenameNoExtension}",
            "args": [],
            "stopAtEntry": false,
            "cwd": "${fileDirname}",
            "environment": [],
            "externalConsole": false,
            "MIMode": "gdb",
            "setupCommands": [
                {
                    "description": "Enable pretty-printing for gdb",
                    "text": "-enable-pretty-printing",
                    "ignoreFailures": true
                }
            ],
            "preLaunchTask": "C/C++: gcc build active file",
            "miDebuggerPath": "/usr/bin/gdb"
        }
    ]
}
```

**tasks.json for C/C++:**
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "type": "cppbuild",
            "label": "C/C++: gcc build active file",
            "command": "/usr/bin/gcc",
            "args": [
                "-fdiagnostics-color=always",
                "-g",  // Debug symbols
                "${file}",
                "-o",
                "${fileDirname}/${fileBasenameNoExtension}",
                "-Wall",  // All warnings
                "-Wextra",
                "-fsanitize=address,undefined"  // AddressSanitizer
            ],
            "options": {
                "cwd": "${fileDirname}"
            },
            "problemMatcher": ["$gcc"],
            "group": {
                "kind": "build",
                "isDefault": true
            }
        }
    ]
}
```

### **B. RustRover Debugging**

RustRover has built-in debugging support:

**Features:**
- Automatic run configurations
- Inline variable inspection
- Memory view
- Evaluate expressions
- Conditional breakpoints

**Quick Setup:**
1. Click debug icon next to `main()` or test functions
2. Or: Run → Debug... → Select configuration
3. Set breakpoints by clicking line numbers

## II. Breakpoint Strategies

### **1. Standard Breakpoints**

**VSCode:**
- Click left of line number (red dot)
- F9 to toggle breakpoint
- Ctrl+Shift+F9 to remove all breakpoints

**Types of Breakpoints:**

#### **A. Conditional Breakpoints**
```
Right-click breakpoint → Edit Breakpoint → Add condition

Examples:
- Python: i == 50 or value > 1000
- Go: count > 100 && name == "test"
- Rust: x.len() > 5
- C/C++: ptr != NULL && *ptr == 42
```

#### **B. Hit Count Breakpoints**
```
Break only after hitting N times:
- "Hit Count: = 10" (exactly 10th hit)
- "Hit Count: > 100" (after 100 hits)
- "Hit Count: % 10 == 0" (every 10th hit)
```

#### **C. Logpoints** (Breakpoint without stopping)
```
Right-click line → Add Logpoint

Examples:
- Python: {variable_name} = {value} at iteration {i}
- Go: Value: {myVar}, Type: {reflect.TypeOf(myVar)}
- Rust: {format!("{:?}", my_struct)}
- C/C++: i={i}, arr[i]={arr[i]}
```

### **2. Strategic Breakpoint Placement**

```
□ Function entry points
□ Before loops (check initialization)
□ Inside loops (check iterations, especially first and last)
□ After loops (verify final state)
□ Before/after critical operations (malloc, file ops, network)
□ Error handling paths
□ Return statements
□ Conditional branches (both true and false paths)
```

## III. Interactive Debugging Techniques

### **A. Debug Console Commands**

#### **Python (during debug session):**
```python
# Evaluate expressions
variable_name
len(my_list)
sum([x for x in arr if x > 0])

# Modify variables
variable_name = 42
my_list.append(100)

# Import and use modules
import math
math.sqrt(16)

# Check type and attributes
type(obj)
dir(obj)
vars(obj)
```

#### **Go (Debug Console):**
```go
// Print variables
p variableName
p myStruct

// Print detailed info
p myStruct.field
p len(mySlice)

// Call functions (limited)
call someFunction(arg)
```

#### **Rust (LLDB Console):**
```rust
// Print variable
p variable_name
p *pointer_name

// Print with format
p/x number  // hexadecimal
p/t number  // binary
p/d number  // decimal

// Expression evaluation
expr my_vec.len()
expr my_string.contains("test")

// Memory examination
x/10xw &array  // examine 10 words in hex
```

#### **C/C++ (GDB Console):**
```bash
# Print variables
p variable_name
p *pointer
p array[5]
p struct_var.member

# Print array
p *array@10  # first 10 elements

# Format specifiers
p/x number  # hex
p/t number  # binary
p/c number  # as character

# Memory examination
x/10xw address  # 10 words in hex
x/s string_ptr  # as string

# Function calls
call function_name(args)

# Set variables
set var x = 10
```

### **B. Watch Expressions**

**Add watches in VSCode:**
1. Debug sidebar → Watch section
2. Click + to add expression
3. Updates automatically during debugging

**Useful watch expressions:**

```python
# Python
len(my_list)
[x for x in arr if x % 2 == 0]  # even numbers
vars(self)  # all instance variables
```

```go
// Go
len(mySlice)
cap(mySlice)
&variable  // address
```

```rust
// Rust
vec.len()
vec.capacity()
std::mem::size_of_val(&variable)
```

```c
// C/C++
sizeof(array)/sizeof(array[0])
ptr != NULL
*ptr
```

## IV. Command-Line Debugging Tools

### **A. GDB (for C/C++, Rust, Go)**

**Basic GDB Commands:**
```bash
# Compile with debug symbols
gcc -g -O0 program.c -o program
g++ -g -O0 program.cpp -o program
cargo build  # Rust (debug by default)

# Start GDB
gdb ./program
gdb --args ./program arg1 arg2

# Essential commands
(gdb) break main              # breakpoint at main
(gdb) break file.c:42         # breakpoint at line
(gdb) break function_name     # breakpoint at function
(gdb) run                     # start execution
(gdb) run arg1 arg2           # with arguments
(gdb) continue (c)            # continue execution
(gdb) next (n)                # step over
(gdb) step (s)                # step into
(gdb) finish                  # run until function returns
(gdb) print var (p var)       # print variable
(gdb) backtrace (bt)          # call stack
(gdb) frame 2                 # switch to frame 2
(gdb) info locals             # local variables
(gdb) info args               # function arguments
(gdb) list                    # show source code
(gdb) quit                    # exit
```

**Advanced GDB:**
```bash
# Conditional breakpoints
(gdb) break 42 if i == 100

# Watch points (break when value changes)
(gdb) watch variable_name
(gdb) watch *(int*)0x12345678  # watch memory location

# Catch points
(gdb) catch throw              # break on C++ exceptions
(gdb) catch syscall            # break on system calls

# Display (auto-print on each stop)
(gdb) display variable_name
(gdb) display/x pointer        # in hex

# Examine memory
(gdb) x/10xw address           # 10 words in hex
(gdb) x/10i address            # 10 instructions

# Reverse debugging (if recorded)
(gdb) record
(gdb) reverse-next             # step backward
(gdb) reverse-continue         # run backward
```

### **B. LLDB (for Rust, C/C++, preferred on Linux)**

```bash
# Start LLDB
lldb ./program

# Similar to GDB but different syntax
(lldb) breakpoint set --name main
(lldb) breakpoint set --file main.rs --line 42
(lldb) process launch (run)
(lldb) thread step-over (next)
(lldb) thread step-in (step)
(lldb) frame variable          # show locals
(lldb) bt                      # backtrace
(lldb) exit
```

### **C. Delve (Go-specific debugger)**

```bash
# Install
go install github.com/go-delve/delve/cmd/dlv@latest

# Debug commands
dlv debug                      # debug main package
dlv test                       # debug tests
dlv exec ./binary              # debug compiled binary

# Inside delve
(dlv) break main.main
(dlv) break main.go:42
(dlv) continue (c)
(dlv) next (n)
(dlv) step (s)
(dlv) print variable
(dlv) goroutines               # list goroutines
(dlv) goroutine 2              # switch to goroutine
(dlv) stack                    # show stack trace
```

### **D. Python Debugger (pdb)**

```bash
# Built-in Python debugger
python -m pdb script.py

# Or insert in code
import pdb; pdb.set_trace()    # Python < 3.7
breakpoint()                   # Python >= 3.7

# Commands
(Pdb) l(ist)                   # show code
(Pdb) n(ext)                   # step over
(Pdb) s(tep)                   # step into
(Pdb) c(ontinue)              # continue
(Pdb) p variable               # print variable
(Pdb) pp variable              # pretty print
(Pdb) w(here)                  # stack trace
(Pdb) u(p)                     # up stack frame
(Pdb) d(own)                   # down stack frame
(Pdb) b(reak) 42               # set breakpoint
(Pdb) b module.function        # break at function
(Pdb) cl(ear)                  # clear breakpoints
(Pdb) q(uit)                   # exit

# Better alternative: ipdb
pip install ipdb
import ipdb; ipdb.set_trace()
```

## V. Memory Debugging Tools (Linux)

### **A. Valgrind (C/C++)**

```bash
# Install
sudo apt install valgrind

# Memory leak detection
valgrind --leak-check=full ./program

# More verbose
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./program

# Cache profiling
valgrind --tool=cachegrind ./program

# Heap profiling
valgrind --tool=massif ./program

# Thread error detection
valgrind --tool=helgrind ./program
```

**Common Valgrind Errors:**
```
- Invalid read/write: accessing memory you don't own
- Use of uninitialized value: reading before writing
- Invalid free: freeing memory twice or wrong pointer
- Memory leak: allocated but never freed
- Mismatched free: malloc/delete mismatch
```

### **B. AddressSanitizer (ASan)**

```bash
# Compile with ASan (C/C++)
gcc -g -fsanitize=address -fno-omit-frame-pointer program.c -o program
g++ -g -fsanitize=address -fno-omit-frame-pointer program.cpp -o program

# Run normally
./program

# Rust (nightly)
RUSTFLAGS="-Z sanitizer=address" cargo +nightly build --target x86_64-unknown-linux-gnu

# Go (experimental)
go build -asan
```

**ASan detects:**
- Buffer overflows (stack and heap)
- Use after free
- Use after return
- Double free
- Memory leaks

### **C. UndefinedBehaviorSanitizer (UBSan)**

```bash
# C/C++
gcc -g -fsanitize=undefined program.c -o program

# Rust
RUSTFLAGS="-Z sanitizer=undefined" cargo +nightly build
```

**UBSan detects:**
- Integer overflow
- Division by zero
- Null pointer dereference
- Invalid shifts
- Out of bounds array access

### **D. ThreadSanitizer (TSan)**

```bash
# C/C++
gcc -g -fsanitize=thread program.c -o program -lpthread

# Go (built-in)
go build -race

# Rust
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly build
```

**TSan detects:**
- Data races
- Deadlocks (Go only)

## VI. Profiling & Performance Debugging

### **A. Linux `perf` Tool**

```bash
# Install
sudo apt install linux-tools-common linux-tools-generic

# Record performance data
perf record ./program
perf record -g ./program  # with call graph

# Analyze
perf report

# Live view
perf top

# CPU profiling
perf stat ./program

# Specific events
perf stat -e cache-misses,cache-references ./program
```

### **B. Language-Specific Profilers**

#### **Python:**
```bash
# cProfile (built-in)
python -m cProfile -s cumulative script.py

# line_profiler (install first)
pip install line_profiler
kernprof -l -v script.py

# memory_profiler
pip install memory_profiler
python -m memory_profiler script.py

# py-spy (sampling profiler)
pip install py-spy
py-spy record -o profile.svg -- python script.py
```

#### **Go:**
```go
// CPU profiling
import _ "net/http/pprof"
import "runtime/pprof"

// In code
f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()

// View
go tool pprof cpu.prof
```

```bash
# Built-in profiling
go test -cpuprofile cpu.prof -memprofile mem.prof -bench .
go tool pprof cpu.prof
```

#### **Rust:**
```bash
# Flamegraph
cargo install flamegraph
cargo flamegraph

# Valgrind cachegrind
cargo build --release
valgrind --tool=cachegrind ./target/release/binary

# perf
cargo build --release
perf record --call-graph dwarf ./target/release/binary
perf report
```

#### **C/C++:**
```bash
# gprof
gcc -pg program.c -o program
./program
gprof program gmon.out > analysis.txt

# Or use perf (better)
perf record -g ./program
perf report
```

## VII. Logging & Tracing Strategies

### **A. Strategic Logging**

```python
# Python - structured logging
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def function():
    logger.debug(f"Entering function with params: {params}")
    logger.info(f"Processing {count} items")
    logger.warning(f"Suspicious value: {value}")
    logger.error(f"Failed to process: {error}")
```

```go
// Go - structured logging with zerolog
import "github.com/rs/zerolog/log"

log.Debug().
    Str("function", "myFunc").
    Int("value", value).
    Msg("Debug info")
```

```rust
// Rust - tracing crate
use tracing::{debug, info, warn, error, instrument};

#[instrument]
fn my_function(value: i32) {
    debug!("Processing value: {}", value);
    info!("Completed successfully");
}
```

```c
// C - macro-based logging
#define DEBUG_PRINT(fmt, ...) \
    fprintf(stderr, "[%s:%d] " fmt "\n", __FILE__, __LINE__, ##__VA_ARGS__)

DEBUG_PRINT("Value: %d, Pointer: %p", value, ptr);
```

### **B. Assertion Strategies**

```python
# Python
assert condition, "Error message with context"
assert len(arr) > 0, f"Array is empty, expected non-empty"

# Disable with python -O (optimization)
```

```go
// Go - panic for invariant violations
if ptr == nil {
    panic("unexpected nil pointer")
}

// Assertions in tests
require.NotNil(t, ptr)
assert.Equal(t, expected, actual)
```

```rust
// Rust
assert!(condition, "Error message");
assert_eq!(actual, expected);
debug_assert!(condition);  // Only in debug builds
```

```c
// C/C++
#include <assert.h>
assert(ptr != NULL);
assert(size > 0 && "Size must be positive");

// Disable with -DNDEBUG
```

## VIII. Network & System Call Debugging

### **A. strace - System Call Tracer**

```bash
# Trace all system calls
strace ./program

# Trace specific syscalls
strace -e open,read,write ./program
strace -e network ./program  # network calls only

# Trace with timestamps
strace -t ./program
strace -tt ./program  # microsecond precision

# Attach to running process
strace -p PID

# Save to file
strace -o trace.log ./program

# Count syscalls
strace -c ./program
```

### **B. ltrace - Library Call Tracer**

```bash
# Trace library calls
ltrace ./program

# Specific libraries
ltrace -l libname.so ./program
```

### **C. Network Debugging**

```bash
# tcpdump - capture network packets
sudo tcpdump -i any port 8080
sudo tcpdump -i any -w capture.pcap

# netstat - network connections
netstat -tuln  # listening ports
netstat -tupn  # active connections

# ss (modern netstat)
ss -tuln

# lsof - open files and sockets
lsof -i :8080  # what's using port 8080
lsof -p PID    # files opened by process
```

## IX. Debugging Patterns & Workflows

### **Pattern 1: Binary Search Debugging**

```
1. Find a working version (or minimal input)
2. Find a broken version (or failing input)
3. Test midpoint
4. Recurse into broken half
5. Identify exact change/input that breaks it
```

**Implementation:**
```bash
# Git bisect for code regression
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
git bisect run ./test_script.sh
```

### **Pattern 2: Rubber Duck Debugging**

```
1. Explain code line-by-line out loud
2. Describe what you EXPECT to happen
3. Describe what ACTUALLY happens
4. Identify the discrepancy
```

### **Pattern 3: Hypothesis-Driven Debugging**

```
1. Observe the symptom
2. Form a hypothesis about the cause
3. Design a test to verify hypothesis
4. Run the test
5. If wrong, form new hypothesis
6. If right, fix and verify
```

### **Pattern 4: Delta Debugging**

```
1. Start with failing large input
2. Remove half the input
3. Does it still fail?
   - Yes: Continue with smaller input
   - No: Keep the removed portion, remove other half
4. Minimize to smallest failing input
```

### **Pattern 5: Divide and Conquer**

```
1. Comment out half the code
2. Does it still fail?
3. Recurse into the problematic half
4. Narrow down to exact lines
```

## X. VSCode Debugging Shortcuts

```
F5              - Start debugging
F9              - Toggle breakpoint
F10             - Step over
F11             - Step into
Shift+F11       - Step out
Shift+F5        - Stop debugging
Ctrl+Shift+F5   - Restart debugging
Ctrl+K Ctrl+I   - Show hover (variable inspection)
Ctrl+Shift+D    - Show debug sidebar
```

## XI. Common Bug Patterns & How to Find Them

### **1. Memory Issues (C/C++, Rust unsafe)**

```bash
# Always run with:
valgrind --leak-check=full ./program
# or compile with
gcc -fsanitize=address,undefined
```

**Look for:**
- Segmentation faults → usually null/dangling pointers
- Corrupted output → buffer overflows, use-after-free
- Intermittent crashes → uninitialized memory

### **2. Race Conditions**

```bash
# Always test concurrent code with:
go build -race  # Go
gcc -fsanitize=thread  # C/C++
```

**Look for:**
- Intermittent failures
- Different results on different runs
- Heisenbug (disappears when debugging)

### **3. Off-by-One Errors**

**Debug strategy:**
- Print array/slice bounds
- Add assertions: `assert(i >= 0 && i < size)`
- Test with size 0, 1, 2

### **4. Integer Overflow**

```bash
# Compile with overflow detection
gcc -fsanitize=signed-integer-overflow
# Rust panics by default in debug mode
```

### **5. Logic Errors**

**Debug strategy:**
- Add asserts for invariants
- Print expected vs actual at each step
- Trace through with minimal example

### **6. Performance Issues**

```bash
# Profile first, optimize second
perf record -g ./program
perf report

# For I/O issues
strace -c ./program  # counts syscalls
```

## XII. Emergency Debugging Checklist

When nothing works:

```
□ Did I compile with debug symbols? (-g flag)
□ Did I save the file before running?
□ Am I running the correct binary?
□ Are my print statements actually executing?
□ Did I check the simplest possible input?
□ Did I read the error message CAREFULLY?
□ Did I check return values?
□ Did I verify my assumptions with print/asserts?
□ Did I try explaining it out loud?
□ Did I take a break? (seriously, helps)
□ Did I search for the exact error message?
□ Did I check if it's a known issue (GitHub/Stack Overflow)?
□ Did I try a different approach entirely?
```

## XIII. Useful `.vscode/settings.json` Configurations

```json
{
    "editor.rulers": [80, 120],
    "files.trimTrailingWhitespace": true,
    "editor.formatOnSave": true,
    
    // Python
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    
    // Go
    "go.lintOnSave": "package",
    "go.vetOnSave": "package",
    
    // Rust
    "rust-analyzer.checkOnSave.command": "clippy",
    
    // C/C++
    "C_Cpp.default.cppStandard": "c++17",
    "C_Cpp.default.cStandard": "c11",
    
    // Error Lens (highly recommended)
    "errorLens.enabled": true
}
```

---

**Pro Tip**: Create debug aliases in your `~/.bashrc`:

```bash
# Add to ~/.bashrc
alias gdb='gdb -q'  # quiet mode
alias valg='valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes'
alias pydbg='python -m pdb'
alias gorace='go test -race ./...'
```

Remember: **The best debugging tool is a clear understanding of what your code SHOULD do.** If you can't explain it simply, you don't understand it well enough to debug it effectively.