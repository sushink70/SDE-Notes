# A **stack** is a linear data structure that follows the **Last In, First Out (LIFO)** principle, meaning the last element added to the stack is the first one to be removed. 
# Think of it like a stack of plates: you add plates to the top and remove them from the top. 
# In this explanation, I’ll provide a detailed implementation of a stack in Python without using built-in modules, discuss its applications, limitations, real-world examples, 
# advantages, disadvantages, Big O notation, database integration, and security considerations.

# ---

# ### **1. Stack Implementation in Python (Without Built-in Modules)**

# We’ll implement a stack using a Python class with a list as the underlying storage (but without relying on advanced built-in functions like `pop()` or `append()`). 
# The stack will support basic operations: push (add), pop (remove), peek (view top), is_empty (check if empty), and size (get number of elements).


class Stack:
    def __init__(self, capacity):
        """Initialize a stack with a fixed capacity."""
        self.capacity = capacity
        self.items = [None] * capacity  # Fixed-size array
        print("length of items:",len(self.items))
        self.top = -1  # Index of the top element (-1 means empty)

    def is_empty(self):
        """Check if the stack is empty."""
        return self.top == -1

    def is_full(self):
        """Check if the stack is full."""
        return self.top == self.capacity - 1

    def push(self, item):
        """Add an item to the top of the stack."""
        if self.is_full():
            raise OverflowError("Stack is full")
        self.top += 1
        self.items[self.top] = item

    def pop(self):
        """Remove and return the top item from the stack."""
        if self.is_empty():
            raise IndexError("Stack is empty")
        item = self.items[self.top]
        self.items[self.top] = None  # Clear the slot
        self.top -= 1
        return item

    def peek(self):
        """Return the top item without removing it."""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items[self.top]

    def size(self):
        """Return the number of items in the stack."""
        return self.top + 1

# Example usage
stack = Stack(5)  # Stack with capacity 5
stack.push(1)
stack.push(2)
stack.push(3)
print("Top item:", stack.peek())  # Output: Top item: 3
print("Stack size:", stack.size())  # Output: Stack size: 3
print("Popped:", stack.pop())      # Output: Popped: 3
print("Top item after pop:", stack.peek())  # Output: Top item: 2
print("Is empty?", stack.is_empty())  # Output: Is empty? False


# This implementation uses a fixed-size array to store elements, which avoids dynamic resizing (like Python’s `list.append()` would do). 
# For a dynamic stack, you’d need to resize the array when it’s full, but that’s omitted here for simplicity.

# ---

# ### **2. Where Stacks Can Be Used**

# Stacks are fundamental in scenarios requiring LIFO behavior. Common applications include:

# 1. **Function Call Management**: Stacks manage function calls in programming languages, storing return addresses, local variables, and parameters (the "call stack").
# 2. **Expression Evaluation**: Stacks are used to evaluate expressions (e.g., infix to postfix conversion, or evaluating postfix expressions).
# 3. **Undo/Redo Operations**: Applications like text editors or graphic design software use stacks to track actions for undo (pop last action) and redo (push back).
# 4. **Backtracking Algorithms**: Stacks are used in algorithms like depth-first search (DFS), maze solving, or parsing syntax in compilers.
# 5. **Browser History**: Web browsers use stacks to track visited pages, allowing users to go back (pop) to previous pages.

# ---

# ### **3. Where Stacks Should Not Be Used**

# Stacks are not ideal in these scenarios:

# 1. **Random Access**: If you need to access elements in the middle or search for specific items, stacks are inefficient since they only allow access to the top.
# 2. **Large Data Storage**: Stacks with fixed capacity can overflow, and dynamic stacks may require frequent resizing, which is costly.
# 3. **Parallel Processing**: Stacks are inherently sequential (LIFO), making them unsuitable for scenarios requiring concurrent access without additional synchronization.
# 4. **Complex Data Relationships**: For hierarchical or networked data (e.g., graphs or trees), other structures like trees or graphs are more appropriate.

# ---

### **4. Real-World Code Example**

# Here’s a practical example of using a stack to implement an **undo feature** in a text editor, where each edit is stored and can be undone by popping the last change.


class TextEditor:
    def __init__(self):
        self.text = ""
        self.undo_stack = Stack(100)  # Stack to store edit history

    def add_text(self, new_text):
        """Add text and save the previous state for undo."""
        self.undo_stack.push(self.text)  # Save current state
        self.text += new_text
        print(f"Text updated: {self.text}")

    def undo(self):
        """Revert to the previous state."""
        if self.undo_stack.is_empty():
            print("Nothing to undo")
            return
        self.text = self.undo_stack.pop()
        print(f"Undo performed. Current text: {self.text}")

# Usage
editor = TextEditor()
editor.add_text("Hello, ")
editor.add_text("world!")
editor.undo()  # Reverts to "Hello, "
editor.undo()  # Reverts to ""


# This simulates a text editor where each `add_text` operation saves the previous state, and `undo` restores it by popping from the stack.

# ---

# ### **5. Advantages of Stacks**

# - **Simplicity**: Stacks are easy to implement and understand due to their LIFO behavior.
# - **Efficiency**: Push and pop operations are O(1) with a fixed-size array, making them very fast.
# - **Memory Management**: Stacks are memory-efficient for LIFO scenarios, as they don’t require complex pointers or indexing.
# - **Predictable Behavior**: The LIFO principle ensures deterministic access, ideal for specific algorithms like backtracking.

