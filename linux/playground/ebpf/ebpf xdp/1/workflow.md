# File: docs/WORKFLOW.md
# How a Linux Kernel Developer Actually Works
## (The path from "idea" to "Linus pulls your patch")

---

## The Kernel Tree Hierarchy

```
Linus Torvalds (torvalds/linux on kernel.org)
    │
    ├── net-next tree (David S. Miller / Jakub Kicinski)
    │       └── net/  — core networking
    │       └── drivers/net/  — network drivers
    │       └── include/linux/netdevice.h etc.
    │
    ├── bpf-next tree (Alexei Starovoitov / Daniel Borkmann)
    │       └── kernel/bpf/  — BPF verifier, core
    │       └── net/core/filter.c  — BPF net hooks
    │       └── tools/lib/bpf/  — libbpf
    │
    └── (many other subsystem trees: mm, fs, sched, etc.)

GitHub mirror (READ-ONLY reference):
    https://github.com/torvalds/linux
    ↑ NOT where patches are submitted. Email-based workflow only.
```

**Linus does NOT accept GitHub pull requests.**
Everything goes through mailing lists.

---

## Day-to-Day Developer Workflow

### Step 1: Get the right tree

```bash
# For eBPF changes: bpf-next tree
git clone git://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git
cd bpf-next

# For net subsystem changes: net-next tree
git clone git://git.kernel.org/pub/scm/linux/kernel/git/netdev/net-next.git

# Linus's mainline (for reading, not for patches usually):
git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

# GitHub mirror (same content, convenient for browsing):
git clone https://github.com/torvalds/linux.git
```

### Step 2: Set up your development environment

```bash
# Configure kernel with BPF + net debugging options
cd bpf-next
make defconfig
./scripts/config -e CONFIG_BPF
./scripts/config -e CONFIG_BPF_SYSCALL
./scripts/config -e CONFIG_DEBUG_INFO_BTF
./scripts/config -e CONFIG_DEBUG_KERNEL
./scripts/config -e CONFIG_PROVE_LOCKING      # detects deadlocks
./scripts/config -e CONFIG_DEBUG_ATOMIC_SLEEP  # catches sleep-in-atomic
./scripts/config -e CONFIG_KASAN              # AddressSanitizer for kernel
./scripts/config -e CONFIG_KCSAN              # data race detector
make olddefconfig

# Build (use ccache for faster rebuilds)
make -j$(nproc) CC="ccache gcc"
```

### Step 3: Write your change

```bash
# Always work on a branch
git checkout -b my-xdp-improvement

# Make your change to the relevant file
# For BPF/XDP: typically in net/core/filter.c, kernel/bpf/verifier.c,
#              or samples/bpf/ or tools/testing/selftests/bpf/

vim net/core/filter.c
```

### Step 4: Run the kernel selftests (MANDATORY before submitting)

```bash
# Build and run eBPF selftests
cd tools/testing/selftests/bpf
make -j$(nproc)
sudo ./test_progs -t xdp          # run XDP-related tests
sudo ./test_progs -v              # verbose — all tests

# Run specific tests
sudo ./test_progs -t xdp_bonding
sudo ./test_progs -t tc_redirect

# Network selftests
cd tools/testing/selftests/net
make
sudo bash fcnal-test.sh           # functional net tests
```

### Step 5: Check your code style

```bash
# The kernel has strict style rules (see Documentation/process/coding-style.rst)
./scripts/checkpatch.pl --strict my-patch.patch

# Fix common issues automatically:
./scripts/clang-format.py -i <file>   # for C files
```

### Step 6: Generate the patch

```bash
# Commit message format (CRITICAL — maintainers are strict):
git commit -s   # -s adds your Signed-off-by line (legally required)

# Commit message template:
# ┌────────────────────────────────────────────────────────────────┐
# │ bpf: xdp: fix bounds check for variable-length headers         │
# │                                                                │
# │ When parsing IPv4 options, the current code uses a fixed 20-   │
# │ byte offset without accounting for the IHL field. This causes  │
# │ the verifier to reject programs that access bytes beyond the   │
# │ minimum IP header when IHL > 5.                                │
# │                                                                │
# │ Fix this by using ihl * 4 as the dynamic offset, consistent    │
# │ with how the network stack handles variable-length IP headers. │
# │                                                                │
# │ Fixes: abc1234 ("bpf: add XDP metadata support")              │
# │ Signed-off-by: Your Name <you@example.com>                     │
# └────────────────────────────────────────────────────────────────┘

# Generate patch file(s)
git format-patch -1 HEAD              # single patch
git format-patch -3 HEAD              # last 3 commits as patch series
git format-patch --cover-letter -3    # add cover letter for series
```

