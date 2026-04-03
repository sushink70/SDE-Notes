# BTRFS: The Complete, In-Depth Guide
## From Kernel Internals to Production Mastery

> *"The filesystem is the soul of the OS — it determines how truth is stored, versioned, and recovered."*

---

## TABLE OF CONTENTS

```
PART I   — FOUNDATIONS
  01. What Is Btrfs & Why It Exists
  02. Historical Context & Design Philosophy
  03. The B-Tree: Core Data Structure
  04. Copy-on-Write (CoW): The Central Paradigm

PART II  — ON-DISK FORMAT & KERNEL INTERNALS
  05. On-Disk Layout & Superblock
  06. Object IDs, Keys & the Item Model
  07. Extent Trees & Block Groups
  08. Chunk Trees & Device Management

PART III — FEATURES IN DEPTH
  09. Subvolumes & Snapshots
  10. RAID in Btrfs (0, 1, 10, 5, 6, single, dup)
  11. Compression (zlib, lzo, zstd)
  12. Checksums & Data Integrity
  13. Deduplication (inline & out-of-band)
  14. Send/Receive Protocol
  15. Quota Groups (qgroups)
  16. Free Space Cache & Space Management

PART IV  — LINUX KERNEL INTEGRATION
  17. VFS Layer & Btrfs Hooks
  18. Page Cache, Writeback & Journaling
  19. Ordered vs Unordered Writes
  20. Transaction Model & Commit Protocol
  21. Memory Management (slab caches, extent buffers)

PART V   — ADMINISTRATION & OPERATIONS
  22. Formatting, Mounting & Mount Options
  23. Device Add/Remove/Replace & Balance
  24. Scrub, Check & Repair
  25. Monitoring & Debugging

PART VI  — CODE DEEP DIVES
  26. Kernel C Source Walkthrough
  27. Rust Userspace Tooling & Concepts
  28. Performance Tuning & Benchmarking

PART VII — MENTAL MODELS & MASTERY
  29. Expert Mental Models
  30. Common Pitfalls & Anti-Patterns
```

---

# PART I — FOUNDATIONS

---

## Chapter 01: What Is Btrfs & Why It Exists

### 1.1 The Problem Btrfs Solves

Before understanding Btrfs, you must understand what was *broken* with traditional filesystems.

```
TRADITIONAL FILESYSTEM PROBLEMS
═══════════════════════════════

  ext4 / xfs / fat32
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  Problem 1: NO DATA INTEGRITY VERIFICATION              │
  │  ─────────────────────────────────────────────────────  │
  │  A cosmic ray flips a bit on disk → corruption silent   │
  │  You read wrong data and never know it                  │
  │                                                         │
  │  Problem 2: NO ATOMIC MULTI-FILE OPERATIONS             │
  │  ─────────────────────────────────────────────────────  │
  │  Power cuts mid-write → partial state on disk           │
  │  fsck can repair metadata but data is GONE              │
  │                                                         │
  │  Problem 3: NO SNAPSHOTS (cheap cloning)                │
  │  ─────────────────────────────────────────────────────  │
  │  Want to backup before upgrade? Copy everything.        │
  │  On 1TB disk → takes hours, doubles storage use         │
  │                                                         │
  │  Problem 4: NO ONLINE RESIZE / MULTIPLE DEVICES         │
  │  ─────────────────────────────────────────────────────  │
  │  Adding a disk = LVM complexity, separate layer         │
  │                                                         │
  │  Problem 5: NO TRANSPARENT COMPRESSION                  │
  │  ─────────────────────────────────────────────────────  │
  │  Compress? Use a layer above. Performance penalty.      │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
```

### 1.2 What Btrfs Provides

```
BTRFS SOLUTION MATRIX
═════════════════════

  Feature                    ext4   xfs    Btrfs
  ─────────────────────────  ─────  ─────  ─────
  Per-block checksums         ✗      ✗      ✓
  Copy-on-Write               ✗      ✗      ✓
  Atomic snapshots            ✗      ✗      ✓
  Subvolumes                  ✗      ✗      ✓
  Built-in RAID               ✗      ✗      ✓
  Transparent compression     ✗      ✗      ✓
  Online defrag               ✗      ✓      ✓
  Online resize               ✓      ✓      ✓
  Multi-device mgmt           ✗      ✗      ✓
  Deduplication (inline)      ✗      ✗      ✓
  Send/Receive                ✗      ✗      ✓
  Quota groups                ✗      ✗      ✓
  Self-healing (RAID)         ✗      ✗      ✓
  fsck without unmount        ✗      ✓      ✓
```

**Btrfs** (B-tree Filesystem, pronounced "butter fs" or "better fs") was created at Oracle by Chris Mason in 2007, merged into the Linux kernel mainline in 2009 (v2.6.29).

---

## Chapter 02: Historical Context & Design Philosophy

### 2.1 Design Principles

Btrfs was designed around these core axioms:

```
BTRFS DESIGN AXIOMS
═══════════════════

  Axiom 1: NEVER OVERWRITE DATA IN PLACE
  ════════════════════════════════════════
  Old data stays until new data is safely committed.
  This is Copy-on-Write (CoW). It is the foundation
  of everything: snapshots, integrity, atomicity.

  Axiom 2: CHECKSUMS ON EVERYTHING
  ══════════════════════════════════
  Every data block, every metadata block carries a
  checksum. Silent corruption is detected instantly.

  Axiom 3: ONE UNIFIED B-TREE NAMESPACE
  ═══════════════════════════════════════
  All filesystem state (inodes, extents, directories,
  checksums) lives in a single B-tree key space.
  Elegant, unified, powerful.

  Axiom 4: TRANSACTIONS ARE ATOMIC
  ══════════════════════════════════
  Either ALL changes of a transaction are visible,
  or NONE of them are. No partial states.

  Axiom 5: STORAGE POOLS, NOT PARTITIONS
  ════════════════════════════════════════
  Multiple physical devices → one logical filesystem.
  Add/remove disks online, RAID without LVM.
```

### 2.2 The Influence of ZFS

Btrfs was heavily inspired by ZFS (from Sun Microsystems). Both share:
- Copy-on-Write
- Checksums
- Snapshots
- Pooled storage

But Btrfs is GPL-licensed (ZFS is CDDL, incompatible with the Linux kernel), written in C as a kernel module, and designed around the Linux VFS/page cache architecture.

---

## Chapter 03: The B-Tree — Core Data Structure

> **Prerequisite Concept**: Before Btrfs makes sense, you must deeply understand B-trees. This chapter builds that foundation rigorously.

### 3.1 What Is a Tree?

A **tree** is a hierarchical data structure:
- One **root** node at the top
- Each node has **children**
- Leaf nodes have no children
- Every node (except root) has exactly one **parent**

### 3.2 What Is a Binary Search Tree (BST)?

A BST stores **sorted keys** such that:
- All keys in the left subtree < current node's key
- All keys in the right subtree > current node's key

```
BST EXAMPLE
═══════════

          [50]
         /    \
      [30]    [70]
      /  \    /  \
   [20] [40] [60] [80]

  Search for 60:
  50 → go right → 70 → go left → 60 ✓
```

**Problem**: BSTs can become unbalanced (degenerate into a linked list).

### 3.3 What Is a B-Tree?

A **B-tree** (Balanced tree) of order `m` solves the balance problem:

```
B-TREE PROPERTIES (Order = m)
══════════════════════════════

  1. Every node has at most m children
  2. Every non-root node has at least ⌈m/2⌉ children
  3. The root has at least 2 children (unless it's a leaf)
  4. All leaves appear at the same level (perfectly balanced)
  5. A node with k children has k-1 keys
  6. Keys within a node are sorted in ascending order
```

```
B-TREE OF ORDER 3 (max 2 keys, max 3 children per node)
════════════════════════════════════════════════════════

                    [40 | 70]
                   /    |    \
                  /     |     \
          [10|20]    [50|60]   [80|90]
         /  |  \    /  |  \   /  |  \
       [5][15][25][45][55][65][75][85][95]

  Internal node [40|70]:
    Left subtree  → keys < 40
    Middle subtree → 40 ≤ keys < 70
    Right subtree → keys ≥ 70

  SEARCH: O(log n)  — guaranteed balanced
  INSERT: O(log n)  — may cause node splits
  DELETE: O(log n)  — may cause node merges
```

### 3.4 Why B-Trees Are Perfect for Filesystems

```
FILESYSTEM STORAGE PROPERTIES
══════════════════════════════

  ┌─────────────────────────────────────────────────────┐
  │  Disk I/O COST MODEL                                │
  │                                                     │
  │  RAM access:   ~5 nanoseconds                       │
  │  SSD access:   ~100 microseconds  (20,000× slower)  │
  │  HDD access:   ~10 milliseconds   (2,000,000× slower)│
  │                                                     │
  │  KEY INSIGHT: Minimize number of disk reads!        │
  │                                                     │
  │  B-tree node = 1 disk page (4KB or 16KB)            │
  │  Each node holds MANY keys (not just 1-2 like BST)  │
  │  Tree is WIDE and SHORT → fewer reads per search    │
  │                                                     │
  │  Example: 1 million records                         │
  │  BST height:    ~20 levels → 20 disk reads          │
  │  B-tree (4KB):  ~3 levels  →  3 disk reads  ✓       │
  └─────────────────────────────────────────────────────┘
```

### 3.5 The Btrfs B-Tree: B-Tree+

Btrfs uses a variant called a **B-Tree+** (B+ Tree):

```
B-TREE vs B+ TREE COMPARISON
══════════════════════════════

  B-Tree:                    B+ Tree (Btrfs uses this):
  ───────                    ──────────────────────────
  Data stored in ALL nodes   Data stored ONLY in leaves
  Internal nodes: keys+data  Internal nodes: keys only
  No linked leaves           Leaves linked as linked list

  B+ TREE ADVANTAGE:
  ┌───────────────────────────────────────────────┐
  │                                               │
  │  Internal nodes hold MORE keys (no data)      │
  │  → Tree is wider → fewer levels               │
  │  → Faster searches                            │
  │                                               │
  │  Leaves are linked:                           │
  │  → Range scans are O(1) per element           │
  │  → "Give me all files with inode 100-200"     │
  │     Just find 100, then walk right            │
  │                                               │
  └───────────────────────────────────────────────┘

  BTRFS B-TREE STRUCTURE:
  ═══════════════════════

  Level 2 (Root):   [ key1 | key2 | key3 ]   ← Internal node
                   /       |      |      \
  Level 1:   [k|k|k]   [k|k|k]   [k|k|k]   [k|k|k]  ← Internal
             / | | \   / | | \
  Level 0:  L  L  L  L  L  L  L  L  L ←→ L ←→ L     ← Leaves
                                          (doubly linked)

  L = Leaf node containing actual data items
```

### 3.6 B-Tree Node Anatomy in Btrfs

Every B-tree node in Btrfs has this exact on-disk structure:

```
BTRFS B-TREE NODE ON DISK (4KB or 16KB block)
═══════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │                   HEADER (101 bytes)                     │
  │  csum[32]     - Checksum of this block (SHA256/crc32c)   │
  │  fsid[16]     - Filesystem UUID (identifies this fs)     │
  │  bytenr[8]    - Byte offset of this block on disk        │
  │  flags[8]     - Node type flags                          │
  │  chunk_tree_uuid[16] - UUID of chunk tree                │
  │  generation[8]- Transaction ID when last written         │
  │  owner[8]     - Which tree owns this node                │
  │  nritems[4]   - Number of items/key-ptrs in this node    │
  │  level[1]     - 0 = leaf, >0 = internal node             │
  ├──────────────────────────────────────────────────────────┤
  │              IF INTERNAL NODE:                           │
  │              KEY POINTER PAIRS                           │
  │  ┌──────────────────────────────┐                        │
  │  │ key[17]  | blockptr[8]       │ × nritems              │
  │  │          | generation[8]     │                        │
  │  └──────────────────────────────┘                        │
  │  key = (objectid[8], type[1], offset[8])                 │
  │  blockptr = disk byte number of child node               │
  ├──────────────────────────────────────────────────────────┤
  │              IF LEAF NODE:                               │
  │              ITEM HEADERS + DATA AREA                    │
  │  ┌─────────────────────────────────────────────┐        │
  │  │ Items grow from LEFT →                      │        │
  │  │ [item0_hdr][item1_hdr][item2_hdr]...        │        │
  │  │                             ← Data grows    │        │
  │  │ ...[data2][data1][data0]                    │        │
  │  └─────────────────────────────────────────────┘        │
  │                                                          │
  │  Item header (25 bytes):                                 │
  │    key[17] + data_offset[4] + data_size[4]               │
  └──────────────────────────────────────────────────────────┘
```

---

## Chapter 04: Copy-on-Write (CoW) — The Central Paradigm

### 4.1 What Is CoW?

**Copy-on-Write** means: when you modify data, you do NOT overwrite the original location. Instead, you write the new version to a NEW location, then update pointers.

```
WITHOUT COW (Traditional In-Place Write)
══════════════════════════════════════════

  Before write:                 During write (DANGER ZONE):
  ─────────────                 ──────────────────────────
  Block 100: "Hello"            Block 100: "He????"  ← CORRUPTED
                                                       if power fails HERE

  After write:
  ────────────
  Block 100: "World"  ✓ (but data from before is GONE forever)
```

```
WITH COW (Btrfs Approach)
══════════════════════════

  Step 1: Original state
  ─────────────────────
  Block 100: "Hello"   ← Original, still intact
  Root pointer → Block 100

  Step 2: Write new version to FREE block
  ────────────────────────────────────────
  Block 100: "Hello"   ← Still intact!
  Block 200: "World"   ← New data written to fresh block

  Step 3: Update parent pointer (atomic)
  ───────────────────────────────────────
  Block 100: "Hello"   ← Now orphaned (will be freed)
  Block 200: "World"
  Root pointer → Block 200  ← Atomically updated

  KEY INSIGHT:
  If power fails at Step 2: Block 100 still valid → no corruption
  If power fails at Step 3: Root still points to 100 → valid!
  Only after Step 3 completes is the new state visible.
```

### 4.2 CoW and the B-Tree: Shadow Paging

When you modify a leaf node in Btrfs, you can't modify it in place (CoW!). Instead, you create a new version. But then the parent must be updated (it held the old block pointer). This propagates all the way to the root:

```
SHADOW PAGING: THE COW CHAIN
══════════════════════════════

  BEFORE MODIFICATION:
  ────────────────────
         [Root A]
        /         \
   [Node B]     [Node C]
   /     \
[Leaf D] [Leaf E]   ← We want to modify Leaf E

  MODIFICATION PROCESS:
  ─────────────────────

  Step 1: Write new Leaf E' (copy of E with changes)
  ┌──────────────────────────────────────────────┐
  │       [Root A]                               │
  │      /         \                             │
  │  [Node B]     [Node C]                       │
  │  /     \                                     │
  │[Leaf D][Leaf E]    [Leaf E'] ← new           │
  └──────────────────────────────────────────────┘

  Step 2: Write new Node B' pointing to E' instead of E
  ┌──────────────────────────────────────────────┐
  │       [Root A]                               │
  │      /         \                             │
  │  [Node B]     [Node C]     [Node B']← new   │
  │  /     \                   /      \          │
  │[Leaf D][Leaf E]    [Leaf D]   [Leaf E']      │
  └──────────────────────────────────────────────┘

  Step 3: Write new Root A' pointing to B' instead of B
  ┌──────────────────────────────────────────────┐
  │  [Root A]         [Root A'] ← new            │
  │  /      \         /        \                 │
  │[Node B][Node C] [Node B'] [Node C]           │
  │                 /      \                     │
  │             [Leaf D] [Leaf E']               │
  └──────────────────────────────────────────────┘

  Step 4: Superblock atomically updated to point to Root A'

  OLD CHAIN (A→B→E) freed. NEW CHAIN (A'→B'→E') is live.

  ATOMIC GUARANTEE: Superblock update is a single 512-byte
  sector write. Either it completes or it doesn't. No halfway.
```

### 4.3 CoW and Snapshots: The Magic Connection

This is where Btrfs becomes brilliant. If you take a snapshot:

```
SNAPSHOT CREATION (O(1) time, O(1) space initially)
═════════════════════════════════════════════════════

  Before snapshot:
  ────────────────
  Tree Root A → points to entire filesystem tree
  Superblock → Root A

  Take snapshot:
  ──────────────
  Original Root A  (reference count: 1 → 2)
  Snapshot Root A  (same block, different tree entry)

  ┌─────────────────────────────────────────────┐
  │                                             │
  │  SUBVOLUME:   Root A                        │
  │               │                             │
  │               └─→ [Node B] → [Leaf D]       │
  │                   [Node C] → [Leaf F]       │
  │                                             │
  │  SNAPSHOT:    Root A  ← SAME ROOT BLOCK!    │
  │               │                             │
  │               └─→ [Node B] → [Leaf D]       │
  │                   [Node C] → [Leaf F]       │
  │                                             │
  │  Both share IDENTICAL tree structure.       │
  │  Zero data duplication!                     │
  └─────────────────────────────────────────────┘

  Now modify a file in the original:
  ───────────────────────────────────
  CoW creates new Leaf D', new Node B', new Root A'
  Snapshot still points to OLD Root A (unchanged!)

  ┌─────────────────────────────────────────────┐
  │  SUBVOLUME:   Root A'                       │
  │               └─→ [Node B'] → [Leaf D'] ← modified │
  │                   [Node C] → [Leaf F]       │
  │                                             │
  │  SNAPSHOT:    Root A  ← unchanged           │
  │               └─→ [Node B] → [Leaf D] ← original   │
  │                   [Node C] → [Leaf F]       │
  │                                             │
  │  [Node C] and [Leaf F] are SHARED between   │
  │  both versions (reference counted)!         │
  └─────────────────────────────────────────────┘
```

