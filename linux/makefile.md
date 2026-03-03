# Makefile: Comprehensive Guide for Linux Kernel Developers

## 1. What is a Makefile?

A **Makefile** is a build automation script interpreted by GNU Make (`make`). It describes:
- **What** to build (targets)
- **From what** (prerequisites/dependencies)
- **How** to build it (recipes/rules)

Make uses **dependency graphs** + **timestamp comparison** to only rebuild what's stale — it's fundamentally a DAG executor.

```
                        ┌─────────────────────────────────────┐
                        │           GNU Make Engine            │
                        │                                      │
   Makefile  ──────────>│  1. Parse rules & variables          │
   (rules)              │  2. Build dependency DAG             │
                        │  3. Compare mtime(target) vs prereqs │
   File system ────────>│  4. Execute stale recipes            │──> Build artifacts
   (timestamps)         │                                      │
                        └─────────────────────────────────────┘

   DAG Example:
   vmlinux ──┬── init/built-in.a ──── init/main.o ──── init/main.c
             ├── kernel/built-in.a
             ├── mm/built-in.a ─────── mm/slub.o ────── mm/slub.c
             └── arch/x86/built-in.a                        │
                                                    (recompile only if
                                                     slub.c changed)
```

---

## 2. Anatomy of a Makefile Rule

```makefile
# Syntax:
target: prerequisites
<TAB>recipe
<TAB>recipe
```

> ⚠️ Recipes **must** be indented with a **real TAB** (`\t`), not spaces. This is the #1 beginner mistake.

```makefile
# Concrete example:
foo.o: foo.c foo.h
	$(CC) -c -o $@ $
#        ↑        ↑  ↑
#        compiler  |  first prerequisite (foo.c)
#                  output target ($@)
```

### Automatic Variables (critical to internalize)

| Variable | Meaning |
|----------|---------|
| `$@` | Target name |
| `$<` | First prerequisite |
| `$^` | All prerequisites (deduplicated) |
| `$?` | Prerequisites newer than target |
| `$*` | Stem of pattern rule match |
| `$(@D)` | Directory part of `$@` |
| `$(@F)` | File part of `$@` |

---

## 3. Variable System

```makefile
# Assignment flavors — this matters a lot:
CC      := gcc          # Simply expanded (evaluated immediately, like C const)
CFLAGS   = -Wall        # Recursively expanded (evaluated at USE time — lazy)
LDFLAGS ?= -lm          # Set only if not already defined
CFLAGS  += -O2          # Append

# Recursively expanded pitfall:
X = foo
X = $(X) bar            # INFINITE LOOP! Use := to avoid this.

# Target-specific variables:
debug: CFLAGS += -g -DDEBUG
debug: foo

# Automatic variable in multi-target context:
%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $
```

### Variable Precedence (high → low)
```
Command line  >  override directive  >  Makefile  >  environment  >  default rules
make CFLAGS="-O3"    # overrides Makefile CFLAGS
```

---

## 4. Pattern Rules & Implicit Rules

```makefile
# Pattern rule: % is the stem wildcard
%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $

%.o: %.S
	$(AS) $(ASFLAGS) -o $@ $

# Static pattern rule (restricts which targets):
OBJS := foo.o bar.o baz.o
$(OBJS): %.o: %.c
	$(CC) -c -o $@ $

# Chained pattern rules (make handles intermediates):
# .c -> .o -> .so automatically chained
```

GNU Make has **built-in implicit rules** you can view with:
```bash
make -p | grep -A2 "%.o:"
```

Disable them for hygiene:
```makefile
MAKEFLAGS += --no-builtin-rules
.SUFFIXES:        # Clear suffix rules
```

---

## 5. Functions

```makefile
SRC_DIR := src
SRCS    := $(wildcard $(SRC_DIR)/*.c)           # glob
OBJS    := $(patsubst %.c,%.o,$(SRCS))          # pattern substitution
OBJS    := $(SRCS:.c=.o)                        # shorthand equivalent
NAMES   := $(notdir $(SRCS))                    # strip directory
DIRS    := $(sort $(dir $(SRCS)))               # unique directories
FILTERED:= $(filter-out main.c,$(SRCS))        # exclusion

# String functions:
$(subst from,to,text)
$(strip string)
$(words list)           # count
$(word n,list)          # nth element
$(firstword list)
$(lastword list)

# Shell function (executes at parse time with :=):
KERNEL_VERSION := $(shell uname -r)
GIT_HASH       := $(shell git rev-parse --short HEAD)

# foreach:
MODULES := net mm fs
CLEAN_TARGETS := $(foreach m,$(MODULES),clean-$(m))

# call — user-defined functions:
define cc_flags
$(CC) -I$(1)/include -L$(1)/lib
endef

result := $(call cc_flags,/usr/local)

# if/or/and:
DEBUG ?= 0
CFLAGS += $(if $(filter 1,$(DEBUG)),-g -DDEBUG,)
```

