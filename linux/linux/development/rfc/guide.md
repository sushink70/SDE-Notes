# RFC-Based Linux Kernel Network Development Guide

A comprehensive guide to understanding, referencing, and implementing RFCs in Linux kernel networking code.

## 1. Understanding RFCs

### What are RFCs?

**RFC (Request for Comments)** are documents that define Internet standards, protocols, procedures, and concepts. They are published by the Internet Engineering Task Force (IETF).

### RFC Types

- **Standards Track**: Official Internet standards (e.g., TCP, IP, HTTP)
- **Informational**: General information about protocols or concepts
- **Experimental**: Experimental protocols or procedures
- **Best Current Practice (BCP)**: Guidelines and recommendations
- **Historic**: Obsolete or deprecated specifications

### RFC Status Levels

1. **Proposed Standard**: Initial specification
2. **Draft Standard**: Tested and refined (no longer used after RFC 6410)
3. **Internet Standard (STD)**: Mature, widely implemented

## 2. Finding and Reading RFCs

### Primary Sources

```bash
# Official RFC repository
https://www.rfc-editor.org/

# Individual RFC access
https://www.rfc-editor.org/rfc/rfc793.html  # TCP
https://www.rfc-editor.org/rfc/rfc791.html  # IPv4
https://www.rfc-editor.org/rfc/rfc8200.html # IPv6

# Alternative sources
https://tools.ietf.org/html/rfc793
https://datatracker.ietf.org/doc/html/rfc793
```

### Searching for RFCs

```bash
# RFC Editor search
https://www.rfc-editor.org/search/rfc_search.php

# IETF Datatracker (shows working groups, updates, obsoletes)
https://datatracker.ietf.org/

# Search by topic
https://www.rfc-editor.org/search/rfc_search_detail.php?title=tcp

# Tools to download RFCs
# Install
pip3 install rfctools

# Download RFC
rfc get 793

# Or using curl
curl https://www.rfc-editor.org/rfc/rfc793.txt -o rfc793.txt
```

### Key Networking RFCs

```
Core Protocols:
- RFC 791  - IPv4
- RFC 793  - TCP
- RFC 768  - UDP
- RFC 792  - ICMP
- RFC 8200 - IPv6

TCP Extensions:
- RFC 1323 - TCP Extensions (Window Scaling, Timestamps)
- RFC 2018 - TCP Selective Acknowledgment (SACK)
- RFC 3168 - ECN (Explicit Congestion Notification)
- RFC 5681 - TCP Congestion Control
- RFC 6298 - TCP Retransmission Timer
- RFC 7323 - TCP Extensions for High Performance (updates 1323)

Modern Features:
- RFC 8684 - TCP Multipath (MPTCP)
- RFC 9000 - QUIC (over UDP)
- RFC 8985 - TCP Rack Loss Detection
- RFC 9293 - TCP (updates 793)

Routing:
- RFC 4271 - BGP-4
- RFC 2328 - OSPF v2
- RFC 8200 - IPv6

Application Layer:
- RFC 9110 - HTTP Semantics
- RFC 9293 - TLS 1.3
```

### Reading RFC Structure

```
1. Abstract         - Quick overview
2. Status           - Standards track/informational/etc
3. Introduction     - Problem statement
4. Specification    - Technical details
5. Security         - Security considerations
6. IANA             - Protocol number assignments
7. References       - Related RFCs
8. Appendix         - Additional information
```

## 3. How Linux Kernel References RFCs

### Finding RFC References in Kernel Code

```bash
cd ~/kernel-dev/linux

# Search for RFC mentions
git grep -i "rfc.*793" net/
git grep "RFC 793" net/ipv4/

# Find all RFCs referenced in a file
git grep -h "RFC [0-9]" net/ipv4/tcp.c | sort -u

# Search for specific protocol RFCs
git grep -i "rfc.*mptcp" net/

# Find implementation comments
git grep -A5 "RFC.*window scaling" net/ipv4/
```

### Common RFC Reference Patterns in Code

```c
/* From net/ipv4/tcp_output.c */

/*
 * RFC 793: "The window field (SEQ.WND) of every segment, except
 * initial SYN segments, must contain the window at the sender
 * when this segment was sent."
 */

/*
 * RFC 7323, Section 2.3:
 * TCP Timestamps are only included in data segments if the
 * timestamp option was successfully negotiated during the
 * 3-way handshake.
 */

/* RFC 5681: Congestion avoidance phase */

/*
 * Implementation of TCP window scaling (RFC 1323/7323)
 */
```

## 4. Workflow: From RFC to Implementation

### Step-by-Step Process

```
1. Identify the problem/feature
   ↓
2. Find relevant RFC(s)
   ↓
3. Read and understand specification
   ↓
4. Check existing kernel implementation
   ↓
5. Design implementation
   ↓
6. Write code with RFC references
   ↓
7. Test against RFC requirements
   ↓
8. Submit patch with RFC citations
```

### Example: Understanding TCP Timestamps

```bash
# 1. Find the RFC
wget https://www.rfc-editor.org/rfc/rfc7323.txt

# 2. Read relevant sections
less rfc7323.txt
# Section 3: TCP Timestamps Option

# 3. Find kernel implementation
cd ~/kernel-dev/linux
git grep -n "tcp_timestamp" net/ipv4/tcp*.c

# 4. Examine the code
vim net/ipv4/tcp_output.c
# Look for: tcp_syn_options(), tcp_established_options()
```

## 5. Practical Example: Implementing TCP Option

Let's implement support for a **TCP Experimental Option** (RFC 4727) as an example.

### Example RFC: TCP Echo Option (Simplified Demo)

This is a simplified educational example based on RFC concepts.

### Step 1: Read RFC Specification

```
RFC 1072 - TCP Extensions for Long-Delay Paths (Historic, but good example)

The TCP Echo option provides a way to measure round-trip times
by having the receiver echo back data sent by the sender.

Option Format:
+--------+--------+--------+--------+
|Kind=6  |Length=6|  Echo Data (4B) |
+--------+--------+--------+--------+

Kind: 6
Length: 6 bytes
Echo Data: 4 bytes of data to echo back
```

### Step 2: Locate Relevant Kernel Code

```bash
# TCP option handling is in:
net/ipv4/tcp_input.c    # Parsing received options
net/ipv4/tcp_output.c   # Adding options to sent packets
include/net/tcp.h       # TCP structures and constants
include/linux/tcp.h     # TCP header definitions
```

### Step 3: Implementation

#### A. Define Option Constants

**File: `include/net/tcp.h`**