# ---

# ### **6. Disadvantages of Stacks**

# - **Limited Access**: Only the top element is accessible, making stacks unsuitable for random access or searching.
# - **Fixed Capacity (in this implementation)**: A fixed-size stack can overflow if too many elements are pushed.
# - **Not Thread-Safe**: Without synchronization, stacks are not safe for concurrent access in multithreaded applications.
# - **Scalability**: Dynamic resizing (if implemented) can lead to O(n) operations during reallocation, impacting performance.

# ---

# ### **7. Big O Notation**

# The time complexity of stack operations in the above implementation is:

# - **Push**: O(1) – Adding an element to the top is constant time.
# - **Pop**: O(1) – Removing the top element is constant time.
# - **Peek**: O(1) – Viewing the top element is constant time.
# - **Is_empty**: O(1) – Checking if the stack is empty is constant time.
# - **Size**: O(1) – Returning the number of elements is constant time.

# Space complexity:
# - **O(n)**, where `n` is the capacity of the stack (fixed-size array).

# For a dynamic stack (not shown here), resizing the array during a push operation when the stack is full would be O(n) due to copying elements to a new array.

# ---

# ### **8. Using Stacks with Database Connections**

# Stacks can be used with database connections in specific scenarios, but they require careful handling:

# #### **Use Case Example**
# A stack can manage database transactions in a nested transaction system. For example, in a system where transactions can be nested (e.g., PostgreSQL’s `SAVEPOINT`), a stack can track transaction states:


class DatabaseConnection:
    def __init__(self):
        self.transaction_stack = Stack(10)  # Stack to manage transaction savepoints
        self.connection = None  # Simulate a database connection

    def begin_transaction(self, savepoint_name):
        """Start a new transaction and push it to the stack."""
        if self.transaction_stack.is_full():
            raise Exception("Too many nested transactions")
        self.transaction_stack.push(savepoint_name)
        print(f"Began transaction: {savepoint_name}")

    def rollback(self):
        """Rollback to the last transaction savepoint."""
        if self.transaction_stack.is_empty():
            raise Exception("No transaction to rollback")
        savepoint = self.transaction_stack.pop()
        print(f"Rolled back to savepoint: {savepoint}")

# Usage
db = DatabaseConnection()
db.begin_transaction("savepoint1")
db.begin_transaction("savepoint2")
db.rollback()  # Rolls back to savepoint2
db.rollback()  # Rolls back to savepoint1


# #### **Feasibility**
# - **Yes**, stacks can be used with database connections for managing transaction states, connection pooling, or query history.
# - **Challenges**:
#   - **Connection Management**: Database connections are resource-intensive. A stack of connections must ensure proper closure to avoid resource leaks.
#   - **Concurrency**: If multiple threads access the stack, synchronization (e.g., locks) is needed to prevent race conditions.
#   - **Error Handling**: Stack operations must handle database-specific errors (e.g., connection timeouts) gracefully.

# #### **Implementation Notes**
# - Use a stack to store connection states or query logs, but ensure the stack is thread-safe if used in a multi-threaded environment.
# - For large-scale systems, consider connection pooling libraries (e.g., `psycopg2.pool` for PostgreSQL) instead of a custom stack.

# ---

### **9. Security Considerations**

# When using stacks in applications, especially with database connections, consider:

# 1. **Overflow Attacks**: A fixed-size stack can be exploited by pushing excessive elements, causing an overflow. Mitigate by:
#    - Enforcing strict capacity limits.
#    - Validating inputs before pushing.

# 2. **Data Exposure**: If the stack stores sensitive data (e.g., database credentials or query results), ensure:
#    - Data is encrypted or sanitized before storage.
#    - Stack memory is cleared (e.g., set popped elements to `None`) to prevent data leaks.

# 3. **Thread Safety**: In multi-threaded applications, use locks or thread-safe data structures to prevent concurrent modification issues:
   
   import threading

   class ThreadSafeStack(Stack):
       def __init__(self, capacity):
           super().__init__(capacity)
           self.lock = threading.Lock()

       def push(self, item):
           with self.lock:
               super().push(item)

       def pop(self):
           with self.lock:
               return super().pop()
   

# 4. **Database-Specific Security**:
#    - Use parameterized queries to prevent SQL injection when storing queries in a stack.
#    - Ensure database connections are closed properly to avoid resource exhaustion.
#    - Avoid storing sensitive data (e.g., passwords) in the stack.

# ---

# ### **10. Summary**

# - **Implementation**: A stack can be implemented in Python using a fixed-size array, supporting O(1) push, pop, and peek operations.
# - **Applications**: Ideal for LIFO scenarios like function calls, undo/redo, and backtracking.
# - **Limitations**: Not suitable for random access, large datasets, or concurrent access without synchronization.
# -_ASM: **Real-World Example**: Undo feature in a text editor or transaction management in databases.
# - **Advantages**: Simple, efficient, and predictable.
# - **Disadvantages**: Limited access, potential overflow, and not thread-safe by default.
# - **Big O**: O(1) for core operations, O(n) for space.
# - **Database Integration**: Feasible for transaction management or connection pooling, but requires careful resource and concurrency handling.
# - **Security**: Protect against overflows, data leaks, and concurrency issues; use encryption and proper resource cleanup.

