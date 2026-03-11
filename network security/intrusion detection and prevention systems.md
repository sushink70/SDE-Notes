# Intrusion Detection and Prevention Systems (IDPS) - Comprehensive Deep Dive

## Executive Summary (4-8 lines)

An IDPS is a security control that monitors network traffic, system calls, file integrity, and behavioral patterns to detect and optionally block malicious activity. It operates at multiple layers: packet/flow analysis (NIDS), host-level monitoring (HIDS), and application-aware inspection, using signature matching, anomaly detection, stateful protocol analysis, and ML-based classification. Core challenges include false positive/negative rates, evasion resistance, performance at line-rate (10/40/100G), stateful tracking under high connection volume, and integration into zero-trust architectures. Modern IDPS must handle encrypted traffic (TLS 1.3), container/pod-level isolation, cloud-native ephemeral infrastructure, and eBPF/XDP-based kernel bypass for performance. This guide covers detection theory, architecture patterns, implementation deep-dives (packet capture → rule engine → action), deployment models, evasion techniques, and production integration with K8s/service mesh/cloud security.

---

## Table of Contents

1. **Core Concepts & Taxonomy**
2. **Detection Methodologies**
3. **Architecture Patterns & System Design**
4. **Packet Capture & Processing Pipeline**
5. **Pattern Matching & Rule Engines**
6. **Stateful Protocol Analysis**
7. **Anomaly Detection & ML Approaches**
8. **Host-Based IDS (HIDS) Deep Dive**
9. **Network-Based IDS (NIDS) Deep Dive**
10. **Evasion Techniques & Countermeasures**
11. **Performance Optimization**
12. **Cloud-Native & Container IDPS**
13. **Threat Model & Security Analysis**
14. **Production Deployment**
15. **Implementation Examples**
16. **Testing, Fuzzing, Benchmarking**
17. **Rollout/Rollback Strategy**
18. **Next 3 Steps**

---

## 1. Core Concepts & Taxonomy

### IDPS Classification

```
┌─────────────────────────────────────────────────────────────┐
│                    IDPS TAXONOMY                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  BY SCOPE:                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐        │
│  │    NIDS     │  │    HIDS     │  │   Hybrid     │        │
│  │ Network-based│  │  Host-based │  │  NBA (flow)  │        │
│  └─────────────┘  └─────────────┘  └──────────────┘        │
│                                                              │
│  BY ACTION:                                                  │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │     IDS     │  │     IPS     │                          │
│  │  (passive)  │  │  (active)   │                          │
│  └─────────────┘  └─────────────┘                          │
│                                                              │
│  BY METHOD:                                                  │
│  ┌──────────────┐ ┌───────────────┐ ┌─────────────┐       │
│  │  Signature   │ │   Anomaly     │ │  Stateful   │       │
│  │  (pattern)   │ │   (baseline)  │ │  Protocol   │       │
│  └──────────────┘ └───────────────┘ └─────────────┘       │
│                                                              │
│  BY DEPLOYMENT:                                              │
│  ┌──────────────┐ ┌───────────────┐ ┌─────────────┐       │
│  │   Inline     │ │   Passive TAP │ │   Agent     │       │
│  │  (L2 bridge) │ │   (mirror)    │ │   (kernel)  │       │
│  └──────────────┘ └───────────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Key Definitions

- **IDS (Intrusion Detection System)**: Monitors and alerts; passive observation
- **IPS (Intrusion Prevention System)**: Monitors and blocks; active inline enforcement
- **False Positive (FP)**: Benign traffic flagged as malicious (alert fatigue)
- **False Negative (FN)**: Malicious traffic missed (security gap)
- **True Positive Rate (TPR)**: Sensitivity = TP / (TP + FN)
- **False Positive Rate (FPR)**: FP / (FP + TN)
- **Signature**: Static pattern/regex/hash matching known attacks
- **Anomaly**: Statistical deviation from learned baseline
- **Stateful**: Track connection state, reassemble streams
- **Evasion**: Attacker techniques to bypass detection

---

## 2. Detection Methodologies

### 2.1 Signature-Based Detection

**Mechanism**: Match known attack patterns (strings, regex, byte sequences, protocol anomalies)

**Advantages**:
- Low false positive rate for known attacks
- Deterministic, explainable alerts
- Fast matching with optimized algorithms (Aho-Corasick, hyperscan)

**Disadvantages**:
- Zero-day attacks bypass completely
- Requires continuous signature updates
- Vulnerable to polymorphic/metamorphic malware

**Implementation Approach**:
```
Rule Format (Snort-style):
alert tcp $EXTERNAL_NET any -> $HOME_NET 445 (
  msg:"SMB EternalBlue exploit attempt";
  content:"|ff|SMB|75|"; offset:4; depth:5;
  content:"|00 00 00 00 00 00 01 00 00 00 00 00|";
  pcre:"/^\x00\x00\x00.\x{ff}SMB/smi";
  classtype:attempted-admin;
  sid:100001;
  rev:1;
)
```

### 2.2 Anomaly-Based Detection

**Mechanism**: Establish behavioral baseline, flag statistical outliers

**Approaches**:
1. **Statistical**: Mean/variance of packet size, connection rate, protocol distribution
2. **Machine Learning**: Supervised (labeled data), unsupervised (clustering), semi-supervised
3. **Protocol Behavior**: Deviation from RFC-compliant protocol state machines

**Advantages**:
- Detects zero-day and novel attacks
- Adapts to evolving threats

**Disadvantages**:
- High false positive rate (benign anomalies)
- Training phase required, concept drift
- Computationally expensive

**ML Pipeline**:
```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Packet  │──>│ Feature  │──>│  Model   │──>│ Anomaly  │
│ Capture  │   │Extraction│   │ Inference│   │  Score   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                    │
Features:                                           ▼
- Flow duration                              ┌─────────────┐
- Bytes sent/received                        │  Threshold  │
- Packet rate                                │  Decision   │
- Port distribution                          └─────────────┘
- Protocol ratios
- Inter-arrival times
```

### 2.3 Stateful Protocol Analysis

**Mechanism**: RFC-aware protocol state machines detect violations

**Example - TCP State Tracking**:
```
CLOSED -> SYN_SENT -> ESTABLISHED -> FIN_WAIT -> CLOSED

Violations:
- SYN flood (many SYN_SENT)
- Out-of-window sequence numbers
- Invalid flag combinations (SYN+FIN, FIN without ESTABLISHED)
- Protocol downgrades (TLS version rollback)
```

**Advantages**:
- High accuracy for protocol-specific attacks
- Low false positive rate

**Disadvantages**:
- CPU/memory intensive state tracking
- Must decode all protocols (HTTP, DNS, TLS, SMB, etc.)

---

## 3. Architecture Patterns & System Design

### 3.1 High-Level IDPS Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        IDPS ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐   │
│  │   CAPTURE    │──────>│   DECODE     │──────>│   DETECT     │   │
│  │              │       │              │       │              │   │
│  │ • libpcap    │       │ • L2-L7      │       │ • Signatures │   │
│  │ • AF_PACKET  │       │ • Defrag     │       │ • Anomaly    │   │
│  │ • PF_RING    │       │ • Reassembly │       │ • Protocol   │   │
│  │ • DPDK       │       │ • Normalize  │       │              │   │
│  │ • eBPF/XDP   │       │              │       │              │   │
│  └──────────────┘       └──────────────┘       └──────────────┘   │
│         │                       │                       │           │
│         │                       │                       ▼           │
│         │                       │              ┌──────────────┐   │
│         │                       │              │    ACTION    │   │
│         │                       │              │              │   │
│         │                       │              │ • Alert      │   │
│         │                       │              │ • Drop/Block │   │
│         │                       │              │ • Log        │   │
│         │                       │              │ • Quarantine │   │
│         │                       │              └──────────────┘   │
│         │                       │                                  │
│         ▼                       ▼                                  │
│  ┌─────────────────────────────────────┐                          │
│  │         STATE MANAGEMENT            │                          │
│  │                                     │                          │
│  │  • Connection tracking (5-tuple)   │                          │
│  │  • Flow reassembly buffers         │                          │
│  │  • Protocol state machines         │                          │
│  │  • Session persistence             │                          │
│  └─────────────────────────────────────┘                          │
│                                                                      │
│  ┌─────────────────────────────────────┐                          │
│  │      RULE/SIGNATURE ENGINE          │                          │
│  │                                     │                          │
│  │  • Pattern matcher (Hyperscan)     │                          │
│  │  • Rule parser & optimizer         │                          │
│  │  • Multi-pattern DFA/NFA           │                          │
│  └─────────────────────────────────────┘                          │
│                                                                      │
│  ┌─────────────────────────────────────┐                          │
│  │     PERFORMANCE OPTIMIZATION        │                          │
│  │                                     │                          │
│  │  • Multi-core scaling (RSS/RPS)    │                          │
│  │  • Zero-copy packet buffers        │                          │
│  │  • Lock-free queues                │                          │
│  │  • Cache-friendly data structures  │                          │
│  │  • Kernel bypass (DPDK/XDP)        │                          │
│  └─────────────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 NIDS Architecture (Network Inline)

```
         Internet
            │
            ▼
     ┌─────────────┐
     │   Router    │
     └─────────────┘
            │
            ▼
     ┌─────────────┐
     │  Firewall   │
     └─────────────┘
            │
            ▼
     ╔═════════════╗
     ║  IDS/IPS    ║◄──── TAP/SPAN port (passive)
     ║  Sensor     ║
     ║             ║◄──── Inline bridge (active)
     ╚═════════════╝
            │
            ▼
     ┌─────────────┐
     │   Switch    │
     └─────────────┘
            │
     ┌──────┴──────┐
     ▼             ▼
  Servers      Workstations
