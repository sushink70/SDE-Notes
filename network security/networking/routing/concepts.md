# Network Security: Senior-Level Routing Guide

## 1. Routing Protocol Security Fundamentals

### Core Security Principles
- **Confidentiality**: Protecting routing information from unauthorized disclosure
- **Integrity**: Ensuring routing updates haven't been tampered with
- **Authenticity**: Verifying the source of routing information
- **Availability**: Ensuring routing infrastructure remains operational under attack

### Common Routing Threats
- Route injection/poisoning
- Route hijacking
- Route leaking
- Denial of Service (DoS) attacks on routing protocols
- Man-in-the-middle attacks
- Replay attacks
- Resource exhaustion attacks

## 2. BGP (Border Gateway Protocol) Security

### BGP Vulnerabilities
- **Prefix hijacking**: Malicious ASes announcing IP prefixes they don't own
- **Route leaks**: Unintentional announcement of routes beyond intended scope
- **AS path manipulation**: Forging AS paths to manipulate routing decisions
- **BGP session hijacking**: Compromising TCP sessions between BGP peers

### BGP Security Mechanisms

#### RPKI (Resource Public Key Infrastructure)
- **ROA (Route Origin Authorization)**: Cryptographically signed objects that authorize an AS to originate specific prefixes
- **ROV (Route Origin Validation)**: Process of validating BGP announcements against ROAs
- Three validation states: Valid, Invalid, NotFound
- Implementation considerations and filtering policies

#### BGP Authentication
- **MD5 Authentication (RFC 2385)**: Legacy option using shared secrets
- **TCP AO (Authentication Option, RFC 5925)**: Modern replacement with better key management
- **IPsec**: Can protect BGP sessions at network layer

#### BGPSEC
- Path validation using cryptographic signatures
- Provides AS path authentication
- Still in limited deployment due to complexity

#### Best Practices
- Implement prefix filtering with IRR (Internet Routing Registry) objects
- Use maximum prefix limits on peer sessions
- Implement route flap dampening
- Configure BGP TTL security (GTSM - Generalized TTL Security Mechanism)
- Use peer-specific prefixes for eBGP sessions
- Implement strict AS path filtering

### BGP Route Filtering
- **Inbound filters**: Bogon lists, RFC 1918 addresses, own prefixes, customer validation
- **Outbound filters**: Prevent route leaks, control what you announce
- **AS path filters**: Regular expressions to control routing based on AS path
- **Community-based filtering**: Implementing routing policies using BGP communities

## 3. OSPF (Open Shortest Path First) Security

### OSPF Attack Vectors
- LSA (Link State Advertisement) flooding
- Injecting false routing information
- Adjacency manipulation
- Resource exhaustion through excessive LSAs
- Replay attacks

### OSPF Security Features

#### Authentication Types
- **Null (Type 0)**: No authentication - never use in production
- **Simple password (Type 1)**: Clear text - insecure, legacy only
- **MD5 (Type 2)**: Cryptographic authentication
- **SHA authentication**: Modern alternative in newer implementations

#### Area Design for Security
- Proper area segmentation limits attack propagation
- Stub areas reduce external routing information
- Totally stubby areas minimize routing overhead
- NSSA (Not-So-Stubby Area) for controlled external routes

#### Best Practices
- Enable authentication on all OSPF interfaces
- Use passive interfaces where appropriate
- Implement strict neighbor authentication
- Control LSA propagation with filtering
- Monitor for LSA anomalies
- Set maximum LSA limits to prevent flooding attacks

## 4. EIGRP Security

### EIGRP Vulnerabilities
- Neighbor relationship exploitation
- Route injection through fake hello packets
- Query/reply flooding (SIA - Stuck in Active)
- Authentication bypass attempts

### Security Mechanisms
- **MD5 authentication**: Legacy authentication method
- **SHA-256 authentication**: Modern, stronger alternative
- Key chain management with key rotation
- Named mode EIGRP for enhanced security

### Best Practices
- Always enable authentication
- Use stub routing to limit query scope
- Implement passive interfaces
- Control routing updates with distribute lists
- Monitor for SIA conditions

## 5. Route Filtering and Policy

### Access Control Lists (ACLs) for Routing
- Standard ACLs for simple filtering
- Extended ACLs for granular control
- Prefix lists for efficient route filtering
- Route maps for complex policy implementation

### Distribute Lists
- Controlling route advertisements
- Filtering routing updates in/out
- Per-protocol and per-interface application

### Route Maps
- Conditional matching and modification
- Setting routing attributes (metric, preference, tags)
- Policy-based routing (PBR) implementation
- Redistribution control

### Prefix Lists
- Efficient prefix matching using first-match logic
- Supporting both exact and range matches
- Performance benefits over ACLs for routing

## 6. Route Redistribution Security

### Risks
- Routing loops
- Suboptimal routing
- Unintended route propagation
- Metric inconsistencies

### Best Practices
- Use route tags to track redistributed routes
- Implement filtering to prevent loops
- Control administrative distance
- Use prefix lists and route maps for selective redistribution
- Document redistribution points clearly
- Monitor redistribution carefully

## 7. Control Plane Security

### Control Plane Policing (CoPP)
- Rate limiting control plane traffic
- Protecting routing protocols from DoS attacks
- Classifying and prioritizing control plane traffic
- Hardware vs. software rate limiting

### Infrastructure ACLs (iACLs)
- Protecting network infrastructure devices
- Permitting only authorized management traffic
- Implementing at network edge
- Regular review and updates

### Routing Protocol Authentication Summary

| Protocol | Authentication Methods | Best Practice |
|----------|------------------------|---------------|
| BGP | MD5, TCP-AO, IPsec | TCP-AO + RPKI |
| OSPF | MD5, SHA | SHA with key rotation |
| EIGRP | MD5, SHA-256 | SHA-256 with key chains |
| RIP | MD5 | Avoid RIP; if necessary, use MD5 |
| IS-IS | HMAC-MD5, SHA | SHA family algorithms |

## 8. Advanced Security Concepts

### Unicast Reverse Path Forwarding (uRPF)
- **Strict mode**: Interface must have route back to source with same interface
- **Loose mode**: Route to source must exist in routing table
- **VRF mode**: Applies uRPF per VRF instance
- Use cases: Anti-spoofing at network edge
- Limitations: Asymmetric routing environments

### Route Authentication Best Practices
- Implement key chains with overlapping key lifetimes
- Regular key rotation policies
- Secure key storage and distribution
- Automated key management where possible

### Routing Protocol Hardening
- Disable unused routing protocols
- Minimize routing protocol scope
- Use authentication on all routing adjacencies
- Implement TTL security mechanisms
- Monitor for unexpected routing changes
- Log all routing protocol events

## 9. SD-WAN and Modern Routing Security

### SD-WAN Security Considerations
- Overlay security (IPsec, TLS)
- Controller security and authentication
- Zero-trust network access (ZTNA) integration
- Secure segmentation using VRFs or VXLANs
- Application-aware routing security

### Segment Routing and SRv6 Security
- Segment routing header integrity
- Limiting segment list manipulation
- Securing controller-to-router communication
- Preventing segment ID spoofing

## 10. DDoS Mitigation in Routing

### Detection Mechanisms
- NetFlow/sFlow analysis
- Anomaly detection systems
- BGP FlowSpec for automated mitigation
- RTBH (Remotely Triggered Black Hole) routing

### Mitigation Techniques
- **BGP FlowSpec**: Distribute traffic filtering rules via BGP
- **RTBH**: Null routing attack traffic at upstream
- **Source-based RTBH**: Null routing based on source address
- **Destination-based RTBH**: Protecting specific targets
- Rate limiting and traffic shaping

## 11. Routing in Zero Trust Architectures

### Micro-segmentation
- VLAN and VRF-based segmentation
- Software-defined perimeters
- Dynamic routing based on identity and context
- East-west traffic control

### Dynamic Routing Policies
- Identity-aware routing
- Application-based routing decisions
- Real-time threat intelligence integration
- Conditional access enforcement

## 12. Monitoring and Incident Response

### Key Metrics to Monitor
- Routing table size and changes
- BGP session states and flaps
- IGP neighbor relationships
- Routing protocol CPU utilization
- Unexpected route advertisements
- Prefix origin changes

### Tools and Technologies
- BGP monitoring systems (BGPmon, RIPE RIS)
- Route analytics platforms
- SIEM integration for routing events
- Automated alerting systems

### Incident Response for Routing Attacks
- Isolation procedures for compromised routers
- Emergency BGP filtering activation
- ROA/IRR database updates
- Coordination with upstream providers
- Communication protocols (NOC, SOC, ISAC)

## 13. Compliance and Best Practice Frameworks

### Industry Standards
- **NIST SP 800-54**: Border Gateway Protocol Security
- **MANRS (Mutually Agreed Norms for Routing Security)**: Four key actions
  - Preventing propagation of incorrect routing information
  - Preventing traffic with spoofed source addresses
  - Facilitating operational communication
  - Facilitating validation of routing information
- **PCI DSS**: Network segmentation requirements
- **ISO 27001**: Information security controls

## 14. Interview Focus Areas

### Technical Deep Dives
- Explain RPKI validation process in detail
- Design BGP security architecture for multi-homed enterprise
- Troubleshoot routing protocol authentication failures
- Analyze routing table anomalies
- Design control plane security policies

### Scenario-Based Questions
- How would you respond to a BGP hijack affecting your prefixes?
- Design a secure routing architecture for a merger/acquisition
- Implement routing security for a multi-tenant environment
- Address route leaks from a downstream customer
- Secure routing during a DDoS attack

### Architecture and Design
- Multi-layer routing security design
- Defense-in-depth for routing infrastructure
- Secure routing protocol selection and justification
- Integration with existing security stack
- Balancing security with operational requirements

## 15. Emerging Technologies and Future Trends

