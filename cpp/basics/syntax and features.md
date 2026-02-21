# Modern C++ — Comprehensive Syntax & Features Guide
*C++11 → C++23: Everything You Need to Master*

---

## Foundation Mental Model

Think of modern C++ evolution in layers:
- **C++11/14** → The revolution (move semantics, lambdas, type inference)
- **C++17** → The refinement (structured bindings, if-constexpr, std::optional)
- **C++20** → The paradigm shift (concepts, ranges, coroutines, modules)
- **C++23** → The polish (std::expected, deducing this, stackful coroutines)

---

## C++11 — The Revolution

### Auto & Type Deduction
```cpp
auto x = 42;           // int
auto y = 3.14;         // double
auto z = "hello";      // const char*
auto w = std::string{"hello"};  // std::string

// decltype — deduce type of expression without evaluating
int a = 5;
decltype(a) b = 10;    // int
decltype(a + 3.0) c;   // double

// trailing return type
auto add(int x, int y) -> int { return x + y; }
```

**Rust parallel:** `let x = 42;` — same concept, same benefit.

---

### Move Semantics & Rvalue References
The single most important C++11 feature. Eliminates unnecessary copies.

```cpp
// lvalue = has a name/address. rvalue = temporary, no persistent address
int x = 5;          // x is lvalue, 5 is rvalue
std::string s = std::string("hello");  // std::string("hello") is rvalue

// Rvalue reference — binds to temporaries
void process(std::string&& s) {
    // s is now "moved into" this function
    std::string local = std::move(s);  // transfer ownership
    // s is now in valid-but-unspecified state
}

// Move constructor
class Buffer {
    int* data;
    size_t size;
public:
    // Copy constructor — expensive O(n)
    Buffer(const Buffer& other) : size(other.size) {
        data = new int[size];
        std::copy(other.data, other.data + size, data);
    }
    
    // Move constructor — O(1), just pointer steal
    Buffer(Buffer&& other) noexcept 
        : data(other.data), size(other.size) {
        other.data = nullptr;
        other.size = 0;
    }
    
    // Move assignment
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data;
            data = other.data;
            size = other.size;
            other.data = nullptr;
            other.size = 0;
        }
        return *this;
    }
    
    ~Buffer() { delete[] data; }
};
```

**Rule of Five:** If you define any of destructor, copy ctor, copy assign, move ctor, move assign — define all five.

**Perfect Forwarding:**
```cpp
// std::forward preserves value category
template<typename T>
void wrapper(T&& arg) {
    // Without forward: always lvalue inside function
    // With forward: preserves original lvalue/rvalue nature
    actual_function(std::forward<T>(arg));
}
```

---

### Lambda Expressions
```cpp
// Basic syntax: [capture](params) -> return_type { body }
auto add = [](int a, int b) -> int { return a + b; };
auto add2 = [](int a, int b) { return a + b; };  // return deduced

// Capture modes
int x = 10, y = 20;
auto by_value  = [x, y]() { return x + y; };     // copy
auto by_ref    = [&x, &y]() { x++; return x+y; }; // reference
auto all_val   = [=]() { return x + y; };          // capture all by copy
auto all_ref   = [&]() { x++; y++; };              // capture all by ref
auto mixed     = [=, &x]() { x++; return x+y; };  // x by ref, rest by copy

// Mutable lambda — modify captured copies
auto counter = [count = 0]() mutable { return ++count; };
counter(); // 1
counter(); // 2

// Generic lambda (C++14)
auto generic = [](auto a, auto b) { return a + b; };
generic(1, 2);       // int
generic(1.0, 2.0);   // double
generic(std::string{"a"}, std::string{"b"});  // string

// Immediately invoked
int result = [](int x) { return x * x; }(5);  // 25
```

---

### Uniform Initialization & Initializer Lists
```cpp
// Brace initialization — works everywhere, prevents narrowing
int a{5};
double b{3.14};
std::vector<int> v{1, 2, 3, 4, 5};
std::map<std::string, int> m{{"one", 1}, {"two", 2}};

struct Point { int x, y; };
Point p{10, 20};  // aggregate init

// Narrowing conversion — compile error with braces
int x = 3.14;   // OK (implicit truncation, bad)
int y{3.14};    // ERROR: narrowing conversion

// std::initializer_list
class MyVec {
public:
    MyVec(std::initializer_list<int> list) {
        for (int val : list) data.push_back(val);
    }
private:
    std::vector<int> data;
};
MyVec mv{1, 2, 3, 4};
```

