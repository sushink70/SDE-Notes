# Reservoir Sampling: A Complete Mastery Guide

Reservoir sampling is an elegant family of algorithms for randomly selecting k items from a stream of n items where n is either very large or unknown. This is a fundamental pattern in streaming algorithms and probabilistic data structures.

## I. Core Problem & Mathematical Foundation

### The Central Challenge
You're reading data from a stream where:
- You don't know the total count n in advance
- You can't store all items (memory constraint)
- You must maintain uniform random probability for each item
- You can only make one pass through the data

**Key Insight**: Traditional random sampling requires knowing n to compute `random(0, n-1)`. Reservoir sampling inverts this: it maintains probabilistic guarantees *during* the stream processing.

### Probability Proof (k=1 case)

Each item must have exactly probability 1/n of being selected:

```
Item i (where i ∈ [1,n]) is in reservoir if:
1. It was selected when encountered: P(selected at i) = 1/i
2. NOT replaced by any subsequent item j ∈ [i+1, n]

P(item i survives) = (1/i) × ∏(j=i+1 to n) P(not replaced at j)
                   = (1/i) × ∏(j=i+1 to n) (1 - 1/j)
                   = (1/i) × ∏(j=i+1 to n) ((j-1)/j)
                   = (1/i) × (i/(i+1)) × ((i+1)/(i+2)) × ... × ((n-1)/n)
                   = (1/i) × (i/n)
                   = 1/n  ✓
```

This telescoping product is the mathematical elegance at the heart of reservoir sampling.

## II. Pattern 1: Basic Reservoir (k=1)

### Algorithm (Rust)

```rust
use rand::Rng;

fn reservoir_sample_one<T>(stream: impl Iterator<Item = T>) -> Option<T> {
    let mut rng = rand::thread_rng();
    let mut reservoir: Option<T> = None;
    let mut count = 0;
    
    for item in stream {
        count += 1;
        // Replace with probability 1/count
        if rng.gen_range(0..count) == 0 {
            reservoir = Some(item);
        }
    }
    
    reservoir
}
```

**Mental Model**: Each new item "challenges" the current reservoir with decreasing probability. The champion survives probabilistically based on tournament size.

### Go Implementation

```go
func reservoirSampleOne[T any](stream <-chan T) *T {
    var reservoir *T
    count := 0
    
    for item := range stream {
        count++
        // With probability 1/count, replace reservoir
        if rand.Intn(count) == 0 {
            itemCopy := item
            reservoir = &itemCopy
        }
    }
    
    return reservoir
}
```

**Complexity Analysis**:
- Time: O(n) - single pass, O(1) per element
- Space: O(1) - constant memory regardless of stream size
- Random calls: O(n) - one per element

## III. Pattern 2: Reservoir of Size k (Algorithm R)

### The Classic Algorithm

```rust
use rand::Rng;

fn reservoir_sample_k<T: Clone>(stream: impl Iterator<Item = T>, k: usize) -> Vec<T> {
    let mut rng = rand::thread_rng();
    let mut reservoir: Vec<T> = Vec::with_capacity(k);
    
    for (i, item) in stream.enumerate() {
        if i < k {
            // Fill reservoir with first k items
            reservoir.push(item);
        } else {
            // Generate random index j in [0, i]
            let j = rng.gen_range(0..=i);
            if j < k {
                // Replace item at position j with probability k/(i+1)
                reservoir[j] = item;
            }
        }
    }
    
    reservoir
}
```

### Probability Analysis (k items)

For any subset S of size k from n items:
```
P(S is the final reservoir) = k!/(n choose k) × 1/k!
                             = 1/(n choose k)
```

Each item i has probability k/n of being in final reservoir:
```
P(item i in reservoir) = (k/i) × ∏(j=i+1 to n)(1 - k/(j×(j+1)))
                       = k/n
```

### C Implementation (Zero-Cost Abstraction)

```c
#include <stdlib.h>
#include <string.h>

typedef struct {
    void **items;
    size_t k;
    size_t count;
} Reservoir;

Reservoir* reservoir_create(size_t k) {
    Reservoir *r = malloc(sizeof(Reservoir));
    r->items = calloc(k, sizeof(void*));
    r->k = k;
    r->count = 0;
    return r;
}

void reservoir_add(Reservoir *r, void *item) {
    if (r->count < r->k) {
        r->items[r->count] = item;
    } else {
        size_t j = rand() % (r->count + 1);
        if (j < r->k) {
            r->items[j] = item;
        }
    }
    r->count++;
}

void reservoir_destroy(Reservoir *r) {
    free(r->items);
    free(r);
}
```

## IV. Pattern 3: Weighted Reservoir Sampling (Algorithm A-Res)

### Problem Evolution
Standard reservoir assumes uniform probability. What if items have weights?

**Goal**: Sample k items where P(item i selected) ∝ weight_i

### Algorithm: Generate Keys

