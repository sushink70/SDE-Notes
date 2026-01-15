# Comprehensive Helm Guide: Package Management for Kubernetes

**Summary**: Helm is the de facto package manager for Kubernetes, enabling declarative deployment of complex applications through templated manifests (charts). It solves dependency management, versioning, rollback, and configuration reuse across environments. You'll learn chart architecture, templating engine mechanics, release lifecycle, security boundaries (RBAC, provenance, signing), repository patterns, and production deployment strategies. This guide covers Helm 3 architecture (Tiller removal), chart development workflows, hooks for job orchestration, testing/linting pipelines, and security-first practices including OCI registry integration, signing chains, and supply chain security.

---

## I. Architecture & Core Concepts

### 1.1 Helm 3 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Helm Client                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ CLI (cobra)  │  │ Chart Loader │  │ Template Eng │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │ (REST API)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes API Server                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Release Secrets (helm.sh/release.v1.*)               │ │
│  │  - Compressed JSON (gzip)                              │ │
│  │  - Release metadata + manifest                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                     ┌───────────────┐
                     │   Workloads   │
                     │ (Deployments, │
                     │  StatefulSets,│
                     │   Services)   │
                     └───────────────┘
```

**Key Changes from Helm 2**:
- **No Tiller**: Direct client-to-API server communication (eliminates privilege escalation vector)
- **3-way strategic merge**: Client, live state, and desired state reconciliation
- **Release storage**: Kubernetes Secrets in release namespace (previously ConfigMaps/Secrets in Tiller namespace)
- **Namespace scoped**: Releases live in target namespace, enabling better RBAC isolation

### 1.2 Chart Structure

```
mychart/
├── Chart.yaml          # Chart metadata (version, dependencies, type)
├── Chart.lock          # Dependency lock file (pinned versions)
├── values.yaml         # Default configuration values
├── values.schema.json  # JSON schema for values validation
├── templates/          # Template directory
│   ├── NOTES.txt      # Post-install usage notes
│   ├── _helpers.tpl   # Template partials/functions
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── serviceaccount.yaml
│   ├── rbac.yaml
│   └── tests/
│       └── test-connection.yaml
├── charts/            # Dependency charts (subcharts)
├── crds/              # Custom Resource Definitions
└── .helmignore        # Patterns to ignore when packaging
```

---

## II. Chart.yaml Deep Dive

```yaml
apiVersion: v2  # Helm 3 (v1 = Helm 2)
name: myapp
version: 1.2.3  # SemVer chart version (incremented on chart changes)
appVersion: "2.5.1"  # Application version (what's being deployed)
description: High-performance service mesh proxy
type: application  # 'application' or 'library'
keywords:
  - networking
  - proxy
  - security
home: https://github.com/org/myapp
sources:
  - https://github.com/org/myapp
maintainers:
  - name: Security Team
    email: security@example.com
icon: https://example.com/icon.svg
deprecated: false
kubeVersion: ">=1.26.0-0"  # Kubernetes version constraint

# Dependencies (alternative to requirements.yaml in Helm 2)
dependencies:
  - name: redis
    version: "~17.0.0"  # Tilde: patch-level changes allowed
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled  # Enable via values
    tags:
      - cache
    import-values:  # Import specific values from subchart
      - child: redis.master.persistence
        parent: persistence
  - name: postgresql
    version: "^12.0.0"  # Caret: minor version changes allowed
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
    alias: db  # Rename dependency

annotations:
  # OCI registry annotations
  org.opencontainers.image.source: https://github.com/org/myapp
  org.opencontainers.image.licenses: Apache-2.0
  # Artifact Hub annotations
  artifacthub.io/containsSecurityUpdates: "true"
  artifacthub.io/changes: |
    - kind: security
      description: CVE-2024-XXXX patched
