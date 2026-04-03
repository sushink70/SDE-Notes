# Linux Virtual Filesystem (VFS): A Complete In-Depth Guide

> *"The filesystem is not just a storage abstraction — it is the nervous system of the kernel, binding processes, memory, devices, and data into a unified, navigable reality."*

---

## Table of Contents

1. [Introduction & Philosophy](#1-introduction--philosophy)
2. [The Big Picture: What Problem Does VFS Solve?](#2-the-big-picture-what-problem-does-vfs-solve)
3. [VFS Architecture Overview](#3-vfs-architecture-overview)
4. [Core VFS Objects: The Four Pillars](#4-core-vfs-objects-the-four-pillars)
   - 4.1 [Superblock Object](#41-superblock-object)
   - 4.2 [Inode Object](#42-inode-object)
   - 4.3 [Dentry Object](#43-dentry-object)
   - 4.4 [File Object](#44-file-object)
5. [VFS Operations Tables (vtables)](#5-vfs-operations-tables-vtables)
6. [The Path Walk: How the Kernel Resolves a Filename](#6-the-path-walk-how-the-kernel-resolves-a-filename)
7. [The Mount Subsystem](#7-the-mount-subsystem)
   - 7.1 [Mount Namespaces](#71-mount-namespaces)
   - 7.2 [Bind Mounts](#72-bind-mounts)
   - 7.3 [The vfsmount Structure](#73-the-vfsmount-structure)
8. [Dentry Cache (dcache)](#8-dentry-cache-dcache)
9. [Inode Cache (icache)](#9-inode-cache-icache)
10. [Page Cache & Buffer Cache](#10-page-cache--buffer-cache)
11. [File Descriptors & the Open File Table](#11-file-descriptors--the-open-file-table)
12. [System Calls: From User Space to VFS](#12-system-calls-from-user-space-to-vfs)
13. [Pseudo Filesystems Deep Dive](#13-pseudo-filesystems-deep-dive)
    - 13.1 [procfs (/proc)](#131-procfs-proc)
    - 13.2 [sysfs (/sys)](#132-sysfs-sys)
    - 13.3 [tmpfs](#133-tmpfs)
    - 13.4 [devtmpfs (/dev)](#134-devtmpfs-dev)
    - 13.5 [cgroupfs](#135-cgroupfs)
    - 13.6 [pipefs & sockfs](#136-pipefs--sockfs)
14. [Implementing a Minimal Filesystem in C](#14-implementing-a-minimal-filesystem-in-c)
15. [FUSE: Filesystems in Userspace](#15-fuse-filesystems-in-userspace)
16. [Implementing a FUSE Filesystem in C](#16-implementing-a-fuse-filesystem-in-c)
17. [VFS from Rust: Safe Abstractions and Kernel Modules](#17-vfs-from-rust-safe-abstractions-and-kernel-modules)
18. [Extended Attributes (xattr)](#18-extended-attributes-xattr)
19. [File Locking in VFS](#19-file-locking-in-vfs)
20. [Asynchronous I/O and io_uring interaction with VFS](#20-asynchronous-io-and-io_uring-interaction-with-vfs)
21. [Filesystem Notifications: inotify & fanotify](#21-filesystem-notifications-inotify--fanotify)
22. [Security in VFS: LSM Hooks](#22-security-in-vfs-lsm-hooks)
23. [Memory-Mapped Files and VFS](#23-memory-mapped-files-and-vfs)
24. [Filesystem Writeback and Journaling](#24-filesystem-writeback-and-journaling)
25. [VFS Performance Internals](#25-vfs-performance-internals)
26. [Tracing & Debugging VFS](#26-tracing--debugging-vfs)
27. [Mental Models and Expert Intuition](#27-mental-models-and-expert-intuition)

---

## 1. Introduction & Philosophy

The Linux Virtual Filesystem Switch (VFS) is one of the most elegant examples of object-oriented design within a C codebase. It defines a *universal contract* that every filesystem — whether it stores data on spinning rust, flash, a network server, or generates it purely in memory — must honor.

Understanding VFS is not merely a kernel programming skill. It is a **mental model** that changes how you reason about:

- Why `/proc/self/fd/` can represent open files as symlinks
- Why `cp /dev/stdin output.txt` works
- Why mounting a filesystem inside a container is isolated from the host
- Why a `stat()` on a file over NFS looks identical to one on ext4
- Why `mmap()` and `read()` share the same page cache

**The Cognitive Principle at Work:** This is *chunking* at the systems level — once you absorb VFS as a unified abstraction layer, every individual filesystem becomes a mere plugin. You will read new filesystem source code 10× faster because you already know the contract.

---

## 2. The Big Picture: What Problem Does VFS Solve?

### 2.1 The Fundamental Problem

Without a unifying layer, every program would need to know *which* filesystem holds the file it wants to open. A program reading a file from ext4 would need different code than one reading from XFS, NTFS, NFS, or procfs.

This violates the most important principle in systems design: **programs should not care about the physical medium.**

### 2.2 The UNIX Answer: Everything is a File

UNIX declared that files, directories, devices, pipes, sockets, and even processes are all files. The consequence of this declaration is that a single set of system calls — `open`, `read`, `write`, `close`, `stat`, `mmap` — works for all of them.

VFS is the kernel machinery that makes this declaration *true*.

### 2.3 The Layered Model

```
User Space
─────────────────────────────────────────────────
    Application (open, read, write, close)
─────────────────────────────────────────────────
System Call Interface (syscall table)
─────────────────────────────────────────────────
    VFS Layer (unified objects + operations)
─────────────────────────────────────────────────
    ┌──────────┬──────────┬──────────┬─────────┐
    │  ext4    │   xfs    │  tmpfs   │  procfs │  ...
    └──────────┴──────────┴──────────┴─────────┘
─────────────────────────────────────────────────
    Block Layer / Network Layer / Memory
─────────────────────────────────────────────────
Kernel Space
```

---

## 3. VFS Architecture Overview

### 3.1 Core Design Principles

VFS is built on **four core object types**, each with an associated **operations table** (a struct of function pointers — C's version of a vtable):

| VFS Object   | Operations Structure          | Represents                          |
|--------------|-------------------------------|-------------------------------------|
| `superblock` | `super_operations`            | A mounted filesystem instance       |
| `inode`      | `inode_operations`            | A file or directory (metadata)      |
| `dentry`     | `dentry_operations`           | A directory entry (name → inode)    |
| `file`       | `file_operations`             | An open file descriptor             |

### 3.2 Relationships Between Objects

```
superblock ──────────────────────────────────────────────┐
    │                                                     │
    │ owns many                                           │
    ▼                                                     │
  inode ──── inode_operations (mkdir, create, link...)   │
    │                                                     │
    │ referenced by                                       │
    ▼                                                     │
  dentry ── dentry_operations (compare, hash, revalidate)│
    │                                                     │
    │ pointed to by                                       │
    ▼                                                     │
  file ───── file_operations (read, write, mmap, ioctl)  │
    │                                                     │
    └─────────────────── all rooted at ──────────────────┘
```

### 3.3 The Global Root and Mount Tree

The kernel maintains a **global mount tree**. Every mounted filesystem is a node in this tree. The root of the entire tree is the **rootfs** — the initial ramfs/tmpfs mounted at boot. All other filesystems attach as subtrees via the `mount()` system call.

---

## 4. Core VFS Objects: The Four Pillars

### 4.1 Superblock Object

#### Concept

The superblock represents a *mounted filesystem instance*. It contains global metadata: block size, total blocks, free blocks, the root inode, and pointers to the operations this filesystem supports.

When you run `mount /dev/sda1 /mnt`, the kernel:
1. Finds the filesystem type (ext4)
2. Calls `ext4_fill_super()` to populate the superblock
3. Reads the on-disk superblock into this in-memory structure

#### Kernel Definition (Simplified from `include/linux/fs.h`)

```c
struct super_block {
    struct list_head        s_list;         /* list of all superblocks */
    dev_t                   s_dev;          /* device identifier */
    unsigned char           s_blocksize_bits;
    unsigned long           s_blocksize;
    loff_t                  s_maxbytes;     /* max file size */
    struct file_system_type *s_type;        /* filesystem type */
    const struct super_operations *s_op;   /* operations vtable */
    const struct dquot_operations *dq_op;  /* quota operations */
    const struct quotactl_ops *s_qcop;
    const struct export_operations *s_export_op;
    unsigned long           s_flags;        /* mount flags (MS_RDONLY, etc.) */
    unsigned long           s_iflags;       /* internal flags */
    unsigned long           s_magic;        /* filesystem magic number */
    struct dentry           *s_root;        /* root dentry */
    struct rw_semaphore     s_umount;       /* unmount semaphore */
    int                     s_count;        /* reference count */
    atomic_t                s_active;       /* active uses */
    void                    *s_fs_info;     /* filesystem private info */
    unsigned int            s_max_links;
    struct mutex            s_vfs_rename_mutex;
    char                    s_id[32];       /* informational name */
    uuid_t                  s_uuid;
    unsigned int            s_time_gran;    /* granularity of c/m/atime */
    struct list_head        s_inodes;       /* all inodes */
    spinlock_t              s_inode_list_lock;
    struct list_lru         s_dentry_lru;   /* unused dentry LRU */
    struct list_lru         s_inode_lru;    /* unused inode LRU */
    /* ... many more fields ... */
};
```

#### The super_operations Vtable

```c
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
    int  (*show_options)(struct seq_file *, struct dentry *);
    int  (*show_devname)(struct seq_file *, struct dentry *);
    int  (*show_path)(struct seq_file *, struct dentry *);
    int  (*show_stats)(struct seq_file *, struct dentry *);
    long (*nr_cached_objects)(struct super_block *, struct shrink_control *);
    long (*free_cached_objects)(struct super_block *, struct shrink_control *);
};
```

**Key Insight:** `alloc_inode` is where a filesystem can embed its private data within the inode. ext4 allocates an `ext4_inode_info` which *contains* a `struct inode` as its first member, allowing safe casting between the two.

```c
/* From fs/ext4/ext4.h */
struct ext4_inode_info {
    /* ext4-specific fields */
    __le32  i_data[15];         /* block pointers */
    __u32   i_flags;
    ext4_lblk_t i_dir_start_lookup;
    /* ... hundreds more fields ... */

    struct inode vfs_inode;     /* THE VFS INODE — must be last or first */
};

/* Kernel trick: container_of macro allows casting */
static inline struct ext4_inode_info *EXT4_I(struct inode *inode)
{
    return container_of(inode, struct ext4_inode_info, vfs_inode);
}
```

This **container_of** pattern is the C equivalent of inheritance. It is one of the most important kernel idioms. Memorize it.

---

### 4.2 Inode Object

#### Concept

An **inode** (index node) represents a *file or directory* — its metadata, not its name or location in the directory tree. The inode stores:

- File type (regular, directory, symlink, device, pipe, socket)
- Permissions (mode)
- Owner (UID, GID)
- Timestamps (atime, mtime, ctime)
- Size
- Link count (how many dentries point to this inode)
- Pointers to data blocks (for on-disk filesystems)

An inode has **no name**. Names are stored in dentries. This is why hard links work: two dentries, one inode.

#### Kernel Definition

```c
struct inode {
    umode_t                 i_mode;         /* file type + permissions */
    unsigned short          i_opflags;
    kuid_t                  i_uid;
    kgid_t                  i_gid;
    unsigned int            i_flags;
    const struct inode_operations *i_op;   /* operations vtable */
    struct super_block      *i_sb;          /* owning superblock */
    struct address_space    *i_mapping;     /* page cache mapping */
    /* ... */
    unsigned long           i_ino;          /* inode number */
    union {
        const unsigned int i_nlink;
        unsigned int __i_nlink;
    };
    dev_t                   i_rdev;         /* device (for dev files) */
    loff_t                  i_size;         /* file size in bytes */
    struct timespec64       i_atime;        /* last access time */
    struct timespec64       i_mtime;        /* last modification time */
    struct timespec64       i_ctime;        /* last status change time */
    spinlock_t              i_lock;
    unsigned short          i_bytes;
    u8                      i_blkbits;
    u8                      i_write_hint;
    blkcnt_t                i_blocks;       /* 512-byte block count */
    /* ... */
    const struct file_operations *i_fop;   /* default file operations */
    struct file_lock_context *i_flctx;     /* file lock context */
    struct address_space    i_data;         /* page cache for this inode */
    struct list_head        i_devices;      /* for block/char device inodes */
    union {
        struct pipe_inode_info  *i_pipe;
        struct block_device     *i_bdev;
        struct cdev             *i_cdev;
        char                    *i_link;    /* for symlinks */
        unsigned                i_dir_seq;
    };
    __u32                   i_generation;
    /* ... */
    atomic_t                i_count;        /* reference count */
    atomic_t                i_writecount;
    atomic_t                i_readcount;
    union {
        const struct file_operations *i_fop;
        void (*free_inode)(struct inode *);
    };
    struct file_lock_context *i_flctx;
    struct address_space    i_data;
    /* ... Security, RCU, etc. */
};
```

#### The inode_operations Vtable

```c
struct inode_operations {
    struct dentry * (*lookup)(struct inode *, struct dentry *, unsigned int);
    const char * (*get_link)(struct dentry *, struct inode *, struct delayed_call *);
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
    int (*getattr)(struct user_namespace *, const struct path *,
                   struct kstat *, u32, unsigned int);
    ssize_t (*listxattr)(struct dentry *, char *, size_t);
    int (*fiemap)(struct inode *, struct fiemap_extent_info *, u64, u64);
    int (*update_time)(struct inode *, struct timespec64 *, int);
    int (*atomic_open)(struct inode *, struct dentry *, struct file *,
                       unsigned open_flag, umode_t create_mode);
    int (*tmpfile)(struct user_namespace *, struct inode *, struct file *,
                   umode_t);
    int (*set_acl)(struct user_namespace *, struct inode *, struct posix_acl *,
                   int);
    int (*fileattr_set)(struct user_namespace *mnt_userns,
                        struct dentry *dentry, struct fileattr *fa);
    int (*fileattr_get)(struct dentry *dentry, struct fileattr *fa);
};
```

**Critical Method: `lookup`**

When the kernel resolves a path like `/home/user/file.txt`, it calls `lookup` on each directory inode with the next component name. The directory's `lookup` searches its entries (on-disk in ext4, in-memory in tmpfs) and either returns a dentry or signals ENOENT.

---

### 4.3 Dentry Object

#### Concept

A **dentry** (directory entry) is the glue between a **name** and an **inode**. It represents a single path component: a filename, a directory name, or `.` and `..`.

Dentries form a **tree structure** mirroring the directory hierarchy. Every dentry has:
- A name (`d_name`)
- A pointer to its inode (`d_inode`) — can be NULL for negative dentries
- A pointer to its parent dentry (`d_parent`)
- A pointer to the superblock (`d_sb`)
- A list of child dentries (`d_subdirs`)

#### Kernel Definition

```c
struct dentry {
    unsigned int            d_flags;        /* protected by d_lock */
    seqcount_spinlock_t     d_seq;          /* per dentry seqlock */
    struct hlist_bl_node    d_hash;         /* lookup hash list */
    struct dentry           *d_parent;      /* parent directory */
    struct qstr             d_name;         /* name: hash + len + string ptr */
    struct inode            *d_inode;       /* inode (NULL = negative dentry) */
    unsigned char           d_iname[DNAME_INLINE_LEN]; /* small name optimization */

    const struct dentry_operations *d_op;
    struct super_block      *d_sb;          /* root of the tree */
    unsigned long           d_time;         /* revalidate time */
    void                    *d_fsdata;      /* fs-specific data */

    union {
        struct list_head    d_lru;          /* LRU list */
        wait_queue_head_t   *d_wait;        /* in-lookup wait queue */
    };
    struct list_head        d_child;        /* child of parent list */
    struct list_head        d_subdirs;      /* our children */
    union {
        struct hlist_node   d_alias;        /* inode alias list */
        struct hlist_bl_node d_in_lookup_hash;
        struct rcu_head     d_rcu;
    } d_u;
};
```

#### Negative Dentries

A **negative dentry** has `d_inode == NULL`. It caches the knowledge that a particular name does *not* exist in a directory. This is a critical optimization: without negative dentries, every failed `open()` call on a nonexistent file would result in repeated disk seeks.

#### The dentry_operations Vtable

```c
struct dentry_operations {
    int (*d_revalidate)(struct dentry *, unsigned int);
    int (*d_weak_revalidate)(struct dentry *, unsigned int);
    int (*d_hash)(const struct dentry *, struct qstr *);
    int (*d_compare)(const struct dentry *, unsigned int,
                     const char *, const struct qstr *);
    int (*d_delete)(const struct dentry *);
    int (*d_init)(struct dentry *);
    void (*d_release)(struct dentry *);
    void (*d_prune)(struct dentry *);
    void (*d_iput)(struct dentry *, struct inode *);
    char *(*d_dname)(struct dentry *, char *, int);
    struct vfsmount *(*d_automount)(struct path *);
    int (*d_manage)(const struct path *, bool);
    struct dentry *(*d_real)(struct dentry *, const struct inode *);
};
```

**`d_revalidate`:** Used by network filesystems (NFS, CIFS) to check if a cached dentry is still valid. On local filesystems this is often NULL, meaning "always valid."

**`d_dname`:** Used by pseudo-filesystems to generate names dynamically. For example, `sockfs` uses this to produce names like `socket:[12345]` shown in `/proc/self/fd/`.

---

### 4.4 File Object

#### Concept

A **file** object represents an *open file description* — it is created when a process calls `open()` and destroyed when the last reference is dropped via `close()` (or process exit). It tracks:

- The **current file position** (`f_pos`)
- **Open flags** (`f_flags`: O_RDONLY, O_WRONLY, O_NONBLOCK, etc.)
- The **dentry** (and thus the inode) it refers to
- The **vfsmount** (which mount it's on)
- The **file_operations** vtable

Multiple processes can share a file object (via `fork()` or `dup2()`). Multiple file objects can point to the same inode.

#### Kernel Definition

```c
struct file {
    union {
        struct llist_node   fu_llist;
        struct rcu_head     fu_rcuhead;
    } f_u;
    struct path             f_path;         /* dentry + vfsmount */
    struct inode            *f_inode;       /* cached inode */
    const struct file_operations *f_op;    /* operations vtable */
    spinlock_t              f_lock;
    enum rw_hint            f_write_hint;
    atomic_long_t           f_count;        /* reference count */
    unsigned int            f_flags;        /* O_RDONLY, O_WRONLY, etc. */
    fmode_t                 f_mode;         /* FMODE_READ, FMODE_WRITE */
    struct mutex            f_pos_lock;
    loff_t                  f_pos;          /* current read/write position */
    struct fown_struct      f_owner;        /* for async I/O notification */
    const struct cred       *f_cred;        /* credentials at open time */
    struct file_ra_state    f_ra;           /* read-ahead state */
    u64                     f_version;
    void                    *f_security;    /* LSM security data */
    void                    *private_data;  /* fs/driver private data */
    struct address_space    *f_mapping;     /* page cache */
    errseq_t                f_wb_err;
    errseq_t                f_sb_err;
};
```

#### The file_operations Vtable

This is the most important vtable for application developers:

```c
struct file_operations {
    struct module *owner;
    loff_t (*llseek)(struct file *, loff_t, int);
    ssize_t (*read)(struct file *, char __user *, size_t, loff_t *);
    ssize_t (*write)(struct file *, const char __user *, size_t, loff_t *);
    ssize_t (*read_iter)(struct file *, struct kiocb *, struct iov_iter *);
    ssize_t (*write_iter)(struct file *, struct kiocb *, struct iov_iter *);
    int (*iopoll)(struct kiocb *kiocb, struct io_comp_batch *, unsigned int flags);
    int (*iterate)(struct file *, struct dir_context *);
    int (*iterate_shared)(struct file *, struct dir_context *);
    __poll_t (*poll)(struct file *, struct poll_table_struct *);
    long (*unlocked_ioctl)(struct file *, unsigned int, unsigned long);
    long (*compat_ioctl)(struct file *, unsigned int, unsigned long);
    int (*mmap)(struct file *, struct vm_area_struct *);
    unsigned long mmap_supported_flags;
    int (*open)(struct inode *, struct file *);
    int (*flush)(struct file *, fl_owner_t id);
    int (*release)(struct inode *, struct file *);
    int (*fsync)(struct file *, loff_t, loff_t, int datasync);
    int (*fasync)(int, struct file *, int);
    int (*lock)(struct file *, int, struct file_lock *);
    ssize_t (*sendpage)(struct file *, struct page *, int, size_t, loff_t *, int);
    unsigned long (*get_unmapped_area)(struct file *, unsigned long, unsigned long,
                                        unsigned long, unsigned long);
    int (*check_flags)(int);
    int (*setfl)(struct file *, unsigned long);
    int (*flock)(struct file *, int, struct file_lock *);
    ssize_t (*splice_write)(struct pipe_inode_info *, struct file *, loff_t *,
                            size_t, unsigned int);
    ssize_t (*splice_read)(struct file *, loff_t *, struct pipe_inode_info *,
                           size_t, unsigned int);
    int (*setlease)(struct file *, long, struct file_lock **, void **);
    long (*fallocate)(struct file *file, int mode, loff_t offset, loff_t len);
    void (*show_fdinfo)(struct seq_file *m, struct file *f);
    ssize_t (*copy_file_range)(struct file *, loff_t, struct file *, loff_t,
                               size_t, unsigned int);
    loff_t (*remap_file_range)(struct file *file_in, loff_t pos_in,
                               struct file *file_out, loff_t pos_out,
                               loff_t len, unsigned int remap_flags);
    int (*fadvise)(struct file *, loff_t, loff_t, int);
    int (*uring_cmd)(struct io_uring_cmd *ioucmd, unsigned int issue_flags);
    int (*uring_cmd_iopoll)(struct io_uring_cmd *, struct io_comp_batch *,
                            unsigned int poll_flags);
};
```

---

## 5. VFS Operations Tables (vtables)

### 5.1 The Dispatch Pattern

When a system call like `read(fd, buf, n)` arrives:

```
sys_read(fd, buf, n)
    → fdget_pos(fd)           // get struct file from fd
    → file->f_op->read_iter() // dispatch through vtable
        → ext4_file_read_iter()   (for ext4)
        → tmpfs_file_read_iter()  (for tmpfs)
        → nfs_file_read()         (for NFS)
```

This is **compile-time polymorphism through function pointers** — C's approach to virtual dispatch. The overhead is one pointer dereference, which is negligible compared to I/O.

### 5.2 Default Implementations

VFS provides default implementations for common operations. For example, `generic_file_read_iter()` implements buffered reads through the page cache and works for any filesystem that populates `address_space_operations` correctly.

```c
/* Many filesystems simply do: */
const struct file_operations ext4_file_operations = {
    .llseek         = ext4_llseek,
    .read_iter      = ext4_file_read_iter,
    .write_iter     = ext4_file_write_iter,
    .iopoll         = iocb_bio_iopoll,
    .unlocked_ioctl = ext4_ioctl,
    .mmap           = ext4_file_mmap,
    .open           = ext4_file_open,
    .release        = ext4_release_file,
    .fsync          = ext4_sync_file,
    .get_unmapped_area = thp_get_unmapped_area,
    .splice_read    = generic_file_splice_read,  /* generic! */
    .splice_write   = iter_file_splice_write,
    .fallocate      = ext4_fallocate,
};
```

---

## 6. The Path Walk: How the Kernel Resolves a Filename

### 6.1 Overview

Path resolution is called **namei** (from the historical Unix function `namei()`). It is one of the most complex parts of VFS, handling:

- Absolute vs. relative paths
- Symlink following (with loop detection, max 40 hops)
- Mount point traversal
- `.` and `..` handling across mount boundaries
- Race conditions (TOCTOU — time-of-check-time-of-use)
- RCU-mode fast path for read-only lookups

### 6.2 The Walk Data Structure

```c
struct nameidata {
    struct path     path;           /* current {dentry, vfsmount} */
    struct qstr     last;           /* last component name */
    struct path     root;           /* root for this lookup */
    struct inode    *inode;         /* inode of path.dentry */
    unsigned int    flags;          /* lookup flags */
    unsigned        seq, m_seq, r_seq; /* seqlock sequence numbers */
    int             last_type;      /* LAST_NORM, LAST_ROOT, LAST_DOT, etc. */
    unsigned        depth;          /* symlink recursion depth */
    int             total_link_count;
    struct saved {
        struct path link;
        struct delayed_call done;
        const char *name;
        unsigned seq;
    } *stack, internal[EMBEDDED_LEVELS];
    struct filename *name;
    struct nameidata *saved;
    unsigned        root_seq;
    int             dfd;            /* AT_FDCWD or directory fd */
    kuid_t          dir_uid;
    umode_t         dir_mode;
};
```

### 6.3 The Walk Algorithm (Simplified)

```
path_lookupat("/home/user/file.txt", ...)
    set nd.path = root or cwd (for absolute/relative)
    for each component in "/home/user/file.txt":
        1. Hash the component name
        2. Lock d_lock on current directory dentry
        3. Search dcache hash table for (parent_dentry, name)
        4. If found in dcache:
              use cached dentry (fast path — no disk I/O)
        5. If not found:
              call inode->i_op->lookup(dir_inode, dentry, flags)
              filesystem reads directory from disk
              creates and returns new dentry
        6. If dentry->d_inode is NULL → ENOENT
        7. If dentry->d_flags & DCACHE_MOUNTED:
              follow mount point → get new vfsmount
        8. If inode is a symlink and not final component:
              read link target, recursively walk
        9. Advance nd.path to new {dentry, vfsmount}
    return final {dentry, vfsmount}
```

### 6.4 RCU Mode: The Fast Path

For read-only path walks (common case: opening existing files), the kernel uses **RCU-mode lookup** — it walks the dentry tree *without any locks*, using sequence counters to detect concurrent modifications. If a race is detected, it falls back to the slower reference-counted walk.

This makes file opens on hot cached paths extremely fast — often just a hash lookup and a few seqlock checks with no contention.

### 6.5 Mount Point Crossing

When the walk reaches a dentry that is a mount point, the kernel must switch to the mounted filesystem:

```c
/* Simplified mount point crossing */
static int follow_mount(struct path *path) {
    while (d_mountpoint(path->dentry)) {
        struct vfsmount *mounted = lookup_mnt(path);
        if (!mounted)
            break;
        path->mnt = mounted;
        path->dentry = mounted->mnt_root;
    }
    return 0;
}
```

When crossing `..` at a mount point root, the reverse happens: the kernel must go *up* into the parent mount.

---

## 7. The Mount Subsystem

### 7.1 Architecture

The mount subsystem tracks which filesystems are mounted where. Internally, the kernel uses:

- `struct mount` (not `struct vfsmount`!) — the *real* mount structure
- `struct vfsmount` — the *public* view (embedded inside `struct mount`)
- `struct mountpoint` — represents a dentry that has something mounted on it

```c
struct mount {
    struct hlist_node   mnt_hash;
    struct mount        *mnt_parent;    /* parent mount */
    struct dentry       *mnt_mountpoint; /* dentry of mount point */
    struct vfsmount     mnt;            /* public mount info */
    union {
        struct rcu_head mnt_rcu;
        struct llist_node mnt_llist;
    };
    struct list_head    mnt_mounts;     /* child mounts */
    struct list_head    mnt_child;      /* and our position in the list */
    struct list_head    mnt_instance;   /* mount instance on sb->s_mounts */
    const char          *mnt_devname;   /* device name: "/dev/sda1" */
    struct list_head    mnt_list;
    struct list_head    mnt_expire;     /* for autofs */
    struct list_head    mnt_share;      /* circular list of shared mounts */
    struct list_head    mnt_slave_list; /* slave mounts */
    struct list_head    mnt_slave;      /* slave list entry */
    struct mount        *mnt_master;    /* master mount for slave */
    struct mnt_namespace *mnt_ns;       /* containing namespace */
    struct mountpoint   *mnt_mp;        /* where we are mounted */
    union {
        struct hlist_node mnt_mp_list;
        struct hlist_node mnt_umount;
    };
    /* ... */
    int                 mnt_id;         /* mount ID */
    int                 mnt_group_id;   /* peer group ID */
    int                 mnt_expiry_mark; /* for autofs */
    struct hlist_head   mnt_pins;
    struct hlist_head   mnt_stuck_children;
};

struct vfsmount {
    struct dentry *mnt_root;    /* root of the mounted tree */
    struct super_block *mnt_sb; /* pointer to superblock */
    int mnt_flags;              /* MNT_NOSUID, MNT_NODEV, etc. */
    struct user_namespace *mnt_userns;
};
```

### 7.2 Mount Namespaces

A **mount namespace** is a set of mount points visible to a process. Linux supports *per-process mount namespaces*, enabling the isolation used by containers.

```c
struct mnt_namespace {
    struct ns_common        ns;
    struct mount *          root;           /* root mount */
    struct rb_root          mounts;         /* tree of mounts */
    struct user_namespace   *user_ns;
    struct ucounts          *ucounts;
    u64                     seq;            /* sequence number */
    wait_queue_head_t       poll;
    u64                     event;
    unsigned int            mnt_count;
    unsigned int            pending_mounts;
};
```

**Creating a new namespace:** `unshare(CLONE_NEWNS)` or `clone(CLONE_NEWNS)`. After this, the process has its own copy of the mount tree. Changes to mounts are invisible to other namespaces (unless propagation is configured).

**Propagation types** (controlled by `mount --make-*`):
- `MS_SHARED`: mounts propagate to/from peer group
- `MS_PRIVATE`: no propagation (default after `unshare`)
- `MS_SLAVE`: receives propagation from master, does not send
- `MS_UNBINDABLE`: cannot be bind-mounted

This is the foundation of **container filesystems**: Docker's overlay filesystem is mounted in a new mount namespace isolated from the host.

### 7.3 Bind Mounts

A **bind mount** mounts one part of the filesystem tree at another point. Unlike a normal mount, it does not use a block device — it reuses an existing subtree.

```bash
mount --bind /home/user/data /mnt/data
# Now /mnt/data shows the same files as /home/user/data
# Both dentries point to the same inodes
```

In the kernel, a bind mount creates a new `struct mount` that points to the same `struct super_block` and has its `mnt_root` set to the source dentry. The source inode's `i_nlink` is NOT incremented — bind mounts don't affect the inode at all.

---

## 8. Dentry Cache (dcache)

### 8.1 Purpose

The dcache is the kernel's cache for directory entries. Without it, every path walk would require disk reads to traverse directories. The dcache allows hot paths to be resolved entirely in RAM.

### 8.2 Structure

The dcache is a **hash table** indexed by `(parent_dentry, name_hash)`. Each bucket is a `hlist_bl_head` (hash list with a bottom-bit lock).

```c
/* Global dcache hash table */
static struct hlist_bl_head *dentry_hashtable __read_mostly;
static unsigned int d_hash_shift __read_mostly;

static inline struct hlist_bl_head *d_hash(unsigned int hash)
{
    return dentry_hashtable + (hash >> d_hash_shift);
}
```

### 8.3 LRU Management

Unused dentries (not referenced by any `struct file` or ongoing path walk) are placed on a **per-superblock LRU list**. Under memory pressure, the kernel's shrinker subsystem reclaims these dentries via `prune_dcache_sb()`.

The shrinker uses a **two-stage** approach:
1. `count_objects`: reports how many dentries can potentially be freed
2. `scan_objects`: actually frees them, walking the LRU from the tail

### 8.4 The Dentry Lifecycle

```
            d_alloc()
                ↓
         [REFERENCED state]
         (actively used, in hash table)
                ↓
         dput() → last reference dropped
                ↓
         [UNUSED state]
         (in LRU, still in hash table)
                ↓
         memory pressure → shrinker
                ↓
         d_free() → returned to slab allocator
```

### 8.5 Cache Coherence

The dcache is always **coherent for local filesystems** — because file system operations (create, delete, rename) go through VFS, which updates the dcache atomically.

For **network filesystems** (NFS), cache coherence is harder: another client may have modified the directory on the server. NFS uses `d_revalidate()` to check staleness, which may require a network round-trip.

---

## 9. Inode Cache (icache)

### 9.1 Structure

The inode cache is another hash table, indexed by `(superblock, inode_number)`. It prevents re-reading inodes from disk for recently accessed files.

```c
/* inode hash table */
static struct hlist_head *inode_hashtable __read_mostly;

static inline struct hlist_head *inode_hashtable_ptr(struct super_block *sb,
                                                      unsigned long hashval)
{
    return inode_hashtable + hash_long(hashval ^ (unsigned long)sb, i_hash_shift);
}
```

### 9.2 Inode States

An inode can be in multiple states simultaneously (bit flags):

```c
#define I_DIRTY_SYNC        (1 << 0)  /* dirty, must be written to disk */
#define I_DIRTY_DATASYNC    (1 << 1)  /* critical data dirty */
#define I_DIRTY_PAGES       (1 << 2)  /* dirty pages in page cache */
#define I_NEW               (1 << 3)  /* being created */
#define I_WILL_FREE         (1 << 4)  /* being freed */
#define I_FREEING           (1 << 5)  /* being freed */
#define I_CLEAR             (1 << 6)  /* cleared (no ops possible) */
#define I_SYNC              (1 << 7)  /* being synced to disk */
#define I_REFERENCED        (1 << 8)  /* recently used */
#define I_LINKABLE          (1 << 9)  /* can be linked */
#define I_DIRTY_TIME        (1 << 11) /* times lazy-updated */
#define I_WB_SWITCH         (1 << 13) /* writeback switching */
#define I_OVL_INUSE         (1 << 14) /* used by overlayfs */
#define I_CREATING          (1 << 15) /* being created on disk */
#define I_DONTCACHE         (1 << 16) /* don't cache after last use */
#define I_SYNC_QUEUED       (1 << 17) /* sync queued */
```

### 9.3 Writeback

Dirty inodes are tracked per-superblock in a **writeback list**. The kernel's `writeback` thread periodically flushes dirty inodes to disk. You can observe this with `cat /proc/sys/vm/dirty_writeback_centisecs`.

The `address_space` embedded in each inode (`i_data`) manages the dirty pages. `writeback_control` structures coordinate the flushing policy (how many pages, by when).

---

## 10. Page Cache & Buffer Cache

### 10.1 The Page Cache

The **page cache** is the kernel's cache of file content in memory. When you `read()` a file, the kernel checks if the relevant pages are in the page cache. If yes — served from RAM. If no — read from disk, populate cache, serve from RAM.

Every cached page is associated with an `address_space` object, which belongs to an inode:

```c
struct address_space {
    struct inode            *host;          /* owner: inode or block device */
    struct xarray           i_pages;        /* cached pages (radix tree now xarray) */
    struct rw_semaphore     invalidate_lock;
    gfp_t                   gfp_mask;
    atomic_t                i_mmap_writable;
    struct rb_root_cached   i_mmap;         /* tree of VMAs mapping this file */
    struct rw_semaphore     i_mmap_rwsem;
    unsigned long           nrpages;        /* number of cached pages */
    pgoff_t                 writeback_index;
    const struct address_space_operations *a_ops;
    unsigned long           flags;
    errseq_t                wb_err;
    spinlock_t              private_lock;
    struct list_head        private_list;
    void                    *private_data;
};
```

### 10.2 address_space_operations

```c
struct address_space_operations {
    int (*writepage)(struct page *page, struct writeback_control *wbc);
    int (*readpage)(struct file *, struct page *);
    int (*writepages)(struct address_space *, struct writeback_control *);
    bool (*dirty_folio)(struct address_space *, struct folio *);
    void (*readahead)(struct readahead_control *);
    int (*write_begin)(struct file *, struct address_space *mapping,
                       loff_t pos, unsigned len, unsigned flags,
                       struct page **pagep, void **fsdata);
    int (*write_end)(struct file *, struct address_space *mapping,
                     loff_t pos, unsigned len, unsigned copied,
                     struct page *page, void *fsdata);
    sector_t (*bmap)(struct address_space *, sector_t);
    void (*invalidate_folio)(struct folio *, size_t, size_t);
    bool (*release_folio)(struct folio *, gfp_t);
    void (*free_folio)(struct folio *);
    ssize_t (*direct_IO)(struct kiocb *, struct iov_iter *iter);
    int (*migrate_folio)(struct address_space *, struct folio *, struct folio *,
                         enum migrate_mode);
    int (*launder_folio)(struct folio *);
    bool (*is_partially_uptodate)(struct folio *, size_t, size_t);
    void (*is_dirty_writeback)(struct folio *, bool *, bool *);
    int (*error_remove_page)(struct address_space *, struct page *);
    int (*swap_activate)(struct swap_info_struct *, struct file *, sector_t *);
    void (*swap_deactivate)(struct file *);
    int (*swap_rw)(struct kiocb *iocb, struct iov_iter *iter);
};
```

### 10.3 Unified Page Cache (No More Buffer Cache)

In old Linux kernels, there were two separate caches:
- **Page cache**: for file data
- **Buffer cache**: for block device metadata (superblocks, inode blocks, directory blocks)

Since Linux 2.4, these are **unified**. Block device buffers are just pages in the block device's own `address_space`. The `buffer_head` structure still exists for tracking sub-page block alignments (a "buffer" is a page slice corresponding to one block), but all actual caching goes through the page cache.

### 10.4 The XArray (Radix Tree)

Pages in the cache are indexed by their **page offset within the file** (a `pgoff_t`, which is `page_number = file_offset / PAGE_SIZE`). They are stored in an **XArray** (the modern replacement for the radix tree), allowing O(1) lookup by page index.

### 10.5 Read Path (Simplified)

```
read(fd, buf, count)
    → vfs_read()
    → file->f_op->read_iter()
    → generic_file_read_iter()
        → filemap_read()
            → find_get_pages_contig()   // look in page cache
            → if pages found:
                  copy_page_to_iter()   // copy to user buffer
            → if pages missing:
                  page_cache_sync_readahead()  // trigger readahead
                  add_to_page_cache_lru()      // allocate page
                  mapping->a_ops->readpage()   // ask filesystem to fill it
                      → ext4_readpage()
                          → mpage_readpage()
                              → submit_bio()    // issue block I/O
                  wait_on_page_locked()        // sleep until I/O done
                  copy_page_to_iter()          // copy to user buffer
```

### 10.6 Write Path

```
write(fd, buf, count)
    → generic_file_write_iter()
        → generic_perform_write()
            → mapping->a_ops->write_begin()  // prepare page (lock it)
                → grab_cache_page_write_begin()  // get/create page
            → copy_from_iter_advance()           // copy from user
            → mapping->a_ops->write_end()        // mark page dirty
                → block_write_end()
                    → __mark_inode_dirty()       // mark inode dirty
```

The page is now **dirty in RAM** — it has NOT been written to disk. The writeback subsystem will flush it later. `fsync()` forces immediate writeback.

---

## 11. File Descriptors & the Open File Table

### 11.1 Three-Level Indirection

```
Process                 Kernel
─────────────────────────────────────────
task_struct
  └── files (struct files_struct)
        └── fdt (struct fdtable)
              └── fd[] (array of file*)
                    ↓
              struct file           (open file description)
                    ↓
              struct dentry + vfsmount
                    ↓
              struct inode
```

### 11.2 The files_struct

```c
struct files_struct {
    atomic_t        count;          /* reference count (shared after fork) */
    bool            resize_in_progress;
    wait_queue_head_t resize_wait;
    struct fdtable __rcu *fdt;      /* pointer to current fd table */
    struct fdtable  fdtab;          /* embedded small fd table */
    unsigned int    next_fd;        /* hint for next free fd */
    unsigned long   close_on_exec_init[1];
    unsigned long   open_fds_init[1];
    unsigned long   full_fds_bits_init[1];
    struct file __rcu * fd_array[NR_OPEN_DEFAULT]; /* initial fd array (64 entries) */
};
```

**Key subtlety:** After `fork()`, parent and child share the *same* `struct file` objects for their open files. This means they share `f_pos` — seeking in one affects the other. This is why shells must `dup()` file descriptors to independent positions after forking.

### 11.3 The O_CLOEXEC Flag

When `execve()` is called, all file descriptors with `O_CLOEXEC` (or `FD_CLOEXEC`) are closed. This prevents unintended file descriptor leaks into child processes. The kernel tracks this with the `close_on_exec` bitmap in `fdtable`.

### 11.4 File Descriptor Limits

- Per-process soft limit: `ulimit -n` (default often 1024)
- Per-process hard limit: `ulimit -Hn` (often 1048576 in modern systems)
- System-wide limit: `/proc/sys/fs/file-max`
- Currently open system-wide: `/proc/sys/fs/file-nr`

---

## 12. System Calls: From User Space to VFS

### 12.1 The open() System Call

```c
/* User space: */
int fd = open("/path/to/file", O_RDWR | O_CREAT, 0644);

/* Kernel entry point (simplified): */
SYSCALL_DEFINE3(open, const char __user *, filename, int, flags, umode_t, mode)
{
    return do_sys_open(AT_FDCWD, filename, flags, mode);
}

long do_sys_open(int dfd, const char __user *filename, int flags, umode_t mode)
{
    struct open_how how = build_open_how(flags, mode);
    return do_sys_openat2(dfd, filename, &how);
}

static long do_sys_openat2(int dfd, const char __user *filename,
                            struct open_how *how)
{
    /* 1. Copy filename from user space */
    tmp = getname(filename);

    /* 2. Get a free file descriptor */
    fd = get_unused_fd_flags(how->flags);

    /* 3. Open the file, creating struct file */
    f = do_filp_open(dfd, tmp, &op);

    /* 4. Install the file into the fd table */
    fd_install(fd, f);

    return fd;
}
```

### 12.2 do_filp_open: The Heart of open()

```c
struct file *do_filp_open(int dfd, struct filename *pathname,
                           const struct open_flags *op)
{
    struct nameidata nd;
    /* ... */
    /* 1. Walk the path (namei) */
    /* 2. Call do_open() → vfs_open() */
    /* 3. vfs_open() calls file->f_op->open() */
    /* 4. Security checks (LSM hooks) */
    /* 5. Return struct file */
}
```

### 12.3 The read() System Call

```c
SYSCALL_DEFINE3(read, unsigned int, fd, char __user *, buf, size_t, count)
{
    struct fd f = fdget_pos(fd);           /* get file, increment f_pos lock */
    if (!f.file)
        return -EBADF;

    loff_t pos, *ppos = file_ppos(f.file); /* get position */
    if (ppos) {
        pos = *ppos;
        ppos = &pos;
    }

    ret = vfs_read(f.file, buf, count, ppos); /* dispatch to VFS */

    if (ret >= 0 && ppos)
        f.file->f_pos = pos;               /* update position */

    fdput_pos(f);
    return ret;
}

ssize_t vfs_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
    /* Permission checks */
    if (!(file->f_mode & FMODE_READ))
        return -EBADF;

    /* Size sanity */
    ret = rw_verify_area(READ, file, pos, count);

    /* LSM security hook */
    ret = security_file_permission(file, MAY_READ);

    /* Dispatch */
    if (file->f_op->read)
        ret = file->f_op->read(file, buf, count, pos);
    else if (file->f_op->read_iter)
        ret = new_sync_read(file, buf, count, pos);
    else
        ret = -EINVAL;

    return ret;
}
```

### 12.4 The stat() System Call

```c
SYSCALL_DEFINE2(stat, const char __user *, filename, struct __old_kernel_stat __user *, statbuf)
{
    struct kstat stat;
    /* 1. Resolve path */
    /* 2. Call vfs_stat() → vfs_getattr() → inode->i_op->getattr() */
    /* 3. Copy kstat to user space */
}

int vfs_getattr(const struct path *path, struct kstat *stat, u32 request_mask,
                unsigned int query_flags)
{
    /* Call filesystem-specific getattr */
    if (inode->i_op->getattr)
        return inode->i_op->getattr(&init_user_ns, path, stat,
                                    request_mask, query_flags);
    /* Default: fill from inode fields */
    generic_fillattr(&init_user_ns, inode, stat);
    return 0;
}
```

---

## 13. Pseudo Filesystems Deep Dive

Pseudo-filesystems don't store data on disk. They generate content dynamically, representing kernel state, devices, or transient data. They are registered with `register_filesystem()` but their `mount` callback returns in-memory structures.

### 13.1 procfs (/proc)

#### Purpose

`procfs` exposes process information, kernel parameters, and system state as a virtual directory tree. Every running process gets a directory `/proc/<pid>/`.

#### Architecture

procfs uses a combination of `proc_dir_entry` structures for static entries and per-process entries generated dynamically:

```c
struct proc_dir_entry {
    atomic_t            in_use;         /* module reference count */
    refcount_t          refcnt;
    struct list_head    pde_openers;
    spinlock_t          pde_unload_lock;
    struct completion   *pde_unload_completion;
    const struct inode_operations *proc_iops;
    union {
        const struct proc_ops *proc_ops;
        const struct file_operations *proc_dir_ops;
    };
    const struct dentry_operations *proc_dops;
    union {
        const struct seq_operations *seq_ops;
        int (*single_show)(struct seq_file *, void *);
    };
    proc_write_t        write;
    void                *data;
    unsigned int        state_size;
    unsigned int        low_ino;
    nlink_t             nlink;
    kuid_t              uid;
    kgid_t              gid;
    loff_t              size;
    struct proc_dir_entry *parent;
    struct rb_node      subdir;
    struct rb_root      subdir_root;
    char                *name;
    umode_t             mode;
    u8                  flags;
    u8                  namelen;
    char                inline_name[];
};
```

#### Key /proc Entries

- `/proc/<pid>/maps` — virtual memory map of the process
- `/proc/<pid>/fd/` — directory of symlinks to open file descriptors
- `/proc/<pid>/status` — human-readable process status
- `/proc/<pid>/smaps` — detailed memory mapping statistics
- `/proc/<pid>/mem` — direct access to process memory (privileged)
- `/proc/<pid>/exe` — symlink to the executable
- `/proc/<pid>/cmdline` — null-separated command line
- `/proc/sys/` — sysctl parameters (readable/writable kernel tunables)
- `/proc/net/` — networking statistics
- `/proc/self/` — symlink to current process's `/proc/<pid>/`

#### Creating a proc entry in C:

```c
#include <linux/proc_fs.h>
#include <linux/seq_file.h>

static int mymodule_show(struct seq_file *m, void *v)
{
    seq_printf(m, "Hello from kernel module!\n");
    seq_printf(m, "jiffies = %lu\n", jiffies);
    return 0;
}

static int mymodule_open(struct inode *inode, struct file *file)
{
    return single_open(file, mymodule_show, NULL);
}

static const struct proc_ops mymodule_proc_ops = {
    .proc_open    = mymodule_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

static int __init mymodule_init(void)
{
    proc_create("mymodule", 0444, NULL, &mymodule_proc_ops);
    return 0;
}

static void __exit mymodule_exit(void)
{
    remove_proc_entry("mymodule", NULL);
}

module_init(mymodule_init);
module_exit(mymodule_exit);
```

#### /proc/sys and sysctl

`/proc/sys` exposes the **sysctl** interface. Reading `/proc/sys/vm/swappiness` shows the current swappiness value. Writing to it changes the kernel parameter in real time.

Each sysctl entry is backed by a `ctl_table` structure:

```c
static struct ctl_table vm_table[] = {
    {
        .procname   = "swappiness",
        .data       = &vm_swappiness,
        .maxlen     = sizeof(vm_swappiness),
        .mode       = 0644,
        .proc_handler = proc_dointvec_minmax,
        .extra1     = SYSCTL_ZERO,
        .extra2     = (void *)&one_hundred,
    },
    /* ... */
};
```

### 13.2 sysfs (/sys)

#### Purpose

`sysfs` exports the **kernel object (kobject) hierarchy** as a filesystem. It provides a structured view of:
- Devices (`/sys/devices/`)
- Buses (`/sys/bus/`)
- Drivers (`/sys/bus/*/drivers/`)
- Kernel modules (`/sys/module/`)
- Power management (`/sys/power/`)
- Block devices (`/sys/block/`)

#### Architecture

sysfs is built on the **kobject** infrastructure:

```c
struct kobject {
    const char          *name;
    struct list_head    entry;
    struct kobject      *parent;
    struct kset         *kset;
    struct kobj_type    *ktype;
    struct kernfs_node  *sd;    /* sysfs directory node */
    struct kref         kref;   /* reference count */
    unsigned int        state_initialized:1;
    unsigned int        state_in_sysfs:1;
    unsigned int        state_add_uevent_sent:1;
    unsigned int        state_remove_uevent_sent:1;
    unsigned int        uevent_suppress:1;
};
```

#### sysfs Attributes

Each file in sysfs is a **kobject attribute**:

```c
struct attribute {
    const char  *name;
    umode_t     mode;
};

struct kobj_attribute {
    struct attribute attr;
    ssize_t (*show)(struct kobject *kobj, struct kobj_attribute *attr, char *buf);
    ssize_t (*store)(struct kobject *kobj, struct kobj_attribute *attr,
                     const char *buf, size_t count);
};
```

Example: creating a sysfs entry:

```c
static ssize_t myattr_show(struct kobject *kobj, struct kobj_attribute *attr,
                            char *buf)
{
    return sprintf(buf, "%d\n", my_value);
}

static ssize_t myattr_store(struct kobject *kobj, struct kobj_attribute *attr,
                             const char *buf, size_t count)
{
    sscanf(buf, "%d", &my_value);
    return count;
}

static struct kobj_attribute my_attribute =
    __ATTR(my_value, 0664, myattr_show, myattr_store);

static struct kobject *my_kobject;

static int __init mymodule_init(void)
{
    my_kobject = kobject_create_and_add("mymodule", kernel_kobj);
    sysfs_create_file(my_kobject, &my_attribute.attr);
    return 0;
}
```

#### kernfs: The sysfs Backend

Modern sysfs is built on **kernfs**, a generic in-kernel filesystem layer. kernfs handles:
- The VFS glue (superblock, inodes, dentries)
- Synchronization for attribute show/store callbacks
- File polling

This means sysfs attributes don't need to implement VFS objects directly — they just provide `show` and `store` callbacks.

### 13.3 tmpfs

#### Purpose

`tmpfs` is a **memory-backed filesystem**. It stores files in the page cache, with optional swap backing. It appears as a real filesystem but all data is lost on unmount.

Common uses:
- `/tmp` (on many modern distros)
- `/dev/shm` (POSIX shared memory)
- Container overlay layers
- Runtime directories

#### Architecture

tmpfs is one of the most important VFS examples because it implements the full VFS interface without a block device:

```c
/* tmpfs inode allocation */
static struct inode *shmem_get_inode(struct super_block *sb, const struct inode *dir,
                                     umode_t mode, dev_t dev, unsigned long flags)
{
    struct inode *inode;
    struct shmem_inode_info *info;
    struct shmem_sb_info *sbinfo = SHMEM_SB(sb);

    inode = new_inode(sb);
    if (inode) {
        inode->i_ino = get_next_ino();
        inode_init_owner(&init_user_ns, inode, dir, mode);
        inode->i_blocks = 0;
        inode->i_atime = inode->i_mtime = inode->i_ctime = current_time(inode);

        info = SHMEM_I(inode);
        memset(info, 0, (char *)inode - (char *)info);
        spin_lock_init(&info->lock);
        atomic_set(&info->stop_eviction, 0);
        info->seals = F_SEAL_SEAL;

        switch (mode & S_IFMT) {
        case S_IFREG:
            inode->i_mapping->a_ops = &shmem_aops;
            inode->i_op = &shmem_inode_operations;
            inode->i_fop = &shmem_file_operations;
            /* ... */
            break;
        case S_IFDIR:
            inc_nlink(inode);
            inode->i_op = &shmem_dir_inode_operations;
            inode->i_fop = &simple_dir_operations;
            break;
        case S_IFLNK:
            inode->i_op = &shmem_symlink_inode_operations;
            break;
        }
    }
    return inode;
}
```

#### tmpfs and memfd_create

`memfd_create()` creates an anonymous tmpfs file:

```c
int fd = memfd_create("my_buffer", MFD_CLOEXEC);
ftruncate(fd, 4096);
void *ptr = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
```

This creates a file that exists only in memory, can be shared between processes via the file descriptor, and supports sealing (`F_ADD_SEALS`) to prevent modification.

### 13.4 devtmpfs (/dev)

`devtmpfs` is a tmpfs instance that the kernel automatically populates with device nodes as hardware is detected. `udev` then applies rules (permissions, symlinks, renaming) on top.

```c
/* kernel/driver/base/devtmpfs.c */
int devtmpfs_create_node(struct device *dev)
{
    /* kernel thread creates device node: */
    /* mknod(path, mode | device_type, devt) */
}
```

### 13.5 cgroupfs

`cgroupfs` (v1 and v2) exposes the **cgroup hierarchy** that controls resource limits for process groups:

- `/sys/fs/cgroup/memory/` — memory limits
- `/sys/fs/cgroup/cpu/` — CPU scheduling
- `/sys/fs/cgroup/blkio/` — block I/O limits

cgroup v2 (`cgroupv2`) uses a unified hierarchy under `/sys/fs/cgroup/`. Each file represents a control knob or statistic:

```bash
echo 100M > /sys/fs/cgroup/mygroup/memory.max
echo $$ > /sys/fs/cgroup/mygroup/cgroup.procs
```

### 13.6 pipefs & sockfs

**pipefs** is the filesystem backing pipes. When you call `pipe(fds)`, the kernel mounts pipefs (privately) and creates two file objects pointing to the same pipe inode:

```c
/* fs/pipe.c */
static struct file_system_type pipe_fs_type = {
    .name       = "pipefs",
    .mount      = pipefs_mount,
    .kill_sb    = kill_anon_super,
};

/* Pipe inode lives in pipefs, accessed through anonymous file objects */
```

**sockfs** similarly backs socket file descriptors. When you call `socket()`, you get an fd pointing to a sockfs inode. The `struct socket` is embedded in the inode's private data.

The key insight: **everything in Unix is a file because every kernel object, even a pipe or socket, can be represented as a VFS inode**. The `dentry_operations.d_dname` callback generates the visible name (e.g., `pipe:[12345]`) when `/proc/self/fd/N` is read.

---

## 14. Implementing a Minimal Filesystem in C

Let's build a complete, loadable minimal filesystem module — `simplefs` — that demonstrates all VFS concepts.

```c
/* simplefs.c - A minimal VFS filesystem module */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/slab.h>
#include <linux/statfs.h>
#include <linux/seq_file.h>
#include <linux/pagemap.h>

#define SIMPLEFS_MAGIC  0x53494D50  /* 'SIMP' */

/* ============================================================
 * INODE OPERATIONS
 * ============================================================ */

static const struct inode_operations simplefs_inode_ops;
static const struct file_operations simplefs_file_ops;
static const struct file_operations simplefs_dir_ops;
static const struct address_space_operations simplefs_aops;

/* ============================================================
 * SUPERBLOCK OPERATIONS
 * ============================================================ */

static struct inode *simplefs_alloc_inode(struct super_block *sb)
{
    struct inode *inode = new_inode(sb);
    if (!inode)
        return NULL;

    inode_init_once(inode);
    return inode;
}

static void simplefs_destroy_inode(struct inode *inode)
{
    /* In a real filesystem, free embedded private data here */
}

static int simplefs_statfs(struct dentry *dentry, struct kstatfs *buf)
{
    buf->f_type     = SIMPLEFS_MAGIC;
    buf->f_bsize    = PAGE_SIZE;
    buf->f_blocks   = 0;   /* dynamic — we're memory-backed */
    buf->f_bfree    = 0;
    buf->f_bavail   = 0;
    buf->f_namelen  = NAME_MAX;
    return 0;
}

static int simplefs_show_options(struct seq_file *m, struct dentry *root)
{
    seq_puts(m, ",simplefs");
    return 0;
}

static const struct super_operations simplefs_super_ops = {
    .alloc_inode    = simplefs_alloc_inode,
    .destroy_inode  = simplefs_destroy_inode,
    .statfs         = simplefs_statfs,
    .drop_inode     = generic_delete_inode,
    .show_options   = simplefs_show_options,
};

/* ============================================================
 * FILE OPERATIONS (regular files)
 * ============================================================ */

static ssize_t simplefs_read(struct file *file, char __user *buf,
                              size_t count, loff_t *pos)
{
    return generic_file_read_iter(/* ... */);
}

static ssize_t simplefs_write(struct file *file, const char __user *buf,
                               size_t count, loff_t *pos)
{
    return generic_file_write_iter(/* ... */);
}

static const struct file_operations simplefs_file_ops = {
    .owner      = THIS_MODULE,
    .read_iter  = generic_file_read_iter,
    .write_iter = generic_file_write_iter,
    .mmap       = generic_file_mmap,
    .fsync      = generic_file_fsync,
    .splice_read= generic_file_splice_read,
    .llseek     = generic_file_llseek,
};

/* ============================================================
 * DIRECTORY OPERATIONS
 * ============================================================ */

/*
 * lookup: called when walking into a directory.
 * We use dcache-backed simple directory (like ramfs).
 */
static struct dentry *simplefs_lookup(struct inode *dir,
                                       struct dentry *dentry,
                                       unsigned int flags)
{
    /* simple_lookup handles dcache-based lookup */
    return simple_lookup(dir, dentry, flags);
}

static int simplefs_create(struct user_namespace *mnt_userns,
                            struct inode *dir, struct dentry *dentry,
                            umode_t mode, bool excl)
{
    struct inode *inode;
    struct super_block *sb = dir->i_sb;

    /* Allocate a new inode */
    inode = new_inode(sb);
    if (!inode)
        return -ENOMEM;

    /* Initialize the inode */
    inode->i_ino     = get_next_ino();
    inode->i_mode    = mode;
    inode->i_uid     = current_fsuid();
    inode->i_gid     = current_fsgid();
    inode->i_atime   = inode->i_mtime = inode->i_ctime = current_time(inode);
    inode->i_op      = &simplefs_inode_ops;
    inode->i_fop     = &simplefs_file_ops;
    inode->i_mapping->a_ops = &simplefs_aops;

    /* Link inode to dentry */
    d_instantiate(dentry, inode);

    /* Mark parent directory as modified */
    dir->i_mtime = dir->i_ctime = current_time(dir);
    mark_inode_dirty(dir);

    return 0;
}

static int simplefs_mkdir(struct user_namespace *mnt_userns,
                           struct inode *dir, struct dentry *dentry,
                           umode_t mode)
{
    int ret;

    /* Call create with directory mode */
    ret = simplefs_create(mnt_userns, dir, dentry, mode | S_IFDIR, false);
    if (ret)
        return ret;

    /* Set directory-specific fields */
    struct inode *inode = d_inode(dentry);
    inode->i_fop = &simplefs_dir_ops;
    inode->i_op  = &simplefs_inode_ops;
    inc_nlink(dir);   /* account for ".." link */

    return 0;
}

static int simplefs_unlink(struct inode *dir, struct dentry *dentry)
{
    struct inode *inode = d_inode(dentry);

    inode->i_ctime = dir->i_ctime = dir->i_mtime = current_time(inode);
    drop_nlink(inode);          /* decrement link count */
    dput(dentry);               /* release dentry reference */
    return 0;
}

static const struct inode_operations simplefs_inode_ops = {
    .lookup = simplefs_lookup,
    .create = simplefs_create,
    .mkdir  = simplefs_mkdir,
    .unlink = simplefs_unlink,
    .link   = simple_link,
    .rmdir  = simple_rmdir,
    .rename = simple_rename,
};

static const struct file_operations simplefs_dir_ops = {
    .owner      = THIS_MODULE,
    .open       = dcache_dir_open,
    .release    = dcache_dir_close,
    .llseek     = dcache_dir_lseek,
    .read       = generic_read_dir,
    .iterate_shared = dcache_readdir,
    .fsync      = noop_fsync,
};

/* ============================================================
 * ADDRESS SPACE OPERATIONS
 * ============================================================ */

static const struct address_space_operations simplefs_aops = {
    .readpage       = simple_readpage,
    .write_begin    = simple_write_begin,
    .write_end      = simple_write_end,
    .dirty_folio    = noop_dirty_folio,
};

/* ============================================================
 * MOUNT: fill superblock
 * ============================================================ */

static int simplefs_fill_super(struct super_block *sb, void *data, int silent)
{
    struct inode *root_inode;
    struct dentry *root_dentry;

    /* Configure superblock */
    sb->s_magic     = SIMPLEFS_MAGIC;
    sb->s_op        = &simplefs_super_ops;
    sb->s_blocksize = PAGE_SIZE;
    sb->s_blocksize_bits = PAGE_SHIFT;
    sb->s_maxbytes  = MAX_LFS_FILESIZE;
    sb->s_time_gran = 1;

    /* Create root inode */
    root_inode = new_inode(sb);
    if (!root_inode)
        return -ENOMEM;

    root_inode->i_ino   = 1;
    root_inode->i_mode  = S_IFDIR | 0755;
    root_inode->i_uid   = GLOBAL_ROOT_UID;
    root_inode->i_gid   = GLOBAL_ROOT_GID;
    root_inode->i_atime = root_inode->i_mtime = root_inode->i_ctime
                        = current_time(root_inode);
    root_inode->i_op    = &simplefs_inode_ops;
    root_inode->i_fop   = &simplefs_dir_ops;
    set_nlink(root_inode, 2);  /* "." and parent reference */

    /* Create root dentry */
    root_dentry = d_make_root(root_inode);
    if (!root_dentry)
        return -ENOMEM;

    sb->s_root = root_dentry;
    return 0;
}

static struct dentry *simplefs_mount(struct file_system_type *fs_type,
                                      int flags, const char *dev_name,
                                      void *data)
{
    return mount_nodev(fs_type, flags, data, simplefs_fill_super);
}

static struct file_system_type simplefs_type = {
    .owner      = THIS_MODULE,
    .name       = "simplefs",
    .mount      = simplefs_mount,
    .kill_sb    = kill_litter_super,  /* cleans up all dentries on unmount */
};

/* ============================================================
 * MODULE INIT/EXIT
 * ============================================================ */

static int __init simplefs_init(void)
{
    int ret = register_filesystem(&simplefs_type);
    if (ret)
        printk(KERN_ERR "simplefs: failed to register: %d\n", ret);
    else
        printk(KERN_INFO "simplefs: registered\n");
    return ret;
}

static void __exit simplefs_exit(void)
{
    unregister_filesystem(&simplefs_type);
    printk(KERN_INFO "simplefs: unregistered\n");
}

module_init(simplefs_init);
module_exit(simplefs_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("You");
MODULE_DESCRIPTION("A minimal VFS filesystem demonstration");
```

**Usage after building and loading:**
```bash
insmod simplefs.ko
mkdir /mnt/test
mount -t simplefs none /mnt/test
ls /mnt/test
echo "hello" > /mnt/test/file.txt
cat /mnt/test/file.txt
umount /mnt/test
rmmod simplefs
```

---

## 15. FUSE: Filesystems in Userspace

### 15.1 Architecture

FUSE allows implementing filesystems in userspace. The kernel FUSE module acts as a bridge: it receives VFS calls, packages them as messages, sends them to a userspace daemon via `/dev/fuse`, waits for the response, then returns it to VFS.

```
VFS Call
    ↓
fuse.ko (kernel module)
    ↓ writes request to /dev/fuse
Userspace daemon reads request
    ↓ processes it (stat, read, write, readdir, ...)
Userspace daemon writes reply to /dev/fuse
    ↑
fuse.ko receives reply
    ↑
VFS returns to caller
```

### 15.2 Performance Considerations

FUSE incurs overhead from:
- Context switches between kernel and userspace (at least 2 per operation)
- Memory copies for data
- The `/dev/fuse` read/write protocol

Modern FUSE mitigations:
- **`splice`**: zero-copy for large reads/writes
- **`FUSE_CAP_WRITEBACK_CACHE`**: write buffering in kernel
- **`FUSE_CAP_PARALLEL_DIROPS`**: parallel directory operations
- **`io_uring`** integration (FUSE over io_uring)

---

## 16. Implementing a FUSE Filesystem in C

Using `libfuse3`:

```c
/*
 * memfs.c — A simple in-memory FUSE filesystem
 * Compile: gcc -Wall memfs.c $(pkg-config fuse3 --cflags --libs) -o memfs
 * Mount:   ./memfs /mnt/point
 * Unmount: fusermount3 -u /mnt/point
 */

#define FUSE_USE_VERSION 31
#include <fuse3/fuse.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <time.h>

/* ============================================================
 * In-memory inode representation
 * ============================================================ */

#define MAX_INODES  1024
#define MAX_NAME    256
#define MAX_DATA    65536

typedef enum { FT_DIR, FT_REG } file_type_t;

typedef struct memfs_inode {
    ino_t           ino;
    file_type_t     type;
    mode_t          mode;
    uid_t           uid;
    gid_t           gid;
    struct timespec atime, mtime, ctime;
    off_t           size;
    char            *data;          /* for regular files */
    /* For directories: list of (name, ino) pairs */
    struct dirent_entry {
        char        name[MAX_NAME];
        ino_t       ino;
    } *entries;
    int             entry_count;
    nlink_t         nlink;
} memfs_inode_t;

static memfs_inode_t inodes[MAX_INODES];
static int inode_count = 0;

/* ============================================================
 * Inode helpers
 * ============================================================ */

static ino_t alloc_inode(file_type_t type, mode_t mode)
{
    if (inode_count >= MAX_INODES) return -1;
    int idx = inode_count++;
    memfs_inode_t *in = &inodes[idx];
    memset(in, 0, sizeof(*in));
    in->ino  = idx + 1;     /* inodes start at 1 */
    in->type = type;
    in->mode = mode;
    in->uid  = getuid();
    in->gid  = getgid();
    clock_gettime(CLOCK_REALTIME, &in->atime);
    in->mtime = in->ctime = in->atime;
    in->nlink = (type == FT_DIR) ? 2 : 1;
    if (type == FT_REG) {
        in->data = calloc(1, MAX_DATA);
    } else {
        in->entries = calloc(64, sizeof(*in->entries));
    }
    return in->ino;
}

static memfs_inode_t *get_inode(ino_t ino)
{
    if (ino < 1 || ino > inode_count) return NULL;
    return &inodes[ino - 1];
}

static ino_t dir_lookup(memfs_inode_t *dir, const char *name)
{
    for (int i = 0; i < dir->entry_count; i++) {
        if (strcmp(dir->entries[i].name, name) == 0)
            return dir->entries[i].ino;
    }
    return 0;
}

static void dir_add(memfs_inode_t *dir, const char *name, ino_t ino)
{
    struct dirent_entry *e = &dir->entries[dir->entry_count++];
    strncpy(e->name, name, MAX_NAME - 1);
    e->ino = ino;
}

/* Resolve path to inode */
static memfs_inode_t *path_to_inode(const char *path)
{
    if (strcmp(path, "/") == 0)
        return get_inode(1);  /* root is inode 1 */

    /* Walk components */
    char tmp[4096];
    strncpy(tmp, path + 1, sizeof(tmp) - 1);  /* skip leading '/' */

    memfs_inode_t *dir = get_inode(1);
    char *saveptr, *comp = strtok_r(tmp, "/", &saveptr);

    while (comp) {
        if (dir->type != FT_DIR) return NULL;
        ino_t child_ino = dir_lookup(dir, comp);
        if (!child_ino) return NULL;
        dir = get_inode(child_ino);
        comp = strtok_r(NULL, "/", &saveptr);
    }
    return dir;
}

/* ============================================================
 * FUSE Operations
 * ============================================================ */

static void inode_to_stat(memfs_inode_t *in, struct stat *st)
{
    memset(st, 0, sizeof(*st));
    st->st_ino   = in->ino;
    st->st_mode  = in->mode | (in->type == FT_DIR ? S_IFDIR : S_IFREG);
    st->st_nlink = in->nlink;
    st->st_uid   = in->uid;
    st->st_gid   = in->gid;
    st->st_size  = in->size;
    st->st_atim  = in->atime;
    st->st_mtim  = in->mtime;
    st->st_ctim  = in->ctime;
    st->st_blksize = 4096;
    st->st_blocks  = (in->size + 511) / 512;
}

static int memfs_getattr(const char *path, struct stat *st,
                          struct fuse_file_info *fi)
{
    memfs_inode_t *in = path_to_inode(path);
    if (!in) return -ENOENT;
    inode_to_stat(in, st);
    return 0;
}

static int memfs_readdir(const char *path, void *buf, fuse_fill_dir_t filler,
                          off_t offset, struct fuse_file_info *fi,
                          enum fuse_readdir_flags flags)
{
    memfs_inode_t *dir = path_to_inode(path);
    if (!dir || dir->type != FT_DIR) return -ENOENT;

    filler(buf, ".", NULL, 0, 0);
    filler(buf, "..", NULL, 0, 0);

    for (int i = 0; i < dir->entry_count; i++) {
        struct stat st;
        memfs_inode_t *child = get_inode(dir->entries[i].ino);
        if (child) {
            inode_to_stat(child, &st);
            filler(buf, dir->entries[i].name, &st, 0, 0);
        }
    }
    return 0;
}

static int memfs_create(const char *path, mode_t mode,
                         struct fuse_file_info *fi)
{
    /* Split path into parent dir + filename */
    char dirpath[4096], *filename;
    strncpy(dirpath, path, sizeof(dirpath) - 1);
    filename = strrchr(dirpath, '/');
    if (!filename) return -EINVAL;

    *filename++ = '\0';
    const char *parent_path = (dirpath[0] == '\0') ? "/" : dirpath;

    memfs_inode_t *parent = path_to_inode(parent_path);
    if (!parent || parent->type != FT_DIR) return -ENOENT;
    if (dir_lookup(parent, filename)) return -EEXIST;

    ino_t new_ino = alloc_inode(FT_REG, mode);
    if (new_ino < 0) return -ENOSPC;

    dir_add(parent, filename, new_ino);
    clock_gettime(CLOCK_REALTIME, &parent->mtime);
    return 0;
}

static int memfs_mkdir(const char *path, mode_t mode)
{
    char dirpath[4096], *dirname;
    strncpy(dirpath, path, sizeof(dirpath) - 1);
    dirname = strrchr(dirpath, '/');
    if (!dirname) return -EINVAL;
    *dirname++ = '\0';

    const char *parent_path = (dirpath[0] == '\0') ? "/" : dirpath;
    memfs_inode_t *parent = path_to_inode(parent_path);
    if (!parent || parent->type != FT_DIR) return -ENOENT;

    ino_t new_ino = alloc_inode(FT_DIR, mode | S_IFDIR);
    if (new_ino < 0) return -ENOSPC;

    dir_add(parent, dirname, new_ino);
    parent->nlink++;  /* for new ".." */
    return 0;
}

static int memfs_read(const char *path, char *buf, size_t size, off_t offset,
                       struct fuse_file_info *fi)
{
    memfs_inode_t *in = path_to_inode(path);
    if (!in || in->type != FT_REG) return -ENOENT;

    if (offset >= in->size) return 0;
    if (offset + (off_t)size > in->size)
        size = in->size - offset;

    memcpy(buf, in->data + offset, size);
    clock_gettime(CLOCK_REALTIME, &in->atime);
    return (int)size;
}

static int memfs_write(const char *path, const char *buf, size_t size,
                        off_t offset, struct fuse_file_info *fi)
{
    memfs_inode_t *in = path_to_inode(path);
    if (!in || in->type != FT_REG) return -ENOENT;

    if (offset + (off_t)size > MAX_DATA) return -ENOSPC;

    memcpy(in->data + offset, buf, size);
    if (offset + (off_t)size > in->size)
        in->size = offset + size;

    clock_gettime(CLOCK_REALTIME, &in->mtime);
    in->ctime = in->mtime;
    return (int)size;
}

static int memfs_truncate(const char *path, off_t size,
                           struct fuse_file_info *fi)
{
    memfs_inode_t *in = path_to_inode(path);
    if (!in || in->type != FT_REG) return -ENOENT;
    if (size > MAX_DATA) return -ENOSPC;

    if (size > in->size)
        memset(in->data + in->size, 0, size - in->size);
    in->size = size;
    clock_gettime(CLOCK_REALTIME, &in->mtime);
    return 0;
}

static int memfs_unlink(const char *path)
{
    char dirpath[4096], *filename;
    strncpy(dirpath, path, sizeof(dirpath) - 1);
    filename = strrchr(dirpath, '/');
    if (!filename) return -EINVAL;
    *filename++ = '\0';

    const char *parent_path = (dirpath[0] == '\0') ? "/" : dirpath;
    memfs_inode_t *parent = path_to_inode(parent_path);
    if (!parent) return -ENOENT;

    /* Remove from directory entries */
    for (int i = 0; i < parent->entry_count; i++) {
        if (strcmp(parent->entries[i].name, filename) == 0) {
            parent->entries[i] = parent->entries[--parent->entry_count];
            return 0;
        }
    }
    return -ENOENT;
}

static const struct fuse_operations memfs_ops = {
    .getattr    = memfs_getattr,
    .readdir    = memfs_readdir,
    .create     = memfs_create,
    .mkdir      = memfs_mkdir,
    .read       = memfs_read,
    .write      = memfs_write,
    .truncate   = memfs_truncate,
    .unlink     = memfs_unlink,
};

int main(int argc, char *argv[])
{
    /* Initialize root inode */
    ino_t root_ino = alloc_inode(FT_DIR, S_IFDIR | 0755);
    (void)root_ino;  /* root is always inode 1 */

    return fuse_main(argc, argv, &memfs_ops, NULL);
}
```

---

## 17. VFS from Rust: Safe Abstractions and Kernel Modules

### 17.1 Rust in the Linux Kernel

Since Linux 6.1, Rust is an officially supported language for kernel modules. The `rust/kernel/` directory provides safe wrappers around kernel APIs.

### 17.2 A Rust VFS Module (Conceptual)

The kernel's Rust bindings abstract the unsafe C APIs into safe Rust traits. Here's how a filesystem module looks conceptually:

```rust
// Kernel Rust (linux kernel module context)
// This uses the actual kernel Rust API as of ~6.6+

use kernel::prelude::*;
use kernel::fs::{self, dentry, inode, file, sb};

module! {
    type: SimpleFs,
    name: "simplefs_rust",
    author: "You",
    description: "A simple Rust filesystem",
    license: "GPL",
}

struct SimpleFs;

impl kernel::Module for SimpleFs {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("SimpleFs: loading\n");
        fs::Registration::new_pinned(c_str!("simplefs_rust"), &THIS_MODULE)?;
        Ok(SimpleFs)
    }
}

impl Drop for SimpleFs {
    fn drop(&mut self) {
        pr_info!("SimpleFs: unloading\n");
    }
}
```

### 17.3 Userspace VFS Interaction in Rust

For userspace programs interacting with the VFS through system calls, here is safe, idiomatic Rust:

```rust
use std::fs::{self, File, OpenOptions};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt};
use std::os::unix::io::{AsRawFd, FromRawFd, RawFd};
use std::path::Path;
use std::io::{self, Read, Write, Seek, SeekFrom};

/// Demonstrates interacting with VFS through Rust's std library.
/// Each operation maps directly to a VFS system call.
fn vfs_operations_demo() -> io::Result<()> {

    // ── open() syscall ──────────────────────────────────────────
    // VFS: sys_open → do_filp_open → vfs_open → file->f_op->open
    let mut file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .mode(0o644)  // Unix permissions (O_CREAT mode)
        .open("/tmp/vfs_test.txt")?;

    // ── write() syscall ─────────────────────────────────────────
    // VFS: sys_write → vfs_write → file->f_op->write_iter
    // → generic_file_write_iter → page cache
    file.write_all(b"VFS is beautiful\n")?;

    // ── lseek() syscall ─────────────────────────────────────────
    // VFS: sys_lseek → vfs_llseek → file->f_op->llseek
    file.seek(SeekFrom::Start(0))?;

    // ── read() syscall ──────────────────────────────────────────
    let mut content = String::new();
    file.read_to_string(&mut content)?;
    println!("Read: {}", content.trim());

    // ── fstat() / stat() ────────────────────────────────────────
    // VFS: sys_fstat → vfs_fstat → vfs_getattr → inode->i_op->getattr
    let metadata = file.metadata()?;
    println!("Inode:       {}", metadata.ino());
    println!("Size:        {}", metadata.size());
    println!("Permissions: {:o}", metadata.permissions().mode());
    println!("UID:         {}", metadata.uid());
    println!("GID:         {}", metadata.gid());
    println!("Nlinks:      {}", metadata.nlink());
    println!("Dev:         {}", metadata.dev());
    println!("Rdev:        {}", metadata.rdev());
    println!("Block size:  {}", metadata.blksize());
    println!("Blocks:      {}", metadata.blocks());

    // ── fsync() ─────────────────────────────────────────────────
    // VFS: sys_fsync → vfs_fsync → file->f_op->fsync
    // Forces writeback of dirty pages to disk
    file.sync_all()?;   // fsync (data + metadata)
    file.sync_data()?;  // fdatasync (data only)

    // ── readdir() ───────────────────────────────────────────────
    // VFS: sys_getdents64 → iterate_dir → file->f_op->iterate_shared
    println!("\nDirectory listing of /proc/self/fd/:");
    for entry in fs::read_dir("/proc/self/fd/")? {
        let entry = entry?;
        let name = entry.file_name();
        // Each fd entry is a symlink — readlink internally
        if let Ok(target) = fs::read_link(entry.path()) {
            println!("  fd {} → {}", name.to_string_lossy(), target.display());
        }
    }

    // ── unlink() ────────────────────────────────────────────────
    // VFS: sys_unlink → do_unlinkat → vfs_unlink → inode->i_op->unlink
    fs::remove_file("/tmp/vfs_test.txt")?;

    Ok(())
}

/// Demonstrates mmap via VFS
fn mmap_demo() -> io::Result<()> {
    use std::os::unix::io::AsRawFd;

    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .open("/tmp/mmap_test")?;

    // Size the file
    file.set_len(4096)?;

    let fd = file.as_raw_fd();

    // mmap() system call:
    // VFS: sys_mmap → vm_mmap → mmap_region → file->f_op->mmap
    // → creates a VMA (vm_area_struct) in the process's mm_struct
    // → page faults are handled by the address_space's fault handler
    let ptr = unsafe {
        libc::mmap(
            std::ptr::null_mut(),
            4096,
            libc::PROT_READ | libc::PROT_WRITE,
            libc::MAP_SHARED,  // shared: writes go to page cache and eventually disk
            fd,
            0,
        )
    };

    if ptr == libc::MAP_FAILED {
        return Err(io::Error::last_os_error());
    }

    // Write via mmap — this bypasses the read/write path entirely
    // but still goes through the page cache (shared mapping)
    unsafe {
        let slice = std::slice::from_raw_parts_mut(ptr as *mut u8, 4096);
        let msg = b"written via mmap!";
        slice[..msg.len()].copy_from_slice(msg);
    }

    // msync() — ensures mmap writes reach the page cache (and optionally disk)
    unsafe {
        libc::msync(ptr, 4096, libc::MS_SYNC);
        libc::munmap(ptr, 4096);
    }

    fs::remove_file("/tmp/mmap_test")?;
    Ok(())
}

/// Demonstrates /proc interaction from Rust
fn proc_demo() -> io::Result<()> {
    // Read process maps — same as /proc/self/maps
    let maps = fs::read_to_string("/proc/self/maps")?;
    println!("First 3 memory regions:");
    for line in maps.lines().take(3) {
        println!("  {}", line);
    }

    // Read kernel parameters via /proc/sys
    let swappiness = fs::read_to_string("/proc/sys/vm/swappiness")?;
    println!("vm.swappiness = {}", swappiness.trim());

    // Read system-wide file stats
    let file_nr = fs::read_to_string("/proc/sys/fs/file-nr")?;
    println!("file-nr (open/free/max): {}", file_nr.trim());

    Ok(())
}

/// Low-level raw fd operations demonstrating VFS directly
fn raw_fd_demo() -> io::Result<()> {
    use std::os::unix::io::OwnedFd;
    use std::os::fd::AsFd;

    // pipe() creates two file objects in pipefs
    // VFS: sys_pipe → create_pipe_files → alloc_file → pipefs inode
    let mut fds: [RawFd; 2] = [0; 2];
    unsafe { libc::pipe(fds.as_mut_ptr()); }

    let read_fd  = unsafe { OwnedFd::from_raw_fd(fds[0]) };
    let write_fd = unsafe { OwnedFd::from_raw_fd(fds[1]) };

    // Write to pipe
    let mut write_file = unsafe { File::from_raw_fd(write_fd.as_raw_fd()) };
    write_file.write_all(b"through the pipe!")?;
    std::mem::forget(write_file);  // don't double-close

    // Close write end — signals EOF to reader
    drop(write_fd);

    // Read from pipe
    let mut read_file = unsafe { File::from_raw_fd(read_fd.as_raw_fd()) };
    let mut buf = String::new();
    read_file.read_to_string(&mut buf)?;
    println!("Pipe read: {}", buf);
    std::mem::forget(read_file);  // OwnedFd will close
    drop(read_fd);

    Ok(())
}

fn main() {
    vfs_operations_demo().expect("VFS ops demo failed");
    mmap_demo().expect("mmap demo failed");
    proc_demo().expect("/proc demo failed");
    raw_fd_demo().expect("raw fd demo failed");
}
```

### 17.4 Rust and inotify

```rust
use std::os::unix::io::RawFd;

/// Wraps Linux inotify API via raw syscalls
struct Inotify {
    fd: RawFd,
}

impl Inotify {
    fn new() -> io::Result<Self> {
        let fd = unsafe { libc::inotify_init1(libc::IN_CLOEXEC | libc::IN_NONBLOCK) };
        if fd < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(Inotify { fd })
    }

    fn add_watch(&self, path: &str, mask: u32) -> io::Result<i32> {
        let c_path = std::ffi::CString::new(path).unwrap();
        let wd = unsafe { libc::inotify_add_watch(self.fd, c_path.as_ptr(), mask) };
        if wd < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(wd)
    }
}

impl Drop for Inotify {
    fn drop(&mut self) {
        unsafe { libc::close(self.fd); }
    }
}
```

---

## 18. Extended Attributes (xattr)

Extended attributes allow attaching arbitrary metadata (name=value pairs) to files and directories. They live in four namespaces:

| Namespace  | Prefix      | Use                              |
|------------|-------------|----------------------------------|
| `user`     | `user.`     | Application metadata             |
| `security` | `security.` | LSM (SELinux, AppArmor) labels   |
| `system`   | `system.`   | ACLs, capabilities               |
| `trusted`  | `trusted.`  | Root-only kernel use             |

### VFS xattr calls

```c
/* Setting an xattr: */
int vfs_setxattr(struct user_namespace *mnt_userns, struct dentry *dentry,
                 const char *name, const void *value, size_t size, int flags)
{
    /* Calls inode->i_op->setxattr() or the xattr handler */
}

/* Getting an xattr: */
ssize_t vfs_getxattr(struct user_namespace *mnt_userns, struct dentry *dentry,
                     const char *name, void *value, size_t size)
{
    /* Calls inode->i_op->getxattr() */
}
```

### C Example

```c
#include <sys/xattr.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    const char *path = "/tmp/xattr_test";
    const char *name = "user.myapp.version";
    const char *value = "1.2.3";

    /* Create the file */
    FILE *f = fopen(path, "w");
    fclose(f);

    /* Set xattr */
    if (setxattr(path, name, value, strlen(value), 0) < 0) {
        perror("setxattr");
        return 1;
    }

    /* Get xattr */
    char buf[256] = {0};
    ssize_t len = getxattr(path, name, buf, sizeof(buf));
    if (len < 0) {
        perror("getxattr");
        return 1;
    }
    printf("xattr %s = %.*s\n", name, (int)len, buf);

    /* List all xattrs */
    char list[1024] = {0};
    ssize_t list_len = listxattr(path, list, sizeof(list));
    printf("All xattrs:\n");
    for (char *p = list; p < list + list_len; p += strlen(p) + 1) {
        printf("  %s\n", p);
    }

    remove(path);
    return 0;
}
```

---

## 19. File Locking in VFS

Linux supports multiple file locking mechanisms, all managed through VFS:

### 19.1 POSIX Locks (fcntl)

```c
struct flock fl = {
    .l_type   = F_WRLCK,       /* write lock */
    .l_whence = SEEK_SET,
    .l_start  = 0,
    .l_len    = 0,              /* 0 = lock entire file */
    .l_pid    = 0,
};

/* Acquire lock (blocking) */
fcntl(fd, F_SETLKW, &fl);

/* Release lock */
fl.l_type = F_UNLCK;
fcntl(fd, F_SETLK, &fl);
```

**POSIX locks are per-(pid, file) not per-fd.** This is a notorious design flaw: if you open the same file twice in one process and lock it via one fd, unlocking via the other fd releases it. Multiple threads in the same process share the lock.

### 19.2 BSD flock Locks

```c
flock(fd, LOCK_EX);   /* exclusive lock */
flock(fd, LOCK_SH);   /* shared lock */
flock(fd, LOCK_UN);   /* unlock */
```

`flock` locks are associated with the *open file description* (struct file), not the fd. Two fds from `dup()` share the same lock. Two `open()` calls create independent locks. `flock` works across threads in the same process correctly.

### 19.3 Mandatory vs Advisory Locks

Linux supports mandatory locking (enabled via `mount -o mand` and `chmod g+s,g-x file`) but it is deprecated and largely useless in practice. POSIX and flock are advisory — processes must cooperate.

### 19.4 Open File Description Locks (OFD locks)

```c
/* F_OFD_SETLK, F_OFD_SETLKW, F_OFD_GETLK */
/* These are associated with the open file description, not the PID.
   Correctly handles the multi-thread case. */
fcntl(fd, F_OFD_SETLKW, &fl);
```

OFD locks solve POSIX lock's threading problem. They are the recommended mechanism for modern applications.

### 19.5 Kernel Implementation

All locks are stored in a `file_lock_context` embedded in each inode. The VFS `locks_lock_file_wait()` function handles blocking and the lock conflict matrix:

| Existing \ Requested | Shared | Exclusive |
|----------------------|--------|-----------|
| Shared               | OK     | Wait      |
| Exclusive            | Wait   | Wait      |

---

## 20. Asynchronous I/O and io_uring interaction with VFS

### 20.1 AIO (Legacy)

The old `aio_read`/`aio_write` interface submits I/O asynchronously but has significant limitations: it only works truly asynchronously for O_DIRECT files, and falls back to blocking for buffered I/O.

### 20.2 io_uring

`io_uring` (Linux 5.1+) is the modern async I/O interface. It uses two shared memory ring buffers between user and kernel:
- **SQ (submission queue)**: user submits I/O requests
- **CQ (completion queue)**: kernel posts completions

```c
#include <liburing.h>

int main(void) {
    struct io_uring ring;

    /* Initialize io_uring with 8-entry queues */
    io_uring_queue_init(8, &ring, 0);

    int fd = open("/tmp/test", O_RDONLY);
    char buf[4096];

    /* Get submission queue entry */
    struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);

    /* Prepare a read operation */
    io_uring_prep_read(sqe, fd, buf, sizeof(buf), 0);
    sqe->user_data = 42;  /* tag for identifying completion */

    /* Submit to kernel */
    io_uring_submit(&ring);

    /* Wait for completion */
    struct io_uring_cqe *cqe;
    io_uring_wait_cqe(&ring, &cqe);

    if (cqe->res < 0)
        fprintf(stderr, "Read error: %s\n", strerror(-cqe->res));
    else
        printf("Read %d bytes\n", cqe->res);

    io_uring_cqe_seen(&ring, cqe);
    io_uring_queue_exit(&ring);
    close(fd);
    return 0;
}
```

### 20.3 How io_uring Interacts with VFS

Each io_uring operation maps to a VFS operation:

```
IORING_OP_READ    → vfs_read() / kiocb-based read
IORING_OP_WRITE   → vfs_write()
IORING_OP_OPENAT  → do_sys_openat2()
IORING_OP_STATX   → do_statx()
IORING_OP_READV   → vfs_readv()
IORING_OP_FSYNC   → vfs_fsync()
IORING_OP_SPLICE  → do_splice()
```

The kernel's io_uring subsystem submits these as `struct kiocb` (kernel I/O control block) with `ki_complete` set to the io_uring completion handler. For truly asynchronous filesystems (block devices with O_DIRECT), the kiocb is queued to the block layer. For buffered I/O, it may execute synchronously but in a kernel thread (io-wq).

### 20.4 SQPOLL Mode

With `IORING_SETUP_SQPOLL`, a kernel thread polls the submission queue, eliminating the `io_uring_submit()` syscall overhead entirely — I/O can be submitted with zero syscalls.

---

## 21. Filesystem Notifications: inotify & fanotify

### 21.1 inotify

`inotify` watches for filesystem events on specific files or directories:

```c
#include <sys/inotify.h>

int fd = inotify_init1(IN_CLOEXEC);
int wd = inotify_add_watch(fd, "/tmp/watched/",
                            IN_CREATE | IN_DELETE | IN_MODIFY |
                            IN_MOVED_FROM | IN_MOVED_TO | IN_CLOSE_WRITE);

/* Read events (blocking) */
char buf[4096] __attribute__((aligned(__alignof__(struct inotify_event))));
ssize_t len = read(fd, buf, sizeof(buf));

for (char *ptr = buf; ptr < buf + len; ) {
    struct inotify_event *ev = (struct inotify_event *)ptr;

    if (ev->mask & IN_CREATE)   printf("Created: %s\n", ev->name);
    if (ev->mask & IN_DELETE)   printf("Deleted: %s\n", ev->name);
    if (ev->mask & IN_MODIFY)   printf("Modified: %s\n", ev->name);
    if (ev->mask & IN_ISDIR)    printf("  (is a directory)\n");

    ptr += sizeof(struct inotify_event) + ev->len;
}
```

### 21.2 VFS Hooks for inotify

inotify is implemented via **fsnotify hooks** embedded in VFS:

```c
/* Called by VFS after a file is created */
static inline void fsnotify_create(struct inode *inode, struct dentry *dentry)
{
    audit_inode_child(inode, dentry, AUDIT_TYPE_CHILD_CREATE);
    return fsnotify(inode, FS_CREATE, d_inode(dentry), FSNOTIFY_EVENT_INODE,
                    &dentry->d_name, 0);
}

/* Called by VFS on write */
static inline void fsnotify_modify(struct file *file) { ... }
/* Called by VFS on access */
static inline void fsnotify_access(struct file *file) { ... }
```

### 21.3 fanotify

`fanotify` is more powerful than inotify:
- Can **intercept** file accesses (permission events)
- Works on entire mount points
- Provides the file descriptor of the file being accessed (not just the name)

```c
#include <sys/fanotify.h>

int fd = fanotify_init(FAN_CLASS_NOTIF | FAN_CLOEXEC | FAN_NONBLOCK, O_RDONLY);

/* Watch entire filesystem */
fanotify_mark(fd, FAN_MARK_ADD | FAN_MARK_FILESYSTEM,
              FAN_OPEN | FAN_CLOSE_WRITE | FAN_CREATE,
              AT_FDCWD, "/");

/* Read events */
struct fanotify_event_metadata metadata;
while (read(fd, &metadata, sizeof(metadata)) > 0) {
    printf("PID %d opened fd %d\n", metadata.pid, metadata.fd);
    close(metadata.fd);  /* must close the provided fd */
}
```

---

## 22. Security in VFS: LSM Hooks

### 22.1 Linux Security Modules

VFS has **security hooks** at every sensitive operation. These are called by the LSM framework, which dispatches to active security modules (SELinux, AppArmor, Smack, etc.).

```c
/* Examples of VFS-level LSM hooks (in include/linux/lsm_hooks.h) */

/* Before opening a file */
int security_file_open(struct file *file);

/* Before executing a binary */
int security_bprm_check(struct linux_binprm *bprm);

/* Before creating an inode */
int security_inode_create(struct inode *dir, struct dentry *dentry, umode_t mode);

/* Before reading file attributes */
int security_inode_getattr(const struct path *path);

/* Before setting xattr */
int security_inode_setxattr(struct user_namespace *mnt_userns,
                             struct dentry *dentry, const char *name,
                             const void *value, size_t size, int flags);

/* Before mounting */
int security_sb_mount(const char *dev_name, const struct path *path,
                      const char *type, unsigned long flags, void *data);
```

### 22.2 SELinux Example

SELinux stores security context labels in `security.selinux` xattrs on filesystem inodes. When a process tries to open a file:

1. `sys_open()` calls `vfs_open()`
2. `vfs_open()` calls `security_file_open()`
3. SELinux checks: does the process's type have `allow process_t file_t:file { open read }`?
4. If denied → EACCES

### 22.3 Capabilities in VFS

VFS checks capabilities at multiple points:

```c
/* CAP_DAC_OVERRIDE: bypass file read/write/exec permission checks */
/* CAP_DAC_READ_SEARCH: bypass file read permission checks */
/* CAP_CHOWN: change file UID/GID */
/* CAP_FOWNER: bypass permission checks requiring file ownership */
/* CAP_SYS_ADMIN: mount filesystems, use ioctl on filesystems */

/* Example check in VFS: */
if (!capable(CAP_CHOWN))
    return -EPERM;
```

---

## 23. Memory-Mapped Files and VFS

### 23.1 The mmap Lifecycle

```
mmap(NULL, len, PROT_READ|PROT_WRITE, MAP_SHARED, fd, offset)
    ↓
sys_mmap_pgoff()
    ↓
vm_mmap_pgoff()
    ↓
mmap_region()
    ↓
file->f_op->mmap()
    (installs vm_operations_struct into the VMA)
    ↓
vma->vm_ops->fault() called on first page access (page fault)
    ↓
filemap_fault()
    ↓
find_get_page() — check page cache
    ↓ miss:
page_cache_alloc() — allocate new page
mapping->a_ops->readpage() — fill from disk
wait_on_page_locked() — wait for I/O
    ↓ hit:
return page → install PTE → resume process
```

### 23.2 Shared vs Private Mappings

**`MAP_SHARED`:** Writes go to the page cache. The page is marked dirty. Writeback eventually flushes it to disk. All processes mapping the same file see each other's writes immediately (no copy — same physical page).

**`MAP_PRIVATE`:** Copy-on-write semantics. Initially maps the same page cache page (read-only). On first write, the kernel allocates a private copy of the page, maps it as writable, and the write goes to the private copy. Disk is never modified.

### 23.3 vm_area_struct and VMA Operations

```c
struct vm_area_struct {
    unsigned long vm_start;         /* start address */
    unsigned long vm_end;           /* end address (exclusive) */
    struct vm_area_struct *vm_next; /* linked list of VMAs */
    pgprot_t vm_page_prot;          /* access permissions */
    unsigned long vm_flags;         /* VM_READ, VM_WRITE, VM_EXEC, VM_SHARED */
    struct file *vm_file;           /* the mapped file */
    const struct vm_operations_struct *vm_ops;
    unsigned long vm_pgoff;         /* offset in FILE_PAGE units */
    /* ... */
};

struct vm_operations_struct {
    void (*open)(struct vm_area_struct *area);
    void (*close)(struct vm_area_struct *area);
    int (*split)(struct vm_area_struct *area, unsigned long addr);
    int (*mremap)(struct vm_area_struct *area);
    vm_fault_t (*fault)(struct vm_fault *vmf);
    vm_fault_t (*huge_fault)(struct vm_fault *vmf, enum page_entry_size pe_size);
    vm_fault_t (*map_pages)(struct vm_fault *vmf, pgoff_t start_pgoff, pgoff_t end_pgoff);
    unsigned long (*pagesize)(struct vm_area_struct *area);
    /* ... */
};
```

---

## 24. Filesystem Writeback and Journaling

### 24.1 Writeback Architecture

Linux uses **write-back caching** for buffered writes: data goes to the page cache first, disk writes happen asynchronously. The writeback subsystem is managed by `bdi_writeback` (backing device info writeback):

```c
struct bdi_writeback {
    struct backing_dev_info *bdi;
    long nr_pages;              /* number of dirty pages */
    struct list_head b_dirty;   /* dirty inodes */
    struct list_head b_io;      /* inodes being written */
    struct list_head b_more_io; /* inodes deferring writeback */
    struct list_head b_dirty_time; /* time-lazy dirty inodes */
    struct delayed_work dwork;  /* work item for writeback */
    /* ... */
};
```

### 24.2 Writeback Triggers

Writeback is triggered by:
1. **`dirty_writeback_interval`** timer (default every 5 seconds)
2. **Memory pressure**: page reclaim needs to evict dirty pages
3. **`sync()` / `fsync()` / `fdatasync()`**: explicit user request
4. **Dirty ratio threshold**: when dirty pages exceed `vm.dirty_ratio` of RAM, writers block

### 24.3 Journaling (Ordered, Writeback, Journal modes)

ext4 (and ext3 before it) uses a **journal** (write-ahead log) to guarantee metadata consistency after crashes:

**Journal mode** (`data=journal`): Both data and metadata go through the journal. Safest, slowest.

**Ordered mode** (`data=ordered`, default): Metadata goes through journal. Data is written to final location *before* the metadata journal commit. Guarantees no stale data after crash.

**Writeback mode** (`data=writeback`): Only metadata is journaled. Data may appear before or after metadata. Fastest, least safe.

The journal (JBD2 layer) works by:
1. Grouping metadata operations into a **transaction**
2. Writing the transaction to a circular buffer on disk (the journal)
3. Committing the transaction (writing a commit block)
4. Asynchronously checkpointing (writing actual data to final locations)
5. Releasing journal space

On recovery, the kernel replays committed but not checkpointed transactions.

---

## 25. VFS Performance Internals

### 25.1 RCU-Walk for Fast Path

The RCU path walk (introduced in ~2.6.38) allows concurrent path lookups without any locks, using RCU (Read-Copy-Update) for safe lock-free traversal of the dentry tree. Critical optimizations:

- **`seqcount` on parent dentry**: detects renames during walk
- **`d_seq` on each dentry**: detects modifications
- Falls back to ref-count walk if any seqcount retry occurs

### 25.2 Per-CPU Slab Caches

Dentries and inodes are allocated from slab caches (`dentry_cache`, `inode_cache`). These are **SLUB** caches with per-CPU free lists, making allocation/deallocation essentially free (just a pointer pop/push) in the common case.

### 25.3 Lockless fdget

```c
/* Getting a file from fd — most reads use lockless fdget */
static inline struct fd fdget(unsigned int fd)
{
    return __to_fd(__fdget(fd));
}

/* __fdget uses RCU and atomic operations to avoid any spinlock */
```

### 25.4 Read-Ahead

The kernel's read-ahead logic (`mm/readahead.c`) speculatively reads ahead in files being read sequentially. The `file_ra_state` tracks:
- Current window size
- Current async/sync state
- Previous read position (to detect sequential vs. random access)

### 25.5 Reducing VFS Overhead

For applications requiring maximum I/O throughput:

1. **O_DIRECT**: bypass page cache entirely. Data goes DMA'd directly between userspace and device. Requires aligned buffers and sizes. Used by databases (PostgreSQL, MySQL) to manage their own caching.

2. **io_uring with fixed buffers**: register buffers once, reuse without copy.

3. **Huge pages for mmap**: reduces TLB pressure for large mappings.

4. **`fadvise(POSIX_FADV_SEQUENTIAL)`**: hints to increase read-ahead.

5. **`madvise(MADV_WILLNEED)`**: proactively faults pages into memory.

---

## 26. Tracing & Debugging VFS

### 26.1 strace

Observe all VFS system calls made by a process:

```bash
strace -e trace=file,desc ls /tmp
strace -e trace=openat,read,write,close cat /etc/hosts
```

### 26.2 ftrace

Trace kernel function calls:

```bash
# Trace all calls to vfs_read
echo 'vfs_read' > /sys/kernel/debug/tracing/set_ftrace_filter
echo 'function' > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on
# ... run your workload ...
cat /sys/kernel/debug/tracing/trace
echo 0 > /sys/kernel/debug/tracing/tracing_on
```

### 26.3 eBPF / bpftrace

```bash
# Trace open() calls with filenames
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s opened %s\n", comm, str(args->filename)); }'

# Track write sizes
bpftrace -e 'tracepoint:syscalls:sys_enter_write { @bytes = hist(args->count); }'

# Trace dentry cache misses
bpftrace -e 'kprobe:d_lookup { @[comm] = count(); }'
```

### 26.4 /proc/sys/fs Statistics

```bash
# File table statistics (open files / free files / max files)
cat /proc/sys/fs/file-nr

# Inode cache statistics
cat /proc/sys/fs/inode-nr

# Dentry state (# dentries / unused / negative)
cat /proc/sys/fs/dentry-state

# Per-filesystem mount info
cat /proc/mounts
cat /proc/mountinfo      # detailed including peer group IDs

# Filesystem usage
df -i   # inode usage
df -h   # block usage
```

### 26.5 Useful /proc Filesystem Debug Files

```bash
# All open files in the system (requires root)
ls -la /proc/*/fd/ 2>/dev/null | grep -v "Permission"

# Memory maps for a specific process
cat /proc/<pid>/smaps

# Detailed inode information for a specific file
stat /path/to/file

# Filesystem-specific debug (ext4 example)
debugfs /dev/sda1   # ext4 interactive debugger
```

---

## 27. Mental Models and Expert Intuition

### 27.1 The Three Questions

When encountering any VFS operation, ask:
1. **Which object is involved?** (superblock, inode, dentry, or file)
2. **Which operation table is called?** (super_ops, inode_ops, dentry_ops, or file_ops)
3. **Where does the data live?** (page cache, disk, network, or generated in-kernel)

These three questions resolve 90% of VFS reasoning.

### 27.2 The Identity Principle

In VFS, *identity* is always the **inode**, never the name. A file can have:
- Multiple names (hard links) → same inode, multiple dentries
- No names (unlinked but still open) → inode exists, no dentries
- The same name at different times → different inodes (delete and recreate)

This principle explains why `inotify` watches by inode (watch descriptor ties to the path, but events fire on the underlying inode).

### 27.3 The Caching Hierarchy Mental Model

```
  ┌─────────────────────────────────┐
  │       CPU Registers / L1-L3     │  nanoseconds
  ├─────────────────────────────────┤
  │  Dentry Cache (resolved paths)  │  ~50ns (hash lookup)
  ├─────────────────────────────────┤
  │    Inode Cache (file metadata)  │  ~50ns
  ├─────────────────────────────────┤
  │    Page Cache (file content)    │  ~100ns (RAM access)
  ├─────────────────────────────────┤
  │         SSD / NVMe              │  ~100µs (0.1ms)
  ├─────────────────────────────────┤
  │         HDD                     │  ~10ms
  ├─────────────────────────────────┤
  │         Network (NFS)           │  >1ms
  └─────────────────────────────────┘
```

Every caching layer is a 100-1000× speedup over the next. Cold cache misses are catastrophic for performance. Warm cache hits make Linux "feel" instant.

### 27.4 The Fork/Exec Model

```
fork()
  → child gets copy of parent's file descriptor table
  → both share the SAME struct file objects
  → both share SAME f_pos (cursor position)
  → closing in child does NOT close in parent (unless it was the last ref)

exec()
  → closes O_CLOEXEC fds (safe default: use O_CLOEXEC on everything)
  → inherits non-CLOEXEC fds
  → new binary gets same open files, same positions
```

### 27.5 The Zero-Copy Philosophy

The kernel's design trend is toward **zero-copy** — data should never be copied if it can be referenced:

- **sendfile()**: sends file data to socket without userspace copy
- **splice()**: moves data between two fds through the kernel splice pipe
- **mmap()**: maps file pages into process address space (no read/write copies)
- **io_uring fixed buffers**: kernel pins userspace buffers, avoids copy

Every `memcpy()` in the I/O path is a bug waiting to be optimized.

### 27.6 Chunking VFS Knowledge

Apply **chunking** (a cognitive science principle) to VFS. Instead of memorizing individual functions, chunk them by role:

**Chunk 1 — Lifecycle**: alloc_inode → fill → use → evict → destroy
**Chunk 2 — Name Resolution**: lookup → dentry → (mount crossing) → inode
**Chunk 3 — Data Access**: open → read/write → page cache → writeback
**Chunk 4 — Consistency**: journal → commit → checkpoint → recovery

Each chunk can be recalled as a unit. When debugging, identify which chunk the problem lives in and you immediately narrow the search space.

### 27.7 Pattern Recognition: What To Look For

| Symptom                      | VFS Layer Suspect             |
|------------------------------|-------------------------------|
| `open()` slow on first call  | Dcache miss + disk directory read |
| `open()` fast after first    | Dcache hit                    |
| `stat()` slow over NFS       | `d_revalidate` network call   |
| Stale file contents          | Page cache not invalidated    |
| `EMFILE` error               | fd limit reached              |
| `ENOSPC` on file creation    | Inode exhaustion (check `df -i`) |
| Deleted file still consuming space | Inode held by open fd  |
| Bind mount not propagating   | Mount propagation type mismatch |
| Container can't see host mount | Mount namespace isolation   |

---

## Summary: The VFS Mental Map

```
                    User Process
                         │
              ┌──────────▼──────────┐
              │   System Call Layer  │
              │  open/read/write/... │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────────────────────┐
              │              VFS LAYER               │
              │                                      │
              │  superblock ──► super_operations     │
              │      │                               │
              │  inode ──────► inode_operations      │
              │      │                               │
              │  dentry ─────► dentry_operations     │
              │      │                               │
              │  file ───────► file_operations       │
              │      │                               │
              │  [dcache] [icache] [page cache]      │
              │  [mount tree] [path walk (namei)]    │
              └──────┬─────────────────────┬─────────┘
                     │                     │
          ┌──────────▼──────┐   ┌──────────▼──────────┐
          │   ext4 / xfs    │   │  tmpfs / procfs      │
          │   (disk-based)  │   │  (memory-based)      │
          └──────┬──────────┘   └─────────────────────-┘
                 │
          ┌──────▼──────────┐
          │   Block Layer   │
          │   (bio, queue)  │
          └──────┬──────────┘
                 │
          ┌──────▼──────────┐
          │  Storage Device │
          │  (NVMe / HDD)   │
          └─────────────────┘
```

---

*The VFS is not just kernel machinery. It is a philosophy: that the interface to information should be universal, that names should be separate from identity, that caching should be transparent, and that the same simple contract — open, read, write, close — should work whether the data lives on a chip, a spinning disk, a remote server, or in the kernel's own memory. Mastering VFS is mastering the deepest possible understanding of how Linux mediates between programs and the world.*

Here is your complete guide — **~8,500 words, 27 chapters, fully in-depth**. Here's what it covers at a glance:

**Architecture & Core Objects**
The four VFS pillars — `superblock`, `inode`, `dentry`, `file` — with full kernel struct definitions from `linux/fs.h`, every operations vtable (`super_operations`, `inode_operations`, `dentry_operations`, `file_operations`), and the `container_of` / embedded-struct inheritance pattern that ext4 uses.

**Deep Subsystems**
The full path walk algorithm (RCU-mode fast path, mount crossing, symlink recursion), dcache/icache architecture with LRU and shrinker internals, the unified page cache (`address_space`, XArray, read/write paths traced instruction by instruction through `generic_file_read_iter`).

**Pseudo-filesystems**
procfs (`proc_dir_entry`, sysctl), sysfs (kobject hierarchy, kernfs backend, attribute show/store), tmpfs (full `shmem_get_inode`), devtmpfs, cgroupfs, pipefs/sockfs — each with implementation-level code.

**C Implementations**
A fully loadable `simplefs` kernel module implementing all four VFS objects, plus a complete FUSE in-memory filesystem (`memfs`) with getattr, readdir, create, mkdir, read, write, truncate, unlink.

**Rust**
Idiomatic userspace VFS interaction (every syscall mapped to its kernel dispatch chain), mmap demo, `/proc` interaction, raw fd/pipe operations, inotify wrapper.

**Advanced Topics**
io_uring ↔ VFS dispatch, inotify/fanotify with `fsnotify` hook internals, LSM/SELinux hooks at every VFS call site, OFD locks, xattr namespaces, journaling modes (ordered/journal/writeback), writeback architecture, mount namespaces and propagation types.

**Expert Mental Models**
The three-question framework, the identity principle, the caching hierarchy with latency numbers, the zero-copy philosophy, and a diagnostic table mapping symptoms to VFS layers — the kind of intuition that separates a top 1% systems programmer from the rest.