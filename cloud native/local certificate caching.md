# Local Certificate Caching: Comprehensive Security-First Guide

Certificate caching reduces TLS handshake overhead and external CA dependencies but introduces attack surfaces around staleness, revocation bypass, and privilege escalation. This guide covers OS-level trust stores, application-specific caches (OpenSSL, Go crypto/x509, Rust rustls), OCSP/CRL mechanics, cache poisoning threats, and production patterns for high-throughput mTLS environments. You'll build reproducible PoCs, threat models, and rollout strategies for Kubernetes ingress, service mesh sidecars, and edge proxies.

**Key trade-offs:** Performance (reduced handshake latency, CA outage tolerance) vs. security (revocation check bypass, stale cert acceptance, cache poisoning). **Actionable outcome:** Implement tiered caching with automatic rotation, OCSP stapling, and audit trails for compliance-heavy environments.

---

## 1. Foundational Concepts & Threat Model

### 1.1 What Gets Cached & Where

```
┌─────────────────────────────────────────────────────────────┐
│  Certificate Caching Layers                                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ OS Trust Store (System-wide)                        │   │
│  │ - /etc/ssl/certs (Linux), Keychain (macOS), CertMgr │   │
│  │ - Root CAs, intermediate CAs                        │   │
│  │ - Shared by all apps unless overridden              │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │ TLS Library Session Cache (In-Memory)              │   │
│  │ - OpenSSL: SSL_CTX session cache                   │   │
│  │ - Go: tls.Config.ClientSessionCache                │   │
│  │ - Rust rustls: ClientSessionMemoryCache            │   │
│  │ - Stores: session tickets, PSK, negotiated params  │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │ Application Certificate Cache (Disk/DB)            │   │
│  │ - Intermediate CA certs (AIA fetching)             │   │
│  │ - OCSP responses (stapled or fetched)              │   │
│  │ - CRL files (if used)                              │   │
│  │ - Custom: Redis, etcd, local files                 │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │ Service Mesh / Ingress Cache (Envoy, NGINX)        │   │
│  │ - Client certs for mTLS (workload identity)        │   │
│  │ - SPIFFE SVID bundles                              │   │
│  │ - Auto-rotation via cert-manager, SPIRE            │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**What's cached:**
- **Root/Intermediate CA certificates:** Trust anchors, chain builders
- **Leaf certificates:** Server certs (rarely cached except in controlled envs)
- **TLS session data:** Session IDs, tickets, PSKs (ephemeral, not certs themselves)
- **OCSP responses:** Revocation status (timestamped, short TTL)
- **CRLs:** Certificate Revocation Lists (large, infrequent updates)

### 1.2 Threat Model

| Threat | Impact | Mitigation |
|--------|--------|-----------|
| **Stale certificate acceptance** | Use revoked cert (compromised key) | OCSP stapling, CRL checks, short cache TTL |
| **Cache poisoning** | Inject malicious CA, MITM | Signed OCSP, authenticated cache updates, integrity checks |
| **Privilege escalation** | Untrusted process writes to cache | File perms (600/400), SELinux/AppArmor, namespace isolation |
| **Revocation bypass** | Attacker forces offline mode | Must-staple OCSP, fail-closed policies, monitoring |
| **Memory exhaustion** | DoS via unbounded cache | LRU eviction, memory limits (cgroup), rate limiting |
| **Side-channel leakage** | Timing attacks on cache hits | Constant-time lookups (hard in practice), cache obfuscation |

**Security assumptions:**
- Trust store integrity (OS package signing, immutable rootfs)
- Clock sync for OCSP/CRL freshness checks (NTP/chrony hardened)
- Secure key material storage (HSM, TPM, encrypted disk)

---

## 2. OS-Level Trust Store Mechanics

### 2.1 Linux (/etc/ssl/certs, ca-certificates)

```bash
# Inspect system CA bundle
ls -lh /etc/ssl/certs/ca-certificates.crt
openssl crl2pkcs7 -nocrl -certfile /etc/ssl/certs/ca-certificates.crt | \
  openssl pkcs7 -print_certs -text -noout | grep -E "Subject:|Not After"

# Add custom CA (Debian/Ubuntu)
sudo cp my-internal-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
# Verify
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt server.crt

# RHEL/CentOS
sudo cp my-internal-ca.crt /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust extract

