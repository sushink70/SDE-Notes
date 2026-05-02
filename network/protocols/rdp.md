# Remote Desktop Protocol (RDP) — Complete In-Depth Reference Guide

> **Scope**: This guide covers every layer of RDP — from ISO OSI mapping and raw PDU byte layouts
> to virtual channels, security subsystems, encoding pipelines, vulnerability anatomy, and
> implementation patterns. Nothing is omitted.

---

## Table of Contents

1. [History and Versioning](#1-history-and-versioning)
2. [Protocol Philosophy and Design Goals](#2-protocol-philosophy-and-design-goals)
3. [OSI Layer Mapping](#3-osi-layer-mapping)
4. [Protocol Stack Deep Dive](#4-protocol-stack-deep-dive)
   - 4.1 [ISO 8073 / X.224 Transport Layer](#41-iso-8073--x224-transport-layer)
   - 4.2 [T.125 MCS (Multipoint Communication Service)](#42-t125-mcs-multipoint-communication-service)
   - 4.3 [GCC (Generic Conference Control)](#43-gcc-generic-conference-control)
   - 4.4 [RDP Core Layer](#44-rdp-core-layer)
5. [Full Connection Sequence](#5-full-connection-sequence)
   - 5.1 [Phase 1 — TCP + TPKT + X.224 Handshake](#51-phase-1--tcp--tpkt--x224-handshake)
   - 5.2 [Phase 2 — MCS Connect + GCC Conference Create](#52-phase-2--mcs-connect--gcc-conference-create)
   - 5.3 [Phase 3 — Security Commencement](#53-phase-3--security-commencement)
   - 5.4 [Phase 4 — Capability Exchange](#54-phase-4--capability-exchange)
   - 5.5 [Phase 5 — Channel Join](#55-phase-5--channel-join)
   - 5.6 [Phase 6 — Licensing](#56-phase-6--licensing)
   - 5.7 [Phase 7 — Finalization](#57-phase-7--finalization)
   - 5.8 [Phase 8 — Active Data Transfer](#58-phase-8--active-data-transfer)
6. [PDU Structure and Framing](#6-pdu-structure-and-framing)
   - 6.1 [TPKT Header](#61-tpkt-header)
   - 6.2 [X.224 Data PDU](#62-x224-data-pdu)
   - 6.3 [MCS Send Data Request/Indication](#63-mcs-send-data-requestindication)
   - 6.4 [RDP Basic Security Header](#64-rdp-basic-security-header)
   - 6.5 [Share Control Header](#65-share-control-header)
   - 6.6 [Share Data Header](#66-share-data-header)
7. [Security Subsystems](#7-security-subsystems)
   - 7.1 [Classic RDP Security (RC4)](#71-classic-rdp-security-rc4)
   - 7.2 [Standard RDP Encryption Levels](#72-standard-rdp-encryption-levels)
   - 7.3 [TLS Security Mode](#73-tls-security-mode)
   - 7.4 [NLA — Network Level Authentication](#74-nla--network-level-authentication)
   - 7.5 [CredSSP Protocol (MS-CSSP)](#75-credssp-protocol-ms-cssp)
   - 7.6 [NTLM within CredSSP](#76-ntlm-within-credssp)
   - 7.7 [Kerberos within CredSSP](#77-kerberos-within-credssp)
   - 7.8 [RDP Certificate Validation](#78-rdp-certificate-validation)
8. [Capability Sets](#8-capability-sets)
9. [Graphics Pipeline](#9-graphics-pipeline)
   - 9.1 [GDI Orders (Drawing Orders)](#91-gdi-orders-drawing-orders)
   - 9.2 [Bitmap Caching](#92-bitmap-caching)
   - 9.3 [Bitmap Compression (RLE / RDP6 / RDP6.1)](#93-bitmap-compression-rle--rdp6--rdp61)
   - 9.4 [RemoteFX (RFX)](#94-remotefx-rfx)
   - 9.5 [H.264/AVC Codec (RDP 8+)](#95-h264avc-codec-rdp-8)
   - 9.6 [EGFX — Enhanced Graphics Channel (RDP 10)](#96-egfx--enhanced-graphics-channel-rdp-10)
   - 9.7 [Progressive Bitmap Compression](#97-progressive-bitmap-compression)
10. [Input Subsystem](#10-input-subsystem)
    - 10.1 [Keyboard Input PDU](#101-keyboard-input-pdu)
    - 10.2 [Mouse Input PDU](#102-mouse-input-pdu)
    - 10.3 [Unicode Keyboard Events](#103-unicode-keyboard-events)
    - 10.4 [Fast-Path Input](#104-fast-path-input)
11. [Virtual Channels](#11-virtual-channels)
    - 11.1 [Static Virtual Channels (SVC)](#111-static-virtual-channels-svc)
    - 11.2 [Dynamic Virtual Channels (DVC)](#112-dynamic-virtual-channels-dvc)
    - 11.3 [Channel Fragmentation and Reassembly](#113-channel-fragmentation-and-reassembly)
12. [Clipboard Redirection (CLIPRDR)](#12-clipboard-redirection-cliprdr)
13. [Drive Redirection (RDPDR)](#13-drive-redirection-rdpdr)
14. [Audio Redirection (RDPSND / AUDIO_PLAYBACK)](#14-audio-redirection-rdpsnd--audio_playback)
15. [Printer Redirection](#15-printer-redirection)
16. [Smart Card Redirection](#16-smart-card-redirection)
17. [USB Redirection (URBDRC)](#17-usb-redirection-urbdrc)
18. [RemoteApp (RAIL)](#18-remoteapp-rail)
19. [Multipoint / Multiparty (RDP Multipoint)](#19-multipoint--multiparty-rdp-multipoint)
20. [Multi-Monitor Support](#20-multi-monitor-support)
21. [Reconnection and Session Resume](#21-reconnection-and-session-resume)
22. [Performance Flags and Optimizations](#22-performance-flags-and-optimizations)
23. [Gateway Protocol (RDG / MS-TSGU)](#23-gateway-protocol-rdg--ms-tsgu)
24. [Load Balancing (MS-RDPBCGR Cookie)](#24-load-balancing-ms-rdpbcgr-cookie)
25. [RDP over UDP (MS-RDPEUDP)](#25-rdp-over-udp-ms-rdpeudp)
26. [Vulnerability Anatomy](#26-vulnerability-anatomy)
    - 26.1 [MS12-020 (DoS)](#261-ms12-020-dos)
    - 26.2 [MS15-067 and MS15-082](#262-ms15-067-and-ms15-082)
    - 26.3 [BlueKeep — CVE-2019-0708](#263-bluekeep--cve-2019-0708)
    - 26.4 [DejaBlue — CVE-2019-1181/1182](#264-dejablue--cve-2019-11811182)
    - 26.5 [PrintNightmare via RDP Printer Channel](#265-printnightmare-via-rdp-printer-channel)
27. [RDP Specification References (MS-RDPBCGR)](#27-rdp-specification-references-ms-rdpbcgr)
28. [Implementing an RDP Client — Architectural Decisions](#28-implementing-an-rdp-client--architectural-decisions)
29. [Implementing an RDP Server — Architectural Decisions](#29-implementing-an-rdp-server--architectural-decisions)
30. [Wireshark Dissection and Protocol Analysis](#30-wireshark-dissection-and-protocol-analysis)

---

## 1. History and Versioning

RDP was born from the ITU-T T.128 Application Sharing Protocol specification and Microsoft's
acquisition of Citrix's MultiWin technology in the mid-1990s. It is Microsoft's proprietary
extension of the T.120 protocol family.

```
Timeline:
─────────────────────────────────────────────────────────────────────────────────
 Year   Version   OS / Product                Key Addition
─────────────────────────────────────────────────────────────────────────────────
 1996   RDP 4.0   Windows NT 4.0 Terminal Srv Basic screen / keyboard / mouse
 1999   RDP 5.0   Windows 2000 Server         Printer/clipboard redirect, 24-bit
 2001   RDP 5.1   Windows XP                  ClearType, 32-bit color, NLA prereq
 2003   RDP 5.2   Windows Server 2003         Console sessions, Shadow
 2006   RDP 6.0   Vista / 2008                RemoteApp, Network Level Auth (NLA)
 2008   RDP 6.1   Windows 7 RTM               TS Easy Print, TS Gateway
 2009   RDP 7.0   Windows 7 SP1               RemoteFX (vGPU), multi-touch
 2010   RDP 7.1   Windows 7 SP1 update        Aero Glass over WAN
 2012   RDP 8.0   Windows 8 / 2012            H.264/AVC, UDP transport, EGFX
 2013   RDP 8.1   Windows 8.1 / 2012 R2       Reconnect perf, DX11 over RemoteFX
 2015   RDP 10.0  Windows 10 / 2016           H.264 full screen, AutoFit, 4K
 2016   RDP 10.1  Windows 10 1511             Pen/multitouch improvements
 2017   RDP 10.2  Windows 10 1703             H.264 chroma subsampling
 2018   RDP 10.3  Windows 10 1709             AVC444v2 codec
 2019   RDP 10.4  Windows 10 1803             Progressive codec
 2020   RDP 10.5  Windows 10 20H2             ARM64 client, GFX progressive v2
 2022   RDP 10.9  Windows 11 / 2022           Watermarking, QoS, QUIC explore
─────────────────────────────────────────────────────────────────────────────────
```

The version negotiated is the *minimum* of client and server capabilities. The actual RDP
version used in any session is determined during the GCC conference create phase via
`earlyCapabilityFlags` and the core capability set's `rdpVersion` field.

---

## 2. Protocol Philosophy and Design Goals

RDP was designed to solve a fundamentally hard problem: **efficiently transmit the visual state
of a remote computer to a thin client over a potentially lossy, low-bandwidth network**, while
feeding input back in the opposite direction.

### Design Constraints That Shaped Everything

| Constraint              | Design Choice                                                          |
|-------------------------|------------------------------------------------------------------------|
| Low bandwidth (ISDN/WAN)| GDI drawing orders instead of raw pixels                              |
| Heterogeneous clients   | Capability negotiation, graceful degradation                           |
| Shared hosting          | MCS multi-channel multiplexing per session                            |
| Security over wire      | Layered: RC4 → TLS → NLA (CredSSP)                                   |
| Peripheral access       | Virtual channel plugin architecture                                    |
| Reconnect tolerance     | Session persistence in Terminal Services                              |

### Core Abstractions

**Surface**: A rectangular region of pixels representing a remote display. A session may have
multiple surfaces (multi-monitor or RemoteApp windows).

**Order**: A GDI drawing command that instructs the client to render something (line, rectangle,
bitmap blit, glyph, polygon) without transmitting raw pixels.

**Channel**: A named logical byte-stream multiplexed over the single TCP connection.

**Capability Set**: A typed struct negotiated bidirectionally describing what features each
endpoint supports.

---

## 3. OSI Layer Mapping

```
OSI Model           RDP Stack
─────────────────────────────────────────────────────────────────────
Application (7)  ─► RDP Core: Graphics, Input, Virtual Channels
                    RemoteApp (RAIL), Clipboard (CLIPRDR),
                    Drive Redirect (RDPDR), Audio (RDPSND)
─────────────────────────────────────────────────────────────────────
Presentation (6) ─► T.125 MCS ASN.1 BER encoding / GCC
                    RDP Security (RC4 encryption / MAC)
─────────────────────────────────────────────────────────────────────
Session (5)      ─► X.224 / ISO 8073 Class 0 Transport Protocol
                    TPKT (RFC 1006) — TCP packetization
─────────────────────────────────────────────────────────────────────
Transport (4)    ─► TCP/3389  (primary)
                    UDP/3389  (MS-RDPEUDP, RDP 8.0+, optional)
─────────────────────────────────────────────────────────────────────
Network (3)      ─► IP (IPv4 / IPv6)
─────────────────────────────────────────────────────────────────────
Data Link (2)    ─► Ethernet / Wi-Fi / etc.
─────────────────────────────────────────────────────────────────────
Physical (1)     ─► Physical medium
─────────────────────────────────────────────────────────────────────
```

Note that when NLA (Network Level Authentication) is used, TLS wraps the TCP connection
**before** TPKT/X.224 — so the TLS handshake occurs at layer 4/5, and only then does the
TPKT/X.224 exchange begin inside the encrypted tunnel.

---

## 4. Protocol Stack Deep Dive

### 4.1 ISO 8073 / X.224 Transport Layer

X.224 (also called ISO 8073 Class 0, or COTP) provides the connection establishment primitive
over TCP. It defines:

- **CR-TPDU** (Connection Request): sent by client to server to request a transport connection.
- **CC-TPDU** (Connection Confirm): sent by server to accept.
- **DT-TPDU** (Data): carries all subsequent payload.

The X.224 CR/CC exchange is where **RDP protocol negotiation happens** (via the
`routingToken` or `cookie` field and the `rdpNegReq`/`rdpNegResp` structures).

```
X.224 CR PDU layout:
 ┌──────────────┬────────────┬──────────┬──────────────────────┬────────────────┐
 │ TPKT Header  │ LI (1 byte)│ CR (0xE0)│ DST-REF  SRC-REF    │ CLASS (0x00)   │
 │ (4 bytes)    │            │          │ (2B each)            │                │
 └──────────────┴────────────┴──────────┴──────────────────────┴────────────────┘
  followed by variable-length fields including:
  - RDP Negotiation Request (Type=0x01, Flags, Length=8, requestedProtocols)
  - Routing Cookie (for load balancing)
```

`requestedProtocols` is a 32-bit flags field:
```
Bit 0 (0x00000001) — PROTOCOL_SSL       : TLS 1.0+ security
Bit 1 (0x00000002) — PROTOCOL_HYBRID    : CredSSP (NLA)
Bit 2 (0x00000004) — PROTOCOL_RDSTLS    : RDSTLS (used in AAD scenarios)
Bit 3 (0x00000008) — PROTOCOL_HYBRID_EX : CredSSP with early user auth result
Bit 0 = 0 and no other bits — PROTOCOL_RDP : Classic RC4 security
```

### 4.2 T.125 MCS (Multipoint Communication Service)

MCS is the ITU-T T.125 standard for multipoint data conferencing. RDP repurposes it as a
**multi-channel multiplexer** within a single TCP connection. In RDP's use, multipoint is
always point-to-point (one client, one server), but the channel architecture is retained.

Key MCS primitives used by RDP:

```
MCS-Connect-Initial     → Client sends GCC Conference Create Request
MCS-Connect-Response    ← Server sends GCC Conference Create Response
MCS-ErectDomainRequest  → Client installs the domain
MCS-AttachUserRequest   → Client requests a user handle (User ID)
MCS-AttachUserConfirm   ← Server confirms, returns User ID
MCS-ChannelJoinRequest  → Client joins channel by Channel ID
MCS-ChannelJoinConfirm  ← Server confirms channel join
MCS-SendDataRequest     → Client sends data on a channel (to server)
MCS-SendDataIndication  ← Server sends data on a channel (to client)
MCS-DisconnectProviderUltimatum → Either side initiates disconnect
```

MCS uses **ASN.1 BER (Basic Encoding Rules)** for encoding. Each PDU has a type tag,
length, and value.

**MCS Channel IDs** (predefined):
```
0x03EA (1002) — I/O channel (main RDP channel: graphics, input, licensing)
0x03EB (1003) — First static virtual channel
0x03EC (1004) — Second static virtual channel
...
0x03FF (1023) — Maximum static virtual channel ID
```

The client's **User Channel ID** is dynamically assigned by the server during
`MCS-AttachUserConfirm`. All data from the client rides on `MCS-SendDataRequest` with
the initiator set to the User Channel ID.

### 4.3 GCC (Generic Conference Control)

GCC (T.124) manages the conference (session) creation. Inside the MCS-Connect-Initial PDU,
RDP embeds a **GCC Conference Create Request** (ASN.1 PER encoded). Inside that, RDP
further embeds its own proprietary data structures in the `userData` field.

The GCC userData contains:
- **CS_CORE** — Client Core Data (version, desktop dimensions, color depth, etc.)
- **CS_SECURITY** — Client Security Data (encryption methods supported)
- **CS_NET** — Client Network Data (list of requested virtual channels by name)
- **CS_CLUSTER** — Client Cluster Data (console session, redirection info)
- **CS_MONITOR** — Client Monitor Data (multi-monitor configuration)
- **CS_MCS_MSGCHANNEL** — Message channel support
- **CS_MULTITRANSPORT** — UDP multitransport support

The server responds with a **GCC Conference Create Response** containing:
- **SC_CORE** — Server Core Data (server RDP version, requested protocol)
- **SC_SECURITY** — Server Security Data (chosen encryption, server certificate)
- **SC_NET** — Server Network Data (confirmed virtual channel IDs)
- **SC_MULTITRANSPORT** — Server UDP multitransport flags

### 4.4 RDP Core Layer

Above MCS sits the RDP core, responsible for:
- Sending and receiving **Share Control PDUs** (the top-level RDP PDU wrapper)
- Multiplexing different PDU types: demand-active, confirm-active, data, deactivate-all
- Managing the **Share ID** — a 32-bit identifier for the session's share (the virtual
  desktop being shared)

The RDP data path for a typical graphics update:

```
Server                                          Client
  │                                               │
  │── [TCP] [TPKT] [X.224 DT] ─────────────────► │
  │        [MCS SendDataIndication]               │
  │           Channel: I/O (1002)                 │
  │           [RDP Security Header (optional)]    │
  │              [Share Control Header]           │
  │                 [Share Data Header]           │
  │                    [Fast-Path Update PDU]     │
  │                       [Bitmap Update]         │
  │                          [Bitmap Data]        │
  │                                               │
```

---

## 5. Full Connection Sequence

The RDP connection is a multi-phase process. Each phase must complete before the next begins.
Understanding this sequence is essential for implementing RDP clients/servers or debugging
with Wireshark.

```
CLIENT                                               SERVER
  │                                                    │
  │──────── TCP SYN ──────────────────────────────────►│
  │◄─────── TCP SYN-ACK ──────────────────────────────│
  │──────── TCP ACK ──────────────────────────────────►│
  │                                                    │
  │═══════════════════ PHASE 1: X.224 ════════════════│
  │──── X.224 CR (Connection Request) ───────────────►│
  │     [RDP Negotiation Request: requestedProtocols] │
  │                                                    │
  │◄─── X.224 CC (Connection Confirm) ────────────────│
  │     [RDP Negotiation Response: selectedProtocol]  │
  │                                                    │
  │═════ If NLA selected: TLS Handshake + CredSSP ════│
  │──── ClientHello (TLS) ────────────────────────────►│
  │◄─── ServerHello + Certificate ────────────────────│
  │         (TLS completes)                            │
  │──── CredSSP negoToken (NTLM NEGOTIATE) ──────────►│
  │◄─── CredSSP negoToken (NTLM CHALLENGE) ───────────│
  │──── CredSSP negoToken (NTLM AUTHENTICATE) ───────►│
  │──── CredSSP pubKeyAuth ───────────────────────────►│
  │◄─── CredSSP pubKeyAuth confirmed ─────────────────│
  │──── CredSSP credentials (encrypted) ─────────────►│
  │                                                    │
  │═══════════════════ PHASE 2: MCS/GCC ══════════════│
  │──── MCS Connect-Initial ─────────────────────────►│
  │     [GCC Conference Create Request]                │
  │        [CS_CORE, CS_SECURITY, CS_NET, ...]        │
  │                                                    │
  │◄─── MCS Connect-Response ─────────────────────────│
  │     [GCC Conference Create Response]              │
  │        [SC_CORE, SC_SECURITY, SC_NET, ...]        │
  │                                                    │
  │──── MCS Erect Domain Request ────────────────────►│
  │──── MCS Attach User Request ─────────────────────►│
  │◄─── MCS Attach User Confirm [User ID] ────────────│
  │                                                    │
  │═══════════════════ PHASE 3: Channel Join ══════════│
  │──── MCS Channel Join Request (User Channel) ─────►│
  │◄─── MCS Channel Join Confirm ─────────────────────│
  │──── MCS Channel Join Request (I/O Channel 1002) ─►│
  │◄─── MCS Channel Join Confirm ─────────────────────│
  │  (repeat for each virtual channel)                │
  │──── MCS Channel Join Request (SVC channel N) ────►│
  │◄─── MCS Channel Join Confirm ─────────────────────│
  │                                                    │
  │═══════════════════ PHASE 4: Security ═════════════│
  │  (if RDP Security mode, not NLA)                  │
  │──── Security Exchange PDU ───────────────────────►│
  │     [client_random encrypted with server pub key] │
  │                                                    │
  │═══════════════════ PHASE 5: Licensing ════════════│
  │◄─── License Request ──────────────────────────────│
  │──── New License Request ─────────────────────────►│
  │◄─── Platform Challenge ───────────────────────────│
  │──── Platform Challenge Response ─────────────────►│
  │◄─── License Error (STATUS_VALID_CLIENT) ──────────│
  │     (or New License, Upgrade License)             │
  │                                                    │
  │═══════════════════ PHASE 6: Capabilities ══════════│
  │◄─── Demand Active PDU ────────────────────────────│
  │     [Server Capability Sets]                      │
  │     [Session ID, Share ID]                        │
  │                                                    │
  │──── Confirm Active PDU ──────────────────────────►│
  │     [Client Capability Sets]                      │
  │                                                    │
  │═══════════════════ PHASE 7: Finalization ══════════│
  │──── Synchronize PDU ─────────────────────────────►│
  │──── Control PDU (Cooperate) ─────────────────────►│
  │──── Control PDU (Request Control) ───────────────►│
  │──── Font List PDU ───────────────────────────────►│
  │                                                    │
  │◄─── Synchronize PDU ──────────────────────────────│
  │◄─── Control PDU (Cooperate) ──────────────────────│
  │◄─── Control PDU (Granted Control) ───────────────│
  │◄─── Font Map PDU ─────────────────────────────────│
  │                                                    │
  │═══════════════════ PHASE 8: Active Session ════════│
  │◄─── Graphics Updates (Bitmap, Orders, ...) ───────│
  │──── Input Events (Keyboard, Mouse) ──────────────►│
  │◄═══► Virtual Channel Data (CLIPRDR, RDPDR, ...) ══│
```

### 5.1 Phase 1 — TCP + TPKT + X.224 Handshake

The client sends an X.224 CR-TPDU containing an `rdpNegReq` structure:

```
Offset  Size  Field
──────────────────────────────────────────────────────
0       1     type = 0x01 (TYPE_RDP_NEG_REQ)
1       1     flags (usually 0x00 or 0x08 for correlation)
2       2     length = 0x0008
4       4     requestedProtocols (bitmask)
──────────────────────────────────────────────────────
```

The server's CC-TPDU contains an `rdpNegResp` or `rdpNegFailure`:

```
rdpNegResp:
Offset  Size  Field
──────────────────────────────────────────────────────
0       1     type = 0x02 (TYPE_RDP_NEG_RSP)
1       1     flags (EXTENDED_CLIENT_DATA_SUPPORTED=0x01,
                     DYNVC_GFX_PROTOCOL_SUPPORTED=0x02,
                     NEGRSP_FLAG_RESERVED=0x04,
                     RESTRICTED_ADMIN_MODE_SUPPORTED=0x08)
2       2     length = 0x0008
4       4     selectedProtocol (one of the requested values)
──────────────────────────────────────────────────────
```

### 5.2 Phase 2 — MCS Connect + GCC Conference Create

The MCS Connect-Initial PDU is an ASN.1 BER encoded structure:

```
MCS-Connect-Initial ::= [APPLICATION 101] IMPLICIT SEQUENCE {
    callingDomainSelector  OCTET STRING,        -- "\x01"
    calledDomainSelector   OCTET STRING,        -- "\x01"
    upwardFlag             BOOLEAN,             -- TRUE
    targetParameters       DomainParameters,
    minimumParameters      DomainParameters,
    maximumParameters      DomainParameters,
    userData               OCTET STRING         -- GCC Conference Create Request
}
```

Inside `userData` lives the GCC Conference Create Request (T.124 PER encoded), and within
*that* is a sequence of RDP data blocks (CS_CORE, CS_SECURITY, CS_NET, etc.).

**CS_CORE** (Client Core Data):
```
Field                   Size  Description
─────────────────────────────────────────────────────────────────────────
version                 4     RDP version: 0x00080004 = RDP5, 0x00080008 = RDP8+
desktopWidth            2     Requested width (e.g., 1920)
desktopHeight           2     Requested height (e.g., 1080)
colorDepth              2     0xCA00=4bpp, 0xCA01=8bpp, 0xCA02=15bpp,
                              0xCA03=16bpp, 0xCA04=24bpp (legacy)
SASSequence             2     0xAA03 (Del key in SASequence)
keyboardLayout          4     Windows LCID (e.g., 0x0409 = en-US)
clientBuild             4     Build number of client OS
clientName              32    Unicode string (null-padded)
keyboardType            4     IBM PC/AT=4, etc.
keyboardSubType         4
keyboardFunctionKey     4     Number of function keys
imeFileName             64    Unicode IME filename
postBeta2ColorDepth     2     0xCA00=4bpp, 0xCAFE=8bpp+
clientProductId         2     0x0001
serialNumber            4     0
highColorDepth          2     4=24bpp, 8=32bpp
supportedColorDepths    2     Bitmask: RNS_UD_24BPP_SUPPORT=0x0001,
                              RNS_UD_16BPP_SUPPORT=0x0002,
                              RNS_UD_15BPP_SUPPORT=0x0004,
                              RNS_UD_32BPP_SUPPORT=0x0008
earlyCapabilityFlags    2     Flags for 5.2+ features
clientDigProductId      64    Digital product ID (Unicode)
connectionType          1     0=modem,1=low,2=satellite,3=cable,4=LAN,5=auto,6=detect
pad1octet               1
serverSelectedProtocol  4     Must match X.224 selectedProtocol
desktopPhysicalWidth    4     Physical width in mm
desktopPhysicalHeight   4     Physical height in mm
desktopOrientation      2     0,90,180,270 degrees
desktopScaleFactor      4     100-500 (percent)
deviceScaleFactor       4     100,140,180
─────────────────────────────────────────────────────────────────────────
```

### 5.3 Phase 3 — Security Commencement

**For RDP Security (Classic):**

After X.224 and MCS, if classic RDP security was selected, the client sends a
**Security Exchange PDU**:
```
Field                   Size  Description
─────────────────────────────────────────────────────────────────────────
length                  4     Length of encryptedClientRandom
encryptedClientRandom   ≤512  client_random[32] RSA-encrypted with
                              server's public key (from SC_SECURITY)
─────────────────────────────────────────────────────────────────────────
```

The session keys are then derived from:
```
client_random XOR server_random → pre_master_secret
SaltedHash("A",  pre_master_secret) → session_key_blob[0..47]
SaltedHash("BB", pre_master_secret) → session_key_blob[16..79]
SaltedHash("CCC",pre_master_secret) → session_key_blob[32..95]
```

Then from these blobs, the actual RC4 encrypt/decrypt keys and MAC key are derived.

**For NLA/TLS:**
The CredSSP exchange occurs inside the TLS tunnel before any TPKT/MCS traffic.
No separate Security Exchange PDU is needed because NLA handles both authentication
and key agreement.

### 5.4 Phase 4 — Capability Exchange

The **Demand Active PDU** from the server announces server capabilities:
```
PDU Type: PDUTYPE_DEMANDACTIVEPDU (0x1)
Share Control Header → Share ID
sourceDescriptor: "RDP" (server name)
numberCapabilities: count
capabilitySets: array of typed capability sets
sessionId: 32-bit session identifier
```

The client responds with a **Confirm Active PDU** containing its own capability sets.

Mismatches are handled gracefully — both sides use the minimum of what was offered and
what was confirmed.

### 5.5 Phase 5 — Channel Join

After MCS domain erection and user attachment, the client must join each channel:
- User Channel (its own User ID)
- I/O Channel (1002) — mandatory
- Each SVC channel (1003, 1004, ...) allocated during CS_NET negotiation

### 5.6 Phase 6 — Licensing

RDP licensing is a Terminal Services mechanism for client access licenses (CALs).
For modern Windows clients with valid Windows licenses, the server typically sends
a `LICENSE_ERROR_VALID_CLIENT` message immediately (effectively skipping licensing).

The licensing protocol uses RSA and RC4 internally:
```
Server: LICENSE_REQUEST
  └── ServerRandom (32 bytes)
  └── ProductInfo (company name, product ID, version)
  └── KeyExchangeList (algorithm list, usually KEY_EXCHANGE_ALG_RSA)
  └── ServerCertificate (proprietary or X.509)
  └── ScopeList

Client: NEW_LICENSE_REQUEST or LICENSE_INFO
  └── PreferredKeyExchangeAlg
  └── PlatformId
  └── ClientRandom (32 bytes)
  └── EncryptedPreMasterSecret (RSA encrypted with server cert public key)
  └── ClientUserName
  └── ClientMachineName

Server: PLATFORM_CHALLENGE
  └── ConnectFlags
  └── EncryptedPlatformChallenge (RC4 encrypted)

Client: PLATFORM_CHALLENGE_RESPONSE
  └── EncryptedPlatformChallengeResponse
  └── EncryptedHWID (hardware ID, RC4 encrypted)
  └── MACData (HMAC-MD5 over the challenge response)

Server: NEW_LICENSE | UPGRADE_LICENSE | ERROR_ALERT (STATUS_VALID_CLIENT)
```

### 5.7 Phase 7 — Finalization

The finalization phase synchronizes the client and server state before data begins:

```
Client → Server: Synchronize PDU         (confirms client is ready)
Client → Server: Control PDU (Cooperate) (enters cooperative mode)
Client → Server: Control PDU (Request)   (requests keyboard/mouse control)
Client → Server: Font List PDU           (announces available font cache)

Server → Client: Synchronize PDU
Server → Client: Control PDU (Cooperate)
Server → Client: Control PDU (Granted)   (grants control to client)
Server → Client: Font Map PDU            (maps font IDs to glyph cache entries)
```

After the server sends Font Map, the session enters **Active State**.

### 5.8 Phase 8 — Active Data Transfer

In the active state, the server continuously sends graphics updates and the client sends
input events. Both sides may send virtual channel data at any time.

---

## 6. PDU Structure and Framing

Every byte transmitted over TCP in an RDP connection is wrapped in multiple layers of headers.
Understanding this nesting is critical for parsing or implementing RDP.

### 6.1 TPKT Header

RFC 1006 defines TPKT as a simple TCP packetization layer:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌─────────────────┬─────────────────┬─────────────────────────────┐
│    version=3    │    reserved=0   │           length            │
│    (1 byte)     │    (1 byte)     │          (2 bytes BE)       │
└─────────────────┴─────────────────┴─────────────────────────────┘
```
- `version`: always 3 for TPKT
- `reserved`: always 0
- `length`: total length including the 4-byte TPKT header itself (big-endian)

**Maximum TPKT payload**: 65531 bytes (65535 - 4). Large RDP PDUs are fragmented at
MCS level and reassembled.

### 6.2 X.224 Data PDU

```
 0                   1                   2
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3
┌─────────────────┬─────────────────┬─────────────┐
│      LI=2       │  type=0xF0 (DT) │  EOT=0x80   │
│    (1 byte)     │    (1 byte)     │  (1 byte)   │
└─────────────────┴─────────────────┴─────────────┘
```
- `LI`: Length Indicator (number of bytes in X.224 header, not counting LI itself = 2)
- `type`: 0xF0 = DT-TPDU (data)
- `EOT`: 0x80 means End of TSDU (last fragment), 0x00 means more follows

### 6.3 MCS Send Data Request/Indication

After X.224, the MCS layer header. BER-encoded, but effectively a fixed-size structure for
SendData:

```
 0         1         2         3         4         5         6         7
┌─────────────────────────────────────────────────────────────────────────┐
│ BER Tag  │     initiator (MCS user ID, 2 bytes)                         │
│ 0x64/0x65│     channelId (2 bytes, e.g., 0x03EA for I/O channel)        │
│          │     dataPriority+segmentation (1 byte)                       │
│          │     userData length (BER encoded, 1 or 3 bytes)              │
│          │     ... payload ...                                           │
└─────────────────────────────────────────────────────────────────────────┘
```
- Tag `0x64` = SendDataRequest (client to server)
- Tag `0x65` = SendDataIndication (server to client)

`dataPriority` (upper 2 bits): 0=high, 1=medium, 2=low, 3=lowest
`segmentation` (lower 2 bits): 0x00=not fragmented, 0x01=first, 0x10=last, 0x11=middle

### 6.4 RDP Basic Security Header

When RDP Security (classic, RC4) is active, every PDU on the I/O channel is prefixed:

```
Field           Size  Description
─────────────────────────────────────────────────────
flags           2     Security flags bitmask
flagsHi         2     Reserved (0)
[dataSignature] 8     Present if SEC_ENCRYPT|SEC_IGNORE_SEQNO
                      HMAC-MD5 MAC over plaintext + seq_num
[encryptedData] var   RC4 ciphertext (rest of PDU)
─────────────────────────────────────────────────────
```

Security flag bits:
```
SEC_EXCHANGE_PKT     0x0001  Security Exchange PDU
SEC_TRANSPORT_REQ    0x0002  Transport layer request (unused)
SEC_ENCRYPT          0x0008  PDU is encrypted
SEC_RESET_SEQNO      0x0010  Reset sequence number
SEC_IGNORE_SEQNO     0x0020  Ignore sequence number
SEC_INFO_PKT         0x0040  Info PDU (user credentials)
SEC_LICENSE_PKT      0x0080  Licensing PDU
SEC_LICENSE_ENCRYPT_CS 0x0200 Encrypted licensing (client→server)
SEC_LICENSE_ENCRYPT_SC 0x0200 Encrypted licensing (server→client)
SEC_REDIRECTION_PKT  0x0400  Auto-reconnect PDU
SEC_SECURE_CHECKSUM  0x0800  Use salted MAC
SEC_AUTODETECT_REQ   0x1000  Bandwidth auto-detection request
SEC_AUTODETECT_RSP   0x2000  Bandwidth auto-detection response
SEC_HEARTBEAT        0x4000  Heartbeat PDU
SEC_FLAGSHI_VALID    0x8000  flagsHi field is valid
```

When TLS/NLA is used, there is **no** RDP Security header — TLS provides confidentiality.
However, there **is** still a 4-byte security header with `flags=0` for some PDU types.

### 6.5 Share Control Header

The first RDP-level header inside the decrypted payload:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌───────────────────────────────┬───────────────────────────────┐
│         totalLength           │            pduType            │
│         (2 bytes LE)          │         (2 bytes LE)          │
├───────────────────────────────┴───────────────────────────────┤
│                          PDUSource                            │
│                       (2 bytes LE) (= MCS user channel ID)   │
└───────────────────────────────────────────────────────────────┘
```

`pduType` lower 4 bits = PDU type:
```
0x1  PDUTYPE_DEMANDACTIVEPDU
0x3  PDUTYPE_CONFIRMACTIVEPDU
0x6  PDUTYPE_DEACTIVATEALLPDU
0x7  PDUTYPE_DATAPDU
0xA  PDUTYPE_SERVER_REDIR_PKT
```

Upper 12 bits of `pduType` contain version info (always 0x0010 for RDP 5.0+).

### 6.6 Share Data Header

For `PDUTYPE_DATAPDU`, the Share Control Header is followed by a Share Data Header:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌───────────────────────────────────────────────────────────────┐
│                           shareId                             │
│                         (4 bytes LE)                         │
├───────────────┬───────────────┬───────────────────────────────┤
│    pad1octet  │  streamId     │        uncompressedLength     │
│    (1 byte)   │  (1 byte)     │          (2 bytes LE)        │
├───────────────┬───────────────┴───────────────────────────────┤
│    pduType2   │  generalCompressedType  │generalCompressedLen │
│    (1 byte)   │  (1 byte)               │  (2 bytes LE)      │
└───────────────┴─────────────────────────┴────────────────────┘
```

`streamId`:
```
STREAM_UNDEFINED  0x00
STREAM_LOW        0x01  (background data)
STREAM_MED        0x02  (normal priority)
STREAM_HI         0x04  (interactive: input echo, UI)
```

`pduType2` — the actual RDP data PDU type:
```
0x02  PDUTYPE2_UPDATE                (graphics update)
0x14  PDUTYPE2_CONTROL               (control messages)
0x1B  PDUTYPE2_POINTER               (cursor update)
0x1C  PDUTYPE2_INPUT                 (input event)
0x1D  PDUTYPE2_SYNCHRONIZE           (sync)
0x22  PDUTYPE2_REFRESH_RECT          (request redraw)
0x28  PDUTYPE2_PLAY_SOUND            (system beep)
0x29  PDUTYPE2_SUPPRESS_OUTPUT       (minimize/restore)
0x2C  PDUTYPE2_SHUTDOWN_REQUEST      (logoff request)
0x2D  PDUTYPE2_SHUTDOWN_DENIED       (logoff denied)
0x2E  PDUTYPE2_SAVE_SESSION_INFO     (logon info/redirect)
0x2F  PDUTYPE2_FONTLIST              (font list)
0x30  PDUTYPE2_FONTMAP               (font map)
0x31  PDUTYPE2_SET_KEYBOARD_INDICATORS (caps/num/scroll lock LEDs)
0x35  PDUTYPE2_BITMAPCACHE_PERSISTENT_LIST
0x36  PDUTYPE2_BITMAPCACHE_ERROR_PDU
0x37  PDUTYPE2_SET_KEYBOARD_IME_STATUS
0x38  PDUTYPE2_OFFSCR_CACHE_ERROR_PDU
0x39  PDUTYPE2_SET_ERROR_INFO_PDU    (error notification)
0x3A  PDUTYPE2_DRAWNINEGRID_ERROR_PDU
0x3B  PDUTYPE2_DRAWGDIPLUS_ERROR_PDU
0x3C  PDUTYPE2_ARC_STATUS_PDU
0x3F  PDUTYPE2_STATUS_INFO_PDU
0x40  PDUTYPE2_MONITOR_LAYOUT_PDU
```

---

## 7. Security Subsystems

### 7.1 Classic RDP Security (RC4)

Classic RDP security uses RSA key exchange and RC4 stream cipher. It was the **only** option
in RDP 4.x–5.x.

**Key Generation:**
```
1. Server generates 512-bit or 2048-bit RSA key pair
2. Server sends public key in SC_SECURITY (server certificate)
3. Client generates 32-byte client_random
4. Client encrypts client_random with server public key → sends in Security Exchange PDU
5. Server decrypts → obtains client_random
6. Both sides know: client_random, server_random (from SC_SECURITY)

Pre-master secret = client_random XOR server_random

master_secret = SaltedHash(pre_master_secret, "A",  client_random, server_random)
             + SaltedHash(pre_master_secret, "BB", client_random, server_random)
             + SaltedHash(pre_master_secret, "CCC",client_random, server_random)
              (48 bytes total)

SaltedHash(secret, salt, r1, r2):
  SHA1(secret + salt + r1 + r2)  → SHA1_result
  MD5(secret + SHA1_result)      → 16-byte result

session_key_blob = SaltedHash(master_secret, "X",  client_random, server_random) +
                   SaltedHash(master_secret, "YY", client_random, server_random) +
                   SaltedHash(master_secret, "ZZZ",client_random, server_random)

MAC_key          = session_key_blob[0..15]       (16 bytes)
initial_decrypt  = session_key_blob[16..31]      (16 bytes, server→client)
initial_encrypt  = session_key_blob[32..47]      (16 bytes, client→server)

For 128-bit encryption:
encrypt_key = FIPS186_PRF(initial_encrypt, client_random, server_random)[0..15]
decrypt_key = FIPS186_PRF(initial_decrypt, client_random, server_random)[0..15]
```

**RC4 Session Key Update** (after every 4096 encrypted packets):
```
temp = MD5(current_key + PAD1 + original_key)
new  = RC4(MD5(temp + PAD2 + original_key), 16) [using temp as key]
```
PAD1 = 0x36 * 40, PAD2 = 0x5C * 48

**MAC computation** (for each packet):
```
MAC = first 8 bytes of:
  MD5( MAC_key + PAD2 + MD5(MAC_key + PAD1 + length[4LE] + data) )
```

**Critical weakness**: RC4 with the above key schedule is vulnerable to cryptanalytic
attacks. Microsoft's proprietary MAC scheme is not HMAC. This is why NLA/TLS replaced it.

### 7.2 Standard RDP Encryption Levels

Configured in server Group Policy:
```
Level 0: ENCRYPTION_LEVEL_NONE     (0x00000000) — no encryption
Level 1: ENCRYPTION_LEVEL_LOW      (0x00000001) — client→server only
Level 2: ENCRYPTION_LEVEL_CLIENT_COMPATIBLE (0x00000002) — 56-bit RC4
Level 3: ENCRYPTION_LEVEL_HIGH     (0x00000003) — 128-bit RC4
Level 4: ENCRYPTION_LEVEL_FIPS     (0x00000004) — FIPS 140-1 (3DES + SHA1 MAC)
```

### 7.3 TLS Security Mode

When `PROTOCOL_SSL` is negotiated, after the X.224 exchange:
1. A TLS handshake occurs directly on the TCP stream
2. All subsequent TPKT/MCS/RDP traffic is inside the TLS tunnel
3. No RDP Security header encryption is used (flags=0)
4. Authentication is only via TLS certificate — **no user authentication at the network
   level** (user authenticates inside the session, in the Windows login screen)

TLS 1.2+ is required on modern Windows. The server certificate is either:
- Self-signed (default) → client should warn on first connect
- CA-signed enterprise certificate (via Group Policy / AD CS)

**Server authentication gap**: In TLS mode without NLA, an attacker can perform a
MITM attack during the TLS handshake since most RDP clients blindly accept self-signed
certificates (they prompt but users typically accept).

### 7.4 NLA — Network Level Authentication

NLA (introduced in RDP 6.0) authenticates the **user before** the remote desktop session
is established. This means:

- No Windows logon screen is exposed to unauthenticated connections
- Reduces attack surface (BlueKeep pre-auth vuln only affects non-NLA)
- More efficient: server resources not consumed until auth succeeds

NLA wraps TLS + CredSSP. The flow:
```
X.224 negotiation selects PROTOCOL_HYBRID (CredSSP)
→ TLS handshake on raw TCP
→ CredSSP exchange inside TLS
→ User credentials passed to server
→ Server authenticates via Windows auth subsystem (NTLM or Kerberos)
→ If auth succeeds: normal RDP connection continues (MCS/GCC phase)
→ If auth fails: connection is dropped before any session is created
```

### 7.5 CredSSP Protocol (MS-CSSP)

CredSSP (Credential Security Support Provider) is Microsoft's extension for delegating
credentials over a TLS-protected channel. It uses ASN.1 DER encoding.

```
TSRequest ::= SEQUENCE {
    version        [0] INTEGER,       -- 2, 3, 4, 5, or 6
    negoTokens     [1] NegoData OPTIONAL,  -- SPNEGO token (NTLM or Kerberos)
    authInfo       [2] OCTET STRING OPTIONAL,  -- encrypted credentials
    pubKeyAuth     [3] OCTET STRING OPTIONAL,  -- public key binding
    errorCode      [4] INTEGER OPTIONAL,
    clientNonce    [5] OCTET STRING OPTIONAL   -- random nonce (v5+)
}
```

CredSSP exchange (simplified):
```
Round 1 (Client→Server): TSRequest{negoTokens: NTLM-NEGOTIATE or Kerberos AP-REQ}
Round 2 (Server→Client): TSRequest{negoTokens: NTLM-CHALLENGE or Kerberos AP-REP}
Round 3 (Client→Server): TSRequest{negoTokens: NTLM-AUTH, pubKeyAuth: encrypt(pubkey)}
Round 4 (Server→Client): TSRequest{pubKeyAuth: encrypt(pubkey+1)} (server echo)
Round 5 (Client→Server): TSRequest{authInfo: encrypt(TSCredentials)}
```

`TSCredentials` contains either:
- `TSPasswordCreds` (domain + username + password) for password-based auth
- `TSSmartCardCreds` for smart card auth
- `TSRemoteGuardCreds` for Remote Guard (credentials not sent, used locally)

### 7.6 NTLM within CredSSP

NTLM (NT LAN Manager) is the default fallback when Kerberos is unavailable.

```
NTLM NEGOTIATE message (Type 1):
  Signature: "NTLMSSP\0"
  MessageType: 0x00000001
  NegotiateFlags: (bitmask of requested features)
  DomainNameFields, WorkstationFields, Version

NTLM CHALLENGE message (Type 2):
  Signature: "NTLMSSP\0"
  MessageType: 0x00000002
  TargetNameFields
  NegotiateFlags
  ServerChallenge: 8 bytes random
  TargetInfoFields → (pairs of Type/Value: NetBIOS domain, DNS domain, etc.)

NTLM AUTHENTICATE message (Type 3):
  Signature: "NTLMSSP\0"
  MessageType: 0x00000003
  LmChallengeResponseFields → LMv2 response (24 bytes)
  NtChallengeResponseFields → NTLMv2 response (variable)
  DomainNameFields, UserNameFields, WorkstationFields
  EncryptedRandomSessionKeyFields
  NegotiateFlags
  MIC: 16-byte message integrity code

NTLMv2 response computation:
  NTHash = MD4(UTF16-LE(password))
  NTLMv2_key = HMAC-MD5(NTHash, UTF16-LE(uppercase(user) + domain))
  blob = timestamp + client_challenge + target_info
  NTProofStr = HMAC-MD5(NTLMv2_key, server_challenge + blob)
  NTLMv2_response = NTProofStr + blob
```

### 7.7 Kerberos within CredSSP

When the client is domain-joined and can reach a KDC (Key Distribution Center):

```
Client obtains a Kerberos Service Ticket for:
  SPN = TERMSRV/<server-fqdn>

AP-REQ is embedded in the SPNEGO token in TSRequest.negoTokens.

Server validates the ticket with its keytab / AD account secrets.

Mutual authentication is achieved via AP-REP.

Extended protection: Channel binding token (CBT) binds the Kerberos session
to the TLS channel via the TLS server's public key hash (outer TLS cert hash).
```

### 7.8 RDP Certificate Validation

When TLS is used (SSL or NLA mode), the server presents an X.509 certificate. The certificate
can be:

1. **Self-signed** (default): Generated on first RDP service start, stored in
   `HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server\RDPCertificate`
2. **AD-enrolled**: Pushed via GPO using "Remote Desktop Session Host Certificate Template"
3. **Custom**: Manually assigned in RDP-TCP properties

Certificate pinning behavior of mstsc.exe:
- On first connection: warns user if cert is untrusted
- On subsequent connections: warns if cert hash changes
- Hash stored per server in: `HKCU\Software\Microsoft\Terminal Server Client\Servers\<host>`

Certificate contains the **RDP Server identifier** (SubjectAltName or CN), and the
CredSSP `pubKeyAuth` field binds credential delegation specifically to this certificate's
public key — preventing credential relay attacks to a different server.

---

## 8. Capability Sets

Capability sets are exchanged in Demand Active / Confirm Active PDUs. Each has a 4-byte
header: `capabilitySetType` (2 bytes) + `lengthCapability` (2 bytes), followed by type-
specific data.

```
Capability Set Types:
──────────────────────────────────────────────────────────────────
Type  Name                        Key Fields
──────────────────────────────────────────────────────────────────
0x01  CAPSTYPE_GENERAL            osMajorType, osMinorType,
                                  extraFlags (fastpath, salted MAC,
                                  long credentials, auto reconnect,
                                  server reactivate, net char detect)
0x02  CAPSTYPE_BITMAP             preferredBitsPerPixel, desktopWidth,
                                  desktopHeight, desktopResizeFlag,
                                  bitmapCompressionFlag, drawingFlags
0x03  CAPSTYPE_ORDER              desktopSaveSize, orderFlags,
                                  orderSupport[32] (bitmask of GDI orders)
0x04  CAPSTYPE_BITMAPCACHE        (RDP4 cache caps, deprecated)
0x07  CAPSTYPE_CONTROL            controlFlags, remoteDetachFlag
0x08  CAPSTYPE_WINDOWACTIVATION   helpKeyFlag, helpKeyIndexFlag,
                                  helpExtendedKeyFlag, windowManagerKeyFlag
0x09  CAPSTYPE_POINTER            colorPointerFlag, colorPointerCacheSize,
                                  pointerCacheSize
0x0A  CAPSTYPE_SHARE              nodeId, pad2octets
0x0B  CAPSTYPE_COLORCACHE         colorTableCacheSize
0x0D  CAPSTYPE_SOUND              soundFlags (beeps)
0x0E  CAPSTYPE_INPUT              inputFlags (scancodes, mouse, extended,
                                  fastpath, unicode, relative mouse,
                                  horizontal scrolling)
0x0F  CAPSTYPE_FONT               fontSupportFlags
0x10  CAPSTYPE_BRUSH              brushSupportLevel (mono only, color 8x8,
                                  color full, 32-bit brush)
0x11  CAPSTYPE_GLYPHCACHE         GlyphCache[10] (cacheEntries+cellSize each)
                                  fragCache (entries+size)
                                  glyphSupportLevel (NONE/PARTIAL/FULL/ENCODE)
0x12  CAPSTYPE_OFFSCREENCACHE     offscreenSupportLevel, offscreenCacheSize,
                                  offscreenCacheEntries
0x13  CAPSTYPE_BITMAPCACHE_HOSTSUPPORT (bitmapCacheVersion, pad)
0x14  CAPSTYPE_BITMAPCACHE_REV2   cacheFlags, numCellCaches, bitmapCache0..4
0x15  CAPSTYPE_VIRTUALCHANNEL     flags (COMPRESS_RDP_8K/64K), VCChunkSize
0x16  CAPSTYPE_DRAWNINEGRID       drawNineGridSupportLevel, cacheEntries, size
0x17  CAPSTYPE_DRAWGDIPLUS        drawGdiPlusSupportLevel, drawGdiPlusCacheLevel
                                  GdiPlusCacheEntries (5 sub-caches)
0x18  CAPSTYPE_RAIL               railSupportLevel
0x19  CAPSTYPE_WINDOW             wndSupportLevel, numIconCaches, iconCacheSize
0x1A  CAPSTYPE_COMPDESK           compDeskSupportLevel
0x1B  CAPSTYPE_MULTIFRAGMENTUPDATE maxRequestSize (max single update PDU size)
0x1C  CAPSTYPE_LARGE_POINTER      largePointerSupportFlags
0x1D  CAPSTYPE_SURFACE_COMMANDS   cmdFlags (SET_SURFACE_BITS, FRAME_MARKER,
                                  STREAM_SURFACE_BITS)
0x1E  CAPSTYPE_BITMAP_CODECS      supportedBitmapCodecs (GUID + properties)
                                  (NSCodec, RemoteFX, JPEG, H.264 listed here)
0x1F  CAPSTYPE_FRAME_ACKNOWLEDGE  maxUnacknowledgedFrameCount
0x20  CAPSTYPE_BITMAP_CACHE_V3_CODEC_ID (used for RDP 8 cached codec)
──────────────────────────────────────────────────────────────────
```

The `orderSupport[32]` array in CAPSTYPE_ORDER is a bitmask where each bit indicates
support for a specific GDI drawing order. Critical orders:
```
Index  Order                    Meaning
 0     TS_NEG_DSTBLT_INDEX      Destination BLT (screen clear/fill)
 1     TS_NEG_PATBLT_INDEX      Pattern BLT (filled shapes)
 2     TS_NEG_SCRBLT_INDEX      Screen-to-screen BLT (scroll)
 7     TS_NEG_DRAWNINEGRID_INDEX Nine-grid BLT
 8     TS_NEG_LINETO_INDEX      Line draw
 9     TS_NEG_MULTI_DRAWNINEGRID_INDEX
11     TS_NEG_SAVEBITMAP_INDEX  Save screen region to offscreen cache
15     TS_NEG_MEMBLT_INDEX      Memory BLT (blit from bitmap cache)
16     TS_NEG_MEM3BLT_INDEX     Memory BLT with brush
20     TS_NEG_MULTIDSTBLT_INDEX Multiple DSTBLT
21     TS_NEG_MULTIPATBLT_INDEX Multiple PATBLT
22     TS_NEG_MULTISCRBLT_INDEX Multiple SCRBLT
23     TS_NEG_MULTIOPAQUERECT_INDEX
25     TS_NEG_FAST_INDEX_INDEX  Fast glyph rendering
26     TS_NEG_POLYGON_SC_INDEX  Solid-color polygon
27     TS_NEG_POLYGON_CB_INDEX  Cached-brush polygon
28     TS_NEG_POLYLINE_INDEX    Polyline
30     TS_NEG_FAST_GLYPH_INDEX  Fast glyph (alternate)
31     TS_NEG_ELLIPSE_SC_INDEX  Solid ellipse
32     TS_NEG_ELLIPSE_CB_INDEX  Cached-brush ellipse
33     TS_NEG_INDEX_INDEX       Glyph index
```

---

## 9. Graphics Pipeline

The graphics pipeline is the most complex part of RDP. Multiple encoding strategies are
layered to minimize bandwidth while maintaining visual fidelity.

### 9.1 GDI Orders (Drawing Orders)

GDI orders are the most bandwidth-efficient update type. Instead of sending pixels, the
server sends the **GDI drawing commands** that the client replicates locally. This works
perfectly for text, lines, rectangles, and bitmaps that fit in the bitmap cache.

**Update PDU structure for orders:**
```
Share Control Header
  └── Share Data Header (pduType2=PDUTYPE2_UPDATE)
        └── UpdateType=UPDATETYPE_ORDERS (0x0000)
              └── numberOrders (2 bytes)
                    └── [Order 1][Order 2]...[Order N]
```

**Order encoding**: Each order has a control byte, followed by field presence flags, followed
by field data for fields that changed since the last order of the same type.

```
Primary Order Encoding:
┌─────────────────────────────────────────────────────┐
│ controlFlags (1 byte)                               │
│   Bit 0 (0x01): STANDARD — standard primary order  │
│   Bit 1 (0x02): SECONDARY — secondary order prefix │
│   Bit 2 (0x04): ALTSEC — alternate secondary order │
│   Bit 3 (0x08): CHANGE_TYPE — order type present   │
│   Bit 4 (0x10): DELTA_COORDINATES — delta encoding │
│   Bit 5 (0x20): ZERO_FIELD_BYTE_BIT0               │
│   Bit 6 (0x40): ZERO_FIELD_BYTE_BIT1               │
│   Bit 7 (0x80): BOUNDS — bounding rectangle present│
└─────────────────────────────────────────────────────┘
[if CHANGE_TYPE]: orderType (1 byte)
[if BOUNDS]: bounding rectangle (variable, 1-8 bytes using delta compression)
fieldFlags: variable (N/8 bytes where N=fields in this order type)
field data: only fields whose bit is set in fieldFlags
```

**Delta coordinate encoding**: Coordinates that differ from the previous order by less than
128 are encoded as 1 byte instead of 2, saving bandwidth.

### 9.2 Bitmap Caching

The bitmap cache is a **client-side LRU cache of image tiles**. The server identifies each
cached image by a 64-bit hash (called the **cache key**). When a bitmap is first sent, it is
compressed and transmitted. Subsequent uses reference it by cache ID.

**Cache structure (RDP 5.x, Revision 2):**
```
Cell Cache 0: 600 entries, max 256×256 pixels each
Cell Cache 1: 300 entries, max 256×256 pixels each
Cell Cache 2: 262 entries, max 256×256 pixels each
Cell Cache 3: 100 entries, max 256×256 pixels each
Cell Cache 4: 100 entries, max 256×256 pixels each
```

Each entry: `(cacheId, cacheIndex)` = 2 bytes identifies cached bitmap.

**MemBlt order** uses these to blit a cached bitmap at coordinates (x, y):
```
MemBlt fields:
  cacheId    : which cell cache (0–4)
  nLeftRect  : destination X
  nTopRect   : destination Y
  nWidth     : source width
  nHeight    : source height
  bRop       : raster operation (0xCC = copy)
  nXSrc      : source X offset within cached tile
  nYSrc      : source Y offset within cached tile
  cacheIndex : index within cacheId
```

**Persistent Bitmap Cache**: Between sessions, clients can save the bitmap cache to disk
and restore it on reconnect, avoiding retransmission of unchanged bitmaps. The server
sends a `PDUTYPE2_BITMAPCACHE_PERSISTENT_LIST` to declare which keys it considers still
valid.

### 9.3 Bitmap Compression (RLE / RDP6 / RDP6.1)

When a bitmap region cannot be expressed as GDI orders or cached tiles, it must be sent
as raw/compressed pixels.

**RDP4 (RLE Compression)**:
```
Run Length Encoding over scan lines.
Code bytes: 0x00–0x5F = encoded runs, 0x60–0xFF = raw pixels
Suites: Background run, foreground run, color run, dithered, black, white, etc.
```

**RDP5 (NSR Compression — Not Simply RLE)**:
```
Improved multi-pass compression:
Level-1: First-line encoding (start with raw pixels for first scan line)
Subsequent lines: delta from previous scan line, then RLE on deltas
Achieved ~30-50% better compression than RDP4 RLE
```

**RDP6 / RDP6.1**:
Introduced in Windows Vista/2008:
```
XOR-based compression on scan-line deltas
Huffman coding on XOR residuals
Color lossy compression option for low-bandwidth
RDP6.1 adds tiling of large bitmaps for better compression ratio
```

**Compression flag in Bitmap Data:**
```
BITMAP_COMPRESSION      0x0001  — data is compressed
NO_BITMAP_COMPRESSION_HDR 0x0400 — skip compression header (RDP6+)
```

### 9.4 RemoteFX (RFX)

RemoteFX (introduced in RDP 7.0) is a wavelet-based codec designed for high-quality
desktop transmission including Aero Glass, video, and 3D content.

**Architecture**:
```
Source frame (32bpp RGBA)
    │
    ▼
Color space conversion: RGB → YCbCr (YUV)
    │  (reduces perceptual chroma resolution)
    ▼
Tiling: split into 64×64 pixel tiles
    │
    ▼
2D Discrete Wavelet Transform (DWT) on each tile
    │  (3-level sub-band decomposition: HL, LH, HH, LL)
    ▼
Quantization of DWT coefficients
    │  (quality-controlled lossy step)
    ▼
RLGR (Run-Length Golomb-Rice) entropy coding
    │
    ▼
RFX Frame Data → transmitted as surface command
```

**RFX Data Format:**
```
TS_RFX_CONTEXT:
  contextId, tileSize (64), codecId (0x0010/0x0020 for RFX/RFX-Progressive)

TS_RFX_FRAME_BEGIN / TS_RFX_FRAME_END:
  frameIdx

TS_RFX_REGION:
  numRectsRects[]  — affected regions

TS_RFX_TILESET:
  codecId, lt (header), numQuants, numTiles
  Quants[numQuants]: quantization values for Y, Cb, Cr DWT sub-bands
  Tiles[numTiles]: TS_RFX_TILE structs

TS_RFX_TILE:
  quantIdxY, quantIdxCb, quantIdxCr
  xIdx, yIdx   (tile position in 64-pixel units)
  YLen, CbLen, CrLen   (compressed data lengths)
  YData[], CbData[], CrData[]   (RLGR compressed DWT coefficients)
```

**RemoteFX Codec GUID**: `{76772967-7468-4569-7375-66647470}` (human-readable: "wuWthisufdt")
More precisely: `0x76772967-0x7468-0x4569-0x7375-0x66647470`

### 9.5 H.264/AVC Codec (RDP 8+)

RDP 8.0 introduced H.264 encoding for graphics transport via the **EGFX** (Enhanced
Graphics Channel) or as a bitmap codec.

**Two sub-modes**:
```
AVC420: H.264 YUV 4:2:0 — normal video compression
AVC444: H.264 YUV 4:4:4 — lossless chroma (text rendering quality)
AVC444v2: Improved version in RDP 10.3
```

The server encodes the desktop (or surface) as an H.264 stream with:
- I-frames (full frames) on reconnect / scene change
- P-frames (predicted frames) for motion
- Metadata PDU describes which surface rectangles were updated

Latency optimizations:
- Low-delay H.264 profile (no B-frames)
- Constrained baseline profile
- Slice-level parallelism
- Fast entropy coding (CAVLC preferred over CABAC for latency)

### 9.6 EGFX — Enhanced Graphics Channel (RDP 10)

EGFX (MS-RDPEGFX) is a **Dynamic Virtual Channel** named `"Microsoft::Windows::RDS::Graphics"`.
It replaces the legacy graphics path entirely for clients that support it.

EGFX commands:
```
RDPGFX_CMDID_WIRETOSURFACE_1      (0x0001) — compressed surface bitmap (old codecs)
RDPGFX_CMDID_WIRETOSURFACE_2      (0x0002) — H.264/RemoteFX data
RDPGFX_CMDID_DELETEENCODINGCONTEXT (0x0003)
RDPGFX_CMDID_SOLIDFILL            (0x0004) — fill rect with solid color
RDPGFX_CMDID_SURFACETOSURFACE     (0x0005) — GPU-to-GPU blit
RDPGFX_CMDID_SURFACETOCACHE       (0x0006) — cache a surface region
RDPGFX_CMDID_CACHETOSURFACE       (0x0007) — blit from cache to surface
RDPGFX_CMDID_EVICTCACHEENTRY      (0x0008) — evict cache entry
RDPGFX_CMDID_CREATESURFACE        (0x0009) — create offscreen surface
RDPGFX_CMDID_DELETESURFACE        (0x000A) — delete offscreen surface
RDPGFX_CMDID_STARTFRAME           (0x000B) — begin frame marker
RDPGFX_CMDID_ENDFRAME             (0x000C) — end frame marker
RDPGFX_CMDID_FRAMEACKNOWLEDGE     (0x000D) — client acks frame (flow control)
RDPGFX_CMDID_RESETGRAPHICS        (0x000E) — resize display
RDPGFX_CMDID_MAPSURFACETOOUTPUT   (0x000F) — bind surface to monitor region
RDPGFX_CMDID_CACHEIMPORTREPLY     (0x0011) — server replies to cache import
RDPGFX_CMDID_CAPSCONFIRM          (0x0013) — codec capability confirm
RDPGFX_CMDID_CAPSADVERTISE        (0x0012) — client announces EGFX caps
RDPGFX_CMDID_MAPSURFACETOSCALEDOUTPUT (0x001A) — scaled surface output
RDPGFX_CMDID_MAPSURFACETOSCALEDWINDOW (0x001B) — scaled surface to window
```

**Frame Acknowledgment** is critical for flow control: client sends
`RDPGFX_CMDID_FRAMEACKNOWLEDGE` for each `ENDFRAME`. Server tracks
`maxUnacknowledgedFrameCount` (from CAPSTYPE_FRAME_ACKNOWLEDGE capability) and stops
sending new frames if too many are unacknowledged.

### 9.7 Progressive Bitmap Compression

Introduced in RDP 10.4, the **progressive codec** (MS-RDPEGFX progressive) allows:
- **Initial transmission** at low quality (thumbnail-like) → very fast first paint
- **Refinement passes** progressively improve quality
- Client sees something immediately, then detail improves over ~3-5 passes
- Works like progressive JPEG but for desktop regions

The codec uses RemoteFX DWT + RLGR but controls quantization per pass:
```
Pass 1 (Thumbnail): high quantization, low quality, small size
Pass 2 (Rough):     medium quantization
Pass 3 (Fine):      low quantization
Pass 4+ (Lossless): quantization=1 (near-lossless)
```

---

## 10. Input Subsystem

### 10.1 Keyboard Input PDU

Keyboard input uses **scan codes** (hardware-level key codes), not character codes.
This preserves keyboard behavior regardless of the client OS's key layout.

```
TS_KEYBOARD_EVENT:
  eventFlags  (2 bytes):
    KBDFLAGS_EXTENDED  0x0100  — Extended key (e.g., right Ctrl, numpad Enter)
    KBDFLAGS_DOWN      0x4000  — Key pressed (absent = key released)
    KBDFLAGS_RELEASE   0x8000  — Key released (explicit release flag)
  keyCode     (2 bytes): scan code (e.g., 0x001E = 'A' on US keyboard)
```

The server remaps scan codes to virtual keys using the session's keyboard layout.
**Important**: RDP sends the physical scan code, not the character. This allows proper
behavior for international keyboards and keyboard shortcuts.

Special keys:
```
Scan code → Physical key (US layout reference)
0x001C     Enter
0x001D     Ctrl (left)
0x001D+EXT Right Ctrl
0x003A     Caps Lock
0xE01D     Right Ctrl (extended)
0xE038     Right Alt
0xE047     Home (numpad vs extended)
```

### 10.2 Mouse Input PDU

```
TS_POINTER_EVENT:
  pointerFlags (2 bytes):
    PTRFLAGS_HWHEEL     0x0400  — Horizontal scroll (RDP 5.1+)
    PTRFLAGS_WHEEL      0x0200  — Vertical scroll
    PTRFLAGS_WHEEL_NEG  0x0100  — Scroll direction (combined with wheel)
    PTRFLAGS_MOVE       0x0800  — Pointer move event
    PTRFLAGS_DOWN       0x8000  — Button press (combined with button flags)
    PTRFLAGS_BUTTON1    0x1000  — Left button
    PTRFLAGS_BUTTON2    0x2000  — Right button
    PTRFLAGS_BUTTON3    0x4000  — Middle button
    Bits 8-10: wheel rotation delta (for wheel events, WheelRotationMask=0x01FF)
  xPos (2 bytes): absolute X coordinate (0 to desktopWidth-1)
  yPos (2 bytes): absolute Y coordinate (0 to desktopHeight-1)
```

**Extended pointer events** (TS_POINTER_EX_EVENT): Adds support for extra mouse buttons
(XBUTTON1=0x0001, XBUTTON2=0x0002) via PTRXFLAGS in a separate flags word.

### 10.3 Unicode Keyboard Events

For input methods (IME) that produce Unicode characters directly:

```
TS_UNICODE_KEYBOARD_EVENT:
  eventFlags (2 bytes):
    KBDFLAGS_RELEASE  0x8000
  unicode    (2 bytes): UTF-16LE code unit
```

This bypasses scan codes entirely and directly injects a Unicode character.

### 10.4 Fast-Path Input

Fast-Path Input (introduced in RDP 5.0) bypasses the MCS/Share Data header overhead
for latency-critical input events.

```
Normal path: TPKT(4) + X.224(3) + MCS(7) + SecurityHdr(4) + ShareCtrl(6) + ShareData(12) + Input = ~36 bytes overhead
Fast path:   TPKT(4) + FastPathHeader(1-2) + [MAC(8)] + EventCount(1) + Events = ~6 bytes overhead
```

**Fast-Path Input PDU:**
```
fpInputHeader (1 byte):
  Bits 0-1: action = 0x01 (FASTPATH_INPUT_ACTION_FASTPATH)
  Bits 2-3: numEvents (0-15; or 0 if extended count used)
  Bits 6-7: encryption flags (0=none, 1=encrypted, 2=secure checksum)
[length2 (1 byte, optional)]: high byte of length if > 127
[fipsInformation]: if FIPS encryption
[dataSignature (8 bytes)]: if encrypted
[numEvents (1 byte)]: if numEvents in header == 0
events[]: TS_FP_INPUT_EVENT structures
```

**TS_FP_INPUT_EVENT**:
```
eventHeader (1 byte):
  Bits 0-4: eventCode (event type)
  Bits 5-6: eventFlags
[eventData]: depends on eventCode
  FASTPATH_INPUT_EVENT_SCANCODE (0x0): keyboardFlags(upper bits) + keyCode(1 byte)
  FASTPATH_INPUT_EVENT_MOUSE    (0x1): pointerFlags(2) + xPos(2) + yPos(2)
  FASTPATH_INPUT_EVENT_MOUSEX   (0x2): pointerFlags(2) + xPos(2) + yPos(2)
  FASTPATH_INPUT_EVENT_SYNC     (0x3): eventFlags = keyboard LED state
  FASTPATH_INPUT_EVENT_UNICODE  (0x4): unicodeCode(2 bytes)
  FASTPATH_INPUT_EVENT_RELMOUSE (0x5): relative mouse event (RDP 8+)
```

---

## 11. Virtual Channels

Virtual channels provide the extensibility mechanism for RDP. Every peripheral redirection
feature uses a virtual channel.

### 11.1 Static Virtual Channels (SVC)

Static channels are negotiated during GCC Conference Create (in CS_NET / SC_NET).

**CS_NET** announces requested channels:
```
channelCount   (4 bytes)
channelDefArray[channelCount]:
  name   (8 bytes, ASCII null-padded) — e.g., "cliprdr\0", "rdpdr\0\0\0"
  options (4 bytes):
    CHANNEL_OPTION_INITIALIZED              0x80000000
    CHANNEL_OPTION_ENCRYPT_RDP              0x40000000
    CHANNEL_OPTION_ENCRYPT_SC              0x20000000
    CHANNEL_OPTION_ENCRYPT_CS              0x10000000
    CHANNEL_OPTION_PRI_HIGH                0x08000000
    CHANNEL_OPTION_PRI_MED                 0x04000000
    CHANNEL_OPTION_PRI_LOW                 0x02000000
    CHANNEL_OPTION_COMPRESS_RDP            0x00800000
    CHANNEL_OPTION_COMPRESS                0x00400000
    CHANNEL_OPTION_SHOW_PROTOCOL           0x00200000
    CHANNEL_OPTION_REMOTE_CONTROL_PERSISTENT 0x00100000
```

**SC_NET** allocates channel IDs:
```
MCSChannelId  (2 bytes) — base channel ID (1002 = I/O)
channelCount  (2 bytes)
channelIdArray[channelCount]: (2 bytes each) — allocated IDs (1003, 1004, ...)
```

The channel name→ID mapping is by index: CS_NET.channelDefArray[i] corresponds to
SC_NET.channelIdArray[i].

Well-known channel names:
```
"cliprdr"   — Clipboard redirection (CLIPRDR)
"rdpdr"     — Device redirection (drives, printers, smart cards, ports)
"rdpsnd"    — Audio output redirection
"drdynvc"   — Dynamic virtual channel manager
"rdpinpt"   — Touch/pen input (Remote Desktop Input)
"Microsoft::Windows::RDS::Telemetry" — Telemetry
"MS_T120"   — (Legacy, RDP 4.0 T.120 channel — vulnerable to BlueKeep)
```

### 11.2 Dynamic Virtual Channels (DVC)

DVCs are multiplexed over a single SVC named `"drdynvc"`. They allow channels to be
opened and closed dynamically during a session.

**DRDYNVC Protocol (MS-RDPEDYC):**
```
Cmd                   Value  Direction   Description
──────────────────────────────────────────────────────
CAPABILITY_REQ        0x05   S→C         Announce DVC capabilities
CAPABILITY_RESP       0x15   C→S         Client capability response
OPEN_REQ              0x10   S→C         Open new DVC by name
OPEN_RSP              0x20   C→S         Response to open
DATA_FIRST            0x02   Both        First fragment of DVC data
DATA                  0x03   Both        Non-first fragment / single-fragment
DATA_FIRST_COMPRESSED 0x06   Both        First fragment, compressed
DATA_COMPRESSED       0x07   Both        Fragment, compressed
CLOSE_REQ             0x40   Both        Close DVC
SOFT_SYNC_REQ         0x08   S→C         Soft sync (RDP 8+)
SOFT_SYNC_RESP        0x18   C→S         Soft sync response
```

Each DVC message has a **Channel ID** (1-3 bytes, cbId-encoded) identifying which
dynamic channel the data belongs to.

Well-known DVC names:
```
"Microsoft::Windows::RDS::Graphics"     — EGFX (RDP 10 graphics pipeline)
"Microsoft::Windows::RDS::DisplayControl" — Display layout control
"Microsoft::Windows::RDS::Geometry"     — Desktop composition geometry
"Microsoft::Windows::RDS::Video::Control" — H.264 video
"Microsoft::Windows::RDS::Video::Data"   — H.264 video data
"rdpinpt"                               — Input redirection (DVC version)
"AUDIO_PLAYBACK_DYN_VC"                 — Audio playback DVC
"AUDIO_RECORDING_DYN_VC"               — Audio capture
"Microsoft::Windows::RDS::Telemetry"    — Telemetry DVC
"FileRedirectorChannel"                 — RDPDR DVC version (future)
```

### 11.3 Channel Fragmentation and Reassembly

Virtual channel data may exceed the negotiated chunk size (`VCChunkSize` from
CAPSTYPE_VIRTUALCHANNEL, default 1600 bytes, max 16KB or 64KB depending on flags).

**Channel PDU Header** (prepended to first chunk only):
```
length        (4 bytes LE) — total uncompressed length of the message
flags         (4 bytes LE):
  CHANNEL_FLAG_FIRST      0x00000001 — first chunk
  CHANNEL_FLAG_LAST       0x00000002 — last chunk
  CHANNEL_FLAG_SHOW_PROTOCOL 0x00000010 — header present in all chunks
  CHANNEL_FLAG_SUSPEND    0x00000020
  CHANNEL_FLAG_RESUME     0x00000040
  CHANNEL_FLAG_SHADOW_PERSISTENT 0x00000080
  CHANNEL_PACKET_COMPRESSED  0x00200000
  CHANNEL_PACKET_AT_FRONT    0x00400000
  CHANNEL_PACKET_FLUSHED     0x00800000
  CompressionTypeMask        0x000F0000 (8K/64K RDP compression type)
```

Subsequent chunks for `SHOW_PROTOCOL` channels include the header with updated flags.
Otherwise, subsequent chunks are raw data.

---

## 12. Clipboard Redirection (CLIPRDR)

The clipboard channel (`"cliprdr"`) allows copy-paste between client and server.

**Protocol flow:**
```
Client                                           Server
  │── CLIPRDR_HEADER: CB_CLIP_CAPS ────────────►│ (announce capabilities)
  │◄─ CLIPRDR_HEADER: CB_CLIP_CAPS ─────────────│
  │◄─ CB_MONITOR_READY ──────────────────────────│ (server ready)
  │── CB_CLIENT_TEMP_DIRECTORY ─────────────────►│ (temp dir for file transfer)

  ┌── User copies text on server ──────────────────────────────┐
  │◄─ CB_FORMAT_LIST ────────────────────────────│ (available formats: CF_TEXT, etc.)
  │── CB_FORMAT_LIST_RESPONSE ──────────────────►│ (OK)
  │── CB_FORMAT_DATA_REQUEST (CF_UNICODETEXT) ──►│ (paste requested)
  │◄─ CB_FORMAT_DATA_RESPONSE (UTF-16 data) ─────│
  └──────────────────────────────────────────────────────────┘

  ┌── User copies on client ────────────────────────────────────┐
  │── CB_FORMAT_LIST ────────────────────────────►│
  │◄─ CB_FORMAT_LIST_RESPONSE ───────────────────│
  │◄─ CB_FORMAT_DATA_REQUEST ────────────────────│
  │── CB_FORMAT_DATA_RESPONSE ──────────────────►│
  └──────────────────────────────────────────────────────────┘
```

**File copy/paste** (CLIPRDR File Transfer):
```
Additional format: CF_HDROP or CLIPRDR_FORMAT_FILE_LIST
Server sends CB_FORMAT_LIST with fileDescriptors
Client requests CB_FORMAT_DATA_REQUEST
Server provides CLIPRDR_FILELIST with:
  cFiles: count
  fileDescriptors[]:
    flags, lastWriteTime, fileAttributes, fileSize (lo/hi), fileName

Client then uses:
  CB_FILECONTENTS_REQUEST (specifying file index + offset + length)
  CB_FILECONTENTS_RESPONSE (actual file bytes)
```

Security consideration: Clipboard channel can be exploited for data exfiltration.
Group Policy can restrict clipboard direction (client→server only, server→client only, both, neither).

---

## 13. Drive Redirection (RDPDR)

The device redirection channel (`"rdpdr"`) provides access to client-side drives, printers,
serial ports, and smart cards from the server.

**RDPDR message structure:**
```
RDPDR_HEADER:
  Component (2 bytes): RDPDR_CTYP_CORE=0x4472, RDPDR_CTYP_PRN=0x5052
  PacketId  (2 bytes): message type ID
```

**Initialization sequence:**
```
Server → Client: PAKID_CORE_SERVER_ANNOUNCE    (server version, session ID)
Client → Server: PAKID_CORE_CLIENTID_CONFIRM   (client version, client ID)
Client → Server: PAKID_CORE_CLIENT_NAME        (client machine name)
Server → Client: PAKID_CORE_USER_LOGGEDON      (after user auth)
Client → Server: PAKID_CORE_CLIENT_CAPABILITY  (client capabilities)
Server → Client: PAKID_CORE_SERVER_CAPABILITY  (server capabilities)

Client → Server: PAKID_CORE_DEVICELIST_ANNOUNCE (list of devices to redirect)
Server → Client: PAKID_CORE_DEVICE_REPLY        (per-device status)
```

**Device Announcement Structure:**
```
DEVICE_ANNOUNCE:
  DeviceType (4 bytes):
    RDPDR_DTYP_SERIAL    0x00000001
    RDPDR_DTYP_PARALLEL  0x00000002
    RDPDR_DTYP_PRINT     0x00000004
    RDPDR_DTYP_FILESYSTEM 0x00000008
    RDPDR_DTYP_SMARTCARD 0x00000020
  DeviceId    (4 bytes): unique device ID
  PreferredDosName (8 bytes): e.g., "C:\x00\x00\x00\x00\x00\x00\x00"
  DeviceDataLength (4 bytes)
  DeviceData[]: type-specific data
```

**File System I/O** (for drive redirection):

The server sends I/O requests to the client device using the **IRP (I/O Request Packet)**
model borrowed from Windows kernel:

```
DR_DEVICE_IOREQUEST (PAKID_CORE_DEVICE_IOREQUEST):
  DeviceId    (4 bytes)
  FileId      (4 bytes): open file handle on client
  CompletionId (4 bytes): for matching responses
  MajorFunction (4 bytes):
    IRP_MJ_CREATE            0x00000000  (open/create file)
    IRP_MJ_CLOSE             0x00000002  (close handle)
    IRP_MJ_READ              0x00000003  (read file)
    IRP_MJ_WRITE             0x00000004  (write file)
    IRP_MJ_DEVICE_CONTROL    0x0000000E  (IOCTL)
    IRP_MJ_QUERY_VOLUME_INFORMATION 0x0000000A
    IRP_MJ_SET_VOLUME_INFORMATION   0x0000000B
    IRP_MJ_QUERY_INFORMATION  0x00000005
    IRP_MJ_SET_INFORMATION    0x00000006
    IRP_MJ_DIRECTORY_CONTROL  0x0000000C
    IRP_MJ_LOCK_CONTROL       0x00000011
  MinorFunction (4 bytes): for IRP_MJ_DIRECTORY_CONTROL sub-types
  [request-specific data]

DR_DEVICE_IOCOMPLETION (client → server):
  DeviceId, CompletionId, IoStatus (NTSTATUS), [response data]
```

This effectively gives the Windows server a full filesystem view of the client's drives,
including read, write, create, delete, enumerate, query info operations.

---

## 14. Audio Redirection (RDPSND / AUDIO_PLAYBACK)

### Static Channel: RDPSND (`"rdpsnd"`)

Used in RDP 5.0 through 7.x for audio playback redirection.

```
Server → Client: SNDC_FORMATS (WaveFormatEx structures for supported formats)
Client → Server: SNDC_FORMATS (client's supported formats)
Client → Server: SNDC_TRAINING (latency measurement packet)
Server → Client: SNDC_TRAINING_CONFIRM

Server → Client: SNDC_WAVE (audio data, up to 4KB per PDU)
  wFormatNo, wTimeStamp, bBlockNo, [audio data]
Client → Server: SNDC_WAVECONFIRM (bBlockNo, wTimeStamp) — flow control

Server → Client: SNDC_CLOSE (terminate audio stream)
Server → Client: SNDC_SETVOLUME (volume control)
Server → Client: SNDC_PITCH (pitch control)
Server → Client: SNDC_CRYPTKEY (encryption key for audio)
```

### Dynamic Channel: AUDIO_PLAYBACK_DYN_VC

RDP 8+ uses a DVC for higher quality audio:
- Supports more codecs (AAC, SILK, Opus via future extension)
- Lower latency framing
- Better synchronization with video

### Audio Capture: AUDIO_RECORDING_DYN_VC

Redirects microphone audio from client to server (for voice applications on the server):
```
Server → Client: capabilities
Client → Server: RDPSND audio data (PCM or encoded)
```

---

## 15. Printer Redirection

Printer redirection is handled via the RDPDR channel (DeviceType=RDPDR_DTYP_PRINT).

The client announces redirected printers in PAKID_CORE_DEVICELIST_ANNOUNCE. The server
receives print jobs via IRP calls to the virtual printer device, and the client renders
and submits them to the local print queue.

**TS Easy Print** (RDP 6.1+):
Before TS Easy Print, the server required the printer driver to be installed server-side.
TS Easy Print sends the job as **XPS (XML Paper Specification)** from server to client,
and the client uses its local drivers to render it. This eliminates the need for
driver installation on the server.

```
Print flow with Easy Print:
  1. App on server creates print job
  2. XPS print driver on server converts to XPS
  3. XPS stream sent via RDPDR to client
  4. Client's print system routes to local printer with local drivers
  5. Physical printing occurs at client location
```

---

## 16. Smart Card Redirection

Smart card redirection lets server-side applications use the client's smart card.

Channel: `"scard"` within RDPDR (DeviceType=RDPDR_DTYP_SMARTCARD, DeviceId=0x00000000 by convention).

The protocol tunnels **PC/SC (WinSCard)** API calls over the RDP channel:

```
Server-side WinSCard call → IOCTL wrapper → RDPDR IRP_MJ_DEVICE_CONTROL
    → transmitted to client → PC/SC Lite or WinSCard API call
    → response returned via IRP completion
```

IOCTL codes tunneled (from winscard.h):
```
SCARD_IOCTL_ESTABLISHCONTEXT      0x00090014
SCARD_IOCTL_RELEASECONTEXT        0x00090018
SCARD_IOCTL_ISVALIDCONTEXT        0x0009001C
SCARD_IOCTL_LISTREADERNAMESW      0x00090030
SCARD_IOCTL_CONNECTW              0x000900AC
SCARD_IOCTL_RECONNECT             0x000900B0
SCARD_IOCTL_DISCONNECT            0x000900B4
SCARD_IOCTL_BEGINTRANSACTION      0x000900B8
SCARD_IOCTL_ENDTRANSACTION        0x000900BC
SCARD_IOCTL_TRANSMIT              0x000900D4
SCARD_IOCTL_STATUSA               0x000900E4
SCARD_IOCTL_GETSTATUSCHANGEW      0x000900A0
```

---

## 17. USB Redirection (URBDRC)

USB Redirection (MS-RDPEUSB) allows full USB device forwarding (not just specific device
classes like smart cards or storage).

Channel: `"URBDRC"` (DVC)

Protocol model:
```
Client discovers USB devices
Client → Server: ADD_VIRTUAL_CHANNEL (device added)
Server → Client: URB_TRANSFER (USB Request Block transfer)
Client executes URB against local USB device
Client → Server: URB_TRANSFER response
```

This enables forwarding of arbitrary USB devices: cameras, dongles, biometric readers,
specialized hardware — anything with a USB interface.

---

## 18. RemoteApp (RAIL)

RemoteApp (Remote Application Integrated Locally) presents individual server-side
applications as if they were running locally on the client. The client sees a normal
application window, not a full desktop.

**Architecture**:
```
                    Server Side                     Client Side
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│  Application (Notepad.exe)      │   │  mstsc.exe (client shell mode)  │
│  Windows GDI → RDP graphics     │   │  Receives window positions,     │
│                                 │   │  renders content, integrates    │
│  Shell integration              │   │  with client taskbar            │
│  Window management              │◄──►│                                 │
│  (position, title, icon,        │   │  Client OS owns desktop chrome  │
│   z-order, state changes)       │   │  (title bar, window borders)    │
└─────────────────────────────────┘   └─────────────────────────────────┘
```

**RAIL Protocol (MS-RDPERP / MS-RDPBCGR RAIL extensions)**:
- Negotiated via `CAPSTYPE_RAIL` capability set
- Uses a dedicated virtual channel for window management messages
- Graphics still flow through normal RDP graphics pipeline, but client knows
  which surface region belongs to which window

RAIL PDU types:
```
TS_RAIL_ORDER_HANDSHAKE          0x0012  — version exchange
TS_RAIL_ORDER_CLIENTSTATUS       0x000B  — client status (flags)
TS_RAIL_ORDER_EXEC               0x0001  — execute remote app
TS_RAIL_ORDER_ACTIVATE           0x0002  — activate/deactivate window
TS_RAIL_ORDER_SYSPARAM           0x0003  — system parameter sync
TS_RAIL_ORDER_SYSCOMMAND         0x0004  — window system command (min/max/close)
TS_RAIL_ORDER_NOTIFY_EVENT       0x0006  — notification area events
TS_RAIL_ORDER_WINDOWMOVE         0x0008  — request window move
TS_RAIL_ORDER_LOCALMOVESIZE      0x0009  — move/size started locally
TS_RAIL_ORDER_MINMAXINFO         0x000A  — min/max size constraints
TS_RAIL_ORDER_APPID_REQ          0x000E  — app ID request
TS_RAIL_ORDER_APPID_RESP         0x000F  — app ID response
TS_RAIL_ORDER_SNAP_ARRANGE       0x0025  — snap/arrange window
TS_RAIL_ORDER_GET_APPID_REQ      0x000E
TS_RAIL_ORDER_LANGUAGEBAR_INFO   0x0011
TS_RAIL_ORDER_LANGUAGEIME_INFO   0x002C
```

**Window Information PDU (TS_WINDOW_ORDER_INFO)** — server tells client about window state:
```
OrderSize, FieldsPresentFlags:
  WINDOW_ORDER_TYPE_WINDOW    0x01000000
  WINDOW_ORDER_TYPE_NOTIFY    0x02000000
  WINDOW_ORDER_TYPE_DESKTOP   0x04000000
  WINDOW_ORDER_FIELD_OWNER        0x00000002
  WINDOW_ORDER_FIELD_STYLE        0x00000008
  WINDOW_ORDER_FIELD_TITLE        0x00000040
  WINDOW_ORDER_FIELD_ICON_BIG     0x00002000
  WINDOW_ORDER_FIELD_TASKBAR_BUTTON 0x00800000
  WINDOW_ORDER_FIELD_CLIENT_AREA_SIZE 0x00010000
  WINDOW_ORDER_FIELD_WND_SIZE     0x00000800
  WINDOW_ORDER_FIELD_WND_OFFSET   0x00000100
  WINDOW_ORDER_FIELD_WND_CLIENT_DELTA 0x00008000
  WINDOW_ORDER_FIELD_WND_RECTS    0x00000200
  WINDOW_ORDER_FIELD_VIS_OFFSET   0x00001000
  WINDOW_ORDER_FIELD_VISIBILITY   0x00000400
```

---

## 19. Multipoint / Multiparty (RDP Multipoint)

Originally, MCS was designed for true multipoint conferencing (multiple clients viewing
one session). RDP implements this as **Remote Assistance / Shadow Sessions** rather
than multi-client desktop sharing in the traditional T.128 sense.

**Shadow Sessions (Remote Assistance):**
```
Primary session (Shadowee)
    │
    ├── Regular RDP connection (primary display)
    │
    └── Shadow connection (Shadow protocol MS-RDPESP):
            TS_SHADOW_PDU
            Shadow target server ←→ Shadow client
            Viewer receives copies of all output PDUs
            Viewer can optionally inject input (if shadowee permits)
```

Shadow uses a separate protocol stack (MS-RDPESP) that multiplexes a second virtual
terminal to the first.

---

## 20. Multi-Monitor Support

Multiple monitors are negotiated during GCC Conference Create via **CS_MONITOR** and
subsequent **Monitor Layout PDUs**.

**CS_MONITOR** (Client Monitor Data):
```
flags         (4 bytes): 0x00000000 (reserved)
monitorCount  (4 bytes): number of monitors (max 16)
monitors[monitorCount]:
  left    (4 bytes, signed): leftmost pixel coordinate
  top     (4 bytes, signed): topmost pixel coordinate
  right   (4 bytes, signed): rightmost pixel coordinate
  bottom  (4 bytes, signed): bottommost pixel coordinate
  flags   (4 bytes): MONITOR_PRIMARY=0x00000001
```

Monitor coordinates use the **client's virtual screen** coordinate system. The primary
monitor must contain (0, 0). Monitors are arranged with pixel-accurate offsets.

**Monitor Layout PDU** (PDUTYPE2_MONITOR_LAYOUT_PDU) — can be sent during active session
to change monitor configuration without full reconnect (RDP 10+).

**Per-monitor DPI** (EGFX MAPSURFACETOSCALEDOUTPUT):
With EGFX, each surface can be mapped to a specific monitor region with independent
scaling. This enables proper HiDPI multi-monitor configurations.

---

## 21. Reconnection and Session Resume

RDP maintains server-side sessions across disconnects. When a client reconnects:

**Auto-Reconnect Cookie (ARC)**:
Generated at session establishment:
```
serverRandom (16 bytes)  — generated by server
arc_key = HMAC-MD5(serverRandom, sessionId + "Auto-Reconnect")
arcCookie = HMAC-MD5(arc_key, clientRandom)
```

The cookie is stored by the client. On reconnect, it is presented in the **Info PDU**
(`SEC_INFO_PKT`) `autoReconnectCookie` field. The server validates it without requiring
the user's password. This enables:
- Seamless reconnect after network interruption
- Network roaming (changing IP while maintaining session)

**Info PDU** (inside Security Exchange, before capabilities):
```
TS_INFO_PACKET:
  CodePage            (4 bytes): ANSI code page
  flags               (4 bytes):
    INFO_MOUSE              0x00000001
    INFO_DISABLECTRLALTDEL  0x00000002
    INFO_AUTOLOGON          0x00000008
    INFO_UNICODE            0x00000010
    INFO_MAXIMIZESHELL      0x00000020
    INFO_LOGONNOTIFY        0x00000040
    INFO_COMPRESSION        0x00000080
    INFO_ENABLEWINDOWSKEY   0x00000100
    INFO_REMOTECONSOLEAUDIO 0x00002000
    INFO_FORCE_ENCRYPTED_CS_PDU 0x00004000
    INFO_RAIL               0x00008000
    INFO_LOGONERRORS        0x00010000
    INFO_MOUSE_HAS_WHEEL    0x00020000
    INFO_PASSWORD_IS_SC_PIN 0x00040000
    INFO_NOAUDIOPLAYBACK    0x00080000
    INFO_USING_SAVED_CREDS  0x00100000
    INFO_AUDIOCAPTURE       0x00200000
    INFO_VIDEO_DISABLE      0x00400000
    INFO_RESERVED1          0x00800000
    INFO_HIDEF_RAIL_SUPPORTED 0x02000000
  cbDomain, cbUserName, cbPassword, cbAlternateShell, cbWorkingDir
  Domain, UserName, Password (encrypted), AlternateShell, WorkingDir
  extraInfo (TS_EXTENDED_INFO_PACKET):
    clientAddressFamily, cbClientAddress, clientAddress
    cbClientDir, clientDir
    clientTimeZone (TS_TIME_ZONE_INFORMATION)
    clientSessionId
    performanceFlags
    cbAutoReconnectLen, autoReconnectCookie
    reserved1, reserved2
    cbDynamicDSTTimeZoneKeyName, dynamicDSTTimeZoneKeyName
    dynamicDaylightTimeDisabled
```

---

## 22. Performance Flags and Optimizations

The `performanceFlags` field in TS_EXTENDED_INFO_PACKET controls which expensive
visual features are disabled for bandwidth/CPU savings:

```
Flag                              Value       Disables
──────────────────────────────────────────────────────────────────
PERF_DISABLE_WALLPAPER            0x00000001  Desktop wallpaper
PERF_DISABLE_FULLWINDOWDRAG       0x00000002  Window drag show contents
PERF_DISABLE_MENUANIMATIONS       0x00000004  Menu fade animations
PERF_DISABLE_THEMING              0x00000008  Visual styles/themes
PERF_DISABLE_CURSOR_SHADOW        0x00000020  Cursor shadow
PERF_DISABLE_CURSORSETTINGS       0x00000040  Cursor blinking/trails
PERF_ENABLE_FONT_SMOOTHING        0x00000080  Enable ClearType
PERF_ENABLE_DESKTOP_COMPOSITION   0x00000100  Enable Aero Glass
```

**Bandwidth auto-detection** (MS-RDPBCGR § 2.2.1.4):
RDP 8+ can auto-detect network conditions and adjust performance flags:
- Sends bandwidth estimation packets during connection
- Measures RTT and throughput
- Server applies appropriate performance profile

**Suppress Output PDU** (`PDUTYPE2_SUPPRESS_OUTPUT`):
```
allowDisplayUpdates: 0=suppress, 1=resume
desktopRect: region to suppress (usually full desktop when minimized)
```
When the client window is minimized or not visible, it sends this to stop the server
from sending unnecessary graphics updates, saving server-side encoding CPU.

---

## 23. Gateway Protocol (RDG / MS-TSGU)

RD Gateway allows RDP connections through HTTPS (port 443) firewall traversal.

```
Client ──HTTPS──► RD Gateway Server ──TCP 3389──► Target RDP Server
```

**Transport**: HTTP/HTTPS + WebSocket or HTTP/1.1 chunked transfer.

**MS-TSGU Protocol:**

Two transport modes:
1. **IN channel** (client→gateway→server): HTTP POST, chunked, long-lived
2. **OUT channel** (server→gateway→client): HTTP GET or WebSocket

The gateway encapsulates RDP PDUs in HTTP DATA packets:
```
PKT_TYPE_HEADER          0x01  — Connection establishment
PKT_TYPE_RESPONSE        0x02
PKT_TYPE_CLOSE_CHANNEL   0x03
PKT_TYPE_TUNNEL_CREATE   0x04  — Create tunnel to target
PKT_TYPE_TUNNEL_RESPONSE 0x05
PKT_TYPE_TUNNEL_AUTH     0x06  — Authenticate tunnel
PKT_TYPE_CHANNEL_CREATE  0x08  — Create data channel within tunnel
PKT_TYPE_CHANNEL_RESPONSE 0x09
PKT_TYPE_DATA            0x0A  — Actual RDP data
PKT_TYPE_SERVICE_MESSAGE 0x0B
PKT_TYPE_REAUTH_MESSAGE  0x0C
PKT_TYPE_KEEPALIVE       0x0D
PKT_TYPE_HTTP_RESPONSE   0x04 (HTTP transport variant)
```

**Authentication at gateway**: Client authenticates to gateway using Windows Auth
(NTLM/Kerberos via HTTP Negotiate). The gateway then authenticates the user's access
to the target server based on Resource Authorization Policies (RAPs) and
Connection Authorization Policies (CAPs).

---

## 24. Load Balancing (MS-RDPBCGR Cookie)

For Terminal Services farms, load balancing uses a **routing token** embedded in the
X.224 CR-TPDU.

**Cookie format:**
```
"Cookie: mstshash=<username>\r\n"
```

More specifically, the routing token contains either:
- A cookie with the username (for name-based routing)
- An `msts=<session_token>` value (for reconnecting to an existing session)

Network load balancers (NLB or RD Connection Broker) parse this token from the initial
X.224 connection request (before any TLS handshake) to route to the appropriate session
host in the farm.

**RD Connection Broker Redirection** (server-side redirect):

After initial connection, the server can send a **Redirect PDU** to move the client
to a different server:
```
Server Redirection PDU (SEC_REDIRECTION_PKT):
  flags
  sessionID        (target session to reconnect to)
  redirectedSessionID (for seamless reconnect)
  targetNetAddress (IP or FQDN to connect to)
  cookie           (load balancing cookie for target)
  username, domain, password (pre-populated for seamless reconnect)
  targetCertificate (X.509 DER for the target server)
```

The client receives this, disconnects, and re-connects to the target address using
the provided cookie and optionally the credentials.

---

## 25. RDP over UDP (MS-RDPEUDP)

RDP 8.0 introduced a parallel **UDP transport** to improve performance over lossy networks
(primarily WiFi and WAN). The UDP transport runs alongside (not replacing) TCP.

**Two UDP modes:**
```
RDPEUDP_MODE_1: Reliable UDP (RDPEUDP)     — with retransmission, in-order delivery
RDPEUDP_MODE_2: Lossy UDP (RDPEUDP2)       — no retransmission, for real-time data
```

**UDP Connection Setup:**
```
TCP RDP connection is established first.
Server → Client (on TCP I/O channel): Server-to-Client sequence initiation
Client → Server: RDPEUDP SYN (on UDP port 3389)
Server → Client: RDPEUDP SYN+ACK
Client → Server: RDPEUDP ACK
DTLS handshake on the UDP channel (CredSSP validation)
Virtual channels migrate from TCP to UDP (or new channels on UDP)
```

**RDPEUDP Packet structure:**
```
RDPUDP_FEC_HEADER:
  snSourceAck  (4 bytes): last sequence number ACKed
  uReceiveWindowSize (2 bytes): receive window
  uFlags (2 bytes): SYN/SYN_ACK/FEC_PRESENT/SNACK_PRESENT/ACK_OF_ACKS/...

[RDPUDP_FEC_PAYLOAD_HEADER]:
  snCoded     (4 bytes): coded sequence number
  snSourceStart (4 bytes): source start for FEC group
  uSourceRange  (1 byte): FEC group size
  uFECIndex     (1 byte): position in FEC group

[RDPUDP_SOURCE_PAYLOAD_HEADER]:
  snSourceStart, snCoded

[RDPUDP_SYNDATAEX_PAYLOAD]:  (in SYN packets)
  uSynEx flags
  uUdpVer: version 2=RDPEUDP2
  uCookieHash: for connecting to correct session
  uReceiveWindowSize

payload: actual data
```

**Forward Error Correction (FEC)** in RDPEUDP:
- Sender groups N source packets + M parity packets per FEC group
- Parity = XOR of source packets in group
- If any ≤M packets are lost, receiver reconstructs from parity
- This eliminates retransmits for small loss rates, reducing latency

---

## 26. Vulnerability Anatomy

### 26.1 MS12-020 (DoS)

**CVE-2012-0002** — March 2012, affects RDP pre-auth.

Root cause: Integer/memory issue in the RDP kernel-mode driver (`rdpwd.sys`) when handling
malformed X.224 Connection Request PDUs with specific `rdpNegReq` structures.

An unauthenticated attacker could send a crafted PDU that causes a NULL pointer dereference
in kernel space, resulting in BSOD (system crash).

### 26.2 MS15-067 and MS15-082

**CVE-2015-2373 / CVE-2015-2546** — Remote Desktop Service vulnerabilities in Windows 7/2008.

- MS15-067: Remote code execution in RDP via malformed packet before authentication.
- MS15-082: Man-in-the-Middle attack on TS Web Access leading to RCE.

### 26.3 BlueKeep — CVE-2019-0708

**One of the most critical Windows vulnerabilities in recent history.**

**Affected versions**: Windows XP, Vista, 7, Server 2003, Server 2008 (pre-NLA only)
**Severity**: CVSS 9.8 — **Pre-auth, unauthenticated, wormable RCE**

**Root cause** (detailed):

The vulnerability lies in the **MS_T120 channel** handling in `termdd.sys`
(Windows Terminal Services kernel driver):

```
MS_T120 is a legacy T.120 virtual channel.
It is allocated a fixed channel object at initialization.
Channel ID binding is stored in a global array indexed by channel ID.

Vulnerability: The channel object for MS_T120 is allocated early in
rdpwsx.dll (pre-authentication) and can be freed by a malformed
CHANNEL_CLOSE or deactivation PDU before proper cleanup.

The freed channel object memory is then reusable for heap spray.

Attack sequence:
  1. Connect to RDP (port 3389, no auth needed)
  2. Negotiate X.224 (no NLA selected)
  3. MCS Connect-Initial with malformed channel data
  4. Trigger MS_T120 channel binding race:
     - Bind MS_T120 to an unexpected channel ID
     - This puts a dangling pointer in the channel table
  5. Free the channel object
  6. Spray heap with controlled data (e.g., via other PDUs)
  7. The dangling pointer now points to attacker-controlled memory
  8. Trigger a virtual function call through the corrupted channel object
  9. RCE in kernel context (SYSTEM)
```

**Why wormable**: No interaction needed. A worm can scan for open port 3389, send the
exploit PDU sequence, gain SYSTEM, install backdoor/spread.

**Mitigations**:
- Enable NLA (pre-authentication validates user before any channel setup)
- Firewall port 3389 from public internet
- Apply MS patch (KB4499175 etc.)
- Disable MS_T120 binding (registry workaround)

### 26.4 DejaBlue — CVE-2019-1181/1182

Similar to BlueKeep but affects **Windows 8, 10, Server 2012–2019** (i.e., patched
BlueKeep systems).

Root cause: Integer overflow in `rdpbase.dll` when parsing the **BitmapCacheV3 codec**
capability. The `numCells` field controls allocation size; an integer overflow causes
under-allocation, then a heap buffer overflow when cells are written.

```
Exploitation path:
  1. Pre-auth (RDP without NLA, or before auth completes in capability exchange)
  2. Send Confirm Active PDU with crafted CAPSTYPE_BITMAP_CACHE_REV2
     with numCells causing overflow in: size = numCells * sizeof(BITMAP_CACHE_CELL)
  3. Under-allocated buffer is written beyond its bounds
  4. Heap overflow → RCE via heap corruption primitives
```

### 26.5 PrintNightmare via RDP Printer Channel

PrintNightmare (CVE-2021-1675 / CVE-2021-34527) is a Windows Print Spooler vulnerability.
The RDP printer redirection channel (`rdpdr`, printer type) was one attack vector because:

1. RDP client redirects a printer to the server
2. Server's Print Spooler attempts to install the driver for the redirected printer
3. If the printer announces a malicious driver DLL path, the Spooler (running as SYSTEM)
   loads it → RCE as SYSTEM

**Mitigations**: Disable printer redirection in RDP, or patch the Print Spooler.

---

## 27. RDP Specification References (MS-RDPBCGR)

Microsoft publishes the complete RDP specification as open protocol documents.
The base protocol is **MS-RDPBCGR** (Remote Desktop Protocol: Basic Connectivity
and Graphics Remoting). Key documents:

```
Core Protocol:
  [MS-RDPBCGR]    Basic Connectivity and Graphics Remoting
  [MS-RDPEGDI]    GDI Orders Protocol
  [MS-RDPECLIP]   Clipboard (CLIPRDR)
  [MS-RDPEFS]     File System Virtual Channel (RDPDR filesystem part)
  [MS-RDPESP]     Shadow (Multiparty)
  [MS-RDPEDYC]    Dynamic Virtual Channel (DRDYNVC)
  [MS-RDPEGFX]    Graphics Pipeline (EGFX, H.264, Progressive)
  [MS-RDPERP]     Remote Programs (RAIL/RemoteApp)
  [MS-RDPEUSB]    USB Redirection (URBDRC)
  [MS-RDPEUDP]    UDP Transport Extension
  [MS-RDPEI]      Input Virtual Channel (touch/pen)
  [MS-RDPEDP]     Display Control Virtual Channel
  [MS-RDPELE]     Licensing
  [MS-CSSP]       CredSSP (NLA)
  [MS-TSGU]       Terminal Services Gateway
  [MS-TSRAP]      TS Resource Authorization Protocol
  [MS-TSWEBPROXY] TS Web Access Proxy

All available at: https://docs.microsoft.com/en-us/openspecs/windows_protocols/
```

---

## 28. Implementing an RDP Client — Architectural Decisions

### Protocol State Machine

```
States:
  DISCONNECTED
  TCP_CONNECTING
  X224_HANDSHAKE
  TLS_HANDSHAKE       (if NLA or SSL)
  CREDSSP_AUTH        (if NLA)
  MCS_CONNECT
  MCS_ERECT
  MCS_ATTACH_USER
  MCS_CHANNEL_JOIN    (multiple channels)
  SECURITY_EXCHANGE   (if classic RDP)
  LICENSING
  CAPABILITIES
  FINALIZATION
  ACTIVE
  RECONNECTING
  DISCONNECTING

Transitions are driven by received PDU types and internal events.
```

### Goroutine/Thread Architecture (Go example)

```
┌─────────────────────────────────────────────────────────────────┐
│                        RDP Client Process                        │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ TCP Recv     │    │ PDU Router   │    │  UI/Render Thread│  │
│  │ goroutine    │───►│  goroutine   │───►│  (surface decode)│  │
│  │ (ring buffer)│    │ (TPKT/X224/  │    │                  │  │
│  └──────────────┘    │  MCS/RDP     │    └──────────────────┘  │
│                      │  demux)      │                           │
│  ┌──────────────┐    └──────┬───────┘    ┌──────────────────┐  │
│  │ TCP Send     │◄──────────┤            │ Virtual Channel  │  │
│  │ goroutine    │           │            │ Dispatchers      │  │
│  │ (write queue)│    ┌──────▼───────┐    │ (CLIPRDR, RDPDR) │  │
│  └──────────────┘    │ Input Event  │    └──────────────────┘  │
│                      │ goroutine    │                           │
│                      │ (keyboard,   │                           │
│                      │  mouse)      │                           │
│                      └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### Key Implementation Components

**TPKT Framing:**
```rust
// Rust: Reading a complete TPKT PDU
async fn read_tpkt(stream: &mut TlsStream<TcpStream>) -> Result<Vec<u8>> {
    let mut header = [0u8; 4];
    stream.read_exact(&mut header).await?;
    assert_eq!(header[0], 3, "Expected TPKT version 3");
    let length = u16::from_be_bytes([header[2], header[3]]) as usize;
    let mut payload = vec![0u8; length - 4];
    stream.read_exact(&mut payload).await?;
    Ok(payload)
}
```

**X.224 DT-TPDU:**
```rust
// Skip X.224 DT header (always 3 bytes for RDP: LI=2, type=0xF0, EOT=0x80)
fn parse_x224_dt(data: &[u8]) -> Result<&[u8]> {
    if data.len() < 3 || data[1] != 0xF0 {
        return Err(Error::InvalidX224);
    }
    Ok(&data[3..])
}
```

**MCS BER parsing**: The BER encoding requires a proper recursive descent parser.
The tricky parts:
- Variable-length BER tags (1–4 bytes)
- Variable-length BER lengths (definite and indefinite)
- MCS `DomainParameters` with multiple INTEGER fields

**ASN.1 PER for GCC**: Even trickier — PER is bit-aligned, not byte-aligned.
Most implementations use a pre-built binary blob for the GCC portion rather than
a proper PER encoder.

**Capability set parsing**: A `HashMap<u16, CapabilitySet>` keyed by type.
Parse each cap set based on `capabilitySetType`, storing only what you need.

**RC4 state machine**: For classic RDP security, maintain separate RC4 states for
encrypt and decrypt (they are independent streams). Update keys after every 4096 packets.

**Bitmap decompression**: Implement the RDP 5.x RLE algorithm. Validate carefully —
malformed compression data from a server could be a security issue.

**Order rendering**: Use the `orderSupport` bitmask to advertise only orders your
renderer can handle. For simple clients: advertise 0 orders and rely on bitmap updates.

### Critical Gotchas

1. **Endianness**: TPKT length is big-endian. RDP PDU fields are little-endian.
   ASN.1 BER integers are big-endian. Do not confuse them.

2. **Unicode strings**: RDP uses UTF-16LE for all strings. Client name, domain, etc.
   Null-pad to fixed buffer sizes.

3. **Sequence numbers**: Classic RDP security tracks sequence numbers for MAC. Sequence
   number is **not** transmitted — both sides maintain it independently. Increment on
   every encrypted PDU sent.

4. **Channel join order**: Must join User Channel, then I/O Channel (1002), then SVCs.
   Attempting to join I/O before User Channel causes the server to drop the connection.

5. **Fast-path vs slow-path**: Server can switch between them at any time. Both must
   be supported simultaneously.

6. **MCS PDU length encoding**: Short form (1 byte, ≤127) vs long form (3 bytes for
   RDPBCGR). TPKT length is always 2 bytes BE.

---

## 29. Implementing an RDP Server — Architectural Decisions

Implementing a server is more complex than a client because you must:
- Generate RSA keys and a self-signed X.509 certificate
- Handle CredSSP/TLS termination
- Manage multiple concurrent sessions
- Implement a graphics capture pipeline
- Implement session persistence and reconnect

### Session Architecture

```
Per-session process/thread model (Windows approach):
  csrss.exe  — Console subsystem (one per session)
  winlogon.exe — Logon/unlock UI
  rdpclip.exe  — Clipboard service
  rdpdr.exe    — Device redirection service

RDP-specific kernel driver:
  termdd.sys   — Transport (RDPWD), MCS, channel management
  rdpwsx.dll   — Usermode portion of terminal services stack
  rdpbase.dll  — RDP core protocol engine

Graphics capture:
  Legacy: GDI hooking (DrvXxx miniport callbacks)
  Modern: DXGI Desktop Duplication API (DirectX)
  RemoteFX: vGPU capture via DirectX remoting
```

### Graphics Capture Pipeline (for custom servers)

```
DXGI Desktop Duplication (Windows 8+):
  IDXGIOutputDuplication::AcquireNextFrame()
  → FrameInfo.TotalMetadataBufferSize > 0: dirty regions
  → GetFrameDirtyRects() → rectangles that changed
  → GetFrameMoveRects() → scrolling regions (destination=source move)
  → Map desktop surface → copy pixel data

For each dirty rect:
  Encode with H.264/RemoteFX/RDP compression
  Wrap in EGFX RDPGFX_CMDID_WIRETOSURFACE_2
  Send via drdynvc "Microsoft::Windows::RDS::Graphics" channel

Move rects can be expressed as RDPGFX_CMDID_SURFACETOSURFACE (GPU blit) —
much cheaper than re-encoding.
```

### Server Key Components

```rust
// Server state per connection
struct RdpServerSession {
    state: SessionState,
    tcp: TlsStream<TcpStream>,
    session_id: u32,
    share_id: u32,
    user_channel_id: u16,
    io_channel_id: u16,  // always 1002
    svc_channels: HashMap<u16, &'static str>,  // channel_id -> name
    server_random: [u8; 32],
    // security keys (if classic RDP):
    mac_key: [u8; 16],
    encrypt_key: [u8; 16],
    decrypt_key: [u8; 16],
    encrypt_count: u32,
    decrypt_count: u32,
    // capabilities (from Confirm Active):
    client_caps: HashMap<u16, Vec<u8>>,
    // EGFX state:
    egfx_channel_id: Option<u32>,  // DVC channel ID
    frame_id: u32,
    unacked_frames: VecDeque<u32>,
}
```

---

## 30. Wireshark Dissection and Protocol Analysis

### Decryption in Wireshark

For TLS-encrypted sessions, Wireshark can decrypt if you have:
- The server's RSA private key (pre-TLS 1.3): add in Preferences → Protocols → TLS → RSA keys
- TLS session keys via `SSLKEYLOGFILE` environment variable on the client

For classic RDP security (RC4), Wireshark has limited built-in support.

### Key Dissectors

```
tpkt:      TPKT framing
cotp:      X.224/ISO 8073 (COTP)
t125:      MCS
gcc:       GCC Conference Create
rdp:       RDP core protocol
rdpbcgr:   Capability sets, Demand/Confirm Active
rdpclip:   Clipboard (CLIPRDR)
rdpdr:     Drive/Device redirection
rdpsnd:    Audio redirection
drdynvc:   Dynamic virtual channel
rdpegfx:   Enhanced graphics
```

### Useful Display Filters

```
rdp                            — all RDP traffic
rdp.pduType == 1               — Demand Active (server capabilities)
rdp.pduType == 3               — Confirm Active (client capabilities)
rdp.pduType2 == 2              — Graphics updates
rdp.pduType2 == 28             — Input events
rdpclip                        — clipboard operations
rdpdr                          — device redirection
rdpegfx.cmdId == 0x000B        — EGFX frame start
rdpegfx.cmdId == 0x000C        — EGFX frame end
```

### Packet Timeline: Typical RDP Session

```
Frame  1:  TCP SYN
Frame  2:  TCP SYN-ACK
Frame  3:  TCP ACK
Frame  4:  X.224 CR (RDP Negotiation Request, PROTOCOL_HYBRID)
Frame  5:  X.224 CC (RDP Negotiation Response, selectedProtocol=HYBRID)
Frame  6:  TLS ClientHello
Frame  7:  TLS ServerHello + Certificate + ServerHelloDone
Frame  8:  TLS ClientKeyExchange + ChangeCipherSpec + Finished
Frame  9:  TLS ChangeCipherSpec + Finished (server)
[all subsequent frames are inside TLS]
Frame 10:  CredSSP TSRequest (negoTokens: NTLM NEGOTIATE)
Frame 11:  CredSSP TSRequest (negoTokens: NTLM CHALLENGE)
Frame 12:  CredSSP TSRequest (negoTokens: NTLM AUTH + pubKeyAuth)
Frame 13:  CredSSP TSRequest (pubKeyAuth echo)
Frame 14:  CredSSP TSRequest (authInfo: credentials)
Frame 15:  MCS Connect-Initial (GCC Conference Create Request)
Frame 16:  MCS Connect-Response (GCC Conference Create Response)
Frame 17:  MCS Erect Domain Request
Frame 18:  MCS Attach User Request
Frame 19:  MCS Attach User Confirm
Frame 20:  MCS Channel Join Request (User Channel)
Frame 21:  MCS Channel Join Confirm
Frame 22:  MCS Channel Join Request (I/O Channel 1002)
Frame 23:  MCS Channel Join Confirm
Frame 24:  MCS Channel Join Request (cliprdr)
Frame 25:  MCS Channel Join Confirm
... (more channel joins)
Frame 30:  TS_INFO_PACKET (user credentials, performance flags)
Frame 31:  License Request
Frame 32:  New License Request
Frame 33:  Platform Challenge
Frame 34:  Platform Challenge Response
Frame 35:  License Error STATUS_VALID_CLIENT
Frame 36:  Demand Active PDU (server capabilities)
Frame 37:  Confirm Active PDU (client capabilities)
Frame 38:  Synchronize PDU (client)
Frame 39:  Control PDU Cooperate (client)
Frame 40:  Control PDU Request Control (client)
Frame 41:  Font List PDU (client)
Frame 42:  Synchronize PDU (server)
Frame 43:  Control PDU Cooperate (server)
Frame 44:  Control PDU Granted Control (server)
Frame 45:  Font Map PDU (server)
--- SESSION NOW ACTIVE ---
Frame 46+: Bitmap Updates, GDI Orders, Input Events, SVC data...
```

---

## Appendix A: Complete RDP Security Flag Reference

```
Security flags in RDP Security Header:
Bit  Hex Value   Name                        Direction  Description
───────────────────────────────────────────────────────────────────────
0    0x0001  SEC_EXCHANGE_PKT            C→S  Security Exchange PDU
1    0x0002  SEC_TRANSPORT_REQ           C→S  Transport request (unused)
2    0x0004  (reserved)
3    0x0008  SEC_ENCRYPT                 Both PDU body is RC4 encrypted
4    0x0010  SEC_RESET_SEQNO             Both Reset MAC sequence number
5    0x0020  SEC_IGNORE_SEQNO            Both Don't check MAC seq number
6    0x0040  SEC_INFO_PKT                C→S  Contains TS_INFO_PACKET
7    0x0080  SEC_LICENSE_PKT             Both Contains licensing PDU
8    0x0100  (reserved)
9    0x0200  SEC_LICENSE_ENCRYPT_CS      C→S  Encrypted licensing (C→S)
9    0x0200  SEC_LICENSE_ENCRYPT_SC      S→C  Encrypted licensing (S→C)
10   0x0400  SEC_REDIRECTION_PKT         Both Auto-reconnect redirect
11   0x0800  SEC_SECURE_CHECKSUM         Both Use salted MAC calculation
12   0x1000  SEC_AUTODETECT_REQ          S→C  Bandwidth detection req
13   0x2000  SEC_AUTODETECT_RSP          C→S  Bandwidth detection resp
14   0x4000  SEC_HEARTBEAT               Both Heartbeat PDU
15   0x8000  SEC_FLAGSHI_VALID           Both flagsHi field is present/valid
```

## Appendix B: NTSTATUS Codes in RDPDR

```
STATUS_SUCCESS               0x00000000
STATUS_NO_MORE_FILES         0x80000006  (end of directory listing)
STATUS_UNSUCCESSFUL          0xC0000001
STATUS_NOT_IMPLEMENTED       0xC0000002
STATUS_INVALID_PARAMETER     0xC000000D
STATUS_NO_SUCH_FILE          0xC000000F
STATUS_ACCESS_DENIED         0xC0000022
STATUS_OBJECT_NAME_NOT_FOUND 0xC0000034
STATUS_OBJECT_NAME_COLLISION 0xC0000035
STATUS_DISK_FULL             0xC000007F
STATUS_FILE_IS_A_DIRECTORY   0xC00000BA
STATUS_NOT_A_DIRECTORY       0xC0000103
```

## Appendix C: RDP Error Codes (ERRINFO)

```
Sent in PDUTYPE2_SET_ERROR_INFO_PDU:
0x00000000  ERRINFO_SUCCESS
0x00000001  ERRINFO_RPC_INITIATED_DISCONNECT
0x00000002  ERRINFO_RPC_INITIATED_LOGOFF
0x00000003  ERRINFO_IDLE_TIMEOUT
0x00000004  ERRINFO_LOGON_TIMEOUT
0x00000005  ERRINFO_DISCONNECTED_BY_OTHERCONNECTION
0x00000006  ERRINFO_OUT_OF_MEMORY
0x00000007  ERRINFO_SERVER_DENIED_CONNECTION
0x00000009  ERRINFO_SERVER_INSUFFICIENT_PRIVILEGES
0x0000000A  ERRINFO_SERVER_FRESH_CREDENTIALS_REQUIRED
0x0000000B  ERRINFO_RPC_INITIATED_DISCONNECT_BYUSER
0x0000000C  ERRINFO_LOGOFF_BY_USER
0x00000100  ERRINFO_LICENSE_INTERNAL
0x00000101  ERRINFO_LICENSE_NO_LICENSE_SERVER
0x00000102  ERRINFO_LICENSE_NO_LICENSE
0x00000103  ERRINFO_LICENSE_BAD_CLIENT_MSG
0x00000104  ERRINFO_LICENSE_HWID_DOESNT_MATCH_LICENSE
0x00000105  ERRINFO_LICENSE_BAD_CLIENT_LICENSE
0x00000106  ERRINFO_LICENSE_CANT_FINISH_PROTOCOL
0x00000107  ERRINFO_LICENSE_CLIENT_ENDED_PROTOCOL
0x00000108  ERRINFO_LICENSE_BAD_CLIENT_ENCRYPTION
0x00000109  ERRINFO_LICENSE_CANT_UPGRADE_LICENSE
0x0000010A  ERRINFO_LICENSE_NO_REMOTE_CONNECTIONS
```

## Appendix D: GDI Order Type Reference

```
Type  Name                       Class
────────────────────────────────────────────────────────────────
0x00  DstBlt                     Primary
0x01  PatBlt                     Primary
0x02  ScrBlt                     Primary
0x07  DrawNineGrid               Primary
0x08  MultiDrawNineGrid          Primary
0x09  LineTo                     Primary
0x0A  OpaqueRect                 Primary
0x0B  SaveBitmap                 Primary (save to server-side bitmap store)
0x0F  MemBlt                     Primary (blit from cache)
0x10  Mem3Blt                    Primary (blit from cache with brush)
0x14  MultiDstBlt                Primary
0x15  MultiPatBlt                Primary
0x16  MultiScrBlt                Primary
0x17  MultiOpaqueRect            Primary
0x1A  FastIndex                  Primary (fast glyph draw)
0x1B  PolygonSC                  Primary
0x1C  PolygonCB                  Primary
0x1D  Polyline                   Primary
0x1E  FastGlyph                  Primary (alternate fast glyph)
0x1F  EllipseSC                  Primary
0x20  EllipseCB                  Primary
0x21  GlyphIndex                 Primary (general glyph)
─────────────────────────────
Secondary orders (follow SECONDARY-flagged control byte):
0x00  CacheBitmap                Secondary (cache a bitmap in cell cache)
0x01  CacheColorTable            Secondary
0x02  CacheGlyph                 Secondary (add glyph to glyph cache)
0x03  CacheBitmapV2              Secondary (RDP 5 cache)
0x04  CacheGlyphV2               Secondary
0x05  CacheBrush                 Secondary (store brush pattern)
0x07  CacheBitmapV3              Secondary (RDP 6 cache)
─────────────────────────────
Alternate secondary orders (ALTSEC flag):
0x00  SwitchSurface              (switch to offscreen surface)
0x01  CreateOffscreenBitmap      (allocate offscreen surface)
0x02  StreamBitmapFirst          (begin streaming bitmap update)
0x03  StreamBitmapNext           (continue streaming)
0x04  CreateNineGridBitmap       (nine-grid scaling resource)
0x06  FrameMarker                (frame begin/end)
0x07  SetSurfaceBits             (surface bits with compression)
0x08  StreamBitmapFirstV2
0x09  StreamBitmapNextV2
0x0A  CreateOffscreenBitmapV2
```

---

*End of RDP Complete Reference Guide*
*Specification baseline: MS-RDPBCGR v58.0 (2023), MS-RDPEGFX v34.0 (2023)*
*Protocol version coverage: RDP 4.0 through RDP 10.9*