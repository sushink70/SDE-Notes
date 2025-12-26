# Comprehensive Guide to Distributed Systems

## The Journey Ahead: A Structured Path to Mastery

Welcome to the world of distributed systems - where computing transcends single machines and embraces networks, coordination, and complexity. This guide will build your understanding from first principles, layer by layer, with the same disciplined approach you bring to DSA mastery.

---

## Part I: Foundational Concepts

### 1.1 What is a Distributed System?

**Definition**: A distributed system is a collection of independent computers (nodes) that appear to users as a single coherent system. These nodes communicate and coordinate through message passing over a network.

**Core Characteristics**:
- **Concurrency**: Multiple components execute simultaneously
- **No global clock**: Each node has its own clock; perfect synchronization is impossible
- **Independent failures**: Components can fail independently of each other
- **Spatial separation**: Nodes are physically distributed across networks

```
Single Machine (Monolithic)          Distributed System
┌──────────────────┐                ┌─────────┐   ┌─────────┐
│                  │                │ Node A  │   │ Node B  │
│   Application    │                │         │◄──►         │
│                  │                └─────────┘   └─────────┘
│   ┌──────────┐   │                     │  ▲         │  ▲
│   │ Database │   │                     │  │         │  │
│   └──────────┘   │                     ▼  │         ▼  │
└──────────────────┘                ┌─────────┐   ┌─────────┐
                                    │ Node C  │   │ Node D  │
                                    │         │◄──►         │
                                    └─────────┘   └─────────┘
```

### 1.2 Why Build Distributed Systems?

**Fundamental Motivations**:

1. **Scalability**: Handle more load by adding machines (horizontal scaling)
2. **Availability**: System continues operating despite failures
3. **Performance**: Reduce latency by placing data closer to users
4. **Reliability**: No single point of failure
5. **Physical constraints**: Data must be near users (legal/regulatory)

**Mental Model**: Think of distributed systems like a team of specialists working together, versus a single expert doing everything. Coordination overhead increases, but capabilities multiply.

---

## Part II: The Eight Fundamental Challenges

These challenges are the "gotchas" that make distributed systems intellectually fascinating and practically difficult.

### 2.1 Network Unreliability

Networks can:
- **Drop packets**: Messages disappear without trace
- **Delay packets**: Messages arrive late (unbounded delay)
- **Duplicate packets**: Same message arrives multiple times
- **Reorder packets**: Messages arrive out of order

```
Sender (A)                           Receiver (B)
    │                                     │
    │─────── Message 1 ─────────────X    │  (Lost)
    │                                     │
    │─────── Message 2 ──────┐           │
    │                        │           │
    │─────── Message 3 ───┐  │           │
    │                     │  └──────────►│  (Arrives first)
    │                     └──────────────►│  (Arrives second)
```

**Key Insight**: You can never distinguish between a slow node and a dead node over the network.

### 2.2 Partial Failures

In a monolithic system, either everything works or nothing works. In distributed systems:
- Node A might be working perfectly
- Node B might have crashed
- Node C might be slow due to garbage collection
- The network between A and B might be broken

```
Request Flow with Partial Failure:
                                    
Client ────► Load Balancer ────┬───► Server 1 ✓ (healthy)
                                ├───► Server 2 ✗ (crashed)
                                ├───► Server 3 ⚠ (slow)
                                └───► Server 4 ✓ (healthy)
                                         │
                                         ├───► DB Primary ✓
                                         └───► DB Replica ✗
```

**Mental Model**: Embrace uncertainty. Design for failure as the norm, not the exception.

### 2.3 Time and Clocks

**Three Types of Time**:

1. **Physical Time**: Wall-clock time (unreliable in distributed systems)
2. **Logical Time**: Ordering of events (Lamport timestamps, vector clocks)
3. **Hybrid Time**: Combination of both

**The Clock Synchronization Problem**:
```
Machine A Clock:  12:00:00.000
Machine B Clock:  12:00:00.045  (45ms drift)
Machine C Clock:  11:59:59.980  (20ms behind)

Event Timeline:
A writes X at 12:00:00.010 (A's clock)
B writes Y at 12:00:00.005 (B's clock)

Which happened first? Impossible to know!
```

**Cognitive Principle**: Causality matters more than chronology. Focus on "happened-before" relationships, not absolute timestamps.

### 2.4 Consensus

**The Problem**: Getting multiple nodes to agree on a single value in the presence of failures.

**Why It's Hard**:
- Nodes can crash
- Networks can partition
- Messages can be lost or delayed

```
Consensus Scenario:

Initial State:           Proposal Phase:        Final State:
Node A: ?                Node A: propose "X"    Node A: "X"
Node B: ?                Node B: propose "Y"    Node B: "X"
Node C: ?                Node C: propose "X"    Node C: "X"

Goal: All nodes must agree on the same value
Challenge: Doing this reliably with failures
```

**FLP Impossibility Result**: In an asynchronous system with even one faulty process, there's no deterministic algorithm that guarantees consensus in bounded time.

