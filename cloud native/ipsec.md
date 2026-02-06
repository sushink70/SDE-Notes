# IPSec Comprehensive Deep-Dive

**Summary**: IPSec is a Layer 3 protocol suite providing cryptographic security for IP packets through authentication (AH), encryption/confidentiality (ESP), key management (IKE), and security policy enforcement (SPD/SAD). It operates in two modes—transport (end-to-end) and tunnel (gateway-to-gateway)—supporting site-to-site VPNs, cloud interconnects, and secure overlay networks. Core production use: AWS VPN, Azure VPN Gateway, GCP Cloud VPN, Kubernetes encrypted CNI, and hybrid multi-cloud backhaul. Security primitives: IKEv2 for key exchange, AES-GCM for AEAD, X.509/PSK for authentication, anti-replay via sequence numbers, perfect forward secrecy via ephemeral DH groups.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         IPSec Stack Architecture                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────┐      ┌─────────────┐      ┌──────────────┐         │
│  │ Application│      │  Transport  │      │  Application │         │
│  │   Layer    │      │    Layer    │      │     Data     │         │
│  └─────┬──────┘      └──────┬──────┘      └──────┬───────┘         │
│        │                    │                    │                  │
│        ▼                    ▼                    ▼                  │
│  ┌──────────────────────────────────────────────────────┐          │
│  │              IP Layer (IPv4/IPv6)                     │          │
│  └───────────────────┬──────────────────────────────────┘          │
│                      │                                              │
│       ┌──────────────┴──────────────┐                              │
│       │                             │                              │
│       ▼                             ▼                              │
│  ┌─────────┐                  ┌─────────┐                         │
│  │   AH    │                  │   ESP   │                         │
│  │ (Auth)  │                  │(Enc+Auth)│                        │
│  └────┬────┘                  └────┬────┘                         │
│       │                            │                              │
│       └────────────┬───────────────┘                              │
│                    ▼                                               │
│         ┌──────────────────────┐                                  │
│         │   Security Policy    │                                  │
│         │   Database (SPD)     │◄─────────┐                       │
│         └──────────────────────┘          │                       │
│                    │                       │                       │
│                    ▼                       │                       │
│         ┌──────────────────────┐          │                       │
│         │Security Association  │          │                       │
│         │   Database (SAD)     │          │                       │
│         └──────────────────────┘          │                       │
│                    │                       │                       │
│                    ▼                       │                       │
│         ┌──────────────────────┐          │                       │
│         │    IKE Daemon        │──────────┘                       │
│         │  (IKEv2/strongSwan)  │                                  │
│         └──────────────────────┘                                  │
│                    │                                               │
│                    ▼                                               │
│         ┌──────────────────────┐                                  │
│         │   Crypto Engine      │                                  │
│         │ (Kernel/NIC offload) │                                  │
│         └──────────────────────┘                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Protocol Headers:

Transport Mode:
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ IP Header│ESP Header│TCP/UDP   │ Payload  │ESP Trailer│
│ (original)│         │ Header   │          │+ ICV     │
└──────────┴──────────┴──────────┴──────────┴──────────┘
           └──────────── Encrypted ───────────┘
           └────────────── Authenticated ─────────────┘

Tunnel Mode:
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│New IP Hdr│ESP Header│ Original │ Original │ Payload  │ESP Trailer│
│          │          │ IP Header│TCP/UDP   │          │+ ICV     │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
           └───────────────── Encrypted ──────────────────┘
           └─────────────────── Authenticated ────────────────────┘
```

---

## Core Concepts & Under-the-Hood Operations

### 1. **IPSec Protocol Suite Components**

#### **ESP (Encapsulating Security Payload) - RFC 4303**
- **Purpose**: Provides confidentiality, authentication, integrity, anti-replay
- **Operations**:
  - Encrypts payload using symmetric cipher (AES-GCM-256, ChaCha20-Poly1305)
  - Adds Integrity Check Value (ICV) using AEAD or separate HMAC (SHA2-256/384/512)
  - Sequence number for anti-replay protection
  - Padding for block cipher alignment and traffic flow confidentiality

**ESP Header Structure**:
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|               Security Parameters Index (SPI)                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Sequence Number                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Payload Data (variable)                    |
~                                                               ~
|                                                               |
+               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|               |     Padding (0-255 bytes)                     |
+-+-+-+-+-+-+-+-+               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               |  Pad Length   | Next Header   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Integrity Check Value-ICV   (variable)                |
~                                                               ~
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **SPI**: Security Parameter Index (32-bit) - identifies SA in SAD
- **Sequence Number**: 32-bit counter (Extended Sequence Number ESN: 64-bit) for anti-replay
- **Next Header**: Identifies encapsulated protocol (TCP=6, UDP=17, IP=4)

#### **AH (Authentication Header) - RFC 4302**
- **Purpose**: Provides authentication, integrity, anti-replay (NO confidentiality)
- **Use Case**: Legacy compliance where encryption prohibited; mostly obsolete
- **Issue**: Modifies IP header (immutable fields), breaks NAT
- **Production**: Rarely used; ESP with null encryption preferred

#### **IKE (Internet Key Exchange) - RFC 7296 (IKEv2)**
- **Purpose**: Automated key management, SA establishment, authentication
- **Phases**:
  - **IKE_SA_INIT**: DH exchange, nonce exchange, cipher suite negotiation (unauthenticated)
  - **IKE_AUTH**: Mutual authentication (certs/PSK), establish first CHILD_SA (IPSec SA)
  - **CREATE_CHILD_SA**: Rekey SAs, establish additional SAs
  - **INFORMATIONAL**: Delete SAs, keepalives (DPD - Dead Peer Detection)

**IKEv2 Message Flow**:
```
Initiator                          Responder
─────────────────────────────────────────────
IKE_SA_INIT:
HDR, SAi1, KEi, Ni  ──────────►
                    ◄────────── HDR, SAr1, KEr, Nr, [CERTREQ]

[Derive SKEYSEED, SK_d, SK_ai, SK_ar, SK_ei, SK_er, SK_pi, SK_pr]

IKE_AUTH:
HDR, SK {IDi, [CERT,] [CERTREQ,]
[IDr,] AUTH, SAi2, TSi, TSr} ──►
                    ◄────────── HDR, SK {IDr, [CERT,] AUTH,
                                         SAr2, TSi, TSr}

[CHILD_SA established, IPSec traffic flows]
```

**Key Derivation (RFC 5996)**:
```
SKEYSEED = prf(Ni | Nr, g^ir)  // DH shared secret
{SK_d | SK_ai | SK_ar | SK_ei | SK_er | SK_pi | SK_pr}
    = prf+ (SKEYSEED, Ni | Nr | SPIi | SPIr)

SK_d  : Derive keys for CHILD_SAs
SK_ai/ar : IKE integrity (HMAC)
SK_ei/er : IKE encryption (AES-CBC/GCM)
SK_pi/pr : IKE authentication payloads
```

### 2. **Security Databases**

#### **SPD (Security Policy Database)**
- **Location**: Kernel (Linux: `ip xfrm policy`, strongSwan config)
- **Function**: Maps traffic selectors to security actions
- **Selectors**: src/dst IP, port, protocol, direction (in/out/fwd)
- **Actions**: PROTECT (apply IPSec), BYPASS, DISCARD

**Example SPD Entry**:
```bash
# Protect traffic 10.0.1.0/24 -> 10.0.2.0/24 via IPSec tunnel
ip xfrm policy add src 10.0.1.0/24 dst 10.0.2.0/24 dir out \
  tmpl src 203.0.113.1 dst 198.51.100.1 proto esp mode tunnel
```

#### **SAD (Security Association Database)**
- **Location**: Kernel (Linux: `ip xfrm state`)
- **Function**: Stores per-flow cryptographic state
- **SA Parameters**: SPI, crypto algorithms, keys, sequence numbers, lifetime
- **Lookup**: By (SPI, dest IP, protocol) tuple

**Example SAD Entry**:
```bash
# Inbound SA
ip xfrm state add src 198.51.100.1 dst 203.0.113.1 proto esp spi 0xc001cafe \
  mode tunnel \
  auth-trunc 'hmac(sha256)' 0x<32-byte-key> 128 \
  enc 'cbc(aes)' 0x<32-byte-key> \
  replay-window 64 \
  flag align4
```

### 3. **Cryptographic Algorithms (Production Grade)**

#### **Encryption (Confidentiality)**
| Algorithm | Key Size | Mode | Performance | Security | Use Case |
|-----------|----------|------|-------------|----------|----------|
| AES-GCM | 128/256-bit | AEAD | High (AES-NI) | Strong | Default |
| AES-CBC | 128/256-bit | CBC | Medium | Strong | Legacy |
| ChaCha20-Poly1305 | 256-bit | AEAD | High (SW) | Strong | Non-AES-NI CPUs |

#### **Integrity/Authentication**
| Algorithm | Output | Performance | Security |
|-----------|--------|-------------|----------|
| HMAC-SHA2-256 | 256-bit | High | Strong |
| HMAC-SHA2-384 | 384-bit | Medium | Strong |
| HMAC-SHA2-512 | 512-bit | Medium | Strong |
| AES-GMAC | 128-bit | High | Strong (AEAD) |

#### **Key Exchange (DH Groups)**
| Group | Type | Key Size | Security | Performance |
|-------|------|----------|----------|-------------|
| 14 | MODP | 2048-bit | Minimum | Fast |
| 19 | ECP | 256-bit (Curve25519) | Strong | Fastest |
| 20 | ECP | 384-bit (secp384r1) | Strong | Fast |
| 21 | ECP | 521-bit | Overkill | Slow |

**Production Recommendation**:
```
Transform: ESP with AES-GCM-256, DH Group 19 (Curve25519)
IKE: AES-GCM-256, PRF-HMAC-SHA2-256, DH Group 19
PFS: Enabled (rekey with new DH exchange)
```

### 4. **Transport vs Tunnel Mode**

#### **Transport Mode**
- **Packet**: Original IP header + ESP + Payload
- **Use Case**: Host-to-host, end-to-end encryption
- **Limitation**: NAT breaks it (IP/port in ESP hash), requires NAT-T (UDP encapsulation)
- **Example**: Kubernetes pod-to-pod encryption (Calico/Cilium with IPSec)

#### **Tunnel Mode**
- **Packet**: New IP header + ESP + (Original IP header + Payload)
- **Use Case**: Site-to-site VPN, cloud interconnects, gateway-to-gateway
- **Advantage**: NAT-friendly, hides original topology
- **Example**: AWS Site-to-Site VPN, GCP Cloud VPN, Azure VPN Gateway

**Tunnel Mode Path MTU Calculation**:
```
MTU_ipsec = MTU_physical - IP_header(20/40) - ESP_header(8) - ESP_trailer(2+pad) - ICV(16)
          = 1500 - 20 - 8 - 18 - 16 = 1438 bytes (IPv4, AES-GCM)

Recommendation: Set MSS clamping on VPN gateway
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
  -j TCPMSS --set-mss 1360
```

### 5. **NAT Traversal (NAT-T) - RFC 3947/3948**

**Problem**: ESP encrypts ports, NAT devices cannot rewrite port numbers in encrypted payload

**Solution**: UDP encapsulation on port 4500
```
Original:  IP | ESP | Payload
With NAT-T: IP | UDP:4500 | Non-ESP-Marker(4-bytes=0) | ESP | Payload
```

**Detection**: IKE sends NAT_DETECTION_SOURCE/DESTINATION_IP payloads (hash of IP/port)
- If hash mismatch → NAT detected → enable UDP encapsulation

**Keepalive**: Send UDP packet every 20-30s to keep NAT mapping alive

---

## Production Deployment Patterns

### 1. **Site-to-Site VPN (AWS VPN)**

**Scenario**: On-prem datacenter ↔ AWS VPC

```bash
# AWS Side: Virtual Private Gateway (VGW) automatically configured
# Customer Gateway: strongSwan on Linux

# /etc/ipsec.conf
conn aws-vpn-tunnel1
    type=tunnel
    authby=secret
    left=%defaultroute
    leftid=203.0.113.1
    leftsubnet=10.0.1.0/24
    right=52.95.1.1  # AWS VPN endpoint
    rightsubnet=10.10.0.0/16
    ike=aes256-sha256-modp2048!
    esp=aes256-sha256-modp2048!
    keyexchange=ikev2
    ikelifetime=8h
    lifetime=1h
    dpdaction=restart
    dpddelay=10s
    dpdtimeout=30s
    auto=start

# /etc/ipsec.secrets
203.0.113.1 52.95.1.1 : PSK "your-pre-shared-key"

# Start
ipsec start
ipsec up aws-vpn-tunnel1

# Verify
ipsec statusall
ip xfrm state
ip xfrm policy
ping -I 10.0.1.1 10.10.0.5  # Test connectivity
```

**Architecture**:
```
┌─────────────────┐         ┌──────────────┐         ┌─────────────┐
│  On-Prem DC     │         │   Internet   │         │   AWS VPC   │
│  10.0.1.0/24    │◄───────►│              │◄───────►│ 10.10.0.0/16│
│                 │  IPSec  │              │  IPSec  │             │
│  strongSwan GW  │  Tunnel │              │  Tunnel │     VGW     │
│  203.0.113.1    │         │              │         │ 52.95.1.1   │
└─────────────────┘         └──────────────┘         └─────────────┘
```

### 2. **Kubernetes CNI with IPSec (Calico)**

**Use Case**: Encrypt pod-to-pod traffic across nodes

```bash
# Enable Calico IPSec
kubectl patch felixconfiguration default --type='merge' -p \
  '{"spec":{"ipsecEnabled":true}}'

# Calico generates WireGuard keys, falls back to IPSec if WireGuard unavailable
# Automatically configures:
# - SPD: pod CIDR -> pod CIDR = PROTECT
# - SAD: Per-node SAs
# - IKE daemon: Manages key rotation

# Verify on node
ip xfrm state
ip xfrm policy

