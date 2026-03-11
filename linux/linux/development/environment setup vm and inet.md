# Linux Kernel Development Setup Guide

A comprehensive guide for contributing to Linux kernel development, focusing on VM and networking subsystems without affecting your host system.

## 1. Prerequisites

### System Requirements

- **Host System**: Any modern Linux distribution (Ubuntu, Fedora, Arch, Debian, etc.)
- **RAM**: Minimum 16GB (32GB recommended for running multiple VMs)
- **Storage**: At least 100GB free space for kernel source, builds, and VMs
- **CPU**: Multi-core processor with virtualization support (Intel VT-x or AMD-V)

### Essential Packages

Install these on your host system:

```bash
# For Debian/Ubuntu
sudo apt update
sudo apt install -y \
    git build-essential kernel-package fakeroot libncurses-dev \
    libssl-dev bison flex libelf-dev bc dwarves \
    qemu-system-x86 qemu-utils libvirt-daemon-system \
    libvirt-clients bridge-utils virt-manager \
    gdb cgdb crash strace ltrace \
    sparse cppcheck clang-format \
    python3-pip python3-dev \
    vim emacs nano \
    ccache distcc \
    pahole

# For Fedora/RHEL
sudo dnf groupinstall "Development Tools"
sudo dnf install -y \
    git ncurses-devel openssl-devel bison flex elfutils-libelf-devel \
    bc dwarves qemu-kvm qemu-img libvirt virt-install \
    bridge-utils virt-manager gdb crash strace \
    sparse cppcheck clang-tools-extra \
    python3-devel ccache vim

# For Arch Linux
sudo pacman -S base-devel git vim gdb qemu-full libvirt virt-manager \
    bridge-utils ebtables dnsmasq openbsd-netcat \
    bc cpio perl tar xz pahole python ccache
```

## 2. Safe Development Environment Setup

### Option A: QEMU/KVM Virtual Machines (Recommended)

#### Enable Virtualization

```bash
# Check if virtualization is enabled
egrep -c '(vmx|svm)' /proc/cpuinfo
# Should return > 0

# Enable and start libvirt
sudo systemctl enable libvirtd
sudo systemctl start libvirtd

# Add your user to libvirt group
sudo usermod -aG libvirt,kvm $(whoami)
# Log out and back in for this to take effect
```

#### Create Development VM

**Method 1: Using virt-install (Command Line)**

```bash
# Download a minimal Linux ISO (e.g., Debian netinst)
wget https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.x.x-amd64-netinst.iso

# Create VM
virt-install \
    --name kernel-dev \
    --ram 4096 \
    --disk path=/var/lib/libvirt/images/kernel-dev.qcow2,size=40 \
    --vcpus 4 \
    --os-variant debian11 \
    --network bridge=virbr0 \
    --graphics none \
    --console pty,target_type=serial \
    --location 'debian-12.x.x-amd64-netinst.iso' \
    --extra-args 'console=ttyS0,115200n8 serial'
```

**Method 2: Using virt-manager (GUI)**

- Launch virt-manager
- Create new VM → Local install media
- Choose your ISO
- Allocate 4GB RAM, 4 CPUs, 40GB disk
- Complete installation

#### Create Testing VM Image

```bash
# Create a minimal testing image for quick boots
mkdir -p ~/kernel-testing
cd ~/kernel-testing

# Download or create a minimal rootfs
# Option 1: Use debootstrap (Debian-based)
sudo debootstrap --arch=amd64 stable debian-rootfs http://deb.debian.org/debian/

# Option 2: Download pre-built image
wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2

# Create a snapshot for testing (preserves original)
qemu-img create -f qcow2 -b debian-12-generic-amd64.qcow2 -F qcow2 test-snapshot.qcow2
```

### Option B: Docker/Podman Containers (For Build Environment)