### IPv6 Routing Security
- Different threat landscape than IPv4
- NDP (Neighbor Discovery Protocol) security
- RA (Router Advertisement) guard
- IPv6 source address validation

### Automation and Security
- Intent-based networking security implications
- Automated policy enforcement
- AI/ML for anomaly detection in routing
- Infrastructure as Code (IaC) for routing configs

### Quantum-Resistant Routing Security
- Post-quantum cryptography for routing protocols
- Future-proofing routing authentication
- Migration strategies

## Key Takeaways for Interviews

1. **Understand the "why"**: Know not just how security mechanisms work, but why they're needed and what they protect against
2. **Think defense-in-depth**: Multiple layers of security controls
3. **Consider operational impact**: Security measures that break operations won't be implemented
4. **Stay current**: Be aware of recent routing security incidents and new mechanisms
5. **Balance security and functionality**: Understand trade-offs in security decisions
6. **Know your tools**: Hands-on experience with routing security configurations
7. **Incident response mindset**: Think about detection, response, and recovery

## Recommended Study Resources

- RFCs: 4271 (BGP), 2328 (OSPFv2), 7454 (BGP Operations), 6810 (RPKI/Router Protocol)
- NIST publications on routing security
- MANRS documentation and case studies
- Recent routing security incidents and post-mortems
- Vendor security configuration guides (Cisco, Juniper, Arista)
- RIPE NCC routing security resources

# 100 Network Security Routing Scenario Questions & Answers

## Category 1: BGP Security & Incident Response (Questions 1-20)

### Q1: Your monitoring system alerts you that your company's /24 prefix is being announced by an unknown AS in Asia. How do you respond?

**Answer:**
1. **Immediate verification**: Check multiple looking glasses and route servers (RIPE RIS, Hurricane Electric, RouteViews) to confirm the hijack scope and affected regions
2. **Assess impact**: Determine if traffic is being redirected by checking traffic patterns and user complaints
3. **Contact upstream providers**: Reach out to your ISP NOCs immediately to request filtering of the malicious announcement
4. **Emergency BGP actions**: Announce more specific prefixes (if possible) to override the hijack using longest-match routing
5. **RPKI ROA verification**: Ensure your ROAs are properly published and up-to-date
6. **Community coordination**: Contact the offending AS's NOC and upstream providers; report to ARIN/RIPE abuse contacts
7. **Document everything**: Capture BGP table dumps, traceroutes, and timeline for potential legal action
8. **Post-incident**: Review why existing safeguards didn't prevent this; implement additional monitoring

**Long-term prevention:**
- Ensure ROAs are published in all RIRs
- Work with upstreams to implement RPKI ROV
- Implement IRR objects with proper authentication
- Set up real-time BGP monitoring with alerts

### Q2: A customer is announcing your infrastructure prefixes along with their own routes. How do you handle this route leak?

**Answer:**
1. **Verify the leak**: Confirm via looking glasses that your routes are being propagated through the customer AS inappropriately
2. **Immediate mitigation**: Contact customer NOC to stop the announcements; if unresponsive, implement emergency prefix filtering on their session
3. **Check BGP configuration**: Review if you're sending full tables vs. default route only; verify communities are applied correctly
4. **Implement technical controls**:
   - Add AS-path prepending to make customer paths less attractive
   - Use BGP communities to signal "no-export" or "no-advertise"
   - Implement prefix filtering on customer session (accept only their assigned blocks)
5. **Max-prefix limits**: Set appropriate maximum prefix limits on the customer session to auto-shutdown if exceeded
6. **ROA validation**: Ensure customer cannot validate routes they don't own if RPKI is implemented
7. **Contractual review**: Document incident; review customer agreement regarding route announcements
8. **Ongoing monitoring**: Implement continuous monitoring for this customer's announcements

**Prevention measures:**
- Default-deny prefix filters on customer sessions
- Regular audits of what customers are announcing
- Automated monitoring systems for unexpected route propagation
- Include route leak clauses in customer contracts

### Q3: You notice BGP session flapping between your edge routers and ISP every 30-45 seconds. Security logs show no obvious attacks. How do you troubleshoot?

**Answer:**
1. **Check BGP logs**: Review debug logs for specific error messages (Hold timer expiration, TCP connection reset, authentication failure)
2. **Analyze patterns**: 30-45 second intervals suggest hold timer (default 180s) or keepalive issues (default 60s)
3. **Verify authentication**: MD5/TCP-AO authentication failures would cause immediate flaps
4. **Interface statistics**: Check for input/output errors, CRC errors, buffer overflows on the physical interface
5. **Resource utilization**: Verify CPU, memory, and BGP process health on both sides
6. **MTU issues**: Verify MTU settings; fragmentation issues can cause BGP instability
7. **Prefix count**: Check if approaching max-prefix limits causing soft-reconfiguration
8. **Control plane policing**: Verify CoPP isn't rate-limiting BGP packets
9. **Routing loops**: Check for IGP issues causing instability that affects BGP next-hops
10. **Security considerations**: Could be a low-rate DoS attack targeting BGP sessions

**Testing approach:**
- Increase hold timer temporarily (240s) to see if flapping stops
- Capture packets during flap to see TCP RST or BGP NOTIFICATION messages
- Test with ISP during maintenance window
- Implement BFD for faster detection and failover

### Q4: Design a BGP security architecture for a company with three ISPs, two data centers, and cloud connectivity.

**Answer:**

**Architecture components:**

1. **Multi-layer filtering approach:**
   - **Tier 1 (ISP edge)**: Strict inbound filters
     - Bogon lists (martian addresses, RFC 1918, reserved)
     - Own prefixes (prevent reflection)
     - Default route only or full tables based on requirements
   - **Tier 2 (Internet edge)**: Outbound announcement control
     - Explicit prefix-lists of owned/announced blocks
     - AS-path filters to prevent private ASN leakage
     - Community tagging for traffic engineering
   - **Tier 3 (Internal iBGP)**: Policy enforcement
     - Route reflectors with security policies
     - Clusters per data center for redundancy

2. **Authentication & encryption:**
   - TCP-AO on all external BGP sessions
   - IPsec for sensitive ISP connections
   - Unique keys per session with regular rotation schedule

3. **RPKI implementation:**
   - Publish ROAs for all announced prefixes at RIR
   - Implement ROV on all ISP sessions (drop invalid)
   - Monitor ROA validation states

4. **Session protection:**
   - TTL security (GTSM) on all eBGP sessions
   - Dedicated /31 or /30 for each peer
   - Max-prefix limits per session (ISPs: 900k, customers: specific)
   - BFD for rapid failure detection

5. **DDoS mitigation integration:**
   - BGP FlowSpec capability with ISPs
   - RTBH routing capability for emergency null-routing
   - Anycast for critical services

6. **Data center interconnection:**
   - iBGP full mesh or route reflectors
   - Private ASN for internal use
   - QoS markings and community-based routing policies

7. **Cloud connectivity:**
   - Separate BGP sessions for each cloud provider
   - Private peering where available (AWS Direct Connect, Azure ExpressRoute)
   - Strict filtering of cloud-announced prefixes

8. **Monitoring & visibility:**
   - BGP monitoring system (real-time alerts)
   - NetFlow/IPFIX collection and analysis
   - SIEM integration for BGP events
   - Looking glass access for troubleshooting

### Q5: Your RPKI validation shows several of your routes as "Invalid" but they're legitimately yours. What's wrong and how do you fix it?

**Answer:**

**Root causes to investigate:**

1. **ROA misconfiguration:**
   - MaxLength in ROA too restrictive (e.g., ROA for /22 with maxLength /22, but announcing /24s)
   - Wrong origin AS in ROA
   - ROA expired or not yet valid

2. **Multiple ROA conflicts:**
   - Overlapping ROAs from different RIRs
   - ROAs covering same space with different origin ASNs

3. **AS migration incomplete:**
   - Transferred prefixes but didn't update ROAs
   - Old ROAs still active with previous AS

**Resolution steps:**

1. **Verify current state:**
   ```
   - Check RPKI validator output
   - Query rpki-client or RIPE validator
   - Review ROAs in RPKI repository
   ```

2. **Access RIR portal:**
   - Log into appropriate RIR (ARIN, RIPE, APNIC)
   - Review all ROAs for affected prefixes
   - Check resource certificates

3. **Update ROAs correctly:**
   - For /22 announcing /24s: Set maxLength to /24
   - Ensure correct origin AS number
   - Set appropriate validity dates

4. **Example ROA fix:**
   ```
   Prefix: 203.0.113.0/22
   Origin AS: AS65001
   MaxLength: /24
   
   This allows: 203.0.113.0/22, /23, or /24 announcements
   ```

5. **Wait for propagation:**
   - Changes take 1-24 hours to propagate
   - Monitor multiple RPKI validators
   - Test with different ISPs

6. **Temporary workaround:**
   - Contact ISPs to temporarily not enforce RPKI validation
   - Use IRR route objects as backup validation

7. **Preventive measures:**
   - Document all ROAs in change management system
   - Automate ROA creation/updates via RIR APIs
   - Test ROAs in staging before production changes
   - Set calendar reminders for ROA expiration

### Q6: You're seeing asymmetric routing causing issues with stateful firewalls. How do you resolve this from a routing perspective?

**Answer:**

**Analysis:**
- Traffic enters via ISP-A but returns via ISP-B
- Firewall drops return traffic as it didn't see original session
- Root cause: BGP path selection differs by direction

**Solutions by priority:**

1. **Policy-Based Routing (PBR):**
   - Implement PBR on firewalls to force symmetric paths
   - Match source addresses and direct to appropriate next-hop
   - Use route-maps with set ip next-hop commands

