Great, I have your full notes. Now let me address your question precisely.

## Your Question: How Does the Edited Kernel Get Into the VM?

The short answer: **it does not go into the ISO at all**. The ISO is only used once — to install Ubuntu Server onto `netlab.qcow2`. After that, the VM boots from the `.qcow2` disk, not the ISO. Your custom kernel gets installed into the VM separately.

Here's the complete mental model:

---

### The Boot Flow You're Imagining (Wrong)

```
Edit linux-7.0.6 → somehow update the ISO → KVM boots ISO → custom kernel runs
```

This is not how it works. The ISO is a read-only installer. It doesn't change.

---

### The Actual Flow (Correct)

```
Step 1 — One time only:
  virt-install --cdrom ubuntu-24.04.4.iso
  → Installs Ubuntu Server onto netlab.qcow2
  → netlab.qcow2 now has Ubuntu with the stock Ubuntu kernel
  → You eject the ISO mentally, never touch it again

Step 2 — Build your custom kernel on the HOST:
  cd linux-7.0.6
  [edit source files]
  make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab
  → Produces: ../linux-image-7.0.6-netlab_amd64.deb

Step 3 — Copy the .deb into the running VM:
  scp ../linux-image-7.0.6-netlab*.deb netlab@192.168.122.100:~

Step 4 — Install it inside the VM:
  ssh netlab@192.168.122.100
  sudo dpkg -i linux-image-7.0.6-netlab*.deb
  sudo update-grub
  sudo reboot

Step 5 — VM now boots YOUR kernel from netlab.qcow2:
  uname -r
  → 7.0.6-netlab
```

---

### What `bindeb-pkg` Actually Builds

When you run:

```bash
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab
```

It produces `.deb` packages **one directory up** from the kernel source:

```
linux_kernel_net_playground/
├── linux-7.0.6/                 ← you edited source here
├── linux-image-7.0.6-netlab_amd64.deb    ← kernel + modules
├── linux-headers-7.0.6-netlab_amd64.deb  ← header files
└── linux-libc-dev_7.0.6-netlab_amd64.deb ← libc headers
```

The `.deb` contains the kernel binary (`vmlinuz-7.0.6-netlab`), all loadable modules, and the initramfs. When you `dpkg -i` it inside the VM, it drops these into the VM's `/boot/` and registers with GRUB automatically.

---

### The Incremental Loop After First Setup

Every time you edit the kernel source:

```bash
# On host — rebuild (faster on incremental changes, ~2-5 min not 60)
cd linux-7.0.6
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab

# Copy and install into VM
scp ../linux-image-7.0.6-netlab*.deb netlab@192.168.122.100:~
ssh netlab@192.168.122.100 "sudo dpkg -i ~/linux-image-7.0.6-netlab*.deb && sudo reboot"

# After reboot
ssh netlab@192.168.122.100
uname -r   # confirms 7.0.6-netlab
sudo dmesg -w | grep "\[NL-"  # see your pr_info prints
```

---

### Your `workshop/` Directory

Since you want to do everything in `workshop/`, here's a clean structure:

```bash
cd ~/Documents/clion/opensource_sushink70/workshop/

mkdir -p kernel-builds scripts

# Symlink to your kernel source so you don't duplicate it
ln -s ../linux_kernel_net_playground/linux-7.0.6 kernel-src
```

Then write a deploy script at `scripts/deploy.sh`:

```bash
#!/bin/bash
set -e

VM_USER="netlab"
VM_IP="192.168.122.100"
DEB_DIR="$(realpath ../linux_kernel_net_playground)"

echo "==> Copying .deb to VM..."
scp "${DEB_DIR}"/linux-image-7.0.6-netlab*.deb "${VM_USER}@${VM_IP}":~

echo "==> Installing and rebooting VM..."
ssh "${VM_USER}@${VM_IP}" "sudo dpkg -i ~/linux-image-7.0.6-netlab*.deb && sudo update-grub && sudo reboot"

echo "==> Waiting for VM to come back..."
sleep 15
ssh "${VM_USER}@${VM_IP}" "uname -r"
```

So your full loop from `workshop/` becomes:

```bash
# Edit kernel source
vim ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/net/ipv4/tcp_output.c

# Build
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab

# Deploy
cd ~/Documents/clion/opensource_sushink70/workshop/
bash scripts/deploy.sh
```

