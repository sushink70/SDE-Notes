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

# Complete Data Structures Guide: From Basics to Advanced Applications

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

# Data Structures in Go, Rust, Scala, Haskell, Python & TypeScript

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