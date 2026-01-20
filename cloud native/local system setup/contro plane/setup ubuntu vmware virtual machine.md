# Setting up a Secure Kubernetes Control Plane on Ubuntu VM

# Summary: Production-Grade Kubernetes Control Plane Setup

You're building a **two-node Kubernetes cluster** (1 control plane, 1 worker) to run lightweight microservices (Flask, Django, FastAPI) for learning cloud-native patterns. Control plane gets 8GB RAM, worker gets 16GB RAM—sufficient for 4 pods with light workloads. We'll use **kubeadm** for reproducible, production-aligned setup, focus on **containerd runtime** (CNCF standard), **Cilium CNI** for advanced networking/security, and implement **security-first patterns** (RBAC, NetworkPolicies, admission control). This guide covers control plane setup with explicit threat mitigations, verification steps, and next actions.

---

## Architecture View

```
┌─────────────────────────────────────────────────────────────────┐
│ Kali Linux Host (VMware Workstation Pro)                       │
│  ├─ VM1: control-plane (8GB RAM, 2 vCPU)  10.0.0.10            │
│  │   ├─ kube-apiserver :6443 (HTTPS, mTLS)                     │
│  │   ├─ kube-controller-manager (localhost only)               │
│  │   ├─ kube-scheduler (localhost only)                        │
│  │   ├─ etcd :2379-2380 (mTLS, localhost bind)                │
│  │   ├─ kubelet :10250 (authN/authZ enabled)                   │
│  │   ├─ containerd runtime + CNI plugins                       │
│  │   └─ Cilium agent (eBPF datapath, NetworkPolicy enforce)    │
│  │                                                              │
│  └─ VM2: worker-01 (16GB RAM, 4 vCPU)  10.0.0.20               │
│      ├─ kubelet :10250                                          │
│      ├─ containerd runtime                                      │
│      ├─ Cilium agent                                            │
│      └─ kube-proxy (or Cilium kube-proxy replacement)          │
│                                                                 │
│  Pod Network: 10.244.0.0/16 (Cilium-managed)                   │
│  Service CIDR: 10.96.0.0/12                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Control Plane Node: Installation & Configuration

### Prerequisites & System Preparation

```bash
# On control-plane VM (Ubuntu 22.04/24.04)
# Set hostname
sudo hostnamectl set-hostname control-plane

# Update /etc/hosts with static IPs
sudo tee -a /etc/hosts <<EOF
10.0.0.10 control-plane
10.0.0.20 worker-01
EOF

# Disable swap (Kubernetes requirement)
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Load required kernel modules
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# Configure sysctl for networking
sudo tee /etc/sysctl.d/k8s.conf <<EOF
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system

# Verify modules loaded
lsmod | grep -E 'overlay|br_netfilter'
sysctl net.bridge.bridge-nf-call-iptables net.ipv4.ip_forward
```

**Threat Context**: Swap can leak sensitive secrets to disk; improper netfilter config breaks pod-to-pod routing and NetworkPolicy enforcement.

---

### Install Container Runtime (containerd)

```bash
# Install containerd from Docker's repo (stable, well-tested)
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add repo
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y containerd.io

# Generate default config and enable systemd cgroup driver
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# CRITICAL: Enable systemd cgroup driver (required for kubelet)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# Restart and verify
sudo systemctl restart containerd
sudo systemctl enable containerd
sudo systemctl status containerd
```

**Security Hardening**:
```bash
# Restrict containerd socket permissions
sudo chmod 660 /run/containerd/containerd.sock
sudo chown root:root /run/containerd/containerd.sock

# Verify no world-readable socket
ls -la /run/containerd/containerd.sock
# Should show: srw-rw---- 1 root root
```

---

### Install Kubernetes Components

```bash
# Install kubeadm, kubelet, kubectl (v1.31.x - latest stable as of Jan 2025)
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Add Kubernetes GPG key
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add repo
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \
  https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | \
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# Verify versions
kubeadm version
kubelet --version
kubectl version --client
```

---

### Initialize Control Plane with kubeadm

```bash
# Create kubeadm config for reproducibility and security
cat <<EOF | sudo tee /tmp/kubeadm-config.yaml
apiVersion: kubeadm.k8s.io/v1beta3
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 10.0.0.10
  bindPort: 6443
