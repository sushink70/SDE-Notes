# Kubernetes and Docker: Architecture and Integration Concepts

## Understanding the Relationship

Kubernetes and Docker have an intertwined history, though their relationship has evolved significantly. Docker popularized containerization, while Kubernetes emerged as the leading container orchestration platform. Understanding how they work together requires grasping both their individual roles and their integration points.

## Core Concepts

### Containerization Foundation

Docker introduced the concept of lightweight, portable containers that package applications with their dependencies. Containers share the host OS kernel but run in isolated user spaces, making them much more efficient than virtual machines. This container image format became an industry standard that Kubernetes was built to orchestrate.

### Kubernetes' Original Docker Dependency

Initially, Kubernetes was tightly coupled with Docker as its container runtime. Kubernetes would communicate with the Docker daemon to create, start, stop, and manage containers. This made Docker both a development tool and a production runtime.

### The Runtime Evolution (CRI)

Kubernetes introduced the Container Runtime Interface (CRI) to decouple itself from any specific container runtime. This architectural decision allowed Kubernetes to work with multiple container runtimes, not just Docker. The CRI defines a standard API that any container runtime can implement.

## Architectural Layers

### The Container Runtime Hierarchy

**High-level runtimes** like Docker and containerd provide user-friendly interfaces, image management, and networking capabilities. **Low-level runtimes** like runc actually create and run the containers according to OCI (Open Container Initiative) specifications.

Docker itself is actually a stack: the Docker CLI communicates with dockerd (the Docker daemon), which uses containerd as its runtime, which in turn uses runc to actually spawn containers.

### How Kubernetes Sits Above

Kubernetes operates at the orchestration layer, managing where containers run, how many instances exist, networking between them, storage, and lifecycle management. It doesn't care about the specifics of containerization itself—it delegates that to the container runtime through the CRI.

## Key Integration Points

### Image Management

Docker excels at building container images through Dockerfiles. Developers use Docker to create, test, and push images to container registries. Kubernetes then pulls these same images from registries to deploy containers across its cluster. The image format is standardized (OCI), so images built with Docker work seamlessly with Kubernetes regardless of the underlying runtime.

### The kubelet and Container Runtime