```

**Deployment Options**:

1. **Passive TAP**: Read-only mirror, no packet loss risk
2. **Inline Bridge**: L2 transparent, can drop packets (IPS)
3. **Routed Mode**: L3 hop, NAT/routing decisions

### 3.3 HIDS Architecture

```
┌────────────────────────────────────────────────────────┐
│                  HOST SYSTEM                            │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────┐      │
│  │         USER SPACE                           │      │
│  │                                              │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │      │
│  │  │   App    │  │   App    │  │   App    │  │      │
│  │  └──────────┘  └──────────┘  └──────────┘  │      │
│  │       │              │              │       │      │
│  │       └──────────────┴──────────────┘       │      │
│  │                      │                       │      │
│  │                      ▼                       │      │
│  │           ┌────────────────────┐            │      │
│  │           │   HIDS Agent       │            │      │
│  │           │                    │            │      │
│  │           │ • File Integrity   │            │      │
│  │           │ • Log Analysis     │            │      │
│  │           │ • Rootkit Detection│            │      │
│  │           │ • Process Monitor  │            │      │
│  │           └────────────────────┘            │      │
│  └──────────────────┬──────────────────────────┘      │
│                     │                                  │
│  ═══════════════════╪═════════════════════════════    │
│                     │                                  │
│  ┌──────────────────▼─────────────────────────────┐   │
│  │         KERNEL SPACE                           │   │
│  │                                                 │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │   eBPF Probes / kprobes / tracepoints    │  │   │
│  │  │                                          │  │   │
│  │  │  • syscall enter/exit                   │  │   │
│  │  │  • file open/close/write                │  │   │
│  │  │  • process exec/fork                    │  │   │
│  │  │  • network socket connect/accept        │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  │                                                 │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │   LSM (Linux Security Module)           │  │   │
│  │  │   - SELinux / AppArmor hooks            │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

---

## 4. Packet Capture & Processing Pipeline

### 4.1 Kernel-Based Capture (libpcap/AF_PACKET)

**Traditional Path**:
```
NIC → Hardware Interrupt → Kernel DMA → sk_buff → netfilter → 
→ socket buffer → user space (copy) → application
```

**Issues**:
- Multiple memory copies (kernel → user)
- Context switches
- Lock contention in kernel networking stack
- Interrupt storms at high packet rates

**AF_PACKET Optimization**:
```c
// PACKET_MMAP: zero-copy ring buffer
int sock = socket(PF_PACKET, SOCK_RAW, htons(ETH_P_ALL));

struct tpacket_req req = {
    .tp_block_size = 4096,     // Block size
    .tp_block_nr = 64,          // Number of blocks
    .tp_frame_size = 2048,      // Frame size
    .tp_frame_nr = 128          // Number of frames
};

setsockopt(sock, SOL_PACKET, PACKET_RX_RING, &req, sizeof(req));

// mmap shared ring buffer
void *ring = mmap(NULL, req.tp_block_size * req.tp_block_nr,
                  PROT_READ | PROT_WRITE, MAP_SHARED, sock, 0);

// Poll for packets without syscalls
struct tpacket_hdr *header;
while (1) {
    header = ring + (offset % ring_size);
    if (!(header->tp_status & TP_STATUS_USER))
        continue;  // Kernel still owns
    
    // Process packet at header + TPACKET_ALIGN(sizeof(*header))
    process_packet((uint8_t*)header + TPACKET_ALIGN(sizeof(*header)),
                   header->tp_len);
    
    header->tp_status = TP_STATUS_KERNEL;  // Return to kernel
}
```

### 4.2 Kernel Bypass with DPDK

**DPDK Architecture**:
```
┌─────────────────────────────────────────┐
│        USER SPACE APPLICATION           │
│  ┌───────────────────────────────────┐  │
│  │     DPDK Application (IDS)        │  │
│  └───────────────────────────────────┘  │
│              │         ▲                 │
│              ▼         │                 │
│  ┌───────────────────────────────────┐  │
│  │        DPDK Libraries             │  │
│  │  • rte_ethdev (Ethernet)          │  │
│  │  • rte_mbuf (packet buffers)      │  │
│  │  • rte_mempool (memory mgmt)      │  │
│  │  • rte_ring (lockless queues)     │  │
│  └───────────────────────────────────┘  │
│              │         ▲                 │
│              ▼         │                 │
│  ┌───────────────────────────────────┐  │
│  │      Poll Mode Drivers (PMD)      │  │
│  │    (NIC-specific drivers)         │  │
│  └───────────────────────────────────┘  │
└──────────────┬────────────▲──────────────┘
               │            │
     ══════════╪════════════╪════════════
               │            │
┌──────────────▼────────────┴──────────────┐
│         NIC (SR-IOV / Direct)            │
│    DMA directly to user space buffers   │
└──────────────────────────────────────────┘
```

**DPDK Packet Processing Example (C)**:
```c
#include <rte_eal.h>
#include <rte_ethdev.h>
#include <rte_mbuf.h>

#define RX_RING_SIZE 1024
#define NUM_MBUFS 8191
#define MBUF_CACHE_SIZE 250
#define BURST_SIZE 32

static void process_packets(struct rte_mbuf **pkts, uint16_t nb_pkts) {
    for (uint16_t i = 0; i < nb_pkts; i++) {
        struct rte_mbuf *pkt = pkts[i];
        uint8_t *data = rte_pktmbuf_mtod(pkt, uint8_t *);
        
        // Extract Ethernet header
        struct rte_ether_hdr *eth = (struct rte_ether_hdr *)data;
        
        // IP header
        if (eth->ether_type == rte_cpu_to_be_16(RTE_ETHER_TYPE_IPV4)) {
            struct rte_ipv4_hdr *ip = (struct rte_ipv4_hdr *)(data + 14);
            
            // Run detection logic
            if (detect_threat(data, pkt->pkt_len)) {
                // Drop packet or alert
                rte_pktmbuf_free(pkt);
                continue;
            }
        }
        
        // Forward if IPS inline mode
        rte_eth_tx_burst(out_port, 0, &pkt, 1);
    }
}

int main_loop(__attribute__((unused)) void *arg) {
    struct rte_mbuf *pkts_burst[BURST_SIZE];
    
    while (!quit_signal) {
        uint16_t nb_rx = rte_eth_rx_burst(port_id, 0,
                                           pkts_burst, BURST_SIZE);
        
        if (nb_rx == 0)
            continue;
        
        process_packets(pkts_burst, nb_rx);
    }
    return 0;
}
```

### 4.3 eBPF/XDP for In-Kernel Processing

**XDP Hook Point**:
```
NIC → XDP (earliest possible) → tc ingress → netfilter → socket
      ▲
      └── Can drop/redirect here before sk_buff allocation
```

**XDP Program Example (C)**:
```c
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 100000);
    __type(key, __u32);      // Source IP
    __type(value, __u64);    // Packet count
} blocklist SEC(".maps");

SEC("xdp")
int xdp_ids_prog(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    
    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;
    
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;
    
    // Check if source IP is blocklisted
    __u32 src_ip = ip->saddr;
    __u64 *count = bpf_map_lookup_elem(&blocklist, &src_ip);
    
    if (count) {
        // Blocked IP - drop immediately
        __sync_fetch_and_add(count, 1);
        return XDP_DROP;
    }
    
    // TCP SYN flood detection
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
        if ((void *)(tcp + 1) > data_end)
            return XDP_PASS;
        
        if (tcp->syn && !tcp->ack) {
            // SYN packet - rate limit logic here
            // If threshold exceeded, add to blocklist
        }
    }
    
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

**Load XDP Program (Go)**:
```go
package main

import (
    "github.com/cilium/ebpf"
    "github.com/cilium/ebpf/link"
    "net"
)

func loadXDP(ifname string) error {
    spec, err := ebpf.LoadCollectionSpec("xdp_ids.o")
    if err != nil {
        return err
    }
    
    coll, err := ebpf.NewCollection(spec)
    if err != nil {
        return err
    }
    defer coll.Close()
    
    iface, err := net.InterfaceByName(ifname)
    if err != nil {
        return err
    }
    
    l, err := link.AttachXDP(link.XDPOptions{
        Program:   coll.Programs["xdp_ids_prog"],
        Interface: iface.Index,
    })
    if err != nil {
        return err
    }
    defer l.Close()
    
    // Block until signal
    select {}
}
```

---

## 5. Pattern Matching & Rule Engines

### 5.1 Multi-Pattern Matching Algorithms

**Aho-Corasick**:
- Builds trie (prefix tree) + failure links
- O(n + m + z) where n=text, m=pattern total length, z=matches
- Used in Snort, Suricata

**Hyperscan (Intel)**:
- Regex compilation to DFA/NFA
- SIMD vectorization (AVX2/AVX512)
- Simultaneous matching of thousands of patterns
- State compression techniques

**Implementation Comparison**:
```go
package main

