DSA
===


A stack is a linear data structure in Data Structures and Algorithms (DSA) that follows the Last In, First Out (LIFO) principle. This means the last element added to the stack is the first one to be removed. Think of it like a stack of plates: you add (push) a plate on top and remove (pop) from the top.

 Key Operations of a Stack
1. Push: Add an element to the top of the stack.
2. Pop: Remove and return the top element from the stack.
3. Peek/Top: View the top element without removing it.
4. isEmpty: Check if the stack is empty.
5. Size: Get the number of elements in the stack.

 Implementation in Python
Python doesn’t have a built-in stack class, but you can implement a stack using:
1. A list (simplest approach).
2. A collections.deque (more efficient for certain operations).
3. A custom class for better control.

# 1. Stack Using a List
Python lists can be used as stacks because they support append (push) and pop operations.

python
# Stack implementation using a list
stack = []

# Push elements
stack.append(1)  # [1]
stack.append(2)  # [1, 2]
stack.append(3)  # [1, 2, 3]
print("Stack after pushing:", stack)

# Pop element
top_element = stack.pop()  # Removes and returns 3
print("Popped element:", top_element)
print("Stack after popping:", stack)

# Peek at top element
if stack:
    print("Top element:", stack[-1])

# Check if stack is empty
print("Is stack empty?", len(stack) == 0)

# Get stack size
print("Stack size:", len(stack))


Output:

Stack after pushing: [1, 2, 3]
Popped element: 3
Stack after popping: [1, 2]
Top element: 2
Is stack empty? False
Stack size: 2


Pros: Simple and intuitive.
Cons: Not thread-safe, and dynamic resizing of lists can be inefficient for very large stacks.

# 2. Stack Using collections.deque
The `collections.deque` is more efficient for stack operations because it’s optimized for appending and popping from both ends.

python
from collections.deque import deque

# Stack implementation using deque
stack = deque()

# Push elements
stack.append(1)  # [1]
stack.append(2)  # [1, 2]
stack.append(3)  # [1, 2, 3]
print("Stack after pushing:", list(stack))

# Pop element
top_element = stack.pop()  # Removes and returns 3
print("Popped element:", top_element)
print("Stack after popping:", list(stack))

# Peek at top element
if stack:
    print("Top element:", stack[-1])

# Check if stack is empty
print("Is stack empty?", len(stack) == 0)

# Get stack size
print("Stack size:", len(stack))


Output: Same as the list example.

Pros: More efficient for large datasets due to optimized memory management.
Cons: Slightly less intuitive than lists for beginners.

# 3. Custom Stack Class
For better encapsulation and control, you can create a custom stack class.

python
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        raise IndexError("Pop from an empty stack")

    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        raise IndexError("Peek from an empty stack")

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)

# Usage
stack = Stack()
stack.push(1)
stack.push(2)
stack.push(3)
print("Stack size:", stack.size())
print("Top element:", stack.peek())
print("Popped element:", stack.pop())
print("Is stack empty?", stack.is_empty())


Output:

Stack size: 3
Top element: 3
Popped element: 3
Is stack empty? False


Pros: Encapsulates stack operations, handles edge cases (e.g., popping from an empty stack), and is easy to extend.
Cons: More code than using a list or deque.

 Time Complexity
| Operation | Time Complexity (List) | Time Complexity (deque) |
|-----------|------------------------|-------------------------|
| Push      | O(1) amortized         | O(1)                    |
| Pop       | O(1)                   | O(1)                    |
| Peek      | O(1)                   | O(1)                    |
| isEmpty   | O(1)                   | O(1)                    |
| Size      | O(1)                   | O(1)                    |

*Note*: List `append` is O(1) amortized because Python occasionally resizes the underlying array, which is O(n) but rare.

 Common Use Cases
Stacks are widely used in:
- Expression evaluation (e.g., balancing parentheses, infix to postfix conversion).
- Backtracking algorithms (e.g., maze solving, depth-first search).
- Function call management (call stack in programming languages).
- Undo mechanisms in applications (e.g., text editors).

 Example: Balancing Parentheses
A classic stack application is checking if parentheses in an expression are balanced.

python
def is_balanced(expression):
    stack = []
    for char in expression:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return False
            stack.pop()
    return len(stack) == 0

# Test
print(is_balanced("((()))"))  # True
print(is_balanced("(()"))     # False


 Recommendations
- Use lists for simple stacks in small-scale applications.
- Use collections.deque for better performance in large-scale applications.
- Use a custom class when you need error handling or specific functionality.

===

Interview QandA
---------------

math lib
even and odd
reverse string
recursion
