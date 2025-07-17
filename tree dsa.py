I'll provide a comprehensive explanation of trees in Python, covering all the aspects you've requested.Now let me provide a detailed explanation covering all the aspects you requested:

## What is a Tree?

A tree is a hierarchical data structure consisting of nodes connected by edges, where each node can have zero or more child nodes. It's called a "tree" because it resembles an inverted tree structure with a root at the top and branches extending downward.

## Key Components:

**Root**: The topmost node with no parent
**Node**: Individual elements containing data
**Edge**: Connection between nodes
**Parent**: A node that has children
**Child**: A node connected to a parent
**Leaf**: A node with no children
**Height**: Maximum distance from root to any leaf
**Depth**: Distance from root to a specific node

# Complete Tree Implementation in Python (Without Built-in Modules)

class TreeNode:
    """Basic tree node implementation"""
    def __init__(self, data):
        self.data = data
        self.children = []
        self.parent = None
    
    def add_child(self, child_node):
        """Add a child to this node"""
        child_node.parent = self
        self.children.append(child_node)
    
    def remove_child(self, child_node):
        """Remove a child from this node"""
        if child_node in self.children:
            child_node.parent = None
            self.children.remove(child_node)
    
    def get_level(self):
        """Get the level/depth of this node"""
        level = 0
        current = self
        while current.parent:
            current = current.parent
            level += 1
        return level
    
    def print_tree(self, level=0):
        """Print the tree structure"""
        indent = "  " * level
        print(f"{indent}{self.data}")
        for child in self.children:
            child.print_tree(level + 1)

class BinaryTreeNode:
    """Binary tree node implementation"""
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None

class BinarySearchTree:
    """Binary Search Tree implementation"""
    def __init__(self):
        self.root = None
    
    def insert(self, data):
        """Insert data into BST"""
        if self.root is None:
            self.root = BinaryTreeNode(data)
        else:
            self._insert_recursive(self.root, data)
    
    def _insert_recursive(self, node, data):
        """Helper method for insertion"""
        if data < node.data:
            if node.left is None:
                node.left = BinaryTreeNode(data)
            else:
                self._insert_recursive(node.left, data)
        else:
            if node.right is None:
                node.right = BinaryTreeNode(data)
            else:
                self._insert_recursive(node.right, data)
    
    def search(self, data):
        """Search for data in BST"""
        return self._search_recursive(self.root, data)
    
    def _search_recursive(self, node, data):
        """Helper method for searching"""
        if node is None:
            return False
        if node.data == data:
            return True
        elif data < node.data:
            return self._search_recursive(node.left, data)
        else:
            return self._search_recursive(node.right, data)
    
    def delete(self, data):
        """Delete data from BST"""
        self.root = self._delete_recursive(self.root, data)
    
    def _delete_recursive(self, node, data):
        """Helper method for deletion"""
        if node is None:
            return node
        
        if data < node.data:
            node.left = self._delete_recursive(node.left, data)
        elif data > node.data:
            node.right = self._delete_recursive(node.right, data)
        else:
            # Node to be deleted found
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            
            # Node has two children
            min_val = self._find_min(node.right)
            node.data = min_val
            node.right = self._delete_recursive(node.right, min_val)
        
        return node
    
    def _find_min(self, node):
        """Find minimum value in subtree"""
        while node.left is not None:
            node = node.left
        return node.data
    
    def inorder_traversal(self):
        """Inorder traversal (Left, Root, Right)"""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node, result):
        """Helper for inorder traversal"""
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.data)
            self._inorder_recursive(node.right, result)
    
    def preorder_traversal(self):
        """Preorder traversal (Root, Left, Right)"""
        result = []
        self._preorder_recursive(self.root, result)
        return result
    
    def _preorder_recursive(self, node, result):
        """Helper for preorder traversal"""
        if node:
            result.append(node.data)
            self._preorder_recursive(node.left, result)
            self._preorder_recursive(node.right, result)
    
    def postorder_traversal(self):
        """Postorder traversal (Left, Right, Root)"""
        result = []
        self._postorder_recursive(self.root, result)
        return result
    
    def _postorder_recursive(self, node, result):
        """Helper for postorder traversal"""
        if node:
            self._postorder_recursive(node.left, result)
            self._postorder_recursive(node.right, result)
            result.append(node.data)

class AVLTree:
    """Self-balancing AVL Tree implementation"""
    def __init__(self):
        self.root = None
    
    class AVLNode:
        def __init__(self, data):
            self.data = data
            self.left = None
            self.right = None
            self.height = 1
    
    def get_height(self, node):
        """Get height of node"""
        if not node:
            return 0
        return node.height
    
    def get_balance(self, node):
        """Get balance factor of node"""
        if not node:
            return 0
        return self.get_height(node.left) - self.get_height(node.right)
    
    def update_height(self, node):
        """Update height of node"""
        if node:
            node.height = 1 + max(self.get_height(node.left), 
                                 self.get_height(node.right))
    
    def rotate_right(self, y):
        """Right rotation"""
        x = y.left
        T2 = x.right
        
        x.right = y
        y.left = T2
        
        self.update_height(y)
        self.update_height(x)
        
        return x
    
    def rotate_left(self, x):
        """Left rotation"""
        y = x.right
        T2 = y.left
        
        y.left = x
        x.right = T2
        
        self.update_height(x)
        self.update_height(y)
        
        return y
    
    def insert(self, data):
        """Insert data into AVL tree"""
        self.root = self._insert_recursive(self.root, data)
    
    def _insert_recursive(self, node, data):
        """Helper method for AVL insertion"""
        # Normal BST insertion
        if not node:
            return self.AVLNode(data)
        
        if data < node.data:
            node.left = self._insert_recursive(node.left, data)
        else:
            node.right = self._insert_recursive(node.right, data)
        
        # Update height
        self.update_height(node)
        
        # Get balance factor
        balance = self.get_balance(node)
        
        # Left Left Case
        if balance > 1 and data < node.left.data:
            return self.rotate_right(node)
        
        # Right Right Case
        if balance < -1 and data > node.right.data:
            return self.rotate_left(node)
        
        # Left Right Case
        if balance > 1 and data > node.left.data:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)
        
        # Right Left Case
        if balance < -1 and data < node.right.data:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)
        
        return node

class Trie:
    """Trie (Prefix Tree) implementation"""
    def __init__(self):
        self.root = self.TrieNode()
    
    class TrieNode:
        def __init__(self):
            self.children = {}
            self.is_end_of_word = False
    
    def insert(self, word):
        """Insert word into trie"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = self.TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
    
    def search(self, word):
        """Search for word in trie"""
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word
    
    def starts_with(self, prefix):
        """Check if any word starts with prefix"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

class HeapTree:
    """Min Heap implementation using tree structure"""
    def __init__(self):
        self.heap = []
    
    def parent(self, i):
        """Get parent index"""
        return (i - 1) // 2
    
    def left_child(self, i):
        """Get left child index"""
        return 2 * i + 1
    
    def right_child(self, i):
        """Get right child index"""
        return 2 * i + 2
    
    def swap(self, i, j):
        """Swap elements at indices i and j"""
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
    
    def insert(self, data):
        """Insert data into heap"""
        self.heap.append(data)
        self._heapify_up(len(self.heap) - 1)
    
    def _heapify_up(self, i):
        """Heapify up from index i"""
        while i > 0 and self.heap[i] < self.heap[self.parent(i)]:
            self.swap(i, self.parent(i))
            i = self.parent(i)
    
    def extract_min(self):
        """Extract minimum element"""
        if not self.heap:
            return None
        
        min_val = self.heap[0]
        self.heap[0] = self.heap[-1]
        self.heap.pop()
        
        if self.heap:
            self._heapify_down(0)
        
        return min_val
    
    def _heapify_down(self, i):
        """Heapify down from index i"""
        while True:
            smallest = i
            left = self.left_child(i)
            right = self.right_child(i)
            
            if (left < len(self.heap) and 
                self.heap[left] < self.heap[smallest]):
                smallest = left
            
            if (right < len(self.heap) and 
                self.heap[right] < self.heap[smallest]):
                smallest = right
            
            if smallest == i:
                break
            
            self.swap(i, smallest)
            i = smallest

# Real-world examples and usage

def file_system_example():
    """Example: File system representation"""
    print("=== File System Example ===")
    
    # Create root directory
    root = TreeNode("C:")
    
    # Add directories
    users = TreeNode("Users")
    program_files = TreeNode("Program Files")
    windows = TreeNode("Windows")
    
    root.add_child(users)
    root.add_child(program_files)
    root.add_child(windows)
    
    # Add subdirectories
    john = TreeNode("John")
    admin = TreeNode("Admin")
    users.add_child(john)
    users.add_child(admin)
    
    # Add files
    documents = TreeNode("Documents")
    desktop = TreeNode("Desktop")
    john.add_child(documents)
    john.add_child(desktop)
    
    # Print file system structure
    root.print_tree()
    print()

def company_hierarchy_example():
    """Example: Company organizational chart"""
    print("=== Company Hierarchy Example ===")
    
    ceo = TreeNode("CEO")
    
    # VPs
    vp_engineering = TreeNode("VP Engineering")
    vp_sales = TreeNode("VP Sales")
    vp_marketing = TreeNode("VP Marketing")
    
    ceo.add_child(vp_engineering)
    ceo.add_child(vp_sales)
    ceo.add_child(vp_marketing)
    
    # Engineering team
    senior_dev = TreeNode("Senior Developer")
    junior_dev = TreeNode("Junior Developer")
    qa_lead = TreeNode("QA Lead")
    
    vp_engineering.add_child(senior_dev)
    vp_engineering.add_child(junior_dev)
    vp_engineering.add_child(qa_lead)
    
    ceo.print_tree()
    print()

def bst_example():
    """Example: Binary Search Tree usage"""
    print("=== Binary Search Tree Example ===")
    
    bst = BinarySearchTree()
    
    # Insert values
    values = [50, 30, 70, 20, 40, 60, 80]
    for val in values:
        bst.insert(val)
    
    print("Inserted values:", values)
    print("Inorder traversal:", bst.inorder_traversal())
    print("Preorder traversal:", bst.preorder_traversal())
    print("Postorder traversal:", bst.postorder_traversal())
    
    # Search examples
    print("Search 40:", bst.search(40))
    print("Search 90:", bst.search(90))
    
    # Delete example
    bst.delete(30)
    print("After deleting 30:", bst.inorder_traversal())
    print()

