# A **queue** is a linear data structure that follows the **First-In-First-Out (FIFO)** principle, meaning the first element added to the queue is the first one to be removed. It operates like a real-world queue, such as people waiting in line at a ticket counter. In this explanation, I’ll provide a detailed overview of queues, implement one in Python without using the built-in `deque` module, discuss its use cases, advantages, disadvantages, Big O notation, database integration, security considerations, and provide a real-world code example.

# ---

# ### **1. Queue Implementation in Python (Without `deque`)**
# We’ll implement a queue using a Python **list** as the underlying data structure. 
# The queue will support basic operations: enqueue (add), dequeue (remove), peek (view front element), 
# and check if empty.


class Queue:
    def __init__(self):
        self.queue = []  # Initialize an empty list to store queue elements

    def enqueue(self, item):
        """Add an item to the rear of the queue."""
        self.queue.append(item)

    def dequeue(self):
        """Remove and return the front item from the queue."""
        if self.is_empty():
            raise IndexError("Cannot dequeue from an empty queue")
        return self.queue.pop(0)  # Remove the first element (front)

    def peek(self):
        """Return the front item without removing it."""
        if self.is_empty():
            raise IndexError("Cannot peek an empty queue")
        return self.queue[0]

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.queue) == 0

    def size(self):
        """Return the number of items in the queue."""
        return len(self.queue)

    def __str__(self):
        """Return a string representation of the queue."""
        return str(self.queue)


#### **How It Works**
# - **Enqueue**: Adds an item to the end of the list (`O(1)` time complexity).
# - **Dequeue**: Removes the first element from the list (`O(n)` time complexity due to shifting elements).
# - **Peek**: Returns the first element without removing it (`O(1)`).
# - **is_empty**: Checks if the queue is empty (`O(1)`).
# - **size**: Returns the number of elements (`O(1)`).

# This implementation uses a list, but note that Python’s `list.pop(0)` is inefficient for large queues because 
# it shifts all remaining elements, leading to `O(n)` complexity for dequeue.

# ---

# ### **2. Where Queues Can Be Used**
# Queues are widely used in scenarios requiring FIFO processing. Common use cases include:
# - **Task Scheduling**: Managing tasks in operating systems (e.g., CPU process scheduling).
# - **Message Queues**: Handling messages in systems like RabbitMQ, Kafka, or AWS SQS for asynchronous communication.
# - **Breadth-First Search (BFS)**: Graph traversal algorithms use queues to explore nodes level by level.
# - **Print Queue**: Managing print jobs in a printer.
# - **Real-Time Systems**: Buffering data streams, such as video or audio streaming.
# - **Event Handling**: Processing user inputs or events in GUI applications.
# - **Network Packet Processing**: Routers and switches use queues to manage packet transmission.

# #### **Where Queues Should Not Be Used**
# - **Random Access**: Queues are not suitable when you need to access elements in the middle or at arbitrary positions (use arrays or lists instead).
# - **LIFO Operations**: If Last-In-First-Out (LIFO) behavior is needed, use a stack.
# - **Priority-Based Processing**: If elements need to be processed based on priority, use a **priority queue** instead.
# - **Large-Scale Dequeue Operations**: The list-based queue implementation is inefficient for frequent dequeue operations due to `O(n)` complexity.

# ---

# ### **3. Real-World Code Example**
# Here’s an example of a queue used to simulate a **task queue** in a simplified task management system, where tasks are processed in the order they are received.


class TaskQueue:
    def __init__(self):
        self.queue = []

    def enqueue_task(self, task):
        """Add a task to the queue."""
        self.queue.append(task)
        print(f"Task '{task}' added to the queue.")

    def process_task(self):
        """Process the next task in the queue."""
        if not self.queue:
            return "No tasks to process."
        task = self.queue.pop(0)
        print(f"Processing task: {task}")
        return task

    def is_empty(self):
        """Check if the task queue is empty."""
        return len(self.queue) == 0

# Example usage: Simulating a task management system
def main():
    task_queue = TaskQueue()

    # Adding tasks to the queue
    task_queue.enqueue_task("Send email to client")
    task_queue.enqueue_task("Generate report")
    task_queue.enqueue_task("Update database")
    task_queue.enqueue_task("Backup files")

    # Processing tasks in FIFO order
    print("\nProcessing tasks:")
    while not task_queue.is_empty():
        task_queue.process_task()

if __name__ == "__main__":
    main()


# **Output**:
# 
# Task 'Send email to client' added to the queue.
# Task 'Generate report' added to the queue.
# Task 'Update database' added to the queue.
# Task 'Backup files' added to the queue.

# Processing tasks:
# Processing task: Send email to client
# Processing task: Generate report
# Processing task: Update database
# Processing task: Backup files
# 

# This simulates a system where tasks (e.g., in a job scheduler) are processed in the order they are received.

# ---

# ### **4. Advantages of Queues**
# - **FIFO Semantics**: Ensures fair processing of elements in the order they arrive.
# - **Simplicity**: Easy to implement and understand for FIFO-based applications.
# - **Scalability in Distributed Systems**: Queues are ideal for decoupling components in distributed systems (e.g., producer-consumer patterns).
# - **Thread-Safe Variants**: Can be extended with locks for concurrent access in multithreaded environments.
# - **Buffering**: Useful for smoothing out bursts of data or tasks (e.g., in message queues).

# #### **Disadvantages**
# - **Inefficient Dequeue with Lists**: Using a Python list, `dequeue` is `O(n)` due to element shifting.
# - **Limited Access**: Only allows access to the front and rear, not suitable for random access.
# - **Memory Overhead**: Inefficient for large datasets if not optimized (e.g., list resizing in Python).
# - **Not Suitable for Priority Tasks**: Standard queues don’t support prioritizing elements.
# - **Concurrency Challenges**: Requires additional mechanisms (e.g., locks) for thread safety, which can add complexity.

# ---

# ### **5. Big O Notation**
# The time complexity of queue operations (using a list-based implementation) is:
# - **Enqueue**: `O(1)` (appending to the end of the list).
# - **Dequeue**: `O(n)` (removing the first element requires shifting all others).
# - **Peek**: `O(1)` (accessing the first element).
# - **is_empty**: `O(1)` (checking list length).
# - **size**: `O(1)` (getting list length).

# **Optimization Note**: To improve dequeue performance to `O(1)`, use a **linked list** or a **circular buffer**. 
# A linked list implementation would store nodes with pointers, allowing constant-time removal from the front.

# ---