```bash
# Create a container for building kernels
mkdir -p ~/kernel-build-env
cd ~/kernel-build-env

cat > Dockerfile <<EOF
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    build-essential git bc bison flex libssl-dev \
    libelf-dev libncurses-dev dwarves python3 \
    vim nano curl wget ccache
RUN useradd -m -s /bin/bash kerneldev
USER kerneldev
WORKDIR /home/kerneldev
EOF

docker build -t kernel-build .

# Use it
docker run -it -v ~/linux:/home/kerneldev/linux kernel-build
```

## 3. Getting the Linux Kernel Source

### Clone the Kernel Repository

```bash
# Create workspace
mkdir -p ~/kernel-dev
cd ~/kernel-dev

# Clone mainline kernel (this will take time, ~3-4 GB)
git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

# Or clone with limited history for faster download
git clone --depth=1 git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

cd linux

# Add relevant subsystem trees for networking
git remote add netdev git://git.kernel.org/pub/scm/linux/kernel/git/netdev/net-next.git
git remote add net git://git.kernel.org/pub/scm/linux/kernel/git/netdev/net.git

# Fetch
git fetch netdev
git fetch net
```

### Understanding Branches

- **mainline (torvalds/linux.git)**: Linus's tree, latest development
- **net-next**: Networking development for next merge window
- **net**: Networking fixes for current release
- **linux-stable**: Stable kernel releases

## 4. Building the Kernel

### Configure the Kernel

```bash
cd ~/kernel-dev/linux

# Option 1: Use your current system's config as base
cp /boot/config-$(uname -r) .config
make olddefconfig

# Option 2: Start with default config
make defconfig

# Option 3: Minimal config for faster builds
make tinyconfig

# Option 4: Interactive configuration
make menuconfig  # ncurses-based
make nconfig     # newer ncurses interface
make xconfig     # Qt-based (if you have Qt dev packages)

# Enable specific features for VM/networking development
make menuconfig
# Navigate to:
# - Networking support → enable what you need
# - Device Drivers → Network device support
# - Virtualization → KVM
# - Enable DEBUG_INFO, KASAN, etc. for debugging
```

### Key Config Options for Development

Add these to your `.config` or enable via menuconfig:

```bash
# Essential debugging options
CONFIG_DEBUG_INFO=y
CONFIG_DEBUG_INFO_DWARF4=y
CONFIG_FRAME_POINTER=y
CONFIG_DEBUG_KERNEL=y
CONFIG_DEBUG_SECTION_MISMATCH=y

# Memory debugging
CONFIG_KASAN=y              # Kernel Address Sanitizer
CONFIG_KASAN_INLINE=y
CONFIG_UBSAN=y              # Undefined Behavior Sanitizer
CONFIG_DEBUG_KMEMLEAK=y

# Lock debugging
CONFIG_PROVE_LOCKING=y
CONFIG_LOCK_STAT=y
CONFIG_DEBUG_ATOMIC_SLEEP=y

# Networking debugging
CONFIG_NET_DROP_MONITOR=y
CONFIG_NETFILTER_XT_TARGET_TRACE=y

# VM/KVM (if working on virtualization)
CONFIG_KVM=y
CONFIG_KVM_INTEL=y   # or CONFIG_KVM_AMD=y
CONFIG_VHOST_NET=y
```

### Build the Kernel

```bash
# Speed up compilation with ccache
export PATH="/usr/lib/ccache:$PATH"

# Determine number of cores
CORES=$(nproc)

# Build kernel
make -j$CORES

# Build modules
make -j$CORES modules

# Build specific subsystem only (faster for testing)
make -j$CORES net/
make -j$CORES drivers/net/

# Create packages (optional)
make -j$CORES bindeb-pkg    # Debian/Ubuntu
make -j$CORES binrpm-pkg    # Fedora/RHEL
```

### Build Time Optimization

```bash
# Use ccache
export CCACHE_DIR=~/.ccache
export PATH="/usr/lib/ccache:$PATH"

# Reduce debug info size
scripts/config --disable DEBUG_INFO_SPLIT
scripts/config --enable DEBUG_INFO_DWARF4

# Disable unused drivers
make localmodconfig  # Only builds modules currently loaded
```

