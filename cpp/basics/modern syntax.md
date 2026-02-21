# Modern C++ Complete Syntax Reference
## Basic to Advanced — C++11 through C++23
### Every Feature. Detailed Explanations. Zero Fluff.

---

> **How to use this guide:**
> Read linearly if you're building from scratch.
> Each feature includes: *What it is → Why it exists → How it works → Nuances & traps → Code.*

---

# PART I — C++11: THE REVOLUTION

C++11 was the most significant update since C++ was born. It fundamentally changed
how the language is written. If you write pre-C++11 code today, you are doing it wrong.

---

## 1. `auto` — Type Deduction

### What it is
`auto` tells the compiler: *"you know the type — you figure it out."*
The compiler deduces the type from the initializer expression at compile time.
There is **zero runtime cost**. This is purely a compile-time feature.

### Why it exists
Before `auto`, declaring variables required repeating type information the compiler
already knew:
```cpp
std::map<std::string, std::vector<int>>::iterator it = m.begin();
// The compiler knows m.begin() returns this iterator type.
// Why should you repeat it?
```

### How it works
```cpp
auto x = 42;            // int   (literal 42 is int)
auto y = 42u;           // unsigned int
auto z = 42L;           // long
auto d = 3.14;          // double
auto f = 3.14f;         // float
auto s = "hello";       // const char* (NOT std::string — important!)
auto str = std::string{"hello"};  // std::string

// With containers
std::vector<int> v{1,2,3};
auto it = v.begin();    // std::vector<int>::iterator — saves typing
auto size = v.size();   // size_t (unsigned)

// With functions
auto result = std::make_pair(1, 3.14);  // std::pair<int, double>
```

### Critical Rules — What `auto` drops
`auto` always strips top-level `const` and references from the deduced type.
This is the #1 source of confusion.

```cpp
const int x = 42;
auto a = x;       // int — NOT const int. const is stripped!
auto& b = x;      // const int& — reference preserves const
const auto c = x; // const int — you re-add const explicitly

int arr[5] = {1,2,3,4,5};
auto d = arr;     // int* — arrays decay to pointers with auto!
auto& e = arr;    // int (&)[5] — reference preserves array type

// Function pointers
int add(int a, int b) { return a+b; }
auto fp = add;    // int (*)(int, int) — function decays to pointer
auto& fr = add;   // int (&)(int, int) — reference preserves function
```

### `auto` in function return types (C++14)
```cpp
// Trailing return type (C++11)
auto add(int a, int b) -> int { return a + b; }

// Deduced return type (C++14)
auto square(int x) { return x * x; }  // deduced as int

// Multiple return paths must deduce same type
auto f(bool condition) {
    if (condition) return 42;     // int
    return 3.14;                  // double — ERROR: conflicting deductions
}
```

### `auto&&` — Universal/Forwarding Reference
```cpp
// auto&& deduces to lvalue ref OR rvalue ref depending on initializer
auto&& a = 42;         // int&& — rvalue ref (42 is rvalue)
int x = 5;
auto&& b = x;          // int& — lvalue ref (x is lvalue)

// In range-for — the most correct form for generic code
for (auto&& elem : container) {
    // Works correctly whether container returns values, refs, or proxies
}
```

---

## 2. `decltype` — Type Inspection Without Evaluation

### What it is
`decltype(expr)` asks: *"what is the type of this expression?"*
Critically, the expression is **never evaluated** — only its type is inspected.

### Why it exists
Sometimes you need a type that you cannot name or that depends on other deductions.
`auto` deduces from assignment, `decltype` inspects any expression.

```cpp
int x = 5;
double y = 3.14;

decltype(x) a;              // int — same type as x
decltype(x + y) b;          // double — x+y promotes to double
decltype(x) c = x;          // int

// decltype does NOT evaluate the expression
int arr[100];
decltype(arr[99]) elem = arr[0];  // int& — arr[99] is never accessed!

// The crucial difference between decltype(x) and decltype((x)):
int z = 5;
decltype(z)   t1 = z;  // int   — named variable: gives its type
decltype((z)) t2 = z;  // int&  — parenthesized: always an lvalue ref
// Rule: decltype of a parenthesized lvalue is always an lvalue reference
```

### `decltype(auto)` — Reference-Preserving Return Deduction (C++14)
```cpp
int x = 5;
int& get_ref() { return x; }

// auto strips the reference:
auto a = get_ref();        // int — COPY, not reference

// decltype(auto) preserves the reference:
decltype(auto) b = get_ref();  // int& — true reference

// Most useful for perfect return forwarding:
template<typename F, typename... Args>
decltype(auto) call_and_return(F&& f, Args&&... args) {
    return std::forward<F>(f)(std::forward<Args>(args)...);
    // If f returns int&, we return int& (not a copy)
}
```

### Trailing Return Type with `decltype`
```cpp
// Before C++14 deduced returns — use decltype in trailing return
template<typename A, typename B>
auto add(A a, B b) -> decltype(a + b) {
    return a + b;
}
// Why? Because at the point of -> decltype(a+b), a and b are in scope.
// The return type is whatever a+b produces (int, double, etc.)
```

---

## 3. Rvalue References & Move Semantics

### The Fundamental Problem Move Solves
This is the most important C++11 feature. Understand it deeply.

Before C++11, passing or returning objects always meant copying.
Copying a `std::vector<int>` with 1 million elements meant:
1. Allocate 1 million ints on the heap
2. Copy each one
3. Possibly destroy the original

But what if the original is a **temporary**? You're copying then destroying.
That's work done for nothing.

### lvalue vs rvalue — The Core Distinction
```cpp
// lvalue: has a name, persists beyond the expression, addressable
int x = 5;      // x is an lvalue
int* p = &x;    // can take address — confirms lvalue

// rvalue: temporary, no persistent identity, cannot take address
5              // literal — rvalue
x + 1          // expression result — rvalue
std::string{"hello"}  // temporary — rvalue
```

### Rvalue References (`T&&`)
```cpp
int x = 5;
int& lref = x;          // lvalue reference — OK
int& lref2 = 5;         // ERROR: cannot bind lvalue ref to rvalue

int&& rref = 5;         // rvalue reference — OK: binds to rvalue
int&& rref2 = x;        // ERROR: cannot bind rvalue ref to lvalue
int&& rref3 = std::move(x);  // OK: std::move casts x to rvalue
```

### `std::move` — Casting to Rvalue
```cpp
// std::move does NOT move anything. It is a CAST.
// It casts an lvalue to an rvalue, enabling move semantics.
// Implementation:
template<typename T>
constexpr std::remove_reference_t<T>&& move(T&& t) noexcept {
    return static_cast<std::remove_reference_t<T>&&>(t);
}

// After std::move, the object is in a "valid but unspecified state"
// You can still assign to it or destroy it, but don't read its value.
std::vector<int> v{1,2,3,4,5};
std::vector<int> v2 = std::move(v);  // v2 steals v's buffer
// v is now empty (valid but unspecified — in practice, empty for vector)
// v2 has the 5 elements — no allocation, no copy — O(1) operation
```

### Move Constructor & Move Assignment
```cpp
class Buffer {
public:
    int* data;
    size_t size;

    // Default constructor
    Buffer() : data(nullptr), size(0) {}

    // Constructor
    Buffer(size_t n) : data(new int[n]), size(n) {}

    // Destructor
    ~Buffer() { delete[] data; }

    // Copy constructor — expensive O(n)
    Buffer(const Buffer& other) : size(other.size) {
        data = new int[size];
        std::copy(other.data, other.data + size, data);
        // We allocated new memory and copied every element
    }

    // Copy assignment — expensive O(n)
    Buffer& operator=(const Buffer& other) {
        if (this == &other) return *this;  // self-assignment check
        delete[] data;                      // free existing resource
        size = other.size;
        data = new int[size];
        std::copy(other.data, other.data + size, data);
        return *this;
    }

    // Move constructor — O(1) — just steal the pointer
    Buffer(Buffer&& other) noexcept  // noexcept is CRITICAL for STL optimizations
        : data(other.data), size(other.size) {
        other.data = nullptr;  // leave source in valid state
        other.size = 0;
        // No allocation. No element copy. Just pointer reassignment.
    }

    // Move assignment — O(1)
    Buffer& operator=(Buffer&& other) noexcept {
        if (this == &other) return *this;
        delete[] data;          // free our current resource
        data = other.data;      // steal their resource
        size = other.size;
        other.data = nullptr;   // nullify source
        other.size = 0;
        return *this;
    }
};
```

### Why `noexcept` on Move Matters
```cpp
// std::vector::push_back needs to reallocate sometimes.
// When it does, it moves/copies elements to new storage.
// It will ONLY use your move constructor if it is noexcept.
// If move might throw, it falls back to copy (to preserve strong guarantee).
// Conclusion: always mark move operations noexcept.

// The Rule of Five: if you define any of these, define all five:
// 1. Destructor
// 2. Copy constructor
// 3. Copy assignment operator
// 4. Move constructor
// 5. Move assignment operator
```

### `std::exchange` — Cleaner Move Pattern (C++14)
```cpp
#include <utility>

// std::exchange(obj, new_val) — sets obj = new_val, returns old obj
// Perfect for move constructors:
Buffer(Buffer&& other) noexcept
    : data(std::exchange(other.data, nullptr))
    , size(std::exchange(other.size, 0)) {
    // Single expression: steal value AND nullify source
}
```

---

## 4. Perfect Forwarding

### The Problem
When you wrap a function call, you need to pass arguments with their exact
value category preserved. Without forwarding, temporaries become lvalues.

```cpp
// Naive wrapper — breaks rvalue semantics
template<typename T>
void wrapper(T arg) {        // arg is always an lvalue (it has a name)
    actual_function(arg);    // always passes as lvalue — loses rvalue-ness
}

// Even with T&&:
template<typename T>
void wrapper(T&& arg) {      // arg has a name — it IS an lvalue in the body
    actual_function(arg);    // still passing as lvalue!
}
```

### `std::forward` — Conditional Cast
```cpp
// std::forward<T>(arg) — if T was deduced as lvalue ref: passes as lvalue
//                       — if T was deduced as rvalue ref: casts to rvalue
template<typename T>
void wrapper(T&& arg) {
    actual_function(std::forward<T>(arg));  // value category preserved!
}

// How template deduction makes this work (reference collapsing):
// T&& where T = int&  → int& &&  → int&   (lvalue stays lvalue)
// T&& where T = int   → int&&            (rvalue stays rvalue)
// Rule: & + & = &, & + && = &, && + & = &, && + && = &&
// T&&  in template context is NOT an rvalue ref — it's a forwarding ref!

// Real-world: make_unique uses this
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
    // Constructor receives exact same value categories as the caller passed
}
```

---

## 5. Lambda Expressions

### What They Are
A lambda is an anonymous function object (a *closure*) defined inline.
The compiler generates a unique class with `operator()` for each lambda.

### Basic Syntax
```cpp
// [capture-list](parameter-list) -> return-type { body }
// All parts except [] and {} are optional.

auto greet = []() { std::cout << "Hello\n"; };
greet();  // call it

auto add = [](int a, int b) { return a + b; };
int sum = add(3, 4);  // 7

auto square = [](double x) -> double { return x * x; };
```

### Capture — The Heart of Lambdas
Capture lets the lambda access variables from the enclosing scope.

```cpp
int x = 10, y = 20, z = 30;

// By value — lambda gets its own copy at time of capture
auto f1 = [x]() { return x; };  // x is COPIED into the lambda
x = 99;
f1();  // returns 10 — NOT 99, because x was copied at capture time

// By reference — lambda accesses the original variable
auto f2 = [&x]() { return x; };
x = 99;
f2();  // returns 99 — accesses live x

// DANGER: if lambda outlives the captured reference, you have UB
auto make_bad_lambda() {
    int local = 42;
    return [&local]() { return local; };  // UB! local is destroyed
    // Never capture local variables by reference in returned lambdas
}

// Multiple captures
auto f3 = [x, &y]() { return x + y; };  // x by value, y by reference

// Capture all by value
auto f4 = [=]() { return x + y + z; };  // all three copied

// Capture all by reference
auto f5 = [&]() { x++; y++; };  // all by reference

// Mixed: capture all by value, but x by reference
auto f6 = [=, &x]() { x++; return y + z; };  // x ref, y/z value

// Init capture (C++14) — create new variables in capture
auto f7 = [val = x * 2]() { return val; };  // val = 20, new variable
auto f8 = [ptr = std::make_unique<int>(42)]() { return *ptr; };  // move-only!

// this capture — capture the enclosing object
struct Widget {
    int value = 10;
    auto get_adder() {
        return [this]() { return value; };   // captures this pointer
        // C++17: [*this]() — captures entire object by value (copy)
    }
};
```

### Mutable Lambdas
```cpp
// By default, value-captured variables are const inside the lambda.
// 'mutable' removes this restriction.
int count = 0;
auto counter = [count]() mutable {
    return ++count;  // modifies the lambda's OWN copy of count
};
counter();  // 1
counter();  // 2
count;      // still 0 — the original is unchanged

// Without mutable:
auto bad = [count]() {
    return ++count;  // ERROR: count is const
};
```

