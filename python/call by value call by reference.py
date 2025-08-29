# In Python, the concepts of **call by value** and **call by reference** are often discussed in the context of how arguments are passed to functions. 
# However, Python uses a mechanism that is best described as **call by object reference** or **call by assignment**. 
# This is distinct from traditional call by value or call by reference, and understanding it requires looking at Python's data types and their internal behavior.

# Below, I’ll explain:

# 1. **Call by Value vs. Call by Reference vs. Python’s Mechanism**
# 2. **Python Data Types**
# 3. **How Python Handles Argument Passing Internally**
# 4. **Examples for Clarity**

# ---

### 1. Call by Value vs. Call by Reference vs. Python’s Mechanism

# - **Call by Value**: In languages like C, when a function is called, a copy of the argument’s value is passed to the function. 
# Modifications to the parameter inside the function do not affect the original variable outside the function. This applies to immutable types in Python (to some extent).

# - **Call by Reference**: In languages like C++ (with references or pointers), the memory address of the argument is passed to the function. 
# Modifications to the parameter inside the function directly affect the original variable. This resembles Python’s behavior with mutable types.

# - **Python’s Call by Object Reference**:
#   - Python passes references to objects (not copies of values or direct memory addresses).
#   - The behavior depends on whether the object is **mutable** (e.g., lists, dictionaries) or **immutable** (e.g., integers, strings, tuples).
#   - If the object is mutable, modifications inside the function affect the original object.
#   - If the object is immutable, modifications create a new object, leaving the original unchanged.

# ---

### 2. Python Data Types

# Python’s data types can be broadly classified as **mutable** or **immutable**. This distinction is key to understanding how argument passing works.

#### Immutable Types
# Immutable objects cannot be modified after creation. Any operation that seems to modify them creates a new object.

# - **int**: Integer numbers (e.g., `5`, `-10`)
# - **float**: Floating-point numbers (e.g., `3.14`, `0.001`)
# - **complex**: Complex numbers (e.g., `3+4j`)
# - **str**: Strings (e.g., `"hello"`)
# - **tuple**: Immutable sequences (e.g., `(1, 2, 3)`)
# - **frozenset**: Immutable set (e.g., `frozenset([1, 2, 3])`)
# - **bool**: Boolean values (`True`, `False`)
# - **bytes**: Immutable byte sequences (e.g., `b"hello"`)

#### Mutable Types
# Mutable objects can be modified in place after creation.

# - **list**: Ordered, mutable sequences (e.g., `[1, 2, 3]`)
# - **dict**: Key-value mappings (e.g., `{"a": 1, "b": 2}`)
# - **set**: Unordered collections of unique elements (e.g., `{1, 2, 3}`)
# - **bytearray**: Mutable byte sequences (e.g., `bytearray(b"hello")`)
# - **User-defined classes**: Objects of custom classes (unless explicitly made immutable)

#### Special Types
# - **NoneType**: The `None` object, representing the absence of a value.
# - **Function, Module, Class Objects**: These are less commonly manipulated but can be passed to functions.

# ---

### 3. How Python Handles Argument Passing Internally

# Python’s argument-passing mechanism can be summarized as follows:

# 1. **Objects and References**:
#    - Every variable in Python is a reference to an object in memory.
#    - When you pass an argument to a function, you pass a reference to the object, not a copy of the object or its value.

# 2. **Mutable vs. Immutable Behavior**:
#    - **Immutable Objects**: If you attempt to modify an immutable object inside a function (e.g., an integer or string), a new object is created. 
# The original object remains unchanged because the reference is reassigned to the new object within the function’s scope.
#    - **Mutable Objects**: If you modify a mutable object (e.g., a list or dictionary) inside a function, the changes are reflected in the original object because the 
# reference points to the same object in memory.

# 3. **Assignment vs. Modification**:
#    - **Assignment**: Assigning a new value to a parameter (e.g., `param = 42`) rebinds the parameter to a new object within the function’s scope. 
# This does not affect the original object outside the function.
#    - **Modification**: Modifying a mutable object in place (e.g., `param.append(42)`) changes the object’s state, and since the reference points to 
# the same object, the change is visible outside the function.

# 4. **Memory Management**:
#    - Python uses a **reference counting** mechanism and a **garbage collector** to manage memory.
#    - Objects are stored in memory, and variables hold references to these objects.
#    - When a function is called, the reference (not the object itself) is passed, which is why mutable objects can be modified in place, while immutable objects cannot.

# ---

### 4. Examples for Clarity