## 5. Testing Environment

### QEMU Test Script

Create a script for easy kernel testing:

```bash
cat > ~/kernel-dev/run-kernel.sh <<'EOF'
#!/bin/bash

KERNEL="$1"
ROOTFS="${2:-debian-12-generic-amd64.qcow2}"
APPEND="root=/dev/sda1 console=ttyS0 nokaslr"

qemu-system-x86_64 \
    -kernel "$KERNEL" \
    -hda "$ROOTFS" \
    -append "$APPEND" \
    -m 2G \
    -smp 2 \
    -nographic \
    -enable-kvm \
    -net nic,model=virtio \
    -net user,hostfwd=tcp::2222-:22 \
    -serial mon:stdio

# Exit QEMU with: Ctrl-A X
EOF

chmod +x ~/kernel-dev/run-kernel.sh

# Run your kernel
~/kernel-dev/run-kernel.sh ~/kernel-dev/linux/arch/x86/boot/bzImage
```

### Advanced QEMU Networking Setup

#### Bridge Networking for VM-to-VM Testing

```bash
# Create bridge (one-time setup)
sudo ip link add br0 type bridge
sudo ip link set br0 up
sudo ip addr add 192.168.100.1/24 dev br0

# Create TAP interfaces
sudo ip tuntap add dev tap0 mode tap user $(whoami)
sudo ip link set tap0 up
sudo ip link set tap0 master br0

sudo ip tuntap add dev tap1 mode tap user $(whoami)
sudo ip link set tap1 up
sudo ip link set tap1 master br0

# Now run VMs with TAP interfaces
qemu-system-x86_64 \
    -kernel bzImage \
    -hda vm1.qcow2 \
    -netdev tap,id=net0,ifname=tap0,script=no,downscript=no \
    -device virtio-net-pci,netdev=net0 \
    -m 2G -enable-kvm -nographic
```

#### Network Namespace Testing

```bash
# Create network namespaces for isolated testing
sudo ip netns add ns1
sudo ip netns add ns2

# Create veth pair
sudo ip link add veth0 type veth peer name veth1

# Move to namespaces
sudo ip link set veth0 netns ns1
sudo ip link set veth1 netns ns2

# Configure
sudo ip netns exec ns1 ip addr add 10.0.0.1/24 dev veth0
sudo ip netns exec ns2 ip addr add 10.0.0.2/24 dev veth1
sudo ip netns exec ns1 ip link set veth0 up
sudo ip netns exec ns2 ip link set veth1 up

# Test
sudo ip netns exec ns1 ping 10.0.0.2
```

## 6. Debugging Tools and Techniques

### GDB with QEMU

```bash
# Start QEMU with GDB server
qemu-system-x86_64 \
    -kernel bzImage \
    -hda rootfs.qcow2 \
    -s -S \  # -s = GDB server on :1234, -S = pause at start
    -m 2G -enable-kvm -nographic

# In another terminal
cd ~/kernel-dev/linux
gdb vmlinux
(gdb) target remote :1234
(gdb) break start_kernel
(gdb) continue
(gdb) layout src
(gdb) list
```

### Useful GDB Commands for Kernel Debugging

```gdb
# Break on function
break function_name
break net/core/dev.c:netif_receive_skb

# Hardware breakpoints
hbreak *0xaddress

# Watch memory
watch variable_name

# Print structures
p *skb
p/x variable  # print in hex

# Backtrace
bt
bt full

# Load module symbols dynamically
add-symbol-file drivers/net/mydriver.ko 0xaddress

# Examine memory
x/20x $sp  # examine 20 words at stack pointer

# QEMU monitor commands (Ctrl-A C to switch to monitor)
info registers
info tlb
info mem
```

### Dynamic Debugging