# ### **6. Using Queues with Database Connections**
# Queues can be integrated with database systems to manage tasks or data processing. For example:
# - **Task Queuing**: A queue can hold database queries or updates to be executed sequentially, preventing overload on the database server.
# - **Connection Pooling**: A queue can manage database connection requests, ensuring connections are allocated in order.
# - **Asynchronous Processing**: Queues can store database tasks (e.g., logging user actions) to be processed by a background worker.

# #### **Example: Queue with Database**
# Here’s a simplified example using SQLite to queue and process database operations.


import sqlite3
from time import sleep

class DatabaseQueue:
    def __init__(self, db_name):
        self.queue = []
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Create a table to store processed tasks."""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                              (id INTEGER PRIMARY KEY, task TEXT, status TEXT)''')
        self.conn.commit()

    def enqueue_task(self, task):
        """Add a task to the queue."""
        self.queue.append(task)
        print(f"Task '{task}' enqueued.")

    def process_tasks(self):
        """Process tasks by inserting them into the database."""
        while self.queue:
            task = self.queue.pop(0)
            self.cursor.execute("INSERT INTO tasks (task, status) VALUES (?, ?)",
                               (task, "Processed"))
            self.conn.commit()
            print(f"Task '{task}' processed and stored in database.")
            sleep(1)  # Simulate processing time

    def close(self):
        """Close the database connection."""
        self.conn.close()

# Example usage
db_queue = DatabaseQueue("tasks.db")
db_queue.enqueue_task("Insert user data")
db_queue.enqueue_task("Update analytics")
db_queue.process_tasks()
db_queue.close()


# **Explanation**:
# - Tasks are enqueued and then processed by inserting them into an SQLite database.
# - The queue ensures tasks are processed in order, preventing race conditions or database overload.
# - This approach is useful for background jobs, such as logging or batch updates.

# ---

# ### **7. Security Considerations**
# When using queues, especially with database integration or in distributed systems, consider:
# - **Input Validation**: Validate data before enqueuing to prevent injection attacks (e.g., SQL injection for database tasks).
# - **Thread Safety**: Use locks or thread-safe queue implementations (e.g., Python’s `queue.Queue` for multithreading) to avoid race conditions.
# - **Data Sensitivity**: Encrypt sensitive data in the queue if it contains personal or confidential information.
# - **Queue Overflow**: Implement size limits to prevent memory exhaustion in high-throughput systems.
# - **Authentication/Authorization**: Ensure only authorized processes can enqueue or dequeue tasks, especially in distributed systems.
# - **Logging**: Log queue operations for auditing and debugging, but avoid logging sensitive data.

# ---

# ### **8. Improving the Implementation**
# To address the `O(n)` dequeue issue, you can implement a queue using a **linked list**:


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedListQueue:
    def __init__(self):
        self.front = None
        self.rear = None
        self._size = 0

    def enqueue(self, item):
        node = Node(item)
        if self.is_empty():
            self.front = node
            self.rear = node
        else:
            self.rear.next = node
            self.rear = node
        self._size += 1

    def dequeue(self):
        if self.is_empty():
            raise IndexError("Cannot dequeue from an empty queue")
        item = self.front.data
        self.front = self.front.next
        self._size -= 1
        if self.is_empty():
            self.rear = None
        return item

    def peek(self):
        if self.is_empty():
            raise IndexError("Cannot peek an empty queue")
        return self.front.data

    def is_empty(self):
        return self._size == 0

    def size(self):
        return self._size


# **Big O for Linked List Queue**:
# - Enqueue: `O(1)`
# - Dequeue: `O(1)`
# - Peek: `O(1)`
# - is_empty: `O(1)`
# - size: `O(1)`

# This implementation is more efficient for dequeue operations but requires more memory due to node pointers.

# ---

### **9. Conclusion**
# Queues are a fundamental data structure for managing FIFO-based workflows. 
# While the list-based implementation is simple, it’s inefficient for dequeue operations. 
# A linked list or circular buffer can optimize performance. 
# Queues are versatile, used in task scheduling, message processing, and database integration, but they require careful handling for concurrency and security. By understanding their strengths, limitations, and proper use cases, you can effectively apply queues to solve real-world problems.

# If you have further questions or need a specific use case explored, let me know!

#---

# I'll provide a comprehensive explanation of queues in Python, covering all the aspects you mentioned.

## What is a Queue?

# A queue is a linear data structure that follows the **First In, First Out (FIFO)** principle. Think of it like a line at a coffee shop - the first person in line is the first person served.

## Queue Implementation in Python## Where Queues Are Used

from collections import deque
import threading
import time
from typing import Any, Optional, Generic, TypeVar
from dataclasses import dataclass
import asyncio
import aioredis
from datetime import datetime

T = TypeVar('T')

# 1. Basic Queue Implementation using List (Not Recommended for Production)
class BasicQueue:
    """
    Basic queue implementation using Python list.
    WARNING: Not efficient for large queues due to O(n) dequeue operation
    """
    def __init__(self):
        self.items: list = []
    
    def enqueue(self, item: Any) -> None:
        """Add item to the rear of queue - O(1)"""
        self.items.append(item)
    
    def dequeue(self) -> Any:
        """Remove and return item from front - O(n) due to list.pop(0)"""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items.pop(0)  # This is O(n) operation!
    
    def front(self) -> Any:
        """Return front item without removing - O(1)"""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items[0]
    
    def is_empty(self) -> bool:
        """Check if queue is empty - O(1)"""
        return len(self.items) == 0
    
    def size(self) -> int:
        """Return queue size - O(1)"""
        return len(self.items)

# 2. Efficient Queue Implementation using collections.deque
class EfficientQueue(Generic[T]):
    """
    Efficient queue implementation using collections.deque.
    All operations are O(1) - RECOMMENDED for production use
    """
    def __init__(self):
        self._queue: deque[T] = deque()
    
    def enqueue(self, item: T) -> None:
        """Add item to the rear of queue - O(1)"""
        self._queue.append(item)
    
    def dequeue(self) -> T:
        """Remove and return item from front - O(1)"""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self._queue.popleft()
    
    def front(self) -> T:
        """Return front item without removing - O(1)"""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self._queue[0]
    
    def is_empty(self) -> bool:
        """Check if queue is empty - O(1)"""
        return len(self._queue) == 0
    
    def size(self) -> int:
        """Return queue size - O(1)"""
        return len(self._queue)

# 3. Thread-Safe Queue Implementation
class ThreadSafeQueue(Generic[T]):
    """
    Thread-safe queue implementation using threading.Lock.
    Safe for concurrent access from multiple threads.
    """
    def __init__(self, maxsize: int = 0):
        self._queue: deque[T] = deque()
        self._lock = threading.Lock()
        self._maxsize = maxsize
    
    def enqueue(self, item: T, timeout: Optional[float] = None) -> bool:
        """Add item to queue with optional timeout - O(1)"""
        with self._lock:
            if self._maxsize > 0 and len(self._queue) >= self._maxsize:
                return False  # Queue is full
            self._queue.append(item)
            return True
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[T]:
        """Remove and return item from queue with optional timeout - O(1)"""
        with self._lock:
            if self.is_empty():
                return None
            return self._queue.popleft()
    
    def is_empty(self) -> bool:
        """Check if queue is empty - O(1)"""
        with self._lock:
            return len(self._queue) == 0
    
    def size(self) -> int:
        """Return queue size - O(1)"""
        with self._lock:
            return len(self._queue)

# 4. Priority Queue Implementation
import heapq
from typing import Tuple

@dataclass
class PriorityItem:
    """Item with priority for priority queue"""
    priority: int
    item: Any
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def __lt__(self, other):
        # Lower priority number = higher priority
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp

class PriorityQueue:
    """
    Priority queue implementation using heapq.
    Items with lower priority numbers are dequeued first.
    """
    def __init__(self):
        self._queue: list[PriorityItem] = []
        self._index = 0
    
    def enqueue(self, item: Any, priority: int) -> None:
        """Add item with priority - O(log n)"""
        priority_item = PriorityItem(priority, item)
        heapq.heappush(self._queue, priority_item)
    
    def dequeue(self) -> Any:
        """Remove and return highest priority item - O(log n)"""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return heapq.heappop(self._queue).item
    
    def is_empty(self) -> bool:
        """Check if queue is empty - O(1)"""
        return len(self._queue) == 0
    
    def size(self) -> int:
        """Return queue size - O(1)"""
        return len(self._queue)

# 5. Database-Connected Queue (Task Queue Example)
@dataclass
class Task:
    """Task model for database queue"""
    id: str
    payload: dict
    priority: int
    created_at: datetime
    status: str = "pending"  # pending, processing, completed, failed
    retry_count: int = 0
    max_retries: int = 3

class DatabaseQueue:
    """
    Database-backed queue implementation.
    Suitable for persistent task queues that survive server restarts.
    """
    def __init__(self, db_connection):
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create tasks table if it doesn't exist"""
        # This would be your actual database table creation
        # For PostgreSQL with Django ORM, you'd have a Task model
        pass
    
    def enqueue(self, task: Task) -> bool:
        """Add task to database queue - O(log n) due to index"""
        try:
            # INSERT INTO tasks (id, payload, priority, created_at, status)
            # VALUES (task.id, task.payload, task.priority, task.created_at, task.status)
            # In Django: Task.objects.create(...)
            return True
        except Exception as e:
            print(f"Failed to enqueue task: {e}")
            return False
    
    def dequeue(self) -> Optional[Task]:
        """Get next task from database queue - O(log n)"""
        try:
            # SELECT * FROM tasks 
            # WHERE status = 'pending' 
            # ORDER BY priority ASC, created_at ASC 
            # LIMIT 1 FOR UPDATE
            # 
            # UPDATE tasks SET status = 'processing' WHERE id = task.id
            # In Django: Task.objects.filter(status='pending').order_by('priority', 'created_at').first()
            return None  # Placeholder
        except Exception as e:
            print(f"Failed to dequeue task: {e}")
            return None
    
    def mark_completed(self, task_id: str) -> bool:
        """Mark task as completed - O(log n)"""
        try:
            # UPDATE tasks SET status = 'completed' WHERE id = task_id
            return True
        except Exception as e:
            print(f"Failed to mark task completed: {e}")
            return False
    
    def mark_failed(self, task_id: str) -> bool:
        """Mark task as failed and handle retries - O(log n)"""
        try:
            # Increment retry_count, set status based on max_retries
            # If retry_count < max_retries: status = 'pending'
            # Else: status = 'failed'
            return True
        except Exception as e:
            print(f"Failed to mark task failed: {e}")
            return False

