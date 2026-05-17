# Linux Kernel Network Lab — Setup Verification Checklist

Run each command on your **Dell G3 Ubuntu Desktop (host)**  
unless the step says *"inside VM"*.  
Mark `[x]` as you verify each item.

---

## Phase 1 — Hardware & KVM Stack

- [ ] **CPU virtualisation is enabled**
  ```bash
  egrep -c '(vmx|svm)' /proc/cpuinfo
  ```
  Result must be > 0. If 0, enable VT-x / AMD-V in BIOS.

- [ ] **KVM kernel module is loaded**
  ```bash
  lsmod | grep kvm
  ```
  You should see `kvm_intel` (Intel) or `kvm_amd` (AMD) in the output.

- [ ] **/dev/kvm device exists**
  ```bash
  ls -la /dev/kvm
  ```
  Must exist. If missing, the KVM module is not loaded.

- [ ] **libvirtd is running**
  ```bash
  systemctl is-active libvirtd
  ```
  Must print `active`. Fix: `sudo systemctl enable --now libvirtd`

- [ ] **User is in `libvirt` and `kvm` groups**
  ```bash
  groups
  ```
  Both `libvirt` and `kvm` must appear. Fix:
  ```bash
  sudo usermod -aG libvirt,kvm $USER
  newgrp libvirt
  ```

- [ ] **Default NAT bridge (virbr0) is up**
  ```bash
  ip link show virbr0
  ```
  Should show `state UP`. Fix:
  ```bash
  virsh net-start default
  virsh net-autostart default
  ```

---

## Phase 2 — Required Host Packages

Run this to check all at once:

```bash
dpkg -l \
  build-essential libncurses-dev bison flex libssl-dev libelf-dev \
  dwarves bc cpio pahole \
  qemu-kvm libvirt-daemon-system virt-manager bridge-utils virtinst qemu-utils \
  gdb crash trace-cmd linux-tools-common \
  cscope exuberant-ctags tmux git devscripts dpkg-dev \
  2>&1 | grep -E '^(ii|un|dpkg)'
```

Every line must start with `ii`. Lines starting with `un` mean the package is missing.

- [ ] Build tools: `build-essential bison flex libncurses-dev libssl-dev libelf-dev`
- [ ] Kernel build extras: `dwarves bc cpio pahole`
- [ ] QEMU/KVM stack: `qemu-kvm libvirt-daemon-system virt-manager bridge-utils virtinst qemu-utils`
- [ ] Debug tools: `gdb crash trace-cmd linux-tools-common`
- [ ] Navigation tools: `cscope exuberant-ctags tmux git`
- [ ] Packaging tools: `devscripts dpkg-dev`

Install anything missing in one shot:
```bash
sudo apt install -y \
  build-essential libncurses-dev bison flex libssl-dev libelf-dev \
  dwarves bc cpio pahole \
  qemu-kvm libvirt-daemon-system virt-manager bridge-utils virtinst qemu-utils \
  gdb crash trace-cmd linux-tools-common \
  cscope exuberant-ctags tmux git devscripts dpkg-dev
```

---

## Phase 3 — Lab Files & Disk Space

- [ ] **Kernel tarball is present**
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6.tar.xz
  ```
  Expected size: ~215 MB.

- [ ] **Ubuntu Server ISO is present**
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/ubuntu-24.04.4-live-server-amd64.iso
  ```
  Expected size: ~2.6 GB.

- [ ] **At least 40 GB free in lab directory**
  ```bash
  df -h ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/
  ```
  Look at the `Avail` column. Kernel build alone needs ~15 GB; VM disk takes 40 GB.

- [ ] **VM directory exists**
  ```bash
  ls ~/vms/
  ```
  Create if missing: `mkdir -p ~/vms`

---

## Phase 4 — Kernel Source Extraction

- [ ] **linux-7.0.6 directory is extracted**
  ```bash
  ls ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/Makefile
  ```
  If missing, extract:
  ```bash
  cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/
  tar -xf linux-7.0.6.tar.xz
  ```

