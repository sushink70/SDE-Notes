# Comprehensive Guide to Distributed Systems with Security Focus

## 1. Fundamentals of Distributed Systems

### 1.1 Definition and Characteristics
A distributed system is a collection of independent computers that appears to users as a single coherent system. Key characteristics include:

- **Resource Sharing**: Hardware, software, and data resources are shared across nodes
- **Concurrency**: Multiple processes execute simultaneously
- **Scalability**: System capacity grows with added resources
- **Fault Tolerance**: System continues operating despite component failures
- **Transparency**: Distribution is hidden from users

### 1.2 Core Challenges
- **Network unreliability**: Messages can be delayed, lost, or duplicated
- **Partial failures**: Some components fail while others continue
- **Latency**: Communication delays between nodes
- **Concurrency control**: Managing simultaneous operations
- **Consistency**: Maintaining data coherence across nodes

## 2. Architectural Patterns

### 2.1 Client-Server Architecture
Traditional model where clients request services from centralized servers.

**Security Considerations**:
- Server becomes single point of attack
- Requires strong authentication mechanisms
- SSL/TLS for encrypted communications
- Rate limiting to prevent DoS attacks

### 2.2 Peer-to-Peer (P2P)
All nodes act as both clients and servers with equal responsibilities.

**Security Considerations**:
- No central authority for trust management
- Vulnerable to Sybil attacks (fake identities)
- Requires distributed authentication
- Content verification mechanisms needed

### 2.3 Microservices Architecture
Application broken into small, independent services.

**Security Considerations**:
- Larger attack surface with more endpoints
- Service-to-service authentication required
- API gateway for centralized security
- Container security and orchestration
- Secret management across services

### 2.4 Service-Oriented Architecture (SOA)
Enterprise-level services communicate via standardized protocols.

**Security Considerations**:
- WS-Security standards
- Message-level encryption
- SAML for federated identity
- Enterprise service bus security

## 3. Communication Mechanisms

### 3.1 Remote Procedure Call (RPC)
Allows programs to execute procedures on remote systems.

**Common Implementations**:
- gRPC (Google)
- Apache Thrift
- JSON-RPC

**Security Measures**:
- TLS encryption for data in transit
- Authentication tokens (OAuth, JWT)
- Input validation to prevent injection attacks
- Rate limiting per client

### 3.2 Message Queuing
Asynchronous communication via message brokers.

**Popular Systems**:
- RabbitMQ
- Apache Kafka
- Amazon SQS
- Redis Streams

**Security Measures**:
- Message encryption at rest and in transit
- Access control lists (ACLs) for topics/queues
- Message authentication codes (MAC)
- Audit logging of all operations
- Network segmentation for broker access

### 3.3 RESTful APIs
HTTP-based stateless communication.

**Security Best Practices**:
- HTTPS everywhere (TLS 1.3)
- OAuth 2.0 / OpenID Connect for authorization
- JWT tokens with proper expiration
- API keys with rotation policies
- CORS configuration
- Input sanitization and validation
- Rate limiting and throttling
- API versioning to deprecate insecure versions

### 3.4 GraphQL
Query language for APIs with flexible data fetching.

**Security Considerations**:
- Query complexity limits (prevent DoS)
- Query depth limiting
- Field-level authorization
- Query cost analysis
- Disable introspection in production
- Input validation on mutations

## 4. Data Management

### 4.1 CAP Theorem
States that distributed systems can provide only two of three guarantees:
- **Consistency**: All nodes see the same data
- **Availability**: System responds to all requests
- **Partition Tolerance**: System continues despite network partitions

**Security Implications**:
- CP systems: Risk of availability during attacks
- AP systems: Risk of serving stale/inconsistent data
- Trade-offs affect security model design

### 4.2 Data Replication Strategies

**Master-Slave Replication**:
- Single master for writes, multiple slaves for reads
- Security: Protect master with strongest measures
- Encrypt replication streams
- Authenticate slave connections

**Multi-Master Replication**:
- Multiple nodes accept writes
- Security: Conflict resolution must be tamper-proof
- Requires strong consistency verification

**Quorum-Based Replication**:
- Majority agreement required for operations
- Security: Byzantine fault tolerance considerations
- Cryptographic verification of quorum responses

### 4.3 Distributed Databases

**SQL Databases**:
- Google Spanner
- CockroachDB
- TiDB

**NoSQL Databases**:
- MongoDB (document)
- Cassandra (wide-column)
- Neo4j (graph)
- Redis (key-value)

**Security Hardening**:
- Encryption at rest (AES-256)
- Encryption in transit (TLS)
- Role-based access control (RBAC)
- Database auditing and logging
- Network isolation (VPC, private subnets)
- Regular security patches
- Principle of least privilege
- Data masking for sensitive information
- Backup encryption and secure storage

### 4.4 Distributed Transactions

**Two-Phase Commit (2PC)**:
1. Prepare phase: Coordinator asks participants to prepare
2. Commit phase: If all agree, commit; otherwise abort

**Security Concerns**:
- Coordinator is critical target
- Transaction logs must be tamper-proof
- Timeout mechanisms prevent resource locking attacks

**Three-Phase Commit (3PC)**:
Adds pre-commit phase to reduce blocking.

**Saga Pattern**:
Long-running transactions as series of local transactions with compensating actions.

**Security Measures**:
- Idempotency to prevent replay attacks
- Secure compensation logic
- Audit trail of all transaction steps
- Cryptographic verification of transaction integrity

## 5. Consistency Models

### 5.1 Strong Consistency
All reads return the most recent write.

**Examples**: Traditional SQL databases, Zookeeper
**Security**: Easier to reason about security invariants

### 5.2 Eventual Consistency
System eventually becomes consistent given no new updates.

**Examples**: DNS, Cassandra, DynamoDB
**Security**: Risk of reading stale data, require version vectors

### 5.3 Causal Consistency
Operations that are causally related are seen in the same order.

**Security**: Important for maintaining security policy ordering

### 5.4 Session Consistency
Consistency guarantees within a single session.

**Security**: Session hijacking becomes more critical

## 6. Consensus Algorithms

### 6.1 Paxos
Classic consensus algorithm for asynchronous systems.

**Security Considerations**:
- Byzantine failures not addressed
- Leader election must be secure
- Message authentication required

### 6.2 Raft
More understandable alternative to Paxos.

**Components**:
- Leader election
- Log replication
- Safety guarantees

