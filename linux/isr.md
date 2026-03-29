# ═══════════════════════════════════════════════════════════════
#  INTERRUPT SERVICE ROUTINE (ISR) — COMPLETE COMPREHENSIVE GUIDE
#  From First Principles to Expert-Level Mastery
#  Languages: C · Rust · Go
# ═══════════════════════════════════════════════════════════════

---

## TABLE OF CONTENTS

```
 1. Mental Model Before We Begin
 2. What is an Interrupt? (First Principles)
 3. Why Interrupts Exist — The Problem They Solve
 4. Anatomy of the CPU Interrupt Mechanism
 5. Interrupt Vector Table (IVT)
 6. What is an ISR? (Interrupt Service Routine)
 7. Types of Interrupts
 8. Hardware Interrupts — Deep Dive
 9. Software Interrupts — Deep Dive
10. Exceptions & Faults — Deep Dive
11. Interrupt Lifecycle — Step by Step
12. Context Saving & Restoration
13. Interrupt Priority & Nesting
14. Interrupt Latency
15. Critical Sections & Atomicity
16. ISR Design Rules (Golden Rules)
17. Volatile & Memory Barriers
18. Deferred Work — Bottom Halves, Tasklets, Workqueues
19. ISR in C — Bare Metal & Linux
20. ISR in Rust — Embedded & Systems
21. ISR in Go — Signal Handling & Runtime
22. Real-World Examples
23. Common Pitfalls & Debugging
24. Advanced Topics
25. Mental Models & Cognitive Strategies
26. Summary Reference Card
```

---

## CHAPTER 1 — MENTAL MODEL BEFORE WE BEGIN

> *"Before you write a single line, build a map in your mind."*

### The Monk's Approach to Systems Programming

When learning interrupts, most people jump to code immediately.
The expert does the opposite: they first understand the **physical reality** of the
problem, then map it to abstractions, then finally touch the code.

**Chunking Strategy:** Break this topic into 3 mental chunks:

```
CHUNK 1: WHY does the CPU need interrupts at all?
CHUNK 2: HOW does the CPU mechanically respond to an interrupt?
CHUNK 3: WHAT does the programmer write inside the ISR?
```

Each chunk must be fully solid before moving to the next.
This is deliberate practice — depth before breadth.

---

## CHAPTER 2 — WHAT IS AN INTERRUPT? (FIRST PRINCIPLES)

### Vocabulary You Must Know Before Proceeding

| Term | Plain English Meaning |
|---|---|
| **CPU** | The processor — executes instructions one by one |
| **Program Counter (PC)** | A register that holds the address of the *next instruction* to execute |
| **Register** | A tiny, extremely fast storage slot inside the CPU (e.g., `rax`, `rsp`) |
| **Stack** | A region of memory that grows/shrinks like a pile of plates — LIFO |
| **Stack Pointer (SP)** | A register that always points to the "top" of the stack |
| **Peripheral** | External hardware device: keyboard, UART, timer, network card |
| **Bus** | Wires connecting CPU to memory and peripherals |
| **Polling** | CPU repeatedly asking "are you done yet?" in a loop |
| **Signal** | An electrical pulse sent on a wire to notify something happened |
| **Latency** | Delay between an event happening and the response beginning |
| **Atomicity** | An operation that cannot be interrupted — it's all-or-nothing |
| **Race Condition** | A bug caused by two things accessing shared data concurrently |
| **Context** | The complete CPU state (all registers) at a given moment |

---

### The Fundamental Problem: The World is Asynchronous

Imagine your CPU is executing a program. Suddenly, the user presses a key.

```
TIMELINE (without interrupts):

  CPU:  [task A] [task A] [task A] [task A] [task A] [task A]
  Key:              PRESSED!
                    ↑
              CPU doesn't know!
              It's busy running task A.
              The keypress is LOST.
```

The CPU has no way to know the key was pressed unless it **asks**.
This asking-in-a-loop is called **polling**.

```
POLLING APPROACH:

  while(true) {
      if (key_was_pressed()) handle_key();   // wastes 99.999% of CPU time
      do_work();
  }

  PROBLEM: CPU wastes enormous time checking "did something happen?"
           when nothing ever does.
```

**Interrupt is the solution:** Instead of the CPU asking the hardware,
the **hardware notifies the CPU** when something happens.

```
INTERRUPT APPROACH:

  CPU runs task A → hardware event → CPU pauses → runs ISR → resumes task A

  CPU:  [A][A][A][A][A]──interrupt──>[ISR][ISR][ISR]──return──>[A][A][A]
```

This is the entire philosophy. Everything else is implementation detail.

---

## CHAPTER 3 — WHY INTERRUPTS EXIST: THE PROBLEM THEY SOLVE

### Comparison: Polling vs Interrupts vs DMA

```
┌─────────────────────────────────────────────────────────────────┐
│                    POLLING vs INTERRUPTS vs DMA                 │
├─────────────────┬───────────────────┬───────────────────────────┤
│   POLLING       │   INTERRUPTS      │   DMA                     │
├─────────────────┼───────────────────┼───────────────────────────┤
│ CPU checks      │ Hardware notifies │ Hardware transfers data    │
│ device in a     │ CPU when ready.   │ directly to memory.       │
│ loop.           │ CPU then handles. │ CPU notified at end only. │
├─────────────────┼───────────────────┼───────────────────────────┤
│ Simple code     │ Complex but       │ Most efficient for bulk   │
│ Wastes CPU      │ efficient.        │ data (e.g., disk I/O)     │
│ High power use  │ Low latency.      │ Minimal CPU involvement   │
├─────────────────┼───────────────────┼───────────────────────────┤
│ OK for very     │ Best for most     │ Best for large transfers  │
│ fast devices    │ peripherals       │                           │
└─────────────────┴───────────────────┴───────────────────────────┘
```

### Real-World Analogy

```
POLLING:   You stand at the door every second asking "has the pizza arrived?"
INTERRUPT: You sit watching TV; the doorbell rings; you go to the door.
DMA:       The pizza delivery person has a key. They put the pizza in the fridge.
           You only get one notification: "pizza is in the fridge."
```

---

## CHAPTER 4 — ANATOMY OF THE CPU INTERRUPT MECHANISM

### The Physical Hardware Path of an Interrupt

```
┌──────────────────────────────────────────────────────────────────┐
│              HARDWARE INTERRUPT SIGNAL PATH                      │
│                                                                  │
│  ┌──────────┐   IRQ line    ┌──────────┐   INT line  ┌───────┐  │
│  │ DEVICE   │──────────────►│  PIC /   │────────────►│  CPU  │  │
│  │(keyboard,│               │  APIC    │             │       │  │
│  │ timer,   │               │(Interrupt│             │Checks │  │
│  │ UART...) │               │Controller│             │IF flag│  │
│  └──────────┘               └──────────┘             └───┬───┘  │
│                                   ▲                      │      │
│                                   │                      │      │
│                             CPU sends               CPU sends   │
│                             EOI signal              INTA signal │
│                             (End of                 (Interrupt  │
│                              Interrupt)              Acknowledge)│
└──────────────────────────────────────────────────────────────────┘
```

### Key Hardware Concepts

**IRQ (Interrupt ReQuest):** A dedicated wire/signal line from a device to the
interrupt controller. Each device typically has a fixed IRQ number.

```
  IRQ0  → System Timer (PIT/APIC Timer)
  IRQ1  → Keyboard Controller
  IRQ3  → COM2 Serial Port
  IRQ4  → COM1 Serial Port
  IRQ6  → Floppy Disk Controller
  IRQ8  → Real-Time Clock
  IRQ14 → Primary IDE/ATA
  IRQ15 → Secondary IDE/ATA
```

**PIC (Programmable Interrupt Controller):**
Old x86 hardware chip (Intel 8259A) that:
1. Collects IRQ signals from up to 8 devices
2. Arbitrates priority
3. Signals the CPU with the vector number

**APIC (Advanced PIC):**
Modern replacement for PIC. Supports:
- Multiple CPUs (multicore)
- Up to 255 interrupt vectors
- Local APIC per CPU core
- I/O APIC for routing device IRQs

**IF Flag (Interrupt Flag):**
A bit inside the CPU's FLAGS register.
- IF = 1: Hardware interrupts are **enabled** (CPU will respond)
- IF = 0: Hardware interrupts are **disabled** (CPU ignores IRQs)

```
  x86 instructions:
    CLI  → CLear Interrupt flag  (disable hardware interrupts)
    STI  → SeT Interrupt flag    (enable hardware interrupts)
```

---

## CHAPTER 5 — INTERRUPT VECTOR TABLE (IVT)

### What is a Vector?

The word **vector** here simply means **a pointer to a function** —
specifically, the address in memory where the ISR code begins.

When an interrupt occurs, the CPU needs to know: *"Which function should I run?"*
The answer comes from the **Interrupt Vector Table**.

### Structure of the IVT (x86 Real Mode)

```
MEMORY LAYOUT (x86 Real Mode — first 1KB of RAM):

  Address 0x0000:
  ┌─────────────────────────────────────────┐
  │ Vector  0: Divide-by-zero handler addr  │  ← 4 bytes (segment:offset)
  │ Vector  1: Single Step debugger addr    │
  │ Vector  2: NMI handler addr             │
  │ Vector  3: Breakpoint handler addr      │
  │ Vector  4: Overflow handler addr        │
  │ Vector  5: Bound Range handler addr     │
  │ Vector  6: Invalid Opcode handler addr  │
  │ Vector  7: Device Not Available addr    │
  │ Vector  8: Double Fault handler addr    │
  │    ...                                  │
  │ Vector 32: Timer IRQ handler addr       │  ← Hardware IRQs start here
  │ Vector 33: Keyboard IRQ handler addr    │
  │    ...                                  │
  │ Vector255: Last entry                   │
  └─────────────────────────────────────────┘
  Address 0x03FF (end of 1KB IVT)
```

### IDT (Interrupt Descriptor Table) — x86 Protected/Long Mode

In modern 32/64-bit mode, the IVT is replaced by the **IDT**.
Each entry (called a **gate descriptor**) is 8 or 16 bytes.

```
IDT ENTRY STRUCTURE (64-bit, 16 bytes):

  Bits 127:96 ┌──────────────────────┐
              │   Reserved           │
  Bits  95:64 ├──────────────────────┤
              │ Handler Addr [63:32] │  ← Upper 32 bits of ISR address
  Bits  63:48 ├────────┬─────────────┤
              │ Offset │  Reserved   │
              │[31:16] │             │
  Bits  47:40 ├────────┴─────────────┤
              │ P│DPL│0│Gate Type   │  ← P=Present, DPL=Privilege Level
  Bits  39:32 ├──────────────────────┤
              │     Reserved         │
  Bits  31:16 ├──────────────────────┤
              │  Segment Selector    │  ← Which code segment to use
  Bits  15: 0 ├──────────────────────┤
              │ Handler Addr [15:0]  │  ← Lower 16 bits of ISR address
              └──────────────────────┘

  IDTR register points to the base of IDT.
  LIDT instruction loads IDTR.
```

### ARM Cortex-M Vector Table

For embedded systems (ARM Cortex-M microcontrollers — most common in IoT/embedded):

```
ARM CORTEX-M VECTOR TABLE (in Flash, starts at 0x00000000):

  Offset 0x00: Initial Stack Pointer value
  Offset 0x04: Reset Handler address          ← After power-on
  Offset 0x08: NMI Handler address
  Offset 0x0C: HardFault Handler address
  Offset 0x10: MemManage Handler address
  Offset 0x14: BusFault Handler address
  Offset 0x18: UsageFault Handler address
  ...
  Offset 0x40: SysTick Handler address
  Offset 0x44: IRQ0 Handler address
  Offset 0x48: IRQ1 Handler address
  ...
  Offset 0x44 + 4*N: IRQN Handler address
```

---

## CHAPTER 6 — WHAT IS AN ISR? (INTERRUPT SERVICE ROUTINE)

### Precise Definition

An **Interrupt Service Routine (ISR)** is a special function that:
1. Is registered at a specific entry in the interrupt vector table
2. Is automatically called by the CPU hardware when the corresponding interrupt fires
3. Runs in a special context (no user process, often no scheduler)
4. Must complete quickly and return control to the interrupted code

### Alternative Names for ISR

```
  ISR         = Interrupt Service Routine   (most common)
  IH          = Interrupt Handler
  ISA         = Interrupt Service Algorithm
  IRQ handler = Interrupt Request handler   (Linux kernel term)
  Trap handler= Used for software interrupts / exceptions
  Fault handler = Used for CPU exceptions (divide by zero, page fault)
  Signal handler = User-space analog in POSIX systems
```

### ISR vs Regular Function — Critical Differences

```
┌────────────────────────────────────┬────────────────────────────────────┐
│        REGULAR FUNCTION            │         ISR                        │
├────────────────────────────────────┼────────────────────────────────────┤
│ Called by your code explicitly     │ Called by CPU hardware             │
│ Has parameters                     │ No parameters (or implicit)        │
│ Has return value                   │ Returns void (or uses IRET)        │
│ Uses standard calling convention   │ Uses special ISR calling convention│
│ Interrupts can fire during it      │ Often runs with interrupts disabled│
│ Can sleep / block                  │ MUST NOT sleep or block            │
│ Can call malloc / OS functions     │ MUST NOT call blocking OS funcs    │
│ Can take as long as needed         │ Must be as short as possible       │
│ Stack usage is flexible            │ Stack is often tiny — be careful   │
│ Compiled normally                  │ Needs special attributes/annotations│
└────────────────────────────────────┴────────────────────────────────────┘
```

---

## CHAPTER 7 — TYPES OF INTERRUPTS

### The Full Taxonomy

```
                    ALL INTERRUPTS
                         │
          ┌──────────────┴──────────────┐
          │                             │
    HARDWARE                        SOFTWARE
    INTERRUPTS                      INTERRUPTS
          │                             │
    ┌─────┴──────┐               ┌──────┴──────┐
    │            │               │             │
 MASKABLE    NON-MASKABLE     TRAPS /       SYSTEM
 (IRQ)       (NMI)           EXCEPTIONS    CALLS
    │                            │
┌───┴───┐                  ┌─────┴────┐
│ Timer │               FAULTS    ABORTS
│ UART  │               (page       │
│ USB   │                fault,  ┌──┴──────┐
│ GPIO  │                GPF)    │ Machine │
│ etc.  │                        │  Check  │
└───────┘                        └─────────┘
```

### Type 1: Maskable Hardware Interrupts (IRQs)

**Maskable** = can be disabled by software (via CLI instruction or clearing IF flag).

```
  SOURCE:  External hardware device
  TRIGGER: Rising/falling edge or level on IRQ line
  CAN DISABLE: YES (CLI instruction)
  EXAMPLES:
    - Timer tick (IRQ0 on x86)
    - Keyboard press (IRQ1)
    - Serial data received (COM1=IRQ4)
    - Network packet arrived
    - USB event
    - GPIO pin change (on microcontrollers)
```

### Type 2: Non-Maskable Interrupts (NMI)

**Non-maskable** = the CPU **cannot** ignore it, no matter what.
Used for critical hardware failures.

```
  SOURCE:  Special NMI pin on CPU
  TRIGGER: Serious hardware error
  CAN DISABLE: NO
  EXAMPLES:
    - Memory parity error (RAM corruption)
    - Bus error
    - Watchdog timer expiry (embedded)
    - Power failure warning
    - Hardware debugger (JTAG)
  
  RESPONSE: Log error, attempt recovery, or trigger system halt.
```

### Type 3: Exceptions / Faults / Traps / Aborts

These are generated by the **CPU itself** when it detects an error or special condition
during instruction execution.

```
┌─────────────────────────────────────────────────────────────────┐
│                  CPU EXCEPTION TYPES                            │
├──────────────┬─────────────────────────────────────────────────┤
│ FAULT        │ Recoverable error. PC saved to FAULTING          │
│              │ instruction (so it can retry).                   │
│              │ Example: Page Fault (#PF) — OS loads page,       │
│              │ restarts the instruction. Memory works!          │
├──────────────┼─────────────────────────────────────────────────┤
│ TRAP         │ Intentional exception. PC saved to NEXT          │
│              │ instruction. Execution continues after handler.  │
│              │ Example: INT 3 (breakpoint), INT 0x80 (syscall)  │
├──────────────┼─────────────────────────────────────────────────┤
│ ABORT        │ Unrecoverable. Cannot determine where PC was.    │
│              │ System must halt or reset.                       │
│              │ Example: Double Fault (#DF), Machine Check (#MC) │
└──────────────┴─────────────────────────────────────────────────┘
```

### x86 Exception Table (First 32 vectors — reserved by Intel)

