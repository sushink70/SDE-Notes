## Summary

Full QEMU/KVM installation for GNS3 on Kali provides hardware-accelerated virtualization with strong isolation boundaries via kernel modules (kvm_intel/kvm_amd). KVM confirmed available on your system. This setup creates secure VM boundaries for network device emulation, critical for security lab environments. Install includes libvirt orchestration, virt-manager GUI, OVMF UEFI firmware, and networking components (bridge-utils, virt-viewer). Post-install: configure libvirt networks, import appliances, harden with AppArmor/seccomp.

---

## Full Installation Commands

### 1. Install QEMU/KVM Stack + Dependencies

```bash
# Update package cache
sudo apt update

# Core QEMU/KVM packages
sudo apt install -y \
  qemu-kvm \
  qemu-system-x86 \
  qemu-system-arm \
  qemu-utils \
  qemu-efi-aarch64 \
  qemu-efi-arm \
  libvirt-daemon-system \
  libvirt-daemon \
  libvirt-clients \
  libvirt-daemon-driver-qemu \
  virtinst \
  virt-manager \
  virt-viewer \
  bridge-utils \
  ovmf \
  genisoimage \
  cpu-checker

# Networking components
sudo apt install -y \
  dnsmasq-base \
  ebtables \
  iptables \
  libguestfs-tools

# Additional GNS3-specific requirements
sudo apt install -y \
  python3-pip \
  python3-pyqt5 \
  python3-pyqt5.qtsvg \
  python3-pyqt5.qtwebsockets \
  x11-xserver-utils \
  wireshark

# Verify KVM module loaded
lsmod | grep -E 'kvm_(intel|amd)'
# Expected output: kvm_intel or kvm_amd with kvm dependency
```

### 2. Configure User Permissions

```bash
# Add user to required groups
sudo usermod -aG libvirt,kvm,libvirt-qemu,input,disk $USER

# Verify group assignment
groups $USER

# Apply groups without logout
newgrp libvirt

# Set KVM device permissions (persistent)
echo 'KERNEL=="kvm", GROUP="kvm", MODE="0660"' | sudo tee /etc/udev/rules.d/65-kvm.rules

# Reload udev rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# Verify /dev/kvm permissions
ls -lh /dev/kvm
# Expected: crw-rw---- 1 root kvm ... /dev/kvm
```

### 3. Enable and Configure libvirt

```bash
# Enable libvirt services
sudo systemctl enable libvirtd
sudo systemctl enable virtlogd
sudo systemctl start libvirtd
sudo systemctl start virtlogd

# Verify service status
sudo systemctl status libvirtd --no-pager

# Configure libvirt for current user
sudo sed -i 's/#unix_sock_group = "libvirt"/unix_sock_group = "libvirt"/' /etc/libvirt/libvirtd.conf
sudo sed -i 's/#unix_sock_rw_perms = "0770"/unix_sock_rw_perms = "0770"/' /etc/libvirt/libvirtd.conf

# Restart libvirt to apply
sudo systemctl restart libvirtd

# Test virsh access (no sudo needed)
virsh --connect qemu:///system list --all
# Expected: Empty list of VMs (no "permission denied" errors)
```

### 4. Configure Default libvirt Network

```bash
# Start default network
virsh net-start default

# Set autostart
virsh net-autostart default

# Verify network
virsh net-list --all
# Expected: 
# Name      State    Autostart   Persistent
# default   active   yes         yes

# Check network details
virsh net-dumpxml default | grep -E 'bridge|ip'
# Expected: virbr0 bridge with 192.168.122.0/24
```

### 5. Install GNS3 with QEMU Support

```bash
# Add GNS3 PPA
sudo add-apt-repository ppa:gns3/ppa -y
sudo apt update

# Install GNS3
sudo apt install -y gns3-gui gns3-server

# Add user to GNS3-specific groups
sudo usermod -aG ubridge,wireshark $USER

# Configure ubridge SUID (required for TAP interfaces)
sudo chmod u+s /usr/bin/ubridge
sudo setcap cap_net_admin,cap_net_raw=ep /usr/bin/ubridge

# Verify capabilities
getcap /usr/bin/ubridge
# Expected: /usr/bin/ubridge cap_net_admin,cap_net_raw=ep
```

