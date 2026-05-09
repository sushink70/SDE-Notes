# SSH Hardening

SSH (Secure Shell) is a **cryptographic network protocol** used to securely access and manage remote systems over an unsecured network. It replaced older, plaintext protocols like Telnet and rlogin.

**SSH Hardening** means configuring and securing your SSH server to reduce its attack surface — making it significantly harder for attackers to gain unauthorized access.

---

## Why SSH is a Target

SSH is almost always exposed to the internet (port 22 by default). This makes it one of the most brute-forced services in the world. Every minute, bots are scanning the internet attempting logins.

```
Internet
   │
   ▼
[Port 22 Open]  ◄──── Bots constantly hammering this
   │
   ▼
SSH Daemon (sshd)
   │
   ▼
Your Server
```

---

## Core SSH Hardening Techniques

### 1. Change the Default Port
```
Default: Port 22  →  Change to: Port 2222 (or any high port)
```
This is "security through obscurity" — not a real fix alone, but it reduces automated bot noise dramatically.

```bash
# /etc/ssh/sshd_config
Port 2222
```

---

### 2. Disable Root Login
Never allow direct root SSH login.

```
Attack Path WITHOUT this:
  Attacker → SSH → root login → Full system control ✗

Attack Path WITH this:
  Attacker → SSH → must know a valid non-root user → then escalate ✓
```

```bash
PermitRootLogin no
```

---

### 3. Use Key-Based Authentication (Disable Passwords)
Passwords can be brute-forced. **Cryptographic key pairs cannot** (in practical terms).

```
How Key Auth Works:
─────────────────────────────────────────────
  Your Machine          Remote Server
  ┌──────────┐          ┌──────────────────┐
  │ Private  │          │  Public Key       │
  │ Key 🔑   │◄────────►│  (stored here)    │
  └──────────┘          └──────────────────┘
        │
        ▼
  Never leaves your machine.
  Server encrypts a challenge with your public key.
  Only your private key can decrypt it → Authenticated.
─────────────────────────────────────────────
```

```bash
# Disable password auth
PasswordAuthentication no
PubkeyAuthentication yes
```

---

### 4. Use Fail2Ban or Similar
Automatically **ban IPs** that fail login attempts repeatedly.

```
IP attempts login 5 times → FAIL
         │
         ▼
   fail2ban detects this
         │
         ▼
   iptables/firewall BLOCKS that IP
         │
         ▼
   Attacker is locked out for N minutes/hours
```

---

### 5. Restrict Allowed Users/Groups

```bash
# Only allow specific users
AllowUsers alice bob
AllowGroups sshusers
```

This means even if an attacker compromises another account, they cannot SSH in.

---

### 6. Idle Session Timeout

```bash
ClientAliveInterval 300   # ping client every 5 min
ClientAliveCountMax 2     # disconnect after 2 missed pings
```

Kills abandoned/hijacked idle sessions.

---

### 7. Disable Empty Passwords & Weak Options

```bash
PermitEmptyPasswords no
X11Forwarding no           # Disable GUI forwarding (attack surface)
AllowTcpForwarding no      # Unless needed
```

---

### 8. Use Modern Cryptography Only

Old algorithms (MD5, DSA, arcfour) are broken. Force strong ones:

```bash
# Strong Key Exchange Algorithms
KexAlgorithms curve25519-sha256,diffie-hellman-group16-sha512

# Strong Ciphers
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com

# Strong MACs (Message Authentication Codes)
MACs hmac-sha2-512-etm@openssh.com
```

---

### 9. Two-Factor Authentication (2FA)
Even if someone steals your key, they need a second factor (TOTP like Google Authenticator).

```
Login Flow WITH 2FA:
─────────────────────────────────────
  Step 1: Present SSH Key  ✓
  Step 2: Enter TOTP Code  ✓ (changes every 30 seconds)
  Step 3: Access Granted   ✓
─────────────────────────────────────
  Steal key alone?  → Still blocked at Step 2
```

---

### 10. Firewall: Whitelist SSH Access

```bash
# Allow SSH only from YOUR IP
ufw allow from 203.0.113.5 to any port 22

# Or use firewalld / iptables
```

---

## Full Decision Tree: Is Your SSH Hardened?

```
Start
  │
  ├─ Default port 22?
  │     Yes → Change it
  │     No  → ✓
  │
  ├─ Root login allowed?
  │     Yes → Disable it
  │     No  → ✓
  │
  ├─ Password auth enabled?
  │     Yes → Switch to key-based, disable passwords
  │     No  → ✓
  │
  ├─ Fail2Ban running?
  │     No  → Install it
  │     Yes → ✓
  │
  ├─ Idle timeout set?
  │     No  → Set ClientAliveInterval
  │     Yes → ✓
  │
  ├─ Strong ciphers enforced?
  │     No  → Update sshd_config
  │     Yes → ✓
  │
  └─ 2FA enabled?
        No  → Consider adding it
        Yes → ✓ You're well-hardened
```

---

## Quick Summary Table

| Technique | Protection Against |
|---|---|
| Change port | Automated bots |
| Disable root | Direct root takeover |
| Key-based auth | Brute force passwords |
| Fail2Ban | Brute force attacks |
| AllowUsers | Lateral movement |
| Idle timeout | Session hijacking |
| Strong ciphers | Cryptographic attacks |
| 2FA | Stolen key attacks |
| Firewall whitelist | All unauthorized sources |

---

SSH hardening is fundamentally about **reducing attack surface** — every unnecessary feature or weak default you disable removes a potential entry point. The principle is: **deny everything, allow only what is explicitly needed.**