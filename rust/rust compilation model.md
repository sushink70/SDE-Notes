**Summary:** Rust compilation is a multi-stage pipeline that enforces memory/concurrency safety before LLVM codegen, using borrow checking on MIR, monomorphization for zero-cost generics, and minimal runtime—resulting in safe, native binaries with C-level performance.

---

## End-to-End Rust Compilation: Systems Engineering View

The document you provided covers the pipeline well. I'll extend it with **production concerns, security implications, toolchain internals, and verification steps** relevant to systems work.

---

## Architecture: Toolchain Components (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                         DEVELOPER INPUT                          │
│  src/*.rs + Cargo.toml + build.rs + .cargo/config.toml         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                           CARGO                                  │
│  • Dependency resolution (registry.crates.io + git)             │
│  • Build graph construction (toposort)                          │
│  • Feature unification                                          │
│  • Fingerprinting (incremental builds)                          │
│  • Build script execution (build.rs → OUT_DIR)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                          RUSTC                                   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ FRONT-END (per crate)                                    │   │
│  │  lex → parse → macro-expand → name-resolve → HIR        │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                         │
│  ┌─────────────────────▼───────────────────────────────────┐   │
│  │ TYPE SYSTEM                                              │   │
│  │  type-check → trait-solve → lifetime-inference          │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                         │
│  ┌─────────────────────▼───────────────────────────────────┐   │
│  │ MIR (Mid-level IR)                                       │   │
│  │  borrow-check → drop-elaborate → MIR-opts               │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                         │
│  ┌─────────────────────▼───────────────────────────────────┐   │
│  │ MONOMORPHIZATION + CODEGEN                               │   │
│  │  instantiate-generics → LLVM-IR-gen                      │   │
│  └─────────────────────┬───────────────────────────────────┘   │
└────────────────────────┼───────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LLVM BACKEND                              │
│  opt passes → instruction-selection → register-alloc → emit-obj │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                          LINKER                                  │
│  ld.lld / mold / ld → .rlib + libstd + libc → ELF/PE/Mach-O    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                    NATIVE BINARY
```

---

## Deep Dive: Critical Stages for Systems Engineers

### Stage 0: Cargo's Dependency Resolution (Supply Chain)

**What happens:**
```bash
cargo build
```

1. **Index fetch** from `crates.io-index` (git repo)
2. **Version solving** (uses `pub-grub` algorithm)
3. **Crate download** from `static.crates.io`
4. **Checksum verification** (SHA256 in `Cargo.lock`)

**Security concerns:**
- **Typosquatting**: `tokio` vs `tokio-core` vs `tokioo`
- **Dependency confusion**: private vs public crate names
- **Malicious build.rs**: arbitrary code execution at build time
- **Transitive deps**: 1 direct dep can pull 50+ indirect deps

**Mitigations:**
```bash
# Audit dependencies
cargo install cargo-audit
cargo audit

# Check for yanked crates
cargo install cargo-deny
cargo deny check

# Vendor dependencies (airgap builds)
cargo vendor

# Lock dependencies
cargo update --locked  # CI should use this

# Review build scripts
find target/debug/build -name "build-script-build"
```

**Failure mode:**
```bash
# Dependency solver can fail on conflicting semver
# Example: crate-a needs tokio 1.0, crate-b needs tokio 0.2
error: failed to select a version for `tokio`.
```

**Alternative:** Use `cargo-chef` for Docker layer caching in CI:
```dockerfile
FROM rust:1.75 as planner
WORKDIR /app
RUN cargo install cargo-chef
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM rust:1.75 as builder
WORKDIR /app
RUN cargo install cargo-chef
COPY --from=planner /app/recipe.json recipe.json
RUN cargo chef cook --release --recipe-path recipe.json
COPY . .
RUN cargo build --release
```

---

### Stage 3: Macro Expansion (Code Generation Attack Surface)

**What happens:**
Procedural macros are **compiled Rust binaries** executed during compilation.

```bash
# See where proc-macros live
ls -la target/debug/build/*/out/
```

**Security concerns:**
- **Arbitrary code execution**: proc-macros run with your user permissions
- **Network access**: nothing stops a proc-macro from phoning home
- **File system access**: can read secrets, modify files

**Verification:**
```bash
# Expand macros to see generated code
cargo expand > expanded.rs

