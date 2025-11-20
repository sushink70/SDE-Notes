Below is a comprehensive catalog of searching (lookup) algorithms, grouped by problem domain, data structure assumptions, time/space complexity, and practical relevance. This covers algorithms you will encounter in systems programming (e.g., Linux kernel, Rust std, glibc), competitive programming, databases, and theoretical CS.

I’ve noted key properties: worst-case guarantees, amortized bounds, cache behavior, parallelism, and real-world usage (especially in memory-safe or security-critical contexts).

### 1. Searching in Unsorted / Sequential Data

| Algorithm                  | Time (best / avg / worst) | Space | Notes / Real-world |
|----------------------------|---------------------------|-------|--------------------|
| Linear Search              | O(1) / O(n) / O(n)        | O(1)  | Sentinel trick (glibc memset-like), ubiquitous for tiny n |
| Bidirectional Linear      | —                         | O(1)  | Rare, minor constant win |
| Exponential Search         | O(log i) where i = pos    | O(1)  | Precursor to binary search on unbounded arrays |

### 2. Searching in Sorted Arrays (Static, Comparison-Based)

| Algorithm                       | Time (worst)      | Space | Stable/Order | Notes |
|---------------------------------|-------------------|-------|--------------|-------|
| Binary Search (classic)         | O(log n)          | O(1)  | —            | Iterative preferred in systems (no recursion stack) |
| Uniform Binary Search           | O(log n)          | O(1)  | —            | Fewer branches (Bentley/Yao) |
| Interpolation Search            | O(log log n) avg, O(n) worst | O(1) | — | Assumes uniform distribution; used in dictionaries |
| Exponential + Binary            | O(log i)          | O(1)  | —            | For unbounded sorted arrays (Java, Rust lower_bound on infinite streams) |
| Fibonacci Search                | O(log n)          | O(1)  | —            | No divisions/multiplications – useful on old hardware |

### 3. Self-Balancing Binary Search Trees (Dynamic Sets)

| Tree                  | Search / Insert / Delete | Space       | Notes |
|-----------------------|--------------------------|-------------|-------|
| Red-Black (std::map/set C++, BTreeMap Rust) | O(log n) all             | O(n)        | Cache-friendly, used in kernels |
| AVL                   | O(log n)                 | O(n)        | Stricter balance → fewer rotations |
| Splay                 | O(log n) amortized       | O(n)        | Cache-oblivious, self-optimizing |
| Treap (randomized BST)| O(log n) expected        | O(n)        | Simple + provably balanced |
| Weight-Balanced (WB)  | O(log n)                 | O(n)        | Used in some functional languages |

### 4. Hash-Based Searching (Average-Case O(1))

| Algorithm / Table             | Search / Insert / Delete | Load Factor | Collision Strategy | Real-World |
|-------------------------------|--------------------------|-------------|--------------------|------------|
| Separate Chaining             | O(1) avg, O(n) worst     | ~1.0        | Linked lists / trees | Java HashMap (trees after threshold) |
| Open Addressing – Linear Probe| O(1) avg                 | <0.7        | Clustering issues   | Rust HashMap (SwissTable variant) |
| Open Addressing – Robin Hood  | O(1) avg, better probes  | <0.9        | Variance reduction  | Google Abseil, Rust hashbrown |
| Cuckoo Hashing                | O(1) worst (amortized)   | ~0.5        | Two tables + kicks  | High-performance caches |
| Hopscotch Hashing             | O(1) worst               | high        | Neighborhood        | Intel TBB |
| Perfect Hashing (static)      | O(1) worst               | O(n)        | gperf, cmph         | Compilers, kernels |

Modern high-perf: **SwissTable** (Rust hashbrown, Abseil) – SIMD probe + metadata bytes → best real-world lookup speed.

### 5. Integer / Succinct Data Structures (Beyond Comparison)

