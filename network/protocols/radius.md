# RADIUS — Remote Authentication Dial-In User Service
## A Complete, In-Depth Reference Guide

---

> **Mental Model Preface:**  
> Think of RADIUS as the **gatekeeper of a castle**. Every person (user) who wants to enter the castle (network) must present credentials to the guard at the gate (NAS). The guard doesn't make the decision himself — he calls the castle's security department (RADIUS Server) to verify identity, check permissions, and record the visit. This separation of concerns — authentication, authorization, and accounting — is the soul of RADIUS.

---

## Table of Contents

1. [What is RADIUS?](#1-what-is-radius)
2. [History and RFC Standards](#2-history-and-rfc-standards)
3. [The AAA Framework — Core Philosophy](#3-the-aaa-framework)
4. [RADIUS Architecture — Who Are the Players?](#4-radius-architecture)
5. [How RADIUS Works — The Complete Flow](#5-how-radius-works)
6. [RADIUS Packet Structure — Deep Dive](#6-radius-packet-structure)
7. [RADIUS Attributes — The Language of RADIUS](#7-radius-attributes)
8. [Authentication Methods — PAP, CHAP, MS-CHAP, EAP](#8-authentication-methods)
9. [Authorization — What Can You Do?](#9-authorization)
10. [Accounting — The Audit Trail](#10-accounting)
11. [RADIUS Proxy and Realms — Federation](#11-radius-proxy-and-realms)
12. [Network Access Server (NAS)](#12-network-access-server)
13. [RADIUS Shared Secret — Security Foundation](#13-radius-shared-secret)
14. [RADIUS vs DIAMETER — Evolution](#14-radius-vs-diameter)
15. [RADIUS Over TLS (RadSec)](#15-radsec)
16. [EAP — Extensible Authentication Protocol (Deep Dive)](#16-eap-deep-dive)
17. [FreeRADIUS — Real-World Implementation](#17-freeradius)
18. [Packet Capture and Protocol Analysis](#18-packet-capture-and-analysis)
19. [Security Threats and Mitigations](#19-security-threats-and-mitigations)
20. [Common Use Cases](#20-common-use-cases)
21. [Troubleshooting RADIUS](#21-troubleshooting-radius)
22. [Mental Models and Thinking Frameworks](#22-mental-models)

---

## 1. What is RADIUS?

**RADIUS** stands for **Remote Authentication Dial-In User Service**.

It is a **client-server networking protocol** that provides:
- **Centralized Authentication** — Who are you?
- **Authorization** — What are you allowed to do?
- **Accounting** — What did you do, for how long?

RADIUS operates at the **Application Layer (Layer 7)** of the OSI model, uses **UDP** as its transport protocol (port **1812** for Auth, **1813** for Accounting — older systems used 1645/1646), and follows a **request-response** model.

### Why RADIUS Exists

Before RADIUS, every network device (a modem bank, a VPN concentrator, a switch) managed its own user database. Imagine 500 modems each with their own user list. Updating a password meant updating it 500 times. RADIUS solved this by **centralizing** identity decisions.

```
WITHOUT RADIUS (Distributed Hell):
+---------+    +---------+    +---------+
| Modem 1 |    | Modem 2 |    | Modem 3 |
| user DB |    | user DB |    | user DB |
+---------+    +---------+    +---------+
  (each manages its own users — nightmare)

WITH RADIUS (Centralized Control):
+---------+    +---------+    +---------+
| Modem 1 |    | Modem 2 |    | Modem 3 |
+----+----+    +----+----+    +----+----+
     |              |              |
     +--------------+--------------+
                    |
            +-------+-------+
            | RADIUS Server |
            | (single truth)|
            +---------------+
```

---

## 2. History and RFC Standards

Understanding the history of RADIUS gives you a **mental anchor** — you understand WHY design decisions were made the way they were.

### Timeline

```
1991 — Merit Network creates RADIUS for managing dial-up modem pools
        (The internet was made of phone lines — modems dialing ISPs)

1997 — RFC 2058 / RFC 2059: First official RADIUS standards published
        RFC 2058 = Authentication & Authorization
        RFC 2059 = Accounting

2000 — RFC 2865: RADIUS (obsoletes 2058) — THE definitive Auth RFC
        RFC 2866: RADIUS Accounting (obsoletes 2059)

2003 — RFC 3579: RADIUS Support for EAP
        RFC 3580: 802.1X RADIUS Guidelines

2012 — RFC 6614: RADIUS over TLS (RadSec)
        RFC 6733: DIAMETER (successor protocol)

2020+ — RFC 9250: RADIUS over QUIC (proposed)
         Ongoing work on RADIUS modernization
```

### Key RFCs You Must Know

| RFC    | Title                                           | Importance |
|--------|-------------------------------------------------|------------|
| 2865   | Remote Authentication Dial In User Service      | THE core spec |
| 2866   | RADIUS Accounting                               | Accounting spec |
| 2867   | RADIUS Accounting Modifications for Tunnels     | Tunnel accounting |
| 2868   | RADIUS Attributes for Tunnel Protocol Support   | Tunnel attributes |
| 2869   | RADIUS Extensions                               | Extra attributes |
| 3579   | RADIUS Support for EAP                          | EAP over RADIUS |
| 3580   | 802.1X RADIUS Usage Guidelines                  | Wi-Fi / LAN auth |
| 5176   | Dynamic Authorization Extensions to RADIUS      | CoA / Disconnect |
| 6614   | RADIUS over TLS (RadSec)                        | Secure transport |

---

## 3. The AAA Framework

**AAA** is the conceptual backbone of RADIUS. Every aspect of RADIUS maps to one of these three functions.

```
+-------------------------------------------------------------+
|                    AAA FRAMEWORK                            |
+-------------------------------------------------------------+
|                                                             |
|   AUTHENTICATION           AUTHORIZATION     ACCOUNTING     |
|   "Who are you?"           "What can you do?" "What did you"|
|                                               do?"          |
|   +-------------+          +-------------+   +----------+  |
|   | Verify      |          | Grant or    |   | Log      |  |
|   | identity    |          | Deny access |   | session  |  |
|   | credentials |          | + enforce   |   | data     |  |
|   +-------------+          | policies    |   +----------+  |
|                            +-------------+                  |
|                                                             |
|   Examples:                Examples:         Examples:      |
|   - Password check         - VLAN assign     - Start time   |
|   - Certificate verify     - Bandwidth limit - Stop time    |
|   - OTP validation         - IP address      - Data usage   |
|                            - Time-of-day ACL - Location     |
+-------------------------------------------------------------+
```

### Authentication in Detail

Authentication is the process of **verifying identity**. RADIUS supports multiple authentication methods (PAP, CHAP, EAP — covered in depth later). The fundamental question is: "Are you really who you say you are?"

### Authorization in Detail

Authorization answers: "Given that you ARE who you say you are, what are you ALLOWED to do?" This happens after authentication. RADIUS can return attributes that tell the NAS:
- Assign this user to VLAN 100
- Give this user 10 Mbps bandwidth
- Set the session timeout to 3600 seconds
- Apply this access control list

### Accounting in Detail

Accounting is the **audit trail**. It records:
- When did the session start?
- When did it stop?
- How many bytes were transferred?
- Which NAS served the connection?
- What IP was assigned?

This data is used for billing, compliance, security auditing, and capacity planning.

---

## 4. RADIUS Architecture

### The Players (Components)

#### 1. User / Supplicant
The entity trying to gain access. Could be a human with a laptop, a phone, an IoT device, or even a machine. The user has **credentials** (username/password, certificate, token).

#### 2. Network Access Server (NAS) / RADIUS Client
This is the **edge device** — the entity the user physically or logically connects to first. It is called a "RADIUS Client" because it sends RADIUS requests to the RADIUS Server.

Examples of NAS devices:
- Wi-Fi Access Points (802.1X authentication)
- VPN concentrators (Cisco ASA, Palo Alto)
- DSL/Cable modems
- Network switches (802.1X port authentication)
- Dial-up modem banks (historical)
- 4G/5G GGSN/PGW (mobile networks)

The NAS does NOT make the access decision — it **delegates** to the RADIUS server.

#### 3. RADIUS Server
The **decision-making authority**. It:
- Receives Access-Request from NAS
- Consults its user database (local files, LDAP, Active Directory, SQL)
- Returns Access-Accept, Access-Reject, or Access-Challenge

#### 4. User Database / Backend
Where actual user data lives. RADIUS servers typically connect to:
- Flat files (users file in FreeRADIUS)
- LDAP / Active Directory
- SQL databases (MySQL, PostgreSQL)
- NoSQL stores
- External APIs

```
COMPLETE RADIUS ARCHITECTURE
=============================

+------------------+
|   USER           |
|  (Supplicant)    |
|  laptop/phone    |
+--------+---------+
         |
         | (1) User connects and provides credentials
         | Could be: Ethernet port, Wi-Fi, VPN tunnel, DSL line
         |
+--------+---------+          +------------------+
|   NAS            |          |                  |
|  (RADIUS Client) |          |  RADIUS SERVER   |
|                  |  (2)     |                  |
|  Wi-Fi AP        +--------->|  FreeRADIUS      |
|  VPN Gateway     | Access-  |  Cisco ISE       |
|  Switch Port     | Request  |  Microsoft NPS   |
|  DSL Modem       |          |  Aruba ClearPass |
|                  |  (3)     |                  |
|                  |<---------+  Checks:         |
|                  | Access-  |  - local users   |
|                  | Accept / |  - LDAP/AD       |
|                  | Reject / |  - SQL DB        |
|                  | Challenge|  - External API  |
|                  |          |                  |
+------------------+          +--------+---------+
         |                             |
         | (4) User gets access        | (5) Queries backend
         | (or is rejected)            |
         |                    +--------+---------+
                              |  Backend DB      |
                              |                  |
                              |  Active Directory|
                              |  LDAP Server     |
                              |  MySQL Database  |
                              |  /etc/passwd     |
                              +------------------+
```

### RADIUS Proxy Architecture

When organizations federate or when you have multiple RADIUS servers, a **RADIUS Proxy** sits between NAS and the authoritative RADIUS server. It forwards requests based on **realm** (more in Section 11).

```
RADIUS PROXY ARCHITECTURE
==========================

    NAS          RADIUS Proxy        Home RADIUS Server
+--------+      +-----------+       +----------------+
|        |----->|           |------>|                |
|Wi-Fi AP|      |  Proxy    |       | University     |
|        |<-----|  Server   |<------|  RADIUS Server |
+--------+      |           |       +----------------+
                |           |
                |           |       +----------------+
                |           |------>|                |
                |           |       | Corporate      |
                |           |<------|  RADIUS Server |
                +-----------+       +----------------+
                (routes based on
                 username realm)
```

---

## 5. How RADIUS Works — The Complete Flow

Let me walk through **every step** with exhaustive detail.

### Scenario: User Connects to Wi-Fi with WPA2-Enterprise (802.1X)

```
STEP-BY-STEP RADIUS AUTHENTICATION FLOW
=========================================

USER                NAS (Wi-Fi AP)           RADIUS SERVER        Backend DB
 |                       |                        |                    |
 |  (1) Associate        |                        |                    |
 |  with AP (Wi-Fi probe)|                        |                    |
 |---------------------->|                        |                    |
 |                       |                        |                    |
 |  (2) EAP-Start        |                        |                    |
 |<----------------------|                        |                    |
 |                       |                        |                    |
 |  (3) EAP-Response/    |                        |                    |
 |  Identity             |                        |                    |
 |  (username sent)      |                        |                    |
 |---------------------->|                        |                    |
 |                       |                        |                    |
 |                       |  (4) Access-Request    |                    |
 |                       |  [User-Name,           |                    |
 |                       |   NAS-IP-Address,      |                    |
 |                       |   EAP-Message,         |                    |
 |                       |   Message-Authenticator|                    |
 |                       |  UDP/1812]             |                    |
 |                       |----------------------->|                    |
 |                       |                        |                    |
 |                       |                        |  (5) Lookup user   |
 |                       |                        |  in backend        |
 |                       |                        |------------------->|
 |                       |                        |                    |
 |                       |                        |  (6) User found,   |
 |                       |                        |  send password hash|
 |                       |                        |<-------------------|
 |                       |                        |                    |
 |                       |  (7) Access-Challenge  |                    |
 |                       |  [EAP-Message (nonce)] |                    |
 |                       |<-----------------------|                    |
 |                       |                        |                    |
 |  (8) EAP-Request      |                        |                    |
 |  (challenge sent)     |                        |                    |
 |<----------------------|                        |                    |
 |                       |                        |                    |
 |  (9) EAP-Response     |                        |                    |
 |  (compute response    |                        |                    |
 |   with password)      |                        |                    |
 |---------------------->|                        |                    |
 |                       |                        |                    |
 |                       |  (10) Access-Request   |                    |
 |                       |  [EAP-Message (resp)]  |                    |
 |                       |----------------------->|                    |
 |                       |                        |                    |
 |                       |                        |  (11) Verify       |
 |                       |                        |  response against  |
 |                       |                        |  stored credential |
 |                       |                        |                    |
 |                       |  (12) Access-Accept    |                    |
 |                       |  [Session-Timeout,     |                    |
 |                       |   Tunnel-Type (VLAN),  |                    |
 |                       |   Framed-IP-Address,   |                    |
 |                       |   Class attributes]    |                    |
 |                       |<-----------------------|                    |
 |                       |                        |                    |
 |  (13) EAP-Success     |                        |                    |
 |<----------------------|                        |                    |
 |                       |                        |                    |
 |  (14) Network Access  |                        |                    |
 |  GRANTED              |                        |                    |
 |                       |                        |                    |
 |                       |  (15) Accounting-Start |                    |
 |                       |  [Acct-Session-Id,     |                    |
 |                       |   Acct-Status-Type=    |                    |
 |                       |   Start,               |                    |
 |                       |   Framed-IP-Address]   |                    |
 |                       |----------------------->|                    |
 |                       |                        |                    |
 |                       |  (16) Accounting-      |                    |
 |                       |  Response              |                    |
 |                       |<-----------------------|                    |
 |                       |                        |                    |
 |  [... session active ...]                      |                    |
 |                       |                        |                    |
 |  (17) User            |                        |                    |
 |  Disconnects          |                        |                    |
 |---------------------->|                        |                    |
 |                       |                        |                    |
 |                       |  (18) Accounting-Stop  |                    |
 |                       |  [Acct-Input-Octets,   |                    |
 |                       |   Acct-Output-Octets,  |                    |
 |                       |   Acct-Session-Time]   |                    |
 |                       |----------------------->|                    |
 |                       |                        |                    |
```

### The Four RADIUS Packet Types

```
ACCESS-REQUEST
  NAS --> RADIUS Server
  "Can this user get in?"
  
ACCESS-ACCEPT
  RADIUS Server --> NAS
  "Yes, and here are their permissions."
  
ACCESS-REJECT
  RADIUS Server --> NAS
  "No, deny this user."
  
ACCESS-CHALLENGE
  RADIUS Server --> NAS
  "I need more information. Ask the user for X."
  (Used in multi-step authentication: OTP, EAP, etc.)

ACCOUNTING-REQUEST
  NAS --> RADIUS Server
  "Log this event (session start/stop/update)."

ACCOUNTING-RESPONSE
  RADIUS Server --> NAS
  "Got it, logged."

COA-REQUEST (Change of Authorization) — RFC 5176
  RADIUS Server --> NAS (direction reversed!)
  "Change something about an active session."

DISCONNECT-REQUEST — RFC 5176
  RADIUS Server --> NAS
  "Kick this user off immediately."
```

---

## 6. RADIUS Packet Structure — Deep Dive

Every RADIUS packet has the same fundamental structure. Understanding it deeply is critical for debugging and implementation.

### Packet Header Structure

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Code      |  Identifier   |            Length             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                         Authenticator                         |
|                                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Attributes ...
+-+-+-+-+-+-+-+-+-+-
```

### Field-by-Field Explanation

#### Code (1 byte)
Identifies the **type of packet**. This single byte tells you everything about what this packet is trying to do.

```
Code Values:
+---------+----------------------------------------------+
|  Code   | Packet Type                                  |
+---------+----------------------------------------------+
|    1    | Access-Request                               |
|    2    | Access-Accept                                |
|    3    | Access-Reject                                |
|    4    | Accounting-Request                           |
|    5    | Accounting-Response                          |
|   11    | Access-Challenge                             |
|   12    | Status-Server (experimental)                 |
|   13    | Status-Client (experimental)                 |
|   40    | Disconnect-Request (RFC 5176)                |
|   41    | Disconnect-ACK (RFC 5176)                    |
|   42    | Disconnect-NAK (RFC 5176)                    |
|   43    | CoA-Request (RFC 5176)                       |
|   44    | CoA-ACK (RFC 5176)                           |
|   45    | CoA-NAK (RFC 5176)                           |
|  255    | Reserved                                     |
+---------+----------------------------------------------+
```

#### Identifier (1 byte)
A **matching token**. When the NAS sends an Access-Request with Identifier=42, the response from the RADIUS server will also have Identifier=42. This allows matching requests to responses when multiple are in flight simultaneously.

Think of it like a **ticket number** at a deli counter — you hold ticket #42 and wait for #42 to be called.

#### Length (2 bytes)
Total length of the entire RADIUS packet in bytes, including the Code, Identifier, Length, Authenticator, and all Attributes. Minimum value: 20 (header only). Maximum value: 4096.

#### Authenticator (16 bytes)
This is the **most subtle and critical field**. It has different meanings depending on the packet direction:

**In Access-Request (sent by NAS):**
The authenticator is a **Random 16-byte value** (Request Authenticator). This randomness is crucial — it prevents replay attacks. Every new request must have a different Request Authenticator.

```
Request Authenticator = Random 128-bit value
                        (generated by NAS for each new request)
```

**In Access-Accept, Access-Reject, Access-Challenge (sent by RADIUS Server):**
The authenticator is a **Response Authenticator**, computed as:

```
Response Authenticator = MD5(Code + Identifier + Length +
                              Request Authenticator +
                              Attributes +
                              Shared Secret)
```

This computation **proves** the response came from a server that knows the shared secret. The NAS verifies this before trusting the response.

**In Accounting-Request:**
The authenticator is computed as:

```
Acct Authenticator = MD5(Code + Identifier + Length +
                          16 zero bytes +           <-- zeroes, not random!
                          Attributes +
                          Shared Secret)
```

### Attribute Structure (Variable Length)

After the 20-byte header, RADIUS packets contain zero or more **attributes** in TLV format (Type-Length-Value):

```
 0                   1                   2
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Type      |    Length     |   Value ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **Type**: 1 byte — identifies which attribute this is (1=User-Name, 2=User-Password, etc.)
- **Length**: 1 byte — total bytes for this attribute including Type and Length fields. Minimum: 2. Maximum: 255.
- **Value**: Variable (Length - 2) bytes — the actual data.

**Important:** The maximum size of a single attribute value is 253 bytes (255 - 2 bytes for Type and Length). For larger data (like EAP messages), multiple attributes of the same type are concatenated in order.

---

## 7. RADIUS Attributes — The Language of RADIUS

**Attributes are the vocabulary of RADIUS.** Every piece of information exchanged between NAS and RADIUS server is encoded as an attribute. Mastering attributes means mastering RADIUS.

### Attribute Data Types

Before listing attributes, understand the fundamental data types:

```
+-----------------+---------------------------------------------+
| Data Type       | Description                                 |
+-----------------+---------------------------------------------+
| string          | 1-253 bytes of arbitrary data               |
| text            | 1-253 bytes of UTF-8 text                  |
| address         | 4 bytes, IPv4 address (network byte order)  |
| integer         | 4 bytes, unsigned 32-bit integer            |
| time            | 4 bytes, seconds since Jan 1, 1970 UTC      |
| ifid            | 8 bytes, interface identifier               |
| ipv6addr        | 16 bytes, IPv6 address                      |
| ipv6prefix      | Variable, IPv6 prefix                       |
+-----------------+---------------------------------------------+
```

### Core Attributes (RFC 2865)

```
+------+---------------------------+-----------+---------------------+
| Type | Attribute Name            | Data Type | Description         |
+------+---------------------------+-----------+---------------------+
|  1   | User-Name                 | text      | Username/login      |
|  2   | User-Password             | string    | Encrypted password  |
|  3   | CHAP-Password             | string    | CHAP response       |
|  4   | NAS-IP-Address            | address   | NAS IPv4 address    |
|  5   | NAS-Port                  | integer   | Physical port number|
|  6   | Service-Type              | integer   | Requested service   |
|  7   | Framed-Protocol           | integer   | PPP, SLIP, etc.     |
|  8   | Framed-IP-Address         | address   | IP to assign user   |
|  9   | Framed-IP-Netmask         | address   | Netmask for user    |
| 10   | Framed-Routing            | integer   | Routing method      |
| 11   | Filter-Id                 | text      | ACL/filter name     |
| 12   | Framed-MTU                | integer   | MTU for user        |
| 13   | Framed-Compression        | integer   | Compression type    |
| 14   | Login-IP-Host             | address   | Host to login to    |
| 15   | Login-Service             | integer   | Telnet, SSH, etc.   |
| 16   | Login-TCP-Port            | integer   | Port for login      |
| 18   | Reply-Message             | text      | Human-readable msg  |
| 19   | Callback-Number           | text      | Callback number     |
| 20   | Callback-Id               | text      | Callback identifier |
| 22   | Framed-Route              | text      | Static route        |
| 23   | Framed-IPX-Network        | integer   | IPX network number  |
| 24   | State                     | string    | Challenge state     |
| 25   | Class                     | string    | Session class tag   |
| 26   | Vendor-Specific           | string    | VSA container       |
| 27   | Session-Timeout           | integer   | Max session seconds |
| 28   | Idle-Timeout              | integer   | Max idle seconds    |
| 29   | Termination-Action        | integer   | On timeout action   |
| 30   | Called-Station-Id         | text      | Called number/BSSID |
| 31   | Calling-Station-Id        | text      | Calling number/MAC  |
| 32   | NAS-Identifier            | text      | NAS name string     |
| 33   | Proxy-State               | string    | Proxy chain state   |
| 34   | Login-LAT-Service         | text      | LAT service name    |
| 35   | Login-LAT-Node            | text      | LAT node name       |
| 36   | Login-LAT-Group           | string    | LAT group codes     |
| 37   | Framed-AppleTalk-Link     | integer   | AppleTalk link num  |
| 38   | Framed-AppleTalk-Network  | integer   | AppleTalk network   |
| 39   | Framed-AppleTalk-Zone     | text      | AppleTalk zone      |
| 40   | Acct-Status-Type          | integer   | Start/Stop/Interim  |
| 41   | Acct-Delay-Time           | integer   | Seconds to deliver  |
| 42   | Acct-Input-Octets         | integer   | Bytes from user     |
| 43   | Acct-Output-Octets        | integer   | Bytes to user       |
| 44   | Acct-Session-Id           | text      | Unique session ID   |
| 45   | Acct-Authentic            | integer   | RADIUS/Local/Remote |
| 46   | Acct-Session-Time         | integer   | Session duration    |
| 47   | Acct-Input-Packets        | integer   | Packets from user   |
| 48   | Acct-Output-Packets       | integer   | Packets to user     |
| 49   | Acct-Terminate-Cause      | integer   | Why session ended   |
| 50   | Acct-Multi-Session-Id     | text      | Multi-link session  |
| 51   | Acct-Link-Count           | integer   | Links in multi-link |
| 55   | Event-Timestamp           | time      | When event occurred |
| 60   | CHAP-Challenge            | string    | CHAP challenge value|
| 61   | NAS-Port-Type             | integer   | Port type           |
| 62   | Port-Limit                | integer   | Max concurrent ports|
| 63   | Login-LAT-Port            | text      | LAT port identifier |
| 77   | Connect-Info              | text      | Connection speed    |
| 79   | EAP-Message               | string    | EAP packet data     |
| 80   | Message-Authenticator     | string    | HMAC-MD5 integrity  |
| 87   | NAS-Port-Id               | text      | Port identifier text|
| 95   | NAS-IPv6-Address          | ipv6addr  | NAS IPv6 address    |
+------+---------------------------+-----------+---------------------+
```

### Vendor-Specific Attributes (VSA) — Attribute 26

This is a **crucial concept**. Attribute 26 is a container that allows any vendor to define their own custom attributes. This is how RADIUS is extensible.

VSA structure:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Type=26   |  Length       |            Vendor-Id          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Vendor-Id (cont)             |  Vendor-Type  |  Vendor-Length|
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Attribute-Specific Data ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
```

**Vendor-Id** is the IANA-assigned Private Enterprise Number (PEN).

```
Common Vendor IDs:
+--------+----------------------------------+
| PEN    | Vendor                           |
+--------+----------------------------------+
|    9   | Cisco Systems                    |
|   25   | HP                               |
|   43   | 3Com                             |
|  311   | Microsoft                        |
|  2352  | Juniper Networks                 |
|  3076  | Cisco Aironet (Wi-Fi)            |
|  9694  | Aruba Networks                   |
| 12356  | Fortinet                          |
| 14823  | Aruba (legacy)                   |
| 25506  | H3C / Huawei                     |
+--------+----------------------------------+
```

**Example VSAs:**

Cisco VSA for privilege level:
```
Type=26, Length=10, Vendor-Id=9 (Cisco), Vendor-Type=1 (cisco-avpair)
Value: "shell:priv-lvl=15"
(Gives user enable-level access on Cisco device)
```

Microsoft VSAs for MPPE (MS-CHAPv2 encryption):
```
Type=26, Vendor-Id=311 (Microsoft)
  MS-MPPE-Recv-Key (Vendor-Type=17)
  MS-MPPE-Send-Key (Vendor-Type=16)
(Encryption keys for PPTP/SSTP VPN)
```

### The User-Password Encryption (Attribute 2)

This is the **most important security mechanism** in basic RADIUS. The password is never sent in plaintext.

```
User-Password Encryption Algorithm:
=====================================

Given:
  P = Password (padded with nulls to multiple of 16 bytes)
  S = Shared Secret
  R = Request Authenticator (16 random bytes from the request)

Step 1: Compute b1 = MD5(S + R)  [concatenate S and R, then MD5]
Step 2: c1 = P[0..15] XOR b1      [XOR first 16 bytes of password with b1]
Step 3: Compute b2 = MD5(S + c1)  [for subsequent blocks]
Step 4: c2 = P[16..31] XOR b2     [XOR next 16 bytes]
... continue for all blocks ...

Result: [c1][c2][c3]...  = Encrypted password in the packet
```

**Decryption** (at RADIUS server) is the reverse:
```
Step 1: Compute b1 = MD5(S + R)   [server knows S and R from packet]
Step 2: P[0..15] = c1 XOR b1     [recovers original plaintext bytes]
Step 3: Compute b2 = MD5(S + c1)
Step 4: P[16..31] = c2 XOR b2
...
```

The **shared secret** and **Request Authenticator** together protect the password. If an attacker captures the packet, they cannot decrypt the password without knowing the shared secret. However, if the shared secret is weak (e.g., "radius"), offline dictionary attacks are possible — this is why strong shared secrets matter.

---

## 8. Authentication Methods — PAP, CHAP, MS-CHAP, EAP

### 8.1 PAP — Password Authentication Protocol

**What is PAP?**  
PAP is the **simplest** authentication method. The client sends the username and password in (effectively) plaintext. It has almost no built-in security mechanisms.

```
PAP FLOW
=========

User                  NAS                 RADIUS Server
 |                     |                       |
 | username + password |                       |
 |-------------------->|                       |
 |                     | Access-Request        |
 |                     | [User-Name=alice,     |
 |                     |  User-Password=       |
 |                     |  <encrypted>]         |
 |                     |---------------------->|
 |                     |                       | Decrypt password
 |                     |                       | Compare to stored
 |                     |                       | hash/password
 |                     | Access-Accept/Reject  |
 |                     |<----------------------|
 |  Grant/Deny         |                       |
 |<--------------------|                       |
```

**How User-Password Works in PAP:**
The NAS takes the plaintext password, encrypts it with the User-Password algorithm (XOR with MD5 of shared secret + request authenticator), and puts it in attribute 2.

**PAP Security Analysis:**
- Password is encrypted in transit (from NAS to RADIUS server) — but only with a weak MD5-based scheme
- Password is exposed in plaintext between USER and NAS if the access link is unencrypted
- Vulnerable to: offline dictionary attacks (if shared secret is known), replay attacks (without proper implementation)
- Modern usage: Only acceptable when the user-to-NAS link is already encrypted (e.g., PAP inside an HTTPS tunnel, or PAP over a VPN)

```
SECURITY RATING: ★★☆☆☆ (Low — avoid unless wrapped in TLS)
```

### 8.2 CHAP — Challenge Handshake Authentication Protocol

**What is CHAP?**  
CHAP is a **challenge-response** authentication method. The password is **never sent** — instead, proof of knowing the password is sent.

```
CHAP FLOW
==========

User                  NAS                 RADIUS Server
 |                     |                       |
 | connect             |                       |
 |-------------------->|                       |
 |                     |                       |
 |  CHAP Challenge     |                       |
 |  [ID, random 16B]   |                       |
 |<--------------------|                       |
 |                     |                       |
 |  CHAP Response      |                       |
 |  [ID, MD5(ID +      |                       |
 |   Password +        |                       |
 |   Challenge)]       |                       |
 |-------------------->|                       |
 |                     | Access-Request        |
 |                     | [User-Name=alice,     |
 |                     |  CHAP-Password=       |
 |                     |  <16-byte response>,  |
 |                     |  CHAP-Challenge=      |
 |                     |  <original challenge>]|
 |                     |---------------------->|
 |                     |                       | Server computes:
 |                     |                       | expected=MD5(ID+
 |                     |                       |   stored_pwd+
 |                     |                       |   challenge)
 |                     |                       | Compare to received
 |                     | Access-Accept/Reject  |
 |                     |<----------------------|
```

**CHAP-Password Attribute (Type 3):**
```
+--------+----------+--------+
|  ID    | CHAP-    |
| 1 byte | Response |
|        | 16 bytes |
+--------+----------+
CHAP-Password = ID || MD5(ID || Password || Challenge)
```

**CHAP Security Analysis:**
- Password never sent — better than PAP
- RADIUS server needs access to the **plaintext** password (to compute the expected MD5) — cannot use hashed passwords in backend
- Protects against passive eavesdropping
- Vulnerable to: dictionary attacks (attacker captures challenge+response and brute-forces the password offline), does NOT provide mutual authentication

```
SECURITY RATING: ★★★☆☆ (Medium)
```

### 8.3 MS-CHAP and MS-CHAPv2 — Microsoft's Extension

MS-CHAPv2 is widely used for VPN (PPTP, SSTP) and Wi-Fi. It improves on CHAP by:
1. **Mutual authentication** — the server also proves it knows the password
2. **NT hash** — uses NT hash of password, not plaintext
3. **Per-session encryption keys** — enables MPPE for data encryption

```
MS-CHAPv2 FLOW
===============

User                NAS              RADIUS Server
 |                   |                    |
 | connect           |                    |
 |------------------>|                    |
 |                   |                    |
 | Authenticator-    |                    |
 | Challenge (16B)   |                    |
 |<------------------|                    |
 |                   |                    |
 | Peer-Challenge    |                    |
 | (16B random)      |                    |
 | NT-Response       |                    |
 | (computed with    |                    |
 | NTHash(password)) |                    |
 |------------------>|                    |
 |                   | Access-Request     |
 |                   | [MS-CHAP2-Response]|
 |                   |------------------->|
 |                   |                    |
 |                   |                    | Verify NT-Response
 |                   |                    | Compute Auth-Response
 |                   | Access-Accept      |
 |                   | [MS-CHAP2-Success, |
 |                   |  MS-MPPE-Keys]     |
 |                   |<-------------------|
 |                   |                    |
 | Auth-Response     |                    |
 | (mutual auth)     |                    |
 |<------------------|                    |
```

**NT Hash:**
```
NTHash(password) = MD4(UTF-16LE(password))
```

**MS-CHAPv2 NT-Response Computation:**
```
1. AuthenticatorChallenge = random 16 bytes from server
2. PeerChallenge = random 16 bytes from client
3. Challenge = SHA1(PeerChallenge || AuthenticatorChallenge || username)[0:8]
   (first 8 bytes of SHA1 hash)
4. NT-Response = ChallengeResponse(Challenge, NTHash(password))
   (DES-based function: 3 DES operations)
```

```
SECURITY RATING: ★★★★☆ (Good, but NT hash is weak — use EAP-PEAP/MS-CHAPv2 instead)
```

### 8.4 EAP — Overview

**EAP (Extensible Authentication Protocol)** is not itself an authentication method — it is a **framework** for authentication. EAP defines a way to negotiate and carry authentication protocols. The actual authentication happens inside an EAP method.

Think of EAP as an **envelope** that can contain different letters (authentication methods).

```
EAP ENCAPSULATION HIERARCHY
=============================

+------------------------------------------------------+
|  RADIUS Packet                                        |
|  +--------------------------------------------------+|
|  | Attribute: EAP-Message (Type 79)                 ||
|  |  +----------------------------------------------+||
|  |  | EAP Packet                                   |||
|  |  |  +------------------------------------------+|||
|  |  |  | EAP Method (PEAP, TTLS, TLS, etc.)       ||||
|  |  |  |  +--------------------------------------+ ||||
|  |  |  |  | Inner Authentication                 | ||||
|  |  |  |  | (MSCHAPv2, PAP, GTC, TLS cert, etc.) | ||||
|  |  |  |  +--------------------------------------+ ||||
|  |  |  +------------------------------------------+|||
|  |  +----------------------------------------------+||
|  +--------------------------------------------------+|
+------------------------------------------------------+
```

EAP packets are carried as RADIUS attributes (EAP-Message, Type 79). If an EAP message is larger than 253 bytes, it's split across multiple EAP-Message attributes in sequence.

Common EAP Methods:

```
+------------------+-------+-----------------------------------------------+
| EAP Method       | RFC   | Description                                   |
+------------------+-------+-----------------------------------------------+
| EAP-MD5          | 3748  | Simple MD5 challenge-response. Insecure.      |
| EAP-TLS          | 5216  | Mutual TLS with client cert. Most secure.     |
| EAP-TTLS         | 5281  | TLS tunnel, inner auth (any method)           |
| PEAP             | IETF  | Protected EAP. TLS tunnel, inner EAP          |
| EAP-FAST         | 4851  | Cisco. PAC-based tunnel                       |
| EAP-SIM          | 4186  | GSM SIM card authentication                   |
| EAP-AKA          | 4187  | UMTS/LTE SIM authentication                   |
| EAP-PWD          | 5931  | Password-based, no PKI needed                 |
| EAP-GPSK         | 5433  | Pre-shared key, no PKI                        |
+------------------+-------+-----------------------------------------------+
```

Full EAP deep dive in Section 16.

---

## 9. Authorization

Authorization in RADIUS is **implicit** — it's not a separate packet type. The authorization decision is embedded in the **Access-Accept** packet as attributes.

When the RADIUS server sends Access-Accept, it includes **return attributes** that tell the NAS how to configure the user's session.

### Common Authorization Attributes

```
VLAN Assignment (802.1X Port-Based):
+---------------------------------------+
| Tunnel-Type (64)        = VLAN (13)  |
| Tunnel-Medium-Type (65) = 802 (6)    |
| Tunnel-Private-Group-ID (81) = "100" |
+---------------------------------------+
(Assigns user to VLAN 100)

Bandwidth Limiting (Cisco VSA):
+---------------------------------------+
| Vendor-Specific (26)                  |
|   Vendor-Id: 9 (Cisco)               |
|   cisco-avpair: "sub-qos-policy-in=  |
|                  LIMIT_10MBPS"        |
+---------------------------------------+

Session Timeout:
+---------------------------------------+
| Session-Timeout (27) = 86400          |
| (Session ends after 24 hours)         |
+---------------------------------------+

ACL Assignment (Cisco):
+---------------------------------------+
| Filter-Id (11) = "ACL-GUEST-INTERNET" |
| (Apply this ACL to user's interface)  |
+---------------------------------------+

IP Address Assignment:
+---------------------------------------+
| Framed-IP-Address (8)  = 10.0.1.50   |
| Framed-IP-Netmask (9)  = 255.255.255.0|
+---------------------------------------+

Static Route Injection:
+---------------------------------------+
| Framed-Route (22) = "192.168.10.0/24 |
|                      via 10.0.1.1"   |
+---------------------------------------+
```

### Service-Type Attribute (Type 6)

This attribute tells the NAS what kind of service to provide:

```
Service-Type Values:
+-------+-----------------------------------------------+
| Value | Service                                       |
+-------+-----------------------------------------------+
|   1   | Login (connect to a host)                     |
|   2   | Framed (PPP, SLIP — IP connectivity)          |
|   3   | Callback Login                                |
|   4   | Callback Framed                               |
|   5   | Outbound (service for outbound connects)      |
|   6   | Administrative (full administrative access)   |
|   7   | NAS Prompt (shell/console access)             |
|   8   | Authenticate Only (no service, just verify)   |
|   9   | Callback NAS Prompt                           |
|  10   | Call Check (for callback)                     |
|  11   | Callback Administrative                       |
+-------+-----------------------------------------------+
```

### Policy-Based Authorization

In enterprise deployments, authorization is driven by **policies** — logical rules that say "if user is in group X AND connecting from device type Y AND during hours Z, then assign VLAN V and bandwidth B."

```
POLICY ENGINE DECISION TREE
=============================

Access-Request received
         |
         v
    Is user in AD?
    /           \
  Yes            No
   |              |
   v              v
Is user in    Reject with
"Employees"   Reply-Message=
group?        "Unknown user"
  /    \
Yes     No
 |       |
 v       v
Is     Is user in
device  "Contractors"
trusted? group?
 / \    /     \
Y   N  Yes     No
|   |   |       |
v   v   v       v
Full Guest Contractor REJECT
VLAN VLAN   VLAN
100  200    300
```

---

## 10. Accounting

Accounting is where RADIUS keeps **records of what happened**. This is essential for:
- **Billing** (ISPs charge per MB or per hour)
- **Compliance** (who accessed what, when)
- **Capacity planning** (how many concurrent users)
- **Security forensics** (who was connected when an incident occurred)

### Accounting Packet Types

**Acct-Status-Type (Attribute 40) Values:**

```
+-------+----------------------------------------------------+
| Value | Meaning                                            |
+-------+----------------------------------------------------+
|   1   | Start — session is beginning                       |
|   2   | Stop — session has ended                           |
|   3   | Interim-Update — session is ongoing, sending stats |
|   7   | Accounting-On — NAS is coming online               |
|   8   | Accounting-Off — NAS is going offline              |
+-------+----------------------------------------------------+
```

### Accounting Flow

```
ACCOUNTING LIFECYCLE
=====================

    NAS                          RADIUS Accounting Server
     |                                    |
     | Accounting-Request (Start)         |
     | [Acct-Status-Type=1,              |
     |  Acct-Session-Id="unique-id-123", |
     |  User-Name="alice",               |
     |  NAS-IP-Address=10.1.1.1,         |
     |  Framed-IP-Address=10.0.1.50,     |
     |  Called-Station-Id="AP-BUILDING1",|
     |  Calling-Station-Id="aa:bb:cc:...",|
     |  Event-Timestamp=1700000000]      |
     |----------------------------------->|
     |                                    |
     |  Accounting-Response               |
     |<-----------------------------------|
     |                                    |
     | [... session active, every 5 min...]|
     |                                    |
     | Accounting-Request (Interim)       |
     | [Acct-Status-Type=3,              |
     |  Acct-Session-Id="unique-id-123", |
     |  Acct-Input-Octets=15000000,      |
     |  Acct-Output-Octets=2000000,      |
     |  Acct-Session-Time=300]           |
     |----------------------------------->|
     |                                    |
     |  Accounting-Response               |
     |<-----------------------------------|
     |                                    |
     | [... session ends ...]             |
     |                                    |
     | Accounting-Request (Stop)          |
     | [Acct-Status-Type=2,              |
     |  Acct-Session-Id="unique-id-123", |
     |  Acct-Input-Octets=45000000,      |
     |  Acct-Output-Octets=8000000,      |
     |  Acct-Session-Time=1800,          |
     |  Acct-Terminate-Cause=1]          |  <- User Request (cause=1)
     |----------------------------------->|
     |                                    |
     |  Accounting-Response               |
     |<-----------------------------------|
```

### Acct-Terminate-Cause Values

Why did the session end? This is forensically important:

```
+-------+----------------------------------------------+
| Value | Cause                                        |
+-------+----------------------------------------------+
|   1   | User Request (user logged out)               |
|   2   | Lost Carrier (physical disconnection)        |
|   3   | Lost Service (service disappeared)           |
|   4   | Idle Timeout (no traffic for too long)       |
|   5   | Session Timeout (max time reached)           |
|   6   | Admin Reset (administrator kicked user)      |
|   7   | Admin Reboot (NAS rebooted)                  |
|   8   | Port Error                                   |
|   9   | NAS Error                                    |
|  10   | NAS Request                                  |
|  11   | NAS Reboot                                   |
|  12   | Port Unneeded                                |
|  13   | Port Preempted                               |
|  14   | Port Suspended                               |
|  15   | Service Unavailable                          |
|  16   | Callback                                     |
|  17   | User Error                                   |
|  18   | Host Request                                 |
+-------+----------------------------------------------+
```

### Acct-Input/Output-Octets Wrap-Around

A critical implementation detail: Acct-Input-Octets and Acct-Output-Octets are **32-bit unsigned integers** (max ~4.3 GB). A fast connection can overflow this in minutes. To handle this, two extension attributes exist:

- **Acct-Input-Gigawords (Type 52)**: Number of times the input octet counter has wrapped (overflowed)
- **Acct-Output-Gigawords (Type 53)**: Same for output

Actual bytes = (Gigawords × 2^32) + Octets

---

## 11. RADIUS Proxy and Realms

### What is a Realm?

A **realm** is the domain portion of a username. It identifies which "home" RADIUS server is responsible for authenticating that user.

```
Username formats with realms:
  alice@university.edu          <- @ delimiter (most common)
  university.edu\alice          <- \ delimiter (Windows-style)
  alice%university.edu          <- % delimiter (some systems)
  alice                         <- no realm (local user)
```

The realm tells the proxy server: "Forward this request to the RADIUS server responsible for university.edu."

### RADIUS Proxy Operation

```
RADIUS PROXY ROUTING
=====================

                     Proxy Server
                    +-----------+
                    | Routing   |
                    | Table:    |
                    |           |
                    | @corpA.com|---------> CorpA RADIUS
NAS ----Request---->| @univB.edu|---------> Univ B RADIUS
     (user=         |           |
      bob@corpA.com)| (default) |---------> Local RADIUS
                    +-----------+

Routing Decision:
  Parse username --> extract realm --> look up routing table --> forward
```

### Proxy Packet Flow

```
NAS          Proxy          Home RADIUS Server
 |             |                  |
 | Access-     |                  |
 | Request     |                  |
 | [ID=1,      |                  |
 |  User-Name= |                  |
 |  alice@uni] |                  |
 |------------>|                  |
 |             | Access-Request   |
 |             | [ID=99,          |  <-- Proxy generates NEW ID
 |             |  User-Name=      |
 |             |  alice@uni,      |
 |             |  Proxy-State=X]  |  <-- Proxy adds Proxy-State
 |             |----------------->|
 |             |                  | Verify alice
 |             |                  |
 |             | Access-Accept    |
 |             | [ID=99,          |
 |             |  Proxy-State=X,  |
 |             |  attrs...]       |
 |             |<-----------------|
 |             |                  |
 |             | (Proxy maps ID   |
 |             |  99 back to 1,   |
 |             |  using Proxy-State)
 |             |                  |
 | Access-     |                  |
 | Accept      |                  |
 | [ID=1,      |                  |
 |  attrs...]  |                  |
 |<------------|                  |
```

**Proxy-State (Attribute 33):** Added by the proxy to maintain state between the original request and the forwarded request. This is how the proxy remembers which NAS is waiting for which response.

### eduroam — Real-World RADIUS Federation

**eduroam** (education roaming) is the world's largest RADIUS federation, allowing university students to connect to Wi-Fi at any participating institution worldwide using their home university credentials.

```
eduroam ARCHITECTURE
=====================

Student from University A
connects to Wi-Fi at University B

   Student          Univ B's AP      Univ B RADIUS    National Proxy    Univ A RADIUS
      |                  |                |                 |                |
      | Connect          |                |                 |                |
      |----------------->|                |                 |                |
      |                  | Access-Request |                 |                |
      |                  | (alice@uniA.edu)|               |                |
      |                  |--------------->|                 |                |
      |                  |                | Realm=uniA.edu  |                |
      |                  |                | Not local! Fwd  |                |
      |                  |                |---------------->|                |
      |                  |                |                 | Route to       |
      |                  |                |                 | uniA.edu proxy |
      |                  |                |                 |--------------->|
      |                  |                |                 |                | Verify alice
      |                  |                |                 |                | in own DB
      |                  |                |                 | Access-Accept  |
      |                  |                |                 |<---------------|
      |                  |                | Access-Accept   |                |
      |                  |                |<----------------|                |
      |                  | Access-Accept  |                 |                |
      |                  |<---------------|                 |                |
      | EAP-Success      |                |                 |                |
      |<-----------------|                |                 |                |
      | CONNECTED        |                |                 |                |
```

This is the power of RADIUS federation — a student in India connects to Wi-Fi in Germany using their home university account, all through a chain of RADIUS proxies.

---

## 12. Network Access Server (NAS)

The NAS is the **edge enforcement point** — it enforces whatever the RADIUS server decides. Let's understand it thoroughly.

### NAS-Specific Attributes

```
NAS Identification Attributes:
+---------------------------+-----------------------------------+
| Attribute                 | Example Value                     |
+---------------------------+-----------------------------------+
| NAS-IP-Address (4)        | 10.1.1.1                          |
| NAS-IPv6-Address (95)     | 2001:db8::1                       |
| NAS-Identifier (32)       | "building-3-switch"               |
| NAS-Port (5)              | 10001 (slot 1, port 1)            |
| NAS-Port-Id (87)          | "GigabitEthernet1/0/1"            |
| NAS-Port-Type (61)        | Ethernet, ISDN, Virtual, etc.     |
+---------------------------+-----------------------------------+
```

### NAS-Port-Type Values

```
+-------+------------------------------+
| Value | Port Type                    |
+-------+------------------------------+
|   0   | Async (modem)                |
|   1   | Sync (leased line)           |
|   2   | ISDN Sync                    |
|   3   | ISDN Async V.120             |
|   4   | ISDN Async V.110             |
|   5   | Virtual (VPN)                |
|  15   | Ethernet (wired LAN)         |
|  19   | Wireless 802.11              |
|  41   | Wireless UMTS                |
|  43   | ADSL CAP                     |
|  44   | ADSL DMT                     |
|  45   | IDSL                         |
|  46   | Ethernet VDSL                |
+-------+------------------------------+
```

### Called-Station-Id and Calling-Station-Id

These are **critical** for Wi-Fi and MAC-based authentication:

```
In Wi-Fi environments:
  Called-Station-Id (30)  = "AA-BB-CC-DD-EE-FF:SSID-Name"
                             (AP's MAC : SSID name)
  Calling-Station-Id (31) = "11-22-33-44-55-66"
                             (Client's MAC address)

In dial-up environments:
  Called-Station-Id  = phone number dialed
  Calling-Station-Id = phone number calling from (caller ID)

In VPN environments:
  Called-Station-Id  = VPN gateway identifier
  Calling-Station-Id = client's source IP address
```

---

## 13. RADIUS Shared Secret — Security Foundation

The **shared secret** is the cryptographic foundation of RADIUS security. It is a pre-shared secret known only to the NAS and the RADIUS server. Every message is cryptographically tied to this secret.

### What the Shared Secret Protects

1. **Password encryption** — User-Password is XOR'd with MD5(secret + authenticator)
2. **Message-Authenticator (HMAC-MD5)** — proves packet integrity
3. **Response Authenticator** — proves response came from an authorized server
4. **Key derivation** — MS-MPPE keys are derived using the shared secret

### Message-Authenticator (Attribute 80)

This is **required** for EAP packets (RFC 3579) and is a best practice for all packets.

```
Message-Authenticator = HMAC-MD5(entire packet, shared_secret)
                        (with Message-Authenticator field zeroed out during computation)
```

This provides **integrity protection** for the entire RADIUS packet. Without it, an attacker could forge Access-Accept packets.

### Shared Secret Requirements

Best practices:

```
SHARED SECRET STRENGTH REQUIREMENTS
=====================================

MINIMUM (barely acceptable):
  Length: 16+ characters
  Charset: alphanumeric + symbols
  Example: "R@d1usS3cr3t!2024"

RECOMMENDED:
  Length: 32+ characters  
  Charset: full random bytes
  Example: base64-encoded random: "mK9xQzPn7Rv2LYw4sA8uCjT5eN6hD3bF"

BEST PRACTICE:
  Length: 32+ characters
  Source: Cryptographically secure random number generator
  Rotation: Every 90 days
  Unique per NAS: YES (each NAS has its own secret)

AVOID:
  - Dictionary words
  - "radius", "secret", "password"
  - Reusing the same secret for all NAS devices
  - Short secrets (<16 chars)
```

### RFC 2865 Shared Secret Limitations

The original RFC 2865 has a fundamental security flaw: there is **no forward secrecy**. If the shared secret is compromised, all past traffic can be decrypted. This is one of the main motivations for **RadSec** (RADIUS over TLS).

---

## 14. RADIUS vs DIAMETER

**DIAMETER** is the **successor protocol** to RADIUS, designed to address RADIUS's limitations. The name is a pun — DIAMETER is twice RADIUS (2× RADIUS).

### Comparison Table

```
+----------------------------+-------------------+------------------------+
| Feature                    | RADIUS            | DIAMETER               |
+----------------------------+-------------------+------------------------+
| RFC                        | 2865/2866         | 6733                   |
| Transport                  | UDP               | TCP or SCTP            |
| Reliability                | Application layer | Transport layer        |
| Port (Auth)                | 1812              | 3868                   |
| Port (Acct)                | 1813              | 3868 (same)            |
| TLS support                | RadSec (add-on)   | Native                 |
| Packet size                | Max 4096 bytes    | Unlimited (TCP)        |
| Attribute space            | 8-bit type (256)  | 32-bit AVP code        |
| Error handling             | Basic             | Rich error codes       |
| Routing                    | Proxy hops        | Agent network          |
| State machine              | Stateless         | Stateful (with CER/CEA)|
| Peer discovery             | Manual            | Dynamic                |
| Failover                   | No standard       | Built-in               |
| Capability negotiation     | None              | CER/CEA handshake      |
| Agent types                | Proxy only        | Relay, Proxy, Redirect,|
|                            |                   | Translation agents     |
| Primary use today          | Enterprise,       | Telecom (4G/5G),       |
|                            | Wi-Fi, VPN        | IMS, Ro/Rf interfaces  |
+----------------------------+-------------------+------------------------+
```

### DIAMETER Message Structure

```
DIAMETER PACKET FORMAT
=======================

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Version    |                 Message Length                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| command flags |                  Command Code                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Application-ID                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Hop-by-Hop Identifier                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      End-to-End Identifier                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  AVPs ...
+-+-+-+-+-+-+-

Note: Two separate identifiers (Hop-by-Hop and End-to-End) enable
      tracking across proxy chains — impossible in RADIUS.
```

### DIAMETER AVP (Attribute-Value-Pair) Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           AVP Code                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|V M P r r r r r|                  AVP Length                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Vendor-ID (if V bit set)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Data ...
+-+-+-+-+-+-+-

AVP Code: 32-bit (vs RADIUS's 8-bit) — 4 billion possible attributes
V bit: Vendor-ID present
M bit: Mandatory (error if not understood)
P bit: Protected (encrypt this AVP with CMS)
```

---

## 15. RadSec — RADIUS over TLS

**RadSec** (RFC 6614) solves RADIUS's transport security problem by running RADIUS over TLS/TCP instead of UDP.

### Why RadSec?

```
RADIUS Security Problem:
  - UDP transport: no encryption, no reliability
  - All security depends on shared secret + MD5
  - MD5 is cryptographically broken (collision attacks)
  - No forward secrecy
  - Inter-realm traffic (proxy chains) carries sensitive data across the internet

RadSec Solution:
  - TLS 1.2/1.3 provides: encryption, authentication, integrity, forward secrecy
  - Mutual TLS: both NAS and RADIUS server authenticate with certificates
  - Standard port: 2083/TCP
  - Fallback to shared secret still possible for compatibility
```

### RadSec Architecture

```
RADSEC TRANSPORT COMPARISON
=============================

Traditional RADIUS:
  NAS ----UDP/1812---> RADIUS Server
  (UDP: no connection, no encryption, no guaranteed delivery)
  Security: MD5-based, shared secret

RadSec:
  NAS ----TLS/TCP/2083---> RADIUS Server
  |                              |
  Cert: nas.corp.com      Cert: radius.corp.com
  (Mutual TLS authentication: both sides verify certificates)
  Security: TLS 1.3, PFS, strong cipher suites

eduroam with RadSec:
  Univ A <====TLS====> National Proxy <====TLS====> Univ B
  (All inter-realm traffic encrypted with proper TLS)
```

### RadSec Configuration (FreeRADIUS example)

```
# /etc/raddb/sites-enabled/tls
listen {
    ipaddr = *
    port   = 2083
    type   = auth+acct
    proto  = tcp
    tls {
        private_key_file = ${certdir}/server.key
        certificate_file = ${certdir}/server.pem
        ca_file          = ${cadir}/ca.pem
        tls_min_version  = "1.2"
        cipher_list      = "ECDHE-RSA-AES256-GCM-SHA384:..."
    }
}
```

---

## 16. EAP Deep Dive

EAP is so central to modern RADIUS (especially 802.1X Wi-Fi and VPN) that it deserves its own detailed section.

### EAP Packet Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Code      |  Identifier   |             Length            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Data ...
+-+-+-+-+-+-+-

EAP Code Values:
  1 = Request  (server to client: "prove yourself")
  2 = Response (client to server: "here's my proof")
  3 = Success  (server to client: "you're in")
  4 = Failure  (server to client: "access denied")
```

EAP Request/Response contain a **Type** byte indicating which EAP method:
```
Type  1 = Identity (username request)
Type  2 = Notification
Type  3 = NAK (Not Acceptable: "I don't support that method")
Type  4 = MD5-Challenge
Type 13 = EAP-TLS
Type 21 = EAP-TTLS
Type 25 = PEAP
Type 26 = MS-CHAP-V2 (inside tunnel)
Type 43 = EAP-FAST
Type 50 = EAP-pwd
Type 56 = EAP-TEAP (RFC 7170, modern standard)
```

### EAP-TLS — The Gold Standard

EAP-TLS requires **certificates on BOTH sides** — the client has a certificate, and the server has a certificate. This provides the strongest authentication.

```
EAP-TLS FLOW
=============

Client (Supplicant)       RADIUS Server
        |                      |
        | EAP-Identity         |
        | (username)           |
        |--------------------->|
        |                      |
        | EAP-Request/TLS      |
        | (TLS Start)          |
        |<---------------------|
        |                      |
        | EAP-Response/TLS     |
        | (ClientHello)        |
        |--------------------->|
        |                      |
        | EAP-Request/TLS      |
        | (ServerHello,        |
        |  Certificate,        |  <- Server cert (client verifies this)
        |  CertificateRequest, |  <- Server requests client cert
        |  ServerHelloDone)    |
        |<---------------------|
        |                      |
        | EAP-Response/TLS     |
        | (Certificate,        |  <- Client cert (server verifies this)
        |  ClientKeyExchange,  |
        |  CertVerify,         |
        |  ChangeCipherSpec,   |
        |  Finished)           |
        |--------------------->|
        |                      |
        | EAP-Request/TLS      |
        | (ChangeCipherSpec,   |
        |  Finished)           |
        |<---------------------|
        |                      |
        | EAP-Response/TLS     |
        | (ACK)                |
        |--------------------->|
        |                      |
        | EAP-Success          |
        | [MSK exported from   |
        |  TLS session]        |
        |<---------------------|
        |                      |
        [TLS keys used to derive
         PMK for WPA2/3 encryption]

PROS: Mutual auth, certificate-based, no passwords
CONS: PKI infrastructure required for every client
```

### PEAP — Protected EAP

PEAP (Protected EAP) is a **two-phase** protocol:

**Phase 1**: Establish a TLS tunnel (only **server** certificate needed)
**Phase 2**: Run another EAP method inside the TLS tunnel (typically MS-CHAPv2)

This is the most common enterprise Wi-Fi authentication method.

```
PEAP FLOW
==========

                    Phase 1: Establish TLS Tunnel
                    ================================
Client                     RADIUS Server
  |                             |
  | EAP-Identity (identity)     |
  |---------------------------->|
  |                             |
  | EAP-Request PEAP Start      |
  |<----------------------------|
  |                             |
  | [TLS Handshake]             |
  | ClientHello                 |
  |---------------------------->|
  | ServerHello + Certificate   |
  | (CLIENT verifies server cert)|
  |<----------------------------|
  | ClientKeyExchange, etc.     |
  |---------------------------->|
  |                             |
  | TLS Tunnel Established      |  ===ENCRYPTED===
  +============================++==================
                    Phase 2: Inner Authentication (inside tunnel)
                    ==============================================
  |                             |
  | [Inside TLS tunnel]         |
  |                             |
  | EAP-Identity (real username)|
  |---------------------------->|
  |                             |
  | EAP-Request MS-CHAPv2       |
  | (challenge)                 |
  |<----------------------------|
  |                             |
  | EAP-Response MS-CHAPv2      |
  | (NT-Response)               |
  |---------------------------->|
  |                             |
  | EAP-Request MS-CHAPv2       |
  | (Success, Auth-Response     |
  |  for mutual auth)           |
  |<----------------------------|
  |                             |
  | EAP-Response MS-CHAPv2 ACK  |
  |---------------------------->|
  |                             |
  | EAP-Success                 |
  |<----------------------------|

PROS: Only server certificate needed (easier deployment)
CONS: Client doesn't verify inner identity binding
      (see PEAP unauthenticated identity issue)
```

### EAP-TTLS — Tunneled TLS

Similar to PEAP but more flexible. Inside the TLS tunnel, it can carry:
- Any EAP method
- RADIUS AVPs (attributes) directly — including PAP (plaintext password inside TLS is secure!)

```
EAP-TTLS Inner Methods:
+------------------+----------------------------------------------+
| Inner Method     | Description                                  |
+------------------+----------------------------------------------+
| EAP-MS-CHAPv2    | Most common, same as PEAP inner              |
| PAP              | Password in plaintext (safe inside TLS)      |
| CHAP             | Challenge-response                           |
| EAP-MD5          | Simple MD5 challenge                         |
| EAP-GTC          | Generic Token Card (OTP)                     |
+------------------+----------------------------------------------+
```

### EAP State Machine in RADIUS

The RADIUS server must maintain **state** across multiple Access-Request/Challenge exchanges. The **State attribute (Type 24)** carries an opaque value that the NAS echoes back:

```
STATE TRACKING IN RADIUS
==========================

RADIUS Server (with State):
  Request 1: Access-Request [User-Name, EAP-Start]
  Response 1: Access-Challenge [State=AAAA, EAP-Request/Identity]
              ^^^^
              Server remembers EAP session state tagged as AAAA

  Request 2: Access-Request [User-Name, State=AAAA, EAP-Response/Identity]
                                        ^^^^
                                        NAS echoes State back
  Response 2: Access-Challenge [State=BBBB, EAP-Request/TLS]
  ...
  Request N: Access-Request [User-Name, State=ZZZZ, EAP-Response/TLS-Finished]
  Response N: Access-Accept [EAP-Success, VLAN, Session-Timeout, ...]
```

---

## 17. FreeRADIUS — Real-World Implementation

**FreeRADIUS** is the world's most widely deployed RADIUS server. It is open-source, highly configurable, and supports every RADIUS feature.

### FreeRADIUS Architecture

```
FREERADIUS INTERNAL ARCHITECTURE
==================================

              Request arrives
                    |
                    v
            +---------------+
            |  Listener     |  (UDP socket, TLS socket)
            +-------+-------+
                    |
                    v
            +-------+-------+
            |  Request      |
            |  Processing   |
            |  Pipeline     |
            +-------+-------+
                    |
         +----------+-----------+
         |          |           |
         v          v           v
    +--------+  +--------+  +--------+
    |authorize|  |authen- |  |account-|
    |  section|  |ticate  |  |  ing   |
    |         |  | section|  | section|
    +----+----+  +----+---+  +----+---+
         |            |           |
    [modules]    [modules]   [modules]

Modules (pluggable):
  files      - local users file
  ldap       - LDAP/Active Directory
  sql        - SQL database (MySQL, PostgreSQL)
  eap        - EAP framework
  mschap     - MS-CHAP authentication
  pap        - PAP authentication
  chap       - CHAP authentication
  preprocess - Request preprocessing
  detail     - Write accounting to flat file
  redis      - Redis for session/rate limiting
  python     - Python modules
  perl       - Perl modules
  rest       - REST API integration
```

### FreeRADIUS Directory Structure

```
/etc/raddb/
├── radiusd.conf          # Main configuration file
├── clients.conf          # NAS/client definitions
├── users                 # Local user database
├── proxy.conf            # Proxy and realm configuration
├── policy.d/             # Policy definitions
│   ├── filter            # Attribute filtering
│   └── accounting        # Accounting policies
├── mods-available/       # Module configurations (all)
│   ├── eap               # EAP module config
│   ├── sql               # SQL module config
│   ├── ldap              # LDAP module config
│   └── ...
├── mods-enabled/         # Symlinks to active modules
├── sites-available/      # Virtual server configs
│   ├── default           # Main auth/acct site
│   ├── inner-tunnel      # PEAP/TTLS inner auth
│   └── tls               # RadSec config
├── sites-enabled/        # Symlinks to active sites
├── certs/                # TLS certificates
│   ├── ca.pem            # CA certificate
│   ├── server.pem        # Server certificate
│   └── server.key        # Server private key
└── dictionary            # Attribute definitions
```

### Key Configuration Files

#### clients.conf — Define NAS Devices

```
# clients.conf
# Each NAS that is allowed to talk to this RADIUS server

client wifi_ap_building1 {
    ipaddr          = 10.1.1.100       # NAS IP address
    secret          = "xK9pQ7rN3mL5vB2wA8sD6tF4jH1yC0e"  # Shared secret
    shortname       = "building1-ap"
    nastype         = other            # or: cisco, livingston, merit, etc.
    
    # Virtual server for this client (optional)
    # virtual_server = enterprise_auth
}

client vpn_gateway {
    ipaddr          = 10.1.1.50
    secret          = "differentSecretForVPN7Kx9Mz3Pw"
    nastype         = cisco
    shortname       = vpn-gw
}

# Allow entire subnet of APs
client all_aps {
    ipaddr          = 10.0.0.0/24
    secret          = "subnetSharedSecret"
    shortname       = "all-aps"
}
```

#### users — Local User Database

The users file format is crucial to understand. Each entry has:
- A **check** section (conditions that must match)
- A **reply** section (attributes to send back)

```
# /etc/raddb/users
# Format:
# username   Attribute=Value, ...          <- check items (conditions)
#            Reply-Attribute=Value, ...    <- reply items (what to send back)

# Simple user with password and VLAN
alice         Cleartext-Password := "her_password"
              Tunnel-Type = VLAN,
              Tunnel-Medium-Type = IEEE-802,
              Tunnel-Private-Group-ID = "100",
              Session-Timeout = 28800

# User with NT hash (for MS-CHAP)
bob           NT-Password := "nt_hash_hex_here"
              Service-Type = Framed-User,
              Framed-Protocol = PPP

# MAC address authentication (no password - MAC is username)
aa-bb-cc-dd-ee-ff   Auth-Type := Accept
                    Tunnel-Type = VLAN,
                    Tunnel-Medium-Type = IEEE-802,
                    Tunnel-Private-Group-ID = "200"

# Catch-all DEFAULT entry
DEFAULT         Auth-Type = Reject,
                Reply-Message = "Access denied: contact IT support"
```

**Check Item Operators:**

```
:=   Set (force assign, regardless of existing value)
==   Equal (check item must equal this value)
!=   Not equal
>=   Greater than or equal
<=   Less than or equal
=~   Regular expression match (Perl compatible)
!~   Regular expression not match
=*   Always matches (attribute must exist)
!*   Never matches (attribute must not exist)
```

#### radiusd.conf — Main Configuration

```
# /etc/raddb/radiusd.conf (key sections)

# Run as this user/group
user  = radiusd
group = radiusd

# Log configuration
log {
    destination = files
    file        = ${logdir}/radius.log
    requests    = yes            # Log all requests
    auth        = yes            # Log auth decisions
    auth_badpass = yes          # Log bad passwords (careful: security)
    auth_goodpass = no          # Don't log good passwords (security)
}

# Performance tuning
thread pool {
    start_servers    = 5
    max_servers      = 32
    min_spare_servers = 3
    max_spare_servers = 10
    max_requests_per_server = 0   # 0 = unlimited
    auto_limit_acct  = no
}

# Security
security {
    max_attributes    = 200       # Max attributes per packet
    reject_delay      = 1         # Seconds to delay reject (anti-brute-force)
    status_server     = yes       # Respond to Status-Server packets
}
```

#### mods-available/eap — EAP Configuration

```
# /etc/raddb/mods-available/eap
eap {
    default_eap_type    = peap       # Default EAP method
    timer_expire        = 60         # Seconds to keep EAP state
    max_sessions        = ${max_requests}

    # EAP-TLS configuration
    tls-config tls-common {
        private_key_password = "server_key_password"
        private_key_file     = ${certdir}/server.key
        certificate_file     = ${certdir}/server.pem
        ca_file              = ${cadir}/ca.pem
        
        # DH parameters for DHE cipher suites
        dh_file              = ${certdir}/dh
        
        # OCSP for certificate revocation
        # ocsp { ... }
        
        # Minimum TLS version
        tls_min_version      = "1.2"
        
        # Cipher suites (TLS 1.2)
        cipher_list          = "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384"
    }
    
    tls {
        tls = tls-common
    }
    
    peap {
        tls = tls-common
        default_method = mschapv2    # Inner auth method
        copy_request_to_tunnel = no
        use_tunneled_reply = no
        
        virtual_server = "inner-tunnel"   # Process inner auth here
    }
    
    ttls {
        tls = tls-common
        default_eap_type = mschapv2
        copy_request_to_tunnel = no
        use_tunneled_reply = no
        virtual_server = "inner-tunnel"
    }
    
    mschapv2 {
        # No special config needed usually
    }
}
```

### Processing Pipeline — The Virtual Server

The `default` site defines what happens to every request:

```
# /etc/raddb/sites-available/default

server default {

    # Authentication requests
    authorize {
        # 1. Preprocess (fix up Calling-Station-Id format, etc.)
        preprocess
        
        # 2. Get user's cached password or info
        chap           # Handle CHAP attribute detection
        mschap         # Handle MS-CHAP detection
        
        # 3. Look up user in database
        files          # Check local users file
        # -ldap        # Uncomment to check LDAP
        # -sql         # Uncomment to check SQL
        
        # 4. EAP handling — set Auth-Type=EAP if EAP packet
        eap {
            ok = return
        }
        
        # 5. Detect auth type
        pap
    }
    
    # Perform actual authentication
    authenticate {
        Auth-Type PAP {
            pap
        }
        Auth-Type CHAP {
            chap
        }
        Auth-Type MS-CHAP {
            mschap
        }
        Auth-Type EAP {
            eap
        }
    }
    
    # Post-authentication (session setup, logging)
    post-auth {
        # Update session database
        # -sql
        # exec          # Run external scripts
        
        # Handle rejects
        Post-Auth-Type REJECT {
            # Add reject delay
            attr_filter.access_reject
        }
    }
    
    # Accounting requests
    preacct {
        preprocess
        acct_unique       # Generate unique accounting key
    }
    
    accounting {
        detail            # Write to detail file
        # -sql            # Write to SQL database
        # -redis          # Track in Redis
    }
}
```

### Testing with radtest

```bash
# Basic authentication test
radtest username password radius-server-ip 0 shared_secret

# Example:
radtest alice her_password 127.0.0.1 0 testing123

# Expected output:
# Sent Access-Request Id 12 from 0.0.0.0:57473 to 127.0.0.1:1812 length 74
#   User-Name = "alice"
#   User-Password = "her_password"
#   NAS-IP-Address = 127.0.0.1
#   NAS-Port = 0
#   Message-Authenticator = 0x00
# Received Access-Accept Id 12 from 127.0.0.1:1812 to 0.0.0.0:57473 length 44
#   Tunnel-Type:0 = VLAN
#   Tunnel-Medium-Type:0 = IEEE-802
#   Tunnel-Private-Group-Id:0 = "100"

# Test with specific EAP method
eapol_test -c peap-test.conf -s shared_secret
```

### LDAP/Active Directory Integration

```
# /etc/raddb/mods-available/ldap
ldap {
    server     = 'ldap.company.com'
    port       = 389
    
    # Bind credentials for searching
    identity   = 'cn=radius-reader,ou=service-accounts,dc=company,dc=com'
    password   = 'service_account_password'
    
    # Where to find users
    base_dn    = 'dc=company,dc=com'
    
    # How to find a user by username
    filter     = '(sAMAccountName=%{User-Name})'
    
    # For group membership checks
    group {
        base_dn    = 'dc=company,dc=com'
        filter     = '(objectClass=group)'
        name_attribute = cn
        membership_filter = '(member=%{control:Ldap-UserDn})'
    }
    
    # Password retrieval (for PAP/CHAP)
    update {
        control:Password-With-Header  += 'userPassword'
        control:                      += 'radiusControlAttribute'
        request:                      += 'radiusRequestAttribute'
        reply:                        += 'radiusReplyAttribute'
    }
    
    # TLS for LDAPS
    tls {
        start_tls  = no          # Set yes for STARTTLS
        ca_file    = /etc/ssl/certs/company-ca.pem
    }
}
```

### SQL Integration

```
# /etc/raddb/mods-available/sql
sql {
    dialect     = "mysql"     # or postgresql, sqlite
    driver      = "rlm_sql_mysql"
    
    server      = "localhost"
    port        = 3306
    login       = "radius"
    password    = "db_password"
    radius_db   = "radius"
    
    # Query to get check and reply attributes for a user
    read_clients = yes        # Read clients from DB too
    
    pool {
        start      = 5
        min        = 4
        max        = 32
        spare      = 3
        uses       = 0
        retry_delay = 30
        lifetime   = 0
        idle_timeout = 60
    }
}

-- SQL Schema (standard FreeRADIUS tables):

-- Check attributes (conditions)
CREATE TABLE radcheck (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(64) NOT NULL DEFAULT '',
    attribute   VARCHAR(64) NOT NULL DEFAULT '',
    op          CHAR(2) NOT NULL DEFAULT '==',
    value       VARCHAR(253) NOT NULL DEFAULT ''
);

-- Reply attributes (what to send back)
CREATE TABLE radreply (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(64) NOT NULL DEFAULT '',
    attribute   VARCHAR(64) NOT NULL DEFAULT '',
    op          CHAR(2) NOT NULL DEFAULT '=',
    value       VARCHAR(253) NOT NULL DEFAULT ''
);

-- Group membership
CREATE TABLE radusergroup (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(64) NOT NULL DEFAULT '',
    groupname   VARCHAR(64) NOT NULL DEFAULT '',
    priority    INT NOT NULL DEFAULT 1
);

-- Group check attributes
CREATE TABLE radgroupcheck (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    groupname   VARCHAR(64) NOT NULL DEFAULT '',
    attribute   VARCHAR(64) NOT NULL DEFAULT '',
    op          CHAR(2) NOT NULL DEFAULT '==',
    value       VARCHAR(253) NOT NULL DEFAULT ''
);

-- Group reply attributes
CREATE TABLE radgroupreply (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    groupname   VARCHAR(64) NOT NULL DEFAULT '',
    attribute   VARCHAR(64) NOT NULL DEFAULT '',
    op          CHAR(2) NOT NULL DEFAULT '=',
    value       VARCHAR(253) NOT NULL DEFAULT ''
);

-- Accounting (session records)
CREATE TABLE radacct (
    radacctid           BIGINT AUTO_INCREMENT PRIMARY KEY,
    acctsessionid       VARCHAR(64) NOT NULL DEFAULT '',
    acctuniqueid        VARCHAR(32) NOT NULL DEFAULT '',
    username            VARCHAR(64) NOT NULL DEFAULT '',
    realm               VARCHAR(64) DEFAULT '',
    nasipaddress        VARCHAR(15) NOT NULL DEFAULT '',
    nasportid           VARCHAR(15) DEFAULT NULL,
    nasporttype         VARCHAR(32) DEFAULT NULL,
    acctstarttime       DATETIME DEFAULT NULL,
    acctstoptime        DATETIME DEFAULT NULL,
    acctsessiontime     INT(12) DEFAULT NULL,
    acctauthentic       VARCHAR(32) DEFAULT NULL,
    connectinfo_start   VARCHAR(50) DEFAULT NULL,
    connectinfo_stop    VARCHAR(50) DEFAULT NULL,
    acctinputoctets     BIGINT DEFAULT NULL,
    acctoutputoctets    BIGINT DEFAULT NULL,
    calledstationid     VARCHAR(50) NOT NULL DEFAULT '',
    callingstationid    VARCHAR(50) NOT NULL DEFAULT '',
    acctterminatecause  VARCHAR(32) NOT NULL DEFAULT '',
    servicetype         VARCHAR(32) DEFAULT NULL,
    framedprotocol      VARCHAR(32) DEFAULT NULL,
    framedipaddress     VARCHAR(15) NOT NULL DEFAULT '',
    framedipv6address   VARCHAR(45) NOT NULL DEFAULT '',
    framedipv6prefix    VARCHAR(45) NOT NULL DEFAULT '',
    framedinterfaceid   VARCHAR(44) NOT NULL DEFAULT '',
    delegatedipv6prefix VARCHAR(45) NOT NULL DEFAULT ''
);
```

---

## 18. Packet Capture and Protocol Analysis

Understanding how to **read a real RADIUS capture** is critical for debugging.

### Using tcpdump to Capture RADIUS

```bash
# Capture RADIUS packets (auth + accounting)
sudo tcpdump -i eth0 -w radius_capture.pcap "udp port 1812 or udp port 1813"

# Decode in real-time (requires RADIUS secret in wireshark)
sudo tcpdump -i eth0 -nvX "udp port 1812"

# FreeRADIUS debug mode (best for troubleshooting)
sudo radiusd -X    # Runs in foreground with full debug output
```

### Reading FreeRADIUS Debug Output

```
(0) Received Access-Request Id 42 from 10.1.1.100:51234 to 10.1.1.1:1812 length 118
(0)   User-Name = "alice"
(0)   User-Password = "\262\044\246..."     <- encrypted
(0)   NAS-IP-Address = 10.1.1.100
(0)   NAS-Port = 1
(0)   Message-Authenticator = 0x4a2b...    <- HMAC-MD5
(0)   Called-Station-Id = "AA-BB-CC-DD-EE-FF:CorpWifi"
(0)   Calling-Station-Id = "11-22-33-44-55-66"
(0) # Executing section authorize from file /etc/raddb/sites-enabled/default
(0)   [preprocess] = ok
(0)   [chap] = noop                        <- Not CHAP
(0)   [mschap] = noop                      <- Not MS-CHAP
(0)   [files] = updated                    <- Found in users file!
(0)   [pap] = updated                      <- Auth-Type set to PAP
(0) Found Auth-Type = pap
(0) # Executing group from file /etc/raddb/sites-enabled/default
(0)   Auth-Type PAP {
(0)     [pap] = ok                         <- PAP auth succeeded!
(0)   }
(0) Sent Access-Accept Id 42 from 10.1.1.1:1812 to 10.1.1.100:51234 length 64
(0)   Tunnel-Type:0 = VLAN
(0)   Tunnel-Medium-Type:0 = IEEE-802
(0)   Tunnel-Private-Group-Id:0 = "100"
(0)   Session-Timeout = 28800
```

### Annotated Access-Request Hex Dump

```
RADIUS Access-Request Packet (Hex + Annotation)
================================================

01          Code = 1 (Access-Request)
2a          Identifier = 42
00 76       Length = 118 bytes total

-- Authenticator (16 bytes, random) --
a3 f7 2c 11 89 b4 5e 32
d0 7a 1f 4c 83 c6 9e 50

-- Attributes --

01          Type = 1 (User-Name)
07          Length = 7 bytes (type + length + 5 value bytes)
61 6c 69 63 65    Value = "alice"

02          Type = 2 (User-Password)
12          Length = 18 bytes (type + length + 16 encrypted bytes)
b2 2c a6 f3 9d 41 77 e0    <- encrypted password
5c 38 1a b9 c4 62 d7 08    (16 bytes total)

04          Type = 4 (NAS-IP-Address)
06          Length = 6
0a 01 01 64    Value = 10.1.1.100

05          Type = 5 (NAS-Port)
06          Length = 6
00 00 00 01    Value = 1

50          Type = 80 (Message-Authenticator)
12          Length = 18
4a 2b 8f 1c 7e 39 ... (16 bytes HMAC-MD5)
```

---

## 19. Security Threats and Mitigations

### Threat Model

```
RADIUS THREAT LANDSCAPE
========================

Threat 1: Man-in-the-Middle (MitM)
  Attack:  Attacker intercepts RADIUS traffic between NAS and Server
  Impact:  Capture encrypted passwords, forge responses
  RADIUS defense: Shared secret, Message-Authenticator
  Better defense: RadSec (TLS encryption)

Threat 2: Rogue RADIUS Server
  Attack:  Attacker runs a RADIUS server, tricks NAS to use it
  Impact:  Credential harvesting (especially with PEAP)
  Defense: Certificate validation (don't skip server cert check!)
           Use EAP-TLS instead of PEAP

Threat 3: Offline Dictionary Attack
  Attack:  Capture Access-Request, offline brute-force shared secret
           Then decrypt User-Password from other packets
  Defense: Strong shared secret (32+ random chars)
           RadSec (TLS prevents capture of packets)

Threat 4: Replay Attack
  Attack:  Capture Access-Accept, replay to NAS for re-authorization
  Defense: Message-Authenticator with random Request Authenticator
           Short session timeouts

Threat 5: RADIUS Blast / DoS
  Attack:  Flood RADIUS server with bogus Access-Requests
  Defense: Rate limiting on NAS and RADIUS server
           IP allowlist for NAS devices

Threat 6: Packet Spoofing (Fake Access-Accept)
  Attack:  Forge Access-Accept with NAS's source IP, bypass auth
  Defense: Message-Authenticator (HMAC-MD5) — MUST be validated
           RadSec: TLS prevents spoofing

Threat 7: EAP Downgrade Attack
  Attack:  MitM intercepts PEAP negotiation, forces weaker EAP-MD5
  Defense: Server-side minimum EAP type enforcement
           Client-side minimum EAP type enforcement

Threat 8: PEAP Identity Exposure
  Attack:  In PEAP Phase 1, outer identity is sent in plaintext
           (before TLS tunnel)
  Defense: Use anonymous outer identity (e.g., "anonymous@realm")
           EAP-TLS, EAP-TTLS use identity protection better

Threat 9: MD5 Weakness
  Attack:  MD5 collisions (theoretical) weaken authenticator security
  Defense: Message-Authenticator (HMAC-MD5) is collision-resistant
           RadSec removes dependence on MD5 entirely
```

### Security Hardening Checklist

```
RADIUS SECURITY HARDENING CHECKLIST
=====================================

[x] Use strong, unique shared secrets (32+ random chars) per NAS
[x] Enable Message-Authenticator validation on all packets
[x] Use RadSec (TLS) for inter-realm traffic
[x] Configure firewall: only allow NAS IPs to reach port 1812/1813
[x] Disable weak EAP methods (MD5, LEAP)
[x] Enable OCSP/CRL for certificate revocation checking
[x] Use EAP-TLS for highest security (where PKI is feasible)
[x] If using PEAP: enforce server certificate validation on clients
[x] Set reasonable Session-Timeout and Idle-Timeout
[x] Enable accounting for audit trail
[x] Log all auth failures with IP/MAC for incident response
[x] Rotate shared secrets periodically (90-day rotation recommended)
[x] Use reject delay (1 second) to slow brute-force attempts
[x] Monitor for excessive auth failures (security alert threshold)
[x] Separate RADIUS traffic to a dedicated management network
[x] Use RADIUS server redundancy (primary + secondary)
[x] Keep FreeRADIUS updated (security patches)
```

---

## 20. Common Use Cases

### Use Case 1: Enterprise Wi-Fi (802.1X / WPA2-Enterprise)

```
ENTERPRISE WI-FI ARCHITECTURE
===============================

Employee Laptop            Wi-Fi AP           RADIUS Server      Active Directory
     |                        |                    |                  |
     | 802.11 Association      |                    |                  |
     |----------------------->|                    |                  |
     |                        |                    |                  |
     | EAP Exchange (PEAP)     |                    |                  |
     |<---------------------->| RADIUS Packets     |                  |
     |                        |<------------------>|                  |
     |                        |                    | LDAP/Kerberos    |
     |                        |                    |<---------------->|
     |                        |                    |                  |
     |                        | Access-Accept:      |                  |
     |                        | VLAN=100 (Corp)    |                  |
     |                        | Session-Timeout=8h |                  |
     |<---------------------- |                    |                  |
     | Connected to Corp VLAN  |                    |                  |
     |                        |                    |                  |

Guest connecting to same AP:
     Guest Phone             Wi-Fi AP           RADIUS Server
          |                     |                    |
          | 802.11 Association  |                    |
          |-------------------->|                    |
          | PEAP/guest login    |                    |
          |<------------------->|<------------------>|
          |                     |                    |
          |                     | Access-Accept:     |
          |                     | VLAN=200 (Guest)  |
          |                     | Bandwidth=5Mbps   |
          |<--------------------|                    |
          | Connected to Guest VLAN                  |
          | (Internet only, no corp access)          |
```

### Use Case 2: VPN Authentication

```
VPN RADIUS AUTHENTICATION
==========================

Remote User              VPN Gateway         RADIUS Server      Internal Services
    |                         |                   |                   |
    | VPN Connect             |                   |                   |
    | (user@company.com,      |                   |                   |
    |  password)              |                   |                   |
    |------------------------>|                   |                   |
    |                         | Access-Request    |                   |
    |                         | [User-Name,       |                   |
    |                         |  User-Password,   |                   |
    |                         |  NAS-Port-Type=   |                   |
    |                         |  Virtual(5)]      |                   |
    |                         |------------------>|                   |
    |                         |                   | Verify in AD      |
    |                         |                   |                   |
    |                         | Access-Accept     |                   |
    |                         | [Framed-IP=       |                   |
    |                         |  10.10.0.50,      |                   |
    |                         |  Framed-Route=    |                   |
    |                         |  10.0.0.0/8,      |                   |
    |                         |  Session-Timeout= |                   |
    |                         |  28800,           |                   |
    |                         |  cisco-avpair=    |                   |
    |                         |  "ipsec:group=    |                   |
    |                         |   employees"]     |                   |
    |                         |<------------------|                   |
    | IP: 10.10.0.50          |                   |                   |
    | Tunnel up               |                   |                   |
    |<------------------------|                   |                   |
    |                         |                   |                   |
    | Access internal services|                   |                   |
    |--------------------------------------------------------------------->
```

### Use Case 3: Network Switch 802.1X (Port Security)

```
802.1X PORT AUTHENTICATION
============================

Before Authentication:
+----------+     Unauth Port    +----------+
| PC       |<==================>| Switch   |
|          | Only EAP traffic   | Port in  |
|          | allowed            | auth VLAN|
+----------+                    +----------+

Authentication Process:
PC            Switch Port       RADIUS Server
 |                |                 |
 | EAPOL-Start    |                 |
 |--------------->|                 |
 |                | Access-Request  |
 | EAP Exchange   |<--------------->|
 |<-------------->|                 |
 |                | Access-Accept   |
 |                | [VLAN=100]      |
 |                |<----------------|
 |                |                 |
 | Port moves to  |                 |
 | authorized VLAN|                 |
 | (VLAN 100)     |                 |

After Authentication:
+----------+     Auth Port      +----------+
| PC       |<==================>| Switch   |
|          | Full network access| Port in  |
|          |                    | VLAN 100 |
+----------+                    +----------+

When PC disconnects:
  Switch sends EAPOL-Logoff (or detects link-down)
  Port returns to unauthorized/auth VLAN
  Accounting-Stop sent to RADIUS
```

### Use Case 4: ISP Broadband Authentication (PPPoE)

```
ISP DSL AUTHENTICATION
=======================

Home Router         DSL DSLAM/BRAS        ISP RADIUS Server    Billing System
     |                    |                     |                    |
     | PPPoE Discovery    |                     |                    |
     |------------------>|                     |                    |
     | PPPoE Session      |                     |                    |
     |<------------------|                     |                    |
     | LCP Negotiation    |                     |                    |
     |<----------------->|                     |                    |
     | PAP/CHAP Auth      |                     |                    |
     | (username@isp.com, |                     |                    |
     |  password)         |                     |                    |
     |------------------>|                     |                    |
     |                    | Access-Request      |                    |
     |                    |-------------------->|                    |
     |                    |                     | Verify credentials |
     |                    |                     | Check quota        |
     |                    | Access-Accept       |                    |
     |                    | [Framed-IP,         |                    |
     |                    |  Framed-Route,      |                    |
     |                    |  Session-Timeout=   |                    |
     |                    |  86400,             |                    |
     |                    |  cisco-avpair=      |                    |
     |                    |  "ip:bandwidth-     |                    |
     |                    |   limit=100mbps"]   |                    |
     |                    |<--------------------|                    |
     | IP Assigned         |                     |                    |
     | Internet access     |                     |                    |
     |<------------------|                     |                    |
     |                    | Acct-Start          |                    |
     |                    |-------------------->|                    |
     |                    |                     | Record session     |
     |                    |                     |-------------------->
     |                    |                     |                    |
     | [Every 5 min]      | Acct-Interim        |                    |
     |                    |-------------------->|                    |
     |                    |                     | Update quota used  |
```

### Use Case 5: Change of Authorization (CoA) / Dynamic Authorization

CoA (RFC 5176) allows the RADIUS **server to push changes to an active session** — without the user re-authenticating. This is a **reverse flow**: RADIUS server → NAS.

```
COA FLOW — Dynamic Session Modification
=========================================

Admin Portal    RADIUS Server           NAS (Switch/AP)     Connected User
    |                |                        |                   |
    | "Quarantine    |                        |                   |
    | user alice"    |                        |                   |
    |--------------->|                        |                   |
    |                | CoA-Request            |                   |
    |                | [Framed-IP=10.0.1.50, |                   |
    |                |  Tunnel-PVID=999,     |                   |  <- change VLAN to quarantine
    |                |  Filter-Id=           |                   |
    |                |  "QUARANTINE-ACL"]    |                   |
    |                |----------------------->|                  |
    |                |                        |                   |
    |                |                        | Apply new VLAN    |
    |                |                        | Apply new ACL     |
    |                |                        |                   |
    |                | CoA-ACK                |                   |
    |                |<------------------------|                  |
    |                |                        |                   |
    |  "Done"        |                        | Alice is now in   |
    |<---------------|                        | quarantine VLAN   |
    |                |                        |                   |

Disconnect-Request (kick user off):
    |                |                        |                   |
    | "Disconnect    |                        |                   |
    | user bob"      |                        |                   |
    |--------------->|                        |                   |
    |                | Disconnect-Request     |                   |
    |                | [User-Name=bob,       |                   |
    |                |  Calling-Station-Id=  |                   |
    |                |  "bob's MAC"]         |                   |
    |                |----------------------->|                  |
    |                |                        |                   |
    |                |                        | Disconnect bob    |
    |                |                        | Send Acct-Stop    |
    |                |                        |                   |
    |                | Disconnect-ACK         |                   |
    |                |<------------------------|                  |
```

CoA/Disconnect operates on port **3799/UDP** by default (on the NAS).

---

## 21. Troubleshooting RADIUS

### Common Problems and Solutions

```
TROUBLESHOOTING DECISION TREE
===============================

Problem: Authentication fails
          |
          v
Is the RADIUS server receiving the request?
  |               |
 YES              NO
  |               |
  v               v
Check FreeRADIUS  Check NAS config:
debug output:     - RADIUS server IP
radiusd -X        - Shared secret
                  - Port 1812
                  - Firewall rules
  |
  v
What does debug show?
  |
  +-- "Unknown client" ---------> Add NAS to clients.conf
  |
  +-- "No Auth-Type found" -----> Check authorize section,
  |                               check users file operator
  |
  +-- "Wrong password" ---------> Verify password in DB
  |                               Check password type (PAP vs NT hash)
  |
  +-- "EAP: Failed in EAP select"-> Check EAP config
  |                                 Check TLS certificates
  |
  +-- "LDAP: Bind failed" ------> Check LDAP credentials
  |                               Check LDAP server connectivity
  |                               Check base_dn
  |
  +-- Access-Accept sent but  --> Check NAS config
      user still denied           Check VLAN config
                                  Verify attribute format
```

### Systematic Debug Approach

```bash
# Step 1: Enable full FreeRADIUS debug
sudo systemctl stop freeradius
sudo freeradius -X 2>&1 | tee /tmp/radius_debug.log

# Step 2: Test from command line
radtest testuser testpassword 127.0.0.1 0 sharedsecret

# Step 3: Search debug output for key phrases
grep -E "(Accept|Reject|Error|WARN|ERR)" /tmp/radius_debug.log

# Step 4: Test EAP specifically
# Create eapol test config
cat > /tmp/eap_test.conf << 'EOF'
network={
    ssid="TestSSID"
    key_mgmt=WPA-EAP
    eap=PEAP
    identity="testuser"
    password="testpass"
    phase2="auth=MSCHAPV2"
    ca_cert="/etc/raddb/certs/ca.pem"
}
EOF
eapol_test -c /tmp/eap_test.conf -s sharedsecret -a 127.0.0.1

# Step 5: Check accounting separately
radtest testuser testpass 127.0.0.1 1 sharedsecret  # sends to port 1813
```

### Common Error Messages

```
Error: "Failed to load module 'rlm_sql_mysql'"
Fix: sudo apt install freeradius-mysql
     OR: sudo yum install freeradius-mysql

Error: "TLS_accept: error in SSLv3/TLS read client hello"
Fix: Check TLS version compatibility
     Ensure client trusts server certificate
     Check cipher suite compatibility

Error: "Ignoring request to authentication address..."
Fix: Check listen section in sites-enabled/default
     Ensure port = 1812 is configured

Error: "mschap: FAILED: No NT/LM-Password"
Fix: User must have NT-Password attribute
     PAP works with Cleartext-Password
     MS-CHAP needs NT-Password (NT hash of password)

Error: "eap: No EAP-Message, not doing EAP"
Fix: NAS must include EAP-Message attribute
     Check NAS 802.1X configuration

Error: "Attribute not found in dictionary"
Fix: Add attribute definition to /etc/raddb/dictionary
     Or install vendor dictionary file
```

---

## 22. Mental Models and Thinking Frameworks

### The Castle Gate Model (Revisited, Deeper)

Earlier we described RADIUS as a castle gatekeeper. Let's extend this model:

```
RADIUS AS CASTLE SECURITY SYSTEM
===================================

USER = Visitor wanting to enter
NAS  = Gate Guard (enforces decisions but doesn't decide)
RADIUS Server = Castle Security Office (makes all decisions)
Shared Secret = Secure phone line between guard and office
Attributes = Instructions sent over that phone line
Accounting = Visitor logbook in the office

Key insight: The guard (NAS) has NO authority by themselves.
They ONLY enforce what the security office says.
This is the principle of CENTRALIZED POLICY ENFORCEMENT.
```

### Mental Model 2: The Onion Model (EAP)

```
EAP is like nested envelopes:

Outermost envelope: RADIUS packet
  Middle envelope: EAP container
    Inner envelope: PEAP TLS tunnel
      Innermost letter: MS-CHAPv2 authentication

You understand RADIUS when you can:
1. Identify which layer something belongs to
2. Know what can see what (TLS tunnel protects inner content from eavesdroppers)
3. Understand what breaks what (server cert failure breaks Phase 1 = breaks everything)
```

### Mental Model 3: State Machine for EAP

```
EAP SESSION STATE MACHINE
==========================

States:
  IDLE ----------> IDENTITY_REQUEST -----> CHALLENGE -----> SUCCESS
                                    |              |
                                    v              v
                                 FAILURE       FAILURE
                                 (timeout,     (wrong response,
                                  no response)  wrong cert, etc.)

Key insight: RADIUS is STATELESS (UDP). The STATE attribute
is how the server embeds its internal state in the protocol.
The NAS is just a "state carrier" — it holds and echoes State
without understanding it. This is elegant protocol design.
```

### Mental Model 4: The AAA Contract

```
Think of every RADIUS session as a three-part contract:

AUTHENTICATION CONTRACT:
  "I am Alice, here is my proof"
  RADIUS verifies: "Yes, this is Alice"

AUTHORIZATION CONTRACT:
  "As Alice, you are allowed: VLAN 100, 10Mbps, 8 hours"
  RADIUS writes: these terms into the Access-Accept

ACCOUNTING CONTRACT:
  "This session: started at T1, ended at T2, consumed X bytes"
  RADIUS records: all terms of what actually happened

The power: Auditors can check all three parts.
Security teams can see: who connected, what they were allowed, what they did.
```

### Cognitive Principles for Mastery

**1. Chunking (George Miller's 7±2):**  
Don't try to memorize all 255 RADIUS attributes at once. Chunk them:
- Security attributes (Authenticator, Message-Authenticator, Shared Secret)
- Identity attributes (User-Name, Calling-Station-Id, Called-Station-Id)
- Authorization attributes (VLAN, Bandwidth, Session-Timeout, Filter-Id)
- Accounting attributes (Acct-*)
- EAP attributes (EAP-Message, State)

**2. Deliberate Practice:**  
The expert-level skill is reading raw RADIUS debug output and instantly knowing:
- Where in the protocol exchange you are
- Why a particular attribute matters
- What's wrong when something fails

Practice: Set up FreeRADIUS, capture debug output, and annotate every line.

**3. First Principles Thinking:**  
When RADIUS is confusing, return to fundamentals:
- Who is talking to whom? (User ↔ NAS ↔ RADIUS Server ↔ Backend)
- What question is being asked? (Authentication? Authorization? Accounting?)
- What cryptographic protection exists? (Shared secret? TLS?)

**4. The Expert's Question:**  
Ask yourself: "What would break if this attribute/step were missing?"
- No Message-Authenticator? → Can forge Access-Accept packets
- No Accounting-Interim? → Can't detect zombie sessions (user disconnected but not logged)
- No State attribute? → Can't do multi-round EAP
- No Proxy-State? → Proxy can't route responses back to correct NAS

**5. Pattern Recognition — The 5 RADIUS Patterns:**

```
Pattern 1: Simple PAP (lowest security, simplest flow)
  Request → Accept/Reject (2 messages)

Pattern 2: CHAP/MS-CHAP (challenge-response)
  Request → Accept/Reject (2 messages, different attributes)

Pattern 3: EAP Multi-Round (challenge-response with state)
  Request → Challenge → Request → Challenge → ... → Accept/Reject (N messages)

Pattern 4: Proxy Chain (multi-hop)
  NAS → Proxy1 → Proxy2 → HomeServer → Proxy2 → Proxy1 → NAS
  
Pattern 5: Dynamic Auth (CoA/Disconnect, server-initiated)
  Server → NAS (reversed direction)
  
Once you recognize which pattern you're in, the rest follows.
```

### Protocol Design Lessons from RADIUS

RADIUS teaches us profound lessons about protocol design:

1. **Simplicity has value**: RADIUS's simple request-response over UDP made it embeddable in tiny devices (1990s modem firmware). Complexity is the enemy of adoption.

2. **Extensibility matters**: VSA (Vendor-Specific Attributes) allowed RADIUS to grow for 30+ years without changing the core protocol. Design for extension.

3. **Security is retrofit-hard**: MD5 and UDP were fine in 1991. But retrofitting proper security (RadSec) took 20 years. Build security into the protocol from day one.

4. **Statelessness has costs**: RADIUS's UDP statelessness required the State attribute hack for multi-round EAP. DIAMETER's TCP solved this properly but added complexity.

5. **Centralization is a double-edged sword**: RADIUS centralizes auth decisions — great for management, but the RADIUS server becomes a single point of failure. Always deploy redundant RADIUS servers.

---

## Appendix A: RADIUS Attribute Quick Reference

```
MOST COMMONLY USED ATTRIBUTES IN PRACTICE
==========================================

For Access-Request (NAS → Server):
  User-Name (1)              "alice" or "alice@company.com"
  User-Password (2)          Encrypted password (PAP)
  CHAP-Password (3)          CHAP response
  NAS-IP-Address (4)         10.1.1.100
  NAS-Port (5)               Physical port number
  Called-Station-Id (30)     "AA:BB:CC:DD:EE:FF:SSID" (Wi-Fi)
  Calling-Station-Id (31)    "11:22:33:44:55:66" (client MAC)
  NAS-Port-Type (61)         19 (Wireless 802.11)
  EAP-Message (79)           EAP packet data
  Message-Authenticator (80) HMAC-MD5 of entire packet
  State (24)                 EAP session state cookie

For Access-Accept (Server → NAS):
  Tunnel-Type (64)           13 (VLAN)
  Tunnel-Medium-Type (65)    6 (IEEE-802)
  Tunnel-Private-Group-Id(81) "100" (VLAN number)
  Session-Timeout (27)       28800 (8 hours)
  Idle-Timeout (28)          1800 (30 min idle)
  Filter-Id (11)             "CORP-ACL" (apply ACL)
  Framed-IP-Address (8)      10.0.1.50 (assign IP)
  Reply-Message (18)         "Welcome to CorpWifi"
  EAP-Message (79)           EAP-Success packet
  Class (25)                 Session tracking cookie

For Accounting:
  Acct-Status-Type (40)      1=Start, 2=Stop, 3=Interim
  Acct-Session-Id (44)       "abc123xyz" (unique per session)
  Acct-Session-Time (46)     3600 (seconds online)
  Acct-Input-Octets (42)     5242880 (5 MB downloaded)
  Acct-Output-Octets (43)    1048576 (1 MB uploaded)
  Acct-Terminate-Cause (49)  1=User-Request, 4=Idle-Timeout
  Event-Timestamp (55)       Unix timestamp
```

---

## Appendix B: RADIUS Ports Reference

```
RADIUS PORT SUMMARY
====================

Authentication:
  UDP/1812    Standard (RFC 2865)
  UDP/1645    Legacy (original, still used by some vendors)

Accounting:
  UDP/1813    Standard (RFC 2866)  
  UDP/1646    Legacy (original)

RadSec (RADIUS over TLS):
  TCP/2083    Standard (RFC 6614)

Dynamic Authorization (CoA/Disconnect):
  UDP/3799    RFC 5176 (on the NAS, not server)

DIAMETER:
  TCP/3868    Standard (RFC 6733)
  SCTP/3868   Alternative transport
```

---

## Appendix C: Recommended Reading and Standards

```
ESSENTIAL READING FOR RADIUS MASTERY
======================================

Core RFCs (read in this order):
  1. RFC 2865 — Core RADIUS protocol (auth/authz)
  2. RFC 2866 — RADIUS Accounting
  3. RFC 3579 — RADIUS EAP support
  4. RFC 3580 — 802.1X RADIUS guidelines (Wi-Fi)
  5. RFC 5176 — Dynamic Authorization (CoA)
  6. RFC 6614 — RadSec (RADIUS over TLS)

EAP RFCs:
  RFC 3748 — EAP base spec
  RFC 5216 — EAP-TLS
  RFC 5281 — EAP-TTLS
  RFC 4186 — EAP-SIM
  RFC 7170 — EAP-TEAP (modern, superpowers)

Reference Implementation:
  FreeRADIUS source code: https://github.com/FreeRADIUS/freeradius-server
  (Read the module code — it's the best documentation)

Books:
  "RADIUS: Remote Authentication Dial-In User Service" by Jonathan Hassell
  "Network Security: Private Communication in a Public World"

Tools for Practice:
  freeradius       — RADIUS server
  radtest          — Simple CLI test client
  eapol_test       — EAP test client (from wpa_supplicant)
  wireshark        — Packet analysis (supports RADIUS decoding)
  tcpdump          — Packet capture
  radclient        — Advanced RADIUS test client
```

---

*This guide was written to be a complete, self-contained reference for mastering RADIUS. Every concept has been explained from first principles, with the goal of building a precise mental model that lets you reason about any RADIUS problem you encounter — whether debugging a failed 802.1X authentication, designing an enterprise network access policy, implementing a RADIUS server, or understanding the security properties of a given deployment.*

*The path to mastery: read, then implement (set up FreeRADIUS), then debug (break things intentionally), then optimize (add SQL, LDAP, RadSec). Each iteration deepens your mental model.*

Now I'll create the comprehensive RADIUS guide as a `.md` file.Here is your complete RADIUS guide. Here's what's covered across **22 sections**:

**Foundations**
The guide opens with the "castle gatekeeper" mental model, then walks through the full history (1991 → present), all key RFCs, and the AAA framework as the philosophical core of RADIUS.

**Protocol Mechanics (the deep parts)**
Every field of the 20-byte RADIUS header is dissected — including the subtle distinction between Request Authenticator (random nonce) and Response Authenticator (cryptographic proof). The User-Password XOR encryption algorithm is shown step by step. The TLV attribute format is fully annotated with an actual hex dump.

**Attributes**
A complete table of all core attributes with types and descriptions. VSA (Vendor-Specific Attributes) with the PEN system and real Cisco/Microsoft examples. The one-table quick reference in Appendix A covers what you'll use 90% of the time.

**Authentication Methods**
PAP, CHAP, MS-CHAPv2 (with the NT hash algorithm), and EAP — each with full flow diagrams, security ratings, and the exact cryptographic operations involved. EAP-TLS, PEAP, and EAP-TTLS each get their own complete flow.

**FreeRADIUS**
Real, production-ready configuration for `clients.conf`, `users`, `radiusd.conf`, the EAP module, the virtual server pipeline, SQL schema, and LDAP integration. Plus radtest and eapol_test usage.

**Advanced Topics**
CoA/Disconnect (the reversed flow), RADIUS proxy/realm routing, eduroam federation, DIAMETER comparison, RadSec, and a full security threat model with mitigations.

**Mental Models**
The guide closes with the cognitive scaffolding — chunking, deliberate practice paths, the 5 fundamental RADIUS patterns, and protocol design lessons extracted from RADIUS's 30-year history.