# 6. Redis-Based Distributed Queue
class RedisQueue:
    """
    Redis-based distributed queue implementation.
    Suitable for microservices and distributed systems.
    """
    def __init__(self, redis_url: str, queue_name: str):
        self.redis = aioredis.from_url(redis_url)
        self.queue_name = queue_name
    
    async def enqueue(self, item: dict) -> bool:
        """Add item to Redis queue - O(1)"""
        try:
            import json
            await self.redis.lpush(self.queue_name, json.dumps(item))
            return True
        except Exception as e:
            print(f"Failed to enqueue to Redis: {e}")
            return False
    
    async def dequeue(self, timeout: int = 0) -> Optional[dict]:
        """Remove item from Redis queue with optional blocking - O(1)"""
        try:
            import json
            if timeout > 0:
                # Blocking pop with timeout
                result = await self.redis.brpop(self.queue_name, timeout=timeout)
            else:
                # Non-blocking pop
                result = await self.redis.rpop(self.queue_name)
            
            if result:
                if isinstance(result, list):
                    return json.loads(result[1])  # brpop returns [key, value]
                return json.loads(result)  # rpop returns value
            return None
        except Exception as e:
            print(f"Failed to dequeue from Redis: {e}")
            return None
    
    async def size(self) -> int:
        """Get queue size - O(1)"""
        return await self.redis.llen(self.queue_name)

