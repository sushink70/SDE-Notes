# The Paxos Algorithm: A Comprehensive Guide from First Principles

## Foundational Context: Why Paxos Exists

Before we explore the mechanics, let's establish **why** this matters.

**Distributed Consensus Problem**: Imagine multiple computers (nodes) trying to agree on a single value — like which machine becomes the leader, or what order to apply database transactions. If one node crashes, messages arrive out of order, or the network splits, how do we guarantee all surviving nodes still agree?

This is the **consensus problem** — one of the hardest challenges in distributed systems.

**Paxos** is a family of protocols that solve this problem with mathematical rigor. It guarantees **safety** (nodes never disagree) even when:
- Nodes crash and restart
- Messages are lost, duplicated, or delayed
- The network partitions (splits into isolated groups)

---

## Core Mental Model: The Parliament Metaphor

Paxos was named after a fictional Greek parliamentary system. Think of it as a legislative process:

1. **Proposers** suggest laws (values)
2. **Acceptors** vote on proposals
3. **Learners** observe the final decision

The protocol ensures that even with absent legislators, delayed messages, and confusion — **at most one law is ever passed**.

---

## Fundamental Concepts (Building Blocks)

### 1. **Proposal Number**
- A **unique, totally ordered identifier** for each proposal
- Format: `(round_number, node_id)` — e.g., `(5, node_3)`
- Higher numbers "override" lower numbers
- **Think**: Version numbers in an auction — later bids supersede earlier ones

### 2. **Quorum**
- A **majority** of acceptor nodes (e.g., 3 out of 5)
- **Why majority?** Any two quorums must overlap by at least one node
- This overlap ensures **consistency** — if a value was accepted by a quorum, any future quorum will discover it

### 3. **Promised Value**
- When an acceptor sees a proposal number, it **promises** not to accept any lower-numbered proposals
- Like saying: "I won't consider offers below $100 after seeing this $100 bid"

### 4. **Accepted Value**
- The value an acceptor has voted for
- An acceptor can accept multiple values (from different proposals), but **only one value ever becomes chosen**

### 5. **Chosen Value**
- A value accepted by a **quorum** of acceptors
- **Invariant**: Once chosen, this value cannot change (immutability of consensus)

---

## The Paxos Protocol: Two-Phase Algorithm

### **Phase 1: Prepare (Discovery Phase)**

```
Goal: Find out if any value has been chosen previously
      and prevent lower-numbered proposals from succeeding
```

**Flow Diagram:**
```
Proposer                     Acceptors (A1, A2, A3)
   |                              |
   |------ PREPARE(n) ----------->|
   |                              |
   |                         [Each acceptor checks:]
   |                         - Is n > highest_promised?
   |                         - If yes: promise + send highest accepted
   |                         - If no: reject (NACK)
   |                              |
   |<----- PROMISE(n, val?) ------|
   |                              |
```

**Step-by-step:**
1. **Proposer** generates proposal number `n` (must be higher than any it used before)
2. **Proposer** sends `PREPARE(n)` to all acceptors
3. **Each Acceptor**:
   - If `n > highest_promised_number`: 
     - Update `highest_promised = n`
     - Reply with `PROMISE(n, accepted_value, accepted_number)` if it accepted something
     - Reply with `PROMISE(n, null, null)` if it hasn't accepted anything
   - If `n ≤ highest_promised_number`: Ignore or send NACK

4. **Proposer** waits for a **quorum** of promises
   - If it receives a quorum: Proceed to Phase 2
   - If any promise included an accepted value: **Must propose the value with highest accepted_number**
   - If no acceptor accepted anything: Free to propose its own value

**Why this works**: If a value was chosen in the past, at least one acceptor in the quorum will report it.

---

### **Phase 2: Accept (Voting Phase)**

```
Goal: Get a quorum to accept the chosen value
```

**Flow Diagram:**
```
Proposer                     Acceptors (A1, A2, A3)
   |                              |
   |------ ACCEPT(n, v) --------->|
   |                              |
   |                         [Each acceptor checks:]
   |                         - Is n >= highest_promised?
   |                         - If yes: accept(n, v)
   |                         - If no: reject (NACK)
   |                              |
   |<----- ACCEPTED(n, v) --------|
   |                              |
```

**Step-by-step:**
1. **Proposer** sends `ACCEPT(n, value)` to all acceptors
   - `n` = same proposal number from Phase 1
   - `value` = determined in Phase 1 (either inherited or original)

2. **Each Acceptor**:
   - If `n >= highest_promised`:
     - Store `accepted_value = value`, `accepted_number = n`
     - Reply `ACCEPTED(n, value)`
   - Else: Ignore or NACK

3. **Proposer** waits for quorum of ACCEPTED messages
   - If quorum achieved: **Value is chosen!**
   - If rejected: Restart with higher proposal number