import (
    "github.com/cloudflare/ahocorasick"
    "github.com/intel/hyperscan-go/hyperscan"
)

// Aho-Corasick
func ahoCorasickMatch(payload []byte, patterns []string) []string {
    m := ahocorasick.NewStringMatcher(patterns)
    matches := []string{}
    
    hits := m.Match(payload)
    for _, hit := range hits {
        matches = append(matches, patterns[hit])
    }
    return matches
}

// Hyperscan
func hyperscanMatch(payload []byte, patterns []string) ([]string, error) {
    // Compile patterns
    db, err := hyperscan.NewBlockDatabase(
        hyperscan.NewPattern(patterns[0], hyperscan.SomLeftMost),
        // ... add more patterns
    )
    if err != nil {
        return nil, err
    }
    defer db.Close()
    
    scratch, err := hyperscan.NewScratch(db)
    if err != nil {
        return nil, err
    }
    defer scratch.Free()
    
    matches := []string{}
    err = db.Scan(payload, scratch, func(id uint, from, to uint64, flags uint, context interface{}) error {
        matches = append(matches, patterns[id])
        return nil
    }, nil)
    
    return matches, err
}
```

### 5.2 Rule Language Design (Snort-style)

**Rule Structure**:
```
action protocol src_ip src_port direction dst_ip dst_port (options)
```

**Example Rules**:
```bash
# SQL Injection
alert tcp any any -> $HTTP_SERVERS $HTTP_PORTS (
    msg:"SQL Injection attempt";
    flow:to_server,established;
    content:"SELECT"; nocase;
    content:"FROM"; nocase; distance:0;
    pcre:"/union.*select/i";
    sid:1000001;
)

# Port Scan Detection
alert tcp any any -> any any (
    msg:"Potential port scan";
    flags:S;
    threshold: type both, track by_src, count 20, seconds 60;
    sid:1000002;
)

# SSH Brute Force
alert tcp any any -> any 22 (
    msg:"SSH brute force attempt";
    flow:to_server;
    threshold: type both, track by_src, count 5, seconds 60;
    sid:1000003;
)
```

### 5.3 Rule Engine Implementation (Rust)

```rust
use regex::Regex;
use std::collections::HashMap;
use std::net::IpAddr;

#[derive(Debug, Clone)]
pub struct Rule {
    pub id: u32,
    pub action: Action,
    pub protocol: Protocol,
    pub src_ip: IpPattern,
    pub dst_ip: IpPattern,
    pub src_port: PortPattern,
    pub dst_port: PortPattern,
    pub content: Vec<ContentMatch>,
    pub pcre: Option<Regex>,
    pub msg: String,
}

#[derive(Debug, Clone)]
pub enum Action {
    Alert,
    Drop,
    Reject,
    Pass,
}

#[derive(Debug, Clone)]
pub enum Protocol {
    TCP,
    UDP,
    ICMP,
    IP,
}

#[derive(Debug, Clone)]
pub enum IpPattern {
    Any,
    Single(IpAddr),
    Cidr(IpAddr, u8),
    Variable(String),  // $HOME_NET
}

#[derive(Debug, Clone)]
pub struct ContentMatch {
    pub pattern: Vec<u8>,
    pub nocase: bool,
    pub offset: Option<usize>,
    pub depth: Option<usize>,
}

pub struct RuleEngine {
    rules: Vec<Rule>,
    variables: HashMap<String, Vec<IpAddr>>,
}

impl RuleEngine {
    pub fn new() -> Self {
        Self {
            rules: Vec::new(),
            variables: HashMap::new(),
        }
    }
    
    pub fn add_rule(&mut self, rule: Rule) {
        self.rules.push(rule);
    }
    
    pub fn evaluate(&self, packet: &Packet) -> Vec<Alert> {
        let mut alerts = Vec::new();
        
        for rule in &self.rules {
            if self.matches(rule, packet) {
                alerts.push(Alert {
                    rule_id: rule.id,
                    message: rule.msg.clone(),
                    action: rule.action.clone(),
                    timestamp: std::time::SystemTime::now(),
                });
            }
        }
        
        alerts
    }
    
    fn matches(&self, rule: &Rule, packet: &Packet) -> bool {
        // Protocol check
        if !self.match_protocol(&rule.protocol, packet) {
            return false;
        }
        
        // IP check
        if !self.match_ip(&rule.src_ip, &packet.src_ip) ||
           !self.match_ip(&rule.dst_ip, &packet.dst_ip) {
            return false;
        }
        
        // Port check
        if !self.match_port(&rule.src_port, packet.src_port) ||
           !self.match_port(&rule.dst_port, packet.dst_port) {
            return false;
        }
        
        // Content matching
        for content in &rule.content {
            if !self.match_content(content, &packet.payload) {
                return false;
            }
        }
        
        // PCRE
        if let Some(ref pcre) = rule.pcre {
            if let Ok(payload_str) = std::str::from_utf8(&packet.payload) {
                if !pcre.is_match(payload_str) {
                    return false;
                }
            } else {
                return false;
            }
        }
        
        true
    }
    
    fn match_content(&self, content: &ContentMatch, payload: &[u8]) -> bool {
        let start = content.offset.unwrap_or(0);
        let end = content.depth.map(|d| start + d).unwrap_or(payload.len());
        
        if end > payload.len() {
            return false;
        }
        
        let search_buf = &payload[start..end];
        
        if content.nocase {
            // Case-insensitive search
            search_buf.windows(content.pattern.len())
                .any(|window| window.eq_ignore_ascii_case(&content.pattern))
        } else {
            search_buf.windows(content.pattern.len())
                .any(|window| window == content.pattern.as_slice())
        }
    }
    
    // Additional matching functions...
}

#[derive(Debug)]
pub struct Packet {
    pub src_ip: IpAddr,
    pub dst_ip: IpAddr,
    pub src_port: u16,
    pub dst_port: u16,
    pub protocol: u8,
    pub payload: Vec<u8>,
}

#[derive(Debug)]
pub struct Alert {
    pub rule_id: u32,
    pub message: String,
    pub action: Action,
    pub timestamp: std::time::SystemTime,
}
```

---

## 6. Stateful Protocol Analysis

### 6.1 TCP State Machine

```
┌──────────┐
│  CLOSED  │
└─────┬────┘
      │ SYN
      ▼
┌──────────────┐
│  SYN_SENT    │
└─────┬────────┘
      │ SYN+ACK
      ▼
┌──────────────┐
│ ESTABLISHED  │◄────┐
└─────┬────────┘     │
      │ FIN          │ Data transfer
      ▼              │
┌──────────────┐     │
│  FIN_WAIT_1  │     │
└─────┬────────┘     │
      │ ACK          │
      ▼              │
┌──────────────┐     │
│  FIN_WAIT_2  │     │
└─────┬────────┘     │
      │ FIN          │
      ▼              │
┌──────────────┐     │
│  TIME_WAIT   │     │
└─────┬────────┘     │
      │ 2MSL timeout │
      ▼              │
┌──────────┐         │
│  CLOSED  │─────────┘
└──────────┘
```

**State Tracking Implementation (Go)**:
```go
package tcpstate

import (
    "net"
    "sync"
    "time"
)

type TCPState int

const (
    CLOSED TCPState = iota
    LISTEN
    SYN_SENT
    SYN_RECEIVED
    ESTABLISHED
    FIN_WAIT_1
    FIN_WAIT_2
    CLOSE_WAIT
    CLOSING
    LAST_ACK
    TIME_WAIT
)

type FlowKey struct {
    SrcIP   net.IP
    DstIP   net.IP
    SrcPort uint16
    DstPort uint16
}

type TCPFlow struct {
    State       TCPState
    SeqClient   uint32  // Client sequence
    SeqServer   uint32  // Server sequence
    AckClient   uint32
    AckServer   uint32
    WindowClient uint16
    WindowServer uint16
    LastSeen    time.Time
    BytesSent   uint64
    BytesRecv   uint64
}

type TCPTracker struct {
    flows map[FlowKey]*TCPFlow
    mu    sync.RWMutex
}

func NewTCPTracker() *TCPTracker {
    return &TCPTracker{
        flows: make(map[FlowKey]*TCPFlow),
    }
}

