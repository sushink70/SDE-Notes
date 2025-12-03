# Commit Message Templates for Software Engineers

I'll provide you with a comprehensive set of commit message templates that follow best practices for both open-source cloud-native projects and enterprise environments. These templates follow the **Conventional Commits** specification, which is widely adopted in the cloud-native ecosystem.

---

## **Core Template Structure**

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type**: Category of change
- **scope**: Area of codebase affected (optional but recommended)
- **subject**: Brief summary (50 chars max, imperative mood)
- **body**: Detailed explanation (wrap at 72 chars)
- **footer**: Breaking changes, issue references, metadata

---

## **1. Standard Commit Types**

### **Feature Addition**
```
feat(api): add rate limiting middleware

Implement token bucket algorithm for API rate limiting.
- Add RateLimiter struct with configurable capacity
- Integrate with HTTP middleware chain
- Add Redis backend for distributed rate limiting

Closes #234
```

### **Bug Fix**
```
fix(parser): prevent panic on malformed UTF-8 input

Handle invalid UTF-8 sequences gracefully by replacing
with Unicode replacement character (U+FFFD) instead of
panicking. Adds comprehensive test coverage for edge cases.

Fixes #456
```

### **Performance Optimization**
```
perf(cache): optimize memory usage in LRU cache

Replace HashMap+LinkedList with custom intrusive doubly-linked
list to reduce allocations by ~40%. Benchmark results show:
- 35% reduction in memory footprint
- 15% faster eviction operations

Ref: #789
```

### **Refactoring**
```
refactor(auth): extract JWT validation into separate module

Decompose monolithic auth handler into focused components:
- token.rs: JWT parsing and validation
- claims.rs: Claims structure and validation
- middleware.rs: HTTP middleware integration

No functional changes. Improves testability and maintainability.
```

### **Documentation**
```
docs(readme): add architecture decision records section

Document ADR process and link to architectural decisions.
Includes template for future ADRs and rationale for
choosing microservices architecture.
```

### **Tests**
```
test(storage): add property-based tests for key-value store

Implement QuickCheck/proptest generators for:
- Concurrent read/write operations
- Edge cases in key serialization
- Consistency under network partitions

Achieves 95% branch coverage.
```

### **CI/CD Changes**
```
ci: migrate to GitHub Actions from Travis CI

Replace .travis.yml with GitHub Actions workflows:
- test.yml: Run unit/integration tests on PR
- release.yml: Automated semantic versioning and tagging
- security.yml: Daily dependency vulnerability scans

Reduces CI time from 12min to 8min.
```

### **Build System**
```
build(deps): upgrade Kubernetes client-go to v0.28.0

Update client-go and related dependencies to support
Kubernetes 1.28 features. Required for new CRD validation.

BREAKING CHANGE: Deprecated watch API removed. Clients must
migrate to informer pattern. See migration guide: docs/v0.28-migration.md
```

### **Chores/Maintenance**
```
chore(deps): bump tokio from 1.32.0 to 1.33.0

Routine dependency update for security patch.
No API changes. Includes fix for rare race condition
in async runtime shutdown.
```

---

## **2. Open Source Specific Templates**

### **First-Time Contribution**
```
feat(metrics): add Prometheus exporter for custom metrics

Implements Prometheus /metrics endpoint exposing:
- Request latency histograms
- Active connection gauges
- Error rate counters

This is my first contribution to the project. I've read
the CONTRIBUTING.md and signed the CLA. Happy to address
any feedback!

Closes #123
Co-authored-by: Jane Doe <jane@example.com>
```

### **Breaking Change**
```
feat(api)!: redesign configuration API for better ergonomics

BREAKING CHANGE: Configuration now uses builder pattern
instead of struct initialization. Migration required:

Before:
  Config { host: "0.0.0.0", port: 8080 }

After:
  Config::builder()
    .host("0.0.0.0")
    .port(8080)
    .build()?

See migration guide: docs/migration-v2.md

Closes #567
```

### **Security Fix**
```
fix(auth)!: patch SQL injection vulnerability in login handler

Address CWE-89 by using parameterized queries instead of
string concatenation. All user inputs now properly sanitized.

SECURITY: This fixes a critical vulnerability that could
allow unauthorized database access. Upgrade immediately.

CVE-2024-XXXXX
Reported-by: security@example.com
```

---

## **3. Enterprise/Private Project Templates**

### **Feature Development**
```
feat(billing): implement usage-based pricing calculator

Add service for computing monthly charges based on:
- API request volume (tiered pricing)
- Storage utilization (per-GB pricing)
- Data transfer egress (bandwidth pricing)

Integrates with existing invoice generation pipeline.
Includes audit logging for compliance.

JIRA: PROJ-1234
Reviewers: @finance-team @platform-team
```

### **Hotfix Production Issue**
```
fix(cache): resolve memory leak in Redis connection pool

Emergency fix for production memory leak causing OOM crashes.
Root cause: connections not properly returned to pool on error.

Changes:
- Add explicit Drop implementation for Connection wrapper
- Implement connection health checks with 30s timeout
- Add metrics for pool exhaustion monitoring

INCIDENT: INC-5678
Rollback plan: Revert to v1.2.3 if issues persist
Monitoring: Dashboard at https://grafana.internal/d/redis
```

### **Technical Debt**
```
refactor(legacy): migrate authentication from Session to JWT

Phase 1 of auth modernization roadmap. Replaces server-side
sessions with stateless JWT tokens for better scalability.

Migration strategy:
- Parallel run: Support both auth methods for 2 weeks
- Feature flag: auth.use_jwt (default: false)
- Rollback: Disable flag if error rate > 0.1%

TECH-DEBT: AUTH-2024-Q1
Timeline: Complete by 2024-03-15
Risk: Medium (mitigated by gradual rollout)
```