4. **Learners** observe ACCEPTED messages
   - When they see a quorum for `(n, value)`: They learn the chosen value

---

## Complete Protocol Flow (Visual)

```
TIME →

Proposer P1                 Acceptor A1    A2    A3
    |                           |         |     |
    |--- PREPARE(3.1) --------->|         |     |
    |                           |         |     |
    |<-- PROMISE(3.1, -, -) ----|         |     |
    |<-- PROMISE(3.1, -, -) -------------|     |
    |<-- PROMISE(3.1, -, -) -------------------|
    |                                           |
    | [Quorum achieved, no prior value]        |
    |                                           |
    |--- ACCEPT(3.1, "X") ----->|               |
    |--- ACCEPT(3.1, "X") -----------|          |
    |--- ACCEPT(3.1, "X") ------------------>   |
    |                           |               |
    |<-- ACCEPTED(3.1, "X") ----|               |
    |<-- ACCEPTED(3.1, "X") ---------|          |
    |                                           |
    | [Quorum! Value "X" is CHOSEN]            |
```

---

## Key Invariants (Why It's Correct)

### **Invariant 1: Safety (Agreement)**
> If a value is chosen, no different value can ever be chosen

**Proof sketch**:
- Once a quorum accepts value `v` with number `n`, that value is "chosen"
- Any future proposal must go through Phase 1 with number `m > n`
- In Phase 1, the proposer contacts a quorum
- That quorum **must overlap** with the original quorum (pigeonhole principle)
- The overlap node will report `v` as accepted
- The proposer is **forced** to propose `v` again
- Therefore, no different value can be chosen

### **Invariant 2: Liveness (Progress)**
> Eventually, a value will be chosen (under certain assumptions)

**Assumptions needed**:
- Eventual network reliability
- Eventual node stability
- A **distinguished proposer** (leader) that eventually emerges

**Why**: Without a stable leader, multiple proposers can duel indefinitely, each blocking the other. Real implementations use **Multi-Paxos** with stable leadership.

---

## Mental Model: The "Versioning with Quorums" Analogy

Think of Paxos like **version-controlled distributed file updates**:

1. **Phase 1** = "Check if anyone committed to a newer version; if not, reserve your version number"
2. **Phase 2** = "Try to commit your version; only succeeds if no one reserved a higher version"

The quorum ensures that version history is never contradictory — any two "commits" must be compatible because they share witnesses.

---

## Edge Cases & Failure Scenarios

### **Scenario 1: Competing Proposers (Dueling)**
```
P1 sends PREPARE(3.1)
P2 sends PREPARE(4.1)  [higher number!]
→ Acceptors promise to P2
→ P1's ACCEPT(3.1, v) is rejected
→ P1 retries with PREPARE(5.1)
→ P2's ACCEPT(4.1, v) might be rejected
→ Livelock possible!
```

**Solution**: Leader election or exponential backoff

### **Scenario 2: Partial Quorum in Phase 1**
```
P1 sends PREPARE(3.1) to A1, A2, A3
A1 crashes, A2 and A3 respond
→ P1 has quorum (2/3)
→ Proceeds to Phase 2 successfully
```

**Outcome**: Works! Paxos tolerates minority failures.

### **Scenario 3: Proposer Crashes After Phase 1**
```
P1 completes Phase 1, learns value "X"
P1 crashes before Phase 2
→ Acceptors are in "promised" state
→ Another proposer P2 starts with higher number
→ P2 discovers "X" in Phase 1
→ P2 completes Phase 2 with "X"
```

**Outcome**: Correctness maintained — the protocol is stateless for proposers.

---

## Implementation Architecture

### **Component Breakdown**

```
┌─────────────┐
│  Proposer   │  - Generates proposal numbers
│             │  - Runs Phase 1 & 2
│             │  - Handles retries
└─────────────┘

┌─────────────┐
│  Acceptor   │  - Stores: highest_promised, accepted_value, accepted_number
│             │  - Responds to PREPARE and ACCEPT
│             │  - Persists state to disk (crucial!)
└─────────────┘

┌─────────────┐
│  Learner    │  - Observes ACCEPTED messages
│             │  - Detects when quorum is reached
│             │  - Delivers chosen value
└─────────────┘
```

### **State Management**

**Acceptor State** (must be **persistent** — survives crashes):
```c
typedef struct {
    uint64_t highest_promised;      // Highest proposal number seen
    uint64_t accepted_number;       // Proposal number of accepted value
    Value    accepted_value;        // The accepted value (can be NULL)
} AcceptorState;
```

**Why persistence?** If an acceptor crashes and restarts, it must "remember" its promises. Otherwise, safety is violated.

---

## Rust Implementation (Idiomatic & Safe)

