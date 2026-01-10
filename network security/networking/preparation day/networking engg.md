# Comprehensive Networking Software Engineer Interview Guide

*"Mastery in networking is not just knowing the protocols—it's understanding the fundamental tradeoffs, failure modes, and performance characteristics that govern distributed systems."*

---

## **Part 1: Foundational Concepts**

### **1. Explain the OSI Model vs TCP/IP Model. Why do we still reference OSI when TCP/IP is what's actually implemented?**

**Expert Answer:**

The OSI model (7 layers) is a **conceptual framework** for understanding network functions, while TCP/IP (4 layers) is the **practical implementation** used in the Internet.

**OSI (Open Systems Interconnection):**
1. Physical - Bits on wire (voltage, radio waves)
2. Data Link - Frame delivery on local network (MAC addresses, Ethernet)
3. Network - Packet routing across networks (IP)
4. Transport - End-to-end communication (TCP, UDP)
5. Session - Connection management
6. Presentation - Data format translation (encryption, compression)
7. Application - User-facing protocols (HTTP, DNS)

**TCP/IP Model:**
1. Link Layer (combines Physical + Data Link)
2. Internet Layer (Network)
3. Transport Layer
4. Application Layer (combines Session + Presentation + Application)

**Why OSI persists:**
- **Pedagogical clarity**: Breaking concerns into 7 layers helps newcomers understand separation of responsibilities
- **Troubleshooting framework**: "Is this a Layer 2 or Layer 3 problem?" provides diagnostic structure
- **Vendor neutrality**: OSI doesn't favor any implementation

**Mental Model:** Think of OSI as the "theoretical ideal" and TCP/IP as the "battle-tested reality." You reference OSI for conceptual discussions, TCP/IP for actual implementation.

---

### **2. What happens when you type `google.com` in your browser? (Deep dive)**

**Expert's Structured Breakdown:**

**Phase 1: DNS Resolution**
1. Browser checks **DNS cache** (browser → OS → router)
2. If miss, queries **recursive DNS resolver** (ISP or 8.8.8.8)
3. Resolver queries:
   - Root nameserver (returns .com TLD server)
   - TLD nameserver (returns google.com authoritative server)
   - Authoritative server (returns IP: 142.250.80.46)
4. **Optimization**: DNS uses UDP port 53 for speed (with retries)

**Phase 2: TCP Connection (Three-Way Handshake)**
```
Client → Server: SYN (sequence = x)
Server → Client: SYN-ACK (sequence = y, ack = x+1)
Client → Server: ACK (ack = y+1)
```
**Why this matters:** Establishes reliable connection over unreliable IP

**Phase 3: TLS Handshake (if HTTPS)**
1. ClientHello: Supported cipher suites, TLS version
2. ServerHello: Chosen cipher, certificate
3. **Certificate verification** against trusted CA
4. Key exchange (RSA or Diffie-Hellman)
5. Generate session keys
6. Encrypted communication begins

**Phase 4: HTTP Request**
```
GET / HTTP/1.1
Host: google.com
User-Agent: Mozilla/5.0...
Accept: text/html
```

**Phase 5: Server Processing & Response**
- Load balancer routes to backend server
- Server processes request (checks cache, queries database)
- Returns HTTP response with HTML, status code

**Phase 6: Rendering**
- Browser parses HTML → constructs DOM tree
- Fetches CSS, JavaScript, images (parallel connections)
- Renders page incrementally

**Performance Insights:**
- **DNS**: ~20-120ms (cacheable)
- **TCP handshake**: 1 RTT (round-trip time)
- **TLS handshake**: 1-2 RTT
- **Total**: Often 200-500ms for first byte

**Optimization opportunities:** HTTP/2, connection reuse, DNS prefetching, CDN edge caching

---

### **3. TCP vs UDP: When would you choose UDP over TCP despite its unreliability?**

**Deep Analysis:**