This is the power of CoW + B-trees. Snapshots are instantaneous and space-efficient. You only pay for the differences.

---

# PART II — ON-DISK FORMAT & KERNEL INTERNALS

---

## Chapter 05: On-Disk Layout & Superblock

### 5.1 Physical Layout of a Btrfs Filesystem

```
BTRFS PHYSICAL DISK LAYOUT
════════════════════════════

  Byte Offset 0:
  ┌──────────────────────────────────────────────┐
  │  0x0000 - 0xFFFF   (64 KB)                  │
  │  RESERVED (boot sector, BIOS stuff)          │
  └──────────────────────────────────────────────┘
  ┌──────────────────────────────────────────────┐
  │  0x10000 (64 KB)                            │
  │  PRIMARY SUPERBLOCK                          │
  │  (4096 bytes = 1 page)                       │
  └──────────────────────────────────────────────┘
  ┌──────────────────────────────────────────────┐
  │  Data region begins here                     │
  │  Divided into CHUNKS                         │
  │  Each chunk = contiguous physical space      │
  │                                              │
  │  ┌─────────────────────────────────────────┐ │
  │  │ CHUNK: System (holds chunk tree)        │ │
  │  │ CHUNK: Metadata (holds all trees)       │ │
  │  │ CHUNK: Data (holds file data extents)   │ │
  │  └─────────────────────────────────────────┘ │
  └──────────────────────────────────────────────┘

  SUPERBLOCK COPIES (for redundancy):
  ────────────────────────────────────
  Copy 1: offset 0x10000       (64 KB)
  Copy 2: offset 0x4000000     (64 MB)
  Copy 3: offset 0x4000000000  (256 GB)

  All three are written atomically (same generation number).
  If primary is corrupt, kernel tries backups.
```

### 5.2 Superblock Structure (In Detail)

The superblock is the "master index" of the filesystem. It fits in 4096 bytes.

```c
/* From Linux kernel: fs/btrfs/disk-io.h and ctree.h */

/*
 * BTRFS SUPERBLOCK ON-DISK STRUCTURE
 * (Simplified — actual kernel struct is btrfs_super_block)
 */
struct btrfs_super_block {
    /* Integrity */
    u8   csum[BTRFS_CSUM_SIZE];      /* 32 bytes: checksum */
    u8   fsid[BTRFS_FSID_SIZE];      /* 16 bytes: filesystem UUID */

    /* Self-reference */
    __le64 bytenr;                   /* offset of this superblock */
    __le64 flags;                    /* superblock flags */

    /* Magic number */
    __le64 magic;                    /* 0x4D5F53665248425F "_BHRfS_M" */

    /* Transaction */
    __le64 generation;               /* current transaction ID */
    __le64 root;                     /* root tree root bytenr */
    __le64 chunk_root;               /* chunk tree root bytenr */
    __le64 log_root;                 /* log tree root bytenr */
    __le64 log_root_transid;         /* log tree transaction ID */

    /* Sizing */
    __le64 total_bytes;              /* total filesystem size */
    __le64 bytes_used;               /* bytes currently used */
    __le64 root_dir_objectid;        /* objectid of root dir */

    /* Device count */
    __le64 num_devices;              /* number of devices in fs */

    /* Block sizes */
    __le32 sectorsize;               /* sector size (4096) */
    __le32 nodesize;                 /* B-tree node size (16384) */
    __le32 leafsize;                 /* deprecated = nodesize */

    /* Features */
    __le64 compat_flags;
    __le64 compat_ro_flags;
    __le64 incompat_flags;

    /* Checksum type */
    __le16 csum_type;                /* 0=crc32c, 1=xxhash, 2=sha256, 3=blake2b */

    /* Misc */
    u8   root_level;                 /* level of root tree root */
    u8   chunk_root_level;
    u8   log_root_level;

    /* The primary device info */
    struct btrfs_dev_item dev_item;

    /* Label */
    char label[BTRFS_LABEL_SIZE];    /* 256 bytes: filesystem label */

    /* More features */
    __le64 cache_generation;
    __le64 uuid_tree_generation;

    /* Metadata UUID */
    u8   metadata_uuid[BTRFS_FSID_SIZE];

    /* Padding to 4096 bytes */
    u8   reserved[...];

    /* Bootstrap chunk array */
    u8   sys_chunk_array[BTRFS_SYSTEM_CHUNK_ARRAY_SIZE];

    /* Root backup array (older superblock backups) */
    struct btrfs_root_backup super_roots[BTRFS_NUM_BACKUP_ROOTS];
};
```

```
SUPERBLOCK FIELD EXPLANATION
══════════════════════════════

  magic = 0x4D5F53665248425F
          In ASCII: "_BHRfS_M" (reversed = "M_SfRHB_")
          This lets the kernel quickly identify Btrfs disks.

  generation = transaction ID
               Every time the filesystem commits a transaction,
               generation increments by 1. This is the "version
               number" of the filesystem state.

  root = byte offset of the ROOT TREE's root node
         The root tree contains pointers to ALL other trees!

  chunk_root = byte offset of the CHUNK TREE's root node
               The chunk tree maps logical addresses to physical.

  nodesize = size of each B-tree node (default 16KB)
             Larger nodes = fewer tree levels = fewer I/Os
```

---

## Chapter 06: Object IDs, Keys & the Item Model

### 6.1 The Btrfs Key System

Every piece of data in Btrfs is indexed by a **key**. A key has exactly three components:

```
BTRFS KEY STRUCTURE (17 bytes)
════════════════════════════════

  ┌─────────────────────────────────────────────────┐
  │  objectid  (8 bytes, u64)                       │
  │  type      (1 byte,  u8)                        │
  │  offset    (8 bytes, u64)                       │
  └─────────────────────────────────────────────────┘

  Keys are sorted: first by objectid, then type, then offset.
  This creates a total ordering across ALL items.

  Example key comparisons:
  (256, INODE_ITEM, 0) < (256, EXTENT_DATA, 4096) < (257, INODE_ITEM, 0)
```

### 6.2 Reserved Object IDs

```
BTRFS RESERVED OBJECT IDs
══════════════════════════

  Object ID    Name                    Purpose
  ──────────   ──────────────────────  ───────────────────────────────
  1            BTRFS_ROOT_TREE_OBJECTID  The root tree itself
  2            BTRFS_EXTENT_TREE        Tracks all allocated extents
  3            BTRFS_CHUNK_TREE         Maps logical→physical addresses
  4            BTRFS_DEV_TREE           Tracks devices
  5            BTRFS_FS_TREE            Default subvolume tree
  6            BTRFS_ROOT_TREE_DIR      Root dir for subvolumes
  7            BTRFS_CSUM_TREE          Stores all data checksums
  8            BTRFS_QUOTA_TREE         Quota group accounting
  9            BTRFS_UUID_TREE          UUID→subvolume mapping
  10           BTRFS_FREE_SPACE_TREE    Free space cache v2
  256          BTRFS_FIRST_FREE_OBJECTID First normal inode number
  -1 (u64max)  BTRFS_LAST_FREE_OBJECTID  Maximum inode number
```

### 6.3 Key Types

The `type` byte defines what kind of item a key represents:

```
BTRFS ITEM TYPES
═════════════════

  Type Value   Name                    Description
  ──────────   ──────────────────────  ─────────────────────────────
  0x01         INODE_ITEM              Inode stat data (size, mode, times)
  0x0C         INODE_REF               Filename in parent dir
  0x0D         INODE_EXTREF            Extended inode reference
  0x18         XATTR_ITEM              Extended attributes
  0x20         VERITY_DESC_ITEM        fs-verity descriptor
  0x24         VERITY_MERKLE_ITEM      fs-verity Merkle tree
  0x30         DIR_ITEM                Directory entry (name hash)
  0x36         DIR_INDEX               Directory index (sequence number)
  0x60         EXTENT_DATA             File extent (inline or regular)
  0x80         EXTENT_CSUM             Data checksums
  0x84         ROOT_ITEM               Subvolume/snapshot root
  0x90         BLOCK_GROUP_ITEM        Block group metadata
  0xA0         FREE_SPACE_INFO         Free space tracking v2
  0xB0         DEV_EXTENT              Physical→logical mapping
  0xD8         DEV_ITEM                Device information
  0xE4         CHUNK_ITEM              Chunk→stripe mapping
```

### 6.4 Example: Looking Up a File

Let's trace how Btrfs finds file data:

```
FILE LOOKUP WALK-THROUGH
══════════════════════════

  Goal: Read bytes 0-4095 of inode 256

  Step 1: Find INODE_ITEM
  ────────────────────────
  Search key: (256, INODE_ITEM, 0)
  → Finds inode stats: size=65536, mode=0644, mtime=...

  Step 2: Find EXTENT_DATA item
  ─────────────────────────────
  Search key: (256, EXTENT_DATA, 0)
                                 ↑
                          byte offset in file

  Returns EXTENT_DATA item:
  ┌────────────────────────────────────────────┐
  │  generation: 42                            │
  │  type: EXTENT_TYPE_REGULAR (1)             │
  │  disk_bytenr: 0x12345000  ← physical addr  │
  │  disk_num_bytes: 65536    ← extent length  │
  │  offset: 0               ← offset within  │
  │  num_bytes: 65536           the extent     │
  │  compression: 0 (none)                     │
  └────────────────────────────────────────────┘

  Step 3: Verify checksum
  ────────────────────────
  Search in CSUM TREE:
  key: (EXTENT_CSUM_OBJECTID, EXTENT_CSUM, 0x12345000)
  → Retrieve stored checksum
  → Read physical block 0x12345000
  → Compute crc32c of block
  → Compare: match? Serve data. No match? Error/repair.

  Step 4: Map logical→physical via Chunk Tree
  ────────────────────────────────────────────
  0x12345000 is a LOGICAL address.
  The Chunk Tree maps it to actual disk sectors.
  (More in Chapter 08.)
```

---

## Chapter 07: Extent Trees & Block Groups

### 7.1 What Is an Extent?

> **Key Concept — Extent**: An "extent" is a contiguous range of bytes on disk. Instead of tracking blocks one-by-one (which wastes metadata space), Btrfs tracks *runs* of contiguous blocks. "Bytes 0x1000000 through 0x1FFFFFF are allocated to file X."

```
EXTENT vs BLOCK TRACKING
══════════════════════════

  Traditional (block-by-block):
  Inode 256 uses blocks: 100, 101, 102, 103, 200, 201, 202

  ┌─────────────────────────────────────────────────────┐
  │  7 block pointers in inode (7 × 8 bytes = 56 bytes) │
  └─────────────────────────────────────────────────────┘

  Extent-based (Btrfs):
  Inode 256: extent at offset 0 → phys 0x64000, len 4 blocks
             extent at offset 4 → phys 0xC8000, len 3 blocks

  ┌─────────────────────────────────────────────────────┐
  │  2 extent records (2 × ~30 bytes = 60 bytes)        │
  │  For large sequential files: 1 extent = 1 record    │
  │  1 GB sequential file = same size as 4KB file!      │
  └─────────────────────────────────────────────────────┘
```

### 7.2 Block Groups

A **block group** is Btrfs's unit of storage management. It groups extents together and applies a RAID profile:

```
BLOCK GROUP STRUCTURE
══════════════════════

  Block Group 0: [bytes 0 - 1GB]   type=DATA,     profile=single
  Block Group 1: [bytes 1GB - 2GB] type=METADATA,  profile=DUP
  Block Group 2: [bytes 2GB - 3GB] type=DATA,     profile=RAID1
  Block Group 3: [bytes 3GB - 4GB] type=SYSTEM,   profile=DUP

  Each block group has:
  ┌────────────────────────────────────────────────────────┐
  │  BLOCK_GROUP_ITEM key: (start_bytenr, BLOCK_GROUP, len)│
  │                                                        │
  │  used:        bytes currently allocated in this group  │
  │  chunk_objectid: which chunk owns this group           │
  │  flags:       DATA | METADATA | SYSTEM                 │
  │               single | DUP | RAID0 | RAID1 | RAID5 ... │
  └────────────────────────────────────────────────────────┘

  TYPES:
  ──────
  DATA:     Stores file content (extents)
  METADATA: Stores B-tree nodes, inodes, etc.
  SYSTEM:   Stores the chunk tree only (critical!)

  All three types can coexist but are tracked separately.
  This lets Btrfs apply different RAID levels to data vs metadata.
```

### 7.3 The Extent Tree

The **extent tree** tracks every allocated piece of storage:

```
EXTENT TREE ITEMS
══════════════════

  For every allocated extent:
  key: (bytenr, EXTENT_ITEM, num_bytes)

  EXTENT_ITEM data:
  ┌──────────────────────────────────────────────────────┐
  │  refs:        reference count (how many snapshots/   │
  │               files point to this extent)            │
  │  generation:  when this extent was created           │
  │  flags:       DATA or TREE_BLOCK                     │
  │                                                      │
  │  INLINE_REF list:                                    │
  │  type: TREE_BLOCK_REF → B-tree node reference        │
  │  type: EXTENT_DATA_REF → file data reference         │
  │  type: SHARED_BLOCK_REF → shared between snapshots   │
  └──────────────────────────────────────────────────────┘

  REFERENCE COUNTING EXAMPLE:
  ────────────────────────────
  Original file → extent at 0x5000 (refs=1)
  Take snapshot → same extent (refs=2)
  Delete original file → refs goes from 2 to 1
  Delete snapshot → refs goes from 1 to 0 → extent freed!

  This is how Btrfs knows when to free an extent.
  An extent is only freed when ALL references are gone.
```

---

## Chapter 08: Chunk Trees & Device Management

### 8.1 The Address Translation Problem

Btrfs operates in **logical address space** internally. But actual data lives at **physical addresses** on potentially multiple disks. The Chunk Tree bridges this gap.

```
ADDRESS TRANSLATION LAYERS
═══════════════════════════

  Application layer: "Read file offset 4096"
        ↓
  VFS layer: "Read inode X, page Y"
        ↓
  Btrfs: EXTENT_DATA gives logical_bytenr = 0x200000
        ↓
  CHUNK TREE: 0x200000 → Device 1, offset 0x100000
              (or: Device 1 offset X AND Device 2 offset Y for RAID)
        ↓
  Block layer: Read sectors from /dev/sda at offset 0x100000
        ↓
  Disk hardware: Physical sectors returned

  WHY THIS INDIRECTION?
  ─────────────────────
  1. Allows multiple devices to appear as one pool
  2. Allows RAID striping/mirroring to be transparent
  3. Allows online device add/remove (just remap chunks)
  4. Allows balancing data across devices
```

### 8.2 Chunk Tree Structure

```
CHUNK TREE ITEMS
═════════════════

  CHUNK_ITEM key: (CHUNK_TREE_OBJECTID, CHUNK_ITEM, logical_offset)

  Chunk item data:
  ┌───────────────────────────────────────────────────────────────┐
  │  length:        size of this logical chunk (e.g., 1GB)        │
  │  owner:         which tree uses this chunk                    │
  │  stripe_len:    stripe size for RAID (e.g., 64KB)             │
  │  type:          DATA | METADATA | SYSTEM | RAID0 | RAID1 ...  │
  │  io_align:      I/O alignment                                 │
  │  num_stripes:   how many devices this chunk spans             │
  │                                                               │
  │  stripes[num_stripes]:  ← array of stripe descriptors         │
  │    devid:    which device                                      │
  │    offset:   byte offset on that device                       │
  │    dev_uuid: device UUID (for verification)                   │
  └───────────────────────────────────────────────────────────────┘

  EXAMPLE — RAID1 Chunk (mirrored):
  ──────────────────────────────────
  logical: 0x40000000 (1GB)  length: 1GB
  type: DATA | RAID1
  num_stripes: 2
  stripe[0]: devid=1, offset=0x100000000  (/dev/sda)
  stripe[1]: devid=2, offset=0x100000000  (/dev/sdb)
  → Logical byte 0x40000000 maps to BOTH disks (mirror)

  EXAMPLE — RAID0 Chunk (striped):
  ──────────────────────────────────
  logical: 0x80000000 (2GB)  length: 2GB
  type: DATA | RAID0
  stripe_len: 65536 (64KB)
  num_stripes: 2
  stripe[0]: devid=1, offset=0x200000000  (/dev/sda)
  stripe[1]: devid=2, offset=0x200000000  (/dev/sdb)
  → Logical byte X interleaved: even 64KB blocks → sda,
                                 odd  64KB blocks → sdb
```