def trie_example():
    """Example: Trie for autocomplete"""
    print("=== Trie Example (Autocomplete) ===")
    
    trie = Trie()
    
    # Insert words
    words = ["apple", "app", "application", "apply", "banana", "band"]
    for word in words:
        trie.insert(word)
    
    print("Inserted words:", words)
    print("Search 'app':", trie.search("app"))
    print("Search 'appl':", trie.search("appl"))
    print("Starts with 'app':", trie.starts_with("app"))
    print("Starts with 'ban':", trie.starts_with("ban"))
    print()

def heap_example():
    """Example: Min Heap for priority queue"""
    print("=== Min Heap Example ===")
    
    heap = HeapTree()
    
    # Insert values
    values = [10, 20, 5, 6, 1, 8, 9, 4]
    for val in values:
        heap.insert(val)
    
    print("Inserted values:", values)
    print("Heap array:", heap.heap)
    
    # Extract minimum values
    print("Extracting minimums:")
    while heap.heap:
        print(heap.extract_min(), end=" ")
    print("\n")

# Database integration example (conceptual)
class DatabaseTreeNode:
    """Tree node that can be stored in database"""
    def __init__(self, id, data, parent_id=None):
        self.id = id
        self.data = data
        self.parent_id = parent_id
        self.children = []
    
    def to_dict(self):
        """Convert node to dictionary for database storage"""
        return {
            'id': self.id,
            'data': self.data,
            'parent_id': self.parent_id
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create node from database dictionary"""
        return cls(data['id'], data['data'], data['parent_id'])

def database_example():
    """Example: Tree with database-like operations"""
    print("=== Database Integration Example ===")
    
    # Simulate database records
    db_records = [
        {'id': 1, 'data': 'Root', 'parent_id': None},
        {'id': 2, 'data': 'Child 1', 'parent_id': 1},
        {'id': 3, 'data': 'Child 2', 'parent_id': 1},
        {'id': 4, 'data': 'Grandchild 1', 'parent_id': 2},
        {'id': 5, 'data': 'Grandchild 2', 'parent_id': 2},
    ]
    
    # Build tree from database records
    nodes = {}
    for record in db_records:
        node = DatabaseTreeNode.from_dict(record)
        nodes[node.id] = node
    
    # Link parent-child relationships
    for node in nodes.values():
        if node.parent_id:
            parent = nodes[node.parent_id]
            parent.children.append(node)
    
    # Find root and print tree
    root = next(node for node in nodes.values() if node.parent_id is None)
    print("Tree structure from database:")
    print_db_tree(root)
    print()

def print_db_tree(node, level=0):
    """Print database tree structure"""
    indent = "  " * level
    print(f"{indent}{node.data} (ID: {node.id})")
    for child in node.children:
        print_db_tree(child, level + 1)

# Security example
class SecureTreeNode:
    """Tree node with basic security features"""
    def __init__(self, data, access_level=0):
        self.data = data
        self.access_level = access_level
        self.children = []
        self.parent = None
    
    def add_child(self, child_node, user_level=0):
        """Add child with access control"""
        if user_level >= self.access_level:
            child_node.parent = self
            self.children.append(child_node)
            return True
        return False
    
    def get_data(self, user_level=0):
        """Get data with access control"""
        if user_level >= self.access_level:
            return self.data
        return "Access Denied"

def security_example():
    """Example: Tree with access control"""
    print("=== Security Example ===")
    
    # Create nodes with different access levels
    public_root = SecureTreeNode("Public Information", 0)
    internal_node = SecureTreeNode("Internal Data", 1)
    confidential_node = SecureTreeNode("Confidential Data", 2)
    
    # Try to add children with different user levels
    print("Adding internal node (user level 1):", 
          public_root.add_child(internal_node, 1))
    print("Adding confidential node (user level 0):", 
          public_root.add_child(confidential_node, 0))
    print("Adding confidential node (user level 2):", 
          public_root.add_child(confidential_node, 2))
    
    # Access data with different user levels
    print("Access internal data (user level 0):", 
          internal_node.get_data(0))
    print("Access internal data (user level 1):", 
          internal_node.get_data(1))
    print()

# Performance testing
def performance_test():
    """Basic performance comparison"""
    print("=== Performance Test ===")
    
    import time
    
    # Test BST insertion
    bst = BinarySearchTree()
    start_time = time.time()
    for i in range(1000):
        bst.insert(i)
    bst_time = time.time() - start_time
    
    # Test list insertion (for comparison)
    lst = []
    start_time = time.time()
    for i in range(1000):
        lst.append(i)
    list_time = time.time() - start_time
    
    print(f"BST insertion (1000 items): {bst_time:.6f} seconds")
    print(f"List insertion (1000 items): {list_time:.6f} seconds")
    
    # Test search performance
    start_time = time.time()
    for i in range(100):
        bst.search(i)
    bst_search_time = time.time() - start_time
    
    start_time = time.time()
    for i in range(100):
        i in lst
    list_search_time = time.time() - start_time
    
    print(f"BST search (100 searches): {bst_search_time:.6f} seconds")
    print(f"List search (100 searches): {list_search_time:.6f} seconds")
    print()

if __name__ == "__main__":
    # Run all examples
    file_system_example()
    company_hierarchy_example()
    bst_example()
    trie_example()
    heap_example()
    database_example()
    security_example()
    performance_test()

## Types of Trees Implemented:

1. **General Tree**: Nodes can have any number of children
2. **Binary Tree**: Each node has at most 2 children
3. **Binary Search Tree (BST)**: Binary tree with ordering property
4. **AVL Tree**: Self-balancing binary search tree
5. **Trie**: Prefix tree for string operations
6. **Heap**: Complete binary tree with heap property

## Where Trees Can Be Used:

**File Systems**: Directory structures with folders and files
**Database Indexing**: B-trees and B+ trees for efficient data retrieval
**Expression Parsing**: Abstract syntax trees for compilers
**Autocomplete Systems**: Tries for prefix matching
**Decision Making**: Decision trees in AI/ML
**Network Routing**: Spanning trees in network protocols
**Game Development**: Game state trees, AI decision trees
**Organizational Charts**: Company hierarchy representation
**XML/HTML Parsing**: DOM trees for document structure
**Priority Queues**: Heap trees for task scheduling

## Where Trees Should NOT Be Used:

**Sequential Access**: When you need to access elements in order frequently
**Random Access**: When you need constant-time access to elements by index
**Simple Key-Value Storage**: When a hash table would be more efficient
**Small Datasets**: Overhead may not be justified for small amounts of data
**Frequent Insertions/Deletions at Beginning**: Arrays or linked lists might be better
**Memory-Constrained Systems**: Trees have pointer overhead

## Big O Notation:

### Binary Search Tree (Average Case):
- **Search**: O(log n)
- **Insertion**: O(log n)
- **Deletion**: O(log n)
- **Space**: O(n)

### Binary Search Tree (Worst Case - Skewed):
- **Search**: O(n)
- **Insertion**: O(n)
- **Deletion**: O(n)

### AVL Tree (Balanced):
- **Search**: O(log n)
- **Insertion**: O(log n)
- **Deletion**: O(log n)
- **Space**: O(n)

### Trie:
- **Search**: O(m) where m is key length
- **Insertion**: O(m)
- **Deletion**: O(m)
- **Space**: O(ALPHABET_SIZE * N * M)

### Heap:
- **Insert**: O(log n)
- **Extract Min/Max**: O(log n)
- **Peek**: O(1)
- **Space**: O(n)

## Advantages:

**Hierarchical Structure**: Natural representation of hierarchical data
**Efficient Searching**: O(log n) search in balanced trees
**Dynamic Size**: Can grow and shrink during runtime
**Sorted Data**: In-order traversal of BST gives sorted sequence
**Prefix Matching**: Tries excel at prefix-based operations
**Memory Efficiency**: Only allocate memory as needed
**Flexibility**: Can represent complex relationships

## Disadvantages:

**Memory Overhead**: Extra memory for storing pointers
**Complexity**: More complex than linear data structures
**Balancing Issues**: Unbalanced trees can degrade to O(n) operations
**No Random Access**: Can't access elements by index efficiently
**Recursion Overhead**: Many operations use recursion
**Cache Performance**: Poor cache locality compared to arrays

## Database Integration:

Trees can be effectively used with databases in several ways:

**Adjacency List Model**: Store parent-child relationships in tables
**Nested Set Model**: Store tree structure using left/right values
**Path Enumeration**: Store full path from root to each node
**Closure Table**: Store all ancestor-descendant relationships

The example in the code shows how to reconstruct a tree from database records using the adjacency list model. This is particularly useful for:
- Category hierarchies in e-commerce
- Comment threads in forums
- Organizational structures
- Menu systems

## Security Considerations:

**Access Control**: Implement permission levels for different nodes
**Data Validation**: Validate input data to prevent malicious insertions
**Memory Management**: Prevent memory leaks and buffer overflows
**Traversal Limits**: Implement depth limits to prevent stack overflow
**Sanitization**: Clean user input before storing in tree nodes
**Encryption**: Encrypt sensitive data stored in nodes

The security example demonstrates basic access control mechanisms where nodes have different permission levels.

## Performance Considerations:

**Memory Usage**: Trees use more memory than arrays due to pointer storage
**CPU Cache**: Poor cache locality compared to arrays
**Balancing**: Keep trees balanced for optimal performance
**Iterative vs Recursive**: Iterative approaches can be more memory-efficient
**Batch Operations**: Consider bulk operations for better performance

## Real-World Implementation Tips:

1. **Choose the Right Tree Type**: BST for searching, heap for priority queues, trie for strings
2. **Balance Considerations**: Use AVL or Red-Black trees for guaranteed balance
3. **Memory Management**: Implement proper cleanup to prevent memory leaks
4. **Error Handling**: Add validation and error checking
5. **Threading**: Consider thread safety for concurrent access
6. **Persistence**: Implement serialization for data persistence

The comprehensive code example demonstrates practical implementations of various tree types with real-world scenarios including file systems, company hierarchies, autocomplete systems, and database integration. Each implementation focuses on efficiency and practical usability while maintaining clean, readable code structure.

Let’s dive into a detailed explanation of a **tree data structure** implemented in Python without using built-in modules, covering its definition, use cases, real-world examples, advantages, disadvantages, Big O notation, database integration, security considerations, and more.

---

### **What is a Tree Data Structure?**

A tree is a hierarchical, non-linear data structure consisting of nodes connected by edges. Each node contains a value and references to its child nodes. The topmost node is called the **root**, and nodes with no children are called **leaves**. Trees are widely used to represent hierarchical relationships, such as file systems, organizational structures, or decision trees.

Key properties of a tree:
- **Root**: The top node with no parent.
- **Parent**: A node that has child nodes.
- **Child**: A node connected to a parent.
- **Leaf**: A node with no children.
- **Height**: The length of the longest path from the root to a leaf.
- **Depth**: The length of the path from the root to a specific node.

---

### **Implementation of a Tree in Python**

We’ll implement a basic **binary tree** (each node has at most two children: left and right) from scratch, including methods for insertion, traversal, and searching.

```python
class TreeNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

class BinaryTree:
    def __init__(self):
        self.root = None
    
    # Insert a node
    def insert(self, value):
        if not self.root:
            self.root = TreeNode(value)
        else:
            self._insert_recursive(self.root, value)
    
    def _insert_recursive(self, node, value):
        if value < node.value:
            if node.left is None:
                node.left = TreeNode(value)
            else:
                self._insert_recursive(node.left, value)
        else:
            if node.right is None:
                node.right = TreeNode(value)
            else:
                self._insert_recursive(node.right, value)
    
    # Inorder traversal (Left, Root, Right)
    def inorder_traversal(self):
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)
    
    # Search for a value
    def search(self, value):
        return self._search_recursive(self.root, value)
    
    def _search_recursive(self, node, value):
        if node is None or node.value == value:
            return node
        if value < node.value:
            return self._search_recursive(node.left, value)
        return self._search_recursive(node.right, value)

# Example usage
if __name__ == "__main__":
    tree = BinaryTree()
    values = [5, 3, 7, 2, 4, 6, 8]
    for value in values:
        tree.insert(value)
    
    print("Inorder Traversal:", tree.inorder_traversal())  # Output: [2, 3, 4, 5, 6, 7, 8]
    
    search_value = 4
    result = tree.search(search_value)
    print(f"Search for {search_value}: {'Found' if result else 'Not Found'}")
```

This implementation creates a **Binary Search Tree (BST)** where:
- Nodes with values less than the parent go to the left subtree.
- Nodes with values greater than or equal to the parent go to the right subtree.
- It supports insertion, inorder traversal, and searching.

---

### **Where Trees Can Be Used**

Trees are versatile and used in many domains:
1. **File Systems**: Representing directories and files (e.g., folder structures in operating systems).
2. **Databases**: Indexes like B-trees or B+ trees for efficient querying.
3. **Compilers**: Syntax trees for parsing code (e.g., Abstract Syntax Trees in Python’s `ast` module).
4. **Networking**: Routing algorithms (e.g., decision trees for packet routing).
5. **AI/ML**: Decision trees, random forests, or hierarchical clustering.
6. **Web Development**: DOM (Document Object Model) for HTML/XML parsing.
7. **Games**: Game trees for AI decision-making (e.g., chess move prediction).

---

### **Where Trees Should Not Be Used**

1. **Linear Data**: If data is sequential (e.g., time-series data), use arrays or linked lists for simplicity.
2. **Unstructured Data**: Trees require a hierarchical structure; they’re inefficient for flat or random data.
3. **High Update Frequency**: In scenarios with frequent insertions/deletions, balanced trees (e.g., AVL, Red-Black) are needed, but they add complexity.
4. **Memory Constraints**: Trees use more memory due to pointers/references compared to arrays.

---

### **Real-World Code Example**

Let’s build a simple **file system simulator** using a tree to represent directories and files.

```python
class FileSystemNode:
    def __init__(self, name, is_directory=False):
        self.name = name
        self.is_directory = is_directory
        self.children = []  # List of child nodes (files or directories)
        self.parent = None

class FileSystem:
    def __init__(self):
        self.root = FileSystemNode("/", is_directory=True)
        self.current_directory = self.root
    
    def mkdir(self, name):
        new_dir = FileSystemNode(name, is_directory=True)
        new_dir.parent = self.current_directory
        self.current_directory.children.append(new_dir)
    
    def touch(self, name):
        new_file = FileSystemNode(name, is_directory=False)
        new_file.parent = self.current_directory
        self.current_directory.children.append(new_file)
    
    def cd(self, path):
        if path == "..":
            if self.current_directory.parent:
                self.current_directory = self.current_directory.parent
        else:
            for child in self.current_directory.children:
                if child.name == path and child.is_directory:
                    self.current_directory = child
                    return
            print(f"Directory {path} not found")
    
    def ls(self):
        return [child.name for child in self.current_directory.children]

# Example usage
fs = FileSystem()
fs.mkdir("home")
fs.cd("home")
fs.touch("file1.txt")
fs.mkdir("docs")
fs.cd("docs")
fs.touch("note.txt")
fs.cd("..")
print(fs.ls())  # Output: ['file1.txt', 'docs']
fs.cd("docs")
print(fs.ls())  # Output: ['note.txt']
```

This simulates a file system where directories and files are nodes in a tree. The `cd`, `mkdir`, `touch`, and `ls` commands mimic Unix-like functionality.

---

### **Advantages of Trees**

1. **Hierarchical Representation**: Naturally models parent-child relationships.
2. **Efficient Operations**: In a balanced BST, operations like search, insert, and delete are O(log n).
3. **Flexibility**: Supports various types (BST, AVL, Red-Black, B-trees, etc.) for different needs.
4. **Scalability**: Suitable for large datasets when balanced (e.g., database indexing).
5. **Traversal Options**: Multiple traversal methods (inorder, preorder, postorder) for different use cases.

---

### **Disadvantages of Trees**

1. **Complexity**: Implementation is more complex than arrays or linked lists.
2. **Memory Overhead**: Each node stores pointers, increasing memory usage.
3. **Unbalanced Trees**: A skewed tree (e.g., inserting sorted data) degrades to O(n) performance.
4. **Maintenance**: Balancing trees (e.g., AVL, Red-Black) requires additional logic and computation.
5. **Not Cache-Friendly**: Non-contiguous memory allocation reduces cache efficiency compared to arrays.

---

### **Big O Notation**

For a **balanced BST** (e.g., AVL or Red-Black tree):
- **Search**: O(log n) – Logarithmic time due to halving the search space.
- **Insert**: O(log n) – Includes finding the position and inserting.
- **Delete**: O(log n) – Similar to insertion, with rebalancing.
- **Traversal**: O(n) – Visiting all nodes (inorder, preorder, or postorder).
- **Space Complexity**: O(n) for storing n nodes; O(h) for recursion stack, where h is the tree height (O(log n) for balanced trees, O(n) for skewed).

For an **unbalanced BST**:
- **Search, Insert, Delete**: O(n) in the worst case (skewed tree resembling a linked list).

For general trees (e.g., n-ary trees):
- **Search**: O(n) in the worst case, as all nodes may need to be visited.
- **Insert**: O(n) to find the correct parent node.
- **Space**: O(n) for nodes, O(h) for recursion stack.

---

### **Using Trees with Database Connections**

Trees can be integrated with databases for efficient data organization and querying. Here’s how:

1. **Hierarchical Data Storage**:
   - Store hierarchical data (e.g., organizational charts, categories) in relational databases using parent-child relationships.
   - Example: A table with columns `id`, `name`, `parent_id` to represent a tree.

2. **Indexing with Trees**:
   - Databases use B-trees or B+ trees for indexes to enable fast lookups, range queries, and joins.
   - Example: MySQL’s InnoDB uses B+ trees for primary key indexes.

3. **Python with Databases**:
   Use a library like `psycopg2` (for PostgreSQL) or `pymysql` (for MySQL) to interact with a database and represent data as a tree.

Here’s an example of a tree stored in a database and reconstructed in Python:

```python
import sqlite3

# Create a database to store a tree
conn = sqlite3.connect("tree.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS nodes (id INTEGER PRIMARY KEY, value TEXT, parent_id INTEGER)")

# Insert nodes
def insert_node(value, parent_id=None):
    cursor.execute("INSERT INTO nodes (value, parent_id) VALUES (?, ?)", (value, parent_id))
    conn.commit()
    return cursor.lastrowid

# Build tree from database
class DBTreeNode:
    def __init__(self, id, value):
        self.id = id
        self.value = value
        self.children = []

def build_tree_from_db():
    cursor.execute("SELECT id, value, parent_id FROM nodes")
    nodes = {row[0]: DBTreeNode(row[0], row[1]) for row in cursor.fetchall()}
    for row in cursor.fetchall():
        if row[2] is not None:
            nodes[row[2]].children.append(nodes[row[0]])
    return nodes[1] if 1 in nodes else None

# Example usage
root_id = insert_node("Root")
child1_id = insert_node("Child1", root_id)
child2_id = insert_node("Child2", root_id)
insert_node("Grandchild", child1_id)

# Reconstruct and print tree
root = build_tree_from_db()
def print_tree(node, level=0):
    if node:
        print("  " * level + node.value)
        for child in node.children:
            print_tree(child, level + 1)

print_tree(root)
conn.close()
```

This code stores a tree in SQLite and reconstructs it in memory. It’s useful for applications like content management systems or family trees.

---

### **Security Considerations**

When using trees with databases or in production:
1. **SQL Injection**: Sanitize inputs when querying the database (use parameterized queries, as shown above).
2. **Access Control**: Ensure only authorized users can modify the tree structure.
3. **Data Validation**: Validate node values to prevent malicious data (e.g., excessively large strings).
4. **Concurrency**: Use database transactions or locks to prevent race conditions in multi-user systems.
5. **Memory Safety**: Avoid deep recursion in large trees to prevent stack overflow; use iterative approaches or tail recursion.
6. **Serialization**: If trees are serialized (e.g., to JSON), validate and sanitize data to prevent injection attacks.

---

### **Conclusion**

Trees are powerful for hierarchical data, with efficient operations when balanced. They’re widely used in file systems, databases, and AI but require careful implementation to avoid performance pitfalls (e.g., unbalanced trees). Integrating trees with databases is straightforward, and security practices like input validation and parameterized queries are essential in production.

If you’d like a chart to visualize tree performance (e.g., Big O comparisons) or a specific tree variant (e.g., AVL, B-tree), let me know!

I'll provide a comprehensive explanation of the **Tree data structure** in Python, focusing on implementation using built-in modules, its applications, limitations, real-world examples, advantages, disadvantages, Big-O notation, database integration, and security considerations.

---

### **1. What is a Tree Data Structure?**

A tree is a hierarchical, non-linear data structure consisting of nodes connected by edges. Each node contains data and may have child nodes. The topmost node is called the **root**, and nodes with no children are called **leaves**. Trees are widely used to represent hierarchical relationships, such as file systems, organizational charts, or decision trees.

Key properties of a tree:
- **Root**: The top node of the tree.
- **Parent**: A node that has child nodes.
- **Child**: A node directly connected to a parent node.
- **Leaf**: A node with no children.
- **Height**: The length of the longest path from the root to a leaf.
- **Depth**: The distance from the root to a specific node.

---

### **2. Implementing a Tree in Python Using Built-in Modules**

Python doesn't have a built-in tree data structure, but we can implement it using classes and built-in modules like `collections` for managing nodes and relationships. Below is an example of a **generic tree** implementation.

#### **Basic Tree Implementation**

```python
from collections import defaultdict

class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, child_node):
        """Add a child node to this node."""
        self.children.append(child_node)

    def remove_child(self, child_node):
        """Remove a child node from this node."""
        self.children = [child for child in self.children if child != child_node]

    def __str__(self):
        return f"Node({self.value})"

class Tree:
    def __init__(self):
        self.root = None

    def set_root(self, value):
        """Set the root of the tree."""
        self.root = TreeNode(value)

    def traverse_dfs(self, node=None, depth=0):
        """Depth-First Search traversal (pre-order)."""
        if node is None:
            node = self.root
        if node is None:
            return
        print("  " * depth + str(node.value))
        for child in node.children:
            self.traverse_dfs(child, depth + 1)

# Example usage
tree = Tree()
tree.set_root("CEO")
cto = TreeNode("CTO")
cfo = TreeNode("CFO")
dev = TreeNode("Developer")
qa = TreeNode("QA")
accountant = TreeNode("Accountant")

tree.root.add_child(cto)
tree.root.add_child(cfo)
cto.add_child(dev)
cto.add_child(qa)
cfo.add_child(accountant)

# Traverse the tree
print("Tree Structure (DFS):")
tree.traverse_dfs()
```

**Output:**
```
Tree Structure (DFS):
CEO
  CTO
    Developer
    QA
  CFO
    Accountant
```

This implementation uses:
- A `TreeNode` class to represent nodes with a value and a list of children.
- A `Tree` class to manage the tree and provide traversal methods.
- The `collections.defaultdict` could be used for more complex trees (e.g., adjacency lists for graph-like trees), but here we use a simple list for children.

---

### **3. Where Trees Can Be Used**

Trees are versatile and used in many domains:
1. **File Systems**: Represent directory structures (e.g., folders and files).
2. **Organization Charts**: Model hierarchical relationships in companies.
3. **XML/JSON Parsing**: Represent nested data structures.
4. **Decision Trees**: Used in machine learning for classification and regression.
5. **Database Indexing**: B-trees and B+ trees for efficient querying in databases.
6. **Syntax Trees**: Used in compilers to parse code.
7. **DOM in Web Development**: HTML documents are represented as a tree (Document Object Model).
8. **Networking**: Routing algorithms often use trees (e.g., spanning trees).
9. **AI and Game Development**: Minimax trees for game AI decision-making.

---

### **4. Where Trees Should Not Be Used**

1. **Linear Data**: If data is sequential (e.g., a list of numbers), a tree adds unnecessary complexity. Use arrays or lists instead.
2. **Highly Connected Data**: If relationships are not hierarchical (e.g., social networks), graphs are more appropriate.
3. **Small Datasets**: For small datasets, simpler data structures like lists or dictionaries may suffice.
4. **Frequent Updates**: If the tree structure changes frequently (e.g., inserting/removing nodes), maintaining balance (in BSTs or B-trees) can be costly.

---

### **5. Real-World Code Example**

#### **Example: File System Tree**

Here's a real-world example of a tree to represent a file system and search for a file.

```python
class FileSystemNode:
    def __init__(self, name, is_file=False):
        self.name = name
        self.is_file = is_file
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def search_file(self, file_name):
        """Search for a file in the tree."""
        if self.is_file and self.name == file_name:
            return self
        for child in self.children:
            result = child.search_file(file_name)
            if result:
                return result
        return None

    def __str__(self):
        return f"{'File' if self.is_file else 'Dir'}: {self.name}"

# Create a file system tree
root = FileSystemNode("/")
home = FileSystemNode("home")
user = FileSystemNode("user")
docs = FileSystemNode("docs")
readme = FileSystemNode("readme.txt", is_file=True)
pictures = FileSystemNode("pictures")
photo = FileSystemNode("photo.jpg", is_file=True)

root.add_child(home)
home.add_child(user)
user.add_child(docs)
user.add_child(pictures)
docs.add_child(readme)
pictures.add_child(photo)

# Search for a file
file_name = "photo.jpg"
result = root.search_file(file_name)
print(f"Searching for {file_name}: {'Found ' + str(result) if result else 'Not found'}")
```

**Output:**
```
Searching for photo.jpg: Found File: photo.jpg
```

This models a file system where directories and files are nodes, and we can search for a specific file using DFS.

---

### **6. Advantages of Trees**

1. **Hierarchical Representation**: Naturally represents hierarchical relationships.
2. **Efficient Searching**: In balanced trees (e.g., BST, AVL), searching is O(log n).
3. **Scalability**: Suitable for large datasets with hierarchical structures.
4. **Flexibility**: Supports various traversal methods (DFS, BFS) for different use cases.
5. **Specialized Variants**: B-trees, AVL trees, and Red-Black trees optimize specific operations.

---

### **7. Disadvantages of Trees**

1. **Complexity**: Implementing and maintaining trees (especially balanced ones) is complex.
2. **Memory Overhead**: Each node requires pointers to children, increasing memory usage.
3. **Balancing Issues**: Unbalanced trees (e.g., skewed BSTs) degrade to O(n) performance.
4. **Not Ideal for Non-Hierarchical Data**: Inefficient for non-hierarchical relationships.
5. **Traversal Overhead**: Traversing large trees can be computationally expensive.

---

### **8. Big-O Notation**

The time complexity depends on the type of tree and operation:

| Operation          | General Tree | Binary Search Tree (Balanced) | Binary Search Tree (Unbalanced) |
|---------------------|--------------|-------------------------------|----------------------------------|
| **Insertion**       | O(1)         | O(log n)                     | O(n)                            |
| **Deletion**        | O(n)         | O(log n)                     | O(n)                            |
| **Search**          | O(n)         | O(log n)                     | O(n)                            |
| **Traversal**       | O(n)         | O(n)                         | O(n)                            |

- **General Tree**: No inherent ordering, so searching requires visiting all nodes (O(n)).
- **Balanced BST**: Operations are O(log n) due to logarithmicස

System: **Tree Operations and Big-O Notation (Continued)**

- **Balanced BST (Binary Search Tree)**: Operations like insertion, deletion, and search are O(log n) because the tree is height-balanced, ensuring the height is logarithmic in the number of nodes (n).
- **Unbalanced BST**: In the worst case (e.g., a skewed tree), operations degrade to O(n) as the tree behaves like a linked list.

For specialized trees like **B-trees** or **AVL trees** used in databases:
- **Search/Insert/Delete**: O(log n) due to their balanced nature.
- **Space Complexity**: O(n) for storing n nodes, with additional memory for pointers to children.

---

### **9. Using Trees with Database Connections**

Trees can be integrated with databases to represent and query hierarchical data. For example:
- **Relational Databases**: Store tree structures using adjacency lists (parent-child relationships) or nested sets.
- **NoSQL Databases**: Document-based databases like MongoDB can store trees as nested JSON-like structures.

#### **Example: Storing a Tree in SQLite**

```python
import sqlite3

# Create a database and table
conn = sqlite3.connect('tree.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tree (
        id INTEGER PRIMARY KEY,
        value TEXT,
        parent_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES tree(id)
    )
''')

# Insert nodes (e.g., organizational hierarchy)
def insert_node(value, parent_id=None):
    cursor.execute("INSERT INTO tree (value, parent_id) VALUES (?, ?)", (value, parent_id))
    conn.commit()
    return cursor.lastrowid

# Build a tree
root_id = insert_node("CEO")
cto_id = insert_node("CTO", root_id)
cfo_id = insert_node("CFO", root_id)
insert_node("Developer", cto_id)
insert_node("QA", cto_id)
insert_node("Accountant", cfo_id)

# Query the tree (e.g., get all children of CTO)
cursor.execute("SELECT value FROM tree WHERE parent_id = ?", (cto_id,))
children = cursor.fetchall()
print("CTO's direct reports:", [row[0] for row in children])

# Close connection
conn.close()
```

**Output:**
```
CTO's direct reports: ['Developer', 'QA']
```

**Use Cases in Databases**:
- **Hierarchical Data**: Store organizational charts, product categories, or comment threads.
- **B-trees/B+ Trees**: Used internally by databases (e.g., MySQL, PostgreSQL) for indexing to optimize query performance.

**Challenges**:
- Querying hierarchical data in relational databases can be complex (e.g., recursive queries for deep trees).
- NoSQL databases are more flexible but may lack ACID guarantees.

---

### **10. Security Considerations**

When using trees in applications:
1. **Input Validation**: Sanitize inputs to prevent injection attacks (e.g., SQL injection in database-backed trees).
2. **Access Control**: Ensure users can only access authorized parts of the tree (e.g., restrict access to certain file system directories).
3. **Data Integrity**: Use transactions in databases to ensure tree modifications (insert/delete) are atomic.
4. **Recursion Limits**: Prevent stack overflow in recursive tree operations by setting recursion limits or using iterative approaches.
5. **Encryption**: If sensitive data is stored in the tree (e.g., employee data), encrypt it at rest and in transit.
6. **Denial-of-Service (DoS)**: Limit tree depth or size to prevent maliciously large trees from consuming resources.

---

### **11. Additional Notes**

- **Built-in Modules**: Python’s `collections.defaultdict` or `list` is sufficient for most tree implementations. For advanced use cases, libraries like `anytree` or `treelib` provide additional functionality.
- **Thread Safety**: If used in multi-threaded applications, use locks to prevent race conditions during tree modifications.
- **Serialization**: Trees can be serialized to JSON or other formats for storage or transmission.

---

### **Summary**

Trees are powerful for hierarchical data but require careful design for performance and security. They shine in applications like file systems, databases, and AI but are overkill for simple or non-hierarchical data. The provided examples demonstrate practical implementations, and Big-O analysis helps understand performance trade-offs. When used with databases, trees enable efficient storage and querying, but security measures are critical to prevent vulnerabilities.

Let me know if you'd like a deeper dive into any specific aspect, like advanced tree types (e.g., AVL, B-trees) or specific use cases!

### **Implementation Tips (Continued)**

1. **Choose the Right Type**
   - Use **Binary Search Tree** for simple sorted data with occasional modifications
   - Use **AVL Tree** when you need guaranteed O(log n) operations
   - Use **B-Tree** for database applications or when dealing with disk storage
   - Use **Trie** for string-based operations and prefix matching

2. **Memory Management**
   - Implement proper cleanup to avoid memory leaks
   - Use weak references where appropriate to prevent circular references
   - Consider using object pools for frequently created/destroyed nodes

3. **Threading Considerations**
   - Trees are not thread-safe by default
   - Use locks for concurrent access or implement lock-free algorithms
   - Consider using immutable trees for multi-threaded scenarios

### **Performance Optimization Strategies**

1. **Balancing**
   - Implement self-balancing mechanisms (AVL, Red-Black)
   - Periodic rebalancing for frequently modified trees
   - Monitor tree height and trigger rebalancing when needed

2. **Caching**
   - Cache frequently accessed nodes
   - Implement LRU cache for tree traversal results
   - Store computed properties (height, size) in nodes

3. **Iterative vs Recursive**
   - Use iterative approaches for deep trees to avoid stack overflow
   - Recursive solutions are cleaner but have overhead
   - Consider tail recursion optimization

### **Advanced Tree Implementations**### **Error Handling and Robustness**

1. **Input Validation**
   - Check for null/None values
   - Validate data types
   - Handle edge cases (empty trees, single nodes)

2. **Exception Handling**
   - Custom exception classes for tree operations
   - Graceful degradation on errors
   - Logging for debugging

3. **Memory Management**
   - Implement proper cleanup methods
   - Use weak references to prevent cycles
   - Monitor memory usage for large trees

### **Testing Strategies**

1. **Unit Testing**
   - Test individual operations (insert, delete, search)
   - Test edge cases (empty tree, single node)
   - Test balancing operations

2. **Performance Testing**
   - Benchmark different tree types
   - Test with various data sizes
   - Compare with alternative data structures

3. **Integration Testing**
   - Test database integration
   - Test with concurrent access
   - Test serialization/deserialization

### **Best Practices for Production Use**

1. **Configuration Management**
   - Configurable tree parameters (max depth, node limits)
   - Environment-specific settings
   - Feature flags for experimental features

2. **Monitoring and Metrics**
   - Track tree height and balance
   - Monitor operation performance
   - Alert on unusual patterns

3. **Documentation**
   - Clear API documentation
   - Usage examples
   - Performance characteristics

4. **Version Control**
   - Track tree structure changes
   - Implement migration strategies
   - Maintain backward compatibility

### **Common Pitfalls to Avoid**

1. **Unbalanced Trees** - Can degrade to O(n) performance
2. **Memory Leaks** - Failing to clean up node references
3. **Stack Overflow** - Deep recursion in unbalanced trees
4. **Concurrency Issues** - Race conditions in multi-threaded access
5. **Input Validation** - Not sanitizing user input
6. **Infinite Loops** - Circular references in tree structure

### **Integration with Modern Python Features**

1. **Type Hints** - Use typing module for better code clarity
2. **Dataclasses** - Simplify node definitions
3. **Context Managers** - Proper resource management
4. **Asyncio** - Asynchronous tree operations
5. **Generators** - Memory-efficient traversals

### **Database-Specific Considerations**

1. **ORM Integration**
   - SQLAlchemy models for tree structures
   - Django MPTT for hierarchical data
   - Proper foreign key relationships

2. **Query Optimization**
   - Use recursive CTEs for tree queries
   - Implement proper indexing strategies
   - Consider materialized path approach

3. **Caching Strategies**
   - Cache subtrees for frequent access
   - Use Redis for distributed caching
   - Implement cache invalidation

### **Conclusion**

Trees are powerful data structures that provide efficient operations for hierarchical data. The choice of tree type depends on your specific requirements:

- **Use Binary Search Trees** for simple sorted data
- **Use AVL/Red-Black Trees** for guaranteed performance
- **Use B-Trees** for database applications
- **Use Tries** for string operations
- **Use Segment Trees** for range queries

Remember to consider security, performance, and maintainability when implementing trees in production systems. Always validate inputs, implement proper error handling, and choose the right tree type for your use case.

The provided code examples demonstrate various tree implementations with practical applications, database integration, and security considerations. You can extend these implementations based on your specific requirements and constraints.

"""
Complete Tree Data Structure Implementation in Python
Covers: Binary Trees, Binary Search Trees, AVL Trees, and practical applications
"""

import json
import sqlite3
from typing import Optional, List, Any, Dict
from collections import deque
import hashlib

# =============================================================================
# 1. BASIC BINARY TREE IMPLEMENTATION
# =============================================================================

class TreeNode:
    """Basic tree node for binary tree operations"""
    def __init__(self, val: Any = 0, left: Optional['TreeNode'] = None, right: Optional['TreeNode'] = None):
        self.val = val
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f"TreeNode({self.val})"

class BinaryTree:
    """Basic Binary Tree implementation with common operations"""
    
    def __init__(self, root: Optional[TreeNode] = None):
        self.root = root
    
    def insert_level_order(self, values: List[Any]) -> None:
        """Insert values in level order (breadth-first)"""
        if not values:
            return
        
        self.root = TreeNode(values[0])
        queue = deque([self.root])
        i = 1
        
        while queue and i < len(values):
            node = queue.popleft()
            
            if i < len(values) and values[i] is not None:
                node.left = TreeNode(values[i])
                queue.append(node.left)
            i += 1
            
            if i < len(values) and values[i] is not None:
                node.right = TreeNode(values[i])
                queue.append(node.right)
            i += 1
    
    def inorder_traversal(self, node: Optional[TreeNode] = None) -> List[Any]:
        """Inorder traversal: Left -> Root -> Right"""
        if node is None:
            node = self.root
        
        result = []
        if node:
            result.extend(self.inorder_traversal(node.left))
            result.append(node.val)
            result.extend(self.inorder_traversal(node.right))
        return result
    
    def preorder_traversal(self, node: Optional[TreeNode] = None) -> List[Any]:
        """Preorder traversal: Root -> Left -> Right"""
        if node is None:
            node = self.root
        
        result = []
        if node:
            result.append(node.val)
            result.extend(self.preorder_traversal(node.left))
            result.extend(self.preorder_traversal(node.right))
        return result
    
    def postorder_traversal(self, node: Optional[TreeNode] = None) -> List[Any]:
        """Postorder traversal: Left -> Right -> Root"""
        if node is None:
            node = self.root
        
        result = []
        if node:
            result.extend(self.postorder_traversal(node.left))
            result.extend(self.postorder_traversal(node.right))
            result.append(node.val)
        return result
    
    def level_order_traversal(self) -> List[List[Any]]:
        """Level order traversal (breadth-first)"""
        if not self.root:
            return []
        
        result = []
        queue = deque([self.root])
        
        while queue:
            level_size = len(queue)
            level = []
            
            for _ in range(level_size):
                node = queue.popleft()
                level.append(node.val)
                
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
            
            result.append(level)
        
        return result
    
    def height(self, node: Optional[TreeNode] = None) -> int:
        """Calculate height of tree"""
        if node is None:
            node = self.root
        
        if not node:
            return 0
        
        return 1 + max(self.height(node.left), self.height(node.right))
    
    def size(self, node: Optional[TreeNode] = None) -> int:
        """Count total nodes in tree"""
        if node is None:
            node = self.root
        
        if not node:
            return 0
        
        return 1 + self.size(node.left) + self.size(node.right)

# =============================================================================
# 2. BINARY SEARCH TREE (BST) IMPLEMENTATION
# =============================================================================

class BSTNode:
    """Node for Binary Search Tree"""
    def __init__(self, val: Any):
        self.val = val
        self.left: Optional['BSTNode'] = None
        self.right: Optional['BSTNode'] = None
    
    def __repr__(self):
        return f"BSTNode({self.val})"

class BinarySearchTree:
    """Binary Search Tree with standard operations"""
    
    def __init__(self):
        self.root: Optional[BSTNode] = None
    
    def insert(self, val: Any) -> None:
        """Insert a value into BST"""
        self.root = self._insert_recursive(self.root, val)
    
    def _insert_recursive(self, node: Optional[BSTNode], val: Any) -> BSTNode:
        """Helper method for recursive insertion"""
        if not node:
            return BSTNode(val)
        
        if val < node.val:
            node.left = self._insert_recursive(node.left, val)
        elif val > node.val:
            node.right = self._insert_recursive(node.right, val)
        
        return node
    
    def search(self, val: Any) -> bool:
        """Search for a value in BST"""
        return self._search_recursive(self.root, val)
    
    def _search_recursive(self, node: Optional[BSTNode], val: Any) -> bool:
        """Helper method for recursive search"""
        if not node:
            return False
        
        if val == node.val:
            return True
        elif val < node.val:
            return self._search_recursive(node.left, val)
        else:
            return self._search_recursive(node.right, val)
    
    def delete(self, val: Any) -> None:
        """Delete a value from BST"""
        self.root = self._delete_recursive(self.root, val)
    
    def _delete_recursive(self, node: Optional[BSTNode], val: Any) -> Optional[BSTNode]:
        """Helper method for recursive deletion"""
        if not node:
            return None
        
        if val < node.val:
            node.left = self._delete_recursive(node.left, val)
        elif val > node.val:
            node.right = self._delete_recursive(node.right, val)
        else:
            # Node to be deleted found
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            
            # Node with two children
            min_node = self._find_min(node.right)
            node.val = min_node.val
            node.right = self._delete_recursive(node.right, min_node.val)
        
        return node
    
    def _find_min(self, node: BSTNode) -> BSTNode:
        """Find minimum value node in subtree"""
        while node.left:
            node = node.left
        return node
    
    def inorder(self) -> List[Any]:
        """Inorder traversal (sorted order for BST)"""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node: Optional[BSTNode], result: List[Any]) -> None:
        """Helper method for inorder traversal"""
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.val)
            self._inorder_recursive(node.right, result)

# =============================================================================
# 3. AVL TREE (SELF-BALANCING BST) IMPLEMENTATION
# =============================================================================

class AVLNode:
    """Node for AVL Tree"""
    def __init__(self, val: Any):
        self.val = val
        self.left: Optional['AVLNode'] = None
        self.right: Optional['AVLNode'] = None
        self.height = 1

class AVLTree:
    """Self-balancing Binary Search Tree (AVL Tree)"""
    
    def __init__(self):
        self.root: Optional[AVLNode] = None
    
    def _get_height(self, node: Optional[AVLNode]) -> int:
        """Get height of node"""
        if not node:
            return 0
        return node.height
    
    def _get_balance(self, node: Optional[AVLNode]) -> int:
        """Get balance factor of node"""
        if not node:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)
    
    def _rotate_right(self, y: AVLNode) -> AVLNode:
        """Right rotation"""
        x = y.left
        T2 = x.right
        
        # Perform rotation
        x.right = y
        y.left = T2
        
        # Update heights
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        
        return x
    
    def _rotate_left(self, x: AVLNode) -> AVLNode:
        """Left rotation"""
        y = x.right
        T2 = y.left
        
        # Perform rotation
        y.left = x
        x.right = T2
        
        # Update heights
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        
        return y
    
    def insert(self, val: Any) -> None:
        """Insert value into AVL tree"""
        self.root = self._insert_recursive(self.root, val)
    
    def _insert_recursive(self, node: Optional[AVLNode], val: Any) -> AVLNode:
        """Helper method for recursive insertion with balancing"""
        # Standard BST insertion
        if not node:
            return AVLNode(val)
        
        if val < node.val:
            node.left = self._insert_recursive(node.left, val)
        elif val > node.val:
            node.right = self._insert_recursive(node.right, val)
        else:
            return node  # Duplicate values not allowed
        
        # Update height
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        
        # Get balance factor
        balance = self._get_balance(node)
        
        # Left Left Case
        if balance > 1 and val < node.left.val:
            return self._rotate_right(node)
        
        # Right Right Case
        if balance < -1 and val > node.right.val:
            return self._rotate_left(node)
        
        # Left Right Case
        if balance > 1 and val > node.left.val:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        
        # Right Left Case
        if balance < -1 and val < node.right.val:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        
        return node

# =============================================================================
# 4. REAL-WORLD APPLICATIONS
# =============================================================================

class FileSystemTree:
    """File system representation using tree structure"""
    
    def __init__(self, name: str, is_file: bool = False):
        self.name = name
        self.is_file = is_file
        self.children: Dict[str, 'FileSystemTree'] = {}
        self.parent: Optional['FileSystemTree'] = None
    
    def add_child(self, name: str, is_file: bool = False) -> 'FileSystemTree':
        """Add a child node (file or directory)"""
        child = FileSystemTree(name, is_file)
        child.parent = self
        self.children[name] = child
        return child
    
    def get_full_path(self) -> str:
        """Get full path from root"""
        if self.parent is None:
            return self.name
        return self.parent.get_full_path() + "/" + self.name
    
    def find(self, name: str) -> Optional['FileSystemTree']:
        """Find a file or directory by name"""
        if self.name == name:
            return self
        
        for child in self.children.values():
            result = child.find(name)
            if result:
                return result
        
        return None
    
    def list_files(self, extension: str = None) -> List[str]:
        """List all files, optionally filtered by extension"""
        files = []
        
        if self.is_file:
            if extension is None or self.name.endswith(extension):
                files.append(self.get_full_path())
        
        for child in self.children.values():
            files.extend(child.list_files(extension))
        
        return files

class ExpressionTree:
    """Expression tree for mathematical expressions"""
    
    def __init__(self, value: str):
        self.value = value
        self.left: Optional['ExpressionTree'] = None
        self.right: Optional['ExpressionTree'] = None
    
    def evaluate(self) -> float:
        """Evaluate the expression tree"""
        if self.value.isdigit() or (self.value[0] == '-' and self.value[1:].isdigit()):
            return float(self.value)
        
        if self.left and self.right:
            left_val = self.left.evaluate()
            right_val = self.right.evaluate()
            
            if self.value == '+':
                return left_val + right_val
            elif self.value == '-':
                return left_val - right_val
            elif self.value == '*':
                return left_val * right_val
            elif self.value == '/':
                if right_val == 0:
                    raise ValueError("Division by zero")
                return left_val / right_val
        
        raise ValueError(f"Invalid expression: {self.value}")
    
    def to_string(self) -> str:
        """Convert expression tree to string"""
        if not self.left and not self.right:
            return self.value
        
        left_str = self.left.to_string() if self.left else ""
        right_str = self.right.to_string() if self.right else ""
        
        return f"({left_str} {self.value} {right_str})"

# =============================================================================
# 5. DATABASE INTEGRATION
# =============================================================================

class TreeDatabase:
    """Database integration for tree structures"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.setup_tables()
    
    def setup_tables(self):
        """Create necessary tables for tree storage"""
        cursor = self.conn.cursor()
        
        # Table for storing tree nodes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tree_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tree_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                parent_id TEXT,
                value TEXT NOT NULL,
                node_type TEXT DEFAULT 'internal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tree_id, node_id)
            )
        ''')
        
        # Index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tree_parent 
            ON tree_nodes(tree_id, parent_id)
        ''')
        
        self.conn.commit()
    
    def save_tree(self, tree: BinaryTree, tree_id: str) -> None:
        """Save binary tree to database"""
        cursor = self.conn.cursor()
        
        # Clear existing tree data
        cursor.execute('DELETE FROM tree_nodes WHERE tree_id = ?', (tree_id,))
        
        # Save tree nodes
        if tree.root:
            self._save_node_recursive(tree.root, tree_id, "root", None)
        
        self.conn.commit()
    
    def _save_node_recursive(self, node: TreeNode, tree_id: str, node_id: str, parent_id: Optional[str]):
        """Recursively save tree nodes"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO tree_nodes (tree_id, node_id, parent_id, value)
            VALUES (?, ?, ?, ?)
        ''', (tree_id, node_id, parent_id, str(node.val)))
        
        if node.left:
            self._save_node_recursive(node.left, tree_id, f"{node_id}_L", node_id)
        
        if node.right:
            self._save_node_recursive(node.right, tree_id, f"{node_id}_R", node_id)
    
    def load_tree(self, tree_id: str) -> Optional[BinaryTree]:
        """Load binary tree from database"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT node_id, parent_id, value 
            FROM tree_nodes 
            WHERE tree_id = ? 
            ORDER BY node_id
        ''', (tree_id,))
        
        rows = cursor.fetchall()
        if not rows:
            return None
        
        # Build tree from database records
        nodes = {}
        root_node = None
        
        for node_id, parent_id, value in rows:
            node = TreeNode(value)
            nodes[node_id] = node
            
            if parent_id is None:
                root_node = node
            else:
                parent = nodes.get(parent_id)
                if parent:
                    if node_id.endswith('_L'):
                        parent.left = node
                    elif node_id.endswith('_R'):
                        parent.right = node
        
        return BinaryTree(root_node)
    
    def get_tree_statistics(self, tree_id: str) -> Dict[str, Any]:
        """Get statistics for a stored tree"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as node_count,
                   MAX(LENGTH(node_id) - LENGTH(REPLACE(node_id, '_', ''))) as max_depth
            FROM tree_nodes 
            WHERE tree_id = ?
        ''', (tree_id,))
        
        row = cursor.fetchone()
        return {
            'node_count': row[0] if row else 0,
            'estimated_depth': row[1] if row else 0
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()

# =============================================================================
# 6. SECURITY AND VALIDATION
# =============================================================================

class SecureTree:
    """Tree with security features and validation"""
    
    def __init__(self, max_depth: int = 100, max_nodes: int = 10000):
        self.root: Optional[TreeNode] = None
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.node_count = 0
    
    def validate_input(self, value: Any) -> bool:
        """Validate input value"""
        if value is None:
            return False
        
        # Check for potential injection attacks
        if isinstance(value, str):
            dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript']
            value_lower = value.lower()
            for char in dangerous_chars:
                if char in value_lower:
                    return False
        
        return True
    
    def safe_insert(self, value: Any) -> bool:
        """Safely insert value with validation"""
        if not self.validate_input(value):
            return False
        
        if self.node_count >= self.max_nodes:
            return False
        
        # Check depth before insertion
        if self.root and self._get_depth(self.root) >= self.max_depth:
            return False
        
        self.root = self._safe_insert_recursive(self.root, value, 0)
        return True
    
    def _safe_insert_recursive(self, node: Optional[TreeNode], value: Any, depth: int) -> TreeNode:
        """Safely insert with depth checking"""
        if depth > self.max_depth:
            raise ValueError(f"Maximum depth exceeded: {self.max_depth}")
        
        if not node:
            self.node_count += 1
            return TreeNode(value)
        
        # Simple insertion logic (can be customized)
        if value < node.val:
            node.left = self._safe_insert_recursive(node.left, value, depth + 1)
        else:
            node.right = self._safe_insert_recursive(node.right, value, depth + 1)
        
        return node
    
    def _get_depth(self, node: Optional[TreeNode]) -> int:
        """Calculate maximum depth of tree"""
        if not node:
            return 0
        return 1 + max(self._get_depth(node.left), self._get_depth(node.right))
    
    def get_hash(self) -> str:
        """Generate hash of tree structure for integrity checking"""
        tree_string = self._serialize_tree(self.root)
        return hashlib.sha256(tree_string.encode()).hexdigest()
    
    def _serialize_tree(self, node: Optional[TreeNode]) -> str:
        """Serialize tree for hashing"""
        if not node:
            return "null"
        
        left_str = self._serialize_tree(node.left)
        right_str = self._serialize_tree(node.right)
        
        return f"{node.val}({left_str},{right_str})"

# =============================================================================
# 7. PERFORMANCE TESTING AND UTILITIES
# =============================================================================

def performance_test():
    """Test performance of different tree implementations"""
    import time
    import random
    
    # Test data
    test_data = [random.randint(1, 10000) for _ in range(1000)]
    
    # Test BST
    print("Testing Binary Search Tree...")
    bst = BinarySearchTree()
    
    start_time = time.time()
    for val in test_data:
        bst.insert(val)
    insert_time = time.time() - start_time
    
    start_time = time.time()
    for val in test_data[:100]:
        bst.search(val)
    search_time = time.time() - start_time
    
    print(f"BST Insert time: {insert_time:.4f}s")
    print(f"BST Search time: {search_time:.4f}s")
    
    # Test AVL Tree
    print("\nTesting AVL Tree...")
    avl = AVLTree()
    
    start_time = time.time()
    for val in test_data:
        avl.insert(val)
    avl_insert_time = time.time() - start_time
    
    print(f"AVL Insert time: {avl_insert_time:.4f}s")
    
    return {
        'bst_insert': insert_time,
        'bst_search': search_time,
        'avl_insert': avl_insert_time
    }

# =============================================================================
# 8. ADVANCED TREE IMPLEMENTATIONS
# =============================================================================

class RedBlackNode:
    """Node for Red-Black Tree"""
    def __init__(self, val: Any, color: str = 'RED'):
        self.val = val
        self.color = color  # 'RED' or 'BLACK'
        self.left: Optional['RedBlackNode'] = None
        self.right: Optional['RedBlackNode'] = None
        self.parent: Optional['RedBlackNode'] = None

class RedBlackTree:
    """Red-Black Tree implementation for guaranteed O(log n) operations"""
    
    def __init__(self):
        self.NIL = RedBlackNode(None, 'BLACK')  # Sentinel node
        self.root = self.NIL
    
    def insert(self, val: Any) -> None:
        """Insert value maintaining Red-Black properties"""
        node = RedBlackNode(val)
        node.left = self.NIL
        node.right = self.NIL
        
        parent = None
        current = self.root
        
        while current != self.NIL:
            parent = current
            if val < current.val:
                current = current.left
            else:
                current = current.right
        
        node.parent = parent
        
        if parent is None:
            self.root = node
        elif val < parent.val:
            parent.left = node
        else:
            parent.right = node
        
        node.color = 'RED'
        self._fix_insert(node)
    
    def _fix_insert(self, node: RedBlackNode) -> None:
        """Fix Red-Black tree violations after insertion"""
        while node != self.root and node.parent.color == 'RED':
            if node.parent == node.parent.parent.left:
                uncle = node.parent.parent.right
                
                if uncle.color == 'RED':
                    node.parent.color = 'BLACK'
                    uncle.color = 'BLACK'
                    node.parent.parent.color = 'RED'
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self._left_rotate(node)
                    
                    node.parent.color = 'BLACK'
                    node.parent.parent.color = 'RED'
                    self._right_rotate(node.parent.parent)
            else:
                uncle = node.parent.parent.left
                
                if uncle.color == 'RED':
                    node.parent.color = 'BLACK'
                    uncle.color = 'BLACK'
                    node.parent.parent.color = 'RED'
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self._right_rotate(node)
                    
                    node.parent.color = 'BLACK'
                    node.parent.parent.color = 'RED'
                    self._left_rotate(node.parent.parent)
        
        self.root.color = 'BLACK'
    
    def _left_rotate(self, x: RedBlackNode) -> None:
        """Perform left rotation"""
        y = x.right
        x.right = y.left
        
        if y.left != self.NIL:
            y.left.parent = x
        
        y.parent = x.parent
        
        if x.parent is None:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        
        y.left = x
        x.parent = y
    
    def _right_rotate(self, x: RedBlackNode) -> None:
        """Perform right rotation"""
        y = x.left
        x.left = y.right
        
        if y.right != self.NIL:
            y.right.parent = x
        
        y.parent = x.parent
        
        if x.parent is None:
            self.root = y
        elif x == x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        
        y.right = x
        x.parent = y

class TrieNode:
    """Node for Trie (Prefix Tree)"""
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end_word = False
        self.word_count = 0

class Trie:
    """Trie implementation for efficient string operations"""
    
    def __init__(self):
        self.root = TrieNode()
        self.total_words = 0
    
    def insert(self, word: str) -> None:
        """Insert word into trie"""
        node = self.root
        
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        if not node.is_end_word:
            self.total_words += 1
        
        node.is_end_word = True
        node.word_count += 1
    
    def search(self, word: str) -> bool:
        """Search for complete word in trie"""
        node = self._find_node(word)
        return node is not None and node.is_end_word
    
    def starts_with(self, prefix: str) -> bool:
        """Check if any word starts with given prefix"""
        return self._find_node(prefix) is not None
    
    def _find_node(self, word: str) -> Optional[TrieNode]:
        """Find node for given word/prefix"""
        node = self.root
        
        for char in word:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node
    
    def get_words_with_prefix(self, prefix: str) -> List[str]:
        """Get all words with given prefix"""
        node = self._find_node(prefix)
        if not node:
            return []
        
        words = []
        self._collect_words(node, prefix, words)
        return words
    
    def _collect_words(self, node: TrieNode, prefix: str, words: List[str]) -> None:
        """Collect all words from given node"""
        if node.is_end_word:
            words.append(prefix)
        
        for char, child in node.children.items():
            self._collect_words(child, prefix + char, words)
    
    def auto_complete(self, prefix: str, max_suggestions: int = 10) -> List[str]:
        """Get auto-complete suggestions"""
        suggestions = self.get_words_with_prefix(prefix)
        return suggestions[:max_suggestions]

class SegmentTree:
    """Segment Tree for range queries"""
    
    def __init__(self, arr: List[int]):
        self.n = len(arr)
        self.tree = [0] * (4 * self.n)
        self.arr = arr[:]
        self._build(1, 0, self.n - 1)
    
    def _build(self, node: int, start: int, end: int) -> None:
        """Build segment tree"""
        if start == end:
            self.tree[node] = self.arr[start]
        else:
            mid = (start + end) // 2
            self._build(2 * node, start, mid)
            self._build(2 * node + 1, mid + 1, end)
            self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]
    
    def update(self, idx: int, val: int) -> None:
        """Update value at index"""
        self._update(1, 0, self.n - 1, idx, val)
    
    def _update(self, node: int, start: int, end: int, idx: int, val: int) -> None:
        """Update segment tree"""
        if start == end:
            self.tree[node] = val
            self.arr[idx] = val
        else:
            mid = (start + end) // 2
            if idx <= mid:
                self._update(2 * node, start, mid, idx, val)
            else:
                self._update(2 * node + 1, mid + 1, end, idx, val)
            self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]
    
    def query(self, left: int, right: int) -> int:
        """Query sum in range [left, right]"""
        return self._query(1, 0, self.n - 1, left, right)
    
    def _query(self, node: int, start: int, end: int, left: int, right: int) -> int:
        """Query segment tree"""
        if right < start or end < left:
            return 0
        
        if left <= start and end <= right:
            return self.tree[node]
        
        mid = (start + end) // 2
        left_sum = self._query(2 * node, start, mid, left, right)
        right_sum = self._query(2 * node + 1, mid + 1, end, left, right)
        
        return left_sum + right_sum

