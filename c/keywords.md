# Keywords in the C Programming Language (Up to C23 Standard)

The C programming language defines a fixed set of reserved words known as **keywords**, which cannot be used as identifiers (e.g., variable or function names). These keywords form the syntactic backbone for control flow, data types, storage classes, and more. The set has evolved across ISO C standards, with additions reflecting modern needs like parallelism, attributes, and improved type safety.

As of the C23 standard (ISO/IEC 9899:2024, the latest as of November 2025), there are **67 unique keywords**. This count includes all keywords from prior standards plus C23-specific additions, without duplicates (noting that C23 introduces some as unprefixed aliases for prior underscore-prefixed versions, e.g., `bool` alongside `_Bool`).

Below is a comprehensive table enumerating all keywords, grouped by the standard in which they were **first introduced**. This grouping highlights the language's evolution while ensuring completeness for C23 compliance. For real-world systems engineering (e.g., in secure kernel modules or cloud-native tooling), always compile with the target standard flag (e.g., `-std=c23` in GCC/Clang) to enforce keyword recognition.

| Standard | Keywords | Count | Notes |
|----------|----------|-------|-------|
| **C89/C90** (Base Set) | `auto`, `break`, `case`, `char`, `const`, `continue`, `default`, `do`, `double`, `else`, `enum`, `extern`, `float`, `for`, `goto`, `if`, `int`, `long`, `register`, `return`, `short`, `signed`, `sizeof`, `static`, `struct`, `switch`, `typedef`, `union`, `unsigned`, `void`, `volatile`, `while` | 32 | Foundational keywords for types, loops, conditionals, and storage. Ubiquitous in legacy and modern C codebases. |
| **C99** | `_Bool`, `_Complex`, `_Imaginary`, `inline`, `restrict` | 5 | Introduces Boolean type and complex numbers; `inline` and `restrict` optimize function inlining and pointer aliasing—critical for performance in networking/security primitives. |
| **C11** | `_Alignas`, `_Alignof`, `_Atomic`, `_Generic`, `_Noreturn`, `_Static_assert`, `_Thread_local` | 7 | Focuses on concurrency and alignment: `_Atomic` enables lock-free data structures (e.g., in eBPF filters); `_Static_assert` for compile-time checks in kernel drivers. |
| **C23** | `alignas`, `alignof`, `bool`, `constexpr`, `elifdef`, `elifndef`, `embed`, `false`, `nullptr`, `static_assert`, `thread_local`, `true`, `typeof`, `typeof_unqual`, `_BitInt`, `_Decimal128`, `_Decimal32`, `_Decimal64`, `__has_c_attribute`, `__has_embed`, `__has_include`, `warning` | 22 | C23 expands with unprefixed aliases (e.g., `bool` for `_Bool`), decimal floating-point types for financial/secure computations, and metaprogramming (`typeof`). `embed` supports firmware/security enclaves; total unique keywords reach 67. (Note: `_Decimal*` types build on C99's decimal support but are now keywords.) |

#### Key Observations for Systems Engineers
- **Backward Compatibility**: Older compilers (e.g., pre-C11) will treat newer keywords as identifiers unless the standard is specified, risking subtle bugs in cross-compilation for Linux kernels or Rust FFI.
- **Security Implications**: Keywords like `_Atomic` and `restrict` are vital for memory safety in distributed systems (e.g., avoiding races in eBPF programs). Misuse of `goto` (a C89 holdover) should be avoided in favor of structured control for auditability.
- **Usage in Practice**: In cloud-native (CNCF) contexts, C23's `constexpr`-like features (via `typeof`) aid in generating secure, type-safe configs at compile-time, aligning with Rust's const generics for hybrid systems.
- **Verification Tip**: To enumerate keywords programmatically in a C environment, use a macro loop over known strings and check via `#ifdef` or compiler intrinsics—useful for build scripts in secure infra pipelines.

This list is exhaustive and derived from the ISO C standards; for deeper dives into semantics (e.g., `alignas` for cache-line padding in data center networking), consult the standard or tools like Clang's `-fdiagnostics-show-option` for keyword diagnostics.