### Generic Lambdas (C++14)
```cpp
// 'auto' parameters make the lambda a template
auto print = [](auto x) { std::cout << x << '\n'; };
print(42);
print(3.14);
print("hello");
print(std::vector<int>{1,2,3});  // works for anything with operator<<

// Multiple auto parameters
auto add = [](auto a, auto b) { return a + b; };
add(1, 2);       // int
add(1.0, 2.0);   // double

// Template lambda syntax (C++20)
auto typed_add = []<typename T>(T a, T b) -> T { return a + b; };
// Forces both arguments to be the same type T
auto vec_size = []<typename T>(std::vector<T>& v) { return v.size(); };
```

### Immediately Invoked Lambda
```cpp
// Define and call in one expression
int result = [](int x, int y) { return x + y; }(3, 4);  // 7

// Useful for complex initialization of const variables
const std::vector<int> primes = []() {
    std::vector<int> v;
    // ... sieve algorithm ...
    return v;
}();
// v is const but was built procedurally
```

### Lambda as Comparator
```cpp
std::vector<std::string> words{"banana", "apple", "cherry"};

// Sort by length
std::sort(words.begin(), words.end(),
    [](const std::string& a, const std::string& b) {
        return a.size() < b.size();
    });

// Custom priority queue
auto cmp = [](int a, int b) { return a > b; };  // min-heap
std::priority_queue<int, std::vector<int>, decltype(cmp)> pq(cmp);
```

---

## 6. Uniform Initialization (Brace Initialization)

### Why It Exists — The Problem with Old Initialization
```cpp
// Pre-C++11: multiple, inconsistent initialization syntaxes
int a = 5;           // copy initialization
int b(5);            // direct initialization
int c;               // default (uninitialized — dangerous!)
int arr[] = {1,2,3}; // aggregate initialization

// Most dangerous: narrowing conversions happen silently
int x = 3.99;        // compiles! x = 3, precision silently lost
```

### Brace Initialization
```cpp
// Works everywhere, consistent syntax, catches narrowing
int a{5};
int b{};            // zero-initialized (0), NOT uninitialized

double d{3.14};
int x{3.99};        // COMPILE ERROR: narrowing conversion
int y{(int)3.99};   // OK — explicit cast, your responsibility

// Aggregates
struct Point { int x, y, z; };
Point p{1, 2, 3};   // field by field

// Containers
std::vector<int> v{1, 2, 3, 4, 5};
std::array<int, 3> arr{1, 2, 3};
std::map<std::string, int> m{{"one", 1}, {"two", 2}, {"three", 3}};
std::pair<int, double> pair{42, 3.14};

// New expressions
auto p = new Point{1, 2, 3};

// Function arguments
void take_point(Point p) {}
take_point({1, 2, 3});  // brace-init without naming the type

// Return values
Point make_origin() { return {0, 0, 0}; }
```

### `std::initializer_list` — The Mechanism Behind Brace Init
```cpp
#include <initializer_list>

// When you write SomeClass{1,2,3}, the compiler looks for a constructor
// taking std::initializer_list<T> FIRST. This has highest priority.

class IntList {
public:
    // This constructor wins over all others when braces are used
    IntList(std::initializer_list<int> init) {
        for (int val : init) {
            data_.push_back(val);
        }
    }

    // Regular constructor
    IntList(int size, int default_val) {
        data_.assign(size, default_val);
    }

private:
    std::vector<int> data_;
};

IntList a{1, 2, 3};       // calls initializer_list constructor: [1, 2, 3]
IntList b(3, 0);           // calls size constructor: [0, 0, 0]
IntList c{3, 0};           // calls initializer_list constructor: [3, 0]!
// This is the famous vector<int> ambiguity:
std::vector<int> v1(3, 0); // 3 elements, all 0: [0, 0, 0]
std::vector<int> v2{3, 0}; // 2 elements, 3 and 0: [3, 0]
```

### Value Initialization Rules
```cpp
// {} triggers value initialization:
// - Scalars (int, double, pointers): zero-initialized
// - Classes with constructors: default constructor called
// - Classes without constructors: zero-initialized

int x{};       // 0
double d{};    // 0.0
int* p{};      // nullptr
bool b{};      // false

struct Plain { int x; double y; };
Plain obj{};   // x=0, y=0.0 — members are zero-initialized
```

---

## 7. Range-Based For Loop

### Basic Usage
```cpp
// for (declaration : range) — iterates over every element
std::vector<int> v{1, 2, 3, 4, 5};

// By value — COPY each element (expensive for large types)
for (int x : v) { }

// By const reference — READ ONLY (preferred for read access)
for (const int& x : v) { }
for (const auto& x : v) { }  // same, auto is better for complex types

// By reference — MODIFY elements in place
for (int& x : v) { x *= 2; }
for (auto& x : v) { }

// Universal reference — works correctly for all iterator types
for (auto&& x : v) { }
// This is the safest generic form (important for proxy iterators)
```

### What It Expands To
```cpp
// This:
for (auto& x : container) { use(x); }

// Expands to approximately:
{
    auto&& __range = container;
    auto __begin = __range.begin();
    auto __end = __range.end();
    for (; __begin != __end; ++__begin) {
        auto& x = *__begin;
        use(x);
    }
}
// So: any type with begin()/end() (or free functions) works
```

### Making Custom Types Work
```cpp
struct NumberRange {
    int start, end;

    struct Iterator {
        int current;
        bool operator!=(const Iterator& other) const { return current != other.current; }
        Iterator& operator++() { ++current; return *this; }
        int operator*() const { return current; }
    };

    Iterator begin() const { return {start}; }
    Iterator end()   const { return {end}; }
};

NumberRange range{1, 6};
for (int n : range) {
    std::cout << n << ' ';  // 1 2 3 4 5
}
```

### With Structured Bindings (C++17)
```cpp
std::map<std::string, int> scores{{"Alice", 95}, {"Bob", 87}, {"Carol", 92}};
for (const auto& [name, score] : scores) {
    std::cout << name << ": " << score << '\n';
}
```

---

## 8. Smart Pointers

### The Philosophy — Ownership Semantics
Every resource must have a clear owner. The owner is responsible for cleanup.
Smart pointers encode ownership in the type system.
If you ever write `delete` in modern C++, something is wrong.

### `std::unique_ptr` — Exclusive Ownership
```cpp
#include <memory>

// Create — prefer make_unique
auto up = std::make_unique<int>(42);          // single object
auto uarr = std::make_unique<int[]>(10);       // array of 10 ints

// Access
*up;              // dereference: 42
up.get();         // raw pointer (don't own it, don't delete it!)
up->member;       // arrow access for class types

// Ownership transfer — can only MOVE, never copy
auto up2 = std::move(up);  // up is now null, up2 owns the int
// up == nullptr after this

// Transfer to a function — function takes ownership
void take(std::unique_ptr<int> p) { /* p destroyed at end */ }
take(std::move(up2));  // up2 is null after this

// Return from function — most common pattern (no move needed due to NRVO/RVO)
std::unique_ptr<Widget> create_widget() {
    return std::make_unique<Widget>(/* args */);
}

// Check
if (up) { /* non-null */ }
if (up == nullptr) { /* null */ }

// Reset — destroy current, optionally own new
up.reset();              // destroy, become null
up.reset(new int(99));   // destroy old, own new

// Release — give up ownership WITHOUT destroying
int* raw = up.release(); // up is null, YOU must delete raw
delete raw;              // now you own it

// Custom deleter
auto file = std::unique_ptr<FILE, decltype(&fclose)>(
    fopen("data.txt", "r"),
    &fclose  // called instead of delete
);

// Arrays
auto arr = std::make_unique<int[]>(5);
arr[0] = 1;  // subscript works for array unique_ptr
```

### `std::shared_ptr` — Shared Ownership (Reference Counting)
```cpp
// Multiple owners — destroyed when last owner releases it
auto sp1 = std::make_shared<int>(42);  // ref count = 1
{
    auto sp2 = sp1;   // ref count = 2
    auto sp3 = sp1;   // ref count = 3
    // sp2, sp3 destroyed at end of block
}
// ref count = 1 — sp1 is the only owner
// sp1 destroyed at its scope end — object freed

// Control block
// make_shared allocates object + control block in ONE allocation (better)
// shared_ptr(new T) does TWO allocations (object + separate control block)
// Always prefer make_shared

// Use for: shared caches, shared state, graph nodes with multiple parents
// Avoid for: cases where unique_ptr works — shared_ptr has overhead

// shared_ptr cast operations
std::shared_ptr<Base> base = std::make_shared<Derived>();
auto derived = std::dynamic_pointer_cast<Derived>(base);   // dynamic cast
auto casted  = std::static_pointer_cast<Derived>(base);    // static cast
auto const_p = std::const_pointer_cast<const int>(sp1);    // add const
```

### `std::weak_ptr` — Non-Owning Observer
```cpp
// weak_ptr breaks reference cycles and provides safe observation
// Does NOT increment reference count

std::shared_ptr<int> sp = std::make_shared<int>(42);
std::weak_ptr<int> wp = sp;  // ref count still 1

// Must "lock" to safely access the pointed-to object
if (auto locked = wp.lock()) {    // returns shared_ptr (ref count +1)
    std::cout << *locked;         // safe to use
}  // locked destroyed, ref count -1

// sp destroyed — ref count 0 — object freed
sp.reset();

if (auto locked = wp.lock()) {
    // This branch NOT taken — object is gone
} else {
    std::cout << "Object no longer exists\n";
}

// Common pattern: breaking cycles
struct Node {
    std::shared_ptr<Node> next;   // owns next
    std::weak_ptr<Node> prev;     // observes prev WITHOUT owning
    // If both were shared_ptr, you'd have a cycle — memory leak!
};
```

---

## 9. `nullptr`

### The Problem with NULL
```cpp
// NULL is literally 0 (an int). This causes ambiguity:
void process(int x) { std::cout << "int version\n"; }
void process(int* p) { std::cout << "pointer version\n"; }

process(NULL);     // calls process(int) — usually wrong!
process(nullptr);  // always calls process(int*) — correct
```

### `nullptr` Details
```cpp
// nullptr has its own type: std::nullptr_t
// It can convert to any pointer type, but NOT to integer types

int* p = nullptr;        // OK
void* vp = nullptr;      // OK
bool b = (p == nullptr); // OK

// nullptr_t can be used as a type
std::nullptr_t n = nullptr;

// Useful in templates
template<typename T>
void process(T* p) {
    if (p == nullptr) return;
}
process(nullptr);  // deduces T, p = nullptr

// In conditional expressions
int* maybe = condition ? &value : nullptr;
```

---

## 10. `enum class` — Strongly Typed Enumerations

### The Old Enum's Problems
```cpp
// Old enum: pollutes namespace, implicitly converts to int
enum Color { Red, Green, Blue };
enum Direction { North, South, East, West };

// Red, Green, Blue, North, South, East, West are ALL in global scope
Color c = Red;  // OK
int x = Red;    // OK — implicit int conversion (dangerous!)
// If another enum also has Red: compiler error or wrong value
```

### `enum class` Fixes Everything
```cpp
enum class Color { Red, Green, Blue };
enum class Direction { North, South, East, West };

// Must qualify with scope
Color c = Color::Red;
Direction d = Direction::North;

// No implicit conversion to int — must be explicit
int x = Color::Red;               // ERROR: no implicit conversion
int y = static_cast<int>(Color::Red);  // OK: explicit cast

// No name collision between different enums
Color::Red;     // fine
Direction::Red; // ERROR: Red doesn't exist in Direction — fine!

// Specify underlying type (default is int)
enum class Status : uint8_t { Ok = 0, Error = 1, Pending = 2 };
enum class Flags  : uint32_t {
    None    = 0,
    Read    = 1 << 0,   // 1
    Write   = 1 << 1,   // 2
    Execute = 1 << 2,   // 4
    All     = Read | Write | Execute  // 7
};

// Forward declaration (requires type specification)
enum class Future : int;  // forward declared
void use(Future f);       // can use in declaration
enum class Future : int { A, B, C };  // define later
```

---

## 11. `constexpr` — Compile-Time Computation

### What it Does
`constexpr` declares that a function or variable CAN be evaluated at compile time.
If the arguments are compile-time constants, the result is computed at compile time —
zero runtime cost for constant values.

### `constexpr` Variables
```cpp
constexpr int MAX_SIZE = 1024;           // compile-time constant
constexpr double PI = 3.14159265358979;  // compile-time constant
constexpr auto hello = "hello";          // const char* at compile time

// Can use in contexts requiring compile-time constants:
int arr[MAX_SIZE];               // array size must be compile-time
template<int N> struct Fixed {}; // template non-type param
Fixed<MAX_SIZE> f;               // OK
```

### `constexpr` Functions
```cpp
// C++11: single return statement only
constexpr int square(int x) { return x * x; }

// C++14: relaxed — loops, branches, local variables allowed
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

constexpr int f120 = factorial(5);   // computed at compile time: 120
int n = 6;
int f720 = factorial(n);             // computed at runtime (n not constexpr)

// A constexpr function CAN run at runtime if called with non-constexpr args
// It MUST run at compile time only if used in a constexpr context
```

