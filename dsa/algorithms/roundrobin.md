# Round Robin — Complete, In-Depth Guide
### From Fundamentals to Production-Grade Mastery

---

## Table of Contents

1. [What Is Round Robin?](#1-what-is-round-robin)
2. [Core Vocabulary — Every Term Defined](#2-core-vocabulary--every-term-defined)
3. [Mental Model — How to Think About Round Robin](#3-mental-model--how-to-think-about-round-robin)
4. [Architecture of a Round Robin Scheduler](#4-architecture-of-a-round-robin-scheduler)
5. [Step-by-Step Mechanics](#5-step-by-step-mechanics)
6. [Gantt Chart & Timeline Walkthrough](#6-gantt-chart--timeline-walkthrough)
7. [Time Quantum — The Critical Parameter](#7-time-quantum--the-critical-parameter)
8. [Performance Analysis — The Deep Math](#8-performance-analysis--the-deep-math)
9. [Hardware Reality — Cache, Memory, Kernel](#9-hardware-reality--cache-memory-kernel)
10. [C Implementation — Production Grade](#10-c-implementation--production-grade)
11. [Rust Implementation — Production Grade](#11-rust-implementation--production-grade)
12. [Weighted Round Robin (WRR)](#12-weighted-round-robin-wrr)
13. [Deficit Round Robin (DRR)](#13-deficit-round-robin-drr)
14. [Round Robin in Load Balancing & Networking](#14-round-robin-in-load-balancing--networking)
15. [Round Robin vs Other Scheduling Algorithms](#15-round-robin-vs-other-scheduling-algorithms)
16. [Edge Cases & Pathological Inputs](#16-edge-cases--pathological-inputs)
17. [Real Operating System Usage](#17-real-operating-system-usage)
18. [Mental Models for Mastery](#18-mental-models-for-mastery)

---

## 1. What Is Round Robin?

**Round Robin (RR)** is a scheduling algorithm where every entity in a list is served one at a time, in cyclic order, each receiving a fixed maximum slice of resource (called a **time quantum** or **time slice**), before the scheduler moves to the next.

It is the purest form of **fair, preemptive, time-sharing**.

### The Core Idea in One Sentence

> "Every process gets equal turns. No one waits forever. No one monopolizes."

### Where Round Robin Appears

| Domain | What Gets Scheduled | Resource Being Shared |
|---|---|---|
| Operating Systems | Processes / Threads | CPU time |
| Networking | Packets / Flows | Bandwidth |
| Load Balancing | HTTP Requests | Server capacity |
| Database Connection Pools | Queries | Connections |
| Game Engines | Entity update loops | Frame time |
| Compiler Task Queues | Compilation units | Worker threads |

---

## 2. Core Vocabulary — Every Term Defined

Before anything else, you must deeply understand every term used. This vocabulary is the **foundation of your mental model**.

### Process / Task
A unit of work that needs CPU time. A process has:
- A unique **PID** (Process ID)
- A **burst time** — total CPU time it needs to complete
- An **arrival time** — when it enters the ready queue
- A **remaining time** — how much CPU time it still needs

### Ready Queue
A **circular queue** (ring buffer) of processes that are ready to execute but waiting their turn. Processes enter the queue when they arrive. When a process uses its full quantum and is not finished, it re-enters at the **back** of the queue.

```
Ready Queue (circular):
HEAD --> [P3] --> [P1] --> [P4] --> [P2] --> (back to HEAD)
```

### Time Quantum (Time Slice, Q)
A fixed maximum duration (in milliseconds or CPU ticks) that a process is allowed to run before being **preempted** (forcibly stopped). This is the most important parameter in Round Robin.

- If a process finishes before Q expires → it leaves voluntarily (no preemption)
- If a process is still running when Q expires → it is preempted and re-queued

### Preemption
Forcibly stopping a running process before it completes, so another process can run. Round Robin is **always preemptive** (when Q < burst time).

### Context Switch
The act of saving the full state of the current process (registers, program counter, stack pointer, memory maps) and loading the state of the next process. This is expensive — typically 1–10 microseconds on real hardware.

### Turnaround Time (TAT)
The total time from when a process **arrives** to when it **finishes**:
```
TAT = Completion Time − Arrival Time
```

### Waiting Time (WT)
Total time a process spends in the **ready queue** (not executing):
```
WT = TAT − Burst Time
      = (Completion Time − Arrival Time) − Burst Time
```

### Response Time (RT)
Time from when a process arrives to when it **first gets the CPU** (first response):
```
RT = Time of First Execution − Arrival Time
```

### Throughput
Number of processes completed per unit time:
```
Throughput = Number of Completed Processes / Total Time
```

### CPU Utilization
Percentage of time the CPU is doing useful work (not idle):
```
CPU Utilization = (Total Burst Time of All Processes / Total Span) × 100%
```

### Starvation
When a process waits indefinitely because other processes keep getting scheduled first. **Round Robin completely prevents starvation** — every process eventually gets a turn.

### Overhead
Wasted time due to context switching. If Q is too small, overhead dominates.

### Aging
A technique where a process's priority increases the longer it waits (not native to pure RR, but used in enhanced variants).

---

## 3. Mental Model — How to Think About Round Robin

### The Token Passing Analogy

Imagine a circular table with N people. There is one **talking token**. Only the person holding the token can speak. Each person gets to hold the token for exactly Q seconds, then must pass it clockwise. If they finish talking before Q seconds, they pass it immediately. Nobody can hold the token twice in a row without everyone else getting a turn first.

This is **exactly** Round Robin.

### The Carousel Mental Image

```
         ┌─────────────────────────────────────────┐
         │           READY QUEUE (Carousel)         │
         │                                          │
         │    ┌────┐    ┌────┐    ┌────┐    ┌────┐ │
         │    │ P1 │ -> │ P2 │ -> │ P3 │ -> │ P4 │ │
         │    └────┘    └────┘    └────┘    └────┘ │
         │       ^                              |   │
         │       └──────────────────────────────┘   │
         │           (circular, wraps around)        │
         └─────────────────────────────────────────┘
                              |
                              v  (front of queue)
                         ┌─────────┐
                         │   CPU   │  <-- runs for Q ms
                         └─────────┘
```

The carousel spins at fixed intervals (Q). Each seat gets exactly one turn per revolution.

### The Key Insight About Fairness

Round Robin achieves **max-min fairness**: it maximizes the minimum allocation any process receives. This is mathematically optimal for fairness when all processes are equal in priority.

---

## 4. Architecture of a Round Robin Scheduler

### High-Level System Architecture

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │                        OPERATING SYSTEM KERNEL                        │
  │                                                                        │
  │  ┌─────────────┐     ┌────────────────────────────────────────────┐  │
  │  │   NEW       │     │              READY QUEUE (Circular)         │  │
  │  │  PROCESSES  │────>│  [P5|10ms] -> [P2|4ms] -> [P1|8ms] -> ...  │  │
  │  │  (arriving) │     │                    ^                         │  │
  │  └─────────────┘     └─────────────────┬──┴─────────────────────── ┘  │
  │                                         │         ^                     │
  │                                         │  (dequeue front)             │
  │                                         v         |                     │
  │                                   ┌──────────┐    | (re-enqueue if     │
  │                                   │  DISPATCH │    |  not finished)     │
  │                                   │  (Sched.) │    |                    │
  │                                   └─────┬─────┘    |                    │
  │                                         |           |                    │
  │                          ┌──────────────v───────────┴──┐                │
  │                          │           CPU CORE           │                │
  │                          │  ┌────────────────────────┐ │                │
  │                          │  │  Timer Interrupt (HW)  │ │                │
  │                          │  │  fires every Q ms      │ │                │
  │                          │  └────────────────────────┘ │                │
  │                          │  ┌────────────────────────┐ │                │
  │                          │  │  Context Switch Logic  │ │                │
  │                          │  │  save/restore PCB      │ │                │
  │                          │  └────────────────────────┘ │                │
  │                          └─────────────────────────────┘                │
  │                                         |                                │
  │                             ┌───────────v──────────┐                    │
  │                             │     TERMINATED        │                    │
  │                             │  (process finished)   │                    │
  │                             └──────────────────────┘                    │
  └──────────────────────────────────────────────────────────────────────┘
```

### Process Control Block (PCB) — The Data Behind Each Process

Each process is represented by a PCB (Process Control Block):

```
  ┌──────────────────────────────────────┐
  │         PROCESS CONTROL BLOCK (PCB)  │
  ├──────────────────────────────────────┤
  │  pid           : u32                 │  <-- unique identifier
  │  arrival_time  : u64 (ms)            │  <-- when it joined queue
  │  burst_time    : u64 (ms)            │  <-- total CPU needed
  │  remaining_time: u64 (ms)            │  <-- how much left
  │  start_time    : Option<u64>         │  <-- first CPU time (for RT)
  │  finish_time   : u64                 │  <-- when it completed
  │  state         : ProcessState        │  <-- New|Ready|Running|Done
  └──────────────────────────────────────┘
```

### Scheduler State Machine — Per Process

```
         arrive
  [NEW] ─────────> [READY] <──────────────────────────────────┐
                      │                                         │
              (dequeued, dispatched)                            │
                      │                                         │
                      v                                         │
                 [RUNNING]                                      │
                 /        \                                     │
          (burst done)  (Q expires, remaining > 0)             │
               /                  \                            │
              v                    └──────────────────────────>┘
         [TERMINATED]                    (preempted, re-queued)
```

---

## 5. Step-by-Step Mechanics

### The Algorithm — Pseudocode (Language-Agnostic)

```
Algorithm ROUND_ROBIN(processes[], quantum Q):

  ready_queue  ← empty circular queue
  current_time ← 0
  sort processes by arrival_time (ascending)

  LOOP forever:
    // Enqueue all processes that have arrived by current_time
    FOR each process p where p.arrival_time <= current_time AND p not yet queued:
      enqueue(ready_queue, p)

    IF ready_queue is empty:
      IF all processes terminated → BREAK
      ELSE:
        current_time ← next_arrival_time()   // CPU idle jump
        CONTINUE

    p ← dequeue(ready_queue)                  // take front process

    IF p.start_time is NOT SET:
      p.start_time ← current_time             // record first execution

    run_duration ← min(p.remaining_time, Q)   // how long to actually run

    current_time      += run_duration          // advance clock
    p.remaining_time  -= run_duration          // subtract from burst

    // Enqueue NEW arrivals during this run window (important!)
    FOR each process q where q.arrival_time IN (current_time - run_duration, current_time]:
      enqueue(ready_queue, q)

    IF p.remaining_time == 0:
      p.finish_time ← current_time
      MARK p as TERMINATED
    ELSE:
      enqueue(ready_queue, p)                  // p goes to back of queue

  COMPUTE metrics for each process
  RETURN results
```

### Critical Detail: Arrival During Execution

When a new process P_new arrives **while** another process P_cur is running on the CPU, P_new must be enqueued **before** P_cur is re-enqueued (if P_cur gets preempted). This preserves FIFO order among processes that arrive during the same quantum.

```
  Time 0-4:    P1 runs
    At t=2:    P2 arrives → enqueued (queue: [P2])
    At t=4:    P1 preempted → queue becomes [P2, P1]
  Time 4-8:    P2 runs  ← P2 goes first because it arrived DURING P1's run
  Time 8-12:   P1 runs  ← P1 continues
```

---

## 6. Gantt Chart & Timeline Walkthrough

### Example Setup

| Process | Arrival Time | Burst Time |
|---------|-------------|-----------|
| P1      | 0           | 10        |
| P2      | 1           | 4         |
| P3      | 2           | 6         |
| P4      | 3           | 3         |

**Quantum Q = 4**

### Simulation Trace

```
Step-by-step execution (Q=4):

t=0:  P1 arrives → queue: [P1]
      Dequeue P1. run_duration = min(10,4) = 4

t=4:  P1 remaining=6. Arrivals at t=1,2,3 → P2,P3,P4 arrive during [0,4]
      Enqueue P2, P3, P4 (arrived while P1 ran)
      P1 re-enqueued → queue: [P2, P3, P4, P1]
      Dequeue P2. run_duration = min(4,4) = 4

t=8:  P2 remaining=0 → P2 FINISHES. queue: [P3, P4, P1]
      Dequeue P3. run_duration = min(6,4) = 4

t=12: P3 remaining=2. P3 re-enqueued. queue: [P4, P1, P3]
      Dequeue P4. run_duration = min(3,4) = 3

t=15: P4 remaining=0 → P4 FINISHES. queue: [P1, P3]
      Dequeue P1. run_duration = min(6,4) = 4

t=19: P1 remaining=2. P1 re-enqueued. queue: [P3, P1]
      Dequeue P3. run_duration = min(2,4) = 2

t=21: P3 remaining=0 → P3 FINISHES. queue: [P1]
      Dequeue P1. run_duration = min(2,4) = 2

t=23: P1 remaining=0 → P1 FINISHES.
```

### Gantt Chart

```
  Time: 0    4    8    12   15   19   21   23
        |    |    |    |    |    |    |    |
  CPU:  [P1  ][P2  ][P3  ][P4][P1  ][P3][P1]
        0    4    8   12  15  19  21  23
```

### Metrics Computation

```
Process | Arrival | Burst | Finish | TAT=F-A | WT=TAT-B | RT=First-A
--------|---------|-------|--------|---------|----------|-----------
P1      |  0      |  10   |  23    |  23     |  13      |   0
P2      |  1      |   4   |   8    |   7     |   3      |   3
P3      |  2      |   6   |  21    |  19     |  13      |   6
P4      |  3      |   3   |  15    |  12     |   9      |   9

Average TAT = (23 + 7 + 19 + 12) / 4 = 61 / 4 = 15.25
Average WT  = (13 + 3 + 13 + 9)  / 4 = 38 / 4 = 9.5
Average RT  = (0  + 3 + 6  + 9)  / 4 = 18 / 4 = 4.5
```

---

## 7. Time Quantum — The Critical Parameter

The time quantum Q is the **single most important decision** in Round Robin. It fundamentally determines the character of the scheduler.

### The Two Extremes

```
  Q → 0 (infinitely small)
  ┌──────────────────────────────────────────────────────┐
  │  • Each process gets a tiny sliver every turn        │
  │  • All processes appear to run simultaneously        │
  │  • Response time → 0 (theoretically perfect)         │
  │  • Context switch overhead → INFINITE (impractical)  │
  │  • This is the theoretical ideal: Processor Sharing  │
  └──────────────────────────────────────────────────────┘

  Q → ∞ (infinitely large)
  ┌──────────────────────────────────────────────────────┐
  │  • Each process runs to completion before next       │
  │  • Degenerates into FCFS (First Come First Served)   │
  │  • No preemption. No fairness for late arrivals      │
  │  • Long processes can monopolize CPU                 │
  └──────────────────────────────────────────────────────┘
```

### The Sweet Spot

```
  Response Time                    Context Switch Overhead
       │                                  │
       │    \                             │                /
       │     \                            │               /
       │      \                           │              /
       │       \                          │             /
       │        \________________________ │ ___________/
       └─────────────────────> Q          └──────────────────> Q
             Q too small = bad                Q too large = bad

  Total Cost = Response_Time(Q) + Overhead(Q)

       │            ___
       │           /   \
       │          /     \  SWEET SPOT
       │   ______/       \____________
       └─────────────────────────────> Q
             ^ optimal Q here
```

### Rule of Thumb

**80% rule**: Q should be large enough that **80% of processes** finish within one quantum. This minimizes preemptions while keeping response time acceptable.

In practice:
- Linux default: ~100ms (configurable)
- Interactive systems: 10–50ms
- Real-time systems: 1–10ms
- Batch systems: 100–500ms

### Effect on Average Waiting Time

Smaller Q generally **increases** average waiting time because:
1. More context switches (overhead adds to total time)
2. More trips around the queue before finishing

**BUT** smaller Q **decreases** response time (first execution happens sooner for new processes).

This is the fundamental **fairness vs. efficiency tradeoff**.

---

## 8. Performance Analysis — The Deep Math

### Time Complexity of Scheduling

```
Let:
  N = number of processes
  B_i = burst time of process i
  Q = quantum
  T = sum of all burst times = Σ B_i

Number of context switches (worst case):
  CS = Σ ceil(B_i / Q)
     ≈ T/Q   (when all B_i >> Q)

Overhead time:
  T_overhead = CS × t_switch
             = (T/Q) × t_switch
```

Scheduling loop per step: **O(1)** — dequeue front, run, possibly enqueue back. The scheduler itself is O(1) per scheduling decision.

Full simulation for N processes: **O(N × max_burst / Q)** — proportional to total number of quanta.

### Space Complexity

The ready queue holds at most **N** elements: **O(N)**.

### Average Turnaround Time (Mathematical Derivation)

For N processes all arriving at t=0 with burst times B_1, B_2, ..., B_N (sorted in arrival order):

Assume all bursts are multiples of Q for simplicity.

After round r (r × Q time units), process i has received min(r×Q, B_i) time.
Process i finishes at round: r_i = ceil(B_i / Q)

At that round, time elapsed ≈ N × r_i × Q (approximately, ignoring early finishers).

Exact analysis is complex due to variable finish times. The general result:

```
Average TAT ≈ (N+1)/2 × B_avg   when Q is very small (approaches processor sharing)
Average TAT ≈ TAT_FCFS           when Q is very large
```

### Worst Case Waiting Time

For N processes with burst B_i each:
```
WT_worst = (N - 1) × Q
```
This occurs when a process arrives just after its predecessor starts running, and must wait for N-1 other processes to get their turn.

---

## 9. Hardware Reality — Cache, Memory, Kernel

### Context Switch Cost on Real Hardware

A context switch requires:
1. **Save registers** (~16–32 general-purpose + FP/SIMD) → ~100–300 cycles
2. **Switch page tables** → TLB flush (most expensive part!)
3. **Reload registers** for new process
4. **L1/L2 cache pollution**: new process has different working set → **cache cold start**

```
  ┌──────────────────────────────────────────────────────┐
  │              Cache Behavior During Context Switch     │
  │                                                       │
  │  Before switch:  P1 has warm cache (fast execution)  │
  │  ──────────────────────────────────────────────────  │
  │  Switch occurs:  P1's cache lines still in L1/L2     │
  │                  P2 starts, its lines not in cache   │
  │                  → P2 suffers CACHE MISSES           │
  │                  → penalty: 10-200 cycles per miss   │
  │  ──────────────────────────────────────────────────  │
  │  Working set size matters:                           │
  │  • If P2's working set fits in L2 → short warm-up   │
  │  • If P2's working set > L3 → DRAM reads each time  │
  │    (could be 50-100ns × many accesses = ms wasted)  │
  └──────────────────────────────────────────────────────┘
```

### TLB Shootdown (Multi-Core Systems)

On multi-core systems, when a process is migrated to a different core:
- The **TLB** (Translation Lookaside Buffer) on the new core has no entries for the process
- Every memory access triggers a **page walk** until TLB warms up
- This can add **thousands of cycles** of overhead

### Why Small Q Is Dangerous on Real Hardware

```
  Suppose: t_switch = 1ms, Q = 2ms, N = 10 processes

  Useful work per cycle: 2ms
  Overhead per cycle:    1ms
  Efficiency: 2/(2+1) = 66.7%  ← only 2/3 of time is useful!

  With Q = 20ms:
  Efficiency: 20/(20+1) = 95.2%  ← much better
```

### Linux Scheduler Reality

Modern Linux uses **CFS (Completely Fair Scheduler)**, which is a sophisticated evolution of Round Robin using a **red-black tree** ordered by virtual runtime. However, the core fairness principle is identical to Round Robin.

The `sched_latency_ns` parameter (default ~6ms) is Linux's "one full rotation time" — analogous to N×Q in classic RR.

---

## 10. C Implementation — Production Grade

```c
/*
 * round_robin.c
 *
 * Production-grade Round Robin Scheduler Simulator
 *
 * Demonstrates:
 *   - Circular queue with proper capacity management
 *   - Full metrics: TAT, WT, RT, throughput, CPU utilization
 *   - Gantt chart generation
 *   - Correct handling of arrivals during execution
 *   - Edge cases: single process, zero remaining, idle CPU
 *
 * Compile: gcc -std=c11 -Wall -Wextra -O2 -o rr round_robin.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>

/* ─────────────────────── Constants ─────────────────────── */

#define MAX_PROCESSES       64
#define MAX_GANTT_ENTRIES   512
#define PROCESS_NAME_LEN    8

/* Sentinel: process not yet started */
#define UNSET_TIME UINT64_MAX

/* ─────────────────────── Data Types ───────────────────── */

typedef enum {
    STATE_NEW       = 0,
    STATE_READY     = 1,
    STATE_RUNNING   = 2,
    STATE_TERMINATED = 3
} ProcessState;

typedef struct {
    char     name[PROCESS_NAME_LEN]; /* human-readable label e.g. "P1" */
    uint32_t pid;                    /* unique process id                */
    uint64_t arrival_time;           /* when it enters the ready queue   */
    uint64_t burst_time;             /* total CPU time required          */
    uint64_t remaining_time;         /* how much CPU time remains        */
    uint64_t start_time;             /* time of FIRST execution (for RT) */
    uint64_t finish_time;            /* time when process completes      */
    ProcessState state;
} Process;

/* Metrics computed after simulation */
typedef struct {
    uint64_t turnaround_time; /* finish - arrival                 */
    uint64_t waiting_time;    /* TAT - burst                      */
    uint64_t response_time;   /* first_exec - arrival             */
} ProcessMetrics;

/* One entry in the Gantt chart */
typedef struct {
    char     name[PROCESS_NAME_LEN];
    uint64_t start;
    uint64_t end;
    bool     is_idle; /* true when CPU was idle */
} GanttEntry;

/* Circular queue of process indices */
typedef struct {
    uint32_t *data;
    uint32_t  head;
    uint32_t  tail;
    uint32_t  size;
    uint32_t  capacity;
} CircularQueue;

/* Full scheduler result */
typedef struct {
    ProcessMetrics metrics[MAX_PROCESSES];
    GanttEntry     gantt[MAX_GANTT_ENTRIES];
    uint32_t       gantt_count;
    double         avg_turnaround;
    double         avg_waiting;
    double         avg_response;
    double         cpu_utilization;  /* 0.0 to 1.0 */
    double         throughput;       /* processes per unit time */
    uint64_t       total_time;
} SchedulerResult;

/* ─────────────────── Circular Queue Operations ──────────── */

static CircularQueue *queue_create(uint32_t capacity) {
    CircularQueue *q = malloc(sizeof(CircularQueue));
    if (!q) return NULL;
    q->data = malloc(capacity * sizeof(uint32_t));
    if (!q->data) { free(q); return NULL; }
    q->head     = 0;
    q->tail     = 0;
    q->size     = 0;
    q->capacity = capacity;
    return q;
}

static void queue_destroy(CircularQueue *q) {
    if (q) { free(q->data); free(q); }
}

static bool queue_is_empty(const CircularQueue *q) {
    return q->size == 0;
}

static bool queue_enqueue(CircularQueue *q, uint32_t idx) {
    if (q->size == q->capacity) return false; /* queue full */
    q->data[q->tail] = idx;
    q->tail = (q->tail + 1) % q->capacity;
    q->size++;
    return true;
}

static bool queue_dequeue(CircularQueue *q, uint32_t *out_idx) {
    if (queue_is_empty(q)) return false;
    *out_idx = q->data[q->head];
    q->head  = (q->head + 1) % q->capacity;
    q->size--;
    return true;
}

/* ─────────────────── Comparator for qsort ───────────────── */

static int compare_by_arrival(const void *a, const void *b) {
    const Process *pa = (const Process *)a;
    const Process *pb = (const Process *)b;
    if (pa->arrival_time < pb->arrival_time) return -1;
    if (pa->arrival_time > pb->arrival_time) return  1;
    return 0;
}

/* ─────────────────── Core Scheduler ────────────────────── */

/*
 * run_round_robin()
 *
 * Parameters:
 *   processes  - array of Process structs (will be MODIFIED in place)
 *   n          - number of processes
 *   quantum    - time quantum (must be > 0)
 *   result     - output: filled with metrics and Gantt chart
 *
 * Returns: 0 on success, -1 on error
 */
int run_round_robin(
    Process       *processes,
    uint32_t       n,
    uint64_t       quantum,
    SchedulerResult *result
) {
    if (!processes || n == 0 || quantum == 0 || !result) return -1;
    if (n > MAX_PROCESSES) return -1;

    /* Sort by arrival time */
    qsort(processes, n, sizeof(Process), compare_by_arrival);

    /* Initialize */
    for (uint32_t i = 0; i < n; i++) {
        processes[i].remaining_time = processes[i].burst_time;
        processes[i].start_time     = UNSET_TIME;
        processes[i].finish_time    = 0;
        processes[i].state          = STATE_NEW;
    }

    CircularQueue *rq = queue_create(n + 1); /* +1 for safety */
    if (!rq) return -1;

    memset(result, 0, sizeof(SchedulerResult));

    uint64_t  current_time     = 0;
    uint32_t  next_arrival_idx = 0; /* index into sorted processes[] */
    uint32_t  finished_count   = 0;
    bool     *in_queue         = calloc(n, sizeof(bool));

    if (!in_queue) { queue_destroy(rq); return -1; }

    /* Enqueue all processes arriving at time 0 */
    while (next_arrival_idx < n &&
           processes[next_arrival_idx].arrival_time <= current_time) {
        queue_enqueue(rq, next_arrival_idx);
        in_queue[next_arrival_idx]       = true;
        processes[next_arrival_idx].state = STATE_READY;
        next_arrival_idx++;
    }

    uint64_t total_busy_time = 0;

    while (finished_count < n) {

        /* ── CPU Idle: no process ready, jump time forward ── */
        if (queue_is_empty(rq)) {
            if (next_arrival_idx >= n) break; /* nothing left */

            uint64_t idle_start = current_time;
            current_time = processes[next_arrival_idx].arrival_time;

            /* Record idle period in Gantt */
            if (result->gantt_count < MAX_GANTT_ENTRIES) {
                GanttEntry *ge = &result->gantt[result->gantt_count++];
                snprintf(ge->name, PROCESS_NAME_LEN, "IDLE");
                ge->start   = idle_start;
                ge->end     = current_time;
                ge->is_idle = true;
            }

            /* Enqueue arrivals at new time */
            while (next_arrival_idx < n &&
                   processes[next_arrival_idx].arrival_time <= current_time) {
                queue_enqueue(rq, next_arrival_idx);
                in_queue[next_arrival_idx]       = true;
                processes[next_arrival_idx].state = STATE_READY;
                next_arrival_idx++;
            }
            continue;
        }

        /* ── Dequeue next process ── */
        uint32_t idx;
        queue_dequeue(rq, &idx);
        in_queue[idx]         = false;
        Process *p            = &processes[idx];
        p->state              = STATE_RUNNING;

        /* Record first execution time (for response time) */
        if (p->start_time == UNSET_TIME) {
            p->start_time = current_time;
        }

        /* How long does it run this turn? */
        uint64_t run_duration = (p->remaining_time < quantum)
                                ? p->remaining_time
                                : quantum;

        uint64_t run_start = current_time;
        current_time      += run_duration;
        p->remaining_time -= run_duration;
        total_busy_time   += run_duration;

        /* ── Record Gantt entry ── */
        if (result->gantt_count < MAX_GANTT_ENTRIES) {
            GanttEntry *ge = &result->gantt[result->gantt_count++];
            snprintf(ge->name, PROCESS_NAME_LEN, "%s", p->name);
            ge->start   = run_start;
            ge->end     = current_time;
            ge->is_idle = false;
        }

        /* Enqueue newly arrived processes BEFORE re-enqueuing current */
        while (next_arrival_idx < n &&
               processes[next_arrival_idx].arrival_time <= current_time) {
            queue_enqueue(rq, next_arrival_idx);
            in_queue[next_arrival_idx]       = true;
            processes[next_arrival_idx].state = STATE_READY;
            next_arrival_idx++;
        }

        /* ── Finished or preempted? ── */
        if (p->remaining_time == 0) {
            p->state       = STATE_TERMINATED;
            p->finish_time = current_time;
            finished_count++;
        } else {
            /* Re-enqueue at back — the core of Round Robin */
            p->state = STATE_READY;
            queue_enqueue(rq, idx);
            in_queue[idx] = true;
        }
    }

    result->total_time = current_time;

    /* ── Compute Per-Process Metrics ── */
    uint64_t sum_tat = 0, sum_wt = 0, sum_rt = 0;

    for (uint32_t i = 0; i < n; i++) {
        Process        *p  = &processes[i];
        ProcessMetrics *m  = &result->metrics[i];

        m->turnaround_time = p->finish_time - p->arrival_time;
        m->waiting_time    = m->turnaround_time - p->burst_time;
        m->response_time   = (p->start_time != UNSET_TIME)
                             ? (p->start_time - p->arrival_time)
                             : 0;
        sum_tat += m->turnaround_time;
        sum_wt  += m->waiting_time;
        sum_rt  += m->response_time;
    }

    result->avg_turnaround  = (double)sum_tat / n;
    result->avg_waiting     = (double)sum_wt  / n;
    result->avg_response    = (double)sum_rt  / n;
    result->cpu_utilization = (result->total_time > 0)
                              ? (double)total_busy_time / result->total_time
                              : 0.0;
    result->throughput      = (result->total_time > 0)
                              ? (double)n / result->total_time
                              : 0.0;

    free(in_queue);
    queue_destroy(rq);
    return 0;
}

/* ─────────────────── Output / Reporting ───────────────── */

static void print_gantt_chart(const SchedulerResult *result) {
    printf("\n═══════════════════════════════════════════════════\n");
    printf("                    GANTT CHART\n");
    printf("═══════════════════════════════════════════════════\n");

    /* Top bar */
    printf("|");
    for (uint32_t i = 0; i < result->gantt_count; i++) {
        const GanttEntry *ge = &result->gantt[i];
        uint64_t width = ge->end - ge->start;
        /* Use width proportionally (scale: 1 unit = 2 chars) */
        uint32_t cells = (uint32_t)(width * 2);
        if (cells < 4) cells = 4;
        int pad = ((int)cells - (int)strlen(ge->name)) / 2;
        for (int j = 0; j < pad; j++) printf(" ");
        printf("%s", ge->name);
        for (int j = 0; j < (int)cells - pad - (int)strlen(ge->name); j++) printf(" ");
        printf("|");
    }
    printf("\n");

    /* Timeline */
    printf("%lu", result->gantt[0].start);
    for (uint32_t i = 0; i < result->gantt_count; i++) {
        const GanttEntry *ge = &result->gantt[i];
        uint64_t width = ge->end - ge->start;
        uint32_t cells = (uint32_t)(width * 2);
        if (cells < 4) cells = 4;
        for (uint32_t j = 1; j < cells; j++) printf(" ");
        printf("%lu", ge->end);
    }
    printf("\n");
}

static void print_results(
    const Process       *processes,
    uint32_t             n,
    uint64_t             quantum,
    const SchedulerResult *result
) {
    printf("\n╔══════════════════════════════════════════════════════╗\n");
    printf("║           ROUND ROBIN SCHEDULER RESULTS              ║\n");
    printf("║                   Quantum = %lu ms                   ║\n", quantum);
    printf("╚══════════════════════════════════════════════════════╝\n");

    printf("\n%-8s %-10s %-10s %-10s %-12s %-10s %-10s\n",
           "Process", "Arrival", "Burst", "Finish", "Turnaround", "Waiting", "Response");
    printf("%-8s %-10s %-10s %-10s %-12s %-10s %-10s\n",
           "-------", "-------", "-----", "------", "----------", "-------", "--------");

    for (uint32_t i = 0; i < n; i++) {
        const Process        *p = &processes[i];
        const ProcessMetrics *m = &result->metrics[i];
        printf("%-8s %-10lu %-10lu %-10lu %-12lu %-10lu %-10lu\n",
               p->name,
               p->arrival_time,
               p->burst_time,
               p->finish_time,
               m->turnaround_time,
               m->waiting_time,
               m->response_time);
    }

    printf("\n── Averages ──────────────────────────────────────────\n");
    printf("  Avg Turnaround Time : %.2f ms\n", result->avg_turnaround);
    printf("  Avg Waiting Time    : %.2f ms\n", result->avg_waiting);
    printf("  Avg Response Time   : %.2f ms\n", result->avg_response);
    printf("  CPU Utilization     : %.1f%%\n",  result->cpu_utilization * 100.0);
    printf("  Throughput          : %.4f proc/ms\n", result->throughput);
    printf("  Total Time          : %lu ms\n",  result->total_time);

    print_gantt_chart(result);
}

/* ─────────────────────── main ─────────────────────────── */

int main(void) {
    Process processes[] = {
        { .name = "P1", .pid = 1, .arrival_time = 0, .burst_time = 10 },
        { .name = "P2", .pid = 2, .arrival_time = 1, .burst_time =  4 },
        { .name = "P3", .pid = 3, .arrival_time = 2, .burst_time =  6 },
        { .name = "P4", .pid = 4, .arrival_time = 3, .burst_time =  3 },
    };

    const uint32_t N       = sizeof(processes) / sizeof(processes[0]);
    const uint64_t QUANTUM = 4;

    SchedulerResult result;

    int rc = run_round_robin(processes, N, QUANTUM, &result);
    if (rc != 0) {
        fprintf(stderr, "Scheduler failed with code %d\n", rc);
        return EXIT_FAILURE;
    }

    print_results(processes, N, QUANTUM, &result);

    /* ── Second run: demonstrate effect of different quantum ── */
    printf("\n\n");
    Process processes2[] = {
        { .name = "P1", .pid = 1, .arrival_time = 0, .burst_time = 10 },
        { .name = "P2", .pid = 2, .arrival_time = 1, .burst_time =  4 },
        { .name = "P3", .pid = 3, .arrival_time = 2, .burst_time =  6 },
        { .name = "P4", .pid = 4, .arrival_time = 3, .burst_time =  3 },
    };

    const uint64_t QUANTUM2 = 2;
    SchedulerResult result2;
    run_round_robin(processes2, N, QUANTUM2, &result2);
    print_results(processes2, N, QUANTUM2, &result2);

    return EXIT_SUCCESS;
}
```

### C Memory Layout Diagram

```
  Stack Frame of run_round_robin():
  ┌─────────────────────────────────────────────┐
  │  processes*  → heap: Process[N]              │
  │  rq*         → heap: CircularQueue           │
  │               → heap: uint32_t[N+1] (data)  │
  │  in_queue*   → heap: bool[N]                 │
  │  local vars  : current_time, idx, ...        │
  │               (all on stack, no alloc)        │
  └─────────────────────────────────────────────┘

  Memory: 3 heap allocations total.
  All freed before return → no leaks.
```

---

## 11. Rust Implementation — Production Grade

```rust
//! round_robin.rs
//!
//! Production-grade Round Robin Scheduler Simulator in Rust.
//!
//! Design choices:
//!   - Uses VecDeque<usize> as the ready queue (O(1) push/pop both ends)
//!   - Explicit error types (no unwrap() except where guaranteed)
//!   - Newtype pattern for type-safe time units
//!   - Iterator-based metrics computation
//!   - No unsafe code
//!
//! Run: cargo run  (or: rustc round_robin.rs && ./round_robin)

use std::collections::VecDeque;
use std::fmt;

// ─────────────────────── Constants ────────────────────────

const MAX_GANTT_ENTRIES: usize = 1024;
const UNSET_TIME: u64          = u64::MAX;

// ─────────────────────── Error Type ───────────────────────

#[derive(Debug)]
pub enum SchedulerError {
    EmptyProcessList,
    ZeroQuantum,
    TooManyProcesses { limit: usize, actual: usize },
    GanttOverflow,
}

impl fmt::Display for SchedulerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyProcessList    => write!(f, "Process list is empty"),
            Self::ZeroQuantum         => write!(f, "Quantum must be > 0"),
            Self::TooManyProcesses { limit, actual } =>
                write!(f, "Too many processes: limit {limit}, got {actual}"),
            Self::GanttOverflow =>
                write!(f, "Gantt chart overflow: too many scheduling events"),
        }
    }
}

// ─────────────────────── Data Types ───────────────────────

/// State of a process in the scheduler lifecycle
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProcessState {
    New,
    Ready,
    Running,
    Terminated,
}

/// Represents a single process/task
#[derive(Debug, Clone)]
pub struct Process {
    pub pid:            u32,
    pub name:           String,
    pub arrival_time:   u64,  // ms
    pub burst_time:     u64,  // ms
    // Internal simulation fields (mutable during scheduling)
    remaining_time:     u64,
    start_time:         u64,  // UNSET_TIME until first run
    pub finish_time:    u64,
    pub state:          ProcessState,
}

impl Process {
    /// Create a new process. Returns error if burst_time is 0.
    pub fn new(pid: u32, name: impl Into<String>, arrival: u64, burst: u64)
        -> Result<Self, &'static str>
    {
        if burst == 0 {
            return Err("burst_time must be > 0");
        }
        Ok(Self {
            pid,
            name: name.into(),
            arrival_time:   arrival,
            burst_time:     burst,
            remaining_time: burst,
            start_time:     UNSET_TIME,
            finish_time:    0,
            state:          ProcessState::New,
        })
    }

    fn reset(&mut self) {
        self.remaining_time = self.burst_time;
        self.start_time     = UNSET_TIME;
        self.finish_time    = 0;
        self.state          = ProcessState::New;
    }
}

/// Computed performance metrics for one process
#[derive(Debug, Clone, Copy)]
pub struct ProcessMetrics {
    pub turnaround_time: u64, // finish - arrival
    pub waiting_time:    u64, // TAT - burst
    pub response_time:   u64, // first_exec - arrival
}

impl ProcessMetrics {
    fn compute(p: &Process) -> Self {
        let turnaround = p.finish_time.saturating_sub(p.arrival_time);
        Self {
            turnaround_time: turnaround,
            waiting_time:    turnaround.saturating_sub(p.burst_time),
            response_time:   if p.start_time == UNSET_TIME {
                                 0
                             } else {
                                 p.start_time.saturating_sub(p.arrival_time)
                             },
        }
    }
}

/// One entry in the Gantt chart
#[derive(Debug, Clone)]
pub struct GanttEntry {
    pub name:    String,
    pub start:   u64,
    pub end:     u64,
    pub is_idle: bool,
}

/// Full result of one scheduler run
#[derive(Debug)]
pub struct SchedulerResult {
    pub process_metrics:   Vec<ProcessMetrics>,
    pub gantt:             Vec<GanttEntry>,
    pub avg_turnaround:    f64,
    pub avg_waiting:       f64,
    pub avg_response:      f64,
    pub cpu_utilization:   f64, // 0.0 – 1.0
    pub throughput:        f64, // processes per time unit
    pub total_time:        u64,
}

// ─────────────────────── Scheduler ────────────────────────

/// Run Round Robin scheduling simulation.
///
/// # Arguments
/// * `processes` - slice of Process structs (cloned internally; originals unchanged)
/// * `quantum`   - time quantum in ms (must be > 0)
///
/// # Returns
/// `Ok(SchedulerResult)` with full metrics and Gantt chart,
/// or `Err(SchedulerError)` on invalid input.
pub fn run_round_robin(
    processes: &[Process],
    quantum:   u64,
) -> Result<SchedulerResult, SchedulerError> {

    // ── Validate inputs ──────────────────────────────────
    if processes.is_empty() {
        return Err(SchedulerError::EmptyProcessList);
    }
    if quantum == 0 {
        return Err(SchedulerError::ZeroQuantum);
    }

    let n = processes.len();

    // ── Clone and reset process state ────────────────────
    let mut procs: Vec<Process> = processes.to_vec();
    for p in &mut procs {
        p.reset();
    }

    // ── Sort by arrival time (stable sort preserves pid order for ties) ──
    procs.sort_by_key(|p| (p.arrival_time, p.pid));

    // ── Simulation state ─────────────────────────────────
    let mut ready_queue:      VecDeque<usize> = VecDeque::with_capacity(n);
    let mut in_queue:         Vec<bool>       = vec![false; n];
    let mut current_time:     u64             = 0;
    let mut next_arrival_idx: usize           = 0;
    let mut finished_count:   usize           = 0;
    let mut gantt:            Vec<GanttEntry> = Vec::with_capacity(n * 4);
    let mut total_busy_time:  u64             = 0;

    // Enqueue all processes that arrive at time 0
    while next_arrival_idx < n
        && procs[next_arrival_idx].arrival_time <= current_time
    {
        ready_queue.push_back(next_arrival_idx);
        in_queue[next_arrival_idx] = true;
        procs[next_arrival_idx].state = ProcessState::Ready;
        next_arrival_idx += 1;
    }

    // ── Main scheduling loop ──────────────────────────────
    while finished_count < n {

        // CPU Idle: jump to next arrival
        if ready_queue.is_empty() {
            if next_arrival_idx >= n { break; }

            let idle_start = current_time;
            current_time   = procs[next_arrival_idx].arrival_time;

            if gantt.len() >= MAX_GANTT_ENTRIES {
                return Err(SchedulerError::GanttOverflow);
            }
            gantt.push(GanttEntry {
                name:    "IDLE".into(),
                start:   idle_start,
                end:     current_time,
                is_idle: true,
            });

            while next_arrival_idx < n
                && procs[next_arrival_idx].arrival_time <= current_time
            {
                ready_queue.push_back(next_arrival_idx);
                in_queue[next_arrival_idx] = true;
                procs[next_arrival_idx].state = ProcessState::Ready;
                next_arrival_idx += 1;
            }
            continue;
        }

        // Dequeue front process
        // SAFETY: we checked is_empty above
        let idx = ready_queue.pop_front().expect("queue non-empty (checked above)");
        in_queue[idx] = false;

        let run_start = current_time;

        // Record first execution time (for response time metric)
        if procs[idx].start_time == UNSET_TIME {
            procs[idx].start_time = current_time;
        }
        procs[idx].state = ProcessState::Running;

        // How long does this process run this quantum?
        let run_duration = procs[idx].remaining_time.min(quantum);

        current_time                  += run_duration;
        procs[idx].remaining_time     -= run_duration;
        total_busy_time               += run_duration;

        // Record Gantt entry
        if gantt.len() >= MAX_GANTT_ENTRIES {
            return Err(SchedulerError::GanttOverflow);
        }
        gantt.push(GanttEntry {
            name:    procs[idx].name.clone(),
            start:   run_start,
            end:     current_time,
            is_idle: false,
        });

        // Enqueue arrivals during this quantum BEFORE re-enqueuing current
        while next_arrival_idx < n
            && procs[next_arrival_idx].arrival_time <= current_time
        {
            ready_queue.push_back(next_arrival_idx);
            in_queue[next_arrival_idx] = true;
            procs[next_arrival_idx].state = ProcessState::Ready;
            next_arrival_idx += 1;
        }

        // Finished or preempted?
        if procs[idx].remaining_time == 0 {
            procs[idx].state       = ProcessState::Terminated;
            procs[idx].finish_time = current_time;
            finished_count        += 1;
        } else {
            // Core of Round Robin: re-enqueue at the BACK
            procs[idx].state = ProcessState::Ready;
            ready_queue.push_back(idx);
            in_queue[idx] = true;
        }
    }

    let total_time = current_time;

    // ── Compute per-process metrics ───────────────────────
    let process_metrics: Vec<ProcessMetrics> = procs.iter()
        .map(ProcessMetrics::compute)
        .collect();

    // ── Compute aggregate statistics ──────────────────────
    let sum_tat: u64 = process_metrics.iter().map(|m| m.turnaround_time).sum();
    let sum_wt:  u64 = process_metrics.iter().map(|m| m.waiting_time).sum();
    let sum_rt:  u64 = process_metrics.iter().map(|m| m.response_time).sum();
    let n_f64 = n as f64;

    let cpu_utilization = if total_time > 0 {
        total_busy_time as f64 / total_time as f64
    } else {
        0.0
    };

    let throughput = if total_time > 0 {
        n_f64 / total_time as f64
    } else {
        0.0
    };

    Ok(SchedulerResult {
        process_metrics,
        gantt,
        avg_turnaround:  sum_tat as f64 / n_f64,
        avg_waiting:     sum_wt  as f64 / n_f64,
        avg_response:    sum_rt  as f64 / n_f64,
        cpu_utilization,
        throughput,
        total_time,
    })
}

// ─────────────────────── Display ──────────────────────────

fn print_table(procs: &[Process], result: &SchedulerResult) {
    println!("\n{:═<60}", "");
    println!("  ROUND ROBIN SCHEDULER — PROCESS METRICS");
    println!("{:═<60}", "");
    println!("{:<8} {:<10} {:<8} {:<10} {:<12} {:<10} {:<10}",
        "Process", "Arrival", "Burst", "Finish", "Turnaround", "Waiting", "Response");
    println!("{:-<8} {:-<10} {:-<8} {:-<10} {:-<12} {:-<10} {:-<10}",
        "", "", "", "", "", "", "");

    for (p, m) in procs.iter().zip(result.process_metrics.iter()) {
        println!("{:<8} {:<10} {:<8} {:<10} {:<12} {:<10} {:<10}",
            p.name,
            p.arrival_time,
            p.burst_time,
            p.finish_time,
            m.turnaround_time,
            m.waiting_time,
            m.response_time,
        );
    }

    println!("\n── Aggregate Statistics ──────────────────────────────");
    println!("  Avg Turnaround : {:.2} ms", result.avg_turnaround);
    println!("  Avg Waiting    : {:.2} ms", result.avg_waiting);
    println!("  Avg Response   : {:.2} ms", result.avg_response);
    println!("  CPU Util.      : {:.1}%",   result.cpu_utilization * 100.0);
    println!("  Throughput     : {:.4} proc/ms", result.throughput);
    println!("  Total Time     : {} ms",    result.total_time);
}

fn print_gantt(result: &SchedulerResult) {
    println!("\n── Gantt Chart ───────────────────────────────────────");
    print!("|");
    for entry in &result.gantt {
        let width = (entry.end - entry.start) as usize * 2;
        let width  = width.max(4);
        let label  = &entry.name;
        let pad_l  = (width.saturating_sub(label.len())) / 2;
        let pad_r  = width.saturating_sub(label.len()).saturating_sub(pad_l);
        print!("{}{}{}", " ".repeat(pad_l), label, " ".repeat(pad_r));
        print!("|");
    }
    println!();

    // Timeline
    if let Some(first) = result.gantt.first() {
        print!("{}", first.start);
    }
    for entry in &result.gantt {
        let width = (entry.end - entry.start) as usize * 2;
        let width  = width.max(4);
        print!("{:>width$}", entry.end, width = width);
    }
    println!();
}

// ─────────────────────── main ─────────────────────────────

fn main() {
    // Build process list
    let processes: Vec<Process> = vec![
        Process::new(1, "P1", 0, 10).expect("valid process"),
        Process::new(2, "P2", 1,  4).expect("valid process"),
        Process::new(3, "P3", 2,  6).expect("valid process"),
        Process::new(4, "P4", 3,  3).expect("valid process"),
    ];

    // ── Run with Q = 4 ──
    const QUANTUM_A: u64 = 4;
    println!("╔═══════════════════════════════════╗");
    println!("║   Round Robin  |  Quantum = {}ms   ║", QUANTUM_A);
    println!("╚═══════════════════════════════════╝");

    match run_round_robin(&processes, QUANTUM_A) {
        Ok(result) => {
            // We need sorted processes for display; run_round_robin sorts internally
            let mut sorted = processes.clone();
            sorted.sort_by_key(|p| (p.arrival_time, p.pid));
            print_table(&sorted, &result);
            print_gantt(&result);
        }
        Err(e) => eprintln!("Scheduler error: {e}"),
    }

    println!();

    // ── Run with Q = 2 for comparison ──
    const QUANTUM_B: u64 = 2;
    println!("╔═══════════════════════════════════╗");
    println!("║   Round Robin  |  Quantum = {}ms   ║", QUANTUM_B);
    println!("╚═══════════════════════════════════╝");

    match run_round_robin(&processes, QUANTUM_B) {
        Ok(result) => {
            let mut sorted = processes.clone();
            sorted.sort_by_key(|p| (p.arrival_time, p.pid));
            print_table(&sorted, &result);
            print_gantt(&result);
        }
        Err(e) => eprintln!("Scheduler error: {e}"),
    }

    // ── Demonstrate error handling ──
    let empty: Vec<Process> = vec![];
    match run_round_robin(&empty, 4) {
        Ok(_)  => unreachable!(),
        Err(e) => println!("\n[Error handling test] Caught: {e}"),
    }

    match run_round_robin(&processes, 0) {
        Ok(_)  => unreachable!(),
        Err(e) => println!("[Error handling test] Caught: {e}"),
    }
}
```

### Rust Ownership & Memory Model Notes

```
  Ownership flow:
  ┌───────────────────────────────────────────────────────────┐
  │  main()                                                    │
  │  ├── processes: Vec<Process>          (owns all process   │
  │  │                                    data on heap)       │
  │  │                                                        │
  │  └── run_round_robin(&processes, q)                       │
  │       │                                                   │
  │       ├── &[Process] (shared borrow — read-only view)     │
  │       │                                                   │
  │       ├── procs: Vec<Process>  (internal clone — mutable) │
  │       │   → simulation modifies remaining_time etc.       │
  │       │   → original processes in main() UNCHANGED        │
  │       │                                                   │
  │       ├── ready_queue: VecDeque<usize>  (indices only)    │
  │       │   → no duplication of Process data                │
  │       │                                                   │
  │       └── Returns SchedulerResult (moves out of fn)       │
  │           → caller now owns the result                    │
  └───────────────────────────────────────────────────────────┘

  VecDeque is backed by a ring buffer:
  ┌────────────────────────────────┐
  │  heap: [_, _, 2, 3, 0, 1, _]  │
  │            ^              ^    │
  │           head           tail  │
  │  pop_front → O(1) (move head) │
  │  push_back → O(1) amortized   │
  └────────────────────────────────┘
```

---

## 12. Weighted Round Robin (WRR)

### The Problem with Basic Round Robin

Pure Round Robin gives every process **exactly equal** quantum. But what if some processes deserve more CPU time than others? For example:
- A video streaming process needs 3× CPU of a background sync task
- A high-priority kernel thread vs. a user-space batch job

### The Solution: Weighted Round Robin

Each process is assigned a **weight** W_i. In each "round", process i gets W_i quanta (or runs for W_i × Q time).

```
  Process Weights:
  ┌──────┬────────┐
  │  P1  │ W = 3  │  gets 3 quanta per round
  │  P2  │ W = 1  │  gets 1 quantum per round
  │  P3  │ W = 2  │  gets 2 quanta per round
  └──────┴────────┘

  Total weight per round = 3 + 1 + 2 = 6 quanta

  One full round:
  [P1][P1][P1][P2][P3][P3]  → then repeat
```

### WRR Execution Pattern

```
  Round 1:   P1─P1─P1─P2─P3─P3
  Round 2:   P1─P1─P1─P2─P3─P3
  Round 3:   ...
```

### WRR in Networking (Packet Scheduling)

WRR is extremely common in network switches and routers:
- Each traffic flow (e.g., voice, video, data) gets a weight
- The scheduler cycles through flows, sending W_i packets per turn
- Guarantees minimum bandwidth to each flow proportional to weight

```
  ┌─────────────────────────────────────────────────────┐
  │               Network Switch (WRR)                   │
  │                                                      │
  │  Flow A (W=4): [pkt][pkt][pkt][pkt]─┐               │
  │  Flow B (W=2): [pkt][pkt]────────────┤──> Output    │
  │  Flow C (W=1): [pkt]─────────────────┘    Port      │
  │                                                      │
  │  Per round: A gets 4/7 = 57% bandwidth              │
  │             B gets 2/7 = 29% bandwidth               │
  │             C gets 1/7 = 14% bandwidth               │
  └─────────────────────────────────────────────────────┘
```

### WRR Implementation Sketch (Rust)

```rust
struct WeightedProcess {
    process:        Process,
    weight:         u32,    // quanta per round
    remaining_quota: u32,   // quanta left in current round
}

fn weighted_round_robin(mut procs: Vec<WeightedProcess>, quantum: u64) {
    // Reset quotas at start of each round
    for p in &mut procs {
        p.remaining_quota = p.weight;
    }

    loop {
        let mut all_done = true;
        for p in &mut procs {
            while p.remaining_quota > 0 && p.process.remaining_time > 0 {
                // run one quantum
                let run = p.process.remaining_time.min(quantum);
                p.process.remaining_time -= run;
                p.remaining_quota -= 1;
                if p.process.remaining_time > 0 { all_done = false; }
            }
            p.remaining_quota = p.weight; // reset for next round
        }
        if all_done { break; }
    }
}
```

---

## 13. Deficit Round Robin (DRR)

### The Problem with WRR

WRR works with **fixed packet sizes** (networking). But if packets have **variable sizes**, a flow with W=2 sending large packets can still consume more bandwidth than a flow with W=3 sending small packets.

### Deficit Round Robin — The Fix

DRR adds a **deficit counter** D_i to each flow. Each round:
1. D_i += quantum_allowance (credit given)
2. Flow sends packets as long as D_i >= packet_size
3. Leftover credit carries over to next round (no wastage)

```
  State per flow:
  ┌────────────────────────────────────────┐
  │  deficit_counter  D_i  (accumulated)  │
  │  quantum_allowance Q_i (per round)     │
  │  packet_queue     [...packets...]      │
  └────────────────────────────────────────┘

  Each round:
  D_i += Q_i
  WHILE D_i >= packet_queue.front().size:
      send packet
      D_i -= packet.size
  // Leftover D_i is carried to next round
```

DRR achieves **byte-level fairness** with **O(1) per packet** complexity — a critical property for high-speed network hardware.

---

## 14. Round Robin in Load Balancing & Networking

### HTTP Load Balancer (Round Robin)

```
  Client Requests:
  req1, req2, req3, req4, req5, req6 ...

                    ┌────────────────────┐
                    │   Load Balancer    │
                    │  (Round Robin)     │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             v                v                v
        ┌─────────┐      ┌─────────┐      ┌─────────┐
        │Server 1 │      │Server 2 │      │Server 3 │
        │req1,req4│      │req2,req5│      │req3,req6│
        └─────────┘      └─────────┘      └─────────┘

  Pattern: req → S1, req → S2, req → S3, req → S1, ...
```

### DNS Round Robin

Multiple IP addresses are associated with a single hostname. DNS rotates which IP is returned first:

```
  DNS Query: "api.example.com"

  Response rotation:
  Query 1: [192.168.1.1, 192.168.1.2, 192.168.1.3]  (1st)
  Query 2: [192.168.1.2, 192.168.1.3, 192.168.1.1]  (2nd)
  Query 3: [192.168.1.3, 192.168.1.1, 192.168.1.2]  (3rd)
  Query 4: [192.168.1.1, 192.168.1.2, 192.168.1.3]  (wraps)
```

Clients typically connect to the first IP returned → traffic distributes across servers.

### Limitations of Round Robin Load Balancing

1. **No health awareness**: If a server crashes, requests still get sent to it
2. **No load awareness**: A slow request and a fast request count equally
3. **No session persistence**: Stateful protocols may break (same client → different server)

Solutions:
- **Least connections**: Route to server with fewest active connections
- **IP hashing**: Same client IP always → same server (session affinity)
- **WRR**: Servers with higher capacity get more requests

---

## 15. Round Robin vs Other Scheduling Algorithms

```
  ┌─────────────────┬─────────────┬──────────┬───────────┬───────────┬────────────┐
  │  Algorithm      │ Preemptive? │ Starvation│ Resp Time │ Throughput│ Complexity │
  ├─────────────────┼─────────────┼──────────┼───────────┼───────────┼────────────┤
  │ FCFS            │ No          │ No        │ High      │ Moderate  │ O(1)       │
  │ SJF             │ No          │ Yes       │ Low       │ High      │ O(N log N) │
  │ SRTF (preempt.) │ Yes         │ Yes       │ Optimal   │ High      │ O(N log N) │
  │ Priority        │ Optional    │ Yes       │ Variable  │ Variable  │ O(log N)   │
  │ Round Robin     │ Yes (always)│ No        │ Fair      │ Moderate  │ O(1)       │
  │ Multilevel Q    │ Both        │ Partial   │ Variable  │ High      │ O(log N)   │
  └─────────────────┴─────────────┴──────────┴───────────┴───────────┴────────────┘
```

### FCFS vs Round Robin

```
  3 processes: P1(burst=20), P2(burst=2), P3(burst=3)  — all arrive at t=0

  FCFS:
  [P1─────────────────][P2──][P3───]
  0                   20   22    25
  Avg WT = (0 + 20 + 22) / 3 = 14.0

  RR (Q=4):
  [P1─][P2──][P3───][P1─][P1─][P1─][P1─]
  0    4    6     9    13  17  21   25
  Avg WT = much more complex but more fair
  P2 finishes at t=6 (waited only 4ms), P3 at t=9

  Key insight: FCFS is brutal for short jobs if a long job arrives first.
  RR protects short jobs by giving them CPU quickly.
```

### SJF vs Round Robin

SJF (Shortest Job First) minimizes average waiting time **optimally**, but requires knowing future burst times (impossible in practice) and causes starvation of long jobs. Round Robin trades optimality for fairness and practicality.

---

## 16. Edge Cases & Pathological Inputs

### Edge Case 1: All Processes Arrive at Same Time

```
  P1(burst=1), P2(burst=1), P3(burst=1), Q=4

  All burst < Q → each runs to completion in one turn
  Result: degenerates to FCFS for this case
  WT: P1=0, P2=1, P3=2
```

### Edge Case 2: Single Process

```
  P1(burst=15), Q=4

  Runs: [P1][P1][P1][P1 (3ms)]
  WT = 0, TAT = 15, RT = 0
  No context switch overhead at all
```

### Edge Case 3: Q = 1 (Minimum Quantum)

```
  P1(burst=3), P2(burst=3), P3(burst=3), Q=1

  [P1][P2][P3][P1][P2][P3][P1][P2][P3]
  Maximum context switches: 9
  Maximum overhead, but perfect fairness
  All finish at exactly t=9 (all same burst)
```

### Edge Case 4: Burst Time = Exact Multiple of Q

```
  P1(burst=8), Q=4 → P1 runs exactly 2 quanta
  On second run: remaining=4 = quantum exactly
  Decision: run for 4ms, remaining=0 → FINISH (no preemption)
  Must check: if remaining <= Q, run to completion (no re-enqueue)
```

### Edge Case 5: Late-Arriving Process During Idle CPU

```
  P1(burst=2, arrival=0), P2(burst=3, arrival=10), Q=4

  t=0: P1 runs → finishes at t=2
  t=2: queue empty, P2 not yet arrived
  t=2–10: CPU IDLE
  t=10: P2 arrives, runs → finishes at t=13

  Idle gap must be handled: advance time to next arrival
  without spinning (busy-wait would waste CPU cycles)
```

### Edge Case 6: Process Arrives During Another's Quantum

```
  P1(arrival=0, burst=10), P2(arrival=3, burst=5), Q=4

  t=0: P1 starts running
  t=3: P2 arrives → enqueued (queue: [P2])
  t=4: P1 preempted → queue becomes [P2, P1] (P2 first!)
  t=4: P2 runs (not P1!)

  Key: Processes arriving DURING a quantum go before the
  preempted process in the queue.
```

---

## 17. Real Operating System Usage

### Linux: CFS (Completely Fair Scheduler)

Linux does not use pure Round Robin but CFS, which:
- Tracks **virtual runtime** (vruntime) for each process
- Uses a **red-black tree** ordered by vruntime
- Always runs the process with the **smallest vruntime** (most CPU-starved)
- Preempts when current vruntime exceeds minimum by `sched_latency_ns / N`

This is conceptually equivalent to Round Robin with Q = sched_latency_ns / N, but with O(log N) scheduling (due to tree) and perfect proportional fairness.

```
  CFS Virtual Runtime Tree:
              [P3: vrt=50]
             /             \
      [P1: vrt=30]    [P4: vrt=80]
         /
  [P2: vrt=10]   ← always run this (leftmost = smallest vrt)
```

### Windows: Multilevel Feedback Queue

Windows uses a 32-priority-level multilevel queue. Real-time threads (priorities 16–31) get strict priority. User threads (0–15) get Round Robin within each priority level, with **priority boosting** for I/O-bound processes.

### FreeBSD / macOS: ULE Scheduler

Uses a two-queue approach: one for interactive (short CPU bursts), one for batch. Round Robin within each. Interactive queue has priority.

---

## 18. Mental Models for Mastery

### Model 1: The Fairness-Efficiency Duality

Round Robin perfectly embodies a fundamental systems tradeoff:

```
  FAIRNESS ←──────────────────────────→ EFFICIENCY
  (every process gets equal turns)     (best processes finish fastest)

  RR maximizes: fairness
  SJF maximizes: efficiency (avg WT)
  CFS: approximates both

  Your job as a systems engineer: choose where on this spectrum
  your workload belongs. Interactive systems need fairness.
  Batch systems may prefer efficiency.
```

### Model 2: The Buffer Size Analogy

Think of Q like a buffer size in I/O systems:
- Too small → overhead dominates (like reading 1 byte at a time)
- Too large → latency spikes (like waiting to fill a huge buffer)
- Just right → amortizes overhead while keeping latency bounded

**This pattern appears everywhere in systems**: batch size, page size, network MTU, cache line size. Master the tradeoff once, recognize it in every domain.

### Model 3: Work-Conserving Scheduler

Round Robin is **work-conserving**: the CPU is never idle if there is work to do. This is an important property. Non-work-conserving schedulers (e.g., some real-time schedulers) intentionally idle the CPU to enforce timing constraints.

### Cognitive Principle: Chunking

When you simulate Round Robin mentally, chunk the problem:
1. **First pass**: identify all quanta and their owners
2. **Second pass**: identify which processes finish in each round
3. **Third pass**: compute metrics from the completion times

Don't try to hold all state simultaneously. Build a **timeline** incrementally — the same technique your code uses.

### Expert Problem-Solving Pattern

When given any scheduling problem:

```
Step 1: Draw the timeline axis (0 → total_burst_sum)
Step 2: Identify all arrival events (sort by arrival time)
Step 3: Simulate round by round — always ask:
        "Who is at the FRONT of the ready queue RIGHT NOW?"
Step 4: Track remaining time for each process
Step 5: Compute metrics AFTER the full simulation (not during)
Step 6: Verify: sum(burst_times) = total_busy_time
                (this catches errors immediately)
```

### Pattern Recognition: When Is Round Robin the Right Tool?

| Situation | Use Round Robin? |
|---|---|
| Interactive, time-sharing system | ✅ Yes — fairness required |
| Batch processing, throughput priority | ❌ Prefer SJF |
| Real-time with deadlines | ❌ Use EDF or RM |
| Equal-priority tasks, fairness needed | ✅ Yes |
| Tasks with very different durations | ⚠️ WRR might be better |
| Network packet scheduling | ✅ WRR or DRR |
| Load balancing, stateless services | ✅ Yes |

---

## Summary: Round Robin at a Glance

```
  ┌────────────────────────────────────────────────────────────────┐
  │                   ROUND ROBIN — SUMMARY                         │
  ├────────────────────────────────────────────────────────────────┤
  │  Type          │ Preemptive, time-sharing scheduling            │
  │  Data Structure│ Circular queue (FIFO for each round)           │
  │  Time Complex. │ O(1) per scheduling decision                   │
  │  Space Complex.│ O(N) for ready queue                           │
  │  Starvation    │ IMPOSSIBLE — every process gets a turn         │
  │  Fairness      │ MAX-MIN fair (equal share for equal priority)  │
  │  Key Parameter │ Quantum Q — dominates all performance metrics  │
  │  Best For      │ Interactive, time-sharing, equal-priority tasks│
  │  Weakness      │ Higher avg TAT than SJF; context switch cost   │
  ├────────────────────────────────────────────────────────────────┤
  │  Metrics:                                                       │
  │    TAT = Finish − Arrival                                       │
  │    WT  = TAT − Burst                                            │
  │    RT  = FirstExec − Arrival                                    │
  ├────────────────────────────────────────────────────────────────┤
  │  Variants: Weighted RR, Deficit RR, Multilevel RR              │
  │  Real-world: Linux CFS, network schedulers, load balancers     │
  └────────────────────────────────────────────────────────────────┘
```

---

*End of Guide — Round Robin: Complete, In-Depth Coverage*

Now I'll create the comprehensive Round Robin guide as a `.md` file.Here is the complete guide. Every section is crafted for deep understanding, not surface familiarity. Here is exactly what is covered and why each part matters:

**Foundations first** — Every term (preemption, quantum, TAT, WT, RT, starvation, context switch) is defined precisely before it is used anywhere. No assumed vocabulary.

**Architecture with ASCII** — The full OS-level system diagram, the PCB layout, the process state machine, and the circular queue memory model are all drawn as real ASCII art, not hand-waving descriptions.

**The critical arrival-during-execution detail** — Most guides skip this. When a new process arrives *while* another is running its quantum, it must be enqueued *before* the preempted process is re-enqueued. This distinction changes your output and is tested in real interviews.

**Time Quantum deep analysis** — The two extremes (Q→0 degenerates to Processor Sharing, Q→∞ degenerates to FCFS), the overhead equation, the 80% rule, and the exact mathematical derivation of the tradeoff.

**C implementation** — Uses a proper `CircularQueue` with `head`/`tail`/`size`, handles idle CPU gaps, handles arrivals during execution, computes all six metrics, generates a Gantt chart, and frees all heap allocations explicitly.

**Rust implementation** — Uses `VecDeque<usize>` (indices only, no data duplication), a proper `SchedulerError` enum with `Display`, `Option`-style `UNSET_TIME` tracking, iterator-based metric aggregation, and zero `unwrap()` without justification.

**Weighted and Deficit RR** — The generalizations that appear in networking and real OS schedulers.

**Edge cases** — Single process, all same arrival, Q = 1, burst = exact multiple of Q, late-arriving process during idle CPU — all explicitly handled.

**The core mental model** — The fairness-efficiency duality is a universal systems pattern. Once you see it in Round Robin, you will recognize it in buffer sizing, MTU selection, cache line size, and batch I/O — everywhere.