---

### Range-Based For Loop
```cpp
std::vector<int> v{1, 2, 3, 4, 5};

for (int x : v) { }           // copy
for (const int& x : v) { }   // read-only reference (preferred)
for (int& x : v) { x *= 2; } // modify in place
for (auto& x : v) { }        // auto reference (most idiomatic)
for (auto&& x : v) { }       // universal reference (works for proxy iterators)

// Works on arrays too
int arr[] = {1, 2, 3};
for (auto x : arr) { }
```

---

### Smart Pointers
```cpp
#include <memory>

// unique_ptr — sole ownership, zero overhead
auto up = std::make_unique<int>(42);
auto up2 = std::make_unique<std::vector<int>>(10, 0);

// Move ownership (cannot copy)
auto up3 = std::move(up);  // up is now null
// Pass to function
void take(std::unique_ptr<int> p) { }
take(std::move(up3));

// Custom deleter
auto file_ptr = std::unique_ptr<FILE, decltype(&fclose)>(
    fopen("test.txt", "r"), &fclose
);

// shared_ptr — shared ownership, reference counted
auto sp1 = std::make_shared<int>(42);
auto sp2 = sp1;  // ref count = 2
sp1.reset();     // ref count = 1
// sp2 goes out of scope → ref count 0 → deleted

// weak_ptr — non-owning observer, breaks cycles
std::weak_ptr<int> wp = sp2;
if (auto locked = wp.lock()) {  // temporarily own
    std::cout << *locked;
}

// NEVER use raw new/delete in modern C++
// Prefer make_unique / make_shared (single allocation for shared_ptr)
```

**Rust parallel:** `Box<T>` ≈ `unique_ptr`, `Rc<T>` ≈ `shared_ptr`, `Weak<T>` ≈ `weak_ptr`.

---

### nullptr
```cpp
// Before C++11: NULL was 0 (int), causing ambiguity
void f(int);
void f(int*);
f(NULL);    // calls f(int)! — bug
f(nullptr); // calls f(int*) — correct

// nullptr has type nullptr_t
nullptr_t p = nullptr;
```

---

### Strongly Typed Enums
```cpp
// Old enum — pollutes namespace, implicit int conversion
enum Color { Red, Green, Blue };  // Red, Green, Blue in global scope
int x = Red;  // implicit conversion

// enum class — scoped, no implicit conversion
enum class Direction { North, South, East, West };
Direction d = Direction::North;
// int x = d;  // ERROR
int x = static_cast<int>(d);  // explicit only

// Specify underlying type
enum class Flags : uint8_t { None = 0, Read = 1, Write = 2, Exec = 4 };
```

---

### constexpr
```cpp
// Evaluated at compile time
constexpr int square(int x) { return x * x; }
constexpr int val = square(10);  // computed at compile time, not runtime

// constexpr if literal types
constexpr double pi = 3.14159265358979;

// C++14 relaxed constexpr — loops, local vars allowed
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) result *= i;
    return result;
}
constexpr int f5 = factorial(5);  // 120, computed at compile time
```

---

### Variadic Templates
```cpp
// Template that accepts any number of type parameters
template<typename... Args>
void print(Args... args) {
    (std::cout << ... << args);  // fold expression (C++17)
}
print(1, " hello ", 3.14, '\n');

// Recursive variadic (pre-C++17 style)
void print_all() {}  // base case

template<typename T, typename... Rest>
void print_all(T first, Rest... rest) {
    std::cout << first << '\n';
    print_all(rest...);  // recurse with remaining
}

// Perfect forwarding variadic — the make_unique pattern
template<typename T, typename... Args>
std::unique_ptr<T> my_make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}
```

---