# Check trust anchor hashes (used by OpenSSL for quick lookups)
ls -lh /etc/ssl/certs/ | grep "^l" | head -5
# Example: 3513523f.0 -> DigiCert_Global_Root_CA.pem (hash collision resistant)
```

**Security notes:**
- **Immutable rootfs:** Mount `/etc/ssl/certs` read-only, update via package manager only
- **Audit:** `inotify` or `auditd` on trust store modifications
- **Container isolation:** Bind-mount minimal CA bundle (scratch/distroless), not full OS store

### 2.2 Windows Certificate Store

```powershell
# List trusted root CAs
Get-ChildItem Cert:\LocalMachine\Root | Select-Object Subject, NotAfter, Thumbprint

# Export CA bundle for application use
$certs = Get-ChildItem Cert:\LocalMachine\Root
$certs | Export-Certificate -FilePath C:\ca-bundle.crt -Type CERT

# Import custom CA (requires admin)
Import-Certificate -FilePath internal-ca.crt -CertStoreLocation Cert:\LocalMachine\Root

# Verify with certutil
certutil -verify -urlfetch server.crt
```

**Group Policy enforcement:**
- Disable user-added CAs: `Computer Configuration > Windows Settings > Security Settings > Public Key Policies > Certificate Path Validation Settings`
- Pin specific CAs for critical apps via HPKP-like mechanisms (deprecated in browsers, still useful in enterprise)

### 2.3 macOS Keychain

```bash
# System keychain (requires sudo)
sudo security find-certificate -a -p /Library/Keychains/System.keychain > system-cas.pem

# Add CA to system keychain
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain internal-ca.crt

# Verify trust settings
security verify-cert -c server.crt -p ssl -L -l

# Programmatic access (Swift/ObjC Security framework)
# SecTrustCreateWithCertificates, SecTrustEvaluate
```

---

## 3. Application-Level Certificate Caching

### 3.1 OpenSSL Session Cache

**Shared memory cache (multi-process servers):**

```c
// server.c
#include <openssl/ssl.h>
#include <openssl/err.h>

SSL_CTX *ctx = SSL_CTX_new(TLS_server_method());

// Internal cache (single process, default)
SSL_CTX_sess_set_cache_size(ctx, 1024);
SSL_CTX_set_timeout(ctx, 300); // 5 min session TTL

// External cache (Redis, shared mem) - callbacks
SSL_CTX_sess_set_new_cb(ctx, session_new_cb);
SSL_CTX_sess_set_get_cb(ctx, session_get_cb);
SSL_CTX_sess_set_remove_cb(ctx, session_remove_cb);

// Disable client-side caching for debugging
SSL_CTX_set_session_cache_mode(ctx, SSL_SESS_CACHE_OFF);

// Cert chain verification cache (AIA fetch)
X509_STORE *store = SSL_CTX_get_cert_store(ctx);
X509_STORE_set_flags(store, X509_V_FLAG_CRL_CHECK | X509_V_FLAG_CRL_CHECK_ALL);
```

**External cache implementation (pseudocode):**

```c
int session_new_cb(SSL *ssl, SSL_SESSION *sess) {
    unsigned char *data;
    int len = i2d_SSL_SESSION(sess, &data);
    // Store to Redis: SET sess:<id> <data> EX 300
    redis_setex(session_id, data, len, 300);
    OPENSSL_free(data);
    return 1; // Success
}

SSL_SESSION *session_get_cb(SSL *ssl, const unsigned char *id, int len, int *copy) {
    unsigned char *data = redis_get(id);
    if (!data) return NULL;
    SSL_SESSION *sess = d2i_SSL_SESSION(NULL, &data, redis_len);
    *copy = 0; // OpenSSL takes ownership
    return sess;
}
```

**Build & test:**

```bash
# Compile
gcc -o tlsserver server.c -lssl -lcrypto -Wall -O2
# Run with session cache
./tlsserver --cert server.crt --key server.key --port 8443

# Client test (reuse session)
openssl s_client -connect localhost:8443 -reconnect -sess_out session.pem
openssl s_client -connect localhost:8443 -sess_in session.pem
# Observe "Reused, TLSv1.3" in output
```

### 3.2 Go crypto/tls ClientSessionCache

```go
// cache.go
package main

import (
    "crypto/tls"
    "fmt"
    "net/http"
    "sync"
    "time"
)

// In-memory LRU cache (production: use groupcache, redis)
type SessionCache struct {
    mu    sync.RWMutex
    cache map[string]*tls.ClientSessionState
    maxEntries int
}

func NewSessionCache(max int) *SessionCache {
    return &SessionCache{cache: make(map[string]*tls.ClientSessionState), maxEntries: max}
}

func (c *SessionCache) Get(key string) (*tls.ClientSessionState, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    sess, ok := c.cache[key]
    return sess, ok
}