**Security Measures**:
- Mutual TLS between nodes
- Log integrity verification
- Secure leader election process
- Protection against split-brain scenarios

### 6.3 Byzantine Fault Tolerance (BFT)
Tolerates arbitrary (malicious) failures.

**Algorithms**:
- Practical Byzantine Fault Tolerance (PBFT)
- Tendermint
- HotStuff

**Security Properties**:
- Tolerates up to f faulty nodes in 3f+1 system
- Cryptographic signatures for messages
- Prevents forgery and tampering
- Critical for untrusted environments

## 7. Distributed System Security

### 7.1 Authentication Mechanisms

**Kerberos**:
- Ticket-based authentication
- Trusted third-party (KDC)
- Time-sensitive tickets
- Mutual authentication

**OAuth 2.0**:
- Delegated authorization
- Access tokens and refresh tokens
- Multiple grant types
- Suitable for API authentication

**Mutual TLS (mTLS)**:
- Both client and server verify certificates
- Strong authentication for service-to-service
- Certificate management overhead

**SAML (Security Assertion Markup Language)**:
- XML-based SSO standard
- Enterprise federation
- Identity provider (IdP) trust

### 7.2 Authorization Models

**Role-Based Access Control (RBAC)**:
- Users assigned to roles
- Roles have permissions
- Scalable for large organizations

**Attribute-Based Access Control (ABAC)**:
- Policies based on attributes (user, resource, environment)
- Fine-grained control
- Complex policy management

**Capability-Based Security**:
- Unforgeable tokens represent rights
- Delegation through token passing
- Used in distributed object systems

### 7.3 Encryption

**Data at Rest**:
- Full disk encryption
- Database-level encryption
- File-level encryption
- Key management systems (KMS)
- Hardware security modules (HSM)

**Data in Transit**:
- TLS 1.3 for all communications
- IPSec for network layer
- VPN for site-to-site
- Perfect forward secrecy

**End-to-End Encryption**:
- Only endpoints can decrypt
- Server cannot read contents
- Key exchange protocols (Diffie-Hellman)

### 7.4 Key Management

**Centralized Key Management**:
- AWS KMS, Azure Key Vault, Google Cloud KMS
- Centralized policies
- Audit logging
- Key rotation

**Distributed Key Management**:
- Shamir's Secret Sharing
- Threshold cryptography
- No single point of compromise

**Best Practices**:
- Regular key rotation
- Separate keys per environment
- Hardware-backed keys
- Audit all key operations
- Principle of least privilege

### 7.5 Network Security

**Segmentation**:
- VPCs and subnets
- Security groups
- Network ACLs
- Private networks for internal services

**Firewalls**:
- Host-based firewalls
- Network firewalls
- Web application firewalls (WAF)
- DDoS protection (CloudFlare, AWS Shield)

**Service Mesh**:
- Istio, Linkerd, Consul
- mTLS between all services
- Traffic encryption
- Policy enforcement
- Circuit breaking

**Zero Trust Architecture**:
- Never trust, always verify
- Micro-segmentation
- Least privilege access
- Continuous verification

### 7.6 Security Patterns

**API Gateway Pattern**:
- Single entry point for all requests
- Authentication and authorization
- Rate limiting
- Request validation
- SSL termination
- Logging and monitoring

**Circuit Breaker Pattern**:
- Prevents cascading failures
- Security benefit: Limits DoS impact
- Graceful degradation

**Bulkhead Pattern**:
- Isolate resources by service
- Limit blast radius of attacks
- Prevent resource exhaustion

**Strangler Pattern**:
- Gradual migration to new systems
- Security: Allows incremental security improvements

## 8. Fault Tolerance and Reliability

### 8.1 Failure Detection

**Heartbeat Mechanisms**:
- Periodic ping between nodes
- Timeout-based detection
- Security: Authenticate heartbeats

**Gossip Protocols**:
- Epidemic information dissemination
- Eventually consistent membership
- Security: Encrypt gossip messages, authenticate participants

### 8.2 Recovery Strategies

**Checkpointing**:
- Periodic state snapshots
- Security: Encrypt checkpoint data
- Tamper-proof checkpoint verification

**Logging and Replay**:
- Record operations for replay
- Security: Secure log storage
- Prevent log tampering with signatures

**Rollback Recovery**:
- Return to previous consistent state
- Security: Verify state integrity before rollback

### 8.3 Redundancy

**Active Replication**:
- All replicas process requests
- Higher availability
- Security: Requires Byzantine fault tolerance for untrusted environments

**Passive Replication**:
- Primary processes, backups standby
- Lower overhead
- Security: Protect failover mechanisms

## 9. Scalability

### 9.1 Horizontal Scaling
Adding more machines to the system.

**Load Balancing**:
- Round robin
- Least connections
- IP hash
- Security: DDoS protection, SSL termination at load balancer

**Sharding**:
- Data partitioning across nodes
- Hash-based, range-based, or directory-based
- Security: Ensure cross-shard queries are authorized

### 9.2 Vertical Scaling
Adding resources to existing machines.

**Limitations**:
- Hardware limits
- Single point of failure
- Security: Easier to secure but higher impact if compromised

### 9.3 Caching

**Distributed Caches**:
- Redis Cluster
- Memcached
- Hazelcast

**Cache Patterns**:
- Cache-aside
- Write-through
- Write-behind
- Refresh-ahead

**Security Concerns**:
- Cache poisoning attacks
- Sensitive data in cache
- Encrypt cached data
- Implement cache ACLs
- Short TTLs for sensitive data
- Secure cache eviction policies

## 10. Monitoring and Observability

### 10.1 Logging

**Centralized Logging**:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Datadog
- Graylog

**Security Logging**:
- Authentication attempts
- Authorization failures
- Configuration changes
- Anomalous behavior
- Data access patterns

**Best Practices**:
- Encrypt logs in transit and at rest
- Tamper-proof logging (write-once)
- Log retention policies
- PII redaction
- Separate security logs
- SIEM integration

### 10.2 Metrics

**Key Metrics**:
- Request rate
- Error rate
- Latency (p50, p95, p99)
- Saturation (CPU, memory, disk)

**Security Metrics**:
- Failed authentication attempts
- Rate of authorization denials
- Unusual traffic patterns
- Certificate expiration warnings
- Vulnerability scan results

**Tools**:
- Prometheus + Grafana
- InfluxDB
- CloudWatch
- New Relic

### 10.3 Tracing

**Distributed Tracing**:
- Jaeger
- Zipkin
- AWS X-Ray
- OpenTelemetry

