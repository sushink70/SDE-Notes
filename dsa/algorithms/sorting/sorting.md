Below is a comprehensive (but not literally infinite) catalog of sorting algorithms, grouped by their core design principles, time/space complexity, and practical relevance. This list prioritizes algorithms that have appeared in academic literature, standard textbooks, competitive programming, systems programming (e.g., libc, Linux kernel, Rust std), or real-world high-performance libraries.

I’ve included the best/average/worst time complexity, stability, and keyed notes on when they shine or are used in practice (especially in secure/systems contexts where predictability, cache behavior, or memory safety matter).

### Comparison-Based Sorts (Ω(n log n) lower bound in worst case)

| Algorithm                  | Best      | Average    | Worst      | Space   | Stable? | Notes / Real-world use |
|----------------------------|-----------|------------|------------|---------|---------|------------------------|
| Insertion Sort             | O(n)      | O(n²)      | O(n²)      | O(1)    | Yes     | Tiny arrays, adaptive, used in TimSort hybrid |
| Binary Insertion Sort      | O(n log n)| O(n²)      | O(n²)      | O(1)    | Yes     | Reduces comparisons but more shifts |
| Selection Sort             | O(n²)     | O(n²)      | O(n²)      | O(1)    | No      | Rarely used; simple but poor cache |
| Bubble Sort                | O(n)      | O(n²)      | O(n²)      | O(1)    | Yes     | Teaching only; Cocke–Younger–Kasami variant exists |
| Cocktail Shaker Sort       | O(n)      | O(n²)      | O(n²)      | O(1)    | Yes     | Bidirectional bubble |
| Gnome Sort                 | O(n)      | O(n²)      | O(n²)      | O(1)    | Yes     | Silly but insertion-like |
| Comb Sort                  | O(n log n)| ~O(n²/2^k)| O(n²)     | O(1)    | No      | Bubble with gaps; surprisingly fast in practice |
| QuickSort                  | O(n log n)| O(n log n) | O(n²)      | O(log n)| No      | Dominant in libc (qsort), dual-pivot variants, introsort hybrid |
| Introsort                  | O(n log n)| O(n log n) | O(n log n) | O(log n)| No      | Heapsort fallback → worst-case guarantee (used in C++ std::sort) |
| Merge Sort                 | O(n log n)| O(n log n) | O(n log n) | O(n)    | Yes     | External sorting, stable, parallelizable |
| Bottom-up Merge Sort       | same      | same       | same       | O(n)    | Yes     | No recursion → better in systems code |
| In-place Merge Sort        | same      | same       | same       | O(1)    | Yes     | Complex, rarely practical |
| TimSort                    | O(n)      | O(n log n) | O(n log n) | O(n)    | Yes     | Python, Java, Android, Rust (since 1.78) — exploits natural runs |
| Heap Sort                  | O(n log n)| O(n log n) | O(n log n) | O(1)    | No      | Simple, guaranteed, used as fallback |
| Smoothsort                 | O(n)      | O(n log n) | O(n log n) | O(1)    | No      | Leonardo heaps; adaptive like TimSort but in-place |
| Weak Heap Sort             | same      | same       | same       | O(1)    | No      | Fewer comparisons than heap sort |
| Library Sort (Gapped Insertion) | O(n log n)| O(n log n) | O(n log n) | O(n) | Yes     | Theoretical bridge to patience sorting |
| Patience Sorting           | —         | O(n log n) | O(n log n) | O(n)    | Yes     | Longest increasing subsequence based |
| Tournament Sort            | same      | same       | same       | O(n)    | Yes/No  | Heap-like replacement selection |
| Tree Sort (BST)            | O(n log n)| O(n log n) | O(n²)      | O(n)    | Yes     | Becomes balanced → O(n log n) worst |
| Cube Sort                  | —         | O(n log n) | O(n log n) | O(n)    | Yes     | Multi-dimensional merge |
| Strand Sort                | O(n)      | O(n²)      | O(n²)      | O(n)    | Yes     | Builds increasing strands |
| Bitonic Sorter             | O(log² n) parallel | fixed | O(n log² n) sequential | O(1) | No | Parallel networks, GPU sorting networks |
| Odd-Even Merge Sort        | same as bitonic | — | — | — | Yes | Batcher's parallel sort |
| Pairwise Sorting Network   | fixed depth | — | — | O(1) | No | Best for small fixed n (hardware) |