func (c *SessionCache) Put(key string, sess *tls.ClientSessionState) {
    c.mu.Lock()
    defer c.mu.Unlock()
    if len(c.cache) >= c.maxEntries {
        // Simple eviction: delete random entry (use LRU in prod)
        for k := range c.cache {
            delete(c.cache, k)
            break
        }
    }
    c.cache[key] = sess
}

func main() {
    cache := NewSessionCache(128)
    
    client := &http.Client{
        Transport: &http.Transport{
            TLSClientConfig: &tls.Config{
                ClientSessionCache: cache,
                MinVersion: tls.VersionTLS12,
                // Custom root CA pool
                // RootCAs: loadCustomCAs(),
            },
        },
    }
    
    // First request: full handshake
    resp1, _ := client.Get("https://example.com")
    resp1.Body.Close()
    
    // Second request: session resumption (0-RTT if TLS 1.3)
    resp2, _ := client.Get("https://example.com")
    resp2.Body.Close()
    
    fmt.Printf("Cache size: %d\n", len(cache.cache))
}
```

**Cert verification cache (x509.CertPool):**

```go
// Custom verification with cache
func loadCertPool() *x509.CertPool {
    pool := x509.NewCertPool()
    caCert, _ := os.ReadFile("/etc/ssl/certs/ca-bundle.crt")
    pool.AppendCertsFromPEM(caCert)
    return pool
}

tlsConfig := &tls.Config{
    RootCAs: loadCertPool(), // Cached in memory, reused across conns
    VerifyPeerCertificate: func(rawCerts [][]byte, verifiedChains [][]*x509.Certificate) error {
        // Custom revocation check (OCSP, CRL)
        return checkRevocation(verifiedChains[0])
    },
}
```

**Test with observability:**

```bash
# Build
go build -o client cache.go

# Trace TLS handshakes
GODEBUG=x509roots=1,tls13=1 ./client 2>&1 | grep "Handshake\|Session"

# Benchmark session reuse
go test -bench=. -benchmem -cpuprofile=cpu.prof
go tool pprof -http=:8080 cpu.prof
```

### 3.3 Rust rustls ClientSessionMemoryCache

```rust
// Cargo.toml
// [dependencies]
// rustls = "0.23"
// tokio = { version = "1", features = ["full"] }
// tokio-rustls = "0.26"

use rustls::{ClientConfig, ClientConnection, RootCertStore};
use rustls::client::ClientSessionStore;
use std::sync::Arc;
use tokio::net::TcpStream;
use tokio_rustls::TlsConnector;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load root CAs
    let mut root_store = RootCertStore::empty();
    root_store.add_parsable_certificates(
        rustls_native_certs::load_native_certs()?.into_iter().map(|c| c.0)
    );
    
    // Client config with session cache
    let mut config = ClientConfig::builder()
        .with_root_certificates(root_store)
        .with_no_client_auth();
    
    // Enable session resumption (default in rustls 0.23+)
    // config.resumption = rustls::client::Resumption::in_memory_sessions(256);
    
    let connector = TlsConnector::from(Arc::new(config));
    
    // First connection: full handshake
    let stream = TcpStream::connect("example.com:443").await?;
    let domain = "example.com".try_into()?;
    let tls_stream = connector.connect(domain, stream).await?;
    drop(tls_stream);
    
    // Second connection: session reuse
    let stream = TcpStream::connect("example.com:443").await?;
    let tls_stream = connector.connect(domain, stream).await?;
    // Check connection.peer_certificates() for chain
    
    Ok(())
}
```

**Custom persistent cache:**

```rust
use rustls::client::{ClientSessionStore, ClientSessionValue};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

struct RedisSessionStore {
    client: Arc<Mutex<redis::Client>>,
}

impl ClientSessionStore for RedisSessionStore {
    fn put(&self, key: Vec<u8>, value: Vec<u8>) -> bool {
        let mut conn = self.client.lock().unwrap().get_connection().unwrap();
        redis::cmd("SETEX")
            .arg(&key)
            .arg(300) // 5 min TTL
            .arg(&value)
            .query(&mut conn)
            .is_ok()
    }
    
    fn get(&self, key: &[u8]) -> Option<Vec<u8>> {
        let mut conn = self.client.lock().unwrap().get_connection().unwrap();
        redis::cmd("GET").arg(key).query(&mut conn).ok()
    }
    
    // Implement take() and remaining methods
}
```

**Fuzz testing session cache:**

```rust
// fuzz/fuzz_targets/session_cache.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if data.len() < 32 { return; }
    let key = &data[..32];
    let value = &data[32..];
    
    let store = MySessionStore::new();
    store.put(key.to_vec(), value.to_vec());
    let retrieved = store.get(key);
    assert_eq!(retrieved.as_deref(), Some(value));
});
```

```bash
# Run fuzzer
cargo fuzz run session_cache -- -max_total_time=300
```

---

## 4. OCSP Stapling & CRL Caching

### 4.1 OCSP Response Cache

**Fetch & cache OCSP response:**

```bash
#!/bin/bash
# fetch-ocsp.sh