```rust
use rand::Rng;
use std::collections::BinaryHeap;
use std::cmp::Ordering;

#[derive(Clone)]
struct WeightedItem<T> {
    item: T,
    key: f64,
}

impl<T> PartialEq for WeightedItem<T> {
    fn eq(&self, other: &Self) -> bool {
        self.key == other.key
    }
}

impl<T> Eq for WeightedItem<T> {}

impl<T> PartialOrd for WeightedItem<T> {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        // Min-heap: reverse ordering
        other.key.partial_cmp(&self.key)
    }
}

impl<T> Ord for WeightedItem<T> {
    fn cmp(&self, other: &Self) -> Ordering {
        self.partial_cmp(other).unwrap()
    }
}

fn weighted_reservoir_sample<T: Clone>(
    stream: impl Iterator<Item = (T, f64)>,
    k: usize
) -> Vec<T> {
    let mut rng = rand::thread_rng();
    let mut heap: BinaryHeap<WeightedItem<T>> = BinaryHeap::new();
    
    for (item, weight) in stream {
        // Generate key: u^(1/weight) where u ~ Uniform(0,1)
        let u: f64 = rng.gen();
        let key = u.powf(1.0 / weight);
        
        if heap.len() < k {
            heap.push(WeightedItem { item, key });
        } else if let Some(min_item) = heap.peek() {
            if key > min_item.key {
                heap.pop();
                heap.push(WeightedItem { item, key });
            }
        }
    }
    
    heap.into_iter().map(|wi| wi.item).collect()
}
```

**Mathematical Insight**: The key generation `u^(1/w)` comes from exponential distribution theory. Items with higher weights generate larger keys with higher probability.

### Go Implementation with Generics

```go
import (
    "container/heap"
    "math"
    "math/rand"
)

type WeightedItem[T any] struct {
    item T
    key  float64
}

type WeightedHeap[T any] []WeightedItem[T]

func (h WeightedHeap[T]) Len() int           { return len(h) }
func (h WeightedHeap[T]) Less(i, j int) bool { return h[i].key < h[j].key }
func (h WeightedHeap[T]) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *WeightedHeap[T]) Push(x interface{}) {
    *h = append(*h, x.(WeightedItem[T]))
}

func (h *WeightedHeap[T]) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[0 : n-1]
    return x
}

func weightedReservoirSample[T any](stream <-chan struct{item T; weight float64}, k int) []T {
    h := &WeightedHeap[T]{}
    heap.Init(h)
    
    for s := range stream {
        u := rand.Float64()
        key := math.Pow(u, 1.0/s.weight)
        
        if h.Len() < k {
            heap.Push(h, WeightedItem[T]{item: s.item, key: key})
        } else if key > (*h)[0].key {
            heap.Pop(h)
            heap.Push(h, WeightedItem[T]{item: s.item, key: key})
        }
    }
    
    result := make([]T, h.Len())
    for i := range result {
        result[i] = (*h)[i].item
    }
    return result
}
```

**Complexity**:
- Time: O(n log k) - heap operations
- Space: O(k) - only store k items
- Superior to sorting entire stream: O(n log n)

## V. Pattern 4: Distributed Reservoir Sampling

### Problem: Multiple Streams

You have m parallel streams, each with n_i items. Sample k items uniformly from all streams combined.

**Naive Approach**: Collect all, then sample → O(Σn_i) space ✗

**Optimal Approach**: Sample k from each stream, then combine

### Algorithm

```rust
use rand::Rng;

fn distributed_reservoir_sample<T: Clone>(
    streams: Vec<Vec<T>>,
    k: usize
) -> Vec<T> {
    let mut rng = rand::thread_rng();
    
    // Step 1: Sample k items from each stream
    let mut all_reservoirs: Vec<(T, usize)> = Vec::new();
    
    for stream in streams {
        let n = stream.len();
        let local_reservoir = reservoir_sample_k(stream.into_iter(), k);
        
        // Tag each item with its stream size
        for item in local_reservoir {
            all_reservoirs.push((item, n));
        }
    }
    
    // Step 2: Sample k items from combined reservoirs using weights
    // Weight = stream size (to maintain uniform probability)
    let mut final_reservoir = Vec::with_capacity(k);
    
    for (i, (item, n)) in all_reservoirs.iter().enumerate() {
        if i < k {
            final_reservoir.push(item.clone());
        } else {
            // Weighted selection based on stream size
            let j = rng.gen_range(0..=i);
            if j < k {
                final_reservoir[j] = item.clone();
            }
        }
    }
    
    final_reservoir
}
```

**Key Insight**: This maintains O(k) space per stream, total O(mk) space, much better than O(Σn_i).

## VI. Pattern 5: Time-Decayed Reservoir Sampling

### Problem: Recent Items Matter More

Sample with bias toward recent items using exponential decay.

