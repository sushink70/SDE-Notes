# A **heap** is a specialized tree-based data structure that satisfies the **heap property**. 
# It is commonly used to implement priority queues, where elements are organized based on their priority (e.g., smallest or largest value). 
# In this explanation, I'll provide a detailed understanding of heaps, implement a heap in Python without using the `heapq` module, discuss its applications, 
# advantages, disadvantages, Big O notation, database connection considerations, security aspects, and provide a real-world code example.

# ---

### **What is a Heap?**

# A **heap** is a complete binary tree (a binary tree where all levels except possibly the last are fully filled, and all nodes in the last level are as far left as possible) 
# that satisfies the **heap property**:

# - **Max-Heap**: The value of each node is greater than or equal to the values of its children. The largest value is at the root.
# - **Min-Heap**: The value of each node is less than or equal to the values of its children. The smallest value is at the root.

# Heaps are typically implemented using arrays for efficiency, where the tree structure is implicitly maintained using index calculations:
# - For a node at index `i`:
#   - Left child: `2*i + 1`
#   - Right child: `2*i + 2`
#   - Parent: `(i-1)//2`

# ---

### **Implementing a Min-Heap in Python**

# Below is a Python implementation of a **min-heap** without using the `heapq` module. This implementation includes insertion, deletion (popping the minimum element), 
# and heapification processes.


class MinHeap:
    def __init__(self):
        self.heap = []

    def parent(self, i):
        return (i - 1) // 2

    def left_child(self, i):
        return 2 * i + 1

    def right_child(self, i):
        return 2 * i + 2

    def swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def insert(self, value):
        # Add the new element at the end
        self.heap.append(value)
        # Fix the heap property by moving the element up
        self._sift_up(len(self.heap) - 1)

    def _sift_up(self, i):
        # While the node is not the root and is smaller than its parent
        while i > 0 and self.heap[i] < self.heap[self.parent(i)]:
            self.swap(i, self.parent(i))
            i = self.parent(i)

    def pop_min(self):
        if not self.heap:
            raise IndexError("Heap is empty")
        
        # Get the minimum value (root)
        min_val = self.heap[0]
        
        # Move the last element to the root and reduce heap size
        self.heap[0] = self.heap[-1]
        self.heap.pop()
        
        # Fix the heap property by moving the root down
        if self.heap:  # Only sift down if heap is not empty
            self._sift_down(0)
        
        return min_val

    def _sift_down(self, i):
        min_index = i
        size = len(self.heap)
        
        while True:
            left = self.left_child(i)
            right = self.right_child(i)
            
            # Compare with left child
            if left < size and self.heap[left] < self.heap[min_index]:
                min_index = left
            
            # Compare with right child
            if right < size and self.heap[right] < self.heap[min_index]:
                min_index = right
            
            if min_index == i:
                break
            
            self.swap(i, min_index)
            i = min_index

    def get_min(self):
        if not self.heap:
            raise IndexError("Heap is empty")
        return self.heap[0]

    def size(self):
        return len(self.heap)

# Example usage
if __name__ == "__main__":
    heap = MinHeap()
    heap.insert(3)
    heap.insert(1)
    heap.insert(4)
    heap.insert(2)
    print("Min-Heap:", heap.heap)  # Output: [1, 2, 4, 3]
    print("Minimum:", heap.get_min())  # Output: 1
    print("Popped Min:", heap.pop_min())  # Output: 1
    print("Min-Heap after pop:", heap.heap)  # Output: [2, 3, 4]


### **How the Implementation Works**

# 1. **Initialization**: The heap is stored as a list (`self.heap`).
# 2. **Insert**:
#    - Append the new value to the end of the list.
#    - "Sift up" by comparing with the parent and swapping if the child is smaller (for a min-heap).
# 3. **Pop Min**:
#    - Return the root (minimum value).
#    - Move the last element to the root and reduce the heap size.
#    - "Sift down" by comparing with children and swapping with the smaller child until the heap property is restored.
# 4. **Sift Up/Down**:
#    - **Sift Up**: Moves a node up the tree to restore the heap property after insertion.
#    - **Sift Down**: Moves a node down the tree to restore the heap property after deletion.

# ---

### **Where Heaps Are Used**

# Heaps are versatile and used in various applications:

# 1. **Priority Queues**:
#    - Tasks are prioritized based on urgency (e.g., job scheduling in operating systems).
#    - Example: A hospital triage system where patients with higher severity are treated first.

# 2. **Graph Algorithms**:
#    - **Dijkstra’s Algorithm**: Finds the shortest path in a graph using a min-heap to select the node with the smallest distance.
#    - **Prim’s Algorithm**: Builds a minimum spanning tree by selecting the edge with the minimum weight.

# 3. **Heap Sort**:
#    - A sorting algorithm that builds a max-heap and repeatedly extracts the maximum element to sort in ascending order.

# 4. **Real-Time Systems**:
#    - Managing tasks with deadlines (e.g., real-time event processing in IoT systems).

# 5. **Median Maintenance**:
#    - Using two heaps (a max-heap for the lower half and a min-heap for the upper half) to efficiently compute the median of a stream of numbers.

# ---

### **Where Heaps Should Not Be Used**

# 1. **Searching for Arbitrary Elements**:
#    - Heaps are not designed for fast lookup of arbitrary elements (O(n) time for searching).
#    - Use hash tables or balanced binary search trees (e.g., AVL trees) instead.


# 2. **Dynamic Updates of Priorities**:
#    - If priorities of elements change frequently, heaps require O(n) to locate the element and O(log n) to update it, which can be inefficient.
#    - Consider Fibonacci heaps for better performance in such cases.

# 3. **Small Datasets**:
#    - For small datasets, simpler data structures like arrays or linked lists may suffice due to lower overhead.

# 4. **Stable Sorting**:
#    - Heap sort is not stable (does not preserve the relative order of equal elements), so it’s unsuitable when stability is required.

# ---

### **Real-World Code Example: Task Scheduler**

# Below is a real-world example of a task scheduler using a min-heap to prioritize tasks based on their deadlines.


class Task:
    def __init__(self, task_id, deadline, priority):
        self.task_id = task_id
        self.deadline = deadline
        self.priority = priority

    def __lt__(self, other):
        # Compare tasks based on deadline (earlier deadline has higher priority)
        return self.deadline < other.deadline

class TaskScheduler:
    def __init__(self):
        self.heap = MinHeap()

    def add_task(self, task_id, deadline, priority):
        task = Task(task_id, deadline, priority)
        self.heap.insert(task)

    def process_task(self):
        if self.heap.size() == 0:
            return None
        task = self.heap.pop_min()
        return task.task_id, task.deadline, task.priority

# Example usage
scheduler = TaskScheduler()
scheduler.add_task("T1", 10, 2)
scheduler.add_task("T2", 5, 1)
scheduler.add_task("T3", 8, 3)
print("Processing tasks:")
while scheduler.heap.size() > 0:
    task_id, deadline, priority = scheduler.process_task()
    print(f"Task {task_id}, Deadline: {deadline}, Priority: {priority}")


# **Output**:

# Processing tasks:
# Task T2, Deadline: 5, Priority: 1
# Task T3, Deadline: 8, Priority: 3
# Task T1, Deadline: 10, Priority: 2


# This scheduler processes tasks in order of their deadlines, ensuring the most urgent tasks are handled first.

# ---

### **Advantages of Heaps**

# 1. **Efficient Priority Operations**:
#    - Insertion and deletion of the minimum/maximum element are O(log n).
#    - Retrieving the minimum/maximum is O(1).

# 2. **Space Efficiency**:
#    - Implemented as an array, requiring no extra pointers like trees or linked lists.

# 3. **Versatility**:
#    - Supports both min-heap and max-heap, making it adaptable for various use cases.

# 4. **Scalability**:
#    - Performs well for large datasets due to logarithmic time complexity for key operations.

# ---

### **Disadvantages of Heaps**

# 1. **No Fast Lookup**:
#    - Searching for an arbitrary element takes O(n) time, as heaps are not designed for searching.

# 2. **Not Stable**:
#    - Heap sort does not preserve the relative order of equal elements.

# 3. **Complex Implementation**:
#    - Compared to simple arrays or lists, heap operations (sift up/down) are more complex to implement correctly.

# 4. **Limited Flexibility**:
#    - Heaps are specialized for priority-based operations and are less suitable for dynamic updates or general-purpose data storage.