# Check encryption
tcpdump -i eth0 -n esp  # Should see ESP packets between nodes
```

**Data Path**:
```
Pod A (10.244.1.5)  ──►  veth  ──►  cali123  ──►  XFRM Encrypt  ──►  eth0
                                                      ▼
                                                   ESP Packet
                                                      ▼
                                      Internet / Underlay Network
                                                      ▼
                                                   ESP Packet
                                                      ▼
eth0  ◄──  XFRM Decrypt  ◄──  cali456  ◄──  veth  ◄──  Pod B (10.244.2.8)
```

### 3. **GCP Cloud VPN (BGP over IPSec)**

**Scenario**: Multi-region mesh with dynamic routing

```bash
# GCP side: Cloud VPN Gateway with Cloud Router (BGP)
gcloud compute vpn-gateways create gw-us-central1 \
  --network=vpc1 --region=us-central1

gcloud compute routers create router-us-central1 \
  --network=vpc1 --region=us-central1 --asn=65001

# Create VPN tunnel
gcloud compute vpn-tunnels create tunnel-to-onprem \
  --peer-address=203.0.113.1 \
  --shared-secret=your-psk \
  --region=us-central1 \
  --vpn-gateway=gw-us-central1 \
  --ike-version=2

# BGP peer
gcloud compute routers add-bgp-peer router-us-central1 \
  --peer-name=onprem-bgp \
  --peer-asn=65002 \
  --interface=if-tunnel-to-onprem \
  --peer-ip-address=169.254.1.2 \
  --region=us-central1

# On-prem strongSwan + FRR (BGP)
# /etc/ipsec.conf (similar to AWS example)

# FRR BGP config
router bgp 65002
  neighbor 169.254.1.1 remote-as 65001
  network 10.0.1.0/24
```

---

## Security & Threat Model

### **Threats Mitigated**
1. **Eavesdropping**: ESP encryption (AES-GCM)
2. **Man-in-the-Middle**: IKE mutual authentication (X.509/PSK), certificate validation
3. **Replay Attacks**: Anti-replay window (64-bit sequence number)
4. **Traffic Analysis**: Tunnel mode hides inner topology, padding obscures packet size
5. **Key Compromise**: PFS ensures past sessions safe even if current key leaked

### **Attack Surface & Mitigations**

| Attack | Mitigation |
|--------|------------|
| **IKE DDoS** | Cookie mechanism (COOKIE notify), rate limiting |
| **Weak DH Group** | Enforce Group 19+ (ECP 256-bit minimum) |
| **Downgrade Attack** | Strict cipher suite ordering, reject weak algos |
| **Certificate Forgery** | Pin CA certificates, use CRL/OCSP, short-lived certs |
| **Timing Side-Channel** | Constant-time crypto (AES-NI), avoid RSA (use ECDSA) |
| **Quantum Threat** | Transition to PQC (post-quantum IKE under development) |

### **Hardening Checklist**
```bash
# Disable IKEv1 (only IKEv2)
ipsec.conf: keyexchange=ikev2

# Strong ciphers only
ike=aes256gcm16-prfsha384-ecp384!
esp=aes256gcm16-ecp384!

# Certificate-based auth (no PSK in production at scale)
leftcert=server.crt
leftkey=server.key
rightcert=client.crt

# Enable DPD (detect dead peer)
dpdaction=restart
dpddelay=30s

# Limit SA lifetime (force rekey)
ikelifetime=3h
lifetime=1h

# Enable perfect forward secrecy
keyingtries=1
rekey=yes
```

### **Monitoring & Detection**

```bash
# Log IKE negotiations
ipsec.conf: charondebug="ike 2, knl 2, cfg 2"

# Prometheus metrics (strongSwan exporter)
ipsec_sa_established{tunnel="aws-vpn-tunnel1"} 1
ipsec_sa_bytes_in{tunnel="aws-vpn-tunnel1"} 1234567890
ipsec_ikev2_init_failures_total 5

# Detect anomalies
# - Frequent rekeys → possible attack or config issue
# - Asymmetric byte counts → possible packet loss
# - IKE auth failures → brute force attempt

# Kernel stats
ip -s xfrm state
ip -s xfrm policy
cat /proc/net/xfrm_stat  # Errors, dropped packets
```

---

## Performance Optimization

### **Hardware Offload**

#### **NIC IPSec Offload (Intel X710, Mellanox CX-5)**
```bash
# Check NIC capabilities
ethtool -k eth0 | grep esp

# Enable IPSec offload
ethtool -K eth0 esp-hw-offload on

# Offloads ESP encryption/decryption to NIC
# Throughput: 10-40 Gbps (vs 2-5 Gbps CPU)
# Latency: <1µs additional overhead
```

#### **AES-NI (CPU Instruction Set)**
```bash
# Verify AES-NI enabled
grep -o aes /proc/cpuinfo | uniq

# strongSwan automatically uses AES-NI if available
# Throughput: 2-5 Gbps per core (AES-GCM-128)
```

#### **QAT (Intel QuickAssist Technology)**
```bash
# Hardware crypto accelerator
# Used by strongSwan via OpenSSL engine
# Throughput: 50-100 Gbps (dedicated card)

# Configure
/etc/strongswan.d/charon/openssl.conf:
  openssl { engine_id = qat }
```

### **Kernel Tuning**

```bash
# Increase conntrack table (for many SAs)
sysctl -w net.netfilter.nf_conntrack_max=1048576

# IPSec buffer sizes
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728

# Disable reverse path filtering (for asymmetric routing)
sysctl -w net.ipv4.conf.all.rp_filter=0

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1
```

### **Benchmarking**

```bash
# Throughput test (iperf3 over IPSec tunnel)
# Server (AWS)
iperf3 -s -B 10.10.0.5

# Client (on-prem)
iperf3 -c 10.10.0.5 -B 10.0.1.1 -t 60 -P 4

# Baseline (no IPSec): ~9.5 Gbps
# With IPSec (AES-GCM, AES-NI): ~5 Gbps
# With IPSec (NIC offload): ~9.2 Gbps

# Latency test
ping -I 10.0.1.1 10.10.0.5
# Baseline: 20ms
# With IPSec: 21ms (+1ms overhead)

# Crypto benchmark (OpenSSL)
openssl speed -evp aes-256-gcm
# AES-NI: ~3.5 GB/s per core
```

---

## Failure Modes & Debugging

### **Common Issues**

| Symptom | Cause | Fix |
|---------|-------|-----|
| **IKE_SA established, CHILD_SA fails** | Traffic selector mismatch | Verify `leftsubnet`/`rightsubnet` match SPD |
| **Packets not encrypted** | SPD missing or wrong priority | `ip xfrm policy show`, check `priority` |
| **High packet loss** | MTU issue (fragmentation) | Enable MSS clamping, reduce MTU |
| **Frequent rekeys** | Lifetime too short | Increase `lifetime`, check DPD settings |
| **No traffic after rekey** | Old SA not deleted | `ipsec down`, `ipsec up`, check `ipsec statusall` |

### **Debug Commands**

```bash
# IKE negotiations (live)
ipsec statusall
journalctl -u strongswan -f

# Packet capture (IKE on UDP 500/4500)
tcpdump -i eth0 -n 'udp port 500 or udp port 4500'

# ESP packets
tcpdump -i eth0 -n esp

# Kernel XFRM errors
dmesg | grep -i xfrm
cat /proc/net/xfrm_stat

# Decrypt ESP packets (wireshark)
# Edit -> Preferences -> Protocols -> ESP
# Add SA: SPI, Encryption algo, Encryption key, Auth algo, Auth key

# Test encryption (tcpdump inside tunnel)
# Should see ESP packets on outer interface
# Should see plaintext on inner interface (if tun device used)
```

### **Rollback Plan**

```bash
# Disable IPSec, allow cleartext (emergency)
ipsec down <connection-name>
ip xfrm policy flush
ip xfrm state flush

# Re-enable routing without IPSec
ip route add 10.10.0.0/16 via 203.0.113.254  # Direct route

# Restore IPSec (after fix)
ipsec reload
ipsec up <connection-name>
```

---

## Real-World Deployment Examples

### **Example 1: Multi-Cloud Hybrid Mesh (AWS + GCP + On-Prem)**

```
          On-Prem DC               AWS VPC              GCP VPC
        (10.0.0.0/16)           (10.1.0.0/16)        (10.2.0.0/16)
              │                       │                    │
              │   IPSec Tunnel 1      │                    │
              ├───────────────────────┤                    │
              │                       │   IPSec Tunnel 2   │
              │                       ├────────────────────┤
              │       IPSec Tunnel 3  │                    │
              └───────────────────────┴────────────────────┘

# On-Prem strongSwan (3 tunnels)
conn aws-tunnel
    right=52.95.1.1
    rightsubnet=10.1.0.0/16
    ...

conn gcp-tunnel
    right=35.190.1.1
    rightsubnet=10.2.0.0/16
    ...

conn aws-to-gcp  # Transit via on-prem
    leftsubnet=10.1.0.0/16
    rightsubnet=10.2.0.0/16
    # Policy route: AWS traffic -> GCP tunnel
```

### **Example 2: Kubernetes Multi-Cluster with Cilium + IPSec**

```bash
# Cluster 1 (us-east1)
cilium install --set encryption.enabled=true \
  --set encryption.type=ipsec \
  --cluster-name=us-east1 \
  --cluster-id=1

# Cluster 2 (eu-west1)
cilium install --set encryption.enabled=true \
  --set encryption.type=ipsec \
  --cluster-name=eu-west1 \
  --cluster-id=2

# Clustermesh (cross-cluster service discovery + IPSec)
cilium clustermesh enable
cilium clustermesh connect --destination-context eu-west1

# Verify
cilium status
kubectl -n kube-system exec -ti cilium-xxxxx -- cilium encrypt status
```

### **Example 3: Zero-Trust Overlay (Teleport/Tailscale-style)**

```go
// IPSec SA per user session (not typical strongSwan, custom daemon)
// Go implementation using netlink (github.com/vishvananda/netlink)

import (
    "github.com/vishvananda/netlink"
    "github.com/vishvananda/netlink/nl"
)

func createIPSecSA(spi uint32, srcIP, dstIP net.IP, key []byte) error {
    state := &netlink.XfrmState{
        Src:   srcIP,
        Dst:   dstIP,
        Proto: netlink.XFRM_PROTO_ESP,
        Spi:   int(spi),
        Mode:  netlink.XFRM_MODE_TUNNEL,
        Aead: &netlink.XfrmStateAlgo{
            Name:   "rfc4106(gcm(aes))",
            Key:    key, // 32-byte AES-256 + 4-byte salt
            ICVLen: 128,
        },
        Reqid: 1,
    }
    return netlink.XfrmStateAdd(state)
}

func createIPSecPolicy(srcNet, dstNet *net.IPNet, spi uint32) error {
    policy := &netlink.XfrmPolicy{
        Src:      srcNet,
        Dst:      dstNet,
        Dir:      netlink.XFRM_DIR_OUT,
        Priority: 100,
        Tmpls: []netlink.XfrmPolicyTmpl{{
            Src:   net.ParseIP("10.0.1.1"),
            Dst:   net.ParseIP("10.0.2.1"),
            Proto: netlink.XFRM_PROTO_ESP,
            Mode:  netlink.XFRM_MODE_TUNNEL,
            Spi:   int(spi),
            Reqid: 1,
        }},
    }
    return netlink.XfrmPolicyAdd(policy)
}
```

---

## Testing & Validation

### **Unit Tests (Kernel XFRM API)**

```bash
# Test SA installation
ip xfrm state add src 10.0.1.1 dst 10.0.2.1 proto esp spi 0x1000 \
  mode tunnel auth sha256 0x$(xxd -p -c 32 /dev/urandom | head -1) \
  enc aes 0x$(xxd -p -c 32 /dev/urandom | head -1)

ip xfrm state list
# Verify SPI, algorithms

# Test packet transformation
ip netns add test
ip link add veth0 type veth peer name veth1
ip link set veth1 netns test
# Configure IPs, routes, apply XFRM policy, ping, tcpdump

# Cleanup
ip xfrm state flush
ip xfrm policy flush
```

### **Integration Tests (strongSwan)**

```bash
# /etc/swanctl/swanctl.conf (VTI mode for testing)
connections {
    test-tunnel {
        local_addrs = 10.0.1.1
        remote_addrs = 10.0.2.1
        local {
            auth = psk
            id = 10.0.1.1
        }
        remote {
            auth = psk
            id = 10.0.2.1
        }
        children {
            test-child {
                mode = tunnel
                local_ts = 0.0.0.0/0
                remote_ts = 0.0.0.0/0
                esp_proposals = aes256gcm16-ecp256
                if_id_in = 42
                if_id_out = 42
            }
        }
        version = 2
        proposals = aes256-sha256-ecp256
    }
}

secrets {
    ike-test {
        id = 10.0.1.1
        secret = "test-psk-do-not-use-in-prod"
    }
}

# Create VTI interface
ip link add ipsec0 type vti key 42 local 10.0.1.1 remote 10.0.2.1
ip addr add 192.168.1.1/30 dev ipsec0
ip link set ipsec0 up

# Start tunnel
swanctl --load-all
swanctl --initiate --child test-child

# Test connectivity
ping 192.168.1.2
iperf3 -c 192.168.1.2
```

### **Fuzzing (IKE Parser)**

```bash
# Use AFL++ to fuzz IKE packet parser
# Example: strongSwan's charon daemon

# Build with AFL instrumentation
CC=afl-clang-fast ./configure --enable-test-vectors
make

# Create seed corpus (valid IKE packets)
mkdir seeds
tcpdump -w seeds/ike_init.pcap -c 1 'udp port 500'

# Fuzz
afl-fuzz -i seeds -o findings -- \
  ./src/libcharon/tests/test_ike_parser @@

