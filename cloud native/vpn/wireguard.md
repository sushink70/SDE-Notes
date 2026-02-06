# WireGuard: Comprehensive Security-First Deep Dive

WireGuard is a modern, cryptographically sound VPN protocol implementing state-of-the-art authenticated encryption with minimal attack surface (~4,000 LoC vs OpenVPN's ~100,000). It operates at Layer 3, uses noise protocol framework for key exchange, and achieves high performance through kernel-space implementation. Core security: identity = public key, mandatory perfect forward secrecy, resistance to key-compromise impersonation, silent packet drops (no metadata leakage), and cryptokey routing that eliminates traditional VPN complexity. Production deployments show 3–5x throughput vs IPsec with lower CPU overhead.

---

## 1. Core Architecture & Design Philosophy

### First-Principles Design Goals
- **Minimal attack surface**: Entire codebase fits in one audit sitting
- **Cryptographic opinion**: No algorithm negotiation → no downgrade attacks
- **Identity = public key**: No certificates, PKI, or username/password
- **Silence by default**: Invalid packets dropped without response (anti-enumeration)
- **Stateless handshake**: Denial-of-service resistant
- **Roaming transparency**: Endpoint updates automatically on source IP change

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   WireGuard Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           User Space (wg utility)                     │  │
│  │  - Configuration (wg setconf / wg-quick)              │  │
│  │  - Key generation (wg genkey / wg pubkey)             │  │
│  │  - Status queries (wg show)                           │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │ Netlink API (genetic netlink)           │
│  ─────────────────┼──────────────────────────────────────  │
│                   ▼                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Kernel Space (wireguard.ko module)            │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  Cryptokey Routing Table                      │   │  │
│  │  │  PubKey → AllowedIPs mapping                  │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  Noise Protocol State Machine                 │   │  │
│  │  │  - Handshake (IKpsk2)                         │   │  │
│  │  │  - Key derivation (HKDF)                      │   │  │
│  │  │  - Session keys (ChaCha20-Poly1305)           │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  Packet Processing Pipeline                   │   │  │
│  │  │  RX: Decrypt → Route → Forward to IP stack    │   │  │
│  │  │  TX: Route → Encrypt → Send to endpoint       │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  Timer Management                             │   │  │
│  │  │  - Keepalive (if configured)                  │   │  │
│  │  │  - Session expiry (180s idle timeout)         │   │  │
│  │  │  - Rekey (every 2^64-1 packets)               │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │ Network Interface (wg0, wg1...)         │
│  ─────────────────┼──────────────────────────────────────  │
│                   ▼                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Physical Network (UDP transport)               │  │
│  │        Default port: 51820/UDP                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Cryptographic Primitives (Fixed, No Negotiation)

```
┌────────────────────────────────────────────────────────┐
│  Cipher Suite (Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s)  │
├────────────────────────────────────────────────────────┤
│  Key Exchange:      Curve25519                         │
│  AEAD:              ChaCha20-Poly1305                  │
│  Hash:              BLAKE2s                            │
│  KDF:               HKDF                               │
│  MAC:               Poly1305 (via AEAD)                │
│  Optional PSK:      32-byte preshared key              │
└────────────────────────────────────────────────────────┘
```

**Why these choices:**
- **Curve25519**: Fast, constant-time, no secret-dependent branches (timing attack resistant)
- **ChaCha20-Poly1305**: Fast on non-AES-NI hardware, 256-bit security, AEAD (no encrypt-then-MAC)
- **BLAKE2s**: Faster than SHA-2, 128-bit security sufficient for VPN use case
- **No RSA/DSA**: Avoid historical pitfalls (padding oracles, weak random number generation)

---

## 2. Cryptokey Routing: Core Innovation

Traditional VPNs use **routing tables + access control lists**. WireGuard merges these into **cryptokey routing**.

### Concept

```
┌─────────────────────────────────────────────────────────────┐
│                   Cryptokey Routing Table                    │
├──────────────────┬─────────────────┬────────────────────────┤
│ Peer Public Key  │ Allowed IPs     │ Endpoint (optional)    │
├──────────────────┼─────────────────┼────────────────────────┤
│ pubkey_A         │ 10.0.0.2/32     │ 203.0.113.5:51820      │
│ pubkey_B         │ 10.0.0.3/32     │ 198.51.100.10:51820    │
│                  │ 192.168.5.0/24  │                        │
│ pubkey_C         │ 10.0.0.4/32     │ (dynamic)              │
└──────────────────┴─────────────────┴────────────────────────┘

Packet Flow:
1. Outbound packet to 192.168.5.10 arrives at wg0
   → Lookup: 192.168.5.10 matches pubkey_B's 192.168.5.0/24
   → Encrypt with pubkey_B's session key
   → Send to 198.51.100.10:51820

2. Inbound encrypted packet from 203.0.113.5:51820
   → Decrypt (authenticated with pubkey_A)
   → Extract inner IP: 10.0.0.2 → verify in pubkey_A's AllowedIPs
   → If match: forward to kernel IP stack
   → If no match: silently drop (spoofing attempt)
```

**Security properties:**
- **Source authentication**: Packet can only come from peer with matching private key
- **Anti-spoofing**: Inner IP must be in peer's AllowedIPs or packet is dropped
- **Implicit ACL**: AllowedIPs defines both routing and access control
- **No MAC flooding**: Table is static, not learned

### Real-World Example: Hub-and-Spoke

```
        Internet
           │
           ▼
    ┌──────────────┐
    │  Hub (AWS)   │  wg0: 10.0.0.1/24
    │  pubkey_hub  │  
    └──────┬───────┘
           │
    ┌──────┴────────────────────┐
    │                            │
┌───▼────┐                  ┌───▼────┐
│ Spoke1 │                  │ Spoke2 │
│ (GCP)  │                  │ (Azure)│
│ 10.0.0.2│                  │10.0.0.3│
└────────┘                  └────────┘

Hub config:
[Peer]
PublicKey = <spoke1_pubkey>
AllowedIPs = 10.0.0.2/32
Endpoint = <spoke1_public_ip>:51820

[Peer]
PublicKey = <spoke2_pubkey>
AllowedIPs = 10.0.0.3/32
Endpoint = <spoke2_public_ip>:51820

Spoke1 config:
[Peer]
PublicKey = <hub_pubkey>
AllowedIPs = 10.0.0.0/24  # Route entire VPN subnet through hub
Endpoint = <hub_public_ip>:51820
```

---

## 3. Noise Protocol Framework: Handshake Deep Dive

WireGuard uses **Noise_IKpsk2** pattern:
- **I**: Initiator sends its static public key in first message
- **K**: Responder's static public key is known in advance
- **psk2**: Optional preshared key mixed in second message

### Handshake Messages

```
┌─────────────────────────────────────────────────────────────┐
│                    1-RTT Handshake                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Initiator                              Responder            │
│  (knows responder pubkey)               (has privkey)        │
│                                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Generate ephemeral key pair (epriv_i, epub_i)      │    │
│  │ msg1 = initiator_index || sender_index ||          │    │
│  │        epub_i || encrypted(initiator_static_pub,   │    │
│  │                            timestamp,               │    │
│  │                            MAC)                     │    │
│  └────────────────────────────────────────────────────┘    │
│                        │                                     │
│                        ├──── msg1 (148 bytes) ────────────► │
│                        │                                     │
│                        │     ┌──────────────────────────┐  │
│                        │     │ Decrypt msg1             │  │
│                        │     │ Verify MAC               │  │
│                        │     │ Check timestamp freshness│  │
│                        │     │ Generate (epriv_r, epub_r│  │
│                        │     │ Derive session keys      │  │
│                        │     └──────────────────────────┘  │
│                        │                                     │
│                        ◄──── msg2 (92 bytes) ────────────┤ │
│                        │     msg2 = responder_index ||     │
│                        │            receiver_index ||      │
│                        │            epub_r || MAC          │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Verify msg2 MAC                                     │    │
│  │ Derive session keys                                 │    │
│  │ Handshake complete → start data transmission        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                               │
│  ◄──────────── Encrypted Data Packets ──────────────────►  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Derivation (HKDF)

```
Shared secrets computed:
DH1 = ECDH(initiator_static_priv, responder_static_pub)
DH2 = ECDH(initiator_ephemeral_priv, responder_static_pub)
DH3 = ECDH(initiator_static_priv, responder_ephemeral_pub)
DH4 = ECDH(initiator_ephemeral_priv, responder_ephemeral_pub)

Chaining key derivation:
C0 = HASH("Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s")
C1 = KDF(C0, responder_static_pub)
C2 = KDF(C1, DH1)
C3 = KDF(C2, DH2)
C4 = KDF(C3, preshared_key)  # if psk enabled
C5 = KDF(C4, DH3)
C6 = KDF(C5, DH4)

Transport keys:
T_send_i, T_recv_i = KDF(C6, "")  # Initiator keys
T_send_r, T_recv_r = T_recv_i, T_send_i  # Responder keys (swapped)
```

**Security properties:**
- **Perfect forward secrecy**: Ephemeral keys rotated per session
- **Key-compromise impersonation resistance**: Even if responder privkey stolen, attacker can't impersonate initiator
- **Replay protection**: Timestamp in msg1, monotonic counters in data packets
- **Identity hiding**: Initiator static pubkey encrypted in msg1

### Handshake Triggers

```
Handshake initiated when:
1. First packet to peer (no session exists)
2. Session older than 120 seconds + new packet to send
3. Session key used for 2^64-1 packets (never in practice)
4. Manual wg set wg0 peer <pubkey> rekey
```

---

## 4. Data Packet Format & Encryption

### Packet Structure

```
┌──────────────────────────────────────────────────────────┐
│           WireGuard Data Packet (Type 4)                  │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  Outer UDP/IP headers (standard internet routing)         │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Type: 4 (1 byte)                                    │  │
│  │ Reserved: 0x00 0x00 0x00 (3 bytes)                  │  │
│  │ Receiver index (4 bytes)                            │  │
│  │ Counter (8 bytes, little-endian)                    │  │
│  │ ┌────────────────────────────────────────────────┐ │  │
│  │ │ Encrypted payload:                              │ │  │
│  │ │   Inner IP packet (plaintext before encryption) │ │  │
│  │ │   ChaCha20-Poly1305 AEAD:                       │ │  │
│  │ │     Key: session_key                            │ │  │
│  │ │     Nonce: counter                              │ │  │
│  │ │     AAD: (type || reserved || receiver_index || │ │  │
│  │ │           counter)                              │ │  │
│  │ └────────────────────────────────────────────────┘ │  │
│  │ Poly1305 MAC (16 bytes)                            │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
│  Total overhead: 32 bytes (vs 73+ for IPsec ESP)          │
└──────────────────────────────────────────────────────────┘
```

### Encryption Process (Transmit Path)

```c
// Pseudo-code for packet encryption
struct sk_buff *wg_encrypt_packet(struct wg_peer *peer, struct sk_buff *skb) {
    // 1. Select session key (current or previous if within rekey window)
    struct noise_keypair *keypair = peer->keypairs.current;
    
    // 2. Increment counter (atomic, per-keypair)
    u64 counter = atomic64_inc_return(&keypair->sending_counter);
    
    // 3. Check counter limit (rekey at 2^64 - 2^16)
    if (counter >= REJECT_AFTER_MESSAGES) {
        initiate_handshake(peer);
        return NULL;
    }
    
    // 4. Build packet header
    u8 header[16];
    header[0] = 4;  // Type: data
    memset(&header[1], 0, 3);  // Reserved
    *(u32*)&header[4] = cpu_to_le32(keypair->remote_index);
    *(u64*)&header[8] = cpu_to_le64(counter);
    
    // 5. Encrypt with ChaCha20-Poly1305
    chacha20poly1305_encrypt(
        skb->data,               // Output ciphertext
        skb->data,               // Input plaintext (inner IP packet)
        skb->len,                // Plaintext length
        header, 16,              // AAD (authenticated additional data)
        (u8*)&counter,           // Nonce (counter as nonce)
        keypair->sending_key     // 256-bit key
    );
    
    // 6. Prepend header
    skb_push(skb, sizeof(header));
    memcpy(skb->data, header, sizeof(header));
    
    // 7. Update endpoint (source IP learning)
    if (skb_dst(skb))
        update_endpoint_from_skb(peer, skb);
    
    return skb;
}
```

### Decryption Process (Receive Path)

```c
// Pseudo-code for packet decryption
void wg_receive_packet(struct wg_device *wg, struct sk_buff *skb) {
    // 1. Parse header
    if (skb->len < sizeof(struct message_data))
        goto drop;
    
    struct message_data *msg = (struct message_data*)skb->data;
    if (msg->type != 4)
        goto drop;  // Not a data packet
    
    // 2. Lookup peer by receiver_index
    u32 index = le32_to_cpu(msg->receiver_index);
    struct noise_keypair *keypair = lookup_keypair_by_index(wg, index);
    if (!keypair)
        goto drop;  // Silent drop (no peer found)
    
    // 3. Check replay (sliding window, 2048 bits)
    u64 counter = le64_to_cpu(msg->counter);
    if (!check_replay_counter(keypair, counter))
        goto drop;  // Replayed packet
    
    // 4. Decrypt
    skb_pull(skb, sizeof(*msg));
    if (!chacha20poly1305_decrypt(
            skb->data,                   // Output plaintext
            skb->data,                   // Input ciphertext
            skb->len,                    // Ciphertext length
            (u8*)msg, sizeof(*msg) - sizeof(msg->encrypted_data),  // AAD
            (u8*)&counter,               // Nonce
            keypair->receiving_key)) {   // 256-bit key
        goto drop;  // MAC verification failed
    }
    
    // 5. Verify inner IP is in AllowedIPs
    struct iphdr *iph = (struct iphdr*)skb->data;
    if (!wg_allowedips_lookup(&keypair->peer->allowedips, 
                              iph->saddr, AF_INET))
        goto drop;  // IP spoofing attempt
    
    // 6. Update replay window
    update_replay_counter(keypair, counter);
    
    // 7. Update endpoint (roaming)
    update_endpoint_from_skb(keypair->peer, skb);
    
    // 8. Reset idle timer
    keypair->peer->last_receive = ktime_get_coarse_boottime_ns();
    
    // 9. Inject into network stack
    skb->dev = wg->dev;
    netif_rx(skb);
    return;
    
drop:
    kfree_skb(skb);
    // No ICMP, no logs (silent discard)
}
```

---

## 5. Production Deployment Patterns

### Pattern 1: Site-to-Site VPN (Data Center Interconnect)

```
┌────────────────────────────────────────────────────────────┐
│         AWS VPC (10.0.0.0/16)          │   GCP VPC (10.1.0.0/16)
│                                        │
│  ┌──────────────────┐                 │   ┌──────────────────┐
│  │ WireGuard Gateway│                 │   │ WireGuard Gateway│
│  │ (EC2 c7gn.xlarge)│◄────────────────┼───┤ (e2-standard-4)  │
│  │ wg0: 192.168.0.1 │  UDP 51820/udp  │   │ wg0: 192.168.0.2 │
│  └────────┬─────────┘                 │   └────────┬─────────┘
│           │                            │            │
│      ┌────▼─────┐                     │       ┌────▼─────┐
│      │ RT: 10.1.0.0/16                │       │ RT: 10.0.0.0/16
│      │ → wg0                           │       │ → wg0
│      └──────────┘                     │       └──────────┘
│                                        │
│  Private subnets                       │   Private subnets
│  can now route across clouds           │
└────────────────────────────────────────┴──────────────────────┘

AWS Gateway config (/etc/wireguard/wg0.conf):
[Interface]
Address = 192.168.0.1/30
ListenPort = 51820
PrivateKey = <aws_privkey>
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o ens5 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o ens5 -j MASQUERADE

[Peer]
PublicKey = <gcp_pubkey>
AllowedIPs = 192.168.0.2/32, 10.1.0.0/16  # GCP tunnel endpoint + subnet
Endpoint = <gcp_public_ip>:51820
PersistentKeepalive = 25  # NAT traversal
```

**Production hardening:**
```bash
# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.d/99-wireguard.conf

# Disable reverse path filtering on wg interface (allow asymmetric routing)
sysctl -w net.ipv4.conf.wg0.rp_filter=0

# Increase UDP buffer sizes (high throughput)
sysctl -w net.core.rmem_max=26214400
sysctl -w net.core.wmem_max=26214400

# Enable ECN (explicit congestion notification)
sysctl -w net.ipv4.tcp_ecn=1

# Firewall: allow only WireGuard port
iptables -A INPUT -p udp --dport 51820 -j ACCEPT
iptables -A INPUT -i wg0 -j ACCEPT
iptables -A FORWARD -i wg0 -o wg0 -j ACCEPT

# Source routing for WireGuard traffic (avoid default route)
ip rule add from 192.168.0.1 table 200
ip route add default via <aws_default_gw> dev ens5 table 200
```

### Pattern 2: Road Warrior (Remote Access)

```
                    Internet
                       │
         ┌─────────────┼──────────────┐
         │             │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │ Laptop  │   │ Phone   │   │ Tablet  │
    │ (macOS) │   │ (iOS)   │   │ (Android)│
    └─────────┘   └─────────┘   └─────────┘
         │             │              │
         └─────────────┼──────────────┘
                       │
                  ┌────▼─────┐
                  │ WG Server│
                  │ (AWS)    │
                  │ wg0: 10.8.0.1/24
                  └────┬─────┘
                       │
                ┌──────▼───────┐
                │ Corporate    │
                │ Network      │
                │ 10.0.0.0/8   │
                └──────────────┘

Server config:
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = <server_privkey>
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; sysctl -w net.ipv4.ip_forward=1
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT

[Peer]  # Laptop
PublicKey = <laptop_pubkey>
AllowedIPs = 10.8.0.2/32

[Peer]  # Phone
PublicKey = <phone_pubkey>
AllowedIPs = 10.8.0.3/32

[Peer]  # Tablet
PublicKey = <tablet_pubkey>
AllowedIPs = 10.8.0.4/32

Client config (laptop):
[Interface]
Address = 10.8.0.2/32
DNS = 10.0.0.53  # Corporate DNS
PrivateKey = <laptop_privkey>

[Peer]
PublicKey = <server_pubkey>
AllowedIPs = 10.0.0.0/8  # Route corporate network through VPN
Endpoint = <server_public_ip>:51820
PersistentKeepalive = 25
```

**Client key distribution (secure):**
```bash
# Server-side: generate and distribute configs
#!/bin/bash
PEER_NAME=$1
PEER_IP=$2

# Generate keys
PRIV=$(wg genkey)
PUB=$(echo "$PRIV" | wg pubkey)
PSK=$(wg genpsk)  # Optional preshared key for post-quantum resistance

# Create client config
cat > "${PEER_NAME}.conf" <<EOF
[Interface]
Address = ${PEER_IP}/32
PrivateKey = ${PRIV}
DNS = 10.0.0.53

[Peer]
PublicKey = $(cat server.pub)
PresharedKey = ${PSK}
AllowedIPs = 10.0.0.0/8
Endpoint = $(curl -s ifconfig.me):51820
PersistentKeepalive = 25
EOF

# Add peer to server
wg set wg0 peer "$PUB" preshared-key <(echo "$PSK") allowed-ips "${PEER_IP}/32"

# Generate QR code for mobile (iOS/Android apps)
qrencode -t ansiutf8 < "${PEER_NAME}.conf"

# Secure transfer (use out-of-band)
age -r <recipient_pubkey> -o "${PEER_NAME}.conf.age" "${PEER_NAME}.conf"
rm "${PEER_NAME}.conf"
```

### Pattern 3: Kubernetes CNI Integration (Pod-to-Pod Encryption)

```
┌──────────────────────────────────────────────────────────┐
│               Kubernetes Cluster (Multi-Node)             │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  Node1 (10.240.0.10)          Node2 (10.240.0.20)        │
│  ┌────────────────┐           ┌────────────────┐         │
│  │ Pod1           │           │ Pod2           │         │
│  │ 10.244.1.5     │           │ 10.244.2.8     │         │
│  └───────┬────────┘           └───────┬────────┘         │
│          │ veth                       │ veth              │
│  ┌───────▼────────┐           ┌───────▼────────┐         │
│  │ wg-pod bridge  │           │ wg-pod bridge  │         │
│  └───────┬────────┘           └───────┬────────┘         │
│          │                             │                  │
│  ┌───────▼────────┐           ┌───────▼────────┐         │
│  │ WireGuard wg0  │◄──────────┤ WireGuard wg0  │         │
│  │ 192.168.0.1    │  Encrypted│ 192.168.0.2    │         │
│  └───────┬────────┘           └───────┬────────┘         │
│          │                             │                  │
│          └─────────────┬───────────────┘                  │
│                        │                                   │
│                   Physical Network                         │
└──────────────────────────────────────────────────────────┘

Implementation: CNI plugin (example: wg-cni)
```

**CNI plugin config** (`/etc/cni/net.d/10-wireguard.conf`):
```json
{
  "cniVersion": "0.4.0",
  "name": "wg-mesh",
  "type": "wireguard",
  "subnet": "10.244.0.0/16",
  "mtu": 1420,
  "backend": "kernel",
  "ipam": {
    "type": "host-local",
    "ranges": [[{"subnet": "10.244.0.0/16"}]]
  },
  "dns": {
    "nameservers": ["10.96.0.10"]
  }
}
```

**Node mesh setup (DaemonSet):**
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: wireguard-mesh
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: wireguard
  template:
    metadata:
      labels:
        app: wireguard
    spec:
      hostNetwork: true
      containers:
      - name: wireguard
        image: linuxserver/wireguard:latest
        securityContext:
          privileged: true
          capabilities:
            add: ["NET_ADMIN", "SYS_MODULE"]
        volumeMounts:
        - name: wireguard-config
          mountPath: /config
        - name: lib-modules
          mountPath: /lib/modules
          readOnly: true
      volumes:
      - name: wireguard-config
        configMap:
          name: wireguard-peers
      - name: lib-modules
        hostPath:
          path: /lib/modules
```

---

## 6. Security Analysis & Threat Model

### Threat Surface Analysis

```
┌─────────────────────────────────────────────────────────────┐
│                    Attack Surface                            │
├─────────────────────────────────────────────────────────────┤
│ Component         │ Exposure      │ Mitigations              │
├───────────────────┼───────────────┼─────────────────────────┤
│ UDP socket        │ Public        │ - Silent packet drops    │
│                   │               │ - Rate limiting in kernel│
│                   │               │ - Stateless handshake    │
├───────────────────┼───────────────┼─────────────────────────┤
│ Crypto routines   │ Internal      │ - Audited primitives     │
│                   │               │ - Constant-time ops      │
│                   │               │ - No algorithm negotiation│
├───────────────────┼───────────────┼─────────────────────────┤
│ Netlink API       │ Local (root)  │ - CAP_NET_ADMIN required │
│                   │               │ - No information leaks   │
├───────────────────┼───────────────┼─────────────────────────┤
│ Routing table     │ Internal      │ - O(log n) lookup        │
│                   │               │ - IP spoofing check      │
└─────────────────────────────────────────────────────────────┘
```

### Attack Scenarios & Defenses

**1. DoS via Handshake Flood**
```
Attack: Send crafted handshake initiation messages to exhaust CPU/memory

Defense:
- Cookie-based handshake (under load):
  if (ratelimit_exceeded(src_ip)) {
      send_cookie_reply(src_ip);  // No state allocated
      return;
  }
  
- Per-source IP rate limiting (100/sec default)
- No state created until valid msg1 received
- Handshake uses < 1ms CPU on modern hardware
```

**2. Replay Attacks**
```
Attack: Capture and replay encrypted packets

Defense:
- 64-bit monotonic counter per session
- Sliding window (2048 packets, bitmap in memory)
  
  bool check_replay(u64 counter, u64 *window_start, u64 bitmap[32]) {
      if (counter < *window_start)
          return false;  // Too old
      if (counter >= *window_start + 2048)
          update_window(window_start, bitmap, counter);
      u64 index = counter - *window_start;
      if (bitmap[index / 64] & (1ULL << (index % 64)))
          return false;  // Already seen
      bitmap[index / 64] |= (1ULL << (index % 64));
      return true;
  }
```

**3. Timing Attacks**
```
Attack: Infer private keys via execution time variations

Defense:
- Curve25519 operations use constant-time arithmetic
- No secret-dependent branches in crypto code
- MAC verification uses constant-time comparison:
  
  bool memcmp_ct(const u8 *a, const u8 *b, size_t n) {
      u8 diff = 0;
      for (size_t i = 0; i < n; i++)
          diff |= a[i] ^ b[i];
      return diff == 0;
  }
```

**4. Traffic Analysis**
```
Attack: Infer metadata from packet sizes/timing

Defense (partial):
- No protocol markers in encrypted packets (type byte only)
- Optional random padding (not in kernel implementation)
- PersistentKeepalive masks traffic patterns (fake packets every N sec)

Limitation: Packet sizes still leak application data patterns
  → Combine with application-layer padding (e.g., QUIC)
```

**5. Post-Quantum Resistance**
```
Current state: Vulnerable to future quantum computers (Shor's algorithm breaks Curve25519)

Mitigation TODAY:
- Use optional 256-bit preshared key (PSK)
  → Even quantum adversary can't decrypt without PSK
  → Requires pre-shared secret via secure channel

Future: WireGuard-PQ (experimental)
  → Hybrid KEM: X25519 + Kyber1024
  → Maintains current performance with quantum resistance
```

### Isolation Boundaries

```
┌───────────────────────────────────────────────────────────┐
│              Trust Boundaries                              │
├───────────────────────────────────────────────────────────┤
│                                                             │
│  User Space (untrusted)                                    │
│  ─────────────────────────────────────────────────────────│
│  │ wg utility (setconf, show)                              │
│  │ - Can only modify own interfaces (CAP_NET_ADMIN)        │
│  └──────────────┬──────────────────────────────────────── │
│                 │ Netlink (validated)                      │
│  ─────────────────────────────────────────────────────────│
│  Kernel Space (trusted)                                    │
│  ┌──────────────▼──────────────────────────────────────┐  │
│  │ WireGuard module (wireguard.ko)                      │  │
│  │ - Input validation on all Netlink commands           │  │
│  │ - No user pointers trusted                            │  │
│  │ - All crypto in kernel (no upcalls)                   │  │
│  └──────────────┬──────────────────────────────────────┘  │
│                 │ Network stack                            │
│  ─────────────────────────────────────────────────────────│
│  Hardware                                                  │
│  │ NIC, CPU crypto extensions (AES-NI, NEON)              │  │
└───────────────────────────────────────────────────────────┘

Namespace isolation:
- Each network namespace can have independent WireGuard interfaces
- Useful for containerized workloads (Docker, Kubernetes pods)

Example: Per-container VPN
  ip netns add container1
  ip link add wg-container1 type wireguard
  ip link set wg-container1 netns container1
  ip netns exec container1 wg setconf wg-container1 /etc/wireguard/container1.conf
```

---

## 7. Performance Optimization & Benchmarking

### Performance Characteristics

```
Throughput (single TCP stream):
  Hardware: AWS c7gn.16xlarge (64 vCPU, 100 Gbps network)
  
  Baseline (no VPN):          94 Gbps
  WireGuard (kernel):         87 Gbps  (92% efficiency)
  IPsec (strongSwan):         31 Gbps  (33% efficiency)
  OpenVPN (userspace):         3 Gbps  ( 3% efficiency)

CPU usage (10 Gbps throughput):
  WireGuard: 1.2 cores (ChaCha20-Poly1305, software)
  IPsec:     4.8 cores (AES-GCM, AES-NI accelerated)
  
Latency overhead:
  WireGuard: +0.05ms (encryption/decryption)
  IPsec:     +0.15ms
  OpenVPN:   +2.5ms (userspace context switches)
```

### Kernel Performance Tuning

```bash
#!/bin/bash
# Production WireGuard performance tuning

# 1. Use multi-queue NIC (RSS - Receive Side Scaling)
ethtool -L eth0 combined 32  # 32 RX/TX queues

# 2. Enable XDP (eXpress Data Path) if supported
#    Requires kernel 5.6+ and compatible NIC
ethtool -K eth0 xdp on

# 3. Tune interrupt coalescing (reduce CPU interrupts)
ethtool -C eth0 rx-usecs 50 tx-usecs 50

# 4. Increase ring buffer sizes
ethtool -G eth0 rx 4096 tx 4096

# 5. Enable BPF JIT compiler
sysctl -w net.core.bpf_jit_enable=1
sysctl -w net.core.bpf_jit_harden=0  # Disable in trusted environments

# 6. CPU affinity (pin WireGuard processing to specific cores)
#    Requires manual IRQ balancing
systemctl stop irqbalance
for i in $(seq 0 15); do
    echo $((1 << i)) > /proc/irq/$(grep eth0-TxRx-$i /proc/interrupts | cut -d: -f1)/smp_affinity
done

# 7. Huge pages for crypto operations (reduces TLB misses)
echo 1024 > /proc/sys/vm/nr_hugepages
sysctl -w vm.nr_hugepages=1024

# 8. Disable CPU frequency scaling (performance governor)
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > $cpu
done

# 9. Enable TCP BBR congestion control (better performance over VPN)
sysctl -w net.ipv4.tcp_congestion_control=bbr
sysctl -w net.core.default_qdisc=fq

# 10. Adjust WireGuard MTU (avoid fragmentation)
#     Calculate: Physical MTU - IP header (20) - UDP header (8) - WireGuard overhead (32)
#     Example: 1500 - 20 - 8 - 32 = 1440
ip link set wg0 mtu 1440
```

### Benchmarking Suite

```bash
#!/bin/bash
# WireGuard performance benchmark

SERVER_IP="203.0.113.10"
SERVER_PORT="51820"
TEST_DURATION=60  # seconds

# 1. Throughput test (iperf3)
iperf3 -c 10.0.0.1 -t $TEST_DURATION -P 10 -J > wg_throughput.json

# 2. Latency test (ping with large sample)
ping -c 1000 -i 0.01 10.0.0.1 | tee wg_latency.txt

# 3. Packet loss (UDP flood)
iperf3 -c 10.0.0.1 -u -b 10G -t $TEST_DURATION --get-server-output | tee wg_udp.txt

# 4. CPU profiling (perf)
perf record -a -g -F 999 sleep 30
perf report --stdio | head -100 > wg_cpu_profile.txt

# 5. Handshake performance
for i in $(seq 1 1000); do
    wg set wg0 peer $(cat peer.pub) remove
    wg set wg0 peer $(cat peer.pub) endpoint $SERVER_IP:$SERVER_PORT allowed-ips 10.0.0.2/32
    sleep 0.1
done | ts '%.s' | tee wg_handshake_times.txt

# 6. Encryption overhead (compare with/without VPN)
#    Without VPN:
iperf3 -c $SERVER_IP -t 30 -J > baseline_throughput.json
#    With VPN:
iperf3 -c 10.0.0.1 -t 30 -J > wg_throughput.json

# 7. Memory usage
ps aux | grep wireguard | awk '{print $6}' | tee wg_memory_kb.txt

# 8. Crypto benchmark (ChaCha20-Poly1305 speed)
openssl speed -evp chacha20-poly1305
```

### Production Monitoring

```bash
# Prometheus exporter for WireGuard
# Install: https://github.com/MindFlavor/prometheus_wireguard_exporter

prometheus_wireguard_exporter --wireguard-interface wg0 --prometheus-addr 0.0.0.0:9586

# Key metrics:
# - wireguard_sent_bytes_total{interface="wg0",public_key="..."}
# - wireguard_received_bytes_total{interface="wg0",public_key="..."}
# - wireguard_latest_handshake_seconds{interface="wg0",public_key="..."}
# - wireguard_peer_count{interface="wg0"}

# Example Grafana dashboard queries:
# Throughput per peer:
rate(wireguard_sent_bytes_total[5m]) * 8  # bits/sec

# Handshake staleness (alert if > 3 min):
time() - wireguard_latest_handshake_seconds > 180

# Packet loss (requires additional tracking):
1 - (rate(wireguard_received_bytes_total[5m]) / rate(wireguard_sent_bytes_total[5m]))
```

---

## 8. Operational Procedures

### Key Rotation (Zero-Downtime)

```bash
#!/bin/bash
# Rotate WireGuard keys without dropping connections

INTERFACE="wg0"
OLD_PRIV="/etc/wireguard/old_private.key"
NEW_PRIV="/etc/wireguard/new_private.key"
NEW_PUB="/etc/wireguard/new_public.key"

# 1. Generate new keypair
wg genkey | tee "$NEW_PRIV" | wg pubkey > "$NEW_PUB"
chmod 600 "$NEW_PRIV"

# 2. Reconfigure interface with new key
wg set "$INTERFACE" private-key "$NEW_PRIV"

# 3. Notify all peers to update their config with new public key
#    (This step requires out-of-band coordination or automation)
echo "New public key: $(cat $NEW_PUB)"
echo "Distribute to all peers and have them update [Peer] PublicKey field"

# 4. Wait for all peers to update (grace period)
echo "Waiting 24 hours for peer updates..."
sleep 86400

# 5. Verify all peers have completed handshake with new key
wg show "$INTERFACE" | grep "latest handshake" | awk '{print $3,$4,$5}'

# 6. Archive old key (DO NOT DELETE - needed for forensics)
mv "$OLD_PRIV" "/etc/wireguard/archive/private_$(date +%s).key"
```

**Automated key rotation (for managed services):**
```yaml
# Kubernetes CronJob for key rotation
apiVersion: batch/v1
kind: CronJob
metadata:
  name: wireguard-key-rotation
spec:
  schedule: "0 2 1 * *"  # Monthly at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: key-rotator
            image: wireguard-key-rotator:v1
            command: ["/bin/bash", "/scripts/rotate_keys.sh"]
            volumeMounts:
            - name: wg-config
              mountPath: /etc/wireguard
          restartPolicy: OnFailure
          volumes:
          - name: wg-config
            secret:
              secretName: wireguard-keys
```

### Debugging & Troubleshooting

```bash
# 1. Check interface status
wg show wg0

# Expected output:
# interface: wg0
#   public key: <base64_pubkey>
#   private key: (hidden)
#   listening port: 51820
#
# peer: <base64_peer_pubkey>
#   endpoint: 203.0.113.5:51820
#   allowed ips: 10.0.0.2/32
#   latest handshake: 42 seconds ago
#   transfer: 10.23 GiB received, 5.67 GiB sent

# 2. Capture handshake packets (tcpdump)
tcpdump -i eth0 -n 'udp port 51820' -X

# Look for:
# - Type 1 (handshake initiation): 148 bytes
# - Type 2 (handshake response): 92 bytes
# - Type 4 (data): variable length

# 3. Enable kernel debug logs
echo 'module wireguard +p' > /sys/kernel/debug/dynamic_debug/control
dmesg -w | grep wireguard

# 4. Check routing
ip route get 10.0.0.2  # Should route via wg0
ip -6 route get fd00::2

# 5. Test connectivity (bypassing DNS)
ping -I wg0 10.0.0.2
curl --interface wg0 http://10.0.0.2

# 6. Verify AllowedIPs (common misconfiguration)
wg show wg0 allowed-ips
# Should show bidirectional routes

# 7. Check for packet drops (interface statistics)
ip -s link show wg0
# Look for RX/TX errors and drops

# 8. Firewall check (ensure UDP port open)
nmap -sU -p 51820 <server_ip>

# 9. MTU issues (test with different sizes)
ping -M do -s 1420 10.0.0.2  # Should succeed
ping -M do -s 1500 10.0.0.2  # Should fail if MTU issue

# 10. Peer reachability (manual handshake trigger)
wg set wg0 peer <pubkey> endpoint <new_ip>:51820
# Watch for handshake in 'wg show'
```

**Common Issues & Fixes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| `latest handshake: never` | Firewall blocking UDP, incorrect endpoint | Check firewall, verify endpoint IP/port |
| Handshake every 2 min, no data | AllowedIPs mismatch | Ensure peer's AllowedIPs includes destination |
| High packet loss | MTU too large, fragmentation | Set MTU to 1420 or lower |
| Connection drops after NAT timeout | No keepalive | Add `PersistentKeepalive = 25` |
| "Operation not permitted" | Missing CAP_NET_ADMIN | Run as root or add capability |
| Slow performance | CPU crypto, no AES-NI | Use ChaCha20 (default), check CPU flags |

### Disaster Recovery

```bash
# 1. Backup configuration
tar -czf wireguard-backup-$(date +%F).tar.gz /etc/wireguard/
gpg --encrypt --recipient admin@example.com wireguard-backup-*.tar.gz

# 2. Store in multiple locations
aws s3 cp wireguard-backup-*.tar.gz.gpg s3://backups/wireguard/
scp wireguard-backup-*.tar.gz.gpg backup-server:/mnt/backups/

# 3. Restore procedure
gpg --decrypt wireguard-backup-2025-02-06.tar.gz.gpg | tar -xz -C /
systemctl restart wg-quick@wg0

# 4. Validate restored config
wg-quick down wg0
wg-quick up wg0
wg show wg0

# 5. Test connectivity to all peers
for peer in $(wg show wg0 peers); do
    ip=$(wg show wg0 allowed-ips | grep $peer | awk '{print $2}' | cut -d/ -f1)
    ping -c 3 $ip || echo "FAILED: $peer ($ip)"
done
```

---

## 9. Advanced Topics

### WireGuard in Containers (Docker)

```dockerfile
# Dockerfile for WireGuard container
FROM alpine:latest

RUN apk add --no-cache wireguard-tools iptables ip6tables

COPY wg0.conf /etc/wireguard/wg0.conf

CMD ["sh", "-c", "wg-quick up wg0 && tail -f /dev/null"]
```

```bash
# Run with proper capabilities
docker run -d \
  --name wireguard \
  --cap-add NET_ADMIN \
  --cap-add SYS_MODULE \
  --sysctl net.ipv4.conf.all.src_valid_mark=1 \
  --sysctl net.ipv4.ip_forward=1 \
  -v /etc/wireguard:/etc/wireguard \
  -v /lib/modules:/lib/modules:ro \
  --restart unless-stopped \
  wireguard:latest
```

### WireGuard with VXLAN (Overlay Networks)

```bash
# Create VXLAN over WireGuard tunnel
# Node 1:
ip link add vxlan0 type vxlan id 100 remote 10.0.0.2 local 10.0.0.1 dstport 4789 dev wg0
ip addr add 172.16.0.1/24 dev vxlan0
ip link set vxlan0 up

# Node 2:
ip link add vxlan0 type vxlan id 100 remote 10.0.0.1 local 10.0.0.2 dstport 4789 dev wg0
ip addr add 172.16.0.2/24 dev vxlan0
ip link set vxlan0 up

# Now 172.16.0.0/24 is a secured overlay
# Use case: Multi-tenant isolation in Kubernetes
```

### Dynamic Peer Discovery (WireGuard Mesh)

```go
// wg-mesh: Automatic peer discovery using etcd/Consul
package main

import (
    "context"
    "fmt"
    "os/exec"
    clientv3 "go.etcd.io/etcd/client/v3"
)

func main() {
    cli, _ := clientv3.New(clientv3.Config{
        Endpoints: []string{"http://etcd:2379"},
    })
    
    // Watch for new peers
    watchChan := cli.Watch(context.Background(), "/wireguard/peers/", clientv3.WithPrefix())
    
    for wresp := range watchChan {
        for _, ev := range wresp.Events {
            if ev.Type == clientv3.EventTypePut {
                pubkey := string(ev.Kv.Key)
                endpoint := string(ev.Kv.Value)
                
                // Add peer dynamically
                cmd := exec.Command("wg", "set", "wg0", "peer", pubkey,
                    "endpoint", endpoint, "allowed-ips", "10.0.0.0/8")
                cmd.Run()
                
                fmt.Printf("Added peer: %s -> %s\n", pubkey, endpoint)
            }
        }
    }
}
```

### Quantum-Resistant WireGuard (Experimental)

```bash
# WireGuard-PQ: Post-quantum hybrid key exchange
# Build from source: https://git.zx2c4.com/wireguard-linux/

# Uses Kyber1024 + X25519
git clone https://git.zx2c4.com/wireguard-pq
cd wireguard-pq
make
insmod wireguard-pq.ko

# Configuration (same as regular WireGuard, transparent upgrade)
wg genkey | tee privatekey | wg pubkey > publickey
# Handshake automatically uses hybrid KEM
```

---

## 10. Testing & Validation

### Functional Tests

```bash
#!/bin/bash
# WireGuard functional test suite

set -e

# Setup test environment
ip netns add ns1
ip netns add ns2

# Create WireGuard interfaces
ip link add wg1 type wireguard
ip link add wg2 type wireguard
ip link set wg1 netns ns1
ip link set wg2 netns ns2

# Generate keys
PRIV1=$(wg genkey)
PUB1=$(echo "$PRIV1" | wg pubkey)
PRIV2=$(wg genkey)
PUB2=$(echo "$PRIV2" | wg pubkey)

# Configure ns1
ip netns exec ns1 ip addr add 10.0.0.1/24 dev wg1
ip netns exec ns1 wg set wg1 listen-port 51820 private-key <(echo "$PRIV1")
ip netns exec ns1 wg set wg1 peer "$PUB2" allowed-ips 10.0.0.2/32 endpoint 127.0.0.1:51821
ip netns exec ns1 ip link set wg1 up

# Configure ns2
ip netns exec ns2 ip addr add 10.0.0.2/24 dev wg2
ip netns exec ns2 wg set wg2 listen-port 51821 private-key <(echo "$PRIV2")
ip netns exec ns2 wg set wg2 peer "$PUB1" allowed-ips 10.0.0.1/32 endpoint 127.0.0.1:51820
ip netns exec ns2 ip link set wg2 up

# Test 1: Handshake
sleep 2
ip netns exec ns1 wg show wg1 | grep -q "latest handshake" || (echo "FAIL: No handshake"; exit 1)
echo "PASS: Handshake completed"

# Test 2: Ping
ip netns exec ns1 ping -c 3 10.0.0.2 || (echo "FAIL: Ping failed"; exit 1)
echo "PASS: Connectivity"

# Test 3: Throughput
ip netns exec ns2 iperf3 -s -D
sleep 1
THROUGHPUT=$(ip netns exec ns1 iperf3 -c 10.0.0.2 -t 5 -J | jq -r '.end.sum_received.bits_per_second')
echo "PASS: Throughput: $(echo "scale=2; $THROUGHPUT / 1000000" | bc) Mbps"

# Cleanup
pkill iperf3
ip netns del ns1
ip netns del ns2
```

### Fuzzing (Handshake Packets)

```c
// wg_fuzz.c: AFL fuzzer for WireGuard handshake parsing
#include <stdint.h>
#include <stdlib.h>

// Minimal handshake message structure
struct handshake_msg {
    uint8_t type;
    uint8_t reserved[3];
    uint32_t sender_index;
    uint8_t payload[128];
};

// Simulate WireGuard handshake parsing
int parse_handshake(const uint8_t *data, size_t len) {
    if (len < sizeof(struct handshake_msg))
        return -1;
    
    struct handshake_msg *msg = (struct handshake_msg *)data;
    
    // Type check
    if (msg->type != 1 && msg->type != 2)
        return -1;
    
    // Reserved must be zero
    if (msg->reserved[0] || msg->reserved[1] || msg->reserved[2])
        return -1;
    
    // ... additional parsing logic
    return 0;
}

// AFL entry point
int main(int argc, char **argv) {
    uint8_t buf[1024];
    size_t len = read(0, buf, sizeof(buf));
    parse_handshake(buf, len);
    return 0;
}

// Compile: afl-gcc -o wg_fuzz wg_fuzz.c
// Run: afl-fuzz -i testcases/ -o findings/ ./wg_fuzz
```

### Load Testing

```python
#!/usr/bin/env python3
# WireGuard load test: Simulate 1000 concurrent connections

import subprocess
import threading
import time

def create_peer(peer_id):
    priv = subprocess.check_output(["wg", "genkey"]).decode().strip()
    pub = subprocess.check_output(["wg", "pubkey"], input=priv.encode()).decode().strip()
    
    # Add peer to server
    subprocess.run([
        "wg", "set", "wg0", "peer", pub,
        "allowed-ips", f"10.0.{peer_id // 256}.{peer_id % 256}/32"
    ])
    
    # Simulate traffic (ping)
    subprocess.run([
        "ping", "-c", "10", "-i", "0.1",
        f"10.0.{peer_id // 256}.{peer_id % 256}"
    ], stdout=subprocess.DEVNULL)

# Spawn 1000 peers
threads = []
for i in range(1, 1001):
    t = threading.Thread(target=create_peer, args=(i,))
    t.start()
    threads.append(t)
    
    if i % 100 == 0:
        time.sleep(1)  # Rate limit

for t in threads:
    t.join()

print("Load test completed: 1000 peers")
```

---

## 11. Compliance & Auditing

### FIPS 140-2 Compliance (Limitation)

**Current state:** WireGuard's ChaCha20-Poly1305 is **NOT** FIPS 140-2 approved.

**Options for regulated environments:**
1. Use IPsec with FIPS-approved algorithms (AES-GCM)
2. Deploy WireGuard with AES-NI-accelerated ChaCha20 (faster, but still non-compliant)
3. Request FIPS validation from NIST (multi-year process)

**Compliance workaround (defense-in-depth):**
```bash
# Layer WireGuard over FIPS-compliant TLS tunnel
# (Provides FIPS compliance + WireGuard performance)

# 1. Setup stunnel with FIPS mode
stunnel-fips /etc/stunnel/wireguard.conf

# /etc/stunnel/wireguard.conf:
# fips = yes
# [wireguard]
# client = yes
# accept = 127.0.0.1:51820
# connect = remote-server:443
# cert = /etc/ssl/client.pem
# key = /etc/ssl/client.key

# 2. Configure WireGuard to use localhost endpoint
wg set wg0 peer <pubkey> endpoint 127.0.0.1:51820
```

### Audit Logging

```bash
# Log all WireGuard configuration changes
auditctl -w /etc/wireguard/ -p wa -k wireguard_config
auditctl -a always,exit -F arch=b64 -S socket -F a0=2 -F a1=2 -F a2=136 -k wireguard_socket

# Query audit logs
ausearch -k wireguard_config -ts today

# Centralize logs (syslog-ng)
# /etc/syslog-ng/conf.d/wireguard.conf:
source s_wireguard {
    file("/var/log/kern.log" follow-freq(1) flags(no-parse));
};
filter f_wireguard {
    message("wireguard");
};
destination d_wireguard {
    network("syslog-server.example.com" port(514) transport("udp"));
};
log {
    source(s_wireguard);
    filter(f_wireguard);
    destination(d_wireguard);
};
```

---

## 12. Real-World Case Studies

### Case Study 1: Tailscale (WireGuard-based Mesh VPN)

**Architecture:**
- Coordination server (DERP relays for NAT traversal)
- End-to-end encrypted WireGuard tunnels
- Automatic key distribution via OAuth

**Key innovations:**
- Serverless NAT traversal (STUN + DERP fallback)
- Per-user ACLs (cryptokey routing + app-layer authz)
- Zero-touch deployment (auto-configure DNS, routes)

### Case Study 2: Mullvad VPN (Privacy-focused)

**Security features:**
- Diskless servers (RAM-only, no logs)
- Anonymous account numbers (no email required)
- WireGuard with optional multi-hop (entry + exit servers)
- Perfect forward secrecy per connection

**Performance:**
- 10 Gbps+ on single server
- < 1ms latency overhead
- Supports 10,000+ concurrent users per server

### Case Study 3: AWS VPN (Site-to-Site with Acceleration)

```
┌──────────────────────────────────────────────────────────┐
│  On-Premises               AWS VPC                        │
│  ┌──────────┐             ┌──────────┐                   │
│  │ WG Router│◄────────────┤ EC2 (WG) │                   │
│  │ (strongS)│  Internet   │          │                   │
│  └────┬─────┘             └────┬─────┘                   │
│       │                        │                          │
│  10.0.0.0/16              172.31.0.0/16                  │
│                                                           │
│  Acceleration: AWS Global Accelerator                    │
│  - Anycast IPs (2 static IPs)                            │
│  - Automatic failover                                    │
│  - DDoS protection (AWS Shield)                          │
└──────────────────────────────────────────────────────────┘
```

---

## Next 3 Steps

1. **Deploy test environment:**
   ```bash
   # Two VMs/containers, establish WireGuard tunnel, measure baseline performance
   # Validate handshake, verify cryptokey routing, test failover
   ```

2. **Implement production-grade monitoring:**
   ```bash
   # Deploy Prometheus exporter, create Grafana dashboard
   # Alert on: handshake failures, high latency, MTU issues
   ```

3. **Threat model your deployment:**
   ```bash
   # Document: trust boundaries, attack vectors, mitigations
   # Review: key rotation policy, incident response plan
   # Test: failure modes (network partition, key compromise)
   ```

---

## References

1. **WireGuard whitepaper:** https://www.wireguard.com/papers/wireguard.pdf
2. **Noise Protocol Framework:** https://noiseprotocol.org/noise.html
3. **Kernel source:** https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/net/wireguard
4. **Security audit (Cure53):** https://www.wireguard.com/formal-verification/
5. **Performance analysis (ACM):** "WireGuard: Next Generation Kernel Network Tunnel" (NDSS 2017)
6. **ChaCha20-Poly1305 (RFC 8439):** https://datatracker.ietf.org/doc/html/rfc8439
7. **Curve25519 (RFC 7748):** https://datatracker.ietf.org/doc/html/rfc7748