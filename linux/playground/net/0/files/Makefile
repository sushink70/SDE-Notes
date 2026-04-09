# =============================================================================
# Makefile — drivers/net/edu_net/Makefile
# In-tree build: invoked by Kbuild when CONFIG_EDU_NET=m|y
# =============================================================================

# C module
obj-$(CONFIG_EDU_NET) += edu_net.o
edu_net-y              := c/edu_net.o

# Buggy variant (always built as module for debugging exercises)
# obj-m                += edu_net_buggy.o  # uncomment to build buggy version

# Rust module
obj-$(CONFIG_EDU_NET_RS) += edu_net_rs.o
edu_net_rs-y             := rust/lib.o


# =============================================================================
# out-of-tree Makefile — use when developing OUTSIDE the kernel tree.
# Place this file at the root of your module directory.
# Usage:
#   make KDIR=/path/to/kernel/source         # default: /lib/modules/$(uname -r)/build
#   make KDIR=... clean
#   make KDIR=... modules_install
# =============================================================================

KDIR    ?= /lib/modules/$(shell uname -r)/build
PWD     := $(shell pwd)

# Cross-compile example:
# ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- make KDIR=...
ARCH           ?= $(shell uname -m | sed 's/x86_64/x86/')
CROSS_COMPILE  ?=

# Extra CFLAGS for debugging: enable -DDEBUG, KASAN, etc.
# ccflags-y := -DDEBUG -g

.PHONY: all clean modules_install

all:
	$(MAKE) -C $(KDIR) M=$(PWD) \
	    ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) \
	    modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

modules_install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a

# Build with KASAN (address sanitizer) — requires kernel built with CONFIG_KASAN=y
kasan:
	$(MAKE) -C $(KDIR) M=$(PWD) \
	    KCFLAGS="-fsanitize=kernel-address" modules

# Build with UBSAN
ubsan:
	$(MAKE) -C $(KDIR) M=$(PWD) \
	    KCFLAGS="-fsanitize=undefined" modules
