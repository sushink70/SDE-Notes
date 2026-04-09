# Makefile — net_monitor Linux kernel module
#
# ─── Concepts ─────────────────────────────────────────────────────────────
#
# Kbuild is the kernel's build system. For external (out-of-tree) modules
# you invoke it in two phases:
#
#   Phase 1: make runs in YOUR directory, sets M=$(PWD), then calls
#            make -C $(KDIR) which enters the kernel source tree.
#
#   Phase 2: The kernel's top-level Makefile recurses back into M=$(PWD)
#            and reads THIS file again, this time as a Kbuild makefile
#            to build the objects listed in obj-m.
#
# obj-m  := foo.o          — build foo.c as a loadable module (foo.ko)
# obj-y  := foo.o          — build foo.c into the kernel image (vmlinux)
# foo-y  := a.o b.o        — build foo.ko from a.c + b.c (multi-file)
#
# ─── For Linus's kernel tree ──────────────────────────────────────────────
#
# Clone the tree:
#   git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
#
# Build a config:
#   cd linux && make defconfig
#   make menuconfig   # enable CONFIG_NETFILTER, CONFIG_IP_NF_FILTER
#
# Build the kernel and modules:
#   make -j$(nproc)
#   make modules_install
#   make install        # updates grub / boot
#
# Then point KDIR here:
#   KDIR=/path/to/linux make
#
# ─── Out-of-tree build (default, against running kernel) ──────────────────

obj-m := net_monitor.o

# KDIR: kernel headers for the *running* kernel.
# For cross-compilation:  KDIR=/path/to/cross-build/linux ARCH=arm64
KDIR  ?= /lib/modules/$(shell uname -r)/build
PWD   := $(shell pwd)

# EXTRA_CFLAGS:
#   -DDEBUG     — enables pr_debug() output (visible via dmesg -l debug)
#   -g          — DWARF debug info for kgdb / crash analysis
#   -Werror     — treat warnings as errors (recommended for upstream patches)
#   -DKBUILD_MODNAME=\"net_monitor\"  — auto-set by Kbuild, listed for clarity
EXTRA_CFLAGS += -DDEBUG -g -Werror

# ── Targets ────────────────────────────────────────────────────────────────

.PHONY: all clean install sparse cppcheck

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# Install into /lib/modules/$(uname -r)/extra/ and regenerate depmod database
install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a
	@echo "Module installed. Load with: sudo modprobe net_monitor"

# ── Static analysis ────────────────────────────────────────────────────────

# Sparse: the kernel's own static analyser. Checks __be32 vs unsigned int,
# __user pointer misuse, RCU annotations, etc.
# Install: apt install sparse  OR  build from kernel tools/sparse
sparse:
	$(MAKE) -C $(KDIR) M=$(PWD) C=1 CF="-D__CHECK_ENDIAN__" modules

# Cppcheck: general C static analyser, good for logic bugs
cppcheck:
	cppcheck --enable=all --suppress=missingInclude \
	         --include=/lib/modules/$(shell uname -r)/build/include \
	         net_monitor.c

# ── In-tree build instructions ─────────────────────────────────────────────
# To build net_monitor as part of Linus's kernel tree:
#
# 1. Copy net_monitor.c to:  drivers/net/net_monitor.c
#    OR to:                   net/netfilter/net_monitor.c
#
# 2. Add to the appropriate Kconfig (e.g., drivers/net/Kconfig):
#
#    config NET_MONITOR
#        tristate "Network packet monitor (educational)"
#        depends on NETFILTER && IP_NF_FILTER
#        help
#          A netfilter-based IPv4 packet monitor for learning purposes.
#          If unsure, say N.
#
# 3. Add to the Makefile in that directory:
#    obj-$(CONFIG_NET_MONITOR) += net_monitor.o
#
# 4. Run make menuconfig, enable it as M (module), then:
#    make -j$(nproc) M=drivers/net modules