#### Example 1: Immutable Type (Integer)

def modify_number(x):
    x = x + 1  # Creates a new integer object
    print(f"Inside function: x = {x}")

num = 5
modify_number(num)
print(f"Outside function: num = {num}")


# **Output**:
# 
# Inside function: x = 6
# Outside function: num = 5
# 

# **Explanation**:
# - `num` is an integer (immutable).
# - When `num` is passed to `modify_number`, the function receives a reference to the integer object `5`.
# - The statement `x = x + 1` creates a new integer object `6` and rebinds `x` to it.
# - The original `num` still points to `5`, so it remains unchanged.

#### Example 2: Mutable Type (List)

def modify_list(lst):
    lst.append(4)  # Modifies the list in place
    print(f"Inside function: lst = {lst}")

my_list = [1, 2, 3]
modify_list(my_list)
print(f"Outside function: my_list = {my_list}")


# **Output**:
# 
# Inside function: lst = [1, 2, 3, 4]
# Outside function: my_list = [1, 2, 3, 4]
# 

# **Explanation**:
# - `my_list` is a list (mutable).
# - The function receives a reference to the same list object.
# - `lst.append(4)` modifies the list in place, so the change is visible outside the function.

#### Example 3: Reassigning a Mutable Type

def reassign_list(lst):
    lst = [7, 8, 9]  # Reassigns lst to a new list
    print(f"Inside function: lst = {lst}")

my_list = [1, 2, 3]
reassign_list(my_list)
print(f"Outside function: my_list = {my_list}")


# **Output**:
# 
# Inside function: lst = [7, 8, 9]
# Outside function: my_list = [1, 2, 3]
# 

# **Explanation**:
# - Reassigning `lst` to a new list `[7, 8, 9]` creates a new object and rebinds the local variable `lst`.
# - The original `my_list` still points to `[1, 2, 3]`, so it remains unchanged.

#### Example 4: Immutable Type with String

def modify_string(s):
    s = s + " world"  # Creates a new string
    print(f"Inside function: s = {s}")

text = "hello"
modify_string(text)
print(f"Outside function: text = {text}")


# **Output**:
# 
# Inside function: s = hello world
# Outside function: text = hello
# 

# **Explanation**:
# - Strings are immutable, so `s = s + " world"` creates a new string object.
# - The original `text` remains unchanged.

#### Example 5: Complex Example with Mixed Types

def mixed_types(num, lst, s):
    num += 1  # New integer object
    lst.append(4)  # Modifies list in place
    s += " world"  # New string object
    print(f"Inside: num={num}, lst={lst}, s={s}")

number = 10
my_list = [1, 2, 3]
text = "hello"
mixed_types(number, my_list, text)
print(f"Outside: number={number}, my_list={my_list}, text={text}")


# **Output**:
# 
# Inside: num=11, lst=[1, 2, 3, 4], s=hello world
# Outside: number=10, my_list=[1, 2, 3, 4], text=hello
# 

# **Explanation**:
# - `num` (integer) is immutable, so `num += 1` creates a new object.
# - `lst` (list) is mutable, so `lst.append(4)` modifies the original list.
# - `s` (string) is immutable, so `s += " world"` creates a new string.

# ---

### 5. Internal Workings Summary

# - **Object References**: Variables in Python are names bound to objects. Passing an argument to a function binds the parameter name to the same object.
# - **Mutable Objects**: Modifications (e.g., `append`, `update`) change the object’s state, affecting all references to it.
# - **Immutable Objects**: Operations that seem to modify the object (e.g., `+=`) create a new object, and the local parameter is rebound, leaving the original unchanged.
# - **Memory**: Python’s memory manager ensures that objects are shared efficiently (e.g., small integers are reused), but this is transparent to the programmer.

# ---

### Key Takeaways

# - Python’s argument passing is **call by object reference**, not strictly call by value or call by reference.
# - The behavior depends on whether the object is mutable or immutable:
#   - **Mutable**: Changes are reflected outside the function if modified in place.
#   - **Immutable**: Changes create new objects, leaving the original unchanged.
# - All Python data types (int, float, str, list, dict, etc.) follow this model, and the distinction between mutable and immutable types governs their behavior.

# If you have further questions or want more examples, let me know!

####

# I'll explain call by value and call by reference in Python, how it works internally, and compare it with C++.

## Python's Parameter Passing Mechanism

# Python uses **"call by object reference"** (also called "call by sharing"), which is different from traditional call by value or call by reference. Here's how it works:

### How Python Handles Different Data Types## How It Works Internally

### Memory Management and Object References

# **Python's approach:**
# - Everything in Python is an object
# - Variables are references (names) that point to objects in memory
# - When you pass a parameter, you're passing the reference to the object, not the object itself
# - The function parameter becomes another reference to the same object

# **Internal mechanism:**
# 1. **Object creation**: Objects are stored in heap memory
# 2. **Reference counting**: Python keeps track of how many references point to each object
# 3. **Namespace binding**: Variable names are bound to object references
# 4. **Parameter passing**: Function parameters receive copies of the references, not copies of the objects

### Data Type Categories

# **Immutable Objects** (behave like call by value):
# - `int`, `float`, `str`, `tuple`, `frozenset`, `bytes`, `bool`, `None`
# - Any operation creates a new object
# - Original object remains unchanged

# **Mutable Objects** (behave like call by reference):
# - `list`, `dict`, `set`, `bytearray`, custom class instances
# - Operations can modify the object in-place
# - Changes are visible to all references

## Comparison with C++## Key Differences: Python vs C++

### 1. **Explicit Control (C++)**
# - **Call by value**: Explicitly copies the entire object
# - **Call by reference**: Explicitly passes reference using `&`
# - **Call by pointer**: Explicitly passes memory address using `*`

### 2. **Automatic Behavior (Python)**
# - **No explicit syntax**: Behavior depends on object mutability
# - **Always passes references**: But effect depends on whether object is mutable
# - **No memory address access**: Can't directly manipulate pointers

### 3. **Memory Management**
# - **C++**: Manual memory management, stack vs heap allocation
# - **Python**: Automatic garbage collection, all objects on heap

### 4. **Performance Implications**
# - **C++**: Call by value can be expensive for large objects (full copy)
# - **Python**: Always efficient reference passing, but object creation/destruction handled by GC

## Real-World Security Considerations

# When building secure applications with Django REST Framework:


# SECURITY RISK: Direct mutation
def update_user_permissions(user_permissions: list, new_perms: list) -> None:
    """BAD: Directly modifying user permissions without validation"""
    user_permissions.extend(new_perms)  # Dangerous!

# SECURE APPROACH: Defensive copying and validation
def secure_update_permissions(user_permissions: list, new_perms: list) -> list:
    """GOOD: Validate and return new permissions list"""
    import copy
    
    # Validate new permissions
    validated_perms = validate_permissions(new_perms)
    
    # Return new list instead of modifying original
    return user_permissions + validated_perms

# For Django models (mutable objects)
def update_user_safely(user_instance):
    """Always validate before modifying model instances"""
    # user_instance is mutable - changes affect database
    if validate_user_data(user_instance):
        user_instance.save()  # This modifies the actual DB record


# Python Parameter Passing: Call by Object Reference

# 1. IMMUTABLE OBJECTS (behave like call by value)
def modify_immutable(x: int, name: str, tup: tuple) -> None:
    """
    Immutable objects: int, float, str, tuple, frozenset, bytes
    Changes create new objects, original remains unchanged
    """
    print(f"Inside function - Before: x={x}, name='{name}', tup={tup}")
    print(f"Object IDs - x: {id(x)}, name: {id(name)}, tup: {id(tup)}")
    
    # These operations create NEW objects
    x = x + 10  # New int object
    name = name + " modified"  # New string object
    tup = tup + (4,)  # New tuple object
    
    print(f"Inside function - After: x={x}, name='{name}', tup={tup}")
    print(f"New Object IDs - x: {id(x)}, name: {id(name)}, tup: {id(tup)}")

# Test immutable objects
print("=== IMMUTABLE OBJECTS ===")
num = 5
string = "hello"
tuple_obj = (1, 2, 3)

print(f"Before function call: num={num}, string='{string}', tuple={tuple_obj}")
print(f"Original IDs - num: {id(num)}, string: {id(string)}, tuple: {id(tuple_obj)}")

modify_immutable(num, string, tuple_obj)

print(f"After function call: num={num}, string='{string}', tuple={tuple_obj}")
print(f"Original IDs unchanged - num: {id(num)}, string: {id(string)}, tuple: {id(tuple_obj)}")

print("\n" + "="*60 + "\n")