# This comprehensive explanation covers the stack’s implementation, use cases, and considerations for real-world applications. Let me know if you’d like further details or a specific aspect explored!

# Stack Data Structure in Python: Complete Guide

## What is a Stack?

# A stack is a **Last In, First Out (LIFO)** linear data structure where elements are added and removed from the same end, called the "top". Think of it like a stack of plates - you can only add or remove plates from the top.

## Core Operations


from typing import Optional, Generic, TypeVar, List

T = TypeVar('T')

class Stack(Generic[T]):
    """
    Thread-safe stack implementation with type hints
    """
    def __init__(self, max_size: Optional[int] = None):
        self._items: List[T] = []
        self._max_size = max_size
        self._lock = threading.Lock()  # For thread safety
    
    def push(self, item: T) -> None:
        """Add item to top of stack - O(1) amortized"""
        with self._lock:
            if self._max_size and len(self._items) >= self._max_size:
                raise OverflowError("Stack overflow")
            self._items.append(item)
    
    def pop(self) -> T:
        """Remove and return top item - O(1)"""
        with self._lock:
            if self.is_empty():
                raise IndexError("Pop from empty stack")
            return self._items.pop()
    
    def peek(self) -> T:
        """Return top item without removing - O(1)"""
        if self.is_empty():
            raise IndexError("Peek from empty stack")
        return self._items[-1]
    
    def is_empty(self) -> bool:
        """Check if stack is empty - O(1)"""
        return len(self._items) == 0
    
    def size(self) -> int:
        """Return number of items - O(1)"""
        return len(self._items)


## Big O Notation Analysis

# | Operation | Time Complexity | Space Complexity |
# |-----------|----------------|------------------|
# | Push      | O(1) amortized* | O(1) |
# | Pop       | O(1) | O(1) |
# | Peek/Top  | O(1) | O(1) |
# | Search    | O(n) | O(1) |
# | Space     | O(n) | O(n) |

# *Amortized because Python lists may need to resize internally

## Real-World Use Cases

### 1. Function Call Stack (Most Critical)

def fibonacci(n: int) -> int:
    """
    Each recursive call creates a new stack frame
    Stack manages return addresses and local variables
    """
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Call stack visualization:
# fibonacci(3) -> calls fibonacci(2) and fibonacci(1)
# fibonacci(2) -> calls fibonacci(1) and fibonacci(0)
# Stack manages all these nested calls


### 2. Expression Evaluation & Parsing

