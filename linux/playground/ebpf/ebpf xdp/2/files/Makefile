# Makefile — BPF LSM Security Monitor
#
# Build targets:
#   make            — build everything (BPF object + skeleton + userspace binary)
#   make vmlinux    — regenerate vmlinux.h from running kernel BTF
#   make clean      — remove build artifacts
#   make load       — load BPF program (requires root)
#   make check      — run static analysis (clang-tidy, sparse)
#   make test       — run BPF selftests integration
#
# Dependencies:
#   clang ≥ 14, llvm, libbpf-dev ≥ 1.0, bpftool, linux-headers
#
# Reference:
#   tools/lib/bpf/Makefile
#   samples/bpf/Makefile
#   Documentation/bpf/bpf_devel_QA.rst

# ─── Toolchain ────────────────────────────────────────────────────────────────
CLANG      ?= clang
LLC        ?= llc
BPFTOOL    ?= bpftool
CC         ?= gcc
ARCH       := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')

# ─── Paths ────────────────────────────────────────────────────────────────────
SRCDIR     := .
BPF_SRC    := bpf/security_monitor.bpf.c
USR_SRC    := userspace/security_monitor.c
INCDIR     := include
BPF_OBJ    := build/security_monitor.bpf.o
SKEL_HDR   := include/security_monitor.skel.h
BINARY     := build/security_monitor
VMLINUX    := include/vmlinux.h

# ─── Flags ────────────────────────────────────────────────────────────────────
#
# BPF compilation flags:
#   -target bpf          — emit BPF bytecode (not native code)
#   -g                   — emit DWARF → BTF (needed for CO-RE, bpftool, verifier msgs)
#   -O2                  — mandatory: BPF verifier rejects non-optimised loops
#   -D__TARGET_ARCH_*    — architecture hint for BPF portability headers
#   -Wall -Wextra        — catch bugs early
#   -Wno-unused-value    — BPF_CORE_READ generates unused casts intentionally
#
BPF_CFLAGS := \
    -target bpf \
    -g \
    -O2 \
    -Wall \
    -Wextra \
    -Wno-unused-value \
    -D__TARGET_ARCH_$(ARCH) \
    -I$(INCDIR) \
    -I/usr/include/$(shell uname -m)-linux-gnu

#
# Userspace flags:
#   -lbpf                — libbpf for skeleton API, map ops, ringbuf
#   -lelf -lz            — libbpf runtime deps (ELF parsing, zlib for BTF)
#   -fsanitize=address   — enable for development; remove for production builds
#   -fstack-protector-strong — exploit mitigation
#
USR_CFLAGS := \
    -g \
    -O2 \
    -Wall \
    -Wextra \
    -fstack-protector-strong \
    -D_FORTIFY_SOURCE=2 \
    -I$(INCDIR)

USR_LDFLAGS := \
    -lbpf \
    -lelf \
    -lz \
    -lpthread

# ─── Build targets ────────────────────────────────────────────────────────────
.PHONY: all vmlinux skeleton userspace clean load unload check test fmt

all: $(BINARY)

$(BINARY): $(BPF_OBJ) $(SKEL_HDR) $(USR_SRC)
	@mkdir -p build
	$(CC) $(USR_CFLAGS) $(USR_SRC) $(USR_LDFLAGS) -o $@
	@echo "[OK] Built: $@"

# Step 1: Compile BPF C → BPF ELF object
# -c: compile only (no link); BPF has no traditional linker step
$(BPF_OBJ): $(BPF_SRC) $(VMLINUX) $(INCDIR)/security_monitor.h
	@mkdir -p build
	$(CLANG) $(BPF_CFLAGS) -c $< -o $@
	@echo "[OK] BPF object: $@"
	@# Verify BTF is embedded (required for CO-RE)
	$(BPFTOOL) btf dump file $@ | head -5

# Step 2: Generate skeleton header from BPF object
# The skeleton encodes:
#   - map definitions as typed structs
#   - program pointers with attach/detach lifecycle
#   - open/load/attach/destroy functions
$(SKEL_HDR): $(BPF_OBJ)
	$(BPFTOOL) gen skeleton $< > $@
	@echo "[OK] Skeleton: $@"

# Regenerate vmlinux.h from the running kernel's BTF blob.
# This must match the kernel you intend to run against.
# For cross-compilation: copy /sys/kernel/btf/vmlinux from target.
vmlinux:
	@if [ ! -f /sys/kernel/btf/vmlinux ]; then \
	    echo "[ERR] /sys/kernel/btf/vmlinux missing (need CONFIG_DEBUG_INFO_BTF=y)"; \
	    exit 1; \
	fi
	$(BPFTOOL) btf dump file /sys/kernel/btf/vmlinux format c > $(VMLINUX)
	@echo "[OK] vmlinux.h regenerated ($(shell wc -l < $(VMLINUX)) lines)"

# ─── Runtime targets (root required) ──────────────────────────────────────────
load: $(BINARY)
	@[ "$$(id -u)" = "0" ] || (echo "Need root"; exit 1)
	@# Verify BPF LSM is active in lsm= boot parameter
	@grep -q bpf /sys/kernel/security/lsm 2>/dev/null || \
	    (echo "[ERR] BPF not in active LSMs. Boot with lsm=...,bpf"; exit 1)
	sudo $(BINARY)

# Unpin and cleanup if BPF objects were pinned to BPFFS
unload:
	@rm -f /sys/fs/bpf/security_monitor_*
	@echo "[OK] Unpinned"

# ─── Static analysis ──────────────────────────────────────────────────────────
check:
	@# clang-tidy on userspace code
	clang-tidy $(USR_SRC) -- $(USR_CFLAGS)
	@# sparse on BPF code (limited support for BPF target)
	@command -v sparse >/dev/null && sparse $(BPF_SRC) || true
	@# Run kernel's checkpatch.pl (for eventual upstream submission)
	@$(KERNEL_SRC)/scripts/checkpatch.pl --no-tree -f $(BPF_SRC) 2>/dev/null || true

fmt:
	clang-format -i -style=kernel $(BPF_SRC) $(USR_SRC)

# ─── Tests ────────────────────────────────────────────────────────────────────
test:
	@echo "Running integration tests..."
	@$(MAKE) -C tests/ run

clean:
	rm -rf build/
	rm -f $(SKEL_HDR)
	@echo "[OK] Cleaned"