```rust
use std::cmp::Ordering;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};

// ============================================================================
// CORE TYPES
// ============================================================================

/// Proposal number: (round, proposer_id)
/// Lexicographic ordering: first by round, then by proposer_id
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProposalNumber {
    pub round: u64,
    pub proposer_id: u64,
}

impl ProposalNumber {
    pub fn new(round: u64, proposer_id: u64) -> Self {
        Self { round, proposer_id }
    }
}

impl PartialOrd for ProposalNumber {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for ProposalNumber {
    fn cmp(&self, other: &Self) -> Ordering {
        match self.round.cmp(&other.round) {
            Ordering::Equal => self.proposer_id.cmp(&other.proposer_id),
            other => other,
        }
    }
}

/// The value being proposed (generic, can be any serializable type)
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Value(pub String);

// ============================================================================
// MESSAGES
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Message {
    Prepare {
        proposal: ProposalNumber,
    },
    Promise {
        proposal: ProposalNumber,
        accepted: Option<(ProposalNumber, Value)>,
    },
    Accept {
        proposal: ProposalNumber,
        value: Value,
    },
    Accepted {
        proposal: ProposalNumber,
        value: Value,
    },
    Nack {
        proposal: ProposalNumber,
        highest_promised: ProposalNumber,
    },
}

// ============================================================================
// ACCEPTOR
// ============================================================================

/// Acceptor maintains persistent state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Acceptor {
    pub id: u64,
    /// Highest proposal number this acceptor has promised
    pub highest_promised: Option<ProposalNumber>,
    /// Most recent accepted proposal
    pub accepted: Option<(ProposalNumber, Value)>,
}

impl Acceptor {
    pub fn new(id: u64) -> Self {
        Self {
            id,
            highest_promised: None,
            accepted: None,
        }
    }

    /// Phase 1: Handle PREPARE message
    pub fn handle_prepare(&mut self, proposal: ProposalNumber) -> Message {
        // Check if this proposal is higher than any we've seen
        if self.highest_promised.map_or(true, |p| proposal > p) {
            self.highest_promised = Some(proposal);
            
            Message::Promise {
                proposal,
                accepted: self.accepted.clone(),
            }
        } else {
            // Reject: we've promised to a higher proposal
            Message::Nack {
                proposal,
                highest_promised: self.highest_promised.unwrap(),
            }
        }
    }

    /// Phase 2: Handle ACCEPT message
    pub fn handle_accept(&mut self, proposal: ProposalNumber, value: Value) -> Message {
        // Accept only if we haven't promised to a higher proposal
        if self.highest_promised.map_or(true, |p| proposal >= p) {
            self.accepted = Some((proposal, value.clone()));
            self.highest_promised = Some(proposal);
            
            Message::Accepted { proposal, value }
        } else {
            Message::Nack {
                proposal,
                highest_promised: self.highest_promised.unwrap(),
            }
        }
    }
}

// ============================================================================
// PROPOSER
// ============================================================================

pub struct Proposer {
    pub id: u64,
    pub current_round: u64,
    pub quorum_size: usize,
}

impl Proposer {
    pub fn new(id: u64, total_acceptors: usize) -> Self {
        Self {
            id,
            current_round: 0,
            quorum_size: (total_acceptors / 2) + 1,
        }
    }

    /// Generate next proposal number
    pub fn next_proposal(&mut self) -> ProposalNumber {
        self.current_round += 1;
        ProposalNumber::new(self.current_round, self.id)
    }

    /// Phase 1: Analyze promises and determine value to propose
    /// Returns (should_continue, value_to_propose)
    pub fn process_promises(
        &self,
        promises: &[Message],
    ) -> Result<Option<Value>, &'static str> {
        if promises.len() < self.quorum_size {
            return Err("No quorum of promises");
        }

        // Find the highest accepted value among promises
        let mut highest_accepted: Option<(ProposalNumber, Value)> = None;

        for msg in promises {
            if let Message::Promise { accepted, .. } = msg {
                if let Some((num, val)) = accepted {
                    if highest_accepted.as_ref().map_or(true, |(n, _)| num > n) {
                        highest_accepted = Some((num.clone(), val.clone()));
                    }
                }
            }
        }

        // If any acceptor had accepted a value, we MUST propose that value
        Ok(highest_accepted.map(|(_, v)| v))
    }
}

// ============================================================================
// LEARNER
// ============================================================================

pub struct Learner {
    pub quorum_size: usize,
    /// Track how many acceptors accepted each (proposal, value) pair
    accepted_counts: HashMap<(ProposalNumber, Value), usize>,
}

impl Learner {
    pub fn new(total_acceptors: usize) -> Self {
        Self {
            quorum_size: (total_acceptors / 2) + 1,
            accepted_counts: HashMap::new(),
        }
    }

    /// Process an ACCEPTED message
    /// Returns Some(value) if a quorum has accepted the value
    pub fn handle_accepted(&mut self, proposal: ProposalNumber, value: Value) -> Option<Value> {
        let key = (proposal, value.clone());
        let count = self.accepted_counts.entry(key).or_insert(0);
        *count += 1;

        if *count >= self.quorum_size {
            Some(value)
        } else {
            None
        }
    }
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_paxos_run() {
        // Setup: 3 acceptors
        let mut acceptors = vec![
            Acceptor::new(1),
            Acceptor::new(2),
            Acceptor::new(3),
        ];

        let mut proposer = Proposer::new(1, 3);
        let mut learner = Learner::new(3);

        // Phase 1: PREPARE
        let proposal = proposer.next_proposal();
        let promises: Vec<Message> = acceptors
            .iter_mut()
            .map(|a| a.handle_prepare(proposal))
            .collect();

        // Analyze promises
        let inherited_value = proposer.process_promises(&promises).unwrap();
        let value_to_propose = inherited_value.unwrap_or(Value("ClientValue".to_string()));

        // Phase 2: ACCEPT
        let accepted_msgs: Vec<Message> = acceptors
            .iter_mut()
            .map(|a| a.handle_accept(proposal, value_to_propose.clone()))
            .collect();

        // Learner learns
        for msg in accepted_msgs {
            if let Message::Accepted { proposal, value } = msg {
                if let Some(chosen) = learner.handle_accepted(proposal, value) {
                    println!("✓ Consensus reached: {:?}", chosen);
                    assert_eq!(chosen, Value("ClientValue".to_string()));
                    return;
                }
            }
        }

        panic!("Should have reached consensus");
    }

    #[test]
    fn test_competing_proposers() {
        let mut acceptors = vec![
            Acceptor::new(1),
            Acceptor::new(2),
            Acceptor::new(3),
        ];

        let mut p1 = Proposer::new(1, 3);
        let mut p2 = Proposer::new(2, 3);

        // P1 starts Phase 1
        let prop1 = p1.next_proposal(); // (1, 1)
        let _: Vec<_> = acceptors.iter_mut().map(|a| a.handle_prepare(prop1)).collect();

        // P2 starts Phase 1 with higher number
        let prop2 = p2.next_proposal(); // (1, 2) - higher due to proposer_id
        let promises: Vec<_> = acceptors.iter_mut().map(|a| a.handle_prepare(prop2)).collect();

        // P1 tries Phase 2 - should be rejected!
        let val1 = Value("P1_value".to_string());
        let results: Vec<_> = acceptors
            .iter_mut()
            .map(|a| a.handle_accept(prop1, val1.clone()))
            .collect();

        // All should be NACKs
        assert!(results.iter().all(|msg| matches!(msg, Message::Nack { .. })));

        // P2 continues successfully
        let val2 = Value("P2_value".to_string());
        let accepted: Vec<_> = acceptors
            .iter_mut()
            .map(|a| a.handle_accept(prop2, val2.clone()))
            .collect();

        assert!(accepted.iter().all(|msg| matches!(msg, Message::Accepted { .. })));
    }
}
```