| Aspect | TCP | UDP |
|--------|-----|-----|
| **Reliability** | Guarantees delivery, order | Best-effort, no guarantees |
| **Overhead** | ~20 bytes + retransmissions | 8 bytes header |
| **Latency** | Variable (retransmits add delay) | Predictable, low |
| **Use Case** | Data integrity critical | Speed > reliability |

**UDP is superior when:**

1. **Real-time applications** (gaming, VoIP, video conferencing)
   - **Why**: 100ms delayed voice packet is worthless—better to drop it
   - Retransmitting old audio creates stuttering

2. **High-frequency updates** (stock tickers, IoT sensors)
   - **Why**: Only latest value matters; old data obsolete

3. **Multicast/Broadcast**
   - **Why**: TCP is point-to-point only

4. **Custom reliability layer** (QUIC, SCTP)
   - **Why**: Build exactly the guarantees you need

**Real-world example:**
```
Video streaming (like Zoom):
- Uses UDP for video/audio packets
- 1% packet loss acceptable (interpolation handles it)
- TCP would cause buffering as it waits for retransmits
```

**Implementation Pattern (Rust):**
```rust
// UDP socket for low-latency gaming
use std::net::UdpSocket;

fn send_player_position(socket: &UdpSocket, pos: (f32, f32, f32)) -> std::io::Result<()> {
    let data = bincode::serialize(&pos).unwrap();
    socket.send(&data)?;
    // No ACK needed - next update in 16ms anyway (60 FPS)
    Ok(())
}
```

**Mental Model:** TCP is a "reliable pipe"—data comes out in order. UDP is "fire and forget messaging"—you control everything.

---

## **Part 2: Advanced TCP/IP**

### **4. Explain TCP Congestion Control. How does it prevent network collapse?**

**Expert Explanation:**

TCP prevents overwhelming the network using **four algorithms**:

**1. Slow Start**
- Begins with `cwnd` (congestion window) = 1 MSS (Maximum Segment Size)
- Doubles every RTT: 1 → 2 → 4 → 8 → 16...
- **Exponential growth** until `ssthresh` (slow start threshold) reached

**2. Congestion Avoidance**
- After `ssthresh`, switches to **linear growth** (+1 MSS per RTT)
- Conservative increase to probe for available bandwidth

**3. Fast Retransmit**
- If 3 duplicate ACKs received → retransmit immediately
- Don't wait for timeout (saves ~200ms)

**4. Fast Recovery**
- After fast retransmit, set `ssthresh` = `cwnd / 2`
- Set `cwnd` = `ssthresh + 3`
- Avoid dropping back to slow start

**Visualizing the sawtooth pattern:**
```
cwnd
 |     /\      /\      /\
 |    /  \    /  \    /  \
 |   /    \  /    \  /    \
 |  /      \/      \/      \
 |___________________________ time
     ↑packet loss (congestion detected)
```

**Modern variants:**
- **TCP Cubic** (Linux default): More aggressive bandwidth probing
- **TCP BBR** (Google): Measures bottleneck bandwidth and RTT directly
- **Why it matters**: BBR achieves 2-25x higher throughput on lossy networks

**C implementation insight:**
```c
// Simplified congestion window update
if (in_slow_start) {
    cwnd += mss;  // Exponential growth
} else {
    cwnd += (mss * mss) / cwnd;  // Linear growth (~1 MSS per RTT)
}

// On packet loss
ssthresh = cwnd / 2;
cwnd = 1;  // Back to slow start
```

**Mental Model:** TCP is constantly **probing** for available bandwidth—increase until loss occurs, back off, repeat.

---

### **5. What is TCP Head-of-Line Blocking? How does HTTP/2 and HTTP/3 address this?**

**Deep Dive:**

**Problem: HTTP/1.1 + TCP**
- Single TCP connection serializes requests
- If packet 5 is lost, packets 6-10 must wait (TCP guarantees order)
- Browser opens 6-8 parallel connections to mitigate