CERT="$1"
ISSUER_CERT="$2"
OCSP_CACHE_DIR="/var/cache/ocsp"

# Extract OCSP responder URL
OCSP_URL=$(openssl x509 -in "$CERT" -noout -ocsp_uri)

# Fetch OCSP response
openssl ocsp \
    -issuer "$ISSUER_CERT" \
    -cert "$CERT" \
    -url "$OCSP_URL" \
    -respout "$OCSP_CACHE_DIR/$(sha256sum "$CERT" | cut -d' ' -f1).ocsp" \
    -noverify # Verify response with -VAfile in production

# Check response validity
openssl ocsp \
    -respin "$OCSP_CACHE_DIR/$(sha256sum "$CERT" | cut -d' ' -f1).ocsp" \
    -text | grep -E "This Update|Next Update|Cert Status"
```

**Systemd timer for auto-refresh:**

```ini
# /etc/systemd/system/ocsp-refresh.service
[Unit]
Description=Refresh OCSP responses

[Service]
Type=oneshot
ExecStart=/usr/local/bin/fetch-ocsp.sh /etc/ssl/certs/server.crt /etc/ssl/certs/intermediate-ca.crt
User=ocsp-cache
PrivateTmp=yes
NoNewPrivileges=yes
```

```ini
# /etc/systemd/system/ocsp-refresh.timer
[Unit]
Description=Refresh OCSP every hour

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now ocsp-refresh.timer
```

**NGINX OCSP stapling config:**

```nginx
server {
    listen 443 ssl http2;
    
    ssl_certificate /etc/ssl/certs/server.crt;
    ssl_certificate_key /etc/ssl/private/server.key;
    ssl_trusted_certificate /etc/ssl/certs/intermediate-ca.crt;
    
    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_stapling_file /var/cache/ocsp/server.ocsp; # Pre-fetched response
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Force OCSP (fail closed if response unavailable)
    # ssl_stapling_responder_timeout 2s; # Default 5s
}
```

**Verify stapling:**

```bash
echo | openssl s_client -connect example.com:443 -status -tlsextdebug 2>&1 | grep -A 20 "OCSP"
# Should show "OCSP Response Status: successful (0x0)"
```

### 4.2 CRL Caching Strategy

**Download & validate CRL:**

```bash
# Extract CRL Distribution Point
openssl x509 -in server.crt -noout -text | grep -A 4 "CRL Distribution"

# Download CRL
wget -O /var/cache/crl/ca.crl http://crl.example.com/ca.crl

# Verify CRL signature
openssl crl -in /var/cache/crl/ca.crl -CAfile /etc/ssl/certs/ca.crt -noout

# Check CRL contents
openssl crl -in /var/cache/crl/ca.crl -text -noout | grep -E "Last Update|Next Update|Serial"

# Validate cert against CRL
openssl verify -crl_check -CRLfile /var/cache/crl/ca.crl -CAfile /etc/ssl/certs/ca.crt server.crt
```

**Automated CRL refresh (Python):**

```python
#!/usr/bin/env python3
# crl-sync.py

import requests
import subprocess
import time
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timezone

CRL_URL = "http://crl.example.com/ca.crl"
CRL_PATH = "/var/cache/crl/ca.crl"
CA_CERT_PATH = "/etc/ssl/certs/ca.crt"

def fetch_crl():
    resp = requests.get(CRL_URL, timeout=10)
    resp.raise_for_status()
    
    crl = x509.load_der_x509_crl(resp.content, default_backend())
    
    # Validate freshness
    now = datetime.now(timezone.utc)
    if crl.next_update_utc < now:
        raise ValueError(f"CRL expired: next_update={crl.next_update_utc}")
    
    # Write to cache
    with open(CRL_PATH, 'wb') as f:
        f.write(resp.content)
    
    print(f"CRL updated: next_update={crl.next_update_utc}, revoked={len(list(crl))}")

if __name__ == "__main__":
    while True:
        try:
            fetch_crl()
        except Exception as e:
            print(f"CRL fetch failed: {e}")
        time.sleep(3600)  # Hourly
```

**Run as systemd service:**

```ini
[Unit]
Description=CRL synchronization daemon

