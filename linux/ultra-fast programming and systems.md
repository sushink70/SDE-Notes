Ultra-Fast Programming & Systems: A Comprehensive Guide

PART 1: FUNDAMENTAL SPEED PRINCIPLES
How CPUs Actually Work (and Why It Matters)
Before optimizing anything, you must understand the hardware. Modern CPUs are deeply pipelined, out-of-order, and speculative. Speed comes from feeding the CPU a predictable, compact stream of work with no stalls. Every technique below serves that goal.
The memory hierarchy is the single most important concept:

L1 cache: ~1–4 ns, 32–64 KB
L2 cache: ~5–12 ns, 256 KB – 1 MB
L3 cache: ~20–50 ns, 8–64 MB
DRAM: ~60–100 ns, gigabytes
NVMe SSD: ~100,000 ns

A cache miss to RAM is 50–100x slower than an L1 hit. Everything else — bit tricks, SIMD, lock-free structures — only matters if you've already solved your memory access patterns.

PART 2: LOW-LEVEL PROGRAMMING TECHNIQUES
Bit Manipulation
Bit manipulation replaces expensive branches and multiplications with single-cycle CPU instructions.
Check if a number is a power of 2:
cbool is_pow2(unsigned n) { return n && !(n & (n - 1)); }
Round up to next power of 2:
cuint32_t next_pow2(uint32_t n) {
    n--;
    n |= n >> 1; n |= n >> 2; n |= n >> 4; n |= n >> 8; n |= n >> 16;
    return ++n;
}
Fast modulo for power-of-2 sizes (replaces % which is a division):
csize_t idx = value & (SIZE - 1);  // SIZE must be power of 2
Swap without a temp variable:
ca ^= b; b ^= a; a ^= b;
Clear the lowest set bit:
cn &= (n - 1);  // Used in Hamming weight, subset enumeration
Isolate the lowest set bit:
clowest = n & (-n);
Count trailing zeros (find alignment, power of 2 log):
c__builtin_ctz(n);   // GCC/Clang intrinsic — single instruction on x86
__builtin_clz(n);   // Count leading zeros
__builtin_popcount(n); // Population count (number of 1 bits)
Branchless absolute value:
cint abs_val(int x) {
    int mask = x >> 31;
    return (x + mask) ^ mask;
}
Branchless min/max:
cint min_val = b + ((a - b) & ((a - b) >> 31));
int max_val = a - ((a - b) & ((a - b) >> 31));
These replace conditional branches which cause pipeline flushes on misprediction.

Hexadecimal and Fixed-Width Types
Always use fixed-width types from <stdint.h> / <cstdint> in performance-critical code:
cuint8_t, uint16_t, uint32_t, uint64_t   // exact width, no sign ambiguity
int8_t,  int16_t,  int32_t,  int64_t
Using int where you mean "32 bits" is dangerous and slower on some architectures. Using size_t for sizes and indices is correct because it matches pointer width on the target platform.
Hex literals make bitmask intent obvious:
c#define FLAGS_DIRTY   0x01
#define FLAGS_LOCKED  0x02
#define FLAGS_PINNED  0x04
#define FLAGS_VALID   0x08

// Set multiple flags at once
entry->flags |= (FLAGS_DIRTY | FLAGS_VALID);

// Clear a flag
entry->flags &= ~FLAGS_LOCKED;

// Test a flag
if (entry->flags & FLAGS_PINNED) { ... }

Memory Layout and Cache Efficiency
Structure of Arrays (SoA) vs Array of Structures (AoS)
AoS (bad for hot loops that touch only a few fields):
cstruct Particle {
    float x, y, z;       // position
    float vx, vy, vz;    // velocity
    float mass;
    uint32_t flags;
    char name[32];        // cold data — rarely touched
};
Particle particles[N];
If your hot loop only reads x, y, z, you load 56 bytes per particle but use only 12. Cache lines are 64 bytes — you're wasting 75% of every cache line.
SoA (good — hot data is packed):
cstruct ParticleSystem {
    float *x, *y, *z;       // arrays of positions
    float *vx, *vy, *vz;    // arrays of velocities
    float *mass;
    uint32_t *flags;
    char **names;            // cold — pointer to separate allocation
};
Now a loop over all x positions loads 16 floats per cache line, fully utilized.
Cache line alignment:
c// Force struct to start on a cache line boundary
struct alignas(64) HotData {
    uint64_t counter;
    uint64_t timestamp;
    // pad to 64 bytes to prevent false sharing
    char _pad[48];
};
False sharing is when two threads write to different variables that happen to sit on the same cache line, causing constant cache invalidation between cores. Always pad shared structures to 64 bytes.
Prefetching:
cfor (int i = 0; i < N; i++) {
    __builtin_prefetch(&data[i + 16], 0, 1);  // prefetch 16 ahead, read, low locality
    process(data[i]);
}
The CPU can prefetch automatically for sequential access — only use manual prefetching for non-sequential patterns (linked lists, trees, hash tables).

