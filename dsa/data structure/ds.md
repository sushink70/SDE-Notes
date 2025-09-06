# Data Structures (DS) Overview

I'll provide you with a comprehensive overview of data structures from basics to advanced, organized by their applications in different domains. This will be a substantial reference guide.I've created a comprehensive guide covering data structures from basics to advanced applications across all the domains you mentioned. The guide is organized by complexity and application areas, including:

**Key highlights:**

- **Fundamentals**: Arrays, linked lists, stacks, queues, trees, graphs
- **Database Systems**: B+ trees, LSM trees, skip lists, bloom filters for both SQL and NoSQL
- **Advanced Applications**: Merkle trees for blockchain, tries for compilers, consistent hashing for distributed systems
- **Domain-Specific**: Routing tables for networking, page tables for OS, inverted indexes for search engines
- **Big Data**: Stream processing structures, approximation algorithms, distributed hash tables

Each section includes real-world usage examples and performance characteristics. This should serve as a complete reference for understanding which data structures are critical in different software engineering contexts.

Would you like me to elaborate on any specific domain or data structure? I can also provide implementation examples or dive deeper into the theoretical aspects of any particular area.

## Complete Data Structures Guide: From Basics to Advanced Applications

## 1. Fundamental Data Structures

### Linear Data Structures

- **Arrays**: Contiguous memory allocation, O(1) access
- **Linked Lists**: Dynamic memory, O(n) search, O(1) insertion/deletion
- **Stacks**: LIFO principle, function calls, expression evaluation
- **Queues**: FIFO principle, process scheduling, breadth-first search
- **Deques**: Double-ended queues, sliding window problems

### Non-Linear Data Structures

- **Trees**: Hierarchical structure, file systems, decision trees
- **Graphs**: Vertices and edges, social networks, routing algorithms

## 2. Advanced Tree Structures

### Self-Balancing Trees

- **AVL Trees**: Height-balanced BST, guaranteed O(log n) operations
- **Red-Black Trees**: Used in C++ STL map, Java TreeMap
- **Splay Trees**: Self-adjusting BST, recently accessed nodes move to root
- **Treaps**: Randomized BST using heap property

### Specialized Trees

- **B-Trees**: Multi-way search trees, database indexing
- **B+ Trees**: Leaf nodes linked, range queries in databases
- **Segment Trees**: Range queries and updates in O(log n)
- **Fenwick Trees (Binary Indexed Trees)**: Efficient prefix sum calculations
- **Trie (Prefix Trees)**: String searching, autocomplete systems
- **Suffix Trees**: Pattern matching, DNA sequencing
- **K-D Trees**: Multi-dimensional data, nearest neighbor search

## 3. Database-Specific Data Structures

### SQL Database Structures

- **B+ Trees**: Primary indexing structure in most RDBMS
  - Used in: MySQL InnoDB, PostgreSQL, SQL Server
  - Optimized for disk-based storage
- **Hash Indexes**: O(1) equality lookups
- **Bitmap Indexes**: Efficient for low-cardinality data
- **LSM Trees (Log-Structured Merge Trees)**: Write-optimized storage
  - Used in: Apache Cassandra, RocksDB, LevelDB

### NoSQL Database Structures

- **Consistent Hashing**: Distributed hash tables, load balancing
  - Used in: Amazon DynamoDB, Apache Cassandra
- **Merkle Trees**: Data integrity verification in distributed systems
- **Skip Lists**: Probabilistic alternative to balanced trees
  - Used in: Redis sorted sets, LevelDB
- **Bloom Filters**: Space-efficient probabilistic data structure
  - Used in: Apache Cassandra, BigTable
- **HyperLogLog**: Cardinality estimation with minimal memory
- **Count-Min Sketch**: Frequency estimation in data streams

## 4. Advanced Graph Structures

### Graph Representations

- **Adjacency Matrix**: O(V²) space, O(1) edge lookup
- **Adjacency List**: O(V + E) space, efficient for sparse graphs
- **Edge List**: Simple representation for algorithms

### Specialized Graph Structures

- **Directed Graphs**: Web page linking, task scheduling
- **Directed Acyclic Graphs (DAGs)**: Dependency graphs, blockchain
- **Weighted Graphs**: Network routing, shortest path algorithms
- **Bipartite Graphs**: Matching problems, recommendation systems
- **Planar Graphs**: Circuit design, geographic mapping

## 5. Operating Systems Data Structures

### Memory Management

- **Free Lists**: Track available memory blocks
- **Buddy System**: Binary tree-based memory allocation
- **Slab Allocator**: Object caching in kernel
- **Page Tables**: Virtual to physical address translation
  - Multi-level page tables, inverted page tables

### Process Management

- **Process Control Blocks (PCB)**: Process state information
- **Ready Queues**: Multi-level feedback queues for scheduling
- **Wait Queues**: Blocked processes waiting for resources

### File Systems

- **Inodes**: File metadata storage in Unix-like systems
- **B-Trees**: Directory indexing in NTFS, ext4
- **Extent Trees**: Contiguous block allocation
- **Journal Structures**: File system consistency

## 6. Compiler Data Structures

### Lexical Analysis

- **Symbol Tables**: Variable/function scope and type information
  - Implemented using hash tables or balanced trees
- **Finite Automata**: Token recognition
- **Trie**: Keyword recognition, symbol tables

### Syntax Analysis

- **Parse Trees**: Concrete syntax representation
- **Abstract Syntax Trees (AST)**: Simplified parse trees
- **LR/LALR Parse Tables**: Bottom-up parsing

### Semantic Analysis

- **Symbol Tables**: Variable and function information
  - Hash tables with chaining
  - Scoped symbol tables using stacks
- **Type Trees**: Type checking and inference

### Code Generation

- **Control Flow Graphs**: Program flow analysis
- **Data Flow Graphs**: Variable usage analysis
- **Intermediate Representation**: Three-address code, SSA form

## 7. Networking Data Structures

### Routing

- **Routing Tables**: IP address to next-hop mapping
- **Trie-based IP Lookup**: Longest prefix matching
- **Radix Trees**: Compressed tries for routing tables

### Network Protocols

- **Hash Tables**: ARP tables, DNS caches
- **Priority Queues**: QoS packet scheduling
- **Ring Buffers**: Network packet buffering
- **Sliding Window**: TCP flow control

### Network Security

- **Bloom Filters**: Intrusion detection systems
- **Hash Chains**: One-time password systems
- **Merkle Trees**: Secure multicast protocols

## 8. Cryptographic Data Structures

### Hash-Based Structures

- **Merkle Trees**: Blockchain integrity, certificate transparency
- **Hash Chains**: Secure audit logs, one-time signatures
- **Merkle DAGs**: IPFS content addressing

### Advanced Cryptographic Structures

- **Accumulators**: Cryptographic sets with membership proofs
- **Zero-Knowledge Proofs**: Privacy-preserving verification
- **Commitment Schemes**: Secure multiparty computation

## 9. Blockchain Data Structures

### Core Structures

- **Blockchain**: Linked list of cryptographically linked blocks
- **Merkle Trees**: Transaction integrity within blocks
- **Patricia Tries**: Ethereum state trees
  - Modified Merkle Patricia Trie for key-value storage

### Consensus Mechanisms

- **Hash Pointers**: Tamper-evident linking
- **Merkle Mountain Ranges**: Efficient append-only logs
- **Sparse Merkle Trees**: Efficient state updates

### Smart Contract Storage

- **State Tries**: Ethereum account state storage
- **Storage Tries**: Contract storage organization
- **Receipt Tries**: Transaction receipt organization

## 10. Search Engine Data Structures

### Text Processing

- **Inverted Index**: Document-term mapping
  - Term frequency, document frequency storage
- **Suffix Arrays**: Efficient string searching
- **N-gram Indexes**: Phrase and proximity searching

### Web Graph Analysis

- **Web Graph**: Hyperlink structure representation
- **Link Analysis**: PageRank calculation structures
- **Anchor Text Indexes**: Link text indexing

### Query Processing

- **Query Trees**: Search query parsing and optimization
- **Result Heaps**: Top-k result retrieval
- **Caching Structures**: Query result caching

## 11. Big Data Structures

### Distributed Data Structures

- **Distributed Hash Tables (DHT)**: Chord, Pastry protocols
- **Consistent Hashing**: Data distribution across nodes
- **Vector Clocks**: Distributed system event ordering
- **Gossip Protocols**: Information dissemination

### Stream Processing

- **Sliding Windows**: Time-based and count-based windows
- **Watermarks**: Out-of-order event handling
- **State Backends**: Fault-tolerant state storage

### Approximation Structures

- **Count-Min Sketch**: Frequency estimation
- **HyperLogLog**: Cardinality estimation
- **Top-K Sketches**: Heavy hitter detection
- **Reservoir Sampling**: Random sampling from streams

## 12. Embedded Systems Data Structures

### Memory-Constrained Structures

- **Static Arrays**: Fixed-size data storage
- **Circular Buffers**: FIFO queues in fixed memory
- **Bit Arrays**: Space-efficient boolean storage
- **Packed Structures**: Memory alignment optimization

### Real-Time Structures

- **Priority Queues**: Task scheduling
- **Ring Buffers**: Interrupt-driven data collection
- **State Machines**: Event-driven programming

## 13. Machine Learning Data Structures

### Core ML Structures

- **Decision Trees**: Classification and regression
- **Random Forests**: Ensemble of decision trees
- **Neural Network Graphs**: Computational graphs
- **KD-Trees**: Nearest neighbor search

### Feature Engineering

- **Feature Hashing**: Dimensionality reduction
- **Sparse Matrices**: High-dimensional data representation
- **Embedding Tables**: Dense vector representations

## 14. Performance Considerations

### Time Complexities

- **Access**: Array O(1), Linked List O(n)
- **Search**: BST O(log n), Hash Table O(1) average
- **Insertion**: Dynamic Array O(1) amortized, BST O(log n)
- **Deletion**: Hash Table O(1), BST O(log n)

### Space Complexities

- **Memory Overhead**: Pointers, metadata storage
- **Cache Locality**: Array vs. Linked structures
- **Memory Fragmentation**: Dynamic allocation concerns

### Choosing the Right Structure

- **Read vs. Write Heavy**: Different optimization strategies
- **Memory Constraints**: Embedded vs. server applications
- **Concurrency Requirements**: Thread-safe structures
- **Distribution Needs**: Network-aware data structures

## 15. Implementation Languages and Libraries

### C/C++

- STL containers: vector, map, unordered_map, set
- Custom implementations for performance-critical code

### Java

- Collections Framework: ArrayList, HashMap, TreeMap
- Concurrent collections for multi-threaded applications

### Python

- Built-in: list, dict, set, tuple
- Libraries: NumPy arrays, Pandas DataFrames

### Specialized Libraries

- **Graph Processing**: NetworkX (Python), SNAP (C++)
- **Numerical Computing**: BLAS, LAPACK
- **Database Engines**: RocksDB, LevelDB
- **Distributed Systems**: Apache Kafka, Redis

This comprehensive guide covers the essential data structures used across different domains of computer science and software engineering. Each structure has specific use cases where it excels, and understanding these applications is crucial for system design and optimization.

I'll create a comprehensive guide focusing on data structures implementation and usage in Go, Rust, Scala, Haskell, Python, and TypeScript, showing language-specific features and idiomatic patterns.I've created a comprehensive guide covering data structures in Go, Rust, Scala, Haskell, Python, and TypeScript. This guide focuses on:

**Key Language-Specific Features:**

1. **Go**: 
   - CSP concurrency with channels
   - Simple but powerful built-ins (slices, maps)
   - Excellent for systems programming

2. **Rust**: 
   - Ownership system preventing memory issues
   - Zero-cost abstractions
   - Lock-free concurrent structures

3. **Scala**: 
   - Immutable persistent data structures
   - Actor model for distributed systems
   - Powerful type system with higher-kinded types

4. **Haskell**: 
   - Pure functional programming
   - Lazy evaluation enabling infinite structures
   - Advanced monadic patterns

5. **Python**: 
   - Rich built-in collections
   - NumPy for scientific computing
   - Dynamic typing with extensive libraries

6. **TypeScript**: 
   - Static typing for JavaScript
   - Advanced type system features
   - Excellent for large-scale applications

The guide includes practical code examples, performance comparisons, and cross-language analysis to help you choose the right language and data structure for your specific use case.

Would you like me to dive deeper into any specific language or provide more implementation examples for particular data structures?

## Data Structures in Go, Rust, Scala, Haskell, Python & TypeScript

## 1. Go (Golang) Data Structures

### Built-in Types

```go
// Arrays - Fixed size
var arr [5]int = [5]int{1, 2, 3, 4, 5}

// Slices - Dynamic arrays
slice := []int{1, 2, 3}
slice = append(slice, 4, 5)

// Maps - Hash tables
m := make(map[string]int)
m["key"] = 42

// Channels - CSP communication
ch := make(chan int, 100) // Buffered channel
```

### Custom Data Structures

```go
// Linked List
type Node struct {
    data int
    next *Node
}

// Binary Tree
type TreeNode struct {
    val   int
    left  *TreeNode
    right *TreeNode
}

// Trie for string operations
type TrieNode struct {
    children map[rune]*TrieNode
    isEnd    bool
}

// Graph using adjacency list
type Graph struct {
    vertices map[int][]int
}
```

### Concurrent Data Structures

```go
import "sync"

// Thread-safe counter
type SafeCounter struct {
    mu sync.Mutex
    v  map[string]int
}

// Lock-free operations using channels
type SafeQueue struct {
    items chan interface{}
}
```

### Go-Specific Advanced Structures

- **Sync.Map**: Concurrent map for high-performance scenarios
- **Container/heap**: Priority queue implementation
- **Container/ring**: Circular lists
- **Context trees**: Request scoping and cancellation

### Performance Considerations

- Garbage collector optimizations for pointer-heavy structures
- Memory alignment for structs
- Channel-based patterns for concurrent access
- Interface{} vs. generic types (Go 1.18+)

---

## 2. Rust Data Structures

### Ownership-Based Collections
```rust
// Vec - Growable arrays
let mut vec = vec![1, 2, 3];
vec.push(4);

// HashMap - Hash tables
use std::collections::HashMap;
let mut map = HashMap::new();
map.insert("key", 42);

// BTreeMap - Ordered map
use std::collections::BTreeMap;
let mut btree = BTreeMap::new();
```

### Memory-Safe Linked Structures
```rust
// Box for heap allocation
type Link<T> = Option<Box<Node<T>>>;

struct Node<T> {
    elem: T,
    next: Link<T>,
}

// Rc for reference counting
use std::rc::Rc;
use std::cell::RefCell;

type RcNode<T> = Rc<RefCell<Node<T>>>;

// Arc for atomic reference counting (thread-safe)
use std::sync::Arc;
use std::sync::Mutex;

type SafeNode<T> = Arc<Mutex<Node<T>>>;
```