# ---

### **Big O Notation**

# | Operation          | Time Complexity | Space Complexity |
# |--------------------|-----------------|------------------|
# | Insert             | O(log n)        | O(1)             |
# | Delete Min/Max     | O(log n)        | O(1)             |
# | Get Min/Max        | O(1)            | O(1)             |
# | Search             | O(n)            | O(1)             |
# | Heapify (build)    | O(n)            | O(1)             |
# | Heap Sort          | O(n log n)      | O(1)             |

# - **Insert and Delete**: Require sifting up or down, which takes O(log n) as the height of the heap is log n.
# - **Get Min/Max**: The root is directly accessible in O(1).
# - **Search**: Requires linear traversal of the array, hence O(n).
# - **Heapify**: Building a heap from an array takes O(n) due to the linear number of sift-down operations.
# - **Heap Sort**: Repeatedly extracting the min/max takes O(n log n).

# ---

### **Using Heaps with Database Connections**

# Heaps can be used in database-related applications, particularly for managing connections or query prioritization. Here’s how:

# 1. **Connection Pool Management**:
#    - A min-heap can prioritize database connections based on their availability or last-used timestamp, ensuring efficient reuse of connections.
#    - Example: A connection pool manager can use a heap to track idle connections and assign the one that has been idle the longest to a new request.

# 2. **Query Prioritization**:
#    - In a database system, queries can be assigned priorities (e.g., based on user type or urgency). A min-heap can schedule high-priority queries first.

# 3. **Example: Database Connection Pool**


class DatabaseConnection:
    def __init__(self, conn_id, last_used):
        self.conn_id = conn_id
        self.last_used = last_used

    def __lt__(self, other):
        return self.last_used < other.last_used

class ConnectionPool:
    def __init__(self):
        self.heap = MinHeap()

    def add_connection(self, conn_id, last_used):
        conn = DatabaseConnection(conn_id, last_used)
        self.heap.insert(conn)

    def get_connection(self):
        if self.heap.size() == 0:
            return None
        conn = self.heap.pop_min()
        return conn.conn_id, conn.last_used

# Example usage
pool = ConnectionPool()
pool.add_connection("Conn1", 100)
pool.add_connection("Conn2", 50)
pool.add_connection("Conn3", 75)
print("Available connection:", pool.get_connection())  # Output: ('Conn2', 50)


# In this example, the heap ensures the connection that was least recently used is allocated, optimizing resource utilization.

# ---

### **Security Considerations**

# When using heaps in applications (e.g., with database connections), consider the following security aspects:

# 1. **Data Integrity**:
#    - Ensure heap elements (e.g., task priorities or connection timestamps) are validated to prevent malicious inputs from disrupting the heap property.
#    - Example: Sanitize task deadlines to prevent negative or invalid values.

# 2. **Access Control**:
#    - If the heap manages sensitive data (e.g., database connections), ensure only authorized components can modify or access the heap.
#    - Use thread-safe implementations (e.g., with locks) in multi-threaded environments to prevent race conditions.

# 3. **Memory Safety**:
#    - Avoid memory leaks by properly managing heap memory, especially when storing complex objects.
#    - Use defensive programming to handle edge cases (e.g., empty heap, invalid indices).

# 4. **Denial-of-Service (DoS)**:
#    - Prevent excessive insertions that could exhaust memory by setting size limits or monitoring heap growth.
#    - Validate inputs to prevent malformed data from causing infinite loops in sift operations.

# 5. **Secure Database Connections**:
#    - When using heaps to manage database connections, ensure connections use secure protocols (e.g., TLS) and credentials are encrypted.
#    - Regularly rotate connection credentials and monitor for unauthorized access.

# ---

### **Conclusion**

# Heaps are powerful data structures for managing prioritized data, with applications in scheduling, graph algorithms, and sorting. Their logarithmic time complexity for key operations makes them efficient for large datasets, but they are not suitable for arbitrary searches or dynamic updates. When used with database connections, heaps can optimize resource allocation, but security measures like input validation and access control are critical. The provided Python implementation and real-world example demonstrate how to apply heaps effectively in practical scenarios.

# If you have further questions or need additional examples, let me know!

# Complete Guide to Heaps in Python

## What is a Heap?

# A heap is a specialized tree-based data structure that satisfies the **heap property**. It's a complete binary tree where every parent node has a value that is either greater than or equal to (max-heap) or less than or equal to (min-heap) its children.

# **Key Characteristics:**
# - **Complete Binary Tree**: All levels are filled except possibly the last level, which is filled from left to right
# - **Heap Property**: Parent-child relationship maintains order (min or max)
# - **Array Representation**: Efficiently stored in arrays where for index `i`, left child is at `2i+1` and right child is at `2i+2`

## Python Implementation

# Python's `heapq` module implements a **min-heap** by default:


import heapq
from typing import List, Optional, Any, Tuple
import time
from dataclasses import dataclass
from datetime import datetime

# Basic heap operations
def basic_heap_operations():
    """Demonstrates basic heap operations with type hints"""
    
    # Create a min-heap
    heap: List[int] = []
    
    # Insert elements (heapify maintains heap property)
    elements = [4, 1, 3, 2, 16, 9, 10, 14, 8, 7]
    for element in elements:
        heapq.heappush(heap, element)
    
    print(f"Heap after insertions: {heap}")
    # Output: [1, 2, 3, 4, 7, 9, 10, 14, 8, 16]
    
    # Pop minimum element
    minimum = heapq.heappop(heap)
    print(f"Minimum element: {minimum}")
    print(f"Heap after pop: {heap}")
    
    # Peek at minimum without removing
    if heap:
        print(f"Current minimum: {heap[0]}")
    
    return heap

# Custom heap for complex objects
@dataclass
class Task:
    """Task with priority for task scheduling"""
    priority: int
    name: str
    created_at: datetime
    
    def __lt__(self, other: 'Task') -> bool:
        """Less than comparison for heap ordering"""
        return self.priority < other.priority

def priority_queue_example():
    """Real-world example: Task scheduler using heap"""
    
    task_heap: List[Task] = []
    
    # Add tasks with different priorities
    tasks = [
        Task(3, "Send email", datetime.now()),
        Task(1, "Fix critical bug", datetime.now()),
        Task(2, "Code review", datetime.now()),
        Task(1, "Database backup", datetime.now()),
    ]
    
    # Insert tasks into heap
    for task in tasks:
        heapq.heappush(task_heap, task)
    
    # Process tasks in priority order
    print("Processing tasks by priority:")
    while task_heap:
        current_task = heapq.heappop(task_heap)
        print(f"Priority {current_task.priority}: {current_task.name}")


## Real-World Use Cases

### 1. **API Rate Limiting System**

from typing import Dict, NamedTuple
import time

class RateLimitEntry(NamedTuple):
    """Entry for rate limiting with timestamp"""
    timestamp: float
    user_id: str
    
    def __lt__(self, other: 'RateLimitEntry') -> bool:
        return self.timestamp < other.timestamp