Continuous Memory Allocation
Dynamic allocation (malloc/new) is slow because:

It acquires a lock (thread-safe heap)
It searches a free list
It introduces fragmentation
Allocations are scattered — bad locality

Arena / Linear Allocator:
ctypedef struct {
    uint8_t *base;
    size_t   offset;
    size_t   capacity;
} Arena;

void* arena_alloc(Arena *a, size_t size, size_t align) {
    size_t aligned = (a->offset + align - 1) & ~(align - 1);
    if (aligned + size > a->capacity) return NULL;
    a->offset = aligned + size;
    return a->base + aligned;
}

void arena_reset(Arena *a) { a->offset = 0; }  // O(1) free everything
Use one arena per frame, per request, per task. Free everything at once. Zero per-object overhead.
Pool Allocator (fixed-size objects):
ctypedef struct FreeNode { struct FreeNode *next; } FreeNode;

typedef struct {
    uint8_t   *memory;
    FreeNode  *freelist;
    size_t     object_size;
} Pool;

void* pool_alloc(Pool *p) {
    if (!p->freelist) return NULL;
    FreeNode *node = p->freelist;
    p->freelist = node->next;
    return node;
}

void pool_free(Pool *p, void *ptr) {
    FreeNode *node = ptr;
    node->next = p->freelist;
    p->freelist = node;
}
Constant time, no fragmentation, excellent cache locality.
Ring Buffer (lock-free producer-consumer):
ctypedef struct {
    uint8_t  *buf;
    uint32_t  mask;       // size - 1, size must be power of 2
    _Atomic uint32_t head;
    _Atomic uint32_t tail;
} RingBuf;

bool rb_push(RingBuf *rb, uint8_t byte) {
    uint32_t h = atomic_load_explicit(&rb->head, memory_order_relaxed);
    uint32_t next = (h + 1) & rb->mask;
    if (next == atomic_load_explicit(&rb->tail, memory_order_acquire))
        return false;  // full
    rb->buf[h] = byte;
    atomic_store_explicit(&rb->head, next, memory_order_release);
    return true;
}

SIMD (Single Instruction, Multiple Data)
SIMD allows one instruction to operate on multiple data lanes simultaneously.

SSE2: 128-bit registers, 4 floats or 2 doubles at once
AVX2: 256-bit registers, 8 floats at once
AVX-512: 512-bit registers, 16 floats at once

c#include <immintrin.h>

// Add 8 floats at once using AVX
void add_arrays_avx(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i += 8) {
        __m256 va = _mm256_loadu_ps(&a[i]);
        __m256 vb = _mm256_loadu_ps(&b[i]);
        __m256 vc = _mm256_add_ps(va, vb);
        _mm256_storeu_ps(&c[i], vc);
    }
}
Use aligned loads (_mm256_load_ps) when data is 32-byte aligned — it's faster than unaligned.
Auto-vectorization: GCC and Clang can auto-vectorize simple loops if you help them:
c// Hint: no aliasing between pointers
void add(float * __restrict__ a, float * __restrict__ b, float * __restrict__ c, int n) {
    for (int i = 0; i < n; i++) c[i] = a[i] + b[i];
}
Compile with -O3 -march=native -ffast-math to enable auto-vectorization with native ISA.

Branch Prediction and Branchless Code
Modern CPUs predict branches speculatively. A misprediction costs ~15–20 cycles.
Sort data to make branches predictable:
c// Unpredictable — branch mispredicts ~50% of the time
for (int i = 0; i < N; i++)
    if (data[i] >= 128) sum += data[i];

// After sorting data[], the branch is predictable (all-no then all-yes)
Replace branches with arithmetic:
c// Branchy
if (x > 0) result = x;
else result = 0;

// Branchless
result = x & -(x > 0);  // or use: result = (x > 0) ? x : 0  — compilers often make this branchless
Use __builtin_expect to tell the compiler which branch is hot:
cif (__builtin_expect(ptr == NULL, 0)) {
    // cold path — error handling
}