### Step 7: Find the right maintainers

```bash
# This is critical — sending to wrong list = patch ignored
./scripts/get_maintainer.pl my-patch.patch

# Example output:
# Alexei Starovoitov <ast@kernel.org> (maintainer:BPF)
# Daniel Borkmann <daniel@iogearbox.net> (maintainer:BPF)
# bpf@vger.kernel.org (open list:BPF)
# netdev@vger.kernel.org (open list:NETWORKING)
# linux-kernel@vger.kernel.org (open list)
```

### Step 8: Send the patch via email

```bash
# Configure git send-email
git config --global sendemail.smtpserver  smtp.gmail.com
git config --global sendemail.smtpserverport 587
git config --global sendemail.smtpencryption tls
git config --global sendemail.smtpuser you@gmail.com

# Send it
git send-email \
    --to="bpf@vger.kernel.org" \
    --cc="ast@kernel.org" \
    --cc="daniel@iogearbox.net" \
    --cc="netdev@vger.kernel.org" \
    my-patch.patch

# For a series:
git send-email \
    --to="bpf@vger.kernel.org" \
    --cc="ast@kernel.org" \
    --annotate \           # lets you add per-patch notes
    *.patch
```

### Step 9: Respond to review feedback

- Reply inline to reviewer comments in your email client
- If changes requested: amend commit + resend with `[PATCH v2]`
- Version history goes at the bottom of the commit message, after `---`

### Step 10: Acceptance flow

```
Your patch → bpf-next tree (Alexei/Daniel) → Linus's tree (merge window)
                                              ↑
                           Takes 1-3 kernel cycles (6-12 weeks)
```

---

## Important Mailing Lists

| List | Purpose | Subscribe |
|------|---------|-----------|
| bpf@vger.kernel.org | eBPF patches | https://vger.kernel.org |
| netdev@vger.kernel.org | Net subsystem patches | https://vger.kernel.org |
| linux-kernel@vger.kernel.org | Everything | https://vger.kernel.org |

## Archive search (CRITICAL for researching prior art):
- https://lore.kernel.org/bpf/
- https://lore.kernel.org/netdev/
- https://patchwork.kernel.org/project/netdevbpf/list/

---

## Key Source Files to Read

For eBPF + net:
```
kernel/bpf/verifier.c     ← The verifier (10k+ lines, read carefully)
kernel/bpf/core.c         ← BPF interpreter + JIT
net/core/filter.c         ← BPF network hooks, XDP core
net/core/dev.c            ← netdevice_notifier, NAPI, skb processing
net/netfilter/core.c      ← Netfilter hook registration
include/linux/bpf.h       ← BPF types, map types, prog types
include/uapi/linux/bpf.h  ← Userspace-facing BPF API
include/linux/netdevice.h ← net_device struct (read this carefully!)
include/linux/skbuff.h    ← sk_buff struct (the most important struct in net)
```

---

## The sk_buff (socket buffer) — Most Important Net Struct

```c
// sk_buff is the kernel's representation of a network packet.
// Every packet traverses the stack as an sk_buff.
// Understanding its layout is mandatory for net kernel work.

struct sk_buff {
    // Packet boundaries
    unsigned char   *head;      // start of allocated buffer
    unsigned char   *data;      // start of packet data (L2 header)
    unsigned char   *tail;      // end of packet data
    unsigned char   *end;       // end of allocated buffer

    // Header pointers (set by each layer as packet traverses stack)
    // Access via: skb_mac_header(), skb_network_header(), skb_transport_header()

    // Metadata
    __u32            len;       // length of packet data
    __u16            protocol;  // L3 protocol (ETH_P_IP, etc.)
    __u8             pkt_type;  // PACKET_HOST, PACKET_BROADCAST, etc.

    // Device
    struct net_device *dev;     // interface packet arrived on (or goes out on)

    // Routing
    struct dst_entry *_skb_refdst; // routing destination cache entry

    // Connection tracking
    struct nf_conntrack *nfct;  // netfilter connection track entry

    // ... 300+ more fields
};
```