### Type Aliases
```cpp
// using — cleaner than typedef, works with templates
using Integer = int;
using StringVec = std::vector<std::string>;
using Callback = std::function<void(int, double)>;

// Template alias — typedef cannot do this
template<typename T>
using Vec = std::vector<T>;
Vec<int> v;  // std::vector<int>

template<typename K, typename V>
using HashMap = std::unordered_map<K, V>;
```

---

### std::thread & Concurrency
```cpp
#include <thread>
#include <mutex>
#include <atomic>
#include <future>

// Basic thread
std::thread t([]() { std::cout << "thread\n"; });
t.join();  // wait for completion (or t.detach())

// Mutex
std::mutex mtx;
int counter = 0;
auto increment = [&]() {
    std::lock_guard<std::mutex> lock(mtx);  // RAII lock
    ++counter;
};

// Atomic — lock-free for simple types
std::atomic<int> atomic_counter{0};
atomic_counter.fetch_add(1, std::memory_order_relaxed);

// async / future — high level
auto future = std::async(std::launch::async, []() {
    return expensive_computation();
});
// ... do other work ...
auto result = future.get();  // block until ready
```

---

### static_assert
```cpp
static_assert(sizeof(int) == 4, "Requires 32-bit int");
static_assert(std::is_trivially_copyable_v<int>, "Must be trivially copyable");

template<typename T>
void process(T val) {
    static_assert(std::is_integral_v<T>, "T must be integral type");
}
```

---

### Other C++11 Features
```cpp
// override / final
struct Base { virtual void foo() {} };
struct Derived : Base {
    void foo() override {}   // compiler error if Base::foo doesn't exist
};
struct Leaf final : Derived {}; // cannot be further derived

// delete / default
struct NonCopyable {
    NonCopyable() = default;
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable& operator=(const NonCopyable&) = delete;
};

// delegating constructors
class Widget {
    int x, y, z;
public:
    Widget(int x, int y, int z) : x(x), y(y), z(z) {}
    Widget(int x, int y) : Widget(x, y, 0) {}  // delegate
    Widget() : Widget(0, 0) {}                  // chain delegate
};

// Explicit conversion operators
struct MyBool {
    explicit operator bool() const { return value; }
    bool value;
};

// Raw string literals
auto path = R"(C:\Users\name\file.txt)";   // no escaping needed
auto regex = R"(\d+\.\d+)";
auto multiline = R"(
    line 1
    line 2
)";
```

---

## C++14 — The Refinement

```cpp
// Generic lambdas (already shown above)
auto add = [](auto a, auto b) { return a + b; };

// Lambda capture with initializer
int x = 10;
auto f = [y = x * 2]() { return y; };   // y = 20, captured by value
auto g = [&r = x]() { r++; };           // r is reference to x

// Return type deduction for functions
auto make_pair_custom(auto a, auto b) {  // deduced
    return std::make_pair(a, b);
}

// decltype(auto) — preserves reference-ness
decltype(auto) get_ref(std::vector<int>& v) {
    return v[0];  // returns int& (not int)
}

// std::make_unique (was missing from C++11!)
auto p = std::make_unique<int>(42);

// Integer literals with separators
auto million = 1'000'000;
auto pi_bits = 0b1100'1010'1111'0000;
auto hex     = 0xFF'AA'BB;

// [[deprecated]] attribute
[[deprecated("Use new_function instead")]]
void old_function() {}

// Variable templates
template<typename T>
constexpr T pi = T(3.14159265358979);
double pd = pi<double>;
float  pf = pi<float>;

// std::exchange
int old_val = std::exchange(x, 42);  // sets x=42, returns old x
// Pattern: useful in move constructors
Buffer(Buffer&& other) noexcept
    : data(std::exchange(other.data, nullptr))
    , size(std::exchange(other.size, 0)) {}
```

---

## C++17 — Structured Power

### Structured Bindings
```cpp
// Decompose aggregates, pairs, tuples, arrays
std::pair<int, std::string> p{42, "hello"};
auto [num, str] = p;

std::tuple<int, double, std::string> t{1, 3.14, "world"};
auto [a, b, c] = t;

// With maps — extremely useful
std::map<std::string, int> scores{{"Alice", 95}, {"Bob", 87}};
for (auto& [name, score] : scores) {
    std::cout << name << ": " << score << '\n';
}

// Arrays
int arr[3] = {1, 2, 3};
auto [x, y, z] = arr;

// Structs (if all members public)
struct Point { int x, y, z; };
Point pt{1, 2, 3};
auto [px, py, pz] = pt;
```