```bash
# Enable dynamic debug at boot
# Add to kernel command line:
dyndbg="file net/core/dev.c +p"

# Or at runtime:
echo "file drivers/net/virtio_net.c +p" > /sys/kernel/debug/dynamic_debug/control
echo "func netif_receive_skb +p" > /sys/kernel/debug/dynamic_debug/control

# View debug messages
dmesg -w
```

### Ftrace

```bash
# Enable function tracing
cd /sys/kernel/debug/tracing
echo function > current_tracer
echo 1 > tracing_on

# Trace specific function
echo tcp_sendmsg > set_ftrace_filter
cat trace

# Function graph tracing
echo function_graph > current_tracer
echo tcp_sendmsg > set_graph_function

# Trace events
echo 1 > events/net/enable
cat trace_pipe
```

### perf

```bash
# Record kernel events
sudo perf record -a -g -- sleep 10
sudo perf report

# Trace specific events
sudo perf record -e net:netif_receive_skb -a

# Profile networking
sudo perf top -e cycles:k

# Trace system calls
sudo perf trace
```

### eBPF Tools (bpftrace/bcc)

```bash
# Install bpftrace
sudo apt install bpftrace  # Ubuntu
sudo dnf install bpftrace  # Fedora

# Trace TCP connections
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_connect { @[comm] = count(); }'

# Network packet tracing
sudo bpftrace -e 'kprobe:tcp_sendmsg { @bytes = hist(arg2); }'
```

## 7. Development Workflow

### Making Changes

```bash
# Create a branch for your work
git checkout -b my-networking-feature

# Make changes to code
vim net/core/dev.c

# Check your changes
git diff

# Run checkpatch before committing
scripts/checkpatch.pl --strict --file net/core/dev.c

# Or check your patch
git diff > my.patch
scripts/checkpatch.pl my.patch
```

### Code Style and Static Analysis

```bash
# Check coding style
scripts/checkpatch.pl --strict --file your_file.c
scripts/checkpatch.pl --strict -g HEAD  # check last commit

# Format code (use with caution)
clang-format -i your_file.c

# Run sparse (semantic checker)
make C=1 net/
make C=2  # check all files

# Smatch
sudo apt install sqlite3 libsqlite3-dev llvm
git clone git://repo.or.cz/smatch.git
cd smatch
make
cd ~/kernel-dev/linux
~/smatch/smatch_scripts/build_kernel_data.sh
~/smatch/smatch_scripts/test_kernel.sh

# cppcheck
cppcheck --enable=all --suppress=missingIncludeSystem net/core/dev.c
```

### Testing Your Changes

```bash
# Compile only your changes
make net/core/dev.o

# Build module
make M=drivers/net/ethernet/intel/e1000e

# Install module in test VM
scp drivers/net/.../mymodule.ko testvm:/root/
ssh testvm
rmmod mymodule
insmod mymodule.ko
dmesg | tail
```

### Creating Patches

```bash
# Commit your changes
git add net/core/dev.c
git commit -s  # -s adds Signed-off-by

# Write good commit message:
# Line 1: Short summary (50 chars)
# Line 2: Blank
# Lines 3+: Detailed description
#
# Example:
# net: fix memory leak in skb allocation
#
# When allocating skb in fastpath, we were not properly
# freeing memory on error path. This adds proper cleanup
# using kfree_skb().

# Generate patch
git format-patch -1  # last commit
git format-patch HEAD~3  # last 3 commits
git format-patch master..my-branch  # range

# Review patch
less 0001-*.patch

# Check patch with checkpatch
scripts/checkpatch.pl 0001-*.patch
```

### Running Kernel Tests

```bash
# KUnit (unit testing framework)
./tools/testing/kunit/kunit.py run
make ARCH=um mrproper
./tools/testing/kunit/kunit.py run --kunitconfig=net/

# kselftest
cd tools/testing/selftests
make
sudo make run_tests

# Run specific test
cd net
sudo make run_tests

# Network tests
cd tools/testing/selftests/net
./pmtu.sh
./gso.sh
./fib_tests.sh
```