**Practical Takeaway**: We use probabilistic or time-bounded algorithms (Paxos, Raft, etc.)

### 2.5 Consistency vs. Availability Trade-off

**CAP Theorem** (Fundamental limit):
You cannot simultaneously have:
- **C**onsistency: All nodes see the same data
- **A**vailability: Every request gets a response
- **P**artition tolerance: System works despite network splits

You must choose two out of three. But partition tolerance is non-negotiable (networks do fail), so the real choice is **C** vs **A**.

```
Network Partition Scenario:

Normal Operation:          During Partition:
┌─────┐    ┌─────┐        ┌─────┐ ╱╱╱╱╱ ┌─────┐
│  A  │────│  B  │        │  A  │ ╱╱╱╱╱ │  B  │
└─────┘    └─────┘        └─────┘ ╱╱╱╱╱ └─────┘
   │          │              │            │
   │          │              │            │
┌─────┐    ┌─────┐        ┌─────┐      ┌─────┐
│  C  │────│  D  │        │  C  │      │  D  │
└─────┘    └─────┘        └─────┘      └─────┘

Choice during partition:
CP: Reject writes to maintain consistency
AP: Accept writes, risk inconsistency
```

### 2.6 State Management

**The Challenge**: Each node maintains state, but states diverge due to:
- Different operation orders
- Partial failures
- Network delays

```
State Divergence Example:

Time │ Node 1        │ Node 2        │ Node 3
─────┼───────────────┼───────────────┼──────────────
 t0  │ balance: $100 │ balance: $100 │ balance: $100
 t1  │ +$50          │               │
 t2  │ balance: $150 │ -$30          │
 t3  │               │ balance: $70  │ +$50
 t4  │ sync...       │ sync...       │ balance: $150
 t5  │ balance: ???  │ balance: ???  │ balance: ???

What should final balance be?
```

**Mental Framework**: Think about state as a sequence of transformations, not snapshots.

### 2.7 Scalability Dimensions

**Vertical Scaling**: Add more resources to a single node (CPU, RAM)
- **Limits**: Physical and cost constraints
- **Benefit**: Simple, no distribution complexity

**Horizontal Scaling**: Add more nodes
- **Limits**: Coordination overhead, diminishing returns
- **Benefit**: Theoretically unlimited

```
Scalability Patterns:

Load Distribution:
                    ┌─► Worker 1
Client ──► Router ──┼─► Worker 2
                    ├─► Worker 3
                    └─► Worker 4

Data Partitioning:
Users A-G ──► Shard 1 (Node A)
Users H-N ──► Shard 2 (Node B)
Users O-Z ──► Shard 3 (Node C)
```

### 2.8 Coordination Overhead

**Amdahl's Law for Distributed Systems**: As you add nodes, coordination cost increases. The speedup is limited by the sequential (coordinated) portion of work.

```
Speedup vs. Number of Nodes:

Speedup
   │
 8 │                               ... (theoretical)
   │                          ....
 6 │                     .....
   │                ....
 4 │           .....              ──── (actual with
   │      .....                        coordination)
 2 │ .....
   │─────────────────────────────────────►
   1   2   4   8   16  32  64        Nodes
```

**Design Principle**: Minimize coordination. Shared-nothing architectures scale best.

---

## Part III: Architecture Patterns

### 3.1 Client-Server Model

**Structure**: Clients request services, servers provide them.

```
┌──────────┐     Request      ┌──────────┐
│ Client 1 │─────────────────►│          │
└──────────┘                  │          │
                              │  Server  │
┌──────────┐     Response     │          │
│ Client 2 │◄─────────────────│          │
└──────────┘                  └──────────┘
```

**Characteristics**:
- Asymmetric: Clients initiate, servers respond
- Stateless or stateful server
- Single point of failure (server)

### 3.2 Peer-to-Peer (P2P)

**Structure**: All nodes are equal, can act as both client and server.

```
    ┌────┐
    │ P1 │◄───────┐
    └────┘        │
      ◄─┐         │
        │         │
        │    ┌────┐
        └───►│ P2 │
             └────┘
               ▲ │
               │ │
               │ ▼
    ┌────┐  ┌────┐
    │ P4 │◄─┤ P3 │
    └────┘  └────┘
```

**Use Cases**: BitTorrent, blockchain, IPFS

**Trade-offs**:
- ✓ No single point of failure
- ✓ Scales naturally
- ✗ Complex coordination
- ✗ Security challenges

### 3.3 Master-Slave (Primary-Replica)

**Structure**: One master handles writes, replicas handle reads.

```
           Writes
Client ───────────────► ┌─────────┐
                        │ Master  │
                        └─────────┘
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
              ┌─────────┐ ┌─────────┐ ┌─────────┐
 Reads ──────►│ Slave 1 │ │ Slave 2 │ │ Slave 3 │
              └─────────┘ └─────────┘ └─────────┘
```

**Replication Lag**: Time between master write and slave update creates eventual consistency.

### 3.4 Microservices Architecture