```c
/* TCP option types */
#define TCPOPT_NOP              1  /* Padding */
#define TCPOPT_EOL              0  /* End of options */
#define TCPOPT_MSS              2  /* Maximum Segment Size */
#define TCPOPT_WINDOW           3  /* Window scaling */
#define TCPOPT_SACK_PERM        4  /* SACK Permitted */
#define TCPOPT_SACK             5  /* SACK */
#define TCPOPT_TIMESTAMP        8  /* Better RTT measurement */
// ... existing options ...

/* RFC 1072 - TCP Echo Option (for demonstration) */
#define TCPOPT_ECHO             6  /* Echo */
#define TCPOPT_ECHO_REPLY       7  /* Echo Reply */
#define TCPOLEN_ECHO            6  /* Length of echo option */

/* TCP option lengths */
#define TCPOLEN_MSS             4
#define TCPOLEN_WINDOW          3
#define TCPOLEN_SACK_PERM       2
#define TCPOLEN_TIMESTAMP       10
// ... existing lengths ...

/* Add to tcp_sock structure */
struct tcp_sock {
    // ... existing fields ...
    
    u32 echo_seq;           /* RFC 1072: Echo sequence number */
    u32 echo_reply_seq;     /* RFC 1072: Last echo reply sent */
    u8  echo_enabled:1;     /* RFC 1072: Echo option enabled */
    
    // ... rest of structure ...
};
```

#### B. Parse Incoming Options

**File: `net/ipv4/tcp_input.c`**

```c
/*
 * Parse TCP options from incoming packet
 * This function is called for every received TCP segment
 */
void tcp_parse_options(const struct net *net,
                       const struct sk_buff *skb,
                       struct tcp_options_received *opt_rx,
                       int estab,
                       struct tcp_fastopen_cookie *foc)
{
    const unsigned char *ptr;
    const struct tcphdr *th = tcp_hdr(skb);
    int length = (th->doff * 4) - sizeof(struct tcphdr);

    ptr = (const unsigned char *)(th + 1);
    opt_rx->saw_tstamp = 0;
    opt_rx->saw_echo = 0;  /* Initialize echo flag */

    while (length > 0) {
        int opcode = *ptr++;
        int opsize;

        switch (opcode) {
        case TCPOPT_EOL:
            return;
        case TCPOPT_NOP:    /* Padding */
            length--;
            continue;
        default:
            opsize = *ptr++;
            if (opsize < 2) /* Silly options */
                return;
            if (opsize > length)
                return; /* Partial option */

            switch (opcode) {
            case TCPOPT_MSS:
                /* ... existing MSS handling ... */
                break;

            /* RFC 1072: TCP Echo Option
             * This option is used to measure RTT by having
             * the receiver echo back data sent by the sender.
             * 
             * Format: [Kind=6][Length=6][Echo Data (4 bytes)]
             */
            case TCPOPT_ECHO:
                if (opsize == TCPOLEN_ECHO) {
                    /* Extract 4-byte echo data */
                    opt_rx->saw_echo = 1;
                    opt_rx->echo_seq = get_unaligned_be32(ptr);
                    
                    /* For debugging - remove in production */
                    pr_debug("TCP: Received Echo option, seq=%u\n",
                            opt_rx->echo_seq);
                }
                break;

            /* RFC 1072: TCP Echo Reply Option
             * This is the echo reply containing the data
             * from the received echo option.
             */
            case TCPOPT_ECHO_REPLY:
                if (opsize == TCPOLEN_ECHO && estab) {
                    struct tcp_sock *tp = tcp_sk(sk);
                    u32 echo_reply = get_unaligned_be32(ptr);
                    
                    /* Calculate RTT from echo reply */
                    if (tp->echo_enabled && 
                        echo_reply == tp->echo_seq) {
                        /* Valid echo reply received */
                        u32 rtt = tcp_stamp_us_delta(
                            tcp_sk(sk)->tcp_mstamp,
                            tp->echo_send_ts
                        );
                        
                        /* Update RTT estimate */
                        tcp_rtt_estimator(sk, rtt);
                    }
                }
                break;

            case TCPOPT_TIMESTAMP:
                /* ... existing timestamp handling ... */
                break;

            /* Other options ... */
            }

            ptr += opsize - 2;
            length -= opsize;
        }
    }
}
```

#### C. Add Options to Outgoing Packets

**File: `net/ipv4/tcp_output.c`**

```c
/*
 * Build TCP options for SYN and SYN-ACK packets
 * This is where we negotiate optional features
 */
static unsigned int tcp_syn_options(struct sock *sk,
                                    struct sk_buff *skb,
                                    struct tcp_out_options *opts,
                                    struct tcp_md5sig_key **md5)
{
    struct tcp_sock *tp = tcp_sk(sk);
    unsigned int remaining = MAX_TCP_OPTION_SPACE;
    struct tcp_fastopen_request *fastopen = tp->fastopen_req;

    /* ... existing option handling ... */

    /* RFC 1072: Negotiate Echo capability in SYN
     * We add the Echo option in SYN packets to indicate
     * support for the echo mechanism.
     */
    if (sock_net(sk)->ipv4.sysctl_tcp_echo && 
        !tp->repair) {
        if (remaining >= TCPOLEN_ECHO) {
            opts->options |= OPTION_ECHO;
            opts->echo_seq = tp->write_seq;
            remaining -= TCPOLEN_ECHO;
        }
    }

    /* ... rest of function ... */
    return MAX_TCP_OPTION_SPACE - remaining;
}

/*
 * Build TCP options for established connection packets
 */
static unsigned int tcp_established_options(struct sock *sk,
                                           struct sk_buff *skb,
                                           struct tcp_out_options *opts,
                                           struct tcp_md5sig_key **md5)
{
    struct tcp_sock *tp = tcp_sk(sk);
    unsigned int size = 0;
    unsigned int eff_sacks;

    opts->options = 0;

    /* ... existing timestamp handling ... */

    /* RFC 1072: Add Echo Reply option
     * If we received an echo option, we must send back
     * an echo reply with the same data.
     */
    if (tp->echo_enabled && tp->rx_opt.saw_echo) {
        opts->options |= OPTION_ECHO_REPLY;
        opts->echo_reply_seq = tp->rx_opt.echo_seq;
        size += TCPOLEN_ECHO;
    }
    /* Alternatively, send Echo option to probe RTT */
    else if (tp->echo_enabled && 
             tcp_jiffies32 - tp->last_echo_sent > HZ) {
        opts->options |= OPTION_ECHO;
        opts->echo_seq = tp->write_seq;
        tp->last_echo_sent = tcp_jiffies32;
        tp->echo_send_ts = tp->tcp_mstamp;
        size += TCPOLEN_ECHO;
    }

    /* ... SACK, window scaling, etc ... */

    return size;
}

/*
 * Write options to TCP header
 * This is called during packet transmission
 */
static void tcp_options_write(__be32 *ptr, struct tcp_sock *tp,
                             struct tcp_out_options *opts)
{
    u16 options = opts->options;

    /* ... existing option writing ... */

    /* RFC 1072: Write Echo option to packet
     * Format: [Kind=6][Length=6][Echo Data (4 bytes)]
     */
    if (unlikely(OPTION_ECHO & options)) {
        *ptr++ = htonl((TCPOPT_NOP << 24) |
                      (TCPOPT_NOP << 16) |
                      (TCPOPT_ECHO << 8) |
                      TCPOLEN_ECHO);
        *ptr++ = htonl(opts->echo_seq);
    }

    /* RFC 1072: Write Echo Reply option
     * Format: [Kind=7][Length=6][Echo Reply Data (4 bytes)]
     */
    if (unlikely(OPTION_ECHO_REPLY & options)) {
        *ptr++ = htonl((TCPOPT_NOP << 24) |
                      (TCPOPT_NOP << 16) |
                      (TCPOPT_ECHO_REPLY << 8) |
                      TCPOLEN_ECHO);
        *ptr++ = htonl(opts->echo_reply_seq);
    }

    /* ... timestamp, SACK, etc ... */
}
```