```
  Vector  0: #DE  Divide Error (Fault)
  Vector  1: #DB  Debug Exception (Fault/Trap)
  Vector  2: ---  NMI Interrupt
  Vector  3: #BP  Breakpoint (Trap)           ← INT 3
  Vector  4: #OF  Overflow (Trap)
  Vector  5: #BR  BOUND Range Exceeded (Fault)
  Vector  6: #UD  Invalid Opcode (Fault)
  Vector  7: #NM  Device Not Available (Fault)
  Vector  8: #DF  Double Fault (Abort)
  Vector 10: #TS  Invalid TSS (Fault)
  Vector 11: #NP  Segment Not Present (Fault)
  Vector 12: #SS  Stack Segment Fault (Fault)
  Vector 13: #GP  General Protection (Fault)
  Vector 14: #PF  Page Fault (Fault)          ← Most common! OS uses this
  Vector 16: #MF  x87 FPU Error (Fault)
  Vector 17: #AC  Alignment Check (Fault)
  Vector 18: #MC  Machine Check (Abort)
  Vector 19: #XM  SIMD FP Exception (Fault)
  Vectors 32-255: User-defined (hardware IRQs, software interrupts)
```

### Type 4: Software Interrupts

Triggered by the CPU executing a specific instruction.
Used as the interface between user programs and the OS kernel.

```
  x86:    INT n        (e.g., INT 0x80 for Linux syscalls on 32-bit)
  x86-64: SYSCALL      (faster, modern replacement for INT 0x80)
  ARM:    SVC (Supervisor Call), previously SWI (Software Interrupt)
  RISC-V: ECALL        (Environment Call)

  FLOW:
  User Program
      │
      │  executes INT 0x80 / SYSCALL
      ▼
  CPU switches to kernel mode (Ring 0)
      │
      ▼
  Kernel ISR (syscall handler) runs
      │
      ▼
  Returns to user mode with result
```

---

## CHAPTER 8 — HARDWARE INTERRUPTS: DEEP DIVE

### The Complete x86 Hardware Interrupt Flow (Step by Step)

```
┌─────────────────────────────────────────────────────────────────┐
│         HARDWARE INTERRUPT — COMPLETE FLOW DIAGRAM              │
│                                                                 │
│  ① Device asserts IRQ line                                      │
│         │                                                       │
│         ▼                                                       │
│  ② PIC/APIC receives IRQ, checks priority                       │
│         │                                                       │
│         ▼                                                       │
│  ③ PIC signals CPU: raises INT pin                              │
│         │                                                       │
│         ▼                                                       │
│  ④ CPU finishes CURRENT instruction (never mid-instruction)     │
│         │                                                       │
│         ▼                                                       │
│  ⑤ CPU checks IF flag (Interrupt Flag in EFLAGS/RFLAGS)        │
│         │                                                       │
│         ├──── IF=0 ──────────────────────────────────────────► │
│         │     (interrupts disabled)  CPU ignores → goes back   │
│         │                            to normal execution        │
│         │                                                       │
│         └──── IF=1 ──────►                                      │
│                (interrupts enabled)  Continue below             │
│                                                                 │
│  ⑥ CPU sends INTA (Interrupt Acknowledge) to PIC               │
│         │                                                       │
│         ▼                                                       │
│  ⑦ PIC responds with vector number on data bus                  │
│         │                                                       │
│         ▼                                                       │
│  ⑧ CPU saves context to stack:                                  │
│     PUSH RFLAGS (flags register)                                │
│     PUSH CS     (code segment)                                  │
│     PUSH RIP    (return address = next instruction)             │
│     [+ error code for some exceptions]                          │
│         │                                                       │
│         ▼                                                       │
│  ⑨ CPU clears IF flag (disables further hardware interrupts)    │
│         │                                                       │
│         ▼                                                       │
│  ⑩ CPU indexes into IDT using vector number                     │
│     IDT[vector] → gate descriptor → ISR address                 │
│         │                                                       │
│         ▼                                                       │
│  ⑪ CPU jumps to ISR address — ISR begins executing              │
│         │                                                       │
│         ▼                                                       │
│  ⑫ ISR does its work (minimal, fast)                            │
│         │                                                       │
│         ▼                                                       │
│  ⑬ ISR sends EOI (End Of Interrupt) to PIC                      │
│         │  outb(0x20, 0x20) for primary PIC                     │
│         ▼                                                       │
│  ⑭ ISR executes IRET (Interrupt Return)                         │
│         │                                                       │
│         ▼                                                       │
│  ⑮ CPU pops RIP, CS, RFLAGS from stack                          │
│     IF flag is restored (interrupts re-enabled)                 │
│         │                                                       │
│         ▼                                                       │
│  ⑯ CPU resumes interrupted program exactly where it left off    │
└─────────────────────────────────────────────────────────────────┘
```

---

## CHAPTER 9 — SOFTWARE INTERRUPTS: DEEP DIVE

### The System Call Path (Linux x86-64)

```
USER SPACE:                              KERNEL SPACE:
                                         
  write(fd, buf, n)                      
  ↓                                      
  C library (glibc)                      
  ↓                                      
  mov rax, 1    ← syscall number         
  mov rdi, fd   ← arg 1                  
  mov rsi, buf  ← arg 2                  
  mov rdx, n    ← arg 3                  
  SYSCALL       ← triggers interrupt     ──────────────────────────►
                                          sys_write() in kernel
                                          ↓
                                          VFS layer
                                          ↓
                                          file driver
                                          ↓
                                          actual write
                                          ↓
                                         SYSRET ◄──────────────────
  ↓
  return value in rax
```

### ARM SVC (Supervisor Call) — Cortex-M

```
  SVC #0          ; Software interrupt, SVC number 0
  
  CPU does:
  1. Save PC, PSR to stack (hardware stacking)
  2. Enter Handler Mode (privileged)
  3. Jump to SVC_Handler
  
  SVC_Handler:
  - Read SVC number from instruction encoding
  - Dispatch to correct OS service
  - BKPT or BX LR to return
```

---

## CHAPTER 10 — EXCEPTIONS & FAULTS: DEEP DIVE

### The Page Fault — Most Important Exception

