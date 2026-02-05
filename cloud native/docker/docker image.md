# Docker Image Comprehensive Guide

**Summary**: Docker images are immutable, layered filesystem snapshots that package application code, runtime, libraries, and dependencies into a portable unit for container execution. Understanding image internals—OCI specs, layer composition, registry protocols, content-addressable storage, and security boundaries—is critical for building minimal, reproducible, and secure container workloads. This guide covers image architecture, build systems, layer optimization, signing/scanning, distribution, and runtime security from a first-principles systems perspective, with emphasis on supply-chain integrity, isolation, and production hardening.

---

## 1. Image Fundamentals & OCI Specification

### 1.1 What Is a Docker Image?

A Docker image is:
- **Layered filesystem**: Union filesystem (OverlayFS, AUFS) combining read-only layers + writable container layer
- **Metadata**: JSON manifest describing layers, config, entrypoint, environment, labels
- **Content-addressable**: Each layer identified by SHA256 digest; enables deduplication and integrity
- **Immutable**: Once built, layers are read-only; containers add ephemeral writable layer

**OCI Image Spec** (https://github.com/opencontainers/image-spec):
- **Image Index** (multi-arch): Points to manifests for different platforms
- **Manifest**: Lists layer digests, config digest, media types
- **Config**: JSON with image metadata (env vars, entrypoint, cmd, user, working dir, labels)
- **Layers**: Tar archives (gzip/zstd compressed) representing filesystem diffs

```
┌─────────────────────────────────────────┐
│         OCI Image Layout                │
├─────────────────────────────────────────┤
│  Image Index (manifest list)            │
│    ├─ Manifest (linux/amd64)            │
│    │   ├─ Config (JSON)                 │
│    │   └─ Layers [sha256:abc..., ...]   │
│    └─ Manifest (linux/arm64)            │
├─────────────────────────────────────────┤
│  Blobs (content-addressable storage)    │
│    ├─ sha256:abc... (layer tar.gz)      │
│    ├─ sha256:def... (layer tar.gz)      │
│    └─ sha256:123... (config.json)       │
└─────────────────────────────────────────┘
```

---

## 2. Image Layers & Storage Drivers

### 2.1 Layer Stacking (Union Filesystem)

Layers are stacked bottom-up. Each `RUN`, `COPY`, `ADD` in Dockerfile creates a new layer.

**OverlayFS (default)**:
- **Lower**: Read-only image layers
- **Upper**: Writable container layer
- **Merged**: Union view presented to container
- **Work**: Temporary directory for copy-up operations

```bash
# Inspect image layers
docker image inspect myimage:latest --format '{{json .RootFS.Layers}}' | jq

# Examine storage driver
docker info | grep "Storage Driver"

# Dive into layers (use dive tool)
dive myimage:latest
```

### 2.2 Layer Optimization

**Problem**: Each layer adds size; unnecessary files persist across layers.

**Solutions**:
1. **Combine commands**: Single `RUN` with `&&` to avoid intermediate artifacts
2. **Multi-stage builds**: Build artifacts in one stage, copy binaries to minimal final stage
3. **`.dockerignore`**: Exclude unnecessary files from build context
4. **Layer caching**: Order Dockerfile instructions from least to most frequently changing

```dockerfile
# Bad: Multiple layers with temp files
RUN apt-get update
RUN apt-get install -y curl
RUN curl -o /tmp/file https://example.com/file
RUN rm /tmp/file

# Good: Single layer, cleanup in same instruction
RUN apt-get update && apt-get install -y curl && \
    curl -o /tmp/file https://example.com/file && \
    rm /tmp/file && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
```

---

## 3. Dockerfile Deep Dive

### 3.1 Core Instructions

| Instruction | Purpose | Layer Created |
|-------------|---------|---------------|
| `FROM` | Base image | No (references existing) |
| `RUN` | Execute command | Yes |
| `COPY` | Copy files from build context | Yes |
| `ADD` | Copy + extract tar/fetch URL | Yes (avoid; use COPY) |
| `WORKDIR` | Set working directory | No (metadata) |
| `ENV` | Set environment variable | No (metadata) |
| `EXPOSE` | Document port (not actual publish) | No (metadata) |
| `USER` | Set UID/GID for container | No (metadata) |
| `ENTRYPOINT` | Container executable | No (metadata) |
| `CMD` | Default args for ENTRYPOINT | No (metadata) |
| `LABEL` | Key-value metadata | No (metadata) |
| `ARG` | Build-time variable | No (metadata) |
| `VOLUME` | Mount point declaration | No (metadata) |
| `HEALTHCHECK` | Container health probe | No (metadata) |

### 3.2 Multi-Stage Builds (Critical for Security & Size)

**Pattern**: Build in one stage (with compilers, dev tools), copy artifacts to minimal runtime stage.

```dockerfile
# Stage 1: Build (Go example)
FROM golang:1.21-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o app .

# Stage 2: Runtime (distroless or scratch)
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /build/app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

**Benefits**:
- Final image ~2-5MB (vs 300MB+ with Go builder)
- No compiler, dev tools, source code in runtime image
- Reduced attack surface

---

## 4. Base Image Selection & Security

### 4.1 Base Image Hierarchy

```
Alpine (~5MB) → Minimal, musl libc, apk package manager
Distroless (~20-40MB) → No shell, no package manager, minimal OS
Scratch (0MB) → Empty image; for static binaries only
Debian/Ubuntu Slim (~30-80MB) → glibc, minimal tooling
Full OS (>100MB) → Debian, Ubuntu, RHEL (avoid for production)
```

### 4.2 Security Considerations

**Threat**: Base image vulnerabilities, supply-chain attacks, malicious layers.

**Mitigations**:
1. **Use minimal bases**: Alpine, Distroless, Scratch
2. **Pin digests**: `FROM alpine:3.19@sha256:abc...` (not `:latest`)
3. **Scan images**: Trivy, Grype, Snyk, Clair
4. **Verify provenance**: Check image signatures (cosign, Notary v2)
5. **Run as non-root**: Set `USER` to non-zero UID
6. **Read-only root FS**: `docker run --read-only`
7. **Drop capabilities**: `--cap-drop=ALL --cap-add=NET_BIND_SERVICE`

```bash
# Scan image for CVEs
trivy image --severity HIGH,CRITICAL myimage:latest

# Verify signature (Sigstore cosign)
cosign verify --key cosign.pub myimage:latest

# Check SBOM (Software Bill of Materials)
syft myimage:latest -o json > sbom.json
```

---

## 5. Build Systems & BuildKit

### 5.1 Docker BuildKit (Modern Build Engine)

**Features**:
- Parallel layer builds
- Build cache import/export (for CI/CD)
- Build secrets (without leaking in layers)
- SSH forwarding for private repos
- Multi-platform builds (QEMU, cross-compilation)

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build with cache from registry
docker buildx build \
  --cache-from=type=registry,ref=myregistry/myimage:cache \
  --cache-to=type=registry,ref=myregistry/myimage:cache,mode=max \
  -t myimage:latest .

# Build secrets (for private dependencies)
docker buildx build \
  --secret id=github_token,src=$HOME/.github/token \
  -t myimage:latest .

# Dockerfile usage:
# RUN --mount=type=secret,id=github_token \
#     export TOKEN=$(cat /run/secrets/github_token) && \
#     go get private-repo
```

### 5.2 Multi-Platform Builds

**Use Case**: Build images for amd64, arm64, armv7 simultaneously.

```bash
# Create buildx builder
docker buildx create --name multiplatform --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t myregistry/myimage:latest \
  --push .
```

**Dockerfile cross-compilation (Go)**:

```dockerfile
FROM --platform=$BUILDPLATFORM golang:1.21-alpine AS builder
ARG TARGETPLATFORM TARGETOS TARGETARCH
WORKDIR /build
COPY . .
RUN GOOS=$TARGETOS GOARCH=$TARGETARCH go build -o app .

FROM alpine:3.19
COPY --from=builder /build/app /app
ENTRYPOINT ["/app"]
```

---

## 6. Image Distribution & Registries

### 6.1 Registry Protocols

**OCI Distribution Spec** (https://github.com/opencontainers/distribution-spec):
- **Pull**: GET /v2/<name>/manifests/<reference>, GET /v2/<name>/blobs/<digest>
- **Push**: POST /v2/<name>/blobs/uploads/, PUT /v2/<name>/manifests/<reference>
- **Authentication**: Bearer token (OAuth2), Basic Auth

**Registries**:
- **Docker Hub**: Public, rate-limited (100 pulls/6h anonymous, 200 pulls/6h authenticated)
- **GHCR** (GitHub Container Registry): Free for public, integrated with GitHub
- **ECR** (AWS), **ACR** (Azure), **GCR/Artifact Registry** (GCP): Cloud-native, private
- **Harbor**: Self-hosted, CNCF project, vulnerability scanning, RBAC, replication
- **Zot**: Lightweight OCI registry (CNCF project), minimal footprint

```bash
# Push to registry
docker tag myimage:latest myregistry.io/myimage:v1.0.0
docker push myregistry.io/myimage:v1.0.0

# Pull with digest (immutable)
docker pull myregistry.io/myimage@sha256:abc123...

# Inspect remote manifest (without pulling)
docker manifest inspect myregistry.io/myimage:v1.0.0
```

### 6.2 Registry Security

**Threats**: Man-in-the-middle, unauthorized access, malicious images.

**Mitigations**:
1. **TLS everywhere**: Enforce HTTPS for registry connections
2. **Image signing**: Cosign, Notary v2, Docker Content Trust
3. **Admission control**: Kubernetes policy engines (OPA/Gatekeeper, Kyverno) reject unsigned images
4. **Private registries**: Use cloud registries or self-host Harbor with RBAC
5. **Vulnerability scanning**: Integrate Trivy/Grype in CI/CD, reject high CVEs

```bash
# Sign image with cosign
cosign sign --key cosign.key myregistry.io/myimage:v1.0.0

# Verify in Kubernetes (admission webhook)
# Policy: Require signature from specific key
```

---

## 7. Container Runtime & Image Loading

### 7.1 containerd & Image Store

**Architecture**:

```
Docker CLI → dockerd → containerd → runc → container
             (daemon)  (runtime)    (OCI runtime)

containerd image store: /var/lib/containerd/io.containerd.content.v1.content/blobs/sha256/
```

**Image lifecycle**:
1. **Pull**: Fetch manifest, config, layers from registry
2. **Unpack**: Extract tar layers to snapshotter (OverlayFS)
3. **Create**: Generate OCI runtime spec (config.json)
4. **Start**: runc creates namespaces, cgroups, mounts, exec container process

```bash
# Inspect containerd images
ctr images ls
ctr images pull docker.io/library/alpine:latest
ctr images export alpine.tar docker.io/library/alpine:latest

# Inspect snapshots (layers)
ctr snapshots ls
```

### 7.2 Image Pull Policies & Mirroring

**Kubernetes `imagePullPolicy`**:
- `Always`: Pull on every pod creation (use for `:latest`)
- `IfNotPresent`: Pull if not cached locally (default for tagged images)
- `Never`: Never pull, use local cache only

**Mirroring/Caching** (reduce registry load, improve pull speed):
- **Harbor replication**: Sync images from Docker Hub to private registry
- **containerd registry mirrors**: Configure `/etc/containerd/config.toml`

```toml
# /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".registry.mirrors]
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
    endpoint = ["https://harbor.internal.corp/v2/dockerhub-proxy"]
```

---

## 8. Image Security Hardening

### 8.1 Threat Model

**Attack Vectors**:
1. **Supply-chain**: Malicious base image, compromised dependency
2. **Vulnerabilities**: Known CVEs in OS packages, libraries
3. **Privilege escalation**: Running as root, excessive capabilities
4. **Data exfiltration**: Container escapes, network access
5. **Lateral movement**: Container-to-container, container-to-host

**Mitigations**:

```dockerfile
# Security-hardened Dockerfile (Go app)
FROM golang:1.21-alpine AS builder
RUN apk add --no-cache ca-certificates
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download && go mod verify
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-w -s -extldflags '-static'" -o app .

FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /build/app /app
USER 65534:65534
ENTRYPOINT ["/app"]
```

**Runtime hardening**:

```bash
docker run \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64M \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  --security-opt=no-new-privileges:true \
  --security-opt=seccomp=/path/to/seccomp-profile.json \
  --pids-limit=100 \
  --memory=256M \
  --cpus=0.5 \
  --network=none \
  myimage:latest
```

### 8.2 Seccomp & AppArmor Profiles

**Seccomp**: Syscall filtering (whitelist allowed syscalls).

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {"names": ["read", "write", "open", "close", "mmap", "exit_group"], "action": "SCMP_ACT_ALLOW"}
  ]
}
```

**AppArmor**: Mandatory Access Control (file access, network, capabilities).

```bash
# Load AppArmor profile
sudo apparmor_parser -r -W /etc/apparmor.d/docker-myapp