**Security Benefits**:
- Track requests across services
- Identify unusual patterns
- Forensics after incidents
- Compliance auditing

**Security Considerations**:
- Sanitize sensitive data in traces
- Access control for trace data
- Encrypt trace data

### 10.4 Alerting

**Alert Types**:
- Threshold-based
- Anomaly detection
- Predictive alerts

**Security Alerts**:
- Multiple failed logins
- Privilege escalation attempts
- Unusual data access
- Configuration drift
- Certificate expiration
- DDoS indicators
- Compliance violations

## 11. Security Threats and Mitigations

### 11.1 Common Attacks

**Distributed Denial of Service (DDoS)**:
- Overwhelm system with traffic
- Mitigations:
  - Rate limiting
  - DDoS protection services
  - Auto-scaling
  - CDN usage
  - Blackholing
  - Anycast networks

**Man-in-the-Middle (MitM)**:
- Intercept communications
- Mitigations:
  - TLS everywhere
  - Certificate pinning
  - mTLS
  - VPN/IPSec

**Replay Attacks**:
- Resend valid messages
- Mitigations:
  - Nonces
  - Timestamps
  - Sequence numbers
  - Token expiration
  - Idempotency keys

**Sybil Attacks**:
- Create multiple fake identities
- Mitigations:
  - Proof of work
  - Reputation systems
  - Identity verification
  - Resource constraints

**Byzantine Attacks**:
- Malicious nodes send conflicting information
- Mitigations:
  - BFT consensus algorithms
  - Cryptographic verification
  - Redundancy (3f+1 nodes)

**Injection Attacks**:
- SQL injection, NoSQL injection, command injection
- Mitigations:
  - Parameterized queries
  - Input validation
  - Principle of least privilege
  - WAF rules

**Insider Threats**:
- Malicious or negligent employees
- Mitigations:
  - Principle of least privilege
  - Separation of duties
  - Audit logging
  - Background checks
  - Data loss prevention (DLP)

### 11.2 Supply Chain Security

**Dependency Management**:
- Vulnerability scanning (Snyk, OWASP Dependency-Check)
- Software composition analysis
- Private artifact repositories
- Dependency pinning

**Container Security**:
- Image scanning (Trivy, Clair)
- Minimal base images
- Non-root containers
- Read-only file systems
- Image signing (Docker Content Trust)
- Registry security

**Infrastructure as Code Security**:
- Secret scanning
- Policy as code (OPA)
- Terraform/CloudFormation security scanning
- Version control for all infrastructure

## 12. Compliance and Governance

### 12.1 Regulatory Requirements

**GDPR (General Data Protection Regulation)**:
- Data protection by design
- Right to erasure
- Data portability
- Breach notification
- Privacy impact assessments

**HIPAA (Health Insurance Portability)**:
- PHI protection
- Access controls
- Audit trails
- Encryption requirements
- Business associate agreements

**PCI DSS (Payment Card Industry)**:
- Cardholder data protection
- Network segmentation
- Encryption requirements
- Access control
- Regular security testing

**SOC 2**:
- Security
- Availability
- Processing integrity
- Confidentiality
- Privacy

### 12.2 Audit and Compliance

**Audit Trails**:
- Immutable logs
- Who, what, when, where
- Tamper-proof storage
- Long-term retention

**Compliance Automation**:
- Continuous compliance monitoring
- Policy enforcement
- Configuration management
- Automated reporting

**Access Reviews**:
- Regular permission audits
- Certification workflows
- Automated deprovisioning
- Privileged access management

## 13. Testing Distributed Systems

### 13.1 Testing Strategies

**Unit Testing**:
- Test individual components
- Mock external dependencies

**Integration Testing**:
- Test component interactions
- Use test doubles for external services

**End-to-End Testing**:
- Test complete workflows
- Production-like environment

**Chaos Engineering**:
- Netflix's Chaos Monkey
- Inject failures deliberately
- Test resilience and recovery
- Security chaos: Test security controls under stress

### 13.2 Security Testing

**Static Application Security Testing (SAST)**:
- Analyze source code
- Find vulnerabilities before deployment
- Tools: SonarQube, Checkmarx

**Dynamic Application Security Testing (DAST)**:
- Test running applications
- Black-box testing
- Tools: OWASP ZAP, Burp Suite

**Interactive Application Security Testing (IAST)**:
- Combines SAST and DAST
- Real-time analysis during testing

**Penetration Testing**:
- Simulate real attacks
- Red team exercises
- Regular assessments
- Bug bounty programs

**Fuzzing**:
- Send malformed inputs
- Discover crashes and vulnerabilities
- Tools: AFL, libFuzzer

## 14. DevSecOps

### 14.1 Security in CI/CD

**Pipeline Security**:
- Secure pipeline configuration
- Secrets management (HashiCorp Vault)
- Pipeline as code
- Audit pipeline changes

**Security Gates**:
- SAST scans
- Dependency checks
- Container scanning
- Infrastructure scanning
- Manual security reviews for high-risk changes

**Shift Left Security**:
- Security early in development
- Developer security training
- IDE security plugins
- Pre-commit hooks

### 14.2 Infrastructure Security

**Immutable Infrastructure**:
- Never modify, only replace
- Reduces configuration drift
- Easier to audit
- Blue-green deployments

**Infrastructure as Code**:
- Version controlled
- Code review process
- Automated testing
- Consistent deployments

**Secrets Management**:
- Never hard-code secrets
- Environment variables or secret stores
- Rotation policies
- Access logging

## 15. Best Practices Summary

### 15.1 Design Principles

1. **Defense in Depth**: Multiple layers of security
2. **Least Privilege**: Minimum necessary permissions
3. **Fail Securely**: Default deny, secure failure modes
4. **Separation of Duties**: No single person has complete control
5. **Keep it Simple**: Complexity is the enemy of security
6. **Zero Trust**: Verify everything, trust nothing
7. **Privacy by Design**: Build privacy in from the start

### 15.2 Operational Security

1. **Patch Management**: Regular updates, vulnerability management
2. **Incident Response**: Prepared plan, regular drills
3. **Backup and Recovery**: Regular backups, tested recovery
4. **Security Training**: Regular training for all personnel
5. **Threat Modeling**: Identify and prioritize threats
6. **Red Team Exercises**: Test defenses regularly
7. **Metrics and KPIs**: Measure security posture

### 15.3 Development Security