---

## 6. Phony Targets & Special Targets

```makefile
# .PHONY: targets that are always "out of date" (never real files)
.PHONY: all clean install check distclean

all: vmlinux modules

clean:
	rm -rf $(OBJS) $(TARGET)

install: all
	install -m755 $(TARGET) /usr/local/bin/

# .DEFAULT_GOAL: what 'make' alone builds
.DEFAULT_GOAL := all

# .SECONDARY: prevent deletion of intermediate files
.SECONDARY: $(OBJS)

# .DELETE_ON_ERROR: delete target if recipe fails (ALWAYS use this)
.DELETE_ON_ERROR:

# .SUFFIXES: controls implicit suffix rules
.SUFFIXES:

# Order-only prerequisites (rebuild if missing but not if stale):
output/foo.o: foo.c | output/
	$(CC) -c -o $@ $

output/:
	mkdir -p $@
```

---

## 7. Conditionals & Include

```makefile
# ifeq/ifneq/ifdef/ifndef
ifeq ($(ARCH),arm64)
    CROSS_COMPILE := aarch64-linux-gnu-
else ifeq ($(ARCH),riscv)
    CROSS_COMPILE := riscv64-linux-gnu-
else
    CROSS_COMPILE :=
endif

ifdef CONFIG_DEBUG_INFO
    CFLAGS += -g
endif

# Include other makefiles:
include scripts/Makefile.lib
-include .config          # dash = don't error if missing (like kernel's .config)
include $(wildcard *.d)   # include all dep files
```

---

## 8. Automatic Dependency Generation

A critical technique used by the kernel — avoid manual header tracking:

```makefile
DEPDIR := .deps
DEPFLAGS = -MT $@ -MMD -MP -MF $(DEPDIR)/$*.d

%.o: %.c $(DEPDIR)/%.d | $(DEPDIR)
	$(CC) $(DEPFLAGS) $(CFLAGS) -c -o $@ $

$(DEPDIR): ; mkdir -p $@

# Include generated .d files (silently if missing on first build):
DEPFILES := $(OBJS:%.o=$(DEPDIR)/%.d)
$(DEPFILES):
-include $(DEPFILES)
```

GCC `-MMD -MP -MF` generates `.d` files like:
```makefile
# .deps/foo.d (auto-generated):
foo.o: foo.c include/foo.h include/bar.h
include/foo.h:
include/bar.h:
```

---

## 9. Multi-Directory Recursive vs Non-Recursive Builds

### Recursive (classic, fragile — what kernel does NOT prefer internally):
```makefile
SUBDIRS := mm fs net

all:
	$(foreach dir,$(SUBDIRS),$(MAKE) -C $(dir) all;)
```

### Non-Recursive (kbuild style — what kernel actually does):
```makefile
# Top-level Makefile includes sub-makefiles:
include mm/Makefile
include fs/Makefile
include net/Makefile

# Each sub-Makefile just appends to variables:
# mm/Makefile:
obj-y += slub.o page_alloc.o vmalloc.o
```

This is exactly how **kbuild** works.

---

## 10. kbuild — The Linux Kernel's Makefile System

The kernel's build system lives in:
```
scripts/
├── Makefile.build       # Core build logic for obj-y/obj-m
├── Makefile.lib         # Utility functions
├── Makefile.host        # Host tool compilation
├── Makefile.modinst     # Module installation
├── Kbuild.include       # Shared kbuild macros
└── basic/               # Very early bootstrap rules

arch/x86/Makefile         # Arch-specific overrides
```

### How kbuild Processes a Subsystem Makefile

```
make vmlinux
  │
  ├── Reads top-level Makefile
  │     sets ARCH, CROSS_COMPILE, KBUILD_CFLAGS...
  │
  ├── Includes arch/$(ARCH)/Makefile
  │
  ├── For each obj-y entry:
  │     $(MAKE) -f scripts/Makefile.build obj=<dir>
  │         → reads <dir>/Makefile (or Kbuild file)
  │         → compiles .o files
  │         → links into built-in.a
  │
  └── Links all built-in.a → vmlinux
```

### Writing a kbuild Makefile (for a driver):

```makefile
# drivers/char/mydev/Makefile

# Build as built-in if CONFIG_MYDEV=y, module if =m:
obj-$(CONFIG_MYDEV) += mydev.o

# Multi-file module:
obj-$(CONFIG_MYDEV_NET) += mydev_net.o
mydev_net-objs := mydev_net_core.o mydev_net_ethtool.o

# Extra CFLAGS for specific file:
CFLAGS_mydev_core.o := -DDEBUG_VERBOSE

# Extra AFLAGS for asm file:
AFLAGS_mydev_asm.o := -DENTRY_POINT

# Host program (runs on build machine):
hostprogs := gen_tables
gen_tables-objs := gen_tables.c

# Generated header dependency:
$(obj)/mydev_core.o: $(obj)/generated_table.h

$(obj)/generated_table.h: $(obj)/gen_tables
	$< > $@
```

