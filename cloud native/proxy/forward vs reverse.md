## Proxy Concepts: Forward vs Reverse

**One-line:** A forward proxy acts on behalf of the **client**; a reverse proxy acts on behalf of the **server**.

---

### The Core Mental Model

```
FORWARD PROXY                          REVERSE PROXY

Client → [Proxy] → Internet            Internet → [Proxy] → Server(s)
         ↑                                          ↑
   client controls it                      server owner controls it
   server doesn't know real client         client doesn't know real server
```

**Analogy:**
- **Forward proxy** = a secretary who makes calls *for you*. The recipient talks to the secretary, not you. You're anonymous.
- **Reverse proxy** = a receptionist at a company. You call the company number (proxy), and the receptionist routes you to the right department (server). You never dial the actual engineer's desk.

---

### Who Knows What?

```

| Aspect | Forward Proxy | Reverse Proxy |
|---|---|---|
| Configured by | Client / client's org | Server owner |
| Hides | Client's identity | Server topology |
| Client awareness | Client knows it's using a proxy | Client is unaware (thinks it's the origin) |
| Use case | Censorship bypass, egress control, caching | Load balancing, TLS termination, WAF, rate limiting |

```

---

### Real-World Usage

**Forward Proxy** — used for:
- Corporate egress filtering (Squid, Zscaler)
- VPNs / anonymization (Tor is a chain of forward proxies)
- Caching outbound requests

**Reverse Proxy** — used for:
- Load balancing (NGINX, HAProxy, Envoy)
- TLS termination (offload TLS before hitting app servers)
- Web Application Firewall (Cloudflare, AWS WAF)
- API gateway / rate limiting
- Blue-green / canary deployments

---

### Where This Matters in Systems Work

```
Client
  │
  ▼
[Reverse Proxy: NGINX/Envoy]  ← TLS termination, rate limit, auth headers
  │
  ├──▶ Service A (gRPC)
  ├──▶ Service B (HTTP)
  └──▶ Service C (WebSocket)
```

In Kubernetes this is your **Ingress Controller** (reverse proxy). In a service mesh like Istio, the **sidecar (Envoy)** acts as *both*: a reverse proxy for inbound traffic and a forward proxy for outbound traffic from the pod.

---

### Quick Security Notes
- **Forward proxy**: can be abused for data exfiltration — always enforce egress allowlists
- **Reverse proxy**: must sanitize/strip internal headers (`X-Forwarded-For` spoofing is a common attack vector); never leak backend server info in error responses

---

**TL;DR:** Client-side problem → forward proxy. Server-side problem → reverse proxy. In production you almost always care about reverse proxies.

The core difference lies in **who the client thinks it is talking to**, and **which side of the connection benefits from the proxy**.

Here is the clearest way to separate them:

### 1. Forward Proxy (The "Client Shield")
**Position:** Sits in front of the **client** (you).
**Flow:** `You → Forward Proxy → Internet → Website`

- **Who uses it?** End users (employees in an office, you at home using a VPN).
- **What does the website see?** The IP address of the **proxy**, not your IP.
- **Primary Use Case:** **Outbound traffic control.**

**Real-world examples:**
- **Bypassing Geo-blocks:** You are in India, but you use a Forward Proxy in the US to watch US Netflix. Netflix thinks the request came from the US proxy.
- **Corporate Firewalls:** Your office IT blocks access to Facebook. The Forward Proxy intercepts your request to `facebook.com` and says "Access Denied."
- **Anonymity:** Hiding your home IP address from the websites you visit.

### 2. Reverse Proxy (The "Server Shield")
**Position:** Sits in front of the **server** (website/application).
**Flow:** `You → Internet → Reverse Proxy → Web Server`

- **Who uses it?** Website owners (Google, Amazon, any large app).
- **What does the client (you) think is happening?** You think you are talking directly to `amazon.com`. You have **no idea** a reverse proxy exists.
- **Primary Use Case:** **Inbound traffic management and security.**

**Real-world examples:**
- **Load Balancing:** You type `amazon.com`. A Reverse Proxy (like NGINX) receives the request and decides which of the 5,000 backend servers is least busy to handle it.
- **SSL Termination:** The Reverse Proxy handles all the complicated encryption/decryption so the backend servers can focus on just serving content faster.
- **Caching:** The Reverse Proxy saves a copy of the homepage image. When the next 1,000 people visit, it serves the image itself without bothering the main server.

### Comparison Table: The Key Check

```
| Feature | Forward Proxy | Reverse Proxy |
| :--- | :--- | :--- |
| **Client Awareness** | **Yes.** You must configure your browser/phone to use it. | **No.** You think you're on the real website. |
| **Protects** | The **Client** (hides identity). | The **Server** (hides infrastructure). |
| **Controls** | **Outgoing** traffic (what users can see). | **Incoming** traffic (how users access the site). |
| **IP Address Hidden** | Client's real IP hidden from **Website**. | Server's real IP hidden from **Hacker/User**. |
| **Analogy** | A **Doorman** for your apartment building filtering who leaves. | A **Receptionist** for an office filtering who gets in. |

```

### The "Same Software" Confusion
It is very common to get confused because the **software** used for both is often the exact same tool (e.g., **NGINX**, **HAProxy**, **Apache**). The difference is purely in the **configuration file** and **intent**:

- **NGINX config:** `proxy_pass http://backend_server;` (This is **Reverse**).
- **Browser Settings:** `HTTP Proxy: 192.168.1.1:8080` (This is **Forward**).