**HTTP/2 Solution (Multiplexing over TCP):**
- Single TCP connection, multiple **streams**
- Frames can be interleaved: Stream1-Frame1, Stream2-Frame1, Stream1-Frame2...
- **Still has TCP-level HOL blocking**: Lost packet blocks all streams

**HTTP/3 Solution (QUIC over UDP):**
- Runs over UDP with custom reliability per stream
- Lost packet in stream 1 doesn't block stream 2
- **True multiplexing without HOL blocking**

**Performance Impact:**
```
1% packet loss scenario:
HTTP/1.1: ~2.5s page load
HTTP/2:   ~2.0s (multiplexing helps, TCP HOL hurts)
HTTP/3:   ~1.2s (no HOL blocking)
```

**Code Example (HTTP/3 in Rust with Quinn):**
```rust
use quinn::{Endpoint, ServerConfig};

// Stream independence - packet loss in stream 1 doesn't affect stream 2
async fn handle_request(mut stream: quinn::RecvStream) {
    // Each stream has independent reliability
    let data = stream.read_to_end(1024).await.unwrap();
    // Process independently
}
```

**Mental Model:** HTTP/2 is like multiple conversations on one phone line (TCP)—dropped words block everyone. HTTP/3 is like multiple independent phone lines (QUIC streams).

---

### **6. Explain NAT (Network Address Translation) and its types. Why is it problematic for P2P applications?**

**Comprehensive Answer:**

**NAT Purpose:**
- Maps private IPs (192.168.x.x, 10.x.x.x) to public IP
- Solves IPv4 address exhaustion
- Provides security (hides internal topology)

**NAT Types:**

1. **Full Cone NAT** (most permissive)
   - Maps internal `IP:Port` → external `IP:Port`
   - **Any** external host can send to that external port
   
2. **Restricted Cone NAT**
   - External host must have received packet from internal host first
   - Checks external IP only (any port allowed)

3. **Port-Restricted Cone NAT**
   - External host must match both IP **and** port

4. **Symmetric NAT** (most restrictive)
   - Different external port for each destination
   - Impossible to predict external port

**P2P Problems:**

**Scenario:** Alice (behind NAT A) wants to connect to Bob (behind NAT B)

```
Alice (192.168.1.5:5000) → NAT A → Internet (203.0.113.10:62000)
Bob (10.0.0.8:6000)      → NAT B → Internet (198.51.100.5:48000)
```

**Challenge:** Neither can initiate connection to the other's private IP

**Solutions:**

1. **STUN** (Session Traversal Utilities for NAT)
   - Discovers external IP:Port
   - Works for cone NATs

2. **TURN** (Traversal Using Relays around NAT)
   - Relay server forwards packets
   - Fallback when direct connection impossible

3. **ICE** (Interactive Connectivity Establishment)
   - Tries STUN first, falls back to TURN
   - Used by WebRTC

**Go Implementation (STUN client):**
```go
package main

import (
    "net"
    "github.com/pion/stun"
)

func discoverPublicIP() (net.IP, int, error) {
    conn, err := net.Dial("udp", "stun.l.google.com:19302")
    if err != nil {
        return nil, 0, err
    }
    
    client := stun.NewClient(conn)
    message := stun.MustBuild(stun.TransactionID, stun.BindingRequest)
    
    var xorAddr stun.XORMappedAddress
    client.Do(message, func(res stun.Event) {
        res.Message.Parse(&xorAddr)
    })
    
    return xorAddr.IP, xorAddr.Port, nil
}
```

**Mental Model:** NAT is a gatekeeper—outbound traffic opens temporary doors, but inbound traffic needs those doors pre-opened or a relay.

---

## **Part 3: DNS & Load Balancing**

### **7. How does DNS load balancing work? What are its limitations?**

**Technical Breakdown:**