**Concept**: Break monolith into small, independent services communicating over network.

```
                    ┌──────────────┐
                    │  API Gateway │
                    └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌─────────┐         ┌─────────┐        ┌─────────┐
   │  User   │         │ Product │        │ Payment │
   │ Service │◄───────►│ Service │◄──────►│ Service │
   └─────────┘         └─────────┘        └─────────┘
        │                   │                   │
   ┌─────────┐         ┌─────────┐        ┌─────────┐
   │ User DB │         │Prod. DB │        │ Pay. DB │
   └─────────┘         └─────────┘        └─────────┘
```

**Mental Model**: Each service is a mini-distributed system. Coordination complexity moves from within the service to between services.

### 3.5 Event-Driven Architecture

**Structure**: Components communicate through events, decoupled in time and space.

```
Producer 1 ──┐
             │
Producer 2 ──┼──► ┌───────────────┐ ───┬──► Consumer 1
             │    │  Event Queue  │    │
Producer 3 ──┘    │  (Kafka/RabbitMQ) ├──► Consumer 2
                  └───────────────┘    │
                                       └──► Consumer 3

Flow:
1. Producers emit events (fire and forget)
2. Queue buffers events
3. Consumers pull/receive events
4. Processing is asynchronous
```

**Advantages**:
- **Loose coupling**: Components don't know about each other
- **Scalability**: Add consumers independently
- **Resilience**: Queue buffers during failures

---

## Part IV: Consistency Models

**Meta-Concept**: Consistency models define what guarantees a system provides about the ordering and visibility of operations.

### 4.1 Strong Consistency (Linearizability)

**Definition**: Operations appear to execute atomically and in real-time order. System behaves as if there's a single copy of data.

```
Timeline:

Client A: ───Write(x=1)───────Read(x)=1───►
               │                  │
               │                  │
Client B: ─────│──────Read(x)=1───│────────►
               ▼                  ▼
          All clients see        After A's write,
          writes immediately     all reads return 1
```

**Cost**: High latency (requires coordination), lower availability during partitions.

### 4.2 Sequential Consistency

**Definition**: Operations of all processes appear in some sequential order, but not necessarily real-time order.

```
Actual Timeline:
Client A: Write(x=1) at t1 ──── Write(x=2) at t3
Client B: ──── Write(y=5) at t2 ──── Read(x) at t4

Valid Sequential Order (not real-time):
Write(x=1) → Write(x=2) → Write(y=5) → Read(x)=2

Invalid Order:
Write(x=1) → Write(y=5) → Read(x)=2 → Write(x=2)
(violates program order of client A)
```

**Weaker than linearizability**: No real-time guarantees, but preserves per-process order.

### 4.3 Causal Consistency

**Definition**: Operations that are causally related appear in the same order to all nodes.

```
Causally Related Events:

Thread 1: Write(x=1) ─────► Read(x)=1 ─────► Write(y=2)
              │                                   │
              │ (causally related)                │
              ▼                                   ▼
Thread 2: ───────────Read(x)=1───────────────Read(y)=2

Thread 3: (independent) Write(z=5)
          Can be ordered anywhere!
```

**Mental Model**: "Happened-before" relationships must be preserved. Concurrent operations can be reordered.

**Lamport's Happened-Before Relation (→)**:
1. If a and b are in the same process and a occurs before b, then a → b
2. If a is sending a message and b is receiving it, then a → b
3. If a → b and b → c, then a → c (transitivity)

### 4.4 Eventual Consistency

**Definition**: If no new updates occur, all replicas eventually converge to the same value.

```
Timeline:

t0: Replica A: x=1    Replica B: x=1    Replica C: x=1

t1: Replica A: x=2    Replica B: x=1    Replica C: x=1
    (write occurs)    (not synced yet)  (not synced yet)

t2: Replica A: x=2    Replica B: x=2    Replica C: x=1
                      (synced)          (network delay)

t3: Replica A: x=2    Replica B: x=2    Replica C: x=2
                                        (eventually synced)
```

**Use Cases**: DNS, caches, shopping carts (where temporary inconsistency is acceptable).

**Trade-off**: Highest availability and performance, weakest guarantees.

### 4.5 Read-Your-Writes Consistency

**Guarantee**: A process always sees its own writes.

```
User Session:

Client: Write(x=1) to Server A
        │
        ├──► Replicate to Server B (async)
        │
        └──► Route subsequent reads to Server A
             (or wait for replication)
             
Client: Read(x) → Must return 1
```

**Implementation**: Session stickiness or read-your-writes tokens.

### 4.6 Monotonic Reads

**Guarantee**: Once a process reads a value, it never sees an older value.

```
Invalid Scenario (violates monotonic reads):

t1: Client reads x=5 from Replica A
t2: Replica A fails
t3: Client reads x=3 from Replica B (lagging)
    ▲
    └── VIOLATION: Went backwards in time!

Valid Implementation: Track read version, always read from version ≥ last seen
```

---

## Part V: Consensus Algorithms

