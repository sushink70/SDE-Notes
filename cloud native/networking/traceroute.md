# Summary: Traceroute Deep-Dive

Traceroute maps network paths by exploiting TTL (Time-To-Live) in IP packets and ICMP/UDP responses from intermediate routers. It sends packets with incrementing TTL values (1, 2, 3...) causing each hop to return "TTL Exceeded" messages, revealing router IPs and round-trip times. Modern variants use UDP, ICMP Echo, or TCP probes depending on firewall/NAT traversal requirements. Critical for network troubleshooting, security boundary discovery, and understanding routing behavior in cloud/hybrid topologies—but also exposes infrastructure topology to adversaries.

---

## How Traceroute Works: Step-by-Step

### 1. **Core Mechanism: TTL Exploitation**

Every IP packet has a TTL field (8-bit, max 255). Each router decrements TTL by 1. When TTL reaches 0, the router:
- **Drops the packet**
- **Sends ICMP Time Exceeded (Type 11, Code 0)** back to the source

Traceroute leverages this by sending packets with TTL=1, 2, 3... to progressively discover each hop.

```
┌──────────┐   TTL=1    ┌──────────┐   TTL=2    ┌──────────┐   TTL=3    ┌──────────┐
│  Source  │────────────>│ Router 1 │────────────>│ Router 2 │────────────>│  Target  │
│(tracert) │             │ (Hop 1)  │             │ (Hop 2)  │             │          │
└──────────┘             └──────────┘             └──────────┘             └──────────┘
     ^                        │                        │                        │
     │                        │                        │                        │
     └────ICMP TTL Exceeded───┘                        │                        │
                               └────ICMP TTL Exceeded──┘                        │
                                                        └────ICMP Echo Reply/UDP Port Unreachable
```

---

### 2. **Packet Flow Sequence**

#### **Probe 1 (TTL=1):**
```
1. Source sends UDP/ICMP packet, TTL=1, to destination
2. First router receives packet
   - Decrements TTL: 1 - 1 = 0
   - Drops packet
   - Sends ICMP Type 11 (Time Exceeded) to source
3. Source records: Hop 1 = Router IP, RTT = time delta
```

#### **Probe 2 (TTL=2):**
```
1. Source sends packet, TTL=2
2. Router 1 decrements TTL to 1, forwards
3. Router 2 decrements TTL to 0, drops, sends ICMP Type 11
4. Source records: Hop 2 = Router 2 IP, RTT
```

#### **Final Probe (TTL=N):**
```
1. Packet reaches destination with TTL≥1
2. Destination responds based on probe type:
   - UDP: ICMP Port Unreachable (Type 3, Code 3)
   - ICMP: ICMP Echo Reply (Type 0)
   - TCP: SYN-ACK or RST
```

---

### 3. **Probe Type Variants**

| **Type**       | **Default Port/Proto** | **Firewall Traversal** | **Use Case**                          |
|----------------|------------------------|------------------------|---------------------------------------|
| **UDP**        | 33434-33534 (incr.)    | Often blocked          | Classic Unix traceroute               |
| **ICMP Echo**  | Protocol 1             | Moderate filtering     | Windows `tracert`, some Linux         |
| **TCP SYN**    | 80/443                 | Best (mimics web)      | Firewall/NAT traversal (`tcptraceroute`) |
| **UDP/ICMP**   | Custom                 | Variable               | Paris traceroute (ECMP-aware)         |

**Key Security Insight:** TCP-based traceroute can map internal topology even behind stateful firewalls by targeting allowed ports (80/443).

---

### 4. **Detailed Algorithm**

```c
// Pseudocode for classic UDP traceroute
int max_ttl = 30;
int nprobes = 3;  // probes per hop
int base_port = 33434;

for (int ttl = 1; ttl <= max_ttl; ttl++) {
    for (int probe = 0; probe < nprobes; probe++) {
        // 1. Construct UDP packet
        packet.ttl = ttl;
        packet.dst_port = base_port + ttl;  // increment per hop
        packet.payload = small_data;
        
        // 2. Send packet, record send time
        send_time = clock();
        sendto(socket, &packet);
        
        // 3. Wait for ICMP response (with timeout ~5s)
        if (recvfrom(icmp_socket, &response, timeout)) {
            recv_time = clock();
            rtt = recv_time - send_time;
            
            // 4. Parse ICMP response
            if (response.type == ICMP_TIME_EXCEEDED) {
                hop_ip = response.src_ip;  // router IP
                printf("%d  %s  %.2fms\n", ttl, hop_ip, rtt);
            } else if (response.type == ICMP_DEST_UNREACH) {
                // Reached destination
                printf("%d  %s  %.2fms (final)\n", ttl, response.src_ip, rtt);
                return;  // stop
            }
        } else {
            printf("%d  * (timeout)\n", ttl);
        }
    }
}
```