### `consteval` (C++20) — Compile Time ONLY
```cpp
// consteval functions MUST be called at compile time. No runtime use.
consteval int strict_square(int x) { return x * x; }

constexpr int a = strict_square(5);   // OK — compile time
int n = 5;
// int b = strict_square(n);          // ERROR: n is not constexpr
```

### `constinit` (C++20) — Guaranteed Static Initialization
```cpp
// Guarantees a variable is initialized at compile time (not runtime)
// Unlike constexpr, the variable CAN be modified after init
constinit int counter = 0;  // init at compile time, mutable at runtime
counter++;  // OK

// Solves the static initialization order fiasco for global variables
constinit std::string global_prefix = "app";  // guaranteed first
```

---

## 12. `static_assert` — Compile-Time Assertions

```cpp
// static_assert(condition, message) — checked at compile time, zero runtime cost
static_assert(sizeof(int) == 4, "This code requires 32-bit int");
static_assert(sizeof(void*) == 8, "Requires 64-bit platform");

// In templates — validates template parameters
template<typename T>
class Matrix {
    static_assert(std::is_arithmetic_v<T>, "Matrix requires numeric type");
    static_assert(!std::is_same_v<T, bool>, "bool matrix not supported");
};

// In functions
constexpr int factorial(int n) {
    static_assert(n >= 0, "factorial requires non-negative input");
    // Note: this is checked at compile time only for constexpr calls
    return n <= 1 ? 1 : n * factorial(n-1);
}

// C++17: message is optional
static_assert(sizeof(long) >= 8);
```

---

## 13. Variadic Templates

### What They Are
Templates that accept any number of template parameters.
The foundation of `std::tuple`, `std::function`, and many other library types.

```cpp
// Parameter pack: Args... represents zero or more type parameters
template<typename... Args>
void print(Args... args) {
    // sizeof...(Args) — number of types in the pack
    // sizeof...(args) — number of values in the pack
    std::cout << "argument count: " << sizeof...(args) << '\n';
}

print();           // 0 arguments
print(1);          // 1 argument
print(1, "hello", 3.14);  // 3 arguments
```

### Recursion — Pre-C++17 Expansion Pattern
```cpp
// Base case — handles empty pack
void print_all() { std::cout << '\n'; }

// Recursive case — peel off first, recurse on rest
template<typename First, typename... Rest>
void print_all(First first, Rest... rest) {
    std::cout << first;
    if constexpr (sizeof...(rest) > 0) std::cout << ", ";
    print_all(rest...);  // ... expands the pack, passes remaining args
}

print_all(1, "hello", 3.14, 'x');
// Output: 1, hello, 3.14, x
```

### Fold Expressions (C++17) — Preferred Over Recursion
```cpp
// (init op ... op pack) — collapses pack with binary operator

template<typename... Args>
auto sum(Args... args) {
    return (args + ...);  // unary right fold: ((a+b)+c)...
}
sum(1, 2, 3, 4, 5);  // 15

template<typename... Args>
auto sum_with_init(Args... args) {
    return (0 + ... + args);  // binary fold with init: handles empty pack
}

template<typename... Args>
void print_all(Args&&... args) {
    ((std::cout << args << ' '), ...);  // comma operator fold
}

template<typename... Args>
bool all_true(Args... args) {
    return (... && args);  // left fold: (((a && b) && c) && d)
}

template<typename... Args>
bool any_true(Args... args) {
    return (... || args);
}
```

### Perfect Forwarding with Variadic Templates
```cpp
// The most common use: forwarding factory functions
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
    // ... after forward expands to: forward<A0>(a0), forward<A1>(a1), ...
}

// Emplace operations use this pattern
std::vector<std::pair<int, std::string>> v;
v.emplace_back(42, "hello");  // constructed IN PLACE — no temporary pair
```

---

## 14. Type Aliases — `using`

```cpp
// using is strictly superior to typedef

// Basic alias
using Byte = unsigned char;
using Size = size_t;
using StringVec = std::vector<std::string>;

// typedef equivalent (harder to read, especially with function pointers)
typedef void (*Callback)(int, double);           // typedef — confusing syntax
using Callback = void(*)(int, double);           // using — clear syntax

// Template aliases — typedef CANNOT do this
template<typename T>
using Vec = std::vector<T>;

template<typename K, typename V>
using HashMap = std::unordered_map<K, V>;

template<typename T>
using SharedPtr = std::shared_ptr<T>;

Vec<int> vi;              // std::vector<int>
HashMap<std::string, int> scores;
SharedPtr<Widget> w;

// Policy-based: parameterize allocator, comparator, etc.
template<typename T, typename Alloc = std::allocator<T>>
using MyVec = std::vector<T, Alloc>;
```

---

## 15. `override` and `final`

```cpp
struct Animal {
    virtual std::string sound() const { return "..."; }
    virtual void move() {}
    virtual ~Animal() = default;
};

struct Dog : Animal {
    // override — compiler checks that this actually overrides a base method
    // Without override: if you misspell, you get a NEW virtual function!
    std::string sound() const override { return "Woof"; }
    void move() override {}

    // void Move() override {}    // COMPILE ERROR: no Animal::Move() to override
    // void sound() override {}   // COMPILE ERROR: wrong signature (missing const)
    // Without override, these would silently create NEW functions — subtle bug
};

// final on a class — cannot be derived from
struct Singleton final : Base {
    static Singleton& instance() {
        static Singleton s;
        return s;
    }
private:
    Singleton() {}
};

// struct DerivedFromSingleton : Singleton {};  // COMPILE ERROR

// final on a method — cannot be overridden further
struct Base {
    virtual void foo() {}
};
struct Middle : Base {
    void foo() final {}  // derived classes cannot override foo
};
struct Leaf : Middle {
    // void foo() override {}  // COMPILE ERROR
};
```

---

## 16. `= default` and `= delete`

```cpp
// = default: explicitly request compiler-generated implementation
class Widget {
public:
    Widget() = default;                          // generate default constructor
    Widget(const Widget&) = default;             // generate copy constructor
    Widget& operator=(const Widget&) = default; // generate copy assignment
    Widget(Widget&&) = default;                  // generate move constructor
    Widget& operator=(Widget&&) = default;       // generate move assignment
    ~Widget() = default;                         // generate destructor
};

// When is this needed?
// If you declare ANY constructor, the default constructor is suppressed.
// = default re-enables it.
class Logger {
public:
    Logger(std::string name) : name_(name) {}
    Logger() = default;  // re-enable default constructor
private:
    std::string name_;
};

// = delete: explicitly forbid operations
class NonCopyable {
public:
    NonCopyable() = default;
    NonCopyable(const NonCopyable&) = delete;             // no copy
    NonCopyable& operator=(const NonCopyable&) = delete;  // no copy assign
    // Move is allowed
};

// Delete any function — not just special members
class OnlyInts {
public:
    void process(int x) {}
    void process(double) = delete;  // forbid double version
    void process(bool) = delete;    // forbid bool version (prevents implicit conv)
};

// Delete makes implicit conversions errors
OnlyInts o;
o.process(42);    // OK
o.process(3.14);  // COMPILE ERROR: deleted
o.process(true);  // COMPILE ERROR: deleted
```

---

## 17. Delegating Constructors

```cpp
class Connection {
    std::string host;
    int port;
    bool ssl;
    int timeout_ms;

public:
    // Primary constructor — does the real work
    Connection(std::string host, int port, bool ssl, int timeout_ms)
        : host(std::move(host))
        , port(port)
        , ssl(ssl)
        , timeout_ms(timeout_ms)
    {
        validate();
        connect();
    }

    // Delegates to primary — avoids code duplication
    Connection(std::string host, int port)
        : Connection(std::move(host), port, false, 5000) {}

    Connection(std::string host)
        : Connection(std::move(host), 80) {}

    Connection()
        : Connection("localhost") {}
};
```

---

## 18. Inheriting Constructors

```cpp
struct Base {
    Base(int x) {}
    Base(int x, double y) {}
    Base(std::string s) {}
};

// Without using: must re-declare all constructors in Derived
// With using: inherit all Base constructors
struct Derived : Base {
    using Base::Base;  // inherit ALL of Base's constructors

    // Now Derived(int), Derived(int, double), Derived(std::string) all work
    int extra_member = 0;  // default-initialized
};

Derived d1(42);
Derived d2(42, 3.14);
Derived d3("hello");
```

---

## 19. Raw String Literals

```cpp
// Regular strings: backslash escapes are required
std::string normal = "C:\\Users\\name\\file.txt";
std::string regex_pattern = "\\d+\\.\\d+";
std::string json = "{ \"key\": \"value\" }";

// Raw string literals: R"delimiter(content)delimiter"
// No escape sequences processed — what you type is what you get
std::string raw_path  = R"(C:\Users\name\file.txt)";
std::string raw_regex = R"(\d+\.\d+)";
std::string raw_json  = R"({ "key": "value" })";

// Multi-line raw strings
std::string html = R"(
    <html>
        <body>
            <p>Hello, World!</p>
        </body>
    </html>
)";

// Custom delimiter — if content contains )"
std::string tricky = R"special(content with )" inside)special";
//                    ^       ^                     ^       ^
//                    R       delimiter=(           content delimiter=)
```

---

## 20. User-Defined Literals

```cpp
// Create your own literal suffixes for custom types

// Literal operator: operator"" suffix_name
constexpr long long operator"" _km(long double km) {
    return static_cast<long long>(km * 1000);  // convert to meters
}
constexpr long long operator"" _m(long double m) {
    return static_cast<long long>(m);
}
constexpr long long operator"" _cm(long double cm) {
    return static_cast<long long>(cm / 100);
}

auto dist = 5.5_km;    // 5500 meters
auto height = 1.8_m;   // 1 meter
auto nail = 5.0_cm;    // 0 meters (integer truncation)

// Standard library UDLs (C++14):
using namespace std::literals;
auto str = "hello"s;          // std::string (not const char*)
auto sv  = "hello"sv;         // std::string_view
auto dur = 500ms;             // std::chrono::milliseconds
auto big = 1h + 30min + 15s;  // std::chrono::duration composition
auto c   = 1.0i;              // std::complex<double> imaginary

// Time literals (C++14)
using namespace std::chrono_literals;
std::this_thread::sleep_for(100ms);
auto timeout = 5s + 500ms;
```

---

# PART II — C++14: THE REFINEMENT

C++14 is a refinement of C++11 — fixing omissions and relaxing restrictions.

---

## 21. Return Type Deduction for Functions

```cpp
// C++11: return type deduction only in lambdas
// C++14: return type deduction for any function

auto add(int a, int b) { return a + b; }     // deduced: int
auto pi() { return 3.14159; }                // deduced: double
auto hello() { return std::string("hello"); } // deduced: std::string

// Recursive functions need the type to be deducible from a non-recursive path
auto fibonacci(int n) -> int {  // must specify or provide early non-recursive return
    if (n <= 1) return n;       // this return's type (int) defines the deduction
    return fibonacci(n-1) + fibonacci(n-2);  // subsequent returns must match
}

// decltype(auto) — preserves references and cv-qualifiers
std::map<std::string, int> global_map;

decltype(auto) get_value(const std::string& key) {
    return global_map[key];  // returns int& (map::operator[] returns reference)
    // With plain 'auto': would return int (copy)
}
```

---

## 22. Generic Lambdas (C++14)

Already covered above in lambdas section. Summary:
```cpp
auto f = [](auto x, auto y) { return x + y; };  // templated call operator
auto g = [](auto&& x) { return std::forward<decltype(x)>(x); };  // perfect forward

// Under the hood, the compiler generates:
struct lambda_type {
    template<typename T, typename U>
    auto operator()(T x, U y) const { return x + y; }
};
```

---

## 23. Extended `constexpr` (C++14)

C++11 `constexpr` functions: single return statement only.
C++14 `constexpr` functions: local variables, loops, branches, multiple returns.

```cpp
// C++14: full control flow in constexpr
constexpr int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}
constexpr int g = gcd(48, 18);  // 6, computed at compile time

constexpr int pow(int base, int exp) {
    int result = 1;
    for (int i = 0; i < exp; ++i) {
        result *= base;
    }
    return result;
}
constexpr int p = pow(2, 10);  // 1024, at compile time
```

---

## 24. Variable Templates (C++14)

```cpp
// Templates for variables, not just functions and classes

template<typename T>
constexpr T pi = T(3.14159265358979323846L);

double pd = pi<double>;  // maximum precision double
float  pf = pi<float>;   // float precision
long double pld = pi<long double>;

// More practical: type-specific constants
template<typename T>
constexpr T epsilon = std::numeric_limits<T>::epsilon();

// Template variable aliases for type traits (C++17 uses this pattern heavily)
template<typename T>
constexpr bool is_pointer_v = std::is_pointer<T>::value;

// std::is_arithmetic_v, std::is_same_v, etc. are all variable templates
```

---

## 25. Numeric Separator (C++14)