### 8.3 The Bootstrap Problem

There's a chicken-and-egg problem: to read the chunk tree, you need to know where it is. But the chunk tree tells you where things are!

```
BOOTSTRAP RESOLUTION
═════════════════════

  The superblock contains an embedded "sys_chunk_array":
  ┌────────────────────────────────────────────────────┐
  │  sys_chunk_array[2048]:                            │
  │  Contains CHUNK_ITEM entries for the SYSTEM chunks  │
  │  (embedded directly, no lookup needed)             │
  └────────────────────────────────────────────────────┘

  Boot sequence:
  1. Read superblock at offset 0x10000 (hardcoded)
  2. Parse sys_chunk_array → find SYSTEM chunk locations
  3. Read SYSTEM chunk → find chunk tree root node
  4. Now chunk tree is readable → can map all addresses
  5. Read chunk_root from superblock → root of chunk tree
  6. Now bootstrap complete!
```

---

# PART III — FEATURES IN DEPTH

---

## Chapter 09: Subvolumes & Snapshots

### 9.1 What Is a Subvolume?

> **Key Concept — Subvolume**: A subvolume is an independently-mountable B-tree within a Btrfs filesystem. It looks and behaves like a directory, but has its own inode namespace and can be snapshotted independently. Each subvolume is a complete, self-contained filesystem tree.

```
SUBVOLUME ARCHITECTURE
═══════════════════════

  One Btrfs filesystem (one mkfs.btrfs):
  ┌──────────────────────────────────────────────────────────┐
  │                  ROOT TREE                               │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │ ROOT_ITEM (5, ROOT_ITEM, 0) → default subvolume  │   │
  │  │ ROOT_ITEM (256, ROOT_ITEM, 0) → subvol "@home"   │   │
  │  │ ROOT_ITEM (257, ROOT_ITEM, 0) → subvol "@var"    │   │
  │  │ ROOT_ITEM (258, ROOT_ITEM, 0) → snap of @home    │   │
  │  └──────────────────────────────────────────────────┘   │
  │                                                          │
  │  Each ROOT_ITEM points to a separate B-tree:             │
  │                                                          │
  │  FS_TREE (ID=5):   FS_TREE (ID=256):  FS_TREE (ID=257): │
  │  /                  /home/user/...     /var/log/...      │
  │  ├── etc/           ├── docs/          ├── syslog        │
  │  └── boot/          └── pics/          └── apt/          │
  └──────────────────────────────────────────────────────────┘

  Each subvolume has its own:
  ─ Independent inode number space (starting from 256)
  ─ Independent root for CoW operations
  ─ Independent snapshot capability
  ─ Mountable independently with: mount -o subvol=@home
```

### 9.2 Creating and Using Subvolumes

```
SUBVOLUME CREATION FLOW
════════════════════════

  btrfs subvolume create /mnt/myfs/@home
        ↓
  Kernel allocates new subvolume ID (e.g., 256)
        ↓
  Creates new ROOT_ITEM in root tree:
  key: (256, ROOT_ITEM, 0)
  data: points to a brand-new empty B-tree
        ↓
  Creates DIR_ITEM in parent to make it visible as directory
        ↓
  New subvolume is ready!

  Command Reference:
  ──────────────────
  btrfs subvolume create  <path>        # Create
  btrfs subvolume list    <path>        # List all subvolumes
  btrfs subvolume delete  <path>        # Delete (async)
  btrfs subvolume snapshot <src> <dst>  # RO or RW snapshot
  btrfs subvolume show    <path>        # Detailed info
  btrfs subvolume get-default <path>    # Get default subvol
  btrfs subvolume set-default <id> <path> # Set default
```

### 9.3 Snapshot Internals

```
SNAPSHOT CREATION INTERNALS
════════════════════════════

  btrfs subvolume snapshot /mnt/@home /mnt/@home-snap-2024

  Kernel actions:
  ───────────────
  1. Lock source subvolume tree (briefly)

  2. Allocate new subvolume ID = 258

  3. Copy ROOT_ITEM for ID=256 into new ROOT_ITEM for ID=258:
     ┌──────────────────────────────────────────────────────┐
     │  Both ROOT_ITEMs now point to SAME b-tree root block │
     │  The block's reference count is incremented to 2     │
     └──────────────────────────────────────────────────────┘

  4. Set snapshot's "parent root ID" = 256 (parent subvolume)
     Set snapshot's "stransid" = current generation

  5. Unlock source. Done!

  TIME: microseconds (regardless of data size!)
  SPACE: ~0 bytes (metadata only — shared data costs nothing)

  DIVERGENCE OVER TIME:
  ──────────────────────
  Original modified → CoW creates new blocks → private to original
  Snapshot untouched → still uses old blocks → shared with original
  Only modified blocks are exclusive; unmodified blocks are shared.
```

### 9.4 Read-Only vs Read-Write Snapshots

```
SNAPSHOT TYPES
═══════════════

  READ-ONLY snapshot:
  btrfs subvolume snapshot -r /src /dst
  ─ Cannot be modified
  ─ Used for backups (send/receive source must be RO)
  ─ Kernel sets BTRFS_ROOT_SUBVOL_RDONLY flag
  ─ Any write attempt → EROFS error

  READ-WRITE snapshot:
  btrfs subvolume snapshot /src /dst
  ─ Fully writable
  ─ Starts sharing data with source
  ─ As you write, CoW diverges them
  ─ Used for: VM disk images, testing, rollbacks

  SNAPSHOT → ROLLBACK WORKFLOW:
  ──────────────────────────────
  ┌──────────────────────────────────────────────────────────┐
  │  1. Create snapshot BEFORE upgrade:                      │
  │     btrfs subvolume snapshot -r /@ /@-backup-pre-upgrade │
  │                                                          │
  │  2. Perform upgrade                                      │
  │                                                          │
  │  3. If upgrade fails:                                    │
  │     btrfs subvolume snapshot /@-backup-pre-upgrade /@-new│
  │     btrfs subvolume set-default <id-of-@-new> /         │
  │     reboot → boots from rolled-back state!               │
  └──────────────────────────────────────────────────────────┘
```

---

## Chapter 10: RAID in Btrfs

### 10.1 RAID Basics

> **Key Concept — RAID**: "Redundant Array of Independent Disks." A way to combine multiple physical disks to achieve redundancy (survive disk failure), performance (parallel I/O), or both.

```
BTRFS RAID PROFILES OVERVIEW
══════════════════════════════

  Profile    Min Disks  Redundancy  Performance  Space Efficiency
  ─────────  ─────────  ──────────  ───────────  ────────────────
  single     1          none        1×           100%
  dup        1          1 copy      1×           50%
  RAID0      2          none        N×           100%
  RAID1      2          1 failure   1× (reads 2×) 50%
  RAID1C3    3          2 failures  1×           33%
  RAID1C4    4          3 failures  1×           25%
  RAID10     4          1 failure   N/2×         50%
  RAID5      3          1 failure   N-1×         (N-1)/N
  RAID6      4          2 failures  N-2×         (N-2)/N

  IMPORTANT: Btrfs applies profiles SEPARATELY to DATA and METADATA!
  Example: mkfs.btrfs -d raid0 -m raid1 /dev/sda /dev/sdb
           → Data striped (performance), Metadata mirrored (safety)
```

### 10.2 RAID Internals

```
RAID1 — MIRRORING
══════════════════

  Logical block 0x1000:
  ┌────────────┐    Written to    ┌────────────┐
  │  sda       │ ←─────────────→ │  sdb       │
  │  offset X  │    both disks   │  offset X  │
  └────────────┘                 └────────────┘

  Read: Can read from EITHER disk (load balancing)
  Write: Must write to BOTH disks (synchronous)
  Failure: One disk dies → data still on other disk ✓

RAID0 — STRIPING
═════════════════

  Logical block 0x0000 → sda (stripe 0)
  Logical block 0x1000 → sdb (stripe 1)
  Logical block 0x2000 → sda (stripe 2)
  Logical block 0x3000 → sdb (stripe 3)

  stripe_len = 64KB (default)

  Read/Write: Both disks work in parallel → 2× throughput
  Failure: One disk dies → ALL data LOST (no redundancy!)

RAID5 — STRIPING + DISTRIBUTED PARITY
═══════════════════════════════════════

  3 disks: sda, sdb, sdc

  Stripe 0: [data][data][parity]   ← parity on sdc
  Stripe 1: [data][parity][data]   ← parity on sdb
  Stripe 2: [parity][data][data]   ← parity on sda

  Parity = XOR of data blocks
  data1 XOR data2 = parity
  parity XOR data2 = data1  (recovery!)

  BTRFS RAID5 WARNING:
  ─────────────────────
  Btrfs RAID5/6 has a known "write hole" bug:
  If power fails DURING a partial stripe write,
  parity may be inconsistent. Data loss possible!
  NOT recommended for production until kernel ≥ 5.18+ with
  rescue=ibadroots mount option for damage control.
  Use RAID1/RAID10 for production redundancy.

DUP — SINGLE DISK MIRRORING
═════════════════════════════

  Both copies on SAME device (different locations)
  Protects against: sector-level corruption
  Does NOT protect against: full disk failure
  Default for metadata on single-disk setups.
```

### 10.3 The RAID Scrub Process

```
SCRUB PROCESS FLOW
═══════════════════

  btrfs scrub start /mnt
        ↓
  Kernel thread reads EVERY extent in filesystem
        ↓
  For each data extent:
  ┌─────────────────────────────────────────────────────┐
  │  Read block from disk                               │
  │  Compute checksum                                   │
  │  Compare with stored checksum in CSUM TREE          │
  │                                                     │
  │  Match? → OK, continue                              │
  │                                                     │
  │  Mismatch?                                          │
  │  ├── RAID1/10: Read from mirror → if mirror OK:     │
  │  │   → Copy mirror data to broken stripe            │
  │  │   → Self-heal complete!                          │
  │  │                                                  │
  │  └── Single/RAID0: Cannot heal → log error          │
  │      → btrfs scrub status shows corrected errors    │
  └─────────────────────────────────────────────────────┘

  Schedule: Run monthly with cron or systemd timer
  systemctl enable --now btrfs-scrub@-.timer
```

---

## Chapter 11: Compression

### 11.1 How Transparent Compression Works

```
COMPRESSION IN BTRFS
═════════════════════

  When you write data:
  ────────────────────
  Application writes 128KB → kernel page cache
        ↓
  Writeback starts → Btrfs intercepts before write
        ↓
  Compress 128KB:
    zlib:  → ~40KB (good ratio, slow)
    lzo:   → ~70KB (poor ratio, fast)
    zstd:  → ~35KB (best ratio, fast — RECOMMENDED)
        ↓
  Write compressed extent (~40KB) to disk
  Store EXTENT_DATA with compression flag set
        ↓
  When reading:
  Page cache miss → read 40KB from disk
  Decompress in kernel → 128KB delivered to app

  COMPRESSION DECISION TREE:
  ───────────────────────────
                 ┌──────────────────┐
                 │  New file write  │
                 └────────┬─────────┘
                          │
              ┌───────────▼───────────┐
              │  Is data compressible?│
              │  (try first 128KB)    │
              └───────┬───────┬───────┘
                      │       │
                   Yes│       │No (e.g., JPEG, video)
                      │       │
         ┌────────────▼┐    ┌─▼──────────────────────┐
         │ Write as     │    │ Mark as NOCOMPRESS,     │
         │ compressed   │    │ write as-is forever     │
         └─────────────┘    └─────────────────────────┘

  MOUNT OPTIONS:
  ──────────────
  compress=zstd          → compress all new data
  compress=zstd:3        → zstd with level 3 (1-15, default 3)
  compress-force=zstd    → compress even incompressible data
  compress=no            → disable compression

  INODE-LEVEL CONTROL:
  ──────────────────────
  chattr +c /path/to/file   → enable compression for file
  chattr -c /path/to/file   → disable compression for file
  btrfs property set /path compression zstd
```

### 11.2 Compression Algorithms Compared

```
ALGORITHM COMPARISON
═════════════════════

  zlib (levels 1-9):
  ──────────────────
  Based on DEFLATE (same as gzip).
  Good compression ratio, CPU-intensive.
  Level 1: fast, worse ratio.
  Level 9: slow, best ratio.
  Block size: 128KB.

  lzo:
  ────
  Lempel-Ziv-Oberhumer. Very fast compression/decompression.
  Worse ratio than zlib or zstd.
  Good for latency-sensitive workloads.
  Block size: 4KB (granular, less amplification).

  zstd (levels 1-15):
  ────────────────────
  Facebook's Zstandard. Best of both worlds.
  Better ratio than zlib at same speed.
  Level 1: Faster than lzo with better ratio.
  Level 15: Extremely compressed, slow.
  Recommended default: zstd:3.
  Added in kernel 4.14 (2017).

  REAL-WORLD NUMBERS (approximate):
  ───────────────────────────────────
  Workload: Software source code (highly compressible)

  Algorithm   Ratio   Compress MB/s   Decompress MB/s
  ─────────   ─────   ─────────────   ───────────────
  zlib:3      2.5×    ~100 MB/s       ~300 MB/s
  lzo         2.1×    ~400 MB/s       ~600 MB/s
  zstd:3      2.8×    ~300 MB/s       ~800 MB/s   ← Winner
  zstd:15     3.1×    ~10 MB/s        ~700 MB/s
```

---

## Chapter 12: Checksums & Data Integrity

### 12.1 The Checksum Model

```
BTRFS CHECKSUM ARCHITECTURE
════════════════════════════

  TWO TYPES of checksums:

  1. METADATA checksums (per-node):
     Every B-tree node has a checksum in its header.
     Checked on every single read of any tree node.

  2. DATA checksums (per-extent):
     Stored separately in the CSUM TREE.
     Not per-block but per-sector (4KB aligned).

  CSUM TREE STRUCTURE:
  ─────────────────────
  key: (EXTENT_CSUM_OBJECTID, EXTENT_CSUM, logical_bytenr)
  data: array of 32-bit checksums, one per sector

  Example: 1MB data extent at logical 0x40000000
  Sector size = 4KB → 256 sectors → 256 checksums
  Packed as:
  key: (EXTENT_CSUM_OBJECTID, EXTENT_CSUM, 0x40000000)
  data: [csum0][csum1][csum2]...[csum255]  (256 × 4 bytes = 1KB)

  CHECKSUM ALGORITHMS (selected at mkfs time):
  ──────────────────────────────────────────────
  crc32c   (default): 4 bytes, hardware-accelerated on x86
  xxhash   : 8 bytes, fast software hash
  sha256   : 32 bytes, cryptographic (tamper detection)
  blake2b  : 32 bytes, faster cryptographic hash

  WARNING: Cannot change checksum algorithm after mkfs!
  Use sha256/blake2b if you need cryptographic integrity.
  Use crc32c for maximum performance.
```

### 12.2 Silent Corruption Detection

```
CORRUPTION DETECTION FLOW
══════════════════════════

  User calls: read(fd, buf, 4096)
        ↓
  Btrfs checks page cache first
        ↓ (cache miss)
  Submit I/O to read block from disk
        ↓
  Block arrives in memory
        ↓
  Compute checksum of received data
        ↓
         ┌────────────────────────────┐
         │ checksum matches stored?   │
         └───────────┬────────────────┘
                     │
          YES        │          NO
           ↓         │           ↓
     Return data     │    Silent corruption detected!
     to user         │           ↓
                     │    Is there a mirror? (RAID1/10)
                     │    ┌──────────────────────────┐
                     │    │ YES → read from mirror    │
                     │    │       verify mirror OK    │
                     │    │       repair bad copy     │
                     │    │       return correct data │
                     │    │                          │
                     │    │ NO → return EIO to user  │
                     │    │      log to dmesg        │
                     │    └──────────────────────────┘
```

---

## Chapter 13: Deduplication

### 13.1 Inline Deduplication (During Write)

Btrfs performs inline dedup only for **inline extents** (small files stored inside the B-tree node itself, ≤ 2KB by default):

```
INLINE EXTENT DEDUP
════════════════════

  Small file (< 2KB) is stored INSIDE the leaf node:
  key: (inode, EXTENT_DATA, 0)
  data: [EXTENT_DATA_INLINE header][actual file bytes...]

  During write: if identical bytes exist → they share
  the same leaf node data (within extent compression).
  This is opportunistic, not aggressive.
```

### 13.2 Out-of-Band Deduplication

For larger files, dedup requires explicit tools:

```
OUT-OF-BAND DEDUP FLOW
═══════════════════════

  Tools: duperemove, bees, rmlint

  Algorithm (duperemove):
  ───────────────────────
  1. Scan all files → hash every 128KB block
  2. Build hash → [list of files+offsets] map
  3. For each group of matching hashes:
     ├── Re-read and verify byte-exact match
     └── Call FIDEDUPRANGE ioctl on kernel

  FIDEDUPRANGE ioctl (kernel API):
  ─────────────────────────────────
  Arguments:
  - src_fd, src_offset, src_length
  - dst_fd, dst_offset

  Kernel action:
  1. Verify contents are identical (byte-by-byte)
  2. Make dst_fd's extent point to same physical blocks as src_fd
  3. Increment reference count on shared extent
  4. Free duplicate physical blocks

  RESULT: Both files share identical extents.
  Write to either → CoW creates independent copy → no interference.

  ┌─────────────────────────────────────────────────┐
  │  Before dedup:                                  │
  │  file_a.iso → extent at 0x1000000 (700MB)       │
  │  file_b.iso → extent at 0x3BD0000 (700MB) ← dup│
  │  Disk used: 1400MB                              │
  │                                                 │
  │  After dedup:                                   │
  │  file_a.iso → extent at 0x1000000 (refs=2)      │
  │  file_b.iso → extent at 0x1000000 (refs=2) ← shared │
  │  Disk used: 700MB (saved 700MB!)                │
  └─────────────────────────────────────────────────┘
```

---

## Chapter 14: Send/Receive Protocol

### 14.1 Concept

Btrfs **send** generates an efficient binary stream of changes between two snapshots. **Receive** applies that stream to another filesystem. This is Btrfs's native replication protocol.

```
SEND/RECEIVE OVERVIEW
══════════════════════

  Machine A (source):         Machine B (destination):
  ─────────────────           ────────────────────────

  @snapshot-v1 ─────────────────────────────────→ @snapshot-v1
                (full send: all data)

  [time passes, files change]

  @snapshot-v2 ────── incremental send ──────────→ @snapshot-v2
                (only the DIFFERENCES
                 between v1 and v2!)

  STORAGE SAVINGS:
  ─────────────────
  Full filesystem: 500GB
  Changed files between snapshots: 2GB
  Full send:        500GB transfer
  Incremental send:   2GB transfer  ← 250× less!

  USAGE:
  ──────
  # Initial full backup
  btrfs send /mnt/@snap-v1 | ssh backup-server btrfs receive /backup/

  # Incremental update (MUCH smaller)
  btrfs send -p /mnt/@snap-v1 /mnt/@snap-v2 | \
      ssh backup-server btrfs receive /backup/

  # Local clone (filesystem copy)
  btrfs send /mnt/@snap | btrfs receive /mnt2/
```

### 14.2 Send Stream Format

```
SEND STREAM COMMANDS (binary protocol)
══════════════════════════════════════

  Stream header:
  magic[13] + version[4]

  Each command:
  cmd_type[2] + checksum[4] + length[4] + [TLV attributes...]

  Command types:
  ──────────────
  SUBVOL        - Start of new subvolume
  SNAPSHOT      - Start of snapshot (has parent)
  MKFILE        - Create empty file
  MKDIR         - Create directory
  MKNOD         - Create device node
  WRITE         - Write data to file
  CLONE         - Clone extent from another file (CoW-aware!)
  SET_XATTR     - Set extended attribute
  REMOVE_XATTR  - Remove extended attribute
  RENAME        - Rename file
  LINK          - Create hard link
  UNLINK        - Remove file
  RMDIR         - Remove directory
  CHMOD, CHOWN  - Permission changes
  UTIMES        - Update timestamps
  UPDATE_EXTENT - Efficient extent update (v2 send)
  END           - End of stream

  CLONE COMMAND — The Key Optimization:
  ───────────────────────────────────────
  When a file extent is shared between parent and child snapshot,
  send emits CLONE instead of WRITE:
  "Copy bytes 0-4095 from file X in snapshot @v1 to file Y"
  → Receiver does a Btrfs CLONE operation (no data transfer!)
  → Network: 50 bytes. Data: 4096 bytes. Saving: 99%!
```

---

## Chapter 15: Quota Groups (qgroups)

### 15.1 The Problem qgroups Solve

```
QGROUP MOTIVATION
══════════════════

  Without qgroups:
  ─────────────────
  User creates subvolume @web-app → takes 100GB
  User creates 50 snapshots → each "free" (CoW)
  Total usage:
    Unique to @web-app:  100GB
    Unique to snapshots:  50GB
    Shared blocks:       250GB
  du -sh /subvol → wildly inaccurate (shows 300GB, real is 400GB)

  With qgroups:
  ─────────────
  Kernel tracks EXACT usage:
  - Exclusive bytes: owned by this subvolume only
  - Shared bytes: referenced by this AND others
  - Referenced bytes: all bytes this subvolume points to

  Set limits:
  btrfs qgroup limit 10G /mnt/@web-app  → enforce quota
```

### 15.2 Qgroup Hierarchy

```
QGROUP HIERARCHY EXAMPLE
══════════════════════════

  Level 0 (leaf qgroups, auto-created for subvolumes):
  0/5    → default subvolume
  0/256  → @home
  0/257  → @var
  0/258  → @home-snap

  Level 1 (aggregate groups, manually created):
  1/100  → "user accounts" group
  1/200  → "system" group

  Hierarchy:
  ┌─────────────────────────────────────────────────┐
  │  1/100 (limit: 50GB total for all users)        │
  │  ├── 0/256  (@home)   → limit: 20GB             │
  │  └── 0/258  (@snap)   → limit: 10GB             │
  │                                                 │
  │  1/200 (limit: 100GB for system)                │
  │  ├── 0/5    (default) → limit: 50GB             │
  │  └── 0/257  (@var)    → limit: 30GB             │
  └─────────────────────────────────────────────────┘

  Commands:
  btrfs quota enable /mnt
  btrfs qgroup create 1/100 /mnt
  btrfs qgroup assign 0/256 1/100 /mnt
  btrfs qgroup limit 20G 0/256 /mnt
  btrfs qgroup show /mnt
```

---

## Chapter 16: Free Space Cache & Space Management

### 16.1 The Free Space Problem

Finding free space efficiently is critical for performance. Btrfs has evolved two approaches:

```
FREE SPACE TRACKING EVOLUTION
═══════════════════════════════

  V1 (free_space_cache, default before kernel 5.15):
  ─────────────────────────────────────────────────
  Stores free space info in special cache files (inode 0)
  inside each block group.
  Fast for simple cases, but can fragment badly.
  Enabled with: -o space_cache (or space_cache=v1)

  V2 (free_space_tree, default since kernel 5.15):
  ─────────────────────────────────────────────────
  Dedicated FREE_SPACE_TREE (object ID 10).
  B-tree of free space extents and bitmaps.
  More robust, better for large filesystems.
  Enabled with: -o space_cache=v2

  FREE_SPACE_TREE ITEMS:
  ──────────────────────
  FREE_SPACE_EXTENT: (block_group_start, FREE_SPACE_EXTENT, bytenr)
    → Contiguous free range: [bytenr, bytenr + len)

  FREE_SPACE_BITMAP: (block_group_start, FREE_SPACE_BITMAP, bytenr)
    → Bitmap of free sectors within a range
    → Used when free space is heavily fragmented
```

### 16.2 The Balance Operation

```
BALANCE — REDISTRIBUTING DATA
═══════════════════════════════

  What is balance?
  ─────────────────
  Balance re-reads block groups and re-writes their contents
  to new locations. This allows:
  1. Removing a device (must move its data elsewhere first)
  2. Changing RAID profile (e.g., single → RAID1)
  3. Defragmenting block group allocation
  4. Converting metadata profile

  Balance flow:
  ─────────────
  btrfs balance start -dusage=50 /mnt
                       ↑
                   Only balance data block groups
                   where usage < 50% (partially full)

  For each matching block group:
  ┌─────────────────────────────────────────────────────┐
  │  1. Read all extents in block group                 │
  │  2. Allocate space in new block group               │
  │  3. CoW-write each extent to new location           │
  │  4. Update all B-tree pointers                      │
  │  5. Free old block group                            │
  └─────────────────────────────────────────────────────┘

  Balance filters (can combine):
  ───────────────────────────────
  -d (data), -m (metadata), -s (system)
  usage=N         → only groups < N% full
  devid=N         → only blocks on device N
  drange=start,len → only in this range
  vrange=start,len → only this virtual range
  convert=PROFILE → change RAID profile

  EXAMPLE SCENARIOS:
  ──────────────────
  # Convert single to RAID1 after adding second disk:
  btrfs balance start -dconvert=raid1 -mconvert=raid1 /mnt

  # Remove a device:
  btrfs device remove /dev/sdc /mnt
  (internally runs balance to move all data off /dev/sdc first)
```

---

# PART IV — LINUX KERNEL INTEGRATION

---

## Chapter 17: VFS Layer & Btrfs Hooks

### 17.1 The Linux VFS Architecture

> **Key Concept — VFS (Virtual Filesystem Switch)**: VFS is the kernel abstraction layer that sits between system calls (open, read, write) and actual filesystem implementations. All filesystems (ext4, xfs, btrfs, nfs) implement the VFS interface. This allows the kernel to treat all filesystems uniformly.

```
VFS ARCHITECTURE
═════════════════

  User Space:
  ┌──────────────────────────────────────────────────┐
  │  open("/data/file.txt")  read(fd)  write(fd)     │
  └──────────────────────────┬───────────────────────┘
                             │ syscall
  ═══════════════════════════╪═══════════════════════
  Kernel Space:              ↓
  ┌──────────────────────────────────────────────────┐
  │             SYSTEM CALL LAYER                    │
  │  sys_open()  sys_read()  sys_write()             │
  └──────────────────────────┬───────────────────────┘
                             ↓
  ┌──────────────────────────────────────────────────┐
  │                  VFS LAYER                       │
  │  struct file_operations  *f_op                   │
  │  struct inode_operations *i_op                   │
  │  struct super_operations *s_op                   │
  │  struct address_space_operations *a_op           │
  └──────────┬────────────────────────────┬──────────┘
             ↓                            ↓
  ┌──────────────────┐          ┌──────────────────┐
  │   BTRFS          │          │    EXT4           │
  │  (implements VFS)│          │  (implements VFS) │
  └──────────────────┘          └──────────────────┘
```

### 17.2 Key VFS Operations Btrfs Implements

```c
/*
 * Btrfs implements these VFS operation tables.
 * Each is a struct of function pointers.
 * Source: fs/btrfs/file.c, inode.c, super.c
 */

/* File operations — called on open file descriptors */
const struct file_operations btrfs_file_operations = {
    .llseek         = btrfs_file_llseek,      /* lseek() */
    .read_iter      = btrfs_file_read_iter,   /* read() */
    .write_iter     = btrfs_file_write_iter,  /* write() */
    .mmap           = btrfs_file_mmap,        /* mmap() */
    .open           = generic_file_open,
    .release        = btrfs_release_file,
    .fsync          = btrfs_sync_file,        /* fsync() — important! */
    .fallocate      = btrfs_fallocate,        /* fallocate() */
    .unlocked_ioctl = btrfs_ioctl,            /* ioctl() */
};

/* Inode operations — called on filesystem objects */
const struct inode_operations btrfs_file_inode_operations = {
    .getattr    = btrfs_getattr,       /* stat() */
    .setattr    = btrfs_setattr,       /* chmod/chown */
    .listxattr  = btrfs_listxattr,
    .get_inode_acl = btrfs_get_acl,
    .set_acl    = btrfs_set_acl,
    .fiemap     = btrfs_fiemap,        /* extent map query */
};

/* Super operations — called on the filesystem itself */
const struct super_operations btrfs_super_ops = {
    .drop_inode     = btrfs_drop_inode,
    .evict_inode    = btrfs_evict_inode,  /* inode eviction */
    .put_super      = btrfs_put_super,    /* unmount */
    .sync_fs        = btrfs_sync_fs,      /* sync() */
    .statfs         = btrfs_statfs,       /* df command */
    .remount_fs     = btrfs_remount,
    .freeze_fs      = btrfs_freeze,       /* snapshot prep */
    .unfreeze_fs    = btrfs_unfreeze,
    .show_options   = btrfs_show_options,
};

/* Address space operations — page cache interface */
const struct address_space_operations btrfs_aops = {
    .read_folio     = btrfs_read_folio,   /* read a page */
    .writepages     = btrfs_writepages,   /* flush dirty pages */
    .readahead      = btrfs_readahead,    /* read-ahead */
    .write_begin    = btrfs_write_begin,  /* before write to page */
    .write_end      = btrfs_write_end,    /* after write to page */
    .dirty_folio    = btrfs_dirty_folio,  /* mark page dirty */
    .migrate_folio  = btrfs_migrate_folio,
    .invalidate_folio = btrfs_invalidate_folio,
};
```

---

## Chapter 18: Page Cache, Writeback & Journaling

### 18.1 The Linux Page Cache

> **Key Concept — Page Cache**: The kernel caches file data in RAM using 4KB "pages." When you read a file, it goes to page cache. Subsequent reads are served from RAM. Writes go to page cache first (fast!), then async writeback to disk.

```
PAGE CACHE + BTRFS INTERACTION
═══════════════════════════════

  Write flow:
  ───────────
  write(fd, buf, 4096)
        ↓
  VFS: copy buf to page cache page
  Mark page as DIRTY
  Return immediately to user (fast! O(1) perceived write)
        ↓
  [kernel writeback daemon runs]
  btrfs_writepages() called:
        ↓
  Group dirty pages into extents (contiguous → one extent)
        ↓
  Begin Btrfs transaction
        ↓
  Find free space (via free space tree)
        ↓
  CoW: write data to new disk location
        ↓
  Update EXTENT_DATA item in file tree
        ↓
  Update checksum in csum tree
        ↓
  Commit transaction (update root, update superblock)
        ↓
  Pages marked clean

  ORDERING CONSTRAINT:
  ─────────────────────
  Data MUST reach disk before metadata pointing to it!
  Otherwise: metadata says data is at block X,
             but block X hasn't been written yet.
  Power fail = inaccessible data.

  Btrfs solves this with ORDERED mode (Chapter 19).
```

### 18.2 Comparison: Journaling vs CoW

Traditional filesystems use journaling. Btrfs uses CoW. Understanding the difference is crucial:

```
JOURNALING (ext4 data=ordered mode)
════════════════════════════════════

  Write file data:
  1. Write new data to journal (log)                [disk write 1]
  2. Write journal commit record                     [disk write 2]
  3. Write data to final location (in-place update)  [disk write 3]
  4. Update metadata (inode, dir, etc.)              [disk write 4]
  5. Write journal checkpoint                        [disk write 5]

  Total: 5 writes (journal amplification!)
  Recovery: Replay journal on crash → consistent state

COPY-ON-WRITE (Btrfs)
══════════════════════

  Write file data:
  1. Write new data to free location                 [disk write 1]
  2. Update B-tree (CoW chain from leaf to root)     [disk write 2-4]
  3. Atomic superblock update → new generation live  [disk write 5]

  Total: ~5 writes too, but NO separate journal!
  Recovery: Old superblock generation still valid → just use it.
  The filesystem is ALWAYS consistent!
  (There's still a log tree for fsync optimization — see Chapter 20)

COMPARISON:
────────────
           Journaling              CoW (Btrfs)
           ──────────              ───────────
Write amp: 2-3×                    1× (no journal dup)
Random IO: Fast (in-place)         Slower (need free block)
Sequential: Fast                   Fast
Recovery:  Replay journal          Just use old tree (instant!)
Snapshots: Not possible            Trivial (O(1))
```

---

## Chapter 19: Ordered Writes & the Transaction Model

### 19.1 Write Ordering in Btrfs

```
BTRFS WRITE ORDERING GUARANTEE
════════════════════════════════

  RULE: Data extents must be durably written before
        the metadata tree nodes that reference them
        are committed.

  Why? If metadata says "data is at block X" but
  block X hasn't been written yet → crash → data lost.

  IMPLEMENTATION:
  ───────────────
  Each transaction has an "ordered list":
  - When a data extent is queued for write: add to ordered list
  - Transaction CANNOT commit until ALL items in ordered
    list have completed their I/O

  ┌───────────────────────────────────────────────────────┐
  │  Transaction N begins                                 │
  │                                                       │
  │  Phase 1: Ordered writes                             │
  │  ├── Write data extents to disk (async)              │
  │  └── Wait for ALL data I/O completions               │
  │                                                       │
  │  Phase 2: Metadata CoW                               │
  │  ├── Write new leaf nodes (with new extent pointers) │
  │  ├── Write new internal nodes                        │
  │  └── Write new roots                                 │
  │                                                       │
  │  Phase 3: Superblock commit                          │
  │  └── Atomically update superblock → transaction done │
  │                                                       │
  │  Transaction N is now durable.                       │
  └───────────────────────────────────────────────────────┘
```

### 19.2 The Transaction System