### Advanced Rust Structures
```rust
// Custom allocators
use std::alloc::{Allocator, Global};

// Zero-copy string processing
use std::borrow::Cow;

// Lock-free data structures
use std::sync::atomic::{AtomicPtr, Ordering};

struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}
```

### Rust-Specific Features

- **Ownership system**: Prevents data races and memory leaks
- **Lifetimes**: Ensures references are valid
- **Send/Sync traits**: Thread safety guarantees
- **Zero-cost abstractions**: Performance without overhead
- **Pattern matching**: Powerful destructuring

### Specialized Crates

- **Serde**: Serialization framework
- **Rayon**: Data parallelism
- **Crossbeam**: Lock-free concurrency
- **Petgraph**: Graph data structures

---

## 3. Scala Data Structures

### Immutable Collections

```scala
// Lists - Persistent linked lists
val list = List(1, 2, 3)
val newList = 0 :: list // Prepend

// Vector - Efficient random access
val vector = Vector(1, 2, 3, 4, 5)

// Map - Persistent hash maps
val map = Map("a" -> 1, "b" -> 2)

// Set - No duplicates
val set = Set(1, 2, 3)
```

### Mutable Collections
```scala
import scala.collection.mutable

val buffer = mutable.ArrayBuffer[Int]()
val hashMap = mutable.HashMap[String, Int]()
val hashSet = mutable.HashSet[Int]()
```

### Functional Data Structures
```scala
// Streams (lazy evaluation)
val stream = Stream.from(1).take(1000000)

// Trees with pattern matching
sealed trait Tree[+A]
case object Empty extends Tree[Nothing]
case class Node[A](value: A, left: Tree[A], right: Tree[A]) extends Tree[A]

// Monadic structures
import cats.data.State
import cats.implicits._

// Writer monad for logging
import cats.data.Writer
type LoggedInt = Writer[List[String], Int]
```

### Advanced Scala Patterns
```scala
// Zipper for tree navigation
case class Zipper[A](focus: Tree[A], context: List[Context[A]])

// Phantom types for type safety
sealed trait Sorted
sealed trait Unsorted
class Array[A, S](private val data: scala.Array[A])

// Type classes
trait Monoid[A] {
  def empty: A
  def combine(x: A, y: A): A
}
```

### Actor Model (Akka)
```scala
import akka.actor.{Actor, ActorSystem, Props}

// Distributed data structures
class DistributedMap extends Actor {
  var data = Map[String, Any]()
  
  def receive = {
    case Get(key) => sender() ! data.get(key)
    case Put(key, value) => data = data + (key -> value)
  }
}
```

### Scala-Specific Features
- **Persistent data structures**: Structural sharing
- **For-comprehensions**: Monadic operations
- **Implicit conversions**: Seamless type extensions
- **Higher-kinded types**: Generic abstractions
- **Macros**: Compile-time code generation

---

## 4. Haskell Data Structures

### Basic Types
```haskell
-- Lists - Linked lists with lazy evaluation
list = [1, 2, 3, 4, 5]
infinite = [1..]

-- Tuples - Product types
pair = (1, "hello")
triple = (1, 2, 3)

-- Maybe - Null safety
safeDivide :: Double -> Double -> Maybe Double
safeDivide _ 0 = Nothing
safeDivide x y = Just (x / y)
```

### Algebraic Data Types
```haskell
-- Binary trees
data Tree a = Empty | Node a (Tree a) (Tree a)
  deriving (Show, Eq)

-- Rose trees (n-ary trees)
data Rose a = Rose a [Rose a]

-- Zippers for efficient navigation
data TreeZipper a = TreeZipper (Tree a) [TreeContext a]
data TreeContext a = LeftTree a (Tree a) | RightTree a (Tree a)
```

### Functional Data Structures
```haskell
-- Finger trees (efficient sequences)
data FingerTree a = Empty
                 | Single a
                 | Deep (Digit a) (FingerTree (Node a)) (Digit a)

-- Red-Black trees
data Color = Red | Black
data RBTree a = E | T Color (RBTree a) a (RBTree a)

-- Skew heaps
data SkewHeap a = Empty | Node a (SkewHeap a) (SkewHeap a)
```

### Monadic Structures
```haskell
-- State monad for stateful computations
import Control.Monad.State

type Stack = [Int]
type StackState = State Stack

push :: Int -> StackState ()
push x = modify (x:)

-- Reader monad for dependency injection
import Control.Monad.Reader

type Config = String
type App = Reader Config

-- STM for concurrent programming
import Control.Concurrent.STM

data Account = Account (TVar Int)

transfer :: Account -> Account -> Int -> STM ()
transfer (Account from) (Account to) amount = do
  fromBalance <- readTVar from
  when (fromBalance >= amount) $ do
    writeTVar from (fromBalance - amount)
    modifyTVar to (+ amount)
```

### Advanced Haskell Patterns
```haskell
-- Free monads
data Free f a = Pure a | Free (f (Free f a))

-- Lenses for nested data access
{-# LANGUAGE TemplateHaskell #-}
import Control.Lens

data Person = Person { _name :: String, _age :: Int }
makeLenses ''Person

-- Generic programming
{-# LANGUAGE DeriveGeneric #-}
import GHC.Generics

data Tree a = Leaf | Branch (Tree a) a (Tree a)
  deriving (Generic, Show)
```

### Haskell-Specific Features
- **Lazy evaluation**: Infinite data structures
- **Type classes**: Ad-hoc polymorphism
- **Higher-order functions**: Functions as first-class values
- **Purity**: Immutable by default
- **Pattern matching**: Powerful data deconstruction

---

## 5. Python Data Structures

### Built-in Collections
```python
# Lists - Dynamic arrays
lst = [1, 2, 3]
lst.append(4)

# Dictionaries - Hash tables
d = {'key': 'value'}
d.update({'new_key': 'new_value'})

# Sets - No duplicates
s = {1, 2, 3}
s.add(4)

# Tuples - Immutable sequences
t = (1, 2, 3)

# Named tuples
from collections import namedtuple
Point = namedtuple('Point', ['x', 'y'])
```

### Advanced Collections
```python
from collections import (
    defaultdict, Counter, deque, 
    ChainMap, OrderedDict
)

# Deque - Double-ended queue
dq = deque([1, 2, 3])
dq.appendleft(0)
dq.append(4)

# Counter - Multiset
counter = Counter(['a', 'b', 'c', 'a'])

# Default dict
dd = defaultdict(list)
dd['key'].append('value')
```

### Custom Data Structures
```python
# Linked List
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

# Binary Tree with traversal
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

# Trie for string operations
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
```

### NumPy and Scientific Computing
```python
import numpy as np

# N-dimensional arrays
arr = np.array([[1, 2], [3, 4]])
sparse_matrix = np.zeros((1000, 1000))

# Structured arrays
dt = np.dtype([('name', 'U10'), ('age', 'i4')])
people = np.array([('Alice', 25), ('Bob', 30)], dtype=dt)

# Pandas DataFrames
import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
```

### Concurrent Data Structures
```python
import threading
from queue import Queue, LifoQueue, PriorityQueue
import multiprocessing as mp

# Thread-safe queue
q = Queue()

# Process-safe structures
manager = mp.Manager()
shared_dict = manager.dict()
shared_list = manager.list()

# Locks and synchronization
lock = threading.Lock()
condition = threading.Condition()
```

### Python-Specific Advanced Patterns
```python
# Descriptors for computed properties
class Property:
    def __get__(self, obj, objtype=None):
        return obj._value
    def __set__(self, obj, value):
        obj._value = value

# Context managers for resource management
class FileManager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# Generators for memory efficiency
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Decorators for caching
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_function(n):
    return n ** 2
```

---

## 6. TypeScript Data Structures

### Basic Types and Interfaces
```typescript
// Arrays with type safety
const numbers: number[] = [1, 2, 3, 4, 5];
const strings: Array<string> = ['a', 'b', 'c'];

// Maps and Sets
const map = new Map<string, number>();
map.set('key', 42);

const set = new Set<number>([1, 2, 3]);

// Objects with index signatures
interface Dictionary<T> {
  [key: string]: T;
}

const dict: Dictionary<number> = { 'one': 1, 'two': 2 };
```

### Generic Data Structures
```typescript
// Linked List with generics
class ListNode<T> {
  constructor(
    public data: T,
    public next: ListNode<T> | null = null
  ) {}
}

class LinkedList<T> {
  private head: ListNode<T> | null = null;
  
  append(data: T): void {
    const newNode = new ListNode(data);
    if (!this.head) {
      this.head = newNode;
      return;
    }
    
    let current = this.head;
    while (current.next) {
      current = current.next;
    }
    current.next = newNode;
  }
}

// Binary Tree with type constraints
interface Comparable {
  compareTo(other: this): number;
}

class BinarySearchTree<T extends Comparable> {
  private root: TreeNode<T> | null = null;
  
  insert(value: T): void {
    this.root = this.insertNode(this.root, value);
  }
  
  private insertNode(node: TreeNode<T> | null, value: T): TreeNode<T> {
    if (!node) return new TreeNode(value);
    
    if (value.compareTo(node.value) < 0) {
      node.left = this.insertNode(node.left, value);
    } else {
      node.right = this.insertNode(node.right, value);
    }
    
    return node;
  }
}
```

### Advanced Type System Features
```typescript
// Conditional types for data structure operations
type Head<T extends readonly unknown[]> = T extends readonly [infer H, ...unknown[]] ? H : never;
type Tail<T extends readonly unknown[]> = T extends readonly [unknown, ...infer Tail] ? Tail : [];

// Template literal types
type EventMap = {
  click: MouseEvent;
  change: Event;
  custom: CustomEvent;
};

type EventKeys = keyof EventMap; // 'click' | 'change' | 'custom'

// Mapped types for transformations
type Optional<T> = {
  [P in keyof T]?: T[P];
};

type ReadOnly<T> = {
  readonly [P in keyof T]: T[P];
};
```

### Functional Data Structures
```typescript
// Immutable list using recursion
type ImmutableList<T> = {
  readonly head: T;
  readonly tail: ImmutableList<T>;
} | null;

const cons = <T>(head: T, tail: ImmutableList<T>): ImmutableList<T> => ({
  head,
  tail
});

// Option type (Maybe monad)
abstract class Option<T> {
  abstract map<U>(f: (value: T) => U): Option<U>;
  abstract flatMap<U>(f: (value: T) => Option<U>): Option<U>;
  abstract getOrElse(defaultValue: T): T;
}

class Some<T> extends Option<T> {
  constructor(private value: T) { super(); }
  
  map<U>(f: (value: T) => U): Option<U> {
    return new Some(f(this.value));
  }
  
  flatMap<U>(f: (value: T) => Option<U>): Option<U> {
    return f(this.value);
  }
  
  getOrElse(defaultValue: T): T {
    return this.value;
  }
}

class None<T> extends Option<T> {
  map<U>(f: (value: T) => U): Option<U> {
    return new None<U>();
  }
  
  flatMap<U>(f: (value: T) => Option<U>): Option<U> {
    return new None<U>();
  }
  
  getOrElse(defaultValue: T): T {
    return defaultValue;
  }
}
```

### Async Data Structures
```typescript
// Promise-based queue
class AsyncQueue<T> {
  private queue: T[] = [];
  private waitingResolvers: Array<(value: T) => void> = [];
  
  enqueue(item: T): void {
    if (this.waitingResolvers.length > 0) {
      const resolve = this.waitingResolvers.shift()!;
      resolve(item);
    } else {
      this.queue.push(item);
    }
  }
  
  dequeue(): Promise<T> {
    if (this.queue.length > 0) {
      return Promise.resolve(this.queue.shift()!);
    }
    
    return new Promise<T>((resolve) => {
      this.waitingResolvers.push(resolve);
    });
  }
}

// Observable streams
interface Observer<T> {
  next(value: T): void;
  error(error: any): void;
  complete(): void;
}

class Observable<T> {
  constructor(
    private subscribe: (observer: Observer<T>) => () => void
  ) {}
  
  map<U>(transform: (value: T) => U): Observable<U> {
    return new Observable<U>((observer) => {
      return this.subscribe({
        next: (value) => observer.next(transform(value)),
        error: (error) => observer.error(error),
        complete: () => observer.complete()
      });
    });
  }
}
```

### TypeScript-Specific Features
- **Structural typing**: Duck typing with compile-time checks
- **Union and intersection types**: Flexible type combinations
- **Type guards**: Runtime type checking
- **Decorators**: Metadata and AOP patterns
- **Module system**: ES6 modules with type information

---

## 7. Cross-Language Comparisons

### Memory Management
| Language | Strategy | Data Structure Impact |
|----------|----------|---------------------|
| Go | Garbage collected | Simple pointers, channel-based sharing |
| Rust | Ownership system | Explicit lifetime management, zero-cost |
| Scala | JVM garbage collected | Persistent structures, structural sharing |
| Haskell | Lazy garbage collected | Infinite structures, thunk-based evaluation |
| Python | Reference counting + GC | Flexible but potential memory overhead |
| TypeScript | JavaScript GC | Similar to Python, but with type safety |

### Concurrency Models
| Language | Model | Data Structure Implications |
|----------|-------|---------------------------|
| Go | CSP with goroutines | Channel-based communication |
| Rust | Fearless concurrency | Send/Sync traits, atomic operations |
| Scala | Actor model (Akka) | Immutable message passing |
| Haskell | STM, Par monad | Pure functional concurrency |
| Python | GIL + threading/async | Limited parallelism, async/await |
| TypeScript | Event loop | Promise-based async operations |

### Type System Strengths
- **Go**: Simple, fast compilation, excellent for systems programming
- **Rust**: Memory safety without GC, zero-cost abstractions
- **Scala**: Powerful type system, functional/OOP hybrid
- **Haskell**: Pure functional, lazy evaluation, advanced type features
- **Python**: Dynamic typing, rapid prototyping, extensive libraries
- **TypeScript**: Gradual typing, JavaScript interop, modern language features

### Performance Characteristics
1. **Compile-time optimization**: Rust > Haskell > Scala > Go > TypeScript > Python
2. **Runtime performance**: Rust ≈ Go > Scala > Haskell > TypeScript > Python
3. **Development speed**: Python > TypeScript > Go > Scala > Haskell > Rust
4. **Memory efficiency**: Rust > Go > Haskell > Scala > TypeScript > Python

This comprehensive guide shows how each language approaches data structures differently, leveraging their unique features and paradigms for optimal performance and expressiveness.


## 🔹 Basic Data Structures

1. **Array**

   * Collection of items stored at contiguous memory locations.
   * Example: `[10, 20, 30, 40]`

2. **String** (special kind of array of characters)

   * Example: `"hello"`

3. **Linked List**

   * Nodes connected by pointers (`next` or `prev`).
   * Types: Singly, Doubly, Circular.

4. **Stack** (LIFO – Last In First Out)

   * Example: Browser back button, Undo operation.