**Rust parallel:** `let (a, b) = tuple;` — same concept.

---

### If / Switch with Initializer
```cpp
// Init statement in if — scopes variable to if block
if (auto it = m.find("key"); it != m.end()) {
    use(it->second);
}
// it is not accessible here

// Before C++17 (leaks it into outer scope):
auto it = m.find("key");
if (it != m.end()) { use(it->second); }

// Switch with init
switch (auto val = compute(); val) {
    case 0: break;
    case 1: break;
    default: break;
}
```

---

### if constexpr
```cpp
// Compile-time branch selection — dead branch not compiled
template<typename T>
void print_type(T val) {
    if constexpr (std::is_integral_v<T>) {
        std::cout << "Integer: " << val;
    } else if constexpr (std::is_floating_point_v<T>) {
        std::cout << "Float: " << val;
    } else {
        std::cout << "Other: " << val;
    }
}

// Critical difference from regular if:
// Regular if — both branches must compile
// if constexpr — only taken branch needs to compile
template<typename T>
auto process(T val) {
    if constexpr (std::is_same_v<T, std::string>) {
        return val.length();   // .length() only valid for string
    } else {
        return val * 2;        // * only valid for numeric
    }
}
```

---

### std::optional
```cpp
#include <optional>

std::optional<int> find_value(bool condition) {
    if (condition) return 42;
    return std::nullopt;  // empty
}

auto result = find_value(true);
if (result) {
    std::cout << *result;  // dereference
    std::cout << result.value();
}

// value_or — default if empty
int val = result.value_or(0);

// Chaining with and_then (C++23) or manual
std::optional<std::string> to_string(std::optional<int> opt) {
    if (!opt) return std::nullopt;
    return std::to_string(*opt);
}
```

**Rust parallel:** `Option<T>` — exact equivalent.

---

### std::variant
```cpp
#include <variant>

// Type-safe union
std::variant<int, double, std::string> v;
v = 42;
v = 3.14;
v = std::string("hello");

// Access
std::get<std::string>(v);           // throws if wrong type
std::get_if<std::string>(&v);       // returns pointer or nullptr

// std::visit — exhaustive pattern matching
std::visit([](auto&& val) {
    using T = std::decay_t<decltype(val)>;
    if constexpr (std::is_same_v<T, int>)
        std::cout << "int: " << val;
    else if constexpr (std::is_same_v<T, double>)
        std::cout << "double: " << val;
    else
        std::cout << "string: " << val;
}, v);

// Visitor with overload set (elegant pattern)
template<typename... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template<typename... Ts> overloaded(Ts...) -> overloaded<Ts...>;  // deduction guide

std::visit(overloaded{
    [](int x)         { std::cout << "int: " << x; },
    [](double x)      { std::cout << "double: " << x; },
    [](std::string& x){ std::cout << "string: " << x; }
}, v);
```

**Rust parallel:** `enum` with data — `variant` is C++'s `enum MyEnum { Int(i32), Float(f64), Str(String) }`.

---

### std::any
```cpp
#include <any>

std::any a = 42;
a = std::string("hello");
a = 3.14;

if (a.type() == typeid(double)) {
    std::cout << std::any_cast<double>(a);
}
// Use sparingly — sacrifices type safety
```

---

### Fold Expressions
```cpp
// Unary right fold: (args op ...)
template<typename... Args>
auto sum(Args... args) { return (args + ...); }       // ((a+b)+c)...

// Unary left fold: (... op args)  
template<typename... Args>
auto sum_left(Args... args) { return (... + args); }  // ...(a+(b+c))

// Binary fold with init value
template<typename... Args>
auto sum_with_init(Args... args) { return (0 + ... + args); }

// Print all with comma separator
template<typename... Args>
void print_all(Args&&... args) {
    ((std::cout << args << ' '), ...);
}

// Logical folds
template<typename... Args>
bool all_positive(Args... args) { return ((args > 0) && ...); }
```

---