Lock-Free Data Structures
Mutexes are slow: they involve kernel syscalls, context switches, cache line bouncing. Lock-free structures use atomic CAS (Compare-And-Swap) operations.
c// Lock-free counter
_Atomic int64_t counter = 0;
atomic_fetch_add(&counter, 1);  // single atomic instruction

// Lock-free stack push (ABA problem exists — use versioned pointers in production)
typedef struct Node { int val; _Atomic(struct Node*) next; } Node;

void stack_push(_Atomic(Node*) *top, Node *node) {
    Node *old;
    do {
        old = atomic_load(top);
        atomic_store(&node->next, old);
    } while (!atomic_compare_exchange_weak(top, &old, node));
}
Memory order matters:

memory_order_relaxed: no synchronization, just atomicity. Use for counters.
memory_order_acquire: prevents loads from moving before this point.
memory_order_release: prevents stores from moving after this point.
memory_order_seq_cst: full fence, slowest, use as default when unsure.


Compiler Optimizations
Always know what your compiler does. Key flags:
bash-O2          # Safe optimizations
-O3          # Aggressive, including vectorization
-Os          # Optimize for size (better cache utilization sometimes)
-march=native # Use all CPU features of the build machine
-ffast-math  # Allows FP reordering (breaks strict IEEE 754)
-flto        # Link-time optimization — cross-TU inlining
-fprofile-use # Profile-guided optimization (PGO) — best real-world speedup
Profile-Guided Optimization (PGO) is often the single biggest win:
bash# Step 1: Instrument binary
gcc -O2 -fprofile-generate -o app app.c

# Step 2: Run with representative workload
./app workload.dat

# Step 3: Recompile using profile data
gcc -O2 -fprofile-use -o app app.c
PGO feeds real branch frequencies and call counts back into the compiler, enabling better inlining, layout, and branch prediction hints.

Memory-Mapped I/O
mmap maps files directly into virtual address space. Reading a mapped file avoids a copy from kernel buffer to user buffer:
cint fd = open("data.bin", O_RDONLY);
struct stat sb;
fstat(fd, &sb);
void *data = mmap(NULL, sb.st_size, PROT_READ, MAP_PRIVATE | MAP_POPULATE, fd, 0);
// Access data directly — page faults bring pages in on demand
// MAP_POPULATE pre-faults all pages at mmap time
munmap(data, sb.st_size);
Use madvise() to give the kernel hints:
cmadvise(data, size, MADV_SEQUENTIAL);  // prefetch ahead
madvise(data, size, MADV_RANDOM);      // don't prefetch — random access pattern
madvise(data, size, MADV_WILLNEED);    // prefetch now
madvise(data, size, MADV_DONTNEED);    // release pages

PART 3: LINUX KERNEL PERFORMANCE TECHNIQUES
The Linux Kernel's Internal Fast Paths
Per-CPU variables eliminate cache line contention:
cDEFINE_PER_CPU(int, my_counter);

// Access without locks — only this CPU touches it
int val = __this_cpu_read(my_counter);
__this_cpu_add(my_counter, 1);
No atomics, no cache invalidation between cores.
RCU (Read-Copy-Update) is Linux's most important synchronization primitive for read-heavy data:
c// Readers — no lock, no atomic, just a memory barrier
rcu_read_lock();
struct config *cfg = rcu_dereference(global_config);
// use cfg
rcu_read_unlock();

// Writer — makes a copy, updates, then waits for existing readers to finish
struct config *new_cfg = kmalloc(sizeof(*new_cfg), GFP_KERNEL);
memcpy(new_cfg, old_cfg, sizeof(*new_cfg));
new_cfg->value = 42;
rcu_assign_pointer(global_config, new_cfg);
synchronize_rcu();  // wait for all pre-existing RCU read sections
kfree(old_cfg);
RCU readers have literally zero overhead on uncontended fast paths — just a preemption disable.
Slab/SLUB Allocator — the kernel's pool allocator:
c// Create a cache for your object type
struct kmem_cache *my_cache = kmem_cache_create(
    "my_object", sizeof(struct my_object), 0, SLAB_HWCACHE_ALIGN, NULL);

