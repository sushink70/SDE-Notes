# Bug Analysis, Diagnosis, and Fix Reference
# =============================================
# File: docs/bugs-and-fixes.md
# Demonstrates how a kernel developer diagnoses and fixes BPF program bugs.

## BUG #1 — Code Bug: Assignment-as-condition (operator error)
###############################################################################

### Location
    kernel/xdp_filter.bpf.BUGGY.c, line 82

### Buggy code
```c
/* WRONG */
if (ip->ihl = 5) {       /* single '=' is ASSIGNMENT, not comparison */
    inc_stat(STAT_PARSE);
    return XDP_PASS;
}
```

### What actually happens
1. `ip->ihl = 5` writes 5 into the ip header's ihl field IN THE PACKET BUFFER.
   XDP gives the BPF program direct read/write access to the packet memory.
   This silently mutates packets that pass through.

2. The expression evaluates to 5 (non-zero), so the condition is ALWAYS TRUE.
   Result: every IPv4 packet immediately hits `return XDP_PASS` — neither the
   blocklist nor the rate limiter is ever checked.

3. On x86_64 this compiles with clang warning:
   `warning: using the result of an assignment as a condition without
    parentheses [-Wparentheses]`
   ...but DOES compile. The BPF verifier does not catch logic errors, only
   safety violations. The program loads and runs silently broken.

### How to detect
```bash
# Method 1: Compiler warning
clang -O2 -g -target bpf -Wall -Werror -c xdp_filter.bpf.BUGGY.c 2>&1
# → error: using the result of an assignment as a condition [-Werror,-Wparentheses]

# Method 2: Behavioral test — blocklist never drops
sudo ./xdp_filter --iface eth0 --block 192.168.1.100 --stats &
hping3 --icmp --spoof 192.168.1.100 -c 100 eth0
# Expected: STAT_BLOCK > 0
# Observed: STAT_BLOCK = 0  ← bug symptom

# Method 3: bpftool xlated dump
bpftool prog dump xlated id $PROG_ID linum
# The xlated bytecode will show:
#   r1 = *(u8 *)(r2 + offset_of_ihl)  ← reads ihl
#   *(u8 *)(r2 + offset_of_ihl) = 5    ← WRITES 5 back (bug!)
#   if r0 == 0 goto ...                ← always evaluates to 5 != 0

# Method 4: bpf_printk instrumentation
# Add temporarily:
bpf_printk("ihl=%d", ip->ihl);
# In trace_pipe:
cat /sys/kernel/debug/tracing/trace_pipe
# If ihl is always 5 for all packets → assignment bug confirmed
```

### Fix (unified diff)
```diff
--- a/kernel/xdp_filter.bpf.BUGGY.c
+++ b/kernel/xdp_filter.bpf.c
@@ -82,7 +82,7 @@
-    if (ip->ihl = 5) {                      /* BUG: assignment */
+    if (ip->ihl < 5) {                      /* FIX: reject IHL < 5 */
         inc_stat(STAT_PARSE);
         return XDP_PASS;
     }
```

### Root cause analysis
C's operator precedence and the accidental validity of lvalue-in-condition.
The compiler allows assigning to a dereferenced pointer inside `if()`.
**Kernel style rule**: always use `-Wall -Werror` and run `sparse` on BPF code.

```bash
# Run sparse (kernel semantic checker):
make C=2 CF="-D__CHECK_ENDIAN__" kernel/bpf/myprog.o
```

---

## BUG #2 — Logic Bug: Byte-order mismatch in map key
###############################################################################

### Location
    kernel/xdp_filter.bpf.BUGGY.c, line 68

### Buggy code
```c
/* WRONG — converts to host byte order before using as map key */
__u32 src_ip = bpf_ntohl(ip->saddr);
```

### What actually happens
IPv4 addresses travel over the wire (and exist in struct iphdr) in **network
byte order** (big-endian). On x86_64 (little-endian), network byte order is
the OPPOSITE of host byte order.