[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/crl-sync.py
Restart=always
User=crl-sync
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

---

## 5. Kubernetes & Service Mesh Certificate Caching

### 5.1 cert-manager + trust-manager

**Architecture:**

```
┌────────────────────────────────────────────────────────┐
│ Kubernetes Cluster                                     │
│                                                        │
│  ┌──────────────────┐      ┌─────────────────────┐   │
│  │ cert-manager     │──────>│ Issuer (Let's Enc,  │   │
│  │ (Certificate CR) │      │ Vault, internal CA) │   │
│  └────────┬─────────┘      └─────────────────────┘   │
│           │ renews                                     │
│           v                                            │
│  ┌──────────────────┐      ┌─────────────────────┐   │
│  │ Secret (TLS)     │      │ trust-manager       │   │
│  │ - tls.crt        │<─────│ (Bundle CR)         │   │
│  │ - tls.key        │      │ Syncs CA bundle to  │   │
│  └────────┬─────────┘      │ all namespaces      │   │
│           │                └─────────────────────┘   │
│           v mount                                      │
│  ┌──────────────────┐                                 │
│  │ Pod (nginx)      │                                 │
│  │ /etc/nginx/certs/│                                 │
│  └──────────────────┘                                 │
└────────────────────────────────────────────────────────┘
```

**Deploy cert-manager:**

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Create internal CA issuer
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: ca-key-pair
  namespace: cert-manager
data:
  tls.crt: $(base64 -w0 < ca.crt)
  tls.key: $(base64 -w0 < ca.key)
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: internal-ca
spec:
  ca:
    secretName: ca-key-pair
EOF

# Request certificate
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: app-tls
  namespace: default
spec:
  secretName: app-tls-secret
  issuerRef:
    name: internal-ca
    kind: ClusterIssuer
  dnsNames:
    - app.example.com
  duration: 2160h  # 90 days
  renewBefore: 360h  # Renew 15 days before expiry
EOF

# Verify cert
kubectl get certificate app-tls -o yaml
kubectl get secret app-tls-secret -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout
```

**trust-manager for CA bundle distribution:**

```bash
# Install trust-manager
helm repo add jetstack https://charts.jetstack.io
helm install trust-manager jetstack/trust-manager -n cert-manager

# Create CA bundle
cat <<EOF | kubectl apply -f -
apiVersion: trust.cert-manager.io/v1alpha1
kind: Bundle
metadata:
  name: internal-ca-bundle
spec:
  sources:
    - secret:
        name: ca-key-pair
        key: tls.crt
  target:
    configMap:
      key: ca-bundle.crt
    namespaceSelector:
      matchLabels: {}  # All namespaces
EOF

# Pods auto-mount /etc/ssl/certs/ca-bundle.crt via projected volume
```

### 5.2 Istio/Envoy Certificate Rotation

**SPIFFE/SPIRE integration:**

```yaml
# spire-server ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: spire-server
  namespace: spire
data:
  server.conf: |
    server {
      bind_address = "0.0.0.0"
      bind_port = "8081"
      trust_domain = "example.org"
      data_dir = "/run/spire/data"
      ca_ttl = "168h"  # 1 week
      default_x509_svid_ttl = "1h"  # Aggressive rotation
    }
    
    plugins {
      KeyManager "disk" {
        keys_path = "/run/spire/data/keys.json"
      }
      
      DataStore "sql" {
        database_type = "sqlite3"
        connection_string = "/run/spire/data/datastore.sqlite3"
      }
    }
```

**Envoy SDS (Secret Discovery Service) config:**

```yaml
# Istio proxy config (sidecar)
apiVersion: v1
kind: ConfigMap
metadata:
  name: istio-sidecar-injector
  namespace: istio-system
data:
  values: |
    global:
      proxy:
        holdApplicationUntilProxyStarts: true
        # Certificate refresh interval
        secretTTL: 3600s  # Fetch new cert every hour
        envoy:
          metricsServiceAddress: ""
          tracingServiceAddress: ""
          # SDS socket
          sdsUdsPath: "unix:///var/run/secrets/workload-spiffe-uds/socket"
```

**Monitor cert rotation:**

```bash
# Watch Envoy admin interface
kubectl exec -it deploy/app -c istio-proxy -- curl localhost:15000/certs | jq '.certificates[] | {days_until_expiration, valid_from, expiration_time}'

# Prometheus metrics
envoy_server_days_until_first_cert_expiring
```

### 5.3 Production Rollout Pattern

```yaml
# Progressive cert rotation
apiVersion: v1
kind: ConfigMap
metadata:
  name: tls-rotation-config
data:
  rollout.yaml: |
    phases:
      - name: canary
        percentage: 5
        duration: 1h
        validation:
          - check: tls_handshake_success_rate > 0.99
          - check: cert_expiry > 24h
      
      - name: progressive
        percentage: 50
        duration: 4h
        validation:
          - check: avg_latency_p99 < baseline * 1.1
      
      - name: full
        percentage: 100
        validation:
          - check: error_rate < 0.01
    
    rollback_triggers:
      - tls_handshake_failures > 10/min
      - cert_validation_errors > 0
```

**Automation script (Go):**

```go
// rollout.go
package main

import (
    "context"
    "time"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/kubernetes"
)

func rotateCerts(ctx context.Context, clientset *kubernetes.Clientset) error {
    // Phase 1: Update canary pods
    canaryPods, _ := clientset.CoreV1().Pods("default").List(ctx, metav1.ListOptions{
        LabelSelector: "tier=canary",
    })
    
    for _, pod := range canaryPods.Items {
        // Trigger cert refresh via annotation
        pod.Annotations["cert-rotation"] = time.Now().Format(time.RFC3339)
        clientset.CoreV1().Pods("default").Update(ctx, &pod, metav1.UpdateOptions{})
    }
    
    // Wait & validate
    time.Sleep(1 * time.Hour)
    if !validateMetrics() {
        return rollback()
    }
    
    // Phase 2: Progressive rollout (omitted for brevity)
    return nil
}

func validateMetrics() bool {
    // Query Prometheus for TLS handshake success rate
    // return rate > 0.99
    return true
}
```

---

## 6. Advanced Topics

### 6.1 Certificate Pinning (HPKP Alternative)

**Public key pinning in code (Go):**

```go
import "crypto/x509"

var trustedPubKeyHashes = []string{
    "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=", // Primary
    "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=", // Backup
}

func verifyPinning(rawCerts [][]byte) error {
    cert, _ := x509.ParseCertificate(rawCerts[0])
    pubKeyDER, _ := x509.MarshalPKIXPublicKey(cert.PublicKey)
    hash := sha256.Sum256(pubKeyDER)
    pinHash := "sha256/" + base64.StdEncoding.EncodeToString(hash[:])
    
    for _, trusted := range trustedPubKeyHashes {
        if pinHash == trusted {
            return nil
        }
    }
    return fmt.Errorf("public key pinning failed")
}
```

### 6.2 Memory-Safe Cache Implementation (Rust)

```rust
use std::sync::Arc;
use dashmap::DashMap; // Concurrent HashMap
use lru::LruCache;

struct CertCache {
    // Eviction policy: LRU
    cache: Arc<DashMap<String, Arc<Vec<u8>>>>,
    max_size: usize,
}

impl CertCache {
    fn new(max_size: usize) -> Self {
        Self {
            cache: Arc::new(DashMap::new()),
            max_size,
        }
    }
    
    fn get(&self, key: &str) -> Option<Arc<Vec<u8>>> {
        self.cache.get(key).map(|v| v.clone())
    }
    
    fn put(&self, key: String, value: Vec<u8>) {
        if self.cache.len() >= self.max_size {
            // Evict random entry (use proper LRU in prod)
            if let Some(k) = self.cache.iter().next().map(|e| e.key().clone()) {
                self.cache.remove(&k);
            }
        }
        self.cache.insert(key, Arc::new(value));
    }
}
```

### 6.3 Constant-Time Cache Lookups (Side-Channel Mitigation)

**Challenge:** Timing attacks can leak cert existence via cache hits/misses.

**Mitigation (theoretical, not practical in most scenarios):**

```c
// Constant-time string comparison
int ct_strcmp(const char *a, const char *b, size_t len) {
    volatile unsigned char diff = 0;
    for (size_t i = 0; i < len; i++) {
        diff |= a[i] ^ b[i];
    }
    return diff;
}

// Cache lookup with obfuscation
void* cache_get_ct(cache_t *cache, const char *key) {
    void *result = NULL;
    for (int i = 0; i < cache->size; i++) {
        int match = ct_strcmp(cache->entries[i].key, key, KEY_LEN) == 0;
        // Branchless assignment
        result = (match ? cache->entries[i].value : result);
    }
    return result;
}
```

**Note:** Real-world systems prioritize performance over constant-time lookups for cert caches. Use this only in high-security contexts.

---

## 7. Testing & Validation

### 7.1 Unit Tests (Go)

```go
// cache_test.go
package cache

import "testing"

func TestSessionCacheEviction(t *testing.T) {
    cache := NewSessionCache(2)
    
    cache.Put("key1", &tls.ClientSessionState{})
    cache.Put("key2", &tls.ClientSessionState{})
    cache.Put("key3", &tls.ClientSessionState{}) // Evicts key1
    
    if _, ok := cache.Get("key1"); ok {
        t.Error("Expected key1 to be evicted")
    }
    if _, ok := cache.Get("key3"); !ok {
        t.Error("Expected key3 to exist")
    }
}

func BenchmarkCachePut(b *testing.B) {
    cache := NewSessionCache(1024)
    sess := &tls.ClientSessionState{}
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        cache.Put(fmt.Sprintf("key%d", i), sess)
    }
}
```

### 7.2 Integration Tests (NGINX + OCSP)

```bash
#!/bin/bash
# test-ocsp-stapling.sh