**DNS Round-Robin:**
```
Query: google.com
Response: 
  142.250.80.46
  172.217.164.46
  142.250.185.78
(rotates order on each query)
```

**How it works:**
1. Authoritative server returns multiple A records
2. Order rotates to distribute load
3. Clients typically use first IP
4. **TTL** controls how long result cached

**Limitations:**

1. **No health checking**
   - DNS returns dead servers
   - Client experiences failure

2. **Caching defeats distribution**
   - Recursive resolvers cache results
   - All users behind resolver hit same server

3. **No geographic awareness** (basic DNS)
   - User in Tokyo might get US server

4. **Coarse-grained**
   - Can't consider server load/capacity

**Modern Solutions:**

**GeoDNS (Latency-based routing):**
- Returns nearest servers based on client location
- AWS Route 53, Cloudflare implement this

**Health-Checked DNS:**
- Only returns healthy backends
- Route 53 performs periodic health checks

**Python example (DNS round-robin simulation):**
```python
import itertools
import socket

class DNSLoadBalancer:
    def __init__(self, servers):
        self.servers = itertools.cycle(servers)
        self.cache = {}
    
    def resolve(self, domain):
        # Simulate TTL-based caching
        if domain in self.cache:
            return self.cache[domain]
        
        # Rotate to next server
        ip = next(self.servers)
        self.cache[domain] = ip
        return ip

# Usage
lb = DNSLoadBalancer(['192.0.2.1', '192.0.2.2', '192.0.2.3'])
print(lb.resolve('api.example.com'))  # 192.0.2.1
print(lb.resolve('api.example.com'))  # 192.0.2.1 (cached)
```

**Mental Model:** DNS load balancing is like handing out business cards with different phone numbers—once someone has the card, they keep calling that number (caching).

---

### **8. Layer 4 vs Layer 7 Load Balancing: When to use each?**

**Critical Distinction:**

**Layer 4 (Transport Layer) Load Balancing:**
- Decisions based on **IP + Port only**
- Doesn't inspect packet payload
- Faster (simple forwarding)
- Examples: HAProxy (TCP mode), AWS NLB

**Layer 7 (Application Layer) Load Balancing:**
- Inspects **HTTP headers, URL path, cookies**
- Content-based routing
- Can modify requests/responses
- Examples: Nginx, HAProxy (HTTP mode), AWS ALB

**Comparison Table:**

| Aspect | Layer 4 | Layer 7 |
|--------|---------|---------|
| **Speed** | ~10-100 µs | ~100-1000 µs |
| **Throughput** | Millions req/s | Hundreds of thousands req/s |
| **Routing** | IP:Port only | URL, headers, cookies |
| **SSL Termination** | No (passthrough) | Yes |
| **WebSocket** | Transparent | Requires special handling |
| **Caching** | No | Yes |

**When to use Layer 4:**
- **Maximum throughput** needed (stock trading, gaming)
- Non-HTTP protocols (databases, custom TCP)
- TLS passthrough (end-to-end encryption)

**When to use Layer 7:**
- **Content-based routing** (`/api/v1` → service1, `/api/v2` → service2)
- A/B testing (route 10% to new backend)
- SSL offloading (decrypt once at LB)
- Request modification (add headers, rewrite URLs)

**Real-world Architecture:**
```
Internet → Layer 7 LB (Nginx) → Layer 4 LB (HAProxy) → Backends
          ↑                      ↑
          SSL termination        Fast forwarding
          Path routing           Health checks
```