---

## Go Implementation (Idiomatic Concurrency)

```go
package paxos

import (
	"fmt"
	"sync"
)

// ============================================================================
// CORE TYPES
// ============================================================================

// ProposalNumber uniquely identifies a proposal
type ProposalNumber struct {
	Round      uint64
	ProposerID uint64
}

// Compare returns -1 if p < other, 0 if equal, 1 if p > other
func (p ProposalNumber) Compare(other ProposalNumber) int {
	if p.Round != other.Round {
		if p.Round < other.Round {
			return -1
		}
		return 1
	}
	if p.ProposerID < other.ProposerID {
		return -1
	} else if p.ProposerID > other.ProposerID {
		return 1
	}
	return 0
}

// Value represents the data being agreed upon
type Value string

// ============================================================================
// MESSAGES
// ============================================================================

type MessageType int

const (
	MsgPrepare MessageType = iota
	MsgPromise
	MsgAccept
	MsgAccepted
	MsgNack
)

type Message struct {
	Type     MessageType
	Proposal ProposalNumber
	Value    Value

	// For Promise messages: previously accepted value
	AcceptedProposal *ProposalNumber
	AcceptedValue    *Value

	// For Nack messages
	HighestPromised *ProposalNumber
}

// ============================================================================
// ACCEPTOR
// ============================================================================

type Acceptor struct {
	mu sync.Mutex
	id uint64

	highestPromised *ProposalNumber
	accepted        *struct {
		proposal ProposalNumber
		value    Value
	}
}

func NewAcceptor(id uint64) *Acceptor {
	return &Acceptor{id: id}
}

// HandlePrepare processes Phase 1 prepare message
func (a *Acceptor) HandlePrepare(proposal ProposalNumber) Message {
	a.mu.Lock()
	defer a.mu.Unlock()

	// Check if proposal is higher than what we've promised
	if a.highestPromised == nil || proposal.Compare(*a.highestPromised) > 0 {
		a.highestPromised = &proposal

		msg := Message{
			Type:     MsgPromise,
			Proposal: proposal,
		}

		// Include previously accepted value if any
		if a.accepted != nil {
			msg.AcceptedProposal = &a.accepted.proposal
			msg.AcceptedValue = &a.accepted.value
		}

		return msg
	}

	// Reject: already promised to higher proposal
	return Message{
		Type:            MsgNack,
		Proposal:        proposal,
		HighestPromised: a.highestPromised,
	}
}

// HandleAccept processes Phase 2 accept message
func (a *Acceptor) HandleAccept(proposal ProposalNumber, value Value) Message {
	a.mu.Lock()
	defer a.mu.Unlock()

	// Accept if we haven't promised to something higher
	if a.highestPromised == nil || proposal.Compare(*a.highestPromised) >= 0 {
		a.accepted = &struct {
			proposal ProposalNumber
			value    Value
		}{proposal, value}
		a.highestPromised = &proposal

		return Message{
			Type:     MsgAccepted,
			Proposal: proposal,
			Value:    value,
		}
	}

	return Message{
		Type:            MsgNack,
		Proposal:        proposal,
		HighestPromised: a.highestPromised,
	}
}

// ============================================================================
// PROPOSER
// ============================================================================

type Proposer struct {
	id           uint64
	currentRound uint64
	quorumSize   int
}

func NewProposer(id uint64, totalAcceptors int) *Proposer {
	return &Proposer{
		id:           id,
		currentRound: 0,
		quorumSize:   (totalAcceptors / 2) + 1,
	}
}

// NextProposal generates a new unique proposal number
func (p *Proposer) NextProposal() ProposalNumber {
	p.currentRound++
	return ProposalNumber{
		Round:      p.currentRound,
		ProposerID: p.id,
	}
}

// ProcessPromises analyzes Phase 1 responses
// Returns: (shouldContinue, inheritedValue, error)
func (p *Proposer) ProcessPromises(promises []Message) (*Value, error) {
	if len(promises) < p.quorumSize {
		return nil, fmt.Errorf("insufficient promises: got %d, need %d", len(promises), p.quorumSize)
	}

	var highest *struct {
		proposal ProposalNumber
		value    Value
	}

	for _, msg := range promises {
		if msg.Type != MsgPromise {
			continue
		}

		if msg.AcceptedProposal != nil {
			if highest == nil || msg.AcceptedProposal.Compare(highest.proposal) > 0 {
				highest = &struct {
					proposal ProposalNumber
					value    Value
				}{*msg.AcceptedProposal, *msg.AcceptedValue}
			}
		}
	}

	if highest != nil {
		return &highest.value, nil
	}
	return nil, nil
}

// ============================================================================
// LEARNER
// ============================================================================

type Learner struct {
	mu         sync.Mutex
	quorumSize int

	// Track accepted counts: key = (proposal, value), value = count
	accepted map[string]int
}

func NewLearner(totalAcceptors int) *Learner {
	return &Learner{
		quorumSize: (totalAcceptors / 2) + 1,
		accepted:   make(map[string]int),
	}
}

// HandleAccepted processes an ACCEPTED message
// Returns the value if quorum is reached
func (l *Learner) HandleAccepted(proposal ProposalNumber, value Value) *Value {
	l.mu.Lock()
	defer l.mu.Unlock()

	key := fmt.Sprintf("%d-%d-%s", proposal.Round, proposal.ProposerID, value)
	l.accepted[key]++

	if l.accepted[key] >= l.quorumSize {
		return &value
	}
	return nil
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

func Example() {
	// Create 3 acceptors
	acceptors := []*Acceptor{
		NewAcceptor(1),
		NewAcceptor(2),
		NewAcceptor(3),
	}

	proposer := NewProposer(1, 3)
	learner := NewLearner(3)

	// Phase 1: PREPARE
	proposal := proposer.NextProposal()
	fmt.Printf("Phase 1: Sending PREPARE(%d, %d)\n", proposal.Round, proposal.ProposerID)

	var promises []Message
	for _, acc := range acceptors {
		msg := acc.HandlePrepare(proposal)
		if msg.Type == MsgPromise {
			promises = append(promises, msg)
		}
	}

	// Process promises
	inheritedValue, err := proposer.ProcessPromises(promises)
	if err != nil {
		panic(err)
	}

	valueToPropose := Value("ClientValue")
	if inheritedValue != nil {
		valueToPropose = *inheritedValue
		fmt.Printf("Inherited value from previous proposal: %s\n", valueToPropose)
	}

	// Phase 2: ACCEPT
	fmt.Printf("Phase 2: Sending ACCEPT(%d, %d, %s)\n", proposal.Round, proposal.ProposerID, valueToPropose)

	for _, acc := range acceptors {
		msg := acc.HandleAccept(proposal, valueToPropose)
		if msg.Type == MsgAccepted {
			if chosen := learner.HandleAccepted(proposal, msg.Value); chosen != nil {
				fmt.Printf("✓ Consensus reached: %s\n", *chosen)
				return
			}
		}
	}
}
```