1. **Secure Coding Standards**: Follow OWASP guidelines
2. **Code Review**: Security-focused reviews
3. **Dependency Management**: Keep dependencies updated
4. **Security Testing**: Automated and manual testing
5. **Threat Modeling**: Design-phase security analysis
6. **Security Champions**: Embedded security expertise
7. **Bug Bounty Programs**: External security research

## 16. Emerging Trends

### 16.1 Service Mesh
- Istio, Linkerd, Consul
- Automatic mTLS
- Traffic management
- Observability
- Policy enforcement

### 16.2 Serverless Security
- Function-level permissions
- Short-lived execution
- API Gateway security
- Event source validation
- Cold start considerations

### 16.3 Edge Computing
- Processing closer to users
- Reduced latency
- Security challenges: distributed attack surface
- Content delivery networks (CDNs)

### 16.4 Blockchain and DLT
- Distributed ledger technology
- Immutable audit trails
- Decentralized identity
- Smart contract security

### 16.5 Confidential Computing
- Hardware-based trusted execution environments
- Intel SGX, AMD SEV, ARM TrustZone
- Encrypted data in use
- Attestation mechanisms

## Conclusion

Distributed systems present unique security challenges due to their inherent complexity, multiple points of failure, and attack surfaces. A comprehensive security strategy must address:

- **Authentication and authorization** at every layer
- **Encryption** for data at rest, in transit, and in use
- **Monitoring and alerting** for security events
- **Resilience** against various attack vectors
- **Compliance** with regulatory requirements
- **Continuous improvement** through testing and updates

Security in distributed systems is not a one-time effort but an ongoing process requiring vigilance, automation, and a culture of security awareness throughout the organization. The key is to build security into the architecture from the beginning rather than bolting it on later, following defense-in-depth principles and maintaining a zero-trust mindset.

# Distributed Systems Implementations in Rust, Go, and Python

## 1. Language-Specific Strengths for Distributed Systems

### Rust
**Strengths:**
- Memory safety without garbage collection
- Zero-cost abstractions
- Fearless concurrency
- Performance comparable to C/C++
- Strong type system prevents many bugs at compile time

**Use Cases:**
- High-performance services
- Systems programming
- Network protocols
- Consensus algorithms
- Critical infrastructure

### Go
**Strengths:**
- Built-in concurrency (goroutines, channels)
- Fast compilation
- Simple syntax
- Excellent standard library for networking
- Great tooling ecosystem

**Use Cases:**
- Microservices
- API servers
- Network tools
- Cloud infrastructure
- Container orchestration

### Python
**Strengths:**
- Rapid development
- Rich ecosystem
- Easy to learn
- Excellent for prototyping
- Data processing capabilities

**Use Cases:**
- Data pipelines
- Machine learning services
- Automation
- Scripting
- API development

---

## 2. Core Distributed Systems Implementations

### 2.1 HTTP Servers### 2.2 gRPC Implementations

// Cargo.toml dependencies:
// [dependencies]
// actix-web = "4.4"
// actix-web-httpauth = "0.8"
// serde = { version = "1.0", features = ["derive"] }
// jsonwebtoken = "9.2"
// tokio = { version = "1.35", features = ["full"] }
// env_logger = "0.11"
// bcrypt = "0.15"

use actix_web::{
    web, App, HttpServer, HttpResponse, HttpRequest, Error,
    middleware::{Logger, Compress},
};
use actix_web_httpauth::extractors::bearer::BearerAuth;
use serde::{Deserialize, Serialize};
use jsonwebtoken::{encode, decode, Header, Validation, EncodingKey, DecodingKey};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: usize,
    iat: usize,
}

#[derive(Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Serialize)]
struct LoginResponse {
    token: String,
}

const SECRET_KEY: &[u8] = b"your-secret-key-change-in-production";

// Middleware for JWT validation
async fn validate_token(auth: BearerAuth) -> Result<String, Error> {
    let token = auth.token();
    
    match decode::<Claims>(
        token,
        &DecodingKey::from_secret(SECRET_KEY),
        &Validation::default(),
    ) {
        Ok(token_data) => Ok(token_data.claims.sub),
        Err(_) => Err(actix_web::error::ErrorUnauthorized("Invalid token")),
    }
}

// Login endpoint
async fn login(credentials: web::Json<LoginRequest>) -> Result<HttpResponse, Error> {
    // In production, verify against database with bcrypt
    if credentials.username == "admin" && credentials.password == "password" {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as usize;
        
        let claims = Claims {
            sub: credentials.username.clone(),
            exp: now + 3600, // 1 hour expiration
            iat: now,
        };
        
        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(SECRET_KEY),
        )
        .map_err(|_| actix_web::error::ErrorInternalServerError("Token generation failed"))?;
        
        Ok(HttpResponse::Ok().json(LoginResponse { token }))
    } else {
        Err(actix_web::error::ErrorUnauthorized("Invalid credentials"))
    }
}

// Protected endpoint
async fn protected_route(
    _req: HttpRequest,
    auth: BearerAuth,
) -> Result<HttpResponse, Error> {
    let username = validate_token(auth).await?;
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "message": format!("Hello, {}!", username),
        "timestamp": SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs()
    })))
}

// Health check endpoint
async fn health_check() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "healthy",
        "timestamp": SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs()
    }))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::new().default_filter_or("info"));
    
    println!("🚀 Starting secure Rust HTTP server on http://127.0.0.1:8080");
    
    HttpServer::new(|| {
        App::new()
            .wrap(Logger::default())
            .wrap(Compress::default())
            // Security headers middleware
            .wrap(actix_web::middleware::DefaultHeaders::new()
                .add(("X-Content-Type-Options", "nosniff"))
                .add(("X-Frame-Options", "DENY"))
                .add(("X-XSS-Protection", "1; mode=block"))
                .add(("Strict-Transport-Security", "max-age=31536000; includeSubDomains")))
            .route("/health", web::get().to(health_check))
            .route("/login", web::post().to(login))
            .route("/protected", web::get().to(protected_route))
    })
    .bind(("127.0.0.1", 8080))?
    .workers(4)
    .run()
    .await
}

// user_service.proto
syntax = "proto3";

package user;

service UserService {
  rpc GetUser (GetUserRequest) returns (UserResponse);
  rpc CreateUser (CreateUserRequest) returns (UserResponse);
  rpc ListUsers (ListUsersRequest) returns (stream UserResponse);
  rpc AuthenticateUser (AuthRequest) returns (AuthResponse);
}

message GetUserRequest {
  string user_id = 1;
}