class RateLimiter:
    """Rate limiter using heap for efficient cleanup"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests_heap: List[RateLimitEntry] = []
        self.user_counts: Dict[str, int] = {}
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user is allowed to make request"""
        current_time = time.time()
        
        # Clean up old entries efficiently using heap
        self._cleanup_old_entries(current_time)
        
        # Check current user's request count
        user_count = self.user_counts.get(user_id, 0)
        
        if user_count >= self.max_requests:
            return False
        
        # Add new request
        entry = RateLimitEntry(current_time, user_id)
        heapq.heappush(self.requests_heap, entry)
        self.user_counts[user_id] = user_count + 1
        
        return True
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Remove entries older than window using heap efficiency"""
        cutoff_time = current_time - self.window_seconds
        
        # Remove old entries from heap (min-heap keeps oldest at top)
        while self.requests_heap and self.requests_heap[0].timestamp < cutoff_time:
            old_entry = heapq.heappop(self.requests_heap)
            # Decrement user count
            if old_entry.user_id in self.user_counts:
                self.user_counts[old_entry.user_id] -= 1
                if self.user_counts[old_entry.user_id] <= 0:
                    del self.user_counts[old_entry.user_id]


### 2. **Database Query Optimization (Connection Pooling)**

from typing import Optional
import threading
import time

class DatabaseConnection:
    """Database connection wrapper with usage tracking"""
    
    def __init__(self, connection_id: str):
        self.connection_id = connection_id
        self.last_used = time.time()
        self.is_active = False
        self.query_count = 0
    
    def __lt__(self, other: 'DatabaseConnection') -> bool:
        """Compare by last used time for LRU cleanup"""
        return self.last_used < other.last_used
    
    def execute_query(self, query: str) -> str:
        """Simulate query execution"""
        self.last_used = time.time()
        self.query_count += 1
        return f"Query executed on {self.connection_id}"

class DatabaseConnectionPool:
    """Connection pool using heap for efficient LRU management"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.available_connections: List[DatabaseConnection] = []
        self.active_connections: Dict[str, DatabaseConnection] = {}
        self.lock = threading.Lock()
        
        # Initialize connection pool
        for i in range(max_connections):
            conn = DatabaseConnection(f"conn_{i}")
            heapq.heappush(self.available_connections, conn)
    
    def get_connection(self) -> Optional[DatabaseConnection]:
        """Get available connection (least recently used)"""
        with self.lock:
            if self.available_connections:
                # Get LRU connection from heap
                conn = heapq.heappop(self.available_connections)
                conn.is_active = True
                self.active_connections[conn.connection_id] = conn
                return conn
            return None
    
    def return_connection(self, connection_id: str) -> None:
        """Return connection to pool"""
        with self.lock:
            if connection_id in self.active_connections:
                conn = self.active_connections.pop(connection_id)
                conn.is_active = False
                conn.last_used = time.time()
                heapq.heappush(self.available_connections, conn)


### 3. **Real-time Chat Message Ordering**

from typing import List, Dict
from dataclasses import dataclass
import json

@dataclass
class ChatMessage:
    """Chat message with timestamp for ordering"""
    timestamp: float
    user_id: str
    message: str
    room_id: str
    
    def __lt__(self, other: 'ChatMessage') -> bool:
        return self.timestamp < other.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'message': self.message,
            'room_id': self.room_id
        }

class ChatMessageBuffer:
    """Buffer for handling out-of-order messages using heap"""
    
    def __init__(self, max_buffer_size: int = 1000):
        self.message_heap: List[ChatMessage] = []
        self.max_buffer_size = max_buffer_size
        self.last_processed_timestamp = 0.0
        self.buffer_window = 5.0  # 5 seconds buffer for out-of-order messages
    
    def add_message(self, message: ChatMessage) -> List[ChatMessage]:
        """Add message and return ready-to-process messages"""
        heapq.heappush(self.message_heap, message)
        
        # Limit buffer size for memory safety
        if len(self.message_heap) > self.max_buffer_size:
            # Force process oldest messages
            return self._force_process_oldest()
        
        return self._process_ready_messages()
    
    def _process_ready_messages(self) -> List[ChatMessage]:
        """Process messages that are ready (past buffer window)"""
        ready_messages = []
        current_time = time.time()
        
        while (self.message_heap and 
               current_time - self.message_heap[0].timestamp > self.buffer_window):
            message = heapq.heappop(self.message_heap)
            if message.timestamp > self.last_processed_timestamp:
                ready_messages.append(message)
                self.last_processed_timestamp = message.timestamp
        
        return ready_messages


## Big O Notation Analysis

# | Operation | Time Complexity | Space Complexity | Notes |
# |-----------|----------------|------------------|--------|
# | **Insert (heappush)** | O(log n) | O(1) | Bubbles up to maintain heap property |
# | **Extract Min/Max (heappop)** | O(log n) | O(1) | Bubbles down after removing root |
# | **Peek (heap[0])** | O(1) | O(1) | Just access first element |
# | **Build Heap (heapify)** | O(n) | O(1) | Floyd's algorithm, bottom-up |
# | **Search** | O(n) | O(1) | No ordering for search operations |
# | **Delete arbitrary** | O(n) | O(1) | Need to find element first |

### Performance Comparison:

import timeit
import random

def performance_comparison():
    """Compare heap vs other data structures"""
    
    # Test data
    data = [random.randint(1, 1000) for _ in range(10000)]
    
    # Heap operations
    def heap_operations():
        heap = []
        for item in data:
            heapq.heappush(heap, item)
        
        results = []
        while heap:
            results.append(heapq.heappop(heap))
        return results
    
    # List sorting (for comparison)
    def list_sorting():
        sorted_data = sorted(data)
        return sorted_data
    
    heap_time = timeit.timeit(heap_operations, number=100)
    sort_time = timeit.timeit(list_sorting, number=100)
    
    print(f"Heap operations: {heap_time:.4f}s")
    print(f"List sorting: {sort_time:.4f}s")
    print(f"Heap is {sort_time/heap_time:.2f}x faster for incremental sorting")


## When to Use Heaps

### ✅ **Perfect Use Cases:**
# 1. **Priority Queues**: Task scheduling, event processing
# 2. **Top-K Problems**: Finding k largest/smallest elements
# 3. **Streaming Data**: Median finding, percentile calculation
# 4. **Graph Algorithms**: Dijkstra's shortest path, Prim's MST
# 5. **Real-time Systems**: Event scheduling, rate limiting
# 6. **Memory Management**: LRU cache implementation

### ❌ **Avoid When:**
# 1. **Need Random Access**: Heaps don't support efficient indexing
# 2. **Frequent Searches**: O(n) search time, use hash tables instead
# 3. **Need All Elements Sorted**: Use sorting algorithms instead
# 4. **Small Datasets**: Overhead might not be worth it (<100 elements)
# 5. **Need Stable Sorting**: Heap sort is not stable

## Database Integration Patterns

### 1. **Connection Pool Management**

class DatabaseHeapManager:
    """Manages database connections using heap for optimization"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.connection_heap: List[DatabaseConnection] = []
        self.active_connections: Dict[str, DatabaseConnection] = {}
        self.db_config = db_config
    
    async def get_optimal_connection(self) -> Optional[DatabaseConnection]:
        """Get the most suitable connection based on load"""
        if not self.connection_heap:
            return await self._create_new_connection()
        
        # Get connection with least load (min-heap by query count)
        return heapq.heappop(self.connection_heap)
    
    async def _create_new_connection(self) -> DatabaseConnection:
        """Create new database connection with proper error handling"""
        try:
            # Simulate database connection creation
            conn = DatabaseConnection(f"conn_{len(self.active_connections)}")
            return conn
        except Exception as e:
            # Log security-safe error information
            print(f"Database connection failed: {type(e).__name__}")
            raise


### 2. **Query Result Caching**

from typing import Any, Tuple
import hashlib

class QueryResult:
    """Query result with priority for cache management"""
    
    def __init__(self, query_hash: str, result: Any, access_count: int = 1):
        self.query_hash = query_hash
        self.result = result
        self.access_count = access_count
        self.last_accessed = time.time()
    
    def __lt__(self, other: 'QueryResult') -> bool:
        """LRU comparison for cache eviction"""
        return self.last_accessed < other.last_accessed

class DatabaseQueryCache:
    """LRU cache for database queries using heap"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, QueryResult] = {}
        self.access_heap: List[QueryResult] = []
        self.max_size = max_size
    
    def get_query_result(self, query: str, params: Tuple[Any, ...]) -> Optional[Any]:
        """Get cached query result"""
        query_hash = self._hash_query(query, params)
        
        if query_hash in self.cache:
            result = self.cache[query_hash]
            result.access_count += 1
            result.last_accessed = time.time()
            return result.result
        
        return None
    
    def cache_query_result(self, query: str, params: Tuple[Any, ...], result: Any) -> None:
        """Cache query result with LRU eviction"""
        query_hash = self._hash_query(query, params)
        
        # Evict if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        query_result = QueryResult(query_hash, result)
        self.cache[query_hash] = query_result
        heapq.heappush(self.access_heap, query_result)
    
    def _hash_query(self, query: str, params: Tuple[Any, ...]) -> str:
        """Create secure hash for query + parameters"""
        # Use SHA-256 for security (avoid hash collisions)
        query_string = f"{query}|{str(params)}"
        return hashlib.sha256(query_string.encode()).hexdigest()
    
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        while self.access_heap:
            lru_item = heapq.heappop(self.access_heap)
            if lru_item.query_hash in self.cache:
                del self.cache[lru_item.query_hash]
                break


## Security Considerations

### 1. **Memory Safety**