On each Kubernetes node, the kubelet agent is responsible for ensuring containers are running as specified. The kubelet communicates with the container runtime (whether that's Docker via dockershim historically, containerd, or CRI-O) to actually create and manage containers based on pod specifications.

### Dockershim Deprecation

Kubernetes deprecated and removed dockershim (the component that allowed Kubernetes to talk to Docker) because Docker itself isn't CRI-compliant. Docker was designed as a complete platform, not just a runtime. Kubernetes now prefers to talk directly to containerd (which Docker uses internally anyway), eliminating the middle layer and improving efficiency.

## Workflow Understanding

### Development to Production Flow

Developers typically use Docker locally to build and test containers. They write Dockerfiles that define how to build images, use Docker Compose for local multi-container applications, and validate their work. Once ready, they push images to a container registry.

In production, Kubernetes pulls these images and orchestrates them at scale. The same container images work identically because of standardization, but Kubernetes adds scheduling, scaling, self-healing, service discovery, and load balancing capabilities that Docker alone doesn't provide.

### Pod Architecture

Kubernetes' fundamental unit is the pod, not the container. A pod can contain one or multiple containers that share networking and storage namespaces. These containers can be built with Docker but are run by whatever container runtime Kubernetes is configured to use. Containers within a pod can communicate via localhost and share mounted volumes.

## Networking Concepts

### Container Networking Model

Docker has its own networking model with bridge networks, host networks, and overlay networks. Kubernetes has its own networking requirements: every pod gets its own IP address, and all pods can communicate with each other without NAT.

When Kubernetes uses a container runtime, it typically bypasses the runtime's networking and uses CNI (Container Network Interface) plugins instead. These plugins handle pod networking according to Kubernetes' requirements. Docker networks become less relevant in Kubernetes clusters.

### Service Discovery and Load Balancing

Docker Compose provides basic service discovery for local development. Kubernetes Services provide production-grade load balancing, service discovery through DNS, and multiple service types (ClusterIP, NodePort, LoadBalancer). This is where Kubernetes significantly extends beyond what Docker alone offers.

## Storage Integration

### Volume Management

Docker has volume concepts for persisting data beyond container lifecycles. Kubernetes abstracts this further with Persistent Volumes (PV) and Persistent Volume Claims (PVC), allowing storage to be provisioned dynamically and managed independently of pod lifecycles.

Container runtimes handle the actual mounting of volumes into containers, but Kubernetes orchestrates which volumes get mounted where and manages their lifecycle across pod restarts and rescheduling.

## Scheduling and Resource Management

### Docker's Limitations

Docker can run containers and impose resource limits (CPU, memory) on individual containers. However, it doesn't decide where to run containers in a cluster, how to distribute load, or how to handle failures.

### Kubernetes Scheduler

The Kubernetes scheduler examines pod requirements (resource requests, affinity rules, taints and tolerations) and cluster state to decide which node should run each pod. The container runtime then creates the containers on that node. This separation of concerns means scheduling logic is independent of container execution.

## Practical Realities Today

### Current Best Practices

Most Kubernetes distributions now use containerd or CRI-O directly rather than Docker. Developers still use Docker for building images and local testing because of its excellent developer experience. The images created with Docker work perfectly in Kubernetes clusters using different runtimes.

### The Mental Model Shift

Think of Docker as your development toolkit and image builder, while Kubernetes is your production orchestration platform. They share the container image format standard but serve different purposes in the application lifecycle. You build with Docker, deploy with Kubernetes.

## Configuration and Declarative Management

### Docker's Imperative Approach

Docker and Docker Compose work primarily through imperative commands and relatively simple YAML files that directly map to containers and networks.

### Kubernetes' Declarative Model

Kubernetes embraces declarative configuration where you describe the desired state (deployments, services, ingresses) and Kubernetes continuously works to achieve and maintain that state. This includes self-healing, rolling updates, and automated rollbacks—capabilities far beyond Docker's scope.

## Security Boundaries

### Isolation Layers

Container runtimes provide the fundamental isolation between containers using Linux namespaces, cgroups, and capabilities. Kubernetes adds additional security layers through pod security policies, network policies, RBAC (role-based access control), and secrets management.

### Image Security

Docker images can contain vulnerabilities. Kubernetes can integrate with image scanning tools and admission controllers to enforce security policies, preventing vulnerable images from being deployed. The runtime executes the container, but Kubernetes controls what gets executed.

This architectural understanding reveals that Kubernetes and Docker are complementary rather than competing technologies, each excelling in their respective domains of the container ecosystem.

# Kubernetes Networking Stack: A Deep Dive

## The Fundamental Networking Challenge

Kubernetes networking is one of its most complex aspects because it must satisfy multiple requirements simultaneously while working across different container runtimes and infrastructure providers. Understanding the stack requires seeing how multiple layers interact.

## The Networking Requirements

### Kubernetes' Four Networking Rules

Kubernetes imposes four fundamental networking requirements that shape the entire stack:

**All pods can communicate with all other pods** without NAT, across any node in the cluster. This flat network model differs dramatically from traditional Docker networking where containers on different hosts can't communicate without explicit configuration.

**All nodes can communicate with all pods** without NAT, allowing the kubelet and other system components to reach any pod.

**The IP address a pod sees for itself** is the same IP address others see when communicating with it—no network address translation confusion.

**Services get stable virtual IPs** that load balance across pod endpoints, even as pods are created and destroyed.

## The Container Runtime Network Layer

### Docker's Network Model (for context)

Docker creates a virtual bridge (docker0) on the host. Each container gets a virtual ethernet pair—one end in the container's network namespace, one end on the bridge. Containers get private IP addresses in a subnet (typically 172.17.0.0/16), and Docker uses iptables NAT rules for external communication.

This works fine for a single host, but breaks down in multi-host scenarios. Docker Swarm and overlay networks attempt to solve this, but they're Docker-specific solutions.

### How Kubernetes Bypasses Runtime Networking

When Kubernetes uses a container runtime, it typically ignores the runtime's networking completely. Instead, Kubernetes creates containers in "none" network mode, meaning the container starts with only a loopback interface. Kubernetes then takes full control of setting up the network.

## The CNI Plugin Architecture

### Container Network Interface (CNI)

CNI is a specification that defines how network plugins should configure container networking. When Kubernetes needs to set up networking for a pod, the kubelet calls the configured CNI plugin with standardized parameters.

The CNI plugin is responsible for:
- Creating a network interface in the pod's network namespace
- Assigning an IP address to the pod
- Setting up routes so the pod can reach other pods and services
- Configuring any necessary network policies

### CNI Plugin Execution Flow

When a pod is scheduled to a node, the kubelet calls the CNI plugin with an "ADD" command. The plugin runs (as a binary executable), configures the networking, and returns the results (including the assigned IP address) to the kubelet. When the pod is deleted, the kubelet calls the plugin with a "DEL" command to clean up.

## Popular CNI Plugin Approaches

### Overlay Networks (Flannel, Weave)

Overlay networks create a virtual network on top of the existing infrastructure network. Each node runs an agent that encapsulates pod traffic in UDP or VXLAN packets.

When a pod on Node A sends traffic to a pod on Node B, the packet travels through the pod's virtual ethernet interface to the node's overlay agent. The agent wraps the packet (with the pod IPs) inside another packet (with the node IPs), sends it over the physical network, and the receiving node's agent unwraps it and delivers it to the destination pod.

This approach works on any infrastructure but adds encapsulation overhead. The pod network and host network are completely separate address spaces.

### Direct Routing (Calico in BGP mode)

Direct routing approaches program actual routes into the infrastructure. Each node advertises routes to its pod CIDR range using BGP (Border Gateway Protocol) or by programming cloud provider route tables.

When a pod sends traffic to another pod, the packet goes to the host's routing table, which knows exactly which node hosts that pod IP and routes directly there—no encapsulation overhead. The pod IPs must be routable in the infrastructure, requiring infrastructure support.

### Host-Local Networking (Calico in VXLAN mode, AWS VPC CNI)

Some CNI plugins allocate pod IPs from the same subnet as the nodes or integrate deeply with cloud provider networking. The AWS VPC CNI, for example, allocates actual AWS Elastic Network Interface IPs to pods, making them first-class citizens in the VPC.

This provides excellent performance and simplifies network policies but ties you to specific infrastructure capabilities.

## The Pod Network Namespace

### Network Namespace Fundamentals

Linux network namespaces provide isolated network stacks. Each pod gets its own network namespace with its own network interfaces, routing tables, and iptables rules.

### The Pause Container

Every Kubernetes pod starts with a special "pause" container (also called the infrastructure container). This container does almost nothing—it just sleeps. However, it creates and holds the pod's network namespace.

All other containers in the pod join this network namespace, which is why they share the same IP address and can communicate via localhost. If the main application container crashes and restarts, it rejoins the same network namespace maintained by the pause container, keeping the pod's network identity stable.

### Virtual Ethernet Pairs (veth)

The CNI plugin creates a virtual ethernet pair for each pod—like a virtual cable with two ends. One end goes into the pod's network namespace and becomes eth0. The other end stays in the host's network namespace, typically connected to a bridge or directly routed.

Traffic flowing out of the pod goes through eth0, crosses the veth pair to the host side, and then follows the host's routing rules to reach its destination.

## The Node Network Layer

### The Linux Bridge Approach

Some CNI plugins create a Linux bridge (like cbr0 or cni0) on each node. All pod veth interfaces on that node connect to this bridge. The bridge has an IP address in the node's pod CIDR range and acts as the default gateway for all pods on that node.

When a pod sends traffic to another pod on the same node, it goes through the bridge directly. When sending to a pod on another node, it goes through the bridge to the host's routing table.

### Direct Routing to Pods

Other CNI plugins skip the bridge entirely and add individual routes in the host routing table for each pod. This is more efficient but requires more routing table entries.

## Inter-Node Communication

### Route Propagation

For pods on different nodes to communicate, each node must know how to reach every pod CIDR range. This happens through:

**Static route configuration** where you manually configure routes (doesn't scale).

**BGP route advertisement** where nodes run BGP daemons and advertise routes to each other.

**Cloud provider route tables** where the CNI plugin programs routes into AWS, GCP, or Azure route tables.

**Overlay encapsulation** where routes aren't needed because traffic is tunneled.

### The Encapsulation Decision

The choice between overlay and direct routing involves tradeoffs. Overlays work everywhere but add overhead and make debugging harder because the actual packet structure is hidden. Direct routing is faster and clearer but requires infrastructure support and careful IP management.

## Service Networking and kube-proxy

### The Service Abstraction Problem

Pods are ephemeral—they get IP addresses when created and lose them when deleted. Applications need stable endpoints. Kubernetes Services provide stable virtual IPs (ClusterIPs) that load balance across pod endpoints.

### kube-proxy's Role

The kube-proxy component runs on every node and implements the Service abstraction. It watches the Kubernetes API for Service and Endpoints changes and programs the node's networking accordingly.

Despite its name, kube-proxy usually doesn't actually proxy traffic—that would be too slow.

### iptables Mode (Traditional)

In iptables mode, kube-proxy programs iptables rules that perform DNAT (Destination NAT). When traffic is sent to a Service's ClusterIP, iptables rules randomly select one of the backend pod IPs and rewrite the destination address.

For a Service with three pods, there might be rules that send 33% of traffic to each pod IP. This happens entirely in the kernel, so it's fast, but iptables doesn't scale well beyond thousands of services.

### IPVS Mode (Modern)

IPVS (IP Virtual Server) is a kernel-level load balancer designed for this exact use case. In IPVS mode, kube-proxy creates IPVS virtual servers for each Service ClusterIP and adds the pod IPs as real servers behind it.

IPVS supports multiple load-balancing algorithms (round-robin, least connection, etc.) and scales much better than iptables. It uses a hash table internally rather than linear rule evaluation.

### Connection Tracking

Both modes rely on conntrack (connection tracking) in the kernel. When a packet arrives at a Service IP, it gets rewritten to a specific pod IP. The kernel remembers this connection, so all subsequent packets in that connection go to the same pod (session affinity).

Return traffic is automatically un-NATed so the pod's response appears to come from the Service IP.

## DNS and Service Discovery

### CoreDNS Integration

Kubernetes runs CoreDNS as a cluster add-on. It watches the Kubernetes API for Services and creates DNS records automatically.

When a pod needs to contact a Service, it does a DNS lookup for the service name. CoreDNS returns the Service's ClusterIP. The pod sends traffic to that IP, and kube-proxy's iptables or IPVS rules direct it to a backend pod.

### Pod DNS Configuration

Every pod's /etc/resolv.conf is configured to use CoreDNS as its nameserver. The kubelet generates this configuration when creating the pod, pointing to the ClusterIP of the kube-dns Service.

### Search Domains

Pods get DNS search domains based on their namespace, allowing short names. A pod in the "default" namespace can reference "myservice" and it expands to "myservice.default.svc.cluster.local".

## Network Policies

### The CNI Plugin Enforcement

Not all CNI plugins support NetworkPolicies. Those that do (like Calico, Cilium, Weave) watch the Kubernetes API for NetworkPolicy objects and enforce them using iptables rules or more sophisticated mechanisms.

### How Enforcement Works

When you create a NetworkPolicy that says "pods with label app=frontend can only receive traffic from pods with label app=backend," the CNI plugin programs rules on every node.

For iptables-based enforcement, it creates chains that match traffic based on source IP addresses (which map to pod labels), destination ports, and protocols. Traffic that doesn't match the policy gets dropped.

### Calico's Advanced Approach

Calico can enforce policies using iptables but also supports eBPF (extended Berkeley Packet Filter) for much better performance. eBPF enforcement happens earlier in the packet processing pipeline and avoids iptables' scalability issues.

## Ingress and Load Balancing

### External Traffic Reaching Services

Services of type LoadBalancer get external IPs provisioned by the cloud provider. Traffic hits the cloud load balancer, which forwards to node IPs.

### NodePort and External Traffic Policy

Services can expose a port on every node (NodePort). External traffic arrives at any node on this port, and kube-proxy's rules forward it to a backend pod—potentially on a different node.

The ExternalTrafficPolicy setting controls this. "Cluster" mode allows cross-node forwarding, which can be inefficient. "Local" mode only forwards to pods on the receiving node, preserving source IP but requiring careful load balancer configuration.

### Ingress Controllers

Ingress controllers (like nginx-ingress, Traefik, or Istio Gateway) are specialized reverse proxies that run as pods. They watch Ingress resources and configure themselves accordingly.

Traffic flows: External client → LoadBalancer → Ingress controller pod → Application pod. The Ingress controller makes routing decisions based on HTTP host headers and paths, then forwards traffic to the appropriate Service ClusterIP, where kube-proxy takes over.

## Service Mesh Networking

### Sidecar Proxies

Service meshes like Istio and Linkerd inject sidecar proxy containers into every pod. All traffic to and from the pod is intercepted by the sidecar.

### iptables Redirection

The service mesh's init container programs iptables rules in the pod's network namespace to redirect all outbound traffic to the sidecar proxy (typically listening on port 15001) and all inbound traffic through another sidecar port.

The application container thinks it's talking directly to other services, but the sidecar intercepts everything, enabling mTLS, retries, circuit breaking, and detailed metrics.

### Envoy as Data Plane

Most service meshes use Envoy as the sidecar proxy. Envoy maintains its own understanding of the service topology (updated by the control plane like Istio's Pilot) and makes intelligent routing decisions that are more sophisticated than kube-proxy's simple load balancing.

## IPv6 and Dual-Stack

### Dual-Stack Networking

Modern Kubernetes supports running IPv4 and IPv6 simultaneously. Pods can get both IPv4 and IPv6 addresses, and Services can have both types of ClusterIPs.

The CNI plugin must support dual-stack and assign both address families. Applications can then use whichever they prefer, with DNS returning both A and AAAA records.

## The Complete Packet Journey

### Example: Pod A to Pod B on Different Nodes

Pod A (10.244.1.5 on Node 1) sends a packet to Pod B (10.244.2.7 on Node 2):

The packet leaves Pod A's eth0, which is one end of a veth pair. It crosses to the host side of the veth pair in Node 1's network namespace. Node 1's routing table has a route for 10.244.2.0/24 pointing to Node 2 (either directly or via encapsulation). The packet is sent to Node 2 (possibly encapsulated in VXLAN). Node 2 receives it, decapsulates if necessary, and its routing table shows 10.244.2.7 is on the local bridge or via a specific veth interface. The packet crosses the veth pair into Pod B's network namespace and arrives at Pod B's eth0.

Throughout this journey, no NAT occurs—the source and destination IPs remain 10.244.1.5 and 10.244.2.7.

### Example: Pod to Service to Backend Pod

Pod A sends to Service S (ClusterIP 10.96.0.10). The packet leaves Pod A and arrives at Node 1's network stack. iptables or IPVS rules match the destination 10.96.0.10 and rewrite it to one of the backend pod IPs (say 10.244.3.8). The kernel's connection tracking remembers this mapping. The packet is now routed as a normal pod-to-pod packet to Node 3. Pod B (10.244.3.8) receives the packet, processes it, and sends a response back to 10.244.1.5. When the response reaches Node 1, conntrack recognizes the connection and rewrites the source IP from 10.244.3.8 to 10.96.0.10. Pod A receives the response appearing to come from the Service IP.

## Performance Considerations

### Latency Sources

Every network hop adds latency. Overlay encapsulation requires CPU cycles for wrapping and unwrapping. iptables rules are evaluated linearly, slowing down with thousands of Services. Network Policy enforcement adds rule evaluation overhead.

### Optimization Strategies

Using IPVS instead of iptables improves Service routing. eBPF-based CNI plugins like Cilium process packets in the kernel more efficiently. Direct routing avoids encapsulation overhead. Careful pod placement can minimize cross-node traffic.

## Troubleshooting the Stack

### Common Issues

Pods can't reach each other usually means CNI plugin issues or routes not propagated. Pods can't reach Services suggests kube-proxy isn't running or misconfigured. External traffic can't reach Services indicates LoadBalancer or Ingress problems. DNS doesn't resolve points to CoreDNS issues or /etc/resolv.conf misconfiguration.

### Debugging Tools

Use kubectl exec to get into pods and run ping, curl, or traceroute. Check iptables rules with iptables-save to see Service mappings. Examine routing tables with ip route on nodes. Inspect CNI plugin logs for configuration errors. Use tcpdump on both pod and host interfaces to see where packets are going.

The Kubernetes networking stack is incredibly sophisticated, coordinating multiple technologies to create the illusion of a simple, flat network while providing powerful features like service discovery, load balancing, and network policies. Understanding each layer and how they interact is key to operating Kubernetes successfully.

# Cloud Native Ecosystem: Architecture and Integration

## The Cloud Native Landscape

The cloud native ecosystem is a vast collection of projects and tools that extend, enhance, or complement Kubernetes. Understanding how they fit together requires seeing the broader architecture of modern cloud native systems.

## What "Cloud Native" Actually Means

### The Philosophy

Cloud native represents a fundamentally different approach to building and running applications. Instead of monolithic applications running on long-lived servers, cloud native emphasizes microservices, containers, dynamic orchestration, and declarative APIs. Applications are designed to expect failure, scale horizontally, and update without downtime.

### The CNCF's Role

The Cloud Native Computing Foundation (CNCF) serves as the neutral home for cloud native projects. It provides governance, community building, and a maturity framework (Sandbox → Incubating → Graduated) that signals a project's production readiness and adoption level.

The CNCF landscape includes hundreds of projects across different categories, forming layers that build upon each other.

## The Foundation Layer: Container Runtime and Orchestration

### containerd and CRI-O

These are lightweight, focused container runtimes that implement the CRI specification. While Docker provides a complete development platform, containerd and CRI-O focus specifically on running containers in production environments under Kubernetes.

**containerd** was extracted from Docker and donated to CNCF. It handles image transfer and storage, container execution and supervision, and low-level storage and network attachments. Major cloud providers use containerd as their default runtime because it's efficient and well-maintained.

**CRI-O** was built specifically for Kubernetes, implementing exactly what CRI requires and nothing more. It's particularly popular in Red Hat's OpenShift. The minimalist approach reduces attack surface and resource overhead.

### runc and Alternative Low-Level Runtimes

**runc** is the actual executor that creates containers according to OCI specifications. Both containerd and CRI-O use runc underneath.

Alternative runtimes like **gVisor** and **Kata Containers** provide stronger isolation. gVisor runs containers in a user-space kernel, adding a security boundary. Kata Containers runs each container in a lightweight VM, providing VM-level isolation with container-like speed. These integrate with Kubernetes through the CRI, allowing you to mix different isolation levels in the same cluster.

## Service Mesh Layer

### Istio Architecture

Istio is the most comprehensive service mesh. It consists of a control plane (istiod) and a data plane (Envoy sidecars).

**The control plane** discovers services, converts high-level routing rules into Envoy configurations, distributes these configurations to all proxies, and manages certificate generation for mTLS. It runs as a deployment in the cluster, watching Kubernetes resources.

**The data plane** consists of Envoy proxies injected as sidecars into application pods. These proxies intercept all network traffic, enforce policies, collect telemetry, and implement advanced routing. They communicate with the control plane to get configuration updates but make traffic decisions locally.

### How Traffic Flows Through Istio

When Pod A calls Pod B, the request goes to Pod A's Envoy sidecar first. Envoy checks routing rules, selects a destination instance (potentially across multiple versions for canary deployments), establishes an mTLS connection to Pod B's Envoy, and forwards the request. Pod B's Envoy terminates mTLS, checks authorization policies, and forwards to the actual application container.

Both sidecars collect detailed metrics about latency, success rates, and traffic volumes, sending them to observability tools.

### Linkerd's Simplified Approach

Linkerd focuses on simplicity and performance. Instead of Envoy, it uses a custom Rust-based proxy that's smaller and faster. The architecture is similar—control plane and data plane—but configuration is simpler and resource overhead is lower.

Linkerd automatically encrypts all traffic between meshed pods, provides golden metrics (success rate, request rate, latency distribution), and implements retries and timeouts without complex configuration.

### Service Mesh Interface (SMI)

SMI is a specification attempting to standardize service mesh APIs. It defines common interfaces for traffic policies, telemetry, and traffic management. The goal is to allow applications to work with any SMI-compliant mesh, though adoption has been mixed as meshes have diverged in capabilities.

## Observability Stack

### Prometheus Architecture

Prometheus is the de facto monitoring system for Kubernetes. Its architecture is pull-based rather than push-based.

**The Prometheus server** periodically scrapes metrics from instrumented applications via HTTP endpoints. It stores these time-series metrics in an efficient local database and provides PromQL, a powerful query language for analyzing metrics.

**Service Discovery** integration allows Prometheus to automatically discover all pods, services, and nodes in the cluster. It reads Kubernetes API annotations to find what to scrape and at what interval.

**Exporters** expose metrics from systems that don't natively speak Prometheus format. The node-exporter runs on every node collecting hardware and OS metrics. Other exporters handle databases, message queues, and various infrastructure components.

### How Prometheus Integrates with Kubernetes

Applications expose metrics at /metrics endpoints in Prometheus format. Pods get annotated with prometheus.io/scrape: "true" and prometheus.io/port to indicate they should be scraped. Prometheus service discovery watches the Kubernetes API for these annotations and automatically adds the targets to its scraping configuration.

This dynamic discovery means new pods automatically get monitored without manual configuration changes.

### Grafana Visualization

Grafana connects to Prometheus as a data source and builds dashboards visualizing the metrics. It can query multiple Prometheus servers, combine data from different sources, and create alerts based on query results.

Grafana doesn't store data itself—it's purely a visualization and alerting layer. The separation of concerns allows you to scale storage and visualization independently.

### OpenTelemetry: The Unified Observability Framework

OpenTelemetry (OTel) is a massive initiative to standardize observability instrumentation. It provides SDKs for collecting traces, metrics, and logs from applications in a vendor-neutral format.

**Auto-instrumentation** allows you to add observability to applications without code changes. For example, the OTel Java agent can automatically instrument Spring Boot applications, capturing HTTP requests, database queries, and external API calls.

**The Collector** is a highly configurable agent that receives telemetry data, processes it (filtering, sampling, enriching), and exports it to various backends. You might collect traces and send them to Jaeger, collect metrics and send them to Prometheus, all through a single collector pipeline.

### Distributed Tracing with Jaeger

Jaeger implements distributed tracing, allowing you to follow a single request across multiple services.

When a request enters the system, the first service generates a trace ID and propagates it to downstream services via HTTP headers. Each service creates spans representing work it performs, associating them with the trace ID. These spans are sent to the Jaeger collector, which stores them in a database.

The Jaeger UI allows you to query traces, see the full request path, identify slow services, and understand dependencies. This is invaluable for debugging microservices where a single user request might touch dozens of services.

### The ELK/EFK Stack for Logging

**Elasticsearch** stores logs as searchable documents. **Logstash** or **Fluentd** collects logs from containers and ships them to Elasticsearch. **Kibana** provides a UI for searching and visualizing logs.

In Kubernetes, **Fluent Bit** (a lighter-weight log forwarder) typically runs as a DaemonSet, collecting logs from every node's container runtime. It enriches logs with Kubernetes metadata (pod name, namespace, labels) and forwards them to Elasticsearch or other backends.

### The Shift to Loki

Grafana Loki offers a simpler alternative to Elasticsearch. Instead of indexing log content, it only indexes metadata (labels), making it much cheaper to operate. You still get powerful querying through LogQL, which feels similar to PromQL.

The architecture mirrors Prometheus: promtail agents run on nodes collecting logs, adding labels, and shipping them to Loki. Grafana queries Loki alongside Prometheus metrics, providing unified observability.

## Ingress and API Gateway Layer

### NGINX Ingress Controller

The NGINX Ingress Controller watches Kubernetes Ingress resources and configures an NGINX instance accordingly. When you create an Ingress defining routing rules, the controller generates NGINX configuration and reloads NGINX.

It runs as a deployment (or DaemonSet) in the cluster, typically exposed via a LoadBalancer Service. All external HTTP(S) traffic flows through it, and it routes requests based on hostnames and paths to backend Services.

### Traefik's Dynamic Configuration

Traefik takes a more dynamic approach. Instead of reloading configuration, it watches Kubernetes resources and updates routing rules in real-time without restarts. It supports automatic HTTPS via Let's Encrypt, middlewares for authentication and rate limiting, and multiple protocols beyond HTTP.

### Envoy Gateway and Contour

These projects use Envoy as the underlying proxy but provide Kubernetes-native configuration experiences.

**Contour** uses HTTPProxy custom resources that are more expressive than standard Ingress, supporting advanced features like request retries, traffic weighting, and header manipulation.

**Envoy Gateway** is implementing the Gateway API, the next-generation replacement for Ingress that provides role-oriented design, portable configurations, and expressive routing.

### Kong as API Gateway

Kong extends beyond simple ingress, providing full API gateway capabilities: authentication, rate limiting, request/response transformation, and plugin extensibility.

It runs as pods in Kubernetes but can also manage APIs outside the cluster. The declarative configuration can be stored in Kubernetes custom resources, making API management infrastructure-as-code.

## Security Projects

### cert-manager: Certificate Automation

cert-manager automates the creation, renewal, and use of TLS certificates. It acts as a Kubernetes controller watching Certificate custom resources.

When you create a Certificate resource specifying you want a cert for "myapp.example.com," cert-manager initiates an ACME challenge with Let's Encrypt, proves domain ownership, obtains the certificate, and stores it in a Kubernetes Secret. It monitors expiration and renews automatically.

This integrates with Ingress controllers, service meshes, and any application needing TLS, eliminating manual certificate management.

### Open Policy Agent (OPA) and Gatekeeper

OPA is a general-purpose policy engine. You write policies in Rego (a declarative language) defining what's allowed and what's denied.

**Gatekeeper** integrates OPA with Kubernetes admission control. It intercepts resource creation/update requests before they're persisted, evaluates them against policies, and accepts or rejects them.

Example policies: require all containers to have resource limits, prohibit running as root, enforce specific label requirements, or restrict which registries images can come from. Policies are stored as Kubernetes custom resources and can be managed via GitOps.

### Falco: Runtime Security

Falco monitors system calls in real-time, detecting suspicious behavior. It runs as a DaemonSet with kernel modules or eBPF probes watching all system activity.

Predefined rules detect things like: shells spawned in containers, sensitive file access, unexpected network connections, or privilege escalation attempts. When violations occur, Falco generates alerts sent to SIEM systems, Slack, or other alerting channels.

This provides runtime threat detection complementing the admission control that Gatekeeper provides at deployment time.

### Trivy and Image Scanning

Trivy scans container images for known vulnerabilities, misconfigurations, and secrets. It can run as a CLI tool in CI/CD pipelines or as a Kubernetes operator continuously scanning running images.

Integration with admission controllers allows you to prevent vulnerable images from being deployed. The continuous scanning catches newly discovered vulnerabilities in already-running images.

## GitOps and Continuous Deployment

### Flux Architecture

Flux implements GitOps by continuously synchronizing cluster state with Git repositories. It consists of several controllers:

**Source Controller** watches Git repositories, Helm repositories, and OCI registries for changes. When it detects updates, it fetches the content and makes it available to other controllers.

**Kustomize Controller** applies Kustomize configurations from the fetched sources. **Helm Controller** installs and upgrades Helm charts. **Notification Controller** sends alerts about sync status.

The critical insight is that Git becomes the single source of truth. You never kubectl apply directly to production—you commit changes to Git, and Flux automatically applies them.

### ArgoCD's UI and Workflow

ArgoCD provides a more opinionated GitOps experience with a powerful UI. It continuously monitors Git repositories and compares the desired state (in Git) with actual state (in cluster).

When drift is detected—someone manually changed a resource—ArgoCD shows the difference and can auto-sync or wait for manual approval. The UI visualizes application deployments, showing the entire resource tree: deployments, pods, services, ingresses.

ArgoCD supports multi-cluster deployments, where a single ArgoCD instance manages applications across many Kubernetes clusters, essential for enterprises with multiple environments.

### Progressive Delivery with Flagger

Flagger automates canary deployments, blue/green deployments, and A/B testing. It integrates with service meshes and ingress controllers to gradually shift traffic.

When you update a deployment, Flagger creates a canary version, gradually increases traffic to it while monitoring metrics, and automatically promotes or rolls back based on success criteria. If error rates spike or latency increases, it automatically reverts.

This happens declaratively through custom resources defining promotion thresholds and analysis metrics, removing the manual orchestration of phased rollouts.

## Storage and Data Management

### Container Storage Interface (CSI)

CSI standardizes how storage systems integrate with Kubernetes. Storage vendors implement CSI drivers that Kubernetes can use to provision volumes.

When you create a PersistentVolumeClaim, the CSI driver provisions storage (creating an AWS EBS volume, for example), attaches it to the appropriate node, and mounts it into the pod. Different storage classes can use different CSI drivers with different parameters.

### Rook: Cloud Native Storage

Rook turns distributed storage systems into self-managing, self-scaling, self-healing storage services. It runs **Ceph** (a distributed storage system) inside Kubernetes, managing all the operational complexity.

Rook operators watch custom resources defining storage clusters, object stores, and file systems. They orchestrate Ceph daemons as pods, handle failures and rebalancing, and expose storage through standard Kubernetes APIs (PVCs, object storage APIs).

This provides cloud-like storage on-premises or in any environment, managed entirely through Kubernetes.

### Velero: Backup and Disaster Recovery

Velero backs up Kubernetes resources and persistent volumes. It can back up entire namespaces or specific resources filtered by labels.

Backups are stored in object storage (S3, GCS, Azure Blob) and can restore to the same cluster (disaster recovery) or different clusters (migration). Volume snapshots integrate with CSI drivers for efficient storage backups.

Scheduled backups run automatically, and restore operations can selectively restore specific resources or namespaces.

## CI/CD Integration

### Tekton Pipelines

Tekton is a Kubernetes-native CI/CD framework. Instead of external CI/CD servers, pipelines run as pods in the cluster.

**Tasks** define individual steps (run tests, build images, deploy applications). **Pipelines** chain tasks together. **PipelineRuns** are instances of executing pipelines with specific parameters.

Everything is Kubernetes resources, allowing you to manage CI/CD infrastructure the same way you manage applications. Tekton provides building blocks; you compose them into workflows matching your needs.

### Jenkins X: Opinionated CI/CD

Jenkins X builds on Tekton, providing an opinionated, fully automated CI/CD experience. It auto-generates pipelines for applications, implements GitOps, and handles preview environments for pull requests.

When you create a pull request, Jenkins X automatically deploys a preview environment, runs tests, and adds status checks. When merged, it automatically promotes through staging to production based on configured strategies.

## Package Management and Application Delivery

### Helm Architecture

Helm packages Kubernetes applications as charts—collections of templated YAML files with a values file for configuration.

**Charts** define the application structure. **Values** customize the chart for specific deployments. **Releases** are instances of charts deployed to clusters.

Helm's templating allows you to maintain a single chart that deploys differently across environments. The helm CLI talks to the Kubernetes API directly (Helm 3 removed the server-side Tiller component, improving security).

### Kustomize: Template-Free Customization

Kustomize takes a different approach—overlays instead of templates. You start with base manifests, then apply patches and transformations without modifying the originals.

A base directory contains standard manifests. Overlay directories (dev, staging, prod) contain kustomization.yaml files specifying changes: different replica counts, additional labels, different images.

This composition approach is often simpler than templating for teams uncomfortable with template syntax, and it's built into kubectl natively.

### Operators and Custom Resource Definitions

Operators extend Kubernetes to manage complex applications. They combine custom resources (representing the desired state) with custom controllers (reconciling actual state to desired state).

A database operator might provide a PostgreSQL custom resource. When you create one, the operator creates all necessary pods, services, config maps, secrets, and persistent volumes. It handles backups, failover, and upgrades—all the operational knowledge encoded as software.

**Operator Framework** provides tools for building operators. **OperatorHub** is a registry of community operators. This pattern has become the standard way to manage stateful applications in Kubernetes.

## Multi-Tenancy and Cluster Management

### Hierarchical Namespaces

The Hierarchical Namespace Controller (HNC) allows namespaces to be organized in trees, with child namespaces inheriting policies and resources from parents.

This simplifies multi-tenant clusters where teams get root namespaces, and they can create sub-namespaces for applications, automatically inheriting network policies, RBAC, and quotas.

### Virtual Clusters with vcluster

vcluster runs complete virtual Kubernetes clusters inside namespaces of a host cluster. Each virtual cluster has its own API server, scheduler, and controller manager, but shares the host's worker nodes.

This provides strong isolation for tenants without the overhead of separate physical clusters. Each tenant feels like they have a dedicated cluster with full control, while infrastructure teams manage a single underlying cluster.

### Cluster API: Declarative Cluster Management

Cluster API treats Kubernetes clusters themselves as resources that can be managed declaratively. You define a Cluster resource, and controllers provision infrastructure and bootstrap Kubernetes.

This works across cloud providers and on-premises environments. You can manage fleets of clusters (dev, staging, production across multiple regions) using the same declarative approach you use for applications.

## How They Work Together: The Complete Picture

### The Layered Architecture

These projects form layers of abstraction. At the bottom, container runtimes execute containers. Kubernetes orchestrates them. Service meshes add sophisticated traffic management. Observability tools provide visibility. GitOps tools automate deployment. Security tools enforce policies at every layer.

### The Integration Pattern

Most cloud native projects follow a similar pattern: they watch Kubernetes resources via the API server, reconcile desired state with actual state, and leverage standard Kubernetes extension points (CRDs, admission webhooks, CSI, CNI, CRI).

This consistency means projects compose well. You can use Prometheus for metrics, Jaeger for traces, Loki for logs, Flagger for progressive delivery, Flux for GitOps, and cert-manager for certificates—all in the same cluster, all following similar operational patterns.

### The Ecosystem Effect

The cloud native ecosystem's power comes from this composability. Instead of monolithic platforms, you assemble best-of-breed components. Each project focuses on doing one thing well, relying on Kubernetes primitives for integration.

The CNCF provides governance ensuring projects remain open, vendor-neutral, and interoperable. The community shares patterns and practices, creating a collective knowledge base that accelerates everyone's adoption.

Understanding how these projects work individually and how they integrate reveals the true power of cloud native: not just containers and Kubernetes, but an entire ecosystem of tools working together to build resilient, observable, and manageable distributed systems.

# eBPF in Cloud Native: The Revolutionary Kernel Technology

## What eBPF Actually Is

### The Fundamental Concept

eBPF (extended Berkeley Packet Filter) is a revolutionary technology that allows you to run sandboxed programs directly in the Linux kernel without changing kernel source code or loading kernel modules. Think of it as a safe, JIT-compiled virtual machine running inside the kernel.

This is transformative because traditionally, extending kernel functionality required writing kernel modules—risky, crash-prone, and requiring deep kernel expertise. eBPF provides a safe way to add custom logic at the kernel level.

### The Evolution from Packet Filtering

The original BPF was designed for packet filtering (hence the name). You could write simple programs to decide which network packets to capture. eBPF vastly expanded this concept to cover almost any kernel subsystem: networking, security, tracing, performance monitoring, and more.

Modern eBPF programs can attach to hundreds of kernel hook points, inspect and modify kernel data structures, maintain state in maps, and communicate with user-space programs—all while running at kernel speed.

## The eBPF Architecture

### The Verifier: Safety First

When you load an eBPF program, the kernel's verifier analyzes it to ensure it's safe. It checks that:

**The program terminates** (no infinite loops allowed). **Memory accesses are valid** (no out-of-bounds reads or writes). **No kernel crashes are possible** (bounds checking on all operations). **Helper functions are called correctly** (type checking and privilege verification).

This verification happens at load time, not runtime, so there's no performance overhead. If verification fails, the program is rejected before it ever runs. This is how eBPF achieves safety without sacrificing performance.

### JIT Compilation

Verified eBPF programs are compiled just-in-time to native machine code. This means eBPF programs run at nearly the same speed as natively compiled kernel code, without the interpretation overhead of a traditional virtual machine.

The JIT compiler is architecture-specific (x86, ARM, etc.), translating eBPF bytecode into optimized native instructions for the host CPU.

### eBPF Maps: Kernel-Space Data Structures

eBPF maps are key-value data structures that persist beyond individual program invocations. They're how eBPF programs maintain state and communicate with user-space.

**Hash maps** store arbitrary key-value pairs. **Array maps** provide indexed storage. **Ring buffers** enable efficient event streaming from kernel to user-space. **LRU maps** automatically evict least-recently-used entries. **Per-CPU maps** avoid synchronization overhead for performance-critical paths.

User-space programs can read and write these maps, creating a bidirectional communication channel with kernel-space eBPF programs.

### Hook Points: Where eBPF Programs Attach

eBPF programs attach to specific kernel events or locations:

**Tracepoints** are stable kernel instrumentation points defined for observability. **Kprobes** (kernel probes) can attach to almost any kernel function dynamically. **Uprobes** (user probes) attach to user-space functions in applications. **XDP** (eXpress Data Path) hooks run at the earliest point when network packets arrive. **TC** (Traffic Control) hooks process packets in the networking stack. **LSM** (Linux Security Module) hooks intercept security-sensitive operations. **Cgroup** hooks trigger on cgroup-related events.

Each hook type serves different purposes and has different capabilities and performance characteristics.

## eBPF in Kubernetes Networking

### Cilium: The eBPF-Native CNI

Cilium is the most prominent eBPF-based Kubernetes CNI plugin, and it demonstrates why eBPF is revolutionary for networking.

### How Cilium Replaces kube-proxy

Traditional kube-proxy uses iptables or IPVS for Service load balancing. For every Service, it creates numerous iptables rules. With thousands of Services, this becomes a performance bottleneck—every packet traverses a long chain of rules.

**Cilium's eBPF approach** is fundamentally different. When a packet arrives, an eBPF program attached to the network interface directly examines the packet, looks up the destination in an eBPF map containing Service endpoint information, and rewrites the packet destination to a backend pod IP—all in a single kernel function call.

No iptables traversal. No linear rule evaluation. Just direct hash map lookups. This is orders of magnitude faster and scales to tens of thousands of Services without performance degradation.

### Connection Tracking Without conntrack

The Linux kernel's conntrack system tracks all network connections for NAT and stateful firewalling. With high connection rates, conntrack becomes a bottleneck and can even drop connections when its table fills.

Cilium can bypass conntrack entirely using eBPF maps to track connections. The eBPF programs maintain their own connection state, avoiding conntrack's global lock and table size limitations. This enables handling millions of connections per second.

### XDP: Packet Processing at Wire Speed

XDP allows eBPF programs to process packets immediately when they arrive at the network card, before any kernel networking stack processing.

**DDoS mitigation** can drop malicious packets at XDP, using almost no CPU—the kernel never allocates memory for these packets. **Load balancing** can happen at XDP, distributing traffic across backends with minimal latency. **Packet filtering** at XDP is incredibly efficient for high-throughput scenarios.

Cilium uses XDP for features like NodePort acceleration, where external traffic arriving at any node can be load-balanced directly to backend pods on other nodes with microsecond-level latency.

### eBPF for Network Policy Enforcement

Traditional network policies are enforced using iptables, which evaluates rules sequentially. Cilium compiles network policies directly into eBPF programs.

When you create a NetworkPolicy saying "pod A can talk to pod B on port 80," Cilium generates an eBPF program that's attached to the network namespace. When pod A sends a packet, the eBPF program checks the destination and port against the policy (using map lookups), allowing or dropping the packet immediately.

This is dramatically faster than iptables, especially with complex policies. The performance is constant regardless of the number of policies because eBPF uses hash maps rather than linear rule evaluation.

### Identity-Based Security

Cilium assigns numeric identities to pods based on their labels. Instead of tracking source/destination IP addresses (which change as pods restart), eBPF programs work with these stable identities.

When a packet leaves pod A, Cilium's eBPF program tags it with pod A's identity. The receiving node's eBPF program checks if that identity is allowed to reach pod B based on policies. This survives pod restarts and IP changes automatically.

The identity information is stored in efficient eBPF maps replicated across all nodes, enabling identity-based security without centralized policy servers.

## eBPF in Service Mesh

### Cilium Service Mesh vs. Sidecar Meshes

Traditional service meshes like Istio inject sidecar proxies into every pod. Every packet goes: app container → sidecar → network → sidecar → app container. This adds latency and resource overhead.

**Cilium's eBPF-based service mesh** eliminates sidecars. eBPF programs attached at the socket or network layer intercept traffic, apply policies, collect metrics, and perform mTLS—all in the kernel.

Traffic goes: app container → eBPF → network → eBPF → app container. No user-space proxy. No additional process overhead. Latency drops from milliseconds to microseconds.

### How Transparent Encryption Works

Cilium can transparently encrypt all pod-to-pod traffic using IPsec or WireGuard, implemented via eBPF.

When a packet leaves a pod, an eBPF program intercepts it, encrypts it using WireGuard (which has kernel support), and sends it on the wire. The receiving node's eBPF program decrypts it before delivering to the destination pod.

The applications are completely unaware—no code changes, no configuration. The eBPF programs handle key exchange, rotation, and all encryption operations transparently.

### L7 Protocol Visibility

eBPF programs can parse HTTP, gRPC, Kafka, and other application protocols directly in the kernel, extracting metadata like request methods, response codes, and latencies.

This data populates eBPF maps that user-space agents read to export metrics. You get service mesh-level observability (seeing all HTTP requests, for example) without proxy overhead.

For protocols eBPF can't efficiently parse in-kernel, Cilium falls back to user-space parsers, but the architecture allows moving more parsing into eBPF as capabilities expand.

## eBPF for Observability

### Pixie: Automatic Observability

Pixie uses eBPF to automatically collect telemetry from all applications without instrumentation. It's like getting OpenTelemetry-level observability for free.

**How it works**: Pixie deploys eBPF programs that attach to system calls (read, write, send, recv) and SSL/TLS functions. When applications make network calls, these programs capture request/response data, parse protocols automatically, and correlate requests across services.

You get distributed tracing, full-body request/response capture, and golden metrics for every service—without adding libraries to applications or changing code. The eBPF programs recognize HTTP, gRPC, DNS, MySQL, PostgreSQL, Redis, Kafka, and more.

### Parca: Continuous Profiling

Parca uses eBPF to continuously profile applications, showing exactly where CPU time is spent—down to individual functions.

eBPF programs sample stack traces periodically (using perf events), building flame graphs showing the complete call hierarchy. This happens system-wide with minimal overhead (typically <1% CPU).

You can see which Kubernetes pods are consuming CPU, which functions within those pods, and even which lines of code. This helps identify performance issues, memory leaks, and optimization opportunities without application changes.

### Tetragon: Security Observability

Tetragon uses eBPF to provide deep runtime security insights. It tracks process execution, file access, network connections, and privilege changes in real-time.

eBPF programs attach to kernel functions handling exec, file open, network connect, and capability changes. They capture rich context: which pod, which container, full command line, parent process, user ID, and more.

This creates a complete audit trail of security-relevant behavior. You can detect when a container spawns a shell, access sensitive files, or makes unexpected network connections—with context about the Kubernetes workload involved.

## eBPF for Security

### Falco's eBPF Driver

Falco originally used a kernel module but now primarily uses eBPF. The eBPF programs monitor system calls, watching for suspicious patterns.

When a container makes a system call like execve (starting a process) or connect (network connection), the eBPF program captures the details and sends them to user-space. Falco's rule engine evaluates these events against security rules.

Example detection: "If a container spawns bash and it wasn't the entrypoint, alert." The eBPF program sees the execve syscall, checks if it's bash, the user-space component checks if this is expected, and generates alerts if not.

### Tracee: Runtime Security and Forensics

Tracee uses eBPF for runtime security monitoring and forensics. It captures comprehensive system activity—every process, file operation, network connection—with full context.

The eBPF programs use ring buffers to efficiently stream events to user-space. Tracee includes signatures detecting known attack patterns: reverse shells, privilege escalation, container escapes, crypto mining.

Because eBPF runs in the kernel, it's very difficult for attackers to evade. Even rootkits that hide processes from user-space tools are visible to eBPF programs examining kernel data structures directly.

### KubeArmor: Enforcement, Not Just Detection

KubeArmor uses eBPF LSM (Linux Security Module) hooks to enforce security policies. Instead of just alerting on violations, it can block them.

When an application tries to execute a process, open a file, or make a network connection, the eBPF LSM program checks it against policies. If violated, it returns an error, preventing the operation.

This provides runtime protection: even if an attacker exploits a vulnerability, they can't execute shells, access credential files, or exfiltrate data if policies prevent it.

## eBPF for Performance Optimization

### Bypassing the Kernel Network Stack

Typical packet flow: NIC → driver → kernel network stack (TCP/IP) → socket buffer → application. This involves numerous memory copies, context switches, and layers of processing.

**AF_XDP** (Address Family XDP) creates a fast path: NIC → XDP program → user-space application, bypassing most of the kernel. Applications get raw packets with microsecond-level latency.

This is used in high-performance scenarios like packet capture at 100Gbps, low-latency trading systems, and specialized load balancers. In Kubernetes, it can accelerate data plane performance for specialized workloads.

### CPU Scheduling Optimization

eBPF programs can even influence CPU scheduling decisions. Experimental schedulers using eBPF can implement custom policies: prioritizing latency-sensitive pods, co-locating related containers on the same CPU cores, or implementing specialized scheduling algorithms.

This is cutting-edge but shows eBPF's potential—extending even core kernel subsystems like the scheduler without kernel modifications.

## eBPF Tooling and Development

### libbpf and CO-RE

**libbpf** is the standard library for working with eBPF from C. **CO-RE** (Compile Once, Run Everywhere) solves a major eBPF problem: kernel data structure offsets change between kernel versions.

CO-RE programs include relocation information. When loaded, libbpf adjusts the program for the running kernel's structure layouts. A single eBPF binary works across different kernel versions without recompilation.

This is crucial for cloud native tools that must work on diverse Kubernetes nodes running various kernel versions.

### BCC and bpftrace

**BCC** (BPF Compiler Collection) provides Python/Lua frontends for writing eBPF programs. It's great for prototyping and one-off debugging.

**bpftrace** is a high-level tracing language inspired by awk and DTrace. One-liners can answer complex questions:

"Show me which pods are making DNS queries for specific domains." "Count system calls by Kubernetes namespace." "Measure latency distribution for file I/O per container."

These tools make eBPF accessible to operators and SREs, not just kernel developers.

### Hubble: Network Observability UI

Hubble is Cilium's observability component, visualizing eBPF-collected data. It shows:

**Service dependency maps** built from actual observed traffic. **Flow logs** showing every connection between pods with L7 details. **Network policy violations** showing blocked connections. **DNS queries** and responses.

All this data comes from eBPF programs watching network traffic in real-time, with no application instrumentation.

## The Challenges and Limitations

### Kernel Version Requirements

eBPF features have evolved rapidly. Basic eBPF works on older kernels, but advanced features require modern kernels (5.x+). CO-RE requires 5.2+. BPF LSM requires 5.7+. Some cloud native tools require specific kernel configurations.

This creates compatibility challenges. Organizations with older distributions may not access cutting-edge eBPF features, limiting which cloud native tools they can adopt.

### Complexity and Debugging

eBPF programs are difficult to debug. They run in kernel context, can't use standard debugging tools, and have strict limitations (no loops, bounded stack usage, limited helper functions).

When eBPF programs misbehave, diagnosing issues requires examining verifier rejection messages, using bpftool to inspect maps, and sometimes adding debug output to figure out what's happening.

### The Privilege Requirement

Loading eBPF programs typically requires CAP_BPF or CAP_SYS_ADMIN capabilities. In multi-tenant environments, this limits who can deploy eBPF-based tools.

Solutions exist (eBPF programs loaded by privileged system agents, unprivileged eBPF for limited use cases), but privilege management remains a consideration.

### Memory Overhead

While eBPF programs themselves are efficient, the maps storing state consume kernel memory. High-cardinality data (tracking millions of connections, thousands of security events per second) can use significant memory.

This is usually manageable but requires capacity planning, especially in large clusters with comprehensive observability.

## The Future: eBPF's Growing Role

### eBPF as Infrastructure Foundation

Increasingly, eBPF is becoming the foundational technology for cloud native infrastructure. Instead of building on iptables, conntrack, and traditional Linux networking, new tools build directly on eBPF.

This shift is happening because eBPF provides better performance, flexibility, and safety. As kernel eBPF capabilities expand, more functionality moves from user-space or kernel modules into eBPF programs.

### Multi-Cluster and Edge Computing

eBPF's efficiency makes it ideal for edge computing where resources are constrained. A single node can run comprehensive networking, security, and observability with eBPF-based tools, using far less overhead than traditional approaches.

For multi-cluster scenarios, eBPF enables efficient cluster mesh implementations where nodes across clusters communicate directly with transparent encryption and policy enforcement.

### The Convergence

We're seeing convergence where a single eBPF foundation supports multiple functions:

Cilium provides networking, network policy, service mesh, and observability—all from unified eBPF programs. This reduces complexity (one system instead of separate CNI, service mesh, monitoring tools) while improving performance and consistency.

## How It All Connects

### eBPF Transforms the Stack

In a modern cloud native stack with eBPF:

**Cilium** replaces traditional CNI and kube-proxy with eBPF networking and load balancing. **Cilium Service Mesh** replaces sidecar proxies with eBPF-based traffic management and mTLS. **Hubble** provides observability from eBPF flow logs. **Tetragon** adds runtime security monitoring via eBPF. **Pixie** automatically instruments applications using eBPF tracing.

This creates an integrated platform where eBPF programs at various kernel hook points work together, sharing data via eBPF maps, providing capabilities that would require multiple separate tools in traditional architectures.

### The Paradigm Shift

eBPF represents a paradigm shift in how we build cloud native infrastructure. Instead of bolting tools onto the kernel from outside (iptables, kernel modules, user-space proxies), we extend the kernel safely from within.

This enables performance levels and integration depths previously impossible. The cloud native ecosystem is increasingly eBPF-first, building the next generation of networking, security, and observability tools on this foundation.

Understanding eBPF is now essential to understanding modern Kubernetes infrastructure—it's not a niche technology but the core of how cutting-edge cloud native systems work.

# Cloud Native Architecture: Comprehensive ASCII Diagrams

I'll create multiple detailed diagrams covering the entire architecture we discussed. Each diagram will show component relationships, data flows, and interaction patterns.

## Diagram 1: Container Runtime & Kubernetes Core Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           KUBERNETES CONTROL PLANE                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐                 │
│  │   API Server │◄────►│   Scheduler  │      │  Controller  │                 │
│  │              │      │              │      │   Manager    │                 │
│  │ - REST API   │      │ - Pod        │      │              │                 │
│  │ - AuthN/AuthZ│      │   Placement  │      │ - Deployment │                 │
│  │ - Validation │      │ - Resource   │      │ - ReplicaSet │                 │
│  │ - Admission  │      │   Fit        │      │ - StatefulSet│                 │
│  │   Control    │      │ - Affinity   │      │ - DaemonSet  │                 │
│  └──────┬───────┘      └──────────────┘      └──────────────┘                 │
│         │                                                                       │
│         │ Watch Resources                                                      │
│         ▼                                                                       │
│  ┌──────────────────────────────────────────────────────────┐                 │
│  │                     etcd (Cluster State)                  │                 │
│  │  - Distributed Key-Value Store                            │                 │
│  │  - Stores all cluster data: pods, services, configs       │                 │
│  │  - Source of truth for desired state                      │                 │
│  └──────────────────────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ API Calls
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              KUBERNETES WORKER NODE                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────────────┐        │
│  │                           kubelet                                   │        │
│  │  ┌──────────────────────────────────────────────────────────────┐  │        │
│  │  │ Responsibilities:                                             │  │        │
│  │  │ • Watch API Server for assigned pods                         │  │        │
│  │  │ • Ensure containers are running as specified                 │  │        │
│  │  │ • Report pod & node status back to API Server                │  │        │
│  │  │ • Mount volumes, manage secrets                              │  │        │
│  │  │ • Execute health checks (liveness, readiness, startup)       │  │        │
│  │  └──────────────────────────────────────────────────────────────┘  │        │
│  │                              │                                      │        │
│  │                              │ CRI (gRPC)                           │        │
│  │                              ▼                                      │        │
│  │  ┌──────────────────────────────────────────────────────────────┐  │        │
│  │  │              Container Runtime Interface (CRI)                │  │        │
│  │  │  • Standard API for container lifecycle management           │  │        │
│  │  │  • Allows pluggable runtimes (containerd, CRI-O)             │  │        │
│  │  └──────────────────────────────────────────────────────────────┘  │        │
│  └───────────────────────────┬──────────────────────────────────────────┘        │
│                              │                                                  │
│                              ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │                    Container Runtime (containerd)                    │       │
│  │  ┌───────────────────────────────────────────────────────────────┐  │       │
│  │  │ High-Level Runtime Functions:                                 │  │       │
│  │  │ • Image pull from registry                                    │  │       │
│  │  │ • Image storage & management                                  │  │       │
│  │  │ • Container lifecycle (create, start, stop, delete)           │  │       │
│  │  │ • Snapshot management                                         │  │       │
│  │  │ • Delegation to low-level runtime                             │  │       │
│  │  └───────────────────────────────────────────────────────────────┘  │       │
│  │                              │                                       │       │
│  │                              │ OCI Runtime Spec                      │       │
│  │                              ▼                                       │       │
│  │  ┌───────────────────────────────────────────────────────────────┐  │       │
│  │  │              Low-Level Runtime (runc)                         │  │       │
│  │  │  • Creates namespaces (PID, NET, MNT, UTS, IPC)              │  │       │
│  │  │  • Sets up cgroups for resource limits                       │  │       │
│  │  │  • Applies security (capabilities, AppArmor, SELinux)        │  │       │
│  │  │  • Executes container process                                │  │       │
│  │  └───────────────────────────────────────────────────────────────┘  │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │                           POD STRUCTURE                              │       │
│  │  ┌─────────────────────────────────────────────────────────────┐    │       │
│  │  │ Pod Network Namespace (shared by all containers)            │    │       │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │    │       │
│  │  │  │    Pause     │  │     App      │  │   Sidecar    │      │    │       │
│  │  │  │  Container   │  │  Container   │  │  Container   │      │    │       │
│  │  │  │              │  │              │  │              │      │    │       │
│  │  │  │ • Holds NS   │  │ • Main App   │  │ • Envoy      │      │    │       │
│  │  │  │ • Sleeps     │  │ • Joins NS   │  │ • Logging    │      │    │       │
│  │  │  │   forever    │  │ • Same IP    │  │ • Monitoring │      │    │       │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘      │    │       │
│  │  │                                                              │    │       │
│  │  │  Shared Resources:                                          │    │       │
│  │  │  • eth0 (same IP for all)                                   │    │       │
│  │  │  • localhost communication                                  │    │       │
│  │  │  • Shared volumes                                           │    │       │
│  │  └─────────────────────────────────────────────────────────────┘    │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │                        kube-proxy                                    │       │
│  │  • Watches Services & Endpoints from API Server                     │       │
│  │  • Programs iptables/IPVS rules for load balancing                  │       │
│  │  • ClusterIP → Pod IP translation                                   │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key Flows:**
1. **Pod Creation**: User → API Server → etcd (store) → Scheduler (select node) → API Server → kubelet → CRI → containerd → runc → container running
2. **Container Lifecycle**: kubelet monitors → health checks → report status → API Server → etcd
3. **Runtime Hierarchy**: kubelet (K8s level) → containerd (image/container management) → runc (actual execution)

---

## Diagram 2: Kubernetes Networking Stack - Pod-to-Pod Communication

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          NODE 1 (IP: 192.168.1.10)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────┐         │
│  │                    Pod A (10.244.1.5)                              │         │
│  │  ┌─────────────────────────────────────────────────────────────┐  │         │
│  │  │ Container: eth0 (10.244.1.5)                                │  │         │
│  │  │                                                              │  │         │
│  │  │  Application sends packet to Pod B (10.244.2.7)            │  │         │
│  │  │  Dest: 10.244.2.7, Src: 10.244.1.5                         │  │         │
│  │  └────────────────┬────────────────────────────────────────────┘  │         │
│  │                   │                                                │         │
│  │                   │ Virtual Ethernet Pair (veth)                  │         │
│  │                   ▼                                                │         │
│  └───────────────────┼────────────────────────────────────────────────┘         │
│                      │                                                          │
│         ┌────────────▼─────────────┐                                            │
│         │  veth123abc (host side)  │                                            │
│         └────────────┬─────────────┘                                            │
│                      │                                                          │
│         ┌────────────▼──────────────────────────────────────┐                   │
│         │         Linux Bridge (cni0) or Direct Route       │                   │
│         │  • IP: 10.244.1.1 (gateway for pods on this node)│                   │
│         │  • All pod veth interfaces connect here          │                   │
│         └────────────┬──────────────────────────────────────┘                   │
│                      │                                                          │
│                      │ Check routing table                                      │
│                      ▼                                                          │
│         ┌────────────────────────────────────────────────────┐                  │
│         │         Node 1 Routing Table                       │                  │
│         │  10.244.1.0/24  → local (cni0)                    │                  │
│         │  10.244.2.0/24  → 192.168.1.20 (Node 2)           │                  │
│         │  10.244.3.0/24  → 192.168.1.30 (Node 3)           │                  │
│         │                                                    │                  │
│         │  (Routes populated by CNI plugin via BGP/static)  │                  │
│         └────────────┬──────────────────────────────────────┘                  │
│                      │                                                          │
│                      │ Packet routed to Node 2                                  │
│                      ▼                                                          │
│         ┌────────────────────────────────────────────────────┐                  │
│         │           Physical NIC (eth0)                      │                  │
│         │  • Sends packet to 192.168.1.20                   │                  │
│         │  • Packet: Dest=10.244.2.7, Src=10.244.1.5        │                  │
│         │    (NO NAT - direct routing)                      │                  │
│         │                                                    │                  │
│         │  OR (Overlay Mode):                               │                  │
│         │  • Encapsulates in VXLAN/UDP                      │                  │
│         │  • Outer: Dest=192.168.1.20, Src=192.168.1.10    │                  │
│         │  • Inner: Dest=10.244.2.7, Src=10.244.1.5        │                  │
│         └────────────┬──────────────────────────────────────┘                  │
└──────────────────────┼─────────────────────────────────────────────────────────┘
                       │
                       │ Physical Network
                       │
┌──────────────────────▼─────────────────────────────────────────────────────────┐
│                          NODE 2 (IP: 192.168.1.20)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│         ┌────────────────────────────────────────────────────┐                  │
│         │           Physical NIC (eth0)                      │                  │
│         │  • Receives packet from Node 1                    │                  │
│         │                                                    │                  │
│         │  Direct Mode:                                     │                  │
│         │  • Packet: Dest=10.244.2.7, Src=10.244.1.5       │                  │
│         │                                                    │                  │
│         │  Overlay Mode:                                    │                  │
│         │  • CNI agent decapsulates VXLAN                  │                  │
│         │  • Extracts inner packet                         │                  │
│         └────────────┬──────────────────────────────────────┘                  │
│                      │                                                          │
│                      │ Consult routing table                                    │
│                      ▼                                                          │
│         ┌────────────────────────────────────────────────────┐                  │
│         │         Node 2 Routing Table                       │                  │
│         │  10.244.2.0/24  → local (cni0)                    │                  │
│         │  10.244.1.0/24  → 192.168.1.10 (Node 1)           │                  │
│         └────────────┬──────────────────────────────────────┘                  │
│                      │                                                          │
│                      │ Local delivery                                           │
│                      ▼                                                          │
│         ┌────────────────────────────────────────────────────┐                  │
│         │         Linux Bridge (cni0)                        │                  │
│         │  • Receives packet for 10.244.2.7                 │                  │
│         │  • Forwards to appropriate veth interface         │                  │
│         └────────────┬──────────────────────────────────────┘                  │
│                      │                                                          │
│         ┌────────────▼─────────────┐                                            │
│         │  veth456def (host side)  │                                            │
│         └────────────┬─────────────┘                                            │
│                      │                                                          │
│                      │ Virtual Ethernet Pair                                    │
│                      ▼                                                          │
│  ┌───────────────────┼────────────────────────────────────────────────┐         │
│  │                   │                                                │         │
│  │  ┌────────────────▼────────────────────────────────────────────┐  │         │
│  │  │ Container: eth0 (10.244.2.7)                                │  │         │
│  │  │                                                              │  │         │
│  │  │  Application receives packet                               │  │         │
│  │  │  Dest: 10.244.2.7, Src: 10.244.1.5                         │  │         │
│  │  │  (Same IPs throughout - no NAT!)                           │  │         │
│  │  └─────────────────────────────────────────────────────────────┘  │         │
│  │                    Pod B (10.244.2.7)                              │         │
│  └───────────────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────────┘

CNI PLUGIN OPERATIONS:
┌──────────────────────────────────────────────────────────────────┐
│  When Pod is Created:                                            │
│  1. kubelet calls CNI plugin with "ADD" command                  │
│  2. CNI plugin:                                                  │
│     • Creates veth pair                                          │
│     • Moves one end to pod's network namespace                   │
│     • Assigns IP from pod CIDR range                             │
│     • Sets up routes in pod (default gw → bridge)                │
│     • Connects host end to bridge or adds route                  │
│     • Returns IP info to kubelet                                 │
│  3. kubelet stores IP in pod status                              │
│                                                                  │
│  Route Propagation (varies by CNI):                              │
│  • Calico BGP: Advertises routes via BGP to all nodes            │
│  • Flannel: Stores route info in etcd, agents watch it           │
│  • Cloud CNI: Programs cloud provider route tables               │
└──────────────────────────────────────────────────────────────────┘
```

**Key Concepts:**
- **No NAT**: Pod IPs are preserved across nodes (Kubernetes requirement)
- **Flat Network**: All pods can reach each other directly
- **CNI Plugin**: Handles IP allocation, veth creation, routing setup
- **Routing**: Either direct (infrastructure routes) or overlay (encapsulation)

---

## Diagram 3: Service Networking & kube-proxy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       SERVICE ABSTRACTION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────┐                │
│  │              Service: frontend (ClusterIP)                  │                │
│  │  • ClusterIP: 10.96.10.50                                  │                │
│  │  • Port: 80                                                │                │
│  │  • Selector: app=nginx                                     │                │
│  │                                                            │                │
│  │  Endpoints (dynamically updated):                          │                │
│  │    - 10.244.1.10:8080 (Pod nginx-1 on Node 1)             │                │
│  │    - 10.244.2.15:8080 (Pod nginx-2 on Node 2)             │                │
│  │    - 10.244.2.20:8080 (Pod nginx-3 on Node 2)             │                │
│  └────────────────────────────────────────────────────────────┘                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ kube-proxy watches
                                    │ Services & Endpoints
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          KUBE-PROXY ON EACH NODE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │                    IPTABLES MODE                              │              │
│  │  ┌────────────────────────────────────────────────────────┐  │              │
│  │  │ kube-proxy programs iptables rules:                    │  │              │
│  │  │                                                         │  │              │
│  │  │ # PREROUTING chain (catches Service traffic)           │  │              │
│  │  │ -A PREROUTING -j KUBE-SERVICES                         │  │              │
│  │  │                                                         │  │              │
│  │  │ # Service ClusterIP rule                               │  │              │
│  │  │ -A KUBE-SERVICES -d 10.96.10.50/32 -p tcp --dport 80  │  │              │
│  │  │    -j KUBE-SVC-FRONTEND                                │  │              │
│  │  │                                                         │  │              │
│  │  │ # Random selection among endpoints (probability)       │  │              │
│  │  │ -A KUBE-SVC-FRONTEND -m statistic --mode random       │  │              │
│  │  │    --probability 0.33 -j KUBE-SEP-ENDPOINT1            │  │              │
│  │  │ -A KUBE-SVC-FRONTEND -m statistic --mode random       │  │              │
│  │  │    --probability 0.50 -j KUBE-SEP-ENDPOINT2            │  │              │
│  │  │ -A KUBE-SVC-FRONTEND -j KUBE-SEP-ENDPOINT3            │  │              │
│  │  │                                                         │  │              │
│  │  │ # DNAT to actual pod IPs                               │  │              │
│  │  │ -A KUBE-SEP-ENDPOINT1 -p tcp -j DNAT                  │  │              │
│  │  │    --to-destination 10.244.1.10:8080                   │  │              │
│  │  │ -A KUBE-SEP-ENDPOINT2 -p tcp -j DNAT                  │  │              │
│  │  │    --to-destination 10.244.2.15:8080                   │  │              │
│  │  │ -A KUBE-SEP-ENDPOINT3 -p tcp -j DNAT                  │  │              │
│  │  │    --to-destination 10.244.2.20:8080                   │  │              │
│  │  └────────────────────────────────────────────────────────┘  │              │
│  └──────────────────────────────────────────────────────────────┘              │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │                      IPVS MODE (Modern)                       │              │
│  │  ┌────────────────────────────────────────────────────────┐  │              │
│  │  │ kube-proxy creates IPVS virtual servers:               │  │              │
│  │  │                                                         │  │              │
│  │  │ Virtual Server: 10.96.10.50:80                         │  │              │
│  │  │   Scheduler: rr (round-robin)                          │  │              │
│  │  │   Real Servers:                                        │  │              │
│  │  │     → 10.244.1.10:8080   (weight: 1)                   │  │              │
│  │  │     → 10.244.2.15:8080   (weight: 1)                   │  │              │
│  │  │     → 10.244.2.20:8080   (weight: 1)                   │  │              │
│  │  │                                                         │  │              │
│  │  │ Benefits:                                              │  │              │
│  │  │  • Hash table lookups (O(1) vs O(n) for iptables)     │  │              │
│  │  │  • Better load balancing algorithms                   │  │              │
│  │  │  • Scales to 10,000+ services efficiently             │  │              │
│  │  └────────────────────────────────────────────────────────┘  │              │
│  └──────────────────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘

REQUEST FLOW WITH SERVICE:
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Client Pod (10.244.1.5)                                                        │
│  │                                                                               │
│  │ Application code: GET http://frontend:80/api                                 │
│  │  (DNS resolves "frontend" → 10.96.10.50)                                     │
│  │                                                                               │
│  └──► Packet sent: Dest=10.96.10.50:80, Src=10.244.1.5:54321                   │
│                      │                                                           │
│                      ▼                                                           │
│         ┌────────────────────────────────────┐                                  │
│         │  Node's Network Stack (iptables)   │                                  │
│         │  • Matches Service ClusterIP       │                                  │
│         │  • Random selection → Endpoint 2   │                                  │
│         │  • DNAT: Dest becomes 10.244.2.15:8080                               │
│         │  • conntrack records this mapping  │                                  │
│         └────────────────┬───────────────────┘                                  │
│                          │                                                       │
│                          ▼                                                       │
│         Packet now: Dest=10.244.2.15:8080, Src=10.244.1.5:54321                │
│         (Routes as normal pod-to-pod traffic to Node 2)                         │
│                          │                                                       │
│                          ▼                                                       │
│         ┌────────────────────────────────────────────────┐                      │
│         │  Backend Pod (nginx-2) receives packet        │                      │
│         │  Sees source as: 10.244.1.5:54321             │                      │
│         │  Processes request, sends response             │                      │
│         └────────────────┬───────────────────────────────┘                      │
│                          │                                                       │
│                          ▼                                                       │
│         Response: Dest=10.244.1.5:54321, Src=10.244.2.15:8080                  │
│                          │                                                       │
│                          ▼                                                       │
│         ┌────────────────────────────────────┐                                  │
│         │  Node's conntrack                  │                                  │
│         │  • Recognizes connection           │                                  │
│         │  • Reverse DNAT (Un-NAT)           │                                  │
│         │  • Source becomes 10.96.10.50:80   │                                  │
│         └────────────────┬───────────────────┘                                  │
│                          │                                                       │
│                          ▼                                                       │
│         Client receives: Dest=10.244.1.5:54321, Src=10.96.10.50:80             │
│         (Response appears to come from Service IP!)                             │
└─────────────────────────────────────────────────────────────────────────────────┘

DNS INTEGRATION:
┌─────────────────────────────────────────────────────────────────────┐
│                   CoreDNS Deployment                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ CoreDNS watches Kubernetes API for Services                   │  │
│  │                                                                │  │
│  │ DNS Records automatically created:                            │  │
│  │  frontend.default.svc.cluster.local → 10.96.10.50            │  │
│  │  frontend.default.svc → 10.96.10.50                          │  │
│  │  frontend.default → 10.96.10.50                              │  │
│  │  frontend → 10.96.10.50 (with search domains)                │  │
│  │                                                                │  │
│  │ Pod's /etc/resolv.conf:                                       │  │
│  │   nameserver 10.96.0.10 (CoreDNS Service IP)                 │  │
│  │   search default.svc.cluster.local svc.cluster.local         │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Flows:**
1. **Service Creation**: User creates Service → API Server → etcd → kube-proxy watches → programs iptables/IPVS
2. **Endpoint Updates**: Pods created/deleted → Endpoints controller updates → kube-proxy reprograms rules
3. **Load Balancing**: Stateless (per-packet decision) vs Sticky sessions (SessionAffinity: ClientIP)
4. **Connection Tracking**: Ensures response packets get un-NATed correctly

---

## Diagram 4: eBPF-Based Networking (Cilium)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CILIUM eBPF ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │                  Cilium Control Plane                         │              │
│  │  ┌────────────────────────────────────────────────────────┐  │              │
│  │  │ cilium-operator (Deployment)                           │  │              │
│  │  │  • Watches Kubernetes API                             │  │              │
│  │  │  • Manages IP address allocation (IPAM)               │  │              │
│  │  │  • Computes network policies                          │  │              │
│  │  │  • Distributes identity information                   │  │              │
│  │  └────────────────────────────────────────────────────────┘  │              │
│  │                                                               │              │
│  │  ┌────────────────────────────────────────────────────────┐  │              │
│  │  │ cilium-agent (DaemonSet - runs on every node)         │  │              │
│  │  │  • Loads eBPF programs into kernel                    │  │              │
│  │  │  • Manages eBPF maps                                  │  │              │
│  │  │  • Handles CNI requests from kubelet                  │  │              │
│  │  │  • Updates routing and policy maps                    │  │              │
│  │  └────────────────────────────────────────────────────────┘  │              │
│  └──────────────────────────────────────────────────────────────┘              │
│                              │                                                  │
│                              │ Loads eBPF programs & maps                       │
│                              ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │                    LINUX KERNEL                               │              │
│  │  ┌────────────────────────────────────────────────────────┐  │              │
│  │  │              eBPF PROGRAMS (JIT compiled)              │  │              │
│  │  │                                                         │  │              │
│  │  │ 1. XDP Program (Earliest packet processing)            │  │              │
│  │  │    • Attached to: Physical NIC driver                  │  │              │
│  │  │    • Runs: Before skb allocation                       │  │              │
│  │  │    • Use cases:                                        │  │              │
│  │  │      - DDoS mitigation (drop at wire speed)            │  │              │
│  │  │      - NodePort load balancing                         │  │              │
│  │  │      - Packet sampling/monitoring                      │  │              │
│  │  │                                                         │  │              │
│  │  │ 2. TC (Traffic Control) Ingress                        │  │              │
│  │  │    • Attached to: Network interfaces (eth0, veth)      │  │              │
│  │  │    • Runs: As packets enter interface                  │  │              │
│  │  │    • Use cases:                                        │  │              │
│  │  │      - Pod-to-pod routing                              │  │              │
│  │  │      - Service load balancing (replaces kube-proxy)    │  │              │
│  │  │      - Network policy enforcement                      │  │              │
│  │  │      - NAT operations                                  │  │              │
│  │  │                                                         │  │              │
│  │  │ 3. TC Egress                                           │  │              │
│  │  │    • Attached to: Network interfaces                   │  │              │
│  │  │    • Runs: As packets leave interface                  │  │              │
│  │  │    • Use cases:                                        │  │              │
│  │  │      - Egress policy enforcement                       │  │              │
│  │  │      - Bandwidth limiting                              │  │              │
│  │  │      - Packet encryption (IPsec/WireGuard)             │  │              │
│  │  │                                                         │  │              │
│  │  │ 4. Socket/Connect Programs                             │  │              │
│  │  │    • Attached to: cgroup v2                            │  │              │
│  │  │    • Runs: At socket operations (connect, sendmsg)     │  │              │
│  │  │    • Use cases:                                        │  │              │
│  │  │      - Service translation in socket layer             │  │              │
│  │  │      - Accelerated host networking                     │  │              │
│  │  │      - L7 protocol parsing                             │  │              │
│  │  └────────────────────────────────────────────────────────┘  │              │
│  │                                                               │              │
│  │  ┌────────────────────────────────────────────────────────┐  │              │
│  │  │                   eBPF MAPS                             │  │              │
│  │  │  (Kernel memory, accessible from programs & userspace) │  │              │
│  │  │                                                         │  │              │
│  │  │  cilium_ipcache (IP → Identity)                        │  │              │
│  │  │  ┌─────────────────────────────────────────────────┐  │  │              │
│  │  │  │ 10.244.1.10 → Identity: 12345                   │  │  │              │
│  │  │  │ 10.244.2.15 → Identity: 12345                   │  │  │              │
│  │  │  │ 10.244.3.20 → Identity: 67890                   │  │  │              │
│  │  │  └─────────────────────────────────────────────────┘  │  │              │
│  │  │                                                         │  │              │
│  │  │  cilium_lb4_services (Service → Endpoints)             │  │              │
│  │  │  ┌─────────────────────────────────────────────────┐  │  │              │
│  │  │  │ 10.96.10.50:80 → [10.244.1.10:8080,            │  │  │              │
│  │  │  │                   10.244.2.15:8080,             │  │  │              │
│  │  │  │                   10.244.2.20:8080]             │  │  │              │
│  │  │  └─────────────────────────────────────────────────┘  │  │              │
│  │  │                                                         │  │              │
│  │  │  cilium_policy (Identity-based policies)               │  │              │
│  │  │  ┌─────────────────────────────────────────────────┐  │  │              │
│  │  │  │ Identity 12345 → Allow from Identity 67890     │  │  │              │
│  │  │  │                  Port 80, Protocol TCP          │  │  │              │
│  │  │  └─────────────────────────────────────────────────┘  │  │              │
│  │  │                                                         │  │              │
│  │  │  cilium_lxc (Local endpoints - pod veth mapping)       │  │              │
│  │  │  cilium_tunnel_map (Remote node → tunnel endpoint)     │  │              │
│  │  │  cilium_ct4_global (Connection tracking)               │  │              │
│  │  └────────────────────────────────────────────────────────┘  │              │
│  └──────────────────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘

PACKET FLOW WITH CILIUM eBPF:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Scenario: Pod A (10.244.1.10, Identity 12345) → Service frontend (10.96.10.50) │
│           Service backend: Pod B (10.244.2.15, Identity 67890)                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Step 1: Application sends packet                                              │
│  ┌───────────────────────────────────────────────────────┐                     │
│  │ Pod A Container                                        │                     │
│  │ send(sock, data, dest=10.96.10.50:80)                │                     │
│  └────────────────────────┬──────────────────────────────┘                     │
│                           │                                                     │
│                           ▼                                                     │
│  Step 2: Socket-level eBPF program (cgroup/connect)                            │
│  ┌────────────────────────────────────────────────────────────────┐            │
│  │ eBPF Program: sock4_connect                                    │            │
│  │  • Lookup dest IP in cilium_lb4_services map                   │            │
│  │  • Found: 10.96.10.50:80 → backend list                        │            │
│  │  • Select backend (consistent hashing): 10.244.2.15:8080       │            │
│  │  • Modify socket destination in kernel BEFORE packet created   │            │
│  │  • Result: Packet is created with dest=10.244.2.15:8080       │            │
│  │            (Application never knows about translation!)         │            │
│  └────────────────────────────────────────────────────────────────┘            │
│                           │                                                     │
│  Step 3: Packet leaves pod's eth0 → veth pair → host side                      │
│                           │                                                     │
│                           ▼                                                     │
│  Step 4: TC Egress eBPF program on veth (host side)                            │
│  ┌────────────────────────────────────────────────────────────────┐            │
│  │ eBPF Program: to-container                                     │            │
│  │  • Extract source IP: 10.244.1.10                              │            │
│  │  • Lookup in cilium_ipcache: 10.244.1.10 → Identity 12345      │            │
│  │  • Tag packet with source identity in packet metadata          │            │
│  │  • Check cilium_policy map for egress rules                    │            │
│  │  • Allow packet to proceed                                     │            │
│  └────────────────────────────────────────────────────────────────┘            │
│                           │                                                     │
│  Step 5: Routing decision (eBPF or kernel routing)                             │
│  ┌────────────────────────────────────────────────────────────────┐            │
│  │ eBPF can directly route:                                       │            │
│  │  • Lookup dest 10.244.2.15 in cilium_lxc (local) - NOT FOUND  │            │
│  │  • Lookup in cilium_tunnel_map for remote node                │            │
│  │  • Found: Node 2 (192.168.1.20)                                │            │
│  │  • Encapsulate in VXLAN or route directly                      │            │
│  │  • Forward to physical NIC                                     │            │
│  └────────────────────────────────────────────────────────────────┘            │
│                           │                                                     │
│                           │ Network                                             │
│                           ▼                                                     │
│  Step 6: Packet arrives at Node 2's NIC                                        │
│                           │                                                     │
│                           ▼                                                     │
│  Step 7: TC Ingress eBPF program on Node 2                                     │
│  ┌────────────────────────────────────────────────────────────────┐            │
│  │ eBPF Program: from-netdev                                      │            │
│  │  • Decapsulate if VXLAN                                        │            │
│  │  • Extract dest IP: 10.244.2.15                                │            │
│  │  • Extract source identity from packet metadata: 12345         │            │
│  │  • Lookup dest in cilium_lxc → find local veth for Pod B      │            │
│  │  • Check cilium_policy: Can Identity 12345 reach 67890?       │            │
│  │  •   Lookup policy: 67890 allows from 12345 on port 8080 ✓    │            │
│  │  • Update cilium_ct4_global (connection tracking)             │            │
│  │  • Forward directly to Pod B's veth                            │            │
│  └────────────────────────────────────────────────────────────────┘            │
│                           │                                                     │
│                           ▼                                                     │
│  Step 8: Packet delivered to Pod B container                                   │
│  ┌───────────────────────────────────────────────────────┐                     │
│  │ Pod B receives packet                                  │                     │
│  │ Source: 10.244.1.10:54321                             │                     │
│  │ Dest: 10.244.2.15:8080                                │                     │
│  │ (Direct pod-to-pod IPs, Service translation invisible)│                     │
│  └───────────────────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────────┘

IDENTITY-BASED SECURITY:
┌──────────────────────────────────────────────────────────────────┐
│  Traditional IP-based policies have problems:                    │
│   • Pod IPs change on restart                                    │
│   • Need to update policies constantly                           │
│   • IP lists become huge in large clusters                       │
│                                                                  │
│  Cilium's Identity-based approach:                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Every unique set of labels gets a numeric identity      │ │
│  │    Example: app=nginx,tier=frontend → Identity 12345       │ │
│  │                                                             │ │
│  │ 2. identities stored in cilium_ipcache (IP→Identity map)   │ │
│  │    When pod starts: cilium-agent assigns identity, updates  │ │
│  │    map on all nodes                                        │ │
│  │                                                             │ │
│  │ 3. NetworkPolicy translated to identity rules              │ │
│  │    Instead of: "Allow from pod IPs 10.244.x.x"             │ │
│  │    Becomes: "Allow from Identity 12345"                    │ │
│  │                                                             │ │
│  │ 4. eBPF programs check identity, not IP                    │ │
│  │    Packet arrives → extract source IP → lookup identity →  │ │
│  │    check policy → allow/deny                               │ │
│  │                                                             │ │
│  │ 5. Pod restart: New IP, same labels, same identity         │ │
│  │    Policy still works! Just update ipcache.                │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘

PERFORMANCE COMPARISON:
┌──────────────────────────────────────────────────────────────────┐
│  Traditional kube-proxy (iptables):                              │
│   • 1,000 services = ~20,000 iptables rules                      │
│   • Linear rule evaluation: O(n)                                 │
│   • Every packet traverses PREROUTING → KUBE-SERVICES → ...     │
│   • High CPU at scale                                            │
│                                                                  │
│  Cilium eBPF:                                                    │
│   • 10,000 services = 10,000 map entries                         │
│   • Hash table lookup: O(1)                                      │
│   • Direct map lookup, immediate decision                        │
│   • Constant performance regardless of service count             │
│   • Can handle 100K+ connections/sec per node                    │
└──────────────────────────────────────────────────────────────────┘
```

**Key eBPF Advantages:**
1. **Performance**: Hash map lookups vs linear rule evaluation
2. **Flexibility**: Programs can be updated without kernel recompilation
3. **Safety**: Verifier ensures programs can't crash kernel
4. **Integration**: Works at multiple layers (XDP, TC, socket, LSM)
5. **Identity-based**: Survives pod IP changes automatically

---

## Diagram 5: Service Mesh Architecture (Istio)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ISTIO SERVICE MESH ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│                          CONTROL PLANE (istiod)                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐ │  │
│  │  │    Pilot        │  │    Citadel      │  │       Galley             │ │  │
│  │  │                 │  │                 │  │                          │ │  │
│  │  │ • Service       │  │ • Certificate   │  │ • Configuration         │ │  │
│  │  │   Discovery     │  │   Management    │  │   Validation            │ │  │
│  │  │ • Traffic Mgmt  │  │ • mTLS Keys     │  │ • CRD Processing        │ │  │
│  │  │ • Envoy Config  │  │ • Identity      │  │                          │ │  │
│  │  │   (xDS APIs)    │  │   (SPIFFE)      │  │                          │ │  │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬─────────────────┘ │  │
│  │           │                    │                     │                   │  │
│  │           │                    │                     │                   │  │
│  │           │  Watches K8s API   │                     │                   │  │
│  │           └────────────────────┴─────────────────────┘                   │  │
│  │                                │                                          │  │
│  │                                ▼                                          │  │
│  │                    ┌────────────────────────┐                            │  │
│  │                    │  Kubernetes API Server │                            │  │
│  │                    │  • Services            │                            │  │
│  │                    │  • Endpoints           │                            │  │
│  │                    │  • VirtualServices     │                            │  │
│  │                    │  • DestinationRules    │                            │  │
│  │                    └────────────────────────┘                            │  │
│  │                                                                           │  │
│  │           Pushes Configuration via xDS (Envoy Discovery Service)         │  │
│  └───────────────────────────────┬───────────────────────────────────────────┘  │
│                                  │                                              │
│                                  │ gRPC Stream                                  │
│                                  ▼                                              │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA PLANE (PODS)                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    POD: frontend-v1                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                     │  │  │
│  │  │  ┌──────────────────────┐      ┌──────────────────────────────┐   │  │  │
│  │  │  │   Envoy Sidecar      │      │   Application Container      │   │  │  │
│  │  │  │   (istio-proxy)      │      │   (nginx)                    │   │  │  │
│  │  │  │                      │      │                              │   │  │  │
│  │  │  │ Listeners:           │      │ Listening on: localhost:8080│   │  │  │
│  │  │  │ • Inbound: 15006     │◄─────┤                              │   │  │  │
│  │  │  │ • Outbound: 15001    │      │ Makes calls to other         │   │  │  │
│  │  │  │                      ├─────►│ services via envoy           │   │  │  │
│  │  │  │ Admin: 15000         │      │                              │   │  │  │
│  │  │  │ Prometheus: 15020    │      └──────────────────────────────┘   │  │  │
│  │  │  │                      │                                          │  │  │
│  │  │  │ Connects to istiod   │                                          │  │  │
│  │  │  │ via xDS (gRPC)       │                                          │  │  │
│  │  │  └──────────────────────┘                                          │  │  │
│  │  │                                                                     │  │  │
│  │  │  Init Container (istio-init) ran at pod startup:                  │  │  │
│  │  │  • Programmed iptables rules to redirect all traffic to Envoy     │  │  │
│  │  │                                                                     │  │  │
│  │  │  iptables rules:                                                   │  │  │
│  │  │  PREROUTING: Inbound → redirect to 15006                          │  │  │
│  │  │  OUTPUT: Outbound → redirect to 15001                             │  │  │
│  │  │  (except traffic from UID 1337, which is Envoy itself)            │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

REQUEST FLOW THROUGH SERVICE MESH:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Scenario: frontend-v1 calls backend service (which has v1 and v2 versions)     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Step 1: Application makes HTTP call                                           │
│  ┌──────────────────────────────────────────────────────────┐                  │
│  │ frontend-v1 application container                         │                  │
│  │ http.get("http://backend:8080/api/data")                 │                  │
│  │ Connects to: backend:8080                                 │                  │
│  └────────────────────────┬─────────────────────────────────┘                  │
│                           │                                                     │
│                           │ Packet: dest=backend:8080                           │
│                           ▼                                                     │
│  Step 2: iptables intercepts (programmed by istio-init)                        │
│  ┌────────────────────────────────────────────────────────────────┐            │
│  │ iptables OUTPUT chain                                           │            │
│  │  -A OUTPUT -p tcp -j ISTIO-OUTPUT                              │            │
│  │  -A ISTIO-OUTPUT ! -d 127.0.0.1/32 -o lo                       │            │
│  │     -m owner ! --uid-owner 1337                                │            │
│  │     -j REDIRECT --to-ports 15001                               │            │
│  │                                                                 │            │
│  │ Result: Redirects to localhost:15001 (Envoy outbound listener)│            │
│  └────────────────────────────────────────────────────────────────┘            │
│                           │                                                     │
│                           ▼                                                     │
│  Step 3: Envoy Outbound Listener processes request                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ Envoy Sidecar (frontend-v1 pod)                                         │   │
│  │                                                                          │   │
│  │ Listener: 0.0.0.0:15001 (virtual outbound listener)                     │   │
│  │  ↓                                                                       │   │
│  │  Determines original destination: backend:8080                          │   │
│  │  ↓                                                                       │   │
│  │  Matches Cluster: backend.default.svc.cluster.local                     │   │
│  │  ↓                                                                       │   │
│  │  Applies Traffic Policy (from VirtualService/DestinationRule):          │   │
│  │   ┌──────────────────────────────────────────────────────────┐          │   │
│  │   │ VirtualService: backend                                  │          │   │
│  │   │   http:                                                  │          │   │
│  │   │     - match:                                             │          │   │
│  │   │         - headers:                                       │          │   │
│  │   │             user: "test"                                 │          │   │
│  │   │       route:                                             │          │   │
│  │   │         - destination: backend-v2 (100%)                │          │   │
│  │   │     - route:  # default                                 │          │   │
│  │   │         - destination: backend-v1 (90%)                 │          │   │
│  │   │         - destination: backend-v2 (10%)                 │          │   │
│  │   └──────────────────────────────────────────────────────────┘          │   │
│  │  ↓                                                                       │   │
│  │  Selects endpoint: backend-v1-abc123 (10.244.2.20:8080)                │   │
│  │  ↓                                                                       │   │
│  │  Load Balancing (Round Robin / Least Request / Random)                  │   │
│  │  ↓                                                                       │   │
│  │  mTLS Configuration:                                                    │   │
│  │   • Establishes TLS connection to backend's Envoy                       │   │
│  │   • Uses certificates from Citadel (auto-rotated)                       │   │
│  │   • SNI: backend.default.svc.cluster.local                              │   │
│  │  ↓                                                                       │   │
│  │  Telemetry Collection:                                                  │   │
│  │   • Request metrics (latency, status code)                              │   │
│  │   • Trace span created (sent to Jaeger/Zipkin)                          │   │
│  │   • Access logs                                                         │   │
│  │  ↓                                                                       │   │
│  │  Sends request to: 10.244.2.20:15006 (backend pod's inbound)           │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                           │                                                     │
│                           │ mTLS encrypted                                      │
│                           │ Network: Pod-to-Pod (via CNI)                       │
│                           ▼                                                     │
│  Step 4: Arrives at backend-v1 pod                                             │
│                           │                                                     │
│                           ▼                                                     │
│  Step 5: iptables intercepts inbound traffic                                   │
│  ┌────────────────────────────────────────────────────────────────┐            │
│  │ iptables PREROUTING chain (backend-v1 pod)                     │            │
│  │  -A PREROUTING -p tcp -j ISTIO-INBOUND                         │            │
│  │  -A ISTIO-INBOUND -p tcp --dport 8080                          │            │
│  │     -j REDIRECT --to-ports 15006                               │            │
│  │                                                                 │            │
│  │ Result: Redirects to localhost:15006 (Envoy inbound listener) │            │
│  └────────────────────────────────────────────────────────────────┘            │
│                           │                                                     │
│                           ▼                                                     │
│  Step 6: Envoy Inbound Listener processes                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ Envoy Sidecar (backend-v1 pod)                                          │   │
│  │                                                                          │   │
│  │ Listener: 0.0.0.0:15006 (virtual inbound listener)                      │   │
│  │  ↓                                                                       │   │
│  │  Terminates mTLS (extracts client identity)                             │   │
│  │   • Client: frontend-v1 (SPIFFE ID verification)                        │   │
│  │  ↓                                                                       │   │
│  │  Authorization Policy Check:                                            │   │
│  │   ┌──────────────────────────────────────────────────────────┐          │   │
│  │   │ AuthorizationPolicy: backend-policy                      │          │   │
│  │   │   action: ALLOW                                          │          │   │
│  │   │   rules:                                                 │          │   │
│  │   │     - from:                                              │          │   │
│  │   │         - source:                                        │          │   │
│  │   │             principals: ["*/sa/frontend-sa"]             │          │   │
│  │   │       to:                                                │          │   │
│  │   │         - operation:                                     │          │   │
│  │   │             methods: ["GET", "POST"]                     │          │   │
│  │   └──────────────────────────────────────────────────────────┘          │   │
│  │  ↓                                                                       │   │
│  │  Policy: ALLOW (frontend-v1 identity verified via mTLS cert)            │   │
│  │  ↓                                                                       │   │
│  │  Rate Limiting (if configured)                                          │   │
│  │  ↓                                                                       │   │
│  │  Forwards to application: localhost:8080                                │   │
│  │  ↓                                                                       │   │
│  │  Telemetry: Records inbound metrics, trace span                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                           │                                                     │
│                           ▼                                                     │
│  Step 7: Application container receives request                                │
│  ┌──────────────────────────────────────────────────────────┐                  │
│  │ backend-v1 application container                          │                  │
│  │ Receives HTTP request on localhost:8080                   │                  │
│  │ Processes and sends response                              │                  │
│  └────────────────────────┬─────────────────────────────────┘                  │
│                           │                                                     │
│                           │ Response                                            │
│                           ▼                                                     │
│  Step 8: Response flows back through Envoy → mTLS → frontend's Envoy → app    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

ENVOY CONFIGURATION (xDS APIs):
┌─────────────────────────────────────────────────────────────────────┐
│  istiod pushes configuration to Envoys via xDS protocols:           │
│                                                                     │
│  LDS (Listener Discovery Service):                                 │
│    Defines listeners (15001 outbound, 15006 inbound, etc.)         │
│                                                                     │
│  RDS (Route Discovery Service):                                    │
│    HTTP routing rules (VirtualService → Envoy routes)              │
│    Example: header-based routing, path rewrites                    │
│                                                                     │
│  CDS (Cluster Discovery Service):                                  │
│    Defines upstream clusters (backend services)                    │
│    Includes: load balancing, circuit breaking, timeouts            │
│                                                                     │
│  EDS (Endpoint Discovery Service):                                 │
│    Actual pod IPs/ports for each service                           │
│    Updated continuously as pods scale up/down                      │
│                                                                     │
│  SDS (Secret Discovery Service):                                   │
│    TLS certificates and keys for mTLS                              │
│    Rotated automatically by Citadel                                │
│                                                                     │
│  Each Envoy maintains a gRPC stream to istiod, receiving           │
│  incremental updates when configuration changes                    │
└─────────────────────────────────────────────────────────────────────┘

OBSERVABILITY:
┌─────────────────────────────────────────────────────────────────────┐
│  Every request generates telemetry:                                 │
│                                                                     │
│  Metrics (Prometheus format on :15020/stats/prometheus):           │
│   • istio_requests_total{...}                                      │
│   • istio_request_duration_milliseconds{...}                       │
│   • istio_request_bytes{...}                                       │
│   Labels: source_app, dest_app, response_code, etc.                │
│                                                                     │
│  Distributed Traces (OpenTelemetry/Zipkin):                        │
│   • Each Envoy creates spans                                       │
│   • Propagates trace context via headers (b3, traceparent)         │
│   • Sent to tracing backend (Jaeger/Zipkin)                        │
│   • Shows complete request path across services                    │
│                                                                     │
│  Access Logs (can be configured):                                  │
│   • JSON formatted logs per request                                │
│   • Sent to stdout or external collector                           │
│                                                                     │
│  Service Graph:                                                    │
│   • Kiali visualizes service topology from metrics                 │
│   • Shows traffic flow, error rates, latencies                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Service Mesh Concepts:**
1. **Transparent Interception**: iptables redirects traffic without app awareness
2. **mTLS Everywhere**: Automatic encryption with identity verification
3. **Traffic Management**: Sophisticated routing (canary, A/B, circuit breaking)
4. **Observability**: Metrics, traces, logs generated automatically
5. **Security**: AuthZ policies, identity-based access control

---

## Diagram 6: Observability Stack Integration

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CLOUD NATIVE OBSERVABILITY ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│                           APPLICATION PODS                                      │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │  │
│  │  │  App Container │  │  App Container │  │  App Container │             │  │
│  │  │                │  │                │  │                │             │  │
│  │  │ • Instrumented │  │ • Envoy Sidecar│  │ • eBPF         │             │  │
│  │  │   with OTel SDK│  │   (auto-metric)│  │   (auto-trace) │             │  │
│  │  │ • /metrics     │  │ • Prometheus   │  │ • No code      │             │  │
│  │  │   endpoint     │  │   endpoint     │  │   changes!     │             │  │
│  │  │ • stdout logs  │  │ • Access logs  │  │                │             │  │
│  │  └───┬────┬───┬───┘  └───┬────┬───┬───┘  └───┬────────────┘             │  │
│  │      │    │   │          │    │   │          │                           │  │
│  │      │    │   │          │    │   │          │                           │  │
│  └──────┼────┼───┼──────────┼────┼───┼──────────┼───────────────────────────┘  │
│         │    │   │          │    │   │          │                              │
│    ┌────┘    │   │          │    │   └──────────┼──────────┐                   │
│    │         │   │          │    │              │          │                   │
│    │ Metrics │   │ Logs     │    │              │ Traces   │                   │
│    │         │   │          │    │              │          │                   │
└────┼─────────┼───┼──────────┼────┼──────────────┼──────────┼───────────────────┘
     │         │   │          │    │              │          │
     ▼         │   ▼          │    ▼              │          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            METRICS PIPELINE                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                     Prometheus Server                                     │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Scrape Configuration (generated from K8s SD):                      │  │  │
│  │  │                                                                     │  │  │
│  │  │ scrape_configs:                                                    │  │  │
│  │  │   - job_name: 'kubernetes-pods'                                   │  │  │
│  │  │     kubernetes_sd_configs:                                        │  │  │
│  │  │       - role: pod                                                 │  │  │
│  │  │     relabel_configs:                                              │  │  │
│  │  │       # Scrape pods with prometheus.io/scrape: "true"            │  │  │
│  │  │       - source_labels: [__meta_kubernetes_pod_annotation_        │  │  │
│  │  │           prometheus_io_scrape]                                   │  │  │
│  │  │         action: keep                                              │  │  │
│  │  │         regex: true                                               │  │  │
│  │  │       # Extract port from annotation                             │  │  │
│  │  │       - source_labels: [__meta_kubernetes_pod_annotation_        │  │  │
│  │  │           prometheus_io_port]                                     │  │  │
│  │  │         target_label: __address__                                 │  │  │
│  │  │       # Add pod labels as metrics labels                          │  │  │
│  │  │       - action: labelmap                                          │  │  │
│  │  │         regex: __meta_kubernetes_pod_label_(.+)                   │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Time Series Database (TSDB):                                       │  │  │
│  │  │  • Stores metrics with labels                                     │  │  │
│  │  │  • Compression and downsampling                                   │  │  │
│  │  │  • Retention policies (e.g., 15 days)                             │  │  │
│  │  │                                                                     │  │  │
│  │  │ Example metric stored:                                            │  │  │
│  │  │  http_requests_total{                                             │  │  │
│  │  │    job="kubernetes-pods",                                         │  │  │
│  │  │    namespace="default",                                           │  │  │
│  │  │    pod="frontend-abc123",                                         │  │  │
│  │  │    app="frontend",                                                │  │  │
│  │  │    method="GET",                                                  │  │  │
│  │  │    status="200"                                                   │  │  │
│  │  │  } = 1523                                                         │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ PromQL Query Engine:                                               │  │  │
│  │  │  • rate(http_requests_total[5m])                                  │  │  │
│  │  │  • histogram_quantile(0.95,                                       │  │  │
│  │  │      rate(http_request_duration_seconds_bucket[5m]))              │  │  │
│  │  │  • sum by (app) (...)                                             │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────┬───────────────────────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────────────────────┘
                                │ Query API
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            LOGGING PIPELINE                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    Fluent Bit (DaemonSet)                                 │  │
│  │  Runs on every node, collects logs from:                                 │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Input Sources:                                                      │  │  │
│  │  │  1. Container Runtime Logs:                                        │  │  │
│  │  │     /var/log/containers/*.log                                      │  │  │
│  │  │     (symlinks to actual container logs)                            │  │  │
│  │  │                                                                     │  │  │
│  │  │  2. Systemd Logs:                                                  │  │  │
│  │  │     kubelet, container runtime logs                                │  │  │
│  │  │                                                                     │  │  │
│  │  │  3. Kernel Logs (optional)                                         │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Processing Pipeline:                                                │  │  │
│  │  │  1. Parse JSON from container logs                                 │  │  │
│  │  │  2. Kubernetes metadata enrichment:                                │  │  │
│  │  │     • Extract pod name from filename                               │  │  │
│  │  │     • Query K8s API for pod metadata                               │  │  │
│  │  │     • Add labels: namespace, app, pod, container                   │  │  │
│  │  │  3. Filter/exclude (e.g., health check logs)                       │  │  │
│  │  │  4. Multiline parsing (stack traces)                               │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Output:                                                             │  │  │
│  │  │  • Forward to Loki (HTTP API)                                      │  │  │
│  │  │  • Labels extracted for indexing                                   │  │  │
│  │  │  • Log line stored as string                                       │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────┬───────────────────────────────────────────────┘  │
│                              │                                                  │
│                              ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         Grafana Loki                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Architecture:                                                       │  │  │
│  │  │                                                                     │  │  │
│  │  │  Distributor → Ingester → Store (Object Storage: S3/GCS)           │  │  │
│  │  │       ↓            ↓                                                │  │  │
│  │  │    Validates   Writes chunks                                       │  │  │
│  │  │    labels      to object store                                     │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Index Strategy (Labels Only):                                      │  │  │
│  │  │   {namespace="default", app="frontend", pod="frontend-abc"}        │  │  │
│  │  │                                                                     │  │  │
│  │  │ Log content is NOT indexed, only labels!                           │  │  │
│  │  │ This makes Loki much cheaper than Elasticsearch                    │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ LogQL Query Examples:                                              │  │  │
│  │  │  {namespace="prod", app="backend"} |= "error"                      │  │  │
│  │  │  {namespace="prod"} | json | level="error"                         │  │  │
│  │  │  rate({app="nginx"}[5m])                                           │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────┬───────────────────────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────────────────────┘
                                │ Query API
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TRACING PIPELINE                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                  OpenTelemetry Collector (DaemonSet/Deployment)           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Receivers (accept traces):                                         │  │  │
│  │  │  • OTLP (gRPC and HTTP)                                            │  │  │
│  │  │  • Jaeger                                                          │  │  │
│  │  │  • Zipkin                                                          │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Processors (transform traces):                                     │  │  │
│  │  │  • batch (batches for efficiency)                                  │  │  │
│  │  │  • k8sattributes (adds pod/namespace metadata)                     │  │  │
│  │  │  • probabilistic sampler (reduce volume)                           │  │  │
│  │  │  • tail sampler (keep error traces)                                │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Exporters (send to backends):                                      │  │  │
│  │  │  • Jaeger                                                          │  │  │
│  │  │  • Tempo (Grafana's tracing backend)                               │  │  │
│  │  │  • Prometheus (for trace-derived metrics)                          │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────┬───────────────────────────────────────────────┘  │
│                              │                                                  │
│                              ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                          Jaeger Backend                                   │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Components:                                                         │  │  │
│  │  │  • Collector: Receives traces                                      │  │  │
│  │  │  • Storage: Cassandra/Elasticsearch/Badger                         │  │  │
│  │  │  • Query Service: API for retrieving traces                        │  │  │
│  │  │  • UI: Web interface for visualization                             │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Trace Structure:                                                    │  │  │
│  │  │                                                                     │  │  │
│  │  │  Trace ID: abc123                                                  │  │  │
│  │  │    Span: frontend (root)         [0ms────────100ms]                │  │  │
│  │  │      Span: backend-v1             [10ms───70ms]                    │  │  │
│  │  │        Span: database-query        [15ms-50ms]                     │  │  │
│  │  │        Span: cache-lookup          [55ms-60ms]                     │  │  │
│  │  │      Span: external-api            [75ms───95ms]                   │  │  │
│  │  │                                                                     │  │  │
│  │  │  Each span includes:                                               │  │  │
│  │  │   • Service name, operation name                                   │  │  │
│  │  │   • Start time, duration                                           │  │  │
│  │  │   • Tags (http.method, error, k8s.pod, etc.)                       │  │  │
│  │  │   • Logs (events during the span)                                  │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────┬───────────────────────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────────────────────┘
                                │ Query API
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        VISUALIZATION & ALERTING                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                            Grafana                                        │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Data Sources:                                                       │  │  │
│  │  │  • Prometheus (metrics)                                             │  │  │
│  │  │  • Loki (logs)                                                      │  │  │
│  │  │  • Jaeger/Tempo (traces)                                            │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Unified Dashboard Example:                                          │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │ Service: frontend                                             │  │  │  │
│  │  │  │                                                               │  │  │  │
│  │  │  │ Request Rate (Prometheus):                                   │  │  │  │
│  │  │  │   [Graph showing rate(http_requests_total[5m])]              │  │  │  │
│  │  │  │                                                               │  │  │  │
│  │  │  │ Error Logs (Loki):                                           │  │  │  │
│  │  │  │   {app="frontend"} |= "error" | json                         │  │  │  │
│  │  │  │   [Table of error logs with timestamp, message]              │  │  │  │
│  │  │  │   Click log → Links to trace in Jaeger                       │  │  │  │
│  │  │  │                                                               │  │  │  │
│  │  │  │ Trace Visualization:                                         │  │  │  │
│  │  │  │   Trace ID from log: Click to view in Jaeger                 │  │  │  │
│  │  │  │   [Waterfall showing entire request path]                    │  │  │  │
│  │  │  └──────────────────────────────────────────────────────────────┘  │  │  │
│  │  │                                                                     │  │  │
│  │  │ Correlation: Metrics → Logs → Traces                                │  │  │
│  │  │  1. Metric spike detected                                          │  │  │
│  │  │  2. Drill into logs for that time period                           │  │  │
│  │  │  3. Find trace ID in logs                                          │  │  │
│  │  │  4. View full trace to identify bottleneck                         │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Alerting:                                                           │  │  │
│  │  │  • Alert rules defined in Grafana or Prometheus                    │  │  │
│  │  │  • Notification channels: Slack, PagerDuty, Email                  │  │  │
│  │  │  • Example: Alert if error rate > 5% for 5 minutes                 │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

EBPF-BASED AUTO-INSTRUMENTATION (Pixie):
┌─────────────────────────────────────────────────────────────────────┐
│  Pixie eBPF Agents (DaemonSet)                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ eBPF Programs attached to:                                    │  │
│  │  • syscalls (read, write, sendto, recvfrom)                   │  │
│  │  • SSL/TLS functions (openssl, boringssl)                     │  │
│  │  • MySQL, PostgreSQL wire protocols                           │  │
│  │                                                                │  │
│  │ For every network call:                                       │  │
│  │  1. eBPF intercepts syscall                                   │  │
│  │  2. Captures request/response data                            │  │
│  │  3. Parses protocol (HTTP, gRPC, MySQL, etc.)                 │  │
│  │  4. Extracts metadata (method, path, SQL query)               │  │
│  │  5. Correlates req/resp into trace spans                      │  │
│  │  6. Streams to Pixie backend via ring buffers                 │  │
│  │                                                                │  │
│  │ Result: Full observability without code changes!              │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Observability Three Pillars:**
1. **Metrics**: Aggregated numerical data, efficient for alerting
2. **Logs**: Detailed event records, good for debugging specific issues
3. **Traces**: Request path across services, essential for distributed systems

**Key Integration Points:**
- **Trace Context Propagation**: HTTP headers (traceparent, b3) carry trace IDs across services
- **Exemplars**: Link metrics to traces (Prometheus can store trace IDs with samples)
- **Correlation IDs**: Logs include trace IDs, enabling metrics→logs→traces navigation

---

## Diagram 7: GitOps and CI/CD Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          GITOPS ARCHITECTURE (Flux/ArgoCD)                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         GIT REPOSITORIES                                  │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Application Repo (github.com/org/app)                              │  │  │
│  │  │  • Source code                                                     │  │  │
│  │  │  • Dockerfile                                                      │  │  │
│  │  │  • CI configuration (.github/workflows/ci.yaml)                   │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ GitOps Repo (github.com/org/gitops)                                │  │  │
│  │  │  apps/                                                             │  │  │
│  │  │    frontend/                                                       │  │  │
│  │  │      base/                                                         │  │  │
│  │  │        deployment.yaml                                             │  │  │
│  │  │        service.yaml                                                │  │  │
│  │  │        kustomization.yaml                                          │  │  │
│  │  │      overlays/                                                     │  │  │
│  │  │        dev/                                                        │  │  │
│  │  │          kustomization.yaml (image: v1.2.3-dev)                   │  │  │
│  │  │          replicas.yaml (replicas: 1)                              │  │  │
│  │  │        staging/                                                    │  │  │
│  │  │          kustomization.yaml (image: v1.2.3-rc1)                   │  │  │
│  │  │          replicas.yaml (replicas: 2)                              │  │  │
│  │  │        prod/                                                       │  │  │
│  │  │          kustomization.yaml (image: v1.2.2)                       │  │  │
│  │  │          replicas.yaml (replicas: 5)                              │  │  │
│  │  │                                                                     │  │  │
│  │  │  infrastructure/                                                   │  │  │
│  │  │    istio/                                                          │  │  │
│  │  │    cert-manager/                                                   │  │  │
│  │  │    monitoring/                                                     │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                           │                              │
                           │                              │
                           ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               CI PIPELINE                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Trigger: Developer pushes code to application repo                            │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ Step 1: Run Tests                                                         │  │
│  │  • Unit tests                                                             │  │
│  │  • Integration tests                                                      │  │
│  │  • Security scanning (SAST)                                               │  │
│  └────────────────────────────┬─────────────────────────────────────────────┘  │
│                               │ Pass                                           │
│                               ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ Step 2: Build Container Image                                            │  │
│  │  • docker build -t myapp:${GIT_SHA} .                                    │  │
│  │  • Image layers cached for speed                                         │  │
│  └────────────────────────────┬─────────────────────────────────────────────┘  │
│                               │                                                 │
│                               ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ Step 3: Scan Image                                                        │  │
│  │  • Trivy scan for CVEs                                                    │  │
│  │  • Fail build if critical vulnerabilities found                          │  │
│  └────────────────────────────┬─────────────────────────────────────────────┘  │
│                               │ Pass                                           │
│                               ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ Step 4: Push Image to Registry                                           │  │
│  │  • docker push registry.example.com/myapp:${GIT_SHA}                     │  │
│  │  • Also tag as: myapp:v1.2.3, myapp:latest                               │  │
│  └────────────────────────────┬─────────────────────────────────────────────┘  │
│                               │                                                 │
│                               ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ Step 5: Update GitOps Repo (for dev environment)                         │  │
│  │  • Clone gitops repo                                                     │  │
│  │  • Update apps/frontend/overlays/dev/kustomization.yaml:                │  │
│  │    newImage: registry.example.com/myapp:${GIT_SHA}                      │  │
│  │  • Git commit and push                                                   │  │
│  │  • Message: "Update frontend to ${GIT_SHA}"                              │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  Note: Staging/Prod updated via manual PR approval or automated promotion      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                │ Git commit triggers sync
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FLUX CONTROL PLANE                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    Source Controller                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ GitRepository Resource:                                             │  │  │
│  │  │   apiVersion: source.toolkit.fluxcd.io/v1                           │  │  │
│  │  │   kind: GitRepository                                               │  │  │
│  │  │   metadata:                                                         │  │  │
│  │  │     name: gitops-repo                                               │  │  │
│  │  │   spec:                                                             │  │  │
│  │  │     interval: 1m  # Poll every minute                               │  │  │
│  │  │     url: https://github.com/org/gitops                              │  │  │
│  │  │     ref:                                                            │  │  │
│  │  │       branch: main                                                  │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  Responsibilities:                                                        │  │
│  │  • Polls Git repo every interval                                         │  │
│  │  • Detects changes (new commit SHA)                                      │  │
│  │  • Fetches updated manifests                                             │  │
│  │  • Makes them available to other controllers                             │  │
│  └───────────────────────────┬───────────────────────────────────────────────┘  │
│                              │ New revision available                          │
│                              ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    Kustomize Controller                                   │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Kustomization Resource:                                             │  │  │
│  │  │   apiVersion: kustomize.toolkit.fluxcd.io/v1                        │  │  │
│  │  │   kind: Kustomization                                               │  │  │
│  │  │   metadata:                                                         │  │  │
│  │  │     name: frontend-dev                                              │  │  │
│  │  │   spec:                                                             │  │  │
│  │  │     interval: 5m                                                    │  │  │
│  │  │     sourceRef:                                                      │  │  │
│  │  │       kind: GitRepository                                           │  │  │
│  │  │       name: gitops-repo                                             │  │  │
│  │  │     path: ./apps/frontend/overlays/dev                             │  │  │
│  │  │     prune: true  # Delete resources not in Git                     │  │  │
│  │  │     wait: true   # Wait for resources to be ready                  │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  Reconciliation Loop:                                                     │  │
│  │  1. Source controller signals new revision                               │  │
│  │  2. Fetch manifests from path                                            │  │
│  │  3. Run `kustomize build` to generate final YAML                         │  │
│  │  4. Compare with current cluster state                                   │  │
│  │  5. If different:                                                         │  │
│  │     • Apply changes to cluster (kubectl apply)                           │  │
│  │     • Prune resources not in Git (if enabled)                            │  │
│  │     • Wait for health checks                                             │  │
│  │  6. Update status (Ready/Failed)                                         │  │
│  │  7. Emit events for notifications                                        │  │
│  └───────────────────────────┬───────────────────────────────────────────────┘  │
│                              │ Apply to cluster                                │
│                              ▼                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         KUBERNETES CLUSTER (DEV)                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ Before Sync:                                                              │  │
│  │   Deployment: frontend                                                    │  │
│  │     image: registry.example.com/myapp:abc123  (old)                      │  │
│  │     replicas: 1                                                           │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                               │                                                 │
│                               │ Flux applies changes                            │
│                               ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ After Sync:                                                               │  │
│  │   Deployment: frontend                                                    │  │
│  │     image: registry.example.com/myapp:def456  (new)                      │  │
│  │     replicas: 1                                                           │  │
│  │                                                                           │  │
│  │ Kubernetes reconciliation:                                                │  │
│  │  1. Deployment controller sees spec change                               │  │
│  │  2. Updates ReplicaSet with new image                                    │  │
│  │  3. RollingUpdate strategy:                                              │  │
│  │     • Create new pod with new image                                      │  │
│  │     • Wait for readiness probe                                           │  │
│  │     • Terminate old pod                                                  │  │
│  │  4. New pod running, old pod terminated                                  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

DRIFT DETECTION AND REMEDIATION:
┌──────────────────────────────────────────────────────────────────────┐
│  Scenario: Someone manually edits a deployment                       │
│                                                                      │
│  1. kubectl edit deployment frontend                                 │
│     Changes replicas from 1 → 3                                     │
│                                                                      │
│  2. Flux detects drift on next reconciliation (within 5 minutes):   │
│     • Compares desired state (Git) vs actual state (cluster)        │
│     • Finds difference in replica count                             │
│                                                                      │
│  3. Flux reverts the change:                                        │
│     • Applies Git version (replicas: 1)                             │
│     • Kubernetes scales back down to 1                              │
│     • Emits event: "Reverted manual change"                         │
│                                                                      │
│  Result: Cluster always matches Git (Git is source of truth)        │
└──────────────────────────────────────────────────────────────────────┘

PROGRESSIVE DELIVERY WITH FLAGGER:
┌──────────────────────────────────────────────────────────────────────────────┐
│  Canary Deployment Automation                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Canary Resource:                                                        │  │
│  │   apiVersion: flagger.app/v1beta1                                      │  │
│  │   kind: Canary                                                         │  │
│  │   metadata:                                                            │  │
│  │     name: frontend                                                     │  │
│  │   spec:                                                                │  │
│  │     targetRef:                                                         │  │
│  │       apiVersion: apps/v1                                              │  │
│  │       kind: Deployment                                                 │  │
│  │       name: frontend                                                   │  │
│  │     service:                                                           │  │
│  │       port: 80                                                         │  │
│  │     analysis:                                                          │  │
│  │       interval: 1m                                                     │  │
│  │       threshold: 5  # Max failed checks before rollback               │  │
│  │       maxWeight: 50 # Max traffic to canary                           │  │
│  │       stepWeight: 10 # Increase by 10% each step                      │  │
│  │       metrics:                                                         │  │
│  │         - name: request-success-rate                                   │  │
│  │           thresholdRange:                                              │  │
│  │             min: 99  # Must maintain 99% success rate                  │  │
│  │         - name: request-duration                                       │  │
│  │           thresholdRange:                                              │  │
│  │             max: 500  # P99 latency must be < 500ms                    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  Automated Canary Process:                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 1: New image detected in deployment                              │  │
│  │   Git: frontend image updated to v1.3.0                                │  │
│  │   Flux applies change                                                  │  │
│  │   Flagger detects deployment change                                    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                               ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 2: Initialize Canary                                             │  │
│  │   • Create canary deployment (frontend-canary) with v1.3.0             │  │
│  │   • Keep primary deployment (frontend-primary) on v1.2.2               │  │
│  │   • Route 0% traffic to canary (via Istio VirtualService)              │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                               ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 3: Progressive Traffic Shift                                     │  │
│  │                                                                         │  │
│  │ Step 1: 10% traffic to canary                                          │  │
│  │   Wait 1 minute, check metrics:                                        │  │
│  │   ✓ Success rate: 99.5% (> 99% threshold)                              │  │
│  │   ✓ P99 latency: 320ms (< 500ms threshold)                             │  │
│  │                                                                         │  │
│  │ Step 2: 20% traffic to canary                                          │  │
│  │   Wait 1 minute, check metrics: ✓ Pass                                 │  │
│  │                                                                         │  │
│  │ Step 3: 30% traffic... ✓ Pass                                          │  │
│  │ Step 4: 40% traffic... ✓ Pass                                          │  │
│  │ Step 5: 50% traffic... ✓ Pass (maxWeight reached)                      │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                               ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 4: Promotion                                                     │  │
│  │   • All checks passed                                                  │  │
│  │   • Update primary deployment to v1.3.0                                │  │
│  │   • Route 100% traffic to primary                                      │  │
│  │   • Scale down canary deployment to 0                                  │  │
│  │   • Send success notification                                          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  Rollback Scenario:                                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ If at any step metrics fail threshold:                                 │  │
│  │   Example: Step 3 (30% traffic)                                        │  │
│  │     ✗ Success rate: 97% (below 99% threshold)                          │  │
│  │                                                                         │  │
│  │ Automatic rollback:                                                    │  │
│  │   • Route 0% traffic to canary immediately                             │  │
│  │   • Keep primary on v1.2.2 (old stable version)                        │  │
│  │   • Scale down canary                                                  │  │
│  │   • Send failure alert to team                                         │  │
│  │   • Mark canary as "Failed"                                            │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

**GitOps Principles:**
1. **Declarative**: Entire system state declared in Git
2. **Versioned**: Git history = deployment history
3. **Immutable**: Changes via new commits, not manual edits
4. **Automated**: Controllers automatically sync Git → cluster
5. **Auditable**: Every change has commit, author, timestamp

---

## Diagram 8: Security Stack Integration

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      CLOUD NATIVE SECURITY LAYERS                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│                         IMAGE BUILD & SUPPLY CHAIN                              │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │  Developer Workflow:                                                     │  │
│  │  1. Write code → 2. Build image → 3. Scan → 4. Sign → 5. Push            │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Build Stage (Docker/Buildpacks)                                    │  │  │
│  │  │   docker build -t myapp:v1 .                                       │  │  │
│  │  │                                                                     │  │  │
│  │  │ Best Practices:                                                    │  │  │
│  │  │   • Multi-stage builds (minimize final image)                      │  │  │
│  │  │   • Distroless base images (no shell, package manager)             │  │  │
│  │  │   • Non-root USER in Dockerfile                                    │  │  │
│  │  │   • .dockerignore to exclude secrets                               │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                             ▼                                             │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Trivy Scan (Vulnerability Detection)                               │  │  │
│  │  │   trivy image --severity HIGH,CRITICAL myapp:v1                    │  │  │
│  │  │                                                                     │  │  │
│  │  │ Scans for:                                                         │  │  │
│  │  │   • Known CVEs in OS packages                                      │  │  │
│  │  │   • Vulnerabilities in language dependencies                       │  │  │
│  │  │   • Misconfigurations (weak passwords, exposed ports)              │  │  │
│  │  │   • Secrets accidentally committed (API keys, passwords)           │  │  │
│  │  │                                                                     │  │  │
│  │  │ Output:                                                            │  │  │
│  │  │   myapp:v1 (alpine 3.14)                                           │  │  │
│  │  │   ════════════════════════════                                     │  │  │
│  │  │   Total: 15 (HIGH: 3, MEDIUM: 12)                                  │  │  │
│  │  │                                                                     │  │  │
│  │  │   HIGH: CVE-2021-12345 (openssl 1.1.1)                             │  │  │
│  │  │         Fixed in: 1.1.1k                                           │  │  │
│  │  │                                                                     │  │  │
│  │  │ CI/CD Integration: Fail build if HIGH/CRITICAL found              │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                             ▼                                             │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Cosign (Image Signing with Sigstore)                               │  │  │
│  │  │   cosign sign registry.io/myapp:v1                                 │  │  │
│  │  │                                                                     │  │  │
│  │  │ Process:                                                           │  │  │
│  │  │  1. Generate signature of image manifest                           │  │  │
│  │  │  2. Sign with private key (or keyless via OIDC)                    │  │  │
│  │  │  3. Store signature in registry alongside image                    │  │  │
│  │  │  4. Record in transparency log (Rekor)                             │  │  │
│  │  │                                                                     │  │  │
│  │  │ Attestations can also include:                                    │  │  │
│  │  │  • SBOM (Software Bill of Materials)                               │  │  │
│  │  │  • Build provenance (where/how it was built)                       │  │  │
│  │  │  • Scan results                                                    │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Image pushed to registry
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ADMISSION CONTROL (DEPLOY TIME)                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    Kubernetes API Server                                  │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Request: kubectl apply -f deployment.yaml                          │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                             ▼                                             │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Authentication & Authorization (RBAC)                              │  │  │
│  │  │   • Verify user identity                                           │  │  │
│  │  │   • Check RBAC permissions                                         │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                             ▼                                             │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Admission Webhooks (Mutating & Validating)                         │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────┬───────────────────────────────────────────────────────┘  │
│                      │                                                          │
│     ┌────────────────┼────────────────┬─────────────────┐                      │
│     │                │                │                 │                      │
│     ▼                ▼                ▼                 ▼                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  ┌──────────────┐             │
│  │ OPA/     │  │ Cosign   │  │ Pod Security  │  │ Istio        │             │
│  │Gatekeeper│  │ Policy   │  │ Admission     │  │ Sidecar      │             │
│  │          │  │Controller│  │               │  │ Injector     │             │
│  └────┬─────┘  └────┬─────┘  └───────┬───────┘  └──────┬───────┘             │
│       │             │                │                 │                      │
└───────┼─────────────┼────────────────┼─────────────────┼──────────────────────┘
        │             │                │                 │
        ▼             ▼                ▼                 ▼

┌──────────────────────────────────────────────────────────────────────────────┐
│ OPA/Gatekeeper Policy Enforcement                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ ConstraintTemplate (Policy Definition):                                │  │
│  │   apiVersion: templates.gatekeeper.sh/v1                               │  │
│  │   kind: ConstraintTemplate                                             │  │
│  │   metadata:                                                            │  │
│  │     name: k8srequiredlabels                                            │  │
│  │   spec:                                                                │  │
│  │     crd:                                                               │  │
│  │       spec:                                                            │  │
│  │         names:                                                         │  │
│  │           kind: K8sRequiredLabels                                      │  │
│  │     targets:                                                           │  │
│  │       - target: admission.k8s.gatekeeper.sh                            │  │
│  │         rego: |                                                        │  │
│  │           package k8srequiredlabels                                    │  │
│  │           violation[{"msg": msg}] {                                    │  │
│  │             provided := {label | input.review.object.metadata.         │  │
│  │                          labels[label]}                                │  │
│  │             required := {label | label := input.parameters.            │  │
│  │                          labels[_]}                                    │  │
│  │             missing := required - provided                             │  │
│  │             count(missing) > 0                                         │  │
│  │             msg := sprintf("Missing required labels: %v",              │  │
│  │                            [missing])                                  │  │
│  │           }                                                            │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Constraint (Policy Instance):                                          │  │
│  │   apiVersion: constraints.gatekeeper.sh/v1beta1                        │  │
│  │   kind: K8sRequiredLabels                                              │  │
│  │   metadata:                                                            │  │
│  │     name: deployment-must-have-labels                                  │  │
│  │   spec:                                                                │  │
│  │     match:                                                             │  │
│  │       kinds:                                                           │  │
│  │         - apiGroups: ["apps"]                                          │  │
│  │           kinds: ["Deployment"]                                        │  │
│  │     parameters:                                                        │  │
│  │       labels: ["app", "team", "environment"]                           │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  Additional Common Policies:                                                 │
│   • Container must not run as root (runAsNonRoot: true)                      │
│   • Resource limits required (CPU/memory requests and limits)                │  │
│   • Images must come from approved registries                                │
│   • Privileged containers prohibited                                         │
│   • Host network/PID/IPC namespaces disallowed                               │
│   • Immutable root filesystem (readOnlyRootFilesystem: true)                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ Cosign Policy Controller (Image Verification)                                │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ ClusterImagePolicy:                                                    │  │
│  │   apiVersion: policy.sigstore.dev/v1beta1                              │  │
│  │   kind: ClusterImagePolicy                                             │  │
│  │   metadata:                                                            │  │
│  │     name: image-signature-verification                                 │  │
│  │   spec:                                                                │  │
│  │     images:                                                            │  │
│  │       - glob: "registry.io/myorg/*"                                    │  │
│  │     authorities:                                                       │  │
│  │       - keyless:                                                       │  │
│  │           url: https://fulcio.sigstore.dev                             │  │
│  │           identities:                                                  │  │
│  │             - issuer: https://token.actions.githubusercontent.com      │  │
│  │               subject: https://github.com/myorg/myrepo/.github/        │  │
│  │                        workflows/ci.yaml                               │  │
│  │       - attestations:                                                  │  │
│  │           - name: must-have-sbom                                       │  │
│  │             predicateType: https://spdx.dev/Document                   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  Verification Process:                                                       │
│  1. Deployment specifies image: registry.io/myorg/app:v1                    │
│  2. Policy controller intercepts                                             │
│  3. Fetches signatures from registry                                         │
│  4. Verifies signature using public key/Fulcio                               │
│  5. Checks attestations (SBOM present?)                                      │
│  6. If valid: Allow. If invalid: Deny with error message                     │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ All policies passed
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         RUNTIME SECURITY                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │               Falco/Tetragon (eBPF-based Detection)                       │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ eBPF Programs attached to:                                         │  │  │
│  │  │  • execve (process execution)                                      │  │  │
│  │  │  • open/openat (file access)                                       │  │  │
│  │  │  • connect/accept (network connections)                            │  │  │
│  │  │  • setuid/setgid (privilege changes)                               │  │  │
│  │  │  • ptrace (debugging)                                              │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Detection Rules:                                                    │  │  │
│  │  │                                                                     │  │  │
│  │  │ 1. Shell Spawned in Container:                                     │  │  │
│  │  │    - rule: Terminal shell in container                             │  │  │
│  │  │      desc: A shell was spawned in a container                      │  │  │
│  │  │      condition: >                                                  │  │  │
│  │  │        spawned_process and container and                           │  │  │
│  │  │        proc.name in (bash, sh, zsh) and                            │  │  │
│  │  │        not parent_is_entrypoint                                    │  │  │
│  │  │      output: >                                                     │  │  │
│  │  │        Shell spawned (user=%user.name command=%proc.cmdline        │  │  │
│  │  │         container=%container.name pod=%k8s.pod.name)               │  │  │
│  │  │      priority: WARNING                                             │  │  │
│  │  │                                                                     │  │  │
│  │  │ 2. Sensitive File Access:                                          │  │  │
│  │  │    - rule: Read sensitive file                                     │  │  │
│  │  │      condition: >                                                  │  │  │
│  │  │        open_read and container and                                 │  │  │
│  │  │        fd.name in (/etc/shadow, /etc/passwd,                       │  │  │
│  │  │                    /root/.ssh/id_rsa)                              │  │  │
│  │  │      priority: CRITICAL                                            │  │  │
│  │  │                                                                     │  │  │
│  │  │ 3. Outbound Connection to Known Malicious IP:                      │  │  │
│  │  │    - rule: Outbound connection to crypto mining pool               │  │  │
│  │  │      condition: >                                                  │  │  │
│  │  │        outbound and container and                                  │  │  │
│  │  │        fd.sip in (known_mining_pools)                              │  │  │
│  │  │      priority: CRITICAL                                            │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Alert Flow:                                                         │  │  │
│  │  │  eBPF detects event → Falco evaluates rules → Alert generated →   │  │  │
│  │  │  Send to: Slack, PagerDuty, SIEM, Webhook                          │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │               KubeArmor (Policy Enforcement)                              │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ KubeArmorPolicy:                                                    │  │  │
│  │  │   apiVersion: security.kubearmor.com/v1                             │  │  │
│  │  │   kind: KubeArmorPolicy                                             │  │  │
│  │  │   metadata:                                                         │  │  │
│  │  │     name: restrict-wordpress                                        │  │  │
│  │  │   spec:                                                             │  │  │
│  │  │     selector:                                                       │  │  │
│  │  │       matchLabels:                                                  │  │  │
│  │  │         app: wordpress                                              │  │  │
│  │  │     process:                                                        │  │  │
│  │  │       matchPaths:                                                   │  │  │
│  │  │         - path: /bin/bash                                           │  │  │
│  │  │           action: Block  # Prevent shell execution                 │  │  │
│  │  │         - path: /usr/bin/wget                                       │  │  │
│  │  │           action: Block  # Prevent downloads                        │  │  │
│  │  │     file:                                                           │  │  │
│  │  │       matchDirectories:                                             │  │  │
│  │  │         - dir: /var/www/html/                                       │  │  │
│  │  │           recursive: true                                           │  │  │
│  │  │           action: Allow  # Application files                        │  │  │
│  │  │         - dir: /etc/                                                │  │  │
│  │  │           recursive: true                                           │  │  │
│  │  │           action: Block  # Prevent config tampering                 │  │  │
│  │  │     network:                                                        │  │  │
│  │  │       matchProtocols:                                               │  │  │
│  │  │         - protocol: tcp                                             │  │  │
│  │  │           fromSource:                                               │  │  │
│  │  │             - port: 3306  # MySQL                                   │  │  │
│  │  │           action: Allow                                             │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  │  Enforcement via eBPF LSM hooks:                                         │  │
│  │   • Blocks operations at kernel level (can't be bypassed)                │  │
│  │   • Even if attacker gains shell, can't execute commands                 │  │
│  │   • Defense in depth beyond admission control                            │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

NETWORK SECURITY (Cilium Network Policies):
┌──────────────────────────────────────────────────────────────────────────────┐
│  CiliumNetworkPolicy (L3/L4/L7):                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ apiVersion: cilium.io/v2                                               │  │
│  │ kind: CiliumNetworkPolicy                                              │  │
│  │ metadata:                                                              │  │
│  │   name: backend-policy                                                 │  │
│  │ spec:                                                                  │  │
│  │   endpointSelector:                                                    │  │
│  │     matchLabels:                                                       │  │
│  │       app: backend                                                     │  │
│  │   ingress:                                                             │  │
│  │     - fromEndpoints:                                                   │  │
│  │         - matchLabels:                                                 │  │
│  │             app: frontend                                              │  │
│  │       toPorts:                                                         │  │
│  │         - ports:                                                       │  │
│  │             - port: "8080"                                             │  │
│  │               protocol: TCP                                            │  │
│  │           rules:                                                       │  │
│  │             http:  # L7 rules                                          │  │
│  │               - method: "GET"                                          │  │
│  │                 path: "/api/.*"                                        │  │
│  │               - method: "POST"                                         │  │
│  │                 path: "/api/data"                                      │  │
│  │   egress:                                                              │  │
│  │     - toEndpoints:                                                     │  │
│  │         - matchLabels:                                                 │  │
│  │             app: database                                              │  │
│  │       toPorts:                                                         │  │
│  │         - ports:                                                       │  │
│  │             - port: "5432"                                             │  │
│  │     - toFQDNs:  # DNS-based egress                                     │  │
│  │         - matchName: "api.example.com"                                 │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  Enforcement: eBPF programs on veth interfaces check identity + ports + L7    │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Security Defense in Depth:**
1. **Build Time**: Scan images, enforce base image policies
2. **Deploy Time**: Verify signatures, enforce pod security standards, validate configurations
3. **Runtime**: Monitor behavior, enforce runtime policies, detect anomalies
4. **Network**: Segment traffic, enforce L3-L7 policies, encrypt in transit

---

## Diagram 9: Complete Request Flow - All Layers Combined

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    END-TO-END REQUEST FLOW                                      │
│          (External Client → Ingress → Service Mesh → App → Database)           │
└─────────────────────────────────────────────────────────────────────────────────┘

USER MAKES REQUEST
│
▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 1: DNS Resolution                                                │
│   User: curl https://myapp.example.com/api/users                     │
│   DNS: myapp.example.com → 203.0.113.10 (LoadBalancer IP)           │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 2: Cloud LoadBalancer                                           │
│   • Receives HTTPS request on 203.0.113.10:443                      │
│   • TLS termination (or passthrough)                                 │
│   • Selects backend node (Node 1: 192.168.1.10:30080)               │
│   • Forwards request                                                 │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 3: Node 1 - Ingress Controller Pod                              │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ NGINX Ingress Controller (or Istio Gateway)                    │  │
│  │                                                                 │  │
│  │ Listening on NodePort 30080                                    │  │
│  │                                                                 │  │
│  │ Ingress Rules:                                                 │  │
│  │   Host: myapp.example.com                                      │  │
│  │   Path: /api/* → Service: frontend-svc:80                      │  │
│  │                                                                 │  │
│  │ TLS: Cert from cert-manager (auto-renewed Let's Encrypt)       │  │
│  │                                                                 │  │
│  │ Actions:                                                        │  │
│  │  • Terminate TLS                                               │  │
│  │  • Match host + path                                           │  │
│  │  • Add X-Forwarded-* headers                                   │  │
│  │  • Forward to: frontend-svc ClusterIP (10.96.10.50:80)         │  │
│  └────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 4: Service Load Balancing (kube-proxy or Cilium eBPF)           │
│                                                                       │
│ Request to: 10.96.10.50:80 (ClusterIP)                               │
│                                                                       │
│ Traditional (iptables):                                               │
│  • Packet hits PREROUTING chain                                      │
│  • Matches Service ClusterIP rule                                    │
│  • Random selection: frontend-v1-pod1 (10.244.2.15:8080)             │
│  • DNAT to pod IP                                                    │
│                                                                       │
│ Cilium eBPF:                                                         │
│  • Socket-level intercept                                            │
│  • Hash map lookup in cilium_lb4_services                            │
│  • Consistent hash selection: frontend-v1-pod1                       │
│  • Direct connection to pod IP                                       │
│                                                                       │
│ Selected: frontend-v1-pod1 on Node 2 (10.244.2.15:8080)              │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 │ Pod-to-Pod routing
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 5: CNI Routing (Node 1 → Node 2)                                │
│                                                                       │
│ Packet: Src=ingress-pod, Dest=10.244.2.15:8080                       │
│                                                                       │
│ Node 1 routing table:                                                │
│   10.244.2.0/24 → 192.168.1.20 (Node 2)                              │
│                                                                       │
│ Cilium direct routing:                                               │
│  • eBPF TC program on eth0                                           │
│  • Lookup dest in cilium_tunnel_map                                  │
│  • Forward to Node 2 physical NIC                                    │
│                                                                       │
│ OR Flannel overlay:                                                  │
│  • Encapsulate in VXLAN                                              │
│  • Outer: Src=192.168.1.10, Dest=192.168.1.20                        │
│  • Inner: Src=10.244.1.x, Dest=10.244.2.15                           │
│                                                                       │
│ Packet arrives at Node 2                                             │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 6: Node 2 - Service Mesh Interception                           │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Packet arrives at Node 2's NIC                                 │  │
│  │ CNI routes to frontend-v1-pod1's veth                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                             ▼                                         │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ iptables PREROUTING (Istio-injected)                           │  │
│  │   -A PREROUTING -p tcp -j ISTIO-INBOUND                        │  │
│  │   -A ISTIO-INBOUND --dport 8080 -j REDIRECT --to-port 15006    │  │
│  │                                                                 │  │
│  │ Redirects to Envoy sidecar's inbound listener                  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                             ▼                                         │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Envoy Sidecar (frontend-v1-pod1)                               │  │
│  │                                                                 │  │
│  │ Inbound processing:                                            │  │
│  │  1. Terminate mTLS (if enabled)                                │  │
│  │  2. Extract client identity from certificate                   │  │
│  │  3. Check AuthorizationPolicy:                                 │  │
│  │     • Allow from ingress-gateway? ✓                            │  │
│  │  4. Apply rate limits (if configured)                          │  │
│  │  5. Parse HTTP request                                         │  │
│  │  6. Record metrics (request count, latency timer start)        │  │
│  │  7. Create trace span (if trace context in headers)            │  │
│  │  8. Forward to app container: localhost:8080                   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                             ▼                                         │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Application Container (frontend-v1)                            │  │
│  │                                                                 │  │
│  │ Receives: GET /api/users HTTP/1.1                              │  │
│  │ Headers include:                                               │  │
│  │   • traceparent: 00-abc123-def456-01 (trace context)           │  │
│  │   • x-forwarded-for: original client IP                        │  │
│  │   • x-request-id: unique request ID                            │  │
│  │                                                                 │  │
│  │ Application logic:                                             │  │
│  │  1. Parse request                                              │  │
│  │  2. Validate auth token (JWT)                                  │  │
│  │  3. Need data from backend service                             │  │
│  │  4. Make request: http.get("http://backend:8080/users")        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                             ▼                                         │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Outbound request intercepted                                   │  │
│  │                                                                 │  │
│  │ iptables OUTPUT chain:                                         │  │
│  │   Redirects backend:8080 → Envoy outbound :15001               │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                             ▼                                         │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Envoy Sidecar Outbound Processing                              │  │
│  │                                                                 │  │
│  │  1. Resolve "backend" via DNS → backend ClusterIP              │  │
│  │  2. Check VirtualService routing rules:                        │  │
│  │     • 90% → backend-v1                                         │  │
│  │     • 10% → backend-v2 (canary)                                │  │
│  │  3. Select backend-v2 (10% chance, canary testing)             │  │
│  │  4. EDS provides endpoints for backend-v2:                     │  │
│  │     • 10.244.3.20:8080 (backend-v2-pod1 on Node 3)             │  │
│  │  5. Establish mTLS connection to backend-v2's Envoy            │  │
│  │  6. Propagate trace context (add span)                         │  │
│  │  7. Send request                                               │  │
│  │  8. Record outbound metrics                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 │ Service mesh mTLS encrypted
                                 │ Pod-to-pod via CNI
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 7: Backend Pod on Node 3                                        │
│  (Similar flow: Envoy inbound → App container)                       │
│                                                                       │
│  Application needs database query:                                   │
│   SELECT * FROM users WHERE id = ?                                   │
│                                                                       │
│  Makes connection to: postgresql:5432                                │
│  → Envoy outbound intercepts                                         │
│  → Routes to postgres-0 pod (StatefulSet)                            │
│  → eBPF/Pixie captures SQL query for observability                   │
│  → Executes query, returns data                                      │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 │ Response bubbles back
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 8: Response Path                                                │
│                                                                       │
│ backend-v2 → Envoy (record response metrics) →                       │
│ frontend-v1's Envoy (correlate request/response) →                   │
│ frontend-v1 app (process data, render JSON) →                        │
│ Envoy outbound → ingress controller →                                │
│ LoadBalancer → User                                                  │
│                                                                       │
│ Throughout:                                                          │
│  • Every hop records telemetry                                       │
│  • Trace spans created at each service                               │
│  • Logs generated with trace IDs                                     │
│  • Metrics incremented (request counters, histograms)                │
│  • eBPF programs capture low-level network data                      │
└──────────────────────────────────────────────────────────────────────┘

OBSERVABILITY DATA GENERATED:
┌──────────────────────────────────────────────────────────────────────┐
│ Metrics (Prometheus):                                                │
│  • http_requests_total{service="frontend",code="200"} +1             │
│  • http_request_duration_seconds{...} histogram                      │
│  • istio_requests_total{...} +1                                      │
│                                                                      │
│ Logs (Loki):                                                         │
│  {app="frontend"} 2025-01-18 INFO GET /api/users 200 45ms           │
│                   trace_id=abc123                                   │
│  {app="backend-v2"} 2025-01-18 INFO SELECT users 12ms               │
│                     trace_id=abc123                                 │
│                                                                      │
│ Traces (Jaeger):                                                     │
│  Trace abc123:                                                       │
│    Span: ingress [0-150ms]                                          │
│      Span: frontend-v1 [5-145ms]                                    │
│        Span: backend-v2 [10-100ms]                                  │
│          Span: postgres [15-90ms]                                   │
│                                                                      │
│ All correlated by trace_id for complete visibility!                 │
└──────────────────────────────────────────────────────────────────────┘
```

**Complete Stack Summary:**
- **Infrastructure**: Kubernetes orchestrates containers across nodes
- **Networking**: CNI provides pod connectivity, kube-proxy/eBPF handles Services
- **Service Mesh**: Envoy sidecars provide mTLS, traffic management, observability
- **Security**: Multi-layer defense from build to runtime
- **Observability**: Metrics, logs, traces provide complete visibility
- **GitOps**: Declarative deployment from Git, automated sync

This comprehensive architecture shows how all the cloud native components we discussed work together to create a production-ready, secure, observable, and highly automated platform.