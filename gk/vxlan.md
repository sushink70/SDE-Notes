Virtual Extensible LAN (VXLAN) is a network virtualization technology that creates a Layer 2 (L2) overlay network on top of an existing Layer 3 (L3) physical infrastructure. Developed by Cisco, VMware, and Arista, it was designed to overcome the scalability limits of traditional VLANs in large-scale cloud and data centre environments. [1, 2, 3, 4] 

[VXLAN | Virtual Extensible LAN | What is VXLAN? | VNI | VTEP](https://ipcisco.com/lesson/virtual-extensible-lan-vxlan/)
[Virtual Extensible LAN (VXLAN) Overview > Implementing Data ...](https://www.ciscopress.com/articles/article.asp?p=2999385&seqNum=3)
[VXLAN | Networking](https://docs.netscaler.com/en-us/citrix-adc/current-release/networking/vxlans.html)

## Key Concepts and Architecture

* Encapsulation: VXLAN uses MAC-in-UDP encapsulation. It wraps a standard L2 Ethernet frame inside a Layer 4 UDP packet for transport across an IP network.
* VTEP (VXLAN Tunnel Endpoint): These are the devices (switches, routers, or software in hypervisors) that perform the encapsulation and decapsulation.
* VNI (VXLAN Network Identifier): A 24-bit identifier used to distinguish between different logical networks. This allows for up to 16 million unique segments, compared to the 4,094 limit of a 12-bit VLAN ID.
* Overlay vs. Underlay: The underlay is the physical L3 IP network (the transport), while the overlay is the virtual L2 network running on top of it. [1, 2, 5, 6, 7, 8] 

## VXLAN vs. VLAN Comparison

| Feature [1, 2, 6, 8, 9] | Traditional VLAN (802.1Q) | VXLAN (RFC 7348) |
|---|---|---|
| Max Segments | 4,094 | ~16.7 Million |
| Encapsulation | L2 Tagging (4 bytes) | MAC-in-UDP (50+ bytes) |
| Transport | Limited to L2 domains | Stretches across L3 networks |
| Loop Avoidance | Spanning Tree Protocol (STP) | L3 Routing (ECMP) |

## Why Use VXLAN?

   1. Multi-Tenancy: Essential for cloud providers to isolate thousands of different customers on the same physical infrastructure.
   2. VM Mobility: Allows virtual machines to migrate between physical hosts across different L3 subnets without needing to change their IP addresses.
   3. Efficiency: By using an L3 underlay, networks can leverage Equal-Cost Multi-Path (ECMP) for better load balancing and redundancy, eliminating the need for STP.
   4. Hardware Offload: Many modern switches from vendors like [Arista](https://www.arista.com/assets/data/pdf/Whitepapers/Arista_Networks_VXLAN_White_Paper.pdf) and [HPE](https://www.hpe.com/in/en/what-is/vxlan.html) support VXLAN in hardware to minimize performance overhead. [2, 5, 7, 8, 9] 

For complex environments, VXLAN is often paired with BGP EVPN as a control plane to dynamically manage MAC address learning and reduce broadcast traffic. [10, 11] 
Are you planning to configure VXLAN on specific hardware (like Cisco or Juniper) or looking for a deeper dive into the BGP EVPN control plane?

Virtual eXtensible Local Area Network (VXLAN) is a tunneling protocol that encapsulates Layer 2 Ethernet frames within Layer 4 UDP packets (MAC-in-UDP), allowing Layer 2 networks to span over Layer 3 infrastructures. It solves VLAN scalability issues by supporting up to 16 million networks (vs. 4,096 in VLAN) and eliminating Spanning Tree Protocol (STP) restrictions. 

Key Concepts and Benefits

    Encapsulation: Uses MAC-in-UDP encapsulation, typically using port 4789.
    Scalability: Features a 24-bit Virtual Network Identifier (VNID), allowing for 16 million logical networks.
    VTEP (VXLAN Tunnel Endpoints): Switches or routers that encapsulate and decapsulate traffic.
    Network Segmentation: Enables secure, isolated multi-tenant environments where organizations can share a single physical network.
    Underlay/Overlay: VXLAN creates an overlay network on top of a physical (underlay) IP network. 


Common Implementations
VXLAN is heavily used in cloud and data center environments, often implemented via technologies like: 

    EVPN-VXLAN (Ethernet VPN): A popular control plane for distributing network information.
    OVSDB-VXLAN: Used in SDN environments.
    Manual VXLAN: Configured manually with static unicast or multicast tunnels. 

Operational Considerations

    MTU: VXLAN adds 50 bytes of overhead to frames, making it essential to support jumbo frames on the physical underlay network.
    Infrastructure: Typically deployed over 10Gbps or higher capacity Ethernet.
    Automation: Often managed through Infrastructure as Code (IaC) to handle complex network topologies. 