class SecureHeap:
    """Heap with memory and security protections"""
    
    def __init__(self, max_size: int = 10000):
        self.heap: List[Any] = []
        self.max_size = max_size
        self._validate_max_size(max_size)
    
    def _validate_max_size(self, max_size: int) -> None:
        """Validate maximum size to prevent memory exhaustion"""
        if max_size <= 0 or max_size > 1_000_000:
            raise ValueError("Invalid heap size: must be between 1 and 1,000,000")
    
    def secure_push(self, item: Any) -> bool:
        """Push with size validation"""
        if len(self.heap) >= self.max_size:
            raise MemoryError("Heap size limit exceeded")
        
        # Validate item type and size
        if not self._validate_item(item):
            raise ValueError("Invalid item for heap")
        
        heapq.heappush(self.heap, item)
        return True
    
    def _validate_item(self, item: Any) -> bool:
        """Validate item before adding to heap"""
        # Check for basic types only
        allowed_types = (int, float, str, tuple)
        if not isinstance(item, allowed_types):
            return False
        
        # Check string length to prevent memory attacks
        if isinstance(item, str) and len(item) > 10000:
            return False
        
        return True


### 2. **Input Validation**

from typing import Union, Type

class ValidatedHeap:
    """Heap with comprehensive input validation"""
    
    def __init__(self, item_type: Type, max_size: int = 1000):
        self.heap: List[Any] = []
        self.item_type = item_type
        self.max_size = max_size
        self._insertion_count = 0
        self._max_insertions_per_second = 1000
        self._last_reset = time.time()
    
    def validated_push(self, item: Any) -> None:
        """Push with comprehensive validation"""
        self._rate_limit_check()
        self._validate_item_type(item)
        self._validate_heap_size()
        
        heapq.heappush(self.heap, item)
        self._insertion_count += 1
    
    def _rate_limit_check(self) -> None:
        """Prevent DOS attacks through rate limiting"""
        current_time = time.time()
        if current_time - self._last_reset > 1.0:
            self._insertion_count = 0
            self._last_reset = current_time
        
        if self._insertion_count >= self._max_insertions_per_second:
            raise Exception("Rate limit exceeded")
    
    def _validate_item_type(self, item: Any) -> None:
        """Validate item type matches expected type"""
        if not isinstance(item, self.item_type):
            raise TypeError(f"Expected {self.item_type.__name__}, got {type(item).__name__}")
    
    def _validate_heap_size(self) -> None:
        """Validate heap hasn't exceeded maximum size"""
        if len(self.heap) >= self.max_size:
            raise MemoryError("Heap size limit exceeded")


## Advantages and Disadvantages

### ✅ **Advantages:**
# 1. **Efficient Priority Operations**: O(log n) insert/extract
# 2. **Memory Efficient**: In-place array representation
# 3. **Partially Sorted**: Maintains order invariant without full sorting
# 4. **Real-time Capable**: Predictable performance for streaming data
# 5. **Cache Friendly**: Array-based storage improves cache locality
# 6. **Versatile**: Works with any comparable data type

### ❌ **Disadvantages:**
# 1. **No Random Access**: Can't efficiently access arbitrary elements
# 2. **Unstable**: Doesn't preserve original order for equal elements
# 3. **Search Inefficient**: O(n) time to find arbitrary elements
# 4. **No Decrease Key**: Standard heapq doesn't support priority updates
# 5. **Memory Overhead**: Requires additional space for heap maintenance
# 6. **Limited Ordering**: Only supports min-heap natively (need negation for max-heap)

## Advanced Patterns for Django/NextJS Integration

### 1. **WebSocket Message Prioritization**

# Django Channels consumer with heap-based message prioritization
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from typing import Dict, Any
import heapq
import asyncio

class PrioritizedMessage:
    """Message with priority for WebSocket handling"""
    
    def __init__(self, priority: int, message: Dict[str, Any], user_id: str):
        self.priority = priority
        self.message = message
        self.user_id = user_id
        self.timestamp = time.time()
    
    def __lt__(self, other: 'PrioritizedMessage') -> bool:
        # Higher priority first (reverse for min-heap)
        return self.priority > other.priority

class PrioritizedChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer with message prioritization"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_heap: List[PrioritizedMessage] = []
        self.processing_task: Optional[asyncio.Task] = None
    
    async def connect(self):
        await self.accept()
        # Start message processing task
        self.processing_task = asyncio.create_task(self._process_messages())
    
    async def disconnect(self, close_code):
        if self.processing_task:
            self.processing_task.cancel()
    
    async def receive(self, text_data):
        """Receive message and add to priority queue"""
        try:
            data = json.loads(text_data)
            priority = data.get('priority', 5)  # Default priority
            user_id = data.get('user_id')
            
            # Validate input
            if not user_id or not isinstance(priority, int):
                await self.send_error("Invalid message format")
                return
            
            message = PrioritizedMessage(priority, data, user_id)
            heapq.heappush(self.message_heap, message)
            
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            await self.send_error(f"Error processing message: {type(e).__name__}")
    
    async def _process_messages(self):
        """Process messages in priority order"""
        while True:
            try:
                if self.message_heap:
                    message = heapq.heappop(self.message_heap)
                    await self._handle_priority_message(message)
                else:
                    await asyncio.sleep(0.1)  # Small delay when no messages
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing message: {e}")
    
    async def _handle_priority_message(self, message: PrioritizedMessage):
        """Handle individual priority message"""
        # Process based on message type and priority
        response = {
            'type': 'priority_response',
            'priority': message.priority,
            'processed_at': time.time(),
            'original_message': message.message
        }
        
        await self.send(text_data=json.dumps(response))


# This comprehensive guide shows how heaps are powerful tools for managing ordered data efficiently, especially in real-time systems, database optimization, and API development. The key is understanding when the heap's strengths (efficient priority operations) outweigh its limitations (no random access) for your specific use case.

# 10 Heap Interview Questions with Detailed Solutions

## 🟢 Easy Questions (1-4)

### 1. **Find the Kth Largest Element in an Array**
# **Question:** Given an unsorted array, find the Kth largest element.


from typing import List
import heapq

def find_kth_largest(nums: List[int], k: int) -> int:
    """
    Find Kth largest element using min-heap approach.
    Time: O(n log k), Space: O(k)
    """
    # Input validation for security
    if not nums or k <= 0 or k > len(nums):
        raise ValueError("Invalid input parameters")
    
    # Use min-heap of size k
    # Keep only k largest elements, root will be kth largest
    min_heap: List[int] = []
    
    for num in nums:
        if len(min_heap) < k:
            heapq.heappush(min_heap, num)
        elif num > min_heap[0]:  # num is larger than kth largest so far
            heapq.heapreplace(min_heap, num)  # More efficient than pop+push
    
    return min_heap[0]

# Alternative solution using max-heap (for comparison)
def find_kth_largest_maxheap(nums: List[int], k: int) -> int:
    """
    Alternative using max-heap by negating values.
    Time: O(n log n), Space: O(n)
    """
    if not nums or k <= 0 or k > len(nums):
        raise ValueError("Invalid input parameters")
    
    # Convert to max-heap by negating values
    max_heap = [-num for num in nums]
    heapq.heapify(max_heap)
    
    # Pop k-1 elements to get kth largest
    for _ in range(k - 1):
        heapq.heappop(max_heap)
    
    return -max_heap[0]  # Convert back to positive

# Test cases
def test_kth_largest():
    # Test case 1: Basic example
    nums1 = [3, 2, 1, 5, 6, 4]
    k1 = 2
    assert find_kth_largest(nums1, k1) == 5
    print(f"✅ Test 1 passed: {nums1}, k={k1} → {find_kth_largest(nums1, k1)}")
    
    # Test case 2: Duplicates
    nums2 = [3, 2, 3, 1, 2, 4, 5, 5, 6]
    k2 = 4
    assert find_kth_largest(nums2, k2) == 4
    print(f"✅ Test 2 passed: {nums2}, k={k2} → {find_kth_largest(nums2, k2)}")
    
    # Test case 3: Edge case - single element
    nums3 = [1]
    k3 = 1
    assert find_kth_largest(nums3, k3) == 1
    print(f"✅ Test 3 passed: {nums3}, k={k3} → {find_kth_largest(nums3, k3)}")

test_kth_largest()


# **Key Insights:**
# - **Min-heap approach is more efficient** for large arrays with small k
# - **Heap size remains constant** at k, saving memory
# - **Security consideration**: Always validate input parameters

# ---