# Start NGINX with test config
nginx -c /tmp/nginx-test.conf

# Fetch with OCSP status
RESPONSE=$(echo | openssl s_client -connect localhost:443 -status 2>&1)

if echo "$RESPONSE" | grep -q "OCSP Response Status: successful"; then
    echo "PASS: OCSP stapling works"
else
    echo "FAIL: No OCSP response"
    exit 1
fi

# Validate response freshness
THIS_UPDATE=$(echo "$RESPONSE" | grep "This Update:" | cut -d: -f2-)
NEXT_UPDATE=$(echo "$RESPONSE" | grep "Next Update:" | cut -d: -f2-)

# Check expiry (basic)
if [[ -z "$NEXT_UPDATE" ]]; then
    echo "FAIL: Missing Next Update field"
    exit 1
fi

echo "PASS: OCSP response valid until $NEXT_UPDATE"
```

### 7.3 Fuzzing Certificate Parser (libFuzzer + AFL)

```c
// fuzz_cert_cache.c
#include <openssl/x509.h>
#include <stdint.h>
#include <stddef.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    const unsigned char *p = data;
    X509 *cert = d2i_X509(NULL, &p, size);
    if (cert) {
        X509_verify_cert_error_string(X509_V_OK);
        X509_free(cert);
    }
    return 0;
}
```

```bash
# Build with AFL++
afl-clang-fast -o fuzz_cert_cache fuzz_cert_cache.c -lssl -lcrypto
afl-fuzz -i testcases/ -o findings/ ./fuzz_cert_cache

