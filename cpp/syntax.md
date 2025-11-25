# Comprehensive C++ Syntax Guide

## 1. Basic Program Structure

```cpp
#include <iostream>  // Preprocessor directive

int main() {         // Main function - program entry point
    std::cout << "Hello, World!" << std::endl;
    return 0;        // Return status code
}
```

## 2. Variables and Data Types

### Primitive Data Types

```cpp
// Integer types
int number = 42;              // Standard integer
short smallNum = 100;         // Short integer
long longNum = 1000000L;      // Long integer
long long veryLong = 1000000000LL;

// Floating point
float decimal = 3.14f;        // Single precision
double precise = 3.14159265;  // Double precision
long double morePrecise = 3.14159265358979L;

// Character and boolean
char letter = 'A';            // Single character
bool flag = true;             // Boolean (true/false)

// Unsigned variants
unsigned int positive = 42;
unsigned char byte = 255;
```

### Type Modifiers

```cpp
const int CONSTANT = 100;     // Cannot be modified
static int counter = 0;       // Retains value between calls
extern int globalVar;         // Declared elsewhere
```

### Auto Keyword (C++11)

```cpp
auto x = 42;          // int
auto y = 3.14;        // double
auto z = "text";      // const char*
```

## 3. Operators

### Arithmetic Operators

```cpp
int a = 10, b = 3;
int sum = a + b;      // Addition: 13
int diff = a - b;     // Subtraction: 7
int prod = a * b;     // Multiplication: 30
int quot = a / b;     // Division: 3
int rem = a % b;      // Modulus: 1

a++;  // Increment
b--;  // Decrement
```

### Comparison Operators

```cpp
a == b   // Equal to
a != b   // Not equal to
a > b    // Greater than
a < b    // Less than
a >= b   // Greater than or equal to
a <= b   // Less than or equal to
```

### Logical Operators

```cpp
bool x = true, y = false;
x && y   // AND
x || y   // OR
!x       // NOT
```

### Bitwise Operators

```cpp
int a = 5, b = 3;
a & b    // AND
a | b    // OR
a ^ b    // XOR
~a       // NOT
a << 1   // Left shift
a >> 1   // Right shift
```

### Assignment Operators

```cpp
a = 5;
a += 3;   // a = a + 3
a -= 2;   // a = a - 2
a *= 4;   // a = a * 4
a /= 2;   // a = a / 2
a %= 3;   // a = a % 3
```

## 4. Control Structures

### If-Else Statements

```cpp
int x = 10;

if (x > 0) {
    std::cout << "Positive";
} else if (x < 0) {
    std::cout << "Negative";
} else {
    std::cout << "Zero";
}

// Ternary operator
int result = (x > 0) ? 1 : -1;
```

### Switch Statement

```cpp
int day = 3;

switch (day) {
    case 1:
        std::cout << "Monday";
        break;
    case 2:
        std::cout << "Tuesday";
        break;
    case 3:
        std::cout << "Wednesday";
        break;
    default:
        std::cout << "Other day";
        break;
}
```

## 5. Loops

### For Loop

```cpp
// Traditional for loop
for (int i = 0; i < 10; i++) {
    std::cout << i << " ";
}

// Range-based for loop (C++11)
int arr[] = {1, 2, 3, 4, 5};
for (int num : arr) {
    std::cout << num << " ";
}
```

### While Loop

```cpp
int i = 0;
while (i < 10) {
    std::cout << i << " ";
    i++;
}
```

### Do-While Loop

```cpp
int i = 0;
do {
    std::cout << i << " ";
    i++;
} while (i < 10);
```

### Loop Control

```cpp
for (int i = 0; i < 10; i++) {
    if (i == 5) break;      // Exit loop
    if (i % 2 == 0) continue; // Skip iteration
}
```

## 6. Functions

### Basic Function

```cpp
// Function declaration
int add(int a, int b);

// Function definition
int add(int a, int b) {
    return a + b;
}

// Void function (no return)
void printMessage() {
    std::cout << "Hello!" << std::endl;
}
```

### Function Overloading

```cpp
int add(int a, int b) {
    return a + b;
}

double add(double a, double b) {
    return a + b;
}

int add(int a, int b, int c) {
    return a + b + c;
}
```

### Default Parameters

```cpp
void greet(std::string name = "World") {
    std::cout << "Hello, " << name << "!" << std::endl;
}

greet();          // "Hello, World!"
greet("Alice");   // "Hello, Alice!"
```

### Inline Functions

```cpp
inline int square(int x) {
    return x * x;
}
```

### Lambda Functions (C++11)

```cpp
auto add = [](int a, int b) { return a + b; };
int result = add(3, 4);  // 7

// With capture
int multiplier = 3;
auto multiply = [multiplier](int x) { return x * multiplier; };
```

## 7. Arrays and Strings

### Arrays

```cpp
// Declaration and initialization
int arr1[5];                           // Uninitialized
int arr2[5] = {1, 2, 3, 4, 5};        // Initialized
int arr3[] = {1, 2, 3};               // Size inferred

// Multidimensional arrays
int matrix[3][3] = {
    {1, 2, 3},
    {4, 5, 6},
    {7, 8, 9}
};

// Accessing elements
int first = arr2[0];
int element = matrix[1][2];  // 6
```