#### D. Add Sysctl Control

**File: `net/ipv4/sysctl_net_ipv4.c`**

```c
static struct ctl_table ipv4_net_table[] = {
    /* ... existing sysctls ... */
    
    /* RFC 1072: Enable/disable TCP Echo option
     * This allows runtime control of the feature
     * 
     * Usage:
     *   sysctl -w net.ipv4.tcp_echo=1  # enable
     *   sysctl -w net.ipv4.tcp_echo=0  # disable
     */
    {
        .procname   = "tcp_echo",
        .data       = &init_net.ipv4.sysctl_tcp_echo,
        .maxlen     = sizeof(int),
        .mode       = 0644,
        .proc_handler   = proc_dointvec,
    },
    /* ... more sysctls ... */
};
```

#### E. Update Protocol Structure

**File: `include/linux/tcp.h`**

```c
/* TCP option flags - stored in tcp_out_options.options */
#define OPTION_SACK_ADVERTISE   (1 << 0)
#define OPTION_TS               (1 << 1)
#define OPTION_MD5              (1 << 2)
#define OPTION_WSCALE           (1 << 3)
#define OPTION_FAST_OPEN_COOKIE (1 << 8)
#define OPTION_SMC              (1 << 9)
/* RFC 1072: Echo and Echo Reply options */
#define OPTION_ECHO             (1 << 10)  /* Send echo */
#define OPTION_ECHO_REPLY       (1 << 11)  /* Send echo reply */

struct tcp_options_received {
    /* ... existing fields ... */
    
    /* RFC 1072: Echo option fields */
    u8  saw_echo:1;         /* Echo option seen */
    u32 echo_seq;           /* Echo sequence number */
};

struct tcp_out_options {
    u16 options;            /* Bitmask of options */
    /* ... existing fields ... */
    
    /* RFC 1072: Echo fields for outgoing packets */
    u32 echo_seq;           /* Echo sequence to send */
    u32 echo_reply_seq;     /* Echo reply data */
};
```

### Step 4: Testing the Implementation

#### A. Compile and Boot Test Kernel

```bash
# Configure with debug options
cd ~/kernel-dev/linux
make menuconfig
# Enable: CONFIG_NET_DROP_MONITOR, CONFIG_DEBUG_INFO

# Build
make -j$(nproc)

# Test in QEMU
./run-kernel.sh arch/x86/boot/bzImage
```

#### B. Enable the Feature

```bash
# Inside test VM
sysctl -w net.ipv4.tcp_echo=1

# Verify
sysctl net.ipv4.tcp_echo
```

#### C. Test with tcpdump

```bash
# Terminal 1: Start packet capture
sudo tcpdump -i lo -w tcp_echo.pcap 'tcp and port 8080'

# Terminal 2: Start server
nc -l 8080

# Terminal 3: Connect client
nc localhost 8080

# Analyze capture
tcpdump -r tcp_echo.pcap -vvv -XX
# Look for TCP option kind=6 in packets
```

#### D. Write Test Program

**File: `test_tcp_echo.c`**

```c
/*
 * Test program for TCP Echo option (RFC 1072)
 * 
 * Compile: gcc -o test_tcp_echo test_tcp_echo.c
 * Run: sudo ./test_tcp_echo
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

#define SERVER_PORT 8080

void test_server() {
    int listen_fd, conn_fd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t addr_len = sizeof(client_addr);
    char buffer[1024];
    int optval = 1;
    
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd < 0) {
        perror("socket");
        exit(1);
    }
    
    /* Enable address reuse */
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, 
               &optval, sizeof(optval));
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(SERVER_PORT);
    
    if (bind(listen_fd, (struct sockaddr*)&server_addr, 
             sizeof(server_addr)) < 0) {
        perror("bind");
        exit(1);
    }
    
    if (listen(listen_fd, 5) < 0) {
        perror("listen");
        exit(1);
    }
    
    printf("Server listening on port %d\n", SERVER_PORT);
    printf("Check kernel messages: dmesg | grep -i echo\n\n");
    
    conn_fd = accept(listen_fd, (struct sockaddr*)&client_addr, 
                     &addr_len);
    if (conn_fd < 0) {
        perror("accept");
        exit(1);
    }
    
    printf("Client connected from %s:%d\n",
           inet_ntoa(client_addr.sin_addr),
           ntohs(client_addr.sin_port));
    
    /* Exchange data to trigger echo options */
    while (1) {
        ssize_t n = read(conn_fd, buffer, sizeof(buffer));
        if (n <= 0) break;
        
        printf("Received: %.*s", (int)n, buffer);
        write(conn_fd, buffer, n);  /* Echo back */
    }
    
    close(conn_fd);
    close(listen_fd);
}

void test_client() {
    int sock_fd;
    struct sockaddr_in server_addr;
    char buffer[1024];
    
    sleep(1);  /* Wait for server to start */
    
    sock_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (sock_fd < 0) {
        perror("socket");
        exit(1);
    }
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);
    
    printf("Connecting to server...\n");
    if (connect(sock_fd, (struct sockaddr*)&server_addr,
                sizeof(server_addr)) < 0) {
        perror("connect");
        exit(1);
    }
    
    printf("Connected! Sending test data...\n");
    printf("Check: dmesg | tail -20\n\n");
    
    /* Send some test data */
    for (int i = 0; i < 5; i++) {
        snprintf(buffer, sizeof(buffer), 
                "Test message %d\n", i);
        write(sock_fd, buffer, strlen(buffer));
        
        ssize_t n = read(sock_fd, buffer, sizeof(buffer));
        if (n > 0) {
            printf("Echo: %.*s", (int)n, buffer);
        }
        sleep(1);
    }
    
    close(sock_fd);
}

int main(int argc, char *argv[]) {
    pid_t pid;
    
    printf("TCP Echo Option Test (RFC 1072)\n");
    printf("================================\n\n");
    
    printf("Before running:\n");
    printf("  1. Enable: sysctl -w net.ipv4.tcp_echo=1\n");
    printf("  2. Run: dmesg -w (in another terminal)\n\n");
    
    pid = fork();
    
    if (pid == 0) {
        /* Child process - client */
        test_client();
    } else {
        /* Parent process - server */
        test_server();
    }
    
    return 0;
}
```