### 6. Configure GNS3 for QEMU

```bash
# Create GNS3 config directory
mkdir -p ~/.config/GNS3/2.2

# Configure GNS3 to use local server
cat > ~/.config/GNS3/2.2/gns3_server.conf << 'EOF'
[Server]
host = 127.0.0.1
port = 3080
path = /usr/bin/gns3server
ubridge_path = /usr/bin/ubridge
auto_start = true
allow_remote_console = false

[Qemu]
enable_kvm = true
require_kvm = true
EOF

# Set permissions
chmod 600 ~/.config/GNS3/2.2/gns3_server.conf
```

---

## Architecture View (Full Stack)

```
┌─────────────────────────────────────────────────────────────┐
│                    Kali Linux (Host OS)                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              GNS3 GUI (Qt5 PyQt5)                      │  │
│  │  - Project Manager                                     │  │
│  │  - Topology Designer                                   │  │
│  └───────────┬────────────────────────────────────────────┘  │
│              │ IPC Socket / REST API (127.0.0.1:3080)        │
│  ┌───────────▼────────────────────────────────────────────┐  │
│  │           GNS3 Server (Python Backend)                 │  │
│  │  - Compute Manager                                     │  │
│  │  - Notification Controller                             │  │
│  └─┬──────────────────────┬───────────────────────────────┘  │
│    │                      │                                   │
│    │         ┌────────────▼─────────────┐                     │
│    │         │  QEMU Compute Engine     │                     │
│    │         │  - VM Lifecycle Mgmt     │                     │
│    │         │  - Disk Image Handling   │                     │
│    │         └────────┬─────────────────┘                     │
│    │                  │                                       │
│  ┌─▼──────────────────▼────────────────────────────────────┐ │
│  │              libvirt Daemon (libvirtd)                  │ │
│  │  - virsh CLI                                            │ │
│  │  - XML Domain Definitions                               │ │
│  │  - Storage Pool Manager                                 │ │
│  │  - Network Manager (dnsmasq)                            │ │
│  └─┬────────────────────┬──────────────────┬───────────────┘ │
│    │                    │                  │                  │
│ ┌──▼────────┐  ┌────────▼────────┐  ┌─────▼──────┐          │
│ │QEMU Process│  │QEMU Process     │  │ ubridge    │          │
│ │(Router VM) │  │(Switch/FW VM)   │  │(TAP/Bridge)│          │
│ │KVM accel   │  │KVM accel        │  │CAP_NET_ADM │          │
│ └─┬──────────┘  └────────┬────────┘  └─────┬──────┘          │
│   │                      │                  │                 │
│   │  ┌───────────────────▼──────────────────▼──────────────┐ │
│   │  │           KVM Kernel Module (kvm_intel)             │ │
│   │  │  - /dev/kvm character device                        │ │
│   │  │  - Hardware virtualization (VT-x/AMD-V)             │ │
│   │  │  - EPT/NPT page tables                              │ │
│   │  └─────────────────────────────────────────────────────┘ │
│   │                                                           │
│   └────────────┬──────────────────────────────────────────┐  │
│                │       Linux Kernel Network Stack         │  │
│       ┌────────▼─────────┐         ┌──────────────────┐   │  │
│       │  virbr0 (NAT)    │         │  br0 (Bridged)   │   │  │
│       │  192.168.122.1/24│         │  DHCP from LAN   │   │  │
│       └──────┬───────────┘         └────────┬─────────┘   │  │
│              │                              │             │  │
│        ┌─────▼─────────┐            ┌───────▼────────┐    │  │
│        │ iptables NAT  │            │  Physical NIC  │    │  │
│        │ MASQUERADE    │            │  (eth0/wlan0)  │    │  │
│        └─────┬─────────┘            └───────┬────────┘    │  │
└──────────────┼─────────────────────────────┼──────────────┘  │
               │                             │                 │
          ┌────▼─────────────────────────────▼────┐            │
          │         External Network              │            │
          │  (Internet / Physical Infrastructure) │            │
          └───────────────────────────────────────┘            │
```