// Alloc and free are O(1), cache-hot
struct my_object *obj = kmem_cache_alloc(my_cache, GFP_KERNEL);
kmem_cache_free(my_cache, obj);
Objects are recycled — allocation returns a cache-warm object that was recently freed.
Seqlocks for read-mostly data that changes atomically:
cseqlock_t my_lock = __SEQLOCK_UNLOCKED(my_lock);

// Reader — retries if a write happened mid-read
unsigned seq;
do {
    seq = read_seqbegin(&my_lock);
    // read data
} while (read_seqretry(&my_lock, seq));

// Writer
write_seqlock(&my_lock);
// update data
write_sequnlock(&my_lock);
Hugepages reduce TLB pressure. By default Linux maps memory in 4 KB pages. With hugepages (2 MB), the same data requires 512x fewer TLB entries:
bash# Transparent Huge Pages (automatic)
echo always > /sys/kernel/mm/transparent_hugepage/enabled

# In code
void *ptr = mmap(NULL, size, PROT_READ|PROT_WRITE,
                 MAP_PRIVATE|MAP_ANONYMOUS|MAP_HUGETLB, -1, 0);
io_uring — the modern Linux I/O interface (5.1+):
Traditional I/O: read() → syscall → kernel → data → return. Each read() is a full syscall round-trip.
io_uring: submit batches of I/O requests into a shared ring buffer with the kernel. Zero syscalls for the fast path when the submission queue has space:
cstruct io_uring ring;
io_uring_queue_init(256, &ring, 0);

struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_read(sqe, fd, buf, len, offset);
io_uring_submit(&ring);

struct io_uring_cqe *cqe;
io_uring_wait_cqe(&ring, &cqe);
io_uring_cqe_seen(&ring, cqe);
io_uring can achieve millions of IOPS on NVMe by batching and polling rather than blocking.
eBPF for kernel-speed custom logic without kernel modules:
bash# Attach a BPF program to a kernel tracepoint or network hook
# Run custom packet filtering, tracing, or load balancing at kernel speed
# Tools: bpftool, libbpf, BCC, bpftrace
eBPF programs run in the kernel JIT-compiled, with no user/kernel boundary crossing.
DPDK (Data Plane Development Kit) — bypass the kernel entirely for networking:

Polls NICs from userspace using PMD (Poll Mode Drivers)
Zero-copy packet processing
Millions of packets per second per core
Used in NFV, firewalls, load balancers


Linux Performance Tuning
CPU isolation — dedicate cores to your workload:
bash# Kernel boot parameter: isolate cores 2-7 from scheduler
isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7

# Pin a process to isolated cores
taskset -c 2-7 ./my_realtime_app
CPU frequency scaling — disable for latency:
bash# Set performance governor (no frequency scaling)
cpupower frequency-set -g performance

# Or per-CPU
echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
NUMA awareness:
bash# Run on NUMA node 0, allocate memory from node 0
numactl --cpunodebind=0 --membind=0 ./app

# Check NUMA topology
numactl --hardware
NUMA (Non-Uniform Memory Access) means CPUs have local and remote RAM. Accessing remote RAM can be 2x slower. Always bind processes to a NUMA node and allocate memory from the same node.
IRQ affinity — move interrupts off your hot cores:
bash# Move NIC interrupts to core 0, leave cores 1-7 for your app
echo 1 > /proc/irq/[IRQ_NUM]/smp_affinity_list
Disable kernel mitigations for trusted environments:
bash# Boot parameters (significant performance impact on some workloads)
spectre_v2=off nopti mitigations=off
# WARNING: Only on trusted/isolated systems
Tune the scheduler:
bash# Reduce scheduling latency (lower = more responsive, higher CPU overhead)
echo 100000 > /proc/sys/kernel/sched_min_granularity_ns
echo 500000 > /proc/sys/kernel/sched_wakeup_granularity_ns

PART 4: RTOS vs LINUX KERNEL
Why RTOS is Faster (for Real-Time Tasks)
An RTOS (Real-Time Operating System — FreeRTOS, Zephyr, VxWorks, QNX, RT-Thread) is designed from the ground up for determinism and bounded latency, not throughput.
The fundamental difference: Linux optimizes for average-case throughput. RTOS optimizes for worst-case latency.
Key architectural differences:
AspectLinuxRTOSSchedulerCFS (fairness-based, complex)Priority-based preemption, O(1)Kernel preemptionPartial (preempt-rt patches full)Fully preemptible at any pointInterrupt latency10–100+ µs typical1–10 µs typicalContext switch~1–5 µs~100 ns – 1 µsMemory managementVirtual memory, paging, TLB missesOften no MMU, or simple MPUTickDynamic tickless or 4ms defaultOften 1ms or tick-freeSyscall overheadFull user/kernel boundaryNone — single address space
Why RTOS has lower latency:

No virtual memory overhead. Many RTOS run without an MMU. No page table walks, no TLB misses, no page faults. Everything is in physical memory, always.
Fully preemptible kernel. A high-priority task can preempt even the kernel itself at any instruction. In Linux, certain kernel sections hold locks that make preemption impossible, adding unpredictable latency.
Priority-based scheduler with O(1) dispatch. When a high-priority task becomes ready, it runs immediately. No fairness calculations, no scheduling groups, no load balancing.
No complex subsystems. No VFS, no network stack overhead, no cgroups, no namespaces. The scheduler does one thing: run the highest priority ready task.
Deterministic memory allocation. Pool allocators with no heap fragmentation. Allocation time is bounded and constant.
Interrupt-to-task latency is deterministic. ISR fires → highest priority waiting task runs within a known, bounded time (µs range).


PART 5: MAKING LINUX BEHAVE LIKE AN RTOS
Yes, It Is Possible — With Caveats
Linux can be tuned to achieve near-RTOS real-time performance. It will never match a bare-metal RTOS for absolute worst-case latency, but can reach 10–50 µs worst-case jitter, which is sufficient for many industrial applications.
PREEMPT_RT Patch (Now Mainlined)
The most important step. PREEMPT_RT converts nearly all kernel spinlocks into sleeping mutexes, makes interrupt handlers run in kernel threads (schedulable), and makes the kernel fully preemptible:
bash# Check if your kernel has PREEMPT_RT
uname -v | grep PREEMPT_RT

# Build kernel with full preemption
make menuconfig
# → General Setup → Preemption Model → Fully Preemptible Kernel (RT)

# Or use a distribution RT kernel
apt install linux-image-rt-amd64  # Debian/Ubuntu
With PREEMPT_RT, worst-case interrupt latency drops from hundreds of microseconds to tens of microseconds.
SCHED_FIFO and SCHED_RR — real-time scheduling policies:
cstruct sched_param sp = { .sched_priority = 99 };  // 1-99, 99 is highest
pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp);
SCHED_FIFO: runs until it blocks or yields. Never preempted by lower-priority tasks. Preempts all SCHED_OTHER (normal) tasks.
bash# From shell
chrt -f 99 ./my_realtime_app
Memory locking — prevent page faults:
c#include <sys/mman.h>

// Lock all current and future pages in RAM — no page faults ever
mlockall(MCL_CURRENT | MCL_FUTURE);

// Pre-fault the stack
void prefault_stack(void) {
    char buf[8 * 1024 * 1024];  // 8 MB
    memset(buf, 0, sizeof(buf));
}
A page fault in a real-time task causes a kernel page-in which can take milliseconds. mlockall eliminates this entirely.
Use the cyclictest tool to measure latency:
bash# Install rt-tests
apt install rt-tests

# Measure scheduling latency on core 1
cyclictest --mlockall --smp --priority=99 --interval=200 --distance=0 -a 1

# Target: max latency < 100 µs for soft real-time, < 20 µs for hard real-time
Disable dynamic tick for real-time cores:
bash# Boot parameters
nohz_full=2-7    # Disable tick on cores 2-7 when one task runs
rcu_nocbs=2-7    # Move RCU callbacks off these cores
The periodic tick (HZ) causes unnecessary wakeups — every 1ms or 4ms the scheduler interrupts your real-time task. nohz_full suppresses this.
Use real-time memory allocation patterns:
c// Pre-allocate all memory at startup
// Never call malloc() in the real-time loop
// Use pool allocators (see Part 2)

// Stack allocation is fine — already locked via mlockall
Thread and CPU isolation stack:
bash# 1. Isolate cores at boot
isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7 irqaffinity=0-1

