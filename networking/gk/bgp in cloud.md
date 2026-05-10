In cloud-native environments, the Border Gateway Protocol (BGP) is used to dynamically advertise pod and service IP addresses to the physical network, eliminating the need for complex overlay networks and manual route configuration. While the Linux kernel handles the actual forwarding of data packets, BGP itself typically runs as a user-space control plane that interacts with the kernel to program routing tables. [1, 2, 3, 4, 5]  
Key Implementations 
Cloud-native BGP is primarily managed through Container Network Interfaces (CNIs) and specialized routing software: 

• Cilium: Uses an eBPF-based data plane for high-performance networking and features a built-in BGP control plane (based on GoBGP) to advertise  ClusterIP 
 and pod networks. 
• Project Calico: A widely used CNI that uses a BGP speaker on every node to propagate routes across a cluster mesh, supporting both non-overlay and overlay modes. 
• Kube-router: A solution that combines BGP for inter-node pod networking with IPVS for in-kernel load balancing. 
• Juniper Cloud-Native Router (JCNR): A containerized router that integrates the Junos OS control plane with the Linux kernel or a DPDK-based forwarding plane to support advanced protocols like BGP unnumbered and MPLS. 
• FRRouting (FRR): An open-source routing suite often used in projects like Red Hat OpenStack and OpenShift to enable BGP peering and dynamic route updates for virtual machines and containers. [3, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]  

Interaction with the Linux Kernel [17]  
BGP is an application-layer protocol (TCP port 179) that does not reside directly "in" the kernel; instead, it "talks" to the kernel through the following mechanisms: 

• Netlink: The standard interface BGP daemons (like FRR or GoBGP) use to program the Linux kernel's routing table based on learned BGP routes. 
• eBPF / XDP: Modern cloud-native routers use eBPF to bypass or optimize the kernel's networking stack, allowing for high-speed packet processing and direct interaction with the BGP control plane. 
• VRF (Virtual Routing and Forwarding): The Linux kernel supports  VRF-lite 
, which allows BGP to maintain multiple independent routing tables on a single node for network segmentation. 

AI responses may include mistakes.