# 2. MUTABLE OBJECTS (behave like call by reference)
def modify_mutable(lst: list, dct: dict, st: set) -> None:
    """
    Mutable objects: list, dict, set, custom objects
    Modifications affect the original object
    """
    print(f"Inside function - Before: lst={lst}, dct={dct}, st={st}")
    print(f"Object IDs - lst: {id(lst)}, dct: {id(dct)}, st: {id(st)}")
    
    # These operations modify the SAME objects
    lst.append(4)  # Modifies original list
    dct['new_key'] = 'new_value'  # Modifies original dict
    st.add('new_item')  # Modifies original set
    
    print(f"Inside function - After: lst={lst}, dct={dct}, st={st}")
    print(f"Same Object IDs - lst: {id(lst)}, dct: {id(dct)}, st: {id(st)}")

# Test mutable objects
print("=== MUTABLE OBJECTS ===")
my_list = [1, 2, 3]
my_dict = {'a': 1, 'b': 2}
my_set = {'item1', 'item2'}

print(f"Before function call: list={my_list}, dict={my_dict}, set={my_set}")
print(f"Original IDs - list: {id(my_list)}, dict: {id(my_dict)}, set: {id(my_set)}")

modify_mutable(my_list, my_dict, my_set)

print(f"After function call: list={my_list}, dict={my_dict}, set={my_set}")
print(f"Same IDs - list: {id(my_list)}, dict: {id(my_dict)}, set: {id(my_set)}")

print("\n" + "="*60 + "\n")

# 3. REASSIGNMENT vs MODIFICATION
def reassign_vs_modify(lst: list) -> None:
    """
    Demonstrates difference between reassignment and modification
    """
    print(f"Parameter lst ID: {id(lst)}")
    
    # MODIFICATION - affects original
    lst.append('modified')
    print(f"After append: {lst}, ID: {id(lst)}")
    
    # REASSIGNMENT - creates new local reference
    lst = ['completely', 'new', 'list']
    print(f"After reassignment: {lst}, ID: {id(lst)}")

print("=== REASSIGNMENT vs MODIFICATION ===")
original_list = ['a', 'b', 'c']
print(f"Original list: {original_list}, ID: {id(original_list)}")

reassign_vs_modify(original_list)

print(f"After function: {original_list}, ID: {id(original_list)}")

print("\n" + "="*60 + "\n")

# 4. CUSTOM OBJECTS
class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    
    def __str__(self):
        return f"Person(name='{self.name}', age={self.age})"

def modify_custom_object(person: Person) -> None:
    """
    Custom objects are mutable - modifications affect original
    """
    print(f"Inside function - Before: {person}, ID: {id(person)}")
    
    # Modify object attributes
    person.name = "Modified Name"
    person.age = 999
    
    print(f"Inside function - After: {person}, ID: {id(person)}")

print("=== CUSTOM OBJECTS ===")
person_obj = Person("Alice", 25)
print(f"Before function: {person_obj}, ID: {id(person_obj)}")

modify_custom_object(person_obj)

print(f"After function: {person_obj}, ID: {id(person_obj)}")

print("\n" + "="*60 + "\n")

# 5. DEFENSIVE COPYING
import copy

def safe_modify_list(lst: list) -> list:
    """
    Use copy to avoid modifying original
    """
    # Shallow copy for simple objects
    local_copy = lst.copy()  # or list(lst) or lst[:]
    local_copy.append('safely added')
    return local_copy

def safe_modify_complex(data: dict) -> dict:
    """
    Use deepcopy for nested structures
    """
    local_copy = copy.deepcopy(data)
    local_copy['nested']['new_key'] = 'new_value'
    return local_copy

print("=== DEFENSIVE COPYING ===")
original_data = [1, 2, 3]
result = safe_modify_list(original_data)
print(f"Original: {original_data}, Modified copy: {result}")

complex_data = {'nested': {'key': 'value'}}
result_complex = safe_modify_complex(complex_data)
print(f"Original: {complex_data}")
print(f"Modified copy: {result_complex}")

## Architecture Insights

# Understanding Python's parameter passing is crucial for:

# 1. **API Design**: When designing REST endpoints, knowing that mutable objects are shared helps prevent accidental data corruption
# 2. **Caching**: Mutable objects in Redis need careful handling to avoid cache corruption
# 3. **WebSocket Real-time Updates**: Shared mutable state between WebSocket connections requires proper synchronization
# 4. **Database Transactions**: Django model instances are mutable - understand when changes are committed

# This knowledge directly impacts your system design decisions, especially when building scalable applications with Django, channels, and Redis for real-time features.

# // C++ Parameter Passing Examples

#include <iostream>
#include <vector>
#include <string>