### Class Template Argument Deduction (CTAD)
```cpp
// Before C++17 — needed make_ functions
auto p = std::make_pair(1, 3.14);     // explicit

// C++17 — deduced from constructor args
std::pair p2(1, 3.14);               // pair<int, double>
std::vector v{1, 2, 3};             // vector<int>
std::tuple t(1, 3.14, "hello");     // tuple<int, double, const char*>

// Deduction guides for custom types
template<typename T>
struct MyWrapper {
    T value;
    MyWrapper(T v) : value(v) {}
};
// Deduction guide
template<typename T> MyWrapper(T) -> MyWrapper<T>;
MyWrapper w(42);  // MyWrapper<int>
```

---

### Other C++17 Features
```cpp
// [[nodiscard]] — warn if return value ignored
[[nodiscard]] int compute() { return 42; }
compute();  // warning: ignoring return value

// [[maybe_unused]] — suppress unused warnings
[[maybe_unused]] int debug_only = 0;

// [[fallthrough]] — intentional switch fallthrough
switch (x) {
    case 1:
        do_something();
        [[fallthrough]];
    case 2:
        do_other();
        break;
}

// Inline variables
struct Config {
    inline static int max_size = 100;  // defined in header, no ODR violation
};

// constexpr lambdas
constexpr auto square = [](int x) constexpr { return x * x; };
constexpr int val = square(5);  // compile time

// std::string_view — non-owning string reference
void process(std::string_view sv) {
    // No allocation, just a pointer + length
    sv.substr(0, 3);  // still no allocation
}
process("literal");          // no conversion cost
process(std::string("heap")); // no copy

// Parallel algorithms (execution policy)
#include <execution>
std::sort(std::execution::par_unseq, v.begin(), v.end());

// std::filesystem
#include <filesystem>
namespace fs = std::filesystem;
fs::path p = "/home/user/file.txt";
fs::create_directories(p.parent_path());
for (auto& entry : fs::directory_iterator(".")) {
    std::cout << entry.path() << '\n';
}

// Nested namespaces
namespace A::B::C {  // C++17, was A { namespace B { namespace C {
    void foo() {}
}
```

---

## C++20 — The Paradigm Shift

### Concepts
The most transformative C++20 feature — type constraints for templates.

```cpp
#include <concepts>

// Define a concept
template<typename T>
concept Numeric = std::is_arithmetic_v<T>;

template<typename T>
concept Printable = requires(T t) {
    { std::cout << t };  // must be valid expression
};

template<typename T>
concept Container = requires(T c) {
    c.begin();
    c.end();
    c.size();
    typename T::value_type;
};

// Sortable with comparison
template<typename T>
concept Comparable = requires(T a, T b) {
    { a < b } -> std::convertible_to<bool>;
    { a == b } -> std::convertible_to<bool>;
};

// Use concepts — 4 equivalent syntaxes
template<Numeric T>                         // 1. Constrained template param
T add(T a, T b) { return a + b; }

template<typename T> requires Numeric<T>    // 2. Requires clause
T multiply(T a, T b) { return a * b; }

auto square(Numeric auto x) { return x*x; } // 3. Abbreviated template

template<typename T>
T cube(T x) requires Numeric<T> { return x*x*x; } // 4. Trailing requires

// Compound concepts
template<typename T>
concept StringLike = std::convertible_to<T, std::string_view>;

template<typename T>
concept HashableComparable = requires(T a, T b) {
    { std::hash<T>{}(a) } -> std::convertible_to<size_t>;
    { a == b } -> std::convertible_to<bool>;
};

// Standard library concepts
// <concepts>: same_as, derived_from, convertible_to, integral, floating_point,
//             signed_integral, unsigned_integral, invocable, predicate...
// <ranges>:   range, sized_range, input_range, forward_range...

template<std::integral T>
T gcd(T a, T b) { return b == 0 ? a : gcd(b, a % b); }

// Concept-based overloading
template<std::integral T>
void process(T x) { std::cout << "integral\n"; }

template<std::floating_point T>
void process(T x) { std::cout << "float\n"; }
```

**Mental Model:** Concepts = Rust traits for template constraints. But more expressive — can constrain on expressions, not just methods.

---

### Ranges
A complete rethinking of iterators and algorithms.

