# Stack Protector — A Complete, Comprehensive Guide
### From Hardware Reality to Kernel Internals to Production Code

---

## Table of Contents

1. [Mental Model: Why This Guide Exists](#1-mental-model-why-this-guide-exists)
2. [Foundational Vocabulary](#2-foundational-vocabulary)
3. [The Call Stack — Deep Hardware Reality](#3-the-call-stack--deep-hardware-reality)
4. [Stack Layout — Byte-Level Anatomy](#4-stack-layout--byte-level-anatomy)
5. [Buffer Overflow — The Enemy](#5-buffer-overflow--the-enemy)
6. [Stack Canary — The Core Defense](#6-stack-canary--the-core-defense)
7. [How the Compiler Instruments Code](#7-how-the-compiler-instruments-code)
8. [GCC Stack Protector Variants (All Flags Explained)](#8-gcc-stack-protector-variants-all-flags-explained)
9. [Clang Stack Protector](#9-clang-stack-protector)
10. [Linux Kernel Stack Protector](#10-linux-kernel-stack-protector)
11. [Kernel Concepts Connected to Stack Protection](#11-kernel-concepts-connected-to-stack-protection)
12. [C Implementation — Production Grade](#12-c-implementation--production-grade)
13. [Go — Stack Safety Model](#13-go--stack-safety-model)
14. [Rust — Ownership as Stack Protection](#14-rust--ownership-as-stack-protection)
15. [Attack Techniques and Why Canaries Are Not Enough](#15-attack-techniques-and-why-canaries-are-not-enough)
16. [Complementary Defenses — The Full Picture](#16-complementary-defenses--the-full-picture)
17. [Performance Analysis](#17-performance-analysis)
18. [Verification and Auditing](#18-verification-and-auditing)
19. [Expert Mental Models](#19-expert-mental-models)

---

## 1. Mental Model: Why This Guide Exists

Before a single line of code, fix this mental model in your mind:

> **The stack is not just a data structure. It is the runtime autobiography of your program — a living record of where it has been, what it was doing, and where it will go next.**

When an attacker corrupts the stack, they do not merely corrupt data. They rewrite the program's *future*. Stack protection is the discipline of ensuring that this autobiography cannot be falsified.

### The Three Guarantees Stack Protector Tries to Provide

```
┌─────────────────────────────────────────────────────────┐
│  GUARANTEE 1: INTEGRITY                                 │
│  The return address is what the compiler put there.     │
│                                                         │
│  GUARANTEE 2: DETECTION                                 │
│  If integrity is violated, the program dies loudly      │
│  rather than silently executing attacker code.          │
│                                                         │
│  GUARANTEE 3: CONTAINMENT                               │
│  Corruption in one frame does not silently propagate    │
│  to callers without detection.                          │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Foundational Vocabulary

Before diving deeper, every term used in this guide is defined precisely:

| Term | Definition |
|------|------------|
| **Stack** | A region of memory that grows and shrinks as functions are called and return. Grows downward on x86/ARM (toward lower addresses). |
| **Stack Frame** | The dedicated memory block created for one function call. Contains local variables, saved registers, and the return address. |
| **Return Address** | The address the CPU will jump to when the current function finishes (`ret` instruction on x86). |
| **Stack Pointer (RSP/SP)** | A CPU register always pointing to the top of the stack (lowest valid address). |
| **Base Pointer (RBP/BP)** | A CPU register pointing to the base (bottom) of the current frame. Used to locate local variables. |
| **Buffer** | A contiguous block of memory (typically an array). `char buf[64]` is a buffer of 64 bytes. |
| **Buffer Overflow** | Writing more bytes into a buffer than it can hold, overwriting adjacent memory. |
| **Canary** | A sentinel value placed between local variables and the return address. If overwritten, the program detects it and aborts. Named after the canary in a coal mine. |
| **Stack Smashing** | The act of overflowing a stack buffer to overwrite the return address. |
| **Shellcode** | Machine code injected by an attacker, usually opens a shell or executes commands. |
| **NX / DEP** | No-Execute / Data Execution Prevention. Makes the stack non-executable so injected shellcode cannot run. |
| **ASLR** | Address Space Layout Randomization. Randomizes where the stack, heap, and libraries are loaded. |
| **ROP** | Return-Oriented Programming. An advanced attack reusing existing code fragments (gadgets) instead of injecting shellcode. |
| **Prologue** | The first few instructions of a function — sets up the stack frame. |
| **Epilogue** | The last few instructions — tears down the frame and returns. |
| **TLS** | Thread-Local Storage. Memory unique to each thread. The canary value is stored here. |
| **__stack_chk_guard** | The global (or TLS) variable holding the canary value. |
| **__stack_chk_fail** | The function called when canary corruption is detected. Terminates the process. |
| **Instrumentation** | Code inserted by the compiler (not written by you) to add runtime checks. |
| **CFI** | Control Flow Integrity. Ensures indirect calls/returns go only to valid targets. |
| **Shadow Stack** | A separate hardware-protected stack holding only return addresses (Intel CET). |

---

## 3. The Call Stack — Deep Hardware Reality

### 3.1 How the CPU Uses the Stack

On x86-64 (the architecture you must understand first):

```
CALL instruction does two things atomically:
  1. PUSH the return address (RIP+instruction_size) onto the stack
  2. JMP to the target function

RET instruction does two things:
  1. POP the return address from the stack into RIP
  2. JMP to that address (the popped value)
```

The entire security model of return-address protection is built on this simple fact: **the CPU blindly trusts whatever value is on the stack when RET executes**.

### 3.2 Memory Layout of a Running Process

```
Higher Addresses
┌──────────────────────────────────────────┐
│              KERNEL SPACE                │
│         (not accessible to user)        │
├──────────────────────────────────────────┤  0x7FFF...FFFF
│                 STACK                    │  ← RSP moves here
│        (grows downward ↓)               │
│                                          │
│            [stack frames]               │
│                                          │
├──────────────────────────────────────────┤
│                  ...                     │
├──────────────────────────────────────────┤
│    Memory-Mapped Files / Shared Libs    │
├──────────────────────────────────────────┤
│                 HEAP                     │
│        (grows upward ↑)                 │
├──────────────────────────────────────────┤
│          BSS (uninitialized data)        │
├──────────────────────────────────────────┤
│          DATA (initialized globals)      │
├──────────────────────────────────────────┤
│          TEXT (executable code)          │
└──────────────────────────────────────────┤  0x400000 (typical)
Lower Addresses
```

### 3.3 Stack Frame Anatomy (x86-64 System V ABI)

When `main()` calls `vulnerable_function()`:

```
Higher Addresses  (before the call, this is main's frame)
┌──────────────────────────────────────────┐
│          main's local variables          │
├──────────────────────────────────────────┤
│          saved main's RBP                │ ← pushed by vulnerable_function's prologue
├──────────────────────────────────────────┤
│   RETURN ADDRESS (back to main)          │ ← pushed by CALL instruction
├══════════════════════════════════════════╡ ← RBP of vulnerable_function
│   [CANARY GOES HERE — between locals     │
│    and return address]                   │
├──────────────────────────────────────────┤
│   vulnerable_function's local variables  │
│   char buf[64]   ← buffer lives here     │
├──────────────────────────────────────────┤  ← RSP (stack pointer)
Lower Addresses
```

**Critical insight**: The buffer lives at a LOWER address than the return address. When you write past the end of a buffer, you write toward HIGHER addresses — directly toward the canary, then the saved RBP, then the return address. This is not an accident of implementation; it is an inherent property of the x86 ABI.

### 3.4 Prologue and Epilogue in Assembly

A typical function prologue (without stack protector):
```asm
push   rbp          ; save caller's base pointer
mov    rbp, rsp     ; set our base pointer
sub    rsp, 0x50    ; allocate space for local variables
```

With stack protector inserted by compiler:
```asm
push   rbp
mov    rbp, rsp
sub    rsp, 0x60                     ; extra space for canary
mov    rax, QWORD PTR fs:0x28        ; load canary from TLS (offset 0x28)
mov    QWORD PTR [rbp-0x8], rax      ; store canary just below saved RBP
xor    eax, eax                      ; zero out rax (security hygiene)
```

Epilogue with canary check:
```asm
mov    rax, QWORD PTR [rbp-0x8]      ; load what should be the canary
xor    rax, QWORD PTR fs:0x28        ; XOR with original canary
je     .ok                           ; if zero, no corruption
call   __stack_chk_fail              ; else: ABORT
.ok:
leave                                ; restore RSP and RBP
ret
```

---

## 4. Stack Layout — Byte-Level Anatomy

### 4.1 Without Stack Protector

```
Address     Content
─────────────────────────────────────────
rbp - 0x40  char buf[64] starts here
rbp - 0x10  (more locals or padding)
rbp - 0x08  (alignment padding)
rbp + 0x00  ← saved RBP (8 bytes)
rbp + 0x08  ← RETURN ADDRESS (8 bytes)  ← TARGET of attack
rbp + 0x10  caller's locals
```

### 4.2 With Stack Protector

```
Address     Content
─────────────────────────────────────────
rbp - 0x48  char buf[64] starts here      ← attacker writes here
rbp - 0x08  CANARY VALUE (8 bytes)        ← trip wire
rbp + 0x00  saved RBP (8 bytes)
rbp + 0x08  RETURN ADDRESS (8 bytes)
rbp + 0x10  caller's locals
```

**The canary sits as a mine between the dangerous buffer and the precious return address.** To overwrite the return address, the attacker MUST overwrite the canary first.

---

## 5. Buffer Overflow — The Enemy

### 5.1 A Classic Overflow — Step by Step

```c
void vulnerable(char *input) {
    char buf[64];
    strcpy(buf, input);  // No bounds checking!
}
```

If `input` is 200 bytes:

```
Step 1: strcpy writes byte 0 to buf[0]     (rbp - 0x48)
Step 2: strcpy writes byte 63 to buf[63]   (rbp - 0x09)
Step 3: strcpy writes byte 64 to buf[64]   (rbp - 0x08) ← CANARY OVERWRITTEN
Step 4: strcpy writes byte 72 to buf[72]   (rbp + 0x00) ← saved RBP overwritten
Step 5: strcpy writes byte 80 to buf[80]   (rbp + 0x08) ← RETURN ADDRESS overwritten
Step 6: strcpy writes null terminator
```

When the function returns, the CPU jumps to whatever address the attacker put at `rbp + 0x08`.

### 5.2 What the Attacker Wants to Control

```
Attacker's payload layout (200 bytes):
┌────────────────┬────────┬──────────┬───────────────────┐
│ 64 bytes       │ 8 bytes│  8 bytes │  8 bytes          │
│ (junk padding) │ (junk) │  (junk)  │  attacker address │
│ fills buf      │ canary │ saved RBP│  → shell / ROP    │
└────────────────┴────────┴──────────┴───────────────────┘
```

Without knowing the canary value, the attacker cannot construct this payload correctly.

---

## 6. Stack Canary — The Core Defense

### 6.1 What Is a Canary?

Named after canaries taken into coal mines: if gas was present, the canary died first, warning miners. In stack protection, if a buffer overflow occurs, the canary value is corrupted first, triggering termination before the return address is used.

### 6.2 Properties of a Good Canary

```
1. RANDOM: Generated at program startup using a CSPRNG.
           Attacker cannot guess it.

2. CONTAINS NULL BYTE: Many overflow attacks use strcpy, which
                       stops at '\0'. A canary with \x00 in it
                       truncates naive attacks.

3. PER-PROCESS (or per-thread): Different for every run (ASLR for canary).

4. PROTECTED: Stored in TLS (Thread-Local Storage) at fs:0x28 on x86-64,
              making it hard to read directly.

5. VERIFIED BEFORE RET: Checked in epilogue, not at a predictable point
                        the attacker can jump over.
```

### 6.3 Canary Value Generation on Linux

The kernel initializes the canary in the ELF auxiliary vector (`AT_RANDOM`) — 16 random bytes placed in memory before `main()` is called. The C runtime (`glibc`) reads these bytes and stores one (8-byte aligned) as `__stack_chk_guard`.

```
Kernel →  AT_RANDOM (16 bytes) → stored at a random stack address
         ↓
glibc startup (before main):
  __stack_chk_guard = *(uintptr_t *)getauxval(AT_RANDOM);

Then stored in TLS:
  fs:0x28 = __stack_chk_guard
```

On x86-64 Linux, `fs` segment register points to the Thread Control Block (TCB). Offset `0x28` (40 bytes) into the TCB holds the stack canary. This is a fixed ABI offset defined by glibc.

### 6.4 Thread Safety

Each thread has its own TCB, therefore its own TLS, therefore potentially its own canary. In practice, glibc uses the same canary value for all threads in a process (it copies the value into each new thread's TLS). The protections is that reading `fs:0x28` is cheap and does not require synchronization.

---

## 7. How the Compiler Instruments Code

### 7.1 The Decision: Which Functions Get Protected?

The compiler does not blindly protect every function. It uses heuristics:

```
A function is a candidate for protection if it contains:

  1. An array of chars (or any type) on the stack
     → most dangerous: attackable with string functions

  2. A call to alloca() (dynamic stack allocation)
     → variable-size allocation, unpredictable layout

  3. A local variable whose address is taken
     → pointer to stack, might escape

  4. (with -fstack-protector-all): every function, no exceptions
```

### 7.2 Compiler Transformation Pipeline

```
Source Code (C)
      ↓
  [Lexing / Parsing → AST]
      ↓
  [Semantic Analysis — identifies vulnerable local variables]
      ↓
  [Gimple IR / RTL generation]
      ↓
  [Stack Layout Pass]
        → Identifies "dangerous" variables
        → Moves them to higher addresses within the frame
          (closer to return address, so canary sits between them and caller data)
      ↓
  [Stack Protector Pass]
        → Inserts canary load in prologue
        → Inserts canary check in epilogue
        → Adds call to __stack_chk_fail if mismatch
      ↓
  [Code Generation → Assembly]
      ↓
  [Assembler → Object File]
      ↓
  [Linker → links __stack_chk_fail from libc]
```

### 7.3 Variable Rearrangement

The compiler also **rearranges the stack layout** to group dangerous variables together, away from safe ones:

```
Original source order:
  int safe_int;
  char buf[64];       ← dangerous
  void *safe_ptr;

Compiler reorders to:
  [higher addresses]
  canary
  safe_int
  safe_ptr
  buf[64]             ← dangerous, pushed to lowest address
  [lower addresses, RSP]
```

This ensures that a linear overflow from `buf` must traverse the canary before reaching any safe variables or the return address. **This rearrangement is a defense in depth**, not just the canary.

---

## 8. GCC Stack Protector Variants (All Flags Explained)

### 8.1 `-fno-stack-protector`

Disables all stack protection. Used for:
- Embedded systems with no canary support in libc
- Bootloaders, very early kernel code
- Performance-critical hot paths (measure first!)
- When you are implementing your own protection

### 8.2 `-fstack-protector`

```
Protects: Functions that contain a local char array of 8 bytes or more
          OR call alloca().

NOT protected: Functions with only int/long locals, no arrays.

Cost: ~3 instructions in prologue + 3 in epilogue for protected functions.
```

This is the **minimal** protection. Miss rate is high for functions with small buffers.

### 8.3 `-fstack-protector-strong` *(recommended default)*

```
Protects: All functions that have:
  - Any local array (any type, any size, including 1-element arrays)
  - Local variable whose address is taken (&local_var)
  - Any call to alloca()
  - Local variable that is a struct/union containing an array

Does NOT protect: Pure functions with only scalar locals and no address-taking.
```

Introduced in GCC 4.9. This is the right default for production code. It catches the vast majority of real-world vulnerabilities while skipping truly safe functions.

### 8.4 `-fstack-protector-all`

```
Protects: Every single function, unconditionally.

Including: Functions with only "int x; return x+1;" — zero benefit.

Cost: Significant performance overhead in loop-heavy code that makes
      many small function calls.
```

Useful for: Security auditing, testing, environments where maximum protection trumps performance.

### 8.5 `-fstack-protector-explicit`

```
Protects: Only functions explicitly annotated with:
  __attribute__((stack_protect))

Use case: Fine-grained control in embedded/kernel code where you know
          exactly which functions need protection.
```

### 8.6 Comparing Protection Coverage

```
Flag                     | Coverage    | Overhead  | Use Case
─────────────────────────┼─────────────┼───────────┼──────────────────────
-fno-stack-protector     | 0%          | 0%        | Kernel/embedded opt.
-fstack-protector        | ~30-40%     | Low       | Legacy compat
-fstack-protector-strong | ~70-90%     | Low-Med   | Production default ✓
-fstack-protector-all    | 100%        | Med-High  | Audit/paranoid
-fstack-protector-       | Manual      | Varies    | Explicit annotation
  explicit               |             |           |
```

### 8.7 Additional GCC Stack Flags

```bash
# Warn if stack usage exceeds N bytes (static analysis)
-Wstack-usage=<N>

# Error if stack frame size exceeds N bytes
-fstack-limit-symbol=<symbol>

# Insert stack clash protection (guards against heap-to-stack collision)
-fstack-clash-protection

# Shadow call stack (AArch64) — hardware-assisted return address protection
-fsanitize=shadow-call-stack

# Address sanitizer — detects buffer overflows at runtime (dev only)
-fsanitize=address
```

---

## 9. Clang Stack Protector

Clang uses the same flags as GCC for compatibility:

```bash
clang -fstack-protector-strong -o binary source.c
```

### 9.1 Clang-Specific Differences

```
1. SafeStack (-fsanitize=safe-stack):
   Clang's extension. Splits the stack into:
   - "Safe stack": scalars, return addresses (normal RSP)
   - "Unsafe stack": arrays, address-taken variables (separate region)
   
   The unsafe stack is placed in a random location, not adjacent
   to the safe stack. An overflow in the unsafe stack cannot reach
   return addresses because they are in a completely different region.

2. ShadowCallStack (-fsanitize=shadow-call-stack):
   Stores return addresses in a separate shadow stack region.
   On function entry: push return address to shadow stack.
   On return: verify return address matches shadow stack top.
   
   This defeats ROP attacks that overwrite the call stack's return address
   because the shadow stack is unrelated to RSP.
```

### 9.2 Clang SafeStack Architecture

```
Normal layout (vulnerable):
  [return addr] [canary] [buf] ← single contiguous stack

SafeStack layout:
  Safe Stack (RSP-based):          Unsafe Stack (random addr):
  [return addr]                    [buf]  ← isolated!
  [scalars]
  
  Overflow in buf cannot reach return addr — they're in different memory.
```

---

## 10. Linux Kernel Stack Protector

### 10.1 Kernel Stack Characteristics

The kernel stack is fundamentally different from userspace:

```
User Process Stack:
  - Per-thread, grows dynamically
  - Starts large (default 8MB limit)
  - Protected by ASLR, canary in TLS (fs:0x28)
  - Overflow → SIGSEGV, program terminates

Kernel Stack:
  - Per-thread (kernel threads) OR per-CPU (interrupt handlers)
  - Fixed size: 8KB or 16KB (architecture-dependent, config option)
  - Critically small — kernel functions must be stack-conservative
  - Overflow corrupts kernel data → kernel panic OR silent exploitation
  - No SIGSEGV — corruption can be silent and catastrophic
```

### 10.2 Kernel Stack Protector Configuration

In the Linux kernel Kconfig (`make menuconfig`):

```
Security options →
  [*] Stack Protector buffer overflow detection
      (X) Regular (CONFIG_STACKPROTECTOR)
      ( ) Strong (CONFIG_STACKPROTECTOR_STRONG)
```

```
CONFIG_STACKPROTECTOR:
  Uses -fstack-protector
  Only protects functions with 8+ byte char arrays

CONFIG_STACKPROTECTOR_STRONG:
  Uses -fstack-protector-strong
  Protects more functions
  Recommended for security-conscious kernels
  Default in most distributions since kernel 3.14
```

### 10.3 Kernel Canary Implementation

Unlike userspace (which uses `fs:0x28`), the kernel uses its own per-CPU canary:

```c
/* arch/x86/include/asm/stackprotector.h */

/*
 * Initialize the stackprotector canary value.
 * NOTE: Boot CPU calls this once from setup_arch().
 * Each CPU gets its own canary.
 */
static __always_inline void boot_init_stack_canary(void)
{
    u64 canary;
    u64 tsc;

    BUILD_BUG_ON(offsetof(union irq_stack_union, stack_canary) != 40);

    /*
     * We both use the random pool and the current TSC as a source
     * of randomness. The TSC is not reliable as a random number
     * source but provides some extra unpredictability (different
     * on each CPU).
     */
    get_random_bytes(&canary, sizeof(canary));
    tsc = rdtsc();
    canary ^= tsc;
    canary &= CANARY_MASK;      /* mask off null byte for strcpy resistance */

    current->stack_canary = canary;

    /* Write to the per-CPU irq_stack_union at offset 40 */
    this_cpu_write(irq_stack_union.stack_canary, canary);
}
```

**Key differences from userspace:**
- The canary is stored at `gs:40` (kernel uses `gs` segment, not `fs`)
- Each CPU has its own canary via per-CPU data
- The canary is stored in `irq_stack_union` — the same structure as the IRQ stack

### 10.4 `irq_stack_union` — The Kernel's TLS Equivalent

```c
/* arch/x86/include/asm/processor.h */
union irq_stack_union {
    char irq_stack[IRQ_STACK_SIZE];   /* interrupt handler stack */
    struct {
        char gs_base[40];             /* must be at offset 0 */
        unsigned long stack_canary;   /* at offset 40 = gs:40 */
    };
};
```

This is a union — the IRQ stack and the canary share the same memory region. The canary sits at the very base (offset 40) of the interrupt stack, a fixed ABI location.

### 10.5 Kernel Stack Overflow Protection Layers

```
Layer 1: CONFIG_STACKPROTECTOR_STRONG
         → Canary in every vulnerable kernel function
         → Detects linear overflows

Layer 2: CONFIG_VMAP_STACK (since kernel 4.9)
         → Maps the kernel stack with virtual memory guard pages
         → A stack overflow hits a guard page → immediate page fault
         → Eliminates "silent" stack overflows that previously
           could corrupt adjacent thread_info

Layer 3: CONFIG_SCHED_STACK_END_CHECK
         → At schedule() time, checks if the end-of-stack magic
           number is intact (debug feature)

Layer 4: CONFIG_KASAN (Kernel Address Sanitizer)
         → Full shadow memory instrumentation
         → Detects any out-of-bounds access on kernel stack
         → ~2x slowdown, development/testing only

Layer 5: CONFIG_SHADOW_CALL_STACK (AArch64 only, kernel 5.8+)
         → Hardware shadow stack for kernel return addresses
```

### 10.6 VMAP_STACK — Guard Pages in Detail

```
Without VMAP_STACK (old kernels):
  thread_info    ← bottom of stack, overlaps with process metadata
  [stack grows down]
  Overflow → corrupts thread_info silently → privilege escalation!

With VMAP_STACK:
  GUARD PAGE (not mapped, triggers page fault on access)
  [kernel stack — 16KB]
  GUARD PAGE
  
  Overflow → immediate fault → kernel prints stack trace and panics
  No silent corruption possible.
```

This was a major security improvement. Before VMAP_STACK, the infamous "Stack Clash" vulnerability class could silently jump over guard pages by using `alloca()` in large steps.

### 10.7 Stack Clash Protection in the Kernel

```
CONFIG_STACKLEAK (grsecurity/PaX origin, merged in kernel 4.20):
  - Zeroes the kernel stack before returning to userspace
  - Prevents info leakage from stack residue
  - Prevents "use of uninitialized stack" vulnerabilities
  
-fstack-clash-protection (GCC 8+):
  - Generates probe instructions when adjusting RSP by more than
    one page at a time
  - Prevents jumping over guard pages with large alloca()
  - Applied to kernel builds with: CONFIG_CC_HAS_STACKLEAK_INTRINSIC
```

### 10.8 Kernel Oops vs. Panic on Stack Corruption

```
Stack canary failure in userspace:
  → __stack_chk_fail() called
  → Sends SIGABRT to the process
  → Process dies, kernel continues

Stack canary failure in kernel:
  → __stack_chk_fail() called
  → Kernel calls panic("stack-protector: Kernel stack is corrupted in: %pB")
  → System halts
  → (or reboots if panic_on_oops=1)
  
The kernel cannot "kill" itself partially — a corrupted kernel stack 
means the entire system is in an undefined state.
```

---

## 11. Kernel Concepts Connected to Stack Protection

### 11.1 Thread Information Structure (`thread_info`)

Every kernel thread has a `thread_info` structure containing its flags, CPU number, and a pointer to the `task_struct`. Historically stored at the bottom of the kernel stack (why overflow was dangerous). With VMAP_STACK, `thread_info` is moved out of the stack entirely on some architectures.

```c
/* include/linux/thread_info.h */
struct thread_info {
    unsigned long flags;    /* low level flags */
    int           preempt_count;
    mm_segment_t  addr_limit;  /* user-space address space limit */
    /* ... */
};
```

### 11.2 Per-CPU Data and the `gs` Register

The kernel uses the `gs` segment register to point to per-CPU data. This is how `gs:40` (the canary location) is different for each CPU without any locks. Per-CPU data is allocated during boot for each online CPU, initialized, and then accessed via `gs` which the kernel sets during context switch.

```
CPU 0 gs → per_cpu_data_cpu0 { [0..39: other data] [40: canary_cpu0] ... }
CPU 1 gs → per_cpu_data_cpu1 { [0..39: other data] [40: canary_cpu1] ... }
```

### 11.3 Context Switch and Canary Restoration

When the kernel switches from thread A to thread B on the same CPU:
- The scheduler calls `__switch_to()`
- The `gs` base is updated to point to the new thread's per-CPU area
- The canary at `gs:40` is updated to the new thread's canary value
- This ensures each thread's function calls use the correct canary

### 11.4 KASLR (Kernel ASLR)

KASLR randomizes the base address of the kernel image itself. This complements stack protection by making it harder for an attacker to know the address of useful kernel gadgets for ROP chains, even if they can overwrite a return address.

```bash
# Enabled in kernel command line:
kaslr              # enable (default in most distros)
nokaslr            # disable (for debugging)

# Check if enabled:
cat /proc/kallsyms | head   # addresses will be non-zero only for root
```

### 11.5 SMEP and SMAP

```
SMEP (Supervisor Mode Execution Prevention):
  CPU refuses to execute code in user-space pages while in kernel mode.
  Defeats: "ret2user" attacks where overflow redirects kernel to shellcode
           in user memory.

SMAP (Supervisor Mode Access Prevention):
  CPU refuses to READ or WRITE user-space pages from kernel mode
  without explicit `stac`/`clac` instructions.
  Defeats: Kernel dereferencing user pointers without copy_from_user().
```

Both require hardware support (Intel Broadwell+, AMD Zen+) and kernel config:
```
CONFIG_X86_SMEP=y
CONFIG_X86_SMAP=y
```

---

## 12. C Implementation — Production Grade

### 12.1 Demonstrating Stack Protector in Action

```c
/*
 * stack_protector_demo.c
 *
 * Compile variants:
 *   WITHOUT protection: gcc -fno-stack-protector -o demo_unsafe demo.c
 *   WITH protection:    gcc -fstack-protector-strong -o demo_safe demo.c
 *
 * Purpose: Demonstrate canary insertion, detection, and the difference
 *          in generated assembly between protected and unprotected code.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>

/* Named constants — no magic numbers */
#define BUFFER_CAPACITY     64U
#define SAFE_INPUT_LIMIT    (BUFFER_CAPACITY - 1U)   /* leave room for '\0' */
#define CANARY_TLS_OFFSET   40U                       /* gs:40 on x86-64 */

/*
 * Read the canary from TLS directly (x86-64 Linux only).
 * This is what the compiler-generated code does at fs:0x28.
 *
 * NOTE: On x86-64 Linux userspace, the segment is 'fs', not 'gs'.
 *       gs is used by the kernel. fs is used by glibc for TLS.
 */
static inline uintptr_t read_canary_from_tls(void)
{
    uintptr_t canary;
    __asm__ volatile (
        "mov %%fs:%1, %0"
        : "=r" (canary)
        : "m" (*(uintptr_t *)CANARY_TLS_OFFSET)
    );
    return canary;
}

/*
 * safe_copy: Production-grade bounded string copy.
 *
 * Returns 0 on success, -1 if input exceeds capacity.
 * Always NUL-terminates dst.
 */
static int safe_copy(char *restrict dst, const char *restrict src,
                     size_t dst_capacity)
{
    if (dst == NULL || src == NULL || dst_capacity == 0) {
        return -1;
    }

    size_t src_len = strnlen(src, dst_capacity);
    if (src_len == dst_capacity) {
        /* Input is too long: truncate and NUL-terminate */
        memcpy(dst, src, dst_capacity - 1U);
        dst[dst_capacity - 1U] = '\0';
        return -1;   /* Signal truncation */
    }

    memcpy(dst, src, src_len + 1U);   /* +1 for '\0' */
    return 0;
}

/*
 * unsafe_function: Intentionally vulnerable.
 * Compile with -fstack-protector-strong to see canary detection.
 * Compile with -fno-stack-protector to see silent corruption.
 */
__attribute__((noinline))   /* prevent inlining so frame is visible */
static void unsafe_function(const char *user_input)
{
    char buf[BUFFER_CAPACITY];

    printf("[unsafe_function] buffer at: %p\n", (void *)buf);
    printf("[unsafe_function] canary from TLS: 0x%016lx\n",
           (unsigned long)read_canary_from_tls());

    /*
     * strcpy has no bounds checking.
     * If user_input > 64 bytes, this overflows buf onto the canary.
     */
    strcpy(buf, user_input);   /* DELIBERATELY UNSAFE */

    printf("[unsafe_function] Contents: %.63s\n", buf);
    /* If we reach here with long input, canary check in epilogue fires */
}

/*
 * safe_function: Identical purpose, properly bounded.
 */
__attribute__((noinline))
static void safe_function(const char *user_input)
{
    char buf[BUFFER_CAPACITY];

    int result = safe_copy(buf, user_input, sizeof(buf));
    if (result != 0) {
        fprintf(stderr, "[safe_function] WARNING: Input truncated to %zu bytes\n",
                SAFE_INPUT_LIMIT);
    }

    printf("[safe_function] Contents: %s\n", buf);
}

/*
 * inspect_stack_frame:
 * Shows the memory layout of the current stack frame to visualize
 * where the canary sits relative to local variables.
 */
__attribute__((noinline))
static void inspect_stack_frame(void)
{
    char     local_buf[32];           /* 32-byte buffer */
    int      local_int  = 0xDEADBEEF;
    uint64_t local_u64  = 0xCAFEBABECAFEBABEULL;

    /* These addresses reveal the stack layout */
    printf("\n=== Stack Frame Inspection ===\n");
    printf("  &local_buf[0]:  %p\n", (void *)&local_buf[0]);
    printf("  &local_int:     %p\n", (void *)&local_int);
    printf("  &local_u64:     %p\n", (void *)&local_u64);
    printf("  Canary (TLS):   0x%016lx\n",
           (unsigned long)read_canary_from_tls());

    /*
     * On a protected build, the compiler has placed a canary
     * at [rbp - 8], above (higher address than) local_buf.
     * We can peek at it:
     */
    uintptr_t *frame_canary = (uintptr_t *)((char *)__builtin_frame_address(0) - 8);
    printf("  Frame canary:   0x%016lx  (at %p)\n",
           (unsigned long)*frame_canary, (void *)frame_canary);
    printf("  Match TLS?      %s\n\n",
           (*frame_canary == read_canary_from_tls()) ? "YES ✓" : "NO ✗");

    (void)local_int;
    (void)local_u64;
}

int main(int argc, char *argv[])
{
    printf("=== Stack Protector Demo ===\n\n");

    /* Show canary value for this process */
    printf("Process canary (from TLS fs:0x28): 0x%016lx\n\n",
           (unsigned long)read_canary_from_tls());

    inspect_stack_frame();

    /* Safe path */
    puts("--- Safe function with normal input ---");
    safe_function("Hello, world!");

    /* Safe path with long input (truncated gracefully) */
    puts("\n--- Safe function with oversized input ---");
    safe_function("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                  "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");

    /* Unsafe path — will trigger canary check if compiled with -fstack-protector */
    if (argc > 1 && strcmp(argv[1], "--trigger-overflow") == 0) {
        puts("\n--- TRIGGERING OVERFLOW (unsafe_function) ---");
        char payload[200];
        memset(payload, 'A', sizeof(payload) - 1);
        payload[sizeof(payload) - 1] = '\0';
        unsafe_function(payload);
    } else {
        puts("\n--- Unsafe function with normal input ---");
        unsafe_function("Safe input");
    }

    puts("\nProgram completed normally.");
    return EXIT_SUCCESS;
}
```

### 12.2 Verifying Canary Presence in Binary

```bash
# Compile with protection
gcc -fstack-protector-strong -O2 -o demo stack_protector_demo.c

# Check for __stack_chk_fail reference (symbol must exist for protection to work)
nm demo | grep stack_chk
# Expected output:
# U __stack_chk_fail          (U = undefined, resolved from libc)

# Check if binary was compiled with stack protector (checksec tool)
checksec --file=demo
# Expected:
# RELRO: Full | STACK CANARY: Enabled | NX: Enabled | PIE: Enabled | ...

# View generated assembly (look for fs:0x28 loads)
objdump -d demo | grep -A 20 "<unsafe_function>"
# You should see:
#   mov rax, QWORD PTR fs:0x28    ← canary load
#   mov QWORD PTR [rbp-0x8], rax  ← canary store
#   ...
#   xor rax, QWORD PTR fs:0x28    ← canary verify
#   je  ...                        ← jump if OK
#   call __stack_chk_fail          ← die if not OK
```

### 12.3 Custom Stack Canary (Embedded / No libc)

For bare-metal or embedded systems without glibc's `__stack_chk_guard`:

```c
/*
 * custom_canary.c
 *
 * Implement __stack_chk_guard and __stack_chk_fail for environments
 * without glibc (embedded, kernel modules, bootloaders).
 *
 * Compile: gcc -fstack-protector-strong -ffreestanding -nostdlib ...
 */

#include <stdint.h>
#include <stdnoreturn.h>

/*
 * The canary sentinel. Must be initialized before any protected function
 * runs. In a real system, seed from hardware RNG or TRNG peripheral.
 *
 * Placement in .data ensures it is a fixed symbol the compiler can reference.
 */
uintptr_t __stack_chk_guard = 0;

/*
 * Platform-specific: read hardware random number.
 * Replace with your platform's RNG (e.g., ARM TrustZone, RISC-V entropy src).
 */
static uintptr_t platform_get_random(void)
{
    /*
     * On x86 with RDRAND support:
     * This is the production approach — RDRAND is a hardware CSPRNG.
     */
    uintptr_t value = 0;

#if defined(__x86_64__)
    uint8_t ok;
    __asm__ volatile (
        "rdrand %0\n"
        "setc   %1\n"
        : "=r"(value), "=qm"(ok)
        :
        : "cc"
    );
    if (!ok) {
        /* RDRAND failed — use TSC XOR with a compile-time constant */
        uint64_t tsc;
        __asm__ volatile ("rdtsc" : "=A"(tsc));
        value = (uintptr_t)(tsc ^ 0xDEADBEEFCAFEBABEULL);
    }
#else
    /* Fallback for other architectures */
    value = (uintptr_t)0xDEADBEEFCAFEBABEULL;  /* NOT secure, demo only */
#endif

    /* Force null byte at MSB position (strcpy protection) */
    value &= ~(uintptr_t)0xFF00000000000000ULL;

    return value;
}

/*
 * init_stack_canary: Call once before any protected function.
 * In a real OS: call from early boot, before enabling interrupts.
 */
void init_stack_canary(void)
{
    __stack_chk_guard = platform_get_random();
}

/*
 * __stack_chk_fail: Called by compiler-generated epilogue code.
 *
 * This function MUST NOT return. It MUST NOT use the stack beyond
 * what it absolutely needs (the stack may be corrupted).
 *
 * noreturn: tells compiler this function never returns.
 * __attribute__((naked)): no prologue/epilogue (stack may be corrupt).
 */
noreturn __attribute__((noinline))
void __stack_chk_fail(void)
{
    /*
     * At this point:
     * - The stack canary has been corrupted
     * - The stack may be partially or fully corrupted
     * - The return address may have been overwritten
     * - We CANNOT trust any stack-based data
     * - We CANNOT safely call functions that use the stack
     *
     * Safe actions:
     * 1. Write to a hardware register (UART, LED, etc.)
     * 2. Trigger a hardware reset
     * 3. Enter an infinite loop (fail-safe halt)
     * 4. Trigger a hardware watchdog reset
     */

    /* On x86: raise General Protection Fault intentionally */
    __asm__ volatile (
        "ud2"    /* Undefined instruction — causes CPU exception */
        ::: "memory"
    );

    /* Unreachable, but required by noreturn semantics */
    __builtin_unreachable();
}
```

---

## 13. Go — Stack Safety Model

### 13.1 How Go Avoids Traditional Stack Overflows

Go does not use fixed-size stacks. It uses **goroutine stacks** that start small and grow dynamically. This fundamentally changes the threat model:

```
Traditional C stack:
  Fixed size (default 8MB for threads)
  Lives at a fixed address range
  Overflow → corrupts adjacent memory

Go goroutine stack:
  Starts at 2KB (Go 1.4+, previously 8KB)
  Grows by: detecting stack growth need → allocating new, larger stack
            → copying all data to new stack → continuing
  Shrinks by: GC detecting large idle stack → copying to smaller stack
  
  An attacker cannot "overflow" the goroutine stack in the traditional sense
  because Go detects the growth need before it happens.
```

### 13.2 Stack Growth Mechanism in Go Runtime

The compiler inserts a **stack growth check** at the start of every function:

```asm
; Generated by Go compiler for every non-leaf function
MOVQ (TLS), R14          ; load goroutine pointer from TLS
CMPQ SP, 16(R14)         ; compare SP with g.stackguard0
JBE  stack_grow          ; if SP <= stackguard0, grow the stack
```

The `stackguard0` field in the `g` (goroutine) struct is set to `stack.lo + StackGuard` where `StackGuard` is a small buffer zone. When the stack pointer approaches the bottom of the current stack segment, the goroutine's stack is transparently grown.

### 13.3 Go Stack Security Implications

```
WHAT GO PROVIDES:
  ✓ No buffer overflow via stack exhaustion (goroutine stacks grow)
  ✓ Safe slices with runtime bounds checking (index out of range → panic)
  ✓ No manual memory management → no use-after-free on stack
  ✓ Garbage collector manages heap → no heap-based return address corruption

WHAT GO DOES NOT PROVIDE:
  ✗ Traditional canary (not needed by design)
  ✗ Protection against unsafe.Pointer misuse
  ✗ Protection against cgo calling into unsafe C code
  ✗ The runtime itself (written in Go+asm) must be carefully audited
```

### 13.4 Go's `unsafe` Package — The Stack Safety Escape Hatch

```go
/*
 * stack_safety_go.go
 *
 * Demonstrates Go's stack safety guarantees and how unsafe breaks them.
 * Purpose: Understand what Go protects and what it doesn't.
 *
 * Build: go build -gcflags="-m" stack_safety_go.go
 *        (-m shows escape analysis decisions)
 */

package main

import (
	"fmt"
	"runtime"
	"unsafe"
)

// SafeBuffer: Go's type system prevents overflow.
// The compiler inserts bounds checks on every slice index.
func safeBufferDemo() {
	buf := make([]byte, 64)
	input := make([]byte, 200)
	for i := range input {
		input[i] = 'A'
	}

	// Safe: copy respects destination capacity
	n := copy(buf, input)
	fmt.Printf("[safe] Copied %d bytes into buf[64]. buf intact.\n", n)

	// This would panic at runtime with "index out of range":
	// buf[100] = 'X'
}

// GoroutineStackGrowthDemo: Shows transparent stack growth.
// Each recursive call consumes ~N bytes of stack.
// Go grows the stack automatically — no overflow possible.
func deepRecursion(depth int) int {
	if depth == 0 {
		// Print current goroutine stack info
		var stats runtime.MemStats
		runtime.ReadMemStats(&stats)
		return 0
	}
	// Large local array forces stack growth
	var localData [512]byte
	localData[0] = byte(depth)
	return int(localData[0]) + deepRecursion(depth-1)
}

// UnsafePointerMisuse: Demonstrates that unsafe breaks all guarantees.
// This is the ONLY way to corrupt Go's stack — intentional misuse.
func unsafePointerMisuse() {
	var x int64 = 0x4141414141414141 // "AAAAAAAA"

	// Get a pointer to x, then arithmetic to "nearby" memory
	// This is UNDEFINED BEHAVIOR and can corrupt the stack.
	// DO NOT do this in production code.
	ptr := unsafe.Pointer(&x)
	_ = ptr

	// NOTE: In Go, return addresses are on the goroutine stack,
	// but the GC and runtime actively scan and update them during
	// stack growth (copying GC). Even if you corrupt a return address,
	// the next GC cycle may overwrite your corruption.
	// This makes exploitation far harder than in C.
	fmt.Println("[unsafe] This is where undefined behavior begins.")
}

// StackInspector: Inspect goroutine stack limits.
func stackInspector() {
	var dummy int
	// Stack grows downward; &dummy is near current SP
	fmt.Printf("[stack inspector] Local variable at: %p\n", &dummy)

	// Go runtime provides no direct API to read stack bounds,
	// but you can use runtime/debug.Stack() for a human-readable trace.
	// The goroutine's stack lo/hi are internal runtime fields.
}

// CgoUnsafeDemo: Shows that cgo can bypass Go's safety.
// (Shown conceptually — actual cgo requires C code in same package)
//
// import "C"
// func cgoOverflow() {
//     var buf [64]C.char
//     C.strcpy(&buf[0], (*C.char)(unsafe.Pointer(longInput)))
//     // C's strcpy has NO bounds checking — overflow possible!
// }

func main() {
	fmt.Println("=== Go Stack Safety Demo ===\n")

	safeBufferDemo()

	fmt.Println("\n[goroutine stack growth] Starting deep recursion...")
	result := deepRecursion(10000) // 10000 deep — would blow C stack
	fmt.Printf("[goroutine stack growth] Completed: result=%d\n", result)

	stackInspector()

	fmt.Println("\nAll safe operations completed.")
}
```

### 13.5 Go Compiler Flags Related to Stack Safety

```bash
# Build with race detector (detects data races, not stack overflows)
go build -race ./...

# Show escape analysis (which variables escape to heap)
go build -gcflags="-m -m" ./...

# Show stack frame sizes
go build -gcflags="-S" ./... 2>&1 | grep "FUNCDATA\|stack"

# Disable bounds checking (DANGEROUS — development benchmarking only)
go build -gcflags="-B" ./...

# Build without optimization (useful for debugging stack issues)
go build -gcflags="-N -l" ./...
```

---

## 14. Rust — Ownership as Stack Protection

### 14.1 Rust's Compile-Time Stack Safety

Rust eliminates the entire class of stack buffer overflow vulnerabilities at compile time through its ownership and type system:

```
C approach: Buffer exists → runtime check (or no check) → overflow possible
Rust approach: Overflow is a compile-time error OR a checked runtime panic
               (via bounds checking on slices/arrays — no silent corruption)
```

### 14.2 What Rust Guarantees

```
COMPILE-TIME GUARANTEES (zero runtime cost):
  ✓ No dangling pointers to stack variables
  ✓ No use-after-return (lifetimes enforce this)
  ✓ No double-free of stack-allocated memory
  ✓ Borrowing rules prevent aliased mutable references

RUNTIME GUARANTEES (bounds checks — small overhead):
  ✓ Array/slice indexing panics on out-of-bounds (no silent overflow)
  ✓ No undefined behavior in safe code
  ✓ Stack unwinding on panic (optional, can be replaced with abort)

EXPLICITLY NOT GUARANTEED (in unsafe blocks):
  ✗ Raw pointer arithmetic can overflow
  ✗ unsafe { ptr.offset(n) } can corrupt the stack
  ✗ FFI calls into C can trigger traditional overflows
```

### 14.3 Production Rust Stack Safety Code

```rust
//! stack_protector_rust.rs
//!
//! Demonstrates Rust's stack safety model:
//!   - Ownership preventing use-after-stack-deallocation
//!   - Slice bounds checking preventing buffer overflow
//!   - Lifetime system as compile-time stack protection
//!   - How unsafe blocks interact with these guarantees
//!
//! Build: cargo build --release
//!        RUSTFLAGS="-C overflow-checks=yes" cargo build

use std::fmt;

/// Error type for buffer operations — no panic, proper propagation.
#[derive(Debug, PartialEq)]
pub enum BufferError {
    InputTooLarge { input_len: usize, capacity: usize },
    NullInput,
    EmptyInput,
}

impl fmt::Display for BufferError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            BufferError::InputTooLarge { input_len, capacity } => {
                write!(f, "Input length {} exceeds buffer capacity {}", input_len, capacity)
            }
            BufferError::NullInput => write!(f, "Null input provided"),
            BufferError::EmptyInput => write!(f, "Empty input provided"),
        }
    }
}

/// BUFFER_CAPACITY: Stack-allocated buffer size.
/// Named constant — no magic numbers.
const BUFFER_CAPACITY: usize = 64;

/// StackBuffer: A fixed-size, stack-allocated buffer with explicit bounds.
///
/// The size is a compile-time constant, so the stack frame size is known
/// to the compiler. The compiler can (and does) verify no overflow is possible
/// in safe code.
pub struct StackBuffer {
    data: [u8; BUFFER_CAPACITY],
    len: usize,  /// Tracks how many bytes are actually used
}

impl StackBuffer {
    /// Creates a new zeroed buffer.
    ///
    /// Performance note: [0u8; N] is initialized by the compiler, often
    /// optimized to memset or even elided if the compiler can prove it
    /// will be overwritten before read.
    pub const fn new() -> Self {
        Self {
            data: [0u8; BUFFER_CAPACITY],
            len: 0,
        }
    }

    /// Write data into the buffer, returning error if too large.
    ///
    /// No panic. No undefined behavior. If input doesn't fit, returns Err.
    pub fn write(&mut self, input: &[u8]) -> Result<(), BufferError> {
        if input.is_empty() {
            return Err(BufferError::EmptyInput);
        }

        if input.len() > BUFFER_CAPACITY {
            return Err(BufferError::InputTooLarge {
                input_len: input.len(),
                capacity: BUFFER_CAPACITY,
            });
        }

        // Rust's slice::copy_from_slice performs bounds checking.
        // The compiler can PROVE at compile time this is safe because:
        //   - input.len() <= BUFFER_CAPACITY (checked above)
        //   - self.data[..input.len()] is valid (slice of known-size array)
        // So the bounds check is ELIDED in release mode — zero overhead!
        self.data[..input.len()].copy_from_slice(input);
        self.len = input.len();
        Ok(())
    }

    /// Read the active portion of the buffer.
    pub fn as_slice(&self) -> &[u8] {
        &self.data[..self.len]
    }
}

/// DanglingPointerPrevention: Demonstrates Rust's lifetime system.
///
/// In C, this would compile and produce a dangling pointer.
/// In Rust, the compiler rejects it with a lifetime error.
///
/// ```c
/// // C: UNDEFINED BEHAVIOR — returns pointer to dead stack memory
/// char* get_stack_data() {
///     char buf[64] = "hello";
///     return buf;  // buf is destroyed here!
/// }
/// ```
///
/// In Rust, the equivalent is a compile-time error:
pub fn rust_prevents_dangling() {
    // This function CANNOT be written incorrectly in safe Rust:
    //
    // fn bad() -> &str {
    //     let s = String::from("hello");
    //     &s   // ERROR: `s` does not live long enough
    // }
    //
    // The borrow checker enforces: no reference outlives its owner.
    // This is compile-time stack protection — zero runtime cost.

    println!("[rust_prevents_dangling] Rust's borrow checker prevents this error class.");
}

/// BoundsCheckDemo: Shows that Rust panics instead of overflowing.
///
/// The panic is a detected, loud failure — not silent corruption.
/// With `panic = "abort"` in Cargo.toml, this terminates the process.
/// With `panic = "unwind"`, the stack unwinds and caller can catch it.
pub fn bounds_check_demo() {
    let buf: [u8; BUFFER_CAPACITY] = [0u8; BUFFER_CAPACITY];

    // Safe access: verified at runtime
    let byte = buf[10];
    println!("[bounds_check] buf[10] = {}", byte);

    // This would PANIC at runtime:
    // let bad = buf[100];  // thread 'main' panicked at 'index out of range'
    //
    // Critically: this is NOT silent. The program halts loudly.
    // The return address is NEVER corrupted. The canary is NEVER needed.
    // The panic is the security mechanism.

    // Unchecked access (requires unsafe — explicit contract violation):
    // let bad = unsafe { *buf.get_unchecked(100) };  // UB — don't do this
}

/// UnsafeAuditDemo: Shows the exact surface area where Rust's guarantees break.
///
/// In a security audit, every `unsafe` block must be justified and reviewed.
/// The unsafe surface should be minimal and well-documented.
///
/// # Safety
/// This function performs raw pointer arithmetic. The caller must ensure
/// that `ptr` points to valid memory of at least `len` bytes.
pub unsafe fn unsafe_copy(dst: *mut u8, src: *const u8, len: usize) {
    // SAFETY INVARIANTS (must be upheld by caller):
    //   1. dst is valid for writes of `len` bytes
    //   2. src is valid for reads of `len` bytes
    //   3. dst and src do not overlap (use memmove semantics otherwise)
    //   4. len <= isize::MAX (required by pointer arithmetic)
    std::ptr::copy_nonoverlapping(src, dst, len);
}

/// FFIBoundaryDemo: Demonstrates the risk at the C FFI boundary.
///
/// When calling C functions from Rust, all of C's unsafety re-enters.
/// This is why `unsafe extern "C"` blocks must be treated with the same
/// rigor as C code itself.
mod ffi_safety {
    /// Safe wrapper around a hypothetical C function.
    ///
    /// The raw C function is declared in an extern block (unsafe).
    /// The wrapper adds Rust-side validation before crossing the FFI boundary.
    pub fn safe_c_strlen(s: &str) -> usize {
        // We use Rust's built-in — no FFI needed for this.
        // In a real FFI scenario:
        //   extern "C" { fn strlen(s: *const i8) -> usize; }
        //   // SAFETY: s is valid UTF-8 with a null terminator
        //   unsafe { strlen(s.as_ptr() as *const i8) }
        //
        // The key: validate ALL inputs before passing to C.
        // C doesn't know about Rust's guarantees.
        s.len()
    }
}

/// StackFrameSizeInspection: Shows how Rust's compiler manages stack frames.
///
/// Unlike C, where the programmer implicitly defines frame size by declaring
/// locals, Rust's ownership system means variables can be moved OUT of the
/// frame when no longer needed (compiler optimization).
#[inline(never)]  // Prevent inlining — keeps frame visible in profile
pub fn demonstrate_stack_frame_sizes() {
    // Large stack allocation — compiler knows this is 64 bytes
    let buf = StackBuffer::new();
    let addr = buf.data.as_ptr();

    println!("[frame] StackBuffer starts at: {:p}", addr);
    println!("[frame] Size of StackBuffer: {} bytes", std::mem::size_of::<StackBuffer>());

    // buf is dropped here — stack frame reclaimed
    // No manual free(), no destructor pitfalls
    drop(buf);
    // Attempting to use buf after drop is a COMPILE-TIME ERROR
}

fn main() {
    println!("=== Rust Stack Safety Demo ===\n");

    // Demonstrate safe buffer operations
    let mut buf = StackBuffer::new();

    match buf.write(b"Hello, Rust!") {
        Ok(()) => println!("[safe write] Success: {:?}", buf.as_slice()),
        Err(e) => eprintln!("[safe write] Error: {}", e),
    }

    // Demonstrate overflow detection
    let oversized = vec![0xAAu8; BUFFER_CAPACITY + 1];
    match buf.write(&oversized) {
        Ok(()) => println!("[overflow write] Unexpectedly succeeded!"),
        Err(e) => println!("[overflow write] Correctly rejected: {}", e),
    }

    rust_prevents_dangling();
    bounds_check_demo();
    demonstrate_stack_frame_sizes();

    println!("\nAll Rust safety guarantees verified.");
}

/// Tests: Rust's type system is verified by the compiler on every build.
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exact_capacity_write_succeeds() {
        let mut buf = StackBuffer::new();
        let exact = vec![0x41u8; BUFFER_CAPACITY];
        assert_eq!(buf.write(&exact), Ok(()));
        assert_eq!(buf.len, BUFFER_CAPACITY);
    }

    #[test]
    fn test_overflow_returns_error_not_panic() {
        let mut buf = StackBuffer::new();
        let oversized = vec![0x41u8; BUFFER_CAPACITY + 1];
        assert_eq!(
            buf.write(&oversized),
            Err(BufferError::InputTooLarge {
                input_len: BUFFER_CAPACITY + 1,
                capacity: BUFFER_CAPACITY,
            })
        );
    }

    #[test]
    fn test_empty_input_is_rejected() {
        let mut buf = StackBuffer::new();
        assert_eq!(buf.write(b""), Err(BufferError::EmptyInput));
    }

    #[test]
    fn test_buffer_not_corrupted_after_failed_write() {
        let mut buf = StackBuffer::new();
        buf.write(b"original").unwrap();
        let _ = buf.write(&vec![0x41u8; BUFFER_CAPACITY + 1]);  // Should fail
        assert_eq!(buf.as_slice(), b"original");  // Original data intact
    }
}
```

### 14.4 Rust Compiler Flags for Stack Safety

```bash
# Enable stack probes (detect stack overflow before it corrupts memory)
RUSTFLAGS="-C target-feature=+stack-probe" cargo build

# Use abort on panic (no unwinding — simpler, faster, no stack corruption
# possible during unwind)
# In Cargo.toml:
# [profile.release]
# panic = "abort"

# Address sanitizer (nightly only)
RUSTFLAGS="-Z sanitizer=address" cargo +nightly build --target x86_64-unknown-linux-gnu

# Enable overflow checks in release mode (default: on in debug, off in release)
RUSTFLAGS="-C overflow-checks=yes" cargo build --release

# Control stack size for the main thread
# RUST_MIN_STACK=8388608 ./binary   # 8MB

# Show generated assembly
cargo rustc -- --emit=asm
cat target/debug/deps/*.s | grep -A 30 "stack_chk"
```

### 14.5 Does Rust Use Stack Canaries?

```
Short answer: Sometimes, for specific targets.

Long answer:
  Rust's primary defense is compile-time correctness — if the code compiles,
  most stack overflow classes are impossible in safe code.

  For FFI-heavy code or embedded targets, rustc can emit stack canaries:
  - On Linux targets with glibc: rustc uses __stack_chk_guard (same as C)
  - On targets requiring it (e.g., some embedded): rustc links to libcompiler-builtins
    which provides __stack_chk_fail

  Check if your binary uses canaries:
    nm target/release/binary | grep stack_chk

  For most pure Rust code, canaries are a redundant fallback because
  the ownership/bounds-check model prevents the underlying vulnerability.
```

---

## 15. Attack Techniques and Why Canaries Are Not Enough

### 15.1 Canary Bypass Technique 1: Information Leak

If the attacker can read the canary value (e.g., via a format string bug, an out-of-bounds read, or a memory disclosure), they can include it in their overflow payload:

```
Normal overflow (fails):
  [junk 64 bytes] [wrong canary] [junk 8 bytes] [attacker addr]
                        ↑ detected

Informed overflow (succeeds):
  [junk 64 bytes] [CORRECT canary] [junk 8 bytes] [attacker addr]
                        ↑ not detected
```

Defense: Combine canary with ASLR (so leaked canary doesn't help with address), CFI (so even a valid canary doesn't allow arbitrary jumps).

### 15.2 Canary Bypass Technique 2: Overwrite Non-Stack Data

The canary only protects the return address. An attacker can target:

```
  Function pointers stored as local variables:
    void (*handler)(void) = default_handler;
    char buf[64];
    // Overflow buf → overwrite handler → call handler() → arbitrary execution
    // Canary is between buf and RETURN ADDRESS, not between buf and handler!

  Heap-based overflow → heap metadata corruption
  Format string → write to arbitrary address
  Use-after-free → overwrite function pointer in object
```

Defense: `-fstack-protector-strong` rearranges the frame so dangerous arrays are below ALL locals. Function pointers are placed above (higher address than) the buffer.

### 15.3 Canary Bypass Technique 3: Brute Force (fork() servers)

If the server forks for each connection, the child inherits the parent's memory — including the canary. An attacker can brute-force one byte at a time:

```
Strategy:
  1. Send payload with canary byte 0 = 0x00, observe crash or no-crash
  2. If crash: try 0x01, 0x02, ... until no crash (correct byte found)
  3. Repeat for each byte of the 8-byte canary
  4. After 256*8 = 2048 attempts, canary is known (not killed because fork)
```

Defense: Re-randomize canary after fork (glibc does this for `posix_spawn` but not plain `fork`). Use process-level isolation.

### 15.4 Canary Bypass Technique 4: Return-Oriented Programming (ROP)

Even with a correct canary in the payload, the attacker redirects execution to existing code gadgets. This does not require shellcode and works even with NX/DEP.

```
ROP Chain:
  [padding] [correct canary] [junk] [gadget1 addr] [gadget2 addr] ...

Each gadget:
  pop rdi; ret    ← sets argument register
  pop rsi; ret    ← sets argument register
  ...
  call system     ← calls system("/bin/sh")
```

Defense: CFI (Control Flow Integrity) — validates that indirect jumps/calls go to valid targets. Shadow Stack (Intel CET) — validates that RET goes to the address pushed by the matching CALL.

---

## 16. Complementary Defenses — The Full Picture

### 16.1 Defense in Depth Matrix

```
Threat                          | Canary | NX/DEP | ASLR  | CFI   | Shadow Stack
─────────────────────────────────┼────────┼────────┼───────┼───────┼─────────────
Stack overflow → shellcode       | ✓      | ✓      | ✓     | ✓     | ✓
Stack overflow → ROP             | ✓*     | ✗      | ✓*    | ✓     | ✓
Stack overflow → ret2libc        | ✓      | ✗      | ✓     | ✓     | ✓
Format string info leak          | ✗      | ✗      | ✗     | ✗     | ✗
Heap overflow → func ptr         | ✗      | ✓      | ✓     | ✓     | ✗
Use-after-free                   | ✗      | ✓      | ✓     | ✓     | ✗
Type confusion                   | ✗      | ✓      | ✓     | ✓     | ✗

* = Partial defense
```

### 16.2 Intel CET — Hardware Shadow Stack

The most powerful modern defense. Available on Intel Tiger Lake+ and AMD Zen 3+:

```
Hardware Shadow Stack:
  - A second stack, managed by the CPU, inaccessible to software in ring 3
  - CALL pushes the return address to BOTH the normal stack AND shadow stack
  - RET pops from both; if they don't match → CPU fault → immediate termination
  - No software can forge a shadow stack entry (requires ring 0 WRSS instruction)
  - Completely transparent to existing code (no recompile needed for basic IBT)

Linux kernel support: CONFIG_X86_USER_SHADOW_STACK (kernel 6.6+)
glibc support: 2.39+
```

### 16.3 FORTIFY_SOURCE

```bash
gcc -D_FORTIFY_SOURCE=2 -O1 -fstack-protector-strong
```

`FORTIFY_SOURCE` replaces dangerous functions (`strcpy`, `sprintf`, `memcpy`) with checked versions that know the destination buffer size (determined at compile time or via `__builtin_object_size`).

```c
// With FORTIFY_SOURCE=2:
char buf[64];
strcpy(buf, input);
// → becomes: __strcpy_chk(buf, input, 64);
// → if strlen(input) >= 64: __chk_fail() is called
// This is a COMPILE-TIME or EARLY-RUNTIME check, before overflow happens.
// Complements the canary (canary is last resort; FORTIFY is early detection).
```

---

## 17. Performance Analysis

### 17.1 Canary Overhead Breakdown

```
Per-function overhead (protected function):

  Prologue additions:
    mov rax, QWORD PTR fs:0x28    ; 1 cycle (TLS cached in L1)
    mov [rbp-8], rax              ; 1 cycle (stack write, cache hot)
    xor eax, eax                  ; 1 cycle (zero rax for security)
    Total prologue: ~3 cycles

  Epilogue additions:
    mov rax, [rbp-8]              ; 1 cycle
    xor rax, QWORD PTR fs:0x28   ; 1 cycle
    je  .ok                       ; 0 cycles (predicted taken)
    Total epilogue: ~2-3 cycles

Total per-call overhead: ~5-6 cycles

At 1 GHz call rate (1 billion function calls/sec, extreme case):
  5 cycles × 1GHz = 5ns extra per call
  For 10ns average function duration: 50% overhead (pathological case)
  For 1μs average function duration:  0.5% overhead (typical case)
```

### 17.2 Cache Behavior of TLS Canary Access

```
fs:0x28 access:
  - fs points to the TCB (Thread Control Block) in per-thread memory
  - The TCB is accessed very frequently (TLS variables, errno, etc.)
  - It lives in L1 data cache (virtually guaranteed for active threads)
  - Access latency: ~4 cycles (L1 hit) vs 200+ cycles (DRAM)
  
  Result: The canary read/write is effectively free in cache-warm code.
  The overhead in benchmarks comes from:
    1. Increased frame size (slightly more stack pressure)
    2. Extra RSP adjustment (allocation of canary slot)
    3. Branch misprediction budget (the cmp+je in epilogue)
```

### 17.3 Measuring Real Overhead

```bash
# Create two identical programs — one protected, one not
gcc -O2 -fno-stack-protector  -o bench_unsafe bench.c
gcc -O2 -fstack-protector-strong -o bench_safe   bench.c

# Use perf to measure
perf stat -e cycles,instructions,cache-misses ./bench_unsafe
perf stat -e cycles,instructions,cache-misses ./bench_safe

# Typical result for a realistic workload:
# Overhead: 0.1% to 3% depending on function call density
# Hot loops with function calls: up to 5-8% in extreme cases
```

### 17.4 Compiler Optimization Interactions

```
Stack protector interacts with:

1. INLINING:
   Inlined functions do not get their own frame → no canary needed.
   -fstack-protector-strong + heavy inlining = fewer protections needed.
   LTO (Link-Time Optimization) increases inlining → further reduces overhead.

2. TAIL CALL OPTIMIZATION:
   A tail call reuses the caller's frame → no new frame → no new canary.
   Canary check happens once in the merged epilogue.

3. LEAF FUNCTIONS:
   Leaf functions (no function calls) don't need to save registers.
   -fstack-protector (not -strong) often skips them if no arrays.
   Reduces protection coverage but also reduces overhead in hot inner loops.

4. REGISTER ALLOCATION:
   The extra local variable (canary slot) slightly reduces available
   registers, potentially causing register spills → slight overhead.
```

---

## 18. Verification and Auditing

### 18.1 Verifying Stack Protection at Build Time

```bash
# Method 1: Check compiler flags in your build system
cmake -DCMAKE_C_FLAGS="-fstack-protector-strong" ..
# Or for Cargo (Rust):
# RUSTFLAGS="-C target-feature=+stack-guard" cargo build

# Method 2: Inspect the binary (ELF)
readelf -s binary | grep stack_chk_guard    # should appear in .dynsym
objdump -d binary | grep -c "fs:0x28"       # count canary accesses

# Method 3: checksec (hardening checker)
pip install checksec.py
checksec --file=binary

# Method 4: pwn (pwntools)
python3 -c "
from pwn import *
e = ELF('./binary')
print('Canary:', e.canary)
print('NX:', e.nx)
print('PIE:', e.pie)
"
```

### 18.2 Verifying Kernel Stack Protection

```bash
# Check kernel config
grep "STACKPROTECTOR" /boot/config-$(uname -r)
# Expected:
# CONFIG_STACKPROTECTOR=y
# CONFIG_STACKPROTECTOR_STRONG=y

# Check VMAP_STACK
grep "VMAP_STACK" /boot/config-$(uname -r)
# CONFIG_VMAP_STACK=y

# Check at runtime
zcat /proc/config.gz | grep STACK
# (if CONFIG_IKCONFIG_PROC=y)

# View kernel canary address (root only)
cat /proc/kallsyms | grep stack_canary
# or
sudo grep __stack_chk_guard /proc/kallsyms

# Check KASLR
dmesg | grep -i kaslr
# [ 0.000000] KASLR enabled
```

### 18.3 Security Audit Checklist for C Code

```
COMPILATION FLAGS:
  [ ] -fstack-protector-strong (or -strong for production)
  [ ] -D_FORTIFY_SOURCE=2
  [ ] -Wformat -Wformat-security
  [ ] -pie -fPIE (enable ASLR)
  [ ] -Wl,-z,relro -Wl,-z,now (RELRO)

SOURCE CODE:
  [ ] No unbounded string operations (strcpy, sprintf, gets — NEVER)
  [ ] All buffer operations use sized variants (strncpy, snprintf, fgets)
  [ ] Input lengths validated BEFORE buffer operations
  [ ] Integer overflow checks before using result as buffer size
  [ ] alloca() avoided or bounded (use VLAs cautiously)

RUNTIME:
  [ ] ASLR enabled: cat /proc/sys/kernel/randomize_va_space (should be 2)
  [ ] NX enabled: check /proc/PID/smaps for non-exec stack
  [ ] Core dump settings: consider restricting (setuid programs)
```

---

## 19. Expert Mental Models

### 19.1 The Attacker's Perspective Mental Model

Before implementing any security control, think like the attacker:

```
ATTACKER'S DECISION TREE:

Can I find a buffer overflow?
  └─ YES → Is there a canary?
               ├─ NO  → Directly overwrite return address
               └─ YES → Can I leak the canary?
                            ├─ YES → Include correct canary in payload
                            └─ NO  → Can I overflow non-stack targets?
                                        ├─ YES → Target function pointers, vtables
                                        └─ NO  → Is there ASLR?
                                                    ├─ NO  → Use ROP with known addresses
                                                    └─ YES → Can I leak addresses?
                                                               └─ Loop back to leaks
```

Every defense you add forces the attacker one branch deeper into this tree, requiring more skill and more information. Defense in depth means there is no short path to exploitation.

### 19.2 The Trust Boundary Mental Model

```
The stack canary creates a TRUST BOUNDARY within the stack frame:

  BELOW THE CANARY (lower addresses):
    → Untrusted zone: attacker-influenced data lives here
    → Assume corrupt
    → Bounds-check everything

  ABOVE THE CANARY (higher addresses):
    → Protected zone: control flow data lives here
    → Canary guards the crossing
    → The moment the crossing is detected, process dies
```

Apply this model to any security mechanism: identify the trust boundary, ensure the sentinel is at the correct crossing point, and verify the sentinel is checked at the right time.

### 19.3 Cognitive Model: Compile-Time vs. Runtime Defense

```
                 ┌─────────────────────────────────────────┐
   COMPILE-TIME  │  Rust type system, borrow checker,       │  BEST
   (Zero cost)   │  lifetime system, const bounds           │  (catch at source)
                 ├─────────────────────────────────────────┤
   LINK-TIME     │  FORTIFY_SOURCE checked variants,        │
                 │  LTO-enabled inlining                    │
                 ├─────────────────────────────────────────┤
   LOAD-TIME     │  ASLR (randomize layout),                │
                 │  PIE (position-independent executable)   │
                 ├─────────────────────────────────────────┤
   EARLY RUNTIME │  FORTIFY_SOURCE runtime checks,          │
                 │  Go bounds checking, length validation    │
                 ├─────────────────────────────────────────┤
   LATE RUNTIME  │  Stack canary (last line of defense),    │  LAST RESORT
   (Detection)   │  Shadow stack (hardware)                 │  (catch at explosion)
                 └─────────────────────────────────────────┘
```

Push defenses as early in this stack as possible. The canary is a last resort, not a first line. Rust operates at the top. C relies heavily on the bottom.

### 19.4 Deliberate Practice Application

To master this topic, follow this progression:

```
WEEK 1 — Build the intuition:
  □ Compile the C demo above with and without -fstack-protector-strong
  □ Run objdump on both — find the fs:0x28 instructions
  □ Trigger the canary manually (--trigger-overflow flag)
  □ Read the kernel source: arch/x86/include/asm/stackprotector.h

WEEK 2 — Attack perspective:
  □ Study basic buffer overflow exploitation (pwn.college, Protostar)
  □ Understand why strcpy is dangerous at the assembly level
  □ Trace a stack overflow byte-by-byte in GDB

WEEK 3 — Defense perspective:
  □ Audit a real open-source C project for unsafe buffer operations
  □ Implement the custom canary (Section 12.3) for an ARM bare-metal target
  □ Write the Rust equivalent and observe what the type system catches

WEEK 4 — Systems integration:
  □ Configure a Linux kernel with all stack protection options enabled
  □ Verify with checksec, objdump, and /proc/config.gz
  □ Write a kernel module and verify its stack protection level
```

### 19.5 The Meta-Principle

> **Security is not a feature you add at the end. It is a property that emerges from correct reasoning at every level — from the instruction set architecture, through the OS kernel, through the compiler, through the type system, through the code. Stack Protector is one sentinel in a chain. Understanding why each sentinel exists, what it can and cannot detect, and how they compose is what separates a practitioner from an expert.**

The canary does not make your code safe. Correct code, in a memory-safe language, with bounded operations, verified at compile time — that makes your code safe. The canary catches what correctness missed.

---

## Summary Reference Card

```
┌──────────────────────┬────────────────────────────────────┬────────────┐
│ Compiler Flag        │ Protection                         │ Overhead   │
├──────────────────────┼────────────────────────────────────┼────────────┤
│ -fstack-protector    │ char arrays >= 8 bytes             │ Minimal    │
│ -fstack-protector-   │ All arrays, address-taken vars     │ Low        │
│   strong             │ (RECOMMENDED)                      │            │
│ -fstack-protector-   │ Every function                     │ Moderate   │
│   all                │                                    │            │
│ -fstack-clash-       │ Guard page probe injection         │ Minimal    │
│   protection         │                                    │            │
│ -D_FORTIFY_SOURCE=2  │ Bounded libc function calls        │ Minimal    │
│ -fsanitize=safe-     │ Separate safe/unsafe stacks        │ Low-Med    │
│   stack (Clang)      │ (Clang only)                       │            │
├──────────────────────┼────────────────────────────────────┼────────────┤
│ Kernel Config        │ Protection                         │            │
├──────────────────────┼────────────────────────────────────┼────────────┤
│ STACKPROTECTOR_STRONG│ Kernel functions protected         │ Low        │
│ VMAP_STACK           │ Guard pages around kernel stack    │ Minimal    │
│ STACKLEAK            │ Zero stack before return to user   │ Low-Med    │
│ KASAN                │ Full shadow memory (debug)         │ ~2x        │
│ SHADOW_CALL_STACK    │ HW shadow stack (AArch64)          │ Minimal    │
├──────────────────────┼────────────────────────────────────┼────────────┤
│ Language             │ Primary Defense                    │ Model      │
├──────────────────────┼────────────────────────────────────┼────────────┤
│ C                    │ Canary + FORTIFY + NX + ASLR       │ Runtime    │
│ Go                   │ Growing goroutine stacks + GC      │ Runtime    │
│ Rust                 │ Ownership + bounds checks          │ Compile    │
└──────────────────────┴────────────────────────────────────┴────────────┘
```

---

*This guide was written for systematic mastery. Return to it as your skills deepen — the same concepts reveal new layers at each level of understanding.*

Now let me build the comprehensive guide:Here is a high-level map of what the guide covers, so you can navigate it with intent:

**Foundations → Attack → Defense → Verification**

The guide is structured in four logical arcs:

**Arc 1 — Hardware Reality (Sections 2–5).** Every term is defined before use. You get the x86-64 ABI frame layout at the byte level — exactly where RSP, RBP, the return address, and the buffer sit in memory, and *why* a linear overflow from a low-address buffer walks directly into the return address.

**Arc 2 — The Defense Mechanism (Sections 6–9).** The canary's properties (null byte, TLS storage at `fs:0x28`, per-process randomness), how the compiler transformation pipeline works, all GCC flags compared by coverage and cost, and Clang's `SafeStack` and `ShadowCallStack` extensions.

**Arc 3 — Linux Kernel Specifics (Sections 10–11).** This is where most guides stop — this one doesn't. You get the `irq_stack_union`, `boot_init_stack_canary()`, `gs:40` (kernel uses `gs`, not `fs`), `VMAP_STACK` guard pages, `STACKLEAK`, KASLR, SMEP, SMAP, and how a canary failure in kernel space causes a full system panic rather than a process signal.

**Arc 4 — Language Implementations (Sections 12–14).** Production-grade C with inline assembly to read the TLS canary directly. Go's goroutine stack growth mechanism at the assembly level. Rust's ownership system as compile-time stack protection, with the precise distinction between what Rust guarantees at compile time versus runtime, and where `unsafe` re-introduces C-level risk.

**Arc 5 — The Attacker's View and Completeness (Sections 15–18).** Four bypass techniques (info leak, non-stack targets, fork brute force, ROP), a defense-in-depth matrix, Intel CET shadow stack, and a full audit checklist.