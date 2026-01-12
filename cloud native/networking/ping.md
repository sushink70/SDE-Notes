# How Ping Works: Deep Technical Analysis

**Summary**: Ping uses ICMP Echo Request/Reply packets to measure host reachability and RTT. The kernel's network stack constructs raw ICMP packets (type 8/0), sends them via IP routing, and processes replies. Key components: socket creation with `SOCK_RAW`, ICMP header construction with sequence numbers, checksum calculation, IP routing decision, link-layer encapsulation, and round-trip timing. Security implications include amplification attacks, network reconnaissance, and firewall evasion. Understanding ping requires knowledge of raw sockets, ICMP protocol structure, IP routing, ARP resolution, and kernel network stack processing.

---

## Step-by-Step Technical Flow

### 1. **User Space: Process Initialization**

```bash
# Requires CAP_NET_RAW capability or root
ping -c 4 192.168.1.100
```

**What happens:**
- Process calls `socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)` requiring `CAP_NET_RAW`
- Kernel allocates socket descriptor, attaches to ICMP protocol handler
- Process constructs ICMP Echo Request packet in user space

**Code reference (simplified C):**
```c
int sock = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);
if (sock < 0) {
    perror("socket creation failed - need CAP_NET_RAW");
    exit(1);
}
```

### 2. **ICMP Packet Construction**

**ICMP Echo Request Structure:**
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Type=8    |     Code=0    |          Checksum             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Identifier          |        Sequence Number        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Data (timestamp + padding, typically 56 bytes)            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Fields:**
- **Type**: 8 (Echo Request), 0 (Echo Reply)
- **Code**: 0 (always for echo)
- **Checksum**: Internet checksum (RFC 1071) over entire ICMP packet
- **Identifier**: Process ID (to match replies)
- **Sequence**: Incrementing counter (per packet)
- **Data**: Timestamp (for RTT) + padding to 64 bytes total

**Checksum calculation:**
```c
uint16_t icmp_checksum(uint16_t *buf, int len) {
    uint32_t sum = 0;
    while (len > 1) {
        sum += *buf++;
        len -= 2;
    }
    if (len == 1) sum += *(uint8_t*)buf;
    sum = (sum >> 16) + (sum & 0xffff);
    sum += (sum >> 16);
    return ~sum;
}
```

### 3. **Kernel Space: Socket Layer Processing**

**Call path:**
```
sendto() → __sys_sendto() → sock_sendmsg() → inet_sendmsg() → raw_sendmsg()
```

**Key operations:**
- Validate destination address (`sockaddr_in`)
- Check socket permissions and filters
- Allocate `sk_buff` structure (kernel packet buffer)
- Copy ICMP data from user space to kernel space

### 4. **IP Layer Processing**

**Routing decision:**
```
ip_route_output_key() → fib_lookup() → select next hop
```

**Steps:**
- Lookup routing table (`ip route show`)
- Determine outgoing interface (e.g., `eth0`, `wlan0`)
- Resolve next-hop IP (gateway or direct)
- Construct IP header:

```
IP Header (20 bytes minimum):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |Type of Service|          Total Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |  Protocol=1   |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Critical fields:**
- **Protocol**: 1 (ICMP)
- **TTL**: Default 64 (Linux), decremented at each hop
- **Source/Dest**: Your IP and target IP

### 5. **Link Layer: ARP/ND and Frame Construction**

**ARP Resolution (IPv4):**
```bash
# Check ARP cache
ip neigh show

# If not cached, send ARP request:
# "Who has 192.168.1.100? Tell 192.168.1.5"
```

**ARP packet flow:**
```
[ARP Request: Broadcast FF:FF:FF:FF:FF:FF]
    ↓
[Target responds with MAC address]
    ↓
[Cache entry created: 192.168.1.100 → aa:bb:cc:dd:ee:ff]
```

**Ethernet frame:**
```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Dest MAC (6B) | Src MAC (6B)  | EtherType=0x0800 (IPv4)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    IP Header (20B)                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    ICMP Packet (64B)                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    FCS (4B)                                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 6. **Physical Transmission**

**NIC driver operations:**
- Packet copied to DMA ring buffer
- NIC signals PHY layer
- Electrical/optical signals sent on wire/fiber
- For cloud VMs: virtio-net → hypervisor → virtual switch → physical NIC

**Cloud-specific path (AWS EC2 example):**
```
VM (eth0) → virtio-net → QEMU/KVM → 
Nitro hypervisor → VPC routing → 
Physical switch fabric → Destination subnet
```

### 7. **Remote Host: Packet Reception**

**Receive path (reverse):**
```
NIC IRQ → net_rx_action() → __netif_receive_skb() → 
ip_rcv() → ip_local_deliver() → icmp_rcv()
```

