# OIDC Comprehensive Deep-Dive: Security-First Production Guide

**Summary**: OpenID Connect (OIDC) is an identity layer on OAuth 2.0 enabling federated authentication with cryptographically-signed ID tokens (JWT). It solves SSO, user identity propagation, and token-based authN/authZ across distributed systems. Core security model: asymmetric cryptography (RS256/ES256), short-lived access tokens, refresh token rotation, PKCE for public clients, and strict redirect URI validation. Used extensively in cloud IAM (AWS IRSA, GCP Workload Identity, Azure MI), Kubernetes service account federation, service mesh mTLS bootstrap, and zero-trust architectures. Production focus: token validation, key rotation, replay prevention, and secure session management.

---

## Architecture Overview

```
┌─────────────┐                                    ┌──────────────┐
│   Client    │                                    │ OIDC Provider│
│ Application │                                    │   (IdP)      │
│             │                                    │              │
│ - Web App   │                                    │ - Issuer     │
│ - CLI Tool  │                                    │ - JWKS Endpoint
│ - Service   │                                    │ - Token Endpoint
└──────┬──────┘                                    │ - UserInfo   │
       │                                           └───────┬──────┘
       │                                                   │
       │ 1. Auth Request (+ PKCE)                         │
       │─────────────────────────────────────────────────>│
       │                                                   │
       │ 2. User Authentication                           │
       │   (Redirect to IdP Login)                        │
       │<──────────────────────────────────────────────────│
       │                                                   │
       │ 3. Authorization Code                            │
       │   (+ state, nonce validation)                    │
       │<──────────────────────────────────────────────────│
       │                                                   │
       │ 4. Token Exchange (code + code_verifier)         │
       │─────────────────────────────────────────────────>│
       │                                                   │
       │ 5. ID Token + Access Token + Refresh Token       │
       │<──────────────────────────────────────────────────│
       │                                                   │
       ▼                                                   │
┌─────────────┐                                           │
│   Token     │                                           │
│ Validation  │                                           │
│             │                                           │
│ - Signature │  6. Fetch JWKS (cache w/ rotation)       │
│ - Claims    │─────────────────────────────────────────>│
│ - Expiry    │                                           │
│ - Audience  │  7. Public Keys (RS256/ES256)            │
│ - Issuer    │<──────────────────────────────────────────│
└─────────────┘                                           │
       │                                                   │
       ▼                                                   │
┌─────────────┐                                           │
│  Protected  │  8. API Call (Bearer token)              │
│  Resource   │─────────────────────────────────────────>│
│   (API)     │                                           │
└─────────────┘  9. UserInfo (optional profile data)     │
                 <──────────────────────────────────────────┘
```

---

## Core Concepts: First Principles

### 1. **What is OIDC and Why It Exists**

**Problem Space**:
- OAuth 2.0 provides **authorization** (delegated access) but no standard for **authentication** (who the user is)
- Pre-OIDC: custom user info endpoints, inconsistent identity claims, no standardized token format
- Need: federated identity, SSO across domains, machine-to-machine identity

**OIDC Solution**:
- Adds identity layer on OAuth 2.0
- Introduces **ID Token** (JWT) with standardized claims about authenticated user
- Provides **UserInfo endpoint** for additional profile data
- Standardizes **Discovery** (`/.well-known/openid-configuration`)

**Core Guarantee**: Cryptographically-signed assertion of user identity from a trusted authority

---

### 2. **Token Types and Lifecycle**

#### **ID Token** (JWT)
- **Purpose**: Proof of authentication, user identity claims
- **Format**: JSON Web Token (JWT) with three parts: `header.payload.signature`
- **Signature Algorithms**: RS256 (RSA-SHA256), ES256 (ECDSA-P256), HS256 (symmetric, avoid in production)
- **Lifetime**: Short (5-15 min), single-use for initial authentication
- **Validation**: Signature, issuer, audience, expiry, nonce (replay prevention)

```json
{
  "header": {
    "alg": "RS256",
    "kid": "abc123",  // Key ID for rotation
    "typ": "JWT"
  },
  "payload": {
    "iss": "https://idp.example.com",      // Issuer
    "sub": "user-uuid-1234",               // Subject (unique user ID)
    "aud": "client-app-id",                // Audience (client ID)
    "exp": 1707264000,                     // Expiry (Unix timestamp)
    "iat": 1707263100,                     // Issued at
    "nonce": "random-cryptographic-nonce", // Replay prevention
    "email": "user@example.com",
    "email_verified": true,
    "groups": ["admin", "dev"]             // Custom claims
  },
  "signature": "..."  // RS256 signature over header.payload
}
```

#### **Access Token** (Opaque or JWT)
- **Purpose**: Authorization to access protected resources (APIs)
- **Format**: Often opaque (random string), can be JWT for stateless validation
- **Lifetime**: Short (1 hour typical), can be refreshed
- **Scope**: Defines permissions (e.g., `read:user`, `write:data`)
- **Validation**: Introspection endpoint (opaque) or JWT validation (if JWT)

