# Comprehensive C Language Syntax Guide

## 1. Basic Program Structure

```c
#include <stdio.h>  // Preprocessor directive

int main() {
    printf("Hello, World!\n");
    return 0;  // Return status to OS
}
```

## 2. Data Types

### Primitive Types
```c
int age = 25;              // Integer (4 bytes typically)
float price = 19.99;       // Floating point (4 bytes)
double pi = 3.14159265;    // Double precision (8 bytes)
char grade = 'A';          // Single character (1 byte)
_Bool flag = 1;            // Boolean (0 or 1)

// Size modifiers
short int s = 32767;       // Short integer (2 bytes)
long int l = 2147483647;   // Long integer (4+ bytes)
long long ll = 9223372036854775807LL;  // Long long (8 bytes)
unsigned int u = 4294967295U;  // Unsigned (no negative values)
```

### Type Qualifiers
```c
const int MAX = 100;       // Cannot be modified
volatile int sensor;       // May change unexpectedly
```

## 3. Variables and Constants

```c
// Variable declaration
int x;
int y = 10;
int a, b, c;

// Constants
#define PI 3.14159         // Preprocessor constant
const float E = 2.71828;   // Const variable
enum { BUFFER_SIZE = 512 }; // Enum constant
```

## 4. Operators

### Arithmetic Operators
```c
int a = 10, b = 3;
int sum = a + b;        // Addition: 13
int diff = a - b;       // Subtraction: 7
int prod = a * b;       // Multiplication: 30
int quot = a / b;       // Division: 3 (integer division)
int rem = a % b;        // Modulus: 1

a++;  // Increment (a = 11)
b--;  // Decrement (b = 2)
```

### Relational Operators
```c
a == b  // Equal to
a != b  // Not equal to
a > b   // Greater than
a < b   // Less than
a >= b  // Greater than or equal to
a <= b  // Less than or equal to
```

### Logical Operators
```c
int x = 1, y = 0;
x && y  // Logical AND: 0
x || y  // Logical OR: 1
!x      // Logical NOT: 0
```

### Bitwise Operators
```c
int a = 5;   // Binary: 0101
int b = 3;   // Binary: 0011

a & b   // AND: 1 (0001)
a | b   // OR: 7 (0111)
a ^ b   // XOR: 6 (0110)
~a      // NOT: -6 (inverts all bits)
a << 1  // Left shift: 10 (1010)
a >> 1  // Right shift: 2 (0010)
```

### Assignment Operators
```c
int x = 10;
x += 5;   // x = x + 5
x -= 3;   // x = x - 3
x *= 2;   // x = x * 2
x /= 4;   // x = x / 4
x %= 3;   // x = x % 3
```

## 5. Conditional Statements

### if-else
```c
int age = 18;

if (age >= 18) {
    printf("Adult\n");
} else if (age >= 13) {
    printf("Teenager\n");
} else {
    printf("Child\n");
}

// Ternary operator
int max = (a > b) ? a : b;
```

### switch-case
```c
char grade = 'B';

switch (grade) {
    case 'A':
        printf("Excellent!\n");
        break;
    case 'B':
    case 'C':
        printf("Good!\n");
        break;
    case 'D':
        printf("Pass\n");
        break;
    default:
        printf("Fail\n");
}
```

## 6. Loops

### for Loop
```c
// Standard for loop
for (int i = 0; i < 10; i++) {
    printf("%d ", i);
}

// Multiple variables
for (int i = 0, j = 10; i < j; i++, j--) {
    printf("%d-%d ", i, j);
}

// Infinite loop
for (;;) {
    // break to exit
}
```

### while Loop
```c
int i = 0;
while (i < 5) {
    printf("%d ", i);
    i++;
}

// Infinite loop
while (1) {
    // break to exit
}
```

### do-while Loop
```c
int i = 0;
do {
    printf("%d ", i);
    i++;
} while (i < 5);
```

### Loop Control
```c
for (int i = 0; i < 10; i++) {
    if (i == 3) continue;  // Skip iteration
    if (i == 7) break;     // Exit loop
    printf("%d ", i);
}
```

## 7. Functions

### Function Declaration and Definition
```c
// Function prototype (declaration)
int add(int a, int b);
void greet(void);

int main() {
    int result = add(5, 3);
    greet();
    return 0;
}

// Function definition
int add(int a, int b) {
    return a + b;
}

void greet(void) {
    printf("Hello!\n");
}
```

### Function Types
```c
// No return value
void printMessage() {
    printf("Message\n");
}

// With return value
int multiply(int x, int y) {
    return x * y;
}

// Pass by value
void increment(int x) {
    x++;  // Original unchanged
}

// Pass by reference (using pointers)
void incrementRef(int *x) {
    (*x)++;  // Original changed
}
```

### Recursion
```c
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
```

## 8. Arrays

### One-Dimensional Arrays
```c
// Declaration and initialization
int numbers[5];
int values[] = {1, 2, 3, 4, 5};
int data[10] = {0};  // Initialize all to 0

// Accessing elements
numbers[0] = 10;
int first = values[0];

// Array size
int size = sizeof(values) / sizeof(values[0]);

// Iterating
for (int i = 0; i < 5; i++) {
    printf("%d ", values[i]);
}
```