### Strings

```cpp
#include <string>

// C-style strings
char str1[] = "Hello";
const char* str2 = "World";

// C++ strings
std::string str3 = "Hello";
std::string str4 = "World";

// String operations
std::string combined = str3 + " " + str4;  // Concatenation
int length = str3.length();
char ch = str3[0];                         // Access character
str3.append(" there");
str3.substr(0, 5);                         // Substring
```

## 8. Pointers and References

### Pointers

```cpp
int x = 10;
int* ptr = &x;        // Pointer to x

std::cout << *ptr;    // Dereference: 10
*ptr = 20;            // Modify through pointer

// Null pointer
int* nullPtr = nullptr;  // C++11

// Pointer arithmetic
int arr[] = {1, 2, 3, 4, 5};
int* p = arr;
p++;                  // Points to arr[1]
```

### References

```cpp
int x = 10;
int& ref = x;         // Reference to x

ref = 20;             // Modifies x
std::cout << x;       // 20

// Function with reference parameter
void increment(int& num) {
    num++;
}
```

### Dynamic Memory

```cpp
// Allocate memory
int* ptr = new int;
int* arr = new int[10];

// Deallocate memory
delete ptr;
delete[] arr;

// Smart pointers (C++11)
#include <memory>
std::unique_ptr<int> uptr(new int(42));
std::shared_ptr<int> sptr = std::make_shared<int>(42);
```

## 9. Classes and Objects

### Basic Class

```cpp
class Rectangle {
private:
    int width;
    int height;

public:
    // Constructor
    Rectangle(int w, int h) : width(w), height(h) {}
    
    // Default constructor
    Rectangle() : width(0), height(0) {}
    
    // Destructor
    ~Rectangle() {
        // Cleanup code
    }
    
    // Member functions
    int area() const {
        return width * height;
    }
    
    void setWidth(int w) {
        width = w;
    }
    
    int getWidth() const {
        return width;
    }
};

// Usage
Rectangle rect(10, 5);
int a = rect.area();
```

### Access Specifiers

```cpp
class Example {
public:
    int publicVar;      // Accessible everywhere
    
protected:
    int protectedVar;   // Accessible in class and derived classes
    
private:
    int privateVar;     // Only accessible in this class
};
```

### Inheritance

```cpp
class Shape {
protected:
    int width;
    int height;

public:
    Shape(int w, int h) : width(w), height(h) {}
    virtual int area() { return 0; }  // Virtual function
};

class Rectangle : public Shape {
public:
    Rectangle(int w, int h) : Shape(w, h) {}
    
    int area() override {  // Override base class function
        return width * height;
    }
};

class Circle : public Shape {
private:
    int radius;

public:
    Circle(int r) : Shape(0, 0), radius(r) {}
    
    int area() override {
        return 3.14 * radius * radius;
    }
};
```

### Polymorphism

```cpp
Shape* shape1 = new Rectangle(10, 5);
Shape* shape2 = new Circle(7);

std::cout << shape1->area();  // Calls Rectangle::area()
std::cout << shape2->area();  // Calls Circle::area()

delete shape1;
delete shape2;
```

### Static Members

```cpp
class Counter {
private:
    static int count;  // Static member variable

public:
    Counter() {
        count++;
    }
    
    static int getCount() {  // Static member function
        return count;
    }
};

// Initialize static member
int Counter::count = 0;
```

### Friend Functions

```cpp
class Box {
private:
    int width;

public:
    Box(int w) : width(w) {}
    
    friend void printWidth(Box& b);  // Friend function
};

void printWidth(Box& b) {
    std::cout << b.width;  // Can access private members
}
```

## 10. Templates

### Function Templates

```cpp
template <typename T>
T maximum(T a, T b) {
    return (a > b) ? a : b;
}

int x = maximum(5, 10);
double y = maximum(3.14, 2.71);
```

### Class Templates

```cpp
template <typename T>
class Container {
private:
    T value;

public:
    Container(T v) : value(v) {}
    
    T getValue() const {
        return value;
    }
    
    void setValue(T v) {
        value = v;
    }
};

Container<int> intContainer(42);
Container<std::string> strContainer("Hello");
```

## 11. Standard Template Library (STL)

### Vector

```cpp
#include <vector>

std::vector<int> vec;           // Empty vector
std::vector<int> vec2 = {1, 2, 3, 4, 5};

vec.push_back(10);              // Add element
vec.pop_back();                 // Remove last element
int size = vec.size();
int first = vec[0];
vec.clear();                    // Remove all elements

// Iteration
for (int i = 0; i < vec2.size(); i++) {
    std::cout << vec2[i] << " ";
}

for (int num : vec2) {
    std::cout << num << " ";
}
```

### Map

```cpp
#include <map>

std::map<std::string, int> ages;

ages["Alice"] = 25;
ages["Bob"] = 30;

int aliceAge = ages["Alice"];

// Iteration
for (const auto& pair : ages) {
    std::cout << pair.first << ": " << pair.second << std::endl;
}
```

