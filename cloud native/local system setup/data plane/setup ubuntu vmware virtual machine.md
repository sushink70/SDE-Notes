# Setting up a Secure Kubernetes Data Plane on Ubuntu VM

# Summary: Production-Grade Kubernetes Data Plane (Worker Node) Setup

You're correct—I included containerd in control plane because **kubelet on control plane also needs a container runtime** to run static pods (kube-apiserver, etcd, etc.) and system pods (CoreDNS, Cilium agent). **Every node in k8s cluster (control plane + workers) runs kubelet + container runtime**. Now for data plane: worker-01 gets containerd, kubelet, and joins the cluster. We'll harden kubelet, configure resource limits for your 16GB RAM, enable seccomp/AppArmor, verify Cilium datapath, and test pod scheduling. This node will run your actual workloads (Flask, Django, FastAPI).

---

## Architecture Reminder: Why Control Plane Needs Container Runtime

```
Control Plane Components:
├─ Static Pods (run by kubelet via containerd):
│   ├─ kube-apiserver (container)
│   ├─ kube-controller-manager (container)
│   ├─ kube-scheduler (container)
│   └─ etcd (container)
├─ DaemonSet Pods (scheduled by k8s):
│   ├─ Cilium agent (container)
│   └─ CoreDNS (container)

Worker Node Components:
├─ No static pods
├─ DaemonSet Pods:
│   └─ Cilium agent (container)
├─ User Workloads (your apps):
    ├─ Flask pod (container)
    ├─ Django pod (container)
    └─ FastAPI pod (container)
```

**Key Point**: Kubelet on control plane uses containerd to start API server, scheduler, etc. as containers. Worker nodes only run user workloads + system DaemonSets.

---

## Data Plane Node: Installation & Configuration

### Prerequisites & System Preparation

```bash
# On worker-01 VM (Ubuntu 22.04/24.04, 16GB RAM)
# Set hostname
sudo hostnamectl set-hostname worker-01

# Update /etc/hosts with static IPs
sudo tee -a /etc/hosts <<EOF
10.0.0.10 control-plane
10.0.0.20 worker-01
EOF

# Disable swap
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Verify swap is off
free -h | grep -i swap
# Should show 0B total

# Load kernel modules
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# Configure sysctl
sudo tee /etc/sysctl.d/k8s.conf <<EOF
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system

# Verify
lsmod | grep -E 'overlay|br_netfilter'
sysctl net.bridge.bridge-nf-call-iptables net.ipv4.ip_forward
```

---

### Install Container Runtime (containerd)

```bash
# Install containerd (same steps as control plane)
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

# Generate and configure containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Enable systemd cgroup driver (CRITICAL for kubelet)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# Restart containerd
sudo systemctl restart containerd
sudo systemctl enable containerd
sudo systemctl status containerd
```

**Security Hardening**:
```bash
# Restrict socket permissions
sudo chmod 660 /run/containerd/containerd.sock
sudo chown root:root /run/containerd/containerd.sock

# Verify
ls -la /run/containerd/containerd.sock
# Expected: srw-rw---- 1 root root
```

---

### Install Kubernetes Components

```bash
# Install kubeadm, kubelet, kubectl
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

# Verify versions match control plane
kubeadm version
kubelet --version
```

---

### Join Worker to Cluster

```bash
# On CONTROL PLANE: Get join command (if you lost it)
kubeadm token create --print-join-command

# Example output:
# kubeadm join 10.0.0.10:6443 --token abc123.xyz456 \
#   --discovery-token-ca-cert-hash sha256:deadbeef...

# On WORKER NODE: Run the join command
sudo kubeadm join 10.0.0.10:6443 \
  --token <your-token> \
  --discovery-token-ca-cert-hash sha256:<your-hash>

# Expected output:
# [preflight] Running pre-flight checks
# [kubelet-start] Writing kubelet configuration to file
# [kubelet-start] Starting the kubelet
# This node has joined the cluster:
# * Certificate signing request was sent to apiserver and a response was received.
# * The Kubelet was informed of the new secure connection details.
```

**Verify Join from Control Plane**:
```bash
# On control-plane
kubectl get nodes
# Expected:
# NAME            STATUS   ROLES           AGE   VERSION
# control-plane   Ready    control-plane   30m   v1.31.x
# worker-01       Ready    <none>          1m    v1.31.x

# Wait for Cilium agent to start on worker
kubectl get pods -n kube-system -o wide | grep worker-01
# Expected: cilium-xxxxx running on worker-01
```

---

### Configure Kubelet for Worker Node Hardening

```bash
# On worker-01: Create kubelet config drop-in
sudo mkdir -p /etc/systemd/system/kubelet.service.d

# Configure kubelet security flags
sudo tee /etc/systemd/system/kubelet.service.d/20-hardening.conf <<EOF
[Service]
Environment="KUBELET_EXTRA_ARGS=--protect-kernel-defaults=true --event-qps=5 --read-only-port=0"
EOF

# Reload and restart kubelet
sudo systemctl daemon-reload
sudo systemctl restart kubelet
sudo systemctl status kubelet

# Verify kubelet is running
sudo journalctl -u kubelet -f
```

