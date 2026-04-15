# ─── XDP Security System — Makefile ────────────────────────────────────────
#
# Key concepts:
#   clang    : We compile BPF programs with Clang (NOT gcc).
#              GCC cannot produce BPF ELF objects.
#   -target bpf: tells Clang to emit BPF bytecode (not x86).
#   -g       : Include BTF (BPF Type Format) debug info.
#              BTF is like DWARF but for BPF — enables CO-RE.
#   CO-RE    : Compile Once, Run Everywhere.
#              BPF programs that adapt to different kernel struct layouts
#              using BTF relocation (no need to recompile per kernel).
#   vmlinux.h: Single header with ALL kernel struct definitions.
#              Generated from: bpftool btf dump file /sys/kernel/btf/vmlinux
#              format c > vmlinux.h
#   bpftool  : Swiss-army tool for BPF introspection and skeleton gen.
#
# Prerequisites (install):
#   sudo apt install clang llvm libbpf-dev linux-headers-$(uname -r) bpftool
#   OR: sudo dnf install clang llvm libbpf-devel kernel-devel bpftool

# ─── Detect kernel version and arch ─────────────────────────────────────────
KERNEL_VERSION  := $(shell uname -r)
ARCH            := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')
KERNEL_HEADERS  := /usr/src/linux-headers-$(KERNEL_VERSION)

# ─── Tool paths ──────────────────────────────────────────────────────────────
CLANG    ?= clang
LLC      ?= llc
BPFTOOL  ?= bpftool
CC       ?= gcc

# ─── Source files ─────────────────────────────────────────────────────────
BPF_SRC    := kern/xdp_security.bpf.c
BPF_OBJ    := kern/xdp_security.bpf.o
SKEL_HDR   := user/xdp_security.skel.h
USER_SRC   := user/xdp_loader.c
USER_BIN   := xdp_loader

VMLINUX_H  := kern/vmlinux.h

# ─── Compiler flags ──────────────────────────────────────────────────────────
# BPF kernel-side flags:
BPF_CFLAGS := \
    -g \
    -O2 \
    -target bpf \
    -D__TARGET_ARCH_$(ARCH) \
    -I$(KERNEL_HEADERS)/include \
    -I/usr/include/bpf \
    -I./kern \
    -I./user \
    -Wall \
    -Wno-unused-value \
    -Wno-pointer-sign \
    -Wno-compare-distinct-pointer-types \
    -fno-stack-protector

# Userspace flags:
USER_CFLAGS := \
    -g \
    -O2 \
    -Wall \
    -I./user \
    -I/usr/include/bpf

USER_LDFLAGS := \
    -lbpf \
    -lelf \
    -lz

# ─── Build targets ────────────────────────────────────────────────────────────

.PHONY: all clean load unload test vmlinux check-tools

all: check-tools $(USER_BIN)

# Step 0: Check required tools
check-tools:
	@which $(CLANG)   > /dev/null || (echo "ERROR: clang not found" && exit 1)
	@which $(BPFTOOL) > /dev/null || (echo "ERROR: bpftool not found" && exit 1)
	@which $(CC)      > /dev/null || (echo "ERROR: gcc not found" && exit 1)
	@echo "✓ All tools found"

# Step 1: Generate vmlinux.h (kernel struct definitions for CO-RE)
# This reads the BTF blob from the running kernel.
vmlinux: $(VMLINUX_H)

$(VMLINUX_H):
	@echo "Generating vmlinux.h from running kernel BTF..."
	$(BPFTOOL) btf dump file /sys/kernel/btf/vmlinux format c > $@
	@echo "✓ vmlinux.h generated ($(shell wc -l < $@) lines)"

# Step 2: Compile BPF C → BPF ELF object
# clang emits BPF bytecode; the verifier checks this later.
$(BPF_OBJ): $(BPF_SRC) $(VMLINUX_H)
	@echo "Compiling BPF kernel program..."
	$(CLANG) $(BPF_CFLAGS) -c $< -o $@
	@echo "✓ BPF object: $@"
	@# Show the BPF program sections in the ELF:
	@$(BPFTOOL) prog dump xlated obj $@ 2>/dev/null || true

# Step 3: Generate skeleton header from BPF ELF
# The skeleton provides type-safe C wrappers for maps and programs.
$(SKEL_HDR): $(BPF_OBJ)
	@echo "Generating BPF skeleton header..."
	$(BPFTOOL) gen skeleton $< > $@
	@echo "✓ Skeleton: $@"

# Step 4: Compile userspace loader
$(USER_BIN): $(USER_SRC) $(SKEL_HDR)
	@echo "Compiling userspace loader..."
	$(CC) $(USER_CFLAGS) $< -o $@ $(USER_LDFLAGS)
	@echo "✓ Loader binary: $@"

# ─── Load / Unload helpers ────────────────────────────────────────────────────
IFACE ?= eth0

load: $(USER_BIN)
	@echo "Loading XDP security on interface $(IFACE)..."
	sudo ./$(USER_BIN) $(IFACE)

# Load in generic (SKB) mode — works on any driver, slower
load-skb: $(USER_BIN)
	sudo ./$(USER_BIN) $(IFACE) --mode skb

unload:
	@echo "Detaching XDP from $(IFACE)..."
	sudo ip link set $(IFACE) xdp off

# ─── Debug helpers ────────────────────────────────────────────────────────────

# Dump loaded BPF programs
bpf-progs:
	sudo $(BPFTOOL) prog show

# Dump all BPF maps
bpf-maps:
	sudo $(BPFTOOL) map show

# Dump blocklist map contents
dump-blocklist:
	sudo $(BPFTOOL) map dump name ip_blocklist

# Show XDP program attached to interface
show-xdp:
	sudo $(BPFTOOL) net show dev $(IFACE)

# Trace bpf_printk output (requires root)
trace:
	sudo cat /sys/kernel/debug/tracing/trace_pipe

# Disassemble BPF bytecode (inspect what the JIT sees)
disasm: $(BPF_OBJ)
	$(BPFTOOL) prog dump xlated obj $(BPF_OBJ) visual 2>/dev/null || \
	$(LLVM_OBJDUMP) -d $(BPF_OBJ)

# ─── Testing ──────────────────────────────────────────────────────────────────
test:
	@echo "Running XDP tests..."
	cd tests && ./run_tests.sh

# ─── Cleanup ──────────────────────────────────────────────────────────────────
clean:
	rm -f $(BPF_OBJ) $(SKEL_HDR) $(USER_BIN)
	@echo "✓ Cleaned"

# ─── Install libbpf from source (if distro version is old) ───────────────────
libbpf-install:
	git clone --depth 1 https://github.com/libbpf/libbpf.git /tmp/libbpf
	cd /tmp/libbpf/src && make && sudo make install
	sudo ldconfig