**ICMP processing:**
- Verify checksum
- Check Type=8 (Echo Request)
- Construct Echo Reply (Type=0):
  - Swap source/dest IPs
  - Copy identifier, sequence, data
  - Recalculate checksum
- Send reply back through same path

### 8. **Reply Reception and RTT Calculation**

**Local host receives reply:**
```c
// Pseudo-code
gettimeofday(&recv_time, NULL);
rtt = (recv_time - send_time) * 1000.0; // milliseconds
printf("64 bytes from %s: icmp_seq=%d ttl=%d time=%.2f ms\n",
       dest_ip, seq, ttl, rtt);
```

**Output example:**
```
64 bytes from 192.168.1.100: icmp_seq=1 ttl=64 time=0.342 ms
```

---

## Architecture View

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER SPACE                               │
│  ┌──────────────┐                                               │
│  │ ping process │  socket(SOCK_RAW) → sendto() → recvfrom()    │
│  └──────┬───────┘                                               │
└─────────┼─────────────────────────────────────────────────────┘
          │ System call boundary
┌─────────▼─────────────────────────────────────────────────────┐
│                       KERNEL SPACE                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Socket Layer: raw_sendmsg() / raw_recvmsg()           │   │
│  └────────────────┬────────────────────────────────────────┘   │
│  ┌────────────────▼────────────────────────────────────────┐   │
│  │  ICMP Layer: icmp_send() / icmp_rcv()                  │   │
│  │  - Construct/parse ICMP header                         │   │
│  │  - Checksum validation                                 │   │
│  └────────────────┬────────────────────────────────────────┘   │
│  ┌────────────────▼────────────────────────────────────────┐   │
│  │  IP Layer: ip_send_skb() / ip_rcv()                    │   │
│  │  - Routing decision (fib_lookup)                       │   │
│  │  - Fragmentation if needed (MTU)                       │   │
│  │  - TTL decrement (at routers)                          │   │
│  └────────────────┬────────────────────────────────────────┘   │
│  ┌────────────────▼────────────────────────────────────────┐   │
│  │  Neighbor Subsystem: ARP/NDP resolution                │   │
│  │  - MAC address lookup/cache                            │   │
│  └────────────────┬────────────────────────────────────────┘   │
│  ┌────────────────▼────────────────────────────────────────┐   │
│  │  Link Layer: dev_queue_xmit()                          │   │
│  │  - Queue packet to NIC TX ring                         │   │
│  └────────────────┬────────────────────────────────────────┘   │
└───────────────────┼──────────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────────┐
│                 NETWORK INTERFACE CARD (NIC)                  │
│  - DMA transfer from ring buffer                             │
│  - PHY layer encoding → electrical/optical signal            │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ▼
              Physical Medium
           (Ethernet, WiFi, Fiber)
                    │
                    ▼
            ┌───────────────┐
            │ Network Path  │  Switches, routers, firewalls
            │ (L2/L3 hops)  │  Each router: TTL--, routing decision
            └───────┬───────┘
                    │
                    ▼
            ┌──────────────────┐
            │  Destination Host │ (Reverse path for Echo Reply)
            └──────────────────┘
```

---

## Scenario-Based Examples

### **Scenario 1: Local Network Ping**

```bash
# Source: 192.168.1.5, Target: 192.168.1.100 (same subnet)
ping -c 1 192.168.1.100
```

**Flow:**
1. **Routing**: Direct delivery (no gateway), out `eth0`
2. **ARP**: Broadcast "Who has 192.168.1.100?"
3. **Target responds**: MAC `aa:bb:cc:dd:ee:ff`
4. **Frame sent**: Src MAC=your_mac, Dst MAC=aa:bb:cc:dd:ee:ff
5. **Switch forwards** based on MAC table
6. **Reply**: RTT ~0.3ms (wire latency + processing)

**Packet capture:**
```bash
# Terminal 1
sudo tcpdump -i eth0 -n icmp

# Terminal 2
ping -c 1 192.168.1.100