def evaluate_postfix(expression: str) -> int:
    """
    Real-world usage: Calculator apps, compilers
    Example: "3 4 + 2 *" = (3 + 4) * 2 = 14
    """
    stack: Stack[int] = Stack()
    
    for token in expression.split():
        if token.isdigit():
            stack.push(int(token))
        else:
            b = stack.pop()
            a = stack.pop()
            if token == '+':
                stack.push(a + b)
            elif token == '-':
                stack.push(a - b)
            elif token == '*':
                stack.push(a * b)
            elif token == '/':
                stack.push(a // b)
    
    return stack.pop()


### 3. Undo/Redo Operations

class TextEditor:
    """
    Real-world usage: Code editors, document processors
    """
    def __init__(self):
        self.content = ""
        self.undo_stack: Stack[str] = Stack()
        self.redo_stack: Stack[str] = Stack()
    
    def type_text(self, text: str) -> None:
        # Save current state for undo
        self.undo_stack.push(self.content)
        self.content += text
        # Clear redo stack when new action performed
        self.redo_stack = Stack()
    
    def undo(self) -> None:
        if not self.undo_stack.is_empty():
            self.redo_stack.push(self.content)
            self.content = self.undo_stack.pop()
    
    def redo(self) -> None:
        if not self.redo_stack.is_empty():
            self.undo_stack.push(self.content)
            self.content = self.redo_stack.pop()


### 4. Browser History Navigation

class BrowserHistory:
    """
    Real-world usage: Web browsers, navigation systems
    """
    def __init__(self):
        self.back_stack: Stack[str] = Stack()
        self.forward_stack: Stack[str] = Stack()
        self.current_page = "home"
    
    def visit_page(self, url: str) -> None:
        self.back_stack.push(self.current_page)
        self.current_page = url
        self.forward_stack = Stack()  # Clear forward history
    
    def back(self) -> str:
        if not self.back_stack.is_empty():
            self.forward_stack.push(self.current_page)
            self.current_page = self.back_stack.pop()
        return self.current_page
    
    def forward(self) -> str:
        if not self.forward_stack.is_empty():
            self.back_stack.push(self.current_page)
            self.current_page = self.forward_stack.pop()
        return self.current_page


## When to Use Stacks

### ✅ **Perfect Use Cases:**
# - **Parsing & Compilation**: Bracket matching, syntax analysis
# - **Memory Management**: Function call management, local variable storage
# - **Algorithmic Problems**: DFS traversal, backtracking algorithms
# - **User Interface**: Undo/redo functionality, navigation history
# - **Mathematical Operations**: Expression evaluation, calculator logic

### ❌ **Avoid When:**
# - **Random Access Needed**: Use arrays/lists instead
# - **FIFO Required**: Use queues instead
# - **Frequent Middle Element Access**: Use linked lists or arrays
# - **Large Data with Memory Constraints**: Consider disk-based storage

## Database Integration Examples

### 1. PostgreSQL with Connection Pooling

import psycopg2
from psycopg2 import pool
from typing import Optional

class DatabaseConnectionPool:
    """
    Connection pool uses stack-like behavior for connection reuse
    """
    def __init__(self, min_conn: int = 1, max_conn: int = 10):
        self.pool = psycopg2.pool.SimpleConnectionPool(
            min_conn, max_conn,
            host="localhost",
            database="mydb",
            user="user",
            password="password"
        )
        self.connection_stack: Stack[psycopg2.extensions.connection] = Stack()
    
    def get_connection(self) -> psycopg2.extensions.connection:
        """Get connection from pool (stack-like LIFO)"""
        return self.pool.getconn()
    
    def return_connection(self, conn: psycopg2.extensions.connection) -> None:
        """Return connection to pool"""
        self.pool.putconn(conn)

# Usage in Django DRF API
class UserHistoryService:
    """
    Track user actions using stack for recent history
    """
    def __init__(self):
        self.user_actions: Dict[int, Stack[dict]] = {}
    
    def add_action(self, user_id: int, action: dict) -> None:
        if user_id not in self.user_actions:
            self.user_actions[user_id] = Stack(max_size=100)  # Limit history
        
        self.user_actions[user_id].push({
            'action': action,
            'timestamp': timezone.now(),
            'user_id': user_id
        })
    
    def get_recent_actions(self, user_id: int, count: int = 10) -> List[dict]:
        """Get most recent actions (LIFO order)"""
        if user_id not in self.user_actions:
            return []
        
        actions = []
        temp_stack = Stack()
        
        # Pop items to get recent ones
        for _ in range(min(count, self.user_actions[user_id].size())):
            action = self.user_actions[user_id].pop()
            actions.append(action)
            temp_stack.push(action)
        
        # Restore original stack
        while not temp_stack.is_empty():
            self.user_actions[user_id].push(temp_stack.pop())
        
        return actions


### 2. MongoDB with NextJS

# For your NextJS backend API routes
from pymongo import MongoClient
from typing import List, Dict, Any

class MongoStackOperations:
    """
    Using MongoDB for stack-like operations
    """
    def __init__(self, connection_string: str):
        self.client = MongoClient(connection_string)
        self.db = self.client.stack_db
        self.collection = self.db.user_stacks
    
    def push_to_user_stack(self, user_id: str, item: Dict[Any, Any]) -> None:
        """Push item to user's stack in MongoDB"""
        self.collection.update_one(
            {'user_id': user_id},
            {
                '$push': {
                    'stack_items': {
                        'item': item,
                        'timestamp': datetime.utcnow()
                    }
                }
            },
            upsert=True
        )
    
    def pop_from_user_stack(self, user_id: str) -> Optional[Dict[Any, Any]]:
        """Pop item from user's stack in MongoDB"""
        result = self.collection.find_one_and_update(
            {'user_id': user_id},
            {'$pop': {'stack_items': 1}},  # Remove last item (LIFO)
            return_document=pymongo.ReturnDocument.BEFORE
        )
        
        if result and result.get('stack_items'):
            return result['stack_items'][-1]
        return None


## Security Considerations

### 1. Stack Overflow Protection

import sys
from functools import wraps

def stack_overflow_protection(max_depth: int = 1000):
    """
    Decorator to prevent stack overflow in recursive functions
    Critical for web applications to prevent DoS attacks
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(inspect.stack()) > max_depth:
                raise RecursionError("Maximum recursion depth exceeded")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@stack_overflow_protection(max_depth=500)
def recursive_function(n: int) -> int:
    """Protected recursive function"""
    if n <= 1:
        return n
    return recursive_function(n-1) + recursive_function(n-2)


### 2. Input Validation for Stack Operations

import re
from typing import Union

class SecureStack(Stack[str]):
    """
    Security-hardened stack for web applications
    """
    def __init__(self, max_size: int = 1000):
        super().__init__(max_size)
        self.max_item_size = 10000  # Prevent memory exhaustion
    
    def secure_push(self, item: str) -> None:
        """Push with security validations"""
        # Input validation
        if not isinstance(item, str):
            raise ValueError("Only strings allowed")
        
        # Size check to prevent memory attacks
        if len(item) > self.max_item_size:
            raise ValueError("Item too large")
        
        # Sanitize input (example for web content)
        sanitized_item = re.sub(r'<script.*?</script>', '', item, flags=re.DOTALL)
        
        self.push(sanitized_item)
    
    def secure_pop(self) -> str:
        """Pop with logging for security monitoring"""
        if self.is_empty():
            # Log security event
            logger.warning(f"Attempted pop from empty stack at {datetime.now()}")
            raise IndexError("Pop from empty stack")
        
        return self.pop()


## Advantages and Disadvantages

### ✅ **Advantages:**
# - **Simple Implementation**: Easy to understand and implement
# - **Efficient Operations**: O(1) time complexity for basic operations
# - **Memory Efficient**: Only stores necessary data
# - **Natural Recursion Support**: Perfect for recursive algorithms
# - **Undo/Redo Functionality**: Ideal for user interface features

### ❌ **Disadvantages:**
# - **Limited Access**: Only top element accessible
# - **No Random Access**: Cannot access middle elements efficiently
# - **Memory Overhead**: Function call stack can cause stack overflow
# - **Fixed Access Pattern**: LIFO only, not suitable for all use cases
# - **Cache Performance**: May not be cache-friendly for large datasets

## Advanced Stack Implementations

### 1. Thread-Safe Stack for Django Channels

import threading
from channels.generic.websocket import WebsocketConsumer

class WebSocketStackConsumer(WebsocketConsumer):
    """
    Real-time stack operations via WebSocket
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_stack = Stack()
        self.lock = threading.Lock()
    
    def receive(self, text_data: str) -> None:
        import json
        data = json.loads(text_data)
        
        with self.lock:
            if data['action'] == 'push':
                self.user_stack.push(data['item'])
                self.send_stack_update()
            elif data['action'] == 'pop':
                if not self.user_stack.is_empty():
                    item = self.user_stack.pop()
                    self.send_stack_update()
    
    def send_stack_update(self) -> None:
        """Send current stack state to client"""
        self.send(text_data=json.dumps({
            'stack_size': self.user_stack.size(),
            'top_item': self.user_stack.peek() if not self.user_stack.is_empty() else None
        }))


### 2. Persistent Stack with Redis

import redis
import json
from typing import Any

class RedisStack:
    """
    Distributed stack using Redis for scalability
    Perfect for microservices architecture
    """
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "stack"):
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    def push(self, stack_id: str, item: Any) -> None:
        """Push item to Redis-backed stack"""
        key = f"{self.key_prefix}:{stack_id}"
        self.redis.lpush(key, json.dumps(item))
    
    def pop(self, stack_id: str) -> Any:
        """Pop item from Redis-backed stack"""
        key = f"{self.key_prefix}:{stack_id}"
        result = self.redis.lpop(key)
        return json.loads(result) if result else None
    
    def peek(self, stack_id: str) -> Any:
        """Peek at top item"""
        key = f"{self.key_prefix}:{stack_id}"
        result = self.redis.lindex(key, 0)
        return json.loads(result) if result else None