#### **Refresh Token** (Opaque, long-lived)
- **Purpose**: Obtain new access tokens without re-authentication
- **Lifetime**: Long (days/weeks), single-use with rotation
- **Security**: Encrypted at rest, bound to client, revocable
- **Rotation**: Each use issues new refresh token, invalidates old (prevents replay)

---

### 3. **OIDC Flows (Grant Types)**

#### **Authorization Code Flow** (Most Secure, Server-Side Apps)

```
User → Client → IdP (login) → Client (code) → Client (exchange) → Tokens
```

**Steps**:
1. Client redirects user to IdP with `response_type=code`
2. User authenticates, consents
3. IdP redirects back with **authorization code** (short-lived, single-use)
4. Client exchanges code for tokens (backend, client secret required)
5. Tokens issued

**Security**: Code is useless without client secret, prevents token interception

**PKCE (Proof Key for Code Exchange)**: Required for public clients (mobile, SPA)
- Client generates random `code_verifier` (43-128 chars)
- Sends SHA256 hash as `code_challenge` in auth request
- Sends `code_verifier` in token exchange
- IdP verifies hash matches
- **Prevents**: Authorization code interception attacks

```bash
# Generate PKCE pair
CODE_VERIFIER=$(openssl rand -base64 32 | tr -d '=' | tr '+/' '-_')
CODE_CHALLENGE=$(echo -n "$CODE_VERIFIER" | openssl dgst -sha256 -binary | base64 | tr -d '=' | tr '+/' '-_')
```

#### **Implicit Flow** (DEPRECATED - DO NOT USE)
- Returns tokens directly in URL fragment
- No code exchange step
- **Vulnerability**: Tokens exposed in browser history, referrer headers
- **Replacement**: Authorization Code + PKCE

#### **Client Credentials Flow** (Machine-to-Machine)
```
Service → IdP (client_id + secret) → Access Token
```

- No user involved, service identity
- Used for: microservice-to-microservice, CI/CD pipelines
- **Security**: Rotate secrets, scope down permissions

#### **Device Code Flow** (IoT, CLI Tools)
```
Device → IdP (device code) → User (browser login with code) → Device (poll) → Tokens
```

- For devices without browsers (smart TVs, CLI)
- User enters code on separate device

---

### 4. **Discovery and Metadata**

**Well-Known Endpoint**: `https://idp.example.com/.well-known/openid-configuration`

```json
{
  "issuer": "https://idp.example.com",
  "authorization_endpoint": "https://idp.example.com/authorize",
  "token_endpoint": "https://idp.example.com/token",
  "userinfo_endpoint": "https://idp.example.com/userinfo",
  "jwks_uri": "https://idp.example.com/.well-known/jwks.json",
  "response_types_supported": ["code", "token", "id_token"],
  "subject_types_supported": ["public", "pairwise"],
  "id_token_signing_alg_values_supported": ["RS256", "ES256"],
  "scopes_supported": ["openid", "profile", "email"],
  "claims_supported": ["sub", "email", "name", "groups"],
  "grant_types_supported": ["authorization_code", "refresh_token"]
}
```

**JWKS (JSON Web Key Set)**: Public keys for token signature verification

```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "key-2024-01",
      "n": "...",  // Modulus (base64url)
      "e": "AQAB"  // Exponent
    },
    {
      "kty": "EC",
      "use": "sig",
      "kid": "key-2024-02",
      "crv": "P-256",
      "x": "...",
      "y": "..."
    }
  ]
}
```

**Key Rotation**:
- Multiple keys in JWKS (old + new)
- Grace period for validation (24-48 hours)
- Clients cache JWKS, refresh on unknown `kid`

---

### 5. **Token Validation (Critical Security)**

#### **ID Token Validation Steps** (MUST enforce all)