# Monitor for crashes, hangs
# Typical findings: integer overflow, buffer overread
```

---

## Operational Playbook

### **Initial Setup (Site-to-Site VPN)**

```bash
# 1. Install strongSwan
apt-get install strongswan strongswan-pki libcharon-extra-plugins

# 2. Generate certificates (if using cert auth)
ipsec pki --gen --type ed25519 --outform pem > caKey.pem
ipsec pki --self --ca --lifetime 3650 --in caKey.pem \
  --dn "CN=VPN CA" --outform pem > caCert.pem

ipsec pki --gen --type ed25519 --outform pem > serverKey.pem
ipsec pki --pub --in serverKey.pem --type ed25519 | \
  ipsec pki --issue --lifetime 1825 --cacert caCert.pem \
  --cakey caKey.pem --dn "CN=vpn.example.com" --san vpn.example.com \
  --flag serverAuth --outform pem > serverCert.pem

# 3. Configure /etc/ipsec.conf (see examples above)

# 4. Add secrets to /etc/ipsec.secrets
: RSA serverKey.pem
# OR for PSK:
<local-ip> <remote-ip> : PSK "your-strong-psk"

# 5. Enable and start
systemctl enable strongswan
systemctl start strongswan

# 6. Initiate connection
ipsec up <connection-name>

# 7. Verify
ipsec statusall
ip xfrm state
ip xfrm policy
ping <remote-subnet-ip>
```

### **Monitoring (Production)**

```bash
# Prometheus exporter (strongSwan)
# https://github.com/dennisstritzke/ipsec_exporter

# Grafana dashboard metrics:
# - ipsec_sa_state (up/down)
# - ipsec_sa_bytes_in/out (throughput)
# - ipsec_ikev2_errors (auth failures, rekey failures)
# - ipsec_sa_rekey_time (PFS overhead)

# Alerting rules
- alert: IPSecTunnelDown
  expr: ipsec_sa_state{tunnel="aws-vpn-tunnel1"} == 0
  for: 5m
  annotations:
    summary: "IPSec tunnel {{ $labels.tunnel }} down"

- alert: IPSecHighRekeyRate
  expr: rate(ipsec_sa_rekey_total[5m]) > 0.1
  for: 10m
  annotations:
    summary: "Frequent IPSec rekeys on {{ $labels.tunnel }}"
```

### **Capacity Planning**

```bash
# Throughput budget (per tunnel, AES-GCM-256, AES-NI)
# - Single core: ~2.5 Gbps
# - Dual core: ~5 Gbps
# - NIC offload: ~10-40 Gbps

# SA limits (kernel)
sysctl net.xfrm.xfrm_acq_expires  # Default: 30s
sysctl net.xfrm.xfrm_aevent_etime # Default: 2s

# Typical limits:
# - 10,000 SAs per host (site-to-site)
# - 100,000 SAs per host (cloud-scale overlay with NIC offload)
# - 1,000,000 policies (routing table size limit)
```

---

## Next 3 Steps

1. **Deploy Test VPN**: Set up strongSwan site-to-site VPN between two VMs (or containers), use certificate-based auth, enable DPD, verify with `iperf3` and `tcpdump`, capture IKE handshake in Wireshark
2. **Implement IPSec in Go**: Use `vishvananda/netlink` to programmatically create XFRM states/policies, build a minimal IKE daemon or use existing IKE library (github.com/strongswan/strongswan-go), integrate with Prometheus metrics
3. **Benchmark & Optimize**: Compare AES-GCM vs ChaCha20-Poly1305, test with/without AES-NI, measure NIC offload impact (if available), run `openssl speed`, profile with `perf` to identify crypto bottlenecks

---

## References

- **RFCs**: 4301 (IPSec arch), 4303 (ESP), 7296 (IKEv2), 3947/3948 (NAT-T), 4868 (AEAD)
- **strongSwan Docs**: https://docs.strongswan.org
- **Linux XFRM**: https://www.kernel.org/doc/html/latest/networking/xfrm.html
- **Calico IPSec**: https://docs.tigera.io/calico/latest/network-policy/encrypt-cluster-pod-traffic
- **AWS VPN**: https://docs.aws.amazon.com/vpn/latest/s2svpn/VPC_VPN.html
- **GCP Cloud VPN**: https://cloud.google.com/network-connectivity/docs/vpn
- **Rust IPSec**: https://github.com/smoltcp-rs/smoltcp (user-space TCP/IP, IPSec WIP)
- **XFRM netlink (Go)**: https://github.com/vishvananda/netlink

# IPSec Exhaustive Deep-Dive: Complete Reference

**Extended Summary**: IPSec is a Layer 3 (network layer) security framework providing cryptographic protection for IP packets through a suite of protocols and mechanisms. Core components: ESP (RFC 4303) for confidentiality+integrity, AH (RFC 4302) for integrity-only, IKEv2 (RFC 7296) for automated key exchange and SA negotiation, SPD/SAD databases for policy and state management. Operates at kernel level with crypto offload to CPU (AES-NI) or NIC. Production deployment spans cloud interconnects (AWS VPN, GCP Cloud VPN, Azure VPN Gateway), container networking (Kubernetes CNI encryption via Calico/Cilium/Weave), SD-WAN overlays, and zero-trust architectures. Critical for compliance (PCI-DSS, HIPAA), data sovereignty, and defense-in-depth. Modern implementations leverage AEAD ciphers (AES-GCM, ChaCha20-Poly1305), elliptic curve DH (Curve25519), and hardware acceleration achieving 10-100 Gbps throughput with <1ms latency overhead.

---

## Extended Architecture & Component Interaction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Complete IPSec System Architecture                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                        User Space                                  │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │     │
│  │  │ IKE Daemon   │  │ Config Mgr   │  │  Monitoring  │            │     │
│  │  │ (charon/     │  │ (swanctl/    │  │ (Prometheus  │            │     │
│  │  │  pluto)      │  │  ipsec)      │  │  exporter)   │            │     │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘            │     │
│  │         │                 │                                        │     │
│  │         │ Netlink/        │ Netlink/                              │     │
│  │         │ PF_KEY          │ PF_KEY                                │     │
│  │         ▼                 ▼                                        │     │
│  └─────────┼─────────────────┼────────────────────────────────────────┘     │
│            │                 │                                               │
│  ══════════╪═════════════════╪═══════════════════════════════════════════   │
│            │                 │                                               │
│  ┌─────────┼─────────────────┼────────────────────────────────────────┐     │
│  │         │   Kernel Space  │                                        │     │
│  │         ▼                 ▼                                        │     │
│  │  ┌──────────────────────────────────────┐                         │     │
│  │  │        XFRM Framework                │                         │     │
│  │  │  ┌────────────┐  ┌─────────────┐    │                         │     │
│  │  │  │    SPD     │  │     SAD     │    │                         │     │
│  │  │  │  (Policy)  │  │   (State)   │    │                         │     │
│  │  │  └─────┬──────┘  └──────┬──────┘    │                         │     │
│  │  │        │                │            │                         │     │
│  │  │        │  Policy Lookup │            │                         │     │
│  │  │        ▼                ▼            │                         │     │
│  │  │  ┌──────────────────────────────┐   │                         │     │
│  │  │  │   XFRM State Machine         │   │                         │     │
│  │  │  │   - Acquire                  │   │                         │     │
│  │  │  │   - Transform (enc/dec)      │   │                         │     │
│  │  │  │   - Sequence number check    │   │                         │     │
│  │  │  └───────────┬──────────────────┘   │                         │     │
│  │  └──────────────┼──────────────────────┘                         │     │
│  │                 │                                                 │     │
│  │                 ▼                                                 │     │
│  │  ┌──────────────────────────────────────┐                        │     │
│  │  │      Crypto Subsystem                │                        │     │
│  │  │  ┌────────────┐  ┌─────────────┐    │                        │     │
│  │  │  │ Crypto API │  │  Algorithm  │    │                        │     │
│  │  │  │            │  │  Backends   │    │                        │     │
│  │  │  └─────┬──────┘  └──────┬──────┘    │                        │     │
│  │  │        │                │            │                        │     │
│  │  │        └────────┬───────┘            │                        │     │
│  │  │                 ▼                    │                        │     │
│  │  │  ┌──────────────────────────────┐   │                        │     │
│  │  │  │   Crypto Backends:           │   │                        │     │
│  │  │  │   - Software (generic)       │   │                        │     │
│  │  │  │   - AES-NI (x86)             │   │                        │     │
│  │  │  │   - ARMv8 Crypto             │   │                        │     │
│  │  │  │   - QAT (Intel accel)        │   │                        │     │
│  │  │  │   - CAAM (NXP)               │   │                        │     │
│  │  │  └──────────────────────────────┘   │                        │     │
│  │  └──────────────────────────────────────┘                        │     │
│  │                 │                                                 │     │
│  │                 ▼                                                 │     │
│  │  ┌──────────────────────────────────────┐                        │     │
│  │  │      Network Stack                   │                        │     │
│  │  │  ┌────────────┐  ┌─────────────┐    │                        │     │
│  │  │  │  Routing   │  │  Netfilter  │    │                        │     │
│  │  │  │  (FIB)     │  │  (iptables) │    │                        │     │
│  │  │  └─────┬──────┘  └──────┬──────┘    │                        │     │
│  │  │        │                │            │                        │     │
│  │  │        └────────┬───────┘            │                        │     │
│  │  │                 ▼                    │                        │     │
│  │  │  ┌──────────────────────────────┐   │                        │     │
│  │  │  │   Network Device Layer       │   │                        │     │
│  │  │  │   - Software (virtio/veth)   │   │                        │     │
│  │  │  │   - Hardware (physical NIC)  │   │                        │     │
│  │  │  └──────────────────────────────┘   │                        │     │
│  │  └──────────────────────────────────────┘                        │     │
│  │                 │                                                 │     │
│  └─────────────────┼─────────────────────────────────────────────────┘     │
│                    │                                                        │
│                    ▼                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │                    Hardware Layer                                │     │
│  │  ┌────────────────────────────────────────────────────────┐     │     │
│  │  │  NIC with IPSec Offload (Intel X710, Mellanox CX-5/6)  │     │     │
│  │  │  - Inline encryption/decryption                         │     │     │
│  │  │  - SA lookup in hardware                                │     │     │
│  │  │  - Sequence number checking                             │     │     │
│  │  │  - Checksum offload                                     │     │     │
│  │  └────────────────────────────────────────────────────────┘     │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Packet Flow (Outbound - Tunnel Mode):

Application
    │
    ▼
Socket Buffer (skb)
    │
    ▼
TCP/UDP Layer (add L4 header)
    │
    ▼
IP Layer (add original IP header)
    │
    ▼
Routing Decision (FIB lookup)
    │
    ▼
XFRM Policy Lookup (SPD)
    │  └──► BYPASS → skip IPSec
    │  └──► DISCARD → drop packet
    │  └──► PROTECT → continue
    ▼
XFRM State Lookup (SAD via SPI)
    │
    ▼
XFRM Transform
    │  ├─► Add outer IP header (tunnel mode)
    │  ├─► Add ESP header (SPI, seq)
    │  ├─► Encrypt payload (AES-GCM)
    │  ├─► Add ESP trailer (padding, next header)
    │  └─► Compute ICV (AEAD tag)
    ▼
Routing Decision (for outer IP)
    │
    ▼
Netfilter (iptables FORWARD/POSTROUTING)
    │
    ▼
Network Device (physical NIC or vNIC)
    │
    ▼
Physical Medium
```

---

## Complete Protocol Specifications

### 1. **ESP (Encapsulating Security Payload) - Exhaustive**

#### **Complete ESP Packet Structure**

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|               Security Parameters Index (SPI)                 | ─┐
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  │
|                      Sequence Number                          |  │ ESP
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  │ Header
|                    Payload Data* (variable)                   | ─┘ (Not
~                                                               ~    Encrypted)
|                                                               |
+               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ─┐
|               |     Padding (0-255 bytes)                     |  │
+-+-+-+-+-+-+-+-+               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  │
|                               |  Pad Length   | Next Header   |  │ ESP
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  │ Trailer
|         Integrity Check Value-ICV   (variable)                |  │ (Encrypted)
~                                                               ~ ─┘
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

* Payload Data: In tunnel mode = (Inner IP Header + Inner Packet)
                In transport mode = (TCP/UDP Header + Application Data)
```

#### **Field Descriptions**

| Field | Size | Description | Security Impact |
|-------|------|-------------|-----------------|
| **SPI** | 32 bits | Security Parameters Index - identifies SA in SAD | Lookup key for decryption; must be unique per (dest IP, protocol) |
| **Sequence Number** | 32 bits (or 64 bits with ESN) | Anti-replay counter, increments per packet | Prevents replay attacks; receiver tracks window |
| **Payload Data** | Variable | Encrypted inner packet | Confidentiality of actual data |
| **Padding** | 0-255 bytes | Align to cipher block size + TFC | Required for block ciphers; optional TFC padding obscures true packet length |
| **Pad Length** | 8 bits | Number of padding bytes | Receiver strips padding correctly |
| **Next Header** | 8 bits | Protocol of encapsulated packet (4=IP, 6=TCP, 17=UDP, 41=IPv6, 50=ESP) | Critical for decapsulation; wrong value = packet drop |
| **ICV** | Variable (96-256 bits) | Integrity Check Value / Authentication Tag | AEAD tag (GCM) or HMAC; tampering detected |

#### **Encryption & Authentication Coverage**

```
Non-AEAD (CBC + HMAC):
┌──────────┬──────────┬──────────────────────────────────┬──────────┐
│   SPI    │   Seq    │   Encrypted Payload + Trailer    │   ICV    │
└──────────┴──────────┴──────────────────────────────────┴──────────┘
└──────────── Authenticated (HMAC input) ──────────────────────────┘
             └────────── Encrypted (Cipher input) ─────────┘