# This comprehensive guide covers stack implementation with your preferred tech stack, emphasizing security, real-world applications, and database integration patterns you'll encounter in production Django REST API and NextJS applications.

# Stack Interview Questions & Answers: Easy to Hard

## 🟢 Easy Level

### Q1: Implement a basic stack using Python list
# **Expected Answer:**

class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        if self.is_empty():
            raise IndexError("Pop from empty stack")
        return self.items.pop()
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Peek from empty stack")
        return self.items[-1]
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)


### Q2: Check if parentheses are balanced in a string
**Example:** `"((()))"` → True, `"(()"` → False


def is_balanced_parentheses(s: str) -> bool:
    """
    Time: O(n), Space: O(n)
    Real-world usage: Code editors, compilers
    """
    stack = []
    
    for char in s:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return False
            stack.pop()
    
    return len(stack) == 0

# Test cases
print(is_balanced_parentheses("((()))"))  # True
print(is_balanced_parentheses("(()"))     # False
print(is_balanced_parentheses(""))        # True


### Q3: Reverse a string using stack

def reverse_string(s: str) -> str:
    """
    Time: O(n), Space: O(n)
    """
    stack = []
    
    # Push all characters to stack
    for char in s:
        stack.append(char)
    
    # Pop all characters to get reverse
    result = ""
    while stack:
        result += stack.pop()
    
    return result

# More Pythonic approach
def reverse_string_pythonic(s: str) -> str:
    return s[::-1]  # O(n) time, O(n) space


---

## 🟡 Medium Level

### Q4: Valid parentheses with multiple bracket types
**Example:** `"()[]{}"` → True, `"([)]"` → False


def is_valid_parentheses(s: str) -> bool:
    """
    LeetCode #20 - Valid Parentheses
    Time: O(n), Space: O(n)
    """
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    
    for char in s:
        if char in mapping:  # Closing bracket
            if not stack or stack.pop() != mapping[char]:
                return False
        else:  # Opening bracket
            stack.append(char)
    
    return len(stack) == 0

# Test cases
print(is_valid_parentheses("()[]{}"))  # True
print(is_valid_parentheses("([)]"))    # False
print(is_valid_parentheses("{[]}"))    # True


### Q5: Implement stack using two queues

from collections import deque

class StackUsingQueues:
    """
    Real-world: Understanding data structure relationships
    Push: O(n), Pop: O(1), Peek: O(1)
    """
    def __init__(self):
        self.q1 = deque()
        self.q2 = deque()
    
    def push(self, x: int) -> None:
        # Add to q2, then move all q1 elements to q2
        self.q2.append(x)
        while self.q1:
            self.q2.append(self.q1.popleft())
        
        # Swap queues
        self.q1, self.q2 = self.q2, self.q1
    
    def pop(self) -> int:
        if not self.q1:
            raise IndexError("Pop from empty stack")
        return self.q1.popleft()
    
    def top(self) -> int:
        if not self.q1:
            raise IndexError("Top from empty stack")
        return self.q1[0]
    
    def empty(self) -> bool:
        return len(self.q1) == 0


