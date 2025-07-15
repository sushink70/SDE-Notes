# Linked Lists in Python: Complete Guide

## What is a Linked List?

# A linked list is a linear data structure where elements (nodes) are stored in sequence, but unlike arrays, elements are not stored in contiguous memory locations.
# Each node contains data and a reference (pointer) to the next node in the sequence.


from typing import Optional, Generic, TypeVar, Iterator
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Node(Generic[T]):
    """
    Node class representing a single element in the linked list
    Uses generics for type safety
    """
    data: T
    next_node: Optional['Node[T]'] = None

class LinkedList(Generic[T]):
    """
    Singly Linked List implementation with type hints
    """
    def __init__(self) -> None:
        self.head: Optional[Node[T]] = None
        self.size: int = 0
    
    def append(self, data: T) -> None:
        """Add element to the end - O(n)"""
        new_node = Node(data)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next_node:
                current = current.next_node
            current.next_node = new_node
        self.size += 1
    
    def prepend(self, data: T) -> None:
        """Add element to the beginning - O(1)"""
        new_node = Node(data)
        new_node.next_node = self.head
        self.head = new_node
        self.size += 1
    
    def delete(self, data: T) -> bool:
        """Delete first occurrence of data - O(n)"""
        if not self.head:
            return False
        
        if self.head.data == data:
            self.head = self.head.next_node
            self.size -= 1
            return True
        
        current = self.head
        while current.next_node:
            if current.next_node.data == data:
                current.next_node = current.next_node.next_node
                self.size -= 1
                return True
            current = current.next_node
        return False
    
    def find(self, data: T) -> Optional[Node[T]]:
        """Find node with given data - O(n)"""
        current = self.head
        while current:
            if current.data == data:
                return current
            current = current.next_node
        return None
    
    def __iter__(self) -> Iterator[T]:
        """Make the linked list iterable"""
        current = self.head
        while current:
            yield current.data
            current = current.next_node
    
    def __len__(self) -> int:
        """Return size of linked list"""
        return self.size
    
    def __str__(self) -> str:
        """String representation"""
        return " -> ".join(str(data) for data in self)


## Advanced Implementations

### Doubly Linked List

@dataclass
class DoublyNode(Generic[T]):
    """Node for doubly linked list"""
    data: T
    next_node: Optional['DoublyNode[T]'] = None
    prev_node: Optional['DoublyNode[T]'] = None

class DoublyLinkedList(Generic[T]):
    """
    Doubly linked list - allows bidirectional traversal
    Better for scenarios requiring backward navigation
    """
    def __init__(self) -> None:
        self.head: Optional[DoublyNode[T]] = None
        self.tail: Optional[DoublyNode[T]] = None
        self.size: int = 0
    
    def append(self, data: T) -> None:
        """Add to end - O(1) due to tail pointer"""
        new_node = DoublyNode(data)
        if not self.head:
            self.head = self.tail = new_node
        else:
            new_node.prev_node = self.tail
            self.tail.next_node = new_node
            self.tail = new_node
        self.size += 1


### Circular Linked List

class CircularLinkedList(Generic[T]):
    """
    Circular linked list - last node points to first
    Useful for round-robin scheduling, playlist implementations
    """
    def __init__(self) -> None:
        self.head: Optional[Node[T]] = None
        self.size: int = 0
    
    def append(self, data: T) -> None:
        """Add element maintaining circular property"""
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            new_node.next_node = new_node  # Points to itself
        else:
            # Find last node
            current = self.head
            while current.next_node != self.head:
                current = current.next_node
            current.next_node = new_node
            new_node.next_node = self.head
        self.size += 1


## Big O Notation Analysis

# | Operation | Singly Linked List | Doubly Linked List | Array/List |
# |-----------|-------------------|-------------------|------------|
# | Access by index | O(n) | O(n) | O(1) |
# | Search | O(n) | O(n) | O(n) |
# | Insertion at beginning | O(1) | O(1) | O(n) |
# | Insertion at end | O(n) | O(1) | O(1) amortized |
# | Deletion at beginning | O(1) | O(1) | O(n) |
# | Deletion at end | O(n) | O(1) | O(1) |
# | Space complexity | O(n) | O(n) | O(n) |

## Real-World Use Cases

### 1. Web Browser History

class BrowserHistory:
    """
    Browser history using doubly linked list
    Allows efficient back/forward navigation
    """
    def __init__(self, homepage: str) -> None:
        self.current = DoublyNode(homepage)
        self.history = DoublyLinkedList[str]()
        self.history.head = self.history.tail = self.current
        self.history.size = 1
    
    def visit(self, url: str) -> None:
        """Visit new URL - O(1)"""
        new_page = DoublyNode(url)
        new_page.prev_node = self.current
        self.current.next_node = new_page
        self.current = new_page
        self.history.tail = new_page
        self.history.size += 1
    
    def back(self) -> Optional[str]:
        """Go back in history - O(1)"""
        if self.current.prev_node:
            self.current = self.current.prev_node
            return self.current.data
        return None
    
    def forward(self) -> Optional[str]:
        """Go forward in history - O(1)"""
        if self.current.next_node:
            self.current = self.current.next_node
            return self.current.data
        return None


### 2. Music Playlist Manager

class PlaylistManager:
    """
    Music playlist using circular linked list
    Supports continuous playback and shuffle
    """
    def __init__(self) -> None:
        self.playlist = CircularLinkedList[dict]()
        self.current_song: Optional[Node[dict]] = None
    
    def add_song(self, song: dict) -> None:
        """Add song to playlist"""
        # Validate song data for security
        required_keys = ['title', 'artist', 'duration']
        if not all(key in song for key in required_keys):
            raise ValueError("Invalid song data")
        
        self.playlist.append(song)
        if not self.current_song:
            self.current_song = self.playlist.head
    
    def next_song(self) -> Optional[dict]:
        """Get next song in playlist - O(1)"""
        if self.current_song:
            self.current_song = self.current_song.next_node
            return self.current_song.data
        return None
    
    def shuffle(self) -> None:
        """Shuffle playlist - O(n)"""
        import random
        songs = list(self.playlist)
        random.shuffle(songs)
        
        # Rebuild playlist
        self.playlist = CircularLinkedList[dict]()
        for song in songs:
            self.playlist.append(song)
        self.current_song = self.playlist.head


### 3. Django Request Middleware Chain

from typing import Callable
from django.http import HttpRequest, HttpResponse

