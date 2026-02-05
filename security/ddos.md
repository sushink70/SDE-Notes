# DoS/DDoS: Protocol-Level to Cloud-Scale Analysis

**Summary**: DoS/DDoS attacks exploit fundamental asymmetries in network protocols and resource consumption. Attacks range from volumetric floods (UDP/ICMP amplification) to protocol exploitation (SYN floods, slowloris) to application-layer exhaustion (HTTP floods, API abuse). Defense requires multi-layer mitigation: network edge filtering (BCP38, ACLs), stateful middleboxes (SYN cookies, rate limiting), application-layer logic (CAPTCHAs, proof-of-work), and infrastructure over-provisioning. ISPs deploy BGP blackholing, scrubbing centers, and anycast. Cloud providers use global edge networks, ML-based detection, and elastic auto-scaling. Understanding packet flow, TCP state machines, HTTP connection lifecycle, and DNS resolution paths is critical to both attack and defense.

---

## 1. Core Concepts & Attack Taxonomy

### 1.1 Fundamental Asymmetry
**The Attack Surface**: Attacker sends small requests requiring disproportionate victim resources.

```
Attacker Cost vs Victim Cost:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Attack Type          | Attacker BW | Victim BW  | Victim CPU | Amplification
─────────────────────┼─────────────┼────────────┼────────────┼──────────────
DNS Amplification    | 1 Mbps      | 50 Mbps    | Low        | 50x
NTP Amplification    | 1 Mbps      | 556 Mbps   | Low        | 556x
SYN Flood            | 10 Mbps     | 10 Mbps    | High       | 1x (state)
HTTP Slowloris       | 1 Kbps      | 1 Kbps     | Very High  | 1000x (conn)
HTTP POST Flood      | 100 Mbps    | 100 Mbps   | Very High  | 10x (parsing)
```

### 1.2 Attack Layers (OSI Model Mapping)

```
Application Layer (L7)
├─ HTTP Floods (GET/POST/HEAD)
├─ DNS Query Floods
├─ API Abuse (GraphQL complexity, SQL injection attempts)
└─ Slowloris, Slow POST, R.U.D.Y

Transport Layer (L4)
├─ SYN Flood (TCP handshake exhaustion)
├─ UDP Flood
├─ TCP Connection Exhaustion
└─ TCP Reset Attacks

Network Layer (L3)
├─ ICMP Flood (Ping of Death, Smurf)
├─ IP Fragmentation Attacks
└─ Routing Table Exhaustion (BGP Hijack as DDoS vector)

Link Layer (L2)
└─ ARP Spoofing/Flooding (local network only)

Physical Layer (L1)
└─ Cable cuts, fiber taps (kinetic DDoS, rare)
```

---

## 2. Protocol-Level Attack Mechanics

### 2.1 SYN Flood (TCP State Exhaustion)

**TCP Three-Way Handshake**:
```
Client                        Server
  |                              |
  |──── SYN (seq=x) ────────────>|  (Server allocates TCB)
  |                              |  TCB = Transmission Control Block
  |<─── SYN-ACK (seq=y,ack=x+1)─|  (半開き状態、メモリ消費)
  |                              |
  |──── ACK (ack=y+1) ──────────>|  (ESTABLISHED)
```

**Attack Flow**:
1. Attacker sends millions of SYN packets with **spoofed source IPs**
2. Server allocates TCB (512-1024 bytes each) and waits for ACK
3. ACK never arrives (spoofed IP unreachable or non-existent)
4. Server's backlog queue (`/proc/sys/net/ipv4/tcp_max_syn_backlog`) fills
5. Legitimate connections rejected

**Under the Hood - Linux Kernel**:
```c
// net/ipv4/tcp_ipv4.c - simplified
int tcp_v4_conn_request(struct sock *sk, struct sk_buff *skb) {
    struct request_sock *req;
    
    // Check SYN backlog
    if (sk_acceptq_is_full(sk) && inet_csk_reqsk_queue_young(sk) > 1) {
        goto drop;  // Reject if backlog full
    }
    
    // Allocate request_sock (TCB precursor)
    req = inet_reqsk_alloc(&tcp_request_sock_ops, sk, !want_cookie);
    
    // Store state, send SYN-ACK
    tcp_v4_send_synack(sk, dst, req, ...);
    return 0;
    
drop:
    NET_INC_STATS(sock_net(sk), LINUX_MIB_LISTENDROPS);
    return 0;
}
```

**Kernel Tuning (Defense)**:
```bash
# /etc/sysctl.conf
net.ipv4.tcp_syncookies = 1               # Enable SYN cookies
net.ipv4.tcp_max_syn_backlog = 4096       # Increase backlog
net.ipv4.tcp_synack_retries = 2           # Reduce retries (default 5)
net.ipv4.tcp_syn_retries = 2
net.core.somaxconn = 1024                 # Accept queue size
net.ipv4.tcp_abort_on_overflow = 1        # Drop instead of retry
```

**SYN Cookies Mechanism**:
- Server doesn't allocate TCB on SYN
- Encodes connection state in SYN-ACK sequence number:
  ```
  seq_num = hash(src_ip, src_port, dst_ip, dst_port, timestamp, secret)
  ```
- On ACK receipt, validates seq_num and reconstructs TCB
- **Trade-off**: Loses TCP options (window scaling, SACK), slight CPU overhead

### 2.2 DNS Amplification

**Amplification Factor Calculation**:
```
Request:  60 bytes (UDP header + DNS query for ANY record)
Response: 3000+ bytes (full zone transfer or large TXT records)
Amplification: 50x typical, 100x+ possible
```

**Attack Mechanism**:
```
Attacker (spoofed src=Victim IP)          Open Resolver          Victim
     |──── DNS Query (ANY example.com) ──────>|                     |
     |      60 bytes, src=Victim IP            |                     |
     |                                         |─── Response ──────>|
     |                                         |   3000 bytes        |
     |                                         |                     |
     (Repeat with 1000s of resolvers)                               ↓
                                                            Bandwidth exhaustion
```

**Packet Structure (DNS Query)**:
```
UDP Header (8 bytes):
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Src Port    │ Dst Port    │ Length      │ Checksum    │
│ (random)    │ 53          │ 60          │ ...         │
└─────────────┴─────────────┴─────────────┴─────────────┘

DNS Query (52 bytes):
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Transaction │ Flags       │ Questions   │ Answer RRs  │
│ ID          │ 0x0100      │ 1           │ 0           │
├─────────────┴─────────────┴─────────────┴─────────────┤
│ Query: example.com ANY (QTYPE=255)                     │
└─────────────────────────────────────────────────────────┘
```

**Mitigation - DNS Resolver Side**:
```bash
# BIND9 - /etc/bind/named.conf.options
options {
    rate-limit {
        responses-per-second 5;
        window 5;
        slip 2;  # Send truncated response every 2nd
    };
    
    # Disable recursion for public IPs
    allow-recursion { localnets; localhost; };
    
    # Response Rate Limiting (RRL)
    max-cache-size 256M;
};
```

**Mitigation - Network Edge (BCP38)**:
```bash
# iptables - Drop spoofed packets (egress filtering)
iptables -A OUTPUT -s ! 203.0.113.0/24 -j DROP  # Allow only our subnet

# Cisco IOS ACL
ip access-list extended ANTI_SPOOF
 permit ip 203.0.113.0 0.0.0.255 any
 deny ip any any log
interface GigabitEthernet0/1
 ip access-group ANTI_SPOOF out
```

### 2.3 HTTP Slowloris (Connection Exhaustion)

**Attack Principle**: Keep HTTP connections open indefinitely with incomplete requests.

```
Client                           Web Server (Apache/Nginx)
  |──── GET / HTTP/1.1 ──────────>|  (Allocate worker thread)
  |──── Host: victim.com ─────────>|  (Wait for headers)
  |──── X-Custom: partial... ─────>|  (Still waiting...)
  |     [10 second delay]           |
  |──── X-Another: more... ────────>|  (Thread still allocated)
  |     [10 second delay]           |
  |     ...                         |  (Worker pool exhausted)
  |     [Never sends final \r\n\r\n]|
  
  Repeat with 500-5000 connections → All workers blocked
```

**Apache Worker Exhaustion**:
```apache
# httpd.conf - Default (vulnerable)
<IfModule mpm_prefork_module>
    StartServers          5
    MinSpareServers       5
    MaxSpareServers      10
    MaxRequestWorkers   150  ← Only 150 concurrent connections
    MaxConnectionsPerChild 0
</IfModule>

# 200 slowloris connections = server unresponsive
```

**Defense - Nginx (Event-Driven)**:
```nginx
# nginx.conf
http {
    # Close slow clients
    client_body_timeout 10s;   # POST body must arrive in 10s
    client_header_timeout 10s; # Headers must complete in 10s
    keepalive_timeout 15s;
    send_timeout 10s;
    
    # Limit connections per IP
    limit_conn_zone $binary_remote_addr zone=addr:10m;
    limit_conn addr 10;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;
    limit_req zone=one burst=20 nodelay;
}
```

**Defense - HAProxy**:
```haproxy
# haproxy.cfg
defaults
    timeout client 10s
    timeout server 10s
    timeout connect 5s
    
frontend http-in
    bind *:80
    # Track connection rate per IP
    stick-table type ip size 100k expire 30s store conn_rate(10s)
    tcp-request connection track-sc0 src
    tcp-request connection reject if { sc_conn_rate(0) gt 20 }
```

---

## 3. Infrastructure-Level Defenses

### 3.1 ISP-Level Mitigation