### Q6: Evaluate Reverse Polish Notation (RPN)
# **Example:** `["2", "1", "+", "3", "*"]` → `((2 + 1) * 3) = 9`


def eval_rpn(tokens: List[str]) -> int:
    """
    LeetCode #150 - Evaluate Reverse Polish Notation
    Time: O(n), Space: O(n)
    Real-world: Calculator apps, compiler expression evaluation
    """
    stack = []
    operators = {'+', '-', '*', '/'}
    
    for token in tokens:
        if token in operators:
            # Pop two operands (order matters for - and /)
            b = stack.pop()
            a = stack.pop()
            
            if token == '+':
                result = a + b
            elif token == '-':
                result = a - b
            elif token == '*':
                result = a * b
            elif token == '/':
                # Python3 division truncates towards zero
                result = int(a / b)
            
            stack.append(result)
        else:
            stack.append(int(token))
    
    return stack[0]

# Test
print(eval_rpn(["2", "1", "+", "3", "*"]))  # 9
print(eval_rpn(["4", "13", "5", "/", "+"]))  # 6


### Q7: Next Greater Element
# **Example:** `[2, 1, 2, 4, 3, 1]` → `[4, 2, 4, -1, -1, -1]`


def next_greater_element(nums: List[int]) -> List[int]:
    """
    Time: O(n), Space: O(n)
    Real-world: Stock price analysis, temperature monitoring
    """
    stack = []
    result = [-1] * len(nums)
    
    for i in range(len(nums)):
        # While stack is not empty and current element is greater
        # than element at stack top index
        while stack and nums[i] > nums[stack[-1]]:
            index = stack.pop()
            result[index] = nums[i]
        
        stack.append(i)
    
    return result

# Test
print(next_greater_element([2, 1, 2, 4, 3, 1]))  # [4, 2, 4, -1, -1, -1]


---

## 🔴 Hard Level

### Q8: Implement Min Stack (O(1) operations)
# **Requirements:** Push, pop, top, and getMin all in O(1) time


class MinStack:
    """
    LeetCode #155 - Min Stack
    All operations: O(1) time, O(n) space
    Real-world: Database query optimization, algorithm optimization
    """
    def __init__(self):
        self.stack = []
        self.min_stack = []  # Stores minimum values
    
    def push(self, val: int) -> None:
        self.stack.append(val)
        
        # Update min_stack
        if not self.min_stack or val <= self.min_stack[-1]:
            self.min_stack.append(val)
    
    def pop(self) -> None:
        if not self.stack:
            return
        
        val = self.stack.pop()
        
        # If popped value was minimum, remove from min_stack
        if val == self.min_stack[-1]:
            self.min_stack.pop()
    
    def top(self) -> int:
        return self.stack[-1]
    
    def getMin(self) -> int:
        return self.min_stack[-1]

# Alternative space-optimized approach
class MinStackOptimized:
    """
    Space optimization: Store differences from minimum
    """
    def __init__(self):
        self.stack = []
        self.min_val = None
    
    def push(self, val: int) -> None:
        if not self.stack:
            self.stack.append(0)
            self.min_val = val
        else:
            # Store difference from current minimum
            diff = val - self.min_val
            self.stack.append(diff)
            
            # Update minimum if current value is smaller
            if val < self.min_val:
                self.min_val = val
    
    def pop(self) -> None:
        if not self.stack:
            return
        
        diff = self.stack.pop()
        
        # If difference is negative, we're popping the minimum
        if diff < 0:
            self.min_val = self.min_val - diff
    
    def top(self) -> int:
        diff = self.stack[-1]
        if diff < 0:
            return self.min_val
        return self.min_val + diff
    
    def getMin(self) -> int:
        return self.min_val


# ### Q9: Largest Rectangle in Histogram
# **Example:** `[2,1,5,6,2,3]` → `10` (rectangle with height 5 and width 2)


def largest_rectangle_area(heights: List[int]) -> int:
    """
    LeetCode #84 - Largest Rectangle in Histogram
    Time: O(n), Space: O(n)
    Real-world: Computer graphics, image processing, architecture
    """
    stack = []
    max_area = 0
    
    for i, height in enumerate(heights):
        # While current height is less than stack top height
        while stack and heights[stack[-1]] > height:
            h = heights[stack.pop()]
            # Width calculation: current index - previous stack top - 1
            w = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, h * w)
        
        stack.append(i)
    
    # Process remaining elements in stack
    while stack:
        h = heights[stack.pop()]
        w = len(heights) if not stack else len(heights) - stack[-1] - 1
        max_area = max(max_area, h * w)
    
    return max_area

# Test
print(largest_rectangle_area([2,1,5,6,2,3]))  # 10


# ### Q10: Basic Calculator (with +, -, *, /)
# **Example:** `"3+2*2"` → `7`, `" 3/2 "` → `1`


def calculate(s: str) -> int:
    """
    LeetCode #227 - Basic Calculator II
    Time: O(n), Space: O(n)
    Real-world: Compiler design, expression evaluators
    """
    stack = []
    num = 0
    operator = '+'
    
    for i, char in enumerate(s):
        if char.isdigit():
            num = num * 10 + int(char)
        
        # If operator or last character
        if char in '+-*/' or i == len(s) - 1:
            if operator == '+':
                stack.append(num)
            elif operator == '-':
                stack.append(-num)
            elif operator == '*':
                stack.append(stack.pop() * num)
            elif operator == '/':
                # Handle negative division for Python
                prev = stack.pop()
                stack.append(int(prev / num))
            
            operator = char
            num = 0
    
    return sum(stack)