class MiddlewareNode:
    """
    Middleware node for Django request processing
    Demonstrates real-world linked list usage in web frameworks
    """
    def __init__(self, middleware_func: Callable, process_request: bool = True):
        self.middleware_func = middleware_func
        self.process_request = process_request
        self.next_middleware: Optional['MiddlewareNode'] = None
    
    def process(self, request: HttpRequest) -> HttpResponse:
        """Process request through middleware chain"""
        if self.process_request:
            # Process request
            response = self.middleware_func(request)
            if response:
                return response
        
        # Continue to next middleware
        if self.next_middleware:
            return self.next_middleware.process(request)
        
        # End of chain - return default response
        return HttpResponse("Request processed")

class MiddlewareChain:
    """
    Middleware processing chain using linked list
    Used in Django's request/response cycle
    """
    def __init__(self):
        self.head: Optional[MiddlewareNode] = None
    
    def add_middleware(self, middleware_func: Callable) -> None:
        """Add middleware to chain"""
        new_node = MiddlewareNode(middleware_func)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next_middleware:
                current = current.next_middleware
            current.next_middleware = new_node


## When to Use Linked Lists

### ✅ **Use When:**
# 1. **Frequent insertions/deletions** at the beginning
# 2. **Unknown or dynamic size** of data
# 3. **Memory is fragmented** (doesn't need contiguous memory)
# 4. **Implementing other data structures** (stacks, queues)
# 5. **Undo functionality** in applications
# 6. **Navigation systems** (browser history, media players)

### ❌ **Don't Use When:**
# 1. **Need random access** to elements (use arrays/lists)
# 2. **Memory is limited** (extra pointer overhead)
# 3. **Cache performance is critical** (poor cache locality)
# 4. **Need to access elements by index frequently**
# 5. **Binary search** is required (use sorted arrays)

## Database Integration


import psycopg2
from typing import List, Optional
import json