AEAD (GCM/ChaCha20-Poly1305):
┌──────────┬──────────┬──────────────────────────────────┬──────────┐
│   SPI    │   Seq    │   Encrypted Payload + Trailer    │   Tag    │
└──────────┴──────────┴──────────────────────────────────┴──────────┘
└────────── Additional Authenticated Data (AAD) ──────┘
             └────────── Encrypted ─────────┘
             └────────────── Authenticated (tag covers both) ───────┘
```

#### **Padding Calculation**

```c
// Block cipher (AES-CBC) - must align to block size (16 bytes)
pad_length = (block_size - ((payload_length + 2) % block_size)) % block_size;

// AEAD (AES-GCM) - no strict requirement, but align to 4-byte boundary
pad_length = (4 - ((payload_length + 2) % 4)) % 4;

// Traffic Flow Confidentiality (TFC) - add extra random padding
// to obscure packet size patterns
tfc_pad = random(0, max_tfc_padding);
total_pad = pad_length + tfc_pad;

// Padding content: can be zeros or random bytes
// Random preferred for side-channel resistance
```

#### **Extended Sequence Number (ESN) - RFC 4304**

```
Problem: 32-bit sequence number wraps after 2^32 packets
         @ 10 Gbps with 1500-byte packets = ~51 minutes

Solution: 64-bit sequence number (ESN)
         Only lower 32 bits transmitted; higher 32 bits implicit

Sender:
  seq_low = seq_counter & 0xFFFFFFFF;
  seq_high = (seq_counter >> 32) & 0xFFFFFFFF;
  // Transmit only seq_low in ESP header

Receiver:
  // Reconstruct full 64-bit sequence
  if (seq_low < expected_seq_low) {
      seq_high = expected_seq_high + 1;  // Wrapped
  } else {
      seq_high = expected_seq_high;
  }
  full_seq = (seq_high << 32) | seq_low;
  
  // Anti-replay check
  if (full_seq <= highest_seq_received) {
      if (is_in_replay_window(full_seq)) {
          drop_packet();  // Replay
      }
  }
```

#### **Anti-Replay Window Implementation**

```c
#define REPLAY_WINDOW_SIZE 64  // Typical: 32, 64, 128, 256

struct replay_state {
    uint64_t seq_highest;      // Highest sequence seen
    uint64_t window_bitmap;    // Bitmap of received packets
};

int check_replay(struct replay_state *state, uint64_t seq) {
    if (seq == 0) return -1;  // Invalid
    
    if (seq > state->seq_highest) {
        // New packet, ahead of window
        uint64_t diff = seq - state->seq_highest;
        if (diff < REPLAY_WINDOW_SIZE) {
            // Shift window
            state->window_bitmap <<= diff;
            state->window_bitmap |= 1;
        } else {
            // Far ahead, reset window
            state->window_bitmap = 1;
        }
        state->seq_highest = seq;
        return 0;  // Accept
    }
    
    uint64_t diff = state->seq_highest - seq;
    if (diff >= REPLAY_WINDOW_SIZE) {
        return -1;  // Too old, outside window
    }
    
    // Check if already received
    if (state->window_bitmap & (1ULL << diff)) {
        return -1;  // Duplicate
    }
    
    // Mark as received
    state->window_bitmap |= (1ULL << diff);
    return 0;  // Accept
}
```

### 2. **AH (Authentication Header) - Complete Spec**

**Why AH is Obsolete in Production**:
- Cannot traverse NAT (authenticates immutable IP header fields)
- No confidentiality (plaintext transmission)
- ESP with null encryption provides same functionality with NAT-T support
- Most modern deployments use ESP-only

**AH Header Structure** (for reference):
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Next Header   |  Payload Len  |          RESERVED             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Security Parameters Index (SPI)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Sequence Number Field                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                Integrity Check Value-ICV (variable)           |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Authenticated Fields**:
- Entire IP header (with mutable fields zeroed: TTL, TOS, header checksum)
- AH header
- Upper-layer protocol data

**NAT Incompatibility**:
```
Original packet:
  IP[src=10.0.1.5, dst=10.0.2.5] | AH[ICV=hash(...)] | TCP | Data

After NAT:
  IP[src=203.0.113.1, dst=10.0.2.5] | AH[ICV=hash(...)] | TCP | Data
                                         ↑
                                    ICV still covers original src IP
                                    → Verification fails at receiver
```

### 3. **IKEv2 (Internet Key Exchange v2) - Complete Protocol**

#### **IKEv2 State Machine**

```
Initiator State                    Responder State
────────────────────────────────────────────────────────

IDLE                               IDLE
  │                                  │
  │ Send IKE_SA_INIT               │
  ├─────────────────────────────────►│
  │                                  │ Receive IKE_SA_INIT
  │                                  │ Verify, generate DH
  │                                  │ Send IKE_SA_INIT response
  │◄─────────────────────────────────┤
  │ Receive IKE_SA_INIT response     │
  │ Verify, compute DH shared secret │
  │ Derive keys (SKEYSEED, SK_*)     │ Derive keys
  │                                  │
INIT_DONE                          INIT_DONE
  │                                  │
  │ Send IKE_AUTH                   │
  │ (encrypted with SK_ei)           │
  ├─────────────────────────────────►│
  │                                  │ Receive IKE_AUTH
  │                                  │ Decrypt, verify AUTH payload
  │                                  │ Authenticate peer (cert/PSK)
  │                                  │ Create CHILD_SA
  │                                  │ Send IKE_AUTH response
  │◄─────────────────────────────────┤
  │ Receive IKE_AUTH response        │
  │ Verify AUTH payload              │
  │ Create CHILD_SA                  │
  │                                  │
ESTABLISHED                        ESTABLISHED
  │                                  │
  │ ◄──── IPSec Traffic ────►        │
  │                                  │
  │ (After lifetime/rekey trigger)   │
  │ Send CREATE_CHILD_SA            │
  ├─────────────────────────────────►│
  │                                  │ Install new SA
  │◄─────────────────────────────────┤ Send CREATE_CHILD_SA response
  │ Install new SA                   │
  │ Delete old SA after grace period │ Delete old SA
  │                                  │
  │ (Dead Peer Detection)            │
  │ Send INFORMATIONAL (empty)      │
  ├─────────────────────────────────►│
  │◄─────────────────────────────────┤ Send INFORMATIONAL (empty)
  │                                  │
  │ (Teardown)                       │
  │ Send INFORMATIONAL (DELETE)     │
  ├─────────────────────────────────►│
  │                                  │ Delete SAs
  │◄─────────────────────────────────┤ Send INFORMATIONAL (DELETE)
  │ Delete SAs                       │
  ▼                                  ▼
IDLE                               IDLE
```

#### **IKE_SA_INIT Exchange - Detailed**

```
Initiator                                                    Responder
─────────────────────────────────────────────────────────────────────

(1) IKE_SA_INIT Request:
HDR(IKE_SA_INIT, 0x0000000000000000, 0x0000000000000000)
  SAi1(Crypto suite proposals)
  KEi(Key Exchange - DH public key)
  Ni(Nonce - random value, 16-32 bytes)
  [N(NAT_DETECTION_SOURCE_IP)]
  [N(NAT_DETECTION_DESTINATION_IP)]
  [N(FRAGMENTATION_SUPPORTED)]
─────────────────────────────────────────────────────────────►

                                              (2) Process:
                                              - Verify proposals
                                              - Select crypto suite
                                              - Generate DH keypair
                                              - Generate Nr (nonce)
                                              - Check NAT detection hashes

◄─────────────────────────────────────────────────────────────
(3) IKE_SA_INIT Response:
HDR(IKE_SA_INIT, SPIi, SPIr)
  SAr1(Selected crypto suite)
  KEr(DH public key)
  Nr(Nonce)
  [N(NAT_DETECTION_SOURCE_IP)]
  [N(NAT_DETECTION_DESTINATION_IP)]
  [CERTREQ(CA distinguished names)]
  [N(FRAGMENTATION_SUPPORTED)]

(4) Process:
- Verify response
- Compute DH shared secret: g^ir = (g^r)^i
- Derive SKEYSEED = prf(Ni | Nr, g^ir)
- Derive SK_d, SK_ai, SK_ar, SK_ei, SK_er, SK_pi, SK_pr
```

**Crypto Suite Proposal Format**:
```
SAi1 = {
  Proposal 1: {
    Protocol: IKE
    Transform Types:
      ENCR: AES-GCM-256 (key length: 256)
      PRF:  HMAC-SHA2-512
      INTEG: (none - integrated in AEAD)
      DH:   Curve25519 (Group 31) or secp256r1 (Group 19)
  }
  Proposal 2: {
    Protocol: IKE
    Transform Types:
      ENCR: AES-CBC-256
      PRF:  HMAC-SHA2-256
      INTEG: HMAC-SHA2-256-128
      DH:   MODP-2048 (Group 14)
  }
}
```

#### **IKE_AUTH Exchange - Detailed**

```
Initiator                                                    Responder