The page fault (#PF, vector 14) is the cornerstone of virtual memory.
Understanding it reveals how OSes implement:
- Lazy memory allocation (malloc doesn't actually allocate RAM immediately)
- Memory-mapped files (mmap)
- Copy-on-write (fork())
- Swapping (paging to disk)

```
PAGE FAULT FLOW:

  Program accesses address 0xDEADBEEF
         │
         ▼
  CPU checks Page Table Entry (PTE) for that address
         │
  ┌──────┴──────┐
  │  Present?   │
  └──────┬──────┘
         │
    YES  │  NO
    (OK) │  (page not in RAM)
         │         │
         │         ▼
         │   #PF fires! → CR2 register = faulting address
         │               CR3 register = page table base
         │         │
         │         ▼
         │   OS Page Fault Handler:
         │    1. Check: is this address valid for this process?
         │         ├── NO → SIGSEGV → program crashes
         │         └── YES → continue
         │    2. Allocate physical page frame
         │    3. Load data (from swap/file if needed)
         │    4. Update PTE: set Present bit, Physical addr
         │    5. IRET — CPU retries the SAME instruction!
         │         │
         ▼         ▼
  Access succeeds transparently
```

### The Double Fault

If a fault occurs **inside a fault handler**, it becomes a Double Fault (#DF).
If another fault occurs inside the Double Fault handler → Triple Fault → CPU reset!

```
  Fault in main code
       ↓
  #PF handler starts
       ↓ (another fault during #PF handling, e.g., stack overflow)
  #DF (Double Fault) handler
       ↓ (another fault here)
  Triple Fault → CPU resets (or shuts down)
  
  OS kernels use a separate stack (TSS — Task State Segment)
  for the #DF handler to prevent the triple fault loop.
```

---

## CHAPTER 11 — INTERRUPT LIFECYCLE: STEP BY STEP

### The Golden Path (ARM Cortex-M, Most Common in Embedded)

```
NORMAL EXECUTION                ISR EXECUTION
═════════════════               ═════════════

  main() {                      void UART_IRQHandler(void) {
    do_work_A();                  // We are here!
    do_work_B();  ◄── interrupted // Handle UART event
    do_work_C();                  // MUST finish fast!
  }                             }

TIMELINE:
  ─────────────────────────────────────────────────────────────────►
  
  [main][main][main]──IRQ──>[HW saves regs]─>[ISR]──[HW restores]──>[main]
  
  ├─────────────────┤        ├─────────────┤  ├──┤  ├────────────┤  ├────┤
  Normal execution   Hardware              ISR   Hardware           Resume
                     entry                runs   exit
                     sequence                    sequence
```

### ARM Cortex-M Hardware Stacking (Automatic Context Save)

When an interrupt fires on Cortex-M, the hardware automatically pushes
8 registers onto the current stack **before** calling the ISR:

```
STACK CONTENTS AFTER HARDWARE STACKING:

  Higher address: ┌─────────────────┐
                  │   xPSR          │  ← Program Status Register
                  │   PC (return)   │  ← Return address
                  │   LR (link reg) │  ← Link Register
                  │   R12           │  ← Scratch registers
                  │   R3            │
                  │   R2            │
                  │   R1            │
  Lower address:  │   R0            │  ← SP points here
                  └─────────────────┘
  
  Note: R4-R11 are NOT auto-saved. If your ISR uses them,
        YOU must save/restore them manually (or compiler does it).

  EXC_RETURN value is loaded into LR.
  When ISR executes BX LR, hardware unstacks automatically.
```

---

## CHAPTER 12 — CONTEXT SAVING & RESTORATION

### What "Context" Means

**Context** = the complete snapshot of CPU state at a moment in time.
For the interrupted program to resume correctly, every register it
was using must be restored to **exactly** what it was before the interrupt.

```
CPU REGISTER STATE (x86-64):

  General Purpose:   RAX, RBX, RCX, RDX, RSI, RDI, RBP
                     R8, R9, R10, R11, R12, R13, R14, R15
  Stack:             RSP (stack pointer)
  Instruction:       RIP (instruction pointer / program counter)
  Flags:             RFLAGS
  Segment:           CS, DS, SS, ES, FS, GS
  FPU/SSE:           XMM0-XMM15, MXCSR (floating point state)
  Debug:             DR0-DR7
  Control:           CR0, CR2, CR3, CR4

  TOTAL: Dozens of registers — all must be preserved!
```

### Calling Convention and Caller/Callee Saved Registers

In the x86-64 System V ABI (Linux):

```
  CALLER-SAVED (ISR must save if it uses them):
    RAX, RCX, RDX, RSI, RDI, R8, R9, R10, R11
    (These can be freely clobbered by any function)
  
  CALLEE-SAVED (ISR must save if compiler uses them):
    RBX, RBP, R12, R13, R14, R15
    (Functions must preserve these across calls)
  
  The compiler handles this automatically when you use
  the correct ISR attribute (__attribute__((interrupt)) in GCC).
  
  This is why ISR calling convention differs from normal functions!
```

### What the Compiler Does For You (C with GCC)

```c
// You write:
__attribute__((interrupt)) void timer_isr(struct interrupt_frame *frame) {
    counter++;
}

// Compiler generates (roughly):
timer_isr:
    push rax          ; save caller-saved regs
    push rcx
    push rdx
    push rsi
    push rdi
    push r8
    push r9
    push r10
    push r11
    ; --- your code ---
    inc [counter]
    ; --- end your code ---
    pop r11           ; restore in reverse order
    pop r10
    pop r9
    pop r8
    pop rdi
    pop rsi
    pop rdx
    pop rcx
    pop rax
    iretq             ; special return instruction (pops RIP, CS, RFLAGS)
```

---

## CHAPTER 13 — INTERRUPT PRIORITY & NESTING

### Concept: Priority

When multiple interrupts fire simultaneously, which runs first?
**Priority** determines the order.

```
PRIORITY EXAMPLE (ARM Cortex-M NVIC):

  Priority 0  (HIGHEST) ── NMI, HardFault (always preempt everything)
  Priority 1             ── Critical: SysTick timer
  Priority 2             ── High: Motor control PWM
  Priority 3             ── Medium: UART receive
  Priority 4             ── Low: Button debounce
  Priority 255 (LOWEST) ── Background tasks

  Note: In ARM Cortex-M, LOWER number = HIGHER priority (counterintuitive!)
```

### Nested Interrupts

**Nesting** = a higher-priority ISR can interrupt a lower-priority ISR.

```
NESTED INTERRUPT TIMELINE:

  Main: [A][A][A][A][A][A]────────────────────────────────[A][A]
                         │                               │
  Low ISR:               [L][L][L]───────────────[L][L][L]
                                │               │
  High ISR:                     [H][H][H][H][H][H]
  
  1. IRQ_LOW fires → pauses Main → Low ISR starts
  2. IRQ_HIGH fires → pauses Low ISR → High ISR starts
  3. High ISR finishes → returns to Low ISR
  4. Low ISR finishes → returns to Main
  
  STACK GROWS at each nesting level:
  ┌───────────────────────────────────────────────────┐
  │  [Main frame] [Low ISR frame] [High ISR frame]    │
  └───────────────────────────────────────────────────┘
  
  DANGER: Stack overflow if too many nesting levels or ISRs use too
          much stack space!
```

### ARM Cortex-M NVIC Priority Configuration

```
  ARM Cortex-M uses a priority register per IRQ.
  
  NVIC->IP[IRQn] = priority << (8 - __NVIC_PRIO_BITS);
  
  BASEPRI register: Masks all interrupts at or below a priority level.
  PRIMASK register: Disables all maskable interrupts (like CLI on x86).
  FAULTMASK: Disables all interrupts except NMI.
  
  EXAMPLE: To run code that cannot be interrupted by anything
           below priority 2:
  
  __set_BASEPRI(2 << (8 - __NVIC_PRIO_BITS));
  // critical section
  __set_BASEPRI(0);  // re-enable all
```

---

## CHAPTER 14 — INTERRUPT LATENCY

### Definition

**Interrupt Latency** = Time from when interrupt signal is asserted to when
the first instruction of the ISR executes.

```
LATENCY BREAKDOWN:

  Event happens
       │
       │ ← Hardware propagation delay (nanoseconds)
       ▼
  IRQ line asserted
       │
       │ ← CPU finishes current instruction
       │   (WORST CASE: complex instruction like REP MOVSQ can take hundreds of cycles!)
       ▼
  CPU acknowledges interrupt
       │
       │ ← Hardware stacking (8 registers × 32-bit = 32 bytes)
       │   Cortex-M: typically 12 clock cycles
       ▼
  ISR first instruction executes
       │
       │ ← ISR prologue (compiler saves additional registers)
       ▼
  ISR body begins

TOTAL LATENCY:
  Cortex-M3 @ 72MHz:  ~6 microseconds (typical)
  x86 server @ 3GHz:  ~1-10 microseconds (depends heavily on caches)
  
  REAL-TIME SYSTEMS define WCET = Worst Case Execution Time
  and WCIL = Worst Case Interrupt Latency
```

### Latency Reduction Techniques

```
1. Minimize instruction length in critical sections
   → Avoid REP string instructions near critical code

2. Reduce ISR prologue
   → Use naked functions where safe (manually manage stack)

3. Prioritize correctly
   → Time-critical ISRs get highest priority

4. Avoid cache misses in ISR
   → Keep ISR code small and frequently executed (cache-warm)

5. Avoid interrupt storms
   → Rate-limit or coalesce interrupts

6. Use interrupt coalescing (in network drivers)
   → Process N packets per interrupt instead of 1
```

---

## CHAPTER 15 — CRITICAL SECTIONS & ATOMICITY

### The Problem: Shared Data Between ISR and Main Code

```
RACE CONDITION EXAMPLE:

  Global: uint32_t counter = 0;

  Main code:         ISR:
  counter++;         counter++;    ← can fire ANYTIME!

  IF COUNTER IS 32-BIT AND READ-MODIFY-WRITE IS 3 INSTRUCTIONS:

  LOAD  r0, [counter]   ; r0 = 0
  ADD   r0, #1          ; r0 = 1
  STORE [counter], r0   ; counter = 1

  SCENARIO (Bad):
  Main: LOAD r0, [counter]   r0 = 5, counter = 5
  ISR FIRES!
  ISR:  LOAD r0, [counter]   r0 = 5
  ISR:  ADD r0, #1           r0 = 6
  ISR:  STORE [counter], r0  counter = 6
  ISR returns
  Main: ADD r0, #1           r0 = 6  ← still old r0!
  Main: STORE [counter], r0  counter = 6  ← LOST the ISR's increment!

  RESULT: counter = 6 instead of 7. BUG!
```

### Critical Section — The Solution

A **critical section** is code that must not be interrupted.
We achieve this by temporarily disabling interrupts.

```
CRITICAL SECTION PATTERN:

  ENTER CRITICAL SECTION:
    1. Save current interrupt state (IF flag / PRIMASK value)
    2. Disable interrupts

  [Access shared data safely — no ISR can preempt]

  EXIT CRITICAL SECTION:
    3. Restore interrupt state (don't blindly re-enable!)

  CRITICAL: Always RESTORE, not just "enable".
  Reason: If you were already in a critical section when you
  entered this one (nested), blindly re-enabling would be wrong!
```

```
x86 CORRECT PATTERN:

  // Save and disable
  unsigned long flags;
  asm volatile("pushfq; cli; pop %0" : "=r"(flags));

  // Critical section
  counter++;

  // Restore (not just STI!)
  asm volatile("push %0; popfq" : : "r"(flags));
```

```
ARM CORTEX-M CORRECT PATTERN:

  uint32_t saved = __get_PRIMASK();
  __disable_irq();   // Sets PRIMASK=1

  // Critical section
  counter++;

  __set_PRIMASK(saved);  // Restore (may or may not re-enable)
```

### Atomic Operations — Avoiding Disabling Interrupts

Modern CPUs and C11/C++11 provide **atomic operations** that are
guaranteed to be indivisible even without disabling interrupts.

```
  C11:     atomic_fetch_add(&counter, 1);
  C++11:   std::atomic<uint32_t> counter; counter.fetch_add(1);
  Rust:    use std::sync::atomic::{AtomicU32, Ordering};
           counter.fetch_add(1, Ordering::SeqCst);
  
  UNDER THE HOOD (x86):
    LOCK ADD [counter], 1    ← LOCK prefix makes it atomic
    
  UNDER THE HOOD (ARM):
    LDREX r0, [addr]         ← Load-Exclusive
    ADD   r0, #1
    STREX r1, r0, [addr]     ← Store-Exclusive (fails if concurrent access)
    CMP   r1, #0
    BNE   retry              ← Retry if store failed
```

---

## CHAPTER 16 — ISR DESIGN: THE GOLDEN RULES

```
╔═══════════════════════════════════════════════════════════════╗
║              THE TEN COMMANDMENTS OF ISR DESIGN               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  1. THOU SHALT BE FAST                                        ║
║     ISRs must execute in microseconds, not milliseconds.      ║
║     Long ISRs block other interrupts and miss events.         ║
║                                                               ║
║  2. THOU SHALT NOT SLEEP                                      ║
║     Never call sleep(), delay(), wait(), mutex_lock(),        ║
║     or any blocking function from an ISR.                     ║
║                                                               ║
║  3. THOU SHALT NOT MALLOC                                      ║
║     Never call malloc/free from an ISR.                       ║
║     Memory allocator uses locks — guaranteed deadlock.        ║
║                                                               ║
║  4. THOU SHALT PROTECT SHARED DATA                            ║
║     Every shared variable between ISR and main code          ║
║     must use atomic operations or critical sections.          ║
║                                                               ║
║  5. THOU SHALT DECLARE SHARED VARS VOLATILE                   ║
║     Without volatile, compiler may cache in register          ║
║     and never see ISR's updates.                              ║
║                                                               ║
║  6. THOU SHALT SEND EOI CORRECTLY                             ║
║     Always acknowledge the interrupt controller.              ║
║     Forgetting EOI blocks all future IRQs of same/lower prio. ║
║                                                               ║
║  7. THOU SHALT NOT PRINT FROM ISR                             ║
║     printf uses locks, buffers, OS services — all forbidden.  ║
║     Use lockless ring buffers or LED toggles for ISR debug.   ║
║                                                               ║
║  8. THOU SHALT USE DEFERRED WORK                              ║
║     Do the minimum in ISR. Defer heavy work to task context.  ║
║     (Bottom halves, tasklets, workqueues, semaphores)         ║
║                                                               ║
║  9. THOU SHALT NOT NEST CARELESSLY                            ║
║     Nested interrupts are powerful but dangerous.             ║
║     Each nesting level consumes stack. Stack overflow = death.║
║                                                               ║
║ 10. THOU SHALT HANDLE RE-ENTRANCY                             ║
║     If the same ISR can fire while itself is running,         ║
║     your ISR must be re-entrant (no static local state        ║
║     unless protected).                                        ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## CHAPTER 17 — VOLATILE & MEMORY BARRIERS

### Why `volatile` Matters for ISRs

The compiler is very smart. It optimizes by keeping frequently-used
variables in CPU registers instead of re-reading from memory.

```
WITHOUT VOLATILE (BUG):

  // ISR sets this flag
  bool ready = false;

  // Main code:
  while (!ready) {    ← Compiler: "ready is always false here (I never see it change)"
      // wait          → Compiles to: infinite loop that never re-reads ready!
  }
  // This code is UNREACHABLE according to compiler optimizer!

WITH VOLATILE (CORRECT):

  volatile bool ready = false;

  // Main code:
  while (!ready) {   ← Compiler MUST re-read ready from memory each iteration
      // wait
  }
  // Works correctly!
```

### Memory Barriers

A **memory barrier** (also called memory fence) prevents the CPU and compiler
from **reordering** memory accesses across the barrier.

```
WHY REORDERING MATTERS:

  // Suppose ISR writes data, then sets flag:
  data = 42;       // Step A
  flag = 1;        // Step B

  // Main reads flag, then data:
  if (flag) {      // Step C
      use(data);   // Step D
  }

  WITHOUT BARRIERS:
    CPU or compiler might reorder A and B, or C and D.
    Main might see flag=1 but data still holds garbage!

  WITH BARRIERS:
    ISR:  data = 42;
          MEMORY_BARRIER();  // Nothing above crosses below
          flag = 1;

    Main: if (flag) {
              MEMORY_BARRIER();  // Ensure flag read is visible before data read
              use(data);  // Guaranteed to see data=42
          }
```

```
BARRIER SYNTAX:

  C (GCC):         asm volatile("" ::: "memory");
  C (Linux):       barrier();           // compiler barrier
                   smp_wmb();           // write memory barrier
                   smp_rmb();           // read memory barrier
                   smp_mb();            // full memory barrier
  C11:             atomic_thread_fence(memory_order_seq_cst);
  Rust:            std::sync::atomic::fence(Ordering::SeqCst);
  ARM hardware:    DMB (Data Memory Barrier)
                   DSB (Data Synchronization Barrier)
                   ISB (Instruction Synchronization Barrier)
  x86 hardware:    MFENCE, LFENCE, SFENCE
```

---

## CHAPTER 18 — DEFERRED WORK: BOTTOM HALVES

### The Top-Half / Bottom-Half Model

This is the most important architectural pattern for ISR design.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOP-HALF / BOTTOM-HALF MODEL                 │
│                                                                 │
│  INTERRUPT FIRES                                                │
│       │                                                         │
│       ▼                                                         │
│  ┌────────────────────────────────┐                             │
│  │         TOP-HALF (ISR)         │  ← Runs immediately         │
│  │  Minimal, fast, atomic:        │  ← Interrupts (often)       │
│  │  1. Acknowledge hardware       │     disabled or limited      │
│  │  2. Read urgent data           │                             │
│  │  3. Schedule bottom-half       │                             │
│  │  4. Return ASAP                │                             │
│  └──────────────┬─────────────────┘                             │
│                 │                                               │
│                 │ schedule()                                     │
│                 ▼                                               │
│  ┌────────────────────────────────┐                             │
│  │        BOTTOM-HALF             │  ← Runs later               │
│  │  Heavy processing:             │  ← Interrupts enabled       │
│  │  1. Protocol processing        │  ← Can sleep                │
│  │  2. Memory allocation          │  ← Can use locks            │
│  │  3. File I/O                   │  ← Normal kernel context    │
│  │  4. User notification          │                             │
│  └────────────────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### Linux Kernel Bottom-Half Mechanisms

```
MECHANISM 1: SOFTIRQ
  - Statically allocated (compile time)
  - Can run on multiple CPUs simultaneously
  - Re-entrant (same softirq can run on multiple CPUs)
  - Used by: network (NET_TX, NET_RX), block layer, timers
  - Registration: open_softirq(NET_RX_SOFTIRQ, net_rx_action);
  - Scheduling: raise_softirq(NET_RX_SOFTIRQ);

MECHANISM 2: TASKLET
  - Built on top of SOFTIRQ (uses HI_SOFTIRQ or TASKLET_SOFTIRQ)
  - NOT re-entrant (same tasklet won't run on 2 CPUs simultaneously)
  - Dynamic allocation
  - Simpler to use than softirq
  - DECLARE_TASKLET(my_tasklet, my_tasklet_func, data);
  - tasklet_schedule(&my_tasklet);

MECHANISM 3: WORKQUEUE
  - Runs in process context (kernel thread — kworker)
  - CAN sleep! Most flexible.
  - Slower than softirq/tasklet (thread scheduling overhead)
  - INIT_WORK(&my_work, my_work_function);
  - schedule_work(&my_work);

WHEN TO USE WHICH:
  Need speed + no sleep → SOFTIRQ (if you know what you're doing)
  Need no sleep, simpler → TASKLET  
  Need sleep or locks → WORKQUEUE
```

### Embedded: Deferred Work via Semaphores/FreeRTOS

```
FREERTOS PATTERN (most common in embedded):

  // ISR:
  void UART_IRQHandler(void) {
      BaseType_t xHigherPriorityTaskWoken = pdFALSE;
      
      // Read byte from hardware
      uint8_t byte = UART->DR;
      
      // Put in queue (ISR-safe version!)
      xQueueSendFromISR(uart_queue, &byte, &xHigherPriorityTaskWoken);
      
      // If we woke a higher-priority task, request a context switch
      portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
  }

  // Task (runs in normal task context, can sleep):
  void uart_task(void *params) {
      uint8_t byte;
      while (1) {
          // Block (sleep) until data available
          xQueueReceive(uart_queue, &byte, portMAX_DELAY);
          
          // Heavy processing here — safe to sleep, alloc, etc.
          process_byte(byte);
      }
  }
```

---

## CHAPTER 19 — ISR IN C: BARE METAL & LINUX

### 19.1 — Bare Metal x86: Writing a Complete IDT + ISR from Scratch

```c
/*
 * FILE: idt.h
 * Bare-metal x86-64 IDT setup and ISR registration.
 * No OS — runs directly on hardware or in QEMU.
 */

#ifndef IDT_H
#define IDT_H

#include <stdint.h>

/* ─── IDT Gate Descriptor (16 bytes for x86-64) ─── */
typedef struct __attribute__((packed)) {
    uint16_t offset_low;      /* ISR address bits [15:0]  */
    uint16_t selector;        /* GDT code segment selector */
    uint8_t  ist;             /* Interrupt Stack Table offset (bits 2:0) */
    uint8_t  type_attr;       /* Type and attributes byte  */
    uint16_t offset_mid;      /* ISR address bits [31:16] */
    uint32_t offset_high;     /* ISR address bits [63:32] */
    uint32_t reserved;        /* Must be zero             */
} idt_entry_t;

/* ─── IDTR: Loaded into IDTR register via LIDT instruction ─── */
typedef struct __attribute__((packed)) {
    uint16_t limit;           /* Size of IDT minus 1      */
    uint64_t base;            /* Linear address of IDT    */
} idtr_t;

/* ─── Interrupt Frame pushed by CPU before calling ISR ─── */
typedef struct __attribute__((packed)) {
    uint64_t ip;              /* Instruction pointer (return address) */
    uint64_t cs;              /* Code segment                         */
    uint64_t flags;           /* RFLAGS register                      */
    uint64_t sp;              /* Stack pointer                        */
    uint64_t ss;              /* Stack segment                        */
} interrupt_frame_t;

/* ─── Type attribute byte values ─── */
#define IDT_TYPE_INTERRUPT_GATE  0x8E  /* P=1, DPL=0, Type=0xE (64-bit interrupt gate) */
#define IDT_TYPE_TRAP_GATE       0x8F  /* P=1, DPL=0, Type=0xF (64-bit trap gate)      */
#define IDT_TYPE_USER_INTERRUPT  0xEE  /* P=1, DPL=3 (accessible from user mode)       */

/* ─── Function declarations ─── */
void idt_init(void);
void idt_set_entry(uint8_t vector, void *handler, uint8_t type_attr);

#endif /* IDT_H */
```

```c
/*
 * FILE: idt.c
 * IDT initialization and management.
 */

#include "idt.h"
#include <string.h>  /* memset */

/* ─── The actual IDT: 256 entries × 16 bytes = 4096 bytes ─── */
static idt_entry_t idt[256];

/* ─── The IDTR structure loaded with LIDT ─── */
static idtr_t idtr;

/* ─── Set one IDT entry ─────────────────────────────────────────
 * vector   : Interrupt number (0–255)
 * handler  : Pointer to ISR function
 * type_attr: Gate type and privilege level byte
 * ─────────────────────────────────────────────────────────────── */
void idt_set_entry(uint8_t vector, void *handler, uint8_t type_attr)
{
    uint64_t addr = (uint64_t)handler;

    idt[vector].offset_low  = (uint16_t)(addr & 0xFFFF);
    idt[vector].offset_mid  = (uint16_t)((addr >> 16) & 0xFFFF);
    idt[vector].offset_high = (uint32_t)((addr >> 32) & 0xFFFFFFFF);
    idt[vector].selector    = 0x08;   /* Kernel code segment (GDT entry 1) */
    idt[vector].ist         = 0;      /* Use main kernel stack              */
    idt[vector].type_attr   = type_attr;
    idt[vector].reserved    = 0;
}

/* ─── Initialize the entire IDT ────────────────────────────────── */
void idt_init(void)
{
    /* Zero all entries first (marks all as not-present) */
    memset(idt, 0, sizeof(idt));

    /* Set up the IDTR */
    idtr.limit = sizeof(idt) - 1;
    idtr.base  = (uint64_t)&idt[0];

    /* Load IDT into CPU (LIDT instruction) */
    __asm__ volatile ("lidt %0" : : "m"(idtr));
}
```

```c
/*
 * FILE: isr.c
 * Actual ISR implementations — bare metal x86-64.
 *
 * The __attribute__((interrupt)) tells GCC to:
 *   1. Use IRETQ instead of RET to return
 *   2. Save/restore ALL caller-saved registers
 *   3. Set up the interrupt_frame_t parameter correctly
 */

#include "idt.h"
#include <stdint.h>

/* ─── Shared data between ISR and main code ─── */
volatile uint64_t timer_ticks = 0;   /* MUST be volatile! */
volatile uint8_t  key_buffer[64];
volatile uint8_t  key_head = 0;
volatile uint8_t  key_tail = 0;

/* ─── PIC (8259A) I/O port addresses ─── */
#define PIC1_COMMAND  0x20
#define PIC1_DATA     0x21
#define PIC2_COMMAND  0xA0
#define PIC2_DATA     0xA1
#define PIC_EOI       0x20    /* End-of-Interrupt command */

/* ─── Port I/O helpers ─── */
static inline void outb(uint16_t port, uint8_t value) {
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}

static inline uint8_t inb(uint16_t port) {
    uint8_t value;
    __asm__ volatile ("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}

/* ─── HANDLER: Division by Zero (Vector 0) ────────────────────────
 * This is a FAULT — the faulting instruction is NOT re-executed.
 * (Divide error is a fault that's treated as a termination condition
 *  because there's no sensible way to continue)
 * ─────────────────────────────────────────────────────────────────── */
__attribute__((interrupt))
void isr_divide_error(interrupt_frame_t *frame)
{
    /* In a real kernel, we'd print details, terminate the process,
     * or trigger a kernel panic. Here we just halt. */
    (void)frame;   /* suppress unused warning */

    /* Kernel panic: halt forever */
    __asm__ volatile (
        "cli\n\t"   /* Disable interrupts */
        "hlt\n\t"   /* Halt CPU           */
        ::: "memory"
    );
}

/* ─── HANDLER: General Protection Fault (Vector 13) ───────────────
 * Has an ERROR CODE pushed by CPU before calling handler.
 * The signature differs: takes (frame, error_code).
 * ─────────────────────────────────────────────────────────────────── */
__attribute__((interrupt))
void isr_gpf(interrupt_frame_t *frame, uint64_t error_code)
{
    (void)frame;
    (void)error_code;

    /* In a real kernel: log fault, kill offending process */
    __asm__ volatile ("cli; hlt");
}

/* ─── HANDLER: Page Fault (Vector 14) ─────────────────────────────
 * CR2 register contains the faulting virtual address.
 * Error code bits:
 *   bit 0: P  (0=not-present page, 1=protection violation)
 *   bit 1: W  (0=read access, 1=write access)
 *   bit 2: U  (0=kernel mode, 1=user mode)
 *   bit 3: R  (1=reserved bit violation)
 *   bit 4: I  (1=instruction fetch)
 * ─────────────────────────────────────────────────────────────────── */
__attribute__((interrupt))
void isr_page_fault(interrupt_frame_t *frame, uint64_t error_code)
{
    uint64_t faulting_address;

    /* CR2 holds the virtual address that caused the fault */
    __asm__ volatile ("mov %%cr2, %0" : "=r"(faulting_address));

    (void)frame;

    /* Decode error code */
    int not_present    = !(error_code & 0x1);
    int write_access   = (error_code & 0x2) != 0;
    int user_mode      = (error_code & 0x4) != 0;

    if (not_present) {
        /* In real OS: allocate page, update PTE, return → instruction retries */
        /* Here: just halt */
    }

    (void)write_access;
    (void)user_mode;
    (void)faulting_address;

    __asm__ volatile ("cli; hlt");
}

/* ─── HANDLER: Timer IRQ (Vector 32 = IRQ0) ───────────────────────
 * Fires at 18.2Hz by default (PIT channel 0).
 * Reprogrammed to higher rate in init code.
 *
 * RULES FOLLOWED:
 *  ✓ No sleep
 *  ✓ No malloc
 *  ✓ volatile shared variable
 *  ✓ EOI sent to PIC
 *  ✓ Minimal work
 * ─────────────────────────────────────────────────────────────────── */
__attribute__((interrupt))
void isr_timer(interrupt_frame_t *frame)
{
    (void)frame;

    /* Increment tick counter — this is the ONLY work we do */
    timer_ticks++;

    /* MANDATORY: Send End-Of-Interrupt to PIC                       */
    /* Without this, PIC will not send any more IRQ0 interrupts!     */
    outb(PIC1_COMMAND, PIC_EOI);
}

/* ─── HANDLER: Keyboard IRQ (Vector 33 = IRQ1) ────────────────────
 * Keyboard controller sends scan codes on PS/2 port 0x60.
 *
 * DESIGN:
 *  TOP-HALF (this ISR): Read scan code, put in ring buffer.
 *  BOTTOM-HALF (main loop): Translate scan codes, echo to screen.
 * ─────────────────────────────────────────────────────────────────── */
__attribute__((interrupt))
void isr_keyboard(interrupt_frame_t *frame)
{
    (void)frame;

    /* Read the scan code from keyboard data port */
    uint8_t scan_code = inb(0x60);

    /* Store in ring buffer (lock-free: ISR writes, main reads)      */
    /* This is safe ONLY if:                                         */
    /*   1. Only ONE writer (this ISR)                               */
    /*   2. Only ONE reader (main code)                              */
    /*   3. Buffer size is power of 2 (for wrap-around)             */
    uint8_t next_head = (key_head + 1) & 63;  /* 64-entry ring buffer */
    if (next_head != key_tail) {               /* Not full             */
        key_buffer[key_head] = scan_code;
        /* Memory barrier: ensure data write is visible before head update */
        __asm__ volatile ("" ::: "memory");
        key_head = next_head;
    }
    /* If full: drop the scan code (rare, acceptable for keyboard)   */

    /* EOI to PIC */
    outb(PIC1_COMMAND, PIC_EOI);
}

/* ─── PIC Initialization ───────────────────────────────────────────
 * Remaps PIC IRQs from vectors 0-15 to vectors 32-47.
 * (Default 0-15 conflicts with CPU exception vectors 0-31!)
 * ─────────────────────────────────────────────────────────────────── */
void pic_init(void)
{
    /* ICW1: Start initialization sequence */
    outb(PIC1_COMMAND, 0x11);
    outb(PIC2_COMMAND, 0x11);

    /* ICW2: Set vector offsets */
    outb(PIC1_DATA, 0x20);   /* IRQ0-7  → vectors 32-39  */
    outb(PIC2_DATA, 0x28);   /* IRQ8-15 → vectors 40-47  */

    /* ICW3: Tell PICs about each other */
    outb(PIC1_DATA, 0x04);   /* PIC1: slave PIC at IRQ2  */
    outb(PIC2_DATA, 0x02);   /* PIC2: cascade identity 2 */

    /* ICW4: Set 8086 mode */
    outb(PIC1_DATA, 0x01);
    outb(PIC2_DATA, 0x01);

    /* OCW1: Unmask all IRQs (0 = unmasked, 1 = masked)             */
    outb(PIC1_DATA, 0x00);
    outb(PIC2_DATA, 0x00);
}

/* ─── Setup: Register all ISRs in IDT ─────────────────────────────── */
void isr_install(void)
{
    pic_init();
    idt_init();

    /* CPU exceptions */
    idt_set_entry(0,  isr_divide_error, IDT_TYPE_INTERRUPT_GATE);
    idt_set_entry(13, isr_gpf,          IDT_TYPE_INTERRUPT_GATE);
    idt_set_entry(14, isr_page_fault,   IDT_TYPE_INTERRUPT_GATE);

    /* Hardware IRQs (after PIC remapping) */
    idt_set_entry(32, isr_timer,        IDT_TYPE_INTERRUPT_GATE);
    idt_set_entry(33, isr_keyboard,     IDT_TYPE_INTERRUPT_GATE);

    /* Enable hardware interrupts */
    __asm__ volatile ("sti");
}
```

```c
/*
 * FILE: main.c
 * Main kernel entry point — demonstrates ISR + bottom-half pattern.
 */

#include "idt.h"
#include <stdint.h>

extern volatile uint64_t timer_ticks;
extern volatile uint8_t  key_buffer[];
extern volatile uint8_t  key_head, key_tail;

/* ─── Bottom-half: process keyboard ring buffer ─── */
static void process_keyboard(void)
{
    while (key_tail != key_head) {
        /* Read from ring buffer */
        uint8_t scan_code = key_buffer[key_tail];
        /* Memory barrier: read data before updating tail */
        __asm__ volatile ("" ::: "memory");
        key_tail = (key_tail + 1) & 63;

        /* Now do heavy processing safely (interrupts still enabled) */
        /* translate_scan_code(scan_code); */
        /* display_character(char);        */
        (void)scan_code;
    }
}

/* ─── Main kernel loop ─── */
void kernel_main(void)
{
    isr_install();

    /* Main loop: CPU does useful work between interrupts */
    uint64_t last_tick = 0;

    while (1) {
        /* Bottom-half: process pending keyboard input */
        process_keyboard();

        /* Do time-based work */
        if (timer_ticks != last_tick) {
            last_tick = timer_ticks;
            /* One tick has passed — do scheduled work */
        }

        /* Halt CPU until next interrupt (saves power) */
        __asm__ volatile ("hlt");
    }
}
```

---

### 19.2 — Linux Kernel Driver ISR (with `request_irq`)

```c
/*
 * FILE: my_driver.c
 * Linux kernel character driver with interrupt handler.
 * Compiled as a kernel module.
 *
 * Build: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/interrupt.h>    /* request_irq, free_irq, IRQ_HANDLED */
#include <linux/spinlock.h>     /* spinlock_t, spin_lock_irqsave */
#include <linux/workqueue.h>    /* INIT_WORK, schedule_work */
#include <linux/atomic.h>       /* atomic_t, atomic_inc */
#include <linux/slab.h>         /* kzalloc */

#define DRIVER_NAME "my_driver"
#define MY_IRQ_NUMBER 1         /* IRQ1 = keyboard (example) */

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Systems Programmer");
MODULE_DESCRIPTION("ISR demonstration driver");

/* ─── Driver state structure ─── */
struct my_device {
    spinlock_t      lock;           /* Protects shared state       */
    atomic_t        irq_count;      /* Lockless interrupt counter  */
    struct work_struct work;        /* Bottom-half work item        */
    void __iomem    *base_addr;     /* Memory-mapped register base  */
    uint32_t        data_buffer[64];/* Ring buffer for IRQ data     */
    unsigned int    buf_head;
    unsigned int    buf_tail;
};

static struct my_device *dev_state;

/* ─── Bottom-Half: Work queue handler ──────────────────────────────
 * Runs in process context (kernel thread "kworker").
 * CAN sleep, CAN use locks, CAN allocate memory.
 * ─────────────────────────────────────────────────────────────────── */
static void my_work_handler(struct work_struct *work)
{
    struct my_device *dev = container_of(work, struct my_device, work);
    unsigned long flags;
    uint32_t data[64];
    unsigned int count = 0;

    /* Copy data from ring buffer (need lock to access shared state) */
    spin_lock_irqsave(&dev->lock, flags);
    while (dev->buf_tail != dev->buf_head && count < 64) {
        data[count++] = dev->data_buffer[dev->buf_tail];
        dev->buf_tail = (dev->buf_tail + 1) % 64;
    }
    spin_unlock_irqrestore(&dev->lock, flags);

    /* Now process the data — can sleep, no lock held */
    for (unsigned int i = 0; i < count; i++) {
        /* Heavy processing: protocol decode, DMA, file I/O, etc. */
        pr_debug(DRIVER_NAME ": processing data 0x%08x\n", data[i]);
    }
}

/* ─── Top-Half: The Interrupt Service Routine ──────────────────────
 *
 * SIGNATURE:
 *   irqreturn_t handler(int irq, void *dev_id)
 *
 *   irq    : IRQ number that fired
 *   dev_id : The pointer we passed to request_irq() — our device struct
 *
 * RETURN VALUES:
 *   IRQ_HANDLED    : We handled this interrupt
 *   IRQ_NONE       : This interrupt was not for us (shared IRQ lines)
 *   IRQ_WAKE_THREAD: Wake the threaded IRQ handler (alternative pattern)
 *
 * CONTEXT:
 *   - Interrupts DISABLED on the local CPU
 *   - Cannot sleep
 *   - Cannot use regular mutexes (use spinlocks only)
 *   - Should be as fast as possible
 * ─────────────────────────────────────────────────────────────────── */
static irqreturn_t my_irq_handler(int irq, void *dev_id)
{
    struct my_device *dev = (struct my_device *)dev_id;
    uint32_t status;

    /* ── Step 1: Check if this interrupt is for us ───────────────── */
    /* Read hardware status register (memory-mapped I/O)             */
    /* rmb() ensures we read the actual hardware value               */
    rmb();
    status = readl(dev->base_addr + 0x00);  /* Status register offset */

    if (!(status & 0x01)) {
        /* Interrupt not from our device — IRQ line is shared */
        return IRQ_NONE;
    }

    /* ── Step 2: Acknowledge the interrupt (clear it in hardware) ── */
    /* This prevents the interrupt from firing again immediately      */
    writel(0x01, dev->base_addr + 0x04);   /* Clear interrupt flag   */
    wmb();                                  /* Ensure write completes */

    /* ── Step 3: Collect data (minimal, fast) ─────────────────────── */
    atomic_inc(&dev->irq_count);

    /* Read data register with spinlock (ISR-safe) */
    spin_lock(&dev->lock);   /* NB: spin_lock (not irqsave) — we're already in ISR */

    unsigned int next_head = (dev->buf_head + 1) % 64;
    if (next_head != dev->buf_tail) {
        /* Read data from hardware FIFO register */
        dev->data_buffer[dev->buf_head] = readl(dev->base_addr + 0x08);
        dev->buf_head = next_head;
    }

    spin_unlock(&dev->lock);

    /* ── Step 4: Schedule bottom-half ──────────────────────────────── */
    schedule_work(&dev->work);

    return IRQ_HANDLED;
}

/* ─── Module init ───────────────────────────────────────────────── */
static int __init my_driver_init(void)
{
    int ret;

    pr_info(DRIVER_NAME ": initializing\n");

    /* Allocate device state (GFP_KERNEL = can sleep) */
    dev_state = kzalloc(sizeof(*dev_state), GFP_KERNEL);
    if (!dev_state)
        return -ENOMEM;

    /* Initialize synchronization primitives */
    spin_lock_init(&dev_state->lock);
    atomic_set(&dev_state->irq_count, 0);

    /* Initialize work queue item */
    INIT_WORK(&dev_state->work, my_work_handler);

    /* Register the IRQ handler:
     *
     * request_irq(irq, handler, flags, name, dev_id)
     *
     * IRQF_SHARED    : IRQ line is shared with other devices
     * IRQF_TRIGGER_RISING: Trigger on rising edge
     * dev_state      : Passed back to handler as dev_id
     */
    ret = request_irq(
        MY_IRQ_NUMBER,
        my_irq_handler,
        IRQF_SHARED | IRQF_TRIGGER_RISING,
        DRIVER_NAME,
        dev_state
    );

    if (ret) {
        pr_err(DRIVER_NAME ": failed to request IRQ %d: %d\n",
               MY_IRQ_NUMBER, ret);
        kfree(dev_state);
        return ret;
    }

    pr_info(DRIVER_NAME ": registered IRQ %d\n", MY_IRQ_NUMBER);
    return 0;
}

/* ─── Module cleanup ────────────────────────────────────────────── */
static void __exit my_driver_exit(void)
{
    /* MUST free IRQ before freeing device state!
     * free_irq waits for any ongoing ISR to complete. */
    free_irq(MY_IRQ_NUMBER, dev_state);

    /* Cancel any pending work queue items */
    cancel_work_sync(&dev_state->work);

    pr_info(DRIVER_NAME ": handled %d interrupts total\n",
            atomic_read(&dev_state->irq_count));

    kfree(dev_state);
    pr_info(DRIVER_NAME ": unloaded\n");
}

module_init(my_driver_init);
module_exit(my_driver_exit);
```

---

### 19.3 — ARM Cortex-M (STM32) ISR in C

```c
/*
 * FILE: stm32_uart_isr.c
 * UART receive ISR on STM32F4 microcontroller.
 * Uses CMSIS and STM32 HAL register definitions.
 *
 * Hardware: STM32F407VG @ 168 MHz
 * UART: USART2, 115200 baud, 8N1
 */

#include "stm32f4xx.h"           /* CMSIS device header */
#include <string.h>
#include <stdint.h>

/* ─── Ring buffer for UART RX ─── */
#define UART_RX_BUF_SIZE  256    /* MUST be power of 2 for efficient wrap */
#define UART_RX_BUF_MASK  (UART_RX_BUF_SIZE - 1)

static volatile uint8_t  uart_rx_buf[UART_RX_BUF_SIZE];
static volatile uint32_t uart_rx_head = 0;  /* Written by ISR   */
static volatile uint32_t uart_rx_tail = 0;  /* Read by main()   */

/* ─── Error counters ─── */
static volatile uint32_t uart_overrun_errors = 0;
static volatile uint32_t uart_framing_errors = 0;
static volatile uint32_t uart_rx_overflows   = 0;

/* ─── USART2 Interrupt Handler ──────────────────────────────────────
 *
 * Name MUST match the vector table entry exactly!
 * For STM32F4: "USART2_IRQHandler"
 * The startup file (startup_stm32f407xx.s) has weak symbols for all
 * handlers. Defining one here overrides the weak default.
 *
 * Execution context:
 *  - Handler Mode (privileged)
 *  - Uses Process Stack Pointer if configured, else Main Stack Pointer
 *  - NVIC has already saved: R0-R3, R12, LR, PC, xPSR (8 registers)
 * ─────────────────────────────────────────────────────────────────── */
void USART2_IRQHandler(void)
{
    /* Read status register FIRST — clears some flags when DR is read */
    uint32_t sr = USART2->SR;

    /* ── Handle receive errors ─────────────────────────────────────── */
    if (sr & USART_SR_ORE) {
        /* Overrun Error: new byte arrived before previous was read     */
        /* Reading DR clears ORE flag                                   */
        (void)USART2->DR;
        uart_overrun_errors++;
        return;
    }

    if (sr & USART_SR_FE) {
        /* Framing Error: incorrect stop bit (wrong baud rate / noise)  */
        (void)USART2->DR;
        uart_framing_errors++;
        return;
    }

    /* ── Handle received data ──────────────────────────────────────── */
    if (sr & USART_SR_RXNE) {
        /* RXNE = RX Not Empty: a complete byte has been received       */
        uint8_t byte = (uint8_t)(USART2->DR & 0xFF);   /* Read clears RXNE */

        /* Write to ring buffer if not full */
        uint32_t next_head = (uart_rx_head + 1) & UART_RX_BUF_MASK;

        if (next_head != uart_rx_tail) {
            uart_rx_buf[uart_rx_head] = byte;

            /* Data Memory Barrier: ensure byte written before head updated */
            __DMB();

            uart_rx_head = next_head;
        } else {
            /* Ring buffer full — byte dropped */
            uart_rx_overflows++;
        }
    }

    /* ── Handle transmit complete (if TX interrupts enabled) ─────────── */
    if (sr & USART_SR_TC) {
        /* Transmission complete — could disable TX interrupt here      */
        USART2->CR1 &= ~USART_CR1_TCIE;    /* Disable TC interrupt     */
    }

    /* NOTE: No explicit EOI needed on ARM Cortex-M!
     * The NVIC handles EOI automatically when ISR returns.
     * Contrast with x86 PIC which needs explicit outb(0x20, 0x20). */
}

/* ─── Public API: Read from UART ring buffer (call from main loop) ─── */
int uart_read_byte(uint8_t *out)
{
    if (uart_rx_tail == uart_rx_head) {
        return 0;  /* Buffer empty */
    }

    /* Read Memory Barrier: ensure head is read before data */
    __DMB();

    *out = uart_rx_buf[uart_rx_tail];
    uart_rx_tail = (uart_rx_tail + 1) & UART_RX_BUF_MASK;
    return 1;  /* Success */
}

/* ─── USART2 Initialization ─────────────────────────────────────── */
void usart2_init(void)
{
    /* 1. Enable clocks */
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;   /* GPIOA clock (TX=PA2, RX=PA3) */
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN;  /* USART2 clock                 */

    /* 2. Configure GPIO pins for USART alternate function */
    GPIOA->MODER   |= (2 << 4) | (2 << 6);   /* AF mode for PA2, PA3 */
    GPIOA->AFR[0]  |= (7 << 8) | (7 << 12);  /* AF7 = USART2         */

    /* 3. Configure USART2: 115200 baud, 8N1
     * BRR = f_PCLK / baud = 42,000,000 / 115,200 ≈ 364.58
     * DIV_Mantissa = 364, DIV_Fraction = 0.58 × 16 ≈ 9 */
    USART2->BRR = (364 << 4) | 9;

    /* 4. Enable USART, RX, TX, and RX interrupt */
    USART2->CR1 = USART_CR1_UE        /* USART Enable                   */
                | USART_CR1_RE        /* Receiver Enable                 */
                | USART_CR1_TE        /* Transmitter Enable              */
                | USART_CR1_RXNEIE;   /* RX Not Empty Interrupt Enable   */

    /* 5. Configure NVIC for USART2 interrupt */
    NVIC_SetPriority(USART2_IRQn, 5);  /* Priority 5 (0=highest on Cortex-M4) */
    NVIC_EnableIRQ(USART2_IRQn);
}

/* ─── Main: demonstrates top-half/bottom-half pattern ─────────────── */
int main(void)
{
    usart2_init();

    while (1) {
        uint8_t byte;

        /* Bottom-half: drain ring buffer and process */
        while (uart_read_byte(&byte)) {
            /* Process received byte: echo back, parse protocol, etc. */
            /* This runs with interrupts ENABLED — safe to do anything */
        }

        /* WFI: Wait For Interrupt — halts core until next interrupt
         * Saves power! Core resumes at instruction after WFI. */
        __WFI();
    }
}
```

---

## CHAPTER 20 — ISR IN RUST: EMBEDDED & SYSTEMS

### 20.1 — Rust Philosophy for ISR/Embedded Work

Rust's ownership system makes ISR programming safer but requires
understanding several key patterns:

```
KEY RUST CONCEPTS FOR ISRs:

  1. Static Mutability Problem:
     ISRs are called by hardware — they don't "own" the data.
     Rust's borrow checker cannot track this at compile time.
     Solution: Use special safe abstractions:
       - cortex_m::interrupt::Mutex<RefCell<T>>
       - critical_section::Mutex<RefCell<T>>
       - atomic types (AtomicU32, AtomicBool)

  2. No std in Bare Metal:
     #![no_std] — no heap, no OS, no standard library
     Use: core:: (always available) + heapless:: (for data structures)

  3. Unsafe Boundaries:
     Accessing hardware registers is inherently unsafe.
     Rust embedded ecosystem wraps this in safe HAL abstractions.
     (PAC = Peripheral Access Crate, HAL = Hardware Abstraction Layer)

  4. RTIC Framework:
     Real-Time Interrupt-driven Concurrency
     Provides safe, zero-cost ISR framework for Cortex-M.
     Eliminates data races at compile time!
```

### 20.2 — Rust Bare Metal ISR (Cortex-M, no_std)

```rust
//! FILE: src/main.rs
//! Bare-metal Rust ISR for STM32 (ARM Cortex-M4).
//! No OS, no std. Uses cortex-m and stm32f4xx-hal crates.
//!
//! Cargo.toml dependencies:
//!   [dependencies]
//!   cortex-m = "0.7"
//!   cortex-m-rt = "0.7"           # Provides exception! and interrupt! macros
//!   stm32f4xx-hal = { version = "0.20", features = ["stm32f407"] }
//!   heapless = "0.8"              # Stack-allocated data structures
//!   critical-section = "1.1"
//!   nb = "1.0"                    # Non-blocking I/O traits
//!
//!   [profile.release]
//!   opt-level = "s"               # Optimize for size (typical embedded)
//!   debug = true                  # Keep debug symbols

#![no_std]
#![no_main]

use core::sync::atomic::{AtomicU32, AtomicBool, Ordering};
use core::cell::RefCell;

use cortex_m::interrupt::Mutex;
use cortex_m_rt::{entry, exception, interrupt};
use heapless::spsc::{Queue, Producer, Consumer};    // Lock-free SPSC queue

use stm32f4xx_hal::{
    pac,                   // Peripheral Access Crate (raw registers)
    prelude::*,
    serial::{Serial, config::Config},
    interrupt as hal_interrupt,
};

// ─── Shared state between ISR and main ────────────────────────────────
//
// These are global statics — the ONLY way to share data with ISRs.
// We use atomic types where possible for lock-free access.

/// Monotonic tick counter — incremented by SysTick ISR every 1ms
static TICK_COUNT: AtomicU32 = AtomicU32::new(0);

/// Flag: new UART data is available
static UART_DATA_READY: AtomicBool = AtomicBool::new(false);

/// Lock-free Single-Producer Single-Consumer queue.
/// ISR is the producer, main() is the consumer.
/// heapless::Queue is stack-allocated (no heap needed).
///
/// The Mutex<RefCell<...>> pattern allows safe interior mutability
/// in a single-threaded (single-core) embedded context.
static UART_QUEUE: Mutex<RefCell<Option<Queue<u8, 64>>>> =
    Mutex::new(RefCell::new(None));

static UART_PRODUCER: Mutex<RefCell<Option<Producer<'static, u8, 64>>>> =
    Mutex::new(RefCell::new(None));

// ─── SysTick Exception Handler ────────────────────────────────────────
//
// SysTick is a 24-bit countdown timer built into every Cortex-M core.
// Configured to fire every 1ms → TICK_COUNT counts milliseconds.
//
// The #[exception] attribute from cortex-m-rt:
//   1. Generates correct vector table entry
//   2. Ensures the function is not inlined or removed by optimizer
//   3. Handles the exception return (BX LR with correct EXC_RETURN)
//
#[exception]
fn SysTick() {
    // ONLY operation: atomic increment of tick counter.
    // Relaxed ordering is sufficient here because:
    //   - No other data is ordered relative to this store
    //   - Atomic itself prevents torn reads/writes
    TICK_COUNT.fetch_add(1, Ordering::Relaxed);
}

// ─── USART2 Interrupt Handler ──────────────────────────────────────────
//
// The #[interrupt] attribute from cortex-m-rt:
//   1. Name must match exactly what's in the device's interrupt enum
//   2. Generates correct NVIC vector table entry
//   3. Handles EXC_RETURN correctly
//
#[interrupt]
fn USART2() {
    // Access the global producer inside a critical section.
    //
    // critical_section::with / cortex_m::interrupt::free:
    //   - Disables all interrupts (sets PRIMASK=1)
    //   - Provides a CriticalSection token
    //   - Re-enables interrupts on exit
    //   - This is the safe way to access Mutex<RefCell<T>>
    //
    cortex_m::interrupt::free(|cs| {
        // Get a reference to the USART2 peripheral registers
        // Safety: We're in the ISR for USART2, no other code
        //         runs on this core right now (interrupts disabled
        //         by the critical section / ISR context).
        let dp = unsafe { pac::Peripherals::steal() };
        let usart = &dp.USART2;

        // Read Status Register
        let sr = usart.sr.read();

        // Check for Receive Not Empty
        if sr.rxne().bit_is_set() {
            // Read Data Register — this clears RXNE flag
            let byte = usart.dr.read().dr().bits() as u8;

            // Try to push to the lock-free queue
            if let Some(ref mut producer) = *UART_PRODUCER.borrow(cs).borrow_mut() {
                match producer.enqueue(byte) {
                    Ok(()) => {
                        // Signal main that data is available
                        UART_DATA_READY.store(true, Ordering::Release);
                        // Release ordering: ensures the enqueue is
                        // visible BEFORE the flag store (memory barrier)
                    }
                    Err(_) => {
                        // Queue full — byte dropped
                        // In production: increment overflow counter
                    }
                }
            }
        }

        // Check for Overrun Error — must clear it or UART stops working!
        if sr.ore().bit_is_set() {
            // Read DR to clear ORE (per STM32 reference manual)
            let _ = usart.dr.read().dr().bits();
        }
    });
}

// ─── HardFault Exception Handler ──────────────────────────────────────
//
// Called when CPU encounters an unrecoverable error:
//   - Invalid memory access
//   - Unaligned access (if strict alignment enabled)
//   - Execute from XN (Execute Never) region
//   - Stack overflow
//
// The ExceptionFrame contains the stacked register values at the
// point of the fault — invaluable for debugging.
//
#[exception]
unsafe fn HardFault(ef: &cortex_m_rt::ExceptionFrame) -> ! {
    // In production embedded: log to persistent storage (flash/EEPROM),
    // then reset. Here we just loop (visible in debugger).
    //
    // ef contains: r0, r1, r2, r3, r12, lr, pc, xpsr
    // ef.pc() is the address of the faulting instruction!
    let _ = ef;

    // Signal fault via LED or UART if possible, then...
    loop {
        cortex_m::asm::bkpt();  // Trigger debugger breakpoint
    }
}

// ─── Entry Point ──────────────────────────────────────────────────────
#[entry]
fn main() -> ! {
    // Take ownership of device and core peripherals (singleton pattern)
    let dp = pac::Peripherals::take().unwrap();
    let cp = cortex_m::Peripherals::take().unwrap();

    // ── Clock configuration ──────────────────────────────────────────
    let rcc = dp.RCC.constrain();
    let clocks = rcc.cfgr
        .use_hse(8.MHz())       // External crystal: 8 MHz
        .sysclk(168.MHz())      // System clock: 168 MHz
        .pclk1(42.MHz())        // APB1 bus (USART2 is on APB1)
        .freeze();

    // ── SysTick configuration: 1ms tick ─────────────────────────────
    let mut syst = cp.SYST;
    syst.set_clock_source(cortex_m::peripheral::syst::SystClkSource::Core);
    syst.set_reload(168_000 - 1);   // 168MHz / 168000 = 1kHz = 1ms period
    syst.clear_current();
    syst.enable_counter();
    syst.enable_interrupt();        // Enables SysTick exception

    // ── UART configuration ───────────────────────────────────────────
    let gpioa = dp.GPIOA.split();
    let tx_pin = gpioa.pa2.into_alternate();
    let rx_pin = gpioa.pa3.into_alternate();

    let serial = Serial::new(
        dp.USART2,
        (tx_pin, rx_pin),
        Config::default().baudrate(115_200.bps()),
        &clocks,
    ).unwrap();

    let (_tx, mut _rx) = serial.split();

    // ── Initialize the SPSC queue and get producer/consumer ─────────
    // This must happen before enabling the USART interrupt!
    static mut QUEUE_STORAGE: Queue<u8, 64> = Queue::new();

    let (producer, mut consumer) = unsafe { QUEUE_STORAGE.split() };

    // Install producer into the global (inside critical section)
    cortex_m::interrupt::free(|cs| {
        *UART_PRODUCER.borrow(cs).borrow_mut() = Some(producer);
    });

    // ── Enable USART2 interrupt in NVIC ─────────────────────────────
    // Safety: We've set up the ISR and global state above.
    unsafe {
        pac::NVIC::unmask(hal_interrupt::USART2);
        pac::NVIC::set_priority(
            &mut cortex_m::Peripherals::steal().NVIC,
            hal_interrupt::USART2,
            16,   // Priority 1 (lower number = higher priority on Cortex-M4)
        );
    }

    // ── Main loop: bottom-half processing ────────────────────────────
    loop {
        // Check if ISR signalled new data
        if UART_DATA_READY.load(Ordering::Acquire) {
            // Acquire ordering: ensures we see the enqueue
            // that happened BEFORE the flag store in ISR.

            UART_DATA_READY.store(false, Ordering::Relaxed);

            // Drain the queue (runs with interrupts enabled!)
            while let Some(byte) = consumer.dequeue() {
                // Process the byte: echo, parse protocol, etc.
                // Can sleep, allocate, use locks here — we're in main context.
                let _ = byte;
            }
        }

        // Power-saving: sleep until next interrupt
        cortex_m::asm::wfi();
    }
}
```

### 20.3 — Rust RTIC (Real-Time Interrupt-driven Concurrency) Framework

RTIC is the recommended, idiomatic way to write ISR code in Rust embedded.
It eliminates data races at **compile time** using Rust's ownership system.

```rust
//! FILE: src/main.rs  (RTIC version)
//!
//! RTIC provides:
//!   - Task priorities (mapped to NVIC priorities)
//!   - Shared resources with automatic critical sections
//!   - No data races — verified at compile time by borrow checker
//!   - Deterministic scheduling
//!   - Software tasks (deferred work, like bottom-halves)
//!
//! Cargo.toml:
//!   [dependencies]
//!   rtic = { version = "2.1", features = ["thumbv7-backend"] }
//!   rtic-monotonics = "2.0"

#![no_std]
#![no_main]

use panic_halt as _;   // Panic handler: halt on panic

#[rtic::app(device = stm32f4xx_hal::pac, peripherals = true, dispatchers = [TIM2])]
mod app {
    use stm32f4xx_hal::{
        pac,
        prelude::*,
        serial::{Serial, config::Config, Rx, Tx},
        gpio::{Output, PushPull, PA5},
    };
    use heapless::spsc::{Queue, Producer, Consumer};
    use core::fmt::Write;

    // ─── Shared resources ─────────────────────────────────────────────
    //
    // Resources listed here are SHARED between tasks.
    // RTIC enforces that concurrent access uses critical sections.
    // The compiler verifies correctness!
    //
    #[shared]
    struct Shared {
        uart_tx: Tx<pac::USART2>,      // UART transmitter (shared)
        error_count: u32,              // Error counter (shared)
    }

    // ─── Local resources ──────────────────────────────────────────────
    //
    // Local resources are EXCLUSIVE to a single task — no sharing,
    // no locking needed. RTIC enforces this at compile time.
    //
    #[local]
    struct Local {
        uart_rx: Rx<pac::USART2>,      // UART receiver (local to UART task)
        led: PA5<Output<PushPull>>,    // Status LED (local to blink task)
        rx_producer: Producer<'static, u8, 64>,   // Queue producer (UART ISR)
        rx_consumer: Consumer<'static, u8, 64>,   // Queue consumer (process task)
    }

    // ─── Initialization ───────────────────────────────────────────────
    #[init(local = [
        // Static allocation inside init (safe — happens once before tasks start)
        rx_queue: Queue<u8, 64> = Queue::new()
    ])]
    fn init(ctx: init::Context) -> (Shared, Local) {
        let dp = ctx.device;
        let cp = ctx.core;

        // Clock setup
        let rcc = dp.RCC.constrain();
        let clocks = rcc.cfgr.sysclk(168.MHz()).freeze();

        // LED
        let gpioa = dp.GPIOA.split();
        let led = gpioa.pa5.into_push_pull_output();

        // UART
        let tx_pin = gpioa.pa2.into_alternate();
        let rx_pin = gpioa.pa3.into_alternate();
        let serial = Serial::new(
            dp.USART2,
            (tx_pin, rx_pin),
            Config::default().baudrate(115_200.bps()),
            &clocks,
        ).unwrap();
        let (uart_tx, uart_rx) = serial.split();

        // Split the queue
        let (rx_producer, rx_consumer) = ctx.local.rx_queue.split();

        // Schedule software task to run immediately
        blink::spawn().ok();

        (
            Shared { uart_tx, error_count: 0 },
            Local { uart_rx, led, rx_producer, rx_consumer },
        )
    }

    // ─── UART ISR — Hardware Task ──────────────────────────────────────
    //
    // #[task(binds = USART2, ...)] means this function is called when
    // the USART2 interrupt fires. RTIC maps it to the correct NVIC vector.
    //
    // priority = 2: Higher priority than idle (0) and blink (1).
    // Preempts blink task if blink is running.
    //
    // local: Resources exclusive to this task (no locking).
    // shared: Resources shared with other tasks (auto critical sections).
    //
    #[task(
        binds = USART2,
        priority = 2,
        local = [uart_rx, rx_producer],
        shared = [error_count]
    )]
    fn uart_isr(ctx: uart_isr::Context) {
        let rx = ctx.local.uart_rx;
        let producer = ctx.local.rx_producer;

        // Read from UART (non-blocking)
        match rx.read() {
            Ok(byte) => {
                // Push to queue — schedule process task if successful
                if producer.enqueue(byte).is_ok() {
                    // Spawn software task to process the data
                    process_uart::spawn().ok();
                }
            }
            Err(nb::Error::Other(e)) => {
                // Handle UART errors
                // Use lock() to safely access shared resource
                ctx.shared.error_count.lock(|count| {
                    *count += 1;
                });
                let _ = e;
            }
            Err(nb::Error::WouldBlock) => {
                // No data ready — spurious interrupt? Ignore.
            }
        }
    }

    // ─── Process UART Data — Software Task (Bottom-Half) ──────────────
    //
    // Software tasks are not bound to hardware interrupts.
    // They're dispatched by RTIC using a free interrupt (TIM2 here,
    // declared in dispatchers = [TIM2] above).
    //
    // priority = 1: Lower priority than UART ISR (2).
    // Can be preempted by UART ISR — correct behavior!
    //
    #[task(
        priority = 1,
        local = [rx_consumer],
        shared = [uart_tx]
    )]
    async fn process_uart(ctx: process_uart::Context) {
        let consumer = ctx.local.rx_consumer;

        while let Some(byte) = consumer.dequeue() {
            // Process the byte (echo it back)
            ctx.shared.uart_tx.lock(|tx| {
                // write! uses the UART TX
                write!(tx, "{}", byte as char).ok();
            });
        }
    }

    // ─── Blink Task — Periodic Software Task ──────────────────────────
    //
    // Demonstrates a periodic task (heartbeat LED).
    // Uses rtic-monotonics for delay.
    //
    #[task(priority = 1, local = [led])]
    async fn blink(ctx: blink::Context) {
        loop {
            ctx.local.led.toggle();
            // In a real system: rtic_monotonics::systick::Systick::delay(500.millis()).await;
            // Simplified loop here
            for _ in 0..1_000_000 {
                cortex_m::asm::nop();
            }
        }
    }

    // ─── Idle Task ────────────────────────────────────────────────────
    //
    // Runs when no other task is ready. Priority = 0 (lowest).
    // Never returns. Good place to put WFI for power saving.
    //
    #[idle]
    fn idle(_ctx: idle::Context) -> ! {
        loop {
            cortex_m::asm::wfi();  // Sleep until next interrupt
        }
    }
}
```

### 20.4 — Rust: POSIX Signal Handling (Linux/macOS systems programming)

```rust
//! FILE: src/main.rs
//! Signal handling in Rust — the userspace analog of ISRs.
//!
//! POSIX signals ARE software interrupts delivered to processes.
//! They're the OS-level mechanism for async event notification.
//!
//! IMPORTANT: Signal handlers have the SAME restrictions as ISRs!
//!   - Cannot call non-async-signal-safe functions
//!   - Cannot use mutexes (deadlock risk)
//!   - Cannot allocate memory
//!   - Should only set atomic flags or call async-signal-safe functions
//!
//! Cargo.toml:
//!   [dependencies]
//!   libc = "0.2"
//!   signal-hook = "0.3"   # Safe signal handling library

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::thread;
use std::time::Duration;

