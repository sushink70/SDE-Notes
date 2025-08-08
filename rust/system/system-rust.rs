Here's a curated and comprehensive look at **open-source Rust projects** centered on **systems programming**—spanning embedded systems, operating systems, low-level tooling, and more:

---

## Embedded Systems & Bare-Metal

* **Tock OS** – Secure embedded microkernel OS for Cortex‑M and RISC‑V microcontrollers, designed for isolation and memory safety using Rust. ([Wikipedia][1])
* **Ariel OS** – A recent multicore-capable embedded OS in Rust, targeting ARM Cortex‑M, RISC‑V, and Xtensa platforms for networked sensors. ([arXiv][2])
* **rust‑embedded ecosystem** – Includes projects like `stm32-rs` (microcontroller support), RTIC framework, `Embassy`, and embedded OS tutorials. ([GitHub][3])
* **oreboot** – A firmware project (fork of coreboot) fully written in Rust, stripping out C. ([GitHub][4])

---

## Operating Systems & Kernels

* **Redox OS** – A Unix-like microkernel operating system written in Rust for x86‑64, focusing on safety and reliability. ([Wikipedia][5])
* **Theseus** – A research-focused OS built from scratch in Rust exploring novel, intra‑lingual and single-address-space design. ([GitHub][3])
* Additional hobbyist OS efforts include: **rCore**, **zCore**, **BlogOS**, **rust\_os**, **EuraliOS**, **Felix OS**, **yavkOS**, **snarkOS**—listed in the “awesome Rust” collection. ([GitHub][3])

---

## Tools, Libraries & Low-Level Projects

* **Rustls** – A modern, safe, and performant TLS library in Rust, offering FIPS and post-quantum support. ([Wikipedia][6])
* **SIMDeez** – A Rust library for abstracting over SIMD instruction sets (SSE, AVX) to generate optimized variants. ([GitHub][3])

---

## Community Project Ideas & Tutorials

* Inspired by community threads:

  * **Mini shell (`cr4sh_`)** in Rust: implements pipelines, signal handling, redirection, and job control. ([Reddit][7])
  * **Kernel tutorials** like **Philipp Oppermann’s “blog\_os” series**: guides you step-by-step to build a Rust OS from scratch. ([Reddit][8])
  * Suggestions from learners include building a **procfs parser**, **file watcher using inotify**, emulators (e.g., Chip‑8), or a tiny **compile-your-own OS concepts**. ([Reddit][9])
  * Implementing networking algorithms like congestion control (e.g., BBR) is also recommended for systems-level learning. ([Reddit][10])

---

## Quick Reference Table

| **Category**              | **Highlights**                                                                                          |
| ------------------------- | ------------------------------------------------------------------------------------------------------- |
| Embedded OS & Firmware    | Tock OS, Ariel OS, oreboot, rtic, Embassy, stm32-rs                                                     |
| General OS Kernels        | Redox OS, Theseus, rCore, zCore, BlogOS, Felix OS, yax, etc.                                            |
| Low-Level Libraries       | Rustls, SIMD abstractions (e.g., SIMDeez)                                                               |
| Learning & Tutorial Tools | `cr4sh_` shell, blog\_os tutorial, low-level tool ideas (procfs, inotify, emulator, congestion control) |

---

If any of these areas catch your interest—whether that’s embedded systems, kernel development, low-level abstractions, or building learning tools—I'd gladly guide you deeper into them!

[1]: https://en.wikipedia.org/wiki/Tock_%28operating_system%29?utm_source=chatgpt.com "Tock (operating system)"
[2]: https://arxiv.org/abs/2504.19662?utm_source=chatgpt.com "Ariel OS: An Embedded Rust Operating System for Networked Sensors & Multi-Core Microcontrollers"
[3]: https://github.com/coderonion/awesome-rust-list?utm_source=chatgpt.com "GitHub - coderonion/awesome-rust-list: This repository lists some awesome public Rust projects, Videos, Blogs and Jobs."
[4]: https://github.com/StormyTech317/awesome-rust?utm_source=chatgpt.com "GitHub - StormyTech317/awesome-rust: A curated list of Rust code and resources."
[5]: https://en.wikipedia.org/wiki/RedoxOS?utm_source=chatgpt.com "RedoxOS"
[6]: https://en.wikipedia.org/wiki/Rustls?utm_source=chatgpt.com "Rustls"
[7]: https://www.reddit.com/r/rust/comments/osvwq9?utm_source=chatgpt.com "cr4sh_ : A UNIX (only because I have not tested it on Windows) shell built with Rust"
[8]: https://www.reddit.com/r/rust/comments/hardgx?utm_source=chatgpt.com "Systems programming projects for a web developer"
[9]: https://www.reddit.com/r/learnprogramming/comments/o464n7?utm_source=chatgpt.com "need ideas for systems programming projects"
[10]: https://www.reddit.com/r/rust/comments/1i07enj?utm_source=chatgpt.com "Advanced ideas for network/systems programming projects"