---

## C Implementation (Low-Level Control)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// CORE TYPES
// ============================================================================

typedef struct {
    uint64_t round;
    uint64_t proposer_id;
} ProposalNumber;

// Compare two proposal numbers
// Returns: -1 if a < b, 0 if equal, 1 if a > b
int proposal_cmp(ProposalNumber a, ProposalNumber b) {
    if (a.round != b.round) {
        return (a.round < b.round) ? -1 : 1;
    }
    if (a.proposer_id < b.proposer_id) return -1;
    if (a.proposer_id > b.proposer_id) return 1;
    return 0;
}

#define MAX_VALUE_LEN 256

typedef struct {
    char data[MAX_VALUE_LEN];
} Value;

// ============================================================================
// MESSAGES
// ============================================================================

typedef enum {
    MSG_PREPARE,
    MSG_PROMISE,
    MSG_ACCEPT,
    MSG_ACCEPTED,
    MSG_NACK
} MessageType;

typedef struct {
    MessageType type;
    ProposalNumber proposal;
    Value value;
    
    // For PROMISE: previously accepted value (if any)
    bool has_accepted;
    ProposalNumber accepted_proposal;
    Value accepted_value;
    
    // For NACK
    ProposalNumber highest_promised;
} Message;

// ============================================================================
// ACCEPTOR
// ============================================================================