2. **BGP traffic engineering:**
   - **Inbound control (harder):**
     - AS-path prepending on less-preferred ISP
     - Selective announcement (announce specific prefixes only to preferred ISP)
     - BGP communities to influence upstream routing (if ISP supports)
     - MED manipulation
   
   - **Outbound control (easier):**
     - Local preference to prefer one ISP
     - Weight (Cisco) for specific path selection
     - BGP communities for internal policy

3. **Architecture changes:**
   - **Active-Active firewall clustering:**
     - State synchronization between firewalls
     - Both firewalls see both directions
   
   - **Firewall placement:**
     - Move firewalls after routing decision point
     - One firewall per ISP path
   
   - **Load balancer integration:**
     - Use load balancer to normalize paths
     - Session persistence based on source IP

4. **Specific BGP configuration example:**
   ```
   router bgp 65001
     neighbor 10.1.1.1 remote-as 65002  ! ISP-A (preferred)
     neighbor 10.2.2.2 remote-as 65003  ! ISP-B
     
     address-family ipv4
       neighbor 10.1.1.1 weight 200      ! Prefer ISP-A outbound
       neighbor 10.2.2.2 weight 100
       
       ! Inbound - make ISP-A more attractive
       neighbor 10.2.2.2 route-map PREPEND out
     
   route-map PREPEND permit 10
     set as-path prepend 65001 65001 65001
   ```

5. **Monitoring solution:**
   - Implement NetFlow to track asymmetric flows
   - Alert on directional mismatches
   - Visualize traffic flows

6. **Firewall configuration:**
   - Enable asymmetric routing support (if available)
   - Disable strict state checking temporarily
   - Use connection tracking bypass for specific flows

**Best practice:**
- Document traffic flows and expected paths
- Test routing changes during maintenance windows
- Have rollback plan ready
- Consider application requirements (some apps require symmetric paths)

### Q7: A DDoS attack is saturating your primary data center. Walk through your BGP-based mitigation strategy.

**Answer:**

**Immediate response (0-5 minutes):**

1. **Characterize the attack:**
   - Identify target IPs/prefixes
   - Attack type (volumetric, application, protocol)
   - Attack size and source distribution
   - NetFlow analysis for patterns

2. **Remotely Triggered Black Hole (RTBH):**
   - Announce attacked /32 hosts with BGP to null0
   - Use specific community to signal upstream ISPs
   ```
   ip route 203.0.113.50/32 Null0
   
   router bgp 65001
     network 203.0.113.50 mask 255.255.255.255
     neighbor 10.1.1.1 route-map RTBH out
   
   route-map RTBH permit 10
     match ip address prefix-list UNDER_ATTACK
     set community 65002:666  ! ISP's blackhole community
   ```
   - ISP drops traffic at edge, protecting your bandwidth

3. **BGP FlowSpec deployment:**
   ```
   flow-spec
     address-family ipv4
       ! Block specific attack traffic
       local-install interface-all
       
     route-map FLOWSPEC permit 10
       match destination 203.0.113.0/24
       match source 0.0.0.0/0
       match protocol udp
       match destination-port 53
       match packet-length 1024-65535
       set traffic-rate 0  ! Drop
   ```
   - Distribute filtering rules via BGP
   - ISPs apply filters automatically

**Short-term mitigation (5-30 minutes):**

4. **Traffic redirection:**
   - Announce more specific prefix to scrubbing center
   - Use BGP communities for traffic steering
   ```
   ! Announce /25 instead of /24 to divert to scrubbing
   router bgp 65001
     network 203.0.113.0 mask 255.255.255.128
     neighbor 10.3.3.3 activate  ! Scrubbing center
   ```
   - Clean traffic returned via GRE tunnel

5. **Anycast activation:**
   - If available, activate anycast nodes
   - Distribute attack across multiple locations
   - Announce same prefix from multiple sites

6. **Load distribution:**
   - Use AS-path prepending to shift traffic to less-affected links
   - Adjust local-preference to utilize backup capacity

**Sustained response (30+ minutes):**

7. **Coordinate with ISPs:**
   - Request upstream filtering
   - Activate on-demand DDoS mitigation services
   - Increase transit capacity temporarily

8. **Application-layer protection:**
   - Enable WAF rules
   - Rate limiting on application servers
   - CDN integration for static content

**Recovery and documentation:**

9. **Gradual return to normal:**
   - Slowly withdraw RTBH/FlowSpec rules
   - Monitor for attack resumption
   - Document attack patterns

10. **Post-incident actions:**
    - Review effectiveness of each mitigation
    - Update runbooks
    - Test automated responses
    - Capacity planning review

**Preventive architecture:**
- Pre-negotiated DDoS mitigation contracts
- BGP FlowSpec pre-configured with ISPs
- Automated RTBH triggering based on thresholds
- Multiple transit providers for redundancy
- Anycast deployment for critical services

### Q8: You inherit a network with no routing authentication configured. Develop a rollout plan to implement it without causing outages.

**Answer:**

**Phase 1: Assessment & Planning (Week 1-2)**

1. **Discovery:**
   - Inventory all routing adjacencies (BGP, OSPF, EIGRP, etc.)
   - Document current configuration
   - Identify critical vs. non-critical links
   - Map dependencies and SLAs

2. **Risk assessment:**
   - Identify potential issues (clock synchronization, key mismatch)
   - Change windows availability
   - Rollback procedures

3. **Design decisions:**
   - **BGP**: TCP-AO with key chains (modern) or MD5 (legacy devices)
   - **OSPF**: SHA-256 preferred, MD5 minimum
   - **EIGRP**: SHA-256 with named mode
   - Key rotation policy: 90-day rotation with 7-day overlap

**Phase 2: Lab Testing (Week 3)**

4. **Build test environment:**
   - Replicate production topology
   - Test authentication enablement
   - Verify graceful authentication addition
   - Test key rotation procedures
   - Document exact commands and timing

**Phase 3: Implementation Strategy**

5. **Graceful authentication addition approach:**
   ```
   ! OSPF - Old IOS allows null + MD5 simultaneously
   interface GigabitEthernet0/0
     ip ospf authentication message-digest
     ip ospf message-digest-key 1 md5 NewSecureKey123
   
   ! Neighbor still using null auth can form adjacency
   ! Once both sides configured, authentication enforced
   ```

6. **Staged rollout by protocol:**

   **BGP (Weeks 4-6):**
   - Week 4: Non-critical peers (customers, non-primary transit)
   - Week 5: Secondary ISP connections
   - Week 6: Primary ISP connections
   
   ```
   ! Enable TCP MD5 authentication
   router bgp 65001
     neighbor 10.1.1.1 password NewBGPKey456
   
   ! Coordinate with peer to enable simultaneously
   ! Schedule 5-minute maintenance window
   ```

   **OSPF (Weeks 7-9):**
   - Week 7: Lab/test networks
   - Week 8: Distribution layer
   - Week 9: Core and edge
   
   ```
   ! Step 1: Enable on Area 0 interfaces (core first)
   interface range Gi0/0 - 1
     ip ospf authentication message-digest
     ip ospf message-digest-key 1 md5 7 EncryptedKey
   
   ! Step 2: Enable on area interfaces
   ! Step 3: Enable on stub areas last
   ```

   **EIGRP (Weeks 10-11):**
   ```
   ! Create key chain first
   key chain EIGRP-KEYS
     key 1
       key-string SecureEIGRPKey789
       accept-lifetime 00:00:00 Jan 1 2024 infinite
       send-lifetime 00:00:00 Jan 1 2024 infinite
   
   ! Enable per interface
   interface GigabitEthernet0/0
     ip authentication mode eigrp 100 md5
     ip authentication key-chain eigrp 100 EIGRP-KEYS
   ```

**Phase 4: Verification & Monitoring (Ongoing)**

7. **Verification commands:**
   ```
   show ip bgp summary  ! Check BGP status
   show ip ospf neighbor  ! Verify OSPF adjacencies
   show ip eigrp neighbors  ! Check EIGRP neighbors
   show key chain  ! Verify key configuration
   ```

8. **Monitoring setup:**
   - SIEM alerts for authentication failures
   - Neighbor state change monitoring
   - Automated health checks post-change

**Phase 5: Key Rotation Setup (Week 12)**

9. **Automated key rotation:**
   ```
   ! Configure overlapping keys
   key chain EIGRP-KEYS
     key 1
       key-string OldKey
       send-lifetime 00:00:00 Jan 1 2024 23:59:59 Mar 31 2024
       accept-lifetime 00:00:00 Jan 1 2024 23:59:59 Apr 7 2024
     key 2
       key-string NewKey
       send-lifetime 00:00:00 Apr 1 2024 infinite
       accept-lifetime 00:00:00 Mar 25 2024 infinite
   ```

**Rollback procedures:**

- **Immediate rollback:**
  ```
  ! BGP
  router bgp 65001
    no neighbor 10.1.1.1 password
  
  ! OSPF
  interface GigabitEthernet0/0
    no ip ospf authentication
  
  ! EIGRP
  interface GigabitEthernet0/0
    no ip authentication mode eigrp 100
  ```

- Keep previous configuration backed up
- Have console access ready
- Stage support staff

**Communication plan:**
- Weekly status updates to stakeholders
- Pre-change notifications to NOC
- Detailed maintenance windows scheduled
- Escalation procedures documented

**Success criteria:**
- Zero unplanned outages
- All routing protocols authenticated within 12 weeks
- Key rotation procedures documented and tested
- Monitoring in place for authentication failures

### Q9: You discover that a BGP peer is advertising your prefixes with additional AS numbers in the path. What could be happening and how do you investigate?

**Answer:**

**Possible scenarios:**

1. **Legitimate AS prepending:**
   - Your own AS path prepending for traffic engineering
   - Verify your outbound route-maps
   ```
   show ip bgp neighbor 10.1.1.1 advertised-routes
   show route-map
   ```

2. **AS path manipulation (potential attack):**
   - Peer inserting additional ASNs maliciously
   - Could be attempting path hiding or manipulation