# Test
print(calculate("3+2*2"))    # 7
print(calculate(" 3/2 "))    # 1
print(calculate(" 3+5 / 2 "))  # 5


### Q11: Trapping Rain Water
# **Example:** `[0,1,0,2,1,0,1,3,2,1,2,1]` → `6` units of water


def trap_rainwater(height: List[int]) -> int:
    """
    LeetCode #42 - Trapping Rain Water
    Time: O(n), Space: O(n)
    Real-world: Civil engineering, flood modeling
    """
    stack = []
    water = 0
    
    for i, h in enumerate(height):
        # While current height is greater than stack top height
        while stack and height[stack[-1]] < h:
            top = stack.pop()
            
            if not stack:
                break
            
            # Calculate trapped water
            distance = i - stack[-1] - 1
            bounded_height = min(h, height[stack[-1]]) - height[top]
            water += distance * bounded_height
        
        stack.append(i)
    
    return water

# Two-pointer approach (more space efficient)
def trap_rainwater_optimized(height: List[int]) -> int:
    """
    Time: O(n), Space: O(1)
    """
    left, right = 0, len(height) - 1
    left_max, right_max = 0, 0
    water = 0
    
    while left < right:
        if height[left] < height[right]:
            if height[left] >= left_max:
                left_max = height[left]
            else:
                water += left_max - height[left]
            left += 1
        else:
            if height[right] >= right_max:
                right_max = height[right]
            else:
                water += right_max - height[right]
            right -= 1
    
    return water


---

## 🔥 Expert Level (System Design)

### Q12: Design a Stack with Middleware Support
# **Requirements:** Support for logging, authentication, rate limiting


from abc import ABC, abstractmethod
from typing import Any, List, Optional
import time
import functools
from threading import Lock

class StackMiddleware(ABC):
    """Abstract base class for stack middleware"""
    
    @abstractmethod
    def before_push(self, item: Any, stack_id: str) -> bool:
        """Return True to continue, False to abort"""
        pass
    
    @abstractmethod
    def after_push(self, item: Any, stack_id: str) -> None:
        pass
    
    @abstractmethod
    def before_pop(self, stack_id: str) -> bool:
        pass
    
    @abstractmethod
    def after_pop(self, item: Any, stack_id: str) -> None:
        pass

class LoggingMiddleware(StackMiddleware):
    """Middleware for logging stack operations"""
    
    def before_push(self, item: Any, stack_id: str) -> bool:
        print(f"[LOG] Pushing {item} to stack {stack_id}")
        return True
    
    def after_push(self, item: Any, stack_id: str) -> None:
        print(f"[LOG] Successfully pushed {item} to stack {stack_id}")
    
    def before_pop(self, stack_id: str) -> bool:
        print(f"[LOG] Popping from stack {stack_id}")
        return True
    
    def after_pop(self, item: Any, stack_id: str) -> None:
        print(f"[LOG] Successfully popped {item} from stack {stack_id}")

class RateLimitMiddleware(StackMiddleware):
    """Middleware for rate limiting stack operations"""
    
    def __init__(self, max_operations_per_second: int = 10):
        self.max_ops = max_operations_per_second
        self.operations = {}
        self.lock = Lock()
    
    def _check_rate_limit(self, stack_id: str) -> bool:
        current_time = time.time()
        
        with self.lock:
            if stack_id not in self.operations:
                self.operations[stack_id] = []
            
            # Remove old operations (outside 1-second window)
            self.operations[stack_id] = [
                op_time for op_time in self.operations[stack_id]
                if current_time - op_time < 1.0
            ]
            
            if len(self.operations[stack_id]) >= self.max_ops:
                return False
            
            self.operations[stack_id].append(current_time)
            return True
    
    def before_push(self, item: Any, stack_id: str) -> bool:
        return self._check_rate_limit(stack_id)
    
    def after_push(self, item: Any, stack_id: str) -> None:
        pass
    
    def before_pop(self, stack_id: str) -> bool:
        return self._check_rate_limit(stack_id)
    
    def after_pop(self, item: Any, stack_id: str) -> None:
        pass

class EnterpriseStack:
    """
    Production-ready stack with middleware support
    Real-world usage: Microservices, enterprise applications
    """
    
    def __init__(self, stack_id: str, middlewares: List[StackMiddleware] = None):
        self.stack_id = stack_id
        self.items = []
        self.middlewares = middlewares or []
        self.lock = Lock()
    
    def push(self, item: Any) -> bool:
        """Push with middleware support"""
        with self.lock:
            # Execute before_push middleware
            for middleware in self.middlewares:
                if not middleware.before_push(item, self.stack_id):
                    return False
            
            # Actual push operation
            self.items.append(item)
            
            # Execute after_push middleware
            for middleware in self.middlewares:
                middleware.after_push(item, self.stack_id)
            
            return True
    
    def pop(self) -> Optional[Any]:
        """Pop with middleware support"""
        with self.lock:
            if not self.items:
                return None
            
            # Execute before_pop middleware
            for middleware in self.middlewares:
                if not middleware.before_pop(self.stack_id):
                    return None
            
            # Actual pop operation
            item = self.items.pop()
            
            # Execute after_pop middleware
            for middleware in self.middlewares:
                middleware.after_pop(item, self.stack_id)
            
            return item