class BTree:
    """B-Tree implementation for database-like operations"""
    
    def __init__(self, degree: int = 3):
        self.degree = degree
        self.root: Optional['BTreeNode'] = None
    
    def insert(self, key: Any) -> None:
        """Insert key into B-tree"""
        if self.root is None:
            self.root = BTreeNode(self.degree, True)
            self.root.keys.append(key)
        else:
            if len(self.root.keys) == (2 * self.degree) - 1:
                new_root = BTreeNode(self.degree, False)
                new_root.children.append(self.root)
                self._split_child(new_root, 0)
                self.root = new_root
            
            self._insert_non_full(self.root, key)
    
    def _insert_non_full(self, node: 'BTreeNode', key: Any) -> None:
        """Insert into non-full node"""
        i = len(node.keys) - 1
        
        if node.is_leaf:
            node.keys.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            if len(node.children[i].keys) == (2 * self.degree) - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], key)
    
    def _split_child(self, parent: 'BTreeNode', index: int) -> None:
        """Split child node"""
        degree = self.degree
        full_child = parent.children[index]
        new_child = BTreeNode(degree, full_child.is_leaf)
        
        parent.children.insert(index + 1, new_child)
        parent.keys.insert(index, full_child.keys[degree - 1])
        
        new_child.keys = full_child.keys[degree:]
        full_child.keys = full_child.keys[:degree - 1]
        
        if not full_child.is_leaf:
            new_child.children = full_child.children[degree:]
            full_child.children = full_child.children[:degree]
    
    def search(self, key: Any) -> bool:
        """Search for key in B-tree"""
        return self._search(self.root, key) is not None
    
    def _search(self, node: Optional['BTreeNode'], key: Any) -> Optional['BTreeNode']:
        """Search helper method"""
        if node is None:
            return None
        
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if i < len(node.keys) and key == node.keys[i]:
            return node
        
        if node.is_leaf:
            return None
        
        return self._search(node.children[i], key)