3. **BGP confederation:**
   - Private AS numbers in path
   - Normal if confederation is in use

4. **Route leak with manipulation:**
   - Transit provider manipulating paths
   - Possible violation of peering agreement

**Investigation steps:**

1. **Verify the AS path:**
   ```
   show ip bgp 203.0.113.0/24
   show ip bgp neighbors 10.1.1.1 routes
   show ip bgp regexp _65001_65001_65001_  ! Look for repeating ASN
   ```

2. **Check from multiple vantage points:**
   - Use route servers: route-server.eu.routeviews.org
   - RIPE RIS looking glass
   - Hurricane Electric BGP toolkit
   - Compare AS paths from different locations

3. **Review your configuration:**
   ```
   show run | section router bgp
   show route-map OUTBOUND_POLICY
   ```

4. **Analyze BGP updates:**
   ```
   debug ip bgp updates
   show ip bgp neighbors 10.1.1.1 received-routes
   ```

5. **Check for AS path filters:**
   ```
   show ip as-path-access-list
   show ip bgp filter-list
   ```

**Responses based on findings:**

**If legitimate prepending:**
- Verify this matches intended policy
- Document in change records

**If unauthorized manipulation:**

1. **Immediate action:**
   - Contact peer's NOC immediately
   - Request explanation and correction
   - Document evidence (BGP table dumps, timestamps)

2. **Technical mitigation:**
   ```
   ! Filter out manipulated routes
   router bgp 65001
     neighbor 10.1.1.1 filter-list 10 in
   
   ip as-path access-list 10 permit ^65002_[0-9]+$
   ! Only allow peer's AS plus one additional hop
   ```

3. **Escalation:**
   - Report to ISP abuse contacts if applicable
   - Involve peering coordinators
   - Legal review if contractual violation
   - Consider terminating peering relationship

4. **Monitoring enhancement:**
   - Set up alerts for unexpected AS path patterns
   - Implement automated AS path validation
   - Regular audits of received routes

**Security controls to implement:**

```
! BGP inbound filtering example
router bgp 65001
  neighbor 10.1.1.1 route-map SECURE-IN in

route-map SECURE-IN permit 10
  match as-path 20
  ! Additional policy checks

ip as-path access-list 20 permit ^65002_  ! Must originate from peer AS
ip as-path access-list 20 deny _65001_    ! Block our own AS (loop prevention)
ip as-path access-list 20 permit ^65002(_[0-9]+){1,5}$  ! Limit path length
```

**Long-term prevention:**
- Implement RPKI ROV to validate origins
- Use IRR-based filtering
- Regular peer audit procedures
- Automated monitoring for path anomalies
- Clear peering policies in contracts

### Q10: Design a secure OSPF architecture for a large campus network with multiple buildings, DMZs, and guest networks.

**Answer:**

**Architecture design:**

**1. Area design for security segmentation:**

```
Area 0 (Backbone):
- Core routers only
- High-security authentication
- Minimal LSA propagation
- No user VLANs

Area 1 (Building A - Corporate):
- Standard area with full LSAs
- Corporate user access
- Server farms

Area 2 (Building B - Corporate):
- Standard area
- Corporate users

Area 10 (DMZ):
- Stub area (no external LSAs)
- Only default route from backbone
- Web servers, mail servers

Area 20 (Guest Networks):
- Totally Stubby area
- Only default route
- No internal routing information
- High isolation

Area 30 (Management):
- Standard area
- Network management systems
- Monitoring infrastructure
```

**2. Authentication hierarchy:**

```
! Area 0 (Backbone) - Strongest authentication
router ospf 1
  area 0 authentication message-digest

interface range Gi0/1-4  ! Core interconnects
  ip ospf authentication message-digest
  ip ospf message-digest-key 1 md5 7 StrongBackboneKey123
  ip ospf network point-to-point  ! Security: prevent DR/BDR election
  ip ospf hello-interval 5
  ip ospf dead-interval 20

! Building areas - Standard authentication
interface range Gi0/10-20
  ip ospf authentication message-digest
  ip ospf message-digest-key 1 md5 7 BuildingKey456

! DMZ - Enhanced security with additional controls
interface Gi0/30
  ip ospf authentication message-digest
  ip ospf message-digest-key 1 md5 7 DMZKey789
  ip ospf priority 0  ! Prevent becoming DR
  ip ospf mtu-ignore  ! Prevent MTU mismatch attacks
```

**3. Area type security configurations:**

```
! DMZ as Stub Area
router ospf 1
  area 10 stub
  area 10 authentication message-digest
  
! Guest as Totally Stubby
router ospf 1
  area 20 stub no-summary
  area 20 authentication message-digest
  area 20 default-cost 100  ! Make less preferred

! NSSA for external routes with control
router ospf 1
  area 30 nssa default-information-originate
  area 30 authentication message-digest
```

**4. Passive interfaces for security:**

```
router ospf 1
  passive-interface default  ! Secure by default
  no passive-interface Gi0/1  ! Explicitly enable trusted links
  no passive-interface Gi0/2
  
  ! User-facing VLANs remain passive
  passive-interface Vlan100  ! Corporate users
  passive-interface Vlan200  ! Guest WiFi
  passive-interface Vlan300  ! DMZ servers
```

**5. Route filtering and summarization:**

```
! Filter sensitive routes from less-trusted areas
router ospf 1
  area 10 range 10.10.0.0 255.255.0.0  ! Summarize DMZ
  area 20 range 10.20.0.0 255.255.0.0  ! Summarize Guest
  
  ! Prevent specific routes from propagating
  distribute-list prefix-list FILTER-SENSITIVE in
  
ip prefix-list FILTER-SENSITIVE deny 10.99.99.0/24  ! Management network
ip prefix-list FILTER-SENSITIVE deny 10.88.88.0/24  ! Critical servers
ip prefix-list FILTER-SENSITIVE permit 0.0.0.0/0 le 32

! Filter at area boundaries
router ospf 1
  area 10 filter-list prefix BLOCK-INTERNAL in
  
ip prefix-list BLOCK-INTERNAL deny 10.1.0.0/16  ! Corporate internal
ip prefix-list BLOCK-INTERNAL permit 0.0.0.0/0 le 32
```

**6. LSA flood protection:**

```
! Limit LSA flooding to prevent DoS
router ospf 1
  max-lsa 10000
  
! Per-interface rate limiting
interface Gi0/10
  ip ospf flood-reduction  ! Reduce periodic flooding
  ip ospf lsa-interval 100  ! Minimum interval between LSAs
```

**7. Virtual links security (if needed):**

```
! Secure virtual links through non-backbone areas
router ospf 1
  area 5 virtual-link 10.1.1.1 authentication message-digest
  area 5 virtual-link 10.1.1.1 message-digest-key 1 md5 7 VirtualKey
```

**8. Route authentication at redistribution points:**

```
! Tag routes for tracking and filtering
router ospf 1
  redistribute bgp 65001 subnets route-map OSPF-REDIST tag 100

route-map OSPF-REDIST permit 10
  match ip address prefix-list ALLOWED-EXTERNAL
  set metric-type type-1
  set metric 1000
  set tag 100
  
! Filter redistributed routes
ip prefix-list ALLOWED-EXTERNAL permit 203.0.113.0/24
ip prefix-list ALLOWED-EXTERNAL deny 0.0.0.0/0 le 32
```

**9. Additional security controls:**

```
! TTL security
interface Gi0/1
  ip ospf ttl-security all-interfaces hops 1  ! Adjacent routers only

! Prevent OSPF on unauthorized interfaces
interface range Gi0/40-48
  no ip ospf network  ! Explicitly disable
  
! Control plane policing for OSPF
control-plane
  service-policy input CONTROL-PLANE-POLICY
  
class-map match-all OSPF-CONTROL
  match access-group 120
  
policy-map CONTROL-PLANE-POLICY
  class OSPF-CONTROL
    police 8000 conform-action transmit exceed-action drop
    
access-list 120 permit ospf any any
```

**10. Monitoring and alerting:**

```
! SNMP traps for OSPF events
router ospf 1
  log-adjacency-changes detail
  
! Syslog for security events
logging trap informational
logging 10.99.99.10

! Track OSPF neighbor changes
track 1 interface GigabitEthernet0/1 line-protocol
  
! EEM script for automated response
event manager applet OSPF-NEIGHBOR-DOWN
  event syslog pattern "OSPF-5-ADJCHG.*Down"
  action 1.0 syslog msg "OSPF neighbor down - investigating"
  action 2.0 cli command "show ip ospf neighbor"
```

**11. Segmentation between areas:**

```
! Use ACLs between areas for additional control
interface Vlan10  ! DMZ interface
  ip address 10.10.1.1 255.255.255.0
  ip access-group DMZ-IN in
  ip access-group DMZ-OUT out
  
! Allow only necessary traffic from DMZ
ip access-list extended DMZ-IN
  permit tcp 10.10.0.0 0.0.255.255 any eq 443
  permit icmp 10.10.0.0 0.0.255.255 any echo
  deny ip any any log
```

**12. Key rotation procedures:**

```
! Implement overlapping key rotation
key chain OSPF-KEYS
  key 1
    key-string CurrentKey
    accept-lifetime 00:00:00 Jan 1 2024 23:59:59 Jun 30 2024
    send-lifetime 00:00:00 Jan 1 2024 23:59:59 May 31 2024
  key 2
    key-string NextKey
    accept-lifetime 00:00:00 May 1 2024 infinite
    send-lifetime 00:00:00 Jun 1 2024 infinite
```

**Benefits of this architecture:**
- Defense in depth with multiple security layers
- Limited blast radius from compromised areas
- Minimal routing information exposure
- Controlled external route propagation
- Clear segmentation for compliance (PCI DSS, etc.)
- Reduces attack surface significantly

**Operational considerations:**
- Document area design clearly
- Train staff on security controls
- Regular audits of OSPF configuration
- Test failover scenarios
- Maintain change control for routing changes