### Kconfig → Makefile pipeline:
```
Kconfig files ──(make menuconfig)──> .config
                                        │
                              include/config/auto.conf
                                        │
                              kbuild reads CONFIG_* vars
                                        │
                              obj-$(CONFIG_FOO) resolves to obj-y or obj-m
```

---

## 11. Debugging Makefiles

```bash
# Dry run — show what WOULD be executed:
make -n

# Print database of rules and variables:
make -p 2>/dev/null | less

# Trace rule execution:
make --trace

# Debug specific target:
make -d foo.o 2>&1 | less

# Print variable value:
make print-CFLAGS     # if you define: print-%: ; @echo $* = $($*)

# Universal print rule (add to your Makefiles):
print-%:
	@echo '$* = $($*)'
	@echo '  origin: $(origin $*)'
	@echo '  flavor: $(flavor $*)'
	@echo '  value:  $(value $*)'
```

```bash
# Kernel-specific:
make V=1              # verbose — shows full gcc command lines
make V=2              # + shows reason for rebuild
make W=1              # extra warnings (sparse, checkpatch)
make C=1              # run sparse on changed files
make C=2              # run sparse on all files
```

---

## 12. Parallelism

```bash
make -j$(nproc)               # parallel jobs = CPU count
make -j$(nproc) --load-average=$(nproc)   # throttle under load

# In Makefile — never use $(MAKE) without -j inheritance:
# Wrong:
	make -C subdir

# Right (propagates jobserver):
	$(MAKE) -C subdir
```

Parallel safety rules:
- Targets that share output files must have explicit ordering (`|` order-only or `.NOTPARALLEL`)
- Never write to the same file from two recipes
- `.DELETE_ON_ERROR` is essential with `-j`

---

## 13. A Production-Quality Kernel Module Makefile

```makefile
# External module Makefile: drivers/mydriver/Makefile

# Detect if called from kbuild or standalone:
ifneq ($(KERNELRELEASE),)
# ── kbuild context ────────────────────────────────────────
obj-m := mydriver.o
mydriver-objs := core.o netdev.o ioctl.o

ccflags-y := -I$(src)/include
ccflags-y += -DDRIVER_VERSION=\"$(shell git -C $(src) describe --tags 2>/dev/null || echo unknown)\"

else
# ── Standalone context (invoked directly) ─────────────────
KDIR    ?= /lib/modules/$(shell uname -r)/build
ARCH    ?= x86_64
PWD     := $(shell pwd)

.PHONY: all clean modules_install

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

modules_install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a

# Cross-compile target:
arm64:
	$(MAKE) -C $(KDIR) M=$(PWD) ARCH=arm64 \
		CROSS_COMPILE=aarch64-linux-gnu- modules

endif
```

---

## 14. Learning Path & Resources

```
Stage 1 — Fundamentals:
  Read: GNU Make Manual (info make) — chapters 2,3,4,6,8,10
  Practice: write a Makefile for a 5-file C project from scratch

Stage 2 — Patterns:
  Read: "Recursive Make Considered Harmful" (Peter Miller, 1997)
  Practice: rewrite recursive Makefile as non-recursive

Stage 3 — kbuild:
  Read: Documentation/kbuild/makefiles.rst
        Documentation/kbuild/kbuild.rst
  Trace: make V=1 on a kernel module, read scripts/Makefile.build

Stage 4 — Mastery:
  Read: scripts/Makefile.build (every line)
  Practice: add a new subsystem with Kconfig+Makefile integration
  Audit: make -p on kernel build, understand every implicit rule
```

### Key Documentation Paths in Kernel Tree:
```
Documentation/kbuild/
├── makefiles.rst        ← primary reference
├── kbuild.rst           ← kbuild variable reference  
├── kconfig-language.rst ← Kconfig syntax
└── modules.rst          ← external module build
```

### Quick Reference Commands:
```bash
info make                           # GNU Make full manual
make --print-data-base              # all rules/variables
grep -r "obj-y" mm/Makefile         # see kernel mm objects
cat scripts/Makefile.build          # kbuild core engine
make -C /lib/modules/$(uname -r)/build help  # kernel make targets
```

The single most important insight: **Make is a lazy DAG executor driven by timestamps** — everything else (variables, functions, conditionals) exists to express that graph correctly. Once that mental model is solid, kbuild's complexity becomes navigable.