# Comprehensive Security Implementation Guide: IAM, RBAC, and Compliance

> **Summary (4–8 lines):** This guide delivers a first-principles, production-grade treatment of Identity and Access Management (IAM), Role-Based Access Control (RBAC), and compliance frameworks — from kernel-level Linux primitives through cloud control planes to distributed system enforcement. We cover the full stack: Linux DAC/MAC/capabilities, PAM, POSIX ACLs, kernel namespaces, cgroups, seccomp, LSMs (SELinux/AppArmor), cloud IAM (AWS/GCP/Azure), SPIFFE/SPIRE-based workload identity, policy-as-code (OPA/Rego), and compliance automation (SOC2, PCI-DSS, FedRAMP, ISO 27001). Go and Rust implementations are provided for enforcement engines, token validators, audit loggers, and policy evaluators. Threat models, failure modes, and rollback strategies are included for every major component.

---

## Table of Contents

1. [Identity Foundations: First Principles](#1-identity-foundations-first-principles)
2. [Linux Identity and Access Primitives](#2-linux-identity-and-access-primitives)
3. [Linux Security Modules (LSM): SELinux and AppArmor](#3-linux-security-modules-lsm-selinux-and-apparmor)
4. [Capabilities, Namespaces, cgroups, and Seccomp](#4-capabilities-namespaces-cgroups-and-seccomp)
5. [PAM: Pluggable Authentication Modules](#5-pam-pluggable-authentication-modules)
6. [RBAC: Design, Taxonomy, and Formal Models](#6-rbac-design-taxonomy-and-formal-models)
7. [Cloud IAM: AWS, GCP, Azure Deep Dive](#7-cloud-iam-aws-gcp-azure-deep-dive)
8. [Workload Identity: SPIFFE/SPIRE](#8-workload-identity-spiffespire)
9. [Policy-as-Code: OPA/Rego and Cedar](#9-policy-as-code-oparego-and-cedar)
10. [Kubernetes RBAC and Admission Control](#10-kubernetes-rbac-and-admission-control)
11. [Go Implementation: IAM Enforcement Engine](#11-go-implementation-iam-enforcement-engine)
12. [Rust Implementation: Policy Evaluator and Token Validator](#12-rust-implementation-policy-evaluator-and-token-validator)
13. [Secrets Management: Vault, SOPS, KMS](#13-secrets-management-vault-sops-kms)
14. [Audit Logging and Non-Repudiation](#14-audit-logging-and-non-repudiation)
15. [Compliance Frameworks: SOC2, PCI-DSS, FedRAMP, ISO 27001](#15-compliance-frameworks-soc2-pci-dss-fedramp-iso-27001)
16. [Compliance-as-Code Automation](#16-compliance-as-code-automation)
17. [Threat Model: Full Stack IAM](#17-threat-model-full-stack-iam)
18. [Testing, Fuzzing, and Benchmarking](#18-testing-fuzzing-and-benchmarking)
19. [Roll-out and Rollback Strategies](#19-roll-out-and-rollback-strategies)
20. [Next 3 Steps](#20-next-3-steps)
21. [References](#21-references)

---

## 1. Identity Foundations: First Principles

### 1.1 What Is Identity?

Identity is the answer to: **"Who or what is making this request?"** In security systems, identity is the root from which all authorization, audit, and accountability derive. Without strong identity, RBAC collapses — you cannot enforce "what a principal can do" if you cannot verify "who the principal is."

Identity has three attributes:
- **Identifier**: A name, UID, certificate CN, or cryptographic key that uniquely identifies a principal.
- **Credential**: Proof of identity — password, private key, hardware token, biometric.
- **Assertion**: A claim made by a trusted authority that binds an identifier to a credential — JWTs, X.509 certificates, Kerberos tickets, SAML assertions.

### 1.2 The AAA Model

```
+---------------+    +---------------+    +---------------+
| Authentication|    | Authorization |    |   Accounting  |
|               |    |               |    |               |
| Who are you?  |--->| What can you  |--->| What did you  |
| Prove it.     |    | do?           |    | do?           |
+---------------+    +---------------+    +---------------+
      ^                      ^                    ^
      |                      |                    |
  Credential            Policy Store          Audit Log
  Validation            (RBAC/ABAC)           (Immutable)
```

### 1.3 Principal Types

| Principal Type    | Example                          | Identity Source               |
|-------------------|----------------------------------|-------------------------------|
| Human User        | engineer@corp.com                | IdP (Okta, AD, LDAP)         |
| Service Account   | svc-payment@project.iam          | Cloud IAM, Kubernetes SA      |
| Workload          | spiffe://cluster/ns/default/sa   | SPIFFE/SPIRE                  |
| Device            | TPM-backed cert CN=device-001    | mTLS + device attestation     |
| Non-human (CI/CD) | github-actions OIDC token        | OIDC federation               |
| Role              | arn:aws:iam::123:role/ops        | Assumed via STS               |

### 1.4 Authentication Protocols

```
+----------------------------+----------+----------------+-------------------+
| Protocol                   | Transport| Trust Model    | Token Format      |
+----------------------------+----------+----------------+-------------------+
| Kerberos                   | UDP/TCP  | Shared secret  | Kerberos ticket   |
| LDAP/AD                    | TCP 389  | Directory      | Distinguished Name|
| SAML 2.0                   | HTTP POST| PKI + XML sig  | XML assertion     |
| OAuth 2.0                  | HTTPS    | Auth server    | Opaque token      |
| OIDC (OpenID Connect)      | HTTPS    | Auth server    | JWT (id_token)    |
| mTLS                       | TLS 1.3  | PKI / CA       | X.509 cert        |
| SPIFFE/SPIRE               | gRPC     | PKI + OIDC     | SVID (JWT/X.509)  |
| AWS SigV4                  | HTTPS    | HMAC-SHA256    | Signed request    |
+----------------------------+----------+----------------+-------------------+
```

### 1.5 Authorization Models Compared

```
+----------+---------------------------------------+-----------------------------+
| Model    | Decision Basis                        | Use Case                    |
+----------+---------------------------------------+-----------------------------+
| DAC      | Owner sets permissions                | POSIX filesystem            |
| MAC      | System policy, labels                 | SELinux, MLS, government    |
| RBAC     | Role memberships + role permissions   | Enterprise, Kubernetes      |
| ABAC     | Attributes of subject/resource/env    | Fine-grained cloud IAM      |
| ReBAC    | Relationship graph between entities   | Google Zanzibar, SpiceDB    |
| PBAC     | Declarative policy evaluation         | OPA, Cedar, Casbin          |
+----------+---------------------------------------+-----------------------------+
```

### 1.6 The Principle of Least Privilege (PoLP)

PoLP is non-negotiable. Every principal gets the **minimum permissions required to complete its function, for the minimum time necessary, with the minimum scope**.

Implementation dimensions:
- **Permission scope**: Read vs. write vs. admin
- **Resource scope**: Specific ARN/resource, not wildcards
- **Temporal scope**: Short-lived credentials (STS, SVID TTL)
- **Network scope**: VPC, security group, network policy
- **Data scope**: Row-level security, field-level encryption

---

## 2. Linux Identity and Access Primitives

### 2.1 Linux Process Identity Model

Every Linux process carries an identity context in its task_struct:

```c
// kernel/include/linux/cred.h (simplified)
struct cred {
    atomic_t    usage;
    kuid_t      uid;        // Real UID
    kgid_t      gid;        // Real GID
    kuid_t      suid;       // Saved UID
    kgid_t      sgid;       // Saved GID
    kuid_t      euid;       // Effective UID (used for access checks)
    kgid_t      egid;       // Effective GID
    kuid_t      fsuid;      // Filesystem UID
    kgid_t      fsgid;      // Filesystem GID
    struct group_info *group_info;  // Supplementary groups
    kernel_cap_t cap_inheritable;
    kernel_cap_t cap_permitted;
    kernel_cap_t cap_effective;
    kernel_cap_t cap_bset;  // Capability bounding set
    kernel_cap_t cap_ambient;
    // LSM blobs, seccomp filters, etc.
};
```

- **euid/egid**: Used for filesystem and IPC access checks. `setuid` binaries switch euid to 0 or owner.
- **fsuid/fsgid**: Controls filesystem access independently of euid — critical for NFS servers.
- **suid/sgid**: Saved set-user-ID allows regaining elevated privileges after dropping them temporarily.

### 2.2 Discretionary Access Control (DAC): POSIX Permissions

Standard POSIX permission model — 9 bits + sticky/setuid/setgid:

```
-rwxr-xr--  1 alice devs 4096 Jan 1 00:00 binary
 ||||||||| 
 ||||||+++-- Other: r-x (5)
 |||+++------ Group (devs): r-x (5)
 +++--------- Owner (alice): rwx (7)
 ^----------- Type: - regular file

Special bits (octal prefix):
  4000 = setuid  (euid becomes file owner on exec)
  2000 = setgid  (egid becomes file group on exec, or dir inheritance)
  1000 = sticky  (only owner can delete in shared dir, e.g., /tmp)
```

**Kernel DAC check path** (simplified):
```
sys_open()
  -> do_filp_open()
    -> may_open()
      -> inode_permission()
        -> generic_permission()  // checks uid/gid bits
          -> acl_permission_check()  // POSIX ACL override if present
            -> security_inode_permission()  // LSM hook
```

**POSIX ACL** (extends DAC beyond owner/group/other):
```bash
# Install acl tools
apt install acl

# Set ACL: give 'ci-user' read+execute on /app/binary
setfacl -m u:ci-user:rx /app/binary

# Give group 'auditors' read-only on /var/log/app/
setfacl -R -m g:auditors:r /var/log/app/

# Default ACLs on directories (inherited by new files)
setfacl -d -m g:devs:rwx /srv/shared/

# View ACLs
getfacl /app/binary

# Mask: effective permission = ACL & mask
# mask limits named user/group ACEs
setfacl -m m:rx /app/binary  # mask = r-x

# Remove ACL
setfacl -b /app/binary
```

**Production security hardening — DAC**:
```bash
# Find world-writable files (critical misconfiguration)
find / -xdev -type f -perm -0002 -not -path "/proc/*" 2>/dev/null

# Find setuid/setgid binaries
find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null

# Find files with no owner (orphaned)
find / -xdev \( -nouser -o -nogroup \) -type f 2>/dev/null

# Harden /tmp: noexec, nosuid, nodev
echo "tmpfs /tmp tmpfs defaults,noexec,nosuid,nodev,size=1G 0 0" >> /etc/fstab

# Immutable files with chattr
chattr +i /etc/passwd /etc/shadow /etc/sudoers
lsattr /etc/passwd  # ----i-------------- /etc/passwd
```

### 2.3 /etc/passwd, /etc/shadow, and /etc/group

```bash
# /etc/passwd format (world-readable, no passwords since shadow):
# login:x:UID:GID:comment:home:shell
root:x:0:0:root:/root:/bin/bash
svc-app:x:1001:1001:App Service Account:/var/lib/app:/bin/false

# /etc/shadow format (root-only r--------):
# login:hashed_pw:last_change:min:max:warn:inactive:expire:reserved
svc-app:!:19000:0:99999:7:::   # '!' = locked, '*' = no password login

# /etc/group format:
# group:x:GID:member1,member2
devs:x:2000:alice,bob
auditors:x:2001:charlie

# Lock/unlock account
usermod -L svc-app   # Lock (prepends ! to hash)
usermod -U svc-app   # Unlock

# System accounts: UID < 1000 (distro-dependent), no login shell
useradd -r -s /bin/false -d /nonexistent svc-daemon

# Expire account on a date
usermod -e 2025-12-31 contractor1

# Force password change on next login
chage -d 0 user1

# View aging info
chage -l user1
```

**Password hashing (modern)**:
```bash
# /etc/shadow hash field: $algorithm$salt$hash
# $6$  = SHA-512 (crypt)
# $y$  = yescrypt (modern, Debian/RHEL 9+)
# $2b$ = bcrypt

# Generate strong hash
python3 -c "import crypt; print(crypt.crypt('password', crypt.mksalt(crypt.METHOD_SHA512)))"

# PAM configuration for strong hashing (/etc/pam.d/common-password):
# password required pam_unix.so sha512 shadow rounds=65536
```

### 2.4 sudo and sudoers

```bash
# /etc/sudoers (always edit with visudo - validates syntax)
# Format: WHO  WHERE=(AS_WHO:AS_GROUP)  WHAT

# User alice can run all commands as root on all hosts
alice ALL=(ALL:ALL) ALL

# Group devs can restart nginx without password
%devs ALL=(root) NOPASSWD: /bin/systemctl restart nginx

# Service account can only run specific binary
svc-deploy ALL=(root) NOPASSWD: /usr/local/bin/deploy.sh

# Restrict to specific hosts
alice webserver01=(ALL) ALL

# Command aliases for reuse
Cmnd_Alias NETWORK_CMDS = /sbin/ip, /sbin/iptables, /usr/sbin/nmap

# Prevent privilege escalation via shell escapes
Defaults requiretty
Defaults use_pty
Defaults log_input, log_output
Defaults logfile=/var/log/sudo.log
Defaults passwd_timeout=1
Defaults timestamp_timeout=0    # Require re-auth every time

# Sudoers.d drop-ins (preferred over editing main sudoers)
echo "svc-deploy ALL=(root) NOPASSWD: /usr/local/bin/deploy.sh" \
  > /etc/sudoers.d/svc-deploy
chmod 440 /etc/sudoers.d/svc-deploy
```

**sudo threat vectors and mitigations**:

| Threat | Mitigation |
|--------|-----------|
| Shell escapes (vim `:!sh`) | `NOEXEC` tag, restrict allowed commands |
| env var injection | `Defaults env_reset`, `secure_path` |
| PATH hijacking | Absolute paths only in sudoers |
| Timestamp reuse | `timestamp_timeout=0` |
| Log bypass | `log_output`, centralized syslog |
| TOCTOU on script files | Restrict to compiled binaries |

### 2.5 /etc/sudoers vs polkit

```bash
# polkit (PolicyKit) - for D-Bus privileged operations
# More granular than sudo for system services

# View polkit rules
pkaction --verbose --action-id org.freedesktop.systemd1.manage-units

# Custom polkit rule (/etc/polkit-1/rules.d/10-devs.rules):
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        subject.isInGroup("devs")) {
        return polkit.Result.YES;
    }
});
```

### 2.6 Linux Extended Attributes (xattrs) and Security Labels

```bash
# xattrs are used by SELinux, IMA, capabilities
# Namespaces: user.*, system.*, security.*, trusted.*

# View all xattrs
getfattr -d -m - /path/to/file

# SELinux label (security.selinux)
getfattr -n security.selinux /bin/bash

# IMA/EVM integrity measurement (security.ima, security.evm)
getfattr -n security.ima /etc/passwd

# Capability xattrs (file capabilities, preferred over setuid)
# security.capability namespace
getcap /usr/bin/ping   # cap_net_raw=ep
setcap cap_net_raw+ep /usr/bin/ping
setcap -r /usr/bin/ping  # Remove capabilities
```

---

## 3. Linux Security Modules (LSM): SELinux and AppArmor

### 3.1 LSM Architecture

The Linux Security Module framework provides hooks at hundreds of kernel operations. Every major kernel operation calls through LSM hooks that can be intercepted by loaded modules:

```
User Process
     |
     | syscall (open, exec, connect, socket, mmap...)
     v
+----+----+
| VFS /   |
| Kernel  |
+----+----+
     |
     | LSM Hook: security_inode_permission()
     |           security_file_open()
     |           security_socket_connect()
     |           security_bprm_check()
     v
+----+----+----+----+
| SELinux |AppArmor |  (stacked in 5.1+)
+---------+---------+
     |
     | Policy Decision: ALLOW / DENY / AUDIT
     v
 Operation proceeds or AVC denial logged to audit
```

Multiple LSMs can be stacked (Linux 5.1+). SELinux and Yama are commonly co-loaded.

### 3.2 SELinux Deep Dive

SELinux implements **Mandatory Access Control** using a **Type Enforcement (TE)** model with optional **Multi-Level Security (MLS)** and **Multi-Category Security (MCS)**.

**Security Context (label)**:
```
user:role:type:level
  ^     ^    ^    ^
  |     |    |    +-- MLS level: s0:c0,c256 (sensitivity:categories)
  |     |    +------- Type: httpd_t, var_t, sshd_exec_t
  |     +------------ Role: system_r, user_r, sysadm_r
  +------------------ SELinux user: system_u, unconfined_u
```

**Key concepts**:
- **Domain**: The type of a process (e.g., `httpd_t`)
- **Type**: Label on files, sockets, devices (e.g., `httpd_sys_content_t`)
- **Type Transition**: When a process execs a binary, its domain transitions to the target type
- **AVC (Access Vector Cache)**: Kernel cache of allow/deny decisions
- **Policy modules**: Binary policy loaded via `semodule`

```bash
# Check SELinux status
getenforce        # Enforcing / Permissive / Disabled
sestatus -v

# Modes:
# Enforcing: denies and logs
# Permissive: logs but does not deny (for debugging)
# Disabled: no policy loaded (requires reboot to enable)

setenforce 0   # Switch to Permissive (runtime, not persistent)
setenforce 1   # Switch to Enforcing

# Persistent in /etc/selinux/config:
# SELINUX=enforcing
# SELINUXTYPE=targeted  # or mls, minimum

# View process label
ps -eZ | grep httpd
# system_u:system_r:httpd_t:s0   1234 httpd

# View file label
ls -Z /var/www/html/
# system_u:object_r:httpd_sys_content_t:s0 index.html

# Change file label
chcon -t httpd_sys_content_t /srv/myapp/html/
restorecon -Rv /srv/myapp/html/   # Restore to policy default

# Set default label for path (persistent across relabel)
semanage fcontext -a -t httpd_sys_content_t "/srv/myapp/html(/.*)?"
restorecon -Rv /srv/myapp/html/

# View AVC denials (audit log)
ausearch -m AVC,USER_AVC -ts recent
audit2why < /var/log/audit/audit.log

# Generate policy module from denials
audit2allow -a -M myapp_policy
semodule -i myapp_policy.pp

# View loaded policy modules
semodule -l

# Booleans: runtime policy switches
getsebool -a | grep httpd
setsebool -P httpd_can_network_connect on   # Persistent (-P)

# Allow httpd to connect to network (instead of writing custom policy)
setsebool -P httpd_can_network_connect_db on

# Port labeling
semanage port -l | grep http
semanage port -a -t http_port_t -p tcp 8080
```

**Writing a SELinux Policy Module**:
```bash
# myapp.te (Type Enforcement file)
cat > myapp.te << 'EOF'
policy_module(myapp, 1.0)

# Declare types
type myapp_t;           # Process domain
type myapp_exec_t;      # Binary file type
type myapp_log_t;       # Log file type
type myapp_data_t;      # Data directory type
type myapp_port_t;      # Network port type

# Domain transition: init_t executes myapp_exec_t -> myapp_t
application_domain(myapp_t, myapp_exec_t)
init_daemon_domain(myapp_t, myapp_exec_t)

# Allow myapp to read its data
allow myapp_t myapp_data_t:dir { read getattr search open };
allow myapp_t myapp_data_t:file { read getattr open };

# Allow myapp to write logs
logging_write_generic_logs(myapp_t)
allow myapp_t myapp_log_t:file { create write append open getattr };

# Allow myapp to bind to its port
allow myapp_t myapp_port_t:tcp_socket { name_bind name_connect };
corenet_tcp_bind_generic_node(myapp_t)

# Network access: connect outbound to http_port_t
corenet_tcp_connect_http_port(myapp_t)
EOF

# myapp.fc (File Contexts)
cat > myapp.fc << 'EOF'
/usr/sbin/myapp         --      gen_context(system_u:object_r:myapp_exec_t,s0)
/var/lib/myapp(/.*)?            gen_context(system_u:object_r:myapp_data_t,s0)
/var/log/myapp(/.*)?            gen_context(system_u:object_r:myapp_log_t,s0)
EOF

# myapp.if (Interface - exported macros for other modules)
cat > myapp.if << 'EOF'
interface(`myapp_read_data',`
    gen_require(`
        type myapp_data_t;
    ')
    read_files_pattern($1, myapp_data_t, myapp_data_t)
')
EOF

# Build and install
make -f /usr/share/selinux/devel/Makefile myapp.pp
semodule -i myapp.pp

# Verify
seinfo -t myapp_t
sesearch --allow -s myapp_t
```

### 3.3 MLS/MCS Security Levels

```bash
# MLS: Multi-Level Security (Bell-LaPadula model)
# s0 = Unclassified
# s1 = Confidential
# s2 = Secret  
# s3 = Top Secret

# MCS: Multi-Category Security (used in containers/VMs)
# Each container gets unique category pair: s0:c1,c2
# Prevents container A (s0:c1,c2) from accessing container B (s0:c3,c4) data

# Assign MCS label to container process
runcon -t svirt_lxc_net_t -l s0:c100,c200 -- /bin/bash

# In Kubernetes: each pod's files get unique MCS label via container runtime
# This is the SELinux-based container isolation mechanism
```

### 3.4 AppArmor Deep Dive

AppArmor uses **path-based** access control (simpler than SELinux type enforcement). Each profile confines a specific program to a defined set of paths and capabilities.

```bash
# Status
aa-status
apparmor_status

# Modes
# enforce: denies + logs
# complain: logs only (like SELinux permissive)
# disabled

# Switch modes
aa-enforce /etc/apparmor.d/usr.sbin.nginx
aa-complain /etc/apparmor.d/usr.sbin.nginx
aa-disable /etc/apparmor.d/usr.sbin.mysqld

# Load profile
apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx
apparmor_parser -R /etc/apparmor.d/profile  # Remove

# Generate profile from scratch (uses aa-logprof to learn)
aa-genprof /usr/bin/myapp   # Runs app, captures violations, builds profile

# View logs
journalctl -k | grep apparmor
dmesg | grep apparmor
```

**Writing an AppArmor Profile**:
```
#include <tunables/global>

/usr/sbin/myapp {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Capabilities
  capability net_bind_service,
  capability setuid,
  capability setgid,

  # Binary and libraries
  /usr/sbin/myapp mr,
  /usr/lib/** rm,
  /lib/x86_64-linux-gnu/** rm,

  # Config files (read-only)
  /etc/myapp/  r,
  /etc/myapp/** r,

  # Data directory (read-write)
  /var/lib/myapp/  rw,
  /var/lib/myapp/** rw,

  # Log files (append only - critical for log integrity)
  /var/log/myapp/ rw,
  /var/log/myapp/*.log a,

  # PID file
  /var/run/myapp.pid rw,

  # Unix socket
  /var/run/myapp.sock rw,

  # Deny everything else explicitly
  deny /etc/shadow r,
  deny /proc/*/mem rw,
  deny @{HOME}/** w,

  # Network
  network inet tcp,
  network inet6 tcp,

  # Signals (only from init)
  signal receive peer=/sbin/init,

  # Deny ptrace (anti-debugging)
  deny ptrace,
}
```

**AppArmor for containers (Docker/containerd)**:
```bash
# Docker default AppArmor profile: docker-default
# Loaded automatically for all containers
cat /etc/apparmor.d/docker-default

# Use custom profile for container
docker run --security-opt apparmor=my-profile nginx

# containerd / CRI-O: set in pod annotation
# container.apparmor.security.beta.kubernetes.io/mycontainer: localhost/my-profile
```

---

## 4. Capabilities, Namespaces, cgroups, and Seccomp

### 4.1 Linux Capabilities

Capabilities divide the monolithic root privilege into 41 distinct units. This enables fine-grained privilege granting without full root.

```c
// Complete capability list (relevant subset)
CAP_AUDIT_WRITE      // Write to kernel audit log
CAP_CHOWN            // Change file ownership
CAP_DAC_OVERRIDE     // Bypass DAC read/write/execute
CAP_DAC_READ_SEARCH  // Bypass DAC for read and search
CAP_FOWNER           // Bypass permission checks for uid != euid
CAP_FSETID           // Set setuid/setgid bits
CAP_KILL             // Send signals to any process
CAP_MKNOD            // Create device files
CAP_NET_ADMIN        // Network admin (interface, routing, iptables)
CAP_NET_BIND_SERVICE // Bind to ports < 1024
CAP_NET_RAW          // Use RAW sockets (ping, tcpdump)
CAP_SETFCAP          // Set file capabilities
CAP_SETGID           // Manipulate GIDs
CAP_SETPCAP          // Modify process capability sets
CAP_SETUID           // Manipulate UIDs
CAP_SYS_ADMIN        // Mount, sethostname, ptrace, etc. (very broad!)
CAP_SYS_BOOT         // reboot()
CAP_SYS_CHROOT       // chroot()
CAP_SYS_MODULE       // Load/unload kernel modules
CAP_SYS_PTRACE       // ptrace() any process
CAP_SYS_RAWIO        // iopl(), direct I/O
CAP_SYS_TIME         // settimeofday()
```

**Capability sets per process**:
```
Permitted (P):    Max capabilities thread may assume
Effective (E):    Currently active capabilities
Inheritable (I):  Capabilities preserved across exec (new)
Bounding (B):     Hard limit — even root cannot exceed
Ambient (A):      Capabilities passed to non-privileged exec (Linux 4.3+)
```

**Inheritance rules**:
```
# On exec():
P' = (P & I) | (F_permitted & bounding_set)
E' = P' if file has setuid, else (P' & F_effective)
I' = I & I(file)  [if not setuid]
A' = A & P'       [ambient passes through if permitted]

# F = file capability xattr (security.capability)
```

```bash
# View capabilities of a running process
cat /proc/$$/status | grep -E "^Cap"
# CapInh: 0000000000000000
# CapPrm: 0000003fffffffff
# CapEff: 0000003fffffffff
# CapBnd: 0000003fffffffff
# CapAmb: 0000000000000000

# Decode hex capability mask
capsh --decode=0000003fffffffff

# Drop capabilities in shell (simulate restricted environment)
capsh --drop=cap_net_raw,cap_sys_admin --print -- -c "id; ping -c1 8.8.8.8"

# File capabilities (preferred over setuid)
setcap cap_net_bind_service+ep /usr/sbin/myapp   # +ep = effective,permitted
getcap /usr/sbin/myapp

# Run process with specific capabilities only
capsh --caps="cap_net_bind_service+eip" -- -c /usr/sbin/myapp

# Containers: drop all, add only what's needed
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx
```

**CAP_SYS_ADMIN is dangerous** — it enables:
- Mounting filesystems
- ptrace of any process
- sethostname/setdomainname
- ioctl for various devices
- quota control
- swapon/swapoff

Never grant CAP_SYS_ADMIN to containers unless absolutely required.

### 4.2 Linux Namespaces

Namespaces provide isolation by virtualizing global kernel resources. Each namespace has its own view:

```
+--------+---------+----------------------------+---------------------------+
| NS     | Flag    | Isolates                   | Introduced                |
+--------+---------+----------------------------+---------------------------+
| mnt    | CLONE_NEWNS   | Mount points          | Linux 2.4.19              |
| uts    | CLONE_NEWUTS  | hostname, domainname  | Linux 2.6.19              |
| ipc    | CLONE_NEWIPC  | SysV IPC, POSIX MQ    | Linux 2.6.19              |
| pid    | CLONE_NEWPID  | Process IDs           | Linux 2.6.24              |
| net    | CLONE_NEWNET  | Network stack         | Linux 2.6.24              |
| user   | CLONE_NEWUSER | UIDs/GIDs             | Linux 3.8                 |
| cgroup | CLONE_NEWCGROUP| cgroup root view     | Linux 4.6                 |
| time   | CLONE_NEWTIME | CLOCK_MONOTONIC etc.  | Linux 5.6                 |
+--------+---------+----------------------------+---------------------------+
```

**User namespaces** are particularly important for rootless containers:
```bash
# Map container UID 0 -> host UID 100000
# /etc/subuid: alice:100000:65536
# /etc/subgid: alice:100000:65536

# See namespace memberships
ls -la /proc/$$/ns/

# Create new user namespace (unprivileged)
unshare --user --map-root-user /bin/bash
# Inside: id -> uid=0(root) gid=0(root)
# But on host: still your original UID

# Full container-like isolation:
unshare --user --pid --mount --uts --ipc --net --fork --map-root-user \
  /bin/bash

# Inspect a container's namespaces
PID=$(docker inspect --format '{{.State.Pid}}' mycontainer)
ls -la /proc/$PID/ns/
nsenter -t $PID --net -- ip addr  # Enter only network namespace
```

**Network namespace deep dive**:
```bash
# Create and configure a network namespace
ip netns add myns
ip netns exec myns ip link list

# Create veth pair to connect namespace to host
ip link add veth0 type veth peer name veth1
ip link set veth1 netns myns

# Configure addresses
ip addr add 10.0.0.1/24 dev veth0
ip netns exec myns ip addr add 10.0.0.2/24 dev veth1
ip link set veth0 up
ip netns exec myns ip link set veth1 up
ip netns exec myns ip link set lo up

# Enable routing (NAT) for outbound access from namespace
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
ip netns exec myns ip route add default via 10.0.0.1

# This is exactly what container runtimes do for each container
```

### 4.3 cgroups v2

Control Groups limit, account for, and isolate resource usage:

```
cgroup v2 hierarchy (unified, single tree under /sys/fs/cgroup)
/sys/fs/cgroup/
├── cgroup.controllers        (available: cpu cpuset io memory pids)
├── cgroup.subtree_control    (enabled for children)
├── memory.max                (hard memory limit)
├── cpu.max                   (quota period: "100000 1000000" = 10% CPU)
├── system.slice/
│   ├── docker.service/
│   │   └── docker-<id>.scope/
│   │       ├── memory.current
│   │       ├── memory.max
│   │       ├── cpu.stat
│   │       └── pids.current
```

```bash
# Create cgroup
mkdir /sys/fs/cgroup/myapp

# Enable controllers
echo "+cpu +memory +pids" > /sys/fs/cgroup/myapp/cgroup.subtree_control

# Set limits
echo "512M" > /sys/fs/cgroup/myapp/memory.max
echo "200M" > /sys/fs/cgroup/myapp/memory.swap.max   # Limit swap
echo "100000 1000000" > /sys/fs/cgroup/myapp/cpu.max  # 10% of one core
echo "100" > /sys/fs/cgroup/myapp/pids.max            # Max 100 processes

# Add process to cgroup
echo $PID > /sys/fs/cgroup/myapp/cgroup.procs

# Monitor
cat /sys/fs/cgroup/myapp/memory.current
cat /sys/fs/cgroup/myapp/cpu.stat
cat /sys/fs/cgroup/myapp/memory.events  # oom_kill events

# systemd cgroup management
systemctl set-property myapp.service MemoryMax=512M CPUQuota=10%

# View cgroup of a process
cat /proc/$PID/cgroup

# OOM handling: configure oom_score_adj
echo 500 > /proc/$PID/oom_score_adj  # Higher = killed first (range -1000 to 1000)
```

### 4.4 Seccomp: System Call Filtering

Seccomp (Secure Computing Mode) filters system calls using BPF programs. It's the critical mechanism preventing container escapes via dangerous syscalls.

```c
// Seccomp BPF filter structure
// Berkeley Packet Filter (BPF) instructions evaluate syscall nr and args
// Action: SECCOMP_RET_ALLOW, SECCOMP_RET_KILL_PROCESS, SECCOMP_RET_ERRNO
//         SECCOMP_RET_TRAP, SECCOMP_RET_TRACE, SECCOMP_RET_LOG
```

```bash
# Check seccomp support
grep SECCOMP /boot/config-$(uname -r)
# CONFIG_SECCOMP=y
# CONFIG_SECCOMP_FILTER=y

# View seccomp mode of a process
grep Seccomp /proc/$PID/status
# Seccomp: 2  (0=disabled, 1=strict, 2=filter)

# Docker default seccomp profile blocks ~44 dangerous syscalls including:
# keyctl, add_key, request_key (credential attacks)
# ptrace (process inspection)
# reboot, kexec_load (system control)
# mount (filesystem manipulation)
# clone with CLONE_NEWUSER (namespace escapes)
# bpf (eBPF manipulation)
# perf_event_open (side-channel attacks)

# Inspect Docker default seccomp profile
docker run --security-opt seccomp=/etc/docker/seccomp/default.json alpine
# Profile at: https://github.com/moby/moby/blob/master/profiles/seccomp/default.json

# Custom seccomp profile (JSON for container runtimes)
cat > /etc/myapp-seccomp.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat",
                "lstat", "poll", "lseek", "mmap", "mprotect", "munmap",
                "brk", "rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
                "ioctl", "pread64", "pwrite64", "readv", "writev",
                "access", "pipe", "select", "sched_yield", "mremap",
                "msync", "mincore", "madvise", "shmget", "shmat",
                "shmctl", "dup", "dup2", "pause", "nanosleep",
                "getitimer", "alarm", "setitimer", "getpid", "sendfile",
                "socket", "connect", "accept", "sendto", "recvfrom",
                "sendmsg", "recvmsg", "shutdown", "bind", "listen",
                "getsockname", "getpeername", "socketpair", "setsockopt",
                "getsockopt", "clone", "fork", "vfork", "execve",
                "exit", "wait4", "kill", "uname", "fcntl", "flock",
                "fsync", "fdatasync", "truncate", "ftruncate",
                "getdents", "getcwd", "chdir", "fchdir", "rename",
                "mkdir", "rmdir", "creat", "link", "unlink", "symlink",
                "readlink", "chmod", "fchmod", "chown", "fchown",
                "lchown", "umask", "gettimeofday", "getrlimit",
                "getrusage", "sysinfo", "times", "getuid", "syslog",
                "getgid", "setuid", "setgid", "geteuid", "getegid",
                "setpgid", "getppid", "getpgrp", "setsid", "setreuid",
                "setregid", "getgroups", "setgroups", "setresuid",
                "getresuid", "setresgid", "getresgid", "getpgrp",
                "rt_sigsuspend", "sigaltstack", "utime", "mknod",
                "personality", "ustat", "statfs", "fstatfs", "getpriority",
                "setpriority", "mlock", "munlock", "mlockall", "munlockall",
                "getrlimit", "setrlimit", "getrusage", "prctl",
                "arch_prctl", "setitimer", "getitimer", "exit_group",
                "tgkill", "futex", "set_robust_list", "get_robust_list",
                "set_tid_address", "clock_gettime", "clock_getres",
                "clock_nanosleep", "epoll_create", "epoll_ctl",
                "epoll_wait", "epoll_create1", "sendfile", "accept4",
                "recvmmsg", "sendmmsg", "getrandom", "seccomp",
                "openat", "newfstatat", "readlinkat", "faccessat",
                "pselect6", "ppoll", "unshare", "set_mempolicy",
                "get_mempolicy", "move_pages", "mbind"],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["ptrace"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
EOF
```

**Golang: Load seccomp profile programmatically**:
```go
// Using github.com/seccomp/libseccomp-golang
import "github.com/seccomp/libseccomp-golang"

filter, err := seccomp.NewFilter(seccomp.ActErrno.SetReturnCode(int16(syscall.EPERM)))
if err != nil {
    log.Fatal(err)
}

// Allow specific syscalls
allowSyscalls := []string{"read", "write", "open", "close", "exit_group", "futex"}
for _, name := range allowSyscalls {
    sc, _ := seccomp.GetSyscallFromName(name)
    filter.AddRule(sc, seccomp.ActAllow)
}

if err := filter.Load(); err != nil {
    log.Fatal("failed to load seccomp filter:", err)
}
```

---

## 5. PAM: Pluggable Authentication Modules

### 5.1 PAM Architecture

PAM provides a modular authentication framework. Applications call PAM APIs; the framework invokes configured modules:

```
Application (sshd, login, sudo)
     |
     | pam_start(), pam_authenticate(), pam_acct_mgmt()
     v
+----+----+--------+
| PAM Library      |
+----+----+--------+
     |
     | Reads /etc/pam.d/<service>
     v
+----------+----------+----------+----------+
| auth     | account  | password | session  |
| modules  | modules  | modules  | modules  |
+----------+----------+----------+----------+
     |
     v (each module returns: PAM_SUCCESS, PAM_AUTH_ERR, etc.)
     
Control flags:
  required   - failure causes overall failure (but continues processing)
  requisite  - failure causes immediate return with failure
  sufficient - success causes immediate return with success (if no prior required failure)
  optional   - result ignored unless only module for type
  include    - include another PAM config file
  substack   - like include but failures/successes contained
```

### 5.2 PAM Configuration

```bash
# /etc/pam.d/sshd (SSH authentication)
# Format: type  control  module-path  module-arguments

# auth: authenticate the user
auth       required     pam_env.so
auth       required     pam_faillock.so preauth audit deny=5 unlock_time=900
auth       required     pam_unix.so nullok
auth       [default=die] pam_faillock.so authfail audit deny=5 unlock_time=900
auth       optional     pam_permit.so

# account: check account validity (expired, locked, etc.)
account    required     pam_nologin.so    # Block login if /etc/nologin exists
account    required     pam_unix.so       # Check shadow file for expiry
account    sufficient   pam_localuser.so  # Skip LDAP for local accounts
account    required     pam_ldap.so       # LDAP account check

# password: change password
password   required     pam_pwquality.so retry=3 minlen=14 dcredit=-1 ucredit=-1 ocredit=-1 lcredit=-1
password   required     pam_unix.so sha512 shadow remember=24

# session: set up user session
session    optional     pam_keyinit.so revoke
session    required     pam_limits.so      # Apply /etc/security/limits.conf
session    required     pam_unix.so
session    optional     pam_systemd.so     # Register with systemd-logind
session    required     pam_lastlog.so showfailed  # Show last login info
```

```bash
# /etc/pam.d/common-auth (Ubuntu/Debian)
auth [success=2 default=ignore] pam_unix.so nullok_secure
auth [success=1 default=ignore] pam_ldap.so use_first_pass
auth requisite                  pam_deny.so
auth required                   pam_permit.so
auth optional                   pam_cap.so   # Set capabilities on login
```

### 5.3 Key PAM Modules

```bash
# pam_faillock: Account lockout after N failed attempts
# /etc/security/faillock.conf
deny = 5          # Lock after 5 failures
unlock_time = 900 # 15 minutes lockout
even_deny_root    # Also lock root
fail_interval = 900

# View/reset faillock
faillock --user alice
faillock --user alice --reset

# pam_pwquality: Password strength
# /etc/security/pwquality.conf
minlen = 14
dcredit = -1    # At least 1 digit
ucredit = -1    # At least 1 uppercase
lcredit = -1    # At least 1 lowercase
ocredit = -1    # At least 1 other char
maxrepeat = 3   # No more than 3 same consecutive chars
gecoscheck = 1  # Check against GECOS field (full name)
dictcheck = 1   # Check against dictionary words
usercheck = 1   # Check against username

# pam_limits: Resource limits
# /etc/security/limits.conf
# <domain>  <type>  <item>   <value>
*           soft    nofile   65536
*           hard    nofile   131072
*           soft    nproc    4096
*           hard    nproc    8192
root        hard    core     unlimited
@devs       soft    maxlogins 3     # Max concurrent logins

# pam_access: Login access control
# /etc/security/access.conf
# + = allow, - = deny
# format: permission : users : origins
+       : root             : LOCAL
+       : @admins          : ALL
-       : ALL              : ALL        # Deny everyone else

# /etc/pam.d/sshd add:
account required pam_access.so

# pam_time: Time-based access
# /etc/security/time.conf
# services;ttys;users;times
# sshd;*;@devs;Al0800-1800
login;*;root;!Al0000-2400  # Block root login always

# pam_tty_audit: Record terminal I/O to audit log
session required pam_tty_audit.so disable=* enable=root,admin log_passwd

# pam_krb5: Kerberos authentication
auth sufficient pam_krb5.so minimum_uid=1000 forwardable renewable

# pam_google_authenticator: TOTP 2FA
auth required pam_google_authenticator.so nullok secret=/etc/security/.google_authenticator
```

### 5.4 SSSD: System Security Services Daemon

SSSD provides a robust interface to identity and authentication services (LDAP, AD, Kerberos):

```ini
# /etc/sssd/sssd.conf
[sssd]
services = nss, pam, sudo, ssh
domains = corp.example.com
config_file_version = 2

[domain/corp.example.com]
id_provider = ldap
auth_provider = krb5
chpass_provider = krb5
access_provider = ldap

# LDAP settings
ldap_uri = ldaps://ldap1.corp.example.com:636, ldaps://ldap2.corp.example.com:636
ldap_search_base = dc=corp,dc=example,dc=com
ldap_user_search_base = ou=Users,dc=corp,dc=example,dc=com
ldap_group_search_base = ou=Groups,dc=corp,dc=example,dc=com

# TLS/mTLS for LDAP
ldap_tls_reqcert = demand
ldap_tls_cacert = /etc/sssd/certs/ca.pem
ldap_tls_cert = /etc/sssd/certs/sssd-client.pem
ldap_tls_key = /etc/sssd/certs/sssd-client-key.pem

# Kerberos settings
krb5_realm = CORP.EXAMPLE.COM
krb5_server = kdc1.corp.example.com, kdc2.corp.example.com
krb5_renewable_lifetime = 7d
krb5_lifetime = 24h
krb5_store_password_if_offline = True

# Access control: only specific groups can log in
ldap_access_filter = (memberOf=cn=linux-access,ou=Groups,dc=corp,dc=example,dc=com)

# Sudo via LDAP
sudo_provider = ldap
ldap_sudo_search_base = ou=SUDOers,dc=corp,dc=example,dc=com

# SSH public keys from LDAP
ldap_user_ssh_public_key = sshPublicKey

# Caching settings
cache_credentials = True
krb5_store_password_if_offline = True
offline_credentials_expiration = 7
```

---

## 6. RBAC: Design, Taxonomy, and Formal Models

### 6.1 NIST RBAC Standard (INCITS 359-2004)

The NIST RBAC standard defines four levels:

```
+---------------------------+
|  Level 3: Hierarchical    |  + Role inheritance (senior roles
|  RBAC                     |    inherit junior role permissions)
+---------------------------+
|  Level 2: Constrained     |  + Separation of Duties (SoD)
|  RBAC                     |    Static SoD, Dynamic SoD
+---------------------------+
|  Level 1: Core + Hierarchy|  + Role hierarchies
|  RBAC                     |
+---------------------------+
|  Level 0: Core RBAC       |  Users, Roles, Permissions, Sessions
+---------------------------+
```

**Formal Core RBAC components**:
```
USERS   = Set of users
ROLES   = Set of roles
PERMS   = Set of permissions (operation, object) pairs
OPS     = Set of operations
OBS     = Set of objects (resources)

UA ⊆ USERS × ROLES       (User-Role assignment)
PA ⊆ PERMS × ROLES       (Permission-Role assignment)

PERMS = 2^(OPS × OBS)    (Permissions are subsets of op×object pairs)

Authorized permissions for a user u:
  authorized_permissions(u) = ⋃{permissions(r) | r ∈ assigned_roles(u)}

Session s: 
  user(s) ∈ USERS
  roles(s) ⊆ assigned_roles(user(s))   # Subset of all user's roles
```

### 6.2 Separation of Duties (SoD)

SoD prevents conflicts of interest — no single user can complete a sensitive operation alone.

```
Static SoD (SSOD):
  ∀r1, r2 ∈ SSD_role_sets: |UA(u) ∩ {r1,r2}| < t
  (No user can be member of both conflicting roles simultaneously)

  Example: "accountant" and "auditor" cannot be held by same person

Dynamic SoD (DSOD):
  Within a single session, cannot activate both conflicting roles
  A user may hold both roles but cannot use them together

  Example: "requester" and "approver" for purchase orders
```

```yaml
# Practical SoD enforcement example (OpenFGA/Zanzibar-style)
sod_constraints:
  - name: "financial-conflict"
    roles:
      - "accounts-payable"
      - "accounts-receivable"
    constraint: "static"  # User cannot hold both
    
  - name: "deploy-approve"
    roles:
      - "code-committer"
      - "production-deployer"  
    constraint: "dynamic"  # Cannot use both in same session
```

### 6.3 Role Hierarchy Design

```
                    +----------------+
                    |   super-admin  |
                    +-------+--------+
                            |
              +-------------+-------------+
              |                           |
      +-------+------+           +--------+------+
      |    sre-lead  |           |  security-lead |
      +-------+------+           +--------+------+
              |                           |
     +--------+--------+        +---------+--------+
     |                 |        |                  |
  +--+---+        +----+--+  +--+------+     +----+---+
  | sre  |        |devops |  |sec-ops  |     |auditor |
  +--+---+        +-------+  +---------+     +--------+
     |
  +--+----+
  | dev   |
  +-------+

Permission inheritance: sre-lead inherits all sre permissions
                        super-admin inherits all child permissions
```

### 6.4 ABAC: Attribute-Based Access Control

ABAC extends RBAC with environmental and attribute-based conditions:

```
Decision = f(Subject_attrs, Resource_attrs, Action, Environment_attrs)

Subject attributes:   {role=engineer, dept=infra, clearance=confidential, mfa=true}
Resource attributes:  {classification=secret, owner=security-team, env=production}
Action:               read, write, delete, exec
Environment attrs:    {time=09:00, ip=10.0.0.0/8, geo=US}

Policy example (XACML-style logic):
  ALLOW IF:
    subject.role IN ["security-engineer", "sre"] AND
    subject.clearance >= resource.classification AND
    subject.mfa == true AND
    environment.ip IN trusted_networks AND
    environment.time BETWEEN "08:00" AND "18:00"
```

### 6.5 ReBAC: Relationship-Based Access Control

Google's Zanzibar paper introduced ReBAC — access based on relationship graphs:

```
Tuple store: (resource, relation, user_or_userset)

object:relation@user
doc:123#viewer@alice
doc:123#editor@bob
org:acme#member@charlie
group:eng#member@{org:acme#member}  # All acme members are eng group members

Check: "Can alice view doc:123?"
  1. Lookup (doc:123, viewer, alice) -> FOUND -> ALLOW
  
Check: "Can charlie view doc:456?"
  1. Lookup (doc:456, viewer, charlie) -> NOT FOUND
  2. Lookup (doc:456, viewer, org:acme#member) -> FOUND
  3. Lookup (org:acme, member, charlie) -> FOUND -> ALLOW (via group)
```

**OpenFGA** (CNCF project, open-source Zanzibar implementation):
```yaml
# schema.fga
model
  schema 1.1

type user

type document
  relations
    define owner: [user]
    define editor: [user] or owner
    define viewer: [user] or editor
    define commenter: [user] or viewer

type folder
  relations
    define owner: [user]
    define viewer: [user, user:*] or owner
    define parent: [folder]
    define viewer_from_parent: viewer from parent
```

---

## 7. Cloud IAM: AWS, GCP, Azure Deep Dive

### 7.1 AWS IAM Architecture

```
+------------------------+       +------------------------+
|  IAM Principal         |       |  Resource              |
|  User/Role/Group/      |       |  S3/EC2/RDS/etc.       |
|  Service Account       |       |                        |
+----------+-------------+       +-----------+------------+
           |                                 |
           |  Request (action, resource, conditions)
           v                                 v
+--------------------------------------------------------------------+
|                      IAM Policy Evaluation                         |
|                                                                    |
|  1. Explicit DENY?   ---------> DENY (immediately)                |
|  2. SCP (Org policy) denies? -> DENY                              |
|  3. Resource-based policy?   -> check                             |
|  4. Identity-based policy?   -> check                             |
|  5. Permission boundary?     -> check (intersection)             |
|  6. Session policy?          -> check (intersection)             |
|  7. All say ALLOW?          -> ALLOW                              |
|  8. Implicit DENY (default)  -> DENY                              |
+--------------------------------------------------------------------+
```

**IAM Policy Types and Precedence**:

| Policy Type | Scope | Effect | Can Deny |
|------------|-------|--------|----------|
| SCP (Service Control Policy) | AWS Org | Sets max permissions | Yes |
| Resource-based Policy | Resource | Grants cross-account | Yes |
| Identity-based Policy | Principal | Grants to principal | Yes |
| Permission Boundary | Principal | Limits max permissions | Yes (by omission) |
| Session Policy | STS session | Further restricts | Yes (by omission) |
| ACL | Resource (S3, etc.) | Cross-account | Yes (by omission) |

**IAM Policy JSON anatomy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3ReadSpecificBucket",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/app-server-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-app-bucket",
        "arn:aws:s3:::my-app-bucket/*"
      ],
      "Condition": {
        "StringEquals": {
          "s3:prefix": ["app-data/", "config/"],
          "aws:RequestedRegion": "us-east-1"
        },
        "Bool": {
          "aws:SecureTransport": "true",
          "aws:MultiFactorAuthPresent": "true"
        },
        "DateGreaterThan": {
          "aws:CurrentTime": "2024-01-01T00:00:00Z"
        },
        "IpAddress": {
          "aws:SourceIp": ["10.0.0.0/8", "172.16.0.0/12"]
        },
        "StringLike": {
          "aws:PrincipalTag/environment": "production"
        }
      }
    },
    {
      "Sid": "DenyNonTLSAccess",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::my-app-bucket",
        "arn:aws:s3:::my-app-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

**AWS STS: Assume Role Pattern**:
```json
// Trust policy on the target role (who can assume it)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:ref:refs/heads/main"
        }
      }
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

```bash
# Assume role with CLI
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/deploy-role \
  --role-session-name deployment-$(date +%s) \
  --duration-seconds 3600 \
  --external-id "unique-per-customer-id" \
  --policy-arns "arn:aws:iam::aws:policy/ReadOnlyAccess"  # Further restrict session

# IAM Conditions operators reference:
# StringEquals, StringNotEquals, StringLike, StringNotLike
# ArnEquals, ArnLike
# IpAddress, NotIpAddress
# Bool
# DateEquals, DateLessThan, DateGreaterThan
# NumericEquals, NumericLessThan
# Null (check if key exists)
# aws:PrincipalTag/<key>     (tag on principal)
# aws:ResourceTag/<key>      (tag on resource) - ABAC!
# aws:RequestTag/<key>       (tag in request)

# ABAC pattern: use tags to authorize
# Policy: allow action if requester's team tag matches resource's team tag
{
  "Condition": {
    "StringEquals": {
      "aws:ResourceTag/team": "${aws:PrincipalTag/team}"
    }
  }
}

# Service Control Policy (prevent leaving org region)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonEURegions",
      "Effect": "Deny",
      "NotAction": [
        "iam:*", "organizations:*", "support:*", "sts:*",
        "cloudfront:*", "route53:*", "waf:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["eu-west-1", "eu-central-1"]
        }
      }
    }
  ]
}
```

**AWS Permission Boundaries**:
```json
// Permission boundary: even if identity policy allows more,
// effective permission = identity_policy ∩ boundary
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowedServices",
      "Effect": "Allow",
      "Action": [
        "s3:*", "dynamodb:*", "lambda:*", "logs:*", "xray:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyIAMEscalation",
      "Effect": "Deny",
      "Action": [
        "iam:CreateUser", "iam:AttachUserPolicy",
        "iam:CreateAccessKey", "iam:DeletePolicy",
        "iam:PutUserPolicy", "iam:PutRolePolicy"
      ],
      "Resource": "*"
    }
  ]
}
```

```bash
# Attach boundary to role (prevents privilege escalation)
aws iam put-role-permissions-boundary \
  --role-name developer-role \
  --permissions-boundary arn:aws:iam::123456789012:policy/DeveloperBoundary

# IAM Access Analyzer: find unintended external access
aws accessanalyzer create-analyzer \
  --analyzer-name org-analyzer \
  --type ORGANIZATION

aws accessanalyzer list-findings --analyzer-name org-analyzer

# IAM credential report
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d | \
  csvlens  # Find stale credentials, unused access keys
```

### 7.2 GCP IAM Architecture

GCP IAM uses a **resource hierarchy** (Organization > Folder > Project > Resource) with policy inheritance.

```
Organization (org IAM)
  └── Folders (dept IAM)
        └── Projects (project IAM)
              └── Resources (resource-level IAM)

Effective policy at resource = all policies from root to resource (union)
Exception: Organization policy constraints can DENY and override
```

**GCP IAM components**:
```
Member (Principal) Types:
  user:alice@example.com           # Google Account
  serviceAccount:sa@project.iam    # Service Account
  group:devs@example.com           # Google Group
  domain:example.com               # Entire G Suite domain
  allAuthenticatedUsers            # Any authenticated Google account (DANGEROUS)
  allUsers                         # Public (DANGEROUS for most resources)
  principalSet://iam.googleapis.com/...  # Workload Identity Federation

Roles:
  Primitive:  roles/owner, roles/editor, roles/viewer (avoid, too broad)
  Predefined: roles/storage.objectAdmin, roles/compute.instanceAdmin.v1
  Custom:     projects/PROJECT_ID/roles/myCustomRole
```

```bash
# View IAM policy on a project
gcloud projects get-iam-policy PROJECT_ID --format=json

# Grant role (always use specific predefined or custom roles)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:svc@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer" \
  --condition="expression=resource.name.startsWith('projects/_/buckets/prod-'),title=prod-bucket-only"

# Conditional IAM bindings (ABAC in GCP)
gcloud projects set-iam-policy PROJECT_ID policy.json
# policy.json with condition:
{
  "bindings": [{
    "role": "roles/storage.objectAdmin",
    "members": ["serviceAccount:deploy@project.iam.gserviceaccount.com"],
    "condition": {
      "title": "only-in-business-hours",
      "description": "Restrict to business hours",
      "expression": "request.time.getHours('America/New_York') >= 9 && request.time.getHours('America/New_York') <= 17"
    }
  }]
}

# Service Account key management (avoid keys, use Workload Identity)
# Workload Identity Federation (keyless auth):
gcloud iam workload-identity-pools create "github-pool" \
  --project="PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Grant SA impersonation to GitHub workload identity
gcloud iam service-accounts add-iam-policy-binding "deploy-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --project="PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/myorg/myrepo"

# Organization Policy Constraints (enforcement, not just IAM)
gcloud org-policies set-policy policy.yaml

# policy.yaml - restrict public IPs on VMs:
name: projects/PROJECT_ID/policies/compute.vmExternalIpAccess
spec:
  rules:
  - denyAll: true
```

**GCP Custom Roles**:
```bash
# Define minimal custom role
cat > custom-role.yaml << 'EOF'
title: "CI/CD Deployer"
description: "Can deploy to Cloud Run and update configs"
stage: GA
includedPermissions:
  - run.services.create
  - run.services.update
  - run.services.get
  - run.services.list
  - run.configurations.get
  - run.routes.get
  - clouddeploy.deliveryPipelines.get
  - clouddeploy.releases.create
  - storage.objects.get
  - storage.objects.list
EOF

gcloud iam roles create cicd_deployer \
  --project=PROJECT_ID \
  --file=custom-role.yaml

# GCP Recommender: find excess permissions
gcloud recommender recommendations list \
  --project=PROJECT_ID \
  --location=global \
  --recommender=google.iam.policy.Recommender \
  --format=json
```

### 7.3 Azure RBAC Architecture

Azure uses a **management hierarchy** (Management Groups > Subscriptions > Resource Groups > Resources) with an Entra ID (formerly Azure AD) identity backend.

```
Azure RBAC Components:
  Security Principal: User, Group, Service Principal, Managed Identity
  Role Definition:    Collection of permissions (actions, notActions, dataActions)
  Scope:              Management Group / Subscription / Resource Group / Resource
  Role Assignment:    Principal + Role + Scope

Inheritance: permissions assigned at higher scope apply to all child scopes
```

```bash
# List role assignments
az role assignment list --assignee user@corp.com --all

# Assign built-in role
az role assignment create \
  --assignee-object-id $SP_OBJECT_ID \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/$SUB/resourceGroups/prod-rg/providers/Microsoft.Storage/storageAccounts/prodstore"

# Custom role definition
cat > custom-role.json << 'EOF'
{
  "Name": "Deploy Engineer",
  "IsCustom": true,
  "Description": "Can deploy to AKS and update container registry",
  "Actions": [
    "Microsoft.ContainerService/managedClusters/read",
    "Microsoft.ContainerService/managedClusters/listClusterUserCredential/action",
    "Microsoft.ContainerRegistry/registries/read",
    "Microsoft.ContainerRegistry/registries/pull/read",
    "Microsoft.ContainerRegistry/registries/push/write"
  ],
  "NotActions": [
    "Microsoft.ContainerService/managedClusters/delete",
    "Microsoft.ContainerService/managedClusters/write"
  ],
  "DataActions": [
    "Microsoft.ContainerRegistry/registries/*/read"
  ],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/SUBSCRIPTION_ID/resourceGroups/prod-rg"
  ]
}
EOF
az role definition create --role-definition @custom-role.json

# Managed Identity (no credential management)
# System-assigned: tied to resource lifecycle
az vm create --assign-identity ...

# User-assigned: shared across resources  
az identity create --name myapp-identity --resource-group prod-rg
az vm identity assign --identities myapp-identity --name myvm --resource-group prod-rg

# Azure Policy: enforce compliance (not just IAM)
az policy definition create \
  --name 'require-tag-environment' \
  --display-name 'Require environment tag' \
  --description 'Requires environment tag on all resource groups' \
  --rules '{
    "if": {
      "allOf": [
        {"field": "type", "equals": "Microsoft.Resources/subscriptions/resourceGroups"},
        {"field": "tags[environment]", "exists": "false"}
      ]
    },
    "then": {"effect": "deny"}
  }' \
  --mode All

# Privileged Identity Management (PIM): JIT access
# Activate eligible role (maximum 8 hours, with justification)
az ad pim activation-create \
  --role-definition-id $ROLE_DEF_ID \
  --scope $SCOPE \
  --duration PT4H \
  --justification "Incident response ticket #12345"

# Entra ID Conditional Access (MFA enforcement)
# Requires Premium P1/P2 license - configured via portal or MS Graph API
```

---

## 8. Workload Identity: SPIFFE/SPIRE

### 8.1 SPIFFE Standard

SPIFFE (Secure Production Identity Framework For Everyone) provides a standard for workload identity in distributed systems. It solves the "bottom turtle" problem — how do workloads prove their identity without using long-lived secrets?

```
SPIFFE ID:   spiffe://<trust-domain>/<path>
Examples:
  spiffe://prod.corp.com/ns/default/sa/payment-svc
  spiffe://cluster.local/ns/istio-system/sa/istiod
  spiffe://corp.com/env/prod/svc/api-gateway

SVID (SPIFFE Verifiable Identity Document):
  X.509-SVID: X.509 certificate with SPIFFE ID in SAN URI field
  JWT-SVID:   JWT with SPIFFE ID as 'sub' claim

Trust Bundle: Set of CA certificates for a trust domain
Federation:   Cross-trust-domain authentication via bundle exchange
```

### 8.2 SPIRE Architecture

```
+-------------------+      +-------------------+
|  SPIRE Server     |      |  SPIRE Server     |
|  (Trust Domain A) |<---->|  (Trust Domain B) |  Federation
|                   |      |                   |
|  +---------+      |      +-------------------+
|  | CA/PKI  |      |
|  +---------+      |
|  | Datastore|     |
|  | (SQLite/ |     |
|  |  Postgres)|    |
|  +---------+      |
+--------+----------+
         |  gRPC (mTLS)
         |  Node Attestation
         |  Workload Attestation
         v
+--------+----------+
|  SPIRE Agent      |  (runs on every node)
|                   |
|  +--------------+ |
|  | Node Attestor| |  Proves node identity to Server
|  | (TPM/AWS/k8s)| |
|  +--------------+ |
|  | Workload     | |  Detects workloads on this node
|  | Attestor     | |  (k8s, docker, unix PID/UID)
|  +--------------+ |
|  | SVID Cache   | |  Caches and rotates SVIDs
|  +--------------+ |
+--------+----------+
         |  Unix Domain Socket (local)
         |  SPIFFE Workload API
         v
+--------+----------+
|  Workload         |
|  (application)    |  Fetches SVID, uses for mTLS/JWT
+-------------------+
```

```bash
# Install SPIRE (from release)
wget https://github.com/spiffe/spire/releases/latest/download/spire-1.9.0-linux-amd64-musl.tar.gz
tar xzf spire-*.tar.gz -C /opt/spire --strip-components=1

# SPIRE Server config
cat > /opt/spire/conf/server/server.conf << 'EOF'
server {
    bind_address = "0.0.0.0"
    bind_port = "8081"
    socket_path = "/tmp/spire-server/private/api.sock"
    trust_domain = "prod.corp.com"
    data_dir = "/opt/spire/data/server"
    log_level = "INFO"
    
    # Short SVID TTL for fast rotation
    default_x509_svid_ttl = "1h"
    default_jwt_svid_ttl = "5m"
    
    ca_ttl = "24h"
    ca_subject {
        country = ["US"]
        organization = ["Corp"]
        common_name = "SPIRE CA"
    }
}

plugins {
    DataStore "sql" {
        plugin_data {
            database_type = "postgres"
            connection_string = "host=db user=spire password=secret dbname=spire sslmode=require"
        }
    }
    
    KeyManager "disk" {
        plugin_data {
            keys_path = "/opt/spire/data/server/keys.json"
        }
    }
    
    NodeAttestor "k8s_psat" {   # Projected Service Account Tokens
        plugin_data {
            clusters = {
                "prod-cluster" = {
                    service_account_allow_list = ["spire:spire-agent"]
                    kube_config_file = ""
                    allowed_node_label_keys = []
                    allowed_pod_label_keys = ["app", "version"]
                }
            }
        }
    }
    
    BundlePublisher "k8s_configmap" {
        plugin_data {
            cluster = "prod-cluster"
            namespace = "spire"
            configmap = "spire-bundle"
        }
    }
}

health_checks {
    listener_enabled = true
    bind_address = "0.0.0.0"
    bind_port = "8080"
    live_path = "/live"
    ready_path = "/ready"
}
EOF

# SPIRE Agent config
cat > /opt/spire/conf/agent/agent.conf << 'EOF'
agent {
    data_dir = "/opt/spire/data/agent"
    log_level = "INFO"
    server_address = "spire-server.spire.svc.cluster.local"
    server_port = "8081"
    socket_path = "/run/spire/sockets/agent.sock"
    trust_bundle_path = "/opt/spire/conf/agent/bootstrap.crt"
    trust_domain = "prod.corp.com"
}

plugins {
    NodeAttestor "k8s_psat" {
        plugin_data {
            cluster = "prod-cluster"
            token_path = "/var/run/secrets/tokens/spire-agent"
        }
    }
    
    KeyManager "memory" {
        plugin_data {}
    }
    
    WorkloadAttestor "k8s" {
        plugin_data {
            skip_kubelet_verification = false
            node_name_env = "MY_NODE_NAME"
            certificate_path = "/var/lib/kubelet/pki/kubelet-client-current.pem"
            private_key_path = "/var/lib/kubelet/pki/kubelet-client-current.pem"
        }
    }
    
    WorkloadAttestor "unix" {
        plugin_data {
            discover_workload_path = true
        }
    }
}
EOF

# Register workload entry
spire-server entry create \
  -spiffeID spiffe://prod.corp.com/ns/default/sa/payment-svc \
  -parentID spiffe://prod.corp.com/k8s-node/node01 \
  -selector k8s:ns:default \
  -selector k8s:sa:payment-svc \
  -selector k8s:container-name:payment-svc \
  -ttl 3600 \
  -dns payment-svc.default.svc.cluster.local

# Verify entries
spire-server entry show -spiffeID spiffe://prod.corp.com/ns/default/sa/payment-svc

# Health check
spire-server healthcheck
```

**SPIRE Workload API consumption (Go)**:
```go
package main

import (
    "context"
    "crypto/tls"
    "log"
    
    "github.com/spiffe/go-spiffe/v2/spiffeid"
    "github.com/spiffe/go-spiffe/v2/spiffetls"
    "github.com/spiffe/go-spiffe/v2/spiffetls/tlsconfig"
    "github.com/spiffe/go-spiffe/v2/workloadapi"
)

const socketPath = "unix:///run/spire/sockets/agent.sock"

func main() {
    ctx := context.Background()
    
    // Create X.509 source — auto-rotates SVIDs
    x509Source, err := workloadapi.NewX509Source(ctx,
        workloadapi.WithClientOptions(
            workloadapi.WithAddr(socketPath),
        ),
    )
    if err != nil {
        log.Fatalf("failed to create X.509 source: %v", err)
    }
    defer x509Source.Close()
    
    // Get current SVID
    svid, err := x509Source.GetX509SVID()
    if err != nil {
        log.Fatalf("failed to get SVID: %v", err)
    }
    log.Printf("My SPIFFE ID: %s", svid.ID)
    log.Printf("Cert expires: %s", svid.Certificates[0].NotAfter)
    
    // Authorize only specific peer SPIFFE IDs
    authorizedPeer := spiffeid.RequireIDFromString("spiffe://prod.corp.com/ns/default/sa/api-gateway")
    
    // Create mTLS config that validates peer SPIFFE ID
    tlsConfig := tlsconfig.MTLSServerConfig(x509Source, x509Source,
        tlsconfig.AuthorizeID(authorizedPeer),
    )
    
    // Or use spiffetls for dial/listen with automatic SVID validation
    conn, err := spiffetls.Dial(ctx, "tcp", "payment-svc:8080",
        tlsconfig.AuthorizeID(authorizedPeer),
        workloadapi.WithClientOptions(workloadapi.WithAddr(socketPath)),
    )
    if err != nil {
        log.Fatalf("failed to dial: %v", err)
    }
    defer conn.Close()
    
    _ = tlsConfig
    _ = conn
}
```

---

## 9. Policy-as-Code: OPA/Rego and Cedar

### 9.1 Open Policy Agent (OPA)

OPA is a general-purpose policy engine. Policies are written in Rego — a declarative, logic-based language.

```
Architecture:
  Policy (Rego) + Data (JSON) + Input (JSON) -> Decision (JSON)

  +-----------+    +-----------+    +-----------+
  | Rego      |    | Data      |    | Input     |
  | Policy    |    | (external |    | (per-     |
  | (static)  |    |  context) |    |  request) |
  +-----------+    +-----------+    +-----------+
         \              |              /
          \             v             /
           +------> OPA Engine <-----+
                        |
                        v
                    Decision
                    {allow: true/false, ...}
```

```rego
# policies/rbac.rego
package rbac

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Allow if user has required permission via any of their roles
allow if {
    # Get all roles assigned to the user
    some role in data.user_roles[input.user]
    
    # Check if any role has the required permission
    some permission in data.role_permissions[role]
    
    # Match permission to request
    permission.action == input.action
    resource_matches(permission.resource, input.resource)
    
    # Check conditions
    condition_satisfied(permission.conditions)
}

# Resource matching with wildcards
resource_matches(pattern, resource) if {
    pattern == "*"
}

resource_matches(pattern, resource) if {
    pattern == resource
}

resource_matches(pattern, resource) if {
    # Prefix matching: "s3://bucket/*" matches "s3://bucket/key"
    endswith(pattern, "/*")
    prefix := trim_suffix(pattern, "/*")
    startswith(resource, prefix)
}

# Condition evaluation
condition_satisfied(conditions) if {
    count(conditions) == 0
}

condition_satisfied(conditions) if {
    every condition in conditions {
        evaluate_condition(condition)
    }
}

evaluate_condition(cond) if {
    cond.type == "ip_range"
    net.cidr_contains(cond.value, input.source_ip)
}

evaluate_condition(cond) if {
    cond.type == "time_window"
    hour := time.clock(time.now_ns())[0]
    hour >= cond.start_hour
    hour < cond.end_hour
}

evaluate_condition(cond) if {
    cond.type == "mfa_required"
    cond.value == true
    input.mfa_verified == true
}

# SoD check: deny if user has conflicting roles simultaneously
deny contains reason if {
    some r1, r2
    r1 in data.user_roles[input.user]
    r2 in data.user_roles[input.user]
    r1 != r2
    conflict := data.sod_conflicts[_]
    r1 in conflict.roles
    r2 in conflict.roles
    reason := sprintf("SoD violation: roles %v and %v cannot be held simultaneously", [r1, r2])
}
```

```rego
# policies/k8s_admission.rego
package kubernetes.admission

import future.keywords.if

# Deny containers running as root
deny contains msg if {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    container.securityContext.runAsUser == 0
    msg := sprintf("Container %v must not run as root (UID 0)", [container.name])
}

# Deny privileged containers
deny contains msg if {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("Container %v must not be privileged", [container.name])
}

# Require specific labels
deny contains msg if {
    input.request.kind.kind == "Deployment"
    not input.request.object.metadata.labels["app.kubernetes.io/name"]
    msg := "Deployment must have app.kubernetes.io/name label"
}

# Deny latest tag (require pinned digest or version)
deny contains msg if {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    endswith(container.image, ":latest")
    msg := sprintf("Container %v must not use :latest tag", [container.name])
}

# Require resource limits
deny contains msg if {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    not container.resources.limits.memory
    msg := sprintf("Container %v must specify memory limits", [container.name])
}
```

```bash
# Run OPA with bundle reload
opa run --server \
  --addr :8181 \
  --bundle /policies/ \
  --log-format=json \
  --v1-compatible \
  --set=decision_logs.console=true

# Evaluate policy
curl -s -X POST http://localhost:8181/v1/data/rbac/allow \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "user": "alice",
      "action": "s3:GetObject",
      "resource": "s3://prod-bucket/config/app.yaml",
      "source_ip": "10.0.0.5",
      "mfa_verified": true
    }
  }'

# OPA test
cat > policies/rbac_test.rego << 'EOF'
package rbac_test

import data.rbac.allow

test_admin_can_do_anything if {
    allow with input as {
        "user": "admin",
        "action": "s3:DeleteObject",
        "resource": "s3://any-bucket/any-key",
        "mfa_verified": true
    } with data.user_roles as {"admin": ["super-admin"]}
    with data.role_permissions as {
        "super-admin": [{"action": "*", "resource": "*", "conditions": []}]
    }
}

test_regular_user_denied_delete if {
    not allow with input as {
        "user": "alice",
        "action": "s3:DeleteObject",
        "resource": "s3://prod-bucket/key",
        "mfa_verified": true
    } with data.user_roles as {"alice": ["viewer"]}
    with data.role_permissions as {
        "viewer": [{"action": "s3:GetObject", "resource": "s3://prod-bucket/*", "conditions": []}]
    }
}
EOF

opa test policies/ -v --bundle --format=pretty

# OPA bundle build
opa build -b policies/ --output bundle.tar.gz
```

### 9.2 Cedar Policy Language (AWS)

Cedar is a fast, formally verified policy language from AWS, used in Amazon Verified Permissions:

```
# Cedar policies: entities + policies + schema

# Entity types
entity User {
    department: String,
    jobLevel: Long,
    mfaVerified: Boolean,
};

entity Resource {
    owner: User,
    classification: String,
    environment: String,
};

entity Action;

# Allow policy
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal.mfaVerified == true &&
    resource.classification != "top-secret" &&
    resource.environment == "production"
};

# Deny policy (wins over permit)
forbid (
    principal is User,
    action,
    resource is Resource
)
unless {
    resource.owner == principal ||
    principal.jobLevel >= 7
};
```

---

## 10. Kubernetes RBAC and Admission Control

### 10.1 Kubernetes RBAC Model

```
K8s RBAC Objects:
  Role           - namespace-scoped permissions
  ClusterRole    - cluster-scoped permissions (or cluster-wide namespace perms)
  RoleBinding    - binds Role/ClusterRole to subjects in a namespace
  ClusterRoleBinding - binds ClusterRole to subjects cluster-wide

Subjects:
  User          (string, verified by auth mechanism — certs, OIDC)
  Group         (string)
  ServiceAccount (namespace/name, has projected token)
```

```yaml
# ClusterRole: can read pods and logs across all namespaces
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "pods/status"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "list"]
---
# Role: write access in specific namespace only
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployment-manager
  namespace: production
rules:
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: ["apps"]
  resources: ["deployments/scale"]
  verbs: ["update"]
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
# Deny delete explicitly (not needed, default deny, but explicit for docs)
---
# RoleBinding: bind Role to ServiceAccount
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ci-deployment-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: ci-deployer
  namespace: ci-system
roleRef:
  kind: Role
  name: deployment-manager
  apiGroup: rbac.authorization.k8s.io
---
# ServiceAccount with OIDC token binding (Workload Identity)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: payment-svc
  namespace: default
  annotations:
    # AWS EKS: IAM role association
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/payment-svc-role
    # GKE: Workload Identity binding
    iam.gke.io/gcp-service-account: payment@project.iam.gserviceaccount.com
---
# Projected ServiceAccount Token (PSAT) — short-lived, audience-bound
apiVersion: v1
kind: Pod
metadata:
  name: payment-svc
spec:
  serviceAccountName: payment-svc
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600    # 1 hour max (default 1 year — too long)
          audience: "spire-server"   # Bound to specific audience
  containers:
  - name: app
    image: payment-svc:v1.2.3@sha256:abc123
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
      readOnly: true
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      runAsGroup: 1000
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: RuntimeDefault
```

### 10.2 Admission Controllers

```
Request Flow:
  kubectl apply -> API Server -> Authentication -> Authorization (RBAC)
                                -> Admission Controllers -> etcd

Admission Controller types:
  Mutating:   Can modify the request object (inject sidecars, set defaults)
  Validating: Can accept or reject the request (enforce policies)

Order: Mutating webhooks -> Object schema validation -> Validating webhooks
```

**Key built-in admission controllers**:
- `PodSecurity` (replaces deprecated PodSecurityPolicy)
- `NodeRestriction` (kubelets can only modify their own node/pods)
- `LimitRanger` (enforce resource limits defaults)
- `ResourceQuota` (enforce namespace quotas)
- `MutatingAdmissionWebhook` / `ValidatingAdmissionWebhook`

```yaml
# PodSecurity admission (built-in, label-based)
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted    # Block non-compliant pods
    pod-security.kubernetes.io/audit: restricted      # Log violations
    pod-security.kubernetes.io/warn: restricted       # Warn on apply

# Pod Security Standards levels:
# privileged: no restrictions
# baseline:   minimal restrictions (no privileged, hostNetwork, etc.)
# restricted: full pod hardening (non-root, drop all caps, seccomp, etc.)
```

**Custom Validating Webhook (Go)**:
```go
package main

import (
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    
    admissionv1 "k8s.io/api/admission/v1"
    corev1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

type AdmissionHandler struct{}

func (h *AdmissionHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    var review admissionv1.AdmissionReview
    if err := json.NewDecoder(r.Body).Decode(&review); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    response := h.validate(review.Request)
    review.Response = response
    review.Response.UID = review.Request.UID
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(review)
}

func (h *AdmissionHandler) validate(req *admissionv1.AdmissionRequest) *admissionv1.AdmissionResponse {
    if req.Kind.Kind != "Pod" {
        return &admissionv1.AdmissionResponse{Allowed: true}
    }
    
    var pod corev1.Pod
    if err := json.Unmarshal(req.Object.Raw, &pod); err != nil {
        return deny(fmt.Sprintf("failed to decode pod: %v", err))
    }
    
    var violations []string
    
    for _, container := range pod.Spec.Containers {
        // Reject latest tag
        if hasLatestTag(container.Image) {
            violations = append(violations,
                fmt.Sprintf("container %q uses :latest tag", container.Name))
        }
        
        // Require non-root
        if container.SecurityContext == nil ||
            container.SecurityContext.RunAsNonRoot == nil ||
            !*container.SecurityContext.RunAsNonRoot {
            violations = append(violations,
                fmt.Sprintf("container %q must set runAsNonRoot=true", container.Name))
        }
        
        // Require read-only root filesystem
        if container.SecurityContext == nil ||
            container.SecurityContext.ReadOnlyRootFilesystem == nil ||
            !*container.SecurityContext.ReadOnlyRootFilesystem {
            violations = append(violations,
                fmt.Sprintf("container %q must have readOnlyRootFilesystem=true", container.Name))
        }
        
        // Require dropped capabilities
        if container.SecurityContext == nil ||
            container.SecurityContext.Capabilities == nil ||
            !hasDropAll(container.SecurityContext.Capabilities.Drop) {
            violations = append(violations,
                fmt.Sprintf("container %q must drop all capabilities", container.Name))
        }
    }
    
    if len(violations) > 0 {
        return &admissionv1.AdmissionResponse{
            Allowed: false,
            Result: &metav1.Status{
                Code:    403,
                Message: fmt.Sprintf("Policy violations: %v", violations),
            },
        }
    }
    
    return &admissionv1.AdmissionResponse{Allowed: true}
}

func deny(msg string) *admissionv1.AdmissionResponse {
    return &admissionv1.AdmissionResponse{
        Allowed: false,
        Result:  &metav1.Status{Code: 403, Message: msg},
    }
}

func hasLatestTag(image string) bool {
    // Check for :latest suffix or no tag (defaults to latest)
    if image == "" {
        return false
    }
    // Simple check - in production use crane/go-containerregistry
    return len(image) > 0 && (image[len(image)-7:] == ":latest" || 
        !containsTag(image))
}

func hasDropAll(caps []corev1.Capability) bool {
    for _, c := range caps {
        if c == "ALL" {
            return true
        }
    }
    return false
}

func containsTag(image string) bool {
    // Simplified - real implementation should parse image ref properly
    for i := len(image) - 1; i >= 0; i-- {
        if image[i] == ':' || image[i] == '@' {
            return true
        }
        if image[i] == '/' {
            return false
        }
    }
    return false
}

func main() {
    handler := &AdmissionHandler{}
    
    mux := http.NewServeMux()
    mux.Handle("/validate", handler)
    mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    })
    
    server := &http.Server{
        Addr:    ":8443",
        Handler: mux,
    }
    
    log.Printf("Starting admission webhook on :8443")
    log.Fatal(server.ListenAndServeTLS("/certs/tls.crt", "/certs/tls.key"))
}
```

```yaml
# Register the webhook
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-security-policy
webhooks:
- name: pod-validator.security.corp.com
  admissionReviewVersions: ["v1"]
  clientConfig:
    service:
      name: admission-webhook
      namespace: security-system
      path: "/validate"
    caBundle: <base64-encoded-CA-cert>
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
    scope: "Namespaced"
  namespaceSelector:
    matchExpressions:
    - key: security-validation
      operator: In
      values: ["enabled"]
  failurePolicy: Fail   # Fail closed — deny if webhook unavailable
  sideEffects: None
  timeoutSeconds: 10
```

---

## 11. Go Implementation: IAM Enforcement Engine

### 11.1 Full IAM Middleware Stack

```go
// pkg/iam/engine.go
package iam

import (
    "context"
    "crypto/subtle"
    "crypto/tls"
    "encoding/json"
    "errors"
    "fmt"
    "net/http"
    "strings"
    "sync"
    "time"
    
    "github.com/golang-jwt/jwt/v5"
    "github.com/open-policy-agent/opa/rego"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
    "go.uber.org/zap"
)

// Principal represents an authenticated identity
type Principal struct {
    ID          string            `json:"id"`
    Type        PrincipalType     `json:"type"`
    Roles       []string          `json:"roles"`
    Groups      []string          `json:"groups"`
    Attributes  map[string]string `json:"attributes"`
    AuthMethod  string            `json:"auth_method"`
    MFAVerified bool              `json:"mfa_verified"`
    IssuedAt    time.Time         `json:"issued_at"`
    ExpiresAt   time.Time         `json:"expires_at"`
    SPIFFEID    string            `json:"spiffe_id,omitempty"`
}

type PrincipalType string

const (
    PrincipalUser           PrincipalType = "user"
    PrincipalServiceAccount PrincipalType = "service_account"
    PrincipalWorkload       PrincipalType = "workload"
)

// AuthorizationRequest encapsulates what is being requested
type AuthorizationRequest struct {
    Principal  *Principal        `json:"principal"`
    Action     string            `json:"action"`
    Resource   string            `json:"resource"`
    Namespace  string            `json:"namespace,omitempty"`
    Conditions map[string]any    `json:"conditions,omitempty"`
    SourceIP   string            `json:"source_ip,omitempty"`
    RequestID  string            `json:"request_id"`
}

// AuthorizationDecision is the result
type AuthorizationDecision struct {
    Allowed    bool     `json:"allowed"`
    Reasons    []string `json:"reasons,omitempty"`
    Denials    []string `json:"denials,omitempty"`
    PolicyPath string   `json:"policy_path,omitempty"`
    EvalTimeMs int64    `json:"eval_time_ms"`
}

// IAMEngine is the central enforcement point
type IAMEngine struct {
    mu          sync.RWMutex
    opaQuery    *rego.PreparedEvalQuery
    policyStore PolicyStore
    auditLogger AuditLogger
    tracer      trace.Tracer
    logger      *zap.Logger
    
    // Cache for policy decisions (short TTL for security)
    cache       *DecisionCache
}

type PolicyStore interface {
    GetRoles(ctx context.Context, principalID string) ([]string, error)
    GetRolePermissions(ctx context.Context, role string) ([]Permission, error)
    GetSODConstraints(ctx context.Context) ([]SODConstraint, error)
}

type AuditLogger interface {
    LogDecision(ctx context.Context, req *AuthorizationRequest, dec *AuthorizationDecision) error
}

type Permission struct {
    Action     string            `json:"action"`
    Resource   string            `json:"resource"`
    Conditions []Condition       `json:"conditions"`
    Effect     string            `json:"effect"` // "allow" or "deny"
}

type Condition struct {
    Type  string `json:"type"`
    Key   string `json:"key"`
    Value any    `json:"value"`
}

type SODConstraint struct {
    Name  string   `json:"name"`
    Roles []string `json:"roles"`
    Type  string   `json:"type"` // "static" or "dynamic"
}

// NewIAMEngine creates an IAM engine with loaded OPA policy
func NewIAMEngine(
    ctx context.Context,
    policyPath string,
    store PolicyStore,
    auditor AuditLogger,
    logger *zap.Logger,
) (*IAMEngine, error) {
    // Load OPA policy
    r := rego.New(
        rego.Query("data.iam.decision"),
        rego.Load([]string{policyPath}, nil),
    )
    
    query, err := r.PrepareForEval(ctx)
    if err != nil {
        return nil, fmt.Errorf("failed to prepare OPA query: %w", err)
    }
    
    return &IAMEngine{
        opaQuery:    &query,
        policyStore: store,
        auditLogger: auditor,
        tracer:      otel.Tracer("iam-engine"),
        logger:      logger,
        cache:       NewDecisionCache(30 * time.Second), // 30s TTL max
    }, nil
}

// Authorize evaluates whether the principal can perform the action on the resource
func (e *IAMEngine) Authorize(ctx context.Context, req *AuthorizationRequest) (*AuthorizationDecision, error) {
    ctx, span := e.tracer.Start(ctx, "iam.authorize",
        trace.WithAttributes(
            attribute.String("principal.id", req.Principal.ID),
            attribute.String("action", req.Action),
            attribute.String("resource", req.Resource),
        ),
    )
    defer span.End()
    
    start := time.Now()
    
    // Enrich principal with current role assignments
    roles, err := e.policyStore.GetRoles(ctx, req.Principal.ID)
    if err != nil {
        span.SetStatus(codes.Error, "failed to get roles")
        return nil, fmt.Errorf("role lookup failed: %w", err)
    }
    req.Principal.Roles = roles
    
    // Build OPA input document
    input := map[string]any{
        "principal": map[string]any{
            "id":           req.Principal.ID,
            "type":         string(req.Principal.Type),
            "roles":        req.Principal.Roles,
            "groups":       req.Principal.Groups,
            "attributes":   req.Principal.Attributes,
            "mfa_verified": req.Principal.MFAVerified,
            "spiffe_id":    req.Principal.SPIFFEID,
        },
        "action":    req.Action,
        "resource":  req.Resource,
        "namespace": req.Namespace,
        "source_ip": req.SourceIP,
        "request_id": req.RequestID,
        "timestamp": time.Now().UTC().Format(time.RFC3339),
        "conditions": req.Conditions,
    }
    
    // Evaluate OPA policy
    e.mu.RLock()
    rs, err := e.opaQuery.Eval(ctx, rego.EvalInput(input))
    e.mu.RUnlock()
    
    if err != nil {
        span.SetStatus(codes.Error, "opa evaluation failed")
        return nil, fmt.Errorf("policy evaluation failed: %w", err)
    }
    
    decision := &AuthorizationDecision{
        EvalTimeMs: time.Since(start).Milliseconds(),
    }
    
    if len(rs) == 0 || len(rs[0].Expressions) == 0 {
        decision.Allowed = false
        decision.Denials = []string{"no policy result (implicit deny)"}
    } else {
        result, ok := rs[0].Expressions[0].Value.(map[string]any)
        if !ok {
            return nil, fmt.Errorf("unexpected OPA result type")
        }
        
        if allowed, ok := result["allow"].(bool); ok {
            decision.Allowed = allowed
        }
        
        if denials, ok := result["deny"].([]any); ok {
            for _, d := range denials {
                if s, ok := d.(string); ok {
                    decision.Denials = append(decision.Denials, s)
                }
            }
            if len(decision.Denials) > 0 {
                decision.Allowed = false
            }
        }
    }
    
    // Record span outcome
    span.SetAttributes(attribute.Bool("decision.allowed", decision.Allowed))
    
    // Async audit log (non-blocking)
    go func() {
        auditCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
        defer cancel()
        if err := e.auditLogger.LogDecision(auditCtx, req, decision); err != nil {
            e.logger.Error("failed to write audit log",
                zap.Error(err),
                zap.String("request_id", req.RequestID),
            )
        }
    }()
    
    return decision, nil
}

// HTTPMiddleware wraps HTTP handlers with IAM enforcement
func (e *IAMEngine) HTTPMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx := r.Context()
        
        // 1. Extract and validate bearer token / mTLS cert
        principal, err := e.extractPrincipal(r)
        if err != nil {
            e.logger.Warn("authentication failed",
                zap.Error(err),
                zap.String("remote_addr", r.RemoteAddr),
            )
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }
        
        // 2. Map HTTP method + path to IAM action + resource
        action, resource := httpToIAMAction(r.Method, r.URL.Path)
        
        // 3. Build authorization request
        authReq := &AuthorizationRequest{
            Principal: principal,
            Action:    action,
            Resource:  resource,
            SourceIP:  extractClientIP(r),
            RequestID: r.Header.Get("X-Request-ID"),
        }
        
        // 4. Authorize
        decision, err := e.Authorize(ctx, authReq)
        if err != nil {
            e.logger.Error("authorization error", zap.Error(err))
            http.Error(w, "Internal Server Error", http.StatusInternalServerError)
            return
        }
        
        if !decision.Allowed {
            e.logger.Info("access denied",
                zap.String("principal", principal.ID),
                zap.String("action", action),
                zap.String("resource", resource),
                zap.Strings("reasons", decision.Denials),
            )
            http.Error(w, "Forbidden", http.StatusForbidden)
            return
        }
        
        // 5. Inject principal into context for downstream handlers
        ctx = WithPrincipal(ctx, principal)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// JWTClaims extends jwt.RegisteredClaims for our token format
type JWTClaims struct {
    jwt.RegisteredClaims
    Roles      []string          `json:"roles"`
    Groups     []string          `json:"groups"`
    MFA        bool              `json:"mfa"`
    Attributes map[string]string `json:"attrs,omitempty"`
    SPIFFEID   string            `json:"spiffe_id,omitempty"`
}

// extractPrincipal extracts Principal from JWT bearer token or mTLS cert
func (e *IAMEngine) extractPrincipal(r *http.Request) (*Principal, error) {
    // Try mTLS client certificate first (strongest)
    if r.TLS != nil && len(r.TLS.PeerCertificates) > 0 {
        return e.principalFromCert(r.TLS.PeerCertificates[0])
    }
    
    // Fall back to Bearer token
    authHeader := r.Header.Get("Authorization")
    if authHeader == "" {
        return nil, errors.New("no authentication credential provided")
    }
    
    if !strings.HasPrefix(authHeader, "Bearer ") {
        return nil, errors.New("authorization header must use Bearer scheme")
    }
    
    tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
    return e.validateJWT(tokenStr)
}

func (e *IAMEngine) validateJWT(tokenStr string) (*Principal, error) {
    // In production: fetch JWKS from identity provider
    // For demo: using static key
    token, err := jwt.ParseWithClaims(tokenStr, &JWTClaims{},
        func(token *jwt.Token) (interface{}, error) {
            if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
                return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
            }
            // Return public key (loaded from JWKS endpoint in production)
            return e.getPublicKey(token.Header["kid"].(string))
        },
        jwt.WithExpirationRequired(),
        jwt.WithIssuedAt(),
        jwt.WithIssuer("https://auth.corp.com"),
        jwt.WithAudience("iam-service"),
    )
    if err != nil {
        return nil, fmt.Errorf("invalid token: %w", err)
    }
    
    claims, ok := token.Claims.(*JWTClaims)
    if !ok || !token.Valid {
        return nil, errors.New("invalid token claims")
    }
    
    expiry, _ := claims.GetExpirationTime()
    issued, _ := claims.GetIssuedAt()
    
    return &Principal{
        ID:          claims.Subject,
        Type:        PrincipalUser,
        Roles:       claims.Roles,
        Groups:      claims.Groups,
        Attributes:  claims.Attributes,
        AuthMethod:  "jwt",
        MFAVerified: claims.MFA,
        IssuedAt:    issued.Time,
        ExpiresAt:   expiry.Time,
        SPIFFEID:    claims.SPIFFEID,
    }, nil
}

// Context keys
type contextKey string

const principalKey contextKey = "principal"

func WithPrincipal(ctx context.Context, p *Principal) context.Context {
    return context.WithValue(ctx, principalKey, p)
}

func PrincipalFromContext(ctx context.Context) (*Principal, bool) {
    p, ok := ctx.Value(principalKey).(*Principal)
    return p, ok
}

// DecisionCache: LRU with TTL for policy decisions
// (omitted for brevity — use github.com/hashicorp/golang-lru/v2/expirable)
type DecisionCache struct {
    ttl time.Duration
    // ... LRU internals
}

func NewDecisionCache(ttl time.Duration) *DecisionCache {
    return &DecisionCache{ttl: ttl}
}

// Helpers
func httpToIAMAction(method, path string) (action, resource string) {
    actionMap := map[string]string{
        "GET":    "read",
        "POST":   "create",
        "PUT":    "update",
        "PATCH":  "update",
        "DELETE": "delete",
    }
    a, ok := actionMap[method]
    if !ok {
        a = "unknown"
    }
    return fmt.Sprintf("http:%s", a), fmt.Sprintf("path:%s", path)
}

func extractClientIP(r *http.Request) string {
    // Check X-Forwarded-For (trust only if behind known proxy)
    if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
        parts := strings.Split(xff, ",")
        return strings.TrimSpace(parts[0])
    }
    // Fall back to RemoteAddr
    addr := r.RemoteAddr
    if idx := strings.LastIndex(addr, ":"); idx != -1 {
        return addr[:idx]
    }
    return addr
}

// ConstantTimeCompare for token comparison (timing-attack safe)
func safeCompare(a, b string) bool {
    return subtle.ConstantTimeCompare([]byte(a), []byte(b)) == 1
}
```

### 11.2 JWKS (JSON Web Key Set) Client with Caching

```go
// pkg/iam/jwks.go
package iam

import (
    "context"
    "crypto/rsa"
    "encoding/base64"
    "encoding/json"
    "fmt"
    "math/big"
    "net/http"
    "sync"
    "time"
)

// JWKSClient fetches and caches public keys from an OIDC provider
type JWKSClient struct {
    mu          sync.RWMutex
    jwksURL     string
    keys        map[string]*rsa.PublicKey
    lastFetched time.Time
    cacheTTL    time.Duration
    httpClient  *http.Client
}

type jwksResponse struct {
    Keys []jwk `json:"keys"`
}

type jwk struct {
    Kid string `json:"kid"`
    Kty string `json:"kty"`
    Alg string `json:"alg"`
    Use string `json:"use"`
    N   string `json:"n"`
    E   string `json:"e"`
}

func NewJWKSClient(jwksURL string, cacheTTL time.Duration) *JWKSClient {
    return &JWKSClient{
        jwksURL:  jwksURL,
        keys:     make(map[string]*rsa.PublicKey),
        cacheTTL: cacheTTL,
        httpClient: &http.Client{
            Timeout: 10 * time.Second,
            Transport: &http.Transport{
                TLSHandshakeTimeout: 5 * time.Second,
                // Only trust valid TLS certs
                TLSClientConfig: &tls.Config{
                    MinVersion: tls.VersionTLS13,
                },
            },
        },
    }
}

func (c *JWKSClient) GetKey(ctx context.Context, kid string) (*rsa.PublicKey, error) {
    c.mu.RLock()
    key, ok := c.keys[kid]
    stale := time.Since(c.lastFetched) > c.cacheTTL
    c.mu.RUnlock()
    
    if ok && !stale {
        return key, nil
    }
    
    // Refresh JWKS
    if err := c.refresh(ctx); err != nil {
        if ok {
            // Return cached key even if stale, log warning
            return key, nil
        }
        return nil, fmt.Errorf("failed to fetch JWKS and no cached key: %w", err)
    }
    
    c.mu.RLock()
    defer c.mu.RUnlock()
    
    key, ok = c.keys[kid]
    if !ok {
        return nil, fmt.Errorf("key ID %q not found in JWKS", kid)
    }
    return key, nil
}

func (c *JWKSClient) refresh(ctx context.Context) error {
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.jwksURL, nil)
    if err != nil {
        return err
    }
    
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return fmt.Errorf("JWKS fetch failed: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("JWKS endpoint returned status %d", resp.StatusCode)
    }
    
    var jwks jwksResponse
    if err := json.NewDecoder(resp.Body).Decode(&jwks); err != nil {
        return fmt.Errorf("failed to decode JWKS: %w", err)
    }
    
    newKeys := make(map[string]*rsa.PublicKey)
    for _, key := range jwks.Keys {
        if key.Kty != "RSA" || key.Use != "sig" {
            continue
        }
        
        pub, err := parseRSAPublicKey(key.N, key.E)
        if err != nil {
            continue
        }
        newKeys[key.Kid] = pub
    }
    
    c.mu.Lock()
    c.keys = newKeys
    c.lastFetched = time.Now()
    c.mu.Unlock()
    
    return nil
}

func parseRSAPublicKey(nB64, eB64 string) (*rsa.PublicKey, error) {
    nBytes, err := base64.RawURLEncoding.DecodeString(nB64)
    if err != nil {
        return nil, err
    }
    eBytes, err := base64.RawURLEncoding.DecodeString(eB64)
    if err != nil {
        return nil, err
    }
    
    n := new(big.Int).SetBytes(nBytes)
    e := new(big.Int).SetBytes(eBytes)
    
    return &rsa.PublicKey{
        N: n,
        E: int(e.Int64()),
    }, nil
}
```

### 11.3 Audit Logger (Structured, Immutable)

```go
// pkg/iam/audit.go
package iam

import (
    "context"
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "time"
    
    "go.uber.org/zap"
)

// AuditEvent is the immutable audit record
type AuditEvent struct {
    EventID      string                 `json:"event_id"`
    Timestamp    time.Time              `json:"timestamp"`
    EventType    string                 `json:"event_type"`
    Principal    string                 `json:"principal"`
    PrincipalType string               `json:"principal_type"`
    Action       string                 `json:"action"`
    Resource     string                 `json:"resource"`
    Namespace    string                 `json:"namespace,omitempty"`
    SourceIP     string                 `json:"source_ip"`
    RequestID    string                 `json:"request_id"`
    Decision     bool                   `json:"decision"`
    Reasons      []string               `json:"reasons,omitempty"`
    Denials      []string               `json:"denials,omitempty"`
    EvalTimeMs   int64                  `json:"eval_time_ms"`
    Metadata     map[string]any         `json:"metadata,omitempty"`
    // Chain-of-custody HMAC (links events together for tamper detection)
    PrevHash     string                 `json:"prev_hash"`
    Hash         string                 `json:"hash"`
}

// ChainedAuditLogger maintains an HMAC chain for tamper-evidence
type ChainedAuditLogger struct {
    logger   *zap.Logger
    hmacKey  []byte
    prevHash string
    mu       sync.Mutex
    writer   AuditWriter // Interface: file, Kafka, cloud logging
}

type AuditWriter interface {
    Write(ctx context.Context, event *AuditEvent) error
}

func (l *ChainedAuditLogger) LogDecision(ctx context.Context, req *AuthorizationRequest, dec *AuthorizationDecision) error {
    l.mu.Lock()
    defer l.mu.Unlock()
    
    event := &AuditEvent{
        EventID:       generateEventID(),
        Timestamp:     time.Now().UTC(),
        EventType:     "authorization_decision",
        Principal:     req.Principal.ID,
        PrincipalType: string(req.Principal.Type),
        Action:        req.Action,
        Resource:      req.Resource,
        Namespace:     req.Namespace,
        SourceIP:      req.SourceIP,
        RequestID:     req.RequestID,
        Decision:      dec.Allowed,
        Reasons:       dec.Reasons,
        Denials:       dec.Denials,
        EvalTimeMs:    dec.EvalTimeMs,
        PrevHash:      l.prevHash,
    }
    
    // Compute HMAC over event content for tamper detection
    event.Hash = l.computeHash(event)
    l.prevHash = event.Hash
    
    if err := l.writer.Write(ctx, event); err != nil {
        return fmt.Errorf("failed to write audit event: %w", err)
    }
    
    // Also log to structured logger for real-time monitoring
    l.logger.Info("authorization_decision",
        zap.String("event_id", event.EventID),
        zap.String("principal", event.Principal),
        zap.String("action", event.Action),
        zap.String("resource", event.Resource),
        zap.Bool("allowed", event.Decision),
        zap.String("source_ip", event.SourceIP),
        zap.String("hash", event.Hash),
    )
    
    return nil
}

func (l *ChainedAuditLogger) computeHash(event *AuditEvent) string {
    // Hash over canonical fields + prevHash for chaining
    content := fmt.Sprintf("%s|%s|%s|%s|%s|%s|%v|%s",
        event.EventID,
        event.Timestamp.Format(time.RFC3339Nano),
        event.Principal,
        event.Action,
        event.Resource,
        event.RequestID,
        event.Decision,
        event.PrevHash,
    )
    
    mac := hmac.New(sha256.New, l.hmacKey)
    mac.Write([]byte(content))
    return hex.EncodeToString(mac.Sum(nil))
}

// VerifyChain validates the integrity of an audit event sequence
func VerifyChain(events []*AuditEvent, hmacKey []byte) error {
    logger := &ChainedAuditLogger{hmacKey: hmacKey}
    
    for i, event := range events {
        expectedHash := logger.computeHash(event)
        if event.Hash != expectedHash {
            return fmt.Errorf("tampered event at index %d: hash mismatch (event_id=%s)", i, event.EventID)
        }
        if i > 0 && event.PrevHash != events[i-1].Hash {
            return fmt.Errorf("chain break at index %d: prevHash mismatch", i)
        }
    }
    return nil
}
```

---

## 12. Rust Implementation: Policy Evaluator and Token Validator

### 12.1 JWT Validator in Rust

```rust
// src/jwt_validator.rs
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use jsonwebtoken::{decode, decode_header, Algorithm, DecodingKey, Validation};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use tokio::sync::RwLock;
use thiserror::Error;
use tracing::{error, info, warn, instrument};

#[derive(Error, Debug)]
pub enum JWTError {
    #[error("token expired")]
    Expired,
    #[error("invalid signature")]
    InvalidSignature,
    #[error("unknown key id: {0}")]
    UnknownKeyId(String),
    #[error("JWKS fetch failed: {0}")]
    JWKSFetchFailed(String),
    #[error("invalid claims: {0}")]
    InvalidClaims(String),
    #[error("unsupported algorithm: {0}")]
    UnsupportedAlgorithm(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub iss: String,
    pub aud: Vec<String>,
    pub exp: u64,
    pub iat: u64,
    pub nbf: Option<u64>,
    pub jti: Option<String>,
    pub roles: Option<Vec<String>>,
    pub groups: Option<Vec<String>>,
    pub mfa: Option<bool>,
    pub attrs: Option<HashMap<String, String>>,
    pub spiffe_id: Option<String>,
}

#[derive(Debug, Clone)]
pub struct ValidatedPrincipal {
    pub subject: String,
    pub issuer: String,
    pub roles: Vec<String>,
    pub groups: Vec<String>,
    pub mfa_verified: bool,
    pub attributes: HashMap<String, String>,
    pub spiffe_id: Option<String>,
    pub token_id: Option<String>,
    pub expires_at: SystemTime,
}

#[derive(Deserialize)]
struct JwkSet {
    keys: Vec<Jwk>,
}

#[derive(Deserialize, Clone)]
struct Jwk {
    kid: String,
    kty: String,
    alg: Option<String>,
    #[serde(rename = "use")]
    use_: Option<String>,
    n: Option<String>,
    e: Option<String>,
    crv: Option<String>,
    x: Option<String>,
    y: Option<String>,
}

struct CachedKey {
    decoding_key: DecodingKey,
    algorithm: Algorithm,
    cached_at: SystemTime,
}

pub struct JWTValidator {
    jwks_url: String,
    expected_issuer: String,
    expected_audience: String,
    cache: Arc<RwLock<HashMap<String, CachedKey>>>,
    cache_ttl: Duration,
    http_client: Client,
    clock_skew: Duration,
}

impl JWTValidator {
    pub fn new(
        jwks_url: impl Into<String>,
        expected_issuer: impl Into<String>,
        expected_audience: impl Into<String>,
    ) -> Self {
        let http_client = Client::builder()
            .timeout(Duration::from_secs(10))
            .use_rustls_tls()          // Use rustls (memory-safe TLS)
            .min_tls_version(reqwest::tls::Version::TLS_1_3)
            .build()
            .expect("failed to build HTTP client");

        Self {
            jwks_url: jwks_url.into(),
            expected_issuer: expected_issuer.into(),
            expected_audience: expected_audience.into(),
            cache: Arc::new(RwLock::new(HashMap::new())),
            cache_ttl: Duration::from_secs(300), // 5 minutes
            http_client,
            clock_skew: Duration::from_secs(30), // 30 second leeway
        }
    }

    #[instrument(skip(self, token), fields(issuer = %self.expected_issuer))]
    pub async fn validate(&self, token: &str) -> Result<ValidatedPrincipal, JWTError> {
        // 1. Decode header to get kid and alg (no signature verification yet)
        let header = decode_header(token).map_err(|_| {
            JWTError::InvalidSignature
        })?;

        let kid = header.kid.unwrap_or_default();
        
        // Reject insecure algorithms
        match header.alg {
            Algorithm::RS256 | Algorithm::RS384 | Algorithm::RS512 |
            Algorithm::ES256 | Algorithm::ES384 | Algorithm::PS256 |
            Algorithm::PS384 | Algorithm::PS512 => {},
            alg => return Err(JWTError::UnsupportedAlgorithm(format!("{:?}", alg))),
        }

        // 2. Fetch decoding key (from cache or JWKS endpoint)
        let decoding_key = self.get_decoding_key(&kid, header.alg).await?;

        // 3. Validate with strict settings
        let mut validation = Validation::new(header.alg);
        validation.set_issuer(&[&self.expected_issuer]);
        validation.set_audience(&[&self.expected_audience]);
        validation.validate_exp = true;
        validation.validate_nbf = true;
        validation.leeway = self.clock_skew.as_secs();

        let token_data = decode::<Claims>(token, &decoding_key, &validation)
            .map_err(|e| {
                warn!("token validation failed: {:?}", e);
                JWTError::InvalidSignature
            })?;

        let claims = token_data.claims;

        // 4. Additional custom validation
        self.validate_claims(&claims)?;

        info!(
            subject = %claims.sub,
            jti = ?claims.jti,
            "JWT validated successfully"
        );

        Ok(ValidatedPrincipal {
            subject: claims.sub,
            issuer: claims.iss,
            roles: claims.roles.unwrap_or_default(),
            groups: claims.groups.unwrap_or_default(),
            mfa_verified: claims.mfa.unwrap_or(false),
            attributes: claims.attrs.unwrap_or_default(),
            spiffe_id: claims.spiffe_id,
            token_id: claims.jti,
            expires_at: UNIX_EPOCH + Duration::from_secs(claims.exp),
        })
    }

    async fn get_decoding_key(&self, kid: &str, alg: Algorithm) -> Result<DecodingKey, JWTError> {
        // Check cache first
        {
            let cache = self.cache.read().await;
            if let Some(cached) = cache.get(kid) {
                if cached.cached_at.elapsed().unwrap_or_default() < self.cache_ttl {
                    return Ok(cached.decoding_key.clone());
                }
            }
        }

        // Fetch fresh JWKS
        self.refresh_jwks().await?;

        // Try cache again after refresh
        let cache = self.cache.read().await;
        cache.get(kid)
            .map(|c| c.decoding_key.clone())
            .ok_or_else(|| JWTError::UnknownKeyId(kid.to_string()))
    }

    async fn refresh_jwks(&self) -> Result<(), JWTError> {
        let response = self.http_client
            .get(&self.jwks_url)
            .send()
            .await
            .map_err(|e| JWTError::JWKSFetchFailed(e.to_string()))?;

        if !response.status().is_success() {
            return Err(JWTError::JWKSFetchFailed(
                format!("HTTP {}", response.status())
            ));
        }

        let jwks: JwkSet = response.json().await
            .map_err(|e| JWTError::JWKSFetchFailed(e.to_string()))?;

        let mut cache = self.cache.write().await;
        
        for jwk in jwks.keys {
            // Only process signature keys
            if jwk.use_.as_deref() != Some("sig") {
                continue;
            }

            let result = self.jwk_to_decoding_key(&jwk);
            match result {
                Ok((key, alg)) => {
                    cache.insert(jwk.kid.clone(), CachedKey {
                        decoding_key: key,
                        algorithm: alg,
                        cached_at: SystemTime::now(),
                    });
                }
                Err(e) => {
                    warn!("failed to parse JWK {}: {:?}", jwk.kid, e);
                }
            }
        }

        Ok(())
    }

    fn jwk_to_decoding_key(&self, jwk: &Jwk) -> Result<(DecodingKey, Algorithm), JWTError> {
        match jwk.kty.as_str() {
            "RSA" => {
                let n = jwk.n.as_deref().ok_or_else(|| {
                    JWTError::InvalidClaims("RSA key missing n".into())
                })?;
                let e = jwk.e.as_deref().ok_or_else(|| {
                    JWTError::InvalidClaims("RSA key missing e".into())
                })?;
                
                let key = DecodingKey::from_rsa_components(n, e)
                    .map_err(|e| JWTError::InvalidClaims(e.to_string()))?;
                
                Ok((key, Algorithm::RS256))
            }
            "EC" => {
                let x = jwk.x.as_deref().ok_or_else(|| {
                    JWTError::InvalidClaims("EC key missing x".into())
                })?;
                let y = jwk.y.as_deref().ok_or_else(|| {
                    JWTError::InvalidClaims("EC key missing y".into())
                })?;
                
                let key = DecodingKey::from_ec_components(x, y)
                    .map_err(|e| JWTError::InvalidClaims(e.to_string()))?;
                
                Ok((key, Algorithm::ES256))
            }
            kty => Err(JWTError::UnsupportedAlgorithm(kty.to_string())),
        }
    }

    fn validate_claims(&self, claims: &Claims) -> Result<(), JWTError> {
        // Validate not-before
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        if let Some(nbf) = claims.nbf {
            if now + self.clock_skew.as_secs() < nbf {
                return Err(JWTError::InvalidClaims("token not yet valid".into()));
            }
        }

        // Ensure subject is non-empty
        if claims.sub.trim().is_empty() {
            return Err(JWTError::InvalidClaims("empty subject".into()));
        }

        Ok(())
    }
}
```

### 12.2 Rust Policy Evaluator

```rust
// src/policy_engine.rs
use std::collections::{HashMap, HashSet};
use std::net::IpAddr;
use std::str::FromStr;

use ipnet::IpNet;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum PolicyError {
    #[error("policy syntax error: {0}")]
    SyntaxError(String),
    #[error("evaluation error: {0}")]
    EvalError(String),
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Effect {
    Allow,
    Deny,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct PolicyStatement {
    pub sid: Option<String>,
    pub effect: Effect,
    pub principals: Vec<String>, // ["*", "role:admin", "user:alice"]
    pub actions: Vec<String>,    // ["s3:GetObject", "*"]
    pub resources: Vec<String>,  // ["s3://bucket/*", "*"]
    pub conditions: Vec<PolicyCondition>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum PolicyCondition {
    IpRange { cidr: String },
    TimeWindow { start_hour: u8, end_hour: u8 },
    MfaRequired { required: bool },
    StringEquals { key: String, value: String },
    TagMatch { resource_tag: String, principal_tag: String },
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Policy {
    pub version: String,
    pub statements: Vec<PolicyStatement>,
}

#[derive(Debug, Clone)]
pub struct EvalContext {
    pub principal_id: String,
    pub principal_roles: Vec<String>,
    pub principal_groups: Vec<String>,
    pub principal_tags: HashMap<String, String>,
    pub action: String,
    pub resource: String,
    pub resource_tags: HashMap<String, String>,
    pub source_ip: Option<IpAddr>,
    pub mfa_verified: bool,
    pub request_time: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone)]
pub struct EvalResult {
    pub allowed: bool,
    pub matching_sid: Option<String>,
    pub reason: String,
}

pub struct PolicyEngine {
    policies: Vec<Policy>,
}

impl PolicyEngine {
    pub fn new(policies: Vec<Policy>) -> Self {
        Self { policies }
    }

    /// Evaluate with explicit deny taking precedence (AWS-style)
    pub fn evaluate(&self, ctx: &EvalContext) -> EvalResult {
        let mut any_allow = false;
        let mut allow_sid = None;

        for policy in &self.policies {
            for statement in &policy.statements {
                if !self.matches_principal(&statement.principals, ctx) {
                    continue;
                }
                if !self.matches_action(&statement.actions, &ctx.action) {
                    continue;
                }
                if !self.matches_resource(&statement.resources, &ctx.resource) {
                    continue;
                }
                if !self.evaluate_conditions(&statement.conditions, ctx) {
                    continue;
                }

                match statement.effect {
                    Effect::Deny => {
                        // Explicit deny always wins
                        return EvalResult {
                            allowed: false,
                            matching_sid: statement.sid.clone(),
                            reason: "explicit deny policy".to_string(),
                        };
                    }
                    Effect::Allow => {
                        any_allow = true;
                        allow_sid = statement.sid.clone();
                    }
                }
            }
        }

        if any_allow {
            EvalResult {
                allowed: true,
                matching_sid: allow_sid,
                reason: "allowed by policy".to_string(),
            }
        } else {
            EvalResult {
                allowed: false,
                matching_sid: None,
                reason: "implicit deny (no matching allow statement)".to_string(),
            }
        }
    }

    fn matches_principal(&self, principals: &[String], ctx: &EvalContext) -> bool {
        for p in principals {
            if p == "*" {
                return true;
            }
            if p == &format!("user:{}", ctx.principal_id) {
                return true;
            }
            if let Some(role) = p.strip_prefix("role:") {
                if ctx.principal_roles.iter().any(|r| r == role) {
                    return true;
                }
            }
            if let Some(group) = p.strip_prefix("group:") {
                if ctx.principal_groups.iter().any(|g| g == group) {
                    return true;
                }
            }
        }
        false
    }

    fn matches_action(&self, actions: &[String], action: &str) -> bool {
        actions.iter().any(|pattern| self.glob_match(pattern, action))
    }

    fn matches_resource(&self, resources: &[String], resource: &str) -> bool {
        resources.iter().any(|pattern| self.glob_match(pattern, resource))
    }

    /// Glob matching with * wildcard
    fn glob_match(&self, pattern: &str, value: &str) -> bool {
        if pattern == "*" {
            return true;
        }
        if !pattern.contains('*') {
            return pattern == value;
        }
        
        // Split on * and check all segments appear in order
        let parts: Vec<&str> = pattern.split('*').collect();
        let mut pos = 0;
        
        for (i, part) in parts.iter().enumerate() {
            if part.is_empty() {
                continue;
            }
            if i == 0 {
                // First segment must match start
                if !value.starts_with(part) {
                    return false;
                }
                pos = part.len();
            } else if i == parts.len() - 1 {
                // Last segment must match end
                return value.ends_with(part);
            } else {
                // Middle segments: find occurrence after current pos
                if let Some(found) = value[pos..].find(part) {
                    pos += found + part.len();
                } else {
                    return false;
                }
            }
        }
        true
    }

    fn evaluate_conditions(&self, conditions: &[PolicyCondition], ctx: &EvalContext) -> bool {
        conditions.iter().all(|cond| self.evaluate_condition(cond, ctx))
    }

    fn evaluate_condition(&self, condition: &PolicyCondition, ctx: &EvalContext) -> bool {
        match condition {
            PolicyCondition::IpRange { cidr } => {
                if let (Some(ip), Ok(net)) = (ctx.source_ip, IpNet::from_str(cidr)) {
                    net.contains(&ip)
                } else {
                    false
                }
            }
            PolicyCondition::TimeWindow { start_hour, end_hour } => {
                let hour = ctx.request_time.format("%H").to_string().parse::<u8>().unwrap_or(0);
                hour >= *start_hour && hour < *end_hour
            }
            PolicyCondition::MfaRequired { required } => {
                !required || ctx.mfa_verified
            }
            PolicyCondition::StringEquals { key, value } => {
                ctx.principal_tags.get(key).map(|v| v == value).unwrap_or(false)
            }
            PolicyCondition::TagMatch { resource_tag, principal_tag } => {
                match (ctx.resource_tags.get(resource_tag), ctx.principal_tags.get(principal_tag)) {
                    (Some(rv), Some(pv)) => rv == pv,
                    _ => false,
                }
            }
        }
    }
}

// SoD enforcement layer
pub struct SoDEngine {
    constraints: Vec<SoDConstraint>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SoDConstraint {
    pub name: String,
    pub conflicting_roles: Vec<String>,
    pub constraint_type: SoDType,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SoDType {
    Static,   // User cannot hold both roles
    Dynamic,  // User cannot activate both roles in same session
}

impl SoDEngine {
    pub fn new(constraints: Vec<SoDConstraint>) -> Self {
        Self { constraints }
    }

    pub fn check_static_sod(&self, roles: &[String]) -> Vec<String> {
        let role_set: HashSet<&str> = roles.iter().map(|r| r.as_str()).collect();
        let mut violations = Vec::new();
        
        for constraint in &self.constraints {
            if !matches!(constraint.constraint_type, SoDType::Static) {
                continue;
            }
            
            let conflicting: Vec<&str> = constraint.conflicting_roles.iter()
                .filter(|r| role_set.contains(r.as_str()))
                .map(|r| r.as_str())
                .collect();
            
            if conflicting.len() >= 2 {
                violations.push(format!(
                    "SoD violation '{}': roles {:?} cannot be held simultaneously",
                    constraint.name, conflicting
                ));
            }
        }
        
        violations
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::Ipv4Addr;

    fn make_ctx(roles: Vec<String>) -> EvalContext {
        EvalContext {
            principal_id: "alice".to_string(),
            principal_roles: roles,
            principal_groups: vec![],
            principal_tags: HashMap::new(),
            action: "s3:GetObject".to_string(),
            resource: "s3://prod-bucket/data/file.json".to_string(),
            resource_tags: HashMap::new(),
            source_ip: Some(IpAddr::V4(Ipv4Addr::new(10, 0, 0, 5))),
            mfa_verified: true,
            request_time: chrono::Utc::now(),
        }
    }

    #[test]
    fn test_explicit_deny_wins() {
        let engine = PolicyEngine::new(vec![
            Policy {
                version: "1.0".into(),
                statements: vec![
                    PolicyStatement {
                        sid: Some("allow-all".into()),
                        effect: Effect::Allow,
                        principals: vec!["*".into()],
                        actions: vec!["*".into()],
                        resources: vec!["*".into()],
                        conditions: vec![],
                    },
                    PolicyStatement {
                        sid: Some("deny-delete".into()),
                        effect: Effect::Deny,
                        principals: vec!["user:alice".into()],
                        actions: vec!["s3:DeleteObject".into()],
                        resources: vec!["s3://prod-bucket/*".into()],
                        conditions: vec![],
                    },
                ],
            }
        ]);

        let mut ctx = make_ctx(vec!["admin".into()]);
        ctx.action = "s3:DeleteObject".to_string();
        ctx.resource = "s3://prod-bucket/important.json".to_string();

        let result = engine.evaluate(&ctx);
        assert!(!result.allowed, "Explicit deny must override allow");
        assert_eq!(result.matching_sid, Some("deny-delete".into()));
    }

    #[test]
    fn test_implicit_deny_default() {
        let engine = PolicyEngine::new(vec![]);
        let ctx = make_ctx(vec![]);
        let result = engine.evaluate(&ctx);
        assert!(!result.allowed, "No policies = implicit deny");
    }

    #[test]
    fn test_ip_range_condition() {
        let engine = PolicyEngine::new(vec![
            Policy {
                version: "1.0".into(),
                statements: vec![
                    PolicyStatement {
                        sid: None,
                        effect: Effect::Allow,
                        principals: vec!["user:alice".into()],
                        actions: vec!["s3:GetObject".into()],
                        resources: vec!["s3://prod-bucket/*".into()],
                        conditions: vec![
                            PolicyCondition::IpRange { cidr: "10.0.0.0/8".into() }
                        ],
                    }
                ],
            }
        ]);

        // IP in range: allow
        let ctx = make_ctx(vec![]);
        let result = engine.evaluate(&ctx);
        assert!(result.allowed);

        // IP out of range: deny
        let mut ctx2 = make_ctx(vec![]);
        ctx2.source_ip = Some(IpAddr::V4(Ipv4Addr::new(192, 168, 1, 1)));
        let result2 = engine.evaluate(&ctx2);
        assert!(!result2.allowed);
    }

    #[test]
    fn test_glob_matching() {
        let engine = PolicyEngine::new(vec![]);
        assert!(engine.glob_match("s3:*", "s3:GetObject"));
        assert!(engine.glob_match("s3://bucket/*", "s3://bucket/dir/file.json"));
        assert!(!engine.glob_match("s3://bucket/*", "s3://other/file"));
        assert!(engine.glob_match("*", "anything"));
    }

    #[test]
    fn test_sod_static_violation() {
        let sod = SoDEngine::new(vec![
            SoDConstraint {
                name: "financial".into(),
                conflicting_roles: vec!["accounts-payable".into(), "accounts-receivable".into()],
                constraint_type: SoDType::Static,
            }
        ]);

        let roles = vec!["accounts-payable".into(), "accounts-receivable".into(), "viewer".into()];
        let violations = sod.check_static_sod(&roles);
        assert!(!violations.is_empty(), "SoD violation should be detected");
    }
}
```

---

## 13. Secrets Management: Vault, SOPS, KMS

### 13.1 HashiCorp Vault Architecture

```
+------------------------+
|    Vault Cluster        |
|                        |
|  +------------------+  |
|  |  Core Engine     |  |
|  |  - Barrier (AES) |  |
|  |  - Token Store   |  |
|  |  - Policy Engine |  |
|  +------------------+  |
|                        |
|  Auth Methods:         |  Clients authenticate via:
|  - Kubernetes          |  -> JWT (projected SA token)
|  - AWS IAM             |  -> AWS SigV4
|  - OIDC                |  -> OIDC token
|  - TLS certs           |  -> mTLS
|  - AppRole             |  -> role_id + secret_id
|                        |
|  Secret Engines:       |  Secrets backends:
|  - KV v2 (versioned)   |  Static secrets
|  - PKI                 |  Dynamic X.509 certs
|  - Database            |  Dynamic DB credentials
|  - AWS                 |  Dynamic IAM credentials
|  - Transit             |  Encryption-as-a-Service
|                        |
|  Storage Backend:      |
|  - Integrated Raft     |  HA, distributed
|  - Consul              |  External HA
+------------------------+
         |
         | Seal Key (unseal)
         v
+------------------------+
| Shamir / Auto-unseal   |
| AWS KMS / GCP KMS      |
| Azure Key Vault        |
+------------------------+
```

```bash
# Vault production deployment with Raft (integrated storage)
cat > /etc/vault.d/vault.hcl << 'EOF'
ui            = false
disable_mlock = false   # Keep mlock enabled (prevents swap of secrets)
log_level     = "info"
log_format    = "json"

storage "raft" {
    path    = "/opt/vault/data"
    node_id = "vault-node-1"
    
    retry_join {
        leader_api_addr = "https://vault-2.internal:8200"
    }
    retry_join {
        leader_api_addr = "https://vault-3.internal:8200"
    }
}

listener "tcp" {
    address            = "0.0.0.0:8200"
    tls_cert_file      = "/etc/vault/certs/vault.pem"
    tls_key_file       = "/etc/vault/certs/vault-key.pem"
    tls_client_ca_file = "/etc/vault/certs/ca.pem"
    tls_min_version    = "tls13"
    
    # Require mTLS for all connections
    tls_require_and_verify_client_cert = true
}

api_addr     = "https://vault-1.internal:8200"
cluster_addr = "https://vault-1.internal:8201"

# Auto-unseal with AWS KMS
seal "awskms" {
    region     = "us-east-1"
    kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/mrk-abc123"
}

telemetry {
    prometheus_retention_time = "30s"
    disable_hostname           = false
}

audit {
    type = "file"
    options {
        file_path = "/var/log/vault/audit.log"
        format    = "json"
        hmac_accessor = true
    }
}
EOF

# Initialize Vault (first time only)
vault operator init \
  -recovery-shares=5 \
  -recovery-threshold=3  # For auto-unseal with KMS
  
# For Shamir:
# vault operator init -key-shares=5 -key-threshold=3

# Enable Kubernetes auth method
vault auth enable kubernetes

vault write auth/kubernetes/config \
    kubernetes_host="https://k8s-api.internal:6443" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
    issuer="https://kubernetes.default.svc.cluster.local" \
    disable_iss_validation=false

# Create role: pods in namespace 'production' with SA 'payment-svc' get this role
vault write auth/kubernetes/role/payment-svc \
    bound_service_account_names="payment-svc" \
    bound_service_account_namespaces="production" \
    policies="payment-svc-policy" \
    ttl=1h \
    max_ttl=4h

# Create policy (least privilege)
cat > payment-svc-policy.hcl << 'EOF'
# Read DB credentials
path "database/creds/payment-db" {
    capabilities = ["read"]
}

# Read app config
path "secret/data/payment-svc/*" {
    capabilities = ["read"]
}

# Renew own token
path "auth/token/renew-self" {
    capabilities = ["update"]
}

# Lookup own token
path "auth/token/lookup-self" {
    capabilities = ["read"]
}
EOF
vault policy write payment-svc-policy payment-svc-policy.hcl

# Enable PKI engine for dynamic certificate issuance
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki

vault write pki/root/generate/internal \
    common_name="Corp Internal CA" \
    ttl=87600h \
    key_type=rsa \
    key_bits=4096

vault write pki/roles/service-certs \
    allowed_domains="internal.corp.com,svc.cluster.local" \
    allow_subdomains=true \
    max_ttl=72h \
    key_type=rsa \
    key_bits=2048 \
    require_cn=true

# Issue certificate
vault write pki/issue/service-certs \
    common_name="payment-svc.production.svc.cluster.local" \
    alt_names="payment-svc,payment-svc.production" \
    ttl=24h

# Dynamic DB credentials
vault secrets enable database

vault write database/config/payment-postgres \
    plugin_name=postgresql-database-plugin \
    allowed_roles="payment-svc" \
    connection_url="postgresql://{{username}}:{{password}}@postgres.internal:5432/payment?sslmode=require" \
    username="vault-admin" \
    password="vault-admin-password"

vault write database/roles/payment-svc \
    db_name=payment-postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';
                         GRANT SELECT, INSERT, UPDATE ON payments, transactions TO \"{{name}}\";" \
    revocation_statements="DROP ROLE IF EXISTS \"{{name}}\";" \
    default_ttl=1h \
    max_ttl=4h

# Get credentials
vault read database/creds/payment-svc
```

### 13.2 Vault Agent Sidecar (Kubernetes)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-svc
  namespace: production
spec:
  template:
    metadata:
      annotations:
        # Vault Agent injection
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "payment-svc"
        vault.hashicorp.com/agent-inject-secret-db: "database/creds/payment-svc"
        vault.hashicorp.com/agent-inject-template-db: |
          {{- with secret "database/creds/payment-svc" -}}
          POSTGRES_USER={{ .Data.username }}
          POSTGRES_PASSWORD={{ .Data.password }}
          POSTGRES_HOST=postgres.internal
          {{- end }}
        vault.hashicorp.com/agent-inject-secret-config: "secret/data/payment-svc/config"
        vault.hashicorp.com/agent-pre-populate-only: "false"
        vault.hashicorp.com/agent-revoke-on-shutdown: "true"
        vault.hashicorp.com/agent-cache-enable: "true"
```

### 13.3 SOPS: Secrets in Git

```bash
# SOPS (Secrets OPerationS): encrypt secrets files for Git storage
# Uses AWS KMS, GCP KMS, Azure Key Vault, PGP, or age

# .sops.yaml configuration
cat > .sops.yaml << 'EOF'
creation_rules:
  # Production: use AWS KMS
  - path_regex: secrets/production/.*
    kms: "arn:aws:kms:us-east-1:123456789012:key/mrk-prod"
    
  # Staging: use GCP KMS
  - path_regex: secrets/staging/.*
    gcp_kms: "projects/my-project/locations/us-central1/keyRings/sops/cryptoKeys/staging"
    
  # Local dev: use age
  - path_regex: secrets/dev/.*
    age: "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"
EOF

# Encrypt secrets file
sops -e -i secrets/production/payment-svc.yaml

# Edit (decrypts in-memory, re-encrypts on save)
sops secrets/production/payment-svc.yaml

# Decrypt for use (never store decrypted form)
sops -d secrets/production/payment-svc.yaml

# In CI/CD pipeline:
sops -d secrets/production/payment-svc.yaml | kubectl apply -f -
```

---

## 14. Audit Logging and Non-Repudiation

### 14.1 Linux Audit Subsystem (auditd)

```bash
# auditd configuration: /etc/audit/auditd.conf
num_logs = 10
max_log_file = 100        # MB per log file
max_log_file_action = ROTATE
space_left = 500          # MB remaining before alert
space_left_action = SYSLOG
admin_space_left = 100    # MB remaining before action
admin_space_left_action = SUSPEND  # Suspend auditd if disk full

# Audit rules: /etc/audit/rules.d/
cat > /etc/audit/rules.d/99-security.rules << 'EOF'
# Delete all existing rules
-D

# Set buffer size (increase for high-load systems)
-b 8192

# Failure mode: 1=printk, 2=panic
-f 1

# Immutable: prevent rules modification without reboot (-e 2)
# Add this LAST after all rules
# -e 2

# === File System Watches ===
# Watch sensitive files
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k sudo
-w /etc/sudoers.d/ -p wa -k sudo
-w /etc/ssh/sshd_config -p wa -k sshd
-w /etc/pam.d/ -p wa -k pam

# Audit log access
-w /var/log/audit/ -p wa -k audit_logs
-w /etc/audit/ -p wa -k audit_config

# Systemd
-w /usr/lib/systemd/ -p wa -k systemd
-w /etc/systemd/ -p wa -k systemd

# === Privileged Commands ===
-a always,exit -F path=/usr/bin/sudo -F perm=x -F auid>=1000 -F auid!=unset -k privileged_sudo
-a always,exit -F path=/usr/bin/su -F perm=x -F auid>=1000 -F auid!=unset -k privileged_su
-a always,exit -F path=/usr/bin/newgrp -F perm=x -F auid>=1000 -k privileged_newgrp
-a always,exit -F path=/usr/bin/chsh -F perm=x -F auid>=1000 -k privileged_chsh
-a always,exit -F path=/usr/sbin/usermod -F perm=x -F auid>=1000 -k account_mod
-a always,exit -F path=/usr/sbin/useradd -F perm=x -F auid>=1000 -k account_add
-a always,exit -F path=/usr/sbin/userdel -F perm=x -F auid>=1000 -k account_del

# === Capability and Setuid Changes ===
-a always,exit -F arch=b64 -S setuid -S setgid -S setreuid -S setregid -k privilege_change
-a always,exit -F arch=b64 -S capset -k capabilities

# === Module Loading (critical for rootkit detection) ===
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S finit_module -S delete_module -k modules

# === Mount Operations ===
-a always,exit -F arch=b64 -S mount -S umount2 -k mount

# === Network Configuration Changes ===
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k network_modifications
-w /etc/hosts -p wa -k hosts_file
-w /etc/sysconfig/network -p wa -k network_config
-w /etc/resolv.conf -p wa -k dns_config

# === Process and Signal Audit ===
-a always,exit -F arch=b64 -S kill -F a1=9 -k signal_kill9
-a always,exit -F arch=b64 -S ptrace -k ptrace

# === Security-Critical Syscalls ===
-a always,exit -F arch=b64 -S execve -k exec
-a always,exit -F arch=b64 -S open -S openat -F exit=-EACCES -k access_denied
-a always,exit -F arch=b64 -S open -S openat -F exit=-EPERM -k access_denied

# === Make rules immutable (uncomment in production) ===
# -e 2
EOF

augenrules --load
auditctl -l     # List active rules
auditctl -s     # Show status

# Search audit log
ausearch -k identity -ts today
ausearch -m SYSCALL -c sudo -ts recent
ausearch -ua root -ts today  # All actions by UID 0
ausearch -m LOGIN -ts today  # Login events

# Generate report
aureport --summary
aureport -au    # Authentication events
aureport -x --summary  # Executable events
```

### 14.2 Structured Audit to Centralized SIEM

```bash
# Ship audit logs to Elasticsearch via Filebeat
cat > /etc/filebeat/filebeat.yml << 'EOF'
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/audit/audit.log
  json.keys_under_root: false
  fields:
    log_type: auditd
    host: ${HOSTNAME}

processors:
- add_host_metadata: {}
- decode_json_fields:
    fields: ["message"]
    target: "audit"

output.elasticsearch:
  hosts: ["https://es-cluster:9200"]
  ssl:
    certificate_authorities: ["/etc/filebeat/certs/ca.pem"]
    certificate: "/etc/filebeat/certs/filebeat.pem"
    key: "/etc/filebeat/certs/filebeat-key.pem"
  username: "filebeat-user"
  password: "${ELASTICSEARCH_PASSWORD}"
  index: "audit-logs-%{+yyyy.MM.dd}"
EOF

# CloudWatch agent for AWS (ship to CloudWatch Logs + CloudTrail)
# CloudTrail: records all AWS API calls (IAM changes, etc.)
aws cloudtrail create-trail \
  --name org-trail \
  --s3-bucket-name audit-logs-bucket \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --include-global-service-events \
  --cloud-watch-logs-log-group-arn arn:aws:logs:us-east-1:123:log-group:CloudTrail \
  --cloud-watch-logs-role-arn arn:aws:iam::123:role/CloudTrail-CWLogs

aws cloudtrail start-logging --name org-trail
```

---

## 15. Compliance Frameworks: SOC2, PCI-DSS, FedRAMP, ISO 27001

### 15.1 SOC 2 (Type I / Type II)

SOC 2 is an AICPA standard based on **Trust Service Criteria (TSC)**:

```
+------------------+--------------------------------------------------+
| TSC Category     | Key Controls                                     |
+------------------+--------------------------------------------------+
| CC1: Control     | Risk assessment, COSO framework, tone at top    |
| Environment      |                                                  |
+------------------+--------------------------------------------------+
| CC2: Communication| Policies, procedures, training, awareness       |
| & Information    |                                                  |
+------------------+--------------------------------------------------+
| CC3: Risk        | Risk identification, analysis, response         |
| Assessment       |                                                  |
+------------------+--------------------------------------------------+
| CC4: Monitoring  | Performance monitoring, deficiency identification|
+------------------+--------------------------------------------------+
| CC5: Control     | Selection and development of controls           |
| Activities       |                                                  |
+------------------+--------------------------------------------------+
| CC6: Logical     | Logical access controls, auth, least privilege   |
| Access Controls  | MFA, access reviews, termination process         |
+------------------+--------------------------------------------------+
| CC7: System Ops  | Detection of threats, change management          |
+------------------+--------------------------------------------------+
| CC8: Change Mgmt | SDLC, change authorization, testing              |
+------------------+--------------------------------------------------+
| CC9: Risk        | Vendor risk management, business continuity      |
| Mitigation       |                                                  |
+------------------+--------------------------------------------------+
| A1: Availability | Backups, disaster recovery, SLA monitoring       |
+------------------+--------------------------------------------------+
| C1: Confidentiality| Data classification, encryption, DLP           |
+------------------+--------------------------------------------------+
| PI1: Processing  | Complete, accurate, timely processing            |
| Integrity        |                                                  |
+------------------+--------------------------------------------------+
| P1-P8: Privacy   | Personal data collection, use, retention, disposal|
+------------------+--------------------------------------------------+
```

**IAM-specific SOC2 requirements**:
- **CC6.1**: Logical access security (passwords, MFA, unique IDs)
- **CC6.2**: New access requests go through formal approval
- **CC6.3**: Restricted access to sensitive data (PoLP)
- **CC6.6**: Transmission encryption (TLS 1.2+)
- **CC6.7**: Change/transfer/disposal of data secured
- **CC7.2**: Monitor for anomalous behavior

**Evidence collection**:
```bash
# Access review evidence: list all users and their roles
aws iam get-account-authorization-details --output json > iam-report.json

# Unused credentials (SOC2 CC6.3 - terminate unused access)
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | \
  base64 -d | \
  awk -F',' '$11 > 90 {print $1, "last_used:", $11, "days_ago"}' # Keys unused >90 days

# MFA compliance check
aws iam list-users --query 'Users[*].UserName' --output text | \
  xargs -I {} sh -c 'echo -n "{}: "; aws iam list-mfa-devices --user-name {} --query "length(MFADevices)"'

# Password policy
aws iam get-account-password-policy
```

### 15.2 PCI-DSS v4.0

PCI-DSS applies to any system that stores, processes, or transmits **cardholder data (CHD)**.

```
PCI-DSS v4.0 Requirements relevant to IAM:

Req 7: Restrict access to system components and CHD by need to know
  7.1.1: Access control policies
  7.2.1: All access based on job function (RBAC)
  7.2.4: User account reviews (quarterly for privileged, semi-annual for others)
  7.2.5: All accounts and access rights assigned appropriately
  7.3.1: Access control system in place (technical enforcement)

Req 8: Identify users and authenticate access
  8.2.1: Unique IDs for all users (no shared accounts)
  8.2.2: Group/shared accounts only for exceptions with compensating controls
  8.3.6: Password min length 12 chars (or 8 if MFA deployed)
  8.3.9: Passwords expire at least every 90 days (or change if compromise)
  8.3.10: Change at first use
  8.4.2: MFA for all access to CDE
  8.4.3: MFA for all remote network access
  8.5.1: MFA not susceptible to replay attacks
  8.6.1: Interactive logins for application/system accounts documented
  8.6.2: No hardcoded passwords in scripts/source code

Req 10: Log and monitor all access
  10.2.1: Audit logs for: user access to CHD, root/admin actions,
          access to audit trails, invalid auth, privilege use,
          initialization/stop/pause of audit logs, object creation/deletion
  10.3.2: Audit logs protected from destruction/modification
  10.3.3: Audit logs backed up promptly (centralized)
  10.5.1: Retain audit logs at least 12 months, 3 months immediately available
  10.7.1: Failures of critical controls detected and responded to
```

```bash
# PCI-DSS requirement checks (automation examples):

# 8.2.1: No shared accounts (find accounts used by multiple people)
# Should be enforced by process — check for generic names
grep -E "^(test|shared|service|generic|default):" /etc/passwd

# 8.3.6: Password minimum length via PAM
grep "minlen" /etc/security/pwquality.conf

# 8.4.2: MFA enforcement (check SSH config)
grep "AuthenticationMethods" /etc/ssh/sshd_config
# Should be: AuthenticationMethods publickey,keyboard-interactive

# 8.6.2: No hardcoded passwords in code (scan)
# Use truffleHog, git-secrets, or semgrep
trufflehog git file://. --only-verified --json 2>/dev/null | jq .

# 10.5.1: Log retention policy
# Check rsyslog/filebeat shipping config for retention rules
```

### 15.3 FedRAMP

FedRAMP uses **NIST SP 800-53** controls. Three impact levels: Low, Moderate, High.

```
NIST 800-53 Control Families for IAM:

AC - Access Control (27 controls)
  AC-2:  Account Management
  AC-3:  Access Enforcement
  AC-4:  Information Flow Enforcement
  AC-5:  Separation of Duties
  AC-6:  Least Privilege
  AC-7:  Unsuccessful Login Attempts (lockout)
  AC-11: Session Lock
  AC-12: Session Termination
  AC-17: Remote Access
  AC-19: Access Control for Mobile Devices

IA - Identification and Authentication (12 controls)
  IA-2:  Identification and Authentication (Multi-Factor for High)
  IA-3:  Device Identification and Authentication
  IA-4:  Identifier Management (reuse prohibition)
  IA-5:  Authenticator Management (password policies)
  IA-6:  Authentication Feedback (obscure password during entry)
  IA-7:  Cryptographic Module Authentication
  IA-8:  Non-Organizational Users (partners, contractors)

AU - Audit and Accountability (16 controls)
  AU-2:  Event Logging
  AU-3:  Content of Audit Records (user, time, type, result)
  AU-6:  Audit Record Review, Analysis, Reporting
  AU-9:  Protection of Audit Information
  AU-10: Non-repudiation
  AU-11: Audit Record Retention (3 years for High)
  AU-12: Audit Record Generation
```

### 15.4 ISO 27001:2022

ISO 27001 is an information security management system (ISMS) standard.

```
ISO 27001:2022 Annex A controls for IAM:

A.5: Organizational Controls
  5.15: Access control policy
  5.16: Identity management
  5.17: Authentication information (passwords)
  5.18: Access rights (provisioning, review, deprovisioning)
  5.19-5.22: Supplier security

A.8: Technological Controls
  8.2:  Privileged access rights
  8.3:  Information access restriction
  8.4:  Access to source code
  8.5:  Secure authentication (MFA, FIDO2)
  8.6:  Capacity management
  8.15: Logging (content requirements)
  8.16: Monitoring activities
  8.17: Clock synchronization
  8.18: Use of privileged utility programs
  8.20: Networks security
  8.21: Security of network services
  8.22: Segregation in networks
```

---

## 16. Compliance-as-Code Automation

### 16.1 InSpec / Chef for Compliance Checks

```ruby
# controls/iam_hardening.rb
# InSpec compliance profile for Linux IAM

title "IAM Hardening Baseline"

# CIS Benchmark: 5.1.1 - Ensure cron daemon is enabled
control "cis-5-1-1" do
  impact 1.0
  title "Ensure cron daemon is enabled"
  
  describe service("cron") do
    it { should be_enabled }
    it { should be_running }
  end
end

# PCI-DSS 8.3.6: Password minimum length
control "pci-8-3-6-password-length" do
  impact 1.0
  title "PCI-DSS 8.3.6: Passwords must be at least 12 characters"
  tag "pci-dss": "8.3.6"
  
  describe parse_config_file("/etc/security/pwquality.conf") do
    its("minlen") { should cmp >= 12 }
  end
end

# SOC2 CC6.1: MFA for SSH
control "soc2-cc6-1-ssh-mfa" do
  impact 1.0
  title "SOC2 CC6.1: SSH must require MFA"
  tag "soc2": "CC6.1"
  
  describe sshd_config do
    its("AuthenticationMethods") { should match /publickey,keyboard-interactive|publickey,pam/ }
    its("PasswordAuthentication") { should eq "no" }
    its("PermitRootLogin") { should eq "no" }
    its("PermitEmptyPasswords") { should eq "no" }
  end
end

# NIST AC-6: Least Privilege - No world-writable files in /etc
control "nist-ac-6-world-writable" do
  impact 1.0
  title "No world-writable files in /etc"
  tag "nist-800-53": "AC-6"
  
  command("find /etc -type f -perm -0002 2>/dev/null").stdout.strip.split("\n").each do |path|
    describe file(path) do
      it { should_not be_writable.by("others") }
    end
  end
end

# NIST AU-9: Audit log protection
control "nist-au-9-audit-log-permissions" do
  impact 1.0
  title "Audit logs must not be world-readable or world-writable"
  tag "nist-800-53": "AU-9"
  
  describe file("/var/log/audit/audit.log") do
    it { should exist }
    it { should_not be_readable.by("others") }
    it { should_not be_writable.by("others") }
    its("owner") { should eq "root" }
    its("group") { should eq "root" }
  end
end

# FedRAMP IA-5: Password aging
control "fedramp-ia-5-password-aging" do
  impact 0.7
  title "FedRAMP IA-5: Maximum password age must not exceed 60 days"
  tag "fedramp": "IA-5"
  
  shadow.users.each do |user|
    next if shadow.max_days(user) == -1  # No expiry = service account pattern, verify separately
    describe shadow.users(user) do
      its("max_days") { should cmp <= 60 }
    end
  end
end
```

### 16.2 OPA/Conftest for Terraform/K8s Policy

```bash
# conftest: use OPA to validate Terraform plans and K8s manifests
cat > policy/terraform.rego << 'EOF'
package terraform

# Deny S3 buckets without encryption
deny contains msg if {
    resource := input.resource_changes[_]
    resource.type == "aws_s3_bucket"
    not resource.change.after.server_side_encryption_configuration
    msg := sprintf("S3 bucket '%v' must have encryption enabled", [resource.name])
}

# Deny public S3 buckets
deny contains msg if {
    resource := input.resource_changes[_]
    resource.type == "aws_s3_bucket_public_access_block"
    resource.change.after.block_public_acls == false
    msg := sprintf("S3 bucket '%v' must block public ACLs", [resource.name])
}

# Deny IAM policies with wildcard actions
deny contains msg if {
    resource := input.resource_changes[_]
    resource.type == "aws_iam_policy"
    policy := json.unmarshal(resource.change.after.policy)
    statement := policy.Statement[_]
    statement.Effect == "Allow"
    statement.Action == "*"
    msg := sprintf("IAM policy '%v' must not use wildcard actions", [resource.name])
}
EOF

# Validate Terraform plan
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > tfplan.json
conftest test tfplan.json --policy policy/

# Validate Kubernetes manifests
conftest test deployment.yaml --policy k8s-policy/
```

### 16.3 Automated Compliance Pipeline

```yaml
# .github/workflows/compliance.yaml
name: Compliance Checks

on:
  push:
    branches: [main]
  pull_request:

jobs:
  static-analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Secret scanning (truffleHog)
      uses: trufflesecurity/trufflehog@main
      with:
        path: ./
        only-verified: true

    - name: SAST (semgrep)
      uses: semgrep/semgrep-action@v1
      with:
        config: >-
          p/security-audit
          p/secrets
          p/owasp-top-ten
          p/golang
          p/rust

    - name: OPA policy tests
      run: |
        opa test policies/ -v --coverage

    - name: Conftest Terraform
      run: |
        terraform init
        terraform plan -out=tfplan.binary
        terraform show -json tfplan.binary > tfplan.json
        conftest test tfplan.json --policy policy/

  infrastructure-compliance:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: InSpec CIS benchmark
      run: |
        cinc-auditor exec compliance/profiles/cis-linux \
          --target ssh://host \
          --reporter json:reports/inspec-report.json cli

    - name: Prowler AWS security check
      run: |
        prowler aws \
          --compliance cis_level2_aws \
          --output-formats json \
          --output-filename prowler-report \
          --no-banner

    - name: Upload compliance reports
      uses: actions/upload-artifact@v4
      with:
        name: compliance-reports
        path: reports/
        retention-days: 365  # 1 year retention for audit
```

---

## 17. Threat Model: Full Stack IAM

### 17.1 STRIDE Analysis

```
+---------------+-----------------------------------------------+-----------------------------------+
| Threat        | Vector                                        | Mitigation                        |
+---------------+-----------------------------------------------+-----------------------------------+
| Spoofing      | Token theft (JWT in logs/env vars)            | Short TTL, HTTPS-only, no logging |
|               | MITM on JWKS endpoint                         | TLS 1.3, cert pinning             |
|               | Account takeover via password spray           | MFA, lockout, anomaly detection   |
|               | Service account credential theft             | SPIFFE/SPIRE, IRSA, no static keys|
|               | DNS hijacking of IdP endpoint                 | DNSSEC, static trust bundles      |
+---------------+-----------------------------------------------+-----------------------------------+
| Tampering     | Policy store modification (bypass authz)      | Signed policies, OPA bundles      |
|               | Audit log tampering                           | HMAC chains, WORM storage         |
|               | Config drift (setuid added to binary)         | IMA/EVM, file integrity monitoring|
|               | Token forgery (weak JWT key)                  | RS256+/ES256+, key rotation       |
+---------------+-----------------------------------------------+-----------------------------------+
| Repudiation   | Actor denies performing action                | Signed audit events, non-repudiab.|
|               | Shared accounts (no individual attribution)   | Individual accounts, no sharing   |
|               | Log deletion                                  | Centralized, append-only logging  |
+---------------+-----------------------------------------------+-----------------------------------+
| Information   | Excessive permissions (over-privileged role)  | PoLP, IAM Access Analyzer         |
| Disclosure    | JWT claims expose sensitive data              | Encrypt sensitive claims           |
|               | Error messages reveal IAM structure           | Generic error messages externally |
|               | Container breakout reads host secrets         | Seccomp, AppArmor, no CAP_SYS_ADMIN|
+---------------+-----------------------------------------------+-----------------------------------+
| Denial of     | OPA policy eval DDoS                          | Rate limiting, caching, sidecars  |
| Service       | JWKS endpoint unavailability                  | JWKS caching with stale fallback  |
|               | Vault seal causes auth outage                 | Auto-unseal, HA cluster           |
|               | etcd unavailability (k8s RBAC)               | etcd HA, backup restore           |
+---------------+-----------------------------------------------+-----------------------------------+
| Elevation of  | Sudo misconfiguration (shell escape)          | NOEXEC, restricted Cmnd           |
| Privilege     | SUID binary exploitation                      | Minimize SUID, capabilities       |
|               | Namespace escape (user NS + kernel vuln)      | Seccomp, no CAP_SYS_ADMIN, patches|
|               | IAM role chaining (A assumes B assumes C)     | Max session chain depth limits    |
|               | RBAC wildcard (verbs: ["*"])                  | Explicit verb listing, OPA check  |
|               | JWT algorithm confusion (RS256 -> HS256)      | Enforce algorithm in validation   |
|               | SSRF to IMDSv1 (cloud metadata theft)         | IMDSv2 only, block SSRF paths     |
+---------------+-----------------------------------------------+-----------------------------------+
```

### 17.2 Attack Trees

```
Goal: Gain unauthorized access to production database

+-- 1. Compromise cloud IAM
|   +-- 1.1. Steal AWS access key from code/env
|   |   +-- 1.1.1. Scan public Git repos (truffleHog, GitLeaks)
|   |   +-- 1.1.2. Read CloudFormation template with hardcoded keys
|   |   Mitigations: Secret scanning in CI, SOPS, no static keys
|   |
|   +-- 1.2. OIDC token hijack (GitHub Actions)
|   |   +-- 1.2.1. Fork repo and trigger workflow
|   |   Mitigations: sub claim validation, branch restrictions
|   |
|   +-- 1.3. Metadata service SSRF (IMDSv1)
|       +-- 1.3.1. SSRF in app -> GET http://169.254.169.254/...
|       Mitigations: IMDSv2 hop limit=1, block 169.254.x.x at egress

+-- 2. Compromise workload identity
|   +-- 2.1. Steal projected SA token from pod filesystem
|   |   Mitigations: Short TTL, audience-bound, no volume mounts
|   |
|   +-- 2.2. Exploit OPA webhook to bypass admission
|       Mitigations: failurePolicy:Fail, HA webhook, TLS validation

+-- 3. Lateral movement via RBAC misconfiguration
|   +-- 3.1. Verb escalation (create role, bind to self)
|   |   +-- 3.1.1. Requires: verbs:[create] on roles + rolebindings
|   |   Mitigations: No self-escalating permissions, audit RBAC rules
|   |
|   +-- 3.2. Namespace escape via cluster-admin binding
|       Mitigations: No cluster-admin for workloads, PSA restricted

+-- 4. Social engineering / insider threat
    +-- 4.1. Privileged user compromised
    |   Mitigations: JIT access, PIM, break-glass audit trails
    |
    +-- 4.2. SoD bypass
        Mitigations: Technical enforcement, peer approval for privileged actions
```

### 17.3 Supply Chain Threats

```
Software supply chain attacks targeting IAM:

1. Dependency confusion: malicious package shadows internal one
   -> Use private registries, checksum verification, Sigstore/cosign

2. CI/CD pipeline injection: malicious PR modifies pipeline
   -> Branch protection, separate pipeline permissions, OIDC scope per branch

3. Container image tampering: replace image between build and deploy
   -> Image signing (cosign), digest pinning, admission webhook verify signatures

4. Compromised base image: vulnerable OS packages with CVEs
   -> Distroless, minimal base, Trivy/Grype scanning, SBOMs

5. Malicious OPA policy bundle: attacker modifies bundle to always allow
   -> Signed bundles (OPA bundle signing), integrity verification on load
```

---

## 18. Testing, Fuzzing, and Benchmarking

### 18.1 Go IAM Engine Tests

```go
// pkg/iam/engine_test.go
package iam_test

import (
    "context"
    "testing"
    "time"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestAuthorize_ExplicitDenyWins(t *testing.T) {
    engine, _ := setupTestEngine(t)
    ctx := context.Background()
    
    req := &AuthorizationRequest{
        Principal: &Principal{
            ID:    "alice",
            Type:  PrincipalUser,
            Roles: []string{"admin"},  // Admin role
            MFAVerified: true,
        },
        Action:   "s3:DeleteObject",
        Resource: "arn:aws:s3:::prod-bucket/critical.json",
        RequestID: "test-001",
    }
    
    decision, err := engine.Authorize(ctx, req)
    require.NoError(t, err)
    assert.False(t, decision.Allowed, "explicit deny must override allow")
}

func TestAuthorize_ImplicitDenyDefault(t *testing.T) {
    engine, _ := setupTestEngine(t)
    ctx := context.Background()
    
    req := &AuthorizationRequest{
        Principal: &Principal{
            ID:   "anonymous",
            Type: PrincipalUser,
        },
        Action:    "s3:GetObject",
        Resource:  "arn:aws:s3:::any-bucket/any-key",
        RequestID: "test-002",
    }
    
    decision, err := engine.Authorize(ctx, req)
    require.NoError(t, err)
    assert.False(t, decision.Allowed, "no matching policy = implicit deny")
}

func TestAuthorize_JWTAlgorithmConfusion(t *testing.T) {
    // CRITICAL: HS256 with RS256 public key as secret
    // A validator that doesn't enforce algorithm type is vulnerable
    
    validator := NewJWTValidator(
        "https://auth.example.com/.well-known/jwks.json",
        "https://auth.example.com",
        "api-service",
    )
    
    // Craft HS256 token using the public key as HMAC secret
    // (algorithm confusion attack)
    maliciousToken := craftAlgorithmConfusionToken()
    
    _, err := validator.Validate(context.Background(), maliciousToken)
    assert.Error(t, err, "must reject algorithm confusion attack")
}

func BenchmarkAuthorize(b *testing.B) {
    engine, _ := setupTestEngine(b)
    ctx := context.Background()
    
    req := &AuthorizationRequest{
        Principal: &Principal{
            ID:    "alice",
            Type:  PrincipalUser,
            Roles: []string{"developer"},
            MFAVerified: true,
        },
        Action:    "s3:GetObject",
        Resource:  "arn:aws:s3:::prod-bucket/data/file.json",
        RequestID: "bench-001",
    }
    
    b.ResetTimer()
    b.ReportAllocs()
    
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            _, err := engine.Authorize(ctx, req)
            if err != nil {
                b.Fatal(err)
            }
        }
    })
}

// Target: <1ms p99 for authorization decision
// Expected: ~100-500µs with OPA (cached query), <50µs for native Go eval
```

### 18.2 Rust Fuzzing

```rust
// fuzz/fuzz_targets/fuzz_jwt.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

// cargo fuzz run fuzz_jwt -- -max_total_time=3600
fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        let rt = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .unwrap();
        
        rt.block_on(async {
            let validator = create_test_validator();
            // Must not panic on any input
            let _ = validator.validate(s).await;
        });
    }
});

// fuzz/fuzz_targets/fuzz_policy.rs
fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        // Must not panic on any policy input
        if let Ok(policy) = serde_json::from_str::<Policy>(s) {
            let engine = PolicyEngine::new(vec![policy]);
            let ctx = make_fuzz_ctx();
            let _ = engine.evaluate(&ctx);
        }
    }
});
```

```bash
# Run fuzzing
cargo fuzz run fuzz_jwt -- -max_total_time=3600 -jobs=8
cargo fuzz run fuzz_policy -- -max_total_time=3600

# Go fuzzing (built-in since 1.18)
cat > pkg/iam/glob_fuzz_test.go << 'EOF'
package iam

import "testing"

func FuzzGlobMatch(f *testing.F) {
    // Seed corpus
    f.Add("s3:*", "s3:GetObject")
    f.Add("s3://bucket/*", "s3://bucket/key")
    f.Add("*", "anything")
    
    f.Fuzz(func(t *testing.T, pattern, value string) {
        engine := &PolicyEngine{}
        // Must not panic
        _ = engine.globMatch(pattern, value)
    })
}
EOF
go test -fuzz=FuzzGlobMatch ./pkg/iam/ -fuzztime=60s
```

### 18.3 Security Testing

```bash
# Test IAM policy evaluation correctness
cat > tests/iam_scenarios.json << 'EOF'
[
  {
    "name": "admin_can_delete",
    "input": {"user": "alice", "roles": ["admin"], "action": "delete", "resource": "db:prod"},
    "expected": true
  },
  {
    "name": "viewer_cannot_delete",
    "input": {"user": "bob", "roles": ["viewer"], "action": "delete", "resource": "db:prod"},
    "expected": false
  },
  {
    "name": "explicit_deny_overrides",
    "input": {"user": "charlie", "roles": ["admin"], "action": "s3:DeleteBucket", "resource": "s3://prod"},
    "expected": false
  }
]
EOF

# RBAC testing with kube-rbac-proxy
# Test what a specific SA can do
kubectl auth can-i list pods \
  --namespace production \
  --as=system:serviceaccount:production:payment-svc

kubectl auth can-i delete deployments \
  --namespace production \
  --as=system:serviceaccount:production:payment-svc

# rakkess: show all permissions for a user
kubectl rakkess --sa payment-svc --namespace production

# rbac-tool: visualize Kubernetes RBAC
rbac-tool visualize --include-subjects \
  --file rbac-graph.dot
dot -Tpng rbac-graph.dot -o rbac-graph.png

# Test Vault policies
vault token create -policy="payment-svc-policy" -ttl=1h
VAULT_TOKEN=<new-token> vault read database/creds/payment-svc
VAULT_TOKEN=<new-token> vault read database/creds/other-db  # Should fail

# AWS policy simulator
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123:role/payment-svc \
  --action-names s3:GetObject s3:DeleteObject \
  --resource-arns arn:aws:s3:::prod-bucket/data/file.json \
  --output json | jq '.EvaluationResults[] | {Action: .EvalActionName, Decision: .EvalDecision}'
```

---

## 19. Roll-out and Rollback Strategies

### 19.1 IAM Migration Strategy

```
Phase 0: Audit current state (no changes)
  - Document all existing roles, permissions, service accounts
  - Run IAM Access Analyzer, generate credential report
  - Map actual usage vs. granted permissions
  - Identify orphaned accounts, stale credentials, over-privileged roles

Phase 1: Non-breaking additions (shadow mode)
  - Deploy new IAM engine in AUDIT-ONLY mode (logs decisions, does not enforce)
  - Compare new policy decisions vs. current behavior
  - Run for 2-4 weeks, tune policies to eliminate false positives

Phase 2: Enforce for new services
  - All new services MUST use SPIFFE/SPIRE + new RBAC from day 1
  - Legacy services continue with old method

Phase 3: Gradual migration (canary)
  - Enable enforcement for 1% of traffic to one legacy service
  - Monitor: 4xx rates, authorization failures, business metrics
  - Roll back trigger: >0.1% unexpected denials

Phase 4: Bulk migration
  - Migrate services namespace by namespace
  - Each migration: shadow mode -> 1% -> 10% -> 100%

Phase 5: Deprecate old method
  - Revoke old service account credentials
  - Remove legacy auth paths
```

### 19.2 Rollback Procedures

```bash
# Kubernetes RBAC rollback
# Always keep RBAC changes in Git, use GitOps

# Rollback admission webhook (if causing admission failures)
# Emergency: disable webhook (only for break-glass)
kubectl delete validatingwebhookconfiguration pod-security-policy

# Or temporarily switch failurePolicy to Ignore (NOT recommended long-term)
kubectl patch validatingwebhookconfiguration pod-security-policy \
  --type=json \
  -p='[{"op":"replace","path":"/webhooks/0/failurePolicy","value":"Ignore"}]'

# OPA policy rollback
# OPA bundles are versioned — roll back by updating bundle tag
# In production, use OPA bundle signing to prevent unauthorized policy changes

# Vault PKI rollback
# Certificate issues: revoke specific cert
vault write pki/revoke serial_number=<serial>

# CRL is automatically updated and served to clients
vault write pki/config/urls \
    crl_distribution_points="https://vault.internal:8200/v1/pki/crl"

# AWS IAM: break-glass emergency access
# Pre-provision break-glass role with very limited, audited access
# Documented, requires MFA + manual CW Logs alert on assumption

# Deny all external access (incident response)
aws ec2 revoke-security-group-ingress \
  --group-id sg-emergency \
  --protocol all \
  --cidr 0.0.0.0/0

# Feature flags for IAM policy changes
# Use LaunchDarkly or similar to gate new policy enforcement
# Allows instant kill-switch without deployment
```

### 19.3 Monitoring and Alerting

```yaml
# Prometheus alerting rules for IAM
groups:
- name: iam.rules
  rules:
  # High rate of authorization failures
  - alert: HighAuthorizationFailureRate
    expr: |
      rate(iam_authorization_decisions_total{allowed="false"}[5m]) /
      rate(iam_authorization_decisions_total[5m]) > 0.05
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "IAM authorization failure rate > 5%"
      
  # OPA policy evaluation latency
  - alert: OPAEvalLatencyHigh
    expr: histogram_quantile(0.99, rate(opa_eval_duration_seconds_bucket[5m])) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "OPA policy evaluation p99 > 100ms"

  # Vault token renewal failures
  - alert: VaultTokenRenewalFailing
    expr: rate(vault_token_renewal_failures_total[5m]) > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Vault token renewal is failing"

  # AWS root account usage (always alert)
  - alert: AWSRootAccountUsed
    expr: aws_cloudtrail_root_account_usage_total > 0
    labels:
      severity: critical
    annotations:
      summary: "AWS root account was used"
```

---

## 20. Next 3 Steps

1. **Implement SPIFFE/SPIRE workload identity** in your Kubernetes cluster as the foundation for zero-trust service-to-service auth: deploy SPIRE server (HA with Postgres backend), SPIRE agents as DaemonSet, register entries for all workloads, migrate one service from static SA token to SVID-based mTLS, and validate certificate rotation works end-to-end.

2. **Deploy OPA as centralized policy engine** with signed bundle distribution: write comprehensive Rego policies covering RBAC, K8s admission, and Terraform compliance, integrate with your API gateway and admission webhooks, enable decision logging to your SIEM, and run `opa test` in CI to prevent policy regressions.

3. **Conduct a full IAM access review and least-privilege remediation**: run `aws iam generate-credential-report` + GCP IAM Recommender + Azure Access Reviews, identify all over-privileged roles and stale credentials, migrate to ABAC/tag-based policies where appropriate, enforce SCPs (AWS) / Organization Policies (GCP) to create hard guardrails, and establish quarterly access review process with automated evidence collection for SOC2/PCI-DSS.

---

## 21. References

### Standards and Frameworks
- NIST SP 800-53 Rev 5: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- NIST SP 800-63-3 (Digital Identity Guidelines): https://pages.nist.gov/800-63-3/
- OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks/
- PCI-DSS v4.0: https://www.pcisecuritystandards.org/document_library/
- NIST RBAC Model (INCITS 359-2004)
- Google Zanzibar Paper: https://research.google/pubs/pub48190/

### Linux Security
- Linux Capabilities: https://man7.org/linux/man-pages/man7/capabilities.7.html
- Linux Namespaces: https://man7.org/linux/man-pages/man7/namespaces.7.html
- SELinux Project: https://selinuxproject.org/
- AppArmor Wiki: https://gitlab.com/apparmor/apparmor/-/wikis/home
- Kernel LSM: https://www.kernel.org/doc/html/latest/security/lsm.html
- auditd: https://linux.die.net/man/8/auditd

### Cloud IAM
- AWS IAM Best Practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- GCP IAM: https://cloud.google.com/iam/docs/overview
- Azure RBAC: https://learn.microsoft.com/en-us/azure/role-based-access-control/
- AWS IAM Access Analyzer: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html

### SPIFFE/SPIRE
- SPIFFE Specification: https://github.com/spiffe/spiffe/tree/main/standards
- SPIRE Documentation: https://spiffe.io/docs/latest/spire-about/
- go-spiffe: https://github.com/spiffe/go-spiffe

### Policy Engines
- OPA Documentation: https://www.openpolicyagent.org/docs/latest/
- Cedar Language: https://www.cedarpolicy.com/
- OpenFGA: https://openfga.dev/

### Secrets Management
- Vault Architecture: https://developer.hashicorp.com/vault/docs/internals/architecture
- SOPS: https://github.com/getsops/sops

### Kubernetes Security
- Pod Security Standards: https://kubernetes.io/docs/concepts/security/pod-security-standards/
- Kubernetes RBAC: https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- Admission Controllers: https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/

### Tools
- Prowler (AWS/GCP/Azure security): https://github.com/prowler-cloud/prowler
- InSpec: https://community.chef.io/tools/chef-inspec
- rbac-tool: https://github.com/alcideio/rbac-tool
- Trufflehog: https://github.com/trufflesecurity/trufflehog
- Semgrep: https://semgrep.dev/
- Falco (runtime security): https://falco.org/
- Trivy (container scanning): https://trivy.dev/

Now let me build this comprehensive guide. This will be a large, deeply technical document.**5,358 lines / ~172KB** of dense, production-grade material. Here's what's covered end-to-end:

**Linux (kernel to userspace):** DAC/POSIX ACLs with exact kernel check paths, Linux capabilities (all 41, with inheritance rules and `cap_effective`/`cap_permitted`/`cap_bounding` semantics), user/pid/net/mnt/cgroup namespaces with concrete `ip netns` / `unshare` examples, cgroups v2 hierarchy and OOM tuning, seccomp BPF filter design with the full Docker-default rationale, PAM module chain (`auth` → `account` → `password` → `session`) with `pam_faillock`, `pam_pwquality`, `pam_tty_audit`, and SSSD/Kerberos config.

**LSMs:** SELinux type enforcement from `task_struct.cred` through AVC to policy modules — full `.te`/`.fc`/`.if` module authoring workflow, MCS container labeling, AppArmor path-based profiles with `aa-genprof` learning flow.

**Cloud IAM:** AWS policy evaluation order (SCP → resource-based → identity-based → permission boundary → session policy), ABAC tag-match patterns, STS assume-role trust policies, OIDC federation for GitHub Actions. GCP resource hierarchy with conditional IAM bindings and Workload Identity Federation. Azure RBAC with managed identities and PIM JIT access.

**Implementations:** Go IAM engine with OPA integration, JWKS caching client with timing-safe comparison, HMAC-chained audit logger. Rust JWT validator (rustls, algorithm confusion prevention, `libfuzzer` fuzz targets) and policy engine with glob matching, SoD enforcement, full test suite.

**SPIFFE/SPIRE**, **OPA/Rego** (k8s admission + RBAC), **Cedar**, **Vault** (Raft HA, auto-unseal, PKI, dynamic DB creds), **SOPS**, **auditd** rules for SOC2/PCI, compliance-as-code with InSpec profiles mapped to specific control IDs (CC6.1, PCI 8.3.6, NIST AC-6, FedRAMP IA-5).

**Threat model:** Full STRIDE table with attack trees targeting cloud IAM, workload identity, RBAC escalation, supply chain, and JWT algorithm confusion.