# 2. Move all IRQs to core 0
for irq in /proc/irq/*/smp_affinity_list; do echo 0 > $irq; done

# 3. Pin real-time thread to isolated core
taskset -c 3 chrt -f 99 ./rt_app

# 4. Set CPU frequency to performance
cpupower frequency-set -g performance

# 5. Disable C-states (deep sleep causes wakeup latency)
cpupower idle-set -D 0
# or boot parameter: intel_idle.max_cstate=0 processor.max_cstate=0
C-states are CPU sleep states. C0 = running, C1 = light sleep, C6 = deep sleep (saves power, but wakeup takes hundreds of µs). Disable for real-time.
Dual-Kernel Approach (Xenomai / RTAI)
For absolute hard real-time requirements, use a co-kernel:
Xenomai runs a small RTOS underneath Linux. The RTOS handles real-time tasks; Linux runs as the lowest-priority task of the RTOS:
Hardware IRQ
    ↓
Xenomai RTOS (handles RT tasks in µs)
    ↓ (when idle)
Linux kernel (normal tasks)

Real-time tasks use Xenomai APIs (POSIX-compatible via skin)
Worst-case latency: 1–10 µs even under heavy Linux load
Used in CNC machines, robotics, industrial control

bash# Install Xenomai
apt install xenomai-kernel-source
# Build and boot dual kernel
# Compile RT tasks against Xenomai libraries
gcc -o rt_task rt_task.c $(xeno-config --skin=posix --cflags --ldflags)
PREEMPT_RT vs Xenomai:
RequirementUse< 100 µs jitter, Linux APIsPREEMPT_RT< 10 µs jitter, max determinismXenomaiEmbedded, no Linux neededFreeRTOS / Zephyr

PART 6: PROFILING AND MEASUREMENT
You cannot optimize what you cannot measure. Always profile before optimizing.
perf — the Linux profiler:
bash# CPU profiling — where is time spent?
perf record -g ./app
perf report

# Cache misses
perf stat -e cache-misses,cache-references,instructions,cycles ./app

# Branch mispredictions
perf stat -e branch-misses,branches ./app

# Detailed hardware counters
perf stat -e L1-dcache-load-misses,LLC-load-misses,dTLB-load-misses ./app
flamegraphs:
bashperf record -F 99 -g ./app
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > flame.svg
Valgrind/Cachegrind — cache simulation:
bashvalgrind --tool=cachegrind ./app
cg_annotate cachegrind.out.*
gprof — function-level profiling:
bashgcc -pg -o app app.c
./app
gprof app gmon.out | less
Latency measurement in code:
c#include <time.h>

struct timespec t1, t2;
clock_gettime(CLOCK_MONOTONIC_RAW, &t1);
// ... code to measure
clock_gettime(CLOCK_MONOTONIC_RAW, &t2);

long ns = (t2.tv_sec - t1.tv_sec) * 1e9 + (t2.tv_nsec - t1.tv_nsec);
Use CLOCK_MONOTONIC_RAW for measurements — it's not subject to NTP adjustments.
RDTSC for cycle-accurate measurement:
cstatic inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ __volatile__("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

uint64_t start = rdtsc();
// code
uint64_t cycles = rdtsc() - start;

PART 7: NETWORK AND I/O FAST PATHS
Kernel bypass networking:

DPDK: Poll-mode userspace drivers, zero-copy, millions of PPS
AF_XDP: eBPF-based zero-copy socket, kernel bypass for specific queues
RDMA/RoCE: Remote Direct Memory Access — memory-to-memory transfers without CPU involvement, nanosecond latency in HPC

TCP tuning for throughput:
bash# Increase socket buffers
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"

# Enable TCP BBR congestion control (better for high-BDP links)
sysctl -w net.ipv4.tcp_congestion_control=bbr

# Busy-poll for low-latency
sysctl -w net.core.busy_poll=50
sysctl -w net.core.busy_read=50
SO_BUSY_POLL — spin on socket instead of sleeping:
cint val = 50;  // microseconds to busy-poll
setsockopt(fd, SOL_SOCKET, SO_BUSY_POLL, &val, sizeof(val));
Eliminates interrupt latency for low-latency networking at the cost of CPU.

SUMMARY: PRIORITY ORDER OF OPTIMIZATIONS
When optimizing, apply in this order (highest ROI first):

Algorithm complexity — O(n²) → O(n log n) beats any micro-optimization
Memory layout — fix cache misses before anything else
Avoid syscalls / context switches — batch, poll, use userspace
Use the right data structures — pool allocators, ring buffers, flat arrays
Compiler flags and PGO — free wins with correct flags
Eliminate locks — per-CPU data, RCU, lock-free structures
SIMD and bit tricks — after the above are solved
Kernel tuning — PREEMPT_RT, CPU isolation, NUMA binding
Hardware-level — DPDK, RDMA, hugepages, C-state control

Measure at every step. The bottleneck is almost never where you think it is.