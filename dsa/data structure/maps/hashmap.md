# HashMap: Under the Hood

## 1. The core idea

An array gives O(1) access by **integer index**. A hashmap turns an arbitrary key into an integer index, so you get array speed with arbitrary keys.

```
 key ──► hash(key) ──► u64 ──► index = h & (cap-1) ──► slot in array
 "bob"   SipHash/        0x9E3779B97F4A7C15   ...0101        buckets[5]
         wyhash/
         FxHash
```

Capacity is kept a **power of two**, so `h % cap` becomes `h & (cap - 1)`, a single AND instruction instead of a ~20-40 cycle division.

---

## 2. Memory layout

A hashmap is one contiguous allocation (plus the heap data for keys/values like `String`).

```
 struct HashMap {
     ptr:   *mut Slot     ─────┐
     cap:   usize = 8          │
     len:   usize = 3          │
     seed:  (k0, k1)           │   random per-map seed (anti hash-flooding)
 }                             │
                               ▼
 index:   0      1      2      3      4      5      6      7
        ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
        │EMPTY │ "ann"│EMPTY │ "bob"│EMPTY │EMPTY │ "cat"│EMPTY │
        │      │  =31 │      │  =25 │      │      │  =40 │      │
        └──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘
        contiguous memory, cache-line friendly
```

Entries land in positions determined by hash, not insertion order. That is why iteration order is arbitrary and, in Rust, deliberately randomized per map.

---

## 3. Collisions

By the pigeonhole principle, two keys will map to the same index. There are two main strategies.

### A) Separate chaining (classic textbook, Java's old HashMap)

```
 index
 ┌───┐
 │ 0 │──► null
 ├───┤
 │ 1 │──► [ann|31|•]──►[dan|12|•]──► null     ◄── collision chain
 ├───┤        node        node
 │ 2 │──► null
 ├───┤
 │ 3 │──► [bob|25|•]──► null
 ├───┤
 │ 4 │──► null
 └───┘
```

- Each bucket points to a linked list of nodes.
- Cost: pointer chasing, one malloc per node, and poor cache behavior.

### B) Open addressing (Rust, Go ≥1.24, Python dict, most modern maps)

All entries live **inside the array itself**. On collision, probe for another slot.

```
 insert "dan": hash → index 1, but slot 1 is taken by "ann"

 linear probing:   1 ✗ (ann)  →  2 ✓ (empty)  → place here

 index:   0      1      2      3
        ┌──────┬──────┬──────┬──────┐
        │      │ ann  │ dan  │ bob  │
        └──────┴──────┴──────┴──────┘
                  ▲      ▲
               home    displaced by 1 probe
```

Probe sequences:

```
 linear:      i, i+1, i+2, i+3 ...          best cache locality, clusters
 quadratic:   i, i+1, i+3, i+6 ...          (triangular numbers), less clustering
 double hash: i, i+h2, i+2·h2 ...           least clustering, worst locality
 Robin Hood:  linear, but steal slot from the entry that is "richer" (closer to home)
```

---

## 4. Operations step by step

### Get

```
 get("dan"):
   h = hash("dan")  = ...0001      → i = 1
   slot[1] = ann   ≠ dan  → probe
   slot[2] = dan   == dan → return &value      (key compare is required!)
   slot[k] = EMPTY         → key does not exist, stop
```

You must compare the **full key**, not just the hash, because different keys can have equal hashes. Probing stops at the first `EMPTY`, which is the signal "if it existed, it would have been placed before here".

### Insert / update

```
 insert(k, v):
   1. if (used+1)/cap > max_load → grow()
   2. walk probe sequence:
        found same key     → replace value, return old   (update)
        found EMPTY        → place new entry
   3. len += 1
```

### Remove: the tombstone problem

You can't just set the slot to EMPTY, because it breaks probe chains:

```
 Before:    [ ann ][ dan ][ bob ]
              1      2      3         dan was displaced from 1 to 2

 Naive remove ann → EMPTY:
            [  ∅  ][ dan ][ bob ]
 get("dan") → hash → slot 1 is EMPTY → "not found"   ✗ WRONG

 Fix: tombstone (DELETED marker):
            [ ☠   ][ dan ][ bob ]
 get("dan") → slot 1 is ☠ → keep probing → slot 2 → found ✓
```

