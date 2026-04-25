Overlay networks are logical networks built on top of another network, usually IP. They let you create a virtual topology that is independent of the underlying physical network, so endpoints can communicate as if they were on the same network even when they are not.

A simple view:

```text
App/Pod/VM A  <--- overlay tunnel --->  App/Pod/VM B
     |                                      |
     +-------- underlay physical network ---+
```

## Core idea

The physical network is called the **underlay**.
The overlay is the **virtual network** you see on top of it.

The overlay typically works by:

1. Taking an original packet.
2. Encapsulating it inside another packet.
3. Sending it across the underlay.
4. Decapsulating it at the destination.

So the underlay carries the traffic, but the overlay defines the logical connectivity.

## Why overlays exist

They solve common infrastructure problems:

* **Address independence**: virtual machines, containers, or tenants can use their own IP ranges.
* **Tenant isolation**: different groups can share the same physical fabric without interfering.
* **Mobility**: workloads can move between hosts without changing their logical network identity.
* **Scalability**: large logical networks can be built over simple routed IP fabrics.
* **Segmentation**: separate apps, environments, or customers cleanly.

## Common examples

* **VXLAN** in data centers and Kubernetes networking
* **GRE** tunnels
* **IP-in-IP**
* **MPLS** in service provider networks
* **VPNs** such as WireGuard or OpenVPN
* **SD-WAN overlays**
* **Container networking overlays** like Flannel VXLAN, Calico in overlay mode, or Weave Net

## How VXLAN-style overlay works

Suppose Pod A wants to talk to Pod B on another node:

* Pod A sends traffic to its node.
* The node wraps the packet in a VXLAN packet.
* The outer packet is routed across the physical network.
* The destination node removes the VXLAN wrapper.
* The original packet is delivered to Pod B.

The physical network only needs normal IP routing. The overlay handles the virtual network behavior.

## Benefits

* Easier multi-tenant isolation
* Better workload portability
* Works over existing IP infrastructure
* Flexible network segmentation without reconfiguring physical switches heavily

## Tradeoffs

* Extra encapsulation adds **overhead**.
* Can reduce **MTU** unless adjusted correctly.
* More complex troubleshooting, because you must inspect both overlay and underlay.
* Possible performance cost from encapsulation/decapsulation.
* Control-plane complexity for learning, routing, and policy distribution.

## In cloud-native systems

Overlay networks are very common in Kubernetes when:

* Pods need a flat IP space across nodes.
* The physical network does not directly know pod routes.
* Network policy and service routing are implemented logically rather than physically.

A related term is **underlay networking**, where the physical fabric routes the workload traffic directly without tunneling.

## One-sentence definition

An overlay network is a virtual network built on top of another network by encapsulating traffic so nodes can communicate through a logical topology independent of the physical one.

If you want, I can also explain **overlay vs underlay**, or show **how VXLAN works step by step**.