# Or use libFuzzer
clang -g -O1 -fsanitize=fuzzer,address fuzz_cert_cache.c -lssl -lcrypto -o fuzz
./fuzz corpus/ -max_total_time=600
```

---

## 8. Production Deployment

### 8.1 Cache Configuration Template

```yaml
# cert-cache-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tls-cache-config
data:
  cache.conf: |
    # Session cache
    session_cache_type: redis
    session_cache_ttl: 300
    session_cache_max_entries: 10000
    
    # OCSP cache
    ocsp_cache_enabled: true
    ocsp_cache_dir: /var/cache/ocsp
    ocsp_refresh_interval: 3600
    ocsp_must_staple: true
    
    # CRL cache
    crl_cache_enabled: false  # Prefer OCSP
    
    # Security
    cache_file_permissions: "0600"
    cache_owner: "tls-cache:tls-cache"
    
    # Monitoring
    metrics_endpoint: :9090
    log_level: info
```

### 8.2 Monitoring & Alerting

**Prometheus rules:**

```yaml
# prometheus-rules.yaml
groups:
  - name: tls_cache
    interval: 30s
    rules:
      - alert: CertificateExpiringSoon
        expr: envoy_server_days_until_first_cert_expiring < 7
        labels:
          severity: warning
        annotations:
          summary: "Certificate expires in {{ $value }} days"
      
      - alert: OCSPResponseStale
        expr: time() - ocsp_response_last_update > 7200
        labels:
          severity: critical
        annotations:
          summary: "OCSP response not updated for 2h"
      
      - alert: CachePoisoningAttempt
        expr: rate(cert_validation_errors[5m]) > 0.01
        labels:
          severity: critical
        annotations:
          summary: "High rate of cert validation errors"
      
      - alert: CacheMemoryExhaustion
        expr: cert_cache_size_bytes / cert_cache_max_bytes > 0.9
        labels:
          severity: warning
```

**Grafana dashboard (JSON):**

```json
{
  "panels": [
    {
      "title": "TLS Handshake Latency",
      "targets": [
        {"expr": "histogram_quantile(0.99, rate(tls_handshake_duration_seconds_bucket[5m]))"}
      ]
    },
    {
      "title": "Session Cache Hit Rate",
      "targets": [
        {"expr": "rate(tls_session_cache_hits[5m]) / rate(tls_session_cache_lookups[5m])"}
      ]
    },
    {
      "title": "Certificate Expiry",
      "targets": [
        {"expr": "min(envoy_server_days_until_first_cert_expiring) by (pod)"}
      ]
    }
  ]
}
```

### 8.3 Disaster Recovery

**Backup strategy:**

```bash
#!/bin/bash
# backup-tls-cache.sh