## Category 2: OSPF & IGP Security (Questions 11-25)

### Q11: You see thousands of LSA type 5 flooding your OSPF domain causing CPU spikes. How do you troubleshoot and mitigate?

**Answer:**

**Immediate troubleshooting:**

1. **Identify the source:**
   ```
   show ip ospf database external
   show ip ospf database summary
   show ip ospf statistics
   ```
   Look for advertising router IDs generating excessive LSAs

2. **Check LSA rate:**
   ```
   show ip ospf database database-summary
   ! Note the number of Type-5 LSAs
   show ip ospf flood-list
   ```

3. **Identify the ASBR:**
   ```
   show ip ospf border-routers
   show ip ospf database asbr-summary
   ```

4. **Examine specific LSAs:**
   ```
   show ip ospf database external 0.0.0.0
   show ip ospf database external adv-router 10.1.1.1
   ```

**Root causes:**

1. **Route redistribution loop:**
   - Two ASBRs redistributing into each other
   - BGP routes being redistributed without proper filtering

2. **Unstable external routes:**
   - Flapping BGP sessions causing constant updates
   - Unstable connected interfaces being redistributed

3. **Misconfigured redistribution:**
   - Redistributing full BGP table into OSPF
   - No route filtering applied

4. **Malicious activity:**
   - Compromised router injecting routes
   - DoS attack targeting OSPF

**Immediate mitigation:**

1. **Rate limiting (quick fix):**
   ```
   router ospf 1
     timers throttle lsa all 5000 10000 60000
     ! Delays: start-interval, hold-interval, max-wait
   ```

2. **LSA flood protection:**
   ```
   router ospf 1
     max-lsa 12000 80 warning-only
     ! Alert at 9600 LSAs, warning only (don't shutdown)
   ```

3. **Emergency shutdown of problem ASBR:**
   ```
   ! If ASBR 10.1.1.1 is the source
   router ospf 1
     no redistribute bgp 65001
   ```

4. **Control plane policing:**
   ```
   class-map match-all OSPF-CRITICAL
     match access-group 150
   
   policy-map COPP-POLICY
     class OSPF-CRITICAL
       police 10000 conform-action transmit exceed-action drop
   
   access-list 150 permit ospf any any
   
   control-plane
     service-policy input COPP-POLICY
   ```

**Long-term solutions:**

1. **Fix redistribution configuration:**
   ```
   router ospf 1
     redistribute bgp 65001 subnets route-map BGP-TO-OSPF
   
   ! Only redistribute specific prefixes
   route-map BGP-TO-OSPF permit 10
     match ip address prefix-list CUSTOMER-ROUTES
     set metric 1000
     set metric-type type-1
     set tag 100
   
   ip prefix-list CUSTOMER-ROUTES permit 10.100.0.0/16
   ip prefix-list CUSTOMER-ROUTES deny 0.0.0.0/0 le 32
   ```

2. **Prevent redistribution loops:**
   ```
   ! On ASBR-1
   router ospf 1
     redistribute bgp 65001 subnets route-map BGP-TO-OSPF
   
   route-map BGP-TO-OSPF deny 10
     match tag 100  ! Deny routes tagged by other ASBR
   route-map BGP-TO-OSPF permit 20
     match ip address prefix-list ALLOWED
     set tag 200    ! Tag our redistributed routes
   
   ! On ASBR-2
   router ospf 1
     redistribute bgp 65001 subnets route-map BGP-TO-OSPF
   
   route-map BGP-TO-OSPF deny 10
     match tag 200  ! Deny routes tagged by ASBR-1
   route-map BGP-TO-OSPF permit 20
     match ip address prefix-list ALLOWED
     set tag 100
   ```

3. **Use stub areas to block Type-5:**
   ```
   ! Convert appropriate areas to stub
   router ospf 1
     area 10 stub
     area 20 stub no-summary  ! Totally stubby
   
   ! Type-5 LSAs won't propagate into stub areas
   ```

4. **Implement NSSA for controlled external routes:**
   ```
   router ospf 1
     area 30 nssa
     area 30 nssa default-information-originate
   
   ! Type-7 LSAs only, converted to Type-5 at ABR
   ! Better control over external route propagation
   ```

5. **Route summarization:**
   ```
   router ospf 1
     summary-address 10.100.0.0 255.255.0.0
     summary-address 10.200.0.0 255.255.0.0
   
   ! Reduce number of Type-5 LSAs significantly
   ```

**Monitoring and prevention:**

1. **Set appropriate thresholds:**
   ```
   router ospf 1
     max-lsa 10000 75
     ! Shutdown OSPF if exceeds 7500 LSAs
   ```

2. **SNMP monitoring:**
   ```
   router ospf 1
     log-adjacency-changes detail
   
   snmp-server enable traps ospf lsa
   snmp-server host 10.99.99.10 traps version 2c community
   ```

3. **EEM automation:**
   ```
   event manager applet OSPF-LSA-FLOOD
     event syslog pattern "OSPF-4-OSPF_MAX_LSA_THR"
     action 1.0 cli command "enable"
     action 2.0 cli command "show ip ospf database external"
     action 3.0 syslog msg "OSPF LSA threshold exceeded - check ASBR"
     action 4.0 mail server "mail.company.com" to "noc@company.com"
   ```

4. **Regular audits:**
   - Review redistribution configurations monthly
   - Monitor LSA database growth trends
   - Check for unnecessary redistribution points

**Post-incident:**
- Document root cause
- Review all redistribution points
- Update change control procedures
- Test in lab before implementing

### Q12: Two OSPF neighbors won't form adjacency. Walk through your systematic troubleshooting approach.

**Answer:**

**Systematic troubleshooting ladder:**

**1. Layer 1/2 - Physical connectivity:**
```
show interface GigabitEthernet0/1
! Check: line protocol up, no excessive errors
show interface GigabitEthernet0/1 | include error
show interface counters errors

! Test bidirectional connectivity
ping 10.1.1.2 source GigabitEthernet0/1
```

**2. Layer 3 - IP connectivity:**
```
show ip interface brief
! Verify correct IP addressing and subnet

! Common issue: Wrong subnet mask
Router1: 10.1.1.1/24
Router2: 10.1.1.2/30  ❌ Won't form adjacency!

! Verify same subnet
show ip interface GigabitEthernet0/1
```

**3. OSPF enabled and correct network statements:**
```
show ip ospf interface GigabitEthernet0/1
! If shows nothing, OSPF not enabled on interface

show run | section router ospf
! Verify network statement includes interface

! Correct configuration:
router ospf 1
  network 10.1.1.0 0.0.0.255 area 0
```

**4. OSPF hello/dead timers mismatch:**
```
show ip ospf interface GigabitEthernet0/1
! Check: Hello time, Dead time

! Must match on both sides
Router1: Hello 10, Dead 40
Router2: Hello 5, Dead 20  ❌ Mismatch!

! Fix:
interface GigabitEthernet0/1
  ip ospf hello-interval 10
  ip ospf dead-interval 40
```

**5. Area mismatch:**
```
show ip ospf interface GigabitEthernet0/1
! Verify area number

Router1: Area 0
Router2: Area 1  ❌ Won't form adjacency!

! Fix:
router ospf 1
  network 10.1.1.0 0.0.0.255 area 0
```

**6. Network type mismatch:**
```
show ip ospf interface GigabitEthernet0/1
! Check: Network Type

Router1: BROADCAST
Router2: POINT-TO-POINT  ❌ Mismatch!

! Fix: Match network types
interface GigabitEthernet0/1
  ip ospf network point-to-point
```

**7. Authentication mismatch:**
```
show ip ospf interface GigabitEthernet0/1
! Check: Authentication type and key

Router1: MD5 authentication, Key ID 1
Router2: No authentication  ❌ Mismatch!

! Enable debug carefully
debug ip ospf adj
! Look for "Mismatched authentication type"

! Fix authentication:
interface GigabitEthernet0/1
  ip ospf authentication message-digest
  ip ospf message-digest-key 1 md5 SameKeyOnBoth
```

**8. MTU mismatch:**
```
show interface GigabitEthernet0/1 | include MTU
Router1: MTU 1500
Router2: MTU 1400  ❌ DBD exchange fails!

! OSPF neighbors stuck in EXSTART/EXCHANGE

! Options:
! Option 1: Match MTU
interface GigabitEthernet0/1
  mtu 1500

! Option 2: Ignore MTU mismatch (workaround)
interface GigabitEthernet0/1
  ip ospf mtu-ignore
```

**9. Duplicate Router ID:**
```
show ip ospf
! Check router ID

Router1: Router ID 10.1.1.1
Router2: Router ID 10.1.1.1  ❌ Same RID!

! Fix: Set unique router IDs
router ospf 1
  router-id 10.1.1.2
clear ip ospf process
```

**10. Passive interface configuration:**
```
show ip ospf interface GigabitEthernet0/1
! If shows "passive", won't send hellos

router ospf 1
  no passive-interface GigabitEthernet0/1
```

**11. Access lists blocking OSPF:**
```
show ip interface GigabitEthernet0/1 | include access list
show ip access-lists

! OSPF uses protocol 89
! Check for blocking ACL

! Fix: Permit OSPF
ip access-list extended INTERFACE-ACL
  permit ospf any any
  ... other rules ...
```

**12. Stub area mismatch:**
```
show ip ospf | section area
show run | section router ospf

Router1: area 1 stub
Router2: area 1 (not stub)  ❌ Mismatch!

! Fix: Match stub configuration
router ospf 1
  area 1 stub
```

**13. Process ID vs. Router ID confusion:**
```
! Common misconception
Router1: router ospf 1
Router2: router ospf 2

! Process ID is locally significant only
! ✓ This is fine - check other parameters
```