---

## **4. Pull Request Templates**

### **Standard PR Commit**
```
feat(k8s): add custom resource definition for TrafficPolicy

Implements CRD for fine-grained traffic management:
- Schema validation with OpenAPI v3
- Admission webhook for policy validation
- Controller reconciliation loop

Testing:
- Unit tests: 87% coverage
- Integration tests: E2E with Kind cluster
- Manual testing: Deployed to staging

Documentation:
- API reference: docs/api/traffic-policy.md
- User guide: docs/guides/traffic-management.md
- Examples: examples/traffic-policy/

Closes #456
Resolves PROJ-789
```

### **Draft PR / Work in Progress**
```
wip(observability): initial OpenTelemetry integration [WIP]

Early draft for feedback. Still TODO:
- [ ] Add span context propagation across service boundaries
- [ ] Implement custom sampler for high-traffic endpoints
- [ ] Add trace visualization examples
- [ ] Performance benchmarking

Current state: Basic tracing works, but needs optimization.

Feedback wanted on:
1. Approach to sampling strategy
2. Span attribute naming conventions
3. Integration with existing logging

Draft PR - Do not merge
```

---

## **5. Special Situations**

### **Revert Commit**
```
revert: "feat(cache): implement distributed locking"

This reverts commit a1b2c3d4e5f6.

Reason: Distributed locking causes deadlocks under high
concurrency. Need to redesign with lock timeout and deadlock
detection before re-landing.

Incident: INC-9012
Decision: Emergency rollback approved by @tech-lead
```

### **Merge Commit**
```
Merge pull request #789 from user/feature-branch

feat(monitoring): add distributed tracing support

Approved-by: @reviewer1, @reviewer2
Tested-in: staging environment
Performance-impact: +2ms p99 latency (acceptable)
```

### **Cherry-Pick to Release Branch**
```
fix(db): prevent connection pool exhaustion

(cherry picked from commit a1b2c3d4e5f6)

Backporting critical fix to v1.2.x release branch.
Required for production stability.

Original PR: #456
Release: v1.2.4
```

### **Dependency Update with Changelog**
```
chore(deps): upgrade axum from 0.6.x to 0.7.0

Major version upgrade with breaking changes:

Notable changes:
- extractors now require explicit error handling
- State extraction moved to separate extractor
- New typed routing API

Migration completed:
- Updated all route handlers
- Added error mapping layer
- Refactored state management

See upgrade guide: https://docs.rs/axum/0.7.0/axum/upgrade/index.html

Tested-by: Full integration test suite
```

---

## **6. Commit Message Best Practices**

### **Quality Checklist**
```
✓ Type prefix (feat/fix/docs/etc.)
✓ Scope in parentheses (optional but recommended)
✓ Imperative mood ("add" not "added")
✓ No period at end of subject line
✓ Subject under 50 characters
✓ Body wrapped at 72 characters
✓ Blank line between subject and body
✓ Body explains "what" and "why" (not "how")
✓ Issue/ticket reference in footer
✓ Breaking changes clearly marked
```

### **Common Pitfalls to Avoid**
```
❌ "fixed stuff"
❌ "WIP"
❌ "updated files"
❌ "minor changes"
❌ "PR feedback"

✓ "fix(parser): handle empty input gracefully"
✓ "feat(api): add pagination to list endpoint"
✓ "refactor(auth): extract validation logic"
```

---

## **7. Context-Specific Scopes (Cloud-Native)**

Use these scopes for cloud-native projects:

```
api          - REST/gRPC API changes
auth         - Authentication/authorization
cache        - Caching layer
cli          - Command-line interface
config       - Configuration management
controller   - Kubernetes controller
crd          - Custom Resource Definition
db           - Database layer
deps         - Dependencies
docs         - Documentation
e2e          - End-to-end tests
helm         - Helm charts
infra        - Infrastructure code
k8s          - Kubernetes manifests
logging      - Logging infrastructure
metrics      - Metrics/monitoring
operator     - Kubernetes operator
parser       - Parsing logic
proto        - Protocol buffers
sdk          - SDK/client library
security     - Security-related changes
storage      - Storage layer
webhook      - Admission/mutating webhooks
```

---

## **8. Git Aliases for Faster Commits**

Add to your `~/.gitconfig`:

```ini
[alias]
    # Quick commits with type
    feat = "!f() { git commit -m \"feat: $*\"; }; f"
    fix = "!f() { git commit -m \"fix: $*\"; }; f"
    docs = "!f() { git commit -m \"docs: $*\"; }; f"
    test = "!f() { git commit -m \"test: $*\"; }; f"
    refactor = "!f() { git commit -m \"refactor: $*\"; }; f"
    perf = "!f() { git commit -m \"perf: $*\"; }; f"
    
    # Commit with scope
    fc = "!f() { git commit -m \"feat($1): ${@:2}\"; }; f"
    
    # Amend last commit message
    amend = commit --amend
    
    # Show commit template
    template = "!cat ~/.gitmessage"
```

---

## **Mental Model: The Commit Message Pyramid**

```
         [Subject Line]          ← What changed (50 chars)
              |
         [Body Content]          ← Why changed + context
              |
    [Footer/References]          ← Links, breaking changes
```

**Think like a historian:** Future developers (including yourself) should understand the *reasoning* behind changes without reading the code.

---

These templates will serve you across open-source contributions, enterprise work, and personal projects. Adapt them to your team's conventions, but maintain clarity, consistency, and context. Quality commit messages are a hallmark of elite software engineers.

Would you like me to create additional templates for specific scenarios (rollback procedures, migration commits, experimental features, etc.)?