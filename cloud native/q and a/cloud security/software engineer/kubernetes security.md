# 100 Senior-Level Cloud Kubernetes Security Interview Questions & Answers

> **Target Audience:** Senior Engineers, Platform Engineers, Security Engineers, DevSecOps, Cloud Architects  
> **Scope:** Kubernetes Security, Cloud-Native Security, Supply Chain, Runtime Defense, Compliance, Zero Trust

---

## Table of Contents

1. [Kubernetes Core Security Primitives](#1-kubernetes-core-security-primitives) (Q1–Q15)
2. [RBAC & Identity](#2-rbac--identity) (Q16–Q25)
3. [Network Security & Policies](#3-network-security--policies) (Q26–Q35)
4. [Pod & Container Security](#4-pod--container-security) (Q36–Q50)
5. [Secrets Management](#5-secrets-management) (Q51–Q58)
6. [Supply Chain & Image Security](#6-supply-chain--image-security) (Q59–Q66)
7. [Runtime Security & Threat Detection](#7-runtime-security--threat-detection) (Q67–Q75)
8. [Cloud Provider IAM & Integration](#8-cloud-provider-iam--integration) (Q76–Q83)
9. [Compliance, Auditing & Governance](#9-compliance-auditing--governance) (Q84–Q91)
10. [Zero Trust & Advanced Architecture](#10-zero-trust--advanced-architecture) (Q92–Q100)

---

## 1. Kubernetes Core Security Primitives

---

### Q1. Explain the Kubernetes API server authentication pipeline. What happens from the moment a request hits the API server to when it is executed?

**Answer:**

Every request to the Kubernetes API server passes through a multi-stage pipeline:

**1. Transport Security (TLS)**  
All communication uses mutual TLS (mTLS). The API server presents its certificate, and clients (kubectl, kubelets, controllers) present theirs. Without a valid cert, the connection is terminated before reaching any auth logic.

**2. Authentication**  
The API server supports multiple authenticators in sequence (first success wins):
- **X.509 client certificates** — The CN becomes the username, O becomes the group.
- **Static token files** — Discouraged; tokens never expire.
- **Bootstrap tokens** — Used during node join (kubeadm).
- **ServiceAccount tokens** — Projected JWTs signed by the API server's private key.
- **OIDC tokens** — External IdP integration (Dex, Okta, Azure AD).
- **Authenticating proxy** — API server trusts header-based identity from an upstream proxy.

If no authenticator succeeds, the request is treated as `system:anonymous`.

**3. Authorization**  
Once authenticated, the request goes through authorization plugins evaluated in order:
- **RBAC** — Role-based rules against verbs, resources, and resource names.
- **ABAC** — Policy files (deprecated in practice).
- **Node** — Special authorizer for kubelet requests.
- **Webhook** — Delegate to an external HTTP service.

**4. Admission Control**  
Mutating admission webhooks run first (they can modify the request), then validating admission webhooks (they can only accept or reject). Built-in controllers like `LimitRanger`, `ResourceQuota`, and `PodSecurity` are admission plugins.

**5. Persistence**  
Approved requests are written to etcd via the storage layer.

**Key insight for seniors:** The Authenticating → Authorizing → Admitting pipeline is sequential and not short-circuited between stages, except that the first successful authenticator wins. Misunderstanding that admission controllers run before authorization is a common mistake.

---

### Q2. What is the threat model for etcd in a Kubernetes cluster, and how do you harden it?

**Answer:**

etcd is the single source of truth for all cluster state — including Secrets. **Compromising etcd is equivalent to compromising the entire cluster.**

**Threat Model:**
- **Direct etcd access** bypasses all Kubernetes RBAC entirely.
- **Unauthenticated etcd** (exposed on port 2379 without client auth) allows any process on the network to read all Secrets, modify any resource, or delete the cluster.
- **Unencrypted data at rest** means a stolen etcd volume exposes all Secrets in plaintext (base64 is not encryption).
- **Etcd peer communication** without mTLS allows MITM between etcd members.

**Hardening Measures:**

1. **mTLS everywhere** — Enable `--client-cert-auth=true` and `--peer-client-cert-auth=true` on all etcd nodes. Generate dedicated client and peer CA chains.

2. **Restrict network access** — etcd should only be reachable by API server nodes. Use firewall rules, security groups, or private subnets. Never expose port 2379 to the internet.

3. **Encryption at rest** — Configure `EncryptionConfiguration` on the API server:

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>
      - identity: {}
```

4. **Prefer KMS over static keys** — Use `kms` provider (AWS KMS, GCP CKMS, Vault) so the encryption key itself never lives on disk.

5. **Dedicated etcd nodes** — Don't run etcd on worker nodes or co-locate with user workloads.

6. **Regular backups with encryption** — Etcd snapshots should be encrypted and stored off-cluster.

7. **Least privilege for API server** — The API server should have a dedicated etcd client certificate with only the permissions it needs.

---

### Q3. Describe how Kubernetes Admission Controllers work. What is the difference between Mutating and Validating webhooks, and what are the security implications of misconfiguring them?

**Answer:**

Admission controllers intercept API server requests after authentication/authorization but before persistence. They are the primary enforcement point for security policy in Kubernetes.

**Mutating Admission Webhooks (MutatingWebhookConfiguration):**
- Run first, in undefined order among multiple webhooks.
- Can modify the incoming request object (e.g., inject sidecars, add labels, set default security contexts).
- Return a JSON Patch to be applied to the object.
- Are called serially with each receiving the result of the previous mutation.

**Validating Admission Webhooks (ValidatingWebhookConfiguration):**
- Run after all mutating webhooks have completed.
- Can only accept or reject — they cannot modify the request.
- All validating webhooks for a given request run in parallel.
- If any reject, the request fails.

**Security implications of misconfiguration:**

1. **`failurePolicy: Ignore`** — If the webhook endpoint is down, the request proceeds without validation. An attacker who can cause your policy webhook to become unavailable can bypass all policy enforcement. Use `failurePolicy: Fail` for security-critical webhooks.

2. **Broad `namespaceSelector`** — If a webhook applies to all namespaces including `kube-system`, you risk breaking critical system components. Conversely, if it excludes namespaces too broadly, workloads escape policy.

3. **Webhook endpoint security** — The API server calls your webhook over HTTPS. A webhook without TLS, or with a self-signed cert not validated by `caBundle`, is a MITM vector. Kube-rbac-proxy is commonly used to front webhooks.

4. **Unbounded timeout** — Slow or unresponsive webhooks block the API server. Set `timeoutSeconds` appropriately.

5. **Privilege escalation through mutation** — A poorly secured MutatingWebhookConfiguration can be used to inject environment variables, volumes, or security contexts into any pod.

**Best practice:** Use OPA/Gatekeeper or Kyverno for policy — they are battle-tested webhook implementations with their own RBAC and audit modes.

---

### Q4. What is the PodSecurity admission controller? How does it replace PodSecurityPolicy, and what are its limitations?

**Answer:**

**PodSecurityPolicy (PSP)** was deprecated in Kubernetes 1.21 and removed in 1.25. It was powerful but notoriously difficult to configure correctly — enabling it without proper policies would break clusters, and its RBAC model (policies granted via `use` verb) was confusing.

**Pod Security Admission (PSA)** replaced it as a built-in admission controller using three predefined policy levels applied via namespace labels:

| Level | Description |
|-------|-------------|
| `privileged` | No restrictions (for trusted system workloads) |
| `baseline` | Prevents known privilege escalations; allows most defaults |
| `restricted` | Hardened profile; requires non-root, drops all capabilities, enforces seccomp |

**Three modes per level:**
- `enforce` — Reject non-compliant pods.
- `audit` — Allow but log violations in audit events.
- `warn` — Allow but return warnings to the user.

**Label syntax:**
```yaml
metadata:
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.29
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Limitations of PSA vs PSP:**

1. **No mutation** — PSA cannot automatically add `securityContext` fields. PSP could mutate pods to add `runAsNonRoot: true`. With PSA, workloads must be authored correctly.

2. **No fine-grained resource control** — PSP allowed controlling `allowedVolumes`, `allowedHostPaths`, etc. with per-path granularity. PSA is coarser.

3. **No per-user or per-serviceaccount policies** — PSA policies are namespace-wide. PSP could apply different policies to different service accounts within the same namespace.

4. **No custom policies** — PSA only provides three fixed levels. For custom policies, you need OPA/Gatekeeper, Kyverno, or a validating webhook.

**Recommendation:** Use PSA `restricted` as a floor, augmented with Kyverno or Gatekeeper for additional fine-grained controls.

---

### Q5. How does the Kubernetes node authorization mode work, and why is it important for security?

**Answer:**

The **Node Authorizer** is a special-purpose authorization mode (`--authorization-mode=Node`) that restricts what kubelets can read and write on the API server.

**The problem it solves:**  
Without node authorization, any kubelet with a valid client certificate could read any Secret in the cluster, potentially escalating access across all namespaces. This is called the **"noisy neighbor" or lateral movement problem** — a compromised worker node should not have access to secrets of workloads on other nodes.

**How it works:**

Kubelets authenticate with a certificate where:
- `CN = system:node:<nodeName>`
- `O = system:nodes`

The Node authorizer then permits kubelets only to:
- Read **Pods** scheduled to their node.
- Read **Secrets**, **ConfigMaps**, and **PersistentVolumeClaims** referenced by pods on their node.
- Read **ServiceAccounts** referenced by pods on their node.
- Write **Node** and **Pod status** for their own node.
- Create/delete **Events** for their node.

**NodeRestriction admission plugin** (companion to node authorization):  
Even with node authorization, a kubelet could label its Node object with labels that match node selectors for other pods. The `NodeRestriction` admission plugin prevents kubelets from modifying labels of other nodes and from adding arbitrary labels that could affect scheduling.

**Security implication:** Always enable both `Node` and `RBAC` authorization modes together. `--authorization-mode=Node,RBAC` is the production standard.

---

### Q6. Explain the Kubernetes control plane components and the attack surface each one presents.

**Answer:**

| Component | Port(s) | Attack Surface |
|-----------|---------|----------------|
| **kube-apiserver** | 6443 | Central auth/authz bypass, insecure port (deprecated 8080), DoS via large requests |
| **etcd** | 2379, 2380 | Direct data access without RBAC, unencrypted secrets, peer hijacking |
| **kube-scheduler** | 10259 (HTTPS) | Pod placement manipulation (can force workloads to compromised nodes) |
| **kube-controller-manager** | 10257 (HTTPS) | SA token generation, ServiceAccount compromise |
| **kubelet** | 10250 (API), 10255 (read-only) | Code execution on node, pod exec, log exfiltration |
| **kube-proxy** | 10249 | IPTables/eBPF manipulation affecting network routing |
| **CoreDNS** | 53 | DNS spoofing, exfiltration via DNS tunneling |

**Critical hardening per component:**

- **kube-apiserver:** Disable `--insecure-port=0`, enable audit logging (`--audit-log-path`), use `--anonymous-auth=false`, enable all relevant admission plugins.

- **kubelet:** Disable anonymous auth (`--anonymous-auth=false`), enable webhook authn/authz (`--authorization-mode=Webhook`), disable read-only port (`--read-only-port=0`), restrict API access.

- **etcd:** mTLS + encryption at rest + firewall rules (detailed in Q2).

- **kube-scheduler / kube-controller-manager:** These should not be accessible from outside the control plane network. They have their own `--kubeconfig` to authenticate to the API server. Use `--bind-address=127.0.0.1` to restrict local-only listening.

---

### Q7. What is a Kubernetes audit log? How do you design an audit policy for a production cluster?

**Answer:**

Kubernetes audit logs record every request that passes through the API server, giving you a tamper-evident trail of "who did what, when, and on which resource."

**Audit stages:**
- `RequestReceived` — Request is received, before routing.
- `ResponseStarted` — Headers sent; body not yet.
- `ResponseComplete` — Response body fully sent.
- `Panic` — Panic occurred during processing.

**Audit levels per rule:**
- `None` — Don't log.
- `Metadata` — Log request metadata (user, verb, resource) but not request/response body.
- `Request` — Log metadata + request body.
- `RequestResponse` — Log everything including response body.

**Production policy design principles:**

1. **Log all Secrets at `Metadata` level** — Logging request/response for Secrets would expose secret values in log files.
2. **Log all `exec`/`portforward`/`attach` at `RequestResponse`** — These are high-risk operations.
3. **Log all writes (`create`, `update`, `patch`, `delete`) at `Request` level.**
4. **Log auth failures** — Covered by `RequestReceived` stage on failed requests.
5. **Drop noise** — Exclude GET requests to well-known resources like `/healthz`, `/readyz`, leader election ConfigMaps.

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Don't log read-only requests to non-sensitive resources
  - level: None
    verbs: ["get", "watch", "list"]
    resources:
      - group: ""
        resources: ["endpoints", "services", "configmaps"]
    namespaces: ["kube-system"]

  # Log secret access at metadata only (never expose values)
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  # Log exec/attach/portforward fully
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward"]

  # Log all writes
  - level: Request
    verbs: ["create", "update", "patch", "delete", "deletecollection"]

  # Catch-all
  - level: Metadata
```

**Infrastructure:** Stream audit logs to a SIEM (Splunk, Elastic, Datadog) or a cloud-native solution (CloudWatch Logs, GCP Cloud Logging). Never store audit logs only on the control plane node.

---

### Q8. How does the Kubernetes service account token lifecycle work? What is the difference between legacy tokens and projected tokens?

**Answer:**

**Legacy tokens (pre-1.22 default):**
- Stored as Secrets of type `kubernetes.io/service-account-token`.
- Created automatically for every ServiceAccount.
- Never expire — valid until the Secret is manually deleted.
- Automatically mounted into every pod at `/var/run/secrets/kubernetes.io/serviceaccount/token`.
- High risk: Any compromised pod has a never-expiring credential.

**Projected (Bound) Service Account Tokens (1.22+ default):**
- Time-bound JWTs — default expiry is 1 hour, configurable via `expirationSeconds`.
- Audience-bound — issued for a specific audience (e.g., the API server or an external service).
- Kubelet-managed — automatically rotated before expiry.
- Not stored as Secrets — projected directly into pod via the `projected` volume source.

```yaml
volumes:
  - name: kube-api-access
    projected:
      sources:
        - serviceAccountToken:
            path: token
            expirationSeconds: 3600
            audience: "https://kubernetes.default.svc"
        - configMap:
            name: kube-root-ca.crt
        - downwardAPI: ...
```

**Key security differences:**

| Property | Legacy Token | Projected Token |
|----------|--------------|-----------------|
| Expiry | Never | Configurable (1h default) |
| Storage | etcd as Secret | Memory/kubelet |
| Rotation | Manual | Automatic |
| Audience binding | No | Yes |
| OIDC-compatible | No | Yes (JWKS endpoint) |

**Hardening:** Set `--service-account-max-token-expiration` on the API server. Disable automatic legacy token creation with the `LegacyServiceAccountTokenNoAutoGeneration` feature gate (enabled by default in 1.24+). Use the `TokenRequest` API for dynamic short-lived tokens.

---

### Q9. What is the Kubernetes threat matrix (Microsoft), and how do you use it operationally?

**Answer:**

The **Microsoft Kubernetes Threat Matrix** (published 2020, updated 2021) maps attack techniques to the MITRE ATT&CK framework applied to Kubernetes. It organizes threats into tactics:

**Tactics and key techniques:**

| Tactic | Example Techniques |
|--------|--------------------|
| **Initial Access** | Using cloud credentials, Exposed dashboard, Vulnerable application |
| **Execution** | `exec` into container, New container, Application exploit |
| **Persistence** | Backdoor container, Writable hostPath mount, Kubernetes CronJob |
| **Privilege Escalation** | Privileged container, hostPID/hostNetwork, RBAC permissions abuse |
| **Defense Evasion** | Delete logs, Proxy/anonymization, Connect from a proxy |
| **Credential Access** | List Kubernetes Secrets, Mount service account token, Access container service account |
| **Discovery** | Access Kubernetes API server, Access kubelet API, Network scanning |
| **Lateral Movement** | Container service account, ARP poisoning, CoreDNS poisoning |
| **Collection** | Image exfiltration, Access Kubernetes dashboard |
| **Impact** | Data destruction, Resource hijacking (cryptomining), Denial of Service |

**Operational usage:**

1. **Detection engineering** — Map each technique to a detection rule (audit log pattern, Falco rule, SIEM alert). E.g., `exec` into a container → alert on `pods/exec` audit events.

2. **Red team / purple team exercises** — Use the matrix as a structured attack playbook. Test each tactic against your cluster.

3. **Gap analysis** — Walk through each technique and ask: "Do we have a control that prevents or detects this?" Document gaps.

4. **Security posture scoring** — Track coverage across tactics as a maturity metric.

---

### Q10. How does Kubernetes handle CRL and certificate rotation for control plane components?

**Answer:**

Kubernetes uses **PKI certificates** for all internal communication, and certificate management is a critical operational security concern.

**Default certificate locations (kubeadm):**
```
/etc/kubernetes/pki/
├── ca.crt / ca.key           # Cluster CA
├── apiserver.crt / apiserver.key
├── apiserver-kubelet-client.crt
├── etcd/
│   ├── ca.crt / ca.key       # etcd CA (separate from cluster CA)
│   ├── server.crt / server.key
│   └── peer.crt / peer.key
├── front-proxy-ca.crt / front-proxy-ca.key
└── sa.pub / sa.key           # ServiceAccount signing keys
```

**Default expiry:** kubeadm-generated certificates expire in **1 year**. The CA certificate expires in **10 years**.

**Certificate rotation:**

```bash
# Check expiry
kubeadm certs check-expiration

# Rotate all certificates
kubeadm certs renew all

# Or selectively
kubeadm certs renew apiserver
```

After renewal, restart control plane components (they don't hot-reload).

**Kubelet certificate rotation:**
- Enable `--rotate-certificates=true` on kubelet for client cert auto-rotation.
- Enable `--rotate-server-certificates=true` for serving cert rotation (requires CSR approval).
- Approve pending CSRs: `kubectl certificate approve <csr-name>`.

**CRL (Certificate Revocation Lists):**  
Kubernetes does **not** support CRL or OCSP natively. To revoke a certificate:
1. Rotate the CA (nuclear option — revokes all certificates signed by it).
2. Add the certificate's CN to an RBAC deny list if using a webhook authorizer.
3. For ServiceAccount tokens — delete the Secret or revoke via `TokenReview` API.

**Best practice:** Automate certificate monitoring with alerting when certs approach expiry. cert-manager can manage lifecycle for workload certs but not control plane certs directly.

---

### Q11. What is the Container Runtime Interface (CRI), and how does the choice of runtime affect your security posture?

**Answer:**

The **CRI** is a gRPC plugin interface that allows Kubernetes to be decoupled from any specific container runtime. The kubelet speaks CRI to communicate with the runtime for operations like pulling images, creating containers, and managing sandbox lifecycles.

**Common runtimes and security characteristics:**

| Runtime | Isolation | Key Security Feature |
|---------|-----------|----------------------|
| **containerd** | Shared kernel | Lightweight, CNCF standard, supports seccomp/AppArmor |
| **CRI-O** | Shared kernel | OCI-focused, smaller attack surface than Docker |
| **gVisor (runsc)** | User-space kernel | Intercepts syscalls in user space; strong isolation |
| **Kata Containers** | VM-level | Each pod in a lightweight VM; hardware virtualization |
| **Firecracker** | MicroVM | AWS-developed; used in EKS Fargate |

**Security tradeoffs:**

- **containerd/CRI-O:** Standard choice. Security depends entirely on Linux kernel security features — seccomp, AppArmor, namespaces, cgroups. A kernel exploit affects all containers.

- **gVisor:** Excellent for multi-tenant or untrusted workload isolation. The "Sentry" user-space kernel intercepts syscalls before they reach the host kernel. Overhead is ~10-20% performance penalty. Does not support all syscalls (check compatibility matrix).

- **Kata Containers:** Strongest isolation — each pod runs in a real VM. Best for high-security workloads. Higher overhead due to VM startup time and memory.

**Runtime security configuration:**
- Limit the OCI runtime's seccomp profile (`RuntimeDefault` or custom).
- Disable unnecessary container capabilities at the runtime level.
- Use `RuntimeClass` in Kubernetes to assign different runtimes per pod:

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
```

```yaml
spec:
  runtimeClassName: gvisor
```

---

### Q12. What are the security risks of the Kubernetes Dashboard, and how do you secure or deprecate it?

**Answer:**

The Kubernetes Dashboard is a web UI for cluster management. **It has been involved in multiple high-profile cryptomining breaches** (Tesla, Shopify) due to misconfiguration.

**Common misconfigurations:**

1. **`--enable-skip-login`** — Allows login bypass entirely. Anyone who reaches the dashboard has full UI access.
2. **Exposed without authentication** — LoadBalancer service exposing the dashboard to the internet with no auth.
3. **Dashboard ServiceAccount with `cluster-admin`** — Default in older versions. Any user who accesses the dashboard gets cluster-admin effective permissions.
4. **No network policy** — Internal pods can reach the dashboard service.

**Securing the dashboard:**

1. **Never expose via LoadBalancer or Ingress without strong auth.** Use `kubectl proxy` or port-forwarding only for local admin use.

2. **Minimal RBAC for the dashboard's ServiceAccount:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dashboard-read-only
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps"]
    verbs: ["get", "list", "watch"]
```

3. **Enable token-based login and remove skip-login flag.**

4. **Add NetworkPolicy** to restrict dashboard access to specific namespaces or CIDRs.

5. **Consider deprecating in favor of** purpose-built observability tooling (Lens, K9s for local, Grafana for metrics). The dashboard is an unnecessary attack surface for most production clusters.

---

### Q13. How does Kubernetes handle multi-tenancy, and what are the security isolation models?

**Answer:**

Kubernetes was not designed for hard multi-tenancy (arbitrary untrusted tenants), but organizations use it for soft multi-tenancy (trusted but isolated teams). Understanding the isolation models is critical.

**Isolation models:**

**1. Namespace-based isolation (soft):**
- Resource isolation via RBAC + NetworkPolicy + ResourceQuota.
- Tenants are trusted but separated by convention and policy.
- Shared kernel — a container breakout affects all tenants.
- Good for: internal teams, dev/staging/prod separation.

**2. Node-level isolation:**
- Dedicate nodes to tenants using taints/tolerations and node affinity.
- Reduces blast radius of a container breakout.
- Higher cost (less bin-packing efficiency).

**3. Cluster-level isolation:**
- Each tenant gets their own cluster (control plane + workers).
- Maximum isolation — no shared API server, etcd, or kernel.
- Highest cost and operational overhead.
- Required for: regulated industries, untrusted third-party workloads, PCI DSS/HIPAA.

**4. VM-sandbox isolation (Kata/gVisor):**
- Each pod runs in a VM or user-space kernel.
- Provides near-cluster-level isolation at the pod level within a shared cluster.
- Good middle ground for SaaS platforms.

**Multi-tenant security checklist:**
- Enforce namespace per tenant with LimitRange + ResourceQuota.
- NetworkPolicy default-deny per namespace.
- Separate ServiceAccounts per tenant with minimum RBAC.
- PSA `restricted` on all tenant namespaces.
- Audit log monitoring scoped to tenant namespaces.
- Consider virtual clusters (vcluster) for strong API-level isolation without separate physical clusters.

---

### Q14. What is the Kubernetes API aggregation layer, and what are its security implications?

**Answer:**

The **API aggregation layer** allows extending the Kubernetes API by registering custom API servers (extension API servers) that handle their own resource types. The main API server proxies relevant requests to the extension API server.

**How it works:**
1. Register an `APIService` resource pointing to a Service in the cluster.
2. The main API server proxies requests for that group/version to the extension server.
3. The extension server authenticates the request using the `x-remote-user` and `x-remote-group` headers set by the front-proxy.

**Security implications:**

1. **Front-proxy trust** — Extension servers must validate that requests come from the API server's front-proxy CA, not arbitrary callers. If `--requestheader-client-ca-file` is misconfigured, an attacker can forge user identity headers.

2. **Extension server RBAC** — The extension server can implement its own authz logic, potentially bypassing Kubernetes RBAC. Audit any extension API server carefully.

3. **Network path** — Requests to extension servers traverse the cluster network. If the extension server is compromised, it can return arbitrary data to API clients.

4. **Metrics Server** — A common extension server that's often given too-broad ClusterRole permissions. Audit it regularly.

5. **Credential delegation** — Extension servers receive the delegated identity of the original user. They should re-validate authorization against the main API server via SubjectAccessReview.

**Key hardening:**
- Verify `--requestheader-allowed-names` restricts which front-proxy certs are accepted.
- Run extension API servers with minimal ServiceAccount permissions.
- TLS between the main API server and extension server is mandatory.

---

### Q15. What is the `system:masters` group, and why is it dangerous?

**Answer:**

`system:masters` is a built-in Kubernetes group that is **hardcoded** in the API server to grant unconditional cluster-admin access. Any user or certificate with `O=system:masters` bypasses RBAC entirely — including any audit triggers or admission webhooks.

**Why it bypasses RBAC:**  
The node authorization handler and RBAC check both short-circuit for `system:masters` members before reaching normal policy evaluation. It exists for bootstrapping purposes (initial admin access) and break-glass scenarios.

**The danger:**

1. **Hardcoded** — You cannot remove this privilege via RBAC. The only way to revoke it is to rotate the CA (since it's certificate-based) or delete the kubeconfig that contains it.

2. **No admission control** — Even validating webhooks may not fire for `system:masters` users in some configurations.

3. **Often over-provisioned** — CI/CD systems, operators, and even developer kubeconfigs are sometimes given `system:masters` for "convenience."

**Audit for system:masters usage:**

```bash
# Find all certs with O=system:masters
# Search kubeconfigs in your secrets management
kubectl get configmap cluster-info -n kube-public -o yaml
# Check API server audit logs for user groups containing system:masters
```

**Best practice:**
- Reserve `system:masters` credentials for break-glass scenarios only.
- Store break-glass kubeconfigs in a vault (HashiCorp Vault, AWS Secrets Manager) with access auditing and MFA.
- Use `cluster-admin` ClusterRoleBinding for day-to-day admin — this goes through RBAC and is auditable.

---

## 2. RBAC & Identity

---

### Q16. Design an RBAC model for a large organization with multiple teams using a shared Kubernetes cluster. What principles guide your design?

**Answer:**

**Guiding principles:**
1. **Principle of Least Privilege** — Every entity (human, ServiceAccount, CI job) gets only the permissions needed for its function.
2. **Separation of Duties** — Platform team manages cluster-scoped resources; app teams manage namespace-scoped resources.
3. **Defense in Depth** — RBAC is not the only control; network policies and PSA add layers.

**Typical role hierarchy:**

```
Cluster Level:
├── cluster-admin (break-glass only, system:masters)
├── cluster-reader (read-only on all namespaces)
├── namespace-provisioner (create/delete namespaces, assign quotas)
│
Namespace Level (per team namespace):
├── namespace-admin (full control within namespace)
├── developer (deploy, view logs, exec into pods)
├── viewer (read-only on non-sensitive resources)
└── ci-deployer (create/update deployments, services — no exec/delete)
```

**Concrete ClusterRole for a developer:**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: developer
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "configmaps", "persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets", "statefulsets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods/exec", "pods/portforward"]
    verbs: ["create"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: []  # Explicitly no access to secrets
```

Bind via `RoleBinding` in specific namespaces — never `ClusterRoleBinding` for developer roles.

**Avoid common pitfalls:**
- Never grant `*` verbs or `*` resources.
- Never use `ClusterRoleBinding` for namespace-scoped teams.
- Never bind `cluster-admin` to CI/CD pipelines.
- Separate Secret access into a dedicated role and audit its usage.

---

### Q17. How do you implement OIDC integration with Kubernetes for SSO? What are the security considerations?

**Answer:**

OIDC allows Kubernetes to authenticate users via an external identity provider (Okta, Azure AD, Dex, Google, Keycloak) using JWT tokens.

**Configuration on the API server:**

```bash
kube-apiserver \
  --oidc-issuer-url=https://accounts.google.com \
  --oidc-client-id=kubernetes \
  --oidc-username-claim=email \
  --oidc-groups-claim=groups \
  --oidc-username-prefix="oidc:" \
  --oidc-groups-prefix="oidc:" \
  --oidc-ca-file=/etc/kubernetes/pki/oidc-ca.crt
```

**User flow:**
1. User authenticates with IdP, receives `id_token` (JWT).
2. User adds token to kubeconfig (`--token` or via `exec` credential plugin).
3. API server validates JWT signature against IdP's JWKS endpoint.
4. API server extracts `username` and `groups` from configured claims.
5. RBAC evaluates permissions for that username/groups.

**Security considerations:**

1. **Token expiry** — OIDC tokens expire (typically 1h). Users must re-authenticate. Use `kubelogin` or `oidc-login` `exec` plugin for automatic refresh.

2. **Group sync latency** — If a user is removed from a group in the IdP, the change won't take effect until the current token expires. Keep token TTL short.

3. **Prefix isolation** — Always use `--oidc-username-prefix` and `--oidc-groups-prefix` to prevent OIDC identity collision with Kubernetes internal identities like `system:masters`.

4. **CA validation** — Use `--oidc-ca-file` to pin the OIDC provider's CA. Prevents MITM attacks if the IdP's public CA is compromised.

5. **Audience claim validation** — Ensure the `aud` claim in the JWT matches `--oidc-client-id` to prevent token reuse from other applications.

6. **Group → RBAC mapping** — Map IdP groups to ClusterRoles/Roles via RoleBindings. The mapping should be managed as IaC (Terraform, Helm).

---

### Q18. What are common RBAC privilege escalation paths in Kubernetes, and how do you detect and prevent them?

**Answer:**

**Key escalation paths:**

**1. `create` on `roles` or `clusterroles` + `create` on `rolebindings`**  
A subject with these two permissions can create an arbitrary role (including `cluster-admin`) and bind it to themselves or another subject.

**2. `bind` verb on ClusterRoles**  
The `bind` verb allows creating RoleBindings for roles up to and including the permissions of the binder. If misconfigured, a user can bind `cluster-admin` to themselves.

**3. `escalate` verb**  
Allows creating roles with MORE permissions than the requester currently has. This should be granted only to the API server itself.

**4. `impersonate` verb**  
Allows acting as any user, group, or ServiceAccount. Anyone with `impersonate` on `users` can become `system:masters`.

**5. Write access to ConfigMaps or Secrets in `kube-system`**  
Modifying certain kube-system ConfigMaps can affect cluster behavior. Write access to Secrets in kube-system allows stealing control plane credentials.

**6. `patch` on ClusterRoleBindings**  
Can add subjects to existing bindings including `cluster-admin`.

**7. `create` on Pods in privileged namespaces**  
Creating a pod with `hostPID: true` or a privileged security context on a control plane node is cluster takeover.

**Detection:**

```bash
# Find all subjects with dangerous verbs
kubectl get clusterrolebindings -o json | jq '
  .items[] | 
  select(.roleRef.name == "cluster-admin") | 
  {name: .metadata.name, subjects: .subjects}'

# Audit RBAC with rakkess or kubectl-who-can
kubectl-who-can create clusterrolebindings
```

**Prevention:**
- Enable `--authorization-mode=RBAC,Node` — never disable.
- Audit and alert on changes to ClusterRoleBindings.
- Use OPA/Gatekeeper to reject RoleBindings to `cluster-admin` from non-admin namespaces.
- Regularly run `kube-bench` and `rbac-police` or `pluto`.

---

### Q19. How does Workload Identity work in GKE, EKS, and AKS? Compare the mechanisms.

**Answer:**

Workload Identity allows pods to authenticate to cloud provider APIs (IAM, S3, GCS, Key Vault) without storing long-lived credentials in Secrets.

**GKE Workload Identity:**
- Kubernetes ServiceAccount annotated with a Google Service Account (GSA).
- The GKE metadata server intercepts requests to the GCP metadata API and exchanges the Kubernetes SA token for a GSA token via a token federation endpoint.
- Annotation: `iam.gke.io/gcp-service-account: gsa@project.iam.gserviceaccount.com`
- GCP side: `iam.workloadIdentityUser` binding on the GSA for `serviceAccount:project.svc.id.goog[namespace/ksa]`.

**EKS IAM Roles for Service Accounts (IRSA):**
- EKS exposes an OIDC provider endpoint.
- AWS IAM trust policy references the OIDC provider and the Kubernetes SA audience.
- The projected SA token is exchanged via `AssumeRoleWithWebIdentity`.
- Annotation: `eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/role-name`
- AWS injects `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` env vars automatically via a mutating webhook (Amazon EKS Pod Identity Webhook).

**AKS Workload Identity (Azure AD):**
- Federated identity credentials on an Azure Managed Identity (or App Registration).
- AKS OIDC issuer URL registered as federated credential.
- Mutating webhook injects `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_FEDERATED_TOKEN_FILE`.
- Uses MSAL's federated identity to exchange the Kubernetes token for an Azure AD access token.

**Comparison:**

| Feature | GKE | EKS | AKS |
|---------|-----|-----|-----|
| Mechanism | Metadata server intercept | OIDC federation | OIDC federation + webhook |
| Pod annotation required | Yes | Yes | Yes |
| Cloud IAM entity | Google SA | IAM Role | Managed Identity |
| Token exchange endpoint | GKE metadata server | AWS STS | Azure AD |
| Node-level metadata blocking needed | Yes | Yes (IMDSv2) | Yes |

**Security in all three:**  
Block instance metadata access from pods that don't need it. On EKS, enforce IMDSv2 and set hop limit to 1. On GKE, use `--workload-metadata=GKE_METADATA`. On AKS, use the pod identity webhook only on opted-in namespaces.

---

### Q20. What is the risk of auto-mounting ServiceAccount tokens, and how do you disable it selectively?

**Answer:**

By default, Kubernetes auto-mounts the ServiceAccount token at `/var/run/secrets/kubernetes.io/serviceaccount/token` in every pod. Most application pods **do not need** to call the Kubernetes API, making this token an unnecessary attack surface.

**Risk:**
- A compromised pod can use the token to enumerate other resources (discovery).
- Tokens are valid until expiry — if not projected tokens, potentially forever.
- Pods that call external services (S3, databases) have no reason to carry a Kubernetes API credential.

**Disable at ServiceAccount level:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
automountServiceAccountToken: false
```

**Disable at Pod level (overrides SA setting):**

```yaml
spec:
  automountServiceAccountToken: false
```

**Disable cluster-wide via OPA/Gatekeeper:**
```yaml
# Kyverno policy to enforce opt-in
spec:
  rules:
    - name: check-automount
      match:
        resources:
          kinds: [Pod]
      validate:
        message: "automountServiceAccountToken must be false"
        pattern:
          spec:
            automountServiceAccountToken: false
```

**When you DO need API access:**  
Use projected tokens with explicit audience and short expiry, rather than relying on the auto-mounted default token:

```yaml
volumes:
  - name: api-token
    projected:
      sources:
        - serviceAccountToken:
            path: token
            expirationSeconds: 600
            audience: "https://kubernetes.default.svc"
```

---

### Q21. How do you implement just-in-time (JIT) access for Kubernetes cluster administration?

**Answer:**

JIT access means granting elevated Kubernetes permissions only when needed, for a limited time, with full audit trail — not leaving persistent `cluster-admin` bindings.

**Implementation approaches:**

**1. Temporary RoleBinding with TTL (manual/scripted):**

```bash
# Grant access
kubectl create clusterrolebinding jit-admin-alice \
  --clusterrole=cluster-admin \
  --user=alice@company.com

# Auto-delete after 1 hour (using a Job or external controller)
kubectl delete clusterrolebinding jit-admin-alice --dry-run=client
```

**2. Teleport (Gravitational):**
- Users request access through Teleport's access request workflow.
- Approvers approve/deny via Slack, PagerDuty, or web UI.
- Teleport issues short-lived Kubernetes credentials (kubeconfig with a certificate valid for the approved duration).
- Full session recording and audit logs.

**3. HashiCorp Vault Kubernetes Secrets Engine:**
- Vault generates dynamic kubeconfig with a Kubernetes ServiceAccount that has a TTL.
- After TTL, the ServiceAccount and its RoleBinding are automatically deleted.

**4. Crossplane / Custom Controller:**
- Build a CRD `AccessRequest` that triggers creation of a temporary RoleBinding via a controller.
- Reconcile loop cleans up expired bindings.

**Audit requirements for JIT:**
- Log the access request (who, why, approver).
- Record all kubectl commands during the session (Teleport does this natively).
- Alert on JIT access outside business hours.

---

### Q22. Explain the `impersonate` verb and its legitimate use cases vs. security risks.

**Answer:**

The `impersonate` verb in Kubernetes allows a user or ServiceAccount to act on behalf of another user, group, or ServiceAccount. The API server accepts `Impersonate-User`, `Impersonate-Group`, and `Impersonate-Extra` HTTP headers.

```bash
kubectl get pods --as=alice --as-group=engineering
```

**Legitimate use cases:**

1. **Operator testing** — A cluster admin wants to verify what permissions a specific user has without logging in as them.
2. **Platform automation** — A privileged controller that processes requests on behalf of end users (e.g., a self-service portal that creates namespaces on behalf of the requesting developer).
3. **User permission debugging** — `kubectl auth can-i list pods --as=ci-service-account`.

**Security risks:**

- **Privilege escalation** — Any entity with `impersonate` on `users` can impersonate `system:masters`, bypassing RBAC entirely.
- **Audit confusion** — Audit logs show both the impersonating and impersonated identity, but downstream systems may only capture the impersonated identity.
- **Broad grant** — Granting `impersonate` on `*` resources allows impersonating any ServiceAccount cluster-wide.

**Safe RBAC for impersonation:**

```yaml
rules:
  - apiGroups: [""]
    resources: ["users"]
    verbs: ["impersonate"]
    resourceNames: ["alice", "bob"]  # Restrict to specific users
```

**Detection:** Alert on audit events where `impersonatedUser.username` is present but differs from `user.username`. High-risk: impersonation of `system:*` users.

---

### Q23. How do you perform RBAC auditing in a production cluster? What tools do you use?

**Answer:**

RBAC drift is common — permissions accumulate over time without cleanup. Regular auditing is essential.

**Audit questions to answer:**
1. Who has `cluster-admin`?
2. Who can read Secrets?
3. Who can exec into pods?
4. Are there any orphaned RoleBindings (pointing to deleted ServiceAccounts)?
5. Are any default ServiceAccounts over-privileged?

**Tools:**

**1. `kubectl-who-can` (Aqua Security)**
```bash
kubectl who-can create pods
kubectl who-can get secrets -n production
```

**2. `rakkess` (Access Matrix)**
```bash
# Show what a specific user can do
rakkess --as alice@company.com
```

**3. `rbac-tool`**
```bash
rbac-tool lookup alice
rbac-tool visualize  # Generates a GraphViz chart
```

**4. `audit2rbac`**  
Analyzes audit logs and suggests minimal RBAC roles based on actual usage:
```bash
audit2rbac --filename /var/log/kubernetes/audit.log --user ci-deployer
```

**5. OPA/Gatekeeper + Conftest for IaC RBAC scanning:**
```bash
conftest test k8s/rbac/ --policy policies/rbac-checks/
```

**6. Cloud-native solutions:**
- GKE: Policy Insights, Recommender API for RBAC.
- AWS: Access Analyzer for EKS (preview).
- Azure: Azure Policy for AKS.

**RBAC hygiene checklist:**
- Quarterly review of all ClusterRoleBindings.
- Remove stale ServiceAccounts from deleted namespaces.
- Alert on new ClusterRoleBindings in production.
- Never grant `create` on `clusterrolebindings` to non-admins.

---

### Q24. What is the risk of using `kubectl apply -f` with untrusted manifests, and how do you prevent it?

**Answer:**

Applying untrusted Kubernetes manifests is equivalent to executing untrusted code with the permissions of your kubeconfig. A malicious manifest can:

1. **Deploy privileged pods** — `privileged: true`, `hostPID: true`, `hostNetwork: true` → node takeover.
2. **Create ClusterRoleBindings** — Elevate attacker-controlled ServiceAccounts to `cluster-admin`.
3. **Exfiltrate secrets** — Mount arbitrary Secrets as environment variables or volumes.
4. **Deploy backdoor services** — Create NodePort or LoadBalancer services for persistent access.
5. **Poison admission webhooks** — Create MutatingWebhookConfigurations that inject malicious containers.
6. **DaemonSet for node compromise** — Deploy a DaemonSet with hostPath mounts to all nodes.

**Prevention:**

1. **Static analysis before apply:**
```bash
# checkov
checkov -f deployment.yaml

# kubesec
kubesec scan deployment.yaml

# conftest with OPA policies
conftest test deployment.yaml --policy policies/
```

2. **Admission control as backstop:**  
PSA `restricted` mode, OPA/Gatekeeper, or Kyverno will reject privileged manifests even if someone applies them.

3. **CI/CD policy gates:**  
Scan all manifests in PRs before they can be merged or deployed. Block merges that introduce `privileged: true`, `hostPID`, `hostNetwork`, or new ClusterRoleBindings to `cluster-admin`.

4. **GitOps with narrow RBAC:**  
The GitOps operator (ArgoCD, Flux) uses a ServiceAccount with narrow permissions — it can only apply resources in specific namespaces. It cannot create ClusterRoleBindings.

5. **OPA policy example:**
```rego
deny[msg] {
  input.kind == "Pod"
  input.spec.containers[_].securityContext.privileged == true
  msg := "Privileged containers are not allowed"
}
```

---

### Q25. How does the Kubernetes TokenRequest API differ from static token files? When would you use it?

**Answer:**

**Static token files (`--token-auth-file`):**
- A flat file on the API server with `token,user,uid[,groups]` entries.
- Tokens never expire — they're valid as long as the file exists.
- No rotation mechanism — changing requires API server restart.
- **Deprecated and should never be used in production.** They're a bootstrap remnant.

**TokenRequest API:**
Introduced in 1.10, stable in 1.20. Issues time-limited, audience-specific, and optionally pod-bound tokens.

```bash
kubectl create token <service-account-name> \
  --audience=https://vault.example.com \
  --duration=15m
```

```go
// Programmatic via the API
tokenRequest := &authv1.TokenRequest{
    Spec: authv1.TokenRequestSpec{
        Audiences:         []string{"https://vault.example.com"},
        ExpirationSeconds: pointer.Int64(900),
        BoundObjectRef: &authv1.BoundObjectReference{
            Kind:       "Pod",
            Name:       podName,
            APIVersion: "v1",
        },
    },
}
```

**Key properties of TokenRequest tokens:**
- **Audience-bound** — Token is only valid for the specified audience.
- **Time-bound** — Automatically expire.
- **Pod-bound** — If the pod is deleted, the token is immediately invalid (even before expiry).
- **OIDC-compatible** — Can be validated by any OIDC-aware system via the cluster's JWKS endpoint.

**Use cases:**
- Issuing short-lived tokens for Vault authentication.
- Federated identity for cloud provider APIs (IRSA, GKE Workload Identity).
- Pod-to-pod authentication without shared secrets.
- Service mesh JWT issuance (Istio uses this internally).

---

## 3. Network Security & Policies

---

### Q26. Explain Kubernetes NetworkPolicy. What are its limitations, and how do CNI plugins implement it?

**Answer:**

**NetworkPolicy** is a Kubernetes API object that specifies how groups of pods are allowed to communicate with each other and with external endpoints.

**Key concepts:**
- Policies are **additive** — multiple policies applying to a pod are unioned.
- By default (no policies), all traffic is allowed.
- A pod selected by at least one NetworkPolicy with `ingress` or `egress` rules has those directions restricted.
- A default-deny policy selects all pods and has no ingress/egress rules:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}       # Select all pods
  policyTypes:
    - Ingress
    - Egress
```

**Allow specific traffic:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-api
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
          namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: production
      ports:
        - protocol: TCP
          port: 8080
```

**Limitations:**

1. **No Layer 7 filtering** — Cannot filter by HTTP path, method, or headers. Use a service mesh (Istio, Linkerd) for L7 policies.
2. **No FQDN-based egress** — Cannot write a policy that allows `*.example.com`. Use FQDN policies in Cilium or Calico's `NetworkPolicy` extensions.
3. **No logging** — Standard NetworkPolicy has no built-in flow logging. CNI plugins add this.
4. **No policy ordering** — You cannot define priority/order between policies.
5. **Node-level traffic** — NetworkPolicy doesn't control host-network pods or traffic originating from nodes themselves.
6. **Requires CNI support** — Flannel does NOT support NetworkPolicy. You need Calico, Cilium, Weave, or another policy-aware CNI.

**CNI Implementation:**

- **Calico** — Implements via iptables/eBPF rules on each node. Drops packets that don't match allow rules.
- **Cilium** — Uses eBPF programs attached to network interfaces for high-performance, kernel-level enforcement. Supports L7 policies.
- **Weave Net** — Uses iptables. Less performant at scale.

---

### Q27. What is Cilium, and how does eBPF change the Kubernetes networking security model?

**Answer:**

**Cilium** is a CNI plugin that uses **eBPF (Extended Berkeley Packet Filter)** to implement networking, load balancing, and security policies directly in the Linux kernel, bypassing iptables entirely.

**eBPF in a nutshell:**  
eBPF programs are small, verified bytecode programs that run in a sandbox inside the Linux kernel. They can be attached to kernel events (network packets, syscalls, tracepoints) and execute with near-native performance, without needing kernel module compilation.

**How Cilium uses eBPF:**

1. **Network Policy enforcement** — Instead of traversing potentially thousands of iptables rules, Cilium attaches eBPF programs to each pod's network interface. Packet decisions happen at the lowest kernel level.

2. **Identity-based security** — Cilium assigns a numeric identity to each pod based on labels. Policies use identities, not IP addresses, meaning policy enforcement is stable even as pod IPs change.

3. **L7 policy (HTTP/gRPC/Kafka)** — Cilium's Envoy integration allows filtering HTTP requests by path, method, and headers, or Kafka topics, without a sidecar:

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
spec:
  egress:
    - toEndpoints:
        - matchLabels:
            app: api
      toPorts:
        - ports:
            - port: "80"
              protocol: TCP
          rules:
            http:
              - method: GET
                path: /api/v1/public
```

4. **Transparent encryption** — Node-to-node encryption via IPsec or WireGuard, enforced in the kernel.

5. **Observability (Hubble)** — eBPF-based flow visibility without performance overhead. Hubble provides real-time network flow logs, DNS queries, and HTTP traces.

**Security advantages over iptables:**
- eBPF rules are enforced atomically — no rule ordering issues.
- Performance scales linearly; iptables is O(n) per rule.
- Identity-based policies are portable and don't break on IP reuse.
- Kernel-level enforcement is harder to bypass from user space.

---

### Q28. How do you implement egress filtering for Kubernetes workloads? What are the approaches and tradeoffs?

**Answer:**

Egress filtering prevents pods from making outbound connections to unauthorized destinations — critical for preventing data exfiltration, C2 communication, and SSRF attacks reaching cloud metadata APIs.

**Approach 1: Kubernetes NetworkPolicy (basic IP/CIDR-based)**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-egress
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 10.0.0.0/8  # Allow internal only
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 169.254.169.254/32  # Block metadata API
      ports:
        - port: 443
```

*Limitation:* No FQDN filtering; IP ranges change.

**Approach 2: DNS-based FQDN policies (Cilium / Calico Enterprise)**

```yaml
# Cilium FQDN policy
egress:
  - toFQDNs:
      - matchName: "api.stripe.com"
      - matchPattern: "*.s3.amazonaws.com"
    toPorts:
      - ports: [{port: "443"}]
```

**Approach 3: Egress gateway / proxy (Squid, Envoy, Istio)**

Route all pod egress through a dedicated proxy that enforces allowlists. The proxy can do TLS inspection, URL filtering, and request logging.

```
Pod → Egress Proxy (Envoy) → Internet
```

Configure pods to use the proxy via `HTTP_PROXY`/`HTTPS_PROXY` env vars or transparent proxy with iptables redirect.

**Approach 4: Cloud-native NAT Gateway + Security Groups**

On AWS, route pod egress via a NAT Gateway in a private subnet. Use AWS Security Groups for ENIs (EKS Security Groups for Pods) to control outbound traffic at the VPC level.

**Tradeoffs:**

| Approach | FQDN Support | TLS Inspection | Complexity | Performance |
|----------|-------------|----------------|------------|-------------|
| NetworkPolicy | No | No | Low | High |
| Cilium FQDN | Yes | No | Medium | High |
| Egress Proxy | Yes | Yes (break-inspect) | High | Medium |
| Cloud NAT/SG | IP only | No | Low | High |

**Always block:** `169.254.169.254` (EC2/GCP metadata), `100.100.100.200` (Alibaba metadata).

---

### Q29. What is a service mesh, and how does it enhance Kubernetes security beyond NetworkPolicy?

**Answer:**

A service mesh is an infrastructure layer that handles service-to-service communication in a microservices architecture. In Kubernetes, the dominant implementations are **Istio** (Envoy-based), **Linkerd** (Rust Linkerd2-proxy), and **Consul Connect**.

**Security capabilities beyond NetworkPolicy:**

**1. Mutual TLS (mTLS) for all service communication:**
- Every pod gets a SPIFFE/SVID certificate (X.509) issued by the mesh's CA.
- All pod-to-pod communication is encrypted and mutually authenticated — even within the same namespace.
- NetworkPolicy operates at L3/L4; mTLS provides L7 cryptographic identity.

**2. Authorization policies based on service identity:**

```yaml
# Istio AuthorizationPolicy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: require-jwt
spec:
  selector:
    matchLabels:
      app: productpage
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/default/sa/frontend"]
      to:
        - operation:
            methods: ["GET"]
            paths: ["/api/*"]
```

**3. L7 traffic control:**
- Rate limiting per service identity.
- Circuit breaking to prevent cascading failures.
- Traffic splitting for canary deployments.

**4. Observability:**
- Automatic distributed tracing (Jaeger, Zipkin).
- Service-level metrics (latency, error rate, traffic) without code changes.
- mTLS verification in logs.

**5. Egress control:**
- Istio `ServiceEntry` defines allowed external services. Traffic to undefined external services can be blocked.

**Tradeoffs:**
- **Sidecar overhead** — Linkerd adds ~5ms latency; Istio ~10ms. Ambient mesh mode (Istio 1.22+) eliminates sidecar.
- **Operational complexity** — Certificate rotation, control plane HA, upgrade cycles.
- **Not a replacement for NetworkPolicy** — Defense in depth: use both.

---

### Q30. How do you prevent SSRF attacks targeting the cloud metadata API from Kubernetes pods?

**Answer:**

**SSRF (Server-Side Request Forgery)** targeting the cloud metadata API (`169.254.169.254` on AWS/GCP/Azure) allows an attacker who can make the application issue HTTP requests to retrieve IAM credentials, user data scripts (which may contain secrets), and instance identity documents.

**In an SSRF on EKS with IRSA disabled:** The attacker retrieves EC2 instance role credentials with full node permissions — potentially reading all Secrets, executing code, or accessing S3 buckets.

**Defense layers:**

**1. Block at NetworkPolicy level:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 169.254.169.254/32
              - 100.100.100.200/32  # Alibaba
              - fd00:ec2::254/128   # IPv6 AWS
```

**2. IMDSv2 enforcement (AWS):**
IMDSv2 requires a `PUT` request to get a session token before making metadata calls. This breaks simple SSRF attacks that use `GET` only.

```bash
# Enforce IMDSv2 and set hop limit to 1 (prevents container access)
aws ec2 modify-instance-metadata-options \
  --instance-id i-xxxx \
  --http-put-response-hop-limit 1 \
  --http-endpoint enabled \
  --http-tokens required
```

Hop limit `1` means only the instance itself (not containers behind NAT) can reach IMDS.

**3. Workload Identity instead of node role:**
Use IRSA/GKE Workload Identity so pods authenticate with short-lived tokens rather than the node's ambient instance role.

**4. Application-level SSRF prevention:**
- Allowlist outbound URLs at the application layer.
- Validate and sanitize any user-supplied URLs.
- Use a dedicated HTTP client that blocks RFC1918 and link-local ranges.

**5. Runtime detection:**
Detect metadata API calls from pods using Falco:
```yaml
- rule: Metadata API Access from Container
  condition: >
    outbound and container and
    fd.sip = "169.254.169.254"
  output: "Metadata API access from container (pod=%k8s.pod.name)"
  priority: WARNING
```

---

### Q31. What is Kubernetes Ingress security, and how do you harden an Ingress controller?

**Answer:**

The Ingress controller (NGINX, Traefik, HAProxy, AWS ALB, GCE) is a critical trust boundary — it terminates external TLS and routes to internal services. A misconfigured or vulnerable Ingress controller can expose internal services or become an entry point for cluster attacks.

**Hardening checklist:**

**1. TLS configuration:**
- Enforce TLS 1.2+ minimum (`ssl-protocols: TLSv1.2 TLSv1.3`).
- Disable weak ciphers.
- Use cert-manager for automatic certificate lifecycle.
- HSTS headers: `Strict-Transport-Security: max-age=31536000; includeSubDomains`.

**2. Ingress controller isolation:**
- Run the Ingress controller in a dedicated namespace.
- Use a dedicated ServiceAccount with minimal RBAC (only needs to read Ingress resources and create Endpoints).
- NetworkPolicy: only allow traffic on 80/443 from the internet; restrict egress to upstream services.

**3. Prevent namespace crossover:**  
By default, NGINX Ingress allows routing to services in any namespace. Restrict with `--watch-namespace` flag or use `IngressClass`.

**4. Annotations injection attacks:**
Malicious Ingress annotations can inject NGINX config snippets. If your cluster allows untrusted users to create Ingress objects, disable `allow-snippet-annotations`:
```yaml
allow-snippet-annotations: "false"
```
An attacker with Ingress `create` permissions and snippet access can exfiltrate Kubernetes secrets via NGINX Lua scripts.

**5. Rate limiting and WAF:**
- Enable rate limiting at Ingress level.
- Use ModSecurity + OWASP Core Rule Set with NGINX Ingress for WAF.
- Cloud-native WAF (AWS WAF + ALB, GCP Cloud Armor) for managed ingress.

**6. Prevent Ingress resource abuse:**
- Restrict who can create/modify Ingress objects via RBAC.
- Use OPA/Gatekeeper to enforce allowed hostnames per namespace.

---

### Q32. Explain the security model of Kubernetes DNS (CoreDNS) and potential attack vectors.

**Answer:**

**CoreDNS** is the default DNS server in Kubernetes clusters. Every pod's DNS resolver points to the CoreDNS ClusterIP (`kube-dns`), making it a critical infrastructure component.

**DNS resolution chain:**
1. Pod requests resolution of `api.production.svc.cluster.local`.
2. Request goes to CoreDNS (ClusterIP 10.96.0.10 typically).
3. CoreDNS checks its service/endpoint cache.
4. External queries forwarded upstream per Corefile configuration.

**Attack vectors:**

**1. DNS spoofing (MITM):**
- An attacker who can intercept UDP packets on port 53 can respond with forged DNS answers.
- CoreDNS doesn't use DNSSEC by default.
- Mitigation: Service mesh mTLS means even if DNS is spoofed, TLS certificate validation will fail.

**2. DNS tunneling for data exfiltration:**
- DNS queries to external domains can encode data in subdomains.
- `exfil.attacker.com` receives data as encoded subdomains.
- Mitigation: Restrict external DNS forwarding; monitor query volume and entropy.

**3. CoreDNS cache poisoning:**
- If CoreDNS uses an insecure upstream resolver, poisoned responses propagate to all pods.
- Use trusted upstream DNS over TLS (DoT): `forward . tls://8.8.8.8`.

**4. CoreDNS configuration injection:**
- CoreDNS reads its Corefile from a ConfigMap. An attacker with ConfigMap write access in `kube-system` can redirect DNS.

**5. Amplification attacks:**
- CoreDNS can be used for reflection/amplification from within the cluster.

**Hardening:**
- RBAC restricting ConfigMap writes in `kube-system`.
- DNS-over-TLS upstream forwarding.
- Cilium DNS visibility to monitor and optionally block queries to specific external domains.
- Falco rules for unexpected DNS patterns.
- Rate limit DNS queries per pod using Cilium network policies.

---

### Q33. What is the risk of `hostNetwork: true` in a pod spec, and when is it justified?

**Answer:**

`hostNetwork: true` removes the pod from its isolated network namespace and places it directly in the host's network namespace. The pod shares the node's IP address and can bind to any port on the host.

**Security risks:**

1. **Port conflicts** — Pod can bind to privileged ports (80, 443, 22) on the node.
2. **Bypass NetworkPolicy** — NetworkPolicy applies to pod-namespace traffic. A pod in the host namespace may bypass some NetworkPolicy enforcement depending on the CNI.
3. **Access to node services** — Can reach services bound to `127.0.0.1` on the node (kubelet API, local daemons).
4. **Network namespace escape** — Combined with other privileges, this is a step toward node takeover.
5. **Cloud metadata API** — If metadata IP blocking relies on pod networking, a host-network pod may bypass it.

**When is it justified?**

- **Network infrastructure components** — CNI plugins themselves (Calico, Cilium node agents), kube-proxy (when not using eBPF), Flannel.
- **Node-level monitoring** — Node exporters (Prometheus) that need to observe node-level network interfaces.
- **Performance-critical networking** — Some high-frequency trading or HPC workloads.

**Mitigation when required:**
- PSA `baseline` level blocks `hostNetwork` — use `privileged` only for system namespaces.
- Deploy host-network pods only in `kube-system` or a dedicated infrastructure namespace with strict RBAC.
- Use a dedicated RuntimeClass for additional node isolation.
- NetworkPolicy still applies to host-network pod egress in some CNIs (Calico).

---

### Q34. What is the Kubernetes Service topology and how can it be exploited?

**Answer:**

Kubernetes Services abstract pod access behind a stable ClusterIP, NodePort, or LoadBalancer. Understanding the traffic path reveals potential attack surfaces.

**Traffic path for ClusterIP:**
1. Client pod makes request to ClusterIP (e.g., `10.96.100.50:8080`).
2. kube-proxy (iptables/IPVS/eBPF) on the client's node intercepts and rewrites the destination to a healthy pod IP.
3. Packet is routed to the target pod (potentially on another node via CNI overlay).

**Attack vectors:**

**1. NodePort exposure:**  
NodePort services expose a port on EVERY node in the cluster. If the security group/firewall allows the NodePort range (30000-32767), any node IP becomes an entry point. Restrict NodePort access via cloud firewall rules.

**2. External LoadBalancer without authentication:**  
A `LoadBalancer` service creates a cloud load balancer accessible from the internet. Without network ACLs, authentication, or a WAF, this directly exposes the backend service.

**3. ExternalName service for SSRF:**  
`ExternalName` services resolve to an external CNAME. An attacker who can create Services can use ExternalName to redirect traffic intended for a legitimate service to an attacker-controlled endpoint.

**4. EndpointSlice hijacking:**  
An attacker with `update` on `EndpointSlices` can redirect a service to point to any IP — including the metadata API or a pod they control. Restrict EndpointSlice write access.

**5. Service Account token for external services:**  
Services with `externalTrafficPolicy: Local` preserve client IPs. Misusing this can bypass IP-based allow lists.

**Mitigations:**
- Use `spec.loadBalancerSourceRanges` to restrict LoadBalancer access by CIDR.
- Audit all `ExternalName` services.
- Restrict `EndpointSlice` write permissions.
- Prefer `ClusterIP` services with Ingress for external access.

---

### Q35. How does WireGuard encryption work in Cilium, and when would you enable it?

**Answer:**

Cilium supports transparent **WireGuard** encryption for pod-to-pod traffic crossing node boundaries. This provides encryption-in-transit for the cluster overlay network without requiring a service mesh.

**How it works:**

1. Each node generates a WireGuard key pair at startup.
2. Cilium's operator distributes public keys to all nodes via `CiliumNode` custom resources.
3. WireGuard interfaces (`cilium_wg0`) are created on each node.
4. Pod traffic destined for pods on other nodes is routed through the WireGuard interface, encrypted before leaving the node, and decrypted on arrival.
5. Same-node pod-to-pod traffic is NOT encrypted (stays within the node's kernel).

**Comparison with IPsec:**

| Feature | WireGuard | IPsec |
|---------|-----------|-------|
| Performance | ~10% overhead | ~20% overhead |
| Key management | Automatic via Cilium | Manual or external |
| Algorithms | ChaCha20-Poly1305 (fixed) | Configurable |
| Kernel support | 5.6+ | All versions |
| FIPS compliance | No (ChaCha20) | Yes (AES-GCM) |

**Enable WireGuard in Cilium:**
```yaml
# Helm values
encryption:
  enabled: true
  type: wireguard
  nodeEncryption: true
```

**When to enable:**
- **Multi-tenant clusters** — Ensure traffic between tenant workloads on different nodes is encrypted.
- **Compliance requirements** — PCI DSS, HIPAA require encryption in transit.
- **Untrusted network underlay** — Cloud provider networks, co-location facilities.
- **Defense in depth** — Even if CNI network policy is bypassed at L3, WireGuard ensures data confidentiality.

**When NOT to enable:**
- Single-tenant clusters where the underlay is trusted and performance is critical.
- Environments already using a service mesh with mTLS for all service communication.

---

## 4. Pod & Container Security

---

### Q36. Design a hardened pod security context for a production API server container. Explain each field.

**Answer:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  template:
    spec:
      # Pod-level security context
      securityContext:
        runAsNonRoot: true         # Enforce non-root; fails if container runs as UID 0
        runAsUser: 1000            # Specific non-root UID
        runAsGroup: 3000           # Specific GID
        fsGroup: 2000              # Group for mounted volumes
        fsGroupChangePolicy: OnRootMismatch  # Only chown if necessary (perf optimization)
        seccompProfile:
          type: RuntimeDefault     # Apply default seccomp profile (syscall filter)
        sysctls: []                # No custom kernel parameters
        supplementalGroups: []     # No additional groups

      # Disable SA token auto-mount if not needed
      automountServiceAccountToken: false

      containers:
        - name: api
          image: registry.example.com/api:1.2.3@sha256:abc123  # Pinned by digest
          
          # Container-level security context
          securityContext:
            allowPrivilegeEscalation: false  # Prevent setuid/setgid escalation
            privileged: false                # Never run privileged
            readOnlyRootFilesystem: true     # Prevent writes to container FS
            runAsNonRoot: true
            runAsUser: 1000
            capabilities:
              drop:
                - ALL              # Drop ALL Linux capabilities
              add:
                - NET_BIND_SERVICE  # Add back only if binding to port <1024 (prefer >1024)
            seccompProfile:
              type: RuntimeDefault

          # Resource limits (required for security + stability)
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi

          # Writable paths via emptyDir (since rootfs is read-only)
          volumeMounts:
            - name: tmp
              mountPath: /tmp
            - name: cache
              mountPath: /app/cache

      volumes:
        - name: tmp
          emptyDir: {}
        - name: cache
          emptyDir:
            sizeLimit: 100Mi  # Limit emptyDir size
```

**Key decisions explained:**

- `readOnlyRootFilesystem: true` — Prevents malware from writing executables or modifying configs. Requires explicit emptyDir mounts for writable paths.
- `allowPrivilegeEscalation: false` — Prevents `sudo`, setuid binaries, or `execve` to privileged executables.
- `capabilities: drop: ALL` — Modern apps need zero Linux capabilities. NET_BIND_SERVICE is only needed for port <1024; prefer running on port 8080 and let Kubernetes/Ingress handle mapping.
- `seccompProfile: RuntimeDefault` — Applies Docker's default seccomp profile (~300 syscalls blocked including `ptrace`, `mount`, `kexec_load`).
- `runAsNonRoot: true` + `runAsUser: 1000` — Belt and suspenders; even if the image's USER is overridden, the pod will fail to start as root.

---

### Q37. What are Linux capabilities in the context of containers, and which are most dangerous?

**Answer:**

Linux divides root's privileges into discrete units called **capabilities**. Containers can be granted specific capabilities without running as full root. `CAP_NET_BIND_SERVICE`, for example, allows binding to ports below 1024 without full root.

**Most dangerous capabilities:**

| Capability | Risk |
|------------|------|
| `CAP_SYS_ADMIN` | The "kitchen sink" — mount filesystems, configure devices, set hostname, load kernel modules, `ptrace`, etc. Equivalent to root for most purposes. |
| `CAP_NET_ADMIN` | Modify firewall rules, routing tables, MAC addresses. Can bypass NetworkPolicy in some CNIs. |
| `CAP_SYS_PTRACE` | Attach debugger to any process. Can read memory of any process including secrets. |
| `CAP_NET_RAW` | Create raw sockets. Enables ARP spoofing, ICMP flooding, and network sniffing. |
| `CAP_SYS_MODULE` | Load/unload kernel modules. Full kernel-level code execution. |
| `CAP_DAC_OVERRIDE` | Override filesystem permission checks. Read any file regardless of permissions. |
| `CAP_SETUID` / `CAP_SETGID` | Change UID/GID. Can escalate to root. |
| `CAP_CHOWN` | Change file ownership arbitrarily. |

**Default capabilities granted to Docker containers (subset to audit):**
`CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `FSETID`, `KILL`, `SETGID`, `SETUID`, `SETPCAP`, `NET_BIND_SERVICE`, `NET_RAW`, `SYS_CHROOT`, `MKNOD`, `AUDIT_WRITE`, `SETFCAP`

**Best practice:** Drop ALL capabilities (`drop: [ALL]`) and add back only what's explicitly needed. For most web services: none needed. For network tools: only `NET_BIND_SERVICE`. Treat any request to add `SYS_ADMIN` or `NET_ADMIN` as a red flag requiring architectural review.

---

### Q38. What is seccomp, and how do you create and apply a custom seccomp profile in Kubernetes?

**Answer:**

**seccomp (Secure Computing Mode)** is a Linux kernel security feature that restricts the system calls a process can make. In containers, it's a critical defense layer — even if an attacker achieves code execution inside a container, they're restricted in what kernel operations they can perform.

**Profile types:**
- `Unconfined` — No seccomp (default in older Kubernetes; avoid).
- `RuntimeDefault` — Uses the container runtime's default profile (~300 syscalls blocked).
- `Localhost` — A custom JSON profile stored on the node.

**Custom profile format (JSON):**
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "accept4", "access", "arch_prctl", "bind", "brk",
        "clone", "close", "connect", "dup2", "epoll_create1",
        "epoll_ctl", "epoll_wait", "execve", "exit", "exit_group",
        "fstat", "futex", "getdents64", "getpid", "getrandom",
        "getsockname", "getsockopt", "listen", "lstat", "mmap",
        "mprotect", "munmap", "nanosleep", "newfstatat", "open",
        "openat", "pipe2", "poll", "prctl", "pread64",
        "read", "recvfrom", "rt_sigaction", "rt_sigprocmask",
        "rt_sigreturn", "sendto", "set_robust_list", "set_tid_address",
        "setsockopt", "sigaltstack", "socket", "stat", "uname", "write"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

**Applying in Kubernetes:**

1. **Node-local profiles** — Place JSON file on each node at `/var/lib/kubelet/seccomp/profiles/myapp.json`.

```yaml
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: profiles/myapp.json
```

2. **Security Profiles Operator (SPO)** — A Kubernetes operator that manages seccomp/AppArmor/SELinux profiles as CRDs, distributes to nodes, and can generate profiles from `strace` recordings:

```yaml
apiVersion: security-profiles-operator.x-k8s.io/v1beta1
kind: SeccompProfile
metadata:
  name: my-app-profile
spec:
  defaultAction: SCMP_ACT_ERRNO
  syscalls:
    - action: SCMP_ACT_ALLOW
      names: [read, write, open, close, ...]
```

**Profile generation:** Use `strace` or the SPO's recording mode to capture syscalls during normal operation, then create a minimal allowlist.

---

### Q39. What is AppArmor, and how does it complement seccomp in Kubernetes?

**Answer:**

**AppArmor** is a Linux Mandatory Access Control (MAC) system that restricts programs' capabilities using profiles. While seccomp operates at the **syscall level** (what system calls the process can make), AppArmor operates at the **resource access level** (what files, network operations, and capabilities the process can access).

**Seccomp vs AppArmor:**

| Feature | seccomp | AppArmor |
|---------|---------|----------|
| Level | Syscall | Resource (file, network, capability) |
| Granularity | Per syscall argument | Per path, network operation |
| Default support | All modern kernels | Debian/Ubuntu (not RHEL/CentOS by default) |
| Profile language | JSON | Text profiles |

**AppArmor profile example:**
```
#include <tunables/global>

profile my-app flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  network inet tcp,
  network inet udp,

  # Allow read access to app directory
  /app/** r,
  /app/bin/* ix,
  
  # Deny write to everything except /tmp
  deny /** w,
  /tmp/** rw,
  
  # Deny all capabilities except basic
  deny capability sys_admin,
  deny capability net_admin,
  deny capability net_raw,
}
```

**Applying to Kubernetes pods (annotation-based, legacy):**
```yaml
metadata:
  annotations:
    container.apparmor.security.beta.kubernetes.io/mycontainer: localhost/my-app
```

**Applying via securityContext (Kubernetes 1.30+):**
```yaml
securityContext:
  appArmorProfile:
    type: Localhost
    localhostProfile: my-app
```

**Defense-in-depth value:**  
AppArmor catches cases seccomp misses. Example: a container that has `open` syscall allowed (needed for file I/O) but should not be able to open `/etc/shadow`. AppArmor enforces this path-based restriction while seccomp cannot.

Use both together for maximum containment.

---

### Q40. Explain container image immutability and how to enforce it in production.

**Answer:**

**Image immutability** means containers are never updated in-place — they're replaced. Once a container image is built and pushed with a specific tag or digest, it never changes. This is a foundational security principle.

**Why it matters:**
- Prevents in-place patching that creates drift between the running container and the known image.
- Enables reproducibility — the same image always produces the same behavior.
- Makes supply chain verification meaningful (you verify a specific immutable artifact).
- `readOnlyRootFilesystem: true` enforces this at runtime — prevents the container from modifying itself.

**Enforcement at the image level:**

1. **Pin by digest, not tag:**
```yaml
# Tag is mutable — the same tag can point to different images
image: nginx:1.25  # BAD

# Digest is immutable — cryptographically unique
image: nginx@sha256:a4b7...  # GOOD
```

2. **Policy enforcement with Kyverno:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-image-digest
spec:
  rules:
    - name: check-digest
      match:
        resources:
          kinds: [Pod]
      validate:
        message: "Images must be pinned by digest"
        pattern:
          spec:
            containers:
              - image: "*@sha256:*"
```

3. **Cosign signature verification with Kyverno:**
```yaml
rules:
  - name: verify-signature
    verifyImages:
      - imageReferences: ["registry.example.com/*"]
        attestors:
          - count: 1
            entries:
              - keys:
                  publicKeys: |-
                    -----BEGIN PUBLIC KEY-----
                    ...
```

4. **Read-only container filesystem:**
```yaml
securityContext:
  readOnlyRootFilesystem: true
```

5. **Distroless/minimal base images** — Reduce the attack surface by removing shells, package managers, and debugging tools from production images.

---

### Q41. What is the risk of privileged containers and `hostPID`/`hostIPC` flags?

**Answer:**

These flags are the nuclear options of container security — any pod with these settings effectively has node-level access.

**`privileged: true`:**
- The container gets all Linux capabilities (including `SYS_ADMIN`, `SYS_MODULE`).
- Can see and interact with all devices.
- Can mount arbitrary filesystems including the host's `/`.
- **Escape technique:** Mount the host filesystem via `nsenter --target 1 --mount --uts --ipc --net --pid -- bash` or by mounting `/` via the device node.

**`hostPID: true`:**
- The container joins the host's PID namespace.
- Can see ALL processes on the node.
- Can send signals to any process (including `SIGKILL` to system processes).
- Can read `/proc/<pid>/environ` of any process — this often contains secrets, credentials, environment variables of other pods on the same node.
- Can inject code into other processes via `ptrace` (with `SYS_PTRACE` capability).

**`hostIPC: true`:**
- Shares the host's IPC namespace.
- Can attach to shared memory segments of other processes.
- Can manipulate semaphores used by system processes.
- Less common attack vector but a foothold for inter-process attacks.

**Real attack scenario with `hostPID`:**
```bash
# Inside a container with hostPID: true
# Read environment variables of another pod's process
cat /proc/$(pgrep -f "my-app")/environ | tr '\0' '\n'
# Output: SECRET_KEY=supersecret DATABASE_PASSWORD=db_password_here
```

**Prevention:**
- PSA `baseline` blocks `privileged` and `hostPID`/`hostIPC`/`hostNetwork`.
- Never allow these in application namespaces.
- For system components that legitimately need them (node-level DaemonSets), restrict to `kube-system` with tight RBAC on who can create pods there.

---

### Q42. What is a distroless container image, and what are the security benefits and operational tradeoffs?

**Answer:**

**Distroless images** (pioneered by Google) contain only the application runtime and its dependencies — no shell (`bash`, `sh`), no package manager (`apt`, `yum`), no debugging utilities (`curl`, `wget`, `strace`).

**Security benefits:**

1. **No shell = no easy code execution** — If an attacker exploits a vulnerability (RCE) in your app, they can't easily run shell commands, install malware, or pivot. They're limited to what the application binary itself can do.

2. **Smaller attack surface** — Fewer installed packages means fewer CVEs to worry about. A minimal Go binary in `gcr.io/distroless/static` may have 0 OS-level CVEs.

3. **Smaller image size** — Less to scan, faster to pull, less storage.

4. **No package manager** — Can't `apt install nc` to add netcat as a pivot tool.

**Operational tradeoffs:**

1. **No debugging tools** — Can't `exec` into the container and run `curl`, `ss`, `ps`, `strace`. Must use `kubectl cp` or ephemeral debug containers instead.

2. **Ephemeral debug containers** — Kubernetes 1.23+ stable feature to attach a debug container:
```bash
kubectl debug -it <pod> --image=busybox --target=<container>
```

3. **Build complexity** — Multi-stage Dockerfiles required:
```dockerfile
# Build stage
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o api .

# Final stage - distroless
FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/api /api
USER nonroot:nonroot
ENTRYPOINT ["/api"]
```

4. **Signal handling** — Distroless often uses `nonroot` user. Ensure your process handles `SIGTERM` for graceful shutdown.

**Recommendation:** Distroless for production. Full base image with debugging tools for development/testing. Never run development images in production.

---

### Q43. How does OPA/Gatekeeper differ from Kyverno, and when would you choose one over the other?

**Answer:**

Both are policy engines that operate as admission webhooks for Kubernetes, but they have different design philosophies.

**OPA/Gatekeeper:**
- **Language:** Rego (a purpose-built Datalog-like logic language).
- **Model:** Constraint templates define the policy schema (CRD); Constraints are instances with parameters.
- **Expressiveness:** Rego is extremely powerful — can express complex multi-resource policies, cross-resource validation.
- **Ecosystem:** OPA is general-purpose (can be used outside Kubernetes for API gateway policies, Terraform, etc.).
- **Learning curve:** Rego takes significant time to master.

```rego
# Gatekeeper: require resource limits
package k8srequiredlimits

violation[{"msg": msg}] {
  container := input.review.object.spec.containers[_]
  not container.resources.limits.cpu
  msg := sprintf("Container %v must have CPU limits", [container.name])
}
```

**Kyverno:**
- **Language:** YAML/JSON (no new language to learn).
- **Model:** Policies directly in YAML with pattern matching.
- **Capabilities:** Validate, Mutate (auto-fix), Generate (create related resources), Verify Images.
- **Simpler for YAML-native teams.**
- **Built-in image verification** with Cosign.
- **Less powerful** for highly complex cross-resource logic.

```yaml
# Kyverno: require resource limits
apiVersion: kyverno.io/v1
kind: ClusterPolicy
spec:
  rules:
    - name: require-limits
      validate:
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    cpu: "?*"
                    memory: "?*"
```

**Choosing:**

| Factor | Choose OPA/Gatekeeper | Choose Kyverno |
|--------|----------------------|----------------|
| Team expertise | Security engineers comfortable with code | Platform/DevOps teams |
| Policy complexity | Complex multi-resource, cross-namespace logic | Standard Kubernetes policy patterns |
| OPA already used | For API gateways, Terraform, etc. | N/A |
| Image verification | External tooling needed | Built-in Cosign support |
| Mutation needs | Possible but complex | First-class feature |
| Policy reporting | External tooling | Built-in PolicyReport CRD |

**Enterprise trend:** Many organizations use **both** — Gatekeeper for complex governance policies, Kyverno for mutation and image verification.

---

### Q44. What are init containers from a security perspective? How can they be misused?

**Answer:**

**Init containers** run to completion before any app containers start. They share the pod's volumes and network namespace but have their own image, command, and security context.

**Legitimate security uses:**
- Validate configuration or secrets before the main app starts.
- Set file permissions on mounted volumes.
- Wait for dependencies to become available.
- Generate certificates or tokens to be consumed by the main container.

**Security misuse scenarios:**

1. **Bypass security context of the main container:**
   If the main container has `readOnlyRootFilesystem: true` and `allowPrivilegeEscalation: false`, an init container can run as root, write malicious files to a shared volume (emptyDir), and the main container inherits those files.

2. **Exfiltrate secrets before the main app:**
   Init containers have access to the same Secrets and environment variables as the main container. A compromised supply chain could add an init container to exfiltrate all mounted secrets before the app starts.

3. **Network reconnaissance:**
   Init containers can perform network scans during the cluster bootstrap window before NetworkPolicy might fully apply.

4. **Sidecars injected by malicious mutating webhooks:**
   While technically sidecars (not init containers), a malicious webhook could inject additional containers that run alongside your app.

**Security hardening for init containers:**

- Apply the same security context to init containers as to the main container.
- Review init containers in admission policies — they're often overlooked.

```yaml
# OPA/Gatekeeper checking init containers too
containers := array.concat(
  input.review.object.spec.containers,
  input.review.object.spec.initContainers  # Don't forget init containers!
)
```

- Verify init container images with the same image signing policies.
- Restrict what volumes init containers can write to.

---

### Q45. How does the Kubernetes resource quota system contribute to security, and what are its gaps?

**Answer:**

**ResourceQuota** limits the total resources (CPU, memory, object counts) that can be consumed in a namespace. From a security perspective, it's primarily a **denial-of-service defense** and a **blast radius limiter**.

**Security contributions:**

1. **Prevent resource exhaustion (DoS):**
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
    services: "10"
    persistentvolumeclaims: "20"
    secrets: "50"
    configmaps: "30"
```

2. **Limit object proliferation:**
   Restricting `pods`, `services`, and `secrets` counts prevents a compromised tenant from creating thousands of pods for cryptomining or thousands of Services for port scanning.

3. **Enforce resource limits as a prerequisite:**
   LimitRange can require that all containers have resource requests and limits set — preventing unbounded resource consumption.

**Security gaps:**

1. **No isolation** — ResourceQuota doesn't prevent one pod from consuming 100% of its quota and starving others within the same namespace.

2. **No node-level isolation** — Quotas don't enforce which nodes a pod can run on. A noisy neighbor can still impact node performance.

3. **Ephemeral storage often unconstrained** — Add `requests.ephemeral-storage` and `limits.ephemeral-storage` to prevent disk exhaustion.

4. **PriorityClass bypass** — Pods with high `PriorityClass` can preempt quota enforcement in some configurations.

5. **No network quota** — Cannot limit bandwidth consumption.

6. **Extended resources unconstrained** — GPU counts, custom resources may not be quoted.

**LimitRange for defaults:**
```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
spec:
  limits:
    - type: Container
      default:
        cpu: 500m
        memory: 256Mi
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      max:
        cpu: "4"
        memory: 4Gi
```

---

### Q46. What is the Container Runtime Security context `seccompProfile` with type `RuntimeDefault`, and what syscalls does it typically block?

**Answer:**

`RuntimeDefault` applies the container runtime's (containerd or CRI-O) built-in default seccomp profile. This profile is derived from Docker's default seccomp profile, which was compiled from an analysis of common container workloads.

**What it blocks (selected):**

| Syscall | Reason Blocked |
|---------|----------------|
| `kexec_load` | Load a new kernel — only relevant on bare metal |
| `mount` | Mount filesystems (allows namespace escape) |
| `umount2` | Unmount (same risk) |
| `ptrace` | Attach debugger to processes (credential theft) |
| `reboot` | Reboot the system |
| `swapon/swapoff` | Manage swap space |
| `syslog` | Read kernel ring buffer |
| `settimeofday` | Set system time |
| `clock_settime` | Set clock |
| `vhangup` | Hangup a terminal |
| `pivot_root` | Change root filesystem (namespace escape) |
| `init_module` / `finit_module` | Load kernel modules |
| `delete_module` | Unload kernel modules |
| `iopl` / `ioperm` | I/O port access (hardware access) |
| `perf_event_open` | Access performance monitoring (side-channel) |

**What it does NOT block (notable):**
- Standard I/O syscalls (`read`, `write`, `open`, `close`).
- Networking (`socket`, `connect`, `bind`, `send`, `recv`).
- Process management (`fork`, `exec`, `wait`).
- Memory management (`mmap`, `mprotect`, `brk`).

**Recommendation:**
- `RuntimeDefault` is a good baseline — enable it with `pod-security.kubernetes.io/enforce: restricted`.
- For security-sensitive workloads, go further with a custom profile generated from your app's actual syscall usage (use SPO recording mode).
- `Localhost` with a minimal custom profile is the gold standard.

---

### Q47. How would you detect and respond to a cryptomining attack on a Kubernetes cluster?

**Answer:**

**Cryptomining attacks** are the most common attack against exposed Kubernetes clusters. Attackers exploit exposed API servers, dashboards, or vulnerable applications to deploy cryptominer DaemonSets or Deployments.

**Detection signals:**

**1. Unusual CPU usage:**
- Pods consuming near 100% CPU with no legitimate reason.
- `kubectl top pods --all-namespaces | sort -k3 -nr`.
- Prometheus alert: `container_cpu_usage_seconds_total` spike.

**2. Unknown container images:**
- Images from Docker Hub by unknown accounts.
- `kubectl get pods -A -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}' | sort -u`

**3. Falco runtime alerts:**
```yaml
- rule: Cryptocurrency Mining Binary Execution
  condition: >
    spawned_process and container and
    (proc.name in (xmrig, minerd, cpuminer, ethminer, cgminer))
  output: "Crypto miner detected (pod=%k8s.pod.name user=%user.name)"
  priority: CRITICAL
```

**4. Network connections to mining pools:**
- Outbound connections to common mining pool ports (3333, 4444, 5555, 7777, 14444, 45700).
- Cilium Hubble or CNI flow logs showing unexpected outbound connections.

**5. New DaemonSets or Deployments in unusual namespaces.**

**6. Audit log alerts:**
- New ClusterRoleBinding to `cluster-admin`.
- Pod creation in `kube-system` or `default` namespace.

**Response procedure:**

1. **Contain:** NetworkPolicy egress deny to mining pool IPs. Cordon affected nodes.
2. **Identify:** Which pod, which image, which ServiceAccount created it, what RBAC path was used.
3. **Delete:** `kubectl delete <resource>` — be careful of DaemonSets respawning.
4. **Audit:** Trace the initial access vector — exposed dashboard? Vulnerable app? Stolen credentials?
5. **Remediate root cause:** Patch the vulnerability, rotate compromised credentials, revoke the abused ServiceAccount.
6. **Review:** Were there Falco rules that should have caught this earlier? Gap analysis.

---

### Q48. What is the Container escape technique using `hostPath` volume mounts, and how do you prevent it?

**Answer:**

**hostPath** mounts expose directories from the host node's filesystem into a container. Misconfigured hostPath mounts are one of the most common container escape techniques.

**Escape scenario 1 — Docker socket:**
```yaml
volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
```
With the Docker socket mounted, a container can control the Docker daemon on the host — creating privileged containers, running arbitrary commands on the host, or reading any file.

**Escape scenario 2 — `/` or `/etc` mount:**
```yaml
volumes:
  - name: host-root
    hostPath:
      path: /
      type: Directory
```
Direct access to the entire host filesystem. Can read `/etc/shadow`, `/root/.kube/config`, modify `/etc/cron.d` for persistence.

**Escape scenario 3 — `/proc` mount:**
Access to `/proc/sysrq-trigger` allows rebooting the host. Access to `/proc/kcore` can reveal kernel memory.

**Escape scenario 4 — Container runtime socket:**
```yaml
path: /run/containerd/containerd.sock  # containerd
path: /run/crio/crio.sock             # CRI-O
```
Same as Docker socket — allows controlling the runtime to escape to any container.

**Prevention:**

1. **PSA `baseline`+ blocks dangerous hostPath mounts.**

2. **OPA/Gatekeeper policy:**
```rego
deny[msg] {
  volume := input.review.object.spec.volumes[_]
  volume.hostPath
  dangerous_paths := {"/", "/etc", "/root", "/run", "/var/run"}
  dangerous_paths[volume.hostPath.path]
  msg := sprintf("hostPath %v is not allowed", [volume.hostPath.path])
}
```

3. **Kyverno — restrict hostPath to specific allowed paths:**
```yaml
validate:
  pattern:
    spec:
      volumes:
        - =(hostPath):
            path: "/data/logs"  # Only this path allowed
```

4. **When hostPath IS required** (node monitoring, log collection): Use `readOnly: true` and restrict to specific paths. Run only as DaemonSet in `kube-system` with dedicated ServiceAccount.

---

### Q49. What is the risk of running containers as root (UID 0), and why does `runAsNonRoot: true` not always help?

**Answer:**

**Why containers as root are dangerous:**

1. **Host escape risk** — If the container runtime, kernel, or namespace isolation has a vulnerability, root in the container = root on the host.
2. **File system access** — Can read any file mounted into the container, regardless of permissions.
3. **Signal sending** — Can send signals to any process (with appropriate capabilities).
4. **Capability granting** — Root processes can use capabilities like `SYS_ADMIN` if not explicitly dropped.
5. **Supply chain** — Many Docker Hub images default to running as root, importing an unreviewed third-party image and running as root is extremely risky.

**Why `runAsNonRoot: true` doesn't always help:**

1. **Image build problem** — If the image's `USER` directive is not set, the default is root. `runAsNonRoot: true` will cause the pod to fail to start (good!) — but many teams respond by just removing `runAsNonRoot` instead of fixing the image.

2. **Non-root UID that still has dangerous access** — Running as UID 1000 doesn't matter if the container has `CAP_DAC_OVERRIDE` (bypass file permissions) or `CAP_NET_ADMIN`.

3. **Volume ownership issues** — Mounted volumes may have files owned by root, inaccessible to a non-root container. `fsGroup` + `fsGroupChangePolicy` helps, but is often misconfigured.

4. **`allowPrivilegeEscalation: true` (default!)** — A non-root container with `allowPrivilegeEscalation: true` can setuid back to root if a setuid binary exists in the image. **Always set `allowPrivilegeEscalation: false`.**

5. **Namespace user remapping (`--userns-remap`)** — Some organizations use user namespace remapping so container root maps to a high UID on the host. This helps but requires runtime configuration and has compatibility issues.

**Complete non-root hardening requires all of:**
- `runAsNonRoot: true` + `runAsUser: <non-zero>`
- `allowPrivilegeEscalation: false`
- `capabilities: drop: ALL`
- Base image with USER directive set
- `readOnlyRootFilesystem: true`

---

### Q50. How do you handle secrets injection into pods securely? Compare environment variables vs volume mounts.

**Answer:**

**Option 1: Environment Variables**

```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: password
```

**Risks:**
- Env vars are visible via `/proc/<pid>/environ` to any process that can read proc (including other containers if `hostPID`).
- Env vars are logged by many frameworks and debugging tools.
- Env vars are inherited by child processes.
- Visible in `kubectl describe pod` output (base64 in etcd, but metadata exposed).

**Option 2: Volume Mounts**

```yaml
volumes:
  - name: secret-vol
    secret:
      secretName: db-secret
      defaultMode: 0400  # Read-only for owner only
volumeMounts:
  - name: secret-vol
    mountPath: /run/secrets
    readOnly: true
```

**Advantages over env vars:**
- Secrets are files, not memory — can be more tightly controlled with filesystem permissions.
- Secrets are automatically updated in the volume when the Kubernetes Secret changes (with some delay).
- Not logged by most frameworks.
- Can use `defaultMode: 0400` to restrict to owner-only read.

**Option 3: External Secret Stores (Best Practice)**

Avoid storing secrets in Kubernetes Secrets at all. Use:

- **Vault Agent Injector** — Injects secrets as files via init containers and sidecars.
- **External Secrets Operator** — Syncs secrets from AWS Secrets Manager/Parameter Store, GCP Secret Manager, Azure Key Vault into Kubernetes Secrets (still in etcd, but the source of truth is external).
- **CSI Secret Store Driver** — Mounts secrets directly from external stores (Vault, AWS, Azure) into pods as volumes, bypassing Kubernetes Secrets in etcd entirely.

```yaml
volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: aws-secrets-manager
```

**Summary:**
- Prefer volume mounts over env vars.
- Prefer CSI Secret Store over both for most sensitive secrets.
- Always enable etcd encryption at rest.
- Use projected volumes with short-lived tokens for dynamic secrets.

---

## 5. Secrets Management

---

### Q51. What is the Secrets Store CSI Driver, and how does it work with Vault and AWS Secrets Manager?

**Answer:**

The **Secrets Store CSI Driver** (CNCF project) allows pods to mount secrets from external secret stores directly as volumes, without storing them in Kubernetes Secrets (etcd).

**Architecture:**
1. `SecretProviderClass` CRD defines what secrets to fetch and from where.
2. The CSI driver daemon runs on each node as a DaemonSet.
3. When a pod with a CSI volume is scheduled, the kubelet calls the CSI driver.
4. The driver authenticates to the external secret store and fetches the specified secrets.
5. Secrets are mounted into the pod's filesystem via `tmpfs` (in-memory).

**With HashiCorp Vault:**

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-db-credentials
spec:
  provider: vault
  parameters:
    vaultAddress: "https://vault.example.com"
    roleName: "my-app-role"
    objects: |
      - objectName: "db-password"
        secretPath: "secret/data/production/db"
        secretKey: "password"
```

**With AWS Secrets Manager:**

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: aws-db-credentials
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "arn:aws:secretsmanager:us-east-1:123456:secret:prod/db"
        objectType: "secretsmanager"
        jmesPath:
          - path: "password"
            objectAlias: "db-password"
```

**Security benefits:**
- Secrets never touch etcd — significantly reduces exposure from etcd compromise.
- Automatic rotation — the CSI driver polls for updated secrets and updates the mounted volume.
- Audit trail — all secret access is logged in Vault/AWS.
- Revocation — disabling access in Vault immediately prevents new pod mounts.

**Tradeoff:** Harder to debug; adds a dependency on external secret store availability.

---

### Q52. How do you implement secret rotation without downtime in Kubernetes?

**Answer:**

Secret rotation is a critical security operation — compromised or aged secrets must be replaced without interrupting service.

**Challenges:**
- Applications often cache secrets at startup.
- Multiple pods may be using the same secret simultaneously.
- Rotating at the wrong time causes authentication failures.

**Strategies:**

**1. Volume-mounted secrets with inotify:**
When Kubernetes Secrets are mounted as volumes, Kubernetes automatically updates the file when the Secret is updated (within `--sync-period`, typically 1 minute). Applications that watch for file changes can reload credentials without restart.

```go
// Watch for secret file changes
watcher, _ := fsnotify.NewWatcher()
watcher.Add("/run/secrets/db-password")
for event := range watcher.Events {
  if event.Op&fsnotify.Write == fsnotify.Write {
    reloadDatabaseCredential()
  }
}
```

**2. Dual-version secrets (overlap window):**
1. Add the new password to the database (dual-active period).
2. Update Kubernetes Secret with new password.
3. Roll pods (or wait for mounted secret refresh).
4. Remove old password from database.

**3. External Secrets Operator with rotation:**
- Configure AWS Secrets Manager / Vault to rotate the secret.
- External Secrets Operator polls and syncs to Kubernetes Secret.
- Applications using volume mounts get the update automatically.

**4. Rolling restarts:**
```bash
kubectl rollout restart deployment/api-server
```
Ensures new pods start with the latest secret values. Use rolling update strategy with `maxUnavailable: 0` to maintain availability.

**5. Vault dynamic secrets:**
Vault generates short-lived database credentials for each pod. When credentials expire, the pod's Vault agent sidecar renews them automatically. Eliminates the concept of "rotation" — credentials are always fresh.

---

### Q53. What is the External Secrets Operator, and how does it differ from the Secrets Store CSI Driver?

**Answer:**

Both solve the problem of sourcing secrets from external stores, but with different approaches:

**External Secrets Operator (ESO):**
- Syncs secrets FROM external stores (AWS SM, GCP SM, Vault, Azure KV) INTO Kubernetes Secret objects.
- Secrets still exist in etcd (with encryption at rest).
- Applications use secrets normally (env vars or volume mounts from Kubernetes Secrets).
- Polls external store on a configurable schedule and updates the Kubernetes Secret.

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: db-secret  # Creates/updates this Kubernetes Secret
  data:
    - secretKey: password
      remoteRef:
        key: prod/database
        property: password
```

**Secrets Store CSI Driver:**
- Mounts secrets directly from external stores into pods as volumes.
- Secrets do NOT exist in Kubernetes (not in etcd).
- Tighter security — no etcd exposure.
- Pod-lifecycle bound — secrets are mounted when pod starts, unmounted when pod stops.

**Comparison:**

| Feature | ESO | CSI Driver |
|---------|-----|------------|
| Secret in etcd | Yes | No |
| App changes needed | No (uses K8s Secret) | Requires volume mount |
| Rotation propagation | Via K8s Secret update | Direct (faster) |
| Env var support | Yes (via K8s Secret) | Indirect (via secretObjects) |
| Audit trail in K8s | Yes (via audit logs) | Yes |
| Complexity | Lower | Higher |

**Combined approach:** Use CSI for most sensitive secrets (DB passwords, API keys), ESO for less sensitive config that benefits from K8s-native access patterns.

---

### Q54. How do you securely manage Kubernetes Secrets in a GitOps workflow?

**Answer:**

GitOps (ArgoCD, Flux) means your cluster state is defined in Git. Storing raw Kubernetes Secrets in Git is equivalent to storing plaintext passwords in source control — catastrophic.

**Solutions:**

**1. Sealed Secrets (Bitnami):**
- `kubeseal` CLI encrypts a Kubernetes Secret using the cluster's public key.
- The encrypted `SealedSecret` is safe to store in Git.
- The Sealed Secrets controller in the cluster decrypts it using its private key.

```bash
kubectl create secret generic db-secret \
  --from-literal=password=supersecret \
  --dry-run=client -o yaml | \
  kubeseal --format yaml > sealed-secret.yaml
# sealed-secret.yaml is safe to commit
```

**Caveat:** The private key is in the cluster — if the cluster is compromised, all sealed secrets can be decrypted. Rotate the sealing key regularly.

**2. SOPS (Mozilla) + age/PGP:**
- Encrypt secrets at file level using SOPS.
- Commit encrypted files to Git.
- ArgoCD/Flux with SOPS plugin decrypts during sync.

```bash
sops --encrypt --age <public-key> secret.yaml > secret.enc.yaml
```

**3. External Secrets Operator (recommended for production):**
- Store secrets in AWS/GCP/Vault, NOT in Git.
- Commit `ExternalSecret` CRD manifests (which reference secret paths, not values).
- ESO fetches actual values from external stores at runtime.
- Git contains zero secret material.

**4. Vault + ArgoCD Vault Plugin:**
- ArgoCD uses the AVP (ArgoCD Vault Plugin) to inject secret values from Vault at deploy time.
- Manifests in Git use placeholder syntax: `<path:secret/data/prod#password>`.

**Best practice order:**
1. External Secrets Operator or CSI Driver (no secret values in Git).
2. SOPS (values in Git but encrypted with key outside Git).
3. Sealed Secrets (values in Git encrypted with cluster key).
4. **Never** raw Kubernetes Secret YAML in Git.

---

### Q55. Explain SPIFFE and SPIRE and how they relate to Kubernetes workload identity.

**Answer:**

**SPIFFE (Secure Production Identity Framework for Everyone):**  
An open standard for workload identity. Defines a URI scheme for identities (`spiffe://trust-domain/path`) and a standard certificate format (SVID — SPIFFE Verifiable Identity Document).

**SPIRE (SPIFFE Runtime Environment):**  
The reference implementation of SPIFFE. Consists of:
- **SPIRE Server** — Central authority that issues SVIDs.
- **SPIRE Agent** — Runs on each node, attests workloads and fetches SVIDs.

**How SPIRE attests Kubernetes workloads:**

1. The SPIRE Agent on each node uses the node's identity (kubelet credentials, cloud provider attestation) to authenticate to the SPIRE Server.
2. When a workload calls the SPIFFE Workload API (a Unix socket), the Agent uses kernel attestation (namespaces, cgroups) to identify the pod.
3. The Agent fetches a short-lived X.509 SVID for the workload's identity (`spiffe://company.com/ns/production/sa/api-server`).
4. The SVID is rotated automatically before expiry.

**Integration with Kubernetes:**
- Istio's Citadel CA uses SPIFFE SVIDs for mTLS certificates.
- The projected SA token endpoint can be federated with SPIRE.
- SPIRE SVIDs can authenticate to Vault, AWS, GCP, or any OIDC-compatible system.

**Why SPIFFE matters:**
- Workload identity is cryptographically bound to the workload — not a static secret that can be stolen.
- Works across clouds and on-premises — a universal identity layer.
- Short-lived certificates mean compromise windows are minimal.
- Integrates with service meshes, secret managers, and authorization systems.

---

### Q56. How would you audit Kubernetes Secrets access in a production cluster?

**Answer:**

Secrets are the highest-value target in a Kubernetes cluster. Auditing their access requires multiple layers.

**1. API Server Audit Logs:**

Configure audit policy to log all Secret operations:
```yaml
- level: Metadata
  resources:
    - group: ""
      resources: ["secrets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

> **Critical:** Use `Metadata` level, NOT `Request` or `RequestResponse` — those would log secret values.

**2. SIEM queries for sensitive patterns:**

- Any `get` on secrets from non-automated system accounts → alert.
- `list` on secrets (retrieves all secrets in namespace) → immediate alert.
- Secret access from unusual source IPs.
- Service accounts accessing secrets outside their namespace.

**3. Kubernetes audit event structure:**

```json
{
  "verb": "get",
  "requestURI": "/api/v1/namespaces/production/secrets/db-credentials",
  "user": {
    "username": "system:serviceaccount:ci-cd:deployer",
    "groups": ["system:serviceaccounts"]
  },
  "sourceIPs": ["10.0.1.52"],
  "objectRef": {
    "resource": "secrets",
    "namespace": "production",
    "name": "db-credentials"
  }
}
```

**4. Vault audit logs:**

If using Vault, every secret access is logged with requestor identity, path, and timestamp. Route to SIEM.

**5. RBAC minimization:**

```bash
# Who can get secrets in production?
kubectl who-can get secrets -n production
# Who can list secrets?
kubectl who-can list secrets -n production
```

**6. Behavioral anomaly detection:**

Alert on: first-ever access to a secret, access outside business hours, access from a new IP, bulk access to many secrets within a short window.

---

### Q57. What is the risk of environment variable injection of secrets and how do logs exfiltrate them?

**Answer:**

**The core problem:** Environment variables are accessible to the process, its child processes, and any agent that can read `/proc/<pid>/environ`. Multiple logging, monitoring, and debugging systems inadvertently capture them.

**Exfiltration vectors:**

1. **Application crash dumps** — JVM heap dumps, Node.js `--inspect` dumps, Python traceback dumps — all may capture env vars.

2. **Framework logging** — Spring Boot Actuator, Express.js error handlers, Rails error pages can log all env vars in debug mode.

3. **Orchestration logs** — Helm chart rendering logs, CI/CD pipeline logs that print env for debugging.

4. **APM agents** — Datadog, New Relic, Dynatrace agents often capture env vars for process fingerprinting.

5. **`kubectl describe pod`** — Shows env var names (values are base64 in etcd, but the reference is visible).

6. **Container introspection** — `docker inspect` / `crictl inspect` on the node shows all env vars of running containers.

**Example inadvertent exposure:**
```javascript
// Common Express.js error handler
app.use((err, req, res, next) => {
  console.error('Error:', err, 'Environment:', process.env);  // Logs ALL env vars
});
```

**Mitigation:**
- Never log `process.env` or equivalent.
- Use secret scanning in CI to detect secrets in application logs.
- Prefer file-based secret injection (volume mounts with `readOnlyRootFilesystem`).
- For env vars that must be used, ensure secrets are consumed once at startup and not stored in application-level variables that get logged.
- Use structured logging with explicit allowlists for what gets logged.

---

### Q58. How do you handle secrets in Helm charts securely?

**Answer:**

Helm is the dominant Kubernetes package manager, and secret handling is one of its weakest points by default.

**Anti-patterns (never do):**

```yaml
# values.yaml committed to Git
database:
  password: "supersecret"  # NEVER
```

```yaml
# templates/secret.yaml
data:
  password: {{ .Values.database.password | b64enc }}  # Encodes the plaintext from values
```

**Secure patterns:**

**1. Reference existing Secrets (don't create them):**
```yaml
# templates/deployment.yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {{ .Values.database.existingSecret }}  # Pre-existing secret
        key: password
```
```yaml
# values.yaml (safe to commit)
database:
  existingSecret: "db-credentials"  # Reference, not value
```

**2. Helm Secrets plugin (SOPS integration):**
```bash
helm secrets enc values.secret.yaml    # Encrypt
helm secrets dec values.secret.yaml    # Decrypt
helm secrets install myapp . -f values.secret.yaml  # Deploy with decryption
```

**3. External Secrets + Helm:**
Include `ExternalSecret` templates in your chart. The actual values are never in Helm's values:
```yaml
# templates/external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
spec:
  secretStoreRef:
    name: {{ .Values.secretStore }}
  target:
    name: {{ include "app.fullname" . }}-db
  data:
    - secretKey: password
      remoteRef:
        key: {{ .Values.secretPath }}
```

**4. Avoid `helm get values`** — This command retrieves all values including secrets from Helm's release history in the cluster (stored as Secrets in `kube-system`). Use RBAC to restrict who can run `helm get values` on production releases.

---

## 6. Supply Chain & Image Security

---

### Q59. What is the software supply chain attack surface for Kubernetes, and how do you defend it?

**Answer:**

The **software supply chain** in Kubernetes encompasses everything between source code and a running container: source repos, CI/CD pipelines, base images, registries, Helm charts, and the deployment manifests themselves.

**Attack vectors across the supply chain:**

| Stage | Attack | Example |
|-------|--------|---------|
| Source code | Malicious dependency (typosquatting, dependency confusion) | event-stream npm incident |
| Build pipeline | CI runner compromise | SolarWinds-style build injection |
| Base image | Malicious base image on Docker Hub | cryptominer in `node:alpine` |
| Image registry | Registry poisoning, tag mutability | `latest` tag hijacking |
| Helm chart | Compromised chart repository | |
| Deployment manifest | Malicious manifest in GitOps repo | |
| Admission | Bypass of policy controls | |

**Defense framework (SLSA framework):**

**Level 1:** Build scripts generate provenance. Provenance is available.
**Level 2:** Builds are on a hosted CI platform. Provenance is authenticated.
**Level 3:** Build platform is hardened. Provenance is from a non-falsifiable source.
**Level 4:** Hermetic builds. Reviewed build definitions.

**Key controls:**

1. **Image signing with Cosign:**
```bash
cosign sign --key cosign.key registry.example.com/api:1.2.3
cosign verify --key cosign.pub registry.example.com/api:1.2.3
```

2. **SBOM generation:**
```bash
syft registry.example.com/api:1.2.3 -o spdx-json > sbom.json
```

3. **Vulnerability scanning in CI:**
```bash
trivy image --exit-code 1 --severity HIGH,CRITICAL registry.example.com/api:1.2.3
```

4. **Admission-time verification (Sigstore/Cosign + Kyverno).**

5. **Private registry with pull-through cache** — All images pulled from controlled registry, not directly from Docker Hub.

6. **Immutable tags** — Container registry configured to prevent tag overwriting.

---

### Q60. Explain Sigstore and how Cosign, Fulcio, and Rekor work together for keyless signing.

**Answer:**

**Sigstore** is an open-source project (backed by Google, Red Hat, Chainguard) that provides infrastructure for software signing, transparency, and verification.

**Components:**

**Cosign** — The CLI tool for signing and verifying container images (and other OCI artifacts like SBOMs and attestations).

**Fulcio** — A certificate authority that issues short-lived code signing certificates. Instead of managing long-term signing keys, Fulcio issues certificates bound to an OIDC identity (GitHub Actions, Google, Microsoft, etc.).

**Rekor** — An immutable, append-only transparency log (like Certificate Transparency for TLS) that records all signing events. Enables detection of unauthorized signatures.

**Keyless signing flow:**

1. CI/CD pipeline runs in GitHub Actions.
2. GitHub Actions provides an OIDC token proving the workflow's identity (`https://github.com/org/repo/.github/workflows/release.yml@refs/heads/main`).
3. `cosign sign` exchanges the OIDC token with **Fulcio** for a short-lived (10-minute) signing certificate.
4. Cosign signs the container image digest with the ephemeral key.
5. The signature and certificate are stored in the **OCI registry** alongside the image.
6. The signing event is recorded in **Rekor** (public transparency log).
7. The ephemeral private key is discarded.

**Verification:**

```bash
cosign verify \
  --certificate-identity-regexp="^https://github.com/org/repo" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  registry.example.com/api:1.2.3
```

**Benefits:**
- No long-lived signing keys to manage or rotate.
- Identity is tied to the OIDC provider (GitHub Actions workflow, not a person).
- Every signing event is in the public transparency log — impossible to sign without creating a record.

---

### Q61. What is a Software Bill of Materials (SBOM), and how do you use it in a Kubernetes security workflow?

**Answer:**

An **SBOM** is a machine-readable inventory of all components in a software artifact — dependencies, libraries, licenses, and their versions. It answers: "What is in this container image?"

**Standards:**
- **SPDX** (ISO/IEC 5962:2021) — Linux Foundation standard.
- **CycloneDX** — OWASP standard, preferred for security use cases.

**Generation:**

```bash
# Syft - generates SBOM from container images
syft registry.example.com/api:1.2.3 -o cyclonedx-json > sbom.json

# Trivy - generates and scans
trivy image --format cyclonedx registry.example.com/api:1.2.3 > sbom.json
```

**Attaching SBOM to image (OCI attestation):**

```bash
cosign attest --predicate sbom.json \
  --type cyclonedx \
  registry.example.com/api:1.2.3
```

**Kubernetes security workflow:**

1. **CI:** Generate SBOM for every built image.
2. **CI:** Scan SBOM against known CVE databases (Grype, Trivy).
3. **CI:** Attest SBOM to image with Cosign.
4. **Admission:** Kyverno policy verifies that an SBOM attestation exists for every image.
5. **Runtime:** When a CVE is disclosed (e.g., Log4Shell), query SBOM database to find all running containers affected — no manual scanning required.

```bash
# Find all running images with log4j
kubectl get pods -A -o json | jq '.items[].spec.containers[].image' | \
  xargs -I{} grype {} --fail-on high 2>/dev/null | grep log4j
```

**Regulatory value:** US Executive Order 14028 (2021) mandates SBOMs for software sold to the federal government. SBOM infrastructure is increasingly a compliance requirement.

---

### Q62. How do you implement image scanning in a CI/CD pipeline and enforce policies at admission time?

**Answer:**

Defense-in-depth requires scanning at multiple points — build time (proactive) and admission time (enforcement gate).

**Build-time scanning (CI):**

```yaml
# GitHub Actions example
- name: Scan container image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: registry.example.com/api:${{ github.sha }}
    format: sarif
    output: trivy-results.sarif
    severity: HIGH,CRITICAL
    exit-code: '1'  # Fail the pipeline
    ignore-unfixed: true  # Skip vulns with no fix available
```

**Registry scanning (continuous):**
- AWS ECR: Automated scanning on push (Basic or Enhanced with Inspector).
- GCR/GAR: Container Analysis on push.
- Harbor: Built-in Trivy/Clair scanning.
- Sysdig Secure: Registry scanning with policy gating.

**Admission-time enforcement:**

**Option 1: Kyverno image verification + scan attestation:**
```yaml
rules:
  - name: check-scan-attestation
    verifyImages:
      - imageReferences: ["registry.example.com/*"]
        attestations:
          - predicateType: https://trivy.dev/scan/v2
            attestors:
              - entries:
                  - keys:
                      publicKeys: <cosign-public-key>
            conditions:
              - all:
                  - key: "{{ request.object.results[].vulnerabilities[?severity == 'CRITICAL'] | length(@) }}"
                    operator: Equals
                    value: "0"
```

**Option 2: OPA/Gatekeeper with custom constraint:**

```rego
# Enforce maximum CVE severity
violation[msg] {
  image := input.review.object.spec.containers[_].image
  not is_scanned_and_clean(image)
  msg := sprintf("Image %v has not passed security scan", [image])
}
```

**Option 3: Admission webhook backed by Trivy:**
Trivy has an operator (`trivy-operator`) that continuously scans running workloads and reports via `VulnerabilityReport` CRDs. Admission webhook can query these reports.

**Caveat:** Never block production deployments ONLY on CVE findings without an exception workflow — you'll block critical incident response. Always have an override mechanism with audit trail.

---

### Q63. What is image tag pinning by digest, and why is it a security requirement?

**Answer:**

**Image tags are mutable** — the same tag (`nginx:1.25`, `myapp:latest`) can be pushed to point to a completely different image at any time. This means:

- Your deployment that worked yesterday with `nginx:1.25` could pull a completely different (potentially malicious) image tomorrow.
- Supply chain attacks can push poisoned images under existing tags.
- You cannot cryptographically verify what image was running.

**Image digests are immutable** — A digest is the SHA-256 hash of the image manifest. The same digest will always refer to exactly the same image content. It cannot be changed without changing the digest.

```
registry.example.com/nginx:1.25
# vs
registry.example.com/nginx@sha256:a4b71d9...  # Always exactly this image
```

**Production workflow:**

```bash
# After building and pushing
DIGEST=$(docker buildx imagetools inspect \
  registry.example.com/api:1.2.3 \
  --format '{{.Manifest.Digest}}')

# Use in deployment
kubectl set image deployment/api \
  api=registry.example.com/api@${DIGEST}
```

**GitOps with digest pinning:**
Tools like **Flux Image Reflector** and **ArgoCD Image Updater** can automatically update digest references in Git when new images are built and verified.

**Kyverno enforcement:**
```yaml
validate:
  pattern:
    spec:
      containers:
        - image: "*@sha256:*"
  message: "All images must be pinned by SHA256 digest"
```

**`imagePullPolicy: Never`:** In production, if you've pulled and verified the image, set `Never` to prevent the node from re-pulling (potentially a different image) during pod restarts. Use `Always` only with digest pinning.

---

### Q64. How do you secure a private container registry for Kubernetes clusters?

**Answer:**

A private registry is the central distribution point for all container images. It must be treated as critical security infrastructure.

**Authentication:**

1. **imagePullSecrets** — Kubernetes Secret of type `kubernetes.io/dockerconfigjson` referenced in pod specs or ServiceAccount.

```bash
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=serviceaccount \
  --docker-password=$(vault kv get -field=token secret/registry)
```

2. **ECR/GCR/ACR with Workload Identity** — Prefer cloud provider registries that integrate with IRSA/Workload Identity, eliminating the need for imagePullSecrets entirely.

3. **Short-lived registry tokens** — ECR tokens expire after 12 hours. Use a `CronJob` or controller to refresh imagePullSecrets, or use the `ecr-credential-helper`.

**Registry security hardening:**

1. **Immutable tags** — Registry configured to reject tag overwrites. Only new tags can be pushed.
2. **Access control** — RBAC in Harbor / IAM policies in ECR — limit who can push, who can pull.
3. **Vulnerability scanning** — Automated scanning on push; policy to block deployment of images with critical CVEs.
4. **Content trust** — Enable Docker Content Trust (DCT) or Cosign for registry-level signature verification.
5. **Registry webhooks** — Trigger scanning and notification pipelines on push events.
6. **Audit logging** — Log every pull event with the identity of the puller (Kubernetes node, user).
7. **Network isolation** — Registry accessible only from CI/CD runners and cluster nodes. Not from developer laptops directly.
8. **Pull-through cache** — Cache public registry images (Docker Hub, GCR) through your private registry to control what external images enter your environment.

**Harbor features for security:**

Harbor is the CNCF-graduated registry platform with built-in security: CVE scanning (Trivy/Clair), signature verification (Cosign/Notary), replication, garbage collection, and project-level access control.

---

### Q65. What is the Kubernetes Image Policy Webhook, and how does it differ from OPA/Kyverno for image enforcement?

**Answer:**

The **ImagePolicyWebhook** is a built-in Kubernetes admission plugin that delegates image admission decisions to an external HTTP service. It's simpler and more lightweight than a full admission webhook framework.

**How it works:**

1. Enable in API server: `--admission-plugins=...,ImagePolicyWebhook`
2. Configure `--admission-control-config-file` pointing to `AdmissionConfiguration` file.
3. The webhook receives an `ImageReview` object for each image.
4. Returns allow/deny.

```yaml
apiVersion: apiserver.k8s.io/v1alpha1
kind: AdmissionConfiguration
plugins:
  - name: ImagePolicyWebhook
    configuration:
      imagePolicy:
        kubeConfigFile: /etc/kubernetes/imagepolicy-kubeconfig.yaml
        allowTTL: 50
        denyTTL: 50
        retryBackoff: 500
        defaultAllow: false  # Fail closed — deny if webhook unreachable
```

**Comparison:**

| Feature | ImagePolicyWebhook | OPA/Gatekeeper | Kyverno |
|---------|-------------------|----------------|---------|
| Native K8s | Yes (built-in plugin) | No (CRD-based) | No (CRD-based) |
| Policy language | External service (any) | Rego | YAML |
| Image signing | Depends on webhook impl. | Possible | Built-in Cosign |
| Mutation | No | No | Yes |
| Policy visibility | Opaque (external) | CRD-based | CRD-based |
| Complexity | Medium | High | Medium |

**In practice:** Most production clusters use Kyverno or OPA/Gatekeeper rather than ImagePolicyWebhook because:
- Policies are managed as Kubernetes resources (auditable, GitOps-friendly).
- Richer policy language.
- Built-in image signature verification (Kyverno).
- Kyverno's `verifyImages` handles the full signing + scanning attestation workflow.

---

### Q66. How does Chainguard and distroless contribute to Kubernetes supply chain security?

**Answer:**

**Chainguard** builds production-ready container images (Chainguard Images) that are:
- **Distroless** — No shell, no package manager, no debugging utilities.
- **Minimal** — Only the runtime and direct dependencies.
- **Daily rebuilt** — Rebuilt every day from source, patching CVEs immediately.
- **Signed** — Every image signed with Cosign/Sigstore.
- **SBOM attached** — Full CycloneDX SBOM as OCI attestation.
- **Zero CVEs** — The stated goal (maintained via continuous rebuilds).

**How this addresses supply chain threats:**

1. **Eliminates base image CVE debt** — Most CVE counts in images come from the OS layer (Debian, Ubuntu packages). Chainguard Images have zero or near-zero OS CVEs.

2. **No shell = no easy lateral movement** — An attacker who gains RCE in your app can't easily pivot to shell commands.

3. **Verified provenance** — Cosign signatures + SLSA provenance attestations mean you can verify the image was built from the specific source commit, on the specific CI system.

4. **Wolfi OS** — Chainguard builds on Wolfi, their own security-focused Linux distribution with fast CVE patching.

**Practical adoption:**

```dockerfile
# Replace debian-based Node
FROM node:20-alpine  # Has historical CVEs

# With Chainguard
FROM cgr.dev/chainguard/node:latest
```

**Tradeoffs:**
- Less flexibility — if your app requires a system library not in the Chainguard image, you may need to build a custom image.
- `latest` tag is updated daily — pin by digest for stability.
- Debugging requires ephemeral containers or a separate debug image.

---

## 7. Runtime Security & Threat Detection

---

### Q67. What is Falco, and how do you write effective Falco rules for Kubernetes?

**Answer:**

**Falco** (CNCF graduated) is a runtime security tool that detects anomalous behavior in containers and Kubernetes by observing kernel syscalls via eBPF (or kernel module) and matching against a rule set.

**Architecture:**
- Falco agent runs as a DaemonSet on each node.
- eBPF probe hooks into kernel syscall exit points.
- Events are matched against rules in real-time.
- Alerts sent to stdout, syslog, HTTP webhook, gRPC, Slack, PagerDuty.

**Rule anatomy:**

```yaml
- rule: Shell in Container
  desc: >
    A shell was spawned inside a container. This is suspicious in production.
  condition: >
    spawned_process and
    container and
    not container.image.repository in (allowed_build_images) and
    shell_procs
  output: >
    Shell spawned in container
    (user=%user.name user_loginuid=%user.loginuid
     container=%container.name image=%container.image.repository
     shell=%proc.name parent=%proc.pname cmdline=%proc.cmdline
     pid=%proc.pid)
  priority: WARNING
  tags: [container, shell, mitre_execution]
```

**Important macros:**
```yaml
- macro: spawned_process
  condition: (evt.type = execve and evt.dir=<)

- macro: container
  condition: (container.id != host)

- macro: shell_procs
  condition: proc.name in (bash, sh, zsh, ksh, fish, dash)
```

**Effective rules for Kubernetes:**

```yaml
# Detect kubectl exec
- rule: Terminal Shell in Container
  condition: >
    spawned_process and container and
    proc.name = bash and proc.pname in (runc, containerd-shim)
  priority: NOTICE

# Detect privilege escalation attempt
- rule: Setuid or Setgid
  condition: >
    container and
    (evt.type=setuid or evt.type=setgid) and
    (user.uid != 0 and evt.arg.uid = 0)
  priority: WARNING

# Detect write to sensitive paths
- rule: Write to /etc in Container
  condition: >
    open_write and container and
    fd.name startswith /etc
  priority: ERROR

# Detect outbound connection to unusual port
- rule: Unexpected Outbound Connection
  condition: >
    outbound and container and
    not fd.sport in (80, 443, 8080, 8443)
  priority: NOTICE
```

**False positive management:**  
Maintain a list of allowlisted images/containers. Use Falco's `exceptions` mechanism (1.0+) to handle legitimate cases without modifying core rules.

---

### Q68. How does eBPF-based runtime security differ from audit-log-based detection?

**Answer:**

**Audit log-based detection (kube-apiserver):**
- Captures API server activity — what Kubernetes resources were created/modified/deleted.
- High-level: "A Deployment was created", "A Secret was accessed".
- Does NOT capture: what happened inside running containers, syscalls, file I/O, network connections.
- Latency: minutes (audit logs shipped to SIEM, rules evaluated).
- Use for: RBAC auditing, policy violations, control-plane events.

**eBPF-based runtime detection (Falco, Cilium, Tetragon):**
- Captures kernel-level events — syscalls, process creation, file operations, network connections.
- Low-level: "Process X made syscall Y with args Z inside container C".
- Does NOT capture: Kubernetes API events, control plane changes.
- Latency: milliseconds to seconds (real-time).
- Use for: Container escape attempts, malware execution, data exfiltration, lateral movement.

**Tetragon (Cilium):**
A step beyond Falco — Tetragon uses eBPF to enforce security policies in the kernel (not just detect) and can kill processes that violate policies.

```yaml
# Tetragon TracingPolicy - detect and block ptrace
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
spec:
  kprobes:
    - call: "sys_ptrace"
      syscall: true
      args:
        - index: 0
          type: "int"
      selectors:
        - matchActions:
            - action: Sigkill  # Kill the process immediately
```

**Complementary, not competing:**

| Dimension | Audit Logs | eBPF Runtime |
|-----------|------------|-------------|
| Scope | Kubernetes API | OS/kernel |
| Speed | Slow (minutes) | Fast (seconds) |
| Evasion resistance | Can be bypassed by direct etcd | Kernel-level (hard to evade) |
| Data volume | Low to medium | Very high |
| False positives | Low | Higher (requires tuning) |

**Production stack:** Use BOTH — ship audit logs to SIEM for compliance and long-term analysis; run Falco/Tetragon on nodes for real-time detection and response.

---

### Q69. What are the MITRE ATT&CK techniques most relevant to Kubernetes runtime detection, and how do you detect them?

**Answer:**

**T1610 — Deploy Container:**  
*Attack:* Deploy a malicious container (DaemonSet for node compromise).  
*Detection:* Alert on new DaemonSet creation in production namespaces; alert on containers using host mounts.

**T1613 — Container and Resource Discovery:**  
*Attack:* `kubectl get pods --all-namespaces` from a compromised pod using its SA token.  
*Detection:* Audit log alert on `list` operations on pods/secrets from service accounts that shouldn't be listing cluster-wide.

**T1552.007 — Container API:**  
*Attack:* Read secrets via the Kubernetes API from within a compromised container.  
*Detection:* Falco rule detecting `curl` or HTTP calls to `kubernetes.default.svc` from containers; audit log on secret reads from unexpected SA.

**T1611 — Escape to Host:**  
*Attack:* Container breakout via kernel exploit, privileged pod, or hostPath.  
*Detection:* 
- Falco: `mount` syscall in a container; access to `/proc/1/` from a container; `nsenter` execution.
- Admission control: Block privileged pods before they run.

**T1543.002 — System Services (persistence):**  
*Attack:* Create a CronJob or modify an existing Job for persistence.  
*Detection:* Alert on CronJob creation/modification in production; alert on abnormal CronJob schedules.

**T1496 — Resource Hijacking (cryptomining):**  
*Detection:*
- CPU spike alerts (Prometheus).
- Falco: `xmrig`, `minerd` process execution.
- Network: Outbound connections to mining pool ports.
- Kubernetes Events: Pods evicted for CPU limit violations.

**T1048 — Exfiltration Over Alternative Protocol:**  
*Attack:* DNS tunneling to exfiltrate data.  
*Detection:* Cilium Hubble monitoring for high-frequency DNS queries, unusual subdomain lengths, non-standard DNS queries.

---

### Q70. How do you implement incident response for a suspected Kubernetes cluster compromise?

**Answer:**

A structured IR playbook for Kubernetes cluster compromise:

**Phase 1: Contain (first 15 minutes)**

```bash
# 1. Identify the blast radius
kubectl get events --all-namespaces --sort-by='.metadata.creationTimestamp' | tail -50

# 2. Cordon compromised node (prevent new scheduling, allow existing pods)
kubectl cordon <node-name>

# 3. Network isolate suspicious pods
kubectl label pod <pod-name> network-policy=quarantine
# Apply NetworkPolicy that drops all traffic from/to quarantine label

# 4. Revoke compromised ServiceAccount tokens
kubectl delete secret <sa-token-secret>
# For projected tokens: delete and recreate the ServiceAccount

# 5. Snapshot node for forensics (before draining)
# Take EBS snapshot / GCP disk snapshot
```

**Phase 2: Identify (15 min – 2 hours)**

```bash
# What resources were created/modified?
# Query audit logs for the time window
kubectl get events -n <suspicious-namespace>

# What images are running?
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.name}: {range .spec.containers[*]}{.image}{"\n"}{end}{end}'

# What connections is the pod making?
kubectl exec <pod> -- ss -tupn
kubectl exec <pod> -- cat /proc/net/tcp

# Check for suspicious processes
kubectl exec <pod> -- ps aux
```

**Phase 3: Eradicate**

```bash
# Delete malicious resources
kubectl delete deployment <malicious-deployment>
kubectl delete daemonset <malicious-daemonset>
kubectl delete clusterrolebinding <attacker-binding>

# Rotate compromised credentials
# - SA tokens
# - etcd certificates if control plane was accessed
# - Cloud provider IAM credentials

# Force drain the compromised node
kubectl drain <node-name> --force --ignore-daemonsets --delete-emptydir-data

# Terminate and replace the node
```

**Phase 4: Recover**

- Verify admission policies are enforced.
- Re-validate RBAC — remove any bindings the attacker created.
- Rotate Secrets that may have been accessed.
- Review and close the initial access vector.

**Phase 5: Lessons Learned**

- Timeline reconstruction from audit logs + Falco alerts.
- Gap analysis: What detection should have fired?
- Policy improvements to prevent recurrence.

---

### Q71. What is Tetragon, and how does it provide enforcement beyond Falco's detection?

**Answer:**

**Tetragon** (by Isovalent/Cilium) is a Kubernetes-native security observability and enforcement tool using eBPF. Unlike Falco which **detects and alerts**, Tetragon can **enforce** — killing processes or blocking syscalls in real-time at the kernel level.

**Key capabilities:**

**1. Process-level visibility:**
Every process execution, file access, and network connection with full Kubernetes context (pod, namespace, labels, SA) and Linux context (UID, GID, capabilities, cgroup).

**2. Kernel-level enforcement (not just alerting):**

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-shell-execution
spec:
  kprobes:
    - call: "sys_execve"
      syscall: true
      args:
        - index: 0
          type: "string"
      selectors:
        - matchBinaries:
            - operator: In
              values:
                - "/bin/bash"
                - "/bin/sh"
                - "/usr/bin/python3"
          matchActions:
            - action: Sigkill    # Immediately kill the process
            - action: Override   # Override return value (block the syscall)
```

**3. Network enforcement:**
Block specific network connections at the kernel level, complementing but not replacing NetworkPolicy.

**4. File access enforcement:**
Block writes to sensitive paths (e.g., prevent any process in a container from writing to `/etc/passwd`).

**Falco vs Tetragon:**

| Feature | Falco | Tetragon |
|---------|-------|---------|
| Detection | Yes | Yes |
| Enforcement/Kill | No | Yes |
| eBPF-based | Yes (or module) | Yes (eBPF only) |
| Policy language | YAML rules | TracingPolicy CRD |
| Kubernetes integration | Yes | Native (Cilium) |
| Performance overhead | Low | Very low |

**Operational consideration:** Enforcement is powerful but dangerous in production — a misconfigured `Sigkill` policy can kill critical processes. Use `audit` mode first, then promote to enforcement after thorough testing.

---

### Q72. How do you use Prometheus and Grafana to monitor Kubernetes security signals?

**Answer:**

Prometheus + Grafana provide metrics-based security monitoring — complementing log-based (Falco) and audit-based (SIEM) detection with trend analysis and alerting on quantitative security signals.

**Key security metrics to monitor:**

**1. Authentication and Authorization:**
```promql
# Failed authentication attempts
rate(apiserver_authentication_attempts_total{result="error"}[5m])

# Authorization rejections (potential enumeration/abuse)
rate(apiserver_authorization_decisions_total{decision="forbid"}[5m])
```

**2. Admission Control:**
```promql
# Admission webhook rejections
rate(apiserver_admission_webhook_rejection_count[5m]) by (name, operation)

# PSA violations
rate(pod_security_evaluations_total{decision="deny"}[5m]) by (namespace)
```

**3. Runtime security (Falco metrics):**
```promql
# Falco alerts by priority
rate(falco_events_total{priority=~"WARNING|ERROR|CRITICAL"}[5m]) by (rule)
```

**4. Network anomalies (Cilium Hubble):**
```promql
# Dropped packets (NetworkPolicy violations)
rate(hubble_drop_total[5m]) by (reason, direction)

# Connections to blocked destinations
rate(hubble_flows_processed_total{verdict="DROPPED"}[5m])
```

**5. Resource exhaustion (DoS signals):**
```promql
# Pods pending for too long (resource starvation attack)
kube_pod_status_phase{phase="Pending"} > 0

# Namespace quota utilization near limits
kube_resourcequota{type="used"} / kube_resourcequota{type="hard"} > 0.9
```

**Grafana dashboard structure for security:**
- **Overview:** Critical alerts count, recent anomalies.
- **Authentication:** API server auth failures, OIDC token issues.
- **Policy violations:** Admission rejections, PSA violations, OPA/Kyverno denials.
- **Runtime:** Falco event rates, process anomalies per namespace.
- **Network:** Policy drops, unusual external connections, DNS anomaly.

**AlertManager rules:**
```yaml
groups:
  - name: kubernetes-security
    rules:
      - alert: HighAuthenticationFailureRate
        expr: rate(apiserver_authentication_attempts_total{result="error"}[5m]) > 0.1
        for: 5m
        severity: warning
```

---

### Q73. What is Pod Security Admission audit mode, and how do you use it for migration from PSP?

**Answer:**

PSA **audit mode** allows you to deploy a stricter policy alongside your current enforcement, logging violations without blocking workloads. This is the primary tool for PSP → PSA migration.

**Migration strategy:**

**Step 1: Assess current PSP landscape:**
```bash
kubectl get psp
kubectl get rolebindings,clusterrolebindings -A -o json | \
  jq '.items[] | select(.roleRef.kind=="ClusterRole" and (.roleRef.name | startswith("psp:")))' 
```

**Step 2: Enable PSA in warn+audit mode first:**
```yaml
# Label ALL namespaces with warn mode
kubectl label --all namespaces \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/warn-version=latest \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/audit-version=latest
```

**Step 3: Collect audit events:**
```bash
# Find PSA violations in audit logs
kubectl get events -A | grep "PodSecurity"
# Or in API server audit log:
grep '"objectRef":{"resource":"pods"' audit.log | jq 'select(.annotations."pod-security.kubernetes.io/audit-violations")'
```

**Step 4: Fix workloads that violate the target policy:**
- Update security contexts in Deployments/StatefulSets.
- For system workloads that need elevated privileges, apply `privileged` label to system namespaces.
- For workloads that legitimately need `baseline`, apply `baseline` enforce.

**Step 5: Promote to enforce once violations are zero:**
```bash
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=v1.29
```

**Step 6: Disable PSP admission plugin** (must be done atomically — test in staging).

**PSA exemptions (for system components):**
```yaml
# API server flag
--admission-control-config-file=admission-config.yaml

# admission-config.yaml
plugins:
  - name: PodSecurity
    configuration:
      exemptions:
        usernames: ["system:serviceaccount:kube-system:*"]
        namespaces: ["kube-system", "monitoring"]
```

---

### Q74. What is the Kubernetes Security Benchmark (CIS), and how do you implement it?

**Answer:**

The **CIS Kubernetes Benchmark** (Center for Internet Security) is a consensus-based security configuration guide for Kubernetes. It covers the API server, etcd, kubelet, scheduler, controller manager, and worker node OS configuration.

**Key CIS benchmark categories:**

**1. Control Plane Configuration:**
- API server flags: `--anonymous-auth=false`, `--audit-log-path`, `--tls-min-version=VersionTLS12`
- etcd: mTLS, encryption at rest
- RBAC: Node authorization, deny anonymous access

**2. Node Configuration:**
- Kubelet: `--anonymous-auth=false`, `--authorization-mode=Webhook`, `--protect-kernel-defaults=true`
- OS: `/etc/kubernetes/pki` permissions, kubelet.conf permissions

**3. Policies:**
- NetworkPolicies present in all namespaces
- PSA or equivalent policy in effect
- LimitRanges in all application namespaces

**Automated assessment with `kube-bench`:**

```bash
# Run against current node
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# View results
kubectl logs job/kube-bench

# Run against specific benchmark
kube-bench --benchmark cis-1.8 --targets node
```

**Sample kube-bench output:**
```
[PASS] 1.2.1 Ensure that the --anonymous-auth argument is set to false (Automated)
[FAIL] 1.2.22 Ensure that the --audit-log-path argument is set (Automated)
[WARN] 1.2.33 Ensure that the API Server only makes use of Strong Cryptographic Ciphers (Manual)
```

**Continuous compliance:** Run kube-bench as a scheduled Job and ship results to a dashboard. Alert on new FAILs. For managed Kubernetes (EKS, GKE, AKS), some checks don't apply (control plane managed by provider) — use the EKS/GKE-specific benchmarks.

---

### Q75. How do you detect and prevent cryptojacking in a multi-tenant Kubernetes cluster?

**Answer:**

Cryptojacking (unauthorized cryptomining) is the #1 attack against misconfigured Kubernetes clusters.

**Prevention (primary defense):**

1. **Close the initial access vector:**
   - No exposed dashboards or API servers without authentication.
   - All API server access via OIDC/RBAC, not static tokens.
   - Namespace-based admission policies (PSA `restricted`).

2. **Restrict compute resources:**
```yaml
# ResourceQuota prevents a namespace from consuming entire cluster
spec:
  hard:
    limits.cpu: "20"
    limits.memory: 40Gi
```

3. **CPU limits on all pods:** Mining requires sustained CPU. CPU limits prevent any single container from consuming the node's CPU.

4. **Egress firewall:** Block mining pool ports (3333, 4444, 5555, 7777).

5. **Admission policies:** Block `privileged: true`, `hostPID`, host mounts.

**Detection:**

1. **Prometheus anomaly detection:**
```promql
# Alert if any container consumes >80% CPU limit for >10m
(container_cpu_usage_seconds_total / container_spec_cpu_quota * 100) > 80
```

2. **Falco mining detection:**
```yaml
- rule: Crypto Miner Process
  condition: >
    spawned_process and container and
    proc.name in (xmrig, minerd, cpuminer, ethminer, cgminer, monero-wallet)
  priority: CRITICAL
```

3. **DNS monitoring:**
Cryptominers often use stratum protocol which uses specific DNS patterns. Monitor for queries to known mining pool FQDNs.

4. **Process lineage:**
A web server (`nginx`) that spawns `bash` that spawns `xmrig` is immediately suspicious. Tetragon tracks full process lineage.

5. **GPU monitoring:** If your cluster has GPU nodes, monitor for unauthorized GPU usage (crypto miners increasingly use GPUs).

---

## 8. Cloud Provider IAM & Integration

---

### Q76. How does EKS Pod Identity compare to IRSA (IAM Roles for Service Accounts)?

**Answer:**

**IRSA (IAM Roles for Service Accounts) — Original mechanism:**
- Works by creating an OIDC provider in AWS IAM pointing to the EKS cluster's OIDC endpoint.
- A mutating webhook (`amazon-eks-pod-identity-webhook`) injects `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` env vars.
- Pod uses `AssumeRoleWithWebIdentity` to exchange the Kubernetes SA token for AWS credentials.
- IAM Trust Policy references the OIDC provider and specific SA.
- Limitation: OIDC provider URL is cluster-specific — same role can't easily be reused across clusters.

**EKS Pod Identity — Newer mechanism (GA 2023):**
- Simpler setup — no OIDC provider configuration required in IAM.
- `PodIdentityAssociation` resource maps K8s SA to IAM Role.
- AWS EKS Pod Identity Agent (DaemonSet) handles token exchange.
- Same IAM role can be associated with multiple clusters without modifying the trust policy.
- Uses a dedicated `eks-auth` endpoint, not `AssumeRoleWithWebIdentity`.

```yaml
# EKS Pod Identity Association (via eksctl or CloudFormation)
apiVersion: eks.amazonaws.com/v1alpha1
kind: PodIdentityAssociation
spec:
  namespace: production
  serviceAccountName: api-server
  roleArn: arn:aws:iam::123456789012:role/api-role
```

**Comparison:**

| Feature | IRSA | Pod Identity |
|---------|------|--------------|
| OIDC setup | Per cluster | None |
| Role reuse across clusters | Requires IAM update | Easy |
| Token exchange | STS AssumeRoleWithWebIdentity | EKS Auth API |
| Credential delivery | Env vars + token file | Env vars + token file |
| Session tags | Limited | Full support |
| IPv6 support | Yes | Yes |

**Recommendation:** Use Pod Identity for new EKS deployments (simpler operations). IRSA remains fully supported for existing deployments.

---

### Q77. How do you secure the EKS cluster endpoint? What are the security tradeoffs of public vs private endpoints?

**Answer:**

The **EKS API server endpoint** controls how `kubectl` and workers communicate with the control plane.

**Endpoint modes:**

**Public only (default):**
- API server accessible from the internet.
- Protected by IAM (must have valid `aws eks get-token` credentials).
- Can restrict by CIDR (`publicAccessCidrs`).
- Workers communicate via internet (or via NAT gateway if in private subnets).

**Public + Private:**
- API server accessible from both VPC (private) and internet (public).
- Workers in private subnets can communicate directly without internet.
- Public access still available for developer `kubectl` access.
- Most common production configuration.

**Private only:**
- API server only accessible from within the VPC.
- Developers need VPN, AWS Direct Connect, or bastion host.
- Maximum security — no public exposure.
- Required for: PCI DSS, some HIPAA implementations.

**Configuration:**
```bash
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config \
    endpointPublicAccess=true,\
    publicAccessCidrs="10.0.0.0/8,203.0.113.0/24",\
    endpointPrivateAccess=true
```

**Security tradeoffs:**

| Mode | Attack Surface | Developer UX | Egress Cost |
|------|---------------|-------------|-------------|
| Public only | Internet-exposed | Easy | Low |
| Public + Private | Reduced (CIDR restricted) | Good | Medium |
| Private only | Minimal | Requires VPN | Low |

**Additional hardening:**
- Enable audit logging to CloudWatch.
- Use `aws-auth` ConfigMap carefully — or migrate to EKS Access Entries (newer IAM-native approach).
- Enable envelope encryption for Kubernetes secrets (CMK in KMS).
- Use Calico or Cilium for NetworkPolicy (VPC CNI doesn't support NetworkPolicy natively).

---

### Q78. What is the `aws-auth` ConfigMap in EKS, and what are its security risks?

**Answer:**

The `aws-auth` ConfigMap in `kube-system` maps AWS IAM entities (users, roles) to Kubernetes RBAC groups and usernames. It's how EKS knows that an IAM user/role should have Kubernetes permissions.

**Structure:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/NodeGroupRole
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
    - rolearn: arn:aws:iam::123456789012:role/AdminRole
      username: admin
      groups:
        - system:masters  # Full cluster access!
  mapUsers: |
    - userarn: arn:aws:iam::123456789012:user/alice
      username: alice
      groups:
        - developers
```

**Security risks:**

1. **`system:masters` grants** — Common to see IAM roles mapped to `system:masters`. This is appropriate for break-glass roles but often over-applied to developer roles.

2. **ConfigMap can be modified by anyone with `update` on ConfigMaps in `kube-system`** — If an attacker (or a poorly permissioned CI/CD system) can modify this ConfigMap, they can grant any IAM principal cluster-admin.

3. **No approval workflow** — Changes to `aws-auth` take effect immediately; no review process.

4. **Drift from desired state** — Without GitOps management, `aws-auth` accumulates entries over time.

5. **Format errors** — Invalid YAML in `aws-auth` can break all authentication to the cluster.

**Mitigations:**

- **Manage via Terraform/Helm** — Treat `aws-auth` as IaC with PRs and approval.
- **Restrict ConfigMap write** in `kube-system` via RBAC.
- **Migrate to EKS Access Entries** (newer IAM-native approach that doesn't rely on this ConfigMap).
- Alert on any modification to `aws-auth` via CloudTrail + EventBridge.
- Never map to `system:masters` for routine access.

---

### Q79. How do you implement least-privilege node IAM roles for EKS worker nodes?

**Answer:**

EKS worker nodes run on EC2 instances that need an IAM role to function. This role is the **ambient credential** for all pods on the node (unless using IRSA/Pod Identity).

**Minimum required managed policies:**
```
AmazonEKSWorkerNodePolicy       -- Register node, describe cluster
AmazonEC2ContainerRegistryReadOnly  -- Pull images from ECR
AmazonEKS_CNI_Policy            -- Configure VPC networking (if using VPC CNI)
```

**Remove or never add:**
```
AdministratorAccess             -- NEVER
AmazonS3FullAccess              -- Over-permissive; use IRSA for S3 access
AmazonDynamoDBFullAccess        -- Same — use IRSA per workload
```

**Block IMDS from pods:**

Even with IRSA, the node's EC2 metadata (IMDS) is accessible from pods unless blocked. Pods can retrieve the node's instance role credentials if IMDS hop limit is > 1.

```bash
# Enforce IMDSv2 and hop limit of 1
aws ec2 modify-instance-metadata-options \
  --instance-id $(curl -s http://169.254.169.254/latest/meta-data/instance-id) \
  --http-tokens required \
  --http-put-response-hop-limit 1
```

In EKS managed node group launch templates:
```json
{
  "MetadataOptions": {
    "HttpTokens": "required",
    "HttpPutResponseHopLimit": 1,
    "HttpEndpoint": "enabled"
  }
}
```

**Additional node role restrictions:**
- Add a permissions boundary on the node role limiting what it can do even if elevated.
- Use Service Control Policies (SCPs) at the AWS Organization level to prevent key actions from EC2 instances.
- CloudTrail alert on any API calls made by the node role that aren't expected (CreateRole, PutRolePolicy, etc.).

---

### Q80. How does GKE Autopilot enhance security compared to Standard GKE?

**Answer:**

**GKE Autopilot** is a fully managed Kubernetes mode where Google manages the nodes, node pools, and infrastructure. From a security perspective, it enforces a hardened baseline by default.

**Security enhancements in Autopilot:**

1. **Pod-level resource isolation:** Every pod gets dedicated vCPU and memory — no noisy neighbor at the resource level. Burstable workloads are not allowed.

2. **Enforced security context:**
   - `privileged: true` is blocked.
   - `hostNetwork`, `hostPID`, `hostIPC` are blocked.
   - `hostPath` mounts are blocked.
   - `runAsRoot` is blocked for most workloads.
   - Pods must specify resource requests.

3. **Workload Identity required:** Node-level service account permissions are minimal. All GCP API access must use Workload Identity.

4. **No SSH to nodes:** No direct node access — use `kubectl exec` or ephemeral containers.

5. **Hardened OS:** Nodes use Container-Optimized OS with automatic security patches applied by Google.

6. **Network policies enforced:** Calico-based NetworkPolicy is available.

7. **Sandbox (gVisor):** GKE Autopilot supports RuntimeClass with gVisor for untrusted workload isolation.

**Standard vs Autopilot security:**

| Feature | Standard | Autopilot |
|---------|----------|-----------|
| Node access | Yes (SSH, OS tuning) | No |
| Privileged pods | Configurable | Blocked |
| Node OS patching | Manual/NodePool | Automatic |
| Custom kernel settings | Yes | No |
| DaemonSets | Yes | Restricted |
| Security baseline | Operator responsibility | Google enforced |

**When NOT to use Autopilot:** Workloads requiring DaemonSets for node-level monitoring, privileged system components, or custom kernel parameters.

---

### Q81. What is Azure Defender for Containers, and how does it integrate with AKS?

**Answer:**

**Microsoft Defender for Containers** (formerly Azure Defender for Kubernetes/Container Registries) is a cloud-native security product that provides runtime threat detection, vulnerability assessment, and compliance monitoring for AKS clusters.

**Integration architecture:**
- A Defender DaemonSet is deployed to each node.
- Streams audit logs and runtime events to Microsoft's security backend.
- Integrates with Microsoft Sentinel for SIEM correlation.

**Capabilities:**

1. **Kubernetes audit log analysis:**
   - Detects suspicious API server activity (exposed dashboards, crypto mining DaemonSets, RBAC abuse).
   - Alert categories: "Suspicious process execution in a container", "Detected suspicious use of a Kubernetes service account".

2. **Container image vulnerability assessment:**
   - Scans images in Azure Container Registry (ACR).
   - Surfaces CVEs in the Security Center dashboard.

3. **Kubernetes security posture management:**
   - CIS Kubernetes Benchmark compliance scoring.
   - Recommendations for RBAC, network policies, pod security.

4. **Threat intelligence:**
   - Correlates container activity with Microsoft's global threat intelligence.
   - Detects known mining pool connections, C2 communication.

5. **Runtime anomaly detection:**
   - "New container in a privileged position" — alerts when a privileged container is detected.
   - "Container running with high privileges" — PSP violation equivalent.

**Integration with Microsoft Sentinel:**
Defender for Containers streams alerts to Sentinel, enabling:
- Cross-resource correlation (container + identity + network alerts).
- SOAR playbooks for automated response.
- Long-term threat hunting.

---

### Q82. How do you implement cross-cloud Kubernetes federation securely?

**Answer:**

Cross-cloud Kubernetes federation connects clusters across AWS, GCP, Azure (or on-premises) into a unified management plane. Security is complex because trust boundaries span multiple cloud providers.

**Federation approaches:**

**1. GitOps-based (Flux/ArgoCD) — Most common:**
- Each cluster is independently managed.
- A central Git repository is the source of truth.
- ArgoCD instances in each cluster sync from Git.
- No direct cluster-to-cluster communication — Git is the intermediary.
- Security: Git repo access control is the critical security perimeter. Use per-cluster deploy keys.

**2. Cluster API (CAPI):**
- A management cluster provisions and manages workload clusters.
- CAPI uses cloud provider credentials to create/modify clusters.
- Security: Management cluster's ServiceAccount needs cross-cloud IAM — use Workload Identity with limited IAM permissions.

**3. Admiral / Istio Multi-cluster:**
- Service mesh spans multiple clusters.
- mTLS between clusters using a shared trust domain.
- Service discovery across clusters.
- Security: Root CA must be shared (or federated) across clusters. Protect the root CA carefully.

**4. KubeFed (legacy, largely deprecated).**

**Cross-cloud authentication:**
- Use OIDC federation between cloud providers (AWS IAM trusting GCP OIDC issuer).
- SPIFFE/SPIRE as a universal identity layer across clouds.
- No shared passwords or static credentials between cloud environments.

**Network security:**
- WireGuard or IPsec tunnels between cluster nodes across clouds.
- Service mesh mTLS for service-level encryption.
- Centralized audit log aggregation to a neutral SIEM.

---

### Q83. What is Cloud Security Posture Management (CSPM) for Kubernetes, and what tools implement it?

**Answer:**

**CSPM for Kubernetes** (also called Kubernetes Security Posture Management, KSPM) continuously assesses cluster configuration against security best practices and compliance frameworks, providing visibility into misconfigurations before they're exploited.

**What it assesses:**
- CIS Kubernetes Benchmark compliance.
- RBAC misconfigurations (over-permissive roles, unused roles).
- Network policy gaps.
- Pod security context violations.
- Container image vulnerabilities.
- Secrets management issues (secrets in env vars, unencrypted etcd).
- Cloud-level misconfigurations (exposed endpoints, weak IAM).

**Tools:**

**Open source:**
- **kube-bench** — CIS benchmark automated checks.
- **kube-hunter** — Active penetration testing (runs from inside or outside).
- **Polaris** (Fairwinds) — Kubernetes best practices validation with policy scores.
- **Starboard/Trivy Operator** — Vulnerability + config audit reports as CRDs.

**Commercial/Cloud-native:**
- **Prisma Cloud (Palo Alto)** — Full-stack CSPM across cloud + Kubernetes.
- **Wiz** — Agentless CSPM with deep K8s context + cloud graph.
- **Lacework** — Behavioral + config-based posture.
- **Sysdig Secure** — Runtime + posture + compliance.
- **AWS Security Hub** (for EKS) — Integrates with Kubernetes Audit logs.
- **Microsoft Defender CSPM** — Azure-native, extends to multi-cloud.

**Polaris example:**
```yaml
# Polaris audit in CI
polaris audit --config polaris-config.yaml \
  --audit-path k8s/manifests/ \
  --format score

# Returns a score (0-100) and detailed findings
```

**Integration pattern:**
1. **CI gate:** Polaris/Conftest fail builds with critical misconfigs.
2. **Admission:** OPA/Gatekeeper prevents known-bad configurations.
3. **Continuous:** CSPM tool scans live cluster and reports drift.
4. **SIEM:** CSPM findings shipped to SIEM for correlation.

---

## 9. Compliance, Auditing & Governance

---

### Q84. What compliance frameworks are most relevant to Kubernetes deployments, and how do you map controls?

**Answer:**

**Key frameworks:**

**PCI DSS (Payment Card Industry):**
- **Requirement 1:** Network segmentation — NetworkPolicy default-deny, separate namespaces for cardholder data.
- **Requirement 2:** Secure configurations — CIS benchmark compliance.
- **Requirement 6:** Vulnerability management — Image scanning, patching.
- **Requirement 7:** Access control — RBAC least privilege.
- **Requirement 10:** Audit logging — API server audit logs, all admin access.
- **Requirement 11:** Penetration testing — Regular kube-hunter, red team exercises.

**HIPAA:**
- **Administrative safeguards:** RBAC policies, access reviews.
- **Technical safeguards:** Encryption at rest (etcd), in transit (mTLS/TLS).
- **Audit controls:** Audit logs for all access to PHI containers.
- **Access control:** ServiceAccount isolation, no shared credentials.

**SOC 2 (Trust Services Criteria):**
- **CC6 (Logical Access):** RBAC, MFA via OIDC, JIT access.
- **CC7 (System Operations):** Monitoring (Falco, Prometheus), incident response playbooks.
- **CC8 (Change Management):** GitOps, audit trails for all deployments.
- **CC9 (Risk Mitigation):** Vulnerability management, security testing.

**NIST SP 800-190 (Application Container Security):**
- Specifically covers container security best practices.
- Maps to: Image hardening, registry security, container runtime configuration, host OS hardening, container orchestration configuration.

**Control mapping approach:**

1. Build a control matrix: compliance requirement → Kubernetes control → tooling.
2. Automate evidence collection: kube-bench outputs, OPA policy reports, audit log exports.
3. Use OpenSCAP or Compliance Operator (OpenShift) for automated SCAP assessments.
4. Continuous compliance: run assessments on schedule, alert on drift.

---

### Q85. How do you implement and maintain a Kubernetes change management process?

**Answer:**

Change management ensures that every modification to the cluster is reviewed, approved, audited, and reversible.

**GitOps as the foundation:**
All cluster changes flow through Git — PRs for review, merges trigger deployment. The Git history is the audit trail.

**Change classification:**

| Type | Examples | Process |
|------|----------|---------|
| Routine | Deploy new app version, scale replicas | Automated pipeline with automated tests |
| Standard | New namespace, RBAC role addition | PR with peer review |
| Significant | Kubernetes version upgrade, new CNI | Change Advisory Board review, staged rollout |
| Emergency | Security patch for active incident | Expedited process with post-change review |

**Technical controls:**

1. **Branch protection rules** — No direct pushes to main; require PR review.
2. **Policy-as-code checks in CI** — Conftest/OPA runs on every PR.
3. **Staging environment** — Changes deployed to staging before production.
4. **ArgoCD sync waves** — Order deployments for controlled rollouts.
5. **Helm revision history** — `helm history <release>` for rollback.
6. **Kubernetes rollout history:**
```bash
kubectl rollout history deployment/api
kubectl rollout undo deployment/api --to-revision=3
```

7. **Audit log correlation** — Every `kubectl apply` in production tied to a ticket/PR.

**Change freeze periods:**
- Block non-emergency production changes via OPA policies during business-critical periods (Black Friday, financial quarter close).
- Automate freeze enforcement: reject deployments from CI during freeze windows.

---

### Q86. How do you handle vulnerability management for running Kubernetes workloads?

**Answer:**

Vulnerability management is a continuous process — new CVEs are disclosed daily, and running containers can become vulnerable without any change on your part.

**Vulnerability management lifecycle:**

**1. Discover:**
- Trivy Operator continuously scans running pods and generates `VulnerabilityReport` CRDs.
- `kubectl get vulnerabilityreports -A`

**2. Assess severity and exploitability:**
- CVSS score alone is insufficient — consider exploitability, reachability, and compensating controls.
- Use VEX (Vulnerability Exploitability eXchange) documents to mark non-exploitable CVEs.
- EPSS (Exploit Prediction Scoring System) — probability of exploitation in the wild.

**3. Prioritize:**
```
Critical + exploitable + in critical workload → Remediate within 24h
High + no available fix → Add compensating control + track
Medium with fix available → Remediate in next sprint
Low → Accept with documentation
```

**4. Remediate:**
- **Rebuild image** — Most CVEs are in OS packages; rebuilding with updated base image is the primary fix.
- **Update dependency** — Application-layer CVE in a library.
- **Patch in-place** — Rarely appropriate for containers (breaks immutability); use only for critical zero-days while rebuilding.

**5. Verify and close:**
- Re-scan after remediation.
- Confirm the vulnerable version is no longer present.

**SLA tracking (example):**

| Severity | SLA |
|----------|-----|
| Critical (CVSS 9+) | 24 hours |
| High (CVSS 7-9) | 7 days |
| Medium (CVSS 4-7) | 30 days |
| Low (CVSS < 4) | 90 days or accept |

**Tooling:** Trivy Operator, Snyk, JFrog Xray, Anchore, Amazon Inspector (ECR), GCP Container Analysis.

---

### Q87. What is the role of Open Policy Agent in Kubernetes governance?

**Answer:**

**Open Policy Agent (OPA)** is a general-purpose policy engine. In Kubernetes, it's deployed as **OPA/Gatekeeper** — a validating/mutating admission webhook that evaluates Rego policies against incoming resources.

**Governance use cases:**

**1. Compliance enforcement:**
- All pods must have resource limits (CIS 5.1.6).
- Images must come from approved registries.
- Services of type LoadBalancer are restricted to specific namespaces.

**2. Organizational standards:**
- All resources must have specific labels (owner, cost-center, environment).
- Namespace names must follow naming convention.

**3. Security policies:**
- No privileged containers.
- No containers running as root.
- All ConfigMaps in kube-system require admin approval (OPA cannot enforce this natively, but can require specific annotations).

**4. Cost control:**
- CPU limits cannot exceed X per container.
- Certain node sizes restricted to specific teams.

**OPA policy pipeline:**

```
Git PR → Conftest (static analysis) → CI merge → Gatekeeper (runtime enforcement) → Audit
```

**Gatekeeper constraint template:**
```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        properties:
          labels:
            type: array
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Missing required labels: %v", [missing])
        }
```

**Audit mode:**
Gatekeeper continuously audits existing resources (not just new ones) and reports violations via `ConstraintViolation` status and `AuditEvent` metrics.

---

### Q88. How do you manage Kubernetes secrets rotation at scale with zero downtime?

**Answer:**

At scale (hundreds of services, thousands of pods), manual secret rotation is impractical. A systematic approach is required.

**Architecture for zero-downtime rotation at scale:**

**1. Vault Dynamic Secrets:**
The most scalable approach — Vault generates unique, short-lived credentials for each pod lease. There's no "rotation" because credentials expire and are renewed automatically.

```
Pod → Vault Agent Sidecar → Database (unique dynamic credential)
```

When the lease expires (e.g., 1 hour), Vault Agent renews with a new credential. The database receives a credential renewal, not a new connection.

**2. Credential Versioning:**
Support two active versions of a credential simultaneously during rotation window:

```
Phase 1: Both old and new password valid in DB
Phase 2: Update Kubernetes Secret with new password → pods reload
Phase 3: Remove old password from DB
Phase 4: Verify no traffic using old password (audit log)
```

**3. Application-level reload:**
Applications must support credential reload without restart:

```go
// Watch for file changes in mounted secret volume
credWatcher.OnChange(func() {
    newCred := readFile("/run/secrets/db-password")
    connectionPool.UpdateCredential(newCred)
})
```

**4. Canary rotation:**
Rotate secrets for 5% of pods (via pod labels + separate ServiceAccount) first. Monitor error rates. Roll out to 100% if clean.

**5. Secrets rotation tracker:**
Track which secrets have been rotated and when. Alert on secrets older than policy threshold.

```bash
# Custom Prometheus metric for secret age
kubectl get secrets -A -o json | jq '.items[] | 
  {name: .metadata.name, namespace: .metadata.namespace, 
   age: (now - (.metadata.creationTimestamp | fromdateiso8601))}'
```

---

### Q89. Describe how to implement a Kubernetes security review process for new workloads.

**Answer:**

A workload security review should be systematic, automated where possible, and proportionate to the risk profile of the workload.

**Risk tiers:**

| Tier | Definition | Review Level |
|------|------------|--------------|
| Tier 1 | Public-facing, processes PII/payment | Full security review |
| Tier 2 | Internal service, no sensitive data | Automated checks + lightweight review |
| Tier 3 | Dev/test, no production data | Automated checks only |

**Review process:**

**1. Pre-deployment (automated in CI):**
- Image scanning (Trivy) — fail on Critical CVEs.
- Static analysis of Kubernetes manifests (Polaris, Conftest).
- Secret scanning in manifests (detect-secrets, truffleHog).
- SBOM generation and attestation.
- Checklist: `readOnlyRootFilesystem`, `runAsNonRoot`, `resources.limits`, `automountServiceAccountToken: false`.

**2. Design review (for Tier 1/2):**
- Data flow diagram — what sensitive data does the workload process?
- External dependencies — what external APIs does it call?
- RBAC requirements — what Kubernetes/cloud permissions are needed?
- Secret requirements — what secrets does it need and how are they accessed?
- Network requirements — what ingress and egress does it need?

**3. Threat modeling:**
- STRIDE analysis of the workload.
- Identify top-3 attack scenarios.
- Mitigation for each.

**4. Acceptance testing:**
- NetworkPolicy tested (can it reach what it should? Can't reach what it shouldn't?).
- Security context verified with kube-score.
- Falco rules covering key behaviors.

**5. Ongoing:**
- Quarterly vulnerability review.
- Annual architecture review.
- Alert on anomalous behavior from the workload.

---

### Q90. What is the Kubernetes Policy Report standard, and how does it centralize compliance information?

**Answer:**

The **Policy Report** custom resource (maintained by the Kubernetes Policy Working Group) provides a standardized format for security and compliance tools to report their findings as Kubernetes resources — making them queryable via the API, displayable in dashboards, and usable in automation.

**Resource types:**
- `PolicyReport` — Namespace-scoped reports.
- `ClusterPolicyReport` — Cluster-scoped reports.

**Standard format:**
```yaml
apiVersion: wgpolicyk8s.io/v1alpha2
kind: PolicyReport
metadata:
  name: kyverno-report
  namespace: production
summary:
  pass: 45
  fail: 3
  warn: 2
  error: 0
  skip: 1
results:
  - policy: require-resource-limits
    rule: check-cpu-limits
    resources:
      - apiVersion: v1
        kind: Pod
        name: api-server-6d5f9b
        namespace: production
    message: "Container api does not have CPU limits"
    result: fail
    severity: medium
    timestamp:
      nanos: 0
      seconds: 1680000000
```

**Tools that generate Policy Reports:**
- **Kyverno** — Per-policy, per-namespace reports.
- **Trivy Operator** — Vulnerability and config audit reports.
- **Polaris** — Best practice reports.
- **kube-bench** — CIS benchmark reports.

**Aggregation and dashboards:**
- **Policy Reporter UI** — Open-source dashboard that aggregates all PolicyReport resources across the cluster.
- **Grafana integration** — Policy Reporter exports Prometheus metrics for dashboard visualization.

**Automation use cases:**
- Block deployments to namespaces with active policy failures.
- Auto-create Jira tickets for policy violations.
- SLA tracking on unresolved violations.

---

### Q91. How do you handle Kubernetes cluster upgrades from a security perspective?

**Answer:**

Kubernetes cluster upgrades are high-risk operations that must be carefully planned to maintain security posture throughout.

**Security risks during upgrades:**

1. **API deprecations break security policies** — OPA/Gatekeeper and Kyverno policies may use deprecated API versions that are removed in the new version.
2. **PSP removal** (1.25) — Upgrading from a cluster relying on PSP without PSA/OPA in place breaks all pod security.
3. **Admission webhook compatibility** — Webhooks must be compatible with the new API server version.
4. **Certificate expiry** — Certificate rotation may be required as part of the upgrade.
5. **CNI/CSI plugin compatibility** — Security-relevant plugins (Cilium, Falco, Gatekeeper) must be compatible with the new version.

**Pre-upgrade security checklist:**

```bash
# Check for deprecated API usage
pluto detect-api-resources --target-versions k8s=v1.28.0

# Check admission webhook compatibility
kubectl get validatingwebhookconfigurations -o json | \
  jq '.items[] | {name: .metadata.name, admissionReviewVersions: .webhooks[].admissionReviewVersions}'

# Verify all CRD versions
kubectl get crds -o json | jq '.items[] | .spec.versions'

# Run kube-bench against new version requirements
kube-bench --benchmark cis-1.8
```

**Upgrade order:**
1. Update CRDs and admission webhooks to support new API versions.
2. Upgrade control plane (API server first, then etcd, then scheduler, controller manager).
3. Upgrade node groups (rolling, draining each node).
4. Verify security policies still enforced post-upgrade.
5. Upgrade security tooling (Falco, Gatekeeper, Cilium) to compatible versions.

**Post-upgrade security validation:**
- All PSA/OPA policies apply correctly.
- Falco generating alerts (test with a known trigger).
- mTLS still functioning in service mesh.
- Certificate expiry dates checked.
- kube-bench re-run to verify benchmark compliance.

---

## 10. Zero Trust & Advanced Architecture

---

### Q92. How do you implement Zero Trust Architecture for a Kubernetes cluster?

**Answer:**

**Zero Trust** is a security model built on the principle "never trust, always verify" — no implicit trust based on network location, and continuous verification of every request.

**Zero Trust pillars applied to Kubernetes:**

**1. Identity as the perimeter:**
- Every workload has a cryptographic identity (SPIFFE SVID, mTLS certificate).
- No implicit trust between pods even in the same namespace.
- Human access via OIDC with MFA — no long-lived kubeconfigs.
- JIT access for administrative operations.

**2. Micro-segmentation:**
- Default-deny NetworkPolicy in every namespace.
- Service mesh (Istio/Linkerd) for L7 identity-based authorization.
- No open network paths — every connection explicitly permitted.

**3. Least privilege everywhere:**
- Pods with minimal RBAC.
- Minimal Linux capabilities.
- Read-only filesystems.
- Minimal cloud IAM (Workload Identity).

**4. Continuous verification:**
- Short-lived tokens (mTLS certificates with 1h expiry, SA tokens with 1h expiry).
- Authorization re-evaluated per request (not at connection time only).
- Behavioral monitoring (Falco, Tetragon) detects anomalies even from authorized entities.

**5. Assume breach:**
- Comprehensive audit logging.
- IR playbooks ready.
- Regular chaos/security exercises.
- Blast radius limitation (ResourceQuota, NetworkPolicy, namespace isolation).

**Implementation roadmap:**

```
Phase 1: AuthN/AuthZ hardening (OIDC, RBAC)
Phase 2: Network micro-segmentation (NetworkPolicy default-deny)
Phase 3: Service mesh mTLS (Istio/Linkerd)
Phase 4: Workload identity (SPIFFE, cloud Workload Identity)
Phase 5: Runtime enforcement (Tetragon, OPA)
Phase 6: Continuous monitoring and posture management
```

---

### Q93. What is the Kubernetes Security Model for multi-cluster environments? How do you federate security policies?

**Answer:**

Multi-cluster environments multiply the attack surface — each cluster is a potential entry point, and lateral movement between clusters is a critical concern.

**Security challenges:**
- Policy drift between clusters.
- Inconsistent RBAC across clusters.
- Trust boundaries between clusters.
- Centralized visibility vs. distributed deployment.

**Federated policy management:**

**1. Policy-as-code in a central Git repository:**
- A `policies/` directory in a monorepo or dedicated policy repo.
- All clusters pull policies via ArgoCD/Flux with cluster-specific overlays (Kustomize).
- PRs to policy repo require security team approval.

**2. Hub-and-spoke with Policy Controller:**

```
Central Git → ArgoCD Hub Cluster
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
    Cluster A  Cluster B  Cluster C
   (Gatekeeper) (Gatekeeper) (Gatekeeper)
```

**3. ClusterPolicy distribution with Kyverno:**
Kyverno policies can be distributed to all clusters and reports aggregated centrally.

**4. Centralized audit log aggregation:**
All clusters ship audit logs to a central SIEM (Splunk/Elastic/Sentinel). Cross-cluster correlation detects multi-cluster attacks.

**5. Cross-cluster network trust:**
- Don't automatically trust traffic from other clusters.
- Use service mesh federation with explicit trust bundles.
- Istio multi-cluster: shared root CA with peer trust established.

**6. Credential isolation:**
- Each cluster has its own CA, etcd PKI, and SA signing key.
- No shared credentials between clusters.
- Cloud-provider cross-cluster access via Workload Identity Federation (not static credentials).

---

### Q94. Explain supply-chain-level attestation and the SLSA framework in the context of Kubernetes deployments.

**Answer:**

**SLSA (Supply-chain Levels for Software Artifacts)** is a framework of security controls to prevent supply chain attacks, from source code to deployed artifact.

**SLSA levels (v1.0):**

| Level | Build | Provenance | Description |
|-------|-------|------------|-------------|
| L1 | Documented | Available | Build scripted; provenance generated |
| L2 | Automated, authenticated | Authenticated | Build on hosted CI; provenance authenticated |
| L3 | Hardened CI | Verified | Build on hardened platform; provenance non-forgeable |

**Provenance in practice:**

Provenance is a signed document stating:
- What was built (image digest).
- How it was built (which CI workflow, which commit).
- When it was built.
- Who triggered the build.

**Generating SLSA provenance in GitHub Actions:**

```yaml
- name: Generate SLSA provenance
  uses: slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@v1.9.0
  with:
    image: registry.example.com/api
    digest: ${{ steps.build.outputs.digest }}
```

**Verifying at admission time with Kyverno:**

```yaml
rules:
  - name: verify-slsa-provenance
    verifyImages:
      - imageReferences: ["registry.example.com/*"]
        attestations:
          - predicateType: https://slsa.dev/provenance/v1
            attestors:
              - entries:
                  - keyless:
                      rekor: https://rekor.sigstore.dev
                      issuer: https://token.actions.githubusercontent.com
                      subject: "https://github.com/myorg/myrepo/.github/workflows/release.yml@refs/heads/main"
            conditions:
              - all:
                  - key: "{{ buildType }}"
                    operator: Equals
                    value: "https://actions.github.com/builds"
```

**What this prevents:**
- An attacker who compromises a developer's machine cannot push an image — the CI system's identity is required for attestation.
- An attacker who compromises a registry cannot substitute a malicious image — the digest is cryptographically attested.
- Build-time attacks (SolarWinds-style) are detectable via the provenance trail.

---

### Q95. How does Kubernetes handle mutual TLS (mTLS) at the pod level without a service mesh?

**Answer:**

Native Kubernetes provides no built-in pod-to-pod mTLS — this must be implemented at the application layer or via a service mesh. However, there are lightweight options short of a full service mesh.

**Option 1: Application-implemented mTLS:**

Each service manages its own TLS certificates via cert-manager or the Kubernetes CSR API:

```yaml
# cert-manager Certificate for a pod
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: api-server-cert
spec:
  secretName: api-server-tls
  dnsNames:
    - api.production.svc.cluster.local
  issuerRef:
    name: cluster-ca
    kind: ClusterIssuer
```

Services load these certs and implement mTLS in their TLS configuration. Requires application code changes for every service.

**Option 2: SPIRE for SPIFFE SVIDs:**

SPIRE injects SVIDs into pods without sidecars via the SPIFFE Workload API (Unix socket). Applications use these SVIDs for mTLS without managing certificate infrastructure.

**Option 3: Linkerd (minimal sidecar overhead):**

Linkerd's `linkerd2-proxy` is a lightweight Rust sidecar (~10MB, <5ms latency) that handles mTLS transparently. It's significantly less complex than Istio.

**Option 4: Cilium with WireGuard (node-level, not pod-level):**

Encrypts all inter-node traffic. Pods don't have individual identities, but all traffic is encrypted in transit. Simpler than a service mesh.

**mTLS without service mesh: the engineering cost:**

Implementing mTLS at the application layer requires:
- Certificate lifecycle management (cert-manager).
- TLS configuration in every service.
- Certificate rotation handling.
- Trust store management.

For most organizations, a service mesh is more cost-effective than per-service implementation.

---

### Q96. What is eBPF-based network security policy enforcement, and how does it compare to iptables-based enforcement?

**Answer:**

**iptables-based enforcement (legacy CNIs, kube-proxy):**

- Rules stored in kernel netfilter/iptables tables.
- O(n) lookup — each packet traverses all rules until a match.
- Rules are applied at the interface level, after routing.
- Complex rule ordering — mistakes are hard to debug.
- No session awareness for UDP/ICMP.
- Rule updates require kernel calls and can have brief windows during which rules are inconsistent.

**eBPF-based enforcement (Cilium, Calico eBPF mode):**

- Programs compiled to eBPF bytecode and loaded into the kernel.
- O(1) lookup via hash maps for established connections.
- Applied at the TC (traffic control) hook — earlier in the network path.
- Atomic updates — new programs replace old ones atomically.
- Rich context available — pod identity, labels, service mesh identity.
- Can also hook at XDP (eXpress Data Path) for line-rate packet processing.

**Performance comparison (Cilium benchmarks):**

| Metric | iptables | eBPF |
|--------|----------|------|
| Rule lookup | O(n) | O(1) |
| Throughput | ~10Gbps | ~25Gbps |
| Latency (p99) | ~200µs | ~50µs |
| Scalability | Degrades at >10K rules | Linear |

**Security advantages of eBPF:**

1. **Identity-based, not IP-based** — eBPF programs access pod labels directly from the kernel; policy is stable across pod IP changes.

2. **Harder to bypass** — iptables can be manipulated from privileged containers that run `iptables -F`. eBPF programs in the kernel are more isolated from user-space manipulation.

3. **Cryptographic enforcement** — WireGuard integration possible at the eBPF level.

4. **Full packet inspection** — eBPF can inspect payload bytes for L7 policy without a separate user-space proxy for simple patterns.

5. **Audit trail** — Every packet decision can be logged via eBPF ring buffers with Kubernetes context.

---

### Q97. How do you implement a defense-in-depth strategy for a regulated Kubernetes environment (e.g., PCI DSS Level 1)?

**Answer:**

PCI DSS Level 1 is the most stringent compliance tier (>6 million card transactions/year). Kubernetes deployment in this context requires layered controls across all security domains.

**Defense-in-depth stack:**

**Layer 1: Cloud/Infrastructure**
- Private VPC with no public subnets for cluster nodes.
- Private EKS/GKE/AKS endpoint only.
- Network ACLs + Security Groups limiting all unnecessary traffic.
- AWS WAF / GCP Cloud Armor in front of all ingress.
- CloudTrail / Cloud Audit Logs enabled with integrity validation.

**Layer 2: Cluster Configuration**
- Kubernetes version within N-2 (actively supported).
- CIS Benchmark compliance automated with kube-bench.
- Etcd encrypted at rest with KMS CMK.
- API server audit logging to immutable storage.
- PSA `restricted` on all cardholder data namespaces.

**Layer 3: Identity and Access**
- OIDC with MFA for all human access.
- No shared credentials; no static tokens.
- JIT access for production administration.
- Workload Identity for all pod-to-cloud API access.
- Quarterly RBAC access review.

**Layer 4: Network**
- Default-deny NetworkPolicy in all namespaces.
- Service mesh mTLS for all pod-to-pod communication.
- Egress filtering to allowlist only required destinations.
- DNS monitoring for tunneling detection.

**Layer 5: Workload**
- PSA `restricted` enforcement.
- OPA/Gatekeeper additional policies.
- All images from private registry, signed and scanned.
- No privileged containers, no host mounts.
- Secrets via Vault CSI driver (not in etcd).

**Layer 6: Runtime**
- Falco on every node.
- Tetragon enforcement for critical rules.
- SIEM integration with 90-day log retention.
- SOC monitoring 24/7.

**Layer 7: Process**
- Penetration testing quarterly + after major changes.
- Vulnerability remediation SLAs (Critical: 24h).
- Annual security review.
- IR plan tested quarterly.

---

### Q98. What advanced Kubernetes attack techniques should senior security engineers be aware of?

**Answer:**

Understanding attacker techniques at a deep level is required to build effective defenses.

**1. etcd direct access:**
An attacker with network access to port 2379 and a valid client certificate (perhaps stolen from the API server's kubeconfig) can read all secrets and write arbitrary resources. Detection: Any connection to etcd port from a non-API-server source.

**2. Kubelet API exploitation:**
The kubelet API (`https://<node>:10250`) allows pod exec, log access, and running commands on the node. Pre-1.15, anonymous access was a known attack vector. Modern attack: steal a kubelet client certificate to access another node's kubelet.

**3. Admission webhook MitM:**
An attacker who can create a `MutatingWebhookConfiguration` pointing to their endpoint can inspect and modify all resources as they're created. Detection: Alert on new MutatingWebhookConfigurations.

**4. Node role abuse:**
A compromised node can use its legitimate kubelet identity (system:node:<name>) to read all secrets assigned to pods on that node. Lateral movement: if a high-privilege pod is rescheduled to the compromised node.

**5. Container namespace escape via `runc` CVEs:**
CVE-2019-5736 (runc), CVE-2020-15257 (containerd), CVE-2022-0185 (Linux kernel). These allow container processes to escape to the host. Detection: Falco rules for unusual mount/ptrace syscalls.

**6. Sidecar injection for credential theft:**
An attacker who controls a MutatingWebhookConfiguration can inject a sidecar into every pod. The sidecar reads environment variables (secrets), exfiltrates them, and is invisible to application teams.

**7. GitOps repo compromise:**
If the ArgoCD Git repository is compromised, arbitrary manifests can be deployed to the cluster. Defense: Sign commits, require PR review, use separate repos for policy vs. application.

**8. DNS rebinding:**
Exploit the cluster DNS to rebind internal service names to external IPs. Mitigation: Cilium DNS policy, CoreDNS minimal resolvers.

**9. RBAC token-from-filesystem:**
Kubernetes automounts SA tokens at a well-known path. Any file read vulnerability in an application (LFI, SSRF) can exfiltrate the token.

**10. etcd backup exfiltration:**
Steal an etcd backup file from storage (S3, GCS). If not encrypted, contains all Secrets in plaintext (or base64). Defense: Encrypt backups, strict IAM on backup storage.

---

### Q99. How do you build a security-first Kubernetes platform team? What are the key organizational and technical practices?

**Answer:**

A security-first platform team embeds security into every aspect of platform development rather than treating it as a gate or afterthought.

**Organizational practices:**

**1. Security champions within application teams:**
Not every developer needs to be a security expert, but each team should have a security champion who is responsible for security review, trained in threat modeling, and a liaison to the platform security team.

**2. Shift-left with guardrails, not gates:**
Security checks should run in the developer's inner loop (IDE plugins, pre-commit hooks, PR checks) rather than only at deployment time. The goal is to fix issues before they become expensive.

**3. Paved road model:**
Provide secure defaults that are easier to use than insecure alternatives. A Helm chart starter template with correct security contexts is more effective than a policy that rejects incorrect ones — the developer's default is already correct.

**4. SLA-driven remediation:**
Treat security findings as engineering work items. Critical CVEs have the same SLA as P0 incidents. Medium findings are in the backlog. Avoid "security debt" by tracking and aging findings.

**Technical practices:**

**1. Security golden path:**
- Curated Helm chart templates with correct security contexts.
- Dockerfile linter (hadolint) in all repos.
- Cosign signing in all CI pipelines (not optional).
- Pre-configured Falco rules reviewed by security team.

**2. Internal security scorecard:**
Each namespace/service scored on: image freshness, CVE count, policy compliance, secrets hygiene, RBAC footprint. Publicly visible to all teams. Gamification drives improvement.

**3. Chaos engineering for security:**
Regular (quarterly) exercises where the security team attempts to break their own controls. Findings drive improvements. This is distinct from penetration testing — it tests detection and response, not just prevention.

**4. Documentation and runbooks:**
Every security control has a runbook: what it does, why it's there, how to request an exception, how to debug it. Without this, developers fight the controls rather than work with them.

---

### Q100. What does the future of Kubernetes security look like? What emerging technologies and practices will dominate?

**Answer:**

Kubernetes security continues to evolve rapidly. Here are the most significant trends defining the next 3-5 years:

**1. eBPF as the security substrate:**
eBPF is becoming the universal observability and enforcement layer. Cilium's Tetragon, Falco's eBPF driver, and Isovalent's security suite all point to eBPF replacing both iptables (for networking) and ptrace/audit (for syscall monitoring). Expect eBPF to become a commodity expectation in all CNI plugins.

**2. Confidential Computing:**
Hardware-enforced isolation where even the cloud provider cannot access workload memory. Intel TDX, AMD SEV-SNP, and ARM CCA enable **Confidential Containers** — pods that run in hardware-isolated trusted execution environments (TEEs). This is critical for healthcare, financial services, and AI model protection.

**3. Ambient Mesh (Istio 1.22+):**
Sidecar-free service mesh architecture where mTLS and L7 policy are enforced by per-node ztunnel proxies and waypoint proxies. This eliminates the sidecar overhead while preserving security guarantees. Expect this to become the default service mesh architecture.

**4. AI-powered security:**
- **Anomaly detection:** ML models trained on cluster behavioral baselines detect subtle deviations that rule-based systems miss.
- **Auto-remediation:** AI-driven SOAR playbooks automatically respond to incidents (quarantine pods, rotate credentials).
- **Policy generation:** AI assistance in writing Rego/Kyverno policies from natural language descriptions.
- **Threat:** AI also enables more sophisticated attacks — auto-adapting malware that evades Falco rule patterns.

**5. Software supply chain formalization:**
SLSA Level 3+, Sigstore (now a Linux Foundation project), and SBOM standards (SPDX/CycloneDX) will become baseline requirements. Expect regulatory mandates (EU CRA, US EO 14028) to drive adoption in enterprise and government.

**6. Zero Trust everywhere by default:**
SPIFFE/SPIRE for universal workload identity, federated identity across clouds, short-lived credentials for everything. The concept of a "trusted internal network" will be fully abandoned.

**7. Policy-as-code maturity:**
OPA and Kyverno will continue to mature. Expect standardized policy libraries (like Terraform Sentinel modules but for Kubernetes), better policy testing frameworks, and policy compliance as a first-class CI/CD signal.

**8. GitOps security hardening:**
ArgoCD and Flux will integrate supply chain security more deeply — signature verification on Helm charts and manifests, SBOM attestation at deploy time, cryptographic proof-of-deployment.

**9. Kubernetes-native security APIs:**
The Kubernetes API itself will absorb more security primitives currently handled by third-party tools. Expect standardization of admission policy APIs, runtime security policy APIs, and audit policy APIs into core Kubernetes.

---

## Appendix: Quick Reference

### Critical Security Flags

```bash
# API Server
--anonymous-auth=false
--audit-log-path=/var/log/kube/audit.log
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--authorization-mode=Node,RBAC
--enable-admission-plugins=NodeRestriction,PodSecurity
--encryption-provider-config=/etc/kubernetes/encryption.yaml
--tls-min-version=VersionTLS12
--insecure-port=0

# Kubelet
--anonymous-auth=false
--authorization-mode=Webhook
--read-only-port=0
--protect-kernel-defaults=true
--rotate-certificates=true

# etcd
--client-cert-auth=true
--peer-client-cert-auth=true
```

### Key Tools Reference

| Domain | Tool | Purpose |
|--------|------|---------|
| Scanning | Trivy, Grype | Image & config vulnerability scanning |
| Policy | OPA/Gatekeeper, Kyverno | Admission control |
| Runtime | Falco, Tetragon | Runtime threat detection |
| RBAC | rbac-tool, kubectl-who-can | RBAC auditing |
| Benchmark | kube-bench | CIS compliance |
| Signing | Cosign, Sigstore | Image signing |
| Secrets | Vault, ESO, CSI Driver | Secrets management |
| Posture | Polaris, Starboard | Security posture |
| Network | Cilium, Calico | NetworkPolicy + eBPF |
| Service Mesh | Istio, Linkerd | mTLS + L7 policy |

---

*Document version: 1.0 | Kubernetes: 1.29+ | Last reviewed: 2025*

100 questions delivered across 10 domains. Here's what's covered:

| # | Domain | Topics |
|---|--------|--------|
| Q1–Q15 | **Core Security Primitives** | API server pipeline, etcd hardening, admission controllers, PSA, node authorizer, audit logs, SA tokens, threat matrix, certificates, CRI, dashboard, multi-tenancy, aggregation layer, `system:masters` |
| Q16–Q25 | **RBAC & Identity** | RBAC design, OIDC SSO, privilege escalation paths, Workload Identity (EKS/GKE/AKS), SA token auto-mount, JIT access, impersonation, RBAC auditing, manifest injection, TokenRequest API |
| Q26–Q35 | **Network Security** | NetworkPolicy deep-dive, Cilium/eBPF, egress filtering, service mesh, SSRF metadata protection, Ingress hardening, CoreDNS attacks, hostNetwork risks, Service topology, WireGuard |
| Q36–Q50 | **Pod & Container Security** | Hardened security context, Linux capabilities, seccomp, AppArmor, image immutability, privileged/hostPID risks, distroless, OPA vs Kyverno, init containers, ResourceQuota, container escapes, root risks, secrets injection |
| Q51–Q58 | **Secrets Management** | CSI Driver, secret rotation, ESO vs CSI, GitOps secrets, SPIFFE/SPIRE, secrets auditing, env var risks, Helm secrets |
| Q59–Q66 | **Supply Chain** | Supply chain threat model, Sigstore/Cosign/Fulcio/Rekor, SBOM, image scanning enforcement, digest pinning, registry hardening, ImagePolicyWebhook, Chainguard |
| Q67–Q75 | **Runtime Security** | Falco rules, eBPF vs audit-log detection, MITRE ATT&CK techniques, IR procedure, Tetragon enforcement, Prometheus security metrics, PSA migration, CIS Benchmark, cryptojacking |
| Q76–Q83 | **Cloud IAM** | EKS Pod Identity vs IRSA, EKS endpoint security, `aws-auth` risks, node IAM least privilege, GKE Autopilot, Azure Defender, cross-cloud federation, CSPM |
| Q84–Q91 | **Compliance & Governance** | PCI DSS/HIPAA/SOC2 mapping, change management, vulnerability management, OPA governance, secret rotation at scale, workload security review, Policy Reports, cluster upgrades |
| Q92–Q100 | **Zero Trust & Advanced** | ZTA implementation, multi-cluster federation, SLSA attestations, mTLS without mesh, eBPF vs iptables deep-dive, PCI DSS L1 defense-in-depth, advanced attack techniques, platform team practices, future of K8s security |