message CreateUserRequest {
  string username = 1;
  string email = 2;
  string password = 3;
}

message ListUsersRequest {
  int32 page = 1;
  int32 page_size = 2;
}

message UserResponse {
  string user_id = 1;
  string username = 2;
  string email = 3;
  int64 created_at = 4;
}

message AuthRequest {
  string username = 1;
  string password = 2;
}

message AuthResponse {
  string token = 1;
  int64 expires_at = 2;
}

// ===============================
// RUST IMPLEMENTATION (Tonic)
// ===============================

// Cargo.toml
// [dependencies]
// tonic = "0.10"
// tokio = { version = "1", features = ["macros", "rt-multi-thread"] }
// prost = "0.12"
// tokio-stream = "0.1"
// uuid = { version = "1.6", features = ["v4"] }
// 
// [build-dependencies]
// tonic-build = "0.10"

// src/main.rs (Rust gRPC Server)
use tonic::{transport::Server, Request, Response, Status};
use tokio_stream::wrappers::ReceiverStream;
use std::pin::Pin;
use uuid::Uuid;

pub mod user {
    tonic::include_proto!("user");
}

use user::{
    user_service_server::{UserService, UserServiceServer},
    GetUserRequest, CreateUserRequest, ListUsersRequest,
    UserResponse, AuthRequest, AuthResponse,
};

#[derive(Debug, Default)]
pub struct UserServiceImpl {}

#[tonic::async_trait]
impl UserService for UserServiceImpl {
    async fn get_user(
        &self,
        request: Request<GetUserRequest>,
    ) -> Result<Response<UserResponse>, Status> {
        let req = request.into_inner();
        
        // Simulate database lookup with authentication check
        if req.user_id.is_empty() {
            return Err(Status::invalid_argument("User ID cannot be empty"));
        }

        let user = UserResponse {
            user_id: req.user_id,
            username: "john_doe".to_string(),
            email: "john@example.com".to_string(),
            created_at: 1640000000,
        };

        Ok(Response::new(user))
    }

    async fn create_user(
        &self,
        request: Request<CreateUserRequest>,
    ) -> Result<Response<UserResponse>, Status> {
        let req = request.into_inner();
        
        // Input validation
        if req.username.len() < 3 {
            return Err(Status::invalid_argument("Username too short"));
        }
        
        if !req.email.contains('@') {
            return Err(Status::invalid_argument("Invalid email"));
        }

        let user = UserResponse {
            user_id: Uuid::new_v4().to_string(),
            username: req.username,
            email: req.email,
            created_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs() as i64,
        };

        Ok(Response::new(user))
    }

    type ListUsersStream = ReceiverStream<Result<UserResponse, Status>>;

    async fn list_users(
        &self,
        request: Request<ListUsersRequest>,
    ) -> Result<Response<Self::ListUsersStream>, Status> {
        let req = request.into_inner();
        let (tx, rx) = tokio::sync::mpsc::channel(4);

        tokio::spawn(async move {
            // Simulate streaming users from database
            for i in 0..req.page_size {
                let user = UserResponse {
                    user_id: Uuid::new_v4().to_string(),
                    username: format!("user_{}", i),
                    email: format!("user{}@example.com", i),
                    created_at: 1640000000 + i as i64,
                };

                if tx.send(Ok(user)).await.is_err() {
                    break;
                }

                tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            }
        });

        Ok(Response::new(ReceiverStream::new(rx)))
    }

    async fn authenticate_user(
        &self,
        request: Request<AuthRequest>,
    ) -> Result<Response<AuthResponse>, Status> {
        let req = request.into_inner();
        
        // Simulate authentication (use bcrypt in production)
        if req.username == "admin" && req.password == "password" {
            let token = format!("token_{}", Uuid::new_v4());
            let expires_at = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs() as i64 + 3600;

            Ok(Response::new(AuthResponse { token, expires_at }))
        } else {
            Err(Status::unauthenticated("Invalid credentials"))
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let user_service = UserServiceImpl::default();

    println!("🚀 Rust gRPC Server listening on {}", addr);

    Server::builder()
        .add_service(UserServiceServer::new(user_service))
        .serve(addr)
        .await?;

    Ok(())
}

// ===============================
// GO IMPLEMENTATION
// ===============================

// go.mod
// module userservice
// go 1.21
// require (
//     google.golang.org/grpc v1.60.0
//     google.golang.org/protobuf v1.32.0
// )

// main.go
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	pb "userservice/proto"
)

type server struct {
	pb.UnimplementedUserServiceServer
}

func (s *server) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.UserResponse, error) {
	if req.UserId == "" {
		return nil, status.Error(codes.InvalidArgument, "User ID cannot be empty")
	}

	log.Printf("GetUser called for ID: %s", req.UserId)

	return &pb.UserResponse{
		UserId:    req.UserId,
		Username:  "john_doe",
		Email:     "john@example.com",
		CreatedAt: time.Now().Unix(),
	}, nil
}

func (s *server) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.UserResponse, error) {
	if len(req.Username) < 3 {
		return nil, status.Error(codes.InvalidArgument, "Username too short")
	}

	if req.Email == "" || !contains(req.Email, "@") {
		return nil, status.Error(codes.InvalidArgument, "Invalid email")
	}

	log.Printf("CreateUser called for username: %s", req.Username)

	return &pb.UserResponse{
		UserId:    generateUUID(),
		Username:  req.Username,
		Email:     req.Email,
		CreatedAt: time.Now().Unix(),
	}, nil
}

func (s *server) ListUsers(req *pb.ListUsersRequest, stream pb.UserService_ListUsersServer) error {
	log.Printf("ListUsers called - Page: %d, PageSize: %d", req.Page, req.PageSize)

	for i := int32(0); i < req.PageSize; i++ {
		user := &pb.UserResponse{
			UserId:    generateUUID(),
			Username:  fmt.Sprintf("user_%d", i),
			Email:     fmt.Sprintf("user%d@example.com", i),
			CreatedAt: time.Now().Unix() + int64(i),
		}

		if err := stream.Send(user); err != nil {
			return err
		}

		time.Sleep(100 * time.Millisecond)
	}

	return nil
}

func (s *server) AuthenticateUser(ctx context.Context, req *pb.AuthRequest) (*pb.AuthResponse, error) {
	log.Printf("Authentication attempt for user: %s", req.Username)

	// Simulate authentication (use proper password hashing in production)
	if req.Username == "admin" && req.Password == "password" {
		return &pb.AuthResponse{
			Token:     fmt.Sprintf("token_%s", generateUUID()),
			ExpiresAt: time.Now().Add(1 * time.Hour).Unix(),
		}, nil
	}

	return nil, status.Error(codes.Unauthenticated, "Invalid credentials")
}