class BTreeNode:
    """Node for B-Tree"""
    def __init__(self, degree: int, is_leaf: bool):
        self.keys: List[Any] = []
        self.children: List['BTreeNode'] = []
        self.is_leaf = is_leaf
        self.degree = degree

# =============================================================================
# 9. SPECIALIZED TREE APPLICATIONS
# =============================================================================

class DecisionTree:
    """Simple decision tree for classification"""
    
    def __init__(self, feature: str = None, threshold: Any = None):
        self.feature = feature
        self.threshold = threshold
        self.left: Optional['DecisionTree'] = None
        self.right: Optional['DecisionTree'] = None
        self.prediction: Any = None
    
    def predict(self, sample: Dict[str, Any]) -> Any:
        """Make prediction for given sample"""
        if self.prediction is not None:
            return self.prediction
        
        if sample[self.feature] <= self.threshold:
            return self.left.predict(sample)
        else:
            return self.right.predict(sample)
    
    def is_leaf(self) -> bool:
        """Check if node is leaf"""
        return self.prediction is not None

class SuffixTree:
    """Suffix tree for string processing"""
    
    def __init__(self, text: str):
        self.text = text
        self.root = {}
        self._build_suffix_tree()
    
    def _build_suffix_tree(self) -> None:
        """Build suffix tree from text"""
        for i in range(len(self.text)):
            self._insert_suffix(self.text[i:], i)
    
    def _insert_suffix(self, suffix: str, start_index: int) -> None:
        """Insert suffix into tree"""
        node = self.root
        
        for char in suffix:
            if char not in node:
                node[char] = {}
            node = node[char]
        
        node['

def demonstrate_trees():
    """Demonstrate various tree operations"""
    print("=== TREE DEMONSTRATION ===\n")
    
    # 1. Basic Binary Tree
    print("1. Basic Binary Tree:")
    bt = BinaryTree()
    bt.insert_level_order([1, 2, 3, 4, 5, 6, 7])
    print(f"Level order: {bt.level_order_traversal()}")
    print(f"Inorder: {bt.inorder_traversal()}")
    print(f"Height: {bt.height()}")
    print(f"Size: {bt.size()}\n")
    
    # 2. Binary Search Tree
    print("2. Binary Search Tree:")
    bst = BinarySearchTree()
    values = [50, 30, 70, 20, 40, 60, 80]
    for val in values:
        bst.insert(val)
    
    print(f"Inorder (sorted): {bst.inorder()}")
    print(f"Search 40: {bst.search(40)}")
    print(f"Search 90: {bst.search(90)}")
    bst.delete(30)
    print(f"After deleting 30: {bst.inorder()}\n")
    
    # 3. File System Tree
    print("3. File System Tree:")
    root = FileSystemTree("root")
    home = root.add_child("home")
    user = home.add_child("user")
    user.add_child("document.txt", True)
    user.add_child("photo.jpg", True)
    
    docs = user.add_child("documents")
    docs.add_child("report.pdf", True)
    
    print(f"All files: {root.list_files()}")
    print(f"Text files: {root.list_files('.txt')}")
    found = root.find("photo.jpg")
    print(f"Found photo.jpg at: {found.get_full_path() if found else 'Not found'}\n")
    
    # 4. Expression Tree
    print("4. Expression Tree:")
    # Create expression tree for: (3 + 4) * 2
    expr = ExpressionTree('*')
    expr.left = ExpressionTree('+')
    expr.left.left = ExpressionTree('3')
    expr.left.right = ExpressionTree('4')
    expr.right = ExpressionTree('2')
    
    print(f"Expression: {expr.to_string()}")
    print(f"Result: {expr.evaluate()}\n")
    
    # 5. Database Integration
    print("5. Database Integration:")
    db = TreeDatabase()
    db.save_tree(bt, "sample_tree")
    
    stats = db.get_tree_statistics("sample_tree")
    print(f"Tree statistics: {stats}")
    
    loaded_tree = db.load_tree("sample_tree")
    if loaded_tree:
        print(f"Loaded tree inorder: {loaded_tree.inorder_traversal()}")
    
    db.close()
    
    # 6. Security Features
    print("\n6. Security Features:")
    secure_tree = SecureTree(max_depth=5, max_nodes=10)
    
    print(f"Insert 5: {secure_tree.safe_insert(5)}")
    print(f"Insert malicious '<script>': {secure_tree.safe_insert('<script>')}")
    print(f"Tree hash: {secure_tree.get_hash()[:16]}...")

if __name__ == "__main__":
    demonstrate_trees()
    print("\n=== PERFORMANCE TEST ===")
    performance_test()
] = start_index  # End marker with position
    
    def search_pattern(self, pattern: str) -> List[int]:
        """Find all occurrences of pattern"""
        node = self.root
        
        # Navigate to pattern
        for char in pattern:
            if char not in node:
                return []
            node = node[char]
        
        # Collect all positions
        positions = []
        self._collect_positions(node, positions)
        return sorted(positions)
    
    def _collect_positions(self, node: Dict, positions: List[int]) -> None:
        """Collect all positions from subtree"""
        for key, value in node.items():
            if key == '

