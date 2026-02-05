# The Raft Consensus Algorithm: A Complete Mastery Guide

*"In distributed systems, agreement is the foundation of truth. Raft makes agreement understandable."*

---

## Mental Model: What Problem Are We Solving?

Before diving into Raft, understand the **fundamental challenge**:

**The Distributed Consensus Problem**: How do multiple computers agree on a single value (or sequence of operations) when:
- Networks can delay, drop, or reorder messages
- Machines can crash and restart
- No global clock exists
- We need fault tolerance (system works even if some machines fail)

**Real-world analogy**: Imagine 5 generals surrounding an enemy city. They communicate via messengers. They must all agree to attack at the same time or all retreat. But messengers can be captured, generals can die, and messages can arrive out of order. How do they reliably agree?

This is **consensus** — and it's the heart of distributed databases (etcd, Consul), distributed file systems, and replicated state machines.

---

## Part 1: Core Concepts & Mental Framework

### 1.1 What is Raft?

**Raft** is a **consensus algorithm** designed to be understandable. It was created as an alternative to Paxos (which is notoriously complex).

**Key insight**: Raft decomposes consensus into three independent subproblems:
1. **Leader Election** - How to choose one server to manage the log
2. **Log Replication** - How to keep logs identical across servers  
3. **Safety** - Ensuring consistency even during failures

### 1.2 Core Concepts Explained

#### **Server States**
Every server is in exactly one of three states:

```
┌─────────────┐
│   FOLLOWER  │ ◄─── Default state, passive
└─────────────┘
       │
       │ (timeout, no heartbeat)
       ▼
┌─────────────┐
│  CANDIDATE  │ ◄─── Requesting votes
└─────────────┘
       │
       │ (wins election)
       ▼
┌─────────────┐
│   LEADER    │ ◄─── Manages log replication
└─────────────┘
```

**Follower**: Passive. Responds to requests from leaders and candidates.
**Candidate**: Actively seeking to become leader.
**Leader**: Handles all client requests, replicates log to followers.

#### **Terms** (Logical Time)
- Think of terms as "epochs" or "presidential terms"
- Each term begins with an election
- At most one leader per term
- Terms act as a logical clock to detect stale information

```
Term:  1    2    2    3    4    4    5
       │    │    │    │    │    │    │
Event: E    L    E    L    E    L    E

E = Election
L = Normal operation under leader
```

#### **Log Structure**
Each server maintains a **log** of commands:

```
Index:  1      2      3      4      5
       ┌──────┬──────┬──────┬──────┬──────┐
       │ x=3  │ y=7  │ x=5  │ z=1  │ y=9  │
       │ T:1  │ T:1  │ T:1  │ T:2  │ T:2  │
       └──────┴──────┴──────┴──────┴──────┘

Each entry contains:
- Command (the operation)
- Term (when it was received by leader)
- Index (position in log)
```

**Log Matching Property**: If two logs contain an entry with same index and term, then:
1. They store the same command
2. All preceding entries are identical

#### **Commitment**
An entry is **committed** when it's safely replicated on a majority of servers.

```
Server 1 (Leader): [1][2][3][4][5]     ← Has entries 1-5
Server 2:          [1][2][3][4][5]     ← Replicated 1-5
Server 3:          [1][2][3]           ← Only has 1-3
Server 4:          [1][2][3][4]        ← Has 1-4
Server 5:          [1][2]              ← Only has 1-2

Committed entries: [1][2][3][4]
(4 is on 3/5 servers = majority)

Entry 5 is not yet committed.
```

---

## Part 2: Leader Election (Deep Dive)

### 2.1 The Election Process

**Mental model**: Think of it as a democratic election with randomized timeouts to prevent ties.

**Election timeout**: Random duration (e.g., 150-300ms) after which a follower becomes a candidate.

**Election flow**:

```
┌─────────────────────────────────────────────────────┐
│ 1. Follower timeout → Become CANDIDATE              │
│ 2. Increment current term                            │
│ 3. Vote for self                                     │
│ 4. Send RequestVote RPCs to all other servers        │
│ 5. Wait for responses:                               │
│    • Receive majority votes → Become LEADER          │
│    • Receive heartbeat from valid leader → FOLLOWER  │
│    • Timeout → Start new election                    │
└─────────────────────────────────────────────────────┘
```

### 2.2 RequestVote RPC

**Purpose**: Candidate requests vote from another server.

**Arguments**:
- `term`: Candidate's term
- `candidateId`: Candidate requesting vote
- `lastLogIndex`: Index of candidate's last log entry
- `lastLogTerm`: Term of candidate's last log entry

**Response**:
- `term`: Current term (for candidate to update itself)
- `voteGranted`: True if candidate received vote