func (t *TCPTracker) ProcessPacket(key FlowKey, flags uint8, seq, ack uint32, window uint16, payloadLen int) error {
    t.mu.Lock()
    defer t.mu.Unlock()
    
    flow, exists := t.flows[key]
    if !exists {
        // New flow
        if flags&0x02 != 0 { // SYN
            flow = &TCPFlow{
                State:     SYN_SENT,
                SeqClient: seq,
                LastSeen:  time.Now(),
            }
            t.flows[key] = flow
        }
        return nil
    }
    
    flow.LastSeen = time.Now()
    
    // State transitions
    switch flow.State {
    case SYN_SENT:
        if flags&0x12 == 0x12 { // SYN+ACK
            flow.State = SYN_RECEIVED
            flow.SeqServer = seq
            flow.AckServer = ack
        }
        
    case SYN_RECEIVED:
        if flags&0x10 == 0x10 { // ACK
            flow.State = ESTABLISHED
            flow.AckClient = ack
        }
        
    case ESTABLISHED:
        // Check sequence numbers are in window
        if !t.validateSequence(flow, seq, ack, payloadLen) {
            return fmt.Errorf("out-of-window sequence")
        }
        
        if flags&0x01 != 0 { // FIN
            flow.State = FIN_WAIT_1
        }
        
        flow.BytesSent += uint64(payloadLen)
        
    case FIN_WAIT_1:
        if flags&0x10 == 0x10 { // ACK of FIN
            flow.State = FIN_WAIT_2
        }
        
    case FIN_WAIT_2:
        if flags&0x01 != 0 { // FIN from other side
            flow.State = TIME_WAIT
        }
        
    case TIME_WAIT:
        // After 2*MSL, remove flow
    }
    
    return nil
}

func (t *TCPTracker) validateSequence(flow *TCPFlow, seq, ack uint32, payloadLen int) bool {
    // Simplified: check if seq is within receive window
    expectedSeq := flow.SeqClient
    windowEnd := expectedSeq + uint32(flow.WindowClient)
    
    if seq < expectedSeq || seq > windowEnd {
        return false
    }
    
    // Update expected sequence
    flow.SeqClient = seq + uint32(payloadLen)
    
    return true
}

func (t *TCPTracker) DetectAnomalies(flow *TCPFlow, flags uint8) []string {
    anomalies := []string{}
    
    // Invalid flag combinations
    if flags&0x06 == 0x06 { // SYN+RST
        anomalies = append(anomalies, "Invalid SYN+RST flags")
    }
    
    if flags&0x03 == 0x03 { // SYN+FIN
        anomalies = append(anomalies, "Invalid SYN+FIN flags")
    }
    
    // State violations
    if flow.State == CLOSED && flags&0x02 == 0 {
        anomalies = append(anomalies, "Data on closed connection")
    }
    
    return anomalies
}

// Garbage collection for old flows
func (t *TCPTracker) CleanupStale(timeout time.Duration) {
    t.mu.Lock()
    defer t.mu.Unlock()
    
    now := time.Now()
    for key, flow := range t.flows {
        if now.Sub(flow.LastSeen) > timeout {
            delete(t.flows, key)
        }
    }
}
```

### 6.2 HTTP Protocol Analysis

```go
package httpanalyzer

import (
    "bufio"
    "bytes"
    "fmt"
    "net/http"
    "strings"
)

type HTTPAnalyzer struct {
    // Track reassembled streams
    streams map[FlowKey]*HTTPStream
}

type HTTPStream struct {
    ClientBuf bytes.Buffer
    ServerBuf bytes.Buffer
}

func (a *HTTPAnalyzer) AnalyzeRequest(data []byte) ([]Anomaly, error) {
    req, err := http.ReadRequest(bufio.NewReader(bytes.NewReader(data)))
    if err != nil {
        return nil, err
    }
    
    anomalies := []Anomaly{}
    
    // Check for SQL injection patterns
    if strings.Contains(req.URL.RawQuery, "' OR '1'='1") {
        anomalies = append(anomalies, Anomaly{
            Type: "SQL Injection",
            Severity: HIGH,
            Details: "SQL injection pattern in query string",
        })
    }
    
    // Check for XSS
    if strings.Contains(req.URL.RawQuery, "<script>") {
        anomalies = append(anomalies, Anomaly{
            Type: "XSS",
            Severity: HIGH,
            Details: "Script tag in query string",
        })
    }
    
    // Check for directory traversal
    if strings.Contains(req.URL.Path, "../") {
        anomalies = append(anomalies, Anomaly{
            Type: "Directory Traversal",
            Severity: MEDIUM,
            Details: "Path traversal attempt",
        })
    }
    
    // Check for abnormal headers
    if req.Header.Get("User-Agent") == "" {
        anomalies = append(anomalies, Anomaly{
            Type: "Missing User-Agent",
            Severity: LOW,
            Details: "No User-Agent header",
        })
    }
    
    // Check for oversized headers (potential DoS)
    if len(req.Header) > 100 {
        anomalies = append(anomalies, Anomaly{
            Type: "Header Bombing",
            Severity: MEDIUM,
            Details: fmt.Sprintf("Excessive headers: %d", len(req.Header)),
        })
    }
    
    return anomalies, nil
}
```

---

## 7. Anomaly Detection & ML Approaches

### 7.1 Feature Extraction

```go
package features

import (
    "time"
)

type FlowFeatures struct {
    // Basic
    Duration        time.Duration
    TotalPackets    int
    TotalBytes      int
    
    // Directional
    FwdPackets      int
    BwdPackets      int
    FwdBytes        int
    BwdBytes        int
    
    // Statistical
    PacketLenMean   float64
    PacketLenStd    float64
    PacketLenMax    int
    PacketLenMin    int
    
    // Temporal
    FlowIATMean     float64  // Inter-arrival time
    FlowIATStd      float64
    FlowIATMax      float64
    FlowIATMin      float64
    
    // TCP-specific
    FINFlagCount    int
    SYNFlagCount    int
    RSTFlagCount    int
    PSHFlagCount    int
    ACKFlagCount    int
    URGFlagCount    int
    
    // Behavioral
    DownUpRatio     float64
    AvgPacketSize   float64
    BytesPerSecond  float64
    PacketsPerSecond float64
}

func ExtractFeatures(flow *Flow) FlowFeatures {
    features := FlowFeatures{
        Duration:     flow.EndTime.Sub(flow.StartTime),
        TotalPackets: len(flow.Packets),
    }
    
    // Calculate statistics
    var packetLens []int
    var iats []time.Duration
    
    for i, pkt := range flow.Packets {
        packetLens = append(packetLens, pkt.Length)
        features.TotalBytes += pkt.Length
        
        if pkt.Direction == FORWARD {
            features.FwdPackets++
            features.FwdBytes += pkt.Length
        } else {
            features.BwdPackets++
            features.BwdBytes += pkt.Length
        }
        
        // IAT
        if i > 0 {
            iat := pkt.Timestamp.Sub(flow.Packets[i-1].Timestamp)
            iats = append(iats, iat)
        }
        
        // Flags
        if pkt.Flags&FIN != 0 {
            features.FINFlagCount++
        }
        // ... other flags
    }
    
    // Compute mean/std
    features.PacketLenMean = mean(packetLens)
    features.PacketLenStd = std(packetLens)
    features.PacketLenMax = max(packetLens)
    features.PacketLenMin = min(packetLens)
    
    if len(iats) > 0 {
        features.FlowIATMean = meanDuration(iats)
        features.FlowIATStd = stdDuration(iats)
    }
    
    // Derived metrics
    if features.BwdBytes > 0 {
        features.DownUpRatio = float64(features.FwdBytes) / float64(features.BwdBytes)
    }
    
    if features.TotalPackets > 0 {
        features.AvgPacketSize = float64(features.TotalBytes) / float64(features.TotalPackets)
    }
    
    seconds := features.Duration.Seconds()
    if seconds > 0 {
        features.BytesPerSecond = float64(features.TotalBytes) / seconds
        features.PacketsPerSecond = float64(features.TotalPackets) / seconds
    }
    
    return features
}
```

### 7.2 Isolation Forest (Anomaly Detection)

```python
# Python for ML model (called from Go/Rust via gRPC)
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

class AnomalyDetector:
    def __init__(self, contamination=0.01):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples=256
        )
        self.scaler = StandardScaler()
        
    def train(self, X_train):
        """Train on benign traffic baseline"""
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled)
        
    def predict(self, X):
        """Return anomaly scores (-1 = anomaly, 1 = normal)"""
        X_scaled = self.scaler.transform(X)
        scores = self.model.predict(X_scaled)
        decision_scores = self.model.decision_function(X_scaled)
        return scores, decision_scores
    
    def save(self, path):
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler
        }, path)
    
    @classmethod
    def load(cls, path):
        data = joblib.load(path)
        detector = cls()
        detector.model = data['model']
        detector.scaler = data['scaler']
        return detector

# Training example
if __name__ == "__main__":
    # Load features from normal traffic
    X_train = np.load('benign_features.npy')
    
    detector = AnomalyDetector(contamination=0.01)
    detector.train(X_train)
    detector.save('anomaly_model.pkl')
    
    # Inference
    X_test = np.load('test_features.npy')
    predictions, scores = detector.predict(X_test)
    
    anomalies = X_test[predictions == -1]
    print(f"Detected {len(anomalies)} anomalies")
```

**Integration with Go IDS**:
```go
package mldetector

import (
    "context"
    "google.golang.org/grpc"
    pb "your_project/anomaly_proto"
)

type MLDetector struct {
    client pb.AnomalyDetectorClient
}

func NewMLDetector(addr string) (*MLDetector, error) {
    conn, err := grpc.Dial(addr, grpc.WithInsecure())
    if err != nil {
        return nil, err
    }
    
    return &MLDetector{
        client: pb.NewAnomalyDetectorClient(conn),
    }, nil
}