def demonstrate_trees():
    """Demonstrate various tree operations"""
    print("=== TREE DEMONSTRATION ===\n")
    
    # 1. Basic Binary Tree
    print("1. Basic Binary Tree:")
    bt = BinaryTree()
    bt.insert_level_order([1, 2, 3, 4, 5, 6, 7])
    print(f"Level order: {bt.level_order_traversal()}")
    print(f"Inorder: {bt.inorder_traversal()}")
    print(f"Height: {bt.height()}")
    print(f"Size: {bt.size()}\n")
    
    # 2. Binary Search Tree
    print("2. Binary Search Tree:")
    bst = BinarySearchTree()
    values = [50, 30, 70, 20, 40, 60, 80]
    for val in values:
        bst.insert(val)
    
    print(f"Inorder (sorted): {bst.inorder()}")
    print(f"Search 40: {bst.search(40)}")
    print(f"Search 90: {bst.search(90)}")
    bst.delete(30)
    print(f"After deleting 30: {bst.inorder()}\n")
    
    # 3. File System Tree
    print("3. File System Tree:")
    root = FileSystemTree("root")
    home = root.add_child("home")
    user = home.add_child("user")
    user.add_child("document.txt", True)
    user.add_child("photo.jpg", True)
    
    docs = user.add_child("documents")
    docs.add_child("report.pdf", True)
    
    print(f"All files: {root.list_files()}")
    print(f"Text files: {root.list_files('.txt')}")
    found = root.find("photo.jpg")
    print(f"Found photo.jpg at: {found.get_full_path() if found else 'Not found'}\n")
    
    # 4. Expression Tree
    print("4. Expression Tree:")
    # Create expression tree for: (3 + 4) * 2
    expr = ExpressionTree('*')
    expr.left = ExpressionTree('+')
    expr.left.left = ExpressionTree('3')
    expr.left.right = ExpressionTree('4')
    expr.right = ExpressionTree('2')
    
    print(f"Expression: {expr.to_string()}")
    print(f"Result: {expr.evaluate()}\n")
    
    # 5. Database Integration
    print("5. Database Integration:")
    db = TreeDatabase()
    db.save_tree(bt, "sample_tree")
    
    stats = db.get_tree_statistics("sample_tree")
    print(f"Tree statistics: {stats}")
    
    loaded_tree = db.load_tree("sample_tree")
    if loaded_tree:
        print(f"Loaded tree inorder: {loaded_tree.inorder_traversal()}")
    
    db.close()
    
    # 6. Security Features
    print("\n6. Security Features:")
    secure_tree = SecureTree(max_depth=5, max_nodes=10)
    
    print(f"Insert 5: {secure_tree.safe_insert(5)}")
    print(f"Insert malicious '<script>': {secure_tree.safe_insert('<script>')}")
    print(f"Tree hash: {secure_tree.get_hash()[:16]}...")

