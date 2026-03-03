## Include Guards — The Full Story

### The Problem: Multiple Inclusion

The C preprocessor is **textual substitution**. When you `#include` a file, the preprocessor literally pastes its contents inline. No deduplication, no tracking.

```
main.c
├── #include "a.h"   → pastes a.h content
└── #include "b.h"
         └── #include "a.h"  → pastes a.h content AGAIN
```

Without guards, `a.h` gets included **twice** → duplicate `struct`, `typedef`, `enum` definitions → **compiler error**.

---

### The Include Guard Pattern (1970s CPP Convention)

```c
#ifndef _BPF_PRELOAD_H    // 1. If NOT defined...
#define _BPF_PRELOAD_H    // 2. Define it (empty macro, just a flag)

/* actual header content */

#endif                    // 3. End of guarded block
```

**Flow on second inclusion:**

```
First inclusion:
  _BPF_PRELOAD_H not defined → enter block → define it → process content

Second inclusion:
  _BPF_PRELOAD_H IS defined → #ifndef is FALSE → skip entire block
```

You **cannot** drop the `#ifndef` and just write `#define` because:
- `#define` unconditionally defines — it has no skip mechanism
- The **skip** is the entire point — `#ifndef` causes the preprocessor to jump to matching `#endif`

---

### ASCII: Preprocessor State Machine

```
                  ┌─────────────────────────────────┐
   #include       │   CPP processes _BPF_PRELOAD_H  │
  "bpf_preload.h" │                                 │
       │          │  ┌──────────────────────────┐   │
       ▼          │  │ #ifndef _BPF_PRELOAD_H   │   │
  ┌────────┐      │  └────────────┬─────────────┘   │
  │  CPP   │      │               │                  │
  │ symbol │      │    defined?   │                  │
  │ table  │      │       ├── NO ─┼──► process body  │
  │        │      │       │       │    define macro   │
  │[macro] │◄─────┤       └── YES─┼──► skip to #endif│
  │ flags  │      │               │                  │
  └────────┘      │          #endif                  │
                  └─────────────────────────────────┘
```

---

### History

| Era | Mechanism | Notes |
|-----|-----------|-------|
| **Pre-C89** | Manual discipline | Developers avoided double-includes manually |
| **C89 (1989)** | `#ifndef` guards standardized | Became universal idiom |
| **1990s** | `#pragma once` appeared | MSVC extension, non-standard |
| **GCC 3.4+ (2004)** | Recognized guard pattern | Compiler **optimization**: if guard macro defined, skip file open entirely (`once_map` in libcpp) |
| **C++20** | Modules (`import`) | Designed to replace header model entirely |

---

### GCC's "Optimization" — Critical Detail

GCC's preprocessor (`libcpp/files.cc`) detects the canonical guard pattern:

```
file starts with: #ifndef MACRO
                  #define MACRO
file ends with:   #endif
```

If detected → file is added to an internal `once_map`. On subsequent `#include`, **the file isn't even opened** (no syscall). This is why guards are more than convention — they're a **performance mechanism**.

Source: `libcpp/files.cc` → `search_cache()` + `_cpp_mark_file_once_only()`

---

### `#pragma once` — Why Kernel Rejects It

```c
#pragma once   // Non-standard, compiler extension
```

**Kernel policy (`Documentation/process/coding-style.rst`):** explicitly rejects `#pragma once` because:

1. **Not in C standard** — sparse, LLVM, obscure cross-compilers may not support it
2. **Identity by path** — `#pragma once` deduplicates by **inode/filename**, not macro. Symlinks or copied headers with same content but different paths break it
3. **Portability** — kernel targets dozens of architectures with varying toolchains (arm-none-eabi, riscv64-linux-gnu, etc.)

---

### Kernel Naming Convention for Guard Macros

```
_<PATH_WITH_UNDERSCORES>_H

include/linux/sched.h        → #ifndef __LINUX_SCHED_H
include/uapi/linux/bpf.h     → #ifndef __LINUX_BPF_H
kernel/bpf/preload/bpf_preload.h → #ifndef _BPF_PRELOAD_H
```

Leading underscores + `_H` suffix = namespace reserved for implementation (C standard allows `_[A-Z]` and `__` prefixes for implementation). Avoids collision with user-defined macros.

---

### What You Actually Cannot Do

```c
// WRONG - no guard, just a define
#define _BPF_PRELOAD_H
struct bpf_preload_ops { ... };  // included twice → error
```

```c
// WRONG - define without ifndef
#define _BPF_PRELOAD_H
#ifndef _BPF_PRELOAD_H           // always false now, content never processed!
struct bpf_preload_ops { ... };
#endif
```

The `#ifndef` → `#define` ordering is load-bearing: define **inside** the guard so first pass sets the flag, second pass sees it.

---

### Relevant Kernel Files

- `include/linux/bpf.h` — canonical example of guard + UAPI split
- `tools/include/uapi/linux/bpf.h` — mirrored UAPI header
- `Documentation/process/coding-style.rst` — policy rejection of `#pragma once`
- GCC source: `libcpp/files.cc:once_map` — guard optimization impl

The TL;DR: `#ifndef` is the **conditional branch** that makes the pattern work. `#define` is just the flag. You need both, in that order, because the preprocessor has no other native "include this file only once" mechanism in standard C.