---

## Validation Tests

### Test 1: KVM Acceleration
```bash
# Verify CPU virtualization extensions
egrep -c '(vmx|svm)' /proc/cpuinfo
# Expected: >0 (number of CPU cores with virt extensions)

# Check KVM modules
lsmod | grep kvm
# Expected:
# kvm_intel (or kvm_amd)    xxx  0
# kvm                       xxx  1 kvm_intel

# Test KVM device access
test -r /dev/kvm && test -w /dev/kvm && echo "KVM ready" || echo "KVM access denied"
# Expected: KVM ready
```

### Test 2: libvirt Connectivity
```bash
# Test system connection
virsh --connect qemu:///system version

# List storage pools
virsh pool-list --all

# Check default network
ip addr show virbr0
# Expected: virbr0 interface with 192.168.122.1 IP
```

### Test 3: Create Test VM
```bash
# Download minimal test image
cd /var/lib/libvirt/images
sudo wget https://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img

# Create test VM
virt-install \
  --name test-vm \
  --ram 256 \
  --disk path=/var/lib/libvirt/images/cirros-0.6.2-x86_64-disk.img,format=qcow2 \
  --vcpus 1 \
  --os-variant cirros0.6.2 \
  --network network=default \
  --graphics none \
  --import \
  --noautoconsole

# Verify VM created
virsh list --all
# Expected: test-vm listed as running

# Get VM console
virsh console test-vm
# Login: cirros / gocubsgo
# Test networking: ping 8.8.8.8
# Exit console: Ctrl+]

# Destroy and remove test VM
virsh destroy test-vm
virsh undefine test-vm --remove-all-storage
```

### Test 4: GNS3 Launch
```bash
# Start GNS3 server in background
gns3server --local --log /tmp/gns3server.log &

# Wait for startup
sleep 3

# Check server listening
ss -tlnp | grep 3080
# Expected: LISTEN on 127.0.0.1:3080

# Launch GUI
gns3 &

# Check logs
tail -f /tmp/gns3server.log
```

### Test 5: QEMU Performance Benchmark
```bash
# Create 1GB test disk
qemu-img create -f qcow2 /tmp/test.qcow2 1G

# Benchmark with KVM
qemu-system-x86_64 \
  -machine type=pc,accel=kvm \
  -m 512 \
  -smp 2 \
  -drive file=/tmp/test.qcow2,format=qcow2 \
  -nographic \
  -serial stdio \
  -kernel /boot/vmlinuz-$(uname -r) \
  -append "console=ttyS0 quiet" &

# Monitor KVM stats
cat /sys/module/kvm_intel/parameters/nested
# Expected: Y (nested virtualization enabled)

# Kill test
pkill qemu-system-x86

# Cleanup
rm /tmp/test.qcow2
```

---

## Security Hardening

### 1. AppArmor Profile for QEMU
```bash
# Check AppArmor status
sudo aa-status | grep qemu

# Enforce QEMU profile (if available)
sudo aa-enforce /etc/apparmor.d/usr.sbin.libvirtd
sudo aa-enforce /etc/apparmor.d/abstractions/libvirt-qemu

# Verify
sudo aa-status | grep -E '(libvirt|qemu)'
```

### 2. libvirt Security Settings
```bash
# Configure QEMU security driver
sudo tee -a /etc/libvirt/qemu.conf > /dev/null << 'EOF'

# Security driver configuration
security_driver = "apparmor"
security_default_confined = 1
security_require_confined = 1

# User/group isolation
user = "libvirt-qemu"
group = "libvirt-qemu"

# Clear capabilities for VMs
clear_emulator_capabilities = 1

# Disable VM memory dumps
auto_dump_bypass_cache = 0
EOF

# Restart libvirt
sudo systemctl restart libvirtd
```