## 8. Contribution Process

### Understanding MAINTAINERS

```bash
# Find maintainers for your changes
scripts/get_maintainer.pl net/core/dev.c
scripts/get_maintainer.pl 0001-*.patch

# Read subsystem documentation
less Documentation/process/submitting-patches.rst
less Documentation/networking/netdev-FAQ.rst
```

### Sending Patches

```bash
# Configure git send-email
git config --global sendemail.smtpserver smtp.gmail.com
git config --global sendemail.smtpserverport 587
git config --global sendemail.smtpencryption tls
git config --global sendemail.smtpuser your@email.com

# Send patch (first time, send to yourself!)
git send-email --to=yourself@email.com 0001-*.patch

# Send to maintainers (example for networking)
git send-email \
    --to="David S. Miller <davem@davemloft.net>" \
    --cc=netdev@vger.kernel.org \
    --cc=linux-kernel@vger.kernel.org \
    0001-*.patch

# For patch series
git send-email --cover-letter --to=... --cc=... *.patch
```

### Responding to Feedback

```bash
# Address review comments
git checkout my-networking-feature
vim net/core/dev.c  # make changes

# Amend commit
git add net/core/dev.c
git commit --amend

# Or create new commit and squash
git add net/core/dev.c
git commit -m "address review comments"
git rebase -i HEAD~2  # mark second commit as 'fixup'

# Send v2
git format-patch -v2 -1
git send-email --to=... 0001-*.patch
```

## 9. Networking-Specific Development

### Key Networking Directories

```
net/
├── core/          # Core networking (dev.c, skbuff.c, etc.)
├── ipv4/          # IPv4 implementation
├── ipv6/          # IPv6 implementation
├── netlink/       # Netlink protocol
├── packet/        # Packet sockets
├── sched/         # Traffic control/QoS
└── xfrm/          # Transform (IPsec) framework

drivers/net/
├── ethernet/      # Ethernet drivers
└── wireless/      # Wireless drivers

include/
├── linux/         # Kernel headers
│   ├── netdevice.h
│   ├── skbuff.h
│   └── ...
├── net/           # Network headers
└── uapi/          # User-space API headers
```

### Key Networking Structures

```c
// Socket buffer - the fundamental networking structure
struct sk_buff

// Network device
struct net_device

// Network namespace
struct net

// Socket
struct sock

// Protocol operations
struct proto_ops
struct proto
```

### Useful Networking Debug Tools

```bash
# Monitor network traffic
tcpdump -i any -nn

# Inside VM
sudo tcpdump -i eth0 -w capture.pcap

# Socket statistics
ss -antp

# Interface statistics
ip -s link

# Network namespace info
ip netns list

# Routing
ip route show

# iptables/nftables for testing filters
iptables -L -v -n
```

## 10. Useful Scripts and Aliases

Add to `~/.bashrc`:

```bash
# Kernel development aliases
alias kbuild='make -j$(nproc)'
alias kclean='make mrproper'
alias kconfig='make menuconfig'
alias kcheck='scripts/checkpatch.pl --strict'

# QEMU shortcuts
alias qemu-test='~/kernel-dev/run-kernel.sh'

# Git aliases for kernel work
alias gfp='git format-patch'
alias gse='git send-email'
alias gcp='git cherry-pick'

# Quick kernel build after config
function kernel-quick() {
    make -j$(nproc) && \
    echo "Build successful!"
}

# Check patch series
function check-patches() {
    for patch in "$@"; do
        echo "Checking $patch"
        scripts/checkpatch.pl "$patch"
    done
}
```

## 11. Common Issues and Solutions

### Build Issues

```bash
# Missing dependencies
# Solution: Install all build-essential packages

# Out of memory during build
# Solution: Reduce parallel jobs
make -j4  # instead of -j$(nproc)

# Or add swap
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### VM Issues

```bash
# VM won't boot with custom kernel
# Solution: Make sure you have:
# - CONFIG_VIRTIO=y
# - CONFIG_VIRTIO_PCI=y
# - CONFIG_VIRTIO_BLK=y
# - CONFIG_VIRTIO_NET=y

