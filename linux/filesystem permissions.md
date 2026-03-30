# Linux Filesystem Permissions — Complete In-Depth Guide

> *"Security in Linux is not a feature you bolt on — it is baked into every inode, every syscall, every process boundary."*

---

## Table of Contents

1. [The Mental Model: Everything is a File](#1-the-mental-model-everything-is-a-file)
2. [Identity: Users, Groups, and Processes](#2-identity-users-groups-and-processes)
3. [The Inode: Where Permissions Live](#3-the-inode-where-permissions-live)
4. [The Classic Unix Permission Bits](#4-the-classic-unix-permission-bits)
5. [Symbolic and Octal Notation](#5-symbolic-and-octal-notation)
6. [How the Kernel Evaluates Permissions](#6-how-the-kernel-evaluates-permissions)
7. [Special Permission Bits: SetUID, SetGID, Sticky](#7-special-permission-bits-setuid-setgid-sticky)
8. [Directory Permissions — A Special Case](#8-directory-permissions--a-special-case)
9. [umask — Default Permission Mask](#9-umask--default-permission-mask)
10. [Access Control Lists (ACLs)](#10-access-control-lists-acls)
11. [Linux Capabilities](#11-linux-capabilities)
12. [Key System Calls Reference](#12-key-system-calls-reference)
13. [C Implementation — Full Permission Toolkit](#13-c-implementation--full-permission-toolkit)
14. [Rust Implementation — Safe Permissions Library](#14-rust-implementation--safe-permissions-library)
15. [Go Implementation — Permission Inspector Tool](#15-go-implementation--permission-inspector-tool)
16. [Real-World Patterns and Hardening](#16-real-world-patterns-and-hardening)
17. [Common Vulnerabilities and Pitfalls](#17-common-vulnerabilities-and-pitfalls)

---

## 1. The Mental Model: Everything is a File

Linux inherits the Unix philosophy: **every resource — regular files, directories, devices, sockets, pipes — is represented as a file in a filesystem**. This unification means that a single, elegant permission model governs all of them.

### What a "File" Means to the Kernel

```
User Space                     Kernel Space
─────────────────────────────────────────────────────
open("/etc/passwd", O_RDONLY)
         │
         ▼
  [Virtual File System (VFS)]  ←── abstraction layer
         │
         ▼
  [Filesystem Driver]          ←── ext4 / xfs / btrfs / tmpfs
         │
         ▼
  [Inode Table on Disk]        ←── UID, GID, mode bits live HERE
         │
         ▼
  [Block Device / Memory]
```

Every file in Linux is uniquely identified by its **inode** (index node) — a data structure on disk that stores metadata. The inode stores:

- Owner user ID (`uid_t`)
- Owner group ID (`gid_t`)
- Permission mode bits (`mode_t`) — **this is where all permissions live**
- Timestamps (atime, mtime, ctime)
- File size, block count, link count

> **Key Insight:** The *filename* is NOT stored in the inode. Filenames live in directory entries (dentries) that point to inodes. One inode can have multiple names (hard links).

---

## 2. Identity: Users, Groups, and Processes

### The Three Levels of Identity

Every process on Linux carries **multiple identity attributes**. Understanding them is prerequisite to understanding permissions.

```
Process Identity (task_struct in kernel)
┌─────────────────────────────────────────────────┐
│  Real UID      (ruid)  ← who launched this?      │
│  Effective UID (euid)  ← who are we acting as?   │
│  Saved UID     (suid)  ← can we drop back to?    │
│                                                   │
│  Real GID      (rgid)                             │
│  Effective GID (egid)                             │
│  Saved GID     (sgid)                             │
│                                                   │
│  Supplementary Groups [] ← up to NGROUPS_MAX      │
└─────────────────────────────────────────────────┘
```

**Real UID/GID** — The identity of the user who actually launched the process. Set at login; stays constant through normal execution.

**Effective UID/GID (euid/egid)** — The identity the kernel uses for permission checks. **This is the one that matters for access control.** Can differ from ruid when SetUID binaries are involved.

**Saved UID/GID (suid/sgid)** — A copy stored so a process can temporarily drop privileges and regain them later. Enables privilege bracketing (run as root only when needed).

**Supplementary Groups** — A process may belong to many groups simultaneously (default limit: 65536 on modern kernels). The `/etc/group` file defines group membership.

### Checking Identity

```bash
id                    # shows uid, gid, groups of current user
cat /proc/self/status # shows all UID/GID values of current process
```

### The Root Special Case

UID 0 (root) **bypasses almost all DAC (Discretionary Access Control) permission checks**. Root can:
- Read/write any file regardless of permissions
- Change ownership of any file (`chown`)
- Execute any file if it has execute permission for anyone
- Kill any process

This is why the root account is called "superuser" — the kernel has explicit checks: `if (current_euid() == 0) allow;`

---

## 3. The Inode: Where Permissions Live

The mode field of an inode is a **16-bit integer** divided into bit fields:

```
Bit Position:  15 14 13 12 | 11 10  9 | 8  7  6 | 5  4  3 | 2  1  0
               ─────────── ─────────── ───────── ───────── ─────────
Meaning:       File Type   | Spec Bits |  Owner  |  Group  |  Others
               (4 bits)    | S S S     | r  w  x | r  w  x | r  w  x
                           | U G T     |         |         |
```

**File Type bits (top 4 bits)** — Defined as constants in `<sys/stat.h>`:

| Constant    | Value  | Meaning              |
|-------------|--------|----------------------|
| `S_IFREG`   | 0100000| Regular file         |
| `S_IFDIR`   | 0040000| Directory            |
| `S_IFLNK`   | 0120000| Symbolic link        |
| `S_IFCHR`   | 0020000| Character device     |
| `S_IFBLK`   | 0060000| Block device         |
| `S_IFIFO`   | 0010000| Named pipe (FIFO)    |
| `S_IFSOCK`  | 0140000| Socket               |

**Special bits (bits 9-11)** — SetUID, SetGID, Sticky (covered in Section 7)

**Permission bits (bits 0-8)** — Nine bits split into three groups of three

---

## 4. The Classic Unix Permission Bits

### The Nine Fundamental Permission Bits

```
Owner (User)    Group           Others (World)
┌───────────┐  ┌───────────┐   ┌───────────┐
│  r  w  x  │  │  r  w  x  │   │  r  w  x  │
│  4  2  1  │  │  4  2  1  │   │  4  2  1  │
│  bit8 7 6 │  │  bit5 4 3 │   │  bit2 1 0 │
└───────────┘  └───────────┘   └───────────┘
```

### What Each Bit Means — For Regular Files

| Bit     | For Regular Files                                              |
|---------|----------------------------------------------------------------|
| **r**   | Can read file content (`open(O_RDONLY)`, `read()`)            |
| **w**   | Can modify file content (`open(O_WRONLY)`, `write()`, `truncate()`) |
| **x**   | Can execute the file as a program, or use as shared library    |

> **Critical subtlety:** Write permission on a file does NOT mean you can delete it. Deletion is controlled by the **parent directory's write permission**.

### What Each Bit Means — For Directories

| Bit     | For Directories                                                |
|---------|----------------------------------------------------------------|
| **r**   | Can list directory contents (`readdir()`, `ls`)               |
| **w**   | Can create, delete, or rename files within (requires **x** too)|
| **x**   | Can **traverse/enter** the directory (`cd`, path resolution)  |

> **The crucial distinction:** You can have `--x` on a directory (traverse but not list). If you know the filename, you can open it. This is how `/etc/shadow` is protected — world has `--x` on `/etc` but not `r--`.

### System Call Constants (`<sys/stat.h>`)

```c
/* Owner permissions */
S_IRUSR = 0400   /* read by owner */
S_IWUSR = 0200   /* write by owner */
S_IXUSR = 0100   /* execute by owner */
S_IRWXU = 0700   /* all three for owner */

/* Group permissions */
S_IRGRP = 0040
S_IWGRP = 0020
S_IXGRP = 0010
S_IRWXG = 0070

/* Others permissions */
S_IROTH = 0004
S_IWOTH = 0002
S_IXOTH = 0001
S_IRWXO = 0007
```

---

## 5. Symbolic and Octal Notation

### Octal Notation

Because each permission group is 3 bits (values 0–7), octal is the natural representation. Each octal digit represents one group:

```
chmod 754 file

7 = 4+2+1 = rwx  (owner: full)
5 = 4+0+1 = r-x  (group: read + execute)
4 = 4+0+0 = r--  (others: read only)
```

Full 4-digit octal includes the special bits:

```
chmod 4755 file
  ↑
  └─ 4 = SetUID bit
     7 = rwx (owner)
     5 = r-x (group)
     5 = r-x (others)
```

### Common Octal Values

| Octal | Symbolic    | Use Case                                |
|-------|-------------|-----------------------------------------|
| 777   | `rwxrwxrwx` | World writable (dangerous)              |
| 755   | `rwxr-xr-x` | Programs, public directories            |
| 750   | `rwxr-x---` | Executables for specific group          |
| 644   | `rw-r--r--` | Regular config/data files               |
| 640   | `rw-r-----` | Group-readable sensitive files          |
| 600   | `rw-------` | Private files (SSH keys, certs)         |
| 700   | `rwx------` | Private directories                     |
| 4755  | `rwsr-xr-x` | SetUID executable (e.g., sudo, passwd)  |
| 2755  | `rwxr-sr-x` | SetGID executable or directory          |
| 1777  | `rwxrwxrwt` | Sticky shared directory (e.g., /tmp)    |

### Symbolic Notation (chmod `[ugoa][+-=][rwxst]`)

```bash
chmod u+x file          # add execute for owner
chmod g-w file          # remove write from group
chmod o=r file          # set others to read-only exactly
chmod a+r file          # add read for all (u+g+o)
chmod u=rwx,g=rx,o= file # set each class explicitly
chmod +x file           # adds execute for all classes (respects umask)
```

### Reading the `ls -l` Output

```
-rwxr-xr-x  2  alice  developers  4096  Mar 15 10:30  program
│└────────┘  │   │         │        │                    │
│  mode     nlinks owner  group   size                  name
│
└── file type: - = regular, d = dir, l = symlink,
                c = char dev, b = block dev, p = pipe, s = socket

rwx    = owner alice: read, write, execute
r-x    = group developers: read, execute (no write)
r-x    = others: read, execute (no write)
```

### The `stat` Command Details

```bash
stat /etc/passwd
  File: /etc/passwd
  Size: 2847         Blocks: 8          IO Block: 4096   regular file
Device: fd01h/64769d Inode: 524289      Links: 1
Access: (0644/-rw-r--r--)  Uid: (   0/  root)  Gid: (   0/  root)
Access: 2024-03-15 09:00:00
Modify: 2024-02-20 14:23:11
Change: 2024-02-20 14:23:11
```

---

## 6. How the Kernel Evaluates Permissions

This is the **permission evaluation algorithm** the kernel runs on every file access. Knowing this precisely eliminates all confusion.

```
                   File Access Request
                          │
                          ▼
              ┌──────────────────────┐
              │  Is euid == 0?       │  ← root check
              │  (superuser)         │
              └──────────────────────┘
                   │          │
                  YES         NO
                   │          │
                   ▼          ▼
              [ALLOW*]   ┌──────────────────────┐
                         │  Is euid == file_uid? │  ← owner check
                         └──────────────────────┘
                              │          │
                             YES         NO
                              │          │
                              ▼          ▼
                         Use OWNER   ┌──────────────────────────┐
                         bits        │  Is egid == file_gid OR  │  ← group check
                              │      │  file_gid in supp_groups? │
                              │      └──────────────────────────┘
                              │           │          │
                              │          YES         NO
                              │           │          │
                              │           ▼          ▼
                              │      Use GROUP    Use OTHERS
                              │      bits         bits
                              │           │          │
                              └─────┬─────┘          │
                                    ▼                 ▼
                             Check requested    Check requested
                             bits in selected   bits in OTHERS
                             category           category
                                    │                 │
                                    └────────┬────────┘
                                             ▼
                                  All required bits set?
                                      │         │
                                     YES         NO
                                      │         │
                                      ▼         ▼
                                  [ALLOW]   [EACCES]
```

> **\*Root exception for execute:** Even root cannot execute a file unless at least one execute bit (u, g, or o) is set. This prevents accidental execution of non-program files.

### The Categories Are Mutually Exclusive!

This is the most misunderstood aspect: **Linux evaluates exactly ONE category**. If you are the file owner, only the owner bits are checked — group and other bits are irrelevant, even if they would grant more access.

**Real-world gotcha:**
```bash
# File permissions: ---rwxrwx (owner has NO permissions!)
# If alice is the owner and the group also contains alice:
# Linux uses OWNER bits (---) → ACCESS DENIED
# It does NOT fall through to group bits (rwx)
```

### The `access()` vs Actual Permission Check

The `access()` syscall uses **real UID/GID** (not effective), making it unsuitable for privilege-aware code. Always use `open()` and let the kernel do the real check. `access()` has a TOCTOU (Time-Of-Check-Time-Of-Use) race condition vulnerability.

---

## 7. Special Permission Bits: SetUID, SetGID, Sticky

These three bits occupy positions 11, 10, and 9 in the mode field.

### SetUID (SUID) — Bit 11 — Value 04000

**On an executable:** When a SetUID binary runs, the process's **effective UID is set to the file owner's UID**, not the launching user's UID.

```
Normal execution:    euid = calling_user_uid
SetUID execution:    euid = file_owner_uid
```

**Real example: `passwd` command**

```bash
ls -l /usr/bin/passwd
-rwsr-xr-x 1 root root 68208 /usr/bin/passwd
     ↑
     └─ 's' in owner execute position = SetUID + executable
        If only SetUID but NOT executable, shows 'S' (capital)
```

When you run `passwd`, your process temporarily gets `euid=0` (root) so it can write to `/etc/shadow`. This is a controlled privilege escalation.

**On a regular file (non-executable):** Has no effect in standard Linux.

**SetUID on a directory:** No standard effect on Linux (differs from BSD).

### SetGID (SGID) — Bit 10 — Value 02000

**On an executable:** The process's **effective GID is set to the file's GID**.

```bash
ls -l /usr/bin/wall
-rwxr-sr-x 1 root tty 35048 /usr/bin/wall
              ↑
              └─ 's' in group execute position = SetGID + executable
```

**On a directory (very important!):** New files and subdirectories created inside inherit the **directory's group ownership**, not the creator's primary group.

```bash
mkdir /shared
chown :developers /shared
chmod 2775 /shared     # SetGID + rwxrwxr-x

# Now when any member of 'developers' creates a file here:
touch /shared/newfile
ls -l /shared/newfile
# -rw-rw-r-- 1 alice developers ...
#                    ↑ group inherited from directory, not from alice's primary group
```

This is the standard way to create collaborative project directories.

### Sticky Bit — Bit 9 — Value 01000

**On a directory:** A file within the directory can only be **deleted or renamed by** its owner, the directory owner, or root — regardless of the directory's write permission.

```bash
ls -ld /tmp
drwxrwxrwt 10 root root 4096 /tmp
          ↑
          └─ 't' = sticky bit + execute
             'T' = sticky bit but NOT execute

# /tmp is world-writable (rwxrwxrwx) but sticky prevents
# users from deleting each other's files.
```

**On a regular file (historical):** Originally told the kernel to keep the program in swap. Modern kernels ignore this entirely.

### Representation in `ls -l`

```
Owner execute column:
  x = execute only
  s = SetUID + execute
  S = SetUID, no execute (warning sign — usually misconfiguration)

Group execute column:
  x = execute only
  s = SetGID + execute
  S = SetGID, no execute

Others execute column:
  x = execute only
  t = sticky + execute
  T = sticky, no execute
```

---

## 8. Directory Permissions — A Special Case

Directories deserve their own section because their permission semantics are entirely different from files.

### Conceptual Model

Think of a directory as a **table of (name → inode_number) mappings**. Directory permissions control operations on this table:

```
Directory Entry (dentry) Structure — simplified:
┌──────────────────────────────────┐
│  inode 1024  │  "passwd"         │
│  inode 2048  │  "shadow"         │
│  inode 3072  │  "hosts"          │
└──────────────────────────────────┘
```

| Permission | Operation Allowed                                            |
|------------|--------------------------------------------------------------|
| **r**      | Read the name→inode table (list filenames with `readdir`)    |
| **w**      | Modify the table: add entries (`creat`/`link`), remove (`unlink`), rename (`rename`) — **always requires x too** |
| **x**      | Use directory in path resolution (traverse it)               |

### The Critical Combinations

```
Permission  │ Can list? │ Can traverse? │ Can create/delete?
────────────┼───────────┼───────────────┼───────────────────
   ---      │    NO     │      NO       │        NO
   r--      │   YES     │      NO       │        NO
   --x      │    NO     │     YES       │        NO
   r-x      │   YES     │     YES       │        NO
   rw-      │   YES     │      NO       │        NO (no x!)
   rwx      │   YES     │     YES       │       YES
   -wx      │    NO     │     YES       │       YES (can modify blindly)
```

### Why `-wx` (Write+Execute, No Read) is Interesting

A drop box directory: users can deposit files but cannot list what others have deposited.

```bash
chmod 1733 /dropbox    # sticky + -wx for all
# Users can: create files, enter directory
# Users cannot: list contents (ls fails)
# Sticky bit: users cannot delete others' files
```

### File Deletion Permission

```
To delete file /dir/file, you need:
  - Write (w) permission on /dir
  - Execute (x) permission on /dir
  - (Optionally, sticky bit logic applies)
  
  You do NOT need any permission on the file itself!
  Root can delete a file they cannot read.
```

### Path Resolution Walk

When you access `/a/b/c/file`:

1. Check `x` on `/` (root dir) — requires execute
2. Check `x` on `/a`
3. Check `x` on `/a/b`
4. Check `x` on `/a/b/c`
5. Check permissions on `file` according to operation

Each directory in the path requires **traverse (x)** permission.

---

## 9. umask — Default Permission Mask

### What umask Is

When a process creates a new file or directory, the kernel applies a **mask** to remove certain permission bits. The `umask` is a process-level setting inherited across `fork()`.

### How It Works

```
New file permissions = requested_mode & ~umask

Example:
  open(path, O_CREAT, 0666)   ← application requests 0666
  umask = 0022
  ~umask = ~0022 = 0755 (in permission bit range)
  Result = 0666 & 0755 = 0644

  mkdir(path, 0777)            ← application requests 0777
  Result = 0777 & 0755 = 0755
```

### Standard umask Values

| umask | Files created with | Dirs created with | Who uses it         |
|-------|-------------------|-------------------|---------------------|
| 0022  | 0644 (`rw-r--r--`)| 0755 (`rwxr-xr-x`)| Most systems (default) |
| 0002  | 0664 (`rw-rw-r--`)| 0775 (`rwxrwxr-x`)| Group-collaborative environments |
| 0027  | 0640 (`rw-r-----`)| 0750 (`rwxr-x---`)| More secure servers  |
| 0077  | 0600 (`rw-------`)| 0700 (`rwx------`)| High-security / SSH keys |

### umask Does NOT Remove Already-Absent Bits

umask only removes bits. It cannot ADD bits. `open(..., 0444)` with `umask=0022` gives `0444 & ~0022 = 0444` — the requested 0444, unchanged.

### Setting umask Programmatically

```c
#include <sys/stat.h>
mode_t old_mask = umask(0077);   // set; returns old value
// ... create file ...
umask(old_mask);                  // restore
```

### umask and Special Bits

umask can also mask special bits. If umask has bit 3 (octal 04000 range) set, SetUID is cleared on new files. Convention: umask typically only operates on the lower 9 bits.

---

## 10. Access Control Lists (ACLs)

### Why Classic Permissions Are Insufficient

Classic Unix permissions support only three categories: owner, one group, and others. What if you need:
- Give alice read access to bob's file without sharing with all of alice's groups?
- Deny a specific user access even though they're in an allowed group?
- Set different permissions for 5 different users on one file?

ACLs solve this with **per-user and per-group entries**.

### ACL Architecture

An ACL is a list of **Access Control Entries (ACEs)**, stored as extended attributes (`system.posix_acl_access`) on the inode.

```
ACL entry format:
  tag : qualifier : permissions

Tags:
  ACL_USER_OBJ   - file owner (maps to classic owner bits)
  ACL_USER       - a specific named user
  ACL_GROUP_OBJ  - file group (maps to classic group bits)
  ACL_GROUP      - a specific named group
  ACL_MASK       - maximum permissions for named users/groups
  ACL_OTHER      - others (maps to classic other bits)
```

### The ACL Mask — Critical Concept

The mask is the **maximum effective permission** for all `ACL_USER`, `ACL_GROUP`, and `ACL_GROUP_OBJ` entries. It does **not** limit `ACL_USER_OBJ` (owner) or `ACL_OTHER`.

```
Example ACL:
  user::rwx          ← owner (ACL_USER_OBJ)   — not masked
  user:alice:rwx     ← named user              — masked
  group::r-x         ← owning group            — masked
  group:devs:rwx     ← named group             — masked
  mask::r-x          ← MASK: limits all above named entries
  other::r--         ← others                  — not masked

Effective permissions:
  user::rwx          → rwx (owner, mask doesn't apply)
  user:alice:rwx     → r-x (rwx & mask r-x = r-x)
  group::r-x         → r-x (r-x & mask r-x = r-x)
  group:devs:rwx     → r-x (rwx & mask r-x = r-x)
  other::r--         → r-- (not masked)
```

### Viewing and Manipulating ACLs

```bash
# View ACL
getfacl file.txt

# Set named user permission
setfacl -m u:alice:rw file.txt

# Set named group permission
setfacl -m g:developers:rx file.txt

# Set default ACL on directory (inherited by new files)
setfacl -d -m u:alice:rw /shared/dir

# Remove a specific entry
setfacl -x u:alice file.txt

# Remove all ACL entries (back to classic permissions)
setfacl -b file.txt

# Copy ACL from one file to another
getfacl source.txt | setfacl --set-file=- dest.txt
```

### ACL Interaction with Classic Permissions

When an ACL is set, the classic group permission bits displayed by `ls -l` are replaced by the ACL mask value, and a `+` is appended:

```bash
ls -l file
-rw-rw-r--+ 1 bob devs 100 Mar 15 file
          ↑
          └─ '+' indicates ACL is present
              The 'rw' in group column is actually the MASK value
```

---

## 11. Linux Capabilities

### The Problem with Root

Traditional Unix: either you are root (all-powerful) or you are not. The binary root model is a security problem — a daemon that only needs to bind to port 80 should NOT need full root.

**Linux Capabilities** divide root privileges into ~40 distinct units.

### Key Capabilities

| Capability           | What it allows                                              |
|----------------------|-------------------------------------------------------------|
| `CAP_CHOWN`          | `chown()` — change file ownership                          |
| `CAP_DAC_OVERRIDE`   | Bypass file permission checks (like root for DAC)           |
| `CAP_DAC_READ_SEARCH`| Bypass read/search permission on files and directories      |
| `CAP_FOWNER`         | Bypass permission checks where file UID must match eUID     |
| `CAP_NET_BIND_SERVICE`| Bind to ports < 1024                                       |
| `CAP_NET_RAW`        | Use raw sockets (e.g., ping)                                |
| `CAP_SYS_ADMIN`      | Broad admin operations (mount, swapon, etc.)               |
| `CAP_SETUID`         | `setuid()`, `setresuid()` — change UID                     |
| `CAP_KILL`           | Send signals to any process                                 |
| `CAP_SYS_PTRACE`     | `ptrace()` — attach to any process                        |

### Capability Sets Per Process

Each process has multiple sets:

```
Permitted (P):     the maximum set of capabilities this process can ever have
Inheritable (I):   capabilities preserved across execve()
Effective (E):     capabilities currently active (used for permission checks)
Bounding (B):      hard limit — caps can only be removed, never added beyond this
Ambient (A):       inherited by child processes even for non-privileged execs
```

### Viewing Capabilities

```bash
# Process capabilities
cat /proc/self/status | grep Cap
# Returns hex bitmasks — decode with:
capsh --decode=0000003fffffffff

# File capabilities
getcap /usr/bin/ping
# /usr/bin/ping cap_net_raw=ep

# Set file capability (instead of SetUID root)
setcap cap_net_bind_service=ep /usr/local/bin/server
```

### How File Capabilities Work

```
When executing a file:
  P' = (P ∩ I) ∪ (F_permitted ∩ bounding)
  E' = P' ∩ F_effective
  I' = P ∩ I ∩ F_inheritable

  Where:
    P = process permitted set
    I = process inheritable set
    F_permitted = file permitted caps
    F_inheritable = file inheritable caps
    F_effective = file effective bit (applies all permitted)
```

The practical use: grant `cap_net_bind_service=ep` on a binary and it can bind port 80 without being SetUID root.

---

## 12. Key System Calls Reference

### Permission-Related Syscalls

| Syscall      | Purpose                                        | Header              |
|--------------|------------------------------------------------|---------------------|
| `stat()`     | Get file metadata including mode, uid, gid     | `<sys/stat.h>`      |
| `lstat()`    | Like stat but doesn't follow symlinks          | `<sys/stat.h>`      |
| `fstat()`    | stat on open file descriptor                   | `<sys/stat.h>`      |
| `chmod()`    | Change file mode by path                       | `<sys/stat.h>`      |
| `fchmod()`   | Change file mode by fd                         | `<sys/stat.h>`      |
| `chown()`    | Change file owner/group by path                | `<unistd.h>`        |
| `fchown()`   | Change file owner/group by fd                  | `<unistd.h>`        |
| `lchown()`   | chown on symlink itself                        | `<unistd.h>`        |
| `umask()`    | Set process umask                              | `<sys/stat.h>`      |
| `access()`   | Check permissions (uses real UID — **avoid**)  | `<unistd.h>`        |
| `faccessat()`| access() with dirfd + flags                    | `<unistd.h>`        |
| `open()`     | Open file — real permission check happens here | `<fcntl.h>`         |
| `openat()`   | open() relative to dirfd (prefer this)         | `<fcntl.h>`         |
| `getxattr()` | Read extended attribute (ACLs)                 | `<sys/xattr.h>`     |
| `setxattr()` | Write extended attribute (ACLs)                | `<sys/xattr.h>`     |

### Stat Macros for Type Checking

```c
S_ISREG(mode)    /* regular file    */
S_ISDIR(mode)    /* directory       */
S_ISLNK(mode)    /* symbolic link   */
S_ISCHR(mode)    /* character device*/
S_ISBLK(mode)    /* block device    */
S_ISFIFO(mode)   /* FIFO / pipe     */
S_ISSOCK(mode)   /* socket          */
```

---

## 13. C Implementation — Full Permission Toolkit

This is a production-grade toolkit demonstrating all permission operations with proper error handling, no magic numbers, and safe coding practices.

```c
/*
 * perm_toolkit.c — Linux Filesystem Permissions Toolkit
 *
 * Demonstrates:
 *   - Reading and printing permissions (stat)
 *   - Changing mode bits (chmod)
 *   - Changing ownership (chown)
 *   - umask manipulation
 *   - Permission bit construction and analysis
 *   - SetUID/SetGID/Sticky detection
 *   - Safe file creation with explicit permissions
 *
 * Compile: gcc -Wall -Wextra -O2 -o perm_toolkit perm_toolkit.c
 */

#define _GNU_SOURCE  /* for AT_FDCWD, faccessat */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <pwd.h>
#include <grp.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>

/* ─── Named Constants — No Magic Numbers ─────────────────────── */

#define PERM_STRING_LEN     11    /* "-rwxrwxrwx\0" */
#define TIME_STRING_LEN     32    /* ctime_r buffer  */
#define NAME_BUFFER_LEN     256   /* username/groupname buffer */

/* Safe file creation modes */
#define MODE_PRIVATE_FILE   (S_IRUSR | S_IWUSR)                        /* 0600 */
#define MODE_PRIVATE_DIR    (S_IRWXU)                                   /* 0700 */
#define MODE_PUBLIC_FILE    (S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)    /* 0644 */
#define MODE_PUBLIC_DIR     (S_IRWXU | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH) /* 0755 */
#define MODE_SHARED_FILE    (S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP)    /* 0660 */
#define MODE_SHARED_DIR     (S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)    /* 0775 */


/* ─── Error Handling Helpers ─────────────────────────────────── */

#define DIE_ON_ERROR(condition, msg) \
    do { \
        if (condition) { \
            fprintf(stderr, "[ERROR] %s: %s (errno=%d)\n", \
                    (msg), strerror(errno), errno); \
            exit(EXIT_FAILURE); \
        } \
    } while (0)

#define WARN_ON_ERROR(condition, msg) \
    do { \
        if (condition) { \
            fprintf(stderr, "[WARN] %s: %s (errno=%d)\n", \
                    (msg), strerror(errno), errno); \
        } \
    } while (0)


/* ─── Permission String Construction ─────────────────────────── */

/*
 * mode_to_string — Convert mode_t to human-readable permission string.
 *
 * Output format: "drwxr-xr-x"  (11 chars including null terminator)
 *   buf must be at least PERM_STRING_LEN bytes.
 *
 * Design note: We build this manually from bitmasks rather than using
 * strmode() (non-standard) to ensure portability and clarity.
 */
void mode_to_string(mode_t mode, char buf[static PERM_STRING_LEN])
{
    /* File type character */
    if      (S_ISREG(mode))  buf[0] = '-';
    else if (S_ISDIR(mode))  buf[0] = 'd';
    else if (S_ISLNK(mode))  buf[0] = 'l';
    else if (S_ISCHR(mode))  buf[0] = 'c';
    else if (S_ISBLK(mode))  buf[0] = 'b';
    else if (S_ISFIFO(mode)) buf[0] = 'p';
    else if (S_ISSOCK(mode)) buf[0] = 's';
    else                     buf[0] = '?';

    /* Owner (user) bits */
    buf[1] = (mode & S_IRUSR) ? 'r' : '-';
    buf[2] = (mode & S_IWUSR) ? 'w' : '-';
    /* SetUID: 's' if execute also set, 'S' if only SetUID */
    if (mode & S_ISUID)
        buf[3] = (mode & S_IXUSR) ? 's' : 'S';
    else
        buf[3] = (mode & S_IXUSR) ? 'x' : '-';

    /* Group bits */
    buf[4] = (mode & S_IRGRP) ? 'r' : '-';
    buf[5] = (mode & S_IWGRP) ? 'w' : '-';
    /* SetGID: 's' if execute also set */
    if (mode & S_ISGID)
        buf[6] = (mode & S_IXGRP) ? 's' : 'S';
    else
        buf[6] = (mode & S_IXGRP) ? 'x' : '-';

    /* Others bits */
    buf[7] = (mode & S_IROTH) ? 'r' : '-';
    buf[8] = (mode & S_IWOTH) ? 'w' : '-';
    /* Sticky bit */
    if (mode & S_ISVTX)
        buf[9] = (mode & S_IXOTH) ? 't' : 'T';
    else
        buf[9] = (mode & S_IXOTH) ? 'x' : '-';

    buf[10] = '\0';
}

/*
 * mode_to_octal_string — Convert mode_t to 4-digit octal string.
 * buf must be at least 6 bytes ("04755\0").
 */
void mode_to_octal_string(mode_t mode, char buf[static 6])
{
    snprintf(buf, 6, "0%04o", (unsigned int)(mode & 07777));
}


/* ─── Identity Resolution ─────────────────────────────────────── */

/*
 * uid_to_name — Resolve UID to username.
 * Returns pointer to buf on success, or numeric string on failure.
 * Thread-safe: uses getpwuid_r.
 */
const char *uid_to_name(uid_t uid, char buf[static NAME_BUFFER_LEN])
{
    struct passwd pw;
    struct passwd *result = NULL;
    char work_buf[1024];

    int ret = getpwuid_r(uid, &pw, work_buf, sizeof(work_buf), &result);
    if (ret == 0 && result != NULL) {
        snprintf(buf, NAME_BUFFER_LEN, "%s", pw.pw_name);
    } else {
        snprintf(buf, NAME_BUFFER_LEN, "%u", (unsigned int)uid);
    }
    return buf;
}

/*
 * gid_to_name — Resolve GID to group name.
 * Thread-safe: uses getgrgid_r.
 */
const char *gid_to_name(gid_t gid, char buf[static NAME_BUFFER_LEN])
{
    struct group gr;
    struct group *result = NULL;
    char work_buf[1024];

    int ret = getgrgid_r(gid, &gr, work_buf, sizeof(work_buf), &result);
    if (ret == 0 && result != NULL) {
        snprintf(buf, NAME_BUFFER_LEN, "%s", gr.gr_name);
    } else {
        snprintf(buf, NAME_BUFFER_LEN, "%u", (unsigned int)gid);
    }
    return buf;
}


/* ─── File Information Display ────────────────────────────────── */

/*
 * print_file_info — Display comprehensive file metadata.
 * Demonstrates reading and interpreting struct stat.
 */
int print_file_info(const char *path)
{
    struct stat st;
    char perm_str[PERM_STRING_LEN];
    char octal_str[6];
    char owner_name[NAME_BUFFER_LEN];
    char group_name[NAME_BUFFER_LEN];
    char time_buf[TIME_STRING_LEN];

    /*
     * Use lstat() to inspect symlinks themselves.
     * stat() would follow the link and show target's info.
     */
    if (lstat(path, &st) != 0) {
        fprintf(stderr, "lstat(%s): %s\n", path, strerror(errno));
        return -1;
    }

    mode_to_string(st.st_mode, perm_str);
    mode_to_octal_string(st.st_mode, octal_str);
    uid_to_name(st.st_uid, owner_name);
    gid_to_name(st.st_gid, group_name);

    /* Format modification time */
    struct tm *tm_info = localtime(&st.st_mtime);
    strftime(time_buf, sizeof(time_buf), "%Y-%m-%d %H:%M:%S", tm_info);

    printf("┌─────────────────────────────────────────────┐\n");
    printf("│ File: %-39s│\n", path);
    printf("├─────────────────────────────────────────────┤\n");
    printf("│ Permissions : %-10s  (%s)            │\n", perm_str, octal_str);
    printf("│ Owner       : %-20s (uid=%u) │\n",
           owner_name, (unsigned int)st.st_uid);
    printf("│ Group       : %-20s (gid=%u) │\n",
           group_name, (unsigned int)st.st_gid);
    printf("│ Inode       : %-10lu                    │\n",
           (unsigned long)st.st_ino);
    printf("│ Size        : %-10lld bytes              │\n",
           (long long)st.st_size);
    printf("│ Hard links  : %-10lu                    │\n",
           (unsigned long)st.st_nlink);
    printf("│ Modified    : %s                  │\n", time_buf);

    /* Decode special bits */
    if (st.st_mode & S_ISUID) printf("│ *** SetUID bit is SET ***                   │\n");
    if (st.st_mode & S_ISGID) printf("│ *** SetGID bit is SET ***                   │\n");
    if (st.st_mode & S_ISVTX) printf("│ *** Sticky bit is SET ***                   │\n");

    printf("└─────────────────────────────────────────────┘\n");
    return 0;
}


/* ─── Permission Analysis ─────────────────────────────────────── */

/*
 * analyze_permissions — Verbose breakdown of who can do what.
 * This mirrors the kernel's permission evaluation algorithm exactly.
 */
void analyze_permissions(mode_t mode)
{
    printf("\n=== Permission Analysis ===\n");
    printf("Mode: %04o\n\n", (unsigned int)(mode & 07777));

    const char *categories[] = {"Owner", "Group", "Others"};
    const mode_t read_bits[]  = { S_IRUSR, S_IRGRP, S_IROTH };
    const mode_t write_bits[] = { S_IWUSR, S_IWGRP, S_IWOTH };
    const mode_t exec_bits[]  = { S_IXUSR, S_IXGRP, S_IXOTH };

    for (int i = 0; i < 3; i++) {
        printf("  %-8s: %s%s%s\n",
               categories[i],
               (mode & read_bits[i])  ? "READ  " : "      ",
               (mode & write_bits[i]) ? "WRITE " : "      ",
               (mode & exec_bits[i])  ? "EXECUTE" : "");
    }

    printf("\n  Special bits:\n");
    printf("    SetUID : %s\n", (mode & S_ISUID) ? "YES (privilege escalation to owner UID)" : "no");
    printf("    SetGID : %s\n", (mode & S_ISGID) ? "YES (escalation to owner GID / dir inherit)" : "no");
    printf("    Sticky : %s\n", (mode & S_ISVTX) ? "YES (restricted deletion in directory)" : "no");
}


/* ─── umask Operations ────────────────────────────────────────── */

/*
 * demonstrate_umask — Show umask interaction with file creation.
 *
 * Design note: We temporarily set umask to 0 before calling open()
 * to get the exact mode we request. Then we restore the original umask.
 * This is the correct pattern for security-sensitive file creation.
 */
int create_file_with_exact_mode(const char *path, mode_t requested_mode)
{
    mode_t old_umask = umask(0);  /* Disable umask temporarily */

    /*
     * O_NOFOLLOW prevents symlink attacks (TOCTOU mitigation).
     * O_CLOEXEC prevents fd leak across exec().
     */
    int fd = open(path,
                  O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC,
                  requested_mode);
    int saved_errno = errno;

    umask(old_umask);  /* Always restore — even on error */

    if (fd < 0) {
        errno = saved_errno;
        fprintf(stderr, "open(%s): %s\n", path, strerror(errno));
        return -1;
    }

    printf("Created '%s' with exact mode %04o\n",
           path, (unsigned int)requested_mode);
    close(fd);
    return 0;
}

/*
 * demonstrate_umask_effect — Show how umask filters creation modes.
 */
void demonstrate_umask_effect(void)
{
    mode_t current_umask = umask(0);
    umask(current_umask);  /* Restore immediately — we just wanted to read it */

    printf("\n=== umask Demonstration ===\n");
    printf("Current umask: %04o\n\n", (unsigned int)current_umask);

    const mode_t test_modes[] = {0777, 0666, 0644, 0600, 0755};
    const size_t n_modes = sizeof(test_modes) / sizeof(test_modes[0]);

    printf("  Requested  -->  After umask(%04o)\n", (unsigned int)current_umask);
    printf("  ---------------------------------\n");
    for (size_t i = 0; i < n_modes; i++) {
        mode_t result = test_modes[i] & ~current_umask;
        printf("  %04o       -->  %04o\n",
               (unsigned int)test_modes[i],
               (unsigned int)result);
    }
}


/* ─── Permission Manipulation ─────────────────────────────────── */

/*
 * safe_chmod — Change mode using fd (not path) to avoid TOCTOU races.
 *
 * Pattern: open file first, verify it is what we expect, then fchmod.
 * This is safer than chmod(path, mode) because the path cannot change
 * between the open() and fchmod() calls.
 */
int safe_chmod(const char *path, mode_t new_mode)
{
    struct stat st_before;
    struct stat st_after;

    if (lstat(path, &st_before) != 0) {
        fprintf(stderr, "lstat before chmod(%s): %s\n", path, strerror(errno));
        return -1;
    }

    /* Do not follow symlinks for chmod — use fchmodat with AT_SYMLINK_NOFOLLOW
     * Note: AT_SYMLINK_NOFOLLOW for fchmodat is Linux 5.12+ / not widely supported
     * For regular files, open + fchmod is the safe approach. */
    if (!S_ISLNK(st_before.st_mode)) {
        int fd = open(path, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
        if (fd < 0) {
            fprintf(stderr, "open for chmod(%s): %s\n", path, strerror(errno));
            return -1;
        }

        if (fstat(fd, &st_after) != 0) {
            fprintf(stderr, "fstat(%s): %s\n", path, strerror(errno));
            close(fd);
            return -1;
        }

        /* Verify inode hasn't changed between lstat and open (TOCTOU check) */
        if (st_before.st_ino != st_after.st_ino ||
            st_before.st_dev != st_after.st_dev) {
            fprintf(stderr, "TOCTOU detected on %s — inode changed!\n", path);
            close(fd);
            return -1;
        }

        if (fchmod(fd, new_mode) != 0) {
            fprintf(stderr, "fchmod(%s, %04o): %s\n",
                    path, (unsigned int)new_mode, strerror(errno));
            close(fd);
            return -1;
        }

        printf("chmod: %s → %04o\n", path, (unsigned int)new_mode);
        close(fd);
    } else {
        fprintf(stderr, "Refusing to chmod symlink: %s\n", path);
        return -1;
    }

    return 0;
}

/*
 * safe_chown — Change ownership using fd to avoid TOCTOU.
 * Pass -1 for uid or gid to leave it unchanged.
 */
int safe_chown(const char *path, uid_t new_uid, gid_t new_gid)
{
    int fd = open(path, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "open for chown(%s): %s\n", path, strerror(errno));
        return -1;
    }

    if (fchown(fd, new_uid, new_gid) != 0) {
        fprintf(stderr, "fchown(%s): %s\n", path, strerror(errno));
        close(fd);
        return -1;
    }

    printf("chown: %s → uid=%d, gid=%d\n",
           path, (int)new_uid, (int)new_gid);
    close(fd);
    return 0;
}


/* ─── Current Process Identity ────────────────────────────────── */

void print_process_identity(void)
{
    char name_buf[NAME_BUFFER_LEN];

    printf("\n=== Process Identity ===\n");
    printf("  Real UID      (ruid): %u (%s)\n",
           (unsigned)getuid(),  uid_to_name(getuid(),  name_buf));
    printf("  Effective UID (euid): %u (%s)\n",
           (unsigned)geteuid(), uid_to_name(geteuid(), name_buf));
    printf("  Real GID      (rgid): %u\n", (unsigned)getgid());
    printf("  Effective GID (egid): %u\n", (unsigned)getegid());

    /* Supplementary groups */
    int n_groups = getgroups(0, NULL);
    if (n_groups > 0) {
        gid_t *groups = malloc((size_t)n_groups * sizeof(gid_t));
        DIE_ON_ERROR(groups == NULL, "malloc for groups");

        getgroups(n_groups, groups);
        printf("  Supplementary GIDs: ");
        for (int i = 0; i < n_groups; i++) {
            printf("%u ", (unsigned)groups[i]);
        }
        printf("\n");
        free(groups);
    }
}


/* ─── Permission Simulation ──────────────────────────────────── */

/*
 * simulate_access — Simulate the kernel permission check algorithm.
 * 
 * This is an educational implementation of the kernel's
 * inode_permission() logic. Not a replacement for actual syscalls.
 *
 * Returns:
 *   0  — access would be granted
 *  -1  — access would be denied
 */
int simulate_access(
    uid_t euid,
    gid_t egid,
    const gid_t *supp_groups,
    int n_supp_groups,
    uid_t file_uid,
    gid_t file_gid,
    mode_t file_mode,
    int want_read,
    int want_write,
    int want_exec)
{
    mode_t check_bits = 0;
    int    is_dir     = S_ISDIR(file_mode);

    /* Step 1: Root bypass */
    if (euid == 0) {
        /* Root can read/write anything. */
        if (want_read || want_write) return 0;
        /* Root can execute only if any execute bit is set. */
        if (want_exec) {
            if (is_dir) return 0;
            return (file_mode & (S_IXUSR | S_IXGRP | S_IXOTH)) ? 0 : -1;
        }
        return 0;
    }

    /* Step 2: Determine which permission group applies */
    if (euid == file_uid) {
        /* Use OWNER bits — group bits ignored even if more permissive */
        check_bits = (file_mode >> 6) & 07;
    } else {
        /* Check if process is in file's group */
        int in_group = (egid == file_gid);
        if (!in_group && supp_groups != NULL) {
            for (int i = 0; i < n_supp_groups; i++) {
                if (supp_groups[i] == file_gid) {
                    in_group = 1;
                    break;
                }
            }
        }

        if (in_group) {
            check_bits = (file_mode >> 3) & 07;  /* GROUP bits */
        } else {
            check_bits = (file_mode >> 0) & 07;  /* OTHERS bits */
        }
    }

    /* Step 3: Check requested permissions against selected bits */
    if (want_read  && !(check_bits & 04)) return -1;
    if (want_write && !(check_bits & 02)) return -1;
    if (want_exec  && !(check_bits & 01)) return -1;

    return 0;
}


/* ─── Main — Demonstration Driver ────────────────────────────── */

int main(int argc, char *argv[])
{
    printf("╔════════════════════════════════════════════╗\n");
    printf("║   Linux Filesystem Permissions Toolkit    ║\n");
    printf("╚════════════════════════════════════════════╝\n\n");

    /* 1. Display current process identity */
    print_process_identity();

    /* 2. Inspect file(s) passed as arguments, or use defaults */
    const char *targets[] = {"/etc/passwd", "/etc/shadow", "/tmp", "/bin/passwd"};
    int n_targets = (int)(sizeof(targets) / sizeof(targets[0]));

    if (argc > 1) {
        printf("\n=== File Information ===\n");
        for (int i = 1; i < argc; i++) {
            printf("\n");
            print_file_info(argv[i]);
            struct stat st;
            if (lstat(argv[i], &st) == 0) {
                analyze_permissions(st.st_mode);
            }
        }
    } else {
        printf("\n=== Inspecting System Files ===\n");
        for (int i = 0; i < n_targets; i++) {
            printf("\n");
            print_file_info(targets[i]);
        }
    }

    /* 3. Demonstrate umask */
    demonstrate_umask_effect();

    /* 4. Simulate permission checks */
    printf("\n=== Permission Simulation ===\n");
    /*
     * Scenario: file owned by root:root with mode 0644
     * Check if user uid=1000, gid=1000 can read, write, execute
     */
    mode_t test_mode = S_IFREG | 0644;
    uid_t  file_uid  = 0;    /* root owns it */
    gid_t  file_gid  = 0;    /* root group   */
    uid_t  test_euid = 1000; /* regular user */
    gid_t  test_egid = 1000;

    printf("File: uid=%u gid=%u mode=%04o\n",
           (unsigned)file_uid, (unsigned)file_gid,
           (unsigned)(test_mode & 07777));
    printf("Process: euid=%u egid=%u\n",
           (unsigned)test_euid, (unsigned)test_egid);

    int can_read  = (simulate_access(test_euid, test_egid, NULL, 0,
                                      file_uid, file_gid, test_mode,
                                      1, 0, 0) == 0);
    int can_write = (simulate_access(test_euid, test_egid, NULL, 0,
                                      file_uid, file_gid, test_mode,
                                      0, 1, 0) == 0);
    int can_exec  = (simulate_access(test_euid, test_egid, NULL, 0,
                                      file_uid, file_gid, test_mode,
                                      0, 0, 1) == 0);

    printf("  Read  : %s\n", can_read  ? "ALLOWED" : "DENIED");
    printf("  Write : %s\n", can_write ? "ALLOWED" : "DENIED");
    printf("  Exec  : %s\n", can_exec  ? "ALLOWED" : "DENIED");

    printf("\nDone.\n");
    return EXIT_SUCCESS;
}
```

---

## 14. Rust Implementation — Safe Permissions Library

This implementation provides a type-safe, idiomatic Rust library for working with Linux permissions.

```rust
//! perm_lib.rs — Linux Filesystem Permissions Library
//!
//! Demonstrates:
//!   - Safe stat() calls with proper error propagation
//!   - Type-safe permission bit manipulation using bitflags
//!   - Process identity inspection
//!   - Permission string formatting
//!   - File creation with exact permissions
//!   - Ownership changes
//!
//! # Build
//! Add to Cargo.toml:
//!   [dependencies]
//!   libc = "0.2"
//!   bitflags = "2.0"
//!
//! Or run: cargo new perm_demo && cd perm_demo
//! Replace src/main.rs with this file, update Cargo.toml.

use std::ffi::CString;
use std::fmt;
use std::io;
use std::path::Path;

// ─── Raw libc bindings ────────────────────────────────────────
//
// We call libc directly to demonstrate the actual syscalls.
// In production, you would use the `nix` crate which wraps these
// with idiomatic types, or `std::fs::metadata` for basic stat.

extern crate libc;
use libc::{
    gid_t, mode_t, off_t, uid_t,
    S_IFBLK, S_IFCHR, S_IFDIR, S_IFIFO, S_IFLNK, S_IFREG, S_IFSOCK, S_IFMT,
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH,
    S_ISUID, S_ISGID, S_ISVTX,
};


// ─── FileType ─────────────────────────────────────────────────

/// Represents the type of a filesystem object, decoded from mode_t.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FileType {
    RegularFile,
    Directory,
    SymbolicLink,
    CharDevice,
    BlockDevice,
    NamedPipe,
    Socket,
    Unknown(u32),
}

impl FileType {
    /// Decode file type from the raw mode bits.
    pub fn from_mode(mode: mode_t) -> Self {
        match mode & S_IFMT as mode_t {
            m if m == S_IFREG as mode_t  => FileType::RegularFile,
            m if m == S_IFDIR as mode_t  => FileType::Directory,
            m if m == S_IFLNK as mode_t  => FileType::SymbolicLink,
            m if m == S_IFCHR as mode_t  => FileType::CharDevice,
            m if m == S_IFBLK as mode_t  => FileType::BlockDevice,
            m if m == S_IFIFO as mode_t  => FileType::NamedPipe,
            m if m == S_IFSOCK as mode_t => FileType::Socket,
            other                         => FileType::Unknown(other as u32),
        }
    }

    /// The single-character code used in `ls -l` output.
    pub fn as_char(self) -> char {
        match self {
            FileType::RegularFile  => '-',
            FileType::Directory    => 'd',
            FileType::SymbolicLink => 'l',
            FileType::CharDevice   => 'c',
            FileType::BlockDevice  => 'b',
            FileType::NamedPipe    => 'p',
            FileType::Socket       => 's',
            FileType::Unknown(_)   => '?',
        }
    }
}

impl fmt::Display for FileType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let name = match self {
            FileType::RegularFile  => "regular file",
            FileType::Directory    => "directory",
            FileType::SymbolicLink => "symbolic link",
            FileType::CharDevice   => "character device",
            FileType::BlockDevice  => "block device",
            FileType::NamedPipe    => "named pipe",
            FileType::Socket       => "socket",
            FileType::Unknown(_)   => "unknown",
        };
        write!(f, "{name}")
    }
}


// ─── PermissionBits ───────────────────────────────────────────

/// The 9 classic permission bits (rwxrwxrwx) as a newtype.
/// We wrap mode_t & 0o777 to ensure invariants.
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct PermissionBits(mode_t);

impl PermissionBits {
    /// Bitmask constants — named for clarity
    pub const OWNER_READ:    mode_t = S_IRUSR as mode_t;
    pub const OWNER_WRITE:   mode_t = S_IWUSR as mode_t;
    pub const OWNER_EXECUTE: mode_t = S_IXUSR as mode_t;
    pub const GROUP_READ:    mode_t = S_IRGRP as mode_t;
    pub const GROUP_WRITE:   mode_t = S_IWGRP as mode_t;
    pub const GROUP_EXECUTE: mode_t = S_IXGRP as mode_t;
    pub const OTHER_READ:    mode_t = S_IROTH as mode_t;
    pub const OTHER_WRITE:   mode_t = S_IWOTH as mode_t;
    pub const OTHER_EXECUTE: mode_t = S_IXOTH as mode_t;

    /// Construct from a raw mode value (lower 9 bits used).
    pub fn from_mode(mode: mode_t) -> Self {
        PermissionBits(mode & 0o777)
    }

    pub fn raw(self) -> mode_t { self.0 }

    pub fn owner_read(self)    -> bool { self.0 & Self::OWNER_READ    != 0 }
    pub fn owner_write(self)   -> bool { self.0 & Self::OWNER_WRITE   != 0 }
    pub fn owner_execute(self) -> bool { self.0 & Self::OWNER_EXECUTE != 0 }
    pub fn group_read(self)    -> bool { self.0 & Self::GROUP_READ    != 0 }
    pub fn group_write(self)   -> bool { self.0 & Self::GROUP_WRITE   != 0 }
    pub fn group_execute(self) -> bool { self.0 & Self::GROUP_EXECUTE != 0 }
    pub fn other_read(self)    -> bool { self.0 & Self::OTHER_READ    != 0 }
    pub fn other_write(self)   -> bool { self.0 & Self::OTHER_WRITE   != 0 }
    pub fn other_execute(self) -> bool { self.0 & Self::OTHER_EXECUTE != 0 }
}

impl fmt::Display for PermissionBits {
    /// Renders as "rwxr-xr-x" (9 characters, no type prefix)
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let bit = |set: bool, c: char| if set { c } else { '-' };
        write!(
            f,
            "{}{}{}{}{}{}{}{}{}",
            bit(self.owner_read(),    'r'),
            bit(self.owner_write(),   'w'),
            bit(self.owner_execute(), 'x'),
            bit(self.group_read(),    'r'),
            bit(self.group_write(),   'w'),
            bit(self.group_execute(), 'x'),
            bit(self.other_read(),    'r'),
            bit(self.other_write(),   'w'),
            bit(self.other_execute(), 'x'),
        )
    }
}

impl fmt::Debug for PermissionBits {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "PermissionBits(0o{:03o} = {})", self.0, self)
    }
}


// ─── SpecialBits ──────────────────────────────────────────────

/// The three special permission bits: SetUID, SetGID, Sticky.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SpecialBits {
    pub setuid: bool,
    pub setgid: bool,
    pub sticky: bool,
}

impl SpecialBits {
    pub fn from_mode(mode: mode_t) -> Self {
        SpecialBits {
            setuid: mode & S_ISUID as mode_t != 0,
            setgid: mode & S_ISGID as mode_t != 0,
            sticky: mode & S_ISVTX as mode_t != 0,
        }
    }

    pub fn none() -> Self {
        SpecialBits { setuid: false, setgid: false, sticky: false }
    }

    pub fn raw(self) -> mode_t {
        let mut bits: mode_t = 0;
        if self.setuid { bits |= S_ISUID as mode_t; }
        if self.setgid { bits |= S_ISGID as mode_t; }
        if self.sticky { bits |= S_ISVTX as mode_t; }
        bits
    }
}


// ─── FileMode — Complete Mode Representation ──────────────────

/// Complete decoded representation of a file's mode_t.
#[derive(Debug, Clone, Copy)]
pub struct FileMode {
    pub file_type:    FileType,
    pub special:      SpecialBits,
    pub permissions:  PermissionBits,
}

impl FileMode {
    /// Decode all components of a raw mode_t value.
    pub fn from_raw(mode: mode_t) -> Self {
        FileMode {
            file_type:   FileType::from_mode(mode),
            special:     SpecialBits::from_mode(mode),
            permissions: PermissionBits::from_mode(mode),
        }
    }

    /// Reconstruct the raw mode_t.
    pub fn to_raw(self) -> mode_t {
        // File type bits are read-only — not reconstructed here.
        // Returns permission + special bits only (suitable for chmod).
        self.special.raw() | self.permissions.raw()
    }

    /// Format as the 10-character ls -l string ("drwxr-xr-x")
    pub fn ls_string(self) -> String {
        let type_char = self.file_type.as_char();

        // For the special bits, we need to modify the x columns
        let owner_exec_char = match (self.special.setuid, self.permissions.owner_execute()) {
            (true,  true)  => 's',
            (true,  false) => 'S',
            (false, true)  => 'x',
            (false, false) => '-',
        };
        let group_exec_char = match (self.special.setgid, self.permissions.group_execute()) {
            (true,  true)  => 's',
            (true,  false) => 'S',
            (false, true)  => 'x',
            (false, false) => '-',
        };
        let other_exec_char = match (self.special.sticky, self.permissions.other_execute()) {
            (true,  true)  => 't',
            (true,  false) => 'T',
            (false, true)  => 'x',
            (false, false) => '-',
        };

        let bit = |set: bool, c: char| if set { c } else { '-' };
        format!(
            "{}{}{}{}{}{}{}{}{}{}",
            type_char,
            bit(self.permissions.owner_read(), 'r'),
            bit(self.permissions.owner_write(), 'w'),
            owner_exec_char,
            bit(self.permissions.group_read(), 'r'),
            bit(self.permissions.group_write(), 'w'),
            group_exec_char,
            bit(self.permissions.other_read(), 'r'),
            bit(self.permissions.other_write(), 'w'),
            other_exec_char,
        )
    }

    /// Format as 4-digit octal string including special bits.
    pub fn octal_string(self) -> String {
        format!("{:04o}", self.to_raw())
    }
}

impl fmt::Display for FileMode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} ({})", self.ls_string(), self.octal_string())
    }
}


// ─── FileStat — Decoded stat structure ────────────────────────

/// Decoded and owned representation of struct stat.
#[derive(Debug, Clone)]
pub struct FileStat {
    pub path:      String,
    pub mode:      FileMode,
    pub uid:       uid_t,
    pub gid:       gid_t,
    pub size:      off_t,
    pub nlink:     u64,
    pub inode:     u64,
    pub device:    u64,
    pub mtime_sec: i64,
}

impl FileStat {
    /// Stat a path without following symlinks.
    /// Returns io::Error on failure with the path included in context.
    pub fn lstat<P: AsRef<Path>>(path: P) -> io::Result<Self> {
        let path_str = path.as_ref()
            .to_str()
            .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "non-UTF-8 path"))?;

        let c_path = CString::new(path_str)
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidInput, e))?;

        // Safety: We hold a valid CString; libc::stat64 fills the struct.
        let mut raw_stat = unsafe { std::mem::zeroed::<libc::stat64>() };
        let ret = unsafe { libc::lstat64(c_path.as_ptr(), &mut raw_stat) };

        if ret != 0 {
            return Err(io::Error::last_os_error());
        }

        Ok(FileStat {
            path:      path_str.to_owned(),
            mode:      FileMode::from_raw(raw_stat.st_mode as mode_t),
            uid:       raw_stat.st_uid,
            gid:       raw_stat.st_gid,
            size:      raw_stat.st_size,
            nlink:     raw_stat.st_nlink as u64,
            inode:     raw_stat.st_ino as u64,
            device:    raw_stat.st_dev as u64,
            mtime_sec: raw_stat.st_mtime,
        })
    }

    /// Display a formatted report of this file's permissions.
    pub fn display_report(&self) {
        println!("┌─────────────────────────────────────────────┐");
        println!("│ Path  : {:<37}│", self.path);
        println!("│ Type  : {:<37}│", self.mode.file_type.to_string());
        println!("│ Mode  : {:<37}│", self.mode.to_string());
        println!("│ Owner : uid={:<5}  gid={:<5}                   │",
                 self.uid, self.gid);
        println!("│ Inode : {:<37}│", self.inode);
        println!("│ Size  : {:<37}│", format!("{} bytes", self.size));
        println!("│ Links : {:<37}│", self.nlink);
        if self.mode.special.setuid {
            println!("│ *** SetUID is SET ***                       │");
        }
        if self.mode.special.setgid {
            println!("│ *** SetGID is SET ***                       │");
        }
        if self.mode.special.sticky {
            println!("│ *** Sticky is SET ***                       │");
        }
        println!("└─────────────────────────────────────────────┘");
    }
}


// ─── Permission Checker ───────────────────────────────────────

/// Desired access flags for a permission check.
#[derive(Debug, Clone, Copy)]
pub struct AccessRequest {
    pub read:    bool,
    pub write:   bool,
    pub execute: bool,
}

impl AccessRequest {
    pub fn read()    -> Self { AccessRequest { read: true,  write: false, execute: false } }
    pub fn write()   -> Self { AccessRequest { read: false, write: true,  execute: false } }
    pub fn execute() -> Self { AccessRequest { read: false, write: false, execute: true  } }
    pub fn all()     -> Self { AccessRequest { read: true,  write: true,  execute: true  } }
}

/// Identity of a process for permission simulation.
#[derive(Debug)]
pub struct ProcessIdentity {
    pub euid:            uid_t,
    pub egid:            gid_t,
    pub supplementary:   Vec<gid_t>,
}

impl ProcessIdentity {
    /// Capture the actual identity of the current process.
    pub fn current() -> Self {
        // Safety: these syscalls always succeed for the calling process.
        let euid = unsafe { libc::geteuid() };
        let egid = unsafe { libc::getegid() };

        let n_groups = unsafe { libc::getgroups(0, std::ptr::null_mut()) };
        let supplementary = if n_groups > 0 {
            let mut groups = vec![0 as gid_t; n_groups as usize];
            unsafe { libc::getgroups(n_groups, groups.as_mut_ptr()) };
            groups
        } else {
            Vec::new()
        };

        ProcessIdentity { euid, egid, supplementary }
    }
}

/// Simulate the kernel permission check (POSIX semantics).
/// Returns Ok(()) if access would be granted, Err(EACCES-equivalent) if denied.
pub fn check_permission(
    identity: &ProcessIdentity,
    stat: &FileStat,
    request: AccessRequest,
) -> Result<(), &'static str> {
    let perms = stat.mode.permissions;
    let ftype = stat.mode.file_type;

    // Step 1: Root superuser bypass
    if identity.euid == 0 {
        if request.execute {
            // Root needs at least one execute bit to be set (for non-directories)
            if ftype != FileType::Directory {
                let any_exec = perms.owner_execute()
                    || perms.group_execute()
                    || perms.other_execute();
                if !any_exec {
                    return Err("EACCES: root cannot execute file with no execute bits");
                }
            }
        }
        return Ok(());
    }

    // Step 2: Determine which permission group to use
    // Categories are mutually exclusive — owner wins even if group is more permissive
    let (can_read, can_write, can_exec) = if identity.euid == stat.uid {
        // Owner class
        (perms.owner_read(), perms.owner_write(), perms.owner_execute())
    } else {
        let in_group = identity.egid == stat.gid
            || identity.supplementary.contains(&stat.gid);

        if in_group {
            // Group class
            (perms.group_read(), perms.group_write(), perms.group_execute())
        } else {
            // Other class
            (perms.other_read(), perms.other_write(), perms.other_execute())
        }
    };

    // Step 3: Check against requested access
    if request.read    && !can_read  { return Err("EACCES: read permission denied"); }
    if request.write   && !can_write { return Err("EACCES: write permission denied"); }
    if request.execute && !can_exec  { return Err("EACCES: execute permission denied"); }

    Ok(())
}


// ─── Umask Demonstration ──────────────────────────────────────

/// Demonstrate what the current umask would do to various creation modes.
pub fn demonstrate_umask() {
    // Safety: umask() always succeeds; we set and immediately restore.
    let current = unsafe {
        let mask = libc::umask(0o077);
        libc::umask(mask);  // restore
        mask
    };

    println!("\n=== umask Demonstration ===");
    println!("Current umask: {:04o}", current);
    println!();

    let test_modes: &[(mode_t, &str)] = &[
        (0o666, "open() with 0666 (typical file)"),
        (0o777, "mkdir() with 0777 (typical dir)"),
        (0o644, "open() with 0644"),
        (0o600, "open() with 0600 (private)"),
    ];

    println!("  {:<10}  {:<10}  {}", "Requested", "Result", "Description");
    println!("  {:-<10}  {:-<10}  {:-<30}", "", "", "");
    for (requested, desc) in test_modes {
        let result = requested & !current;
        println!("  {:04o}       {:04o}        {}",
                 requested, result, desc);
    }
}


// ─── Main ─────────────────────────────────────────────────────

fn main() {
    println!("╔════════════════════════════════════════════╗");
    println!("║   Rust Linux Permissions Library Demo     ║");
    println!("╚════════════════════════════════════════════╝\n");

    // 1. Current process identity
    let identity = ProcessIdentity::current();
    println!("=== Process Identity ===");
    println!("  euid: {}", identity.euid);
    println!("  egid: {}", identity.egid);
    println!("  supplementary groups: {:?}", identity.supplementary);

    // 2. Inspect some files
    let paths = ["/etc/passwd", "/tmp", "/usr/bin/sudo"];
    println!("\n=== File Inspection ===");
    for path in &paths {
        match FileStat::lstat(path) {
            Ok(stat) => {
                println!();
                stat.display_report();

                // Check if current process can read
                match check_permission(&identity, &stat, AccessRequest::read()) {
                    Ok(_)    => println!("  → Current process CAN read this"),
                    Err(msg) => println!("  → Current process CANNOT read: {msg}"),
                }
            }
            Err(e) => eprintln!("lstat({path}): {e}"),
        }
    }

    // 3. Mode parsing demonstration
    println!("\n=== Mode Parsing ===");
    let interesting_modes: &[(mode_t, &str)] = &[
        (0o100755, "rwxr-xr-x regular executable"),
        (0o100644, "rw-r--r-- regular file"),
        (0o104755, "rwsr-xr-x SetUID executable"),
        (0o102755, "rwxr-sr-x SetGID executable"),
        (0o041777, "drwxrwxrwt sticky directory (/tmp)"),
        (0o040750, "drwxr-x--- private dir"),
        (0o120777, "lrwxrwxrwx symbolic link"),
    ];

    for (raw_mode, desc) in interesting_modes {
        let fm = FileMode::from_raw(*raw_mode);
        println!("  {:04o}  {}  ({})", raw_mode, fm.ls_string(), desc);
    }

    // 4. umask
    demonstrate_umask();

    // 5. Permission analysis on a hypothetical file
    println!("\n=== Permission Logic: The Mutually-Exclusive Category Rule ===");
    println!("Scenario: file mode=0606, owner=alice(1000), group=staff(100)");
    println!("Process: euid=1000 (alice), egid=200 (not staff)");

    let trap_mode = 0o100606u32 as mode_t;
    let trap_stat = FileStat {
        path:      "hypothetical".to_string(),
        mode:      FileMode::from_raw(trap_mode),
        uid:       1000,
        gid:       100,
        size:      0,
        nlink:     1,
        inode:     9999,
        device:    0,
        mtime_sec: 0,
    };
    let alice = ProcessIdentity {
        euid: 1000, egid: 200, supplementary: vec![]
    };

    println!("Mode {} — owner has rw-, others have rw-, group has ---",
             trap_stat.mode);
    println!("Alice is the OWNER, so OWNER bits are used: rw-");
    match check_permission(&alice, &trap_stat, AccessRequest::read()) {
        Ok(_)    => println!("  Read:  ALLOWED (owner bit r=1)"),
        Err(msg) => println!("  Read:  DENIED — {msg}"),
    }
    match check_permission(&alice, &trap_stat, AccessRequest::write()) {
        Ok(_)    => println!("  Write: ALLOWED (owner bit w=1)"),
        Err(msg) => println!("  Write: DENIED — {msg}"),
    }
    println!("NOTE: Other bits (rw-) are irrelevant because alice is the owner.");
}
```

---

## 15. Go Implementation — Permission Inspector Tool

```go
// perm_inspector.go — Linux Filesystem Permission Inspector
//
// Demonstrates:
//   - Reading file permissions using syscall.Stat_t
//   - Decoding mode bits into structured types
//   - Process identity inspection
//   - Permission simulation
//   - Formatting ls-style output
//   - umask handling
//
// Build: go build -o perm_inspector perm_inspector.go
// Run:   ./perm_inspector /etc/passwd /tmp /usr/bin/sudo

//go:build linux

package main

import (
	"errors"
	"fmt"
	"os"
	"strings"
	"syscall"
)

// ─── Constants — Named, No Magic Numbers ──────────────────────

const (
	// Permission bit masks (POSIX)
	OwnerRead    = 0o400
	OwnerWrite   = 0o200
	OwnerExecute = 0o100
	GroupRead    = 0o040
	GroupWrite   = 0o020
	GroupExecute = 0o010
	OtherRead    = 0o004
	OtherWrite   = 0o002
	OtherExecute = 0o001

	// Special permission bits
	SetUID    = 0o4000
	SetGID    = 0o2000
	StickyBit = 0o1000

	// File type mask
	FileTypeMask = 0o170000

	// File type values
	TypeRegular   = 0o100000
	TypeDirectory = 0o040000
	TypeSymlink   = 0o120000
	TypeCharDev   = 0o020000
	TypeBlockDev  = 0o060000
	TypeFIFO      = 0o010000
	TypeSocket    = 0o140000
)

// ─── FileType ─────────────────────────────────────────────────

// FileType represents the type of filesystem object.
type FileType int

const (
	RegularFile FileType = iota
	Directory
	SymbolicLink
	CharDevice
	BlockDevice
	NamedPipe
	Socket
	UnknownType
)

// DecodeFileType extracts file type from raw mode bits.
func DecodeFileType(mode uint32) FileType {
	switch mode & FileTypeMask {
	case TypeRegular:
		return RegularFile
	case TypeDirectory:
		return Directory
	case TypeSymlink:
		return SymbolicLink
	case TypeCharDev:
		return CharDevice
	case TypeBlockDev:
		return BlockDevice
	case TypeFIFO:
		return NamedPipe
	case TypeSocket:
		return Socket
	default:
		return UnknownType
	}
}

// TypeChar returns the ls -l type character.
func (ft FileType) TypeChar() byte {
	switch ft {
	case RegularFile:
		return '-'
	case Directory:
		return 'd'
	case SymbolicLink:
		return 'l'
	case CharDevice:
		return 'c'
	case BlockDevice:
		return 'b'
	case NamedPipe:
		return 'p'
	case Socket:
		return 's'
	default:
		return '?'
	}
}

func (ft FileType) String() string {
	switch ft {
	case RegularFile:
		return "regular file"
	case Directory:
		return "directory"
	case SymbolicLink:
		return "symbolic link"
	case CharDevice:
		return "character device"
	case BlockDevice:
		return "block device"
	case NamedPipe:
		return "named pipe (FIFO)"
	case Socket:
		return "socket"
	default:
		return "unknown"
	}
}

// ─── SpecialBits ──────────────────────────────────────────────

// SpecialBits holds decoded SetUID, SetGID, and sticky state.
type SpecialBits struct {
	SetUID bool
	SetGID bool
	Sticky bool
}

// DecodeSpecialBits extracts special bits from a raw mode value.
func DecodeSpecialBits(mode uint32) SpecialBits {
	return SpecialBits{
		SetUID: mode&SetUID != 0,
		SetGID: mode&SetGID != 0,
		Sticky: mode&StickyBit != 0,
	}
}

// ─── PermSet — One rwx Category ───────────────────────────────

// PermSet represents the read/write/execute bits for one category.
type PermSet struct {
	Read    bool
	Write   bool
	Execute bool
}

// PermSetString formats a PermSet as "rwx", "r-x", etc.
func (p PermSet) String() string {
	b := [3]byte{'-', '-', '-'}
	if p.Read {
		b[0] = 'r'
	}
	if p.Write {
		b[1] = 'w'
	}
	if p.Execute {
		b[2] = 'x'
	}
	return string(b[:])
}

// ─── FileMode — Complete Mode Representation ──────────────────

// FileMode decodes all components of a raw mode_t.
type FileMode struct {
	RawMode uint32
	Type    FileType
	Special SpecialBits
	Owner   PermSet
	Group   PermSet
	Other   PermSet
}

// DecodeMode decodes a raw uint32 mode into all its components.
func DecodeMode(mode uint32) FileMode {
	return FileMode{
		RawMode: mode,
		Type:    DecodeFileType(mode),
		Special: DecodeSpecialBits(mode),
		Owner: PermSet{
			Read:    mode&OwnerRead != 0,
			Write:   mode&OwnerWrite != 0,
			Execute: mode&OwnerExecute != 0,
		},
		Group: PermSet{
			Read:    mode&GroupRead != 0,
			Write:   mode&GroupWrite != 0,
			Execute: mode&GroupExecute != 0,
		},
		Other: PermSet{
			Read:    mode&OtherRead != 0,
			Write:   mode&OtherWrite != 0,
			Execute: mode&OtherExecute != 0,
		},
	}
}

// LSString formats the mode as a 10-character ls -l string.
func (m FileMode) LSString() string {
	buf := make([]byte, 10)
	buf[0] = m.Type.TypeChar()

	// Owner bits (with SetUID overlay)
	buf[1] = charIf(m.Owner.Read, 'r', '-')
	buf[2] = charIf(m.Owner.Write, 'w', '-')
	switch {
	case m.Special.SetUID && m.Owner.Execute:
		buf[3] = 's'
	case m.Special.SetUID && !m.Owner.Execute:
		buf[3] = 'S'
	case m.Owner.Execute:
		buf[3] = 'x'
	default:
		buf[3] = '-'
	}

	// Group bits (with SetGID overlay)
	buf[4] = charIf(m.Group.Read, 'r', '-')
	buf[5] = charIf(m.Group.Write, 'w', '-')
	switch {
	case m.Special.SetGID && m.Group.Execute:
		buf[6] = 's'
	case m.Special.SetGID && !m.Group.Execute:
		buf[6] = 'S'
	case m.Group.Execute:
		buf[6] = 'x'
	default:
		buf[6] = '-'
	}

	// Other bits (with sticky overlay)
	buf[7] = charIf(m.Other.Read, 'r', '-')
	buf[8] = charIf(m.Other.Write, 'w', '-')
	switch {
	case m.Special.Sticky && m.Other.Execute:
		buf[9] = 't'
	case m.Special.Sticky && !m.Other.Execute:
		buf[9] = 'T'
	case m.Other.Execute:
		buf[9] = 'x'
	default:
		buf[9] = '-'
	}

	return string(buf)
}

// OctalString formats the lower 13 bits of mode as "0755", "4755", etc.
func (m FileMode) OctalString() string {
	return fmt.Sprintf("%04o", m.RawMode&0o7777)
}

func (m FileMode) String() string {
	return fmt.Sprintf("%s (%s)", m.LSString(), m.OctalString())
}

func charIf(cond bool, t, f byte) byte {
	if cond {
		return t
	}
	return f
}

// ─── FileStat — Decoded stat structure ────────────────────────

// FileStat holds decoded metadata for a filesystem object.
type FileStat struct {
	Path  string
	Mode  FileMode
	UID   uint32
	GID   uint32
	Size  int64
	Nlink uint64
	Inode uint64
	Dev   uint64
}

// StatFile performs lstat() on the given path and returns a FileStat.
// Uses syscall.Lstat so we inspect symlinks, not their targets.
func StatFile(path string) (*FileStat, error) {
	var raw syscall.Stat_t
	if err := syscall.Lstat(path, &raw); err != nil {
		return nil, fmt.Errorf("lstat(%q): %w", path, err)
	}

	return &FileStat{
		Path:  path,
		Mode:  DecodeMode(raw.Mode),
		UID:   raw.Uid,
		GID:   raw.Gid,
		Size:  raw.Size,
		Nlink: raw.Nlink,
		Inode: raw.Ino,
		Dev:   raw.Dev,
	}, nil
}

// DisplayReport prints a formatted permission report.
func (s *FileStat) DisplayReport() {
	fmt.Println("┌─────────────────────────────────────────────┐")
	fmt.Printf("│ Path  : %-37s│\n", truncate(s.Path, 37))
	fmt.Printf("│ Type  : %-37s│\n", s.Mode.Type.String())
	fmt.Printf("│ Mode  : %-37s│\n", s.Mode.String())
	fmt.Printf("│ Owner : uid=%-5d  gid=%-5d                  │\n", s.UID, s.GID)
	fmt.Printf("│ Inode : %-37d│\n", s.Inode)
	fmt.Printf("│ Size  : %-30s bytes  │\n", fmt.Sprintf("%d", s.Size))
	fmt.Printf("│ Links : %-37d│\n", s.Nlink)
	if s.Mode.Special.SetUID {
		fmt.Println("│ *** SetUID is SET ***                       │")
	}
	if s.Mode.Special.SetGID {
		fmt.Println("│ *** SetGID is SET ***                       │")
	}
	if s.Mode.Special.Sticky {
		fmt.Println("│ *** Sticky bit is SET ***                   │")
	}
	fmt.Println("└─────────────────────────────────────────────┘")
}

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return "..." + s[len(s)-(max-3):]
}

// ─── ProcessIdentity ──────────────────────────────────────────

// ProcessIdentity captures the current process's credential state.
type ProcessIdentity struct {
	EUID          int
	EGID          int
	Supplementary []int
}

// GetProcessIdentity returns the current process identity.
func GetProcessIdentity() ProcessIdentity {
	groups, _ := os.Getgroups()
	return ProcessIdentity{
		EUID:          os.Geteuid(),
		EGID:          os.Getegid(),
		Supplementary: groups,
	}
}

// ─── Permission Check ─────────────────────────────────────────

// AccessRequest specifies what access is being requested.
type AccessRequest struct {
	Read    bool
	Write   bool
	Execute bool
}

// CheckPermission simulates the kernel's DAC permission evaluation.
// Mirrors inode_permission() logic precisely.
func CheckPermission(id ProcessIdentity, stat *FileStat, req AccessRequest) error {
	mode := stat.Mode

	// Step 1: Root bypass
	if id.EUID == 0 {
		if req.Execute && stat.Mode.Type != Directory {
			// Root needs at least one execute bit
			anyExec := mode.Owner.Execute || mode.Group.Execute || mode.Other.Execute
			if !anyExec {
				return errors.New("EACCES: no execute bits set (even root cannot execute)")
			}
		}
		return nil
	}

	// Step 2: Select the applicable permission category
	var applicable PermSet
	switch {
	case uint32(id.EUID) == stat.UID:
		applicable = mode.Owner // Owner — ignores group/other even if less restrictive
	default:
		inGroup := uint32(id.EGID) == stat.GID
		if !inGroup {
			for _, sg := range id.Supplementary {
				if uint32(sg) == stat.GID {
					inGroup = true
					break
				}
			}
		}
		if inGroup {
			applicable = mode.Group
		} else {
			applicable = mode.Other
		}
	}

	// Step 3: Verify each requested bit
	if req.Read && !applicable.Read {
		return fmt.Errorf("EACCES: read denied (applicable bits: %s)", applicable)
	}
	if req.Write && !applicable.Write {
		return fmt.Errorf("EACCES: write denied (applicable bits: %s)", applicable)
	}
	if req.Execute && !applicable.Execute {
		return fmt.Errorf("EACCES: execute denied (applicable bits: %s)", applicable)
	}
	return nil
}

// ─── Umask Demonstration ──────────────────────────────────────

// DemonstrateUmask shows how umask affects file creation modes.
// In Go, we use syscall.Umask to read/set the mask.
func DemonstrateUmask() {
	// Read current umask by setting a known value and getting the old one back
	current := syscall.Umask(0)
	syscall.Umask(current) // Restore immediately

	fmt.Println("\n=== umask Demonstration ===")
	fmt.Printf("Current umask: %04o\n\n", current)

	type testCase struct {
		requested int
		desc      string
	}
	cases := []testCase{
		{0o666, "open() with 0666 (typical file)"},
		{0o777, "mkdir() with 0777 (typical dir)"},
		{0o644, "open() with 0644"},
		{0o600, "open() with 0600 (private)"},
	}

	fmt.Printf("  %-12s %-12s %s\n", "Requested", "After umask", "Description")
	fmt.Printf("  %s %s %s\n",
		strings.Repeat("-", 12), strings.Repeat("-", 12), strings.Repeat("-", 30))

	for _, c := range cases {
		result := c.requested & ^current
		fmt.Printf("  %04o         %04o         %s\n", c.requested, result, c.desc)
	}
}

// ─── Verbose Permission Analysis ──────────────────────────────

// AnalyzePermissions prints a human-readable breakdown of what each
// class can do with a file.
func AnalyzePermissions(mode FileMode) {
	fmt.Println("\n=== Permission Analysis ===")
	fmt.Printf("Mode: %s\n\n", mode)

	type categoryInfo struct {
		name string
		perm PermSet
	}
	categories := []categoryInfo{
		{"Owner ", mode.Owner},
		{"Group ", mode.Group},
		{"Others", mode.Other},
	}

	for _, cat := range categories {
		perms := []string{}
		if cat.perm.Read {
			perms = append(perms, "READ")
		}
		if cat.perm.Write {
			perms = append(perms, "WRITE")
		}
		if cat.perm.Execute {
			perms = append(perms, "EXECUTE")
		}
		if len(perms) == 0 {
			perms = []string{"(none)"}
		}
		fmt.Printf("  %s: %s\n", cat.name, strings.Join(perms, " | "))
	}

	fmt.Println("\n  Special bits:")
	fmt.Printf("    SetUID : %v\n", mode.Special.SetUID)
	fmt.Printf("    SetGID : %v\n", mode.Special.SetGID)
	fmt.Printf("    Sticky : %v\n", mode.Special.Sticky)
}

// ─── Main ─────────────────────────────────────────────────────

func main() {
	fmt.Println("╔════════════════════════════════════════════╗")
	fmt.Println("║   Go Linux Permissions Inspector          ║")
	fmt.Println("╚════════════════════════════════════════════╝")
	fmt.Println()

	// 1. Process identity
	id := GetProcessIdentity()
	fmt.Println("=== Process Identity ===")
	fmt.Printf("  EUID: %d\n", id.EUID)
	fmt.Printf("  EGID: %d\n", id.EGID)
	fmt.Printf("  Supplementary groups: %v\n", id.Supplementary)

	// 2. Inspect paths from arguments or defaults
	targets := os.Args[1:]
	if len(targets) == 0 {
		targets = []string{"/etc/passwd", "/etc/shadow", "/tmp", "/usr/bin/sudo"}
	}

	fmt.Println("\n=== File Inspection ===")
	for _, path := range targets {
		fmt.Println()
		stat, err := StatFile(path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "ERROR: %v\n", err)
			continue
		}

		stat.DisplayReport()
		AnalyzePermissions(stat.Mode)

		// Permission check for current process
		reqRead  := AccessRequest{Read: true}
		reqWrite := AccessRequest{Write: true}

		readErr  := CheckPermission(id, stat, reqRead)
		writeErr := CheckPermission(id, stat, reqWrite)

		fmt.Println("\n  Access check for current process:")
		if readErr == nil {
			fmt.Println("    Read  → ALLOWED")
		} else {
			fmt.Printf("    Read  → DENIED (%v)\n", readErr)
		}
		if writeErr == nil {
			fmt.Println("    Write → ALLOWED")
		} else {
			fmt.Printf("    Write → DENIED (%v)\n", writeErr)
		}
	}

	// 3. umask demonstration
	DemonstrateUmask()

	// 4. Interesting modes demonstration
	fmt.Println("\n=== Mode Table — Common Configurations ===")
	interestingModes := []struct {
		raw  uint32
		desc string
	}{
		{0o100755, "Standard executable"},
		{0o100644, "Standard data file"},
		{0o100600, "Private file (SSH key)"},
		{0o104755, "SetUID executable (passwd)"},
		{0o102755, "SetGID executable"},
		{0o041777, "Sticky shared dir (/tmp style)"},
		{0o042775, "SetGID collaborative dir"},
		{0o040700, "Private directory"},
		{0o120777, "Symbolic link"},
	}

	fmt.Printf("  %-8s  %-12s  %s\n", "Octal", "ls style", "Description")
	fmt.Printf("  %s  %s  %s\n",
		strings.Repeat("-", 8), strings.Repeat("-", 12), strings.Repeat("-", 30))
	for _, m := range interestingModes {
		fm := DecodeMode(m.raw)
		fmt.Printf("  %-8s  %-12s  %s\n", fm.OctalString(), fm.LSString(), m.desc)
	}
}
```

---

## 16. Real-World Patterns and Hardening

### Principle of Least Privilege — Applied

```bash
# Web server: should only read web content
chown root:www-data /var/www/html
chmod 750 /var/www/html
find /var/www/html -type f -exec chmod 640 {} \;
find /var/www/html -type d -exec chmod 750 {} \;

# Database data directory: only DB process should access
chown postgres:postgres /var/lib/postgresql/data
chmod 700 /var/lib/postgresql/data

# Application log directory: app writes, admin reads
chown app:syslog /var/log/myapp
chmod 2750 /var/log/myapp   # SetGID so new logs inherit syslog group

# SSH private key: no tolerance for loose permissions
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
chmod 700 ~/.ssh/
```

### Collaborative Directory Pattern

```bash
# Problem: Team members need shared read/write access
# Solution: SetGID directory

groupadd project-team
usermod -aG project-team alice
usermod -aG project-team bob

mkdir /shared/project
chown root:project-team /shared/project
chmod 2775 /shared/project    # SetGID + rwxrwxr-x

# Now files created by alice or bob belong to project-team group
# and other team members can read/write them.

# Set default ACL so even new files inherit group write:
setfacl -d -m g:project-team:rw /shared/project
```

### Drop Box Pattern (Write-Only Directory)

```bash
# Problem: Users should deposit files but not see others' files
mkdir /dropbox
chmod 1733 /dropbox    # sticky + -wx------wx
# This means:
# - Anyone can create files (wx for all)
# - Nobody can list contents (no r for group/others)
# - Sticky prevents deletion of others' files
```

### Secure Temporary File Creation

```bash
# Never use /tmp/myapp.pid — use mktemp for unique names
TMPFILE=$(mktemp /tmp/myapp.XXXXXX)
# mktemp creates with 0600 by default — only owner can read
```

In C:
```c
/* Safe temp file: unique name, 0600 permissions, auto-cleaned */
char template[] = "/tmp/myapp.XXXXXX";
int fd = mkstemp(template);  /* creates with mode 0600 */
if (fd < 0) { /* handle error */ }
unlink(template);  /* Remove name; fd still valid until close() */
/* ... use fd ... */
close(fd);  /* file deleted here */
```

---

## 17. Common Vulnerabilities and Pitfalls

### TOCTOU — Time-Of-Check-Time-Of-Use

```
VULNERABLE:
  if (access(path, W_OK) == 0) {    ← CHECK (real UID)
      /* attacker swaps path to symlink here */
      fd = open(path, O_WRONLY);    ← USE (different file!)
  }

SAFE:
  /* Let open() be both the check AND the use */
  fd = open(path, O_WRONLY | O_NOFOLLOW);
  if (fd < 0) { handle_error(); }
```

### World-Writable Files with Sensitive Content

```bash
# Find dangerous world-writable files
find / -type f -perm -o+w 2>/dev/null | grep -v /proc | grep -v /sys

# Find SetUID/SetGID binaries (audit these!)
find / -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null
```

### Symlink Attacks

```bash
# Attacker: ln -sf /etc/passwd /tmp/target
# Victim daemon (running as root): writes to /tmp/target
# → /etc/passwd is overwritten

# Defense: Always use O_NOFOLLOW
int fd = open(path, O_WRONLY | O_NOFOLLOW | O_CREAT | O_EXCL, 0600);

# Or use openat() with a directory fd to pin the base directory
int dirfd = open("/safe/dir", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
int fd    = openat(dirfd, "filename", O_WRONLY | O_CREAT | O_NOFOLLOW, 0600);
```

### Umask Surprises

```c
/* BUG: umask can silently remove permissions */
int fd = open("/path/to/shared_file", O_CREAT | O_WRONLY, 0666);
/* If umask is 0022, result is 0644 — group cannot write! */

/* FIX: Temporarily zero the umask when exact permissions needed */
mode_t old = umask(0);
int fd = open("/path/to/shared_file", O_CREAT | O_WRONLY, 0660);
umask(old);
```

### The Owner-Wins Trap

```bash
# Developer's mistake:
chmod 007 secret.txt   # "only others can read"
# But if YOU are the owner, owner bits (---) apply → YOU cannot read it!
# chmod 700 secret.txt  ← correct for owner-only access
```

### SetUID Shell Scripts — They Don't Work

Linux deliberately ignores the SetUID bit on interpreted scripts (shell, Python, Perl). This is a security decision — the interpreter would open the script as the unprivileged user before privilege escalation takes effect.

```bash
# This does NOT work as SetUID on Linux:
chmod 4755 myscript.sh

# Only native ELF binaries get SetUID semantics.
# For scripts needing privilege: use sudo with visudo, or a C wrapper.
```

### Capabilities Leakage Across Fork/Exec

```c
/* Files opened before dropping privileges remain accessible */
int secret_fd = open("/etc/shadow", O_RDONLY);  /* as root */
drop_privileges();  /* become regular user */
/* secret_fd is still valid and readable! */

/* Always use O_CLOEXEC on sensitive fds */
int secret_fd = open("/etc/shadow", O_RDONLY | O_CLOEXEC);
/* Now exec() will close this fd automatically */
```

---

## Quick Reference Card

```
Permission Bits:           Special Bits:
  r = 4 (read)               4000 = SetUID
  w = 2 (write)              2000 = SetGID
  x = 1 (execute)            1000 = Sticky

Common Modes:              umask (022 default):
  0644 = rw-r--r--            file created with 0666 → 0644
  0755 = rwxr-xr-x            dir  created with 0777 → 0755
  0600 = rw-------
  0700 = rwx------          Kernel Check Order:
  4755 = rwsr-xr-x            1. root? → allow (with exec caveat)
  2775 = rwxrwsr-x            2. euid == file_uid? → owner bits
  1777 = rwxrwxrwt            3. egid/supp == file_gid? → group bits
                              4. otherwise → other bits
Key Syscalls:               (categories are MUTUALLY EXCLUSIVE)
  stat/lstat/fstat
  chmod/fchmod              Special Bit Effects:
  chown/fchown/lchown         SetUID on exec: euid = file_uid
  umask                       SetGID on exec: egid = file_gid
  open (real access check)    SetGID on dir:  new files inherit GID
  access (real uid — avoid)   Sticky on dir:  only owner can delete
```

---

*This guide covers the complete Linux DAC (Discretionary Access Control) permission model. For mandatory access control (MAC), study SELinux and AppArmor — they layer on top of what is described here.*

Now let me create the comprehensive guide:Here is your complete guide. Here's a summary of what's covered across 17 sections:

**Conceptual Foundation**
The guide starts at the hardware/kernel level — how inodes own permissions, how the 16-bit `mode_t` is laid out bit by bit, and why filenames and permissions are separate concerns.

**Identity Model (the most misunderstood part)**
All three UID/GID pairs (`ruid/euid/suid`) are explained. The guide emphasizes that `euid` is what the kernel actually checks, and that the permission categories (owner/group/other) are **mutually exclusive** — the single most common source of confusion in Linux permissions.

**The Permission Evaluation Algorithm**
An exact flowchart of the kernel's `inode_permission()` logic — including the root bypass, the owner-wins rule, and why having `rw-` in "other" doesn't help you if you own the file with `---`.

**Special Bits (SetUID/SetGID/Sticky)**
Each is explained with its actual kernel semantics, the difference between file and directory behavior, and real system examples like `/usr/bin/passwd` and `/tmp`.

**Advanced Topics**
ACLs (including the mask mechanism), Linux Capabilities (the post-root privilege model), and the complete system call reference are all included.

**Three Production-Grade Implementations**
- **C**: Full toolkit with `mode_to_string`, `simulate_access` (exact kernel algorithm replica), `safe_chmod`/`safe_chown` using fd-based operations to defeat TOCTOU, and `create_file_with_exact_mode` with `umask(0)` bracketing
- **Rust**: Type-safe `FileMode`, `PermissionBits`, `SpecialBits` newtypes; `ProcessIdentity::current()` using raw libc; `check_permission()` mirroring kernel logic
- **Go**: Complete inspector with `DecodeMode`, `CheckPermission`, and `DemonstrateUmask` — all with named constants and no magic numbers

**Security Section**
TOCTOU attacks, symlink attacks, umask surprises, the SetUID-scripts-don't-work rule, and the owner-wins trap are all covered with both vulnerable and safe code patterns.