```

**Security Notes**:
- Lock dependencies with `Chart.lock` (run `helm dependency update`)
- Pin `appVersion` to specific image tags (never `latest`)
- Use `kubeVersion` to prevent deployment to unsupported clusters

---

## III. Templating Engine (Go text/template + Sprig)

### 3.1 Built-in Objects

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "myapp.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
  annotations:
    helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
    helm.sh/revision: "{{ .Release.Revision }}"
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "myapp.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels:
        {{- include "myapp.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "myapp.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        {{- if .Values.command }}
        command:
          {{- toYaml .Values.command | nindent 10 }}
        {{- end }}
        ports:
        - name: http
          containerPort: {{ .Values.service.port }}
          protocol: TCP
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        {{- range $key, $value := .Values.env }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        {{- with .Values.envFrom }}
        envFrom:
          {{- toYaml . | nindent 10 }}
        {{- end }}
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
        {{- if .Values.livenessProbe.enabled }}
        livenessProbe:
          httpGet:
            path: {{ .Values.livenessProbe.path }}
            port: http
          initialDelaySeconds: {{ .Values.livenessProbe.initialDelaySeconds }}
          periodSeconds: {{ .Values.livenessProbe.periodSeconds }}
        {{- end }}
```

**Built-in Objects**:
- `.Release`: Release metadata (Name, Namespace, Revision, Service, IsUpgrade, IsInstall)
- `.Chart`: Chart.yaml content
- `.Values`: Merged values (defaults + user overrides)
- `.Files`: Access to non-template files
- `.Capabilities`: Kubernetes cluster capabilities (API versions, Kube version)
- `.Template`: Current template information (Name, BasePath)