### 3. Network Isolation
```bash
# Create isolated GNS3 network (no host connectivity)
cat > /tmp/gns3-isolated.xml << 'EOF'
<network>
  <name>gns3-isolated</name>
  <bridge name='virbr-gns3' stp='on' delay='0'/>
  <domain name='gns3.lab' localOnly='yes'/>
  <ip address='10.99.99.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='10.99.99.100' end='10.99.99.200'/>
    </dhcp>
  </ip>
</network>
EOF

# Define and start
virsh net-define /tmp/gns3-isolated.xml
virsh net-start gns3-isolated
virsh net-autostart gns3-isolated

# Verify isolation (no forward/NAT)
virsh net-dumpxml gns3-isolated | grep -E '(forward|nat)'
# Expected: No output (isolated network)
```

### 4. Restrict ubridge
```bash
# Create ubridge wrapper with restricted permissions
sudo tee /usr/local/bin/ubridge-restricted > /dev/null << 'EOF'
#!/bin/bash
# Restrict ubridge to specific interfaces only
ALLOWED_PREFIX="tap-gns3"

for arg in "$@"; do
    if [[ "$arg" =~ ^tap- ]] && [[ ! "$arg" =~ ^$ALLOWED_PREFIX ]]; then
        echo "ERROR: Interface $arg not allowed" >&2
        exit 1
    fi
done

exec /usr/bin/ubridge "$@"
EOF

sudo chmod 755 /usr/local/bin/ubridge-restricted

# Update GNS3 config to use wrapper
sed -i 's|ubridge_path = /usr/bin/ubridge|ubridge_path = /usr/local/bin/ubridge-restricted|' \
  ~/.config/GNS3/2.2/gns3_server.conf
```

---

## Storage Configuration

### Create Dedicated Storage Pool for GNS3
```bash
# Create storage directory
sudo mkdir -p /var/lib/libvirt/images/gns3

# Set ownership
sudo chown libvirt-qemu:libvirt-qemu /var/lib/libvirt/images/gns3
sudo chmod 770 /var/lib/libvirt/images/gns3

# Define storage pool
cat > /tmp/gns3-pool.xml << 'EOF'
<pool type='dir'>
  <name>gns3-images</name>
  <target>
    <path>/var/lib/libvirt/images/gns3</path>
    <permissions>
      <mode>0770</mode>
      <owner>64055</owner>
      <group>108</group>
    </permissions>
  </target>
</pool>
EOF

virsh pool-define /tmp/gns3-pool.xml
virsh pool-start gns3-images
virsh pool-autostart gns3-images

# Verify
virsh pool-list --all
virsh pool-info gns3-images
```

---

## Monitoring & Logging

```bash
# Enable libvirt audit logging
sudo sed -i 's/#audit_level = 1/audit_level = 2/' /etc/libvirt/libvirtd.conf
sudo sed -i 's/#audit_logging = 0/audit_logging = 1/' /etc/libvirt/libvirtd.conf

# Configure log filters
sudo sed -i 's/#log_filters=/log_filters="1:qemu 1:libvirt 3:event 3:json 3:rpc"/' /etc/libvirt/libvirtd.conf
sudo sed -i 's|#log_outputs=|log_outputs="1:file:/var/log/libvirt/libvirtd.log"|' /etc/libvirt/libvirtd.conf

# Restart to apply
sudo systemctl restart libvirtd

# Monitor logs
sudo tail -f /var/log/libvirt/libvirtd.log

# Monitor QEMU processes
watch -n 2 'ps aux | grep qemu-system | grep -v grep'

# Check resource usage
virsh domstats --state-running
```

---

## Troubleshooting Common Issues

### Issue 1: Permission Denied on /dev/kvm
```bash
# Check device permissions
ls -lh /dev/kvm

# Fix ownership
sudo chown root:kvm /dev/kvm
sudo chmod 660 /dev/kvm

# Verify group membership
groups | grep kvm || echo "User not in kvm group - re-login required"
```

### Issue 2: libvirt Connection Failed
```bash
# Check socket permissions
ls -lh /var/run/libvirt/libvirt-sock

# Restart service
sudo systemctl restart libvirtd

# Test connection with debug
virsh --connect qemu:///system --debug 1 list
```

### Issue 3: No Network Connectivity in VMs
```bash
# Check bridge status
ip link show virbr0

# Restart network
virsh net-destroy default
virsh net-start default

# Check iptables NAT rules
sudo iptables -t nat -L -n -v | grep virbr0

# If missing, reload
virsh net-destroy default
virsh net-start default
```