```go
// Production-grade ID token validation (Go example)
package oidc

import (
    "context"
    "crypto/rsa"
    "encoding/json"
    "fmt"
    "time"
    
    "github.com/golang-jwt/jwt/v5"
)

type IDTokenClaims struct {
    Issuer    string   `json:"iss"`
    Subject   string   `json:"sub"`
    Audience  []string `json:"aud"`
    ExpiresAt int64    `json:"exp"`
    IssuedAt  int64    `json:"iat"`
    Nonce     string   `json:"nonce"`
    Email     string   `json:"email"`
    Groups    []string `json:"groups"`
    jwt.RegisteredClaims
}

func ValidateIDToken(tokenString, expectedIssuer, expectedAudience, expectedNonce string, jwks *JWKSCache) (*IDTokenClaims, error) {
    // 1. Parse without validation to extract kid
    token, _ := jwt.ParseWithClaims(tokenString, &IDTokenClaims{}, nil)
    kid, ok := token.Header["kid"].(string)
    if !ok {
        return nil, fmt.Errorf("missing kid in header")
    }
    
    // 2. Fetch public key from JWKS (with caching)
    publicKey, err := jwks.GetKey(kid)
    if err != nil {
        return nil, fmt.Errorf("failed to fetch key: %w", err)
    }
    
    // 3. Validate signature and parse claims
    claims := &IDTokenClaims{}
    token, err = jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
        // Ensure RS256/ES256 (prevent algorithm substitution)
        if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
            if _, ok := token.Method.(*jwt.SigningMethodECDSA); !ok {
                return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
            }
        }
        return publicKey, nil
    })
    if err != nil {
        return nil, fmt.Errorf("signature validation failed: %w", err)
    }
    
    // 4. Validate issuer
    if claims.Issuer != expectedIssuer {
        return nil, fmt.Errorf("invalid issuer: got %s, want %s", claims.Issuer, expectedIssuer)
    }
    
    // 5. Validate audience
    validAud := false
    for _, aud := range claims.Audience {
        if aud == expectedAudience {
            validAud = true
            break
        }
    }
    if !validAud {
        return nil, fmt.Errorf("invalid audience: %v", claims.Audience)
    }
    
    // 6. Validate expiry (with clock skew tolerance)
    now := time.Now().Unix()
    clockSkew := int64(60) // 60 seconds
    if claims.ExpiresAt < (now - clockSkew) {
        return nil, fmt.Errorf("token expired")
    }
    
    // 7. Validate issued-at (prevent future tokens)
    if claims.IssuedAt > (now + clockSkew) {
        return nil, fmt.Errorf("token issued in future")
    }
    
    // 8. Validate nonce (replay prevention)
    if claims.Nonce != expectedNonce {
        return nil, fmt.Errorf("invalid nonce")
    }
    
    return claims, nil
}
```

#### **Access Token Validation** (Opaque)

```bash
# Token introspection (RFC 7662)
curl -X POST https://idp.example.com/introspect \
  -u "client_id:client_secret" \
  -d "token=$ACCESS_TOKEN"

# Response
{
  "active": true,
  "scope": "read:user write:data",
  "client_id": "app-xyz",
  "username": "user@example.com",
  "exp": 1707264000,
  "sub": "user-uuid-1234"
}
```

**Access Token as JWT** (Stateless):
- Same validation as ID token
- Check `scope` claim for authorization
- Verify `azp` (authorized party) if present

---

### 6. **Security Considerations and Threat Model**

#### **Threats**

| Threat | Mitigation |
|--------|-----------|
| **Token Interception** (MITM) | TLS 1.3, HSTS, certificate pinning |
| **Authorization Code Interception** | PKCE (mandatory for public clients) |
| **Replay Attacks** | Nonce validation, short token lifetime, single-use codes |
| **Cross-Site Request Forgery** | State parameter validation, SameSite cookies |
| **Token Leakage** (logs, URL) | Never log tokens, use POST for token exchange |
| **Phishing** | Strict redirect URI whitelist, user education |
| **Algorithm Substitution** | Enforce RS256/ES256, reject "none" algorithm |
| **Key Compromise** | Regular rotation, revocation list, HSM for private keys |
| **Session Fixation** | Generate new session ID post-login |
| **Refresh Token Theft** | Rotation on use, device binding, revocation |

#### **Defense-in-Depth Layers**

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Network (TLS, mTLS, WAF, DDoS protection) │
├─────────────────────────────────────────────────────┤
│ Layer 2: Transport (PKCE, state, nonce)            │
├─────────────────────────────────────────────────────┤
│ Layer 3: Token (signature, expiry, audience)       │
├─────────────────────────────────────────────────────┤
│ Layer 4: Session (rotation, binding, revocation)   │
├─────────────────────────────────────────────────────┤
│ Layer 5: Authorization (RBAC, ABAC, scope check)   │
├─────────────────────────────────────────────────────┤
│ Layer 6: Audit (log all auth events, anomaly det.) │
└─────────────────────────────────────────────────────┘
```

---

### 7. **Production Integrations**

#### **AWS: IAM Roles for Service Accounts (IRSA)**

```yaml
# EKS service account with OIDC
apiVersion: v1
kind: ServiceAccount
metadata:
  name: s3-reader
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/s3-reader-role

---
# IAM trust policy (trust EKS OIDC provider)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-west-2.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-west-2.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE:sub": "system:serviceaccount:production:s3-reader",
          "oidc.eks.us-west-2.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

**Flow**:
1. Pod gets projected JWT token from K8s (mounted at `/var/run/secrets/eks.amazonaws.com/serviceaccount/token`)
2. AWS SDK calls STS `AssumeRoleWithWebIdentity` with token
3. STS validates token against EKS OIDC provider JWKS
4. Returns temporary AWS credentials (1 hour)

```bash
# Verify OIDC provider
aws iam list-open-id-connect-providers

# Check trust relationship
aws iam get-role --role-name s3-reader-role
```

#### **GCP: Workload Identity Federation**

```bash
# Create workload identity pool
gcloud iam workload-identity-pools create k8s-pool \
  --location=global \
  --display-name="Kubernetes Workload Identity"

# Create provider (OIDC)
gcloud iam workload-identity-pools providers create-oidc k8s-provider \
  --location=global \
  --workload-identity-pool=k8s-pool \
  --issuer-uri=https://container.googleapis.com/v1/projects/PROJECT_ID/locations/REGION/clusters/CLUSTER_NAME \
  --allowed-audiences=https://gcp.example.com \
  --attribute-mapping="google.subject=assertion.sub,attribute.namespace=assertion['kubernetes.io']['namespace']"

# Bind service account
gcloud iam service-accounts add-iam-policy-binding gcs-reader@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/k8s-pool/attribute.namespace/production"
```

