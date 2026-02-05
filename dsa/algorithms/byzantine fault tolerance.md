# Byzantine Fault Tolerance (BFT) Algorithms: A Comprehensive Guide

## Foundation: Understanding the Byzantine Generals Problem

Before we dive into algorithms, let's build the conceptual foundation.

### What is a "Byzantine Fault"?

Imagine you're coordinating with others, but some participants might:
- Send contradictory information to different people
- Lie about what they received
- Simply fail to respond
- Act maliciously or unpredictably

A **Byzantine fault** is any behavior where a component (node/process) can behave arbitrarily — including appearing functional to some while being broken to others.

### The Byzantine Generals Problem (1982)

**Scenario**: Several generals surround a city. They must coordinate to either **attack** or **retreat**. They communicate via messengers, but some generals might be **traitors** who send different messages to different generals.

**Goal**: All loyal generals must agree on the same plan, and this plan should be reasonable (if the commander is loyal, all loyal generals follow their order).

**Core Challenge**: How do you achieve consensus when you can't trust everyone?

---

## Mental Model: The Three Pillars of BFT

```
┌─────────────────────────────────────────────────┐
│         Byzantine Fault Tolerance               │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│  │   Safety     │  │  Liveness    │  │Validity││
│  │              │  │              │  │        ││
│  │ All honest   │  │ System makes │  │ Output ││
│  │ nodes agree  │  │ progress &   │  │ comes  ││
│  │ on the same  │  │ eventually   │  │ from   ││
│  │ value        │  │ decides      │  │ honest ││
│  │              │  │              │  │ inputs ││
│  └──────────────┘  └──────────────┘  └────────┘│
│                                                 │
└─────────────────────────────────────────────────┘
```

**Safety**: No two honest nodes decide differently
**Liveness**: The system eventually makes a decision
**Validity**: If all honest nodes propose the same value, that's what's decided

---

## Fundamental Theorem: The n > 3f Rule

**Theorem**: To tolerate `f` Byzantine faults, you need at least `n = 3f + 1` total nodes.

**Why?**

```
Total nodes: n
Faulty nodes: f
Honest nodes: n - f

For consensus:
- You need a majority to override Byzantine nodes
- Byzantine nodes can lie to split the network
- You need enough honest nodes to:
  1. Form a majority even when f nodes are silent
  2. Detect inconsistencies when f nodes lie

Minimum: n = 3f + 1
Example: f=1 → need n≥4 nodes
         f=2 → need n≥7 nodes
```

---

## Core BFT Algorithms: A Taxonomy

```
                    BFT Algorithms
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
   Synchronous                         Asynchronous
   (bounded delay)                    (unbounded delay)
        │                                   │
   ┌────┴────┐                         ┌────┴────┐
   │         │                         │         │
 PBFT    Tendermint               HoneyBadger  Algorand
```

**Synchronous**: Messages arrive within a known time bound
**Asynchronous**: Messages can be delayed arbitrarily (more realistic)

---

## Algorithm 1: Practical Byzantine Fault Tolerance (PBFT)

### Conceptual Flow

PBFT operates in **views** (epochs with a designated leader called **primary**).

**Key Terms:**
- **Primary**: The current leader proposing values
- **Replica**: A participating node
- **View**: An epoch with a specific primary
- **Sequence number**: Unique ID for each request
- **Quorum**: A set of 2f+1 nodes (ensures at least f+1 honest)

### Protocol Phases

```
┌─────────────────────────────────────────────────────┐
│                    PBFT Phases                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Client                                             │
│    │                                                │
│    │ REQUEST                                        │
│    └──────────────┐                                 │
│                   ▼                                 │
│              ┌─────────┐                            │
│              │ Primary │                            │
│              └────┬────┘                            │
│                   │ PRE-PREPARE (sequence request)  │
│                   ▼                                 │
│         ┌────────────────────┐                      │
│         │ All Replicas       │                      │
│         └─────────┬──────────┘                      │
│                   │ PREPARE (2f msgs needed)        │
│                   ▼                                 │
│         ┌────────────────────┐                      │
│         │ Prepared State     │                      │
│         └─────────┬──────────┘                      │
│                   │ COMMIT (2f msgs needed)         │
│                   ▼                                 │
│         ┌────────────────────┐                      │
│         │ Committed State    │                      │
│         └─────────┬──────────┘                      │
│                   │ REPLY                           │
│                   ▼                                 │
│              Client (waits for f+1 replies)         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Implementation in Rust

```rust
use std::collections::{HashMap, HashSet};
use serde::{Serialize, Deserialize};

/// Core message types in PBFT protocol
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
enum MessageType {
    Request,
    PrePrepare,
    Prepare,
    Commit,
    Reply,
    ViewChange,
}

/// A cryptographic digest (simplified as String for demonstration)
/// In production: use SHA-256 or similar
type Digest = String;

/// Unique identifier for each node/replica
type ReplicaId = usize;

/// View number (epoch)
type ViewNumber = u64;

/// Sequence number for ordering requests
type SequenceNumber = u64;

