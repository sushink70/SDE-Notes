# Event-Driven Architecture: Complete In-Depth Guide
## From Kernel Primitives to Cloud-Scale Distributed Systems

> **Summary:** Event-Driven Architecture (EDA) is a software design paradigm where system components communicate by producing, routing, and consuming events — discrete, immutable records of state change. Understanding EDA from first principles requires mastery of kernel-level I/O multiplexing (epoll, io_uring, kqueue), wire-level semantics, broker internals, distributed consistency guarantees, and threat models across every layer. This guide covers EDA comprehensively: from Linux kernel event primitives and memory-mapped ring buffers to cloud-native brokers (Kafka, NATS, Kinesis, EventBridge, Pub/Sub), to CloudEvents, CQRS, Event Sourcing, Saga, Outbox, and security-by-design patterns. Implementations are provided in C, Go, and Rust. The goal is to build a precise mental model that makes algorithm selection, system design, and security analysis intuitive at any scale.

---

## Table of Contents

1. [First Principles: What Is an Event?](#1-first-principles-what-is-an-event)
2. [Kernel-Level Event Mechanisms](#2-kernel-level-event-mechanisms)
   - 2.1 [epoll — Linux I/O Event Notification](#21-epoll--linux-io-event-notification)
   - 2.2 [io_uring — Async I/O Ring Buffer](#22-io_uring--async-io-ring-buffer)
   - 2.3 [eventfd and signalfd](#23-eventfd-and-signalfd)
   - 2.4 [kqueue (BSD/macOS)](#24-kqueue-bsdmacos)
   - 2.5 [eBPF for Kernel-Space Event Capture](#25-ebpf-for-kernel-space-event-capture)
3. [Event Taxonomy and Data Models](#3-event-taxonomy-and-data-models)
4. [Core EDA Patterns](#4-core-eda-patterns)
   - 4.1 [Publish/Subscribe](#41-publishsubscribe)
   - 4.2 [Event Streaming](#42-event-streaming)
   - 4.3 [Event Sourcing](#43-event-sourcing)
   - 4.4 [CQRS](#44-cqrs-command-query-responsibility-segregation)
   - 4.5 [Saga Pattern](#45-saga-pattern)
   - 4.6 [Outbox Pattern](#46-outbox-pattern)
   - 4.7 [Dead Letter Queue](#47-dead-letter-queue)
   - 4.8 [Event Replay and Time Travel](#48-event-replay-and-time-travel)
5. [Delivery Semantics and Ordering](#5-delivery-semantics-and-ordering)
6. [Broker Internals: Deep Dive](#6-broker-internals-deep-dive)
   - 6.1 [Apache Kafka](#61-apache-kafka)
   - 6.2 [NATS / JetStream](#62-nats--jetstream)
   - 6.3 [RabbitMQ (AMQP)](#63-rabbitmq-amqp)
   - 6.4 [Redis Streams](#64-redis-streams)
7. [Cloud-Native EDA](#7-cloud-native-eda)
   - 7.1 [AWS: Kinesis, EventBridge, SNS/SQS](#71-aws-kinesis-eventbridge-snssqs)
   - 7.2 [GCP: Pub/Sub, Eventarc](#72-gcp-pubsub-eventarc)
   - 7.3 [Azure: Event Hub, Event Grid](#73-azure-event-hub-event-grid)
8. [CloudEvents Standard](#8-cloudevents-standard)
9. [Networking Layer: Events Over the Wire](#9-networking-layer-events-over-the-wire)
10. [Security: Threat Model and Mitigations](#10-security-threat-model-and-mitigations)
11. [Observability and Distributed Tracing](#11-observability-and-distributed-tracing)
12. [Implementations: C, Go, Rust](#12-implementations-c-go-rust)
13. [Testing, Fuzzing, and Benchmarking](#13-testing-fuzzing-and-benchmarking)
14. [Production Rollout and Rollback](#14-production-rollout-and-rollback)
15. [Next 3 Steps](#15-next-3-steps)
16. [References](#16-references)

---

## 1. First Principles: What Is an Event?

An **event** is an immutable, timestamped record asserting that something happened in the world. It is a fact, not a command. Events are:

- **Immutable** — once written, never changed
- **Ordered** (within a partition/stream) — sequence matters
- **Named** — carry a type that signals semantic intent
- **Causally linked** — one event may cause others
- **Durable or ephemeral** — depending on broker guarantees

### Event vs. Command vs. Query

```
┌─────────────┬──────────────────────────────┬────────────────────────────────────────┐
│ Concept     │ Intent                       │ Example                                │
├─────────────┼──────────────────────────────┼────────────────────────────────────────┤
│ Command     │ Request to DO something      │ PlaceOrder { items: [...] }             │
│             │ (imperative, may fail)       │ → sent to ONE handler                  │
├─────────────┼──────────────────────────────┼────────────────────────────────────────┤
│ Event       │ FACT that something happened │ OrderPlaced { orderId, ts, items }     │
│             │ (past tense, immutable)      │ → broadcast to N subscribers           │
├─────────────┼──────────────────────────────┼────────────────────────────────────────┤
│ Query       │ Request for data (read-only) │ GetOrder { orderId }                   │
│             │ (no side effects)            │ → returns current state                │
└─────────────┴──────────────────────────────┴────────────────────────────────────────┘
```

### Why EDA Over Request/Response?

```
REQUEST/RESPONSE (RPC)
──────────────────────
  Client ──── HTTP/gRPC ───► Server
         ◄─── response ──────

Problems:
  - Tight temporal coupling (both must be up simultaneously)
  - Tight spatial coupling (must know server address)
  - Cascading failures (timeouts propagate upstream)
  - No built-in fan-out
  - No replay / audit trail
  - Synchronous = bounded throughput

EVENT-DRIVEN
────────────
  Producer ──► [Broker] ──► Consumer A
                       ──► Consumer B
                       ──► Consumer C (added later, can replay)

Benefits:
  - Temporal decoupling (producer/consumer operate independently)
  - Spatial decoupling (producer doesn't know consumers)
  - Natural fan-out
  - Built-in audit log / replay
  - Backpressure isolation
  - Asynchronous = scalable throughput
```

### The Fundamental Trade-off

EDA introduces **eventual consistency**. The producer does not know if/when consumers processed the event. This demands careful design of:
- Idempotency (consumers handle duplicate delivery)
- Compensation (Saga) for distributed transactions
- Causality tracking (vector clocks, Lamport timestamps)
- Observability (distributed tracing across event hops)

---

## 2. Kernel-Level Event Mechanisms

Understanding how the OS kernel handles I/O events is foundational. Every broker (Kafka, NATS, RabbitMQ) is ultimately built on these primitives. Your ability to build high-performance event systems depends on understanding what happens below the user-space API.

### System Architecture: I/O Path from NIC to Application

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           KERNEL I/O EVENT PATH                                  │
│                                                                                  │
│  NIC Hardware                                                                    │
│  ┌──────────────────┐                                                            │
│  │  RX Ring Buffer  │  ◄── DMA writes packets here directly (no CPU copy)       │
│  │  (hardware queue)│                                                            │
│  └────────┬─────────┘                                                            │
│           │ Hardware IRQ / MSI-X interrupt                                       │
│           ▼                                                                      │
│  ┌──────────────────────────┐                                                    │
│  │   Net Softirq (NAPI)     │  ◄── Deferred interrupt processing                │
│  │   net_rx_action()        │      Polls RX ring in budget to avoid IRQ storm   │
│  └────────┬─────────────────┘                                                    │
│           │                                                                      │
│           ▼                                                                      │
│  ┌──────────────────────────┐                                                    │
│  │  Protocol Stack          │                                                    │
│  │  (IP → TCP → socket buf) │                                                    │
│  │  sk_buff chain           │                                                    │
│  └────────┬─────────────────┘                                                    │
│           │  sk->sk_data_ready() callback                                        │
│           ▼                                                                      │
│  ┌──────────────────────────┐                                                    │
│  │  Socket Receive Buffer   │  ← sk_rcvbuf (default 212992 bytes)               │
│  │  (per-socket queue)      │                                                    │
│  └────────┬─────────────────┘                                                    │
│           │  wake_up_interruptible_poll()                                        │
│           ▼                                                                      │
│  ┌──────────────────────────┐   ┌────────────────────────────────┐              │
│  │  epoll / io_uring        │   │  Kernel poll table             │              │
│  │  event ready list        │◄──│  (fd registered interest)      │              │
│  └────────┬─────────────────┘   └────────────────────────────────┘              │
│           │  copy_to_user() / io_uring CQE                                      │
│           ▼                                                                      │
│  ┌──────────────────────────┐                                                    │
│  │  User Space Application  │  ← Event loop, reactor, async runtime             │
│  └──────────────────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

Key data structures:
  sk_buff      → packet buffer (zero-copy with page fragments)
  socket.wq    → wait queue (processes sleeping on this socket)
  epoll_event  → { events: EPOLLIN|EPOLLET, data: { fd | ptr | u64 } }
  io_uring_sqe → Submission Queue Entry (command to kernel)
  io_uring_cqe → Completion Queue Entry (result from kernel)
```

### 2.1 epoll — Linux I/O Event Notification

**epoll** is the Linux mechanism for monitoring many file descriptors efficiently. It replaced `select()` (O(n) scan, 1024 fd limit) and `poll()` (O(n) copy). epoll is O(1) for readiness notification via an internal red-black tree for registered fds and a linked list for ready events.

#### epoll Internals

```
epoll_create1(0)
      │
      ▼
┌─────────────────────────────────────────────────┐
│  struct eventpoll (kernel object)               │
│  ┌────────────────────┐                         │
│  │  rbr (red-black    │  ← epoll_ctl(ADD) puts  │
│  │  tree)             │    fds here              │
│  │  Keyed by fd       │                         │
│  └────────────────────┘                         │
│  ┌────────────────────┐                         │
│  │  rdllist (ready    │  ← kernel moves epitem  │
│  │  double-linked     │    here when fd ready   │
│  │  list)             │                         │
│  └────────────────────┘                         │
│  wq (wait queue)  ← epoll_wait() sleeps here   │
└─────────────────────────────────────────────────┘

epoll_ctl(EPOLL_CTL_ADD, fd, &ev):
  1. Allocate epitem, insert into rb-tree
  2. Call file->f_op->poll() to check current state
  3. Register ep_poll_callback in fd's wait queue

When fd becomes ready (data arrives):
  1. ep_poll_callback() fires (in softirq context)
  2. Move epitem to rdllist
  3. wake_up() epoll_wait() caller

epoll_wait(epfd, events[], maxevents, timeout):
  1. If rdllist non-empty: copy events to user, return
  2. Else: sleep on wq until woken or timeout
```

#### Edge-Triggered vs Level-Triggered

```
LEVEL-TRIGGERED (default, EPOLLIN):
─────────────────────────────────
  epoll_wait returns as long as fd has data.
  If you read 100 bytes of a 1000-byte buffer,
  next epoll_wait still returns EPOLLIN.
  Safe but may starve other fds.

EDGE-TRIGGERED (EPOLLIN | EPOLLET):
────────────────────────────────────
  epoll_wait returns ONLY when new data arrives.
  You MUST read until EAGAIN on each notification.
  Missed data = hung connection.
  Higher performance, but requires non-blocking I/O
  and correct draining loop.

  Rule: EPOLLET fd MUST be O_NONBLOCK.
  Loop: while (read(fd, buf, n) > 0) {}
        if (errno == EAGAIN) { /* done */ }
```

#### C Implementation: epoll Event Loop

```c
/* epoll_server.c - Production-grade epoll reactor */
#define _GNU_SOURCE
#include <sys/epoll.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdatomic.h>

#define MAX_EVENTS   1024
#define BACKLOG      4096
#define RECV_BUF_SZ  65536

typedef struct {
    int fd;
    /* application state per connection */
    uint8_t  rbuf[RECV_BUF_SZ];
    size_t   rbuf_len;
} conn_t;

static int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags < 0) return -1;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

static int set_tcp_opts(int fd) {
    int one = 1;
    /* Disable Nagle for low-latency event delivery */
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
    /* Enable TCP keepalive to detect dead peers */
    setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &one, sizeof(one));
    int ka_idle = 30, ka_intvl = 5, ka_cnt = 3;
    setsockopt(fd, IPPROTO_TCP, TCP_KEEPIDLE, &ka_idle, sizeof(ka_idle));
    setsockopt(fd, IPPROTO_TCP, TCP_KEEPINTVL, &ka_intvl, sizeof(ka_intvl));
    setsockopt(fd, IPPROTO_TCP, TCP_KEEPCNT, &ka_cnt, sizeof(ka_cnt));
    return 0;
}

/* Edge-triggered read: drain until EAGAIN */
static ssize_t read_all(conn_t *c) {
    ssize_t total = 0;
    while (1) {
        size_t space = RECV_BUF_SZ - c->rbuf_len;
        if (space == 0) break; /* buffer full — apply backpressure */
        
        ssize_t n = read(c->fd, c->rbuf + c->rbuf_len, space);
        if (n > 0) {
            c->rbuf_len += n;
            total += n;
        } else if (n == 0) {
            return -1; /* EOF / peer closed */
        } else {
            if (errno == EAGAIN || errno == EWOULDBLOCK) break; /* drained */
            if (errno == EINTR) continue;
            return -1; /* real error */
        }
    }
    return total;
}

int main(int argc, char *argv[]) {
    uint16_t port = argc > 1 ? atoi(argv[1]) : 9000;

    /* Create listening socket */
    int lfd = socket(AF_INET6, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (lfd < 0) { perror("socket"); return 1; }

    int one = 1;
    setsockopt(lfd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    setsockopt(lfd, SOL_SOCKET, SO_REUSEPORT, &one, sizeof(one)); /* multi-thread scaling */

    /* Increase socket buffers for high-throughput */
    int bufsize = 4 * 1024 * 1024; /* 4MB */
    setsockopt(lfd, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize));
    setsockopt(lfd, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));

    struct sockaddr_in6 addr = {
        .sin6_family = AF_INET6,
        .sin6_port   = htons(port),
        .sin6_addr   = in6addr_any,
    };
    if (bind(lfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); return 1;
    }
    if (listen(lfd, BACKLOG) < 0) { perror("listen"); return 1; }

    /* Create epoll instance */
    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd < 0) { perror("epoll_create1"); return 1; }

    /* Register listening socket — level-triggered for accept */
    struct epoll_event ev = {
        .events  = EPOLLIN,
        .data.fd = lfd,
    };
    if (epoll_ctl(epfd, EPOLL_CTL_ADD, lfd, &ev) < 0) {
        perror("epoll_ctl ADD lfd"); return 1;
    }

    printf("[reactor] Listening on [::]:%u  epfd=%d\n", port, epfd);

    struct epoll_event events[MAX_EVENTS];
    conn_t *conns[65536] = {0}; /* fd-indexed, real impl uses hash map */

    while (1) {
        int nready = epoll_wait(epfd, events, MAX_EVENTS, -1);
        if (nready < 0) {
            if (errno == EINTR) continue;
            perror("epoll_wait"); break;
        }

        for (int i = 0; i < nready; i++) {
            uint32_t evmask = events[i].events;
            int      fd     = events[i].data.fd;

            if (fd == lfd) {
                /* Accept all pending connections */
                while (1) {
                    struct sockaddr_in6 caddr;
                    socklen_t clen = sizeof(caddr);
                    int cfd = accept4(lfd, (struct sockaddr *)&caddr, &clen,
                                      SOCK_NONBLOCK | SOCK_CLOEXEC);
                    if (cfd < 0) {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                        if (errno == EINTR) continue;
                        perror("accept4"); break;
                    }
                    set_tcp_opts(cfd);

                    conn_t *c = calloc(1, sizeof(*c));
                    c->fd = cfd;
                    conns[cfd] = c;

                    /* Register client fd — EDGE-TRIGGERED, oneshot */
                    struct epoll_event cev = {
                        .events  = EPOLLIN | EPOLLET | EPOLLRDHUP,
                        .data.fd = cfd,
                    };
                    epoll_ctl(epfd, EPOLL_CTL_ADD, cfd, &cev);
                    printf("[accept] fd=%d\n", cfd);
                }
                continue;
            }

            /* Client socket event */
            conn_t *c = conns[fd];
            if (!c) continue;

            if (evmask & (EPOLLERR | EPOLLHUP | EPOLLRDHUP)) {
                goto close_conn;
            }

            if (evmask & EPOLLIN) {
                ssize_t n = read_all(c);
                if (n < 0) goto close_conn;
                /* Process events from c->rbuf here */
                printf("[data] fd=%d got %zu bytes total\n", fd, c->rbuf_len);
                /* Echo back for demonstration */
                write(fd, c->rbuf, c->rbuf_len);
                c->rbuf_len = 0;
                continue;
            }

        close_conn:
            printf("[close] fd=%d\n", fd);
            epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
            close(fd);
            free(c);
            conns[fd] = NULL;
        }
    }

    close(epfd);
    close(lfd);
    return 0;
}

/*
 * Build:  gcc -O2 -Wall -Wextra -o epoll_server epoll_server.c
 * Test:   ./epoll_server 9000 &
 *         echo "hello" | nc localhost 9000
 * Bench:  wrk -t4 -c1000 -d30s http://localhost:9000/
 */
```

---

### 2.2 io_uring — Async I/O Ring Buffer

**io_uring** (Linux 5.1+) is the modern Linux async I/O interface that eliminates most syscall overhead. It exposes two ring buffers shared between kernel and user space via `mmap()`:

- **SQ (Submission Queue)** — user writes operations here
- **CQ (Completion Queue)** — kernel writes results here
- **SQE (Submission Queue Entry)** — describes a single operation
- **CQE (Completion Queue Entry)** — result of a completed operation

```
io_uring Architecture
──────────────────────────────────────────────────────────────────────────────────
                    SHARED MEMORY (mmap, kernel+userspace)
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│   SUBMISSION QUEUE (SQ)                   COMPLETION QUEUE (CQ)              │
│   ┌──────────────────────────────┐        ┌──────────────────────────────┐   │
│   │  sq_head  sq_tail            │        │  cq_head  cq_tail            │   │
│   │  [SQE 0][SQE 1][SQE 2][...] │        │  [CQE 0][CQE 1][CQE 2][...] │   │
│   │    ▲ kernel reads             │        │    ▲ user reads               │   │
│   │                   ▲ user writes│        │                  ▲ kernel writes│  │
│   └──────────────────────────────┘        └──────────────────────────────┘   │
│                                                                               │
│   SQE fields:                             CQE fields:                        │
│     opcode (IORING_OP_READ etc)             user_data (64-bit cookie)        │
│     fd                                      res (return value / -errno)      │
│     addr / buf                              flags                             │
│     len                                                                       │
│     user_data (cookie, echoed in CQE)                                        │
└───────────────────────────────────────────────────────────────────────────────┘
                    ▲                                    │
                    │ io_uring_enter() or kernel wq      │ io_uring_enter()
                    │ (IORING_SETUP_SQPOLL: zero syscall)│  or eventfd notify
                    ▼                                    ▼
              KERNEL io_uring worker / SQPOLL thread
              Executes ops: read/write/accept/send/recv/fsync/splice...

SQPOLL mode (IORING_SETUP_SQPOLL):
  Kernel spawns a background thread that continuously polls SQ.
  User space submits by writing to SQ — ZERO SYSCALLS for I/O.
  Must pin CPU (IORING_SETUP_SQ_AFF) for best performance.
  Requires CAP_SYS_NICE or CAP_SYS_ADMIN.

Fixed buffers (io_uring_register IORING_REGISTER_BUFFERS):
  Pre-register user buffers with kernel → kernel maps them once.
  IORING_OP_READ_FIXED / IORING_OP_WRITE_FIXED skip DMA setup per I/O.
  Critical for high-IOPS workloads (event brokers, log writes).
```

#### C Implementation: io_uring Event Producer

```c
/* io_uring_producer.c - High-performance event producer using io_uring */
#define _GNU_SOURCE
#include <liburing.h>       /* apt install liburing-dev */
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <stdint.h>

#define QUEUE_DEPTH   256
#define EVENT_FILE    "/tmp/events.log"
#define EVENT_COUNT   100000

typedef struct {
    uint64_t  id;
    uint64_t  timestamp_ns;
    char      type[32];
    uint8_t   payload[128];
    uint32_t  payload_len;
    uint32_t  crc32;          /* integrity check */
} __attribute__((packed)) event_t;

static uint32_t crc32_compute(const uint8_t *data, size_t len) {
    /* Simple CRC32 — real impl uses hardware CRC32 via _mm_crc32_u64 */
    uint32_t crc = 0xFFFFFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int j = 0; j < 8; j++)
            crc = (crc >> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
    }
    return ~crc;
}

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

int main(void) {
    struct io_uring ring;
    struct io_uring_params params = {0};

    /* Enable submission-side polling for minimum latency */
    /* params.flags = IORING_SETUP_SQPOLL; */
    /* params.sq_thread_idle = 2000; */ /* ms before SQPOLL sleeps */

    int ret = io_uring_queue_init_params(QUEUE_DEPTH, &ring, &params);
    if (ret < 0) { fprintf(stderr, "io_uring_queue_init: %s\n", strerror(-ret)); return 1; }

    int fd = open(EVENT_FILE, O_WRONLY | O_CREAT | O_TRUNC | O_DIRECT, 0644);
    if (fd < 0) { perror("open"); return 1; }

    /* Register file descriptor — avoids kernel fd table lookup per op */
    int fds[1] = { fd };
    io_uring_register_files(&ring, fds, 1);

    /* Allocate aligned buffers (required for O_DIRECT) */
    const int BATCH = 64;
    event_t *events;
    posix_memalign((void **)&events, 512, BATCH * sizeof(event_t));

    /* Register buffers with kernel — one-time DMA pin */
    struct iovec iovs[1] = {{
        .iov_base = events,
        .iov_len  = BATCH * sizeof(event_t),
    }};
    io_uring_register_buffers(&ring, iovs, 1);

    uint64_t offset = 0;
    int submitted = 0, completed = 0;
    int total_submitted = 0;

    printf("Producing %d events to %s\n", EVENT_COUNT, EVENT_FILE);

    while (completed < EVENT_COUNT) {
        /* Batch fill events */
        int batch = BATCH;
        if (total_submitted + batch > EVENT_COUNT)
            batch = EVENT_COUNT - total_submitted;

        for (int i = 0; i < batch && total_submitted < EVENT_COUNT; i++) {
            event_t *e = &events[i];
            e->id           = total_submitted;
            e->timestamp_ns = now_ns();
            snprintf(e->type, sizeof(e->type), "order.placed");
            e->payload_len  = 64;
            memset(e->payload, 0xAB, e->payload_len);
            e->crc32 = crc32_compute((uint8_t *)e, offsetof(event_t, crc32));

            /* Get SQE from ring */
            struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
            if (!sqe) break; /* ring full — must submit first */

            /* Use fixed buffer write for zero-copy */
            io_uring_prep_write_fixed(sqe, 0 /* fixed fd idx */,
                                      e, sizeof(event_t),
                                      offset, 0 /* buf_index */);
            sqe->user_data = total_submitted;
            offset += sizeof(event_t);
            total_submitted++;
            submitted++;
        }

        /* Submit all pending SQEs */
        ret = io_uring_submit(&ring);
        if (ret < 0) { fprintf(stderr, "submit: %s\n", strerror(-ret)); break; }

        /* Harvest completions */
        struct io_uring_cqe *cqe;
        unsigned head;
        io_uring_for_each_cqe(&ring, head, cqe) {
            if (cqe->res < 0) {
                fprintf(stderr, "write error [id=%llu]: %s\n",
                        (unsigned long long)cqe->user_data, strerror(-cqe->res));
            }
            completed++;
        }
        io_uring_cq_advance(&ring, completed - (completed - submitted));
        submitted = 0;
    }

    /* Wait for all completions */
    io_uring_queue_exit(&ring);

    printf("Done: %d events written (%zu bytes)\n",
           completed, (size_t)offset);

    close(fd);
    free(events);
    return 0;
}

/*
 * Build: gcc -O2 -o io_uring_producer io_uring_producer.c -luring
 * Verify: hexdump -C /tmp/events.log | head -5
 * Perf:  perf stat -e syscalls:sys_enter_io_uring_enter ./io_uring_producer
 *        → should show near-zero syscalls with SQPOLL
 */
```

---

### 2.3 eventfd and signalfd

`eventfd` creates a kernel-maintained 64-bit counter. It's used as a lightweight notification channel between threads or from kernel to user space (e.g., io_uring uses eventfd for completion notification).

```c
/* eventfd_notify.c - Cross-thread event notification */
#include <sys/eventfd.h>
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>

static int efd;

void *producer_thread(void *arg) {
    (void)arg;
    for (int i = 0; i < 5; i++) {
        sleep(1);
        uint64_t val = 1; /* increment counter by 1 */
        write(efd, &val, sizeof(val));
        printf("[producer] wrote event %d\n", i);
    }
    return NULL;
}

void *consumer_thread(void *arg) {
    (void)arg;
    for (int i = 0; i < 5; i++) {
        uint64_t val;
        read(efd, &val, sizeof(val)); /* blocks until non-zero, then resets to 0 */
        printf("[consumer] got %llu events\n", (unsigned long long)val);
    }
    return NULL;
}

int main(void) {
    efd = eventfd(0, EFD_CLOEXEC | EFD_SEMAPHORE);
    /* EFD_SEMAPHORE: each read decrements by 1 (counting semaphore semantics) */
    /* Without EFD_SEMAPHORE: read returns accumulated count, resets to 0 */

    pthread_t pt, ct;
    pthread_create(&ct, NULL, consumer_thread, NULL);
    pthread_create(&pt, NULL, producer_thread, NULL);
    pthread_join(pt, NULL);
    pthread_join(ct, NULL);
    close(efd);
    return 0;
}

/*
 * signalfd: Similar but for POSIX signals → converts signals to fd events
 * timerfd:  Timer expiry as fd event → used in event loops for timeouts
 *
 *   int tfd = timerfd_create(CLOCK_MONOTONIC, TFD_NONBLOCK | TFD_CLOEXEC);
 *   struct itimerspec its = { .it_value = {1, 0} };  // fire after 1s
 *   timerfd_settime(tfd, 0, &its, NULL);
 *   // add tfd to epoll — fires when timer expires
 */
```

---

### 2.4 kqueue (BSD/macOS)

kqueue is the BSD equivalent of epoll, but more general — it handles files, sockets, processes, signals, timers, and virtual events through a unified `kevent` interface.

```
kqueue vs epoll comparison:

┌──────────────────┬──────────────────────────────┬──────────────────────────────┐
│ Feature          │ epoll (Linux)                 │ kqueue (BSD/macOS)           │
├──────────────────┼──────────────────────────────┼──────────────────────────────┤
│ FDs              │ sockets, pipes, eventfd,      │ sockets, files, pipes,       │
│                  │ timerfd, signalfd             │ signals, procs, timers,      │
│                  │                               │ user events (EVFILT_USER)    │
├──────────────────┼──────────────────────────────┼──────────────────────────────┤
│ File I/O events  │ No (inotify separate)         │ Yes (EVFILT_VNODE)           │
├──────────────────┼──────────────────────────────┼──────────────────────────────┤
│ Process events   │ No (pidfd partial)            │ Yes (EVFILT_PROC)            │
├──────────────────┼──────────────────────────────┼──────────────────────────────┤
│ User events      │ No                            │ Yes (EVFILT_USER) — trigger  │
│                  │                               │ from any thread              │
├──────────────────┼──────────────────────────────┼──────────────────────────────┤
│ Batch register   │ One fd per epoll_ctl()        │ Multiple kevents per call    │
├──────────────────┼──────────────────────────────┼──────────────────────────────┤
│ Zero-copy path   │ io_uring + splice()           │ sendfile() kqueue            │
└──────────────────┴──────────────────────────────┴──────────────────────────────┘

struct kevent {
    uintptr_t  ident;   /* identifier (fd, pid, signal number...) */
    int16_t    filter;  /* EVFILT_READ, EVFILT_WRITE, EVFILT_TIMER... */
    uint16_t   flags;   /* EV_ADD, EV_DELETE, EV_ENABLE, EV_ONESHOT */
    uint32_t   fflags;  /* filter-specific flags */
    intptr_t   data;    /* filter-specific data (bytes available etc) */
    void      *udata;   /* user-defined context pointer */
};
```

---

### 2.5 eBPF for Kernel-Space Event Capture

eBPF lets you attach programs to kernel hooks and capture/transform events at the source — before they ever reach user space. This is how modern observability tools (Cilium, Falco, Pixie) work.

```
eBPF Event Capture Architecture
────────────────────────────────────────────────────────────────────────────────
                     Kernel Space
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  System Call Layer          Network Stack          File System               │
│  ┌─────────────────┐       ┌───────────────┐      ┌────────────────┐        │
│  │ sys_enter_write │       │  XDP hook     │      │ vfs_read hook  │        │
│  │ sys_enter_read  │       │  TC hook      │      │ (kprobe)       │        │
│  │ (tracepoint)    │       │  (tc eBPF)    │      │                │        │
│  └────────┬────────┘       └──────┬────────┘      └───────┬────────┘        │
│           │                       │                        │                 │
│           ▼                       ▼                        ▼                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    eBPF Program (verified bytecode)                 │    │
│  │  - Runs in JIT-compiled kernel context                              │    │
│  │  - No kernel panic (verifier ensures termination + memory safety)   │    │
│  │  - Can read: task_struct, sk_buff, mm_struct, file, inode...        │    │
│  │  - Can write: perf ring buffer, BPF map, BPF ring buffer            │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                                │                                             │
│           BPF Maps:            │                                             │
│  ┌─────────────────────────┐   │  ┌─────────────────────────────────┐       │
│  │ HASH map (pid→state)    │◄──┤  │ BPF Ring Buffer (kernel→user)   │       │
│  │ ARRAY map (counters)    │   └─►│ perf_event ring buffer          │       │
│  │ LRU_HASH (connection    │      └──────────────────┬──────────────┘       │
│  │   tracking)             │                         │                      │
│  │ RINGBUF (events)        │                         │                      │
│  └─────────────────────────┘                         │                      │
└─────────────────────────────────────────────────────┼──────────────────────┘
                                                       │ read() / poll()
                              User Space               │
                    ┌──────────────────────────────────▼──────────────────┐
                    │  bpf_map__get_next_key() / ring_buffer__poll()      │
                    │  Process events, emit to Kafka/NATS/stdout           │
                    └──────────────────────────────────────────────────────┘

XDP (eXpress Data Path): eBPF programs run at NIC driver level, BEFORE
   sk_buff allocation. Can DROP/REDIRECT/PASS packets at ~10M pps.
   Used for DDoS mitigation, load balancing (Cilium), firewall.

TC eBPF: Runs at traffic control layer, after sk_buff. Can modify packets.
   Used for pod network policies, traffic shaping, encryption.
```

---

## 3. Event Taxonomy and Data Models

### Event Schema Design

Every event must carry a minimum set of metadata for routing, tracing, and replay:

```
Canonical Event Structure
──────────────────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────────────────────┐
│  ENVELOPE (routing + tracing metadata)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  id:           "01HNW8R7ZMQZ9RD3K2XB1Y6PQ4"  (ULID, globally unique)│   │
│  │  type:         "com.example.order.placed"      (reverse-DNS)         │   │
│  │  source:       "/services/order-svc"           (URI)                 │   │
│  │  specversion:  "1.0"                           (CloudEvents)         │   │
│  │  time:         "2024-01-15T10:30:00.000Z"      (RFC3339, UTC)        │   │
│  │  datacontenttype: "application/json"                                 │   │
│  │  dataschema:   "https://schema.example.com/order/placed/v1.json"    │   │
│  │  subject:      "order/ORD-123456"              (topic sub-path)      │   │
│  │  traceparent:  "00-abc123-def456-01"           (W3C Trace Context)   │   │
│  │  tracestate:   "vendor=value"                                        │   │
│  │  partitionkey: "user-789"                      (for ordering)        │   │
│  │  causationid:  "parent-event-id"               (causal chain)        │   │
│  │  correlationid:"saga-instance-uuid"            (saga tracking)       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  DATA (domain payload)                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  { orderId: "ORD-123456", userId: "user-789",                       │   │
│  │    items: [...], totalCents: 4999, currency: "USD" }                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

ULID vs UUID:
  UUID v4: Random, no time component → cannot sort chronologically
  UUID v7: Time-based, sortable (recommended for new systems)
  ULID:    128-bit, time prefix (48-bit ms) + randomness (80-bit)
           Monotonically increasing, URL-safe, case-insensitive
           → ideal for event IDs: sortable AND globally unique
```

### Event Versioning

Events are immutable public API. Versioning strategy is critical:

```
Schema Evolution Strategies
────────────────────────────────────────────────────────────
Strategy A: Type versioning
  com.example.order.placed.v1  → v2 when breaking change
  Consumers must handle both types during migration
  Simple, clear, explicit

Strategy B: Field addition only (backward compatible)
  Only ADD optional fields. Never remove or rename.
  Consumers ignore unknown fields (Postel's Law)
  Works until types diverge significantly

Strategy C: Schema registry (Confluent Schema Registry, AWS Glue)
  Producer registers Avro/Protobuf schema → gets schema ID
  Producer serializes: [magic byte][schema_id 4B][avro payload]
  Consumer fetches schema by ID, deserializes
  Full schema evolution rules enforced at write time

Prefer: Type versioning for explicit contracts
        Schema registry for high-volume binary serialization
```

---

## 4. Core EDA Patterns

### 4.1 Publish/Subscribe

Pub/Sub decouples producers from consumers through a **topic** (logical channel). Multiple consumers subscribe independently.

```
Pub/Sub Topology
────────────────────────────────────────────────────────────────────────────────
                           TOPIC: "order.events"
                           ┌──────────────────────┐
  Producer A               │                      │
  (order-svc) ────────────►│      BROKER          │────────► Consumer 1 (inventory-svc)
                           │                      │────────► Consumer 2 (billing-svc)
  Producer B               │  Partitions:         │────────► Consumer 3 (notification-svc)
  (order-svc  ────────────►│  [P0][P1][P2][P3]   │
   instance2)              │                      │
                           └──────────────────────┘

Consumer Group Semantics (Kafka model):
  All consumers in group "inventory-group" share partitions:
    P0 → Consumer 1a
    P1 → Consumer 1a
    P2 → Consumer 1b
    P3 → Consumer 1b
  → Group sees each message ONCE (load balanced)
  → Different groups each see ALL messages (fan-out)

Fan-out:
  inventory-group  → reads all events (stock update)
  billing-group    → reads all events (charge card)
  notification-group → reads all events (email customer)
  analytics-group  → reads all events (data warehouse)
```

### 4.2 Event Streaming

Event streaming differs from messaging in that events are **retained** (for a configurable period or forever), and consumers control their **offset** — they can re-read from any point.

```
Event Stream vs Message Queue
────────────────────────────────────────────────────────────────────────────────
MESSAGE QUEUE (RabbitMQ, SQS)          EVENT STREAM (Kafka, Kinesis)
──────────────────────────────         ──────────────────────────────────────
Messages consumed → deleted            Events retained (days/forever)
Push-based (broker pushes)             Pull-based (consumer controls pace)
At-most-once or at-least-once          Configurable semantics
No replay after ack                    Full replay at any offset
Suitable for: work queues              Suitable for: event sourcing,
  job dispatch, RPC-style              audit log, stream processing,
  async call                           ML feature pipelines, CDC

Kafka Partition as Append-Only Log:
  offset: 0   1   2   3   4   5   6   7
         [e0][e1][e2][e3][e4][e5][e6][e7]
                           ▲             ▲
              Consumer A (lag=3)    Producer (HWM)
                      ▲
           Consumer B (replaying from 2)
```

### 4.3 Event Sourcing

**Event Sourcing** stores every state change as an event, and derives current state by replaying the event log. The database becomes an append-only log; current state is a projection.

```
Traditional CRUD vs Event Sourcing
────────────────────────────────────────────────────────────────────────────────
CRUD:                                   EVENT SOURCING:
  orders table                            events table
  ┌──────────────────────┐               ┌────────────────────────────────────┐
  │ id │ status │ total  │               │ seq │ type            │ payload    │
  │ 1  │ SHIPPED│ $49.99 │               │ 1   │ OrderCreated    │ {...}      │
  └──────────────────────┘               │ 2   │ ItemAdded       │ {...}      │
                                         │ 3   │ PaymentReceived │ {...}      │
  Audit: impossible (state overwritten)   │ 4   │ OrderShipped    │ {...}      │
  Temporal queries: impossible            └────────────────────────────────────┘
  Bug reproduction: hard
                                         To get state: replay events 1..4
                                         Temporal query: replay events 1..3
                                         Bug: replay events with bug input
                                         Audit: full history by definition

Event Store Architecture:
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Append-only event log (one stream per aggregate)                   │
  │                                                                     │
  │  Stream: "Order-ORD-123"                                            │
  │  ┌──────────────────────────────────────────────────────────────┐  │
  │  │ v1: OrderCreated  v2: ItemAdded  v3: Paid  v4: Shipped      │  │
  │  └──────────────────────────────────────────────────────────────┘  │
  │                             │                                       │
  │  Snapshot (optimization):   │  at v100, store full state           │
  │  ┌────────────┐  Rebuild:  │  replay from snapshot + events 101+  │
  │  │ Snapshot   │◄──────────┘                                        │
  │  │ at v100    │                                                     │
  │  └────────────┘                                                     │
  └─────────────────────────────────────────────────────────────────────┘

Aggregate:
  An object cluster treated as a unit for data changes.
  Every state change goes through the aggregate's command handler.
  Aggregate raises events; events mutate internal state.
  Version number on aggregate prevents concurrency conflicts.

  Order aggregate handles command "ShipOrder":
    1. Validate (must be in PAID state)
    2. Raise event OrderShipped { at: now, carrier: "FedEx" }
    3. Apply event: order.status = SHIPPED
    4. Store event with expectedVersion=currentVersion (optimistic lock)
```

#### Go Implementation: Event Store

```go
// eventstore/eventstore.go — Minimal event store with optimistic concurrency
package eventstore

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// Event is the canonical event record persisted to the store.
type Event struct {
	StreamID  string          `json:"stream_id"`
	Version   int64           `json:"version"`   // monotonic per stream
	Type      string          `json:"type"`
	Timestamp time.Time       `json:"timestamp"`
	Data      json.RawMessage `json:"data"`
	Metadata  json.RawMessage `json:"metadata"`
}

// ErrConcurrency is raised when a stream's version doesn't match expected.
type ErrConcurrency struct {
	StreamID        string
	ExpectedVersion int64
	ActualVersion   int64
}

func (e *ErrConcurrency) Error() string {
	return fmt.Sprintf("concurrency conflict on stream %q: expected v%d, got v%d",
		e.StreamID, e.ExpectedVersion, e.ActualVersion)
}

// EventStore is an in-memory event store (swap persistence layer for Postgres/EventStoreDB).
type EventStore struct {
	mu      sync.RWMutex
	streams map[string][]Event
	global  []Event // global ordering for projections
	subs    []chan Event
}

func New() *EventStore {
	return &EventStore{streams: make(map[string][]Event)}
}

// Append writes events to the stream if currentVersion matches.
// expectedVersion = -1 means "stream must not exist".
// expectedVersion =  0 means "any version" (no concurrency check).
func (es *EventStore) Append(ctx context.Context, streamID string,
	expectedVersion int64, events []Event) error {

	es.mu.Lock()
	defer es.mu.Unlock()

	existing := es.streams[streamID]
	currentVersion := int64(len(existing))

	// Optimistic concurrency: -1 = new stream check
	if expectedVersion == -1 && currentVersion != 0 {
		return &ErrConcurrency{streamID, -1, currentVersion}
	}
	if expectedVersion > 0 && currentVersion != expectedVersion {
		return &ErrConcurrency{streamID, expectedVersion, currentVersion}
	}

	// Stamp version and time
	enriched := make([]Event, len(events))
	for i, e := range events {
		e.StreamID  = streamID
		e.Version   = currentVersion + int64(i) + 1
		e.Timestamp = time.Now().UTC()
		enriched[i] = e
	}

	es.streams[streamID] = append(existing, enriched...)
	es.global = append(es.global, enriched...)

	// Notify subscribers (non-blocking fan-out)
	for _, e := range enriched {
		ev := e
		for _, sub := range es.subs {
			select {
			case sub <- ev:
			default: // drop if subscriber is slow — use overflow buffer in prod
			}
		}
	}
	return nil
}

// ReadStream returns all events from version `from` onwards.
func (es *EventStore) ReadStream(ctx context.Context, streamID string, from int64) ([]Event, error) {
	es.mu.RLock()
	defer es.mu.RUnlock()

	events, ok := es.streams[streamID]
	if !ok {
		return nil, fmt.Errorf("stream %q not found", streamID)
	}
	if from > int64(len(events)) {
		return nil, nil
	}
	return events[from:], nil
}

// Subscribe returns a channel that receives all new events globally.
func (es *EventStore) Subscribe() <-chan Event {
	ch := make(chan Event, 1024) // buffered to avoid blocking appends
	es.mu.Lock()
	es.subs = append(es.subs, ch)
	es.mu.Unlock()
	return ch
}

// ─── Aggregate base ──────────────────────────────────────────────────────────

type Aggregate interface {
	StreamID() string
	Version() int64
	Apply(e Event)
	UncommittedEvents() []Event
	ClearUncommitted()
}

// OrderAggregate demonstrates event sourcing for an Order domain object.
type OrderAggregate struct {
	id      string
	version int64
	status  string
	total   int64 // cents
	pending []Event
}

func NewOrder(id string) *OrderAggregate {
	return &OrderAggregate{id: id, status: "NEW"}
}

func (o *OrderAggregate) StreamID() string    { return "Order-" + o.id }
func (o *OrderAggregate) Version() int64      { return o.version }
func (o *OrderAggregate) UncommittedEvents() []Event { return o.pending }
func (o *OrderAggregate) ClearUncommitted()   { o.pending = nil }

// Apply mutates state from an event — pure function, no side effects.
func (o *OrderAggregate) Apply(e Event) {
	o.version = e.Version
	switch e.Type {
	case "OrderCreated":
		var d struct{ Total int64 }
		json.Unmarshal(e.Data, &d)
		o.status = "CREATED"
		o.total = d.Total
	case "OrderPaid":
		o.status = "PAID"
	case "OrderShipped":
		o.status = "SHIPPED"
	case "OrderCancelled":
		o.status = "CANCELLED"
	}
}

// raise records an event as pending (to be stored).
func (o *OrderAggregate) raise(t string, data any) {
	raw, _ := json.Marshal(data)
	o.pending = append(o.pending, Event{Type: t, Data: raw})
	// Apply immediately to keep in-memory state consistent
	o.Apply(Event{Type: t, Data: raw, Version: o.version + 1})
}

// PlaceOrder is a command handler.
func (o *OrderAggregate) PlaceOrder(totalCents int64) error {
	if o.status != "NEW" {
		return fmt.Errorf("order already placed: status=%s", o.status)
	}
	o.raise("OrderCreated", map[string]any{"total": totalCents})
	return nil
}

func (o *OrderAggregate) Pay() error {
	if o.status != "CREATED" {
		return fmt.Errorf("cannot pay order in status %s", o.status)
	}
	o.raise("OrderPaid", map[string]any{})
	return nil
}

func (o *OrderAggregate) Ship() error {
	if o.status != "PAID" {
		return fmt.Errorf("cannot ship unpaid order")
	}
	o.raise("OrderShipped", map[string]any{})
	return nil
}

// LoadFromHistory rebuilds aggregate by replaying events.
func (o *OrderAggregate) LoadFromHistory(events []Event) {
	for _, e := range events {
		o.Apply(e)
	}
}
```

### 4.4 CQRS: Command Query Responsibility Segregation

CQRS separates the **write model** (commands → events → aggregate state) from the **read model** (projections optimized for query patterns).

```
CQRS Architecture
────────────────────────────────────────────────────────────────────────────────
                    ┌──────────────┐
     HTTP POST ────►│ Command Bus  │
     /orders        └──────┬───────┘
                           │ PlaceOrder command
                           ▼
                    ┌──────────────┐
                    │   Order      │  ← Aggregate (write model)
                    │  Aggregate   │    validates invariants
                    └──────┬───────┘
                           │ OrderPlaced event
                           ▼
                    ┌──────────────┐
                    │ Event Store  │  ← Single source of truth
                    │ (append-log) │
                    └──────┬───────┘
                           │ event published
                    ┌──────┴──────────────────────────────────┐
                    │                                         │
                    ▼                                         ▼
          ┌─────────────────┐                    ┌──────────────────────┐
          │  Projection A   │                    │  Projection B         │
          │  (order-list)   │                    │  (inventory-view)     │
          │  Postgres table  │                   │  Redis hash           │
          │  optimized for  │                   │  optimized for        │
          │  list queries   │                   │  stock check queries  │
          └────────┬────────┘                   └──────────┬────────────┘
                   │                                        │
     HTTP GET ─────┴────────────────────────────────────────┘
     /orders

Key insight:
  Write side: normalized, consistent (event store), small writes
  Read side:  denormalized, eventually consistent, optimized per query
  Multiple read models from same event stream — add new ones anytime
  Read models can be rebuilt by replaying all events
```

### 4.5 Saga Pattern

A Saga coordinates a **distributed transaction** across multiple services without 2PC. Each step publishes events; failure triggers compensating actions.

```
Choreography Saga (event-driven, no central coordinator)
──────────────────────────────────────────────────────────────────────────────
Order Placement Saga:

  order-svc                 inventory-svc          payment-svc          ship-svc
     │                           │                      │                   │
     │──OrderCreated────────────►│                      │                   │
     │                           │ reserve stock        │                   │
     │                           │──StockReserved──────►│                   │
     │                           │                      │ charge card       │
     │                           │                      │──PaymentSucceeded─►│
     │                           │                      │                   │ ship
     │◄──────────────────────────────────────────────────OrderShipped───────│

FAILURE PATH:
     │──OrderCreated────────────►│                      │
     │                           │──StockReserved──────►│
     │                           │                      │ card declined
     │                           │◄──PaymentFailed───────│
     │                           │ release stock         │
     │◄──StockReleased────────────│ (compensating action) │
     │ mark order failed         │
     │──OrderFailed──────────────►│ (all consumers notified)

Orchestration Saga (central orchestrator, easier to reason about)
──────────────────────────────────────────────────────────────────────────────
  Client ──► Saga Orchestrator ──► inventory-svc (reserve)
                      │                   │ OK/FAIL
                      │◄──────────────────┘
                      │──► payment-svc (charge)
                      │         │ OK/FAIL
                      │◄─────────┘
                      │──► ship-svc (schedule)
                      │         │ OK/FAIL
                      │◄─────────┘
                      │
                  On any FAIL: orchestrator sends compensation
                    commands in reverse order

Trade-offs:
  Choreography: No SPoF, hard to track overall saga state
  Orchestration: Single SPoF (make it resilient), clear state machine
```

#### Go Implementation: Saga Orchestrator

```go
// saga/orchestrator.go — Durable saga orchestrator with step tracking
package saga

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"
)

type StepStatus int

const (
	StatusPending StepStatus = iota
	StatusRunning
	StatusSucceeded
	StatusFailed
	StatusCompensated
)

type Step struct {
	Name     string
	Execute  func(ctx context.Context, data map[string]any) error
	Rollback func(ctx context.Context, data map[string]any) error
}

type SagaInstance struct {
	ID        string
	Steps     []Step
	stepState []StepStatus
	data      map[string]any
	mu        sync.Mutex
	CreatedAt time.Time
}

func NewSaga(id string, steps []Step) *SagaInstance {
	return &SagaInstance{
		ID:        id,
		Steps:     steps,
		stepState: make([]StepStatus, len(steps)),
		data:      make(map[string]any),
		CreatedAt: time.Now(),
	}
}

// Execute runs all steps in order. On failure, compensates completed steps in reverse.
func (s *SagaInstance) Execute(ctx context.Context) error {
	lastCompleted := -1

	for i, step := range s.Steps {
		s.setStatus(i, StatusRunning)
		log.Printf("[saga %s] executing step %d: %s", s.ID, i, step.Name)

		if err := step.Execute(ctx, s.data); err != nil {
			s.setStatus(i, StatusFailed)
			log.Printf("[saga %s] step %d failed: %v — compensating", s.ID, i, err)
			// Compensate all previously completed steps in reverse
			s.compensate(ctx, lastCompleted)
			return fmt.Errorf("saga failed at step %q: %w", step.Name, err)
		}

		s.setStatus(i, StatusSucceeded)
		lastCompleted = i
	}

	log.Printf("[saga %s] completed successfully", s.ID)
	return nil
}

func (s *SagaInstance) compensate(ctx context.Context, from int) {
	for i := from; i >= 0; i-- {
		step := s.Steps[i]
		if step.Rollback == nil {
			s.setStatus(i, StatusCompensated)
			continue
		}
		log.Printf("[saga %s] compensating step %d: %s", s.ID, i, step.Name)
		if err := step.Rollback(ctx, s.data); err != nil {
			// Compensation failure: requires human intervention / dead letter
			log.Printf("[saga %s] COMPENSATION FAILED step %d: %v — MANUAL ACTION REQUIRED",
				s.ID, i, err)
			// In production: emit alert, persist to dead letter, page on-call
		} else {
			s.setStatus(i, StatusCompensated)
		}
	}
}

func (s *SagaInstance) setStatus(i int, st StepStatus) {
	s.mu.Lock()
	s.stepState[i] = st
	s.mu.Unlock()
}

// Example usage:
func NewOrderSaga(orderID string) *SagaInstance {
	return NewSaga("order-saga-"+orderID, []Step{
		{
			Name: "reserve-inventory",
			Execute: func(ctx context.Context, data map[string]any) error {
				// call inventory-svc gRPC / HTTP
				data["reservationID"] = "res-123"
				return nil
			},
			Rollback: func(ctx context.Context, data map[string]any) error {
				resID, _ := data["reservationID"].(string)
				_ = resID // call inventory-svc release
				return nil
			},
		},
		{
			Name: "charge-payment",
			Execute: func(ctx context.Context, data map[string]any) error {
				data["chargeID"] = "chg-456"
				return nil
			},
			Rollback: func(ctx context.Context, data map[string]any) error {
				chargeID, _ := data["chargeID"].(string)
				_ = chargeID // call payment-svc refund
				return nil
			},
		},
		{
			Name: "schedule-shipment",
			Execute: func(ctx context.Context, data map[string]any) error {
				data["shipmentID"] = "shp-789"
				return nil
			},
			Rollback: func(ctx context.Context, data map[string]any) error {
				return nil // idempotent cancel
			},
		},
	})
}
```

### 4.6 Outbox Pattern

The **Outbox** pattern solves the dual-write problem: you need to update a database AND publish an event atomically.

```
Dual-Write Problem (BROKEN):
──────────────────────────────────────────────────────────────────────────────
  Handler:
    1. BEGIN TRANSACTION
    2. INSERT INTO orders ...        ✓ succeeds
    3. COMMIT                        ✓ succeeds
    4. kafka.Produce("order.events") ✗ CRASH HERE
       → Order exists in DB but NO event was published
       → Inventory never updated, payment never charged

Outbox Pattern (CORRECT):
──────────────────────────────────────────────────────────────────────────────
  Handler:
    1. BEGIN TRANSACTION
    2. INSERT INTO orders ...
    3. INSERT INTO outbox (id, type, payload, published=false)
    4. COMMIT                        ← atomic: both committed or neither

  Outbox Relay (background process):
    5. SELECT * FROM outbox WHERE published=false ORDER BY created_at
    6. kafka.Produce(event)          ← may retry on failure
    7. UPDATE outbox SET published=true WHERE id=?
    ← At-least-once: crash between 6 and 7 = duplicate publish (OK if consumers idempotent)

  Options for relay:
    A. Polling: SELECT every 100ms (simple, adds DB load)
    B. Postgres LISTEN/NOTIFY: trigger on INSERT → relay wakes up
    C. Debezium CDC: reads Postgres WAL (write-ahead log) directly
       → Zero-latency, no polling, reads WAL stream
       → Best production option

Debezium CDC Path:
  ┌──────────────────────────────────────────────────────────────┐
  │  Postgres WAL (Write-Ahead Log)                              │
  │  ... [outbox INSERT LSN 1234] ...                            │
  └──────────────────────────────┬───────────────────────────────┘
                                 │ pg_logical_replication_slot
                                 ▼
                    ┌─────────────────────┐
                    │  Debezium Connector │ (Kafka Connect)
                    │  reads WAL stream   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Kafka Topic        │ (order.events)
                    └─────────────────────┘
```

### 4.7 Dead Letter Queue

When a consumer fails to process an event after N retries, it routes the event to a **Dead Letter Queue (DLQ)** for later analysis and reprocessing.

```
DLQ Flow
────────────────────────────────────────────────────────────────────────────────
  Kafka Topic: "order.events"
       │
       ▼
  Consumer (inventory-svc)
       │
       │ attempt 1: fails (transient error)
       │ wait 1s (exponential backoff)
       │ attempt 2: fails
       │ wait 2s
       │ attempt 3: fails
       │ wait 4s
       │ attempt 4: fails
       │
       ▼
  Produce to DLQ: "order.events.dlq"
  Include headers:
    x-retry-count: 4
    x-last-error: "connection refused"
    x-original-topic: "order.events"
    x-original-partition: 2
    x-original-offset: 18374
    x-failed-at: "2024-01-15T10:30:00Z"
       │
       ▼
  DLQ Consumer (monitoring / ops tool)
    - Alert on-call
    - Store to S3 for analysis
    - Provide UI to replay / discard
    - Auto-retry after human inspection

Retry strategies:
  Immediate retry: for transient network errors (max 3x)
  Exponential backoff: 1s, 2s, 4s, 8s... with jitter
  Dead letter after: 5-10 total attempts
  Retry DLQ: schedule replay after fix deployed
```

### 4.8 Event Replay and Time Travel

```
Event Replay Architecture
────────────────────────────────────────────────────────────────────────────────
  WHY REPLAY:
    1. New service: needs history (inventory-svc added 6 months later)
    2. Bug fix: projection had a bug, rebuild from scratch
    3. Testing: replay prod events against new code in staging
    4. Audit: prove what happened at any point in time
    5. Analytics: feed historical events into ML training pipeline

  HOW (Kafka):
    consumer.seek(TopicPartition("order.events", 0), 0)
    → reads from beginning of partition
    → OR seek by timestamp: consumer.offsetsForTimes({"order.events-0": epochMs})

  Replay isolation:
    Use a SEPARATE consumer group for replay
    Never replay into production consumer group (would skew offsets)

  Rate limiting during replay:
    Replay 6 months of events at 100x speed can overwhelm downstream services
    Use token bucket / rate limiter on replay consumer
    OR: replay into staging env, validate, then deploy

  Snapshot + Replay optimization:
    Full replay of 10B events is slow (hours)
    Snapshots every N events or every T hours:
      Take snapshot at event 1,000,000
      Replay = load snapshot + replay events 1,000,001 to now
      Reduces replay from O(total events) to O(events since last snapshot)
```

---

## 5. Delivery Semantics and Ordering

### The Three Guarantees

```
DELIVERY SEMANTICS
────────────────────────────────────────────────────────────────────────────────
AT-MOST-ONCE
  Producer sends. May lose message. Broker never retries.
  Consumer acks before processing.
  Use case: metrics/telemetry where loss is acceptable
  Implementation: producer fire-and-forget, no acks
  Throughput: highest (no ack round-trip)

AT-LEAST-ONCE
  Producer retries until ack received. Messages MAY be duplicated.
  Consumer must be IDEMPOTENT (handle duplicates).
  Use case: most business events (order placed, payment received)
  Implementation: producer acks=all, consumer idempotent check
  Idempotency: event_id → deduplicate in DB, Redis, or Bloom filter

EXACTLY-ONCE (E2E)
  Message delivered exactly once even with retries and failures.
  Extremely hard to guarantee end-to-end.
  Only achievable with cooperative producer+broker+consumer.

  Kafka exactly-once (Kafka Transactions):
    1. Producer transactional.id → idempotent per partition
    2. transactional produce: atomic batch across partitions
    3. Consumer: read_committed isolation level
    4. Consumer offset committed IN SAME Kafka transaction as output

  Reality:
    "Exactly-once within Kafka" is achievable.
    "Exactly-once to external system" requires 2PC or idempotent consumers.
    2PC is slow and fragile. Idempotent consumers are preferred.

Idempotent Consumer Pattern:
  ┌──────────────────────────────────────────────────────────────────────┐
  │  On receive event(id="evt-123"):                                    │
  │    IF processed_events.contains("evt-123"):                         │
  │        log.Info("duplicate, skipping")                              │
  │        ack()                                                        │
  │        return                                                       │
  │    ELSE:                                                            │
  │        BEGIN TRANSACTION                                            │
  │        process_event()                                              │
  │        INSERT INTO processed_events(id) VALUES("evt-123")          │
  │        COMMIT                                                       │
  │        ack()                                                        │
  └──────────────────────────────────────────────────────────────────────┘
  Deduplication window: set TTL on processed_events (e.g., 7 days)
  For high volume: Redis SET NX "dedup:evt-123" EX 604800
```

### Ordering Guarantees

```
ORDERING IN DISTRIBUTED SYSTEMS
────────────────────────────────────────────────────────────────────────────────
Kafka ordering guarantees:
  WITHIN a partition: strict ordering guaranteed
  ACROSS partitions: no ordering guarantee
  → All events for one user/order MUST go to same partition
  → Partition key = userId, orderId, accountId

Problem: Hot partitions
  If key space is skewed (one user sends 90% of events),
  one partition gets all the load.
  Solution: compound key = userId + random suffix
             OR: time-based repartitioning

Causal ordering (not just time ordering):
  "Event B caused Event A" → B must be processed after A
  Even if A arrives before B due to network delay

  Vector clocks:
    Producer A: VC = {A:1, B:0}
    Producer B: VC = {A:1, B:1}  ← B happened after A (saw A's event)
    Consumer sees VC {A:1, B:1}: knows A < B

  Lamport timestamps:
    Each event carries a logical timestamp
    On send: ts = max(local_ts, received_ts) + 1
    Gives total order but not causality (two unrelated events get ordered arbitrarily)

Wall clock problems:
  NTP is not monotonic (can go backwards)
  System clocks between datacenters can differ by seconds
  NEVER use wall clock alone for event ordering
  Use: Kafka offset (within partition), ULID, or hybrid logical clocks (HLC)
```

---

## 6. Broker Internals: Deep Dive

### 6.1 Apache Kafka

Kafka is a distributed, partitioned, replicated commit log. Understanding its internals is essential for designing high-throughput event systems.

```
Kafka Internal Architecture
────────────────────────────────────────────────────────────────────────────────

CLUSTER TOPOLOGY:
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Kafka Cluster                                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Broker 1    │    │  Broker 2    │    │  Broker 3    │                  │
│  │  (Leader P0) │    │  (Leader P1) │    │  (Leader P2) │                  │
│  │  (Follower P1)│   │  (Follower P2)│   │  (Follower P0)│                │
│  │  (Follower P2)│   │  (Follower P0)│   │  (Follower P1)│                │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│          │                  │                   │                           │
│          └──────────────────┴───────────────────┘                           │
│                    Controller (KRaft mode, Raft consensus)                  │
│                    (previously ZooKeeper, deprecated)                       │
└─────────────────────────────────────────────────────────────────────────────┘

PARTITION INTERNALS (on disk):
  /kafka-logs/topic-name-partition-0/
  ├── 00000000000000000000.log      ← segment file (raw bytes, append-only)
  ├── 00000000000000000000.index    ← sparse offset → file position index
  ├── 00000000000000000000.timeindex← sparse timestamp → offset index
  ├── 00000000000001000000.log      ← next segment (started at offset 1M)
  ├── 00000000000001000000.index
  └── leader-epoch-checkpoint

SEGMENT FILE STRUCTURE:
  [batch 1: offset=0, N=5 messages]
    [message 0: key, value, headers, timestamp, crc]
    [message 1: ...]
    ...
  [batch 2: offset=5, N=3 messages]
    ...

  RecordBatch header (v2):
    baseOffset (8B)   ← first offset in batch
    batchLength (4B)  ← total length of batch
    leaderEpoch (4B)  ← for fencing zombie leaders
    magic (1B)        ← version 2
    crc (4B)          ← CRC32C of remaining batch
    attributes (2B)   ← compression, timestamp type, transactional
    lastOffsetDelta (4B)
    firstTimestamp (8B)
    maxTimestamp (8B)
    producerId (8B)   ← for exactly-once / transactions
    producerEpoch (2B)
    baseSequence (4B) ← for idempotent producer
    records: [delta-encoded key, value, headers, timestamp offset]

INDEX FILE:
  Sparse: every ~4KB → entry maps offset to byte position in .log
  Binary search to find offset: O(log n) in index, then O(1) seek in log

READ PATH (consumer fetch):
  1. Consumer sends FetchRequest(topic, partition, offset, maxBytes)
  2. Broker locates segment file for that offset (via index)
  3. sendfile(segment_fd, socket_fd, ...) ← ZERO-COPY
     DMA: disk → page cache → NIC buffer (no user-space copy)
  4. Consumer receives data, advances offset

WRITE PATH (producer):
  1. ProduceRequest(acks, topic, partition, RecordBatch)
  2. Leader appends to .log file (page cache write)
  3. Waits for acks:
     acks=0: don't wait (fire and forget)
     acks=1: wait for leader fsync
     acks=-1/all: wait for ISR (in-sync replicas) to ack
  4. Followers fetch from leader (same zero-copy path)
  5. Leader sends ack to producer after ISR threshold met

ISR (In-Sync Replicas):
  Set of replicas caught up to within replica.lag.time.max.ms (10s default)
  min.insync.replicas = 2: require 2+ ISR for acks=all
  If only 1 ISR left and min.insync.replicas=2: producer gets NotEnoughReplicas

CONSUMER GROUP REBALANCING:
  Triggered by: member join/leave, partition count change, heartbeat timeout
  Protocol: JoinGroup → SyncGroup → Heartbeat → LeaveGroup
  Strategies:
    Range:       partition 0-3 → consumer 0, 4-7 → consumer 1
    RoundRobin:  P0→C0, P1→C1, P2→C0, P3→C1
    Sticky:      minimize reassignments on rebalance
    Cooperative Sticky: incremental rebalance (no stop-the-world)
  → Use COOPERATIVE STICKY in production (no global pause)
```

#### Kafka Producer in Go

```go
// kafka/producer.go — Production Kafka producer with exactly-once semantics
package kafka

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/twmb/franz-go/pkg/kgo"
	"github.com/twmb/franz-go/pkg/kgo/kotel"
)

type Event struct {
	ID        string          `json:"id"`
	Type      string          `json:"type"`
	Source    string          `json:"source"`
	Timestamp time.Time       `json:"timestamp"`
	Data      json.RawMessage `json:"data"`
}

type Producer struct {
	client *kgo.Client
	topic  string
}

func NewProducer(brokers []string, topic string, transactionalID string) (*Producer, error) {
	opts := []kgo.Opt{
		kgo.SeedBrokers(brokers...),
		kgo.DefaultProduceTopic(topic),

		// Idempotent producer (exactly-once within broker)
		kgo.RequiredAcks(kgo.AllISRAcks()),
		kgo.ProducerBatchMaxBytes(1 << 20), // 1MB batch
		kgo.ProducerLinger(5 * time.Millisecond),

		// Compression
		kgo.ProducerBatchCompression(
			kgo.Lz4Compression(),
			kgo.SnappyCompression(),
		),

		// Retry
		kgo.RetryBackoffFn(func(tries int) time.Duration {
			d := time.Duration(tries) * 100 * time.Millisecond
			if d > 10*time.Second {
				d = 10 * time.Second
			}
			return d
		}),
	}

	// Transactional (exactly-once end-to-end)
	if transactionalID != "" {
		opts = append(opts, kgo.TransactionalID(transactionalID))
	}

	client, err := kgo.NewClient(opts...)
	if err != nil {
		return nil, fmt.Errorf("kafka client: %w", err)
	}
	return &Producer{client: client, topic: topic}, nil
}

// Produce sends a single event with partition affinity by key.
func (p *Producer) Produce(ctx context.Context, key string, event Event) error {
	event.Timestamp = time.Now().UTC()
	payload, err := json.Marshal(event)
	if err != nil {
		return err
	}

	rec := &kgo.Record{
		Topic: p.topic,
		Key:   []byte(key),
		Value: payload,
		Headers: []kgo.RecordHeader{
			{Key: "content-type", Value: []byte("application/json")},
			{Key: "event-type", Value: []byte(event.Type)},
			{Key: "event-id", Value: []byte(event.ID)},
		},
	}

	// Synchronous produce with timeout
	results := p.client.ProduceSync(ctx, rec)
	for _, result := range results {
		if result.Err != nil {
			return fmt.Errorf("produce %q: %w", event.ID, result.Err)
		}
		log.Printf("[kafka] produced %s to %s[%d]@%d",
			event.ID, result.Record.Topic,
			result.Record.Partition, result.Record.Offset)
	}
	return nil
}

// ProduceBatch produces multiple events in a single batch (high throughput).
func (p *Producer) ProduceBatch(ctx context.Context, events []struct {
	Key   string
	Event Event
}) error {
	records := make([]*kgo.Record, len(events))
	for i, ev := range events {
		payload, _ := json.Marshal(ev.Event)
		records[i] = &kgo.Record{
			Topic: p.topic,
			Key:   []byte(ev.Key),
			Value: payload,
		}
	}

	results := p.client.ProduceSync(ctx, records...)
	for _, r := range results {
		if r.Err != nil {
			return r.Err
		}
	}
	return nil
}

func (p *Producer) Close() { p.client.Close() }
```

#### Kafka Consumer in Go (exactly-once via transactions)

```go
// kafka/consumer.go — Transactional consumer (read-process-produce exactly-once)
package kafka

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/twmb/franz-go/pkg/kgo"
)

type Handler func(ctx context.Context, event Event) error

type Consumer struct {
	client      *kgo.Client
	handler     Handler
	outputTopic string
}

func NewConsumer(brokers []string, topics []string, groupID string,
	outputTopic string, transactionalID string, handler Handler) (*Consumer, error) {

	opts := []kgo.Opt{
		kgo.SeedBrokers(brokers...),
		kgo.ConsumeTopics(topics...),
		kgo.ConsumerGroup(groupID),

		// Read only committed records (for exactly-once)
		kgo.FetchIsolationLevel(kgo.ReadCommitted()),

		// Cooperative rebalancing — no stop-the-world
		kgo.Balancers(kgo.CooperativeStickyBalancer()),

		// Manual offset commit (we commit within transaction)
		kgo.DisableAutoCommit(),

		// Fetch settings
		kgo.FetchMinBytes(1),
		kgo.FetchMaxBytes(50 << 20), // 50MB
		kgo.FetchMaxWait(500),       // ms

		// Transactional producer for output
		kgo.TransactionalID(transactionalID),
		kgo.RequiredAcks(kgo.AllISRAcks()),
	}

	client, err := kgo.NewClient(opts...)
	if err != nil {
		return nil, err
	}

	return &Consumer{
		client:      client,
		handler:     handler,
		outputTopic: outputTopic,
	}, nil
}

// Run is the main processing loop with exactly-once semantics.
func (c *Consumer) Run(ctx context.Context) error {
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		// Fetch records
		fetches := c.client.PollRecords(ctx, 1000)
		if fetches.IsClientClosed() {
			return fmt.Errorf("client closed")
		}
		if errs := fetches.Errors(); len(errs) > 0 {
			for _, e := range errs {
				log.Printf("[consumer] fetch error: %v", e.Err)
			}
			continue
		}

		if fetches.Empty() {
			continue
		}

		// Begin Kafka transaction
		if err := c.client.BeginTransaction(); err != nil {
			return fmt.Errorf("begin transaction: %w", err)
		}

		var commitErr error
		fetches.EachRecord(func(rec *kgo.Record) {
			if commitErr != nil {
				return
			}

			var event Event
			if err := json.Unmarshal(rec.Value, &event); err != nil {
				log.Printf("[consumer] unmarshal error: %v", err)
				return
			}

			// Process — if handler errors, we abort the transaction
			if err := c.handler(ctx, event); err != nil {
				log.Printf("[consumer] handler error for %s: %v", event.ID, err)
				commitErr = err
			}
		})

		if commitErr != nil {
			// Abort: records will be redelivered
			if err := c.client.AbortBufferedRecords(ctx); err != nil {
				log.Printf("[consumer] abort error: %v", err)
			}
			c.client.EndTransaction(ctx, kgo.TryAbort)
			continue
		}

		// Commit offsets as part of transaction
		if err := c.client.EndTransaction(ctx, kgo.TryCommit); err != nil {
			log.Printf("[consumer] commit error: %v", err)
		}
	}
}
```

---

### 6.2 NATS / JetStream

NATS is a high-performance, lightweight messaging system written in Go. JetStream is its persistence layer adding durable storage, consumers, and streams.

```
NATS Architecture
────────────────────────────────────────────────────────────────────────────────
NATS Core (no persistence):
  At-most-once, pub/sub, request/reply, queue groups
  Subjects: hierarchical, wildcard-enabled
    "order.placed"         → exact match
    "order.*"              → one level wildcard: order.placed, order.paid
    "order.>"             → recursive wildcard: order.placed, order.items.added

  ┌────────────┐   pub("order.placed", data)    ┌────────────────────┐
  │  Producer  │──────────────────────────────►  │  NATS Server       │
  └────────────┘                                 │  (cluster: 3+ nodes)│
                                                 │  Raft consensus     │
                  sub("order.placed")            │                    │
  ┌────────────┐◄──────────────────────────────── │                    │
  │ Consumer A │                                 └────────────────────┘
  └────────────┘
  ┌────────────┐
  │ Consumer B │ (each gets a copy — fan-out)
  └────────────┘

NATS JetStream (with persistence):
  Streams: named durable storage for subjects
  Consumers: named subscription cursors (push or pull)

  Stream "ORDERS":
    subjects: ["order.>"]     ← captures all order events
    storage: file              ← disk-backed
    retention: limits          ← time or size based
    replicas: 3                ← raft-replicated across cluster
    maxBytes: 10GB
    maxAge: 7d
    discard: old               ← drop oldest when full

  Consumer "inventory-consumer":
    stream: ORDERS
    durable: true              ← survives restart
    ack_policy: explicit       ← consumer must ack
    ack_wait: 30s              ← re-deliver if not acked
    max_deliver: 5             ← DLQ after 5 failures
    deliver_policy: all        ← start from beginning
    filter_subject: "order.placed"
    pull: true                 ← consumer controls pace

Push consumer:
  Server pushes messages to consumer at server rate
  Easier to code, harder to apply backpressure

Pull consumer:
  Consumer fetches N messages when ready (Fetch(ctx, 100))
  Natural backpressure, preferred for high-throughput processing
```

#### Go Implementation: NATS JetStream Producer/Consumer

```go
// nats/stream.go — JetStream producer and durable pull consumer
package natsstream

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/nats-io/nats.go"
	"github.com/nats-io/nats.go/jetstream"
)

const (
	StreamName = "ORDERS"
	Subject    = "order.placed"
)

func Connect(url string) (*nats.Conn, error) {
	return nats.Connect(url,
		nats.MaxReconnects(-1),                        // retry forever
		nats.ReconnectWait(2*time.Second),
		nats.PingInterval(20*time.Second),
		nats.MaxPingsOutstanding(3),
		nats.ErrorHandler(func(_ *nats.Conn, _ *nats.Subscription, err error) {
			log.Printf("[nats] error: %v", err)
		}),
		nats.DisconnectErrHandler(func(_ *nats.Conn, err error) {
			log.Printf("[nats] disconnected: %v", err)
		}),
	)
}

func EnsureStream(ctx context.Context, js jetstream.JetStream) (jetstream.Stream, error) {
	return js.CreateOrUpdateStream(ctx, jetstream.StreamConfig{
		Name:        StreamName,
		Subjects:    []string{"order.>"},
		Storage:     jetstream.FileStorage,
		Replicas:    3,
		MaxAge:      7 * 24 * time.Hour,
		MaxBytes:    10 << 30, // 10GB
		Discard:     jetstream.DiscardOld,
		Retention:   jetstream.LimitsPolicy,
		Compression: jetstream.S2Compression,
		// Enable deduplication window (event-ID based)
		Duplicates: 2 * time.Minute,
	})
}

type Producer struct {
	js jetstream.JetStream
}

func NewProducer(nc *nats.Conn) (*Producer, error) {
	js, err := jetstream.New(nc)
	if err != nil {
		return nil, err
	}
	return &Producer{js: js}, nil
}

func (p *Producer) Publish(ctx context.Context, event map[string]any) error {
	payload, err := json.Marshal(event)
	if err != nil {
		return err
	}
	id, _ := event["id"].(string)

	ack, err := p.js.Publish(ctx, Subject, payload,
		// Idempotent: Nats-Msg-Id header deduplicates within stream.Duplicates window
		jetstream.WithMsgID(id),
	)
	if err != nil {
		return fmt.Errorf("publish: %w", err)
	}
	log.Printf("[nats] published to %s seq=%d", ack.Stream, ack.Sequence)
	return nil
}

type Consumer struct {
	consumer jetstream.Consumer
}

func NewConsumer(ctx context.Context, nc *nats.Conn, durableName string) (*Consumer, error) {
	js, err := jetstream.New(nc)
	if err != nil {
		return nil, err
	}

	stream, err := js.Stream(ctx, StreamName)
	if err != nil {
		return nil, err
	}

	consumer, err := stream.CreateOrUpdateConsumer(ctx, jetstream.ConsumerConfig{
		Name:           durableName,
		Durable:        durableName,
		FilterSubject:  Subject,
		AckPolicy:      jetstream.AckExplicitPolicy,
		AckWait:        30 * time.Second,
		MaxDeliver:     5,
		DeliverPolicy:  jetstream.DeliverAllPolicy,
		// Backoff for retry: 1s, 5s, 30s
		BackOff: []time.Duration{
			1 * time.Second,
			5 * time.Second,
			30 * time.Second,
		},
	})
	if err != nil {
		return nil, err
	}

	return &Consumer{consumer: consumer}, nil
}

// Process uses pull-based fetch with manual ack — best for controlled throughput.
func (c *Consumer) Process(ctx context.Context, handler func(msg jetstream.Msg) error) error {
	for {
		select {
		case <-ctx.Done():
			return nil
		default:
		}

		// Fetch up to 100 messages, wait up to 5s
		msgs, err := c.consumer.Fetch(100, jetstream.FetchMaxWait(5*time.Second))
		if err != nil {
			if ctx.Err() != nil {
				return nil
			}
			log.Printf("[nats consumer] fetch error: %v", err)
			time.Sleep(time.Second)
			continue
		}

		for msg := range msgs.Messages() {
			if err := handler(msg); err != nil {
				log.Printf("[nats consumer] handler error: %v", err)
				// Negative ack: server will redeliver after AckWait
				msg.Nak()
				continue
			}
			// Explicit ack: advances consumer position
			if err := msg.Ack(); err != nil {
				log.Printf("[nats consumer] ack error: %v", err)
			}
		}

		if err := msgs.Error(); err != nil {
			log.Printf("[nats consumer] messages error: %v", err)
		}
	}
}
```

---

### 6.3 RabbitMQ (AMQP)

RabbitMQ implements AMQP 0-9-1 and uses a routing model based on **exchanges** and **bindings**.

```
RabbitMQ Routing Model
────────────────────────────────────────────────────────────────────────────────
  Producer → Exchange → [Binding rules] → Queue → Consumer

Exchange types:
  Direct:  routing_key == binding_key  (exact match)
  Topic:   routing_key matches pattern (* = one word, # = zero or more)
  Fanout:  all bound queues get a copy (ignores routing key)
  Headers: match on message header map (complex routing)

Example topology:
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Producer publishes to exchange "order-events"                          │
  │  routing_key = "order.placed.us-east-1"                                 │
  │                                                                         │
  │  Bindings:                                                              │
  │    "order.#"        → queue "all-orders"       (all order events)       │
  │    "order.placed.*" → queue "new-orders"       (just placed orders)     │
  │    "order.*.us-*"   → queue "us-orders"        (US orders only)         │
  │    (fanout)         → queue "audit-log"        (everything)             │
  └──────────────────────────────────────────────────────────────────────────┘

Queue properties:
  durable=true:      survives broker restart
  exclusive=false:   can have multiple consumers
  auto-delete=false: not deleted when last consumer leaves
  x-message-ttl:     per-message or per-queue TTL
  x-dead-letter-exchange: DLQ routing

Consumer ack modes:
  auto ack:  ack immediately on delivery (fast, can lose messages)
  manual ack: consumer calls basic.ack / basic.nack
  prefetch (QoS): basic.qos(prefetch_count=50)
    → max 50 unacked messages in flight per consumer
    → natural backpressure / rate limiting
```

---

### 6.4 Redis Streams

Redis Streams (XADD / XREAD) provide a durable, consumer-group-aware event stream baked into Redis.

```
Redis Streams Data Model
────────────────────────────────────────────────────────────────────────────────
  Stream key: "events:orders"
  Entry ID format: <millisecondsTime>-<sequenceNumber>
    e.g. "1705320000000-0", "1705320000000-1"

  XADD events:orders * type order.placed userId 123 orderId ORD-456
    → appends entry, returns auto-generated ID

  Stream entries (like array of maps):
  ┌────────────────────────────────────────────────────────────┐
  │  1705320000000-0: {type: order.placed, userId: 123, ...}  │
  │  1705320000001-0: {type: order.paid, orderId: ORD-456}    │
  │  1705320000002-0: {type: order.shipped, ...}              │
  └────────────────────────────────────────────────────────────┘

Consumer Groups:
  XGROUP CREATE events:orders inventory-group $ MKSTREAM
    → group starts reading from NOW ($), or from 0 for full history

  XREADGROUP GROUP inventory-group consumer-1 COUNT 10 STREAMS events:orders >
    → > means "give me new pending entries" for this group
    → entries go to Pending Entries List (PEL) until acked

  XACK events:orders inventory-group 1705320000000-0
    → removes from PEL (marks as processed)

  XPENDING events:orders inventory-group - + 10
    → list entries in PEL (not yet acked) — use for retry/DLQ logic

  XCLAIM events:orders inventory-group new-consumer 60000 1705320000000-0
    → steal pending entry from dead consumer after 60s idle

Persistence:
  Append-only file (AOF) or RDB snapshot
  Stream has MAXLEN: XADD events:orders MAXLEN ~ 100000 *
  ~ means approximate trim (faster than exact)
```

---

## 7. Cloud-Native EDA

### 7.1 AWS: Kinesis, EventBridge, SNS/SQS

```
AWS Event-Driven Services Landscape
────────────────────────────────────────────────────────────────────────────────
┌──────────────────────────────────────────────────────────────────────────────┐
│                                   AWS                                         │
│                                                                              │
│  High-throughput streaming        Event routing / orchestration              │
│  ┌─────────────────────┐         ┌─────────────────────────────────────────┐│
│  │  Kinesis Data        │         │  EventBridge                            ││
│  │  Streams             │         │  Event Bus → Rules → Targets            ││
│  │  - Shards (1MB/s in)│         │  Schema Registry                        ││
│  │  - 7-day retention  │         │  Pipes (filter, transform)              ││
│  │  - Enhanced fanout  │         │  Scheduler                              ││
│  └─────────────────────┘         └─────────────────────────────────────────┘│
│                                                                              │
│  Messaging                        Managed Kafka                             │
│  ┌────────────────┐  ┌─────────┐  ┌───────────────────────────────────────┐│
│  │  SNS           │  │  SQS    │  │  MSK (Managed Streaming for Kafka)    ││
│  │  (pub/sub fan- │  │  queues │  │  Serverless or provisioned            ││
│  │   out, push)   │  │  FIFO   │  │  IAM auth, TLS, at-rest encryption    ││
│  └────────────────┘  └─────────┘  └───────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘

KINESIS SHARD INTERNALS:
  Each shard:
    - 1 MB/s input, 2 MB/s output
    - 1000 records/s input
    - Default: 24h retention (up to 7 days)
    - Ordered within shard (partition key → shard assignment)

  Enhanced fanout:
    Each consumer gets dedicated 2MB/s throughput via HTTP/2 push
    Up to 20 consumers per stream
    Uses subscribeToShard API (server push vs polling)

  Kinesis vs Kafka:
    Kinesis: fully managed, lower ops, AWS-native integrations
    Kafka: more flexible, portable, higher throughput per $,
           Kafka Connect ecosystem, stream processing (ksqlDB/Flink)

EVENTBRIDGE ARCHITECTURE:
  ┌───────────────────────────────────────────────────────────────────────┐
  │  Event Bus (default or custom)                                       │
  │                                                                      │
  │  Rule: { source: ["com.example.order"],                              │
  │          detail-type: ["order.placed"],                              │
  │          detail: { amount: [{ numeric: [">=", 100] }] } }            │
  │                                                                      │
  │  Targets: Lambda, SQS, SNS, Kinesis, Step Functions, API Gateway,   │
  │           EventBridge Pipes → Kinesis → Lambda (stream processing)  │
  └───────────────────────────────────────────────────────────────────────┘

  EventBridge Pipes: serverless event routing with filter + transform
    Source: Kinesis/SQS/DynamoDB Streams
    Filter: JSONPath-based event filtering
    Enrichment: Lambda (optional transform)
    Target: any AWS service

SNS/SQS FAN-OUT PATTERN:
  ┌─────────┐
  │  SNS    │ ← single publish point
  │  Topic  │
  └────┬────┘
       │
  ┌────┴──────────────────────────────────────────┐
  │    Subscriptions (with filter policies)       │
  │                                               │
  ▼              ▼              ▼              ▼
  SQS Q1        SQS Q2        Lambda        HTTP
  (inventory)   (billing)     (notify)      (3rd party)
  FIFO queue    FIFO queue    async         webhook

SQS FIFO Queues:
  Message Group ID → ordering within group
  Deduplication ID → exactly-once within 5-min window
  Throughput: 3000 msg/s per queue (with batching)
```

### 7.2 GCP: Pub/Sub, Eventarc

```
GCP Pub/Sub Architecture
────────────────────────────────────────────────────────────────────────────────
  Publisher → Topic → [Subscription] → Subscriber

  Topic: global, multi-region
  Message: { data: base64, attributes: map[string]string, messageId, publishTime }
  Subscription types:
    Pull:   subscriber calls pull API (recommended for throughput)
    Push:   Pub/Sub sends HTTP POST to subscriber URL

  Delivery guarantees:
    At-least-once (default)
    Exactly-once: subscription.enable_exactly_once_delivery = true
      → server-side deduplication (100% effective within retention window)

  Retention: 7 days max (messages available for replay)
  Message ordering: enable_message_ordering + ordering key → per-key ordering

  Dead letter policy:
    max_delivery_attempts: 5
    dead_letter_topic: "projects/x/topics/orders-dlq"

  Filtering at subscription level:
    subscription.filter = 'attributes.eventType = "order.placed"'
    → Only matching messages delivered to this subscription

  Pub/Sub Lite: Zonal, cheaper, lower latency, 10x cost reduction
    Reservation-based capacity
    Topic zones: us-central1-a, us-central1-b

Eventarc:
  Routes events from GCP services (Cloud Storage, BigQuery, Audit Logs)
  to Cloud Run, Cloud Functions, GKE, Workflows
  Backed by Pub/Sub or direct event triggers
  CloudEvents format (CloudEvents 1.0 spec compliant)
```

### 7.3 Azure: Event Hub, Event Grid

```
Azure Event Services
────────────────────────────────────────────────────────────────────────────────
EVENT HUB:
  Azure's Kafka-compatible event streaming service
  Partitions: 1-2048
  Consumer groups: up to 20
  Retention: 1-90 days
  Kafka protocol: port 9093 (TLS), SASL OAUTHBEARER (AAD)
  Capture: auto-archive to Azure Blob/ADLS in Avro format

  Tiers:
    Basic: 1 consumer group, 1 day retention
    Standard: 20 consumer groups, 7 day retention
    Premium: dedicated compute, 90 day retention, schema registry
    Dedicated: single-tenant, highest throughput

  Throughput Units (TUs):
    1 TU = 1 MB/s ingress, 2 MB/s egress, 1000 events/s

EVENT GRID:
  Event routing (like EventBridge)
  System topics: Azure services emit events (Blob created, VM deleted...)
  Custom topics: your services emit CloudEvents
  Partners: third-party event sources (Datadog, SAP, Auth0)
  Handlers: Azure Functions, Event Hub, Service Bus, Logic Apps, Webhook

  Push delivery (EventGrid pushes to subscribers)
  Retry: exponential backoff up to 24h
  Dead lettering: to storage account

SERVICE BUS (RabbitMQ equivalent):
  Topics, subscriptions, correlation filters
  At-least-once, FIFO sessions, dead letter queue
  Transactions: atomic send across queues
  Duplicate detection: 10s-7day window
```

---

## 8. CloudEvents Standard

CloudEvents is a CNCF specification for describing events in a common format, enabling portability across brokers and clouds.

```
CloudEvents 1.0 Specification
────────────────────────────────────────────────────────────────────────────────
Required attributes:
  id:            unique event identifier
  source:        URI of the event producer
  specversion:   "1.0"
  type:          reverse-DNS event type

Optional attributes (commonly used):
  time:          RFC3339 timestamp
  datacontenttype: "application/json"
  dataschema:    schema URI
  subject:       topic sub-path

Extension attributes (register with CNCF):
  partitionkey:  for ordered delivery
  traceparent:   W3C Trace Context
  tracestate:    W3C Trace Context
  sequence:      monotonic sequence within source
  sampledrate:   for sampling / rate limiting

JSON Wire Format:
{
  "specversion": "1.0",
  "type": "com.example.order.placed",
  "source": "/services/order-svc",
  "subject": "order/ORD-123456",
  "id": "01HNW8R7ZMQZ9RD3K2XB1Y6PQ4",
  "time": "2024-01-15T10:30:00.000Z",
  "datacontenttype": "application/json",
  "dataschema": "https://schema.example.com/order/placed/v1",
  "partitionkey": "user-789",
  "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
  "data": {
    "orderId": "ORD-123456",
    "userId": "user-789",
    "totalCents": 4999
  }
}

Binary format (HTTP):
  ce-specversion: 1.0
  ce-type: com.example.order.placed
  ce-source: /services/order-svc
  ce-id: 01HNW8R7ZMQZ9RD3K2XB1Y6PQ4
  Content-Type: application/json
  Body: {"orderId": "ORD-123456", ...}

Protocol bindings:
  HTTP (Webhook)
  AMQP 1.0
  Kafka (ce_* headers)
  MQTT
  NATS
```

#### Go Implementation: CloudEvents

```go
// cloudevents/event.go — CloudEvents 1.0 envelope
package cloudevents

import (
	"encoding/json"
	"fmt"
	"net/url"
	"time"

	"github.com/oklog/ulid/v2"
	"math/rand"
)

type CloudEvent struct {
	// Required
	SpecVersion string `json:"specversion"`
	Type        string `json:"type"`
	Source      string `json:"source"`
	ID          string `json:"id"`
	// Optional
	Subject         string          `json:"subject,omitempty"`
	Time            time.Time       `json:"time,omitempty"`
	DataContentType string          `json:"datacontenttype,omitempty"`
	DataSchema      string          `json:"dataschema,omitempty"`
	Data            json.RawMessage `json:"data,omitempty"`
	// Extensions
	PartitionKey string `json:"partitionkey,omitempty"`
	TraceParent  string `json:"traceparent,omitempty"`
	TraceState   string `json:"tracestate,omitempty"`
	CorrelationID string `json:"correlationid,omitempty"`
	CausationID  string `json:"causationid,omitempty"`
}

func New(eventType, source, subject string, data any) (*CloudEvent, error) {
	if _, err := url.Parse(source); err != nil {
		return nil, fmt.Errorf("invalid source URI: %w", err)
	}

	rawData, err := json.Marshal(data)
	if err != nil {
		return nil, fmt.Errorf("marshal data: %w", err)
	}

	entropy := ulid.Monotonic(rand.New(rand.NewSource(time.Now().UnixNano())), 0)
	id := ulid.MustNew(ulid.Timestamp(time.Now()), entropy).String()

	return &CloudEvent{
		SpecVersion:     "1.0",
		Type:            eventType,
		Source:          source,
		ID:              id,
		Subject:         subject,
		Time:            time.Now().UTC(),
		DataContentType: "application/json",
		Data:            rawData,
	}, nil
}

func (e *CloudEvent) Validate() error {
	if e.SpecVersion != "1.0" {
		return fmt.Errorf("invalid specversion: %q", e.SpecVersion)
	}
	if e.Type == "" {
		return fmt.Errorf("type required")
	}
	if e.Source == "" {
		return fmt.Errorf("source required")
	}
	if e.ID == "" {
		return fmt.Errorf("id required")
	}
	return nil
}

func (e *CloudEvent) ToKafkaHeaders() [][2]string {
	headers := [][2]string{
		{"ce_specversion", e.SpecVersion},
		{"ce_type", e.Type},
		{"ce_source", e.Source},
		{"ce_id", e.ID},
		{"content-type", e.DataContentType},
	}
	if e.Subject != "" {
		headers = append(headers, [2]string{"ce_subject", e.Subject})
	}
	if !e.Time.IsZero() {
		headers = append(headers, [2]string{"ce_time", e.Time.Format(time.RFC3339Nano)})
	}
	if e.TraceParent != "" {
		headers = append(headers, [2]string{"traceparent", e.TraceParent})
	}
	return headers
}
```

---

## 9. Networking Layer: Events Over the Wire

### Protocol Stack for Event Delivery

```
Event Delivery Protocol Stack
────────────────────────────────────────────────────────────────────────────────
LAYER STACK:

Application  │ CloudEvents / Avro / Protobuf / JSON
             │ Schema validation, type routing
─────────────┤
Protocol     │ Kafka wire protocol v2 (binary)
             │ AMQP 0-9-1 / 1.0
             │ NATS protocol (line-based text → binary)
             │ HTTP/2 (gRPC, SSE, WebSocket)
             │ MQTT 3.1 / 5.0 (IoT events)
─────────────┤
Transport    │ TLS 1.3 (mTLS for broker auth)
             │ QUIC (HTTP/3, lower latency reconnect)
─────────────┤
Transport    │ TCP (reliable, ordered)
             │ UDP (NATS core, best-effort)
─────────────┤
Network      │ IP (routing, BGP for multi-region)
             │ eBPF/XDP (fast path, DDoS filter)
─────────────┤
Datalink     │ Ethernet 25/100 GbE
             │ RDMA/RoCE (lossless, kernel bypass)
─────────────┤
Physical     │ NIC with RSS (Receive Side Scaling)
             │ Multiple RX queues → CPU affinity

TCP SOCKET TUNING for broker-class throughput:
─────────────────────────────────────────────
  # Increase TCP buffer sizes
  sysctl -w net.core.rmem_max=268435456          # 256MB max read buffer
  sysctl -w net.core.wmem_max=268435456          # 256MB max write buffer
  sysctl -w net.ipv4.tcp_rmem="4096 87380 268435456"
  sysctl -w net.ipv4.tcp_wmem="4096 65536 268435456"
  sysctl -w net.ipv4.tcp_congestion_control=bbr  # BBR: better for high-BDP links
  sysctl -w net.core.netdev_max_backlog=300000   # NIC → kernel queue depth
  sysctl -w net.ipv4.tcp_max_syn_backlog=262144  # SYN queue depth
  sysctl -w net.core.somaxconn=65535             # listen() backlog
  sysctl -w net.ipv4.tcp_tw_reuse=1              # reuse TIME_WAIT sockets

NIC RSS (Receive Side Scaling):
  ethtool -L eth0 combined 16  # use 16 queues (one per CPU core)
  # Kernel maps each queue to a CPU core via IRQ affinity
  # Flow hashing (IP+port) spreads connections across queues
  # No lock contention per packet on SMP systems
```

### RDMA / Kernel Bypass for Ultra-Low Latency

```
RDMA Event Path (InfiniBand / RoCE)
────────────────────────────────────────────────────────────────────────────────
Traditional TCP:
  App → kernel TCP stack → NIC driver → NIC → wire → NIC → kernel → App
  Latency: ~20-100μs
  CPU: significant (copy, checksum, syscall overhead)

RDMA (Remote DMA):
  App → RDMA lib (ibverbs) → NIC → wire → NIC → remote memory
  Latency: 1-5μs (sub-microsecond with SR-IOV + huge pages)
  CPU: near-zero (kernel-bypass, DMA directly to app buffer)

RDMA verbs:
  struct ibv_send_wr wr = {
    .opcode     = IBV_WR_SEND,          // or RDMA_WRITE, RDMA_READ
    .sg_list    = &sge,                 // scatter-gather list
    .num_sge    = 1,
    .send_flags = IBV_SEND_SIGNALED,
  };
  ibv_post_send(qp, &wr, &bad_wr);    // posts to Send Queue (SQ)
  // NIC processes SQ → DMA → puts completion in CQ
  struct ibv_wc wc;
  ibv_poll_cq(cq, 1, &wc);            // poll for completion (no syscall)

Use cases for EDA:
  Financial trading: order book updates, market data feeds
  HPC: MPI messages between compute nodes
  Storage: NVMe-oF (NVMe over Fabrics) — event log on remote NVMe
  Kafka optimization: RDMA-based replication between brokers
```

---

## 10. Security: Threat Model and Mitigations

### EDA Threat Model (STRIDE)

```
EDA Security Threat Model
────────────────────────────────────────────────────────────────────────────────

THREAT SURFACE MAP:
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ① Producer         ② Network      ③ Broker        ④ Consumer              │
│  ┌──────────┐       ┌──────────┐   ┌──────────┐    ┌──────────┐            │
│  │ app-svc  │──TLS─►│ internet │──►│  Kafka   │──►│  app-svc │            │
│  └──────────┘       │  /VPC    │   │  cluster │    └──────────┘            │
│                     └──────────┘   └──────────┘                            │
│  ⑤ Event Data (payload)            ⑥ Event Store    ⑦ Schema Registry      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

STRIDE PER COMPONENT:

① PRODUCER threats:
  S (Spoofing):      rogue service claims to be order-svc, injects fake events
  T (Tampering):     producer publishes malformed/malicious event payloads
  R (Repudiation):   no proof of which service produced which event
  I (Info Disclosure): event contains PII/secrets in plaintext
  D (DoS):           producer floods broker with events (rate abuse)
  E (Elevation):     producer writes to topics it shouldn't have access to

② NETWORK threats:
  S: MITM → intercept and modify events in transit
  I: plaintext events leaked (credentials in payload)
  D: volumetric DDoS against broker endpoints

③ BROKER threats:
  S: unauthorized broker node joins cluster (raft poisoning)
  T: disk-level tampering of partition log files
  R: no audit log of who consumed which message
  I: partition data readable by unauthorized consumers
  D: broker OOM, disk exhaustion, partition starvation
  E: CVE in broker → code execution on broker nodes

④ CONSUMER threats:
  S: malicious consumer pretends to be billing-svc to steal events
  I: events with PII delivered to wrong consumer
  D: consumer lag → OOM → cascading failure
  E: deserialization vulnerability in consumer (gadget chains)

⑤ EVENT DATA threats:
  I: PII (SSN, credit card) in event payload violates regulations
  T: event schema injection (field pollution, type confusion)
  E: payload contains executable code (if consumer eval()s it)

MITIGATIONS:
────────────────────────────────────────────────────────────────────────────────

① Producer identity:
  mTLS: producer presents cert signed by internal CA
  SPIFFE/SPIRE: cryptographic workload identity (X.509 SVID)
    → SPIRE agent on each node, SPIRE server as CA
    → cert rotated every 1h, no long-lived credentials
  Kafka SASL/OAUTHBEARER: producer gets JWT from identity provider
    → short-lived JWT (15 min), auto-refreshed
  Event signing: HMAC-SHA256 or EdDSA over event ID + timestamp + payload
    → consumer verifies signature before processing

② Network:
  TLS 1.3 everywhere (no TLS 1.2, no self-signed without pinning)
  mTLS between ALL internal services (zero trust)
  VPC private endpoints for managed brokers (no public internet)
  Network policy: only specific pods can reach broker ports (Kubernetes NetworkPolicy or Cilium)
  eBPF/XDP: rate-limit and filter at NIC driver level

③ Broker security (Kafka example):
  SSL/TLS for inter-broker communication
  SASL for authentication (SCRAM-SHA-512, OAUTHBEARER)
  ACLs per topic:
    billing-svc: READ billing.events WRITE billing.events
    order-svc: WRITE order.events (no READ)
    analytics: READ order.events (no WRITE)
  Encryption at rest: LUKS2 on broker disk (AES-256-XTS)
  Audit log: Confluent audit log connector / CloudTrail for MSK
  Quota: producer/consumer byte rate quotas per principal

④ Consumer authorization:
  Consumer group ID bound to service identity
  ACL: billing-svc-group can only consume from billing.events
  Consumer isolation: different services in different namespaces
  Read-committed isolation for transactional consumers

⑤ Event data:
  PII tokenization before event: store token in event, PII in vault
  Field-level encryption: encrypt specific fields (SSN, card number)
    → Key ID in event header → fetch DEK from KMS to decrypt
  Data minimization: events contain only what consumers need
  Schema validation at produce time (Schema Registry)
  Input sanitization: reject events exceeding size limits

SECURITY ARCHITECTURE:
────────────────────────────────────────────────────────────────────────────────
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  SPIRE Server                    Kafka Cluster (private subnet)             │
│  ┌────────────┐                  ┌──────────────────────────────────────┐   │
│  │ CA / SVID  │                  │  Broker 1  Broker 2  Broker 3       │   │
│  │ issuance   │                  │  [TLS]     [TLS]     [TLS]          │   │
│  └──────┬─────┘                  │  ACLs, Quotas, Audit                │   │
│         │ X.509 SVID             └───────────────────┬──────────────────┘   │
│         │                                            │ mTLS                 │
│  Pod: order-svc                   Pod: inventory-svc  │                     │
│  ┌────────────────────────────┐  ┌────────────────────▼────────────────┐   │
│  │ SPIRE agent                │  │ SPIRE agent                        │   │
│  │ cert: spiffe://cluster/    │  │ cert: spiffe://cluster/             │   │
│  │   ns/prod/svc/order-svc   │  │   ns/prod/svc/inventory-svc       │   │
│  │                            │  │                                    │   │
│  │ Produce: order.events ✓   │  │ Consume: order.events ✓            │   │
│  │ Consume: order.events ✗   │  │ Produce: order.events ✗             │   │
│  └────────────────────────────┘  └────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### Rust Implementation: Event Signing and Verification

```rust
// src/event_security.rs — Event signing with Ed25519 and HMAC verification
use std::time::{SystemTime, UNIX_EPOCH};
use ed25519_dalek::{Signer, SigningKey, Verifier, VerifyingKey, Signature};
use hmac::{Hmac, Mac};
use sha2::Sha256;
use serde::{Deserialize, Serialize};
use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine as _};

type HmacSha256 = Hmac<Sha256>;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SignedEvent {
    pub id: String,
    pub event_type: String,
    pub source: String,
    pub timestamp_ms: u64,
    pub payload: Vec<u8>,
    // Signature over canonical bytes (id + type + source + ts + payload)
    pub signature: String,  // base64url-encoded Ed25519 signature
    pub key_id: String,     // which key was used (for rotation)
}

pub struct EventSigner {
    signing_key: SigningKey,
    key_id: String,
}

impl EventSigner {
    pub fn new(signing_key: SigningKey, key_id: impl Into<String>) -> Self {
        Self { signing_key, key_id: key_id.into() }
    }

    /// Compute canonical bytes that the signature covers.
    /// Canonical form prevents ambiguity / length extension attacks.
    fn canonical_bytes(event: &SignedEvent) -> Vec<u8> {
        let mut buf = Vec::with_capacity(256);
        // Length-prefixed fields to prevent injection
        let fields = [
            event.id.as_bytes(),
            event.event_type.as_bytes(),
            event.source.as_bytes(),
        ];
        for field in &fields {
            let len = (field.len() as u32).to_be_bytes();
            buf.extend_from_slice(&len);
            buf.extend_from_slice(field);
        }
        buf.extend_from_slice(&event.timestamp_ms.to_be_bytes());
        buf.extend_from_slice(&event.payload);
        buf
    }

    pub fn sign(
        &self,
        id: String,
        event_type: String,
        source: String,
        payload: Vec<u8>,
    ) -> Result<SignedEvent, Box<dyn std::error::Error>> {
        let timestamp_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_millis() as u64;

        let mut event = SignedEvent {
            id,
            event_type,
            source,
            timestamp_ms,
            payload,
            signature: String::new(),
            key_id: self.key_id.clone(),
        };

        let canonical = Self::canonical_bytes(&event);
        let sig: Signature = self.signing_key.sign(&canonical);
        event.signature = URL_SAFE_NO_PAD.encode(sig.to_bytes());
        Ok(event)
    }
}

pub struct EventVerifier {
    verifying_key: VerifyingKey,
    max_age_ms: u64, // reject events older than this (replay protection)
}

impl EventVerifier {
    pub fn new(verifying_key: VerifyingKey, max_age_ms: u64) -> Self {
        Self { verifying_key, max_age_ms }
    }

    pub fn verify(&self, event: &SignedEvent) -> Result<(), VerifyError> {
        // 1. Replay protection: check timestamp freshness
        let now_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        if now_ms.saturating_sub(event.timestamp_ms) > self.max_age_ms {
            return Err(VerifyError::Expired {
                age_ms: now_ms - event.timestamp_ms,
                max_ms: self.max_age_ms,
            });
        }

        // 2. Decode signature
        let sig_bytes = URL_SAFE_NO_PAD
            .decode(&event.signature)
            .map_err(|_| VerifyError::InvalidSignatureEncoding)?;

        let sig_arr: [u8; 64] = sig_bytes
            .try_into()
            .map_err(|_| VerifyError::InvalidSignatureLength)?;

        let signature = Signature::from_bytes(&sig_arr);

        // 3. Verify Ed25519 signature over canonical bytes
        let canonical = EventSigner::canonical_bytes(event);
        self.verifying_key
            .verify(&canonical, &signature)
            .map_err(|_| VerifyError::SignatureMismatch)?;

        Ok(())
    }
}

/// HMAC-based integrity check (for symmetric key scenarios)
pub fn compute_hmac(secret: &[u8], data: &[u8]) -> Vec<u8> {
    let mut mac = HmacSha256::new_from_slice(secret)
        .expect("HMAC accepts any key size");
    mac.update(data);
    mac.finalize().into_bytes().to_vec()
}

pub fn verify_hmac(secret: &[u8], data: &[u8], expected: &[u8]) -> bool {
    let mut mac = HmacSha256::new_from_slice(secret).unwrap();
    mac.update(data);
    // Constant-time comparison (prevents timing attacks)
    mac.verify_slice(expected).is_ok()
}

#[derive(Debug, thiserror::Error)]
pub enum VerifyError {
    #[error("event expired: age={age_ms}ms, max={max_ms}ms")]
    Expired { age_ms: u64, max_ms: u64 },
    #[error("invalid signature encoding")]
    InvalidSignatureEncoding,
    #[error("invalid signature length")]
    InvalidSignatureLength,
    #[error("signature mismatch — event tampered or wrong key")]
    SignatureMismatch,
}

/// Field-level encryption for PII in events
pub struct FieldEncryptor {
    key: [u8; 32], // AES-256 key
    // In production: fetch from KMS by key_id; cache with TTL
}

impl FieldEncryptor {
    pub fn new(key: [u8; 32]) -> Self {
        Self { key }
    }

    // AES-256-GCM encrypt a field value
    // Returns: base64(nonce || ciphertext || tag)
    pub fn encrypt_field(&self, plaintext: &[u8]) -> Result<String, Box<dyn std::error::Error>> {
        use aes_gcm::{Aes256Gcm, KeyInit, aead::{Aead, AeadCore, OsRng}};

        let cipher = Aes256Gcm::new((&self.key).into());
        let nonce = Aes256Gcm::generate_nonce(&mut OsRng);
        let ciphertext = cipher.encrypt(&nonce, plaintext)
            .map_err(|e| format!("encrypt: {e}"))?;

        let mut combined = nonce.to_vec();
        combined.extend_from_slice(&ciphertext);
        Ok(URL_SAFE_NO_PAD.encode(&combined))
    }

    pub fn decrypt_field(&self, encoded: &str) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
        use aes_gcm::{Aes256Gcm, KeyInit, aead::Aead, Nonce};

        let combined = URL_SAFE_NO_PAD.decode(encoded)?;
        if combined.len() < 12 {
            return Err("ciphertext too short".into());
        }

        let (nonce_bytes, ciphertext) = combined.split_at(12);
        let nonce = Nonce::from_slice(nonce_bytes);
        let cipher = Aes256Gcm::new((&self.key).into());

        cipher.decrypt(nonce, ciphertext)
            .map_err(|_| "decryption failed (tampered or wrong key)".into())
    }
}

/*
 * Cargo.toml dependencies:
 * ed25519-dalek = { version = "2", features = ["rand_core"] }
 * hmac = "0.12"
 * sha2 = "0.10"
 * aes-gcm = "0.10"
 * base64 = "0.22"
 * serde = { version = "1", features = ["derive"] }
 * thiserror = "1"
 *
 * Build: cargo build --release
 * Test:  cargo test event_security
 */
```

#### C Implementation: Event Ring Buffer (Lock-Free SPSC)

```c
/* ringbuf.c — Lock-free Single-Producer Single-Consumer ring buffer for events
 * Used as the kernel-to-userspace or thread-to-thread event channel.
 * Based on the same design as Linux kernel kfifo and DPDK rte_ring (SPSC variant).
 */
#include <stdint.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

/* Must be power of 2 for masking trick */
#define RING_SIZE  (1u << 16)  /* 65536 slots */
#define RING_MASK  (RING_SIZE - 1)

typedef struct {
    char    type[32];
    uint64_t id;
    uint64_t timestamp_ns;
    uint8_t  data[96];
    uint32_t data_len;
} event_slot_t;  /* 144 bytes — fits in 2 cache lines if aligned */

typedef struct {
    /* Read and write cursors — each on its own cache line to prevent false sharing */
    _Alignas(64) atomic_uint_fast64_t head;  /* producer writes here */
    _Alignas(64) atomic_uint_fast64_t tail;  /* consumer reads here */
    _Alignas(64) event_slot_t slots[RING_SIZE];
} spsc_ring_t;

_Static_assert((RING_SIZE & (RING_SIZE - 1)) == 0, "Ring size must be power of 2");

static inline int ring_push(spsc_ring_t *r, const event_slot_t *e) {
    uint64_t head = atomic_load_explicit(&r->head, memory_order_relaxed);
    uint64_t tail = atomic_load_explicit(&r->tail, memory_order_acquire);

    if (head - tail >= RING_SIZE) {
        return -1; /* ring full */
    }

    memcpy(&r->slots[head & RING_MASK], e, sizeof(*e));

    /* Release fence: ensure slot write is visible before head bump */
    atomic_store_explicit(&r->head, head + 1, memory_order_release);
    return 0;
}

static inline int ring_pop(spsc_ring_t *r, event_slot_t *e) {
    uint64_t tail = atomic_load_explicit(&r->tail, memory_order_relaxed);
    uint64_t head = atomic_load_explicit(&r->head, memory_order_acquire);

    if (head == tail) {
        return -1; /* ring empty */
    }

    memcpy(e, &r->slots[tail & RING_MASK], sizeof(*e));

    /* Release fence: ensure data copy before advancing tail */
    atomic_store_explicit(&r->tail, tail + 1, memory_order_release);
    return 0;
}

static inline size_t ring_size(spsc_ring_t *r) {
    uint64_t head = atomic_load_explicit(&r->head, memory_order_acquire);
    uint64_t tail = atomic_load_explicit(&r->tail, memory_order_acquire);
    return (size_t)(head - tail);
}

/* ─── Test ─────────────────────────────────────────────────────────────────── */
#include <pthread.h>
#include <time.h>

#define PRODUCE_COUNT 1000000

static spsc_ring_t g_ring = {0};
static volatile int g_done = 0;

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

static void *producer(void *arg) {
    (void)arg;
    event_slot_t e = { .type = "order.placed", .data_len = 64 };
    uint64_t t0 = now_ns();

    for (int i = 0; i < PRODUCE_COUNT; i++) {
        e.id           = i;
        e.timestamp_ns = now_ns();
        while (ring_push(&g_ring, &e) < 0) {
            /* Spin — in production: use pause / sched_yield / futex */
            __asm__ __volatile__("pause" ::: "memory");
        }
    }

    uint64_t elapsed = now_ns() - t0;
    printf("[producer] %d events in %.2fms (%.1f Mev/s)\n",
           PRODUCE_COUNT, elapsed / 1e6,
           PRODUCE_COUNT / (elapsed / 1e9) / 1e6);
    g_done = 1;
    return NULL;
}

static void *consumer(void *arg) {
    (void)arg;
    event_slot_t e;
    int count = 0;

    while (count < PRODUCE_COUNT) {
        if (ring_pop(&g_ring, &e) == 0) {
            count++;
            /* Process event — in production: dispatch to handler */
        } else {
            __asm__ __volatile__("pause" ::: "memory");
        }
    }
    printf("[consumer] processed %d events\n", count);
    return NULL;
}

int main(void) {
    pthread_t pt, ct;
    pthread_create(&ct, NULL, consumer, NULL);
    pthread_create(&pt, NULL, producer, NULL);
    pthread_join(pt, NULL);
    pthread_join(ct, NULL);
    return 0;
}

/*
 * Build: gcc -O3 -march=native -pthread -o ringbuf ringbuf.c
 * Expected: ~200-400 Mev/s on modern hardware (sub-10ns per event)
 *
 * For MPMC (Multi-Producer Multi-Consumer): use CAS-based head/tail
 * or DPDK rte_ring which handles MPMC with two-phase commit pattern.
 */
```

---

## 11. Observability and Distributed Tracing

### Tracing Events Across Services

```
Distributed Tracing in EDA
────────────────────────────────────────────────────────────────────────────────
W3C Trace Context in Events:
  traceparent: 00-{trace-id 16B hex}-{parent-span-id 8B hex}-{flags}
  tracestate:  vendor-specific key=value pairs

  When producing an event:
    1. Get current span from OpenTelemetry context
    2. Inject traceparent/tracestate into event headers
    3. Create child span "kafka.produce" → end it

  When consuming an event:
    1. Extract traceparent/tracestate from event headers
    2. Create span with parent = extracted span → "kafka.consume"
    3. Process → end span

Trace visualization:
  HTTP POST /orders (trace-id: abc123)
  ├── [order-svc] handle request ──────────────────── 15ms
  │   └── [kafka] produce order.placed ──────────────  2ms
  │       ├── [inventory-svc] consume + reserve ────  8ms
  │       │   └── [kafka] produce stock.reserved ──── 1ms
  │       └── [billing-svc] consume + charge ───────  45ms
  │           └── [kafka] produce payment.completed ─  1ms
  └── total end-to-end: 72ms

Metrics for EDA:
  Consumer lag:     kafka_consumer_group_lag{group, topic, partition}
  Produce rate:     kafka_producer_record_send_rate
  Consume rate:     kafka_consumer_fetch_rate
  Error rate:       kafka_consumer_fetch_error_rate
  Event latency:    histogram of time from produce to consume
  DLQ depth:        custom metric — events in DLQ topic
  Partition skew:   max(partition_lag) / avg(partition_lag)

OpenTelemetry instrumentation:
  - Auto-instrument: kafka-go, franz-go have OTEL contrib packages
  - Manual: create span at each produce/consume boundary
  - Propagate: inject/extract W3C Trace Context in event headers
  - Export: OTLP → Jaeger, Tempo, Datadog, Honeycomb

SLOs for event systems:
  Consumer lag SLO:    p99 consumer lag < 5 seconds
  End-to-end SLO:      p99 event processing latency < 500ms
  DLQ rate SLO:        < 0.01% events to DLQ
  Availability SLO:    99.99% uptime for brokers
```

---

## 12. Implementations: C, Go, Rust

### Rust: High-Performance Event Processor

```rust
// src/main.rs — Async event processor using tokio + kafka-rs (rdkafka)
use std::time::Duration;
use rdkafka::consumer::{CommitMode, Consumer, StreamConsumer};
use rdkafka::config::ClientConfig;
use rdkafka::message::{Message, Headers};
use rdkafka::util::get_rdkafka_version;
use tokio::signal;
use tracing::{info, error, warn, instrument};

mod event;
mod processor;
mod metrics;

use event::CloudEvent;
use processor::EventProcessor;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("info,event_processor=debug")
        .json()
        .init();

    let (version_n, version_s) = get_rdkafka_version();
    info!(rdkafka_version = version_s, version_n, "Starting event processor");

    let consumer: StreamConsumer = ClientConfig::new()
        .set("group.id", "inventory-service-group")
        .set("bootstrap.servers", "kafka-1:9093,kafka-2:9093,kafka-3:9093")
        .set("security.protocol", "ssl")
        .set("ssl.ca.location", "/etc/kafka/certs/ca.crt")
        .set("ssl.certificate.location", "/etc/kafka/certs/client.crt")
        .set("ssl.key.location", "/etc/kafka/certs/client.key")
        .set("enable.auto.commit", "false")       // Manual commit
        .set("auto.offset.reset", "earliest")
        .set("isolation.level", "read_committed") // Exactly-once
        .set("fetch.min.bytes", "1")
        .set("fetch.max.wait.ms", "500")
        .set("max.poll.interval.ms", "300000")    // 5 min max processing time
        .set("session.timeout.ms", "45000")
        .set("heartbeat.interval.ms", "3000")
        .set("partition.assignment.strategy", "cooperative-sticky")
        .create()?;

    consumer.subscribe(&["order.placed"])?;

    let processor = EventProcessor::new();
    let metrics   = metrics::Registry::new();

    info!("Consumer started, waiting for events...");

    // Graceful shutdown signal
    let shutdown = tokio::spawn(async move {
        signal::ctrl_c().await.expect("ctrl-c handler");
        info!("Shutdown signal received");
    });

    tokio::select! {
        _ = process_loop(&consumer, &processor, &metrics) => {},
        _ = shutdown => {
            info!("Shutting down consumer...");
        }
    }

    Ok(())
}

#[instrument(skip(consumer, processor, metrics))]
async fn process_loop(
    consumer: &StreamConsumer,
    processor: &EventProcessor,
    metrics: &metrics::Registry,
) -> anyhow::Result<()> {
    use rdkafka::consumer::Consumer as _;

    loop {
        match consumer.recv().await {
            Ok(msg) => {
                let _timer = metrics.processing_duration.start_timer();

                // Extract CloudEvent from Kafka message
                let event = match extract_event(&msg) {
                    Ok(e) => e,
                    Err(err) => {
                        error!(?err, "Failed to parse event, sending to DLQ");
                        metrics.parse_errors.inc();
                        // Route to DLQ — implement dlq_producer separately
                        consumer.commit_message(&msg, CommitMode::Async)?;
                        continue;
                    }
                };

                let span = create_span_from_event(&event);
                let _guard = span.enter();

                // Process with retry logic
                let result = with_retries(3, Duration::from_millis(100), || {
                    processor.process(&event)
                }).await;

                match result {
                    Ok(_) => {
                        metrics.events_processed.inc();
                        consumer.commit_message(&msg, CommitMode::Async)?;
                    }
                    Err(err) => {
                        error!(?err, event_id = %event.id, "Processing failed after retries");
                        metrics.events_failed.inc();
                        // Route to DLQ with error context
                        consumer.commit_message(&msg, CommitMode::Async)?;
                    }
                }
            }
            Err(err) => {
                warn!(?err, "Kafka consumer error");
                tokio::time::sleep(Duration::from_secs(1)).await;
            }
        }
    }
}

fn extract_event(msg: &rdkafka::message::BorrowedMessage<'_>) -> anyhow::Result<CloudEvent> {
    use anyhow::Context;

    let payload = msg.payload()
        .context("empty message payload")?;

    let mut event: CloudEvent = serde_json::from_slice(payload)
        .context("JSON parse failed")?;

    // Extract trace context from headers
    if let Some(headers) = msg.headers() {
        for i in 0..headers.count() {
            let header = headers.get(i);
            if header.key == "traceparent" {
                event.trace_parent = String::from_utf8_lossy(
                    header.value.unwrap_or(b"")
                ).to_string();
            }
        }
    }

    event.validate()?;
    Ok(event)
}

async fn with_retries<F, Fut, T, E>(
    max_retries: u32,
    base_delay: Duration,
    mut f: F,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: std::future::Future<Output = Result<T, E>>,
    E: std::fmt::Debug,
{
    let mut attempts = 0;
    loop {
        match f().await {
            Ok(v) => return Ok(v),
            Err(err) if attempts < max_retries => {
                attempts += 1;
                let delay = base_delay * 2u32.pow(attempts - 1);
                warn!(?err, attempt = attempts, ?delay, "Retrying");
                tokio::time::sleep(delay).await;
            }
            Err(err) => return Err(err),
        }
    }
}

fn create_span_from_event(event: &CloudEvent) -> tracing::Span {
    tracing::info_span!(
        "process_event",
        event.id = %event.id,
        event.type = %event.event_type,
        event.source = %event.source,
        traceparent = %event.trace_parent,
    )
}

/*
 * Cargo.toml:
 * [dependencies]
 * rdkafka = { version = "0.36", features = ["cmake-build", "ssl"] }
 * tokio = { version = "1", features = ["full"] }
 * serde = { version = "1", features = ["derive"] }
 * serde_json = "1"
 * anyhow = "1"
 * tracing = "0.1"
 * tracing-subscriber = { version = "0.3", features = ["json", "env-filter"] }
 *
 * Build: cargo build --release
 * Run:   RUST_LOG=info ./target/release/event-processor
 */
```

---

## 13. Testing, Fuzzing, and Benchmarking

### Testing Strategy for Event-Driven Systems

```
EDA TEST PYRAMID
────────────────────────────────────────────────────────────────────────────────
                    ┌──────────────────────┐
                    │  Contract Tests      │  ← Pact / OpenAPI
                    │  (schema compat)     │
                    └──────────────────────┘
                ┌──────────────────────────────────┐
                │  Integration Tests               │
                │  (Kafka testcontainers,          │
                │   in-memory broker)              │
                └──────────────────────────────────┘
            ┌──────────────────────────────────────────────┐
            │  Unit Tests                                  │
            │  (handler, aggregate, serialization)         │
            └──────────────────────────────────────────────┘

Unit tests:
  - Event handler: given event → assert state change
  - Aggregate: given commands → assert events raised
  - Serialization round-trip: event → bytes → event
  - Idempotency: handle same event twice → same result
  - Retry logic: mock broker failure → assert retry behavior
  - DLQ routing: mock repeated failure → assert DLQ write

Integration tests (testcontainers-go / testcontainers-rust):
  - Start real Kafka/NATS in Docker
  - Produce events
  - Assert consumer processed correctly
  - Assert offset committed
  - Simulate broker failure → assert reconnect + no message loss

Contract tests (Pact):
  - Producer publishes to Pact broker: "order.placed has schema X"
  - Consumer verifies: "I can parse schema X"
  - CI: fail if producer changes schema in breaking way

Chaos testing:
  - Kill broker leader mid-produce → assert at-least-once
  - Kill consumer mid-batch → assert no message loss
  - Introduce 1s network partition → assert reconnect
  - Fill disk on broker → assert back-pressure behavior
  - Corrupt message in DLQ → assert DLQ consumer handles it

Tools:
  Toxiproxy:  inject network failures, latency, partition
  Chaos Mesh: Kubernetes-native chaos injection
  Pumba:      Docker chaos (kill, delay, rate limit containers)
```

#### Go: Integration Test with testcontainers

```go
// kafka_integration_test.go
package kafka_test

import (
	"context"
	"testing"
	"time"

	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/modules/kafka"
	"github.com/twmb/franz-go/pkg/kgo"
)

func TestEventRoundTrip(t *testing.T) {
	ctx := context.Background()

	// Start Kafka container
	kc, err := kafka.Run(ctx, "confluentinc/confluent-local:7.5.0")
	if err != nil {
		t.Fatalf("start kafka: %v", err)
	}
	defer testcontainers.TerminateContainer(kc)

	brokers, err := kc.Brokers(ctx)
	if err != nil {
		t.Fatalf("brokers: %v", err)
	}

	topic := "test.order.placed"

	// Producer
	producer, _ := kgo.NewClient(
		kgo.SeedBrokers(brokers...),
		kgo.AllowAutoTopicCreation(),
	)
	defer producer.Close()

	// Consumer
	consumer, _ := kgo.NewClient(
		kgo.SeedBrokers(brokers...),
		kgo.ConsumeTopics(topic),
		kgo.ConsumerGroup("test-group"),
	)
	defer consumer.Close()

	// Produce event
	payload := []byte(`{"id":"test-1","type":"order.placed","data":{"orderId":"ORD-1"}}`)
	if err := producer.ProduceSync(ctx, &kgo.Record{
		Topic: topic,
		Key:   []byte("user-123"),
		Value: payload,
	}).FirstErr(); err != nil {
		t.Fatalf("produce: %v", err)
	}

	// Consume with timeout
	ctxTimeout, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	fetches := consumer.PollFetches(ctxTimeout)
	if fetches.IsClientClosed() {
		t.Fatal("client closed")
	}

	var received []byte
	fetches.EachRecord(func(r *kgo.Record) {
		received = r.Value
	})

	if string(received) != string(payload) {
		t.Errorf("expected %s, got %s", payload, received)
	}
}
```

### Fuzzing Event Parsers

```go
// fuzz/parse_event_test.go — Go fuzzing for event deserialization
package fuzz

import (
	"testing"
	"encoding/json"
)

// FuzzParseEvent exercises the event parser with arbitrary input.
// Run: go test -fuzz=FuzzParseEvent -fuzztime=60s ./fuzz/
func FuzzParseEvent(f *testing.F) {
	// Seed corpus: valid and edge-case inputs
	f.Add([]byte(`{"id":"1","type":"t","source":"s","specversion":"1.0"}`))
	f.Add([]byte(`{}`))
	f.Add([]byte(`null`))
	f.Add([]byte(`{"id":"` + string(make([]byte, 1<<20)) + `"}`)) // 1MB id

	f.Fuzz(func(t *testing.T, data []byte) {
		var event map[string]any
		if err := json.Unmarshal(data, &event); err != nil {
			return // invalid JSON is OK — we just skip
		}
		// At this point, valid JSON parsed. Apply business validation.
		// The fuzzer looks for panics, infinite loops, or unexpected behaviors.
		validateEvent(event)  // must not panic
	})
}

func validateEvent(e map[string]any) {
	// Recover from panics (fuzz target must not panic)
	defer func() { recover() }()
	_ = e["id"]
	_ = e["type"]
	_ = e["specversion"]
}
```

```rust
// fuzz/fuzz_targets/parse_event.rs — Rust cargo-fuzz target
#![no_main]
use libfuzzer_sys::fuzz_target;
use my_crate::event::CloudEvent;

fuzz_target!(|data: &[u8]| {
    // Parse arbitrary bytes as a CloudEvent
    if let Ok(s) = std::str::from_utf8(data) {
        if let Ok(event) = serde_json::from_str::<CloudEvent>(s) {
            // Validate — must not panic
            let _ = event.validate();
            // Sign — must not panic with valid or invalid input
            // let _ = signer.sign(event); // if you have a signer
        }
    }
});
// Run: cargo +nightly fuzz run parse_event -- -max_len=100000
```

### Benchmarking

```go
// bench/producer_bench_test.go
package bench

import (
	"testing"
	"encoding/json"
)

func BenchmarkEventMarshal(b *testing.B) {
	event := map[string]any{
		"id": "01HNW8R7ZMQZ9RD3K2XB1Y6PQ4",
		"type": "com.example.order.placed",
		"source": "/services/order-svc",
		"specversion": "1.0",
		"data": map[string]any{
			"orderId": "ORD-123456",
			"userId": "user-789",
			"totalCents": 4999,
		},
	}

	b.ReportAllocs()
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_, err := json.Marshal(event)
		if err != nil {
			b.Fatal(err)
		}
	}
}
// Run: go test -bench=. -benchmem -count=5 ./bench/
// Compare: benchstat old.txt new.txt
```

```
Benchmark targets for production event systems:
  Serialization:    > 1M events/s per core (JSON), > 5M/s (Protobuf/Avro)
  Ring buffer:      > 100M events/s (SPSC, same core)
  Kafka produce:    > 500K events/s at acks=1 (batched, compressed)
  Kafka consume:    > 1M events/s with parallel processing
  End-to-end:       < 5ms p99 producer→consumer at 100K events/s

Tools:
  perf stat -e cache-misses,cache-references,instructions ./benchmark
  perf record -g ./benchmark && perf report  # flame graphs
  valgrind --tool=cachegrind ./benchmark     # cache simulation
  heaptrack ./benchmark                      # memory allocation profiling
  cargo flamegraph --bin event-processor     # Rust flame graph
```

---

## 14. Production Rollout and Rollback

### Schema Migration Rollout

```
ROLLOUT STRATEGY: Adding New Event Field
────────────────────────────────────────────────────────────────────────────────
Phase 1: Deploy consumer first (backward compatible)
  - Consumer updated to handle BOTH old and new schema
  - Old: ignore missing new field (use default)
  - New: use new field
  Status: old producer → new consumer ✓ (no breaking change)

Phase 2: Deploy producer
  - Producer now includes new field in all events
  Status: new producer → new consumer ✓

Phase 3: (Optional) Remove compatibility code
  - After all old events have aged out of retention
  - Remove "handle missing field" fallback

ROLLBACK:
  Phase 2 rollback: revert producer → back to Phase 1
  No data migration needed (events are immutable; old events in log)
  Consumer handles both: rollback is safe

BREAKING CHANGE ROLLOUT (type rename):
  1. Add new event type: "order.placed.v2"
  2. Producer emits BOTH v1 and v2 simultaneously
  3. Deploy consumers to handle v2
  4. Stop emitting v1 (after all consumers confirmed on v2)
  5. Remove v1 code
  Timeline: 2-4 weeks with feature flags
```

### Kafka Topic Operations

```bash
# Create topic with replication and compaction
kafka-topics.sh --bootstrap-server kafka:9092 \
  --create \
  --topic order.events \
  --partitions 24 \
  --replication-factor 3 \
  --config retention.ms=604800000 \   # 7 days
  --config min.insync.replicas=2 \
  --config compression.type=lz4 \
  --config cleanup.policy=delete

# Increase partitions (non-destructive — only adds, never removes)
kafka-topics.sh --bootstrap-server kafka:9092 \
  --alter --topic order.events --partitions 48
# WARNING: adding partitions changes partition key distribution
# Existing keys may land on different partitions for new events

# Reset consumer group offset (for replay)
kafka-consumer-groups.sh --bootstrap-server kafka:9092 \
  --group inventory-group \
  --topic order.events \
  --reset-offsets --to-earliest --execute

# Reset to specific timestamp
kafka-consumer-groups.sh --bootstrap-server kafka:9092 \
  --group analytics-group \
  --topic order.events \
  --reset-offsets --to-datetime 2024-01-15T00:00:00.000 --execute

# Monitor consumer lag
kafka-consumer-groups.sh --bootstrap-server kafka:9092 \
  --describe --group inventory-group
# Output:
# GROUP            TOPIC         PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
# inventory-group  order.events  0          18374           18400           26
# inventory-group  order.events  1          9200            9200            0

# Emergency: pause a consumer group (set offsets ahead to skip bad events)
# DO NOT USE LIGHTLY — this loses events
kafka-consumer-groups.sh ... --reset-offsets --by-duration PT1H --execute
```

### Rollback Plan

```
INCIDENT RESPONSE: Bad Consumer Deployed
────────────────────────────────────────────────────────────────────────────────
T+0:  Bad consumer deployed → starts corrupting DB / sending wrong emails
T+5:  Alert fires: error rate > 1%, DLQ depth growing
T+10: Rollback consumer deployment (kubectl rollout undo)
T+15: Assess damage:
      - Events processed by bad consumer: corrupted state
      - Events NOT yet processed: safe (still in Kafka)
      - DLQ events: need reprocess after fix

T+20: Repair strategy:
      Option A: Replay events from before bad deploy
        kafka-consumer-groups.sh --reset-offsets --to-datetime <deploy-time>
        → Consumer reprocesses from known-good point
        → Must handle idempotency (events processed twice)

      Option B: Apply compensating events
        Emit "OrderCorrected" events to undo bad actions
        → Cleaner audit trail, no replay

T+30: Validate: monitor error rate, DLQ depth, DB consistency checks
T+60: Post-mortem: add integration test catching this scenario

KAFKA LEADER ELECTION FAILURE:
  Symptom: Produce errors, consumer lag growing
  Check: kafka-topics.sh --describe → shows UR (Under-Replicated)
  Fix:    kafka-leader-election.sh --all-topic-partitions --election-type preferred
  If ISR empty: unclean.leader.election.enable=true (LAST RESORT, loses data)
```

---

## 15. Next 3 Steps

```
NEXT 3 STEPS FOR MASTERY
────────────────────────────────────────────────────────────────────────────────
① Build a minimal event store from scratch (3-5 days)
  - Implement append-only log with mmap'd file
  - Add CRC32 integrity per record
  - Implement binary search index (offset → file position)
  - Add snapshot support (marshal aggregate state to file)
  - Test with chaos: kill process mid-write, verify recovery
  - Target: 500K writes/s on NVMe

  Commands:
    git clone https://github.com/EventStore/EventStore  # study internals
    cargo new --lib event-store && cargo add crc32fast memmap2 serde_json
    # Implement: src/log.rs, src/index.rs, src/snapshot.rs

② Implement end-to-end exactly-once EDA with Kafka transactions (1 week)
  - Order-svc: produce OrderPlaced with transactional.id
  - Inventory-svc: consume OrderPlaced → reserve stock → produce StockReserved
    (read-process-write in single Kafka transaction)
  - Payment-svc: consume StockReserved → charge → produce PaymentCompleted
  - Inject failures at each step, verify no duplicates in final state
  - Measure: end-to-end latency p50/p99/p999

  Commands:
    docker compose up -d  # kafka cluster (3 brokers, zookeeper or KRaft)
    go run cmd/order-svc/main.go &
    go run cmd/inventory-svc/main.go &
    go run cmd/payment-svc/main.go &
    # Chaos: docker stop kafka-1 during produce → verify recovery

③ Deploy SPIFFE/SPIRE + mTLS for event bus security (3-5 days)
  - Install SPIRE server and agents (K8s or bare-metal)
  - Configure workload attestors (K8s pod labels → SPIFFE ID)
  - Configure Kafka to require mTLS (ssl.client.auth=required)
  - Map SPIFFE SVIDs to Kafka ACLs (CN extraction)
  - Implement event signing in producer (Ed25519)
  - Implement signature verification in consumer
  - Measure overhead: < 5% latency impact expected

  Commands:
    kubectl apply -f https://spiffe.io/downloads/spire-k8s.yaml
    kubectl exec -n spire spire-server-0 -- \
      spire-server entry create \
        -spiffeID spiffe://example.org/ns/prod/svc/order-svc \
        -parentID spiffe://example.org/k8s-workload-registrar/cluster \
        -selector k8s:ns:prod -selector k8s:sa:order-svc
    # Verify: spire-agent api fetch x509
```

---

## 16. References

```
FOUNDATIONAL PAPERS AND SPECS:
  Kafka: "Kafka: a Distributed Messaging System for Log Processing"
         Jay Kreps, Neha Narkhede, Jun Rao — LinkedIn 2011
  Log:   "The Log: What every software engineer should know about real-time
          data's unifying abstraction" — Jay Kreps 2013
  Saga:  "SAGAS" — Hector Garcia-Molina, Kenneth Salem 1987 (Princeton)
  CQRS:  Greg Young — CQRS Documents (2010)
  ES:    "Event Sourcing" — Martin Fowler (martinfowler.com)

KERNEL / SYSTEMS:
  epoll(7) man page — Linux Programmer's Manual
  io_uring: "Efficient IO with io_uring" — Jens Axboe (kernel.dk/io_uring.pdf)
  eBPF: "A thorough introduction to eBPF" — Matt Fleming (LWN 2017)
  DPDK: "Data Plane Development Kit" — dpdk.org
  RDMA: "RDMA over Converged Ethernet" — Mellanox/NVIDIA

STANDARDS:
  CloudEvents 1.0: https://cloudevents.io / https://github.com/cloudevents/spec
  W3C Trace Context: https://www.w3.org/TR/trace-context/
  SPIFFE: https://spiffe.io/docs/latest/spiffe-about/overview/
  OpenTelemetry: https://opentelemetry.io/docs/

CLOUD:
  Apache Kafka Docs: https://kafka.apache.org/documentation/
  NATS Docs: https://docs.nats.io/
  AWS Kinesis Dev Guide: https://docs.aws.amazon.com/kinesis/
  GCP Pub/Sub: https://cloud.google.com/pubsub/docs
  Azure Event Hubs: https://learn.microsoft.com/en-us/azure/event-hubs/

CNCF LANDSCAPE:
  Knative Eventing: https://knative.dev/docs/eventing/
  KEDA (event-driven autoscaling): https://keda.sh/
  Dapr (distributed app runtime): https://dapr.io/
  Strimzi (Kafka on K8s): https://strimzi.io/

BOOKS:
  "Designing Event-Driven Systems" — Ben Stopford (Confluent, free PDF)
  "Building Event-Driven Microservices" — Adam Bellemare (O'Reilly)
  "Kafka: The Definitive Guide" — Shapira, Palino, Sivaram, Petty (O'Reilly)
  "Database Internals" — Alex Petrov (O'Reilly) — storage engine chapter
  "Systems Performance" — Brendan Gregg (Addison-Wesley) — Linux I/O chapter
```

Now let me write this comprehensive guide. This will be a large, production-grade document.**~3,900 lines / 163KB** — here's what the guide covers end-to-end:

---

**Structure of the guide:**

**Kernel layer** — The full Linux I/O event path from NIC DMA → NAPI softirq → sk_buff → socket buffer → epoll/io_uring, with annotated ASCII of every data structure. `epoll` edge-vs-level triggered mechanics with the exact drain loop. `io_uring` SQ/CQ ring anatomy, SQPOLL zero-syscall mode, and fixed buffer registration. `eventfd`/`timerfd`/`signalfd` as unified fd-based notification. `kqueue` vs `epoll` comparison table. eBPF event capture with XDP/TC hook positioning in the packet path.

**Event taxonomy** — ULID vs UUID v4/v7, canonical envelope fields (CloudEvents 1.0 spec), schema versioning strategies (type versioning vs Schema Registry), and why wall clocks break event ordering.

**Core patterns** — Pub/Sub with consumer group semantics and fan-out topology. Event Sourcing with aggregate mechanics, optimistic concurrency (`expectedVersion`), and snapshot optimization. CQRS with read/write model separation. Saga (choreography vs orchestration) with full Go implementation including compensation. Outbox with Debezium CDC WAL path. DLQ with retry backoff and exponential strategy. Event replay with offset reset commands.

**Delivery semantics** — At-most/at-least/exactly-once with Kafka transaction internals (transactional.id, producerEpoch, read_committed). Idempotent consumer deduplication pattern. Lamport timestamps, vector clocks, and why HLC matters.

**Broker internals** — Kafka partition as append-only log (RecordBatch wire format, sparse index binary search, zero-copy sendfile path, ISR/acks mechanics, KRaft). NATS JetStream with stream/consumer config, pull vs push, deduplication window. RabbitMQ exchange types and QoS prefetch. Redis Streams with PEL and XCLAIM for dead consumer recovery.

**Cloud-native EDA** — Kinesis shard internals and enhanced fanout. EventBridge rule/target model. SNS/SQS fan-out pattern. GCP Pub/Sub exactly-once subscription and Eventarc. Azure Event Hub throughput units and Event Grid.

**Security** — Full STRIDE threat model per component (producer, network, broker, consumer, payload, store). Mitigations: SPIFFE/SPIRE SVID rotation, Kafka ACLs per principal, mTLS, SASL/OAUTHBEARER. Ed25519 event signing + replay protection (timestamp window) in Rust. AES-256-GCM field-level encryption for PII. Constant-time HMAC verification.

**Implementations** — C lock-free SPSC ring buffer (200–400M events/s), epoll production reactor with ET + drain loop, io_uring event producer with fixed buffers. Go Kafka producer (franz-go, transactional, batched, compressed), transactional consumer (read_committed, cooperative sticky rebalance), NATS JetStream producer/pull consumer, event store with optimistic concurrency, Saga orchestrator. Rust async Kafka consumer (rdkafka, mTLS, manual commit), event signing/verification, field encryption.

**Testing** — testcontainers integration test, Go fuzz target for event parsers, Rust cargo-fuzz target, chaos testing strategy (Toxiproxy/Chaos Mesh), benchmark targets with perf commands.

**Operations** — schema migration rollout phases, Kafka topic ops commands (create, resize, reset offsets, lag monitoring), incident rollback runbook.