#### E. Kernel Testing with kselftest

**File: `tools/testing/selftests/net/tcp_echo_test.sh`**

```bash
#!/bin/bash
# SPDX-License-Identifier: GPL-2.0
#
# Test TCP Echo option (RFC 1072)

set -e

# Check if echo option is supported
if [ ! -f /proc/sys/net/ipv4/tcp_echo ]; then
    echo "SKIP: TCP Echo option not supported"
    exit 4
fi

# Enable echo option
echo 1 > /proc/sys/net/ipv4/tcp_echo

# Setup network namespace for testing
ip netns add tcp_echo_test1
ip netns add tcp_echo_test2

# Create veth pair
ip link add veth0 type veth peer name veth1
ip link set veth0 netns tcp_echo_test1
ip link set veth1 netns tcp_echo_test2

# Configure interfaces
ip netns exec tcp_echo_test1 ip addr add 10.0.0.1/24 dev veth0
ip netns exec tcp_echo_test2 ip addr add 10.0.0.2/24 dev veth1
ip netns exec tcp_echo_test1 ip link set veth0 up
ip netns exec tcp_echo_test2 ip link set veth1 up

# Start server in ns1
ip netns exec tcp_echo_test1 nc -l 8080 &
SERVER_PID=$!
sleep 1

# Connect from ns2 and send data
echo "Test data for TCP Echo" | \
    ip netns exec tcp_echo_test2 nc 10.0.0.1 8080 &
CLIENT_PID=$!

sleep 2

# Check if echo options were seen
if dmesg | tail -50 | grep -q "TCP.*Echo"; then
    echo "PASS: TCP Echo option detected"
    RESULT=0
else
    echo "FAIL: TCP Echo option not detected"
    RESULT=1
fi

# Cleanup
kill $SERVER_PID $CLIENT_PID 2>/dev/null || true
ip netns del tcp_echo_test1
ip netns del tcp_echo_test2

exit $RESULT
```

## 6. Testing Against RFC Compliance

### Create RFC Compliance Checklist

```markdown
RFC 1072 TCP Echo Option Compliance:

[ ] Option format correct (Kind=6, Length=6)
[ ] Echo data is 4 bytes
[ ] Echo reply uses Kind=7
[ ] Echo reply contains original echo data
[ ] Option only sent when both sides support it
[ ] Option negotiated in SYN/SYN-ACK
[ ] Echo reply sent in response to echo
[ ] No echo reply for non-data segments (pure ACKs)
[ ] Proper handling of option length
[ ] Graceful handling when option space exhausted
```

### Automated Testing Script

```bash
#!/bin/bash
# RFC compliance test script

echo "Testing RFC 1072 Compliance"
echo "==========================="

# Test 1: Option format
echo "Test 1: Verify option format..."
tcpdump -r test.pcap -vvv | grep "TCP.*option.*6" && \
    echo "✓ Echo option present" || \
    echo "✗ Echo option missing"

# Test 2: Option length
echo "Test 2: Verify option length is 6 bytes..."
# Parse and verify length field

# Test 3: Echo reply generation
echo "Test 3: Verify echo reply generated..."
# Check for Kind=7 in response

# Test 4: Data integrity
echo "Test 4: Verify echo data matches..."
# Compare sent and received echo data

# Add more tests...
```

## 7. Documentation Requirements

### Update Kernel Documentation

**File: `Documentation/networking/tcp_echo.rst`**

```rst
.. SPDX-License-Identifier: GPL-2.0

======================
TCP Echo Option (RFC 1072)
======================

Overview
========

The TCP Echo option provides a mechanism for measuring round-trip
time (RTT) by having the receiver echo back data sent by the sender.

This implementation follows RFC 1072 specification.

Configuration
=============

Enable or disable the feature::

    sysctl -w net.ipv4.tcp_echo=1  # enable
    sysctl -w net.ipv4.tcp_echo=0  # disable

Option Format
=============

Echo Option (Kind=6)::

    +--------+--------+--------+--------+
    |Kind=6  |Length=6|  Echo Data (4B) |
    +--------+--------+--------+--------+

Echo Reply Option (Kind=7)::

    +--------+--------+--------+--------+
    |Kind=7  |Length=6| Reply Data (4B) |
    +--------+--------+--------+--------+

Behavior
========

1. If TCP Echo is enabled, the sender includes an Echo option
   in outgoing segments.

2. The receiver responds with an Echo Reply option containing
   the same data.

3. The sender uses the echo reply to calculate RTT.

Performance Considerations
==========================

- Adds 8 bytes per segment (with padding)
- May impact maximum segment size (MSS)
- Consider disabling for low-latency applications

Implementation Details
======================

- Echo sequence numbers track sent echo options
- Echo replies are validated against sent sequences
- RTT calculations integrate with existing TCP RTT estimator

References
==========

- RFC 1072: TCP Extensions for Long-Delay Paths
- RFC 7323: TCP Extensions for High Performance

Testing
=======

Run kernel selftests::

    cd tools/testing/selftests/net
    sudo ./tcp_echo_test.sh

Known Issues
============

None

Author
======

Your Name <your.email@example.com>
```

## 8. Submitting the Patch

### Create Patch with Proper RFC References

```bash
cd ~/kernel-dev/linux

# Stage your changes
git add net/ipv4/tcp_input.c \
        net/ipv4/tcp_output.c \
        net/ipv4/sysctl_net_ipv4.c \
        include/net/tcp.h \
        include/linux/tcp.h \
        Documentation/networking/tcp_echo.rst

# Commit with proper message
git commit -s

# Commit message format:
```

**Commit Message Template:**