/// Core PBFT message structure
#[derive(Debug, Clone, Serialize, Deserialize)]
struct PBFTMessage {
    msg_type: MessageType,
    view: ViewNumber,
    sequence: SequenceNumber,
    digest: Digest,
    replica_id: ReplicaId,
    // Simplified: in production, include cryptographic signatures
}

/// Request from client
#[derive(Debug, Clone, Serialize, Deserialize)]
struct ClientRequest {
    operation: String,  // The actual operation to perform
    timestamp: u64,
    client_id: String,
}

/// State of a replica in the PBFT network
struct PBFTReplica {
    id: ReplicaId,
    view: ViewNumber,
    sequence: SequenceNumber,
    
    // Total number of replicas
    n: usize,
    
    // Maximum number of faulty replicas (n = 3f + 1)
    f: usize,
    
    // Current primary replica id (view % n)
    primary_id: ReplicaId,
    
    // Message logs
    pre_prepare_log: HashMap<(ViewNumber, SequenceNumber), PBFTMessage>,
    prepare_log: HashMap<(ViewNumber, SequenceNumber), HashSet<PBFTMessage>>,
    commit_log: HashMap<(ViewNumber, SequenceNumber), HashSet<PBFTMessage>>,
    
    // Execution state
    executed_requests: HashSet<SequenceNumber>,
    
    // Request queue
    pending_requests: Vec<ClientRequest>,
}

impl PBFTReplica {
    /// Create a new PBFT replica
    fn new(id: ReplicaId, n: usize) -> Self {
        // Calculate f from n = 3f + 1
        assert!(n >= 4, "Need at least 4 replicas (f=1)");
        let f = (n - 1) / 3;
        
        PBFTReplica {
            id,
            view: 0,
            sequence: 0,
            n,
            f,
            primary_id: 0, // Primary in view 0 is replica 0
            pre_prepare_log: HashMap::new(),
            prepare_log: HashMap::new(),
            commit_log: HashMap::new(),
            executed_requests: HashSet::new(),
            pending_requests: Vec::new(),
        }
    }
    
    /// Check if this replica is the current primary
    fn is_primary(&self) -> bool {
        self.id == self.primary_id
    }
    
    /// Calculate digest of a request (simplified)
    fn digest(request: &ClientRequest) -> Digest {
        // In production: use cryptographic hash
        format!("{:?}", request)
    }
    
    /// Handle incoming client request (Primary only)
    fn handle_client_request(&mut self, request: ClientRequest) -> Option<PBFTMessage> {
        if !self.is_primary() {
            // Forward to primary or queue
            self.pending_requests.push(request);
            return None;
        }
        
        // Assign sequence number
        self.sequence += 1;
        let digest = Self::digest(&request);
        
        // Create PRE-PREPARE message
        let pre_prepare = PBFTMessage {
            msg_type: MessageType::PrePrepare,
            view: self.view,
            sequence: self.sequence,
            digest: digest.clone(),
            replica_id: self.id,
        };
        
        // Store in log
        self.pre_prepare_log.insert(
            (self.view, self.sequence),
            pre_prepare.clone()
        );
        
        println!("Replica {} (PRIMARY): Sent PRE-PREPARE for seq={}", 
                 self.id, self.sequence);
        
        Some(pre_prepare)
    }
    
    /// Handle PRE-PREPARE message (Backups)
    fn handle_pre_prepare(&mut self, msg: PBFTMessage) -> Option<PBFTMessage> {
        // Validation checks
        if msg.replica_id != self.primary_id {
            println!("Replica {}: Rejected PRE-PREPARE from non-primary", self.id);
            return None;
        }
        
        if msg.view != self.view {
            println!("Replica {}: Rejected PRE-PREPARE with wrong view", self.id);
            return None;
        }
        
        // Check we haven't accepted different request with same sequence
        if let Some(existing) = self.pre_prepare_log.get(&(msg.view, msg.sequence)) {
            if existing.digest != msg.digest {
                println!("Replica {}: Conflicting PRE-PREPARE detected!", self.id);
                return None;
            }
        }
        
        // Accept PRE-PREPARE
        self.pre_prepare_log.insert((msg.view, msg.sequence), msg.clone());
        
        // Send PREPARE to all replicas
        let prepare = PBFTMessage {
            msg_type: MessageType::Prepare,
            view: msg.view,
            sequence: msg.sequence,
            digest: msg.digest,
            replica_id: self.id,
        };
        
        println!("Replica {}: Sent PREPARE for seq={}", self.id, msg.sequence);
        
        Some(prepare)
    }
    
    /// Handle PREPARE message
    fn handle_prepare(&mut self, msg: PBFTMessage) -> Option<PBFTMessage> {
        let key = (msg.view, msg.sequence);
        
        // Add to prepare log
        self.prepare_log.entry(key).or_insert_with(HashSet::new).insert(msg.clone());
        
        // Check if we have prepared (2f PREPARE messages)
        let prepare_count = self.prepare_log.get(&key).map_or(0, |s| s.len());
        
        if prepare_count >= 2 * self.f {
            println!("Replica {}: PREPARED for seq={} (received {} PREPAREs)",
                     self.id, msg.sequence, prepare_count);
            
            // Transition to prepared state - send COMMIT
            let commit = PBFTMessage {
                msg_type: MessageType::Commit,
                view: msg.view,
                sequence: msg.sequence,
                digest: msg.digest,
                replica_id: self.id,
            };
            
            println!("Replica {}: Sent COMMIT for seq={}", self.id, msg.sequence);
            
            return Some(commit);
        }
        
        None
    }
    