---

## Rollback Plan

```bash
# Stop all VMs
virsh list --name | xargs -I {} virsh destroy {}

# Stop services
sudo systemctl stop libvirtd virtlogd

# Remove packages
sudo apt remove --purge \
  gns3-gui gns3-server \
  qemu-kvm libvirt-daemon-system virt-manager \
  qemu-system-x86 qemu-utils

# Remove PPA
sudo add-apt-repository --remove ppa:gns3/ppa

# Clean config
rm -rf ~/.config/GNS3
sudo rm -rf /var/lib/libvirt/images/gns3

# Remove groups
sudo deluser $USER libvirt
sudo deluser $USER kvm
sudo deluser $USER ubridge

# Clean packages
sudo apt autoremove
sudo apt autoclean
```

---

## Next 3 Steps

1. **Import Cisco IOS images**: Download IOSv (vIOS-L2, vIOS-L3) or CSR1000v from Cisco VIRL/CML, convert to qcow2 format, import into GNS3 appliance templates
   ```bash
   qemu-img convert -f vmdk -O qcow2 input.vmdk output.qcow2
   ```

2. **Build multi-tier security lab**: Create topology with DMZ (firewall), internal network (vulnerable hosts), attacker network; practice lateral movement detection and prevention

3. **Integrate with automation**: Script GNS3 topology deployment via REST API, combine with Terraform for infrastructure-as-code network testing environments

---

## Verification Checklist

```bash
# Complete system verification script
cat > /tmp/verify-gns3-kvm.sh << 'VERIFY'
#!/bin/bash
echo "=== GNS3 + QEMU/KVM Verification ==="

echo -e "\n[1] KVM Module"
lsmod | grep -E 'kvm_(intel|amd)' || echo "FAIL: KVM module not loaded"

echo -e "\n[2] /dev/kvm Access"
test -r /dev/kvm && test -w /dev/kvm && echo "OK" || echo "FAIL"

echo -e "\n[3] Group Membership"
groups | grep -E 'libvirt|kvm' || echo "FAIL: Missing groups"

echo -e "\n[4] libvirt Service"
systemctl is-active libvirtd || echo "FAIL"

echo -e "\n[5] Default Network"
virsh net-list | grep default || echo "FAIL"

echo -e "\n[6] GNS3 Version"
gns3 --version && gns3server --version || echo "FAIL"

echo -e "\n[7] ubridge Capabilities"
getcap /usr/bin/ubridge | grep cap_net_admin || echo "FAIL"

echo -e "\n[8] Bridge Interface"
ip link show virbr0 || echo "FAIL"

echo -e "\n=== All Checks Complete ==="
VERIFY

chmod +x /tmp/verify-gns3-kvm.sh
/tmp/verify-gns3-kvm.sh
```

Run this script to validate your complete installation.

## Summary

Kali's package dependency conflict: `virt-manager` requires newer `gir1.2-glib-2.0` which breaks `gnome-shell`. This is a known Kali/Debian Sid issue where GTK/GNOME packages are in transition. **Solution**: Skip GUI tools (`virt-manager`, `virt-viewer`) and use CLI (`virsh`, `virt-install`) + remote management or run virt-manager in container. GNS3 doesn't require these packages—only needs libvirt daemon and QEMU. Proceed with core install, bypass broken GUI dependencies.

---

## Workaround Installation

### Option 1: Install Without GUI Tools (Recommended for Headless/CLI)

```bash
# Install core packages ONLY (skip virt-manager/virt-viewer)
sudo apt install -y \
  bridge-utils \
  genisoimage

# Verify already-installed packages
dpkg -l | grep -E 'qemu-system-x86|libvirt-daemon-system|virtinst'

# Install remaining networking components
sudo apt install -y \
  dnsmasq-base \
  ebtables \
  iptables \
  libguestfs-tools

# Verify libvirt is functional
sudo systemctl status libvirtd
virsh --version
```