### 2. **Merge K Sorted Arrays**
# **Question:** Merge k sorted arrays into one sorted array.


from typing import List, Tuple
import heapq

def merge_k_sorted_arrays(arrays: List[List[int]]) -> List[int]:
    """
    Merge k sorted arrays using min-heap.
    Time: O(n log k) where n is total elements, k is number of arrays
    Space: O(k) for heap + O(n) for result
    """
    if not arrays:
        return []
    
    # Remove empty arrays for efficiency
    arrays = [arr for arr in arrays if arr]
    if not arrays:
        return []
    
    # Heap stores (value, array_index, element_index)
    heap: List[Tuple[int, int, int]] = []
    result: List[int] = []
    
    # Initialize heap with first element from each array
    for i, arr in enumerate(arrays):
        if arr:  # Check if array is not empty
            heapq.heappush(heap, (arr[0], i, 0))
    
    # Process all elements
    while heap:
        value, array_idx, element_idx = heapq.heappop(heap)
        result.append(value)
        
        # Add next element from same array if exists
        if element_idx + 1 < len(arrays[array_idx]):
            next_value = arrays[array_idx][element_idx + 1]
            heapq.heappush(heap, (next_value, array_idx, element_idx + 1))
    
    return result

# Real-world example: Merging database query results
class DatabaseQueryResult:
    """Represents a sorted query result from database"""
    
    def __init__(self, query_id: str, results: List[int]):
        self.query_id = query_id
        self.results = results
        self.processed_at = time.time()

def merge_database_results(query_results: List[DatabaseQueryResult]) -> List[int]:
    """
    Real-world application: Merge sorted results from multiple database shards
    """
    # Extract sorted arrays from query results
    sorted_arrays = [result.results for result in query_results if result.results]
    
    # Log for debugging (security: don't log sensitive data)
    print(f"Merging {len(sorted_arrays)} database query results")
    
    return merge_k_sorted_arrays(sorted_arrays)

# Test with realistic database scenario
def test_merge_k_arrays():
    # Simulate database shard results
    shard1_results = DatabaseQueryResult("shard1", [1, 4, 7, 10])
    shard2_results = DatabaseQueryResult("shard2", [2, 5, 8, 11])
    shard3_results = DatabaseQueryResult("shard3", [3, 6, 9, 12])
    
    query_results = [shard1_results, shard2_results, shard3_results]
    merged = merge_database_results(query_results)
    
    expected = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    assert merged == expected
    print(f"✅ Database merge test passed: {merged}")

test_merge_k_arrays()


# **Real-world Applications:**
# - **Database sharding**: Merge results from multiple database shards
# - **Log aggregation**: Combine sorted log files from multiple servers
# - **Search results**: Merge ranked results from different search indexes

# ---

### 3. **Check if Binary Tree is a Min-Heap**
# **Question:** Verify if a binary tree satisfies the min-heap property.


from typing import Optional
from dataclasses import dataclass

@dataclass
class TreeNode:
    """Binary tree node with type safety"""
    val: int
    left: Optional['TreeNode'] = None
    right: Optional['TreeNode'] = None

def is_min_heap(root: Optional[TreeNode]) -> bool:
    """
    Check if binary tree is a valid min-heap.
    Must satisfy: 1) Complete binary tree, 2) Min-heap property
    Time: O(n), Space: O(h) where h is height
    """
    if not root:
        return True
    
    # Check both complete tree property and heap property
    node_count = count_nodes(root)
    return (is_complete_tree(root, 0, node_count) and 
            satisfies_min_heap_property(root))

def count_nodes(root: Optional[TreeNode]) -> int:
    """Count total nodes in tree"""
    if not root:
        return 0
    return 1 + count_nodes(root.left) + count_nodes(root.right)

def is_complete_tree(root: Optional[TreeNode], index: int, node_count: int) -> bool:
    """
    Check if tree is complete using array indexing logic.
    In complete tree: left child at 2*i+1, right child at 2*i+2
    """
    if not root:
        return True
    
    # Index should be within bounds for complete tree
    if index >= node_count:
        return False
    
    # Recursively check left and right subtrees
    return (is_complete_tree(root.left, 2 * index + 1, node_count) and
            is_complete_tree(root.right, 2 * index + 2, node_count))

def satisfies_min_heap_property(root: Optional[TreeNode]) -> bool:
    """Check if tree satisfies min-heap property (parent <= children)"""
    if not root:
        return True
    
    # Check current node against its children
    if root.left and root.val > root.left.val:
        return False
    if root.right and root.val > root.right.val:
        return False
    
    # Recursively check subtrees
    return (satisfies_min_heap_property(root.left) and
            satisfies_min_heap_property(root.right))

# Advanced version with detailed error reporting
def validate_heap_with_details(root: Optional[TreeNode]) -> Tuple[bool, str]:
    """
    Validate heap with detailed error reporting for debugging.
    Returns (is_valid, error_message)
    """
    if not root:
        return True, "Empty tree is valid heap"
    
    # Check completeness
    node_count = count_nodes(root)
    if not is_complete_tree(root, 0, node_count):
        return False, "Tree is not complete"
    
    # Check heap property with node tracking
    violation_node = find_heap_property_violation(root)
    if violation_node:
        return False, f"Heap property violated at node with value {violation_node.val}"
    
    return True, "Valid min-heap"

def find_heap_property_violation(root: Optional[TreeNode]) -> Optional[TreeNode]:
    """Find the first node that violates heap property"""
    if not root:
        return None
    
    # Check current node
    if root.left and root.val > root.left.val:
        return root
    if root.right and root.val > root.right.val:
        return root
    
    # Check subtrees
    left_violation = find_heap_property_violation(root.left)
    if left_violation:
        return left_violation
    
    return find_heap_property_violation(root.right)

# Test cases
def test_heap_validation():
    # Test case 1: Valid min-heap
    #       1
    #      / \
    #     2   3
    #    / \
    #   4   5
    root1 = TreeNode(1)
    root1.left = TreeNode(2)
    root1.right = TreeNode(3)
    root1.left.left = TreeNode(4)
    root1.left.right = TreeNode(5)
    
    assert is_min_heap(root1) == True
    print("✅ Test 1 passed: Valid min-heap")
    
    # Test case 2: Invalid - heap property violation
    #       1
    #      / \
    #     0   3  (0 < 1, violates heap property)
    root2 = TreeNode(1)
    root2.left = TreeNode(0)
    root2.right = TreeNode(3)
    
    assert is_min_heap(root2) == False
    is_valid, error = validate_heap_with_details(root2)
    print(f"✅ Test 2 passed: {error}")
    
    # Test case 3: Invalid - incomplete tree
    #       1
    #      / \
    #     2   3
    #      \
    #       4  (incomplete - missing left child)
    root3 = TreeNode(1)
    root3.left = TreeNode(2)
    root3.right = TreeNode(3)
    root3.left.right = TreeNode(4)  # Missing left child
    
    assert is_min_heap(root3) == False
    print("✅ Test 3 passed: Incomplete tree detected")

test_heap_validation()


# **Key Concepts:**
# - **Complete tree**: All levels filled except possibly last, filled left to right
# - **Array indexing**: Left child at `2i+1`, right child at `2i+2`
# - **Heap property**: Parent value ≤ children values (min-heap)

# ---

### 4. **Last Stone Weight**
# **Question:** Given stones with weights, repeatedly smash the two heaviest stones until one or none remain.


import heapq
from typing import List

def last_stone_weight(stones: List[int]) -> int:
    """
    Find weight of last remaining stone using max-heap simulation.
    Time: O(n log n), Space: O(n)
    """
    if not stones:
        return 0
    
    # Convert to max-heap by negating values (heapq is min-heap)
    max_heap = [-stone for stone in stones]
    heapq.heapify(max_heap)
    
    # Process stones until 0 or 1 remains
    while len(max_heap) > 1:
        # Get two heaviest stones
        first = -heapq.heappop(max_heap)   # Heaviest
        second = -heapq.heappop(max_heap)  # Second heaviest
        
        # If stones have different weights, add the difference back
        if first != second:
            heapq.heappush(max_heap, -(first - second))
    
    # Return last stone weight or 0 if no stones left
    return -max_heap[0] if max_heap else 0