func contains(s, substr string) bool {
	return len(s) > 0 && len(substr) > 0 && s != substr && 
		   (s[0:len(substr)] == substr || s[len(s)-len(substr):] == substr || 
		   len(s) > len(substr))
}

func generateUUID() string {
	return fmt.Sprintf("%d-%d", time.Now().UnixNano(), time.Now().Unix())
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	s := grpc.NewServer(
		grpc.MaxRecvMsgSize(4 * 1024 * 1024), // 4MB
		grpc.MaxSendMsgSize(4 * 1024 * 1024),
	)
	
	pb.RegisterUserServiceServer(s, &server{})

	log.Println("🚀 Go gRPC Server listening on :50051")
	
	if err := s.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}

// ===============================
// PYTHON IMPLEMENTATION
// ===============================

# requirements.txt
# grpcio==1.60.0
# grpcio-tools==1.60.0
# protobuf==4.25.1

# user_service_server.py
import grpc
from concurrent import futures
import logging
import time
import uuid
from typing import Iterator

import user_pb2
import user_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
    
    def GetUser(self, request, context):
        """Get a single user by ID"""
        if not request.user_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "User ID cannot be empty")
        
        logger.info(f"GetUser called for ID: {request.user_id}")
        
        return user_pb2.UserResponse(
            user_id=request.user_id,
            username="john_doe",
            email="john@example.com",
            created_at=int(time.time())
        )
    
    def CreateUser(self, request, context):
        """Create a new user"""
        if len(request.username) < 3:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Username too short")
        
        if '@' not in request.email:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid email")
        
        logger.info(f"CreateUser called for username: {request.username}")
        
        return user_pb2.UserResponse(
            user_id=str(uuid.uuid4()),
            username=request.username,
            email=request.email,
            created_at=int(time.time())
        )
    
    def ListUsers(self, request, context):
        """Stream a list of users"""
        logger.info(f"ListUsers called - Page: {request.page}, PageSize: {request.page_size}")
        
        for i in range(request.page_size):
            yield user_pb2.UserResponse(
                user_id=str(uuid.uuid4()),
                username=f"user_{i}",
                email=f"user{i}@example.com",
                created_at=int(time.time()) + i
            )
            time.sleep(0.1)  # Simulate processing time
    
    def AuthenticateUser(self, request, context):
        """Authenticate a user"""
        logger.info(f"Authentication attempt for user: {request.username}")
        
        # Simulate authentication (use proper password hashing in production)
        if request.username == "admin" and request.password == "password":
            return user_pb2.AuthResponse(
                token=f"token_{uuid.uuid4()}",
                expires_at=int(time.time()) + 3600  # 1 hour
            )
        
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid credentials")

def serve():
    """Start the gRPC server"""
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 4 * 1024 * 1024),  # 4MB
            ('grpc.max_receive_message_length', 4 * 1024 * 1024),
        ]
    )
    
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    
    server.add_insecure_port('[::]:50051')
    server.start()
    
    logger.info("🚀 Python gRPC Server listening on :50051")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop(0)

if __name__ == '__main__':
    serve()

# Generate Python code from proto:
# python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. user_service.proto

// ===============================
// RUST - RabbitMQ Implementation
// ===============================

// Cargo.toml
// [dependencies]
// lapin = "2.3"
// tokio = { version = "1", features = ["full"] }
// serde = { version = "1.0", features = ["derive"] }
// serde_json = "1.0"
// tracing = "0.1"
// tracing-subscriber = "0.3"

use lapin::{
    options::*, types::FieldTable, BasicProperties, Connection,
    ConnectionProperties, Result as LapinResult,
};
use serde::{Deserialize, Serialize};
use tracing::{info, error};

#[derive(Debug, Serialize, Deserialize)]
struct OrderMessage {
    order_id: String,
    user_id: String,
    amount: f64,
    timestamp: i64,
}

// RabbitMQ Producer
async fn rabbitmq_producer() -> LapinResult<()> {
    let addr = "amqp://guest:guest@localhost:5672/%2f";
    let conn = Connection::connect(addr, ConnectionProperties::default()).await?;
    let channel = conn.create_channel().await?;

    // Declare exchange
    channel.exchange_declare(
        "orders_exchange",
        lapin::ExchangeKind::Topic,
        ExchangeDeclareOptions {
            durable: true,
            ..Default::default()
        },
        FieldTable::default(),
    ).await?;

    // Declare queue
    channel.queue_declare(
        "orders_queue",
        QueueDeclareOptions {
            durable: true,
            ..Default::default()
        },
        FieldTable::default(),
    ).await?;

    // Bind queue to exchange
    channel.queue_bind(
        "orders_queue",
        "orders_exchange",
        "order.created",
        QueueBindOptions::default(),
        FieldTable::default(),
    ).await?;

    // Publish messages
    for i in 0..10 {
        let message = OrderMessage {
            order_id: format!("order_{}", i),
            user_id: format!("user_{}", i),
            amount: 100.0 * (i as f64),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs() as i64,
        };

        let payload = serde_json::to_vec(&message)?;
        
        channel.basic_publish(
            "orders_exchange",
            "order.created",
            BasicPublishOptions::default(),
            &payload,
            BasicProperties::default()
                .with_content_type("application/json".into())
                .with_delivery_mode(2), // Persistent
        ).await?;

        info!("Published order: {}", message.order_id);
        tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
    }

    Ok(())
}

// RabbitMQ Consumer
async fn rabbitmq_consumer() -> LapinResult<()> {
    let addr = "amqp://guest:guest@localhost:5672/%2f";
    let conn = Connection::connect(addr, ConnectionProperties::default()).await?;
    let channel = conn.create_channel().await?;

    channel.basic_qos(10, BasicQosOptions::default()).await?;

    let mut consumer = channel.basic_consume(
        "orders_queue",
        "order_consumer",
        BasicConsumeOptions::default(),
        FieldTable::default(),
    ).await?;

    info!("Waiting for messages...");

    while let Some(delivery) = consumer.next().await {
        match delivery {
            Ok(delivery) => {
                match serde_json::from_slice::<OrderMessage>(&delivery.data) {
                    Ok(order) => {
                        info!("Received order: {:?}", order);
                        
                        // Process order (simulate work)
                        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
                        
                        // Acknowledge message
                        delivery.ack(BasicAckOptions::default()).await?;
                    }
                    Err(e) => {
                        error!("Failed to deserialize message: {}", e);
                        delivery.nack(BasicNackOptions {
                            requeue: false,
                            ..Default::default()
                        }).await?;
                    }
                }
            }
            Err(e) => {
                error!("Consumer error: {}", e);
                break;
            }
        }
    }

    Ok(())
}