// ─── Atomic shared state (safe for signal handlers) ───────────────────
static SHUTDOWN_REQUESTED: AtomicBool = AtomicBool::new(false);
static RELOAD_CONFIG:      AtomicBool = AtomicBool::new(false);
static SIGNAL_COUNT:       AtomicU64  = AtomicU64::new(0);

// ─── Method 1: Using signal-hook crate (recommended, safe) ────────────
fn run_with_signal_hook() -> Result<(), Box<dyn std::error::Error>> {
    use signal_hook::{
        consts::{SIGINT, SIGTERM, SIGHUP, SIGUSR1},
        flag,
        iterator::Signals,
    };

    // Register signals to set atomic flags when received.
    // signal-hook uses correct async-signal-safe mechanisms internally.
    //
    // SIGINT  → Ctrl+C → request shutdown
    // SIGTERM → kill   → request shutdown
    flag::register(SIGINT,  SHUTDOWN_REQUESTED.clone())?;
    flag::register(SIGTERM, SHUTDOWN_REQUESTED.clone())?;

    // Alternative: use Signals iterator for more control
    let mut signals = Signals::new([SIGINT, SIGTERM, SIGHUP, SIGUSR1])?;

    // Signal handling thread — receives signals and dispatches them
    let handle = signals.handle();
    let signal_thread = thread::spawn(move || {
        for sig in &mut signals {
            SIGNAL_COUNT.fetch_add(1, Ordering::Relaxed);

            match sig {
                SIGINT | SIGTERM => {
                    eprintln!("\n[signal] Shutdown requested (signal {})", sig);
                    SHUTDOWN_REQUESTED.store(true, Ordering::Release);
                }
                SIGHUP => {
                    eprintln!("[signal] SIGHUP received — reload config");
                    RELOAD_CONFIG.store(true, Ordering::Release);
                }
                SIGUSR1 => {
                    eprintln!("[signal] SIGUSR1 — status dump");
                    // Print status (this is in a thread, not signal context — safe!)
                    println!("  Total signals received: {}",
                             SIGNAL_COUNT.load(Ordering::Relaxed));
                }
                _ => {}
            }
        }
    });

    // ── Main loop ────────────────────────────────────────────────────
    println!("[main] Running. PID: {}", std::process::id());
    println!("[main] Send SIGINT (Ctrl+C), SIGHUP, or SIGUSR1 to test");

    let mut work_cycle = 0u64;

    loop {
        // Check for shutdown — Acquire ensures we see all stores
        // that happened before the signal handler's Release store.
        if SHUTDOWN_REQUESTED.load(Ordering::Acquire) {
            println!("[main] Shutdown detected. Cleaning up...");
            break;
        }

        // Check for config reload
        if RELOAD_CONFIG.swap(false, Ordering::AcqRel) {
            println!("[main] Reloading configuration...");
            // reload_config();
        }

        // Do actual work
        work_cycle += 1;
        thread::sleep(Duration::from_millis(100));

        if work_cycle % 10 == 0 {
            println!("[main] Work cycle {} (signals: {})",
                     work_cycle,
                     SIGNAL_COUNT.load(Ordering::Relaxed));
        }
    }

    // Cleanup
    handle.close();             // Stop the signal iterator
    signal_thread.join().ok();  // Wait for signal thread to finish

    println!("[main] Clean shutdown complete.");
    Ok(())
}