**The Consensus Problem**: Multiple nodes must agree on a single value, even with failures.

### 5.1 Two-Phase Commit (2PC)

**Purpose**: Atomic commitment - all nodes commit or all abort a transaction.

**Phases**:

```
Phase 1: Prepare (Voting)
Coordinator                        Participants
     │                           ┌──────┐  ┌──────┐
     ├─── Prepare ──────────────►│ N1   │  │ N2   │
     │                           │ Vote │  │ Vote │
     │◄──── Yes/No ──────────────┤ Y/N  │  │ Y/N  │
     │                           └──────┘  └──────┘
     │
     ├─── Decision Phase ────►

Phase 2: Commit/Abort
     │
     ├─── Commit (if all Yes) ──►│ N1   │  │ N2   │
     │                            │Execute   Execute
     │                            └──────┘  └──────┘
```

**Blocking Problem**:
```
Scenario: Coordinator crashes after Phase 1
Participants: In limbo, waiting forever
Solution: Use Three-Phase Commit (3PC) or timeout
```

**Mental Model**: Like a committee vote where abstention (failure) blocks progress.

### 5.2 Paxos (The Byzantine General)

**Conceptual Flow**:

**Roles**:
- **Proposers**: Suggest values
- **Acceptors**: Vote on values
- **Learners**: Learn the chosen value

```
Paxos Phases:

Phase 1: Prepare
Proposer                    Acceptors (3 nodes)
   │─── Prepare(n=5) ──────┬──► A1: Promise(5)
   │                        ├──► A2: Promise(5)
   │                        └──► A3: Promise(5)
   │◄─── Promise ───────────────(majority)

Phase 2: Accept
   │─── Accept(n=5, v="X")─┬──► A1: Accepted
   │                        ├──► A2: Accepted
   │                        └──► A3: Accepted
   │◄─── Accepted ──────────────(majority)
   
   Value "X" is chosen!
```

**Key Insight**: Uses proposal numbers to serialize concurrent proposals. Higher proposal number takes precedence.

**Failure Handling**:
- Can tolerate f failures with 2f+1 nodes
- Requires majority (quorum) for progress
- Never decides on two different values

### 5.3 Raft (Understandable Consensus)

**Simplification of Paxos**: Designed for understandability.

**States**:
- **Leader**: Handles all client requests
- **Follower**: Passively receive updates
- **Candidate**: Trying to become leader

```
Normal Operation:

┌────────┐                    ┌──────────┐
│ Client │───Request────────► │  Leader  │
└────────┘                    └──────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │ AppendEntries   │                 │
                  ▼                 ▼                 ▼
            ┌──────────┐      ┌──────────┐     ┌──────────┐
            │Follower 1│      │Follower 2│     │Follower 3│
            └──────────┘      └──────────┘     └──────────┘
```

**Leader Election**:
```
Initial State: All Followers
    │
    ├─► Follower 1: Election timeout
    │                │
    │                ├─► Becomes Candidate
    │                │
    │                ├─► Requests votes
    │                │
    ├───────────────►│◄─── Vote granted
    │                │
    └───────────────►│◄─── Vote granted
                     │
            (Majority achieved)
                     │
                     ▼
               Becomes Leader
```

**Log Replication**:
```
Leader Log:  [1: x=1] [2: y=2] [3: z=3] [4: w=4]
               │       │       │       │
Follower 1:  [1: x=1] [2: y=2] [3: z=3] [syncing...]
Follower 2:  [1: x=1] [2: y=2] [3: z=3] [4: w=4] ✓
Follower 3:  [1: x=1] [2: y=2] [syncing...]

Committed:   [1: x=1] [2: y=2] [3: z=3]
             (replicated on majority)
```

**Safety Properties**:
1. **Election Safety**: At most one leader per term
2. **Leader Append-Only**: Leader never deletes/overwrites entries
3. **Log Matching**: If two logs contain same entry, all preceding entries are identical
4. **Leader Completeness**: If entry committed in term T, it appears in all future leaders
5. **State Machine Safety**: If server applies entry at index i, no other server applies different entry at i

**Mental Framework**: Think of Raft as a replicated state machine where the leader serializes all operations into a log that followers replicate.

---

## Part VI: Replication Strategies

**Purpose**: Maintain multiple copies of data for availability and fault tolerance.

### 6.1 Single-Leader Replication

```
Writes Only             Reads (can be distributed)
     │                           │
     ▼                           ▼
┌─────────┐                ┌─────────┐
│ Leader  │───Sync────────►│Follower1│
└─────────┘                └─────────┘
     │                           ▲
     │                           │
     └───────Async──────────────►│
                           ┌─────────┐
                           │Follower2│
                           └─────────┘
```

**Synchronous vs. Asynchronous Replication**:

**Synchronous**:
```
Client ──Write──► Leader ──Sync──► Follower
          │                           │
          │◄─────── ACK ──────────────┤
          │                           │
          └◄────── Response ──────────┘

+ Strong consistency
- Higher latency
- Lower availability (follower failure blocks writes)
```