# Output:
# 10:23:45.123456 IP 192.168.1.5 > 192.168.1.100: ICMP echo request, id 1234, seq 1
# 10:23:45.123798 IP 192.168.1.100 > 192.168.1.5: ICMP echo reply, id 1234, seq 1
```

### **Scenario 2: Cross-Subnet Ping (via Router)**

```bash
# Source: 10.0.1.5, Target: 10.0.2.100 (different subnet)
ping -c 1 10.0.2.100
```

**Flow:**
1. **Routing**: Lookup shows gateway `10.0.1.1`
2. **ARP**: Resolve gateway MAC (not target!)
3. **Frame sent**: Dst MAC=gateway_mac, IP Dst=10.0.2.100
4. **Router receives**: Decrements TTL (64→63), re-routes
5. **Router forwards**: New Ethernet frame, Src MAC=router_if2, Dst MAC=target_mac
6. **Reply follows reverse path**: RTT ~1-5ms

**Routing table:**
```bash
ip route show
# default via 10.0.1.1 dev eth0
# 10.0.1.0/24 dev eth0 proto kernel scope link
# 10.0.2.0/24 via 10.0.1.1 dev eth0
```

### **Scenario 3: Internet Ping (Multi-Hop)**

```bash
ping -c 1 8.8.8.8
```

**Flow:**
1. **DNS not needed** (IP provided)
2. **Default gateway**: Send to local router
3. **ISP routers**: 10-15 hops, each decrements TTL
4. **Google edge**: Responds from nearest PoP
5. **RTT**: 10-50ms depending on distance

**Traceroute to see hops:**
```bash
traceroute 8.8.8.8
# 1  _gateway (192.168.1.1)  0.5ms
# 2  10.20.30.1  2ms
# 3  isp-router.net  8ms
# ...
# 10 dns.google (8.8.8.8)  15ms
```

### **Scenario 4: Cloud VM to VM (Same VPC)**

**AWS example:**
```bash
# VM1 (10.0.1.10) → VM2 (10.0.1.20), same subnet
ping -c 1 10.0.1.20
```

**Flow:**
- **No ARP**: Hypervisor intercepts, knows MAC mapping
- **VPC routing**: Virtual router forwards within same AZ
- **RTT**: <1ms (same physical host) to ~2ms (different hosts)

**Security Group check:**
```bash
# Must allow ICMP in inbound rules
aws ec2 describe-security-groups --group-ids sg-12345 \
  | jq '.SecurityGroups[].IpPermissions[] | select(.IpProtocol=="icmp")'
```

### **Scenario 5: Blocked ICMP (Firewall)**

```bash
ping -c 3 blocked-host.com
# PING blocked-host.com (203.0.113.10): 56 data bytes
# Request timeout for icmp_seq 0
# Request timeout for icmp_seq 1
```

**Reasons:**
- **Firewall drops ICMP**: Stateful firewall, iptables, cloud SG
- **No route**: Intermediate router returns ICMP "Network Unreachable" (Type 3, Code 0)
- **Host down**: No response, timeout after ~1s per packet

**Check iptables:**
```bash
sudo iptables -L INPUT -v -n | grep icmp
# DROP  icmp -- *  *  0.0.0.0/0  0.0.0.0/0  icmptype 8
```

### **Scenario 6: MTU and Fragmentation**

```bash
# Send large ICMP packet, DF flag set
ping -M do -s 1472 192.168.1.100  # 1472 data + 28 headers = 1500 MTU
ping -M do -s 1473 192.168.1.100  # Exceeds MTU

# Error: "ping: local error: message too long, mtu=1500"
```

**What happens:**
- IP header has DF (Don't Fragment) bit set
- If packet > MTU on any hop, router sends ICMP "Fragmentation Needed" (Type 3, Code 4)
- Sender reduces packet size (PMTUD - Path MTU Discovery)

---

## Threat Model and Security Implications

### **Reconnaissance Attacks**

**Issue**: Ping reveals live hosts
```bash
# Attacker scans subnet
nmap -sn 10.0.1.0/24  # Uses ICMP Echo
```

**Mitigation:**
- Block external ICMP at perimeter firewall
- Rate-limit ICMP responses
- Use cloud security groups to deny ICMP from untrusted sources

### **ICMP Flood (DoS)**

**Attack:**
```bash
# Send massive ICMP traffic
hping3 --icmp --flood target.com
```

**Impact**: Saturate bandwidth, exhaust connection tracking

**Mitigation:**
```bash
# iptables rate limiting
iptables -A INPUT -p icmp --icmp-type echo-request \
  -m limit --limit 1/s --limit-burst 5 -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# nftables
nft add rule ip filter input icmp type echo-request limit rate 1/second accept
```

### **ICMP Redirect Attacks**

**Attack**: Malicious router sends ICMP Redirect (Type 5) to change routing
```
Attacker → Victim: "Use me (attacker) as gateway for 8.8.8.8"
```

**Mitigation:**
```bash
# Disable ICMP redirects
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0
```

### **Smurf Attack (Amplification)**

**Attack**: Spoof victim's IP, send ICMP to broadcast address
```
Attacker → 192.168.1.255 (broadcast), Src IP=victim
All hosts reply → victim (amplification)
```

**Mitigation:**
- Disable IP directed broadcasts
```bash
sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=1
```
- BCP38: ISPs drop packets with spoofed source IPs

### **Information Leakage**

**Issue**: TTL reveals OS (Linux=64, Windows=128, Cisco=255)

**Example:**
```bash
ping 192.168.1.100
# 64 bytes from 192.168.1.100: ttl=64 → Linux
# 64 bytes from 192.168.1.101: ttl=128 → Windows
```

**Mitigation**: Normalize TTL at border or disable ICMP

---

## Testing and Verification

### **1. Capture and Analyze Packets**

```bash
# Capture ICMP on interface
sudo tcpdump -i eth0 -nn icmp -vvv -X