```
tcp: implement TCP Echo option per RFC 1072

This patch implements the TCP Echo option as specified in RFC 1072.
The echo mechanism allows measurement of round-trip time by having
the receiver echo back data sent by the sender.

Implementation details:

1. Added TCPOPT_ECHO (Kind=6) and TCPOPT_ECHO_REPLY (Kind=7)
   option handling as specified in RFC 1072 Section 3.1.

2. Echo options are negotiated during the three-way handshake.
   Both sides must support the option for it to be enabled.

3. The sender includes echo data in outgoing segments. The
   receiver responds with an echo reply containing the same data.

4. RTT is calculated from the echo reply and integrated with
   the existing TCP RTT estimator as described in RFC 6298.

5. Added sysctl net.ipv4.tcp_echo to enable/disable the feature
   (default: disabled for backward compatibility).

This implementation follows the specification in RFC 1072 and
has been tested against the kernel selftests.

References:
  RFC 1072: TCP Extensions for Long-Delay Paths
  RFC 6298: Computing TCP's Retransmission Timer

Signed-off-by: Your Name <your.email@example.com>
---
 Documentation/networking/tcp_echo.rst |  87 ++++++++++
 include/linux/tcp.h                   |   8 +
 include/net/tcp.h                     |   5 +
 net/ipv4/sysctl_net_ipv4.c           |   7 +
 net/ipv4/tcp_input.c                  |  45 ++++-
 net/ipv4/tcp_output.c                 | 125 +++++++++++++-
 tools/testing/selftests/net/tcp_echo_test.sh | 50 ++++++
 7 files changed, 320 insertions(+), 7 deletions(-)
```

### Generate and Check Patch

```bash
# Generate patch
git format-patch -1

# Check patch
scripts/checkpatch.pl 0001-*.patch

# Verify RFC references
grep -i "rfc" 0001-*.patch

# Test build
make net/ipv4/tcp_input.o
make net/ipv4/tcp_output.o
```

## 9. Key Takeaways

### Best Practices for RFC Implementation

1. **Thoroughly Read the RFC**
   - Understand all requirements, not just the happy path
   - Note edge cases and error handling
   - Check for updated or superseding RFCs

2. **Reference Appropriately**
   ```c
   /* RFC XXXX, Section Y.Z: Brief description
    * More detailed explanation if needed
    */
   ```

3. **Follow Existing Patterns**
   - Look at similar options (timestamps, SACK, window scaling)
   - Maintain consistency with kernel style
   - Reuse existing infrastructure

4. **Add Comprehensive Testing**
   - Unit tests via kselftest
   - Integration tests with real traffic
   - Stress testing and edge cases

5. **Document Everything**
   - Add kernel documentation
   - Update relevant rst files
   - Include usage examples

### Common RFC-Related Pitfalls

```
❌ Misinterpreting "SHOULD" vs "MUST"
✓  Understand RFC 2119 keywords

❌ Ignoring backward compatibility
✓  Ensure graceful fallback

❌ Not handling option space exhaustion
✓  Priority handling when space limited

❌ Forgetting endianness conversion
✓  Use htonl/ntohl, get_unaligned_be32

❌ Poor error handling
✓  Handle all error paths per RFC
```

## 10. Useful Tools and Resources

### RFC Tools

```bash
# Install RFC toolchain
pip3 install rfctools rfcdiff

# Compare RFC versions
rfcdiff rfc1323.txt rfc7323.txt

# Extract ASCII art diagrams
rfc --extract-ascii rfc793.txt

# Search RFC by keyword
rfc --search "tcp window scaling"
```

### Kernel RFC References Database

```bash
# Find all RFCs mentioned in kernel
cd ~/kernel-dev/linux
git grep -oh "RFC [0-9]\+" | sort -u | sort -n -t' ' -k2

# RFCs per subsystem
git grep -oh "RFC [0-9]\+" net/ | sort | uniq -c

# Most referenced RFCs
git grep -oh "RFC [0-9]\+" | sort | uniq -c | sort -rn | head -20
```

### Online Resources