**14. Virtual link issues (if applicable):**
```
show ip ospf virtual-links

! Virtual link must match on both ends
router ospf 1
  area 5 virtual-link 10.1.1.1
  area 5 virtual-link 10.1.1.1 authentication message-digest
  area 5 virtual-link 10.1.1.1 message-digest-key 1 md5 Key
```

**Debugging approach:**

```
! Enable targeted debugging
debug ip ospf hello
debug ip ospf adj

! Watch for specific errors:
! - "Mismatched authentication"
! - "Dead timer expired"
! - "Area mismatch"
! - "Hello timer mismatch"

! Turn off debugging after troubleshooting
undebug all
```

**Verification after fix:**

```
! Check neighbor state
show ip ospf neighbor
! Should show FULL state (or 2WAY on broadcast if not DR/BDR)

! Verify routes exchanged
show ip route ospf

! Check interface details
show ip ospf interface GigabitEthernet0/1

! Monitor stability
show ip ospf neighbor detail
! Check: State changes, Dead time countdown
```

**Documented checklist for quick reference:**

1. ☐ Physical/Data link up
2. ☐ IP connectivity (same subnet)
3. ☐ OSPF enabled on interface
4. ☐ Hello/Dead timers match
5. ☐ Area numbers match
6. ☐ Network types match
7. ☐ Authentication matches
8. ☐ MTU matches or ignored
9. ☐ Unique Router IDs
10. ☐ Not passive interface
11. ☐ No blocking ACLs
12. ☐ Stub settings match

**Common pitfalls:**
- Forgetting to check both directions
- Not verifying authentication keys match exactly
- Overlooking MTU mismatches
- Assuming process ID must match (it doesn't)
- Not checking for duplicate RIDs across domain

### Q13: Design an EIGRP security architecture for a multi-site retail network with automated key rotation.

**Answer:**

**Network topology:**
- HQ (Hub): Corporate datacenter
- 500 Branch stores (Spokes): Retail locations
- Regional distribution centers: 10 locations
- Hub-and-spoke DMVPN topology

**Architecture components:**

**1. EIGRP named mode configuration (HQ hub):**

```
! Named mode required for advanced features
router eigrp RETAIL-WAN
  !
  address-family ipv4 unicast autonomous-system 100
    !
    af-interface default
      authentication mode hmac-sha-256 RETAIL-KEYS
      hello-interval 30
      hold-time 90
      split-horizon
      ! Passive by default for security
      passive-interface
    !
    af-interface Tunnel0
      ! Enable on DMVPN tunnel
      no passive-interface
      authentication mode hmac-sha-256 RETAIL-KEYS
      ! Reduce hello overhead for 500 spokes
      hello-interval 60
      hold-time 180
      ! Stub configuration for spokes
      stub-site wan-interface
    !
    topology base
      distribute-list prefix DEFAULT-ONLY out Tunnel0
      redistribute connected route-map REDISTRIBUTE-CONNECTED
    !
    network 10.0.0.0 0.255.255.255
    network 172.16.0.0 0.15.255.255
    !
    eigrp router-id 10.255.255.1
    eigrp stub-routing connected summary
  !
```

**2. Key chain design with automated rotation:**

```
! Primary key chain - 90-day rotation
key chain RETAIL-KEYS
  key 1
    key-string Q1-2024-SecureKey-Alpha-7x9!
    cryptographic-algorithm hmac-sha-256
    send-lifetime 00:00:00 Jan 1 2024 23:59:59 Mar 31 2024
    accept-lifetime 00:00:00 Dec 25 2023 23:59:59 Apr 7 2024
  key 2
    key-string Q2-2024-SecureKey-Bravo-4m2@
    cryptographic-algorithm hmac-sha-256
    send-lifetime 00:00:00 Apr 1 2024 23:59:59 Jun 30 2024
    accept-lifetime 00:00:00 Mar 25 2024 23:59:59 Jul 7 2024
  key 3
    key-string Q3-2024-SecureKey-Charlie-8n5#
    cryptographic-algorithm hmac-sha-256
    send-lifetime 00:00:00 Jul 1 2024 23:59:59 Sep 30 2024
    accept-lifetime 00:00:00 Jun 25 2024 23:59:59 Oct 7 2024
  key 4
    key-string Q4-2024-SecureKey-Delta-1p6$
    cryptographic-algorithm hmac-sha-256
    send-lifetime 00:00:00 Oct 1 2024 23:59:59 Dec 31 2024
    accept-lifetime 00:00:00 Sep 25 2024 23:59:59 Jan 7 2025
```

**3. Branch spoke configuration:**

```
router eigrp RETAIL-WAN
  !
  address-family ipv4 unicast autonomous-system 100
    !
    af-interface default
      authentication mode hmac-sha-256 RETAIL-KEYS
      passive-interface
    !
    af-interface Tunnel0
      no passive-interface
      authentication mode hmac-sha-256 RETAIL-KEYS
      hello-interval 60
      hold-time 180
    !
    topology base
    !
    network 10.0.0.0 0.255.255.255
    network 192.168.0.0 0.0.255.255
    !
    eigrp router-id 10.1.STORE_ID.1
    ! Stub routing - reduce query scope
    eigrp stub connected summary
  !
```

**4. Regional distribution center configuration:**

```
router eigrp RETAIL-WAN
  !
  address-family ipv4 unicast autonomous-system 100
    !
    af-interface default
      authentication mode hmac-sha-256 RETAIL-KEYS
      passive-interface
    !
    af-interface Tunnel0
      no passive-interface
      authentication mode hmac-sha-256 RETAIL-KEYS
      hello-interval 30
      hold-time 90
    !
    af-interface Tunnel1
      no passive-interface
      authentication mode hmac-sha-256 RETAIL-KEYS
    !
    topology base
      ! Leak specific routes to branches
      leak-map CRITICAL-SERVICES
    !
    network 10.0.0.0 0.255.255.255
    network 172.20.0.0 0.0.255.255
    !
    eigrp router-id 10.200.REGION_ID.1
  !
```

### Comprehensive Guide to Senior-Level Network Security: Routing-Related Topics and Concepts

As a senior network security engineer preparing for interviews, you'll encounter questions that probe not just rote knowledge but your ability to reason through real-world scenarios involving routing protocols, vulnerabilities, and mitigation strategies. Routing security is a critical intersection of protocol design, cryptographic protections, and operational resilience, especially in distributed systems like cloud-native environments (e.g., CNCF's Kubernetes with Calico or Cilium for eBPF-based routing). Interviewers often frame questions around failure modes, attack vectors, and trade-offs in secure system design—emphasizing zero-trust principles, memory-safe implementations (e.g., Rust for routing daemons), and algorithmic efficiency in threat detection.

This guide is structured for depth and clarity:
1. **Core Concepts**: Foundational routing security principles.
2. **Key Protocols and Vulnerabilities**: Protocol-specific breakdowns.
3. **Advanced Topics**: Emerging paradigms like SDN and eBPF.
4. **Best Practices and Tools**: Real-world engineering approaches.
5. **Scenario-Based Interview Prep**: 100 questions and answers, categorized for targeted study (e.g., 25 on BGP, 20 on OSPF, etc., totaling 100). Each Q&A includes a brief rationale tying back to systems engineering.

Focus on **scenario-based thinking**: For each question, mentally map the attack surface (e.g., control plane vs. data plane), evaluate mitigations (e.g., cryptographic vs. filtering), and consider scalability (e.g., in a multi-tenant cloud datacenter).

#### 1. Core Concepts
- **Routing Security Pillars**: Confidentiality (encrypted updates), Integrity (anti-tampering, e.g., via digital signatures), Availability (DDoS resilience via blackholing), and Authenticity (peer validation to prevent spoofing).
- **Threat Model**: Insider threats (rogue AS), external hijacks (route leaks), amplification attacks (e.g., BGP path poisoning), and side-channel leaks (e.g., timing in route convergence).
- **Zero-Trust Routing**: Assume no implicit trust; enforce per-packet policies, micro-segmentation via route tags, and dynamic revocation (e.g., RPKI for BGP).
- **Algorithmic Foundations**: Understand shortest-path algorithms (Dijkstra in OSPF) for vulnerability analysis—e.g., how poisoned routes propagate exponentially in link-state floods.

#### 2. Key Protocols and Vulnerabilities
| Protocol | Security Features | Common Vulnerabilities | Mitigation Strategies |
|----------|-------------------|------------------------|-----------------------|
| **BGP (Exterior Gateway)** | MD5/TCP-AO authentication; RPKI (ROA validation); Communities for filtering. | Route hijacking (e.g., Pakistan YouTube incident); Leaks (e.g., Level3-T-Mobile); Prefix hijacks. | AS-path prepending; Max-prefix limits; BGPsec (draft standard for hop-by-hop signing). |
| **OSPF (Interior Link-State)** | MD5 authentication; Area authentication; Hello padding. | Flooding attacks (LSAs overload CPU); Sequence number replay; Man-in-the-middle (MITM) on adjacencies. | Area border restrictions; LSA pacing; IPsec encapsulation. |
| **RIP (Distance-Vector)** | RIPv2 MD5; Split horizon/poison reverse. | Count-to-infinity loops; Route poisoning. | Rarely used in enterprise; migrate to EIGRP/OSPF. |
| **EIGRP (Hybrid)** | MD5; Diffie-Hellman key exchange (modern). | Proprietary (Cisco-only); SIA (stuck-in-active) exploits. | DUAL algorithm enhancements for loop prevention. |
| **Multicast (PIM)** | Scoped zones; RP election security. | RPF failures leading to DDoS; RP hijacking. | MSDP with SHA-256 hashing; Anycast RP. |

- **Vulnerability Patterns**: Control-plane exhaustion (e.g., BGP UPDATE storms), data-plane diversion (blackhole routing), and convergence delays (e.g., 15-min BGP hold timers exploited for persistence).