# Real-world application: Resource allocation system
class ResourceAllocation:
    """Simulate resource allocation using stone weight logic"""
    
    def __init__(self):
        self.resource_heap: List[int] = []
    
    def add_resource(self, capacity: int) -> None:
        """Add resource with given capacity"""
        if capacity <= 0:
            raise ValueError("Resource capacity must be positive")
        heapq.heappush(self.resource_heap, -capacity)  # Max-heap
    
    def allocate_resources(self, request1: int, request2: int) -> int:
        """
        Allocate resources to two requests, return remaining capacity.
        Simulates taking two largest resources and returning difference.
        """
        if len(self.resource_heap) < 2:
            raise ValueError("Need at least 2 resources for allocation")
        
        # Get two largest resources
        resource1 = -heapq.heappop(self.resource_heap)
        resource2 = -heapq.heappop(self.resource_heap)
        
        # Calculate remaining after allocation
        remaining1 = max(0, resource1 - request1)
        remaining2 = max(0, resource2 - request2)
        
        # Return unused resources to pool
        if remaining1 > 0:
            heapq.heappush(self.resource_heap, -remaining1)
        if remaining2 > 0:
            heapq.heappush(self.resource_heap, -remaining2)
        
        return remaining1 + remaining2

# Optimized version for large datasets
def last_stone_weight_optimized(stones: List[int]) -> int:
    """
    Optimized version with early termination and input validation.
    """
    # Input validation
    if not stones:
        return 0
    
    # Early termination for single stone
    if len(stones) == 1:
        return stones[0]
    
    # Use max-heap
    max_heap = [-stone for stone in stones if stone > 0]  # Filter invalid stones
    heapq.heapify(max_heap)
    
    # Process with optimizations
    while len(max_heap) > 1:
        first = -heapq.heappop(max_heap)
        second = -heapq.heappop(max_heap)
        
        # Only add back if there's a difference
        difference = first - second
        if difference > 0:
            heapq.heappush(max_heap, -difference)
    
    return -max_heap[0] if max_heap else 0

# Test cases with edge cases
def test_last_stone_weight():
    # Test case 1: Standard example
    stones1 = [2, 7, 4, 1, 8, 1]
    result1 = last_stone_weight(stones1)
    assert result1 == 1
    print(f"✅ Test 1 passed: {stones1} → {result1}")
    
    # Test case 2: All stones cancel out
    stones2 = [2, 2, 3, 3]
    result2 = last_stone_weight(stones2)
    assert result2 == 0
    print(f"✅ Test 2 passed: {stones2} → {result2}")
    
    # Test case 3: Single stone
    stones3 = [10]
    result3 = last_stone_weight(stones3)
    assert result3 == 10
    print(f"✅ Test 3 passed: {stones3} → {result3}")
    
    # Test case 4: Empty array
    stones4 = []
    result4 = last_stone_weight(stones4)
    assert result4 == 0
    print(f"✅ Test 4 passed: {stones4} → {result4}")
    
    # Test resource allocation
    allocator = ResourceAllocation()
    allocator.add_resource(100)
    allocator.add_resource(80)
    allocator.add_resource(60)
    
    remaining = allocator.allocate_resources(30, 20)
    print(f"✅ Resource allocation test: {remaining} units remaining")

test_last_stone_weight()


# **Problem-Solving Pattern:**
# - **Max-heap simulation**: Use negative values with min-heap
# - **Process pairs**: Always take two largest elements
# - **Early termination**: Optimize for edge cases

# ---

## 🟡 Normal Questions (5-7)

### 5. **Design a Twitter-like Timeline (Top K Recent Tweets)**
# **Question:** Design a system to get the k most recent tweets from multiple users' timelines.


import heapq
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class Tweet:
    """Tweet with timestamp for ordering"""
    tweet_id: str
    user_id: str
    content: str
    timestamp: float
    like_count: int = 0
    retweet_count: int = 0
    
    def __lt__(self, other: 'Tweet') -> bool:
        """Compare tweets by timestamp (newer first in max-heap)"""
        return self.timestamp > other.timestamp
    
    def __hash__(self) -> int:
        return hash(self.tweet_id)
    
    def to_dict(self) -> Dict:
        """Convert to dict for API response"""
        return {
            'tweet_id': self.tweet_id,
            'user_id': self.user_id,
            'content': self.content,
            'timestamp': self.timestamp,
            'like_count': self.like_count,
            'retweet_count': self.retweet_count
        }

class TwitterTimeline:
    """
    Twitter-like timeline system using heaps for efficient k-recent tweets.
    Handles following relationships and tweet ranking.
    """
    
    def __init__(self, max_timeline_size: int = 1000):
        self.users: Dict[str, Set[str]] = {}  # user_id -> set of following
        self.tweets: Dict[str, List[Tweet]] = {}  # user_id -> tweets
        self.max_timeline_size = max_timeline_size
        self.tweet_index: Dict[str, Tweet] = {}  # tweet_id -> tweet
    
    def follow_user(self, follower_id: str, followee_id: str) -> bool:
        """
        Create following relationship with validation.
        """
        # Input validation
        if not follower_id or not followee_id:
            raise ValueError("User IDs cannot be empty")
        
        if follower_id == followee_id:
            return False  # Can't follow yourself
        
        # Initialize user if not exists
        if follower_id not in self.users:
            self.users[follower_id] = set()
        
        self.users[follower_id].add(followee_id)
        return True
    
    def unfollow_user(self, follower_id: str, followee_id: str) -> bool:
        """Remove following relationship"""
        if follower_id in self.users and followee_id in self.users[follower_id]:
            self.users[follower_id].remove(followee_id)
            return True
        return False
    
    def post_tweet(self, user_id: str, content: str) -> str:
        """
        Post a tweet with timestamp and security validation.
        """
        # Security validation
        if not user_id or not content:
            raise ValueError("User ID and content cannot be empty")
        
        if len(content) > 280:  # Twitter limit
            raise ValueError("Tweet content exceeds 280 characters")
        
        # Generate tweet ID (in real system, use UUID)
        tweet_id = f"{user_id}_{int(time.time() * 1000)}"
        
        tweet = Tweet(
            tweet_id=tweet_id,
            user_id=user_id,
            content=content,
            timestamp=time.time()
        )
        
        # Add to user's tweets
        if user_id not in self.tweets:
            self.tweets[user_id] = []
        
        self.tweets[user_id].append(tweet)
        self.tweet_index[tweet_id] = tweet
        
        # Keep only recent tweets for memory efficiency
        if len(self.tweets[user_id]) > self.max_timeline_size:
            old_tweet = self.tweets[user_id].pop(0)
            del self.tweet_index[old_tweet.tweet_id]
        
        return tweet_id
    
    def get_timeline(self, user_id: str, k: int = 10) -> List[Tweet]:
        """
        Get k most recent tweets from followed users using heap.
        Time: O(n log k) where n is total tweets from followed users
        """
        if user_id not in self.users:
            return []
        
        # Get all tweets from followed users
        followed_users = self.users[user_id]
        all_tweets: List[Tweet] = []
        
        # Collect tweets from all followed users
        for followee_id in followed_users:
            if followee_id in self.tweets:
                all_tweets.extend(self.tweets[followee_id])
        
        # Add user's own tweets
        if user_id in self.tweets:
            all_tweets.extend(self.tweets[user_id])
        
        # Use min-heap to get k most recent tweets
        if len(all_tweets) <= k:
            return sorted(all_tweets, key=lambda t: t.timestamp, reverse=True)
        
        # Use heap to efficiently get k most recent
        min_heap: List[Tweet] = []
        
        for tweet in all_tweets:
            if len(min_heap) < k:
                heapq.heappush(min_heap, tweet)
            elif tweet.timestamp > min_heap[0].timestamp:
                heapq.heapreplace(min_heap, tweet)
        
        # Convert to list and sort by timestamp (newest first)
        result = sorted(min_heap, key=lambda t: t.timestamp, reverse=True)
        return result
    
    def get_trending_tweets(self, k: int = 10) -> List[Tweet]:
        """
        Get trending tweets based on engagement (likes + retweets).
        Uses heap for efficient top-k selection.
        """
        if not self.tweet_index:
            return []
        
        # Create engagement score heap
        engagement_heap: List[Tuple[int, Tweet]] = []
        
        for tweet in self.tweet_index.values():
            engagement_score = tweet.like_count + tweet.retweet_count
            
            if len(engagement_heap) < k:
                heapq.heappush(engagement_heap, (engagement_score, tweet))
            elif engagement_score > engagement_heap[0][0]:
                heapq.heapreplace(engagement_heap, (engagement_score, tweet))
        
        # Sort by engagement score (highest first)
        trending_tweets = [tweet for _, tweet in engagement_heap]
        trending_tweets.sort(key=lambda t: t.like_count + t.retweet_count, reverse=True)
        
        return trending_tweets

