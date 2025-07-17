# A **queue** is a linear data structure that follows the **First-In-First-Out (FIFO)** principle, meaning the first element added to the queue is the first one to be removed. It operates like a real-world queue, such as people waiting in line at a ticket counter. In this explanation, I’ll provide a detailed overview of queues, implement one in Python without using the built-in `deque` module, discuss its use cases, advantages, disadvantages, Big O notation, database integration, security considerations, and provide a real-world code example.

# ---

# ### **1. Queue Implementation in Python (Without `deque`)**
# We’ll implement a queue using a Python **list** as the underlying data structure. The queue will support basic operations: enqueue (add), dequeue (remove), peek (view front element), and check if empty.


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

# This implementation uses a list, but note that Python’s `list.pop(0)` is inefficient for large queues because it shifts all remaining elements, leading to `O(n)` complexity for dequeue.

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

# **Optimization Note**: To improve dequeue performance to `O(1)`, use a **linked list** or a **circular buffer**. A linked list implementation would store nodes with pointers, allowing constant-time removal from the front.

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
# Queues are a fundamental data structure for managing FIFO-based workflows. While the list-based implementation is simple, it’s inefficient for dequeue operations. A linked list or circular buffer can optimize performance. Queues are versatile, used in task scheduling, message processing, and database integration, but they require careful handling for concurrency and security. By understanding their strengths, limitations, and proper use cases, you can effectively apply queues to solve real-world problems.

# If you have further questions or need a specific use case explored, let me know!

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