```cpp
// Apostrophe as digit separator — improves readability, ignored by compiler
auto million     = 1'000'000;
auto pi          = 3.141'592'653'589'793;
auto hex_color   = 0xFF'AA'BB'CC;
auto binary      = 0b1010'1100'1111'0000;
auto phone       = 555'867'5309LL;  // long long

// Can place separator anywhere between digits
auto x = 1'2'3;  // 123 — valid but silly
```

---

# PART III — C++17: STRUCTURED POWER

C++17 brings language-level features that eliminate entire boilerplate patterns.

---

## 26. Structured Bindings

### What They Are
Structured bindings decompose compound objects into named components.
Think of it as unpacking/destructuring.

```cpp
// Pairs
std::pair<int, std::string> employee{42, "Alice"};
auto [id, name] = employee;        // id = 42, name = "Alice"

// Tuples
auto record = std::make_tuple(1, 3.14, "hello");
auto [a, b, c] = record;           // a=1, b=3.14, c="hello"

// Arrays
int coords[3] = {10, 20, 30};
auto [x, y, z] = coords;           // x=10, y=20, z=30

// Structs — all public members
struct RGBA { uint8_t r, g, b, a; };
RGBA color{255, 128, 0, 255};
auto [red, green, blue, alpha] = color;

// With references — modify original
auto& [ref_id, ref_name] = employee;
ref_id = 99;  // modifies employee.first

// Const
const auto& [cid, cname] = employee;  // read-only refs

// Most useful: map iteration
std::map<std::string, int> scores{{"Alice", 95}, {"Bob", 87}};
for (auto& [name, score] : scores) {
    score += 5;  // boost everyone's score
    std::cout << name << ": " << score << '\n';
}

// Function return
std::pair<bool, int> divide_safe(int a, int b) {
    if (b == 0) return {false, 0};
    return {true, a / b};
}
auto [ok, result] = divide_safe(10, 2);
if (ok) std::cout << result;
```

### How to Make Your Types Work
```cpp
// Option 1: std::get specialization (tuple-like protocol)
struct Point3D { double x, y, z; };

namespace std {
    template<> struct tuple_size<Point3D> : integral_constant<size_t, 3> {};
    template<> struct tuple_element<0, Point3D> { using type = double; };
    template<> struct tuple_element<1, Point3D> { using type = double; };
    template<> struct tuple_element<2, Point3D> { using type = double; };
}

template<size_t I>
double& get(Point3D& p) {
    if constexpr (I == 0) return p.x;
    if constexpr (I == 1) return p.y;
    if constexpr (I == 2) return p.z;
}

Point3D p{1.0, 2.0, 3.0};
auto [px, py, pz] = p;  // now works
```

---

## 27. `if` and `switch` with Initializer

```cpp
// Syntax: if (init; condition)
// The init variable is scoped to the entire if/else — not beyond

// Without C++17 — variable leaks into outer scope
auto it = my_map.find("key");
if (it != my_map.end()) {
    use(it->second);
}
// it still accessible here (unnecessary pollution)

// With C++17 — perfectly scoped
if (auto it = my_map.find("key"); it != my_map.end()) {
    use(it->second);
}
// it is NOT accessible here

// Pattern: error-checking with cleanup
if (auto result = some_operation(); result.has_value()) {
    process(*result);
} else {
    log_error(result.error());
}

// Mutex lock scoping
if (std::lock_guard lock(mtx); !queue.empty()) {
    auto item = queue.front();
    queue.pop();
    process(item);
}
// lock released here (even in else branch or early return)

// switch with init
switch (auto status = get_status(); status) {
    case Status::Ok:      handle_ok(); break;
    case Status::Error:   handle_error(); break;
    case Status::Pending: handle_pending(); break;
}
// status not accessible here
```

---

## 28. `if constexpr`

### The Critical Distinction
Regular `if`: both branches MUST compile. Branch selection at runtime.
`if constexpr`: only taken branch needs to compile. Selection at compile time.

```cpp
// Without if constexpr — must be valid for ALL types T
template<typename T>
std::string stringify(T val) {
    if (std::is_same_v<T, std::string>) {
        return val;          // ERROR for non-string T: no conversion
    } else {
        return std::to_string(val);  // ERROR for string T: no overload
    }
}

// With if constexpr — only matching branch compiled
template<typename T>
std::string stringify(T val) {
    if constexpr (std::is_same_v<T, std::string>) {
        return val;               // only compiled when T = string
    } else if constexpr (std::is_arithmetic_v<T>) {
        return std::to_string(val);   // only compiled when T is numeric
    } else {
        static_assert(false, "Unsupported type");
    }
}

stringify(42);           // uses second branch
stringify("hi"s);        // uses first branch
stringify(std::string("hi")); // uses first branch

// Extremely useful for compile-time dispatch
template<typename T>
auto process(T val) {
    if constexpr (std::is_pointer_v<T>) {
        return *val;  // deref only compiled for pointer types
    } else {
        return val;   // pass-through for non-pointer
    }
}

// Check sizes, member existence, etc.
template<typename Container>
void print_info(const Container& c) {
    std::cout << "size: " << c.size() << '\n';
    if constexpr (requires { c.capacity(); }) {  // C++20 requires expression
        std::cout << "capacity: " << c.capacity() << '\n';
    }
}
```

---

## 29. `std::optional<T>`

### What It Is
`optional<T>` is a value that may or may not be present.
It replaces the pattern of using sentinel values (-1, nullptr, empty string)
or out-parameters to indicate "no value".

```cpp
#include <optional>

// OLD: return -1 to indicate "not found"
int find_index(const std::vector<int>& v, int target) {
    for (int i = 0; i < v.size(); ++i)
        if (v[i] == target) return i;
    return -1;  // -1 is a sentinel — easy to forget to check!
}

// NEW: return optional — type system enforces checking
std::optional<int> find_index(const std::vector<int>& v, int target) {
    for (int i = 0; i < v.size(); ++i)
        if (v[i] == target) return i;  // implicitly wraps i in optional
    return std::nullopt;               // explicit "no value"
}

// Usage
auto idx = find_index(v, 42);

// Check presence
if (idx) { /* has value */ }
if (idx.has_value()) { /* same */ }
if (idx != std::nullopt) { /* same */ }

// Access value
*idx;            // dereference — UB if empty!
idx.value();     // throws std::bad_optional_access if empty
idx.value_or(-1);  // returns -1 if empty — safe default

// Conditionally use
if (idx) {
    std::cout << "Found at index: " << *idx;
}

// Construction
std::optional<std::string> opt1;                    // empty
std::optional<std::string> opt2 = std::nullopt;    // empty
std::optional<std::string> opt3 = "hello";          // has "hello"
std::optional<std::string> opt4{"world"};            // has "world"
auto opt5 = std::make_optional<std::string>(5, 'x'); // "xxxxx"

// Reset
opt3.reset();   // now empty
opt3 = std::nullopt;  // also empties it
opt3 = "new value";   // re-assigns
```

### Monadic Interface (C++23)
```cpp
// Chain operations without explicit checks
auto result = parse_int("42")
    .and_then([](int x) -> std::optional<int> {
        return x > 0 ? std::optional(x) : std::nullopt;  // only positive
    })
    .transform([](int x) { return x * 2; })  // transform if present
    .or_else([]() -> std::optional<int> { return 0; }); // fallback
```

---

## 30. `std::variant<T...>`

### What It Is
A type-safe union. Holds exactly ONE value at a time, from a fixed set of types.
The type it currently holds is tracked and enforced at runtime.

```cpp
#include <variant>

// Can hold int, double, or string — but only one at a time
std::variant<int, double, std::string> v;

v = 42;             // holds int
v = 3.14;           // now holds double (int is destroyed)
v = std::string("hello");  // now holds string

// Query the active type
v.index();          // 2 (index of string in type list)
std::holds_alternative<std::string>(v);  // true

// Access — std::get
std::get<std::string>(v);    // "hello" — throws std::bad_variant_access if wrong type
std::get<2>(v);              // by index
std::get_if<std::string>(&v); // returns pointer or nullptr — safe!

// std::visit — exhaustive dispatch (like pattern matching)
std::visit([](auto&& val) {
    std::cout << val;
}, v);

// Typed visitor with overloads
std::visit([](const int& x)         { std::cout << "int: " << x; },
           [](const double& x)      { std::cout << "dbl: " << x; },
           [](const std::string& x) { std::cout << "str: " << x; }
    // But this doesn't work directly — need overloaded helper...
);

// The overloaded trick — creates one callable from multiple lambdas
template<typename... Ts>
struct overloaded : Ts... { using Ts::operator()...; };

template<typename... Ts>
overloaded(Ts...) -> overloaded<Ts...>;  // C++17 deduction guide

std::visit(overloaded{
    [](int x)         { std::cout << "int: " << x << '\n'; },
    [](double x)      { std::cout << "double: " << x << '\n'; },
    [](std::string& x){ std::cout << "string: " << x << '\n'; }
}, v);

// Practical use: AST nodes, error handling, command pattern
using JsonValue = std::variant<
    std::nullptr_t,
    bool,
    int64_t,
    double,
    std::string,
    std::vector<JsonValue>,             // recursive! use std::unique_ptr in practice
    std::map<std::string, JsonValue>
>;

// variant is never empty — always holds a value (unlike optional)
// std::monostate — empty alternative for default-constructible variant
std::variant<std::monostate, int, std::string> maybe;
// Starts as monostate — effectively "no value" within variant
```

---

## 31. `std::any`

```cpp
#include <any>

// Holds a value of ANY type — complete type erasure
// Runtime cost: dynamic allocation + type info

std::any a;               // empty
a = 42;                   // holds int
a = std::string("hi");    // now holds string
a = 3.14;                 // now holds double

// Type check
a.type() == typeid(double);  // true
a.has_value();               // true

// Access — throws std::bad_any_cast if wrong type
std::any_cast<double>(a);    // 3.14
std::any_cast<int>(a);       // throws!
std::any_cast<double>(&a);   // returns double* or nullptr — safe

// Reset
a.reset();  // empty

// Use cases: plugin systems, property bags, scripting interfaces
// Prefer variant when the set of types is known — it's much faster
```

---

## 32. `std::string_view`

### What It Is
A non-owning, read-only view into a string's character data.
Zero allocation. Just a pointer and a length.

```cpp
#include <string_view>

// Takes any string-like thing without copying
void print(std::string_view sv) {
    std::cout << sv;
    std::cout << sv.size();
    std::cout << sv.substr(0, 3);  // creates another view, no allocation
}

print("literal string");         // const char* — no allocation
print(std::string("heap str"));  // string — no copy
std::string s = "hello";
print(s);                        // also no copy
print(std::string_view(s.data(), 3));  // first 3 chars

// Operations (all non-allocating)
std::string_view sv = "hello, world";
sv.starts_with("hello");   // true
sv.ends_with("world");     // true
sv.find("world");           // 7
sv.substr(7, 5);            // "world" (another view)
sv.remove_prefix(7);        // sv now = "world"
sv.remove_suffix(1);        // sv now = "worl"
sv[0];                      // 'h' (on original before modifications)

// CRITICAL DANGER: lifetime!
std::string_view danger() {
    std::string s = "local string";
    return s;  // DANGLING! s is destroyed, view points to freed memory
}

std::string_view sv2 = "hello"s;  // DANGLING! temporary string destroyed

// Safe patterns
std::string_view sv3 = "string literal";  // OK: literal lives forever
void func(std::string_view sv);            // OK: caller owns the string
```

---

## 33. Class Template Argument Deduction (CTAD)

```cpp
// Before C++17: needed make_ helpers because constructors couldn't deduce
auto p = std::make_pair(1, 3.14);    // forced to use helper
auto t = std::make_tuple(1, 2, 3);

// C++17 CTAD: deduce template args from constructor arguments
std::pair p2(1, 3.14);              // pair<int, double>
std::tuple t2(1, 2.0, "three");     // tuple<int, double, const char*>
std::vector v{1, 2, 3};            // vector<int>
std::array arr{1, 2, 3};           // array<int, 3>
std::optional opt = 42;            // optional<int>
std::lock_guard lock(mtx);         // lock_guard<std::mutex>

// Custom deduction guides
template<typename T>
struct Container {
    Container(T val) : data(val) {}
    T data;
};

// Deduction guide: Container(T) -> Container<T>
template<typename T>
Container(T) -> Container<T>;  // explicit guide (often auto-generated)

Container c(42);     // Container<int>
Container c2(3.14);  // Container<double>

// More complex guide
template<typename Iterator>
struct Range {
    Range(Iterator begin, Iterator end);
};
// Guide: deduce value_type from iterator
template<typename Iterator>
Range(Iterator, Iterator) -> Range<typename std::iterator_traits<Iterator>::value_type>;
```

---

## 34. Fold Expressions (C++17 — revisited fully)