#### 3. Advanced Topics
- **SDN and Programmable Routing**: In CNCF ecosystems (e.g., OpenDaylight), secure southbound APIs (OpenFlow) with TLS; eBPF for kernel-level route inspection without user-space overhead.
- **Cloud-Native Routing Security**: Cilium/Hubble for eBPF-based L7 policies; secure overlays (WireGuard in Rust for memory safety); multi-cluster BGP (e.g., in EKS with Calico).
- **Emerging Threats**: Quantum-resistant crypto for BGP (post-quantum signatures); AI-driven anomaly detection in route flaps using ML on NetFlow.
- **Distributed Systems Angle**: Consensus in routing (e.g., Raft-inspired for route election); fault-tolerant designs (e.g., Byzantine resilience in BGP peering).

#### 4. Best Practices and Tools
- **Configuration Hygiene**: Always enable authentication; use route-maps for granular filtering; audit with Batfish (model-based validation).
- **Monitoring and Response**: eBPF probes for real-time route tracing; SIEM integration (e.g., ELK with BGP logs); automated blackholing via BGP communities.
- **Tools**: FRR (Free Range Routing) for open-source BGP with Rust bindings; ExaBGP for testing hijacks; RPKI validators (e.g., Routinator).
- **Innovation Tip**: Design hybrid systems—e.g., Go-based microservices for dynamic route injection with Python scripts for simulation (using Mininet).

Study Tip: Simulate scenarios with GNS3/EVE-NG; read RFCs (e.g., 7454 for BGP operations) for rigor. For interviews, articulate trade-offs: e.g., RPKI's global coordination vs. local filtering's speed.

---

### 100 Scenario-Based Questions and Answers

Questions are categorized for efficiency (e.g., BGP: 25 Qs; OSPF: 20; etc.). Each answer is concise yet rigorous: **Problem Analysis** → **Solution** → **Rationale/Trade-offs**. Focus on senior-level depth—e.g., protocol internals, scalability.

#### BGP Security (Questions 1-25)
1. **Q: In a multi-homed ISP setup, an upstream provider accidentally announces your /24 prefix with a shorter /16 mask. How does this manifest as a security incident, and what's your immediate mitigation?**  
   **A:** Analysis: This is a route leak causing prefix hijacking; traffic diverts to the leak source, enabling eavesdropping/MITM. Solution: Implement max-prefix limits on peering sessions (e.g., `neighbor X.X.X.X maximum-prefix 100`) and withdraw the invalid route via communities (e.g., NO_EXPORT). Rationale: Limits bound exposure; RPKI ROAs would prevent propagation, but local filters act faster in convergence (sub-60s). Trade-off: Overly strict limits risk legitimate growth blocking.

2. **Q: During a BGP session flap, an attacker sends forged UPDATE messages with invalid AS_PATH. How do you detect and prevent replay?**  
   **A:** Analysis: Forged paths enable route poisoning, inflating metrics for diversion. Solution: Enable TCP-AO (RFC 5925) over MD5 for sequence-number integrity; monitor with BGPmon for anomaly detection. Rationale: AO provides cryptographic sequencing without key exposure risks of MD5. Trade-off: Higher CPU overhead in high-volume peers.

3. **Q: Your enterprise peers with a cloud provider via BGP. A competitor spoofs your AS and advertises blackhole communities. Scenario: All outbound traffic loops infinitely. Fix?**  
   **A:** Analysis: AS spoofing triggers route withdrawal loops via invalid communities. Solution: Enforce AS_PATH regex filtering (e.g., `ip as-path access-list 1 permit ^65000$`) and RPKI validation to drop non-originating routes. Rationale: Regex ensures prepend authenticity; RPKI scales globally. Trade-off: Regex compilation is O(n) expensive on large tables.

4. **Q: In a DDoS attack, the attacker uses BGP flowspec to redirect SYN floods to your scrubbing center, but it backfires and amplifies to your upstream. Response?**  
   **A:** Analysis: Flowspec (RFC 8955) rules propagate, but misconfig causes re-amplification. Solution: Withdraw flowspec rules post-scrub and use RTBH (remote triggered blackholing) with more-specific prefixes. Rationale: RTBH is deterministic; flowspec adds rule complexity. Trade-off: Blackholing drops all, vs. flowspec's granular L4 filtering.

5. **Q: A junior admin enables BGP without authentication on a customer edge router. An insider from the customer injects routes advertising malware C2 servers. Contain it.**  
   **A:** Analysis: Unauth peering allows arbitrary prefix insertion, poisoning global tables. Solution: Shut down the session (`neighbor X.X.X.X shutdown`), apply inbound prefix-lists denying non-customer aggregates, then re-enable with MD5. Rationale: Prefix-lists are lightweight ACLs; MD5 retrofits legacy peers. Trade-off: MD5 vulnerable to offline attacks if keys leak.

6. **Q: During route convergence after a fiber cut, an attacker floods KEEPALIVEs to exhaust TCP windows. How does this exploit BGP's hold timer, and mitigate?**  
   **A:** Analysis: Flooding delays hold-timer expiry (default 180s), stalling convergence. Solution: Tune hold-timer to 60s and implement rate-limiting on BGP port 179 via CoPP (Control Plane Policing). Rationale: Shorter timers speed fail-over; CoPP prevents DoS at L3. Trade-off: Frequent flaps increase instability.

7. **Q: Your BGP table shows a sudden spike in paths for a critical prefix from a new AS. Suspect hijack—verify and remediate.**  
   **A:** Analysis: New AS indicates injection; check via Looking Glass tools. Solution: Query RPKI for ROA mismatch, then prepend your AS multiple times to de-preference hijacked paths. Rationale: Prepending restores preference without global coordination. Trade-off: Increases path length, bloating tables.

8. **Q: In a confederation setup, sub-AS leaks poison routes across iBGP. Scenario: Internal loops cause packet drops. Secure it.**  
   **A:** Analysis: Leaks bypass confederation boundaries, violating split-horizon. Solution: Apply LOCAL_PREF filters on sub-AS boundaries and use SOO (Site-of-Origin) extended communities. Rationale: SOO prevents re-advertisement loops algorithmically. Trade-off: Adds state to route selection.

9. **Q: An attacker uses BGP to announce anycast IPs mimicking your DNS servers, causing cache poisoning. Defensive routing?**  
   **A:** Analysis: Anycast hijack diverts queries to rogue servers. Solution: Use GeoIP-based communities for selective advertisement and RPKI for origin validation. Rationale: GeoIP adds location-aware granularity. Trade-off: Requires accurate IRR data.

10. **Q: Post-quantum era: How would Shor's algorithm break BGPsec signatures? Propose a forward-secure alternative.**  
    **A:** Analysis: Breaks ECDSA in BGPsec (hop-by-hop signing). Solution: Migrate to lattice-based signatures (e.g., Dilithium per NIST PQC). Rationale: PQC resists quantum; forward secrecy via ephemeral keys. Trade-off: Larger sig sizes inflate UPDATEs.

11-25: (Condensed for brevity; expand in practice)  
11. Q: VPN overlay leaks BGP routes to underlay—fix encapsulation mismatch. A: Use VRF-lite with route-leaking ACLs; rationale: Isolates namespaces.  
12. Q: eBGP multihop exploited for tunneling attacks. A: Set TTL=1 strictly; trade-off: Limits loopback peering.  
13. Q: Route reflector cluster-id collision causes selection errors. A: Unique IDs per cluster; rationale: Prevents non-deterministic paths.  
14. Q: MD5 key rotation during active session—impact? A: Session flap; use rolling keys with TCP-AO.  
15. Q: BGP dampening punishes a flapping peer unfairly. A: Tune reuse/suppress thresholds; rationale: Balances stability vs. responsiveness.  
16. Q: Customer de-aggregates prefixes, bloating your table. A: Enforce aggregation policies via templates.  
17. Q: iBGP full-mesh scales poorly in 100-router net—secure scaling? A: Confederations with RR; rationale: Reduces sessions O(n^2).  
18. Q: Attacker forges ORIGINATOR_ID in RR paths. A: Validate via cluster-list filtering.  
19. Q: Flowspec for HTTP flood mitigation fails on IPv6. A: Extend to BGP-MP; trade-off: Dual-stack complexity.  
20. Q: RPKI cache poisoning via TAL compromise. A: Use multiple TAs; rationale: Byzantine fault tolerance.  
21. Q: BGP UPDATE storm from misconfig neighbor. A: Input/output rate-limits; CoPP integration.  
22. Q: Secure BGP in SDN: OpenFlow table overflows. A: eBPF for offload; rationale: Kernel bypass.  
23. Q: Path vector loop via confederation leak. A: NOPEER community enforcement.  
24. Q: Quantum-safe key exchange for BGP peering. A: Kyber integration in TCP-AO extensions.  
25. Q: Multi-tenant cloud: Isolate BGP per tenant. A: EVPN with VRFs; rationale: Zero-trust segmentation.

#### OSPF Security (Questions 26-45)
26. **Q: In a large OSPF domain, an attacker floods rogue LSAs from a DR-other router, crashing the LSDB. Detect and contain.**  
    **A:** Analysis: LSA floods exploit MaxAge mechanics, causing recomputation storms (SPF O(V^2)). Solution: Enable LSA pacing (RFC 3137) and area authentication with SHA-256. Rationale: Pacing serializes floods; SHA prevents forgery. Trade-off: Delays convergence slightly.

27. **Q: Your OSPF adjacency over a GRE tunnel is MITM'd via ARP spoofing. Secure the link.**  
    **A:** Analysis: GRE lacks native auth, exposing Hellos. Solution: Wrap in IPsec ESP with AES-GCM. Rationale: Provides replay protection; integrates with OSPF's MD5. Trade-off: Overhead ~5-10% latency.

