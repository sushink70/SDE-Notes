# Trees: Structure, Internals, and Operations

## 1. What a tree is

A tree is a connected, acyclic graph. With N nodes it has exactly N-1 edges, and there is exactly one path between any two nodes. A rooted tree picks one node as the root and orients every edge away from it.

```
                 [A]              depth 0   (root)
               /  |  \
            [B]  [C]  [D]         depth 1
           /  \        |
         [E]  [F]     [G]         depth 2   (E, F, G are leaves)
               |
              [H]                 depth 3

Height of tree = longest root-to-leaf path = 3
```

| Term | Meaning |
|---|---|
| Root | Node with no parent (A) |
| Leaf | Node with no children (E, H, C, G) |
| Parent / child | Direct edge relationship (B is the parent of E and F) |
| Sibling | Same parent (E and F) |
| Ancestor / descendant | Anywhere on the path to or from the root |
| Depth of node | Edges from root to the node |
| Height of node | Edges from node down to its deepest leaf |
| Degree | Number of children of a node |
| Subtree | A node plus all its descendants |

The recursive definition is what drives most algorithms: a tree is either empty, or a node plus a set of child trees. Almost every tree algorithm falls out of this.

---

## 2. How trees live in memory

### 2.1 Pointer-based (linked) representation

Each node is a heap allocation holding data and pointers to its children.

```
Binary node layout on 64-bit (24 bytes, 8-byte aligned):

 offset  0        8        16       24
         +--------+--------+--------+
         |  key   |  left  | right  |
         +--------+--------+--------+

Heap (addresses scattered by the allocator):

 0x1000: [ 50 | 0x2400 | 0x1A80 ]
 0x2400: [ 30 | 0x3F10 | 0x0000 ]     0x0000 = null
 0x1A80: [ 70 | 0x0000 | 0x0000 ]
 0x3F10: [ 20 | 0x0000 | 0x0000 ]

Logical view:
        50
       /  \
     30    70
    /
  20
```

**What happens under the hood on access:** `node.left.key` means loading the pointer from `node+8`, then loading the key from that address. Each hop is a dependent load, so the CPU cannot prefetch the next address until the current load finishes. This is pointer chasing. If nodes are scattered across memory, nearly every hop is a cache miss (~100 ns to DRAM versus ~1 ns for L1). This is the main reason tree performance in practice is worse than the Big-O suggests, and why B-trees, arenas, and array layouts exist.

### 2.2 Array-based (implicit) representation

For complete binary trees, no pointers are needed. Position encodes structure.

```
Tree:            Array (0-indexed):
       10
      /  \        idx:  0   1   2   3   4   5
     20   30      val: [10, 20, 30, 40, 50, 60]
    /  \  /
   40 50 60

 parent(i) = (i - 1) / 2
 left(i)   = 2i + 1
 right(i)  = 2i + 2
```

Properties:
- Zero pointer overhead, contiguous memory, cache friendly.
- `parent`, `left` and `right` compile to shifts and adds (`2i+1` is `(i<<1)|1`).
- Wastes space if the tree isn't complete: a skewed tree of height h needs 2^h slots.

Used by binary heaps, segment trees, and Fenwick trees.

### 2.3 Arena / index-based representation

Nodes live in one `Vec`/slice, and "pointers" are integer indices.

```
nodes: [ {key:50, l:1, r:2}, {key:30, l:3, r:-1}, {key:70, l:-1, r:-1}, {key:20, l:-1, r:-1} ]
index:       0                     1                    2                      3
```

Benefits:
- 4-byte indices instead of 8-byte pointers, so more nodes per cache line.
- Allocation is one bump of `len`; deallocation is free (drop the whole arena).
- Go's GC has no per-node pointers to scan.
- In Rust it sidesteps ownership and borrow-checker fights for parent pointers and graphs.

This is the default choice for competitive programming.

### 2.4 N-ary trees: first-child / next-sibling

A node with an arbitrary number of children can't have a fixed number of child pointers. Convert it to a binary tree.

```
N-ary:                 LCRS form (left = first child, right = next sibling):
      A                      A
    / | \                   /
   B  C  D                 B
      |                     \
      E                      C
                            / \
                           E   D
```

Alternatives are `Vec<Child>` per node, or adjacency lists (`children: Vec<Vec<usize>>`), or a parent array `parent[i]`, which is the compact form used in union-find and many graph problems.

### 2.5 Ownership and lifetime

**Rust:** `Option<Box<Node>>` means each node owns its children exclusively. `Box` is a heap pointer with a destructor. Dropping the root recursively drops the whole tree. Consequences:
- No parent pointers without `Rc<RefCell<>>`/`Weak` or indices.
- **A deep tree (e.g. 10^6-node chain) overflows the stack on drop**, because the compiler-generated drop recurses. Fix with a manual iterative `Drop`, or use an arena.

**Go:** nodes are pointers, and the GC traces them. Cycles (parent pointers) are fine. Millions of small pointer-heavy nodes make GC mark phases slow, so use an index arena for large trees.

---

## 3. Binary trees and traversals

A binary tree has at most 2 children per node. Counts worth memorizing:
- Max nodes at depth d: 2^d. Max nodes at height h: 2^(h+1) - 1.
- A tree with n nodes has height between floor(log2 n) (balanced) and n-1 (a chain).
- Leaves = internal nodes with 2 children + 1.