```cpp
// 4 forms:
// Unary right fold:  (pack op ...)     — evaluates right to left
// Unary left fold:   (... op pack)     — evaluates left to right
// Binary right fold: (pack op ... op init)
// Binary left fold:  (init op ... op pack)

template<typename... Ts>
auto sum(Ts... vals) { return (vals + ...); }       // unary right
//                              a+b+c = (a+(b+c))

template<typename... Ts>
auto product(Ts... vals) { return (... * vals); }   // unary left
//                                  a*b*c = ((a*b)*c)

// Binary fold handles empty packs (identity element as init)
template<typename... Ts>
auto safe_sum(Ts... vals) { return (0 + ... + vals); }  // 0 if empty

// Practical examples
template<typename... Ts>
void print_all(Ts&&... vals) {
    ((std::cout << std::forward<Ts>(vals) << ' '), ...);
}

template<typename T, typename... Args>
bool is_any_of(T val, Args... candidates) {
    return ((val == candidates) || ...);
}
is_any_of(3, 1, 2, 3, 4, 5);  // true

// Push multiple items
template<typename Container, typename... Items>
void push_all(Container& c, Items&&... items) {
    (c.push_back(std::forward<Items>(items)), ...);
}
std::vector<int> v;
push_all(v, 1, 2, 3, 4, 5);
```

---

## 35. Inline Variables (C++17)

```cpp
// Problem: defining static members in header files causes ODR violations
// Each translation unit gets its own copy

// Old way: declare in header, define in .cpp
// header.hpp:
struct Config { static int max_size; };  // declaration
// config.cpp:
int Config::max_size = 100;             // one definition

// C++17: inline variable — defined in header, ODR-safe
struct Config {
    inline static int max_size = 100;   // defined here, in header
    inline static const std::string name = "app";
};

// Also useful for global constants in headers
inline constexpr double PI = 3.14159265358979;
inline constexpr int MAX_BUFFER = 4096;
```

---

## 36. `[[nodiscard]]`, `[[deprecated]]`, `[[fallthrough]]`, `[[maybe_unused]]`

```cpp
// [[nodiscard]] — warn if return value is ignored
[[nodiscard]] int compute_result() { return 42; }
[[nodiscard("Please check the error code")]] bool try_operation();  // C++20 with message

compute_result();          // warning: ignoring return value
int r = compute_result();  // OK

// Common uses: error codes, resource handles, allocations
[[nodiscard]] std::unique_ptr<Widget> create_widget();
[[nodiscard]] std::expected<int, Error> parse(std::string_view);

// Apply to entire class
struct [[nodiscard]] ErrorCode {
    int code;
};
ErrorCode get_error();
get_error();  // warning

// [[deprecated]] — warn on use
[[deprecated]] void old_api() {}
[[deprecated("Use new_api() instead")]] void also_old() {}

old_api();    // warning: 'old_api' is deprecated
also_old();   // warning with message

// [[fallthrough]] — mark intentional switch fallthrough
switch (x) {
    case 1:
        step_one();
        [[fallthrough]];  // intentional — suppresses warning
    case 2:
        step_two();       // runs for case 1 AND case 2
        break;
    case 3:
        step_three();
        // missing break here — compiler warning (no [[fallthrough]])
    case 4:
        step_four();
        break;
}

// [[maybe_unused]] — suppress unused warning
void debug_function([[maybe_unused]] int debug_only_param) {}

[[maybe_unused]] static void helper() {}  // might not be called in all configs

// [[likely]] / [[unlikely]] (C++20)
if (condition) [[likely]] {
    fast_path();
} else [[unlikely]] {
    slow_path();  // optimizer treats this as rare
}
```

---

## 37. Nested Namespace Definition

```cpp
// Before C++17 — nested verbose
namespace A {
    namespace B {
        namespace C {
            void foo() {}
        }
    }
}

// C++17 — inline nested
namespace A::B::C {
    void foo() {}
}

// C++20 — inline namespaces (versioning)
namespace library::v2::detail {
    void impl() {}
}
```

---

## 38. `std::filesystem` (C++17)

```cpp
#include <filesystem>
namespace fs = std::filesystem;

// Path manipulation — works cross-platform
fs::path p = "/home/user/docs";
p / "file.txt";          // /home/user/docs/file.txt
p.filename();            // "docs"
p.parent_path();         // /home/user
p.extension();           // "" (no extension on "docs")
(p / "a.txt").stem();   // "a" (filename without extension)

// File queries
fs::exists(p);
fs::is_directory(p);
fs::is_regular_file(p / "file.txt");
fs::file_size(p / "file.txt");
fs::last_write_time(p);  // std::filesystem::file_time_type

// Directory operations
fs::create_directory("new_dir");
fs::create_directories("a/b/c/d");  // creates entire path
fs::remove("file.txt");
fs::remove_all("directory");        // recursive delete
fs::copy("src.txt", "dst.txt");
fs::rename("old.txt", "new.txt");

// Directory iteration
for (const fs::directory_entry& entry : fs::directory_iterator(".")) {
    std::cout << entry.path() << '\n';
    if (entry.is_regular_file()) {
        std::cout << "  size: " << entry.file_size() << '\n';
    }
}

// Recursive iteration
for (auto& entry : fs::recursive_directory_iterator(".")) {
    if (entry.path().extension() == ".cpp") {
        std::cout << entry.path() << '\n';
    }
}

// Error handling (non-throwing overloads)
std::error_code ec;
fs::create_directory("exists", ec);  // doesn't throw
if (ec) { /* handle error */ }
```

---

## 39. Parallel Algorithms (C++17)

```cpp
#include <execution>
#include <algorithm>

std::vector<int> v(1'000'000);
std::iota(v.begin(), v.end(), 0);

// Execution policies
std::sort(std::execution::seq,       v.begin(), v.end());  // sequential (default)
std::sort(std::execution::par,       v.begin(), v.end());  // parallel
std::sort(std::execution::par_unseq, v.begin(), v.end());  // parallel + vectorized

// Most algorithms support execution policies
std::for_each(std::execution::par, v.begin(), v.end(),
    [](int& x) { x *= 2; });

std::transform(std::execution::par, v.begin(), v.end(), v.begin(),
    [](int x) { return x * x; });

std::count_if(std::execution::par_unseq, v.begin(), v.end(),
    [](int x) { return x % 2 == 0; });

// NOTE: your lambda must be thread-safe for par/par_unseq!
// Don't capture shared mutable state without synchronization.
```

---

# PART IV — C++20: THE PARADIGM SHIFT

C++20 is the largest update since C++11. Concepts, ranges, coroutines, and modules
change how C++ is written at an architectural level.

---

## 40. Concepts — Type Constraints for Templates

### The Problem Concepts Solve
```cpp
// Without concepts — error messages are catastrophic
template<typename T>
T add(T a, T b) { return a + b; }

add("hello", "world");
// Error: /usr/include/c++/11/bits/...line 847: 'operator+' not found
// ...30 lines of template instantiation noise...
// ACTUAL error buried somewhere in the noise

// With concepts — clear, early, meaningful errors
template<typename T>
requires std::is_arithmetic_v<T>
T add(T a, T b) { return a + b; }

add("hello", "world");
// Error: no matching function for call to add(const char*, const char*)
// note: constraints not satisfied: T is not arithmetic
```

### Defining Concepts
```cpp
#include <concepts>

// Concept = named boolean constraint on template parameters
template<typename T>
concept Numeric = std::is_arithmetic_v<T>;

// Requires expression — check that operations are valid
template<typename T>
concept Printable = requires(T t) {
    std::cout << t;           // expression must be valid
};

template<typename T>
concept Sizeable = requires(T t) {
    { t.size() } -> std::convertible_to<size_t>;  // return type constrained
    { t.empty() } -> std::same_as<bool>;
};

template<typename T>
concept Hashable = requires(T t) {
    { std::hash<T>{}(t) } -> std::convertible_to<std::size_t>;
};

// Compound concepts using && and ||
template<typename T>
concept HashableAndComparable = Hashable<T> && requires(T a, T b) {
    { a == b } -> std::convertible_to<bool>;
};

// Concepts with multiple type parameters
template<typename From, typename To>
concept ConvertibleTo = std::is_convertible_v<From, To>;

template<typename Iter, typename T>
concept IteratorOf = std::input_iterator<Iter>
    && std::same_as<std::iter_value_t<Iter>, T>;
```

### Using Concepts — 4 Syntaxes

```cpp
// Syntax 1: Constrained template parameter
template<Numeric T>
T square(T x) { return x * x; }

// Syntax 2: Requires clause (after template parameter list)
template<typename T>
requires Numeric<T>
T cube(T x) { return x * x * x; }

// Syntax 3: Abbreviated function template (most concise)
auto add(Numeric auto a, Numeric auto b) { return a + b; }
// Note: a and b can be DIFFERENT Numeric types here

// Same type constraint:
template<Numeric T>
T add_same(T a, T b) { return a + b; }

// Syntax 4: Trailing requires
template<typename T>
T halve(T x) requires Numeric<T> { return x / 2; }
```

### Standard Library Concepts
```cpp
#include <concepts>

// Type categories
std::integral<T>            // int, long, char, bool, etc.
std::floating_point<T>      // float, double, long double
std::signed_integral<T>
std::unsigned_integral<T>
std::arithmetic<T>          // integral || floating_point

// Relationships
std::same_as<T, U>          // T and U are the same type
std::derived_from<T, Base>  // T is derived from Base
std::convertible_to<From, To>  // implicit conversion exists
std::common_with<T, U>      // T and U share a common type

// Callable
std::invocable<F, Args...>  // F can be called with Args
std::predicate<F, Args...>  // F returns bool-convertible

// Iterator and range
std::input_iterator<I>
std::forward_iterator<I>
std::bidirectional_iterator<I>
std::random_access_iterator<I>
std::contiguous_iterator<I>
std::range<R>
std::sized_range<R>
std::contiguous_range<R>

// Object concepts
std::copyable<T>
std::movable<T>
std::semiregular<T>   // movable + default constructible
std::regular<T>       // semiregular + equality comparable
std::equality_comparable<T>
std::totally_ordered<T>

// Usage
template<std::totally_ordered T>
T clamp(T val, T lo, T hi) {
    return val < lo ? lo : val > hi ? hi : val;
}
```

### Concept-Based Overloading
```cpp
// Compiler selects most constrained matching overload
template<typename T>
void process(T x) { std::cout << "generic\n"; }

template<std::integral T>
void process(T x) { std::cout << "integral\n"; }

template<std::floating_point T>
void process(T x) { std::cout << "floating_point\n"; }

process(42);    // "integral" — more constrained than generic
process(3.14);  // "floating_point" — more constrained than generic
process("hi");  // "generic" — only the unconstrained version matches
```

---

## 41. Ranges — A New Model for Algorithms

### The Problem with Iterators
```cpp
// Old style: must pass begin/end separately
std::sort(v.begin(), v.end());
// What if you sort the wrong range? No protection.
// What if begin/end are from different containers? UB.
// Composing algorithms requires temporary vectors.
```

### Ranges Algorithms
```cpp
#include <ranges>
#include <algorithm>

std::vector<int> v{5, 3, 1, 4, 2};

// Range algorithms: take the whole range object
std::ranges::sort(v);
std::ranges::reverse(v);
bool found = std::ranges::contains(v, 3);
auto it = std::ranges::find(v, 3);
auto [min, max] = std::ranges::minmax(v);

std::ranges::sort(v, std::greater{});  // sort descending
std::ranges::sort(v, {}, &Person::age);  // sort by member — projection!

// Projection — apply transformation before comparison
struct Person { std::string name; int age; };
std::vector<Person> people = {{"Alice", 30}, {"Bob", 25}, {"Carol", 35}};
std::ranges::sort(people, {}, &Person::age);   // sort by age
std::ranges::sort(people, {}, &Person::name);  // sort by name
std::ranges::sort(people, std::greater{}, &Person::age);  // sort by age, desc
```

### Views — Lazy Composable Transformations
```cpp
namespace rv = std::views;

std::vector<int> v{1,2,3,4,5,6,7,8,9,10};

// Views are LAZY — nothing is computed until you iterate
auto even_squares = v
    | rv::filter([](int x) { return x % 2 == 0; })  // 2,4,6,8,10
    | rv::transform([](int x) { return x * x; });    // 4,16,36,64,100

// Iterating triggers computation
for (int x : even_squares) { std::cout << x << ' '; }
// Intermediate results are NOT stored — computed on demand element by element

// This means: constant memory regardless of pipeline length!
// A 1-billion-element pipeline uses the same memory as a 10-element one.
```