```cpp
#include <ranges>
#include <algorithm>

std::vector<int> v{5, 3, 1, 4, 2, 6, 8, 7};

// Ranges algorithms — no begin/end needed
std::ranges::sort(v);
auto it = std::ranges::find(v, 4);
bool found = std::ranges::contains(v, 4);  // C++23

// Views — lazy, composable, zero-copy transformations
namespace rv = std::views;

// Pipeline syntax with |
auto result = v 
    | rv::filter([](int x) { return x % 2 == 0; })  // keep evens
    | rv::transform([](int x) { return x * x; })     // square
    | rv::take(3);                                    // first 3

for (int x : result) std::cout << x << ' ';
// Lazily computed — no intermediate containers!

// Common views
auto evens   = v | rv::filter([](int x){ return x%2==0; });
auto squared = v | rv::transform([](int x){ return x*x; });
auto first5  = v | rv::take(5);
auto last5   = v | rv::drop(v.size()-5);
auto rev     = v | rv::reverse;
auto indices = rv::iota(0, 10);                    // 0,1,2,...,9
auto pairs   = rv::zip(v1, v2);                    // C++23

// Collect into container
auto vec = result | std::ranges::to<std::vector>();  // C++23

// iota view
for (int i : rv::iota(1, 11)) std::cout << i << ' '; // 1..10

// generate_n equivalent
auto countdown = rv::iota(0) | rv::transform([](int x){ return 10-x; }) | rv::take(10);
```

---

### Coroutines
C++20 introduces coroutine machinery (low-level — generators and async built on top).

```cpp
#include <coroutine>
#include <generator>  // C++23 std::generator, or implement yourself

// Generator coroutine (using C++23 std::generator)
#include <generator>

std::generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;           // suspend and yield value
        auto next = a + b;
        a = b;
        b = next;
    }
}

for (int fib : fibonacci() | std::views::take(10)) {
    std::cout << fib << ' ';
}

// co_yield — yield a value and suspend
// co_await — wait for an async operation
// co_return — return from coroutine

// Async coroutine (framework-dependent, e.g., Asio or custom)
Task<int> async_compute() {
    auto result = co_await some_async_operation();
    co_return result * 2;
}
```

---

### Modules
Replaces `#include` — faster compilation, no macro leakage.

```cpp
// math.cpp — module implementation
export module math;           // declare module

export int add(int a, int b) { return a + b; }     // exported
int internal_helper() { return 0; }                 // not exported

export namespace geometry {
    double area(double r) { return 3.14 * r * r; }
}

// main.cpp — module consumer  
import math;                  // import module (not file)
import <iostream>;            // import standard headers

int main() {
    auto result = add(1, 2);
    auto a = geometry::area(5.0);
}

// Module partitions
export module math:core;
export module math:geometry;
import math:core;
```

---

### Three-Way Comparison (Spaceship Operator)
```cpp
#include <compare>

struct Point {
    int x, y;
    
    // Generates all 6 comparison operators automatically
    auto operator<=>(const Point&) const = default;
    
    // Or custom implementation
    std::strong_ordering operator<=>(const Point& other) const {
        if (auto cmp = x <=> other.x; cmp != 0) return cmp;
        return y <=> other.y;
    }
    bool operator==(const Point&) const = default;
};

Point p1{1, 2}, p2{1, 3};
bool lt = p1 < p2;   // all work now
bool gt = p1 > p2;
bool eq = p1 == p2;

// Ordering types
// strong_ordering:  == means substitutable (int)
// weak_ordering:    == means equivalent but not substitutable (case-insensitive string)
// partial_ordering: incomparable values allowed (float: NaN)

auto result = 1.0 <=> 2.0;  // std::partial_ordering
auto result2 = 1 <=> 2;     // std::strong_ordering::less
```

---