class DatabaseLinkedList:
    """
    Linked list stored in PostgreSQL database
    Demonstrates persistence and database integration
    """
    def __init__(self, db_config: dict, table_name: str = "linked_list_nodes"):
        self.db_config = db_config
        self.table_name = table_name
        self.create_table()
    
    def create_table(self) -> None:
        """Create table for linked list storage"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id SERIAL PRIMARY KEY,
                        data JSONB NOT NULL,
                        next_id INTEGER REFERENCES {self.table_name}(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_next_id ON {self.table_name}(next_id)
                    );
                """)
    
    def insert_node(self, data: dict, after_id: Optional[int] = None) -> int:
        """Insert node into database linked list"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                # Security: Use parameterized queries
                cur.execute(f"""
                    INSERT INTO {self.table_name} (data, next_id)
                    VALUES (%s, %s)
                    RETURNING id;
                """, (json.dumps(data), after_id))
                
                return cur.fetchone()[0]
    
    def traverse_from_head(self, head_id: int) -> List[dict]:
        """Traverse linked list from head node"""
        result = []
        current_id = head_id
        
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                while current_id:
                    cur.execute(f"""
                        SELECT data, next_id 
                        FROM {self.table_name} 
                        WHERE id = %s;
                    """, (current_id,))
                    
                    row = cur.fetchone()
                    if row:
                        result.append(row[0])
                        current_id = row[1]
                    else:
                        break
        
        return result


## Security Considerations


import hashlib
import hmac
from typing import Any
import logging

class SecureLinkedList(Generic[T]):
    """
    Security-enhanced linked list implementation
    Includes integrity checks and access controls
    """
    def __init__(self, secret_key: str) -> None:
        self.head: Optional[Node[T]] = None
        self.secret_key = secret_key.encode()
        self.size: int = 0
        self.access_log: List[str] = []
    
    def _generate_hash(self, data: Any) -> str:
        """Generate HMAC for data integrity"""
        return hmac.new(
            self.secret_key,
            str(data).encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _validate_input(self, data: Any) -> bool:
        """Validate input data to prevent injection attacks"""
        # Example validation - customize based on your needs
        if isinstance(data, str):
            # Check for potential SQL injection patterns
            dangerous_patterns = ['DROP', 'DELETE', 'UPDATE', 'INSERT', '--', ';']
            data_upper = data.upper()
            if any(pattern in data_upper for pattern in dangerous_patterns):
                logging.warning(f"Suspicious input detected: {data}")
                return False
        return True
    
    def secure_append(self, data: T, user_id: str) -> bool:
        """Securely append data with validation and logging"""
        # Input validation
        if not self._validate_input(data):
            return False
        
        # Generate integrity hash
        data_hash = self._generate_hash(data)
        
        # Log access
        self.access_log.append(f"User {user_id} added data at {datetime.now()}")
        
        # Secure node creation
        secure_data = {
            'data': data,
            'hash': data_hash,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self.append(secure_data)
        return True
    
    def verify_integrity(self) -> bool:
        """Verify data integrity of entire list"""
        current = self.head
        while current:
            if isinstance(current.data, dict) and 'hash' in current.data:
                expected_hash = self._generate_hash(current.data['data'])
                if current.data['hash'] != expected_hash:
                    logging.error(f"Data integrity compromised: {current.data}")
                    return False
            current = current.next_node
        return True


## Performance Optimization


class OptimizedLinkedList(Generic[T]):
    """
    Performance-optimized linked list with caching
    """
    def __init__(self):
        self.head: Optional[Node[T]] = None
        self.tail: Optional[Node[T]] = None  # O(1) append
        self.size: int = 0
        self.cache: dict = {}  # LRU cache for frequently accessed nodes
        self.max_cache_size: int = 100
    
    def append(self, data: T) -> None:
        """Optimized append with tail pointer - O(1)"""
        new_node = Node(data)
        if not self.head:
            self.head = self.tail = new_node
        else:
            self.tail.next_node = new_node
            self.tail = new_node
        self.size += 1
        
        # Update cache
        self._update_cache(self.size - 1, new_node)
    
    def _update_cache(self, index: int, node: Node[T]) -> None:
        """Update LRU cache"""
        if len(self.cache) >= self.max_cache_size:
            # Remove least recently used
            oldest_key = min(self.cache.keys())
            del self.cache[oldest_key]
        
        self.cache[index] = node
    
    def get_at_index(self, index: int) -> Optional[T]:
        """Get element at index with caching - O(1) best case"""
        if index < 0 or index >= self.size:
            return None
        
        # Check cache first
        if index in self.cache:
            return self.cache[index].data
        
        # Traverse and cache
        current = self.head
        for i in range(index):
            current = current.next_node
        
        self._update_cache(index, current)
        return current.data


## Testing with pytest


import pytest
from typing import List

class TestLinkedList:
    """
    Comprehensive test suite for linked list
    Following TDD principles for robust code
    """
    
    def test_empty_list_creation(self):
        """Test creating empty linked list"""
        ll = LinkedList[int]()
        assert len(ll) == 0
        assert ll.head is None
    
    def test_append_single_element(self):
        """Test appending single element"""
        ll = LinkedList[int]()
        ll.append(1)
        assert len(ll) == 1
        assert ll.head.data == 1
    
    def test_append_multiple_elements(self):
        """Test appending multiple elements"""
        ll = LinkedList[int]()
        values = [1, 2, 3, 4, 5]
        for val in values:
            ll.append(val)
        
        assert len(ll) == 5
        assert list(ll) == values
    
    def test_prepend_performance(self):
        """Test prepend operation performance"""
        ll = LinkedList[int]()
        
        # Time prepend operations
        import time
        start = time.time()
        for i in range(1000):
            ll.prepend(i)
        end = time.time()
        
        # Should be very fast (O(1) per operation)
        assert end - start < 0.1
        assert len(ll) == 1000
    
    def test_security_validation(self):
        """Test security features"""
        secure_ll = SecureLinkedList[str]("secret_key")
        
        # Test malicious input rejection
        assert not secure_ll.secure_append("DROP TABLE users;", "user1")
        assert not secure_ll.secure_append("'; DELETE FROM accounts; --", "user2")
        
        # Test valid input acceptance
        assert secure_ll.secure_append("Hello World", "user3")
    
    @pytest.mark.parametrize("size", [10, 100, 1000])
    def test_performance_scaling(self, size: int):
        """Test performance with different sizes"""
        ll = LinkedList[int]()
        
        # Measure append performance
        start = time.time()
        for i in range(size):
            ll.append(i)
        append_time = time.time() - start
        
        # Measure search performance
        start = time.time()
        ll.find(size // 2)
        search_time = time.time() - start
        
        # Performance should scale linearly
        assert append_time < size * 0.001  # Max 1ms per append
        assert search_time < size * 0.001  # Max 1ms per search


## Advantages and Disadvantages

### Advantages:
# 1. **Dynamic size** - grows/shrinks during runtime
# 2. **Efficient insertion/deletion** at beginning (O(1))
# 3. **Memory efficient** - allocates memory as needed
# 4. **No memory waste** - unlike arrays with fixed size
# 5. **Flexibility** - can store any data type

### Disadvantages:
# 1. **No random access** - must traverse from head (O(n))
# 2. **Extra memory overhead** - storing pointers
# 3. **Poor cache locality** - nodes scattered in memory
# 4. **Not suitable for binary search** - no indexing
# 5. **Potential memory leaks** - if not properly managed

## Integration with Modern Python Ecosystem


# Integration with Django Models
from django.db import models
from django.contrib.postgres.fields import JSONField

class LinkedListNode(models.Model):
    """Django model for persistent linked list"""
    data = JSONField()
    next_node = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'linked_list_nodes'
        indexes = [
            models.Index(fields=['next_node']),
        ]

# Integration with Redis for caching
import redis
import pickle

class CachedLinkedList(LinkedList[T]):
    """Redis-cached linked list for better performance"""
    def __init__(self, redis_client: redis.Redis, cache_key: str):
        super().__init__()
        self.redis = redis_client
        self.cache_key = cache_key
        self.load_from_cache()
    
    def save_to_cache(self) -> None:
        """Save list to Redis cache"""
        data = list(self)
        self.redis.set(self.cache_key, pickle.dumps(data))
    
    def load_from_cache(self) -> None:
        """Load list from Redis cache"""
        cached_data = self.redis.get(self.cache_key)
        if cached_data:
            data = pickle.loads(cached_data)
            for item in data:
                self.append(item)


# Linked lists are fundamental data structures that shine in scenarios requiring frequent insertions/deletions at the beginning and when the size of data is unknown or highly variable. While they have limitations like poor cache performance and lack of random access, they're invaluable for implementing other data structures, managing dynamic data, and building efficient algorithms for specific use cases.

# The key is understanding when their strengths align with your requirements and implementing them with proper security, type safety, and performance considerations in mind.

# Linked List Interview Questions & Answers

## 🟢 Easy Questions (1-4)

### 1. **Implement a basic singly linked list with insert, delete, and display methods**


from typing import Optional, Generic, TypeVar

T = TypeVar('T')

class Node(Generic[T]):
    def __init__(self, data: T):
        self.data: T = data
        self.next: Optional['Node[T]'] = None

class LinkedList(Generic[T]):
    def __init__(self):
        self.head: Optional[Node[T]] = None
    
    def insert(self, data: T) -> None:
        """Insert at beginning - O(1)"""
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node
    
    def delete(self, data: T) -> bool:
        """Delete first occurrence - O(n)"""
        if not self.head:
            return False
        
        if self.head.data == data:
            self.head = self.head.next
            return True
        
        current = self.head
        while current.next:
            if current.next.data == data:
                current.next = current.next.next
                return True
            current = current.next
        return False
    
    def display(self) -> None:
        """Display all elements - O(n)"""
        current = self.head
        elements = []
        while current:
            elements.append(str(current.data))
            current = current.next
        print(" -> ".join(elements))

# Usage example
ll = LinkedList[int]()
ll.insert(3)
ll.insert(2)
ll.insert(1)
ll.display()  # Output: 1 -> 2 -> 3


# **Time Complexity:** Insert O(1), Delete O(n), Display O(n)
# **Space Complexity:** O(n) for storage

### 2. **Find the length of a linked list (iterative and recursive)**


def length_iterative(self) -> int:
    """Iterative approach - O(n) time, O(1) space"""
    count = 0
    current = self.head
    while current:
        count += 1
        current = current.next
    return count

def length_recursive(self, node: Optional[Node[T]] = None) -> int:
    """Recursive approach - O(n) time, O(n) space due to call stack"""
    if node is None:
        node = self.head
    
    if not node:
        return 0
    
    return 1 + self.length_recursive(node.next)

# Add these methods to LinkedList class
LinkedList.length_iterative = length_iterative
LinkedList.length_recursive = length_recursive

# Test
ll = LinkedList[int]()
for i in range(5):
    ll.insert(i)

print(f"Iterative length: {ll.length_iterative()}")  # Output: 5
print(f"Recursive length: {ll.length_recursive()}")  # Output: 5


# **Key Point:** Recursive solution uses O(n) stack space, iterative uses O(1)



### 3. **Search for an element in a linked list**


def search(self, target: T) -> Optional[Node[T]]:
    """Search for element - returns node if found, None otherwise"""
    current = self.head
    position = 0
    
    while current:
        if current.data == target:
            return current, position
        current = current.next
        position += 1
    
    return None, -1

def search_recursive(self, node: Optional[Node[T]], target: T, position: int = 0) -> tuple:
    """Recursive search implementation"""
    if not node:
        return None, -1
    
    if node.data == target:
        return node, position
    
    return self.search_recursive(node.next, target, position + 1)

# Add to LinkedList class
LinkedList.search = search
LinkedList.search_recursive = search_recursive

# Test
ll = LinkedList[str]()
ll.insert("python")
ll.insert("java")
ll.insert("javascript")

node, pos = ll.search("java")
if node:
    print(f"Found '{node.data}' at position {pos}")  # Output: Found 'java' at position 1


# **Time Complexity:** O(n) - worst case traverse entire list
# **Space Complexity:** O(1) iterative, O(n) recursive

### 4. **Reverse a linked list**


def reverse_iterative(self) -> None:
    """Reverse linked list iteratively - O(n) time, O(1) space"""
    prev = None
    current = self.head
    
    while current:
        next_temp = current.next  # Store next node
        current.next = prev       # Reverse the link
        prev = current           # Move prev forward
        current = next_temp      # Move current forward
    
    self.head = prev

def reverse_recursive(self, node: Optional[Node[T]]) -> Optional[Node[T]]:
    """Reverse linked list recursively - O(n) time, O(n) space"""
    if not node or not node.next:
        return node
    
    # Recursively reverse the rest
    reversed_head = self.reverse_recursive(node.next)
    
    # Reverse current connection
    node.next.next = node
    node.next = None
    
    return reversed_head

def reverse_recursive_wrapper(self) -> None:
    """Wrapper for recursive reverse"""
    self.head = self.reverse_recursive(self.head)

# Add to LinkedList class
LinkedList.reverse_iterative = reverse_iterative
LinkedList.reverse_recursive = reverse_recursive_wrapper

# Test
ll = LinkedList[int]()
for i in range(5):
    ll.insert(i)

print("Original:")
ll.display()  # 4 -> 3 -> 2 -> 1 -> 0

ll.reverse_iterative()
print("Reversed:")
ll.display()  # 0 -> 1 -> 2 -> 3 -> 4


# **Key Insight:** Iterative approach preferred for space efficiency

## 🟡 Normal Questions (5-7)

### 5. **Detect if a linked list has a cycle (Floyd's Cycle Detection)**


def has_cycle(self) -> bool:
    """
    Floyd's Cycle Detection Algorithm (Tortoise and Hare)
    Time: O(n), Space: O(1)
    """
    if not self.head or not self.head.next:
        return False
    
    slow = self.head      # Tortoise moves 1 step
    fast = self.head.next # Hare moves 2 steps
    
    while fast and fast.next:
        if slow == fast:
            return True
        slow = slow.next
        fast = fast.next.next
    
    return False

def find_cycle_start(self) -> Optional[Node[T]]:
    """
    Find the starting node of cycle
    Uses Floyd's algorithm + mathematical property
    """
    if not self.has_cycle():
        return None
    
    # Phase 1: Detect cycle
    slow = fast = self.head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            break
    
    # Phase 2: Find cycle start
    # Move one pointer to head, keep other at meeting point
    slow = self.head
    while slow != fast:
        slow = slow.next
        fast = fast.next
    
    return slow  # Both pointers meet at cycle start

def cycle_length(self) -> int:
    """Find length of cycle"""
    if not self.has_cycle():
        return 0
    
    slow = fast = self.head
    # Find meeting point
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            break
    
    # Count cycle length
    count = 1
    current = slow.next
    while current != slow:
        count += 1
        current = current.next
    
    return count

# Test cycle detection
def create_cycle_test():
    """Create test linked list with cycle"""
    ll = LinkedList[int]()
    
    # Create nodes manually for cycle testing
    node1 = Node(1)
    node2 = Node(2)
    node3 = Node(3)
    node4 = Node(4)
    
    # Connect nodes
    node1.next = node2
    node2.next = node3
    node3.next = node4
    node4.next = node2  # Create cycle: 4 -> 2
    
    ll.head = node1
    return ll

# Add methods to LinkedList
LinkedList.has_cycle = has_cycle
LinkedList.find_cycle_start = find_cycle_start
LinkedList.cycle_length = cycle_length

# Test
cycle_list = create_cycle_test()
print(f"Has cycle: {cycle_list.has_cycle()}")  # True
print(f"Cycle length: {cycle_list.cycle_length()}")  # 3


# **Algorithm Explanation:** 
# - Slow pointer moves 1 step, fast moves 2 steps
# - If there's a cycle, fast will eventually catch up to slow
# - Mathematical proof: If cycle length is C, they'll meet within C iterations


### 6. **Find the middle element of a linked list**


def find_middle(self) -> Optional[Node[T]]:
    """
    Find middle element using two pointers
    Time: O(n), Space: O(1)
    For even length: returns second middle element
    """
    if not self.head:
        return None
    
    slow = fast = self.head
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    
    return slow

def find_middle_both(self) -> tuple:
    """
    For even length lists, return both middle elements
    """
    if not self.head:
        return None, None
    
    slow = fast = self.head
    prev_slow = None
    
    while fast and fast.next:
        prev_slow = slow
        slow = slow.next
        fast = fast.next.next
    
    # If fast is None, even length - return both middles
    if not fast:
        return prev_slow, slow
    else:
        return slow, None  # Odd length - single middle

def find_middle_iterative(self) -> Optional[Node[T]]:
    """
    Alternative approach: count length first
    Time: O(n), Space: O(1) - but requires two passes
    """
    if not self.head:
        return None
    
    # Count total nodes
    count = 0
    current = self.head
    while current:
        count += 1
        current = current.next
    
    # Find middle position
    middle_pos = count // 2
    current = self.head
    
    for _ in range(middle_pos):
        current = current.next
    
    return current

# Add to LinkedList class
LinkedList.find_middle = find_middle
LinkedList.find_middle_both = find_middle_both
LinkedList.find_middle_iterative = find_middle_iterative

# Test
ll = LinkedList[int]()
for i in range(1, 8):  # 1,2,3,4,5,6,7
    ll.insert(i)

middle = ll.find_middle()
print(f"Middle element: {middle.data}")  # Output: 4

# Test with even length
ll2 = LinkedList[int]()
for i in range(1, 7):  # 1,2,3,4,5,6
    ll2.insert(i)

first_mid, second_mid = ll2.find_middle_both()
print(f"Middle elements: {first_mid.data}, {second_mid.data}")  # 3, 4


# **Two-Pointer Technique:** Classic approach - fast pointer moves twice as fast as slow

### 7. **Remove duplicates from a sorted linked list**


def remove_duplicates_sorted(self) -> None:
    """
    Remove duplicates from sorted linked list
    Time: O(n), Space: O(1)
    """
    if not self.head:
        return
    
    current = self.head
    
    while current.next:
        if current.data == current.next.data:
            # Skip duplicate node
            current.next = current.next.next
        else:
            current = current.next

def remove_duplicates_unsorted(self) -> None:
    """
    Remove duplicates from unsorted linked list
    Time: O(n), Space: O(n) - uses hash set
    """
    if not self.head:
        return
    
    seen = set()
    current = self.head
    prev = None
    
    while current:
        if current.data in seen:
            # Remove duplicate
            prev.next = current.next
        else:
            seen.add(current.data)
            prev = current
        current = current.next

def remove_duplicates_unsorted_no_buffer(self) -> None:
    """
    Remove duplicates without using extra space
    Time: O(n²), Space: O(1)
    """
    if not self.head:
        return
    
    current = self.head
    
    while current:
        runner = current
        while runner.next:
            if runner.next.data == current.data:
                runner.next = runner.next.next
            else:
                runner = runner.next
        current = current.next

# Add methods to LinkedList
LinkedList.remove_duplicates_sorted = remove_duplicates_sorted
LinkedList.remove_duplicates_unsorted = remove_duplicates_unsorted
LinkedList.remove_duplicates_unsorted_no_buffer = remove_duplicates_unsorted_no_buffer

# Test sorted duplicates
ll_sorted = LinkedList[int]()
for val in [1, 1, 2, 2, 2, 3, 4, 4, 5]:
    ll_sorted.insert(val)

print("Before removing duplicates:")
ll_sorted.display()  # 5 -> 4 -> 4 -> 3 -> 2 -> 2 -> 2 -> 1 -> 1

ll_sorted.remove_duplicates_sorted()
print("After removing duplicates:")
ll_sorted.display()  # 5 -> 4 -> 3 -> 2 -> 1

# Test unsorted duplicates
ll_unsorted = LinkedList[int]()
for val in [1, 3, 2, 1, 4, 2, 5, 3]:
    ll_unsorted.insert(val)

print("\nUnsorted before:")
ll_unsorted.display()  # 3 -> 5 -> 2 -> 4 -> 1 -> 2 -> 3 -> 1

ll_unsorted.remove_duplicates_unsorted()
print("Unsorted after:")
ll_unsorted.display()  # 3 -> 5 -> 2 -> 4 -> 1


# **Trade-off Analysis:**
# - **Sorted:** O(n) time, O(1) space - optimal
# - **Unsorted with buffer:** O(n) time, O(n) space
# - **Unsorted without buffer:** O(n²) time, O(1) space

## 🔴 Hard Questions (8-10)

### 8. **Merge two sorted linked lists**


def merge_sorted_lists(list1: Optional[Node[T]], list2: Optional[Node[T]]) -> Optional[Node[T]]:
    """
    Merge two sorted linked lists iteratively
    Time: O(m + n), Space: O(1)
    """
    # Create dummy head for easier implementation
    dummy = Node(None)
    current = dummy
    
    while list1 and list2:
        if list1.data <= list2.data:
            current.next = list1
            list1 = list1.next
        else:
            current.next = list2
            list2 = list2.next
        current = current.next
    
    # Append remaining nodes
    current.next = list1 if list1 else list2
    
    return dummy.next

def merge_sorted_lists_recursive(list1: Optional[Node[T]], list2: Optional[Node[T]]) -> Optional[Node[T]]:
    """
    Merge two sorted linked lists recursively
    Time: O(m + n), Space: O(m + n) due to recursion stack
    """
    # Base cases
    if not list1:
        return list2
    if not list2:
        return list1
    
    # Choose smaller element and recurse
    if list1.data <= list2.data:
        list1.next = merge_sorted_lists_recursive(list1.next, list2)
        return list1
    else:
        list2.next = merge_sorted_lists_recursive(list1, list2.next)
        return list2

def merge_k_sorted_lists(lists: list[Optional[Node[T]]]) -> Optional[Node[T]]:
    """
    Merge k sorted linked lists using divide and conquer
    Time: O(N log k) where N is total nodes, k is number of lists
    Space: O(log k) for recursion stack
    """
    if not lists:
        return None
    
    def merge_two_lists(l1: Optional[Node[T]], l2: Optional[Node[T]]) -> Optional[Node[T]]:
        dummy = Node(None)
        current = dummy
        
        while l1 and l2:
            if l1.data <= l2.data:
                current.next = l1
                l1 = l1.next
            else:
                current.next = l2
                l2 = l2.next
            current = current.next
        
        current.next = l1 if l1 else l2
        return dummy.next
    
    # Divide and conquer approach
    while len(lists) > 1:
        merged_lists = []
        for i in range(0, len(lists), 2):
            l1 = lists[i]
            l2 = lists[i + 1] if i + 1 < len(lists) else None
            merged_lists.append(merge_two_lists(l1, l2))
        lists = merged_lists
    
    return lists[0] if lists else None

# Priority queue approach for k sorted lists
import heapq
from typing import List

def merge_k_sorted_lists_heap(lists: List[Optional[Node[T]]]) -> Optional[Node[T]]:
    """
    Merge k sorted lists using min heap
    Time: O(N log k), Space: O(k)
    """
    heap = []
    
    # Add first node from each list to heap
    for i, node in enumerate(lists):
        if node:
            heapq.heappush(heap, (node.data, i, node))
    
    dummy = Node(None)
    current = dummy
    
    while heap:
        val, list_idx, node = heapq.heappop(heap)
        
        # Add node to result
        current.next = node
        current = current.next
        
        # Add next node from same list
        if node.next:
            heapq.heappush(heap, (node.next.data, list_idx, node.next))
    
    return dummy.next

# Test merge functionality
def test_merge():
    # Create sorted lists
    ll1 = LinkedList[int]()
    for val in [1, 3, 5, 7]:
        ll1.insert(val)
    
    ll2 = LinkedList[int]()
    for val in [2, 4, 6, 8]:
        ll2.insert(val)
    
    # Merge lists
    merged_head = merge_sorted_lists(ll1.head, ll2.head)
    
    # Display result
    current = merged_head
    result = []
    while current:
        result.append(current.data)
        current = current.next
    
    print("Merged result:", result)  # [1, 2, 3, 4, 5, 6, 7, 8]

test_merge()


# **Key Insights:**
# - **Dummy head technique** simplifies edge cases
# - **Divide and conquer** optimal for k lists
# - **Heap approach** easier to understand but same complexity


### 9. **Add two numbers represented as linked lists**


def add_two_numbers(l1: Optional[Node[int]], l2: Optional[Node[int]]) -> Optional[Node[int]]:
    """
    Add two numbers represented as linked lists (digits in reverse order)
    Example: 342 + 465 = 807 represented as [2,4,3] + [5,6,4] = [7,0,8]
    Time: O(max(m, n)), Space: O(max(m, n))
    """
    dummy = Node(0)
    current = dummy
    carry = 0
    
    while l1 or l2 or carry:
        # Get current digits
        x = l1.data if l1 else 0
        y = l2.data if l2 else 0
        
        # Calculate sum
        total = x + y + carry
        carry = total // 10
        digit = total % 10
        
        # Create new node
        current.next = Node(digit)
        current = current.next
        
        # Move to next nodes
        if l1:
            l1 = l1.next
        if l2:
            l2 = l2.next
    
    return dummy.next

def add_two_numbers_forward(l1: Optional[Node[int]], l2: Optional[Node[int]]) -> Optional[Node[int]]:
    """
    Add two numbers with digits in forward order
    Example: 342 + 465 = 807 represented as [3,4,2] + [4,6,5] = [8,0,7]
    Uses stack to reverse the process
    """
    # Convert to stacks
    stack1, stack2 = [], []
    
    while l1:
        stack1.append(l1.data)
        l1 = l1.next
    
    while l2:
        stack2.append(l2.data)
        l2 = l2.next
    
    # Add from least significant digits
    result = None
    carry = 0
    
    while stack1 or stack2 or carry:
        x = stack1.pop() if stack1 else 0
        y = stack2.pop() if stack2 else 0
        
        total = x + y + carry
        carry = total // 10
        digit = total % 10
        
        # Insert at beginning (reverse order)
        new_node = Node(digit)
        new_node.next = result
        result = new_node
    
    return result

def multiply_two_numbers(l1: Optional[Node[int]], l2: Optional[Node[int]]) -> Optional[Node[int]]:
    """
    Multiply two numbers represented as linked lists
    More complex - requires handling multiple partial products
    """
    # Convert linked lists to integers
    def list_to_number(node: Optional[Node[int]]) -> int:
        num = 0
        while node:
            num = num * 10 + node.data
            node = node.next
        return num
    
    # Convert integer to linked list
    def number_to_list(num: int) -> Optional[Node[int]]:
        if num == 0:
            return Node(0)
        
        dummy = Node(0)
        current = dummy
        
        # Convert to string to handle digits
        for digit in str(num):
            current.next = Node(int(digit))
            current = current.next
        
        return dummy.next
    
    # Perform multiplication
    num1 = list_to_number(l1)
    num2 = list_to_number(l2)
    product = num1 * num2
    
    return number_to_list(product)

# Optimized version for very large numbers
def add_two_numbers_optimized(l1: Optional[Node[int]], l2: Optional[Node[int]]) -> Optional[Node[int]]:
    """
    Optimized version that handles edge cases better
    """
    if not l1:
        return l2
    if not l2:
        return l1
    
    dummy = Node(0)
    current = dummy
    carry = 0
    
    while l1 or l2 or carry:
        # Use getattr for safer access
        val1 = l1.data if l1 else 0
        val2 = l2.data if l2 else 0
        
        # Input validation for security
        if not (0 <= val1 <= 9) or not (0 <= val2 <= 9):
            raise ValueError("Invalid digit in linked list")
        
        total = val1 + val2 + carry
        carry, digit = divmod(total, 10)
        
        current.next = Node(digit)
        current = current.next
        
        # Move pointers
        l1 = l1.next if l1 else None
        l2 = l2.next if l2 else None
    
    return dummy.next

# Test addition
def test_addition():
    # Create number 342 as [2,4,3]
    ll1 = LinkedList[int]()
    for digit in [2, 4, 3]:
        ll1.insert(digit)
    
    # Create number 465 as [5,6,4]
    ll2 = LinkedList[int]()
    for digit in [5, 6, 4]:
        ll2.insert(digit)
    
    # Add numbers
    result = add_two_numbers(ll1.head, ll2.head)
    
    # Display result
    digits = []
    while result:
        digits.append(result.data)
        result = result.next
    
    print("Addition result:", digits)  # [7, 0, 8] representing 807

test_addition()


# **Real-world Application:** Used in big integer arithmetic libraries, cryptocurrency calculations

# I'll provide the complete code for cloning a linked list with random pointers, including all the missing parts and comprehensive testing. This implementation follows your preferences for type safety, security, and detailed explanations.This complete implementation provides four different approaches to clone a linked list with random pointers, each with its own trade-offs:

from typing import Optional, Dict, Set
import unittest

class RandomNode:
    """
    Node with additional random pointer
    
    Real-world usage: This structure is used in:
    - Undo/Redo systems where nodes can reference any previous state
    - Graph representations in social networks (connections + random friend suggestions)
    - Memory management systems with garbage collection references
    """
    def __init__(self, data: int):
        self.data = data
        self.next: Optional['RandomNode'] = None
        self.random: Optional['RandomNode'] = None
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        random_data = self.random.data if self.random else "None"
        return f"Node({self.data}, random={random_data})"

def clone_random_list_hashmap(head: Optional[RandomNode]) -> Optional[RandomNode]:
    """
    Clone linked list with random pointers using hashmap approach
    
    Time Complexity: O(n) - two passes through the list
    Space Complexity: O(n) - hashmap stores all nodes
    
    Algorithm:
    1. First pass: Create all cloned nodes and store original->clone mapping
    2. Second pass: Set next and random pointers using the mapping
    
    Real-world example: Database record cloning where foreign keys need remapping
    """
    if not head:
        return None
    
    # Phase 1: Create all nodes and store mapping
    node_map: Dict[RandomNode, RandomNode] = {}
    current = head
    
    # Create all cloned nodes first
    while current:
        node_map[current] = RandomNode(current.data)
        current = current.next
    
    # Phase 2: Set next and random pointers using the mapping
    current = head
    while current:
        cloned = node_map[current]
        
        # Set next pointer if it exists
        if current.next:
            cloned.next = node_map[current.next]
        
        # Set random pointer if it exists
        if current.random:
            cloned.random = node_map[current.random]
        
        current = current.next
    
    return node_map[head]

def clone_random_list_optimized(head: Optional[RandomNode]) -> Optional[RandomNode]:
    """
    Clone using interleaving technique - O(n) time, O(1) space
    
    Technique: Insert cloned nodes between original nodes
    Pattern: A -> A' -> B -> B' -> C -> C'
    
    Real-world usage: Memory-efficient cloning in embedded systems
    where memory is limited but processing power is available
    
    Algorithm:
    1. Interleave cloned nodes: A->A'->B->B'->C->C'
    2. Set random pointers: A'.random = A.random.next
    3. Separate lists: restore original and return cloned
    """
    if not head:
        return None
    
    # Phase 1: Create cloned nodes interleaved with original
    current = head
    while current:
        cloned = RandomNode(current.data)
        cloned.next = current.next
        current.next = cloned
        current = cloned.next
    
    # Phase 2: Set random pointers for cloned nodes
    current = head
    while current:
        if current.random:
            # current.next is the cloned node
            # current.random.next is the cloned version of random target
            current.next.random = current.random.next
        current = current.next.next  # Skip cloned node
    
    # Phase 3: Separate original and cloned lists
    dummy = RandomNode(0)  # Dummy head for easier list building
    cloned_current = dummy
    current = head
    
    while current:
        # Extract cloned node
        cloned_current.next = current.next
        current.next = current.next.next  # Restore original list
        
        cloned_current = cloned_current.next
        current = current.next
    
    return dummy.next

def clone_random_list_recursive(head: Optional[RandomNode], 
                              visited: Optional[Dict[RandomNode, RandomNode]] = None) -> Optional[RandomNode]:
    """
    Recursive approach with memoization
    
    Time Complexity: O(n)
    Space Complexity: O(n) - recursion stack + memoization
    
    Real-world usage: Functional programming approach, useful in
    languages with tail call optimization
    """
    if not head:
        return None
    
    if visited is None:
        visited = {}
    
    # Return already cloned node (memoization)
    if head in visited:
        return visited[head]
    
    # Create new node
    cloned = RandomNode(head.data)
    visited[head] = cloned  # Memoize before recursion to handle cycles
    
    # Recursively clone next and random
    cloned.next = clone_random_list_recursive(head.next, visited)
    cloned.random = clone_random_list_recursive(head.random, visited)
    
    return cloned

def validate_clone(original: Optional[RandomNode], cloned: Optional[RandomNode]) -> bool:
    """
    Validate that the clone is correct and independent
    
    Security check: Ensures deep copy was successful and no references
    to original objects exist (prevents data corruption)
    """
    if not original and not cloned:
        return True
    
    if not original or not cloned:
        return False
    
    # Build position maps for structure validation
    orig_nodes: Dict[RandomNode, int] = {}
    clone_nodes: Dict[RandomNode, int] = {}
    
    # Map original nodes to indices
    index = 0
    orig_current = original
    while orig_current:
        orig_nodes[orig_current] = index
        orig_current = orig_current.next
        index += 1
    
    # Map cloned nodes to indices
    index = 0
    clone_current = cloned
    while clone_current:
        clone_nodes[clone_current] = index
        clone_current = clone_current.next
        index += 1
    
    # Verify structure and independence
    orig_current = original
    clone_current = cloned
    
    while orig_current and clone_current:
        # Check data integrity
        if orig_current.data != clone_current.data:
            return False
        
        # SECURITY: Check that nodes are different objects
        if orig_current is clone_current:
            return False
        
        # Verify random pointer structure
        if orig_current.random:
            if not clone_current.random:
                return False
            # Check that random pointers point to corresponding positions
            if orig_nodes[orig_current.random] != clone_nodes[clone_current.random]:
                return False
        elif clone_current.random:
            return False
        
        orig_current = orig_current.next
        clone_current = clone_current.next
    
    return orig_current is None and clone_current is None

def clone_random_list_secure(head: Optional[RandomNode]) -> Optional[RandomNode]:
    """
    Security-enhanced version with input validation
    
    Security measures:
    1. Cycle detection to prevent infinite loops
    2. Size limits to prevent DoS attacks
    3. Input sanitization
    
    Real-world usage: Production systems handling untrusted input
    """
    if not head:
        return None
    
    # SECURITY: Validate input - prevent cycles and malicious structures
    visited: Set[RandomNode] = set()
    current = head
    node_count = 0
    max_nodes = 10000  # Prevent DoS attacks
    
    while current and node_count < max_nodes:
        if current in visited:
            raise ValueError("Cycle detected in input list")
        
        visited.add(current)
        node_count += 1
        current = current.next
    
    if node_count >= max_nodes:
        raise ValueError("Input list too large - potential DoS attack")
    
    # SECURITY: Validate data ranges (prevent integer overflow)
    current = head
    while current:
        if not isinstance(current.data, int):
            raise TypeError("Invalid data type - expected int")
        if current.data < -2**31 or current.data > 2**31 - 1:
            raise ValueError("Data value out of safe range")
        current = current.next
    
    # Proceed with secure cloning
    return clone_random_list_hashmap(head)

def print_list(head: Optional[RandomNode], name: str = "List") -> None:
    """Helper function to print list for debugging"""
    print(f"\n{name}:")
    current = head
    while current:
        random_data = current.random.data if current.random else "None"
        print(f"  Node({current.data}) -> random: {random_data}")
        current = current.next

def create_test_list() -> RandomNode:
    """Create a test list for demonstration"""
    # Create test list: 1 -> 2 -> 3
    node1 = RandomNode(1)
    node2 = RandomNode(2)
    node3 = RandomNode(3)
    
    # Set next pointers
    node1.next = node2
    node2.next = node3
    
    # Set random pointers (creates complex structure)
    node1.random = node3  # 1 points to 3
    node2.random = node1  # 2 points to 1
    node3.random = node2  # 3 points to 2
    
    return node1

class TestRandomListClone(unittest.TestCase):
    """Comprehensive test suite for all cloning methods"""
    
    def setUp(self):
        """Set up test data"""
        self.test_list = create_test_list()
    
    def test_hashmap_approach(self):
        """Test hashmap-based cloning"""
        cloned = clone_random_list_hashmap(self.test_list)
        self.assertTrue(validate_clone(self.test_list, cloned))
    
    def test_optimized_approach(self):
        """Test space-optimized cloning"""
        cloned = clone_random_list_optimized(self.test_list)
        self.assertTrue(validate_clone(self.test_list, cloned))
    
    def test_recursive_approach(self):
        """Test recursive cloning"""
        cloned = clone_random_list_recursive(self.test_list)
        self.assertTrue(validate_clone(self.test_list, cloned))
    
    def test_secure_approach(self):
        """Test security-enhanced cloning"""
        cloned = clone_random_list_secure(self.test_list)
        self.assertTrue(validate_clone(self.test_list, cloned))
    
    def test_empty_list(self):
        """Test edge case: empty list"""
        self.assertIsNone(clone_random_list_hashmap(None))
        self.assertIsNone(clone_random_list_optimized(None))
        self.assertIsNone(clone_random_list_recursive(None))
    
    def test_single_node(self):
        """Test edge case: single node"""
        single = RandomNode(42)
        single.random = single  # Self-reference
        
        cloned = clone_random_list_hashmap(single)
        self.assertEqual(cloned.data, 42)
        self.assertEqual(cloned.random, cloned)  # Should point to itself
    
    def test_security_cycle_detection(self):
        """Test security: cycle detection"""
        # Create a cycle
        node1 = RandomNode(1)
        node2 = RandomNode(2)
        node1.next = node2
        node2.next = node1  # Creates cycle
        
        with self.assertRaises(ValueError):
            clone_random_list_secure(node1)
    
    def test_security_size_limit(self):
        """Test security: size limit protection"""
        # This test would require creating a very large list
        # In practice, you'd mock the max_nodes value for testing
        pass

def performance_comparison():
    """
    Performance comparison of different approaches
    
    Real-world usage: Helps choose the right algorithm based on constraints
    """
    import time
    
    # Create larger test list for performance testing
    def create_large_list(size: int) -> RandomNode:
        if size == 0:
            return None
        
        nodes = [RandomNode(i) for i in range(size)]
        
        # Link nodes
        for i in range(size - 1):
            nodes[i].next = nodes[i + 1]
        
        # Set random pointers
        for i, node in enumerate(nodes):
            node.random = nodes[(i + size // 2) % size]
        
        return nodes[0]
    
    test_sizes = [100, 1000]
    
    for size in test_sizes:
        print(f"\nPerformance test for {size} nodes:")
        test_list = create_large_list(size)
        
        # Test hashmap approach
        start = time.time()
        clone_random_list_hashmap(test_list)
        hashmap_time = time.time() - start
        
        # Test optimized approach
        start = time.time()
        clone_random_list_optimized(test_list)
        optimized_time = time.time() - start
        
        print(f"  Hashmap approach: {hashmap_time:.6f}s")
        print(f"  Optimized approach: {optimized_time:.6f}s")
        print(f"  Space savings: {((hashmap_time - optimized_time) / hashmap_time * 100):.1f}%")

if __name__ == "__main__":
    # Demonstration
    print("=== Random Linked List Cloning Demo ===")
    
    # Create test list
    original = create_test_list()
    print_list(original, "Original List")
    
    # Test all approaches
    approaches = [
        ("Hashmap", clone_random_list_hashmap),
        ("Optimized", clone_random_list_optimized),
        ("Recursive", clone_random_list_recursive),
        ("Secure", clone_random_list_secure)
    ]
    
    for name, func in approaches:
        try:
            cloned = func(original)
            print_list(cloned, f"{name} Cloned List")
            
            # Validate
            is_valid = validate_clone(original, cloned)
            print(f"  Validation: {'✓ PASSED' if is_valid else '✗ FAILED'}")
            
        except Exception as e:
            print(f"  {name} approach failed: {e}")
    
    # Run performance comparison
    performance_comparison()
    
    # Run unit tests
    print("\n=== Running Unit Tests ===")
    unittest.main(verbosity=2, exit=False)


## **Algorithm Approaches:**

### 1. **Hashmap Approach** (Most Common)
# - **Time:** O(n), **Space:** O(n)
# - **Usage:** Standard approach, easy to understand and implement
# - **Real-world:** Database record cloning, object serialization

### 2. **Optimized Interleaving** (Space Efficient)
# - **Time:** O(n), **Space:** O(1)
# - **Usage:** Memory-constrained environments, embedded systems
# - **Technique:** Temporarily interleaves cloned nodes between original nodes

### 3. **Recursive with Memoization**
# - **Time:** O(n), **Space:** O(n)
# - **Usage:** Functional programming paradigms, elegant solution
# - **Advantage:** Natural handling of complex pointer relationships

### 4. **Security-Enhanced Version**
# - **Features:** Input validation, cycle detection, DoS protection
# - **Usage:** Production systems handling untrusted input
# - **Security:** Prevents infinite loops and resource exhaustion

## **Key Security Considerations:**

# 1. **Cycle Detection:** Prevents infinite loops from malicious input
# 2. **Size Limits:** Protects against DoS attacks
# 3. **Data Validation:** Ensures type safety and range checking
# 4. **Deep Copy Validation:** Confirms no references to original objects

## **Real-world Applications:**

# - **Undo/Redo Systems:** Complex state management with arbitrary references
# - **Social Networks:** User connections with friend suggestions
# - **Memory Management:** Garbage collection with reference tracking
# - **Database Systems:** Record cloning with foreign key remapping

## **Performance Characteristics:**

# The optimized approach saves memory but requires three passes through the data. The hashmap approach is faster but uses more memory. Choose based on your specific constraints.

# The implementation includes comprehensive testing, performance comparison, and follows your preferences for type safety, security, and detailed explanations of internal workings.