**Voting rules** (voter's perspective):
```
Grant vote if ALL of these are true:
1. Candidate's term ≥ my current term
2. I haven't voted for anyone else this term
3. Candidate's log is at least as up-to-date as mine
```

**"Up-to-date" comparison**:
```
Candidate's log is more up-to-date if:
1. Last entry has higher term, OR
2. Same term but longer log (higher lastLogIndex)

Example:
Me:        [T:1][T:1][T:2]
Candidate: [T:1][T:2][T:2][T:3]

Candidate wins (term 3 > term 2)

Me:        [T:1][T:2][T:2]
Candidate: [T:1][T:2]

I win (same term 2, but I have more entries)
```

---

## Part 3: Log Replication (The Heart of Raft)

### 3.1 Normal Operation Flow

```
Client
  │
  │ 1. Send command
  ▼
Leader
  │
  │ 2. Append to local log
  │ 3. Send AppendEntries RPC to followers
  ▼
Followers
  │
  │ 4. Append to their logs
  │ 5. Send success response
  ▼
Leader
  │
  │ 6. Wait for majority
  │ 7. Commit entry
  │ 8. Apply to state machine
  │ 9. Respond to client
  ▼
Client
```

### 3.2 AppendEntries RPC

**Purpose**: Leader replicates log entries AND sends heartbeats.

**Arguments**:
- `term`: Leader's term
- `leaderId`: So follower can redirect clients
- `prevLogIndex`: Index of log entry immediately preceding new ones
- `prevLogTerm`: Term of prevLogIndex entry
- `entries[]`: Log entries to store (empty for heartbeat)
- `leaderCommit`: Leader's commitIndex

**Response**:
- `term`: Current term
- `success`: True if follower contained entry matching prevLogIndex and prevLogTerm

**Consistency check** (follower's perspective):
```
1. Reply false if leader's term < my term
2. Reply false if I don't have an entry at prevLogIndex 
   with term matching prevLogTerm
3. Delete conflicting entries and append new ones
4. Update commitIndex to min(leaderCommit, index of last new entry)
```

### 3.3 Handling Log Inconsistencies

**Problem**: After crashes, follower logs can diverge from leader's log.

**Example scenario**:
```
Leader:   [1,1][2,1][3,1][4,2][5,2]
Follower: [1,1][2,1][3,1][4,3]

Follower has entry at index 4 with wrong term (3 vs 2)
```

**Raft's solution**: Leader forces followers to duplicate its log.

**Algorithm**:
1. Leader maintains `nextIndex[]` for each follower (next entry to send)
2. If AppendEntries fails (consistency check), decrement `nextIndex` and retry
3. Eventually find the point where logs match, then overwrite follower's log from that point

**Optimization**: Instead of decrementing one at a time, follower can return:
- Conflicting term
- Index of first entry with that term
- Leader jumps back to that point

---

## Part 4: Safety Properties

### 4.1 Election Restriction

**Critical invariant**: Only candidates with all committed entries can become leader.

**Why?**: Prevents committed entries from being lost.

**How?**: The "up-to-date" check in RequestVote ensures this.

**Proof sketch**:
```
1. Entry committed → replicated on majority
2. Candidate wins → receives votes from majority
3. These majorities must overlap (pigeonhole principle)
4. At least one voter has the committed entry
5. That voter won't vote unless candidate's log ≥ theirs
6. Therefore, candidate has committed entry
```

### 4.2 Leader Completeness

**Property**: If an entry is committed in some term, it will be present in the logs of all leaders for higher terms.

**Consequence**: Leaders never overwrite or delete committed entries.

### 4.3 State Machine Safety

**Property**: If a server has applied a log entry at a given index to its state machine, no other server will ever apply a different log entry for the same index.

**Why it holds**: Follows from log matching + leader completeness.

---

## Part 5: Complete Implementation in Rust

Let's build a production-ready Raft implementation.

### 5.1 Core Data Structures

```rust
// src/raft.rs

use std::time::{Duration, Instant};
use std::collections::HashMap;
use tokio::sync::{mpsc, RwLock};
use std::sync::Arc;

/// Represents the state of a Raft server
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ServerState {
    Follower,
    Candidate,
    Leader,
}

/// A single log entry
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LogEntry {
    /// The term when entry was received by leader
    pub term: u64,
    /// The command to apply to state machine
    pub command: Vec<u8>,
}

/// Persistent state on all servers
/// (Updated on stable storage before responding to RPCs)
#[derive(Debug, Clone)]
pub struct PersistentState {
    /// Latest term server has seen (increases monotonically)
    pub current_term: u64,
    /// CandidateId that received vote in current term (or None)
    pub voted_for: Option<u64>,
    /// Log entries; each entry contains command and term
    pub log: Vec<LogEntry>,
}

/// Volatile state on all servers
#[derive(Debug, Clone)]
pub struct VolatileState {
    /// Index of highest log entry known to be committed
    pub commit_index: usize,
    /// Index of highest log entry applied to state machine
    pub last_applied: usize,
}

/// Volatile state on leaders (reinitialized after election)
#[derive(Debug, Clone)]
pub struct LeaderState {
    /// For each server, index of next log entry to send
    /// (initialized to leader last log index + 1)
    pub next_index: HashMap<u64, usize>,
    /// For each server, index of highest log entry known to be replicated
    /// (initialized to 0, increases monotonically)
    pub match_index: HashMap<u64, usize>,
}

/// Main Raft server structure
pub struct RaftNode {
    /// Unique identifier for this server
    pub id: u64,
    /// IDs of all servers in cluster
    pub peers: Vec<u64>,
    
    /// Current state (Follower/Candidate/Leader)
    pub state: ServerState,
    
    /// Persistent state
    pub persistent: PersistentState,
    
    /// Volatile state
    pub volatile: VolatileState,
    
    /// Leader-specific state (Some if leader, None otherwise)
    pub leader_state: Option<LeaderState>,
    
    /// When we last heard from the leader
    pub last_heartbeat: Instant,
    
    /// Random election timeout duration
    pub election_timeout: Duration,
    
    /// Channel for receiving RPCs
    pub rpc_rx: mpsc::UnboundedReceiver<RaftRPC>,
    
    /// Channels for sending RPCs to peers
    pub peer_channels: HashMap<u64, mpsc::UnboundedSender<RaftRPC>>,
}

/// RPC messages
#[derive(Debug, Clone)]
pub enum RaftRPC {
    RequestVote {
        term: u64,
        candidate_id: u64,
        last_log_index: usize,
        last_log_term: u64,
        response_tx: mpsc::UnboundedSender<RequestVoteResponse>,
    },
    RequestVoteResponse {
        term: u64,
        vote_granted: bool,
    },
    AppendEntries {
        term: u64,
        leader_id: u64,
        prev_log_index: usize,
        prev_log_term: u64,
        entries: Vec<LogEntry>,
        leader_commit: usize,
        response_tx: mpsc::UnboundedSender<AppendEntriesResponse>,
    },
    AppendEntriesResponse {
        term: u64,
        success: bool,
        match_index: usize,  // For optimization
    },
}

#[derive(Debug, Clone)]
pub struct RequestVoteResponse {
    pub term: u64,
    pub vote_granted: bool,
}

#[derive(Debug, Clone)]
pub struct AppendEntriesResponse {
    pub term: u64,
    pub success: bool,
    pub match_index: usize,
}
```

**Mental note**: We separate persistent state (must survive crashes) from volatile state (can be reconstructed). This is critical for correctness.

### 5.2 Helper Functions

```rust
impl RaftNode {
    /// Get the index of the last log entry (0 if log is empty)
    fn last_log_index(&self) -> usize {
        self.persistent.log.len()
    }
    
    /// Get the term of the last log entry (0 if log is empty)
    fn last_log_term(&self) -> u64 {
        self.persistent.log
            .last()
            .map(|entry| entry.term)
            .unwrap_or(0)
    }
    
    /// Get the term of a log entry at given index
    /// Returns 0 if index is 0 or out of bounds
    fn log_term_at(&self, index: usize) -> u64 {
        if index == 0 || index > self.persistent.log.len() {
            return 0;
        }
        self.persistent.log[index - 1].term
    }
    
    /// Check if candidate's log is at least as up-to-date as ours
    /// Used in RequestVote to ensure safety
    fn is_log_up_to_date(&self, last_log_index: usize, last_log_term: u64) -> bool {
        let my_last_term = self.last_log_term();
        let my_last_index = self.last_log_index();
        
        // Candidate's last entry has higher term → more up-to-date
        if last_log_term > my_last_term {
            return true;
        }
        
        // Same term → longer log is more up-to-date
        if last_log_term == my_last_term {
            return last_log_index >= my_last_index;
        }
        
        // Candidate's last entry has lower term → less up-to-date
        false
    }
    
    /// Generate random election timeout
    fn random_election_timeout() -> Duration {
        use rand::Rng;
        let mut rng = rand::thread_rng();
        Duration::from_millis(rng.gen_range(150..300))
    }
    
    /// Check if election timeout has elapsed
    fn election_timeout_elapsed(&self) -> bool {
        self.last_heartbeat.elapsed() >= self.election_timeout
    }
    
    /// Reset election timer (called when receiving heartbeat)
    fn reset_election_timer(&mut self) {
        self.last_heartbeat = Instant::now();
        self.election_timeout = Self::random_election_timeout();
    }
    
    /// Transition to follower state
    fn become_follower(&mut self, term: u64) {
        self.state = ServerState::Follower;
        self.persistent.current_term = term;
        self.persistent.voted_for = None;
        self.leader_state = None;
        self.reset_election_timer();
    }
    
    /// Transition to candidate state
    fn become_candidate(&mut self) {
        self.state = ServerState::Candidate;
        self.persistent.current_term += 1;
        self.persistent.voted_for = Some(self.id);
        self.leader_state = None;
        self.reset_election_timer();
    }
    
    /// Transition to leader state
    fn become_leader(&mut self) {
        self.state = ServerState::Leader;
        
        // Initialize leader state
        let next_index = self.last_log_index() + 1;
        let mut leader_state = LeaderState {
            next_index: HashMap::new(),
            match_index: HashMap::new(),
        };
        
        for &peer in &self.peers {
            if peer != self.id {
                leader_state.next_index.insert(peer, next_index);
                leader_state.match_index.insert(peer, 0);
            }
        }
        
        self.leader_state = Some(leader_state);
        
        // Send immediate heartbeats to establish authority
        self.send_heartbeats();
    }
}
```

### 5.3 RequestVote Implementation

```rust
impl RaftNode {
    /// Handle incoming RequestVote RPC
    pub fn handle_request_vote(
        &mut self,
        term: u64,
        candidate_id: u64,
        last_log_index: usize,
        last_log_term: u64,
    ) -> RequestVoteResponse {
        // Rule: If RPC request or response contains term T > currentTerm,
        // set currentTerm = T, convert to follower
        if term > self.persistent.current_term {
            self.become_follower(term);
        }
        
        let mut vote_granted = false;
        
        // Grant vote if:
        // 1. Candidate's term >= my term
        // 2. I haven't voted for anyone else this term (or voted for this candidate)
        // 3. Candidate's log is at least as up-to-date as mine
        if term >= self.persistent.current_term {
            let haven_voted_this_term = self.persistent.voted_for.is_none();
            let already_voted_for_candidate = self.persistent.voted_for == Some(candidate_id);
            let log_is_up_to_date = self.is_log_up_to_date(last_log_index, last_log_term);
            
            if (haven_voted_this_term || already_voted_for_candidate) && log_is_up_to_date {
                vote_granted = true;
                self.persistent.voted_for = Some(candidate_id);
                self.persistent.current_term = term;
                self.reset_election_timer();
            }
        }
        
        RequestVoteResponse {
            term: self.persistent.current_term,
            vote_granted,
        }
    }
    
    /// Start an election
    pub async fn start_election(&mut self) {
        self.become_candidate();
        
        let current_term = self.persistent.current_term;
        let candidate_id = self.id;
        let last_log_index = self.last_log_index();
        let last_log_term = self.last_log_term();
        
        // Vote for ourselves
        let mut votes_received = 1;
        let votes_needed = (self.peers.len() / 2) + 1;
        
        // Send RequestVote RPCs to all other servers
        let mut response_receivers = Vec::new();
        
        for &peer in &self.peers {
            if peer == self.id {
                continue;
            }
            
            if let Some(sender) = self.peer_channels.get(&peer) {
                let (response_tx, response_rx) = mpsc::unbounded_channel();
                
                let rpc = RaftRPC::RequestVote {
                    term: current_term,
                    candidate_id,
                    last_log_index,
                    last_log_term,
                    response_tx,
                };
                
                let _ = sender.send(rpc);
                response_receivers.push(response_rx);
            }
        }
        
        // Wait for responses
        for mut rx in response_receivers {
            if let Some(response) = rx.recv().await {
                // If we discover higher term, become follower
                if response.term > current_term {
                    self.become_follower(response.term);
                    return;
                }
                
                // Count votes
                if response.vote_granted {
                    votes_received += 1;
                    
                    // Won election?
                    if votes_received >= votes_needed {
                        self.become_leader();
                        return;
                    }
                }
            }
        }
        
        // Election timeout or didn't win → stay candidate, will retry
    }
}
```

### 5.4 AppendEntries Implementation

```rust
impl RaftNode {
    /// Handle incoming AppendEntries RPC
    pub fn handle_append_entries(
        &mut self,
        term: u64,
        leader_id: u64,
        prev_log_index: usize,
        prev_log_term: u64,
        entries: Vec<LogEntry>,
        leader_commit: usize,
    ) -> AppendEntriesResponse {
        // Reply false if term < currentTerm
        if term < self.persistent.current_term {
            return AppendEntriesResponse {
                term: self.persistent.current_term,
                success: false,
                match_index: 0,
            };
        }
        
        // If RPC contains higher term, update and become follower
        if term > self.persistent.current_term {
            self.become_follower(term);
        }
        
        // Reset election timer (we heard from valid leader)
        self.reset_election_timer();
        
        // If we're candidate and receive AppendEntries from valid leader, become follower
        if self.state == ServerState::Candidate {
            self.become_follower(term);
        }
        
        // Consistency check: Reply false if log doesn't contain an entry
        // at prevLogIndex whose term matches prevLogTerm
        if prev_log_index > 0 {
            if prev_log_index > self.persistent.log.len() {
                return AppendEntriesResponse {
                    term: self.persistent.current_term,
                    success: false,
                    match_index: self.last_log_index(),
                };
            }
            
            if self.log_term_at(prev_log_index) != prev_log_term {
                // Delete conflicting entry and all that follow
                self.persistent.log.truncate(prev_log_index - 1);
                
                return AppendEntriesResponse {
                    term: self.persistent.current_term,
                    success: false,
                    match_index: self.last_log_index(),
                };
            }
        }
        
        // Append new entries not already in the log
        let mut index = prev_log_index;
        for entry in entries {
            index += 1;
            
            if index <= self.persistent.log.len() {
                // If existing entry conflicts, delete it and all following
                if self.persistent.log[index - 1].term != entry.term {
                    self.persistent.log.truncate(index - 1);
                    self.persistent.log.push(entry);
                }
            } else {
                // Append any new entries
                self.persistent.log.push(entry);
            }
        }
        
        // Update commit index
        if leader_commit > self.volatile.commit_index {
            self.volatile.commit_index = std::cmp::min(leader_commit, self.last_log_index());
        }
        
        AppendEntriesResponse {
            term: self.persistent.current_term,
            success: true,
            match_index: self.last_log_index(),
        }
    }
    
    /// Send AppendEntries RPC to a specific peer (called by leader)
    pub async fn send_append_entries(&mut self, peer_id: u64) {
        if self.state != ServerState::Leader {
            return;
        }
        
        let leader_state = self.leader_state.as_mut().unwrap();
        let next_index = *leader_state.next_index.get(&peer_id).unwrap();
        
        let prev_log_index = next_index - 1;
        let prev_log_term = self.log_term_at(prev_log_index);
        
        // Get entries to send
        let entries: Vec<LogEntry> = self.persistent.log[next_index - 1..]
            .iter()
            .cloned()
            .collect();
        
        if let Some(sender) = self.peer_channels.get(&peer_id) {
            let (response_tx, mut response_rx) = mpsc::unbounded_channel();
            
            let rpc = RaftRPC::AppendEntries {
                term: self.persistent.current_term,
                leader_id: self.id,
                prev_log_index,
                prev_log_term,
                entries: entries.clone(),
                leader_commit: self.volatile.commit_index,
                response_tx,
            };
            
            let _ = sender.send(rpc);
            
            // Handle response
            if let Some(response) = response_rx.recv().await {
                // If response contains higher term, step down
                if response.term > self.persistent.current_term {
                    self.become_follower(response.term);
                    return;
                }
                
                if self.state != ServerState::Leader {
                    return;
                }
                
                let leader_state = self.leader_state.as_mut().unwrap();
                
                if response.success {
                    // Update nextIndex and matchIndex
                    leader_state.next_index.insert(peer_id, next_index + entries.len());
                    leader_state.match_index.insert(peer_id, response.match_index);
                    
                    // Check if we can advance commitIndex
                    self.advance_commit_index();
                } else {
                    // Decrement nextIndex and retry
                    let new_next = std::cmp::max(1, response.match_index + 1);
                    leader_state.next_index.insert(peer_id, new_next);
                }
            }
        }
    }
    
    /// Send heartbeats to all peers (empty AppendEntries)
    pub fn send_heartbeats(&mut self) {
        if self.state != ServerState::Leader {
            return;
        }
        
        for &peer in &self.peers {
            if peer != self.id {
                // In real implementation, spawn async task here
                // For now, this is a synchronous sketch
            }
        }
    }
    
    /// Advance commit index if possible
    fn advance_commit_index(&mut self) {
        if self.state != ServerState::Leader {
            return;
        }
        
        let leader_state = self.leader_state.as_ref().unwrap();
        
        // Find highest N such that majority of matchIndex[i] >= N
        // and log[N].term == currentTerm
        for n in (self.volatile.commit_index + 1..=self.last_log_index()).rev() {
            // Only commit entries from current term
            if self.log_term_at(n) != self.persistent.current_term {
                continue;
            }
            
            // Count how many servers have replicated this entry
            let mut count = 1; // Leader itself
            for &match_idx in leader_state.match_index.values() {
                if match_idx >= n {
                    count += 1;
                }
            }
            
            // Majority?
            if count > self.peers.len() / 2 {
                self.volatile.commit_index = n;
                break;
            }
        }
    }
}
```

### 5.5 Main Event Loop

```rust
impl RaftNode {
    /// Main event loop
    pub async fn run(&mut self) {
        let heartbeat_interval = Duration::from_millis(50);
        let mut heartbeat_timer = tokio::time::interval(heartbeat_interval);
        
        loop {
            tokio::select! {
                // Handle incoming RPCs
                Some(rpc) = self.rpc_rx.recv() => {
                    match rpc {
                        RaftRPC::RequestVote {
                            term,
                            candidate_id,
                            last_log_index,
                            last_log_term,
                            response_tx,
                        } => {
                            let response = self.handle_request_vote(
                                term,
                                candidate_id,
                                last_log_index,
                                last_log_term,
                            );
                            let _ = response_tx.send(response);
                        }
                        
                        RaftRPC::AppendEntries {
                            term,
                            leader_id,
                            prev_log_index,
                            prev_log_term,
                            entries,
                            leader_commit,
                            response_tx,
                        } => {
                            let response = self.handle_append_entries(
                                term,
                                leader_id,
                                prev_log_index,
                                prev_log_term,
                                entries,
                                leader_commit,
                            );
                            let _ = response_tx.send(response);
                        }
                        
                        _ => {}
                    }
                }
                
                // Leader: Send periodic heartbeats
                _ = heartbeat_timer.tick() => {
                    if self.state == ServerState::Leader {
                        self.send_heartbeats();
                    }
                }
                
                // Follower/Candidate: Check election timeout
                _ = tokio::time::sleep(Duration::from_millis(10)) => {
                    if self.state != ServerState::Leader && self.election_timeout_elapsed() {
                        self.start_election().await;
                    }
                }
            }
            
            // Apply committed entries to state machine
            self.apply_committed_entries();
        }
    }
    
    /// Apply committed but not yet applied entries
    fn apply_committed_entries(&mut self) {
        while self.volatile.last_applied < self.volatile.commit_index {
            self.volatile.last_applied += 1;
            let entry = &self.persistent.log[self.volatile.last_applied - 1];
            
            // Apply entry.command to state machine
            // (In real system, this would call a state machine interface)
            println!("Applied entry {}: {:?}", self.volatile.last_applied, entry.command);
        }
    }
}
```

---

## Part 6: Go Implementation

Now let's implement the same concepts in Go.

```go
// raft.go

package raft

import (
	"math/rand"
	"sync"
	"time"
)

// ServerState represents the state of a Raft server
type ServerState int

const (
	Follower ServerState = iota
	Candidate
	Leader
)

// LogEntry represents a single log entry
type LogEntry struct {
	Term    uint64
	Command []byte
}

// PersistentState holds state that must survive crashes
type PersistentState struct {
	CurrentTerm uint64      // Latest term server has seen
	VotedFor    *uint64     // CandidateId that received vote (nil if none)
	Log         []LogEntry  // Log entries
}

// VolatileState holds state that can be reconstructed
type VolatileState struct {
	CommitIndex uint64 // Index of highest log entry known to be committed
	LastApplied uint64 // Index of highest log entry applied to state machine
}

// LeaderState holds leader-specific volatile state
type LeaderState struct {
	NextIndex  map[uint64]uint64  // For each server, index of next log entry to send
	MatchIndex map[uint64]uint64  // For each server, index of highest known replicated entry
}

// RaftNode represents a Raft server
type RaftNode struct {
	mu sync.RWMutex
	
	ID    uint64    // This server's ID
	Peers []uint64  // All server IDs in cluster
	
	State       ServerState
	Persistent  PersistentState
	Volatile    VolatileState
	LeaderState *LeaderState
	
	LastHeartbeat   time.Time
	ElectionTimeout time.Duration
	
	// Channels
	rpcChan      chan RaftRPC
	shutdownChan chan struct{}
}

// RPC message types
type RequestVoteArgs struct {
	Term         uint64
	CandidateID  uint64
	LastLogIndex uint64
	LastLogTerm  uint64
}

type RequestVoteReply struct {
	Term        uint64
	VoteGranted bool
}

type AppendEntriesArgs struct {
	Term         uint64
	LeaderID     uint64
	PrevLogIndex uint64
	PrevLogTerm  uint64
	Entries      []LogEntry
	LeaderCommit uint64
}

type AppendEntriesReply struct {
	Term       uint64
	Success    bool
	MatchIndex uint64
}

type RaftRPC interface {
	// Marker interface
}

// Helper functions
func (rn *RaftNode) lastLogIndex() uint64 {
	return uint64(len(rn.Persistent.Log))
}

func (rn *RaftNode) lastLogTerm() uint64 {
	if len(rn.Persistent.Log) == 0 {
		return 0
	}
	return rn.Persistent.Log[len(rn.Persistent.Log)-1].Term
}

func (rn *RaftNode) logTermAt(index uint64) uint64 {
	if index == 0 || index > uint64(len(rn.Persistent.Log)) {
		return 0
	}
	return rn.Persistent.Log[index-1].Term
}

func (rn *RaftNode) isLogUpToDate(lastLogIndex, lastLogTerm uint64) bool {
	myLastTerm := rn.lastLogTerm()
	myLastIndex := rn.lastLogIndex()
	
	if lastLogTerm > myLastTerm {
		return true
	}
	
	if lastLogTerm == myLastTerm {
		return lastLogIndex >= myLastIndex
	}
	
	return false
}

func randomElectionTimeout() time.Duration {
	return time.Duration(150+rand.Intn(150)) * time.Millisecond
}

func (rn *RaftNode) electionTimeoutElapsed() bool {
	return time.Since(rn.LastHeartbeat) >= rn.ElectionTimeout
}

func (rn *RaftNode) resetElectionTimer() {
	rn.LastHeartbeat = time.Now()
	rn.ElectionTimeout = randomElectionTimeout()
}

// State transitions
func (rn *RaftNode) becomeFollower(term uint64) {
	rn.State = Follower
	rn.Persistent.CurrentTerm = term
	rn.Persistent.VotedFor = nil
	rn.LeaderState = nil
	rn.resetElectionTimer()
}

func (rn *RaftNode) becomeCandidate() {
	rn.State = Candidate
	rn.Persistent.CurrentTerm++
	myID := rn.ID
	rn.Persistent.VotedFor = &myID
	rn.LeaderState = nil
	rn.resetElectionTimer()
}

func (rn *RaftNode) becomeLeader() {
	rn.State = Leader
	
	// Initialize leader state
	nextIndex := rn.lastLogIndex() + 1
	leaderState := &LeaderState{
		NextIndex:  make(map[uint64]uint64),
		MatchIndex: make(map[uint64]uint64),
	}
	
	for _, peer := range rn.Peers {
		if peer != rn.ID {
			leaderState.NextIndex[peer] = nextIndex
			leaderState.MatchIndex[peer] = 0
		}
	}
	
	rn.LeaderState = leaderState
	
	// Send immediate heartbeats
	rn.sendHeartbeats()
}

// RequestVote RPC handler
func (rn *RaftNode) HandleRequestVote(args *RequestVoteArgs) *RequestVoteReply {
	rn.mu.Lock()
	defer rn.mu.Unlock()
	
	reply := &RequestVoteReply{
		Term:        rn.Persistent.CurrentTerm,
		VoteGranted: false,
	}
	
	// If RPC contains higher term, update and become follower
	if args.Term > rn.Persistent.CurrentTerm {
		rn.becomeFollower(args.Term)
	}
	
	// Grant vote if:
	// 1. Candidate's term >= my term
	// 2. Haven't voted or already voted for this candidate
	// 3. Candidate's log is at least as up-to-date
	if args.Term >= rn.Persistent.CurrentTerm {
		haventVoted := rn.Persistent.VotedFor == nil
		votedForCandidate := rn.Persistent.VotedFor != nil && *rn.Persistent.VotedFor == args.CandidateID
		logUpToDate := rn.isLogUpToDate(args.LastLogIndex, args.LastLogTerm)
		
		if (haventVoted || votedForCandidate) && logUpToDate {
			reply.VoteGranted = true
			rn.Persistent.VotedFor = &args.CandidateID
			rn.Persistent.CurrentTerm = args.Term
			rn.resetElectionTimer()
		}
	}
	
	reply.Term = rn.Persistent.CurrentTerm
	return reply
}

// StartElection initiates an election
func (rn *RaftNode) StartElection() {
	rn.mu.Lock()
	rn.becomeCandidate()
	
	currentTerm := rn.Persistent.CurrentTerm
	candidateID := rn.ID
	lastLogIndex := rn.lastLogIndex()
	lastLogTerm := rn.lastLogTerm()
	rn.mu.Unlock()
	
	votesReceived := 1 // Vote for self
	votesNeeded := len(rn.Peers)/2 + 1
	
	var voteMu sync.Mutex
	
	// Send RequestVote RPCs to all peers
	for _, peer := range rn.Peers {
		if peer == rn.ID {
			continue
		}
		
		go func(peerID uint64) {
			args := &RequestVoteArgs{
				Term:         currentTerm,
				CandidateID:  candidateID,
				LastLogIndex: lastLogIndex,
				LastLogTerm:  lastLogTerm,
			}
			
			reply := &RequestVoteReply{}
			
			// Send RPC (would use network in real implementation)
			// reply = sendRequestVoteRPC(peerID, args)
			
			rn.mu.Lock()
			defer rn.mu.Unlock()
			
			// Check if we're still candidate for this term
			if rn.State != Candidate || rn.Persistent.CurrentTerm != currentTerm {
				return
			}
			
			// If we discover higher term, become follower
			if reply.Term > currentTerm {
				rn.becomeFollower(reply.Term)
				return
			}
			
			// Count vote
			if reply.VoteGranted {
				voteMu.Lock()
				votesReceived++
				votes := votesReceived
				voteMu.Unlock()
				
				// Won election?
				if votes >= votesNeeded {
					rn.becomeLeader()
				}
			}
		}(peer)
	}
}

// AppendEntries RPC handler
func (rn *RaftNode) HandleAppendEntries(args *AppendEntriesArgs) *AppendEntriesReply {
	rn.mu.Lock()
	defer rn.mu.Unlock()
	
	reply := &AppendEntriesReply{
		Term:    rn.Persistent.CurrentTerm,
		Success: false,
	}
	
	// Reply false if term < currentTerm
	if args.Term < rn.Persistent.CurrentTerm {
		return reply
	}
	
	// Update term and become follower if necessary
	if args.Term > rn.Persistent.CurrentTerm {
		rn.becomeFollower(args.Term)
	}
	
	rn.resetElectionTimer()
	
	// If candidate, step down
	if rn.State == Candidate {
		rn.becomeFollower(args.Term)
	}
	
	// Consistency check
	if args.PrevLogIndex > 0 {
		if args.PrevLogIndex > rn.lastLogIndex() {
			reply.MatchIndex = rn.lastLogIndex()
			return reply
		}
		
		if rn.logTermAt(args.PrevLogIndex) != args.PrevLogTerm {
			// Delete conflicting entries
			rn.Persistent.Log = rn.Persistent.Log[:args.PrevLogIndex-1]
			reply.MatchIndex = rn.lastLogIndex()
			return reply
		}
	}
	
	// Append new entries
	index := args.PrevLogIndex
	for _, entry := range args.Entries {
		index++
		
		if index <= rn.lastLogIndex() {
			// Check for conflict
			if rn.Persistent.Log[index-1].Term != entry.Term {
				rn.Persistent.Log = rn.Persistent.Log[:index-1]
				rn.Persistent.Log = append(rn.Persistent.Log, entry)
			}
		} else {
			rn.Persistent.Log = append(rn.Persistent.Log, entry)
		}
	}
	
	// Update commit index
	if args.LeaderCommit > rn.Volatile.CommitIndex {
		rn.Volatile.CommitIndex = min(args.LeaderCommit, rn.lastLogIndex())
	}
	
	reply.Success = true
	reply.MatchIndex = rn.lastLogIndex()
	reply.Term = rn.Persistent.CurrentTerm
	return reply
}

func min(a, b uint64) uint64 {
	if a < b {
		return a
	}
	return b
}

func max(a, b uint64) uint64 {
	if a > b {
		return a
	}
	return b
}

// sendHeartbeats sends empty AppendEntries to all peers
func (rn *RaftNode) sendHeartbeats() {
	for _, peer := range rn.Peers {
		if peer == rn.ID {
			continue
		}
		
		go rn.sendAppendEntries(peer)
	}
}

// sendAppendEntries sends AppendEntries RPC to a peer
func (rn *RaftNode) sendAppendEntries(peerID uint64) {
	rn.mu.Lock()
	
	if rn.State != Leader {
		rn.mu.Unlock()
		return
	}
	
	nextIndex := rn.LeaderState.NextIndex[peerID]
	prevLogIndex := nextIndex - 1
	prevLogTerm := rn.logTermAt(prevLogIndex)
	
	var entries []LogEntry
	if nextIndex <= rn.lastLogIndex() {
		entries = rn.Persistent.Log[nextIndex-1:]
	}
	
	args := &AppendEntriesArgs{
		Term:         rn.Persistent.CurrentTerm,
		LeaderID:     rn.ID,
		PrevLogIndex: prevLogIndex,
		PrevLogTerm:  prevLogTerm,
		Entries:      entries,
		LeaderCommit: rn.Volatile.CommitIndex,
	}
	
	currentTerm := rn.Persistent.CurrentTerm
	rn.mu.Unlock()
	
	reply := &AppendEntriesReply{}
	
	// Send RPC (would use network in real implementation)
	// reply = sendAppendEntriesRPC(peerID, args)
	
	rn.mu.Lock()
	defer rn.mu.Unlock()
	
	// Check if we're still leader for this term
	if rn.State != Leader || rn.Persistent.CurrentTerm != currentTerm {
		return
	}
	
	// If response contains higher term, step down
	if reply.Term > rn.Persistent.CurrentTerm {
		rn.becomeFollower(reply.Term)
		return
	}
	
	if reply.Success {
		// Update nextIndex and matchIndex
		rn.LeaderState.NextIndex[peerID] = nextIndex + uint64(len(entries))
		rn.LeaderState.MatchIndex[peerID] = reply.MatchIndex
		
		// Try to advance commit index
		rn.advanceCommitIndex()
	} else {
		// Decrement nextIndex and retry
		rn.LeaderState.NextIndex[peerID] = max(1, reply.MatchIndex+1)
	}
}

// advanceCommitIndex tries to advance the commit index
func (rn *RaftNode) advanceCommitIndex() {
	if rn.State != Leader {
		return
	}
	
	// Find highest N such that majority of matchIndex[i] >= N
	// and log[N].term == currentTerm
	for n := rn.lastLogIndex(); n > rn.Volatile.CommitIndex; n-- {
		// Only commit entries from current term
		if rn.logTermAt(n) != rn.Persistent.CurrentTerm {
			continue
		}
		
		// Count replicas
		count := 1 // Leader itself
		for _, matchIdx := range rn.LeaderState.MatchIndex {
			if matchIdx >= n {
				count++
			}
		}
		
		// Majority?
		if count > len(rn.Peers)/2 {
			rn.Volatile.CommitIndex = n
			break
		}
	}
}

// Run is the main event loop
func (rn *RaftNode) Run() {
	heartbeatTicker := time.NewTicker(50 * time.Millisecond)
	defer heartbeatTicker.Stop()
	
	for {
		select {
		case <-rn.shutdownChan:
			return
			
		case <-heartbeatTicker.C:
			rn.mu.Lock()
			if rn.State == Leader {
				rn.sendHeartbeats()
			}
			rn.mu.Unlock()
			
		default:
			rn.mu.Lock()
			if rn.State != Leader && rn.electionTimeoutElapsed() {
				rn.mu.Unlock()
				rn.StartElection()
			} else {
				rn.mu.Unlock()
			}
			
			time.Sleep(10 * time.Millisecond)
		}
		
		// Apply committed entries
		rn.applyCommittedEntries()
	}
}

func (rn *RaftNode) applyCommittedEntries() {
	rn.mu.Lock()
	defer rn.mu.Unlock()
	
	for rn.Volatile.LastApplied < rn.Volatile.CommitIndex {
		rn.Volatile.LastApplied++
		entry := rn.Persistent.Log[rn.Volatile.LastApplied-1]
		
		// Apply to state machine
		_ = entry // Would call state machine here
	}
}
```

---

## Part 7: C Implementation

Finally, let's implement in C (focusing on core structures and key functions).

```c
// raft.h

#ifndef RAFT_H
#define RAFT_H

#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include <pthread.h>

#define MAX_PEERS 10
#define MAX_LOG_ENTRIES 10000

typedef enum {
    STATE_FOLLOWER,
    STATE_CANDIDATE,
    STATE_LEADER
} server_state_t;

typedef struct {
    uint64_t term;
    uint8_t *command;
    size_t command_len;
} log_entry_t;

typedef struct {
    uint64_t current_term;
    uint64_t voted_for;  // UINT64_MAX if haven't voted
    bool has_voted;
    
    log_entry_t *log;
    size_t log_size;
    size_t log_capacity;
} persistent_state_t;

typedef struct {
    uint64_t commit_index;
    uint64_t last_applied;
} volatile_state_t;

typedef struct {
    uint64_t next_index[MAX_PEERS];
    uint64_t match_index[MAX_PEERS];
} leader_state_t;

typedef struct {
    uint64_t id;
    uint64_t peers[MAX_PEERS];
    size_t num_peers;
    
    server_state_t state;
    
    persistent_state_t persistent;
    volatile_state_t volatile_state;
    leader_state_t leader_state;
    bool is_leader;
    
    struct timespec last_heartbeat;
    uint64_t election_timeout_ms;
    
    pthread_mutex_t lock;
} raft_node_t;

// RPC structures
typedef struct {
    uint64_t term;
    uint64_t candidate_id;
    uint64_t last_log_index;
    uint64_t last_log_term;
} request_vote_args_t;

typedef struct {
    uint64_t term;
    bool vote_granted;
} request_vote_reply_t;

typedef struct {
    uint64_t term;
    uint64_t leader_id;
    uint64_t prev_log_index;
    uint64_t prev_log_term;
    log_entry_t *entries;
    size_t entries_len;
    uint64_t leader_commit;
} append_entries_args_t;

typedef struct {
    uint64_t term;
    bool success;
    uint64_t match_index;
} append_entries_reply_t;

// Function declarations
void raft_node_init(raft_node_t *node, uint64_t id, uint64_t *peers, size_t num_peers);
void raft_node_destroy(raft_node_t *node);

uint64_t last_log_index(raft_node_t *node);
uint64_t last_log_term(raft_node_t *node);
uint64_t log_term_at(raft_node_t *node, uint64_t index);
bool is_log_up_to_date(raft_node_t *node, uint64_t last_log_index, uint64_t last_log_term);

void become_follower(raft_node_t *node, uint64_t term);
void become_candidate(raft_node_t *node);
void become_leader(raft_node_t *node);

void handle_request_vote(raft_node_t *node, request_vote_args_t *args, request_vote_reply_t *reply);
void handle_append_entries(raft_node_t *node, append_entries_args_t *args, append_entries_reply_t *reply);

void start_election(raft_node_t *node);
void send_heartbeats(raft_node_t *node);
void advance_commit_index(raft_node_t *node);

#endif // RAFT_H
```

```c
// raft.c

#include "raft.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static uint64_t random_election_timeout() {
    return 150 + (rand() % 150); // 150-300ms
}

static uint64_t timespec_to_ms(struct timespec *ts) {
    return ts->tv_sec * 1000 + ts->tv_nsec / 1000000;
}

static bool election_timeout_elapsed(raft_node_t *node) {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    
    uint64_t last_ms = timespec_to_ms(&node->last_heartbeat);
    uint64_t now_ms = timespec_to_ms(&now);
    
    return (now_ms - last_ms) >= node->election_timeout_ms;
}

static void reset_election_timer(raft_node_t *node) {
    clock_gettime(CLOCK_MONOTONIC, &node->last_heartbeat);
    node->election_timeout_ms = random_election_timeout();
}

void raft_node_init(raft_node_t *node, uint64_t id, uint64_t *peers, size_t num_peers) {
    memset(node, 0, sizeof(raft_node_t));
    
    node->id = id;
    node->num_peers = num_peers;
    memcpy(node->peers, peers, num_peers * sizeof(uint64_t));
    
    node->state = STATE_FOLLOWER;
    
    // Initialize persistent state
    node->persistent.current_term = 0;
    node->persistent.voted_for = UINT64_MAX;
    node->persistent.has_voted = false;
    node->persistent.log_capacity = 1024;
    node->persistent.log = malloc(node->persistent.log_capacity * sizeof(log_entry_t));
    node->persistent.log_size = 0;
    
    // Initialize volatile state
    node->volatile_state.commit_index = 0;
    node->volatile_state.last_applied = 0;
    
    node->is_leader = false;
    
    reset_election_timer(node);
    
    pthread_mutex_init(&node->lock, NULL);
}

void raft_node_destroy(raft_node_t *node) {
    free(node->persistent.log);
    pthread_mutex_destroy(&node->lock);
}

uint64_t last_log_index(raft_node_t *node) {
    return node->persistent.log_size;
}

uint64_t last_log_term(raft_node_t *node) {
    if (node->persistent.log_size == 0) {
        return 0;
    }
    return node->persistent.log[node->persistent.log_size - 1].term;
}

uint64_t log_term_at(raft_node_t *node, uint64_t index) {
    if (index == 0 || index > node->persistent.log_size) {
        return 0;
    }
    return node->persistent.log[index - 1].term;
}

bool is_log_up_to_date(raft_node_t *node, uint64_t candidate_last_index, uint64_t candidate_last_term) {
    uint64_t my_last_term = last_log_term(node);
    uint64_t my_last_index = last_log_index(node);
    
    if (candidate_last_term > my_last_term) {
        return true;
    }
    
    if (candidate_last_term == my_last_term) {
        return candidate_last_index >= my_last_index;
    }
    
    return false;
}

void become_follower(raft_node_t *node, uint64_t term) {
    node->state = STATE_FOLLOWER;
    node->persistent.current_term = term;
    node->persistent.voted_for = UINT64_MAX;
    node->persistent.has_voted = false;
    node->is_leader = false;
    reset_election_timer(node);
}

void become_candidate(raft_node_t *node) {
    node->state = STATE_CANDIDATE;
    node->persistent.current_term++;
    node->persistent.voted_for = node->id;
    node->persistent.has_voted = true;
    node->is_leader = false;
    reset_election_timer(node);
}

void become_leader(raft_node_t *node) {
    node->state = STATE_LEADER;
    node->is_leader = true;
    
    // Initialize leader state
    uint64_t next_index = last_log_index(node) + 1;
    for (size_t i = 0; i < node->num_peers; i++) {
        node->leader_state.next_index[i] = next_index;
        node->leader_state.match_index[i] = 0;
    }
    
    send_heartbeats(node);
}

void handle_request_vote(raft_node_t *node, request_vote_args_t *args, request_vote_reply_t *reply) {
    pthread_mutex_lock(&node->lock);
    
    reply->term = node->persistent.current_term;
    reply->vote_granted = false;
    
    // Update term if necessary
    if (args->term > node->persistent.current_term) {
        become_follower(node, args->term);
    }
    
    // Grant vote logic
    if (args->term >= node->persistent.current_term) {
        bool havent_voted = !node->persistent.has_voted;
        bool voted_for_candidate = node->persistent.has_voted && 
                                   node->persistent.voted_for == args->candidate_id;
        bool log_up_to_date = is_log_up_to_date(node, args->last_log_index, args->last_log_term);
        
        if ((havent_voted || voted_for_candidate) && log_up_to_date) {
            reply->vote_granted = true;
            node->persistent.voted_for = args->candidate_id;
            node->persistent.has_voted = true;
            node->persistent.current_term = args->term;
            reset_election_timer(node);
        }
    }
    
    reply->term = node->persistent.current_term;
    
    pthread_mutex_unlock(&node->lock);
}

void handle_append_entries(raft_node_t *node, append_entries_args_t *args, append_entries_reply_t *reply) {
    pthread_mutex_lock(&node->lock);
    
    reply->term = node->persistent.current_term;
    reply->success = false;
    reply->match_index = 0;
    
    // Reply false if term < currentTerm
    if (args->term < node->persistent.current_term) {
        pthread_mutex_unlock(&node->lock);
        return;
    }
    
    // Update term if necessary
    if (args->term > node->persistent.current_term) {
        become_follower(node, args->term);
    }
    
    reset_election_timer(node);
    
    // If candidate, step down
    if (node->state == STATE_CANDIDATE) {
        become_follower(node, args->term);
    }
    
    // Consistency check
    if (args->prev_log_index > 0) {
        if (args->prev_log_index > last_log_index(node)) {
            reply->match_index = last_log_index(node);
            pthread_mutex_unlock(&node->lock);
            return;
        }
        
        if (log_term_at(node, args->prev_log_index) != args->prev_log_term) {
            // Delete conflicting entries
            node->persistent.log_size = args->prev_log_index - 1;
            reply->match_index = last_log_index(node);
            pthread_mutex_unlock(&node->lock);
            return;
        }
    }
    
    // Append new entries
    uint64_t index = args->prev_log_index;
    for (size_t i = 0; i < args->entries_len; i++) {
        index++;
        
        if (index <= node->persistent.log_size) {
            // Check for conflict
            if (node->persistent.log[index - 1].term != args->entries[i].term) {
                node->persistent.log_size = index - 1;
                node->persistent.log[node->persistent.log_size++] = args->entries[i];
            }
        } else {
            // Append new entry
            node->persistent.log[node->persistent.log_size++] = args->entries[i];
        }
    }
    
    // Update commit index
    if (args->leader_commit > node->volatile_state.commit_index) {
        uint64_t last_new_entry = last_log_index(node);
        node->volatile_state.commit_index = 
            (args->leader_commit < last_new_entry) ? args->leader_commit : last_new_entry;
    }
    
    reply->success = true;
    reply->match_index = last_log_index(node);
    reply->term = node->persistent.current_term;
    
    pthread_mutex_unlock(&node->lock);
}

void start_election(raft_node_t *node) {
    pthread_mutex_lock(&node->lock);
    
    become_candidate(node);
    
    uint64_t current_term = node->persistent.current_term;
    uint64_t candidate_id = node->id;
    uint64_t my_last_log_index = last_log_index(node);
    uint64_t my_last_log_term = last_log_term(node);
    
    pthread_mutex_unlock(&node->lock);
    
    int votes_received = 1; // Vote for self
    int votes_needed = (node->num_peers / 2) + 1;
    
    // In real implementation, send RequestVote RPCs to all peers
    // and collect votes
    
    printf("Node %lu starting election for term %lu\n", node->id, current_term);
}

void send_heartbeats(raft_node_t *node) {
    if (node->state != STATE_LEADER) {
        return;
    }
    
    // In real implementation, send AppendEntries RPCs to all peers
    printf("Leader %lu sending heartbeats\n", node->id);
}

void advance_commit_index(raft_node_t *node) {
    if (node->state != STATE_LEADER) {
        return;
    }
    
    // Find highest N such that majority of matchIndex[i] >= N
    for (uint64_t n = last_log_index(node); n > node->volatile_state.commit_index; n--) {
        // Only commit entries from current term
        if (log_term_at(node, n) != node->persistent.current_term) {
            continue;
        }
        
        // Count replicas
        int count = 1; // Leader itself
        for (size_t i = 0; i < node->num_peers; i++) {
            if (node->leader_state.match_index[i] >= n) {
                count++;
            }
        }
        
        // Majority?
        if (count > (int)(node->num_peers / 2)) {
            node->volatile_state.commit_index = n;
            break;
        }
    }
}
```

---

## Part 8: Advanced Topics & Optimizations

### 8.1 Log Compaction (Snapshotting)

**Problem**: Log grows unbounded.

**Solution**: Take snapshots of state machine, discard old log entries.

```
Before snapshot:
Log: [1][2][3][4][5][6][7][8][9][10]

After snapshot (snapshot up to index 7):
Snapshot: {state at index 7}
Log: [8][9][10]
```

**InstallSnapshot RPC**: Leader sends snapshot to followers who are too far behind.

### 8.2 Membership Changes

**Challenge**: Changing cluster configuration (adding/removing servers) safely.

**Raft's approach**: Two-phase protocol using **joint consensus**.

**Flow**:
```
C_old → C_old,new (joint consensus) → C_new
```

During joint consensus, both old and new configurations must agree.

### 8.3 Performance Optimizations

**1. Batching**: Group multiple client requests into single AppendEntries RPC.

**2. Pipelining**: Don't wait for response before sending next AppendEntries.

**3. Parallel RPCs**: Send to all followers simultaneously.

**4. Fast log backtracking**: Instead of decrementing nextIndex one at a time:
```rust
// Follower returns in AppendEntries response:
struct ConflictInfo {
    conflict_term: u64,        // Term of conflicting entry
    first_index: usize,        // First entry with that term
}

// Leader uses this to jump back to start of conflicting term
```

---

## Part 9: Correctness Reasoning & Proof Sketches

### 9.1 Election Safety

**Property**: At most one leader per term.

**Proof**:
1. To win, candidate needs majority votes
2. Each server votes for at most one candidate per term
3. Two different candidates can't both get majority (pigeonhole principle)
4. Therefore, at most one leader per term ∎

### 9.2 Leader Append-Only

**Property**: Leader never overwrites or deletes entries in its log.

**Proof**: By inspection of algorithm - leader only appends entries ∎

### 9.3 Log Matching

**Property**: If two logs contain entry with same index and term, then:
1. Entries are identical
2. All preceding entries are identical

**Proof**:
1. Leader creates at most one entry per index per term
2. Entries never change position
3. AppendEntries consistency check ensures prefix matches
4. Therefore, property holds inductively ∎

### 9.4 Leader Completeness

**Property**: If entry committed in term T, it appears in all future leaders' logs.

**Proof** (sketch):
1. Entry committed → replicated on majority in term T
2. Future leader must win election
3. To win, must receive votes from majority
4. These majorities overlap → at least one voter has entry
5. RequestVote only grants if candidate's log ≥ voter's log
6. Therefore, winner must have entry ∎

---

## Part 10: Testing & Debugging Strategies

### Mental Models for Testing

**1. Partition Tolerance**: Test with network partitions
```
Scenario: Leader gets isolated
[L] | [F][F][F][F]  ← Old leader can't reach majority
    
New election happens on right side
[F] | [L'][F][F][F]  ← New leader elected
```

**2. Crash Recovery**: Kill and restart servers randomly

**3. Message Delays/Reordering**: Inject random delays

**4. Byzantine Failures**: Some servers send contradictory messages (Raft doesn't handle this, but test for it)

### Debugging Techniques

**1. Logging**: Log every state transition and RPC
```
[T=5][Node-2][FOLLOWER] Received AppendEntries from 1, prevIndex=3, entries=1
[T=5][Node-2][FOLLOWER] Appended entry 4, commitIndex=4
```

**2. Visualization**: Build visual debugger showing cluster state

**3. Invariant Checking**: Assert invariants after every operation
```rust
fn check_invariants(&self) {
    // No two servers think they're leader for same term
    // Committed entries never disappear
    // Log matching property holds
}
```

---

## Final Wisdom: The Raft Philosophy

**Why Raft succeeds where Paxos struggles**:
1. **Understandability**: Decomposed into leader election, log replication, safety
2. **Strong leader**: Simplifies reasoning (log flows in one direction)
3. **Randomized timeouts**: Elegant solution to split votes

**Mental framework for distributed consensus**:
```
The Three Challenges:
1. Agreement: All correct servers agree on same value
2. Validity: Agreed value was proposed by some server
3. Termination: All correct servers eventually decide

Raft's answers:
1. Agreement: Via majority voting and log matching
2. Validity: Leader only replicates client commands
3. Termination: Via randomized election timeouts
```

**Deep insight**: Raft trades some performance for understandability. In production systems (etcd, Consul), this trade-off is worth it.

---

You now have a complete mental model of Raft, implementations in three languages, and the reasoning tools to master distributed consensus. Practice implementing these concepts, test with failures, and you'll develop the intuition of a distributed systems expert.

*Continue?* Ask about specific topics (membership changes, optimizations, etcd internals) or request harder problems to test your understanding.