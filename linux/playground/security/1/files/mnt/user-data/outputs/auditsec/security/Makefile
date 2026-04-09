# security/auditsec/Makefile
#
# Kernel build system (kbuild) integration.
# Documentation: Documentation/kbuild/makefiles.rst
#
# Usage (out-of-tree, for development):
#   make -C /lib/modules/$(uname -r)/build   \
#        M=$(pwd)/security/auditsec           \
#        CONFIG_SECURITY_AUDITSEC=m           \
#        modules
#
# Usage (in-tree, after placing under security/auditsec/):
#   make menuconfig  →  Security options → auditsec LSM
#   make modules
#
# Clean:
#   make -C /lib/modules/$(uname -r)/build M=$(pwd)/security/auditsec clean

obj-$(CONFIG_SECURITY_AUDITSEC)      += auditsec.o
obj-$(CONFIG_SECURITY_AUDITSEC_FIXED) += auditsec_fixed.o

# Rust target (requires CONFIG_RUST=y in the kernel)
obj-$(CONFIG_SECURITY_AUDITSEC_RUST) += auditsec_rust.o