- [ ] **Source tree size looks right (~1.2 GB)**
  ```bash
  du -sh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
  ```
  Less than 800 MB suggests a bad or incomplete extraction.

- [ ] **Git is initialised in the kernel source (to track your changes)**
  ```bash
  ls ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/.git
  ```
  If missing, initialise:
  ```bash
  cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
  git init
  git add -A
  git commit -m "vanilla linux-7.0.6 base"
  ```

---

## Phase 5 — Kernel .config — Required Debug Options

First, check the .config exists:
```bash
ls ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/.config
```
If missing, create it:
```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
cp /boot/config-$(uname -r) .config
make olddefconfig
```

Then verify each option (run from inside `linux-7.0.6/`):

### Debug symbols (needed for GDB)

- [ ] `CONFIG_DEBUG_INFO=y`
  ```bash
  grep '^CONFIG_DEBUG_INFO=' .config
  ```

- [ ] `CONFIG_DEBUG_INFO_DWARF4=y`
  ```bash
  grep '^CONFIG_DEBUG_INFO_DWARF4=' .config
  ```

- [ ] `CONFIG_DEBUG_KERNEL=y`
  ```bash
  grep '^CONFIG_DEBUG_KERNEL=' .config
  ```

- [ ] `CONFIG_FRAME_POINTER=y`
  ```bash
  grep '^CONFIG_FRAME_POINTER=' .config
  ```

- [ ] `CONFIG_KALLSYMS=y` and `CONFIG_KALLSYMS_ALL=y`
  ```bash
  grep '^CONFIG_KALLSYMS' .config
  ```

### KGDB (step through kernel from GDB on host)

- [ ] `CONFIG_KGDB=y`
  ```bash
  grep '^CONFIG_KGDB=' .config
  ```

- [ ] `CONFIG_KGDB_SERIAL_CONSOLE=y`
  ```bash
  grep '^CONFIG_KGDB_SERIAL_CONSOLE=' .config
  ```

- [ ] `CONFIG_GDB_SCRIPTS=y`
  ```bash
  grep '^CONFIG_GDB_SCRIPTS=' .config
  ```

### ftrace (function call tracing without recompiling)

- [ ] `CONFIG_FTRACE=y`
  ```bash
  grep '^CONFIG_FTRACE=' .config
  ```

- [ ] `CONFIG_FUNCTION_TRACER=y`
  ```bash
  grep '^CONFIG_FUNCTION_TRACER=' .config
  ```

- [ ] `CONFIG_FUNCTION_GRAPH_TRACER=y`
  ```bash
  grep '^CONFIG_FUNCTION_GRAPH_TRACER=' .config
  ```

- [ ] `CONFIG_DYNAMIC_FTRACE=y`
  ```bash
  grep '^CONFIG_DYNAMIC_FTRACE=' .config
  ```

- [ ] `CONFIG_STACK_TRACER=y`
  ```bash
  grep '^CONFIG_STACK_TRACER=' .config
  ```

### Dynamic debug (enable pr_debug per file at runtime)

- [ ] `CONFIG_DYNAMIC_DEBUG=y`
  ```bash
  grep '^CONFIG_DYNAMIC_DEBUG=' .config
  ```

### eBPF / bpftrace

- [ ] `CONFIG_BPF_SYSCALL=y`
  ```bash
  grep '^CONFIG_BPF_SYSCALL=' .config
  ```

- [ ] `CONFIG_BPF_JIT=y`
  ```bash
  grep '^CONFIG_BPF_JIT=' .config
  ```

- [ ] `CONFIG_DEBUG_INFO_BTF=y` (allows bpftrace to access struct fields by name)
  ```bash
  grep '^CONFIG_DEBUG_INFO_BTF=' .config
  ```

### Network subsystem

