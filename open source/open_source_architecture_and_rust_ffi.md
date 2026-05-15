# Open Source Project Architecture, C Internals & Rust FFI
## A Complete Mental Model Guide for Systems Engineers

---

> **How to read this document**
> Every section follows: Mental Model → File Layout → Real ASCII Architecture →
> C Internals → Rust Integration → Failure Modes → Real Codebase References.
> Do not skip sections. Each one builds on the last.

---

## Table of Contents

1. [The Philosophy of Open Source Project Structure](#1-the-philosophy)
2. [How Projects Are Decomposed — The Universals](#2-project-decomposition)
3. [C Project Architecture — Deep Internals](#3-c-project-architecture)
4. [Rust Project Architecture — Idiomatic Layout](#4-rust-project-architecture)
5. [Naming Conventions — The Standard Across Languages](#5-naming-conventions)
6. [Layered Architecture Patterns](#6-layered-architecture-patterns)
7. [Build Systems — Make, CMake, Cargo, and How They Wire Together](#7-build-systems)
8. [C Implementation Internals — How C Actually Works](#8-c-implementation-internals)
9. [Rust FFI — Calling C from Rust](#9-rust-ffi)
10. [Bindgen — Automating C Binding Generation](#10-bindgen)
11. [The `-sys` Crate Pattern — The Rust Ecosystem Standard](#11-sys-crate-pattern)
12. [Unsafe Contracts in FFI — What You Must Guarantee](#12-unsafe-contracts-in-ffi)
13. [Real Project Walkthroughs](#13-real-project-walkthroughs)
    - 13.1 [Linux Kernel — The C Archetype](#131-linux-kernel)
    - 13.2 [tokio — Rust Async Runtime](#132-tokio)
    - 13.3 [rustls — Pure Rust TLS](#133-rustls)
    - 13.4 [aya — eBPF in Rust with Kernel C FFI](#134-aya)
    - 13.5 [OpenSSL / ring — Crypto Library FFI Pattern](#135-openssl--ring)
    - 13.6 [libbpf-sys — The sys Crate Pattern in Practice](#136-libbpf-sys)
14. [Variable Naming Deep Dive — What Names Signal](#14-variable-naming-deep-dive)
15. [Function Decomposition — How Real Projects Break Down Work](#15-function-decomposition)
16. [Error Handling Architecture — C vs Rust Patterns](#16-error-handling-architecture)
17. [Memory Management Architecture — C vs Rust](#17-memory-management-architecture)
18. [Concurrency Architecture — C Pthreads vs Rust Ownership](#18-concurrency-architecture)
19. [Testing Architecture — How Real Projects Structure Tests](#19-testing-architecture)
20. [Documentation Architecture — Comments That Build Mental Models](#20-documentation-architecture)
21. [Connection Map — How Everything Ties Together](#21-connection-map)

---

## 1. The Philosophy

### Why Open Source Projects Have Structure at All

A project's structure is not aesthetic preference. It is a contract between
contributors. The layout of files, the naming of functions, and the
decomposition of modules encode a set of answers to invariant questions:

```
1. What is the boundary between public API and private implementation?
2. Who owns which memory?
3. What is allowed to depend on what?
4. How are errors propagated across abstraction layers?
5. What can change without breaking callers?
```

When you read a project's file tree, you are reading answers to these questions
encoded as directory names and file boundaries. A good project makes these
answers obvious. A bad project hides them.

### The Dependency Inversion Principle at File Scale

Every serious open source project enforces a layered dependency graph.
Lower layers know nothing about higher layers. This is not a suggestion —
it is enforced by build system rules, visibility modifiers, and in Rust,
by the module system and `pub`/`pub(crate)`/private boundaries.

```
              ┌──────────────────────────────────┐
              │         Application Layer         │  ← knows about everything below
              │   (binary, CLI, daemon, main.rs)  │
              └──────────────┬───────────────────┘
                             │ depends on
              ┌──────────────▼───────────────────┐
              │         Interface Layer           │  ← defines the public API contract
              │   (lib.rs, include/*.h, traits)   │
              └──────────────┬───────────────────┘
                             │ depends on
              ┌──────────────▼───────────────────┐
              │       Implementation Layer        │  ← all the real work
              │   (src/*, internal/, private)     │
              └──────────────┬───────────────────┘
                             │ depends on
              ┌──────────────▼───────────────────┐
              │         Platform Layer            │  ← syscalls, OS, hardware
              │  (sys crates, libc, kernel ABI)   │
              └──────────────────────────────────┘
```

**Key rule**: arrows point downward only. A `src/crypto/aes.c` does not
`#include` anything from `src/tls/handshake.h`. The handshake layer depends
on crypto. Never the reverse.

This is enforced differently in each language:
- **C**: include guards, opaque pointers, compilation unit boundaries
- **Rust**: `mod` visibility, `pub(crate)`, `pub(super)`, workspace members
- **Go**: package import restrictions, internal packages

---

## 2. Project Decomposition

### The Universal Layout Pattern

Every serious systems project — whether C, Rust, Go, or mixed — converges on
the same logical decomposition. The names differ; the structure does not.

```
project-root/
│
├── [BUILD SYSTEM FILES]         ← how to compile everything
│   ├── Cargo.toml / Makefile / CMakeLists.txt
│   └── build.rs                 ← (Rust only) build-time code generation
│
├── [PUBLIC API SURFACE]         ← what callers see
│   ├── include/                 ← (C) public headers, your ABI contract
│   ├── src/lib.rs               ← (Rust) the crate root, re-exports only
│   └── proto/                   ← (protobuf) wire-format contracts
│
├── [IMPLEMENTATION]             ← the actual work
│   └── src/                     ← C: .c files; Rust: submodules
│       ├── internal/            ← private implementation details
│       └── platform/            ← OS-specific code
│
├── [TESTS]                      ← verification
│   ├── tests/                   ← integration tests (Rust: tests/)
│   ├── test/                    ← (C) test harness
│   └── benches/                 ← benchmarks
│
├── [EXAMPLES]                   ← usage demonstrations
│   └── examples/
│
├── [TOOLING]
│   ├── tools/                   ← dev tools, codegen scripts
│   ├── scripts/                 ← CI/CD helpers
│   └── .github/workflows/       ← CI pipelines
│
└── [DOCUMENTATION]
    ├── docs/                    ← architecture docs, RFCs, decisions
    └── README.md                ← entry point
```

### What Each Boundary Means

| Boundary | What It Enforces | Who Crosses It |
|---|---|---|
| `include/` vs `src/` | Public ABI vs private impl | External callers |
| `lib.rs` re-exports | What the crate publishes | Downstream crates |
| `pub(crate)` | Crate-internal sharing | Same crate, different modules |
| `pub(super)` | Sibling module sharing | Parent module only |
| `mod.rs` / `internal/` | Logical grouping | Same subsystem |
| `tests/` | Integration boundary | Tests only |

---

## 3. C Project Architecture — Deep Internals

### The Canonical C Library Layout

C projects follow a standard that has evolved since the 1970s. Every major
C library — OpenSSL, libbpf, glibc, libcurl — follows this pattern with
minor variations.

```
libfoo/
│
├── include/
│   └── foo/
│       ├── foo.h                ← primary public header (API contract)
│       ├── foo_types.h          ← public type definitions, structs
│       └── foo_compat.h         ← platform compatibility shims
│
├── src/
│   ├── foo.c                    ← primary implementation, public functions
│   ├── foo_internal.h           ← PRIVATE header, never installed
│   ├── crypto/
│   │   ├── aes.c
│   │   ├── aes.h                ← private header, subsystem-internal
│   │   ├── sha256.c
│   │   └── sha256.h
│   ├── net/
│   │   ├── socket.c
│   │   └── socket.h
│   └── platform/
│       ├── linux/
│       │   └── epoll.c
│       └── bsd/
│           └── kqueue.c
│
├── test/
│   ├── test_foo.c
│   ├── test_crypto.c
│   └── Makefile
│
├── tools/
│   └── foo_gen.py               ← code generation script
│
├── Makefile
├── CMakeLists.txt
└── README.md
```

### The Critical C Header Discipline

In C, the header file IS the public API. Misunderstanding this is the source
of most C library design mistakes.

```
┌────────────────────────────────────────────────────────────┐
│                    PUBLIC HEADER (foo.h)                    │
│  Installed to /usr/include/foo/foo.h during `make install`  │
│                                                            │
│  Contains:                                                 │
│  ✓ struct declarations (opaque or full, your choice)       │
│  ✓ function prototypes (declarations, not definitions)     │
│  ✓ enum definitions                                        │
│  ✓ #define constants                                       │
│  ✓ typedef aliases                                         │
│                                                            │
│  NEVER contains:                                           │
│  ✗ function bodies (unless inline/static inline)          │
│  ✗ global variable definitions (declarations only)        │
│  ✗ #include of private headers                            │
│  ✗ implementation details that might change               │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                  PRIVATE HEADER (foo_internal.h)            │
│  Never installed. Only #included by .c files in src/       │
│                                                            │
│  Contains:                                                 │
│  ✓ full struct member layout (what the opaque type holds)  │
│  ✓ internal function prototypes                            │
│  ✓ private #define macros                                  │
│  ✓ internal state machine enums                            │
│  ✓ debugging/logging macros                               │
└────────────────────────────────────────────────────────────┘
```

### Opaque Pointer Pattern — The Most Important C Architecture Technique

This is the C equivalent of Rust's private fields. It enforces that callers
cannot access struct internals, making the struct layout part of the private
implementation, not the ABI.

```c
/* === include/foo/foo.h (PUBLIC) === */

/* Forward declaration only. Callers get a pointer but never the layout. */
typedef struct foo_ctx foo_ctx_t;

/* Callers can only use pointers. They cannot allocate foo_ctx on the stack. */
foo_ctx_t *foo_ctx_new(const char *config_path);
int        foo_ctx_connect(foo_ctx_t *ctx, const char *host, uint16_t port);
void       foo_ctx_free(foo_ctx_t *ctx);

/* === src/foo_internal.h (PRIVATE) === */

/* The actual struct, visible only to .c files that #include this */
struct foo_ctx {
    int           fd;              /* socket file descriptor       */
    uint32_t      state;           /* connection state machine      */
    uint8_t       key[32];         /* session key material         */
    size_t        buf_len;         /* bytes in read buffer         */
    uint8_t      *buf;             /* read buffer pointer          */
    struct {
        uint64_t  bytes_rx;
        uint64_t  bytes_tx;
    } stats;
};
```

**Why this matters for Rust FFI**: When you call a C library from Rust that
uses opaque pointers, you must represent that opaque type in Rust as an
uninhabited enum or a `c_void` pointer. You cannot dereference it. You
cannot know its size. This is enforced by Rust's type system.

### C File Organization — The Internal Structure of a .c File

Every well-structured C file follows a canonical ordering that mirrors
the logical flow from dependencies to implementation:

```c
/* 1. FILE-LEVEL COMMENT — what this file is, who owns it, license */
/*
 * sha256.c — SHA-256 hash implementation
 * Implements FIPS 180-4, Section 6.2
 * SPDX-License-Identifier: Apache-2.0
 */

/* 2. SYSTEM INCLUDES — angle bracket, alphabetically ordered */
#include <stdint.h>
#include <string.h>

/* 3. PROJECT-INTERNAL INCLUDES — quote style, private headers */
#include "foo_internal.h"
#include "crypto/sha256.h"

/* 4. COMPILE-TIME CONSTANTS — #define, local to this file */
#define SHA256_BLOCK_SIZE  64
#define SHA256_DIGEST_SIZE 32

/* 5. STATIC CONSTANTS — read-only data, not exported */
static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, /* ... */
};

/* 6. FORWARD DECLARATIONS of static (file-local) functions */
static void sha256_transform(uint32_t state[8], const uint8_t block[64]);
static void sha256_pad(sha256_ctx_t *ctx);

/* 7. PUBLIC FUNCTION DEFINITIONS — match the order in the .h */
void sha256_init(sha256_ctx_t *ctx) { /* ... */ }
void sha256_update(sha256_ctx_t *ctx, const uint8_t *data, size_t len) { /* ... */ }
void sha256_final(sha256_ctx_t *ctx, uint8_t digest[32]) { /* ... */ }

/* 8. STATIC (PRIVATE) FUNCTION DEFINITIONS — helper functions */
static void sha256_transform(uint32_t state[8], const uint8_t block[64]) {
    /* ... */
}
```

**The `static` keyword here is critical**: `static` on a C function makes
it invisible outside the translation unit (the .c file). This is C's only
mechanism for function-level encapsulation. A function without `static` is
globally visible by default. This is why well-designed C libraries have
many `static` functions — they are implementation details, not public API.

---

## 4. Rust Project Architecture — Idiomatic Layout

### Single Crate Library Layout

```
my-lib/
├── Cargo.toml
├── build.rs                     ← build script (codegen, C compilation, bindgen)
├── src/
│   ├── lib.rs                   ← CRATE ROOT: pub use re-exports only
│   ├── error.rs                 ← unified error type (thiserror)
│   ├── config.rs                ← configuration types
│   │
│   ├── net/
│   │   ├── mod.rs               ← re-exports from net submodules
│   │   ├── socket.rs            ← socket abstraction
│   │   ├── listener.rs          ← accept loop
│   │   └── framing.rs           ← wire framing (nom/bytes)
│   │
│   ├── crypto/
│   │   ├── mod.rs
│   │   ├── aead.rs              ← AEAD cipher wrapper
│   │   ├── kdf.rs               ← key derivation
│   │   └── zeroize.rs           ← key material lifecycle
│   │
│   └── platform/
│       ├── mod.rs
│       ├── linux.rs             ← #[cfg(target_os = "linux")]
│       └── macos.rs             ← #[cfg(target_os = "macos")]
│
├── tests/
│   ├── integration_test.rs      ← integration tests (separate crate, sees only pub API)
│   └── fixtures/                ← test data files
│
├── benches/
│   └── throughput.rs            ← criterion benchmarks
│
└── examples/
    └── basic_client.rs          ← runnable example
```

### Workspace Layout — Multi-Crate Projects

This is how large projects (tokio, rustls, aya, axum) structure themselves:

```
project-workspace/
├── Cargo.toml                   ← workspace root: [workspace] members = [...]
│
├── crates/
│   ├── project-core/            ← pure logic, no I/O, no std sometimes
│   │   ├── Cargo.toml
│   │   └── src/lib.rs
│   │
│   ├── project-sys/             ← raw FFI bindings to C library (unsafe)
│   │   ├── Cargo.toml           ← links = "foo" (tells cargo about native lib)
│   │   ├── build.rs             ← runs bindgen or pkg-config
│   │   └── src/lib.rs           ← extern "C" blocks, raw types
│   │
│   ├── project/                 ← safe wrapper over project-sys
│   │   ├── Cargo.toml           ← depends on project-sys, project-core
│   │   └── src/lib.rs
│   │
│   └── project-tokio/           ← async integration layer
│       ├── Cargo.toml
│       └── src/lib.rs
│
├── examples/
├── tests/
└── tools/
```

**The workspace dependency graph (critical)**:

```
project-tokio ──depends on──► project ──depends on──► project-sys (unsafe, raw)
                                        │                    │
                                        └──depends on──► project-core (pure)
                                                             │
                                                        [no dependencies
                                                         outside std/core]
```

**Why this layering**: `project-sys` is the only crate that touches `unsafe`.
`project` wraps it in safe Rust. `project-core` has no I/O, so it can be used
in `no_std` environments (eBPF, embedded). `project-tokio` adds async.
Each crate has a single, testable responsibility.

### The lib.rs Contract

The crate root `src/lib.rs` should contain almost no logic. Its job is to:
1. Re-export the public API
2. Set crate-level attributes
3. Document the crate with `//!` doc comments

```rust
// src/lib.rs — the public surface of the crate
//
// Rules enforced here:
// - Only `pub use` statements
// - Only `pub mod` for modules whose entire content is public
// - No logic whatsoever
// - No `use` without `pub` (would be a private import with no effect)

#![deny(unsafe_code)]                          // safety policy
#![warn(missing_docs)]                         // documentation policy
#![cfg_attr(not(feature = "std"), no_std)]    // conditional std

//! # my-lib
//!
//! A secure channel library for Kubernetes pod-to-pod communication.
//!
//! ## Quick Start
//! ```rust
//! use my_lib::Channel;
//! ```

pub mod error;                  // error types are always public
pub use error::{Error, Result}; // re-export at crate root for ergonomics

pub mod net;                    // entire net module is public
pub use net::Channel;           // but also re-export the primary type

mod crypto;                     // private module — callers cannot import it
pub(crate) use crypto::Session; // accessible within crate, not outside
```

---

## 5. Naming Conventions — The Standard Across Languages

### C Naming — The Namespace Prefix Rule

C has no namespaces. The entire solution is: **prefix everything with
the library name**. This is not optional. It is mandatory.

```c
/* LIBRARY NAME: libfoo */

/* Types: foo_<name>_t */
typedef struct foo_ctx     foo_ctx_t;
typedef struct foo_config  foo_config_t;
typedef uint32_t           foo_handle_t;

/* Functions: foo_<noun>_<verb> */
foo_ctx_t *foo_ctx_new(void);
void       foo_ctx_free(foo_ctx_t *ctx);
int        foo_ctx_connect(foo_ctx_t *ctx, const char *host);
int        foo_ctx_send(foo_ctx_t *ctx, const uint8_t *data, size_t len);

/* Enums: FOO_<NOUN>_<VALUE> — all caps */
typedef enum {
    FOO_STATE_INIT        = 0,
    FOO_STATE_CONNECTING  = 1,
    FOO_STATE_CONNECTED   = 2,
    FOO_STATE_ERROR       = -1,
} foo_state_t;

/* Constants: FOO_<NAME> — all caps */
#define FOO_MAX_CONNECTIONS  1024
#define FOO_DEFAULT_TIMEOUT  30

/* Internal (static) functions: no prefix, descriptive */
static int  parse_header(const uint8_t *buf, size_t len);
static void reset_state(foo_ctx_t *ctx);

/* Error codes: FOO_OK, FOO_ERR_<REASON> */
#define FOO_OK              0
#define FOO_ERR_NOMEM      -1
#define FOO_ERR_TIMEOUT    -2
#define FOO_ERR_INVALID    -3
```

### What the Prefix Tells You in Real Code

When reading OpenSSL code, you encounter: `SSL_CTX_new()`, `SSL_connect()`,
`BIO_new()`, `EVP_CIPHER_CTX_new()`. The prefix tells you which subsystem
owns the function. `SSL_*` = TLS state machine. `BIO_*` = buffered I/O
abstraction. `EVP_*` = envelope (high-level crypto). The prefix is the
subsystem documentation encoded in the function name.

### Rust Naming — Enforced by the Language

Rust's compiler enforces naming conventions via warnings. `rustc` warns on
violations. These are not preferences; they are part of the language contract.

```rust
// TYPES: UpperCamelCase (structs, enums, traits, type aliases)
struct TlsSession { }
enum ConnectionState { Connecting, Connected, Closed }
trait PacketParser { }
type Result<T> = std::result::Result<T, Error>;

// FUNCTIONS AND METHODS: snake_case
fn parse_packet(buf: &[u8]) -> Result<Packet> { }
impl TlsSession {
    fn new(config: Config) -> Self { }
    fn send_data(&mut self, data: &[u8]) -> Result<usize> { }
}

// VARIABLES AND PARAMETERS: snake_case
let session_key: [u8; 32] = derive_key(&ikm);
let bytes_written: usize = 0;

// CONSTANTS: SCREAMING_SNAKE_CASE
const MAX_PACKET_SIZE: usize = 65535;
const DEFAULT_TIMEOUT_MS: u64 = 30_000;

// STATIC: SCREAMING_SNAKE_CASE
static GLOBAL_REGISTRY: Lazy<Registry> = Lazy::new(Registry::new);

// LIFETIMES: short, lowercase, single character or short word
fn parse<'buf>(data: &'buf [u8]) -> Packet<'buf> { }
fn handshake<'session, 'key>(
    session: &'session mut Session,
    key: &'key [u8; 32],
) -> Result<()> { }

// MODULES: snake_case (match directory/file name exactly)
mod crypto;        // file: src/crypto.rs or src/crypto/mod.rs
mod packet_codec;  // file: src/packet_codec.rs

// CRATES: kebab-case (Cargo.toml name)
// [dependencies]
// my-crypto-lib = "1.0"
// USAGE in code: my_crypto_lib (hyphens become underscores)
```

### What Function Names Signal About Ownership and Allocation

In Rust and C, naming conventions encode memory contracts:

```rust
// CONSTRUCTOR PATTERNS:
// fn new(...)            → allocates, returns owned value
// fn with_config(...)    → builder pattern step
// fn from_bytes(...)     → conversion from borrowed data
// fn try_from(...)       → fallible conversion

// REFERENCE-RETURNING PATTERNS:
// fn as_bytes(&self)     → borrows self, returns borrowed slice
// fn as_str(&self)       → borrows self, returns &str (lifetime tied to self)
// fn as_mut_ptr(&mut self) → borrows mutably, returns raw pointer (unsafe territory)

// CONSUMING PATTERNS:
// fn into_bytes(self)    → consumes self, returns owned Vec<u8>
// fn into_inner(self)    → unwraps a wrapper type, consuming it

// CLONING PATTERNS:
// fn clone(&self)        → deep copy, always allocates
// fn clone_from(&mut self, source: &Self) → reuse allocation

// ERROR HANDLING PATTERNS:
// fn try_parse(...)      → returns Result<T, E>
// fn parse(...)          → panics on invalid input (document this!)
```

---

## 6. Layered Architecture Patterns

### Pattern 1: The Layered Stack (Most Common in Systems Code)

Used by: Linux kernel, OpenSSL, tokio, rustls, gRPC stacks.

Each layer has:
- A clearly defined interface (the contract)
- No knowledge of the layers above it
- Explicit knowledge of the layer directly below

```
                     TCP/TLS Networking Stack Example
                     ─────────────────────────────────

┌─────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                      │
│  fn handle_request(req: HttpRequest) -> HttpResponse     │
│  - knows: HTTP semantics                                 │
│  - doesn't know: TLS, TCP, sockets                      │
└───────────────────────────┬─────────────────────────────┘
                            │ uses trait: AsyncRead + AsyncWrite
┌───────────────────────────▼─────────────────────────────┐
│                     TLS LAYER (rustls)                   │
│  struct TlsStream<IO: AsyncRead + AsyncWrite>            │
│  - knows: TLS handshake, record layer, crypto            │
│  - doesn't know: TCP, sockets, addresses                │
└───────────────────────────┬─────────────────────────────┘
                            │ uses trait: AsyncRead + AsyncWrite
┌───────────────────────────▼─────────────────────────────┐
│                     TCP LAYER (tokio)                    │
│  struct TcpStream                                        │
│  - knows: stream framing, TCP state machine              │
│  - doesn't know: TLS, HTTP, application logic           │
└───────────────────────────┬─────────────────────────────┘
                            │ syscalls: read(2), write(2), connect(2)
┌───────────────────────────▼─────────────────────────────┐
│                   KERNEL / OS LAYER                      │
│  epoll, io_uring, kqueue                                 │
│  - knows: file descriptors, network buffers              │
│  - doesn't know: protocols, applications                │
└─────────────────────────────────────────────────────────┘
```

### Pattern 2: The Hub-and-Spoke (Control Plane Pattern)

Used by: Kubernetes controller-manager, Cilium control plane, etcd.

```
                    Kubernetes Controller Architecture
                    ──────────────────────────────────

                         ┌─────────────┐
                         │   API Server │  ← single source of truth
                         └──────┬──────┘
                                │ watches (ListWatch)
              ┌─────────────────┼─────────────────┐
              │                 │                 │
     ┌────────▼──────┐ ┌────────▼──────┐ ┌───────▼───────┐
     │  Pod Controller│ │ Svc Controller│ │  CNI Plugin   │
     │  (reconcile)  │ │  (reconcile)  │ │  (reconcile)  │
     └────────┬──────┘ └────────┬──────┘ └───────┬───────┘
              │                 │                 │
     ┌────────▼──────┐ ┌────────▼──────┐ ┌───────▼───────┐
     │  kubelet       │ │  iptables/    │ │  eBPF maps    │
     │  (node agent) │ │  ipvs/ebpf   │ │  (data plane) │
     └───────────────┘ └───────────────┘ └───────────────┘
```

### Pattern 3: The Pipeline (Stream Processing)

Used by: tokio tower middleware, packet processing in XDP, log pipelines.

```
                        Tower Middleware Pipeline
                        ────────────────────────

  Request
    │
    ▼
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
│   Rate    │────►│   Auth    │────►│  Tracing  │────►│  Handler  │
│  Limiter  │     │  Check    │     │  Span     │     │ (business │
│  Layer    │     │  Layer    │     │  Layer    │     │  logic)   │
└───────────┘     └───────────┘     └───────────┘     └───────────┘
    │                 │                 │
    ▼                 ▼                 ▼
  429 Too         401 Unauthorized   Emit span
  Many Requests                      to OTLP

  Response flows back through layers in reverse order.
  Each layer wraps the next: Service<Request> trait.
```

### Pattern 4: The Actor / Channel Pattern

Used by: tokio actor model, Erlang-style systems, aya's event loops.

```
                          Actor Architecture
                          ─────────────────

  ┌────────────────────────────────────────────────────────┐
  │                    ACTOR SYSTEM                        │
  │                                                        │
  │  ┌──────────┐  mpsc::channel  ┌──────────────────────┐│
  │  │ Producer │ ──────────────► │   Actor (event loop) ││
  │  │ (sender) │                 │   loop {             ││
  │  └──────────┘                 │     match rx.recv() { ││
  │                               │       Msg::Work(d) => ││
  │  ┌──────────┐  mpsc::channel  │         process(d)   ││
  │  │ Producer │ ──────────────► │       Msg::Shutdown   ││
  │  │ (sender) │                 │         => break      ││
  │  └──────────┘                 │     }                 ││
  │                               │   }                   ││
  │                               └──────────────────────┘│
  └────────────────────────────────────────────────────────┘

  Each actor owns its state exclusively. No shared mutable state.
  Communication is via typed channels only.
  Backpressure: bounded channel blocks sender when full.
```

---

## 7. Build Systems

### Cargo Build System — What Actually Happens

Understanding the Cargo build pipeline is essential for FFI work because
`build.rs` is how C libraries get compiled and linked into Rust crates.

```
cargo build
    │
    ├── 1. READ Cargo.toml + Cargo.lock
    │        ↳ resolve dependency graph
    │        ↳ determine feature flags
    │
    ├── 2. RUN build.rs (if present, before compiling src/)
    │        ↳ build.rs can: compile C code, run bindgen, detect system libs
    │        ↳ emits: cargo:rustc-link-lib=..., cargo:rustc-link-search=...
    │        ↳ emits: cargo:rerun-if-changed=... (invalidation triggers)
    │
    ├── 3. COMPILE src/ with rustc
    │        ↳ applies features, cfg flags, target architecture
    │        ↳ generates .rlib or .so
    │
    ├── 4. LINK final binary
    │        ↳ links .rlib files together
    │        ↳ links native libraries specified in build.rs
    │        ↳ links system libraries (libc, pthread, etc.)
    │
    └── 5. OUTPUT to target/debug/ or target/release/
```

### The build.rs File — Central to FFI

```rust
// build.rs — runs before the crate compiles
// This file compiles C code and integrates it with the Rust crate.

fn main() {
    // 1. Tell Cargo to recompile if these files change
    println!("cargo:rerun-if-changed=src/native/foo.c");
    println!("cargo:rerun-if-changed=include/foo.h");

    // 2. Compile C source files using the `cc` crate
    cc::Build::new()
        .file("src/native/foo.c")           // C source file
        .file("src/native/sha256.c")
        .include("include")                  // -I include/
        .flag("-O2")                         // optimization
        .flag("-fstack-protector-strong")    // security hardening
        .flag_if_supported("-fPIC")          // position-independent code
        .define("FOO_VERSION", "\"1.0\"")   // -DFOO_VERSION="1.0"
        .compile("foo");                     // output: libfoo.a

    // 3. Tell Cargo where to find the compiled library
    // "cargo:rustc-link-lib=foo" is emitted automatically by cc::compile()

    // 4. Link additional system libraries if needed
    println!("cargo:rustc-link-lib=crypto"); // -lcrypto (OpenSSL)

    // 5. Run bindgen to generate Rust FFI bindings (see Section 10)
    let bindings = bindgen::Builder::default()
        .header("include/foo.h")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out_path = std::path::PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("foo_bindings.rs"))
        .expect("Couldn't write bindings!");
}
```

### Makefile — The C Build Standard

```makefile
# Canonical C library Makefile structure

# Compiler and flags
CC      := gcc
CFLAGS  := -Wall -Wextra -Wpedantic -O2 -fPIC -fstack-protector-strong
LDFLAGS := -shared
ARFLAGS := rcs

# Directories
SRC_DIR  := src
INC_DIR  := include
OBJ_DIR  := build/obj
LIB_DIR  := build/lib

# Source files — auto-discovered
SRCS := $(wildcard $(SRC_DIR)/*.c) \
        $(wildcard $(SRC_DIR)/crypto/*.c) \
        $(wildcard $(SRC_DIR)/net/*.c)

# Object files — preserve directory structure
OBJS := $(SRCS:$(SRC_DIR)/%.c=$(OBJ_DIR)/%.o)

# Targets
TARGET_STATIC := $(LIB_DIR)/libfoo.a     # static library
TARGET_SHARED := $(LIB_DIR)/libfoo.so    # shared library

.PHONY: all clean install test

all: $(TARGET_STATIC) $(TARGET_SHARED)

# Static library
$(TARGET_STATIC): $(OBJS)
    @mkdir -p $(LIB_DIR)
    $(AR) $(ARFLAGS) $@ $^

# Shared library
$(TARGET_SHARED): $(OBJS)
    @mkdir -p $(LIB_DIR)
    $(CC) $(LDFLAGS) -o $@ $^

# Compile each .c to .o
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
    @mkdir -p $(dir $@)
    $(CC) $(CFLAGS) -I$(INC_DIR) -c $< -o $@

# Install to system (requires root)
install: all
    install -d $(DESTDIR)/usr/lib
    install -m 644 $(TARGET_STATIC) $(DESTDIR)/usr/lib/
    install -m 755 $(TARGET_SHARED) $(DESTDIR)/usr/lib/
    install -d $(DESTDIR)/usr/include/foo
    install -m 644 $(INC_DIR)/foo/*.h $(DESTDIR)/usr/include/foo/

clean:
    rm -rf build/

test: all
    $(CC) $(CFLAGS) -I$(INC_DIR) test/test_foo.c -L$(LIB_DIR) -lfoo -o build/test_foo
    ./build/test_foo
```

---

## 8. C Implementation Internals — How C Actually Works

### Translation Units — The C Compilation Model

This is the foundational concept that explains why C headers and source files
work the way they do.

```
Each .c file = one translation unit.
A translation unit is the basic unit of C compilation.

Source files:             Compilation:              Linking:
                                                  
foo.c ──────────────►  foo.o (object file)  ─┐
  #includes:                                   │
  - <stdint.h>          Contains:              │   Final binary or
  - "foo_internal.h"    - machine code        ─┼──► library:
  - "crypto/sha256.h"   - symbol table        │    libfoo.a or
                        - relocation table    │    libfoo.so or
                                             │    program
sha256.c ──────────►  sha256.o               ─┘
  #includes:
  - "crypto/sha256.h"

The linker resolves symbols across object files.
If foo.c calls sha256_update(), the linker finds sha256_update's
address in sha256.o and patches the call site in foo.o.
```

**Critical insight**: When `foo.c` includes `foo_internal.h`, the preprocessor
literally copies the text of `foo_internal.h` into `foo.c` before compilation.
The `#include` directive is textual substitution. This is why:
- Circular includes cause infinite recursion (solved by include guards)
- Changing a header causes all files that include it to recompile
- Header files must never contain function definitions (or they get
  defined in every translation unit that includes them, causing
  "multiple definition" linker errors)

### The C Memory Model — Stack, Heap, Data Segment, BSS

```
                   Process Memory Layout (Linux x86-64)
                   ─────────────────────────────────────

High Address
┌─────────────────────────────────────────────────────┐ 0x7FFF_FFFF_FFFF
│                      STACK                          │ ← grows downward
│   Local variables, function call frames             │
│   Automatic storage duration                        │
│   Fast: no allocation overhead                      │
│   Limited: ~8MB default (ulimit -s)                 │
├─────────────────────────────────────────────────────┤
│                 (unmapped gap)                       │
├─────────────────────────────────────────────────────┤
│                   HEAP                              │ ← grows upward
│   malloc/free, mmap                                 │
│   Dynamic allocation                                │
│   Managed by allocator (glibc ptmalloc, jemalloc)  │
├─────────────────────────────────────────────────────┤
│                    BSS                              │ ← zero-initialized
│   Uninitialized global/static variables             │
│   static int counter; // lives here                 │
│   Not stored in binary (just size recorded)         │
├─────────────────────────────────────────────────────┤
│                    DATA                             │
│   Initialized global/static variables               │
│   static int max = 1024; // lives here              │
│   static const K[64] = {...}; // here (read-only)  │
├─────────────────────────────────────────────────────┤
│                    TEXT                             │ ← read-only
│   Compiled machine code                             │
│   const string literals                             │
└─────────────────────────────────────────────────────┘ 0x0000_0000_0000
Low Address
```

**Why this matters for Rust FFI**:
- When C allocates with `malloc()` and passes the pointer to Rust, that
  memory lives on the C heap. Rust's allocator does not manage it.
  You cannot call `Box::from_raw()` on it — that would cause a double-free.
- When C fills a stack buffer and passes a pointer to Rust, that pointer
  is only valid for the duration of the C function call. You cannot store it.
- `static` C variables have the lifetime of the process, so Rust can
  safely hold `'static` references to them if they are immutable.

### C Calling Conventions — The ABI Contract

The ABI defines how functions are called at the machine level. For x86-64
Linux (System V AMD64 ABI):

```
Function Call Layout (x86-64 System V ABI)
────────────────────────────────────────────

Argument Passing (first 6 integer/pointer args):
  Arg 1  → RDI register
  Arg 2  → RSI register
  Arg 3  → RDX register
  Arg 4  → RCX register
  Arg 5  → R8  register
  Arg 6  → R9  register
  Arg 7+ → pushed onto stack, right to left

Return Value:
  Integer/Pointer → RAX register
  Large struct    → RDI points to caller-allocated space (hidden first arg)

Caller-saved registers (callee may trash these):
  RAX, RCX, RDX, RSI, RDI, R8, R9, R10, R11

Callee-saved registers (callee must preserve these):
  RBX, RBP, R12, R13, R14, R15

Stack alignment: RSP must be 16-byte aligned before CALL instruction.

foo(ctx, buf, len):   // int foo(foo_ctx_t *ctx, const uint8_t *buf, size_t len)
  ctx → RDI
  buf → RSI
  len → RDX
  ret → RAX (int)
```

**Why Rust needs `extern "C"`**: Rust's default calling convention (for
regular Rust functions) is not guaranteed to match any C ABI. It can
change between compiler versions. `extern "C"` pins the function to the
C calling convention, making it callable from C code and callable from Rust.

### C Error Handling Architecture

C has no exceptions, no `Result<T, E>`. Error handling is done through
return values and output parameters. Knowing this is essential for writing
safe Rust wrappers.

```
Pattern 1: Return error code, output via pointer parameter
──────────────────────────────────────────────────────────
int foo_ctx_connect(
    foo_ctx_t *ctx,
    const char *host,
    uint16_t port,
    char **errmsg    // out-parameter: on error, *errmsg points to allocated string
);

Return:  0 = success
        -1 = system error (check errno)
        -2 = protocol error (check errmsg)
        -3 = timeout

Pattern 2: Return NULL on failure (constructor pattern)
───────────────────────────────────────────────────────
foo_ctx_t *foo_ctx_new(const char *config_path);
// Returns: valid pointer on success
//          NULL on failure, errno is set

Pattern 3: Return number of bytes or -1
───────────────────────────────────────
ssize_t foo_ctx_recv(foo_ctx_t *ctx, uint8_t *buf, size_t buf_len);
// Returns: > 0 = bytes received
//            0 = connection closed (EOF)
//           -1 = error, check errno

Pattern 4: OpenSSL style — separate error stack
────────────────────────────────────────────────
int SSL_connect(SSL *ssl);
// Returns: 1  = success
//          0  = controlled shutdown
//         -1  = fatal error, call SSL_get_error() for reason
//
// The error is on a per-thread error stack. Must be consumed.
unsigned long ERR_get_error(void); // pop from error stack
```

When wrapping these in Rust, each pattern requires a different wrapping strategy.

---

## 9. Rust FFI — Calling C from Rust

### The Mental Model

Foreign Function Interface (FFI) is the mechanism by which Rust calls
C functions and C calls Rust functions. The core idea:

1. Rust must know the **layout** of C types (struct field offsets, sizes)
2. Rust must know the **calling convention** of C functions
3. Rust must uphold the **memory safety invariants** that C would normally
   enforce through programmer discipline

The `unsafe` block around every FFI call is Rust's way of saying:
"The compiler cannot verify that this call is safe. The programmer
has manually checked the contract."

```
┌──────────────────────────────────────────────────────────────┐
│                    SAFETY BOUNDARY                           │
│                                                              │
│  Rust world (safe)       │   C world (unsafe, unknown)       │
│                          │                                   │
│  let ctx = unsafe {      │                                   │
│    foo_ctx_new()         │   foo_ctx_t *foo_ctx_new(void)    │
│  };                      │   {                               │
│                          │       return malloc(sizeof(...)); │
│  // Rust compiler        │   }                               │
│  // cannot see into      │                                   │
│  // the C function.      │                                   │
│  // You must verify:     │                                   │
│  // 1. Returns non-null? │                                   │
│  // 2. Who frees it?     │                                   │
│  // 3. Is it thread-safe?│                                   │
│  // 4. Lifetime?         │                                   │
└──────────────────────────────────────────────────────────────┘
```

### Declaring External C Functions

```rust
// src/sys.rs — raw FFI declarations

// extern "C" block declares C functions Rust can call.
// These are DECLARATIONS, not definitions. The actual code is in .c files.
// The linker resolves these at link time.

use std::ffi::{c_int, c_char, c_void};
use std::os::raw::c_size_t;    // or use libc::size_t

// Opaque type for C structs we cannot see the internals of
// This is the correct Rust representation of `typedef struct foo_ctx foo_ctx_t;`
#[repr(C)]
pub struct FooCtx {
    // Empty struct with a private field to prevent construction outside unsafe
    // and to make the type non-zero-sized (important: zero-sized types in FFI
    // cause undefined behavior)
    _opaque: [u8; 0],
    // PhantomData prevents this type from being Send/Sync automatically
    _marker: std::marker::PhantomData<(*mut u8, std::marker::PhantomUnsafe)>,
}

// Alternative: use c_void pointer
// pub type FooCtx = c_void; // less common, loses type checking

extern "C" {
    // Maps to: foo_ctx_t *foo_ctx_new(void);
    pub fn foo_ctx_new() -> *mut FooCtx;

    // Maps to: void foo_ctx_free(foo_ctx_t *ctx);
    pub fn foo_ctx_free(ctx: *mut FooCtx);

    // Maps to: int foo_ctx_connect(foo_ctx_t *ctx, const char *host, uint16_t port);
    pub fn foo_ctx_connect(
        ctx: *mut FooCtx,
        host: *const c_char,
        port: u16,
    ) -> c_int;

    // Maps to: ssize_t foo_ctx_recv(foo_ctx_t *ctx, uint8_t *buf, size_t len);
    pub fn foo_ctx_recv(
        ctx: *mut FooCtx,
        buf: *mut u8,
        len: usize,
    ) -> isize;
}
```

### Representing C Types in Rust — The Complete Mapping

```
C Type                    Rust Type                   Notes
────────────────────────────────────────────────────────────────
void                      ()                           unit type
int                       c_int (= i32 on most)       use std::ffi::c_int
unsigned int              c_uint
long                      c_long                       platform-dependent!
unsigned long             c_ulong
long long                 c_longlong (= i64)
size_t                    usize                        or libc::size_t
ssize_t                   isize                        or libc::ssize_t
uint8_t                   u8
uint16_t                  u16
uint32_t                  u32
uint64_t                  u64
int8_t                    i8
int16_t                   i16
int32_t                   i32
int64_t                   i64
float                     f32
double                    f64
char *                    *mut c_char                  or *const c_char
const char *              *const c_char
void *                    *mut c_void                  or *const c_void
uint8_t *                 *mut u8
const uint8_t *           *const u8
bool (_Bool in C99)       bool                         same layout
enum (C)                  u32 / i32 / #[repr(u32)]   depends on platform
struct (C)                #[repr(C)] struct            MUST have repr(C)
union (C)                 #[repr(C)] union             requires unsafe to access
function pointer          Option<unsafe extern "C" fn(...)>
NULL pointer              std::ptr::null() / null_mut()
```

### The `#[repr(C)]` Attribute — Critical for FFI

Without `#[repr(C)]`, Rust's compiler can reorder struct fields, add padding
differently, or change the struct layout in any way it wants. With `#[repr(C)]`,
the struct has exactly the same layout as the equivalent C struct.

```rust
// C:
// struct packet_header {
//     uint8_t  version;
//     uint8_t  flags;
//     uint16_t length;
//     uint32_t sequence;
// };

// Rust equivalent:
#[repr(C)]
pub struct PacketHeader {
    pub version:  u8,
    pub flags:    u8,
    pub length:   u16,
    pub sequence: u32,
}

// Memory layout:
// Offset 0: version  (1 byte)
// Offset 1: flags    (1 byte)
// Offset 2: length   (2 bytes, may have padding without repr(C))
// Offset 4: sequence (4 bytes)
// Total:    8 bytes

// WITHOUT #[repr(C)], Rust might lay this out differently for optimization.
// WITH #[repr(C)], it matches C exactly. This is required for:
// - eBPF map key/value structs
// - Network packet header parsing (when casting raw bytes)
// - Structs passed to/from C functions by pointer
// - Any struct that matches a wire format

// ASCII layout diagram:
//  0         1         2         3
//  0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
// +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
// |    version    |     flags     |            length             |
// +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
// |                           sequence                            |
// +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### String Handling Across the FFI Boundary

Strings are the most common source of FFI bugs. C strings are `\0`-terminated
byte arrays. Rust strings are UTF-8, length-prefixed, and not `\0`-terminated.

```rust
use std::ffi::{CStr, CString, c_char};

// PASSING A RUST STRING TO C:
// Must create a CString (adds the \0 terminator and validates no interior \0s)
fn connect_to_host(ctx: *mut FooCtx, host: &str) -> Result<(), Error> {
    // CString::new fails if host contains \0 bytes
    let c_host = CString::new(host).map_err(|_| Error::InvalidHost)?;

    // c_host.as_ptr() gives *const c_char
    // The pointer is valid as long as c_host is alive.
    // Do NOT return c_host.as_ptr() and drop c_host — dangling pointer!
    let ret = unsafe {
        foo_ctx_connect(ctx, c_host.as_ptr(), 443)
    };

    if ret == 0 { Ok(()) } else { Err(Error::ConnectFailed(ret)) }
}
// c_host is dropped here — that's fine because foo_ctx_connect already used it.

// RECEIVING A STRING FROM C:
// C returns const char *, pointing to C-owned memory
fn get_error_message(ctx: *mut FooCtx) -> &'static str {
    let raw: *const c_char = unsafe { foo_get_error_msg(ctx) };

    if raw.is_null() {
        return "unknown error";
    }

    // CStr::from_ptr: borrows the C string without copying
    // SAFETY: raw must be a valid, \0-terminated C string
    //         and must remain valid for the returned lifetime
    let c_str = unsafe { CStr::from_ptr(raw) };

    // to_str() validates UTF-8 — C strings may not be valid UTF-8!
    c_str.to_str().unwrap_or("invalid utf-8 in error message")
}
```

### Ownership and Lifetime Across FFI

This is the hardest part of FFI. C does not have ownership. You must
manually encode the ownership contract into Rust types.

```rust
// PATTERN: RAII wrapper that owns C-allocated memory
// When this struct is dropped, it calls the C free function.

pub struct FooContext {
    // NonNull ensures we can't have a null pointer accidentally
    // The *mut is necessary because C functions take mutable pointers
    inner: std::ptr::NonNull<FooCtx>,
}

impl FooContext {
    pub fn new() -> Result<Self, Error> {
        let raw = unsafe { foo_ctx_new() };

        // Check for NULL — C allocation can fail
        let inner = std::ptr::NonNull::new(raw)
            .ok_or(Error::AllocationFailed)?;

        Ok(FooContext { inner })
    }

    // Returns a raw pointer for passing to C functions.
    // The pointer is valid as long as `self` is alive.
    fn as_ptr(&self) -> *mut FooCtx {
        self.inner.as_ptr()
    }

    pub fn connect(&self, host: &str, port: u16) -> Result<(), Error> {
        let c_host = CString::new(host)?;
        let ret = unsafe {
            foo_ctx_connect(self.as_ptr(), c_host.as_ptr(), port)
        };
        if ret == 0 { Ok(()) } else { Err(Error::ConnectFailed(ret)) }
    }
}

impl Drop for FooContext {
    fn drop(&mut self) {
        // SAFETY: self.inner is always a valid pointer obtained from
        //         foo_ctx_new(). We call foo_ctx_free() exactly once
        //         here in Drop, which is the last use.
        unsafe { foo_ctx_free(self.inner.as_ptr()) }
    }
}

// Thread safety: declare explicitly based on C library documentation.
// Only do this if the C library is documented as thread-safe for these ops.
unsafe impl Send for FooContext {}    // Can be sent to another thread
// unsafe impl Sync for FooContext {} // Can be shared between threads (DON'T
                                      // unless C library is reentrant)
```

---

## 10. Bindgen — Automating C Binding Generation

### What Bindgen Does

Bindgen parses C header files and generates Rust `extern "C"` declarations
automatically. Without bindgen, you write FFI declarations by hand —
error-prone and labor-intensive for large C libraries.

```
Process:
                                    
include/foo.h ──────────────────────────────────────────────────────►
                                                                      bindgen
libclang (C parser) ─► AST of C types/functions/constants ──────────►
                                                                      │
                                                               foo_bindings.rs
                                                               (auto-generated)
                                                                      │
                                                              src/lib.rs:
                                                              include!(concat!(
                                                                env!("OUT_DIR"),
                                                                "/foo_bindings.rs"
                                                              ));
```

### Bindgen Configuration in build.rs

```rust
// build.rs — complete bindgen setup for a real C library
use bindgen;
use std::path::PathBuf;

fn main() {
    // 1. Locate the C library headers (use pkg-config in production)
    let library = pkg_config::probe_library("libfoo").unwrap_or_else(|_| {
        // Fallback: look in standard locations
        println!("cargo:rustc-link-lib=foo");
        pkg_config::Library::default()
    });

    // 2. Configure bindgen
    let bindings = bindgen::Builder::default()
        // The header to parse
        .header("include/foo.h")

        // Parse Cargo-related env vars for rerun-if-changed
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))

        // Only generate bindings for symbols starting with "foo_"
        .allowlist_function("foo_.*")
        .allowlist_type("foo_.*")
        .allowlist_var("FOO_.*")

        // Block types we don't want (e.g., system types already in libc)
        .blocklist_type("__.*")
        .blocklist_type("size_t")  // use usize instead

        // Generate #[repr(C)] on all structs (default: yes)
        // .default_enum_style(bindgen::EnumVariation::Rust)  ← nicer enums

        // Mark types as not implementing Copy (for RAII wrappers)
        .no_copy("foo_ctx_t")

        // Generate Default impl for POD types
        .derive_default(true)

        // For eBPF structs: generate packed layout
        // .packed(true)  ← only if needed

        .generate()
        .expect("Unable to generate bindings");

    // 3. Write to OUT_DIR (Cargo-managed temp directory)
    let out_path = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("foo_bindings.rs"))
        .expect("Couldn't write bindings!");
}
```

### What Generated Bindings Look Like

Given this C header:

```c
// include/foo.h
typedef struct foo_ctx foo_ctx_t;

typedef enum {
    FOO_STATE_INIT      = 0,
    FOO_STATE_CONNECTED = 1,
    FOO_STATE_ERROR     = -1,
} foo_state_t;

foo_ctx_t *foo_ctx_new(void);
void       foo_ctx_free(foo_ctx_t *ctx);
int        foo_ctx_connect(foo_ctx_t *ctx, const char *host, uint16_t port);

#define FOO_MAX_CONNECTIONS 1024
```

Bindgen generates approximately:

```rust
// foo_bindings.rs (AUTO-GENERATED — DO NOT EDIT)

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct foo_ctx {
    pub _address: u8,  // placeholder for opaque struct
}

pub type foo_ctx_t = foo_ctx;

pub type foo_state_t = ::std::os::raw::c_int;
pub const foo_state_t_FOO_STATE_INIT: foo_state_t = 0;
pub const foo_state_t_FOO_STATE_CONNECTED: foo_state_t = 1;
pub const foo_state_t_FOO_STATE_ERROR: foo_state_t = -1;

pub const FOO_MAX_CONNECTIONS: u32 = 1024;

extern "C" {
    pub fn foo_ctx_new() -> *mut foo_ctx_t;
    pub fn foo_ctx_free(ctx: *mut foo_ctx_t);
    pub fn foo_ctx_connect(
        ctx: *mut foo_ctx_t,
        host: *const ::std::os::raw::c_char,
        port: u16,
    ) -> ::std::os::raw::c_int;
}
```

---

## 11. The -sys Crate Pattern — The Rust Ecosystem Standard

### Why -sys Crates Exist

The Rust ecosystem standardized on a pattern for C FFI:
- `libfoo-sys` crate: raw, unsafe bindings only. No safe wrappers.
- `libfoo` crate: safe Rust wrapper over `libfoo-sys`.

This separation means multiple safe wrappers can exist over one set of bindings.

```
Rust Ecosystem Dependency Graph:
─────────────────────────────────

my-application
    │
    └── depends on: tokio-rustls
                        │
                        ├── depends on: rustls     (safe TLS, pure Rust)
                        └── depends on: tokio      (async runtime)

OR, if using OpenSSL:

my-application
    │
    └── depends on: openssl          (safe wrapper)
                        │
                        └── depends on: openssl-sys     (raw FFI)
                                            │
                                    build.rs: compiles libssl.a
                                    or links system libssl.so
```

### -sys Crate Structure

```
libfoo-sys/
├── Cargo.toml
├── build.rs           ← compiles C, runs bindgen, links library
├── src/
│   └── lib.rs         ← only: include!(concat!(env!("OUT_DIR"), "/bindings.rs"))
├── include/           ← vendored C headers (or use installed)
│   └── foo.h
└── src_c/             ← vendored C source (optional: some sys crates compile C)
    ├── foo.c
    └── sha256.c
```

The `Cargo.toml` for a `-sys` crate has a special key: `links`:

```toml
# libfoo-sys/Cargo.toml
[package]
name = "libfoo-sys"
version = "0.1.0"
links = "foo"          # ← tells Cargo this crate links to native library "foo"
                       #   Cargo enforces that only one crate links to "foo"
                       #   Prevents duplicate symbol errors

[build-dependencies]
bindgen = "0.70"
cc = "1.0"
pkg-config = "0.3"

[dependencies]
libc = "0.2"
```

### Complete -sys to Safe Wrapper Example

```rust
// libfoo-sys/src/lib.rs — raw bindings, nothing else
#![allow(non_upper_case_globals)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]

include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
```

```rust
// libfoo/src/lib.rs — safe wrapper
//! Safe Rust bindings to libfoo.

mod context;
mod error;

pub use context::FooContext;
pub use error::Error;
pub type Result<T> = std::result::Result<T, Error>;
```

```rust
// libfoo/src/error.rs — translating C error codes to Rust errors
use thiserror::Error;

#[derive(Debug, Error)]
pub enum Error {
    #[error("allocation failed (out of memory)")]
    AllocationFailed,

    #[error("connection failed: error code {0}")]
    ConnectFailed(i32),

    #[error("null pointer in C string argument")]
    NullInString(#[from] std::ffi::NulError),

    #[error("C library returned invalid UTF-8")]
    InvalidUtf8,

    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
}

// Translate C integer error codes to Rust errors
pub fn from_c_error(code: i32) -> Error {
    match code {
        -1 => Error::ConnectFailed(-1),  // or map to io::Error via errno
        -2 => Error::ConnectFailed(-2),
        _  => Error::ConnectFailed(code),
    }
}
```

---

## 12. Unsafe Contracts in FFI — What You Must Guarantee

### The Safety Contract Checklist

Every `unsafe { }` block that calls a C function has an implicit contract.
Documenting this contract is mandatory in production code. Here is the
complete checklist for every FFI call:

```rust
// Template for documenting unsafe FFI calls:

/// # Safety
///
/// Callers must ensure:
/// 1. POINTER VALIDITY: `ctx` must be a non-null pointer obtained from
///    `foo_ctx_new()` and not yet freed.
///
/// 2. ALIASING: No other thread may hold a mutable reference to `*ctx`
///    while this function executes.
///
/// 3. LIFETIME: `ctx` must remain valid for the entire duration of this
///    function call and until `foo_ctx_free()` is called.
///
/// 4. STRING TERMINATION: `host` must point to a null-terminated C string
///    valid for the duration of this call.
///
/// 5. ERROR HANDLING: If this returns non-zero, call `foo_get_error()` to
///    retrieve the error and `foo_clear_error()` to reset state before
///    any subsequent call.
pub unsafe fn raw_connect(ctx: *mut FooCtx, host: *const c_char, port: u16)
    -> c_int
{
    unsafe { foo_ctx_connect(ctx, host, port) }
}
```

### Common FFI Undefined Behavior Sources

```
┌─────────────────────────────────────────────────────────────────┐
│               FFI UNDEFINED BEHAVIOR CATALOG                    │
├─────────────────┬───────────────────────────────────────────────┤
│ UB Type         │ Example                                       │
├─────────────────┼───────────────────────────────────────────────┤
│ Null deref      │ Passing null where C expects non-null         │
├─────────────────┼───────────────────────────────────────────────┤
│ Use after free  │ Calling foo_ctx_send() after foo_ctx_free()  │
├─────────────────┼───────────────────────────────────────────────┤
│ Double free     │ Two Drop impls calling foo_ctx_free()         │
├─────────────────┼───────────────────────────────────────────────┤
│ Mismatched      │ Calling C's free() on Rust-allocated memory   │
│ allocator       │ or Box::from_raw on malloc'd pointer          │
├─────────────────┼───────────────────────────────────────────────┤
│ Data race       │ Sharing *mut FooCtx across threads without    │
│                 │ synchronization when C is not thread-safe     │
├─────────────────┼───────────────────────────────────────────────┤
│ Invalid enum    │ Transmuting integer to Rust enum where value  │
│ discriminant    │ is not a valid variant                        │
├─────────────────┼───────────────────────────────────────────────┤
│ Uninitialized   │ Reading from a C out-param before C fills it  │
│ memory read     │ (use MaybeUninit<T> for out-params)           │
├─────────────────┼───────────────────────────────────────────────┤
│ Wrong alignment │ Casting *mut u8 to *mut u32 on misaligned ptr │
├─────────────────┼───────────────────────────────────────────────┤
│ Stack lifetime  │ Storing pointer to C stack allocation after   │
│ violation       │ C function returns                            │
├─────────────────┼───────────────────────────────────────────────┤
│ Signal unsafety │ Calling non-async-signal-safe functions from  │
│                 │ a signal handler                              │
└─────────────────┴───────────────────────────────────────────────┘
```

### MaybeUninit — The Correct Pattern for C Out-Parameters

```rust
use std::mem::MaybeUninit;

// C function: int foo_get_stats(foo_ctx_t *ctx, foo_stats_t *out_stats);
// Pattern: C fills in *out_stats, returns 0 on success

pub fn get_stats(ctx: &FooContext) -> Result<FooStats, Error> {
    // MaybeUninit<T> is uninitialized memory of the right size/alignment.
    // We cannot read from it until C fills it in.
    let mut stats = MaybeUninit::<FooStats>::uninit();

    let ret = unsafe {
        foo_get_stats(
            ctx.as_ptr(),
            stats.as_mut_ptr()   // *mut FooStats: safe to pass to C for writing
        )
    };

    if ret != 0 {
        return Err(Error::GetStatsFailed(ret));
    }

    // SAFETY: foo_get_stats returned 0, meaning it initialized *out_stats fully.
    // We may now call assume_init() to treat the memory as initialized.
    let stats = unsafe { stats.assume_init() };
    Ok(stats)
}

// ANTI-PATTERN:
// let mut stats: FooStats = std::mem::zeroed(); // zeroed() creates arbitrary bit pattern
// This works for many types but is UB for types with invalid bit patterns (bool, enum, etc.)
// MaybeUninit is always correct.
```

---

## 13. Real Project Walkthroughs

### 13.1 Linux Kernel — The C Archetype

The Linux kernel is the canonical example of large-scale C architecture.
Every systems programmer should understand its structure.

```
linux/
├── arch/               ← architecture-specific code
│   ├── x86/
│   │   ├── kernel/     ← x86 kernel entry, syscalls, interrupts
│   │   ├── mm/         ← x86 memory management
│   │   └── include/    ← x86-specific headers
│   └── arm64/
│
├── kernel/             ← core kernel subsystems
│   ├── sched/          ← CPU scheduler (CFS, RT, deadline)
│   ├── time/           ← timekeeping, hrtimers
│   ├── locking/        ← spinlocks, mutexes, rwlocks
│   └── bpf/            ← eBPF verifier, interpreter, JIT
│
├── mm/                 ← memory management (slab, vmalloc, mmap)
├── net/                ← networking subsystem
│   ├── core/           ← socket layer, sk_buff
│   ├── ipv4/           ← IPv4 stack
│   ├── ipv6/           ← IPv6 stack
│   └── sched/          ← traffic control (TC)
│
├── fs/                 ← filesystems (ext4, btrfs, overlayfs)
├── drivers/            ← device drivers
├── security/           ← LSM, SELinux, seccomp
├── tools/
│   └── bpf/            ← BPF tools, bpftool, libbpf
│
└── include/
    ├── linux/          ← kernel headers (also exported to userspace)
    │   ├── bpf.h       ← BPF syscall API, map types, program types
    │   └── if_ether.h  ← Ethernet header definitions
    └── uapi/           ← ONLY headers exported to userspace ABI
        └── linux/
            ├── bpf.h
            └── if_packet.h
```

**Key kernel naming conventions**:

```c
/* Subsystem prefix convention */
// net/   → sk_*, skb_*, net_*, sock_*
// mm/    → page_*, pgd_*, pmd_*, vma_*
// bpf/   → bpf_*, BPF_*, btf_*
// sched/ → task_*, sched_*, cfs_*, rt_*

/* Function name patterns */
static int  foo_init(struct foo_device *dev);    // init: returns 0 or -errno
static void foo_cleanup(struct foo_device *dev); // cleanup: void, always succeeds
static int  foo_open(struct inode *inode, struct file *file); // VFS ops

/* Error return convention */
// Returns 0 on success
// Returns -errno on failure (negative errno value, e.g. -ENOMEM, -EINVAL)
// Never returns positive values unless specifically documented
```

**The sk_buff (socket buffer) — how the kernel represents a packet**:

```
                     struct sk_buff Layout
                     ─────────────────────

sk_buff (metadata):                    
┌─────────────────────────────────┐    
│ struct sk_buff *next, *prev     │ ← linked list of buffers
│ struct sock *sk                 │ ← owning socket
│ unsigned int len                │ ← total data length
│ __u16 protocol                  │ ← ETH_P_IP, ETH_P_IPV6, etc.
│ unsigned char *head             │ ←─────────────────────────────────┐
│ unsigned char *data             │ ←──────────────────────┐          │
│ unsigned char *tail             │ ←─────────────┐        │          │
│ unsigned char *end              │ ←─────┐       │        │          │
│ transport_header offset         │       │       │        │          │
│ network_header offset           │       │       │        │          │
│ mac_header offset               │       │       │        │          │
└─────────────────────────────────┘       │       │        │          │
                                          │       │        │          │
Actual packet data buffer:                │       │        │          │
┌────────────────────────────────────────┐│       │        │          │
│ headroom (for prepending headers) ◄────┘│       │        │          │
│                                         │       │        │          │
│ [Ethernet header]     ◄─────── mac_hdr─┤       │        │          │
│ [IP header]           ◄─────── net_hdr─┤       │        │          │
│ [TCP header]          ◄─────── thdr────┤       │        │          │
│ [Payload data]        ◄─────────────────┘       │        │          │
│ tailroom              ◄─────────────────────────┘        │          │
│ (unused)                                                  │          │
└───────────────────────────────────────────────────────────┘          │
 ^                                                                      │
 head ◄──────────────────────────────────────────────────────────────┘
```

### 13.2 tokio — Rust Async Runtime

```
tokio/
├── tokio/                        ← main library crate
│   ├── src/
│   │   ├── lib.rs                ← feature-gated re-exports
│   │   ├── runtime/              ← the executor
│   │   │   ├── mod.rs
│   │   │   ├── builder.rs        ← Runtime::new(), RuntimeBuilder
│   │   │   ├── handle.rs         ← runtime handle for spawning
│   │   │   ├── task/             ← task representation
│   │   │   │   ├── mod.rs
│   │   │   │   ├── harness.rs    ← future polling logic
│   │   │   │   ├── list.rs       ← task list for shutdown
│   │   │   │   └── state.rs      ← task state machine
│   │   │   ├── scheduler/        ← work-stealing scheduler
│   │   │   │   ├── current_thread.rs
│   │   │   │   └── multi_thread/
│   │   │   │       ├── mod.rs
│   │   │   │       ├── worker.rs ← per-thread worker loop
│   │   │   │       └── queue.rs  ← work-stealing deque
│   │   │   └── io/               ← I/O driver (epoll/kqueue/IOCP)
│   │   │       ├── driver/
│   │   │       │   ├── mod.rs
│   │   │       │   └── mio.rs    ← mio integration
│   │   │       └── poll_evented.rs
│   │   │
│   │   ├── net/                  ← async networking types
│   │   │   ├── tcp/
│   │   │   │   ├── stream.rs     ← TcpStream
│   │   │   │   └── listener.rs   ← TcpListener
│   │   │   └── udp.rs
│   │   │
│   │   ├── sync/                 ← async synchronization primitives
│   │   │   ├── mpsc/             ← multi-producer single-consumer channel
│   │   │   ├── broadcast.rs      ← broadcast channel
│   │   │   ├── mutex.rs          ← async Mutex
│   │   │   ├── rwlock.rs         ← async RwLock
│   │   │   └── semaphore.rs      ← async Semaphore
│   │   │
│   │   ├── time/                 ← timers and sleep
│   │   │   ├── sleep.rs          ← tokio::time::sleep()
│   │   │   └── wheel/            ← hierarchical timing wheel
│   │   │
│   │   └── task/                 ← public task API (spawn, JoinHandle)
│   │
│   └── tests/                    ← integration tests
│
├── tokio-util/                   ← utilities (codecs, framing)
├── tokio-stream/                 ← Stream trait integration
└── tokio-test/                   ← test utilities
```

**How tokio's async task becomes a system call**:

```
async fn read_packet(stream: &mut TcpStream) -> io::Result<Vec<u8>>

Step 1: Future created (no system call yet)
    ↓
Step 2: Executor polls the Future
    ↓
Step 3: TcpStream tries to read (calls mio)
    ↓
Step 4: mio calls recv(2) syscall
    ↓
    ├── Data available: return Poll::Ready(data)
    │
    └── EWOULDBLOCK: register fd with epoll_ctl()
            ↓
        Return Poll::Pending
            ↓
        Executor parks this task, runs other tasks
            ↓
        epoll_wait() returns this fd as ready
            ↓
        Executor wakes task, polls again
            ↓
        recv(2) succeeds
            ↓
        Return Poll::Ready(data)
```

### 13.3 rustls — Pure Rust TLS

```
rustls/
├── rustls/
│   ├── src/
│   │   ├── lib.rs              ← public API surface
│   │   ├── client/
│   │   │   ├── mod.rs
│   │   │   ├── client_conn.rs  ← ClientConnection type
│   │   │   ├── hs.rs           ← client handshake state machine
│   │   │   └── tls13.rs        ← TLS 1.3 client handshake
│   │   ├── server/
│   │   │   ├── server_conn.rs  ← ServerConnection type
│   │   │   ├── hs.rs           ← server handshake state machine
│   │   │   └── tls13.rs        ← TLS 1.3 server handshake
│   │   │
│   │   ├── record_layer.rs     ← TLS record layer (encrypt/decrypt)
│   │   ├── tls13/              ← TLS 1.3 key schedule (RFC 8446)
│   │   │   ├── key_schedule.rs ← HKDF key derivation
│   │   │   └── handshake.rs
│   │   │
│   │   ├── crypto/             ← crypto provider abstraction
│   │   │   ├── mod.rs          ← CryptoProvider trait
│   │   │   └── ring.rs         ← ring crate implementation
│   │   │
│   │   ├── msgs/               ← TLS message encoding/decoding
│   │   │   ├── handshake.rs    ← ClientHello, ServerHello, etc.
│   │   │   ├── enums.rs        ← CipherSuite, ExtensionType, etc.
│   │   │   └── codec.rs        ← TLS wire format codec
│   │   │
│   │   └── verify/             ← certificate verification
│   │       ├── mod.rs
│   │       └── webpki.rs       ← X.509 certificate verification
```

**Key architecture insight in rustls**: The handshake state machine is
encoded in the type system. Each handshake state is a different struct.
Transitions are function calls that consume the old state and produce the new.
The compiler prevents skipping states.

```rust
// Simplified rustls handshake state machine (conceptual):

struct ClientStart;
struct ClientWaitServerHello { client_hello: ClientHello }
struct ClientWaitCertificate { handshake_hash: HandshakeHash }
struct ClientConnected      { session: Session }

impl ClientStart {
    fn send_hello(self, config: &Config) 
        -> (ClientWaitServerHello, Vec<u8>) // returns (new state, bytes to send)
    { /* ... */ }
}

impl ClientWaitServerHello {
    fn process_server_hello(self, msg: ServerHello) 
        -> Result<ClientWaitCertificate, Error>
    { /* ... */ }
}
// Type system enforces: you cannot call process_certificate() before
// process_server_hello() because you don't have a ClientWaitCertificate yet.
```

### 13.4 aya — eBPF in Rust with Kernel C FFI

aya is the prime example of: Rust safe wrapper over complex kernel C ABI.

```
aya/
├── aya/                    ← userspace crate (loads and manages eBPF programs)
│   ├── src/
│   │   ├── lib.rs
│   │   ├── bpf/
│   │   │   ├── mod.rs      ← Ebpf struct: the handle to loaded eBPF programs
│   │   │   └── info.rs
│   │   ├── maps/           ← eBPF map types
│   │   │   ├── mod.rs
│   │   │   ├── hash_map.rs ← BPF_MAP_TYPE_HASH
│   │   │   ├── array.rs    ← BPF_MAP_TYPE_ARRAY
│   │   │   └── ring_buf.rs ← BPF_MAP_TYPE_RINGBUF
│   │   ├── programs/       ← eBPF program types
│   │   │   ├── mod.rs
│   │   │   ├── xdp.rs      ← XDP programs
│   │   │   ├── tc.rs       ← TC classifier programs
│   │   │   ├── kprobe.rs   ← kprobe/kretprobe
│   │   │   └── tracepoint.rs
│   │   └── sys/            ← raw bpf(2) syscall wrappers
│   │       ├── mod.rs
│   │       └── bpf.rs      ← bpf() syscall, all BPF_CMD_ variants
│   │
├── aya-ebpf/               ← in-kernel crate (code that runs IN the kernel)
│   ├── src/
│   │   ├── lib.rs          ← no_std, BPF verifier constraints apply
│   │   ├── maps/           ← kernel-side map access
│   │   └── programs/       ← program context types (XdpContext, etc.)
│   │
└── aya-obj/                ← ELF object file parsing (reads compiled eBPF ELF)
    └── src/
        ├── obj.rs          ← ELF section parsing
        └── btf/            ← BTF (BPF Type Format) parsing
```

**How aya interacts with the kernel C ABI**:

```
aya loads eBPF program:
                         
 1. aya-obj parses .o ELF file  (compiled from aya-ebpf Rust code)
    ↓
 2. aya extracts BTF type info   (for CO-RE: Compile Once Run Everywhere)
    ↓
 3. aya calls bpf(BPF_MAP_CREATE, ...) syscall
    → raw bpf(2) syscall: unsafe { syscall(SYS_bpf, BPF_MAP_CREATE, ...) }
    → kernel validates map spec, returns fd
    ↓
 4. aya calls bpf(BPF_PROG_LOAD, ...) with bytecode + BTF
    → kernel eBPF verifier checks safety of bytecode
    → if verified: JIT-compiles to native code, returns program fd
    ↓
 5. aya attaches program to hook point
    → XDP: netlink socket + XDP_FLAGS_* to set xdp program on interface
    → TC:  netlink socket + tc qdisc/filter commands
    → kprobe: perf_event_open() + ioctl(PERF_EVENT_IOC_SET_BPF)

aya map access:
    Rust code calls: map.insert(&key, &value, 0)?
    ↓
    bpf(BPF_MAP_UPDATE_ELEM, { map_fd, key_ptr, value_ptr, flags })
    ↓
    kernel atomically updates map entry
```

**The aya XDP program in aya-ebpf**:

```rust
// In-kernel eBPF Rust code (compiles to BPF bytecode)
// This runs in the kernel, not userspace.
// no_std, no heap, no system calls, strict verifier rules.

#![no_std]
#![no_main]

use aya_ebpf::{
    macros::xdp,
    programs::XdpContext,
    maps::HashMap,
};
use aya_ebpf::bindings::xdp_action; // generated from kernel headers

// This HashMap is a BPF map shared between kernel and userspace
#[map]
static BLOCKED_IPS: HashMap<u32, u8> = HashMap::with_max_entries(10_000, 0);

#[xdp]   // tells aya this is an XDP program, goes into .text.xdp ELF section
pub fn xdp_firewall(ctx: XdpContext) -> u32 {
    match try_xdp_firewall(ctx) {
        Ok(ret) => ret,
        Err(_)  => xdp_action::XDP_PASS,  // on error, pass packet (fail-open)
    }
}

fn try_xdp_firewall(ctx: XdpContext) -> Result<u32, ()> {
    // Parse IP header from raw packet bytes
    let ip_hdr: *const iphdr = ptr_at(&ctx, ETH_HDR_LEN)?;

    // SAFETY: verifier ensures data pointer is valid after bounds check
    let src_ip = unsafe { (*ip_hdr).saddr };

    // Check if source IP is in blocked list
    if BLOCKED_IPS.get(&src_ip).is_some() {
        return Ok(xdp_action::XDP_DROP);  // drop the packet
    }

    Ok(xdp_action::XDP_PASS)
}
```

### 13.5 OpenSSL / ring — Crypto Library FFI Pattern

`ring` is pure Rust. `openssl` is Rust FFI over C OpenSSL. Comparing them
shows the full spectrum of C integration.

```
openssl (crate)/
├── openssl/                ← safe Rust wrapper
│   └── src/
│       ├── ssl/            ← SSL_CTX, SSL, handshake
│       ├── x509/           ← certificate types
│       ├── aes.rs          ← AES cipher wrapper
│       └── error.rs        ← OpenSSL error stack → Rust Result
│
└── openssl-sys/            ← raw FFI: -sys crate
    ├── build/
    │   ├── main.rs         ← build.rs: detects system OpenSSL or builds vendored
    │   ├── find_normal.rs  ← pkg-config / system library detection
    │   └── run_bindgen.rs  ← bindgen invocation
    └── src/
        ├── lib.rs
        ├── ssl.rs          ← SSL_* function declarations
        ├── x509.rs         ← X509_* function declarations
        └── handgenerated/  ← some bindings written by hand (complex macros)
```

**Key pattern in openssl-sys build.rs** — detecting whether to use system
OpenSSL or vendored (compiled from source):

```rust
// openssl-sys/build/main.rs (conceptual)
fn main() {
    // Check for OPENSSL_DIR env var (explicit path override)
    // Then try pkg-config: pkg-config --libs openssl
    // Then try well-known system paths: /usr/lib, /usr/local/lib
    // If vendor feature enabled: compile OpenSSL from bundled source

    let openssl = find_openssl();

    // Emit link instructions
    for lib in &openssl.libs {
        println!("cargo:rustc-link-lib={}", lib);       // -lssl, -lcrypto
    }
    for path in &openssl.link_paths {
        println!("cargo:rustc-link-search=native={}", path); // -L/path
    }

    // Run bindgen for the detected version
    generate_bindings(&openssl);
}
```

### 13.6 libbpf-sys — The sys Crate Pattern in Practice

`libbpf-sys` is the direct C-to-Rust binding for `libbpf`, the canonical
C library for loading eBPF programs. `aya` does NOT use libbpf (it reimplements
the functionality in pure Rust). But `libbpf-sys` shows the pattern.

```
libbpf-sys/
├── Cargo.toml
│   [package]
│   name = "libbpf-sys"
│   links = "bpf"
│
├── build.rs            ← compile vendored libbpf C source
│   // Uses cc crate to compile:
│   // - libbpf/src/bpf.c
│   // - libbpf/src/btf.c
│   // - libbpf/src/ringbuf.c
│   // - libbpf/src/xsk.c (AF_XDP)
│   // Runs bindgen on libbpf/include/bpf/libbpf.h
│
├── libbpf/             ← vendored C source (git submodule)
│   └── src/
│       ├── bpf.c       ← bpf() syscall wrappers
│       ├── btf.c       ← BTF parsing
│       └── libbpf.c    ← program load, map creation
│
└── src/
    └── lib.rs
        include!(concat!(env!("OUT_DIR"), "/libbpf_bindings.rs"));
```

---

## 14. Variable Naming Deep Dive — What Names Signal

### Naming Encodes Semantics, Not Just Description

The best naming conventions encode the **type, ownership, and lifetime**
of a variable in its name, so a reader can understand key properties
without reading the type annotation.

```rust
// LENGTH AND COUNT variables — always usize or similar unsigned
let len: usize;          // byte count in a buffer
let count: usize;        // element count in a collection
let n_connections: u32;  // "n_" prefix = count
let num_retries: u32;    // "num_" prefix = count (less preferred in Rust)

// CAPACITY vs LENGTH distinction:
let buf_len: usize;      // bytes currently in buf (data end)
let buf_cap: usize;      // total allocated capacity of buf
// In Rust: Vec::len() vs Vec::capacity()

// OFFSET AND INDEX — explicit type prevents confusion
let byte_offset: usize;  // offset in bytes (always from start)
let bit_offset: usize;   // offset in bits
let idx: usize;          // index into a slice/vec
let header_offset: u32;  // offset to a protocol header

// POINTER/REFERENCE naming — signal mutability and origin
let buf: &[u8];          // immutable borrow of byte slice
let buf: &mut [u8];      // mutable borrow
let buf: Vec<u8>;        // owned
let buf_ptr: *const u8;  // raw pointer (implies unsafe)
let buf_ptr: *mut u8;    // mutable raw pointer (implies unsafe)

// CHANNEL/SOCKET naming
let fd: RawFd;           // file descriptor (opaque OS handle)
let sock: TcpStream;     // typed OS socket abstraction
let conn: Connection;    // application-level connection

// KEY MATERIAL — naming signals security requirements
let key: [u8; 32];            // generic key
let session_key: SessionKey;  // typed for zeroize on drop
let ikm: [u8; 32];            // input key material (HKDF terminology)
let prk: [u8; 32];            // pseudorandom key (HKDF output)
let okm: [u8; 64];            // output key material

// STATE MACHINE variables
let state: ConnectionState;   // current state (enum)
let prev_state: ConnectionState; // for logging state transitions

// DURATION AND TIMEOUT
let timeout: Duration;        // typed duration, not raw integer
let deadline: Instant;        // absolute point in time
let elapsed: Duration;        // time that has passed
```

### The `_` Prefix in C — Private by Convention

In C, single underscore prefix signals "internal, not for public use":

```c
/* Public: documented, stable */
int  foo_connect(foo_ctx_t *ctx, const char *host);

/* Internal: undocumented, may change */
int  _foo_parse_addr(const char *host, struct sockaddr *out);
void _foo_log(int level, const char *fmt, ...);

/* System-reserved: never use in your code */
/* Double underscore or underscore+uppercase is RESERVED by C standard */
/* __attribute__, _Noreturn, _Static_assert, etc. */
```

In Rust, `_` prefix suppresses unused variable warnings:

```rust
let _unused = compute_something(); // result deliberately ignored
let _ = tx.send(msg);             // error deliberately ignored (anti-pattern!)
```

### Naming for Lifetimes — Signals in Rust Code

```rust
// Lifetime names encode the relationship between references:

// 'a — generic single lifetime (most common)
fn parse<'a>(data: &'a [u8]) -> Header<'a> { }

// 'buf — names the source buffer (more descriptive)
fn parse<'buf>(data: &'buf [u8]) -> Header<'buf> { }

// 'static — lives for entire program duration
fn error_message() -> &'static str { "connection refused" }

// 'self — tied to the struct lifetime (rarely written explicitly)
impl Session {
    fn key(&self) -> &[u8] { &self.key }
    // compiler infers: fn key<'self>(&'self self) -> &'self [u8]
}

// Named lifetimes in production code (example: zero-copy packet parser)
struct PacketView<'pkt> {
    header: &'pkt [u8],  // borrows from original packet buffer
    payload: &'pkt [u8], // borrows from same buffer
}
// The name 'pkt signals: these references live as long as the packet buffer.
```

---

## 15. Function Decomposition — How Real Projects Break Down Work

### The Single Responsibility Principle at Function Scale

Each function should have exactly one reason to change. In systems code,
this maps to: one function = one operation on one data structure.

```
GOOD decomposition:
─────────────────
parse_packet_header(buf: &[u8]) -> Result<Header>
validate_header(hdr: &Header) -> Result<()>
route_packet(hdr: &Header, map: &RouteMap) -> Option<NextHop>
forward_packet(pkt: &[u8], hop: NextHop, sock: &Socket) -> Result<()>

BAD decomposition (too much in one function):
─────────────────────────────────────────────
process_packet(buf: &[u8], sock: &Socket, map: &RouteMap) -> Result<()>
// Does everything: parse, validate, route, forward, log errors
// Untestable: must test all combinations together
// Unmaintainable: changes to routing logic risk breaking parsing
```

### The Actual Structure of a Production Rust Function

```rust
// Template for a well-structured production function:

/// Connects `ctx` to `host:port` using mTLS.
///
/// # Arguments
/// * `ctx`  - active session context (must be in `Initialized` state)
/// * `host` - hostname for SNI and certificate verification
/// * `port` - TCP port (1–65535)
///
/// # Returns
/// `Ok(())` on successful connection.
///
/// # Errors
/// * `Error::DnsResolution` — host does not resolve
/// * `Error::TlsHandshake` — TLS negotiation failed (includes reason)
/// * `Error::Timeout` — connection exceeded `ctx.config.connect_timeout`
///
/// # Panics
/// Never panics. All error conditions return `Err`.
#[instrument(skip(ctx), fields(host = %host, port = port))]  // tracing
pub async fn connect(
    ctx: &mut Context,
    host: &str,
    port: u16,
) -> Result<(), Error> {
    // 1. VALIDATE inputs before any I/O
    if port == 0 {
        return Err(Error::InvalidPort(port));
    }
    validate_hostname(host)?;  // returns Err for invalid hostnames

    // 2. DO THE WORK — structured, delegating to helpers
    let addr = resolve_host(host, port)
        .await
        .map_err(|e| Error::DnsResolution { host: host.to_owned(), source: e })?;

    let tcp_stream = tokio::net::TcpStream::connect(addr)
        .await
        .map_err(Error::Io)?;

    let tls_stream = tls_handshake(tcp_stream, host, &ctx.tls_config)
        .await
        .map_err(|e| Error::TlsHandshake { host: host.to_owned(), source: e })?;

    // 3. UPDATE STATE only after success
    ctx.stream = Some(tls_stream);
    ctx.state = State::Connected;

    // 4. EMIT TELEMETRY
    metrics::increment_counter!("connections.established");
    tracing::info!("connected to {}:{}", host, port);

    Ok(())
}
```

---

## 16. Error Handling Architecture — C vs Rust Patterns

### The Full Error Handling Architecture

```
C Error Architecture:
                              
Return value signals error:           errno or error struct holds detail:
                                      
int ret = foo_connect(ctx, host, port);
if (ret != 0) {
    // errno is set, or call foo_get_error(ctx)
    fprintf(stderr, "connect failed: %s\n", strerror(errno));
    return ret;  // propagate error code upward
}

Problem: error codes are integers. Callers can ignore them.
         No compiler enforcement. Silent failure is common.

─────────────────────────────────────────────────────────────────

Rust Error Architecture:
                              
┌─────────────────────────────────────────────────────────────┐
│                    Error Type Hierarchy                     │
│                                                             │
│   crate::Error  (top-level, what callers see)               │
│       │                                                     │
│       ├── IoError(std::io::Error)   ← wraps std errors      │
│       ├── TlsError(rustls::Error)   ← wraps dependency errs │
│       ├── ParseError(ParseError)    ← subsystem error       │
│       └── ConfigError(ConfigError)  ← subsystem error       │
│                                                             │
│   #[must_use] on Result<T, E>       ← compiler enforces     │
│   ? operator propagates             ← no silent failure     │
│   thiserror derives Display/Error   ← consistent formatting │
│   anyhow for applications           ← add context with .context()│
└─────────────────────────────────────────────────────────────┘
```

```rust
// src/error.rs — canonical error type structure

use thiserror::Error;

/// Top-level error type for this crate.
/// All public functions return Result<T, Error>.
#[derive(Debug, Error)]
pub enum Error {
    /// Network I/O failure. Contains the underlying OS error.
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    /// TLS handshake or record layer failure.
    #[error("TLS error connecting to {host}: {source}")]
    Tls {
        host: String,
        #[source]
        source: rustls::Error,
    },

    /// Packet parsing failed. Contains byte offset of failure.
    #[error("parse error at byte {offset}: {reason}")]
    Parse {
        offset: usize,
        reason: &'static str,
    },

    /// Connection pool exhausted.
    #[error("connection pool exhausted (limit: {limit})")]
    PoolExhausted {
        limit: usize,
    },
}

// For application binaries (not libraries), use anyhow:
// anyhow::Error is a heap-allocated type-erased error with backtrace.
// Libraries should NOT use anyhow as their return type.
// Binaries CAN use anyhow to collect errors from multiple library types.
```

---

## 17. Memory Management Architecture — C vs Rust

### The Four C Memory Ownership Patterns

Every C API uses one of these patterns. Knowing which one is the
first step to writing a correct Rust wrapper.

```
Pattern 1: CALLER ALLOCATES, CALLER FREES (stack/array pattern)
────────────────────────────────────────────────────────────────
// C API:
int foo_compute(const uint8_t *in, size_t in_len,
                uint8_t *out, size_t out_len); // caller provides output buffer

// Rust wrapper:
pub fn compute(input: &[u8]) -> Result<Vec<u8>, Error> {
    let mut output = vec![0u8; EXPECTED_OUTPUT_LEN]; // Rust allocates
    let ret = unsafe {
        foo_compute(input.as_ptr(), input.len(),
                    output.as_mut_ptr(), output.len())
    };
    if ret < 0 { return Err(Error::ComputeFailed(ret)); }
    output.truncate(ret as usize); // actual output length
    Ok(output)
}

Pattern 2: LIBRARY ALLOCATES, LIBRARY FREES (opaque context pattern)
──────────────────────────────────────────────────────────────────────
// C API:
foo_ctx_t *foo_ctx_new();   // library allocates
void       foo_ctx_free();  // library frees

// Rust wrapper: RAII with Drop (see FooContext above)

Pattern 3: LIBRARY ALLOCATES, CALLER FREES (transfer of ownership)
────────────────────────────────────────────────────────────────────
// C API:
char *foo_format_error(int code); // malloc'd string, caller must free()

// Rust wrapper:
pub fn format_error(code: i32) -> String {
    let raw = unsafe { foo_format_error(code) };
    if raw.is_null() { return String::from("unknown"); }
    // Convert to owned Rust string, then free the C allocation
    let s = unsafe { CStr::from_ptr(raw) }
        .to_string_lossy()
        .into_owned();
    unsafe { libc::free(raw as *mut libc::c_void) }; // must free with C's free()
    s
}

Pattern 4: STATIC STORAGE (no allocation, no free)
────────────────────────────────────────────────────
// C API:
const char *foo_version(void); // returns pointer to static string literal

// Rust wrapper:
pub fn version() -> &'static str {
    let raw = unsafe { foo_version() };
    // SAFETY: foo_version() returns a 'static string literal.
    //         It is valid for the entire program lifetime.
    unsafe { CStr::from_ptr(raw) }
        .to_str()
        .expect("C library version string is not valid UTF-8")
}
```

### Rust Allocator Interaction with C

```
Rust's global allocator (jemalloc by default in some configs, System otherwise)
is SEPARATE from C's allocator (malloc/free in libc).

                    ┌─────────────────────┐
Rust code:          │    Rust allocator   │  Box::new(), Vec::new(), String::new()
                    │  (System or custom) │
                    └─────────────────────┘
                              ≠
                    ┌─────────────────────┐
C code:             │    C allocator      │  malloc(), calloc(), realloc(), free()
                    │    (ptmalloc/glibc) │
                    └─────────────────────┘

RULE: Memory allocated by one must be freed by the other.
      NEVER call Box::from_raw() on malloc'd memory.
      NEVER call free() on Box-allocated memory.
      NEVER call Rust's allocator on memory from a C pool.
```

---

## 18. Concurrency Architecture — C Pthreads vs Rust Ownership

### C Threading Model — All Manual

```c
/* C concurrency: programmer is responsible for everything */

/* Shared state: protected by mutex */
static pthread_mutex_t g_conn_lock = PTHREAD_MUTEX_INITIALIZER;
static int             g_conn_count = 0;

/* Must lock before access, unlock after — no enforcement */
void increment_connections(void) {
    pthread_mutex_lock(&g_conn_lock);
    g_conn_count++;   // critical section
    pthread_mutex_unlock(&g_conn_lock);
}

/* Condition variable for signaling */
static pthread_cond_t  g_conn_ready = PTHREAD_COND_INITIALIZER;
```

### Rust Threading Model — Enforced by Type System

```rust
// Rust concurrency: compiler enforces sharing rules via Send + Sync

// Send: T can be TRANSFERRED to another thread
// Sync: T can be SHARED (referenced) from multiple threads simultaneously

// Arc<T>: atomically reference-counted shared ownership (T: Send + Sync)
// Mutex<T>: guards T, provides interior mutability (T: Send makes Mutex<T>: Send+Sync)

// Compiler enforces:
// - You cannot share &mut T across threads (would be data race)
// - You cannot send *mut T across threads unless you explicitly impl Send
// - Mutex<T> gives you MutexGuard<T>, which holds the lock; lock releases when guard drops

use std::sync::{Arc, Mutex};

// Thread-safe connection counter:
let conn_count = Arc::new(Mutex::new(0usize));

// Clone Arc for each thread — cheap atomic reference count bump
let count_for_thread = Arc::clone(&conn_count);

std::thread::spawn(move || {
    // move: takes ownership of count_for_thread
    let mut count = count_for_thread.lock().unwrap();
    *count += 1;
    // MutexGuard<usize> dropped here: lock released automatically
});

// WON'T COMPILE:
// let shared_ref: &mut usize = ...;
// std::thread::spawn(move || { *shared_ref += 1 });
// ERROR: `&mut usize` cannot be sent between threads safely
//        the trait `Send` is not implemented for `&mut usize`
```

### The `Send + Sync` Rules for FFI Types

```rust
// C types are NOT automatically Send or Sync.
// You must manually assert thread safety based on C library documentation.

pub struct FooContext {
    inner: NonNull<FooCtx>,
}

// DEFAULT: FooContext is NEITHER Send NOR Sync (raw pointer, unknown safety)
// The compiler is conservative: if you hold a raw pointer, it can't be sent.

// TO MAKE IT Send (can be transferred to another thread):
// Assert: the C library is safe to use from a different thread as long as
//         only one thread uses it at a time (no concurrent calls).
unsafe impl Send for FooContext {}

// TO MAKE IT Sync (can be shared across threads):
// Assert: the C library's functions are safe to call concurrently from
//         multiple threads without additional locking. This requires
//         explicit documentation in the C library.
// DON'T DO THIS unless you are certain. Incorrect Sync is a data race.
// If unsure: wrap in Mutex<FooContext> instead.
unsafe impl Sync for FooContext {} // ONLY if C library is documented thread-safe
```

---

## 19. Testing Architecture — How Real Projects Structure Tests

### The Three Test Levels in Rust

```
Level 1: UNIT TESTS — in the same file as the code
  #[cfg(test)] mod tests { }
  Location: inside src/crypto/aes.rs
  Access:   private functions (same module)
  Speed:    milliseconds
  Purpose:  one function, one property

Level 2: INTEGRATION TESTS — in tests/ directory
  Location: tests/tls_handshake.rs
  Access:   only public API (acts as external crate)
  Speed:    seconds
  Purpose:  multiple components working together

Level 3: PROPERTY TESTS / FUZZING — randomized input
  Location: tests/fuzz/ or fuzz/
  Tooling:  cargo-fuzz, proptest, arbitrary
  Speed:    hours (CI) or continuous
  Purpose:  find edge cases in parsers, crypto, data structures
```

### Unit Test Structure in C — The Test Harness Pattern

Real C projects use test harnesses because C has no built-in test framework.

```c
/* test/test_crypto.c — C unit test pattern */

#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "crypto/sha256.h"  // unit under test

/* Test helper macros */
#define TEST_ASSERT(cond) \
    do { \
        if (!(cond)) { \
            fprintf(stderr, "FAIL: %s:%d: %s\n", __FILE__, __LINE__, #cond); \
            return -1; \
        } \
    } while(0)

#define TEST_ASSERT_MEM_EQ(a, b, len) \
    TEST_ASSERT(memcmp((a), (b), (len)) == 0)

/* One function per test case */
static int test_sha256_empty_input(void) {
    sha256_ctx_t ctx;
    uint8_t digest[32];

    /* Known answer test: SHA-256("") from FIPS 180-4 */
    static const uint8_t expected[32] = {
        0xe3, 0xb0, 0xc4, 0x42, /* ... */
    };

    sha256_init(&ctx);
    sha256_final(&ctx, digest);

    TEST_ASSERT_MEM_EQ(digest, expected, 32);
    return 0;  /* 0 = pass */
}

/* Test runner — enumerate all tests */
int main(void) {
    int pass = 0, fail = 0;

    #define RUN(test) \
        do { \
            if (test() == 0) { pass++; printf("PASS: " #test "\n"); } \
            else { fail++; printf("FAIL: " #test "\n"); } \
        } while(0)

    RUN(test_sha256_empty_input);
    /* ... more tests ... */

    printf("\n%d passed, %d failed\n", pass, fail);
    return fail > 0 ? 1 : 0;
}
```

### Rust Integration Test — Realistic Structure

```rust
// tests/tls_connection_test.rs
// This is a separate crate. It can only use public API.

use my_lib::{Config, Context, Error};
use std::time::Duration;

// Test fixtures: shared setup
mod fixtures {
    pub fn test_config() -> super::Config {
        Config::builder()
            .connect_timeout(Duration::from_secs(5))
            .tls_verify(false)  // test only
            .build()
            .expect("test config should be valid")
    }
}

#[tokio::test]
async fn test_connect_to_localhost() {
    let config = fixtures::test_config();
    let mut ctx = Context::new(config);

    // This test requires a local TLS server.
    // In CI: start a test server in a fixture or use testcontainers.
    let result = ctx.connect("127.0.0.1", 4443).await;

    assert!(result.is_ok(), "connect failed: {:?}", result.err());
}

#[tokio::test]
async fn test_connect_wrong_port_returns_error() {
    let mut ctx = Context::new(fixtures::test_config());

    let result = ctx.connect("127.0.0.1", 0).await;

    assert!(matches!(result, Err(Error::InvalidPort(0))));
}
```

---

## 20. Documentation Architecture — Comments That Build Mental Models

### The Three Levels of Comments

Real projects distinguish between three kinds of comments:

```rust
//! (Module-level doc comment — what this module IS and WHY it exists)
//! 
//! # Key schedule for TLS 1.3
//!
//! Implements the key derivation schedule from RFC 8446, Section 7.1.
//! All key material is derived from a single input using HKDF (RFC 5869).
//! 
//! # Security Note
//! Key material is held in `Zeroizing<[u8; N]>` and is zeroed on drop.

/// (Item-level doc comment — what this function/struct DOES and HOW to use it)
///
/// Derives the traffic keys for a TLS 1.3 session.
///
/// Implements: RFC 8446 Section 7.3 "Traffic Key Calculation"
///
/// # Arguments
/// * `secret` - the [sender]_write_traffic_secret from the key schedule
/// * `cipher` - the negotiated cipher suite
///
/// # Returns
/// A key and IV suitable for AEAD encryption.
///
/// # Security
/// The returned key is valid only for the current epoch.
/// Advancing to the next epoch requires calling `derive_next_generation()`.
pub fn derive_traffic_keys(secret: &[u8], cipher: CipherSuite)
    -> Result<(AeadKey, IV), Error>
{ ... }

// (Inline comment — what this specific line DOES that isn't obvious)
// Expand label as per RFC 8446 §7.1: "tls13 " prefix is mandatory.
let label = format!("tls13 {}", label_str);
```

### The Safety Comment — Mandatory for Every unsafe Block

```rust
// Every unsafe block must have a SAFETY comment.
// No exceptions. The comment answers: why is this sound?

// SAFETY: `self.ptr` is guaranteed non-null (checked in constructor)
//         and the allocation is still live (held by this struct).
//         No other code can alias this pointer because FooCtx is !Sync.
let ctx_ref: &FooCtx = unsafe { &*self.ptr.as_ptr() };

// SAFETY: This transmute is safe because:
//         1. PacketHeader is #[repr(C)] with no padding
//         2. The source slice is exactly size_of::<PacketHeader>() bytes
//         3. All bit patterns are valid for PacketHeader (no bool, no enum)
//         4. The alignment of buf.as_ptr() is verified at entry to this function.
let hdr = unsafe { &*(buf.as_ptr() as *const PacketHeader) };
```

---

## 21. Connection Map — How Everything Ties Together

```
Open Source Project Architecture — Concept Lattice
────────────────────────────────────────────────────

FILE STRUCTURE
    │
    ├── enforces → DEPENDENCY DIRECTION (no upward deps)
    ├── encodes  → PUBLIC vs PRIVATE API boundary
    └── maps to  → MODULE SYSTEM (C: includes, Rust: mod/pub)

NAMING CONVENTIONS
    │
    ├── encode   → OWNERSHIP (new/into/as_/from_)
    ├── encode   → SAFETY LEVEL (unsafe prefix, _internal suffix)
    └── connect  → SUBSYSTEM PREFIX (ssl_*, foo_*, skb_*)

C IMPLEMENTATION INTERNALS
    │
    ├── translation units → COMPILATION MODEL
    ├── static functions  → ENCAPSULATION (C's only mechanism)
    ├── #include model    → TEXTUAL SUBSTITUTION (not scoped import)
    ├── memory segments   → STACK/HEAP/BSS/DATA/TEXT
    └── calling convention → ABI CONTRACT (extern "C" in Rust)

RUST FFI
    │
    ├── extern "C"     → CALLING CONVENTION BRIDGE
    ├── #[repr(C)]     → LAYOUT GUARANTEE (for C structs)
    ├── unsafe {}      → SAFETY BOUNDARY (explicit UB surface)
    ├── Drop trait     → RAII WRAPPER (automatic resource release)
    ├── Send/Sync      → THREAD SAFETY MARKERS (FFI types need manual impl)
    └── NonNull<T>     → NON-NULL POINTER (prevents null deref class of bugs)

-sys CRATE PATTERN
    │
    ├── separates  → RAW FFI from SAFE WRAPPER
    ├── uses       → build.rs + cc + bindgen
    ├── enforces   → SINGLE LINKER UNIT (links = "foo")
    └── examples   → libbpf-sys, openssl-sys, libssh2-sys

EBPF + RUST (aya)
    │
    ├── aya-ebpf   → IN-KERNEL: no_std, BPF verifier constraints
    ├── aya        → USERSPACE: load, pin, attach via bpf(2)
    ├── BTF/CO-RE  → TYPE INFORMATION for kernel-version portability
    └── maps       → SHARED MEMORY between kernel program and userspace

SECURITY IMPLICATIONS
    │
    ├── opaque pointer  → PREVENTS struct layout leakage
    ├── MaybeUninit     → PREVENTS reading uninitialized memory
    ├── Zeroizing<T>    → KEY MATERIAL zeroed on drop
    ├── NonNull<T>      → PREVENTS null pointer class of vulnerabilities
    └── Send/Sync bounds → PREVENTS data races on shared C state

ARCHITECTURE PATTERNS
    │
    ├── Layered stack   → TCP/IP, TLS, HTTP stacks
    ├── Hub-and-spoke   → Kubernetes controllers
    ├── Pipeline        → Tower middleware, TC egress
    └── Actor/channel   → eBPF event processing, tokio tasks
```

---

## Further Reading — Real Source Code to Study

| Project | What to Read | Why |
|---|---|---|
| `linux/kernel/bpf/verifier.c` | BPF verifier | Largest C state machine in the wild |
| `rustls/src/tls13/` | Key schedule | RFC → Rust type mapping |
| `tokio/src/runtime/` | Executor | Async runtime internals |
| `aya/src/programs/xdp.rs` | XDP attach | Netlink + FFI pattern |
| `libbpf-sys/build.rs` | Build script | vendored C compilation |
| `openssl-sys/build/` | Multi-strategy build | pkg-config + vendor fallback |
| `crossbeam/src/queue/` | Lock-free queue | unsafe with invariants documented |
| `bytes/src/bytes.rs` | Shared buffer | Arc + raw ptr + atomics |

---

*End of Guide*

*Version: 1.0 | Covers: C project architecture, Rust project architecture,*
*C calling conventions, Rust FFI, bindgen, -sys crate pattern, eBPF/aya,*
*OpenSSL FFI, naming conventions, memory models, concurrency models,*
*testing architecture, documentation architecture.*