### Other C++20 Features
```cpp
// Designated initializers
struct Config {
    int width = 800;
    int height = 600;
    bool fullscreen = false;
    std::string title = "App";
};
Config c{.width = 1920, .height = 1080, .title = "Game"};
// Fields in order, unspecified use default

// consteval — MUST be evaluated at compile time (not just CAN)
consteval int square(int x) { return x * x; }
constexpr int a = square(5);  // OK — compile time
// int x = 5; square(x);      // ERROR — x not constexpr

// constinit — guaranteed static initialization (no static init order fiasco)
constinit int global = 42;  // init at compile time, but mutable

// std::span — non-owning view over contiguous data
#include <span>
void process(std::span<int> data) {
    for (int& x : data) x *= 2;
}
std::vector<int> v{1,2,3};
int arr[3] = {1,2,3};
process(v);    // works
process(arr);  // works — no copy

// Template lambda
auto f = []<typename T>(T x) { return x * 2; };
auto g = []<typename T>(std::vector<T>& v) { return v.size(); };

// Aggregate initialization with base classes
struct Base { int x; };
struct Derived : Base { int y; };
Derived d{{1}, 2};  // C++20: can aggregate-init with base class

// std::format (Python f-strings for C++)
#include <format>
std::string s = std::format("Hello, {}! You are {} years old.", "Alice", 30);
std::string hex = std::format("{:#010x}", 255);  // "0x000000ff"
std::cout << std::format("{:>10.2f}\n", 3.14159);  // right-align, 2 decimal

// Likely/unlikely hints
if (condition) [[likely]] {
    fast_path();
} else [[unlikely]] {
    slow_path();
}

// Calendar and time zones in <chrono>
using namespace std::chrono;
auto today = year_month_day{floor<days>(system_clock::now())};
auto tp = sys_days{2024y/January/15};

// std::jthread — automatically joins + stoppable
std::jthread t([](std::stop_token st) {
    while (!st.stop_requested()) {
        do_work();
    }
});
t.request_stop();  // signal stop
// t automatically joins at end of scope

// Abbreviated function templates
void print(auto x) { std::cout << x; }  // any type
void process(Numeric auto x) { }         // constrained
```

---

## C++23 — The Polish

```cpp
// std::expected — error handling without exceptions
#include <expected>

std::expected<int, std::string> divide(int a, int b) {
    if (b == 0) return std::unexpected("division by zero");
    return a / b;
}

auto result = divide(10, 2);
if (result) {
    std::cout << *result;         // 5
} else {
    std::cout << result.error();  // error string
}
// Monadic operations
auto doubled = divide(10, 2)
    .and_then([](int x) -> std::expected<int, std::string> { return x * 2; })
    .or_else([](auto& e) -> std::expected<int, std::string> { return 0; });
```

**Rust parallel:** `Result<T, E>` — this IS `Result<T, E>` for C++.

```cpp
// Deducing this — explicit self parameter
struct Widget {
    // Before: needed const/non-const overloads
    // After: single template handles both
    template<typename Self>
    auto& value(this Self&& self) {
        return std::forward<Self>(self).m_value;
    }
    
    // CRTP without virtual — recursive lambdas!
    int m_value;
};

// Recursive lambda with deducing this
auto fib = [](this auto self, int n) -> int {
    if (n <= 1) return n;
    return self(n-1) + self(n-2);  // call self recursively
};

// std::generator (coroutine generator)
std::generator<int> range(int start, int end) {
    for (int i = start; i < end; ++i)
        co_yield i;
}

// std::mdspan — multidimensional span
#include <mdspan>
int data[12];
std::mdspan<int, std::extents<int, 3, 4>> matrix(data);
matrix[1, 2] = 42;  // multidimensional subscript operator

// std::flat_map / std::flat_set — sorted contiguous containers
#include <flat_map>
std::flat_map<std::string, int> m;  // better cache performance than map

// Monadic operations on std::optional
std::optional<int> opt = 42;
auto result = opt
    .and_then([](int x) -> std::optional<int> { return x > 0 ? std::optional(x*2) : std::nullopt; })
    .transform([](int x) { return x + 1; })
    .or_else([]() -> std::optional<int> { return 0; });

// Multidimensional subscript operator
struct Matrix {
    double data[4][4];
    double& operator[](size_t i, size_t j) { return data[i][j]; }
};
Matrix m;
m[1, 2] = 3.14;

// if consteval — inside constexpr, check if we're in consteval context
constexpr int f(int x) {
    if consteval {
        // compile-time path
        return x * 2;
    } else {
        // runtime path (can use non-constexpr functions)
        return runtime_compute(x);
    }
}

// std::print / std::println
#include <print>
std::print("Hello, {}!\n", "world");
std::println("The answer is {}", 42);

// std::ranges::zip, stride, chunk, slide views
auto zipped  = std::views::zip(v1, v2);
auto strided = v | std::views::stride(2);       // every 2nd element
auto chunks  = v | std::views::chunk(3);        // groups of 3
auto windows = v | std::views::slide(3);        // sliding window of 3
auto joined  = nested | std::views::join;       // flatten
auto concat  = std::views::concat(v1, v2);      // C++26 (note: not yet stable)

// [[assume]] attribute — undefined behavior if false (optimizer hint)
void f(int x) {
    [[assume(x > 0)]];  // tell optimizer x is always positive
    return std::log(x); // can skip x <= 0 check
}
```

