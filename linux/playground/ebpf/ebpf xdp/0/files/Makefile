# SPDX-License-Identifier: GPL-2.0
# Makefile — xdp-filter (C/libbpf build)
#
# Prerequisites:
#   apt install -y clang llvm libelf-dev libbpf-dev linux-headers-$(uname -r) \
#                  bpftool iproute2 linux-tools-$(uname -r)
#
# Layout:
#   kernel/xdp_filter.bpf.c     → xdp_filter.bpf.o  → skeleton header
#   userspace/xdp_filter.c      → xdp_filter (binary)
#
# Targets:
#   make all         build BPF object + skeleton + userspace binary
#   make vmlinux     generate vmlinux.h from running kernel BTF
#   make clean       remove build artifacts
#   make load        attach XDP to IFACE (default: eth0)
#   make unload      detach XDP from IFACE
#   make test        run network test suite (requires root)

CLANG       ?= clang
LLC         ?= llc
BPFTOOL     ?= bpftool
CC          ?= gcc

IFACE       ?= eth0
KERNEL_HDR  ?= /usr/include/x86_64-linux-gnu
ARCH        := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')

BPF_CFLAGS  := -O2 -g -Wall -target bpf \
               -D__TARGET_ARCH_$(ARCH)   \
               -I$(KERNEL_HDR)           \
               -Ikernel                  \
               -mcpu=v3                  \
               -fno-stack-protector

USR_CFLAGS  := -O2 -g -Wall -Iuserspace -Ikernel
LDFLAGS     := -lbpf -lelf -lz

.PHONY: all vmlinux clean load unload test fmt

all: kernel/vmlinux.h userspace/xdp_filter.skel.h userspace/xdp_filter

# ── 1. Generate vmlinux.h from running kernel BTF ─────────────────────────
kernel/vmlinux.h:
	@echo "[BTF] Generating vmlinux.h from /sys/kernel/btf/vmlinux"
	$(BPFTOOL) btf dump file /sys/kernel/btf/vmlinux format c > $@

# ── 2. Compile BPF kernel-side object ─────────────────────────────────────
kernel/xdp_filter.bpf.o: kernel/xdp_filter.bpf.c kernel/vmlinux.h
	@echo "[BPF] Compiling $<"
	$(CLANG) $(BPF_CFLAGS) -c $< -o $@
	@echo "[BPF] Verifying BTF in object:"
	$(BPFTOOL) prog load $@ /sys/fs/bpf/_test_load 2>/dev/null && \
	    rm -f /sys/fs/bpf/_test_load || true

# ── 3. Generate libbpf skeleton header ────────────────────────────────────
userspace/xdp_filter.skel.h: kernel/xdp_filter.bpf.o
	@echo "[SKEL] Generating skeleton header"
	$(BPFTOOL) gen skeleton $< > $@

# ── 4. Build userspace loader ──────────────────────────────────────────────
userspace/xdp_filter: userspace/xdp_filter.c userspace/xdp_filter.skel.h
	@echo "[CC] Compiling userspace loader"
	$(CC) $(USR_CFLAGS) $< -o $@ $(LDFLAGS)

# ── Compile BUGGY version (for training) ─────────────────────────────────
buggy: kernel/vmlinux.h
	@echo "[BPF] Compiling BUGGY version (expect warnings/errors)"
	$(CLANG) $(BPF_CFLAGS) -Wno-parentheses \
	    -c kernel/xdp_filter.bpf.BUGGY.c \
	    -o kernel/xdp_filter.bpf.BUGGY.o 2>&1 || true
	@echo "[BPF] Checking verifier rejection for buggy object:"
	$(BPFTOOL) prog load kernel/xdp_filter.bpf.BUGGY.o \
	    /sys/fs/bpf/_test_buggy 2>&1 || true

# ── Attach XDP program ─────────────────────────────────────────────────────
load: userspace/xdp_filter
	@echo "[LOAD] Attaching XDP to $(IFACE)"
	sudo ./userspace/xdp_filter --iface $(IFACE) --stats &

# ── Detach XDP program ─────────────────────────────────────────────────────
unload:
	@echo "[UNLOAD] Detaching XDP from $(IFACE)"
	sudo ip link set $(IFACE) xdp off

# ── Format BPF C code (kernel coding style) ───────────────────────────────
fmt:
	clang-format --style=file kernel/xdp_filter.bpf.c

# ── Run tests ─────────────────────────────────────────────────────────────
test:
	sudo bash scripts/test.sh $(IFACE)

clean:
	rm -f kernel/vmlinux.h kernel/*.o
	rm -f userspace/xdp_filter.skel.h userspace/xdp_filter