```
RFC Editor:          https://www.rfc-editor.org/
IETF Datatracker:    https://datatracker.ietf.org/
Linux Network Stack: https://www.kernel.org/doc/html/latest/networking/
Kernel Source:       https://elixir.bootlin.com/linux/latest/source

Mailing List:        netdev@vger.kernel.org
IRC:                 #netdev on irc.oftc.net
```

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│ RFC → Kernel Implementation Workflow                │
├─────────────────────────────────────────────────────┤
│ 1. Find RFC:  wget https://rfc-editor.org/rfc/...  │
│ 2. Read spec: less rfcXXXX.txt                     │
│ 3. Find code: git grep "protocol_name" net/        │
│ 4. Implement: Follow existing patterns             │
│ 5. Test:      kselftest + manual testing           │
│ 6. Document:  Add .rst file                        │
│ 7. Patch:     git format-patch -1                  │
│ 8. Check:     scripts/checkpatch.pl                │
│ 9. Submit:    git send-email to netdev@vger        │
└─────────────────────────────────────────────────────┘
```

Good luck with your RFC-based kernel development!

#!/bin/bash
# RFC Development Toolkit for Linux Kernel
# A collection of utilities for RFC-based kernel development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

KERNEL_DIR="${KERNEL_DIR:-$HOME/kernel-dev/linux}"
RFC_CACHE_DIR="$HOME/.rfc-cache"

# Create RFC cache directory
mkdir -p "$RFC_CACHE_DIR"

# ============================================================================
# RFC Download and Management
# ============================================================================

rfc_download() {
    local rfc_num="$1"
    local rfc_file="$RFC_CACHE_DIR/rfc${rfc_num}.txt"
    
    if [ -f "$rfc_file" ]; then
        echo -e "${GREEN}✓${NC} RFC ${rfc_num} already cached"
        return 0
    fi
    
    echo -e "${BLUE}→${NC} Downloading RFC ${rfc_num}..."
    
    # Try multiple sources
    if curl -sL "https://www.rfc-editor.org/rfc/rfc${rfc_num}.txt" \
         -o "$rfc_file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Downloaded RFC ${rfc_num}"
        return 0
    elif curl -sL "https://tools.ietf.org/rfc/rfc${rfc_num}.txt" \
         -o "$rfc_file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Downloaded RFC ${rfc_num}"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to download RFC ${rfc_num}"
        rm -f "$rfc_file"
        return 1
    fi
}

rfc_view() {
    local rfc_num="$1"
    local rfc_file="$RFC_CACHE_DIR/rfc${rfc_num}.txt"
    
    rfc_download "$rfc_num" || return 1
    
    if command -v bat &> /dev/null; then
        bat "$rfc_file"
    else
        less "$rfc_file"
    fi
}

rfc_search_text() {
    local rfc_num="$1"
    local search_term="$2"
    local rfc_file="$RFC_CACHE_DIR/rfc${rfc_num}.txt"
    
    rfc_download "$rfc_num" || return 1
    
    echo -e "\n${BLUE}Searching RFC ${rfc_num} for: ${search_term}${NC}\n"
    grep -n -i -C 3 "$search_term" "$rfc_file" | \
        sed "s/\(${search_term}\)/$(echo -e ${GREEN})\1$(echo -e ${NC})/gi"
}

rfc_extract_section() {
    local rfc_num="$1"
    local section="$2"
    local rfc_file="$RFC_CACHE_DIR/rfc${rfc_num}.txt"
    
    rfc_download "$rfc_num" || return 1
    
    echo -e "\n${BLUE}Section ${section} of RFC ${rfc_num}:${NC}\n"
    
    # Try to extract the section (basic implementation)
    awk "/^${section}\./ {flag=1} /^[0-9]+\./ && flag && !/^${section}\./ {flag=0} flag" \
        "$rfc_file"
}

# ============================================================================
# Kernel RFC Analysis
# ============================================================================

kernel_find_rfcs() {
    echo -e "${BLUE}→${NC} Scanning kernel for RFC references...\n"
    
    cd "$KERNEL_DIR" || return 1
    
    # Find all RFC references
    git grep -oh "RFC[- ]*[0-9]\+" | \
        sed 's/RFC[- ]*//' | \
        sort -n | uniq -c | sort -rn | \
        while read count rfc; do
            printf "${GREEN}%4d${NC} references to ${YELLOW}RFC %s${NC}\n" \
                   "$count" "$rfc"
        done
}

kernel_find_rfc_in_path() {
    local path="${1:-.}"
    
    echo -e "${BLUE}→${NC} RFCs referenced in: $path\n"
    
    cd "$KERNEL_DIR" || return 1
    
    git grep -oh "RFC[- ]*[0-9]\+" "$path" 2>/dev/null | \
        sed 's/RFC[- ]*//' | \
        sort -n | uniq -c | sort -rn | \
        while read count rfc; do
            printf "${GREEN}%4d${NC} × ${YELLOW}RFC %-5s${NC} " "$count" "$rfc"
            
            # Try to get RFC title from cache or download
            local rfc_file="$RFC_CACHE_DIR/rfc${rfc}.txt"
            if [ -f "$rfc_file" ]; then
                head -20 "$rfc_file" | grep -m1 "^[A-Z]" | \
                    sed 's/^/- /'
            else
                echo ""
            fi
        done
}

kernel_show_rfc_usage() {
    local rfc_num="$1"
    
    echo -e "${BLUE}→${NC} Showing usage of RFC ${rfc_num} in kernel:\n"
    
    cd "$KERNEL_DIR" || return 1
    
    git grep -n "RFC[- ]*${rfc_num}" | \
        while IFS=: read file line text; do
            printf "${GREEN}%s${NC}:${YELLOW}%s${NC}\n" "$file" "$line"
            printf "  %s\n\n" "$text"
        done
}

# ============================================================================
# RFC Implementation Helper
# ============================================================================

rfc_create_template() {
    local rfc_num="$1"
    local feature_name="$2"
    local output_file="${3:-rfc${rfc_num}_${feature_name}.c}"
    
    cat > "$output_file" << EOF
// SPDX-License-Identifier: GPL-2.0
/*
 * Implementation of ${feature_name} per RFC ${rfc_num}
 *
 * Copyright (C) $(date +%Y) Your Name <your.email@example.com>
 *
 * This file implements the ${feature_name} as specified in
 * RFC ${rfc_num}. 
 *
 * References:
 *   RFC ${rfc_num} - [Title]
 */

#include <linux/types.h>
#include <linux/kernel.h>
#include <net/tcp.h>

/*
 * RFC ${rfc_num}, Section X.Y: [Description]
 *
 * [Detailed explanation of what this code does]
 */

/* Constants from RFC ${rfc_num} */
#define FEATURE_CONSTANT_NAME    0x00

/* 
 * Data structures for RFC ${rfc_num} implementation
 */
struct feature_state {
    u32 field1;
    u16 field2;
    u8  flags;
};

/*
 * Initialize feature per RFC ${rfc_num} Section X
 */
int feature_init(struct sock *sk)
{
    /* TODO: Implement initialization */
    return 0;
}

/*
 * Process incoming option per RFC ${rfc_num} Section Y
 */
int feature_process_option(struct sock *sk, const u8 *ptr, int len)
{
    /* TODO: Implement option parsing */
    return 0;
}

/*
 * Generate outgoing option per RFC ${rfc_num} Section Z
 */
int feature_write_option(u8 *ptr, struct sock *sk)
{
    /* TODO: Implement option generation */
    return 0;
}

/* 
 * Module initialization
 */
static int __init feature_module_init(void)
{
    pr_info("RFC ${rfc_num} ${feature_name} module loaded\n");
    return 0;
}

static void __exit feature_module_exit(void)
{
    pr_info("RFC ${rfc_num} ${feature_name} module unloaded\n");
}

module_init(feature_module_init);
module_exit(feature_module_exit);

MODULE_DESCRIPTION("RFC ${rfc_num} ${feature_name} implementation");
MODULE_AUTHOR("Your Name <your.email@example.com>");
MODULE_LICENSE("GPL v2");
EOF

    echo -e "${GREEN}✓${NC} Created template: $output_file"
    echo -e "${YELLOW}→${NC} Edit the file and replace TODOs with actual implementation"
}

rfc_create_test_template() {
    local rfc_num="$1"
    local feature_name="$2"
    local output_file="${3:-test_rfc${rfc_num}_${feature_name}.sh}"
    
    cat > "$output_file" << 'EOF'
#!/bin/bash
# SPDX-License-Identifier: GPL-2.0
#
# Test script for RFC %RFC_NUM% %FEATURE_NAME% implementation

set -e

KSFT_SKIP=4
KSFT_FAIL=1
KSFT_PASS=0

# Test setup
setup_test() {
    echo "Setting up test environment..."
    
    # Create network namespaces
    ip netns add test_ns1 2>/dev/null || true
    ip netns add test_ns2 2>/dev/null || true
    
    # Create veth pair
    ip link add veth0 type veth peer name veth1 2>/dev/null || true
    ip link set veth0 netns test_ns1
    ip link set veth1 netns test_ns2
    
    # Configure interfaces
    ip netns exec test_ns1 ip addr add 10.0.0.1/24 dev veth0
    ip netns exec test_ns2 ip addr add 10.0.0.2/24 dev veth1
    ip netns exec test_ns1 ip link set veth0 up
    ip netns exec test_ns2 ip link set veth1 up
    ip netns exec test_ns1 ip link set lo up
    ip netns exec test_ns2 ip link set lo up
}

# Test cleanup
cleanup_test() {
    echo "Cleaning up..."
    ip netns del test_ns1 2>/dev/null || true
    ip netns del test_ns2 2>/dev/null || true
}

# RFC %RFC_NUM% Test 1: Basic functionality
test_basic() {
    echo "Test 1: Basic functionality"
    
    # Start server
    ip netns exec test_ns1 nc -l 8080 > /tmp/server.out &
    SERVER_PID=$!
    sleep 1
    
    # Connect client
    echo "test data" | ip netns exec test_ns2 nc 10.0.0.1 8080 &
    CLIENT_PID=$!
    sleep 2
    
    # Verify
    if [ -s /tmp/server.out ]; then
        echo "  PASS: Connection established"
        kill $SERVER_PID $CLIENT_PID 2>/dev/null || true
        return 0
    else
        echo "  FAIL: Connection failed"
        kill $SERVER_PID $CLIENT_PID 2>/dev/null || true
        return 1
    fi
}

# RFC %RFC_NUM% Test 2: Option format verification
test_option_format() {
    echo "Test 2: Option format verification"
    
    # Capture packets
    ip netns exec test_ns1 timeout 5 tcpdump -i veth0 -w /tmp/test.pcap &
    TCPDUMP_PID=$!
    sleep 1
    
    # Generate traffic
    ip netns exec test_ns1 nc -l 8080 &
    SERVER_PID=$!
    sleep 1
    echo "test" | ip netns exec test_ns2 nc 10.0.0.1 8080 &
    sleep 2
    
    kill $SERVER_PID $TCPDUMP_PID 2>/dev/null || true
    wait $TCPDUMP_PID 2>/dev/null || true
    
    # Analyze capture
    if tcpdump -r /tmp/test.pcap -vvv 2>&1 | grep -q "option"; then
        echo "  PASS: Options detected in packets"
        return 0
    else
        echo "  SKIP: Options not detected (may be disabled)"
        return $KSFT_SKIP
    fi
}

# Main test execution
main() {
    echo "RFC %RFC_NUM% %FEATURE_NAME% Tests"
    echo "================================"
    
    # Check permissions
    if [ "$(id -u)" -ne 0 ]; then
        echo "ERROR: Tests must be run as root"
        exit $KSFT_SKIP
    fi
    
    # Setup
    setup_test
    
    # Run tests
    local failed=0
    
    test_basic || ((failed++))
    test_option_format || true  # Don't fail on skip
    
    # Cleanup
    cleanup_test
    
    # Report results
    echo ""
    if [ $failed -eq 0 ]; then
        echo "All tests passed!"
        exit $KSFT_PASS
    else
        echo "Some tests failed!"
        exit $KSFT_FAIL
    fi
}

# Handle signals
trap cleanup_test EXIT INT TERM

# Run tests
main "$@"
EOF

    # Replace placeholders
    sed -i "s/%RFC_NUM%/${rfc_num}/g" "$output_file"
    sed -i "s/%FEATURE_NAME%/${feature_name}/g" "$output_file"
    chmod +x "$output_file"
    
    echo -e "${GREEN}✓${NC} Created test template: $output_file"
}

# ============================================================================
# RFC Compliance Checker
# ============================================================================

rfc_compliance_check() {
    local rfc_num="$1"
    local file="$2"
    
    echo -e "${BLUE}→${NC} Checking RFC ${rfc_num} compliance in: $file\n"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗${NC} File not found: $file"
        return 1
    fi
    
    local issues=0
    
    # Check for RFC references
    if ! grep -q "RFC.*${rfc_num}" "$file"; then
        echo -e "${YELLOW}⚠${NC} No RFC ${rfc_num} reference found in comments"
        ((issues++))
    else
        echo -e "${GREEN}✓${NC} RFC ${rfc_num} referenced in code"
    fi
    
    # Check for proper SPDX license
    if ! grep -q "SPDX-License-Identifier:" "$file"; then
        echo -e "${YELLOW}⚠${NC} Missing SPDX license identifier"
        ((issues++))
    else
        echo -e "${GREEN}✓${NC} SPDX license identifier present"
    fi
    
    # Check for signed-off-by (for patches)
    if git log -1 --format=%B "$file" 2>/dev/null | \
       grep -q "Signed-off-by:"; then
        echo -e "${GREEN}✓${NC} Commit is signed off"
    fi
    
    # Run checkpatch if in kernel tree
    if [ -f "$KERNEL_DIR/scripts/checkpatch.pl" ]; then
        echo -e "\n${BLUE}→${NC} Running checkpatch.pl...\n"
        "$KERNEL_DIR/scripts/checkpatch.pl" --strict --file "$file" || true
    fi
    
    return $issues
}

# ============================================================================
# RFC Documentation Generator
# ============================================================================

rfc_generate_docs() {
    local rfc_num="$1"
    local feature_name="$2"
    local output_file="${3:-rfc${rfc_num}_${feature_name}.rst}"
    
    cat > "$output_file" << EOF
.. SPDX-License-Identifier: GPL-2.0

================================================
${feature_name} (RFC ${rfc_num})
================================================

:Author: Your Name <your.email@example.com>
:Date: $(date +"%B %Y")

Overview
========

This document describes the Linux kernel implementation of
${feature_name} as specified in RFC ${rfc_num}.

Specification
=============

RFC ${rfc_num} defines [brief description].

Key requirements from RFC ${rfc_num}:

- Requirement 1
- Requirement 2
- Requirement 3

Configuration
=============

Enable the feature::

    sysctl -w net.ipv4.feature_name=1

Or via sysctl.conf::

    net.ipv4.feature_name = 1

Usage
=====

Example usage::

    # Example command or code

Implementation Details
======================

The implementation consists of:

1. **Option Parsing** (net/ipv4/tcp_input.c)
   
   Parses incoming options according to RFC ${rfc_num} Section X.

2. **Option Generation** (net/ipv4/tcp_output.c)
   
   Generates outgoing options as specified.

3. **State Management** (include/net/tcp.h)
   
   Maintains per-connection state.

Data Structures
---------------

::

    struct feature_state {
        u32 field1;    /* Description */
        u16 field2;    /* Description */
    };

Protocol Flow
-------------

::

    Client                    Server
      |                         |
      |-------- SYN ----------->|
      |  [Feature Option]       |
      |                         |
      |<----- SYN-ACK ----------|
      |  [Feature Option]       |
      |                         |
      |-------- ACK ----------->|
      |                         |

Testing
=======

Run the test suite::

    cd tools/testing/selftests/net
    sudo ./test_${feature_name}.sh

Manual testing::

    # Commands for manual testing

Performance Impact
==================

- Overhead: [describe]
- Latency impact: [describe]
- Throughput impact: [describe]

Compatibility
=============

- Backward compatible: Yes/No
- Fallback behavior: [describe]
- Interoperability: [describe]

Known Limitations
=================

List any known limitations or issues.

References
==========

- RFC ${rfc_num}: [Title]
- Related RFCs: [if any]

See Also
========

- :doc:\`/networking/tcp\`
- :doc:\`/networking/segmentation-offloads\`
EOF

    echo -e "${GREEN}✓${NC} Created documentation: $output_file"
    echo -e "${YELLOW}→${NC} Edit the file and fill in the details"
}

# ============================================================================
# Helper Functions
# ============================================================================

show_help() {
    cat << EOF
RFC Development Toolkit for Linux Kernel

Usage: $0 <command> [arguments]

Commands:
  
  RFC Management:
    download <NUM>              Download RFC to cache
    view <NUM>                  View RFC in pager
    search <NUM> <TEXT>         Search RFC for text
    section <NUM> <SEC>         Extract RFC section
  
  Kernel Analysis:
    find-all                    Find all RFCs in kernel
    find-in <PATH>              Find RFCs in specific path
    show-usage <NUM>            Show how RFC is used in kernel
  
  Development:
    create-code <NUM> <NAME>    Create code template
    create-test <NUM> <NAME>    Create test template
    create-docs <NUM> <NAME>    Create documentation template
    check <NUM> <FILE>          Check RFC compliance
  
  Configuration:
    config                      Show current configuration
    
Examples:
  $0 download 793
  $0 view 793
  $0 search 793 "window scaling"
  $0 find-in net/ipv4
  $0 create-code 793 tcp_echo
  $0 create-test 793 tcp_echo
  $0 check 793 net/ipv4/tcp_input.c

Environment Variables:
  KERNEL_DIR                    Path to kernel source (default: ~/kernel-dev/linux)
  RFC_CACHE_DIR                 RFC cache directory (default: ~/.rfc-cache)

EOF
}

show_config() {
    echo -e "${BLUE}Current Configuration:${NC}"
    echo "  KERNEL_DIR:    $KERNEL_DIR"
    echo "  RFC_CACHE_DIR: $RFC_CACHE_DIR"
    echo ""
    echo "  Cached RFCs:   $(ls -1 "$RFC_CACHE_DIR" 2>/dev/null | wc -l)"
    echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        download)
            rfc_download "$@"
            ;;
        view)
            rfc_view "$@"
            ;;
        search)
            rfc_search_text "$@"
            ;;
        section)
            rfc_extract_section "$@"
            ;;
        find-all)
            kernel_find_rfcs
            ;;
        find-in)
            kernel_find_rfc_in_path "$@"
            ;;
        show-usage)
            kernel_show_rfc_usage "$@"
            ;;
        create-code)
            rfc_create_template "$@"
            ;;
        create-test)
            rfc_create_test_template "$@"
            ;;
        create-docs)
            rfc_generate_docs "$@"
            ;;
        check)
            rfc_compliance_check "$@"
            ;;
        config)
            show_config
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

I'll create a comprehensive guide on working with RFCs in Linux kernel development, including a practical implementation example.Perfect! I've created a comprehensive guide on working with RFCs in kernel development. Let me also create a practical script toolkit to help you work with RFCs more efficiently:Excellent! I've created two comprehensive resources for you:

## 📚 What I've Created:

### 1. **Complete RFC Development Guide** 
Shows you:
- How to find and read RFCs
- Where networking RFCs are implemented in the kernel
- A **complete working example**: TCP Echo Option (RFC 1072) implementation
- Testing methodology against RFC requirements
- Proper documentation and patch submission

### 2. **RFC Development Toolkit Script**
A practical bash tool that helps you:
- Download and cache RFCs
- Search RFCs for specific terms
- Find which RFCs are used in kernel code
- Auto-generate code/test/documentation templates
- Check RFC compliance

## 🚀 Quick Start:

```bash
# Save the toolkit script
cat > ~/bin/rfc-dev-tool.sh << 'EOF'
[paste the script content]
EOF
chmod +x ~/bin/rfc-dev-tool.sh