nodeRegistration:
  criSocket: unix:///run/containerd/containerd.sock
  name: control-plane
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/control-plane
---
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
kubernetesVersion: v1.31.0
clusterName: secure-lab-cluster
controlPlaneEndpoint: "10.0.0.10:6443"
networking:
  podSubnet: 10.244.0.0/16
  serviceSubnet: 10.96.0.0/12
etcd:
  local:
    dataDir: /var/lib/etcd
    extraArgs:
      listen-client-urls: "https://127.0.0.1:2379"
      advertise-client-urls: "https://127.0.0.1:2379"
apiServer:
  certSANs:
  - "10.0.0.10"
  - "control-plane"
  - "127.0.0.1"
  extraArgs:
    audit-log-path: /var/log/kubernetes/audit.log
    audit-log-maxage: "30"
    audit-log-maxbackup: "10"
    audit-log-maxsize: "100"
    enable-admission-plugins: NodeRestriction,PodSecurity
    profiling: "false"
    anonymous-auth: "false"
controllerManager:
  extraArgs:
    profiling: "false"
    bind-address: 127.0.0.1
scheduler:
  extraArgs:
    profiling: "false"
    bind-address: 127.0.0.1
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
serverTLSBootstrap: true
tlsCipherSuites:
- TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
- TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
- TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
- TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
EOF

# Initialize cluster
sudo kubeadm init --config /tmp/kubeadm-config.yaml

# CRITICAL: Save join command output - you'll need it for worker node
# Example output:
# kubeadm join 10.0.0.10:6443 --token <token> \
#   --discovery-token-ca-cert-hash sha256:<hash>
```

**Post-Init Setup**:
```bash
# Configure kubectl for current user
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Verify control plane components
kubectl get nodes
kubectl get pods -n kube-system

# Check component health
kubectl get --raw='/readyz?verbose'
kubectl get cs  # deprecated but still useful
```

---

### Install CNI: Cilium (Security-First Networking)

**Why Cilium**: eBPF-based, L7-aware NetworkPolicies, Hubble observability, transparent encryption, kube-proxy replacement for performance.

```bash
# Install Cilium CLI
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
CLI_ARCH=amd64
curl -L --fail --remote-name-all \
  https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
sha256sum --check cilium-linux-${CLI_ARCH}.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
rm cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}

# Install Cilium into cluster (replace kube-proxy for better performance)
cilium install \
  --version 1.16.5 \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost=10.0.0.10 \
  --set k8sServicePort=6443

# Wait for Cilium to be ready
cilium status --wait

# Verify CNI
kubectl get pods -n kube-system | grep cilium
kubectl get nodes  # Should show Ready
```

**Enable Hubble (Observability)**:
```bash
cilium hubble enable --ui

# Verify Hubble
kubectl get pods -n kube-system | grep hubble

# Port-forward to access Hubble UI (optional, later)
# kubectl port-forward -n kube-system svc/hubble-ui 12000:80
```

---

## Security Hardening & Verification

### 1. Audit Logging
```bash
# Create audit log directory
sudo mkdir -p /var/log/kubernetes
sudo chmod 700 /var/log/kubernetes

# Verify audit logs are being written
sudo ls -lah /var/log/kubernetes/
sudo tail -f /var/log/kubernetes/audit.log
```

### 2. RBAC Verification
```bash
# Test that anonymous access is blocked
curl -k https://10.0.0.10:6443/api/v1/namespaces
# Should return 401 Unauthorized