if __name__ == "__main__":
    demonstrate_trees()
    print("\n=== PERFORMANCE TEST ===")
    performance_test()
:
                positions.append(value)
            else:
                self._collect_positions(value, positions)

class ThreadedBinaryTree:
    """Threaded binary tree for efficient traversal"""
    
    def __init__(self, val: Any):
        self.val = val
        self.left: Optional['ThreadedBinaryTree'] = None
        self.right: Optional['ThreadedBinaryTree'] = None
        self.left_thread = False
        self.right_thread = False
    
    def insert(self, val: Any) -> None:
        """Insert value into threaded binary tree"""
        if val < self.val:
            if not self.left_thread:
                self.left.insert(val)
            else:
                new_node = ThreadedBinaryTree(val)
                new_node.left = self.left
                new_node.right = self
                new_node.left_thread = True
                new_node.right_thread = True
                self.left = new_node
                self.left_thread = False
        else:
            if not self.right_thread:
                self.right.insert(val)
            else:
                new_node = ThreadedBinaryTree(val)
                new_node.left = self
                new_node.right = self.right
                new_node.left_thread = True
                new_node.right_thread = True
                self.right = new_node
                self.right_thread = False
    
    def inorder_traversal(self) -> List[Any]:
        """Efficient inorder traversal using threads"""
        result = []
        current = self
        
        # Go to leftmost node
        while not current.left_thread:
            current = current.left
        
        while current:
            result.append(current.val)
            
            if current.right_thread:
                current = current.right
            else:
                current = current.right
                while not current.left_thread:
                    current = current.left
        
        return result