### Set

```cpp
#include <set>

std::set<int> numbers;

numbers.insert(5);
numbers.insert(3);
numbers.insert(5);  // Duplicates ignored

if (numbers.find(3) != numbers.end()) {
    std::cout << "Found 3" << std::endl;
}
```

### Other Containers

```cpp
#include <list>
#include <queue>
#include <stack>

std::list<int> myList;
std::queue<int> myQueue;
std::stack<int> myStack;
```

## 12. Exception Handling

```cpp
#include <exception>
#include <stdexcept>

try {
    int x = 10;
    if (x < 0) {
        throw std::runtime_error("Negative value");
    }
    
    int* ptr = nullptr;
    if (ptr == nullptr) {
        throw "Null pointer exception";
    }
}
catch (const std::runtime_error& e) {
    std::cout << "Runtime error: " << e.what() << std::endl;
}
catch (const char* msg) {
    std::cout << "Error: " << msg << std::endl;
}
catch (...) {
    std::cout << "Unknown exception" << std::endl;
}
```

### Custom Exceptions

```cpp
class MyException : public std::exception {
private:
    std::string message;

public:
    MyException(const std::string& msg) : message(msg) {}
    
    const char* what() const noexcept override {
        return message.c_str();
    }
};

try {
    throw MyException("Custom error");
}
catch (const MyException& e) {
    std::cout << e.what() << std::endl;
}
```

## 13. File I/O

```cpp
#include <fstream>
#include <iostream>

// Writing to file
std::ofstream outFile("output.txt");
if (outFile.is_open()) {
    outFile << "Hello, File!" << std::endl;
    outFile << "Line 2" << std::endl;
    outFile.close();
}

// Reading from file
std::ifstream inFile("input.txt");
if (inFile.is_open()) {
    std::string line;
    while (std::getline(inFile, line)) {
        std::cout << line << std::endl;
    }
    inFile.close();
}

// Reading/Writing
std::fstream file("data.txt", std::ios::in | std::ios::out);
```

## 14. Namespaces

```cpp
namespace MyNamespace {
    int value = 42;
    
    void myFunction() {
        std::cout << "Function in namespace" << std::endl;
    }
}

// Usage
MyNamespace::myFunction();
int x = MyNamespace::value;

// Using declaration
using MyNamespace::value;
int y = value;

// Using directive (use cautiously)
using namespace MyNamespace;
myFunction();
```

## 15. Enum

```cpp
// Traditional enum
enum Color {
    RED,
    GREEN,
    BLUE
};

Color c = RED;

// Enum class (C++11) - strongly typed
enum class Direction {
    NORTH,
    SOUTH,
    EAST,
    WEST
};

Direction d = Direction::NORTH;
```

## 16. Struct

```cpp
struct Point {
    int x;
    int y;
    
    // Structs can have constructors and methods
    Point(int x, int y) : x(x), y(y) {}
    
    void print() {
        std::cout << "(" << x << ", " << y << ")" << std::endl;
    }
};

Point p1 = {10, 20};
Point p2(30, 40);
```

## 17. Preprocessor Directives

```cpp
#include <iostream>        // Include header
#define PI 3.14159         // Define constant
#define MAX(a, b) ((a) > (b) ? (a) : (b))  // Macro

#ifdef DEBUG
    std::cout << "Debug mode" << std::endl;
#endif

#ifndef HEADER_H
#define HEADER_H
// Header content
#endif

#pragma once              // Include guard (modern)
```

## Key Tips

1. **Always initialize variables** before use
2. **Use `const` when values shouldn't change**
3. **Prefer references over pointers** when possible
4. **Use smart pointers** instead of raw pointers for dynamic memory
5. **Follow RAII principle** (Resource Acquisition Is Initialization)
6. **Use range-based for loops** when iterating over containers
7. **Prefer STL containers** over raw arrays
8. **Use `auto`** to reduce verbosity when type is obvious
9. **Mark functions that don't modify state as `const`**
10. **Use `override` keyword** when overriding virtual functions

I'll create a comprehensive C++ syntax guide covering all the essential topics. This will serve as a solid reference for learning or reviewing C++ fundamentals.I've created a comprehensive C++ syntax guide covering all the essential topics you requested. The guide includes:

- **Basic program structure** and setup
- **Variables and data types** (primitives, modifiers, auto keyword)
- **All operators** (arithmetic, comparison, logical, bitwise, assignment)
- **Control structures** (if-else, switch, ternary operator)
- **All loop types** (for, while, do-while, range-based for)
- **Functions** (declaration, overloading, default parameters, lambdas)
- **Arrays and strings** (including C++ string class)
- **Pointers and references** (including smart pointers)
- **Classes and OOP** (constructors, inheritance, polymorphism, virtual functions)
- **Templates** (function and class templates)
- **STL basics** (vector, map, set, and other containers)
- **Exception handling** (try-catch, custom exceptions)
- **File I/O operations**
- **Namespaces, enums, structs**
- **Preprocessor directives**

Each section includes practical code examples and explanations. The guide ends with key tips for writing better C++ code. This should serve as a solid reference whether you're learning C++ or need a quick syntax reminder!