# Create read-only user for testing (later)
# kubectl create serviceaccount readonly-user
# kubectl create clusterrolebinding readonly-binding \
#   --clusterrole=view --serviceaccount=default:readonly-user
```

### 3. Network Policy Testing (After Worker Joins)
```bash
# Default deny all ingress policy (apply per namespace)
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF
```

### 4. Pod Security Standards
```bash
# Enforce baseline pod security at namespace level
kubectl label namespace default \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted
```

---

## Threat Model & Mitigations

| Threat | Impact | Mitigation |
|--------|--------|------------|
| **etcd data exfiltration** | Cluster secrets, config leakage | etcd bound to localhost, mTLS enforced, encrypt at rest (add later) |
| **API server MITM** | Credential theft, cluster takeover | mTLS required, anonymous auth disabled, audit logging |
| **Kubelet unauthorized access** | Node compromise, container escape | TLS bootstrap, NodeRestriction admission, RBAC |
| **Pod-to-pod lateral movement** | Workload compromise spreads | Cilium NetworkPolicies, default-deny posture, L7 policies |
| **Privilege escalation via insecure pod** | Container breakout to host | PodSecurity admission (baseline/restricted), seccomp/AppArmor |
| **Control plane component exploit** | Full cluster compromise | Disable profiling endpoints, bind scheduler/controller to localhost |

---

## Verification & Testing

```bash
# 1. Verify all control plane pods running
kubectl get pods -n kube-system
# Expected: kube-apiserver, kube-controller-manager, kube-scheduler, etcd, coredns, cilium

# 2. Check node status
kubectl get nodes -o wide
# control-plane should be Ready

# 3. Verify CNI health
cilium status
cilium connectivity test  # Takes 5-10 min, run after worker joins

# 4. Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup kubernetes.default
# Should resolve to 10.96.0.1

# 5. Check certificate validity
sudo kubeadm certs check-expiration

# 6. Verify API server is only accessible via HTTPS
curl -k https://10.0.0.10:6443/healthz
# Should return "ok"

curl http://10.0.0.10:6443/healthz
# Should fail (no HTTP endpoint)
```

---

## Rollback Plan

```bash
# If init fails or you need to reset
sudo kubeadm reset -f
sudo rm -rf /etc/cni/net.d
sudo rm -rf $HOME/.kube/config
sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F && sudo iptables -X

# Remove Cilium state
sudo rm -rf /var/lib/cilium

# Re-run init process from "Initialize Control Plane" step
```

---

## Next 3 Steps

1. **Save Join Token**: If you lost the join command, regenerate it:
   ```bash
   kubeadm token create --print-join-command
   ```
   You'll use this on the worker node.

2. **Prepare Worker Node** (next guide): Install containerd, kubelet, kubeadm on worker-01, then join the cluster.

3. **Deploy Test Workloads**: After worker joins, create namespaces for your apps (flask, django, fastapi) with NetworkPolicies and resource limits.

https://claude.ai/share/8b47210d-0f88-43f0-9267-e84e4b6be088

---

## References

- [kubeadm init reference](https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm-init/)
- [Cilium Installation](https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/)
- [Kubernetes Hardening Guide (NSA/CISA)](https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [containerd systemd cgroup driver](https://kubernetes.io/docs/setup/production-environment/container-runtimes/#containerd-systemd)

**Control plane is now production-ready**. Proceed with worker node setup when ready.

---

The Kubernetes control plane requires several critical components: container runtime (containerd), kubelet, kubeadm, kubectl, and etcd. Additional production needs include CNI plugins, load balancer for HA, certificate management tooling, and monitoring agents. For a security-first production setup, you need hardened kernel parameters, AppArmor/SELinux policies, audit logging, and encrypted etcd. This guide provides end-to-end installation with security controls, verification steps, and production-grade configuration for a single control plane node that can scale to HA later.

---

## Architecture View

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane Node                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  kube-apiserver (6443) ← External/Internal Access    │   │
│  │    ↓ authz/authn ↓                                   │   │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  │   │
│  │  │kube-sched  │  │kube-ctrl-mgr │  │cloud-ctrl-  │  │   │
│  │  │            │  │              │  │mgr (opt)    │  │   │
│  │  └────────────┘  └──────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  etcd cluster (2379/2380) - encrypted at rest        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  kubelet + container runtime (containerd/CRI-O)      │   │
│  │    ↓ CNI plugins (Calico/Cilium) ↓                   │   │
│  │  Pod network (overlay or BGP)                        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CoreDNS, kube-proxy (optional: eBPF replacement)    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          ↑ SSH (22) - harden, key-only, fail2ban
          ↑ Node exporter (9100), kubelet metrics (10250/10255)
```