Types:
```
Full:      every node has 0 or 2 children
Complete:  all levels full except possibly last, which fills left to right  (heaps)
Perfect:   all leaves at the same depth, all internal nodes have 2 children
Balanced:  height = O(log n)  (AVL: subtree heights differ by <= 1)
Degenerate: effectively a linked list
```

### 3.1 Depth-first traversals

```
          1
         / \
        2   3
       / \
      4   5

Preorder  (N L R): 1 2 4 5 3     -> copy a tree, serialize
Inorder   (L N R): 4 2 5 1 3     -> sorted output for a BST
Postorder (L R N): 4 5 2 3 1     -> delete a tree, compute subtree values
```

**Under the hood:** recursion is the call stack. Each call pushes a frame (return address, saved registers, locals, roughly 32 to 100 bytes). Stack depth equals tree height, so a degenerate tree with 10^6 nodes means 10^6 frames, and typical 8 MB stacks overflow. Iterative versions replace the hardware stack with an explicit heap-allocated stack.

```
Recursive inorder call stack at node 4:
  inorder(4)
  inorder(2)
  inorder(1)       <- frames grow downward; depth = height
```

### 3.2 Breadth-first (level order)

Uses a queue. It visits the nodes of depth d before depth d+1.

```
queue: [1]  -> pop 1, push 2,3 -> [2,3] -> pop 2, push 4,5 -> [3,4,5] ...
Order: 1 2 3 4 5
```

Queue size peaks at the widest level (up to n/2), whereas DFS stack size peaks at the height.

### 3.3 Morris traversal (O(1) extra space)

It temporarily rewires the inorder predecessor's right pointer to point back to the current node (a "thread"), uses that thread to climb back up, then restores it. It trades stack space for 2x pointer writes. It is a good example of mutating the structure itself to avoid auxiliary memory.

### 3.4 Iterative inorder in Rust

```rust
#[derive(Debug)]
struct Node {
    key: i32,
    left: Tree,
    right: Tree,
}
type Tree = Option<Box<Node>>;

fn inorder(root: &Tree) -> Vec<i32> {
    let mut out = Vec::new();
    let mut stack: Vec<&Node> = Vec::new();
    let mut cur = root.as_deref(); // Option<&Node>
    while cur.is_some() || !stack.is_empty() {
        while let Some(n) = cur {      // go as far left as possible
            stack.push(n);
            cur = n.left.as_deref();
        }
        let n = stack.pop().unwrap();  // visit
        out.push(n.key);
        cur = n.right.as_deref();      // then go right
    }
    out
}
```

---

## 4. Binary Search Tree (BST)

**Invariant:** for every node, all keys in the left subtree < key < all keys in the right subtree.

```
          50
        /    \
      30      70
     /  \    /  \
   20   40  60   80

Inorder = 20 30 40 50 60 70 80   (sorted)
```

### 4.1 Search: O(h)

At each node, compare and discard half the remaining candidates (if balanced). This is binary search over a pointer structure.

```
find 60: 50 -> (60>50) right -> 70 -> (60<70) left -> 60 found
```

### 4.2 Insert: O(h)

Search until you hit a null link, then put the new node there. It is always inserted as a leaf, so no restructuring occurs.

### 4.3 Delete: O(h), three cases

```
Case 1: leaf          -> just unlink
Case 2: one child     -> replace node with its child (splice out)
Case 3: two children  -> replace key with inorder successor (min of right subtree),
                         then delete that successor (which has at most 1 child)

Delete 50 (two children):
         50                60
       /    \             /  \
     30      70   ->    30    70
            /  \              \
          60    80             80
   successor = leftmost of right subtree = 60
```

### 4.4 The BST problem

Insert sorted input 1,2,3,4,... and you get a chain, so everything becomes O(n):

```
1
 \
  2
   \
    3
     \
      4      <- height = n-1
```

Self-balancing trees solve this.

### 4.5 BST in Rust

```rust
fn insert(t: &mut Tree, key: i32) {
    match t {
        None => *t = Some(Box::new(Node { key, left: None, right: None })),
        Some(n) => {
            if key < n.key { insert(&mut n.left, key) }
            else if key > n.key { insert(&mut n.right, key) }
        }
    }
}

fn contains(mut t: &Tree, key: i32) -> bool {
    while let Some(n) = t {
        if key == n.key { return true; }
        t = if key < n.key { &n.left } else { &n.right };
    }
    false
}

fn min_key(mut n: &Node) -> i32 {
    while let Some(l) = n.left.as_deref() { n = l; }
    n.key
}

fn remove(t: &mut Tree, key: i32) {
    if let Some(n) = t {
        if key < n.key { return remove(&mut n.left, key); }
        if key > n.key { return remove(&mut n.right, key); }
        match (n.left.take(), n.right.take()) {
            (None, None) => *t = None,
            (Some(l), None) => *t = Some(l),
            (None, Some(r)) => *t = Some(r),
            (Some(l), Some(r)) => {
                let mut right = Some(r);
                let succ = min_key(right.as_deref().unwrap());
                remove(&mut right, succ);
                n.key = succ;
                n.left = Some(l);
                n.right = right;
            }
        }
    }
}
```