// ===============================
// GO - Kafka Implementation
// ===============================

// go.mod
// module kafkaservice
// go 1.21
// require github.com/segmentio/kafka-go v0.4.47

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/segmentio/kafka-go"
)

type OrderEvent struct {
	OrderID   string  `json:"order_id"`
	UserID    string  `json:"user_id"`
	Amount    float64 `json:"amount"`
	Timestamp int64   `json:"timestamp"`
}

// Kafka Producer
func kafkaProducer() {
	writer := kafka.NewWriter(kafka.WriterConfig{
		Brokers:          []string{"localhost:9092"},
		Topic:            "orders",
		Balancer:         &kafka.LeastBytes{},
		CompressionCodec: kafka.Snappy.Codec(),
		RequiredAcks:     kafka.RequireAll, // Wait for all replicas
		MaxAttempts:      3,
		BatchSize:        100,
		BatchTimeout:     10 * time.Millisecond,
	})
	defer writer.Close()

	ctx := context.Background()

	for i := 0; i < 10; i++ {
		order := OrderEvent{
			OrderID:   fmt.Sprintf("order_%d", i),
			UserID:    fmt.Sprintf("user_%d", i),
			Amount:    100.0 * float64(i),
			Timestamp: time.Now().Unix(),
		}

		payload, err := json.Marshal(order)
		if err != nil {
			log.Printf("Failed to marshal order: %v", err)
			continue
		}

		err = writer.WriteMessages(ctx, kafka.Message{
			Key:   []byte(order.OrderID),
			Value: payload,
			Headers: []kafka.Header{
				{Key: "content-type", Value: []byte("application/json")},
			},
			Time: time.Now(),
		})

		if err != nil {
			log.Printf("Failed to write message: %v", err)
			continue
		}

		log.Printf("Published order: %s", order.OrderID)
		time.Sleep(500 * time.Millisecond)
	}
}

// Kafka Consumer
func kafkaConsumer() {
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:         []string{"localhost:9092"},
		Topic:           "orders",
		GroupID:         "order-processor",
		MinBytes:        10e3, // 10KB
		MaxBytes:        10e6, // 10MB
		MaxWait:         1 * time.Second,
		CommitInterval:  1 * time.Second,
		StartOffset:     kafka.LastOffset,
		SessionTimeout:  30 * time.Second,
		HeartbeatInterval: 3 * time.Second,
	})
	defer reader.Close()

	ctx := context.Background()

	log.Println("Waiting for messages...")

	for {
		msg, err := reader.ReadMessage(ctx)
		if err != nil {
			log.Printf("Error reading message: %v", err)
			continue
		}

		var order OrderEvent
		if err := json.Unmarshal(msg.Value, &order); err != nil {
			log.Printf("Failed to unmarshal message: %v", err)
			continue
		}

		log.Printf("Received order: %+v (Partition: %d, Offset: %d)",
			order, msg.Partition, msg.Offset)

		// Process order (simulate work)
		time.Sleep(100 * time.Millisecond)

		// Message is automatically committed based on CommitInterval
	}
}

// Kafka Consumer with Manual Commit
func kafkaConsumerManualCommit() {
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers: []string{"localhost:9092"},
		Topic:   "orders",
		GroupID: "order-processor-manual",
	})
	defer reader.Close()

	ctx := context.Background()

	for {
		msg, err := reader.FetchMessage(ctx)
		if err != nil {
			log.Printf("Error fetching message: %v", err)
			continue
		}

		var order OrderEvent
		if err := json.Unmarshal(msg.Value, &order); err != nil {
			log.Printf("Failed to unmarshal message: %v", err)
			continue
		}

		log.Printf("Processing order: %+v", order)

		// Process order
		if err := processOrder(&order); err != nil {
			log.Printf("Failed to process order: %v", err)
			continue
		}

		// Commit only after successful processing
		if err := reader.CommitMessages(ctx, msg); err != nil {
			log.Printf("Failed to commit message: %v", err)
		}
	}
}

func processOrder(order *OrderEvent) error {
	time.Sleep(100 * time.Millisecond)
	log.Printf("Order %s processed successfully", order.OrderID)
	return nil
}

func main() {
	// Run producer in one goroutine
	go kafkaProducer()

	// Run consumer in another goroutine
	go kafkaConsumer()

	// Keep the program running
	select {}
}

// ===============================
// PYTHON - RabbitMQ & Kafka
// ===============================

# requirements.txt
# pika==1.3.2
# kafka-python==2.0.2

import pika
import json
import time
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== RabbitMQ ===========

class RabbitMQProducer:
    def __init__(self, host='localhost', exchange='orders_exchange'):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host)
        )
        self.channel = self.connection.channel()
        self.exchange = exchange
        
        # Declare exchange
        self.channel.exchange_declare(
            exchange=self.exchange,
            exchange_type='topic',
            durable=True
        )
        
        # Declare queue
        self.channel.queue_declare(queue='orders_queue', durable=True)
        
        # Bind queue to exchange
        self.channel.queue_bind(
            exchange=self.exchange,
            queue='orders_queue',
            routing_key='order.created'
        )
    
    def publish(self, message, routing_key='order.created'):
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type='application/json'
            )
        )
        logger.info(f"Published order: {message['order_id']}")
    
    def close(self):
        self.connection.close()

class RabbitMQConsumer:
    def __init__(self, host='localhost', queue='orders_queue'):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host)
        )
        self.channel = self.connection.channel()
        self.queue = queue
        
        self.channel.basic_qos(prefetch_count=10)
    
    def callback(self, ch, method, properties, body):
        try:
            order = json.loads(body)
            logger.info(f"Received order: {order}")
            
            # Process order (simulate work)
            time.sleep(0.1)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        self.channel.basic_consume(
            queue=self.queue,
            on_message_callback=self.callback
        )
        logger.info("Waiting for messages...")
        self.channel.start_consuming()
    
    def close(self):
        self.connection.close()

# ========== Kafka ===========

