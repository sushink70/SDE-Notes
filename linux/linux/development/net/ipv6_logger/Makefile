# Makefile — nl_ipv6_logger kernel module
#
# Usage:
#   make              — build the .ko against the running kernel
#   make clean        — remove build artefacts
#   make load         — insmod (requires root / sudo)
#   make unload       — rmmod  (requires root / sudo)
#   make watch        — tail dmesg for our tag (requires root / sudo)
#
# Override KDIR to cross-compile:
#   make KDIR=/path/to/kernel/build

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD  := $(shell pwd)

# The object that kbuild will compile
obj-m := nl_ipv6_logger.o

# ── Standard targets ─────────────────────────────────────────────────────

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# ── Convenience targets (need root) ──────────────────────────────────────

load: all
	sudo insmod nl_ipv6_logger.ko

load-verbose: all
	sudo insmod nl_ipv6_logger.ko rate_limit=0 log_l4=1

unload:
	sudo rmmod nl_ipv6_logger

watch:
	sudo dmesg -w | grep --line-buffered '\[NL-IPV6-'

reload: unload load

.PHONY: all clean load load-verbose unload watch reload