**Security Context**:
- `--protect-kernel-defaults=true`: Ensures kernel tuning matches kubelet expectations (prevents drift)
- `--read-only-port=0`: Disables insecure read-only port 10255
- `--event-qps=5`: Rate-limits event spam (DoS mitigation)

---

### Resource Allocation for 16GB Worker Node

```bash
# Reserve resources for system daemons (kubelet, containerd, OS)
# For 16GB RAM worker running light workloads:
# - System reserve: 1GB
# - Kubelet reserve: 500MB
# - Eviction threshold: 500MB
# - Allocatable for pods: ~14GB

# Create kubelet config for resource management
sudo tee /var/lib/kubelet/config.yaml <<EOF
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
systemReserved:
  cpu: "500m"
  memory: "1Gi"
  ephemeral-storage: "1Gi"
kubeReserved:
  cpu: "200m"
  memory: "512Mi"
  ephemeral-storage: "1Gi"
evictionHard:
  memory.available: "500Mi"
  nodefs.available: "10%"
  imagefs.available: "15%"
evictionSoft:
  memory.available: "1Gi"
  nodefs.available: "15%"
evictionSoftGracePeriod:
  memory.available: "1m30s"
  nodefs.available: "2m"
maxPods: 110
EOF

# Restart kubelet to apply config
sudo systemctl restart kubelet

# Verify allocatable resources from control-plane
kubectl describe node worker-01 | grep -A 10 "Allocatable:"
# Should show ~14GB memory, ~3.3 CPU cores
```

---

### Enable Security Profiles (seccomp, AppArmor)

```bash
# Verify seccomp support
grep SECCOMP /boot/config-$(uname -r)
# Expected: CONFIG_SECCOMP=y

# Verify AppArmor is active
sudo aa-status
# Expected: apparmor module is loaded

# Create custom seccomp profile directory
sudo mkdir -p /var/lib/kubelet/seccomp/profiles

# Example: restrictive seccomp profile for web apps
sudo tee /var/lib/kubelet/seccomp/profiles/web-app.json <<'EOF'
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "arch_prctl", "bind", "brk",
        "capget", "capset", "chdir", "chmod", "chown", "clock_gettime",
        "clone", "close", "connect", "dup", "dup2", "epoll_create",
        "epoll_ctl", "epoll_wait", "execve", "exit", "exit_group",
        "fcntl", "fstat", "futex", "getcwd", "getdents", "getegid",
        "geteuid", "getgid", "getpid", "getppid", "getrlimit", "getsockname",
        "getsockopt", "gettid", "getuid", "ioctl", "listen", "lseek",
        "madvise", "mmap", "mprotect", "munmap", "nanosleep", "open",
        "openat", "pipe", "poll", "prctl", "pread64", "prlimit64",
        "read", "readlink", "recvfrom", "recvmsg", "rt_sigaction",
        "rt_sigprocmask", "rt_sigreturn", "sched_getaffinity", "sched_yield",
        "sendmsg", "sendto", "set_robust_list", "set_tid_address",
        "setgid", "setgroups", "setsockopt", "setuid", "shutdown",
        "sigaltstack", "socket", "stat", "statfs", "tgkill", "uname",
        "wait4", "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
EOF

# Verify profile is valid JSON
sudo cat /var/lib/kubelet/seccomp/profiles/web-app.json | jq .
```

---

## Verification & Testing

### 1. Node Health Check
```bash
# From control-plane
kubectl get nodes -o wide
# Both nodes should be Ready

kubectl describe node worker-01
# Check Conditions, Allocatable resources, Taints

# Verify Cilium connectivity
cilium status
cilium connectivity test  # Run full L3/L4/L7 connectivity test (10-15 min)
```

### 2. Deploy Test Pod on Worker
```bash
# Create test deployment (nginx)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nginx-test
  namespace: default
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.25-alpine
    ports:
    - containerPort: 80
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
    securityContext:
      runAsNonRoot: true
      runAsUser: 101
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
      seccompProfile:
        type: RuntimeDefault
EOF

# Wait for pod to run
kubectl wait --for=condition=Ready pod/nginx-test --timeout=60s

# Verify pod is on worker-01
kubectl get pod nginx-test -o wide
# NODE column should show worker-01

# Check pod logs
kubectl logs nginx-test

# Test pod network connectivity
kubectl exec nginx-test -- wget -qO- http://kubernetes.default.svc.cluster.local
# Should return HTML from API server health endpoint
```

### 3. Test DNS Resolution
```bash
# Create debug pod
kubectl run debug --image=busybox:1.36 --rm -it --restart=Never -- sh

# Inside pod:
nslookup kubernetes.default
nslookup nginx-test.default.svc.cluster.local
wget -qO- http://nginx-test
exit
```