---

### 5. **Scenario-Based Examples**

#### **Scenario A: Basic Cloud Path Discovery (AWS → On-Prem)**

**Setup:**
- Source: EC2 instance in us-east-1 VPC (10.0.1.5)
- Target: On-prem server via VPN (192.168.100.10)

**Execution:**
```bash
# UDP traceroute (Linux)
sudo traceroute -n -w 2 192.168.100.10

# Output:
 1  10.0.1.1        0.3 ms  (VPC router)
 2  172.31.0.1      1.2 ms  (AWS Transit Gateway)
 3  169.254.100.2   5.8 ms  (VPN endpoint, AWS side)
 4  169.254.100.1   6.1 ms  (VPN endpoint, on-prem side)
 5  192.168.1.1     6.5 ms  (On-prem core router)
 6  192.168.100.10  7.2 ms  (Target server)
```

**Analysis:**
- Hop 1-2: Intra-AWS routing
- Hop 3-4: VPN tunnel (IPsec overhead adds ~5ms)
- Hop 5-6: On-prem network
- **Security**: Exposed internal IPs (169.254.x.x VPN endpoints)

---

#### **Scenario B: Asymmetric Routing in Multi-Cloud**

**Setup:**
- Source: GKE pod in GCP us-central1
- Target: Azure VM in eastus via VPN peering

```bash
# TCP traceroute to port 443 (bypasses ICMP blocks)
sudo tcptraceroute -n 52.168.10.5 443

# Output:
 1  10.128.0.1       0.5 ms  (GKE node)
 2  10.128.10.1      1.0 ms  (GCP VPC router)
 3  169.254.1.1      8.2 ms  (Cloud Router/VPN)
 4  10.0.0.1        12.5 ms  (Azure vNet gateway)
 5  10.0.5.10       13.1 ms  (Azure internal LB)
 6  52.168.10.5     13.8 ms  (Target VM)
```

**Return Path (from Azure → GCP):**
```
Different path due to BGP policy! Goes via internet:
1  10.0.5.10 → 2 13.107.4.50 (Azure edge) → 3 * * * (blackhole) → ...
```

**Threat Model:**
- Asymmetric routes can bypass IDS/IPS in one direction
- Exposed peering IPs leak network topology
- **Mitigation:** Use Cloud NAT, private endpoints, disable ICMP responses at perimeter

---

#### **Scenario C: ECMP (Equal-Cost Multi-Path) Detection**

**Problem:** Standard traceroute shows different hops on each run due to load-balancing.

```bash
# Standard traceroute (non-deterministic)
traceroute google.com
# Run 1: hop 5 = 108.170.252.1
# Run 2: hop 5 = 108.170.252.33  (different!)

# Paris traceroute (flow-aware)
sudo paris-traceroute -n google.com
# Uses consistent 5-tuple (src/dst IP/port, proto) to ensure same path
```

**AWS Scenario:**
```
Source → NLB (4 targets) → Backend

Traceroute shows 4 different IPs at hop 3:
 3  10.0.1.10  or  10.0.1.20  or  10.0.1.30  or  10.0.1.40

Solution: Use source port pinning or scamper tool for ECMP topology mapping
```

---

### 6. **Protocol Deep-Dive: ICMP Messages**

**ICMP Type 11 (Time Exceeded):**
```c
struct icmp_time_exceeded {
    uint8_t  type;       // 11
    uint8_t  code;       // 0 = TTL exceeded in transit
    uint16_t checksum;
    uint32_t unused;
    // IP header + 8 bytes of original datagram (for matching)
    struct ip_header original_ip;
    uint8_t  original_data[8];
};
```