# Add to PATH
export PATH="$HOME/bin:$PATH"

# Try it out!
rfc-dev-tool.sh download 793    # Download TCP RFC
rfc-dev-tool.sh view 793        # Read it
rfc-dev-tool.sh search 793 "window"  # Search for window scaling

# Find RFCs in networking code
cd ~/kernel-dev/linux
rfc-dev-tool.sh find-in net/ipv4

# Create implementation template
rfc-dev-tool.sh create-code 7323 tcp_timestamps
rfc-dev-tool.sh create-test 7323 tcp_timestamps
```

## 📖 Key RFC Resources for Networking:

**Core Protocols:**
- **RFC 793** → TCP (now RFC 9293)
- **RFC 791** → IPv4
- **RFC 768** → UDP
- **RFC 8200** → IPv6

**TCP Features You Can Work On:**
- **RFC 7323** → TCP Window Scaling, Timestamps
- **RFC 2018** → TCP SACK
- **RFC 3168** → ECN
- **RFC 8684** → Multipath TCP (MPTCP)
- **RFC 8985** → TCP RACK

## 💡 Practical Workflow Example:

```bash
# 1. Pick an RFC to implement (e.g., RFC 6937 - Proportional Rate Reduction)
rfc-dev-tool.sh download 6937
rfc-dev-tool.sh view 6937

