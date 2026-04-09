# Outer Makefile — drives out-of-tree kbuild
# Usage:
#   make                 — build against running kernel
#   make KDIR=/path/to/source  — build against specific kernel tree
#   make clean
#   make sparse          — run C sparse checker
#   make coccicheck      — run coccinelle semantic patches

KDIR     ?= /lib/modules/$(shell uname -r)/build
PWD      := $(shell pwd)
SUBDIR   := $(PWD)/security

# Pass Kconfig symbols on the command line for out-of-tree builds
KBUILD_EXTRA_SYMBOLS :=
EXTRA_CFLAGS := -DDEBUG        # enable pr_debug() output during development

# Default target
all:
	$(MAKE) -C $(KDIR) M=$(SUBDIR) \
		CONFIG_SECURITY_AUDITSEC=m \
		modules

fixed:
	$(MAKE) -C $(KDIR) M=$(SUBDIR) \
		CONFIG_SECURITY_AUDITSEC_FIXED=m \
		modules

clean:
	$(MAKE) -C $(KDIR) M=$(SUBDIR) clean
	find . -name "*.o" -o -name "*.ko" -o -name "*.mod.*" | xargs rm -f

# Static analysis — requires sparse package
# Install: apt install sparse
sparse:
	$(MAKE) -C $(KDIR) M=$(SUBDIR) \
		CONFIG_SECURITY_AUDITSEC=m \
		C=2 CF="-D__CHECK_ENDIAN__ -Wsparse-all" \
		modules

# Coccinelle semantic patch check — requires coccinelle/spatch
# Install: apt install coccinelle
# Kernel cocci scripts: scripts/coccinelle/
coccicheck:
	$(MAKE) -C $(KDIR) M=$(SUBDIR) coccicheck \
		MODE=report \
		COCCI=$(KDIR)/scripts/coccinelle/null/

# checkpatch.pl — kernel coding style linter
checkpatch:
	$(KDIR)/scripts/checkpatch.pl --no-tree \
		--ignore SPDX_LICENSE_TAG \
		security/auditsec.c

# dtags — generate compile_commands.json for clangd/LSP
compile_commands:
	$(MAKE) -C $(KDIR) M=$(SUBDIR) \
		CONFIG_SECURITY_AUDITSEC=m \
		compile_commands.json

.PHONY: all fixed clean sparse coccicheck checkpatch compile_commands