# Usage example
middlewares = [
    LoggingMiddleware(),
    RateLimitMiddleware(max_operations_per_second=5)
]

stack = EnterpriseStack("user_123", middlewares)


### Q13: Distributed Stack Implementation
# **Requirements:** Scalable across multiple servers, fault-tolerant


import redis
import json
import hashlib
from typing import List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class StackOperation(Enum):
    PUSH = "push"
    POP = "pop"
    PEEK = "peek"

@dataclass
class StackNode:
    """Node in distributed stack"""
    server_id: str
    is_active: bool
    last_heartbeat: float

class DistributedStack:
    """
    Distributed stack implementation for microservices
    Real-world: Cloud applications, distributed systems
    """
    
    def __init__(self, stack_id: str, redis_nodes: List[str]):
        self.stack_id = stack_id
        self.redis_connections = {}
        self.consistent_hash_ring = {}
        
        # Initialize Redis connections
        for node in redis_nodes:
            self.redis_connections[node] = redis.Redis.from_url(node)
        
        # Build consistent hash ring
        self._build_hash_ring()
    
    def _build_hash_ring(self):
        """Build consistent hash ring for load distribution"""
        for node in self.redis_connections.keys():
            for i in range(100):  # 100 virtual nodes per physical node
                virtual_node = f"{node}:{i}"
                hash_value = int(hashlib.md5(virtual_node.encode()).hexdigest(), 16)
                self.consistent_hash_ring[hash_value] = node
    
    def _get_node_for_operation(self, operation: StackOperation) -> str:
        """Get Redis node for operation using consistent hashing"""
        operation_hash = int(hashlib.md5(
            f"{self.stack_id}:{operation.value}".encode()
        ).hexdigest(), 16)
        
        # Find next node in hash ring
        for hash_value in sorted(self.consistent_hash_ring.keys()):
            if hash_value >= operation_hash:
                return self.consistent_hash_ring[hash_value]
        
        # Wrap around to first node
        return self.consistent_hash_ring[min(self.consistent_hash_ring.keys())]
    
    def push(self, item: Any) -> bool:
        """Distributed push operation"""
        try:
            node = self._get_node_for_operation(StackOperation.PUSH)
            redis_client = self.redis_connections[node]
            
            # Use Redis list as stack (LPUSH for stack behavior)
            result = redis_client.lpush(self.stack_id, json.dumps(item))
            
            # Replicate to backup nodes for fault tolerance
            backup_nodes = self._get_backup_nodes(node)
            for backup in backup_nodes:
                backup_client = self.redis_connections[backup]
                backup_client.lpush(f"{self.stack_id}:backup", json.dumps(item))
            
            return result > 0
            
        except Exception as e:
            print(f"Push failed: {e}")
            return False
    
    def pop(self) -> Optional[Any]:
        """Distributed pop operation"""
        try:
            node = self._get_node_for_operation(StackOperation.POP)
            redis_client = self.redis_connections[node]
            
            # Use LPOP for stack behavior
            result = redis_client.lpop(self.stack_id)
            
            if result:
                # Remove from backup nodes
                backup_nodes = self._get_backup_nodes(node)
                for backup in backup_nodes:
                    backup_client = self.redis_connections[backup]
                    backup_client.lpop(f"{self.stack_id}:backup")
                
                return json.loads(result)
            
            return None
            
        except Exception as e:
            print(f"Pop failed: {e}")
            return None
    
    def _get_backup_nodes(self, primary_node: str) -> List[str]:
        """Get backup nodes for replication"""
        all_nodes = list(self.redis_connections.keys())
        all_nodes.remove(primary_node)
        return all_nodes[:2]  # Use 2 backup nodes
    
    def health_check(self) -> dict:
        """Check health of all nodes"""
        health_status = {}
        
        for node, client in self.redis_connections.items():
            try:
                response = client.ping()
                health_status[node] = "healthy" if response else "unhealthy"
            except Exception as e:
                health_status[node] = f"error: {e}"
        
        return health_status


## 🎯 Key Interview Tips

### **For Junior Level:**
# - Focus on basic operations and time complexity
# - Understand LIFO principle clearly
# - Practice simple applications like balanced parentheses

# ### **For Mid Level:**
# - Master advanced applications (calculator, histogram problems)
# - Understand when to use stack vs other data structures
# - Know multiple implementation approaches

# ### **For Senior Level:**
# - Design scalable, production-ready solutions
# - Consider security, monitoring, and fault tolerance
# - Understand distributed systems implications

# ### **Common Follow-up Questions:**
# 1. "How would you handle stack overflow in production?"
# 2. "What's the difference between stack and recursion?"
# 3. "How would you implement undo/redo in a collaborative editor?"
# 4. "Design a stack that supports push, pop, and getMin in O(1)?"

# These questions progress from basic implementation to complex system design, covering real-world scenarios you'll encounter in your Django REST API and NextJS development work.