| Structure                          | Query Time                | Space                  | Use Case |
|------------------------------------|---------------------------|------------------------|----------|
| Binary Search on Prefix Sums       | O(log n)                  | O(n)                   | Static sets |
| van Emde Boas Tree                 | O(log log u)              | O(u)                   | Universe size u |
| y-Fast Trie                        | O(log log u) amortized    | O(n)                   | Practical vEB |
| Fusion Tree                        | O(log n / log log n)      | O(n)                   | Word-RAM, theoretical |
| Rank/Select on Bitvectors (FM-index, succint) | O(1) with O(n) preproc | o(n) bits            | Burrows-Wheeler, bioinformatics |
| Wavelet Tree                       | O(log σ)                  | O(n log σ)             | Text indexes |

### 6. Spatial / Multi-Dimensional Searching

| Structure                     | Query                  | Notes |
|-------------------------------|------------------------|-------|
| k-d Tree                      | O(√n + k) nearest     | Static, cache-poor |
| R-Tree / R*                   | Rectangle overlap      | GIS, databases (PostGIS) |
| Quadtree / Octree             | Point/region           | Games, spatial indexing |
| Ball Tree                     | Nearest neighbors      | ML (scikit-learn) |
| Cover Tree                    | O(c¹² log n) nearest   | Theoretical guarantees |

### 7. String / Pattern Searching

| Algorithm                  | Preproc | Search Time       | Notes |
|----------------------------|---------|-------------------|-------|
| Naive                      | O(1)    | O(nm) worst       | — |
| Knuth–Morris–Pratt (KMP)   | O(m)    | O(n)              | Partial match table |
| Boyer–Moore (BM)           | O(m)    | O(n/m) avg, O(nm) worst | Sublinear in practice |
| Rabin–Karp (rolling hash)  | O(m)    | O(n) avg, O(nm) worst | Multiple patterns |
| Aho–Corasick               | O(m)    | O(n + z)          | Dictionary matching (virus scanners) |
| Bitap (shift-or)           | O(m)    | O(n ⌈m/w⌉)        | Bit-parallel, fast for small m |
| Sunday / Quick Search      | O(m)    | Sublinear practical | Faster BM variant |

### 8. Graph Searching / Traversal

| Algorithm       | Time         | Space      | Notes |
|-----------------|--------------|------------|-------|
| DFS (recursive) | O(V+E)       | O(V) stack | Kernel call graphs |
| DFS (iterative) | O(V+E)       | O(V)       | Avoids stack overflow |
| BFS             | O(V+E)       | O(V) queue | Level-order |
| Bidirectional Search | √O(V+E) in practice | O(V) | Faster pathfinding |
| A*              | Optimal with admissible heuristic | O(V) | Games, robotics |
| IDA*            | Same, linear space | O(d)     | Memory-constrained |

### 9. Exotic / Theoretical

| Algorithm                        | Claim                                 | Status |
|----------------------------------|---------------------------------------|--------|
| Grover’s Algorithm (quantum)     | O(√n) for unsorted database           | Quantum only |
| Quantum Exponential Search       | O(√log n) on sorted                   | Theoretical |
| Fredman–Saks Deterministic vEB   | O(log log u) amortized per op         | Impractical |
| Learned Indexes (Google 2018)    | O(1) effective with ML model          | Used in SOSD benchmarks |

### Searching Implementations in Major Systems (2025)

| System / Language       | Primary Search for Ordered    | Primary Hash Table                |
|-------------------------|-------------------------------|-----------------------------------|
| C++ std::lower_bound    | Binary search (uniform variant in libstdc++) | Unordered_map → Robin Hood variant |
| Rust slice::binary_search | Galloping + binary (exponential then binary) | hashbrown → SwissTable |
| Linux kernel            | Custom red-black, sorted arrays + binary | htable, rhashtable |
| Go                      | Map → open addressing         | — |
| Java                    | TreeMap (red-black) / HashMap (trees after 8) | — |
| glibc bsearch           | Classic binary search         | — |

There is no literal “all” – new variants appear yearly (e.g., learned bloom filters, ice lake-optimized SIMD hashing, xgboost-tuned indexes). The list above covers >99% of what systems/kernel/cloud-native engineers actually use or study.

Want a deep dive into any (e.g., why Rust’s binary_search uses galloping, SwissTable metadata layout, or how Aho–Corasick is used in eBPF packet filtering)? Let me know.