```
┌─────────────────────────────────────────────────────────────────┐
│                    ISP Network Architecture                      │
└─────────────────────────────────────────────────────────────────┘

Internet ─┬─> Border Router (BGP)
          │   ├─ BCP38 Egress Filtering
          │   ├─ RTBH (Remotely Triggered Black Hole)
          │   └─ FlowSpec (RFC 5575)
          │
          ├─> DDoS Scrubbing Center
          │   ├─ Traffic diversion (BGP Anycast)
          │   ├─ Packet inspection (DPI)
          │   ├─ Rate limiting
          │   └─ Clean traffic forwarding (GRE tunnel)
          │
          ├─> CDN/Edge PoPs
          │   ├─ Anycast IP distribution
          │   ├─ Local caching
          │   └─ Origin shielding
          │
          └─> Customer Servers
              └─ DDoS mitigation appliances (local)
```

#### 3.1.1 BGP Blackholing (RTBH)

**Concept**: Announce victim IP with special community tag → upstream drops traffic.

```bash
# Cisco IOS - RTBH Configuration
# 1. Define blackhole community
ip community-list standard BLACKHOLE permit 65000:666

# 2. Route-map to set next-hop to null
route-map BLACKHOLE permit 10
 match community BLACKHOLE
 set ip next-hop 192.0.2.1  # RFC 3849 blackhole IP
 set local-preference 200

# 3. BGP announcement
router bgp 65000
 neighbor 203.0.113.1 remote-as 65001
 neighbor 203.0.113.1 send-community
 
# 4. Trigger blackhole for victim IP
ip route 198.51.100.10 255.255.255.255 Null0
router bgp 65000
 network 198.51.100.10 mask 255.255.255.255
 neighbor 203.0.113.1 route-map BLACKHOLE out

# Upstream ISP drops all traffic to 198.51.100.10
```

**Trade-off**: Victim is offline, but attack stops affecting other customers.

#### 3.1.2 FlowSpec (RFC 5575)

**Distributed ACL via BGP**:
```bash
# Juniper - FlowSpec rule
set policy-options policy-statement FLOWSPEC term BLOCK_SYN_FLOOD from protocol tcp
set policy-options policy-statement FLOWSPEC term BLOCK_SYN_FLOOD from destination-port 80
set policy-options policy-statement FLOWSPEC term BLOCK_SYN_FLOOD from tcp-flags syn
set policy-options policy-statement FLOWSPEC term BLOCK_SYN_FLOOD from packet-length 40-60
set policy-options policy-statement FLOWSPEC term BLOCK_SYN_FLOOD then discard

# BGP propagates this rule to all routers
```

#### 3.1.3 Scrubbing Center Flow

```
Normal Traffic:
Client → ISP Router → Customer Server

Under Attack:
Client → ISP Router ──BGP Anycast──> Scrubbing Center
                                      ├─ DPI Analysis
                                      ├─ Drop malicious packets
                                      └─ GRE Tunnel ──> Customer Server
                                         (clean traffic)
```

**GRE Tunnel Setup**:
```bash
# Customer server side
ip tunnel add gre1 mode gre remote 203.0.113.50 local 198.51.100.10
ip link set gre1 up
ip addr add 10.0.0.2/30 dev gre1
ip route add default via 10.0.0.1 dev gre1 table 100
ip rule add from 198.51.100.10 table 100

# Scrubbing center forwards cleaned traffic through GRE
```

### 3.2 Cloud Provider Architectures

#### 3.2.1 AWS Shield & CloudFront

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS DDoS Defense Stack                       │
└─────────────────────────────────────────────────────────────────┘

User Request
    ↓
Route53 (Anycast DNS)
├─ Health checks
├─ Geolocation routing
└─ Shuffle sharding
    ↓
CloudFront Edge (400+ PoPs)
├─ AWS Shield Standard (automatic L3/L4)
│  ├─ SYN flood mitigation (SYN cookies)
│  ├─ UDP reflection filtering
│  └─ ICMP flood absorption
├─ AWS Shield Advanced (optional, L7)
│  ├─ ML-based anomaly detection
│  ├─ DDoS cost protection
│  └─ DRT (DDoS Response Team)
└─ WAF (Web Application Firewall)
   ├─ Rate limiting rules
   ├─ Geo-blocking
   └─ Signature-based blocking
    ↓
ALB/NLB (Regional)
├─ Auto-scaling (surge capacity)
├─ Connection draining
└─ TLS termination
    ↓
EC2/ECS/EKS (Target)
└─ Security Groups (stateful firewall)
```

**CloudFront Distribution Config** (Terraform):
```hcl
resource "aws_cloudfront_distribution" "main" {
  enabled = true
  
  # Origin shielding (reduce origin load)
  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb"
    
    origin_shield {
      enabled              = true
      origin_shield_region = "us-east-1"
    }
  }
  
  # Geo-restriction
  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = ["US", "CA", "GB"]
    }
  }
  
  # WAF association
  web_acl_id = aws_wafv2_web_acl.ddos_protection.arn
}

resource "aws_wafv2_web_acl" "ddos_protection" {
  name  = "ddos-protection"
  scope = "CLOUDFRONT"
  
  rule {
    name     = "RateLimitRule"
    priority = 1
    
    action {
      block {}
    }
    
    statement {
      rate_based_statement {
        limit              = 2000  # Requests per 5 min
        aggregate_key_type = "IP"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }
}
```

**Shield Advanced - Automatic Mitigation**:
```python
# AWS Shield Advanced uses ML models to detect attacks
# Baseline: Normal traffic patterns (requests/sec, packet size distribution)
# Detection: Chi-squared test for anomalies

import boto3

# Enable Shield Advanced
client = boto3.client('shield')
response = client.create_protection(
    Name='WebServer',
    ResourceArn='arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/1234567890abcdef'
)

# DRT (DDoS Response Team) auto-engages for Advanced customers
```

#### 3.2.2 GCP Cloud Armor

```yaml
# cloud-armor-policy.yaml
name: "ddos-protection"
rules:
  # Throttle rule (Layer 7 rate limiting)
  - action: "throttle"
    priority: 1000
    match:
      expr:
        expression: "origin.region_code == 'US'"
    rateLimitOptions:
      conformAction: "allow"
      exceedAction: "deny(429)"
      rateLimitThreshold:
        count: 100
        intervalSec: 60
      enforceOnKey: IP
  
  # Adaptive Protection (ML-based)
  - action: "deny(403)"
    priority: 900
    match:
      expr:
        expression: "evaluatePreconfiguredExpr('cve-canary')"
  
  # Geo-fencing
  - action: "deny(403)"
    priority: 800
    match:
      expr:
        expression: "origin.region_code == 'CN' || origin.region_code == 'RU'"

adaptiveProtectionConfig:
  layer7DdosDefenseConfig:
    enable: true
```

**Deployment**:
```bash
gcloud compute security-policies create ddos-protection \
    --file-name cloud-armor-policy.yaml

gcloud compute backend-services update web-backend \
    --security-policy ddos-protection \
    --global
```

**GCP Anycast Architecture**:
```
User Request (203.0.113.100)
    ↓
Google Front End (GFE) - Nearest PoP
├─ TCP Proxy (SYN flood mitigation)
├─ TLS termination
└─ HTTP/2 optimization
    ↓
Cloud Armor (Policy Engine)
├─ L7 DDoS detection
├─ OWASP Top 10 rules
└─ Rate limiting
    ↓
Load Balancer (Global/Regional)
├─ Maglev hashing (connection persistence)
└─ Health checks
    ↓
GCE/GKE Instances (Auto-scaled)
```

#### 3.2.3 Azure DDoS Protection

```hcl
# Terraform - Azure DDoS Protection Plan
resource "azurerm_network_ddos_protection_plan" "main" {
  name                = "ddos-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_virtual_network" "main" {
  name                = "vnet-main"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  
  ddos_protection_plan {
    id     = azurerm_network_ddos_protection_plan.main.id
    enable = true
  }
}

resource "azurerm_public_ip" "main" {
  name                = "public-ip"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
  
  # DDoS protection automatically applied
}
```

**Azure Traffic Analytics (Attack Detection)**:
```bash
# Enable diagnostic logs
az monitor diagnostic-settings create \
    --name ddos-logs \
    --resource /subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Network/publicIPAddresses/{ip} \
    --logs '[{"category": "DDoSProtectionNotifications", "enabled": true}]' \
    --workspace /subscriptions/{sub-id}/resourcegroups/{rg}/providers/microsoft.operationalinsights/workspaces/{workspace}

# Query attack metrics (KQL)
AzureDiagnostics
| where ResourceType == "PUBLICIPADDRESSES"
| where Category == "DDoSProtectionNotifications"
| where TimeGenerated > ago(1h)
| summarize AttackVectors=make_set(attackType_s), MaxPPS=max(packetsPerSecond_d) by TimeGenerated
```

---

## 4. Application-Level Hardening

### 4.1 Golang HTTP Server (Production-Grade)

```go
// main.go - DDoS-resistant HTTP server
package main

import (
    "context"
    "fmt"
    "net"
    "net/http"
    "sync"
    "time"

    "golang.org/x/time/rate"
)

// Per-IP rate limiter
type IPRateLimiter struct {
    ips map[string]*rate.Limiter
    mu  *sync.RWMutex
    r   rate.Limit  // Requests per second
    b   int         // Burst size
}

func NewIPRateLimiter(r rate.Limit, b int) *IPRateLimiter {
    return &IPRateLimiter{
        ips: make(map[string]*rate.Limiter),
        mu:  &sync.RWMutex{},
        r:   r,
        b:   b,
    }
}

func (i *IPRateLimiter) GetLimiter(ip string) *rate.Limiter {
    i.mu.Lock()
    defer i.mu.Unlock()

    limiter, exists := i.ips[ip]
    if !exists {
        limiter = rate.NewLimiter(i.r, i.b)
        i.ips[ip] = limiter
    }

    return limiter
}

// Middleware
func (i *IPRateLimiter) Limit(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ip, _, err := net.SplitHostPort(r.RemoteAddr)
        if err != nil {
            http.Error(w, "Internal error", http.StatusInternalServerError)
            return
        }

        limiter := i.GetLimiter(ip)
        if !limiter.Allow() {
            http.Error(w, "Too many requests", http.StatusTooManyRequests)
            return
        }

        next.ServeHTTP(w, r)
    })
}

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hello, %s!", r.URL.Path[1:])
    })

    // Rate limiter: 10 req/s per IP, burst of 20
    limiter := NewIPRateLimiter(10, 20)

    server := &http.Server{
        Addr:         ":8080",
        Handler:      limiter.Limit(mux),
        ReadTimeout:  5 * time.Second,  // Slowloris defense
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  120 * time.Second,
        
        // Connection limits
        MaxHeaderBytes: 1 << 20, // 1 MB
        
        // TLS config (if HTTPS)
        // TLSConfig: &tls.Config{
        //     MinVersion: tls.VersionTLS13,
        // },
    }

    // Graceful shutdown
    go func() {
        if err := server.ListenAndServe(); err != http.ErrServerClosed {
            panic(err)
        }
    }()

    // Wait for interrupt
    // ... (signal handling code)
}
```

**Build & Run**:
```bash
go mod init ddos-resistant-server
go get golang.org/x/time/rate
go build -o server main.go
./server

