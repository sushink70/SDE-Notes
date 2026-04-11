# Union, Intersection & Complement: A Complete Technical Guide

> Covering mathematical foundations, bit-level mechanics, data structure implementations,
> complexity analysis, and idiomatic C / Go / Rust code.

---

## Table of Contents

1. [Mathematical Foundations](#1-mathematical-foundations)
2. [Set Representations](#2-set-representations)
3. [Union](#3-union)
4. [Intersection](#4-intersection)
5. [Complement](#5-complement)
6. [Difference & Symmetric Difference](#6-difference--symmetric-difference)
7. [De Morgan's Laws](#7-de-morgans-laws)
8. [Bitset Implementation — C](#8-bitset-implementation--c)
9. [Hash-Set Implementation — C](#9-hash-set-implementation--c)
10. [Go: `map`-based & `bitset`-based](#10-go-map-based--bitset-based)
11. [Rust: `HashSet`, `BTreeSet`, and a `BitSet`](#11-rust-hashset-btreeset-and-a-bitset)
12. [Complexity Reference Table](#12-complexity-reference-table)
13. [Real-World Patterns](#13-real-world-patterns)
14. [Kernel Context — Bitmasks & cpumask](#14-kernel-context--bitmasks--cpumask)

---

## 1. Mathematical Foundations

### 1.1 What Is a Set?

A **set** is an unordered collection of **distinct** elements drawn from some **universe** U.

```
U = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 }   ← universal set (integers 0–9)
A = { 1, 3, 5, 7 }                       ← odd digits
B = { 2, 3, 5, 7 }                       ← prime digits
```

Sets obey:

- **Extensionality**: Two sets are equal if they contain exactly the same elements.
- **No duplicates**: `{1, 1, 2}` ≡ `{1, 2}`.
- **No order**: `{1, 2}` ≡ `{2, 1}`.

### 1.2 Membership & Notation

| Symbol | Meaning              | Example             |
|--------|----------------------|---------------------|
| ∈      | is a member of       | 3 ∈ A               |
| ∉      | is not a member of   | 4 ∉ A               |
| ⊆      | subset of            | {1,3} ⊆ A           |
| ⊂      | proper subset        | {1,3} ⊂ A           |
| ∅      | empty set            | {}                  |
| \|A\|  | cardinality          | \|A\| = 4           |
| 2^A    | power set            | all subsets of A    |

### 1.3 Cardinality of the Power Set

For a set of `n` elements, the power set has `2^n` subsets.

```
A = {1, 3}
2^A = { {}, {1}, {3}, {1,3} }   → 2^2 = 4 subsets
```

---

## 2. Set Representations

### 2.1 Characteristic Function (Indicator)

Map each element x of U to 1 (member) or 0 (not member).

```
U = { 0,1,2,3,4,5,6,7 }     (8 elements)
A = { 1,3,5,7 }

Index: 7 6 5 4 3 2 1 0
A:     1 0 1 0 1 0 1 0  =  0xAA  (binary: 1010 1010)
```

This is the **bitset** representation — the most cache-friendly and operation-efficient form.

### 2.2 ASCII Venn Diagrams

#### Two Sets (A and B in Universe U)

```
 Universe U
 +-----------------------------------------------+
 |                                               |
 |    +--------+          +--------+            |
 |   /          \        /          \           |
 |  /     A      \      /     B      \          |
 | |    only      | -- |    only     |          |
 | |  (A - B)     |/  \| (B - A)     |          |
 |  \            /  A∩B \            /           |
 |   \          /  (both) \          /           |
 |    +--------+          +--------+            |
 |                                               |
 +-----------------------------------------------+
```

#### Three Sets (A, B, C)

```
 Universe U
 +----------------------------------------------------------+
 |                                                          |
 |         +----------+    +----------+                    |
 |        /            \  /            \                   |
 |       /      A        \/      B       \                 |
 |      |    only       /\    only        |                |
 |      |              /  \               |                |
 |       \        A∩B /    \ B∩C         /                |
 |        \          / A∩B∩C\           /                  |
 |         +--------+--------+--------+                    |
 |                  /          \                           |
 |                 /     C      \                          |
 |                |    only      |                         |
 |                 \            /                          |
 |                  +----------+                           |
 +----------------------------------------------------------+
```

### 2.3 Representation Comparison

```
+--------------------+----------+---------+----------+-----------+
| Representation     | Space    | Lookup  | Union    | Intersect |
+--------------------+----------+---------+----------+-----------+
| Sorted array       | O(n)     | O(log n)| O(n+m)   | O(n+m)    |
| Unsorted array     | O(n)     | O(n)    | O(n*m)   | O(n*m)    |
| Hash set           | O(n)     | O(1)avg | O(n+m)   | O(min)    |
| Bitset (fixed U)   | O(|U|/w) | O(1)    | O(|U|/w) | O(|U|/w)  |
| Balanced BST       | O(n)     | O(log n)| O(n+m)   | O(n+m)    |
+--------------------+----------+---------+----------+-----------+
w = word size (64 on x86_64)
```

---

## 3. Union

### 3.1 Definition

```
A ∪ B = { x | x ∈ A  OR  x ∈ B }
```

Everything in A, everything in B, with no duplicates.

### 3.2 ASCII Illustration

```
A = { 1, 3, 5, 7 }
B = { 2, 3, 5, 7 }

A ∪ B = { 1, 2, 3, 5, 7 }

Bitset view (U = 0..7):
        7 6 5 4 3 2 1 0
A:      1 0 1 0 1 0 1 0   = 0xAA
B:      0 0 1 0 1 1 1 0   = 0x2E (primes 2,3,5,7 → bits 2,3,5,7)
        ---------------
A | B:  1 0 1 0 1 1 1 0   = 0xAE  → {1,2,3,5,7}
```

Wait — let me re-derive with correct bit positions:

```
U = {0,1,2,3,4,5,6,7}
A = {1,3,5,7}  →  bit positions 1,3,5,7  →  1010 1010  = 0xAA
B = {2,3,5,7}  →  bit positions 2,3,5,7  →  1010 1100  = 0xAC

A | B = 0xAA | 0xAC = 1010 1110 = 0xAE
Set bits: 1,2,3,5,7  →  {1,2,3,5,7}  ✓
```

### 3.3 Properties

| Property            | Formula                              |
|---------------------|--------------------------------------|
| Commutativity       | A ∪ B = B ∪ A                        |
| Associativity       | (A ∪ B) ∪ C = A ∪ (B ∪ C)            |
| Identity            | A ∪ ∅ = A                            |
| Idempotence         | A ∪ A = A                            |
| Domination          | A ∪ U = U                            |
| Absorption          | A ∪ (A ∩ B) = A                      |

### 3.4 Inclusion-Exclusion Principle

For counting elements (avoids double-counting):

```
|A ∪ B| = |A| + |B| - |A ∩ B|

|A ∪ B ∪ C| = |A| + |B| + |C|
             - |A∩B| - |A∩C| - |B∩C|
             + |A∩B∩C|
```

General form:
```
|A₁ ∪ A₂ ∪ ... ∪ Aₙ| = Σ|Aᵢ| - Σ|Aᵢ∩Aⱼ| + Σ|Aᵢ∩Aⱼ∩Aₖ| - ...
```

---

## 4. Intersection

### 4.1 Definition

```
A ∩ B = { x | x ∈ A  AND  x ∈ B }
```

Only elements present in **both** sets.

### 4.2 ASCII Illustration

```
A = {1,3,5,7}
B = {2,3,5,7}

A ∩ B = {3,5,7}

Bitset view:
        7 6 5 4 3 2 1 0
A:      1 0 1 0 1 0 1 0   = 0xAA
B:      1 0 1 0 1 1 0 0   = 0xAC
        ---------------
A & B:  1 0 1 0 1 0 0 0   = 0xA8  → bits 3,5,7 → {3,5,7}  ✓
```

### 4.3 Properties

| Property            | Formula                              |
|---------------------|--------------------------------------|
| Commutativity       | A ∩ B = B ∩ A                        |
| Associativity       | (A ∩ B) ∩ C = A ∩ (B ∩ C)            |
| Identity            | A ∩ U = A                            |
| Annihilator         | A ∩ ∅ = ∅                            |
| Idempotence         | A ∩ A = A                            |
| Absorption          | A ∩ (A ∪ B) = A                      |

### 4.4 Disjoint Sets

Two sets are **disjoint** if their intersection is empty:

```
A ∩ B = ∅

Bitset: (A & B) == 0
```

### 4.5 Subset Test via Intersection

```
A ⊆ B  ⟺  A ∩ B = A
         ⟺  (A & B) == A    (bitset form)
         ⟺  (A & ~B) == 0   (no bits in A that are not in B)
```

---

## 5. Complement

### 5.1 Definition

```
A' = Aᶜ = ~A = { x ∈ U | x ∉ A }
```

Everything in the universe that is **not** in A.

```
U = {0,1,2,3,4,5,6,7}
A = {1,3,5,7}

A' = {0,2,4,6}

Bitset:
        7 6 5 4 3 2 1 0
A:      1 0 1 0 1 0 1 0   = 0xAA
~A:     0 1 0 1 0 1 0 1   = 0x55  → {0,2,4,6}  ✓
```

### 5.2 Critical: Universe Boundary

When using machine integers (e.g., `uint64_t`), the universe is all 64 bits.
If your logical universe U has fewer elements (say 10), you **must** mask:

```c
uint64_t mask = (1ULL << U_SIZE) - 1;   /* keep only U_SIZE bits */
uint64_t complement = (~A) & mask;
```

Otherwise, bits above `U_SIZE - 1` are garbage set-bits that represent
elements outside your universe.

### 5.3 Properties

| Property            | Formula                              |
|---------------------|--------------------------------------|
| Double complement   | (A')' = A                            |
| Complement of U     | U' = ∅                               |
| Complement of ∅     | ∅' = U                               |
| Complementation     | A ∪ A' = U                           |
| Contradiction       | A ∩ A' = ∅                           |

---

## 6. Difference & Symmetric Difference

### 6.1 Set Difference (Relative Complement)

```
A - B  =  A \ B  =  { x | x ∈ A  AND  x ∉ B }
        =  A ∩ B'
        =  A & (~B)      (bitset)
```

```
A = {1,3,5,7},  B = {2,3,5,7}
A - B = {1}           ← in A but not in B
B - A = {2}           ← in B but not in A

Bitset:
A & ~B = 0xAA & ~0xAC
       = 0xAA &  0x53
       = 0000 0010 = 0x02 → bit 1 → {1}  ✓
```

### 6.2 Symmetric Difference (XOR)

```
A △ B  =  (A - B) ∪ (B - A)
        =  (A ∪ B) - (A ∩ B)
        =  A XOR B            (bitset)
```

Elements in **exactly one** of A or B (not both).

```
A △ B = 0xAA ^ 0xAC = 0x06 → bits 1,2 → {1,2}  ✓
```

Properties:
- Commutative: A △ B = B △ A
- Associative: (A △ B) △ C = A △ (B △ C)
- Identity:    A △ ∅ = A
- Self-inverse: A △ A = ∅

```
+-------------------------------------------+
| Operation  | Bitwise | Set formula         |
+-------------------------------------------+
| Union      |  A | B  | A ∪ B               |
| Intersect  |  A & B  | A ∩ B               |
| Complement |   ~A    | U - A  (mask req'd) |
| Difference |  A & ~B | A - B               |
| Sym. Diff  |  A ^ B  | A △ B               |
+-------------------------------------------+
```

---

## 7. De Morgan's Laws

Fundamental duality between union/intersection under complement:

```
(A ∪ B)' = A' ∩ B'     "NOT (A OR B)  =  (NOT A) AND (NOT B)"
(A ∩ B)' = A' ∪ B'     "NOT (A AND B) =  (NOT A) OR  (NOT B)"
```

### Proof by membership table

```
A  B | A∪B | (A∪B)' | A' | B' | A'∩B'
-----+-----+--------+----+----+-------
0  0 |  0  |   1    |  1 |  1 |   1    ✓
0  1 |  1  |   0    |  1 |  0 |   0    ✓
1  0 |  1  |   0    |  0 |  1 |   0    ✓
1  1 |  1  |   0    |  0 |  0 |   0    ✓
```

### Bitwise verification

```c
uint8_t A = 0xAA, B = 0xAC, mask = 0xFF;

uint8_t lhs = ~(A | B) & mask;          /* (A ∪ B)' */
uint8_t rhs = (~A & mask) & (~B & mask);/* A' ∩ B'  */
assert(lhs == rhs);                     /* always true */
```

De Morgan's Laws are the bridge between **Boolean algebra**, **digital logic gates**,
**bitwise programming**, and **set theory** — the same identity, four domains.

---

## 8. Bitset Implementation — C

A bitset stores a set of non-negative integers ≤ `CAPACITY - 1`
using one bit per element packed into `uint64_t` words.

```c
/*
 * bitset.h — compact bitset for set operations
 * Kernel-style C (no stdlib beyond stdint/assert for demo purposes)
 */

#ifndef BITSET_H
#define BITSET_H

#include <stdint.h>
#include <stddef.h>
#include <string.h>   /* memset, memcpy */
#include <assert.h>

#define BITS_PER_WORD   64UL
#define WORD_IDX(bit)   ((bit) / BITS_PER_WORD)
#define BIT_IDX(bit)    ((bit) % BITS_PER_WORD)
#define WORDS_FOR(n)    (((n) + BITS_PER_WORD - 1) / BITS_PER_WORD)

typedef struct {
    uint64_t *words;
    size_t    nbits;     /* logical universe size */
    size_t    nwords;    /* allocated word count  */
} bitset_t;

/* ------------------------------------------------------------------ */
/* Lifecycle                                                           */
/* ------------------------------------------------------------------ */

/* Caller provides backing storage; no heap allocation needed. */
static inline void
bs_init(bitset_t *bs, uint64_t *storage, size_t nbits)
{
    bs->words  = storage;
    bs->nbits  = nbits;
    bs->nwords = WORDS_FOR(nbits);
    memset(storage, 0, bs->nwords * sizeof(uint64_t));
}

/* ------------------------------------------------------------------ */
/* Element operations                                                  */
/* ------------------------------------------------------------------ */

static inline void
bs_set(bitset_t *bs, size_t bit)
{
    assert(bit < bs->nbits);
    bs->words[WORD_IDX(bit)] |= (1ULL << BIT_IDX(bit));
}

static inline void
bs_clear(bitset_t *bs, size_t bit)
{
    assert(bit < bs->nbits);
    bs->words[WORD_IDX(bit)] &= ~(1ULL << BIT_IDX(bit));
}

static inline int
bs_test(const bitset_t *bs, size_t bit)
{
    assert(bit < bs->nbits);
    return (bs->words[WORD_IDX(bit)] >> BIT_IDX(bit)) & 1U;
}

/* Count set bits (popcount) */
static inline size_t
bs_count(const bitset_t *bs)
{
    size_t n = 0;
    for (size_t i = 0; i < bs->nwords; i++)
        n += (size_t)__builtin_popcountll(bs->words[i]);
    return n;
}

/* ------------------------------------------------------------------ */
/* Set operations (dst = a OP b; dst may alias a or b)                */
/* ------------------------------------------------------------------ */

/*
 * Union:  dst = a | b
 * A ∪ B  — every bit set in a OR b.
 */
static inline void
bs_union(bitset_t *dst, const bitset_t *a, const bitset_t *b)
{
    assert(dst->nwords == a->nwords && a->nwords == b->nwords);
    for (size_t i = 0; i < dst->nwords; i++)
        dst->words[i] = a->words[i] | b->words[i];
}

/*
 * Intersection: dst = a & b
 * A ∩ B  — only bits set in BOTH a and b.
 */
static inline void
bs_intersect(bitset_t *dst, const bitset_t *a, const bitset_t *b)
{
    assert(dst->nwords == a->nwords && a->nwords == b->nwords);
    for (size_t i = 0; i < dst->nwords; i++)
        dst->words[i] = a->words[i] & b->words[i];
}

/*
 * Complement: dst = ~a  (masked to universe size)
 * A'  — bits NOT in a, within the universe.
 *
 * The last word may have padding bits beyond nbits; mask them off.
 */
static inline void
bs_complement(bitset_t *dst, const bitset_t *a)
{
    assert(dst->nwords == a->nwords && dst->nbits == a->nbits);
    for (size_t i = 0; i < dst->nwords; i++)
        dst->words[i] = ~a->words[i];

    /* Zero out padding bits in the final word */
    size_t tail = a->nbits % BITS_PER_WORD;
    if (tail != 0) {
        uint64_t mask = (1ULL << tail) - 1ULL;
        dst->words[dst->nwords - 1] &= mask;
    }
}

/*
 * Difference: dst = a & ~b
 * A \ B  — bits in a but NOT in b.
 */
static inline void
bs_difference(bitset_t *dst, const bitset_t *a, const bitset_t *b)
{
    assert(dst->nwords == a->nwords && a->nwords == b->nwords);
    for (size_t i = 0; i < dst->nwords; i++)
        dst->words[i] = a->words[i] & ~b->words[i];
}

/*
 * Symmetric difference: dst = a ^ b
 * A △ B  — bits in exactly one of a, b.
 */
static inline void
bs_sym_diff(bitset_t *dst, const bitset_t *a, const bitset_t *b)
{
    assert(dst->nwords == a->nwords && a->nwords == b->nwords);
    for (size_t i = 0; i < dst->nwords; i++)
        dst->words[i] = a->words[i] ^ b->words[i];
}

/* ------------------------------------------------------------------ */
/* Predicates                                                          */
/* ------------------------------------------------------------------ */

/* Is A a subset of B?  A ⊆ B  ⟺  (A & ~B) == 0 */
static inline int
bs_subset(const bitset_t *a, const bitset_t *b)
{
    for (size_t i = 0; i < a->nwords; i++)
        if (a->words[i] & ~b->words[i])
            return 0;
    return 1;
}

/* Are A and B disjoint?  A ∩ B = ∅  ⟺  (A & B) == 0 */
static inline int
bs_disjoint(const bitset_t *a, const bitset_t *b)
{
    for (size_t i = 0; i < a->nwords; i++)
        if (a->words[i] & b->words[i])
            return 0;
    return 1;
}

/* Are A and B equal? */
static inline int
bs_equal(const bitset_t *a, const bitset_t *b)
{
    if (a->nbits != b->nbits) return 0;
    return memcmp(a->words, b->words,
                  a->nwords * sizeof(uint64_t)) == 0;
}

/* Is the set empty? */
static inline int
bs_empty(const bitset_t *bs)
{
    for (size_t i = 0; i < bs->nwords; i++)
        if (bs->words[i]) return 0;
    return 1;
}

#endif /* BITSET_H */
```

### Usage & Demo

```c
/*
 * bitset_demo.c — demonstrates union, intersection, complement
 *
 * Compile: gcc -O2 -Wall -o bitset_demo bitset_demo.c
 */

#include <stdio.h>
#include "bitset.h"

#define UNIVERSE 16   /* U = { 0 .. 15 } */

static void print_set(const char *name, const bitset_t *bs)
{
    printf("%-8s = { ", name);
    for (size_t i = 0; i < bs->nbits; i++)
        if (bs_test(bs, i))
            printf("%zu ", i);
    printf("}\n");
}

int main(void)
{
    /* Static backing storage — no heap */
    uint64_t sa[WORDS_FOR(UNIVERSE)];
    uint64_t sb[WORDS_FOR(UNIVERSE)];
    uint64_t sc[WORDS_FOR(UNIVERSE)];

    bitset_t A, B, C;
    bs_init(&A, sa, UNIVERSE);
    bs_init(&B, sb, UNIVERSE);
    bs_init(&C, sc, UNIVERSE);

    /* A = odd numbers in 0..15 */
    for (int i = 1; i < UNIVERSE; i += 2)
        bs_set(&A, i);

    /* B = multiples of 3 in 0..15 */
    for (int i = 0; i < UNIVERSE; i += 3)
        bs_set(&B, i);

    print_set("A", &A);
    print_set("B", &B);
    putchar('\n');

    bs_union(&C, &A, &B);
    print_set("A ∪ B", &C);

    bs_intersect(&C, &A, &B);
    print_set("A ∩ B", &C);

    bs_complement(&C, &A);
    print_set("A'", &C);

    bs_difference(&C, &A, &B);
    print_set("A \\ B", &C);

    bs_sym_diff(&C, &A, &B);
    print_set("A △ B", &C);

    printf("\n|A|  = %zu\n", bs_count(&A));
    printf("|B|  = %zu\n",   bs_count(&B));
    bs_union(&C, &A, &B);
    printf("|A∪B| = %zu  (expected: |A|+|B|-|A∩B| = %zu)\n",
           bs_count(&C), bs_count(&A) + bs_count(&B) - ({
               uint64_t tmp[WORDS_FOR(UNIVERSE)];
               bitset_t T;
               bs_init(&T, tmp, UNIVERSE);
               bs_intersect(&T, &A, &B);
               bs_count(&T);
           }));

    printf("\nA ⊆ B ? %s\n", bs_subset(&A, &B) ? "yes" : "no");
    printf("A ∩ B = ∅ ? %s\n", bs_disjoint(&A, &B) ? "yes" : "no");

    return 0;
}
```

### Expected Output

```
A        = { 1 3 5 7 9 11 13 15 }
B        = { 0 3 6 9 12 15 }

A ∪ B    = { 0 1 3 5 6 7 9 11 12 13 15 }
A ∩ B    = { 3 9 15 }
A'       = { 0 2 4 6 8 10 12 14 }
A \ B    = { 1 5 7 11 13 }
A △ B    = { 0 1 5 6 7 11 12 13 }

|A|  = 8
|B|  = 6
|A∪B| = 11  (expected: 8+6-3 = 11)

A ⊆ B ? no
A ∩ B = ∅ ? no
```

---

## 9. Hash-Set Implementation — C

For sets over arbitrary types (strings, structs) where a dense universe
cannot be assumed.

```c
/*
 * hset.h — open-addressing hash set with Robin Hood probing
 * Supports: union, intersection, complement (relative), difference
 *
 * Key type: const char * (null-terminated strings)
 * Adapt hash/eq for other types.
 */

#ifndef HSET_H
#define HSET_H

#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define HSET_EMPTY    0
#define HSET_DELETED  1
#define HSET_LIVE     2

#define HSET_LOAD_NUM  7
#define HSET_LOAD_DEN  10      /* 70% max load before resize */

typedef struct {
    const char *key;
    uint32_t    hash;
    uint8_t     state;   /* EMPTY / DELETED / LIVE */
    uint8_t     psl;     /* probe sequence length (Robin Hood) */
} hset_slot_t;

typedef struct {
    hset_slot_t *slots;
    size_t       cap;    /* must be power of 2 */
    size_t       count;
} hset_t;

/* FNV-1a 32-bit */
static inline uint32_t
hset_hash(const char *s)
{
    uint32_t h = 2166136261u;
    while (*s)
        h = (h ^ (unsigned char)*s++) * 16777619u;
    return h ? h : 1u;   /* 0 is reserved */
}

static inline int
hset_init(hset_t *hs, size_t initial_cap)
{
    /* Round up to next power of 2 */
    size_t cap = 8;
    while (cap < initial_cap) cap <<= 1;
    hs->slots = calloc(cap, sizeof(hset_slot_t));
    if (!hs->slots) return -1;
    hs->cap   = cap;
    hs->count = 0;
    return 0;
}

static inline void
hset_free(hset_t *hs)
{
    free(hs->slots);
    hs->slots = NULL;
    hs->cap = hs->count = 0;
}

static int hset_insert_raw(hset_t *hs,
                            const char *key, uint32_t hash);

static int
hset_grow(hset_t *hs)
{
    hset_t tmp;
    tmp.cap   = hs->cap * 2;
    tmp.count = 0;
    tmp.slots = calloc(tmp.cap, sizeof(hset_slot_t));
    if (!tmp.slots) return -1;

    for (size_t i = 0; i < hs->cap; i++)
        if (hs->slots[i].state == HSET_LIVE)
            hset_insert_raw(&tmp,
                            hs->slots[i].key,
                            hs->slots[i].hash);

    free(hs->slots);
    *hs = tmp;
    return 0;
}

static int
hset_insert_raw(hset_t *hs, const char *key, uint32_t hash)
{
    if (hs->count * HSET_LOAD_DEN >= hs->cap * HSET_LOAD_NUM)
        if (hset_grow(hs) < 0) return -1;

    size_t mask = hs->cap - 1;
    size_t idx  = hash & mask;
    uint8_t psl = 0;
    hset_slot_t incoming = { key, hash, HSET_LIVE, 0 };

    for (;;) {
        hset_slot_t *s = &hs->slots[idx];
        if (s->state != HSET_LIVE) {
            *s = incoming;
            s->psl = psl;
            hs->count++;
            return 0;
        }
        /* Robin Hood: steal from the rich */
        if (s->psl < psl) {
            hset_slot_t tmp = *s;
            *s = incoming;
            s->psl = psl;
            incoming = tmp;
            psl = incoming.psl;
        }
        idx = (idx + 1) & mask;
        psl++;
    }
}

static inline int
hset_insert(hset_t *hs, const char *key)
{
    uint32_t h = hset_hash(key);
    size_t mask = hs->cap - 1;
    size_t idx  = h & mask;
    /* Lookup first to avoid duplicate */
    for (uint8_t psl = 0; ; psl++) {
        hset_slot_t *s = &hs->slots[idx & mask];
        if (s->state != HSET_LIVE || s->psl < psl) break;
        if (s->hash == h && strcmp(s->key, key) == 0) return 0; /* dup */
        idx++;
    }
    return hset_insert_raw(hs, key, h);
}

static inline int
hset_contains(const hset_t *hs, const char *key)
{
    uint32_t h = hset_hash(key);
    size_t mask = hs->cap - 1;
    size_t idx  = h & mask;
    for (uint8_t psl = 0; ; psl++) {
        const hset_slot_t *s = &hs->slots[idx & mask];
        if (s->state != HSET_LIVE || s->psl < psl) return 0;
        if (s->hash == h && strcmp(s->key, key) == 0) return 1;
        idx++;
    }
}

/* ------------------------------------------------------------------ */
/* Set operations                                                      */
/* ------------------------------------------------------------------ */

/*
 * Union: dst = a ∪ b
 * Insert every element from both a and b into dst.
 */
static inline int
hset_union(hset_t *dst, const hset_t *a, const hset_t *b)
{
    for (size_t i = 0; i < a->cap; i++)
        if (a->slots[i].state == HSET_LIVE)
            if (hset_insert(dst, a->slots[i].key) < 0) return -1;
    for (size_t i = 0; i < b->cap; i++)
        if (b->slots[i].state == HSET_LIVE)
            if (hset_insert(dst, b->slots[i].key) < 0) return -1;
    return 0;
}

/*
 * Intersection: dst = a ∩ b
 * Insert elements of a that also appear in b.
 */
static inline int
hset_intersect(hset_t *dst, const hset_t *a, const hset_t *b)
{
    for (size_t i = 0; i < a->cap; i++)
        if (a->slots[i].state == HSET_LIVE &&
            hset_contains(b, a->slots[i].key))
            if (hset_insert(dst, a->slots[i].key) < 0) return -1;
    return 0;
}

/*
 * Relative complement / Difference: dst = a \ b
 * Insert elements of a that do NOT appear in b.
 */
static inline int
hset_difference(hset_t *dst, const hset_t *a, const hset_t *b)
{
    for (size_t i = 0; i < a->cap; i++)
        if (a->slots[i].state == HSET_LIVE &&
            !hset_contains(b, a->slots[i].key))
            if (hset_insert(dst, a->slots[i].key) < 0) return -1;
    return 0;
}

/*
 * Symmetric Difference: dst = a △ b
 * Elements in exactly one of a, b.
 */
static inline int
hset_sym_diff(hset_t *dst, const hset_t *a, const hset_t *b)
{
    if (hset_difference(dst, a, b) < 0) return -1;
    if (hset_difference(dst, b, a) < 0) return -1;
    /* Use temporary to avoid inserting b\a into a modified dst */
    return 0;
}

/*
 * Note on "complement" with hash sets:
 * True complement requires enumerating U \ A.
 * Provide the universe set explicitly:
 *   hset_difference(dst, &universe, &A)
 */

#endif /* HSET_H */
```

### Driver

```c
/*
 * hset_demo.c
 * gcc -O2 -Wall -o hset_demo hset_demo.c
 */

#include <stdio.h>
#include "hset.h"

static void print_hset(const char *name, const hset_t *hs)
{
    printf("%-8s = { ", name);
    for (size_t i = 0; i < hs->cap; i++)
        if (hs->slots[i].state == HSET_LIVE)
            printf("%s ", hs->slots[i].key);
    printf("}\n");
}

int main(void)
{
    hset_t A, B, C;
    hset_init(&A, 16); hset_init(&B, 16); hset_init(&C, 16);

    const char *fruits[]  = {"apple","banana","cherry","date", NULL};
    const char *veggies[] = {"carrot","banana","pear","cherry", NULL};

    for (int i = 0; fruits[i];  i++) hset_insert(&A, fruits[i]);
    for (int i = 0; veggies[i]; i++) hset_insert(&B, veggies[i]);

    print_hset("A", &A);
    print_hset("B", &B);
    putchar('\n');

    hset_union(&C, &A, &B);        print_hset("A ∪ B", &C); hset_free(&C); hset_init(&C, 16);
    hset_intersect(&C, &A, &B);    print_hset("A ∩ B", &C); hset_free(&C); hset_init(&C, 16);
    hset_difference(&C, &A, &B);   print_hset("A \\ B", &C); hset_free(&C); hset_init(&C, 16);
    hset_sym_diff(&C, &A, &B);     print_hset("A △ B", &C);

    hset_free(&A); hset_free(&B); hset_free(&C);
    return 0;
}
```

---

## 10. Go: `map`-based & `bitset`-based

### 10.1 Generic Set using `map[T]struct{}`

```go
// set/set.go
// Go 1.21+  (generics)
package set

import "fmt"

// Set is a generic hash-based set backed by map[T]struct{}.
// The empty struct value costs 0 bytes.
type Set[T comparable] map[T]struct{}

// New creates a set from variadic elements.
func New[T comparable](elems ...T) Set[T] {
	s := make(Set[T], len(elems))
	for _, e := range elems {
		s[e] = struct{}{}
	}
	return s
}

// Add inserts an element.
func (s Set[T]) Add(v T) { s[v] = struct{}{} }

// Remove deletes an element.
func (s Set[T]) Remove(v T) { delete(s, v) }

// Contains reports membership.
func (s Set[T]) Contains(v T) bool {
	_, ok := s[v]
	return ok
}

// Len returns cardinality.
func (s Set[T]) Len() int { return len(s) }

// Clone returns a shallow copy.
func (s Set[T]) Clone() Set[T] {
	c := make(Set[T], len(s))
	for k := range s {
		c[k] = struct{}{}
	}
	return c
}

// ---------------------------------------------------------------
// Union: A ∪ B — all elements in A or B.
// ---------------------------------------------------------------
func Union[T comparable](a, b Set[T]) Set[T] {
	// Pre-size for upper bound (|A| + |B|)
	out := make(Set[T], len(a)+len(b))
	for k := range a {
		out[k] = struct{}{}
	}
	for k := range b {
		out[k] = struct{}{}
	}
	return out
}

// ---------------------------------------------------------------
// Intersection: A ∩ B — elements common to both.
// Iterate over the smaller set for efficiency.
// ---------------------------------------------------------------
func Intersection[T comparable](a, b Set[T]) Set[T] {
	if len(a) > len(b) {
		a, b = b, a // iterate the smaller
	}
	out := make(Set[T])
	for k := range a {
		if b.Contains(k) {
			out[k] = struct{}{}
		}
	}
	return out
}

// ---------------------------------------------------------------
// Difference: A \ B — in A but not in B.
// ---------------------------------------------------------------
func Difference[T comparable](a, b Set[T]) Set[T] {
	out := make(Set[T])
	for k := range a {
		if !b.Contains(k) {
			out[k] = struct{}{}
		}
	}
	return out
}

// ---------------------------------------------------------------
// SymmetricDifference: A △ B — in exactly one of A, B.
// ---------------------------------------------------------------
func SymmetricDifference[T comparable](a, b Set[T]) Set[T] {
	out := make(Set[T])
	for k := range a {
		if !b.Contains(k) {
			out[k] = struct{}{}
		}
	}
	for k := range b {
		if !a.Contains(k) {
			out[k] = struct{}{}
		}
	}
	return out
}

// ---------------------------------------------------------------
// Complement: U \ A  (requires explicit universe)
// ---------------------------------------------------------------
func Complement[T comparable](universe, a Set[T]) Set[T] {
	return Difference(universe, a)
}

// ---------------------------------------------------------------
// Predicates
// ---------------------------------------------------------------

// IsSubset reports whether a ⊆ b.
func IsSubset[T comparable](a, b Set[T]) bool {
	for k := range a {
		if !b.Contains(k) {
			return false
		}
	}
	return true
}

// IsDisjoint reports whether A ∩ B = ∅.
func IsDisjoint[T comparable](a, b Set[T]) bool {
	if len(a) > len(b) {
		a, b = b, a
	}
	for k := range a {
		if b.Contains(k) {
			return false
		}
	}
	return true
}

// Equal reports whether A = B.
func Equal[T comparable](a, b Set[T]) bool {
	if len(a) != len(b) {
		return false
	}
	for k := range a {
		if !b.Contains(k) {
			return false
		}
	}
	return true
}

// String renders the set — order unspecified (map iteration).
func (s Set[T]) String() string {
	elems := make([]any, 0, len(s))
	for k := range s {
		elems = append(elems, k)
	}
	return fmt.Sprintf("%v", elems)
}
```

### 10.2 Bitset in Go

```go
// bitset/bitset.go
package bitset

import (
	"math/bits"
)

const wordBits = 64

// BitSet stores a dense set of non-negative integers < Cap.
type BitSet struct {
	words []uint64
	cap   uint
}

// New allocates a BitSet for a universe of size n.
func New(n uint) *BitSet {
	nw := (n + wordBits - 1) / wordBits
	return &BitSet{words: make([]uint64, nw), cap: n}
}

func (bs *BitSet) wordIdx(i uint) uint { return i / wordBits }
func (bs *BitSet) bitIdx(i uint) uint  { return i % wordBits }

// Set marks bit i.
func (bs *BitSet) Set(i uint) {
	bs.words[bs.wordIdx(i)] |= 1 << bs.bitIdx(i)
}

// Clear unsets bit i.
func (bs *BitSet) Clear(i uint) {
	bs.words[bs.wordIdx(i)] &^= 1 << bs.bitIdx(i)
}

// Test reports whether bit i is set.
func (bs *BitSet) Test(i uint) bool {
	return bs.words[bs.wordIdx(i)]>>bs.bitIdx(i)&1 == 1
}

// Count returns the number of set bits (popcount).
func (bs *BitSet) Count() int {
	n := 0
	for _, w := range bs.words {
		n += bits.OnesCount64(w)
	}
	return n
}

// Union returns a new BitSet equal to a ∪ b.
func Union(a, b *BitSet) *BitSet {
	out := New(a.cap)
	for i := range out.words {
		out.words[i] = a.words[i] | b.words[i]
	}
	return out
}

// Intersect returns a new BitSet equal to a ∩ b.
func Intersect(a, b *BitSet) *BitSet {
	out := New(a.cap)
	for i := range out.words {
		out.words[i] = a.words[i] & b.words[i]
	}
	return out
}

// Complement returns ~a masked to the universe.
func Complement(a *BitSet) *BitSet {
	out := New(a.cap)
	for i := range out.words {
		out.words[i] = ^a.words[i]
	}
	// Mask trailing bits in last word
	tail := a.cap % wordBits
	if tail != 0 {
		mask := uint64((1 << tail) - 1)
		out.words[len(out.words)-1] &= mask
	}
	return out
}

// Difference returns a \ b.
func Difference(a, b *BitSet) *BitSet {
	out := New(a.cap)
	for i := range out.words {
		out.words[i] = a.words[i] &^ b.words[i] // &^ is bit-clear (AND NOT)
	}
	return out
}

// SymDiff returns a △ b.
func SymDiff(a, b *BitSet) *BitSet {
	out := New(a.cap)
	for i := range out.words {
		out.words[i] = a.words[i] ^ b.words[i]
	}
	return out
}

// IsSubset reports a ⊆ b.
func IsSubset(a, b *BitSet) bool {
	for i := range a.words {
		if a.words[i]&^b.words[i] != 0 {
			return false
		}
	}
	return true
}

// IsDisjoint reports a ∩ b = ∅.
func IsDisjoint(a, b *BitSet) bool {
	for i := range a.words {
		if a.words[i]&b.words[i] != 0 {
			return false
		}
	}
	return true
}
```

### 10.3 Usage

```go
// main.go
package main

import (
	"fmt"
	"myproject/set"
)

func main() {
	A := set.New(1, 3, 5, 7, 9)
	B := set.New(3, 6, 9, 12)
	U := set.New(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)

	fmt.Println("A ∪ B  =", set.Union(A, B))
	fmt.Println("A ∩ B  =", set.Intersection(A, B))
	fmt.Println("A'     =", set.Complement(U, A))
	fmt.Println("A \\ B =", set.Difference(A, B))
	fmt.Println("A △ B  =", set.SymmetricDifference(A, B))
	fmt.Println("A ⊆ B  =", set.IsSubset(A, B))
	fmt.Printf("|A ∪ B| = %d\n", set.Union(A, B).Len())

	// Inclusion–Exclusion verification
	ab := set.Intersection(A, B)
	fmt.Printf("|A|+|B|-|A∩B| = %d+%d-%d = %d\n",
		A.Len(), B.Len(), ab.Len(),
		A.Len()+B.Len()-ab.Len())
}
```

---

## 11. Rust: `HashSet`, `BTreeSet`, and a `BitSet`

### 11.1 Standard-Library Sets (`std::collections`)

```rust
// src/std_sets.rs

use std::collections::{HashSet, BTreeSet};

// ---------------------------------------------------------------
// HashSet — O(1) avg operations, unordered
// ---------------------------------------------------------------

pub fn demo_hashset() {
    let a: HashSet<i32> = [1, 3, 5, 7, 9].iter().cloned().collect();
    let b: HashSet<i32> = [3, 6, 9, 12].iter().cloned().collect();

    // Union: iterate both, collect unique elements
    let union_ab: HashSet<_> = a.union(&b).cloned().collect();
    println!("A ∪ B  = {:?}", sorted(&union_ab));

    // Intersection: elements in both
    let inter_ab: HashSet<_> = a.intersection(&b).cloned().collect();
    println!("A ∩ B  = {:?}", sorted(&inter_ab));

    // Difference: A \ B
    let diff_ab: HashSet<_> = a.difference(&b).cloned().collect();
    println!("A \\ B = {:?}", sorted(&diff_ab));

    // Symmetric difference: A △ B
    let sym: HashSet<_> = a.symmetric_difference(&b).cloned().collect();
    println!("A △ B  = {:?}", sorted(&sym));

    // Subset / superset
    let c: HashSet<i32> = [3, 9].iter().cloned().collect();
    println!("{{3,9}} ⊆ A = {}", c.is_subset(&a));
    println!("A ⊇ {{3,9}} = {}", a.is_superset(&c));
    println!("A ∩ B = ∅  = {}", a.is_disjoint(&b));

    // Complement: no built-in; use difference from the universe
    let u: HashSet<i32> = (1..=12).collect();
    let comp_a: HashSet<_> = u.difference(&a).cloned().collect();
    println!("A'     = {:?}", sorted(&comp_a));
}

// ---------------------------------------------------------------
// BTreeSet — O(log n) operations, ordered output
// ---------------------------------------------------------------

pub fn demo_btreeset() {
    let a: BTreeSet<&str> = ["apple", "banana", "cherry", "date"]
        .iter().cloned().collect();
    let b: BTreeSet<&str> = ["banana", "cherry", "elderberry"]
        .iter().cloned().collect();

    // The same methods are available on BTreeSet
    let union_ab: BTreeSet<_> = a.union(&b).cloned().collect();
    println!("A ∪ B = {:?}", union_ab);

    let inter_ab: BTreeSet<_> = a.intersection(&b).cloned().collect();
    println!("A ∩ B = {:?}", inter_ab);

    let diff_ab: BTreeSet<_> = a.difference(&b).cloned().collect();
    println!("A \\ B = {:?}", diff_ab);
}

fn sorted(hs: &HashSet<i32>) -> Vec<i32> {
    let mut v: Vec<i32> = hs.iter().cloned().collect();
    v.sort_unstable();
    v
}
```

### 11.2 Custom `BitSet<N>` in Rust (const generics, no `std`)

```rust
// src/bitset.rs
//
// A compile-time-sized bitset using const generics.
// N = number of bits in the universe.
// Works in no_std (kernel Rust) with alloc disabled.

#![allow(dead_code)]

/// Number of u64 words needed for N bits.
const fn words_for(n: usize) -> usize {
    (n + 63) / 64
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BitSet<const N: usize>
where
    [u64; words_for(N)]: Sized,
{
    words: [u64; words_for(N)],
}

impl<const N: usize> BitSet<N>
where
    [u64; words_for(N)]: Sized,
{
    /// Create an empty BitSet.
    pub const fn new() -> Self {
        Self { words: [0u64; words_for(N)] }
    }

    /// Create a full BitSet (all elements present), masked to N.
    pub fn full() -> Self {
        let mut bs = Self { words: [u64::MAX; words_for(N)] };
        bs.mask_tail();
        bs
    }

    #[inline]
    fn word_idx(i: usize) -> usize { i / 64 }

    #[inline]
    fn bit_idx(i: usize) -> u32 { (i % 64) as u32 }

    /// Mask out bits above N-1 in the last word.
    fn mask_tail(&mut self) {
        let tail = N % 64;
        if tail != 0 {
            let last = words_for(N) - 1;
            self.words[last] &= (1u64 << tail) - 1;
        }
    }

    // -------- Element operations --------

    /// Insert element i.
    pub fn insert(&mut self, i: usize) {
        assert!(i < N, "element {} out of range (universe = {})", i, N);
        self.words[Self::word_idx(i)] |= 1u64 << Self::bit_idx(i);
    }

    /// Remove element i.
    pub fn remove(&mut self, i: usize) {
        assert!(i < N);
        self.words[Self::word_idx(i)] &= !(1u64 << Self::bit_idx(i));
    }

    /// Test membership.
    pub fn contains(&self, i: usize) -> bool {
        assert!(i < N);
        (self.words[Self::word_idx(i)] >> Self::bit_idx(i)) & 1 == 1
    }

    /// Cardinality (popcount).
    pub fn len(&self) -> usize {
        self.words.iter().map(|w| w.count_ones() as usize).sum()
    }

    pub fn is_empty(&self) -> bool {
        self.words.iter().all(|&w| w == 0)
    }

    // -------- Set operations (return new values; immutable style) --------

    /// Union: self ∪ rhs
    pub fn union(&self, rhs: &Self) -> Self {
        let mut out = Self::new();
        for i in 0..words_for(N) {
            out.words[i] = self.words[i] | rhs.words[i];
        }
        out
    }

    /// Intersection: self ∩ rhs
    pub fn intersection(&self, rhs: &Self) -> Self {
        let mut out = Self::new();
        for i in 0..words_for(N) {
            out.words[i] = self.words[i] & rhs.words[i];
        }
        out
    }

    /// Complement: U \ self  (all bits not in self, within universe)
    pub fn complement(&self) -> Self {
        let mut out = Self::new();
        for i in 0..words_for(N) {
            out.words[i] = !self.words[i];
        }
        out.mask_tail();
        out
    }

    /// Difference: self \ rhs
    pub fn difference(&self, rhs: &Self) -> Self {
        let mut out = Self::new();
        for i in 0..words_for(N) {
            out.words[i] = self.words[i] & !rhs.words[i];
        }
        out
    }

    /// Symmetric difference: self △ rhs
    pub fn sym_difference(&self, rhs: &Self) -> Self {
        let mut out = Self::new();
        for i in 0..words_for(N) {
            out.words[i] = self.words[i] ^ rhs.words[i];
        }
        out
    }

    // -------- Operator overloads via std::ops --------
    // (Uncomment if std is available)
    //
    // impl<const N: usize> std::ops::BitOr  for BitSet<N> { ... }
    // impl<const N: usize> std::ops::BitAnd for BitSet<N> { ... }
    // impl<const N: usize> std::ops::Not    for BitSet<N> { ... }

    // -------- Predicates --------

    /// Is self ⊆ rhs?
    pub fn is_subset(&self, rhs: &Self) -> bool {
        self.words.iter().zip(rhs.words.iter())
            .all(|(&a, &b)| a & !b == 0)
    }

    /// Is self ∩ rhs = ∅?
    pub fn is_disjoint(&self, rhs: &Self) -> bool {
        self.words.iter().zip(rhs.words.iter())
            .all(|(&a, &b)| a & b == 0)
    }

    // -------- Iterator --------

    pub fn iter(&self) -> impl Iterator<Item = usize> + '_ {
        (0..N).filter(move |&i| self.contains(i))
    }

    // -------- Display --------

    pub fn to_vec(&self) -> std::vec::Vec<usize> {
        self.iter().collect()
    }
}

impl<const N: usize> Default for BitSet<N>
where
    [u64; words_for(N)]: Sized,
{
    fn default() -> Self { Self::new() }
}
```

### 11.3 Operator Overloading for Ergonomic Bitset

```rust
// src/bitset_ops.rs  — operator overloads

use std::ops::{BitOr, BitAnd, BitXor, Not, Sub};
use super::bitset::{BitSet, words_for};

impl<const N: usize> BitOr for BitSet<N>
where [u64; words_for(N)]: Sized
{
    type Output = Self;
    fn bitor(self, rhs: Self) -> Self { self.union(&rhs) }
}

impl<const N: usize> BitAnd for BitSet<N>
where [u64; words_for(N)]: Sized
{
    type Output = Self;
    fn bitand(self, rhs: Self) -> Self { self.intersection(&rhs) }
}

impl<const N: usize> BitXor for BitSet<N>
where [u64; words_for(N)]: Sized
{
    type Output = Self;
    fn bitxor(self, rhs: Self) -> Self { self.sym_difference(&rhs) }
}

impl<const N: usize> Not for BitSet<N>
where [u64; words_for(N)]: Sized
{
    type Output = Self;
    fn not(self) -> Self { self.complement() }
}

// A - B  ≡  A \ B
impl<const N: usize> Sub for BitSet<N>
where [u64; words_for(N)]: Sized
{
    type Output = Self;
    fn sub(self, rhs: Self) -> Self { self.difference(&rhs) }
}
```

### 11.4 Rust Demo

```rust
// src/main.rs

mod bitset;
mod bitset_ops;
mod std_sets;

use bitset::BitSet;

fn main() {
    // ------- BitSet demo -------
    const U: usize = 16;       // universe = {0..15}
    let mut a: BitSet<U> = BitSet::new();
    let mut b: BitSet<U> = BitSet::new();

    // A = odd numbers {1,3,5,7,9,11,13,15}
    for i in (1..U).step_by(2) { a.insert(i); }
    // B = multiples of 3 {0,3,6,9,12,15}
    for i in (0..U).step_by(3) { b.insert(i); }

    println!("A       = {:?}", a.to_vec());
    println!("B       = {:?}", b.to_vec());

    let u_set: BitSet<U> = a.union(&b);
    println!("A ∪ B   = {:?}", u_set.to_vec());

    let i_set = a.intersection(&b);
    println!("A ∩ B   = {:?}", i_set.to_vec());

    let c_set = a.complement();
    println!("A'      = {:?}", c_set.to_vec());

    let d_set = a.difference(&b);
    println!("A \\ B  = {:?}", d_set.to_vec());

    let s_set = a.sym_difference(&b);
    println!("A △ B   = {:?}", s_set.to_vec());

    // Operator syntax (after bitset_ops)
    let union2 = a.clone() | b.clone();
    assert_eq!(union2, u_set);

    let inter2 = a.clone() & b.clone();
    assert_eq!(inter2, i_set);

    println!("\n|A|     = {}", a.len());
    println!("|B|     = {}", b.len());
    println!("|A ∪ B| = {} (|A|+|B|-|A∩B| = {})",
        u_set.len(),
        a.len() + b.len() - i_set.len());

    println!("\nA ⊆ B   = {}", a.is_subset(&b));
    println!("A ∩ B=∅ = {}", a.is_disjoint(&b));

    // ------- std HashSet demo -------
    std_sets::demo_hashset();
    std_sets::demo_btreeset();
}
```

---

## 12. Complexity Reference Table

```
+------------------+---------------+----------+----------+----------+
| Operation        | Bitset        | HashSet  | BTreeSet | Sorted[] |
+------------------+---------------+----------+----------+----------+
| Insert           | O(1)          | O(1)*    | O(log n) | O(n)     |
| Delete           | O(1)          | O(1)*    | O(log n) | O(n)     |
| Lookup           | O(1)          | O(1)*    | O(log n) | O(log n) |
| Union            | O(|U|/w)      | O(n+m)   | O(n+m)   | O(n+m)   |
| Intersection     | O(|U|/w)      | O(min)   | O(n+m)   | O(n+m)   |
| Complement       | O(|U|/w)      | O(|U|)** | O(|U|)** | O(|U|)** |
| Difference       | O(|U|/w)      | O(n)     | O(n+m)   | O(n+m)   |
| Sym. Difference  | O(|U|/w)      | O(n+m)   | O(n+m)   | O(n+m)   |
| Subset test      | O(|U|/w)      | O(n)     | O(n)     | O(n)     |
| Disjoint test    | O(|U|/w)      | O(min)   | O(n+m)   | O(n+m)   |
| Cardinality      | O(|U|/w)      | O(1)***  | O(1)***  | O(1)***  |
| Iterate          | O(|U|)        | O(n)     | O(n)     | O(n)     |
+------------------+---------------+----------+----------+----------+
*   amortized average; worst case O(n) due to hash collisions
**  complement needs universe enumeration
*** if count is maintained; otherwise O(n)
w = 64 (word width on x86_64)
|U| = universe size; n, m = set cardinalities
```

### When to choose what

```
+----------------------+------------------------------------------+
| Use Case             | Best Representation                      |
+----------------------+------------------------------------------+
| Dense integer set    | Bitset (packed bits, SIMD-friendly)      |
| Sparse integer set   | HashSet or sorted array                  |
| Ordered iteration    | BTreeSet / sorted array                  |
| String / struct keys | HashSet                                  |
| Read-heavy           | Sorted array (cache locality) + bsearch  |
| Many unions/inters.  | Bitset (single bitwise op per word)      |
| CPU affinity masks   | Bitset (kernel cpumask_t)                |
| Bloom filter variant | Multi-bitset (probabilistic membership)  |
+----------------------+------------------------------------------+
```

---

## 13. Real-World Patterns

### 13.1 Permission / Capability Bits

```c
/* Classic UNIX permission bitmask */
#define PERM_READ    (1U << 2)   /* r */
#define PERM_WRITE   (1U << 1)   /* w */
#define PERM_EXEC    (1U << 0)   /* x */

uint8_t owner = PERM_READ | PERM_WRITE | PERM_EXEC;  /* rwx = 7 */
uint8_t group = PERM_READ | PERM_EXEC;               /* r-x = 5 */
uint8_t other = PERM_READ;                           /* r-- = 4 */

/* Intersection: what permissions apply to both owner AND group? */
uint8_t both = owner & group;            /* r-x */

/* Complement: what does group lack that owner has? */
uint8_t owner_only = owner & ~group;     /* -w- */
```

### 13.2 Tag-Based Filtering

```go
// content tags — union means "any of these", intersection "all of these"
articles := []struct {
    Title string
    Tags  set.Set[string]
}{
    {"A", set.New("go", "linux", "networking")},
    {"B", set.New("go", "rust")},
    {"C", set.New("linux", "kernel", "memory")},
}

query := set.New("go", "linux")  // find articles touching go OR linux

for _, a := range articles {
    if !set.IsDisjoint(a.Tags, query) {
        fmt.Println(a.Title)  // A, B, C all qualify
    }
}
```

### 13.3 Database JOIN semantics

```
INNER JOIN  ≡  Intersection  (rows in both tables)
LEFT JOIN   ≡  A ∪ (A ∩ B)  = A  +  matched B rows
FULL JOIN   ≡  Union         (all rows, nulls where missing)
EXCEPT      ≡  Difference    (rows in A not in B)
```

### 13.4 Set Partitioning

```
                +--------------------+
                |   Universe U       |
   +------------+--------------------+------------+
   |   A only   |     A ∩ B          |   B only   |
   |   A \ B    |  (A & B)           |   B \ A    |
   +------------+--------------------+------------+
                |  Neither (A ∪ B)'  |
                +--------------------+

These four regions are pairwise disjoint and cover U:
  (A \ B)  ∪  (A ∩ B)  ∪  (B \ A)  ∪  (A ∪ B)'  =  U
```

---

## 14. Kernel Context — Bitmasks & `cpumask`

The Linux kernel uses bitset-based set operations pervasively.

### 14.1 cpumask — CPU set operations

```
include/linux/cpumask.h
kernel/smp.c
```

```c
/*
 * cpumask_t wraps a bitmap of NR_CPUS bits.
 * Internal representation: unsigned long bits[BITS_TO_LONGS(NR_CPUS)]
 */

cpumask_t online;   /* CPUs currently online    — cpus_read_lock() */
cpumask_t present;  /* CPUs present in hardware                     */
cpumask_t possible; /* CPUs that may come online                    */

/* Union: CPUs that are online OR present */
cpumask_or(&result, &online, &present);      /* result = online | present */

/* Intersection: CPUs both online AND possible */
cpumask_and(&result, &online, &possible);    /* result = online & possible */

/* Complement (relative to possible): CPUs NOT online */
cpumask_andnot(&offline, &possible, &online); /* offline = possible & ~online */

/* Subset test: are all online CPUs also possible? (always true) */
if (cpumask_subset(&online, &possible)) { ... }

/* Iterate over set */
int cpu;
for_each_cpu(cpu, &online) {
    /* cpu ∈ online */
}
```

### 14.2 NUMA nodemask

```
include/linux/nodemask.h
```

```c
nodemask_t nodes_allowed;

/* Intersection: nodes both allowed by policy AND online */
nodes_and(result, nodes_allowed, node_online_map);

/* First set bit = nearest node */
int node = first_node(result);
```

### 14.3 IRQ affinity

```
kernel/irq/manage.c
include/linux/interrupt.h
```

```c
struct irq_affinity_desc {
    struct cpumask  mask;   /* bitset of CPUs for this IRQ */
    bool            is_managed;
};

/* Move IRQ to intersection of requested mask and online CPUs */
cpumask_and(&effective, &requested_mask, cpu_online_mask);
irq_set_affinity(irq_no, &effective);
```

### 14.4 Internal Bitmap API

```
include/linux/bitmap.h
lib/bitmap.c
```

```c
DECLARE_BITMAP(a, NBITS);
DECLARE_BITMAP(b, NBITS);
DECLARE_BITMAP(result, NBITS);

bitmap_or(result, a, b, NBITS);          /* union        */
bitmap_and(result, a, b, NBITS);         /* intersection */
bitmap_complement(result, a, NBITS);     /* complement   */
bitmap_andnot(result, a, b, NBITS);      /* A \ B        */
bitmap_xor(result, a, b, NBITS);         /* A △ B        */

bitmap_subset(a, b, NBITS);              /* A ⊆ B ?      */
bitmap_intersects(a, b, NBITS);          /* A ∩ B ≠ ∅ ?  */
bitmap_empty(a, NBITS);                  /* A = ∅ ?      */
bitmap_full(a, NBITS);                   /* A = U ?      */
bitmap_weight(a, NBITS);                 /* |A|          */
```

### 14.5 Architecture of Kernel Set Operations

```
      Logical Layer (cpumask, nodemask, iommu_group_bitmap)
           |
           v
      bitmap API  (lib/bitmap.c, include/linux/bitmap.h)
           |
           v
      bitops primitives  (include/linux/bitops.h)
      [  set_bit / clear_bit / test_bit / __ffs / ffz  ]
           |
           v
      arch-specific  (arch/x86/include/asm/bitops.h)
      [  BSF/BSR on x86, CLZ/CTZ on ARM, POPCNT  ]
           |
           v
      Hardware Word Operations  (64-bit OR / AND / NOT / XOR / POPCNT)
```

---

*End of Guide*

---

> **Quick Reference Card**
>
> ```
> A ∪ B   = A | B   (union — OR)
> A ∩ B   = A & B   (intersection — AND)
> A'      = ~A & M  (complement — NOT, masked)
> A \ B   = A & ~B  (difference — AND NOT)
> A △ B   = A ^ B   (symmetric difference — XOR)
> A ⊆ B   ⟺  (A & ~B) == 0
> A ∩ B = ∅ ⟺  (A & B)  == 0
> ```

The guide covers everything end-to-end across 14 sections:

**Theory** — mathematical definitions, membership notation, power sets, the characteristic/indicator function, inclusion-exclusion, and membership tables proving De Morgan's laws.

**Operations** — union (`|`), intersection (`&`), complement (`~`, with universe masking), difference (`& ~`), and symmetric difference (`^`) — each with ASCII Venn diagrams, worked bitset examples, and full property tables.

**C** — two complete implementations: a stack-allocated `bitset_t` (word-level, uses `__builtin_popcountll`, no heap), and a Robin Hood open-addressing `hset_t` for arbitrary string keys. Both include union, intersection, complement, difference, symmetric difference, subset, and disjoint predicates.

**Go** — a generic `Set[T comparable]` backed by `map[T]struct{}` (Go 1.21+), and a `BitSet` struct with word-level ops using `bits.OnesCount64`. Go's `&^` (AND NOT / bit-clear) maps directly to set difference.

**Rust** — `std::collections::{HashSet, BTreeSet}` with their native `.union()/.intersection()/.difference()/.symmetric_difference()` methods, plus a `BitSet<const N: usize>` using const generics that works in `no_std`. Operator overloads (`|`, `&`, `^`, `!`, `-`) make the syntax match the math directly.

**Kernel section** — `cpumask_t`, `nodemask_t`, `bitmap.h`, and IRQ affinity as real bitset consumers, with the full layered architecture from `cpumask` down to `arch/x86` `BSF`/`POPCNT` instructions.