### Non-Comparison (Integer / Radix) Sorts — beat Ω(n log n) when keys have bounded size

| Algorithm                  | Time (typical)          | Space   | Stable? | Notes |
|----------------------------|-------------------------|---------|---------|-------|
| Counting Sort              | O(n + k)                | O(k)    | Yes     | k = range; used in radix |
| Radix Sort (LSD)           | O(d(n + b))             | O(n + b)| Yes     | b = base; most practical integer sort |
| Radix Sort (MSD)           | same                    | O(n)    | Yes     | In-place variants exist |
| Bucket Sort (uniform)      | O(n) expected           | O(n)    | Yes     | With good bucket count |
| Pigeonhole Sort            | O(n + k)                | O(k)    | Yes     | Counting sort variant |
| Proxmap Sort               | O(n) expected           | O(n)    | Yes     | Adaptive bucket |
| FlashSort                  | O(n) expected           | O(n)    | No      | In-place bucket-like |
| Burstsort                  | O(n log n / w) worst    | O(n)    | Yes     | Cache-efficient string sort; fastest for strings |
| Spreadsort                 | O(n √log log n) worst   | O(n)    | Yes     | Hybrid radix + comparison (used in some libraries) |
| American Flag Sort         | O(d n)                  | O(1) aux| Yes     | In-place radix variant |

### Exotic / Theoretical / Rarely Used in Practice

| Algorithm                  | Claimed Complexity       | Notes |
|----------------------------|--------------------------|-------|
| Block Sort / WikiSort      | O(n log n), O(1) space, stable | Very complex in-place merge |
| Sqrt Sort                  | O(n √n)                  | Theoretical |
| Ultimate Sorting Algorithm (Han/Korman) | O(n log log n) comparison lower bound challenger (unpractical) |
| Ford–Johnson (Merge-Insertion) | Minimal comparisons for small n |
| Pancake Sorting            | O(n) flips               | By billiard ball / pancake flips |
| Spaghetti Sort             | O(n) parallel rods       | Joke algorithm |
| Quantum Sorting            | O(n log n) but with quantum comparisons | Theoretical |
| Bead Sort                  | O(n) or O(√n) parallel   | Physical abacus simulation |

### Sorting Algorithms Used in Major Real-World Systems (2025)

| System / Language          | Primary Sort Implementation |
|----------------------------|-----------------------------|
| C qsort()                  | glibc: introsorted dual-pivot quicksort |
| C++ std::sort              | Introsort (gcc/clang/libstdc++) |
| C++ std::stable_sort       | Merge sort |
| Rust Vec::sort             | TimSort (as of Rust 1.78) |
| Rust Vec::sort_unstable    | Pattern-defeating quicksort (ipn-sort variant) |
| Python sorted() / list.sort() | TimSort |
| Java Arrays.sort (primitives) | Dual-pivot Quicksort |
| Java Arrays.sort (objects) | TimSort |
| Go sort.Slice              | Pattern-defeating quicksort + insertion |
| Linux kernel (sort())      | Heapsort-like (simple, predictable) |
| .NET Array.Sort            | Introsort |

There is no single “complete” list—new variants appear in papers every year (e.g., learned index sorts, gpu-specific sorts like cub/sort, or powersort, grailsort, holy grail in-place stable merges). But the table above covers >99% of algorithms you will ever encounter in systems programming, competitive programming, or academic study.

If you want a deep dive into any specific one (e.g., why Rust switched to TimSort, or how ipn-sort defeats quicksort killers, or how burstsort achieves the best real-world string performance), just ask.