func (d *MLDetector) IsAnomaly(features FlowFeatures) (bool, float64, error) {
    // Convert features to proto
    req := &pb.PredictRequest{
        Features: []float64{
            float64(features.Duration),
            float64(features.TotalPackets),
            features.PacketLenMean,
            features.PacketLenStd,
            // ... all features
        },
    }
    
    resp, err := d.client.Predict(context.Background(), req)
    if err != nil {
        return false, 0, err
    }
    
    return resp.IsAnomaly, resp.AnomalyScore, nil
}
```

---

## 8. Host-Based IDS (HIDS) Deep Dive

### 8.1 File Integrity Monitoring

```go
package fim

import (
    "crypto/sha256"
    "io"
    "os"
    "path/filepath"
    "time"
)

type FileRecord struct {
    Path         string
    SHA256       string
    Size         int64
    Mode         os.FileMode
    ModTime      time.Time
    Owner        uint32
    Group        uint32
}

type FIM struct {
    baseline  map[string]FileRecord
    watchDirs []string
}

func (f *FIM) CreateBaseline(dirs []string) error {
    f.baseline = make(map[string]FileRecord)
    
    for _, dir := range dirs {
        err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
            if err != nil {
                return err
            }
            
            if info.IsDir() {
                return nil
            }
            
            record, err := f.recordFile(path, info)
            if err != nil {
                return err
            }
            
            f.baseline[path] = record
            return nil
        })
        
        if err != nil {
            return err
        }
    }
    
    return nil
}

func (f *FIM) recordFile(path string, info os.FileInfo) (FileRecord, error) {
    file, err := os.Open(path)
    if err != nil {
        return FileRecord{}, err
    }
    defer file.Close()
    
    hash := sha256.New()
    if _, err := io.Copy(hash, file); err != nil {
        return FileRecord{}, err
    }
    
    return FileRecord{
        Path:    path,
        SHA256:  fmt.Sprintf("%x", hash.Sum(nil)),
        Size:    info.Size(),
        Mode:    info.Mode(),
        ModTime: info.ModTime(),
        // Get owner/group from stat_t
    }, nil
}

func (f *FIM) CheckIntegrity() []Alert {
    alerts := []Alert{}
    
    for path, baseline := range f.baseline {
        info, err := os.Stat(path)
        if err != nil {
            if os.IsNotExist(err) {
                alerts = append(alerts, Alert{
                    Type:     "File Deleted",
                    Path:     path,
                    Severity: HIGH,
                })
            }
            continue
        }
        
        current, err := f.recordFile(path, info)
        if err != nil {
            continue
        }
        
        // Check for changes
        if current.SHA256 != baseline.SHA256 {
            alerts = append(alerts, Alert{
                Type:     "File Modified",
                Path:     path,
                Severity: HIGH,
                Details:  fmt.Sprintf("Hash changed: %s -> %s", 
                                    baseline.SHA256[:8], current.SHA256[:8]),
            })
        }
        
        if current.Mode != baseline.Mode {
            alerts = append(alerts, Alert{
                Type:     "Permission Changed",
                Path:     path,
                Severity: MEDIUM,
                Details:  fmt.Sprintf("Mode: %v -> %v", baseline.Mode, current.Mode),
            })
        }
    }
    
    return alerts
}
```

### 8.2 System Call Monitoring with eBPF

```c
// ebpf/syscall_monitor.bpf.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct syscall_event {
    __u32 pid;
    __u32 uid;
    __u64 syscall_id;
    __u64 timestamp;
    char comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

// Dangerous syscalls to monitor
SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx) {
    struct syscall_event *event;
    
    event = bpf_ringbuf_reserve(&events, sizeof(*event), 0);
    if (!event)
        return 0;
    
    event->pid = bpf_get_current_pid_tgid() >> 32;
    event->uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    event->syscall_id = ctx->id;
    event->timestamp = bpf_ktime_get_ns();
    bpf_get_current_comm(&event->comm, sizeof(event->comm));
    
    bpf_ringbuf_submit(event, 0);
    return 0;
}

SEC("tracepoint/syscalls/sys_enter_connect")
int trace_connect(struct trace_event_raw_sys_enter *ctx) {
    // Similar monitoring for network connections
    return 0;
}