**Asynchronous**:
```
Client ──Write──► Leader ──Async──► Follower
          │            │
          │            └──► (continues in background)
          │
          └◄── Response (immediate)

+ Lower latency
+ Higher availability
- Potential data loss
- Eventual consistency
```

**Semi-Synchronous** (Hybrid):
```
Leader ────Sync───► Follower 1 (synchronous)
    │
    └────Async───► Follower 2 (asynchronous)
    │
    └────Async───► Follower 3 (asynchronous)

Balance: Guarantee at least one up-to-date copy without blocking on all
```

### 6.2 Multi-Leader Replication

**Structure**: Multiple nodes accept writes, replicate to each other.

```
    Data Center 1              Data Center 2
    ┌─────────┐                ┌─────────┐
    │ Leader 1│◄──Replicate───►│ Leader 2│
    └─────────┘                └─────────┘
         │                          │
    Followers                  Followers
```

**Conflict Resolution Challenge**:
```
Scenario: Both leaders receive concurrent writes

Leader 1: Write(x=1) at t1
Leader 2: Write(x=2) at t1

After replication, both see:
  x=1 (from Leader 1)
  x=2 (from Leader 2)

Which value to keep?
```

**Conflict Resolution Strategies**:

1. **Last Write Wins (LWW)**:
```
Keep the write with the latest timestamp
Problem: Clocks are unreliable!
```

2. **Version Vectors**:
```
Track causality, keep both if concurrent
x = {value: 1, version: [L1:1, L2:0]}
y = {value: 2, version: [L1:0, L2:1]}
→ Conflict! Application must resolve
```

3. **Custom Merge**:
```
Application-specific logic
Example: Shopping cart merges both additions
```

4. **Operational Transformation**:
```
Transform operations to commute
Used in: Google Docs, collaborative editors
```

### 6.3 Leaderless Replication (Dynamo-style)

**Principle**: Client writes to multiple replicas, majority determines success.

```
Client Write Request:
                            Replica 1 ✓ ACK
                                │
Client ──Write(x=5, W=2)───────┼──► Replica 2 ✓ ACK
                                │
                                └──► Replica 3 ✗ (timeout)
                                     Replica 4 ✗ (slow)

Write succeeds if W replicas acknowledge (W=2 in this case)
```

**Quorum Reads and Writes**:

**Configuration**:
- N = Total replicas
- W = Write quorum (replicas that must acknowledge write)
- R = Read quorum (replicas that must respond to read)

**Quorum Condition**: W + R > N ensures overlap

```
Example: N=5, W=3, R=3

Write to 5 replicas:
┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐
│ A │ │ B │ │ C │ │ D │ │ E │
└───┘ └───┘ └───┘ └───┘ └───┘
  ✓     ✓     ✓     ?     ?
(W=3 acknowledged, write succeeds)

Read from 5 replicas:
┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐
│ A │ │ B │ │ C │ │ D │ │ E │
└───┘ └───┘ └───┘ └───┘ └───┘
  ✓     ?     ✓     ✓     ?
(R=3 responded)

At least one replica in read quorum has latest write!
```

**Sloppy Quorums and Hinted Handoff**:
```
Normal Quorum: Write to nodes A, B, C
Network Partition: A, B unreachable
Sloppy Quorum: Write to C, D, E instead
                (D, E are "hints" for A, B)

When A, B return:
  D, E transfer data back to A, B
  ("hinted handoff")
```

**Anti-Entropy** (Background repair):
```
Periodic process comparing replica data:

Replica 1: {x:5, y:3, z:8}
Replica 2: {x:5, y:2, z:8}  ← y is outdated
                │
                └──► Merkle tree comparison
                     detects divergence
                     │
                     └──► Transfer missing data
```

---

## Part VII: Partitioning (Sharding)

**Goal**: Split data across multiple nodes to scale beyond single machine capacity.

### 7.1 Partitioning by Key Range

**Strategy**: Assign continuous range of keys to each partition.

```
Key Space:  A─────────M─────────Z
            │         │         │
Partition:  1         2         3

Partition 1: Keys A-L (node1)
Partition 2: Keys M-T (node2)
Partition 3: Keys U-Z (node3)
```

**Advantage**: Range queries efficient (scan one partition)
**Disadvantage**: Hotspots if access isn't uniform

### 7.2 Partitioning by Hash

**Strategy**: Hash key, assign to partition based on hash value.

```
Key → Hash Function → Partition

hash("alice") % 3 = 1 → Partition 1
hash("bob") % 3 = 2 → Partition 2
hash("charlie") % 3 = 0 → Partition 0

Hash space:  ──────────────────────►
             0    1    2    3    4  (mod 5)
             │    │    │    │    │
Partition:   A    B    A    B    A
```

**Advantage**: Uniform distribution
**Disadvantage**: Range queries require scanning all partitions

### 7.3 Consistent Hashing

**Problem**: When adding/removing nodes, minimize data movement.

