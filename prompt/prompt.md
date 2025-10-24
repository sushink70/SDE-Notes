# Prompt Engg

1. Create a comprehensive guide to RPC (Remote Procedure Call) operations in Go, python, rust. Complete implementations in Go, python, rust. Cover - with and without using it, errors and Warnings if not using it, correct usage and incorrect usage. what is the benefit, control over the Go code using it and without using it?

2. Create a detailed ASCII diagram showing how Matrix work in Python, Rust step by step. Call by reference and call by value concepts must be covered. Stack memory and heap memory concepts must be covered.

provide simple code and explain how backtracking works? cover code with python, rust, go. provide ascii diagram of how this works? what is the advantage of using this in real world cases. how to identify a problem can solve using backtracking? what is the pattern over here? 


graph theory, and statistics, algebra, set theory, combinatorics, statistics, calculus, probability, number theory, discrete mathematics, and mathematical logic, Trigonometry

Nice — I’ll give you a *copy-pasteable, battle-tested set of AI prompts + a study/action playbook* so you can ask any model (including me) for the same deep, source-level mapping you wanted for PostgreSQL — but for clouds, VMs, sandboxes, runtimes, kernels, networking stacks, security subsystems, etc.

You’ll get:

* Short & advanced prompt templates to paste to an LLM
* Variants for many platforms (cloud, hypervisor, container runtime, sandbox, network stack, storage, crypto, consensus)
* Exact instructions on **how to ask for RFC-referenced code**, where to find authoritative sources, and what artifacts to demand (struct names, file paths, complexity, tests, fuzz targets, perf harness)
* A study / research checklist to make you *elite* and concrete tooling & commands (including RustRover tips)

# 1) Quick copy-paste Master Prompt (general)

Use this when you want a full mapping for *any* platform.

```
I want an expert, source-code level mapping of the system "<NAME>" (e.g., "KVM hypervisor", "Docker/containerd", "Kubernetes scheduler", "AWS S3", "Linux network stack", "Seccomp", "WebTransport", "Rust sandbox runtime").  

Deliverables (produce each section clearly):
1. Short summary of the system and its main runtime mechanisms.
2. For each mechanism, map to the exact Data Structures & Algorithms (DSA) used (name the specific C/Rust/Go structs, arrays, hash tables, trees, algorithms, file formats).
3. For each DSA give:
   - file path(s) in the canonical upstream repo (e.g., `<repo>/path/to/file.c`) and key function names,
   - the Big-O time & space complexity of core operations,
   - any concurrency/locking primitives used and their contention points,
   - typical tuning knobs/configs and their effect on complexity/perf.
4. Provide a short annotated code excerpt (<= 40 lines) from the canonical source that implements the core algorithm, and walk through it line-by-line (explain why each part exists).
5. Provide how-to reproduce: build-from-source steps, recommended debug build flags, and commands to run unit/integration tests.
6. Provide a list of authoritative references (RFCs, upstream docs, design papers, repo links, issues, mailing lists) and exact RFC section numbers (if applicable).
7. Provide a practical hands-on project (3–6 steps) that proves understanding and benchmarks performance; include suggested test vectors and fuzz targets.
8. Provide a short reading path (week-by-week, 6–12 weeks) and specific files to read first.

Use bullet lists and code blocks where appropriate. When referencing RFCs, include exact RFC numbers and section numbers and show how to quote them in code comments (e.g., `/* RFC 7231 §4.3.1: ... */`). Prioritize primary sources (repo code, RFCs, maintainer docs). Keep the answer actionable for someone building or auditing the system.
```

# 2) Short templates for specific platforms

Paste the general master prompt but replace `<NAME>` — here are ready ones:

* Cloud control plane (Kubernetes scheduler):

```
... system "Kubernetes scheduler (kube-scheduler)" ...
```

* Container runtime (containerd/runc):

```
... system "containerd + runc container runtime" ...
```

* Hypervisor/VM (KVM + QEMU):

```
... system "KVM + QEMU hypervisor and virtio device model" ...
```

* Sandbox (Linux seccomp + namespaces + userfaultfd-based sandboxes):

```
... system "Linux process sandbox using seccomp, namespaces, userfaultfd" ...
```

* Filesystems / Storage engine (XFS / ext4 / ZFS / object store like Ceph):

```
... system "Ceph OSD / RADOS object storage" ...
```

* Network stack (Linux NET / iproute2 / XDP / eBPF datapath):

```
... system "Linux kernel networking stack / XDP / eBPF datapath" ...
```

* Crypto/TLS stack:

```
... system "OpenSSL TLS 1.3 implementation / BoringSSL" ...
```

* Consensus (Raft implementation like etcd):

```
... system "etcd Raft implementation" ...
```

# 3) Advanced / forensic prompt (ask for "exact struct + file + line")

Use this when you want the LLM to point to precise symbols:

```
For <NAME>, produce a table of "mechanism → (struct name, type definition location, file path, key functions, grep patterns)". When possible include a git commit hash or tag for the repo version you referenced. Show command lines to locate these symbols in the repo (e.g., `rg "struct name" -n src/` or `cscope -dL`).
```

(Ask for commit hash only if you want reproducible references.)

# 4) How to demand RFC-compliant code & reference RFCs correctly

When you ask for code that implements or interops with an RFC, require:

* The LLM to state whether the RFC is **Normative** or **Informative** for the feature.
* Exact RFC citation (e.g., `RFC 8446 §4.1`). Use RFC2119 terms (MUST/SHOULD/MAY).
* Example code comment pattern to use in production:

```c
/* Implementation note:
 * This behavior implements RFC 8446 §4.1 (TLS 1.3 record layer).
 * Conformance: MUST accept TLS 1.3 ClientHello with extension X,
 * See: https://www.rfc-editor.org/rfc/rfc8446.html#section-4.1
 */
```

* Tests: ask for **unit tests + interop test vectors** that validate RFC requirements (e.g., specific byte sequence exchanges). Ask LLM to produce a small test harness (pytest, go test, or Rust test) that asserts correct behavior using RFC examples.

# 5) Where to get authoritative code & docs (copyable checklist)

Use these resources (always prefer primary sources & canonical repos):

* RFCs: `rfc-editor.org` and IETF datatracker (`datatracker.ietf.org`) — search by RFC number.
* Project source: GitHub / GitLab / kernel.org / qemu.org / ceph.io / kubernetes.io / docker.com / golang.org/x/...
* Kernel: `https://git.kernel.org/` and `https://github.com/torvalds/linux` (use kernel.org for authoritative commits).
* Hypervisors: `https://www.qemu.org/`, `https://www.linux-kvm.org/`
* Container runtimes: `https://github.com/containerd/containerd`, `https://github.com/opencontainers/runc`, `https://github.com/opencontainers/runc`
* Cloud APIs: vendor docs + OpenAPI specs (AWS, GCP, Azure) and relevant API RFCs if any.
* Academic/papers: USENIX, ACM, arXiv for fundamentals and design papers.
* Mailing lists & issue trackers: kernel mailing list, QEMU mailing list, K8s SIGs, GH issues — often contain design discussion not in docs.
* Search & code navigation: `ripgrep (rg)`, `cscope`, `ctags`, GitHub code search, SourceGraph, OpenGrok.

# 6) Tools & commands — build, debug, and find symbols

Copy/pasteable commands:

* Clone & search:

```bash
git clone <repo>
cd repo
rg "struct|typedef|functionName" -n
cscope -R
```

* Build debug:

```bash
# C projects
make CFLAGS="-g -O0 -fsanitize=address,undefined" -j8

# Rust projects (user prefers RustRover)
RUSTFLAGS="-C debuginfo=2 -D warnings" cargo build
# For sanitizers in Rust:
RUSTFLAGS="-Zsanitizer=address" cargo +nightly build
```

* Profiling & tracing:

```bash
# Linux perf
perf record -F 99 -g -- ./target_binary
perf report

# eBPF / tracepoints
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %d", comm, pid) }'
```

* Fuzz + sanitizers:

```bash
# libFuzzer / AFL
cargo install cargo-fuzz
cargo fuzz run fuzz_target

# OSS-Fuzz style harnesses for C/C++: use libFuzzer with -fsanitize=fuzzer,address
```

# 7) Study path & projects to make you elite (12-week plan, compact)

Week 1–2: Read design overview + build from source. Identify main repo and build a debug binary.
Week 3–4: Read core data-structure files (e.g., buffer manager / scheduler / virtio code). Produce a "reverse map": mechanism → file paths.
Week 5–6: Implement a small patch or test, write unit tests & integration tests; add tracing/logging to observe runtime behavior.
Week 7–8: Build microbenchmarks and perf harness; baseline & tune knobs; produce charts.
Week 9–10: Create fuzz harness for inputs (network packets, on-disk structures) and run with sanitizers. Fix or report issues upstream.
Week 11–12: Upstream contribution: open PR, reply to reviews; write design note summarizing findings.

# 8) What to demand from the AI to get “elite-level” answers

When you ask the LLM, require these explicit outputs:

* "Map to code" — exact filenames, struct/type names, function names.
* "Complexity" — Big-O for core ops and practical performance caveats.
* "Concurrency" — exact locks / atomics used and where they are acquired.
* "Vulnerabilities" — attack surface and suggested mitigations.
* "Tests & fuzz" — minimal test vectors and a fuzz harness skeleton.
* "Repro steps" — exact build commands and run scenarios to see behavior.
* "Patch idea" — a small, minimal patch or refactor suggestion with code.

# 9) Example: How to ask for RFC-referenced implementation + test