    /// Handle COMMIT message
    fn handle_commit(&mut self, msg: PBFTMessage) -> bool {
        let key = (msg.view, msg.sequence);
        
        // Add to commit log
        self.commit_log.entry(key).or_insert_with(HashSet::new).insert(msg.clone());
        
        // Check if we have committed (2f + 1 COMMIT messages)
        let commit_count = self.commit_log.get(&key).map_or(0, |s| s.len());
        
        if commit_count >= 2 * self.f + 1 {
            if self.executed_requests.insert(msg.sequence) {
                println!("Replica {}: COMMITTED and EXECUTED seq={} (received {} COMMITs)",
                         self.id, msg.sequence, commit_count);
                return true;
            }
        }
        
        false
    }
}

/// Simulation of PBFT network
fn simulate_pbft() {
    println!("=== PBFT Simulation (n=4, f=1) ===\n");
    
    // Create 4 replicas
    let mut replicas: Vec<PBFTReplica> = (0..4)
        .map(|id| PBFTReplica::new(id, 4))
        .collect();
    
    // Client request
    let request = ClientRequest {
        operation: "SET x = 42".to_string(),
        timestamp: 1000,
        client_id: "client_1".to_string(),
    };
    
    println!("Client sends request: {:?}\n", request.operation);
    
    // Phase 1: PRE-PREPARE (Primary broadcasts)
    let pre_prepare = replicas[0].handle_client_request(request).unwrap();
    
    // Phase 2: PREPARE (Backups send to all)
    let mut prepare_messages = Vec::new();
    for i in 1..4 {
        if let Some(prepare) = replicas[i].handle_pre_prepare(pre_prepare.clone()) {
            prepare_messages.push((i, prepare));
        }
    }
    
    println!();
    
    // Primary also prepares
    if let Some(prepare) = replicas[0].handle_pre_prepare(pre_prepare.clone()) {
        prepare_messages.push((0, prepare));
    }
    
    // Distribute PREPARE messages
    let prepare_msgs: Vec<_> = prepare_messages.iter()
        .map(|(_, msg)| msg.clone())
        .collect();
    
    println!();
    
    // Phase 3: COMMIT
    let mut commit_messages = Vec::new();
    for i in 0..4 {
        for prepare in &prepare_msgs {
            if let Some(commit) = replicas[i].handle_prepare(prepare.clone()) {
                commit_messages.push((i, commit));
            }
        }
    }
    
    println!();
    
    // Distribute COMMIT messages
    let commit_msgs: Vec<_> = commit_messages.iter()
        .map(|(_, msg)| msg.clone())
        .collect();
    
    // Final execution
    for i in 0..4 {
        for commit in &commit_msgs {
            replicas[i].handle_commit(commit.clone());
        }
    }
    
    println!("\n=== Consensus Achieved ===");
}

fn main() {
    simulate_pbft();
}
```

### Time Complexity Analysis

**Per Request:**
- PRE-PREPARE: O(1) - Primary broadcasts once
- PREPARE: O(n²) - n replicas send to n replicas = n² messages
- COMMIT: O(n²) - Similar to PREPARE

**Total Messages**: O(n²) per request

**Latency**: 3 message delays (pre-prepare → prepare → commit)

---

## Implementation in Go

```go
package main

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"sync"
)

// MessageType represents different PBFT message types
type MessageType int

const (
	Request MessageType = iota
	PrePrepare
	Prepare
	Commit
	Reply
)

// PBFTMessage is the core message structure
type PBFTMessage struct {
	Type      MessageType
	View      uint64
	Sequence  uint64
	Digest    string
	ReplicaID int
}

// ClientRequest from client
type ClientRequest struct {
	Operation string
	Timestamp uint64
	ClientID  string
}

// PBFTReplica represents a node in the PBFT network
type PBFTReplica struct {
	mu sync.Mutex
	
	id        int
	view      uint64
	sequence  uint64
	n         int // total replicas
	f         int // max faulty replicas
	primaryID int
	
	// Message logs
	prePrepareLog map[string]*PBFTMessage
	prepareLog    map[string]map[int]*PBFTMessage
	commitLog     map[string]map[int]*PBFTMessage
	
	// Execution tracking
	executedRequests map[uint64]bool
}

// NewPBFTReplica creates a new replica
func NewPBFTReplica(id, n int) *PBFTReplica {
	if n < 4 {
		panic("Need at least 4 replicas")
	}
	
	f := (n - 1) / 3
	
	return &PBFTReplica{
		id:               id,
		view:             0,
		sequence:         0,
		n:                n,
		f:                f,
		primaryID:        0,
		prePrepareLog:    make(map[string]*PBFTMessage),
		prepareLog:       make(map[string]map[int]*PBFTMessage),
		commitLog:        make(map[string]map[int]*PBFTMessage),
		executedRequests: make(map[uint64]bool),
	}
}