- Lookups skip tombstones; inserts may reuse the first tombstone seen.
- Tombstones count toward load, and are cleaned up during rehash.
- Alternatives: backward-shift deletion (Robin Hood) and group-based EMPTY/DELETED logic (SwissTable).

### Resize / rehash

```
 load factor α = len / cap       (Rust ≈ 7/8, Go classic 6.5/8 per bucket)

 α too high → probes get long (expected probes ≈ 1/(1-α) for a miss)

 grow():
   old: cap 8,  [ann][dan][bob][cat][..][..][..][..]
                      │ allocate 2× array
                      ▼
   new: cap 16, re-insert EVERY entry using hash & 15
                (indices change, so you can't memcpy)

 Amortized O(1): total copy work = n + n/2 + n/4 + ... ≈ 2n
```

A single insert can cost O(n), which matters for latency-sensitive code. Fix it with `with_capacity(n)` in Rust or `make(map[K]V, n)` in Go.

---

## 5. What real implementations do

### Rust: `std::HashMap` = hashbrown (SwissTable)

```
 control bytes (1 per slot)          slots (K,V pairs)
 ┌────┬────┬────┬────┬────┬────┬────┬────┐   ┌────┬────┬────┬────┬────┬────┬────┬────┐
 │0x3A│0xFF│0x7C│0x3A│0xFF│0x80│0xFF│0x51│   │ k,v│    │ k,v│ k,v│    │ ☠  │    │ k,v│
 └────┴────┴────┴────┴────┴────┴────┴────┘   └────┴────┴────┴────┴────┴────┴────┴────┘
  FULL: top bit 0, low 7 bits = h2 (7 bits of the hash)
  EMPTY = 0xFF      DELETED = 0x80
```

Lookup:
1. `h1 = hash >> 7` picks the starting group, `h2 = hash & 0x7F` is the tag.
2. Load 16 control bytes at once (SSE2/NEON) and compare against `h2` in a **single SIMD instruction**, giving a bitmask of candidate slots.
3. Only for those few candidates, do the real key comparison. False positive rate is about 1/128.
4. If the group contains an EMPTY byte, stop. Otherwise probe the next group (triangular probing).

Metadata being separate from the data means probing touches 16 bytes instead of 16 full entries, so far fewer cache misses.

Default hasher is **SipHash-1-3** with a random seed: slower, but resistant to hash-flooding DoS. For trusted keys you can swap in `FxHash` or `ahash`.

### Go: `map`

Classic (≤1.23) was bucketed chaining:

```
 hmap ──► buckets[ 2^B ]
              │
              ▼
          bucket (8 slots)
          ┌─────────────────────────────────────┐
          │ tophash[8]  (1 byte each, top 8 bits of hash)
          │ keys[8]     (stored contiguously)
          │ values[8]   (stored contiguously, avoids padding waste)
          │ overflow ──► next bucket
          └─────────────────────────────────────┘
```

Go resized **incrementally**: old buckets were evacuated a few at a time during later writes, so there's no big pause. From Go 1.24 the runtime uses a **Swiss-table design** like Rust's, with groups of 8 slots and control words.

Go also **randomizes iteration start** on purpose, so you can't depend on order.

---

## 6. Bare-metal style implementation in Rust

Open addressing, linear probing, tombstones, power-of-two capacity:

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

enum Slot<K, V> {
    Empty,
    Tombstone,
    Full(K, V),
}

pub struct Map<K, V> {
    slots: Vec<Slot<K, V>>,
    len: usize,  // live entries
    used: usize, // live + tombstones (what probing actually sees)
}

impl<K: Hash + Eq, V> Map<K, V> {
    pub fn new() -> Self {
        Self::with_cap(8)
    }

    fn with_cap(cap: usize) -> Self {
        debug_assert!(cap.is_power_of_two());
        let mut slots = Vec::with_capacity(cap);
        slots.resize_with(cap, || Slot::Empty);
        Self { slots, len: 0, used: 0 }
    }

    fn hash(k: &K) -> usize {
        let mut h = DefaultHasher::new();
        k.hash(&mut h);
        h.finish() as usize
    }

    #[inline]
    fn mask(&self) -> usize {
        self.slots.len() - 1
    }