```c
/*
 * BTRFS TRANSACTION SYSTEM
 * Source: fs/btrfs/transaction.h, transaction.c
 */

/* Transaction states */
enum btrfs_trans_state {
    TRANS_STATE_RUNNING,           /* Transaction is active */
    TRANS_STATE_COMMIT_PREP,       /* About to commit */
    TRANS_STATE_COMMIT_START,      /* Commit started */
    TRANS_STATE_COMMIT_DOING,      /* Writing metadata */
    TRANS_STATE_UNBLOCKED,         /* New transactions allowed */
    TRANS_STATE_COMPLETED,         /* Fully committed */
};

struct btrfs_transaction {
    u64 transid;                   /* Transaction ID (generation) */
    
    /*
     * Reference counting: how many handles are open.
     * Transaction can't commit while refs > 0.
     */
    refcount_t use_count;
    
    enum btrfs_trans_state state;
    
    /* Dirty B-tree nodes waiting to be written */
    struct list_head dirty_bgs;    /* dirty block groups */
    struct list_head io_bgs;       /* block groups being written */
    
    /* Ordered extents: data writes in progress */
    atomic_t     num_extents;
    struct list_head ordered_operations;
    
    /* Delayed references (deferred extent tree updates) */
    struct btrfs_delayed_ref_root delayed_refs;
    
    /* Timing */
    ktime_t start_time;
};

/*
 * Transaction handle: one per kernel operation (syscall).
 * Multiple handles can share one transaction.
 */
struct btrfs_trans_handle {
    u64 transid;
    u64 bytes_reserved;            /* Reserved metadata space */
    struct btrfs_transaction *transaction;
    struct btrfs_fs_info *fs_info;
    
    /* How many tree modifications this handle can make */
    unsigned long blocks_used;
    unsigned long blocks_reserved;
    
    bool dirty;                    /* Did we modify anything? */
};

/*
 * USAGE PATTERN in kernel code:
 *
 * struct btrfs_trans_handle *trans;
 * trans = btrfs_start_transaction(root, num_items);
 * if (IS_ERR(trans)) return PTR_ERR(trans);
 *
 * // ... do work: insert items, delete items ...
 * btrfs_insert_item(trans, root, &key, &data, data_size);
 *
 * btrfs_end_transaction(trans);  // releases handle, may trigger commit
 */
```

### 19.3 Transaction Commit Protocol

```
TRANSACTION COMMIT SEQUENCE (Detailed)
════════════════════════════════════════

  Trigger: 30 seconds elapsed, OR dirty pages > threshold,
           OR explicit sync(), fsync(), or balance

  Step 1: Block new transactions (briefly)
  ─────────────────────────────────────────
  Set state = COMMIT_PREP
  Wait for all current trans handles to finish

  Step 2: Flush ordered extents
  ──────────────────────────────
  Submit all dirty data pages to block layer
  Wait for all ordered extent I/O to complete
  (This ensures data is on disk before metadata)

  Step 3: Run delayed references
  ───────────────────────────────
  "Delayed refs" = deferred extent tree updates
  (Adding/removing references is expensive; batch them)
  Process all pending reference count changes
  Update extent tree accordingly

  Step 4: Write dirty block groups
  ──────────────────────────────────
  Block group usage has changed (allocations/frees)
  Write updated BLOCK_GROUP_ITEM entries

  Step 5: CoW-write all dirty tree nodes
  ────────────────────────────────────────
  All modified B-tree nodes are dirty (in memory)
  Write them all to disk (CoW: new locations)

  Step 6: Write the log tree (if needed)
  ────────────────────────────────────────
  If any fsync() calls happened within this transaction,
  write the log tree to disk (for fast fsync recovery)

  Step 7: Write the new roots
  ─────────────────────────────
  Write ROOT_ITEM entries for all modified trees

  Step 8: Write the superblock
  ──────────────────────────────
  New generation number
  New root tree bytenr
  Write to ALL superblock copies (64KB, 64MB, 256GB)
  Use FLUSH + FUA (Force Unit Access) to ensure durability

  Step 9: Free old tree blocks
  ──────────────────────────────
  Old CoW versions of nodes/leaves/extents are now unreferenced
  Add them to the free space tree
  (They're not freed immediately — kept for a few transactions
   for safety, then returned to free pool)

  COMMIT COMPLETE. Generation N is durable.
```

---

## Chapter 20: Memory Management (Extent Buffers & Slab Caches)

### 20.1 Extent Buffers

> **Key Concept — Extent Buffer**: Btrfs doesn't use the page cache for B-tree nodes. Instead, it uses "extent buffers" — kernel objects that wrap one or more pages and represent a single B-tree node. They have their own reference counting and locking.

```c
/*
 * EXTENT BUFFER STRUCTURE
 * Source: fs/btrfs/extent_io.h
 */
struct extent_buffer {
    u64 start;              /* Logical address on disk */
    unsigned long len;      /* Size (= nodesize, e.g. 16384) */
    
    /* Locking */
    struct rw_semaphore lock;
    
    /* Reference counting */
    atomic_t refs;
    
    /* State flags */
    unsigned long bflags;   /* EXTENT_BUFFER_DIRTY, _UPTODATE, etc. */
    
    /* Pages backing this buffer */
    /* For 16KB node on 4KB page system: 4 pages */
    int     num_pages;
    struct page **pages;    /* array of pages */
    
    /* Radix tree (for fast lookup by address) */
    /* Cached in btrfs_fs_info->buffer_radix */
};

/*
 * READING A B-TREE NODE:
 *
 * eb = btrfs_find_create_tree_block(fs_info, bytenr, owner, level);
 *   → Look up in radix tree (cache hit?)
 *   → If not found: allocate extent_buffer, allocate pages, submit I/O
 *   → Check checksum after read
 *
 * btrfs_read_extent_buffer(eb, ...);
 *   → Wait for I/O, verify checksum
 *
 * Now you can read B-tree data:
 * nritems = btrfs_header_nritems(eb);
 * level   = btrfs_header_level(eb);
 *
 * If leaf (level == 0):
 *   btrfs_item_key_to_cpu(eb, &key, slot);
 *   ptr = btrfs_item_ptr(eb, slot, struct btrfs_inode_item);
 *
 * When done:
 * free_extent_buffer(eb);  → decrement ref, may free pages
 */
```

### 20.2 Key Kernel Slab Caches

```c
/*
 * BTRFS SLAB CACHE ALLOCATIONS
 * Source: fs/btrfs/super.c btrfs_init_cachep()
 *
 * "Slab cache" = kernel memory pool for fixed-size objects.
 * Faster than kmalloc() for frequently allocated objects.
 */

/* Inode in memory */
static struct kmem_cache *btrfs_inode_cachep;
/* struct btrfs_inode = VFS inode + btrfs-specific fields */

/* Delayed inodes (for deferred metadata writes) */
static struct kmem_cache *delayed_node_cache;

/* Path objects for tree traversal */
static struct kmem_cache *btrfs_path_cachep;

/* Ordered extents */
static struct kmem_cache *btrfs_ordered_extent_cachep;

/* Transaction handles */
static struct kmem_cache *btrfs_trans_handle_cachep;

/* Delayed references (for batched extent tree updates) */
static struct kmem_cache *btrfs_delayed_ref_head_cachep;
static struct kmem_cache *btrfs_delayed_tree_ref_cachep;
static struct kmem_cache *btrfs_delayed_data_ref_cachep;

/*
 * BTRFS INODE IN MEMORY:
 * Embeds VFS inode for efficiency (no separate alloc)
 */
struct btrfs_inode {
    /* VFS inode — MUST be first! */
    struct inode vfs_inode;
    
    /* Btrfs-specific fields */
    struct btrfs_root *root;
    struct btrfs_key location;        /* (objectid, INODE_ITEM, 0) */
    
    u64 generation;                   /* last modified transaction */
    u64 sequence;                     /* dir sequence for readdir */
    u64 last_trans;
    u64 logged_trans;
    
    /* Flags */
    u32 flags;                        /* BTRFS_INODE_COMPRESS, etc. */
    u32 ro_flags;
    
    /* Extent locking */
    struct extent_io_tree io_tree;
    struct extent_io_tree file_extent_tree;
    
    /* Ordered extent list */
    spinlock_t ordered_tree_lock;
    struct rb_root ordered_tree;
    
    /* Compression */
    u8 prop_compress;                 /* from property inheritance */
    u8 defrag_compress;
    
    /* Delayed node for async metadata writes */
    struct btrfs_delayed_node *delayed_node;
};

/* To get btrfs_inode from VFS inode: */
/* BTRFS_I(inode) → container_of(inode, struct btrfs_inode, vfs_inode) */
```

---

# PART V — ADMINISTRATION & OPERATIONS

---

## Chapter 21: The Log Tree (Journal for fsync)

### 21.1 Why a Log Tree?

Btrfs's full transaction commit takes time (flush data, CoW metadata, etc.). But `fsync()` must guarantee durability immediately. The **log tree** is Btrfs's optimization:

```
LOG TREE CONCEPT
════════════════

  Problem:
  ─────────
  fsync() must ensure data survives a crash.
  Full transaction commit = expensive (all dirty data).
  Many apps call fsync() constantly (databases, editors).

  Solution: Per-subvolume LOG TREE
  ──────────────────────────────────
  Log tree = small, fast B-tree that records recent fsync'd
  changes WITHIN the current transaction.

  fsync() flow:
  ─────────────
  1. Write dirty pages for this file to disk (ordered)
  2. Write MODIFIED items (inode, extents) to LOG TREE
  3. Commit the LOG TREE (much smaller than full commit)
  4. fsync() returns — file is durable

  Crash recovery:
  ────────────────
  On mount after crash:
  1. Read superblock — get current generation
  2. Check if log_root_transid > last committed transid
  3. If YES: replay log tree (apply its changes)
  4. Log tree replayed → remove it → mount normally

  LOG TREE INTERACTION WITH FULL COMMIT:
  ────────────────────────────────────────
  When full transaction commits:
  All log tree changes are absorbed into the main trees.
  Log tree is cleared.
  Next fsync() starts a fresh log tree.
```

---

## Chapter 22: Formatting, Mounting & Mount Options

### 22.1 mkfs.btrfs Options

```
MKFS.BTRFS REFERENCE
═════════════════════

  Basic:
  ──────
  mkfs.btrfs /dev/sda
  mkfs.btrfs -L "MyLabel" /dev/sda           # Set label
  mkfs.btrfs -n 16384 /dev/sda               # Node size (16KB default)
  mkfs.btrfs -s 4096 /dev/sda               # Sector size

  Multi-device:
  ─────────────
  mkfs.btrfs /dev/sda /dev/sdb /dev/sdc     # Pool of 3 disks

  RAID profiles:
  ──────────────
  mkfs.btrfs -d raid0 -m raid1 /dev/sda /dev/sdb
                ↑data profile  ↑metadata profile

  mkfs.btrfs -d raid1 -m raid1 /dev/sda /dev/sdb   # Full mirror
  mkfs.btrfs -d raid10 -m raid10 /dev/sd{a..d}      # RAID10, 4 disks
  mkfs.btrfs -d single -m dup /dev/sda               # Single disk, safe

  Checksum:
  ─────────
  mkfs.btrfs --csum sha256 /dev/sda         # Cryptographic checksums
  mkfs.btrfs --csum blake2b /dev/sda        # Blake2b (faster than sha256)

  Features:
  ─────────
  mkfs.btrfs --features no-holes /dev/sda   # Sparse file optimization
  mkfs.btrfs --features free-space-tree /dev/sda  # V2 free space cache
```

### 22.2 Mount Options Reference

```
BTRFS MOUNT OPTIONS (complete reference)
══════════════════════════════════════════

  PERFORMANCE:
  ─────────────
  noatime              → don't update access times (big perf boost)
  nodatasum            → disable checksums for data (DANGEROUS!)
  nodatacow            → disable CoW for data (like ext4 for databases)
                         WARNING: also disables checksums!
  autodefrag           → automatic background defragmentation
  max_inline=SIZE      → max size for inline extents (default 2048)
  commit=N             → transaction commit interval in seconds (default 30)

  COMPRESSION:
  ─────────────
  compress=zstd:3      → compress all new data with zstd level 3
  compress-force=lzo   → compress even incompressible data
  compress=no          → disable compression

  SPACE:
  ───────
  space_cache=v2       → use free space tree v2 (recommended)
  space_cache=no       → disable space cache (slow, debugging only)
  discard=async        → async SSD TRIM (recommended for SSDs)
  discard=sync         → synchronous TRIM (slow)

  SUBVOLUME:
  ──────────
  subvol=@home         → mount specific subvolume by name
  subvolid=256         → mount specific subvolume by ID

  RECOVERY:
  ──────────
  recovery             → enable recovery mode (deprecated)
  rescue=usebackuproot → try backup superroots on corruption
  rescue=nologreplay   → skip log tree replay (dangerous!)
  rescue=ignorebadroots → skip bad tree roots
  rescue=ignoredatacsums → skip data checksum verification (get data out!)
  degraded             → mount even if RAID is missing devices

  DEBUGGING:
  ──────────
  enospc_debug         → verbose ENOSPC (no space) debugging
  flushoncommit        → flush page cache on each commit (slower, safer)
  treelog              → enable log tree (default on; use nologreplay to skip)
  notreelog            → disable log tree (all fsyncs do full commits)

  EXAMPLE - DESKTOP OPTIMAL:
  ──────────────────────────
  UUID=xxxx / btrfs defaults,noatime,compress=zstd:3,space_cache=v2,discard=async 0 0

  EXAMPLE - DATABASE SERVER:
  ──────────────────────────
  /dev/sda /mnt btrfs nodatacow,noatime,space_cache=v2 0 0
  (databases do their own checksumming + journaling)
```

---

## Chapter 23: Device Add/Remove/Replace & Balance

```
DEVICE OPERATIONS WORKFLOW
═══════════════════════════

  ADD A DEVICE:
  ─────────────
  btrfs device add /dev/sdc /mnt
  → Adds /dev/sdc to the filesystem pool
  → Device is now usable but data isn't balanced to it yet
  → Run balance to spread data:
     btrfs balance start -dconvert=raid1 /mnt

  REMOVE A DEVICE:
  ─────────────────
  btrfs device remove /dev/sdb /mnt
  → Internally: run balance to move all data OFF /dev/sdb
  → Then deregister the device
  → Device is now free
  → This may take hours on large filesystems!

  REPLACE A DEVICE (online, no downtime):
  ────────────────────────────────────────
  btrfs replace start /dev/sdb /dev/sdd /mnt
  → Read all data from /dev/sdb, write to /dev/sdd
  → Works even if /dev/sdb is failing (reads from mirrors)
  → Monitor: btrfs replace status /mnt
  → Cancel:  btrfs replace cancel /mnt

  DEVICE USAGE:
  ─────────────
  btrfs filesystem usage /mnt
  btrfs device usage /mnt
  btrfs device stats /mnt     ← Shows per-device error counters!

  DEVICE STATS (critical for monitoring):
  ────────────────────────────────────────
  btrfs device stats /dev/sda
  Output:
  /dev/sda:
    write_io_errs    0    ← should be 0
    read_io_errs     0    ← should be 0
    flush_io_errs    0    ← should be 0
    corruption_errs  0    ← should be 0 (fatal if > 0!)
    generation_errs  0    ← should be 0
```

---

## Chapter 24: Scrub, Check & Repair

```
SCRUB — ONLINE INTEGRITY CHECK
════════════════════════════════

  btrfs scrub start /mnt
  btrfs scrub status /mnt     ← while running
  btrfs scrub cancel /mnt
  btrfs scrub resume /mnt     ← resume if interrupted

  Output:
  ───────
  Scrub started:    Mon Sep 25 10:30:00 2023
  Status:           finished
  Duration:         0:02:45
  Total to scrub:   128.50GiB
  Rate:             797.26MiB/s
  Error summary:    no errors found

  If errors found:
  ─────────────────
  Error summary: corrected=2, unrecoverable=0, no_csum=0
  corrected   → Found corruption, repaired from mirror ✓
  unrecoverable → Found corruption, no mirror to repair from ✗

BTRFS CHECK — OFFLINE INTEGRITY CHECK
═══════════════════════════════════════

  WARNING: Do NOT run btrfs check on a mounted filesystem!
  (Unlike fsck for ext4, btrfs check is destructive if filesystem is live)

  btrfs check /dev/sda             ← read-only check
  btrfs check --repair /dev/sda    ← DANGEROUS! Only as last resort

  btrfs check modes:
  ──────────────────
  (default)                → Full check, very slow (hours on large FS)
  --mode=lowmem            → Low memory usage (slower but works on big FS)
  --check-data-csum        → Verify data checksums too (very slow!)

FILESYSTEM RESCUE
═══════════════════

  SCENARIO 1: Superblock corrupted
  mount -o rescue=usebackuproot /dev/sda /mnt
  → Tries superblock copies at 64MB and 256GB offsets

  SCENARIO 2: Log tree corrupted
  mount -o rescue=nologreplay /dev/sda /mnt
  → Skips log replay (lose last few seconds of data)
  → Then run: btrfs check --clear-space-cache v2 /dev/sda

  SCENARIO 3: Extent tree corrupted
  btrfs rescue zero-log /dev/sda    ← clear log tree
  btrfs rescue fix-device-size /dev/sda
  btrfs rescue chunk-recover /dev/sda  ← rebuild chunk tree from dev extents
  btrfs rescue super-recover /dev/sda  ← try backup superblocks

  BTRFS RESTORE — DATA RECOVERY
  ───────────────────────────────
  btrfs restore /dev/sda /recovery-dir/
  → Read-only extraction of files from damaged filesystem
  → Does NOT repair FS, just extracts what it can read
  → Use when filesystem is too damaged to mount
```