The ISO is completely out of this loop. It only exists to do the initial Ubuntu Server install into the `.qcow2` once.

This is a classic libvirt permission issue. The `libvirt-qemu` user (uid 64055) can't traverse your home directory. Two ways to fix it — pick one:

---

## Option A — Move files to libvirt's default pool (cleanest)

```bash
# Move the qcow2 disk to where libvirt expects it
sudo mv ~/vms/netlab.qcow2 /var/lib/libvirt/images/netlab.qcow2

# Copy (not move) the ISO there too
sudo cp ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/ubuntu-24.04.4-live-server-amd64.iso \
    /var/lib/libvirt/images/ubuntu-24.04.4-live-server-amd64.iso

# Fix ownership
sudo chown libvirt-qemu:kvm /var/lib/libvirt/images/netlab.qcow2
sudo chown libvirt-qemu:kvm /var/lib/libvirt/images/ubuntu-24.04.4-live-server-amd64.iso
```

Then reinstall the domain (delete the broken one first):

```bash
virsh --connect qemu:///system undefine netlab 2>/dev/null || true

virt-install \
  --name netlab \
  --ram 4096 \
  --vcpus 4 \
  --disk /var/lib/libvirt/images/netlab.qcow2,format=qcow2 \
  --cdrom /var/lib/libvirt/images/ubuntu-24.04.4-live-server-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=default \
  --graphics vnc,listen=127.0.0.1 \
  --serial pty \
  --channel unix,target_type=virtio,name=org.qemu.guest_agent.0 \
  --noautoconsole
```

---

## Option B — Grant libvirt-qemu access to your home dir (keep files in place)

```bash
# Give execute (traversal) permission on your home dir to others
chmod o+x /home/iamdreamer

# Then run your original virt-install command unchanged
virsh --connect qemu:///system undefine netlab 2>/dev/null || true

virt-install \
  --name netlab \
  --ram 4096 \
  --vcpus 4 \
  --disk ~/vms/netlab.qcow2,format=qcow2 \
  --cdrom ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/ubuntu-24.04.4-live-server-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=default \
  --graphics vnc,listen=127.0.0.1 \
  --serial pty \
  --channel unix,target_type=virtio,name=org.qemu.guest_agent.0 \
  --noautoconsole
```

`chmod o+x` on a directory only grants traversal, not listing (`o+r`) — so other users can't `ls` your home, but the hypervisor can pass through it to reach the files. This is the minimal safe permission.

---

## Connect to the installer after launch

The WARNING about `virt-viewer` means you have no graphical console yet. Install it, then connect:

```bash
sudo apt install virt-viewer

# Connect to the VNC installer
virt-viewer --connect qemu:///system netlab
```

Or use VNC directly — find the port and connect with any VNC client:

```bash
virsh --connect qemu:///system vncdisplay netlab
# e.g. outputs :0 → connect to 127.0.0.1:5900
```

**I'd recommend Option A** — keeping VM assets in `/var/lib/libvirt/images/` is the standard convention and avoids this class of problem permanently. The ISO copy is temporary; once Ubuntu is installed you can delete it from there.

The VM is running and the Ubuntu installer is active. Now connect to it:

```bash
sudo apt install virt-viewer -y
virt-viewer --connect qemu:///system netlab
```

A VNC window will open showing the Ubuntu Server installer. Go through it:

1. **Language** → English
2. **Installer update** → Continue without updating (saves time)
3. **Keyboard** → your layout
4. **Network** → leave default (it will get an IP via DHCP from virbr0)
5. **Proxy** → leave blank
6. **Mirror** → leave default
7. **Storage** → Use entire disk (the 40GB qcow2)
8. **Profile setup** → this is important:
   - Your name: anything
   - Server name: `netlab`
   - Username: `netlab`
   - Password: `netlab` (simple, it's a local lab VM)
9. **SSH** → **Install OpenSSH server ✓** (check this, critical for later)
10. **Featured snaps** → skip all, just hit Done
11. **Installation** → wait for it to finish, then **Reboot Now**

---

While the installer runs, you can verify the VM is alive in another terminal:

```bash
virsh --connect qemu:///system list
# Should show:  netlab   running
```

---

After reboot, find the VM's IP and SSH in:

```bash
virsh --connect qemu:///system domifaddr netlab
# e.g. 192.168.122.100

ssh netlab@192.168.122.100
uname -r
# Shows the stock Ubuntu kernel — your base is ready
```

Once you're SSHed in, the VM is set up and you're ready to start building and deploying your custom kernel into it.

Yes, those settings are correct for a lab VM. Here's what each means:

- **(X) Use an entire disk** → correct, use the full 40GB qcow2
- **/dev/vda** → correct, that's your virtual disk (KVM uses `vda` instead of `sda`)
- **[X] Set up this disk as an LVM group** → fine, standard Ubuntu default
- **[ ] Encrypt with LUKS** → leave it **unchecked** — no point encrypting a local lab VM, it would just add a passphrase prompt on every boot

Hit **Done** and continue. The next screen will show you a storage layout summary — just confirm it and proceed with the installation.

Those settings are already perfect as-is:

- **[X] Install OpenSSH server** → checked ✓ (critical, this is how you'll `ssh` in from your host)
- **[X] Allow password authentication over SSH** → checked ✓ (lets you `ssh netlab@192.168.122.100` with password)
- **Import SSH key** → skip this, not needed for a local lab VM
- **No authorized key** → fine, password auth is enough

Just hit **Done** and continue. Nothing to change here.

Yes! After reboot, the VM will eject the ISO and boot from the disk. Now do this on your host:

**Wait about 30 seconds**, then find the VM's IP:

```bash
virsh --connect qemu:///system domifaddr netlab
```

You should see something like:
```
 Name       MAC address         Protocol   Address
 vnet0      52:54:00:xx:xx:xx   ipv4       192.168.122.100/24
```

Then SSH in:

```bash
ssh netlab@192.168.122.100
```

Type `yes` to accept the host key, then enter the password you set during install.

Once you're in, confirm it booted correctly:

```bash
uname -r
# Shows stock Ubuntu kernel e.g. 6.8.0-xx-generic

df -h
# Shows your 40GB disk mounted

ip addr
# Shows eth0 with 192.168.122.x IP
```

If `domifaddr` shows nothing, the VM may still be booting. Give it another 30 seconds and try again. If it still shows nothing:

```bash
virsh --connect qemu:///system list
# Should show netlab as running

virsh --connect qemu:///system console netlab
# Direct console access if SSH isn't up yet
```

Tell me what `domifaddr` shows and we'll go from there.

Normal — the VM shut down after the reboot at end of installation. The ISO is still attached which can cause it to boot back into the installer. Start it manually:

```bash
virsh --connect qemu:///system start netlab
```

Wait 30 seconds, then check:

```bash
virsh --connect qemu:///system domifaddr netlab
```

If it still loops into the installer, detach the ISO first then start:

```bash
# Detach the cdrom
virsh --connect qemu:///system change-media netlab sda --eject --force 2>/dev/null || \
virsh --connect qemu:///system change-media netlab hda --eject --force 2>/dev/null || true

# Or edit the VM config to remove cdrom
virsh --connect qemu:///system edit netlab
# Find the line with <disk type='file' device='cdrom'> and remove that whole block
# Save and quit (:wq in vi)

# Then start
virsh --connect qemu:///system start netlab
```

After it starts, connect to see what's on screen:

```bash
virt-viewer --connect qemu:///system netlab
```

Tell me what you see — whether it's booting Ubuntu normally or going back into the installer.

Perfect! The VM is up and has IP `192.168.122.23`. SSH in:

```bash
ssh netlab@192.168.122.23
```

Type `yes` for the host key prompt, then enter your password. Once in, verify everything:

```bash
uname -r
# e.g. 6.8.0-xx-generic  ← stock Ubuntu kernel, expected

df -h
# Should show 40GB disk

ip addr
# Should show eth0 with 192.168.122.23
```

If it connects successfully you're ready to move to the next phase — building your custom `linux-7.0.6` kernel on the host and deploying it into this VM.

Tell me what `uname -r` shows and we'll start the kernel build.

The VM may have booted back into the installer instead of the installed system, creating confusion. Let's check directly via console:

```bash
virt-viewer --connect qemu:///system netlab
```

Look at what's on screen — is it a login prompt or the installer again?

If it's a login prompt, try logging in directly in the console with your username and password to verify they work. If the console login also fails, the password may not have been set correctly during install.

**To reset the password without reinstalling:**

```bash
# On your host — open the VM console
virsh --connect qemu:///system console netlab
```

When you see the login prompt, reboot the VM into recovery:

```bash
# Shut down the VM
virsh --connect qemu:///system destroy netlab

# Edit grub to boot into single user mode
virsh --connect qemu:///system start netlab
```

Then immediately open virt-viewer and at the GRUB menu:
1. Press `e` to edit the boot entry
2. Find the line starting with `linux` 
3. Add `init=/bin/bash` at the end of that line
4. Press `Ctrl+X` to boot

Once you get a root shell:

```bash
mount -o remount,rw /
passwd netlab
# Enter new password twice
sync
reboot -f
```

Then SSH again with the new password.

**Alternatively — simplest fix, just reinstall** since the install only takes ~5 minutes:

```bash
virsh --connect qemu:///system destroy netlab
virsh --connect qemu:///system undefine netlab

# Recreate fresh qcow2
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/netlab.qcow2 40G

# Reinstall
virt-install \
  --name netlab \
  --ram 4096 \
  --vcpus 4 \
  --disk /var/lib/libvirt/images/netlab.qcow2,format=qcow2 \
  --cdrom /var/lib/libvirt/images/ubuntu-24.04.4-live-server-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=default \
  --graphics vnc,listen=127.0.0.1 \
  --serial pty \
  --channel unix,target_type=virtio,name=org.qemu.guest_agent.0 \
  --noautoconsole
```

This time be extra careful at the profile setup screen — type the password slowly, the installer has no "show password" option.

I see the issue — during install you created the user as **`netuser`** not `netlab`. And the hostname is `netuser` too. That's why SSH failed — you were using the wrong username.

The VM is perfectly fine. SSH with the correct username:

```bash
ssh netuser@192.168.122.23
```

Everything looks great from the console:
- Ubuntu 24.04.4 LTS ✓
- Kernel `6.8.0-117-generic` ✓ (stock, expected)
- IP `192.168.122.23` ✓
- 18.53GB disk ✓

Once SSHed in from your host terminal, you're ready to start the kernel build phase. Close the virt-viewer window — you won't need it anymore, SSH is cleaner.

Simple. After turning your PC back on:

**1. Start the VM:**
```bash
virsh --connect qemu:///system start netlab
```

**2. Wait ~20 seconds, then SSH in:**
```bash
ssh netuser@192.168.122.23
```

That's it. The VM resumes exactly where you left off.

---

**If the IP changed** (rare but possible):
```bash
virsh --connect qemu:///system domifaddr netlab
# Check the IP, then ssh to whatever it shows
```

---

**To make life easier**, add this to your `~/.bashrc` on your host so you don't have to remember commands:

```bash
echo "alias netlab-start='virsh --connect qemu:///system start netlab'" >> ~/.bashrc
echo "alias netlab-ssh='ssh netuser@192.168.122.23'" >> ~/.bashrc
echo "alias netlab-stop='virsh --connect qemu:///system shutdown netlab'" >> ~/.bashrc
echo "alias netlab-ip='virsh --connect qemu:///system domifaddr netlab'" >> ~/.bashrc
source ~/.bashrc
```

Then every day:
```bash
netlab-start   # start the VM
netlab-ssh     # SSH in
```

And at end of day instead of just powering off your PC:
```bash
netlab-stop    # graceful shutdown of VM first
```

You're now at the start of the kernel build phase. Here's where you are in the overall plan:

```
[✓] VM installed and running
[✓] SSH working
[ ] Build custom linux-7.0.6 on HOST
[ ] Copy .deb to VM
[ ] Install custom kernel in VM
[ ] Boot and verify
[ ] Add net stack probes and learn
```

---

**First, on your HOST** (open a new terminal, not the VM SSH):

Install build dependencies:

```bash
sudo apt install -y \
    build-essential libncurses-dev bison flex \
    libssl-dev libelf-dev dwarves bc cpio pahole
```

Then go to the kernel source:

```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6
```

Copy your running host kernel config as the base:

```bash
cp /boot/config-$(uname -r) .config
make olddefconfig
```

Tell me when that's done and we'll enable the debug flags and start the build. The build takes 30-60 minutes on first run so we want to kick it off and let it run.

Great questions. Let me explain both clearly.

---

## `cp /boot/config-$(uname -r) .config`

Your running host kernel has a config file at `/boot/config-6.8.0-xxx-generic`. This file has **thousands of options** — every driver, every feature, enabled or disabled.

```
/boot/config-6.8.0-117-generic
├── CONFIG_VIRTIO_NET=y        ← virtual NIC driver
├── CONFIG_TCP_CONG_CUBIC=y    ← TCP congestion control
├── CONFIG_EXT4_FS=y           ← filesystem
├── CONFIG_USB_SUPPORT=y       ← USB drivers
... (12,000+ options)
```

You copy it as your starting point because:
- It's known to **boot and work** on your hardware
- It already has `VIRTIO_NET` enabled — your VM's NIC driver
- Writing a config from scratch would take weeks

**The mismatch concern — valid question.** Your host is a Dell G3 laptop. Your VM is a virtual machine. Some host-specific drivers will be compiled in unnecessarily (WiFi chipset, Nvidia GPU, etc.) but they cause **zero problems** — they just sit unused inside the VM. The VM only uses what it needs (virtio-net, virtio-disk, etc.) and ignores the rest.

---

## `make olddefconfig`

Break it down:

```
make          → run the kernel build system
old           → start from the OLD config you just copied (.config)
def           → for any NEW options that exist in linux-7.0.6
               but didn't exist in your 6.8 config → use DEFAULT value
config        → this is a config-resolving operation, not a build
```

Your host config was made for kernel `6.8`. You are building `7.0.6`. Between those versions, new config options were added that your old `.config` doesn't have answers for.

`olddefconfig` silently fills in all those new options with their default values without asking you anything. No interactive prompts.

```
Before olddefconfig:
  .config has 12,000 options
  linux-7.0.6 needs 12,347 options
  → 347 options are unanswered

After olddefconfig:
  All 347 new options filled with sensible defaults
  → .config is complete and valid for 7.0.6
```

**Alternative you may have heard of:** `make menuconfig` — opens an interactive menu where YOU answer every new option manually. That's for when you want full control. `olddefconfig` is for "just make it work with safe defaults."

---

## Summary

```
cp /boot/config-$(uname -r) .config
→ "Start from a known-working config"

make olddefconfig  
→ "Fill in any gaps for the new kernel version with safe defaults"
```

Safe to run both. No mismatches that will cause problems. Ready to proceed?

Now enable the debug flags needed for net stack learning. Run these one by one on your **host** in the `linux-7.0.6` directory:

```bash
# Debug symbols — needed for GDB to show function names and line numbers
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_DEBUG_INFO_DWARF4
scripts/config --enable CONFIG_DEBUG_KERNEL
scripts/config --enable CONFIG_FRAME_POINTER
scripts/config --enable CONFIG_KALLSYMS
scripts/config --enable CONFIG_KALLSYMS_ALL

# KGDB — step through kernel code live from GDB
scripts/config --enable CONFIG_KGDB
scripts/config --enable CONFIG_KGDB_SERIAL_CONSOLE
scripts/config --enable CONFIG_GDB_SCRIPTS

# ftrace — trace kernel function calls
scripts/config --enable CONFIG_FTRACE
scripts/config --enable CONFIG_FUNCTION_TRACER
scripts/config --enable CONFIG_FUNCTION_GRAPH_TRACER
scripts/config --enable CONFIG_DYNAMIC_FTRACE

# Dynamic debug — turn pr_debug() on/off per file at runtime
scripts/config --enable CONFIG_DYNAMIC_DEBUG

# BPF/eBPF — for bpftrace tools
scripts/config --enable CONFIG_BPF_SYSCALL
scripts/config --enable CONFIG_BPF_JIT
scripts/config --enable CONFIG_DEBUG_INFO_BTF

# virtio-net — your VM's NIC driver
scripts/config --enable CONFIG_VIRTIO_NET
scripts/config --enable CONFIG_VHOST_NET

# Disable KASLR — keeps memory addresses stable across reboots for GDB
scripts/config --disable CONFIG_RANDOMIZE_BASE

# Resolve any new dependencies
make olddefconfig
```

Once done, start the build:

```bash
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee build.log
```

This will take **30-60 minutes**. You'll see lots of `CC` and `LD` lines scrolling — that's normal.

While it builds, you can watch progress in another terminal:

```bash
# See what's currently compiling
tail -f ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/build.log
```

Let me know when the build finishes or if you see any errors.

Easy fix — just missing two build dependencies. Install them:

```bash
sudo apt install -y debhelper libdw-dev
```

Then run the build again:

```bash
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee build.log
```

The Android binder warnings from earlier (`symbol value 'm' invalid`) are harmless — just ignore them.

This time it should start compiling. You'll see lines like:
```
CC      init/main.o
CC      kernel/fork.o
...
```

That means the build is running. It'll take 30-60 minutes. Let me know when it finishes or if you see any new errors.

The real error is hidden earlier in the log. Let's find it:

```bash
grep -i "error:" build.log | head -30
```

Or look at what happened just before the xfs error:

```bash
grep -B5 "Error 2" build.log | head -50
```

Also check specifically for BTF errors — that's the most common cause:

```bash
grep -i "btf\|pahole\|dwarf" build.log | head -20
```

Paste what those show and I'll tell you the exact fix.

The real error is in the `certs` directory. Let's see it:

```bash
grep -A3 "certs" build.log | grep -i "error\|failed\|No such" | head -20
```

And check the full context around it:

```bash
grep -n "certs" build.log | head -20
```

Most likely it's a missing signing key. Fix it preemptively:

```bash
# Disable module signing and trusted keys — not needed for a lab kernel
scripts/config --disable CONFIG_SYSTEM_TRUSTED_KEYS
scripts/config --disable CONFIG_SYSTEM_REVOCATION_KEYS
scripts/config --set-str CONFIG_SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str CONFIG_SYSTEM_REVOCATION_KEYS ""

make olddefconfig
```

Then rebuild:

```bash
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee build.log
```

This is the most common build failure on 7.x kernels when using a distro config — the Ubuntu config references certificate files that don't exist in the vanilla kernel source tree. Disabling them is safe for a lab VM.

Confirmed — exactly as expected. The Ubuntu config references `debian/canonical-certs.pem` which doesn't exist in the vanilla kernel source. Run the fix:

```bash
scripts/config --disable CONFIG_SYSTEM_TRUSTED_KEYS
scripts/config --disable CONFIG_SYSTEM_REVOCATION_KEYS
scripts/config --set-str CONFIG_SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str CONFIG_SYSTEM_REVOCATION_KEYS ""

make olddefconfig
```

Then rebuild:

```bash
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee build.log
```

This time it should run all the way through. The build will take 30-60 minutes — you'll see thousands of `CC` lines scrolling. That's normal, just let it run.

You can monitor progress in another terminal:

```bash
tail -f ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/build.log
```

Let me know when it finishes or if you see any new errors.

Easy — `gawk` is not installed:

```bash
sudo apt install -y gawk
```

Then rebuild:

```bash
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee build.log
```

We're getting closer each time — these are all just missing tools, not actual kernel errors. Let it run and tell me what happens.

No worries — those are two completely **separate and unrelated** things happening at the same time:

```
HOST (your PC)                      VM (netlab)
──────────────────────────────      ──────────────────────────────
make bindeb-pkg running...          apt upgrade running...
building linux-7.0.6-netlab         updating stock 6.8.0-117-generic
                │                                │
                │                                │
                ▼                                ▼
  will produce .deb package          just keeping Ubuntu updated
  (your custom kernel)               (has nothing to do with 7.0.6)
```

The VM updating `initrd.img-6.8.0-117-generic` is just Ubuntu's normal package update — it has no connection to your kernel build on the host.

Your custom `7.0.6-netlab` kernel gets into the VM **only** after:
1. Build finishes on host → produces `.deb`
2. You `scp` the `.deb` into the VM
3. You `dpkg -i` it inside the VM
4. VM reboots into `7.0.6-netlab`

The VM update is actually good — keeps the base system clean. Let both finish and tell me when the `make` on the host completes.

That's perfectly correct and expected. That's the **stock Ubuntu kernel** inside the VM right now.

```
Current state:
  VM kernel:  6.8.0-117-generic  ← stock Ubuntu (normal)
  Building:   7.0.6-netlab       ← your custom (in progress on host)
```

Nothing to do in the VM right now. Just wait for the `make` to finish on your host.

When the build completes you'll see something like:

```
dpkg-deb: building package 'linux-image-7.0.6-netlab' ...
dpkg-deb: building package 'linux-headers-7.0.6-netlab' ...
```

And back in your host terminal:

```bash
# Confirm the .deb files were created
ls ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/*.deb
```

You should see:
```
linux-headers-7.0.6-netlab_7.0.6-1_amd64.deb
linux-image-7.0.6-netlab_7.0.6-1_amd64.deb
linux-libc-dev_7.0.6-1_amd64.deb
```

Then we copy them into the VM and install. Let me know when `make` finishes!

The build is complete! Let's verify the .deb files:

```bash
ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/*.deb
```

You should see several `.deb` files. Now copy them into the VM:

```bash
scp ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-image-7.0.6-netlab_7.0.6-4_amd64.deb \
    ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-headers-7.0.6-netlab_7.0.6-4_amd64.deb \
    netuser@192.168.122.23:~
```

Then SSH into the VM and install:

```bash
ssh netuser@192.168.122.23
```

Inside the VM:

```bash
sudo dpkg -i ~/linux-image-7.0.6-netlab_7.0.6-4_amd64.deb \
             ~/linux-headers-7.0.6-netlab_7.0.6-4_amd64.deb

sudo update-grub
sudo reboot
```

After reboot, SSH back in and verify:

```bash
ssh netuser@192.168.122.23
uname -r
# Should show: 7.0.6-netlab
```

Tell me what `ls *.deb` shows first so we confirm the exact filenames before copying.

Check if it's still running or actually stuck:

```bash
# In another terminal — see if make is still active
ps aux | grep make | grep -v grep
```

Also check the last few lines of the log:

```bash
tail -20 ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/build.log
```

The `dpkg-deb: building package 'linux-image-7.0.6-netlab-dbg'` line you saw is actually building the **debug symbols package** — it's a very large package (~2-3GB) and takes a long time to compress. So it may just be silently working on that.

Check disk space too — the debug package needs a lot:

```bash
df -h ~
```

If disk is fine and make is still running, just wait — the dbg package compression can take 10-20 minutes silently with no output.

It's still running — not stuck. The last line shows:

```
dpkg-deb: building package 'linux-image-7.0.6-netlab-dbg'
```

This debug symbols package is **2-3GB** and `dpkg-deb` is silently compressing it right now. No output during compression — that's normal. It can take **15-30 minutes** just for this one step.

You have 317GB free so disk is not an issue.

Just leave it alone and wait. You can watch if the file is growing:

```bash
watch -n5 ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-image-7.0.6-netlab-dbg*.deb
```

You'll see the file size increasing as it compresses. When it stops growing and the make process disappears from `ps`, the build is done.

Go have a tea/coffee break — this part just takes time. ☕

Build complete! Verify the .deb files:

```bash
ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/*.deb
```

You should see something like:
```
linux-headers-7.0.6-netlab_7.0.6-4_amd64.deb
linux-image-7.0.6-netlab_7.0.6-4_amd64.deb
linux-image-7.0.6-netlab-dbg_7.0.6-4_amd64.deb
linux-libc-dev_7.0.6-4_amd64.deb
```

Now copy the important ones into the VM (skip the `-dbg` one — it's huge and not needed yet):

```bash
scp ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-image-7.0.6-netlab_7.0.6-4_amd64.deb \
    ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-headers-7.0.6-netlab_7.0.6-4_amd64.deb \
    netuser@192.168.122.23:~
```

Then SSH into the VM and install:

```bash
ssh netuser@192.168.122.23
```

Inside the VM:

```bash
sudo dpkg -i ~/linux-image-7.0.6-netlab_7.0.6-4_amd64.deb \
             ~/linux-headers-7.0.6-netlab_7.0.6-4_amd64.deb
sudo update-grub
sudo reboot
```

After reboot, SSH back in and verify:

```bash
ssh netuser@192.168.122.23
uname -r
# Should show: 7.0.6-netlab
```

Tell me what `ls *.deb` shows first!

All 4 packages are there. Now copy the two needed ones to the VM:

```bash
scp ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-image-7.0.6-netlab_7.0.6-4_amd64.deb \
    ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-headers-7.0.6-netlab_7.0.6-4_amd64.deb \
    netuser@192.168.122.23:~
```

This will take a minute — the image is 124MB. Tell me when the `scp` finishes.

Now SSH into the VM and install:

```bash
ssh netuser@192.168.122.23
```

Inside the VM:

```bash
sudo dpkg -i ~/linux-image-7.0.6-netlab_7.0.6-4_amd64.deb \
             ~/linux-headers-7.0.6-netlab_7.0.6-4_amd64.deb
```

Tell me what output you see — it should show something like:
```
Selecting previously unselected package linux-image-7.0.6-netlab
Setting up linux-image-7.0.6-netlab ...
update-initramfs: Generating /boot/initrd.img-7.0.6-netlab
```

Then we run `update-grub` and reboot.

Perfect output! Everything installed correctly:

```
✓ linux-image-7.0.6-netlab installed
✓ initrd.img-7.0.6-netlab generated
✓ GRUB found vmlinuz-7.0.6-netlab
✓ GRUB config updated automatically
```

Now reboot the VM:

```bash
sudo reboot
```

Wait about 20 seconds, then SSH back in from your host:

```bash
ssh netuser@192.168.122.23
```

Then verify your custom kernel is running:

```bash
uname -r
```

It should show:
```
7.0.6-netlab
```

🎉 **Your custom-built Linux 7.0.6 kernel is running in the VM!**

Let's confirm everything is healthy:

```bash
uname -r
# 7.0.6-netlab

uname -a
# Full kernel info

dmesg | tail -20
# Check for any boot errors

lsmod | head -20
# Modules loaded correctly
```

Here's where you are now:

```
[✓] VM installed and running
[✓] SSH working
[✓] Built custom linux-7.0.6 on HOST
[✓] Copied .deb to VM
[✓] Installed custom kernel in VM
[✓] Booted and verified 7.0.6-netlab
[ ] Add net stack pr_info probes
[ ] Rebuild and redeploy
[ ] Start tracing packets layer by layer
```

**Next step** is the fun part — adding your first `pr_info` probes to the net stack on the host, rebuilding, and watching packets flow through each layer live.

Ready to add the first probe to `net/ipv4/tcp_output.c`?

Everything looks perfect:

```
✓ 7.0.6-netlab running
✓ Kernel compiled Sun May 17 21:50:40 IST 2026 (your build)
✓ Modules loading correctly (virtio, kvm, etc.)
✓ Clean boot, no errors
```

Now the real learning begins. **Back on your HOST**, add the first net stack probe:

```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6
```

Open `net/ipv4/tcp_output.c` and find `tcp_transmit_skb`:

```bash
grep -n "static int tcp_transmit_skb" net/ipv4/tcp_output.c
```

It will show a line number like:
```
1234:static int tcp_transmit_skb(...)
```

Open that file at that line:

```bash
nano +1234 net/ipv4/tcp_output.c
```

Add this as the first line inside the function body, after the opening `{`:

```c
pr_info("[NL-TCP] tcp_transmit_skb: len=%u\n", skb->len);
```

Save, then rebuild — this time much faster since only one file changed:

```bash
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee build.log
```

Incremental build should take **2-5 minutes** not 60. Tell me what line number `grep` shows for `tcp_transmit_skb`.

From your **host terminal**:

```bash
virsh --connect qemu:///system shutdown netlab
```

This sends a proper ACPI shutdown signal — same as pressing the power button on a real machine. The VM OS shuts down cleanly.

Verify it stopped:

```bash
virsh --connect qemu:///system list --all
# Should show:  netlab   shut off
```

---

**Other useful VM power commands:**

```bash
# Graceful shutdown (always use this)
virsh --connect qemu:///system shutdown netlab

# Force kill (only if VM is frozen/unresponsive)
virsh --connect qemu:///system destroy netlab

# Start
virsh --connect qemu:///system start netlab

# Reboot gracefully
virsh --connect qemu:///system reboot netlab

# Check status
virsh --connect qemu:///system list --all
```

Or from **inside the VM** via SSH:

```bash
sudo poweroff
```

Both do the same thing. Always prefer graceful shutdown over `destroy` to avoid filesystem corruption in the VM.

https://claude.ai/share/d5a8bc0b-c289-4a93-8f00-857ffaaa2d8b - ecu-enex-hq-gml