# Wireshark filter
icmp.type == 8 or icmp.type == 0
```

### **2. Simulate Packet Loss**

```bash
# Drop 20% of ICMP packets
sudo tc qdisc add dev eth0 root netem loss 20%
ping -c 10 8.8.8.8

# Remove rule
sudo tc qdisc del dev eth0 root
```

### **3. Test Fragmentation**

```bash
# Find PMTU
ping -M do -s 1472 target  # Start at 1472
ping -M do -s 1400 target  # Reduce if failed
```

### **4. Performance Benchmarking**

```bash
# Flood ping (requires root)
sudo ping -f -c 10000 192.168.1.100

# Statistics
# 10000 packets transmitted, 9998 received, 0.02% packet loss
# round-trip min/avg/max = 0.123/0.234/1.456 ms
```

### **5. Kernel Tracing**

```bash
# Trace ICMP with ftrace
sudo trace-cmd record -e icmp ping -c 1 8.8.8.8
sudo trace-cmd report

# Or with bpftrace
sudo bpftrace -e 'kprobe:icmp_send { printf("Sending ICMP from %s\n", comm); }'
```

---

## Production Deployment Considerations

### **Cloud Security Groups (AWS)**

```bash
# Allow ICMP echo from specific CIDR
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345 \
  --ip-permissions IpProtocol=icmp,FromPort=8,ToPort=0,IpRanges='[{CidrIp=10.0.0.0/8}]'
```

### **Kubernetes Network Policies**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-icmp
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: monitoring
    # Note: Network policies don't filter ICMP directly,
    # relies on CNI plugin (Calico, Cilium)
```

### **Monitoring and Alerting**

```bash
# Prometheus blackbox exporter for ICMP checks
cat <<EOF > blackbox.yml
modules:
  icmp:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: ip4
EOF

# Alert on packet loss
# ALERTS: ping_loss > 10% for 5 minutes
```

---

## Alternatives and Failure Modes

### **Alternative: TCP/UDP Probes**

```bash
# When ICMP blocked, use TCP probe
nc -zv target.com 443  # Check if port 443 open

# Or HTTP health check
curl -I https://target.com/health
```

### **Failure Mode: Asymmetric Routing**

**Scenario**: Outbound via ISP-A, return via ISP-B
- **Symptom**: High RTT variance, packet loss
- **Diagnosis**: `mtr target.com` shows different paths

### **Failure Mode: ICMP Blackhole**

**Scenario**: Firewall drops ICMP silently, no "unreachable" message
- **Symptom**: Timeout, no error
- **Diagnosis**: tcpdump shows request, no reply

---

## Next 3 Steps

1. **Implement raw ICMP socket in Go/Rust**
   ```bash
   # Build minimal ping tool
   # Go: github.com/go-ping/ping
   # Rust: pnet crate for raw sockets
   git clone <your-repo> && cd ping-tool
   cargo build --release
   sudo ./target/release/ping 8.8.8.8
   ```

2. **Set up controlled test environment**
   ```bash
   # Use network namespaces to simulate multi-hop
   sudo ip netns add ns1
   sudo ip netns add ns2
   sudo ip link add veth0 type veth peer name veth1
   sudo ip link set veth1 netns ns1
   # Test ping across namespaces with iptables rules
   ```

3. **Deploy ICMP monitoring in prod**
   ```bash
   # Blackbox exporter + Grafana dashboard
   helm install blackbox prometheus-community/prometheus-blackbox-exporter
   # Configure targets: internal services, external APIs
   # Alert on >5% packet loss or RTT >100ms
   ```

---

## References

- **RFC 792**: Internet Control Message Protocol (ICMP)
- **RFC 1071**: Computing the Internet Checksum
- **RFC 1191**: Path MTU Discovery
- **Kernel source**: `net/ipv4/icmp.c`, `net/ipv4/ip_output.c`
- **BPF tools**: `bpftrace`, `trace-cmd` for kernel-level tracing
- **Cloud docs**: AWS VPC ICMP, GCP firewall rules, Azure NSG ICMP handling