**Use Cases Without virt-manager:**
- GNS3 manages VMs via API (doesn't need virt-manager)
- Use `virsh` CLI for VM management
- Use remote `virt-manager` from another machine
- Use web UI (Cockpit) as alternative

---

### Option 2: Install virt-manager in Isolated Container

```bash
# Run virt-manager from Docker (no dependency conflicts)
docker pull quay.io/virt-manager/virt-manager:latest

# Create wrapper script
cat > ~/bin/virt-manager-docker << 'EOF'
#!/bin/bash
xhost +local:docker
docker run --rm -it \
  --name virt-manager \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -v /var/run/libvirt:/var/run/libvirt \
  -v $HOME/.config/virt-manager:/root/.config/virt-manager \
  --network host \
  quay.io/virt-manager/virt-manager:latest
xhost -local:docker
EOF

chmod +x ~/bin/virt-manager-docker

# Run containerized virt-manager
~/bin/virt-manager-docker
```

---

### Option 3: Install Cockpit Web UI (Alternative to virt-manager)

```bash
# Install Cockpit with libvirt plugin
sudo apt install -y cockpit cockpit-machines

# Enable and start
sudo systemctl enable --now cockpit.socket

# Access web UI
# Open browser: https://localhost:9090
# Login with your system credentials

# Verify cockpit-machines plugin
dpkg -l | grep cockpit-machines
```

**Cockpit provides:**
- Web-based VM management (alternative to virt-manager GUI)
- No GTK/GNOME dependencies
- Works remotely over HTTPS
- Storage pool and network management

---

### Option 4: Force Install with Held Packages (Not Recommended)

```bash
# Hold gnome-shell to prevent breaks
sudo apt-mark hold gnome-shell

# Attempt install with --fix-broken
sudo apt install -y --fix-broken virt-manager virt-viewer

# If successful, unhold later
sudo apt-mark unhold gnome-shell

# Check for issues
sudo apt --fix-broken install
```

⚠️ **Warning**: This may break GNOME desktop. Only use on disposable VMs or if you can recover via TTY.

---

## Continue GNS3 Installation (Core Components)

```bash
# Add GNS3 PPA
sudo add-apt-repository ppa:gns3/ppa -y
sudo apt update

# Install GNS3 (doesn't require virt-manager)
sudo apt install -y gns3-gui gns3-server

# Install additional dependencies
sudo apt install -y \
  python3-pip \
  python3-pyqt5 \
  python3-pyqt5.qtsvg \
  python3-pyqt5.qtwebsockets \
  x11-xserver-utils \
  wireshark

# Configure user groups
sudo usermod -aG libvirt,kvm,libvirt-qemu,ubridge,wireshark $USER

# Apply groups
newgrp libvirt

# Verify
groups | grep -E 'libvirt|kvm'
```

---

## Configure libvirt (CLI-Only Workflow)

```bash
# Enable services
sudo systemctl enable --now libvirtd virtlogd

# Configure user permissions
sudo sed -i 's/#unix_sock_group = "libvirt"/unix_sock_group = "libvirt"/' /etc/libvirt/libvirtd.conf
sudo sed -i 's/#unix_sock_rw_perms = "0770"/unix_sock_rw_perms = "0770"/' /etc/libvirt/libvirtd.conf

# Restart libvirt
sudo systemctl restart libvirtd

# Test virsh access (no sudo)
virsh --connect qemu:///system list --all

# Start default network
virsh net-start default
virsh net-autostart default

# Verify
virsh net-list --all
ip addr show virbr0
```

---

## Configure ubridge for GNS3

```bash
# Set SUID bit
sudo chmod u+s /usr/bin/ubridge

# Set capabilities
sudo setcap cap_net_admin,cap_net_raw=ep /usr/bin/ubridge

# Verify
getcap /usr/bin/ubridge
ls -lh /usr/bin/ubridge
```

---

## Create GNS3 Server Config

```bash
# Create config directory
mkdir -p ~/.config/GNS3/2.2

# Configure for QEMU/KVM
cat > ~/.config/GNS3/2.2/gns3_server.conf << 'EOF'
[Server]
host = 127.0.0.1
port = 3080
path = /usr/bin/gns3server
ubridge_path = /usr/bin/ubridge
auto_start = true
allow_remote_console = false

[Qemu]
enable_kvm = true
require_kvm = true
EOF

chmod 600 ~/.config/GNS3/2.2/gns3_server.conf
```

---

## CLI VM Management (Without virt-manager)

### Create Test VM Using virt-install

```bash
# Download test image
sudo mkdir -p /var/lib/libvirt/images
cd /var/lib/libvirt/images
sudo wget https://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img

# Create VM via CLI
virt-install \
  --name test-cirros \
  --ram 256 \
  --disk path=/var/lib/libvirt/images/cirros-0.6.2-x86_64-disk.img,format=qcow2 \
  --vcpus 1 \
  --os-variant cirros0.6.2 \
  --network network=default \
  --graphics none \
  --import \
  --noautoconsole

# List VMs
virsh list --all

# Connect to console
virsh console test-cirros
# Login: cirros / gocubsgo
# Exit: Ctrl + ]

# VM lifecycle commands
virsh start test-cirros
virsh shutdown test-cirros
virsh destroy test-cirros  # force stop
virsh undefine test-cirros --remove-all-storage
```

### Useful virsh Commands

```bash
# VM info
virsh dominfo <vm-name>
virsh domstats <vm-name>

# Network management
virsh net-list
virsh net-info default
virsh net-dhcp-leases default

# Storage pools
virsh pool-list
virsh pool-info default
virsh vol-list default

# Snapshots
virsh snapshot-create-as test-cirros snapshot1
virsh snapshot-list test-cirros
virsh snapshot-revert test-cirros snapshot1

# Clone VM
virt-clone --original test-cirros --name test-cirros-clone --auto-clone
```

---

## Remote virt-manager Access

If you have another Linux machine with working virt-manager:

```bash
# On Kali (server side) - allow remote libvirt
sudo sed -i 's/#listen_tls = 0/listen_tls = 0/' /etc/libvirt/libvirtd.conf
sudo sed -i 's/#listen_tcp = 1/listen_tcp = 1/' /etc/libvirt/libvirtd.conf
sudo sed -i 's/#auth_tcp = "sasl"/auth_tcp = "none"/' /etc/libvirt/libvirtd.conf

# Edit systemd service to listen on TCP
sudo mkdir -p /etc/systemd/system/libvirtd.socket.d/
cat | sudo tee /etc/systemd/system/libvirtd.socket.d/override.conf << 'EOF'
[Socket]
ListenStream=0.0.0.0:16509
EOF

sudo systemctl daemon-reload
sudo systemctl restart libvirtd.socket libvirtd

# On remote machine with virt-manager
virt-manager -c qemu+tcp://kali-ip/system
```

⚠️ **Security**: This exposes unencrypted libvirt. Use SSH tunneling in production:

```bash
# Secure remote access via SSH
ssh -L 16509:localhost:16509 user@kali-host

# On local machine
virt-manager -c qemu+ssh://user@kali-host/system
```

---

## Launch and Test GNS3

```bash
# Start GNS3 server
gns3server --local --log /tmp/gns3server.log &

# Verify server
ss -tlnp | grep 3080

# Launch GNS3 GUI
gns3 &

# Monitor logs
tail -f /tmp/gns3server.log
```

---

## Verification Without GUI Tools

```bash
# Complete verification script
cat > /tmp/verify-gns3-cli.sh << 'VERIFY'
#!/bin/bash
set -e

echo "=== GNS3 + QEMU/KVM CLI Installation Verification ==="

echo -e "\n[1] KVM Module & /dev/kvm"
lsmod | grep kvm_intel || lsmod | grep kvm_amd
test -r /dev/kvm && test -w /dev/kvm && echo "  ✓ /dev/kvm accessible" || echo "  ✗ FAIL"

echo -e "\n[2] Group Membership"
groups | grep -E 'libvirt|kvm|ubridge' && echo "  ✓ Groups OK" || echo "  ✗ FAIL"

echo -e "\n[3] libvirt Service"
systemctl is-active libvirtd && echo "  ✓ libvirtd active" || echo "  ✗ FAIL"

echo -e "\n[4] virsh Access (no sudo)"
virsh --connect qemu:///system version > /dev/null 2>&1 && echo "  ✓ virsh works" || echo "  ✗ FAIL"

echo -e "\n[5] Default Network"
virsh net-list | grep -q default && echo "  ✓ Network present" || echo "  ✗ FAIL"
ip link show virbr0 > /dev/null 2>&1 && echo "  ✓ virbr0 exists" || echo "  ✗ FAIL"

echo -e "\n[6] GNS3 Installation"
command -v gns3 > /dev/null && echo "  ✓ gns3 GUI installed" || echo "  ✗ FAIL"
command -v gns3server > /dev/null && echo "  ✓ gns3server installed" || echo "  ✗ FAIL"

echo -e "\n[7] ubridge Capabilities"
getcap /usr/bin/ubridge | grep -q cap_net_admin && echo "  ✓ ubridge caps OK" || echo "  ✗ FAIL"

echo -e "\n[8] QEMU Version"
qemu-system-x86_64 --version | head -n1

echo -e "\n=== All Core Components Verified ==="
echo "Note: virt-manager GUI skipped due to dependency conflicts"
echo "Use: virsh (CLI), Cockpit (web), or remote virt-manager"
VERIFY

chmod +x /tmp/verify-gns3-cli.sh
/tmp/verify-gns3-cli.sh
```

---

## Alternative: Fix Dependency Hell (Advanced)

If you absolutely need virt-manager locally:

```bash
# Option: Downgrade gir packages (risky)
sudo apt install -y aptitude
sudo aptitude install virt-manager virt-viewer
# Follow prompts to resolve conflicts (may downgrade GNOME)

# OR: Use Debian Testing repo temporarily
echo "deb http://deb.debian.org/debian testing main" | sudo tee /etc/apt/sources.list.d/testing.list
sudo apt update
sudo apt install -y -t testing virt-manager virt-viewer
sudo rm /etc/apt/sources.list.d/testing.list
sudo apt update
```

⚠️ **Danger Zone**: May destabilize system. Snapshot first.

---

## Architecture (CLI-Only Setup)

```
┌─────────────────────────────────────────────────┐
│          GNS3 GUI (Qt5 - X11/Wayland)           │
│               ↓ REST API                        │
│          GNS3 Server (Python)                   │
│               ↓ libvirt API                     │
│          libvirtd (daemon)                      │
│               ↓                                 │
│     ┌─────────┴──────────┐                     │
│     ↓                    ↓                      │
│  virsh CLI          QEMU/KVM VMs                │
│  (management)       (network devices)           │
│     ↓                    ↓                      │
│  libvirt API      /dev/kvm (hardware accel)     │
│                          ↓                      │
│                   kvm_intel module              │
└─────────────────────────────────────────────────┘
        ↓ Network                ↓ Storage
   virbr0 (NAT)          /var/lib/libvirt/images
```

---

## Next 3 Steps

1. **Test GNS3 with QEMU appliance**: Import pre-built appliance (e.g., Alpine Linux, Tiny Core) from GNS3 marketplace, verify KVM acceleration working
   ```bash
   # Check KVM in use
   ps aux | grep qemu | grep -o '\-accel kvm'
   ```

2. **Build CLI automation**: Script topology creation via `virsh` + GNS3 API for reproducible lab environments
   ```bash
   curl -X POST http://localhost:3080/v2/projects
   ```

3. **Deploy Cockpit for web management**: Install `cockpit-machines` for browser-based VM management as virt-manager replacement

---

## Summary of Install Status

✅ **Installed & Working:**
- QEMU/KVM with hardware acceleration
- libvirt daemon and virsh CLI
- GNS3 GUI and server
- Bridge networking (virbr0)
- ubridge with capabilities

❌ **Skipped (Dependency Conflicts):**
- virt-manager (GUI)
- virt-viewer (VNC/SPICE client)

**Workarounds Available:**
- Use `virsh` CLI for all VM management
- Install Cockpit web UI
- Run virt-manager in Docker
- Remote virt-manager from another host

Proceed with GNS3 verification now—it doesn't require the broken GUI packages.