# 7. Real-World Usage Examples
def demonstrate_queue_usage():
    """Demonstrate various queue usage patterns"""
    
    # Example 1: Basic queue for BFS algorithm
    def bfs_example():
        """Breadth-First Search using queue"""
        graph = {
            'A': ['B', 'C'],
            'B': ['D', 'E'],
            'C': ['F'],
            'D': [],
            'E': ['F'],
            'F': []
        }
        
        def bfs(graph: dict, start: str) -> list:
            visited = set()
            queue = EfficientQueue[str]()
            result = []
            
            queue.enqueue(start)
            visited.add(start)
            
            while not queue.is_empty():
                vertex = queue.dequeue()
                result.append(vertex)
                
                for neighbor in graph[vertex]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.enqueue(neighbor)
            
            return result
        
        return bfs(graph, 'A')
    
    # Example 2: Task processing system
    def task_processing_example():
        """Task processing with priority queue"""
        task_queue = PriorityQueue()
        
        # Add tasks with different priorities
        task_queue.enqueue({"action": "send_email", "to": "user@example.com"}, priority=2)
        task_queue.enqueue({"action": "process_payment", "amount": 100}, priority=1)  # Higher priority
        task_queue.enqueue({"action": "generate_report", "type": "monthly"}, priority=3)
        
        # Process tasks in priority order
        processed_tasks = []
        while not task_queue.is_empty():
            task = task_queue.dequeue()
            processed_tasks.append(task)
            print(f"Processing task: {task}")
        
        return processed_tasks
    
    # Example 3: Producer-Consumer pattern
    def producer_consumer_example():
        """Producer-Consumer pattern using thread-safe queue"""
        import threading
        import time
        import random
        
        shared_queue = ThreadSafeQueue[str](maxsize=10)
        results = []
        
        def producer(name: str, items: int):
            """Producer function"""
            for i in range(items):
                item = f"{name}-item-{i}"
                if shared_queue.enqueue(item):
                    print(f"Producer {name}: Added {item}")
                else:
                    print(f"Producer {name}: Queue full, couldn't add {item}")
                time.sleep(random.uniform(0.1, 0.3))
        
        def consumer(name: str):
            """Consumer function"""
            while True:
                item = shared_queue.dequeue()
                if item is None:
                    time.sleep(0.1)
                    continue
                
                results.append(item)
                print(f"Consumer {name}: Processed {item}")
                time.sleep(random.uniform(0.2, 0.5))
                
                # Stop after processing some items (for demo)
                if len(results) >= 10:
                    break
        
        # Start producer and consumer threads
        producer_thread = threading.Thread(target=producer, args=("P1", 5))
        consumer_thread = threading.Thread(target=consumer, args=("C1"))
        
        producer_thread.start()
        consumer_thread.start()
        
        producer_thread.join()
        consumer_thread.join()
        
        return results
    
    # Run examples
    print("BFS Example:", bfs_example())
    print("\nTask Processing Example:")
    task_processing_example()
    print("\nProducer-Consumer Example:")
    producer_consumer_example()

# 8. Performance Comparison
def performance_comparison():
    """Compare performance of different queue implementations"""
    import time
    
    def benchmark_queue(queue_class, operations: int = 10000):
        """Benchmark queue operations"""
        queue = queue_class()
        
        # Enqueue operations
        start_time = time.time()
        for i in range(operations):
            queue.enqueue(i)
        enqueue_time = time.time() - start_time
        
        # Dequeue operations
        start_time = time.time()
        for i in range(operations):
            queue.dequeue()
        dequeue_time = time.time() - start_time
        
        return enqueue_time, dequeue_time
    
    # Compare BasicQueue vs EfficientQueue
    print("Performance Comparison (10,000 operations):")
    
    basic_enqueue, basic_dequeue = benchmark_queue(BasicQueue)
    print(f"BasicQueue - Enqueue: {basic_enqueue:.4f}s, Dequeue: {basic_dequeue:.4f}s")
    
    efficient_enqueue, efficient_dequeue = benchmark_queue(EfficientQueue)
    print(f"EfficientQueue - Enqueue: {efficient_enqueue:.4f}s, Dequeue: {efficient_dequeue:.4f}s")

if __name__ == "__main__":
    # Demonstrate queue usage
    demonstrate_queue_usage()
    
    # Performance comparison
    performance_comparison()

### 1. **Web Development (Your Stack)**
# - **Django + DRF**: Task queues with Celery for background jobs
# - **NextJS**: Client-side queues for API request management
# - **WebSocket with Channels**: Message queues for real-time communication
# - **Redis**: Distributed queues for caching and session management

# ### 2. **System Architecture**
# - **Load Balancing**: Nginx queue management for incoming requests
# - **Database Connection Pooling**: PostgreSQL connection queues
# - **Message Brokers**: RabbitMQ, Apache Kafka for microservices

# ### 3. **Algorithm Applications**
# - **Breadth-First Search (BFS)**: Graph traversal, shortest path
# - **Tree Level Order Traversal**: Binary tree processing
# - **Topological Sorting**: Dependency resolution

## Where NOT to Use Queues

### 1. **Random Access Required**
# - Use arrays/lists when you need to access elements by index
# - Hash tables for key-based lookups

# ### 2. **Stack Operations Needed**
# - Last In, First Out (LIFO) operations
# - Function call management, undo operations

# ### 3. **Small Data Sets**
# - Overhead might not be worth it for < 100 elements
# - Simple list operations might be more readable

## Big O Notation Analysis

# | Operation | collections.deque | List (pop(0)) | Priority Queue | Database Queue |
# |-----------|-------------------|---------------|----------------|----------------|
# | Enqueue   | O(1)             | O(1)          | O(log n)       | O(log n)       |
# | Dequeue   | O(1)             | O(n)          | O(log n)       | O(log n)       |
# | Peek      | O(1)             | O(1)          | O(1)           | O(log n)       |
# | Size      | O(1)             | O(1)          | O(1)           | O(1)           |

## Database Integration

### 1. **PostgreSQL Task Queue (Django)**

# models.py
from django.db import models
from django.utils import timezone

class TaskQueue(models.Model):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]
    
    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    payload = models.JSONField()
    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'priority', 'created_at']),
        ]


### 2. **MongoDB Task Queue (NextJS)**

# For NextJS with MongoDB, you'd typically use a similar structure
# but with a NoSQL approach in your API routes


## Security Considerations

### 1. **Input Validation**

def secure_enqueue(self, item: Any) -> bool:
    """Secure enqueue with validation"""
    # Validate item structure
    if not self._validate_item(item):
        raise ValueError("Invalid item structure")
    
    # Sanitize input
    sanitized_item = self._sanitize_item(item)
    
    # Rate limiting
    if not self._check_rate_limit():
        raise Exception("Rate limit exceeded")
    
    return self.enqueue(sanitized_item)


### 2. **Authentication & Authorization**

class SecureQueue:
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self._verify_token()
    
    def _verify_token(self):
        """Verify authentication token"""
        # Implement JWT verification or session validation
        pass
    
    def enqueue(self, item: Any, user_id: str) -> bool:
        """Enqueue with user authorization"""
        if not self._user_authorized(user_id):
            raise PermissionError("User not authorized")
        
        return super().enqueue(item)


### 3. **Data Encryption**

import base64
from cryptography.fernet import Fernet

class EncryptedQueue:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        self.queue = EfficientQueue()
    
    def enqueue(self, item: Any) -> None:
        """Encrypt and enqueue item"""
        import json
        serialized = json.dumps(item)
        encrypted = self.cipher.encrypt(serialized.encode())
        self.queue.enqueue(encrypted)
    
    def dequeue(self) -> Any:
        """Dequeue and decrypt item"""
        encrypted_item = self.queue.dequeue()
        decrypted = self.cipher.decrypt(encrypted_item)
        return json.loads(decrypted.decode())