28. **Q: Scenario: Backbone area floods with external LSAs after a type-5 import error, overloading ABRs. Mitigation?**  
    **A:** Analysis: Type-5 proliferation ignores area boundaries. Solution: Configure NSSA with no-summary and LSA filtering. Rationale: Reduces type-7 translation; scales for stub areas. Trade-off: Loses inter-area visibility.

29. **Q: Attacker replays old Hello packets to maintain a silent flap. Exploit details and fix.**  
    **A:** Analysis: Hellos lack timestamps, allowing seq# wrap-around. Solution: Use OSPFv3 with IPsec AH for integrity. Rationale: AH covers L3 headers; v2 MD5 insufficient. Trade-off: v3 migration cost.

30. **Q: In a DMZ with OSPF stub area, a host injects default routes poisoning outbound traffic. Prevent.**  
    **A:** Analysis: Stubs accept default but not externals. Solution: Suppress default propagation with `no default-information originate`. Rationale: Enforces policy-based defaults. Trade-off: Manual static defaults needed.

31-45: (Condensed)  
31. Q: OSPF MD5 key mismatch post-rotation—adj down. A: Graceful reload with key chains.  
32. Q: Virtual link security in partitioned area. A: IPsec tunnel; rationale: Bridges transit securely.  
33. Q: LSA throttling during DoS. A: Max-lsa per-interface; trade-off: Drops legit updates.  
34. Q: OSPF in SDN: Secure controller floods. A: TLS for northbound; eBPF validation.  
35. Q: Type-3 summary LSA spoof in ABR. A: Area auth only; rationale: Per-area keys.  
36. Q: Convergence delay exploited for session hijack. A: BFD integration (10ms detect).  
37. Q: Multicast Hello DoS on 224.0.0.5. A: IGMP snooping filters.  
38. Q: OSPF over untrusted WAN—encrypt? A: DMVPN with NHRP auth.  
39. Q: LSDB overflow in high-mesh net. A: Area segmentation; O(V log V) SPF opt.  
40. Q: Rogue router elects as DR via priority spoof. A: Authenticated priorities in Hellos.  
41. Q: OSPF v2 to v3 migration security gap. A: Dual-stack with parallel auth.  
42. Q: External route poisoning via ASBR. A: Route-tags for filtering.  
43. Q: Backup DR election failure post-flap. A: Preempt with higher priority.  
44. Q: eBPF for OSPF anomaly detection. A: Hook on netfilter for LSA inspect.  
45. Q: Zero-trust OSPF: Per-link policies. A: Micro-segment with ACLs on interfaces.

#### Other Routing Protocols and General (Questions 46-70)
46. **Q: RIPng in IPv6 net: Attacker poisons routes with infinite metrics. Contain the loop.**  
    **A:** Analysis: No poison-reverse in v1; v2 vulnerable to broadcasts. Solution: Enable RIPv2 MD5 and split-horizon. Rationale: Horizon prevents count-to-infinity. Trade-off: Legacy protocol—migrate to OSPFv3.

47. **Q: EIGRP: Stuck-in-Active from query loops in a hub-spoke. Secure query path.**  
    **A:** Analysis: SIA timer (3min) exhausted by divergent replies. Solution: Use summarization on spokes and SIA thresholds. Rationale: Summaries bound query scope. Trade-off: Hides topology details.

48. **Q: PIM-SM RP election hijacked via hash collision. Scenario: Multicast DDoS. Fix?**  
    **A:** Analysis: Hash on group addr vulnerable to crafting. Solution: Bootstrap RP with PKI auth (BSR messages signed). Rationale: PKI ensures election integrity. Trade-off: Embedded RP simpler but less secure.

49. **Q: IS-IS: Attacker floods LSPs with high seq#, causing purge storms. Mitigate.**  
    **A:** Analysis: LSPs lack pacing, leading to O(E) floods. Solution: Enable LSP throttling and HMAC-MD5 auth. Rationale: HMAC covers variable lengths. Trade-off: IS-IS less common than OSPF.

50. **Q: Secure multicast in cloud: Bidir PIM leaks to unauthorized groups. Policy?**  
    **A:** Analysis: Bidir lacks explicit joins, risking floods. Solution: Scoped zones with key-based group auth. Rationale: Scopes limit TTL. Trade-off: Overhead in large clusters.

51-70: (Condensed; mix RIP/EIGRP/PIM/IS-IS/general)  
51. Q: RIP split-horizon bypassed via secondary IP. A: Disable multis.  
52. Q: EIGRP K-values mismatch causes flap. A: Consistent metrics.  
53. Q: PIM Assert loss leads to duplicates. A: Assert timers tune.  
54. Q: IS-IS NET spoof in L1 area. A: Area auth.  
55. Q: General: Route flapping damping in mixed proto. A: BFD for fast detect.  
56. Q: RIP over VPN: Metric inflation. A: Offset-lists.  
57. Q: EIGRP graceful shutdown. A: Stub routing.  
58. Q: PIM DM floods unsecured. A: Migrate to SM.  
59. Q: IS-IS over Ethernet: Designated router spoof. A: LSP auth.  
60. Q: General: Secure route redistribution. A: Tags and maps.  
61. Q: RIPng split-horizon poisoning fail. A: Triggered updates.  
62. Q: EIGRP unequal load-balancing DoS. A: Variance limits.  
63. Q: PIM RP anycast security. A: MSDP peers auth.  
64. Q: IS-IS TLV parsing overflow. A: Input validation.  
65. Q: General: eBPF for proto-agnostic monitoring. A: XDP hooks.  
66. Q: RIP v1 broadcast storm. A: V2 unicast.  
67. Q: EIGRP DUAL loop via misconfig. A: Feasibility checks.  
68. Q: PIM source-specific forwarding fail. A: RPF strict.  
69. Q: IS-IS CSNP corruption. A: IIH auth.  
70. Q: General: Rust impl for secure routing daemon. A: Tokio for async.

#### Advanced/Emerging Topics (Questions 71-100)
71. **Q: In Cilium (eBPF), a pod injects invalid BGP routes via Hubble. Zero-trust fix?**  
    **A:** Analysis: eBPF lacks native auth for user-space injections. Solution: Enforce RBAC on Hubble gRPC with mTLS; validate routes via eBPF maps. Rationale: Maps provide kernel-enforced isolation. Trade-off: Perf hit from map lookups (~1us).

72. **Q: SDN controller (ONOS) compromised, poisoning OpenFlow flow-mods for routes. Detect?**  
    **A:** Analysis: Flows install bogus next-hops. Solution: Anomaly detection with ML on flow stats; sign mods with HMAC. Rationale: Stats reveal divergence from OSPF. Trade-off: False positives in dynamic nets.

73. **Q: Quantum threat to IPsec in routed tunnels—scenario: ESP breaks, routes leak. Migrate?**  
    **A:** Analysis: Grover halves AES key space. Solution: Adopt Kyber for key exchange in IKEv2. Rationale: Hybrid classical-PQC. Trade-off: Larger headers.

74. **Q: Multi-cluster K8s with Calico BGP: Tenant A poisons Tenant B's routes. Segment.**  
    **A:** Analysis: Shared BGP daemons leak via global table. Solution: Per-namespace VRFs with policy-based routing. Rationale: Aligns with CNCF zero-trust. Trade-off: Increases etcd state.

75. **Q: eBPF XDP for DDoS route diversion: Drop rate exceeds NIC capacity. Optimize.**  
    **A:** Analysis: Early drop at L2 floods CPU. Solution: RSS hashing + eBPF batching. Rationale: Distributes load O(cores). Trade-off: Complex prog verification.

76-100: (Condensed; SDN/eBPF/cloud/innovative)  
76. Q: WireGuard (Rust) tunnel route leak. A: AllowedIPs strict.  
77. Q: AI anomaly in BGP flaps. A: Timeseries ML (Prophet).  
78. Q: RPKI in edge computing. A: Delegated validators.  
79. Q: eBPF for OSPF Hello inspect. A: Socket filters.  
80. Q: SDN southbound TLS expiry DoS. A: Auto-renew certs.  
81. Q: Cloud BGP anycast hijack. A: Geo-fencing.  
82. Q: Post-quantum BGPsec draft. A: CRYSTALS-Dilithium.  
83. Q: CNCF Istio route policy security. A: Envoy WASM.  
84. Q: Memory-safe routing in Go. A: Gorilla for BGP parser.  
85. Q: Distributed hash table for secure RP. A: Chord-inspired.  
86. Q: eBPF tail calls for route chain. A: Modular progs.  
87. Q: Zero-trust BGP peering. A: SPIFFE certs.  
88. Q: SDN flow table poisoning. A: Versioned tables.  
89. Q: Rust eBPF verifier bypass. A: Bounds-checked maps.  
90. Q: Multi-path BGP ECMP DoS. A: Weighted paths.  
91. Q: Cloud-native multicast with eBPF. A: Sockmap redirects.  
92. Q: Innovative: Blockchain for RPKI. A: Distributed ledger ROAs.  
93. Q: OSPF in serverless (Lambda). A: Ephemeral adj.  
94. Q: BGP flowspec in IPv6. A: Extension headers.  
95. Q: eBPF for IS-IS LSP validation. A: TC ingress.  
96. Q: SDN northbound API vuln. A: OAuth scopes.  
97. Q: Secure route analytics with Prometheus. A: Federated queries.  
98. Q: Algorithmic: Dijkstra with poisoned edges. A: Weighted shortest-path trust scores.  
99. Q: CNCF Linkerd route mesh security. A: mTLS proxies.  
100. **Q: Future: AI-orchestrated routing attacks—defend a datacenter fabric.**  
     **A:** Analysis: ML generates optimal poison paths. Solution: Adversarial training on eBPF traces; ensemble detectors. Rationale: Outpaces static rules with dynamic adaptation. Trade-off: Model drift in evolving threats.

This set covers breadth and depth—practice verbalizing answers with diagrams (e.g., AS_PATH traces). For more, simulate with FRR in Docker. Good luck!