BACKUP_DIR="/backup/tls-cache/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup trust store
tar czf "$BACKUP_DIR/trust-store.tar.gz" /etc/ssl/certs/

# Backup OCSP responses
tar czf "$BACKUP_DIR/ocsp-cache.tar.gz" /var/cache/ocsp/

# Backup cert-manager secrets (Kubernetes)
kubectl get secrets -n cert-manager -o yaml > "$BACKUP_DIR/cert-manager-secrets.yaml"

# Backup SPIRE data
kubectl exec -n spire spire-server-0 -- tar czf - /run/spire/data > "$BACKUP_DIR/spire-data.tar.gz"

# Upload to S3
aws s3 sync "$BACKUP_DIR" s3://tls-backups/$(date +%Y%m%d)/
```

**Rollback procedure:**

```bash
# 1. Stop services
systemctl stop nginx envoy

# 2. Restore trust store
tar xzf trust-store.tar.gz -C /

# 3. Restore OCSP cache
tar xzf ocsp-cache.tar.gz -C /

# 4. Verify certs
openssl verify -CAfile /etc/ssl/certs/ca-bundle.crt /etc/ssl/certs/server.crt

# 5. Restart services
systemctl start nginx envoy

# 6. Validate
curl -v https://localhost:443 2>&1 | grep "SSL connection"
```

---

## 9. Threat Mitigation Summary

| Threat | Detection | Prevention | Recovery |
|--------|-----------|------------|----------|
| **Stale cert use** | Monitor `cert_age` metric | OCSP must-staple, short cache TTL | Force refresh, revoke cert |
| **Cache poisoning** | Hash mismatch alerts | Signed OCSP, file integrity (AIDE) | Restore from backup, rebuild cache |
| **Privilege escalation** | `auditd` file access logs | Strict perms (600), LSM (SELinux) | Rotate keys, forensic analysis |
| **Revocation bypass** | OCSP fetch failures | Fail-closed policy, monitoring | Emergency cert replacement |
| **Memory DoS** | OOM alerts, cgroup limits | LRU eviction, rate limiting | Restart service, scale pods |
| **Side-channel leak** | Timing analysis (rare) | Constant-time ops (limited use) | Rotate cert, key compromise handling |

---

## 10. Next Steps

### Immediate (Week 1)
1. **Audit current trust stores:** Run `openssl verify` on all prod certs, identify custom CAs
2. **Enable OCSP stapling:** NGINX/Envoy configs, validate with `openssl s_client -status`
3. **Deploy cert-manager:** Kubernetes clusters, automate cert renewal

### Short-term (Month 1)
4. **Implement session cache monitoring:** Prometheus metrics for hit rate, expiry
5. **Set up CRL/OCSP auto-refresh:** Systemd timers, Kubernetes CronJobs
6. **Create rollback playbook:** Document restore procedures, test in staging

### Long-term (Quarter 1)
7. **Migrate to SPIFFE/SPIRE:** Workload identity, automated rotation
8. **Fuzz test custom cache code:** AFL++/libFuzzer for memory safety
9. **Implement cache sharding:** Redis Cluster for high-throughput mTLS environments
10. **Build threat detection pipeline:** SIEM integration for cert validation anomalies

---

## References

**Standards & RFCs:**
- [RFC 6960: OCSP](https://datatracker.ietf.org/doc/html/rfc6960)
- [RFC 5280: X.509 Certificate and CRL Profile](https://datatracker.ietf.org/doc/html/rfc5280)
- [RFC 8446: TLS 1.3](https://datatracker.ietf.org/doc/html/rfc8446) (Section 4.6: Session Resumption)
- [SPIFFE/SPIRE](https://spiffe.io/docs/latest/spire-about/)

**Tools:**
- [cert-manager](https://cert-manager.io/docs/)
- [trust-manager](https://cert-manager.io/docs/trust/trust-manager/)
- [OpenSSL](https://www.openssl.org/docs/)
- [rustls](https://docs.rs/rustls/)
- [Go crypto/tls](https://pkg.go.dev/crypto/tls)

**Security:**
- [NIST SP 800-52r2: TLS Guidelines](https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final)
- [OWASP: Certificate Pinning](https://owasp.org/www-community/controls/Certificate_and_Public_Key_Pinning)
- [CAA Records (RFC 8659)](https://datatracker.ietf.org/doc/html/rfc8659)

This guide provides production-grade patterns for cert caching across multiple stacks. Adjust cache TTLs, eviction policies, and revocation strategies based on your threat model and latency requirements.