# Run container with profile
docker run --security-opt apparmor=docker-myapp myimage:latest
```

---

## 9. Image Scanning & SBOM

### 9.1 Vulnerability Scanning

**Tools**:
- **Trivy**: Fast, accurate, supports OS packages + language deps (Go, Rust, Python, Node, etc.)
- **Grype**: Anchore's scanner, similar to Trivy
- **Snyk**: Commercial, IDE integration
- **Clair**: CoreOS project, used by Quay.io

```bash
# Scan with Trivy (local image)
trivy image --severity HIGH,CRITICAL --exit-code 1 myimage:latest

# Scan with Grype
grype myimage:latest -o json

# Scan remote image (without pulling)
trivy image --severity HIGH,CRITICAL myregistry.io/myimage:v1.0.0

# Generate SBOM (Syft)
syft myimage:latest -o spdx-json > sbom.json

# Scan SBOM with Grype
grype sbom:sbom.json
```

### 9.2 CI/CD Integration

**Pipeline example (GitHub Actions)**:

```yaml
name: Build & Scan
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build image
        run: docker build -t myimage:${{ github.sha }} .
      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myimage:${{ github.sha }}
          severity: HIGH,CRITICAL
          exit-code: 1
      - name: Sign image
        run: |
          cosign sign --key ${{ secrets.COSIGN_KEY }} myimage:${{ github.sha }}
      - name: Push image
        run: docker push myregistry.io/myimage:${{ github.sha }}