---

# PART VI — CODE DEEP DIVES

---

## Chapter 25: Kernel C Source Walkthrough

### 25.1 B-Tree Search — The Core Algorithm

```c
/*
 * BTRFS B-TREE SEARCH
 * Source: fs/btrfs/ctree.c — btrfs_search_slot()
 *
 * This is THE central function of Btrfs. Everything
 * (reads, writes, deletes) goes through this.
 *
 * Returns: 0 if found, 1 if not found, < 0 if error
 * On success: path->nodes[0] = leaf node
 *             path->slots[0] = slot (index) within leaf
 */
int btrfs_search_slot(struct btrfs_trans_handle *trans,
                      struct btrfs_root *root,
                      const struct btrfs_key *key,
                      struct btrfs_path *path,
                      int ins_len,    /* > 0 if we'll insert */
                      int cow)        /* 1 if we'll modify (CoW the path) */
{
    struct extent_buffer *b;  /* current node */
    int slot;                 /* slot within current node */
    int ret;
    int level;
    int lowest_level = 0;

    /* Start from the root node */
    b = btrfs_root_node(root);
    level = btrfs_header_level(b);

    /* Traverse from root down to leaf */
    while (level > lowest_level) {
        /* Binary search within this internal node */
        slot = btrfs_bin_search(b, 0, key, &ret);

        /*
         * Binary search returns the slot where key
         * would be inserted. Adjust for internal nodes:
         * key-ptr pairs mean we follow the pointer BEFORE
         * the first key that's greater than our search key.
         */
        if (ret && slot > 0)
            slot -= 1;

        /* CoW this node if we'll modify the tree */
        if (cow) {
            ret = btrfs_cow_block(trans, root, b,
                                  path->nodes[level + 1],
                                  path->slots[level + 1],
                                  &b, ...);
            if (ret) goto done;
        }

        /* Record path for backtracking */
        path->nodes[level] = b;
        path->slots[level] = slot;

        /* Follow the key pointer to the child node */
        b = read_node_slot(fs_info, b, slot);
        level--;
    }

    /* Now b is a leaf node (level == 0) */
    /* Binary search within the leaf */
    slot = btrfs_bin_search(b, 0, key, &ret);

    path->nodes[0] = b;
    path->slots[0] = slot;

    /* ret == 0: exact match found */
    /* ret == 1: key not found, slot is insertion point */
    return ret;
done:
    return ret;
}

/*
 * BTRFS PATH STRUCTURE
 * Remembers which node/slot we're at for each level.
 * Like a "stack of breadcrumbs" from root to leaf.
 */
struct btrfs_path {
    struct extent_buffer *nodes[BTRFS_MAX_LEVEL];  /* node at each level */
    int slots[BTRFS_MAX_LEVEL];                    /* slot at each level */
    
    /* Locks held */
    u8 locks[BTRFS_MAX_LEVEL];
    
    /* Keep path locked after search? */
    int reada;
    int leave_spinning;
    
    /* Skip locking (for read-only, no concurrent writes) */
    int skip_locking;
    
    /* Hint for search start */
    int lowest_level;
};
```

### 25.2 CoW Block — Making a Node Writable

```c
/*
 * COW A B-TREE BLOCK
 * Source: fs/btrfs/ctree.c — btrfs_cow_block()
 *
 * Creates a new copy of a tree node at a new location.
 * This is the copy in "copy-on-write."
 */
static noinline int btrfs_cow_block(struct btrfs_trans_handle *trans,
                                    struct btrfs_root *root,
                                    struct extent_buffer *buf,   /* original */
                                    struct extent_buffer *parent,/* parent node */
                                    int parent_slot,
                                    struct extent_buffer **cow_ret,
                                    enum btrfs_lock_nesting nest)
{
    struct btrfs_fs_info *fs_info = root->fs_info;
    struct extent_buffer *cow;   /* new CoW copy */
    
    /*
     * Is this block already in the current transaction?
     * (i.e., was it already CoW'd this transaction?)
     * If so, no need to CoW again — just use it.
     */
    if (btrfs_header_generation(buf) == trans->transid &&
        !btrfs_header_flag(buf, BTRFS_HEADER_FLAG_WRITTEN)) {
        *cow_ret = buf;
        return 0;  /* Already CoW'd, reuse */
    }

    /*
     * Allocate a new block from free space.
     * This is the KEY STEP: find a free location on disk.
     */
    ret = btrfs_alloc_tree_block(trans, root,
                                 parent ? btrfs_node_blockptr(parent, parent_slot) : 0,
                                 root->root_key.objectid,
                                 &disk_key,
                                 btrfs_header_level(buf),
                                 search_start, empty_size,
                                 nest);
    cow = btrfs_init_new_buffer(trans, root, ...);

    /* Copy all data from old block to new block */
    copy_extent_buffer_full(cow, buf);

    /* Update the generation number in the new block */
    btrfs_set_header_generation(cow, trans->transid);

    /* Clear the WRITTEN flag (not yet committed) */
    btrfs_clear_header_flag(cow, BTRFS_HEADER_FLAG_WRITTEN);

    /* Update parent to point to new block instead of old */
    if (parent) {
        btrfs_set_node_blockptr(parent, parent_slot,
                                cow->start);           /* new physical addr */
        btrfs_set_node_ptr_generation(parent, parent_slot,
                                      trans->transid);
        btrfs_mark_buffer_dirty(trans, parent);
    } else {
        /* This is the root! Update root's bytenr */
        root->node = cow;
        atomic_inc(&cow->refs);
    }

    /* Queue the old block for freeing (after transaction commits) */
    btrfs_free_tree_block(trans, btrfs_root_id(root), buf, ...);

    free_extent_buffer(buf);
    *cow_ret = cow;
    return 0;
}
```

### 25.3 Reading an Inode

```c
/*
 * READING AN INODE FROM B-TREE
 * Source: fs/btrfs/inode.c — btrfs_read_locked_inode()
 *
 * Given an inode number, find it in the B-tree and
 * populate the in-memory inode struct.
 */
static int btrfs_read_locked_inode(struct inode *inode,
                                   struct btrfs_path *path)
{
    struct btrfs_fs_info *fs_info = inode_to_fs_info(inode);
    struct btrfs_root *root;
    struct extent_buffer *leaf;
    struct btrfs_inode_item *inode_item;
    struct btrfs_key location;
    int maybe_acls;
    u32 rdev;
    int ret;

    root = BTRFS_I(inode)->root;

    /* Build the key: (inode_number, INODE_ITEM, 0) */
    location.objectid = btrfs_ino(BTRFS_I(inode));
    location.type = BTRFS_INODE_ITEM_KEY;
    location.offset = 0;

    /* Search the B-tree */
    ret = btrfs_lookup_inode(NULL, root, path, &location, 0);
    if (ret > 0)
        ret = -ENOENT;  /* Inode doesn't exist */
    if (ret)
        goto failed;

    /* Got it! Extract the leaf and slot */
    leaf = path->nodes[0];
    inode_item = btrfs_item_ptr(leaf, path->slots[0],
                                struct btrfs_inode_item);

    /*
     * Populate VFS inode from on-disk btrfs_inode_item.
     * These are the standard Unix inode fields.
     */
    inode->i_mode   = btrfs_inode_mode(leaf, inode_item);
    set_nlink(inode, btrfs_inode_nlink(leaf, inode_item));
    
    i_uid_write(inode, btrfs_inode_uid(leaf, inode_item));
    i_gid_write(inode, btrfs_inode_gid(leaf, inode_item));
    
    btrfs_inode_set_file_extent_range(BTRFS_I(inode), 0,
                      btrfs_inode_nbytes(leaf, inode_item));
    inode->i_size   = btrfs_inode_size(leaf, inode_item);
    inode->i_blocks = btrfs_inode_nblocks(leaf, inode_item);

    /* Timestamps */
    inode_set_atime(inode,
        btrfs_timespec_sec(leaf, &inode_item->atime),
        btrfs_timespec_nsec(leaf, &inode_item->atime));
    inode_set_mtime(inode,
        btrfs_timespec_sec(leaf, &inode_item->mtime),
        btrfs_timespec_nsec(leaf, &inode_item->mtime));
    inode_set_ctime(inode,
        btrfs_timespec_sec(leaf, &inode_item->ctime),
        btrfs_timespec_nsec(leaf, &inode_item->ctime));

    /* Btrfs-specific */
    BTRFS_I(inode)->generation  = btrfs_inode_generation(leaf, inode_item);
    BTRFS_I(inode)->last_trans  = btrfs_inode_transid(leaf, inode_item);
    BTRFS_I(inode)->flags       = btrfs_inode_flags(leaf, inode_item);
    BTRFS_I(inode)->ro_flags    = btrfs_inode_ro_flags(leaf, inode_item);

    /* Special files */
    rdev = btrfs_inode_rdev(leaf, inode_item);
    if (S_ISDIR(inode->i_mode))
        inode->i_op = &btrfs_dir_inode_operations;
    else if (S_ISLNK(inode->i_mode))
        inode->i_op = &btrfs_symlink_inode_operations;
    else
        inode->i_op = &btrfs_file_inode_operations;

    return 0;
failed:
    return ret;
}
```

---

## Chapter 26: Rust Userspace — btrfs-progs Concepts

### 26.1 Implementing a Btrfs Key in Rust

```rust
//! BTRFS KEY TYPE IN RUST
//! Demonstrates the key comparison logic and tree traversal concepts.

use std::cmp::Ordering;

/// A Btrfs on-disk key (17 bytes total)
/// This is the fundamental lookup/sort unit in all Btrfs B-trees.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(C, packed)]
pub struct BtrfsKey {
    /// Object ID: inode number, tree ID, etc.
    pub objectid: u64,
    /// Type: what kind of item this is (INODE_ITEM, EXTENT_DATA, etc.)
    pub key_type: u8,
    /// Offset: meaning depends on type (file offset, hash, etc.)
    pub offset: u64,
}

/// Btrfs item types (the `type` byte of a key)
#[derive(Debug, Clone, Copy, PartialEq, Eq, repr_u8)]
#[repr(u8)]
pub enum BtrfsKeyType {
    InodeItem    = 0x01,  // Inode metadata
    InodeRef     = 0x0C,  // Filename in parent directory
    XattrItem    = 0x18,  // Extended attributes
    DirItem      = 0x30,  // Directory entry (name hash as offset)
    DirIndex     = 0x36,  // Directory index (sequence as offset)
    ExtentData   = 0x60,  // File extent (file offset as key offset)
    ExtentCsum   = 0x80,  // Data checksum
    RootItem     = 0x84,  // Subvolume/snapshot root descriptor
    BlockGroup   = 0x90,  // Block group metadata
    ChunkItem    = 0xE4,  // Chunk → physical stripe mapping
}

impl PartialOrd for BtrfsKey {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for BtrfsKey {
    /// Keys are compared: objectid first, then type, then offset.
    /// This defines the total ordering of ALL items in a B-tree.
    fn cmp(&self, other: &Self) -> Ordering {
        // Safety: packed struct fields read via copy
        let self_objectid = self.objectid;
        let other_objectid = other.objectid;
        let self_type = self.key_type;
        let other_type = other.key_type;
        let self_offset = self.offset;
        let other_offset = other.offset;

        self_objectid.cmp(&other_objectid)
            .then(self_type.cmp(&other_type))
            .then(self_offset.cmp(&other_offset))
    }
}

impl BtrfsKey {
    pub fn new(objectid: u64, key_type: u8, offset: u64) -> Self {
        BtrfsKey { objectid, key_type, offset }
    }

    /// Create a key for looking up an inode
    pub fn inode_key(inode: u64) -> Self {
        BtrfsKey::new(inode, 0x01, 0)
    }

    /// Create a key for looking up a file extent at given offset
    pub fn extent_key(inode: u64, file_offset: u64) -> Self {
        BtrfsKey::new(inode, 0x60, file_offset)
    }
}
```

### 26.2 Implementing B-Tree Binary Search in Rust

```rust
//! BTRFS BINARY SEARCH IMPLEMENTATION IN RUST
//! Mirrors the kernel's btrfs_bin_search() logic.

/// Simulated B-tree leaf node containing sorted items
pub struct BtrfsLeaf {
    /// Array of (key, data) pairs, sorted by key
    pub items: Vec<(BtrfsKey, Vec<u8>)>,
}

impl BtrfsLeaf {
    /// Binary search for a key within this leaf.
    ///
    /// Returns:
    ///   Ok(slot)  → exact match at `slot`
    ///   Err(slot) → not found; `slot` is the insertion point
    ///               (index of first key GREATER than search key)
    ///
    /// This exactly mirrors btrfs_bin_search() semantics.
    pub fn search(&self, target: &BtrfsKey) -> Result<usize, usize> {
        // Rust's standard binary_search_by handles this perfectly:
        // Returns Ok(i) for exact match, Err(i) for not found.
        self.items.binary_search_by(|(key, _)| key.cmp(target))
    }

    /// Find the item at or just BEFORE the given key.
    /// This is what tree traversal uses for internal nodes:
    /// "go to the child whose key range contains our target."
    pub fn find_slot(&self, target: &BtrfsKey) -> usize {
        match self.search(target) {
            Ok(slot) => slot,
            Err(slot) => {
                // Not found. slot is the first key > target.
                // We want the last key <= target.
                if slot == 0 { 0 } else { slot - 1 }
            }
        }
    }
}

/// In-memory representation of a B-tree for simulation
pub struct BtrfsTree {
    /// All leaf items (sorted). Real implementation uses
    /// a multi-level tree; this is a flat approximation for clarity.
    pub leaves: Vec<BtrfsLeaf>,
}

impl BtrfsTree {
    /// Search the tree for a key.
    /// Returns Some((leaf_idx, slot)) if found.
    pub fn search(&self, key: &BtrfsKey) -> Option<(usize, usize)> {
        // In a real B-tree, we'd traverse internal nodes.
        // Here we simulate by searching each leaf.
        for (leaf_idx, leaf) in self.leaves.iter().enumerate() {
            match leaf.search(key) {
                Ok(slot) => return Some((leaf_idx, slot)),
                Err(_)   => continue,
            }
        }
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_key_ordering() {
        // Keys sort by: objectid, then type, then offset
        let k1 = BtrfsKey::new(256, 0x01, 0);   // inode 256, INODE_ITEM
        let k2 = BtrfsKey::new(256, 0x60, 0);   // inode 256, EXTENT_DATA, offset 0
        let k3 = BtrfsKey::new(256, 0x60, 4096); // inode 256, EXTENT_DATA, offset 4096
        let k4 = BtrfsKey::new(257, 0x01, 0);   // inode 257, INODE_ITEM

        assert!(k1 < k2);   // same objectid, type 0x01 < 0x60
        assert!(k2 < k3);   // same objectid+type, offset 0 < 4096
        assert!(k3 < k4);   // objectid 256 < 257

        println!("Key ordering verified: k1 < k2 < k3 < k4");
    }

    #[test]
    fn test_leaf_binary_search() {
        let leaf = BtrfsLeaf {
            items: vec![
                (BtrfsKey::new(256, 0x01, 0), vec![1, 2, 3]),  // slot 0
                (BtrfsKey::new(256, 0x60, 0), vec![4, 5, 6]),  // slot 1
                (BtrfsKey::new(256, 0x60, 4096), vec![7]),      // slot 2
                (BtrfsKey::new(257, 0x01, 0), vec![8, 9]),      // slot 3
            ],
        };

        // Exact match
        let target = BtrfsKey::new(256, 0x60, 0);
        assert_eq!(leaf.search(&target), Ok(1));

        // Not found — should return insertion point
        let target = BtrfsKey::new(256, 0x60, 2048);
        assert_eq!(leaf.search(&target), Err(2));
        // Err(2) means: not found, would insert at slot 2

        // find_slot: for traversal (returns slot of last key <= target)
        assert_eq!(leaf.find_slot(&target), 1); // slot 1 has key 0x60/0, which is < 0x60/2048
    }
}
```

### 26.3 Simulating CoW B-Tree in Rust

