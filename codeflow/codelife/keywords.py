**1. Keywords:**
- `break`
- `case`
- `catch`
- `class` (introduced in ES6)
- `const` (introduced in ES6)
- `continue`
- `debugger`
- `default`
- `delete`
- `do`
- `else`
- `enum` (introduced in ES6)
- `export` (introduced in ES6)
- `extends` (introduced in ES6)
- `false`
- `finally`
- `for`
- `function`
- `if`
- `import` (introduced in ES6)
- `in`
- `instanceof` (introduced in ES5)
- `interface`
- `let` (introduced in ES6)
- `new`
- `null`
- `return`
- `super`
- `switch`
- `this`
- `throw`
- `true`
- `try`
- `typeof`
- `var` (avoid using in new TypeScript code due to scoping issues)
- `void`
- `while`
- `with` (not recommended due to potential scoping problems)

**2. Type-Related Keywords:**

- `implements`
- `namespace`
- `private`
- `protected`
- `public`
- `static`
- `type`

**3. Utility Keywords:**

- `declare`
- `abstract` (introduced in ES2022)
- `async` (introduced in ES2017)
- `await` (introduced in ES2017)
- `yield` (introduced in ES6)

TypeScript, a typed superset of JavaScript, has its own set of reserved keywords that are used to define the structure and behavior of code. These keywords are crucial for writing TypeScript programs and are derived from both JavaScript and additional TypeScript-specific features.

### TypeScript Keywords


#### JavaScript/TypeScript Common Keywords

1. **break**: Terminates the current loop, switch, or label statement and transfers program control to the statement following the terminated statement.
2. **case**: Defines a block of code in a switch statement that will be executed if its case value matches the switch value.
3. **catch**: Declares a block of statements to be executed if an error occurs in the try block.
4. **class**: Defines a class.
5. **const**: Declares a block-scoped, read-only named constant.
6. **continue**: Terminates the current iteration of the loop and proceeds to the next iteration.
7. **debugger**: Invokes any available debugging functionality.
8. **default**: Specifies the default block of code in a switch statement.
9. **delete**: Deletes an object's property or an element in an array.
10. **do**: Defines a loop that executes a block of code at least once before the condition is tested.
11. **else**: Defines the block of code to be executed if the condition in an if statement is false.
12. **enum**: Defines an enumeration, a distinct type consisting of a set of named constants.
13. **export**: Exports a module, making it available for import in other modules.
14. **extends**: Indicates that a class is inheriting properties and methods from another class.
15. **false**: Represents the Boolean value false.
16. **finally**: Declares a block of code to be executed after the try and catch blocks, regardless of the result.
17. **for**: Defines a loop that executes a block of code a specified number of times.
18. **function**: Declares a function.
19. **if**: Executes a block of code if a specified condition is true.
20. **import**: Imports a module, making it available for use in the current file.
21. **in**: Checks if a property exists in an object.
22. **instanceof**: Checks if an object is an instance of a specific class or constructor function.
23. **new**: Creates an instance of a class.
24. **null**: Represents the absence of any object value.
25. **return**: Exits a function and returns a value.
26. **super**: Refers to the parent class.
27. **switch**: Evaluates an expression and executes the corresponding case block.
28. **this**: Refers to the current instance of a class.
29. **throw**: Throws an exception.
30. **true**: Represents the Boolean value true.
31. **try**: Defines a block of code to be tested for errors while it is being executed.
32. **typeof**: Returns the type of a variable.
33. **var**: Declares a variable, optionally initializing it to a value.
34. **void**: Indicates that a function does not return a value.
35. **while**: Creates a loop that executes a block of code as long as the specified condition evaluates to true.
36. **with**: Extends the scope chain for a statement.

#### TypeScript-Specific Keywords

1. **any**: Declares a variable that can hold any type of value.
2. **as**: Used for type assertions.
3. **async**: Declares an asynchronous function.
4. **await**: Pauses the execution of an async function and waits for the passed Promise's resolution.
5. **boolean**: Declares a variable of type boolean.
6. **constructor**: Defines the constructor method for a class.
7. **declare**: Declares a variable, function, class, etc., without assigning it a value.
8. **get**: Binds an object property to a function that will be called when that property is looked up.
9. **implements**: Checks whether a class satisfies an interface.
10. **interface**: Defines a contract for classes to implement.
11. **keyof**: Represents the names of the properties of a type.
12. **module**: Defines a module, a self-contained piece of code.
13. **namespace**: Used to organize code into logical groups and prevent name collisions.
14. **never**: Represents the type of values that never occur.
15. **readonly**: Declares a field as read-only.
16. **require**: Imports a module (typically used in Node.js).
17. **number**: Declares a variable of type number.
18. **object**: Declares a variable of type object.
19. **set**: Binds an object property to a function that will be called when that property is set.
20. **static**: Defines a static method or property of a class.
21. **string**: Declares a variable of type string.
22. **symbol**: Declares a variable of type symbol.
23. **type**: Defines an alias for a type.
24. **undefined**: Represents the absence of a value.
25. **unknown**: Represents a value whose type is not known.
26. **unique**: Represents a unique symbol.
27. **yield**: Pauses and resumes a generator function.