# =============================================================================
# 10. DEMONSTRATION AND EXAMPLES
# =============================================================================

def demonstrate_trees():
    """Demonstrate various tree operations"""
    print("=== TREE DEMONSTRATION ===\n")
    
    # 1. Basic Binary Tree
    print("1. Basic Binary Tree:")
    bt = BinaryTree()
    bt.insert_level_order([1, 2, 3, 4, 5, 6, 7])
    print(f"Level order: {bt.level_order_traversal()}")
    print(f"Inorder: {bt.inorder_traversal()}")
    print(f"Height: {bt.height()}")
    print(f"Size: {bt.size()}\n")
    
    # 2. Binary Search Tree
    print("2. Binary Search Tree:")
    bst = BinarySearchTree()
    values = [50, 30, 70, 20, 40, 60, 80]
    for val in values:
        bst.insert(val)
    
    print(f"Inorder (sorted): {bst.inorder()}")
    print(f"Search 40: {bst.search(40)}")
    print(f"Search 90: {bst.search(90)}")
    bst.delete(30)
    print(f"After deleting 30: {bst.inorder()}\n")
    
    # 3. File System Tree
    print("3. File System Tree:")
    root = FileSystemTree("root")
    home = root.add_child("home")
    user = home.add_child("user")
    user.add_child("document.txt", True)
    user.add_child("photo.jpg", True)
    
    docs = user.add_child("documents")
    docs.add_child("report.pdf", True)
    
    print(f"All files: {root.list_files()}")
    print(f"Text files: {root.list_files('.txt')}")
    found = root.find("photo.jpg")
    print(f"Found photo.jpg at: {found.get_full_path() if found else 'Not found'}\n")
    
    # 4. Expression Tree
    print("4. Expression Tree:")
    # Create expression tree for: (3 + 4) * 2
    expr = ExpressionTree('*')
    expr.left = ExpressionTree('+')
    expr.left.left = ExpressionTree('3')
    expr.left.right = ExpressionTree('4')
    expr.right = ExpressionTree('2')
    
    print(f"Expression: {expr.to_string()}")
    print(f"Result: {expr.evaluate()}\n")
    
    # 5. Database Integration
    print("5. Database Integration:")
    db = TreeDatabase()
    db.save_tree(bt, "sample_tree")
    
    stats = db.get_tree_statistics("sample_tree")
    print(f"Tree statistics: {stats}")
    
    loaded_tree = db.load_tree("sample_tree")
    if loaded_tree:
        print(f"Loaded tree inorder: {loaded_tree.inorder_traversal()}")
    
    db.close()
    
    # 6. Security Features
    print("\n6. Security Features:")
    secure_tree = SecureTree(max_depth=5, max_nodes=10)
    
    print(f"Insert 5: {secure_tree.safe_insert(5)}")
    print(f"Insert malicious '<script>': {secure_tree.safe_insert('<script>')}")
    print(f"Tree hash: {secure_tree.get_hash()[:16]}...")

if __name__ == "__main__":
    demonstrate_trees()
    print("\n=== PERFORMANCE TEST ===")
    performance_test()