```

---

## 10. Advanced Topics

### 10.1 Image Layer Deduplication & Garbage Collection

**Problem**: Registry storage bloat from unreferenced layers.

**Solution**: Garbage collection (GC) in registries.

```bash
# Harbor GC (via API or UI)
# Removes blobs not referenced by any manifest

# Docker registry GC
docker exec registry bin/registry garbage-collect /etc/docker/registry/config.yml
```

### 10.2 Image Reproducibility

**Challenge**: Same Dockerfile + context should produce identical image (for supply-chain verification).

**Techniques**:
- **BuildKit `SOURCE_DATE_EPOCH`**: Set build timestamp to fixed value
- **Kaniko**: Google's daemonless builder, reproducible by default
- **ko**: Go-specific builder, minimal images, reproducible

```bash
# Reproducible build with BuildKit
export SOURCE_DATE_EPOCH=$(date +%s)
docker buildx build --build-arg SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH -t myimage:latest .

# Build with ko (Go)
ko build --bare --platform=linux/amd64 ./cmd/myapp
```

### 10.3 Image Attestation & SLSA

**SLSA** (Supply-chain Levels for Software Artifacts): Framework for build provenance.

**Cosign attestation**:

```bash
# Generate SBOM attestation
syft myimage:latest -o spdx-json | cosign attest --key cosign.key --type spdx myimage:latest