class KafkaProducerWrapper:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='snappy',
            acks='all',  # Wait for all replicas
            retries=3,
            max_in_flight_requests_per_connection=5
        )
    
    def send_order(self, topic, order):
        try:
            future = self.producer.send(
                topic,
                key=order['order_id'].encode('utf-8'),
                value=order,
                headers=[('content-type', b'application/json')]
            )
            
            # Wait for acknowledgment
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Published order: {order['order_id']} "
                f"(Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset})"
            )
        except KafkaError as e:
            logger.error(f"Failed to send message: {e}")
    
    def close(self):
        self.producer.flush()
        self.producer.close()

class KafkaConsumerWrapper:
    def __init__(self, bootstrap_servers=['localhost:9092'], 
                 topic='orders', group_id='order-processor'):
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
            session_timeout_ms=30000,
            max_poll_records=100
        )
    
    def start_consuming(self):
        logger.info("Waiting for messages...")
        try:
            for message in self.consumer:
                order = message.value
                logger.info(
                    f"Received order: {order} "
                    f"(Partition: {message.partition}, Offset: {message.offset})"
                )
                
                # Process order
                self.process_order(order)
        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
        finally:
            self.consumer.close()
    
    def process_order(self, order):
        time.sleep(0.1)
        logger.info(f"Order {order['order_id']} processed successfully")

# Example usage
if __name__ == '__main__':
    # RabbitMQ Producer example
    rabbitmq_producer = RabbitMQProducer()
    for i in range(10):
        order = {
            'order_id': f'order_{i}',
            'user_id': f'user_{i}',
            'amount': 100.0 * i,
            'timestamp': int(time.time())
        }
        rabbitmq_producer.publish(order)
        time.sleep(0.5)
    rabbitmq_producer.close()
    
    # Kafka Producer example
    kafka_producer = KafkaProducerWrapper()
    for i in range(10):
        order = {
            'order_id': f'order_{i}',
            'user_id': f'user_{i}',
            'amount': 100.0 * i,
            'timestamp': int(time.time())
        }
        kafka_producer.send_order('orders', order)
        time.sleep(0.5)
    kafka_producer.close()

// ===============================
// RUST - Redis Implementation
// ===============================

// Cargo.toml
// [dependencies]
// redis = { version = "0.24", features = ["tokio-comp", "connection-manager"] }
// tokio = { version = "1", features = ["full"] }
// serde = { version = "1.0", features = ["derive"] }
// serde_json = "1.0"

use redis::{aio::ConnectionManager, AsyncCommands, RedisResult};
use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Debug, Serialize, Deserialize)]
struct User {
    id: String,
    username: String,
    email: String,
}

#[derive(Clone)]
struct RedisCache {
    client: ConnectionManager,
}

impl RedisCache {
    async fn new(redis_url: &str) -> RedisResult<Self> {
        let client = redis::Client::open(redis_url)?;
        let manager = ConnectionManager::new(client).await?;
        Ok(Self { client: manager })
    }

    // Set key-value with expiration
    async fn set_with_expiry<T: Serialize>(
        &mut self,
        key: &str,
        value: &T,
        ttl_seconds: usize,
    ) -> RedisResult<()> {
        let serialized = serde_json::to_string(value)
            .map_err(|e| redis::RedisError::from((
                redis::ErrorKind::TypeError,
                "Serialization failed",
                e.to_string(),
            )))?;
        
        self.client.set_ex(key, serialized, ttl_seconds).await
    }

    // Get value by key
    async fn get<T: for<'de> Deserialize<'de>>(
        &mut self,
        key: &str,
    ) -> RedisResult<Option<T>> {
        let value: Option<String> = self.client.get(key).await?;
        
        match value {
            Some(v) => {
                let deserialized = serde_json::from_str(&v)
                    .map_err(|e| redis::RedisError::from((
                        redis::ErrorKind::TypeError,
                        "Deserialization failed",
                        e.to_string(),
                    )))?;
                Ok(Some(deserialized))
            }
            None => Ok(None),
        }
    }

    // Delete key
    async fn delete(&mut self, key: &str) -> RedisResult<()> {
        self.client.del(key).await
    }

    // Check if key exists
    async fn exists(&mut self, key: &str) -> RedisResult<bool> {
        self.client.exists(key).await
    }

    // Increment counter
    async fn increment(&mut self, key: &str) -> RedisResult<i64> {
        self.client.incr(key, 1).await
    }

    // Set with NX (only if not exists)
    async fn set_nx(&mut self, key: &str, value: &str, ttl: usize) -> RedisResult<bool> {
        let result: Option<String> = redis::cmd("SET")
            .arg(key)
            .arg(value)
            .arg("NX")
            .arg("EX")
            .arg(ttl)
            .query_async(&mut self.client)
            .await?;
        Ok(result.is_some())
    }

    // Distributed lock implementation
    async fn acquire_lock(&mut self, lock_key: &str, timeout: usize) -> RedisResult<bool> {
        let lock_value = format!("{}", std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis());
        
        self.set_nx(lock_key, &lock_value, timeout).await
    }

    async fn release_lock(&mut self, lock_key: &str) -> RedisResult<()> {
        self.delete(lock_key).await
    }
}

// Cache-aside pattern
struct CacheAsidePattern {
    cache: RedisCache,
}

impl CacheAsidePattern {
    async fn get_user(&mut self, user_id: &str) -> RedisResult<Option<User>> {
        let cache_key = format!("user:{}", user_id);
        
        // Try cache first
        if let Some(user) = self.cache.get::<User>(&cache_key).await? {
            println!("Cache HIT for user: {}", user_id);
            return Ok(Some(user));
        }
        
        println!("Cache MISS for user: {}", user_id);
        
        // Simulate database lookup
        let user = self.fetch_from_database(user_id).await;
        
        if let Some(ref u) = user {
            // Store in cache for 5 minutes
            self.cache.set_with_expiry(&cache_key, u, 300).await?;
        }
        
        Ok(user)
    }

    async fn fetch_from_database(&self, user_id: &str) -> Option<User> {
        // Simulate database call
        tokio::time::sleep(Duration::from_millis(100)).await;
        
        Some(User {
            id: user_id.to_string(),
            username: format!("user_{}", user_id),
            email: format!("user_{}@example.com", user_id),
        })
    }
}

#[tokio::main]
async fn main() -> RedisResult<()> {
    let mut cache = RedisCache::new("redis://127.0.0.1:6379").await?;
    
    // Basic operations