// ─── Method 2: Raw libc signal handler (educational — shows the C API) ─
//
// WARNINGS:
//   - This is UNSAFE Rust — we're using C signal APIs directly
//   - The handler must only use async-signal-safe operations
//   - No Rust standard library functions inside the handler!
//   - This is shown for educational purposes; prefer signal-hook in production
//
mod raw_signal {
    use std::sync::atomic::{AtomicBool, Ordering};

    static CAUGHT: AtomicBool = AtomicBool::new(false);

    /// The actual signal handler — called by OS when signal fires.
    ///
    /// # Safety
    /// - Must only call async-signal-safe functions (see man 7 signal-safety)
    /// - Must not use Rust's allocator, mutexes, or panicking functions
    /// - Parameters: signum = the signal number that was received
    extern "C" fn signal_handler(signum: libc::c_int) {
        // Store is async-signal-safe (atomic operation)
        CAUGHT.store(true, Ordering::Release);

        // write() is async-signal-safe (direct syscall, no buffering)
        let msg = b"[handler] Signal caught!\n";
        unsafe {
            libc::write(libc::STDOUT_FILENO, msg.as_ptr() as *const _, msg.len());
        }

        let _ = signum;
    }

    /// Install the raw signal handler using sigaction (more reliable than signal())
    pub fn install() {
        unsafe {
            // sigaction is the modern, preferred way to install signal handlers
            // It's more portable and predictable than the legacy signal() call
            let mut sa: libc::sigaction = core::mem::zeroed();

            // Set our handler function
            sa.sa_sigaction = signal_handler as libc::sighandler_t;

            // SA_RESTART: Automatically restart interrupted system calls
            // Without this, syscalls like read() return EINTR on signal delivery
            sa.sa_flags = libc::SA_RESTART;

            // Install for SIGUSR2
            libc::sigaction(libc::SIGUSR2, &sa, core::ptr::null_mut());
        }
    }

