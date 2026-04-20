**Core Infrastructure (Foundational Topics in System Design / SRE Context)**

This covers the underlying platform and operational layer that supports distributed/system-designed applications (often overlapping with SRE practices: treating operations as code, focusing on reliability/observability).

- **Networking & Compute Basics**
  - TCP/IP stack, DNS, Load balancing at infrastructure level, Firewalls/NAT
  - Horizontal/vertical scaling infrastructure

- **Cloud & Modern Infrastructure**
  - Cloud models: IaaS, PaaS, Serverless, Containers
  - Orchestration: Containerization (Docker concepts), Kubernetes (pods, services, auto-scaling)
  - Infrastructure as Code (IaC) principles
  - Hybrid/multi-cloud considerations

- **Storage & Data Infrastructure**
  - Distributed storage fundamentals (object stores, block/file systems)
  - Backup, replication, and disaster recovery at infra level

- **Reliability & Observability (SRE Core)**
  - SLIs, SLOs, Error budgets
  - Monitoring & Observability stack: Metrics, Logs, Traces (e.g., Prometheus, ELK concepts)
  - Incident response, Chaos engineering, Health checks
  - Auto-scaling, Resource management, Toil reduction

- **Security & Operations**
  - Foundational security: Authentication, Encryption, Federated identity, Rate limiting at infra level
  - CI/CD pipelines and deployment strategies
  - High availability infrastructure patterns (redundancy, failover)