#### **Kubernetes: Service Account Token Projection**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  serviceAccountName: app-sa
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: oidc-token
      mountPath: /var/run/secrets/tokens
      readOnly: true
  volumes:
  - name: oidc-token
    projected:
      sources:
      - serviceAccountToken:
          path: oidc-token
          expirationSeconds: 3600
          audience: https://api.example.com
```

**Token Validation in Workload**:

```go
// Read projected token
tokenBytes, err := os.ReadFile("/var/run/secrets/tokens/oidc-token")
token := string(tokenBytes)

// Fetch K8s OIDC discovery
// https://kubernetes.default.svc/.well-known/openid-configuration
```

---

### 8. **Client Implementation Patterns**

#### **Confidential Client (Backend Service)**

```go
// Go example using github.com/coreos/go-oidc/v3/oidc
package main

import (
    "context"
    "log"
    "net/http"
    
    "github.com/coreos/go-oidc/v3/oidc"
    "golang.org/x/oauth2"
)

func main() {
    ctx := context.Background()
    
    // 1. Discover provider configuration
    provider, err := oidc.NewProvider(ctx, "https://idp.example.com")
    if err != nil {
        log.Fatal(err)
    }
    
    // 2. Configure OAuth2 client
    oauth2Config := oauth2.Config{
        ClientID:     "client-id",
        ClientSecret: "client-secret",
        RedirectURL:  "https://app.example.com/callback",
        Endpoint:     provider.Endpoint(),
        Scopes:       []string{oidc.ScopeOpenID, "profile", "email"},
    }
    
    // 3. Generate auth URL with state and PKCE
    state := generateRandomState() // crypto/rand
    verifier := oauth2.GenerateVerifier()
    authURL := oauth2Config.AuthCodeURL(state, 
        oauth2.S256ChallengeOption(verifier))
    
    http.HandleFunc("/login", func(w http.ResponseWriter, r *http.Request) {
        // Store state and verifier in session
        http.Redirect(w, r, authURL, http.StatusFound)
    })
    
    // 4. Handle callback
    http.HandleFunc("/callback", func(w http.ResponseWriter, r *http.Request) {
        // Validate state
        if r.URL.Query().Get("state") != state {
            http.Error(w, "invalid state", http.StatusBadRequest)
            return
        }
        
        // Exchange code for tokens
        oauth2Token, err := oauth2Config.Exchange(ctx, 
            r.URL.Query().Get("code"),
            oauth2.VerifierOption(verifier))
        if err != nil {
            http.Error(w, "token exchange failed", http.StatusInternalServerError)
            return
        }
        
        // Extract ID token
        rawIDToken, ok := oauth2Token.Extra("id_token").(string)
        if !ok {
            http.Error(w, "no id_token", http.StatusInternalServerError)
            return
        }
        
        // Validate ID token
        verifier := provider.Verifier(&oidc.Config{ClientID: "client-id"})
        idToken, err := verifier.Verify(ctx, rawIDToken)
        if err != nil {
            http.Error(w, "id_token validation failed", http.StatusUnauthorized)
            return
        }
        
        // Extract claims
        var claims struct {
            Email         string   `json:"email"`
            EmailVerified bool     `json:"email_verified"`
            Groups        []string `json:"groups"`
        }
        if err := idToken.Claims(&claims); err != nil {
            http.Error(w, "failed to parse claims", http.StatusInternalServerError)
            return
        }
        
        // Create session, store tokens securely
        log.Printf("User authenticated: %s", claims.Email)
    })
    
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

#### **Public Client (SPA/Mobile) - PKCE Flow**

```typescript
// TypeScript example (browser)
import { AuthorizationServiceConfiguration, AuthorizationRequest, 
         RedirectRequestHandler, BaseTokenRequestHandler, 
         AuthorizationNotifier, GRANT_TYPE_AUTHORIZATION_CODE } from '@openid/appauth';

class OIDCClient {
  private config!: AuthorizationServiceConfiguration;
  private clientId = 'spa-client-id';
  private redirectUri = 'https://app.example.com/callback';
  
  async init() {
    // 1. Discover configuration
    this.config = await AuthorizationServiceConfiguration.fetchFromIssuer(
      'https://idp.example.com'
    );
  }
  
  async login() {
    // 2. Generate PKCE pair
    const codeVerifier = this.generateCodeVerifier();
    const codeChallenge = await this.generateCodeChallenge(codeVerifier);
    
    // Store verifier securely (sessionStorage)
    sessionStorage.setItem('pkce_verifier', codeVerifier);
    
    // 3. Create authorization request
    const request = new AuthorizationRequest({
      client_id: this.clientId,
      redirect_uri: this.redirectUri,
      scope: 'openid profile email',
      response_type: 'code',
      state: this.generateState(),
      extras: {
        code_challenge: codeChallenge,
        code_challenge_method: 'S256',
        nonce: this.generateNonce() // Store for validation
      }
    });
    
    // 4. Redirect to IdP
    const handler = new RedirectRequestHandler();
    handler.performAuthorizationRequest(this.config, request);
  }
  
  async handleCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    
    // 5. Validate state
    if (state !== sessionStorage.getItem('state')) {
      throw new Error('Invalid state');
    }
    
    // 6. Exchange code for tokens
    const codeVerifier = sessionStorage.getItem('pkce_verifier')!;
    const tokenResponse = await fetch(this.config.tokenEndpoint!, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: GRANT_TYPE_AUTHORIZATION_CODE,
        code: code!,
        redirect_uri: this.redirectUri,
        client_id: this.clientId,
        code_verifier: codeVerifier
      })
    });
    
    const tokens = await tokenResponse.json();
    
    // 7. Validate ID token (use jose library)
    const idToken = await this.validateIDToken(tokens.id_token);
    
    // 8. Store tokens securely
    this.storeTokensSecurely(tokens);
  }
  
  private generateCodeVerifier(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return this.base64UrlEncode(array);
  }
  
  private async generateCodeChallenge(verifier: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return this.base64UrlEncode(new Uint8Array(hash));
  }
}
```

---

### 9. **Token Storage and Session Management**

#### **Storage Strategies**

| Client Type | ID Token | Access Token | Refresh Token |
|-------------|----------|--------------|---------------|
| **Backend Service** | Memory (validation only) | Memory/Redis (encrypted) | Database (encrypted at rest) |
| **Web App (Server-Side)** | HTTP-only cookie | HTTP-only cookie | Encrypted session store |
| **SPA** | Memory (no storage) | Memory | Not issued (use re-auth) |
| **Mobile App** | Secure Enclave/Keychain | Keychain (encrypted) | Keychain (encrypted) |

**Never Store in**:
- LocalStorage (XSS vulnerable)
- SessionStorage (XSS vulnerable)
- Unencrypted cookies
- URL parameters
- Browser history

#### **Session Management Pattern**

```go
// Redis-backed session with encrypted tokens
package session

import (
    "context"
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "encoding/base64"
    "time"
    
    "github.com/go-redis/redis/v8"
)

type SessionStore struct {
    redis *redis.Client
    aead  cipher.AEAD
}

func NewSessionStore(redisAddr, encryptionKey string) (*SessionStore, error) {
    client := redis.NewClient(&redis.Options{
        Addr:         redisAddr,
        DB:           0,
        MaxRetries:   3,
        DialTimeout:  5 * time.Second,
        ReadTimeout:  3 * time.Second,
        WriteTimeout: 3 * time.Second,
    })
    
    // AES-GCM for authenticated encryption
    block, err := aes.NewCipher([]byte(encryptionKey))
    if err != nil {
        return nil, err
    }
    aead, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }
    
    return &SessionStore{redis: client, aead: aead}, nil
}

func (s *SessionStore) StoreTokens(ctx context.Context, sessionID string, tokens *Tokens) error {
    // Serialize tokens
    data, err := json.Marshal(tokens)
    if err != nil {
        return err
    }
    
    // Encrypt
    nonce := make([]byte, s.aead.NonceSize())
    if _, err := rand.Read(nonce); err != nil {
        return err
    }
    ciphertext := s.aead.Seal(nonce, nonce, data, nil)
    
    // Store with TTL matching refresh token lifetime
    return s.redis.Set(ctx, sessionID, base64.StdEncoding.EncodeToString(ciphertext), 7*24*time.Hour).Err()
}

func (s *SessionStore) GetTokens(ctx context.Context, sessionID string) (*Tokens, error) {
    // Retrieve
    ciphertext, err := s.redis.Get(ctx, sessionID).Result()
    if err != nil {
        return nil, err
    }
    
    // Decode and decrypt
    data, err := base64.StdEncoding.DecodeString(ciphertext)
    if err != nil {
        return nil, err
    }
    
    nonceSize := s.aead.NonceSize()
    nonce, ciphertext := data[:nonceSize], data[nonceSize:]
    plaintext, err := s.aead.Open(nil, nonce, ciphertext, nil)
    if err != nil {
        return nil, err
    }
    
    var tokens Tokens
    if err := json.Unmarshal(plaintext, &tokens); err != nil {
        return nil, err
    }
    
    return &tokens, nil
}
```

---

### 10. **Refresh Token Rotation**

```go
// Secure refresh token rotation
func (c *OIDCClient) RefreshAccessToken(ctx context.Context, refreshToken string) (*TokenResponse, error) {
    // 1. Exchange refresh token
    resp, err := c.oauth2Config.TokenSource(ctx, &oauth2.Token{
        RefreshToken: refreshToken,
    }).Token()
    if err != nil {
        // Token expired or revoked - require re-authentication
        return nil, fmt.Errorf("refresh failed: %w", err)
    }
    
    // 2. Extract new refresh token
    newRefreshToken, ok := resp.Extra("refresh_token").(string)
    if !ok {
        // IdP may not issue new refresh token every time
        newRefreshToken = refreshToken
    }
    
    // 3. Revoke old refresh token (if IdP supports RFC 7009)
    if newRefreshToken != refreshToken {
        c.revokeToken(ctx, refreshToken)
    }
    
    // 4. Return new tokens
    return &TokenResponse{
        AccessToken:  resp.AccessToken,
        RefreshToken: newRefreshToken,
        ExpiresAt:    resp.Expiry,
    }, nil
}

func (c *OIDCClient) revokeToken(ctx context.Context, token string) error {
    revocationEndpoint := c.providerConfig.RevocationEndpoint
    req, _ := http.NewRequestWithContext(ctx, "POST", revocationEndpoint, 
        strings.NewReader(url.Values{
            "token":           {token},
            "token_type_hint": {"refresh_token"},
        }.Encode()))
    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
    req.SetBasicAuth(c.clientID, c.clientSecret)
    
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("revocation failed: %d", resp.StatusCode)
    }
    return nil
}
```

---

### 11. **Multi-Tenant OIDC (Tenant Isolation)**

```go
// Dynamic OIDC provider per tenant
type TenantOIDCManager struct {
    providers sync.Map // tenant_id -> *oidc.Provider
    mu        sync.RWMutex
}

func (m *TenantOIDCManager) GetProvider(ctx context.Context, tenantID string) (*oidc.Provider, error) {
    // Check cache
    if p, ok := m.providers.Load(tenantID); ok {
        return p.(*oidc.Provider), nil
    }
    
    m.mu.Lock()
    defer m.mu.Unlock()
    
    // Double-check after acquiring lock
    if p, ok := m.providers.Load(tenantID); ok {
        return p.(*oidc.Provider), nil
    }
    
    // Fetch tenant OIDC config from database
    config, err := m.getTenantOIDCConfig(tenantID)
    if err != nil {
        return nil, err
    }
    
    // Initialize provider
    provider, err := oidc.NewProvider(ctx, config.IssuerURL)
    if err != nil {
        return nil, err
    }
    
    m.providers.Store(tenantID, provider)
    return provider, nil
}

// Tenant-specific validation
func (m *TenantOIDCManager) ValidateToken(ctx context.Context, tenantID, tokenString string) (*oidc.IDToken, error) {
    provider, err := m.GetProvider(ctx, tenantID)
    if err != nil {
        return nil, err
    }
    
    config, _ := m.getTenantOIDCConfig(tenantID)
    verifier := provider.Verifier(&oidc.Config{
        ClientID: config.ClientID,
    })
    
    return verifier.Verify(ctx, tokenString)
}
```

---

### 12. **Observability and Monitoring**

#### **Metrics to Track**

```go
// Prometheus metrics
var (
    authAttempts = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "oidc_auth_attempts_total",
            Help: "Total authentication attempts",
        },
        []string{"provider", "tenant", "result"}, // result: success/failure
    )
    
    tokenValidations = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "oidc_token_validation_duration_seconds",
            Help:    "Token validation latency",
            Buckets: prometheus.DefBuckets,
        },
        []string{"provider", "token_type"},
    )
    
    jwksCacheMisses = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "oidc_jwks_cache_misses_total",
            Help: "JWKS cache miss count",
        },
        []string{"provider"},
    )
    
    refreshTokenRotations = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "oidc_refresh_token_rotations_total",
            Help: "Refresh token rotation events",
        },
        []string{"tenant", "status"},
    )
)
```

#### **Audit Logging**

```go
type AuthEvent struct {
    Timestamp    time.Time `json:"timestamp"`
    EventType    string    `json:"event_type"` // login, logout, token_refresh, validation_failure
    TenantID     string    `json:"tenant_id"`
    UserID       string    `json:"user_id"`
    ClientID     string    `json:"client_id"`
    IPAddress    string    `json:"ip_address"`
    UserAgent    string    `json:"user_agent"`
    Success      bool      `json:"success"`
    ErrorMessage string    `json:"error_message,omitempty"`
    Metadata     map[string]interface{} `json:"metadata"`
}

func logAuthEvent(event *AuthEvent) {
    // Structured logging (JSON to stdout for container logging)
    json.NewEncoder(os.Stdout).Encode(event)
    
    // Send to SIEM (e.g., Splunk, ELK)
    // Trigger alerts on anomalies (e.g., multiple failures, unusual location)
}
```

---

### 13. **Testing Strategy**

#### **Unit Tests: Token Validation**

```go
func TestIDTokenValidation(t *testing.T) {
    // Generate test RSA key pair
    privateKey, _ := rsa.GenerateKey(rand.Reader, 2048)
    publicKey := &privateKey.PublicKey
    
    // Create test JWKS
    jwks := &JWKSCache{
        keys: map[string]*rsa.PublicKey{
            "test-key-1": publicKey,
        },
    }
    
    // Generate valid token
    claims := &IDTokenClaims{
        Issuer:    "https://test-idp.example.com",
        Subject:   "user-123",
        Audience:  []string{"test-client"},
        ExpiresAt: time.Now().Add(10 * time.Minute).Unix(),
        IssuedAt:  time.Now().Unix(),
        Nonce:     "test-nonce-xyz",
    }
    
    token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
    token.Header["kid"] = "test-key-1"
    tokenString, _ := token.SignedString(privateKey)
    
    // Test valid token
    t.Run("valid token", func(t *testing.T) {
        validated, err := ValidateIDToken(tokenString, 
            "https://test-idp.example.com", 
            "test-client", 
            "test-nonce-xyz", 
            jwks)
        
        if err != nil {
            t.Fatalf("validation failed: %v", err)
        }
        if validated.Subject != "user-123" {
            t.Errorf("unexpected subject: %s", validated.Subject)
        }
    })
    
    // Test expired token
    t.Run("expired token", func(t *testing.T) {
        expiredClaims := *claims
        expiredClaims.ExpiresAt = time.Now().Add(-1 * time.Hour).Unix()
        expiredToken := jwt.NewWithClaims(jwt.SigningMethodRS256, &expiredClaims)
        expiredToken.Header["kid"] = "test-key-1"
        expiredTokenString, _ := expiredToken.SignedString(privateKey)
        
        _, err := ValidateIDToken(expiredTokenString, 
            "https://test-idp.example.com", 
            "test-client", 
            "test-nonce-xyz", 
            jwks)
        
        if err == nil {
            t.Fatal("expected error for expired token")
        }
    })
    
    // Test nonce mismatch
    t.Run("nonce mismatch", func(t *testing.T) {
        _, err := ValidateIDToken(tokenString, 
            "https://test-idp.example.com", 
            "test-client", 
            "wrong-nonce", 
            jwks)
        
        if err == nil || !strings.Contains(err.Error(), "nonce") {
            t.Fatal("expected nonce validation error")
        }
    })
}
```

#### **Integration Tests: Full Flow**

```bash
#!/bin/bash
# Test OIDC flow with Keycloak test instance

# 1. Start Keycloak in Docker
docker run -d \
  --name keycloak-test \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest \
  start-dev

# 2. Configure realm and client
# (Use Keycloak Admin API or Terraform provider)

# 3. Test authorization code flow
curl -X POST http://localhost:8080/realms/test/protocol/openid-connect/token \
  -d "grant_type=authorization_code" \
  -d "code=AUTH_CODE" \
  -d "client_id=test-client" \
  -d "client_secret=test-secret" \
  -d "redirect_uri=http://localhost:3000/callback" \
  -d "code_verifier=PKCE_VERIFIER"

# 4. Validate response
# - Check token structure
# - Verify signature
# - Validate claims

# 5. Cleanup
docker rm -f keycloak-test
```

#### **Fuzz Testing: Token Parser**

```go
// Fuzz test for token validation
func FuzzTokenValidation(f *testing.F) {
    // Seed corpus
    f.Add("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...")
    
    f.Fuzz(func(t *testing.T, tokenString string) {
        // Should not panic on malformed input
        _, _ = ValidateIDToken(tokenString, "https://idp.example.com", "client-id", "nonce", jwks)
    })
}
```

---

### 14. **Rollout and Migration Strategy**

#### **Phase 1: Add OIDC Alongside Existing Auth** (Weeks 1-2)

```
┌─────────────────┐
│ Load Balancer   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Legacy │ │ OIDC  │
│ Auth  │ │ Auth  │
│(99%)  │ │ (1%)  │
└───────┘ └───────┘
```

**Steps**:
1. Deploy OIDC middleware (disabled by default)
2. Enable for internal test accounts
3. Monitor error rates, latency
4. Validate token caching performance

**Feature Flag**:
```go
if featureFlags.IsEnabled("oidc_auth", userID) {
    return oidcAuthHandler(r)
}
return legacyAuthHandler(r)
```

#### **Phase 2: Gradual Rollout** (Weeks 3-6)

```
Traffic: 1% → 5% → 25% → 50% → 100%
```

**Monitoring**:
- Authentication success rate (target: >99.9%)
- P50/P95/P99 latency (target: <200ms)
- JWKS cache hit rate (target: >95%)
- Session creation failures

**Rollback Trigger**:
- Auth failure rate >0.5%
- Latency P99 >500ms
- Error rate spike >10x baseline

#### **Phase 3: Deprecate Legacy** (Weeks 7-8)

1. Disable new legacy sessions
2. Expire existing legacy sessions (7 day grace period)
3. Remove legacy auth code
4. Archive legacy session data

---

### 15. **Disaster Recovery**

#### **JWKS Endpoint Outage**

```go
// JWKS cache with fallback
type ResilientJWKSCache struct {
    primary   string // https://idp.example.com/.well-known/jwks.json
    fallback  string // https://backup-idp.example.com/.well-known/jwks.json
    cache     *cache.Cache // TTL: 1 hour, stale-while-revalidate: 24 hours
}

func (c *ResilientJWKSCache) GetKey(kid string) (*rsa.PublicKey, error) {
    // 1. Check cache
    if key, found := c.cache.Get(kid); found {
        return key.(*rsa.PublicKey), nil
    }
    
    // 2. Fetch from primary
    key, err := c.fetchFromEndpoint(c.primary, kid)
    if err == nil {
        c.cache.Set(kid, key, 1*time.Hour)
        return key, nil
    }
    
    // 3. Fallback to secondary
    key, err = c.fetchFromEndpoint(c.fallback, kid)
    if err == nil {
        c.cache.Set(kid, key, 1*time.Hour)
        return key, nil
    }
    
    // 4. Use stale cache if available
    if staleKey, found := c.cache.GetStale(kid); found {
        log.Warn("Using stale JWKS key", "kid", kid)
        return staleKey.(*rsa.PublicKey), nil
    }
    
    return nil, fmt.Errorf("JWKS unavailable: %w", err)
}
```

#### **IdP Complete Outage**

```
┌──────────────┐
│ Auth Request │
└──────┬───────┘
       │
   ┌───▼────┐
   │ IdP    │ ──X─> Timeout
   │ Health │
   └───┬────┘
       │
   ┌───▼──────────┐
   │ Fallback:    │
   │ - Use cached │
   │   sessions   │
   │ - Extend TTL │
   │ - Queue new  │
   │   requests   │
   └──────────────┘
```

**Mitigation**:
1. Increase access token TTL temporarily (1 hour → 4 hours)
2. Accept cached ID tokens beyond expiry (grace period: 1 hour)
3. Queue authentication requests, process when IdP recovers
4. Send alerts to on-call

---

### 16. **Advanced: Custom Claims and Token Enhancement**

```go
// Token claims transformer (add custom claims from DB)
type ClaimsEnhancer struct {
    db *sql.DB
}

func (e *ClaimsEnhancer) EnhanceIDToken(ctx context.Context, idToken *oidc.IDToken) (*EnhancedClaims, error) {
    var standardClaims struct {
        Email string `json:"email"`
        Sub   string `json:"sub"`
    }
    if err := idToken.Claims(&standardClaims); err != nil {
        return nil, err
    }
    
    // Fetch custom claims from database
    var customClaims CustomClaims
    err := e.db.QueryRowContext(ctx, `
        SELECT roles, permissions, tenant_id, metadata
        FROM user_claims
        WHERE user_id = $1
    `, standardClaims.Sub).Scan(
        &customClaims.Roles,
        &customClaims.Permissions,
        &customClaims.TenantID,
        &customClaims.Metadata,
    )
    if err != nil {
        return nil, err
    }
    
    return &EnhancedClaims{
        StandardClaims: standardClaims,
        CustomClaims:   customClaims,
    }, nil
}
```

---

### 17. **Real-World Use Cases**

| Use Case | Flow | Integration |
|----------|------|-------------|
| **Kubernetes Workload Identity** | Service Account Token Projection → AWS STS/GCP WIF | IRSA, Workload Identity |
| **Service Mesh mTLS Bootstrap** | OIDC token → SPIFFE/SPIRE → x509 cert | Istio, Linkerd |
| **CI/CD Pipeline Auth** | GitHub OIDC → Cloud IAM role assumption | GitHub Actions → AWS/GCP/Azure |
| **Multi-Cloud SSO** | Corporate IdP → AWS SSO → GCP Cloud Identity | Okta, Azure AD |
| **API Gateway Auth** | OIDC token → JWT validation → upstream headers | Kong, Envoy, NGINX |
| **Zero Trust Network** | Device attestation + OIDC → network access | BeyondCorp, ZTA |

---

## Next 3 Steps

1. **Implement Token Validation Library** (Week 1)
   - Create Go package with JWKS caching, signature validation, claims enforcement
   - Add Prometheus metrics, structured logging
   - Write comprehensive unit/fuzz tests
   - Benchmark: target <5ms P99 validation latency

2. **Deploy OIDC Test Environment** (Week 1-2)
   - Stand up Keycloak/Dex in Kubernetes
   - Configure test realm with multiple tenants
   - Implement sample client (Go backend + TypeScript SPA)
   - Test PKCE flow, refresh token rotation, session management

3. **Production Hardening** (Week 2-3)
   - Add JWKS fallback/stale cache handling
   - Implement refresh token rotation with revocation
   - Set up monitoring dashboards (auth success rate, latency, cache hit rate)
   - Document runbook for IdP outage scenarios

---

## References

- **RFC 6749**: OAuth 2.0 Authorization Framework
- **RFC 7636**: Proof Key for Code Exchange (PKCE)
- **RFC 7519**: JSON Web Token (JWT)
- **OpenID Connect Core 1.0**: https://openid.net/specs/openid-connect-core-1_0.html
- **OIDC Discovery**: https://openid.net/specs/openid-connect-discovery-1_0.html
- **OAuth 2.0 Security Best Practices**: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics
- **AWS IRSA**: https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html
- **GCP Workload Identity**: https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity
- **CNCF SPIFFE**: https://spiffe.io/docs/latest/spiffe-about/overview/