**Matching Logic:**
- Traceroute uses UDP source port or ICMP ID to correlate responses
- Router includes original IP header + 8 bytes in ICMP reply
- Source extracts UDP src port or ICMP seq number to match probes

---

### 7. **Failure Modes & Evasion**

| **Symptom**          | **Cause**                                  | **Security Impact**                  |
|----------------------|--------------------------------------------|--------------------------------------|
| `* * *` (no reply)   | Router rate-limits ICMP or drops TTL=0     | Hides infrastructure, breaks debug   |
| Wrong hop order      | ICMP replies queued/delayed asymmetrically | Misleads troubleshooting             |
| Same IP all hops     | NAT/proxy interception                     | Hides internal topology              |
| Abrupt termination   | Firewall blocks dest port                  | Recon blocked, use TCP traceroute    |

**Advanced Evasion (Red Team):**
```bash
# Firewalk: map firewall ACLs via TTL manipulation
sudo firewalk -n -p TCP -d 443 <target_ip> <gateway_ip>

# Finds which ports are allowed through firewall at each hop
```

---

### 8. **Security: Threat Model & Mitigations**

#### **Threats:**
1. **Topology Disclosure:** Reveals internal IPs, firewall boundaries, VPN endpoints
2. **DDoS Amplification:** Attacker spoofs source IP, triggers ICMP floods
3. **Recon for Lateral Movement:** Maps trust boundaries in hybrid cloud
4. **ICMP Tunneling:** Covert channels via ICMP data fields

#### **Mitigations:**

```bash
# 1. Rate-limit ICMP Type 11 generation (Linux)
iptables -A OUTPUT -p icmp --icmp-type time-exceeded -m limit --limit 10/sec -j ACCEPT
iptables -A OUTPUT -p icmp --icmp-type time-exceeded -j DROP

# 2. Disable ICMP at perimeter (cloud security groups)
# AWS Security Group: Block ICMP Type 11 outbound to internet
aws ec2 authorize-security-group-egress \
  --group-id sg-xxx \
  --ip-permissions IpProtocol=icmp,FromPort=11,ToPort=11,IpRanges=[{CidrIp=0.0.0.0/0}] \
  --revoke

# 3. Use private endpoints (no public IPs in path)
# Azure: Enable Private Link for cross-vNet traffic

# 4. Monitor for reconnaissance
# Detect sequential TTL probes in 5s window
# Zeek/Suricata rule:
alert icmp any any -> $HOME_NET any (msg:"Traceroute scan"; \
  itype:11; threshold:type threshold,track by_src,count 5,seconds 5; \
  classtype:network-scan; sid:100001;)
```

---

### 9. **Implementation: Minimal Traceroute in Go**

```go
package main

import (
    "fmt"
    "golang.org/x/net/icmp"
    "golang.org/x/net/ipv4"
    "net"
    "os"
    "time"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Println("Usage: go run traceroute.go <host>")
        os.Exit(1)
    }
    dst := os.Args[1]
    
    dstAddr, _ := net.ResolveIPAddr("ip4", dst)
    conn, _ := net.ListenPacket("ip4:icmp", "0.0.0.0")
    defer conn.Close()
    
    rawConn, _ := ipv4.NewRawConn(conn)
    
    for ttl := 1; ttl <= 30; ttl++ {
        // Build ICMP Echo packet
        msg := icmp.Message{
            Type: ipv4.ICMPTypeEcho, Code: 0,
            Body: &icmp.Echo{ID: os.Getpid(), Seq: ttl, Data: []byte("TRACE")},
        }
        wb, _ := msg.Marshal(nil)
        
        // Set TTL and send
        rawConn.SetTTL(ttl)
        start := time.Now()
        rawConn.WriteTo(wb, nil, dstAddr)
        
        // Read ICMP reply (timeout 3s)
        conn.SetReadDeadline(time.Now().Add(3 * time.Second))
        rb := make([]byte, 1500)
        n, peer, err := conn.ReadFrom(rb)
        rtt := time.Since(start)
        
        if err != nil {
            fmt.Printf("%2d  * * *\n", ttl)
            continue
        }
        
        rm, _ := icmp.ParseMessage(1, rb[:n])
        if rm.Type == ipv4.ICMPTypeTimeExceeded {
            fmt.Printf("%2d  %-15s  %.2f ms\n", ttl, peer.String(), float64(rtt.Microseconds())/1000)
        } else if rm.Type == ipv4.ICMPTypeEchoReply {
            fmt.Printf("%2d  %-15s  %.2f ms (final)\n", ttl, peer.String(), float64(rtt.Microseconds())/1000)
            break
        }
    }
}
```

