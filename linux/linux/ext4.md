# EXT4 Filesystem: A Complete, Comprehensive Guide
## From Bits on Disk to Linux Kernel Internals

---

> *"A filesystem is not just storage — it is the contract between your software and the physical world."*

---

## Table of Contents

1. [Foundations: What is a Filesystem?](#1-foundations)
2. [Storage Hardware Fundamentals](#2-storage-hardware)
3. [The ext Family: History & Evolution](#3-ext-family)
4. [Disk Layout: The Big Picture](#4-disk-layout)
5. [The Superblock: The Master Record](#5-superblock)
6. [Block Groups: Divide and Conquer](#6-block-groups)
7. [Inodes: The DNA of Every File](#7-inodes)
8. [Extent Trees: How Data Blocks Are Found](#8-extent-trees)
9. [Directories: Files That Contain Files](#9-directories)
10. [The Journal (JBD2): Crash Safety](#10-journaling)
11. [Linux VFS Layer: The Abstraction](#11-vfs)
12. [Page Cache & Buffer Cache](#12-page-cache)
13. [Writeback & Dirty Pages](#13-writeback)
14. [Delayed Allocation (delalloc)](#14-delalloc)
15. [Disk I/O Schedulers & Block Layer](#15-block-layer)
16. [ext4 Kernel Data Structures (C deep dive)](#16-kernel-structures)
17. [Rust-level Filesystem Concepts](#17-rust-concepts)
18. [mount, mkfs, tune2fs — Tools Deep Dive](#18-tools)
19. [Performance Tuning](#19-performance)
20. [Forensics, Recovery & Debugging](#20-forensics)
21. [Security: Encryption & ACLs](#21-security)
22. [Comparison: ext4 vs xfs vs btrfs vs zfs](#22-comparison)

---

# 1. Foundations: What is a Filesystem?

## 1.1 The Core Problem

Imagine you have a hard disk — a physical device that stores raw bytes. From the hardware's perspective, the disk is just a flat, linear sequence of **blocks** (512-byte or 4096-byte chunks), numbered from 0 to N. There is no concept of "files", "directories", or "names" — just raw bytes at addresses.

A **filesystem** is software (mostly in the kernel) that imposes structure on this flat sequence of blocks, giving us:

```
Raw Disk (hardware view):
┌──────────────────────────────────────────────────────────────────┐
│ Block 0 │ Block 1 │ Block 2 │ ... │ Block N                      │
└──────────────────────────────────────────────────────────────────┘
     ↓  filesystem imposes structure
     ↓
Filesystem View (human/OS view):
/
├── home/
│   └── user/
│       ├── notes.txt   (4 KB)
│       └── video.mp4   (2 GB)
└── etc/
    └── fstab           (512 bytes)
```

## 1.2 What a Filesystem Must Provide

| Capability | What it means |
|---|---|
| **Namespace** | Human-readable names for data (files, dirs) |
| **Metadata** | Who owns a file, when was it modified, permissions |
| **Space management** | Track which blocks are free vs used |
| **Data mapping** | Given a filename, find the actual disk blocks |
| **Crash safety** | If power fails mid-write, don't corrupt data |
| **Performance** | Minimize seeks, maximize throughput |

## 1.3 Key Vocabulary (Defined First)

Before going deeper, let's define every technical term you'll encounter:

| Term | Definition |
|---|---|
| **Block** | Smallest unit of disk I/O. In ext4, typically 4096 bytes |
| **Inode** | A fixed-size structure storing file metadata (NOT the filename) |
| **Superblock** | The master control record of the filesystem |
| **Block Group** | A cluster of consecutive blocks; ext4 divides the disk into these |
| **Journal** | A log of pending changes, used for crash recovery |
| **Extent** | A contiguous range of disk blocks (start block + length) |
| **dentry** | Directory entry — maps a filename to an inode number |
| **VFS** | Virtual Filesystem Switch — the kernel abstraction layer |
| **Page Cache** | RAM used to cache recently read/written disk data |
| **writeback** | The process of flushing dirty (modified) pages from RAM to disk |
| **delalloc** | Delayed allocation — deferring block assignment to improve layout |
| **JBD2** | Journaling Block Device 2 — the journal subsystem used by ext4 |
| **checksum** | A hash of data used to detect corruption |
| **htree** | A hash-indexed B-tree used for large directories |
| **orphan** | An inode with no directory entry (deleted while open) |
| **bitmap** | A sequence of bits, 1 = used, 0 = free |

---

# 2. Storage Hardware Fundamentals

## 2.1 HDDs (Hard Disk Drives)

A traditional HDD has physical spinning platters and a read/write arm.

```
         ┌───────────────────────────────┐
         │        Spindle (motor)        │
         │  ┌───┐  ┌───┐  ┌───┐         │
         │  │P1 │  │P2 │  │P3 │  Platters│
         │  └───┘  └───┘  └───┘         │
         │     ↕          Read/Write Arm │
         └───────────────────────────────┘

Platter surface:
         Track 0 (outer)
     ┌───────────────────────────────────┐
     │  Sector 0 │ Sector 1 │ Sector 2  │  ← Track
     └───────────────────────────────────┘
         Track 1
     └───────────────────────────────────┘
```

- **Sector**: Smallest addressable unit, historically 512 bytes (modern: 4096 = "4Kn" drives)
- **Track**: A circular path on the platter
- **Cylinder**: The same track across all platters
- **Seek time**: Time for the arm to move to the right track (~5-15ms)
- **Rotational latency**: Waiting for the right sector to spin under the head (~0-8ms at 7200 RPM)

**Key insight for filesystems**: HDDs are dramatically faster for **sequential** access than **random** access. A good filesystem (like ext4) tries to place related data close together.

## 2.2 SSDs (Solid State Drives)

SSDs use NAND flash memory cells:

```
SSD Internal Structure:
┌────────────────────────────────────────────────────────┐
│ Controller (ARM CPU + DRAM cache)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Die 0   │  │  Die 1   │  │  Die 2   │  NAND Dies  │
│  │ Plane 0  │  │ Plane 0  │  │ Plane 0  │             │
│  │ Block 0  │  │ ...      │  │ ...      │             │
│  │ Page 0-N │  │          │  │          │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└────────────────────────────────────────────────────────┘
```

- **Page** (in SSD context): ~4KB-16KB, smallest writable unit
- **Block** (in SSD context): ~256KB-4MB, smallest erasable unit
- **Write amplification**: SSDs cannot overwrite in place; must erase an entire block first
- **FTL** (Flash Translation Layer): Maps logical block addresses to physical NAND locations
- **Wear leveling**: Spreads writes evenly to prevent early cell death

**Key insight**: SSDs have near-equal random/sequential read speed, but writes still benefit from sequential patterns due to write amplification.

## 2.3 Block Device Abstraction

Linux presents all storage as a **block device** — a uniform interface:

```
Application
    │
    ▼
Filesystem (ext4, xfs, btrfs...)
    │
    ▼
VFS (Virtual Filesystem Switch)
    │
    ▼
Block Layer (I/O Scheduler, request merging)
    │
    ▼
Device Driver (SCSI, NVMe, SATA...)
    │
    ▼
Physical Device (HDD, SSD, RAID...)
```

Block devices appear as files in `/dev/`:
- `/dev/sda` — SATA disk
- `/dev/nvme0n1` — NVMe SSD
- `/dev/vda` — Virtual disk (VM)

---

# 3. The ext Family: History & Evolution

## 3.1 Filesystem Evolution Tree

```
1992 ── ext (Extended Filesystem)
           │  Problems: no timestamps, max 2GB
           ▼
1993 ── ext2
           │  Added: proper inodes, 32-bit timestamps, 16TB max
           │  Problem: no journaling → long fsck on crash
           ▼
1999 ── ext3
           │  Added: journaling (via JBD), online resizing
           │  Problem: limited to 32-bit block pointers, slow for large dirs
           ▼
2008 ── ext4  ◄─── We are here
           │  Added: extents, 64-bit support, delayed allocation,
           │         dir htree, metadata checksums, online defrag,
           │         nanosecond timestamps, large files (16 TB)
           ▼
Future ── (btrfs, bcachefs as potential successors)
```

## 3.2 ext4 Key Specifications

| Feature | ext4 limit |
|---|---|
| Max filesystem size | 1 exabyte (1 EB = 10^18 bytes) |
| Max file size | 16 TiB |
| Max filename length | 255 bytes |
| Max files per filesystem | 4 billion (2^32) |
| Block size | 1KB, 2KB, 4KB (default), 64KB (with bigalloc) |
| Timestamp resolution | Nanosecond |
| Timestamp range | 1901–2446 |
| Journal size | 1MB – 1GB |

---

# 4. Disk Layout: The Big Picture

## 4.1 Partition vs Filesystem

Before ext4 even starts, the disk must be partitioned:

```
Physical Disk:
┌────────────────────────────────────────────────────────────────────┐
│ MBR/GPT (partition table at sector 0)                              │
├────────────────────┬───────────────────┬───────────────────────────┤
│ Partition 1        │ Partition 2        │ Partition 3               │
│ /dev/sda1 (EFI)   │ /dev/sda2 (/)     │ /dev/sda3 (swap)          │
│ FAT32              │ ext4               │ swap                      │
└────────────────────┴───────────────────┴───────────────────────────┘
```

- **MBR** (Master Boot Record): Old scheme, max 2TB, max 4 primary partitions
- **GPT** (GUID Partition Table): Modern, max 9.4 ZB, 128 partitions

## 4.2 ext4 On-Disk Layout (Full View)

Once a partition is formatted with `mkfs.ext4`, the space is organized like this:

```
ext4 Partition (e.g., /dev/sda2):

Byte 0                                                      End
┌──────────┬─────────────────────────────────────────────────┐
│  Boot    │                   Block Groups                   │
│ Sector   │                                                  │
│ (1024 B) │  [Group 0][Group 1][Group 2]...[Group N]        │
└──────────┴─────────────────────────────────────────────────┘

Each Block Group (e.g., 128MB for 4KB blocks, 32768 blocks):
┌──────────┬────────────┬────────────┬──────────┬────────────┬───────────────────┐
│Superblock│  Group     │  Block     │  Inode   │  Inode     │  Data Blocks      │
│(backup)  │Descriptor  │  Bitmap    │  Bitmap  │  Table     │                   │
│ 1 block  │  1 block   │  1 block   │ 1 block  │  N blocks  │  Remaining blocks │
└──────────┴────────────┴────────────┴──────────┴────────────┴───────────────────┘
 ^-- Only group 0 has the primary superblock
```

**Critical concept — Group 0** always starts at block 0 (or after the 1024-byte boot sector). It contains the **primary superblock** at byte offset 1024. All other groups may contain **backup superblocks** (for recovery).

## 4.3 Understanding Block Numbering

Every block has a **logical block number** (LBN). Block 0 is the very first block of the partition.

```
Block 0      Block 1      Block 2      Block 3   ...
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Boot     │ │Superblock│ │  Group   │ │  Block   │
│ Sector   │ │(1024–2048│ │Descriptor│ │  Bitmap  │
│(0–1023 B)│ │offset)   │ │  Table   │ │          │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
   ^
   This 1024-byte "padding" is for BIOS boot code (legacy)
```

---

# 5. The Superblock: The Master Record

## 5.1 What is the Superblock?

The **superblock** is a single, critical data structure that describes the entire filesystem. It lives at byte offset **1024** from the start of the partition (block 1 in a 1KB-block filesystem, still the first block if 4KB blocks since 1024 < 4096).

Think of it as the "birth certificate" of the filesystem — every critical parameter lives here.

## 5.2 Superblock Fields (from Linux kernel `fs/ext4/ext4.h`)

```c
/* Simplified version of struct ext4_super_block */
struct ext4_super_block {
    /* Core counts */
    __le32  s_inodes_count;         /* Total inode count */
    __le32  s_blocks_count_lo;      /* Total block count (low 32 bits) */
    __le32  s_r_blocks_count_lo;    /* Reserved blocks (for root) */
    __le32  s_free_blocks_count_lo; /* Free block count */
    __le32  s_free_inodes_count;    /* Free inode count */
    __le32  s_first_data_block;     /* First data block (0 for 4KB, 1 for 1KB) */
    __le32  s_log_block_size;       /* Block size = 1024 << s_log_block_size */
                                    /*   0 = 1KB, 1 = 2KB, 2 = 4KB */
    __le32  s_log_cluster_size;     /* Cluster size (bigalloc) */
    __le32  s_blocks_per_group;     /* Blocks per block group */
    __le32  s_clusters_per_group;   /* Clusters per group */
    __le32  s_inodes_per_group;     /* Inodes per block group */

    /* Timestamps */
    __le32  s_mtime;                /* Last mount time (Unix epoch) */
    __le32  s_wtime;                /* Last write time */
    __le16  s_mnt_count;           /* Mount count since last fsck */
    __le16  s_max_mnt_count;       /* Max mounts before fsck required */

    /* Magic number */
    __le16  s_magic;               /* MUST be 0xEF53 — identifies ext2/3/4 */

    /* State and behavior */
    __le16  s_state;               /* 0x0001=clean, 0x0002=errors */
    __le16  s_errors;              /* On error: 1=continue, 2=remount-ro, 3=panic */
    __le16  s_minor_rev_level;     /* Minor revision level */
    __le32  s_lastcheck;           /* Last fsck time */
    __le32  s_checkinterval;       /* Max time between fscks */
    __le32  s_creator_os;          /* 0=Linux, 3=FreeBSD, etc. */
    __le32  s_rev_level;           /* 0=original, 1=dynamic (ext4 uses 1) */
    __le16  s_def_resuid;          /* Default UID for reserved blocks */
    __le16  s_def_resgid;          /* Default GID for reserved blocks */

    /* EXT4-specific fields (rev_level = 1) */
    __le32  s_first_ino;           /* First non-reserved inode (usually 11) */
    __le16  s_inode_size;          /* Inode structure size (128 for ext2/3, 256 for ext4) */
    __le16  s_block_group_nr;      /* Which block group holds THIS superblock */
    __le32  s_feature_compat;      /* Compatible feature set flags */
    __le32  s_feature_incompat;    /* Incompatible feature set flags */
    __le32  s_feature_ro_compat;   /* Read-only compatible feature flags */
    __u8    s_uuid[16];            /* 128-bit filesystem UUID */
    char    s_volume_name[16];     /* Volume name (null-terminated) */
    char    s_last_mounted[64];    /* Last mount point path */

    /* Journal info */
    __le32  s_journal_inum;        /* Inode number of journal file */
    __le32  s_journal_dev;         /* Device number of journal (if external) */
    __le32  s_last_orphan;         /* Head of orphan inode list */

    /* Hash seeds for dir htree */
    __le32  s_hash_seed[4];        /* HTREE hash seed */
    __u8    s_def_hash_version;    /* Default hash algorithm */

    /* 64-bit support */
    __le32  s_blocks_count_hi;     /* High 32 bits of block count */
    __le32  s_r_blocks_count_hi;   /* High 32 bits of reserved blocks */
    __le32  s_free_blocks_count_hi;/* High 32 bits of free blocks */

    /* Checksum */
    __le32  s_checksum;            /* CRC32c of superblock */
};
```

## 5.3 Feature Flags Explained

Feature flags are **bitmasks** that tell the kernel what features this filesystem uses. There are three categories:

**Compatible (compat)** — Can be ignored by older kernels (won't break RW):
```
EXT4_FEATURE_COMPAT_DIR_PREALLOC    = 0x0001  (dir preallocation)
EXT4_FEATURE_COMPAT_HAS_JOURNAL     = 0x0004  (has a journal)
EXT4_FEATURE_COMPAT_EXT_ATTR        = 0x0008  (extended attributes)
EXT4_FEATURE_COMPAT_RESIZE_INODE   = 0x0010  (online resize)
EXT4_FEATURE_COMPAT_DIR_INDEX      = 0x0020  (htree directories)
EXT4_FEATURE_COMPAT_SPARSE_SUPER2  = 0x0200  (sparse superblock v2)
```

**Incompatible (incompat)** — Must be understood or refuse to mount:
```
EXT4_FEATURE_INCOMPAT_COMPRESSION   = 0x0001  (compression — not used)
EXT4_FEATURE_INCOMPAT_FILETYPE     = 0x0002  (file type in dir entries)
EXT4_FEATURE_INCOMPAT_RECOVER      = 0x0004  (journal recovery needed)
EXT4_FEATURE_INCOMPAT_JOURNAL_DEV  = 0x0008  (journal on separate device)
EXT4_FEATURE_INCOMPAT_META_BG      = 0x0010  (meta block groups)
EXT4_FEATURE_INCOMPAT_EXTENTS      = 0x0040  (extent trees — KEY ext4 feature)
EXT4_FEATURE_INCOMPAT_64BIT        = 0x0080  (64-bit block numbers)
EXT4_FEATURE_INCOMPAT_FLEX_BG      = 0x0200  (flexible block groups)
EXT4_FEATURE_INCOMPAT_ENCRYPT      = 0x10000 (filesystem-level encryption)
```

**Read-Only Compatible (ro_compat)** — Older kernels can mount read-only:
```
EXT4_FEATURE_RO_COMPAT_SPARSE_SUPER = 0x0001  (sparse superblock copies)
EXT4_FEATURE_RO_COMPAT_LARGE_FILE  = 0x0002  (files > 2GB)
EXT4_FEATURE_RO_COMPAT_HUGE_FILE   = 0x0008  (files > 2TB)
EXT4_FEATURE_RO_COMPAT_GDT_CSUM    = 0x0010  (group descriptor checksum)
EXT4_FEATURE_RO_COMPAT_DIR_NLINK   = 0x0020  (nlink > 65000)
EXT4_FEATURE_RO_COMPAT_EXTRA_ISIZE = 0x0040  (inode extra fields)
EXT4_FEATURE_RO_COMPAT_METADATA_CSUM= 0x0400  (metadata checksums)
```

## 5.4 Reading the Superblock in C

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

/* Minimal superblock structure for reading */
#define EXT4_SUPER_MAGIC  0xEF53
#define SUPERBLOCK_OFFSET 1024   /* Always at byte 1024 */
#define SUPERBLOCK_SIZE   1024   /* 1024 bytes */

/* We use packed to prevent compiler from adding padding bytes */
struct __attribute__((packed)) ext4_superblock_minimal {
    uint32_t s_inodes_count;
    uint32_t s_blocks_count_lo;
    uint32_t s_r_blocks_count_lo;
    uint32_t s_free_blocks_count_lo;
    uint32_t s_free_inodes_count;
    uint32_t s_first_data_block;
    uint32_t s_log_block_size;       /* block_size = 1024 << this */
    uint32_t s_log_cluster_size;
    uint32_t s_blocks_per_group;
    uint32_t s_clusters_per_group;
    uint32_t s_inodes_per_group;
    uint32_t s_mtime;
    uint32_t s_wtime;
    uint16_t s_mnt_count;
    uint16_t s_max_mnt_count;
    uint16_t s_magic;               /* Should be 0xEF53 */
    uint16_t s_state;
    uint16_t s_errors;
    uint16_t s_minor_rev_level;
    uint32_t s_lastcheck;
    uint32_t s_checkinterval;
    uint32_t s_creator_os;
    uint32_t s_rev_level;
    uint16_t s_def_resuid;
    uint16_t s_def_resgid;
    /* Rev 1 fields */
    uint32_t s_first_ino;
    uint16_t s_inode_size;
    uint16_t s_block_group_nr;
    uint32_t s_feature_compat;
    uint32_t s_feature_incompat;
    uint32_t s_feature_ro_compat;
    uint8_t  s_uuid[16];
    char     s_volume_name[16];
};

void print_uuid(uint8_t uuid[16]) {
    printf("%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
        uuid[0],  uuid[1],  uuid[2],  uuid[3],
        uuid[4],  uuid[5],
        uuid[6],  uuid[7],
        uuid[8],  uuid[9],
        uuid[10], uuid[11], uuid[12], uuid[13], uuid[14], uuid[15]);
}

int read_superblock(const char *device_path) {
    int fd = open(device_path, O_RDONLY);
    if (fd < 0) {
        perror("open");
        return -1;
    }

    struct ext4_superblock_minimal sb;

    /* Seek to byte 1024 (where superblock lives) */
    if (lseek(fd, SUPERBLOCK_OFFSET, SEEK_SET) < 0) {
        perror("lseek");
        close(fd);
        return -1;
    }

    /* Read the superblock */
    if (read(fd, &sb, sizeof(sb)) < 0) {
        perror("read");
        close(fd);
        return -1;
    }

    /* Validate magic number */
    if (sb.s_magic != EXT4_SUPER_MAGIC) {
        fprintf(stderr, "Not an ext2/3/4 filesystem! Magic: 0x%04x\n", sb.s_magic);
        close(fd);
        return -1;
    }

    /* Compute block size: 1024 << s_log_block_size */
    uint32_t block_size = 1024 << sb.s_log_block_size;
    uint64_t total_blocks = sb.s_blocks_count_lo;
    uint64_t total_size   = total_blocks * block_size;

    printf("=== EXT4 Superblock ===\n");
    printf("Magic:               0x%04x ✓\n", sb.s_magic);
    printf("Volume name:         %.16s\n",     sb.s_volume_name);
    printf("UUID:                ");
    print_uuid(sb.s_uuid);
    printf("\n");
    printf("Block size:          %u bytes\n",  block_size);
    printf("Total blocks:        %lu\n",        (unsigned long)total_blocks);
    printf("Total size:          %lu MB\n",     (unsigned long)(total_size / (1024*1024)));
    printf("Free blocks:         %u\n",         sb.s_free_blocks_count_lo);
    printf("Total inodes:        %u\n",         sb.s_inodes_count);
    printf("Free inodes:         %u\n",         sb.s_free_inodes_count);
    printf("Inodes per group:    %u\n",         sb.s_inodes_per_group);
    printf("Blocks per group:    %u\n",         sb.s_blocks_per_group);
    printf("Inode size:          %u bytes\n",   sb.s_inode_size);
    printf("First inode:         %u\n",         sb.s_first_ino);
    printf("Mount count:         %u\n",         sb.s_mnt_count);

    /* Compute number of block groups */
    uint32_t num_groups = (total_blocks + sb.s_blocks_per_group - 1)
                         / sb.s_blocks_per_group;
    printf("Block groups:        %u\n",         num_groups);

    /* State */
    const char *state_str = (sb.s_state == 1) ? "clean" :
                            (sb.s_state == 2) ? "errors detected" : "unknown";
    printf("State:               %s\n",         state_str);

    /* Last mounted time */
    time_t mtime = sb.s_mtime;
    printf("Last mounted:        %s",           ctime(&mtime));

    /* Rev level */
    printf("Revision:            %u\n",         sb.s_rev_level);

    /* Feature flags */
    printf("Feature incompat:    0x%08x\n",     sb.s_feature_incompat);
    if (sb.s_feature_incompat & 0x0040)
        printf("  - EXTENTS (ext4 extent trees)\n");
    if (sb.s_feature_incompat & 0x0080)
        printf("  - 64BIT support\n");
    if (sb.s_feature_incompat & 0x0200)
        printf("  - FLEX_BG\n");

    close(fd);
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <device>\n", argv[0]);
        fprintf(stderr, "Example: %s /dev/sda1\n", argv[0]);
        fprintf(stderr, "         %s disk.img\n", argv[0]);
        return 1;
    }
    return read_superblock(argv[1]);
}

/* Compile:  gcc -O2 -o read_sb read_sb.c
   Run:      sudo ./read_sb /dev/sda1
             sudo ./read_sb /dev/nvme0n1p2
*/
```

## 5.5 Superblock Backups

ext4 keeps **backup copies** of the superblock in certain block groups. This is because if block group 0 (containing the primary superblock) is corrupted, we need a way to recover.

With the `sparse_super` feature (default), backups exist only in block groups:
- Group 0 (primary)
- Groups that are powers of 3, 5, or 7: 1, 3, 5, 7, 9, 25, 27, 49, ...

```
Group:    0    1    2    3    4    5    6    7    8    9   10  ...
Backup:   ✓    ✓    ✗    ✓    ✗    ✓    ✗    ✓    ✗    ✓   ✗  ...
          │    │         │         │         │         │
        primary  1^1    3^1       5^1       7^1       9=3^2
```

Recovery using backup: `sudo e2fsck -b 32768 /dev/sda1` (use group 1's backup)

---

# 6. Block Groups: Divide and Conquer

## 6.1 Why Block Groups?

If we had one giant bitmap tracking every block's free/used status, allocating near where you need it would require searching the whole disk. Block groups solve this by dividing the filesystem into **local zones**.

**The key insight**: When creating a file, ext4 tries to allocate its inode and data blocks in the **same block group**, minimizing seek distances.

## 6.2 Block Group Size

With 4KB blocks:
- **Blocks per group** = 8 × block_size_in_bytes = 8 × 4096 = **32768 blocks**
  - (Because the block bitmap is 1 block = 4096 bytes = 32768 bits)
- **Group size** = 32768 × 4096 = **128 MB per group**

So a 1TB ext4 filesystem has approximately 8192 block groups.

## 6.3 Block Group Descriptor Table (GDT)

The **Group Descriptor Table** (GDT) is an array of `ext4_group_desc` structures, one per block group. It lives immediately after the superblock (or its backup).

```c
/* From linux/fs/ext4/ext4.h */
struct ext4_group_desc {
    __le32  bg_block_bitmap_lo;      /* Block number of block bitmap */
    __le32  bg_inode_bitmap_lo;      /* Block number of inode bitmap */
    __le32  bg_inode_table_lo;       /* Block number of inode table */
    __le16  bg_free_blocks_count_lo; /* Free blocks in this group */
    __le16  bg_free_inodes_count_lo; /* Free inodes in this group */
    __le16  bg_used_dirs_count_lo;   /* Number of directories */
    __le16  bg_flags;                /* EXT4_BG_* flags */
    __le32  bg_exclude_bitmap_lo;    /* Snapshot exclude bitmap */
    __le16  bg_block_bitmap_csum_lo; /* Block bitmap checksum */
    __le16  bg_inode_bitmap_csum_lo; /* Inode bitmap checksum */
    __le16  bg_itable_unused_lo;     /* Unused inodes count */
    __le16  bg_checksum;             /* CRC16 of sb UUID+group+desc */

    /* 64-bit fields (only present if 64bit feature is enabled) */
    __le32  bg_block_bitmap_hi;
    __le32  bg_inode_bitmap_hi;
    __le32  bg_inode_table_hi;
    __le16  bg_free_blocks_count_hi;
    __le16  bg_free_inodes_count_hi;
    __le16  bg_used_dirs_count_hi;
    __le16  bg_itable_unused_hi;
    __le32  bg_exclude_bitmap_hi;
    __le16  bg_block_bitmap_csum_hi;
    __le16  bg_inode_bitmap_csum_hi;
    __le32  bg_reserved;
};
```

## 6.4 Block Group Internal Layout (Detailed)

```
Block Group N (128 MB, 32768 blocks of 4KB):
┌──────────┬──────────┬──────────┬──────────┬─────────────────────────────────────┐
│ Optional │  Block   │  Inode   │  Inode   │           Data Blocks               │
│  SB+GDT  │  Bitmap  │  Bitmap  │  Table   │        (inodes' actual data)        │
│ (backup) │ 1 block  │ 1 block  │ N blocks │                                     │
│          │ 4096 bits│ 4096 bits│          │                                     │
└──────────┴──────────┴──────────┴──────────┴─────────────────────────────────────┘
           ▲          ▲          ▲
           │          │          └── bg_inode_table_lo
           │          └──────────── bg_inode_bitmap_lo
           └─────────────────────── bg_block_bitmap_lo
           All three come from the group descriptor!
```

## 6.5 Flex Block Groups

With the `flex_bg` feature (default in modern ext4), several consecutive block groups are organized as a **flex group**. The metadata (bitmaps and inode tables) of all groups in the flex set are pooled together in the first group, leaving more contiguous space for data in subsequent groups.

```
Flex Group (flex_bg_size = 16, groups 0–15):

Group 0: [SB][GDT][Bitmap0][IBitmap0][ITable0][Bitmap1][IBitmap1][ITable1]...[Data0]
Group 1: [Data1 only — no metadata overhead!]
Group 2: [Data2 only]
...
Group 15: [Data15 only]
```

This dramatically improves large sequential writes by keeping metadata far from data.

---

# 7. Inodes: The DNA of Every File

## 7.1 What is an Inode?

**Inode** stands for "index node." It is the central data structure representing a file (or directory, or symlink, or device). Crucially:

- An inode stores **everything about a file EXCEPT its name**
- The filename lives in a **directory entry** (dentry) that points to the inode
- Each inode has a unique **inode number** within the filesystem

```
Directory entry (dentry):                Inode:
┌─────────────────────────┐             ┌──────────────────────────┐
│ name: "notes.txt"       │──inode_nr──►│ size: 4096 bytes         │
│ inode_nr: 42            │             │ uid: 1000                │
└─────────────────────────┘             │ gid: 1000                │
                                        │ mode: 0644 (-rw-r--r--)  │
                                        │ atime: 2024-01-15 10:30  │
                                        │ mtime: 2024-01-15 09:00  │
                                        │ ctime: 2024-01-15 09:00  │
                                        │ nlinks: 1                │
                                        │ blocks: [42, 43, ...]    │
                                        └──────────────────────────┘
                                                    │
                                                    ▼ (data blocks)
                                        ┌──────────────────────────┐
                                        │  Actual file contents    │
                                        │  "Hello, world!\n..."    │
                                        └──────────────────────────┘
```

This separation is what makes **hard links** possible: multiple directory entries pointing to the same inode number.

## 7.2 The Inode Structure (ext4, 256 bytes)

```c
/*
 * Structure of an inode on the disk
 * From: linux/fs/ext4/ext4.h
 *
 * In ext4, inodes are 256 bytes by default (s_inode_size in superblock).
 * ext2/3 used 128 bytes. The extra 128 bytes in ext4 store extra timestamps,
 * version info, and the crucial "extra size" field for future expansion.
 */
struct ext4_inode {
    /* ── BLOCK 1 (bytes 0–127, same as ext2/ext3) ─────────────────── */
    __le16  i_mode;          /* File mode (permissions + type) */
    __le16  i_uid;           /* Low 16 bits of owner uid */
    __le32  i_size_lo;       /* Lower 32 bits of file size in bytes */
    __le32  i_atime;         /* Last access time (seconds since epoch) */
    __le32  i_ctime;         /* Inode change time */
    __le32  i_mtime;         /* Last data modification time */
    __le32  i_dtime;         /* Deletion time (0 if not deleted) */
    __le16  i_gid;           /* Low 16 bits of group id */
    __le16  i_links_count;   /* Hard link count */
    __le32  i_blocks_lo;     /* Block count (in 512-byte units, lower 32 bits) */
    __le32  i_flags;         /* File flags (see below) */

    union {
        struct { __le32 l_i_version; } linux1;
        /* osd1 — OS-dependent field 1 */
    } osd1;

    /*
     * i_block[15]: The 60-byte block mapping array.
     * In ext4 with extents, this holds the EXTENT TREE ROOT.
     * In ext2/3 mode, this holds block pointers (12 direct + 3 indirect).
     */
    __le32  i_block[EXT4_N_BLOCKS];  /* EXT4_N_BLOCKS = 15 */

    __le32  i_generation;    /* File version (NFS use) */
    __le32  i_file_acl_lo;   /* Lower 32 bits of extended attribute block */
    __le32  i_size_high;     /* Upper 32 bits of file size (for large files) */
    __le32  i_obso_faddr;    /* Obsolete fragment address */

    union {
        struct {
            __le16 l_i_blocks_high;  /* High 16 bits of block count */
            __le16 l_i_file_acl_high;
            __le16 l_i_uid_high;     /* High 16 bits of uid */
            __le16 l_i_gid_high;     /* High 16 bits of gid */
            __le16 l_i_checksum_lo;  /* Lower 16 bits of inode checksum */
            __le16 l_i_reserved;
        } linux2;
    } osd2;

    /* ── BLOCK 2 (bytes 128–255, ext4 extension) ────────────────────── */
    __le16  i_extra_isize;        /* Size of extra fields beyond 128 bytes */
    __le16  i_checksum_hi;        /* High 16 bits of inode checksum */
    __le32  i_ctime_extra;        /* Extra change time bits (nanoseconds) */
    __le32  i_mtime_extra;        /* Extra modification time bits */
    __le32  i_atime_extra;        /* Extra access time bits */
    __le32  i_crtime;             /* File creation time (seconds) */
    __le32  i_crtime_extra;       /* File creation time extra (nanoseconds) */
    __le32  i_version_hi;         /* High 32 bits of file version */
    __le32  i_projid;             /* Project ID */
};
```

## 7.3 Understanding i_mode: File Type + Permissions

The `i_mode` field is a 16-bit number encoding both the **file type** and the **permissions**:

```
Bit layout of i_mode (16 bits):
Bit: 15  14  13  12  11  10   9   8   7   6   5   4   3   2   1   0
     ├────────────┤  ├─────────────────────────────────────────────┤
          TYPE                      PERMISSIONS
     
Type bits (bits 12–15):
  0100 = regular file  (S_IFREG = 0x8000)
  0010 = directory     (S_IFDIR = 0x4000)
  1010 = symbolic link (S_IFLNK = 0xA000)
  0110 = block device  (S_IFBLK = 0x6000)
  0010 = char device   (S_IFCHR = 0x2000)
  0001 = FIFO          (S_IFIFO = 0x1000)
  1100 = socket        (S_IFSOCK= 0xC000)

Permission bits (bits 0–8) — the familiar rwxrwxrwx:
  Bit 8 = owner read     (S_IRUSR)
  Bit 7 = owner write    (S_IWUSR)
  Bit 6 = owner execute  (S_IXUSR)
  Bit 5 = group read     (S_IRGRP)
  Bit 4 = group write    (S_IWGRP)
  Bit 3 = group execute  (S_IXGRP)
  Bit 2 = other read     (S_IROTH)
  Bit 1 = other write    (S_IWOTH)
  Bit 0 = other execute  (S_IXOTH)

Special bits (bits 9–11):
  Bit 11 = setuid (SUID) — run as file owner
  Bit 10 = setgid (SGID) — run as file group
  Bit 9  = sticky — only owner can delete in dir

Example: -rw-r--r-- (0100644)
  = 0100 (regular) + 110 100 100
    = 0x8000 | 0x0180 | 0x0020 | 0x0004 = 0x81A4
    
Example: drwxr-xr-x (0040755)
  = 0010 (directory) + 111 101 101
    = 0x4000 | 0x01C0 | 0x0028 | 0x0005 = 0x41ED
```

## 7.4 inode Flags (i_flags)

```c
#define EXT4_SECRM_FL           0x00000001  /* Secure deletion */
#define EXT4_UNRM_FL            0x00000002  /* Undelete */
#define EXT4_COMPR_FL           0x00000004  /* Compress file */
#define EXT4_SYNC_FL            0x00000008  /* Sync updates */
#define EXT4_IMMUTABLE_FL       0x00000010  /* Immutable file — no writes, deletes */
#define EXT4_APPEND_FL          0x00000020  /* Append only */
#define EXT4_NODUMP_FL          0x00000040  /* Do not dump */
#define EXT4_NOATIME_FL         0x00000080  /* Do not update atime */
#define EXT4_DIRTY_FL           0x00000100  /* Dirty (modified) */
#define EXT4_COMPRBLK_FL        0x00000200  /* One or more compressed clusters */
#define EXT4_NOCOMPR_FL         0x00000400  /* Access raw compressed data */
#define EXT4_ENCRYPT_FL         0x00000800  /* Encrypted inode */
#define EXT4_INDEX_FL           0x00001000  /* Hash-indexed directory */
#define EXT4_IMAGIC_FL          0x00002000  /* AFS directory */
#define EXT4_JOURNAL_DATA_FL    0x00004000  /* File data should be journaled */
#define EXT4_NOTAIL_FL          0x00008000  /* File tail should not be merged */
#define EXT4_DIRSYNC_FL         0x00010000  /* Dirsync behaviour (dirs only) */
#define EXT4_TOPDIR_FL          0x00020000  /* Top of directory hierarchies */
#define EXT4_HUGE_FILE_FL       0x00040000  /* Set to each huge file */
#define EXT4_EXTENTS_FL         0x00080000  /* Inode uses extents — KEY FLAG */
#define EXT4_EA_INODE_FL        0x00200000  /* Inode used for large EA */
#define EXT4_INLINE_DATA_FL     0x10000000  /* Data stored inline in inode */
#define EXT4_PROJINHERIT_FL     0x20000000  /* Inherit project ID */
#define EXT4_CASEFOLD_FL        0x40000000  /* Case-insensitive filename */
```

## 7.5 Timestamp Precision in ext4

ext4 stores timestamps at **nanosecond precision** using a clever scheme:

```
i_atime       (32 bits): seconds since 1970-01-01 00:00:00 UTC
i_atime_extra (32 bits): extra bits

Layout of i_atime_extra:
Bits 31–2: nanoseconds (30 bits, range 0–999,999,999)
Bits 1–0:  high 2 bits of seconds (extends range from 2^32 to 2^34)

Total seconds range: 2^34 = 17,179,869,184 seconds
  Start: 1901-12-13 20:45:52 UTC (signed, using 2's complement trick)
  End:   2446-05-10 22:38:55 UTC
```

## 7.6 Reserved Inodes

The first 10 inodes are **reserved** by ext4:

| Inode # | Purpose |
|---|---|
| 0 | Doesn't exist (0 = null/invalid) |
| 1 | Defective block list |
| 2 | **Root directory** (`/`) — ALWAYS inode 2 |
| 3 | User quota |
| 4 | Group quota |
| 5 | Boot loader |
| 6 | Undelete directory |
| 7 | Reserved group descriptors |
| 8 | **Journal inode** (the journal is a file!) |
| 9 | Exclude inode (snapshots) |
| 10 | Replica inode |
| 11 | First non-reserved inode (configurable via s_first_ino) |

## 7.7 Finding an Inode on Disk (The Math)

Given inode number `n`, here's how ext4 locates it:

```
Step 1: Which block group?
  group = (n - 1) / s_inodes_per_group

Step 2: Which index within that group's inode table?
  index = (n - 1) % s_inodes_per_group

Step 3: Which block within the inode table?
  inode_table_block = bg_inode_table_lo  (from group descriptor)
  offset_in_table   = index * s_inode_size
  block_offset      = offset_in_table / block_size
  target_block      = inode_table_block + block_offset

Step 4: Which byte within that block?
  byte_in_block = offset_in_table % block_size

Example (4KB blocks, 256 inodes/group, 256-byte inodes):
  Find inode 42:
    group = (42 - 1) / 256 = 0
    index = (42 - 1) % 256 = 41
    offset_in_table = 41 * 256 = 10496 bytes
    inode_table_block = bg_inode_table_lo (say it's block 5)
    block_offset = 10496 / 4096 = 2 (block 7)
    byte_in_block = 10496 % 4096 = 2304
    → Read 256 bytes at (block 7, offset 2304)
```

```
ASCII Visualization:
Inode Table (starting at block bg_inode_table_lo):

Block 5:       Block 6:       Block 7:
┌──────────┐  ┌──────────┐  ┌─────┬──────┬──────────┐
│ inode 1  │  │ inode 17 │  │ ... │ino42 │ inode 43 │
│ inode 2  │  │ inode 18 │  │     │◄─────│          │
│ ...      │  │ ...      │  │     │ HERE!│          │
│ inode 16 │  │ inode 32 │  │     │      │          │
└──────────┘  └──────────┘  └─────┴──────┴──────────┘
   (4096/256=16 inodes per block)
```

---

# 8. Extent Trees: How Data Blocks Are Found

## 8.1 The Problem with ext2/3 Block Pointers

In ext2/3, finding data blocks used **indirect block pointers**:

```
ext2/ext3 inode.i_block[15]:
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │10 │11 │12 │13 │14 │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
  ↑ direct (12 blocks)              ↑      ↑      ↑
                                 single  double  triple
                                indirect indirect indirect
```

- **Direct** (blocks 0–11): Point directly to data blocks (12 blocks = 48KB at 4KB/block)
- **Single indirect** (block 12): Points to a block full of block numbers (4096/4 = 1024 pointers = 4MB)
- **Double indirect** (block 13): Pointer → block of pointers → data (1024² = 4GB)
- **Triple indirect** (block 14): 3 levels deep (1024³ = 4TB)

**Problems with indirect blocks**:
1. For large files, accessing block 10,000 requires reading 2-3 extra blocks (the indirect blocks) first
2. **Fragmentation**: A 100MB file might be scattered across thousands of individual blocks, requiring thousands of entries in indirect blocks
3. **No metadata about contiguity**: The filesystem can't easily know "blocks 1000–2000 are all consecutive"

## 8.2 ext4 Extents: The Solution

An **extent** is a descriptor for a **contiguous run of blocks**:

```
Extent = (logical block number, physical block number, length)

Instead of:
  block[0] = physical block 1000
  block[1] = physical block 1001
  block[2] = physical block 1002
  ...
  block[99]= physical block 1099

We store ONE extent:
  (logical=0, physical=1000, len=100)
  = "logical blocks 0–99 map to physical blocks 1000–1099"
```

This is exponentially more efficient for large, contiguous files.

## 8.3 The Extent Tree Structure

ext4 uses the **60 bytes** of `i_block[15]` to store an **extent tree** (a B-tree variant):

```
The 60 bytes of i_block are used as:

┌──────────────────────────────────────────────────────────────┐
│                    60 bytes total                             │
├──────────────┬───────────────────────────────────────────────┤
│  ext4_extent │  ext4_extent structures (12 bytes each)       │
│    _header   │  OR ext4_extent_idx (12 bytes each)           │
│  (12 bytes)  │  4 entries fit (4 × 12 = 48 bytes)            │
└──────────────┴───────────────────────────────────────────────┘
```

### The Header

```c
struct ext4_extent_header {
    __le16  eh_magic;       /* Magic number: 0xF30A */
    __le16  eh_entries;     /* Number of valid entries */
    __le16  eh_max;         /* Maximum number of entries (capacity) */
    __le16  eh_depth;       /* Depth of tree:
                               0 = leaf node (has actual extents)
                               1 = one level above leaf (has index nodes)
                               N = N levels above leaf */
    __le32  eh_generation;  /* Generation counter */
};
```

### The Leaf Node (actual extents)

```c
struct ext4_extent {
    __le32  ee_block;    /* First logical block number this extent covers */
    __le16  ee_len;      /* Number of blocks covered (max 32768; unwritten if > 32768) */
    __le16  ee_start_hi; /* High 16 bits of physical block number */
    __le32  ee_start_lo; /* Low 32 bits of physical block number */
    /* Total physical block = (ee_start_hi << 32) | ee_start_lo */
};
```

### The Index Node (interior tree node)

```c
struct ext4_extent_idx {
    __le32  ei_block;    /* Logical block covered by this index */
    __le32  ei_leaf_lo;  /* Low 32 bits of physical block of child node */
    __le16  ei_leaf_hi;  /* High 16 bits of physical block of child node */
    __u16   ei_unused;
};
```

## 8.4 Extent Tree Depth=0 (Inline Extents — Most Common)

For files with few, contiguous extents (very common!), the tree fits entirely in the inode's 60 bytes:

```
i_block (60 bytes), depth=0 (leaf level IS the inode):

Bytes 0–11:  ext4_extent_header
  eh_magic   = 0xF30A
  eh_entries = 2        (2 extents stored)
  eh_max     = 4        (room for 4 extents)
  eh_depth   = 0        (this IS the leaf)

Bytes 12–23: ext4_extent #1
  ee_block    = 0       (starts at logical block 0)
  ee_len      = 1000    (1000 blocks = 4MB)
  ee_start    = 50000   (physical block 50000)
  → "logical blocks 0–999 = physical blocks 50000–50999"

Bytes 24–35: ext4_extent #2
  ee_block    = 1000    (starts at logical block 1000)
  ee_len      = 500     (500 blocks = 2MB)
  ee_start    = 80000   (physical block 80000)
  → "logical blocks 1000–1499 = physical blocks 80000–80499"

Bytes 36–47: (empty slot)
Bytes 48–59: (empty slot)
```

## 8.5 Extent Tree Depth=1 (One Level of Indirection)

When a file is very fragmented (many extents), the tree grows:

```
Inode's i_block (60 bytes), depth=1:

  Header (depth=1, entries=3)
  Index[0]: logical=0,    → physical block 7000 (child leaf node)
  Index[1]: logical=8000, → physical block 7001 (child leaf node)
  Index[2]: logical=16000,→ physical block 7002 (child leaf node)

Block 7000 (leaf node, depth=0):
  Header (depth=0, entries=340)
  Extent[0]: logical=0,    len=200, physical=10000
  Extent[1]: logical=200,  len=300, physical=20000
  Extent[2]: logical=500,  len=100, physical=30000
  ...340 extents total...

Block 7001 (leaf node, depth=0):
  ...up to 340 more extents...

Block 7002 (leaf node, depth=0):
  ...up to 340 more extents...
```

Each leaf block at 4KB can hold 4096/12 ≈ **340 extents**.
Each index block can hold 4096/12 ≈ **340 index entries**.
- Depth 0: max 4 extents (inline)
- Depth 1: 340 leaf blocks × 340 extents = ~115,600 extents
- Depth 2: 340 × 340 × 340 extents ≈ 39 million extents

## 8.6 Unwritten Extents (Preallocation)

An extent with `ee_len > 32768` is an **unwritten extent** — space has been allocated but not yet filled with data (all reads return zeros):

```
ee_len values:
  1–32767:     normal written extent
  32768–65535: unwritten extent (allocated but zeroed on read)
                The actual length = ee_len - 32768

Use case: fallocate() — preallocate disk space without writing data
  This prevents fragmentation for growing files (like databases, video files)
```

## 8.7 Implementing Extent Lookup in C

```c
/*
 * Extent tree lookup — given an inode and a logical block number,
 * find the corresponding physical block number.
 *
 * This is a simplified version of ext4_ext_find_extent() in the kernel.
 */

#include <stdint.h>
#include <string.h>
#include <stdio.h>

#define EXT4_EXT_MAGIC      0xF30A
#define EXT4_UNWRITTEN_MAX  0x8000  /* 32768 */

/* These structures match the on-disk format exactly */
typedef struct {
    uint16_t eh_magic;
    uint16_t eh_entries;
    uint16_t eh_max;
    uint16_t eh_depth;
    uint32_t eh_generation;
} __attribute__((packed)) ExtentHeader;

typedef struct {
    uint32_t ee_block;    /* First logical block */
    uint16_t ee_len;      /* Number of blocks (>=32768 means unwritten) */
    uint16_t ee_start_hi;
    uint32_t ee_start_lo;
} __attribute__((packed)) Extent;

typedef struct {
    uint32_t ei_block;    /* First logical block covered */
    uint32_t ei_leaf_lo;
    uint16_t ei_leaf_hi;
    uint16_t ei_unused;
} __attribute__((packed)) ExtentIndex;

/* Returns physical block number for logical block `lblk`.
 * buf: the inode's i_block[15] (60 bytes) or a loaded extent tree block
 * read_block_fn: callback to read a disk block into memory
 * Returns 0 on failure.
 */
typedef int (*ReadBlockFn)(uint64_t block_num, void *buf, void *ctx);

static uint64_t extent_get_physical(const Extent *ext) {
    return ((uint64_t)ext->ee_start_hi << 32) | ext->ee_start_lo;
}

static uint64_t index_get_leaf(const ExtentIndex *idx) {
    return ((uint64_t)idx->ei_leaf_hi << 32) | idx->ei_leaf_lo;
}

static int extent_len(const Extent *ext) {
    uint16_t len = ext->ee_len;
    if (len >= EXT4_UNWRITTEN_MAX)
        len -= EXT4_UNWRITTEN_MAX;  /* Remove unwritten flag */
    return len;
}

/*
 * Binary search: find the index i such that
 *   array[i].block <= target < array[i+1].block
 *
 * This mirrors ext4_ext_binsearch() in the kernel.
 */
static int binsearch_extent(const Extent *extents, int count, uint32_t target) {
    int lo = 0, hi = count - 1;
    int result = -1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (extents[mid].ee_block <= target) {
            result = mid;
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return result;
}

static int binsearch_index(const ExtentIndex *idxs, int count, uint32_t target) {
    int lo = 0, hi = count - 1;
    int result = -1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (idxs[mid].ei_block <= target) {
            result = mid;
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return result;
}

/*
 * Recursive extent tree lookup.
 * node: pointer to a 60-byte inode area or 4096-byte block
 * lblk: logical block we're looking for
 * depth_remaining: how many more levels to traverse
 */
uint64_t ext4_lookup_block(const void *node, uint32_t lblk,
                           ReadBlockFn read_block, void *ctx) {
    const ExtentHeader *hdr = (const ExtentHeader *)node;

    /* Validate magic */
    if (hdr->eh_magic != EXT4_EXT_MAGIC) {
        fprintf(stderr, "Bad extent magic: 0x%04x\n", hdr->eh_magic);
        return 0;
    }

    if (hdr->eh_depth == 0) {
        /* Leaf node: search through extents */
        const Extent *extents = (const Extent *)(hdr + 1);
        int idx = binsearch_extent(extents, hdr->eh_entries, lblk);
        if (idx < 0) return 0;  /* Block not found */

        const Extent *ext = &extents[idx];
        uint32_t offset = lblk - ext->ee_block;

        if (offset >= (uint32_t)extent_len(ext)) {
            return 0;  /* Outside this extent */
        }

        /* Physical block = start + offset */
        return extent_get_physical(ext) + offset;

    } else {
        /* Index node: find the right child, recurse */
        const ExtentIndex *idxs = (const ExtentIndex *)(hdr + 1);
        int i = binsearch_index(idxs, hdr->eh_entries, lblk);
        if (i < 0) return 0;

        /* Load the child block */
        uint64_t child_block = index_get_leaf(&idxs[i]);
        static uint8_t child_buf[4096];  /* 4KB block */

        if (read_block(child_block, child_buf, ctx) < 0) {
            fprintf(stderr, "Failed to read child block %lu\n",
                    (unsigned long)child_block);
            return 0;
        }

        /* Recurse into child */
        return ext4_lookup_block(child_buf, lblk, read_block, ctx);
    }
}

/* Demo usage */
void demonstrate_extent_parsing(void) {
    /*
     * Simulate an inode's i_block (60 bytes) with:
     *   - 1 extent: logical 0-999 → physical 50000-50999
     */
    uint8_t iblock[60];
    memset(iblock, 0, sizeof(iblock));

    ExtentHeader *hdr = (ExtentHeader *)iblock;
    hdr->eh_magic   = EXT4_EXT_MAGIC;
    hdr->eh_entries = 1;
    hdr->eh_max     = 4;
    hdr->eh_depth   = 0;

    Extent *ext = (Extent *)(iblock + sizeof(ExtentHeader));
    ext->ee_block    = 0;
    ext->ee_len      = 1000;
    ext->ee_start_lo = 50000;
    ext->ee_start_hi = 0;

    printf("Looking up logical block 500...\n");
    /* In real code, pass actual read_block function and fd */
    /* For demo, we only have depth=0 so no read needed */
    const ExtentHeader *h = (const ExtentHeader *)iblock;
    const Extent *e = (const Extent *)(h + 1);
    int i = binsearch_extent(e, h->eh_entries, 500);
    if (i >= 0) {
        uint64_t phys = extent_get_physical(&e[i]) + (500 - e[i].ee_block);
        printf("Physical block: %lu\n", (unsigned long)phys);
        /* Expected: 50000 + 500 = 50500 */
    }
}
```

---

# 9. Directories: Files That Contain Files

## 9.1 What is a Directory (at the bit level)?

A directory is an inode whose data blocks contain a list of **directory entries** (dentries). Each entry maps a **filename** to an **inode number**.

**Key insight**: A directory is just a special type of file. Its `i_mode` has the directory bit set, and its data is a stream of dentry records.

## 9.2 Linear Directory Format (small dirs)

For directories with few entries, ext4 uses the **linear (linked list)** format:

```c
struct ext4_dir_entry_2 {
    __le32  inode;          /* Inode number (0 = deleted/empty entry) */
    __le16  rec_len;        /* Total length of this entry (including padding) */
    __u8    name_len;       /* Length of filename (not null-terminated) */
    __u8    file_type;      /* File type (1=regular, 2=dir, 7=symlink, etc.) */
    char    name[];         /* Filename (variable length, NOT null-terminated) */
};
/* Total size of entry: 4+2+1+1 + name_len, rounded up to 4-byte alignment */
```

The `file_type` field:

| Value | Type |
|---|---|
| 0 | Unknown |
| 1 | Regular file |
| 2 | Directory |
| 3 | Character device |
| 4 | Block device |
| 5 | FIFO |
| 6 | Socket |
| 7 | Symbolic link |

## 9.3 Directory Block Layout (ASCII)

```
Directory data block (4096 bytes), a flat list of entries:

Offset 0:
┌──────────────────────────────────────────────────────────┐
│ inode=2    rec_len=12  name_len=1  type=2  name="."      │ (12 bytes)
├──────────────────────────────────────────────────────────┤
│ inode=5    rec_len=12  name_len=2  type=2  name=".."     │ (12 bytes)
├──────────────────────────────────────────────────────────┤
│ inode=42   rec_len=20  name_len=9  type=1  name="notes.t"│
│            (9 chars: n-o-t-e-s-.-t-x-t, +3 padding)     │ (20 bytes)
├──────────────────────────────────────────────────────────┤
│ inode=43   rec_len=16  name_len=5  type=1  name="video"  │ (16 bytes)
├──────────────────────────────────────────────────────────┤
│ inode=0    rec_len=4024  (deleted, spans to end of block)│
│ (deleted entries keep their rec_len, inode=0 means skip) │
└──────────────────────────────────────────────────────────┘
                              4096 bytes total
NOTE: Sum of all rec_len always equals block_size (4096).
      Deleted entries are "swallowed" by the previous entry's rec_len.
```

## 9.4 HTree (Hash-Indexed B-Tree) for Large Directories

When a directory has thousands of entries, linear search becomes O(n). ext4 uses an **HTree** — a B-tree indexed by **filename hash** — when the `dir_index` feature is enabled (it is, by default).

**What is a hash?** A hash function takes a string (filename) and produces a fixed-size integer (hash value). Files are sorted by their hash in the HTree.

```
HTree Structure:

Root block (one of the dir's data blocks):
┌──────────────────────────────────────────────────────────┐
│  "." and ".." entries (always at the very beginning)     │
├──────────────────────────────────────────────────────────┤
│  dx_root: (B-tree root node)                             │
│    hash_version: half-MD4                                │
│    indirect_levels: 0 (one level of indexing)           │
│    entries[]:                                            │
│      { hash=0x00000000, block=5 }  (leaf block)         │
│      { hash=0xAAAAAAAA, block=6 }  (leaf block)         │
│      { hash=0xEEEEEEEE, block=7 }  (leaf block)         │
└──────────────────────────────────────────────────────────┘

Leaf block 5 (sorted by hash):
  { inode=100, name="alice"    hash=0x1234 }
  { inode=200, name="bob"      hash=0x5678 }
  ...

Leaf block 6:
  { inode=300, name="charlie"  hash=0xBBBB }
  ...

Lookup of "bob":
  1. Hash("bob") = 0x5678
  2. Binary search root entries: 0x5678 > 0xAAAAAAAA? No → block 5
  3. Binary search leaf block 5 for hash 0x5678 → found entry
  4. Compare full name "bob" = "bob" → match! Return inode 200
  
Time complexity: O(log n) vs O(n) for linear
```

## 9.5 Directory Entry Parsing in C

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>

#define BLOCK_SIZE 4096

/* EXT4 directory entry */
struct ext4_dirent {
    uint32_t inode;
    uint16_t rec_len;
    uint8_t  name_len;
    uint8_t  file_type;
    char     name[256];  /* Padded to 256 for easy reading */
} __attribute__((packed));

const char *filetype_str(uint8_t ft) {
    switch(ft) {
        case 0: return "unknown";
        case 1: return "file";
        case 2: return "dir";
        case 3: return "chrdev";
        case 4: return "blkdev";
        case 5: return "fifo";
        case 6: return "socket";
        case 7: return "symlink";
        default: return "?";
    }
}

/*
 * Parse one block of directory entries.
 * block: pointer to 4096 bytes of directory data
 */
void parse_dir_block(const uint8_t *block) {
    const uint8_t *ptr = block;
    const uint8_t *end = block + BLOCK_SIZE;
    int entry_num = 0;

    printf("%-5s %-10s %-8s %s\n", "Idx", "Inode", "Type", "Name");
    printf("%-5s %-10s %-8s %s\n", "---", "-----", "----", "----");

    while (ptr < end) {
        /* Minimum entry size is 8 bytes (header only) */
        if (ptr + 8 > end) break;

        uint32_t inode   = *(uint32_t *)(ptr + 0);
        uint16_t rec_len = *(uint16_t *)(ptr + 4);
        uint8_t  name_len= *(uint8_t  *)(ptr + 6);
        uint8_t  file_type=*(uint8_t  *)(ptr + 7);

        /* Sanity checks */
        if (rec_len < 8 || rec_len > (end - ptr)) {
            fprintf(stderr, "Corrupt directory entry at offset %ld\n",
                    (long)(ptr - block));
            break;
        }

        if (inode != 0) {  /* inode=0 means deleted entry */
            char name[256] = {0};
            memcpy(name, ptr + 8, name_len > 255 ? 255 : name_len);
            printf("%-5d %-10u %-8s %s\n",
                   entry_num, inode, filetype_str(file_type), name);
            entry_num++;
        }

        /* Advance to next entry */
        ptr += rec_len;
    }
}

/*
 * To use this in practice:
 * 1. Read superblock to get block size and inode table location
 * 2. Read the inode for the directory (e.g., inode 2 for root)
 * 3. Follow the extent tree to get the first data block number
 * 4. Read that block and call parse_dir_block()
 */
int main(void) {
    /* Example: simulate a directory block */
    uint8_t block[BLOCK_SIZE];
    memset(block, 0, BLOCK_SIZE);

    /* Build test directory entries manually */
    uint8_t *ptr = block;
    uint16_t remaining = BLOCK_SIZE;

    /* Entry 1: "." */
    *(uint32_t*)(ptr)   = 2;   /* inode 2 (current dir) */
    *(uint16_t*)(ptr+4) = 12;  /* rec_len */
    *(uint8_t *)(ptr+6) = 1;   /* name_len */
    *(uint8_t *)(ptr+7) = 2;   /* type: dir */
    ptr[8] = '.';
    ptr += 12; remaining -= 12;

    /* Entry 2: ".." */
    *(uint32_t*)(ptr)   = 2;   /* parent = root = 2 */
    *(uint16_t*)(ptr+4) = 12;
    *(uint8_t *)(ptr+6) = 2;
    *(uint8_t *)(ptr+7) = 2;
    ptr[8] = '.'; ptr[9] = '.';
    ptr += 12; remaining -= 12;

    /* Entry 3: "notes.txt" */
    const char *name3 = "notes.txt";
    uint8_t nl3 = strlen(name3);
    uint16_t rl3 = (8 + nl3 + 3) & ~3;  /* round up to 4 */
    *(uint32_t*)(ptr)   = 42;
    *(uint16_t*)(ptr+4) = rl3;
    *(uint8_t *)(ptr+6) = nl3;
    *(uint8_t *)(ptr+7) = 1;  /* regular file */
    memcpy(ptr+8, name3, nl3);
    ptr += rl3; remaining -= rl3;

    /* Final entry: span the rest */
    *(uint32_t*)(ptr)   = 0;   /* Deleted/empty */
    *(uint16_t*)(ptr+4) = remaining;
    *(uint8_t *)(ptr+6) = 0;
    *(uint8_t *)(ptr+7) = 0;

    printf("Parsed directory block:\n");
    parse_dir_block(block);
    return 0;
}
```

---

# 10. The Journal (JBD2): Crash Safety

## 10.1 The Crash Safety Problem

Without journaling, consider what happens when you write a file:

```
Writing "hello.txt" (simplified steps):
  1. Find free inode → update inode bitmap
  2. Find free data blocks → update block bitmap
  3. Write data to data blocks
  4. Update inode (size, block pointers)
  5. Add directory entry

If power fails after step 3 but before step 4:
  - Data is written but inode doesn't know about it
  - Space is marked used but inode doesn't point to it
  - LEAK: those blocks are "allocated" but inaccessible
  - CORRUPTION: disk state is inconsistent
  
Without a journal: must run fsck (full disk scan) to find and fix all
inconsistencies. On a 4TB disk, fsck can take HOURS.
```

## 10.2 What is a Journal?

A **journal** is a **write-ahead log** (WAL): before making any change to the filesystem, we first write that change to a special log file (the journal). Once the journal entry is safe on disk, we apply the change. If we crash, on the next boot we **replay** the journal to complete interrupted operations.

**Write-Ahead Log principle**: Never modify the filesystem directly until you've written what you intend to do in the journal first.

```
Journal Flow:

Phase 1 — Write to journal:
  ┌──────────────┐         ┌────────────────────────────────┐
  │ "I intend to │──write──►  Journal (on disk):            │
  │ modify block │         │  [descriptor][block_copy][commit│]
  │ 42 (bitmap)" │         └────────────────────────────────┘
  └──────────────┘
  
Phase 2 — Apply change (after journal commit):
  ┌────────────────────────────┐    ┌──────────────────────────┐
  │ Journal: [committed ✓]    │────►│ Actual filesystem block 42│
  └────────────────────────────┘    └──────────────────────────┘

Phase 3 — Checkpoint (free journal space):
  Once block 42 is safely written to its real location,
  the journal entry for this transaction can be freed.
```

## 10.3 JBD2 (Journaling Block Device 2)

ext4 uses the **JBD2** (Journaling Block Device 2) subsystem, which is a generic journal layer usable by any filesystem (but only used by ext4 in practice).

The journal itself is stored as a **regular file** — inode 8 (the journal inode). This file lives on the same partition (or can be on a separate device for performance).

## 10.4 Journal Data Structures

```
Journal on disk (a circular log):

┌────────────┬──────────┬──────────┬──────────┬──────────────┐
│ Superblock │Transaction│Transaction│Transaction│  (free)     │
│ (journal)  │    T1    │    T2    │    T3    │              │
└────────────┴──────────┴──────────┴──────────┴──────────────┘

Each Transaction:
┌─────────────┬──────────────────────────────┬──────────────┐
│  Descriptor │  Data blocks (copies of      │  Commit block │
│   Block     │  filesystem blocks being     │  (signals     │
│  (JBD2_BH_ │  changed, in their new state)│   completion) │
│   DESCRIPTOR│                              │               │
└─────────────┴──────────────────────────────┴──────────────┘
```

### Journal Superblock

```c
typedef struct journal_superblock_s {
    /* Static information describing the journal */
    __be32 s_header;         /* Magic: 0xC03B3998 */
    __be32 s_blocktype;      /* Type: JBD2_SUPERBLOCK_V2 = 4 */
    __be32 s_sequence;       /* Current transaction sequence number */
    __be32 s_start;          /* Journal tail block number (oldest transaction) */
    __be32 s_errno;          /* Error from last failed commit */

    /* Version 2 additions */
    __be32 s_feature_compat;
    __be32 s_feature_incompat;
    __be32 s_feature_ro_compat;
    __u8   s_uuid[16];          /* Journal UUID */
    __be32 s_nr_users;          /* Number of filesystems using this journal */
    __be32 s_dynsuper;          /* Dynamic superblock block number */
    __be32 s_max_transaction;   /* Max blocks per transaction */
    __be32 s_max_trans_data;    /* Max data blocks per transaction */
    __u8   s_checksum_type;     /* Checksum type (CRC32c) */
    __be32 s_checksum;          /* Superblock checksum */
    __be32 s_head;              /* Journal head — next block to use */
} journal_superblock_t;
```

## 10.5 Journaling Modes

ext4 supports three journaling modes (set at mount time):

### 1. `journal` (full data journaling — safest, slowest)
```
What's journaled: BOTH metadata AND file data
Process:
  - Data blocks written to journal first
  - Then metadata
  - Then commit
  - Then everything written to real location
Overhead: Very high — every write goes to disk TWICE
Use when: Maximum data safety required (e.g., database logs)
```

### 2. `ordered` (DEFAULT — metadata journaling + data ordering)
```
What's journaled: Only metadata
Guarantee: Data blocks are written to disk BEFORE metadata is committed

Write order:
  1. Write new data to its final disk location (data blocks)
  2. Write metadata to journal  
  3. Commit journal
  4. Write metadata to real location

If crash between step 1 and 3:
  - Data is on disk (or partially written)
  - Journal replay will re-apply metadata (or not apply it)
  - Worst case: file appears empty/smaller (not corrupted)
  
This is why ext4 in "ordered" mode guarantees: you'll never see a file
with NEW metadata pointing to OLD data from a previous file that
happened to use those blocks.
```

### 3. `writeback` (metadata-only journaling — fastest, least safe)
```
What's journaled: Only metadata
No ordering guarantee between data and metadata writes!

Write order: Any order the I/O scheduler decides
If crash: Possible to see old garbage data in files
Use when: Performance critical, data can be regenerated
```

```
Journaling Mode Comparison:
                 journal     ordered     writeback
Safety           Highest     High        Medium
Throughput       Lowest      Good        Best
Data after crash Protected   Empty/trunc Possibly garbage
Metadata         Protected   Protected   Protected
```

## 10.6 Journal Transaction Lifecycle

```
Transaction lifecycle (state machine):

         RUNNING          LOCKED         FLUSH
┌─────────────────┐  ┌──────────┐  ┌──────────────┐
│  New operations │─►│  Close   │─►│  Write data  │
│  join here      │  │  to new  │  │  blocks (for │
│                 │  │  writes  │  │  ordered mode│
│  j_running_      │  └──────────┘  └──────────────┘
│  transaction    │                        │
└─────────────────┘                        ▼
                                   ┌──────────────┐   ┌──────────────┐
                                   │  Write       │──►│  COMMITTED   │
                                   │  metadata to │   │  (on journal)│
                                   │  journal +   │   └──────────────┘
                                   │  commit block│          │
                                   └──────────────┘          ▼
                                                    ┌──────────────────┐
                                                    │  CHECKPOINT      │
                                                    │  Write metadata  │
                                                    │  to real places  │
                                                    │  Free journal    │
                                                    └──────────────────┘
```

## 10.7 Crash Recovery

On mount, ext4 checks if the `s_state` field shows unclean shutdown. If so:

```
Recovery Process:
1. Read journal superblock → find s_start (tail) and s_head (head)
2. Scan from tail to head, reading each block
3. For each transaction:
   a. Read descriptor block → know which fs blocks are logged
   b. Read commit block → verify checksum → confirm this transaction completed
   c. If committed: replay all blocks (copy from journal to real location)
   d. If not committed: skip (transaction was incomplete, discard)
4. Update journal superblock: s_start = s_head (journal is empty)
5. Set s_state = clean
6. Done — mount succeeds

Time complexity: Only scan the journal (typically 64MB-1GB)
NOT the entire filesystem!
vs. ext2 fsck: Must scan every block of the entire disk
```

---

# 11. Linux VFS Layer: The Abstraction

## 11.1 What is VFS?

The **Virtual Filesystem Switch (VFS)** is a kernel abstraction layer that provides a **uniform interface** for all filesystem operations, regardless of the underlying filesystem type (ext4, xfs, btrfs, tmpfs, procfs, NFS, etc.).

```
User Space:
  open("file.txt", O_RDONLY)
        │
        ▼ (syscall: sys_open)
┌───────────────────────────────────────────────────────────┐
│                   VFS Layer (kernel)                       │
│                                                           │
│  ┌─────────────┐ ┌─────────────┐ ┌────────────────────┐  │
│  │ Path lookup │ │   Dentry    │ │  Inode operations  │  │
│  │ (namei.c)  │ │   cache     │ │  (file_operations) │  │
│  └─────────────┘ └─────────────┘ └────────────────────┘  │
└────────────────────────┬──────────────────────────────────┘
                         │ calls filesystem-specific methods
        ┌────────────────┼────────────────────┐
        ▼                ▼                    ▼
   ext4_ops          xfs_ops             tmpfs_ops
   (ext4/file.c)     (xfs/*)             (mm/shmem.c)
        │
        ▼
   Block layer → driver → disk
```

## 11.2 VFS Key Objects

### `struct super_block` — In-memory superblock

```c
struct super_block {
    struct list_head    s_list;          /* Keep this first */
    dev_t               s_dev;           /* Device identifier */
    unsigned char       s_blocksize_bits;
    unsigned long       s_blocksize;     /* Block size (bytes) */
    loff_t              s_maxbytes;      /* Max file size */
    struct file_system_type *s_type;     /* Filesystem type */
    const struct super_operations *s_op; /* Superblock methods */
    const struct dquot_operations *dq_op;
    const struct quotactl_ops *s_qcop;
    const struct export_operations *s_export_op;
    unsigned long       s_flags;         /* Mount flags */
    unsigned long       s_iflags;        /* Internal SB_I_* flags */
    unsigned long       s_magic;         /* Filesystem magic number */
    struct dentry       *s_root;         /* Directory mount point */
    struct rw_semaphore s_umount;        /* Unmount semaphore */
    int                 s_count;         /* Superblock ref count */
    atomic_t            s_active;        /* Active references */
    void                *s_security;     /* Security module */
    const struct xattr_handler * const *s_xattr;
    struct hlist_bl_head s_roots;        /* Alternate roots for NFS */
    struct list_head    s_mounts;        /* List of mounts */
    struct block_device *s_bdev;         /* Associated block device */
    struct backing_dev_info *s_bdi;      /* Writeback info */
    struct mtd_info     *s_mtd;          /* MTD device (flash) */
    struct hlist_node   s_instances;     /* Instances of this fs type */
    unsigned int        s_quota_types;   /* Quota types in use */
    struct quota_info   s_dquot;         /* Quota info */
    struct sb_writers   s_writers;       /* Pause writes */
    void                *s_fs_info;      /* Filesystem private info
                                          * ← For ext4: struct ext4_sb_info */
    u32                 s_time_gran;     /* Timestamp granularity (nsec) */
    s64                 s_time_min;
    s64                 s_time_max;
    /* ... many more fields ... */
};
```

### `struct inode` — In-memory inode

```c
struct inode {
    umode_t             i_mode;       /* File type + permissions */
    unsigned short      i_opflags;
    kuid_t              i_uid;
    kgid_t              i_gid;
    unsigned int        i_flags;      /* Filesystem flags */
    struct posix_acl    *i_acl;
    struct posix_acl    *i_default_acl;
    const struct inode_operations *i_op;  /* inode operations */
    struct super_block  *i_sb;        /* Superblock */
    struct address_space *i_mapping;  /* Page cache mapping */
    unsigned long       i_ino;        /* Inode number */
    union {
        const unsigned int i_nlink;   /* Hard link count */
        unsigned int __i_nlink;
    };
    dev_t               i_rdev;       /* Device (for dev files) */
    loff_t              i_size;       /* File size in bytes */
    struct timespec64   i_atime;
    struct timespec64   i_mtime;
    struct timespec64   i_ctime;
    spinlock_t          i_lock;
    unsigned short      i_bytes;      /* Bytes in last block */
    u8                  i_blkbits;    /* Log2 of block size */
    u8                  i_write_hint;
    blkcnt_t            i_blocks;     /* Blocks allocated (512-byte units) */
    unsigned long       i_state;      /* State flags */
    struct rw_semaphore i_rwsem;
    unsigned long       dirtied_when; /* When was this dirtied */
    unsigned long       dirtied_time_when;
    struct hlist_node   i_hash;       /* Hash table for fast lookup */
    struct list_head    i_io_list;    /* Writeback list */
    struct list_head    i_lru;        /* Inode LRU */
    struct list_head    i_sb_list;    /* Superblock's inode list */
    struct list_head    i_wb_list;    /* Writeback list */
    union {
        struct hlist_head    i_dentry;/* Dentry alias list */
        struct rcu_head      i_rcu;
    };
    atomic64_t          i_version;
    atomic64_t          i_sequence;
    atomic_t            i_count;      /* Reference count */
    atomic_t            i_dio_count;  /* Direct I/O count */
    atomic_t            i_writecount;
    union {
        const struct file_operations *i_fop; /* File ops */
        void (*free_inode)(struct inode *);
    };
    struct file_lock_context *i_flctx;
    struct address_space i_data;      /* Pages belonging to this file */
    struct list_head    i_devices;    /* Block/char device list */
    union {
        struct pipe_inode_info *i_pipe;
        struct cdev       *i_cdev;
        char              *i_link;     /* symlink target */
        unsigned          i_dir_seq;
    };
    __u32               i_generation;
    __u32               i_fsnotify_mask;
    void                *i_private;   /* ← ext4_inode_info stored here */
};
```

### `struct dentry` — Directory entry cache

```c
struct dentry {
    unsigned int        d_flags;         /* Dentry flags */
    seqcount_spinlock_t d_seq;           /* Sequence count for lockless reads */
    struct hlist_bl_node d_hash;         /* Lookup hash list */
    struct dentry       *d_parent;       /* Parent directory */
    struct qstr         d_name;          /* Name of this entry */
    struct inode        *d_inode;        /* Associated inode (NULL if negative) */
    unsigned char       d_iname[DNAME_INLINE_LEN]; /* Small name buffer */
    struct lockref      d_lockref;       /* Ref count + lock */
    const struct dentry_operations *d_op;
    struct super_block  *d_sb;           /* Filesystem superblock */
    unsigned long       d_time;          /* Time of last revalidation */
    void                *d_fsdata;       /* Filesystem-specific data */
    union {
        struct list_head d_lru;          /* LRU list */
        wait_queue_head_t *d_wait;       /* in-lookup wait queue */
    };
    struct list_head    d_child;         /* Child of parent list */
    struct list_head    d_subdirs;       /* Subdirectory list */
    union {
        struct hlist_node d_alias;       /* Inode alias list */
        struct hlist_bl_node d_in_lookup_hash;
        struct rcu_head   d_rcu;
    } d_u;
};
```

**Negative dentry**: A dentry for a filename that does NOT exist (cached to avoid repeated failed lookups).

### `struct file` — Open file instance

```c
struct file {
    union {
        struct llist_node   fu_llist;
        struct rcu_head     fu_rcuhead;
    } f_u;
    struct path         f_path;       /* Path (dentry + vfsmount) */
    struct inode        *f_inode;     /* Cached inode */
    const struct file_operations *f_op;  /* File operations */
    spinlock_t          f_lock;
    enum rw_hint        f_write_hint;
    atomic_long_t       f_count;      /* Reference count */
    unsigned int        f_flags;      /* O_RDONLY, O_NONBLOCK, etc. */
    fmode_t             f_mode;       /* FMODE_READ, FMODE_WRITE, etc. */
    struct mutex        f_pos_lock;
    loff_t              f_pos;        /* Current file offset (seek position) */
    struct fown_struct  f_owner;      /* For signal-based async I/O */
    const struct cred   *f_cred;      /* Credentials */
    struct file_ra_state f_ra;        /* Readahead state */
    u64                 f_version;
    void                *private_data; /* Filesystem/driver private */
    struct address_space *f_mapping;  /* Page cache */
    errseq_t            f_wb_err;     /* writeback error */
    errseq_t            f_sb_err;     /* Filesystem error */
};
```

## 11.3 VFS Operations (Function Pointer Tables)

VFS uses **function pointer tables** (like vtables in C++) to dispatch operations to the right filesystem:

```c
/* Superblock operations — filesystem-level */
struct super_operations {
    struct inode *(*alloc_inode)(struct super_block *sb);
    void (*destroy_inode)(struct inode *);
    void (*free_inode)(struct inode *);
    void (*dirty_inode)(struct inode *, int flags);
    int  (*write_inode)(struct inode *, struct writeback_control *wbc);
    int  (*drop_inode)(struct inode *);
    void (*evict_inode)(struct inode *);
    void (*put_super)(struct super_block *);
    int  (*sync_fs)(struct super_block *sb, int wait);
    int  (*freeze_super)(struct super_block *);
    int  (*freeze_fs)(struct super_block *);
    int  (*thaw_super)(struct super_block *);
    int  (*unfreeze_fs)(struct super_block *);
    int  (*statfs)(struct dentry *, struct kstatfs *);
    int  (*remount_fs)(struct super_block *, int *, char *);
    void (*umount_begin)(struct super_block *);
    /* ... */
};

/* Inode operations */
struct inode_operations {
    struct dentry *(*lookup)(struct inode *, struct dentry *, unsigned int);
    const char *(*get_link)(struct dentry *, struct inode *, struct delayed_call *);
    int (*permission)(struct user_namespace *, struct inode *, int);
    struct posix_acl * (*get_acl)(struct inode *, int, bool);
    int (*readlink)(struct dentry *, char __user *, int);
    int (*create)(struct user_namespace *, struct inode *, struct dentry *,
                  umode_t, bool);
    int (*link)(struct dentry *, struct inode *, struct dentry *);
    int (*unlink)(struct inode *, struct dentry *);
    int (*symlink)(struct user_namespace *, struct inode *, struct dentry *,
                   const char *);
    int (*mkdir)(struct user_namespace *, struct inode *, struct dentry *,
                 umode_t);
    int (*rmdir)(struct inode *, struct dentry *);
    int (*mknod)(struct user_namespace *, struct inode *, struct dentry *,
                 umode_t, dev_t);
    int (*rename)(struct user_namespace *, struct inode *, struct dentry *,
                  struct inode *, struct dentry *, unsigned int);
    int (*setattr)(struct user_namespace *, struct dentry *, struct iattr *);
    int (*getattr)(struct user_namespace *, const struct path *, struct kstat *,
                   u32, unsigned int);
    /* ... */
};

/* File operations — per-open-file operations */
struct file_operations {
    struct module *owner;
    loff_t (*llseek)(struct file *, loff_t, int);
    ssize_t (*read)(struct file *, char __user *, size_t, loff_t *);
    ssize_t (*write)(struct file *, const char __user *, size_t, loff_t *);
    ssize_t (*read_iter)(struct kiocb *, struct iov_iter *);
    ssize_t (*write_iter)(struct kiocb *, struct iov_iter *);
    int (*iopoll)(struct kiocb *kiocb, struct io_comp_batch *,
                  unsigned int flags);
    int (*iterate)(struct file *, struct dir_context *);
    int (*iterate_shared)(struct file *, struct dir_context *);
    __poll_t (*poll)(struct file *, struct poll_table_struct *);
    long (*unlocked_ioctl)(struct file *, unsigned int, unsigned long);
    long (*compat_ioctl)(struct file *, unsigned int, unsigned long);
    int (*mmap)(struct file *, struct vm_area_struct *);
    int (*open)(struct inode *, struct file *);
    int (*flush)(struct file *, fl_owner_t id);
    int (*release)(struct inode *, struct file *);
    int (*fsync)(struct file *, loff_t, loff_t, int datasync);
    int (*fasync)(int, struct file *, int);
    /* ... */
};
```

## 11.4 Path Resolution (namei): How open("/home/user/file.txt") Works

```
Path: "/home/user/file.txt"

Step 1: Start at root dentry (inode 2, always the root)
  current_dir = root_dentry

Step 2: Look up "home" in current_dir
  - Check dentry cache first (in-RAM cache of recent lookups)
  - If not cached: read directory data blocks for root inode
  - Parse directory entries looking for "home"
  - Found: inode 100 for "home"
  - Create/update dentry: {name="home", inode=100, parent=root}

Step 3: Check permissions — can we enter "home"? (execute bit on dir)
  - Read inode 100's i_mode, compare with current uid/gid
  - OK: proceed

Step 4: Look up "user" in inode 100's directory
  - Similar process → inode 200

Step 5: Look up "file.txt" in inode 200's directory
  - → inode 300

Step 6: Return inode 300 — that's our file!

Dentry cache (dcache) optimization:
  Linux caches every successfully resolved dentry in a hash table.
  Next time open("/home/user/file.txt") is called:
  - Step 2: "home" found in dcache → skip disk read
  - Step 4: "user" found in dcache → skip disk read
  - Step 5: "file.txt" found in dcache → skip disk read
  - Go directly to inode 300!
  - Zero disk I/O for path resolution on warm cache!
```

---

# 12. Page Cache & Buffer Cache

## 12.1 What is the Page Cache?

The **page cache** is a region of RAM where the kernel caches disk data. When you read a file, the kernel reads it into the page cache (4KB pages), and subsequent reads hit RAM instead of disk.

```
Physical RAM layout (simplified):
┌───────────────────────────────────────────────────────────────┐
│                        System RAM (e.g., 16GB)                │
├──────────────────┬────────────────────────────────────────────┤
│  Kernel code +   │             Page Cache                     │
│  data structures │  ┌──────┬──────┬──────┬──────┬──────┐     │
│  (~256MB)        │  │page 0│page 1│page 2│page 3│ ...  │     │
│                  │  │file A│file A│file B│file A│      │     │
│                  │  │off 0 │off 4K│off 0 │off 8K│      │     │
│                  │  └──────┴──────┴──────┴──────┴──────┘     │
│  Process memory  │  (grows to fill available RAM)             │
│  (stack, heap,   │  (evicted using LRU when RAM is needed)   │
│   code, mmap)    │                                            │
└──────────────────┴────────────────────────────────────────────┘
```

## 12.2 The address_space Object

Each inode has an **address_space** (`i_mapping`) that manages its pages in the page cache:

```c
struct address_space {
    struct inode        *host;            /* Owner inode */
    struct xarray       i_pages;          /* Cached pages (radix tree of pages) */
    struct rw_semaphore invalidate_lock;
    gfp_t               gfp_mask;         /* Allocation flags for new pages */
    atomic_t            i_mmap_writable;  /* Count of writable mmap's */
    struct rb_root_cached i_mmap;         /* Tree of mmap'd areas */
    struct rw_semaphore i_mmap_rwsem;
    unsigned long       nrpages;          /* Number of pages in cache */
    unsigned long       nrexceptional;    /* Shadow/swap entries */
    pgoff_t             writeback_index;  /* Writeback start offset */
    const struct address_space_operations *a_ops; /* Operations */
    unsigned long       flags;            /* Error bits/flags */
    struct wb_lock_cookie i_pages_lock_cookie;
    errseq_t            wb_err;           /* Writeback error */
    spinlock_t          private_lock;
    struct list_head    private_list;     /* For use by address_space */
    void                *private_data;
};
```

## 12.3 Reading Through the Page Cache

```
read(fd, buf, 4096) system call flow:

User Process
    │
    ▼
sys_read()  → vfs_read() → ext4_file_read_iter()
    │
    ▼
generic_file_read_iter():
    │
    ├── Look up page in address_space's i_pages (XArray/radix tree)
    │   ├── Page FOUND in cache → copy to user buffer → DONE (fast path!)
    │   └── Page NOT FOUND → page fault/cache miss
    │           │
    │           ▼
    │       Allocate new page (struct page / struct folio)
    │           │
    │           ▼
    │       ext4_readpage() or ext4_readahead()
    │           │
    │           ▼
    │       ext4_mpage_readpages()
    │           │
    │           ▼
    │       Look up extent → find physical block number
    │           │
    │           ▼
    │       submit_bio() → Block layer → Disk driver → Read from disk
    │           │
    │           ▼ (I/O completion interrupt)
    │       Page marked uptodate, inserted into page cache
    │           │
    │           ▼
    │       Copy page data to user buffer
    │
    ▼
Return bytes_read to process
```

## 12.4 Buffer Cache vs Page Cache

Historically, Linux had two separate caches:
- **Buffer cache**: Cached raw disk blocks (metadata, superblock, etc.)
- **Page cache**: Cached file data pages

Modern Linux (since ~2.4) **unified** these. Everything goes through the page cache. Block device buffers are stored as pages in the block device's own address_space.

## 12.5 struct page / struct folio

Every 4KB page in the page cache is described by a `struct page` (or the newer `struct folio` for multi-page units):

```c
struct page {
    unsigned long   flags;       /* Atomic flags: PG_uptodate, PG_dirty, PG_locked, ... */
    union {
        struct { /* Page cache pages */
            struct address_space *mapping; /* File this page belongs to */
            pgoff_t index;                 /* Offset within file (in pages) */
            unsigned long private;
        };
        /* ... other uses ... */
    };
    atomic_t        _refcount;   /* Reference count */
    atomic_t        _mapcount;   /* Number of page table entries mapping this page */
    /* ... */
};

/* Key page flags: */
/* PG_uptodate: page has valid data (read from disk or written) */
/* PG_dirty:    page has been modified, needs writeback */
/* PG_locked:   page is locked (being read from disk or written) */
/* PG_writeback: page is currently being written back */
/* PG_lru:      page is on an LRU list */
/* PG_referenced: page has been recently accessed */
/* PG_active:   page is on the active LRU list */
```

---

# 13. Writeback & Dirty Pages

## 13.1 The Write Path

When a process writes data, it doesn't go directly to disk. Instead:

1. Data is written to a page in the page cache
2. Page is marked **dirty** (`PG_dirty` flag set)
3. The inode is added to the writeback list
4. A background kernel thread (**kworker/flush**) eventually writes dirty pages to disk

```
write(fd, data, size) flow:

User data
    │
    ▼
generic_perform_write()
    │
    ├── grab_cache_page_write_begin() — get/allocate page in page cache
    │
    ├── copy data from user buffer → page
    │
    ├── mark page dirty (set_page_dirty())
    │   → marks inode as dirty
    │   → adds inode to per-BDI (Backing Device Info) dirty list
    │
    └── return to user (write() returns immediately — data is in RAM!)

Later (asynchronously):
    kworker/u:N-flush thread wakes up:
    ├── For each dirty inode:
    │   ├── call ext4_writepages()
    │   ├── Allocate actual disk blocks (extent allocation)
    │   ├── Submit bio (block I/O) to block layer
    │   └── On completion: mark pages clean (PG_dirty cleared)
    └── Update inode on disk (write_inode)
```

## 13.2 Dirty Page Limits and Thresholds

The kernel throttles writes to prevent RAM from filling with dirty pages:

```
/proc/sys/vm/dirty_ratio         = 20  (20% of total RAM)
/proc/sys/vm/dirty_background_ratio = 10  (10% of total RAM)
/proc/sys/vm/dirty_expire_centisecs = 3000  (30 seconds)
/proc/sys/vm/dirty_writeback_centisecs = 500  (5 seconds)

Behavior:
  dirty pages < dirty_background_ratio (10%):
    → kflushd writes lazily in background

  dirty pages > dirty_background_ratio:
    → kflushd kicks in aggressively

  dirty pages > dirty_ratio (20%):
    → Writing processes are THROTTLED (blocked until dirty pages decrease)
    
  page older than dirty_expire_centisecs (30s):
    → Must be written back regardless of dirty ratio

Writeback interval:
  kflushd wakes every dirty_writeback_centisecs (5s) to check for old dirty pages
```

## 13.3 fsync(): Forcing Dirty Data to Disk

```c
/* User space: fsync() forces all dirty data for this file to disk */
fsync(fd);

/* Kernel path: */
/* sys_fsync() → vfs_fsync() → ext4_sync_file() */

int ext4_sync_file(struct file *file, loff_t start, loff_t end, int datasync) {
    struct inode *inode = file->f_mapping->host;
    
    /* 1. Flush dirty pages to disk (data blocks) */
    ret = file_write_and_wait_range(file, start, end);
    
    /* 2. If not datasync, also write inode metadata */
    if (!datasync || ext4_should_journal_data(inode)) {
        /* Write inode to disk */
        ret = ext4_write_inode(inode, &wbc);
    }
    
    /* 3. Commit the journal to ensure durability */
    ret = jbd2_complete_transaction(journal, commit_tid);
    
    /* After fsync() returns, data is on non-volatile storage */
    return ret;
}
```

---

# 14. Delayed Allocation (delalloc)

## 14.1 The Problem delalloc Solves

In ext3 (without delalloc), when a process writes a byte to a file:
1. A disk block is immediately allocated (reserving it)
2. The data is written to the page cache
3. Later, the data is written to that pre-allocated block

**Problem**: If a process writes 10MB in tiny 1-byte chunks, we allocate blocks one at a time. The filesystem doesn't know the final size, so it can't place blocks optimally. Result: heavy fragmentation.

## 14.2 How delalloc Works

With **delayed allocation** (default in ext4):
1. When a process writes, blocks are **NOT immediately allocated**
2. Data goes into the page cache, marked dirty
3. A **reservation** is tracked in RAM (saying "this inode will need ~N blocks")
4. Block allocation happens at **writeback time** (when dirty pages are flushed)
5. At writeback time, the allocator knows the full extent of data to write → can allocate one large, contiguous extent!

```
Without delalloc:
  write 1 byte  → allocate block A
  write 1 byte  → allocate block B (might not be adjacent to A!)
  write 1 byte  → allocate block C
  ...1000 writes → 1000 separate blocks, fragmented!

With delalloc:
  write 1 byte  → no allocation (mark page dirty)
  write 1 byte  → no allocation (page already dirty)
  write 1 byte  → no allocation
  ...1000 writes → all in same page/set of pages
  
  Writeback time:
    → "This inode needs 4MB of contiguous space"
    → Allocate blocks 50000–51023 (all contiguous)
    → Write all 4MB at once with one sequential disk operation
```

## 14.3 The Mmap/Reservation System

ext4 maintains a **block reservation window** for each inode with delayed allocation:

```c
/* From ext4's private inode info */
struct ext4_inode_info {
    /* ... many fields ... */
    
    /* Delayed allocation */
    atomic_t            i_prealloc_list_lock;
    struct list_head    i_prealloc_list;     /* List of prealloc spaces */
    
    /* Per-inode block reservation */
    unsigned long       i_reserved_data_blocks; /* Reserved (not yet allocated) */
    
    /* Preallocation for small files */
    struct ext4_prealloc_space *i_pb; /* inode-level prealloc */
    
    /* ... */
};
```

## 14.4 Bigalloc: Cluster Allocation

With the `bigalloc` feature, ext4 allocates in **clusters** (e.g., 16 blocks = 64KB) instead of individual 4KB blocks. This reduces:
- Bitmap overhead (1 bit per cluster instead of per block)
- Fragmentation for large files
- Number of extents needed

```
Normal allocation:
  Allocate 100 blocks → 100 bitmap bits, up to 100 extents

Bigalloc (cluster_size=16):
  Allocate 100 blocks = 7 clusters (rounded up)
  → 7 bitmap bits (one per cluster)
  → 1-7 extents (clusters are contiguous)
```

---

# 15. Disk I/O Schedulers & Block Layer

## 15.1 The Block Layer Stack

```
ext4 → submit_bio(bio)
           │
           ▼
       Block Layer:
       ┌─────────────────────────────────────────────────────┐
       │  1. I/O Scheduler (reorders/merges requests)        │
       │     - mq-deadline (default for HDDs)                │
       │     - kyber (NVMe SSDs)                             │
       │     - bfq (desktop fairness)                        │
       │     - none (passthrough — no reordering)            │
       │  2. Request queue                                    │
       │  3. Multi-queue (blk-mq) → per-CPU queues           │
       └─────────────────────────────────────────────────────┘
           │
           ▼
       Device Driver (SCSI, NVMe, virtio-blk...)
           │
           ▼
       Hardware (HDD, SSD, NVME controller)
```

## 15.2 struct bio — Block I/O Request

The **bio** (block I/O) structure is the unit of work passed to the block layer:

```c
struct bio {
    struct bio          *bi_next;    /* Request queue link */
    struct block_device *bi_bdev;    /* Target block device */
    blk_opf_t           bi_opf;     /* Operation (READ/WRITE) + flags */
    unsigned short      bi_flags;    /* Status + command flags */
    unsigned short      bi_ioprio;   /* I/O priority */
    blk_status_t        bi_status;   /* Completion status */
    atomic_t            __bi_remaining; /* Reference count for chaining */
    struct bvec_iter    bi_iter;     /* Current position in bio_vec */
    bio_end_io_t        *bi_end_io;  /* Completion callback */
    void                *bi_private; /* Private data for bi_end_io */
    struct blkcg_gq     *bi_blkg;    /* Block cgroup association */
    struct bio_issue    bi_issue;
    u64                 bi_iocost_cost;
    struct bio_crypt_ctx *bi_crypt_context; /* Encryption context */
    union { /* ... */ };
    struct bio_vec      *bi_io_vec;  /* Array of page vectors */
    struct bio_set      *bi_pool;    /* Memory pool */
    struct bio_vec      bi_inline_vecs[]; /* Inline page vectors (small bios) */
};

/* bio_vec: one segment of a scatter-gather I/O */
struct bio_vec {
    struct page *bv_page;   /* Page in page cache */
    unsigned int bv_len;    /* Length to transfer */
    unsigned int bv_offset; /* Offset within page */
};
```

## 15.3 I/O Schedulers Explained

### mq-deadline (for HDDs)
Ensures all requests complete within a **deadline**, preventing starvation:
```
Two queues:
  - Read FIFO (deadline: 500ms by default)
  - Write FIFO (deadline: 5000ms by default)

Algorithm:
  Normally dispatch requests in sorted order (elevator style)
  If any request's deadline is about to expire → dispatch it first
```

### kyber (for NVMe/fast SSDs)
Token-bucket based scheduler for low-latency storage:
```
Two queues:
  - Sync reads (latency target: 2ms)
  - Other (latency target: 10ms)
  
Issues tokens based on latency feedback — self-tunes
```

### bfq (Budget Fair Queuing)
Proportional-share scheduler for desktop fairness:
```
Assigns "budgets" (number of sectors) to processes
Gives each process a fair share of I/O bandwidth
Great for desktop responsiveness (prevents one process from monopolizing disk)
```

---

# 16. ext4 Kernel Data Structures (C Deep Dive)

## 16.1 ext4's Private Superblock Info

ext4 extends the generic VFS `super_block` with its own `ext4_sb_info`:

```c
/*
 * Fourth extended filesystem super-block data in memory
 * Stored in sb->s_fs_info
 */
struct ext4_sb_info {
    unsigned long s_desc_size;         /* Size of group descriptor */
    unsigned long s_inodes_per_block;  /* Inodes per block */
    unsigned long s_blocks_per_group;  /* Blocks per group */
    unsigned long s_clusters_per_group;
    unsigned long s_inodes_per_group;  /* Inodes per group */
    unsigned long s_itb_per_group;     /* Inode table blocks per group */
    unsigned long s_gdb_count;         /* Number of group descriptor blocks */
    unsigned long s_desc_per_block;    /* Group descriptors per block */
    ext4_group_t  s_groups_count;      /* Number of block groups */
    ext4_group_t  s_blockfile_groups;  /* Groups for block file */
    unsigned long s_overhead;          /* Overhead (superblock + GDT) */
    unsigned int  s_cluster_ratio;     /* Blocks per cluster */
    unsigned int  s_cluster_bits;      /* Log2 of cluster ratio */
    loff_t        s_bitmap_maxbytes;   /* Max bytes in partial stride */
    struct buffer_head *s_sbh;         /* Buffer containing the super block */
    struct ext4_super_block *s_es;     /* Pointer to on-disk superblock */
    struct buffer_head * __rcu *s_group_desc; /* GDT buffer heads */
    unsigned int  s_mount_opt;         /* Mount options bitmap */
    unsigned int  s_mount_opt2;
    unsigned long s_mount_flags;
    unsigned int  s_def_mount_opt;
    ext4_fsblk_t  s_sb_block;
    atomic64_t    s_resv_clusters;     /* Reserved clusters for root */
    kuid_t        s_resuid;            /* User allowed to use reserved blocks */
    kgid_t        s_resgid;
    unsigned short s_mount_state;      /* Mount state (flags) */
    unsigned short s_pad;
    int           s_addr_per_block_bits;
    int           s_desc_per_block_bits;
    int           s_inode_size;        /* Size of inode in bytes */
    int           s_first_ino;         /* First non-reserved inode */
    spinlock_t    s_next_gen_lock;
    u32           s_next_generation;
    u32           s_hash_seed[4];      /* HTREE hash seed */
    int           s_def_hash_version;
    int           s_hash_unsigned;
    struct percpu_counter s_freeclusters_counter;
    struct percpu_counter s_freeinodes_counter;
    struct percpu_counter s_dirs_counter;
    struct percpu_counter s_dirtyclusters_counter;
    struct percpu_counter s_sra_exceeded_retry_limit;
    struct blockgroup_lock *s_blockgroup_lock;
    struct proc_dir_entry *s_proc;
    struct kobject s_kobj;
    struct completion s_kobj_unregister;
    struct super_block *s_sb;          /* VFS super block */
    struct buffer_head *s_mmp_bh;      /* Buffer for MMP block */
    struct journal_s *s_journal;       /* ← JBD2 journal handle */
    struct list_head s_orphan;         /* Orphan inode list */
    struct mutex    s_orphan_lock;
    unsigned long   s_commit_interval; /* Commit interval (jiffies) */
    u32             s_max_batch_time;
    u32             s_min_batch_time;
    struct block_device *s_journal_bdev;
    char            *s_qf_names[EXT4_MAXQUOTAS];
    int             s_jquota_fmt;
    /* ... many more fields ... */
    
    /* Multi-block allocator */
    struct ext4_group_info *** s_group_info; /* Per-group info for mballoc */
    struct inode   *s_buddy_cache;           /* Buddy bitmap inode */
    spinlock_t     s_md_lock;
    unsigned short *s_mb_offsets;
    unsigned int   *s_mb_maxs;
    unsigned int    s_group_info_size;
    unsigned int    s_mb_free_pending;
    struct list_head s_freed_data_list;      /* Freed data after tx commit */
    /* ... */
};
```

## 16.2 ext4's Private Inode Info

```c
/*
 * fourth extended file system inode data in memory
 * Stored in inode->i_private (as ei = EXT4_I(inode))
 */
struct ext4_inode_info {
    __le32          i_data[15];      /* On-disk block map / extent root */
    __u32           i_dtime;         /* Deletion time */
    ext4_fsblk_t    i_file_acl;      /* Extended attribute block */
    
    /*
     * i_block_group is the number of the block group which contains
     * this file's inode. Constant across the life of the inode, set
     * on inode creation.
     */
    ext4_group_t    i_block_group;
    ext4_lblk_t     i_dir_start_lookup;
    
    /* Block reservation info */
    struct list_head i_prealloc_list;
    spinlock_t       i_prealloc_lock;
    
    /* Extent status tree */
    struct ext4_es_tree i_es_tree;    /* Cached extent status */
    rwlock_t            i_es_lock;
    struct list_head    i_es_list;
    unsigned int        i_es_all_nr;  /* Nr of entries in status tree */
    unsigned int        i_es_shk_nr;
    ext4_lblk_t         i_es_shrink_lblk; /* Shrink hint */
    
    /* inode location info */
    struct ext4_iloc    i_iloc;       /* Block/offset of disk inode */
    
    /* Transactions */
    unsigned long       i_sync_tid;   /* Last sync transaction ID */
    unsigned long       i_datasync_tid;
    
    /* Journaling */
    struct jbd2_inode   *jinode;      /* JBD2 inode info */
    spinlock_t          i_block_reservation_lock;
    tid_t               i_reserved_data_blocks;
    
    /* Large directory / htree */
    struct rw_semaphore xattr_sem;    /* For extended attributes */
    
    /* Inline data */
    spinlock_t          i_raw_lock;   /* Protect raw inode */
    
    struct list_head    i_orphan;     /* Orphan inode list */
    
    /* Timestamps (extra bits for nanosecond precision) */
    __u32               i_crtime;        /* Creation time (sec) */
    __u32               i_crtime_extra;  /* Creation time (nsec) */
    __u32               i_ctime_extra;
    __u32               i_mtime_extra;
    __u32               i_atime_extra;
    
    /* Encryption */
    struct fscrypt_info *i_crypt_info;
    
    /* Misc */
    __u32               i_projid;     /* Project ID */
    struct inode        vfs_inode;    /* ← VFS inode MUST be LAST */
};

/* Macro to get ext4_inode_info from a VFS inode */
static inline struct ext4_inode_info *EXT4_I(struct inode *inode) {
    return container_of(inode, struct ext4_inode_info, vfs_inode);
}
/*
 * container_of(ptr, type, member):
 *   Given a pointer to a struct member, get pointer to the containing struct
 *   Works because vfs_inode is at a FIXED offset within ext4_inode_info
 */
```

## 16.3 The Multi-Block Allocator (mballoc)

ext4's block allocator (in `fs/ext4/mballoc.c`) uses a **buddy system** for free space management within each block group:

```
Buddy system for a block group (32768 blocks):

Order 0: Individual blocks (tracks runs of 1 block)
Order 1: Pairs of blocks (runs of 2)
Order 2: Quads (runs of 4)
...
Order 13: Runs of 8192 blocks
Order 14: Run of 16384 blocks  
Order 15: Run of 32768 (whole group)

Each order has a bitmap tracking which runs of that size are free.

Allocation of 64 contiguous blocks:
  → Look at order 6 (runs of 64)
  → Find first free run of 64 blocks
  → Mark as used
  → Return start block number

If no run of 64 exists:
  → Look at order 7 (runs of 128)
  → Find first free, split into 64+64
  → Use first half, put second half in order 6 free list
```

This gives O(log N) allocation time for any power-of-2 size request.

---

# 17. Rust-Level Filesystem Concepts

## 17.1 Reading a Superblock in Rust

```rust
//! ext4 superblock reader in Rust
//! Demonstrates zero-copy parsing and type-safe field access

use std::fs::File;
use std::io::{self, Read, Seek, SeekFrom};
use std::fmt;

// ─── Constants ────────────────────────────────────────────────────────────────

const EXT4_SUPER_MAGIC: u16 = 0xEF53;
const SUPERBLOCK_OFFSET: u64 = 1024;

// ─── On-disk structure (repr(C, packed) for exact binary layout) ──────────────

/// Minimal ext4 superblock structure for reading.
/// `repr(C)` ensures C-compatible field ordering.
/// `packed` ensures no padding bytes are inserted.
#[repr(C, packed)]
#[derive(Debug, Clone, Copy)]
struct Ext4SuperblockRaw {
    s_inodes_count:       u32,
    s_blocks_count_lo:    u32,
    s_r_blocks_count_lo:  u32,
    s_free_blocks_count_lo: u32,
    s_free_inodes_count:  u32,
    s_first_data_block:   u32,
    s_log_block_size:     u32,  // block_size = 1024 << this
    s_log_cluster_size:   u32,
    s_blocks_per_group:   u32,
    s_clusters_per_group: u32,
    s_inodes_per_group:   u32,
    s_mtime:              u32,
    s_wtime:              u32,
    s_mnt_count:          u16,
    s_max_mnt_count:      u16,
    s_magic:              u16,  // Must be EXT4_SUPER_MAGIC = 0xEF53
    s_state:              u16,
    s_errors:             u16,
    s_minor_rev_level:    u16,
    s_lastcheck:          u32,
    s_checkinterval:      u32,
    s_creator_os:         u32,
    s_rev_level:          u32,
    s_def_resuid:         u16,
    s_def_resgid:         u16,
    // Rev 1 fields
    s_first_ino:          u32,
    s_inode_size:         u16,
    s_block_group_nr:     u16,
    s_feature_compat:     u32,
    s_feature_incompat:   u32,
    s_feature_ro_compat:  u32,
    s_uuid:               [u8; 16],
    s_volume_name:        [u8; 16],
    // ... remaining fields (we read 1024 bytes but only decode this much)
}

// ─── High-level parsed superblock ────────────────────────────────────────────

#[derive(Debug)]
struct Superblock {
    block_size:        u32,
    total_blocks:      u64,
    free_blocks:       u32,
    total_inodes:      u32,
    free_inodes:       u32,
    blocks_per_group:  u32,
    inodes_per_group:  u32,
    inode_size:        u16,
    uuid:              [u8; 16],
    volume_name:       String,
    mount_count:       u16,
    state:             FsState,
    rev_level:         u32,
    num_block_groups:  u32,
    // Feature flags
    has_extents:       bool,
    has_64bit:         bool,
    has_flex_bg:       bool,
    has_metadata_csum: bool,
}

#[derive(Debug)]
enum FsState {
    Clean,
    HasErrors,
    Unknown(u16),
}

impl fmt::Display for FsState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FsState::Clean => write!(f, "clean"),
            FsState::HasErrors => write!(f, "errors detected"),
            FsState::Unknown(v) => write!(f, "unknown ({})", v),
        }
    }
}

// ─── Error type ───────────────────────────────────────────────────────────────

#[derive(Debug)]
enum Ext4Error {
    Io(io::Error),
    BadMagic(u16),
    InvalidBlockSize(u32),
}

impl fmt::Display for Ext4Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Ext4Error::Io(e) => write!(f, "I/O error: {}", e),
            Ext4Error::BadMagic(m) => {
                write!(f, "Invalid magic number: 0x{:04x} (expected 0x{:04x})",
                       m, EXT4_SUPER_MAGIC)
            }
            Ext4Error::InvalidBlockSize(s) => write!(f, "Invalid block size: {}", s),
        }
    }
}

impl From<io::Error> for Ext4Error {
    fn from(e: io::Error) -> Self {
        Ext4Error::Io(e)
    }
}

// ─── Core parsing logic ───────────────────────────────────────────────────────

fn read_superblock(path: &str) -> Result<Superblock, Ext4Error> {
    let mut file = File::open(path)?;

    // Seek to byte 1024 (superblock always lives here)
    file.seek(SeekFrom::Start(SUPERBLOCK_OFFSET))?;

    // Read 1024 bytes into a raw byte array
    // We use a fixed-size buffer to read the on-disk structure
    let raw_size = std::mem::size_of::<Ext4SuperblockRaw>();
    let mut buf = vec![0u8; 1024]; // full superblock is 1024 bytes
    file.read_exact(&mut buf)?;

    // Safety: We verify the magic number before using any fields.
    // The buffer is exactly the right size and alignment for u8 reads.
    // We use read_unaligned for all accesses due to #[repr(packed)].
    
    // Read magic (at offset 56 from start of superblock)
    let magic_offset = 56; // Byte offset of s_magic within the struct
    let magic = u16::from_le_bytes([buf[magic_offset], buf[magic_offset + 1]]);
    
    if magic != EXT4_SUPER_MAGIC {
        return Err(Ext4Error::BadMagic(magic));
    }

    // Parse all fields using little-endian byte reads (ext4 is always LE)
    let read_u32 = |off: usize| u32::from_le_bytes(buf[off..off+4].try_into().unwrap());
    let read_u16 = |off: usize| u16::from_le_bytes(buf[off..off+2].try_into().unwrap());

    let log_block_size  = read_u32(24);
    let block_size = 1024u32.checked_shl(log_block_size)
        .ok_or(Ext4Error::InvalidBlockSize(log_block_size))?;

    let blocks_count_lo = read_u32(4);
    let total_blocks    = blocks_count_lo as u64; // simplified (ignore high bits)

    let blocks_per_group = read_u32(32);
    let inodes_per_group = read_u32(40);
    let total_inodes     = read_u32(0);

    let num_block_groups = total_blocks
        .saturating_add(blocks_per_group as u64 - 1)
        / blocks_per_group as u64;

    // UUID: 16 bytes at offset 104
    let mut uuid = [0u8; 16];
    uuid.copy_from_slice(&buf[104..120]);

    // Volume name: 16 bytes at offset 120 (null-terminated)
    let name_bytes = &buf[120..136];
    let name_end   = name_bytes.iter().position(|&b| b == 0).unwrap_or(16);
    let volume_name = String::from_utf8_lossy(&name_bytes[..name_end]).into_owned();

    let state = match read_u16(58) {
        1 => FsState::Clean,
        2 => FsState::HasErrors,
        v => FsState::Unknown(v),
    };

    // Feature flags at offsets 92 (compat), 96 (incompat), 100 (ro_compat)
    let feature_incompat  = read_u32(96);
    let feature_ro_compat = read_u32(100);

    Ok(Superblock {
        block_size,
        total_blocks,
        free_blocks:      read_u32(12),
        total_inodes,
        free_inodes:      read_u32(16),
        blocks_per_group,
        inodes_per_group,
        inode_size:       read_u16(88),
        uuid,
        volume_name,
        mount_count:      read_u16(52),
        state,
        rev_level:        read_u32(76),
        num_block_groups: num_block_groups as u32,
        has_extents:      feature_incompat & 0x0040 != 0,
        has_64bit:        feature_incompat & 0x0080 != 0,
        has_flex_bg:      feature_incompat & 0x0200 != 0,
        has_metadata_csum:feature_ro_compat & 0x0400 != 0,
    })
}

fn format_uuid(uuid: &[u8; 16]) -> String {
    format!(
        "{:02x}{:02x}{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}",
        uuid[0], uuid[1], uuid[2],  uuid[3],
        uuid[4], uuid[5],
        uuid[6], uuid[7],
        uuid[8], uuid[9],
        uuid[10],uuid[11],uuid[12], uuid[13], uuid[14], uuid[15]
    )
}

fn print_superblock(sb: &Superblock) {
    let total_mb = sb.total_blocks as u64 * sb.block_size as u64 / (1024 * 1024);
    
    println!("╔══════════════════════════════════════════╗");
    println!("║         EXT4 Superblock Information      ║");
    println!("╚══════════════════════════════════════════╝");
    println!("  UUID:              {}", format_uuid(&sb.uuid));
    println!("  Volume name:       {:?}", sb.volume_name);
    println!("  Block size:        {} bytes", sb.block_size);
    println!("  Total blocks:      {} ({} MB)", sb.total_blocks, total_mb);
    println!("  Free blocks:       {}", sb.free_blocks);
    println!("  Total inodes:      {}", sb.total_inodes);
    println!("  Free inodes:       {}", sb.free_inodes);
    println!("  Blocks/group:      {}", sb.blocks_per_group);
    println!("  Inodes/group:      {}", sb.inodes_per_group);
    println!("  Inode size:        {} bytes", sb.inode_size);
    println!("  Block groups:      {}", sb.num_block_groups);
    println!("  Mount count:       {}", sb.mount_count);
    println!("  State:             {}", sb.state);
    println!("  Revision:          {}", sb.rev_level);
    println!("  Features:");
    println!("    Extents:         {}", sb.has_extents);
    println!("    64-bit:          {}", sb.has_64bit);
    println!("    Flex BG:         {}", sb.has_flex_bg);
    println!("    Metadata CRC32c: {}", sb.has_metadata_csum);
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let path = args.get(1).map(String::as_str).unwrap_or("/dev/sda1");

    match read_superblock(path) {
        Ok(sb) => print_superblock(&sb),
        Err(e) => eprintln!("Error: {}", e),
    }
}

/*
 * Compile: cargo build --release
 * Run:     sudo ./target/release/ext4_reader /dev/sda1
 *
 * Key Rust lessons here:
 * 1. repr(C, packed) for exact binary layout matching C structs
 * 2. Custom error types with From<io::Error> for ? operator
 * 3. Little-endian explicit reads (from_le_bytes) — ext4 is always LE
 * 4. Zero-copy: we read into a u8 slice, then interpret in place
 * 5. Pattern matching for state enums — cleaner than C's switch
 */
```

## 17.2 Extent Tree Walker in Rust

```rust
//! Extent tree traversal in Rust
//! Demonstrates recursive tree walking with type safety

use std::io::{self, Read, Seek, SeekFrom};
use std::fs::File;

const EXT4_EXT_MAGIC: u16 = 0xF30A;
const UNWRITTEN_FLAG: u16  = 0x8000;  // 32768

// ── On-disk types ─────────────────────────────────────────────────────────────

#[repr(C, packed)]
#[derive(Clone, Copy, Debug)]
struct ExtentHeader {
    eh_magic:      u16,
    eh_entries:    u16,
    eh_max:        u16,
    eh_depth:      u16,  // 0 = leaf, N = interior
    eh_generation: u32,
}

#[repr(C, packed)]
#[derive(Clone, Copy, Debug)]
struct Extent {
    ee_block:    u32,  // First logical block
    ee_len:      u16,  // Length (>= 32768 means unwritten)
    ee_start_hi: u16,  // Physical block (high 16 bits)
    ee_start_lo: u32,  // Physical block (low 32 bits)
}

#[repr(C, packed)]
#[derive(Clone, Copy, Debug)]
struct ExtentIndex {
    ei_block:   u32,  // First logical block covered by subtree
    ei_leaf_lo: u32,  // Physical block of child node (low 32)
    ei_leaf_hi: u16,  // Physical block of child node (high 16)
    ei_unused:  u16,
}

// ── High-level types ──────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct ExtentMapping {
    pub logical_block:  u32,
    pub physical_block: u64,
    pub len:            u16,
    pub unwritten:      bool,
}

#[derive(Debug)]
pub enum ExtentError {
    BadMagic(u16),
    DepthLimitExceeded,
    IoError(io::Error),
    OutOfBounds { logical: u32 },
}

impl From<io::Error> for ExtentError {
    fn from(e: io::Error) -> Self { ExtentError::IoError(e) }
}

// ── Extent parsing ────────────────────────────────────────────────────────────

impl Extent {
    fn physical_block(&self) -> u64 {
        // Read packed fields carefully (UB risk with direct deref on packed)
        let hi = self.ee_start_hi as u64;
        let lo = self.ee_start_lo as u64;
        (hi << 32) | lo
    }

    fn length(&self) -> u16 {
        let raw = self.ee_len;
        if raw >= UNWRITTEN_FLAG {
            raw - UNWRITTEN_FLAG
        } else {
            raw
        }
    }

    fn is_unwritten(&self) -> bool {
        self.ee_len >= UNWRITTEN_FLAG
    }

    /// Find physical block for a given logical block within this extent.
    /// Returns None if logical_block is outside this extent.
    fn map(&self, logical_block: u32) -> Option<ExtentMapping> {
        let start  = self.ee_block;
        let length = self.length() as u32;
        if logical_block < start || logical_block >= start + length {
            return None;
        }
        let offset = logical_block - start;
        Some(ExtentMapping {
            logical_block,
            physical_block: self.physical_block() + offset as u64,
            len: (length - offset) as u16,
            unwritten: self.is_unwritten(),
        })
    }
}

impl ExtentIndex {
    fn child_block(&self) -> u64 {
        let hi = self.ei_leaf_hi as u64;
        let lo = self.ei_leaf_lo as u64;
        (hi << 32) | lo
    }
}

// ── Tree walker ───────────────────────────────────────────────────────────────

/// Parses a 60-byte inline extent root or a 4096-byte tree block.
/// Returns all extents covering the file, in order.
pub fn walk_extent_tree(
    node_bytes: &[u8],
    file: &mut File,
    block_size: u64,
    depth_limit: u8,
) -> Result<Vec<ExtentMapping>, ExtentError> {
    if depth_limit == 0 {
        return Err(ExtentError::DepthLimitExceeded);
    }

    // Parse header (first 12 bytes)
    if node_bytes.len() < 12 {
        return Err(ExtentError::BadMagic(0));
    }

    let read_u16 = |buf: &[u8], off: usize| -> u16 {
        u16::from_le_bytes([buf[off], buf[off+1]])
    };
    let read_u32 = |buf: &[u8], off: usize| -> u32 {
        u32::from_le_bytes(buf[off..off+4].try_into().unwrap())
    };

    let magic   = read_u16(node_bytes, 0);
    let entries = read_u16(node_bytes, 2) as usize;
    let depth   = read_u16(node_bytes, 6);

    if magic != EXT4_EXT_MAGIC {
        return Err(ExtentError::BadMagic(magic));
    }

    let mut mappings = Vec::new();

    if depth == 0 {
        // Leaf node: parse Extent entries (12 bytes each, starting at offset 12)
        for i in 0..entries {
            let off = 12 + i * 12;
            if off + 12 > node_bytes.len() { break; }

            let ee_block    = read_u32(node_bytes, off);
            let ee_len      = read_u16(node_bytes, off + 4);
            let ee_start_hi = read_u16(node_bytes, off + 6);
            let ee_start_lo = read_u32(node_bytes, off + 8);

            let extent = Extent { ee_block, ee_len, ee_start_hi, ee_start_lo };
            let unwritten = extent.is_unwritten();
            let length    = extent.length();
            let phys      = extent.physical_block();

            mappings.push(ExtentMapping {
                logical_block: ee_block,
                physical_block: phys,
                len: length,
                unwritten,
            });
        }
    } else {
        // Index node: parse ExtentIndex entries, recurse into children
        for i in 0..entries {
            let off = 12 + i * 12;
            if off + 12 > node_bytes.len() { break; }

            let ei_block   = read_u32(node_bytes, off);
            let ei_leaf_lo = read_u32(node_bytes, off + 4);
            let ei_leaf_hi = read_u16(node_bytes, off + 6);

            let idx = ExtentIndex {
                ei_block, ei_leaf_lo, ei_leaf_hi, ei_unused: 0
            };

            let child_phys_block = idx.child_block();
            let child_byte_off   = child_phys_block * block_size;

            // Read child block from disk
            let mut child_buf = vec![0u8; block_size as usize];
            file.seek(SeekFrom::Start(child_byte_off))?;
            file.read_exact(&mut child_buf)?;

            // Recurse
            let child_mappings = walk_extent_tree(
                &child_buf, file, block_size, depth_limit - 1
            )?;
            mappings.extend(child_mappings);
        }
    }

    Ok(mappings)
}

/// Print all extents for debugging
pub fn print_extents(mappings: &[ExtentMapping]) {
    println!("{:>10} {:>16} {:>8} {:>10}",
             "LogBlock", "PhysBlock", "Len", "Type");
    println!("{:-<10} {:-<16} {:-<8} {:-<10}", "", "", "", "");
    for m in mappings {
        println!("{:>10} {:>16} {:>8} {:>10}",
                 m.logical_block,
                 m.physical_block,
                 m.len,
                 if m.unwritten { "unwritten" } else { "written" });
    }
}

fn main() {
    // Example: create a fake 60-byte extent root (depth=0, 2 extents)
    let mut iblock = [0u8; 60];
    
    // Header
    iblock[0..2].copy_from_slice(&EXT4_EXT_MAGIC.to_le_bytes());
    iblock[2..4].copy_from_slice(&2u16.to_le_bytes()); // entries = 2
    iblock[4..6].copy_from_slice(&4u16.to_le_bytes()); // max = 4
    iblock[6..8].copy_from_slice(&0u16.to_le_bytes()); // depth = 0

    // Extent 1: logical 0-999 → physical 50000
    iblock[12..16].copy_from_slice(&0u32.to_le_bytes());     // ee_block
    iblock[16..18].copy_from_slice(&1000u16.to_le_bytes());  // ee_len
    iblock[18..20].copy_from_slice(&0u16.to_le_bytes());     // ee_start_hi
    iblock[20..24].copy_from_slice(&50000u32.to_le_bytes()); // ee_start_lo

    // Extent 2: logical 1000-1499 → physical 80000 (unwritten!)
    let unwritten_len: u16 = 500 + UNWRITTEN_FLAG;
    iblock[24..28].copy_from_slice(&1000u32.to_le_bytes());
    iblock[28..30].copy_from_slice(&unwritten_len.to_le_bytes());
    iblock[30..32].copy_from_slice(&0u16.to_le_bytes());
    iblock[32..36].copy_from_slice(&80000u32.to_le_bytes());

    // Parse without disk (no index nodes to follow)
    let read_u16 = |buf: &[u8], off: usize| u16::from_le_bytes([buf[off], buf[off+1]]);
    let read_u32 = |buf: &[u8], off: usize| u32::from_le_bytes(buf[off..off+4].try_into().unwrap());

    let entries = read_u16(&iblock, 2) as usize;
    let mut mappings = Vec::new();

    for i in 0..entries {
        let off = 12 + i * 12;
        let ee_block    = read_u32(&iblock, off);
        let ee_len      = read_u16(&iblock, off + 4);
        let ee_start_lo = read_u32(&iblock, off + 8);
        let is_unwritten = ee_len >= UNWRITTEN_FLAG;
        let length = if is_unwritten { ee_len - UNWRITTEN_FLAG } else { ee_len };
        mappings.push(ExtentMapping {
            logical_block: ee_block,
            physical_block: ee_start_lo as u64,
            len: length,
            unwritten: is_unwritten,
        });
    }

    println!("Extent tree mappings:");
    print_extents(&mappings);
}

/*
 * Expected output:
 *    LogBlock    PhysBlock      Len       Type
 * ---------- ---------------- -------- ----------
 *          0            50000     1000    written
 *       1000            80000      500  unwritten
 */
```

---

# 18. mount, mkfs, tune2fs — Tools Deep Dive

## 18.1 mkfs.ext4 — Creating a Filesystem

```bash
# Basic usage
sudo mkfs.ext4 /dev/sdb1

# Full example with options
sudo mkfs.ext4 \
  -b 4096              \  # Block size (1024, 2048, 4096)
  -I 256               \  # Inode size (128 or 256)
  -i 16384             \  # Bytes per inode ratio (default 16384 = 1 inode per 16KB)
  -L "mydata"          \  # Volume label
  -m 5                 \  # Reserved block percentage (default 5% for root)
  -O extents,64bit,flex_bg,metadata_csum \  # Enable specific features
  -E stride=128,stripe-width=512          \  # RAID optimization
  -J size=128          \  # Journal size in MB
  /dev/sdb1

# Create filesystem image file (useful for testing without real disk)
dd if=/dev/zero of=test.img bs=1M count=100
mkfs.ext4 test.img
sudo mount -o loop test.img /mnt/test
```

**What mkfs.ext4 does internally:**

```
1. Open device, determine size
2. Calculate:
   - Number of block groups
   - Inode count (based on -i ratio)
   - Location of each block group's metadata
3. Write superblock (at byte 1024)
4. Write GDT (Group Descriptor Table)
5. Write backup superblocks+GDTs (in sparse groups)
6. Zero-out all block bitmaps (all blocks free initially)
7. Zero-out all inode bitmaps (all inodes free initially)
8. Zero-out inode tables (initialized with zeros)
9. Mark used blocks (superblock, GDT, bitmaps, inode table)
10. Create root directory (inode 2):
    - Allocate inode 2
    - Allocate one data block
    - Write "." and ".." directory entries
11. Create lost+found directory (inode 11):
    - Used by fsck for recovering orphaned files
12. Write journal inode (inode 8):
    - Allocate journal blocks
    - Write journal superblock
13. Update superblock with final counts
14. Sync all changes to disk
```

## 18.2 tune2fs — Modifying Filesystem Parameters

```bash
# View current parameters
sudo tune2fs -l /dev/sda1

# Change volume label
sudo tune2fs -L "new_label" /dev/sda1

# Change reserved block percentage (0 = no reserved blocks, for data drives)
sudo tune2fs -m 1 /dev/sda1

# Disable atime updates (performance)
sudo tune2fs -o acl,user_xattr /dev/sda1

# Set maximum mount count before fsck (0 or -1 = disable check)
sudo tune2fs -c 0 /dev/sda1

# Set time interval between fscks (0 = disable)
sudo tune2fs -i 0 /dev/sda1

# Enable/disable features
sudo tune2fs -O ^has_journal /dev/sda1  # Remove journal (DANGEROUS)
sudo tune2fs -O metadata_csum /dev/sda1  # Enable metadata checksums
sudo tune2fs -O extents /dev/sda1        # Enable extents
sudo tune2fs -O 64bit /dev/sda1          # Enable 64-bit support

# Resize journal
sudo tune2fs -J size=256 /dev/sda1  # Resize journal to 256MB
```

## 18.3 e2fsck — Filesystem Check and Repair

```bash
# Basic check (auto-fix, non-interactive)
sudo e2fsck -f -y /dev/sda1

# Check specific pass only
sudo e2fsck -f -y -T /dev/sda1  # Only pass 1 (inode check)

# Repair using backup superblock (if primary is corrupt)
sudo e2fsck -b 32768 /dev/sda1  # Group 1 backup
sudo e2fsck -b 98304 /dev/sda1  # Group 3 backup

# Verbose output
sudo e2fsck -f -v /dev/sda1

# Force check even if filesystem is "clean"
sudo e2fsck -f /dev/sda1

# Journal recovery only
sudo e2fsck -E journal_only /dev/sda1
```

**fsck passes:**

```
Pass 1: Check inodes, blocks, and sizes
  - Reads every inode
  - Validates mode, size, block counts
  - Builds maps of all used blocks/inodes

Pass 2: Check directory structure
  - Validates every directory entry
  - Checks that each inode number in dentries is valid
  - Checks "." and ".." correctness

Pass 3: Check directory connectivity
  - Ensures every directory is reachable from root
  - Orphaned directories → moved to lost+found

Pass 4: Check reference counts
  - Compares actual hard link counts with what inode says
  - Fixes inode link counts

Pass 5: Check group summary information
  - Recomputes block/inode bitmaps from pass 1 data
  - Compares with on-disk bitmaps
  - Fixes mismatches
```

## 18.4 debugfs — Low-Level Filesystem Inspection

```bash
# Open filesystem for reading (safe)
sudo debugfs /dev/sda1

# Open for writing (DANGEROUS — bypasses all safety)
sudo debugfs -w /dev/sda1

# Inside debugfs:
debugfs> stats              # Show superblock info
debugfs> show_super_stats   # Detailed superblock
debugfs> ls /               # List root directory
debugfs> ls -l /home/user   # List with inode numbers
debugfs> stat /home/user/file.txt  # Show inode details
debugfs> dump_extents /home/user/file.txt  # Show extent tree
debugfs> cat /home/user/file.txt  # Print file contents
debugfs> icheck 1000        # Which file uses block 1000?
debugfs> ncheck 42          # Which directory entry points to inode 42?
debugfs> htree /home/bigdir # Dump HTree index of large directory
debugfs> logdump -a         # Dump all journal transactions
debugfs> block_dump 1       # Hex dump of block 1 (superblock)
debugfs> find_free_block    # Find a free block
debugfs> find_free_inode    # Find a free inode
debugfs> testb 100          # Is block 100 allocated?
debugfs> testi 42           # Is inode 42 allocated?
```

## 18.5 dumpe2fs — Filesystem Structure Dump

```bash
# Dump everything
sudo dumpe2fs /dev/sda1

# Superblock only
sudo dumpe2fs -h /dev/sda1

# Group descriptor for group 0
sudo dumpe2fs /dev/sda1 | head -100

# Sample output:
# Filesystem features:      has_journal ext_attr resize_inode dir_index 
#                           filetype needs_recovery extent 64bit flex_bg 
#                           sparse_super large_file huge_file dir_nlink 
#                           extra_isize metadata_csum
# Filesystem flags:         signed_directory_hash 
# Default mount options:    user_xattr acl
# Filesystem state:         clean
# Errors behavior:          Continue
# Filesystem OS type:       Linux
# Inode count:              655360
# Block count:              2621440
# Reserved block count:     131072
# Overhead clusters:        113856
# Free blocks:              2380944
# Free inodes:              655351
# First block:              0
# Block size:               4096
# Fragment size:             4096
# Group descriptor size:    64
# Blocks per group:         32768
# Fragments per group:      32768
# Inodes per group:         8192
# Inode blocks per group:   512
# Flex block group size:    16
# Journal inode:            8
```

## 18.6 resize2fs — Online Filesystem Resizing

```bash
# Extend filesystem to fill partition (after partition was extended)
sudo resize2fs /dev/sda1

# Shrink filesystem to 10GB (must be unmounted for shrinking!)
sudo umount /dev/sda1
sudo e2fsck -f /dev/sda1
sudo resize2fs /dev/sda1 10G
# Then resize partition too

# Extend online (while mounted!)
sudo resize2fs /dev/sda1 20G
```

## 18.7 Mounting Options

```bash
# Common mount options
sudo mount -t ext4 \
  -o rw,relatime,data=ordered,errors=remount-ro \
  /dev/sda1 /mnt

# Key options:
# data=journal   — Full data journaling (safest, slowest)
# data=ordered   — Metadata journal + data ordering (default)
# data=writeback — Metadata journal only (fastest, less safe)
#
# relatime       — Update atime only if atime < mtime (performance)
# noatime        — Never update atime (better performance)
# nodiratime     — Never update dir atime
#
# barrier=1      — Use write barriers for crash safety (default)
# barrier=0      — Disable barriers (dangerous! only for UPS-backed systems)
#
# commit=N       — Journal commit interval in seconds (default 5)
#
# errors=continue       — On error, try to continue
# errors=remount-ro     — On error, remount read-only (default)
# errors=panic          — On error, kernel panic
#
# discard        — Enable TRIM for SSDs (automatic TRIM on delete)
# nodiscard      — Disable TRIM (default — use fstrim periodically instead)
#
# lazytime       — Buffer timestamp updates in memory (performance)
#
# inode_readahead_blks=N — Number of inode table blocks to readahead

# /etc/fstab example:
# UUID=xxx-yyy  /  ext4  defaults,errors=remount-ro  0 1
```

---

# 19. Performance Tuning

## 19.1 SSD Optimization

```bash
# Check current scheduler
cat /sys/block/sda/queue/scheduler
# Output: [mq-deadline] kyber bfq none

# Use 'none' for NVMe (no reordering needed, SSD handles it)
echo none > /sys/block/nvme0n1/queue/scheduler

# Enable TRIM support
# Option 1: Mount with discard (trim on every delete — some overhead)
mount -o discard /dev/sda1 /mnt

# Option 2: Periodic TRIM (better for performance)
sudo fstrim -v /
# Or via systemd timer:
sudo systemctl enable fstrim.timer
sudo systemctl start fstrim.timer

# Disable write barriers ONLY if using a UPS or battery-backed RAID:
mount -o barrier=0 /dev/sda1 /mnt
```

## 19.2 Tuning Writeback for Performance

```bash
# Increase dirty ratio for write-heavy workloads
echo 40 > /proc/sys/vm/dirty_ratio
echo 20 > /proc/sys/vm/dirty_background_ratio

# Decrease for better durability (more frequent flushes)
echo 10 > /proc/sys/vm/dirty_ratio
echo 5  > /proc/sys/vm/dirty_background_ratio

# Make permanent in /etc/sysctl.conf:
vm.dirty_ratio = 40
vm.dirty_background_ratio = 20

# Increase journal commit interval (reduces journal I/O, less safe)
mount -o commit=60 /dev/sda1 /mnt   # 60 seconds between commits

# For databases: use data=journal + barrier=0 + UPS
mount -o data=journal,barrier=0 /dev/sda1 /mnt
```

## 19.3 Inode Density Tuning

```bash
# For filesystems with many small files (e.g., mail servers, source trees)
# Create with high inode density:
mkfs.ext4 -i 4096 /dev/sda1  # 1 inode per 4KB (4x more inodes)

# For large media files (fewer inodes needed):
mkfs.ext4 -i 131072 /dev/sda1  # 1 inode per 128KB (fewer inodes)

# Check current inode usage:
df -i /
# Filesystem        Inodes   IUsed   IFree IUse% Mounted on
# /dev/sda1        1310720  245831 1064889   19% /
```

## 19.4 RAID Alignment (stride and stripe-width)

When ext4 is on a RAID array, misaligned I/O causes read-modify-write cycles. Setting stride and stripe-width helps:

```bash
# For RAID-5/6 with 4 data disks, 256KB stripe size:
# stripe_size = 256KB, block_size = 4KB
# stride = stripe_size / (num_data_disks * block_size)
#        = 256KB / (4 * 4KB) = 16  ... per-disk chunk
# stripe_width = num_data_disks * stride = 4 * 16 = 64

mkfs.ext4 -E stride=16,stripe-width=64 /dev/md0

# For a simple RAID-0 with 2 disks, 128KB stripe:
# stride = 128KB / (2 * 4KB) = 16
# stripe_width = 2 * 16 = 32
mkfs.ext4 -E stride=16,stripe-width=32 /dev/md0
```

## 19.5 Profiling I/O

```bash
# iostat: per-device I/O statistics
iostat -x 1        # Extended stats every 1 second
# Look for: %util (100% = saturated), await (ms latency)

# iotop: per-process I/O
sudo iotop -a      # Accumulated I/O

# blktrace: kernel-level block I/O tracing
sudo blktrace -d /dev/sda -o - | blkparse -i -

# ioping: I/O latency test
ioping -c 10 /

# fio: comprehensive I/O benchmark
fio --name=randread --rw=randread --bs=4k --numjobs=4 \
    --size=1G --time_based --runtime=30 --filename=/mnt/test

# Check ext4 specific stats
cat /proc/fs/ext4/sda1/mb_groups  # Multiblock allocator stats
```

---

# 20. Forensics, Recovery & Debugging

## 20.1 Recovering Deleted Files

When a file is deleted in ext4:
1. The directory entry is marked deleted (inode=0 or rec_len swallowed)
2. The inode's `i_dtime` is set to the current time
3. The inode is added to a "free inode" list (inode bitmap bit cleared)
4. The data blocks are freed (block bitmap bits cleared)

**The data itself is NOT overwritten immediately!**

```bash
# ext4magic — dedicated ext4 recovery tool
sudo apt install ext4magic

# List deleted files in the last 24 hours
sudo ext4magic /dev/sda1 -l -a $(date -d "24 hours ago" +%s)

# Recover all deleted files from last 24 hours
sudo ext4magic /dev/sda1 -r -a $(date -d "24 hours ago" +%s) -d /tmp/recovered

# Recover specific file by inode number
sudo ext4magic /dev/sda1 -i 42 -r -d /tmp/

# debugfs for manual recovery
sudo debugfs /dev/sda1
debugfs> lsdel          # List deleted inodes
debugfs> undel <inode>  # Attempt to undelete
```

**Important**: In ext4 with extents, recovery is harder than ext2. When an inode is deleted, ext4 **zeroes out the extent tree** in the inode, making it hard to find the data blocks without raw block scanning.

## 20.2 Hex Examination of Raw Disk

```bash
# Examine superblock (at byte 1024)
sudo hexdump -C /dev/sda1 | head -100
sudo dd if=/dev/sda1 bs=1 skip=1024 count=256 | hexdump -C

# Examine inode table (need to calculate offset first)
# Group 0's inode table is at block bg_inode_table_lo
# For group 0, this is typically block 5 (for 4KB blocks)
sudo dd if=/dev/sda1 bs=4096 skip=5 count=1 | hexdump -C

# Read specific block
sudo dd if=/dev/sda1 bs=4096 skip=N count=1 | hexdump -C
```

## 20.3 The Lost+Found Directory

The `lost+found` directory is pre-allocated by mkfs.ext4 and is used by e2fsck to store recovered orphaned files (files with valid inodes but no directory entry):

```bash
ls -la /lost+found/
# If fsck found orphaned files:
# total 48
# drwx------  3 root root 20480 Jan  1 00:00 .
# drwxr-xr-x 20 root root  4096 Jan  1 00:00 ..
# -rw-r--r--  1 root root  4096 Jan 14 15:30 #42      (orphaned inode 42)
```

Files in lost+found are named by their inode number. You must manually identify and move them.

## 20.4 Journal Examination

```bash
# Dump journal contents
sudo debugfs /dev/sda1
debugfs> logdump -a        # All journal blocks
debugfs> logdump -c 5      # Last 5 committed transactions
debugfs> logdump -b 100    # Journal blocks for block 100

# journal2.py or jbd2 tools for deeper analysis
sudo dumpe2fs /dev/sda1 | grep "Journal inode"  # Find journal inode number
```

## 20.5 Checking for Corruption

```bash
# Bad blocks scan (destructive write test — ERASES DATA!)
# DO NOT USE on production disks!
sudo badblocks -wsv /dev/sdb

# Non-destructive read test
sudo badblocks -sv /dev/sda1

# SMART data (HDD health)
sudo smartctl -a /dev/sda

# Check filesystem with verbose pass output
sudo e2fsck -f -v -p /dev/sda1

# Check specific block
sudo debugfs /dev/sda1
debugfs> testb 50000   # Is block 50000 in use?
```

---

# 21. Security: Encryption & ACLs

## 21.1 ext4 Filesystem Encryption (fscrypt)

ext4 supports per-directory encryption (since kernel 4.1), using the **fscrypt** framework:

```bash
# Set up encryption key
# Modern approach (fscrypt v2 API):
sudo fscryptctl create-key /

# Encrypt a directory
sudo fscryptctl encrypt-dir --policy-version=2 /home/user/private

# The encrypted directory stores:
# - Encrypted file contents (per-file key derived from master key)
# - Encrypted filenames
# - Encryption policy in inode xattr

# Unlock (provide key)
sudo fscryptctl unlock-dir /home/user/private

# Kernel-level: in fscrypt_info (pointed to by inode->i_crypt_info):
struct fscrypt_info {
    u8                       ci_mode;        /* Encryption mode */
    u8                       ci_data_unit_bits;
    u8                       ci_level;       /* Tree level (for per-extent keys) */
    u8                       ci_policy_flags;
    union fscrypt_policy     ci_policy;      /* Contains master key identifier */
    struct fscrypt_master_key *ci_master_key;
    struct crypto_skcipher   *ci_enc_key;    /* Prepared cipher */
    struct fscrypt_inode_info *ci_inode_info;
};
```

**Encryption algorithms supported:**
- AES-256-XTS (data, recommended)
- AES-256-CBC-ESSIV (data, older)
- AES-256-CTS-CBC (filenames)
- AES-128-CBC (data)
- AES-128-HEH (filenames)
- Adiantum (ChaCha20+Poly1305 for low-end hardware without AES acceleration)

## 21.2 POSIX Access Control Lists (ACLs)

Extended permissions beyond the traditional rwx:

```bash
# Set ACL: user alice gets read+write
setfacl -m u:alice:rw /home/shared/file.txt

# Set ACL: group devs gets read
setfacl -m g:devs:r /home/shared/file.txt

# Default ACL (inherited by new files in directory)
setfacl -d -m u:alice:rwx /home/shared/

# View ACLs
getfacl /home/shared/file.txt
# Output:
# # file: home/shared/file.txt
# # owner: bob
# # group: bob
# user::rw-
# user:alice:rw-
# group::r--
# group:devs:r--
# mask::rw-
# other::---

# ACLs are stored as extended attributes (xattrs)
# in the inode's attribute block (i_file_acl)
```

## 21.3 Extended Attributes (xattrs)

xattrs store arbitrary key-value metadata alongside files:

```bash
# Set xattr
setfattr -n user.description -v "Project documentation" file.txt
setfattr -n security.selinux -v "system_u:object_r:public_content_t:s0" file.txt

# Get xattr
getfattr -n user.description file.txt
getfattr -d file.txt   # Get all xattrs

# Common namespaces:
# user.*      — User-defined attributes
# security.*  — SELinux, AppArmor
# trusted.*   — Only root can read/write
# system.*    — Used for ACLs (system.posix_acl_access)
```

**Storage**: Small xattrs (< ~60 bytes) can fit in the inode's extra space. Larger xattrs go in a dedicated **attribute block** (pointed to by `i_file_acl`).

---

# 22. Comparison: ext4 vs xfs vs btrfs vs zfs

## 22.1 Feature Comparison Matrix

| Feature | ext4 | xfs | btrfs | zfs |
|---|---|---|---|---|
| **Max FS size** | 1 EB | 8 EB | 16 EB | 256 ZB |
| **Max file size** | 16 TiB | 8 EiB | 16 EiB | 16 EiB |
| **Snapshots** | ✗ | ✗ | ✓ | ✓ |
| **Checksums** | metadata only | metadata only | data+meta | data+meta |
| **Compression** | ✗ | ✗ | ✓ (zstd,lzo) | ✓ |
| **Deduplication** | ✗ | ✗ | ✓ (online) | ✓ |
| **RAID** | via md/lvm | via md/lvm | built-in | built-in |
| **Send/receive** | ✗ | ✓ (xfs_dump) | ✓ (btrfs send) | ✓ |
| **Online grow** | ✓ | ✓ | ✓ | ✓ |
| **Online shrink** | ✓ | ✗ | ✓ | ✗ |
| **Stable/mature** | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓✓ |
| **Fsck speed** | O(journal) | O(journal) | O(data) slow | built-in |

## 22.2 When to Use Each

```
ext4:
  ✓ General purpose Linux (root /, /home, /var)
  ✓ Stability and maturity are paramount
  ✓ Single disk without complex features needed
  ✓ Old hardware, minimal RAM
  ✗ Need snapshots, checksums on data, compression

xfs:
  ✓ High-throughput I/O (databases, media storage)
  ✓ Very large files and filesystems
  ✓ Parallel I/O workloads (scales better at high concurrency)
  ✓ Large directories with millions of files
  ✗ Many small files (worse than ext4)
  ✗ Cannot shrink online

btrfs:
  ✓ Snapshots needed (backups via btrfs send/receive)
  ✓ SSD with transparent compression
  ✓ Subvolumes for container storage (Docker)
  ✓ Self-healing with multiple devices (RAID 1)
  ✗ RAID 5/6 still experimental!
  ✗ Higher CPU overhead

zfs:
  ✓ Enterprise storage with absolute data integrity
  ✓ Compression + deduplication needed
  ✓ Pool-based management (zpools spanning multiple disks)
  ✓ Long-term data storage
  ✗ License conflict with Linux kernel (requires DKMS module)
  ✗ Needs significant RAM (ARC cache, ECC RAM recommended)
```

---

# Appendix A: Kernel Source Navigation

Key files in the Linux kernel source for ext4:

```
fs/ext4/
├── ext4.h          ← All data structures (start here!)
├── super.c         ← Superblock read/write, mount logic
├── inode.c         ← Inode operations, writepage, readpage
├── file.c          ← File read/write operations
├── dir.c           ← Directory operations
├── namei.c         ← File creation, lookup, deletion
├── extents.c       ← Extent tree: lookup, insert, split
├── mballoc.c       ← Multi-block allocator
├── balloc.c        ← Block allocation/deallocation  
├── ialloc.c        ← Inode allocation/deallocation
├── resize.c        ← Online resize
├── journal.c       ← Journal wrapper (ext4 ↔ JBD2)
├── crypto.c        ← fscrypt integration
├── xattr.c         ← Extended attributes
├── acl.c           ← POSIX ACLs
├── htree.c         ← Hash-indexed directory (HTree)
├── inline.c        ← Inline data (small files in inode)
├── migrate.c       ← ext3 → ext4 migration
├── fsync.c         ← fsync(), fdatasync()
└── ioctl.c         ← ioctl() interface

fs/jbd2/
├── journal.c       ← JBD2 core
├── transaction.c   ← Transaction management
├── recovery.c      ← Journal replay on mount
├── commit.c        ← Transaction commit
└── checkpoint.c    ← Journal checkpointing

fs/
├── namei.c         ← VFS path resolution
├── inode.c         ← VFS inode cache
├── dcache.c        ← Dentry cache
├── page-writeback.c← Writeback engine
└── buffer.c        ← Buffer cache (block metadata)

mm/
├── page-writeback.c← Dirty page limits, kflushd
├── readahead.c     ← Read-ahead logic
└── filemap.c       ← Page cache: read/write paths
```

---

# Appendix B: Key System Calls and Their ext4 Path

```
open(path, flags)
  → sys_openat() → do_sys_open() → do_filp_open()
  → path_openat() → link_path_walk() → ext4_lookup()
  → dentry_open() → ext4_file_open()

read(fd, buf, n)
  → sys_read() → vfs_read() → new_sync_read()
  → call_read_iter() → ext4_file_read_iter()
  → generic_file_read_iter() → page cache lookup
  → ext4_readpage() → ext4_mpage_readpages()
  → submit_bio() → block layer → disk

write(fd, buf, n)
  → sys_write() → vfs_write() → new_sync_write()
  → call_write_iter() → ext4_file_write_iter()
  → ext4_buffered_write_iter()
  → generic_perform_write() → ext4_write_begin()
  → mark_page_dirty() → return to user

  (background: kworker → ext4_writepages() → mballoc → submit_bio)

fsync(fd)
  → sys_fsync() → vfs_fsync() → ext4_sync_file()
  → file_write_and_wait_range() → flush dirty pages
  → jbd2_complete_transaction() → wait for journal commit

stat(path, statbuf)
  → sys_newfstatat() → vfs_statx() → ext4_getattr()
  → fill statbuf from in-memory inode
  → returns size, times, permissions, etc.

unlink(path)
  → sys_unlinkat() → do_unlinkat() → vfs_unlink()
  → ext4_unlink():
    1. Start journal transaction
    2. Remove dentry from directory
    3. Decrement inode link count
    4. If link count = 0: add to orphan list
    5. Commit transaction
  → iput() → if count=0: evict_inode() → ext4_evict_inode()
    → if orphan: free inode + data blocks
```

---

# Appendix C: Performance Checklist

```
[ ] Block size matches workload:
    - Small files → 1KB or 2KB blocks (less internal fragmentation)
    - Large files → 4KB blocks (default, best for most cases)
    
[ ] Inode ratio set correctly for workload:
    - Many small files → -i 4096 or smaller
    - Large media files → -i 65536 or larger

[ ] Journal size appropriate:
    - High write workload → larger journal (256MB-1GB)
    - Low write workload → default (64-128MB)

[ ] Mount options optimized:
    - noatime or relatime (reduces write I/O for reads!)
    - data=ordered (default, good balance)
    - commit=30 or higher for write-heavy batch workloads

[ ] SSD-specific:
    - Periodic TRIM (fstrim.timer enabled)
    - Scheduler = none for NVMe
    - discard mount option (optional, trim on delete)
    - Alignment: partition starts at 1MB boundary

[ ] HDD-specific:
    - Scheduler = mq-deadline (default)
    - readahead tuned: blockdev --setra 4096 /dev/sda
    - stride/stripe-width set for RAID arrays

[ ] Writeback tuning:
    - dirty_ratio and dirty_background_ratio set for workload
    - Larger = better performance, worse durability
    - Smaller = more frequent flushes, better durability

[ ] Monitoring:
    - iostat -x 1 (watch %util and await)
    - /proc/meminfo (watch Dirty and Writeback)
    - /proc/sys/vm/nr_dirty (current dirty page count)
```

---

*End of Guide*

**Summary of Core Concepts:**

```
DISK
 └─ Partition (/dev/sda1)
     └─ ext4 filesystem
         ├─ Superblock (master record at byte 1024)
         ├─ Block Groups (128MB chunks)
         │   ├─ Block Bitmap (which blocks are free)
         │   ├─ Inode Bitmap (which inodes are free)
         │   ├─ Inode Table (array of inode structs)
         │   └─ Data Blocks (actual file contents)
         │
         ├─ Inodes (file metadata: permissions, size, timestamps)
         │   └─ Extent Trees (logical→physical block mapping)
         │
         ├─ Directories (files containing filename→inode mappings)
         │   └─ HTree (hash-indexed B-tree for large dirs)
         │
         └─ Journal/JBD2 (write-ahead log for crash safety)

VFS Layer (in kernel RAM):
  super_block → ext4_sb_info
  inode       → ext4_inode_info
  dentry      ← dcache (recently accessed paths)
  file        ← per-process open file descriptor

Page Cache (in kernel RAM):
  address_space → XArray of pages (4KB each)
  dirty pages → writeback thread → disk
  read pages  → served from RAM (no disk I/O)
```

I'll now build the complete ext4 guide. This is a very large document — I'll write it in sections directly to disk.Nearly **4000 lines / 150KB** of dense material. Here's what's inside and what makes each section deep:

---

## What This Guide Covers (and Why Each Section Matters)

| # | Section | Key Depth |
|---|---|---|
| 1 | Foundations | Precise vocabulary table — every term defined before use |
| 2 | Storage Hardware | HDD seek physics, SSD write amplification, FTL — why layout matters |
| 3 | ext Family History | The exact problems each generation solved; why ext4 chose extents |
| 4 | Disk Layout | Full ASCII map from partition table → block groups → individual fields |
| 5 | Superblock | Full `ext4_super_block` C struct annotated; feature flag bitmasks decoded; C reader program |
| 6 | Block Groups | The math of block group sizing; flex_bg; full `ext4_group_desc` struct |
| 7 | Inodes | Full `ext4_inode` struct; `i_mode` bit-level breakdown; timestamp nanosecond encoding; reserved inodes; **the math to locate any inode on disk** |
| 8 | Extent Trees | Why indirect blocks were bad; full extent tree B-tree walkthrough; `ext4_extent`, `ext4_extent_idx`, `ext4_extent_header`; C recursive tree walker |
| 9 | Directories | Linear format vs HTree; binary search on filename hashes; C directory block parser |
| 10 | JBD2 Journal | WAL principle; journal data structures; three journaling modes compared; crash recovery algorithm; transaction lifecycle state machine |
| 11 | VFS Layer | Full `super_block`, `inode`, `dentry`, `file` structs; function pointer vtables; path resolution algorithm (namei) |
| 12 | Page Cache | `address_space`; `struct page` flags; read path from syscall → disk |
| 13 | Writeback | Dirty ratio thresholds; `fsync()` kernel path; kflushd |
| 14 | delalloc | The fragmentation problem; how allocation deferral enables contiguous extents |
| 15 | Block Layer | `struct bio`; I/O scheduler algorithms (mq-deadline, kyber, bfq) |
| 16 | Kernel Structs | `ext4_sb_info`, `ext4_inode_info`, `EXT4_I()` macro, mballoc buddy system |
| 17 | Rust Implementations | Type-safe superblock reader; extent tree walker with proper error types and `repr(C, packed)` |
| 18 | Tools | mkfs internals; tune2fs; e2fsck passes 1–5; debugfs commands; dumpe2fs; resize2fs; all mount options |
| 19 | Performance | SSD/HDD tuning; writeback knobs; RAID stride/stripe-width math; I/O profiling tools |
| 20 | Forensics | Deleted file recovery mechanics; raw disk hex tools; lost+found; journal dumping |
| 21 | Security | fscrypt encryption structs; ACL internals; xattr storage |
| 22 | Comparison | ext4 vs xfs vs btrfs vs zfs feature matrix with when-to-use decision guide |