    pub fn was_caught() -> bool {
        CAUGHT.swap(false, Ordering::AcqRel)
    }
}

fn main() {
    // Install raw handler (educational)
    raw_signal::install();

    // Run main program with safe signal handling
    if let Err(e) = run_with_signal_hook() {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }
}
```

---

## CHAPTER 21 — ISR IN GO: SIGNAL HANDLING & RUNTIME

### 21.1 — Go's Relationship to Interrupts

Go is a high-level language with a runtime (goroutine scheduler,
garbage collector, etc.). It doesn't provide direct access to
hardware interrupts in user space. However:

```
WHAT GO PROVIDES FOR INTERRUPT-LIKE BEHAVIOR:

  1. os/signal package:
     Intercepts POSIX signals delivered to the process.
     The Go runtime translates OS signals to Go channel messages.
     This is the userspace equivalent of ISRs.

  2. Goroutines + channels:
     Natural top-half/bottom-half pattern.
     Signal goroutine = top-half (catches signal fast).
     Worker goroutine = bottom-half (processes it).

  3. sync/atomic:
     Lock-free operations for shared state.
     Same rules apply: atomic for simple flags, channels for data.

  4. CGo + Linux kernel modules:
     For actual hardware ISRs in Go, you'd write a C kernel module
     and use CGo to interface. (Rare but possible.)

  NOTE: Go's garbage collector can pause goroutines arbitrarily.
  This makes Go unsuitable for hard real-time systems.
  For soft real-time (latency in milliseconds is OK), Go works well.
```

### 21.2 — Complete Signal Handler Implementation in Go

```go
// FILE: main.go
// Comprehensive signal handling in Go.
// Demonstrates: top-half/bottom-half, graceful shutdown,
// signal multiplexing, timeouts, and context cancellation.

package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
)

// ─── Shared atomic state (safe to read without locking) ───────────────
//
// In Go, sync/atomic provides CPU-level atomic operations.
// These are safe to use from goroutines receiving signals.
//
var (
	signalCount   atomic.Int64  // Total signals received
	requestCount  atomic.Int64  // Total requests processed (demo)
	isShuttingDown atomic.Bool  // Shutdown in progress flag
)

// ─── Signal Event: structured signal notification ──────────────────────
//
// Instead of just passing raw signal numbers, we pass structured events.
// This is the Go-idiomatic "bottom-half" pattern: ISR puts minimal data
// into a channel; worker goroutine processes the event.
//
type SignalEvent struct {
	Signal    os.Signal     // The signal received
	Timestamp time.Time     // When it was received
	Count     int64         // Which occurrence this is
}

// ─── Application: represents our server/service ────────────────────────
type Application struct {
	// Channels for signal routing (the "bus" between top-half and bottom-half)
	sigChan     chan os.Signal // Raw OS signal channel (buffered!)
	eventChan   chan SignalEvent // Structured event channel

	// Context for graceful shutdown propagation
	ctx    context.Context
	cancel context.CancelFunc

	// WaitGroup to track all goroutines
	wg sync.WaitGroup

	// Metrics
	startTime time.Time
}

// ─── NewApplication creates and initializes the application ───────────
func NewApplication() *Application {
	ctx, cancel := context.WithCancel(context.Background())

	return &Application{
		// Buffer size CRITICAL for signal channels!
		// If the channel is full when a signal arrives, signal.Notify DROPS IT.
		// Buffer of 10 ensures we don't miss rapid signals.
		sigChan:   make(chan os.Signal, 10),
		eventChan: make(chan SignalEvent, 100),

		ctx:       ctx,
		cancel:    cancel,
		startTime: time.Now(),
	}
}

// ─── TOP-HALF: Signal Receiver Goroutine ──────────────────────────────
//
// This goroutine is the equivalent of an ISR top-half:
//   - Runs continuously waiting for signals
//   - Receives signals from the OS via signal.Notify channel
//   - Does MINIMAL work: timestamps, counts, routes to event channel
//   - Never blocks (uses non-blocking send to eventChan)
//
// HOW Go signal handling works under the hood:
//   - Go runtime installs a real POSIX signal handler (in C, in the runtime)
//   - That C handler writes to an internal pipe
//   - The runtime's signal goroutine reads the pipe and sends to
//     registered channels via signal.Notify
//   - This gives us a channel-based API without the async-signal-safety
//     restrictions of raw C handlers!
//
func (app *Application) signalReceiver() {
	defer app.wg.Done()

	log.Println("[top-half] Signal receiver goroutine started")

	for {
		select {
		case sig, ok := <-app.sigChan:
			if !ok {
				// Channel closed — we're done
				log.Println("[top-half] Signal channel closed, exiting")
				return
			}

			// TOP-HALF WORK: Minimal, fast, non-blocking
			count := signalCount.Add(1)

			event := SignalEvent{
				Signal:    sig,
				Timestamp: time.Now(),
				Count:     count,
			}

			// Non-blocking send to bottom-half event channel
			// If full: we lose the event (acceptable for signals)
			select {
			case app.eventChan <- event:
				// Successfully queued
			default:
				// Event channel full — log and continue
				// DO NOT BLOCK HERE — this is the top-half!
				log.Printf("[top-half] WARNING: event channel full, dropped signal %v", sig)
			}

		case <-app.ctx.Done():
			log.Println("[top-half] Context cancelled, shutting down")
			return
		}
	}
}

// ─── BOTTOM-HALF: Signal Event Processor ──────────────────────────────
//
// This goroutine processes signal events at a comfortable pace.
// It CAN block, sleep, allocate, log, etc.
// It's decoupled from the signal reception — can lag behind.
//
func (app *Application) signalProcessor() {
	defer app.wg.Done()

	log.Println("[bottom-half] Signal processor goroutine started")

	for {
		select {
		case event, ok := <-app.eventChan:
			if !ok {
				return
			}

			// BOTTOM-HALF WORK: Full processing power available
			app.processSignalEvent(event)

		case <-app.ctx.Done():
			// Drain remaining events before exiting
			for {
				select {
				case event := <-app.eventChan:
					app.processSignalEvent(event)
				default:
					log.Println("[bottom-half] Event queue drained, exiting")
					return
				}
			}
		}
	}
}

// ─── processSignalEvent: dispatch signal to specific handlers ──────────
func (app *Application) processSignalEvent(event SignalEvent) {
	log.Printf("[bottom-half] Processing signal #%d: %v (received at %v)",
		event.Count, event.Signal, event.Timestamp.Format(time.RFC3339Nano))

	switch event.Signal {

	case syscall.SIGINT, syscall.SIGTERM:
		// ── Graceful Shutdown ─────────────────────────────────────────
		// These are the "turn off" signals.
		// SIGINT = Ctrl+C (user interrupt)
		// SIGTERM = kill <pid> (system shutdown request)

		if isShuttingDown.CompareAndSwap(false, true) {
			// Only handle if not already shutting down (first SIGINT)
			log.Println("[bottom-half] Initiating graceful shutdown...")

			// Cancel the root context — this propagates to ALL goroutines
			// that are using ctx (worker goroutines, HTTP server, etc.)
			app.cancel()
		} else {
			// Second SIGINT while shutting down — force immediate exit
			log.Println("[bottom-half] Forced exit (second signal)")
			os.Exit(1)
		}

	case syscall.SIGHUP:
		// ── Configuration Reload ──────────────────────────────────────
		// Traditional Unix: SIGHUP means "re-read config file".
		// Servers (nginx, sshd) use this for zero-downtime config updates.
		log.Println("[bottom-half] Reloading configuration...")
		app.reloadConfig()

	case syscall.SIGUSR1:
		// ── User-Defined Signal 1: Status Report ──────────────────────
		app.printStatus()

	case syscall.SIGUSR2:
		// ── User-Defined Signal 2: Custom action ──────────────────────
		log.Println("[bottom-half] SIGUSR2 — custom action triggered")

	case syscall.SIGCHLD:
		// ── Child Process Status Change ───────────────────────────────
		// Fires when a child process exits, stops, or resumes.
		log.Println("[bottom-half] Child process state changed")

	default:
		log.Printf("[bottom-half] Unhandled signal: %v", event.Signal)
	}
}

// ─── reloadConfig: simulate configuration reload ────────────────────────
func (app *Application) reloadConfig() {
	// In a real server: re-read config files, hot-swap settings,
	// drain old connections, accept new ones with new config.
	// This can block — that's fine in the bottom-half goroutine!
	log.Println("[config] Reading configuration file...")
	time.Sleep(50 * time.Millisecond) // Simulate I/O
	log.Println("[config] Configuration reloaded successfully")
}

// ─── printStatus: print runtime statistics ──────────────────────────────
func (app *Application) printStatus() {
	uptime := time.Since(app.startTime).Round(time.Second)
	fmt.Printf("\n=== Application Status ===\n")
	fmt.Printf("  Uptime:          %v\n", uptime)
	fmt.Printf("  Signals caught:  %d\n", signalCount.Load())
	fmt.Printf("  Requests served: %d\n", requestCount.Load())
	fmt.Printf("  Shutting down:   %v\n", isShuttingDown.Load())
	fmt.Printf("==========================\n\n")
}

// ─── workerGoroutine: simulates actual application work ────────────────
func (app *Application) workerGoroutine(id int) {
	defer app.wg.Done()

	log.Printf("[worker-%d] Started", id)

	for {
		select {
		case <-app.ctx.Done():
			// Context cancelled — shutdown gracefully
			log.Printf("[worker-%d] Shutting down (pending work flushed)", id)
			return

		default:
			// Simulate doing work (HTTP request, database query, etc.)
			requestCount.Add(1)

			// Simulate work duration (interruptible by context)
			select {
			case <-time.After(200 * time.Millisecond):
				// Work completed normally
			case <-app.ctx.Done():
				// Interrupted during work — that's OK, we handle above
			}
		}
	}
}