SEC("tracepoint/syscalls/sys_enter_open")
int trace_open(struct trace_event_raw_sys_enter *ctx) {
    // Monitor file opens
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

**Userspace Handler (Go)**:
```go
package syscallmon

import (
    "github.com/cilium/ebpf"
    "github.com/cilium/ebpf/ringbuf"
)

type SyscallMonitor struct {
    objs     *syscallMonitorObjects
    reader   *ringbuf.Reader
    baseline map[uint32]ProcessProfile  // pid -> profile
}

type ProcessProfile struct {
    Name            string
    AllowedSyscalls map[uint64]bool
    AllowedPaths    []string
}

func (m *SyscallMonitor) Start() error {
    spec, err := loadSyscallMonitor()
    if err != nil {
        return err
    }
    
    m.objs = &syscallMonitorObjects{}
    if err := spec.LoadAndAssign(m.objs, nil); err != nil {
        return err
    }
    
    m.reader, err = ringbuf.NewReader(m.objs.Events)
    if err != nil {
        return err
    }
    
    go m.processEvents()
    return nil
}

func (m *SyscallMonitor) processEvents() {
    for {
        record, err := m.reader.Read()
        if err != nil {
            continue
        }
        
        var event SyscallEvent
        if err := binary.Read(bytes.NewReader(record.RawSample), 
                             binary.LittleEndian, &event); err != nil {
            continue
        }
        
        if m.isAnomaly(event) {
            m.alertAnomaly(event)
        }
    }
}

func (m *SyscallMonitor) isAnomaly(event SyscallEvent) bool {
    profile, exists := m.baseline[event.PID]
    if !exists {
        // Unknown process - could be suspicious
        return true
    }
    
    if !profile.AllowedSyscalls[event.SyscallID] {
        // Unexpected syscall
        return true
    }
    
    return false
}
```

---

## 9. Cloud-Native & Container IDPS

### 9.1 Kubernetes Network Policy Enforcement

```yaml
# Network policy for microsegmentation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: load-balancer
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 9000
```

### 9.2 Falco Rules for Container Runtime Security

```yaml
# /etc/falco/falco_rules.local.yaml
- rule: Unexpected outbound connection
  desc: Detect unexpected egress connections from containers
  condition: >
    outbound and
    container and
    not proc.name in (allowed_processes) and
    not fd.sip in (allowed_destinations)
  output: >
    Unexpected outbound connection
    (user=%user.name process=%proc.name
     connection=%fd.name container=%container.name
     image=%container.image.repository)
  priority: WARNING
  tags: [network, container]

- rule: Terminal shell in container
  desc: A shell was spawned in a container
  condition: >
    spawned_process and
    container and
    proc.name in (shell_binaries) and
    not container.image.repository in (allowed_images)
  output: >
    Shell spawned in container
    (user=%user.name container=%container.name
     image=%container.image.repository
     shell=%proc.name parent=%proc.pname
     cmdline=%proc.cmdline)
  priority: WARNING
  tags: [shell, container]

- rule: Write below etc
  desc: Detect writes to /etc directory
  condition: >
    write and
    evt.dir = < and
    fd.name startswith /etc and
    not proc.name in (update_manager, dpkg, rpm)
  output: >
    File write below /etc
    (user=%user.name process=%proc.name
     file=%fd.name container=%container.name)
  priority: ERROR
  tags: [filesystem, container]

- macros:
  - macro: shell_binaries
    condition: proc.name in (bash, sh, zsh, ksh, csh)
    
  - macro: allowed_processes
    condition: proc.name in (curl, wget, apt, yum)
```

### 9.3 Service Mesh Integration (Envoy/Istio)

```go
package servicemesh

import (
    "context"
    envoy_auth "github.com/envoyproxy/go-control-plane/envoy/service/auth/v3"
    "google.golang.org/genproto/googleapis/rpc/status"
    "google.golang.org/grpc/codes"
)

// External Authorization Server for Envoy
type AuthzServer struct {
    ids *IDSEngine
}

func (s *AuthzServer) Check(ctx context.Context, 
                            req *envoy_auth.CheckRequest) (*envoy_auth.CheckResponse, error) {
    
    // Extract request attributes
    attrs := req.GetAttributes()
    httpReq := attrs.GetRequest().GetHttp()
    
    // Build IDS packet from Envoy attributes
    packet := Packet{
        SourceIP:   attrs.GetSource().GetAddress().GetSocketAddress().GetAddress(),
        DestIP:     attrs.GetDestination().GetAddress().GetSocketAddress().GetAddress(),
        Method:     httpReq.GetMethod(),
        Path:       httpReq.GetPath(),
        Headers:    httpReq.GetHeaders(),
        Body:       httpReq.GetBody(),
    }
    
    // Run IDS detection
    threats := s.ids.Analyze(packet)
    
    if len(threats) > 0 {
        // Block malicious request
        return &envoy_auth.CheckResponse{
            Status: &status.Status{
                Code:    int32(codes.PermissionDenied),
                Message: "Request blocked by IDS",
            },
        }, nil
    }
    
    // Allow
    return &envoy_auth.CheckResponse{
        Status: &status.Status{
            Code: int32(codes.OK),
        },
    }, nil
}
```

**Envoy Configuration**:
```yaml
static_resources:
  listeners:
  - address:
      socket_address:
        address: 0.0.0.0
        port_value: 8080
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          http_filters:
          - name: envoy.filters.http.ext_authz
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.ext_authz.v3.ExtAuthz
              grpc_service:
                envoy_grpc:
                  cluster_name: ids_authz_cluster
                timeout: 0.5s
          - name: envoy.filters.http.router
          route_config:
            name: local_route
            virtual_hosts:
            - name: backend
              domains: ["*"]
              routes:
              - match:
                  prefix: "/"
                route:
                  cluster: backend_cluster
  
  clusters:
  - name: ids_authz_cluster
    type: STRICT_DNS
    lb_policy: ROUND_ROBIN
    http2_protocol_options: {}
    load_assignment:
      cluster_name: ids_authz_cluster
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: ids-server
                port_value: 50051
```

---

## 10. Evasion Techniques & Countermeasures

### 10.1 Common Evasion Tactics

| Evasion Technique | Description | Countermeasure |
|------------------|-------------|----------------|
| **Fragmentation** | Split malicious payload across IP fragments | Fragment reassembly before inspection |
| **Encoding** | Base64, Unicode, URL encoding | Normalize and decode all variants |
| **Polymorphism** | Change attack signature on each iteration | Heuristic/behavioral detection |
| **Encryption** | TLS/SSL encrypted C2 channels | TLS interception, certificate pinning detection |
| **Timing** | Slow, low-volume attacks | Long-term behavioral baselines |
| **Protocol Confusion** | HTTP over non-standard ports | Deep packet inspection, protocol verification |
| **TTL Manipulation** | Packets expire before reaching target | Normalize TTL values |
| **Overlapping Fragments** | Confuse reassembly | RFC-compliant reassembly |

### 10.2 Fragment Reassembly (C)

```c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define MAX_FRAGMENTS 64
#define MAX_FRAG_SIZE 1500

typedef struct {
    uint16_t id;           // IP identification
    uint32_t src_ip;
    uint32_t dst_ip;
    uint8_t  protocol;
    
    struct fragment {
        uint16_t offset;
        uint16_t len;
        uint8_t  data[MAX_FRAG_SIZE];
        uint8_t  more_fragments;
    } fragments[MAX_FRAGMENTS];
    
    int frag_count;
    uint64_t first_seen;
    uint8_t  complete;
} ip_reassembly_ctx_t;

// Reassembly table
#define REASSEMBLY_TABLE_SIZE 1024
ip_reassembly_ctx_t *reassembly_table[REASSEMBLY_TABLE_SIZE];

uint32_t hash_flow(uint16_t id, uint32_t src, uint32_t dst, uint8_t proto) {
    return (id ^ src ^ dst ^ proto) % REASSEMBLY_TABLE_SIZE;
}

int insert_fragment(uint16_t id, uint32_t src, uint32_t dst, uint8_t proto,
                   uint16_t offset, uint16_t len, uint8_t *data, 
                   uint8_t more_frags) {
    uint32_t hash = hash_flow(id, src, dst, proto);
    ip_reassembly_ctx_t *ctx = reassembly_table[hash];
    
    if (!ctx) {
        ctx = calloc(1, sizeof(ip_reassembly_ctx_t));
        ctx->id = id;
        ctx->src_ip = src;
        ctx->dst_ip = dst;
        ctx->protocol = proto;
        ctx->first_seen = get_timestamp_ms();
        reassembly_table[hash] = ctx;
    }
    
    // Insert fragment in order
    int idx = ctx->frag_count++;
    ctx->fragments[idx].offset = offset;
    ctx->fragments[idx].len = len;
    memcpy(ctx->fragments[idx].data, data, len);
    ctx->fragments[idx].more_fragments = more_frags;
    
    // Check if complete
    if (!more_frags) {
        // Sort fragments by offset
        qsort(ctx->fragments, ctx->frag_count, 
              sizeof(struct fragment), cmp_offset);
        
        // Verify contiguous
        uint16_t expected_offset = 0;
        for (int i = 0; i < ctx->frag_count; i++) {
            if (ctx->fragments[i].offset != expected_offset) {
                return -1;  // Gap or overlap
            }
            expected_offset += ctx->fragments[i].len;
        }
        
        ctx->complete = 1;
        return 1;  // Reassembly complete
    }
    
    return 0;  // More fragments expected
}

uint8_t* get_reassembled_packet(uint16_t id, uint32_t src, uint32_t dst, 
                               uint8_t proto, uint32_t *out_len) {
    uint32_t hash = hash_flow(id, src, dst, proto);
    ip_reassembly_ctx_t *ctx = reassembly_table[hash];
    
    if (!ctx || !ctx->complete)
        return NULL;
    
    // Allocate buffer for full packet
    uint32_t total_len = 0;
    for (int i = 0; i < ctx->frag_count; i++) {
        total_len += ctx->fragments[i].len;
    }
    
    uint8_t *packet = malloc(total_len);
    uint32_t pos = 0;
    
    for (int i = 0; i < ctx->frag_count; i++) {
        memcpy(packet + pos, ctx->fragments[i].data, ctx->fragments[i].len);
        pos += ctx->fragments[i].len;
    }
    
    *out_len = total_len;
    return packet;
}

// Timeout stale reassembly contexts
void cleanup_reassembly_table(uint64_t timeout_ms) {
    uint64_t now = get_timestamp_ms();
    
    for (int i = 0; i < REASSEMBLY_TABLE_SIZE; i++) {
        if (reassembly_table[i] && 
            (now - reassembly_table[i]->first_seen) > timeout_ms) {
            free(reassembly_table[i]);
            reassembly_table[i] = NULL;
        }
    }
}
```

---

## 11. Performance Optimization

### 11.1 Multi-Core Scaling with RSS/RPS

```
┌────────────────────────────────────────────────┐
│            NIC with RSS (Receive Side Scaling) │
└────────────────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │  Hash(src_ip, dst_ip,      │
        │       src_port, dst_port)  │
        └─────────────┬──────────────┘
                      │
        ┌─────────────┴──────────────┐
        ▼             ▼              ▼
    Queue 0       Queue 1        Queue 2
        │             │              │
        ▼             ▼              ▼
    CPU Core 0    CPU Core 1     CPU Core 2
    │             │              │
    ▼             ▼              ▼
  IDS Worker    IDS Worker     IDS Worker
```

**Setup RSS (bash)**:
```bash
#!/bin/bash
# Enable RSS on network interface

IFACE="eth0"
NUM_CORES=$(nproc)

# Set number of queues to number of cores
ethtool -L $IFACE combined $NUM_CORES

# Set IRQ affinity
for i in $(seq 0 $((NUM_CORES-1))); do
    IRQ=$(grep "$IFACE-TxRx-$i" /proc/interrupts | cut -d: -f1 | tr -d ' ')
    echo $((1 << i)) > /proc/irq/$IRQ/smp_affinity
done

# Verify
ethtool -l $IFACE
cat /proc/interrupts | grep $IFACE
```

### 11.2 Lock-Free Data Structures (Rust)

```rust
use crossbeam::queue::SegQueue;
use std::sync::Arc;
use std::thread;

// Lock-free packet queue
pub struct PacketQueue {
    queue: Arc<SegQueue<Packet>>,
}

impl PacketQueue {
    pub fn new() -> Self {
        Self {
            queue: Arc::new(SegQueue::new()),
        }
    }
    
    pub fn enqueue(&self, pkt: Packet) {
        self.queue.push(pkt);
    }
    
    pub fn dequeue(&self) -> Option<Packet> {
        self.queue.pop()
    }
    
    pub fn spawn_workers(&self, num_workers: usize, processor: fn(Packet)) {
        for i in 0..num_workers {
            let queue = Arc::clone(&self.queue);
            
            thread::spawn(move || {
                loop {
                    if let Some(pkt) = queue.pop() {
                        processor(pkt);
                    } else {
                        std::hint::spin_loop();
                    }
                }
            });
        }
    }
}

// Usage
fn packet_processor(pkt: Packet) {
    // Run IDS detection
    let alerts = analyze_packet(&pkt);
    // Handle alerts
}

fn main() {
    let queue = PacketQueue::new();
    queue.spawn_workers(8, packet_processor);
    
    // Capture thread feeds queue
    loop {
        let pkt = capture_packet();
        queue.enqueue(pkt);
    }
}
```

### 11.3 Zero-Copy Techniques

```c
// Packet buffer pool with memory mapping
#define PACKET_SIZE 2048
#define NUM_PACKETS 65536

typedef struct {
    void *mmap_region;
    uint32_t *free_list;
    uint32_t free_count;
} packet_pool_t;

packet_pool_t* create_packet_pool() {
    packet_pool_t *pool = malloc(sizeof(packet_pool_t));
    
    // Allocate huge page for packet buffers
    size_t pool_size = PACKET_SIZE * NUM_PACKETS;
    pool->mmap_region = mmap(NULL, pool_size, 
                             PROT_READ | PROT_WRITE,
                             MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                             -1, 0);
    
    if (pool->mmap_region == MAP_FAILED) {
        // Fallback to regular pages
        pool->mmap_region = mmap(NULL, pool_size,
                                 PROT_READ | PROT_WRITE,
                                 MAP_PRIVATE | MAP_ANONYMOUS,
                                 -1, 0);
    }
    
    // Initialize free list
    pool->free_list = malloc(sizeof(uint32_t) * NUM_PACKETS);
    pool->free_count = NUM_PACKETS;
    
    for (uint32_t i = 0; i < NUM_PACKETS; i++) {
        pool->free_list[i] = i;
    }
    
    return pool;
}

void* alloc_packet(packet_pool_t *pool) {
    if (pool->free_count == 0)
        return NULL;
    
    uint32_t idx = pool->free_list[--pool->free_count];
    return pool->mmap_region + (idx * PACKET_SIZE);
}

void free_packet(packet_pool_t *pool, void *pkt) {
    uint32_t idx = (pkt - pool->mmap_region) / PACKET_SIZE;
    pool->free_list[pool->free_count++] = idx;
}
```

---

## 12. Threat Model & Security Analysis

### 12.1 STRIDE Threat Model for IDPS

| Threat | Attack Vector | Mitigation |
|--------|---------------|------------|
| **Spoofing** | Attacker spoofs source IP to bypass IP-based rules | Use cryptographic authentication (mTLS, IPsec) |
| **Tampering** | Attacker modifies IDS logs/alerts | Tamper-evident logging (syslog-ng, WORM storage) |
| **Repudiation** | Attacker denies malicious activity | Non-repudiable audit logs with timestamps |
| **Info Disclosure** | IDS exposes network topology in alerts | Sanitize alerts, encrypt alert channels |
| **DoS** | Flood IDS with traffic to overwhelm | Rate limiting, resource quotas, load shedding |
| **Elevation** | Compromise IDS to gain network access | Least privilege, sandboxing, SELinux confinement |

### 12.2 Attack Surface Analysis

```
┌──────────────────────────────────────────────────┐
│           IDPS ATTACK SURFACE                     │
├──────────────────────────────────────────────────┤
│                                                   │
│  1. PACKET CAPTURE LAYER                         │
│     • Buffer overflows in packet parsing         │
│     • Malformed packet crashes                   │
│     • Resource exhaustion (packet flood)         │
│                                                   │
│  2. PROTOCOL DECODERS                            │
│     • Parser vulnerabilities (HTTP, DNS, TLS)    │
│     • Integer overflows in length fields         │
│     • State machine confusion                    │
│                                                   │
│  3. PATTERN MATCHING ENGINE                      │
│     • ReDoS (Regular Expression DoS)             │
│     • Algorithmic complexity attacks             │
│                                                   │
│  4. MANAGEMENT INTERFACE                         │
│     • Authentication bypass                       │
│     • Command injection in rule upload           │
│     • XSS in web UI                              │
│                                                   │
│  5. LOG/ALERT OUTPUT                             │
│     • Log injection                              │
│     • SIEM integration vulnerabilities           │
│                                                   │
└──────────────────────────────────────────────────┘
```

### 12.3 Defense in Depth for IDS

```go
package security

// Sandboxed rule execution
func executeSandboxedRule(rule Rule, packet Packet) (bool, error) {
    // Create seccomp sandbox
    if err := applySeccompFilter(); err != nil {
        return false, err
    }
    
    // Resource limits
    ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
    defer cancel()
    
    // Execute rule matching in goroutine with timeout
    resultChan := make(chan bool, 1)
    go func() {
        resultChan <- rule.Match(packet)
    }()
    
    select {
    case result := <-resultChan:
        return result, nil
    case <-ctx.Done():
        return false, fmt.Errorf("rule execution timeout")
    }
}

func applySeccompFilter() error {
    // Allow only safe syscalls
    allowedSyscalls := []string{
        "read", "write", "close",
        "mmap", "munmap",
        "futex", "sched_yield",
    }
    
    // Install seccomp-bpf filter (platform-specific)
    return installSeccomp(allowedSyscalls)
}
```

---

## 13. Production Deployment

### 13.1 High-Availability Architecture

```
┌───────────────────────────────────────────────────────┐
│            Load Balancer (L4 DSR)                     │
└─────────────┬─────────────────────────────────────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
   ┌─────────┐ ┌─────────┐
   │ IDS #1  │ │ IDS #2  │  (Active-Active)
   │ Primary │ │ Secondary│
   └─────────┘ └─────────┘
        │           │
        └─────┬─────┘
              ▼
    ┌──────────────────┐
    │  Shared State    │
    │  (Redis/Memcached│
    │   or etcd)       │
    └──────────────────┘
              │
              ▼
    ┌──────────────────┐
    │  Alert Queue     │
    │  (Kafka/NATS)    │
    └──────────────────┘
              │
              ▼
    ┌──────────────────┐
    │  SIEM / SOC      │
    └──────────────────┘
```

### 13.2 Kubernetes Deployment

```yaml
# ids-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ids-sensor
  namespace: security
spec:
  selector:
    matchLabels:
      app: ids-sensor
  template:
    metadata:
      labels:
        app: ids-sensor
    spec:
      hostNetwork: true
      hostPID: true
      
      initContainers:
      - name: bpf-loader
        image: ids-bpf-loader:latest
        securityContext:
          privileged: true
        volumeMounts:
        - name: sys
          mountPath: /sys
        - name: bpf-maps
          mountPath: /sys/fs/bpf
      
      containers:
      - name: ids-engine
        image: ids-engine:v1.0.0
        securityContext:
          capabilities:
            add:
            - NET_ADMIN
            - NET_RAW
            - SYS_ADMIN
          privileged: false
        
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: INTERFACE
          value: "eth0"
        
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        
        volumeMounts:
        - name: rules
          mountPath: /etc/ids/rules
        - name: bpf-maps
          mountPath: /sys/fs/bpf
        - name: var-log
          mountPath: /var/log/ids
      
      volumes:
      - name: sys
        hostPath:
          path: /sys
      - name: bpf-maps
        hostPath:
          path: /sys/fs/bpf
      - name: rules
        configMap:
          name: ids-rules
      - name: var-log
        hostPath:
          path: /var/log/ids
      
      tolerations:
      - effect: NoSchedule
        operator: Exists
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ids-rules
  namespace: security
data:
  local.rules: |
    alert tcp any any -> any any (
      msg:"Crypto mining traffic detected";
      content:"stratum+tcp://";
      sid:1000100;
    )
```

### 13.3 Monitoring & Observability

```yaml
# Prometheus ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ids-metrics
  namespace: security
spec:
  selector:
    matchLabels:
      app: ids-sensor
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
```

**Metrics to Export**:
```go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    PacketsProcessed = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "ids_packets_processed_total",
            Help: "Total packets processed",
        },
        []string{"interface", "protocol"},
    )
    
    AlertsGenerated = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "ids_alerts_generated_total",
            Help: "Total alerts generated",
        },
        []string{"severity", "category"},
    )
    
    ProcessingLatency = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "ids_processing_latency_seconds",
            Help:    "Packet processing latency",
            Buckets: prometheus.ExponentialBuckets(0.00001, 2, 15),
        },
        []string{"stage"},
    )
    
    DroppedPackets = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "ids_packets_dropped_total",
            Help: "Packets dropped due to resource limits",
        },
        []string{"reason"},
    )
    
    CPUUtilization = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "ids_cpu_utilization_percent",
            Help: "CPU utilization per core",
        },
        []string{"core"},
    )
    
    MemoryUsage = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "ids_memory_usage_bytes",
            Help: "Memory usage in bytes",
        },
    )
)
```

---

## 14. Testing, Fuzzing, Benchmarking

### 14.1 Unit Tests (Go)

```go
package detector

import (
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestSQLInjectionDetection(t *testing.T) {
    detector := NewDetector()
    
    tests := []struct {
        name     string
        payload  string
        expected bool
    }{
        {
            name:     "Basic SQL injection",
            payload:  "' OR '1'='1",
            expected: true,
        },
        {
            name:     "Union-based injection",
            payload:  "UNION SELECT * FROM users",
            expected: true,
        },
        {
            name:     "Benign query",
            payload:  "SELECT name FROM products WHERE id=5",
            expected: false,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := detector.DetectSQLInjection([]byte(tt.payload))
            assert.Equal(t, tt.expected, result)
        })
    }
}

func BenchmarkPatternMatching(b *testing.B) {
    detector := NewDetector()
    payload := []byte("GET /index.php?id=' OR '1'='1 HTTP/1.1")
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        detector.Analyze(payload)
    }
}
```

### 14.2 Fuzzing with AFL++

```c
// fuzz_target.c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

extern int analyze_packet(const uint8_t *data, size_t len);

// AFL++ entry point
__AFL_FUZZ_INIT();

int main(void) {
#ifdef __AFL_HAVE_MANUAL_CONTROL
    __AFL_INIT();
#endif
    
    uint8_t *buf = __AFL_FUZZ_TESTCASE_BUF;
    
    while (__AFL_LOOP(10000)) {
        size_t len = __AFL_FUZZ_TESTCASE_LEN;
        
        // Target function
        analyze_packet(buf, len);
    }
    
    return 0;
}
```

**Build and Fuzz**:
```bash
# Compile with AFL++
AFL_USE_ASAN=1 afl-clang-fast -g -O2 -o fuzz_target \
    fuzz_target.c ids_core.c -lpcre

# Run fuzzer
afl-fuzz -i testcases/ -o findings/ -m none -- ./fuzz_target

# Reproduce crash
./fuzz_target < findings/crashes/id:000000,sig:11,src:000000,op:havoc,rep:4
```

### 14.3 Performance Benchmarking

```bash
#!/bin/bash
# benchmark.sh

# Generate test traffic with tcpreplay
tcpreplay --intf1=eth0 --pps=100000 --loop=10 \
    captures/attack_traffic.pcap &

# Measure packet loss
BEFORE=$(ethtool -S eth0 | grep rx_dropped | awk '{print $2}')
sleep 60
AFTER=$(ethtool -S eth0 | grep rx_dropped | awk '{print $2}')

DROPPED=$((AFTER - BEFORE))
echo "Packets dropped: $DROPPED"

# CPU profiling
perf record -F 99 -p $(pgrep ids-engine) -g -- sleep 30
perf report

# Memory profiling
valgrind --tool=massif --massif-out-file=massif.out ./ids-engine
ms_print massif.out

# Flame graph
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
```

---

## 15. Rollout/Rollback Strategy

### 15.1 Phased Deployment

```
Phase 1: Passive Monitoring (Week 1-2)
├─ Deploy in TAP/mirror mode
├─ Collect baseline metrics
├─ Tune false positive rate
└─ Validate detection accuracy

Phase 2: Shadow Mode (Week 3-4)
├─ Run alongside existing security controls
├─ Compare alerts with SIEM
├─ Refine rules based on feedback
└─ Performance optimization

Phase 3: Canary Deployment (Week 5)
├─ Enable inline mode on 10% of traffic
├─ Monitor for packet loss
├─ Validate business continuity
└─ Measure latency impact

Phase 4: Full Rollout (Week 6+)
├─ Gradual increase to 100% traffic
├─ Continuous monitoring
└─ Incident response readiness
```

### 15.2 Rollback Procedure

```bash
#!/bin/bash
# rollback.sh

set -e

echo "Initiating IDS rollback..."

# 1. Switch to passive mode immediately
kubectl patch daemonset ids-sensor -n security \
    -p '{"spec":{"template":{"spec":{"containers":[{"name":"ids-engine","env":[{"name":"MODE","value":"passive"}]}]}}}}'

# 2. Drain traffic from problematic nodes
for NODE in $(kubectl get nodes -l ids-version=new -o name); do
    kubectl cordon $NODE
    kubectl drain $NODE --ignore-daemonsets --delete-emptydir-data
done

# 3. Restore previous version
kubectl rollout undo daemonset/ids-sensor -n security

# 4. Wait for rollback to complete
kubectl rollout status daemonset/ids-sensor -n security

# 5. Uncordon nodes
for NODE in $(kubectl get nodes -l ids-version=new -o name); do
    kubectl uncordon $NODE
done

# 6. Verify health
kubectl get pods -n security -l app=ids-sensor
kubectl logs -n security -l app=ids-sensor --tail=100

echo "Rollback complete"
```

### 15.3 Circuit Breaker Pattern

```go
package deploy

import (
    "sync/atomic"
    "time"
)

type CircuitBreaker struct {
    errorThreshold   uint32
    errorCount       uint32
    lastError        time.Time
    state            uint32  // 0=closed, 1=open, 2=half-open
    resetTimeout     time.Duration
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    state := atomic.LoadUint32(&cb.state)
    
    if state == 1 {  // Open
        if time.Since(cb.lastError) > cb.resetTimeout {
            atomic.StoreUint32(&cb.state, 2)  // Half-open
        } else {
            return fmt.Errorf("circuit breaker open")
        }
    }
    
    err := fn()
    
    if err != nil {
        atomic.AddUint32(&cb.errorCount, 1)
        cb.lastError = time.Now()
        
        if atomic.LoadUint32(&cb.errorCount) >= cb.errorThreshold {
            atomic.StoreUint32(&cb.state, 1)  // Open circuit
            // Trigger automatic rollback
            triggerRollback()
        }
        
        return err
    }
    
    // Success - reset counters
    atomic.StoreUint32(&cb.errorCount, 0)
    if state == 2 {  // Half-open -> Closed
        atomic.StoreUint32(&cb.state, 0)
    }
    
    return nil
}

func triggerRollback() {
    // Automatically revert to passive mode
    log.Error("Circuit breaker triggered - entering passive mode")
    setIDSMode("passive")
    
    // Alert operations
    sendAlert("IDS automatic rollback initiated")
}
```

---

## 16. References & Further Reading

### Core Papers
1. **Snort**: "Snort - Lightweight Intrusion Detection for Networks" (Roesch, 1999)
2. **Bro/Zeek**: "The Bro Network Security Monitor" (Paxson, 1999)
3. **Suricata**: "Suricata - A Multi-threaded IDS/IPS" (OISF, 2009)
4. **Machine Learning IDS**: "A Survey of Data Mining and Machine Learning Methods for Cyber Security Intrusion Detection" (Buczak & Guven, 2016)

### Books
- "Applied Network Security Monitoring" (Chris Sanders & Jason Smith)
- "The Practice of Network Security Monitoring" (Richard Bejtlich)
- "Network Intrusion Detection" (Stephen Northcutt & Judy Novak)

### Tools & Projects
- **Suricata**: https://suricata.io/
- **Zeek**: https://zeek.org/
- **OSSEC**: https://www.ossec.net/
- **Falco**: https://falco.org/
- **Cilium Tetragon**: https://github.com/cilium/tetragon

### Standards
- **NSA IDPS Guide**: https://media.defense.gov/2023/Jun/13/2003239290/-1/-1/0/CTR_NSA_GUIDE_FOR_SELECTING_IDPS_U_OO_133086_23.PDF
- **NIST SP 800-94**: Guide to Intrusion Detection and Prevention Systems (IDPS)

---

## 17. Next 3 Steps

### Step 1: Build Minimal NIDS Prototype (Week 1)
```bash
# Objective: Packet capture → signature match → alert

# 1. Setup development environment
sudo apt install libpcap-dev golang-go

# 2. Implement basic packet capture
git clone your-repo/ids-minimal
cd ids-minimal

# 3. Write packet processor
cat > main.go << 'EOF'
package main

import (
    "fmt"
    "log"
    "github.com/google/gopacket"
    "github.com/google/gopacket/pcap"
)

func main() {
    handle, err := pcap.OpenLive("eth0", 1600, true, pcap.BlockForever)
    if err != nil {
        log.Fatal(err)
    }
    defer handle.Close()
    
    packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
    
    for packet := range packetSource.Packets() {
        // Extract payload
        if appLayer := packet.ApplicationLayer(); appLayer != nil {
            payload := appLayer.Payload()
            
            // Simple signature check
            if bytes.Contains(payload, []byte("malware_signature")) {
                fmt.Printf("ALERT: Malware detected! %v\n", packet)
            }
        }
    }
}
EOF

# 4. Test
go mod init ids-minimal
go mod tidy
sudo go run main.go

# 5. Validate with test traffic
tcpreplay --intf1=eth0 malware_sample.pcap
```

**Expected Output**: Console alerts when pattern matches

---

### Step 2: Implement Stateful TCP Tracking (Week 2)
```bash
# Objective: Track TCP connections, detect anomalies

# 1. Add TCP state machine
cat > tcp_tracker.go << 'EOF'
// See Section 6.1 for full implementation
EOF

# 2. Integrate into packet processor
# 3. Test with various TCP scenarios:
#    - Normal connection
#    - SYN flood
#    - Out-of-sequence packets
#    - Invalid flag combinations

# 4. Benchmark
go test -bench=. -benchmem

# Expected: <10μs per packet processing latency
```

---

### Step 3: Deploy in Kubernetes with eBPF (Week 3-4)
```bash
# Objective: Production-ready deployment with eBPF acceleration

# 1. Build eBPF program
cd ebpf
make

# 2. Create container image
docker build -t ids-engine:v1 .

# 3. Deploy to K8s
kubectl apply -f k8s/ids-daemonset.yaml

# 4. Verify
kubectl get pods -n security
kubectl logs -n security ids-sensor-xxxxx

# 5. Load test
kubectl run -it --rm load-gen --image=nicolaka/netshoot -- bash
# Inside pod: run traffic generator

# 6. Monitor metrics
kubectl port-forward -n security svc/prometheus 9090:9090
# Open http://localhost:9090 and query ids_* metrics

# Expected: <1% packet loss at 1M pps, <5% CPU overhead
```

---

**Verification Criteria**:
- [ ] Step 1: Successfully captures and alerts on test patterns
- [ ] Step 2: Correctly tracks TCP state, detects anomalies
- [ ] Step 3: Runs in production K8s cluster with metrics

**Failure Modes**:
- Packet drops at high rate → Check RSS/RPS configuration, consider DPDK
- High CPU usage → Profile with perf, optimize pattern matching
- False positives → Tune signatures, add whitelisting

---

This guide provides end-to-end coverage of IDPS from theory to production deployment. Focus on iterative development: start with basic functionality, validate correctness, then optimize for performance and scale. Always prioritize security-by-design and defense-in-depth principles.