# Test with hey (load testing tool)
hey -n 10000 -c 100 -q 50 http://localhost:8080/
# Should see 429 errors for clients exceeding 10 req/s
```

### 4.2 Rust Async Server (Tokio)

```rust
// main.rs - DDoS-resistant async server
use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use warp::{Filter, Rejection, Reply};

// Rate limiter state
#[derive(Clone)]
struct RateLimiter {
    ips: Arc<RwLock<HashMap<String, (Instant, u32)>>>,
    max_requests: u32,
    window: Duration,
}

impl RateLimiter {
    fn new(max_requests: u32, window: Duration) -> Self {
        Self {
            ips: Arc::new(RwLock::new(HashMap::new())),
            max_requests,
            window,
        }
    }

    async fn check(&self, ip: String) -> Result<(), Rejection> {
        let mut ips = self.ips.write().await;
        let now = Instant::now();

        if let Some((last_reset, count)) = ips.get_mut(&ip) {
            if now.duration_since(*last_reset) > self.window {
                *last_reset = now;
                *count = 1;
            } else if *count >= self.max_requests {
                return Err(warp::reject::custom(TooManyRequests));
            } else {
                *count += 1;
            }
        } else {
            ips.insert(ip, (now, 1));
        }

        Ok(())
    }
}

#[derive(Debug)]
struct TooManyRequests;
impl warp::reject::Reject for TooManyRequests {}

#[tokio::main]
async fn main() {
    let limiter = RateLimiter::new(100, Duration::from_secs(60));

    let rate_limit = warp::addr::remote()
        .and_then(move |addr: Option<SocketAddr>| {
            let limiter = limiter.clone();
            async move {
                let ip = addr.unwrap().ip().to_string();
                limiter.check(ip).await
            }
        });

    let routes = warp::path::end()
        .and(rate_limit)
        .map(|| "Hello, World!");

    warp::serve(routes)
        .run(([0, 0, 0, 0], 8080))
        .await;
}
```

**Cargo.toml**:
```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
warp = "0.3"
```

```bash
cargo build --release
./target/release/ddos-resistant-server
```

---

## 5. Threat Model & Mitigation Matrix

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Attack Type     │ Layer │ Mitigation                │ Detection Method    │
├─────────────────┼───────┼───────────────────────────┼─────────────────────┤
│ SYN Flood       │ L4    │ SYN cookies, rate limit   │ Netflow, conn/s spike│
│ UDP Flood       │ L4    │ BCP38, rate limit, ACL    │ pps threshold        │
│ DNS Amplif.     │ L4/L7 │ RRL, recursion ACL        │ Query rate spike     │
│ HTTP Flood      │ L7    │ WAF, rate limit, CAPTCHA  │ req/s anomaly (ML)   │
│ Slowloris       │ L7    │ Timeouts, conn limits     │ Incomplete requests  │
│ NTP Amplif.     │ L4    │ Disable monlist, BCP38    │ Reflection detect    │
│ ICMP Flood      │ L3    │ Rate limit, drop at edge  │ ICMP pps threshold   │
│ BGP Hijack      │ L3    │ ROA, RPKI, prefix filter  │ Route monitoring     │
└───────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Detection Pipeline (Prometheus + eBPF)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'ebpf_exporter'  # DDoS metrics
    static_configs:
      - targets: ['localhost:9435']
```

**eBPF Packet Counter** (for detection):
```c
// packet_counter.bpf.c
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>

BPF_HASH(syn_count, u32, u64);  // IP -> SYN count

int count_syn_packets(struct __sk_buff *skb) {
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return 0;

    if (eth->h_proto != htons(ETH_P_IP))
        return 0;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return 0;

    if (ip->protocol != IPPROTO_TCP)
        return 0;

    struct tcphdr *tcp = (void *)(ip + 1);
    if ((void *)(tcp + 1) > data_end)
        return 0;

    // Check for SYN flag
    if (tcp->syn && !tcp->ack) {
        u32 saddr = ip->saddr;
        u64 *count = syn_count.lookup(&saddr);
        if (count) {
            (*count)++;
        } else {
            u64 init = 1;
            syn_count.update(&saddr, &init);
        }
    }

    return 0;
}
```

**Alert Rule** (Prometheus):
```yaml
# alert.rules.yml
groups:
  - name: ddos
    interval: 10s
    rules:
      - alert: SYNFloodDetected
        expr: rate(ebpf_syn_packets_total[1m]) > 10000
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Possible SYN flood attack"
          description: "SYN packet rate is {{ $value }} pps"
```

---

## 6. Testing & Validation

### 6.1 SYN Flood Test (hping3)

```bash
# Install hping3
apt-get install hping3

# SYN flood test (LOCAL TESTING ONLY)
# Target: 192.168.1.100:80
hping3 -S -p 80 --flood --rand-source 192.168.1.100

# Explanation:
# -S: SYN flag
# -p 80: Target port
# --flood: Send as fast as possible
# --rand-source: Random source IPs (spoofing)

# Monitor on target:
watch -n 1 'netstat -an | grep SYN_RECV | wc -l'
# Should see SYN_RECV connections spike
```

### 6.2 HTTP Flood Test (slowhttptest)

```bash
# Install slowhttptest
git clone https://github.com/shekyan/slowhttptest.git
cd slowhttptest
./configure && make && make install

# Slowloris test
slowhttptest -c 1000 -H -g -o slowloris_stats -i 10 -r 200 -t GET -u http://target.com -x 24

# Explanation:
# -c 1000: 1000 connections
# -H: Slowloris mode
# -i 10: 10 second interval between headers
# -r 200: Connections per second
# -x 24: Max test duration (seconds)

# Slow POST test
slowhttptest -c 1000 -B -g -o slowpost_stats -i 110 -r 200 -s 8192 -t POST -u http://target.com -x 24
```

### 6.3 Load Testing (k6)

```javascript
// load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 100 },  // Ramp up to 100 users
    { duration: '3m', target: 100 },  // Stay at 100 users
    { duration: '1m', target: 500 },  // Spike to 500
    { duration: '2m', target: 500 },
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests < 500ms
    http_req_failed: ['rate<0.1'],    // Error rate < 10%
  },
};

export default function () {
  const res = http.get('http://target.com');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

```bash
k6 run --vus 100 --duration 5m load_test.js
```

---

## 7. Cloud-Specific Configurations

### 7.1 Kubernetes Network Policies (Anti-DDoS)

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: rate-limit-ingress
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080

---
# ConfigMap for nginx-ingress rate limiting
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-configuration
  namespace: ingress-nginx
data:
  limit-req-zone: "$binary_remote_addr zone=one:10m rate=10r/s"
  limit-req: "zone=one burst=20 nodelay"
  limit-conn-zone: "$binary_remote_addr zone=addr:10m"
  limit-conn: "addr 10"
```

### 7.2 Istio Service Mesh (L7 Rate Limiting)

```yaml
# envoy-filter.yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: rate-limit
  namespace: istio-system
spec:
  workloadSelector:
    labels:
      app: productpage
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: SIDECAR_INBOUND
      listener:
        filterChain:
          filter:
            name: "envoy.filters.network.http_connection_manager"
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.local_ratelimit
        typed_config:
          "@type": type.googleapis.com/udpa.type.v1.TypedStruct
          type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
          value:
            stat_prefix: http_local_rate_limiter
            token_bucket:
              max_tokens: 100
              tokens_per_fill: 10
              fill_interval: 1s
            filter_enabled:
              runtime_key: local_rate_limit_enabled
              default_value:
                numerator: 100
                denominator: HUNDRED
            filter_enforced:
              runtime_key: local_rate_limit_enforced
              default_value:
                numerator: 100
                denominator: HUNDRED
```

---

## 8. Rollout & Rollback Plan

### 8.1 Gradual Mitigation Deployment

