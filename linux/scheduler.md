# Linux Scheduler: Complete In-Depth Guide

> **Audience:** Systems engineers, Rust/C developers targeting production Linux.  
> **Kernel version baseline:** 6.6+ (EEVDF era). CFS context included for legacy understanding.  
> **Companion code:** C and Rust implementations throughout.

---

## Table of Contents

1. [Mental Model & Vocabulary](#1-mental-model--vocabulary)
2. [Scheduler Evolution: O(n) → O(1) → CFS → EEVDF](#2-scheduler-evolution)
3. [Scheduling Classes & Policies](#3-scheduling-classes--policies)
4. [CFS Deep Dive: Virtual Runtime & the Red-Black Tree](#4-cfs-deep-dive)
5. [EEVDF: The Modern Replacement](#5-eevdf-the-modern-replacement)
6. [Context Switching Internals](#6-context-switching-internals)
7. [Priority, Nice Values & Weight Tables](#7-priority-nice-values--weight-tables)
8. [Real-Time Scheduling: SCHED_FIFO & SCHED_RR](#8-real-time-scheduling)
9. [Deadline Scheduling: SCHED_DEADLINE (EDF + CBS)](#9-deadline-scheduling)
10. [Preemption Models](#10-preemption-models)
11. [SMP Load Balancing](#11-smp-load-balancing)
12. [NUMA-Aware Scheduling](#12-numa-aware-scheduling)
13. [CPU Affinity & Isolation](#13-cpu-affinity--isolation)
14. [cgroups v2 & CPU Bandwidth Control](#14-cgroups-v2--cpu-bandwidth-control)
15. [Scheduler Tunables](#15-scheduler-tunables)
16. [Idle & Power-Aware Scheduling](#16-idle--power-aware-scheduling)
17. [Observability: perf, ftrace, BPF, sched_debug](#17-observability)
18. [Profiling & Latency Analysis](#18-profiling--latency-analysis)
19. [C Implementations](#19-c-implementations)
20. [Rust Implementations](#20-rust-implementations)
21. [Security Considerations](#21-security-considerations)
22. [Common Pitfalls & War Stories](#22-common-pitfalls--war-stories)
23. [Hands-On Exercises](#23-hands-on-exercises)
24. [Further Reading](#24-further-reading)

---

## 1. Mental Model & Vocabulary

### One-Line Summary

The Linux scheduler decides **which task runs on which CPU at any given moment**, balancing fairness, latency, throughput, and energy efficiency across a heterogeneous system.

### The Core Abstraction

```
Physical CPU cores
      │
      ▼
  Run Queues (per-CPU)
      │
      ├── dl_rq     (SCHED_DEADLINE tasks)
      ├── rt_rq     (SCHED_FIFO / SCHED_RR tasks)
      └── cfs_rq    (SCHED_NORMAL / SCHED_BATCH / SCHED_IDLE tasks)
                         │
                     rb-tree / wait list (vruntime ordered)
```

**Every CPU has its own run queue.** The scheduler picks the highest-priority non-empty class first. Within CFS, it picks the task with the smallest virtual runtime.

### Key Vocabulary

| Term | Definition |
|------|-----------|
| `task_struct` | Kernel representation of a process/thread |
| `sched_entity` (se) | Scheduling entity embedded in `task_struct` |
| `vruntime` | Virtual runtime — normalized CPU time, the CFS ordering key |
| `min_vruntime` | Minimum vruntime across all runnable tasks on a CPU |
| `time slice` | Maximum continuous CPU time before preemption |
| `load weight` | Numeric weight derived from nice value; scales vruntime |
| `runqueue` | Per-CPU data structure holding all runnable tasks |
| `migration` | Moving a task between CPU runqueues |
| `load balancer` | Periodic/triggered code that equalises load across CPUs |
| `cfs_bandwidth` | cgroup mechanism to throttle CPU usage |
| `sched_latency_ns` | Target scheduling period — CFS aims to run every task once within this window |
| `preempt_count` | Per-CPU counter preventing preemption when > 0 |
| `wakeup preemption` | When a waking task immediately preempts the current one |
| `tick` | Periodic timer interrupt (typically 250 Hz or 1000 Hz); drives accounting |
| `HRTICK` | High-resolution tick for finer-grained preemption |

---

## 2. Scheduler Evolution

### 2.1 The O(n) Scheduler (≤ 2.4)

**Algorithm:** Single global runqueue. On each schedule() call, iterate all runnable tasks, compute "goodness", pick the best.

**Problems:**
- O(n) per schedule call — catastrophic at >1000 tasks
- Single lock = SMP bottleneck
- Poor real-time support
- Starvation possible

### 2.2 The O(1) Scheduler (2.5–2.6.22, Ingo Molnár)

**Algorithm:** 2 fixed-size priority arrays per CPU (`active`, `expired`). 140 priority levels. Bitmask find-first-set → O(1) pick.

```
active[140]   expired[140]
   │               │
[prio 0] → task   [prio 0] → ...
[prio 1] → task   ...
...
[prio 139]        [prio 139]
```

When `active` is exhausted, swap pointers with `expired`. Interactive tasks get heuristic boosts to priority.

**Problems:**
- Interactive detection heuristics were famously complex and wrong
- "Unfair" — a process could starve
- Heuristics tied to specific workload patterns

### 2.3 CFS — Completely Fair Scheduler (2.6.23+, Ingo Molnár)

**Core Idea:** Model a perfectly fair multi-tasking CPU. Each task should receive `1/N` of CPU time. Track divergence from ideal using `vruntime`. Always run the task furthest behind.

**Data Structure:** Red-black tree ordered by vruntime. Leftmost node = next to run. O(log N) insert/delete.

### 2.4 EEVDF — Earliest Eligible Virtual Deadline First (6.6+, Peter Zijlstra)

**Core Idea:** Combines virtual time (like CFS) with a deadline concept. Each task has an "eligible time" (can't run before this) and a "virtual deadline" (must have run by this). Pick the eligible task with the earliest virtual deadline.

Fixes CFS wakeup-preemption issues and provides better latency guarantees.

---

## 3. Scheduling Classes & Policies

Linux uses a **layered class system**. Each class implements a `sched_class` vtable. Classes are checked in strict priority order:

```
stop_sched_class       (highest — migrate_disable, stop_machine)
    │
dl_sched_class         (SCHED_DEADLINE)
    │
rt_sched_class         (SCHED_FIFO, SCHED_RR)
    │
fair_sched_class       (SCHED_NORMAL, SCHED_BATCH, SCHED_IDLE)
    │
idle_sched_class       (lowest — swapper/0 threads)
```

### Policy Table

| Policy | Class | Priority Range | Preemptible | Use Case |
|--------|-------|---------------|-------------|----------|
| `SCHED_NORMAL` (0) | fair | nice -20..+19 | Yes | General-purpose processes |
| `SCHED_BATCH` (3) | fair | nice -20..+19 | Yes | CPU-bound batch jobs, no wakeup preemption |
| `SCHED_IDLE` (5) | fair | (below nice +19) | Yes | Very low priority background tasks |
| `SCHED_FIFO` (1) | rt | 1..99 | By higher RT only | Hard real-time, runs until blocks/yields |
| `SCHED_RR` (2) | rt | 1..99 | By higher RT + timeslice | Soft real-time with round-robin among equals |
| `SCHED_DEADLINE` (6) | dl | (runtime,period,deadline) | Yes | EDF tasks with CBS |

### Setting Policies from Userspace

```c
// C: set SCHED_FIFO with priority 50
struct sched_param param = { .sched_priority = 50 };
sched_setscheduler(0, SCHED_FIFO, &param);

// C: set SCHED_DEADLINE
struct sched_attr attr = {
    .size           = sizeof(attr),
    .sched_policy   = SCHED_DEADLINE,
    .sched_runtime  = 5 * 1000 * 1000,   // 5ms
    .sched_period   = 10 * 1000 * 1000,  // 10ms
    .sched_deadline = 10 * 1000 * 1000,  // 10ms
};
syscall(SYS_sched_setattr, 0, &attr, 0);
```

---

## 4. CFS Deep Dive

### 4.1 Virtual Runtime

The fundamental invariant:

```
vruntime_delta = wall_clock_delta × (NICE_0_LOAD / task_weight)
```

- `NICE_0_LOAD` = 1024 (weight of a nice=0 task)
- Higher weight (lower nice) → vruntime grows **slower** → task appears to "fall behind" less → gets more CPU
- Lower weight (higher nice) → vruntime grows **faster** → task falls behind → gets less CPU

```c
// Simplified from kernel/sched/fair.c
static u64 calc_delta_fair(u64 delta, struct sched_entity *se)
{
    if (unlikely(se->load.weight != NICE_0_LOAD))
        delta = __calc_delta(delta, NICE_0_LOAD, &se->load);
    return delta;
}

// The actual scaling (fixed-point arithmetic):
// delta_fair = delta * (NICE_0_LOAD / weight)
//            = delta * NICE_0_LOAD / weight
```

### 4.2 The Red-Black Tree

```
         [vruntime=100]
        /               \
  [vrt=80]           [vrt=120]
   /    \             /     \
[60]   [90]       [110]    [130]
```

- **Leftmost node** = task with smallest vruntime = next to run
- Cached as `cfs_rq->rb_leftmost` — O(1) lookup
- Insert/delete: O(log N)
- The tree only contains **runnable** tasks (not blocked/sleeping ones)

### 4.3 Scheduling Period and Time Slices

CFS does not have a fixed time slice. It targets a **scheduling latency** (`sched_latency_ns`, default 6ms, sometimes 8ms):

```
time_slice_per_task = sched_latency_ns × (task_weight / total_rq_weight)
```

With N tasks all at nice=0:
```
time_slice = 6ms / N
```

But there's a floor: `sched_min_granularity_ns` (default 750µs). Below a threshold of tasks, slices are clamped.

**Throttle check on every tick:**
```c
// kernel/sched/fair.c: entity_tick()
if (cfs_rq->nr_running > 1)
    check_preempt_tick(cfs_rq, curr);

// Preempt if ran longer than ideal slice
// OR if the leftmost task's vruntime is > curr->vruntime + gran
```

### 4.4 Wakeup and Preemption

When a sleeping task wakes up, its vruntime may be very old (it missed CPU time). To prevent it from monopolising the CPU:

```c
// Place waking task's vruntime at:
vruntime = max(vruntime, min_vruntime - sched_latency_ns)
```

The waking task then checks if it should preempt the current task:
```c
// check_preempt_wakeup() in fair.c
// Preempt if: waking_vruntime + gran < curr_vruntime
```

### 4.5 Group Scheduling

CFS supports hierarchical scheduling via `task_group`. Each group gets a share of CPU proportional to its weight. Groups have their own `cfs_rq` nested inside the parent's tree.

```
root cfs_rq
├── group_A sched_entity (weight=1024)
│       └── group_A's cfs_rq
│               ├── task1
│               └── task2
└── group_B sched_entity (weight=512)
        └── group_B's cfs_rq
                └── task3
```

---

## 5. EEVDF: The Modern Replacement

**Paper basis:** "Earliest Eligible Virtual Deadline First" (Stoica, 1995).

### 5.1 Core Concepts

Each task has:
- **Eligible time (ve):** Virtual time at which the task becomes eligible to run (can't run before this)
- **Virtual deadline (vd):** `ve + (slice / weight)` — when the task's slice must be delivered by
- **Lag:** Accumulated service deficit/surplus relative to ideal fair share

```
eligible_time = se->ve
virtual_deadline = se->vd = ve + (r_i / w_i)
  where r_i = requested slice, w_i = weight
```

**Pick rule:** Among all eligible tasks (ve ≤ V, where V = current virtual time), pick the one with the **earliest virtual deadline**.

### 5.2 Why EEVDF Improves on CFS

| Problem | CFS | EEVDF |
|---------|-----|-------|
| Wakeup preemption | Heuristic-based, often wrong | Natural: check eligibility |
| Latency guarantees | Approximate | Bounded by virtual deadline |
| Starvation | Prevented by min_vruntime | Prevented by lag accounting |
| Interactive tasks | Priority boosting hacks | Shorter slice = earlier deadline = runs sooner |

### 5.3 Slice Tuning in EEVDF

EEVDF exposes `sched_slice` per task (via `sched_setattr` custom slice). A task requesting a smaller slice gets an earlier deadline → lower latency. Latency-sensitive tasks should request small slices.

```c
// Set custom slice (EEVDF, kernel 6.6+)
struct sched_attr attr = {
    .size        = sizeof(attr),
    .sched_policy = SCHED_NORMAL,
    .sched_flags  = SCHED_FLAG_UTIL_CLAMP_MIN,
    // sched_runtime used as slice hint in EEVDF
};
```

---

## 6. Context Switching Internals

### 6.1 The `schedule()` Call Path

```
schedule()
  ├── __schedule(false)
  │     ├── local_irq_disable()
  │     ├── rq = this_rq()
  │     ├── prev = rq->curr
  │     ├── deactivate_task(prev)  // if TASK_INTERRUPTIBLE etc.
  │     ├── next = pick_next_task(rq)
  │     │     └── Tries each sched_class in order
  │     │           dl_class → rt_class → fair_class → idle_class
  │     ├── rq->curr = next
  │     ├── context_switch(rq, prev, next)
  │     │     ├── switch_mm()       // TLB flush / CR3 update
  │     │     └── switch_to()       // Save/restore registers, stack pointer
  │     └── (returns in new task's context)
  └── local_irq_enable()
```

### 6.2 `switch_to()` on x86_64

```c
// arch/x86/include/asm/switch_to.h (simplified)
#define switch_to(prev, next, last)                 \
    asm volatile(                                    \
        "pushq %%rbp\n\t"                           \
        "movq %%rsp, %P[prev_sp](%[prev])\n\t"     \  // save prev RSP
        "movq %P[next_sp](%[next]), %%rsp\n\t"     \  // load next RSP
        "movq $1f, %P[prev_ip](%[prev])\n\t"       \  // save prev RIP
        "pushq %P[next_ip](%[next])\n\t"           \  // push next RIP
        "ret\n\t"                                   \  // jump to next
        "1:\t"                                      \
        "popq %%rbp\n\t"                            \
        ...
    )
```

**What is saved/restored:**
- Callee-saved registers: rbx, rbp, r12-r15
- RSP (stack pointer) — most important
- RIP (instruction pointer) — via ret trick
- Floating point / vector state: lazy-saved (only on FPU use or signal)

**What is NOT saved in the task struct:**
- Caller-saved registers (rbx, rcx, rdx, rsi, rdi, r8-r11): the calling convention means they're already on the stack

### 6.3 TLB and CR3

On a process switch (different `mm_struct`):
- CR3 is updated → TLB flush (costly: ~100-1000 cycles)
- With PCID (Process Context Identifier), CR3 tags TLB entries → avoid full flush
- Threads sharing the same `mm_struct` do NOT trigger a CR3 update

### 6.4 Context Switch Cost

| Scenario | Approximate Cost |
|----------|-----------------|
| Thread switch (same process) | 1–5 µs |
| Process switch (different address space, no PCID) | 5–20 µs |
| Process switch (PCID enabled) | 2–8 µs |
| RT task preemption latency (PREEMPT_RT) | <100 µs |

Measure with:
```bash
perf stat -e context-switches,cpu-migrations ./myapp
```

---

## 7. Priority, Nice Values & Weight Tables

### 7.1 The Priority Space

```
RT priority:    0 (lowest RT) ... 99 (highest RT)
Nice:          -20 (highest nice weight) ... +19 (lowest)
Internal prio:   0 (highest) ... 139 (lowest)

Mapping:
  RT task prio P  → internal = 99 - P
  Normal task nice N → internal = 120 + N
```

### 7.2 Weight Table (prio_to_weight[])

The kernel maps nice values to weights using a table where each step is ~1.25× the previous:

```c
// kernel/sched/core.c
const int sched_prio_to_weight[40] = {
 /* -20 */ 88761, 71755, 56483, 46273, 36291,
 /* -15 */ 29154, 23254, 18705, 14949, 11916,
 /* -10 */  9548,  7620,  6100,  4904,  3906,
 /*  -5 */  3121,  2501,  1991,  1586,  1277,
 /*   0 */  1024,   820,   655,   526,   423,
 /*   5 */   335,   272,   215,   172,   137,
 /*  10 */   110,    87,    70,    56,    45,
 /*  15 */    36,    29,    23,    18,    15,
};
```

**Effect:** A nice=-20 task gets 88761/1024 ≈ **86.7× the CPU time** of a nice=0 task.

### 7.3 Changing Priority at Runtime

```bash
# Set nice value
renice -n -10 -p <pid>
nice -n 10 ./myprogram

# Set RT priority
chrt -f 50 ./myprogram          # SCHED_FIFO priority 50
chrt -r 30 ./myprogram          # SCHED_RR priority 30
chrt -p <pid>                   # show current policy

# Taskset for affinity + priority
taskset -c 2,3 chrt -f 99 ./realtime_app
```

---

## 8. Real-Time Scheduling

### 8.1 SCHED_FIFO

- **No time slice.** A FIFO task runs until it:
  1. Blocks (I/O, mutex, sleep)
  2. Calls `sched_yield()`
  3. Is preempted by a **higher-priority** RT task
- Same priority → FIFO order among themselves

**Danger:** A SCHED_FIFO task at prio 99 that never blocks will starve **everything** including kernel threads.

**Protection:**
```bash
# /proc/sys/kernel/sched_rt_runtime_us: RT tasks get at most this many µs per...
# /proc/sys/kernel/sched_rt_period_us:  ...this period
# Default: 950000 / 1000000 = 95% RT, 5% reserved for normal tasks

cat /proc/sys/kernel/sched_rt_runtime_us   # 950000
cat /proc/sys/kernel/sched_rt_period_us    # 1000000

# To allow full RT (DANGEROUS on production):
echo -1 > /proc/sys/kernel/sched_rt_runtime_us
```

### 8.2 SCHED_RR

Identical to FIFO but tasks at the **same priority** get time slices and round-robin among themselves.

```bash
# Default RR timeslice:
cat /proc/sys/kernel/sched_rr_timeslice_ms   # 100ms
```

### 8.3 RT Throttling Internals

```
rt_rq->rt_time       += delta_exec    (accumulate per period)
rt_rq->rt_runtime     = sched_rt_runtime_us

If rt_time > rt_runtime:
    throttle → move tasks to waiting state
    set timer for next period to unthrottle
```

### 8.4 Priority Inheritance

Linux mutexes (`pthread_mutex_t` with `PTHREAD_PRIO_INHERIT` protocol) implement priority inheritance to prevent **priority inversion**:

```c
pthread_mutexattr_t attr;
pthread_mutexattr_init(&attr);
pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT);
pthread_mutex_t mutex;
pthread_mutex_init(&mutex, &attr);
```

Classic priority inversion: Low(L) holds lock, High(H) waits, Medium(M) preempts L → H blocked by M. With inheritance, L temporarily inherits H's priority.

---

## 9. Deadline Scheduling

### 9.1 EDF + CBS Model

`SCHED_DEADLINE` implements **Earliest Deadline First (EDF)** with **Constant Bandwidth Server (CBS)** for isolation.

Each task specifies:
```
runtime  (Q): max CPU time consumed per period    [nanoseconds]
period   (P): replenishment interval              [nanoseconds]
deadline (D): relative deadline ≤ period          [nanoseconds]
```

**Utilization:** `U = Q/P`. Total system utilization must stay ≤ 1.0 (with headroom). The kernel enforces this via **admission control** — `sched_setattr` fails if adding the task would overcommit.

### 9.2 CBS Isolation

CBS ensures a DEADLINE task can't harm others by replenishing its budget `Q` at the start of each period. If it exhausts `Q`, it's throttled until the next replenishment.

```
Task deadline: abs_deadline = now + D
Replenishment: every P nanoseconds, budget reset to Q

Timeline:
|--Q consumed--|--throttled--|--Q replenished--|--Q consumed--|
0              Q             P                 P+Q
```

### 9.3 Example: Audio Rendering Task

```c
// 5ms compute every 10ms, deadline 8ms
struct sched_attr attr = {
    .size           = sizeof(struct sched_attr),
    .sched_policy   = SCHED_DEADLINE,
    .sched_runtime  = 5 * NSEC_PER_MSEC,    // 5ms budget
    .sched_period   = 10 * NSEC_PER_MSEC,   // 10ms period
    .sched_deadline = 8 * NSEC_PER_MSEC,    // 8ms deadline
};
// U = 5/10 = 50% — this task takes 50% of one CPU
```

---

## 10. Preemption Models

### 10.1 Kernel Preemption Modes

| Config | `PREEMPT` | Involuntary Schedule Points | Use Case |
|--------|-----------|---------------------------|----------|
| `PREEMPT_NONE` | Off | Only explicit `schedule()` calls | Server, batch |
| `PREEMPT_VOLUNTARY` | Partial | + explicit preemption points (`might_sleep()`) | Desktop |
| `PREEMPT` | Full | + interrupt return paths | Low-latency |
| `PREEMPT_RT` | Full RT | Converts spinlocks to mutexes, IRQ threads | Hard RT |

Check current mode:
```bash
cat /boot/config-$(uname -r) | grep PREEMPT
zcat /proc/config.gz | grep "^CONFIG_PREEMPT"
```

### 10.2 `preempt_count` Mechanics

```c
// include/linux/preempt.h
#define preempt_disable()   do { preempt_count_inc(); barrier(); } while (0)
#define preempt_enable()    do { ...; if (unlikely(preempt_count_dec_and_test())) __preempt_schedule(); } while (0)

// Layout of preempt_count (32-bit):
// [31:20] = NMI count
// [19:16] = hardirq count
// [15:8]  = softirq count  
// [7:0]   = preempt disable count
```

Preemption is **only allowed** when `preempt_count == 0` and `need_resched` flag is set.

### 10.3 `TIF_NEED_RESCHED`

When the scheduler wants to preempt the current task, it sets `TIF_NEED_RESCHED` in the task's thread_info flags. This flag is checked:
- On return from interrupt/syscall
- On preemption enable (`preempt_enable()`)
- On explicit `schedule()` calls

---

## 11. SMP Load Balancing

### 11.1 Overview

Linux uses a **pull model**: idle or lightly-loaded CPUs steal tasks from busy CPUs. Load balancing is **not** continuous — it runs periodically or on specific triggers.

### 11.2 Scheduling Domains

The topology is modelled as a hierarchy of **scheduling domains**:

```
NUMA Domain (node 0 ↔ node 1)
└── Package Domain (socket 0)
    └── MC Domain (L3 cache cluster)
        └── SMT Domain (hyperthreaded pair)
            └── CPU 0, CPU 1
```

Each domain has:
- `imbalance_pct`: trigger load balance when imbalance > this %
- `balance_interval`: how often to balance
- `flags`: `SD_BALANCE_NEWIDLE`, `SD_BALANCE_EXEC`, `SD_BALANCE_FORK`

### 11.3 Load Balance Triggers

| Trigger | Mechanism | Condition |
|---------|-----------|-----------|
| Periodic tick | `scheduler_tick()` | Every N ticks (domain-specific) |
| CPU goes idle | `newidle_balance()` | Immediately on idle |
| `exec()`/`fork()` | `sched_exec()` / `sched_fork()` | Task creation |
| Manual | `sched_setaffinity()` | Affinity change |

### 11.4 The Pull Algorithm

```
load_balance(src_rq, dst_rq, sd):
    imbalance = busiest_group_load - dst_rq_load
    if imbalance < threshold: return

    busiest_rq = find_busiest_runqueue(sd)
    tasks_to_move = imbalance / task_avg_load

    for each candidate task in busiest_rq (from back of list):
        if task_hot(task): skip      // recently ran, cache-warm
        if !can_migrate(task, dst_cpu): skip  // affinity
        migrate(task, dst_cpu)
        if moved_enough: break
```

### 11.5 Task Hotness

A task is "hot" (cache-warm) and won't be migrated if:
```c
// kernel/sched/fair.c
static int task_hot(struct task_struct *p, struct lb_env *env)
{
    delta = rq_clock_task(env->src_rq) - p->se.exec_start;
    return delta < sysctl_sched_migration_cost; // default 500µs
}
```

### 11.6 Weighted Load Metric

Linux 5.0+ uses **PELT (Per-Entity Load Tracking)**:

```
load_avg = Σ (running_time_i × decay_factor^(now - time_i))
```

The decay is geometric with a half-life of ~32ms. This smooths out burst behaviour and tracks long-term average load.

---

## 12. NUMA-Aware Scheduling

### 12.1 NUMA Topology

On multi-socket systems, memory access latency depends on which NUMA node the memory is on:

```
Socket 0 (node 0)         Socket 1 (node 1)
CPUs: 0-15                CPUs: 16-31
RAM: 64GB (local)         RAM: 64GB (local)
    │                           │
    └───────── QPI/UPI ─────────┘
    Local: ~80ns            Remote: ~140ns
```

### 12.2 NUMA Balancing

Linux automatically migrates tasks and memory pages toward each other via **autonuma** (`CONFIG_NUMA_BALANCING`):

1. Periodically **unmap** task's pages (PROT_NONE)
2. On page fault → record which CPU accessed which page
3. Task scheduler: migrate task toward memory
4. Page migrator: migrate pages toward task

```bash
# Tune NUMA balancing
cat /proc/sys/kernel/numa_balancing          # 0=off, 1=on
cat /proc/sys/kernel/numa_balancing_scan_delay_ms
cat /proc/sys/kernel/numa_balancing_scan_size_mb

# View NUMA stats
numastat -p <pid>
numactl --hardware
```

### 12.3 Manual NUMA Policy

```bash
# Run on node 0 only, memory from node 0
numactl --cpunodebind=0 --membind=0 ./myapp

# Interleave memory across nodes (good for throughput)
numactl --interleave=all ./myapp
```

---

## 13. CPU Affinity & Isolation

### 13.1 Soft Affinity

```bash
# Pin process to CPUs 2 and 3
taskset -cp 2,3 <pid>

# Launch with affinity
taskset -c 2,3 ./myapp

# Programmatic
cpu_set_t cpuset;
CPU_ZERO(&cpuset);
CPU_SET(2, &cpuset);
CPU_SET(3, &cpuset);
sched_setaffinity(0, sizeof(cpuset), &cpuset);
```

### 13.2 Hard Isolation with `isolcpus`

For latency-critical tasks, isolate CPUs from the general scheduler:

```bash
# Boot parameter (grub)
GRUB_CMDLINE_LINUX="isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3"

# After boot, only explicitly affined tasks run on CPUs 2,3
# The kernel won't load-balance other tasks there
```

### 13.3 `nohz_full` — Tickless CPUs

By default, the scheduler tick fires 250 Hz (or 1000 Hz), interrupting even isolated CPUs. `nohz_full` suppresses the tick on CPUs with ≤1 runnable task:

```bash
# Verify tickless operation
trace-cmd record -e 'timer:tick_stop' -p function -P <pid>
```

### 13.4 IRQ Affinity

Move IRQs off isolated CPUs:
```bash
# Show IRQ affinity
cat /proc/irq/<N>/smp_affinity_list

# Move IRQ N away from CPUs 2,3
echo 0-1 > /proc/irq/<N>/smp_affinity_list

# Or use irqbalance with exclusions
irqbalance --banirq=<N> --banscript=...
```

---

## 14. cgroups v2 & CPU Bandwidth Control

### 14.1 cgroup CPU Controller

```bash
# Mount cgroup v2
mount -t cgroup2 none /sys/fs/cgroup

# Create a group
mkdir /sys/fs/cgroup/myapp

# Set CPU weight (replaces cpu.shares in v1)
# Default=100, range 1-10000
echo 200 > /sys/fs/cgroup/myapp/cpu.weight    # 2× normal

# Set hard CPU limit: 50ms every 100ms = 50% of 1 CPU
echo "50000 100000" > /sys/fs/cgroup/myapp/cpu.max

# Move process to cgroup
echo <pid> > /sys/fs/cgroup/myapp/cgroup.procs
```

### 14.2 CFS Bandwidth Control Internals

```
cfs_bandwidth:
    quota   = cpu.max[0]      // runtime per period
    period  = cpu.max[1]
    runtime = current remaining budget

Every tick:
    cfs_rq->runtime_remaining -= delta
    if runtime_remaining <= 0:
        throttle_cfs_rq(cfs_rq)   // stop scheduling this group's tasks

Every period:
    cfs_bandwidth_slack_timer fires
    refill: cfs_rq->runtime_remaining = quota
    unthrottle all throttled queues
```

### 14.3 Burst Mode

Linux 5.14+ supports `cpu.max.burst` — allows a cgroup to "borrow" future quota:

```bash
# Allow 10ms burst above quota
echo 10000 > /sys/fs/cgroup/myapp/cpu.max.burst
```

### 14.4 Monitoring Throttling

```bash
# Check if your cgroup is being throttled
cat /sys/fs/cgroup/myapp/cpu.stat
# nr_throttled  — times throttled
# throttled_usec — total throttled time

# This is a common production problem!
# Symptom: P99 latency spikes even though avg CPU is low
```

---

## 15. Scheduler Tunables

### 15.1 CFS Tunables (`/proc/sys/kernel/`)

| Tunable | Default | Description |
|---------|---------|-------------|
| `sched_latency_ns` | 6,000,000 | Target scheduling period (ns) |
| `sched_min_granularity_ns` | 750,000 | Minimum task run time before preemption |
| `sched_wakeup_granularity_ns` | 1,000,000 | Prevent wakeup preemption if gap < this |
| `sched_migration_cost_ns` | 500,000 | Task considered "hot" for this long |
| `sched_nr_migrate` | 32 | Max tasks migrated per load balance |
| `sched_child_runs_first` | 0 | Fork: child runs before parent |
| `sched_rt_period_us` | 1,000,000 | RT bandwidth period |
| `sched_rt_runtime_us` | 950,000 | RT bandwidth budget per period |

```bash
# Read all at once
sysctl -a | grep sched

# Tune for low-latency server (reduce scheduling period)
sysctl -w kernel.sched_latency_ns=3000000
sysctl -w kernel.sched_min_granularity_ns=300000
sysctl -w kernel.sched_wakeup_granularity_ns=500000
```

### 15.2 NUMA Tunables

```bash
sysctl kernel.numa_balancing=1
sysctl kernel.numa_balancing_scan_delay_ms=1000
sysctl kernel.numa_balancing_scan_period_min_ms=1000
sysctl kernel.numa_balancing_scan_period_max_ms=60000
sysctl kernel.numa_balancing_scan_size_mb=256
```

### 15.3 Scheduler Statistics

```bash
# Per-CPU scheduler stats
cat /proc/schedstat

# Per-task stats (latency, wait time, etc.)
cat /proc/<pid>/schedstat

# Fields: runtime, runqueue wait time, timeslices
# Format: <cpu_time_ns> <wait_time_ns> <nr_timeslices>
```

---

## 16. Idle & Power-Aware Scheduling

### 16.1 CPU Idle States (C-states)

When no task is runnable on a CPU, the idle thread runs and selects a C-state:

| State | Name | Exit Latency | Power Savings |
|-------|------|-------------|---------------|
| C0 | Active | 0 | 0% |
| C1 | Halt | ~1µs | ~30% |
| C1E | Enhanced Halt | ~1µs | ~35% |
| C3 | Sleep | ~50µs | ~70% |
| C6 | Deep Power Down | ~100µs | ~90% |
| C8 | Deeper Sleep | ~200µs | ~95% |

The `cpuidle` governor chooses C-states based on predicted idle duration.

```bash
# View C-state statistics
cat /sys/devices/system/cpu/cpu0/cpuidle/state*/usage
cat /sys/devices/system/cpu/cpu0/cpuidle/state*/time
cat /sys/devices/system/cpu/cpu0/cpuidle/state*/latency

# Force specific governor
echo menu > /sys/devices/system/cpu/cpuidle/current_governor
echo ladder > /sys/devices/system/cpu/cpuidle/current_governor
```

### 16.2 P-states and Frequency Scaling

```bash
# Scaling governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# Options: performance, powersave, ondemand, conservative, schedutil

# schedutil = scheduler-driven (best for most workloads since 4.7)
echo schedutil > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Force max frequency (latency-critical)
cpupower frequency-set -g performance
```

### 16.3 Energy-Aware Scheduling (EAS)

On ARM big.LITTLE systems, the scheduler considers energy efficiency when placing tasks:

```bash
# EAS active indicator
cat /sys/devices/system/cpu/cpufreq/policy0/energy_performance_preference
```

---

## 17. Observability

### 17.1 `perf sched`

```bash
# Record scheduling events
perf sched record -- sleep 10

# Replay and show summary
perf sched latency    # per-task scheduling latency
perf sched timehist   # timeline of schedule() calls
perf sched map        # ASCII art CPU/task timeline
perf sched stats      # aggregate stats

# Example output (latency):
# Task                  |   Runtime ms  | Switches | Avg delay ms | Max delay ms
# myapp:(1)             |     234.310   |      456 |      0.123   |      4.521
```

### 17.2 `ftrace` Scheduler Events

```bash
# Enable scheduler tracing
cd /sys/kernel/debug/tracing
echo 0 > tracing_on
echo "" > trace
echo "sched_switch sched_wakeup sched_migrate_task" > set_event
echo 1 > tracing_on
sleep 5
echo 0 > tracing_on
cat trace | head -100

# Output format:
# <task>-<pid> [<cpu>] <timestamp>: sched_switch: prev_comm=<> prev_pid=<> 
#   prev_state=<R/S/D> next_comm=<> next_pid=<>
```

### 17.3 BPF/eBPF Scheduler Observability

```bash
# BCC tools
runqlat            # Run queue latency histogram
runqlen            # Run queue length over time
cpudist            # On-CPU time distribution
offcputime         # Off-CPU time analysis
llcstat            # Cache hit rate by process

# Examples
runqlat 10 1       # 10-second histogram, 1 iteration
runqlen -C 10      # Show per-CPU queue lengths

# bpftrace one-liners
bpftrace -e 'tracepoint:sched:sched_switch { @[args->next_comm] = count(); }'
bpftrace -e 'tracepoint:sched:sched_wakeup { @latency = hist(nsecs - args->pid); }'
```

### 17.4 `/proc/sched_debug`

```bash
cat /proc/sched_debug
# Shows per-CPU runqueue state, vruntime of each task,
# load weights, throttling stats, scheduling domain info
```

### 17.5 `schedtool`

```bash
schedtool <pid>                     # show current policy
schedtool -F -p 50 <pid>           # set FIFO prio 50
schedtool -R -p 30 <pid>           # set RR prio 30
schedtool -D -t 5000000:10000000 <pid>  # DEADLINE runtime:period
```

---

## 18. Profiling & Latency Analysis

### 18.1 Wakeup Latency

The time from when a task becomes runnable to when it actually starts running:

```bash
# Measure with perf
perf stat -e sched:sched_wakeup,sched:sched_switch ./myapp

# Measure wakeup latency distribution
bpftrace -e '
tracepoint:sched:sched_wakeup /comm == "myapp"/ {
    @ts[tid] = nsecs;
}
tracepoint:sched:sched_switch /args->next_comm == "myapp"/ {
    if (@ts[args->next_pid]) {
        @wakeup_lat = hist(nsecs - @ts[args->next_pid]);
        delete(@ts[args->next_pid]);
    }
}'
```

### 18.2 Off-CPU Analysis

```bash
# See what tasks are blocked on (I/O, locks, etc.)
offcputime-bpfcc -p <pid> 10

# Or with bpftrace
bpftrace -e '
tracepoint:sched:sched_switch /args->prev_pid == <pid>/ {
    @ts = nsecs;
}
tracepoint:sched:sched_switch /args->next_pid == <pid>/ {
    @offcpu = hist(nsecs - @ts);
}'
```

### 18.3 Flame Graphs for Scheduler

```bash
# CPU flame graph
perf record -F 99 -a -g -- sleep 30
perf script | ./stackcollapse-perf.pl | ./flamegraph.pl > cpu.svg

# Off-CPU flame graph
bpftrace -e 'tracepoint:sched:sched_switch { @[ustack] = count(); }' \
    -c ./myapp | ./flamegraph.pl > offcpu.svg
```

### 18.4 `cyclictest` — RT Latency

```bash
# Measure scheduling latency for RT tasks
cyclictest --mlockall --smp --priority=99 --interval=200 --distance=0 \
    --duration=60 --histogram=400 --histfile=hist.txt

# Plot histogram
./plot-latency.sh hist.txt
```

---

## 19. C Implementations

### 19.1 User-Space CFS Simulator

**File:** `cfs_sim.c`

```c
// cfs_sim.c - User-space simulation of CFS core concepts
// Compile: gcc -O2 -o cfs_sim cfs_sim.c
// Run:     ./cfs_sim

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>

#define NICE_0_LOAD     1024ULL
#define MAX_TASKS       16
#define SIM_TICKS       100
#define TICK_NS         4000000ULL  // 4ms tick
#define SCHED_LAT_NS    24000000ULL // 24ms target latency

// Weight table (nice -20 to +19)
static const uint64_t prio_to_weight[40] = {
    88761, 71755, 56483, 46273, 36291,
    29154, 23254, 18705, 14949, 11916,
     9548,  7620,  6100,  4904,  3906,
     3121,  2501,  1991,  1586,  1277,
     1024,   820,   655,   526,   423,
      335,   272,   215,   172,   137,
      110,    87,    70,    56,    45,
       36,    29,    23,    18,    15,
};

typedef struct Task {
    int      id;
    int      nice;           // -20 to +19
    uint64_t weight;
    uint64_t vruntime;       // virtual runtime (ns, normalized)
    uint64_t exec_start;     // wall clock when started this slice
    uint64_t sum_exec;       // total wall clock cpu time
    uint64_t nr_switches;
    int      runnable;
} Task;

// Simple min-heap as our "red-black tree" substitute
typedef struct RunQueue {
    Task    *heap[MAX_TASKS];
    int      size;
    uint64_t min_vruntime;
    uint64_t total_weight;
    uint64_t clock;          // virtual clock
} RunQueue;

static int heap_less(Task *a, Task *b) {
    return a->vruntime < b->vruntime;
}

static void heap_push(RunQueue *rq, Task *t) {
    int i = rq->size++;
    rq->heap[i] = t;
    // bubble up
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (heap_less(rq->heap[i], rq->heap[parent])) {
            Task *tmp = rq->heap[i];
            rq->heap[i] = rq->heap[parent];
            rq->heap[parent] = tmp;
            i = parent;
        } else break;
    }
}

static Task *heap_pop(RunQueue *rq) {
    if (rq->size == 0) return NULL;
    Task *top = rq->heap[0];
    rq->heap[0] = rq->heap[--rq->size];
    // bubble down
    int i = 0;
    while (1) {
        int left = 2*i+1, right = 2*i+2, smallest = i;
        if (left  < rq->size && heap_less(rq->heap[left],  rq->heap[smallest])) smallest = left;
        if (right < rq->size && heap_less(rq->heap[right], rq->heap[smallest])) smallest = right;
        if (smallest == i) break;
        Task *tmp = rq->heap[i];
        rq->heap[i] = rq->heap[smallest];
        rq->heap[smallest] = tmp;
        i = smallest;
    }
    return top;
}

static uint64_t calc_vruntime_delta(uint64_t wall_delta, uint64_t weight) {
    // vruntime_delta = wall_delta * NICE_0_LOAD / weight
    return (wall_delta * NICE_0_LOAD) / weight;
}

static uint64_t calc_timeslice(RunQueue *rq, Task *t) {
    // slice = sched_latency * (task_weight / total_weight)
    if (rq->total_weight == 0) return SCHED_LAT_NS;
    uint64_t slice = (SCHED_LAT_NS * t->weight) / rq->total_weight;
    // clamp to minimum granularity
    if (slice < 1000000ULL) slice = 1000000ULL;  // 1ms min
    return slice;
}

static void update_min_vruntime(RunQueue *rq) {
    if (rq->size > 0)
        rq->min_vruntime = rq->heap[0]->vruntime;
}

static void task_add(RunQueue *rq, Task *t) {
    t->runnable = 1;
    // Place new task at current min_vruntime to avoid starvation bonus
    if (t->vruntime < rq->min_vruntime)
        t->vruntime = rq->min_vruntime;
    rq->total_weight += t->weight;
    heap_push(rq, t);
}

static void simulate(void) {
    RunQueue rq = {0};
    Task tasks[5];
    
    // Setup tasks with different nice values
    int nices[] = {0, 0, -5, 5, 10};
    for (int i = 0; i < 5; i++) {
        tasks[i] = (Task){
            .id       = i,
            .nice     = nices[i],
            .weight   = prio_to_weight[20 + nices[i]],
            .vruntime = 0,
        };
        task_add(&rq, &tasks[i]);
    }
    update_min_vruntime(&rq);

    printf("CFS Simulation — %d ticks, %llu ms each\n",
           SIM_TICKS, (unsigned long long)(TICK_NS / 1000000));
    printf("%-6s %-8s %-10s %-14s %-12s %-10s\n",
           "Tick", "Task", "Nice", "vRuntime(ms)", "CPU(ms)", "Switches");
    printf("%s\n", "------------------------------------------------------------");

    Task *current = NULL;
    uint64_t current_start = 0;
    uint64_t current_slice = 0;

    for (int tick = 0; tick < SIM_TICKS; tick++) {
        uint64_t now = (uint64_t)tick * TICK_NS;

        // Account for current task's execution
        if (current) {
            uint64_t wall_delta = now - current_start;
            uint64_t vdelta = calc_vruntime_delta(wall_delta, current->weight);
            current->vruntime  += vdelta;
            current->sum_exec  += wall_delta;

            // Check if time slice expired
            int preempt = (now - current_start) >= current_slice;

            if (preempt) {
                task_add(&rq, current);
                update_min_vruntime(&rq);
                current = NULL;
            }
        }

        // Pick next task if needed
        if (!current && rq.size > 0) {
            current = heap_pop(&rq);
            current_start = now;
            current_slice = calc_timeslice(&rq, current);
            current->nr_switches++;
        }

        if (current && tick % 10 == 0) {
            printf("%-6d %-8d %-10d %-14.3f %-12.3f %-10llu\n",
                   tick,
                   current->id,
                   current->nice,
                   (double)current->vruntime / 1e6,
                   (double)current->sum_exec / 1e6,
                   (unsigned long long)current->nr_switches);
        }
    }

    printf("\n--- Final Stats ---\n");
    printf("%-8s %-10s %-10s %-10s %-12s\n",
           "Task", "Nice", "Weight", "CPU(ms)", "Switches");
    for (int i = 0; i < 5; i++) {
        printf("%-8d %-10d %-10llu %-10.3f %-12llu\n",
               tasks[i].id,
               tasks[i].nice,
               (unsigned long long)tasks[i].weight,
               (double)tasks[i].sum_exec / 1e6,
               (unsigned long long)tasks[i].nr_switches);
    }
}

int main(void) {
    simulate();
    return 0;
}
```

---

### 19.2 Scheduling Policy Manager

**File:** `sched_policy.c`

```c
// sched_policy.c - Complete scheduling policy manipulation utility
// Compile: gcc -O2 -o sched_policy sched_policy.c
// Run:     sudo ./sched_policy (requires CAP_SYS_NICE for RT)

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sched.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/resource.h>
#include <time.h>
#include <pthread.h>

// sched_attr for SCHED_DEADLINE (may not be in all headers)
struct sched_attr {
    uint32_t size;
    uint32_t sched_policy;
    uint64_t sched_flags;
    int32_t  sched_nice;
    uint32_t sched_priority;
    uint64_t sched_runtime;
    uint64_t sched_deadline;
    uint64_t sched_period;
    uint32_t sched_util_min;
    uint32_t sched_util_max;
};

static int sched_setattr(pid_t pid, const struct sched_attr *attr, unsigned int flags) {
    return syscall(SYS_sched_setattr, pid, attr, flags);
}

static int sched_getattr(pid_t pid, struct sched_attr *attr,
                          unsigned int size, unsigned int flags) {
    return syscall(SYS_sched_getattr, pid, attr, size, flags);
}

static const char *policy_name(int policy) {
    switch (policy) {
        case SCHED_NORMAL:   return "SCHED_NORMAL";
        case SCHED_FIFO:     return "SCHED_FIFO";
        case SCHED_RR:       return "SCHED_RR";
        case SCHED_BATCH:    return "SCHED_BATCH";
        case SCHED_IDLE:     return "SCHED_IDLE";
        case SCHED_DEADLINE: return "SCHED_DEADLINE";
        default:             return "UNKNOWN";
    }
}

static void print_sched_info(pid_t pid) {
    struct sched_attr attr = { .size = sizeof(attr) };
    if (sched_getattr(pid, &attr, sizeof(attr), 0) < 0) {
        perror("sched_getattr");
        return;
    }
    printf("PID %d scheduling info:\n", pid);
    printf("  Policy:   %s (%u)\n", policy_name(attr.sched_policy), attr.sched_policy);
    printf("  Priority: %u\n",  attr.sched_priority);
    printf("  Nice:     %d\n",  attr.sched_nice);
    if (attr.sched_policy == SCHED_DEADLINE) {
        printf("  Runtime:  %llu ns (%.3f ms)\n",
               (unsigned long long)attr.sched_runtime,
               attr.sched_runtime / 1e6);
        printf("  Deadline: %llu ns (%.3f ms)\n",
               (unsigned long long)attr.sched_deadline,
               attr.sched_deadline / 1e6);
        printf("  Period:   %llu ns (%.3f ms)\n",
               (unsigned long long)attr.sched_period,
               attr.sched_period / 1e6);
    }
}

// Demonstrate CPU affinity
static void demo_affinity(void) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(0, &set);

    if (sched_setaffinity(0, sizeof(set), &set) < 0) {
        perror("sched_setaffinity");
        return;
    }
    printf("Pinned to CPU 0\n");

    // Read back
    CPU_ZERO(&set);
    sched_getaffinity(0, sizeof(set), &set);
    printf("Affinity mask: ");
    for (int i = 0; i < CPU_SETSIZE; i++) {
        if (CPU_ISSET(i, &set)) printf("%d ", i);
    }
    printf("\n");

    // Reset to all CPUs
    for (int i = 0; i < sysconf(_SC_NPROCESSORS_ONLN); i++)
        CPU_SET(i, &set);
    sched_setaffinity(0, sizeof(set), &set);
}

// Measure scheduler wakeup latency
#define ITERATIONS 10000
static void measure_wakeup_latency(void) {
    struct timespec t1, t2;
    long long latencies[ITERATIONS];
    pthread_t tid;
    pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
    pthread_cond_t  cond  = PTHREAD_COND_INITIALIZER;
    volatile int ready = 0;

    struct thread_args { pthread_mutex_t *m; pthread_cond_t *c; volatile int *r; };
    struct thread_args args = {&mutex, &cond, &ready};

    // Simple latency via nanosleep round-trip
    printf("\nMeasuring nanosleep wakeup latency (%d iterations)...\n", ITERATIONS);
    
    long long sum = 0, min_lat = 1e18, max_lat = 0;
    struct timespec sleep_time = {0, 0}; // minimal sleep
    
    for (int i = 0; i < ITERATIONS; i++) {
        clock_gettime(CLOCK_MONOTONIC, &t1);
        nanosleep(&sleep_time, NULL);
        clock_gettime(CLOCK_MONOTONIC, &t2);
        
        long long lat = (t2.tv_sec - t1.tv_sec) * 1000000000LL
                      + (t2.tv_nsec - t1.tv_nsec);
        latencies[i] = lat;
        sum += lat;
        if (lat < min_lat) min_lat = lat;
        if (lat > max_lat) max_lat = lat;
    }

    // Sort for percentiles
    for (int i = 0; i < ITERATIONS; i++) {
        for (int j = i+1; j < ITERATIONS; j++) {
            if (latencies[j] < latencies[i]) {
                long long tmp = latencies[i];
                latencies[i] = latencies[j];
                latencies[j] = tmp;
            }
        }
    }

    printf("  Avg:  %8.3f µs\n", (double)sum / ITERATIONS / 1000.0);
    printf("  Min:  %8.3f µs\n", min_lat / 1000.0);
    printf("  P50:  %8.3f µs\n", latencies[ITERATIONS/2] / 1000.0);
    printf("  P99:  %8.3f µs\n", latencies[ITERATIONS*99/100] / 1000.0);
    printf("  P999: %8.3f µs\n", latencies[ITERATIONS*999/1000] / 1000.0);
    printf("  Max:  %8.3f µs\n", max_lat / 1000.0);
}

// Set SCHED_DEADLINE and run a periodic task
static void *deadline_thread(void *arg) {
    struct sched_attr attr = {
        .size           = sizeof(struct sched_attr),
        .sched_policy   = SCHED_DEADLINE,
        .sched_runtime  = 2 * 1000 * 1000,  // 2ms runtime
        .sched_period   = 10 * 1000 * 1000, // 10ms period
        .sched_deadline = 10 * 1000 * 1000, // 10ms deadline
    };

    if (sched_setattr(0, &attr, 0) < 0) {
        perror("sched_setattr DEADLINE");
        return NULL;
    }

    printf("\nDEADLINE thread running (PID %d):\n", (int)syscall(SYS_gettid));
    print_sched_info(syscall(SYS_gettid));

    for (int i = 0; i < 5; i++) {
        struct timespec start, end;
        clock_gettime(CLOCK_MONOTONIC, &start);

        // Simulate 1ms of work
        volatile long x = 0;
        struct timespec work_end;
        do {
            x++;
            clock_gettime(CLOCK_MONOTONIC, &work_end);
        } while ((work_end.tv_nsec - start.tv_nsec +
                  (work_end.tv_sec - start.tv_sec) * 1e9) < 1e6);

        printf("  Period %d: work done\n", i);
        
        // Yield to trigger period completion (DEADLINE tasks use sched_yield)
        sched_yield();
    }
    return NULL;
}

int main(int argc, char *argv[]) {
    printf("=== Linux Scheduler Policy Demo ===\n\n");
    
    // Show current process info
    printf("Current process:\n");
    print_sched_info(getpid());

    // Demo: set nice value
    printf("\nSetting nice value to -5:\n");
    setpriority(PRIO_PROCESS, 0, -5);
    printf("Nice value: %d\n", getpriority(PRIO_PROCESS, 0));
    setpriority(PRIO_PROCESS, 0, 0); // reset

    // Demo: affinity
    printf("\nCPU Affinity Demo:\n");
    demo_affinity();

    // Demo: wakeup latency
    measure_wakeup_latency();

    // Demo: DEADLINE thread (requires CAP_SYS_NICE or root)
    if (geteuid() == 0) {
        pthread_t tid;
        pthread_create(&tid, NULL, deadline_thread, NULL);
        pthread_join(tid, NULL);
    } else {
        printf("\nSkipping DEADLINE demo (requires root/CAP_SYS_NICE)\n");
    }

    return 0;
}
```

---

### 19.3 Run Queue Length Monitor (BPF-less, /proc-based)

**File:** `rqlen_monitor.c`

```c
// rqlen_monitor.c - Monitor CPU run queue lengths via /proc/schedstat
// Compile: gcc -O2 -o rqlen_monitor rqlen_monitor.c
// Run:     ./rqlen_monitor 1 (sample every 1 second)

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

#define MAX_CPUS 256

typedef struct {
    unsigned long long yld_count;       // sched_yield() calls
    unsigned long long yld_act_count;   // yield caused actual reschedule
    unsigned long long sched_count;     // scheduler calls
    unsigned long long sched_goidle;    // went idle
    unsigned long long ttwu_count;      // try_to_wake_up calls
    unsigned long long ttwu_local;      // same-CPU wakeups
    unsigned long long rq_cpu_time;     // cpu time on runqueue
    unsigned long long run_delay;       // time waiting in runqueue
    unsigned long long pcount;          // # of tasks
} CpuSchedStat;

typedef struct {
    int           ncpus;
    CpuSchedStat  stats[MAX_CPUS];
} SchedStat;

static int read_schedstat(SchedStat *out) {
    FILE *f = fopen("/proc/schedstat", "r");
    if (!f) { perror("fopen /proc/schedstat"); return -1; }

    char line[512];
    int cpu_idx = 0;
    out->ncpus = 0;

    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "cpu", 3) != 0) continue;
        if (cpu_idx >= MAX_CPUS) break;

        CpuSchedStat *s = &out->stats[cpu_idx];
        int n = sscanf(line, "cpu%*d %llu %llu %llu %llu %llu %llu %llu %llu %llu",
                       &s->yld_count, &s->yld_act_count,
                       &s->sched_count, &s->sched_goidle,
                       &s->ttwu_count, &s->ttwu_local,
                       &s->rq_cpu_time, &s->run_delay,
                       &s->pcount);
        if (n >= 7) {
            cpu_idx++;
            out->ncpus = cpu_idx;
        }
    }
    fclose(f);
    return 0;
}

// Read per-CPU load average from /proc/stat for utilization
static double read_cpu_util(int cpu) {
    FILE *f = fopen("/proc/stat", "r");
    if (!f) return -1.0;

    char line[256];
    int target = cpu + 1; // line 0 = "cpu  " (aggregate), line 1 = cpu0
    int lineno = 0;
    double util = -1.0;
    
    while (fgets(line, sizeof(line), f)) {
        if (lineno == target && strncmp(line, "cpu", 3) == 0) {
            unsigned long long user, nice, sys, idle, iowait, irq, softirq;
            sscanf(line, "cpu%*d %llu %llu %llu %llu %llu %llu %llu",
                   &user, &nice, &sys, &idle, &iowait, &irq, &softirq);
            unsigned long long total = user+nice+sys+idle+iowait+irq+softirq;
            unsigned long long busy  = user+nice+sys+irq+softirq;
            util = (double)busy / total * 100.0;
            break;
        }
        lineno++;
    }
    fclose(f);
    return util;
}

// Read per-task schedstat from /proc/<pid>/schedstat
static void print_top_tasks(int top_n) {
    // Quick scan of /proc for high-rundelay tasks
    printf("\nTop %d tasks by run queue delay:\n", top_n);
    printf("%-8s %-20s %-15s %-15s\n", "PID", "COMM", "CPU(ms)", "RQDelay(ms)");

    // NOTE: In production, iterate /proc/*/schedstat
    // This is simplified — just show the concept
    FILE *f;
    char path[64], comm[32], line[256];
    
    typedef struct { int pid; char comm[32]; long long run, delay; } TaskInfo;
    TaskInfo best[16] = {0};
    int nb = 0;

    // Read /proc/*/task/*/schedstat for all threads
    // For brevity, just read main threads
    for (int pid = 1; pid < 65536; pid++) {
        snprintf(path, sizeof(path), "/proc/%d/schedstat", pid);
        f = fopen(path, "r");
        if (!f) continue;
        
        long long cpu_time, run_delay, timeslices;
        if (fscanf(f, "%lld %lld %lld", &cpu_time, &run_delay, &timeslices) == 3) {
            if (run_delay > 0) {
                // Read comm
                char comm_path[64];
                snprintf(comm_path, sizeof(comm_path), "/proc/%d/comm", pid);
                FILE *cf = fopen(comm_path, "r");
                char comm_buf[32] = "?";
                if (cf) { fscanf(cf, "%31s", comm_buf); fclose(cf); }

                if (nb < 16) {
                    best[nb++] = (TaskInfo){pid, "", cpu_time, run_delay};
                    strncpy(best[nb-1].comm, comm_buf, 31);
                } else {
                    // Replace minimum
                    int min_i = 0;
                    for (int i = 1; i < 16; i++)
                        if (best[i].delay < best[min_i].delay) min_i = i;
                    if (run_delay > best[min_i].delay) {
                        best[min_i] = (TaskInfo){pid, "", cpu_time, run_delay};
                        strncpy(best[min_i].comm, comm_buf, 31);
                    }
                }
            }
        }
        fclose(f);
    }

    // Sort by delay descending (simple)
    for (int i = 0; i < nb; i++)
        for (int j = i+1; j < nb; j++)
            if (best[j].delay > best[i].delay) {
                TaskInfo tmp = best[i]; best[i] = best[j]; best[j] = tmp;
            }

    int show = nb < top_n ? nb : top_n;
    for (int i = 0; i < show; i++) {
        printf("%-8d %-20s %-15.3f %-15.3f\n",
               best[i].pid, best[i].comm,
               best[i].run / 1e6,
               best[i].delay / 1e6);
    }
}

int main(int argc, char *argv[]) {
    int interval = 1;
    if (argc > 1) interval = atoi(argv[1]);

    printf("Run Queue Monitor (interval=%ds)\n", interval);
    printf("%-6s %-15s %-15s %-15s %-12s\n",
           "CPU", "Sched/s", "Wakeups/s", "RQDelay/s(ms)", "Util%");

    SchedStat prev = {0}, curr = {0};
    read_schedstat(&prev);
    sleep(interval);

    int iter = 0;
    while (1) {
        read_schedstat(&curr);
        printf("\n--- Iteration %d ---\n", ++iter);
        printf("%-6s %-15s %-15s %-15s\n",
               "CPU", "Sched/s", "Wakeups/s", "RQDelay/s(ms)");

        for (int i = 0; i < curr.ncpus && i < prev.ncpus; i++) {
            CpuSchedStat *c = &curr.stats[i];
            CpuSchedStat *p = &prev.stats[i];
            
            long long dsched  = c->sched_count - p->sched_count;
            long long dwakeup = c->ttwu_count  - p->ttwu_count;
            long long ddelay  = c->run_delay   - p->run_delay;

            printf("%-6d %-15lld %-15lld %-15.3f\n",
                   i, dsched, dwakeup, (double)ddelay / 1e6 / interval);
        }

        print_top_tasks(5);

        prev = curr;
        sleep(interval);
    }
    return 0;
}
```

---

### 19.4 Priority Inversion Demo

**File:** `priority_inversion.c`

```c
// priority_inversion.c - Demonstrate priority inversion and its fix
// Compile: gcc -O2 -lpthread -o priority_inversion priority_inversion.c
// Run:     sudo ./priority_inversion

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>
#include <sched.h>
#include <sys/syscall.h>

static pthread_mutex_t      g_mutex;
static volatile int         g_shared = 0;
static volatile int         g_high_done = 0;

static long long now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

static void spin_ms(int ms) {
    long long end = now_ns() + ms * 1000000LL;
    while (now_ns() < end) asm volatile("pause");
}

static void set_rt(int prio) {
    struct sched_param sp = { .sched_priority = prio };
    if (sched_setscheduler(0, SCHED_FIFO, &sp) < 0)
        perror("sched_setscheduler (need root)");
}

// LOW priority thread: acquires lock, holds for a long time
static void *low_thread(void *arg) {
    set_rt(10);
    pid_t tid = syscall(SYS_gettid);
    printf("[LOW  tid=%d prio=10] Acquiring lock...\n", tid);
    pthread_mutex_lock(&g_mutex);
    printf("[LOW  tid=%d] Lock acquired, doing 50ms work\n", tid);
    spin_ms(50);
    g_shared = 1;
    printf("[LOW  tid=%d] Releasing lock\n", tid);
    pthread_mutex_unlock(&g_mutex);
    return NULL;
}

// MEDIUM priority thread: no lock, just burns CPU and starves LOW
static void *medium_thread(void *arg) {
    usleep(5000); // let LOW acquire lock first
    set_rt(50);
    pid_t tid = syscall(SYS_gettid);
    printf("[MED  tid=%d prio=50] Running, burning CPU for 100ms...\n", tid);
    spin_ms(100);
    printf("[MED  tid=%d] Done\n", tid);
    return NULL;
}

// HIGH priority thread: needs the lock
static void *high_thread(void *arg) {
    usleep(10000); // let LOW acquire lock, MED start running
    set_rt(90);
    pid_t tid = syscall(SYS_gettid);
    long long t0 = now_ns();
    printf("[HIGH tid=%d prio=90] Trying to acquire lock...\n", tid);
    pthread_mutex_lock(&g_mutex);
    long long t1 = now_ns();
    printf("[HIGH tid=%d] Lock acquired after %.2f ms (g_shared=%d)\n",
           tid, (t1-t0)/1e6, g_shared);
    pthread_mutex_unlock(&g_mutex);
    g_high_done = 1;
    return NULL;
}

static void run_scenario(int use_pi) {
    pthread_mutexattr_t attr;
    pthread_mutexattr_init(&attr);
    if (use_pi) {
        pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT);
        printf("\n=== WITH Priority Inheritance ===\n");
    } else {
        printf("\n=== WITHOUT Priority Inheritance (classic inversion) ===\n");
    }
    pthread_mutex_init(&g_mutex, &attr);
    pthread_mutexattr_destroy(&attr);

    g_shared = 0;
    g_high_done = 0;

    pthread_t tlow, tmed, thigh;
    long long t_start = now_ns();

    pthread_create(&tlow,  NULL, low_thread,    NULL);
    pthread_create(&tmed,  NULL, medium_thread, NULL);
    pthread_create(&thigh, NULL, high_thread,   NULL);

    pthread_join(tlow,  NULL);
    pthread_join(tmed,  NULL);
    pthread_join(thigh, NULL);

    long long t_end = now_ns();
    printf("Total scenario time: %.2f ms\n", (t_end - t_start) / 1e6);
    pthread_mutex_destroy(&g_mutex);
}

int main(void) {
    if (geteuid() != 0) {
        fprintf(stderr, "Run as root for RT scheduling demo\n");
        fprintf(stderr, "Without root, threads run at normal priority (less dramatic)\n");
    }

    run_scenario(0); // classic priority inversion
    sleep(1);
    run_scenario(1); // priority inheritance fix

    return 0;
}
```

---

## 20. Rust Implementations

### 20.1 Scheduler-Aware Thread Pool

**File:** `scheduler_threadpool/src/main.rs`

```rust
//! scheduler_threadpool — A scheduler-aware thread pool with:
//! - CPU affinity pinning
//! - Priority control
//! - Wakeup latency measurement
//! - Work-stealing queue
//!
//! Cargo.toml:
//! [dependencies]
//! libc = "0.2"
//! crossbeam-deque = "0.8"
//! parking_lot = "0.12"
//!
//! Run: cargo run --release

use std::{
    sync::{
        Arc,
        atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering},
    },
    thread,
    time::{Duration, Instant},
};
use crossbeam_deque::{Injector, Stealer, Worker};
use parking_lot::Mutex;

// ─── libc bindings ────────────────────────────────────────────────────────────

#[allow(dead_code)]
mod sched_sys {
    use libc::{c_int, pid_t};

    pub const SCHED_NORMAL:   c_int = 0;
    pub const SCHED_FIFO:     c_int = 1;
    pub const SCHED_RR:       c_int = 2;
    pub const SCHED_BATCH:    c_int = 3;
    pub const SCHED_IDLE:     c_int = 5;
    pub const SCHED_DEADLINE: c_int = 6;

    #[repr(C)]
    pub struct SchedParam {
        pub sched_priority: c_int,
    }

    extern "C" {
        pub fn sched_setscheduler(pid: pid_t, policy: c_int, param: *const SchedParam) -> c_int;
        pub fn sched_getscheduler(pid: pid_t) -> c_int;
        pub fn sched_setaffinity(pid: pid_t, cpusetsize: libc::size_t,
                                  mask: *const libc::cpu_set_t) -> c_int;
        pub fn sched_getaffinity(pid: pid_t, cpusetsize: libc::size_t,
                                  mask: *mut libc::cpu_set_t) -> c_int;
        pub fn sched_yield() -> c_int;
        pub fn gettid() -> pid_t;
    }
}

// ─── CPU Affinity Helper ───────────────────────────────────────────────────────

fn pin_to_cpu(cpu: usize) -> Result<(), std::io::Error> {
    unsafe {
        let mut set = std::mem::zeroed::<libc::cpu_set_t>();
        libc::CPU_SET(cpu, &mut set);
        let ret = sched_sys::sched_setaffinity(
            0,
            std::mem::size_of::<libc::cpu_set_t>(),
            &set,
        );
        if ret != 0 {
            return Err(std::io::Error::last_os_error());
        }
    }
    Ok(())
}

fn get_online_cpus() -> usize {
    unsafe { libc::sysconf(libc::_SC_NPROCESSORS_ONLN) as usize }
}

// ─── Work Item ────────────────────────────────────────────────────────────────

type Task = Box<dyn FnOnce() + Send + 'static>;

// ─── Per-Worker State ─────────────────────────────────────────────────────────

struct WorkerState {
    id:            usize,
    local:         Worker<Task>,
    stealers:      Vec<Stealer<Task>>,
    injector:      Arc<Injector<Task>>,
    shutdown:      Arc<AtomicBool>,
    tasks_done:    Arc<AtomicU64>,
    steal_count:   Arc<AtomicU64>,
}

impl WorkerState {
    fn find_task(&self) -> Option<Task> {
        // 1. Try local queue first (cache-warm)
        self.local.pop().or_else(|| {
            // 2. Try stealing from others
            for stealer in &self.stealers {
                if let crossbeam_deque::Steal::Success(t) = stealer.steal() {
                    self.steal_count.fetch_add(1, Ordering::Relaxed);
                    return Some(t);
                }
            }
            // 3. Try global injector
            loop {
                match self.injector.steal_batch_and_pop(&self.local) {
                    crossbeam_deque::Steal::Success(t) => return Some(t),
                    crossbeam_deque::Steal::Empty      => return None,
                    crossbeam_deque::Steal::Retry      => continue,
                }
            }
        })
    }

    fn run(self, cpu_pin: Option<usize>) {
        if let Some(cpu) = cpu_pin {
            if let Err(e) = pin_to_cpu(cpu) {
                eprintln!("Worker {} could not pin to CPU {}: {}", self.id, cpu, e);
            } else {
                println!("Worker {} pinned to CPU {}", self.id, cpu);
            }
        }

        while !self.shutdown.load(Ordering::Acquire) {
            if let Some(task) = self.find_task() {
                task();
                self.tasks_done.fetch_add(1, Ordering::Relaxed);
            } else {
                // Exponential backoff before yielding
                std::hint::spin_loop();
                unsafe { sched_sys::sched_yield(); }
                thread::sleep(Duration::from_micros(10));
            }
        }
        // Drain remaining tasks
        while let Some(task) = self.find_task() {
            task();
            self.tasks_done.fetch_add(1, Ordering::Relaxed);
        }
    }
}

// ─── Thread Pool ──────────────────────────────────────────────────────────────

pub struct SchedulerAwarePool {
    injector:    Arc<Injector<Task>>,
    handles:     Vec<thread::JoinHandle<()>>,
    shutdown:    Arc<AtomicBool>,
    tasks_done:  Arc<AtomicU64>,
    steal_count: Arc<AtomicU64>,
    n_workers:   usize,
}

impl SchedulerAwarePool {
    pub fn new(n_workers: usize, pin_cpus: bool) -> Self {
        let injector    = Arc::new(Injector::new());
        let shutdown    = Arc::new(AtomicBool::new(false));
        let tasks_done  = Arc::new(AtomicU64::new(0));
        let steal_count = Arc::new(AtomicU64::new(0));

        // Create all worker queues upfront so we can share stealers
        let mut workers: Vec<Worker<Task>> = (0..n_workers)
            .map(|_| Worker::new_fifo())
            .collect();

        let stealers: Vec<Stealer<Task>> = workers.iter()
            .map(|w| w.stealer())
            .collect();

        let mut handles = Vec::with_capacity(n_workers);
        let ncpus = get_online_cpus();

        for id in 0..n_workers {
            let local    = workers.remove(0);
            // Each worker can steal from all others
            let my_stealers: Vec<_> = stealers.iter()
                .enumerate()
                .filter(|(i, _)| *i != id)
                .map(|(_, s)| s.clone())
                .collect();

            let state = WorkerState {
                id,
                local,
                stealers:    my_stealers,
                injector:    Arc::clone(&injector),
                shutdown:    Arc::clone(&shutdown),
                tasks_done:  Arc::clone(&tasks_done),
                steal_count: Arc::clone(&steal_count),
            };

            let cpu = if pin_cpus { Some(id % ncpus) } else { None };

            handles.push(thread::Builder::new()
                .name(format!("pool-worker-{}", id))
                .spawn(move || state.run(cpu))
                .expect("thread spawn failed"));
        }

        Self { injector, handles, shutdown, tasks_done, steal_count, n_workers }
    }

    pub fn submit<F: FnOnce() + Send + 'static>(&self, f: F) {
        self.injector.push(Box::new(f));
    }

    pub fn stats(&self) -> (u64, u64) {
        (
            self.tasks_done.load(Ordering::Relaxed),
            self.steal_count.load(Ordering::Relaxed),
        )
    }

    pub fn shutdown(self) {
        self.shutdown.store(true, Ordering::Release);
        for h in self.handles {
            h.join().ok();
        }
    }
}

// ─── Wakeup Latency Benchmark ─────────────────────────────────────────────────

fn measure_wakeup_latency(iterations: usize) -> Vec<u128> {
    let mut latencies = Vec::with_capacity(iterations);
    
    for _ in 0..iterations {
        let start = Instant::now();
        // Minimal sleep → measures OS wakeup overhead
        thread::sleep(Duration::ZERO);
        latencies.push(start.elapsed().as_nanos());
    }
    latencies
}

fn percentile(sorted: &[u128], pct: f64) -> u128 {
    let idx = ((sorted.len() as f64) * pct / 100.0) as usize;
    sorted[idx.min(sorted.len() - 1)]
}

// ─── CFS Virtual Runtime Tracker ──────────────────────────────────────────────

/// Tracks vruntime in userspace for analysis/testing purposes.
/// Mirrors the kernel's fixed-point arithmetic.
#[derive(Debug, Clone)]
pub struct VruntimeTracker {
    pub nice:     i32,
    pub weight:   u64,
    pub vruntime: u64,   // nanoseconds (normalized)
    pub sum_exec: u64,
}

const NICE_0_LOAD: u64 = 1024;
const PRIO_TO_WEIGHT: [u64; 40] = [
    88761, 71755, 56483, 46273, 36291,
    29154, 23254, 18705, 14949, 11916,
     9548,  7620,  6100,  4904,  3906,
     3121,  2501,  1991,  1586,  1277,
     1024,   820,   655,   526,   423,
      335,   272,   215,   172,   137,
      110,    87,    70,    56,    45,
       36,    29,    23,    18,    15,
];

impl VruntimeTracker {
    pub fn new(nice: i32) -> Self {
        let idx = (nice + 20).clamp(0, 39) as usize;
        Self {
            nice,
            weight: PRIO_TO_WEIGHT[idx],
            vruntime: 0,
            sum_exec: 0,
        }
    }

    /// Account for `wall_ns` nanoseconds of CPU time.
    pub fn account(&mut self, wall_ns: u64) {
        // vruntime_delta = wall_ns * NICE_0_LOAD / weight
        let vdelta = wall_ns.saturating_mul(NICE_0_LOAD) / self.weight;
        self.vruntime  = self.vruntime.saturating_add(vdelta);
        self.sum_exec  = self.sum_exec.saturating_add(wall_ns);
    }

    /// Timeslice for this task given total runqueue weight.
    pub fn timeslice_ns(&self, total_weight: u64, sched_latency_ns: u64) -> u64 {
        if total_weight == 0 { return sched_latency_ns; }
        let slice = (sched_latency_ns * self.weight) / total_weight;
        slice.max(750_000) // 750µs minimum
    }
}

// ─── Mini Scheduler Simulator in Rust ─────────────────────────────────────────

use std::collections::BinaryHeap;
use std::cmp::Reverse;

#[derive(Debug, Eq, PartialEq)]
struct SchedTask {
    vruntime: u64,
    id:       usize,
}

impl Ord for SchedTask {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        // BinaryHeap is max-heap; we want min-vruntime first → Reverse
        other.vruntime.cmp(&self.vruntime)
            .then(other.id.cmp(&self.id))
    }
}
impl PartialOrd for SchedTask {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

fn simulate_cfs(tasks: &mut Vec<VruntimeTracker>, ticks: usize, tick_ns: u64) {
    let sched_lat = 24_000_000u64; // 24ms
    let n = tasks.len();

    // Min-heap by vruntime
    let mut heap: BinaryHeap<SchedTask> = tasks.iter().enumerate()
        .map(|(id, t)| SchedTask { vruntime: t.vruntime, id })
        .collect();

    let mut min_vruntime = 0u64;

    for tick in 0..ticks {
        let total_weight: u64 = tasks.iter().map(|t| t.weight).sum();

        // Pick task with minimum vruntime
        let chosen = match heap.pop() {
            Some(t) => t,
            None    => break,
        };

        let task = &mut tasks[chosen.id];
        let slice = task.timeslice_ns(total_weight, sched_lat);
        let run_ns = slice.min(tick_ns);

        task.account(run_ns);

        // Update min_vruntime
        if task.vruntime > min_vruntime { min_vruntime = task.vruntime; }

        heap.push(SchedTask { vruntime: task.vruntime, id: chosen.id });

        if tick % (ticks / 10) == 0 {
            println!("Tick {:4}: task={} nice={:3} vrt={:8.2}ms cpu={:7.2}ms",
                tick, chosen.id, task.nice,
                task.vruntime as f64 / 1e6,
                task.sum_exec as f64 / 1e6);
        }
    }
}

// ─── Main ─────────────────────────────────────────────────────────────────────

fn main() {
    println!("=== Rust Scheduler Demo ===\n");

    // 1. CFS vruntime simulation
    println!("--- CFS Simulation (5 tasks, 1000 ticks, 4ms each) ---");
    let mut tasks: Vec<VruntimeTracker> = vec![-10, 0, 0, 5, 10]
        .into_iter()
        .map(VruntimeTracker::new)
        .collect();
    simulate_cfs(&mut tasks, 1000, 4_000_000);

    println!("\nFinal CPU allocations:");
    let total_cpu: u64 = tasks.iter().map(|t| t.sum_exec).sum();
    for (i, t) in tasks.iter().enumerate() {
        let pct = t.sum_exec as f64 / total_cpu as f64 * 100.0;
        println!("  Task {} (nice={:3}): {:.1}% CPU  weight={}", i, t.nice, pct, t.weight);
    }

    // 2. Wakeup latency
    println!("\n--- Wakeup Latency Benchmark (10000 iterations) ---");
    let mut lats = measure_wakeup_latency(10_000);
    lats.sort_unstable();
    let avg = lats.iter().sum::<u128>() / lats.len() as u128;
    println!("  avg:  {:8.3} µs", avg as f64 / 1000.0);
    println!("  min:  {:8.3} µs", lats[0] as f64 / 1000.0);
    println!("  p50:  {:8.3} µs", percentile(&lats, 50.0) as f64 / 1000.0);
    println!("  p99:  {:8.3} µs", percentile(&lats, 99.0) as f64 / 1000.0);
    println!("  p999: {:8.3} µs", percentile(&lats, 99.9) as f64 / 1000.0);
    println!("  max:  {:8.3} µs", lats[lats.len()-1] as f64 / 1000.0);

    // 3. Thread pool demo
    println!("\n--- Work-Stealing Thread Pool (CPU-pinned, 4 workers) ---");
    let ncpus = get_online_cpus();
    println!("Online CPUs: {}", ncpus);
    let pool = SchedulerAwarePool::new(4, true);

    let counter = Arc::new(AtomicUsize::new(0));
    let start = Instant::now();
    const NJOBS: usize = 100_000;

    for _ in 0..NJOBS {
        let c = Arc::clone(&counter);
        pool.submit(move || {
            // Simulate 1µs of work
            let end = Instant::now() + Duration::from_micros(1);
            while Instant::now() < end { std::hint::spin_loop(); }
            c.fetch_add(1, Ordering::Relaxed);
        });
    }

    // Wait for completion
    while counter.load(Ordering::Relaxed) < NJOBS {
        thread::sleep(Duration::from_millis(10));
    }
    let elapsed = start.elapsed();
    let (done, steals) = pool.stats();
    println!("  Completed {} jobs in {:.2}ms", done, elapsed.as_secs_f64() * 1000.0);
    println!("  Throughput: {:.0} jobs/s", NJOBS as f64 / elapsed.as_secs_f64());
    println!("  Work steals: {}", steals);

    pool.shutdown();
    println!("\nDone.");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vruntime_ordering() {
        let mut lo = VruntimeTracker::new(-10); // higher weight
        let mut hi = VruntimeTracker::new(10);  // lower weight

        let wall = 1_000_000u64; // 1ms
        lo.account(wall);
        hi.account(wall);

        // Low nice (high weight) should accumulate LESS vruntime
        assert!(lo.vruntime < hi.vruntime,
            "nice=-10 vrt={} should be < nice=10 vrt={}", lo.vruntime, hi.vruntime);
    }

    #[test]
    fn test_timeslice_proportional() {
        let lo = VruntimeTracker::new(-10);
        let hi = VruntimeTracker::new(10);
        let total = lo.weight + hi.weight;
        let lat = 24_000_000u64;

        let slice_lo = lo.timeslice_ns(total, lat);
        let slice_hi = hi.timeslice_ns(total, lat);

        // Lower nice gets larger slice
        assert!(slice_lo > slice_hi,
            "nice=-10 slice={} should be > nice=10 slice={}", slice_lo, slice_hi);
        // Together they sum to ≈ sched_latency
        let sum = slice_lo + slice_hi;
        assert!((sum as i64 - lat as i64).abs() < 1000,
            "slices should sum to ~{}: got {}", lat, sum);
    }

    #[test]
    fn test_pool_completes_all_tasks() {
        let pool = SchedulerAwarePool::new(2, false);
        let counter = Arc::new(AtomicUsize::new(0));
        const N: usize = 1000;

        for _ in 0..N {
            let c = Arc::clone(&counter);
            pool.submit(move || { c.fetch_add(1, Ordering::Relaxed); });
        }

        let deadline = Instant::now() + Duration::from_secs(5);
        while counter.load(Ordering::Relaxed) < N && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(1));
        }
        assert_eq!(counter.load(Ordering::Relaxed), N);
        pool.shutdown();
    }

    #[test]
    fn test_weight_table_monotonic() {
        for i in 0..39 {
            assert!(PRIO_TO_WEIGHT[i] > PRIO_TO_WEIGHT[i+1],
                "Weight table should be strictly decreasing");
        }
    }
}
```

---

### 20.2 SCHED_DEADLINE Heartbeat Task

**File:** `deadline_task/src/main.rs`

```rust
//! deadline_task — SCHED_DEADLINE periodic task in Rust
//! Demonstrates: syscall wrappers, period enforcement, jitter measurement
//!
//! Cargo.toml: [dependencies] libc = "0.2"
//! Run: sudo cargo run --release

use std::time::{Duration, Instant};
use std::arch::asm;

#[repr(C)]
struct SchedAttr {
    size:           u32,
    sched_policy:   u32,
    sched_flags:    u64,
    sched_nice:     i32,
    sched_priority: u32,
    sched_runtime:  u64,
    sched_deadline: u64,
    sched_period:   u64,
    sched_util_min: u32,
    sched_util_max: u32,
}

const SCHED_DEADLINE: u32 = 6;
const SYS_SCHED_SETATTR: i64 = 314;
const SYS_GETTID: i64 = 186;

unsafe fn sched_setattr(pid: libc::pid_t, attr: &SchedAttr) -> libc::c_int {
    let ret: i64;
    asm!(
        "syscall",
        in("rax") SYS_SCHED_SETATTR,
        in("rdi") pid as i64,
        in("rsi") attr as *const SchedAttr as i64,
        in("rdx") 0i64,
        out("rcx") _,
        out("r11") _,
        lateout("rax") ret,
        options(nostack),
    );
    ret as libc::c_int
}

unsafe fn gettid() -> libc::pid_t {
    let ret: i64;
    asm!(
        "syscall",
        in("rax") SYS_GETTID,
        out("rcx") _,
        out("r11") _,
        lateout("rax") ret,
        options(nostack),
    );
    ret as libc::pid_t
}

fn set_deadline(runtime_ns: u64, period_ns: u64, deadline_ns: u64) -> Result<(), String> {
    let attr = SchedAttr {
        size:           std::mem::size_of::<SchedAttr>() as u32,
        sched_policy:   SCHED_DEADLINE,
        sched_flags:    0,
        sched_nice:     0,
        sched_priority: 0,
        sched_runtime:  runtime_ns,
        sched_deadline: deadline_ns,
        sched_period:   period_ns,
        sched_util_min: 0,
        sched_util_max: 1024,
    };
    let ret = unsafe { sched_setattr(0, &attr) };
    if ret != 0 {
        Err(format!("sched_setattr failed: errno={}", unsafe { *libc::__errno_location() }))
    } else {
        Ok(())
    }
}

/// Simulate audio callback: 5ms of work, 10ms period
fn audio_callback(period_num: u32) {
    // Simulate DSP work: 2ms
    let end = Instant::now() + Duration::from_millis(2);
    while Instant::now() < end {
        std::hint::spin_loop();
    }
    // In real code: mix audio buffers, apply effects, etc.
}

fn run_periodic_task() {
    let runtime_ns  = 5_000_000u64;  // 5ms budget
    let period_ns   = 10_000_000u64; // 10ms period
    let deadline_ns = 10_000_000u64; // 10ms deadline

    println!("Setting SCHED_DEADLINE: runtime={}ms period={}ms deadline={}ms",
        runtime_ns/1_000_000, period_ns/1_000_000, deadline_ns/1_000_000);

    match set_deadline(runtime_ns, period_ns, deadline_ns) {
        Ok(())   => println!("SCHED_DEADLINE set successfully (TID={})",
                             unsafe { gettid() }),
        Err(e)   => {
            eprintln!("Failed to set DEADLINE: {} (run as root?)", e);
            eprintln!("Running with normal scheduling instead...");
        }
    }

    const PERIODS: u32 = 50;
    let mut jitters_ns: Vec<i64> = Vec::with_capacity(PERIODS as usize);
    let mut period_start = Instant::now();
    let period_dur = Duration::from_nanos(period_ns);

    for i in 0..PERIODS {
        let actual_start = Instant::now();
        let expected_start = period_start;
        let jitter_ns = actual_start.duration_since(expected_start).as_nanos() as i64;
        jitters_ns.push(jitter_ns);

        // Do the actual work
        audio_callback(i);

        // DEADLINE tasks use sched_yield() to signal period completion
        unsafe { libc::sched_yield(); }

        period_start = expected_start + period_dur;

        // If we're behind, catch up
        let now = Instant::now();
        if now < period_start {
            let sleep_dur = period_start.duration_since(now);
            std::thread::sleep(sleep_dur);
        }
    }

    // Analyze jitter
    let mut sorted = jitters_ns.clone();
    sorted.sort_unstable();
    let avg = sorted.iter().sum::<i64>() / sorted.len() as i64;
    let p99_idx = sorted.len() * 99 / 100;

    println!("\n=== Period Jitter Analysis ({} periods) ===", PERIODS);
    println!("  avg:  {:7.3} µs", avg as f64 / 1000.0);
    println!("  min:  {:7.3} µs", sorted[0] as f64 / 1000.0);
    println!("  p50:  {:7.3} µs", sorted[sorted.len()/2] as f64 / 1000.0);
    println!("  p99:  {:7.3} µs", sorted[p99_idx] as f64 / 1000.0);
    println!("  max:  {:7.3} µs", sorted[sorted.len()-1] as f64 / 1000.0);
}

fn main() {
    println!("=== SCHED_DEADLINE Periodic Task Demo ===");
    run_periodic_task();
}
```

---

### 20.3 CPU Affinity & Scheduler Stats Tool

**File:** `sched_inspect/src/main.rs`

```rust
//! sched_inspect — Inspect and control scheduling from Rust
//! Reads /proc/sched_debug, /proc/<pid>/schedstat, affinity

use std::{
    fs,
    path::Path,
    collections::HashMap,
};

#[derive(Debug, Default)]
struct TaskSchedStat {
    pid:          u32,
    comm:         String,
    cpu_time_ns:  u64,
    wait_time_ns: u64,
    timeslices:   u64,
}

fn read_proc_schedstat(pid: u32) -> Option<TaskSchedStat> {
    let path = format!("/proc/{}/schedstat", pid);
    let data = fs::read_to_string(&path).ok()?;
    let comm = fs::read_to_string(format!("/proc/{}/comm", pid))
        .unwrap_or_default()
        .trim()
        .to_string();

    let mut parts = data.split_whitespace();
    let cpu_time_ns  = parts.next()?.parse().ok()?;
    let wait_time_ns = parts.next()?.parse().ok()?;
    let timeslices   = parts.next()?.parse().ok()?;

    Some(TaskSchedStat { pid, comm, cpu_time_ns, wait_time_ns, timeslices })
}

fn read_all_tasks() -> Vec<TaskSchedStat> {
    let mut tasks = Vec::new();
    let proc = Path::new("/proc");

    if let Ok(entries) = fs::read_dir(proc) {
        for entry in entries.flatten() {
            let name = entry.file_name();
            let s = name.to_string_lossy();
            if let Ok(pid) = s.parse::<u32>() {
                if let Some(stat) = read_proc_schedstat(pid) {
                    tasks.push(stat);
                }
            }
        }
    }
    tasks
}

fn read_cpu_affinity(pid: u32) -> String {
    let path = format!("/proc/{}/status", pid);
    if let Ok(data) = fs::read_to_string(&path) {
        for line in data.lines() {
            if line.starts_with("Cpus_allowed_list:") {
                return line.split(':').nth(1).unwrap_or("?").trim().to_string();
            }
        }
    }
    "?".to_string()
}

fn read_sched_policy(pid: u32) -> String {
    let path = format!("/proc/{}/sched", pid);
    if let Ok(data) = fs::read_to_string(&path) {
        for line in data.lines() {
            if line.contains("policy") {
                return line.trim().to_string();
            }
        }
    }
    "unknown".to_string()
}

fn print_top_by_wait(mut tasks: Vec<TaskSchedStat>, top_n: usize) {
    tasks.sort_by(|a, b| b.wait_time_ns.cmp(&a.wait_time_ns));
    println!("\n{:-<80}", "");
    println!("Top {} tasks by run-queue wait time", top_n);
    println!("{:-<80}", "");
    println!("{:>8} {:<20} {:>14} {:>14} {:>10}",
        "PID", "COMM", "CPU(ms)", "Wait(ms)", "Switches");
    println!("{:-<80}", "");
    for t in tasks.iter().take(top_n) {
        println!("{:>8} {:<20} {:>14.3} {:>14.3} {:>10}",
            t.pid, t.comm,
            t.cpu_time_ns  as f64 / 1e6,
            t.wait_time_ns as f64 / 1e6,
            t.timeslices);
    }
}

fn read_system_sched_debug_summary() {
    let path = "/proc/sched_debug";
    if let Ok(data) = fs::read_to_string(path) {
        println!("\n{:-<80}", "");
        println!("System Scheduler Summary (/proc/sched_debug excerpt)");
        println!("{:-<80}", "");
        // Print first 30 lines (scheduler version, CPU info, tunables)
        for line in data.lines().take(40) {
            println!("{}", line);
        }
    }
}

fn read_schedstat_per_cpu() {
    println!("\n{:-<80}", "");
    println!("Per-CPU Scheduler Statistics (/proc/schedstat)");
    println!("{:-<80}", "");
    println!("{:>6} {:>15} {:>15} {:>15}", "CPU", "Sched calls", "Wakeups", "RunDelay(ms)");
    println!("{:-<80}", "");
    
    if let Ok(data) = fs::read_to_string("/proc/schedstat") {
        for line in data.lines() {
            if !line.starts_with("cpu") { continue; }
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 8 { continue; }
            let cpu_label = parts[0];
            // Fields: yld yld_act sched sched_goidle ttwu ttwu_local rq_time run_delay
            let sched_calls: u64 = parts.get(3).and_then(|s| s.parse().ok()).unwrap_or(0);
            let wakeups:     u64 = parts.get(5).and_then(|s| s.parse().ok()).unwrap_or(0);
            let run_delay:   u64 = parts.get(8).and_then(|s| s.parse().ok()).unwrap_or(0);
            println!("{:>6} {:>15} {:>15} {:>15.3}",
                cpu_label, sched_calls, wakeups, run_delay as f64 / 1e6);
        }
    }
}

fn main() {
    println!("=== sched_inspect: Linux Scheduler Inspector ===\n");

    // System-wide summary
    read_system_sched_debug_summary();
    read_schedstat_per_cpu();

    // Per-task analysis
    println!("\nCollecting task schedstats (may take a moment)...");
    let tasks = read_all_tasks();
    println!("Found {} tasks with schedstat", tasks.len());

    print_top_by_wait(tasks, 15);

    // Show current process info
    let pid = std::process::id();
    println!("\n{:-<80}", "");
    println!("Current process (PID {}):", pid);
    println!("  CPU affinity: {}", read_cpu_affinity(pid));
    if let Some(s) = read_proc_schedstat(pid) {
        println!("  CPU time:     {:.3} ms", s.cpu_time_ns  as f64 / 1e6);
        println!("  Wait time:    {:.3} ms", s.wait_time_ns as f64 / 1e6);
        println!("  Timeslices:   {}", s.timeslices);
    }
}
```

---

## 21. Security Considerations

### 21.1 Privilege Escalation via Scheduling

| Risk | Description | Mitigation |
|------|-------------|------------|
| SCHED_FIFO starvation | prio-99 FIFO task starves everything including watchdogs | `sched_rt_runtime_us` throttling; seccomp to block `sched_setscheduler` |
| `setpriority` abuse | Process can nice itself to -20 if it has CAP_SYS_NICE | Restrict via cgroup `cpu.weight`, ulimits |
| CPU pinning abuse | Task pins to a single CPU, causes starvation on that CPU | Limit via cgroup `cpuset` controller |
| SCHED_DEADLINE over-admission | Requesting 100% CPU via deadline parameters | Kernel admission control enforces U ≤ 1 per CPU |
| Kernel sched_debug exposure | `/proc/sched_debug` reveals task addresses (KASLR leak) | `kernel.perf_event_paranoid=2`, restrict /proc access |

### 21.2 Capabilities Required

```
CAP_SYS_NICE:
  - setpriority() to negative nice values
  - sched_setscheduler() for FIFO/RR/DEADLINE
  - sched_setattr() with DEADLINE policy
  - taskset / CPU affinity changes for other processes

Without CAP_SYS_NICE:
  - Can only increase own nice value (not decrease)
  - Cannot set RT scheduling policies
  - Can set own CPU affinity (but not others')
```

### 21.3 Seccomp Filter for Scheduler Syscalls

```c
// Block dangerous scheduler syscalls in sandboxed processes
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>

// Deny: sched_setscheduler, sched_setattr, sched_setparam
// Allow: sched_yield, sched_getscheduler, nanosleep, clock_nanosleep
```

### 21.4 cgroup Containment

```bash
# Create isolated cgroup for untrusted workload
mkdir /sys/fs/cgroup/untrusted
echo "10 100000" > /sys/fs/cgroup/untrusted/cpu.max     # 10% of 1 CPU
echo "0-3"       > /sys/fs/cgroup/untrusted/cpuset.cpus  # CPUs 0-3 only
echo <pid>       > /sys/fs/cgroup/untrusted/cgroup.procs
```

### 21.5 Production Security Checklist

```
☐ sched_rt_runtime_us is set (not -1) — prevents RT task starvation
☐ CAP_SYS_NICE dropped from service user — use capability bounding sets
☐ ulimit -r 0 for non-RT services (max RT priority = 0)
☐ /proc/sched_debug permissions restricted (mode 0400 or securityfs)
☐ cpuset cgroups used to isolate critical vs untrusted workloads
☐ isolcpus + rcu_nocbs configured for latency-critical CPUs
☐ IRQ affinity moved off isolated CPUs
☐ Kernel PREEMPT model matches latency requirements
☐ NUMA binding verified for memory-intensive workloads
☐ cgroup cpu.max set for every container/service (no unbounded CPU)
☐ perf_event_paranoid=2 in production
```

---

## 22. Common Pitfalls & War Stories

### Pitfall 1: cgroup CPU Throttling Causing P99 Spikes

**Symptom:** Average CPU is 30%, but P99 request latency is 500ms.  
**Root cause:** `cpu.max` limit hit, entire cgroup throttled for the period (up to 100ms).  
**Fix:**
```bash
cat /sys/fs/cgroup/myservice/cpu.stat | grep throttled
# nr_throttled: 14523  ← this is your smoking gun
# throttled_usec: 2341987654

# Fix: Increase quota or use cpu.max.burst
echo "200000 100000" > /sys/fs/cgroup/myservice/cpu.max  # 200% of 1 CPU
echo 50000            > /sys/fs/cgroup/myservice/cpu.max.burst
```

### Pitfall 2: NUMA Remote Memory Access

**Symptom:** Memory-intensive app runs 2× slower on some deployments.  
**Root cause:** Memory allocated on remote NUMA node.  
```bash
numastat -p <pid>
# numa_miss: 45834521  ← allocated on wrong node
```
**Fix:** `numactl --membind=0 --cpunodebind=0 ./myapp`

### Pitfall 3: Wakeup Preemption Regression

**Symptom:** New kernel deployment causes throughput regression (CFS → EEVDF transition).  
**Root cause:** EEVDF's stricter wakeup preemption interrupts long-running compute tasks.  
**Fix:** Set `SCHED_BATCH` for compute-only tasks — disables wakeup preemption:
```bash
chrt -b 0 ./compute_heavy_job
```

### Pitfall 4: Priority Inversion in RT System

**Symptom:** High-priority RT thread appears "stuck" for seconds.  
**Root cause:** Holding a mutex also held by a low-priority thread, which is preempted by medium-priority work.  
**Fix:** `PTHREAD_PRIO_INHERIT` protocol on all mutexes in RT code paths.

### Pitfall 5: Tick-based Jitter with `nohz=off`

**Symptom:** Periodic task has 4ms jitter that is exactly 1 tick period.  
**Root cause:** HZ=250, tick fires every 4ms, interrupting isolated CPU.  
**Fix:** Boot with `nohz_full=<cpulist>` and use `SCHED_DEADLINE` with `sched_yield()` for period management.

### Pitfall 6: `fork()` Bomb via cgroup Escape

**Symptom:** Service creates thousands of threads, bypasses `cpu.max`.  
**Root cause:** Per-task CPU accounting — many threads each at low usage.  
**Fix:** cgroup `pids.max` to limit process count:
```bash
echo 100 > /sys/fs/cgroup/myservice/pids.max
```

### Pitfall 7: `sched_setaffinity()` Breaking Load Balancing

**Symptom:** Some CPUs at 100%, others idle.  
**Root cause:** Overly aggressive CPU pinning prevents load balancer from rebalancing.  
**Fix:** Only pin truly latency-critical threads. Let general threads float.

---

## 23. Hands-On Exercises

### Exercise 1: Visualize CFS Fairness

Build a program that:
1. Spawns 4 threads with nice values: -10, 0, 5, 15
2. Each thread increments a counter in a tight loop for 10 seconds
3. Prints final counter values and computes CPU ratio vs theoretical weight ratio
4. Verify the actual ratio matches `prio_to_weight[nice+20]` ratios within 5%

**Hint:** Use `pthread_setschedparam` and `setpriority` in C, or `libc::setpriority` in Rust.

---

### Exercise 2: Measure Context Switch Overhead

Build a benchmark that:
1. Creates a pipe between two threads
2. Measures round-trip latency (ping-pong) 100,000 times
3. Repeats with: SCHED_NORMAL, SCHED_FIFO prio-50, SCHED_RR prio-30
4. Plots a histogram showing impact of scheduling policy on latency

**Target:** SCHED_FIFO ping-pong should be noticeably lower latency than SCHED_NORMAL.

---

### Exercise 3: Build a cgroup-based Rate Limiter

1. Create a cgroup for a CPU-intensive process
2. Use `cpu.max` to limit it to 25% of one CPU
3. Verify throttling with `cpu.stat`
4. Write a Rust program that:
   - Spawns a child process under the cgroup
   - Monitors `nr_throttled` every second
   - Adjusts `cpu.max` dynamically to target a throttle rate < 5%

---

### Exercise 4: NUMA Locality Experiment

1. On a NUMA machine (or QEMU with NUMA emulation):
   - Run a matrix multiply with `numactl --membind=0 --cpunodebind=1` (memory on wrong node)
   - Run with `numactl --membind=0 --cpunodebind=0` (local memory)
   - Measure bandwidth difference with `numastat`
2. Write a Rust program that:
   - Allocates large arrays
   - Measures bandwidth (GB/s) for sequential reads
   - Reports NUMA statistics from `/proc/<pid>/numa_maps`

---

### Exercise 5: SCHED_DEADLINE Audio Simulation

Build a complete deadline task that simulates an audio rendering pipeline:
1. 5ms runtime, 10ms period (represents a 10ms audio callback)
2. Measures period jitter over 1000 periods
3. Deliberately injects 3ms of extra work in period 500 (CBS throttle test)
4. Reports whether the overrun caused a deadline miss
5. Compare jitter with and without `SCHED_DEADLINE` (use `SCHED_FIFO` as baseline)

---

## 24. Further Reading

### Primary Sources

| Resource | Type | Focus |
|----------|------|-------|
| [LWN: A complete tour of Linux's CFS scheduler](https://lwn.net/Articles/531853/) | Article | CFS internals deep dive |
| [LWN: EEVDF scheduler](https://lwn.net/Articles/925371/) | Article | EEVDF design and motivation |
| [Linux Kernel Source: `kernel/sched/`](https://github.com/torvalds/linux/tree/master/kernel/sched) | Code | Ground truth |
| "Linux Kernel Development" — Robert Love | Book | Chapters 3–4: Process Scheduling |
| "Systems Performance" — Brendan Gregg (2nd ed.) | Book | Chapter 6: CPUs; real-world profiling |
| [Deadline scheduling: EDF and CBS](https://www.kernel.org/doc/html/latest/scheduler/sched-deadline.html) | Documentation | Kernel official DEADLINE docs |

### Tools & Repositories

| Repo | Purpose |
|------|---------|
| [bcc/tools](https://github.com/iovisor/bcc) | runqlat, runqlen, cpudist, offcputime |
| [bpftrace](https://github.com/iovisor/bpftrace) | One-liner scheduler tracing |
| [rt-tests](https://git.kernel.org/pub/scm/linux/kernel/git/clrkwllms/rt-tests.git) | cyclictest, hackbench |
| [pyperf](https://github.com/psf/pyperf) | Latency benchmarking framework |
| [schedviz](https://github.com/google/schedviz) | Google's kernel scheduling visualizer |
| [perf-tools](https://github.com/brendangregg/perf-tools) | Gregg's ftrace/perf wrappers |

### Kernel Documentation

```bash
# On your system:
/usr/share/doc/linux-doc/scheduler/
# Or online:
# https://www.kernel.org/doc/html/latest/scheduler/
#   sched-design-CFS.html
#   sched-deadline.html
#   sched-rt-group.html
#   sched-nice-design.html
#   sched-energy.html
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LINUX SCHEDULER QUICK REFERENCE                       │
├─────────────────┬──────────────┬──────────────┬─────────────────────────┤
│ Goal            │ Policy       │ Command      │ Notes                   │
├─────────────────┼──────────────┼──────────────┼─────────────────────────┤
│ Default         │ SCHED_NORMAL │ (default)    │ CFS/EEVDF               │
│ High-throughput │ SCHED_BATCH  │ chrt -b 0    │ No wakeup preemption    │
│ Background      │ SCHED_IDLE   │ chrt -i 0    │ Only when CPU free      │
│ Hard RT         │ SCHED_FIFO   │ chrt -f 50   │ Need CAP_SYS_NICE       │
│ Soft RT         │ SCHED_RR     │ chrt -r 30   │ Round-robin among peers │
│ Periodic RT     │ SCHED_DEADLINE│ sched_setattr│ EDF+CBS, admission ctrl │
├─────────────────┼──────────────┼──────────────┼─────────────────────────┤
│ Pin to CPU      │ affinity     │ taskset -c 2 │ Hard: isolcpus boot opt │
│ NUMA local      │ membind      │ numactl      │ Check numastat -p <pid> │
│ CPU quota       │ cgroup v2    │ cpu.max      │ Check cpu.stat throttle │
│ Latency tune    │ sched_latency│ sysctl       │ sched_latency_ns=3ms    │
├─────────────────┼──────────────┼──────────────┼─────────────────────────┤
│ Observe latency │ perf sched   │ perf sched latency    │                │
│ BPF histogram   │ bcc          │ runqlat 10 1           │                │
│ RT jitter       │ cyclictest   │ cyclictest -p99 -m     │                │
│ cgroup throttle │ cpu.stat     │ cat cpu.stat│grep throttled            │
└─────────────────┴──────────────┴──────────────┴─────────────────────────┘

vruntime_delta = wall_delta × (1024 / task_weight)
timeslice      = sched_latency × (task_weight / total_rq_weight)
util_deadline  = runtime / period  [must be ≤ 1.0 per CPU]
```

Now let me build this comprehensive guide. This will be a large, production-grade document.~4,500 lines covering the full scheduler stack. Here's what's inside and how to use it:

---

## Structure at a Glance

**Theory (sections 1–12)**
- Scheduler evolution: O(n) → O(1) → CFS → EEVDF, with the exact algorithmic change at each step
- CFS internals: the vruntime formula, weight table, red-black tree mechanics, wakeup preemption, group scheduling hierarchy
- EEVDF (6.6+): eligible time, virtual deadlines, why it fixes CFS's heuristic wakeup bugs
- Context switch anatomy: exactly what `switch_to()` saves/restores on x86_64, CR3/PCID, cost table
- All six scheduling classes with the vtable dispatch order

**Operations (sections 13–16)**
- CPU affinity (soft), `isolcpus`/`nohz_full` (hard), IRQ migration
- cgroups v2: `cpu.weight`, `cpu.max`, burst mode, and the **P99 spike from throttling** (the #1 production scheduler bug)
- Every tunable in `/proc/sys/kernel/sched_*` with what to change for low-latency vs throughput

**Observability (sections 17–18)**
- `perf sched latency/timehist/map` workflows
- ftrace event format decoded
- bpftrace one-liners for wakeup latency histograms and off-CPU analysis
- `cyclictest` for RT jitter measurement

**Code**
| File | What it demonstrates |
|------|----------------------|
| `cfs_sim.c` | vruntime accumulation, weight-proportional slices, min-heap as rb-tree substitute |
| `sched_policy.c` | `sched_setattr` wrappers, affinity, wakeup latency measurement (avg/p99/p999) |
| `rqlen_monitor.c` | `/proc/schedstat` polling, top tasks by run-queue wait time |
| `priority_inversion.c` | Classic inversion demo + `PTHREAD_PRIO_INHERIT` fix, side by side |
| `scheduler_threadpool/src/main.rs` | Work-stealing pool with CPU pinning, vruntime tracker with unit tests |
| `deadline_task/src/main.rs` | Raw `sched_setattr` via inline asm, periodic task, jitter analysis |
| `sched_inspect/src/main.rs` | `/proc` scraper: top tasks by wait time, per-CPU schedstat |

**Key things to verify immediately on your system:**
```bash
# Are any of your cgroups being throttled right now?
find /sys/fs/cgroup -name cpu.stat -exec grep -l "nr_throttled" {} \; \
  | xargs -I{} sh -c 'echo "=== {} ==="; cat {}'

# What scheduler is running?
uname -r && zcat /proc/config.gz | grep -E "PREEMPT|HZ="
```