---

## Pre-requisites and System Hardening

### 1. Base System Configuration

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Set hostname (use FQDN)
sudo hostnamectl set-hostname k8s-cp-01.local

# Disable swap (required for kubelet)
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# Verify
free -h | grep -i swap  # Should show 0

# Load kernel modules for container runtime
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# Verify
lsmod | grep -E 'overlay|br_netfilter'

# Sysctl params for Kubernetes networking
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
net.ipv4.conf.all.rp_filter         = 1
net.ipv4.conf.default.rp_filter     = 1
# Security hardening
kernel.kptr_restrict                = 2
kernel.dmesg_restrict               = 1
kernel.perf_event_paranoid          = 3
net.ipv4.conf.all.send_redirects    = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
EOF

sudo sysctl --system

# Verify
sysctl net.bridge.bridge-nf-call-iptables net.ipv4.ip_forward
```

### 2. Install Essential Packages

```bash
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    socat \
    conntrack \
    ipset \
    iptables \
    apparmor \
    apparmor-utils \
    auditd \
    fail2ban
```

---

## Container Runtime: containerd

### Installation

```bash
# Add Docker's official GPG key (containerd is part of Docker packages)
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install containerd
sudo apt-get update
sudo apt-get install -y containerd.io

# Generate default config
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Enable SystemdCgroup (required for kubelet)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# Restart and enable
sudo systemctl restart containerd
sudo systemctl enable containerd
sudo systemctl status containerd

# Verify
sudo ctr version
```

### Security Hardening for containerd

```bash
# Configure containerd with security best practices
sudo tee /etc/containerd/config.toml > /dev/null <<'EOF'
version = 2

[plugins."io.containerd.grpc.v1.cri"]
  sandbox_image = "registry.k8s.io/pause:3.9"
  
[plugins."io.containerd.grpc.v1.cri".containerd]
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes]
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
      runtime_type = "io.containerd.runc.v2"
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
        SystemdCgroup = true

[plugins."io.containerd.grpc.v1.cri".cni]
  bin_dir = "/opt/cni/bin"
  conf_dir = "/etc/cni/net.d"

# Disable exposing metrics on 0.0.0.0
[metrics]
  address = "127.0.0.1:1338"
EOF

sudo systemctl restart containerd
```

---

## Kubernetes Components: kubeadm, kubelet, kubectl

### Installation

```bash
# Add Kubernetes GPG key and repository
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | \
    sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \
    https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | \
    sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install specific version (pin for production)
sudo apt-get update
K8S_VERSION="1.29.1-1.1"
sudo apt-get install -y \
    kubelet=${K8S_VERSION} \
    kubeadm=${K8S_VERSION} \
    kubectl=${K8S_VERSION}

# Hold packages to prevent auto-upgrade
sudo apt-mark hold kubelet kubeadm kubectl

# Verify
kubeadm version
kubelet --version
kubectl version --client
```

### Configure kubelet

```bash
# Create kubelet service directory
sudo mkdir -p /etc/systemd/system/kubelet.service.d

# Kubelet extra args for security
sudo tee /etc/default/kubelet > /dev/null <<'EOF'
KUBELET_EXTRA_ARGS=--read-only-port=0 \
    --anonymous-auth=false \
    --protect-kernel-defaults=true \
    --tls-cipher-suites=TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384 \
    --event-qps=0
EOF