**C++ example (Layer 4 simple port forwarding):**
```cpp
#include <sys/socket.h>
#include <netinet/in.h>

// Simplified L4 load balancer
void forward_connection(int client_fd, const char* backend_ip, int backend_port) {
    int backend_fd = socket(AF_INET, SOCK_STREAM, 0);
    
    struct sockaddr_in backend_addr;
    backend_addr.sin_family = AF_INET;
    backend_addr.sin_port = htons(backend_port);
    inet_pton(AF_INET, backend_ip, &backend_addr.sin_addr);
    
    connect(backend_fd, (struct sockaddr*)&backend_addr, sizeof(backend_addr));
    
    // Bidirectional forwarding (simplified)
    char buffer[4096];
    ssize_t n;
    while ((n = recv(client_fd, buffer, sizeof(buffer), 0)) > 0) {
        send(backend_fd, buffer, n, 0);
    }
}
```

**Mental Model:** Layer 4 is like a phone operator connecting calls blindly. Layer 7 is like a receptionist who reads your request and routes you intelligently.

---

## **Part 4: Security & Performance**

### **9. Explain DDoS attacks and mitigation strategies.**

**Attack Taxonomy:**

**1. Volumetric Attacks (consume bandwidth)**
- **UDP Flood**: Spam UDP packets to overwhelm network
- **DNS Amplification**: Send DNS queries with spoofed source IP
  - Attacker sends 64 bytes → Victim receives 4000 bytes (60x amplification)
- **Mitigation**: Traffic scrubbing, rate limiting, Anycast

**2. Protocol Attacks (exhaust server resources)**
- **SYN Flood**: Send TCP SYN, never complete handshake
  - Fills server's connection queue
- **Ping of Death**: Oversized ping packets crash systems
- **Mitigation**: SYN cookies, connection rate limits

**3. Application Layer Attacks (exhaust application resources)**
- **HTTP Flood**: Legitimate-looking HTTP requests
  - Target expensive endpoints (database queries)
- **Slowloris**: Open connections, send partial requests slowly
- **Mitigation**: Rate limiting per IP, CAPTCHA, traffic analysis

**Advanced Mitigation Techniques:**

**1. SYN Cookies (elegant defense):**
```
Normal TCP:
1. Client sends SYN
2. Server allocates memory for connection
3. Attack: Memory exhausted

SYN Cookies:
1. Client sends SYN
2. Server calculates cookie = hash(src_ip, src_port, secret)
3. Server sends SYN-ACK with cookie as sequence number
4. NO memory allocated until ACK received
5. On ACK, verify cookie matches
```

**2. Anycast Routing:**
- Same IP advertised from multiple locations
- Traffic routed to nearest location
- Distributes attack geographically

**3. Rate Limiting (Token Bucket Algorithm):**

```rust
use std::time::{Duration, Instant};

struct RateLimiter {
    tokens: f64,
    capacity: f64,
    refill_rate: f64,  // tokens per second
    last_refill: Instant,
}

impl RateLimiter {
    fn allow_request(&mut self) -> bool {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_refill).as_secs_f64();
        
        // Refill tokens
        self.tokens = (self.tokens + elapsed * self.refill_rate).min(self.capacity);
        self.last_refill = now;
        
        if self.tokens >= 1.0 {
            self.tokens -= 1.0;
            true
        } else {
            false  // Rate limit exceeded
        }
    }
}

// Usage: Allow 100 requests per second, burst of 200
let mut limiter = RateLimiter {
    tokens: 200.0,
    capacity: 200.0,
    refill_rate: 100.0,
    last_refill: Instant::now(),
};
```

**Real-world Defense Stack:**
```
Layer 1: CDN/Anycast (Cloudflare, Akamai)
         ↓ Filters 95% of volumetric attacks
Layer 2: Edge rate limiting
         ↓ Blocks suspicious IPs/patterns
Layer 3: Application firewall (WAF)
         ↓ Inspects HTTP for attack patterns
Layer 4: Application (final defense)
         ↓ Graceful degradation
```

**Mental Model:** DDoS is like flooding a restaurant with fake reservations. Mitigation is multi-layered: bouncer at door (edge filtering), reservations system (rate limiting), priority seating (QoS for legitimate users).

---

### **10. What is the difference between symmetric and asymmetric encryption? When is each used in network protocols?**