```rust
fn time_decayed_reservoir<T: Clone>(
    stream: impl Iterator<Item = T>,
    k: usize,
    decay_rate: f64  // λ in exponential decay
) -> Vec<T> {
    let mut rng = rand::thread_rng();
    let mut heap: BinaryHeap<WeightedItem<T>> = BinaryHeap::new();
    
    for (t, item) in stream.enumerate() {
        // Weight increases exponentially with time
        let weight = (decay_rate * t as f64).exp();
        
        let u: f64 = rng.gen();
        let key = u.powf(1.0 / weight);
        
        if heap.len() < k {
            heap.push(WeightedItem { item, key });
        } else if let Some(min) = heap.peek() {
            if key > min.key {
                heap.pop();
                heap.push(WeightedItem { item, key });
            }
        }
    }
    
    heap.into_iter().map(|wi| wi.item).collect()
}
```

## VII. Advanced Pattern: L-Reservoir (Skip Optimization)

### Algorithm L: Skip Items Probabilistically

Instead of generating random number for *every* item, calculate how many items to skip.

```rust
fn reservoir_sample_optimized<T: Clone>(
    stream: impl Iterator<Item = T>,
    k: usize
) -> Vec<T> {
    let mut rng = rand::thread_rng();
    let mut reservoir: Vec<T> = Vec::with_capacity(k);
    let mut w: f64 = (rng.gen::<f64>()).ln() / (k as f64);
    let mut next: usize = k + ((rng.gen::<f64>().ln() / w).floor() as usize);
    
    for (i, item) in stream.enumerate() {
        if i < k {
            reservoir.push(item);
        } else if i == next {
            // Replace random item
            let j = rng.gen_range(0..k);
            reservoir[j] = item;
            
            // Calculate next skip
            w += (rng.gen::<f64>()).ln() / (k as f64);
            next += ((rng.gen::<f64>().ln() / w).floor() as usize) + 1;
        }
    }
    
    reservoir
}
```

**Complexity Improvement**:
- Expected random calls: O(k log(n/k)) instead of O(n)
- Critical for extremely large streams
- Same probability guarantees

## VIII. Mental Models & Problem-Solving Framework

### 1. **The Competitive Replacement Model**
Think of each new item as a challenger. Older items have "accumulated survival probability" that new items must overcome with increasingly difficult odds.

### 2. **The Shrinking Window**
As n grows, each new item's probability of selection (k/n) shrinks. The reservoir becomes increasingly stable.

### 3. **The Key Generation Paradigm**
Weighted sampling transforms probability into spatial reasoning: larger weights → larger keys → higher chance of top-k selection.

### 4. **The Streaming Constraint**
Can't go back, can't know the future. Every decision is final with imperfect information → requires probabilistic thinking.

## IX. Problem Recognition Patterns

Use reservoir sampling when you encounter:

1. **Stream with unknown size**: "sample from infinite Twitter feed"
2. **Memory constraints**: "select 1000 items from billion-item database"
3. **One-pass requirement**: "sample from unbuffered network stream"
4. **Distributed data**: "uniform sample across multiple servers"
5. **Weighted selection**: "sample URLs proportional to PageRank"
6. **Time-sensitive sampling**: "recent tweets more important"

## X. Common Pitfalls & Optimizations

### Pitfall 1: Incorrect Weight Handling
```rust
// WRONG: Linear probability
let prob = weight / total_weight;  // Requires knowing total!

// CORRECT: Key-based approach
let key = rng.gen::<f64>().powf(1.0 / weight);
```

### Pitfall 2: Modulo Bias
```rust
// WRONG: Modulo bias for large ranges
let j = (rng.gen::<u32>() % (i + 1)) as usize;

// CORRECT: Unbiased range
let j = rng.gen_range(0..=i);
```

### Pitfall 3: Clone vs Move
```rust
// Optimize for move semantics when possible
fn reservoir_sample_move<T>(stream: impl Iterator<Item = T>, k: usize) -> Vec<T> {
    // Store items directly, not clones
    // Critical for large objects
}
```

## XI. Complexity Comparison Table

| Variant | Time | Space | Random Calls | Use Case |
|---------|------|-------|--------------|----------|
| Basic (k=1) | O(n) | O(1) | O(n) | Single item |
| Algorithm R (k) | O(n) | O(k) | O(n) | Fixed k |
| Algorithm L | O(n) | O(k) | O(k log n/k) | Large streams |
| Weighted | O(n log k) | O(k) | O(n) | Priority sampling |
| Distributed | O(n) | O(mk) | O(n) | Parallel streams |

---

## Practice Philosophy

Reservoir sampling teaches you:
- **Probabilistic reasoning under constraints**
- **Trading determinism for efficiency**
- **Mathematical proof construction**
- **Stream processing patterns**

Master this, and you unlock an entire class of algorithms: Bloom filters, HyperLogLog, Count-Min Sketch—all built on similar probabilistic foundations.

Your goal isn't just to implement these—it's to develop the *intuition* to recognize when perfect accuracy isn't needed and probabilistic guarantees suffice. This is the hallmark of systems-level thinking.

Now implement each variant, prove the probabilities yourself, and measure the performance differences. True mastery comes from the doing.