# Or per-file
cargo expand --lib
cargo expand --bin my-binary
```

**Example: Inspect a derive macro**
```rust
// src/main.rs
use serde::Deserialize;

#[derive(Deserialize)]
struct Config {
    host: String,
    port: u16,
}
```

```bash
cargo expand
# You'll see generated impl for Deserialize
```

**Threat model:**
| Threat | Impact | Mitigation |
|--------|--------|------------|
| Malicious proc-macro reads ~/.ssh | Credential theft | Sandbox builds (bubblewrap, gvisor) |
| Proc-macro exfiltrates source code | IP theft | Airgap CI, vendor deps |
| Supply chain compromise | RCE in build | Pin deps, audit, SBOMs |

---

### Stage 5: Borrow Checking (Why Rust Wins for Systems)

**What it prevents:**
```rust
// Use-after-free (CVE-common in C/C++)
let r;
{
    let x = 5;
    r = &x;
}
println!("{}", r);  // ❌ Compile error: x doesn't live long enough
```

```rust
// Data race (CVE-common in concurrent systems)
let mut data = vec![1, 2, 3];
let r1 = &data;
let r2 = &mut data;  // ❌ Compile error: cannot borrow as mutable
```

**Real-world impact:**
- **70% of CVEs in Chrome/Firefox** are memory safety issues
- Rust's borrow checker catches these **at compile time**
- Zero runtime cost (unlike GC or reference counting)

**See borrow checker in action:**
```bash
# Show MIR with borrow checking annotations
cargo rustc -- -Zunpretty=mir-cfg > mir.dot
dot -Tpng mir.dot > mir.png
```

**Limitations:**
- **False positives**: Sometimes valid code rejected (rare in modern Rust)
- **Workarounds**: `Rc<RefCell<T>>` (runtime borrow checking)
- **Unsafe escape hatch**: `unsafe { ... }` (use sparingly)

---

### Stage 8: Monomorphization (Binary Size vs Performance)

**What happens:**
```rust
fn process<T: Display>(item: T) { println!("{}", item); }

fn main() {
    process(42_i32);
    process("hello");
    process(3.14_f64);
}
```

**Compiler generates:**
```
process_i32
process_str
process_f64
```

**Tradeoff:**
| Approach | Binary Size | Runtime Perf | Rust Uses |
|----------|-------------|--------------|-----------|
| Monomorphization | Large | Fast | ✓ |
| Dynamic dispatch (`dyn Trait`) | Small | Slower | Sometimes |
| Generic code in IR (Go) | Medium | Medium | ✗ |

**Measure binary size:**
```bash
cargo build --release
ls -lh target/release/my-binary

# Break down by crate
cargo install cargo-bloat
cargo bloat --release -n 20

# Check for duplicate generic instantiations
cargo install twiggy
twiggy top target/release/my-binary