# Verify attestation
cosign verify-attestation --key cosign.pub myimage:latest | jq
```

---

## 11. Image Build Patterns (Language-Specific)

### 11.1 Go

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-w -s" -o app .

FROM scratch
COPY --from=builder /build/app /app
USER 65534:65534
ENTRYPOINT ["/app"]
```

### 11.2 Rust

```dockerfile
FROM rust:1.75-alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /build
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs && cargo build --release && rm -rf src
COPY . .
RUN cargo build --release

FROM scratch
COPY --from=builder /build/target/release/myapp /app
USER 65534:65534
ENTRYPOINT ["/app"]
```

### 11.3 C/C++

```dockerfile
FROM gcc:13-alpine AS builder
RUN apk add --no-cache cmake make musl-dev
WORKDIR /build
COPY . .
RUN cmake -DCMAKE_BUILD_TYPE=Release . && make

FROM alpine:3.19
RUN apk add --no-cache libstdc++
COPY --from=builder /build/myapp /app
USER nobody:nobody
ENTRYPOINT ["/app"]
```

### 11.4 Python

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
COPY . /app
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
USER nobody:nobody
CMD ["python", "app.py"]
```

---

## 12. Testing & Validation

### 12.1 Image Testing

```bash
# Test image builds
docker build -t myimage:test .