### All Standard Views
```cpp
// Generation views (create sequences from nothing)
rv::iota(1, 11)           // 1,2,3,...,10
rv::iota(0)               // 0,1,2,3,... (infinite!)
rv::single(42)            // just 42
rv::empty<int>            // empty range
rv::repeat(7, 5)          // 7,7,7,7,7 (C++23)

// Transformation views
v | rv::transform(f)      // apply f to each element
v | rv::filter(pred)      // keep elements where pred is true
v | rv::reverse           // reverse order
v | rv::take(5)           // first 5 elements
v | rv::drop(5)           // skip first 5 elements
v | rv::take_while(pred)  // while pred is true
v | rv::drop_while(pred)  // drop while pred is true

// Structure manipulation
nested | rv::join          // flatten nested range
v | rv::split(',')\        // split by delimiter
rv::zip(v1, v2)            // pair up elements (C++23 stable)
rv::enumerate(v)           // (index, value) pairs (C++23)
v | rv::chunk(3)           // groups of 3 (C++23)
v | rv::slide(3)           // sliding window of size 3 (C++23)
v | rv::stride(2)          // every 2nd element (C++23)
rv::concat(v1, v2)         // concatenate ranges (C++26)

// Utility
v | rv::as_const           // treat as const range
v | rv::keys               // keys of a map-like range
v | rv::values             // values of a map-like range
v | rv::elements<0>        // get Nth element of tuple-like range

// Example: process only first 5 positive numbers from large sequence
auto result = rv::iota(1)
    | rv::filter([](int x) { return x % 3 != 0; })  // no multiples of 3
    | rv::transform([](int x) { return x * x; })      // square
    | rv::take(10);                                    // first 10
// This is LAZY — only computes as you iterate, no intermediate storage

// Collect into container (C++23)
auto vec = result | std::ranges::to<std::vector>();
auto set = result | std::ranges::to<std::set>();

// C++20 way to collect:
std::vector<int> collected;
std::ranges::copy(result, std::back_inserter(collected));
```

### Sentinel Types (Generalized End)
```cpp
// Traditional iterators: begin and end must be same type
// Ranges: end can be a sentinel — just needs != with begin

struct NullTerminatorSentinel {};

struct CStringIterator {
    const char* ptr;
    bool operator!=(NullTerminatorSentinel) const { return *ptr != '\0'; }
    CStringIterator& operator++() { ++ptr; return *this; }
    char operator*() const { return *ptr; }
};

// Range over null-terminated string without strlen
struct CStringRange {
    const char* str;
    CStringIterator begin() const { return {str}; }
    NullTerminatorSentinel end() const { return {}; }
};

for (char c : CStringRange{"hello"}) {
    std::cout << c;  // h,e,l,l,o — stops at null terminator
}
```

---

## 42. Coroutines

### What They Are
Coroutines are functions that can be **suspended** and **resumed**.
They remember their state between invocations.
C++20 provides the low-level machinery; generators and async tasks are built on top.

### Three Keywords
```cpp
co_yield value;  // produce a value and suspend
co_await expr;   // wait for an async result and suspend until ready
co_return value; // finish the coroutine
```

### Generator Coroutine (C++23 std::generator)
```cpp
#include <generator>

// A generator: produces values lazily on demand
std::generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;          // suspend here, give a to caller
        auto next = a + b;
        a = b;
        b = next;
    }  // never returns — infinite generator
}

// Consume first 10 fibonacci numbers
for (int fib : fibonacci() | std::views::take(10)) {
    std::cout << fib << ' ';
}
// 0 1 1 2 3 5 8 13 21 34

// Generator with parameter
std::generator<int> range(int start, int end, int step = 1) {
    for (int i = start; i < end; i += step) {
        co_yield i;
    }
    // co_return; — implicit at end
}

for (int x : range(0, 100, 7)) {
    std::cout << x << ' ';  // 0 7 14 21 28 35 42 49 56 63 70 77 84 91 98
}
```

### Understanding the Coroutine Mechanism
```cpp
// When you write:
std::generator<int> my_generator() {
    co_yield 1;
    co_yield 2;
    co_yield 3;
}

// The compiler transforms this into a state machine:
// - First call: runs until first co_yield, saves state, returns 1
// - Second call: resumes from saved state, runs until next co_yield, returns 2
// - Third call: returns 3
// - Fourth call: finishes (co_return or end of function)

// The coroutine frame (state) lives on the heap between suspensions
// This is why coroutines can represent infinite sequences without stack overflow
```

### Async Coroutine (Framework-Dependent)
```cpp
// C++20 provides primitives — actual async Task requires a framework
// (Asio, libunifex, cppcoro, or your own)

// Conceptually:
Task<int> fetch_data(std::string url) {
    auto response = co_await http_get(url);   // suspend until HTTP response arrives
    auto parsed   = co_await parse_json(response);  // suspend until parsing done
    co_return parsed["value"];                 // final result
}

// Key insight: co_await doesn't BLOCK a thread. It suspends the coroutine
// and returns control to the event loop. The thread is free to do other work.
// When the awaited operation completes, the coroutine is resumed.
```

---

## 43. Modules

### Why Modules — The `#include` Problem
```cpp
// The problem with #include:
// 1. Textual inclusion — copies the entire header into every TU
// 2. Order-dependent — subtle bugs from include order
// 3. Macros leak across headers — poisoning other code
// 4. Recompiled every time — slow builds
// 5. No encapsulation — all internals visible
```

### Module Syntax
```cpp
// === math.cppm (module interface unit) ===
export module math;           // declare this is module "math"

// Internal helpers — NOT exported
int internal_helper(int x) { return x * x; }

// Exported symbols — visible to importers
export int add(int a, int b) { return a + b; }
export double sqrt_approx(double x);  // declaration

// Export namespace — all members exported
export namespace geometry {
    double area(double r) { return 3.14159 * r * r; }
    double perimeter(double r) { return 2 * 3.14159 * r; }
}

// Export class
export class Vector2D {
public:
    double x, y;
    Vector2D(double x, double y) : x(x), y(y) {}
    Vector2D operator+(const Vector2D& other) const;
};

// Export multiple at once
export {
    void foo();
    void bar();
    int baz;
}
```

```cpp
// === main.cpp ===
import math;          // import module (like #include but better)
import <iostream>;    // import standard header as module

int main() {
    int sum = add(3, 4);            // from math module
    double a = geometry::area(5.0); // from math::geometry
    Vector2D v{1.0, 2.0};
    std::cout << sum << '\n';       // from imported iostream
}
```

### Module Partitions
```cpp
// Split large modules into partitions
export module math:core;      // partition "core" of module "math"
export module math:geometry;  // partition "geometry" of module "math"

export module math;           // primary module interface
export import math:core;      // re-export core partition
export import math:geometry;  // re-export geometry partition
// Importers of "math" get both partitions

// Import partition internally (not re-exported)
module math;
import math:core;             // use core internally
```

---

## 44. Three-Way Comparison (`<=>`)

### The Problem
```cpp
// Before C++20: implementing all 6 comparisons is tedious and error-prone
// For a struct with 3 fields: 6 operators × complex field-by-field logic
bool operator<(const Point& a, const Point& b) {
    if (a.x != b.x) return a.x < b.x;
    if (a.y != b.y) return a.y < b.y;
    return a.z < b.z;
}
// ...times 6...
```

### `<=>` — The Spaceship Operator
```cpp
#include <compare>

struct Point {
    int x, y, z;

    // This single line generates ALL 6 comparison operators:
    // <, <=, >, >=, ==, !=
    auto operator<=>(const Point&) const = default;
    // Note: =default uses memberwise comparison in declaration order
};

Point p1{1, 2, 3}, p2{1, 3, 0};
bool lt = p1 < p2;   // true  (y: 2 < 3)
bool gt = p1 > p2;   // false
bool eq = p1 == p2;  // false
bool le = p1 <= p2;  // true
// All work without writing them!

// Custom implementation
struct Version {
    int major, minor, patch;

    std::strong_ordering operator<=>(const Version& other) const {
        if (auto cmp = major <=> other.major; cmp != 0) return cmp;
        if (auto cmp = minor <=> other.minor; cmp != 0) return cmp;
        return patch <=> other.patch;
    }
    bool operator==(const Version&) const = default;
};
```

### Ordering Types
```cpp
// std::strong_ordering — equality means identical (int, most types)
// Values: less, equal, greater, equivalent
1 <=> 2;   // strong_ordering::less
2 <=> 2;   // strong_ordering::equal
3 <=> 2;   // strong_ordering::greater

// std::weak_ordering — equal means equivalent, not identical
// (e.g., case-insensitive string: "abc" == "ABC" but they're different objects)
// Values: less, equivalent, greater

// std::partial_ordering — some values are incomparable
// (e.g., floating point: NaN is not less, equal, or greater than anything)
// Values: less, equivalent, greater, unordered
1.0 <=> std::numeric_limits<double>::quiet_NaN();  // partial_ordering::unordered
```

---

## 45. Designated Initializers (C++20)

```cpp
struct Window {
    int x = 0, y = 0;
    int width = 800, height = 600;
    bool fullscreen = false;
    std::string title = "Untitled";
    int refresh_rate = 60;
};

// Specify only the fields you care about — rest get defaults
// Fields must be in order (but can skip)
Window w1{.width = 1920, .height = 1080, .fullscreen = true};
Window w2{.title = "My App", .refresh_rate = 144};
Window w3{.x = 100, .y = 100, .width = 640, .height = 480};

// Why this is better than positional init:
// Window bad{100, 100, 640, 480, false, "Title", 60};
// Hard to read: what does the 4th argument mean?

// Works with union too
union Data {
    int i;
    double d;
    char c;
};
Data dat{.d = 3.14};  // active member is d
```

---

## 46. `std::span<T>` — Non-Owning Contiguous View

```cpp
#include <span>

// Problem: functions that take arrays need size parameter separately,
// or must accept specific container types

// Old way — multiple overloads or templates
void process(int* data, size_t size) {}
void process(std::vector<int>& v) {}

// span: one function works for all contiguous data
void process(std::span<int> data) {
    for (int& x : data) x *= 2;
    data.size();
    data.data();     // underlying pointer
    data[0];
    data.front();
    data.back();
    data.subspan(2, 3);  // span of 3 elements starting at index 2
    data.first(5);       // first 5 elements
    data.last(5);        // last 5 elements
}

int arr[10] = {};
std::vector<int> v(10);
std::array<int, 10> a{};

process(arr);  // works
process(v);    // works
process(a);    // works
process(std::span<int>(arr, 5));  // first 5 elements of arr

// Read-only span
void read(std::span<const int> data) { /* data[0] is const int */ }

// Static extent — size known at compile time
std::span<int, 10> fixed(arr);  // must be exactly 10 elements
```

---

## 47. `std::format` (C++20) — Type-Safe Formatting

```cpp
#include <format>

// Python-style format strings, but type-safe at compile time
std::string s = std::format("Hello, {}!", "world");
std::string n = std::format("The answer is {}", 42);
std::string f = std::format("Pi is {:.4f}", 3.14159265);  // "Pi is 3.1416"

// Positional arguments
std::string pos = std::format("{0} + {1} = {2}", 3, 4, 7);  // "3 + 4 = 7"
std::string rev = std::format("{1} and {0}", "B", "A");     // "A and B"

// Format specifiers
std::format("{:d}",    42);      // decimal: "42"
std::format("{:b}",    42);      // binary:  "101010"
std::format("{:o}",    42);      // octal:   "52"
std::format("{:x}",    42);      // hex:     "2a"
std::format("{:X}",    42);      // HEX:     "2A"
std::format("{:#x}",   42);      // "0x2a"
std::format("{:010x}", 42);      // "0x0000002a" (width 10, zero-padded)
std::format("{:+d}",   42);      // "+42"
std::format("{:>10}",  "hi");    // "        hi" (right-align width 10)
std::format("{:<10}",  "hi");    // "hi        " (left-align)
std::format("{:^10}",  "hi");    // "    hi    " (center)
std::format("{:*>10}", "hi");    // "********hi" (fill with *)
std::format("{:.3f}",  3.14159); // "3.142"
std::format("{:e}",    12345.0); // "1.234500e+04"

// Output directly (C++23 std::print)
std::print("Hello, {}!\n", "world");
std::println("The answer is {}", 42);  // adds newline

// Formatting ranges (C++23)
std::vector<int> v{1,2,3};
std::format("{}", v);            // "[1, 2, 3]"
```

---

## 48. `consteval` (C++20)

Already covered. Summary:
```cpp
consteval int square(int x) { return x * x; }

// Recursive lambdas with deducing this (C++23):
auto factorial = [](this auto self, int n) -> int {
    return n <= 1 ? 1 : n * self(n - 1);
};
```

---

## 49. Template Lambda (C++20)

```cpp
// C++14 generic lambda: auto parameters — different types allowed
auto f = [](auto a, auto b) { return a + b; };  // a and b can differ

// C++20 template lambda: explicit template syntax
auto g = []<typename T>(T a, T b) { return a + b; };  // a and b same type T

// Why? To constrain, to use T explicitly, to handle type relationships
auto sum_vec = []<typename T>(std::vector<T>& v) {
    T sum{};
    for (auto& x : v) sum += x;
    return sum;
};

// With concepts
auto numeric_op = []<std::integral T>(T a, T b) {
    return a % b;  // only valid for integrals
};

// Variadic template lambda
auto print_all = []<typename... Ts>(Ts&&... args) {
    ((std::cout << std::forward<Ts>(args) << ' '), ...);
};
```

---

## 50. Abbreviated Function Templates (C++20)

```cpp
// C++20: 'auto' parameters in regular functions = function template
// Same as writing template<typename T, typename U> void f(T a, U b)

void print(auto x) { std::cout << x; }
// Equivalent to:
template<typename T>
void print(T x) { std::cout << x; }

// Multiple auto — each is a separate type parameter
void add(auto a, auto b) { return a + b; }  // a and b can differ

// With concepts
void process(std::integral auto x) { /* x is integral */ }
void transform(std::ranges::range auto& container, auto func) {
    for (auto& elem : container) elem = func(elem);
}
```