### 4. Verify Cilium Datapath
```bash
# Check eBPF maps loaded on worker
kubectl exec -n kube-system ds/cilium -- cilium bpf endpoint list

# Verify NetworkPolicy enforcement
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-nginx-ingress
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: nginx
  policyTypes:
  - Ingress
  ingress: []  # Deny all ingress
EOF

# Test connectivity should fail
kubectl run test-client --image=busybox:1.36 --rm -it --restart=Never -- \
  wget --timeout=5 -qO- http://nginx-test
# Expected: timeout (connection blocked by NetworkPolicy)

# Delete policy
kubectl delete networkpolicy deny-nginx-ingress
```

### 5. Resource Limit Enforcement
```bash
# Deploy memory-bomb pod to test eviction
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: memory-bomb
spec:
  containers:
  - name: stress
    image: polinux/stress:1.0.4
    resources:
      requests:
        memory: "100Mi"
      limits:
        memory: "200Mi"
    command: ["stress"]
    args: ["--vm", "1", "--vm-bytes", "500M", "--vm-hang", "1"]
EOF

# Pod should fail to start or be OOMKilled
kubectl get pod memory-bomb
kubectl describe pod memory-bomb | grep -A 5 "State:"

# Cleanup
kubectl delete pod memory-bomb nginx-test
```

---

## Threat Model & Mitigations (Data Plane Specific)

| Threat | Impact | Mitigation |
|--------|--------|------------|
| **Container escape to host** | Node compromise, lateral movement | seccomp profiles, AppArmor, drop all capabilities, runAsNonRoot |
| **Kubelet API unauthorized access** | Pod exec/logs access, secret theft | Kubelet authn/authz, NodeRestriction, --read-only-port=0 |
| **Pod resource exhaustion (CPU/memory)** | Node crash, DoS for other pods | Resource requests/limits, eviction thresholds, kubelet QoS |
| **Malicious pod network traffic** | C2 communication, data exfil | Cilium L3/L7 NetworkPolicies, default-deny posture, DNS policies |
| **Privilege escalation via hostPath** | Mount host filesystem | PodSecurity admission (blocks hostPath in baseline/restricted) |
| **Runtime vulnerability (containerd CVE)** | Container escape | Regular patching, minimal attack surface, read-only rootfs |

---

## Performance Tuning for Light Workloads

```bash
# Optimize containerd for low latency
sudo tee -a /etc/containerd/config.toml <<EOF

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  SystemdCgroup = true
  # Reduce CPU overhead for light workloads
  NoPivotRoot = false
  NoNewKeyring = false
EOF

sudo systemctl restart containerd

# Monitor resource usage
# Install metrics-server (on control-plane, later)
kubectl top nodes  # Requires metrics-server
kubectl top pods -A
```

---

## Rollback Plan

```bash
# On worker-01: Leave cluster and reset
sudo kubeadm reset -f
sudo rm -rf /etc/cni/net.d
sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F && sudo iptables -X
sudo rm -rf /var/lib/cilium

# On control-plane: Remove node from cluster
kubectl delete node worker-01

# Re-join by running kubeadm join command again
```

---

## Failure Mode Analysis

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| **Kubelet crash** | `systemctl status kubelet` shows failed | `journalctl -u kubelet`, fix config, restart |
| **Containerd crash** | Pods stuck in ContainerCreating | `journalctl -u containerd`, check OOM, restart |
| **CNI plugin failure** | Pods can't schedule, no IP assigned | `cilium status`, check eBPF maps, reinstall Cilium |
| **Out of memory** | Node shows MemoryPressure | `kubectl describe node`, increase eviction thresholds |
| **Disk pressure** | Node shows DiskPressure | Clean image cache: `crictl rmi --prune` |
| **Network partition** | Node shows NotReady | Verify 10.0.0.10:6443 reachable, check iptables |

---

## Next 3 Steps

1. **Deploy Your Microservices**:
   ```bash
   # Create namespaces for isolation
   kubectl create namespace flask-apps
   kubectl create namespace django-app
   kubectl create namespace fastapi-app
   
   # Label for NetworkPolicy scoping
   kubectl label namespace flask-apps environment=dev
   ```

2. **Install Metrics & Observability**:
   ```bash
   # Metrics-server for resource monitoring
   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
   
   # Enable Hubble UI for network observability
   cilium hubble enable --ui
   kubectl port-forward -n kube-system svc/hubble-ui 12000:80
   # Access at http://localhost:12000
   ```

3. **Build Production Deployment Manifests** for Flask/Django/FastAPI with:
   - Resource limits (based on 14GB allocatable / 4 pods = ~3GB per pod max)
   - NetworkPolicies (default-deny, then allow specific ingress)
   - seccomp profiles (`localhost/web-app.json`)
   - ReadOnlyRootFilesystem where possible

---

## References

- [kubeadm join reference](https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm-join/)
- [Kubelet Configuration](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/)
- [Node Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Seccomp in Kubernetes](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [Cilium Network Policies](https://docs.cilium.io/en/stable/security/policy/)

**Worker node is production-ready**. Proceed with deploying your microservices.