---

## Type Traits & Metaprogramming

```cpp
#include <type_traits>

// Query types at compile time
static_assert(std::is_integral_v<int>);
static_assert(std::is_same_v<int, int>);
static_assert(std::is_base_of_v<Base, Derived>);
static_assert(std::is_trivially_copyable_v<int>);

// Transform types
using T = std::remove_const_t<const int>;         // int
using U = std::remove_reference_t<int&>;          // int  
using V = std::add_pointer_t<int>;                // int*
using W = std::decay_t<const int&>;               // int (remove cv + ref)
using X = std::conditional_t<true, int, double>;  // int

// Enable/disable overloads
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
safe_divide(T a, T b) { return b != 0 ? a/b : 0; }

// C++20: use concepts instead of enable_if
template<std::integral T>
T safe_divide(T a, T b) { return b != 0 ? a/b : 0; }

// std::void_t — detection idiom
template<typename T, typename = void>
struct has_size : std::false_type {};

template<typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};

static_assert(has_size<std::vector<int>>::value);
static_assert(!has_size<int>::value);
```

---

## RAII Patterns & Modern Resource Management

```cpp
// Every resource should be owned by an RAII object
// This is C++'s answer to Rust's ownership system (but manual)

// scope_guard pattern (not in std, but widely used)
template<typename F>
struct scope_guard {
    F f;
    bool active = true;
    scope_guard(F f) : f(std::move(f)) {}
    ~scope_guard() { if (active) f(); }
    void dismiss() { active = false; }
    scope_guard(scope_guard&&) = default;
    scope_guard(const scope_guard&) = delete;
};
template<typename F> scope_guard(F) -> scope_guard<F>;

// Usage
{
    auto guard = scope_guard([&](){ cleanup(); });
    if (error) return;  // cleanup() still called
    guard.dismiss();    // only if success
}
```

---

## Summary: C++ Version Feature Map

| Feature | Version |
|---|---|
| Move semantics, lambdas, `auto`, smart ptrs, `nullptr`, variadic templates | C++11 |
| Generic lambdas, `make_unique`, relaxed `constexpr`, `decltype(auto)` | C++14 |
| Structured bindings, `if constexpr`, `optional/variant/any`, CTAD, `string_view`, `<filesystem>` | C++17 |
| Concepts, Ranges, Coroutines, Modules, `<=>`, `std::format`, `std::span`, `consteval` | C++20 |
| `std::expected`, deducing `this`, `std::generator`, `std::print`, mdspan, monadic optional | C++23 |

---

## The Expert Mental Model

When writing modern C++, reason in this priority order:

1. **Zero-cost abstractions** — if it can be done at compile time, do it (`constexpr`, `consteval`, concepts, templates)
2. **Ownership clarity** — who owns this? `unique_ptr`, `shared_ptr`, or stack. Never raw `new`
3. **Value semantics by default** — move when transferring, copy only when needed
4. **Algorithm over loop** — ranges pipeline > raw for loop for clarity and optimization
5. **Type system as documentation** — `std::expected`, `std::optional`, `enum class` — make illegal states unrepresentable

The deepest insight: **Modern C++ is converging toward Rust's ownership model, but through convention rather than enforcement.** Understanding Rust's borrow checker gives you a mental model for *why* these C++ patterns exist — they're solving the exact same problems.