```bash
# Stage 1: Observability (1 week)
# Deploy metrics collection without blocking
kubectl apply -f prometheus-ebpf-exporter.yaml
# Monitor baselines: req/s, conn/s, packet rates

# Stage 2: Soft Limits (1 week)
# Enable rate limiting in log-only mode
# nginx.conf: limit_req zone=one burst=20 nodelay;
# Check logs for would-be blocks:
grep "limiting requests" /var/log/nginx/error.log | wc -l

# Stage 3: Progressive Enforcement (2 weeks)
# Week 1: 10% traffic enforcement
# Week 2: 50% traffic enforcement
# Week 3: 100% traffic enforcement

# Use feature flags (e.g., LaunchDarkly)
if feature_flag("rate_limit_enforcement", user_id) {
    apply_rate_limit()
}

# Stage 4: Automated Response (1 week)
# Enable auto-scaling, auto-blocking
kubectl autoscale deployment web --cpu-percent=70 --min=3 --max=50

# Rollback Procedure
# 1. Disable rate limiting (instant):
kubectl set env deployment/web RATE_LIMIT_ENABLED=false

# 2. Revert network policies:
kubectl delete networkpolicy rate-limit-ingress

# 3. Emergency: Drain traffic to backup cluster:
# Update DNS TTL to 60s, change A record to backup
```

---

## 9. References

### 9.1 RFCs & Standards
- RFC 4987: TCP SYN Flooding Attacks and Common Mitigations
- RFC 5575: FlowSpec (BGP Flow Specification)
- RFC 2827: BCP38 (Ingress Filtering)
- RFC 6891: EDNS0 (DNS query size limitation)
- RFC 7706: Decreasing DNS Amplification Attack Effectiveness

### 9.2 Tools
- **Attack Simulation**: hping3, LOIC (Low Orbit Ion Cannon), slowhttptest
- **Defense**: fail2ban, iptables, nftables, ModSecurity (WAF)
- **Monitoring**: Prometheus + eBPF, Netflow, sFlow, Wireshark
- **Load Testing**: k6, Apache JMeter, Gatling, hey

### 9.3 Cloud Documentation
- AWS Shield: https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html
- GCP Cloud Armor: https://cloud.google.com/armor/docs
- Azure DDoS Protection: https://learn.microsoft.com/en-us/azure/ddos-protection/

---

## Next 3 Steps

1. **Build Lab Environment**:
   ```bash
   # Spin up test VMs (attacker, victim, monitor)
   vagrant init ubuntu/jammy64
   # Configure iptables, install hping3, prometheus
   # Run controlled SYN flood, measure mitigation effectiveness
   ```

2. **Deploy Production Rate Limiting**:
   - Start with Nginx + Lua rate limiter in staging
   - Validate with k6 load tests (threshold: p95 < 200ms)
   - Roll out to 10% production traffic via canary deployment

3. **Implement eBPF-based Detection**:
   ```bash
   # Install BCC tools
   apt-get install bpfcc-tools linux-headers-$(uname -r)
   # Write custom XDP program to drop SYN floods at NIC level
   # Test with 100k pps synthetic traffic
   ```

**Verification Commands**:
```bash
# Check SYN cookies enabled
sysctl net.ipv4.tcp_syncookies

# Monitor connection states
ss -tan state syn-recv | wc -l

# Analyze packet drops
nstat -az | grep -i drop

# CloudFlare-style challenge (CAPTCHA alternative)
# Generate proof-of-work challenge in HTTP response
```

Let me know which attack vector or defense mechanism you want to dive deeper into, or if you need architecture designs for multi-region DDoS resilience.

# Application-Level & Local DDoS: Algorithmic Complexity Attacks

**Summary**: Application-level DDoS exploits computational asymmetry in data structures, algorithms, and business logic rather than network bandwidth. Attackers trigger O(n²) or worse operations (hash collisions, regex backtracking, GraphQL query depth, database N+1 queries) with minimal input. Detection requires instrumentation of CPU time per request, memory allocation tracking, query plan analysis, and cardinality estimation. Defense involves algorithmic auditing (complexity analysis), resource quotas (CPU/memory limits per request), circuit breakers, and defensive data structure choices (randomized hashing, bloom filters, trie-based routing). Unlike network DDoS, these attacks succeed even from single IPs with low bandwidth because they weaponize application logic itself.

---

## 1. Application-Level Attack Surface

### 1.1 Computational Asymmetry Map

```
Attack Input Size vs Victim CPU/Memory Consumption:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Attack Type              | Input    | CPU Time    | Memory      | Complexity
─────────────────────────┼──────────┼─────────────┼─────────────┼───────────
Hash Collision           | 1 KB     | 10s         | 100 MB      | O(n²)
ReDoS (Regex)            | 100 bytes| 60s         | 1 MB        | O(2ⁿ)
JSON Deep Nesting        | 10 KB    | 5s          | 500 MB      | O(depth)
GraphQL Query Bomb       | 2 KB     | 30s         | 1 GB        | O(n^depth)
XML Entity Expansion     | 1 KB     | 1s          | 3 GB        | O(expansions)
Database N+1 Query       | 50 bytes | 10s         | 50 MB       | O(n*m)
Zip Bomb                 | 42 KB    | 0.1s        | 4.5 PB      | O(ratio)
Algorithmic Sort Attack  | 1 KB     | 20s         | 10 MB       | O(n²)
```

---

## 2. Hash Collision Attacks (Hash Table DoS)

### 2.1 Hash Table Fundamentals

**Ideal Hash Function**:
```
┌─────────────────────────────────────────────────────────────┐
│ Hash Table: O(1) average case for insert/lookup/delete     │
└─────────────────────────────────────────────────────────────┘

Key → hash() → Index → Bucket
"user123" → 0x4AF2 → 42 → [("user123", data)]

Collision Resolution:
1. Chaining (linked list)
   Bucket[42] → ["user123"] → ["user456"] → ["user789"]
   
2. Open Addressing (linear probing)
   Bucket[42] occupied → try Bucket[43] → try Bucket[44]...
```

**Hash Collision Attack**:
```
Attacker Goal: Force all keys into same bucket
Result: O(1) operations degrade to O(n)

Normal Distribution:
Buckets: [1] [2] [1] [0] [3] [1] [2] [0] ...
Lookup: O(1) average

Attack Distribution:
Buckets: [0] [0] [0] [0] [10000] [0] [0] [0] ...
Lookup: O(n) - traverses entire chain
```

### 2.2 Vulnerable Code Example (Python)

**Vulnerable Django View** (pre-3.2.10):
```python
# views.py - VULNERABLE
from django.http import JsonResponse

def process_form(request):
    # Django parses POST data into dict using hash table
    # Attacker sends POST with colliding keys
    data = request.POST  # Internally uses dict
    
    # O(n²) operation if all keys collide
    results = {}
    for key in data:  # Iterates through hash buckets
        results[key] = data[key]  # Each lookup is O(n) in worst case
    
    return JsonResponse(results)

# Attack payload (simplified):
# POST /process with 10000 keys that all hash to same bucket
# Total time: O(n²) = O(10000²) = 100M operations
```

**Hash Collision Generation** (Python 2.x vulnerable):
```python
# exploit.py - Generates colliding keys for Python 2.x dict
def hash_py2(s):
    """Python 2.x string hash (simplified)"""
    if not s:
        return 0
    x = ord(s[0]) << 7
    for c in s:
        x = ((1000003 * x) ^ ord(c)) & 0xFFFFFFFF
    return x ^ len(s)

# Find collisions using meet-in-the-middle
collisions = []
target_hash = hash_py2("base")

# Generate keys with same hash
import itertools
for combo in itertools.product("abcdefghij", repeat=5):
    key = "".join(combo)
    if hash_py2(key) == target_hash:
        collisions.append(key)
        if len(collisions) >= 10000:
            break

# Send POST request
import requests
payload = {key: "value" for key in collisions}
requests.post("http://victim.com/process", data=payload)
# Server spends 10+ seconds processing this single request
```

**Underlying Hash Table Code** (CPython `dictobject.c`):
```c
// Python 2.x dict implementation (VULNERABLE)
static PyDictEntry *
lookdict_string(PyDictObject *mp, PyObject *key, long hash)
{
    size_t i;
    size_t perturb;
    PyDictEntry *freeslot;
    size_t mask = (size_t)mp->ma_mask;
    PyDictEntry *ep0 = mp->ma_table;
    PyDictEntry *ep;

    // Initial index from hash
    i = hash & mask;
    ep = &ep0[i];
    
    // If collision, linear probing (SLOW with many collisions)
    if (ep->me_key == NULL || ep->me_key == key)
        return ep;
    
    if (ep->me_key == dummy)
        freeslot = ep;
    else {
        // Key doesn't match, start probing
        // With hash collisions, this loops many times
        for (perturb = hash; ; perturb >>= 5) {
            i = (i << 2) + i + perturb + 1;  // Perturbation formula
            ep = &ep0[i & mask];
            
            if (ep->me_key == NULL)
                return ep;
            if (ep->me_key == key)
                return ep;
            // Continue searching... O(n) in worst case
        }
    }
}
```

### 2.3 Mitigation: Randomized Hashing

**Python 3.4+ Defense** (PYTHONHASHSEED):
```python
# Python 3 dict uses SipHash with random seed
import sys
print(sys.hash_info)
# hash_info(width=64, modulus=2305843009213693951, 
#           inf=314159, nan=0, imag=1000003, algorithm='siphash24', 
#           hash_bits=64, seed_bits=128, cutoff=0)

# Random seed changes per interpreter invocation
# Same key → different hash across runs
$ python3 -c "print(hash('test'))"
-4850370454444142598

$ python3 -c "print(hash('test'))"
7382479023847293847  # Different!
```

**SipHash Implementation** (Rust):
```rust
// Secure hash function resistant to collision attacks
use siphasher::sip::SipHasher;
use std::hash::{Hash, Hasher};
use std::collections::HashMap;

fn main() {
    // Random seed per HashMap instance
    let mut map = HashMap::new();
    
    // Attacker cannot predict hash values
    map.insert("key1", "value1");
    map.insert("key2", "value2");
    
    // Even if attacker knows the hash algorithm,
    // random seed makes collision search infeasible
}

// Internal: SipHash-2-4 (2 compression rounds, 4 finalization rounds)
// Input: 128-bit key (random), message
// Output: 64-bit hash
// Complexity: O(message_length) with cryptographic properties
```