// IsPrimary checks if this replica is current primary
func (r *PBFTReplica) IsPrimary() bool {
	return r.id == r.primaryID
}

// Digest computes hash of request
func Digest(req *ClientRequest) string {
	data, _ := json.Marshal(req)
	hash := sha256.Sum256(data)
	return fmt.Sprintf("%x", hash)
}

// makeKey creates a unique key for view+sequence
func makeKey(view, seq uint64) string {
	return fmt.Sprintf("%d-%d", view, seq)
}

// HandleClientRequest processes incoming client request (primary only)
func (r *PBFTReplica) HandleClientRequest(req *ClientRequest) *PBFTMessage {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	if !r.IsPrimary() {
		return nil
	}
	
	r.sequence++
	digest := Digest(req)
	
	msg := &PBFTMessage{
		Type:      PrePrepare,
		View:      r.view,
		Sequence:  r.sequence,
		Digest:    digest,
		ReplicaID: r.id,
	}
	
	key := makeKey(r.view, r.sequence)
	r.prePrepareLog[key] = msg
	
	fmt.Printf("Replica %d (PRIMARY): Sent PRE-PREPARE for seq=%d\n", 
		r.id, r.sequence)
	
	return msg
}

// HandlePrePrepare processes PRE-PREPARE message
func (r *PBFTReplica) HandlePrePrepare(msg *PBFTMessage) *PBFTMessage {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	// Validate
	if msg.ReplicaID != r.primaryID {
		fmt.Printf("Replica %d: Rejected PRE-PREPARE from non-primary\n", r.id)
		return nil
	}
	
	if msg.View != r.view {
		fmt.Printf("Replica %d: Rejected PRE-PREPARE with wrong view\n", r.id)
		return nil
	}
	
	key := makeKey(msg.View, msg.Sequence)
	
	// Check for conflicts
	if existing, ok := r.prePrepareLog[key]; ok {
		if existing.Digest != msg.Digest {
			fmt.Printf("Replica %d: Conflicting PRE-PREPARE detected!\n", r.id)
			return nil
		}
	}
	
	r.prePrepareLog[key] = msg
	
	prepare := &PBFTMessage{
		Type:      Prepare,
		View:      msg.View,
		Sequence:  msg.Sequence,
		Digest:    msg.Digest,
		ReplicaID: r.id,
	}
	
	fmt.Printf("Replica %d: Sent PREPARE for seq=%d\n", r.id, msg.Sequence)
	
	return prepare
}

// HandlePrepare processes PREPARE message
func (r *PBFTReplica) HandlePrepare(msg *PBFTMessage) *PBFTMessage {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	key := makeKey(msg.View, msg.Sequence)
	
	if r.prepareLog[key] == nil {
		r.prepareLog[key] = make(map[int]*PBFTMessage)
	}
	r.prepareLog[key][msg.ReplicaID] = msg
	
	prepareCount := len(r.prepareLog[key])
	
	if prepareCount >= 2*r.f {
		fmt.Printf("Replica %d: PREPARED for seq=%d (received %d PREPAREs)\n",
			r.id, msg.Sequence, prepareCount)
		
		commit := &PBFTMessage{
			Type:      Commit,
			View:      msg.View,
			Sequence:  msg.Sequence,
			Digest:    msg.Digest,
			ReplicaID: r.id,
		}
		
		fmt.Printf("Replica %d: Sent COMMIT for seq=%d\n", r.id, msg.Sequence)
		
		return commit
	}
	
	return nil
}

// HandleCommit processes COMMIT message
func (r *PBFTReplica) HandleCommit(msg *PBFTMessage) bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	key := makeKey(msg.View, msg.Sequence)
	
	if r.commitLog[key] == nil {
		r.commitLog[key] = make(map[int]*PBFTMessage)
	}
	r.commitLog[key][msg.ReplicaID] = msg
	
	commitCount := len(r.commitLog[key])
	
	if commitCount >= 2*r.f+1 {
		if !r.executedRequests[msg.Sequence] {
			r.executedRequests[msg.Sequence] = true
			fmt.Printf("Replica %d: COMMITTED and EXECUTED seq=%d (received %d COMMITs)\n",
				r.id, msg.Sequence, commitCount)
			return true
		}
	}
	
	return false
}