# // 1. CALL BY VALUE (C++)
# void modify_by_value(int x, std::string str, std::vector<int> vec) {
#     std::cout << "Inside function (by value):\n";
#     std::cout << "  x address: " << &x << std::endl;
#     std::cout << "  str address: " << &str << std::endl;
#     std::cout << "  vec address: " << &vec << std::endl;
    
#     // These modify COPIES, not originals
#     x = 100;
#     str = "modified string";
#     vec.push_back(999);
    
#     std::cout << "  Modified values: x=" << x << ", str='" << str << "', vec size=" << vec.size() << std::endl;
# }

# // 2. CALL BY REFERENCE (C++)
# void modify_by_reference(int& x, std::string& str, std::vector<int>& vec) {
#     std::cout << "Inside function (by reference):\n";
#     std::cout << "  x address: " << &x << std::endl;
#     std::cout << "  str address: " << &str << std::endl;
#     std::cout << "  vec address: " << &vec << std::endl;
    
#     // These modify ORIGINALS
#     x = 200;
#     str = "reference modified";
#     vec.push_back(888);
    
#     std::cout << "  Modified values: x=" << x << ", str='" << str << "', vec size=" << vec.size() << std::endl;
# }

# // 3. CALL BY POINTER (C++)
# void modify_by_pointer(int* x, std::string* str, std::vector<int>* vec) {
#     std::cout << "Inside function (by pointer):\n";
#     std::cout << "  x address: " << x << std::endl;
#     std::cout << "  str address: " << str << std::endl;
#     std::cout << "  vec address: " << vec << std::endl;
    
#     // These modify ORIGINALS through pointers
#     *x = 300;
#     *str = "pointer modified";
#     vec->push_back(777);
    
#     std::cout << "  Modified values: x=" << *x << ", str='" << *str << "', vec size=" << vec->size() << std::endl;
# }

# int main() {
#     // Original variables
#     int num = 10;
#     std::string text = "original";
#     std::vector<int> numbers = {1, 2, 3};
    
#     std::cout << "=== ORIGINAL VALUES ===\n";
#     std::cout << "num address: " << &num << ", value: " << num << std::endl;
#     std::cout << "text address: " << &text << ", value: '" << text << "'" << std::endl;
#     std::cout << "numbers address: " << &numbers << ", size: " << numbers.size() << std::endl;
    
#     std::cout << "\n=== CALL BY VALUE ===\n";
#     modify_by_value(num, text, numbers);
#     std::cout << "After call by value: num=" << num << ", text='" << text << "', numbers size=" << numbers.size() << std::endl;
    
#     std::cout << "\n=== CALL BY REFERENCE ===\n";
#     modify_by_reference(num, text, numbers);
#     std::cout << "After call by reference: num=" << num << ", text='" << text << "', numbers size=" << numbers.size() << std::endl;
    
#     std::cout << "\n=== CALL BY POINTER ===\n";
#     modify_by_pointer(&num, &text, &numbers);
#     std::cout << "After call by pointer: num=" << num << ", text='" << text << "', numbers size=" << numbers.size() << std::endl;
    
#     return 0;
# }


# Expected Output:
# === ORIGINAL VALUES ===
# num address: 0x7fff5fbff6ac, value: 10
# text address: 0x7fff5fbff6b0, value: 'original'
# numbers address: 0x7fff5fbff6d0, size: 3

# === CALL BY VALUE ===
# Inside function (by value):
#   x address: 0x7fff5fbff68c (DIFFERENT from original)
#   str address: 0x7fff5fbff690 (DIFFERENT from original)
#   vec address: 0x7fff5fbff6a0 (DIFFERENT from original)
#   Modified values: x=100, str='modified string', vec size=4
# After call by value: num=10, text='original', numbers size=3 (UNCHANGED)

# === CALL BY REFERENCE ===  
# Inside function (by reference):
#   x address: 0x7fff5fbff6ac (SAME as original)
#   str address: 0x7fff5fbff6b0 (SAME as original)
#   vec address: 0x7fff5fbff6d0 (SAME as original)
#   Modified values: x=200, str='reference modified', vec size=4
# After call by reference: num=200, text='reference modified', numbers size=4 (CHANGED)

# === CALL BY POINTER ===
# Inside function (by pointer):
#   x address: 0x7fff5fbff6ac (SAME as original)
#   str address: 0x7fff5fbff6b0 (SAME as original)
#   vec address: 0x7fff5fbff6d0 (SAME as original)
#   Modified values: x=300, str='pointer modified', vec size=5
# After call by pointer: num=300, text='pointer modified', numbers size=5 (CHANGED)