// ─── SetupSignals: register all signals we want to handle ──────────────
func (app *Application) SetupSignals() {
	// Tell the Go runtime: route these signals to our channel.
	// Signals NOT registered here will use Go's default handlers
	// (e.g., SIGSEGV → print stack trace and crash, which is correct).
	//
	// IMPORTANT: signal.Notify is NOT async-signal-safe by Go spec,
	// but the implementation IS safe because Go runtime uses
	// internal self-pipe tricks.
	signal.Notify(
		app.sigChan,
		syscall.SIGINT,   // Ctrl+C
		syscall.SIGTERM,  // kill/systemd stop
		syscall.SIGHUP,   // config reload
		syscall.SIGUSR1,  // status dump
		syscall.SIGUSR2,  // custom
		syscall.SIGCHLD,  // child processes
	)

	log.Println("[setup] Signal handlers registered")
	log.Printf("[setup] PID: %d", os.Getpid())
	log.Println("[setup] Send signals: kill -SIGUSR1 <pid>  | kill -SIGHUP <pid>")
}

// ─── Run: main application loop ─────────────────────────────────────────
func (app *Application) Run() {
	app.SetupSignals()

	// Start top-half goroutine
	app.wg.Add(1)
	go app.signalReceiver()

	// Start bottom-half goroutine
	app.wg.Add(1)
	go app.signalProcessor()

	// Start worker goroutines
	numWorkers := 3
	for i := 0; i < numWorkers; i++ {
		app.wg.Add(1)
		go app.workerGoroutine(i + 1)
	}

	log.Printf("[main] Application running with %d workers", numWorkers)

	// Wait for shutdown signal
	<-app.ctx.Done()
	log.Println("[main] Shutdown initiated — waiting for goroutines to finish...")

	// Stop accepting new signals
	signal.Stop(app.sigChan)
	close(app.sigChan)

	// Wait for all goroutines with timeout
	done := make(chan struct{})
	go func() {
		app.wg.Wait()
		close(done)
	}()

	select {
	case <-done:
		log.Println("[main] All goroutines finished. Clean shutdown.")
	case <-time.After(30 * time.Second):
		log.Println("[main] Timeout waiting for goroutines! Force exit.")
		os.Exit(1)
	}
}

func main() {
	log.SetFlags(log.LstdFlags | log.Lmicroseconds)
	log.Println("[main] Starting application...")

	app := NewApplication()
	app.Run()

	log.Println("[main] Exited cleanly.")
}
```

### 21.3 — Go: Simulating Interrupt-Driven I/O with Channels

```go
// FILE: interrupt_sim.go
// Demonstrates interrupt-driven I/O simulation in Go.
// Models: hardware interrupt → ISR → event queue → processor
//
// This pattern mirrors exactly how a hardware UART ISR works,
// but in pure Go userspace code.

package main

import (
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"
)

// ─── Simulated Hardware Device ─────────────────────────────────────────
type SimulatedUART struct {
	irqChan     chan byte    // "IRQ line" — hardware sends bytes here
	isrHandler  func(byte)  // The registered "ISR"
	running     atomic.Bool
}

// SimulateHardware: pretends to be a UART receiving bytes asynchronously
func (u *SimulatedUART) SimulateHardware() {
	data := []byte("Hello, ISR World!\nThis is a test message.\n")
	idx := 0

	for u.running.Load() {
		// Simulate asynchronous byte arrival (random intervals)
		delay := time.Duration(rand.Intn(50)+10) * time.Millisecond
		time.Sleep(delay)

		if idx < len(data) {
			// "Pulse the IRQ line" — send byte to ISR channel
			u.irqChan <- data[idx]
			idx++
		} else {
			idx = 0 // Loop the message
		}
	}
	close(u.irqChan)
}

// ─── ISR Framework ─────────────────────────────────────────────────────
type ISRFramework struct {
	uart     *SimulatedUART
	rxBuf    chan byte       // Ring buffer between ISR and main
	stats    struct {
		received atomic.Int64
		dropped  atomic.Int64
		processed atomic.Int64
	}
	wg sync.WaitGroup
}

func NewISRFramework() *ISRFramework {
	uart := &SimulatedUART{
		irqChan: make(chan byte, 1), // Unbuffered = immediate ISR invocation
	}

	f := &ISRFramework{
		uart:  uart,
		rxBuf: make(chan byte, 256), // Ring buffer (buffered channel)
	}

	// Register ISR (equivalent of writing ISR address into vector table)
	uart.isrHandler = f.uartISR

	return f
}

// ─── TOP-HALF: The ISR ─────────────────────────────────────────────────
//
// Called immediately when hardware "IRQ" fires.
// Minimal work: receive byte, put in ring buffer, return fast.
//
func (f *ISRFramework) uartISR(b byte) {
	f.stats.received.Add(1)

	// Non-blocking write to ring buffer
	// If buffer full → drop byte (models hardware FIFO overflow)
	select {
	case f.rxBuf <- b:
		// Success
	default:
		// Buffer full — byte dropped (ISR MUST NOT BLOCK)
		f.stats.dropped.Add(1)
	}
}

// ─── ISR Dispatcher: polls IRQ channel, calls ISR ──────────────────────
// In hardware, this is done by the CPU+NVIC automatically.
// In our simulation, we need an explicit goroutine.
func (f *ISRFramework) irqDispatcher() {
	defer f.wg.Done()

	for b := range f.uart.irqChan {
		// This is the "CPU acknowledges IRQ, calls ISR" moment
		f.uart.isrHandler(b)
	}
}

// ─── BOTTOM-HALF: Process received bytes ───────────────────────────────
func (f *ISRFramework) rxProcessor(done <-chan struct{}) {
	defer f.wg.Done()

	var lineBuffer []byte
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case b, ok := <-f.rxBuf:
			if !ok {
				return
			}
			f.stats.processed.Add(1)

			// Accumulate into line buffer (heavy processing here is OK)
			lineBuffer = append(lineBuffer, b)

			if b == '\n' {
				fmt.Printf("[RX] Line: %q\n", string(lineBuffer))
				lineBuffer = lineBuffer[:0] // Reset buffer
			}

		case <-ticker.C:
			// Periodic stats print
			fmt.Printf("[stats] received=%d dropped=%d processed=%d\n",
				f.stats.received.Load(),
				f.stats.dropped.Load(),
				f.stats.processed.Load())

		case <-done:
			// Drain remaining bytes
			for {
				select {
				case b := <-f.rxBuf:
					lineBuffer = append(lineBuffer, b)
				default:
					if len(lineBuffer) > 0 {
						fmt.Printf("[RX] Final: %q\n", string(lineBuffer))
					}
					return
				}
			}
		}
	}
}

func RunISRSimulation() {
	fmt.Println("=== ISR Framework Simulation ===")
	fmt.Println("Simulating UART receive with top-half ISR and bottom-half processor")
	fmt.Println()

	f := NewISRFramework()
	done := make(chan struct{})

	// Start simulated hardware
	f.uart.running.Store(true)
	go f.uart.SimulateHardware()

	// Start ISR dispatcher (simulates CPU IRQ handling)
	f.wg.Add(1)
	go f.irqDispatcher()

	// Start bottom-half processor
	f.wg.Add(1)
	go f.rxProcessor(done)

	// Run for 3 seconds
	time.Sleep(3 * time.Second)

	// Shutdown
	f.uart.running.Store(false)
	close(done)
	f.wg.Wait()

	fmt.Println("\n=== Final Statistics ===")
	fmt.Printf("  Bytes received:  %d\n", f.stats.received.Load())
	fmt.Printf("  Bytes dropped:   %d\n", f.stats.dropped.Load())
	fmt.Printf("  Bytes processed: %d\n", f.stats.processed.Load())
}

func main() {
	RunISRSimulation()
}
```

---

## CHAPTER 22 — REAL-WORLD EXAMPLES

### Example 1: Watchdog Timer ISR

A watchdog timer resets the system if the main program stops
"feeding" it (writing to it periodically). Detects hangs/deadlocks.

```c
/*
 * Watchdog ISR Pattern (ARM Cortex-M, STM32)
 *
 * IWDG (Independent Watchdog) on STM32 runs from the LSI oscillator
 * and cannot be disabled once started — true watchdog.
 */

/* ── Watchdog state ── */
static volatile uint32_t wdg_kick_count   = 0;
static volatile uint32_t wdg_expire_count = 0;

/* ── WWDG (Window Watchdog) ISR — fires just BEFORE expiry
 * This gives software a last chance to:
 *   1. Kick the watchdog (if system is healthy)
 *   2. Log the impending reset (if system is stuck)
 *   3. Save critical state to flash before reset
 */
void WWDG_IRQHandler(void)
{
    /* Check if main loop has been kicking the watchdog */
    if (wdg_kick_count > 0) {
        /* System is alive — reload watchdog counter */
        WWDG->CR = WWDG_CR_WDGA | 0x7F;   /* Reload to max value */
        wdg_kick_count = 0;
        return;
    }

    /* System appears hung — log and allow reset */
    wdg_expire_count++;

    /* Save diagnostics to backup registers (survive reset) */
    RTC->BKP0R = wdg_expire_count;
    RTC->BKP1R = (uint32_t)__get_PC();   /* PC when watchdog fired */

    /* Do NOT reload — system will reset */
    /* In ~4ms (next WWDG expiry), CPU resets */
}

/* ── Main loop must "feed" watchdog regularly ── */
void main_loop(void)
{
    while (1) {
        do_periodic_work();

        /* Watchdog kick — must happen before WWDG ISR sees kick_count=0 */
        wdg_kick_count++;    /* Atomic on 32-bit Cortex-M (single write) */

        /* Sleep until next tick */
        __WFI();
    }
}
```

### Example 2: DMA Transfer Complete ISR

Direct Memory Access (DMA) transfers data between peripherals and
RAM without CPU involvement. ISR fires when transfer is complete.

```c
/*
 * DMA Transfer Complete ISR (STM32 ADC via DMA)
 *
 * Scenario: ADC samples 1024 values continuously via DMA.
 *           When buffer is full, ISR fires → process the buffer.
 *
 * This is DOUBLE-BUFFERING: while ISR processes buffer A,
 * DMA fills buffer B (ping-pong buffers).
 */

#define ADC_BUF_SIZE 1024

/* Double buffer: DMA uses one, CPU processes the other */
static volatile uint16_t adc_buf[2][ADC_BUF_SIZE];
static volatile uint8_t  process_buf_idx = 0;   /* Which buffer to process */
static volatile uint8_t  data_ready      = 0;

/* DMA Stream 0 ISR (for ADC1 DMA on STM32F4) */
void DMA2_Stream0_IRQHandler(void)
{
    uint32_t hisr = DMA2->HISR;
    uint32_t lisr = DMA2->LISR;

    if (lisr & DMA_LISR_TCIF0) {
        /* ── Transfer Complete: first half buffer full ──────────────── */
        DMA2->LIFCR = DMA_LIFCR_CTCIF0;   /* Clear TC flag */

        /* Tell main loop: buffer 0 is ready to process */
        process_buf_idx = 0;
        data_ready = 1;

        /* DMA automatically starts filling buffer 1 (circular mode) */
    }

    if (lisr & DMA_LISR_HTIF0) {
        /* ── Half Transfer: second half buffer full ─────────────────── */
        DMA2->LIFCR = DMA_LIFCR_CHTIF0;

        /* Tell main loop: buffer 1 is ready */
        process_buf_idx = 1;
        data_ready = 1;
    }

    if (lisr & DMA_LISR_TEIF0) {
        /* ── Transfer Error ────────────────────────────────────────── */
        DMA2->LIFCR = DMA_LIFCR_CTEIF0;
        /* Handle error: log, restart DMA, alert user */
    }

    (void)hisr;
}

/* Main loop: FFT analysis on completed ADC buffer */
void main_loop(void)
{
    while (1) {
        if (data_ready) {
            /* Snapshot index atomically (single read on 32-bit ARM) */
            uint8_t idx = process_buf_idx;
            data_ready = 0;

            /* Process buffer[idx] while DMA fills the other buffer */
            /* This can take milliseconds — that's fine! DMA runs in parallel */
            compute_fft((uint16_t*)adc_buf[idx], ADC_BUF_SIZE);
        }

        __WFI();   /* Wait for next DMA complete interrupt */
    }
}
```

### Example 3: Network Packet ISR (Linux NIC Driver)

```c
/*
 * Simplified NIC (Network Interface Card) ISR
 * Follows Linux NAPI (New API) pattern for high-performance networking.
 *
 * NAPI pattern:
 *   1. ISR fires on first packet
 *   2. ISR disables further RX interrupts (prevent interrupt storm)
 *   3. ISR schedules NAPI poll
 *   4. NAPI poll function runs as softirq, processes up to N packets
 *   5. If no more packets: re-enable RX interrupt, exit NAPI
 */

#include <linux/netdevice.h>
#include <linux/etherdevice.h>

/* ── NAPI poll: bottom-half, processes packets ── */
static int nic_napi_poll(struct napi_struct *napi, int budget)
{
    struct nic_priv *priv = container_of(napi, struct nic_priv, napi);
    int work_done = 0;

    /* Process up to 'budget' packets per poll */
    while (work_done < budget) {
        struct sk_buff *skb = nic_receive_packet(priv);
        if (!skb)
            break;

        /* Pass packet up to network stack */
        napi_gro_receive(napi, skb);
        work_done++;
    }

    /* If we processed fewer than budget: no more packets */
    if (work_done < budget) {
        /* Re-enable RX interrupt */
        nic_enable_rx_interrupt(priv);

        /* Exit NAPI polling mode */
        napi_complete_done(napi, work_done);
    }

    return work_done;
}

/* ── Top-half ISR: minimal, just triggers NAPI ── */
static irqreturn_t nic_irq_handler(int irq, void *dev_id)
{
    struct net_device *netdev = dev_id;
    struct nic_priv   *priv   = netdev_priv(netdev);

    /* Read and clear interrupt status */
    u32 status = nic_read_status(priv);
    if (!(status & NIC_INT_RX_DONE))
        return IRQ_NONE;

    /* Disable RX interrupt to prevent storm */
    nic_disable_rx_interrupt(priv);

    /* Schedule NAPI poll (runs as NET_RX_SOFTIRQ) */
    napi_schedule(&priv->napi);

    return IRQ_HANDLED;
}
```

---

## CHAPTER 23 — COMMON PITFALLS & DEBUGGING

### Pitfall Map — Decision Tree for Debugging ISR Issues

```
                    ISR NOT WORKING?
                          │
              ┌───────────┴───────────┐
         ISR never fires          ISR fires but wrong behavior
              │                            │
    ┌─────────┴──────────┐        ┌────────┴────────┐
    │                    │        │                 │
 Vector not          IRQ not   Shared data      ISR too slow
 registered         enabled    corrupt          (misses events)
    │                    │        │                 │
 Check IDT/          Check:   Check:            Check:
 vector table      - NVIC     - volatile         - ISR length
 entry is set      - PIC mask - atomic ops       - is blocking
 and present       - IF flag  - memory bars      - print calls
                   - IRQ wire - critical sec      - malloc calls
                               aligned access
                               
         ┌─────────────────────────────────┐
         │    COMMON BUGS CHECKLIST         │
         ├─────────────────────────────────┤
         │ □ Forgot EOI → no more IRQs     │
         │ □ Shared var not volatile       │
         │ □ Stack overflow (nested ISRs)  │
         │ □ malloc/free in ISR            │
         │ □ mutex_lock in ISR (deadlock)  │
         │ □ printf in ISR                 │
         │ □ Missing memory barrier        │
         │ □ IRQ not unmasked in NVIC      │
         │ □ Wrong IRQ priority            │
         │ □ Hardware not configured       │
         │ □ ISR clears wrong status bits  │
         └─────────────────────────────────┘
```

### Classic Bug: The Vanishing ISR (Optimizer Kills Volatile)

```c
/* BUG: Compiler optimizes away the wait loop */
int flag = 0;   /* <-- MISSING volatile! */

void my_isr(void) { flag = 1; }

void wait_for_event(void) {
    while (flag == 0) { }   /* Compiler sees flag never changes HERE
                               so it removes the check entirely!
                               Compiles to: while(1) {} infinite loop */
}

/* FIX: */
volatile int flag = 0;   /* Now compiler MUST re-read from memory */
```

### Classic Bug: Non-Atomic Read-Modify-Write

```c
/* BUG on 8-bit/16-bit MCUs with 32-bit variable */
volatile uint32_t counter = 0;

void isr(void) { counter++; }   /* NOT atomic on 8-bit CPU! */

/* On an 8-bit CPU, counter++ is:
   LOAD  r0, counter+0  ; load low byte
   LOAD  r1, counter+1  ; ISR FIRES HERE! counter = counter+1
   LOAD  r2, counter+2  ; now we load stale high bytes!
   LOAD  r3, counter+3
   ADD   ...
   STORE
   
   RESULT: corrupted counter! */

/* FIX: Disable interrupts around 32-bit access on 8-bit CPU */
uint32_t read_counter(void) {
    uint32_t val;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
        val = counter;
    }
    return val;
}
```

### Classic Bug: Deadlock — Lock in ISR

```c
/* Main code: */
pthread_mutex_lock(&my_mutex);      /* Acquires lock */
/* ... ISR fires here! ... */
pthread_mutex_unlock(&my_mutex);