# Real-world application: News aggregator
class NewsAggregator:
    """
    News aggregator using similar heap-based approach for article ranking.
    """
    
    def __init__(self):
        self.articles: Dict[str, List[Tweet]] = {}
        self.user_preferences: Dict[str, Set[str]] = {}
    
    def add_user_preference(self, user_id: str, category: str) -> None:
        """Add user's preferred news category"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = set()
        self.user_preferences[user_id].add(category)
    
    def get_personalized_news(self, user_id: str, k: int = 10) -> List[Tweet]:
        """
        Get personalized news based on user preferences using heap ranking.
        """
        if user_id not in self.user_preferences:
            return []
        
        preferred_categories = self.user_preferences[user_id]
        candidate_articles: List[Tweet] = []
        
        # Collect articles from preferred categories
        for category in preferred_categories:
            if category in self.articles:
                candidate_articles.extend(self.articles[category])
        
        # Use heap to get top k articles
        if len(candidate_articles) <= k:
            return sorted(candidate_articles, key=lambda a: a.timestamp, reverse=True)
        
        # Heap-based selection
        article_heap: List[Tweet] = []
        
        for article in candidate_articles:
            if len(article_heap) < k:
                heapq.heappush(article_heap, article)
            elif article.timestamp > article_heap[0].timestamp:
                heapq.heapreplace(article_heap, article)
        
        return sorted(article_heap, key=lambda a: a.timestamp, reverse=True)

# Performance testing
def test_twitter_timeline():
    """Test Twitter timeline system with realistic data"""
    
    timeline = TwitterTimeline()
    
    # Create users and following relationships
    users = ['alice', 'bob', 'charlie', 'diana', 'eve']
    
    # Alice follows Bob and Charlie
    timeline.follow_user('alice', 'bob')
    timeline.follow_user('alice', 'charlie')
    
    # Bob follows Charlie and Diana
    timeline.follow_user('bob', 'charlie')
    timeline.follow_user('bob', 'diana')
    
    # Post tweets
    tweets = [
        ('bob', 'Just finished my morning coffee ☕'),
        ('charlie', 'Working on a new Python project 🐍'),
        ('diana', 'Beautiful sunset today 🌅'),
        ('bob', 'Debugging is like detective work 🔍'),
        ('charlie', 'Love the new Django features!'),
        ('alice', 'First tweet! Hello world 👋'),
    ]
    
    for user_id, content in tweets:
        timeline.post_tweet(user_id, content)
        time.sleep(0.1)  # Small delay for timestamp differentiation
    
    # Get Alice's timeline
    alice_timeline = timeline.get_timeline('alice', k=5)
    print(f"✅ Alice's timeline ({len(alice_timeline)} tweets):")
    for tweet in alice_timeline:
        print(f"  @{tweet.user_id}: {tweet.content}")
    
    # Test trending tweets (simulate some engagement)
    for tweet_id, tweet in timeline.tweet_index.items():
        if 'Python' in tweet.content or 'Django' in tweet.content:
            tweet.like_count = 50
            tweet.retweet_count = 20
    
    trending = timeline.get_trending_tweets(k=3)
    print(f"\n✅ Trending tweets ({len(trending)} tweets):")
    for tweet in trending:
        engagement = tweet.like_count + tweet.retweet_count
        print(f"  @{tweet.user_id}: {tweet.content} ({engagement} engagement)")

test_twitter_timeline()


# **System Design Insights:**
# - **Heap for k-recent**: More efficient than sorting entire dataset
# - **Memory management**: Limit stored tweets per user
# - **Security validation**: Input sanitization and rate limiting
# - **Scalability**: Can be extended with caching and sharding

# ---

from typing import List, Deque, Tuple, Optional, Dict, Any
from collections import deque
import heapq
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
from decimal import Decimal, ROUND_HALF_UP

# Configure logging for monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sliding_window_maximum_heap(nums: List[int], k: int) -> List[int]:
    """
    Find sliding window maximum using heap approach.
    Time: O(n log k), Space: O(k)
    
    How it works internally:
    1. Use max-heap to efficiently track maximum in current window
    2. Store (negative_value, index) pairs to handle duplicates and window bounds
    3. Lazy deletion: remove outdated elements only when accessing heap top
    
    Args:
        nums: Input array of integers
        k: Window size (must be positive and <= len(nums))
    
    Returns:
        List of maximum values for each window position
    
    Raises:
        ValueError: If k is invalid or nums is empty
    """
    # Input validation for security
    if not nums or k <= 0:
        raise ValueError("Invalid input: nums must be non-empty and k must be positive")
    
    if k > len(nums):
        raise ValueError(f"Window size {k} cannot be larger than array length {len(nums)}")
    
    if k >= len(nums):
        return [max(nums)]
    
    result: List[int] = []
    # Use max-heap (negate values for min-heap implementation)
    # Store (negative_value, index) to handle duplicates and window bounds
    max_heap: List[Tuple[int, int]] = []
    
    # Process first window
    for i in range(k):
        heapq.heappush(max_heap, (-nums[i], i))
    
    # Maximum of first window
    result.append(-max_heap[0][0])
    
    # Process remaining elements
    for i in range(k, len(nums)):
        # Add new element to heap
        heapq.heappush(max_heap, (-nums[i], i))
        
        # Lazy deletion: remove elements outside current window
        while max_heap and max_heap[0][1] <= i - k:
            heapq.heappop(max_heap)
        
        # Current window maximum
        result.append(-max_heap[0][0])
    
    return result

def sliding_window_maximum_deque(nums: List[int], k: int) -> List[int]:
    """
    Optimized solution using deque (monotonic decreasing queue).
    Time: O(n), Space: O(k)
    
    How it works internally:
    1. Maintain deque with indices in decreasing order of their values
    2. Front of deque always contains index of maximum element in current window
    3. Remove indices that are outside current window from front
    4. Remove indices with smaller values from back (they can never be maximum)
    
    This is optimal for real-time processing as each element is added/removed at most once.
    """
    # Input validation
    if not nums or k <= 0:
        raise ValueError("Invalid input: nums must be non-empty and k must be positive")
    
    if k > len(nums):
        raise ValueError(f"Window size {k} cannot be larger than array length {len(nums)}")
    
    # Deque stores indices, maintains decreasing order of values
    dq: Deque[int] = deque()
    result: List[int] = []
    
    for i, num in enumerate(nums):
        # Remove indices outside current window from front
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # Remove indices with smaller values from back
        # They can never be maximum while current element is in window
        while dq and nums[dq[-1]] <= num:
            dq.pop()
        
        # Add current index
        dq.append(i)
        
        # Add result for current window (when we have processed k elements)
        if i >= k - 1:
            result.append(nums[dq[0]])  # Front has maximum
    
    return result

@dataclass
class PriceData:
    """Data structure for stock price with timestamp and validation."""
    price: Decimal
    timestamp: datetime
    volume: int = 0
    
    def __post_init__(self):
        """Validate price data for security."""
        if self.price < 0:
            raise ValueError("Price cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

class StockPriceMonitor:
    """
    Monitor stock prices and track maximum price in sliding windows.
    
    Real-world applications:
    1. Trading algorithms: Identify resistance levels
    2. Risk management: Track maximum loss in time windows
    3. Market analysis: Detect price breakouts
    4. Automated alerts: Trigger when price exceeds recent maximum
    
    Security considerations:
    - Input validation for all price data
    - Thread-safe operations for concurrent access
    - Decimal arithmetic for financial precision
    - Rate limiting to prevent abuse
    """
    
    def __init__(self, window_size: int = 20, max_history: int = 10000):
        """
        Initialize stock price monitor.
        
        Args:
            window_size: Number of recent prices to consider (default: 20)
            max_history: Maximum number of prices to store (prevents memory exhaustion)
        """
        if window_size <= 0:
            raise ValueError("Window size must be positive")
        if max_history <= 0:
            raise ValueError("Max history must be positive")
            
        self.window_size = window_size
        self.max_history = max_history
        self.prices: List[PriceData] = []
        self.price_values: List[Decimal] = []  # For efficient sliding window calculation
        self.dq: Deque[int] = deque()  # Indices for sliding window maximum
        self._lock = threading.Lock()  # Thread safety
        
        logger.info(f"Stock monitor initialized with window_size={window_size}")
    
    def add_price(self, price: float, timestamp: Optional[datetime] = None, volume: int = 0) -> None:
        """
        Add new price data point.
        
        Args:
            price: Stock price (converted to Decimal for precision)
            timestamp: When price was recorded (defaults to now)
            volume: Trading volume
        """
        with self._lock:  # Thread-safe operation
            try:
                # Convert to Decimal for financial precision
                decimal_price = Decimal(str(price)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                price_data = PriceData(
                    price=decimal_price,
                    timestamp=timestamp or datetime.now(),
                    volume=volume
                )
                
                # Add to history
                self.prices.append(price_data)
                self.price_values.append(decimal_price)
                
                # Maintain maximum history to prevent memory exhaustion
                if len(self.prices) > self.max_history:
                    self.prices.pop(0)
                    self.price_values.pop(0)
                    # Adjust deque indices
                    self.dq = deque(idx - 1 for idx in self.dq if idx > 0)
                
                # Update sliding window maximum deque
                current_idx = len(self.price_values) - 1
                
                # Remove indices outside current window
                while self.dq and self.dq[0] <= current_idx - self.window_size:
                    self.dq.popleft()
                
                # Remove indices with smaller prices
                while self.dq and self.price_values[self.dq[-1]] <= decimal_price:
                    self.dq.pop()
                
                self.dq.append(current_idx)
                
                logger.info(f"Price added: {decimal_price} at {price_data.timestamp}")
                
            except Exception as e:
                logger.error(f"Error adding price: {e}")
                raise
    
    def get_current_maximum(self) -> Optional[Decimal]:
        """Get maximum price in current sliding window."""
        with self._lock:
            if not self.dq or not self.price_values:
                return None
            return self.price_values[self.dq[0]]
    
    def get_window_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for current window."""
        with self._lock:
            if len(self.price_values) < self.window_size:
                window_prices = self.price_values
            else:
                window_prices = self.price_values[-self.window_size:]
            
            if not window_prices:
                return {}
            
            return {
                "maximum": max(window_prices),
                "minimum": min(window_prices),
                "average": sum(window_prices) / len(window_prices),
                "window_size": len(window_prices),
                "total_volume": sum(p.volume for p in self.prices[-len(window_prices):])
            }
    
    def detect_breakout(self, threshold_percentage: float = 5.0) -> bool:
        """
        Detect price breakout above recent maximum.
        
        Args:
            threshold_percentage: Percentage above recent max to trigger breakout
            
        Returns:
            True if current price is a breakout
        """
        with self._lock:
            if len(self.price_values) < self.window_size:
                return False
            
            current_price = self.price_values[-1]
            # Get maximum of previous window (excluding current price)
            prev_window_max = max(self.price_values[-self.window_size-1:-1])
            
            threshold = prev_window_max * (1 + threshold_percentage / 100)
            return current_price > threshold