**Go's map with Random Seed**:
```go
// runtime/map.go (simplified)
const (
    hashSeed = uintptr(fastrand())  // Random seed at init
)

func mapaccess1(t *maptype, h *hmap, key unsafe.Pointer) unsafe.Pointer {
    hash := t.hasher(key, hashSeed)  // Seed prevents collision attacks
    m := bucketMask(h.B)
    b := (*bmap)(add(h.buckets, (hash&m)*uintptr(t.bucketsize)))
    
    // Bucket search with randomized hash
    for ; b != nil; b = b.overflow(t) {
        for i := uintptr(0); i < bucketCnt; i++ {
            if b.tophash[i] != tophash(hash) {
                continue
            }
            // ...
        }
    }
    return nil
}
```

---

## 3. ReDoS (Regular Expression DoS)

### 3.1 Catastrophic Backtracking

**Vulnerable Regex**:
```regex
^(a+)+$
```

**Input**: `aaaaaaaaaaaaaaaaaaaaX`

**Backtracking Tree**:
```
Engine tries to match "^(a+)+$" against "aaaaaaaaaaaaaaaaaaaaX"

Attempt 1: (a+) matches "aaa..." then fails on X
Backtrack: Try (a+) as "aa..." and next (a+) as "a..."
Backtrack: Try (a+) as "a..." and next (a+) as "aa..."
...

Number of attempts: 2^n where n = number of 'a's
20 'a's → 1,048,576 attempts
30 'a's → 1,073,741,824 attempts (takes minutes)
```

**Visualization**:
```
Input: "aaaaaX"
Regex: ^(a+)+$

Matching steps (simplified):
┌─────────────────────────────────────────────────────────────┐
│ Step │ (a+) group 1 │ (a+) group 2 │ Remaining │ Result    │
├──────┼──────────────┼──────────────┼───────────┼───────────┤
│  1   │ "aaaaa"      │ ""           │ "X"       │ FAIL (X)  │
│  2   │ "aaaa"       │ "a"          │ "X"       │ FAIL (X)  │
│  3   │ "aaa"        │ "aa"         │ "X"       │ FAIL (X)  │
│  4   │ "aa"         │ "aaa"        │ "X"       │ FAIL (X)  │
│  5   │ "a"          │ "aaaa"       │ "X"       │ FAIL (X)  │
│  6   │ "aaaa"       │ ""           │ "aX"      │ FAIL (aX) │
│  7   │ "aaa"        │ "a"          │ "aX"      │ FAIL (aX) │
│ ...  │ ...          │ ...          │ ...       │ ...       │
│ 2^n  │ ...          │ ...          │ ...       │ FAIL      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Vulnerable Code (Node.js Email Validator)

```javascript
// VULNERABLE - email validation
function validateEmail(email) {
    // Evil regex with nested quantifiers
    const regex = /^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$/;
    return regex.test(email);
}

// Attack payload
const malicious = "a".repeat(50) + "@example.com";
console.time("validate");
validateEmail(malicious);  // Hangs for seconds/minutes
console.timeEnd("validate");
```

**Real-World Example** (2016 Stack Overflow Outage):
```regex
Vulnerable Regex: \s+$  (trim whitespace)
Context: Parsing markdown with long whitespace strings

Input: "text" + " " * 20000 + "\n"
Result: O(n²) backtracking, 30+ second CPU spike per request
```

### 3.3 Mitigation Strategies

**A. Use Non-Backtracking Engines** (RE2):
```go
// Go uses RE2 engine (linear time guarantee)
package main

import (
    "fmt"
    "regexp"
    "time"
)

func main() {
    // This regex is safe in Go (RE2 engine)
    re := regexp.MustCompile(`^(a+)+$`)
    
    input := strings.Repeat("a", 30) + "X"
    
    start := time.Now()
    matched := re.MatchString(input)
    duration := time.Since(start)
    
    fmt.Printf("Matched: %v, Time: %v\n", matched, duration)
    // Output: Matched: false, Time: ~10µs (not exponential!)
}
```

**B. Timeout Enforcement** (Rust):
```rust
use regex::Regex;
use std::time::{Duration, Instant};
use std::thread;
use std::sync::mpsc;

fn regex_with_timeout(pattern: &str, input: &str, timeout: Duration) -> Option<bool> {
    let (tx, rx) = mpsc::channel();
    let pattern = pattern.to_string();
    let input = input.to_string();
    
    thread::spawn(move || {
        let re = Regex::new(&pattern).unwrap();
        let result = re.is_match(&input);
        let _ = tx.send(result);
    });
    
    match rx.recv_timeout(timeout) {
        Ok(result) => Some(result),
        Err(_) => None,  // Timeout
    }
}

fn main() {
    let evil_regex = r"^(a+)+$";
    let evil_input = "a".repeat(30) + "X";
    
    match regex_with_timeout(evil_regex, &evil_input, Duration::from_secs(1)) {
        Some(result) => println!("Matched: {}", result),
        None => println!("Regex timed out - potential ReDoS!"),
    }
}
```

**C. Static Analysis** (safe-regex npm package):
```javascript
const safeRegex = require('safe-regex');

const patterns = [
    /^(a+)+$/,           // UNSAFE
    /^(a+)$/,            // SAFE
    /^([a-z]+)*$/,       // UNSAFE
    /^[a-z]+$/,          // SAFE
];

patterns.forEach(pattern => {
    console.log(`${pattern}: ${safeRegex(pattern) ? 'SAFE' : 'UNSAFE'}`);
});

// Output:
// /^(a+)+$/: UNSAFE
// /^(a+)$/: SAFE
// /^([a-z]+)*$/: UNSAFE
// /^[a-z]+$/: SAFE
```

---

## 4. GraphQL Query Depth & Complexity Attacks

### 4.1 Query Bomb Example

**GraphQL Schema**:
```graphql
type User {
  id: ID!
  name: String!
  friends: [User!]!
}

