# SPDX-License-Identifier: GPL-2.0-only
#
# Makefile for out-of-tree kernel module build
#
# Usage:
#   make              — build .ko for running kernel
#   make KDIR=...     — build against custom kernel tree
#   make clean        — clean build artefacts
#   make check        — run checkpatch + sparse
#   make coccicheck   — run coccinelle semantic patches
#   make tags         — generate ctags for the module sources
#
# Variable conventions (Documentation/kbuild/makefiles.rst):
#   KDIR    = path to the kernel source / build dir
#   M       = path to the module directory (passed to kernel Makefile)
#   ARCH    = target architecture (default = host)
#   CROSS_COMPILE = toolchain prefix (e.g. aarch64-linux-gnu-)

KDIR    ?= /lib/modules/$(shell uname -r)/build
M       := $(shell pwd)
SOURCES := nf_pkt_inspector.c nf_pkt_inspector_buggy.c

# Default target: invoke kernel Kbuild machinery
.PHONY: all
all:
	$(MAKE) -C $(KDIR) M=$(M) modules

# Clean: kernel Kbuild knows what to remove
.PHONY: clean
clean:
	$(MAKE) -C $(KDIR) M=$(M) clean

# Install .ko into /lib/modules (optional, needs root)
.PHONY: install
install:
	$(MAKE) -C $(KDIR) M=$(M) modules_install
	depmod -a

# ── static analysis targets ──────────────────────────────────────────────────

# checkpatch: kernel coding style checker
# scripts/checkpatch.pl lives in the kernel source tree
.PHONY: check
check:
	$(KDIR)/scripts/checkpatch.pl --no-tree -f $(SOURCES)

# sparse: C semantic checker (install: apt install sparse)
# C=1 runs sparse on files that are recompiled
# C=2 runs sparse on ALL files
.PHONY: sparse
sparse:
	$(MAKE) -C $(KDIR) M=$(M) C=2 CF="-D__CHECK_ENDIAN__ -Wbitwise -Wno-transparent-union" modules

# smatch: deeper semantic checker (apt install smatch)
.PHONY: smatch
smatch:
	$(MAKE) -C $(KDIR) M=$(M) CHECK="smatch -p=kernel" C=1 modules

# coccinelle semantic patches — requires coccinelle (apt install coccinelle)
# The kernel ships cocci scripts under scripts/coccinelle/
.PHONY: coccicheck
coccicheck:
	$(MAKE) -C $(KDIR) M=$(M) coccicheck MODE=report

# Generate ctags for editor navigation
.PHONY: tags
tags:
	ctags -R --c-kinds=+p --fields=+iaS --extras=+q $(SOURCES)

# ── load / unload helpers (run as root on test VM) ───────────────────────────

.PHONY: load
load:
	sudo insmod nf_pkt_inspector.ko drop_port=0
	sleep 0.2
	dmesg | tail -5

.PHONY: load-buggy
load-buggy:
	sudo insmod nf_pkt_inspector_buggy.ko
	sleep 0.2
	dmesg | tail -5

.PHONY: unload
unload:
	-sudo rmmod nf_pkt_inspector
	-sudo rmmod nf_pkt_inspector_buggy

.PHONY: status
status:
	lsmod | grep nf_pkt || echo "module not loaded"
	-cat /proc/net/nf_pkt_inspector

# cross-compile example (ARM64)
.PHONY: arm64
arm64:
	$(MAKE) -C $(KDIR) M=$(M) ARCH=arm64 \
		CROSS_COMPILE=aarch64-linux-gnu- modules