## Real-World Implementation Examples

### 1. **Email Queue System (Django + Redis)**

# tasks.py (Celery)
from celery import Celery
from django.core.mail import send_mail

app = Celery('email_queue')

@app.task
def send_email_task(to_email: str, subject: str, message: str):
    """Background email sending task"""
    try:
        send_mail(subject, message, 'noreply@example.com', [to_email])
        return {'status': 'success', 'email': to_email}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}

# views.py
from django.http import JsonResponse
from .tasks import send_email_task

def send_email_view(request):
    """Queue email for background processing"""
    email_data = request.POST
    send_email_task.delay(
        email_data['to'],
        email_data['subject'],
        email_data['message']
    )
    return JsonResponse({'status': 'queued'})


### 2. **Payment Processing Queue (Stripe Integration)**

# payment_queue.py
import stripe
from typing import Dict, Any

class PaymentQueue:
    def __init__(self):
        self.queue = PriorityQueue()
        stripe.api_key = "your_stripe_secret_key"
    
    def queue_payment(self, amount: int, currency: str, customer_id: str, priority: int = 1):
        """Queue payment for processing"""
        payment_data = {
            'amount': amount,
            'currency': currency,
            'customer': customer_id,
            'timestamp': time.time()
        }
        self.queue.enqueue(payment_data, priority)
    
    def process_payments(self):
        """Process queued payments"""
        while not self.queue.is_empty():
            payment_data = self.queue.dequeue()
            try:
                charge = stripe.Charge.create(**payment_data)
                print(f"Payment processed: {charge.id}")
            except stripe.error.CardError as e:
                print(f"Payment failed: {e}")


## Advantages & Disadvantages

### Advantages
# 1. **FIFO Guarantee**: Predictable ordering
# 2. **Efficient Operations**: O(1) enqueue/dequeue with proper implementation
# 3. **Thread Safety**: Can be made thread-safe for concurrent access
# 4. **Scalability**: Works well with distributed systems
# 5. **Buffering**: Helps manage different processing speeds

# ### Disadvantages
# 1. **Memory Usage**: Can consume significant memory for large queues
# 2. **No Random Access**: Can't access middle elements efficiently
# 3. **Blocking Operations**: May block when queue is full/empty
# 4. **Single Point of Failure**: If queue fails, system may halt

## Testing Strategies

### 1. **Unit Testing with pytest**

import pytest
from your_queue_module import EfficientQueue

def test_queue_operations():
    queue = EfficientQueue[int]()
    
    # Test enqueue
    queue.enqueue(1)
    queue.enqueue(2)
    assert queue.size() == 2
    
    # Test dequeue
    assert queue.dequeue() == 1
    assert queue.size() == 1
    
    # Test empty queue
    queue.dequeue()
    assert queue.is_empty()
    
    with pytest.raises(IndexError):
        queue.dequeue()


### 2. **Integration Testing with Database**

def test_database_queue_integration():
    # Test with actual database connection
    # Verify persistence across restarts
    pass


# This comprehensive overview shows how queues work internally, their practical applications in your tech stack, and how to implement them securely and efficiently. 
# The code examples demonstrate real-world usage patterns you'll encounter in web development, system design, and algorithm implementation.

There are several efficient ways to implement a queue without shifting elements when dequeuing. Here are the most common approaches:

## 1. Circular Array (Ring Buffer)

The most efficient approach uses a circular array with front and rear pointers:

```python
class CircularQueue:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.queue = [None] * capacity
        self.front = 0  # Points to the first element
        self.rear = 0   # Points to the next insertion position
        self.size = 0
    
    def enqueue(self, item) -> bool:
        if self.is_full():
            return False
        
        self.queue[self.rear] = item
        self.rear = (self.rear + 1) % self.capacity  # Circular increment
        self.size += 1
        return True
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        item = self.queue[self.front]
        self.queue[self.front] = None  # Optional: clear reference
        self.front = (self.front + 1) % self.capacity  # Circular increment
        self.size -= 1
        return item
    
    def is_empty(self) -> bool:
        return self.size == 0
    
    def is_full(self) -> bool:
        return self.size == self.capacity
```

**How it works internally**: The circular array uses modulo arithmetic to wrap around. When `rear` or `front` reaches the end of the array, it wraps to index 0. This eliminates the need to shift elements.

## 2. Two Stacks Approach

Uses two stacks to simulate a queue with amortized O(1) operations:

```python
class QueueWithStacks:
    def __init__(self):
        self.stack1 = []  # For enqueue operations
        self.stack2 = []  # For dequeue operations
    
    def enqueue(self, item):
        self.stack1.append(item)
    
    def dequeue(self):
        # If stack2 is empty, transfer all from stack1
        if not self.stack2:
            if not self.stack1:
                raise IndexError("Queue is empty")
            
            # Transfer all elements from stack1 to stack2
            while self.stack1:
                self.stack2.append(self.stack1.pop())
        
        return self.stack2.pop()
    
    def is_empty(self) -> bool:
        return len(self.stack1) == 0 and len(self.stack2) == 0
```

**How it works internally**: Elements are added to `stack1`. When dequeuing, if `stack2` is empty, all elements from `stack1` are transferred to `stack2` (reversing their order). This ensures FIFO behavior without shifting.

## 3. Linked List Implementation

Most straightforward approach using nodes:

```python
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedQueue:
    def __init__(self):
        self.front = None  # Points to first node
        self.rear = None   # Points to last node
        self.size = 0
    
    def enqueue(self, item):
        new_node = Node(item)
        
        if self.rear is None:  # Empty queue
            self.front = self.rear = new_node
        else:
            self.rear.next = new_node
            self.rear = new_node
        
        self.size += 1
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        item = self.front.data
        self.front = self.front.next
        
        if self.front is None:  # Queue became empty
            self.rear = None
        
        self.size -= 1
        return item
    
    def is_empty(self) -> bool:
        return self.front is None
```

## 4. Dynamic Array with Lazy Deletion

For scenarios where you need resizable capacity:

```python
class DynamicQueue:
    def __init__(self):
        self.queue = []
        self.front_index = 0
        self._cleanup_threshold = 1000  # Cleanup when waste exceeds this
    
    def enqueue(self, item):
        self.queue.append(item)
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        item = self.queue[self.front_index]
        self.front_index += 1
        
        # Cleanup when too much space is wasted
        if self.front_index > self._cleanup_threshold:
            self.queue = self.queue[self.front_index:]
            self.front_index = 0
        
        return item
    
    def is_empty(self) -> bool:
        return self.front_index >= len(self.queue)
    
    def size(self) -> int:
        return len(self.queue) - self.front_index
```