# Performance comparison and testing
def benchmark_algorithms(sizes: List[int] = [1000, 5000, 10000]) -> None:
    """
    Benchmark different sliding window maximum algorithms.
    
    This helps understand performance characteristics for different data sizes.
    """
    import random
    
    print("=== Sliding Window Maximum Benchmark ===")
    print(f"{'Size':<8} {'K':<4} {'Heap Time':<12} {'Deque Time':<12} {'Speedup':<10}")
    print("-" * 50)
    
    for size in sizes:
        # Generate test data
        nums = [random.randint(1, 1000) for _ in range(size)]
        k = min(100, size // 10)  # Reasonable window size
        
        # Benchmark heap approach
        start_time = time.time()
        result_heap = sliding_window_maximum_heap(nums, k)
        heap_time = time.time() - start_time
        
        # Benchmark deque approach
        start_time = time.time()
        result_deque = sliding_window_maximum_deque(nums, k)
        deque_time = time.time() - start_time
        
        # Verify results are identical
        assert result_heap == result_deque, "Algorithm results don't match!"
        
        speedup = heap_time / deque_time if deque_time > 0 else float('inf')
        print(f"{size:<8} {k:<4} {heap_time:<12.4f} {deque_time:<12.4f} {speedup:<10.2f}x")

def demo_real_world_usage():
    """Demonstrate real-world usage scenarios."""
    print("\n=== Real-World Usage Examples ===")
    
    # 1. Stock Price Monitoring
    print("\n1. Stock Price Monitoring:")
    monitor = StockPriceMonitor(window_size=5)
    
    # Simulate real-time price updates
    test_prices = [100.50, 101.25, 99.75, 102.00, 98.50, 103.25, 101.75]
    
    for price in test_prices:
        monitor.add_price(price)
        stats = monitor.get_window_statistics()
        current_max = monitor.get_current_maximum()
        breakout = monitor.detect_breakout(threshold_percentage=2.0)
        
        print(f"Price: ${price:6.2f} | Max: ${current_max:6.2f} | "
              f"Avg: ${stats.get('average', 0):6.2f} | Breakout: {breakout}")
    
    # 2. Web Application Response Time Monitoring
    print("\n2. Response Time Monitoring (simulated):")
    response_times = [120, 150, 180, 95, 200, 175, 145, 190, 160, 135]
    window_size = 4
    
    max_response_times = sliding_window_maximum_deque(response_times, window_size)
    
    print(f"{'Time':<8} {'Response':<10} {'Max (4-window)':<15} {'Status':<10}")
    print("-" * 45)
    
    for i, (response, max_time) in enumerate(zip(response_times, max_response_times)):
        status = "ALERT" if max_time > 180 else "OK"
        print(f"{i+1:<8} {response:<10} {max_time:<15} {status:<10}")

# Advanced: Sliding Window Maximum for 2D Arrays
def sliding_window_maximum_2d(matrix: List[List[int]], k: int) -> List[List[int]]:
    """
    Find sliding window maximum in 2D matrix.
    
    Real-world application: Image processing, finding maximum values in sliding windows
    for feature detection, noise reduction, or pattern recognition.
    
    Time: O(m * n), Space: O(k)
    """
    if not matrix or not matrix[0] or k <= 0:
        return []
    
    rows, cols = len(matrix), len(matrix[0])
    if k > rows or k > cols:
        return []
    
    result = []
    
    # Process each possible k×k window
    for i in range(rows - k + 1):
        row_result = []
        for j in range(cols - k + 1):
            # Find maximum in current k×k window
            window_max = float('-inf')
            for r in range(i, i + k):
                for c in range(j, j + k):
                    window_max = max(window_max, matrix[r][c])
            row_result.append(window_max)
        result.append(row_result)
    
    return result

if __name__ == "__main__":
    # Run comprehensive tests and demonstrations
    try:
        # Basic functionality test
        test_array = [1, 3, -1, -3, 5, 3, 6, 7]
        k = 3
        
        print("=== Basic Sliding Window Maximum Test ===")
        print(f"Array: {test_array}")
        print(f"Window size: {k}")
        
        result_heap = sliding_window_maximum_heap(test_array, k)
        result_deque = sliding_window_maximum_deque(test_array, k)
        
        print(f"Heap result:  {result_heap}")
        print(f"Deque result: {result_deque}")
        print(f"Results match: {result_heap == result_deque}")
        
        # Performance benchmark
        benchmark_algorithms()
        
        # Real-world demonstrations
        demo_real_world_usage()
        
        # 2D sliding window example
        print("\n=== 2D Sliding Window Maximum ===")
        matrix = [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
            [13, 14, 15, 16]
        ]
        result_2d = sliding_window_maximum_2d(matrix, 2)
        print(f"2D Matrix sliding window maximum (2×2): {result_2d}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

####

# Django REST API endpoint
@api_view(['POST'])
def analyze_stock_prices(request):
    monitor = StockPriceMonitor(window_size=20)
    prices = request.data.get('prices', [])
    
    # Process prices securely
    for price_data in prices:
        monitor.add_price(
            price=price_data['price'],
            timestamp=datetime.fromisoformat(price_data['timestamp']),
            volume=price_data.get('volume', 0)
        )
    
    return Response({
        'current_maximum': monitor.get_current_maximum(),
        'statistics': monitor.get_window_statistics(),
        'breakout_detected': monitor.detect_breakout()
    })