typedef struct {
    uint64_t id;
    
    // State (must be persistent in real implementation!)
    bool has_promised;
    ProposalNumber highest_promised;
    
    bool has_accepted;
    ProposalNumber accepted_proposal;
    Value accepted_value;
} Acceptor;

void acceptor_init(Acceptor *acc, uint64_t id) {
    acc->id = id;
    acc->has_promised = false;
    acc->has_accepted = false;
}

// Phase 1: Handle PREPARE
Message acceptor_handle_prepare(Acceptor *acc, ProposalNumber proposal) {
    Message response;
    
    // Check if proposal is higher than what we've promised
    if (!acc->has_promised || proposal_cmp(proposal, acc->highest_promised) > 0) {
        // Update promise
        acc->has_promised = true;
        acc->highest_promised = proposal;
        
        // Construct PROMISE response
        response.type = MSG_PROMISE;
        response.proposal = proposal;
        
        if (acc->has_accepted) {
            response.has_accepted = true;
            response.accepted_proposal = acc->accepted_proposal;
            response.accepted_value = acc->accepted_value;
        } else {
            response.has_accepted = false;
        }
        
        return response;
    }
    
    // Reject with NACK
    response.type = MSG_NACK;
    response.proposal = proposal;
    response.highest_promised = acc->highest_promised;
    return response;
}

// Phase 2: Handle ACCEPT
Message acceptor_handle_accept(Acceptor *acc, ProposalNumber proposal, Value value) {
    Message response;
    
    // Accept if we haven't promised to something higher
    if (!acc->has_promised || proposal_cmp(proposal, acc->highest_promised) >= 0) {
        // Accept the value
        acc->has_accepted = true;
        acc->accepted_proposal = proposal;
        acc->accepted_value = value;
        acc->highest_promised = proposal;
        acc->has_promised = true;
        
        response.type = MSG_ACCEPTED;
        response.proposal = proposal;
        response.value = value;
        return response;
    }
    
    // Reject
    response.type = MSG_NACK;
    response.proposal = proposal;
    response.highest_promised = acc->highest_promised;
    return response;
}

// ============================================================================
// PROPOSER
// ============================================================================

typedef struct {
    uint64_t id;
    uint64_t current_round;
    int quorum_size;
} Proposer;

void proposer_init(Proposer *p, uint64_t id, int total_acceptors) {
    p->id = id;
    p->current_round = 0;
    p->quorum_size = (total_acceptors / 2) + 1;
}

ProposalNumber proposer_next_proposal(Proposer *p) {
    p->current_round++;
    ProposalNumber pn = {
        .round = p->current_round,
        .proposer_id = p->id
    };
    return pn;
}