`&mut Tree` is a pointer to the link itself (the parent's field), not to the node. That lets `*t = ...` rewire the parent's pointer directly, which is the same "pointer-to-pointer" trick used in C.

### 4.6 BST in Go (arena, iterative)

```go
type Node struct {
	key  int
	l, r int32 // -1 = nil
}

type BST struct {
	nodes []Node
	root  int32
}

func NewBST() *BST { return &BST{root: -1} }

func (b *BST) Insert(key int) {
	b.nodes = append(b.nodes, Node{key, -1, -1})
	id := int32(len(b.nodes) - 1)
	if b.root == -1 {
		b.root = id
		return
	}
	cur := b.root
	for {
		n := &b.nodes[cur]
		if key < n.key {
			if n.l == -1 { n.l = id; return }
			cur = n.l
		} else {
			if n.r == -1 { n.r = id; return }
			cur = n.r
		}
	}
}

func (b *BST) Contains(key int) bool {
	for cur := b.root; cur != -1; {
		n := &b.nodes[cur]
		switch {
		case key == n.key:
			return true
		case key < n.key:
			cur = n.l
		default:
			cur = n.r
		}
	}
	return false
}
```

Careful: `n := &b.nodes[cur]` becomes invalid if `append` reallocates the slice. Here `append` happens before taking `n`, so it is safe.

---

## 5. Self-balancing trees

### 5.1 Rotations: the primitive

A rotation changes shape in O(1) while preserving the inorder sequence, so BST validity is retained.

```
        y                         x
       / \     rotate right(y)   / \
      x   C   ---------------->  A   y
     / \      <----------------     / \
    A   B     rotate left(x)       B   C

Inorder before: A x B y C
Inorder after:  A x B y C        (identical)
```

It is only 3 pointer rewrites: `y.left = x.right; x.right = y; parent.link = x`.

### 5.2 AVL tree

Each node stores a height (or balance factor in {-1, 0, +1}). After insert or delete, walk back up the path and fix any node whose balance reaches ±2:

```
Case LL: left-left heavy      -> single right rotation
Case RR: right-right heavy    -> single left rotation
Case LR: left child is right-heavy -> rotate left on child, then right on node
Case RL: mirror of LR

LL example:        LR example:
    z                  z                 y
   /                  /                 / \
  y        ->        x       ->        x   z
 /                    \
x                      y
```

Guarantees height ≤ ~1.44 log2(n). Strictly balanced, so lookups are fast but updates do more rotations.

### 5.3 Red-Black tree

Each node is colored. Rules:
1. Root is black.
2. Red nodes have only black children.
3. Every root-to-nil path has the same number of black nodes.

This ensures the longest path is at most 2x the shortest, giving height ≤ 2 log2(n+1). It does fewer rotations than AVL on updates (at most 2 on insert, 3 on delete), so it is used in the Linux kernel (CFS scheduler, `rbtree`), C++ `std::map`, and Java `TreeMap`.

### 5.4 Others, briefly
- **Treap:** BST by key and a heap by random priority. Expected O(log n), simple to code (split/merge).
- **Splay tree:** moves an accessed node to the root by rotations. Amortized O(log n), good for locality.
- **Skip list:** probabilistic alternative with similar bounds (not a tree, but used for the same purpose).

---

## 6. B-tree and B+ tree (disk and database trees)

When data lives on disk, the cost model changes: reading a 4 KB page costs about the same as reading 1 byte. A binary tree wastes this, since it fetches a page to use one key. A B-tree packs many keys per node, matching the page size.

```
B-tree, order 4 (max 3 keys, 4 children per node):

                     [ 20 | 40 ]
                    /     |     \
         [5|10|15]   [25|30|35]   [45|50|55]

Node layout in one 4 KB page:
  [n_keys | k0 k1 k2 ... | child0 child1 child2 ... ]
```

Rules:
- All leaves are at the same depth.
- Every node except the root has at least ceil(m/2) children.
- **Insert:** place the key in a leaf. If it overflows, split into two nodes and push the median up. The root splits only when full, which is the only way height grows (the tree grows upward).
- **Delete:** if a node underflows, borrow from a sibling or merge with it.

Height is O(log_m n). With m ≈ 500, 10^9 keys fit in about 3 to 4 levels, so a lookup is 3 to 4 disk reads.

**B+ tree** (used by InnoDB, PostgreSQL, SQLite indexes, NTFS, ext4's htree):
```
Internal nodes: only keys + child pointers (more fanout)
Leaves: keys + values, linked together in a list

           [ 30 | 60 ]
          /     |     \
   [10 20] <-> [30 40 50] <-> [60 70 80]    <- leaf linked list => fast range scans
```

---

## 7. Heap (priority queue)

A complete binary tree stored in an array, with the **heap property**: each parent ≤ its children (min-heap).

```
Min-heap:               Array: [1, 3, 2, 7, 4, 5]
        1                       0  1  2  3  4  5
       / \
      3   2
     / \  /
    7  4 5
```

### Sift-up (after insert at the end): O(log n)
```
insert 0:  append at idx 6 -> compare with parent idx 2 (val 2) -> swap
           -> compare with parent idx 0 (val 1) -> swap -> done
```

### Sift-down (after pop-min: move the last element to the root): O(log n)
Swap with the smaller child until the property holds.

### Heapify (build from an arbitrary array): O(n)
Run sift-down from index n/2-1 down to 0. It is O(n) rather than O(n log n) because most nodes are near the bottom and sift only a short distance: the sum is n/2·0 + n/4·1 + n/8·2 + ... = O(n).

Heap sort is heapify, then repeatedly swapping the root with the last element and sifting down, giving O(n log n) in place.

```rust
fn sift_down(a: &mut [i32], mut i: usize) {
    let n = a.len();
    loop {
        let (l, r) = (2 * i + 1, 2 * i + 2);
        let mut m = i;
        if l < n && a[l] < a[m] { m = l; }
        if r < n && a[r] < a[m] { m = r; }
        if m == i { break; }
        a.swap(i, m);
        i = m;
    }
}
```

---

## 8. Trie (prefix tree)

Each edge is a character, and each path from the root spells a prefix.

```
Words: "to", "tea", "ten", "in"

 (root)
  ├─ t ─ o*            * = end of word
  │   └─ e ─ a*
  │        └─ n*
  └─ i ─ n*
```

Node layout options:
```
Array children:  [Option<Box<Node>>; 26]   -> O(1) step, 208 bytes/node on 64-bit
HashMap children: sparse alphabets, slower per step
Sorted Vec / compressed (radix tree): merge single-child chains into one edge
```

Insert and search are O(L) where L = word length, independent of how many words are stored. Used for autocomplete, IP routing (longest prefix match), and spell checking.

---

## 9. Range-query trees

### Segment tree
Each node stores an aggregate (sum, min, gcd, ...) of an interval.

```
a = [2, 5, 1, 4]

            [0,3]=12
           /        \
      [0,1]=7      [2,3]=5
      /    \       /    \
   [0]=2  [1]=5  [2]=1  [3]=4

Query sum [1,2]: take [1]=5 and [2]=1 = 6   (O(log n) nodes touched)
Update a[1]:     fix the leaf and every ancestor up to the root = O(log n)
```

Bottom-up array version (2n slots, leaves at `n..2n-1`, parent of i is `i>>1`):

```go
type Seg struct {
	n int
	t []int
}

func NewSeg(a []int) *Seg {
	n := len(a)
	t := make([]int, 2*n)
	copy(t[n:], a)
	for i := n - 1; i > 0; i-- {
		t[i] = t[2*i] + t[2*i+1]
	}
	return &Seg{n, t}
}

func (s *Seg) Update(i, v int) {
	i += s.n
	s.t[i] = v
	for i >>= 1; i >= 1; i >>= 1 {
		s.t[i] = s.t[2*i] + s.t[2*i+1]
	}
}

// sum over [l, r)
func (s *Seg) Query(l, r int) int {
	res := 0
	for l, r = l+s.n, r+s.n; l < r; l, r = l>>1, r>>1 {
		if l&1 == 1 { res += s.t[l]; l++ }
		if r&1 == 1 { r--; res += s.t[r] }
	}
	return res
}
```

Add **lazy propagation** to support range updates in O(log n): store a pending tag at a node and push it to children only when you need to descend.

### Fenwick tree (BIT)
It is an implicit tree where index i is responsible for the range of size `lowbit(i) = i & -i` ending at i.

```
idx:   1  2  3  4  5  6  7  8
covers:1 1-2 3 1-4 5 5-6 7 1-8

prefix(7) = t[7] + t[6] + t[4]     (strip lowbits: 7 -> 6 -> 4 -> 0)
update(i): i += i & -i  until > n
```

It is simpler and faster than a segment tree but supports fewer operations.

---

## 10. Other important trees

| Structure | Idea | Use |
|---|---|---|
| Union-Find (DSU) | Forest with `parent[]`; path compression + union by rank → α(n) per op | Connectivity, Kruskal |
| Merkle tree | Each node = hash of its children's hashes | Git, blockchains, anti-entropy in Dynamo/Cassandra |
| K-d tree | Alternate split dimension per level | Nearest neighbor in k dimensions |
| Quadtree / Octree | Split space into 4 / 8 quadrants | Collision detection, graphics |
| Suffix tree / array | All suffixes in a compressed trie | Substring search, bioinformatics |
| Interval tree | BST by interval start, augmented with max end | Overlap queries |
| Decision tree / expression tree / AST | Tree of branches or operators | ML, compilers |
| Spanning tree | Subtree connecting all vertices of a graph | MST, network protocols |

---

## 11. Core algorithms on trees

**Height / size / diameter (postorder DP):** compute from the children, then combine.
```
height(n) = 1 + max(height(l), height(r))
diameter  = max over nodes of (height(l) + height(r))   // longest path between any two nodes
```

**Lowest Common Ancestor (LCA):**
- Naive: walk up using depth, O(h) per query.
- **Binary lifting:** `up[k][v]` = the 2^k-th ancestor of v, built in O(n log n). Lift the deeper node to the same depth by jumping, then jump both up together; O(log n) per query.
- **Euler tour + RMQ** (sparse table): O(1) per query after O(n log n) preprocessing.

```
Euler tour of tree:   1 2 4 2 5 2 1 3 1
LCA(4,5) = min-depth node between their first occurrences = 2
```

**Euler tour / tin-tout flattening:** record `tin[v]` on entering and `tout[v]` on leaving. A subtree becomes the contiguous array range `[tin, tout]`, so subtree queries become range queries on a segment tree or BIT. This is a very common competitive-programming trick.

```
        1                 tin: 1=0, 2=1, 4=2, 5=3, 3=4
       / \                tout: 4=2, 5=3, 2=3, 3=4, 1=4
      2   3               subtree(2) = array positions [1..3]
     / \
    4   5
```

**Tree DP:** `dp[v]` is computed from `dp[children]` (max independent set, subtree sums, rerooting technique for "answer for every root").

**Serialization:** preorder with null markers uniquely determines a binary tree. Inorder alone does not; preorder + inorder together do.

**Rerooting and centroid decomposition** are advanced techniques for "for every node" queries and path queries in O(n log n).

---

## 12. Complexity cheat sheet

| Structure | Search | Insert | Delete | Notes |
|---|---|---|---|---|
| BST (unbalanced) | O(h), worst O(n) | O(h) | O(h) | Chain worst case |
| AVL / Red-Black | O(log n) | O(log n) | O(log n) | Guaranteed |
| B-tree / B+ tree | O(log_m n) I/Os | O(log_m n) | O(log_m n) | Disk-friendly |
| Binary heap | O(n) arbitrary; O(1) peek-min | O(log n) | O(log n) pop | Build in O(n) |
| Trie | O(L) | O(L) | O(L) | Space heavy |
| Segment tree | O(log n) query | O(log n) update | n/a | 2n to 4n memory |
| Fenwick tree | O(log n) | O(log n) | n/a | n memory |
| DSU | α(n) amortized | | | |

Traversals are O(n) time. Space is O(h) for DFS and O(width) for BFS.

---

## 13. Practical guidance

**Competitive programming**
- Prefer arrays and index arenas over pointer nodes (cache and speed).
- Avoid deep recursion (n ≥ 10^5 chains): use an iterative DFS, or raise the stack limit (Go's goroutine stacks grow dynamically up to 1 GB by default, so it is generally fine; Rust's main thread has about 8 MB, so spawn a thread with a larger stack via `std::thread::Builder::stack_size`).
- Store trees as adjacency lists `Vec<Vec<usize>>`, or as flat CSR arrays (`head[]`, `next[]`) for speed.
- Use Fenwick or segment trees after an Euler tour for subtree queries.

**System design**
- Database indexes: B+ tree (range scans, point lookups), versus LSM-tree (write-heavy, memtable + sorted runs).
- File systems: directory hierarchy is a tree; ext4/XFS/Btrfs use B-tree variants for extents and directories.
- Routing: tries or radix trees for longest-prefix match.
- Sync and integrity: Merkle trees for diffing large datasets cheaply.
- Schedulers and timers: heaps (priority queues) or red-black trees.
- Ordered in-memory maps: balanced BSTs (or skip lists, as in Redis sorted sets).

**Bare metal**
- No allocator? Use a fixed arena with a static array of nodes and a free list, with indices as links.
- Keep a node within a cache line (64 B) when possible; for B-trees, size nodes to the page or a multiple of a cache line.
- Intrusive trees (as in the Linux kernel's `rb_node` embedded in your struct) avoid a separate allocation per node.

---

If you'd like, I can go deeper on any one of these, for example a full AVL or red-black implementation in Rust, a lazy segment tree, or a B+ tree page layout, or put the whole thing in a markdown file.

# Finding an Index in the Array Tree Model

"Find the index of a value" can mean three different things, and each has a different answer. The equations only give you **structure** (where a node sits). They never give you **content** (which value is where) unless the tree has an ordering rule.

## 1. Index from structure (pure math, O(1))

Take a node at level `d` (root = level 0) and position `p` within that level (counted left to right from 0).

```
level 0:                     [0]
level 1:             [1]            [2]
level 2:         [3]    [4]      [5]    [6]
level 3:       [7] [8] [9][10] [11][12] [13][14]

Level d starts at index 2^d - 1 and holds 2^d slots.

index(d, p) = 2^d - 1 + p
```

Inverse: from an index to its level and position (0-indexed array):

```
d = floor(log2(i + 1))
p = (i + 1) - 2^d

Example i = 10:  i+1 = 11, d = floor(log2 11) = 3, p = 11 - 8 = 3
Check: level 3 starts at 7, 7 + 3 = 10 ✓
```

**Under the hood:** `floor(log2(x))` is not computed with floating point. It is the position of the highest set bit, which one CPU instruction finds (`lzcnt`/`bsr` on x86, `clz` on ARM):

```
d = 63 - leading_zeros(i + 1)      // for a 64-bit integer
```

## 2. The 1-indexed trick: the index *is* the path

If you start the root at index 1 instead of 0:

```
left(i)  = 2i        = i << 1
right(i) = 2i + 1    = (i << 1) | 1
parent(i) = i >> 1
```

Each step down appends one bit: 0 for left, 1 for right. So the binary form of the index spells the route from the root.

```
index 11 = 1011₂
           ^ leading 1 = root (drop it)
            011 = bits read left to right: 0=Left, 1=Right, 1=Right

1 --L--> 2 --R--> 5 --R--> 11     ✓   (2*1=2, 2*2+1=5, 2*5+1=11)

          1
        /   \
       2     3
      / \   / \
     4   5 6   7
        / \
      10   11
```

This is why 1-indexing is popular in competitive programming. Going up is a single shift, and the depth is `bit_length(i) - 1`. Fenwick and bottom-up segment trees rely on the same idea.

Path to index and back (1-indexed):

```rust
fn index_from_path(path: &[bool]) -> usize {   // false = left, true = right
    let mut i = 1usize;
    for &right in path {
        i = (i << 1) | right as usize;
    }
    i
}

fn path_from_index(i: usize) -> Vec<bool> {    // i >= 1
    let d = i.ilog2();                          // depth = highest set bit
    (0..d).rev().map(|b| (i >> b) & 1 == 1).collect()
}
```

## 3. Index from a value (needs a search)

This is the case where you cannot use an equation alone. What you can do depends on the ordering rule.

### a) BST stored in an array: O(h)

The ordering rule tells you which child to pick, and the equations turn that choice into an index.

```
find 60 in array BST:

idx:  0   1   2   3   4   5   6
val: [50, 30, 70, 20, 40, 60, 80]

i=0: 50, 60 > 50 -> i = 2*0+2 = 2
i=2: 70, 60 < 70 -> i = 2*2+1 = 5
i=5: 60 found -> return 5
```

```rust
fn find(a: &[Option<i32>], key: i32) -> Option<usize> {
    let mut i = 0;
    while i < a.len() {
        match a[i] {
            None => return None,              // empty slot: key not present
            Some(v) if v == key => return Some(i),
            Some(v) if key < v => i = 2 * i + 1,
            Some(_) => i = 2 * i + 2,
        }
    }
    None
}
```

```go
func find(a []int, used []bool, key int) int {
	i := 0
	for i < len(a) && used[i] {
		switch {
		case a[i] == key:
			return i
		case key < a[i]:
			i = 2*i + 1
		default:
			i = 2*i + 2
		}
	}
	return -1
}
```

Warning: for a skewed tree of depth h, the index grows to about 2^h. At depth 64 a `u64` index overflows, and long before that the array would need exabytes. So array BSTs only make sense when the tree is guaranteed balanced or complete.

### b) Heap: O(n), or O(1) with a side table

A heap only orders parent against child, not left against right. The value could be in either subtree, so there is no path to follow.

```
min-heap:       1            Looking for 7:
              /   \          3 < 7 but 7 could be under 3 or 2
             3     2         -> no pruning possible except "skip subtrees whose root > 7"
            / \
           7   4
```

Options:
- Linear scan of the array: O(n).
- Pruned DFS: stop descending when `a[i] > key` (min-heap). Still O(n) worst case.
- **Position map (indexed heap):** keep `pos[value]` or `pos[id]` and update it inside every swap of sift-up and sift-down. Lookup becomes O(1), and decrease-key becomes O(log n). Dijkstra implementations use this.

```
swap(a[i], a[j]) must also do: pos[a[i]] = i; pos[a[j]] = j;
```

### c) Segment tree: leaf of position `p`

```
bottom-up layout, n leaves:   leaf_index(p) = n + p
parent chain:                 (n+p) >> 1, >> 2, ... , 1
```

You are indexing by *position in the original array*, so no search is needed.

### d) Sorted array into a balanced array-tree (Eytzinger layout)

Given the sorted position `k` of a value (0 to n-1) in a **perfect** tree of height H (n = 2^(H+1) - 1), the inorder rank maps to a heap index like this:

```
k + 1 = odd_part * 2^t        (t = trailing zeros of k+1)
level d = H - t
p = (odd_part - 1) / 2
index = 2^d - 1 + p
```

Example, n = 7, H = 2, sorted `[10,20,30,40,50,60,70]`, value 60 has k = 5:
```
k+1 = 6 = 3 * 2^1  -> t = 1, odd = 3
d = 2 - 1 = 1, p = (3-1)/2 = 1
index = 2^1 - 1 + 1 = 2        (the right child of the root's level... idx 2)
```
Check: the inorder of the layout `[40,20,60,10,30,50,70]` puts 60 at index 2 ✓.

## 4. Summary

| You know | You want | Method | Cost |
|---|---|---|---|
| Level and position | index | `2^d - 1 + p` | O(1) |
| Index | level, position | `ilog2(i+1)` and subtract | O(1) |
| Path L/R string | index | 1-indexed: shift in bits | O(depth) |
| Value in BST array | index | compare and apply `2i+1` / `2i+2` | O(h) |
| Value in heap | index | scan, or maintain `pos[]` | O(n) / O(1) |
| Position in segment tree | leaf index | `n + p` | O(1) |

The rule to remember: an equation can convert between *index* and *shape*. To convert between *value* and *index*, something has to tell you which way to go. That is either the BST ordering rule, a side lookup table, or a scan.

# The Math Behind Locating a Node in a Tree

Everything reduces to four tools: **geometric series** (counting nodes), **base-2 numerals** (index = path), **logarithms** (depth and search cost), and **recurrences** (why balance matters).

## 1. Counting nodes: the geometric series

A perfect binary tree has 2^d nodes at depth d.

```
depth 0:  1 node      = 2^0
depth 1:  2 nodes     = 2^1
depth 2:  4 nodes     = 2^2
depth 3:  8 nodes     = 2^3
```

Nodes **before** level d (all shallower levels):

```
S = 2^0 + 2^1 + ... + 2^(d-1) = 2^d - 1
```

**Proof:** let S = 1 + 2 + ... + 2^(d-1). Then 2S = 2 + 4 + ... + 2^d. Subtract: 2S - S = 2^d - 1.

**Binary view:** 2^d - 1 is d ones in binary (`111...1`), and adding 1 carries through every bit to give `1000...0`. So a run of d ones plus one equals 2^d.

Total nodes in a perfect tree of height h: `n = 2^(h+1) - 1`, so `h = log2(n+1) - 1`.

## 2. Deriving the index formula

Place each node by `(d, p)`: level d, position p counted from 0 on that level.

```
index(d, p) = (nodes before level d) + p = 2^d - 1 + p
```

**Derive the children.** The node at `(d, p)` has children at `(d+1, 2p)` and `(d+1, 2p+1)`. This works because each node on level d produces two slots on level d+1, so the nodes before it produce 2p slots.

```
level d:     p=0        p=1        p=2
            /   \      /   \      /   \
level d+1: 0     1    2     3    4     5      (positions = 2p, 2p+1)
```

Plug into the index formula:

```
left  = 2^(d+1) - 1 + 2p
      = 2(2^d - 1 + p) + 2 - 1
      = 2i + 1                     (with i = 2^d - 1 + p)

right = left + 1 = 2i + 2
```

That is the whole proof of the 0-indexed formulas. The parent comes from solving for i:

```
child c = 2i+1 or 2i+2   =>   i = floor((c - 1) / 2)
```

The floor handles both cases at once, because `(2i+1-1)/2 = i` and `(2i+2-1)/2 = i + 0.5`.

## 3. Why 1-indexing makes the index equal the path

Shift the numbering by 1: the root is index 1 and level d starts at 2^d.

```
index(d, p) = 2^d + p          (0 <= p < 2^d)
left(i)  = 2i,   right(i) = 2i + 1,   parent(i) = floor(i / 2)
```

In base 2, multiplying by 2 is a left shift, so it appends a 0. Adding 1 to an even number sets the last bit.

```
left(i)  : append bit 0     i=101₂  ->  1010₂
right(i) : append bit 1     i=101₂  ->  1011₂
parent(i): drop last bit    i=1011₂ ->  101₂
```

So the index written in binary is `1` followed by the path bits (0 = left, 1 = right):

```
index 13 = 1101₂ :  1 | 1 0 1   -> root, Right, Left, Right

           1
         /   \
        2     3
       / \   / \
      4   5 6   7
         ... 12  13   <- 6 has children 12, 13
```

Polynomial view: if the path bits are b_(d-1) ... b_0, then

```
index = 2^d + b_(d-1)*2^(d-1) + ... + b_1*2 + b_0
```

This is just the positional number system, with the leading 1 marking where the path starts.

**Depth** is the position of the highest set bit:

```
depth(i) = floor(log2 i)        (1-indexed)
```

This is true because `2^d <= i < 2^(d+1)` on level d. Taking log2 of both sides gives `d <= log2 i < d+1`. In hardware it is a leading-zero count: `63 - i.leading_zeros()`.

## 4. LCA with pure bit math

In a heap-indexed tree, an ancestor is a prefix of the binary string, so the lowest common ancestor is the longest common prefix.

```
a = 1011010₂  (90)
b = 10111₂    (23)

align depth:  a >> (depth(a) - depth(b)) = 1011₂ ... then shift both until equal.
```

```rust
fn lca(mut a: u64, mut b: u64) -> u64 {          // 1-indexed heap numbering
    let (da, db) = (a.ilog2(), b.ilog2());
    if da > db { a >>= da - db } else { b >>= db - da }   // same depth
    while a != b { a >>= 1; b >>= 1 }                      // climb together
    a
}
```

Cost is O(log n), with no pointers and no memory access. A faster version finds the highest differing bit with XOR: `shift = (a ^ b).ilog2() + 1`, then `a >> shift`, after depth alignment.

## 5. Why search costs log n: the recurrence

Each comparison discards one subtree. In a balanced tree, a subtree holds about half the nodes:

```
T(n) = T(n/2) + c
     = T(n/4) + 2c
     = T(n/2^k) + k*c       stop when n/2^k = 1, i.e. k = log2 n
T(n) = c * log2 n + T(1) = O(log n)
```

If the tree is skewed, one subtree holds n-1 nodes:

```
T(n) = T(n-1) + c = c*n = O(n)
```

That one recurrence is the difference between a balanced tree and a linked list.

### Lower bound: you can't beat log2 n comparisons

A comparison-based search is itself a binary decision tree. Searching n keys has n+1 distinguishable outcomes (n hits plus "not found"), and each comparison yields at most 2 outcomes. After h comparisons you can distinguish at most 2^h outcomes:

```
2^h >= n + 1   =>   h >= log2(n + 1)
```

So O(log n) search is optimal for comparison-based structures, and no cleverer tree can improve it.

## 6. Height bounds

For any binary tree with n nodes and height h (edges):

```
h + 1 <= n <= 2^(h+1) - 1
log2(n+1) - 1 <= h <= n - 1
```

Left side: a chain. Right side: a perfect tree. Balanced trees keep h = Θ(log n).

### AVL height: Fibonacci appears

Let N(h) be the **minimum** number of nodes in an AVL tree of height h. The sparsest valid tree has one subtree of height h-1 and one of height h-2:

```
N(h) = N(h-1) + N(h-2) + 1       N(0)=1, N(1)=2
```

This is the Fibonacci recurrence, so N(h) grows like φ^h with φ = (1+√5)/2 ≈ 1.618. Invert it:

```
n >= φ^h   =>   h <= log_φ(n) = log2(n) / log2(φ) ≈ 1.44 * log2(n)
```

That is where the 1.44 constant comes from.

### Red-black height

The black-height b is the same on every path, so n >= 2^b - 1. Red nodes can't be adjacent, so the height is at most 2b. Therefore:

```
h <= 2b <= 2*log2(n+1)
```

### Random BST

Inserting n random keys gives an expected depth of about 2·ln(n) ≈ 1.39·log2(n). This comes from the quicksort-style recurrence, because the root is a uniformly random pivot. It is the math behind treaps.

## 7. Change of base: why B-trees are shallow

With m children per node, the height is `log_m(n)`:

```
log_m(n) = log2(n) / log2(m)

n = 10^9, binary:  log2(10^9)   ≈ 30 levels
n = 10^9, m=500:   log_500(10^9) = 29.9 / 8.97 ≈ 3.3 -> 4 levels
```

The comparison count is similar (log2 of m per node via binary search inside), but the **page reads** drop from 30 to 4. That is the whole B-tree argument.

## 8. Fenwick tree math: two's complement

`i & -i` isolates the lowest set bit. Why it works: in two's complement, `-i = ~i + 1`.

```
i    = 0110 1000
~i   = 1001 0111
~i+1 = 1001 1000   (the +1 carries through the trailing 1s of ~i, which were
                    the trailing 0s of i, stops at the lowest set bit)
i & -i = 0000 1000   <- only the lowest set bit survives
```

Index i covers `(i - lowbit(i), i]`.

```
prefix(i):  i -= i & -i     removes the lowest set bit, so at most popcount(i) <= log2 n steps
update(i):  i += i & -i     carries upward through ancestors, at most log2 n steps
```

Query cost equals the number of set bits in the index, which is the math reason it's O(log n).

## 9. Binary lifting: any jump is a sum of powers of two

To go k levels up, write k in binary: `k = Σ b_j * 2^j`. Store `up[j][v]` = the 2^j-th ancestor.

```
up[0][v] = parent(v)
up[j][v] = up[j-1][ up[j-1][v] ]        (2^(j-1) + 2^(j-1) = 2^j)

k = 13 = 1101₂  -> jump 8, then 4, then 1   (3 jumps instead of 13)
```

Every integer 0 to n-1 has a unique binary representation with at most log2 n bits, so any ancestor query takes at most log2 n jumps. Table size is n·log2 n.

## 10. Heap build is O(n): the sum

Sifting down a node at height j costs at most j. At most `n / 2^(j+1)` nodes have height j:

```
T(n) = Σ_{j=0}^{log n}  (n / 2^(j+1)) * j  =  (n/2) * Σ j / 2^j
```

The series Σ_{j>=0} j·x^j = x/(1-x)^2. At x = 1/2:

```
Σ j / 2^j = (1/2) / (1/2)^2 = 2    =>   T(n) <= (n/2) * 2 = n = O(n)
```

## 11. Counting tree shapes: Catalan numbers

The number of distinct binary trees with n nodes is

```
C_n = (1 / (n+1)) * binom(2n, n)       1, 1, 2, 5, 14, 42, ...
```

Derivation: pick a root, then split the other n-1 nodes between the left and right subtrees:

```
C_n = Σ_{i=0}^{n-1} C_i * C_{n-1-i}
```

This is the same recurrence as counting valid bracket sequences and BST shapes. It is also why inorder alone cannot identify a tree: many shapes share one inorder sequence.

## 12. Verifying the formulas in code

```rust
fn main() {
    // 1-indexed heap: check parent/child, depth and path identities
    for i in 1u64..1 << 16 {
        assert_eq!(i << 1 >> 1, i);                 // parent(left(i)) == i
        assert_eq!((i << 1 | 1) >> 1, i);           // parent(right(i)) == i
        let d = i.ilog2();
        assert!((1u64 << d) <= i && i < (1u64 << (d + 1)));   // level bounds
    }
    // 0-indexed vs 1-indexed agree: i0 = i1 - 1
    for i0 in 0u64..1 << 16 {
        let l = 2 * i0 + 1;
        assert_eq!(l + 1, 2 * (i0 + 1));            // shifting the base preserves structure
    }
    // geometric series
    for d in 0..40u32 {
        let s: u64 = (0..d).map(|k| 1u64 << k).sum();
        assert_eq!(s, (1u64 << d) - 1);
    }
    println!("all identities hold");
}
```

```go
package main

import (
	"fmt"
	"math/bits"
)

func main() {
	for i := uint64(1); i < 1<<16; i++ {
		d := bits.Len64(i) - 1 // floor(log2 i)
		if !(uint64(1)<<d <= i && i < uint64(1)<<(d+1)) {
			panic("level bounds")
		}
		if (i<<1)>>1 != i || (i<<1|1)>>1 != i {
			panic("parent/child")
		}
	}
	fmt.Println("all identities hold")
}
```

## Summary

| Question | Math tool | Result |
|---|---|---|
| How many nodes before level d? | Geometric series | 2^d - 1 |
| Where are a node's children? | Algebra on `2^d - 1 + p` | 2i+1, 2i+2 |
| What is a node's path? | Base-2 positional numerals | Index bits = path |
| What depth is node i? | Logarithm = highest set bit | floor(log2 i) |
| Why is search O(log n)? | Recurrence T(n) = T(n/2) + c | c·log2 n |
| Why can't it be faster? | Decision tree, 2^h >= n+1 | h >= log2(n+1) |
| Why is AVL ≈ 1.44 log n? | Fibonacci recurrence | log_φ n |
| Why are B-trees shallow? | Change of base | log2 n / log2 m |
| Why is Fenwick O(log n)? | Two's complement, popcount | ≤ log2 n steps |
| Why is lifting O(log n)? | Binary decomposition of k | ≤ log2 n jumps |
| Why is heapify O(n)? | Σ j/2^j = 2 | n |

The underlying idea is that a tree is a way of encoding a number in base b (b = 2 for binary), so locating a node costs one digit per level, which means log_b(n) steps.