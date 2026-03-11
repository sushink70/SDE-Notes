# The Complete Hash Table Guide
## From First Principles to Expert-Level Mastery

---

## Table of Contents

1. [The Core Abstraction: What Is a Hash Table?](#1-the-core-abstraction)
2. [Hash Functions: The Heart of the System](#2-hash-functions)
3. [Collision Resolution Strategies](#3-collision-resolution)
4. [Load Factor, Resizing, and Amortized Analysis](#4-load-factor-and-resizing)
5. [Implementation in C, Go, and Rust](#5-implementations)
6. [Advanced Variants](#6-advanced-variants)
7. [Complexity Analysis: Full Rigor](#7-complexity-analysis)
8. [Real-World Design Decisions](#8-real-world-design)
9. [Classic DSA Problems](#9-classic-problems)

---

## 1. The Core Abstraction

### Mental Model: The Direct-Address Table

Before understanding a hash table, understand what it *replaces*.

A **direct-address table** is a simple array where you index directly by key. If your keys are integers in range `[0, U)`, you allocate an array of size `U` and do `table[key] = value`. Operations are O(1). Perfect. But if `U = 2^64`, you can't allocate that array — the universe isn't big enough.

**The fundamental problem:** Keys live in a huge universe `U`, but we only ever use a small subset `K ⊆ U` of keys. We need a way to map `U → [0, m)` where `m ≈ |K|`.

That mapping function is the **hash function**. The resulting structure is the **hash table**.

```
Universe U: { all possible strings, integers, etc. }
                        |
                   h(key) = index
                        |
                 [0][1][2][3]...[m-1]   ← hash table of size m
```

### The Three-Part Contract

Every hash table provides:
1. `insert(key, value)` — store a key-value pair
2. `search(key) → value` — retrieve a value by key
3. `delete(key)` — remove a key-value pair

The *goal* is all three in **O(1) average time**.

### Why "Average"?

Two distinct keys `k1 ≠ k2` can produce the same hash `h(k1) = h(k2)`. This is called a **collision**. By the **Pigeonhole Principle**, if `|U| > m`, collisions are *inevitable*. How we handle them determines whether we achieve O(1) average or degrade to O(n) worst.

---

## 2. Hash Functions

A hash function `h: U → {0, 1, ..., m-1}` must be:

1. **Deterministic** — same input, same output, always.
2. **Fast to compute** — ideally O(1) or O(len(key)).
3. **Uniform distribution** — outputs spread evenly across `[0, m)`.
4. **Avalanche effect** — a 1-bit change in input causes ~50% of output bits to flip.

### 2.1 The Division Method

```
h(k) = k mod m
```

**Simple but fragile.** Choose `m` carefully — avoid powers of 2 (which only use the low-order bits of `k`) and avoid composite numbers with many small factors. **Best practice: m is prime**, especially one not close to a power of 2.

### 2.2 The Multiplication Method (Knuth)

```
h(k) = floor(m * ((k * A) mod 1))
```

Where `A ∈ (0,1)` is a constant. Knuth recommends `A = (√5 - 1)/2 ≈ 0.6180339887`.

**Better than division:** works for any `m`, avoids pathological cases.

### 2.3 Polynomial Rolling Hash (for strings)

```
h(s) = (s[0]*p^(n-1) + s[1]*p^(n-2) + ... + s[n-1]*p^0) mod m
```

Common choices: `p = 31` or `p = 37` for lowercase letters, large prime `m` like `1e9+7`.

**The intuition:** Treat the string as a number in base `p`.

### 2.4 FNV-1a (Fowler-Noll-Vo)

One of the most popular hash functions for strings in systems programming:

```c
// FNV-1a 64-bit
uint64_t fnv1a_64(const char *key, size_t len) {
    uint64_t hash = 14695981039346656037ULL;  // FNV offset basis
    for (size_t i = 0; i < len; i++) {
        hash ^= (uint8_t)key[i];
        hash *= 1099511628211ULL;             // FNV prime
    }
    return hash;
}
```

**Why XOR then multiply?** XOR mixes in the byte, multiply spreads the bits. This gives excellent avalanche.

### 2.5 djb2 (Dan Bernstein)

```c
uint64_t djb2(const char *key) {
    uint64_t hash = 5381;
    int c;
    while ((c = *key++)) {
        hash = ((hash << 5) + hash) + c;  // hash * 33 + c
    }
    return hash;
}
```

`hash * 33` is fast (shift + add). Empirically excellent distribution. Simple enough to memorize.

### 2.6 MurmurHash3 / xxHash (Production-Grade)

For production systems, use **MurmurHash3** or **xxHash** — they process data in 4/8-byte blocks, use mixing constants derived from extensive testing, and achieve near-maximum throughput on modern CPUs.

**Key insight:** These functions aren't cryptographically secure (don't use for passwords), but they're *statistically excellent* and extremely fast.

### 2.7 Universal Hashing

**Problem:** For any fixed hash function `h`, an adversary can construct inputs that all collide (e.g., if they know `h`, they can pick keys `k` such that `h(k) = 0` always). This degrades to O(n).

**Solution:** Choose `h` *randomly* from a **universal family** `H` at runtime.

`H` is **universal** if for any `k1 ≠ k2`:
```
Pr_{h∈H}[h(k1) = h(k2)] ≤ 1/m
```

**Carter-Wegman universal family** (for integer keys, prime `p > |U|`):
```
h_{a,b}(k) = ((a*k + b) mod p) mod m
```
where `a ∈ {1,...,p-1}`, `b ∈ {0,...,p-1}` chosen randomly.

**Why this matters for DSA:** With universal hashing, you get *guaranteed* O(1) expected time regardless of input — even adversarial input. This is why Go and Rust randomize their hash seeds at startup.

### 2.8 The Seed/Salt Anti-DoS Pattern

```go
// Go's map uses a random seed per-process to prevent HashDoS attacks
// where attackers send crafted inputs to cause O(n) behavior
// This is why map iteration order in Go is randomized
```

```rust
// Rust's HashMap uses RandomState by default (SipHash-1-3)
// SipHash is specifically designed to be fast AND resist HashDoS
use std::collections::HashMap; // uses SipHash by default
```

---

## 3. Collision Resolution

When `h(k1) = h(k2)`, we have a collision. The two major resolution strategies:

### 3.1 Separate Chaining (Closed Addressing)

Each bucket `i` holds a **linked list** (or dynamic array) of all entries `(k, v)` where `h(k) = i`.

```
Bucket 0: → (key3, val3) → (key7, val7) → NULL
Bucket 1: → (key1, val1) → NULL
Bucket 2: NULL
Bucket 3: → (key9, val9) → NULL
```

**Operations:**
- `insert(k,v)`: Compute `i = h(k) mod m`. Prepend to list at `table[i]`. O(1).
- `search(k)`: Compute `i`. Linear scan list at `table[i]` for `k`. O(1) avg, O(n) worst.
- `delete(k)`: Compute `i`. Find and unlink from list. O(1) avg.

**Analysis:**
- Let `α = n/m` be the **load factor** (average entries per bucket).
- Expected list length = `α`.
- Expected search time = O(1 + α).
- If `m = Θ(n)`, then `α = O(1)`, giving O(1) expected.

**Advantages:**
- Simple to implement.
- Load factor can exceed 1.
- Deletion is straightforward.
- Performance degrades gracefully as load increases.

**Disadvantages:**
- Memory overhead per node (pointer + allocation).
- Poor cache performance (pointer chasing).
- External memory fragmentation.

### 3.2 Open Addressing (Closed Hashing)

All entries stored **inside** the hash table array itself. When a collision occurs, we **probe** alternate slots.

**Probe sequence:** A sequence `h(k,0), h(k,1), h(k,2), ...` of slots to try.

#### 3.2.1 Linear Probing

```
h(k, i) = (h'(k) + i) mod m
```

Probe `h'(k)`, then `h'(k)+1`, then `h'(k)+2`, ...

```c
// Search pseudocode
int search(Table *t, Key k) {
    int i = hash(k) % t->size;
    int probe = 0;
    while (t->slots[i].state != EMPTY) {
        if (t->slots[i].state == OCCUPIED && t->slots[i].key == k)
            return t->slots[i].value;
        probe++;
        i = (i + 1) % t->size;
        if (probe == t->size) return NOT_FOUND;
    }
    return NOT_FOUND;
}
```

**The clustering problem:** Occupied slots tend to cluster together (primary clustering). Long runs form around frequently-used hashes, causing later insertions to require long probes.

**But:** Linear probing has *excellent cache performance* — sequential memory access. In practice it's often the fastest strategy for `α < 0.7`.

#### 3.2.2 Quadratic Probing

```
h(k, i) = (h'(k) + c1*i + c2*i²) mod m
```

Common: `c1 = c2 = 0.5`, `m` a power of 2 → `h(k,i) = h'(k) + i*(i+1)/2 mod m`.

**Reduces primary clustering** but suffers from **secondary clustering** — keys with the same `h'(k)` follow identical probe sequences.

**Important constraint:** Not all slots are guaranteed to be probed unless `m` is chosen carefully. With `m = 2^k` and probe `h + i*(i+1)/2`, you get exactly `m` distinct probes (a permutation of all slots).

#### 3.2.3 Double Hashing

```
h(k, i) = (h1(k) + i * h2(k)) mod m
```

`h2(k)` must be *relatively prime* to `m`. If `m` is prime, any `h2(k) ∈ {1,...,m-1}` works.

**Eliminates both clustering forms** — each key gets a unique probe stride.

**Best theoretical distribution** among open addressing schemes.

```c
// Double hashing
int probe(int key, int i, int m) {
    int h1 = key % m;
    int h2 = 1 + (key % (m - 1));  // guarantees h2 in [1, m-1]
    return (h1 + i * h2) % m;
}
```

#### 3.2.4 The Deletion Problem in Open Addressing

**Critical insight:** You *cannot* simply mark a deleted slot as EMPTY — that would break search chains!

**Example:**
```
Insert A → slot 0
Insert B → h(B)=0, collides, probes → slot 1
Delete A → mark slot 0 as EMPTY
Search B → checks slot 0 (EMPTY), stops → B not found! BUG!
```

**Solution:** Use a **tombstone** marker (`DELETED` state). Search skips tombstones but continues. Insert can reuse tombstone slots.

```c
typedef enum { EMPTY, OCCUPIED, DELETED } SlotState;

typedef struct {
    Key key;
    Value value;
    SlotState state;
} Slot;
```

**The tombstone accumulation problem:** Many deletions fill the table with tombstones, degrading performance. **Solution:** Rebuild the table when tombstone ratio is too high.

### 3.3 Robin Hood Hashing

**Brilliant insight:** Reduce variance in probe lengths by "stealing from the rich to give to the poor."

**Definition:** Each element's **displacement** (DIB = Distance from Initial Bucket) = how far it is from its ideal slot.

**Robin Hood rule:** When inserting element `k` at probe position `i`, if `k`'s DIB is *greater* than the resident element's DIB, **evict** the resident, continue inserting `k`'s old resident.

```
Insert sequence example:
Insert A: h(A)=0, slot 0 free → place A at slot 0, DIB=0
Insert B: h(B)=0, slot 0 taken (A, DIB=0), B DIB=1 > A DIB=0 → EVICT A
  Place B at slot 0 (DIB=0? No, B's DIB=0 now)
  
Actually let's redo:
Insert C: h(C)=0, probe 0 → A(DIB=0), C's DIB=1 > 0 → evict A
  Place C at slot 0... wait, this replaces A
  
The correct algorithm:
When probing slot i for key k with DIB d_k:
  if slot is EMPTY → insert k here with DIB=d_k
  if slot has key j with DIB d_j:
    if d_k > d_j:   (k is "poorer" = further from home)
      swap k with j (now inserting j)
      d_k = d_j (the evicted element takes its DIB)
    continue probing
```

**Result:** The maximum DIB across all elements is minimized. The variance of probe lengths is dramatically reduced.

**Advantage over basic linear probing:**
- O(ln n) worst-case expected probe length (vs O(log n / log log n) for standard)
- Lookup can be terminated *early*: if current probe position DIB > element's expected DIB, it's not there.

```c
// Robin Hood lookup termination
int search(Table *t, Key k) {
    int i = hash(k) % t->size;
    int dib = 0;
    while (true) {
        if (t->slots[i].state == EMPTY) return NOT_FOUND;
        if (t->slots[i].dib < dib) return NOT_FOUND;  // Early exit!
        if (t->slots[i].key == k) return t->slots[i].value;
        i = (i + 1) % t->size;
        dib++;
    }
}
```

**Robin Hood deletion — backward shift deletion:**
Rather than tombstones, when deleting, shift subsequent elements backward:

```c
void delete(Table *t, Key k) {
    // Find k's position i
    // Then shift backward:
    int i = find_slot(t, k);
    while (true) {
        int next = (i + 1) % t->size;
        if (t->slots[next].state == EMPTY || t->slots[next].dib == 0) {
            t->slots[i].state = EMPTY;
            break;
        }
        t->slots[i] = t->slots[next];
        t->slots[i].dib--;
        i = next;
    }
}
```

**This completely eliminates tombstones!**

### 3.4 Cuckoo Hashing

**Concept:** Use *two* hash functions `h1` and `h2` and *two* tables `T1`, `T2`. Each key `k` has exactly two possible locations: `T1[h1(k)]` and `T2[h2(k)]`.

**Invariant:** Key `k` is always at either `T1[h1(k)]` or `T2[h2(k)]`. Never anywhere else.

**Lookup:** O(1) *worst case* — check exactly two locations.

**Insertion:**
```
Insert k:
  if T1[h1(k)] is empty → place k there. Done.
  if T2[h2(k)] is empty → place k there. Done.
  else: evict occupant of T1[h1(k)] (call it k')
        place k at T1[h1(k)]
        now insert k' (which displaces someone from T2, etc.)
  if cycle detected (> C*log(n) iterations) → rehash with new functions
```

**Why it works:** Expected insertion time is O(1) amortized. The "cuckoo" metaphor: like a cuckoo bird evicting eggs from a nest.

**Failure probability:** With `α < 0.5`, insertion fails (enters a cycle) with probability O(1/n). We handle this by choosing new hash functions and rehashing.

**Key property:** Maximum probe length = 2. This makes cache behavior predictable.

---

## 4. Load Factor and Resizing

### 4.1 The Load Factor α

```
α = n / m
```

Where `n` = number of stored entries, `m` = number of buckets.

**α governs everything:**
- α too low → wasted memory, poor cache utilization.
- α too high → long probe chains, O(n) operations.

**Typical thresholds:**
| Strategy | Max α before resize | Notes |
|---|---|---|
| Separate Chaining | 0.75–1.0 | JDK HashMap uses 0.75 |
| Linear Probing | 0.5–0.7 | Beyond 0.7, performance degrades sharply |
| Double Hashing | 0.7–0.8 | More forgiving than linear |
| Robin Hood | 0.9 | Very resilient due to DIB equalization |
| Cuckoo Hashing | 0.45–0.49 | Hard limit; α > 0.5 causes rehash loops |

### 4.2 Expected Probe Length (Mathematical Truth)

For **linear probing**, the expected number of probes for:
- Successful search: `(1/2)(1 + 1/(1-α))`
- Unsuccessful search: `(1/2)(1 + 1/(1-α)²)`

At `α = 0.9`:
- Successful: `(1/2)(1 + 10) = 5.5` probes
- Unsuccessful: `(1/2)(1 + 100) = 50.5` probes!

This dramatic degradation is why linear probing caps at α ≈ 0.7.

For **separate chaining** with `α = load factor`:
- Successful: `1 + α/2`
- Unsuccessful: `α`

Much more forgiving — at α = 2.0 (more entries than buckets!), unsuccessful search still only takes 2 probes.

### 4.3 Dynamic Resizing (Rehashing)

When `α > threshold`:
1. Allocate new table of size `m' = 2m` (or next prime > 2m).
2. For each entry in old table, `insert(key, value)` into new table (recomputing hash).
3. Free old table.

**Time:** O(n) for the resize operation.

**Amortized analysis:** If we double the table each time, the amortized cost per insertion is O(1).

*Proof sketch:* After resizing, we've just inserted n entries. The next resize happens after another n insertions. Cost of resize = O(n), amortized over n insertions = O(1) each. □

**But:** The O(n) resize spike is a problem for *latency-sensitive* applications.

### 4.4 Incremental Resizing

For systems with strict latency requirements (e.g., network servers, game engines):

Instead of resizing all at once, maintain **two tables** simultaneously:
- `old_table`: the existing table
- `new_table`: the larger table being built

**Every operation:**
1. Move a constant number of entries from `old_table` → `new_table`.
2. Search checks both tables.
3. Once `old_table` is empty, switch entirely to `new_table`.

**Result:** O(1) worst-case per operation, with O(1) amortized resize cost.

### 4.5 Shrinking the Table

When entries are deleted and `α < threshold_low` (e.g., 0.1), shrink the table. This prevents the situation where a large table lies nearly empty, wasting memory.

**Hysteresis:** Use different thresholds for growing and shrinking to avoid oscillation:
- Grow when `α > 0.75`
- Shrink when `α < 0.10`

---

## 5. Implementations

### 5.1 C Implementation — Separate Chaining with FNV-1a

```c
/*
 * hash_table.c
 * Separate chaining hash table with FNV-1a hash
 * Supports string keys, void* values
 * Resizes dynamically at load factor > 0.75
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

/* ── Constants ─────────────────────────────────────────────── */
#define HT_INITIAL_CAPACITY  16
#define HT_LOAD_MAX          0.75
#define HT_LOAD_MIN          0.10
#define FNV_OFFSET_BASIS_64  14695981039346656037ULL
#define FNV_PRIME_64         1099511628211ULL

/* ── Structures ─────────────────────────────────────────────── */
typedef struct Entry {
    char        *key;
    void        *value;
    struct Entry *next;
} Entry;

typedef struct {
    Entry   **buckets;
    size_t    capacity;
    size_t    count;
} HashTable;

/* ── Hash Function ──────────────────────────────────────────── */
static uint64_t fnv1a(const char *key) {
    uint64_t hash = FNV_OFFSET_BASIS_64;
    for (const unsigned char *p = (const unsigned char *)key; *p; p++) {
        hash ^= *p;
        hash *= FNV_PRIME_64;
    }
    return hash;
}

static size_t bucket_index(const HashTable *ht, const char *key) {
    /* Fibonacci hashing: multiply by golden ratio constant to spread bits
     * This helps when capacity is a power of 2 (avoids modulo artifacts) */
    uint64_t hash = fnv1a(key);
    /* For power-of-2 capacity, AND is faster than modulo */
    return (size_t)(hash & (uint64_t)(ht->capacity - 1));
}

/* ── Lifecycle ──────────────────────────────────────────────── */
HashTable *ht_create(size_t initial_capacity) {
    /* Ensure capacity is a power of 2 for fast bitwise modulo */
    size_t cap = 1;
    while (cap < initial_capacity) cap <<= 1;

    HashTable *ht = malloc(sizeof(HashTable));
    if (!ht) return NULL;

    ht->buckets = calloc(cap, sizeof(Entry *));
    if (!ht->buckets) { free(ht); return NULL; }

    ht->capacity = cap;
    ht->count    = 0;
    return ht;
}

static void free_entry_chain(Entry *e) {
    while (e) {
        Entry *next = e->next;
        free(e->key);
        free(e);
        e = next;
    }
}

void ht_destroy(HashTable *ht) {
    for (size_t i = 0; i < ht->capacity; i++)
        free_entry_chain(ht->buckets[i]);
    free(ht->buckets);
    free(ht);
}

/* ── Resize ─────────────────────────────────────────────────── */
static bool ht_resize(HashTable *ht, size_t new_capacity) {
    Entry **new_buckets = calloc(new_capacity, sizeof(Entry *));
    if (!new_buckets) return false;

    /* Rehash all existing entries */
    for (size_t i = 0; i < ht->capacity; i++) {
        Entry *e = ht->buckets[i];
        while (e) {
            Entry *next = e->next;
            /* Compute new bucket index */
            uint64_t hash = fnv1a(e->key);
            size_t   new_i = (size_t)(hash & (uint64_t)(new_capacity - 1));
            /* Prepend to new bucket (O(1) — don't maintain order) */
            e->next = new_buckets[new_i];
            new_buckets[new_i] = e;
            e = next;
        }
    }

    free(ht->buckets);
    ht->buckets  = new_buckets;
    ht->capacity = new_capacity;
    return true;
}

static void ht_maybe_resize(HashTable *ht) {
    double load = (double)ht->count / (double)ht->capacity;
    if (load > HT_LOAD_MAX) {
        ht_resize(ht, ht->capacity * 2);
    } else if (load < HT_LOAD_MIN && ht->capacity > HT_INITIAL_CAPACITY) {
        ht_resize(ht, ht->capacity / 2);
    }
}

/* ── Core Operations ────────────────────────────────────────── */
bool ht_insert(HashTable *ht, const char *key, void *value) {
    size_t  i = bucket_index(ht, key);
    Entry  *e = ht->buckets[i];

    /* Update existing key */
    for (; e; e = e->next) {
        if (strcmp(e->key, key) == 0) {
            e->value = value;
            return true;
        }
    }

    /* New entry */
    Entry *new_entry = malloc(sizeof(Entry));
    if (!new_entry) return false;

    new_entry->key   = strdup(key);
    new_entry->value = value;
    new_entry->next  = ht->buckets[i];  /* Prepend: O(1) */
    ht->buckets[i]   = new_entry;
    ht->count++;

    ht_maybe_resize(ht);
    return true;
}

void *ht_search(const HashTable *ht, const char *key) {
    size_t  i = bucket_index(ht, key);
    Entry  *e = ht->buckets[i];
    for (; e; e = e->next) {
        if (strcmp(e->key, key) == 0)
            return e->value;
    }
    return NULL;
}

bool ht_delete(HashTable *ht, const char *key) {
    size_t  i    = bucket_index(ht, key);
    Entry  *prev = NULL;
    Entry  *e    = ht->buckets[i];

    while (e) {
        if (strcmp(e->key, key) == 0) {
            if (prev) prev->next = e->next;
            else       ht->buckets[i] = e->next;
            free(e->key);
            free(e);
            ht->count--;
            ht_maybe_resize(ht);
            return true;
        }
        prev = e;
        e    = e->next;
    }
    return false;
}

/* ── Diagnostics ─────────────────────────────────────────────── */
void ht_print_stats(const HashTable *ht) {
    size_t empty = 0, max_chain = 0, total_chain = 0;
    for (size_t i = 0; i < ht->capacity; i++) {
        size_t  len = 0;
        Entry  *e   = ht->buckets[i];
        if (!e) { empty++; continue; }
        while (e) { len++; e = e->next; }
        if (len > max_chain) max_chain = len;
        total_chain += len;
    }
    size_t used = ht->capacity - empty;
    printf("HashTable Stats:\n");
    printf("  capacity:     %zu\n",  ht->capacity);
    printf("  count:        %zu\n",  ht->count);
    printf("  load_factor:  %.3f\n", (double)ht->count / ht->capacity);
    printf("  empty_buckets:%zu\n",  empty);
    printf("  used_buckets: %zu\n",  used);
    printf("  max_chain:    %zu\n",  max_chain);
    printf("  avg_chain:    %.2f\n", used ? (double)total_chain / used : 0.0);
}

/* ── Demo ────────────────────────────────────────────────────── */
int main(void) {
    HashTable *ht = ht_create(HT_INITIAL_CAPACITY);

    /* Insert 1000 entries */
    char key[32];
    for (int i = 0; i < 1000; i++) {
        snprintf(key, sizeof(key), "key_%d", i);
        ht_insert(ht, key, (void *)(intptr_t)i);
    }

    /* Search */
    void *val = ht_search(ht, "key_42");
    printf("key_42 → %ld\n", (intptr_t)val);

    /* Delete */
    ht_delete(ht, "key_42");
    val = ht_search(ht, "key_42");
    printf("key_42 after delete → %s\n", val ? "found" : "NOT FOUND");

    ht_print_stats(ht);
    ht_destroy(ht);
    return 0;
}
```

### 5.2 C Implementation — Open Addressing with Robin Hood Hashing

```c
/*
 * robin_hood.c
 * Robin Hood open-addressing hash table
 * Uses linear probing + Robin Hood displacement balancing
 * Tombstone-free deletion via backward shift
 *
 * This is architecturally closer to how high-performance tables
 * like Rust's HashMap (hashbrown) work internally.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

#define RH_INITIAL_CAPACITY  16    /* Must be power of 2 */
#define RH_LOAD_FACTOR_MAX   0.875 /* Robin Hood tolerates high load */
#define EMPTY_SLOT           UINT64_MAX

typedef struct {
    uint64_t hash;   /* Cached full hash (EMPTY_SLOT = empty) */
    char    *key;
    void    *value;
    uint32_t dib;    /* Distance from Initial Bucket */
} Slot;

typedef struct {
    Slot   *slots;
    size_t  capacity;
    size_t  count;
} RHTable;

/* ── Internals ──────────────────────────────────────────────── */
static uint64_t rh_hash(const char *key) {
    /* FNV-1a — never returns EMPTY_SLOT sentinel */
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *p = (const unsigned char *)key; *p; p++) {
        h ^= *p;
        h *= 1099511628211ULL;
    }
    return h == EMPTY_SLOT ? h - 1 : h;
}

static inline size_t rh_desired(const RHTable *t, uint64_t hash) {
    return (size_t)(hash & (uint64_t)(t->capacity - 1));
}

static void rh_insert_slot(RHTable *t, Slot incoming);

static bool rh_resize(RHTable *t, size_t new_cap) {
    Slot *old_slots    = t->slots;
    size_t old_capacity = t->capacity;

    t->slots = calloc(new_cap, sizeof(Slot));
    if (!t->slots) { t->slots = old_slots; return false; }

    /* Mark all new slots empty */
    for (size_t i = 0; i < new_cap; i++)
        t->slots[i].hash = EMPTY_SLOT;

    t->capacity = new_cap;
    t->count    = 0;

    /* Re-insert all old entries */
    for (size_t i = 0; i < old_capacity; i++) {
        if (old_slots[i].hash != EMPTY_SLOT) {
            Slot s = old_slots[i];
            s.dib  = 0;
            rh_insert_slot(t, s);
        }
    }

    free(old_slots);
    return true;
}

/*
 * Core Robin Hood insertion.
 * `incoming` is a Slot we want to place. We probe linearly.
 * If we find a slot with smaller DIB, we swap (Robin Hood step)
 * and continue placing the evicted slot.
 */
static void rh_insert_slot(RHTable *t, Slot incoming) {
    size_t i = rh_desired(t, incoming.hash);

    while (true) {
        if (t->slots[i].hash == EMPTY_SLOT) {
            /* Free slot: place incoming here */
            t->slots[i] = incoming;
            t->count++;
            return;
        }

        /* Slot occupied: check if we should Robin Hood */
        if (t->slots[i].dib < incoming.dib) {
            /* Evict the rich (small DIB), continue placing the evicted */
            Slot tmp    = t->slots[i];
            t->slots[i] = incoming;
            incoming    = tmp;
        }

        /* Advance probe */
        i = (i + 1) & (t->capacity - 1);
        incoming.dib++;
    }
}

/* ── Lifecycle ──────────────────────────────────────────────── */
RHTable *rh_create(void) {
    RHTable *t = malloc(sizeof(RHTable));
    if (!t) return NULL;

    t->slots = malloc(RH_INITIAL_CAPACITY * sizeof(Slot));
    if (!t->slots) { free(t); return NULL; }

    for (size_t i = 0; i < RH_INITIAL_CAPACITY; i++)
        t->slots[i].hash = EMPTY_SLOT;

    t->capacity = RH_INITIAL_CAPACITY;
    t->count    = 0;
    return t;
}

void rh_destroy(RHTable *t) {
    for (size_t i = 0; i < t->capacity; i++)
        if (t->slots[i].hash != EMPTY_SLOT)
            free(t->slots[i].key);
    free(t->slots);
    free(t);
}

/* ── Core Operations ────────────────────────────────────────── */
bool rh_insert(RHTable *t, const char *key, void *value) {
    /* Resize check BEFORE insertion */
    if ((double)(t->count + 1) / t->capacity > RH_LOAD_FACTOR_MAX) {
        if (!rh_resize(t, t->capacity * 2)) return false;
    }

    uint64_t hash = rh_hash(key);
    size_t   i    = rh_desired(t, hash);
    uint32_t dib  = 0;

    /* Check for existing key first (update path) */
    for (size_t j = i; ; j = (j + 1) & (t->capacity - 1), dib++) {
        if (t->slots[j].hash == EMPTY_SLOT) break;
        if (t->slots[j].hash == hash && strcmp(t->slots[j].key, key) == 0) {
            t->slots[j].value = value;
            return true;
        }
        if (t->slots[j].dib < dib) break; /* Robin Hood: can't be further */
    }

    /* New key: build slot and insert */
    Slot s;
    s.hash  = hash;
    s.key   = strdup(key);
    s.value = value;
    s.dib   = 0;
    rh_insert_slot(t, s);  /* count incremented inside */
    return true;
}

void *rh_search(const RHTable *t, const char *key) {
    uint64_t hash = rh_hash(key);
    size_t   i    = rh_desired(t, hash);
    uint32_t dib  = 0;

    while (true) {
        if (t->slots[i].hash == EMPTY_SLOT)   return NULL;
        if (t->slots[i].dib  < dib)           return NULL; /* Robin Hood early exit */
        if (t->slots[i].hash == hash && strcmp(t->slots[i].key, key) == 0)
            return t->slots[i].value;
        i = (i + 1) & (t->capacity - 1);
        dib++;
    }
}

/*
 * Backward-shift deletion: NO tombstones!
 * After removing an element, shift subsequent elements
 * backward if they have DIB > 0 (they're not at their ideal slot).
 */
bool rh_delete(RHTable *t, const char *key) {
    uint64_t hash = rh_hash(key);
    size_t   i    = rh_desired(t, hash);
    uint32_t dib  = 0;

    /* Find the slot */
    while (true) {
        if (t->slots[i].hash == EMPTY_SLOT) return false;
        if (t->slots[i].dib  < dib)         return false;
        if (t->slots[i].hash == hash && strcmp(t->slots[i].key, key) == 0)
            break;
        i = (i + 1) & (t->capacity - 1);
        dib++;
    }

    free(t->slots[i].key);
    t->count--;

    /* Backward shift */
    while (true) {
        size_t next = (i + 1) & (t->capacity - 1);
        /* Stop if next slot is empty OR is already at its ideal bucket */
        if (t->slots[next].hash == EMPTY_SLOT || t->slots[next].dib == 0) {
            t->slots[i].hash = EMPTY_SLOT;
            break;
        }
        t->slots[i]      = t->slots[next];
        t->slots[i].dib--;  /* Now one step closer to home */
        i = next;
    }

    return true;
}

/* ── Demo ────────────────────────────────────────────────────── */
int main(void) {
    RHTable *t = rh_create();

    char key[32];
    for (int i = 0; i < 500; i++) {
        snprintf(key, sizeof(key), "entry_%d", i);
        rh_insert(t, key, (void *)(intptr_t)(i * 10));
    }

    void *v = rh_search(t, "entry_100");
    printf("entry_100 → %ld\n", (intptr_t)v);

    rh_delete(t, "entry_100");
    v = rh_search(t, "entry_100");
    printf("After delete → %s\n", v ? "FOUND" : "NOT FOUND");

    printf("Count: %zu, Capacity: %zu, Load: %.3f\n",
           t->count, t->capacity,
           (double)t->count / t->capacity);

    rh_destroy(t);
    return 0;
}
```

### 5.3 Go Implementation — Generic Hash Map with Quadratic Probing

```go
// hashmap.go
// Generic open-addressing hash map using quadratic probing.
// Go generics (1.18+) allow type-safe implementation.
// This is an educational implementation — production code uses the
// built-in map which is implemented in runtime/map.go (Go uses
// a variant of chaining with overflow buckets + SIMD group matching).

package main

import (
	"fmt"
	"math/bits"
)

// ── Slot State ──────────────────────────────────────────────────────────────

type slotState uint8

const (
	slotEmpty   slotState = iota
	slotOccupied
	slotDeleted // tombstone for quadratic probing
)

// ── Slot ─────────────────────────────────────────────────────────────────────

type slot[K comparable, V any] struct {
	key   K
	value V
	state slotState
}

// ── HashMap ──────────────────────────────────────────────────────────────────

const (
	defaultCapacity = 16
	maxLoadFactor   = 0.65 // conservative for quadratic probing
	minLoadFactor   = 0.10
)

// HashMap is a generic open-addressing hash map.
// K must be comparable (Go's constraint for == operator).
type HashMap[K comparable, V any] struct {
	slots    []slot[K, V]
	count    int // occupied (live) entries
	deleted  int // tombstone count
	capacity int // always a power of 2
}

// NewHashMap creates a HashMap with the given initial capacity
// (rounded up to next power of 2).
func NewHashMap[K comparable, V any](initialCap int) *HashMap[K, V] {
	cap := nextPow2(initialCap)
	if cap < defaultCapacity {
		cap = defaultCapacity
	}
	return &HashMap[K, V]{
		slots:    make([]slot[K, V], cap),
		capacity: cap,
	}
}

// nextPow2 returns the smallest power of 2 >= n.
func nextPow2(n int) int {
	if n <= 1 {
		return 1
	}
	return 1 << (bits.Len(uint(n - 1)))
}

// ── Hash ─────────────────────────────────────────────────────────────────────

// hashKey uses Go's built-in hash via interface boxing.
// In production, use maphash.Hash for string keys or crypto/rand seeded hash.
// For this educational implementation we use a simple polynomial approach.
func (m *HashMap[K, V]) hashKey(key K) int {
	// We exploit the fact that Go's map uses runtime hashing internally.
	// Here we use fmt.Sprintf as a bridge — NEVER do this in production.
	// A real implementation would use reflect + unsafe or generics constraints.
	h := fnv1a(fmt.Sprintf("%v", key))
	return int(h & uint64(m.capacity-1))
}

func fnv1a(s string) uint64 {
	h := uint64(14695981039346656037)
	for i := 0; i < len(s); i++ {
		h ^= uint64(s[i])
		h *= 1099511628211
	}
	return h
}

// ── Probe Sequence ───────────────────────────────────────────────────────────

// quadraticProbe returns the i-th probe position.
// With capacity = 2^k and probe = (h + i*(i+1)/2) mod 2^k,
// this visits ALL 2^k slots exactly once (triangular number theorem).
func (m *HashMap[K, V]) probe(h, i int) int {
	// Triangular probe: h + 0, h+1, h+3, h+6, h+10, ...
	return (h + (i*i+i)/2) & (m.capacity - 1)
}

// ── Core Operations ──────────────────────────────────────────────────────────

// Set inserts or updates key → value. O(1) amortized.
func (m *HashMap[K, V]) Set(key K, value V) {
	m.maybeGrow()

	h := m.hashKey(key)
	firstTombstone := -1

	for i := 0; i < m.capacity; i++ {
		idx := m.probe(h, i)
		s := &m.slots[idx]

		switch s.state {
		case slotEmpty:
			// Insert here (or at first tombstone if we passed one)
			if firstTombstone != -1 {
				idx = firstTombstone
				m.deleted-- // reusing tombstone
			}
			m.slots[idx] = slot[K, V]{key: key, value: value, state: slotOccupied}
			m.count++
			return

		case slotDeleted:
			// Record first tombstone for potential insertion
			if firstTombstone == -1 {
				firstTombstone = idx
			}

		case slotOccupied:
			if s.key == key {
				// Update existing
				s.value = value
				return
			}
		}
	}

	// Should never reach here if load factor is maintained
	panic("hash table is full — this should not happen")
}

// Get retrieves the value for key. Returns (value, true) if found.
// O(1) average.
func (m *HashMap[K, V]) Get(key K) (V, bool) {
	h := m.hashKey(key)
	for i := 0; i < m.capacity; i++ {
		idx := m.probe(h, i)
		s := &m.slots[idx]

		switch s.state {
		case slotEmpty:
			var zero V
			return zero, false // Chain broken — definitely not present
		case slotOccupied:
			if s.key == key {
				return s.value, true
			}
		case slotDeleted:
			// Skip tombstone, keep probing
		}
	}
	var zero V
	return zero, false
}

// Delete removes key from the map. Returns true if key was present.
// Uses tombstones. O(1) average.
func (m *HashMap[K, V]) Delete(key K) bool {
	h := m.hashKey(key)
	for i := 0; i < m.capacity; i++ {
		idx := m.probe(h, i)
		s := &m.slots[idx]

		switch s.state {
		case slotEmpty:
			return false
		case slotOccupied:
			if s.key == key {
				s.state = slotDeleted
				m.count--
				m.deleted++
				m.maybeShrink()
				return true
			}
		}
	}
	return false
}

// Len returns the number of live entries.
func (m *HashMap[K, V]) Len() int { return m.count }

// ── Resizing ─────────────────────────────────────────────────────────────────

func (m *HashMap[K, V]) loadFactor() float64 {
	// Count BOTH live + deleted as "used" for probing purposes
	return float64(m.count+m.deleted) / float64(m.capacity)
}

func (m *HashMap[K, V]) maybeGrow() {
	if m.loadFactor() > maxLoadFactor {
		m.resize(m.capacity * 2)
	}
}

func (m *HashMap[K, V]) maybeShrink() {
	if m.capacity > defaultCapacity &&
		float64(m.count)/float64(m.capacity) < minLoadFactor {
		m.resize(m.capacity / 2)
	}
}

// resize rebuilds the table at newCap (tombstones are NOT copied).
func (m *HashMap[K, V]) resize(newCap int) {
	oldSlots := m.slots
	m.slots = make([]slot[K, V], newCap)
	m.capacity = newCap
	m.count = 0
	m.deleted = 0

	for _, s := range oldSlots {
		if s.state == slotOccupied {
			m.Set(s.key, s.value) // Re-insert (tombstones discarded)
		}
	}
}

// ── Iteration ────────────────────────────────────────────────────────────────

// Each calls fn for every live entry. Order is unspecified.
func (m *HashMap[K, V]) Each(fn func(K, V)) {
	for _, s := range m.slots {
		if s.state == slotOccupied {
			fn(s.key, s.value)
		}
	}
}

// ── Stats ─────────────────────────────────────────────────────────────────────

func (m *HashMap[K, V]) Stats() {
	fmt.Printf("HashMap<capacity=%d, count=%d, deleted=%d, load=%.3f>\n",
		m.capacity, m.count, m.deleted,
		float64(m.count)/float64(m.capacity))
}

// ── Demo ──────────────────────────────────────────────────────────────────────

func main() {
	m := NewHashMap[string, int](8)

	// Insert
	for i := 0; i < 100; i++ {
		m.Set(fmt.Sprintf("key_%d", i), i*i)
	}

	// Get
	if val, ok := m.Get("key_42"); ok {
		fmt.Printf("key_42 = %d\n", val)
	}

	// Delete
	m.Delete("key_42")
	if _, ok := m.Get("key_42"); !ok {
		fmt.Println("key_42 deleted successfully")
	}

	m.Stats()

	// Generic: works with any comparable key type
	intMap := NewHashMap[int, string](16)
	intMap.Set(1, "one")
	intMap.Set(2, "two")
	if val, ok := intMap.Get(1); ok {
		fmt.Printf("1 → %s\n", val)
	}
}
```

### 5.4 Rust Implementation — Robin Hood HashMap from Scratch

```rust
// robin_hood_map.rs
//
// A Robin Hood open-addressing HashMap in Rust.
// Demonstrates:
//   - Robin Hood displacement (DIB balancing)
//   - Backward-shift deletion (no tombstones)
//   - Generic types with trait bounds
//   - Ownership-safe design patterns
//   - How hashbrown (Rust's stdlib HashMap backend) conceptually works

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::mem;

// ── Slot ─────────────────────────────────────────────────────────────────────

/// A single slot in the Robin Hood table.
/// Uses Option to distinguish empty from occupied.
#[derive(Debug)]
enum Slot<K, V> {
    Empty,
    Occupied { key: K, value: V, dib: usize },
}

impl<K, V> Slot<K, V> {
    fn is_empty(&self) -> bool {
        matches!(self, Slot::Empty)
    }
    fn dib(&self) -> usize {
        match self {
            Slot::Occupied { dib, .. } => *dib,
            Slot::Empty => 0,
        }
    }
}

// ── RobinHoodMap ─────────────────────────────────────────────────────────────

const DEFAULT_CAPACITY: usize = 16;
const MAX_LOAD: f64 = 0.875; // Robin Hood tolerates high load

pub struct RobinHoodMap<K, V> {
    slots: Vec<Slot<K, V>>,
    count: usize,
    capacity: usize, // always power of 2
}

impl<K, V> RobinHoodMap<K, V>
where
    K: Eq + Hash + Clone,
{
    pub fn new() -> Self {
        Self::with_capacity(DEFAULT_CAPACITY)
    }

    pub fn with_capacity(cap: usize) -> Self {
        let capacity = cap.next_power_of_two().max(DEFAULT_CAPACITY);
        let mut slots = Vec::with_capacity(capacity);
        for _ in 0..capacity {
            slots.push(Slot::Empty);
        }
        Self { slots, count: 0, capacity }
    }

    // ── Hashing ──────────────────────────────────────────────────────────────

    fn hash_key(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        hasher.finish() as usize
    }

    #[inline]
    fn desired_slot(&self, hash: usize) -> usize {
        hash & (self.capacity - 1)
    }

    #[inline]
    fn next_slot(&self, i: usize) -> usize {
        (i + 1) & (self.capacity - 1)
    }

    // ── Core: Insert (Robin Hood) ─────────────────────────────────────────────

    /// Insert key-value. O(1) expected.
    /// Uses Robin Hood: if current element has DIB < incoming's DIB, swap.
    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        // Grow before inserting
        if (self.count + 1) as f64 / self.capacity as f64 > MAX_LOAD {
            self.resize(self.capacity * 2);
        }

        let hash = self.hash_key(&key);
        let start = self.desired_slot(hash);

        // Check for existing key first (update path)
        {
            let mut i = start;
            let mut dib = 0;
            loop {
                match &self.slots[i] {
                    Slot::Empty => break,
                    Slot::Occupied { key: k, dib: d, .. } => {
                        if *d < dib { break; } // Robin Hood: can't be here
                        if k == &key {
                            // Update existing entry
                            let old = mem::replace(
                                &mut self.slots[i],
                                Slot::Occupied { key, value, dib: *d },
                            );
                            if let Slot::Occupied { value: v, .. } = old {
                                return Some(v);
                            }
                        }
                    }
                }
                i = self.next_slot(i);
                dib += 1;
            }
        }

        // New key: Robin Hood insertion
        let mut incoming = Slot::Occupied { key, value, dib: 0 };
        let mut i = start;

        loop {
            match &self.slots[i] {
                Slot::Empty => {
                    self.slots[i] = incoming;
                    self.count += 1;
                    return None;
                }
                Slot::Occupied { dib: resident_dib, .. } => {
                    let rid = *resident_dib;
                    let inc_dib = incoming.dib();

                    if inc_dib > rid {
                        // Robin Hood: swap (steal from the "rich" slot)
                        mem::swap(&mut self.slots[i], &mut incoming);
                    }
                }
            }

            // Advance DIB of incoming
            if let Slot::Occupied { ref mut dib, .. } = incoming {
                *dib += 1;
            }
            i = self.next_slot(i);
        }
    }

    // ── Core: Get ────────────────────────────────────────────────────────────

    /// Retrieve value by key. O(1) expected.
    /// Robin Hood early exit: if probe DIB > slot DIB, key not present.
    pub fn get(&self, key: &K) -> Option<&V> {
        let hash = self.hash_key(key);
        let mut i = self.desired_slot(hash);
        let mut dib = 0;

        loop {
            match &self.slots[i] {
                Slot::Empty => return None,
                Slot::Occupied { key: k, value: v, dib: d } => {
                    if *d < dib { return None; } // Early Robin Hood exit
                    if k == key  { return Some(v); }
                }
            }
            i = self.next_slot(i);
            dib += 1;
        }
    }

    pub fn get_mut(&mut self, key: &K) -> Option<&mut V> {
        let hash = self.hash_key(key);
        let mut i = self.desired_slot(hash);
        let mut dib = 0;
        let capacity = self.capacity;

        loop {
            match &self.slots[i] {
                Slot::Empty => return None,
                Slot::Occupied { key: k, dib: d, .. } => {
                    if *d < dib { return None; }
                    if k == key { break; }
                }
            }
            i = (i + 1) & (capacity - 1);
            dib += 1;
        }

        if let Slot::Occupied { value, .. } = &mut self.slots[i] {
            Some(value)
        } else {
            None
        }
    }

    // ── Core: Remove (Backward Shift) ─────────────────────────────────────────

    /// Remove key. O(1) expected. Tombstone-free via backward shifting.
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let hash = self.hash_key(key);
        let mut i = self.desired_slot(hash);
        let mut dib = 0;

        // Find the slot
        let found = loop {
            match &self.slots[i] {
                Slot::Empty => return None,
                Slot::Occupied { key: k, dib: d, .. } => {
                    if *d < dib { return None; }
                    if k == key { break i; }
                }
            }
            i = self.next_slot(i);
            dib += 1;
        };

        // Extract old value
        let old_value = match mem::replace(&mut self.slots[found], Slot::Empty) {
            Slot::Occupied { value, .. } => value,
            _ => unreachable!(),
        };
        self.count -= 1;

        // Backward shift: pull subsequent elements back one position
        let mut current = found;
        loop {
            let next = self.next_slot(current);
            match &self.slots[next] {
                Slot::Empty => break,
                Slot::Occupied { dib: d, .. } if *d == 0 => break, // at ideal slot
                Slot::Occupied { .. } => {
                    // Move next → current, decrease its DIB by 1
                    let mut moved = mem::replace(&mut self.slots[next], Slot::Empty);
                    if let Slot::Occupied { ref mut dib, .. } = moved {
                        *dib -= 1;
                    }
                    self.slots[current] = moved;
                    current = next;
                }
            }
        }

        Some(old_value)
    }

    // ── Resize ───────────────────────────────────────────────────────────────

    fn resize(&mut self, new_cap: usize) {
        let new_cap = new_cap.next_power_of_two();
        let mut new_map = RobinHoodMap::with_capacity(new_cap);

        // Drain all slots and re-insert into new map
        let old_slots = mem::replace(
            &mut self.slots,
            (0..new_cap).map(|_| Slot::Empty).collect(),
        );
        self.capacity = new_cap;
        self.count = 0;

        for slot in old_slots {
            if let Slot::Occupied { key, value, .. } = slot {
                new_map.insert(key, value);
            }
        }

        *self = new_map;
    }

    // ── Query ─────────────────────────────────────────────────────────────────

    pub fn len(&self) -> usize { self.count }
    pub fn is_empty(&self) -> bool { self.count == 0 }
    pub fn contains_key(&self, key: &K) -> bool { self.get(key).is_some() }

    pub fn load_factor(&self) -> f64 {
        self.count as f64 / self.capacity as f64
    }

    // ── Iteration ─────────────────────────────────────────────────────────────

    pub fn iter(&self) -> impl Iterator<Item = (&K, &V)> {
        self.slots.iter().filter_map(|s| {
            if let Slot::Occupied { key, value, .. } = s {
                Some((key, value))
            } else {
                None
            }
        })
    }

    // ── Diagnostics ───────────────────────────────────────────────────────────

    pub fn stats(&self) {
        let mut max_dib = 0usize;
        let mut total_dib = 0usize;
        for slot in &self.slots {
            if let Slot::Occupied { dib, .. } = slot {
                max_dib = max_dib.max(*dib);
                total_dib += dib;
            }
        }
        let avg_dib = if self.count > 0 {
            total_dib as f64 / self.count as f64
        } else {
            0.0
        };

        println!("RobinHoodMap {{ capacity: {}, count: {}, load: {:.3}, max_dib: {}, avg_dib: {:.2} }}",
            self.capacity, self.count, self.load_factor(), max_dib, avg_dib);
    }
}

// ── Entry API (like std HashMap) ──────────────────────────────────────────────

impl<K, V> RobinHoodMap<K, V>
where
    K: Eq + Hash + Clone,
    V: Default,
{
    /// Returns a mutable reference to the value for key, inserting V::default() if absent.
    pub fn entry_or_default(&mut self, key: K) -> &mut V {
        if !self.contains_key(&key) {
            self.insert(key.clone(), V::default());
        }
        self.get_mut(&key).unwrap()
    }
}

// ── Demo ──────────────────────────────────────────────────────────────────────

fn main() {
    let mut map: RobinHoodMap<String, i64> = RobinHoodMap::new();

    // Insert 1000 entries
    for i in 0..1000i64 {
        map.insert(format!("key_{}", i), i * i);
    }

    // Get
    match map.get(&"key_42".to_string()) {
        Some(v) => println!("key_42 = {}", v),
        None    => println!("key_42 not found"),
    }

    // Remove
    map.remove(&"key_42".to_string());
    println!("After remove: contains key_42? {}", map.contains_key(&"key_42".to_string()));

    map.stats();

    // Frequency counter using entry_or_default
    let text = "the quick brown fox jumps over the lazy dog the fox";
    let mut freq: RobinHoodMap<String, i64> = RobinHoodMap::new();
    for word in text.split_whitespace() {
        *freq.entry_or_default(word.to_string()) += 1;
    }
    for (word, count) in freq.iter() {
        if *count > 1 {
            println!("'{}' appears {} times", word, count);
        }
    }
}
```

---

## 6. Advanced Variants

### 6.1 Swiss Table (hashbrown — Rust's stdlib backend)

The most important modern hash table design. Used in Rust's `std::collections::HashMap`, Abseil's `absl::flat_hash_map`, and others.

**Key insight:** Use SIMD (Single Instruction Multiple Data) to check 16 slots simultaneously.

**Structure:**
```
Groups of 16 slots:
[ctrl_0 | ctrl_1 | ... | ctrl_15 | key_0 | val_0 | key_1 | val_1 | ...]
 ↑─── 16-byte control byte array ───↑   ↑─── 16 key-value pairs ────↑
```

**Control byte `ctrl[i]`:**
- `0xFF` (0b11111111): slot is empty
- `0x80` (0b10000000): slot has tombstone
- `0b0HHHHHHH`: slot is occupied, H = top 7 bits of hash

**Lookup algorithm:**
1. Compute `hash(key)`.
2. Use low bits to find group index.
3. Use top 7 bits as `h2 = hash >> 57`.
4. SIMD-compare 16 control bytes against `h2` simultaneously.
5. Get a bitmask of candidates (typically 0 or 1 match).
6. For each candidate, do full key equality check.

**Why this is brilliant:**
- 16 slots probed per memory fetch (fits in L1 cache line).
- SIMD comparison: 16 potential matches checked in 1–2 CPU instructions.
- False positive rate: only 1/128 ≈ 0.78% (7-bit fingerprint).
- Cache-friendly: all control bytes for a group are contiguous.

### 6.2 Cuckoo Hashing — Detail

```go
// Cuckoo hash table: O(1) worst-case lookup
// Two tables, two hash functions
// Every key is at exactly T1[h1(k)] or T2[h2(k)]

package main

import "fmt"

const (
    cuckooSize    = 1024
    cuckooMaxKick = 500 // Max evictions before rehash
)

type CuckooTable struct {
    t1, t2 [cuckooSize]struct{ key string; val int; occupied bool }
}

func (c *CuckooTable) h1(key string) int {
    h := fnv1aStr(key)
    return int(h) & (cuckooSize - 1)
}

func (c *CuckooTable) h2(key string) int {
    // Different seed for second hash
    h := fnv1aStr(key + "_salt")
    return int(h) & (cuckooSize - 1)
}

func fnv1aStr(s string) uint64 {
    h := uint64(14695981039346656037)
    for _, b := range []byte(s) {
        h ^= uint64(b)
        h *= 1099511628211
    }
    return h
}

func (c *CuckooTable) Get(key string) (int, bool) {
    // O(1) worst case: check exactly 2 locations
    if s := c.t1[c.h1(key)]; s.occupied && s.key == key {
        return s.val, true
    }
    if s := c.t2[c.h2(key)]; s.occupied && s.key == key {
        return s.val, true
    }
    return 0, false
}

func (c *CuckooTable) Set(key string, val int) bool {
    // Check if already exists
    if _, ok := c.Get(key); ok {
        i1 := c.h1(key)
        if c.t1[i1].key == key { c.t1[i1].val = val; return true }
        i2 := c.h2(key)
        c.t2[i2].val = val
        return true
    }

    k, v := key, val
    for i := 0; i < cuckooMaxKick; i++ {
        // Try table 1
        i1 := c.h1(k)
        if !c.t1[i1].occupied {
            c.t1[i1] = struct{ key string; val int; occupied bool }{k, v, true}
            return true
        }
        // Evict from table 1
        k, v, c.t1[i1] = c.t1[i1].key, c.t1[i1].val,
            struct{ key string; val int; occupied bool }{k, v, true}

        // Try table 2
        i2 := c.h2(k)
        if !c.t2[i2].occupied {
            c.t2[i2] = struct{ key string; val int; occupied bool }{k, v, true}
            return true
        }
        // Evict from table 2
        k, v, c.t2[i2] = c.t2[i2].key, c.t2[i2].val,
            struct{ key string; val int; occupied bool }{k, v, true}
    }

    return false // Cycle detected; caller should rehash
}
```

### 6.3 Perfect Hashing

For **static, read-only datasets** (e.g., compiler keyword tables, DNS lookup):

**Minimal Perfect Hash (MPH):** A hash function where:
- No collisions at all.
- Maps exactly `n` keys to `[0, n)`.
- O(1) lookup.

**Construction (offline, O(n) time):**
1. Choose random hash functions until a collision-free mapping is found.
2. Use algorithms like FCH or CHD to construct minimal perfect hashes.

**Use cases:** `gperf` (GNU perfect hash generator for C keywords), language runtime keyword tables, database system catalogs.

### 6.4 Consistent Hashing

For **distributed systems** (e.g., load balancing, distributed caches):

**Problem:** With a regular hash, adding/removing a server requires remapping `~n/m` of all keys. For millions of keys, this is catastrophic.

**Solution:** Map both servers and keys onto a **virtual ring** `[0, 2^32)`. Each key is handled by the **nearest server clockwise** on the ring.

**When a server is added/removed:** Only the keys in that server's arc need to be remapped. Expected `n/m` keys remapped (vs `n` for naive approach).

**Virtual nodes:** Each physical server appears at multiple positions on the ring (e.g., 150 positions) to ensure uniform distribution.

```go
// Conceptual consistent hash ring
type Ring struct {
    nodes   []int               // sorted hash positions
    mapping map[int]string      // hash → server name
}

func (r *Ring) AddServer(name string, replicas int) {
    for i := 0; i < replicas; i++ {
        h := hash(fmt.Sprintf("%s_%d", name, i))
        r.nodes = append(r.nodes, h)
        r.mapping[h] = name
        sort.Ints(r.nodes)
    }
}

func (r *Ring) GetServer(key string) string {
    h := hash(key)
    // Binary search for first node >= h (clockwise)
    i := sort.SearchInts(r.nodes, h)
    if i == len(r.nodes) { i = 0 } // wrap around ring
    return r.mapping[r.nodes[i]]
}
```

---

## 7. Complexity Analysis: Full Rigor

### 7.1 Summary Table

| Operation | Separate Chaining | Open Addressing (avg) | Open Addressing (worst) |
|---|---|---|---|
| Insert | O(1) amortized | O(1) amortized | O(n) |
| Search (success) | O(1+α) | O(1/(1-α)) | O(n) |
| Search (fail) | O(1+α) | O(1/(1-α)²) | O(n) |
| Delete | O(1+α) | O(1) amortized* | O(n) |
| Space | O(n + m) | O(m) | O(m) |

*With Robin Hood backward-shift deletion.

### 7.2 Worst-Case Guarantees

With **random/universal hashing:**
- Expected time per operation: O(1)
- With high probability (whp): O(log n / log log n) per operation for chaining

With **cuckoo hashing:**
- Lookup: O(1) worst case (exactly 2 probes)
- Insert: O(1) expected, O(log n) whp

With **Swiss Table (with SIMD):**
- Lookup: O(1) worst case in terms of cache misses (at most ceil(n/16) groups)

### 7.3 The Birthday Paradox & Collision Probability

With `m` buckets and `n` keys inserted, the expected number of collisions is approximately:
```
E[collisions] ≈ n²/(2m) = α*n/2
```

At `α = 1` and `n = 1000`: expect ~500 collisions. This is why the hash function quality matters enormously — a poor hash amplifies this.

---

## 8. Real-World Design Decisions

### 8.1 Go's Built-in Map

Go's `map` uses:
- **Hybrid of chaining with overflow buckets**
- Groups of 8 key-value pairs per bucket
- An 8-byte "tophash" array per bucket (1 byte per entry storing top 8 bits of hash)
- On overflow, chains to another bucket of 8
- **Randomized iteration** (by design — prevent reliance on order)
- **Randomized seed** at startup (HashDoS prevention)

```go
// How Go implements map internally (simplified):
// Each bucket holds 8 entries:
// [tophash_0...tophash_7][key_0...key_7][val_0...val_7][overflow*]
```

### 8.2 Rust's HashMap (hashbrown)

- **Swiss Table** layout (as described above)
- **SipHash-1-3** by default (fast AND HashDoS resistant)
- Customizable hasher via `BuildHasher` trait
- **FxHashMap** or **AHashMap** commonly used for non-adversarial data (faster)

```rust
use std::collections::HashMap;
// Default: SipHash (secure)

// For performance-critical non-adversarial use:
// use rustc_hash::FxHashMap; (used by rustc compiler itself)
// use ahash::AHashMap;       (very fast, keyed)
```

### 8.3 Choosing the Right Strategy

| Scenario | Recommendation |
|---|---|
| General use (unknown patterns) | Swiss Table / Robin Hood |
| Many deletions | Separate chaining or Robin Hood (no tombstones) |
| Read-heavy, static data | Perfect hashing |
| Memory constrained | Open addressing (no pointer overhead) |
| Distributed system | Consistent hashing |
| Security-sensitive (user input) | SipHash or keyed hash |
| Scientific/numeric workloads | Linear probing (cache performance) |
| Predictable worst-case latency | Cuckoo hashing (O(1) lookup) |

### 8.4 Common Pitfalls

1. **Mutable keys:** If a key changes after insertion, its hash changes, making it unfindable. Always use immutable keys.

2. **Float keys:** `NaN != NaN` — floats violate the equality requirement. Never use floats as keys.

3. **Poor hash functions for small integers:** `h(k) = k % m` is terrible if keys cluster (e.g., all even). Use a proper mixing function.

4. **Ignoring HashDoS:** Using a non-keyed hash in a web server that takes user-controlled input is a security vulnerability.

5. **Over-relying on O(1) amortized:** If your application has hard latency requirements, amortized O(1) resize spikes can be a problem. Use incremental resizing.

---

## 9. Classic DSA Problems

### 9.1 Two Sum — O(n) via Hash Table

```go
// Given nums and target, find indices i,j such that nums[i]+nums[j]=target
func twoSum(nums []int, target int) []int {
    seen := make(map[int]int) // value → index
    for i, n := range nums {
        complement := target - n
        if j, ok := seen[complement]; ok {
            return []int{j, i}
        }
        seen[n] = i
    }
    return nil
}
// Mental model: "For each element, ask: have I seen its complement before?"
// The hash table is a perfect structure for this O(1) membership query.
```

### 9.2 Longest Subarray with Sum K — Prefix Sum + Hash Table

```rust
fn longest_subarray_sum_k(nums: &[i64], k: i64) -> usize {
    // Prefix sum approach: sum[i..j] = prefix[j+1] - prefix[i]
    // We want prefix[j+1] - prefix[i] = k → prefix[i] = prefix[j+1] - k
    use std::collections::HashMap;
    let mut seen: HashMap<i64, usize> = HashMap::new();
    seen.insert(0, 0); // empty prefix has sum 0 at "index 0"
    let mut prefix_sum = 0i64;
    let mut max_len = 0usize;

    for (j, &n) in nums.iter().enumerate() {
        prefix_sum += n;
        let needed = prefix_sum - k;
        if let Some(&i) = seen.get(&needed) {
            max_len = max_len.max(j + 1 - i);
        }
        // Only store FIRST occurrence of each prefix sum (maximize length)
        seen.entry(prefix_sum).or_insert(j + 1);
    }
    max_len
}
```

### 9.3 Group Anagrams — O(n·k) where k = avg word length

```go
func groupAnagrams(strs []string) [][]string {
    groups := make(map[[26]int][]string)
    for _, s := range strs {
        var key [26]int
        for _, c := range s {
            key[c-'a']++
        }
        groups[key] = append(groups[key], s)
    }
    result := make([][]string, 0, len(groups))
    for _, g := range groups {
        result = append(result, g)
    }
    return result
}
// Key insight: anagrams have the same character frequency signature.
// Use that signature as the hash key — arrays are comparable in Go.
```

### 9.4 LRU Cache — Hash Table + Doubly Linked List

```go
// O(1) get and put via:
// - HashMap: key → node pointer (O(1) access)
// - Doubly linked list: maintains recency order (O(1) move-to-front)
type LRUCache struct {
    cap        int
    cache      map[int]*Node
    head, tail *Node // sentinel nodes (dummy)
}

type Node struct {
    key, val   int
    prev, next *Node
}

func Constructor(capacity int) LRUCache {
    head := &Node{}
    tail := &Node{}
    head.next = tail
    tail.prev = head
    return LRUCache{
        cap:   capacity,
        cache: make(map[int]*Node),
        head:  head,
        tail:  tail,
    }
}

func (c *LRUCache) Get(key int) int {
    if node, ok := c.cache[key]; ok {
        c.moveToFront(node)
        return node.val
    }
    return -1
}

func (c *LRUCache) Put(key, val int) {
    if node, ok := c.cache[key]; ok {
        node.val = val
        c.moveToFront(node)
        return
    }
    node := &Node{key: key, val: val}
    c.cache[key] = node
    c.addToFront(node)
    if len(c.cache) > c.cap {
        lru := c.tail.prev
        c.remove(lru)
        delete(c.cache, lru.key)
    }
}

func (c *LRUCache) moveToFront(n *Node) { c.remove(n); c.addToFront(n) }
func (c *LRUCache) addToFront(n *Node) {
    n.prev = c.head; n.next = c.head.next
    c.head.next.prev = n; c.head.next = n
}
func (c *LRUCache) remove(n *Node) { n.prev.next = n.next; n.next.prev = n.prev }
```

### 9.5 Subarray with Equal 0s and 1s — Transform + Hash Table

```rust
// Replace 0s with -1s. Now problem becomes: find longest subarray with sum 0.
// Use prefix sum + hash table (same pattern as 9.2).
fn find_max_length(nums: &[i32]) -> i32 {
    use std::collections::HashMap;
    let mut seen: HashMap<i32, i32> = HashMap::new();
    seen.insert(0, -1);
    let mut sum = 0i32;
    let mut max_len = 0i32;
    for (i, &n) in nums.iter().enumerate() {
        sum += if n == 1 { 1 } else { -1 };
        if let Some(&prev_i) = seen.get(&sum) {
            max_len = max_len.max(i as i32 - prev_i);
        } else {
            seen.insert(sum, i as i32);
        }
    }
    max_len
}
```

---

## Closing Mental Models

### The Expert's Pattern Recognition

Hash tables appear disguised in many problems. Train your eye to see these signatures:

1. **"Find if X exists"** → Hash set (O(1) membership)
2. **"Count frequency of X"** → Hash map: item → count
3. **"Find complement/pair"** → Hash map: complement → index
4. **"Group by property"** → Hash map: property → list
5. **"Longest subarray with property"** → Prefix hash + hash map
6. **"O(1) cache with eviction"** → Hash map + ordered structure (LRU/LFU)

### The Physical Intuition

A hash table is a **filing cabinet** where the drawer number is computed from the document's content. The hash function is the labeling rule. Collisions are when two documents compute to the same drawer. Good hash functions ensure drawers fill evenly. Resizing is buying a bigger cabinet and re-filing everything.

### Complexity Intuition

The reason hash tables achieve O(1) average isn't magic — it's **entropy distribution**. A good hash function maps the structured input space into uniform randomness. Uniform randomness over `m` buckets means each bucket gets `n/m` elements in expectation. When `m = Θ(n)`, that's O(1) per bucket. The "average" is over this probability distribution — on *any specific* input, collisions can cluster, but they *probably won't*.

### The One-Line Wisdom

> **"A hash table trades space for time — it uses extra memory to answer queries faster. Master this trade-off and you master 30% of interview problems."**

Great question — and it reveals a subtle but important distinction.

## What "Limited Size" Actually Means

When people say a hash table has a "limited size," they mean the **underlying array** (the bucket array) has a fixed size at any given moment. A hash table is not infinitely elastic — it is built on top of a plain array, and arrays have a fixed length.

Think of it this way. When you create a hash table, internally something like this is allocated:

```c
// The "table" is just an array of m buckets
Entry *buckets = calloc(16, sizeof(Entry *));  // m = 16 right now
```

That `16` is the current capacity. It is a concrete, finite number. You cannot store an arbitrary number of elements without consequences.

## Why This Creates a Problem

As you insert more and more keys, two things happen depending on your collision strategy:

**Separate chaining** — you *can* store more than `m` elements (chains grow), but performance degrades because every bucket's chain gets longer. At `n = 1000` elements in `m = 16` buckets, each chain has ~62 elements on average. Search is now O(62), not O(1).

**Open addressing** — you *cannot* store more than `m` elements at all. The table is physically full. Every slot is occupied. A new insertion has nowhere to go.

```
Open addressing table, m = 8, all slots filled:

Index:  [0]  [1]  [2]  [3]  [4]  [5]  [6]  [7]
Keys:   [A]  [B]  [C]  [D]  [E]  [F]  [G]  [H]
                                                  ← insert I? IMPOSSIBLE.
```

## The Load Factor is the True Constraint

The real limit isn't "you can't insert more elements" — it's that **performance collapses long before the table is physically full**. This is why the load factor `α = n/m` matters so much.

For linear probing, the expected probe length for an unsuccessful search is:

```
(1/2)(1 + 1/(1-α)²)

At α = 0.5:  (1/2)(1 + 4)   = 2.5  probes   ← acceptable
At α = 0.9:  (1/2)(1 + 100) = 50.5 probes   ← disaster
At α = 0.99: (1/2)(1 + 10000) ≈ 5000 probes ← might as well use a linked list
```

So the "limited size" problem is really: **the fixed array creates a hard ceiling on how many elements can be stored efficiently.**

## The Solution: Dynamic Resizing

This is exactly why resizing exists. When `α` crosses a threshold (typically 0.75), the table **grows itself**:

```
1. Allocate new array of size 2m
2. Rehash every existing entry into the new array
3. Free the old array
```

```go
// Before resize: m=16, n=13, α=0.81 → TOO HIGH
buckets := make([]Slot, 16)

// After resize: m=32, n=13, α=0.40 → healthy again
buckets = make([]Slot, 32)  // rehash all 13 entries here
```

The table appears to have "unlimited" size from the outside, because it keeps resizing. But at any single moment in time, it is a fixed array — that is the "limited size."

## The Key Mental Model

Think of it like a **parking lot**:

- The parking lot has `m` spaces right now — that is its current size limit.
- As it fills up, finding a free space takes longer and longer (probe length increases).
- When it's ~75% full, the city builds a new, larger parking lot and moves all the cars — that is resizing.
- The new lot has a new fixed size `2m`.

The lot is always finite. The management policy (resizing) is what makes it *feel* infinite to drivers (users of the hash table).

**Bottom line:** Every hash table has a finite array underneath. "Limited size" refers to this fixed array capacity. The load factor tells you how close you are to that limit, and dynamic resizing is how you escape it — at the cost of an occasional O(n) rebuild.

Excellent question. Most people use hash functions as a black box. Let's tear the box apart entirely.

---

## The Core Problem a Hash Function Solves

You have a key. It could be a string `"hello"`, an integer `42`, or a struct. You need to convert it into an **integer index** that:

1. Fits inside your array bounds `[0, m)`
2. Is **spread uniformly** across that range
3. Is **fast to compute**

The key insight is: **a hash function is a data compression function**. It takes an arbitrarily large input and crushes it into a small fixed-size integer. Everything that happens inside is just carefully designed bit manipulation to make that compression as *uniform* as possible.

---

## Step 1 — Everything Starts as Bytes

No matter what your key is — string, integer, struct — the hash function sees it as a **sequence of raw bytes**.

```c
// A string "hello" in memory:
// 'h'=0x68  'e'=0x65  'l'=0x6C  'l'=0x6C  'o'=0x6F
//  01101000  01100101  01101100  01101100  01101111

// An integer 12345 in memory (little-endian):
// 0x39  0x30  0x00  0x00
//  00111001  00110000  00000000  00000000
```

The hash function's job is to take these raw bytes and produce one 64-bit integer from them. That's it. Everything else is implementation strategy.

---

## Step 2 — The Two Operations: XOR and Multiply

Almost every hash function in existence uses only two primitive operations internally:

### XOR (`^`) — The Mixer

XOR is the perfect mixing operation because:
- It is its own inverse: `a ^ b ^ b = a`
- Each output bit depends on exactly two input bits
- It never loses information (bijective)
- Changes in any input bit flip exactly one output bit

```c
// XOR mixes two values with zero information loss
0b10110011
^ 0b01101010
= 0b11011001  // every bit is a combination of both inputs
```

**But XOR alone is weak.** If you only XOR all the bytes together, you get a result that doesn't depend on *position*. The strings `"ab"` and `"ba"` would produce the same hash. That's catastrophic.

### Multiply — The Avalanche Producer

Multiplication is the key weapon. When you multiply two numbers, **every bit of the output depends on every bit of both inputs**. This is called the **avalanche effect**.

```c
// Watch what multiplication does to bits:
// Input:  0b00000001  (just bit 0 set)
//       × 0b11111111  (some constant)
// Output: 0b11111111  (bit 0 now affects all 8 bits!)

// Input:  0b00000010  (just bit 1 set)
//       × 0b11111111
// Output: 0b111111110 (shifted — bit 1 affects all higher bits!)
```

**This is why multiplication causes avalanche:** a single bit change in the input cascades through all output bits. Exactly what we want — a 1-bit change in the key should randomize the output entirely.

---

## Step 3 — Walk Through FNV-1a Byte by Byte

FNV-1a is the simplest production-quality hash function. Let's run it manually on `"hi"`.

```c
uint64_t fnv1a(const char *key) {
    uint64_t hash = 14695981039346656037ULL;  // Step A: magic seed
    for (each byte b in key) {
        hash = hash ^ b;                       // Step B: XOR in the byte
        hash = hash * 1099511628211ULL;        // Step C: multiply by prime
    }
    return hash;
}
```

**Step A — The Offset Basis (seed):**
```
hash = 14695981039346656037
     = 0xCBF29CE484222325  (in hex)
```
This is not a random number — it's specifically chosen so that the *empty string* doesn't hash to zero. Starting from zero would make early iterations weak (XOR with 0 is identity, multiply by prime = 0). The seed "pre-charges" the state.

**Processing byte `'h'` = 0x68:**
```
Step B: hash = 0xCBF29CE484222325
               XOR
               0x0000000000000068
             = 0xCBF29CE48422234D   ← one byte mixed in

Step C: hash = 0xCBF29CE48422234D
               ×
               0x00000100000001B3   ← 1099511628211 in hex
             = 0xA8B8BFF9D3B22A6B   ← completely different! avalanche happened
```

**Processing byte `'i'` = 0x69:**
```
Step B: hash = 0xA8B8BFF9D3B22A6B
               XOR
               0x0000000000000069
             = 0xA8B8BFF9D3B22A02

Step C: hash = 0xA8B8BFF9D3B22A02
               ×
               0x00000100000001B3
             = 0x3D2D5F3FEF1B7DFC   ← final hash for "hi"
```

Notice: changing `'i'` to `'j'` (one bit difference) would produce a completely different 64-bit result. That's the avalanche effect working.

**Why a prime multiplier?** Primes have no small factors, so multiplication by a prime creates maximum spread across all bit positions. A power-of-2 multiplier would be a shift — only affecting high bits, leaving low bits unchanged.

---

## Step 4 — The Mixing Problem for Integers

For integer keys, the raw value itself is often a poor hash. Consider:

```c
// If m = 256 and you just do key % 256:
// key = 256  → index 0
// key = 512  → index 0
// key = 768  → index 0
// All multiples of 256 collide at index 0!
```

The integer's bits are not well-distributed. You need to **mix the bits of the integer against itself** before taking modulo.

### The Wang Hash (integer bit mixing)

```c
uint64_t wang_hash(uint64_t x) {
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
    x =  x ^ (x >> 31);
    return x;
}
```

Let's trace what happens step by step. We'll use a small example:

```
Input: x = 0xFF00FF00FF00FF00  (a structured, non-random pattern)

Round 1:
  x >> 30  = 0x0000000003FC03FC
  x ^ that = 0xFF00FF03FB03FB0C   ← high bits XORed into low region
  × prime  = 0x4A73B4DE37A8DAE4   ← multiplication spreads everything

Round 2:
  x >> 27  = 0x0000000894E769BC
  x ^ that = 0x4A73B4DE9B59A358
  × prime  = 0xE3C691B35AF80F98   ← more mixing

Round 3:
  x >> 31  = 0x0000000001C7348D
  x ^ that = 0xE3C691B35B3F3B15   ← final result
```

The output looks nothing like the input. This is what "well-distributed" means — structured inputs produce random-looking outputs.

**The XOR-shift trick explained:**
```c
x ^ (x >> 30)
```
This takes the high 34 bits of `x` and XORs them into the low 34 bits. Now the low bits "know about" the high bits. After multiplication, the high bits "know about" the low bits too. After a few rounds, **every output bit depends on every input bit.** This is the definition of a good mixing function.

---

## Step 5 — SipHash (What Rust Uses by Default)

SipHash is designed for two goals simultaneously: **speed** AND **security** (HashDoS resistance). It uses a structure called a **PRF (Pseudo-Random Function)** with a secret key.

```
SipHash-1-3 internals:
- State: four 64-bit words v0, v1, v2, v3
- Key: 128-bit secret (randomized at program start)
- Process: 1 "compression round" per 8 bytes of input, 3 "finalization rounds"
```

**One SipHash round (the "SipRound"):**

```c
void sip_round(uint64_t *v0, uint64_t *v1, uint64_t *v2, uint64_t *v3) {
    *v0 += *v1;  *v1 = rotl64(*v1, 13);  *v1 ^= *v0;  *v0 = rotl64(*v0, 32);
    *v2 += *v3;  *v3 = rotl64(*v3, 16);  *v3 ^= *v2;
    *v0 += *v3;  *v3 = rotl64(*v3, 21);  *v3 ^= *v0;
    *v2 += *v1;  *v1 = rotl64(*v1, 17);  *v1 ^= *v2;  *v2 = rotl64(*v2, 32);
}
```

Three operations dominate: **Add, Rotate, XOR** — abbreviated **ARX**. This is the same construction used in ChaCha20 (stream cipher) and BLAKE (hash function). ARX is fast because all three operations are single CPU instructions. Rotate is reversible (no information loss). Add creates carry chains (non-linearity). XOR mixes.

**Why rotation instead of shift?**

```c
// Shift LOSES bits (they fall off the end):
0b11000000 >> 2 = 0b00110000  ← top 2 bits gone forever

// Rotate PRESERVES all bits (wraps around):
rotl(0b11000000, 2) = 0b00000011  ← top 2 bits moved to bottom
```

Rotation is bijective — zero information loss. This is critical for a hash function to have good avalanche without destroying entropy.

---

## Step 6 — Reducing to Array Index

After the hash function produces a 64-bit integer, you need to map it to `[0, m)`.

### Method 1: Modulo (when m is prime)
```c
index = hash % m;
```
Works correctly for any `m`. Slow on modern CPUs (division is expensive — ~20–40 cycles).

### Method 2: Bitwise AND (when m is power of 2)
```c
index = hash & (m - 1);
```
**Lightning fast** — single instruction. But only works when `m` is a power of 2.

Why does it work? When `m = 2^k`, `m - 1` is a bitmask of k ones:
```
m = 16   → m-1 = 0b00001111
hash     = 0b10110111001011100
hash & 15= 0b00000000000001100  ← bottom 4 bits only (range 0–15)
```

**The problem:** Using only the bottom bits is risky if the hash function has weak low bits. This is why good hash functions like FNV-1a and SipHash are designed so *all* bit positions have equal entropy.

### Method 3: Fibonacci Hashing (Knuth)
```c
// Multiply by golden ratio constant, take top bits
uint64_t GOLDEN = 11400714819323198485ULL;  // 2^64 / φ
index = (hash * GOLDEN) >> (64 - log2(m));
```

This extracts the top `log2(m)` bits after multiplication by the golden ratio constant. The golden ratio has maximum irrationality — its continued fraction expansion is all 1s, meaning multiplication by it spreads bits maximally before truncation. Better distribution than simple AND for poorly distributed hashes.

---

## Step 7 — The Full Pipeline Visualized

```
Input key: "hello"
     │
     ▼
┌─────────────────────────────────────────────┐
│  BYTE EXTRACTION                             │
│  'h'=0x68 'e'=0x65 'l'=0x6C 'l'=0x6C 'o'=0x6F │
└─────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│  HASH FUNCTION (FNV-1a example)              │
│                                             │
│  seed = 0xCBF29CE484222325                  │
│  for each byte b:                           │
│      state ^= b      ← XOR mixes byte in   │
│      state *= prime  ← multiply avalanches  │
└─────────────────────────────────────────────┘
     │
     ▼
  raw_hash = 0xA430D84680AABD0B  (64-bit integer)
     │
     ▼
┌─────────────────────────────────────────────┐
│  INDEX REDUCTION                            │
│  index = raw_hash & (capacity - 1)          │
│        = 0xA430D84680AABD0B & 0xF           │
│        = 0xB = 11                           │
└─────────────────────────────────────────────┘
     │
     ▼
  Place key in bucket[11]
```

---

## Step 8 — Implementations: See the Bits Move

### C — Full FNV-1a with bit tracing

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
 * FNV-1a 64-bit: XOR then multiply, byte by byte.
 * We print the internal state after each byte so you
 * can watch the avalanche happen in real time.
 */
uint64_t fnv1a_traced(const char *key) {
    uint64_t hash = 14695981039346656037ULL;
    printf("  Initial state: %016llX\n", (unsigned long long)hash);

    for (const unsigned char *p = (const unsigned char *)key; *p; p++) {
        printf("  Processing '%c' (0x%02X):\n", *p, *p);

        hash ^= (uint64_t)(*p);
        printf("    After XOR:      %016llX\n", (unsigned long long)hash);

        hash *= 1099511628211ULL;
        printf("    After multiply: %016llX\n", (unsigned long long)hash);
    }
    return hash;
}

/*
 * Wang hash: mixes a 64-bit integer against itself.
 * For integer keys — turns structured integers into random-looking ones.
 */
uint64_t wang_hash(uint64_t x) {
    printf("  Input:          %016llX\n", (unsigned long long)x);

    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
    printf("  After round 1:  %016llX\n", (unsigned long long)x);

    x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
    printf("  After round 2:  %016llX\n", (unsigned long long)x);

    x = x ^ (x >> 31);
    printf("  After round 3:  %016llX\n", (unsigned long long)x);

    return x;
}

/*
 * Demonstrate avalanche effect:
 * Flip ONE bit in input, observe how many output bits change.
 */
void avalanche_demo(void) {
    uint64_t a = wang_hash(0x0000000000000001ULL);  // bit 0 set
    uint64_t b = wang_hash(0x0000000000000002ULL);  // bit 1 set (1-bit difference)

    uint64_t diff = a ^ b;           // bits that changed
    int changed = __builtin_popcountll(diff);  // count of changed bits

    printf("\nAvalanche test (1-bit input difference):\n");
    printf("  hash(1) = %016llX\n", (unsigned long long)a);
    printf("  hash(2) = %016llX\n", (unsigned long long)b);
    printf("  XOR diff= %016llX\n", (unsigned long long)diff);
    printf("  Bits changed: %d / 64 (ideal: ~32)\n", changed);
}

/*
 * Distribution test: hash 10000 integers, count how
 * many land in each of 16 buckets. Good hash = ~625 each.
 */
void distribution_test(void) {
    int buckets[16] = {0};
    int N = 10000;
    for (int i = 0; i < N; i++) {
        uint64_t h = wang_hash((uint64_t)i);
        buckets[h & 0xF]++;
    }
    printf("\nDistribution across 16 buckets (N=%d, ideal=%d each):\n", N, N/16);
    for (int i = 0; i < 16; i++)
        printf("  bucket[%2d]: %d\n", i, buckets[i]);
}

int main(void) {
    printf("=== FNV-1a trace for \"hi\" ===\n");
    uint64_t h = fnv1a_traced("hi");
    printf("  Final hash: %016llX\n\n", (unsigned long long)h);

    printf("=== Wang hash trace for 42 ===\n");
    wang_hash(42);

    avalanche_demo();
    distribution_test();
    return 0;
}
```

### Go — Hash internals with manual SipHash round

```go
// hash_internals.go
// Implements SipHash-2-4 from scratch to show internal ARX structure.
// This is what Rust's DefaultHasher and Go's runtime use conceptually.

package main

import (
	"encoding/binary"
	"fmt"
	"math/bits"
)

// ── ARX Primitives ────────────────────────────────────────────────────────────

// rotl64: rotate left — preserves ALL bits, just repositions them.
// This is why it's better than shift for hash mixing.
func rotl64(x uint64, k int) uint64 {
	return bits.RotateLeft64(x, k)
}

// sipRound: one round of SipHash mixing.
// Four 64-bit words (v0–v3) mix together via Add, Rotate, XOR.
// After enough rounds, every output bit depends on every input bit.
func sipRound(v0, v1, v2, v3 uint64) (uint64, uint64, uint64, uint64) {
	// Each line: ADD creates carry propagation (non-linear)
	//            ROTATE repositions bits without losing them
	//            XOR mixes two values together
	v0 += v1; v1 = rotl64(v1, 13); v1 ^= v0; v0 = rotl64(v0, 32)
	v2 += v3; v3 = rotl64(v3, 16); v3 ^= v2
	v0 += v3; v3 = rotl64(v3, 21); v3 ^= v0
	v2 += v1; v1 = rotl64(v1, 17); v1 ^= v2; v2 = rotl64(v2, 32)
	return v0, v1, v2, v3
}

// ── SipHash-1-3 ───────────────────────────────────────────────────────────────

// SipHash: keyed hash function.
// k0, k1 = 128-bit secret key (randomized per-process in real usage).
// This is what prevents HashDoS: attacker doesn't know k0,k1.
func SipHash13(key []byte, k0, k1 uint64) uint64 {
	// Initialization: XOR key material into four magic constants.
	// The constants are chosen for their bit patterns (non-zero, non-pattern).
	v0 := k0 ^ 0x736f6d6570736575 // "somepseu" in ASCII
	v1 := k1 ^ 0x646f72616e646f6d // "dorandom" in ASCII
	v2 := k0 ^ 0x6c7967656e657261 // "lygenera" in ASCII
	v3 := k1 ^ 0x7465646279746573 // "tedbytes" in ASCII

	length := len(key)

	// Process 8 bytes (one 64-bit word) at a time.
	// Each word is XORed into v3, then 1 SipRound is applied,
	// then XORed into v0. This is the "compression" step.
	for len(key) >= 8 {
		m := binary.LittleEndian.Uint64(key[:8])
		v3 ^= m
		v0, v1, v2, v3 = sipRound(v0, v1, v2, v3) // 1 compression round
		v0 ^= m
		key = key[8:]
	}

	// Handle the remaining bytes (0–7) + encode total length in top byte.
	// The length encoding prevents length-extension attacks.
	var last uint64
	last = uint64(length&0xFF) << 56 // top byte = length mod 256
	switch len(key) {
	case 7: last |= uint64(key[6]) << 48; fallthrough
	case 6: last |= uint64(key[5]) << 40; fallthrough
	case 5: last |= uint64(key[4]) << 32; fallthrough
	case 4: last |= uint64(binary.LittleEndian.Uint32(key[:4]))
	case 3: last |= uint64(key[2]) << 16; fallthrough
	case 2: last |= uint64(key[1]) << 8;  fallthrough
	case 1: last |= uint64(key[0])
	}
	v3 ^= last
	v0, v1, v2, v3 = sipRound(v0, v1, v2, v3)
	v0 ^= last

	// Finalization: 3 rounds of mixing, then XOR all four words.
	// More rounds = more diffusion = all output bits depend on all input bits.
	v2 ^= 0xFF
	v0, v1, v2, v3 = sipRound(v0, v1, v2, v3)
	v0, v1, v2, v3 = sipRound(v0, v1, v2, v3)
	v0, v1, v2, v3 = sipRound(v0, v1, v2, v3)
	return v0 ^ v1 ^ v2 ^ v3
}

// ── FNV-1a for comparison ─────────────────────────────────────────────────────

func FNV1a(data []byte) uint64 {
	h := uint64(14695981039346656037)
	for _, b := range data {
		h ^= uint64(b)
		h *= 1099511628211
	}
	return h
}

// ── Avalanche Test ────────────────────────────────────────────────────────────

// Measures: given a 1-bit change in input, how many output bits change?
// Perfect avalanche = ~50% of bits flip (32 out of 64).
func avalancheTest(hashFn func([]byte) uint64, name string) {
	fmt.Printf("\n%s avalanche test:\n", name)

	totalBitsChanged := 0
	numTests := 1000

	for t := 0; t < numTests; t++ {
		// Random-ish 8-byte input
		input := make([]byte, 8)
		for i := range input {
			input[i] = byte(t*7 + i*13)
		}

		h1 := hashFn(input)

		// Flip one random bit
		bitPos := t % 64
		bytePos := bitPos / 8
		bitMask := byte(1 << (bitPos % 8))
		input[bytePos] ^= bitMask

		h2 := hashFn(input)

		diff := h1 ^ h2
		changed := bits.OnesCount64(diff)
		totalBitsChanged += changed
	}

	avg := float64(totalBitsChanged) / float64(numTests)
	fmt.Printf("  Average bits changed per 1-bit flip: %.2f / 64 (ideal: 32.0)\n", avg)
}

// ── Distribution Test ──────────────────────────────────────────────────────────

// Hash N consecutive integers, count how many land in each of 16 buckets.
// Perfect distribution = N/16 per bucket.
func distributionTest(hashFn func([]byte) uint64, name string, N int) {
	buckets := make([]int, 16)
	buf := make([]byte, 8)
	for i := 0; i < N; i++ {
		binary.LittleEndian.PutUint64(buf, uint64(i))
		h := hashFn(buf)
		buckets[h&0xF]++
	}
	fmt.Printf("\n%s distribution (N=%d, ideal=%d per bucket):\n", name, N, N/16)
	for i, count := range buckets {
		bar := ""
		for j := 0; j < count/(N/160); j++ {
			bar += "█"
		}
		fmt.Printf("  [%2d] %s %d\n", i, bar, count)
	}
}

// ── Main ───────────────────────────────────────────────────────────────────────

func main() {
	// Fixed key for SipHash (in production this is secret/random)
	k0, k1 := uint64(0x0706050403020100), uint64(0x0f0e0d0c0b0a0908)

	sip := func(data []byte) uint64 { return SipHash13(data, k0, k1) }

	// Show what happens byte by byte
	fmt.Println("=== Hash Values ===")
	fmt.Printf("FNV1a(\"hello\"):   %016X\n", FNV1a([]byte("hello")))
	fmt.Printf("FNV1a(\"hello!\"):  %016X\n", FNV1a([]byte("hello!")))
	fmt.Printf("SipHash(\"hello\"): %016X\n", sip([]byte("hello")))
	fmt.Printf("SipHash(\"hello!\"):%016X\n", sip([]byte("hello!")))

	// One character difference → completely different output
	fmt.Println("\n=== 1-character difference ===")
	fmt.Printf("FNV1a(\"cat\"): %016X\n", FNV1a([]byte("cat")))
	fmt.Printf("FNV1a(\"bat\"): %016X\n", FNV1a([]byte("bat")))

	// Avalanche tests
	avalancheTest(FNV1a, "FNV-1a")
	avalancheTest(sip,   "SipHash-1-3")

	// Distribution tests
	distributionTest(FNV1a, "FNV-1a",    10000)
	distributionTest(sip,   "SipHash-13", 10000)

	// Show index reduction
	fmt.Println("\n=== Index Reduction ===")
	capacity := uint64(64) // power of 2
	h := FNV1a([]byte("mykey"))
	fmt.Printf("raw hash:      %016X\n", h)
	fmt.Printf("capacity-1:    %016X  (mask)\n", capacity-1)
	fmt.Printf("bucket index:  %d\n", h&(capacity-1))
}
```

### Rust — Bit-level hash dissection with avalanche measurement

```rust
// hash_internals.rs
// Dissects hash functions at the bit level.
// Shows: XOR mixing, multiplicative diffusion, rotation, avalanche.

fn main() {
    demonstrate_fnv1a();
    demonstrate_wang_hash();
    demonstrate_avalanche();
    demonstrate_distribution();
    demonstrate_index_reduction();
}

// ── FNV-1a with state tracing ──────────────────────────────────────────────────

fn fnv1a(data: &[u8]) -> u64 {
    const OFFSET: u64 = 14695981039346656037;
    const PRIME:  u64 = 1099511628211;
    let mut hash = OFFSET;
    for &byte in data {
        hash ^= byte as u64;  // XOR: mix byte into state
        hash = hash.wrapping_mul(PRIME); // multiply: avalanche
    }
    hash
}

fn fnv1a_traced(data: &[u8]) -> u64 {
    const OFFSET: u64 = 14695981039346656037;
    const PRIME:  u64 = 1099511628211;
    let mut hash = OFFSET;

    println!("  Seed:          {:016X}", hash);
    for &byte in data {
        println!("  Byte: {:3} (0x{:02X}  {:08b})", byte, byte, byte);

        hash ^= byte as u64;
        println!("  After XOR:     {:016X}", hash);

        hash = hash.wrapping_mul(PRIME);
        println!("  After multiply:{:016X}", hash);
        println!("  ---");
    }
    hash
}

fn demonstrate_fnv1a() {
    println!("=== FNV-1a Traced on b\"hi\" ===");
    let h = fnv1a_traced(b"hi");
    println!("  Final: {:016X}\n", h);
}

// ── Wang Hash: Integer Bit Mixing ─────────────────────────────────────────────
//
// Problem with using raw integers as hash keys:
//   index = key % capacity → for capacity=16, keys 0,16,32,48 all → bucket 0
//
// Solution: mix the integer's bits against itself first.

fn wang_hash(mut x: u64) -> u64 {
    // Round 1: XOR high bits into low region, then multiply
    // x >> 30 moves the top 34 bits down by 30 positions
    // XOR: now bits 0-33 contain info from bits 30-63 (the high region)
    x = x.wrapping_mul(0xBF58476D1CE4E5B9).wrapping_add(x ^ (x >> 30));
    // After multiply: ALL bits know about the high bits

    // Round 2: mix again with different shift
    x = x.wrapping_mul(0x94D049BB133111EB).wrapping_add(x ^ (x >> 27));

    // Round 3: final XOR to break any remaining patterns
    x ^ (x >> 31)
}

fn demonstrate_wang_hash() {
    println!("=== Wang Hash: Integer Bit Mixing ===");

    // Show that sequential integers get scattered
    println!("Sequential inputs → scattered outputs:");
    for i in [0u64, 1, 2, 3, 255, 256, 257, 65536] {
        println!("  wang({:6}) = {:016X}  bucket/16 = {}",
            i, wang_hash(i), wang_hash(i) % 16);
    }

    // Compare raw modulo vs wang_hash
    println!("\nRaw modulo vs Wang for multiples of 16:");
    for i in (0..10u64).map(|x| x * 16) {
        println!("  {:3} % 16 = {}   wang({:3}) % 16 = {}",
            i, i % 16, i, wang_hash(i) % 16);
    }
    println!();
}

// ── Avalanche Effect Measurement ──────────────────────────────────────────────
//
// A good hash function: flipping 1 input bit flips ~50% of output bits.
// We test this by:
//   1. Hash an input
//   2. Flip one bit
//   3. Count how many output bits differ (via XOR + popcount)

fn count_bits(x: u64) -> u32 { x.count_ones() }

fn avalanche_score(hash_fn: impl Fn(u64) -> u64, trials: usize) -> f64 {
    let mut total_bits_changed: u64 = 0;

    for t in 0..trials {
        let input = (t as u64).wrapping_mul(6364136223846793005).wrapping_add(1);

        // Flip one bit (cycle through all 64 bit positions)
        let bit = t % 64;
        let flipped = input ^ (1u64 << bit);

        let h1 = hash_fn(input);
        let h2 = hash_fn(flipped);

        total_bits_changed += count_bits(h1 ^ h2) as u64;
    }

    total_bits_changed as f64 / trials as f64
}

// Poor hash function for comparison: just multiply by a constant
fn weak_hash(x: u64) -> u64 { x.wrapping_mul(2654435761) }

// Even weaker: identity function
fn identity_hash(x: u64) -> u64 { x }

fn demonstrate_avalanche() {
    println!("=== Avalanche Effect (ideal: 32.0 bits changed per flip) ===");

    let trials = 10_000;

    let identity_score = avalanche_score(identity_hash, trials);
    let weak_score     = avalanche_score(weak_hash, trials);
    let fnv_score      = avalanche_score(|x| fnv1a(&x.to_le_bytes()), trials);
    let wang_score     = avalanche_score(wang_hash, trials);

    println!("  identity(x)=x:          {:.2} bits  ← TERRIBLE (1 bit in, 1 bit out)", identity_score);
    println!("  weak(x)=x*constant:     {:.2} bits  ← poor (only low bits affected)", weak_score);
    println!("  FNV-1a:                 {:.2} bits  ← good", fnv_score);
    println!("  Wang hash:              {:.2} bits  ← excellent", wang_score);
    println!();
}

// ── Distribution Test ──────────────────────────────────────────────────────────

fn demonstrate_distribution() {
    println!("=== Distribution across 16 buckets (N=10000, ideal=625) ===");

    let n = 10_000u64;
    let mut buckets_raw  = [0u32; 16];
    let mut buckets_wang = [0u32; 16];
    let mut buckets_fnv  = [0u32; 16];

    for i in 0..n {
        // Raw modulo: terrible for structured data
        buckets_raw[(i % 16) as usize] += 1;

        // Wang hash
        buckets_wang[(wang_hash(i) & 15) as usize] += 1;

        // FNV-1a
        let h = fnv1a(&i.to_le_bytes());
        buckets_fnv[(h & 15) as usize] += 1;
    }

    println!("  Bucket | raw i%16 | wang_hash | FNV-1a");
    println!("  -------|----------|-----------|-------");
    for i in 0..16 {
        println!("    {:2}   |  {:5}   |  {:5}    | {}",
            i, buckets_raw[i], buckets_wang[i], buckets_fnv[i]);
    }
    println!();
}

// ── Index Reduction: All Three Methods ────────────────────────────────────────

fn demonstrate_index_reduction() {
    println!("=== Index Reduction Methods ===");

    let hash = fnv1a(b"my_key_here");
    let capacity_pow2: u64 = 64; // power of 2
    let capacity_prime: u64 = 61; // prime

    println!("  Raw hash:  {:016X} = {}", hash, hash);
    println!();

    // Method 1: modulo (works for any m, slow)
    println!("  Method 1 - Modulo (any m):");
    println!("    hash % {} = {}", capacity_pow2,  hash % capacity_pow2);
    println!("    hash % {} = {}", capacity_prime, hash % capacity_prime);

    // Method 2: bitwise AND (fast, only power of 2)
    println!("\n  Method 2 - Bitwise AND (power-of-2 only):");
    println!("    hash & ({}-1) = hash & {:2} = {}",
        capacity_pow2, capacity_pow2-1, hash & (capacity_pow2-1));
    println!("    Equivalent to keeping bottom {} bits", 
        (capacity_pow2-1).count_ones());

    // Method 3: Fibonacci hashing
    println!("\n  Method 3 - Fibonacci hashing:");
    const GOLDEN: u64 = 11400714819323198485; // 2^64 / φ
    let log2_cap = 6u32; // log2(64) = 6
    let fib_index = hash.wrapping_mul(GOLDEN) >> (64 - log2_cap);
    println!("    (hash × φ_constant) >> {} = {}", 64 - log2_cap, fib_index);
    println!("    Better spread for poorly distributed hashes");
}
```

---

## The Mental Model That Unifies Everything

Here is the single insight that makes all of this click:

**A hash function is an information-destroying compression that is carefully designed to destroy information *uniformly*.**

```
Input space:  infinite (all possible strings, integers, structs)
     ↓  [compression — information is LOST here]
Output space: finite   (64-bit integer = 2^64 possible values)
     ↓  [reduction — more information LOST here]
Bucket index: tiny     (0 to m-1)
```

Since information is being destroyed, collisions are mathematically unavoidable (Pigeonhole Principle). The hash function's only job is to make sure that destruction is **uniform** — no output value is more likely than any other.

The tools to achieve uniformity are:
- **XOR** — lossless mixing, position-independent
- **Multiply** — bit spreading and non-linearity (carries)
- **Rotate** — repositioning without information loss
- **XOR-shift** — folds high bits into low bits and vice versa

Every hash function ever invented is just a different combination of these four operations applied enough times that the output is indistinguishable from randomness.