    fn find(&self, k: &K) -> Option<usize> {
        let mask = self.mask();
        let mut i = Self::hash(k) & mask;
        loop {
            match &self.slots[i] {
                Slot::Empty => return None,                 // chain ends
                Slot::Full(kk, _) if kk == k => return Some(i),
                _ => {}                                     // tombstone or other key
            }
            i = (i + 1) & mask;                             // linear probe, wraps
        }
    }

    pub fn get(&self, k: &K) -> Option<&V> {
        let i = self.find(k)?;
        match &self.slots[i] {
            Slot::Full(_, v) => Some(v),
            _ => None,
        }
    }

    pub fn insert(&mut self, k: K, v: V) -> Option<V> {
        // keep load (including tombstones) <= 7/8 so an Empty always exists
        if (self.used + 1) * 8 > self.slots.len() * 7 {
            self.grow();
        }
        let mask = self.mask();
        let mut i = Self::hash(&k) & mask;
        let mut first_tomb = None;
        loop {
            match &mut self.slots[i] {
                Slot::Full(kk, vv) if *kk == k => {
                    return Some(std::mem::replace(vv, v)); // update in place
                }
                Slot::Tombstone => {
                    if first_tomb.is_none() {
                        first_tomb = Some(i);
                    }
                }
                Slot::Empty => break,
                _ => {}
            }
            i = (i + 1) & mask;
        }
        let target = first_tomb.unwrap_or(i);
        if matches!(self.slots[target], Slot::Empty) {
            self.used += 1; // reusing a tombstone doesn't raise `used`
        }
        self.slots[target] = Slot::Full(k, v);
        self.len += 1;
        None
    }

    pub fn remove(&mut self, k: &K) -> Option<V> {
        let i = self.find(k)?;
        self.len -= 1; // `used` unchanged: tombstone still occupies the chain
        match std::mem::replace(&mut self.slots[i], Slot::Tombstone) {
            Slot::Full(_, v) => Some(v),
            _ => None,
        }
    }

    fn grow(&mut self) {
        let new_cap = self.slots.len() * 2;
        let old = std::mem::replace(self, Self::with_cap(new_cap));
        for s in old.slots {
            if let Slot::Full(k, v) = s {
                self.insert(k, v); // rehash; tombstones are dropped here
            }
        }
    }
}
```

The same logic in Go (struct layout only; the algorithm is identical):

```go
type state uint8
const (
    empty state = iota
    tomb
    full
)

type slot[K comparable, V any] struct {
    st  state
    key K
    val V
}

type Map[K comparable, V any] struct {
    slots     []slot[K, V]
    len, used int
    hash      func(K) uint64
}

func (m *Map[K, V]) find(k K) int {
    mask := uint64(len(m.slots) - 1)
    i := m.hash(k) & mask
    for {
        s := &m.slots[i]
        if s.st == empty { return -1 }
        if s.st == full && s.key == k { return int(i) }
        i = (i + 1) & mask
    }
}
```

---

## 7. Complexity and gotchas

| Operation | Average | Worst case |
|---|---|---|
| get / insert / remove | O(1) | O(n) (all keys collide / during resize) |
| iterate | O(cap) | |
| resize | O(n), amortized O(1) per insert | |

- **Hash quality matters.** A bad hash with poor low bits clusters badly under `& mask`. Real hashers mix bits well.
- **Key invariants:** if `a == b` then `hash(a) == hash(b)`. Never mutate a key's hashed fields while it's in the map (Rust prevents this via ownership).
- **References are invalidated by resize.** Rust's borrow checker forbids holding `&V` across an insert. In Go, taking `&m[k]` isn't even allowed, because entries move.
- **Hash flooding:** an attacker who knows your hash function can craft colliding keys and degrade you to O(n) per op. That's why the default hashers are seeded randomly.
- **Cache behavior beats big-O:** open addressing with a flat array typically outperforms chaining several times over at the same complexity.
- **Competitive programming:** the default Rust `HashMap` (SipHash) is slowish. Use a custom `BuildHasher` (FxHash-style multiply-shift) or a sorted `Vec`/`BTreeMap` when keys are small. In Go, a `map[int]int` is fine, but arrays or sorting + binary search win if the key range is bounded.

If you want, I can go deeper on any piece: SwissTable SIMD probing in detail (with `core::arch` intrinsics), Robin Hood hashing with backward-shift deletion, or a system-design view (consistent hashing, distributed hash tables).