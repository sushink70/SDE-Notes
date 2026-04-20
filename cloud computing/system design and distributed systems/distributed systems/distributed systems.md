**Distributed Systems (Must-Learn Concepts)**

Distributed systems build on the above but focus on coordination across unreliable networks and partial failures. Key resources emphasize first principles (network unreliability, consensus, etc.).

- **Fundamentals & Challenges**
  - Definition: Multiple independent nodes communicating via message passing (vs centralized/parallel/decentralized systems)
  - Benefits: Scalability, Reliability (fault tolerance via replication), Performance (parallel execution)
  - Core challenges: Partial failures, Network unreliability ("the network is not reliable"), Consistency vs Availability, Coordination overhead
  - CAP Theorem (deep dive with real system examples like Cassandra, MongoDB, Redis, Kafka)

- **Communication & Coordination**
  - Inter-process communication (IPC), Message passing, Gossip protocols
  - Remote Procedure Calls (RPC), gRPC
  - Service discovery and coordination tools (e.g., ZooKeeper, etcd concepts)
  - Time synchronization (logical clocks, vector clocks)

- **Data Distribution & Storage**
  - Consistent Hashing, Sharding strategies (range vs hash partitioning, shard keys)
  - Replication (leader-follower, multi-master, quorum)
  - Distributed datastores concepts (e.g., from examples like Cassandra's wide-column + gossip, MongoDB replica sets, Redis Cluster, Kafka partitions)

- **Consensus, Fault Tolerance & Consistency**
  - Consensus algorithms: Paxos, Raft (leader election, global snapshots)
  - Fault tolerance: Retries, Circuit breakers, Idempotency, Eventual consistency models, CRDTs
  - Distributed tracing, Exactly-once semantics
  - Byzantine fault tolerance (advanced)

- **Architectures & Models**
  - Master-Slave vs Peer-to-Peer (and hybrids)
  - Categories: Distributed datastores, messaging systems, computing platforms, file systems, ledgers