**Fundamental Difference:**

**Symmetric Encryption:**
- **Same key** for encryption and decryption
- Fast (hardware acceleration common)
- Key distribution problem
- Examples: AES, ChaCha20

**Asymmetric Encryption:**
- **Public/private key pair**
- Slow (1000x slower than symmetric)
- Solves key distribution
- Examples: RSA, Elliptic Curve (ECDSA, Ed25519)

**Real-World Usage (TLS Handshake):**

```
1. [Asymmetric] Client → Server: 
   "Here are my supported ciphers"

2. [Asymmetric] Server → Client:
   "Here's my certificate (includes public key)"

3. [Asymmetric] Client generates random "pre-master secret"
   Encrypts with server's public key → Server

4. [Both derive] Client and Server independently compute:
   master_secret = PRF(pre-master secret, nonces)
   session_keys = derive(master_secret)

5. [Symmetric] All subsequent traffic encrypted with AES using session_keys
```

**Why this hybrid approach?**
- Asymmetric solves key exchange (no shared secret needed beforehand)
- Symmetric provides fast bulk encryption

**Performance Comparison:**
```
AES-256-GCM:       ~1-5 GB/s (with AES-NI)
RSA-2048 encrypt:  ~10 KB/s
RSA-2048 decrypt:  ~500 bytes/s

Encrypting 1 MB:
AES:  ~1 ms
RSA:  ~100,000 ms (unusable for bulk data)
```

**Python Implementation (Hybrid Encryption):**

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
import os

# Generate RSA key pair
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

def hybrid_encrypt(data: bytes, recipient_public_key):
    # Generate random symmetric key (AES-256)
    aes_key = os.urandom(32)
    iv = os.urandom(16)
    
    # Encrypt data with AES (symmetric - fast)
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    
    # Encrypt AES key with RSA (asymmetric - slow but small payload)
    encrypted_key = recipient_public_key.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    
    return encrypted_key, iv, ciphertext, encryptor.tag

# Usage
plaintext = b"Secret message" * 1000  # Large data
enc_key, iv, ciphertext, tag = hybrid_encrypt(plaintext, public_key)

# Only the small AES key was encrypted with slow RSA
# Bulk data encrypted with fast AES
```

**Mental Model:** Asymmetric is like a lockbox with a public slot—anyone can drop secrets in, only you can open it. Symmetric is like a shared safe—both parties need the combination, but accessing it is instant.

---

## **Part 5: Modern Protocols & Challenges**

### **11. Explain WebSockets vs HTTP. When would you use WebSockets?**

**Core Difference:**

**HTTP:**
- **Request-response** model
- Client initiates every interaction
- New connection overhead for each request (HTTP/1.1) or stream (HTTP/2)

**WebSocket:**
- **Full-duplex** persistent connection
- Server can push data without client request
- Lower overhead after initial handshake

**WebSocket Handshake (Upgrade from HTTP):**
```
Client → Server:
GET /chat HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==

Server → Client:
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=

[Now both sides can send messages anytime]
```

**When to Use WebSockets:**

1. **Real-time bidirectional data** (chat, multiplayer games, collaborative editing)
2. **High-frequency updates** (live dashboards, stock tickers)
3. **Server-initiated events** (notifications, alerts)

**When NOT to use:**
- Simple request-response (RESTful APIs)
- Infrequent updates (HTTP long-polling sufficient)
- Need HTTP caching/proxying

**Performance Comparison:**
```
HTTP Polling (1 message/second):
- 60 requests/minute
- ~3 KB overhead/request (headers)
- Total: ~180 KB/minute overhead

WebSocket:
- 1 initial handshake
- ~2 bytes overhead per message
- Total: ~120 bytes/minute overhead (1500x less!)
```

**Rust WebSocket Server (Tokio + Tungstenite):**

```rust
use tokio::net::{TcpListener, TcpStream};
use tokio_tungstenite::{accept_async, WebSocketStream};
use futures_util::{StreamExt, SinkExt};