**Traditional Hashing Problem**:
```
3 nodes: hash(key) % 3
Add 4th node: hash(key) % 4
→ Most keys must move!
```

**Consistent Hashing Solution**:
```
Hash Ring (0 to 2^32-1):

           hash=0
             │
        ┌────┼────┐
       │     │     │
   Node C   │   Node A
       │     │     │
        └────┼────┘
             │
          Node B

Key "alice" → hash("alice") = 45678
    → Clockwise to next node = Node A

Add Node D:
- Only keys between C and D move
- Other keys unaffected!
```

**Virtual Nodes** (vnodes):
```
Physical node A has virtual nodes: A1, A2, A3
Physical node B has virtual nodes: B1, B2, B3

Ring: ─A1─B1─A2─B2─A3─B3─A1─
          │
    Better distribution than single position
```

### 7.4 Secondary Indexes in Partitioned Databases

**Challenge**: How to index data across partitions?

**Document-Based Partitioning** (Local Index):
```
Partition 1:           Partition 2:
Users: alice, bob      Users: charlie, diana
Index:                 Index:
  age=25: alice          age=25: charlie
  age=30: bob            age=28: diana

Query "age=25" → Must scatter to all partitions!
```

**Term-Based Partitioning** (Global Index):
```
Data Partitions:       Index Partitions:
Partition 1: alice     Index 1: age=20-29
Partition 2: bob       Index 2: age=30-39

Query "age=25":
  → Go directly to Index 1
  → Find relevant data partitions

Downside: Updates must update both data and index partitions
```

---

## Part VIII: Fault Tolerance and Recovery

### 8.1 Failure Detection

**Heartbeat Mechanism**:
```
Node A ────heartbeat───► Monitor
          (every 1s)
                          │
                          ├─ Timeout: 3s
                          │
                          ▼
                    (No heartbeat)
                          │
                          ▼
                    Mark A as failed
```

**Phi Accrual Failure Detector**:
```
Instead of binary (alive/dead):
  φ = continuous suspicion level

φ < threshold: Likely alive
φ > threshold: Likely dead

Adapts to network conditions!
```

### 8.2 Split-Brain Problem

**Scenario**: Network partition creates two groups, each thinking it's the only one.

```
Normal:                   Partition:
┌────────────────┐        ┌──────┐    ┌──────┐
│  N1  N2  N3   │        │ N1   │    │ N2 N3│
│               │   →    │"I'm  │    │"We're│
│  Cluster      │        │leader"    │leader"
└────────────────┘        └──────┘    └──────┘
                          Both accept writes!
                          Data diverges!
```

**Solution: Quorum-Based Decision**:
```
Require majority for operations:

Partition 1: N1 (1 node) → No quorum, halt
Partition 2: N2, N3 (2 nodes) → Quorum, continue

Only one side can make progress
```

### 8.3 Fencing Tokens

**Problem**: Old leader doesn't know it's been replaced.

```
Timeline:
t1: Node 1 is leader (epoch=1)
t2: Node 1 pauses (GC, network issue)
t3: Cluster elects Node 2 (epoch=2)
t4: Node 1 resumes, thinks it's still leader
    Tries to write with epoch=1
```

**Solution: Monotonic Fencing Tokens**:
```
Storage Server:

Receive write(epoch=1, data=X) from Node 1
  Current epoch: 2
  Decision: REJECT (epoch too old)

Receive write(epoch=2, data=Y) from Node 2
  Current epoch: 2
  Decision: ACCEPT
```

### 8.4 Write-Ahead Log (WAL)

**Principle**: Before applying changes, write them to append-only log.

```
Transaction Flow:

1. Client: Write(x=5)
          │
          ▼
2. [WAL]: Write "x=5" to log (durable)
          │
          ▼
3. [Memory]: Update x=5 in memory
          │
          ▼
4. Client: ACK

On Crash:
  Replay WAL to reconstruct state
```

**Log Structure**:
```
WAL File (append-only):
┌─────────────────────────────────────┐
│ [1] BEGIN TRANSACTION               │
│ [2] SET x=5                         │
│ [3] SET y=10                        │
│ [4] COMMIT                          │ ← Checkpoint
│ [5] BEGIN TRANSACTION               │
│ [6] SET z=15                        │
│ ...                                 │
└─────────────────────────────────────┘
```

**Checkpointing**:
```
Periodically flush memory to disk
Mark checkpoint in WAL
Delete old WAL entries before checkpoint

Memory State    WAL
   x=5 ────────► [CHECKPOINT: x=5]
                 [New entries...]
   
Old entries before checkpoint can be discarded
```

### 8.5 Idempotence

**Definition**: Operation produces same result whether applied once or multiple times.

```
Idempotent:
  SET x=5
    First execution: x=5
    Second execution: x=5 (same result) ✓

Non-Idempotent:
  INCREMENT x
    First execution: x=6
    Second execution: x=7 (different!) ✗
```

**Designing for Idempotence**:
```
Non-Idempotent Request:
  POST /transfer?amount=100

Idempotent Request:
  POST /transfer?amount=100&idempotency_key=abc123
                                               │
                                               └─ Server tracks: 
                                                  If seen before,
                                                  return cached result
```