### 3.2 Helper Templates (_helpers.tpl)

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "myapp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
Truncate at 63 chars (DNS label limit).
*/}}
{{- define "myapp.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "myapp.labels" -}}
helm.sh/chart: {{ include "myapp.chart" . }}
{{ include "myapp.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "myapp.selectorLabels" -}}
app.kubernetes.io/name: {{ include "myapp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "myapp.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "myapp.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Chart name and version as used by the chart label.
*/}}
{{- define "myapp.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Image pull secret
*/}}
{{- define "myapp.imagePullSecret" }}
{{- with .Values.imageCredentials }}
{{- printf "{\"auths\":{\"%s\":{\"username\":\"%s\",\"password\":\"%s\",\"email\":\"%s\",\"auth\":\"%s\"}}}" .registry .username .password .email (printf "%s:%s" .username .password | b64enc) | b64enc }}
{{- end }}
{{- end }}
```

### 3.3 Advanced Templating Patterns

```yaml
# Conditional rendering
{{- if and .Values.ingress.enabled .Values.ingress.tls }}
tls:
{{- range .Values.ingress.tls }}
  - hosts:
    {{- range .hosts }}
    - {{ . | quote }}
    {{- end }}
    secretName: {{ .secretName }}
{{- end }}
{{- end }}

# Range with pipeline
{{- range $key, $val := .Values.configMap }}
{{ $key }}: {{ $val | quote }}
{{- end }}

# Fail template rendering on invalid input
{{- if not (or (eq .Values.service.type "ClusterIP") (eq .Values.service.type "NodePort") (eq .Values.service.type "LoadBalancer")) }}
{{- fail "service.type must be ClusterIP, NodePort, or LoadBalancer" }}
{{- end }}

# Lookup existing resources (runtime query)
{{- $existingSecret := lookup "v1" "Secret" .Release.Namespace "my-secret" }}
{{- if $existingSecret }}
# Use existing secret
{{- else }}
# Create new secret
{{- end }}

# File inclusion
{{- (.Files.Glob "config/*.json").AsConfig | nindent 2 }}

# Required values
{{- required "A valid .Values.persistence.storageClass required!" .Values.persistence.storageClass }}
```

---

## IV. Values Files & Schema Validation

### 4.1 values.yaml Structure

```yaml
# Global values (accessible to all subcharts)
global:
  imageRegistry: ""
  imagePullSecrets: []
  storageClass: ""

# Application config
replicaCount: 3

image:
  repository: ghcr.io/org/myapp
  pullPolicy: IfNotPresent
  tag: ""  # Defaults to .Chart.AppVersion

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9090"

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 65534
  fsGroup: 65534
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true

service:
  type: ClusterIP
  port: 8080
  annotations: {}

ingress:
  enabled: false
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: myapp.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: myapp-tls
      hosts:
        - myapp.example.com

resources:
  limits:
    cpu: 1000m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

livenessProbe:
  enabled: true
  path: /healthz
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  enabled: true
  path: /ready
  initialDelaySeconds: 5
  periodSeconds: 5

nodeSelector: {}
tolerations: []
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app.kubernetes.io/name
            operator: In
            values:
            - myapp
        topologyKey: kubernetes.io/hostname

# PodDisruptionBudget
podDisruptionBudget:
  enabled: true
  minAvailable: 1
  # maxUnavailable: 1

# Network Policy
networkPolicy:
  enabled: true
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: ingress-nginx
      ports:
      - protocol: TCP
        port: 8080
  egress:
    - to:
      - namespaceSelector: {}
      ports:
      - protocol: TCP
        port: 443
    - to:
      - namespaceSelector:
          matchLabels:
            name: kube-system
      ports:
      - protocol: UDP
        port: 53

# ConfigMap data
configMap:
  LOG_LEVEL: "info"
  ENVIRONMENT: "production"

# Secret data (base64 encoded)
secrets:
  API_KEY: ""  # Provide via --set or sealed secrets

# Persistence
persistence:
  enabled: false
  storageClass: ""
  accessMode: ReadWriteOnce
  size: 10Gi
  annotations: {}
```

### 4.2 values.schema.json (OpenAPI v3)

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["replicaCount", "image"],
  "properties": {
    "replicaCount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "description": "Number of replicas"
    },
    "image": {
      "type": "object",
      "required": ["repository"],
      "properties": {
        "repository": {
          "type": "string",
          "pattern": "^[a-z0-9.-]+/[a-z0-9._-]+(/[a-z0-9._-]+)*$"
        },
        "tag": {
          "type": "string",
          "pattern": "^[a-zA-Z0-9._-]+$"
        },
        "pullPolicy": {
          "type": "string",
          "enum": ["Always", "IfNotPresent", "Never"]
        }
      }
    },
    "service": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["ClusterIP", "NodePort", "LoadBalancer"]
        },
        "port": {
          "type": "integer",
          "minimum": 1,
          "maximum": 65535
        }
      }
    },
    "resources": {
      "type": "object",
      "properties": {
        "limits": {
          "$ref": "#/definitions/resourceRequirements"
        },
        "requests": {
          "$ref": "#/definitions/resourceRequirements"
        }
      }
    }
  },
  "definitions": {
    "resourceRequirements": {
      "type": "object",
      "properties": {
        "cpu": {
          "type": "string",
          "pattern": "^[0-9]+(m|[.]?[0-9]*)$"
        },
        "memory": {
          "type": "string",
          "pattern": "^[0-9]+(Ei|Pi|Ti|Gi|Mi|Ki|E|P|T|G|M|K)?$"
        }
      }
    }
  }
}
```

**Validation**: Helm validates user-provided values against this schema before rendering templates.

---

## V. Hooks & Lifecycle Management

```yaml
# templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "myapp.fullname" . }}-pre-install
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    metadata:
      name: {{ include "myapp.fullname" . }}-pre-install
    spec:
      restartPolicy: Never
      serviceAccountName: {{ include "myapp.serviceAccountName" . }}
      containers:
      - name: pre-install
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        command: ["/bin/sh", "-c"]
        args:
          - |
            echo "Running pre-install checks..."
            # Database schema migrations, prerequisite validation, etc.
```

**Available Hooks** (execution order):
1. `pre-install`: Before resources are loaded into Kubernetes
2. `post-install`: After all resources are loaded
3. `pre-delete`: Before any resources are deleted
4. `post-delete`: After all resources are deleted
5. `pre-upgrade`: Before templates are rendered for upgrade
6. `post-upgrade`: After all resources are upgraded
7. `pre-rollback`: Before rollback
8. `post-rollback`: After rollback
9. `test`: When `helm test` is invoked

**Hook Weights**: Control execution order (lower weights execute first)

**Delete Policies**:
- `before-hook-creation`: Delete previous hook resource before new one
- `hook-succeeded`: Delete after successful execution
- `hook-failed`: Delete after failed execution

---

## VI. Chart Dependencies

### 6.1 Dependency Management

```bash
# Chart.yaml dependencies section shown earlier

# Update dependencies (download to charts/ and create Chart.lock)
helm dependency update mychart/

# Build dependencies (use existing Chart.lock)
helm dependency build mychart/

# List dependencies
helm dependency list mychart/
```

### 6.2 Subchart Value Overrides

```yaml
# Parent chart values.yaml
redis:
  enabled: true
  auth:
    enabled: true
    password: "strongpassword"
  master:
    persistence:
      enabled: true
      size: 8Gi
  replica:
    replicaCount: 2

postgresql:
  enabled: false
```

**Global Values Access**: Subcharts can access `.Values.global.*`

```yaml
# Subchart can access parent's global values
{{- if .Values.global.imageRegistry }}
image: {{ .Values.global.imageRegistry }}/{{ .Values.image.repository }}
{{- end }}
```

---

## VII. Release Management

### 7.1 Installation & Upgrades

```bash
# Install with default values
helm install myrelease mychart/

# Install with custom values
helm install myrelease mychart/ \
  -f values-production.yaml \
  --set replicaCount=5 \
  --set image.tag=v1.2.3 \
  --namespace production \
  --create-namespace

# Dry-run to see rendered manifests
helm install myrelease mychart/ \
  --dry-run --debug \
  --namespace production

# Upgrade release
helm upgrade myrelease mychart/ \
  -f values-production.yaml \
  --set image.tag=v1.2.4 \
  --namespace production \
  --timeout 10m \
  --wait \
  --atomic  # Rollback on failure

# Install or upgrade (idempotent)
helm upgrade --install myrelease mychart/ \
  -f values-production.yaml \
  --namespace production \
  --create-namespace

# Force resource updates (recreate)
helm upgrade myrelease mychart/ --force

# Reuse previous values during upgrade
helm upgrade myrelease mychart/ --reuse-values
```

### 7.2 Rollback & History

```bash
# List releases
helm list -n production
helm list --all-namespaces

# Get release history
helm history myrelease -n production

# Rollback to previous revision
helm rollback myrelease -n production

# Rollback to specific revision
helm rollback myrelease 3 -n production

# Rollback with wait
helm rollback myrelease --wait --timeout 5m -n production
```

### 7.3 Uninstallation

```bash
# Uninstall release
helm uninstall myrelease -n production

# Keep release history for debugging
helm uninstall myrelease -n production --keep-history

# Dry-run uninstall
helm uninstall myrelease -n production --dry-run
```

---

## VIII. Chart Repositories

### 8.1 Traditional HTTP Repositories

```bash
# Add repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add stable https://charts.helm.sh/stable

# Update repository index
helm repo update

# Search repository
helm search repo redis
helm search repo bitnami/redis --versions

# Remove repository
helm repo remove bitnami

# List repositories
helm repo list

# Show repository index
helm repo index . --url https://myrepo.example.com/charts
```

**Repository Structure**:
```
charts/
├── index.yaml  # Repository index (generated by helm repo index)
├── myapp-1.0.0.tgz
├── myapp-1.0.1.tgz
└── myapp-1.1.0.tgz
```

### 8.2 OCI Registries (Recommended)

```bash
# Login to OCI registry
helm registry login ghcr.io -u username

# Package chart
helm package mychart/

# Push to OCI registry
helm push mychart-1.0.0.tgz oci://ghcr.io/org/charts

# Pull chart
helm pull oci://ghcr.io/org/charts/mychart --version 1.0.0

# Install from OCI registry
helm install myrelease oci://ghcr.io/org/charts/mychart --version 1.0.0

# Show chart metadata
helm show chart oci://ghcr.io/org/charts/mychart --version 1.0.0
helm show values oci://ghcr.io/org/charts/mychart --version 1.0.0
helm show all oci://ghcr.io/org/charts/mychart --version 1.0.0

# Logout
helm registry logout ghcr.io
```

**OCI Advantages**:
- Standard container registry infrastructure (reuse Harbor, ECR, ACR, GCR, GHCR)
- Native signing/verification with Cosign/Notary
- RBAC and access control via registry policies
- Integrated with CI/CD pipelines

---

## IX. Chart Development Workflow

### 9.1 Create & Package

```bash
# Create new chart
helm create mychart

# Lint chart
helm lint mychart/

# Template dry-run (render templates)
helm template myrelease mychart/ \
  -f values-production.yaml \
  --debug

# Package chart
helm package mychart/

# Package with specific version/app-version
helm package mychart/ \
  --version 1.2.3 \
  --app-version v2.5.0

# Sign chart (requires GPG key)
helm package mychart/ --sign --key 'Security Team' --keyring ~/.gnupg/secring.gpg

# Verify signed chart
helm verify mychart-1.0.0.tgz --keyring ~/.gnupg/pubring.gpg
```

### 9.2 Testing

```yaml
# templates/tests/test-connection.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "myapp.fullname" . }}-test-connection"
  annotations:
    "helm.sh/hook": test
spec:
  restartPolicy: Never
  containers:
  - name: wget
    image: busybox
    command: ['wget']
    args: ['{{ include "myapp.fullname" . }}:{{ .Values.service.port }}/healthz']
```

```bash
# Run tests
helm test myrelease -n production

# Run tests with logs
helm test myrelease -n production --logs

# Cleanup test pods
kubectl delete pod -n production -l "helm.sh/hook=test"
```

### 9.3 Debug & Troubleshooting

```bash
# Get manifest of deployed release
helm get manifest myrelease -n production

# Get values used for release
helm get values myrelease -n production

# Get all release information
helm get all myrelease -n production

# Get release hooks
helm get hooks myrelease -n production

# Debug template rendering
helm template myrelease mychart/ --debug

# Show computed values (merged)
helm show values mychart/

# Validate against Kubernetes API
helm install myrelease mychart/ --dry-run --validate
```

---

## X. Security-First Practices

### 10.1 Chart Provenance & Signing

```bash
# Generate GPG key
gpg --full-generate-key

# Export public key
gpg --armor --export security@example.com > pubkey.asc

# Package and sign
helm package mychart/ \
  --sign \
  --key 'security@example.com' \
  --keyring ~/.gnupg/secring.gpg

# Verify chart signature
helm verify mychart-1.0.0.tgz \
  --keyring ~/.gnupg/pubring.gpg

# Install only verified charts
helm install myrelease mychart-1.0.0.tgz \
  --verify \
  --keyring ~/.gnupg/pubring.gpg
```

**Provenance File** (`mychart-1.0.0.tgz.prov`):
```
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

description: Chart metadata and hash
...
-----BEGIN PGP SIGNATURE-----
...
-----END PGP SIGNATURE-----
```

### 10.2 Supply Chain Security (Cosign)

```bash
# Sign chart with Cosign (keyless)
cosign sign ghcr.io/org/charts/mychart:1.0.0

# Verify signature
cosign verify ghcr.io/org/charts/mychart:1.0.0 \
  --certificate-identity-regexp="^https://github.com/org/.*$" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

# Attach SBOM
syft packages oci://ghcr.io/org/charts/mychart:1.0.0 -o spdx-json > sbom.json
cosign attach sbom --sbom sbom.json ghcr.io/org/charts/mychart:1.0.0

# Verify SBOM
cosign verify-attestation ghcr.io/org/charts/mychart:1.0.0 \
  --type spdx
```

### 10.3 RBAC for Helm

```yaml
# ServiceAccount for Helm operations
apiVersion: v1
kind: ServiceAccount
metadata:
  name: helm-deploy
  namespace: production

---
# Role for chart deployments
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: helm-deploy
  namespace: production
rules:
- apiGroups: ["", "apps", "batch", "networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["sh.helm.release.v1.*"]
  verbs: ["*"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: helm-deploy
  namespace: production
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: helm-deploy
subjects:
- kind: ServiceAccount
  name: helm-deploy
  namespace: production
```

```bash
# Use specific service account
helm install myrelease mychart/ \
  --namespace production \
  --service-account helm-deploy
```