(5) IKE_AUTH Request (encrypted with SK_ei, authenticated with SK_ai):
HDR(IKE_AUTH)
SK {
  IDi(Initiator identity: IP, FQDN, email, or DN)
  [CERT(Initiator certificate)]
  [CERTREQ(Request responder cert)]
  AUTH(Proof of IDi's private key)
  SAi2(Child SA proposals for IPSec)
  TSi(Traffic Selectors - initiator)
  TSr(Traffic Selectors - responder)
  [N(USE_TRANSPORT_MODE)]
  [N(ESP_TFC_PADDING_NOT_SUPPORTED)]
  [CP(CFG_REQUEST)] // For config payload (IP assignment)
}
─────────────────────────────────────────────────────────────►

                                              (6) Process:
                                              - Decrypt with SK_er
                                              - Verify integrity with SK_ar
                                              - Verify certificate chain
                                              - Verify AUTH payload
                                              - Check traffic selectors
                                              - Select Child SA proposal

◄─────────────────────────────────────────────────────────────
(7) IKE_AUTH Response:
HDR(IKE_AUTH)
SK {
  IDr(Responder identity)
  [CERT(Responder certificate)]
  AUTH(Proof of IDr's private key)
  SAr2(Selected Child SA proposal)
  TSi(Accepted traffic selectors)
  TSr(Accepted traffic selectors)
  [CP(CFG_REPLY)] // Assigned IP, DNS, etc.
}

(8) Process:
- Decrypt, verify
- Verify responder certificate and AUTH
- Install IPSec SA (CHILD_SA) into kernel SAD
- Install SPD entries for traffic selectors
```

**AUTH Payload Computation**:

```python
# PSK authentication
AUTH = prf(prf(PSK, "Key Pad for IKEv2"), <InitiatorSignedOctets>)

# Certificate authentication (RSA/ECDSA)
AUTH = Sign(private_key, <InitiatorSignedOctets>)

# InitiatorSignedOctets (simplified):
InitiatorSignedOctets = RealMessage1 | NonceRData | prf(SK_pi, IDi')

RealMessage1 = First message sent (IKE_SA_INIT request)
NonceRData = Responder's nonce (Nr)
SK_pi = Derived key for authentication payload
IDi' = IDi payload body (without generic header)
```

#### **Traffic Selectors (TS)**

```
Traffic Selector:
┌────────────────────────────────────────────────┐
│ TS Type: IPv4 address range = 7               │
│ IP Protocol ID: 0 (any), 6 (TCP), 17 (UDP)    │
│ Selector Length: 16 bytes                     │
│ Start Port: 0-65535 (0 = any)                 │
│ End Port: 0-65535 (65535 = any)               │
│ Starting Address: 10.0.1.0                    │
│ Ending Address: 10.0.1.255                    │
└────────────────────────────────────────────────┘

Example:
TSi = {
  { IPv4, protocol=any, port=any, range=10.0.1.0-10.0.1.255 },
  { IPv4, protocol=TCP, port=443, range=10.0.1.5 }
}

TSr = {
  { IPv4, protocol=any, port=any, range=10.0.2.0-10.0.2.255 }
}

Narrowing: Responder can narrow (subset) but not widen
Accepted TSi must be subset of proposed TSi
```

#### **Perfect Forward Secrecy (PFS) in Rekeying**

```
Without PFS (CREATE_CHILD_SA without KEi/KEr):
- New CHILD_SA keys derived from existing IKE_SA's SK_d
- Compromise of SK_d exposes all past and future CHILD_SAs

With PFS (CREATE_CHILD_SA with KEi/KEr):
- New DH exchange for each CHILD_SA rekey
- New keys independent of previous CHILD_SAs
- Compromise limited to single SA window

Initiator:
CREATE_CHILD_SA Request:
  SA (new proposals)
  Ni (new nonce)
  KEi (new DH public key) ← PFS enabled
  TSi, TSr

Responder:
CREATE_CHILD_SA Response:
  SA (selected)
  Nr (new nonce)
  KEr (new DH public key) ← PFS enabled
  TSi, TSr

Key derivation:
KEYMAT = prf+(SK_d, g^ir(new) | Ni | Nr)
```

#### **Dead Peer Detection (DPD)**

```
Mechanism 1: IKE liveness check (INFORMATIONAL exchange)
Initiator:                    Responder:
  INFORMATIONAL {} ─────────►
                  ◄───────── INFORMATIONAL {}

Timeout: 30-60s typical
Action on failure: restart, clear, hold

Mechanism 2: ESP heartbeat
- Send empty ESP packets at interval (not standardized)
- Check for response traffic

strongSwan config:
  dpdaction=restart  # restart, clear, hold
  dpddelay=30s       # Check interval
  dpdtimeout=150s    # Max time without response
```

#### **NAT Detection & UDP Encapsulation**

```
NAT Detection in IKE_SA_INIT:

Initiator sends:
  N(NAT_DETECTION_SOURCE_IP) = HASH(SPIi | SPIr | IP_src | Port_src)
  N(NAT_DETECTION_DESTINATION_IP) = HASH(SPIi | SPIr | IP_dst | Port_dst)

Responder:
  1. Computes expected hashes based on received packet's IP/port
  2. Compares with NAT_DETECTION payloads
  3. If mismatch → NAT detected

If NAT detected:
  - Switch from UDP:500 to UDP:4500 (NAT-T port)
  - Encapsulate ESP in UDP:
    
    [IP header][UDP:4500][Non-ESP Marker: 4 bytes of 0x00][ESP packet]
    
  - Non-ESP Marker distinguishes IKE (no marker) from ESP (marker present)
  - Send keepalives every 20s to maintain NAT mapping

Keepalive packet:
  1 byte: 0xFF (UDP payload on port 4500, not ESP)
```

---

## Cryptographic Deep Dive

### **AEAD Cipher Operations (AES-GCM)**

**AES-GCM (Galois/Counter Mode) - RFC 5116, RFC 4106**

```
Encryption Process:

Inputs:
  K:     Encryption key (128/192/256 bits)
  IV:    Initialization Vector / Nonce (12 bytes for IPSec)
  P:     Plaintext
  A:     Additional Authenticated Data (AAD) = ESP header (SPI + Seq)

Outputs:
  C:     Ciphertext (same length as P)
  T:     Authentication tag (96/128 bits)

Algorithm:
  1. Derive counter block (CB):
     CB[0:95]   = IV (96 bits)
     CB[96:127] = 0x00000001
  
  2. Generate keystream and encrypt:
     For i = 0 to n-1:
       counter = CB + i
       keystream_block[i] = AES_Encrypt(K, counter)
     C = P ⊕ keystream
  
  3. Compute authentication tag:
     H = AES_Encrypt(K, 0^128)  // Hash subkey
     
     // GHASH function over GF(2^128)
     GHASH(H, A, C) = (((A || 0^s || C || 0^t || len(A) || len(C)) • H^m)
     
     Where • is multiplication in GF(2^128)
     
     T = GHASH(H, A, C) ⊕ AES_Encrypt(K, CB)

Decryption Process:
  1. Compute authentication tag T' on received (A, C)
  2. Constant-time compare T' with received T
  3. If match: Decrypt C to get P
  4. If mismatch: Drop packet, log authentication failure

Security Properties:
  - Confidentiality: AES-CTR mode (semantic security under CPA)
  - Integrity: GHASH (unforgeable under chosen message attack)
  - AEAD: Combined mode prevents encrypt-then-MAC timing attacks
  - Nonce reuse: CATASTROPHIC - exposes keystream and authentication key H
```

**Implementation Considerations**:

```c
// Linux kernel: crypto/gcm.c
// Hardware acceleration: AES-NI + PCLMULQDQ (carry-less multiplication)

// AES-NI accelerated AES-GCM (Intel)
// - AES encryption: ~0.7 cycles/byte
// - GHASH (PCLMULQDQ): ~3.5 cycles/byte
// - Total: ~5-6 cycles/byte = 3-4 GB/s @ 3 GHz

// Performance comparison (single core @ 3 GHz):
// Software AES-GCM: ~200 MB/s
// AES-NI AES-GCM:   ~3 GB/s
// NIC offload:      ~10-100 GB/s (line rate)

// Constant-time tag verification (critical for side-channel resistance):
int crypto_memneq(const void *a, const void *b, size_t size) {
    const unsigned char *_a = a;
    const unsigned char *_b = b;
    unsigned char diff = 0;
    while (size--) {
        diff |= *_a++ ^ *_b++;
    }
    return diff != 0;
}
```

### **ChaCha20-Poly1305 - RFC 7539, RFC 7634**

```
Why ChaCha20-Poly1305:
  - Software-friendly (no AES-NI required)
  - Constant-time (no table lookups, resistant to cache-timing attacks)
  - Performance: ~2-3 cycles/byte on modern CPUs (competitive with AES-GCM on non-AES-NI)
  - Mobile/ARM: Often faster than AES

Algorithm:
  Encryption:
    C = ChaCha20(K, nonce, plaintext)
    
  Authentication:
    T = Poly1305(K_mac, AAD || padding || C || padding || lengths)
    
  Where:
    K_mac = ChaCha20(K, nonce, counter=0)[0:256]  // First block for MAC key

ChaCha20 Quarter Round:
  a += b; d ^= a; d <<<= 16;
  c += d; b ^= c; b <<<= 12;
  a += b; d ^= a; d <<<= 8;
  c += d; b ^= c; b <<<= 7;

Poly1305:
  // Computes tag = ((msg * r^n) + (msg * r^(n-1)) + ... + (msg * r)) mod (2^130 - 5)
  // r, s derived from 256-bit key
  // Constant-time implementation critical
```

**Performance**:
```bash
# Benchmark (OpenSSL)
openssl speed -evp chacha20-poly1305
# Typical: 1.5-2.5 GB/s per core (software)

# vs AES-GCM (with AES-NI)
openssl speed -evp aes-256-gcm
# Typical: 3-4 GB/s per core

# ARM64 (Graviton3):
# ChaCha20-Poly1305: ~2 GB/s
# AES-GCM: ~1.5 GB/s (without crypto extensions)
# AES-GCM: ~8 GB/s (with ARMv8 crypto extensions)
```

### **Key Derivation (IKEv2)**

**SKEYSEED and SK Derivation**:

```python
# RFC 5996 Section 2.14

# Step 1: Compute DH shared secret
g_ir = modular_exponentiation(g, i * r, p)  # For MODP groups
# OR
g_ir = scalar_multiplication(g, i * r)      # For ECP groups (Curve25519)

# Step 2: Derive SKEYSEED
SKEYSEED = prf(Ni | Nr, g_ir)

# PRF choices:
# - PRF_HMAC_SHA2_256: HMAC-SHA-256 (most common)
# - PRF_HMAC_SHA2_512: HMAC-SHA-512
# - PRF_AES128_XCBC: AES-XCBC-PRF-128

# Step 3: Derive keying material
{SK_d | SK_ai | SK_ar | SK_ei | SK_er | SK_pi | SK_pr}
    = prf+(SKEYSEED, Ni | Nr | SPIi | SPIr)

# prf+ expands SKEYSEED to required length:
def prf_plus(K, S, desired_length):
    """
    Expand key K with seed S to desired_length bytes
    T1 = prf(K, S | 0x01)
    T2 = prf(K, T1 | S | 0x02)
    T3 = prf(K, T2 | S | 0x03)
    ...
    return T1 | T2 | T3 | ... (truncated to desired_length)
    """
    result = b''
    temp = b''
    counter = 1
    while len(result) < desired_length:
        temp = hmac(K, temp + S + bytes([counter]))
        result += temp
        counter += 1
    return result[:desired_length]

# Key lengths (for AES-256-GCM + SHA-256):
# SK_d:  256 bits (for deriving CHILD_SA keys)
# SK_ai: 256 bits (IKE integrity - initiator to responder)
# SK_ar: 256 bits (IKE integrity - responder to initiator)
# SK_ei: 256 bits (IKE encryption - initiator to responder)
# SK_er: 256 bits (IKE encryption - responder to initiator)
# SK_pi: 256 bits (IKE auth payload - initiator)
# SK_pr: 256 bits (IKE auth payload - responder)

# Step 4: Derive CHILD_SA (IPSec ESP) keys
KEYMAT = prf+(SK_d, Ni | Nr)
# OR with PFS (new DH exchange):
KEYMAT = prf+(SK_d, g_ir(new) | Ni | Nr)

# Split KEYMAT:
SK_ei_child = KEYMAT[0:key_length]
SK_ai_child = KEYMAT[key_length:key_length+integ_key_length]
SK_er_child = KEYMAT[...] 
SK_ar_child = KEYMAT[...]

# For AEAD (AES-GCM), only encryption keys needed:
SK_ei_child = KEYMAT[0:32]   # 256-bit AES key
SK_er_child = KEYMAT[32:64]  # 256-bit AES key
```

### **Diffie-Hellman Groups**

```
Group 14 (MODP-2048):
  p = 2048-bit prime (OAKLEY group)
  g = 2
  Security: ~112-bit equivalent (minimum acceptable)
  Performance: Slow (~10ms per operation)
  Status: Being phased out

Group 19 (ECP256 / secp256r1 / P-256):
  Curve: y^2 = x^3 - 3x + b (mod p)
  Prime: 2^256 - 2^224 + 2^192 + 2^96 - 1
  Security: 128-bit
  Performance: Fast (~1ms)
  Status: Widely supported, but concerns about NSA influence on constants

Group 31 (Curve25519):
  Curve: y^2 = x^3 + 486662x^2 + x (mod 2^255 - 19)
  Security: 128-bit
  Performance: Very fast (~0.5ms), constant-time implementation
  Status: Preferred for new deployments
  Advantage: Designed for security, no magic constants

Group 20 (ECP384 / secp384r1):
  Security: 192-bit
  Performance: Medium (~2ms)
  Use case: High-security requirements (government, classified)

Post-Quantum Groups (Experimental):
  - Kyber512/768/1024 (lattice-based KEM)
  - NTRU
  - Hybrid: Classical DH + PQ KEM
  Status: Not yet standardized for IKEv2
```

**DH Operation Benchmarks**:
```bash
openssl speed ecdhp256  # Group 19
#  256-bit ECDH: ~2000 ops/sec = 0.5ms/op

openssl speed ecdhx25519  # Group 31 (Curve25519)
#  X25519: ~4000 ops/sec = 0.25ms/op

# DH affects IKE_SA_INIT latency (round-trip time + 2x DH compute)
# Typical: 10-50ms depending on group and CPU
```

### **Certificate Validation & PKI**

```
Certificate Chain Verification:
  1. Parse X.509 certificate
  2. Verify signature chain up to trusted root CA
  3. Check validity period (not_before, not_after)
  4. Check revocation status (CRL or OCSP)
  5. Verify key usage extensions (digitalSignature, keyEncipherment)
  6. Check subject alternative names (SAN) against peer ID

OCSP (Online Certificate Status Protocol) - RFC 6960:
  - Real-time revocation checking
  - Query: Hash(Issuer) | Serial Number
  - Response: Good | Revoked | Unknown
  - OCSP Stapling: Server provides OCSP response with certificate
    (reduces latency, privacy-preserving)

CRL (Certificate Revocation List):
  - Periodically published list of revoked certificates
  - Downloaded and cached locally
  - Check serial number against CRL
  - Problem: CRL can grow large, stale

strongSwan Certificate Pinning:
  connections {
    vpn {
      remote {
        certs = vpn-server.crt  # Pin specific certificate
        # OR
        cacerts = ca.crt        # Pin CA
        # OR
        pubkeys = server.pub    # Pin public key (HPKP-style)
      }
    }
  }

Short-lived Certificates (Recommended):
  - Issue certs with 24-48 hour validity
  - Automated renewal (ACME protocol / Let's Encrypt)
  - Eliminates need for revocation checking
  - Reduces blast radius of key compromise
```

---

## Kernel Implementation Deep Dive (Linux XFRM)

### **XFRM Architecture**

```c
// Linux kernel: net/xfrm/

Key structures:

// Security Association (SA)
struct xfrm_state {
    struct xfrm_id          id;              // (daddr, spi, proto)
    struct xfrm_selector    sel;             // Traffic selector
    struct xfrm_lifetime_cfg lft;            // Lifetime limits
    struct xfrm_algo        *aalg;           // Auth algorithm
    struct xfrm_algo        *ealg;           // Encryption algorithm
    struct xfrm_algo_aead   *aead;           // AEAD algorithm
    
    u32  replay_window;                      // Anti-replay window size
    struct xfrm_replay_state replay;         // Replay state
    struct xfrm_replay_state_esn replay_esn; // Extended seq number
    
    atomic_t  refcnt;                        // Reference count
    spinlock_t lock;                         // Concurrent access
    
    u8   mode;                               // Tunnel or transport
    u8   flags;                              // Align, ESN, etc.
};

// Security Policy
struct xfrm_policy {
    struct xfrm_selector   selector;         // src/dst/port/proto
    u32                    priority;         // Lookup order
    u8                     dir;              // in/out/fwd
    u8                     action;           // allow/block
    struct xfrm_tmpl       *xfrm_vec;        // Template for SA
    int                    xfrm_nr;          // Number of SAs (for bundling)
};

// Packet transformation
struct xfrm_state_afinfo {
    int  (*output)(struct xfrm_state *, struct sk_buff *);
    int  (*extract_input)(struct xfrm_state *, struct sk_buff *);
    int  (*extract_output)(struct xfrm_state *, struct sk_buff *);
    int  (*transport_finish)(struct sk_buff *, int);
};
```

### **Packet Processing Flow**

```
Outbound Packet Processing (xfrm_output):

1. IP layer routing decision
   ↓
2. xfrm_lookup() - Policy (SPD) lookup
   ├─► BYPASS: Skip to step 7
   ├─► DISCARD: Drop packet
   └─► PROTECT: Continue
   ↓
3. xfrm_bundle_lookup() - Find SA bundle
   ├─► SA exists: Continue
   └─► No SA: Trigger IKE ACQUIRE, queue packet
   ↓
4. xfrm_state_check_expire() - Check SA lifetime
   ├─► Expired: Delete SA, trigger rekey
   └─► Valid: Continue
   ↓
5. xfrm_output_one() - Transform packet
   ├─► Add outer IP header (tunnel mode)
   ├─► Add ESP header (SPI, sequence number)
   ├─► Increment sequence number (atomic)
   ├─► Encrypt payload (crypto API)
   ├─► Add padding and trailer
   └─► Compute ICV/tag
   ↓
6. Check MTU, fragment if necessary
   ↓
7. xfrm_output_resume() - Continue to network device
   ↓
8. dev_queue_xmit() - Send to NIC

Inbound Packet Processing (xfrm_input):

1. NIC receives packet
   ↓
2. IP layer decodes header
   ↓
3. Identify ESP packet (protocol=50)
   ↓
4. xfrm_input() - Look up SA by (daddr, SPI, proto)
   ├─► SA not found: Drop, increment error counter
   └─► SA found: Continue
   ↓
5. xfrm_state_check_expire() - Check SA lifetime
   ↓
6. Extract sequence number, check anti-replay
   ├─► Duplicate: Drop
   ├─► Outside window: Drop
   └─► Valid: Update replay state
   ↓
7. Decrypt and verify (crypto API)
   ├─► ICV mismatch: Drop, log auth failure
   └─► Valid: Continue
   ↓
8. Remove ESP header/trailer, extract inner packet
   ↓
9. Tunnel mode: Replace outer IP with inner IP
   ↓
10. xfrm_input_resume() - Continue to upper layer
    ↓
11. TCP/UDP layer processes packet
```

### **Crypto API Integration**

```c
// Crypto transformation
struct crypto_aead *aead;
struct aead_request *req;

// Allocate AEAD transform
aead = crypto_alloc_aead("rfc4106(gcm(aes))", 0, 0);
crypto_aead_setkey(aead, key, key_len);
crypto_aead_setauthsize(aead, icv_len);

// Setup request
req = aead_request_alloc(aead, GFP_KERNEL);
aead_request_set_callback(req, 0, crypto_complete, &result);
aead_request_set_crypt(req, sg_in, sg_out, cryptlen, iv);
aead_request_set_ad(req, assoclen);

// Encrypt
crypto_aead_encrypt(req);

// Decrypt & verify
crypto_aead_decrypt(req);

// Hardware offload (if available)
// Crypto API automatically selects:
// 1. Hardware driver (e.g., aesni-intel, qat)
// 2. Software fallback (generic-gcm-aesni)
```

### **Netlink Interface (User↔Kernel)**

```c
// User-space tool (ip xfrm) communicates via Netlink

// Add SA
struct xfrm_usersa_info {
    struct xfrm_selector   sel;
    struct xfrm_id         id;
    xfrm_address_t         saddr;
    struct xfrm_lifetime_cfg lft;
    struct xfrm_lifetime_cur curlft;
    struct xfrm_stats      stats;
    __u32                  seq;
    __u32                  reqid;
    __u16                  family;
    __u8                   mode;    // XFRM_MODE_TRANSPORT=0, XFRM_MODE_TUNNEL=1
    __u8                   replay_window;
    __u8                   flags;
};

// Netlink message
struct nlmsghdr {
    __u32  nlmsg_len;    // Length of message including header
    __u16  nlmsg_type;   // XFRM_MSG_NEWSA, XFRM_MSG_DELSA, etc.
    __u16  nlmsg_flags;  // NLM_F_REQUEST, NLM_F_ACK, etc.
    __u32  nlmsg_seq;    // Sequence number
    __u32  nlmsg_pid;    // Sending process PID
};

// Example: Add SA using netlink (simplified Go code)
import "github.com/vishvananda/netlink"

state := &netlink.XfrmState{
    Src:   net.ParseIP("10.0.1.1"),
    Dst:   net.ParseIP("10.0.2.1"),
    Proto: netlink.XFRM_PROTO_ESP,
    Mode:  netlink.XFRM_MODE_TUNNEL,
    Spi:   0x12345678,
    Aead: &netlink.XfrmStateAlgo{
        Name:   "rfc4106(gcm(aes))",
        Key:    key,  // 32 bytes AES-256 + 4 bytes salt
        ICVLen: 128,
    },
    Reqid: 1,
}
netlink.XfrmStateAdd(state)
```

---

## Advanced Deployment Scenarios

### **1. High-Availability IPSec Gateway (Active-Passive)**

```
Architecture:
┌──────────────┐      ┌──────────────┐
│  Gateway 1   │      │  Gateway 2   │
│  (Active)    │      │  (Standby)   │
│  10.0.1.1    │      │  10.0.1.2    │
└──────┬───────┘      └──────┬───────┘
       │                     │
       └──────────┬──────────┘
                  │
            Virtual IP: 10.0.1.254
                  │
            ┌─────┴─────┐
            │  Internet │
            └───────────┘

Components:
- Keepalived (VRRP for Virtual IP failover)
- Shared SPD/SAD (synchronized via Netlink or database)
- Session state replication (for stateful failover)

# /etc/keepalived/keepalived.conf (Gateway 1)
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass secretpass
    }
    virtual_ipaddress {
        10.0.1.254/24
    }
    notify_master "/usr/local/bin/ipsec-takeover.sh master"
    notify_backup "/usr/local/bin/ipsec-takeover.sh backup"
}

# /usr/local/bin/ipsec-takeover.sh
#!/bin/bash
case "$1" in
    master)
        # Take over IPSec SAs (if using ClusterIP)
        ipsec reload
        ipsec up all
        # Send gratuitous ARP
        arping -c 3 -S 10.0.1.254 -I eth0 10.0.1.1
        ;;
    backup)
        ipsec down all
        ;;
esac
```

**Session State Synchronization**:
```bash
# Option 1: Stateless (recommended)
# - No session sync needed
# - Remote peer reconnects on failover (DPD triggers)
# - Downtime: 30-60s (DPD timeout)

# Option 2: Stateful with conntrackd
# Sync SA sequence numbers and connection state
apt-get install conntrackd

# /etc/conntrackd/conntrackd.conf
Sync {
    Mode FTFW {
        ResendQueueSize 131072
        PurgeTimeout 60
        ACKWindowSize 300
    }
    Multicast {
        IPv4_address 225.0.0.50
        Group 3780
        IPv4_interface 10.0.1.0
        Interface eth1
        SndSocketBuffer 1249280
        RcvSocketBuffer 1249280
        Checksum on
    }
}
```

### **2. Kubernetes Multi-Cluster with Cilium IPSec**

```yaml
# Cluster 1 (us-east-1)
apiVersion: v1
kind: ConfigMap
metadata:
  name: cilium-config
  namespace: kube-system
data:
  enable-ipsec: "true"
  ipsec-key-file: /etc/ipsec/keys
  encrypt-interface: eth0
  encrypt-node: "true"
  
---
apiVersion: v1
kind: Secret
metadata:
  name: cilium-ipsec-keys
  namespace: kube-system
type: Opaque
stringData:
  keys: |
    3 rfc4106(gcm(aes)) $(openssl rand -hex 20) 128
    # Format: <key-id> <algorithm> <hex-key> <icv-length>
    # Key rotation: Add new key with incremented ID, old keys remain for grace period

# Cilium automatically:
# 1. Creates node-to-node IPSec tunnels
# 2. Encrypts pod-to-pod traffic
# 3. Rotates keys based on key-id

# Verify encryption
kubectl -n kube-system exec -ti cilium-xxxxx -- cilium encrypt status
# Expected output:
# Encryption: IPSec
# Keys in use: 1
# Max Seq. Number: 0xffffffff (4294967295)
# Errors: 0

# Check XFRM states
kubectl -n kube-system exec -ti cilium-xxxxx -- ip xfrm state
```

**ClusterMesh with IPSec**:
```bash
# Enable ClusterMesh
cilium clustermesh enable

# Connect clusters
cilium clustermesh connect --destination-context cluster-2

# Cilium creates:
# - IPSec tunnels between cluster nodes
# - Encrypted pod-to-pod across clusters
# - Traffic: Pod (cluster-1) → Node IPSec → Node (cluster-2) → Pod (cluster-2)

# Verify cross-cluster connectivity
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- \
  curl http://svc.namespace.svc.clusterset.local
```

### **3. SD-WAN with IPSec + BGP (Multi-Path)**

```
Architecture:
           ┌──────────────┐
           │ Branch Site  │
           │  10.1.0.0/16 │
           └───────┬──────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ISP 1      ISP 2      LTE
  (Tunnel 1) (Tunnel 2) (Tunnel 3)
        │          │          │
        └──────────┼──────────┘
                   │
           ┌───────┴──────┐
           │   Data Center│
           │  10.0.0.0/16 │
           └──────────────┘

Features:
- Active-Active multi-path (ECMP)
- Per-flow load balancing
- Path quality monitoring (latency, jitter, loss)
- Dynamic path selection based on application SLA

# FRRouting (FRR) configuration
router bgp 65001
  bgp router-id 10.1.255.1
  neighbor 192.168.100.1 remote-as 65000
  neighbor 192.168.100.1 description "DC via ISP1"
  neighbor 192.168.101.1 remote-as 65000
  neighbor 192.168.101.1 description "DC via ISP2"
  
  address-family ipv4 unicast
    network 10.1.0.0/16
    neighbor 192.168.100.1 activate
    neighbor 192.168.100.1 route-map SET-LP-ISP1 in
    neighbor 192.168.101.1 activate
    neighbor 192.168.101.1 route-map SET-LP-ISP2 in
    maximum-paths 3  # ECMP across 3 paths
  exit-address-family
!
route-map SET-LP-ISP1 permit 10
  set local-preference 200  # Prefer ISP1
!
route-map SET-LP-ISP2 permit 10
  set local-preference 100  # ISP2 as backup
!

# IPSec configuration for each tunnel (strongSwan)
# Tunnel 1 (ISP1)
conn isp1-tunnel
    left=10.1.255.1
    leftsubnet=0.0.0.0/0
    right=203.0.113.1
    rightsubnet=0.0.0.0/0
    mark_out=1  # Mark outbound packets for policy routing
    mark_in=1
    auto=start

# Policy routing to steer traffic to specific tunnel
ip rule add fwmark 1 table 100
ip route add default via 192.168.100.1 dev ipsec0 table 100
```

**Application-Aware Routing**:
```bash
# Mark packets based on DSCP/application
iptables -t mangle -A PREROUTING -p tcp --dport 443 -j DSCP --set-dscp 46  # Voice
iptables -t mangle -A PREROUTING -p tcp --dport 80 -j DSCP --set-dscp 0    # Best-effort

# Route based on DSCP
ip rule add dscp 46 table 100  # High-priority → ISP1
ip rule add dscp 0 table 101   # Best-effort → ISP2
```

---

## Performance Optimization & Tuning

### **1. NIC Offload Capabilities**

```bash
# Check NIC capabilities
ethtool -k eth0

esp-hw-offload: on     # IPSec encryption/decryption offload
esp-tx-csum-hw-offload: on
rx-checksumming: on
tx-checksumming: on
scatter-gather: on
tcp-segmentation-offload: on
generic-segmentation-offload: on
generic-receive-offload: on
large-receive-offload: on
rx-vlan-offload: on
tx-vlan-offload: on

# Enable IPSec offload
ethtool -K eth0 esp-hw-offload on

# Verify offload in use
ip xfrm state show
# Look for "offload dev eth0 dir out"

# Supported NICs:
# - Intel X710, XL710, XXV710 (up to 40 Gbps)
# - Mellanox ConnectX-4/5/6 (up to 100 Gbps)
# - Broadcom BCM5871x
# - Netronome Agilio SmartNIC

# Offload statistics
ethtool -S eth0 | grep -i ipsec
```

**Performance Impact**:
```
Without offload (CPU):
- Single core: 2-5 Gbps (AES-GCM-256, AES-NI)
- Multi-core (4): 8-15 Gbps
- Latency: +0.5-1ms

With NIC offload:
- Throughput: Line rate (10-100 Gbps)
- Latency: +10-50µs
- CPU usage: <5% (vs 100% without offload)
```

### **2. Kernel Tuning**

```bash
# /etc/sysctl.d/99-ipsec.conf

# Increase connection tracking table
net.netfilter.nf_conntrack_max = 2097152
net.netfilter.nf_conntrack_tcp_timeout_established = 7200

# Increase network buffers
net.core.rmem_max = 536870912          # 512 MB
net.core.wmem_max = 536870912
net.core.rmem_default = 33554432       # 32 MB
net.core.wmem_default = 33554432
net.ipv4.tcp_rmem = 4096 87380 536870912
net.ipv4.tcp_wmem = 4096 65536 536870912
net.core.netdev_max_backlog = 250000

# Increase socket buffer limits
net.ipv4.udp_mem = 102400 2097152 4194304
net.ipv4.udp_rmem_min = 16384
net.ipv4.udp_wmem_min = 16384

# IP forwarding and routing
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1

# Disable reverse path filtering for asymmetric routing
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.default.rp_filter = 0
net.ipv4.conf.eth0.rp_filter = 0

# Increase local port range
net.ipv4.ip_local_port_range = 1024 65535

# Enable TCP window scaling
net.ipv4.tcp_window_scaling = 1

# Increase max number of open files
fs.file-max = 2097152

# Crypto acceleration
# (automatically used if available, but verify)
lsmod | grep -E 'aesni|ghash|gcm'
```

### **3. CPU Affinity & NUMA**

```bash
# Check NUMA topology
numactl --hardware

# Pin strongSwan charon daemon to specific NUMA node
taskset -c 0-15 /usr/lib/ipsec/charon

# OR use systemd
# /etc/systemd/system/strongswan.service.d/override.conf
[Service]
CPUAffinity=0-15
NUMAPolicy=bind
NUMAMask=0

# Pin IRQs to specific CPUs
# List IRQ numbers for NIC
grep eth0 /proc/interrupts

# Set IRQ affinity
echo "0f" > /proc/irq/100/smp_affinity  # CPU 0-3

# Use irqbalance for automatic balancing
systemctl enable irqbalance
systemctl start irqbalance

# Disable for manual control
systemctl stop irqbalance
```

### **4. Crypto Performance Tuning**

```bash
# Verify AES-NI is enabled
grep -o aes /proc/cpuinfo | uniq
# Output: aes

# Check crypto modules loaded
lsmod | grep -E 'aesni|gcm|ghash'
# Expected:
# aesni_intel
# ghash_clmulni_intel
# gcm

# Benchmark crypto performance
cryptsetup benchmark

# Algorithm |       Key |      Encryption |      Decryption
    aes-cbc        256b       1200.0 MiB/s     3800.0 MiB/s
    aes-gcm        256b       3500.0 MiB/s     3500.0 MiB/s
chacha20-poly1305  256b       2200.0 MiB/s     2200.0 MiB/s

# OpenSSL benchmark (more detailed)
openssl speed -evp aes-256-gcm -elapsed
# type             16 bytes     64 bytes    256 bytes   1024 bytes   8192 bytes  16384 bytes
# aes-256-gcm     412345.67k  1234567.89k  2345678.90k  3456789.01k  3800000.00k  3850000.00k

# Per-core throughput (parallel)
taskset -c 0 openssl speed -evp aes-256-gcm -multi 1
# Single core: ~3.5 GB/s
# 4 cores: ~14 GB/s
# 8 cores: ~28 GB/s (linear scaling up to memory bandwidth limit)
```

### **5. MTU Optimization**

```bash
# Determine optimal MTU for IPSec tunnel
# Formula: MTU_ipsec = MTU_physical - overhead

# Overhead calculation:
# IPv4 tunnel mode with ESP (AES-GCM):
# - Outer IP header: 20 bytes
# - ESP header: 8 bytes
# - ESP trailer: 2 bytes + padding (up to 15 bytes for AES-128, up to 1 byte for GCM)
# - ICV: 16 bytes (AES-GCM-128)
# - Total: ~60-70 bytes (conservatively)

# If physical MTU = 1500:
# IPSec MTU = 1500 - 70 = 1430 bytes

# Set MTU on tunnel interface (VTI)
ip link set ipsec0 mtu 1430

# MSS clamping (for TCP)
# Clamp TCP MSS to prevent fragmentation
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
  -m policy --dir out --pol ipsec \
  -j TCPMSS --set-mss 1360

# Enable Path MTU Discovery
sysctl -w net.ipv4.ip_no_pmtu_disc=0

# Test MTU
ping -M do -s 1400 10.0.2.5  # Should succeed
ping -M do -s 1500 10.0.2.5  # Should fail if MTU too small
```

### **6. Connection Rate Optimization**

```bash
# Increase kernel connection tracking
sysctl -w net.netfilter.nf_conntrack_max=2097152

# Adjust timeouts for short-lived connections
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_close_wait=15

# Disable conntrack for known good traffic (performance boost)
iptables -t raw -A PREROUTING -s 10.0.1.0/24 -d 10.0.2.0/24 -j NOTRACK
iptables -t raw -A OUTPUT -s 10.0.2.0/24 -d 10.0.1.0/24 -j NOTRACK

# Increase IKE daemon connection limits
# /etc/strongswan.d/charon.conf
charon {
    threads = 16           # Worker threads
    dns1 = 8.8.8.8
    max_packet = 10000     # Max IKE packet size
    processor {
        priority_threads {
            high = 4
            medium = 4
            low = 2
        }
    }
}
```

---

## Comprehensive Debugging & Troubleshooting

### **Debugging Layers**

```
Layer 1: Physical / Link Layer
├─► Check cable, switch ports
├─► Verify link status: ethtool eth0
└─► Check for errors: ethtool -S eth0

Layer 2: Network Layer
├─► Ping test (ICMP)
├─► Traceroute (check routing)
└─► MTU path discovery

Layer 3: IPSec Layer
├─► IKE negotiation (port 500/4500)
├─► ESP packets (protocol 50)
├─► SPD/SAD configuration
└─► Crypto operations

Layer 4: Application Layer
├─► TCP handshake
├─► Application-specific issues
└─► Firewall rules (iptables)
```

### **Diagnostic Commands**

```bash
# === IKE Debugging ===

# Live IKE negotiation log
journalctl -u strongswan -f
# Or for swanctl
journalctl -u strongswan-swanctl -f

# Increase debug level
# /etc/strongswan.d/charon-logging.conf
charon-systemd {
    journal {
        ike = 2      # 0=silent, 1=audit, 2=control, 3=controlmore, 4=raw
        knl = 2      # Kernel interface
        cfg = 2      # Configuration
        net = 2      # Network
        enc = 1      # Encryption
    }
}

# Restart to apply
systemctl restart strongswan

# Check IKE SA status
ipsec statusall
# OR
swanctl --list-sas

# Initiate connection manually
ipsec up <connection-name>
# OR
swanctl --initiate --child <connection-name>

# === XFRM (Kernel) Debugging ===

# List all SAs
ip xfrm state
ip xfrm state show

# List policies
ip xfrm policy
ip xfrm policy show

# Monitor XFRM events (real-time)
ip xfrm monitor

# XFRM statistics
cat /proc/net/xfrm_stat
# Look for:
# - XfrmInError: Inbound errors
# - XfrmInHdrError: Header errors
# - XfrmInStateInvalid: SA not found
# - XfrmOutError: Outbound errors

# Detailed SA info
ip -s xfrm state show
# Shows packet/byte counters, errors

# === Packet Capture ===

# Capture IKE negotiation (UDP 500/4500)
tcpdump -i eth0 -n 'udp port 500 or udp port 4500' -w ike.pcap

# Capture ESP packets
tcpdump -i eth0 -n 'esp' -w esp.pcap

# Capture inner traffic (if using VTI interface)
tcpdump -i ipsec0 -n -w inner.pcap

# Analyze in Wireshark
# Edit -> Preferences -> Protocols -> ISAKMP
# Enable "Decryption table" and add shared secrets

# For ESP decryption in Wireshark:
# Edit -> Preferences -> Protocols -> ESP
# Add: Protocol=ESP, SPI=0x12345678, Encryption=AES-GCM [RFC4106], 
#      Encryption key=<hex-key>, Authentication=NULL

# === Crypto Debugging ===

# Check crypto modules
lsmod | grep -E 'esp|xfrm|crypto'

# Crypto algorithm availability
cat /proc/crypto | grep -E 'name|driver|module' | less

# Test crypto performance
openssl speed -evp aes-256-gcm

# Kernel crypto test
modprobe tcrypt mode=10 sec=1  # AES-GCM test
dmesg | tail -50

# === Connection Testing ===

# End-to-end connectivity
ping -I 10.0.1.1 10.0.2.5

# TCP test
nc -vz 10.0.2.5 443

# Traceroute (check routing through tunnel)
traceroute 10.0.2.5

# MTU test
ping -M do -s 1400 10.0.2.5

# === Firewall Debugging ===

# Check iptables rules
iptables -L -v -n
iptables -t nat -L -v -n
iptables -t mangle -L -v -n

# Log dropped packets
iptables -I INPUT -j LOG --log-prefix "IPT-INPUT-DROP: "
iptables -I FORWARD -j LOG --log-prefix "IPT-FORWARD-DROP: "

# Check logs
journalctl -k | grep IPT-

# Temporarily disable firewall (for testing)
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -F
iptables -t nat -F
iptables -t mangle -F
```

### **Common Issues & Solutions**

| Symptom | Cause | Diagnosis | Fix |
|---------|-------|-----------|-----|
| **IKE_SA establishes, CHILD_SA fails** | Traffic selector mismatch | Check `leftsubnet`/`rightsubnet` in config vs actual packet src/dst | Widen traffic selectors or fix subnet config |
| **"no matching peer config found"** | Peer ID mismatch | Check `rightid` in config vs certificate CN/SAN | Set `rightid=%any` or use correct ID |
| **Authentication failure** | Wrong PSK or cert | Check `/etc/ipsec.secrets` or certificate validity | Verify PSK on both sides, check cert expiry/revocation |
| **Packets encrypted but not decrypted on remote** | SA exists only on one side | `ip xfrm state show` on both sides | Check if IKE_AUTH completed on both peers, verify SPD/SAD |
| **High packet loss** | MTU issue / fragmentation | `ping -M do -s <size>`, check `netstat -s \| grep fragment` | Enable MSS clamping, reduce tunnel MTU |
| **ESP packets but no decryption** | Wrong SPI or keys | `tcpdump esp`, compare SPI in packet vs `ip xfrm state` | Verify SPI matches, check if SA expired |
| **Connection works then stops** | SA expired, rekey failed | Check `ipsec statusall` for rekey errors | Increase lifetime, check DPD settings, verify routing |
| **NAT-T not working** | Firewall blocks UDP 4500 | `tcpdump udp port 4500` | Open UDP 4500, check NAT device supports ESP passthrough |
| **Asymmetric routing breaks IPSec** | Return path different | `traceroute`, check routing tables | Disable `rp_filter`, use policy routing |
| **CPU at 100% during IPSec traffic** | No hardware acceleration | Check `lsmod \| grep aesni`, benchmark crypto | Enable AES-NI, use NIC offload, upgrade hardware |

### **Advanced Debugging with strace / perf**

```bash
# Trace strongSwan IKE daemon system calls
strace -p $(pgrep charon) -s 2048 -f -o /tmp/charon.strace

# Look for:
# - socket() calls (IKE communication)
# - sendto()/recvfrom() (IKE packets)
# - open() (accessing /etc/ipsec.conf, certificates)

# Crypto performance profiling
perf record -g -p $(pgrep charon)
# Generate traffic, then:
perf report

# Look for hotspots in:
# - AES encryption functions
# - HMAC computation
# - DH operations

# Kernel function tracing (requires kernel with CONFIG_FTRACE)
# Trace XFRM functions
cd /sys/kernel/debug/tracing
echo 1 > events/xfrm/enable
cat trace_pipe

# Trace crypto operations
echo 1 > events/crypto/enable
```

---

## Security Hardening

### **1. Algorithm Selection (Production Baseline)**

```
# /etc/ipsec.conf or swanctl.conf

Minimum Security Baseline (2025+):

IKE_SA:
  Encryption:  AES-GCM-256, ChaCha20-Poly1305
  PRF:         HMAC-SHA2-512
  DH Group:    Curve25519 (Group 31), P-384 (Group 20)
  
CHILD_SA (ESP):
  Encryption:  AES-GCM-256
  DH Group:    Curve25519 (PFS enabled)

# strongSwan config
conn production
    ike=aes256gcm16-sha512-ecp384,chacha20poly1305-sha512-curve25519!
    esp=aes256gcm16-ecp384,chacha20poly1305-curve25519!
    keyexchange=ikev2
    rekey=yes
    rekeymargin=15m
    keyingtries=%forever

Forbidden (Weak / Deprecated):
  - DES, 3DES (insufficient key length)
  - MD5, SHA1 (collision attacks)
  - MODP-1024 (Group 2), MODP-1536 (Group 5) - too weak
  - IKEv1 (design flaws, use IKEv2 only)
  - AH without ESP (no confidentiality)
```

### **2. Certificate Management**

```bash
# Use short-lived certificates (24-48 hours)
# Automate with ACME / Let's Encrypt

# Generate CA
ipsec pki --gen --type ed25519 --outform pem > caKey.pem
ipsec pki --self --ca --lifetime 3650 --in caKey.pem \
  --dn "C=US, O=Example Corp, CN=VPN CA" \
  --outform pem > caCert.pem

# Generate server cert (24-hour validity)
ipsec pki --gen --type ed25519 --outform pem > serverKey.pem
ipsec pki --pub --in serverKey.pem --type ed25519 | \
  ipsec pki --issue --lifetime 1 --cacert caCert.pem --cakey caKey.pem \
  --dn "C=US, O=Example Corp, CN=vpn.example.com" \
  --san vpn.example.com --san 203.0.113.1 \
  --flag serverAuth --flag ikeIntermediate \
  --outform pem > serverCert.pem

# Automate renewal (cron)
# /etc/cron.hourly/renew-ipsec-cert
#!/bin/bash
CERT_EXPIRY=$(openssl x509 -in /etc/ipsec.d/certs/serverCert.pem -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
REMAINING=$((EXPIRY_EPOCH - NOW_EPOCH))

if [ $REMAINING -lt 7200 ]; then  # Renew if < 2 hours remaining
    /usr/local/bin/issue-new-cert.sh
    ipsec reload
fi

# Certificate pinning (prevent MitM with rogue CA)
# /etc/swanctl/swanctl.conf
connections {
    vpn {
        remote {
            auth = pubkey
            # Pin specific certificate
            certs = vpn-server.crt
            
            # OR pin public key (HPKP-style, survives cert renewal)
            pubkeys = sha256:base64-encoded-spki-hash
        }
    }
}

# Generate SPKI hash
openssl x509 -in cert.pem -pubkey -noout | \
  openssl pkey -pubin -outform DER | \
  openssl dgst -sha256 -binary | base64
```

### **3. Rate Limiting & DoS Protection**

```bash
# IKE cookie mechanism (anti-DoS)
# Enabled by default in IKEv2
# Forces client to prove possession of src IP before server allocates state

# Kernel: Limit IKE packets
iptables -A INPUT -p udp --dport 500 -m limit --limit 100/s --limit-burst 200 -j ACCEPT
iptables -A INPUT -p udp --dport 500 -j DROP

# Limit concurrent IKE_SA negotiations
# /etc/strongswan.d/charon.conf
charon {
    init_limit_half_open = 1000  # Max half-open IKE_SAs
    init_limit_job_load = 100    # Max concurrent IKE_SA_INIT jobs
}

# SYN flood protection (for TCP-based overlays)
sysctl -w net.ipv4.tcp_syncookies=1
sysctl -w net.ipv4.tcp_max_syn_backlog=4096

# Conntrack limits
sysctl -w net.netfilter.nf_conntrack_max=1048576

# Fail2ban for IKE authentication failures
# /etc/fail2ban/jail.local
[ipsec]
enabled = true
port = 500,4500
protocol = udp
filter = ipsec
logpath = /var/log/syslog
maxretry = 5
findtime = 600
bantime = 3600

# /etc/fail2ban/filter.d/ipsec.conf
[Definition]
failregex = .*charon.*received AUTHENTICATION_FAILED notify.*<HOST>
ignoreregex =
```

### **4. Post-Quantum Cryptography (Future-Proofing)**

```
Status (2025):
- NIST PQC standards published (2024)
- Kyber (KEM), Dilithium (signatures) selected
- Hybrid mode: Classical + PQC

Roadmap:
1. Hybrid IKE (Classical DH + PQC KEM)
   Example: X25519 + Kyber-768
   
2. PQC signatures for certificate auth
   Example: ECDSA (P-256) + Dilithium-3

3. PQC for ESP (future)
   Currently: AES-256-GCM sufficient (symmetric crypto unaffected by quantum)

Implementation (experimental):
# strongSwan plugin (pq-kem)
# Not yet in stable release as of 2025

# Manual hybrid approach:
# 1. Run classical IKEv2 with X25519
# 2. Perform out-of-band PQC KEM (Kyber) exchange
# 3. Mix shared secrets: SKEYSEED = prf(Ni | Nr, g_ir_classical XOR kyber_shared_secret)

# Monitor IETF IPsecME working group for standards
# RFC drafts: draft-ietf-ipsecme-ikev2-multiple-ke
```

### **5. Side-Channel Attack Mitigations**

```
Timing Attacks:
- Use constant-time crypto implementations
- AES-NI (hardware) is constant-time
- Avoid software AES with table lookups (cache timing)
- Constant-time comparison for ICV/tag verification

Cache Attacks (e.g., Spectre, Meltdown):
- Use CPU microcode updates
- Enable kernel page-table isolation (KPTI)
- Flush L1 cache on context switch (L1TF mitigation)

Power Analysis (for embedded systems):
- Use hardware crypto (CAAM, QAT) with DPA countermeasures
- Randomize operation timing (add jitter)

Configuration:
# Kernel: Enable mitigations
cat /sys/devices/system/cpu/vulnerabilities/*
# All should show "Mitigation: ..."

# Disable SMT (HyperThreading) for maximum security
echo off > /sys/devices/system/cpu/smt/control

# Use constant-time crypto
# strongSwan automatically selects constant-time implementations when available
```

---

## Cloud Provider Deep Dive

### **AWS Site-to-Site VPN**

```
Architecture:
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  On-Prem    │         │ AWS Transit  │         │  AWS VPC    │
│  Customer   │◄───────►│   Gateway    │◄───────►│             │
│   Gateway   │  VPN    │  (or VGW)    │  VPN    │  10.0.0.0/16│
│ 203.0.113.1 │         │              │         │             │
└─────────────┘         └──────────────┘         └─────────────┘

AWS Configuration (via CLI):
# 1. Create Customer Gateway (your on-prem endpoint)
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.1 \
  --bgp-asn 65000

# 2. Create Virtual Private Gateway (VGW) or Transit Gateway (TGW)
aws ec2 create-vpn-gateway --type ipsec.1
aws ec2 attach-vpn-gateway --vpn-gateway-id vgw-xxxxx --vpc-id vpc-xxxxx

# 3. Create VPN Connection
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-xxxxx \
  --vpn-gateway-id vgw-xxxxx \
  --options TunnelOptions='[{TunnelInsideCidr=169.254.10.0/30},{TunnelInsideCidr=169.254.11.0/30}]'

# 4. Download configuration
aws ec2 describe-vpn-connections --vpn-connection-id vpn-xxxxx \
  --query 'VpnConnections[0].CustomerGatewayConfiguration' \
  --output text > aws-vpn-config.xml

# AWS VPN uses:
# - IKEv2 (strongSwan 5.5+ compatible)
# - Pre-shared keys (PSK)
# - AES-256-CBC + SHA2-256 (older) or AES-256-GCM (newer)
# - DH Group 14 (2048-bit MODP) or higher
# - Dead Peer Detection (DPD) every 10s
# - Rekey every 28800s (8 hours)

# Customer Gateway Configuration (strongSwan)
# Extract from aws-vpn-config.xml and create:

# /etc/ipsec.conf
conn aws-tunnel1
    type=tunnel
    authby=secret
    left=%defaultroute
    leftid=203.0.113.1
    leftsubnet=0.0.0.0/0
    right=52.95.1.1  # AWS VPN endpoint from config
    rightsubnet=0.0.0.0/0
    ike=aes256-sha256-modp2048!
    esp=aes256-sha256-modp2048!
    keyexchange=ikev2
    ikelifetime=28800s
    lifetime=3600s
    rekeymargin=540s
    keyingtries=%forever
    dpdaction=restart
    dpddelay=10s
    dpdtimeout=30s
    auto=start
    mark_in=100
    mark_out=100

# /etc/ipsec.secrets
203.0.113.1 52.95.1.1 : PSK "your-pre-shared-key-from-aws-config"

# Routing (BGP or static)
# Option 1: Static routes
ip route add 10.0.0.0/16 dev ipsec0  # VTI interface

# Option 2: BGP with FRR
router bgp 65000
  neighbor 169.254.10.1 remote-as 64512  # AWS BGP ASN
  neighbor 169.254.10.1 timers 10 30
  address-family ipv4 unicast
    network 10.1.0.0/16
    neighbor 169.254.10.1 activate
  exit-address-family

# Monitoring
aws ec2 describe-vpn-connections --vpn-connection-id vpn-xxxxx \
  --query 'VpnConnections[0].VgwTelemetry'
# Shows: status (UP/DOWN), status_message, last_status_change

# CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/VPN \
  --metric-name TunnelState \
  --dimensions Name=VpnId,Value=vpn-xxxxx \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 300 \
  --statistics Average
```

**AWS VPN Accelerated (Global Accelerator)**:
```bash
# Lower latency via AWS backbone
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-xxxxx \
  --transit-gateway-id tgw-xxxxx \
  --options EnableAcceleration=true

# Benefits:
# - Traffic routed via AWS edge locations
# - ~20-30% latency reduction (depending on geography)
# - Cost: $0.025/hour per accelerated attachment
```

### **GCP Cloud VPN**

```bash
# HA VPN (99.99% SLA, active-active tunnels)

# 1. Create VPN Gateway
gcloud compute vpn-gateways create gw-us-central1 \
  --network=vpc1 \
  --region=us-central1

# 2. Create Cloud Router (for BGP)
gcloud compute routers create router-us-central1 \
  --network=vpc1 \
  --region=us-central1 \
  --asn=65001

# 3. Create external VPN gateway (on-prem endpoint)
gcloud compute external-vpn-gateways create on-prem-gw \
  --interfaces 0=203.0.113.1

# 4. Create VPN tunnels (2 for HA)
gcloud compute vpn-tunnels create tunnel-1 \
  --peer-external-gateway=on-prem-gw \
  --peer-external-gateway-interface=0 \
  --region=us-central1 \
  --ike-version=2 \
  --shared-secret=your-psk \
  --router=router-us-central1 \
  --vpn-gateway=gw-us-central1 \
  --interface=0

gcloud compute vpn-tunnels create tunnel-2 \
  --peer-external-gateway=on-prem-gw \
  --peer-external-gateway-interface=0 \
  --region=us-central1 \
  --ike-version=2 \
  --shared-secret=your-psk-2 \
  --router=router-us-central1 \
  --vpn-gateway=gw-us-central1 \
  --interface=1

# 5. Configure BGP
gcloud compute routers add-interface router-us-central1 \
  --interface-name=if-tunnel-1 \
  --vpn-tunnel=tunnel-1 \
  --region=us-central1

gcloud compute routers add-bgp-peer router-us-central1 \
  --peer-name=bgp-peer-1 \
  --peer-asn=65000 \
  --interface=if-tunnel-1 \
  --region=us-central1 \
  --peer-ip-address=169.254.1.2 \
  --md5-authentication-key=bgp-md5-key

# GCP Cloud VPN uses:
# - IKEv2
# - AES-256-GCM or AES-256-CBC + HMAC-SHA2-256
# - DH Group 14+
# - Perfect Forward Secrecy (PFS) enabled
# - MTU: 1460 bytes (GCP sets DF bit)

# Monitoring
gcloud compute vpn-tunnels describe tunnel-1 --region=us-central1
# Status: ESTABLISHED

# Metrics (via Cloud Monitoring)
# - vpn.googleapis.com/gateway/connections: Tunnel count
# - vpn.googleapis.com/tunnel_established: Boolean (0/1)
# - vpn.googleapis.com/network/sent_bytes_count: Throughput
# - vpn.googleapis.com/network/sent_packets_count: PPS
```

### **Azure VPN Gateway**

```bash
# Route-based VPN (recommended)

# 1. Create Virtual Network Gateway
az network vnet-gateway create \
  --name VNetGateway \
  --resource-group MyRG \
  --vnet MyVNet \
  --gateway-type Vpn \
  --vpn-type RouteBased \
  --sku VpnGw2 \  # VpnGw1/2/3/4/5 (up to 10 Gbps)
  --public-ip-addresses GatewayIP

# 2. Create Local Network Gateway (on-prem endpoint)
az network local-gateway create \
  --name OnPremGateway \
  --resource-group MyRG \
  --gateway-ip-address 203.0.113.1 \
  --local-address-prefixes 10.1.0.0/16

# 3. Create VPN Connection
az network vpn-connection create \
  --name AzureToOnPrem \
  --resource-group MyRG \
  --vnet-gateway1 VNetGateway \
  --local-gateway2 OnPremGateway \
  --shared-key your-psk \
  --enable-bgp

# Azure VPN uses:
# - IKEv2 or IKEv1
# - Custom policy support (specify exact algorithms)
# - Active-Active mode (2 tunnel endpoints for HA)
# - Zone-redundant gateways (99.99% SLA)

# Custom IPsec policy (if needed)
az network vpn-connection ipsec-policy add \
  --connection-name AzureToOnPrem \
  --resource-group MyRG \
  --ike-encryption AES256 \
  --ike-integrity SHA384 \
  --dh-group DHGroup24 \
  --ipsec-encryption GCMAES256 \
  --ipsec-integrity GCMAES256 \
  --pfs-group PFS24 \
  --sa-lifetime 27000 \
  --sa-data-size 102400000

# BGP configuration
az network vnet-gateway update \
  --name VNetGateway \
  --resource-group MyRG \
  --set bgpSettings.asn=65515 \
  --set bgpSettings.bgpPeeringAddress=10.0.1.254

# Monitoring
az network vpn-connection show \
  --name AzureToOnPrem \
  --resource-group MyRG \
  --query connectionStatus
# Output: Connected / NotConnected

# Metrics (Azure Monitor)
az monitor metrics list \
  --resource /subscriptions/.../resourceGroups/MyRG/providers/Microsoft.Network/connections/AzureToOnPrem \
  --metric TunnelIngressBytes \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z
```

---

## Next 3 Steps

1. **Build Production VPN Lab**: Deploy strongSwan-based site-to-site VPN between two Linux VMs (or containers), configure certificate-based auth with short-lived certs (24h validity), enable DPD and PFS, set up BGP with FRR for dynamic routing, implement HA with VRRP (keepalived), monitor with Prometheus/Grafana, test failover scenarios, measure throughput with `iperf3` and latency with `ping`, capture and analyze IKE/ESP packets in Wireshark

2. **Kubernetes IPSec Encryption**: Deploy multi-node Kubernetes cluster (3+ nodes), install Cilium CNI with IPSec encryption enabled, verify pod-to-pod traffic encryption with `tcpdump esp`, implement ClusterMesh for multi-cluster encrypted communication, benchmark performance impact (encrypted vs unencrypted), analyze XFRM kernel state with `ip xfrm`, implement NetworkPolicy to control encrypted flows, integrate with Prometheus for IPSec metrics

3. **Implement Custom IPSec Control Plane**: Write Go application using `vishvananda/netlink` to programmatically manage XFRM states/policies, build minimal IKE daemon or integrate strongSwan library, implement automatic SA rotation based on byte/packet count, add Prometheus metrics exposition, create REST API for IPSec tunnel management, implement configuration validation and pre-flight checks, add automated testing (unit tests for netlink operations, integration tests for tunnel establishment), profile crypto performance with `pprof`, deploy in container with non-root user (capabilities: NET_ADMIN)

---

## Comprehensive References

**RFCs (Essential Reading)**:
- RFC 4301: Security Architecture for IP
- RFC 4302: IP Authentication Header (AH)
- RFC 4303: IP Encapsulating Security Payload (ESP)
- RFC 4304: Extended Sequence Number (ESN)
- RFC 7296: IKEv2 Protocol
- RFC 3947/3948: NAT Traversal
- RFC 4106: AES-GCM for ESP
- RFC 7539: ChaCha20-Poly1305
- RFC 5996: IKEv2 (with corrections)

**Implementation Guides**:
- strongSwan: https://docs.strongswan.org (most comprehensive)
- Linux XFRM: https://www.kernel.org/doc/html/latest/networking/xfrm.html
- Libreswan: https://libreswan.org/wiki/Main_Page

**Crypto References**:
- NIST SP 800-57: Key Management
- NIST SP 800-77: IPsec VPN Guide
- NIST FIPS 140-3: Cryptographic Module Validation

**Cloud Providers**:
- AWS VPN: https://docs.aws.amazon.com/vpn/latest/s2svpn/
- GCP Cloud VPN: https://cloud.google.com/network-connectivity/docs/vpn
- Azure VPN Gateway: https://learn.microsoft.com/azure/vpn-gateway/

**Kubernetes/CNCF**:
- Cilium IPSec: https://docs.cilium.io/en/stable/security/network/encryption/
- Calico IPSec: https://docs.tigera.io/calico/latest/network-policy/encrypt-cluster-pod-traffic
- Weave Net Encryption: https://www.weave.works/docs/net/latest/tasks/manage/security/

**Security**:
- IETF IPsecME WG: https://datatracker.ietf.org/wg/ipsecme/
- BSI TR-02102: Cryptographic Mechanisms (Germany)
- NSA Suite B Cryptography (historical, transitioned to CNSA)

**Code/Tools**:
- strongSwan (C): https://github.com/strongswan/strongswan
- Libreswan (C): https://github.com/libreswan/libreswan
- Go netlink: https://github.com/vishvananda/netlink
- Rust IPSec (WIP): https://github.com/smoltcp-rs/smoltcp