## Real-World Usage Examples

**1. Web Server Request Queue** (using circular buffer):
```python
# Nginx-style request handling
request_queue = CircularQueue(1000)

# Producer (incoming requests)
def handle_incoming_request(request):
    if not request_queue.enqueue(request):
        return "503 Service Unavailable"

# Consumer (worker threads)
def worker_thread():
    while True:
        try:
            request = request_queue.dequeue()
            process_request(request)
        except IndexError:
            time.sleep(0.1)  # Wait for new requests
```

**2. Redis-like Message Queue** (using linked list):
```python
class MessageQueue:
    def __init__(self):
        self.queue = LinkedQueue()
        self.subscribers = []
    
    def publish(self, message):
        self.queue.enqueue(message)
        self.notify_subscribers()
    
    def consume(self):
        return self.queue.dequeue()
```

**3. Django Channels WebSocket** (using two stacks for buffering):
```python
class WebSocketBuffer:
    def __init__(self):
        self.message_queue = QueueWithStacks()
    
    async def send_message(self, message):
        self.message_queue.enqueue(message)
    
    async def process_outgoing(self):
        while not self.message_queue.is_empty():
            message = self.message_queue.dequeue()
            await self.send_to_client(message)
```

## Performance Comparison

| Implementation | Enqueue | Dequeue | Space | Use Case |
|---------------|---------|---------|--------|----------|
| Circular Array | O(1) | O(1) | O(n) | Fixed capacity, high performance |
| Two Stacks | O(1) | O(1) amortized | O(n) | Dynamic size, good for bursts |
| Linked List | O(1) | O(1) | O(n) | Dynamic size, no capacity limit |
| Dynamic Array | O(1) | O(1) amortized | O(n) | Resizable, periodic cleanup |

## Security Considerations

When implementing queues in production systems:

```python
import threading
from typing import Optional, TypeVar, Generic

T = TypeVar('T')

class ThreadSafeQueue(Generic[T]):
    def __init__(self, capacity: int):
        self._queue = CircularQueue(capacity)
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
    
    def enqueue(self, item: T, timeout: Optional[float] = None) -> bool:
        with self._not_full:
            if not self._not_full.wait_for(
                lambda: not self._queue.is_full(), timeout=timeout
            ):
                return False
            
            result = self._queue.enqueue(item)
            self._not_empty.notify()
            return result
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[T]:
        with self._not_empty:
            if not self._not_empty.wait_for(
                lambda: not self._queue.is_empty(), timeout=timeout
            ):
                return None
            
            item = self._queue.dequeue()
            self._not_full.notify()
            return item
```

The key insight is that by maintaining pointers/indices instead of physically moving elements, we achieve O(1) dequeue operations while maintaining the FIFO property of queues.

Yes, absolutely! You can implement a queue by shifting the index value instead of shifting the actual elements. This is actually one of the most practical approaches for queue implementation. Here are several ways to do this:

## 1. Simple Index-Based Queue

```python
class IndexQueue:
    def __init__(self):
        self.data = []
        self.front_index = 0  # Points to the first element
    
    def enqueue(self, item):
        self.data.append(item)
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        # Get element at front_index and increment the index
        item = self.data[self.front_index]
        self.front_index += 1
        return item
    
    def is_empty(self) -> bool:
        return self.front_index >= len(self.data)
    
    def size(self) -> int:
        return len(self.data) - self.front_index
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.data[self.front_index]

# Usage example
queue = IndexQueue()
queue.enqueue(1)
queue.enqueue(2)
queue.enqueue(3)

print(queue.dequeue())  # 1
print(queue.dequeue())  # 2
print(queue.size())     # 1
```

## 2. Index Queue with Memory Management

The simple approach above can waste memory over time. Here's an optimized version:

```python
class OptimizedIndexQueue:
    def __init__(self, cleanup_threshold: int = 100):
        self.data = []
        self.front_index = 0
        self.cleanup_threshold = cleanup_threshold
    
    def enqueue(self, item):
        self.data.append(item)
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        item = self.data[self.front_index]
        self.front_index += 1
        
        # Cleanup when too much memory is wasted
        if self.front_index >= self.cleanup_threshold:
            self._cleanup()
        
        return item
    
    def _cleanup(self):
        """Remove processed elements and reset index"""
        # Keep only unprocessed elements
        self.data = self.data[self.front_index:]
        self.front_index = 0
    
    def is_empty(self) -> bool:
        return self.front_index >= len(self.data)
    
    def size(self) -> int:
        return len(self.data) - self.front_index
    
    def get_memory_usage(self) -> dict:
        return {
            'total_elements': len(self.data),
            'active_elements': self.size(),
            'wasted_space': self.front_index,
            'memory_efficiency': self.size() / len(self.data) if self.data else 1.0
        }
```

## 3. Type-Safe Generic Version

```python
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class TypedIndexQueue(Generic[T]):
    def __init__(self, cleanup_threshold: int = 100):
        self._data: List[T] = []
        self._front_index: int = 0
        self._cleanup_threshold: int = cleanup_threshold
    
    def enqueue(self, item: T) -> None:
        self._data.append(item)
    
    def dequeue(self) -> T:
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        item = self._data[self._front_index]
        self._front_index += 1
        
        # Auto-cleanup to manage memory
        if self._front_index >= self._cleanup_threshold:
            self._cleanup()
        
        return item
    
    def peek(self) -> T:
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self._data[self._front_index]
    
    def is_empty(self) -> bool:
        return self._front_index >= len(self._data)
    
    def size(self) -> int:
        return len(self._data) - self._front_index
    
    def _cleanup(self) -> None:
        """Remove processed elements and reset front index"""
        self._data = self._data[self._front_index:]
        self._front_index = 0
    
    def force_cleanup(self) -> None:
        """Manually trigger cleanup"""
        if self._front_index > 0:
            self._cleanup()
```

## 4. Thread-Safe Index Queue

For Django/DRF applications with concurrent access:

```python
import threading
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class ThreadSafeIndexQueue(Generic[T]):
    def __init__(self, cleanup_threshold: int = 100):
        self._data: List[T] = []
        self._front_index: int = 0
        self._cleanup_threshold: int = cleanup_threshold
        self._lock = threading.RLock()  # Re-entrant lock
    
    def enqueue(self, item: T) -> None:
        with self._lock:
            self._data.append(item)
    
    def dequeue(self) -> T:
        with self._lock:
            if self.is_empty():
                raise IndexError("Queue is empty")
            
            item = self._data[self._front_index]
            self._front_index += 1
            
            if self._front_index >= self._cleanup_threshold:
                self._cleanup()
            
            return item
    
    def dequeue_batch(self, count: int) -> List[T]:
        """Dequeue multiple items at once - more efficient for bulk operations"""
        with self._lock:
            if self.is_empty():
                return []
            
            actual_count = min(count, self.size())
            end_index = self._front_index + actual_count
            
            items = self._data[self._front_index:end_index]
            self._front_index = end_index
            
            if self._front_index >= self._cleanup_threshold:
                self._cleanup()
            
            return items
    
    def is_empty(self) -> bool:
        with self._lock:
            return self._front_index >= len(self._data)
    
    def size(self) -> int:
        with self._lock:
            return len(self._data) - self._front_index
    
    def _cleanup(self) -> None:
        self._data = self._data[self._front_index:]
        self._front_index = 0
```

## Real-World Usage Examples

### 1. Django Task Queue with Redis-like Behavior

```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class TaskQueue:
    def __init__(self):
        self.pending_tasks = TypedIndexQueue[dict]()
        self.completed_tasks = []
    
    def add_task(self, task_data: dict):
        """Add task to queue"""
        task_data['created_at'] = timezone.now()
        task_data['status'] = 'pending'
        self.pending_tasks.enqueue(task_data)
    
    def process_next_task(self) -> Optional[dict]:
        """Process next task in queue"""
        if self.pending_tasks.is_empty():
            return None
        
        task = self.pending_tasks.dequeue()
        task['status'] = 'processing'
        task['started_at'] = timezone.now()
        
        return task
    
    def complete_task(self, task: dict, result: any):
        """Mark task as completed"""
        task['status'] = 'completed'
        task['completed_at'] = timezone.now()
        task['result'] = result
        self.completed_tasks.append(task)

# Usage in Django view
def process_tasks(request):
    task_queue = TaskQueue()
    
    # Add tasks
    task_queue.add_task({'type': 'send_email', 'user_id': 1})
    task_queue.add_task({'type': 'generate_report', 'report_id': 123})
    
    # Process tasks
    while not task_queue.pending_tasks.is_empty():
        task = task_queue.process_next_task()
        result = execute_task(task)
        task_queue.complete_task(task, result)
```

### 2. NextJS WebSocket Message Buffer

```typescript
// For your NextJS app with WebSocket
class MessageBuffer<T> {
    private data: T[] = [];
    private frontIndex: number = 0;
    private cleanupThreshold: number = 50;
    
    enqueue(message: T): void {
        this.data.push(message);
    }
    
    dequeue(): T | null {
        if (this.isEmpty()) {
            return null;
        }
        
        const message = this.data[this.frontIndex];
        this.frontIndex++;
        
        if (this.frontIndex >= this.cleanupThreshold) {
            this.cleanup();
        }
        
        return message;
    }
    
    private cleanup(): void {
        this.data = this.data.slice(this.frontIndex);
        this.frontIndex = 0;
    }
    
    isEmpty(): boolean {
        return this.frontIndex >= this.data.length;
    }
    
    size(): number {
        return this.data.length - this.frontIndex;
    }
}

// Usage in WebSocket handler
const messageBuffer = new MessageBuffer<WebSocketMessage>();

// Buffer incoming messages
ws.on('message', (message) => {
    messageBuffer.enqueue(JSON.parse(message));
});

// Process messages
setInterval(() => {
    while (!messageBuffer.isEmpty()) {
        const message = messageBuffer.dequeue();
        processMessage(message);
    }
}, 100);
```

### 3. Expo/React Native Offline Queue

```javascript
// For handling offline actions in your mobile app
class OfflineActionQueue {
    constructor() {
        this.actions = [];
        this.frontIndex = 0;
    }
    
    async enqueueAction(action) {
        this.actions.push({
            ...action,
            timestamp: Date.now(),
            attempts: 0
        });
        
        // Try to sync immediately if online
        if (await this.isOnline()) {
            this.processPendingActions();
        }
    }
    
    async processPendingActions() {
        while (!this.isEmpty()) {
            const action = this.dequeue();
            
            try {
                await this.executeAction(action);
            } catch (error) {
                // Re-queue failed actions with exponential backoff
                if (action.attempts < 3) {
                    action.attempts++;
                    setTimeout(() => {
                        this.enqueue(action);
                    }, Math.pow(2, action.attempts) * 1000);
                }
            }
        }
    }
    
    dequeue() {
        if (this.isEmpty()) return null;
        
        const action = this.actions[this.frontIndex];
        this.frontIndex++;
        
        // Cleanup periodically
        if (this.frontIndex > 20) {
            this.actions = this.actions.slice(this.frontIndex);
            this.frontIndex = 0;
        }
        
        return action;
    }
    
    isEmpty() {
        return this.frontIndex >= this.actions.length;
    }
}
```

## Performance Analysis

**Time Complexity**:
- Enqueue: O(1)
- Dequeue: O(1) amortized (O(n) only during cleanup)
- Cleanup: O(n) but happens infrequently

**Space Complexity**: O(n) where n is the number of elements ever enqueued

**Memory Management**: The cleanup mechanism ensures that memory usage doesn't grow indefinitely, making it suitable for long-running applications.

## Security Considerations

```python
class SecureIndexQueue:
    def __init__(self, max_size: int = 1000, cleanup_threshold: int = 100):
        self._data = []
        self._front_index = 0
        self._max_size = max_size  # Prevent memory exhaustion
        self._cleanup_threshold = cleanup_threshold
    
    def enqueue(self, item):
        # Security: Prevent memory exhaustion attacks
        if len(self._data) >= self._max_size:
            raise OverflowError("Queue size limit exceeded")
        
        # Security: Validate item size for network applications
        if hasattr(item, '__sizeof__') and item.__sizeof__() > 1024 * 1024:  # 1MB limit
            raise ValueError("Item too large")
        
        self._data.append(item)
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        item = self._data[self._front_index]
        
        # Security: Clear reference to prevent memory leaks
        self._data[self._front_index] = None
        self._front_index += 1
        
        if self._front_index >= self._cleanup_threshold:
            self._cleanup()
        
        return item
```

This index-based approach is particularly efficient for scenarios where you have predictable access patterns and want to avoid the overhead of linked list node allocation or circular buffer complexity. It's commonly used in production systems for message queues, task processors, and buffering systems.

Looking at both approaches, **my circular array (ring buffer) implementation from the previous response is generally better for production systems**. Here's a detailed comparison:

## Performance Comparison