func main() {
	fmt.Println("=== PBFT Simulation (n=4, f=1) ===\n")
	
	// Create replicas
	replicas := make([]*PBFTReplica, 4)
	for i := 0; i < 4; i++ {
		replicas[i] = NewPBFTReplica(i, 4)
	}
	
	// Client request
	req := &ClientRequest{
		Operation: "SET x = 42",
		Timestamp: 1000,
		ClientID:  "client_1",
	}
	
	fmt.Printf("Client sends request: %s\n\n", req.Operation)
	
	// Phase 1: PRE-PREPARE
	prePrepare := replicas[0].HandleClientRequest(req)
	
	// Phase 2: PREPARE
	var prepareMessages []*PBFTMessage
	for i := 1; i < 4; i++ {
		if prepare := replicas[i].HandlePrePrepare(prePrepare); prepare != nil {
			prepareMessages = append(prepareMessages, prepare)
		}
	}
	
	fmt.Println()
	
	if prepare := replicas[0].HandlePrePrepare(prePrepare); prepare != nil {
		prepareMessages = append(prepareMessages, prepare)
	}
	
	fmt.Println()
	
	// Phase 3: COMMIT
	var commitMessages []*PBFTMessage
	for i := 0; i < 4; i++ {
		for _, prepare := range prepareMessages {
			if commit := replicas[i].HandlePrepare(prepare); commit != nil {
				commitMessages = append(commitMessages, commit)
			}
		}
	}
	
	fmt.Println()
	
	// Execute
	for i := 0; i < 4; i++ {
		for _, commit := range commitMessages {
			replicas[i].HandleCommit(commit)
		}
	}
	
	fmt.Println("\n=== Consensus Achieved ===")
}
```

---

## Implementation in C

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// Message types
typedef enum {
    MSG_REQUEST,
    MSG_PRE_PREPARE,
    MSG_PREPARE,
    MSG_COMMIT,
    MSG_REPLY
} MessageType;

// PBFT Message structure
typedef struct {
    MessageType type;
    uint64_t view;
    uint64_t sequence;
    char digest[65];  // SHA-256 hex string
    int replica_id;
} PBFTMessage;

// Client request
typedef struct {
    char operation[256];
    uint64_t timestamp;
    char client_id[64];
} ClientRequest;

// Message log entry
typedef struct MessageNode {
    PBFTMessage msg;
    struct MessageNode *next;
} MessageNode;

// PBFT Replica
typedef struct {
    int id;
    uint64_t view;
    uint64_t sequence;
    int n;  // total replicas
    int f;  // max faulty
    int primary_id;
    
    // Simplified logs (in production: use hash tables)
    PBFTMessage pre_prepare_log[100];
    int pre_prepare_count;
    
    MessageNode *prepare_log[100];
    MessageNode *commit_log[100];
    
    bool executed[100];
} PBFTReplica;

// Initialize replica
void pbft_replica_init(PBFTReplica *r, int id, int n) {
    r->id = id;
    r->view = 0;
    r->sequence = 0;
    r->n = n;
    r->f = (n - 1) / 3;
    r->primary_id = 0;
    r->pre_prepare_count = 0;
    
    for (int i = 0; i < 100; i++) {
        r->prepare_log[i] = NULL;
        r->commit_log[i] = NULL;
        r->executed[i] = false;
    }
}

// Check if primary
bool is_primary(PBFTReplica *r) {
    return r->id == r->primary_id;
}

// Simplified digest (in production: use crypto library)
void compute_digest(ClientRequest *req, char *digest) {
    snprintf(digest, 65, "digest_%s_%lu", req->operation, req->timestamp);
}

// Handle client request (primary only)
bool handle_client_request(PBFTReplica *r, ClientRequest *req, PBFTMessage *out_msg) {
    if (!is_primary(r)) {
        return false;
    }
    
    r->sequence++;
    
    out_msg->type = MSG_PRE_PREPARE;
    out_msg->view = r->view;
    out_msg->sequence = r->sequence;
    compute_digest(req, out_msg->digest);
    out_msg->replica_id = r->id;
    
    // Store in log
    r->pre_prepare_log[r->pre_prepare_count++] = *out_msg;
    
    printf("Replica %d (PRIMARY): Sent PRE-PREPARE for seq=%lu\n", 
           r->id, r->sequence);
    
    return true;
}

// Handle PRE-PREPARE
bool handle_pre_prepare(PBFTReplica *r, PBFTMessage *msg, PBFTMessage *out_msg) {
    // Validate
    if (msg->replica_id != r->primary_id) {
        printf("Replica %d: Rejected PRE-PREPARE from non-primary\n", r->id);
        return false;
    }
    
    if (msg->view != r->view) {
        printf("Replica %d: Rejected PRE-PREPARE with wrong view\n", r->id);
        return false;
    }
    
    // Store
    r->pre_prepare_log[r->pre_prepare_count++] = *msg;
    
    // Create PREPARE
    out_msg->type = MSG_PREPARE;
    out_msg->view = msg->view;
    out_msg->sequence = msg->sequence;
    strcpy(out_msg->digest, msg->digest);
    out_msg->replica_id = r->id;
    
    printf("Replica %d: Sent PREPARE for seq=%lu\n", r->id, msg->sequence);
    
    return true;
}

// Add message to log
void add_to_log(MessageNode **log, PBFTMessage *msg) {
    MessageNode *node = (MessageNode *)malloc(sizeof(MessageNode));
    node->msg = *msg;
    node->next = *log;
    *log = node;
}

// Count messages in log for sequence
int count_messages(MessageNode *log, uint64_t seq) {
    int count = 0;
    MessageNode *curr = log;
    while (curr) {
        if (curr->msg.sequence == seq) {
            count++;
        }
        curr = curr->next;
    }
    return count;
}

// Handle PREPARE
bool handle_prepare(PBFTReplica *r, PBFTMessage *msg, PBFTMessage *out_msg) {
    // Add to log (simplified indexing)
    int idx = msg->sequence % 100;
    add_to_log(&r->prepare_log[idx], msg);
    
    int prepare_count = count_messages(r->prepare_log[idx], msg->sequence);
    
    if (prepare_count >= 2 * r->f) {
        printf("Replica %d: PREPARED for seq=%lu (received %d PREPAREs)\n",
               r->id, msg->sequence, prepare_count);
        
        out_msg->type = MSG_COMMIT;
        out_msg->view = msg->view;
        out_msg->sequence = msg->sequence;
        strcpy(out_msg->digest, msg->digest);
        out_msg->replica_id = r->id;
        
        printf("Replica %d: Sent COMMIT for seq=%lu\n", r->id, msg->sequence);
        
        return true;
    }
    
    return false;
}

// Handle COMMIT
bool handle_commit(PBFTReplica *r, PBFTMessage *msg) {
    int idx = msg->sequence % 100;
    add_to_log(&r->commit_log[idx], msg);
    
    int commit_count = count_messages(r->commit_log[idx], msg->sequence);
    
    if (commit_count >= 2 * r->f + 1) {
        if (!r->executed[idx]) {
            r->executed[idx] = true;
            printf("Replica %d: COMMITTED and EXECUTED seq=%lu (received %d COMMITs)\n",
                   r->id, msg->sequence, commit_count);
            return true;
        }
    }
    
    return false;
}

// Cleanup
void cleanup_replica(PBFTReplica *r) {
    for (int i = 0; i < 100; i++) {
        MessageNode *curr = r->prepare_log[i];
        while (curr) {
            MessageNode *temp = curr;
            curr = curr->next;
            free(temp);
        }
        
        curr = r->commit_log[i];
        while (curr) {
            MessageNode *temp = curr;
            curr = curr->next;
            free(temp);
        }
    }
}

int main() {
    printf("=== PBFT Simulation (n=4, f=1) ===\n\n");
    
    // Create replicas
    PBFTReplica replicas[4];
    for (int i = 0; i < 4; i++) {
        pbft_replica_init(&replicas[i], i, 4);
    }
    
    // Client request
    ClientRequest req = {
        .operation = "SET x = 42",
        .timestamp = 1000,
        .client_id = "client_1"
    };
    
    printf("Client sends request: %s\n\n", req.operation);
    
    // Phase 1: PRE-PREPARE
    PBFTMessage pre_prepare;
    handle_client_request(&replicas[0], &req, &pre_prepare);
    
    // Phase 2: PREPARE
    PBFTMessage prepares[4];
    int prepare_count = 0;
    
    for (int i = 1; i < 4; i++) {
        if (handle_pre_prepare(&replicas[i], &pre_prepare, &prepares[prepare_count])) {
            prepare_count++;
        }
    }
    
    printf("\n");
    
    if (handle_pre_prepare(&replicas[0], &pre_prepare, &prepares[prepare_count])) {
        prepare_count++;
    }
    
    printf("\n");
    
    // Phase 3: COMMIT
    PBFTMessage commits[16];
    int commit_count = 0;
    
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < prepare_count; j++) {
            if (handle_prepare(&replicas[i], &prepares[j], &commits[commit_count])) {
                commit_count++;
            }
        }
    }
    
    printf("\n");
    
    // Execute
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < commit_count; j++) {
            handle_commit(&replicas[i], &commits[j]);
        }
    }
    
    printf("\n=== Consensus Achieved ===\n");
    
    // Cleanup
    for (int i = 0; i < 4; i++) {
        cleanup_replica(&replicas[i]);
    }
    
    return 0;
}
```

