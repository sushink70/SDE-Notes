# File: c/Makefile
#
# Builds:
#   1. eBPF kernel-side objects  (.bpf.c → .bpf.o via clang/BPF target)
#   2. Userspace loader           (loader.c → loader via gcc + libbpf)
#   3. Kernel module              (netdev_module.c → netdev_module.ko)
#
# PREREQUISITES:
#   sudo apt install -y \
#       clang llvm libelf-dev libbpf-dev linux-headers-$(uname -r) \
#       build-essential pkg-config
#
# USAGE:
#   make all          — build everything
#   make bpf          — build only eBPF objects
#   make loader       — build only userspace loader
#   make module       — build only kernel module
#   make clean        — remove all build artifacts
#   make verify       — run bpftool verifier check on BPF objects
#   make fmt          — clang-format all source files

# ─── Toolchain ───────────────────────────────────────────────────────────────

CLANG       ?= clang
LLC         ?= llc
BPFTOOL     ?= bpftool
CC          ?= gcc
KDIR        ?= /lib/modules/$(shell uname -r)/build

ARCH        := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')

# ─── Directories ─────────────────────────────────────────────────────────────

KERN_DIR    := kern
USER_DIR    := user
BUG_DIR     := bugs
OBJ_DIR     := build

$(shell mkdir -p $(OBJ_DIR))

# ─── BPF Compilation Flags ──────────────────────────────────────────────────
#
# -target bpf        : emit BPF bytecode (ELF, not native)
# -D__TARGET_ARCH_x86: selects correct CO-RE relocation offsets
# -O2                : REQUIRED — verifier is stricter on unoptimized code
# -g                 : include BTF debug info (needed for CO-RE + bpftool)
# -Wall -Wextra      : catch issues early
# -Wno-unused-value  : BPF idioms trigger this warning legitimately

BPF_CFLAGS  := -target bpf                     \
               -D__TARGET_ARCH_$(ARCH)          \
               -O2 -g -Wall -Wextra             \
               -Wno-unused-value                \
               -I/usr/include/$(shell uname -m)-linux-gnu \
               -I/usr/include

# ─── Userspace Compilation Flags ─────────────────────────────────────────────

USER_CFLAGS := -O2 -g -Wall -Wextra
USER_LDFLAGS := -lbpf -lelf -lz

# ─── Source Files ────────────────────────────────────────────────────────────

BPF_SRCS    := $(wildcard $(KERN_DIR)/*.bpf.c)
BPF_OBJS    := $(patsubst $(KERN_DIR)/%.bpf.c, $(OBJ_DIR)/%.bpf.o, $(BPF_SRCS))

BUG_SRCS    := $(wildcard $(BUG_DIR)/*.bpf.c)
BUG_OBJS    := $(patsubst $(BUG_DIR)/%.bpf.c, $(OBJ_DIR)/%.bpf.o, $(BUG_SRCS))

USER_SRCS   := $(USER_DIR)/loader.c
USER_BIN    := $(OBJ_DIR)/loader

# ─── Targets ─────────────────────────────────────────────────────────────────

.PHONY: all bpf loader module bugs verify clean fmt help

all: bpf bugs loader module

# ── BPF objects ──────────────────────────────────────────────────────────────

bpf: $(BPF_OBJS)

$(OBJ_DIR)/%.bpf.o: $(KERN_DIR)/%.bpf.c
	@echo "  CLANG  $<"
	$(CLANG) $(BPF_CFLAGS) -c $< -o $@
	@echo "  BTF    $@"
	# Dump BTF info to verify debug info is present
	$(BPFTOOL) btf dump file $@ > /dev/null 2>&1 || true

bugs: $(BUG_OBJS)

$(OBJ_DIR)/%.bpf.o: $(BUG_DIR)/%.bpf.c
	@echo "  CLANG  $< (bug demo)"
	$(CLANG) $(BPF_CFLAGS) -c $< -o $@

# ── Userspace loader ─────────────────────────────────────────────────────────

loader: $(USER_BIN)

$(USER_BIN): $(USER_SRCS)
	@echo "  CC     $<"
	$(CC) $(USER_CFLAGS) $^ -o $@ $(USER_LDFLAGS)

# ── Kernel module (uses the kernel's own Kbuild) ─────────────────────────────
#
# The kernel Kbuild system handles all the module boilerplate.
# We write a minimal Kbuild file and invoke the kernel's make.

module:
	@echo "  KBUILD netdev_module.ko"
	$(MAKE) -C $(KDIR) M=$(CURDIR)/$(KERN_DIR) \
	        src=$(CURDIR)/$(KERN_DIR) \
	        obj=$(CURDIR)/$(OBJ_DIR) \
	        modules

# Write the Kbuild file if it doesn't exist
$(KERN_DIR)/Kbuild:
	echo "obj-m += netdev_module.o" > $@

# ── Verifier check ───────────────────────────────────────────────────────────
# Loads each BPF object into a pinned path to trigger full verifier analysis.
# Shows verifier log on failure — extremely useful for debugging.

verify: $(BPF_OBJS)
	@for obj in $(BPF_OBJS); do \
	    echo "  VERIFY $$obj"; \
	    $(BPFTOOL) prog load $$obj /sys/fs/bpf/test_verify_$$(basename $$obj) \
	        2>&1 && \
	    rm -f /sys/fs/bpf/test_verify_$$(basename $$obj) && \
	    echo "    ✓ OK" || \
	    echo "    ✗ FAILED"; \
	done

# ── Format ───────────────────────────────────────────────────────────────────

fmt:
	clang-format -i $(KERN_DIR)/*.c $(USER_DIR)/*.c $(BUG_DIR)/*.c

# ── Clean ────────────────────────────────────────────────────────────────────

clean:
	rm -rf $(OBJ_DIR)
	$(MAKE) -C $(KDIR) M=$(CURDIR)/$(KERN_DIR) clean 2>/dev/null || true

# ── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo "Targets:"
	@echo "  all     - build BPF objects + loader + kernel module"
	@echo "  bpf     - build eBPF .bpf.o files only"
	@echo "  bugs    - build intentional bug demo objects"
	@echo "  loader  - build userspace loader"
	@echo "  module  - build netdev_module.ko"
	@echo "  verify  - run bpftool verifier on all BPF objects"
	@echo "  fmt     - clang-format all sources"
	@echo "  clean   - remove build artifacts"