async fn handle_connection(stream: TcpStream) {
    let mut ws_stream = accept_async(stream).await.unwrap();
    
    // Bidirectional communication
    while let Some(msg) = ws_stream.next().await {
        let msg = msg.unwrap();
        
        if msg.is_text() {
            let response = format!("Echo: {}", msg.to_text().unwrap());
            ws_stream.send(response.into()).await.unwrap();
        }
    }
}

#[tokio::main]
async fn main() {
    let listener = TcpListener::bind("127.0.0.1:8080").await.unwrap();
    
    while let Ok((stream, _)) = listener.accept().await {
        tokio::spawn(handle_connection(stream));
    }
}
```

**Scaling Challenges:**
- Each WebSocket = persistent connection (C10K problem)
- Need event-driven architecture (epoll, kqueue, io_uring)
- Horizontal scaling requires sticky sessions or pub/sub

**Mental Model:** HTTP is like mailing letters—you send, wait for response. WebSocket is like a phone call—ongoing conversation, either side can speak.

---

### **12. What is HTTP/3 and why does it matter? How does QUIC work?**

**Revolutionary Shift:**

**HTTP/1.1 → HTTP/2 → HTTP/3**
- HTTP/1.1: Multiple TCP connections, head-of-line blocking
- HTTP/2: Multiplexing over single TCP connection (still TCP HOL blocking)
- HTTP/3: QUIC over UDP (no HOL blocking, faster connection establishment)

**QUIC (Quick UDP Internet Connections) Features:**

1. **0-RTT Connection Establishment**
   ```
   Traditional TLS 1.3 over TCP: 2-3 RTT
   - TCP handshake: 1 RTT
   - TLS handshake: 1-2 RTT
   
   QUIC (resumption): 0 RTT
   - Client sends encrypted data immediately with cached credentials
   ```

2. **Stream-Level Reliability**
   - Lost packet in stream 1 doesn't block stream 2
   - Each stream has independent flow control

3. **Connection Migration**
   - Connection tied to ID, not IP
   - Seamless WiFi → 4G handoff

4. **Integrated Encryption**
   - Mandatory TLS 1.3
   - Encrypts almost all packet metadata

**Frame Structure:**
```
UDP Packet:
[IP Header]
[UDP Header: 8 bytes]
[QUIC Header: Long (variable) or Short (1+ bytes)]
[QUIC Frames: STREAM, ACK, CRYPTO, etc.]
[Encrypted Payload]
```

**Performance in Lossy Networks:**
```
1% packet loss:
TCP:     Page load ~3.5s (retransmits block everything)
QUIC:    Page load ~1.8s (independent stream recovery)

Mobile network (5% loss):
TCP:     ~10s
QUIC:    ~3s
```

**Go QUIC Server (using quic-go):**

```go
package main

import (
    "crypto/tls"
    "github.com/quic-go/quic-go/http3"
    "net/http"
)

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("Hello from HTTP/3!"))
    })
    
    server := &http3.Server{
        Addr:    ":443",
        Handler: mux,
        TLSConfig: &tls.Config{
            // Certificate setup
        },
    }
    
    // Serves HTTP/3 over QUIC
    server.ListenAndServe()
}
```

**Adoption Challenges:**

- UDP blocked by some firewalls/middleboxes
- Requires client library changes
- Loss detection algorithms more complex

**Current Adoption (2025):**

- Google services: 100%
- Meta: ~75%
- Cloudflare: Enabled for all customers
- Overall web traffic: ~25-30%

**Mental Model:** QUIC is like having multiple independent conversations over walkie-talkies (UDP datagrams)—one person stuttering doesn't make everyone else wait.

---

## **Part 6: Coding Challenges**

### **13. Implement a simple HTTP server from scratch (TCP sockets)**

**C Implementation (Educational - Production would use libraries):**