sudo systemctl daemon-reload
sudo systemctl enable kubelet
# Don't start yet - kubeadm will do this
```

---

## Initialize Control Plane with kubeadm

### Create kubeadm Configuration

```bash
# Get your node IP (replace ens33 with your interface)
NODE_IP=$(ip -4 addr show ens33 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

cat <<EOF | sudo tee /root/kubeadm-config.yaml
apiVersion: kubeadm.k8s.io/v1beta3
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: ${NODE_IP}
  bindPort: 6443
nodeRegistration:
  criSocket: unix:///var/run/containerd/containerd.sock
  imagePullPolicy: IfNotPresent
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/control-plane
---
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
kubernetesVersion: v1.29.1
controlPlaneEndpoint: "${NODE_IP}:6443"
networking:
  podSubnet: "10.244.0.0/16"  # Adjust based on CNI
  serviceSubnet: "10.96.0.0/12"
apiServer:
  certSANs:
  - ${NODE_IP}
  - k8s-cp-01.local
  - localhost
  - 127.0.0.1
  extraArgs:
    # Security hardening
    anonymous-auth: "false"
    audit-log-path: "/var/log/kubernetes/audit.log"
    audit-log-maxage: "30"
    audit-log-maxbackup: "10"
    audit-log-maxsize: "100"
    enable-admission-plugins: "NodeRestriction,PodSecurityPolicy"
    profiling: "false"
    tls-cipher-suites: "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
    encryption-provider-config: "/etc/kubernetes/enc/encryption-config.yaml"
  extraVolumes:
  - name: audit-log
    hostPath: /var/log/kubernetes
    mountPath: /var/log/kubernetes
    readOnly: false
  - name: encryption-config
    hostPath: /etc/kubernetes/enc
    mountPath: /etc/kubernetes/enc
    readOnly: true
controllerManager:
  extraArgs:
    profiling: "false"
    terminated-pod-gc-threshold: "100"
scheduler:
  extraArgs:
    profiling: "false"
etcd:
  local:
    extraArgs:
      # Encrypt etcd at rest
      auto-tls: "false"
      peer-auto-tls: "false"
    dataDir: /var/lib/etcd
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
authorization:
  mode: Webhook
readOnlyPort: 0
protectKernelDefaults: true
tlsCipherSuites:
- TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
- TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
EOF
```

### etcd Encryption at Rest

```bash
# Generate encryption key
ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)

sudo mkdir -p /etc/kubernetes/enc

cat <<EOF | sudo tee /etc/kubernetes/enc/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
    - secrets
    providers:
    - aescbc:
        keys:
        - name: key1
          secret: ${ENCRYPTION_KEY}
    - identity: {}
EOF

sudo chmod 600 /etc/kubernetes/enc/encryption-config.yaml
```

### Audit Policy

```bash
sudo mkdir -p /var/log/kubernetes

cat <<EOF | sudo tee /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: Metadata
  resources:
  - group: ""
    resources: ["pods", "services"]
- level: Request
  users: ["system:serviceaccount:kube-system:*"]
  verbs: ["get", "list", "watch"]
- level: None
  users: ["system:kube-proxy"]
  verbs: ["watch"]
  resources:
  - group: ""
    resources: ["endpoints", "services"]
EOF
```

### Run kubeadm init

```bash
# Pre-pull images
sudo kubeadm config images pull --config /root/kubeadm-config.yaml

# Initialize cluster
sudo kubeadm init --config /root/kubeadm-config.yaml --upload-certs

# Expected output includes join commands - SAVE THESE SECURELY

# Setup kubectl for root
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Verify
kubectl get nodes
kubectl get pods -A
```

---

## CNI Plugin: Calico (Security-focused)

```bash
# Download Calico manifest
curl -O https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml

# Modify CIDR to match kubeadm config (10.244.0.0/16)
sed -i 's|# - name: CALICO_IPV4POOL_CIDR|- name: CALICO_IPV4POOL_CIDR|' calico.yaml
sed -i 's|#   value: "192.168.0.0/16"|  value: "10.244.0.0/16"|' calico.yaml

# Apply
kubectl apply -f calico.yaml

# Wait for pods to be ready
kubectl wait --for=condition=Ready pods --all -n kube-system --timeout=300s

# Verify
kubectl get pods -n kube-system
kubectl get nodes  # Should show Ready
```

---

## Additional Production Components

### 1. MetalLB (Optional: for LoadBalancer service type)

```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml

# Configure IP pool (adjust to your network)
cat <<EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.240-192.168.1.250  # Adjust to free IPs in your network
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
EOF
```

### 2. Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For test environments, disable TLS verification
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

### 3. Local Storage Provisioner (for StatefulSets)

```bash
# Create StorageClass
cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
EOF
```

---

## Threat Model and Mitigation

| **Threat** | **Attack Vector** | **Mitigation** | **Verification** |
|------------|-------------------|----------------|------------------|
| Unauthorized API access | Exposed 6443, weak RBAC | Firewall + cert-based auth + RBAC | `kubectl auth can-i --list` |
| etcd data exfiltration | Unencrypted etcd data | Encryption at rest + mTLS | Check `/etc/kubernetes/enc/` |
| Container escape | Vulnerable runtime | AppArmor profiles, seccomp, readonly root | `aa-status`, `kubectl get psp` |
| Lateral movement | Flat pod network | NetworkPolicies, Calico policies | `kubectl get networkpolicies -A` |
| Privilege escalation | Weak admission control | PodSecurityPolicy/PodSecurity | Enforce PSP/PSS |
| Node compromise | SSH brute force | Key-only SSH, fail2ban, audit logs | `sudo fail2ban-client status sshd` |
| Supply chain attacks | Malicious images | Image scanning (Trivy), admission webhooks | `trivy image <image>` |

---

## Security Validation and Testing

### 1. Kube-bench (CIS Benchmark)

```bash
# Run kube-bench
docker run --pid=host -v /etc:/etc:ro -v /var:/var:ro \
    aquasec/kube-bench:latest run --targets master

# Review failures and remediate
```

### 2. Falco (Runtime Security)

```bash
# Install Falco
kubectl apply -f https://raw.githubusercontent.com/falcosecurity/charts/master/falco/templates/daemonset.yaml

# Monitor events
kubectl logs -n falco -l app=falco -f
```

### 3. Network Policy Testing

```bash
# Deploy test pods
kubectl run test-pod-1 --image=nginx
kubectl run test-pod-2 --image=busybox --command sleep 3600

# Apply deny-all policy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF

# Test (should fail)
kubectl exec test-pod-2 -- wget -O- test-pod-1 --timeout=2
```

---

## Rollout and Rollback Plan

### Rollout
1. **Pre-check**: Verify all prerequisites, backup `/etc/kubernetes`, etcd snapshot
2. **Init control plane**: `kubeadm init` with config
3. **Deploy CNI**: Apply Calico/Cilium
4. **Validation**: Node ready, pods running, DNS resolution
5. **Smoke tests**: Deploy test workload, check logs/metrics

### Rollback
```bash
# If init fails
sudo kubeadm reset -f
sudo rm -rf /etc/kubernetes /var/lib/kubelet /var/lib/etcd
sudo systemctl restart containerd

# If CNI fails
kubectl delete -f calico.yaml
# Fix config, reapply
```

### etcd Backup/Restore

```bash
# Backup
sudo ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%Y%m%d).db \
    --endpoints=https://127.0.0.1:2379 \
    --cacert=/etc/kubernetes/pki/etcd/ca.crt \
    --cert=/etc/kubernetes/pki/etcd/server.crt \
    --key=/etc/kubernetes/pki/etcd/server.key

# Restore
sudo ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-20260120.db \
    --data-dir=/var/lib/etcd-restore
```

---

## Monitoring and Observability

```bash
# Check component health
kubectl get componentstatuses
kubectl get pods -n kube-system -o wide

# View logs
sudo journalctl -u kubelet -f
kubectl logs -n kube-system <pod-name>

# Check certificates expiry
sudo kubeadm certs check-expiration

# Audit logs
sudo tail -f /var/log/kubernetes/audit.log | jq .
```

---

## Next 3 Steps

1. **Deploy monitoring stack**: Prometheus Operator + Grafana for control plane metrics (`kubectl create ns monitoring; helm install ...`)
2. **Implement RBAC policies**: Create least-privilege service accounts for workloads, test with `kubectl auth can-i`
3. **Join worker nodes**: Use saved join command, verify network policies prevent unauthorized pod-to-pod communication

---

## References

- Kubernetes Official Docs: https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/
- CIS Kubernetes Benchmark: https://www.cisecurity.org/benchmark/kubernetes
- Calico Security: https://docs.tigera.io/calico/latest/network-policy/
- etcd Encryption: https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/
- NIST SP 800-190: Application Container Security Guide