- [ ] `CONFIG_VIRTIO_NET=y` (VM's NIC driver — the driver you will read/modify)
  ```bash
  grep '^CONFIG_VIRTIO_NET=' .config
  ```

- [ ] `CONFIG_VHOST_NET=y` (host-side of virtio — the other end)
  ```bash
  grep '^CONFIG_VHOST_NET=' .config
  ```

- [ ] `CONFIG_NET_SCHED=y` (TC / qdisc layer)
  ```bash
  grep '^CONFIG_NET_SCHED=' .config
  ```

### KASLR must be OFF (so GDB breakpoint addresses stay stable across reboots)

- [ ] `CONFIG_RANDOMIZE_BASE` is NOT set
  ```bash
  grep 'RANDOMIZE_BASE' .config
  ```
  Expected output: `# CONFIG_RANDOMIZE_BASE is not set`  
  If it shows `CONFIG_RANDOMIZE_BASE=y`, disable it:
  ```bash
  scripts/config --disable CONFIG_RANDOMIZE_BASE
  make olddefconfig
  ```

### Fix any missing option

For any option that is missing or wrong:
```bash
scripts/config --enable CONFIG_OPTION_NAME
make olddefconfig
```

---

## Phase 6 — Kernel Build Output

- [ ] **Kernel image .deb was built**
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-image-*-netlab*.deb
  ```
  If missing, build (takes 30–60 min):
  ```bash
  cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
  make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee build.log
  ```

- [ ] **Kernel headers .deb was built** (needed to build modules inside VM)
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-headers-*-netlab*.deb
  ```

- [ ] **vmlinux exists** (the uncompressed kernel with debug symbols — needed for GDB)
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/vmlinux
  ```
  Expected size: ~1.5 GB.

- [ ] **build.log has no errors**
  ```bash
  grep ' error:' ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/build.log | head -20
  ```
  No output = clean build.

---

## Phase 7 — KVM Virtual Machine

- [ ] **VM 'netlab' exists**
  ```bash
  virsh list --all | grep netlab
  ```

- [ ] **VM disk exists**
  ```bash
  ls -lh ~/vms/netlab.qcow2
  ```
  If VM doesn't exist yet, create it using the `virt-install` command from your setup notes.

- [ ] **VM is running**
  ```bash
  virsh list | grep netlab
  ```
  Start it: `virsh start netlab`

- [ ] **VM has an IP address**
  ```bash
  virsh domifaddr netlab
  ```
  Should show something like `192.168.122.100`.

- [ ] **SSH into VM works**
  ```bash
  ssh netlab@$(virsh domifaddr netlab | grep -oP '(\d+\.){3}\d+' | head -1) 'uname -r'
  ```

---

## Phase 8 — Custom Kernel Running in VM

*Run these from your host.*

- [ ] **.deb packages copied into VM**
  ```bash
  LAB=~/Documents/clion/opensource_sushink70/linux_kernel_net_playground
  VM_IP=$(virsh domifaddr netlab | grep -oP '(\d+\.){3}\d+' | head -1)
  scp $LAB/linux-image-*-netlab*.deb $LAB/linux-headers-*-netlab*.deb netlab@$VM_IP:~
  ```

- [ ] **Packages installed inside VM**
  ```bash
  # Inside VM
  sudo dpkg -i ~/linux-image-*-netlab*.deb ~/linux-headers-*-netlab*.deb
  sudo update-grub
  ```

- [ ] **GRUB serial/KGDB line is set** (inside VM, before rebooting)
  ```bash
  # Inside VM
  grep 'GRUB_CMDLINE_LINUX_DEFAULT' /etc/default/grub
  ```
  Must contain: `console=ttyS0,115200 kgdboc=ttyS0,115200 nokaslr`  
  If not, edit `/etc/default/grub` and run `sudo update-grub`.

- [ ] **VM rebooted and running your kernel**
  ```bash
  # Inside VM after reboot
  uname -r
  ```
  Must print: `7.0.6-netlab`

---

## Phase 9 — Debug Tools Inside VM

*SSH into VM first, then check each.*

- [ ] **tshark and tcpdump**
  ```bash
  which tshark tcpdump
  ```
  Install if missing: `sudo apt install -y tshark tcpdump`

- [ ] **trace-cmd** (ftrace from the command line)
  ```bash
  which trace-cmd
  ```

- [ ] **bpftrace** (eBPF-based tracing, no kernel rebuild needed)
  ```bash
  which bpftrace
  bpftrace --version
  ```
  Install: `sudo apt install -y bpftrace`

- [ ] **gdb and strace**
  ```bash
  which gdb strace
  ```

- [ ] **tmux and vim**
  ```bash
  which tmux vim
  ```

- [ ] **debugfs is mounted** (needed for ftrace)
  ```bash
  mount | grep debugfs
  ```
  Mount if missing: `sudo mount -t debugfs none /sys/kernel/debug`  
  Make it permanent: add `debugfs /sys/kernel/debug debugfs defaults 0 0` to `/etc/fstab`

- [ ] **linux-headers for your running kernel are installed** (needed to build kernel modules)
  ```bash
  ls /lib/modules/$(uname -r)/build
  ```

- [ ] **Rust / cargo** (for the Axum server)
  ```bash
  which cargo
  cargo --version
  ```
  Install if missing:
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  source ~/.cargo/env
  ```

---

## Phase 10 — Smoke Tests (Lab Is Ready When All Pass)

*Run these inside the VM.*

- [ ] **ftrace works**
  ```bash
  echo function_graph | sudo tee /sys/kernel/debug/tracing/current_tracer
  cat /sys/kernel/debug/tracing/current_tracer
  ```
  Must print back `function_graph`.

- [ ] **bpftrace can attach to a kernel probe**
  ```bash
  sudo bpftrace -e 'kprobe:tcp_sendmsg { printf("hit\n"); exit(); }' &
  curl -s http://example.com > /dev/null
  ```
  Must print `hit` within a second or two.

- [ ] **tshark can capture live packets**
  ```bash
  sudo tshark -i eth0 -c 5
  ```
  Must show 5 captured frames.

- [ ] **Your pr_info probes fire** (only if you added them in source)
  ```bash
  sudo dmesg -C
  curl -s http://example.com > /dev/null
  sudo dmesg | grep '\[NL-'
  ```
  Must show lines like `[NL-1] sendto enter ...` through `[NL-7] virtnet_xmit ...`

- [ ] **Axum server starts and is reachable** (if you built it)
  ```bash
  # In VM
  cd ~/netlab-server && ./target/release/netlab-server &
  curl http://localhost:3000/
  ```

---

## Quick Reference — Most Common Problems

| Symptom | Likely cause | Fix |
|---|---|---|
| `lsmod` shows no kvm module | VT-x/AMD-V disabled in BIOS | Enable in BIOS, then `sudo modprobe kvm_intel` |
| `virsh` permission denied | Not in libvirt group | `sudo usermod -aG libvirt $USER && newgrp libvirt` |
| `make bindeb-pkg` fails on missing symbol | .config option conflict | `make menuconfig`, find the symbol, enable it, re-run build |
| `uname -r` in VM shows old kernel | Wrong GRUB entry boots | Set `GRUB_DEFAULT=0` and `GRUB_TIMEOUT=5` in `/etc/default/grub`, run `update-grub` |
| `bpftrace` fails: `No BTF found` | CONFIG_DEBUG_INFO_BTF=n | Rebuild kernel with that option enabled |
| GDB breakpoints at wrong address | KASLR is on | Set `CONFIG_RANDOMIZE_BASE=n`, rebuild |
| `dmesg` empty for `[NL-*]` | pr_debug used instead of pr_info, or dynamic_debug not enabled | Either use `pr_info`, or enable: `echo 'file net/ipv4/tcp_output.c +p' > /sys/kernel/debug/dynamic_debug/control` |
| ftrace shows nothing | tracing_on is 0 | `echo 1 > /sys/kernel/debug/tracing/tracing_on` |
| VM has no internet | virbr0 NAT not running | `virsh net-start default && virsh net-autostart default` |

---

*Save this file. Check off items as you go. Once Phase 10 passes, your lab is fully operational.*