| Aspect | Index-Based Queue | Circular Array |
|--------|------------------|----------------|
| **Enqueue** | O(1) | O(1) |
| **Dequeue** | O(1) amortized, O(n) worst case | O(1) guaranteed |
| **Memory Usage** | Grows indefinitely until cleanup | Fixed memory footprint |
| **Memory Fragmentation** | High (periodic cleanup creates gaps) | None |
| **Predictable Performance** | No (cleanup spikes) | Yes |

## Production Analysis

### Index-Based Queue Issues:

```python
# Memory usage over time with index-based queue
class ProductionAnalysis:
    def analyze_index_queue_memory(self):
        queue = IndexQueue()
        
        # Simulate production load
        for i in range(10000):
            queue.enqueue(f"task_{i}")
        
        # Process half the items
        for i in range(5000):
            queue.dequeue()
        
        # Memory issue: Still holding 10000 items in memory
        # but only 5000 are active
        print(f"Memory waste: {queue.front_index} unused elements")
        print(f"Memory efficiency: {queue.size() / len(queue.data) * 100:.1f}%")
        
        # Result: 50% memory waste until cleanup triggers
```

### Circular Array Advantages:

```python
# Production-ready circular queue with monitoring
class ProductionCircularQueue:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.queue = [None] * capacity
        self.front = 0
        self.rear = 0
        self.size = 0
        
        # Production monitoring
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.max_size_reached = 0
    
    def enqueue(self, item) -> bool:
        if self.is_full():
            return False
        
        self.queue[self.rear] = item
        self.rear = (self.rear + 1) % self.capacity
        self.size += 1
        
        # Monitoring
        self.total_enqueued += 1
        self.max_size_reached = max(self.max_size_reached, self.size)
        
        return True
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        item = self.queue[self.front]
        self.queue[self.front] = None  # Clear reference for GC
        self.front = (self.front + 1) % self.capacity
        self.size -= 1
        
        # Monitoring
        self.total_dequeued += 1
        
        return item
    
    def get_metrics(self) -> dict:
        return {
            'current_size': self.size,
            'capacity': self.capacity,
            'utilization': self.size / self.capacity,
            'total_processed': self.total_dequeued,
            'max_size_reached': self.max_size_reached,
            'memory_efficiency': 1.0  # Always 100% efficient
        }
```

## Real-World Production Scenarios

### 1. High-Frequency Trading System

```python
# Index-based queue problems in HFT
class HFTOrderQueue:
    def __init__(self):
        self.orders = IndexQueue()
    
    def process_market_data(self):
        # Problem: In HFT, cleanup pauses are unacceptable
        # Even 1ms cleanup can cause missed opportunities
        
        while True:
            order = self.orders.dequeue()  # Potential cleanup spike!
            self.execute_order(order)
```

```python
# Circular queue solution for HFT
class HFTCircularQueue:
    def __init__(self, capacity=10000):
        self.queue = ProductionCircularQueue(capacity)
    
    def process_market_data(self):
        # Guaranteed O(1) performance - no cleanup spikes
        while not self.queue.is_empty():
            order = self.queue.dequeue()  # Always O(1)
            self.execute_order(order)
```

### 2. Django/DRF API with High Load

```python
# Django middleware with request queue
class RequestQueueMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Production choice: Circular queue for predictable performance
        self.request_queue = ProductionCircularQueue(1000)
        self.worker_thread = threading.Thread(target=self.process_requests)
        self.worker_thread.start()
    
    def __call__(self, request):
        # Enqueue request for processing
        if not self.request_queue.enqueue(request):
            return HttpResponse("503 Service Unavailable", status=503)
        
        # Wait for processing or timeout
        return self.wait_for_response(request)
    
    def process_requests(self):
        while True:
            try:
                request = self.request_queue.dequeue()
                self.process_request(request)
            except IndexError:
                time.sleep(0.001)  # Short sleep when empty
```

### 3. WebSocket Message Buffer (NextJS + Django Channels)

```python
# Django Channels consumer
class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Circular queue for message buffering
        self.message_buffer = ProductionCircularQueue(500)
    
    async def receive(self, text_data):
        message = json.loads(text_data)
        
        # Buffer message for processing
        if not self.message_buffer.enqueue(message):
            await self.send(text_data=json.dumps({
                'error': 'Message buffer full'
            }))
            return
        
        # Process buffered messages
        await self.process_message_buffer()
    
    async def process_message_buffer(self):
        while not self.message_buffer.is_empty():
            message = self.message_buffer.dequeue()
            await self.handle_message(message)
```

## Hybrid Approach for Best of Both Worlds

For scenarios where you need both dynamic sizing AND predictable performance:

```python
class HybridProductionQueue:
    def __init__(self, initial_capacity=1000, max_capacity=10000):
        self.segments = []
        self.current_segment = ProductionCircularQueue(initial_capacity)
        self.segments.append(self.current_segment)
        
        self.max_capacity = max_capacity
        self.total_size = 0
    
    def enqueue(self, item):
        # Try current segment first
        if self.current_segment.enqueue(item):
            self.total_size += 1
            return True
        
        # Create new segment if not at max capacity
        if len(self.segments) * self.current_segment.capacity < self.max_capacity:
            new_segment = ProductionCircularQueue(self.current_segment.capacity)
            self.segments.append(new_segment)
            self.current_segment = new_segment
            
            if self.current_segment.enqueue(item):
                self.total_size += 1
                return True
        
        return False  # Queue full
    
    def dequeue(self):
        # Remove empty segments from front
        while self.segments and self.segments[0].is_empty():
            self.segments.pop(0)
        
        if not self.segments:
            raise IndexError("Queue is empty")
        
        item = self.segments[0].dequeue()
        self.total_size -= 1
        return item
    
    def is_empty(self):
        return self.total_size == 0
    
    def size(self):
        return self.total_size
```

## Production Recommendation

**For production systems, I recommend the circular array approach because:**

1. **Predictable Performance**: No cleanup spikes that can cause latency issues
2. **Memory Efficiency**: Fixed memory footprint prevents memory leaks
3. **Security**: Built-in capacity limits prevent DoS attacks
4. **Monitoring**: Easy to track utilization and performance metrics
5. **Reliability**: No edge cases with cleanup timing

**Use index-based queue only when:**
- You have unpredictable queue sizes that vary dramatically
- Memory is abundant and cleanup pauses are acceptable
- You need unlimited capacity (with proper monitoring)

**For your tech stack specifically:**
- **Django/DRF**: Circular queue for request processing
- **NextJS**: Circular queue for WebSocket message buffering
- **Redis alternative**: Circular queue for in-memory queues
- **Mobile (Expo)**: Circular queue for offline action queues

The circular array's predictable O(1) performance and fixed memory footprint make it the better choice for production systems where reliability and consistent performance are crucial.