# Test container startup
docker run --rm myimage:test --version

# Test with Goss (serverspec-like for containers)
goss validate --format documentation

# Benchmark image size
docker images myimage:test --format "{{.Size}}"

# Test layer count (fewer is better)
docker history myimage:test | wc -l
```

### 12.2 Security Testing

```bash
# Run Anchore inline scan
anchore-cli image add myimage:test
anchore-cli image vuln myimage:test all

# Test privilege escalation (should fail)
docker run --rm myimage:test sh -c "whoami" # should be non-root

# Test read-only filesystem
docker run --rm --read-only myimage:test
```

---

## 13. Rollout & Rollback

### 13.1 Image Versioning Strategy

**Tagging schemes**:
- **Semantic versioning**: `v1.2.3`, `v1.2`, `v1`, `latest`
- **Git SHA**: `sha-abc1234` (immutable, traceable)
- **Build number**: `build-456`

**Best practice**: Tag with both semver and SHA, push digest.

```bash
docker tag myimage:latest myregistry.io/myimage:v1.2.3
docker tag myimage:latest myregistry.io/myimage:sha-$(git rev-parse --short HEAD)
docker push myregistry.io/myimage:v1.2.3
docker push myregistry.io/myimage:sha-$(git rev-parse --short HEAD)
```

### 13.2 Kubernetes Rollout

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    spec:
      containers:
      - name: app
        image: myregistry.io/myimage:v1.2.3
        imagePullPolicy: IfNotPresent
```

**Rollback**:

```bash
kubectl rollout undo deployment/myapp
kubectl rollout history deployment/myapp
kubectl rollout undo deployment/myapp --to-revision=2
```

---

## 14. Threat Model & Mitigations Summary

| Threat | Mitigation |
|--------|------------|
| Malicious base image | Pin digests, verify signatures, use minimal bases |
| CVEs in dependencies | Scan with Trivy/Grype, automate patching |
| Privilege escalation | Run as non-root, drop capabilities, read-only FS |
| Container escape | Seccomp, AppArmor, SELinux, user namespaces |
| Supply-chain attack | SBOM, attestations, SLSA provenance |
| Registry compromise | TLS, RBAC, image signing, admission control |
| Data exfiltration | Network policies, egress filtering |

---

## 15. Next 3 Steps

1. **Build a multi-stage, minimal image** for your primary service (Go/Rust):
   ```bash
   cd /path/to/project
   cat > Dockerfile <<'EOF'
   FROM golang:1.21-alpine AS builder
   WORKDIR /build
   COPY . .
   RUN CGO_ENABLED=0 go build -ldflags="-w -s" -o app .
   FROM scratch
   COPY --from=builder /build/app /app
   USER 65534:65534
   ENTRYPOINT ["/app"]
   EOF
   docker buildx build -t myapp:v1 .
   ```

2. **Scan and sign the image**:
   ```bash
   trivy image --severity HIGH,CRITICAL myapp:v1
   cosign generate-key-pair
   cosign sign --key cosign.key myapp:v1
   ```

3. **Deploy with security constraints** (Kubernetes):
   ```bash
   kubectl apply -f - <<EOF
   apiVersion: v1
   kind: Pod
   metadata:
     name: myapp
   spec:
     securityContext:
       runAsNonRoot: true
       runAsUser: 65534
       fsGroup: 65534
     containers:
     - name: app
       image: myapp:v1
       securityContext:
         readOnlyRootFilesystem: true
         allowPrivilegeEscalation: false
         capabilities:
           drop: ["ALL"]
   EOF
   ```

---

## 16. References

- **OCI Image Spec**: https://github.com/opencontainers/image-spec
- **OCI Distribution Spec**: https://github.com/opencontainers/distribution-spec
- **Docker BuildKit**: https://github.com/moby/buildkit
- **containerd**: https://containerd.io/
- **Trivy**: https://github.com/aquasecurity/trivy
- **Cosign**: https://github.com/sigstore/cosign
- **SLSA**: https://slsa.dev/
- **Distroless images**: https://github.com/GoogleContainerTools/distroless
- **Harbor**: https://goharbor.io/
- **CNCF Landscape**: https://landscape.cncf.io/

This covers Docker images end-to-end with security-first design. Questions on specific areas (e.g., registry internals, layer optimization strategies, Kubernetes admission control for image policy)?