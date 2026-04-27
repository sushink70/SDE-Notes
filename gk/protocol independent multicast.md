Protocol Independent Multicast (PIM) is a family of IP multicast routing protocols used to distribute data efficiently from one or many sources to many receivers across LANs, WANs, or the Internet. It is "protocol-independent" because it uses existing unicast routing tables (OSPF, BGP, etc.) for topology discovery rather than having its own, making it highly flexible. [1, 2, 3]  
Key PIM Modes and Concepts: 

• PIM Sparse Mode (PIM-SM): Efficiently builds shared trees rooted at a Rendezvous Point (RP) for sparse, widely distributed receivers. It is the standard for most internet and enterprise scenarios. 
• PIM Dense Mode (PIM-DM): Uses a "flood and prune" approach, sending traffic to all routers and removing those with no interested receivers. Suitable for dense networks where receivers are everywhere. 
• Source-Specific Multicast (SSM): Builds trees directly from receiver to source, bypassing the need for an RP, optimized for one-to-many streaming. 
• Bidirectional PIM (Bi-Dir PIM): Optimized for many-to-many applications, allowing traffic to travel up and down the shared tree. [1, 4, 5, 6, 7]  

How It Works:PIM relies on Reverse Path Forwarding (RPF) checks to ensure loop-free forwarding. It constructs multicast distribution trees—either shared trees (*,G) or source-specific trees (S,G)—to deliver packets only to links that have requested the data. 

• PIM Registration: In Sparse Mode, the first-hop router encapsulates multicast traffic to the Rendezvous Point (RP). 
• Join/Prune Messages: Routers send PIM messages to join or leave a specific multicast stream. [1, 10, 11, 12]  

PIM is widely used for live video conferencing, IPTV, and live streaming. [2, 4, 13]  

AI can make mistakes, so double-check responses

