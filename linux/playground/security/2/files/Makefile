# Makefile — Guardian LSM kernel module build file
#
# CONCEPTS:
#   obj-m: tells kbuild to build this as a loadable module (.ko file)
#          If you used obj-y, it would be compiled INTO the kernel (built-in).
#
#   KDIR: path to the kernel source tree. The kernel's build system provides
#         all the necessary headers, compiler flags, and symbol tables.
#
#   M=$(PWD): tells kbuild "build the external module in this directory"
#
#   ccflags-y: extra C compiler flags for this module.
#     -DDEBUG: enables pr_debug() calls (they are no-ops without this flag)
#     -Wall:   enable all warnings (kernel developers require warning-clean code)
#
# IMPORTANT: kernel Makefiles use TABS not spaces for recipe lines.
# If you see "missing separator" errors, your editor converted tabs to spaces.

obj-m += guardian_lsm.o

ccflags-y := -DDEBUG -Wall -Wextra

# Path to the running kernel's build tree
# Can be overridden: make KDIR=/path/to/custom/kernel
KDIR ?= /lib/modules/$(shell uname -r)/build

PWD := $(CURDIR)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# Install the module to the system
install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a   # rebuild module dependency database

# Run checkpatch.pl (kernel coding style checker)
# This is REQUIRED before any upstream submission
checkpatch:
	$(KDIR)/scripts/checkpatch.pl --no-tree -f guardian_lsm.c

# Run sparse (semantic parser — catches type errors the compiler misses)
# Example: passing a user pointer where a kernel pointer is expected
sparse:
	$(MAKE) -C $(KDIR) M=$(PWD) C=2 CF="-D__CHECK_ENDIAN__" modules

.PHONY: all clean install checkpatch sparse