---

## Algorithm 2: Tendermint (Modern BFT for Blockchains)

### Key Improvements Over PBFT

Tendermint uses a **round-based voting** mechanism with the following enhancements:

```
┌──────────────────────────────────────────────────┐
│           Tendermint Consensus                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. Propose: Validator proposes block            │
│      │                                           │
│      ▼                                           │
│  2. Prevote: Validators vote on proposal         │
│      │                                           │
│      ▼                                           │
│  3. Precommit: Validators commit to block        │
│      │                                           │
│      ▼                                           │
│  4. Commit: Block finalized (>2/3 precommits)    │
│                                                  │
│  View changes: Automatic timeout mechanism       │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Key Concepts:**
- **Proposer**: Deterministically selected validator for each round
- **Prevote**: First voting phase (like PREPARE)
- **Precommit**: Second voting phase (like COMMIT)
- **Lock**: Once >2/3 prevote, validators lock on that value
- **POL (Proof of Lock)**: Evidence of +2/3 prevotes

### Rust Implementation (Simplified Tendermint)

```rust
use std::collections::{HashMap, HashSet};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum VoteType {
    Prevote,
    Precommit,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Vote {
    vote_type: VoteType,
    height: u64,      // Block height
    round: u64,       // Round number
    block_hash: Option<String>, // None = vote for nil
    validator_id: usize,
}

#[derive(Debug, Clone)]
struct Block {
    height: u64,
    data: String,
    hash: String,
}

struct TendermintValidator {
    id: usize,
    height: u64,
    round: u64,
    
    n: usize,  // total validators
    f: usize,  // max faulty
    
    // Current state
    locked_value: Option<Block>,
    locked_round: Option<u64>,
    valid_value: Option<Block>,
    valid_round: Option<u64>,
    
    // Vote tracking
    prevotes: HashMap<(u64, u64), HashSet<Vote>>,
    precommits: HashMap<(u64, u64), HashSet<Vote>>,
    
    // Committed blocks
    committed: HashMap<u64, Block>,
}

impl TendermintValidator {
    fn new(id: usize, n: usize) -> Self {
        let f = (n - 1) / 3;
        
        TendermintValidator {
            id,
            height: 1,
            round: 0,
            n,
            f,
            locked_value: None,
            locked_round: None,
            valid_value: None,
            valid_round: None,
            prevotes: HashMap::new(),
            precommits: HashMap::new(),
            committed: HashMap::new(),
        }
    }
    
    /// Calculate proposer for round (round-robin)
    fn proposer(&self, round: u64) -> usize {
        (round as usize) % self.n
    }
    
    /// Check if this validator is proposer
    fn is_proposer(&self) -> bool {
        self.id == self.proposer(self.round)
    }
    
    /// Propose a block (proposer only)
    fn propose(&mut self) -> Option<Block> {
        if !self.is_proposer() {
            return None;
        }
        
        // Use valid_value if available, else create new block
        let block = if let Some(ref valid) = self.valid_value {
            valid.clone()
        } else {
            Block {
                height: self.height,
                data: format!("Block at height {}", self.height),
                hash: format!("hash_{}", self.height),
            }
        };
        
        println!("Validator {} (PROPOSER): Proposed block {} for height={}, round={}",
                 self.id, block.hash, self.height, self.round);
        
        Some(block)
    }
    
    /// Upon receiving a proposal
    fn handle_proposal(&mut self, block: &Block) -> Option<Vote> {
        // Rule: Prevote for block if:
        // 1. Not locked, OR
        // 2. Locked on this block, OR
        // 3. Block is from round > locked_round
        
        let should_prevote = if let Some(ref locked) = self.locked_value {
            if locked.hash == block.hash {
                true
            } else if let Some(locked_r) = self.locked_round {
                // Would need POL check here (simplified)
                false
            } else {
                false
            }
        } else {
            true
        };
        
        let vote = Vote {
            vote_type: VoteType::Prevote,
            height: self.height,
            round: self.round,
            block_hash: if should_prevote { Some(block.hash.clone()) } else { None },
            validator_id: self.id,
        };
        
        println!("Validator {}: Prevoted for {} at round={}",
                 self.id,
                 vote.block_hash.as_ref().unwrap_or(&"nil".to_string()),
                 self.round);
        
        Some(vote)
    }
    
    /// Add vote to tracking
    fn add_vote(&mut self, vote: Vote) {
        let key = (vote.height, vote.round);
        
        match vote.vote_type {
            VoteType::Prevote => {
                self.prevotes.entry(key).or_insert_with(HashSet::new).insert(vote);
            }
            VoteType::Precommit => {
                self.precommits.entry(key).or_insert_with(HashSet::new).insert(vote);
            }
        }
    }
    
    /// Check for +2/3 prevotes
    fn check_prevotes(&mut self, block_hash: &str) -> Option<Vote> {
        let key = (self.height, self.round);
        
        if let Some(votes) = self.prevotes.get(&key) {
            let count = votes.iter()
                .filter(|v| v.block_hash.as_ref().map_or(false, |h| h == block_hash))
                .count();
            
            if count >= 2 * self.f + 1 {
                println!("Validator {}: Received +2/3 PREVOTES for {} at round={}",
                         self.id, block_hash, self.round);
                
                // Lock on this value
                self.locked_value = Some(Block {
                    height: self.height,
                    data: "locked".to_string(),
                    hash: block_hash.to_string(),
                });
                self.locked_round = Some(self.round);
                
                // Send PRECOMMIT
                return Some(Vote {
                    vote_type: VoteType::Precommit,
                    height: self.height,
                    round: self.round,
                    block_hash: Some(block_hash.to_string()),
                    validator_id: self.id,
                });
            }
        }
        
        None
    }
    
    /// Check for +2/3 precommits
    fn check_precommits(&mut self, block_hash: &str) -> bool {
        let key = (self.height, self.round);
        
        if let Some(votes) = self.precommits.get(&key) {
            let count = votes.iter()
                .filter(|v| v.block_hash.as_ref().map_or(false, |h| h == block_hash))
                .count();
            
            if count >= 2 * self.f + 1 {
                println!("Validator {}: Received +2/3 PRECOMMITS for {} - COMMITTING",
                         self.id, block_hash);
                
                // Commit block
                self.committed.insert(self.height, Block {
                    height: self.height,
                    data: "committed".to_string(),
                    hash: block_hash.to_string(),
                });
                
                // Move to next height
                self.height += 1;
                self.round = 0;
                self.locked_value = None;
                self.locked_round = None;
                
                return true;
            }
        }
        
        false
    }
}

fn simulate_tendermint() {
    println!("=== Tendermint Simulation (n=4, f=1) ===\n");
    
    let mut validators: Vec<TendermintValidator> = (0..4)
        .map(|id| TendermintValidator::new(id, 4))
        .collect();
    
    // Round 1: Propose
    let proposal = validators[0].propose().unwrap();
    
    // Prevote phase
    let mut prevotes = Vec::new();
    for i in 0..4 {
        if let Some(vote) = validators[i].handle_proposal(&proposal) {
            prevotes.push(vote);
        }
    }
    
    // Distribute prevotes
    for vote in &prevotes {
        for i in 0..4 {
            validators[i].add_vote(vote.clone());
        }
    }
    
    println!();
    
    // Precommit phase
    let mut precommits = Vec::new();
    for i in 0..4 {
        if let Some(vote) = validators[i].check_prevotes(&proposal.hash) {
            precommits.push(vote);
        }
    }
    
    // Distribute precommits
    for vote in &precommits {
        for i in 0..4 {
            validators[i].add_vote(vote.clone());
        }
    }
    
    println!();
    
    // Commit
    for i in 0..4 {
        validators[i].check_precommits(&proposal.hash);
    }
    
    println!("\n=== Consensus Achieved ===");
}

fn main() {
    simulate_tendermint();
}
```

---

## Comparison: PBFT vs Tendermint

```
┌───────────────┬─────────────────┬─────────────────┐
│   Property    │      PBFT       │   Tendermint    │
├───────────────┼─────────────────┼─────────────────┤
│ Message       │                 │                 │
│ Complexity    │     O(n²)       │     O(n²)       │
├───────────────┼─────────────────┼─────────────────┤
│ Finality      │  After commit   │  Instant after  │
│               │  (3 phases)     │  +2/3 precommit │
├───────────────┼─────────────────┼─────────────────┤
│ View Change   │   Complex       │    Simpler      │
│               │   protocol      │   (timeout)     │
├───────────────┼─────────────────┼─────────────────┤
│ Liveness      │  Requires       │   Better        │
│               │  synchrony      │   handling      │
├───────────────┼─────────────────┼─────────────────┤
│ Use Case      │  Permissioned   │  Blockchain     │
│               │  systems        │  consensus      │
└───────────────┴─────────────────┴─────────────────┘
```

---

## Performance Optimization Techniques

### 1. Message Aggregation

Instead of O(n²) messages, use **threshold signatures**:

```rust
// Conceptual: aggregate n signatures into one
struct AggregateSignature {
    signers: HashSet<usize>,
    combined_sig: Vec<u8>,
}

// Reduces messages from n² to n
```

### 2. Pipelining

Process multiple consensus instances concurrently:

```
Height 1: [Propose] → [Prevote] → [Precommit] → [Commit]
Height 2:             [Propose] → [Prevote]   → [Precommit] → [Commit]
Height 3:                         [Propose]   → [Prevote]   → [Precommit]
```

### 3. Optimistic Fast Path

If all nodes agree immediately:

```rust
// Fast path: 2 phases instead of 3
if all_agree_in_prevote() {
    skip_precommit_phase();
    commit_immediately();
}
```

---

## Mental Models for Mastery

### 1. The Voting Quorum Principle

**Insight**: Any two quorums of size 2f+1 must intersect in at least one honest node.

```
Total: n = 3f + 1
Quorum 1: 2f + 1 nodes
Quorum 2: 2f + 1 nodes

Intersection: (2f+1) + (2f+1) - (3f+1) = f + 1 nodes
Since f are faulty → at least 1 honest node in intersection
```

This is why consensus works!

### 2. The Safety-Liveness Trade-off

**Safety**: Never decide wrong
**Liveness**: Eventually decide

**FLP Impossibility Theorem**: You cannot have both in an asynchronous system with even one fault.

**Solution**: Add weak synchrony assumptions (timeouts).

---

## Advanced Topics (Brief Overview)

### HoneyBadgerBFT (Asynchronous)
- No timing assumptions
- Uses **threshold encryption**
- O(n²) communication
- Provably optimal

### Algorand (Pure Proof-of-Stake)
- Uses **verifiable random functions (VRF)**
- Sortition: random committee selection
- Scales to thousands of nodes

### Hotstuff (Used in Libra/Diem)
- **Linear view change**: O(n) instead of O(n²)
- Three-phase voting
- Used in production blockchains

---

## Practice Problems

1. **Implement view change** in PBFT (when primary fails)
2. **Add cryptographic signatures** to messages
3. **Optimize message passing** using channels/goroutines
4. **Simulate Byzantine behavior** (nodes sending conflicting messages)
5. **Implement checkpointing** for garbage collection

---

## Complexity Summary

```
┌──────────────────────┬─────────────┬──────────────┐
│     Operation        │ Time        │ Messages     │
├──────────────────────┼─────────────┼──────────────┤
│ Normal case          │ O(1)        │ O(n²)        │
│ View change          │ O(n)        │ O(n³)        │
│ Checkpoint           │ O(1)        │ O(n²)        │
└──────────────────────┴─────────────┴──────────────┘
```

---

This guide provides a solid foundation in BFT algorithms. The implementations demonstrate core concepts in Rust, Go, and C with proper abstraction and clarity.

**Next steps for mastery:**
- Study the original PBFT paper
- Implement view change protocol
- Add real cryptographic primitives
- Build a distributed test harness
- Analyze attack scenarios

Would you like me to dive deeper into any specific aspect, such as view changes, cryptographic details, or practical optimizations?