5. **Queue** (FIFO – First In First Out)

   * Variants: Circular Queue, Deque, Priority Queue.

6. **Hash Table (Hash Map)**

   * Stores key-value pairs with fast lookup using hashing.
   * Example: `{ "name": "Alex", "age": 25 }`

---

## 🔹 Non-Linear Data Structures

7. **Tree**

   * Hierarchical structure with root → children.
   * Examples:

     * Binary Tree
     * Binary Search Tree (BST)
     * Heap
     * Trie (Prefix Tree)
     * AVL / Red-Black Trees

8. **Graph**

   * Nodes (vertices) + edges (connections).
   * Types: Directed, Undirected, Weighted, Unweighted, Cyclic, Acyclic.

---

## 🔹 Advanced / Abstract Data Structures

9. **Disjoint Set (Union-Find)**

   * Used for grouping elements into disjoint sets.
   * Example: Kruskal’s MST algorithm.

10. **Segment Tree / Fenwick Tree (BIT)**

* For range queries (sum, min, max).

11. **Bloom Filter**

* Probabilistic structure for membership testing.

12. **Skip List**

* Faster alternative to linked lists, supports binary search.

---

👉 **Summary:**

* **Linear DS** → Array, Linked List, Stack, Queue, Hash Table
* **Non-linear DS** → Tree, Graph
* **Advanced DS** → Disjoint Set, Segment Tree, Trie, Bloom Filter, Skip List

---

Do you want me to create a **hierarchy chart (ASCII tree)** that shows all data structures in categories (Linear, Non-Linear, Advanced) so you can visualize the whole DS landscape at once?

Ahh 🔥 this is a deeper level — you’re asking not just the **classic DS taught in DSA**, but the **specialized DS used in real-world systems** like **databases, blockchain, embedded systems, and critical software**. Perfect — let’s map it out.

---

# 🔹 Data Structures in **Databases (SQL & NoSQL)**

Databases are built on **specialized DS** for indexing, searching, and storing efficiently.

### **Relational Databases (SQL)**

* **B-Tree / B+ Tree** → most common for indexing in MySQL, PostgreSQL, Oracle.
* **Heap File Organization** → for unordered table storage.
* **Hash Index** → used in memory-optimized engines (e.g., PostgreSQL hash index, MemSQL).
* **Bitmap Index** → useful for low-cardinality columns.
* **Trie / Radix Trees** → some text indexing.

### **NoSQL Databases**

* **LSM Trees (Log-Structured Merge Trees)** → RocksDB, Cassandra, LevelDB.
* **Skip Lists** → Redis uses skip lists for sorted sets (ZSET).
* **Hash Tables** → MongoDB, Redis, DynamoDB for fast key-value lookup.
* **Merkle Trees** → Cassandra, DynamoDB for consistency checks.

---

# 🔹 Data Structures in **Critical Software (OS, Compilers, Networking)**

### **Operating Systems**

* **Process Control Blocks** (PCB) → implemented with linked lists/queues.
* **Page Tables** → hierarchical trees for memory management.
* **Priority Queues (Heaps)** → CPU scheduling.
* **B-Trees** → file systems (e.g., NTFS, HFS+).
* **Red-Black Trees** → Linux kernel (task scheduling, memory).

### **Compilers**

* **Abstract Syntax Trees (AST)** → parse programs.
* **Symbol Tables** → hash tables for variable/function lookup.
* **Directed Graphs (DAGs)** → for optimization (common subexpression elimination).

### **Networking**

* **Tries (Patricia Trie / Radix Tree)** → IP routing tables.
* **Ring Buffers** → packet queues in NIC drivers.

---

# 🔹 Data Structures in **Embedded Systems**

* **Circular Buffers (Ring Buffers)** → real-time data streaming.
* **Lookup Tables** → precomputed values for fast response.
* **Finite State Machines (FSM)** → for control logic.
* **Compressed Trees** → to save memory.

---

# 🔹 Data Structures in **Blockchain & Cryptosystems**

* **Merkle Tree** → used in Bitcoin, Ethereum for transaction validation.
* **Patricia Merkle Trie (Radix Trie + Merkle Tree)** → Ethereum state storage.
* **Linked Lists** → blockchain itself is a linked list of blocks.
* **Bloom Filters** → light clients for quick membership testing.
* **Hash Maps** → caching and peer tracking in P2P networks.

---

# 🔹 Data Structures in **Search Engines & Big Data**

* **Inverted Index** → used in Elasticsearch, Lucene for full-text search.
* **Suffix Trees / Suffix Arrays** → string search, DNA sequencing.
* **LSM Trees** → huge datasets, write-optimized.

---

✅ **Summary**

* **Databases (SQL/NoSQL)** → B-Tree, B+Tree, LSM Tree, Hash Table, Skip List, Merkle Tree
* **OS & Critical Software** → Red-Black Tree, AST, DAG, Priority Queue, Trie
* **Embedded Systems** → Circular Buffer, FSM, Lookup Table
* **Blockchain** → Merkle Tree, Patricia Trie, Bloom Filter, Linked List
* **Search Engines / Big Data** → Inverted Index, Suffix Tree, LSM Tree

---

⚡This is why in **real systems**, DS is not just *Array/Stack/Queue* — they use specialized hybrids tuned for **speed, concurrency, persistence, and fault tolerance**.

👉 Do you want me to make a **mapping table** like:
**System → Data Structure Used → Why it’s chosen** ? That way you’ll have a quick reference for databases, blockchain, OS, embedded, etc.

### Basic Data Structures
These are foundational building blocks used in almost every programming and system design context. They handle simple data organization and manipulation.

- **Arrays**: Fixed-size collections of elements of the same type, accessed via indices. Efficient for random access (O(1) time). Used in: Basic storage, matrices in embedded systems, buffers in OS and networking.
- **Linked Lists**: Dynamic collections where each element (node) points to the next. Variants include singly-linked, doubly-linked, and circular. Good for insertions/deletions (O(1) if position known). Used in: Memory management in OS (e.g., free lists), queues in compilers.
- **Stacks**: LIFO (Last In, First Out) structure. Operations: push, pop. Implemented via arrays or linked lists. Used in: Function call stacks in OS/compilers, undo mechanisms in software, parsing expressions.
- **Queues**: FIFO (First In, First Out) structure. Operations: enqueue, dequeue. Variants: circular queues, priority queues. Used in: Task scheduling in OS, breadth-first search in graphs, buffering in networking (e.g., packet queues).
- **Hash Tables (Maps/Dictionaries)**: Key-value pairs with average O(1) access via hashing. Handles collisions via chaining or open addressing. Used in: Symbol tables in compilers, caching in databases and search engines.

### Intermediate Data Structures
These build on basics and introduce more efficiency for specific operations like searching or sorting.

- **Trees**: Hierarchical structures with nodes having children. Basic binary trees allow O(log n) operations if balanced.
  - **Binary Search Trees (BST)**: Sorted binary trees for efficient search/insert/delete (O(log n) average). Used in: Indexing in databases (e.g., SQL B-trees), file systems in OS.
  - **Balanced Trees (AVL, Red-Black)**: Self-balancing BSTs ensuring O(log n) worst-case. Used in: Java's TreeMap, process scheduling in OS, blockchain transaction indexing.
- **Heaps**: Complete binary trees satisfying heap property (min-heap or max-heap). Efficient for priority extraction (O(log n)). Used in: Priority queues in OS (e.g., job scheduling), Dijkstra's algorithm in networking, heap sort in compilers.
- **Graphs**: Nodes (vertices) connected by edges. Representations: adjacency lists/matrices. Directed/undirected, weighted/unweighted.
  - Used in: Social networks (e.g., friend graphs), routing in networking (e.g., shortest paths), dependency graphs in compilers, blockchain (transaction graphs).

### Advanced Data Structures
These are optimized for complex scenarios, often with amortized or logarithmic time complexities.

- **Tries (Prefix Trees)**: Tree-like structure for storing strings, where each node represents a character. Efficient for prefix-based searches (O(m) where m is key length). Used in: Autocomplete in search engines, dictionary implementations, IP routing in networking.
- **Segment Trees**: Binary trees for range queries and updates (O(log n)). Used in: Geometric queries in graphics software, range sum/max in big data analytics.
- **Fenwick Trees (Binary Indexed Trees)**: Efficient for prefix sums and updates (O(log n)). Used in: Cumulative frequency tables in databases, competitive programming for big data.
- **Disjoint Set Union (DSU/Union-Find)**: Tracks partitions of sets with union and find operations (near O(1) with path compression). Used in: Kruskal's algorithm for MST in graphs, connected components in networking, cycle detection in blockchain smart contracts.
- **Skip Lists**: Probabilistic layered linked lists for fast search (O(log n) expected). Used in: Redis (NoSQL) for sorted sets, concurrent data access in critical software.
- **Bloom Filters**: Probabilistic space-efficient sets for membership testing (false positives possible). Used in: Caching in big data (e.g., Hadoop), duplicate detection in search engines, blockchain light clients.
- **Suffix Arrays/Trees**: For efficient substring searches in strings (O(n log n) construction). Used in: Text indexing in search engines (e.g., Google), bioinformatics in big data.

| Data Structure | Time Complexity (Search/Insert/Delete) | Space Complexity | Key Advantages |
|---------------|---------------------------------------|------------------|---------------|
| Array | O(1)/O(n)/O(n) | O(n) | Fast access, cache-friendly. |
| Linked List | O(n)/O(1)/O(1) | O(n) | Dynamic size, easy modifications. |
| Stack/Queue | O(1) for core ops | O(n) | Simple LIFO/FIFO semantics. |
| Hash Table | O(1) avg | O(n) | Fast lookups, flexible keys. |
| BST | O(log n) avg | O(n) | Sorted order maintained. |
| AVL/Red-Black Tree | O(log n) | O(n) | Balanced, worst-case guarantees. |
| Heap | O(log n) for insert/extract | O(n) | Efficient priority management. |
| Graph (Adj List) | Varies (e.g., DFS O(V+E)) | O(V+E) | Models relationships. |
| Trie | O(m) | O(alphabet * n) | Prefix efficiency. |
| Segment Tree | O(log n) | O(n) | Range operations. |
| Bloom Filter | O(1) | O(bits) | Space-saving probabilistic. |

### Critical Data Structures in Specific Domains
These are the most commonly used and pivotal ones in real-world systems, selected for efficiency, scalability, and reliability.

#### Databases (SQL and NoSQL)
- **B-Trees/B+ Trees**: Multi-way balanced trees for disk-based indexing (O(log n) with high fanout). Critical in SQL (e.g., MySQL InnoDB indexes) for range scans and joins. In NoSQL (e.g., MongoDB), used for secondary indexes.
- **LSM Trees (Log-Structured Merge Trees)**: Write-optimized with sorted runs and merging. Used in NoSQL like Cassandra, RocksDB for high-throughput writes, big data storage.
- **Hash Indexes**: For equality lookups in SQL/NoSQL. Critical in PostgreSQL hash indexes, Redis hashes.
- **Inverted Indexes**: Maps terms to document lists. Used in search-enabled databases (e.g., Elasticsearch) for full-text search.

#### Critical Software (e.g., Real-Time, Safety-Critical Systems)
- **Priority Queues/Heaps**: For event scheduling in real-time OS.
- **Circular Buffers (Queues)**: Fixed-size, overwrite-oldest for logging in safety systems (e.g., avionics software).
- **Red-Black Trees**: Balanced reliability in mission-critical apps (e.g., Linux kernel for process management).

#### Embedded Systems
- **Arrays and Linked Lists**: Memory-constrained, used in sensor data buffers, task lists in RTOS like FreeRTOS.
- **Heaps**: Dynamic allocation in microcontrollers, but often avoided for predictability; min-heaps for timers.
- **Bitsets/Bit Arrays**: Space-efficient for flags/status in hardware interfaces.

#### Blockchain and Cryptosystems
- **Merkle Trees**: Binary trees of hashes for efficient verification (O(log n)). Critical in Bitcoin/Ethereum for block integrity, transaction proofs.
- **Patricia Tries (Radix Trees)**: Compressed tries for key-value storage. Used in Ethereum state trie for accounts/balances.
- **Graphs**: For transaction dependency analysis, consensus protocols (e.g., DAG in IOTA).
- **Bloom Filters**: In Bitcoin SPV clients for transaction filtering without full chain.
- **Elliptic Curve Structures**: In cryptosystems, but more algorithmic; paired with hash tables for key management.

#### Operating Systems
- **Linked Lists**: Process control blocks (PCBs) in ready queues.
- **Trees (e.g., Red-Black in Linux CFS Scheduler)**: For fair scheduling, file system directories (e.g., ext4 uses B-trees).
- **Page Tables (Multi-Level Hash Tables/Trees)**: For virtual memory mapping.
- **Queues**: Interrupt handling, I/O buffers.

#### Compilers
- **Symbol Tables (Hash Tables)**: Variable scoping and lookup.
- **Abstract Syntax Trees (AST)**: Tree representation of code for parsing/optimization.
- **Graphs**: Control flow graphs (CFG) for optimization, dependency graphs for register allocation.
- **Stacks**: For recursive descent parsing.

#### Networking
- **Graphs**: Routing tables (e.g., OSPF uses shortest path trees).
- **Tries**: IP prefix matching in routers (e.g., longest prefix match).
- **Queues**: Packet buffering (e.g., priority queues for QoS).
- **Hash Tables**: Flow tables in switches, NAT in firewalls.

#### Search Engines & Big Data
- **Inverted Indexes**: Core for term-document mapping in Google, Elasticsearch.
- **Tries/Suffix Trees**: Query autocompletion, wildcard searches.
- **Graphs**: PageRank algorithm in search (e.g., web graph).
- **LSM Trees/B-Trees**: In big data stores like BigTable/HBase.
- **Bloom Filters**: Deduplication in Hadoop MapReduce.
- **Segment Trees/Fenwick Trees**: Analytics queries in Spark for aggregations.

This covers a comprehensive spectrum, focusing on practical usage. For implementation details, refer to standard algorithms texts like CLRS. If you need code examples or deeper dives into any, let me know!

I've created a comprehensive guide comparing data structure implementations in Python and Rust. The guide covers:

## Key Features of This Guide:

1. **Complete Implementations**: Full, working code for 10 major data structures in both languages
2. **Real-world Ready**: Production-quality implementations with proper error handling
3. **Comparative Analysis**: Side-by-side comparison showing language-specific approaches
4. **Performance Insights**: Time and space complexity analysis for each structure
5. **Practical Guidance**: When to use each data structure and language

## Covered Data Structures:

- **Linear**: Dynamic Arrays, Linked Lists, Stacks, Queues
- **Hash-based**: Hash Tables/Maps
- **Tree-based**: Binary Trees, Binary Search Trees, Heaps, Tries  
- **Graph-based**: Graphs with common algorithms (BFS, DFS, Dijkstra)

## Key Differences Highlighted:

### Python Advantages:
- More concise and readable syntax
- Built-in garbage collection
- Faster development time
- Rich standard library

### Rust Advantages:
- Memory safety without garbage collection
- Zero-cost abstractions
- Superior performance
- Thread safety guarantees
- Compile-time error detection

The guide includes complete traversal algorithms, search methods, and practical examples for each data structure. Each implementation demonstrates idiomatic usage patterns for both languages, making it an excellent reference for developers working in either ecosystem.

This resource is particularly valuable for developers transitioning between languages or those who need to make informed decisions about which language and data structure to use for specific use cases.

# Complete Data Structures Guide: Python vs Rust

This comprehensive guide provides complete implementations and comparisons of fundamental data structures in both Python and Rust, highlighting the differences in syntax, memory management, and performance characteristics.

## Table of Contents

1. [Arrays and Lists](#arrays-and-lists)
2. [Linked Lists](#linked-lists)
3. [Stacks](#stacks)
4. [Queues](#queues)
5. [Hash Tables/Maps](#hash-tablesmaps)
6. [Binary Trees](#binary-trees)
7. [Binary Search Trees](#binary-search-trees)
8. [Heaps](#heaps)
9. [Graphs](#graphs)
10. [Tries](#tries)
11. [Performance Comparisons](#performance-comparisons)

---

## Arrays and Lists

### Python Implementation

```python
class DynamicArray:
    def __init__(self):
        self.capacity = 4
        self.size = 0
        self.data = [None] * self.capacity
    
    def __getitem__(self, index):
        if 0 <= index < self.size:
            return self.data[index]
        raise IndexError("Index out of bounds")
    
    def __setitem__(self, index, value):
        if 0 <= index < self.size:
            self.data[index] = value
        else:
            raise IndexError("Index out of bounds")
    
    def append(self, value):
        if self.size == self.capacity:
            self._resize()
        self.data[self.size] = value
        self.size += 1
    
    def insert(self, index, value):
        if index < 0 or index > self.size:
            raise IndexError("Index out of bounds")
        
        if self.size == self.capacity:
            self._resize()
        
        for i in range(self.size, index, -1):
            self.data[i] = self.data[i - 1]
        
        self.data[index] = value
        self.size += 1
    
    def remove(self, index):
        if index < 0 or index >= self.size:
            raise IndexError("Index out of bounds")
        
        removed_value = self.data[index]
        for i in range(index, self.size - 1):
            self.data[i] = self.data[i + 1]
        
        self.size -= 1
        return removed_value
    
    def _resize(self):
        self.capacity *= 2
        new_data = [None] * self.capacity
        for i in range(self.size):
            new_data[i] = self.data[i]
        self.data = new_data
    
    def __len__(self):
        return self.size
    
    def __str__(self):
        return str([self.data[i] for i in range(self.size)])
```

### Rust Implementation

```rust
pub struct DynamicArray<T> {
    capacity: usize,
    size: usize,
    data: Vec<Option<T>>,
}

impl<T: Clone> DynamicArray<T> {
    pub fn new() -> Self {
        Self {
            capacity: 4,
            size: 0,
            data: vec![None; 4],
        }
    }
    
    pub fn get(&self, index: usize) -> Result<&T, &'static str> {
        if index < self.size {
            self.data[index].as_ref().ok_or("Value not found")
        } else {
            Err("Index out of bounds")
        }
    }
    
    pub fn set(&mut self, index: usize, value: T) -> Result<(), &'static str> {
        if index < self.size {
            self.data[index] = Some(value);
            Ok(())
        } else {
            Err("Index out of bounds")
        }
    }
    
    pub fn push(&mut self, value: T) {
        if self.size == self.capacity {
            self.resize();
        }
        self.data[self.size] = Some(value);
        self.size += 1;
    }
    
    pub fn insert(&mut self, index: usize, value: T) -> Result<(), &'static str> {
        if index > self.size {
            return Err("Index out of bounds");
        }
        
        if self.size == self.capacity {
            self.resize();
        }
        
        for i in (index..self.size).rev() {
            self.data[i + 1] = self.data[i].take();
        }
        
        self.data[index] = Some(value);
        self.size += 1;
        Ok(())
    }
    
    pub fn remove(&mut self, index: usize) -> Result<T, &'static str> {
        if index >= self.size {
            return Err("Index out of bounds");
        }
        
        let removed_value = self.data[index].take().unwrap();
        
        for i in index..self.size - 1 {
            self.data[i] = self.data[i + 1].take();
        }
        
        self.size -= 1;
        Ok(removed_value)
    }
    
    fn resize(&mut self) {
        self.capacity *= 2;
        self.data.resize(self.capacity, None);
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
}
```

---

## Linked Lists

### Python Implementation

```python
class ListNode:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
        self.size = 0
    
    def append(self, data):
        new_node = ListNode(data)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self.size += 1
    
    def prepend(self, data):
        new_node = ListNode(data)
        new_node.next = self.head
        self.head = new_node
        self.size += 1
    
    def insert(self, index, data):
        if index < 0 or index > self.size:
            raise IndexError("Index out of bounds")
        
        if index == 0:
            self.prepend(data)
            return
        
        new_node = ListNode(data)
        current = self.head
        for _ in range(index - 1):
            current = current.next
        
        new_node.next = current.next
        current.next = new_node
        self.size += 1
    
    def delete(self, index):
        if index < 0 or index >= self.size:
            raise IndexError("Index out of bounds")
        
        if index == 0:
            removed_data = self.head.data
            self.head = self.head.next
            self.size -= 1
            return removed_data
        
        current = self.head
        for _ in range(index - 1):
            current = current.next
        
        removed_data = current.next.data
        current.next = current.next.next
        self.size -= 1
        return removed_data
    
    def find(self, data):
        current = self.head
        index = 0
        while current:
            if current.data == data:
                return index
            current = current.next
            index += 1
        return -1
    
    def __len__(self):
        return self.size
    
    def __str__(self):
        result = []
        current = self.head
        while current:
            result.append(str(current.data))
            current = current.next
        return " -> ".join(result)
```

### Rust Implementation

```rust
use std::rc::Rc;
use std::cell::RefCell;

type NodeRef<T> = Rc<RefCell<ListNode<T>>>;

#[derive(Debug)]
pub struct ListNode<T> {
    data: T,
    next: Option<NodeRef<T>>,
}

impl<T> ListNode<T> {
    fn new(data: T) -> NodeRef<T> {
        Rc::new(RefCell::new(ListNode {
            data,
            next: None,
        }))
    }
}

pub struct LinkedList<T> {
    head: Option<NodeRef<T>>,
    size: usize,
}

impl<T: Clone + PartialEq> LinkedList<T> {
    pub fn new() -> Self {
        Self {
            head: None,
            size: 0,
        }
    }
    
    pub fn push(&mut self, data: T) {
        let new_node = ListNode::new(data);
        
        if let Some(head) = &self.head {
            let mut current = Rc::clone(head);
            loop {
                let next = {
                    let node = current.borrow();
                    node.next.clone()
                };
                
                if let Some(next_node) = next {
                    current = next_node;
                } else {
                    break;
                }
            }
            current.borrow_mut().next = Some(new_node);
        } else {
            self.head = Some(new_node);
        }
        
        self.size += 1;
    }
    
    pub fn push_front(&mut self, data: T) {
        let new_node = ListNode::new(data);
        new_node.borrow_mut().next = self.head.take();
        self.head = Some(new_node);
        self.size += 1;
    }
    
    pub fn pop_front(&mut self) -> Option<T> {
        self.head.take().map(|head| {
            let node = Rc::try_unwrap(head).unwrap().into_inner();
            self.head = node.next;
            self.size -= 1;
            node.data
        })
    }
    
    pub fn find(&self, data: &T) -> Option<usize> {
        let mut current = self.head.clone();
        let mut index = 0;
        
        while let Some(node) = current {
            if node.borrow().data == *data {
                return Some(index);
            }
            current = node.borrow().next.clone();
            index += 1;
        }
        None
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
}
```

---

## Stacks

### Python Implementation

```python
class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items.pop()
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items[-1]
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)
    
    def __str__(self):
        return f"Stack({self.items})"

# Array-based stack implementation
class ArrayStack:
    def __init__(self, capacity=100):
        self.capacity = capacity
        self.items = [None] * capacity
        self.top = -1
    
    def push(self, item):
        if self.top >= self.capacity - 1:
            raise OverflowError("Stack overflow")
        self.top += 1
        self.items[self.top] = item
    
    def pop(self):
        if self.top < 0:
            raise IndexError("Stack underflow")
        item = self.items[self.top]
        self.top -= 1
        return item
    
    def peek(self):
        if self.top < 0:
            raise IndexError("Stack is empty")
        return self.items[self.top]
    
    def is_empty(self):
        return self.top < 0
    
    def size(self):
        return self.top + 1
```

### Rust Implementation

```rust
pub struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    pub fn new() -> Self {
        Self {
            items: Vec::new(),
        }
    }
    
    pub fn push(&mut self, item: T) {
        self.items.push(item);
    }
    
    pub fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }
    
    pub fn peek(&self) -> Option<&T> {
        self.items.last()
    }
    
    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    pub fn len(&self) -> usize {
        self.items.len()
    }
}

// Array-based stack implementation
pub struct ArrayStack<T> {
    items: Vec<Option<T>>,
    top: isize,
    capacity: usize,
}

impl<T> ArrayStack<T> {
    pub fn new(capacity: usize) -> Self {
        Self {
            items: vec![None; capacity],
            top: -1,
            capacity,
        }
    }
    
    pub fn push(&mut self, item: T) -> Result<(), &'static str> {
        if (self.top + 1) as usize >= self.capacity {
            return Err("Stack overflow");
        }
        
        self.top += 1;
        self.items[self.top as usize] = Some(item);
        Ok(())
    }
    
    pub fn pop(&mut self) -> Result<T, &'static str> {
        if self.top < 0 {
            return Err("Stack underflow");
        }
        
        let item = self.items[self.top as usize].take().unwrap();
        self.top -= 1;
        Ok(item)
    }
    
    pub fn peek(&self) -> Result<&T, &'static str> {
        if self.top < 0 {
            return Err("Stack is empty");
        }
        
        self.items[self.top as usize].as_ref().ok_or("Value not found")
    }
    
    pub fn is_empty(&self) -> bool {
        self.top < 0
    }
    
    pub fn len(&self) -> usize {
        if self.top < 0 { 0 } else { (self.top + 1) as usize }
    }
}
```

---

## Queues

### Python Implementation

```python
from collections import deque

class Queue:
    def __init__(self):
        self.items = deque()
    
    def enqueue(self, item):
        self.items.append(item)
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items.popleft()
    
    def front(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items[0]
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)

# Circular Queue implementation
class CircularQueue:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = [None] * capacity
        self.front_idx = 0
        self.rear_idx = -1
        self.current_size = 0
    
    def enqueue(self, item):
        if self.current_size >= self.capacity:
            raise OverflowError("Queue is full")
        
        self.rear_idx = (self.rear_idx + 1) % self.capacity
        self.items[self.rear_idx] = item
        self.current_size += 1
    
    def dequeue(self):
        if self.current_size <= 0:
            raise IndexError("Queue is empty")
        
        item = self.items[self.front_idx]
        self.items[self.front_idx] = None
        self.front_idx = (self.front_idx + 1) % self.capacity
        self.current_size -= 1
        return item
    
    def front(self):
        if self.current_size <= 0:
            raise IndexError("Queue is empty")
        return self.items[self.front_idx]
    
    def is_empty(self):
        return self.current_size == 0
    
    def is_full(self):
        return self.current_size == self.capacity
    
    def size(self):
        return self.current_size
```

### Rust Implementation

```rust
use std::collections::VecDeque;

pub struct Queue<T> {
    items: VecDeque<T>,
}

impl<T> Queue<T> {
    pub fn new() -> Self {
        Self {
            items: VecDeque::new(),
        }
    }
    
    pub fn enqueue(&mut self, item: T) {
        self.items.push_back(item);
    }
    
    pub fn dequeue(&mut self) -> Option<T> {
        self.items.pop_front()
    }
    
    pub fn front(&self) -> Option<&T> {
        self.items.front()
    }
    
    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    pub fn len(&self) -> usize {
        self.items.len()
    }
}

// Circular Queue implementation
pub struct CircularQueue<T> {
    items: Vec<Option<T>>,
    front_idx: usize,
    rear_idx: usize,
    current_size: usize,
    capacity: usize,
}

impl<T> CircularQueue<T> {
    pub fn new(capacity: usize) -> Self {
        Self {
            items: vec![None; capacity],
            front_idx: 0,
            rear_idx: 0,
            current_size: 0,
            capacity,
        }
    }
    
    pub fn enqueue(&mut self, item: T) -> Result<(), &'static str> {
        if self.current_size >= self.capacity {
            return Err("Queue is full");
        }
        
        self.items[self.rear_idx] = Some(item);
        self.rear_idx = (self.rear_idx + 1) % self.capacity;
        self.current_size += 1;
        Ok(())
    }
    
    pub fn dequeue(&mut self) -> Result<T, &'static str> {
        if self.current_size == 0 {
            return Err("Queue is empty");
        }
        
        let item = self.items[self.front_idx].take().unwrap();
        self.front_idx = (self.front_idx + 1) % self.capacity;
        self.current_size -= 1;
        Ok(item)
    }
    
    pub fn front(&self) -> Result<&T, &'static str> {
        if self.current_size == 0 {
            return Err("Queue is empty");
        }
        
        self.items[self.front_idx].as_ref().ok_or("Value not found")
    }
    
    pub fn is_empty(&self) -> bool {
        self.current_size == 0
    }
    
    pub fn is_full(&self) -> bool {
        self.current_size == self.capacity
    }
    
    pub fn len(&self) -> usize {
        self.current_size
    }
}
```

---

## Hash Tables/Maps

### Python Implementation

```python
class HashTable:
    def __init__(self, initial_capacity=16):
        self.capacity = initial_capacity
        self.size = 0
        self.buckets = [[] for _ in range(self.capacity)]
        self.load_factor_threshold = 0.75
    
    def _hash(self, key):
        return hash(key) % self.capacity
    
    def put(self, key, value):
        if self.size >= self.capacity * self.load_factor_threshold:
            self._resize()
        
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        # Check if key already exists
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        
        # Add new key-value pair
        bucket.append((key, value))
        self.size += 1
    
    def get(self, key):
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        for k, v in bucket:
            if k == key:
                return v
        
        raise KeyError(f"Key '{key}' not found")
    
    def delete(self, key):
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        for i, (k, v) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self.size -= 1
                return v
        
        raise KeyError(f"Key '{key}' not found")
    
    def _resize(self):
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [[] for _ in range(self.capacity)]
        old_size = self.size
        self.size = 0
        
        # Rehash all elements
        for bucket in old_buckets:
            for key, value in bucket:
                self.put(key, value)
    
    def contains(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False
    
    def keys(self):
        result = []
        for bucket in self.buckets:
            for key, value in bucket:
                result.append(key)
        return result
    
    def values(self):
        result = []
        for bucket in self.buckets:
            for key, value in bucket:
                result.append(value)
        return result
    
    def __len__(self):
        return self.size
```

### Rust Implementation

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

pub struct HashTable<K, V> {
    buckets: Vec<Vec<(K, V)>>,
    capacity: usize,
    size: usize,
    load_factor_threshold: f64,
}

impl<K: Hash + PartialEq + Clone, V: Clone> HashTable<K, V> {
    pub fn new() -> Self {
        let capacity = 16;
        Self {
            buckets: vec![Vec::new(); capacity],
            capacity,
            size: 0,
            load_factor_threshold: 0.75,
        }
    }
    
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        hasher.finish() as usize % self.capacity
    }
    
    pub fn put(&mut self, key: K, value: V) {
        if self.size as f64 >= self.capacity as f64 * self.load_factor_threshold {
            self.resize();
        }
        
        let bucket_index = self.hash(&key);
        let bucket = &mut self.buckets[bucket_index];
        
        // Check if key already exists
        for (k, v) in bucket.iter_mut() {
            if *k == key {
                *v = value;
                return;
            }
        }
        
        // Add new key-value pair
        bucket.push((key, value));
        self.size += 1;
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let bucket_index = self.hash(key);
        let bucket = &self.buckets[bucket_index];
        
        for (k, v) in bucket.iter() {
            if *k == *key {
                return Some(v);
            }
        }
        
        None
    }
    
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let bucket_index = self.hash(key);
        let bucket = &mut self.buckets[bucket_index];
        
        for (i, (k, _)) in bucket.iter().enumerate() {
            if *k == *key {
                let (_, value) = bucket.remove(i);
                self.size -= 1;
                return Some(value);
            }
        }
        
        None
    }
    
    fn resize(&mut self) {
        let old_buckets = std::mem::replace(&mut self.buckets, Vec::new());
        self.capacity *= 2;
        self.buckets = vec![Vec::new(); self.capacity];
        let old_size = self.size;
        self.size = 0;
        
        // Rehash all elements
        for bucket in old_buckets {
            for (key, value) in bucket {
                self.put(key, value);
            }
        }
    }
    
    pub fn contains_key(&self, key: &K) -> bool {
        self.get(key).is_some()
    }
    
    pub fn keys(&self) -> Vec<&K> {
        let mut result = Vec::new();
        for bucket in &self.buckets {
            for (key, _) in bucket {
                result.push(key);
            }
        }
        result
    }
    
    pub fn values(&self) -> Vec<&V> {
        let mut result = Vec::new();
        for bucket in &self.buckets {
            for (_, value) in bucket {
                result.push(value);
            }
        }
        result
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
}
```

---

## Binary Trees

### Python Implementation

```python
class TreeNode:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None

class BinaryTree:
    def __init__(self):
        self.root = None
    
    def insert_level_order(self, data):
        new_node = TreeNode(data)
        
        if not self.root:
            self.root = new_node
            return
        
        queue = [self.root]
        
        while queue:
            node = queue.pop(0)
            
            if not node.left:
                node.left = new_node
                break
            elif not node.right:
                node.right = new_node
                break
            else:
                queue.append(node.left)
                queue.append(node.right)
    
    def inorder_traversal(self, node=None, result=None):
        if result is None:
            result = []
        if node is None:
            node = self.root
        
        if node:
            self.inorder_traversal(node.left, result)
            result.append(node.data)
            self.inorder_traversal(node.right, result)
        
        return result
    
    def preorder_traversal(self, node=None, result=None):
        if result is None:
            result = []
        if node is None:
            node = self.root
        
        if node:
            result.append(node.data)
            self.preorder_traversal(node.left, result)
            self.preorder_traversal(node.right, result)
        
        return result
    
    def postorder_traversal(self, node=None, result=None):
        if result is None:
            result = []
        if node is None:
            node = self.root
        
        if node:
            self.postorder_traversal(node.left, result)
            self.postorder_traversal(node.right, result)
            result.append(node.data)
        
        return result
    
    def level_order_traversal(self):
        if not self.root:
            return []
        
        result = []
        queue = [self.root]
        
        while queue:
            node = queue.pop(0)
            result.append(node.data)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        return result
    
    def height(self, node=None):
        if node is None:
            node = self.root
        
        if not node:
            return -1
        
        left_height = self.height(node.left)
        right_height = self.height(node.right)
        
        return max(left_height, right_height) + 1
    
    def count_nodes(self, node=None):
        if node is None:
            node = self.root
        
        if not node:
            return 0
        
        return 1 + self.count_nodes(node.left) + self.count_nodes(node.right)
```

### Rust Implementation

```rust
use std::rc::Rc;
use std::cell::RefCell;
use std::collections::VecDeque;

type TreeNodeRef<T> = Rc<RefCell<TreeNode<T>>>;

#[derive(Debug)]
pub struct TreeNode<T> {
    data: T,
    left: Option<TreeNodeRef<T>>,
    right: Option<TreeNodeRef<T>>,
}

impl<T> TreeNode<T> {
    fn new(data: T) -> TreeNodeRef<T> {
        Rc::new(RefCell::new(TreeNode {
            data,
            left: None,
            right: None,
        }))
    }
}

pub struct BinaryTree<T> {
    root: Option<TreeNodeRef<T>>,
}

impl<T: Clone> BinaryTree<T> {
    pub fn new() -> Self {
        Self { root: None }
    }
    
    pub fn insert_level_order(&mut self, data: T) {
        let new_node = TreeNode::new(data);
        
        if self.root.is_none() {
            self.root = Some(new_node);
            return;
        }
        
        let mut queue = VecDeque::new();
        queue.push_back(self.root.as_ref().unwrap().clone());
        
        while let Some(node) = queue.pop_front() {
            let mut node_ref = node.borrow_mut();
            
            if node_ref.left.is_none() {
                node_ref.left = Some(new_node);
                break;
            } else if node_ref.right.is_none() {
                node_ref.right = Some(new_node);
                break;
            } else {
                queue.push_back(node_ref.left.as_ref().unwrap().clone());
                queue.push_back(node_ref.right.as_ref().unwrap().clone());
            }
        }
    }
    
    pub fn inorder_traversal(&self) -> Vec<T> {
        let mut result = Vec::new();
        self.inorder_helper(self.root.as_ref(), &mut result);
        result
    }
    
    fn inorder_helper(&self, node: Option<&TreeNodeRef<T>>, result: &mut Vec<T>) {
        if let Some(n) = node {
            let node_ref = n.borrow();
            self.inorder_helper(node_ref.left.as_ref(), result);
            result.push(node_ref.data.clone());
            self.inorder_helper(node_ref.right.as_ref(), result);
        }
    }
    
    pub fn preorder_traversal(&self) -> Vec<T> {
        let mut result = Vec::new();
        self.preorder_helper(self.root.as_ref(), &mut result);
        result
    }
    
    fn preorder_helper(&self, node: Option<&TreeNodeRef<T>>, result: &mut Vec<T>) {
        if let Some(n) = node {
            let node_ref = n.borrow();
            result.push(node_ref.data.clone());
            self.preorder_helper(node_ref.left.as_ref(), result);
            self.preorder_helper(node_ref.right.as_ref(), result);
        }
    }
    
    pub fn postorder_traversal(&self) -> Vec<T> {
        let mut result = Vec::new();
        self.postorder_helper(self.root.as_ref(), &mut result);
        result
    }
    
    fn postorder_helper(&self, node: Option<&TreeNodeRef<T>>, result: &mut Vec<T>) {
        if let Some(n) = node {
            let node_ref = n.borrow();
            self.postorder_helper(node_ref.left.as_ref(), result);
            self.postorder_helper(node_ref.right.as_ref(), result);
            result.push(node_ref.data.clone());
        }
    }
    
    pub fn level_order_traversal(&self) -> Vec<T> {
        if self.root.is_none() {
            return Vec::new();
        }
        
        let mut result = Vec::new();
        let mut queue = VecDeque::new();
        queue.push_back(self.root.as_ref().unwrap().clone());
        
        while let Some(node) = queue.pop_front() {
            let node_ref = node.borrow();
            result.push(node_ref.data.clone());
            
            if let Some(left) = &node_ref.left {
                queue.push_back(left.clone());
            }
            if let Some(right) = &node_ref.right {
                queue.push_back(right.clone());
            }
        }
        
        result
    }
    
    pub fn height(&self) -> i32 {
        self.height_helper(self.root.as_ref())
    }
    
    fn height_helper(&self, node: Option<&TreeNodeRef<T>>) -> i32 {
        if let Some(n) = node {
            let node_ref = n.borrow();
            let left_height = self.height_helper(node_ref.left.as_ref());
            let right_height = self.height_helper(node_ref.right.as_ref());
            std::cmp::max(left_height, right_height) + 1
        } else {
            -1
        }
    }
    
    pub fn count_nodes(&self) -> usize {
        self.count_helper(self.root.as_ref())
    }
    
    fn count_helper(&self, node: Option<&TreeNodeRef<T>>) -> usize {
        if let Some(n) = node {
            let node_ref = n.borrow();
            1 + self.count_helper(node_ref.left.as_ref()) + 
                self.count_helper(node_ref.right.as_ref())
        } else {
            0
        }
    }
}

---

## Binary Search Trees

### Python Implementation

```python
class BSTNode:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None

class BinarySearchTree:
    def __init__(self):
        self.root = None
    
    def insert(self, data):
        self.root = self._insert_recursive(self.root, data)
    
    def _insert_recursive(self, node, data):
        if not node:
            return BSTNode(data)
        
        if data < node.data:
            node.left = self._insert_recursive(node.left, data)
        elif data > node.data:
            node.right = self._insert_recursive(node.right, data)
        
        return node
    
    def search(self, data):
        return self._search_recursive(self.root, data)
    
    def _search_recursive(self, node, data):
        if not node or node.data == data:
            return node
        
        if data < node.data:
            return self._search_recursive(node.left, data)
        else:
            return self._search_recursive(node.right, data)
    
    def delete(self, data):
        self.root = self._delete_recursive(self.root, data)
    
    def _delete_recursive(self, node, data):
        if not node:
            return node
        
        if data < node.data:
            node.left = self._delete_recursive(node.left, data)
        elif data > node.data:
            node.right = self._delete_recursive(node.right, data)
        else:
            # Node to be deleted found
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            
            # Node has two children
            # Find inorder successor (smallest in right subtree)
            temp = self._find_min(node.right)
            node.data = temp.data
            node.right = self._delete_recursive(node.right, temp.data)
        
        return node
    
    def _find_min(self, node):
        while node.left:
            node = node.left
        return node
    
    def _find_max(self, node):
        while node.right:
            node = node.right
        return node
    
    def inorder(self):
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.data)
            self._inorder_recursive(node.right, result)
    
    def find_min(self):
        if not self.root:
            return None
        return self._find_min(self.root).data
    
    def find_max(self):
        if not self.root:
            return None
        return self._find_max(self.root).data
```

### Rust Implementation

```rust
use std::rc::Rc;
use std::cell::RefCell;

type BSTNodeRef<T> = Rc<RefCell<BSTNode<T>>>;

#[derive(Debug)]
pub struct BSTNode<T> {
    data: T,
    left: Option<BSTNodeRef<T>>,
    right: Option<BSTNodeRef<T>>,
}

impl<T> BSTNode<T> {
    fn new(data: T) -> BSTNodeRef<T> {
        Rc::new(RefCell::new(BSTNode {
            data,
            left: None,
            right: None,
        }))
    }
}

pub struct BinarySearchTree<T> {
    root: Option<BSTNodeRef<T>>,
}

impl<T: Clone + PartialOrd> BinarySearchTree<T> {
    pub fn new() -> Self {
        Self { root: None }
    }
    
    pub fn insert(&mut self, data: T) {
        if self.root.is_none() {
            self.root = Some(BSTNode::new(data));
        } else {
            self.insert_recursive(self.root.as_ref().unwrap(), data);
        }
    }
    
    fn insert_recursive(&self, node: &BSTNodeRef<T>, data: T) {
        let mut node_ref = node.borrow_mut();
        
        if data < node_ref.data {
            if node_ref.left.is_none() {
                node_ref.left = Some(BSTNode::new(data));
            } else {
                drop(node_ref);
                self.insert_recursive(node.borrow().left.as_ref().unwrap(), data);
            }
        } else if data > node_ref.data {
            if node_ref.right.is_none() {
                node_ref.right = Some(BSTNode::new(data));
            } else {
                drop(node_ref);
                self.insert_recursive(node.borrow().right.as_ref().unwrap(), data);
            }
        }
    }
    
    pub fn search(&self, data: &T) -> bool {
        self.search_recursive(self.root.as_ref(), data)
    }
    
    fn search_recursive(&self, node: Option<&BSTNodeRef<T>>, data: &T) -> bool {
        if let Some(n) = node {
            let node_ref = n.borrow();
            if *data == node_ref.data {
                true
            } else if *data < node_ref.data {
                self.search_recursive(node_ref.left.as_ref(), data)
            } else {
                self.search_recursive(node_ref.right.as_ref(), data)
            }
        } else {
            false
        }
    }
    
    pub fn inorder(&self) -> Vec<T> {
        let mut result = Vec::new();
        self.inorder_recursive(self.root.as_ref(), &mut result);
        result
    }
    
    fn inorder_recursive(&self, node: Option<&BSTNodeRef<T>>, result: &mut Vec<T>) {
        if let Some(n) = node {
            let node_ref = n.borrow();
            self.inorder_recursive(node_ref.left.as_ref(), result);
            result.push(node_ref.data.clone());
            self.inorder_recursive(node_ref.right.as_ref(), result);
        }
    }
    
    pub fn find_min(&self) -> Option<T> {
        self.root.as_ref().map(|root| {
            let mut current = root.clone();
            loop {
                let left = {
                    let node = current.borrow();
                    node.left.clone()
                };
                if let Some(left_node) = left {
                    current = left_node;
                } else {
                    break;
                }
            }
            current.borrow().data.clone()
        })
    }
    
    pub fn find_max(&self) -> Option<T> {
        self.root.as_ref().map(|root| {
            let mut current = root.clone();
            loop {
                let right = {
                    let node = current.borrow();
                    node.right.clone()
                };
                if let Some(right_node) = right {
                    current = right_node;
                } else {
                    break;
                }
            }
            current.borrow().data.clone()
        })
    }
}

---

## Heaps

### Python Implementation

```python
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
    
    def insert(self, data):
        self.heap.append(data)
        self._heapify_up(len(self.heap) - 1)
    
    def _heapify_up(self, i):
        if i > 0 and self.heap[i] < self.heap[self.parent(i)]:
            self.swap(i, self.parent(i))
            self._heapify_up(self.parent(i))
    
    def extract_min(self):
        if not self.heap:
            raise IndexError("Heap is empty")
        
        if len(self.heap) == 1:
            return self.heap.pop()
        
        min_val = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return min_val
    
    def _heapify_down(self, i):
        min_index = i
        left = self.left_child(i)
        right = self.right_child(i)
        
        if left < len(self.heap) and self.heap[left] < self.heap[min_index]:
            min_index = left
        
        if right < len(self.heap) and self.heap[right] < self.heap[min_index]:
            min_index = right
        
        if min_index != i:
            self.swap(i, min_index)
            self._heapify_down(min_index)
    
    def peek(self):
        if not self.heap:
            raise IndexError("Heap is empty")
        return self.heap[0]
    
    def size(self):
        return len(self.heap)
    
    def is_empty(self):
        return len(self.heap) == 0

class MaxHeap:
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
    
    def insert(self, data):
        self.heap.append(data)
        self._heapify_up(len(self.heap) - 1)
    
    def _heapify_up(self, i):
        if i > 0 and self.heap[i] > self.heap[self.parent(i)]:
            self.swap(i, self.parent(i))
            self._heapify_up(self.parent(i))
    
    def extract_max(self):
        if not self.heap:
            raise IndexError("Heap is empty")
        
        if len(self.heap) == 1:
            return self.heap.pop()
        
        max_val = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return max_val
    
    def _heapify_down(self, i):
        max_index = i
        left = self.left_child(i)
        right = self.right_child(i)
        
        if left < len(self.heap) and self.heap[left] > self.heap[max_index]:
            max_index = left
        
        if right < len(self.heap) and self.heap[right] > self.heap[max_index]:
            max_index = right
        
        if max_index != i:
            self.swap(i, max_index)
            self._heapify_down(max_index)
    
    def peek(self):
        if not self.heap:
            raise IndexError("Heap is empty")
        return self.heap[0]
    
    def size(self):
        return len(self.heap)
    
    def is_empty(self):
        return len(self.heap) == 0
```

### Rust Implementation

```rust
use std::cmp::Ordering;

pub struct MinHeap<T> {
    heap: Vec<T>,
}

impl<T: PartialOrd + Clone> MinHeap<T> {
    pub fn new() -> Self {
        Self {
            heap: Vec::new(),
        }
    }
    
    fn parent(&self, i: usize) -> usize {
        (i - 1) / 2
    }
    
    fn left_child(&self, i: usize) -> usize {
        2 * i + 1
    }
    
    fn right_child(&self, i: usize) -> usize {
        2 * i + 2
    }
    
    pub fn insert(&mut self, data: T) {
        self.heap.push(data);
        self.heapify_up(self.heap.len() - 1);
    }
    
    fn heapify_up(&mut self, mut i: usize) {
        while i > 0 && self.heap[i] < self.heap[self.parent(i)] {
            let parent_idx = self.parent(i);
            self.heap.swap(i, parent_idx);
            i = parent_idx;
        }
    }
    
    pub fn extract_min(&mut self) -> Option<T> {
        if self.heap.is_empty() {
            return None;
        }
        
        if self.heap.len() == 1 {
            return self.heap.pop();
        }
        
        let min_val = self.heap[0].clone();
        let last = self.heap.pop().unwrap();
        self.heap[0] = last;
        self.heapify_down(0);
        Some(min_val)
    }
    
    fn heapify_down(&mut self, mut i: usize) {
        loop {
            let mut min_index = i;
            let left = self.left_child(i);
            let right = self.right_child(i);
            
            if left < self.heap.len() && self.heap[left] < self.heap[min_index] {
                min_index = left;
            }
            
            if right < self.heap.len() && self.heap[right] < self.heap[min_index] {
                min_index = right;
            }
            
            if min_index != i {
                self.heap.swap(i, min_index);
                i = min_index;
            } else {
                break;
            }
        }
    }
    
    pub fn peek(&self) -> Option<&T> {
        self.heap.first()
    }
    
    pub fn len(&self) -> usize {
        self.heap.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }
}

pub struct MaxHeap<T> {
    heap: Vec<T>,
}

impl<T: PartialOrd + Clone> MaxHeap<T> {
    pub fn new() -> Self {
        Self {
            heap: Vec::new(),
        }
    }
    
    fn parent(&self, i: usize) -> usize {
        (i - 1) / 2
    }
    
    fn left_child(&self, i: usize) -> usize {
        2 * i + 1
    }
    
    fn right_child(&self, i: usize) -> usize {
        2 * i + 2
    }
    
    pub fn insert(&mut self, data: T) {
        self.heap.push(data);
        self.heapify_up(self.heap.len() - 1);
    }
    
    fn heapify_up(&mut self, mut i: usize) {
        while i > 0 && self.heap[i] > self.heap[self.parent(i)] {
            let parent_idx = self.parent(i);
            self.heap.swap(i, parent_idx);
            i = parent_idx;
        }
    }
    
    pub fn extract_max(&mut self) -> Option<T> {
        if self.heap.is_empty() {
            return None;
        }
        
        if self.heap.len() == 1 {
            return self.heap.pop();
        }
        
        let max_val = self.heap[0].clone();
        let last = self.heap.pop().unwrap();
        self.heap[0] = last;
        self.heapify_down(0);
        Some(max_val)
    }
    
    fn heapify_down(&mut self, mut i: usize) {
        loop {
            let mut max_index = i;
            let left = self.left_child(i);
            let right = self.right_child(i);
            
            if left < self.heap.len() && self.heap[left] > self.heap[max_index] {
                max_index = left;
            }
            
            if right < self.heap.len() && self.heap[right] > self.heap[max_index] {
                max_index = right;
            }
            
            if max_index != i {
                self.heap.swap(i, max_index);
                i = max_index;
            } else {
                break;
            }
        }
    }
    
    pub fn peek(&self) -> Option<&T> {
        self.heap.first()
    }
    
    pub fn len(&self) -> usize {
        self.heap.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }
}

---

## Graphs

### Python Implementation

```python
from collections import deque, defaultdict

class Graph:
    def __init__(self, directed=False):
        self.directed = directed
        self.adj_list = defaultdict(list)
        self.vertices = set()
    
    def add_vertex(self, vertex):
        self.vertices.add(vertex)
        if vertex not in self.adj_list:
            self.adj_list[vertex] = []
    
    def add_edge(self, u, v, weight=1):
        self.add_vertex(u)
        self.add_vertex(v)
        
        self.adj_list[u].append((v, weight))
        if not self.directed:
            self.adj_list[v].append((u, weight))
    
    def remove_edge(self, u, v):
        if u in self.adj_list:
            self.adj_list[u] = [(vertex, weight) for vertex, weight in self.adj_list[u] if vertex != v]
        
        if not self.directed and v in self.adj_list:
            self.adj_list[v] = [(vertex, weight) for vertex, weight in self.adj_list[v] if vertex != u]
    
    def get_neighbors(self, vertex):
        return self.adj_list.get(vertex, [])
    
    def bfs(self, start):
        if start not in self.vertices:
            return []
        
        visited = set()
        queue = deque([start])
        result = []
        
        while queue:
            vertex = queue.popleft()
            if vertex not in visited:
                visited.add(vertex)
                result.append(vertex)
                
                for neighbor, _ in self.adj_list[vertex]:
                    if neighbor not in visited:
                        queue.append(neighbor)
        
        return result
    
    def dfs(self, start):
        if start not in self.vertices:
            return []
        
        visited = set()
        result = []
        
        def dfs_helper(vertex):
            visited.add(vertex)
            result.append(vertex)
            
            for neighbor, _ in self.adj_list[vertex]:
                if neighbor not in visited:
                    dfs_helper(neighbor)
        
        dfs_helper(start)
        return result
    
    def dijkstra(self, start):
        if start not in self.vertices:
            return {}
        
        distances = {vertex: float('inf') for vertex in self.vertices}
        distances[start] = 0
        visited = set()
        
        import heapq
        pq = [(0, start)]
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            for neighbor, weight in self.adj_list[current]:
                if neighbor not in visited:
                    new_dist = current_dist + weight
                    if new_dist < distances[neighbor]:
                        distances[neighbor] = new_dist
                        heapq.heappush(pq, (new_dist, neighbor))
        
        return distances
    
    def has_cycle(self):
        if not self.directed:
            return self._has_cycle_undirected()
        else:
            return self._has_cycle_directed()
    
    def _has_cycle_undirected(self):
        visited = set()
        
        for vertex in self.vertices:
            if vertex not in visited:
                if self._dfs_cycle_undirected(vertex, -1, visited):
                    return True
        return False
    
    def _dfs_cycle_undirected(self, vertex, parent, visited):
        visited.add(vertex)
        
        for neighbor, _ in self.adj_list[vertex]:
            if neighbor not in visited:
                if self._dfs_cycle_undirected(neighbor, vertex, visited):
                    return True
            elif neighbor != parent:
                return True
        
        return False
    
    def _has_cycle_directed(self):
        white = set(self.vertices)  # unvisited
        gray = set()   # visiting
        black = set()  # visited
        
        def dfs(vertex):
            white.discard(vertex)
            gray.add(vertex)
            
            for neighbor, _ in self.adj_list[vertex]:
                if neighbor in gray:
                    return True
                if neighbor in white and dfs(neighbor):
                    return True
            
            gray.discard(vertex)
            black.add(vertex)
            return False
        
        while white:
            if dfs(white.pop()):
                return True
        
        return False
    
    def topological_sort(self):
        if not self.directed:
            raise ValueError("Topological sort only works on directed graphs")
        
        if self.has_cycle():
            raise ValueError("Cannot perform topological sort on graph with cycles")
        
        in_degree = {vertex: 0 for vertex in self.vertices}
        
        for vertex in self.vertices:
            for neighbor, _ in self.adj_list[vertex]:
                in_degree[neighbor] += 1
        
        queue = deque([v for v in self.vertices if in_degree[v] == 0])
        result = []
        
        while queue:
            vertex = queue.popleft()
            result.append(vertex)
            
            for neighbor, _ in self.adj_list[vertex]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
```

### Rust Implementation

```rust
use std::collections::{HashMap, HashSet, VecDeque, BinaryHeap};
use std::cmp::Ordering;
use std::hash::Hash;

#[derive(Debug, Clone)]
pub struct Edge<T> {
    to: T,
    weight: i32,
}

#[derive(Debug, Eq, PartialEq)]
struct State<T> {
    cost: i32,
    vertex: T,
}

impl<T: Ord> Ord for State<T> {
    fn cmp(&self, other: &Self) -> Ordering {
        other.cost.cmp(&self.cost)
            .then_with(|| self.vertex.cmp(&other.vertex))
    }
}

impl<T: Ord> PartialOrd for State<T> {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

pub struct Graph<T> {
    directed: bool,
    adj_list: HashMap<T, Vec<Edge<T>>>,
}

impl<T: Clone + Hash + Eq + Ord> Graph<T> {
    pub fn new(directed: bool) -> Self {
        Self {
            directed,
            adj_list: HashMap::new(),
        }
    }
    
    pub fn add_vertex(&mut self, vertex: T) {
        self.adj_list.entry(vertex).or_insert_with(Vec::new);
    }
    
    pub fn add_edge(&mut self, from: T, to: T, weight: i32) {
        self.add_vertex(from.clone());
        self.add_vertex(to.clone());
        
        self.adj_list.get_mut(&from).unwrap().push(Edge {
            to: to.clone(),
            weight,
        });
        
        if !self.directed {
            self.adj_list.get_mut(&to).unwrap().push(Edge {
                to: from,
                weight,
            });
        }
    }
    
    pub fn get_vertices(&self) -> Vec<&T> {
        self.adj_list.keys().collect()
    }
    
    pub fn get_neighbors(&self, vertex: &T) -> Option<&Vec<Edge<T>>> {
        self.adj_list.get(vertex)
    }
    
    pub fn bfs(&self, start: &T) -> Vec<T> {
        if !self.adj_list.contains_key(start) {
            return Vec::new();
        }
        
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        let mut result = Vec::new();
        
        queue.push_back(start.clone());
        
        while let Some(vertex) = queue.pop_front() {
            if !visited.contains(&vertex) {
                visited.insert(vertex.clone());
                result.push(vertex.clone());
                
                if let Some(neighbors) = self.adj_list.get(&vertex) {
                    for edge in neighbors {
                        if !visited.contains(&edge.to) {
                            queue.push_back(edge.to.clone());
                        }
                    }
                }
            }
        }
        
        result
    }
    
    pub fn dfs(&self, start: &T) -> Vec<T> {
        if !self.adj_list.contains_key(start) {
            return Vec::new();
        }
        
        let mut visited = HashSet::new();
        let mut result = Vec::new();
        
        self.dfs_helper(start, &mut visited, &mut result);
        result
    }
    
    fn dfs_helper(&self, vertex: &T, visited: &mut HashSet<T>, result: &mut Vec<T>) {
        visited.insert(vertex.clone());
        result.push(vertex.clone());
        
        if let Some(neighbors) = self.adj_list.get(vertex) {
            for edge in neighbors {
                if !visited.contains(&edge.to) {
                    self.dfs_helper(&edge.to, visited, result);
                }
            }
        }
    }
    
    pub fn dijkstra(&self, start: &T) -> HashMap<T, i32> {
        let mut distances = HashMap::new();
        let mut visited = HashSet::new();
        let mut heap = BinaryHeap::new();
        
        // Initialize distances
        for vertex in self.adj_list.keys() {
            distances.insert(vertex.clone(), i32::MAX);
        }
        distances.insert(start.clone(), 0);
        
        heap.push(State {
            cost: 0,
            vertex: start.clone(),
        });
        
        while let Some(State { cost, vertex }) = heap.pop() {
            if visited.contains(&vertex) {
                continue;
            }
            
            visited.insert(vertex.clone());
            
            if let Some(neighbors) = self.adj_list.get(&vertex) {
                for edge in neighbors {
                    if !visited.contains(&edge.to) {
                        let new_cost = cost + edge.weight;
                        let current_cost = distances.get(&edge.to).unwrap_or(&i32::MAX);
                        
                        if new_cost < *current_cost {
                            distances.insert(edge.to.clone(), new_cost);
                            heap.push(State {
                                cost: new_cost,
                                vertex: edge.to.clone(),
                            });
                        }
                    }
                }
            }
        }
        
        distances
    }
    
    pub fn has_cycle(&self) -> bool {
        if !self.directed {
            self.has_cycle_undirected()
        } else {
            self.has_cycle_directed()
        }
    }
    
    fn has_cycle_undirected(&self) -> bool {
        let mut visited = HashSet::new();
        
        for vertex in self.adj_list.keys() {
            if !visited.contains(vertex) {
                if self.dfs_cycle_undirected(vertex, None, &mut visited) {
                    return true;
                }
            }
        }
        false
    }
    
    fn dfs_cycle_undirected(&self, vertex: &T, parent: Option<&T>, visited: &mut HashSet<T>) -> bool {
        visited.insert(vertex.clone());
        
        if let Some(neighbors) = self.adj_list.get(vertex) {
            for edge in neighbors {
                if !visited.contains(&edge.to) {
                    if self.dfs_cycle_undirected(&edge.to, Some(vertex), visited) {
                        return true;
                    }
                } else if Some(&edge.to) != parent {
                    return true;
                }
            }
        }
        
        false
    }
    
    fn has_cycle_directed(&self) -> bool {
        let mut white: HashSet<T> = self.adj_list.keys().cloned().collect();
        let mut gray = HashSet::new();
        let mut black = HashSet::new();
        
        while let Some(vertex) = white.iter().next().cloned() {
            white.remove(&vertex);
            if self.dfs_cycle_directed(&vertex, &mut white, &mut gray, &mut black) {
                return true;
            }
        }
        
        false
    }
    
    fn dfs_cycle_directed(&self, vertex: &T, white: &mut HashSet<T>, gray: &mut HashSet<T>, black: &mut HashSet<T>) -> bool {
        white.remove(vertex);
        gray.insert(vertex.clone());
        
        if let Some(neighbors) = self.adj_list.get(vertex) {
            for edge in neighbors {
                if gray.contains(&edge.to) {
                    return true;
                }
                if white.contains(&edge.to) && self.dfs_cycle_directed(&edge.to, white, gray, black) {
                    return true;
                }
            }
        }
        
        gray.remove(vertex);
        black.insert(vertex.clone());
        false
    }
}

---

## Tries

### Python Implementation

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
    
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word
    
    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
    
    def delete(self, word):
        def _delete_helper(node, word, index):
            if index == len(word):
                if not node.is_end_of_word:
                    return False
                node.is_end_of_word = False
                return len(node.children) == 0
            
            char = word[index]
            if char not in node.children:
                return False
            
            should_delete_child = _delete_helper(node.children[char], word, index + 1)
            
            if should_delete_child:
                del node.children[char]
                return not node.is_end_of_word and len(node.children) == 0
            
            return False
        
        _delete_helper(self.root, word, 0)
    
    def get_all_words_with_prefix(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        words = []
        self._collect_words(node, prefix, words)
        return words
    
    def _collect_words(self, node, current_word, words):
        if node.is_end_of_word:
            words.append(current_word)
        
        for char, child_node in node.children.items():
            self._collect_words(child_node, current_word + char, words)
    
    def count_words(self):
        return self._count_words_helper(self.root)
    
    def _count_words_helper(self, node):
        count = 1 if node.is_end_of_word else 0
        for child in node.children.values():
            count += self._count_words_helper(child)
        return count
    
    def longest_common_prefix(self):
        if not self.root.children:
            return ""
        
        prefix = ""
        node = self.root
        
        while len(node.children) == 1 and not node.is_end_of_word:
            char = next(iter(node.children.keys()))
            prefix += char
            node = node.children[char]
        
        return prefix
```

### Rust Implementation

```rust
use std::collections::HashMap;

#[derive(Debug)]
struct TrieNode {
    children: HashMap<char, TrieNode>,
    is_end_of_word: bool,
}

impl TrieNode {
    fn new() -> Self {
        Self {
            children: HashMap::new(),
            is_end_of_word: false,
        }
    }
}

pub struct Trie {
    root: TrieNode,
}

impl Trie {
    pub fn new() -> Self {
        Self {
            root: TrieNode::new(),
        }
    }
    
    pub fn insert(&mut self, word: &str) {
        let mut node = &mut self.root;
        
        for ch in word.chars() {
            node = node.children.entry(ch).or_insert_with(TrieNode::new);
        }
        
        node.is_end_of_word = true;
    }
    
    pub fn search(&self, word: &str) -> bool {
        let mut node = &self.root;
        
        for ch in word.chars() {
            if let Some(child) = node.children.get(&ch) {
                node = child;
            } else {
                return false;
            }
        }
        
        node.is_end_of_word
    }
    
    pub fn starts_with(&self, prefix: &str) -> bool {
        let mut node = &self.root;
        
        for ch in prefix.chars() {
            if let Some(child) = node.children.get(&ch) {
                node = child;
            } else {
                return false;
            }
        }
        
        true
    }
    
    pub fn delete(&mut self, word: &str) -> bool {
        self.delete_helper(&mut self.root, word, 0)
    }
    
    fn delete_helper(&mut self, node: &mut TrieNode, word: &str, index: usize) -> bool {
        let chars: Vec<char> = word.chars().collect();
        
        if index == chars.len() {
            if !node.is_end_of_word {
                return false;
            }
            node.is_end_of_word = false;
            return node.children.is_empty();
        }
        
        let ch = chars[index];
        
        if let Some(child) = node.children.get_mut(&ch) {
            let should_delete_child = self.delete_helper(child, word, index + 1);
            
            if should_delete_child {
                node.children.remove(&ch);
                return !node.is_end_of_word && node.children.is_empty();
            }
        }
        
        false
    }
    
    pub fn get_all_words_with_prefix(&self, prefix: &str) -> Vec<String> {
        let mut node = &self.root;
        
        for ch in prefix.chars() {
            if let Some(child) = node.children.get(&ch) {
                node = child;
            } else {
                return Vec::new();
            }
        }
        
        let mut words = Vec::new();
        self.collect_words(node, prefix, &mut words);
        words
    }
    
    fn collect_words(&self, node: &TrieNode, current_word: &str, words: &mut Vec<String>) {
        if node.is_end_of_word {
            words.push(current_word.to_string());
        }
        
        for (&ch, child) in &node.children {
            let mut new_word = current_word.to_string();
            new_word.push(ch);
            self.collect_words(child, &new_word, words);
        }
    }
    
    pub fn count_words(&self) -> usize {
        self.count_words_helper(&self.root)
    }
    
    fn count_words_helper(&self, node: &TrieNode) -> usize {
        let mut count = if node.is_end_of_word { 1 } else { 0 };
        
        for child in node.children.values() {
            count += self.count_words_helper(child);
        }
        
        count
    }
    
    pub fn longest_common_prefix(&self) -> String {
        let mut prefix = String::new();
        let mut node = &self.root;
        
        while node.children.len() == 1 && !node.is_end_of_word {
            let (&ch, child) = node.children.iter().next().unwrap();
            prefix.push(ch);
            node = child;
        }
        
        prefix
    }
}
```
---

## Performance Comparisons

### Time Complexity Summary

| Data Structure | Insert | Delete | Search | Access |
|----------------|--------|--------|--------|--------|
| **Dynamic Array** | O(1) amortized | O(n) | O(n) | O(1) |
| **Linked List** | O(1) at head | O(n) | O(n) | O(n) |
| **Stack** | O(1) | O(1) | - | O(1) peek |
| **Queue** | O(1) | O(1) | - | O(1) peek |
| **Hash Table** | O(1) average | O(1) average | O(1) average | O(1) average |
| **Binary Tree** | O(log n) balanced | O(log n) balanced | O(log n) balanced | O(log n) balanced |
| **BST** | O(log n) average | O(log n) average | O(log n) average | O(log n) average |
| **Heap** | O(log n) | O(log n) | O(n) | O(1) peek |
| **Graph** | O(1) edge | O(V + E) edge | O(V + E) BFS/DFS | - |
| **Trie** | O(m) | O(m) | O(m) | - |

*Note: m = length of string, V = vertices, E = edges*

### Space Complexity Summary

| Data Structure | Space Complexity |
|----------------|------------------|
| **Dynamic Array** | O(n) |
| **Linked List** | O(n) |
| **Stack** | O(n) |
| **Queue** | O(n) |
| **Hash Table** | O(n) |
| **Binary Tree** | O(n) |
| **BST** | O(n) |
| **Heap** | O(n) |
| **Graph** | O(V + E) |
| **Trie** | O(ALPHABET_SIZE * N * M) |

### Key Differences: Python vs Rust

#### Memory Management
- **Python**: Garbage collected, automatic memory management
- **Rust**: Manual memory management with ownership system, zero-cost abstractions

#### Performance
- **Python**: Interpreted, dynamic typing leads to runtime overhead
- **Rust**: Compiled, static typing with aggressive optimizations

#### Safety
- **Python**: Runtime errors for bounds checking, type errors
- **Rust**: Compile-time guarantees for memory safety and thread safety

#### Syntax Complexity
- **Python**: More concise, easier to read and write
- **Rust**: More verbose but explicit about memory and borrowing

#### Use Cases
- **Python**: Rapid prototyping, data analysis, scripting
- **Rust**: Systems programming, high-performance applications, embedded systems

### When to Use Each Data Structure

1. **Dynamic Arrays/Lists**: When you need indexed access and don't know the size beforehand
2. **Linked Lists**: When frequent insertion/deletion at arbitrary positions is needed
3. **Stacks**: For LIFO operations (function calls, undo operations, parsing)
4. **Queues**: For FIFO operations (breadth-first search, task scheduling)
5. **Hash Tables**: For fast key-value lookups with average O(1) performance
6. **Binary Trees**: For hierarchical data and when you need sorted traversal
7. **BST**: For maintaining sorted data with fast insertion/deletion
8. **Heaps**: For priority queues and finding min/max elements efficiently
9. **Graphs**: For modeling relationships and networks
10. **Tries**: For string operations, autocomplete, and prefix matching

This comprehensive guide provides complete, production-ready implementations of fundamental data structures in both Python and Rust, highlighting the trade-offs and appropriate use cases for each language and data structure.

# Comprehensive Guide to Data Structures: Python vs Rust Implementation ComparisonI've created a comprehensive guide comparing data structures implementations between Python and Rust. This guide covers:

**Key Areas Covered:**
- Linear data structures (arrays, lists, stacks, queues)
- Tree structures (binary trees, heaps, tries)
- Hash-based structures (maps, sets)
- Graph structures and specialized variants
- Advanced structures (B-trees, Bloom filters, skip lists)
- Concurrent and lock-free data structures
- Persistent and immutable collections
- Streaming and external data structures

**For Each Structure, I've Detailed:**
- Implementation characteristics in both languages
- Memory management and performance profiles
- Advanced real-world use cases across industries
- Trade-offs and selection criteria

**Real-World Applications Include:**
- High-frequency trading systems
- Machine learning pipelines
- Distributed databases
- Network security systems
- Game development
- Scientific computing
- Web crawling and search engines
- Cryptocurrency and blockchain
- IoT and real-time analytics

The guide also provides a decision framework to help choose between Python and Rust based on specific project requirements, team expertise, and performance needs. It emphasizes that modern development often benefits from hybrid approaches, using each language where it excels most.

Would you like me to expand on any particular data structure or use case, or would you prefer more details about specific implementation strategies in either language?

# Data Structures: Python vs Rust Implementation Comparison

## Executive Summary

This comprehensive guide examines the implementation characteristics, performance profiles, and real-world applications of fundamental and advanced data structures across Python and Rust ecosystems. Each language brings distinct advantages: Python offers rapid prototyping and extensive libraries, while Rust provides memory safety, zero-cost abstractions, and predictable performance.

## 1. Linear Data Structures

### Arrays and Lists

#### Python Implementation Characteristics
- **Dynamic Arrays (list)**: Automatically resizable with amortized O(1) append operations
- **Memory Management**: Garbage collected, references to objects stored
- **Type Flexibility**: Can store heterogeneous data types
- **Performance**: Interpreted overhead, but optimized C implementations for operations
- **Libraries**: NumPy arrays for numerical computing, providing C-speed operations

#### Rust Implementation Characteristics
- **Static Arrays**: Fixed-size, stack-allocated with compile-time size verification
- **Dynamic Arrays (Vec<T>)**: Heap-allocated, growable with ownership semantics
- **Memory Safety**: Compile-time borrow checker prevents memory leaks and dangling pointers
- **Type System**: Strongly typed with zero-cost abstractions
- **Performance**: Native machine code with predictable memory layout

#### Advanced Real-World Use Cases
- **High-Frequency Trading**: Rust's predictable latency for order book management
- **Scientific Computing**: Python's NumPy ecosystem for research and prototyping
- **Game Development**: Rust for engine core systems, Python for scripting
- **Data Pipeline Processing**: Python for rapid ETL development, Rust for performance-critical components
- **Embedded Systems**: Rust for resource-constrained environments
- **Machine Learning**: Python dominates research phase, Rust emerging in production inference systems

### Linked Lists

#### Python Implementation Characteristics
- **Reference-Based**: Objects connected through references
- **Memory Overhead**: Additional memory for reference storage and object metadata
- **Dynamic Allocation**: Flexible node creation and destruction
- **Garbage Collection**: Automatic memory management handles cycles

#### Rust Implementation Characteristics
- **Ownership Model**: Explicit ownership transfer and borrowing
- **Memory Efficiency**: No garbage collection overhead
- **Safety Guarantees**: Prevents common linked list errors at compile time
- **Pattern Matching**: Elegant traversal through match expressions

#### Advanced Real-World Use Cases
- **Undo/Redo Systems**: Editor applications using doubly-linked command history
- **Music Streaming**: Playlist management with efficient insertion/deletion
- **Process Scheduling**: Operating system task queues
- **Memory Allocators**: Custom heap management in systems programming
- **Blockchain**: Transaction chain validation and block linking
- **Network Packet Processing**: Buffer management in networking stacks

### Stacks and Queues

#### Python Implementation Characteristics
- **Built-in Support**: Lists provide stack operations, collections.deque for queues
- **Thread Safety**: Queue module provides synchronized implementations
- **Flexibility**: Easy to implement custom behaviors and policies

#### Rust Implementation Characteristics
- **Type Safety**: Compile-time guarantees about stack/queue operations
- **Concurrency**: Channels and concurrent data structures in std::sync
- **Memory Control**: Explicit control over allocation strategies

#### Advanced Real-World Use Cases
- **Compiler Design**: Parse stacks and symbol tables
- **Web Crawling**: URL frontier management using priority queues
- **Load Balancing**: Request queues with different prioritization strategies
- **Microservices**: Message queues for service communication
- **Real-time Systems**: Interrupt handling and task scheduling
- **Financial Systems**: Order processing with FIFO/LIFO strategies

## 2. Tree Structures

### Binary Trees and Variants

#### Python Implementation Characteristics
- **Object-Oriented Design**: Natural class-based node representation
- **Library Ecosystem**: Rich set of tree algorithms in libraries like NetworkX
- **Visualization**: Easy integration with plotting libraries for tree visualization
- **Dynamic Typing**: Flexible payload storage in nodes

#### Rust Implementation Characteristics
- **Memory Safety**: Prevention of tree corruption through borrow checker
- **Performance**: Zero-cost abstractions for tree operations
- **Pattern Matching**: Elegant recursive algorithms using match expressions
- **Ownership**: Clear ownership semantics for parent-child relationships

#### Advanced Real-World Use Cases
- **Database Indexing**: B-trees and B+ trees for database storage engines
- **File Systems**: Directory structures and inode management
- **Syntax Analysis**: Abstract syntax trees in compilers and interpreters
- **Decision Systems**: Machine learning decision trees and random forests
- **Game AI**: Behavior trees for NPC decision making
- **Computer Graphics**: Scene graphs for 3D rendering pipelines
- **Version Control**: Git-like systems using tree structures for commits

### Heaps and Priority Queues

#### Python Implementation Characteristics
- **heapq Module**: Built-in binary heap implementation
- **Library Integration**: Priority queues in various scheduling libraries
- **Flexible Comparison**: Custom comparison functions for complex priorities

#### Rust Implementation Characteristics
- **BinaryHeap**: Standard library implementation with ownership semantics
- **Generic Design**: Type-safe priority definitions
- **Performance**: Predictable performance characteristics

#### Advanced Real-World Use Cases
- **Task Scheduling**: Operating system process scheduling
- **Pathfinding**: A* algorithm in navigation systems and game AI
- **Event Simulation**: Discrete event simulation systems
- **Network Routing**: Dijkstra's algorithm in router firmware
- **Load Balancing**: Weighted round-robin scheduling
- **Real-time Analytics**: Top-K queries in streaming data processing
- **Memory Management**: Heap allocation strategies in garbage collectors

### Tries and Prefix Trees

#### Python Implementation Characteristics
- **Dictionary-Based**: Natural implementation using nested dictionaries
- **Library Support**: Specialized trie libraries for text processing
- **Unicode Support**: Native handling of international text

#### Rust Implementation Characteristics
- **Memory Efficiency**: Compact representations with controlled allocation
- **String Handling**: Efficient UTF-8 string processing
- **Performance**: Fast prefix matching for large datasets

#### Advanced Real-World Use Cases
- **Autocomplete Systems**: Search engines and IDE code completion
- **IP Routing**: Network routing tables for packet forwarding
- **Spell Checkers**: Dictionary-based spell correction systems
- **Genomics**: DNA sequence matching and analysis
- **Natural Language Processing**: N-gram models and tokenization
- **Compiler Design**: Symbol tables and keyword recognition
- **Network Security**: Pattern matching in intrusion detection systems

## 3. Hash-Based Structures

### Hash Tables and Maps

#### Python Implementation Characteristics
- **dict Implementation**: Optimized hash table with compact representation
- **Dynamic Resizing**: Automatic load factor management
- **Key Flexibility**: Hashable objects as keys with custom hash functions
- **Memory Model**: Reference-based storage with garbage collection

#### Rust Implementation Characteristics
- **HashMap**: Standard library hash map with ownership semantics
- **Memory Control**: Explicit control over allocation and deallocation
- **Type Safety**: Compile-time key-value type checking
- **Performance**: Predictable hash function behavior

#### Advanced Real-World Use Cases
- **Caching Systems**: Redis-like in-memory data stores
- **Database Storage**: Key-value storage engines
- **Configuration Management**: Application settings and feature flags
- **Session Management**: Web application user session storage
- **Content Addressing**: Distributed storage systems like IPFS
- **Cryptocurrency**: Blockchain transaction indexing
- **Social Networks**: User relationship mapping and graph storage

### Hash Sets

#### Python Implementation Characteristics
- **set Type**: Built-in set operations with mathematical semantics
- **Set Operations**: Union, intersection, difference with optimized algorithms
- **Mutable/Immutable**: Both set and frozenset variants available

#### Rust Implementation Characteristics
- **HashSet**: Standard library implementation with ownership
- **Iterator Chains**: Functional programming style for set operations
- **Memory Safety**: Prevention of iterator invalidation

#### Advanced Real-World Use Cases
- **Deduplication**: Large-scale data processing pipelines
- **Access Control**: Permission systems and role-based security
- **Content Filtering**: Spam detection and content moderation
- **Distributed Systems**: Consistent hashing for load distribution
- **Bioinformatics**: Unique sequence identification
- **Social Media**: Tag systems and category management
- **Network Security**: IP blacklisting and whitelist management

## 4. Graph Structures

### Adjacency Lists and Matrices

#### Python Implementation Characteristics
- **NetworkX**: Comprehensive graph analysis library
- **Flexibility**: Easy representation switching between list/matrix formats
- **Algorithm Library**: Extensive collection of graph algorithms
- **Visualization**: Integration with matplotlib and other plotting tools

#### Rust Implementation Characteristics
- **petgraph**: Primary graph library with type-safe representations
- **Memory Efficiency**: Compact graph representations
- **Performance**: Fast graph traversal and analysis
- **Ownership**: Clear ownership semantics for graph mutations

#### Advanced Real-World Use Cases
- **Social Networks**: Friend recommendations and community detection
- **Transportation**: Route optimization and traffic flow analysis
- **Supply Chain**: Logistics optimization and dependency tracking
- **Cybersecurity**: Attack graph analysis and vulnerability assessment
- **Knowledge Graphs**: Semantic web and AI reasoning systems
- **Circuit Design**: Electronic circuit analysis and optimization
- **Protein Folding**: Molecular structure analysis in computational biology

### Specialized Graph Types

#### Advanced Real-World Use Cases
- **Directed Acyclic Graphs (DAGs)**: Build systems and task scheduling
- **Weighted Graphs**: GPS navigation and network routing protocols
- **Bipartite Graphs**: Matching problems and recommendation systems
- **Planar Graphs**: VLSI design and map applications
- **Hypergraphs**: Complex relationship modeling in databases
- **Temporal Graphs**: Dynamic network analysis and social media trending

## 5. Advanced Data Structures

### B-Trees and B+ Trees

#### Python Implementation Characteristics
- **Library Implementations**: Available in database libraries and specialized modules
- **Disk I/O Optimization**: Libraries designed for persistent storage
- **Flexible Node Sizes**: Configurable parameters for different use cases

#### Rust Implementation Characteristics
- **Memory Safety**: Prevention of tree corruption during modifications
- **Performance**: Efficient cache-friendly implementations
- **Persistence**: Safe concurrent access patterns

#### Advanced Real-World Use Cases
- **Database Management**: MySQL, PostgreSQL index structures
- **File Systems**: ext4, NTFS directory indexing
- **Search Engines**: Inverted index storage and retrieval
- **Time-Series Databases**: Efficient range query processing
- **Document Stores**: MongoDB-like document indexing
- **Distributed Systems**: Consistent distributed data structures

### Bloom Filters

#### Python Implementation Characteristics
- **Library Ecosystem**: Multiple implementations with different optimization focuses
- **Bit Array Libraries**: Efficient bit manipulation support
- **Hash Function Flexibility**: Pluggable hash function implementations

#### Rust Implementation Characteristics
- **Memory Efficiency**: Precise control over bit array allocation
- **Hash Performance**: Fast hash function implementations
- **Type Safety**: Compile-time guarantees about filter operations

#### Advanced Real-World Use Cases
- **Web Crawling**: Duplicate URL detection in large-scale crawlers
- **Database Systems**: Query optimization and join processing
- **Distributed Caching**: Cache admission policies
- **Network Security**: DDoS attack mitigation
- **Bioinformatics**: K-mer counting in DNA sequencing
- **Cryptocurrency**: Transaction pool management
- **Content Distribution**: CDN cache optimization

### Skip Lists

#### Advanced Real-World Use Cases
- **Concurrent Databases**: Lock-free data structures
- **Memory Allocators**: Fast memory block location
- **Search Systems**: Range query optimization
- **Real-time Systems**: Predictable insertion/deletion performance
- **Distributed Systems**: Consistent hashing implementations

### Segment Trees and Fenwick Trees

#### Advanced Real-World Use Cases
- **Computational Geometry**: Range query processing in GIS systems
- **Financial Systems**: Portfolio analytics and risk calculation
- **Game Development**: Collision detection and spatial queries
- **Image Processing**: Multi-dimensional range queries
- **Time Series Analysis**: Moving window calculations
- **Online Algorithms**: Dynamic range minimum/maximum queries

## 6. Concurrent Data Structures

### Thread-Safe Collections

#### Python Implementation Characteristics
- **GIL Limitations**: Global Interpreter Lock affects concurrent performance
- **Queue Module**: Thread-safe queue implementations
- **Multiprocessing**: Process-based parallelism for CPU-intensive tasks
- **Asyncio**: Asynchronous programming model for I/O-bound operations

#### Rust Implementation Characteristics
- **Fearless Concurrency**: Compile-time prevention of data races
- **Arc/Mutex**: Atomic reference counting with mutual exclusion
- **Channels**: Message passing between threads
- **Lock-free Structures**: crossbeam crate for advanced concurrent data structures

#### Advanced Real-World Use Cases
- **Web Servers**: Request handling and connection pooling
- **Message Queues**: Kafka-like distributed messaging systems
- **Real-time Analytics**: Stream processing with Apache Flink patterns
- **Game Servers**: Player state management and matchmaking
- **Trading Systems**: Order book management with microsecond latencies
- **IoT Systems**: Sensor data aggregation and processing
- **Distributed Databases**: Consensus algorithms and replication

### Lock-Free Data Structures

#### Advanced Real-World Use Cases
- **High-Frequency Trading**: Ultra-low latency order processing
- **Real-time Systems**: Interrupt handlers and signal processing
- **Garbage Collectors**: Concurrent memory management
- **Database Systems**: Lock-free B-tree implementations
- **Operating Systems**: Kernel data structures and schedulers
- **Network Processing**: Packet forwarding in routers

## 7. Persistent Data Structures

### Immutable Collections

#### Python Implementation Characteristics
- **pyrsistent Library**: Persistent data structure implementations
- **Functional Programming**: Integration with functional programming patterns
- **Memory Sharing**: Structural sharing for memory efficiency

#### Rust Implementation Characteristics
- **im Crate**: Efficient persistent data structure implementations
- **Ownership Model**: Natural fit for immutable data patterns
- **Performance**: Zero-cost abstractions for persistent operations

#### Advanced Real-World Use Cases
- **Version Control**: Git-like systems with efficient branching
- **Undo/Redo Systems**: Editor state management
- **Database Transactions**: MVCC implementations
- **Functional Programming**: Clojure-style data processing
- **Configuration Management**: Infrastructure as code systems
- **Time Travel Debugging**: Development tools and debuggers
- **Blockchain Systems**: Immutable ledger implementations

## 8. Streaming and External Data Structures

### External Sorting and Merging

#### Advanced Real-World Use Cases
- **Big Data Processing**: MapReduce-style data processing
- **Database Systems**: Large table sorting and indexing
- **Log Processing**: Large-scale log analysis systems
- **ETL Pipelines**: Data warehouse loading processes
- **Scientific Computing**: Large dataset analysis
- **Search Engine Indexing**: Web crawl data processing

### Streaming Algorithms

#### Advanced Real-World Use Cases
- **Network Monitoring**: Real-time traffic analysis
- **Financial Analytics**: Real-time risk calculation
- **Social Media**: Trending topic detection
- **IoT Analytics**: Sensor data stream processing
- **Fraud Detection**: Real-time transaction analysis
- **Ad Tech**: Real-time bidding and audience analysis

## 9. Performance Characteristics and Trade-offs

### Memory Usage Patterns
- **Python**: Higher memory overhead due to object model and garbage collection
- **Rust**: Predictable memory usage with zero-cost abstractions
- **Cache Performance**: Rust's control over memory layout provides better cache locality
- **Allocation Patterns**: Rust allows custom allocators for specialized use cases

### Computational Complexity
- **Time Complexity**: Both languages achieve similar algorithmic complexity
- **Constant Factors**: Rust typically has lower constant factors due to compilation
- **Predictability**: Rust provides more predictable performance characteristics
- **Optimization**: Python relies on library optimizations, Rust on compiler optimizations

### Scalability Considerations
- **Vertical Scaling**: Rust better utilizes single-machine resources
- **Horizontal Scaling**: Python's ecosystem better supports distributed computing
- **Memory Scaling**: Rust handles large datasets more efficiently
- **Development Scaling**: Python enables faster team development cycles

## 10. Ecosystem and Tooling Comparison

### Python Ecosystem Strengths
- **Library Richness**: Extensive ecosystem for scientific computing and data analysis
- **Rapid Prototyping**: Quick iteration and experimentation capabilities
- **Community**: Large community with extensive documentation and examples
- **Integration**: Easy integration with databases, web frameworks, and cloud services

### Rust Ecosystem Strengths
- **Performance**: Predictable, high-performance implementations
- **Safety**: Memory safety without garbage collection overhead
- **Concurrency**: Excellent support for concurrent and parallel programming
- **Systems Programming**: Natural fit for low-level and systems programming tasks

## 11. Selection Criteria and Decision Framework

### Choose Python When:
- **Rapid Development**: Prototyping and time-to-market are priorities
- **Data Science**: Heavy integration with scientific computing libraries
- **Team Expertise**: Team has strong Python background
- **Library Dependencies**: Required libraries are primarily available in Python
- **Integration Needs**: Extensive integration with existing Python infrastructure

### Choose Rust When:
- **Performance Critical**: Microsecond-level latencies are required
- **Memory Constraints**: Operating in resource-constrained environments
- **Safety Requirements**: Memory safety is a hard requirement
- **Concurrent Systems**: Building highly concurrent systems
- **Long-term Maintenance**: Building systems for long-term stability

### Hybrid Approaches:
- **Python for Prototyping, Rust for Production**: Develop in Python, rewrite critical components in Rust
- **Polyglot Systems**: Use each language for its strengths within the same system
- **FFI Integration**: Call Rust code from Python using PyO3 or similar bindings
- **Microservices**: Different services in different languages based on requirements

## 12. Future Trends and Considerations

### Emerging Patterns
- **WebAssembly**: Rust's growing presence in browser-based applications
- **Machine Learning**: Rust's emergence in ML inference and high-performance computing
- **Cloud Native**: Both languages adapting to containerized and serverless environments
- **Edge Computing**: Rust's advantages in resource-constrained edge deployments

### Evolution Trajectories
- **Python**: Continued focus on performance improvements and typing systems
- **Rust**: Growing ecosystem and improved ergonomics for application development
- **Interoperability**: Better integration patterns between the two ecosystems
- **Tooling**: Enhanced development tools and debugging capabilities for both languages

## Conclusion

The choice between Python and Rust for data structure implementation depends on project requirements, team expertise, and long-term goals. Python excels in rapid development, data science applications, and situations requiring extensive library ecosystems. Rust shines in performance-critical applications, systems programming, and scenarios requiring memory safety guarantees.

Modern software development increasingly benefits from polyglot approaches, leveraging each language's strengths while mitigating weaknesses through careful architecture design and interface boundaries. The key is matching the tool to the specific requirements of each component within a larger system.

Understanding both ecosystems provides developers with a comprehensive toolkit for addressing diverse computational challenges, from rapid prototyping to production-scale systems requiring maximum performance and reliability.