```rust
//! COPY-ON-WRITE B-TREE SIMULATION IN RUST
//! Demonstrates the shadow paging concept.

use std::collections::HashMap;
use std::sync::Arc;

type BlockPtr = u64;  // Physical block address
type Generation = u64;

/// Simulated block storage (replaces actual disk)
pub struct BlockStore {
    blocks: HashMap<BlockPtr, Vec<u8>>,
    next_free: BlockPtr,
}

impl BlockStore {
    pub fn new() -> Self {
        BlockStore {
            blocks: HashMap::new(),
            next_free: 0x1000,  // Start allocations at 4KB
        }
    }

    /// Allocate a new free block, return its address
    pub fn alloc_block(&mut self) -> BlockPtr {
        let addr = self.next_free;
        self.next_free += 4096;  // 4KB blocks
        addr
    }

    pub fn write(&mut self, addr: BlockPtr, data: Vec<u8>) {
        self.blocks.insert(addr, data);
    }

    pub fn read(&self, addr: BlockPtr) -> Option<&Vec<u8>> {
        self.blocks.get(&addr)
    }

    pub fn free(&mut self, addr: BlockPtr) {
        self.blocks.remove(&addr);
    }
}

/// A node in our CoW tree
#[derive(Debug, Clone)]
pub struct TreeNode {
    pub generation: Generation,
    pub keys: Vec<u64>,
    pub children: Vec<BlockPtr>,  // For internal nodes
    pub values: Vec<Vec<u8>>,     // For leaf nodes
    pub is_leaf: bool,
}

/// CoW B-tree with full shadow paging semantics
pub struct CoWTree {
    pub store: BlockStore,
    pub root: BlockPtr,
    pub generation: Generation,
    /// Old blocks to free AFTER the transaction commits
    pub pending_free: Vec<BlockPtr>,
}

impl CoWTree {
    pub fn new() -> Self {
        let mut store = BlockStore::new();
        let root_addr = store.alloc_block();
        let root_node = TreeNode {
            generation: 0,
            keys: vec![],
            children: vec![],
            values: vec![],
            is_leaf: true,
        };
        // Serialize and write root
        let data = serialize_node(&root_node);
        store.write(root_addr, data);

        CoWTree {
            store,
            root: root_addr,
            generation: 0,
            pending_free: vec![],
        }
    }

    /// Insert a key-value pair using CoW semantics.
    /// Returns the NEW root block address (old root is now orphaned).
    pub fn insert(&mut self, key: u64, value: Vec<u8>) -> BlockPtr {
        // Increment generation (new transaction)
        self.generation += 1;
        let gen = self.generation;

        println!(
            "[Gen {}] INSERT key={} — starting CoW chain from root@{:#x}",
            gen, key, self.root
        );

        // CoW the path from root to leaf
        let old_root = self.root;
        let new_root = self.cow_insert(old_root, key, value, gen);

        // Queue old root for freeing
        self.pending_free.push(old_root);

        // Update root pointer (like superblock update!)
        self.root = new_root;
        println!(
            "[Gen {}] COMMIT: new root@{:#x}, old root@{:#x} queued for free",
            gen, new_root, old_root
        );

        // "Commit": free old blocks
        self.commit_free();

        new_root
    }

    /// Recursively CoW-insert: returns new block address
    fn cow_insert(&mut self, block: BlockPtr, key: u64, value: Vec<u8>, gen: Generation) -> BlockPtr {
        // Read the original block
        let data = self.store.read(block)
            .expect("Block not found")
            .clone();
        let mut node = deserialize_node(&data);

        if node.is_leaf {
            // Insert into leaf
            let pos = node.keys.partition_point(|&k| k < key);
            node.keys.insert(pos, key);
            node.values.insert(pos, value);
            node.generation = gen;

            // Write to NEW block (CoW!)
            let new_addr = self.store.alloc_block();
            self.store.write(new_addr, serialize_node(&node));
            println!(
                "  [CoW] Leaf@{:#x} → new leaf@{:#x} (inserted key={})",
                block, new_addr, key
            );
            new_addr
        } else {
            // Find the right child
            let child_idx = node.keys.partition_point(|&k| k <= key);
            let old_child = node.children[child_idx];

            // Recurse: CoW the child
            let new_child = self.cow_insert(old_child, key, value, gen);
            self.pending_free.push(old_child);

            // Update this node to point to new child (CoW this node too!)
            node.children[child_idx] = new_child;
            node.generation = gen;

            let new_addr = self.store.alloc_block();
            self.store.write(new_addr, serialize_node(&node));
            println!(
                "  [CoW] Internal@{:#x} → new internal@{:#x} (child ptr updated)",
                block, new_addr
            );
            new_addr
        }
    }

    /// After commit: actually free old blocks
    fn commit_free(&mut self) {
        for addr in self.pending_free.drain(..) {
            self.store.free(addr);
            println!("  [FREE] Block@{:#x} freed (old version)", addr);
        }
    }

    /// Take a snapshot: just copy the root pointer!
    /// Returns the snapshot's root block address.
    pub fn snapshot(&self) -> BlockPtr {
        println!(
            "[SNAPSHOT] Created at root@{:#x} gen={} (O(1) — just a pointer copy!)",
            self.root, self.generation
        );
        self.root  // The snapshot IS the current root pointer
        // In real Btrfs: would increment reference count
        // and create ROOT_ITEM in root tree
    }
}

// Simplified serialization (real Btrfs uses on-disk struct layout)
fn serialize_node(node: &TreeNode) -> Vec<u8> {
    format!("{:?}", node).into_bytes()
}

fn deserialize_node(data: &[u8]) -> TreeNode {
    // Simplified: real Btrfs reads struct fields at fixed offsets
    let _ = data;
    TreeNode {
        generation: 0,
        keys: vec![],
        children: vec![],
        values: vec![],
        is_leaf: true,
    }
}

fn main() {
    let mut tree = CoWTree::new();

    // Insert some data
    let snap1 = tree.snapshot();
    tree.insert(100, b"hello".to_vec());
    tree.insert(200, b"world".to_vec());
    let snap2 = tree.snapshot();
    tree.insert(150, b"btrfs".to_vec());

    println!("\nSnapshot 1 (before inserts): root@{:#x}", snap1);
    println!("Snapshot 2 (after 100,200):  root@{:#x}", snap2);
    println!("Current   (after 150 added): root@{:#x}", tree.root);
    println!("\nAll three coexist independently via CoW + reference counting!");
}
```

### 26.4 Implementing Checksums in Rust

```rust
//! BTRFS CHECKSUM IMPLEMENTATION IN RUST
//! Demonstrates how Btrfs verifies data integrity.

use std::hash::Hasher;

/// CRC32C hardware-accelerated checksum
/// (The default Btrfs checksum algorithm)
pub struct Crc32cHasher {
    state: u32,
}

impl Crc32cHasher {
    pub fn new() -> Self {
        Crc32cHasher { state: 0xFFFFFFFF }
    }

    pub fn update(&mut self, data: &[u8]) {
        // In production: use the `crc32c` crate which uses
        // SSE4.2 hardware instructions on x86 (very fast!)
        // Here we show the conceptual implementation.
        for &byte in data {
            self.state = crc32c_table_lookup(self.state, byte);
        }
    }

    pub fn finalize(self) -> u32 {
        self.state ^ 0xFFFFFFFF
    }
}

/// Polynomial: 0x1EDC6F41 (Castagnoli)
fn crc32c_table_lookup(crc: u32, byte: u8) -> u32 {
    // In production this is a 256-entry lookup table.
    // The magic number is the Castagnoli polynomial.
    const POLY: u32 = 0x82F63B78;  // Reflected polynomial
    let mut c = crc ^ (byte as u32);
    for _ in 0..8 {
        if c & 1 != 0 {
            c = POLY ^ (c >> 1);
        } else {
            c >>= 1;
        }
    }
    c
}

/// Represents a data block with its checksum (as stored on disk)
pub struct ChecksummedBlock {
    pub data: Vec<u8>,
    pub stored_csum: u32,
}

impl ChecksummedBlock {
    /// Create a new block, computing its checksum
    pub fn new(data: Vec<u8>) -> Self {
        let csum = Self::compute_checksum(&data);
        ChecksummedBlock { data, stored_csum: csum }
    }

    pub fn compute_checksum(data: &[u8]) -> u32 {
        let mut hasher = Crc32cHasher::new();
        hasher.update(data);
        hasher.finalize()
    }

    /// Verify the block's integrity (called on every read)
    ///
    /// This is what btrfs does on EVERY block read:
    /// 1. Read block from disk
    /// 2. Compute checksum
    /// 3. Compare with stored value
    /// 4. Mismatch = corruption detected!
    pub fn verify(&self) -> Result<(), CorruptionError> {
        let actual = Self::compute_checksum(&self.data);
        if actual == self.stored_csum {
            Ok(())
        } else {
            Err(CorruptionError {
                expected: self.stored_csum,
                actual,
                block_offset: 0,  // Would be actual disk offset
            })
        }
    }

    /// Simulate a bit flip (cosmic ray / hardware error)
    pub fn corrupt(&mut self, offset: usize) {
        self.data[offset] ^= 0x01;  // Flip the lowest bit
        println!("  [CORRUPTION INJECTED] Bit flipped at offset {}", offset);
    }
}

#[derive(Debug)]
pub struct CorruptionError {
    pub expected: u32,
    pub actual: u32,
    pub block_offset: u64,
}

impl std::fmt::Display for CorruptionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Checksum mismatch at block {:#x}: expected {:#010x}, got {:#010x}",
            self.block_offset, self.expected, self.actual
        )
    }
}

/// Simulate the Btrfs checksum tree
pub struct ChecksumTree {
    /// Maps logical_bytenr → [csum per sector]
    /// In Btrfs: stored as EXTENT_CSUM items in the csum tree
    checksums: std::collections::HashMap<u64, Vec<u32>>,
    sector_size: usize,
}

impl ChecksumTree {
    pub fn new() -> Self {
        ChecksumTree {
            checksums: std::collections::HashMap::new(),
            sector_size: 4096,
        }
    }

    /// Store checksums for a data extent (called during write)
    pub fn store_extent_checksums(&mut self, logical_bytenr: u64, data: &[u8]) {
        let sector_count = (data.len() + self.sector_size - 1) / self.sector_size;
        let mut csums = Vec::with_capacity(sector_count);

        for i in 0..sector_count {
            let start = i * self.sector_size;
            let end = ((i + 1) * self.sector_size).min(data.len());
            let sector_data = &data[start..end];
            let csum = ChecksummedBlock::compute_checksum(sector_data);
            csums.push(csum);
        }

        println!(
            "  [CSUM TREE] Stored {} checksums for extent@{:#x}",
            csums.len(), logical_bytenr
        );
        self.checksums.insert(logical_bytenr, csums);
    }

    /// Verify a data extent against stored checksums
    pub fn verify_extent(&self, logical_bytenr: u64, data: &[u8]) -> Result<(), String> {
        let stored = self.checksums.get(&logical_bytenr)
            .ok_or("No checksum found for this extent")?;

        let sector_count = (data.len() + self.sector_size - 1) / self.sector_size;

        for i in 0..sector_count {
            let start = i * self.sector_size;
            let end = ((i + 1) * self.sector_size).min(data.len());
            let sector_data = &data[start..end];
            let actual = ChecksummedBlock::compute_checksum(sector_data);

            if actual != stored[i] {
                return Err(format!(
                    "Corruption at logical {:#x}+{}: expected={:#010x} actual={:#010x}",
                    logical_bytenr, i * self.sector_size, stored[i], actual
                ));
            }
        }

        println!(
            "  [CSUM VERIFY] All {} sectors OK for extent@{:#x}",
            sector_count, logical_bytenr
        );
        Ok(())
    }
}

fn main() {
    println!("=== Btrfs Checksum Integrity Demo ===\n");

    // 1. Write data (as Btrfs does)
    let mut csum_tree = ChecksumTree::new();
    let original_data = b"Hello, Btrfs! This is important data.".to_vec();
    let logical_addr = 0x40000000u64;

    println!("[WRITE] Writing {} bytes to logical addr {:#x}", original_data.len(), logical_addr);
    csum_tree.store_extent_checksums(logical_addr, &original_data);

    // 2. Normal read — should pass
    println!("\n[READ] Normal read (no corruption):");
    match csum_tree.verify_extent(logical_addr, &original_data) {
        Ok(()) => println!("  ✓ Data integrity verified!"),
        Err(e) => println!("  ✗ CORRUPTION: {}", e),
    }

    // 3. Simulate corruption
    println!("\n[HARDWARE ERROR] Simulating bit flip...");
    let mut corrupted_data = original_data.clone();
    corrupted_data[5] ^= 0xFF;  // Corrupt byte 5

    // 4. Corrupted read — should FAIL with informative error
    println!("\n[READ] Read after corruption:");
    match csum_tree.verify_extent(logical_addr, &corrupted_data) {
        Ok(()) => println!("  ✓ (This should not happen!)"),
        Err(e) => println!("  ✗ DETECTED: {}", e),
    }

    println!("\n=== Silent corruption would have gone undetected on ext4! ===");
    println!("=== Btrfs catches it immediately and can repair from mirror. ===");
}
```

---

# PART VII — MENTAL MODELS & MASTERY

---

## Chapter 27: Expert Mental Models for Btrfs

### 27.1 The "Living Database" Mental Model

```
MENTAL MODEL: BTRFS IS A DATABASE
═══════════════════════════════════

  Think of Btrfs NOT as a "filesystem" but as:
  "An ACID-compliant, append-only, B-tree database
   that stores filesystem metadata as records."

  Parallel:
  ─────────────────────────────────────────────────────
  Database concept    ←→    Btrfs concept
  ─────────────────────────────────────────────────────
  Table               ←→    Tree (fs tree, extent tree...)
  Row                 ←→    Item (in a leaf node)
  Primary key         ←→    Btrfs key (objectid, type, offset)
  Index               ←→    B-tree (sorted key space)
  Transaction         ←→    Btrfs transaction (ACID)
  MVCC (versioning)   ←→    CoW (multiple tree versions)
  Table snapshot      ←→    Subvolume snapshot
  Replication         ←→    Send/Receive
  Partitioning        ←→    Block groups

  WHY THIS MODEL HELPS:
  ─────────────────────
  When you ask "how does Btrfs handle X?", ask:
  "How would a database handle X?"
  Almost always gives you the right intuition.
```

### 27.2 The "Immutable History" Mental Model

```
MENTAL MODEL: COW = IMMUTABLE HISTORY
══════════════════════════════════════

  Think of Btrfs transactions like Git commits:

  Git:                       Btrfs:
  ─────────────────────────  ─────────────────────────
  commit object              transaction (generation N)
  tree object                B-tree root node
  blob object                data extent / leaf node
  ref (branch/tag)           subvolume / snapshot
  git checkout               mount -o subvol=@snap

  In Git: you NEVER modify history. You create new commits.
  In Btrfs: you NEVER modify old blocks. You create new copies.

  This is why Btrfs is so reliable:
  "The past is immutable. Only the future is written."
```

### 27.3 The "Reference Counting Universe" Mental Model

```
MENTAL MODEL: EVERYTHING IS REFERENCE COUNTED
═══════════════════════════════════════════════

  Every byte on a Btrfs disk is "owned" by one or more
  things. It's freed ONLY when ALL owners release it.

  Owners:
  ─────────────────────────────────────────
  An extent can be owned by:
  ├── A file (EXTENT_DATA_REF)
  ├── A snapshot copy of a file (EXTENT_DATA_REF)
  ├── A B-tree node (TREE_BLOCK_REF)
  └── A snapshot copy of a B-tree node (SHARED_BLOCK_REF)

  Reference counting rules:
  ─────────────────────────
  New file:      extent refs = 1
  Snapshot:      extent refs = 2 (original + snapshot)
  Delete original: refs = 1 (snapshot still alive)
  Delete snapshot: refs = 0 → FREED

  This is Rust's ownership model applied to a filesystem!
  Arc<T> in Rust ≈ reference-counted extent in Btrfs
```

### 27.4 Common Pitfalls & Anti-Patterns

```
BTRFS ANTI-PATTERNS TO AVOID
══════════════════════════════

  1. RUNNING BTRFS ON SWAP (NEVER DO THIS)
  ──────────────────────────────────────────
  Swap bypasses the VFS/page cache.
  CoW is incompatible with swap file semantics.
  Use a separate partition for swap, or:
  Use a swapfile only on a nodatacow subvolume.

  2. FORGETTING METADATA SPACE EXHAUSTION
  ────────────────────────────────────────
  df -h shows 20% free → but ENOSPC errors appear!
  WHY: Metadata and data are in separate block groups.
       Data space fine, but metadata full → ENOSPC!
  FIX: btrfs balance start -musage=10 /mnt
       (balance partially-used metadata block groups)

  3. USING RAID5/6 FOR PRODUCTION
  ────────────────────────────────
  Write hole bug = data loss possible on power failure.
  Use RAID1 or RAID10 instead.

  4. IGNORING DEVICE STATS
  ──────────────────────────
  btrfs device stats /dev/sda
  If corruption_errs > 0: disk is failing! Replace NOW.
  Many admins ignore this until catastrophic failure.

  5. NOT SCHEDULING SCRUBS
  ─────────────────────────
  Bit rot (data corruption over time) is real.
  Without scrubbing, corruption goes undetected.
  Schedule monthly: systemctl enable btrfs-scrub@.timer

  6. DELETING SNAPSHOTS IN WRONG ORDER
  ──────────────────────────────────────
  With incremental send/receive:
  Parent snapshot must exist before child snapshot.
  Delete @snap-v1 before @snap-v2 → cannot send @snap-v2!
  Always delete NEWEST snapshots first.

  7. MIXING NODATACOW WITH COMPRESSION
  ──────────────────────────────────────
  nodatacow disables CoW → disables compression!
  If you need both: use two subvolumes.
  subvol @data-cow    → compression enabled (default)
  subvol @data-nocow  → nodatacow (databases)

  8. RUNNING BTRFS CHECK ON MOUNTED FILESYSTEM
  ──────────────────────────────────────────────
  Unlike fsck.ext4, btrfs check can CORRUPT a live FS!
  Always unmount first, or use read-only mode.
  btrfs check --readonly /dev/sda  (safe)
  btrfs check --repair /dev/sda    (unmount first!)
```