type Query {
  user(id: ID!): User
}
```

**Normal Query**:
```graphql
query {
  user(id: "1") {
    name
    friends {
      name
    }
  }
}
# Returns: 1 user + N friends (2 DB queries)
```

**Attack Query** (Depth Bomb):
```graphql
query {
  user(id: "1") {
    friends {
      friends {
        friends {
          friends {
            friends {
              friends {
                friends {
                  friends {
                    friends {
                      friends {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

# Depth: 10 levels
# If each user has 100 friends:
# Total nodes: 100^10 = 100 trillion users fetched!
# DB queries: 100^9 (if not batched)
```

**Attack Query** (Width Bomb):
```graphql
query {
  user1: user(id: "1") { name friends { name } }
  user2: user(id: "2") { name friends { name } }
  user3: user(id: "3") { name friends { name } }
  # ... repeat 1000 times
  user1000: user(id: "1000") { name friends { name } }
}

# 1000 aliases × N friends each = massive load
```

### 4.2 Resolver N+1 Problem

**Naive Implementation** (Node.js):
```javascript
// VULNERABLE - N+1 queries
const resolvers = {
  Query: {
    users: () => db.users.findAll(),  // 1 query
  },
  User: {
    posts: (user) => db.posts.findByUserId(user.id),  // N queries
  },
};

// Attack query
const query = `
  query {
    users {  # Fetches 1000 users (1 query)
      name
      posts {  # Fetches posts for EACH user (1000 queries)
        title
      }
    }
  }
`;

// Total: 1 + 1000 = 1001 database queries for single GraphQL request!
```

**Database Trace**:
```sql
-- Query 1
SELECT * FROM users;

-- Query 2
SELECT * FROM posts WHERE user_id = 1;

-- Query 3
SELECT * FROM posts WHERE user_id = 2;

-- ...

-- Query 1001
SELECT * FROM posts WHERE user_id = 1000;
```

### 4.3 Mitigation: Query Complexity Analysis

**GraphQL Depth Limiting** (Apollo Server):
```javascript
const { ApolloServer } = require('apollo-server');
const depthLimit = require('graphql-depth-limit');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    depthLimit(5),  // Max depth: 5 levels
  ],
});

// Attack query (depth 10) → Rejected with error:
// "Query exceeds maximum depth of 5"
```

**Query Cost Analysis**:
```javascript
const { createComplexityLimitRule } = require('graphql-validation-complexity');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    createComplexityLimitRule(1000, {
      onCost: (cost) => console.log('Query cost:', cost),
      createError: (cost, maxCost) => {
        return new Error(`Query cost ${cost} exceeds max ${maxCost}`);
      },
      formatErrorMessage: (cost) => `Query too complex: ${cost}`,
      
      // Assign costs to fields
      scalarCost: 1,
      objectCost: 5,
      listFactor: 10,  // Lists multiply cost
    }),
  ],
});

// Example cost calculation:
// query {
//   users {         # 100 users × listFactor(10) = 1000
//     posts {       # 100 × 20 posts × listFactor(10) = 20000
//       comments {  # 100 × 20 × 50 comments × listFactor(10) = 1000000
//         ...
// }
// Total cost: 1021000 → REJECTED
```

**DataLoader (Batching)** - Solves N+1:
```javascript
const DataLoader = require('dataloader');

// Batch function: receives array of keys, returns array of values
const batchPosts = async (userIds) => {
  const posts = await db.posts.findAll({
    where: { userId: { $in: userIds } }
  });
  
  // Group by userId
  const postsByUserId = {};
  userIds.forEach(id => postsByUserId[id] = []);
  posts.forEach(post => postsByUserId[post.userId].push(post));
  
  return userIds.map(id => postsByUserId[id] || []);
};

const postLoader = new DataLoader(batchPosts);

const resolvers = {
  User: {
    posts: (user) => postLoader.load(user.id),  // Batches requests
  },
};

// Same attack query now:
// SELECT * FROM users;                    -- 1 query
// SELECT * FROM posts WHERE user_id IN (1,2,3,...,1000);  -- 1 batched query
// Total: 2 queries instead of 1001!
```

---

## 5. JSON/XML Deep Nesting & Expansion

### 5.1 JSON Deep Nesting Attack

**Attack Payload**:
```json
{
  "a": {
    "b": {
      "c": {
        "d": {
          "e": {
            ...  // 10,000 levels deep
          }
        }
      }
    }
  }
}
```

**Vulnerable Parser** (Recursive Descent):
```python
# VULNERABLE - stack overflow with deep nesting
import json

def parse_json(text):
    return json.loads(text)  # Uses recursive parser

# Attack
deep_json = '{"a":' * 10000 + '1' + '}' * 10000
try:
    parse_json(deep_json)
except RecursionError as e:
    print(f"Stack overflow: {e}")

# Python default recursion limit: 1000
# 10000 levels → crashes interpreter
```

**Memory Consumption**:
```
Stack frame size: ~400 bytes (varies by platform)
10,000 levels × 400 bytes = 4 MB stack
If multiple requests: 4 MB × 1000 concurrent = 4 GB memory
```

**Mitigation** (Depth Limiting):
```python
import json

class DepthLimitedDecoder(json.JSONDecoder):
    def __init__(self, max_depth=20, *args, **kwargs):
        self.max_depth = max_depth
        super().__init__(*args, **kwargs)
        self.parse_object = self._limited_parse_object
        
    def _limited_parse_object(self, *args, **kwargs):
        depth = 0
        def parse_with_depth(s, idx):
            nonlocal depth
            depth += 1
            if depth > self.max_depth:
                raise ValueError(f"JSON nesting exceeds {self.max_depth}")
            # Call original parse logic
            # ...
            depth -= 1
        return parse_with_depth(*args, **kwargs)

# Usage
try:
    json.loads(deep_json, cls=DepthLimitedDecoder, max_depth=50)
except ValueError as e:
    print(f"Rejected: {e}")
```

**Golang Defense** (Iterative Parser):
```go
package main

import (
    "encoding/json"
    "fmt"
)

type LimitedReader struct {
    r         io.Reader
    maxDepth  int
    depth     int
}

func (lr *LimitedReader) Read(p []byte) (n int, err error) {
    n, err = lr.r.Read(p)
    for i := 0; i < n; i++ {
        if p[i] == '{' || p[i] == '[' {
            lr.depth++
            if lr.depth > lr.maxDepth {
                return i, fmt.Errorf("JSON depth exceeds %d", lr.maxDepth)
            }
        } else if p[i] == '}' || p[i] == ']' {
            lr.depth--
        }
    }
    return n, err
}

func main() {
    input := strings.NewReader(`{"a":{"b":{"c":"value"}}}`)
    lr := &LimitedReader{r: input, maxDepth: 10}
    
    var data interface{}
    decoder := json.NewDecoder(lr)
    if err := decoder.Decode(&data); err != nil {
        fmt.Println("Error:", err)
    }
}
```

### 5.2 XML Billion Laughs Attack

**Attack Payload**:
```xml
<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
  <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
  <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
  <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
  <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
  <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
]>
<lolz>&lol9;</lolz>
```

**Expansion Calculation**:
```
lol   = "lol" (3 bytes)
lol1  = lol × 10 = 30 bytes
lol2  = lol1 × 10 = 300 bytes
lol3  = lol2 × 10 = 3 KB
lol4  = lol3 × 10 = 30 KB
lol5  = lol4 × 10 = 300 KB
lol6  = lol5 × 10 = 3 MB
lol7  = lol6 × 10 = 30 MB
lol8  = lol7 × 10 = 300 MB
lol9  = lol8 × 10 = 3 GB

Input size: ~1 KB
Expanded size: 3 GB (3,000,000× amplification)
```

**Mitigation** (Disable External Entities):
```python
import defusedxml.ElementTree as ET

# Safe XML parsing
try:
    tree = ET.parse('input.xml')  # Entities disabled by default
except ET.ParseError as e:
    print(f"XML parsing error: {e}")

# Python's xml.etree.ElementTree (UNSAFE):
# import xml.etree.ElementTree as ET  # DO NOT USE
```

**Rust (quick-xml with limits)**:
```rust
use quick_xml::Reader;
use quick_xml::events::Event;

fn parse_xml_safe(xml: &str) -> Result<(), String> {
    let mut reader = Reader::from_str(xml);
    reader.trim_text(true);
    reader.expand_empty_elements(false);
    
    let mut buf = Vec::new();
    let mut depth = 0;
    const MAX_DEPTH: usize = 100;
    
    loop {
        match reader.read_event(&mut buf) {
            Ok(Event::Start(_)) => {
                depth += 1;
                if depth > MAX_DEPTH {
                    return Err(format!("XML depth exceeds {}", MAX_DEPTH));
                }
            }
            Ok(Event::End(_)) => depth -= 1,
            Ok(Event::Eof) => break,
            Err(e) => return Err(format!("XML error: {}", e)),
            _ => (),
        }
        buf.clear();
    }
    Ok(())
}
```

---

## 6. Database Query Complexity Attacks

### 6.1 Cartesian Product Explosion

**Vulnerable ORM Query** (Django):
```python
# VULNERABLE - implicit join without limit
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField()

# Attack query (via API or GraphQL)
users = User.objects.prefetch_related('post_set__comment_set').all()

# Generated SQL:
# SELECT * FROM users;
# SELECT * FROM posts WHERE user_id IN (...);
# SELECT * FROM comments WHERE post_id IN (...);

# If 1000 users, 100 posts/user, 50 comments/post:
# Total rows fetched: 1000 + 100K + 5M = ~5M rows
# Memory: 5M × 1KB/row = 5 GB
```

**Attacker-Controlled Filter**:
```python
# API endpoint: /api/search?filters=...
def search(request):
    filters = json.loads(request.GET['filters'])  # User input!
    
    # VULNERABLE - no limit on join complexity
    query = User.objects.all()
    for field, value in filters.items():
        query = query.filter(**{field: value})  # Arbitrary joins
    
    return JsonResponse(list(query.values()))

# Attack payload:
# /api/search?filters={"post__comment__user__post__comment__text__contains":"a"}
# Joins: users → posts → comments → users → posts → comments
# 6-way self-join with no LIMIT!
```

### 6.2 Query Plan Analyzer (PostgreSQL)

```sql
-- Check query cost
EXPLAIN ANALYZE
SELECT u.name, p.title, c.text
FROM users u
JOIN posts p ON p.user_id = u.id
JOIN comments c ON c.post_id = p.id
WHERE c.text LIKE '%keyword%';

-- Output:
-- Nested Loop  (cost=0.00..1000000.00 rows=5000000 ...)
--   -> Seq Scan on comments c  (cost=0.00..500000.00 rows=5000000 ...)
--         Filter: (text ~~ '%keyword%'::text)
--   -> Index Scan using posts_pkey on posts p  (cost=0.43..0.50 rows=1 ...)
--   -> Index Scan using users_pkey on users u  (cost=0.42..0.48 rows=1 ...)
-- Planning Time: 0.234 ms
-- Execution Time: 45000.123 ms  ← 45 seconds!
```

**Mitigation** (Query Timeout):
```sql
-- PostgreSQL
SET statement_timeout = '5s';  -- Kill queries after 5 seconds

-- MySQL
SET SESSION max_execution_time = 5000;  -- Milliseconds

-- Application-level (Django)
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SET statement_timeout = '5s'")
    cursor.execute("SELECT ...")
```

**Query Complexity Estimator** (Golang):
```go
// Monitor query execution time
package main

import (
    "context"
    "database/sql"
    "time"
)

func QueryWithTimeout(db *sql.DB, query string, timeout time.Duration) error {
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()
    
    start := time.Now()
    rows, err := db.QueryContext(ctx, query)
    duration := time.Since(start)
    
    if err == context.DeadlineExceeded {
        return fmt.Errorf("query timeout after %v", duration)
    }
    
    // Log slow queries
    if duration > 1*time.Second {
        log.Printf("SLOW QUERY (%v): %s", duration, query)
    }
    
    defer rows.Close()
    return err
}
```

---

## 7. Algorithmic Complexity in Sorting/Searching

### 7.1 Quicksort Worst-Case Attack

**Vulnerable Code** (C):
```c
// VULNERABLE - deterministic pivot selection
void quicksort(int arr[], int low, int high) {
    if (low < high) {
        // Pivot is always first element (PREDICTABLE)
        int pivot = arr[low];
        int i = low + 1;
        
        for (int j = low + 1; j <= high; j++) {
            if (arr[j] < pivot) {
                swap(&arr[i], &arr[j]);
                i++;
            }
        }
        swap(&arr[low], &arr[i-1]);
        
        quicksort(arr, low, i-2);
        quicksort(arr, i, high);  // Recursion
    }
}

// Attack: Already sorted array
int evil_input[] = {1, 2, 3, 4, ..., 10000};
quicksort(evil_input, 0, 9999);

// Worst-case: O(n²) = 100M comparisons
// Stack depth: 10000 (potential stack overflow)
```

**Mitigation** (Randomized Pivot):
```c
#include <stdlib.h>
#include <time.h>

void quicksort_random(int arr[], int low, int high) {
    if (low < high) {
        // Random pivot selection
        int pivot_idx = low + rand() % (high - low + 1);
        swap(&arr[low], &arr[pivot_idx]);
        
        int pivot = arr[low];
        int i = low + 1;
        
        for (int j = low + 1; j <= high; j++) {
            if (arr[j] < pivot) {
                swap(&arr[i], &arr[j]);
                i++;
            }
        }
        swap(&arr[low], &arr[i-1]);
        
        quicksort_random(arr, low, i-2);
        quicksort_random(arr, i, high);
    }
}

int main() {
    srand(time(NULL));  // Seed RNG
    int arr[] = {1, 2, 3, ..., 10000};
    quicksort_random(arr, 0, 9999);
    // Expected: O(n log n) even on sorted input
}
```

**Rust (Introsort)** - Standard Library Defense:
```rust
// Rust's Vec::sort() uses introsort (hybrid algorithm)
// - Quicksort with randomized pivot
// - Switches to heapsort if recursion depth > 2*log(n)
// - Insertion sort for small subarrays

fn main() {
    let mut v = vec![1, 2, 3, 4, 5, ..., 10000];
    v.sort();  // O(n log n) guaranteed, even on adversarial input
}

// Implementation (simplified from std::slice):
fn sort<T: Ord>(v: &mut [T]) {
    let max_depth = 2 * v.len().ilog2();
    introsort(v, 0, max_depth);
}

fn introsort<T: Ord>(v: &mut [T], depth: usize, max_depth: u32) {
    if depth > max_depth {
        heapsort(v);  // Fallback to O(n log n) heapsort
    } else if v.len() <= 20 {
        insertion_sort(v);  // Fast for small arrays
    } else {
        let pivot = choose_pivot(v);  // Median-of-three + random
        let mid = partition(v, pivot);
        introsort(&mut v[..mid], depth + 1, max_depth);
        introsort(&mut v[mid+1..], depth + 1, max_depth);
    }
}
```

### 7.2 String Comparison Timing Attack

**Vulnerable Code** (Early Return):
```python
# VULNERABLE - timing leak
def compare_secret(user_input, secret):
    if len(user_input) != len(secret):
        return False
    
    for i in range(len(secret)):
        if user_input[i] != secret[i]:
            return False  # Early return leaks position
    
    return True

# Attacker measures response time:
# "aaaa" → 1µs   (fails at position 0)
# "paaa" → 2µs   (fails at position 1, 'a' != 's')
# "psaa" → 3µs   (fails at position 2, 'a' != 's')
# ...
# "pass" → 4µs   (all match!)
# Can brute-force 8-char password in ~2048 attempts instead of 62^8
```

**Mitigation** (Constant-Time Comparison):
```python
import hmac

def compare_secret_safe(user_input, secret):
    # hmac.compare_digest: constant-time comparison
    return hmac.compare_digest(user_input, secret)

# Implementation (simplified):
def constant_time_compare(a, b):
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)  # No early return
    
    return result == 0
```

---

## 8. Detection & Monitoring

### 8.1 CPU Time per Request (eBPF)

```c
// cpu_profile.bpf.c - Track CPU time per syscall
#include <linux/bpf.h>
#include <linux/ptrace.h>

BPF_HASH(start, u32, u64);      // PID → start timestamp
BPF_HISTOGRAM(cpu_time_hist);   // CPU time histogram

int trace_enter(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid();
    u64 ts = bpf_ktime_get_ns();
    start.update(&pid, &ts);
    return 0;
}

int trace_return(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid();
    u64 *tsp = start.lookup(&pid);
    
    if (tsp != 0) {
        u64 delta = bpf_ktime_get_ns() - *tsp;
        u64 delta_ms = delta / 1000000;  // Convert to ms
        cpu_time_hist.increment(bpf_log2l(delta_ms));
        start.delete(&pid);
    }
    return 0;
}
```

**Usage**:
```bash
# Compile and attach
bpftrace -e 'kprobe:__x64_sys_read { @start[tid] = nsecs; }
             kretprobe:__x64_sys_read /@start[tid]/ { 
                 @ns[comm] = hist(nsecs - @start[tid]); 
                 delete(@start[tid]); 
             }'

# Output:
# @ns[nginx]:
# [1K, 2K)       100 |@@@@                |
# [2K, 4K)       500 |@@@@@@@@@@@@@@@@@@@@|
# [4K, 8K)       200 |@@@@@@@@            |
# [1M, 2M)         5 |                    | ← Outliers (DoS candidates)
```

### 8.2 Memory Allocation Tracking

```go
// memory_profiler.go
package main

import (
    "net/http"
    "runtime"
    "time"
)

type MemoryMiddleware struct {
    handler http.Handler
    maxAlloc uint64  // Max allowed allocation per request
}

func (m *MemoryMiddleware) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    var before, after runtime.MemStats
    runtime.ReadMemStats(&before)
    
    start := time.Now()
    m.handler.ServeHTTP(w, r)
    duration := time.Since(start)
    
    runtime.ReadMemStats(&after)
    allocated := after.TotalAlloc - before.TotalAlloc
    
    if allocated > m.maxAlloc {
        log.Printf("WARNING: Request allocated %d bytes (max: %d) in %v",
            allocated, m.maxAlloc, duration)
        // Trigger alert, rate limit this IP, etc.
    }
}

func main() {
    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Your application logic
    })
    
    wrapped := &MemoryMiddleware{
        handler: handler,
        maxAlloc: 10 * 1024 * 1024,  // 10 MB max per request
    }
    
    http.ListenAndServe(":8080", wrapped)
}
```

### 8.3 Query Plan Monitoring (PostgreSQL)

```sql
-- Enable auto_explain extension
ALTER SYSTEM SET shared_preload_libraries = 'auto_explain';
ALTER SYSTEM SET auto_explain.log_min_duration = 1000;  -- Log queries > 1s
ALTER SYSTEM SET auto_explain.log_analyze = on;
SELECT pg_reload_conf();

-- Queries exceeding 1s will be logged with EXPLAIN ANALYZE output
-- Check logs:
tail -f /var/log/postgresql/postgresql-14-main.log

-- Sample output:
-- 2024-02-05 12:34:56 UTC LOG:  duration: 5432.123 ms  plan:
-- Nested Loop  (cost=0.00..1000000.00 rows=5000000 ...)
--   Filter: (text ~~ '%keyword%'::text)
```

**Application-Level Detection** (Python):
```python
from django.db import connection
from django.core.signals import request_finished
import time

class QueryComplexityDetector:
    def __init__(self):
        self.query_start = {}
    
    def on_query_start(self, sender, **kwargs):
        self.query_start[id(sender)] = time.time()
    
    def on_query_end(self, sender, **kwargs):
        start = self.query_start.get(id(sender))
        if start:
            duration = time.time() - start
            if duration > 1.0:  # Slow query threshold
                queries = connection.queries
                slow_query = queries[-1]['sql']
                print(f"SLOW QUERY ({duration:.2f}s): {slow_query}")
                # Send to monitoring system (Prometheus, Datadog, etc.)

detector = QueryComplexityDetector()
request_finished.connect(detector.on_query_end)
```

---

## 9. Defense-in-Depth Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           Application-Level DDoS Defense Stack                   │
└─────────────────────────────────────────────────────────────────┘

Request → [1] Rate Limiting (IP/User)
          ├─ Token bucket: 10 req/s
          └─ Burst: 20 req
             ↓
          [2] Request Size Limits
          ├─ Body: 1 MB max
          ├─ Headers: 8 KB max
          └─ Query params: 100 max
             ↓
          [3] Timeout Enforcement
          ├─ Read timeout: 5s
          ├─ Write timeout: 10s
          └─ Request timeout: 30s
             ↓
          [4] Input Validation
          ├─ JSON depth: 20 levels
          ├─ Regex timeout: 100ms
          └─ GraphQL depth: 5
             ↓
          [5] Resource Quotas (cgroups)
          ├─ CPU: 200ms per request
          ├─ Memory: 100 MB per request
          └─ File descriptors: 1000
             ↓
          [6] Circuit Breaker
          ├─ Failure threshold: 50%
          ├─ Reset timeout: 60s
          └─ Half-open test: 1 req
             ↓
          [7] Database Query Governor
          ├─ Statement timeout: 5s
          ├─ Max joins: 3
          └─ Result set limit: 10K rows
             ↓
          [8] Application Logic
          └─ Use efficient algorithms (O(n log n))
```

### 9.1 cgroups Resource Limiting (Linux)

```bash
# Create cgroup for web app
cgcreate -g cpu,memory:webapp

# Set CPU limit: 50% of one core
cgset -r cpu.cfs_quota_us=50000 webapp
cgset -r cpu.cfs_period_us=100000 webapp

# Set memory limit: 512 MB
cgset -r memory.limit_in_bytes=536870912 webapp

# Run application in cgroup
cgexec -g cpu,memory:webapp /usr/bin/python app.py

# Monitor resource usage
cgget -r cpu.stat webapp
cgget -r memory.usage_in_bytes webapp
```

**Systemd Service** (cgroup v2):
```ini
# /etc/systemd/system/webapp.service
[Unit]
Description=Web Application

[Service]
ExecStart=/usr/bin/python /opt/webapp/app.py
CPUQuota=50%
MemoryMax=512M
TasksMax=1000
IOWeight=100

[Install]
WantedBy=multi-user.target
```

### 9.2 Circuit Breaker Pattern (Golang)

```go
package main

import (
    "errors"
    "sync"
    "time"
)

type CircuitBreaker struct {
    maxFailures  int
    resetTimeout time.Duration
    
    mu            sync.Mutex
    failures      int
    lastFailTime  time.Time
    state         string  // "closed", "open", "half-open"
}

func NewCircuitBreaker(maxFailures int, resetTimeout time.Duration) *CircuitBreaker {
    return &CircuitBreaker{
        maxFailures:  maxFailures,
        resetTimeout: resetTimeout,
        state:        "closed",
    }
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    cb.mu.Lock()
    
    // Check if we should transition from open to half-open
    if cb.state == "open" {
        if time.Since(cb.lastFailTime) > cb.resetTimeout {
            cb.state = "half-open"
            cb.failures = 0
        } else {
            cb.mu.Unlock()
            return errors.New("circuit breaker is open")
        }
    }
    
    cb.mu.Unlock()
    
    // Execute function
    err := fn()
    
    cb.mu.Lock()
    defer cb.mu.Unlock()
    
    if err != nil {
        cb.failures++
        cb.lastFailTime = time.Now()
        
        if cb.failures >= cb.maxFailures {
            cb.state = "open"
        }
        return err
    }
    
    // Success - reset circuit breaker
    if cb.state == "half-open" {
        cb.state = "closed"
    }
    cb.failures = 0
    return nil
}

// Usage
func main() {
    cb := NewCircuitBreaker(5, 60*time.Second)
    
    for i := 0; i < 100; i++ {
        err := cb.Call(func() error {
            // Call potentially failing service
            return slowDatabaseQuery()
        })
        
        if err != nil {
            log.Printf("Request failed: %v", err)
        }
    }
}
```

---

## 10. Testing & Fuzzing

### 10.1 Algorithmic Complexity Fuzzer

```python
# complexity_fuzzer.py
import time
import json
import requests

def test_json_depth():
    """Test JSON parser depth limits"""
    for depth in [10, 50, 100, 500, 1000, 5000]:
        # Generate deeply nested JSON
        payload = '{"a":' * depth + '1' + '}' * depth
        
        start = time.time()
        try:
            response = requests.post(
                'http://localhost:8080/api/process',
                data=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            duration = time.time() - start
            print(f"Depth {depth}: {duration:.3f}s, Status: {response.status_code}")
        except requests.Timeout:
            print(f"Depth {depth}: TIMEOUT (>10s)")
        except Exception as e:
            print(f"Depth {depth}: ERROR - {e}")

def test_regex_complexity():
    """Test regex backtracking"""
    patterns = [
        r'^(a+)+$',
        r'^(a*)*$',
        r'^([a-z]+)*$',
        r'(a|a)*',
    ]
    
    for pattern in patterns:
        for length in [10, 20, 30, 40]:
            payload = {
                'regex': pattern,
                'input': 'a' * length + 'X'
            }
            
            start = time.time()
            try:
                response = requests.post(
                    'http://localhost:8080/api/validate',
                    json=payload,
                    timeout=5
                )
                duration = time.time() - start
                print(f"Pattern {pattern}, Length {length}: {duration:.3f}s")
            except requests.Timeout:
                print(f"Pattern {pattern}, Length {length}: TIMEOUT")

def test_hash_collision():
    """Generate colliding keys (Python 2.x example)"""
    # For modern systems, this requires knowing the hash seed
    # Use generic collision attack instead
    
    keys = [f"key_{i:05d}" for i in range(10000)]
    payload = {key: "value" for key in keys}
    
    start = time.time()
    response = requests.post(
        'http://localhost:8080/api/bulk',
        json=payload,
        timeout=30
    )
    duration = time.time() - start
    print(f"Hash collision test: {duration:.3f}s")

if __name__ == '__main__':
    test_json_depth()
    test_regex_complexity()
    test_hash_collision()
```

### 10.2 AFL Fuzzing (C/C++)

```bash
# Install AFL
git clone https://github.com/google/AFL
cd AFL
make
sudo make install

# Compile target with AFL instrumentation
afl-gcc -o json_parser json_parser.c

# Create seed inputs
mkdir in out
echo '{"test": "value"}' > in/seed1.json
echo '{"nested": {"data": 123}}' > in/seed2.json

# Fuzz
afl-fuzz -i in -o out ./json_parser @@

# AFL will discover crashing inputs in out/crashes/
# Analyze crashes:
cat out/crashes/id:000000*
```

**Target Program**:
```c
// json_parser.c - Intentionally vulnerable for demo
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void parse_json(const char *input, int depth) {
    if (depth > 100) {
        fprintf(stderr, "Max depth exceeded\n");
        exit(1);  // AFL detects this as crash
    }
    
    // Simplified parser (vulnerable to deep nesting)
    if (strchr(input, '{')) {
        parse_json(input + 1, depth + 1);
    }
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <input_file>\n", argv[0]);
        return 1;
    }
    
    FILE *f = fopen(argv[1], "r");
    if (!f) {
        perror("fopen");
        return 1;
    }
    
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    char *buffer = malloc(size + 1);
    fread(buffer, 1, size, f);
    buffer[size] = '\0';
    fclose(f);
    
    parse_json(buffer, 0);
    
    free(buffer);
    return 0;
}
```

---

## 11. Real-World Case Studies

### 11.1 Stack Overflow (2016) - Regex DoS

**Incident**:
- Regex in markdown parser: `\s+$`
- User posted comment with 20,000 spaces + newline
- Regex engine entered catastrophic backtracking
- CPU spike to 100% for 30+ seconds per request
- Site outage for 34 minutes

**Root Cause**:
```regex
\s+$  # Match one or more whitespace at end of line

With input: " " * 20000 + "\n"
Engine tries:
1. Match all 20000 spaces with \s+, $ fails
2. Backtrack: match 19999 spaces, $ fails
3. Backtrack: match 19998 spaces, $ fails
...
20000 attempts → O(n) complexity, but with 30s timeout per attempt
```

**Fix**:
```regex
\s+$  →  \s*$  # Use * instead of + (greedy match all, then $)
# Or use possessive quantifier: \s++$ (no backtracking)
```

### 11.2 Cloudflare (2019) - Regex CPU Exhaustion

**Incident**:
- WAF regex rule: `.*.*=.*`
- Attacker sent HTTP request with specific URI pattern
- Single request consumed 20s CPU time
- Across global network: 100% CPU on all edge servers
- Service degradation for 27 minutes

**Vulnerable Regex**:
```regex
.*.*=.*

Explained:
.* - matches anything (greedy)
.* - matches anything again (redundant!)
=  - literal equals
.* - matches anything

With input: "x" * 100 (no '=' character)
Engine tries all combinations of splits between first and second .*
Complexity: O(n²) or worse
```

**Lessons**:
1. Static analysis of all regex patterns before deployment
2. Regex timeout enforcement (100ms hard limit)
3. Use RE2 engine (linear time guarantee)

### 11.3 NPM left-pad (2016) - Algorithmic Impact

**Not a DoS, but illustrates dependency on algorithms**:
- Popular package `left-pad` removed from npm
- 1000s of projects broke
- Highlights: Critical path algorithms must be vetted

**Common Algorithmic Vulnerabilities in Dependencies**:
- Regex in validators
- Sorting in data processors
- JSON/XML parsing
- Hash table implementations

---

## 12. Threat Model Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ Asset: Application Availability (CPU, Memory, Database)         │
├─────────────────────────────────────────────────────────────────┤
│ Threat Actor: Malicious user with single IP, low bandwidth      │
├─────────────────────────────────────────────────────────────────┤
│ Attack Vector: Algorithmic complexity exploitation              │
├─────────────────────────────────────────────────────────────────┤
│ Impact: Service unavailable for legitimate users                │
├─────────────────────────────────────────────────────────────────┤
│ Mitigations:                                                     │
│ 1. Input validation (depth, length, complexity)                 │
│ 2. Resource quotas (CPU, memory, time)                          │
│ 3. Randomized algorithms (hash functions, pivots)               │
│ 4. Monitoring & alerting (slow queries, high CPU)               │
│ 5. Circuit breakers (fail fast)                                 │
│ 6. Static analysis (regex, query plans)                         │
│ 7. Defensive data structures (RE2, introsort)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Next 3 Steps

1. **Audit Application for Algorithmic Vulnerabilities**:
   ```bash
   # Scan codebase for dangerous patterns
   grep -r "json.loads" .  # Check for depth limits
   grep -r "re.compile" .  # Check for ReDoS
   grep -r "prefetch_related" .  # Check for N+1 queries
   
   # Run static analysis
   bandit -r . -f json -o security_report.json
   semgrep --config=p/security-audit .
   ```

2. **Implement Request Instrumentation**:
   ```go
   // Add CPU time tracking to all endpoints
   middleware := func(next http.Handler) http.Handler {
       return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
           start := time.Now()
           next.ServeHTTP(w, r)
           duration := time.Since(start)
           
           if duration > 1*time.Second {
               log.Printf("SLOW REQUEST: %s %s (%v)", 
                   r.Method, r.URL.Path, duration)
           }
       })
   }
   ```

3. **Deploy Chaos Engineering Tests**:
   ```python
   # Continuously test with malformed inputs
   def chaos_test():
       while True:
           payload = generate_evil_json()  # Deep nesting
           response = requests.post('/api/endpoint', json=payload)
           assert response.status_code != 500  # No crashes
           assert response.elapsed.total_seconds() < 1.0  # Fast response
           time.sleep(60)
   ```

**Verification Commands**:
```bash
# Monitor CPU per process
pidstat -p $(pgrep -f webapp) 1

# Track memory allocations
valgrind --tool=massif ./webapp
ms_print massif.out.*

# Database query monitoring
SELECT query, calls, mean_exec_time 
FROM pg_stat_statements 
WHERE mean_exec_time > 1000  -- >1s average
ORDER BY mean_exec_time DESC;
```

Which specific attack vector or mitigation strategy would you like to explore with code implementations and benchmarks?