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

https://claude.ai/share/d5a8bc0b-c289-4a93-8f00-857ffaaa2d8b - ecu-enex-hq-gml