# Strip symbols
strip target/release/my-binary
```

**Alternatives for size-critical systems:**
```toml
[profile.release]
opt-level = "z"      # Optimize for size
lto = true           # Link-time optimization
codegen-units = 1    # Better optimization, slower compile
panic = "abort"      # Don't unwind, save unwinding tables
strip = true         # Strip symbols (Rust 1.59+)
```

**Embedded systems:**
```bash
# Minimal binary (no_std)
cargo build --release --target thumbv7em-none-eabihf
```

---

### Stage 9: LLVM IR (Interop & Inspection)

**Generate LLVM IR:**
```bash
cargo rustc --release -- --emit=llvm-ir
cat target/release/deps/*.ll
```

**Why this matters:**
- **FFI debugging**: See how `extern "C"` functions are lowered
- **Performance tuning**: Verify inlining, vectorization
- **Compiler bugs**: Compare IR vs assembly for weird behavior

**Example: Check SIMD codegen**
```rust
// src/lib.rs
pub fn sum(data: &[f32]) -> f32 {
    data.iter().sum()
}
```

```bash
cargo rustc --release -- --emit=llvm-ir -C target-cpu=native
grep -A 10 "define.*sum" target/release/deps/*.ll
# Look for vector instructions: fadd <4 x float>
```

**Check assembly:**
```bash
cargo rustc --release -- --emit=asm
cat target/release/deps/*.s
# Verify SIMD: vaddps, vmulps, etc.
```

---

### Stage 11: Linking (Static vs Dynamic, musl vs glibc)

**Default (glibc, dynamic):**
```bash
cargo build --release
ldd target/release/my-binary
#   linux-vdso.so.1
#   libgcc_s.so.1 => /lib/x86_64-linux-gnu/libgcc_s.so.1
#   libpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0
#   libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
```

**Static with musl (container-friendly):**
```bash
rustup target add x86_64-unknown-linux-musl
cargo build --release --target x86_64-unknown-linux-musl
ldd target/x86_64-unknown-linux-musl/release/my-binary
#   not a dynamic executable
```

**Why musl for production:**
- **No libc version mismatches** (deploy anywhere)
- **Smaller attack surface** (no dynamic loader exploits)
- **Reproducible builds** (no host libc dependency)

**Tradeoffs:**
| Aspect | glibc | musl |
|--------|-------|------|
| Performance | Faster (optimized malloc) | Slower (~10% avg) |
| DNS resolution | nsswitch.conf | Static only |
| Compatibility | Full POSIX | Mostly POSIX |
| Binary size | Smaller (dynamic) | Larger (static) |

**Verify static linking:**
```bash
file target/x86_64-unknown-linux-musl/release/my-binary
# ELF 64-bit LSB executable, statically linked, not stripped

readelf -d target/x86_64-unknown-linux-musl/release/my-binary
# (empty - no dynamic section)
```

**Cross-compile for Alpine/Kubernetes:**
```bash
# .cargo/config.toml
[target.x86_64-unknown-linux-musl]
linker = "x86_64-linux-musl-gcc"

cargo build --release --target x86_64-unknown-linux-musl
```

---

## Security: Threat Model & Mitigations

### Build-time Threats

| Threat | Vector | Mitigation |
|--------|--------|------------|
| Malicious dependency | Compromised crate | `cargo-audit`, pin deps, private registry |
| Supply chain attack | Typosquatting | `cargo-deny` allow-list |
| Build script RCE | `build.rs` arbitrary code | Sandbox builds (Docker, gvisor) |
| Credential theft | Proc-macro reads ~/.ssh | Ephemeral build envs |
| MITM download | crates.io compromise | Checksum verification (automatic) |

**Implement:**
```bash
# CI pipeline (GitHub Actions example)
- name: Audit dependencies
  run: |
    cargo install cargo-audit
    cargo audit --deny warnings

- name: Check licenses
  run: |
    cargo install cargo-deny
    cargo deny check licenses

- name: Verify Cargo.lock
  run: |
    cargo update --locked
    git diff --exit-code Cargo.lock
```

### Runtime Threats

| Threat | Rust Protection | Additional Steps |
|--------|----------------|-------------------|
| Memory corruption | Borrow checker | Use `#![forbid(unsafe_code)]` |
| Integer overflow | Debug: panic, Release: wrap | Use `checked_*`, `saturating_*` |
| Panic unwinding | Stack traces leak info | `panic = "abort"` in release |
| Format string bugs | Type-safe formatting | N/A (impossible in safe Rust) |
| Concurrency bugs | `Send`/`Sync` enforcement | Audit `unsafe` blocks |

**Forbid unsafe in application code:**
```rust
// src/main.rs
#![forbid(unsafe_code)]

fn main() {
    // All code must be safe Rust
}
```

**Allow unsafe only in audited modules:**
```rust
// src/ffi.rs
#![allow(unsafe_code)]

// Centralize unsafe, document invariants
/// SAFETY: ptr must be non-null and aligned
pub unsafe fn from_raw(ptr: *mut Data) -> Box<Data> {
    Box::from_raw(ptr)
}
```

---

## Testing, Fuzzing, Benchmarking

### Unit Tests
```bash
cargo test
cargo test --release  # Test optimized code
cargo test -- --nocapture  # Show println! output
```

### Integration Tests
```bash
# tests/integration_test.rs
#[test]
fn test_real_workflow() {
    // ...
}

cargo test --test integration_test
```

### Fuzzing (Find Undefined Behavior)
```bash
cargo install cargo-fuzz

cargo fuzz init
cargo fuzz add my_target

# fuzz/fuzz_targets/my_target.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let _ = my_crate::parse(data);
});

cargo fuzz run my_target -- -max_total_time=300
```

**Check for UB with Miri:**
```bash
rustup component add miri
cargo miri test
```

### Benchmarking
```bash
cargo install cargo-criterion

# benches/my_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn bench_parse(c: &mut Criterion) {
    c.bench_function("parse", |b| b.iter(|| {
        my_crate::parse(black_box(b"test data"))
    }));
}

criterion_group!(benches, bench_parse);
criterion_main!(benches);

cargo criterion
```

---

## Production Rollout & Rollback

### Build Artifacts
```bash
# Reproducible builds (WIP in Rust)
cargo build --release --target x86_64-unknown-linux-musl

# Generate SBOM (Software Bill of Materials)
cargo install cargo-sbom
cargo sbom > sbom.json

# Sign binary
gpg --detach-sign target/release/my-binary
```

### Deployment
```bash
# Kubernetes sidecar pattern
kubectl apply -f deploy.yaml

# Rollout
kubectl rollout status deployment/my-app

# Rollback
kubectl rollout undo deployment/my-app
```

### Observability
```rust
// Use tracing for structured logging
use tracing::{info, instrument};

#[instrument]
fn process_request(req: &Request) -> Result<Response> {
    info!(request_id = %req.id, "processing");
    // ...
}

fn main() {
    tracing_subscriber::fmt::init();
    // ...
}
```

**Export metrics:**
```rust
use prometheus::{IntCounter, Registry};

let counter = IntCounter::new("requests_total", "Total requests").unwrap();
registry.register(Box::new(counter.clone())).unwrap();

// In request handler
counter.inc();
```

---

## Failure Modes & Recovery

### Compilation Failures

**Out of memory:**
```bash
# Reduce codegen-units (uses more RAM)
CARGO_BUILD_JOBS=1 cargo build --release
```

**Incremental compilation corruption:**
```bash
rm -rf target/debug/incremental
cargo clean
cargo build
```

**Proc-macro incompatibility:**
```bash
# Update dependencies
cargo update
# Or vendor and patch
cargo vendor
```

### Runtime Failures

**Panic in production:**
```rust
use std::panic;

fn main() {
    panic::set_hook(Box::new(|panic_info| {
        eprintln!("PANIC: {}", panic_info);
        // Send to error tracking service
    }));
    // ...
}
```

**OOM killer:**
```bash
# Set memory limits in systemd
MemoryMax=512M
MemoryHigh=400M
```

---

## Next 3 Steps

1. **Audit your dependency tree** (today):
   ```bash
   cargo install cargo-audit cargo-deny
   cargo audit
   cargo tree
   cargo deny init
   cargo deny check
   ```

2. **Set up reproducible, sandboxed builds** (this week):
   - Vendor dependencies: `cargo vendor`
   - Use musl target for static binaries
   - Run builds in ephemeral containers (GitHub Actions, GitLab CI)
   - Generate and store SBOMs

3. **Instrument your binaries for production** (this sprint):
   - Add `tracing` for structured logs
   - Integrate `prometheus` or `opentelemetry` metrics
   - Set up fuzzing in CI with `cargo-fuzz`
   - Run `cargo-miri` in CI to catch UB

**References:**
- Rust compilation model: https://rustc-dev-guide.rust-lang.org/
- MIR optimizations: https://github.com/rust-lang/rust/tree/master/compiler/rustc_mir_transform
- Security: https://anssi-fr.github.io/rust-guide/
- Supply chain: https://github.com/rustsec/rustsec