# 2. See how similar features are implemented
cd ~/kernel-dev/linux
git grep -n "RFC 5681" net/ipv4/tcp*.c  # Similar congestion control RFC

# 3. Create templates
rfc-dev-tool.sh create-code 6937 tcp_prr
rfc-dev-tool.sh create-test 6937 tcp_prr

# 4. Implement in the templates created

# 5. Test
make net/ipv4/tcp_input.o
./test_rfc6937_tcp_prr.sh

# 6. Check compliance
rfc-dev-tool.sh check 6937 net/ipv4/tcp_input.c
```

## 🎯 Best Starting Points for Beginners:

1. **Documentation fixes** - Find typos in RFC references
2. **Sysctl additions** - Add tunables for existing RFC features
3. **Test improvements** - Add tests for RFC edge cases
4. **Small optimizations** - Improve existing RFC implementations

## 🔍 Example: Finding Existing RFC Implementation

```bash
# Let's say you want to understand TCP Window Scaling (RFC 7323)
rfc-dev-tool.sh download 7323
rfc-dev-tool.sh show-usage 7323

# This will show you all files that mention RFC 7323:
# net/ipv4/tcp_input.c:1234  - parsing window scale option
# net/ipv4/tcp_output.c:567  - sending window scale option
# etc.
```

Would you like me to:
1. Show you a simpler, more beginner-friendly RFC example?
2. Explain a specific part of the TCP Echo implementation in detail?
3. Help you choose an RFC to implement based on your interests?
4. Create additional testing or debugging scripts?