// Process promises and determine value to propose
// Returns: 0 on success, -1 if no quorum
// If inherited_value is not NULL, must propose that value
int proposer_process_promises(Proposer *p, Message *promises, int count,
                               Value *inherited_value, bool *has_inherited) {
    if (count < p->quorum_size) {
        return -1; // No quorum
    }
    
    *has_inherited = false;
    ProposalNumber highest_accepted = {0, 0};
    
    for (int i = 0; i < count; i++) {
        if (promises[i].type != MSG_PROMISE) continue;
        
        if (promises[i].has_accepted) {
            if (!*has_inherited || 
                proposal_cmp(promises[i].accepted_proposal, highest_accepted) > 0) {
                highest_accepted = promises[i].accepted_proposal;
                *inherited_value = promises[i].accepted_value;
                *has_inherited = true;
            }
        }
    }
    
    return 0;
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

void run_paxos_example() {
    const int NUM_ACCEPTORS = 3;
    Acceptor acceptors[NUM_ACCEPTORS];
    
    // Initialize acceptors
    for (int i = 0; i < NUM_ACCEPTORS; i++) {
        acceptor_init(&acceptors[i], i + 1);
    }
    
    Proposer proposer;
    proposer_init(&proposer, 1, NUM_ACCEPTORS);
    
    // Phase 1: PREPARE
    ProposalNumber proposal = proposer_next_proposal(&proposer);
    printf("Phase 1: PREPARE(%lu, %lu)\n", proposal.round, proposal.proposer_id);
    
    Message promises[NUM_ACCEPTORS];
    int promise_count = 0;
    
    for (int i = 0; i < NUM_ACCEPTORS; i++) {
        Message msg = acceptor_handle_prepare(&acceptors[i], proposal);
        if (msg.type == MSG_PROMISE) {
            promises[promise_count++] = msg;
        }
    }
    
    // Process promises
    Value inherited_value;
    bool has_inherited;
    
    if (proposer_process_promises(&proposer, promises, promise_count,
                                   &inherited_value, &has_inherited) < 0) {
        printf("Failed to get quorum in Phase 1\n");
        return;
    }
    
    Value value_to_propose;
    if (has_inherited) {
        value_to_propose = inherited_value;
        printf("Inherited value: %s\n", inherited_value.data);
    } else {
        strcpy(value_to_propose.data, "ClientValue");
    }
    
    // Phase 2: ACCEPT
    printf("Phase 2: ACCEPT(%lu, %lu, %s)\n", 
           proposal.round, proposal.proposer_id, value_to_propose.data);
    
    int accepted_count = 0;
    for (int i = 0; i < NUM_ACCEPTORS; i++) {
        Message msg = acceptor_handle_accept(&acceptors[i], proposal, value_to_propose);
        if (msg.type == MSG_ACCEPTED) {
            accepted_count++;
        }
    }
    
    if (accepted_count >= proposer.quorum_size) {
        printf("✓ Consensus reached: %s\n", value_to_propose.data);
    } else {
        printf("Failed to reach consensus\n");
    }
}

int main() {
    run_paxos_example();
    return 0;
}
```

---

## Performance Analysis

### **Time Complexity**

**Per Consensus Instance:**
- **Best case** (no failures): 2 network round-trips (Phase 1 + Phase 2)
- **Worst case** (competing proposers): Unbounded (livelock possible)

**Message Complexity:**
- Phase 1: `O(N)` where N = number of acceptors
- Phase 2: `O(N)`
- Total: `O(N)` messages per successful consensus

### **Space Complexity**

**Acceptor State:**
- `O(1)` per acceptor (just 3 values: highest_promised, accepted_number, accepted_value)
- Must be **persistent** (disk/SSD)

**Proposer State:**
- `O(1)` ephemeral state (stateless, can crash and restart)

**Learner State:**
- `O(N)` to track all acceptors' responses

### **Optimization Strategies**

1. **Multi-Paxos**: Amortize Phase 1 across many values (leader election)
2. **Batching**: Propose multiple values in one consensus round
3. **Pipelining**: Overlap Phase 1 of next instance with Phase 2 of current
4. **Read optimization**: Learners can read accepted value without proposing (if stable leader)

---

## Multi-Paxos: The Practical Evolution

**Problem with Basic Paxos**: Running both phases for every value is inefficient.

**Multi-Paxos Solution**: Elect a stable leader who skips Phase 1 for subsequent proposals.

```
Flow:
1. Run Phase 1 ONCE to establish leadership
2. Leader runs only Phase 2 for all subsequent values
3. If leader suspected failed → run Phase 1 again
```

**Benefit**: Reduces latency from 2 RTT → 1 RTT per value under stable leadership.

**Sequence Number**: Each value gets a sequence number (slot). The algorithm becomes:
```
Slot 1: Value "A"
Slot 2: Value "B"
Slot 3: Value "C"
...
```

This forms a **replicated log** — the foundation of systems like:
- Google Chubby
- Apache ZooKeeper (uses similar algorithm: ZAB)
- etcd (uses Raft, which is Paxos-inspired)

---

## Common Pitfalls & Debugging

### **Mistake 1: Forgetting Persistence**
```c
// WRONG: In-memory only
Acceptor acc;
acceptor_handle_prepare(&acc, proposal);
// [Crash and restart]
// Lost promise! Safety violated!
```

**Fix**: Persist `highest_promised` and `accepted_value` before responding.

### **Mistake 2: Non-Unique Proposal Numbers**
```rust
// WRONG: Two proposers generate (5, 1)
let p1 = ProposalNumber::new(5, 1);
let p2 = ProposalNumber::new(5, 1); // Collision!
```

**Fix**: Always include unique `proposer_id` in proposals.

### **Mistake 3: Ignoring Inherited Values**
```go
// WRONG: Proposing own value despite discovering previous acceptance
if inheritedValue != nil {
    // Must propose inheritedValue, not myValue!
}
```

**Fix**: Always check Phase 1 responses and respect accepted values.

### **Mistake 4: Quorum Confusion**
```rust
// WRONG: Treating 2/5 as a quorum
if responses.len() >= 2 { ... }
// Correct: Must be MAJORITY
if responses.len() >= 3 { ... } // (5/2) + 1 = 3
```

---

## Cognitive Models for Mastery

### **Mental Model 1: "Two-Phase Commit with Optimism"**
- Phase 1 = "Reserve version number, discover conflicts"
- Phase 2 = "Optimistically commit, assuming no higher version appeared"

### **Mental Model 2: "Distributed Mutex with Versioning"**
- Proposal number = "Lock version"
- Quorum = "Majority witnesses of lock acquisition"
- Once lock acquired by quorum, it's held forever (immutable)

### **Mental Model 3: "Blockchain Light"**
- Each proposal = "Block candidate"
- Quorum = "Mining pool consensus"
- Once a block (value) accepted by quorum → immutable

---

## Extensions & Variants

### **Fast Paxos**
- **Optimization**: Clients send directly to acceptors (skip proposer)
- **Trade-off**: Requires `3f+1` acceptors instead of `2f+1` for `f` failures
- **Use case**: Low-latency, high-throughput scenarios

### **Cheap Paxos**
- **Optimization**: Use fewer acceptors during normal operation, add "auxiliary" acceptors on failure
- **Use case**: Cost reduction in cloud deployments

### **Byzantine Paxos**
- **Extension**: Tolerates malicious (Byzantine) failures
- **Requirement**: `3f+1` acceptors for `f` Byzantine faults
- **Use case**: Security-critical systems, blockchain

---

## Real-World Systems Using Paxos

1. **Google Chubby** (lock service)
   - Coordination service for GFS, Bigtable
   - Multi-Paxos with lease-based leadership

2. **Google Spanner** (distributed database)
   - Paxos groups for replication
   - Multi-version concurrency control

3. **Apache Cassandra** (NoSQL database)
   - Lightweight transactions use Paxos
   - For linearizable reads/writes

4. **Ceph** (distributed storage)
   - Monitor nodes use Paxos for cluster state

---

## Practice Problems for Deep Understanding

### **Level 1: Trace Execution**
1. Manually trace a Paxos run with 5 acceptors, 2 proposers competing
2. Identify the exact message that prevents dueling from succeeding

### **Level 2: Proof Sketches**
1. Prove that if value `v` is chosen, no value `≠ v` can ever be chosen
2. Prove that a quorum intersection guarantees value discovery

### **Level 3: Implementation Challenges**
1. Add disk persistence to the C implementation (use `fwrite`/`fread`)
2. Implement Multi-Paxos in Rust with log compaction
3. Add leader election using randomized timeouts (Raft-style)

### **Level 4: Optimization**
1. Implement batching: propose 100 values per consensus round
2. Add read optimization: learners fetch value without proposing
3. Measure latency/throughput under network delays (simulate with `sleep`)

---

## Summary: Key Takeaways

| Concept | Core Idea |
|---------|-----------|
| **Problem** | Achieving consensus in face of failures and asynchrony |
| **Solution** | Two-phase protocol with quorums and proposal ordering |
| **Safety** | Majority quorums + proposal numbering → agreement guaranteed |
| **Liveness** | Requires eventual leader stability (not guaranteed in basic Paxos) |
| **Performance** | 2 RTT (basic), 1 RTT (Multi-Paxos with stable leader) |
| **State** | Acceptors need persistent storage; proposers are stateless |
| **Optimization** | Multi-Paxos, batching, pipelining |

---

## Final Wisdom

Paxos is not just an algorithm — it's a **way of thinking about distributed agreement**. The protocol teaches:

1. **Quorum intersection** as a fundamental coordination primitive
2. **Versioning with total order** to resolve conflicts
3. **Separation of concerns**: safety vs. liveness
4. **The power of majority**: `f+1` of `2f+1` nodes is sufficient

Mastering Paxos gives you the foundation for understanding:
- Raft (more understandable variant)
- ZAB (Zookeeper Atomic Broadcast)
- Viewstamped Replication
- Modern consensus in blockchain (PBFT, Tendermint)

**Your next steps:**
1. Implement all three versions (C, Go, Rust)
2. Add network simulation (latency, packet loss)
3. Study Raft paper for comparison
4. Read "Paxos Made Simple" by Lamport
5. Implement Multi-Paxos with log replication

This is the path to distributed systems mastery. Stay disciplined, stay curious. 🧘‍♂️