/* ISR: */
void my_isr(void) {
    pthread_mutex_lock(&my_mutex);  /* DEADLOCK!
                                       Main has the lock and can't release it
                                       because ISR has preempted it.
                                       ISR waits for the lock forever.
                                       Main never resumes. DEADLOCK! */
}

/* FIX 1: Never use mutexes in ISR. Use spinlocks with irqsave. */
/* FIX 2: Use atomic operations instead. */
/* FIX 3: Use lock-free data structures (ring buffer, atomic queues). */
```

---

## CHAPTER 24 — ADVANCED TOPICS

### 24.1 — Interrupt Coalescing

Instead of processing one event per interrupt, batch multiple events:

```
WITHOUT COALESCING (100,000 packets/sec):
  100,000 interrupts/sec × ISR overhead = CPU overloaded!

WITH COALESCING:
  NIC hardware: accumulate N packets OR wait T microseconds,
                whichever comes first, THEN fire ONE interrupt.

  100,000 packets/sec ÷ 32 packets/interrupt = 3,125 interrupts/sec
  CPU overhead reduced by 32×!

  Linux: ethtool -C eth0 rx-usecs 50 rx-frames 32
  Tradeoff: Latency increases by up to 50μs per packet.
```

### 24.2 — Interrupt Affinity (Multi-Core)

In multi-core systems, each IRQ can be "pinned" to a specific CPU core:

```
INTERRUPT AFFINITY:

  Without pinning: OS routes IRQs to any core → cache thrashing
  
  With pinning: IRQ always handled by core 0 → warm cache, predictable
  
  Linux:
    cat /proc/irq/14/smp_affinity         # See current affinity mask
    echo "2" > /proc/irq/14/smp_affinity  # Pin to CPU1 (bit 1 set)

  Use case: Network driver pinned to CPU0,
            Application running on CPU1,
            NIC data in shared L3 cache → low latency!

  RSS (Receive Side Scaling): Hardware hashes flows to different queues,
  each queue has separate IRQ pinned to different core.
  Multi-core parallel packet processing!
```

### 24.3 — Real-Time Systems and Interrupt Jitter

```
JITTER = variation in interrupt latency

  Expected ISR latency: 5μs
  Actual measurements:  4.8μs, 5.1μs, 5.0μs, 47μs!, 5.2μs
                                                ↑
                                         JITTER spike!

CAUSES OF JITTER:
  1. Cache misses (ISR code/data not in cache)
  2. TLB misses (virtual address translation)
  3. Memory bus contention (DMA, other cores)
  4. Long instructions (REP string ops, FDIV)
  5. SMM (System Management Mode) — x86 steals CPU for BIOS tasks
  6. Interrupt storms from another device
  7. OS scheduler interference (non-RTOS systems)

SOLUTIONS (Real-Time Linux):
  1. PREEMPT_RT patch: Makes Linux kernel fully preemptible
  2. isolcpus: Isolate CPUs from scheduler → dedicate to RT tasks
  3. irq_affinity: Pin ISRs to specific cores
  4. mlockall(): Lock all memory → no page faults in RT code
  5. Use RTOS (FreeRTOS, Zephyr, QNX) for hard real-time
```

### 24.4 — Memory-Mapped I/O (MMIO) in ISRs

Hardware registers are accessed by reading/writing to specific
memory addresses (not regular RAM).

```
MMIO RULES IN ISRs:

  1. Use volatile for all MMIO accesses:
     volatile uint32_t *status_reg = (volatile uint32_t*)0x40020000;
     uint32_t val = *status_reg;   /* MUST read from hardware, not cache */

  2. Use memory barriers for ordered accesses:
     *ctrl_reg = ENABLE;           /* Write control register */
     wmb();                        /* Ensure write completes */
     *start_reg = START;           /* Then write start register */

  3. Use readl/writel (Linux kernel) or HAL functions:
     /* These have barriers built in */
     writel(value, base + CTRL_OFFSET);
     uint32_t v = readl(base + STATUS_OFFSET);

  4. Never let compiler reorder MMIO accesses:
     /* This is WRONG: */
     reg->start = 1;
     reg->config = mode;   /* Compiler might reorder these! */

     /* CORRECT: */
     reg->config = mode;   /* Configure first */
     wmb();                /* Barrier */
     reg->start = 1;       /* Then start */
```

---

## CHAPTER 25 — MENTAL MODELS & COGNITIVE STRATEGIES

### The Monk's Toolkit for Mastering ISRs

#### Mental Model 1: The Restaurant Analogy

```
ISR architecture maps perfectly to a restaurant:

  CUSTOMER ARRIVES (hardware event)
       ↓
  HOST SEATS THEM (interrupt controller routes IRQ)
       ↓
  WAITER TAKES ORDER — FAST (ISR top-half: collect data, schedule work)
       ↓
  KITCHEN COOKS (bottom-half: heavy processing, can take time)
       ↓
  WAITER SERVES (result delivered to application)

The waiter (ISR) must be fast — they can't cook (sleep/block).
The kitchen (workqueue/tasklet) can take time, but isn't blocking others.
```

#### Mental Model 2: The Concentric Circles of Trust

```
     ┌─────────────────────────────────┐
     │         USER SPACE              │
     │   (signals, safe, slow)         │
     │   ┌─────────────────────┐       │
     │   │    KERNEL SPACE     │       │
     │   │  (process context)  │       │
     │   │  ┌─────────────┐   │       │
     │   │  │  SOFTIRQ /  │   │       │
     │   │  │  TASKLET    │   │       │
     │   │  │ ┌─────────┐ │   │       │
     │   │  │ │   ISR   │ │   │       │
     │   │  │ │  (TOP   │ │   │       │
     │   │  │ │  HALF)  │ │   │       │
     │   │  │ └─────────┘ │   │       │
     │   │  └─────────────┘   │       │
     │   └─────────────────────┘       │
     └─────────────────────────────────┘

The INNER circle has the most restrictions.
As you move OUT, more capabilities become available.
ISR (innermost): no sleep, no alloc, ultra-fast.
Softirq: no sleep, can alloc.
Process context: full OS capabilities.
User space: everything (but slow path to hardware).
```

#### Mental Model 3: Atomic Thinking Pattern

Before touching any shared variable, ask yourself:

```
ATOMIC THINKING CHECKLIST:

  Q1: Is this variable accessed from both ISR and non-ISR context?
      YES → It's a shared variable → needs protection.

  Q2: Is it a single machine-word read or write?
      YES → May be atomic on your platform (check ABI!).
      NO  → Definitely NOT atomic → use atomic_t / Rust atomic.

  Q3: Is it read-modify-write (e.g., counter++)?
      YES → NEVER atomic without explicit atomic ops.
            Use: atomic_fetch_add(), fetch_add(), etc.

  Q4: Do you need to coordinate multiple variables atomically?
      YES → Critical section (disable interrupts) or lock.
            You CANNOT atomically update two separate variables
            without a mutex or interrupt disable.

  Q5: Is the ISR a writer and main() the only reader?
      YES → Lock-free SPSC ring buffer is your friend.
            No locks needed if access pattern is:
            ONE producer + ONE consumer + ring buffer size power of 2.
```

#### Deliberate Practice Protocol for ISRs

```
WEEK 1-2: Foundation
  □ Implement a bare-metal timer ISR from scratch (x86 or ARM)
  □ Implement keyboard ISR with ring buffer
  □ Measure interrupt latency with oscilloscope or logic analyzer

WEEK 3-4: Safety & Correctness
  □ Create a race condition intentionally, observe the bug
  □ Fix it with volatile + atomic
  □ Fix it with critical section
  □ Benchmark: which approach is faster?

WEEK 5-6: Architecture
  □ Implement top-half/bottom-half for a real device
  □ Implement priority nesting (2 ISRs at different priorities)
  □ Implement watchdog with ISR

WEEK 7-8: Advanced
  □ Write a Linux kernel driver with ISR and workqueue
  □ Profile interrupt latency jitter with perf/ftrace
  □ Port a C ISR to Rust using RTIC

COGNITIVE PRINCIPLE: Spaced Repetition
  Review each concept 1 day later, 1 week later, 1 month later.
  The discomfort of re-learning = the sensation of memory consolidation.
```

#### The Expert's Pre-Coding Ritual

Before writing a single line of ISR code, answer:

```
1. WHAT fires this interrupt?
   (Which hardware event? What is the exact condition?)

2. HOW OFTEN does it fire?
   (1Hz? 1kHz? 100kHz? This determines ISR time budget)

3. WHAT DATA must I collect?
   (Read status register? Drain FIFO? Copy DMA buffer?)

4. WHERE does the data go?
   (Ring buffer? Semaphore? Direct write? Atomic flag?)

5. WHAT is the bottom-half?
   (Who processes the data? In what context? With what latency?)

6. WHAT is shared?
   (List every variable touched by both ISR and non-ISR code)

7. HOW do I protect shared data?
   (Volatile? Atomic? Critical section? Lock-free structure?)

8. HOW do I acknowledge?
   (EOI to PIC? Clear status bits in hardware? NVIC handles it?)

9. WHAT can go wrong?
   (Overflow? Error conditions? Re-entrancy? Stack overflow?)

10. HOW do I test this?
    (Stress test? Logic analyzer? Fault injection?)
```

---

## CHAPTER 26 — SUMMARY REFERENCE CARD

```
╔══════════════════════════════════════════════════════════════════╗
║              ISR COMPLETE REFERENCE CARD                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  INTERRUPT TYPES:                                                ║
║    Hardware (maskable)  → IRQ0-255, controlled by PIC/APIC      ║
║    Hardware (NMI)       → Cannot be masked, hardware errors      ║
║    Exceptions/Faults    → CPU-generated (divide-0, page fault)   ║
║    Software (trap)      → INT n, SYSCALL, SVC — OS interface     ║
║                                                                  ║
║  ISR DO'S:                          ISR DON'TS:                 ║
║    ✓ Read hardware registers          ✗ sleep() / delay()       ║
║    ✓ Write atomic flags               ✗ malloc() / free()       ║
║    ✓ Use ring buffers (SPSC)          ✗ mutex_lock()            ║
║    ✓ Send EOI                         ✗ printf()                ║
║    ✓ Schedule bottom-half             ✗ block on I/O            ║
║    ✓ Declare shared vars volatile     ✗ call non-reentrant funcs ║
║    ✓ Use memory barriers              ✗ use large stack          ║
║    ✓ Return IRET/BX LR               ✗ take > N microseconds    ║
║                                                                  ║
║  CRITICAL SECTION PATTERN:                                       ║
║    flags = save_and_disable_interrupts();                        ║
║    [access shared data]                                          ║
║    restore_interrupts(flags);  ← RESTORE, not just enable!      ║
║                                                                  ║
║  DEFERRED WORK (choose one):                                     ║
║    Embedded: Queue + Task (FreeRTOS)                             ║
║    Linux:    Tasklet (no sleep) | Workqueue (can sleep)          ║
║    Rust:     RTIC software tasks                                 ║
║    Go:       Channels + goroutines                               ║
║                                                                  ║
║  SHARED DATA PROTECTION:                                         ║
║    Single word read/write → volatile (weak guarantee)            ║
║    Counter/flag r-m-w     → atomic_t / AtomicU32 / atomic.Int64  ║
║    Multiple variables     → critical section / spinlock          ║
║    Large data             → lock-free ring buffer (SPSC)         ║
║                                                                  ║
║  PLATFORM NOTES:                                                 ║
║    x86:        CLI/STI for interrupt disable/enable              ║
║                IRETQ to return from ISR                          ║
║                EOI to PIC (outb 0x20, 0x20)                     ║
║    ARM Cortex: PRIMASK / BASEPRI for disable/priority mask       ║
║                BX LR (EXC_RETURN) to return from ISR            ║
║                NVIC handles EOI automatically                    ║
║                DMB/DSB/ISB for memory barriers                   ║
║    Linux:      request_irq() / free_irq()                        ║
║                irqreturn_t: IRQ_HANDLED / IRQ_NONE               ║
║                IRQF_SHARED for shared IRQ lines                  ║
║    Rust RTIC:  #[interrupt] / #[exception] / #[task]             ║
║    Go:         signal.Notify() → channel → goroutine             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## APPENDIX: ASCII FLOWCHART — COMPLETE ISR DECISION FLOW

```
                    ┌─────────────────────────┐
                    │   HARDWARE EVENT OCCURS  │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  Device asserts IRQ line │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ PIC/APIC receives IRQ   │
                    │ Checks priority         │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ PIC signals CPU (INT pin)│
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ CPU finishes CURRENT     │
                    │ instruction              │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │    IF flag enabled?      │
                    └──────┬──────────┬────────┘
                          YES         NO
                           │           │
                           │           ▼
                           │   ┌──────────────────┐
                           │   │ CPU ignores IRQ  │
                           │   │ (NMI always runs)│
                           │   └──────────────────┘
                           │
                           ▼
                    ┌─────────────────────────┐
                    │ CPU sends INTA to PIC   │
                    │ PIC sends vector number │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ CPU PUSHES to STACK:    │
                    │  RFLAGS / xPSR          │
                    │  CS                     │
                    │  RIP / PC               │
                    │  [error code if any]    │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ CPU clears IF flag      │
                    │ (disables hw interrupts)│
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ CPU indexes IDT[vector] │
                    │ Loads ISR address       │
                    │ Jumps to ISR            │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │      ISR EXECUTES        │
                    │                         │
                    │  1. Save extra regs      │
                    │  2. Clear hw interrupt   │
                    │  3. Read data from hw    │
                    │  4. Store in safe buffer │
                    │  5. Schedule bottom-half │
                    │  6. Send EOI to PIC      │
                    │  7. Restore regs         │
                    │  8. IRET / BX LR        │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ CPU POPS from STACK:    │
                    │  RIP / PC (return addr) │
                    │  CS                     │
                    │  RFLAGS (IF restored!)  │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  INTERRUPTED CODE       │
                    │  RESUMES TRANSPARENTLY  │
                    └─────────────────────────┘
                                │
                         (Meanwhile...)
                                │
                    ┌───────────▼─────────────┐
                    │    BOTTOM-HALF RUNS      │
                    │  (when scheduler allows) │
                    │                         │
                    │  Can sleep, alloc, lock  │
                    │  Full OS capabilities    │
                    │  Heavy processing        │
                    └─────────────────────────┘
```

---

*"The expert programmer understands not just how to write the ISR,
but why the CPU was designed this way, what invariants must be
preserved, and how every nanosecond of latency connects to
real-world system behavior. Mastery is the marriage of theory
and implementation, pursued with the patience of a craftsman."*

---

**END OF GUIDE**

> Revision: 2026-03 | Author: Complete Systems Reference
> Covers: x86-64, ARM Cortex-M, Linux Kernel, Bare Metal, Rust Embedded, Go Signal Handling

Now let me craft the complete, comprehensive guide on Interrupt Service Routines.Your complete ISR guide is ready — here's a structural overview of what's inside:

---

## What This Guide Covers (26 Chapters)

**Foundations (Ch 1–6):** Builds from first principles — why CPUs need interrupts at all, the polling vs interrupt vs DMA tradeoff, the physical hardware path (IRQ → PIC/APIC → CPU), the Interrupt Vector Table (IVT) for x86 real mode, the IDT for x86-64 protected mode, and the ARM Cortex-M vector table — all with ASCII diagrams.

**Type System (Ch 7–10):** Full taxonomy with decision trees — maskable IRQs, NMI, exceptions (fault/trap/abort distinction), the complete x86 exception table (all 32 reserved vectors), the page fault lifecycle (how virtual memory actually works), and software interrupts / system calls.

**Mechanics (Ch 11–15):** Complete interrupt lifecycle flowchart, ARM Cortex-M hardware stacking (exactly which 8 registers are auto-saved), context save/restore, the calling convention difference between ISRs and normal functions, priority and nesting with stack growth diagrams, latency analysis, and the race condition / critical section problem with correct x86 and ARM patterns.

**Design Rules (Ch 16–18):** The Ten Commandments of ISR design, volatile and memory barriers (with compiler barrier syntax for C, Rust, and ARM/x86 hardware), and the top-half/bottom-half model — Linux softirq/tasklet/workqueue compared, and the FreeRTOS queue pattern for embedded.

**Implementations (Ch 19–21):**
- **C:** Bare-metal x86-64 IDT + ISR from scratch, Linux kernel driver with `request_irq` + workqueue, STM32 UART ISR with double-buffered ring buffer
- **Rust:** `no_std` Cortex-M ISR using `cortex-m-rt`, the RTIC framework (compile-time race elimination), and POSIX signal handling with `signal-hook` + raw `libc::sigaction`
- **Go:** Full signal handler with top-half/bottom-half goroutine architecture, graceful shutdown with context cancellation, and a hardware interrupt simulation using channels

**Mastery (Ch 22–25):** Real-world examples (Watchdog, DMA double-buffering, NAPI networking), a debugging decision tree, advanced topics (interrupt coalescing, CPU affinity, MMIO ordering, jitter analysis), and cognitive tools — mental models, the Atomic Thinking Checklist, and a 8-week deliberate practice protocol.