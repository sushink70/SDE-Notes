# HashMap / HashSet: Complete In-Depth Guide
## Internals, Operations, Pitfalls, Concurrent Safety — Go, Rust, C

---

## 0. Four-Line Summary

A hash map is a data structure that maps keys to values via a hash function, achieving amortized O(1) insert/lookup/delete at the cost of unpredictable worst-case behavior, extra memory, and subtle correctness pitfalls. Every language runtime (Go, Rust, C stdlib) implements a distinct collision-resolution scheme with different memory layouts, growth policies, and safety guarantees. Misunderstanding the contract — especially around key mutability, iterator validity, concurrent access, and hash-flooding — leads to data races, panics, silent data loss, and CVEs. This guide takes you from hardware cache lines through algorithmic theory to production-grade implementations and security mitigations.

---

## Table of Contents

1. [First Principles: What Is a Hash Table?](#1-first-principles)
2. [Hash Functions — Theory, Properties, Attacks](#2-hash-functions)
3. [Collision Resolution Schemes](#3-collision-resolution)
4. [Load Factor, Rehashing, Growth Policies](#4-load-factor-and-rehashing)
5. [Memory Layout and Cache Behavior](#5-memory-layout)
6. [HashSet — Relationship to HashMap](#6-hashset)
7. [Go `map` Internals (runtime/map.go)](#7-go-map-internals)
8. [Rust `HashMap`/`HashSet` — hashbrown / SwissTable](#8-rust-hashmap-internals)
9. [C — Manual Open-Addressing Implementation](#9-c-implementation)
10. [Operations Reference — What You CAN Do](#10-operations-you-can-do)
11. [What You CANNOT Do — Common Mistakes & Pitfalls](#11-common-mistakes)
12. [Concurrency: Safe Patterns and Deadly Mistakes](#12-concurrency)
13. [Security — Hash Flooding, Timing Attacks, DoS](#13-security)
14. [Performance — Benchmarking & Profiling](#14-performance)
15. [Iterator Invalidation](#15-iterator-invalidation)
16. [Ordered vs Unordered Maps — When to Choose](#16-ordered-vs-unordered)
17. [Threat Model](#17-threat-model)
18. [Tests, Fuzzing, Benchmarks](#18-tests-fuzzing-benchmarks)
19. [Next 3 Steps](#19-next-3-steps)
20. [References](#20-references)

---

## 1. First Principles

### 1.1 The Core Idea

A hash table answers the question:
> "Given a universe of keys K, how do I look up an associated value in O(1) time regardless of |K|?"

The trick: reduce the key to a small integer (its hash), use that as an index into a fixed-size array.

```
key --[hash function]--> h --[mod capacity]--> bucket index --> value
```

### 1.2 The Contract

| Property              | Requirement                                        |
|-----------------------|----------------------------------------------------|
| Determinism           | `hash(k)` always returns the same value for equal `k` |
| Consistency           | If `k1 == k2` then `hash(k1) == hash(k2)`         |
| Contrapositive        | If `hash(k1) != hash(k2)` then `k1 != k2`         |
| NOT required          | If `k1 != k2` then `hash(k1) != hash(k2)` (collisions are allowed) |

### 1.3 Fundamental ASCII: Conceptual Model

```
 Keys                   Hash Table (capacity = 8)
 ─────                  ─────────────────────────────────────────
 "alice"  ──hash──> 3   slot[0]  [ empty               ]
 "bob"    ──hash──> 6   slot[1]  [ empty               ]
 "carol"  ──hash──> 3   slot[2]  [ empty               ]
 "dave"   ──hash──> 1   slot[3]  [ "alice" -> 42       ]  <─ collision
                        slot[4]  [ empty               ]     resolved by
                        slot[5]  [ empty               ]     chaining or
                        slot[6]  [ "bob"   -> 99       ]     probing
                        slot[7]  [ empty               ]
```

"carol" hashes to slot 3 (same as "alice") — this is a **collision** and must be resolved.

---

## 2. Hash Functions

### 2.1 Properties of a Good Hash Function

| Property           | Meaning                                                       |
|--------------------|---------------------------------------------------------------|
| **Uniformity**     | Distributes keys evenly across all buckets                   |
| **Avalanche**      | A 1-bit change in input changes ~50% of output bits          |
| **Speed**          | Should be computable faster than a cache miss                |
| **Determinism**    | Same key → same hash, always                                  |
| **Non-invertible** | Hard to reverse-engineer key from hash (for security)        |

### 2.2 Common Hash Functions

#### FNV-1a (Fowler–Noll–Vo)

```
offset_basis = 14695981039346656037   (64-bit)
prime        = 1099511628211

hash = offset_basis
for each byte b in key:
    hash = hash XOR b
    hash = hash * prime
```

- Fast, simple, non-cryptographic
- Used in Go's map (with random seed) for short strings
- Vulnerable to chosen-plaintext attacks without seeding

#### MurmurHash3 / xxHash

- Better avalanche than FNV
- SIMD-friendly
- Used in many hash table libraries

#### SipHash-1-3 / SipHash-2-4

```
SipHash(key, seed):
    v0 = seed ^ 0x736f6d6570736575
    v1 = seed ^ 0x646f72616e646f6d
    compress each 64-bit block with SipRound x c times
    finalize with SipRound x d times
```

- **Used by Rust's default HashMap** (via `AHasher` or `SipHasher`)
- Designed specifically to prevent hash-flooding (HashDoS)
- ~3–5 ns/key — acceptable for non-inner-loop code
- c=1,d=3 (SipHash-1-3) is Rust's default since 2018

#### AHash (Rust default since ~2020)

- Uses AES-NI hardware acceleration
- ~1 ns/key on modern x86
- Still resistant to HashDoS (seeded with random data at program start)
- Used by `hashbrown` which backs Rust's `std::collections::HashMap`

### 2.3 Hash Function Internal: Avalanche Visualization

```
Input:   "hello"         hex: 68 65 6c 6c 6f
         change 1 bit
Input:   "iello"         hex: 69 65 6c 6c 6f  (only bit 0 of byte 0)

FNV-1a("hello") = 0xa430d84680aabd0b
FNV-1a("iello") = 0x2a8b93b2e3b52bd8
                    ^^^^^^^^^^^^^^^^
XOR diff:          = 0x8e3b4bf4631b6ed3   (48 bits differ out of 64 = 75% flip)
```

Poor avalanche means clustering → performance degradation → potential DoS.

### 2.4 Why Randomized Seeds Matter (Security)

Without a random seed, an attacker who knows your hash function can craft input keys that all hash to the same bucket, turning O(1) operations into O(n) — **HashDoS attack**.

```
 Normal distribution:        Adversarial input (no seed):
 bucket[0]: 1 key            bucket[0]: 10000 keys  ← O(n) lookup
 bucket[1]: 1 key            bucket[1]: 0 keys
 bucket[2]: 2 keys           ...
 ...
```

Go seeded its maps in Go 1.0 (via `runtime.fastrand`). Rust uses `AHasher` with random seed. Never use an unseeded hash function for keys from untrusted sources.

---

## 3. Collision Resolution

### 3.1 Separate Chaining

Each bucket is a linked list (or other secondary structure). On collision, append to the list.

```
 Bucket Array                   Chains
 ──────────────────────────────────────────────────────────
 slot[0]  ──>[key="alice", v=42]──>[key="carol", v=7]──>nil
 slot[1]  ──>[key="dave",  v=9 ]──>nil
 slot[2]  nil
 slot[3]  nil
 slot[4]  ──>[key="bob",   v=99]──>nil
 ...
```

**Pros:**
- Simple to implement
- Handles high load factor gracefully
- Delete is O(chain length)
- Cache-unfriendly (pointer chasing)

**Cons:**
- Each node is a heap allocation → poor cache locality
- 64-bit pointer overhead per node
- Used by: Java `HashMap`, C++ `std::unordered_map` (most implementations)

### 3.2 Open Addressing — Linear Probing

On collision, scan forward in the array until an empty slot is found.

```
 Insert "carol" (hash=3, slot 3 occupied by "alice"):
 Probe sequence: 3 → 4 → 5 (empty, insert here)

 slot[0]  [ empty    ]
 slot[1]  [ "dave"   ]
 slot[2]  [ empty    ]
 slot[3]  [ "alice"  ]   ← "carol" hashed here, occupied
 slot[4]  [ empty    ]   ← probe +1, empty → insert "carol"
 slot[5]  [ "carol"  ]   ← Wait — actually slot[4] was empty so inserted at [4]
```

Actual linear probe insert:

```
 Capacity = 8, hash("carol") = 3

 Probe 0: slot[3] occupied ("alice") → continue
 Probe 1: slot[4] empty              → INSERT here

 slot[3]  ["alice" -> 42]
 slot[4]  ["carol" -> 7 ]   ← inserted at first empty
```

**Primary Clustering Problem:**

```
 Full run:  [A][B][C][D][ ][ ][ ][ ]
                          ^
            Next insert that hashes anywhere in [A..D]
            extends the cluster by 1, making future
            lookups for any key in that range slower
```

Linear probing suffers from primary clustering: runs of occupied slots grow, creating long probe sequences.

**Cache behavior:** Excellent — sequential memory access. Modern CPUs prefetch well.

### 3.3 Open Addressing — Quadratic Probing

Probe at offsets 1², 2², 3²... from the initial slot.

```
 Initial slot: h
 Probe sequence: h, h+1, h+4, h+9, h+16, ...
```

Reduces primary clustering but introduces secondary clustering (keys with the same hash follow the same probe sequence).

**Only works correctly when capacity is a power of 2 or prime number** — otherwise probing may not visit all slots.

### 3.4 Open Addressing — Double Hashing

Use a second hash function to compute the stride:

```
 probe(i) = (h1(key) + i * h2(key)) mod capacity
 Requirement: h2(key) must never be 0
               h2(key) must be coprime with capacity
```

Eliminates both primary and secondary clustering. More computation per probe. Cache locality worse than linear.

### 3.5 Robin Hood Hashing

A refinement of linear probing. When inserting, if the current key being inserted has traveled farther from its home slot than the existing key, **steal** the slot and continue inserting the displaced key.

```
 Concept: rich keys (close to home) give up slots to poor keys (far from home)
 
 "PSL" = Probe Sequence Length (distance from home bucket)

 Before insert of "X" (PSL=3):
 slot[5]: ["A", PSL=0]   h("A")=5
 slot[6]: ["B", PSL=0]   h("B")=6
 slot[7]: ["C", PSL=1]   h("C")=6

 Inserting "X" at slot[7] (PSL=2 since h("X")=5, want slot 5, probing to 7):
 - "C" at slot[7] has PSL=1 < our PSL=2 → steal slot[7], insert "X", continue with "C"
 
 After:
 slot[7]: ["X", PSL=2]
 slot[0]: ["C", PSL=2]   (displaced, continues probing)
```

**Why this matters:** Reduces maximum probe length. Variance in probe lengths is much lower. Makes lookup faster because you can stop early: if current slot's PSL < your probe count, the key doesn't exist.

**Used by:** Rust's old `HashMap` (before switching to SwissTable), some Redis structures.

### 3.6 SwissTable (Google, used by Rust hashbrown)

This is the current state of the art for open-addressing hashmaps.

```
 Memory layout per "group" of 16 slots (SSE2/AVX2):

 ┌────────────────────────────────────────────────────────────────┐
 │  Control bytes (16 bytes = 1 SIMD register)                    │
 │  Each byte = 1 slot's metadata                                 │
 │  ─────────────────────────────────────────────────────────     │
 │  0x80  = EMPTY                                                  │
 │  0xFE  = DELETED (tombstone)                                    │
 │  0b0xxxxxxx = FULL, where xxxxxxx = top 7 bits of hash         │
 └────────────────────────────────────────────────────────────────┘
 
 ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
 │ ctrl │ ctrl │ ctrl │ ctrl │ ctrl │ ctrl │ ctrl │ ctrl │  16 ctrl bytes
 │  [0] │  [1] │  [2] │  [3] │  [4] │  [5] │  [6] │  [7] │  (1 per slot)
 └──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘
 ┌──────────────┬──────────────┬──────────────┬──────────────┐
 │   slot[0]    │   slot[1]    │   slot[2]    │   slot[3]    │  actual
 │  (key,value) │  (key,value) │  (key,value) │  (key,value) │  data slots
 └──────────────┴──────────────┴──────────────┴──────────────┘
```

**Lookup procedure:**

```
1. Compute h = hash(key)
2. h1 = h & (capacity - 1)   // lower bits → starting bucket
3. h2 = (h >> 57) | 0x80     // top 7 bits → tag for SIMD comparison
4. Load 16 ctrl bytes starting at h1 into SIMD register
5. SIMD compare: find all positions where ctrl == h2 (candidate matches)
6. For each candidate: do full key equality check
7. If no match and no EMPTY ctrl byte found: advance to next group of 16
```

**SIMD Match in ASCII:**

```
 ctrl bytes:  [0x80][0xA3][0x80][0xA3][0xFE][0x80][0xA3][0x80]
                                                    ↑
 target h2:   0xA3

 SIMD PCMPEQB: [0x00][0xFF][0x00][0xFF][0x00][0x00][0xFF][0x00]
                       ↑           ↑                 ↑
               matches at positions 1, 3, 6 → check full keys
```

This means: **with SIMD, you check 16 slots in a single instruction**.

**Why tombstones (0xFE) instead of clearing on delete:** Clearing a slot breaks lookup chains — subsequent keys that probed past this slot would be unreachable. Tombstones preserve probe chains but are skipped on insert.

---

## 4. Load Factor and Rehashing

### 4.1 Definition

```
load_factor = number_of_entries / capacity
```

### 4.2 Impact on Performance

```
 Chaining:
 E[probe length] ≈ 1 + load_factor/2   (successful search)
 E[probe length] ≈ 1 + (load_factor²/2)  (unsuccessful search)

 Linear Probing:
 E[probes] ≈ 0.5 * (1 + 1/(1 - load_factor))   (successful)
 E[probes] ≈ 0.5 * (1 + 1/(1 - load_factor)²)  (unsuccessful)
```

At load factor 0.9, linear probing needs ~5.5 probes on average for a miss. SwissTable's SIMD groups of 16 effectively bring this down dramatically.

### 4.3 Rehashing Process

```
 State: capacity=8, entries=7, load_factor=0.875 → REHASH TRIGGERED

 Step 1: Allocate new array, capacity = 16 (2x growth)
 Step 2: For each occupied slot in old array:
             re-hash key with new modulus
             insert into new slot
 Step 3: Free old array

 Old:                        New:
 [A][B][C][D][E][F][G][ ]   [A][ ][ ][C][ ][B][ ][ ][D][ ][G][F][ ][E][ ][ ]
  0  1  2  3  4  5  6  7     0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
```

**Critical:** During rehash, ALL existing pointers/references to values inside the map are **invalidated** (memory was moved). This is why you cannot hold a reference into a HashMap while inserting.

### 4.4 Growth Policies by Language

| Runtime        | Default load factor | Growth factor | Notes                        |
|----------------|--------------------:|:-------------:|------------------------------|
| Go map         | 6.5 (overloads)    | 2x            | Uses bucket overflow chains  |
| Rust hashbrown | 0.875               | 2x            | SwissTable, shrinks at 0.25  |
| C++ unordered  | 1.0 (default)      | implementation-defined | Chaining |
| Java HashMap   | 0.75               | 2x            | Chaining, tree on depth>8    |
| Python dict    | 0.67               | 2x            | Open addressing (compact)    |

---

## 5. Memory Layout

### 5.1 Separate Chaining — Cache View

```
 Cache line (64 bytes)
 ┌──────────────────────────────────────────────────────────────┐
 │ bucket[0] bucket[1] bucket[2] ... bucket[7]                  │ ← array of pointers
 └──────────────────────────────────────────────────────────────┘
       │           │
       ▼           ▼
 ┌──────────┐  ┌──────────┐
 │ key      │  │ key      │   ← Each node = separate heap alloc
 │ value    │  │ value    │     CACHE MISS per node visited
 │ next ptr │  │ next ptr │     (pointer to next in chain)
 └──────────┘  └──────────┘
```

Every chain traversal = cache miss. On a modern CPU, an L3 cache miss costs ~100 cycles. Linear probing keeps everything in sequential memory.

### 5.2 Open Addressing — Cache View

```
 flat_array: [k0,v0][k1,v1][k2,v2][k3,v3][k4,v4][k5,v5][k6,v6][k7,v7]
              ├─────────────────────────────────────────────────────────┤
              │                   1 cache line (64 bytes)               │
              └─────────────────────────────────────────────────────────┘
              Sequential probing → hardware prefetcher kicks in → fast
```

### 5.3 SwissTable Memory Layout (Detailed)

```
 Allocation: ctrl_bytes[] + slots[] in one contiguous block

 ┌─────────────────────────────────────────────────────────┐
 │ CTRL REGION                                             │
 │ 1 byte per slot (aligned to 16 bytes for SIMD)          │
 │ [E][F][FULL:h2][E][E][FULL:h2][E][FULL:h2]...           │
 │  E=EMPTY(0x80)  F=DELETED(0xFE)  FULL=0b0xxxxxxx        │
 ├─────────────────────────────────────────────────────────┤
 │ SLOT REGION                                             │
 │ sizeof(K) + sizeof(V) per slot, slot[i] under ctrl[i]   │
 │ [  ][  ][ K | V ][  ][  ][ K | V ][  ][ K | V ]...     │
 └─────────────────────────────────────────────────────────┘
 
 Note: EMPTY/DELETED slots have UNINITIALIZED data in slot region
       (this is safe because ctrl byte gates all access)
```

Why ctrl bytes are separate from slots:
- SIMD loads 16 ctrl bytes at once (one 128-bit register)
- Full key comparison only happens for actual tag matches (rare)
- Keeps the "fast path" data tightly packed

### 5.4 Go Map Memory Layout (hmap + bmap)

```
 hmap (map header):
 ┌──────────────────────────────────────────────────────────────────┐
 │ count      int         // number of live keys                    │
 │ flags      uint8       // iterator, oldBuckets iterator flags    │
 │ B          uint8       // log2 of # of buckets (capacity = 2^B)  │
 │ noverflow  uint16      // # overflow buckets                     │
 │ hash0      uint32      // hash seed (randomized at creation)      │
 │ buckets    unsafe.Pointer  // *[2^B]bmap                         │
 │ oldbuckets unsafe.Pointer  // previous bucket array during grow  │
 │ nevacuate  uintptr     // next bucket to evacuate during grow    │
 │ extra      *mapextra                                             │
 └──────────────────────────────────────────────────────────────────┘

 bmap (one bucket, holds 8 key-value pairs):
 ┌──────────────────────────────────────────────────────────────────┐
 │ tophash [8]uint8   // top byte of hash for each slot             │
 │                    // 0 = empty, 1 = evacuated, 2+ = top hash   │
 ├──────────────────────────────────────────────────────────────────┤
 │ keys    [8]KeyType  // all 8 keys packed together                │
 ├──────────────────────────────────────────────────────────────────┤
 │ values  [8]ValType  // all 8 values packed together              │
 ├──────────────────────────────────────────────────────────────────┤
 │ overflow *bmap     // pointer to overflow bucket (chaining)      │
 └──────────────────────────────────────────────────────────────────┘
```

Go separates keys and values within a bucket to **avoid padding waste**. If keys are small (uint8) and values are large (struct{...}), packing them interleaved would waste space due to alignment. Storing all keys then all values minimizes padding.

**Go lookup path:**

```
 hash(key, h.hash0)
  → select bucket:  bucket_index = hash >> (64 - B)
  → load top hash:  top = uint8(hash >> 56)
  → scan tophash[8] for top match
  → on match: full key comparison
  → on all misses: follow overflow pointer
```

---

## 6. HashSet

### 6.1 HashSet IS a HashMap

A `HashSet<K>` is simply `HashMap<K, ()>` — a map where the value type is the unit/zero-size type.

In Rust:
```rust
// HashSet<K> is backed by HashMap<K, ()>
// The () value takes 0 bytes (ZST - zero-sized type)
// The compiler eliminates all value storage
```

In Go:
```go
// Idiomatic Go set pattern (no built-in set)
type Set[K comparable] map[K]struct{}
// struct{} is zero-sized, no allocation for values
```

### 6.2 Set Operations

```
 A = {1, 2, 3, 4, 5}
 B = {3, 4, 5, 6, 7}

 Union (A ∪ B)         = {1,2,3,4,5,6,7}   iterate A, insert all B
 Intersection (A ∩ B)  = {3,4,5}            iterate smaller, check in larger
 Difference (A - B)    = {1,2}              iterate A, keep if not in B
 Symmetric Diff        = {1,2,6,7}          (A-B) ∪ (B-A)
 Subset (A ⊆ B)        = false              all A elements in B?
```

All set operations are O(|A| + |B|) assuming O(1) HashMap operations.

---

## 7. Go `map` Internals

### 7.1 Key Constraints

In Go, only **comparable** types can be map keys. The compiler enforces this at compile time.

```go
// VALID key types:
map[int]string
map[string]int
map[[4]byte]int      // fixed-size array: comparable
map[struct{ X, Y int }]string  // struct of comparables: comparable

// INVALID key types (compile error):
map[[]byte]string    // slice: not comparable
map[map[string]int]string  // map: not comparable
map[func()]string    // func: not comparable
```

### 7.2 Zero Value Behavior

The zero value of a map is `nil`. A nil map:
- Reads return the zero value of the value type (no panic)
- Writes PANIC at runtime

```go
var m map[string]int   // nil map
v := m["key"]          // OK: returns 0
m["key"] = 1           // PANIC: assignment to entry in nil map
```

### 7.3 Make vs Literal

```go
// These are equivalent — both allocate and initialize:
m1 := make(map[string]int)
m2 := map[string]int{}

// With hint — preallocates for ~n entries, avoids rehash:
m3 := make(map[string]int, 1000)

// Literal initialization:
m4 := map[string]int{
    "a": 1,
    "b": 2,
}
```

The size hint in `make` is just a hint. Go may allocate more or less. It does NOT set a capacity ceiling.

### 7.4 Comma-OK Idiom

```go
// Without comma-ok: ambiguous zero value
v := m["missing"]   // returns 0 — was it set to 0, or missing?

// With comma-ok: unambiguous
v, ok := m["missing"]
if !ok {
    // key definitely does not exist
}
```

**Always use comma-ok when distinguishing "key not present" from "key with zero value".**

### 7.5 Iteration Order

Go randomizes map iteration order deliberately (seeded per-iteration, not per-map). This is a **security and correctness** feature — prevents programs from accidentally depending on insertion order.

```go
m := map[string]int{"a": 1, "b": 2, "c": 3}
for k, v := range m {
    fmt.Println(k, v)  // order is RANDOM every run
}
```

**To iterate in sorted order:**
```go
keys := make([]string, 0, len(m))
for k := range m {
    keys = append(keys, k)
}
sort.Strings(keys)
for _, k := range keys {
    fmt.Println(k, m[k])
}
```

### 7.6 Concurrent Access — Go's Deliberate Choice

Go maps are **NOT safe for concurrent access**. The runtime explicitly detects concurrent map reads+writes and **panics**:

```go
// This will panic with: "concurrent map read and map write"
go func() { m["a"] = 1 }()
go func() { _ = m["a"] }()
```

Go added a runtime detector (not just a race detector — it fires even without `-race`) in Go 1.6. **This is intentional** — making maps safe by default would slow down the common (single-goroutine) case.

Safe concurrent patterns:
```go
// Option 1: sync.RWMutex
type SafeMap struct {
    mu sync.RWMutex
    m  map[string]int
}

// Option 2: sync.Map (optimized for read-heavy or disjoint-key workloads)
var sm sync.Map
sm.Store("key", 42)
v, ok := sm.Load("key")
sm.LoadOrStore("key", 42)  // atomic check-then-store
sm.Delete("key")
sm.Range(func(k, v any) bool { /* ... */; return true })
```

### 7.7 Map Shrinking

**Go maps do NOT shrink.** Once a map grows to hold N entries and you delete N-1 of them, the underlying bucket array stays the same size. Memory is NOT returned to the OS.

```go
m := make(map[int]int)
for i := 0; i < 1_000_000; i++ {
    m[i] = i
}
for i := 0; i < 1_000_000; i++ {
    delete(m, i)  // removes entries, does NOT free bucket memory
}
// m is now empty but still holds ~32MB of bucket memory
```

**Workaround:** Assign a fresh map.
```go
m = make(map[int]int) // old map GC'd when no more references
```

### 7.8 Key Addressability

You **cannot take the address of a map value** in Go. This is because a map value may be relocated during rehashing.

```go
m := map[string]Point{"a": {1, 2}}
p := &m["a"]        // COMPILE ERROR: cannot take address of m["a"]
m["a"].X = 10       // COMPILE ERROR: cannot assign to m["a"].X
```

**Workaround:** Store pointers as values.
```go
m := map[string]*Point{"a": {1, 2}}
m["a"].X = 10       // OK: pointer is stable, value behind it modified
```

### 7.9 Delete During Range

In Go, it is **safe** to delete keys while ranging over a map. Deleted keys won't appear later in the iteration, but keys that were already visited won't be re-visited.

```go
// SAFE in Go:
for k, v := range m {
    if shouldDelete(v) {
        delete(m, k)  // safe during range
    }
}
```

**Inserting** during range: the new key may or may not be visited — undefined order.

---

## 8. Rust HashMap Internals

### 8.1 Backing Implementation: hashbrown

Since Rust 1.36, `std::collections::HashMap` is backed by `hashbrown`, which implements the **SwissTable** algorithm (see §3.6).

```
std::collections::HashMap<K, V, S = RandomState>
    │
    └── hashbrown::HashMap<K, V, S>
            │
            └── RawTable<(K, V)>
                    │
                    └── ctrl: *u8        (control bytes)
                    └── data: *[(K,V)]   (slots)
                    └── bucket_mask: usize
                    └── items: usize
                    └── growth_left: usize
```

### 8.2 Ownership and Borrow Rules

Rust's borrow checker enforces hashmap correctness at compile time:

```rust
use std::collections::HashMap;

let mut m: HashMap<String, Vec<i32>> = HashMap::new();
m.insert("a".into(), vec![1, 2, 3]);

// WRONG: can't have mut ref while another ref exists
let v = m.get("a").unwrap();     // immutable borrow
m.insert("b".into(), vec![4]);   // ERROR: mutable borrow while immutable exists
println!("{:?}", v);             // immutable borrow used here

// WHY: insert may rehash → reallocate → v becomes a dangling pointer
// Rust prevents this at compile time — no segfault, no UB
```

```rust
// CORRECT patterns:

// Pattern 1: clone the value out
let v = m.get("a").unwrap().clone();
m.insert("b".into(), vec![4]);

// Pattern 2: entry API for conditional insert
m.entry("c".into())
 .or_insert_with(|| vec![5, 6]);

// Pattern 3: use indices, not references (for Vec-backed structures)
```

### 8.3 Entry API — The Canonical Pattern

The entry API avoids double lookups for "insert if not present" logic:

```rust
// WRONG (two lookups):
if !m.contains_key("key") {
    m.insert("key".into(), expensive_compute());
}

// CORRECT (one lookup):
m.entry("key".into())
 .or_insert_with(|| expensive_compute());

// More patterns:
// Insert default, then modify:
let counter = m.entry("word".into()).or_insert(0);
*counter += 1;   // counter is &mut V

// Only insert if vacant:
m.entry("key".into())
 .or_default();

// Conditional modification:
m.entry("key".into())
 .and_modify(|v| *v += 1)
 .or_insert(1);
```

### 8.4 Iteration and Mutation

```rust
// Immutable iteration:
for (k, v) in &m { ... }

// Mutable value iteration (keys are immutable during iteration):
for (k, v) in &mut m {
    *v += 1;  // OK to mutate values
    // m.insert(...) // NOT allowed — would invalidate iterator
}

// Consuming iteration (m is moved):
for (k, v) in m { ... }

// Retain (filter in place) — safe because it's controlled:
m.retain(|k, v| v > &0);

// Drain:
for (k, v) in m.drain() { ... }
// m is now empty but still allocated
```

### 8.5 Custom Hasher

```rust
use std::collections::HashMap;
use std::hash::BuildHasherDefault;
use fnv::FnvHasher;   // crate: fnv

// FnvHasher is faster for small keys (integers, short strings)
// but NOT DoS-resistant (no randomization)
type FnvHashMap<K, V> = HashMap<K, V, BuildHasherDefault<FnvHasher>>;

let mut m: FnvHashMap<u64, u64> = FnvHashMap::default();
```

```rust
// For production: use ahash (AES-NI accelerated, DoS-resistant)
use ahash::AHashMap;
let mut m: AHashMap<String, i32> = AHashMap::new();
```

### 8.6 HashSet in Rust

```rust
use std::collections::HashSet;

let mut a: HashSet<i32> = [1, 2, 3, 4, 5].iter().cloned().collect();
let b: HashSet<i32> = [3, 4, 5, 6, 7].iter().cloned().collect();

// Set operations return iterators, not new sets:
let union: HashSet<_>        = a.union(&b).cloned().collect();
let intersection: HashSet<_> = a.intersection(&b).cloned().collect();
let difference: HashSet<_>   = a.difference(&b).cloned().collect();  // a - b
let sym_diff: HashSet<_>     = a.symmetric_difference(&b).cloned().collect();

// Membership:
assert!(a.contains(&3));
assert!(a.is_subset(&union));
assert!(intersection.is_subset(&a));

// In-place operations:
a.insert(6);
a.remove(&1);
```

### 8.7 Raw Entry API (Unstable)

For advanced use cases where you want to avoid double hashing:

```rust
// Nightly only as of 2025:
use std::collections::hash_map::RawEntryMut;

let raw_entry = m.raw_entry_mut().from_key("existing_key");
match raw_entry {
    RawEntryMut::Occupied(mut e) => { *e.get_mut() += 1; }
    RawEntryMut::Vacant(e) => { e.insert("existing_key".to_string(), 1); }
}
```

---

## 9. C Implementation

### 9.1 Open-Addressing HashMap with Linear Probing

```c
// hashmap.h
#ifndef HASHMAP_H
#define HASHMAP_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define HM_INITIAL_CAPACITY  16
#define HM_LOAD_FACTOR_NUM    7
#define HM_LOAD_FACTOR_DEN   10   /* load factor = 0.7 */
#define HM_GROWTH_FACTOR      2

typedef enum {
    SLOT_EMPTY   = 0,
    SLOT_FULL    = 1,
    SLOT_DELETED = 2,   /* tombstone for linear probe delete */
} SlotState;

typedef struct {
    SlotState state;
    uint64_t  key_hash;   /* cached hash, avoids re-hashing on resize */
    char     *key;        /* heap-allocated key (NUL-terminated) */
    void     *value;      /* caller-owned value pointer */
} Slot;

typedef struct {
    Slot    *slots;
    size_t   capacity;
    size_t   count;        /* live entries */
    size_t   tombstones;   /* deleted entries (affect load factor) */
    uint64_t seed;         /* per-map random seed */
} HashMap;

/* Internal layout:
 *
 *  slots array (capacity = 16, each slot = 32 bytes):
 *  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
 *  │ E    │ F    │ E    │ D    │ F    │ E    │ F    │ E    │
 *  │ [0]  │ [1]  │ [2]  │ [3]  │ [4]  │ [5]  │ [6]  │ [7] │
 *  └──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘
 *    E=EMPTY  F=FULL  D=DELETED(tombstone)
 *
 *  Probe sequence for "foo" (hash=5):
 *  Try [5] (FULL, wrong key) → try [6] (FULL, match!) → return &slots[6].value
 */

HashMap *hm_new(void);
void     hm_free(HashMap *hm);
bool     hm_insert(HashMap *hm, const char *key, void *value);
void    *hm_get(const HashMap *hm, const char *key);
bool     hm_delete(HashMap *hm, const char *key);
size_t   hm_count(const HashMap *hm);

#endif /* HASHMAP_H */
```

```c
// hashmap.c
#include "hashmap.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <assert.h>

/* SipHash-1-3 implementation (simplified, 64-bit output) */
static inline uint64_t rotl64(uint64_t x, int b) {
    return (x << b) | (x >> (64 - b));
}

static uint64_t siphash13(const void *data, size_t len, uint64_t seed) {
    uint64_t v0 = seed ^ 0x736f6d6570736575ULL;
    uint64_t v1 = seed ^ 0x646f72616e646f6dULL;
    uint64_t v2 = seed ^ 0x6c7967656e657261ULL;
    uint64_t v3 = seed ^ 0x7465646279746573ULL;

    const uint8_t *p = (const uint8_t *)data;
    const uint8_t *end = p + (len & ~7ULL);

    for (; p < end; p += 8) {
        uint64_t m;
        memcpy(&m, p, 8);
        v3 ^= m;
        /* SipRound x1 */
        v0 += v1; v1 = rotl64(v1,13); v1 ^= v0; v0 = rotl64(v0,32);
        v2 += v3; v3 = rotl64(v3,16); v3 ^= v2;
        v0 += v3; v3 = rotl64(v3,21); v3 ^= v0;
        v2 += v1; v1 = rotl64(v1,17); v1 ^= v2; v2 = rotl64(v2,32);
        v0 ^= m;
    }

    /* Handle remaining bytes */
    uint64_t last = (uint64_t)(len & 0xff) << 56;
    size_t rem = len & 7;
    while (rem-- > 0) last |= (uint64_t)p[rem] << (rem * 8);
    v3 ^= last;
    /* SipRound */
    v0 += v1; v1 = rotl64(v1,13); v1 ^= v0; v0 = rotl64(v0,32);
    v2 += v3; v3 = rotl64(v3,16); v3 ^= v2;
    v0 += v3; v3 = rotl64(v3,21); v3 ^= v0;
    v2 += v1; v1 = rotl64(v1,17); v1 ^= v2; v2 = rotl64(v2,32);
    v0 ^= last;
    v2 ^= 0xff;
    /* SipRound x3 */
    for (int i = 0; i < 3; i++) {
        v0 += v1; v1 = rotl64(v1,13); v1 ^= v0; v0 = rotl64(v0,32);
        v2 += v3; v3 = rotl64(v3,16); v3 ^= v2;
        v0 += v3; v3 = rotl64(v3,21); v3 ^= v0;
        v2 += v1; v1 = rotl64(v1,17); v1 ^= v2; v2 = rotl64(v2,32);
    }
    return v0 ^ v1 ^ v2 ^ v3;
}

static uint64_t hash_key(const HashMap *hm, const char *key) {
    return siphash13(key, strlen(key), hm->seed);
}

static size_t probe_index(size_t h, size_t i, size_t cap) {
    return (h + i) & (cap - 1);   /* cap must be power of 2 */
}

HashMap *hm_new(void) {
    HashMap *hm = calloc(1, sizeof(*hm));
    if (!hm) return NULL;
    hm->capacity = HM_INITIAL_CAPACITY;
    hm->slots = calloc(hm->capacity, sizeof(Slot));
    if (!hm->slots) { free(hm); return NULL; }
    /* Use getrandom/arc4random in production; time() for illustration */
    hm->seed = (uint64_t)time(NULL) ^ (uint64_t)(uintptr_t)hm;
    return hm;
}

void hm_free(HashMap *hm) {
    if (!hm) return;
    for (size_t i = 0; i < hm->capacity; i++) {
        if (hm->slots[i].state == SLOT_FULL)
            free(hm->slots[i].key);
    }
    free(hm->slots);
    free(hm);
}

/* Returns slot index for key, or capacity if not found.
 * also_tombstone: if true, returns first tombstone seen (for insert) */
static size_t find_slot(const HashMap *hm, const char *key,
                         uint64_t h, bool also_tombstone, size_t *tomb_out) {
    size_t first_tomb = hm->capacity;
    for (size_t i = 0; i < hm->capacity; i++) {
        size_t idx = probe_index(h, i, hm->capacity);
        Slot  *s   = &hm->slots[idx];
        if (s->state == SLOT_EMPTY) {
            if (also_tombstone && first_tomb < hm->capacity) {
                if (tomb_out) *tomb_out = first_tomb;
                return hm->capacity;   /* not found, tombstone available */
            }
            return hm->capacity;       /* not found, no tombstone */
        }
        if (s->state == SLOT_DELETED) {
            if (first_tomb == hm->capacity) first_tomb = idx;
            continue;
        }
        /* SLOT_FULL: check hash then key */
        if (s->key_hash == h && strcmp(s->key, key) == 0)
            return idx;
    }
    return hm->capacity; /* should not reach here if load factor correct */
}

static bool hm_resize(HashMap *hm) {
    size_t new_cap = hm->capacity * HM_GROWTH_FACTOR;
    Slot  *new_slots = calloc(new_cap, sizeof(Slot));
    if (!new_slots) return false;

    Slot  *old = hm->slots;
    size_t old_cap = hm->capacity;

    hm->slots = new_slots;
    hm->capacity = new_cap;
    hm->count = 0;
    hm->tombstones = 0;

    for (size_t i = 0; i < old_cap; i++) {
        if (old[i].state != SLOT_FULL) continue;
        /* Re-insert into new table */
        uint64_t h = old[i].key_hash;
        for (size_t j = 0; j < new_cap; j++) {
            size_t idx = probe_index(h, j, new_cap);
            if (new_slots[idx].state == SLOT_EMPTY) {
                new_slots[idx] = old[i];   /* struct copy */
                hm->count++;
                break;
            }
        }
    }
    free(old);
    return true;
}

bool hm_insert(HashMap *hm, const char *key, void *value) {
    /* Resize if (count + tombstones) / capacity > load_factor */
    if ((hm->count + hm->tombstones) * HM_LOAD_FACTOR_DEN >=
         hm->capacity * HM_LOAD_FACTOR_NUM) {
        if (!hm_resize(hm)) return false;
    }

    uint64_t h = hash_key(hm, key);
    size_t first_tomb = hm->capacity;

    for (size_t i = 0; i < hm->capacity; i++) {
        size_t idx = probe_index(h, i, hm->capacity);
        Slot  *s   = &hm->slots[idx];

        if (s->state == SLOT_EMPTY || s->state == SLOT_DELETED) {
            size_t insert_at = (s->state == SLOT_DELETED && first_tomb < hm->capacity)
                               ? first_tomb : idx;
            if (s->state == SLOT_DELETED && first_tomb == hm->capacity)
                first_tomb = idx;
            /* Use first tombstone if we found one */
            if (s->state == SLOT_EMPTY && first_tomb < hm->capacity)
                insert_at = first_tomb;
            if (s->state == SLOT_DELETED) {
                if (first_tomb == hm->capacity) first_tomb = idx;
                continue;   /* keep probing for existing key */
            }
            /* SLOT_EMPTY: key not found, insert at first_tomb or here */
            size_t target = (first_tomb < hm->capacity) ? first_tomb : idx;
            Slot *t = &hm->slots[target];
            if (t->state == SLOT_DELETED) hm->tombstones--;
            t->state    = SLOT_FULL;
            t->key_hash = h;
            t->key      = strdup(key);
            t->value    = value;
            hm->count++;
            return true;
        }
        if (s->state == SLOT_DELETED) {
            if (first_tomb == hm->capacity) first_tomb = idx;
            continue;
        }
        /* SLOT_FULL */
        if (s->key_hash == h && strcmp(s->key, key) == 0) {
            s->value = value;   /* update existing */
            return true;
        }
    }
    return false;
}

void *hm_get(const HashMap *hm, const char *key) {
    uint64_t h = hash_key(hm, key);
    for (size_t i = 0; i < hm->capacity; i++) {
        size_t idx = probe_index(h, i, hm->capacity);
        const Slot *s = &hm->slots[idx];
        if (s->state == SLOT_EMPTY) return NULL;
        if (s->state == SLOT_DELETED) continue;
        if (s->key_hash == h && strcmp(s->key, key) == 0)
            return s->value;
    }
    return NULL;
}

bool hm_delete(HashMap *hm, const char *key) {
    uint64_t h = hash_key(hm, key);
    for (size_t i = 0; i < hm->capacity; i++) {
        size_t idx = probe_index(h, i, hm->capacity);
        Slot  *s   = &hm->slots[idx];
        if (s->state == SLOT_EMPTY) return false;
        if (s->state == SLOT_DELETED) continue;
        if (s->key_hash == h && strcmp(s->key, key) == 0) {
            free(s->key);
            s->key   = NULL;
            s->value = NULL;
            s->state = SLOT_DELETED;   /* tombstone, not EMPTY */
            hm->count--;
            hm->tombstones++;
            return true;
        }
    }
    return false;
}

size_t hm_count(const HashMap *hm) { return hm->count; }
```

**Why tombstones on delete instead of clearing:**

```
 State before delete of "B":
 slot[0]: [EMPTY]
 slot[1]: [FULL "A", hash=1]   hash("A")%8 = 1, no collision
 slot[2]: [FULL "B", hash=1]   hash("B")%8 = 1, probed to slot 2
 slot[3]: [FULL "C", hash=1]   hash("C")%8 = 1, probed to slot 3

 If we clear slot[2] (set to EMPTY):
 slot[2]: [EMPTY]              ← probe chain BROKEN
 
 Lookup "C": probe slot[1] (wrong key), probe slot[2] (EMPTY → STOP) → NOT FOUND!
 Data corruption — "C" is still there at slot[3] but unreachable!

 If we tombstone slot[2]:
 slot[2]: [DELETED]            ← probe chain INTACT
 
 Lookup "C": probe slot[1] (wrong key), probe slot[2] (DELETED → continue), 
             probe slot[3] (match) → FOUND!
```

---

## 10. Operations You CAN Do

### 10.1 Go

```go
m := make(map[string]int)

// INSERT / UPDATE
m["key"] = 42

// LOOKUP (zero value if missing)
v := m["key"]

// LOOKUP with existence check
v, ok := m["key"]

// DELETE (no-op if key doesn't exist — safe)
delete(m, "key")

// ITERATE (random order)
for k, v := range m {
    _ = k; _ = v
}

// ITERATE keys only
for k := range m { _ = k }

// LENGTH
n := len(m)

// CHECK NIL
if m == nil { m = make(map[string]int) }

// COPY (shallow)
m2 := make(map[string]int, len(m))
for k, v := range m { m2[k] = v }

// DELETE DURING RANGE (safe in Go)
for k, v := range m {
    if v == 0 { delete(m, k) }
}

// NESTED MAP
nested := map[string]map[string]int{}
nested["outer"] = make(map[string]int)
nested["outer"]["inner"] = 99
```

### 10.2 Rust

```rust
use std::collections::{HashMap, HashSet};

let mut m: HashMap<String, i32> = HashMap::new();

// INSERT
m.insert("key".into(), 42);

// LOOKUP (returns Option<&V>)
if let Some(v) = m.get("key") { println!("{}", v); }

// LOOKUP MUT
if let Some(v) = m.get_mut("key") { *v += 1; }

// DELETE (returns Option<V> with the removed value)
let old = m.remove("key");

// CONTAINS
let exists = m.contains_key("key");

// ENTRY API
m.entry("key".into()).or_insert(0);
*m.entry("key".into()).or_insert(0) += 1;

// ITERATE
for (k, v) in &m { }
for (k, v) in &mut m { *v *= 2; }
for (k, v) in m.drain() { }   // empties map

// RETAIN (filter in place)
m.retain(|k, v| *v > 0);

// EXTEND
m.extend([("a".into(), 1), ("b".into(), 2)]);

// FROM ITERATOR
let m: HashMap<_, _> = vec![("a", 1), ("b", 2)].into_iter().collect();

// LEN / IS_EMPTY
let n = m.len();
let empty = m.is_empty();

// CAPACITY
let cap = m.capacity();
m.reserve(100);      // ensure space for 100 more
m.shrink_to_fit();   // release excess memory

// HashSet
let mut s: HashSet<i32> = HashSet::new();
s.insert(1);
s.remove(&1);         // returns bool
s.contains(&1);
let u: HashSet<_> = s.union(&other).cloned().collect();
```

### 10.3 C (using our implementation)

```c
HashMap *m = hm_new();
hm_insert(m, "key", (void*)42);
void *v = hm_get(m, "key");
hm_delete(m, "key");
hm_free(m);
```

---

## 11. Common Mistakes and What You CANNOT Do

### 11.1 Mutation of Keys

**The cardinal rule: A key's hash must not change after insertion.**

```go
// GO: not possible at language level for map keys
// (only comparable types allowed; strings/ints are value types, immutable)
// BUT: using struct keys with mutable fields via interface{}... avoid it

// RUST: Borrow checker prevents key mutation via reference
// BUT: if key is derived from external mutable state, still a logical bug
```

```cpp
// C++: Easy to accidentally violate
std::unordered_map<std::string, int> m;
m["hello"] = 42;
// std::string keys are value-copied into the map — safe in C++

// DANGER with raw pointer keys:
char buf[10] = "hello";
std::unordered_map<char*, int> m2;
m2[buf] = 42;
strcpy(buf, "world");   // BUG: key changed, hash chain broken, data unreachable
```

**Rule: Keys must be value-semantic (copied), not pointer/reference-semantic.**

### 11.2 Nil Map Writes (Go)

```go
var m map[string]int   // nil!
m["key"] = 1           // PANIC: assignment to entry in nil map

// Fix:
m = make(map[string]int)
m["key"] = 1           // OK
```

### 11.3 Holding References Across Insertions (Rust)

```rust
let mut m: HashMap<String, Vec<i32>> = HashMap::new();
m.insert("a".into(), vec![1, 2, 3]);

let v: &Vec<i32> = m.get("a").unwrap();  // borrow starts here
m.insert("b".into(), vec![4, 5, 6]);     // ERROR: insert may rehash, invalidating v
println!("{:?}", v);                      // dangling reference if allowed
```

Rust prevents this at compile time. In C/C++, this causes **use-after-free**.

### 11.4 Concurrent Map Access Without Synchronization (Go)

```go
// PANIC (detected at runtime even without -race):
var m = map[string]int{}
go func() { for { m["a"]++ } }()
go func() { for { _ = m["a"] } }()
```

### 11.5 Modifying While Iterating (C / C++)

```c
// UNDEFINED BEHAVIOR: iterating over our C hashmap while deleting
// Our implementation: do NOT call hm_delete inside a loop over hm->slots
// Pattern: collect keys to delete, then delete after iteration
```

```cpp
// C++: iterator invalidation on insert during iteration
std::unordered_map<int,int> m = {{1,1},{2,2},{3,3}};
for (auto& [k, v] : m) {
    m.insert({k+10, v});  // UNDEFINED BEHAVIOR: invalidates iterator
}

// SAFE: collect first, then insert
std::vector<std::pair<int,int>> to_add;
for (auto& [k, v] : m) to_add.push_back({k+10, v});
for (auto& p : to_add) m.insert(p);
```

### 11.6 Using Non-Comparable Keys (Go)

```go
// These are compile-time errors in Go:
m := map[[]int]string{}       // COMPILE ERROR: slice not comparable
m2 := map[map[string]int]int{} // COMPILE ERROR: map not comparable
m3 := map[func()]int{}         // COMPILE ERROR: func not comparable
```

**Solution:** Use a serialized/stringified key, or a struct of comparable fields.

```go
type Point struct{ X, Y int }
m := map[Point]string{}   // OK: struct of comparables is comparable
m[Point{1, 2}] = "hello"
```

### 11.7 Assuming Insertion Order is Preserved

```go
// WRONG assumption:
m := map[string]int{"c": 3, "a": 1, "b": 2}
for k := range m { fmt.Print(k, " ") }
// Output is random: may be "a b c" or "c b a" or "b c a"
// NOT "c a b" (insertion order)
```

**If you need ordering:** Use `[]struct{ K, V }` slice, or a library like `golang.org/x/exp/maps` + sort, or an ordered map (red-black tree based).

### 11.8 Float/NaN Keys

```go
// In Go, NaN != NaN (IEEE 754), so:
m := map[float64]int{}
m[math.NaN()] = 1
m[math.NaN()] = 2
fmt.Println(len(m))  // 2 — two different "NaN" keys!
v, ok := m[math.NaN()]  // ok=false — you can insert but never retrieve!
```

**Never use NaN as a map key.** In Rust, `f32`/`f64` don't implement `Hash` or `Eq` for this reason — it's a compile error.

```rust
// Rust correctly refuses:
let mut m: HashMap<f64, i32> = HashMap::new(); // COMPILE ERROR
// f64 does not implement Eq (because NaN != NaN)
```

### 11.9 Zero Value Trap (Go)

```go
m := map[string]int{"a": 0}
v, ok := m["a"]   // v=0, ok=true   ← key exists, value is 0
v, ok  = m["b"]   // v=0, ok=false  ← key missing

// Common bug: not using comma-ok
if m["a"] == 0 {
    // Executes for BOTH missing keys AND keys with value 0
    // You may double-initialize or miscount
}
```

### 11.10 Map Value Addressability (Go)

```go
type Counter struct{ N int }
m := map[string]Counter{"a": {0}}

m["a"].N++        // COMPILE ERROR: cannot assign to struct field in map
(&m["a"]).N++     // COMPILE ERROR: cannot take address of map value

// Fix 1: use pointer values
m2 := map[string]*Counter{"a": {0}}
m2["a"].N++       // OK: pointer is stable

// Fix 2: copy out, modify, copy back
c := m["a"]
c.N++
m["a"] = c        // This involves a hash lookup on write
```

### 11.11 Comparing Maps (Go)

```go
m1 := map[string]int{"a": 1}
m2 := map[string]int{"a": 1}
m1 == m2  // COMPILE ERROR: map can only be compared to nil

// Use reflect.DeepEqual (slow) or write your own comparison:
func mapsEqual(a, b map[string]int) bool {
    if len(a) != len(b) { return false }
    for k, v := range a {
        if bv, ok := b[k]; !ok || bv != v { return false }
    }
    return true
}
```

### 11.12 Memory Leak via Non-Shrinking Maps (Go)

```go
// As described in §7.7: maps don't shrink
// Long-lived services that do bulk-insert + bulk-delete will leak memory

// Pattern: cache with TTL that gets flooded
cache := make(map[string][]byte)
for _, req := range massiveRequestBatch {
    cache[req.ID] = processLarge(req)   // grows to N entries
}
for k := range cache { delete(cache, k) }
// cache is empty but holds its peak memory allocation forever
// Fix: cache = make(map[string][]byte)  -- reassign to release
```

### 11.13 Hash Collision in Custom Types (Rust)

```rust
use std::hash::{Hash, Hasher};

// WRONG: Equal values must have equal hashes
// If you implement PartialEq manually but derive Hash, or vice versa:
#[derive(Hash)]
struct Key {
    a: i32,
    b: i32,
}

impl PartialEq for Key {
    fn eq(&self, other: &Self) -> bool {
        self.a == other.a  // only compares 'a', ignores 'b'
        // BUG: Key{1,1} == Key{1,2} but hash(Key{1,1}) != hash(Key{1,2})
        // Violates the HashMap contract
    }
}
// This causes keys to be unretrievable or multiply-inserted
```

**Rule in Rust:** If you implement `PartialEq` manually, you MUST implement `Hash` manually to match. The same fields must be compared in both.

### 11.14 Using HashMap Where You Need Determinism

```go
// Marshaling to JSON from a map gives random field order every time:
m := map[string]int{"b": 2, "a": 1, "c": 3}
data, _ := json.Marshal(m)
// Output may be: {"a":1,"b":2,"c":3} or {"c":3,"b":2,"a":1} — RANDOM

// Test might pass today and fail tomorrow
// Protocol buffers, hash-based signatures, canonical forms → USE SORTED KEYS
```

### 11.15 Large Value Types in Maps

```go
// Go copies values on every read and write:
type BigStruct struct { data [4096]byte }
m := map[string]BigStruct{}
m["key"] = BigStruct{}   // 4096 byte copy on write
v := m["key"]            // 4096 byte copy on read — v is a COPY

// Fix: store pointers
m2 := map[string]*BigStruct{}
m2["key"] = &BigStruct{}
m2["key"].data[0] = 1    // in-place modification via pointer
```

### 11.16 Forgetting to Initialize Nested Maps (Go)

```go
// PANIC:
m := map[string]map[string]int{}
m["outer"]["inner"] = 1  // PANIC: m["outer"] is nil!

// Fix:
if _, ok := m["outer"]; !ok {
    m["outer"] = make(map[string]int)
}
m["outer"]["inner"] = 1

// Or use helper:
func getOrMake(m map[string]map[string]int, key string) map[string]int {
    if sub, ok := m[key]; ok { return sub }
    sub := make(map[string]int)
    m[key] = sub
    return sub
}
```

### 11.17 sync.Map Misuse

```go
// sync.Map is NOT a general-purpose replacement for map+mutex
// It's optimized for:
//   1. Entries written once and read many times
//   2. Goroutines operating on disjoint key sets

// sync.Map is SLOWER than map+RWMutex for:
//   - Write-heavy workloads
//   - Small numbers of goroutines
//   - When the same keys are frequently written

// sync.Map.LoadOrStore is NOT a transaction:
// Two goroutines calling LoadOrStore("k", v) concurrently
// may BOTH get "loaded=false" (race between load and store checks)
// Use LoadOrStore's return value (actual, loaded) correctly.
```

---

## 12. Concurrency

### 12.1 Architecture: Safe Concurrent Patterns

```
 ┌─────────────────────────────────────────────────────────────┐
 │                   CONCURRENT MAP ACCESS                      │
 ├──────────────────┬──────────────────┬───────────────────────┤
 │  sync.RWMutex    │  sync.Map        │  Sharded Map          │
 │  + plain map     │                  │  (reduce contention)  │
 ├──────────────────┼──────────────────┼───────────────────────┤
 │ Read: RLock      │ Built-in         │ hash(key) % N shards  │
 │ Write: Lock      │ lock-free reads  │ each shard has own mu │
 │                  │ for stable keys  │                       │
 ├──────────────────┼──────────────────┼───────────────────────┤
 │ Best for:        │ Best for:        │ Best for:             │
 │ General purpose  │ Read-heavy,      │ High-throughput,      │
 │ Mixed r/w        │ stable keys,     │ many goroutines,      │
 │                  │ disjoint writers │ write-heavy           │
 └──────────────────┴──────────────────┴───────────────────────┘
```

### 12.2 Go: Sharded Map Implementation

```go
package shardmap

import (
    "hash/fnv"
    "sync"
)

const numShards = 32

type shard[V any] struct {
    mu sync.RWMutex
    m  map[string]V
}

type ShardedMap[V any] struct {
    shards [numShards]shard[V]
}

func NewShardedMap[V any]() *ShardedMap[V] {
    sm := &ShardedMap[V]{}
    for i := range sm.shards {
        sm.shards[i].m = make(map[string]V)
    }
    return sm
}

func (sm *ShardedMap[V]) shardFor(key string) *shard[V] {
    h := fnv.New32a()
    h.Write([]byte(key))
    return &sm.shards[h.Sum32()%numShards]
}

func (sm *ShardedMap[V]) Set(key string, val V) {
    s := sm.shardFor(key)
    s.mu.Lock()
    s.m[key] = val
    s.mu.Unlock()
}

func (sm *ShardedMap[V]) Get(key string) (V, bool) {
    s := sm.shardFor(key)
    s.mu.RLock()
    v, ok := s.m[key]
    s.mu.RUnlock()
    return v, ok
}

func (sm *ShardedMap[V]) Delete(key string) {
    s := sm.shardFor(key)
    s.mu.Lock()
    delete(s.m, key)
    s.mu.Unlock()
}
```

### 12.3 Rust: DashMap (Sharded HashMap)

```rust
// Cargo.toml: dashmap = "6"
use dashmap::DashMap;

let m: DashMap<String, i32> = DashMap::new();

// Concurrent insert from multiple threads:
m.insert("key".to_string(), 42);

// Returns a Ref<K,V> (shard read-locked until dropped):
let v = m.get("key").unwrap();
println!("{}", *v);
// v dropped here → shard unlocked

// Deadlock risk: holding a Ref and calling insert on same shard
// WRONG:
let r = m.get("a");  // shard 0 read-locked
m.insert("b".to_string(), 1);  // if "b" also in shard 0 → DEADLOCK

// CORRECT: drop the reference before inserting
drop(r);
m.insert("b".to_string(), 1);
```

### 12.4 Actor / Channel Pattern (Go)

```go
// Eliminate shared state entirely — single goroutine owns the map
type Op struct {
    key  string
    val  int
    resp chan<- int
    kind int  // 0=get, 1=set, 2=delete
}

type MapActor struct {
    ops chan Op
    m   map[string]int
}

func (a *MapActor) run() {
    for op := range a.ops {
        switch op.kind {
        case 0: op.resp <- a.m[op.key]
        case 1: a.m[op.key] = op.val
        case 2: delete(a.m, op.key)
        }
    }
}
```

---

## 13. Security

### 13.1 Threat Model for Hash Maps

```
 ┌─────────────────────────────────────────────────────────────────┐
 │  THREAT: HashDoS (Hash Denial of Service)                       │
 │                                                                  │
 │  Attacker controls keys → crafts keys with identical hashes     │
 │  → All keys land in same bucket → O(n²) processing              │
 │  → CPU exhaustion, service unavailability                        │
 │                                                                  │
 │  Affected: PHP (CVE-2011-4885), Java, Ruby, Python pre-3.3,     │
 │            Go pre-1.0 (fixed), Rust pre-2018                     │
 │                                                                  │
 │  Mitigations:                                                    │
 │  1. Random seed per map (Go: hash0, Rust: RandomState)           │
 │  2. SipHash / AHash (PRF properties, seed-dependent)             │
 │  3. Rate-limit input key count per request                        │
 │  4. Cap map size (reject if grows beyond threshold)              │
 └─────────────────────────────────────────────────────────────────┘
```

### 13.2 Timing Side Channels

```
 HashMap lookup time varies with:
 - Number of collisions (depends on key)
 - Cache state
 - Probe sequence length

 IF you use a hashmap to store secrets and compare via lookup,
 you MAY leak information about the key space via timing.

 Example WRONG pattern:
 // Token validation via map lookup
 valid := tokenMap[userToken]   // timing varies with collision count

 Example CORRECT pattern:
 // Use constant-time comparison AFTER lookup
 storedToken, ok := tokenMap[userID]
 if !ok { return false }
 return subtle.ConstantTimeCompare([]byte(userToken), []byte(storedToken)) == 1
```

### 13.3 Key Sanitization

```go
// If keys come from HTTP headers/query params, cap key length:
func safeInsert(m map[string]string, k, v string) error {
    if len(k) > 256 { return errors.New("key too long") }
    if len(m) > 10000 { return errors.New("map too large") }
    m[k] = v
    return nil
}
```

### 13.4 Information Disclosure via Iteration Order

```go
// If you iterate a map and return results in iteration order,
// an attacker can probe the hash seed by observing output order.
// Always sort before returning externally visible ordered output.
```

---

## 14. Performance

### 14.1 Pre-allocation

```go
// WITHOUT hint: multiple rehashes as map grows
m := make(map[string]int)
for i := 0; i < 1_000_000; i++ { m[strconv.Itoa(i)] = i }
// ~20 rehashes at growth factors of 2

// WITH hint: 0 or 1 rehashes
m := make(map[string]int, 1_000_000)
for i := 0; i < 1_000_000; i++ { m[strconv.Itoa(i)] = i }
```

```rust
// Rust:
let mut m = HashMap::with_capacity(1_000_000);
// Reserves enough for 1M entries with correct load factor margin
```

### 14.2 Key Type Performance

```
 Integer keys:    fastest (hash is trivial, comparison is single instruction)
 Short strings:   fast (< 16 bytes often fits in SIMD register)
 Long strings:    proportional to length (hash must read all bytes)
 Struct keys:     depends on field types; avoid fields that require heap allocation
 []byte as key:   requires conversion to string in Go (allocates): use string(b) judiciously
```

### 14.3 Benchmarking (Go)

```go
// bench_test.go
package main

import (
    "strconv"
    "testing"
)

func BenchmarkMapInsert(b *testing.B) {
    m := make(map[int]int, b.N)
    for i := 0; i < b.N; i++ {
        m[i] = i
    }
}

func BenchmarkMapLookup(b *testing.B) {
    m := make(map[int]int, 1000)
    for i := 0; i < 1000; i++ { m[i] = i }
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = m[i%1000]
    }
}

func BenchmarkMapStringLookup(b *testing.B) {
    m := make(map[string]int, 1000)
    keys := make([]string, 1000)
    for i := 0; i < 1000; i++ {
        keys[i] = strconv.Itoa(i)
        m[keys[i]] = i
    }
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = m[keys[i%1000]]
    }
}
```

Run: `go test -bench=. -benchmem -count=5`

### 14.4 Benchmarking (Rust)

```rust
// benches/hashmap_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use std::collections::HashMap;
use ahash::AHashMap;

fn bench_std_insert(c: &mut Criterion) {
    c.bench_function("std_hashmap_insert", |b| {
        b.iter(|| {
            let mut m: HashMap<u64, u64> = HashMap::with_capacity(1000);
            for i in 0..1000u64 { m.insert(black_box(i), i); }
        });
    });
}

fn bench_ahash_insert(c: &mut Criterion) {
    c.bench_function("ahash_insert", |b| {
        b.iter(|| {
            let mut m: AHashMap<u64, u64> = AHashMap::with_capacity(1000);
            for i in 0..1000u64 { m.insert(black_box(i), i); }
        });
    });
}

criterion_group!(benches, bench_std_insert, bench_ahash_insert);
criterion_main!(benches);
```

Run: `cargo bench`

---

## 15. Iterator Invalidation

### 15.1 Language Comparison

```
 ┌────────────┬────────────────────────────────────────────────────────┐
 │ Language   │ Rules                                                  │
 ├────────────┼────────────────────────────────────────────────────────┤
 │ Go         │ Delete during range: SAFE (defined behavior)           │
 │            │ Insert during range: SAFE but result undefined         │
 │            │ (new key may or may not appear in iteration)           │
 ├────────────┼────────────────────────────────────────────────────────┤
 │ Rust       │ Cannot mutate map while iterator exists (borrow check) │
 │            │ Use .retain() for filtered deletion                    │
 │            │ Use .drain() for consuming iteration                   │
 ├────────────┼────────────────────────────────────────────────────────┤
 │ C++        │ Any insert MAY invalidate ALL iterators (rehash)       │
 │            │ Delete invalidates ONLY the erased iterator             │
 │            │ Other iterators remain valid after erase                │
 ├────────────┼────────────────────────────────────────────────────────┤
 │ C (ours)   │ No iterator type; manual index loop                    │
 │            │ Deleting during slot scan: mark visited, delete after  │
 └────────────┴────────────────────────────────────────────────────────┘
```

### 15.2 C++ Iterator Invalidation Rules (Important)

```cpp
std::unordered_map<int,int> m = {{1,1},{2,2},{3,3}};

auto it = m.find(2);
m.insert({4, 4});    // MAY rehash → it is NOW INVALID → UB to dereference
m.erase(3);          // it (pointing to 2) remains VALID (erase doesn't rehash)
std::cout << it->second;  // VALID only if no insert triggered rehash

// Safe pattern: use erase(key) not erase(iterator) when modifying during loop
for (auto it = m.begin(); it != m.end(); ) {
    if (it->second == 0)
        it = m.erase(it);  // erase returns next valid iterator
    else
        ++it;
}
```

---

## 16. Ordered vs Unordered Maps

### 16.1 Complexity Comparison

```
 ┌──────────────────────┬────────────────────────┬────────────────────────┐
 │ Operation            │ HashMap (unordered)     │ BTreeMap (ordered)     │
 ├──────────────────────┼────────────────────────┼────────────────────────┤
 │ Insert               │ O(1) amortized          │ O(log n)               │
 │ Lookup               │ O(1) average            │ O(log n)               │
 │ Delete               │ O(1) average            │ O(log n)               │
 │ Iterate in order     │ O(n log n) (sort keys)  │ O(n) (already sorted)  │
 │ Range query [a, b]   │ O(n) (scan all)         │ O(log n + k) results   │
 │ Min / Max            │ O(n)                    │ O(log n)               │
 │ Predecessor / Succ   │ O(n)                    │ O(log n)               │
 │ Memory (per entry)   │ Low (no tree overhead)  │ Higher (tree nodes)    │
 │ Cache behavior       │ Good (linear probing)   │ Poor (random pointers) │
 └──────────────────────┴────────────────────────┴────────────────────────┘
```

### 16.2 Choose HashMap When

- Primary operations are insert/lookup/delete
- No need for ordered traversal or range queries
- Performance is critical
- Keys have a good hash function

### 16.3 Choose BTreeMap When

- You need keys in sorted order
- Range queries (e.g., all entries with keys between A and B)
- Finding min/max efficiently
- Predictable O(log n) worst case (security contexts)

```rust
use std::collections::BTreeMap;
let mut m: BTreeMap<String, i32> = BTreeMap::new();
m.insert("b".into(), 2);
m.insert("a".into(), 1);
for (k, v) in &m { println!("{}: {}", k, v); }  // ALWAYS prints a, b (sorted)

// Range query:
use std::ops::Bound::Included;
for (k, v) in m.range((Included("a"), Included("b"))) { ... }
```

---

## 17. Threat Model

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │                    HASHMAP THREAT MODEL                               │
 ├──────────────┬───────────────────────────────┬───────────────────────┤
 │ Threat       │ Attack Vector                 │ Mitigation            │
 ├──────────────┼───────────────────────────────┼───────────────────────┤
 │ HashDoS      │ Crafted keys → same bucket    │ Random seed, SipHash  │
 │              │ → O(n²) server slowdown        │ Input key count limit │
 ├──────────────┼───────────────────────────────┼───────────────────────┤
 │ Memory Exhaust│ Unbounded map growth          │ Cap map size          │
 │              │ (large request, bulk keys)     │ TTL + eviction        │
 ├──────────────┼───────────────────────────────┼───────────────────────┤
 │ Data Race    │ Concurrent R/W without lock   │ sync.RWMutex          │
 │ (Go)         │ → map corruption, panic        │ sync.Map, channels    │
 ├──────────────┼───────────────────────────────┼───────────────────────┤
 │ Info Leak    │ Timing differences in lookup  │ Post-lookup const-time│
 │              │ (token/secret as key)          │ comparison            │
 ├──────────────┼───────────────────────────────┼───────────────────────┤
 │ UAF (C/C++)  │ Holding ptr to value,         │ Never store raw ptrs  │
 │              │ then inserting → rehash        │ Use indices instead   │
 ├──────────────┼───────────────────────────────┼───────────────────────┤
 │ Iterator UB  │ Insert during C++ iteration   │ erase returns next it │
 │ (C++)        │ → rehash → dangling iterator  │ Collect then modify   │
 ├──────────────┼───────────────────────────────┼───────────────────────┤
 │ Hash Seed    │ Seed derived from time/PID    │ Use getrandom(2),     │
 │ Weakness     │ → predictable seeds            │ arc4random_buf        │
 └──────────────┴───────────────────────────────┴───────────────────────┘
```

---

## 18. Tests, Fuzzing, Benchmarks

### 18.1 Property-Based Tests (Go)

```go
// go test -run TestMapProperties
func TestMapProperties(t *testing.T) {
    rapid.Check(t, func(t *rapid.T) {
        m := make(map[string]int)
        ops := rapid.SliceOf(rapid.StringN(1, 20, 20)).Draw(t, "keys")
        vals := rapid.SliceOf(rapid.Int()).Draw(t, "vals")

        for i, k := range ops {
            if i >= len(vals) { break }
            m[k] = vals[i]
            // Property: what we just inserted is retrievable
            got, ok := m[k]
            if !ok || got != vals[i] {
                t.Fatalf("insert-then-lookup failed")
            }
        }
        // Property: delete removes the key
        for k := range m {
            delete(m, k)
            if _, ok := m[k]; ok {
                t.Fatalf("delete did not remove key")
            }
            break // just test one
        }
    })
}
```

### 18.2 Fuzzing Our C HashMap

```c
// fuzz_hashmap.c — for use with libFuzzer
#include "hashmap.h"
#include <stdint.h>
#include <string.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 2) return 0;
    HashMap *m = hm_new();
    if (!m) return 0;

    size_t i = 0;
    while (i < size) {
        uint8_t op  = data[i++] % 3;       /* 0=insert, 1=lookup, 2=delete */
        if (i >= size) break;
        uint8_t klen = (data[i++] % 32) + 1;
        if (i + klen > size) break;

        char key[33];
        memcpy(key, data + i, klen);
        key[klen] = '\0';
        i += klen;

        switch (op) {
            case 0: hm_insert(m, key, (void*)(uintptr_t)klen); break;
            case 1: hm_get(m, key); break;
            case 2: hm_delete(m, key); break;
        }
    }
    hm_free(m);
    return 0;
}
```

```bash
# Build and run:
clang -fsanitize=address,fuzzer -O1 hashmap.c fuzz_hashmap.c -o fuzz
./fuzz -max_total_time=60 corpus/
```

### 18.3 Rust Fuzzing with cargo-fuzz

```rust
// fuzz/fuzz_targets/hashmap_fuzz.rs
#![no_main]
use libfuzzer_sys::fuzz_target;
use std::collections::HashMap;

fuzz_target!(|data: &[u8]| {
    let mut m: HashMap<Vec<u8>, u64> = HashMap::new();
    let mut i = 0;
    while i + 2 < data.len() {
        let op = data[i] % 3;
        let klen = (data[i+1] as usize % 32) + 1;
        if i + 2 + klen > data.len() { break; }
        let key = data[i+2..i+2+klen].to_vec();
        i += 2 + klen;
        match op {
            0 => { m.insert(key, i as u64); }
            1 => { let _ = m.get(&key); }
            2 => { m.remove(&key); }
            _ => {}
        }
    }
});
```

```bash
cargo fuzz run hashmap_fuzz -- -max_total_time=60
```

### 18.4 Go Benchmark Suite

```bash
go test -bench=. -benchmem -count=5 -cpuprofile=cpu.prof
go tool pprof cpu.prof
# In pprof: top10, list BenchmarkMapLookup
```

---

## 19. Next 3 Steps

1. **Implement a custom SwissTable in C** — write the SIMD ctrl-byte probe loop using `_mm_cmpeq_epi8`/`_mm_movemask_epi8` intrinsics. Compare throughput vs your linear-probing implementation at load factors 0.5, 0.7, 0.875 using perf stat. This builds a first-principles understanding of why hashbrown outperforms chaining implementations.

2. **Profile a real Go service under map contention** — write a microbenchmark with N goroutines all writing to a `map[string]int` guarded by `sync.Mutex`, then by `sync.RWMutex`, then by a `ShardedMap[int]` with 32/64/128 shards. Use `go test -bench -race -trace=trace.out` + `go tool trace` to see goroutine blocking time. Pick the right abstraction for your actual read:write ratio.

3. **Add HashDoS validation to a Go HTTP handler** — write middleware that counts unique keys in a parsed JSON request body or query string, returns `429 Too Many Requests` if count exceeds a threshold, and logs a security event. Add a property-based test using `pgregory.net/rapid` verifying that no request with >500 unique keys ever succeeds insertion into the application map.

---

## 20. References

| Resource | URL / Citation |
|---|---|
| Go runtime map implementation | `src/runtime/map.go` in the Go source tree |
| hashbrown (Rust) | https://github.com/rust-lang/hashbrown |
| SwissTable design doc | https://abseil.io/about/design/swisstables |
| SipHash paper | Aumasson & Bernstein, "SipHash: a fast short-input PRF" (2012) |
| HashDoS paper | Crosby & Wallach, "Denial of Service via Algorithmic Complexity Attacks" (USENIX 2003) |
| AHash crate | https://github.com/tkaitchuck/aHash |
| Robin Hood Hashing | Celis et al., "Robin Hood Hashing" (1985) |
| CNCF etcd — uses Go maps | https://github.com/etcd-io/etcd |
| Go sync.Map docs | https://pkg.go.dev/sync#Map |
| Rust HashMap docs | https://doc.rust-lang.org/std/collections/struct.HashMap.html |
| cargo-fuzz | https://github.com/rust-fuzz/cargo-fuzz |
| pgregory.net/rapid (Go PBT) | https://github.com/flyingmutant/rapid |
| DashMap (Rust concurrent) | https://github.com/xacrimon/dashmap |