For IP 192.168.1.100:
  - Network order bytes: c0 a8 01 64  → u32 value: 0xc0a80164
  - Host order bytes:    64 01 a8 c0  → u32 value: 0x6401a8c0

The userspace loader calls `inet_addr("192.168.1.100")` or `inet_pton()`,
both of which return the address in NETWORK byte order (0xc0a80164).
That's what gets stored as the map key.

The BPF program, after `bpf_ntohl()`, looks up 0x6401a8c0 in the map.
The map contains 0xc0a80164. **They never match.** The blocklist is
completely ineffective — blocked IPs are never dropped.

### How to detect
```bash
# Method 1: Inspect the raw map key bytes
bpftool map dump pinned /sys/fs/bpf/xdp_filter/blocklist
# Shows something like:
#   key: c0 a8 01 64   value: 01
#                              ^^ stored correctly by userspace

# Then add bpf_printk to log the key used for lookup:
bpf_printk("lookup key: %08x", src_ip);
cat /sys/kernel/debug/tracing/trace_pipe
# Shows: lookup key: 6401a8c0   ← WRONG (host order)
# Map key is: c0 a8 01 64       ← RIGHT (net order)
# → Mismatch confirmed

# Method 2: Write a selftest
# Insert 192.168.1.100 (net order), send packet from same IP, expect XDP_DROP.
# If retval == XDP_PASS → byte-order bug present.

# Method 3: Enable __CHECK_ENDIAN__ in sparse
make C=2 CF="-D__CHECK_ENDIAN__"
# sparse will flag: warning: incorrect type in assignment (different base types)
#   expected unsigned int [usertype] src_ip
#   got unsigned int [usertype, bigendian] saddr
```

### Fix (unified diff)
```diff
--- a/kernel/xdp_filter.bpf.BUGGY.c
+++ b/kernel/xdp_filter.bpf.c
@@ -68,7 +68,9 @@
-    __u32 src_ip = bpf_ntohl(ip->saddr);   /* BUG: converts to host order */
+    /*
+     * Keep src_ip in network byte-order throughout.
+     * Maps are populated by userspace using inet_addr()/inet_pton() which
+     * also return network-order values — the key spaces must match.
+     */
+    __u32 src_ip = ip->saddr;              /* FIX: stay in network order */
```

### Deeper: Using __be32 type annotation to prevent this class of bug
```c
/* Annotate network-order values with __be32 — sparse will enforce this */
__be32 src_ip = ip->saddr;   /* sparse enforces: no implicit conversion */

/* If you accidentally call bpf_ntohl(), sparse warns:
   warning: incorrect type in assignment
   expected restricted __be32 [usertype] src_ip
   got unsigned int [unsigned] [usertype]
*/
```
This is how the kernel's net stack works — all network-order values are
typed as `__be16`, `__be32`, `__be64` and sparse enforces correct usage.

---

## General Debugging Strategy for BPF Programs
###############################################################################

```
Step 1: Does it compile with -Wall -Werror?
   clang -O2 -g -target bpf -Wall -Werror -c prog.bpf.c
   → Fix all warnings first.

Step 2: Does the verifier accept it?
   bpftool prog load prog.bpf.o /sys/fs/bpf/_test 2>&1 | grep -i error

Step 3: Does behavior match expected?
   Write a BPF_PROG_TEST_RUN selftest (see tests/xdp_filter_test.c)
   → Inject synthetic packets, check retval and map state.

Step 4: Is the bytecode correct?
   bpftool prog dump xlated id $ID linum
   → Trace execution path for suspicious branches.

Step 5: Is the JIT output correct? (rare, but verifiable)
   bpftool prog dump jited id $ID linum
   → Cross-reference with perf annotate.

Step 6: Add temporary bpf_printk() instrumentation
   → cat /sys/kernel/debug/tracing/trace_pipe
   → Remove before submission (bpf_printk is GPL-only and slow)

Step 7: Run sparse with __CHECK_ENDIAN__
   make C=2 CF="-D__CHECK_ENDIAN__"

Step 8: Run the full selftest suite
   cd tools/testing/selftests/bpf && sudo ./test_progs -j8
```