---

## Part IX: Communication Patterns

### 9.1 Request-Response (Synchronous)

```
Client                        Server
  │                             │
  ├────── Request ─────────────►│
  │                             │ (processing)
  │                             │
  │◄───── Response ─────────────┤
  │                             │
  ▼                             ▼
```

**Characteristics**:
- Blocking: Client waits for response
- Simple to reason about
- Tight coupling
- Latency sensitive

### 9.2 Asynchronous Messaging

```
Producer                   Queue                    Consumer
  │                          │                        │
  ├── Send ─────────────────►│                        │
  │                          │  (message buffered)    │
  │                          │                        │
  ├── (continues work)       │                        │
  │                          │                        │
  │                          │◄────── Poll/Pull ──────┤
  │                          │                        │
  │                          ├───── Message ─────────►│
```

**Advantages**:
- Decoupling (producer/consumer don't interact directly)
- Buffering (queue absorbs load spikes)
- Reliability (message persists if consumer down)

### 9.3 Remote Procedure Call (RPC)

**Goal**: Make remote calls look like local function calls.

```
Client Code:
  result = calculate(5, 10)
           │
           └──► Looks local, but...

Under the Hood:
Client Stub              Network              Server Stub
    │                                              │
    ├─ 1. Serialize args ───►                     │
    │                                              │
    ├─ 2. Send over network ─────────────────────►│
    │                                              │
    │                                        3. Deserialize
    │                                              │
    │                                        4. Call local function
    │                                              │
    │◄─ 6. Return result ──────────────────────── │
    │                                              │
    7. Deserialize result                         │
```

**Fallacies of Distributed Computing**:
1. The network is reliable (it's not!)
2. Latency is zero (it's milliseconds/seconds)
3. Bandwidth is infinite (it's limited)
4. The network is secure (it's not!)
5. Topology doesn't change (it does)
6. There is one administrator (there isn't)
7. Transport cost is zero (marshalling has overhead)
8. The network is homogeneous (mixed technologies)

**Mental Trap**: RPC hides distributed systems complexity, but you must still handle:
- Network failures
- Timeouts
- Partial failures
- Retries and idempotence

### 9.4 Publish-Subscribe

```
      Publisher 1 ──┐
                    │
      Publisher 2 ──┤──► Topic: "orders"
                    │
      Publisher 3 ──┘
                            │
                ┌───────────┼───────────┐
                │           │           │
          Subscriber A  Subscriber B  Subscriber C
          (all get        (all get      (all get
           messages)       messages)     messages)
```

**Fan-Out**:
```
Single publish → Multiple subscribers receive

Message: "Order #123 created"
  ├──► Inventory Service (update stock)
  ├──► Billing Service (charge customer)
  ├──► Email Service (send confirmation)
  └──► Analytics Service (log event)
```

---

## Part X: Distributed Transactions

### 10.1 ACID Properties

**Atomicity**: All or nothing
```
BEGIN TRANSACTION
  UPDATE accounts SET balance = balance - 100 WHERE id=1;
  UPDATE accounts SET balance = balance + 100 WHERE id=2;
COMMIT;

If any statement fails, ALL are rolled back
```

**Consistency**: Database moves from one valid state to another
```
Invariant: sum of all account balances constant

Before: Account A: $500, Account B: $300 (sum=$800)
Transfer: A → B ($100)
After: Account A: $400, Account B: $400 (sum=$800) ✓
```

**Isolation**: Concurrent transactions don't interfere
```
Transaction 1: Read balance → $500
Transaction 2: Read balance → $500
Transaction 1: Withdraw $100 → $400
Transaction 2: Withdraw $200 → $300 (wrong!)

Isolation prevents this race condition
```

**Durability**: Committed data survives failures
```
Write → WAL → Flush to disk → Commit
                │
                └─ Power loss here?
                   Data survives (in WAL)
```

### 10.2 Isolation Levels

**Read Uncommitted** (Lowest):
```
T1: Write(x=1) ─────────► Commit
                │
T2: ────────────┼─Read(x=1)─► (Dirty Read!)
                │              
           (not committed yet)

Allows: Dirty reads
```

**Read Committed**:
```
T1: Write(x=1) ─────────► Commit
                          │
T2: ────Read(x=0)────────┼─Read(x=1)─► ✓
         (old value)   (committed value)

Prevents: Dirty reads
Allows: Non-repeatable reads
```

**Repeatable Read**:
```
T1: Read(x=0) ────Read(x=0)─► (same value) ✓
         │            │
T2: ────────Write(x=1)─Commit

Prevents: Dirty reads, non-repeatable reads
Allows: Phantom reads
```

**Serializable** (Highest):
```
Transactions execute as if serial

T1 ──────────────────►
                      T2 ──────────────►

Result is equivalent to some serial execution
Prevents: All anomalies
Cost: Lowest concurrency
```

### 10.3 Two-Phase Locking (2PL)

**Principle**: Transaction acquires all locks before releasing any.

```
Transaction Lifecycle:

Growing Phase:        Shrinking Phase:
(acquire locks)      (release locks)
    │                     │
    ├─ Read(x) → lock(x)  │
    │                     │
    ├─ Write(y) → lock(y) │
    │                     │
    ├─────────────────────┼→ unlock(x)
    │                     │
    └─────────────────────┼→ unlock(y)

Lock Point ─────────────►▲
         (no more locks acquired after this)
```

**Deadlock Scenario**:
```
T1: Lock(A) ──┐         ┌─ Lock(B)
              │         │
              └─ Want(B) (waiting...)
                         ▲
T2: Lock(B) ──┐         │
              └─ Want(A)─┘ (waiting...)

Both waiting for each other → DEADLOCK!
```

**Deadlock Detection and Resolution**:
```
Wait-For Graph:

T1 ──waits for──► T2
 ▲                │
 │                │
 └────────────────┘
        Cycle! Deadlock detected

Resolution: Abort one transaction (break cycle)
```

### 10.4 Multi-Version Concurrency Control (MVCC)

**Principle**: Keep multiple versions of data, readers don't block writers.

```
Timeline:

T1 (txn_id=1): Read(x) → sees version v1
    │
    ├─ v1: x=100 (visible to T1)
    │
T2 (txn_id=2): Write(x=200) → creates version v2
    │
    ├─ v2: x=200 (visible to T2 and future txns)
    │
    └─ v1: x=100 (still visible to T1)

T1 continues seeing v1 (snapshot isolation)
T2 sees v2 (its own writes)
```

**Version Storage**:
```
Record: x
┌─────────────────────────────────────┐
│ Version 3: x=300, txn_id=3, t=300  │
│ Version 2: x=200, txn_id=2, t=200  │
│ Version 1: x=100, txn_id=1, t=100  │
└─────────────────────────────────────┘

Read(x) at txn_id=2:
  → Find highest version where txn_id ≤ 2
  → Return Version 2: x=200
```

**Garbage Collection**:
```
When no active transaction needs old versions:
  Delete them

Active transactions: txn_id=5, 6, 7
Oldest: txn_id=5
  → Can delete versions with txn_id < 5
```

---

## Part XI: Time and Ordering

### 11.1 Physical Clocks (Wall-Clock Time)

**Challenge**: Clocks drift over time.

```
Perfect Time:  ───────────────────────►
                    
Server A Clock: ───────────────►  (fast)
                    ▲
Server B Clock: ───────────►  (slow)

Drift rate: ~10-6 (1ms per 1000s)
```

**Network Time Protocol (NTP)**:
```
Client                      NTP Server
  │                             │
  ├── t1: Send request ────────►│
  │                             │ t2: Receive
  │                             │ t3: Send response
  │◄───────────────────────────┤
  t4: Receive                   │

Offset = ((t2 - t1) + (t3 - t4)) / 2
Round-trip = (t4 - t1) - (t3 - t2)
```

**Clock Skew Issues**:
```
Server A (clock=12:00:00.100): Write event E1
Server B (clock=12:00:00.050): Write event E2

Which happened first? Cannot tell!
```

### 11.2 Lamport Timestamps (Logical Clocks)

**Principle**: Track causality, not absolute time.

**Algorithm**:
1. Each process maintains counter
2. Increment counter before each event
3. Send counter with messages
4. On receive: counter = max(local, received) + 1

```
Process A:    ──1──────2──────4─────►
                │       │       ▲
               msg(1)   │       │
                │       │     msg(3)
                ▼       │       │
Process B:    ──2──────3──────3─────►
                        │
                       msg(3)
                        │
                        ▼
Process C:    ──1──────4─────►

Event ordering: E1 → E2 iff timestamp(E1) < timestamp(E2)
```

**Limitation**: Cannot determine if events are concurrent.

```
Event A: timestamp=5
Event B: timestamp=5

Are they concurrent or did one happen first?
Lamport timestamps don't tell us!
```

### 11.3 Vector Clocks

**Solution**: Track causality from ALL processes.

**Structure**: Vector of counters, one per process

```
Process A: [1, 0, 0] ──► [2, 0, 0] ──► [2, 2, 0]
                                            ▲
                                            │
Process B: [0, 1, 0] ──► [0, 2, 0] ────────┤
                             │
                             └──► [0, 2, 1]
                                      │
Process C: [0, 0, 1] ────────────────┘

Comparison:
  V1 < V2 iff V1[i] ≤ V2[i] for all i, and V1 ≠ V2
  V1 || V2 (concurrent) iff neither V1 < V2 nor V2 < V1
```

**Example**:
```
A: [2, 0, 0] and B: [1, 1, 0]
  A[0]=2 > B[0]=1 and A[1]=0 < B[1]=1
  → Concurrent!

C: [2, 2, 0] and D: [2, 3, 1]
  C[i] ≤ D[i] for all i, C ≠ D
  → C < D
```