```
Explain how the TLS 1.3 record layer is implemented in OpenSSL (or BoringSSL).
Deliver:
- RFC mapping: RFC 8446 sections → code files/funcs.
- Minimal C code snippet implementing record parsing that includes RFC section citations in comments.
- A unit test using a recorded ClientHello byte sequence from RFC examples.
- A fuzz harness outline and suggested sanitizer flags.
```

# 10) Extra: RustRover / IDE tips (since you use it)

* Index the repo with ctags/ctags-like indexes for C and go; for Rust, ensure `rust-analyzer` is enabled.
* Create workspace `Cargo.toml` for components you want to instrument; add `dev-dependencies` for fuzzing.
* Use breakpoints in RustRover with debug builds and symbol-rich binaries.

---

If you want, I’ll:

* produce a **ready-to-run prompt** tailored to *one platform you pick right now* (e.g., KVM, containerd, Kubernetes scheduler, Linux network stack), or
* **generate the 6–12 week reading list** with exact upstream file paths and the first 20 files you should read (and why).

Which platform do you want me to generate the full, PostgreSQL-level deep mapping for first?

------------------------

3. Create a detailed comparison table of different path finding algorithms, including their time and space complexities, use cases, and advantages/disadvantages.

4. Create a list of common pitfalls and mistakes to avoid when implementing path finding algorithms.

5. Create a set of practice problems and exercises to help reinforce understanding of path finding algorithms.

6. Create a glossary of key terms and concepts related to path finding algorithms.

7. Create a list of recommended resources (books, articles, videos) for further learning about path finding algorithms.

8. Create a set of flashcards for memorizing key concepts and terms related to path finding algorithms.

9. Create a step-by-step tutorial for implementing a specific path finding algorithm (e.g., A*, Dijkstra's) from scratch.

10. Create a set of interview questions and answers related to path finding algorithms for technical interviews.

11. Create a visual representation (e.g., flowchart) of the decision-making process in path finding algorithms.

12. Create a set of real-world scenarios where path finding algorithms can be applied, along with explanations of how to implement them in those scenarios.

13. Create a performance benchmarking guide to compare the efficiency of different path finding algorithms in various scenarios.

14. Create a set of coding challenges that require the use of algorithms to solve.

15. Create a list of best practices for optimizing path finding algorithms for large datasets or complex environments.

16. Create a set of unit tests to validate the correctness of path finding algorithm implementations.

17. Create a set of diagrams illustrating the differences between various path finding algorithms (e.g., BFS vs DFS vs A*).

18. Create a timeline of the development and evolution of path finding algorithms, highlighting key milestones and contributors.

19. Create a set of interactive visualizations to help users understand how different path finding algorithms work in real-time.

20. Create a collection of case studies showcasing successful implementations of path finding algorithms in industry applications.

21. Create a set of guidelines for choosing the appropriate path finding algorithm based on specific problem requirements and constraints.

22. Create a set of exercises to practice implementing path finding algorithms in different programming languages (e.g., Python, Java, C++, Rust).

23. Create a set of diagrams illustrating the differences between various path finding algorithms (e.g., BFS vs DFS vs A*).

24. Create a timeline of the development and evolution of path finding algorithms, highlighting key milestones and contributors.

25. Create a set of interactive visualizations to help users understand how different path finding algorithms work in real-time.

26. Create a collection of case studies showcasing successful implementations of path finding algorithms in industry applications.

27. Create a set of guidelines for choosing the appropriate path finding algorithm based on specific problem requirements and constraints.

28. Create a set of exercises to practice implementing path finding algorithms in different programming languages (e.g., Python, Java, C++, Rust).

29. Create a set of diagrams illustrating the differences between various path finding algorithms (e.g., BFS vs DFS vs A*).

30. Create a timeline of the development and evolution of path finding algorithms, highlighting key milestones and contributors.

31. Create a set of interactive visualizations to help users understand how different path finding algorithms work in real-time.

32. Create a collection of case studies showcasing successful implementations of path finding algorithms in industry applications.

33. Create a set of guidelines for choosing the appropriate path finding algorithm based on specific problem requirements and constraints.

34. Create a set of exercises to practice implementing path finding algorithms in different programming languages (e.g., Python, Java, C++, Rust).

35. Create a set of diagrams illustrating the differences between various path finding algorithms (e.g., BFS vs DFS vs A*).

36. Create a timeline of the development and evolution of path finding algorithms, highlighting key milestones and contributors.

37. Create a set of interactive visualizations to help users understand how different path finding algorithms work in real-time.

38. Create a collection of case studies showcasing successful implementations of path finding algorithms in industry applications.

39. Create a set of guidelines for choosing the appropriate path finding algorithm based on specific problem requirements and constraints.

40. Create a set of exercises to practice implementing path finding algorithms in different programming languages (e.g., Python, Java, C++, Rust).