### Example Usage

Here are some examples demonstrating the use of various TypeScript keywords:

```typescript
// Variable and function declarations
let num: number = 5;
const name: string = 'Alice';

function greet(person: string): string {
    return `Hello, ${person}!`;
}

console.log(greet(name));

// Class and interface
interface Person {
    name: string;
    age: number;
}

class Employee implements Person {
    constructor(public name: string, public age: number, public position: string) {}
}

const emp: Employee = new Employee('Bob', 30, 'Developer');
console.log(emp);

// Enum
enum Color {
    Red,
    Green,
    Blue
}

let color: Color = Color.Green;
console.log(color); // Output: 1

// Async and await
async function fetchData(url: string): Promise<any> {
    const response = await fetch(url);
    const data = await response.json();
    return data;
}

// Type assertion
let someValue: any = "this is a string";
let strLength: number = (someValue as string).length;
console.log(strLength);

// Readonly property
class Car {
    readonly make: string;
    constructor(make: string) {
        this.make = make;
    }
}

const myCar = new Car("Toyota");
// myCar.make = "Honda"; // Error: Cannot assign to 'make' because it is a read-only property.

// Union types
let unionVar: number | string;
unionVar = 10;
unionVar = "Hello";

// Tuple
let tuple: [string, number];
tuple = ["hello", 10];

// Generics
function identity<T>(arg: T): T {
    return arg;
}

let output = identity<string>("myString");
console.log(output);

// Type alias
type StringOrNumber = string | number;
let aliasVar: StringOrNumber;
aliasVar = 10;
aliasVar = "Hello";

// Never
function error(message: string): never {
    throw new Error(message);
}
```



==========================================================
==========================================================
==========================================================


### Python Keywords

1. **False**: Represents the Boolean value false.
2. **None**: Represents a null value or no value at all.
3. **True**: Represents the Boolean value true.
4. **and**: A logical operator for logical conjunction.
5. **as**: Used to create an alias.
6. **assert**: Used for debugging purposes to test if a condition is true.
7. **async**: Defines an asynchronous function (coroutine).
8. **await**: Waits for the completion of an asynchronous function.
9. **break**: Terminates the loop statement and transfers execution to the statement immediately following the loop.
10. **class**: Used to define a new user-defined class.
11. **continue**: Causes the loop to skip the remainder of its body and immediately retest its condition prior to reiterating.
12. **def**: Used to define a new user-defined function.
13. **del**: Deletes objects.
14. **elif**: Used in conditional statements, same as else if.
15. **else**: Used in conditional statements.
16. **except**: Used with exceptions, what to do when an exception occurs.
17. **finally**: Used with exceptions, a block of code that will be executed no matter if there is an exception or not.
18. **for**: Used to create a for loop.
19. **from**: Used to import specific parts of a module.
20. **global**: Declares a variable as global.
21. **if**: Used to make a conditional statement.
22. **import**: Used to import a module.
23. **in**: Used to check if a value is present in a list, tuple, etc.
24. **is**: Used to test object identity.
25. **lambda**: Used to create an anonymous function.
26. **nonlocal**: Declares a variable as not local.
27. **not**: A logical operator for logical negation.
28. **or**: A logical operator for logical disjunction.
29. **pass**: A null statement, a statement that will do nothing.
30. **raise**: Used to raise an exception.
31. **return**: Exits a function and returns a value.
32. **try**: Used to make a try...except statement.
33. **while**: Used to create a while loop.
34. **with**: Used to simplify exception handling.
35. **yield**: Used to end a function, returns a generator.

### Example Usage

Here are some examples demonstrating the use of various keywords:

```python
# if, elif, else
x = 10
if x > 0:
    print("x is positive")
elif x == 0:
    print("x is zero")
else:
    print("x is negative")

# for, in, break, continue
for i in range(10):
    if i == 5:
        break
    if i % 2 == 0:
        continue
    print(i)

# def, return, lambda
def add(a, b):
    return a + b

result = add(5, 3)
print(result)

square = lambda x: x * x
print(square(5))

# try, except, finally, raise
try:
    x = int(input("Enter a number: "))
    if x < 0:
        raise ValueError("Negative number!")
except ValueError as ve:
    print("ValueError:", ve)
finally:
    print("Execution completed")

# class, self
class MyClass:
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

obj = MyClass(10)
print(obj.get_value())

# import, from, as
import math
from math import sqrt as square_root

print(math.pi)
print(square_root(16))

# with, open
with open("example.txt", "w") as file:
    file.write("Hello, world!")

# global, nonlocal
count = 0

def outer():
    count = 10
    def inner():
        nonlocal count
        count += 1
        print("Inner count:", count)
    inner()
    print("Outer count:", count)

outer()

def global_example():
    global count
    count += 1
    print("Global count:", count)

global_example()
```

These examples illustrate