**Build & Run:**
```bash
go mod init traceroute
go get golang.org/x/net/icmp
go get golang.org/x/net/ipv4
sudo go run traceroute.go 8.8.8.8

# Output:
 1  192.168.1.1      1.23 ms
 2  10.0.0.1         5.67 ms
 3  72.14.214.1      8.45 ms
 ...
10  8.8.8.8         12.34 ms (final)
```

---

### 10. **Testing & Validation**

```bash
# Test 1: Verify TTL decrement behavior
sudo hping3 -1 -t 1 -c 1 8.8.8.8  # ICMP, TTL=1, expect Type 11
sudo hping3 -1 -t 64 -c 1 8.8.8.8 # ICMP, TTL=64, expect Type 0

# Test 2: Compare UDP vs ICMP vs TCP paths
traceroute -I google.com        # ICMP
traceroute -T -p 443 google.com # TCP port 443
traceroute google.com           # UDP (default)

# Test 3: Detect ECMP load-balancing
for i in {1..10}; do traceroute -n -q 1 google.com | grep " 5 "; done | sort -u

# Test 4: Firewall ACL mapping
sudo nmap --traceroute --reason -Pn -p 80,443,22 <target>
```

---

### 11. **Cloud-Specific Considerations**

#### **AWS:**
- VPC Flow Logs **don't capture ICMP TTL Exceeded** (only ingress/egress at ENI)
- Use VPC Reachability Analyzer instead of traceroute for path validation
- Transit Gateway routes asymmetrically (return path may differ)

```bash
# AWS VPC path analysis
aws ec2 analyze-path --source <eni-id> --destination <ip> --protocol tcp --destination-port 443
```

#### **GCP:**
- Cloud Router doesn't respond to TTL=0 by default (blackhole in traceroute)
- Use Network Intelligence Center → Connectivity Tests

```bash
gcloud network-management connectivity-tests create test1 \
  --source-instance=vm1 --destination-ip=10.0.1.5 --protocol=TCP --destination-port=443
```

#### **Azure:**
- Network Watcher → Next Hop shows routing without traceroute
- ExpressRoute paths often show `* * *` due to MSEE (Microsoft Edge) filtering

```bash
az network watcher show-next-hop --resource-group rg1 --vm vm1 --nic nic1 --dest-ip 10.0.5.10
```

---

### 12. **Next 3 Steps**

1. **Implement Production Traceroute in Rust** with raw sockets, async I/O (tokio), and JSON output for observability pipelines. Add MTU discovery via DF bit. Time: 4-6 hours.

2. **Build ECMP Topology Mapper** using Paris traceroute algorithm in Go. Integrate with Prometheus for continuous path monitoring in K8s CNI (Cilium/Calico). Detect route flaps. Time: 6-8 hours.

3. **Deploy Defensive Monitoring** with Zeek/Suricata to detect traceroute recon patterns. Create Falco rules for K8s pods sending crafted TTL packets. Integrate alerts into SIEM (Splunk/ELK). Time: 3-4 hours.

---

### References

- RFC 792: ICMP Protocol Specification
- RFC 1393: Traceroute Using an IP Option
- Paris Traceroute: Brice Augustin et al., IEEE/ACM ToN 2006
- TCP Traceroute: Michael C. Toren, https://github.com/mct/tcptraceroute
- Linux `net/ipv4/route.c`: `ip_error()` function (TTL=0 handling)
- AWS VPC Reachability Analyzer: https://docs.aws.amazon.com/vpc/latest/reachability/
- Scamper (CAIDA tool): https://www.caida.org/catalog/software/scamper/

**Justification of Assumptions:**
- Assumed IPv4 (IPv6 uses Hop Limit, ICMP Type 3 for TTL Exceeded)
- Default 3 probes/hop for statistical RTT measurement
- UDP port range 33434-33534 per BSD traceroute convention
- 30-hop max depth (internet diameter typically <20)