### Multi-Dimensional Arrays
```c
// 2D array
int matrix[3][4] = {
    {1, 2, 3, 4},
    {5, 6, 7, 8},
    {9, 10, 11, 12}
};

// Accessing elements
int element = matrix[1][2];  // 7

// Iterating
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 4; j++) {
        printf("%d ", matrix[i][j]);
    }
    printf("\n");
}
```

## 9. Pointers

### Pointer Basics
```c
int x = 10;
int *ptr;        // Pointer declaration
ptr = &x;        // Address-of operator

printf("%d\n", *ptr);   // Dereference: 10
printf("%p\n", ptr);    // Address
printf("%p\n", &x);     // Address of x

*ptr = 20;       // Modify through pointer
```

### Pointer Arithmetic
```c
int arr[] = {10, 20, 30, 40};
int *p = arr;

printf("%d\n", *p);      // 10
printf("%d\n", *(p+1));  // 20
printf("%d\n", *(p+2));  // 30

p++;  // Move to next element
```

### Pointer to Pointer
```c
int x = 5;
int *p = &x;
int **pp = &p;

printf("%d\n", **pp);  // 5
```

### Function Pointers
```c
int add(int a, int b) {
    return a + b;
}

int main() {
    int (*funcPtr)(int, int) = add;
    int result = funcPtr(5, 3);  // 8
    return 0;
}
```

## 10. Strings

```c
// Character arrays
char str1[20] = "Hello";
char str2[] = "World";
char str3[10];

// String functions (string.h)
#include <string.h>

strlen(str1);              // Length
strcpy(str3, str1);        // Copy
strcat(str1, str2);        // Concatenate
strcmp(str1, str2);        // Compare (0 if equal)
strchr(str1, 'e');         // Find character
strstr(str1, "llo");       // Find substring

// String input/output
scanf("%s", str3);         // Read (no spaces)
fgets(str3, 10, stdin);    // Read line
printf("%s\n", str1);      // Print
```

## 11. Structures

### Structure Definition
```c
// Define a structure
struct Person {
    char name[50];
    int age;
    float height;
};

// Declare and initialize
struct Person person1;
struct Person person2 = {"John", 25, 5.9};

// Access members
person1.age = 30;
strcpy(person1.name, "Alice");
printf("%s is %d years old\n", person1.name, person1.age);
```

### Typedef with Structures
```c
typedef struct {
    int x;
    int y;
} Point;

Point p1 = {10, 20};
printf("(%d, %d)\n", p1.x, p1.y);
```

### Nested Structures
```c
struct Date {
    int day;
    int month;
    int year;
};

struct Employee {
    char name[50];
    struct Date birthdate;
    float salary;
};

struct Employee emp = {"Bob", {15, 6, 1990}, 50000.0};
printf("Born: %d/%d/%d\n", emp.birthdate.day, 
       emp.birthdate.month, emp.birthdate.year);
```

### Pointers to Structures
```c
struct Person *ptr = &person1;
ptr->age = 35;  // Arrow operator
(*ptr).age = 35;  // Equivalent
```

## 12. Unions

```c
// Union - shares memory for all members
union Data {
    int i;
    float f;
    char str[20];
};

union Data data;
data.i = 10;
printf("%d\n", data.i);

data.f = 3.14;  // Overwrites i
printf("%f\n", data.f);

// Size is the largest member
printf("Size: %lu\n", sizeof(union Data));
```

## 13. Enumerations

```c
// Define enum
enum Day {
    SUNDAY,    // 0
    MONDAY,    // 1
    TUESDAY,   // 2
    WEDNESDAY, // 3
    THURSDAY,  // 4
    FRIDAY,    // 5
    SATURDAY   // 6
};

enum Day today = WEDNESDAY;

// Custom values
enum Status {
    ERROR = -1,
    SUCCESS = 0,
    PENDING = 1
};
```

## 14. Preprocessor Directives

```c
// File inclusion
#include <stdio.h>    // Standard library
#include "myheader.h" // User-defined

// Macro definition
#define PI 3.14159
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))

// Conditional compilation
#define DEBUG 1

#ifdef DEBUG
    printf("Debug mode\n");
#endif

#ifndef BUFFER_SIZE
    #define BUFFER_SIZE 1024
#endif

#if DEBUG == 1
    printf("Debugging...\n");
#elif DEBUG == 2
    printf("Verbose debugging...\n");
#else
    printf("No debug\n");
#endif

// Undefine macro
#undef PI

// Predefined macros
printf("%s\n", __FILE__);     // Current file
printf("%d\n", __LINE__);     // Current line
printf("%s\n", __DATE__);     // Compilation date
printf("%s\n", __TIME__);     // Compilation time
```

## 15. File I/O