---

## 51. Aggregate Initialization with Base Classes (C++20)

```cpp
// C++17: aggregates cannot have user-declared constructors, virtual functions
// C++20: relaxed — aggregates can have BASE classes

struct Base {
    int x;
    double y;
};

struct Derived : Base {
    std::string name;
    // No user-declared constructors
};

// Initialize base then derived members
Derived d{{10, 3.14}, "hello"};  // {{base members}, derived members}
Derived d2{10, 3.14, "world"};   // also valid — flat brace elision
```

---

## 52. `[[likely]]` and `[[unlikely]]` (C++20)

```cpp
// Branch prediction hints — let optimizer know which branch is hot

void process(int x) {
    if (x > 0) [[likely]] {
        // This branch taken most of the time
        normal_processing(x);
    } else [[unlikely]] {
        // Rare error case
        handle_error();
    }
}

// Typical use: error checking
bool try_operation() {
    if (!init()) [[unlikely]] return false;  // rarely fails
    if (!process()) [[unlikely]] return false;
    return true;  // this is the [[likely]] path (implicitly)
}
```

---

## 53. `std::jthread` (C++20)

```cpp
#include <thread>

// Problem with std::thread:
// 1. Must manually call join() or detach() — easy to forget
// 2. No built-in cancellation mechanism

// std::jthread fixes both:
// 1. Automatically joins in destructor (RAII)
// 2. Provides cooperative cancellation via stop_token

std::jthread t1([]() {
    do_work();
});  // automatically joins when t1 goes out of scope

// With stop_token — cooperative cancellation
std::jthread t2([](std::stop_token st) {
    while (!st.stop_requested()) {
        do_incremental_work();
    }
    cleanup();
});

// Request the thread to stop
t2.request_stop();  // sets stop_requested()
// t2 will join when it checks and exits the loop

// stop_source / stop_token — can share cancellation across multiple threads
std::stop_source ss;
auto t3 = std::jthread(worker, ss.get_token());
auto t4 = std::jthread(worker, ss.get_token());
ss.request_stop();  // cancels both t3 and t4

// stop_callback — register callbacks to run on stop
std::stop_callback cb(ss.get_token(), []() {
    std::cout << "stop was requested\n";
});
```

---

# PART V — C++23: THE POLISH

---

## 54. `std::expected<T, E>` — Result Type

### What It Is
`expected<T, E>` holds either a value of type T (success) or an error of type E.
It is C++'s `Result<T, E>` (Rust) / `Either<E, T>` (Haskell).
Preferred over exceptions for expected failure modes.

```cpp
#include <expected>

// Return either a value or an error
std::expected<int, std::string> parse_int(std::string_view str) {
    try {
        return std::stoi(std::string(str));  // success: wraps value
    } catch (...) {
        return std::unexpected("not a valid integer: " + std::string(str));
    }
}

auto result = parse_int("42");
auto error  = parse_int("abc");

// Check
if (result) { /* has value */ }
result.has_value();  // true

// Access
*result;             // 42 — UB if no value!
result.value();      // 42 — throws std::bad_expected_access if no value
result.error();      // UB if has value — only call when !result

// Safe access
result.value_or(0);  // 0 if error, value if success

// Error case
if (!error) {
    std::cerr << error.error();  // "not a valid integer: abc"
}

// Monadic interface — chain operations
auto doubled = parse_int("21")
    .and_then([](int x) -> std::expected<int, std::string> {
        if (x < 0) return std::unexpected("must be positive");
        return x * 2;
    })
    .transform([](int x) { return x + 1; })  // map on success
    .transform_error([](std::string e) { return "Error: " + e; })  // map on error
    .or_else([](std::string e) -> std::expected<int, std::string> {
        return 0;  // fallback value
    });
```

---

## 55. Deducing `this` — Explicit Self Parameter

### What It Is
C++23 allows writing the implicit `this` parameter explicitly in member functions.
This enables: recursive lambdas, CRTP simplification, perfect-forwarding member functions.

```cpp
struct Widget {
    int value = 10;

    // Traditional: two overloads for const and non-const
    int& get_value() & { return value; }
    const int& get_value() const& { return value; }

    // C++23: single template handles all ref-qualifiers
    template<typename Self>
    auto& get_value(this Self&& self) {
        return std::forward<Self>(self).value;
        // If called on lvalue: returns int&
        // If called on const lvalue: returns const int&
        // If called on rvalue: returns int&&
    }
};

// Recursive lambda — IMPOSSIBLE before C++23 without external variable
auto factorial = [](this auto self, int n) -> int {
    return n <= 1 ? 1 : n * self(n - 1);
};
factorial(5);  // 120

// Fibonacci
auto fib = [](this auto self, int n) -> int {
    if (n <= 1) return n;
    return self(n-1) + self(n-2);
};

// CRTP without templates — method chaining
struct Builder {
    template<typename Self>
    Self& set_name(this Self& self, std::string name) {
        self.name_ = std::move(name);
        return self;  // returns the derived type, not Builder
    }
    std::string name_;
};

struct SpecialBuilder : Builder {
    SpecialBuilder& set_value(int v) { value_ = v; return *this; }
    int value_;
};

SpecialBuilder b;
b.set_name("hello")  // returns SpecialBuilder& (not Builder&)
 .set_value(42);     // works! method chaining across inheritance
```

---

## 56. `std::generator<T>` (C++23)

```cpp
#include <generator>

// Standard library generator — replaces hand-rolled coroutine machinery
std::generator<int> iota(int start = 0) {
    for (;;) co_yield start++;
}

std::generator<double> linspace(double start, double end, int n) {
    double step = (end - start) / (n - 1);
    for (int i = 0; i < n; ++i) {
        co_yield start + i * step;
    }
}

// Tree traversal as generator
struct TreeNode {
    int val;
    std::unique_ptr<TreeNode> left, right;
};

std::generator<int> inorder(const TreeNode* node) {
    if (!node) co_return;
    co_yield std::ranges::elements_of(inorder(node->left.get()));   // recursive!
    co_yield node->val;
    co_yield std::ranges::elements_of(inorder(node->right.get()));
}

for (int val : inorder(root)) {
    std::cout << val << ' ';  // in-order traversal without explicit stack
}
```

---

## 57. New Range Views (C++23)

```cpp
namespace rv = std::views;

std::vector<int> v{1,2,3,4,5,6,7,8,9,10};

// stride — every Nth element
for (int x : v | rv::stride(3)) {}  // 1, 4, 7, 10

// chunk — groups of N
for (auto chunk : v | rv::chunk(3)) {
    // chunk 1: {1,2,3}, chunk 2: {4,5,6}, chunk 3: {7,8,9}, chunk 4: {10}
}

// slide — sliding window of size N
for (auto window : v | rv::slide(3)) {
    // {1,2,3}, {2,3,4}, {3,4,5}, ...
}

// chunk_by — group by predicate
for (auto group : v | rv::chunk_by([](int a, int b) { return (a%2) == (b%2); })) {
    // Groups by same parity: {1}, {2}, {3}, {4}, ...
}

// pairwise — adjacent pairs (slide(2) but as pair)
// zip_transform — zip + transform in one

// repeat (N times or infinite)
for (int x : rv::repeat(42, 5)) {}  // 42, 42, 42, 42, 42
for (int x : rv::repeat(0) | rv::take(3)) {}  // infinite 0s, take 3

// enumerate — (index, value) pairs
for (auto [i, x] : rv::enumerate(v)) {
    std::cout << i << ": " << x << '\n';
}

// cartesian_product — all combinations
std::vector<int> a{1,2}, b{10,20};
for (auto [x, y] : rv::cartesian_product(a, b)) {
    std::cout << x << ',' << y << '\n';  // (1,10),(1,20),(2,10),(2,20)
}
```

---

## 58. Monadic `std::optional` (C++23)

```cpp
// Before: explicit null checks everywhere
std::optional<int> parse_int(std::string_view s);
std::optional<double> to_double(int x);
std::optional<std::string> format(double x);

auto result_old = parse_int(input);
std::optional<std::string> final;
if (result_old) {
    auto step2 = to_double(*result_old);
    if (step2) {
        final = format(*step2);
    }
}

// C++23: monadic chaining — no explicit checks
auto final_new = parse_int(input)
    .and_then(to_double)      // if present, apply; if empty/null result, propagate empty
    .transform(format_fn)     // if present, map; preserve empty otherwise
    .or_else([]() -> std::optional<std::string> { return "0.0"; });
```

---

## 59. `std::print` / `std::println` (C++23)

```cpp
#include <print>

// std::print — like printf but type-safe, uses std::format syntax
std::print("Hello, {}!\n", "world");
std::print(stderr, "Error: {}\n", error_message);  // to stderr

// std::println — adds newline automatically
std::println("The answer is {}", 42);
std::println(stderr, "Fatal: {}", msg);
```

---

## 60. `[[assume]]` Attribute (C++23)

```cpp
// Tell the optimizer something is always true — without a check at runtime
// If assumption is violated: undefined behavior

void process(int* ptr, int n) {
    [[assume(ptr != nullptr)]];  // optimizer: no null check needed
    [[assume(n > 0 && n < 1000)]];  // optimizer: n is in this range

    for (int i = 0; i < n; ++i) {
        ptr[i] *= 2;  // optimizer can generate better code with these assumptions
    }
}

// Useful for: hot loops, SIMD optimizations, alignment guarantees
void simd_process(float* data, int n) {
    [[assume(n % 8 == 0)]];   // n is multiple of 8 — enable full vectorization
    [[assume(reinterpret_cast<uintptr_t>(data) % 32 == 0)]];  // aligned to 32 bytes
}
```

---

## 61. `std::mdspan` — Multidimensional Array View (C++23)

```cpp
#include <mdspan>

// Non-owning view over contiguous data as N-dimensional array
std::vector<double> data(12);

// 3×4 matrix view
std::mdspan<double, std::extents<int, 3, 4>> matrix(data.data());

matrix[1, 2] = 3.14;  // C++23 multidimensional subscript
matrix[0, 0] = 1.0;
// Note: C++23 removed the deprecated use of comma in subscripts
// [1, 2] is now a multi-argument subscript, not the comma operator

// Dynamic extents
std::mdspan<double, std::dextents<int, 2>> dynamic_matrix(
    data.data(),
    3, 4  // extents specified at runtime
);

// 3D tensor
std::vector<float> tensor_data(2 * 3 * 4);
std::mdspan<float, std::extents<int, 2, 3, 4>> tensor(tensor_data.data());
tensor[0, 1, 2] = 3.14f;

// Layout policies
// layout_right (row-major, default, C-style)
// layout_left (column-major, Fortran-style)
// layout_stride (custom strides)
std::mdspan<double, std::extents<int,3,4>, std::layout_left> col_major(data.data());
```

---

## 62. `std::flat_map` / `std::flat_set` (C++23)

```cpp
#include <flat_map>
#include <flat_set>

// Sorted containers backed by contiguous storage (vector by default)
// Better cache performance than std::map (no pointer chasing)
// Trade-off: slower insertion (maintains sorted order), faster iteration/lookup

std::flat_map<std::string, int> fm;
fm["hello"] = 1;
fm["world"] = 2;
// Keys stored in sorted vector: fast binary search, cache-friendly

std::flat_set<int> fs{3, 1, 4, 1, 5, 9, 2, 6};
// Stores: 1, 2, 3, 4, 5, 6, 9 (sorted, unique, contiguous)

// API identical to std::map/std::set
fm.find("hello");
fm.lower_bound("m");
for (auto& [k, v] : fm) {}

// Use when: small to medium datasets, lots of reads, few inserts after build
// Prefer over map for: read-heavy, cache-sensitive, serialization, flat data
```

---

# PART VI — ADVANCED FEATURES & PATTERNS

---

## 63. Template Metaprogramming

### Type Traits
```cpp
#include <type_traits>

// Query types at compile time
std::is_integral_v<int>               // true
std::is_floating_point_v<double>      // true
std::is_pointer_v<int*>               // true
std::is_reference_v<int&>             // true
std::is_const_v<const int>            // true
std::is_same_v<int, int>              // true
std::is_same_v<int, long>             // false
std::is_base_of_v<Base, Derived>      // true
std::is_trivially_copyable_v<int>     // true
std::is_trivially_destructible_v<int> // true
std::is_default_constructible_v<T>    // is T{} valid?
std::is_copy_constructible_v<T>
std::is_move_constructible_v<T>
std::is_nothrow_move_constructible_v<T>

// Transform types
using T1 = std::remove_const_t<const int>;      // int
using T2 = std::remove_reference_t<int&>;       // int
using T3 = std::remove_pointer_t<int*>;         // int
using T4 = std::add_const_t<int>;               // const int
using T5 = std::add_lvalue_reference_t<int>;    // int&
using T6 = std::add_pointer_t<int>;             // int*
using T7 = std::decay_t<const int&>;            // int (remove ref + cv)
using T8 = std::conditional_t<true, int, double>; // int
using T9 = std::common_type_t<int, double>;     // double
using T10 = std::underlying_type_t<MyEnum>;     // underlying int type

// std::enable_if (pre-C++20 — use concepts instead)
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
safe_divide(T a, T b) { return b != 0 ? a/b : 0; }
```