# Serial console not working
# Add to kernel command line: console=ttyS0

# KVM acceleration not working
# Check: grep -E "(vmx|svm)" /proc/cpuinfo
# Load module: modprobe kvm_intel (or kvm_amd)
```

### Debugging Issues

```bash
# GDB can't find symbols
# Solution: Make sure CONFIG_DEBUG_INFO=y
# Build with: make -j$(nproc) vmlinux

# Crash during boot
# Solution: Enable early printk
# Add to kernel cmdline: earlyprintk=serial,ttyS0,115200

# Can't access debugfs
# Mount it: mount -t debugfs none /sys/kernel/debug
```

## 12. Resources and Documentation

### Essential Reading

```bash
# In kernel source tree
Documentation/process/
Documentation/process/submitting-patches.rst
Documentation/process/coding-style.rst
Documentation/networking/
Documentation/vm/

# Online
- https://kernelnewbies.org/
- https://lwn.net/ (kernel articles)
- https://www.kernel.org/doc/html/latest/
- https://elixir.bootlin.com/linux/latest/source (source code browser)
```

### Mailing Lists

```
netdev@vger.kernel.org          - Network development
linux-kernel@vger.kernel.org    - General kernel development
kvm@vger.kernel.org             - KVM/virtualization
```

### IRC/Communication

```
#kernel on irc.oftc.net
#kernelnewbies on irc.oftc.net
#networking on irc.oftc.net
```

## Quick Start Checklist

- [ ] Install all required packages
- [ ] Enable KVM and libvirt
- [ ] Clone Linux kernel source
- [ ] Create test VM
- [ ] Configure kernel with debugging options
- [ ] Build kernel successfully
- [ ] Boot test VM with custom kernel
- [ ] Setup GDB debugging
- [ ] Run checkpatch on test file
- [ ] Setup git send-email
- [ ] Read Documentation/process/submitting-patches.rst
- [ ] Subscribe to netdev mailing list

## Next Steps

1. Start with reading code in `net/core/dev.c` - the network device layer
2. Try making a small documentation fix
3. Fix a beginner-friendly bug from kernel bugzilla
4. Join #kernelnewbies IRC for help
5. Read recent commits in your area of interest

Good luck with your Linux kernel contributions!

I'll create a comprehensive guide for you to set up a safe Linux kernel development environment focused on VM and networking development.I've created a comprehensive guide for Linux kernel development with a focus on VM and networking, while keeping your host system safe.

## Key Highlights:

**Safe Development Approach:**

- Uses QEMU/KVM for isolated testing
- All kernel testing happens in virtual machines
- Your host system remains untouched

**For VM & Networking Focus:**

- Specific sections on network namespace testing
- Bridge networking setup for multi-VM scenarios
- Network debugging tools (tcpdump, bpftrace, ftrace)
- Key networking subsystem directories and structures

**Complete Workflow:**

- Setting up build environment
- Compiling the kernel efficiently (with ccache)
- Testing in QEMU with various networking configurations
- Debugging with GDB, ftrace, perf, and eBPF
- Code style checking and static analysis
- Proper patch submission process

## Immediate Action Items:

1. **Start with the Quick Start Checklist** at the bottom of the guide
2. **Install the prerequisites** for your distro (commands provided)
3. **Set up QEMU/KVM** - this is your safe testing playground
4. **Clone the kernel** and networking subsystem trees

## Pro Tips:

- Use `make localmodconfig` for faster builds (only builds modules you actually use)
- Network namespaces are perfect for testing without needing multiple VMs
- Start small - maybe a typo fix in documentation to learn the workflow
- Join #kernelnewbies on IRC - very welcoming community

Would you like me to elaborate on any specific section, or help you troubleshoot your specific setup?