```c
#include <stdio.h>

// Writing to file
FILE *fp = fopen("data.txt", "w");
if (fp != NULL) {
    fprintf(fp, "Hello, File!\n");
    fputs("Another line\n", fp);
    fputc('A', fp);
    fclose(fp);
}

// Reading from file
fp = fopen("data.txt", "r");
if (fp != NULL) {
    char buffer[100];
    
    // Read line
    while (fgets(buffer, 100, fp) != NULL) {
        printf("%s", buffer);
    }
    
    fclose(fp);
}

// File modes
// "r"  - Read
// "w"  - Write (creates/truncates)
// "a"  - Append
// "r+" - Read and write
// "w+" - Read and write (creates/truncates)
// "a+" - Read and append

// Binary files
fp = fopen("data.bin", "wb");
int data[] = {1, 2, 3, 4, 5};
fwrite(data, sizeof(int), 5, fp);
fclose(fp);

fp = fopen("data.bin", "rb");
int read_data[5];
fread(read_data, sizeof(int), 5, fp);
fclose(fp);
```

## 16. Dynamic Memory Allocation

```c
#include <stdlib.h>

// malloc - allocate memory
int *arr = (int *)malloc(5 * sizeof(int));
if (arr != NULL) {
    for (int i = 0; i < 5; i++) {
        arr[i] = i;
    }
}

// calloc - allocate and initialize to zero
int *arr2 = (int *)calloc(5, sizeof(int));

// realloc - resize memory
arr = (int *)realloc(arr, 10 * sizeof(int));

// free - deallocate memory
free(arr);
free(arr2);

// Dynamic 2D array
int **matrix = (int **)malloc(3 * sizeof(int *));
for (int i = 0; i < 3; i++) {
    matrix[i] = (int *)malloc(4 * sizeof(int));
}

// Free 2D array
for (int i = 0; i < 3; i++) {
    free(matrix[i]);
}
free(matrix);
```

## 17. Command Line Arguments

```c
int main(int argc, char *argv[]) {
    printf("Number of arguments: %d\n", argc);
    
    for (int i = 0; i < argc; i++) {
        printf("Argument %d: %s\n", i, argv[i]);
    }
    
    return 0;
}
```

## 18. Type Casting

```c
// Implicit casting
int i = 10;
float f = i;  // int to float

// Explicit casting
float x = 3.14;
int y = (int)x;  // 3

// Pointer casting
int *ptr = (int *)malloc(sizeof(int));
void *void_ptr = ptr;
int *int_ptr = (int *)void_ptr;
```

## 19. Storage Classes

```c
// auto (default for local variables)
auto int x = 10;

// static - retains value between function calls
void counter() {
    static int count = 0;
    count++;
    printf("%d\n", count);
}

// extern - global variable declared elsewhere
extern int global_var;

// register - suggests CPU register storage
register int fast_var = 100;
```

## 20. Common Standard Library Functions

```c
// stdio.h
printf(), scanf(), fprintf(), fscanf()
fopen(), fclose(), fgets(), fputs()
getchar(), putchar()

// stdlib.h
malloc(), calloc(), realloc(), free()
atoi(), atof(), atol()
rand(), srand()
exit(), abort()

// string.h
strlen(), strcpy(), strcat(), strcmp()
strchr(), strstr(), strtok()
memcpy(), memset()

// math.h
sqrt(), pow(), sin(), cos(), tan()
log(), log10(), exp()
ceil(), floor(), round()

// time.h
time(), clock()
strftime()

// ctype.h
isalpha(), isdigit(), isspace()
toupper(), tolower()
```

---

## Key Points to Remember

1. **Semicolons**: Every statement ends with a semicolon
2. **Case Sensitive**: `variable` and `Variable` are different
3. **Array Indexing**: Starts at 0
4. **Pointers**: Core feature of C, must understand well
5. **Memory Management**: Manual allocation and deallocation
6. **No Classes**: C is procedural, use structures instead
7. **Header Files**: Use `.h` extension for declarations
8. **Compilation**: C code must be compiled before execution

I'll create a comprehensive guide to C language syntax for you. Note that C doesn't have classes (that's C++), but it does have structures which provide similar data organization capabilities.I've created a comprehensive C language syntax guide covering all the major topics. A quick clarification: C doesn't have **classes** (that's a C++ feature), but it does have **structures** which provide similar data organization capabilities.

The guide includes:

- **Basic syntax** and program structure
- **Data types** (int, float, char, etc.) with modifiers
- **All operators** (arithmetic, logical, bitwise, relational)
- **Control structures** (if-else, switch-case)
- **All loops** (for, while, do-while)
- **Functions** (declaration, definition, recursion)
- **Arrays** (1D and multi-dimensional)
- **Pointers** (one of C's most important features)
- **Strings** and string manipulation
- **Structures** (C's way of grouping data)
- **Unions and Enums**
- **Preprocessor directives** (#define, #include, etc.)
- **File I/O** operations
- **Dynamic memory management** (malloc, free, etc.)
- **Standard library functions**

Each section includes practical code examples you can use as reference. C is a powerful procedural language that forms the foundation for many modern languages. Is there any specific topic you'd like me to explain in more detail?