### SFINAE — Substitution Failure Is Not An Error
```cpp
// When template substitution fails, that overload is silently removed
// instead of causing a compile error — enables template overloading

// Detection idiom — check if type has a method
template<typename T, typename = void>
struct has_size : std::false_type {};

template<typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>>
    : std::true_type {};

// std::void_t<expr>: if expr is valid, substitutes void; otherwise substitution fails
// std::declval<T>(): gives an rvalue of T without constructing it (for use in unevaluated contexts)

static_assert(has_size<std::vector<int>>::value);
static_assert(!has_size<int>::value);

// C++20: much cleaner with requires expressions
template<typename T>
constexpr bool has_size_v = requires(T t) { t.size(); };
```

### `if constexpr` with Type Traits
```cpp
// Powerful combination: compile-time dispatch based on type properties
template<typename T>
void serialize(const T& value, std::ostream& out) {
    if constexpr (std::is_arithmetic_v<T>) {
        out.write(reinterpret_cast<const char*>(&value), sizeof(T));
    } else if constexpr (std::is_same_v<T, std::string>) {
        uint32_t size = value.size();
        out.write(reinterpret_cast<const char*>(&size), 4);
        out.write(value.data(), size);
    } else if constexpr (std::is_container_v<T>) {  // custom concept
        // serialize each element
        for (const auto& elem : value) serialize(elem, out);
    } else {
        static_assert(std::is_trivially_copyable_v<T>,
            "Cannot serialize non-trivially-copyable type");
        out.write(reinterpret_cast<const char*>(&value), sizeof(T));
    }
}
```

---

## 64. `requires` Expressions (C++20)

### Four Kinds of Requirements
```cpp
template<typename T>
concept MyConstraint = requires(T t, T u) {
    // 1. Simple requirement — expression must be valid
    t + u;
    t.size();

    // 2. Type requirement — associated type must exist
    typename T::value_type;
    typename T::iterator;

    // 3. Compound requirement — check expression AND its type
    { t.size() } -> std::convertible_to<std::size_t>;
    { t + u } -> std::same_as<T>;
    { t.begin() } noexcept;  // must also be noexcept

    // 4. Nested requirement — embedded constraint
    requires std::copy_constructible<T>;
    requires (sizeof(T) <= 64);  // T must be small
};

// Requires in function body (ad-hoc constraint checking)
template<typename T>
void process(T val) {
    static_assert(requires { val.size(); }, "T must have size()");
}

// Requires in if constexpr
template<typename T>
void print_size(const T& x) {
    if constexpr (requires { x.size(); }) {
        std::cout << "size: " << x.size() << '\n';
    }
}
```

---

## 65. Policy-Based Design with Concepts

```cpp
// Encode design contracts in the type system

template<typename Allocator>
concept AllocatorConcept = requires(Allocator a, size_t n) {
    { a.allocate(n) } -> std::same_as<void*>;
    { a.deallocate(nullptr, n) };
};

template<typename Logger>
concept LoggerConcept = requires(Logger l, std::string_view msg) {
    { l.log(msg) };
    { l.log_error(msg) };
};

template<AllocatorConcept Alloc, LoggerConcept Log>
class MyContainer {
    Alloc allocator_;
    Log logger_;
public:
    void push(int val) {
        logger_.log("pushing value");
        // ...
    }
};
```

---

## 66. CRTP — Curiously Recurring Template Pattern

```cpp
// Enable static polymorphism (no vtable overhead)

template<typename Derived>
class Printable {
public:
    void print() const {
        static_cast<const Derived*>(this)->print_impl();
    }

    void print_twice() const {
        print();
        print();
    }
};

class MyClass : public Printable<MyClass> {
public:
    void print_impl() const {
        std::cout << "MyClass\n";
    }
};

MyClass obj;
obj.print();       // calls print_impl via CRTP — no virtual dispatch
obj.print_twice(); // also static dispatch — zero overhead

// C++23: deducing this is often preferred over CRTP
// But CRTP still useful for static interface enforcement
```

---

## 67. Explicit Object Parameters — Complete Guide (C++23)

```cpp
// The 'this' parameter is explicit in the function signature
// Allows perfect-forwarding of *this

struct Container {
    std::vector<int> data;

    // C++23: single function replaces 4 overloads (& const& && const&&)
    template<typename Self>
    auto&& get(this Self&& self, size_t i) {
        return std::forward<Self>(self).data[i];
    }

    // Builder pattern — returns correct derived type without CRTP
    template<typename Self>
    Self&& add(this Self&& self, int val) {
        self.data.push_back(val);
        return std::forward<Self>(self);
    }
};
```

---

## 68. Memory Model & Atomics — Deep Dive

```cpp
#include <atomic>

// Memory orderings — control visibility and ordering guarantees
// From weakest (fastest) to strongest (slowest):
// relaxed < consume < acquire < release < acq_rel < seq_cst

std::atomic<int> x{0}, y{0};

// seq_cst (default): total sequential consistency — safest, most expensive
x.store(1, std::memory_order_seq_cst);
y.load(std::memory_order_seq_cst);

// acquire-release: synchronize between producer and consumer
// Producer:
std::atomic<bool> ready{false};
int data = 0;

void producer() {
    data = 42;                                    // write data
    ready.store(true, std::memory_order_release); // release: all writes above are visible
}

void consumer() {
    while (!ready.load(std::memory_order_acquire)) {} // acquire: sees all writes before release
    assert(data == 42);  // guaranteed
}

// relaxed: no ordering guarantee — only atomicity
// Use for: counters, statistics, cases where order doesn't matter
std::atomic<int> counter{0};
void increment() {
    counter.fetch_add(1, std::memory_order_relaxed);
}

// Compare-Exchange — foundation of lock-free algorithms
std::atomic<int> val{0};

// CAS loop — atomic "if val == expected, set val = desired"
int expected = 0;
int desired = 42;
bool success = val.compare_exchange_strong(expected, desired);
// If val was 0: val is now 42, success = true
// If val was not 0: expected is updated to actual value, success = false

// Lock-free stack using CAS
struct Node { int data; Node* next; };
std::atomic<Node*> head{nullptr};

void push(int val) {
    Node* new_node = new Node{val, nullptr};
    Node* current_head;
    do {
        current_head = head.load(std::memory_order_relaxed);
        new_node->next = current_head;
    } while (!head.compare_exchange_weak(
        current_head, new_node,
        std::memory_order_release,
        std::memory_order_relaxed
    ));
}
// compare_exchange_weak: may spuriously fail (ok in loop)
// compare_exchange_strong: never spuriously fails (better outside loop)
```

---

## 69. RAII Patterns

```cpp
// Every resource = RAII wrapper

// 1. scope_exit — run code on scope exit (not in std yet, but widely used)
template<typename F>
struct scope_exit {
    F f;
    bool active;
    explicit scope_exit(F f) : f(std::move(f)), active(true) {}
    ~scope_exit() { if (active) f(); }
    void release() { active = false; }
    scope_exit(scope_exit&&) = default;
    scope_exit(const scope_exit&) = delete;
};
template<typename F> scope_exit(F) -> scope_exit<F>;

{
    auto guard = scope_exit([&]{ db.rollback(); });
    // ... operations that might throw ...
    db.commit();
    guard.release();  // success — don't rollback
}

// 2. Unique handle — for non-memory resources
template<typename T, auto Deleter>
struct UniqueHandle {
    T handle;
    explicit UniqueHandle(T h) : handle(h) {}
    ~UniqueHandle() { if (handle) Deleter(handle); }
    UniqueHandle(const UniqueHandle&) = delete;
    UniqueHandle(UniqueHandle&& other) noexcept
        : handle(std::exchange(other.handle, T{})) {}
    T get() const { return handle; }
    T release() { return std::exchange(handle, T{}); }
};

using FileHandle = UniqueHandle<FILE*, &fclose>;
FileHandle f(fopen("data.txt", "r"));
// auto-closed when f goes out of scope
```

---

## 70. `std::chrono` — Modern Time (C++20 Extended)

```cpp
#include <chrono>
using namespace std::chrono;

// Duration arithmetic
auto d1 = 5s;                  // 5 seconds
auto d2 = 500ms;               // 500 milliseconds
auto d3 = d1 + d2;             // 5500ms
auto hours = duration_cast<hours>(d3);

// Time points
auto now = system_clock::now();
auto future = now + 24h;
auto elapsed = steady_clock::now() - start;

// C++20: Calendar types
year_month_day today{floor<days>(system_clock::now())};
year y = today.year();    // 2024
month m = today.month();  // June
day d = today.day();      // 15

auto specific = 2024y / June / 15;     // year_month_day
auto last_day = 2024y / February / last;  // last day of February

// Convert to time_point
auto tp = sys_days{specific};

// C++20: Time zones
auto utc = system_clock::now();
auto local_zone = current_zone();  // system local time zone
auto local_time = zoned_time{local_zone, utc};

// Custom time zone
auto nyc = zoned_time{"America/New_York", utc};
std::cout << std::format("{}", nyc);

// Benchmark helper
auto measure = [](auto&& func) {
    auto start = steady_clock::now();
    std::forward<decltype(func)>(func)();
    auto end = steady_clock::now();
    return duration_cast<microseconds>(end - start);
};

auto time = measure([&]{ sort_data(); });
std::println("Sorted in {}μs", time.count());
```

---

## Summary Reference Table

| Feature | Standard | Category |
|---|---|---|
| `auto`, `decltype`, rvalue refs, move semantics | C++11 | Type system |
| Lambdas, variadic templates, `constexpr`, `nullptr` | C++11 | Language |
| `enum class`, uniform init, range-for, smart ptrs | C++11 | Ergonomics |
| `override`, `final`, `= default/delete`, delegating ctors | C++11 | OOP |
| Generic lambdas, `decltype(auto)`, `make_unique` | C++14 | Refinement |
| Variable templates, extended `constexpr`, digit separators | C++14 | Refinement |
| Structured bindings, `if` initializer, `if constexpr` | C++17 | Language |
| `optional`, `variant`, `any`, `string_view`, CTAD | C++17 | Library |
| Fold expressions, `[[nodiscard]]`, inline variables, nested ns | C++17 | Language |
| `filesystem`, parallel algorithms, `std::byte` | C++17 | Library |
| Concepts, Ranges, Coroutines, Modules | C++20 | Architecture |
| `<=>`, designated init, `consteval`, `constinit`, `jthread` | C++20 | Language |
| `span`, `format`, template lambdas, abbreviated templates | C++20 | Ergonomics |
| `[[likely]]`, `[[unlikely]]`, `[[nodiscard]]` message | C++20 | Attributes |
| `std::expected`, deducing `this`, `std::generator` | C++23 | Language |
| `std::print/println`, mdspan, flat_map/set | C++23 | Library |
| Monadic optional, new range views, `[[assume]]` | C++23 | Refinement |

---

*Keep this document as a living reference. Read a section, implement it, revisit it.*
*Mastery comes from usage, not memorization.*

Here is your complete Modern C++ syntax reference — **70 features across C++11→C++23**, organized from fundamental to advanced, with deep explanations for every single one.

**What's inside:**

- **C++11 (features 1–20):** `auto`/`decltype`, the full move semantics picture (`std::move`, `std::forward`, Rule of Five), lambdas with all capture modes, uniform initialization, range-for, all three smart pointer types, `nullptr`, `enum class`, `constexpr`, `static_assert`, variadic templates, type aliases, `override`/`final`, `= default`/`= delete`, delegating constructors, raw string literals, user-defined literals
- **C++14 (21–25):** Deduced returns, `decltype(auto)`, generic lambdas, extended `constexpr`, variable templates, digit separators
- **C++17 (26–39):** Structured bindings with custom type support, `if`/`switch` initializers, `if constexpr`, `optional`, `variant` (with the `overloaded` trick), `any`, `string_view` lifetime dangers, CTAD, fold expressions, inline variables, all four standard attributes, `filesystem`, parallel algorithms
- **C++20 (40–53):** Full concepts system (4 syntaxes, all std concepts), ranges with every view, coroutine mechanics + `co_yield`/`co_await`/`co_return`, modules with partitions, spaceship operator with all ordering types, designated initializers, `span`, `format` with all specifiers, `consteval`, `jthread`/`stop_token`
- **C++23 (54–62):** `std::expected` with monadic chain, deducing `this` for recursive lambdas and CRTP replacement, `std::generator`, all new range views, monadic optional, `std::print`, `mdspan`, `flat_map/set`, `[[assume]]`
- **Advanced patterns (63–70):** Full TMP/type traits, SFINAE vs concepts, `requires` expressions (all 4 kinds), policy-based design, CRTP, atomics with memory orderings and lock-free CAS loops, RAII patterns, `std::chrono` calendar/timezone