---

## Chapter 28: Performance Tuning Guide

### 28.1 SSD Optimal Configuration

```
SSD OPTIMAL MOUNT OPTIONS
══════════════════════════

  /etc/fstab:
  UUID=xxxx  /  btrfs  \
    defaults,\
    noatime,\          ← Skip access time updates (big win)
    compress=zstd:3,\  ← Good compression, fast decompression
    space_cache=v2,\   ← Faster free space lookup
    discard=async,\    ← Async TRIM (don't block writes)
    commit=120         ← Less frequent commits (120s vs 30s)
    0 0

  WHY EACH OPTION:
  ─────────────────
  noatime:      Every file read would write atime → extra CoW!
                Disabling saves enormous write amplification.

  zstd:3:       Reduces data written to SSD → less wear
                Decompression is faster than SSD reads for
                many workloads (CPU faster than storage).

  discard=async: SSDs need TRIM for performance over time.
                Async = queue TRIMs, apply in batch.
                Sync = TRIM every delete → slow.

  commit=120:   Longer commit interval → batch more writes.
                Risk: up to 120s of data on crash (vs 30s).
                Acceptable for desktop, not for servers.
```

### 28.2 HDD Optimal Configuration

```
HDD OPTIMAL CONFIGURATION
══════════════════════════

  For spinning disks (HDDs), seek time is the enemy.
  Key optimizations:

  1. AUTODEFRAG:
  mount -o autodefrag /mnt
  → Background thread detects fragmented files
  → Rewrites them as contiguous extents
  → Especially important for small random writes
  → Use for databases, VMs on HDD

  2. DISABLE COMPRESSION (or use lzo):
  HDD is slow → CPU time for compression is "free"
  zstd:3 is fine; lzo slightly better for latency.

  3. LARGE NODESIZE:
  mkfs.btrfs --nodesize 65536 /dev/sda  (64KB nodes)
  → Fewer nodes → fewer seeks
  → Each node holds more keys → shallower tree

  4. RAID0 FOR NON-CRITICAL DATA:
  btrfs balance start -dconvert=raid0 /mnt
  → Striping across multiple HDDs → 2× throughput

  5. READAHEAD:
  echo 8192 > /sys/block/sda/queue/read_ahead_kb
  → Aggressive readahead for sequential workloads
```

### 28.3 Kernel Parameters & Sysctls

```
BTRFS-RELEVANT KERNEL PARAMETERS
══════════════════════════════════

  vm.dirty_ratio = 10
  ────────────────────
  Max % of RAM that can be dirty before sync starts.
  Lower = less data at risk on crash.
  Higher = better write performance (more batching).

  vm.dirty_background_ratio = 5
  ──────────────────────────────
  % of RAM when background writeback starts.
  Lower = earlier writebacks = more disk I/O.
  Higher = more batching = fewer, larger writes.

  vm.dirty_expire_centisecs = 3000
  ─────────────────────────────────
  How long a page can sit dirty before forced writeback.
  3000 = 30 seconds (matches Btrfs commit interval).

  vm.dirty_writeback_centisecs = 500
  ────────────────────────────────────
  How often writeback daemon runs (500 = 5 seconds).

  BTRFS-SPECIFIC SYSFS:
  ──────────────────────
  /sys/fs/btrfs/<uuid>/
  ├── allocation/
  │   ├── data/
  │   │   ├── bytes_used
  │   │   ├── bytes_pinned
  │   │   └── disk_used
  │   └── metadata/
  │       ├── bytes_used
  │       └── bytes_reserved
  ├── devices/
  │   └── <devid>/
  │       ├── size
  │       └── fsid
  └── features/
      ├── skinny_metadata
      ├── no_holes
      └── free_space_tree
```

---

## Chapter 29: Monitoring & Debugging

### 29.1 Essential Monitoring Commands

```
BTRFS MONITORING REFERENCE
═══════════════════════════

  SPACE USAGE (comprehensive):
  ─────────────────────────────
  btrfs filesystem usage /mnt
  Output:
    Overall:
        Device size:                 500.00GiB
        Device allocated:            320.00GiB
        Device unallocated:          180.00GiB   ← truly free
        Device missing:                  0.00B
        Used:                        298.52GiB   ← actual data
        Free (estimated):            195.22GiB   ← usable
        Free (statfs, df):           195.22GiB
        Data ratio:                        1.00
        Metadata ratio:                    2.00  ← DUP metadata!
        Global reserve:              512.00MiB

    Data,single: Size:250GiB, Used:248GiB
    Metadata,DUP: Size:64GiB, Used:25GiB
    System,DUP:   Size:32MiB, Used:16KiB

  INODE STATS:
  ─────────────
  btrfs filesystem show /mnt
  btrfs subvolume list /mnt
  btrfs subvolume show /mnt/@home

  COMPRESSION STATS:
  ───────────────────
  compsize -x /mnt/   # install: compsize package
  Output:
    Processed 12345 files, 234 dirs
    Compression ratio: 2.87  (data: 45GB, compressed: 15GB)
    COMPRESS  Uncompressed  Compressed  Ratio
    zstd      43.21GiB      15.06GiB    2.87x
    none      1.23GiB       1.23GiB     1.00x

  EXTENT FRAGMENTATION:
  ──────────────────────
  btrfs filesystem defragment -v -r -czstd /mnt/
  filefrag -v /path/to/file    # Check fragmentation
  btrfs inspect-internal dump-tree /dev/sda   # Full tree dump (expert)

  TRANSACTION INFO:
  ──────────────────
  btrfs-debug-tree /dev/sda   # Unmounted only!
  btrfs inspect-internal dump-super /dev/sda

  KERNEL DEBUG (dmesg):
  ──────────────────────
  dmesg | grep -i btrfs
  # Look for:
  # BTRFS: error → something went wrong
  # BTRFS: csum failed → checksum error (corruption!)
  # BTRFS: bad magic on a free sequence → bad block group
```

### 29.2 Debugging ENOSPC

```
DEBUGGING ENOSPC (NO SPACE LEFT)
══════════════════════════════════

  SYMPTOM: df shows free space, but writes fail with ENOSPC.

  DIAGNOSIS FLOWCHART:
  ─────────────────────
  ┌────────────────────────────────────────────────────┐
  │  btrfs filesystem usage /mnt                       │
  └────────────────────────────┬───────────────────────┘
                               │
              ┌────────────────▼───────────────────┐
              │  Check Metadata usage               │
              │  Metadata,DUP: Used = X GiB?        │
              └──────────┬──────────────────────────┘
                         │
        ┌────────────────▼──────────────────────────┐
        │  Metadata nearly full (>85%)?             │
        │  YES → balance metadata block groups:     │
        │    btrfs balance start -musage=50 /mnt    │
        │                                           │
        │  NO → check data block groups:            │
        │    Data nearly full (>95%)?               │
        │    YES → delete files or add device       │
        │    NO  → many tiny block groups?          │
        │          btrfs balance start -dusage=20   │
        └───────────────────────────────────────────┘

  EMERGENCY RECOVERY (fs completely full):
  ─────────────────────────────────────────
  # Reserve space for root operations
  # Btrfs keeps a "global reserve" for metadata emergencies.
  # If that's also gone:

  1. Delete some files (even small ones free metadata space)
  2. btrfs balance start -musage=1 /mnt  (merge tiny chunks)
  3. Mount with -o clear_cache,space_cache=v2  (rebuild cache)
  4. As last resort: mount with -o skip_balance and delete data
```

---

## Chapter 30: Deliberate Practice Roadmap

### 30.1 The Mastery Path

```
BTRFS MASTERY PROGRESSION
══════════════════════════

  Level 0: Foundation (Week 1-2)
  ──────────────────────────────
  □ Set up a test VM (qemu/kvm) with 4 virtual disks
  □ mkfs.btrfs with different profiles
  □ Create/delete subvolumes and snapshots
  □ Measure snapshot creation time vs data size
  □ Test: corrupt a block with dd, observe detection

  Level 1: Operations (Week 3-4)
  ──────────────────────────────
  □ Set up RAID1 and kill one disk → verify survival
  □ Practice send/receive for incremental backup
  □ Measure compression ratios (zstd vs lzo vs zlib)
  □ Trigger ENOSPC and debug/recover
  □ Run scrub with injected corruption

  Level 2: Internals (Week 5-8)
  ──────────────────────────────
  □ Read btrfs-progs source code (C)
  □ Use btrfs inspect-internal to dump trees
  □ Write a B-tree key parser (Python or Rust)
  □ Trace btrfs_search_slot() with ftrace
  □ Understand the on-disk hex dump of a superblock

  Level 3: Expert (Month 3+)
  ──────────────────────────
  □ Read fs/btrfs/*.c in the Linux kernel
  □ Write a Rust tool to parse btrfs on-disk format
  □ Contribute a bug fix or documentation to btrfs-progs
  □ Understand qgroups accounting edge cases
  □ Design a production backup system using Btrfs primitives

  COGNITIVE PRINCIPLE (Deliberate Practice):
  ─────────────────────────────────────────
  At each level, practice at the EDGE of your ability.
  If it's easy, go deeper. If it's impossible, step back.
  The discomfort zone is exactly where learning happens.
  (Ericsson, 1993 — "The Role of Deliberate Practice")
```

### 30.2 Mental Frameworks for Understanding

```
CHUNKING FRAMEWORK FOR BTRFS
══════════════════════════════

  Novice sees: 47 btrfs commands, 30 mount options, 8 trees.
  Expert sees: 3 core concepts + their consequences.

  CHUNK 1: CoW + B-tree = everything else follows
  ────────────────────────────────────────────────
  Once you deeply understand CoW + B-trees:
  - Snapshots: obvious (just share tree roots)
  - Integrity: obvious (hash new blocks before linking)
  - Transactions: obvious (update root atomically)
  - Space efficiency: obvious (shared extents = reference count)

  CHUNK 2: Logical vs Physical address space
  ──────────────────────────────────────────
  Once you understand logical/physical split:
  - Multi-device: obvious (remap logical to multiple physical)
  - RAID: obvious (logical block → multiple physical stripes)
  - Balance: obvious (move physical chunks, remap logical)
  - Device replace: obvious (copy physical, remap logical)

  CHUNK 3: Everything is a tree item with a key
  ──────────────────────────────────────────────
  Once you understand the key space:
  - Finding any data: search for key
  - Range queries: binary search then walk right
  - All trees use same code: elegant and consistent

  META-LEARNING INSIGHT:
  ──────────────────────
  Understanding the "why" (design philosophy) is more
  powerful than memorizing the "what" (commands/options).
  The "what" follows from the "why" naturally.
  This is second-order learning: learning how things
  were designed, not just what they do.
```

---

## APPENDIX A: Key Kernel Files Reference

```
BTRFS KERNEL SOURCE MAP
════════════════════════

  fs/btrfs/
  ├── ctree.h          ← ALL key data structures (read first!)
  ├── ctree.c          ← B-tree operations (search, insert, delete)
  ├── disk-io.h/c      ← Superblock, tree root reading, commit
  ├── extent-tree.c    ← Extent allocation/freeing
  ├── extent_io.c      ← Extent buffers, I/O
  ├── inode.c          ← Inode operations (create, read, write)
  ├── file.c           ← File read/write operations
  ├── transaction.c    ← Transaction begin/commit/abort
  ├── volumes.c        ← Multi-device, RAID, balance, replace
  ├── raid56.c         ← RAID5/6 parity logic
  ├── compression.c    ← zlib/lzo/zstd compress/decompress
  ├── send.c           ← Send stream generation
  ├── receive.c        ← Receive stream application (userspace)
  ├── tree-log.c       ← Log tree (fsync optimization)
  ├── qgroup.c         ← Quota group tracking
  ├── free-space-cache.c ← V1 free space cache
  ├── free-space-tree.c  ← V2 free space tree
  ├── scrub.c          ← Online integrity checking
  ├── ioctl.c          ← Btrfs-specific ioctls
  ├── props.c          ← Compression properties
  ├── ref-verify.c     ← Debug: reference count verification
  └── super.c          ← VFS superblock, mount, module init
```

## APPENDIX B: Btrfs Checksum Algorithm Codes

```
CHECKSUM TYPE CODES
════════════════════

  0x00  BTRFS_CSUM_TYPE_CRC32    crc32c (hardware, default)
  0x01  BTRFS_CSUM_TYPE_XXHASH   xxHash64 (fast software)
  0x02  BTRFS_CSUM_TYPE_SHA256   SHA-256 (cryptographic, 32B)
  0x03  BTRFS_CSUM_TYPE_BLAKE2   Blake2b (fast crypto, 32B)

  Size of checksum by type:
  CRC32:  4 bytes
  XXHASH: 8 bytes
  SHA256: 32 bytes
  BLAKE2: 32 bytes
```

## APPENDIX C: Incompatible Feature Flags

```
BTRFS INCOMPAT FEATURE FLAGS
══════════════════════════════

  Flag                      Hex       Meaning
  ──────────────────────────────────────────────────────
  MIXED_BACKREF             0x001     Backward-compat ext refs
  DEFAULT_SUBVOL            0x002     Default subvolume support
  MIXED_GROUPS              0x004     Mixed data+metadata groups
  COMPRESS_LZO              0x008     LZO compression used
  COMPRESS_ZSTD             0x010     ZSTD compression used
  BIG_METADATA              0x020     Nodesize > sectorsize
  EXTENDED_IREF             0x040     Extended inode refs (hard link limit removed)
  RAID56                    0x080     RAID5/6 support
  SKINNY_METADATA           0x100     Compact extent refs (RECOMMENDED)
  NO_HOLES                  0x200     Sparse file optimization
  METADATA_UUID             0x400     Separate metadata UUID
  FREE_SPACE_TREE           0x800     V2 free space cache
  RAID1C34                  0x1000    RAID1 with 3 or 4 copies
  ZONED                     0x2000    Zoned device support (SMR HDDs)
  EXTENT_TREE_V2            0x4000    New extent tree format
  RAID_STRIPE_TREE          0x8000    RAID stripe tree

  Check your filesystem:
  btrfs inspect-internal dump-super /dev/sda | grep incompat
```

---

*This guide covers Btrfs as of Linux kernel 6.x and btrfs-progs 6.x.*
*Last conceptual update: 2024.*

> **"Mastery is not about knowing everything. It is about building the right mental models so that everything else follows logically."**
>
> — Approach Btrfs like this: understand CoW and B-trees deeply, and the entire filesystem becomes transparent to you.

Now let me craft the comprehensive Btrfs guide. This is a massive document — I'll build it section by section.Here is your complete Btrfs guide — **3,961 lines, ~155KB** of deep technical content across 30 chapters and 7 parts.

---

**What's covered, and why it's structured this way:**

**Part I — Foundations** builds upward from first principles. You cannot truly understand Btrfs without owning the B-tree and CoW mental models first. Every feature in Btrfs is a *consequence* of these two ideas. The guide teaches BST → B-tree → B+Tree → Btrfs B-tree, with the exact on-disk node anatomy.

**Part II — On-Disk Format** goes into the superblock byte-by-byte, the key system (the `(objectid, type, offset)` triple that governs everything), extent trees, block groups, and the chunk tree's logical→physical address translation. The bootstrap problem (how the kernel reads the chunk tree before it knows where anything is) is explained explicitly.

**Part III — Features** covers every major Btrfs capability in depth: subvolumes, snapshots (with CoW chain diagrams), all RAID profiles including the RAID5/6 write-hole warning, all three compression algorithms with real numbers, the checksum model, dedup (inline vs out-of-band with FIDEDUPRANGE ioctl), the send/receive binary protocol, qgroups, and free space evolution (v1 vs v2).

**Part IV — Kernel Integration** digs into the VFS layer (the `file_operations`, `inode_operations`, `address_space_operations` structs Btrfs implements), the page cache writeback model, the transaction commit protocol (9-step sequence), and memory management via extent buffers and slab caches.

**Part V — Administration** is production-grade reference: every `mkfs.btrfs` option, every mount option with rationale, device operations, scrub/check/rescue procedures.

**Part VI — Code** provides actual kernel C (`btrfs_search_slot`, `btrfs_cow_block`, `btrfs_read_locked_inode`) and full Rust implementations of CoW B-tree simulation, the checksum tree, and key ordering — all runnable, annotated code.

**Part VII — Mental Models** closes with the three *chunking frameworks* an expert uses (CoW+B-tree → everything; logical/physical split → RAID/balance; key space → all lookups), common production pitfalls, and a deliberate practice roadmap grounded in Ericsson's learning science.