# The Complete Arsenal: Game Theory in Competitive Programming

Game theory problems represent the **pinnacle of algorithmic thinking** — they demand mathematical intuition, backward induction mastery, and the ability to reason about adversarial optimization. You're entering a domain where most programmers falter, but the top 1% dominate through pattern recognition and deep understanding.

---

## I. The Foundation: What Makes a Game?

A combinatorial game has these properties:
- **Two players** alternating turns
- **Perfect information** (both players see the complete state)
- **Deterministic** (no randomness)
- **Normal play convention** (last player to move wins) OR **Misère** (last to move loses)

**Mental Model:** Think of the game state as a directed acyclic graph (DAG) where each node is a position and edges represent legal moves.

---

## II. Core Concepts: The Pillars of Game Theory

### 1. **Winning and Losing Positions**

```
AXIOMS (commit these to memory):
- Terminal position (no moves available) is LOSING in normal play
- A position is WINNING if ANY move leads to a LOSING position
- A position is LOSING if ALL moves lead to WINNING positions
```

**The Monk's Insight:** This is backward induction — you reason from the end state backward. Like a chess grandmaster, you must see the endgame first.

### 2. **Nim and the XOR Property**

The **Game of Nim** is the cornerstone. Multiple piles of stones, players alternate removing any number from one pile. Last to move wins.

**Breakthrough Theorem (Bouton's):**
```
Position is LOSING ⟺ XOR of all pile sizes = 0
```

**Rust Implementation:**
```rust
fn is_losing_nim(piles: &[u32]) -> bool {
    piles.iter().fold(0, |acc, &x| acc ^ x) == 0
}

// Why this works: XOR has the symmetric difference property
// If nim_sum = 0, ANY move creates nim_sum ≠ 0
// If nim_sum ≠ 0, there EXISTS a move to make nim_sum = 0
```

**Time Complexity:** O(n), Space: O(1)

**Deep Understanding:** XOR cancels pairs. The nim-sum being 0 means perfect "balance" — any disturbance favors the opponent.

---

## III. The Complete Pattern Catalog

### Pattern 1: **Simple DP Game States**

**Template Problem:** "Can I Win" (LeetCode 464)

```rust
use std::collections::HashMap;

fn can_i_win(max_choosable: i32, desired_total: i32) -> bool {
    // Edge case: if sum of all numbers < desired, impossible
    let total = (max_choosable * (max_choosable + 1)) / 2;
    if total < desired_total { return false; }
    if desired_total <= 0 { return true; }
    
    let mut memo = HashMap::new();
    dfs(0, desired_total, &mut memo)
}

fn dfs(used: i32, remaining: i32, memo: &mut HashMap<i32, bool>) -> bool {
    if remaining <= 0 { return false; } // Previous player won
    
    if let Some(&cached) = memo.get(&used) {
        return cached;
    }
    
    // Try each unused number
    for i in 1..=20 { // max_choosable ≤ 20
        let mask = 1 << i;
        if used & mask != 0 { continue; } // Already used
        
        // If this move makes opponent lose, we win
        if !dfs(used | mask, remaining - i, memo) {
            memo.insert(used, true);
            return true;
        }
    }
    
    memo.insert(used, false);
    false
}
```

**Key Insight:** Use bitmask to represent state (which numbers used). Memoize on state. The negation (`!`) is crucial — if opponent loses, we win.

**Complexity:** O(2^n × n) states, each state does O(n) work.

---

### Pattern 2: **Nim Variants**

**Stone Game Series** (LeetCode 877, 1140, 1406, 1510, 1563, 1686)

**Core Strategy:**
```rust
// Stone Game I: Even piles, can always win
// Proof: Color piles alternating (odd/even indices)
// Total stones at odd indices vs even differs
// First player chooses the color with more stones

fn stone_game(piles: Vec<i32>) -> bool {
    true // Always win with optimal play (even number of piles)
}

// Stone Game II: M parameter (can take up to 2M piles)
fn stone_game_ii(piles: Vec<i32>) -> i32 {
    let n = piles.len();
    let mut suffix = vec![0; n + 1];
    
    // suffix[i] = sum from i to end
    for i in (0..n).rev() {
        suffix[i] = suffix[i + 1] + piles[i];
    }
    
    let mut dp = vec![vec![0; n + 1]; n];
    
    // dp[i][m] = max stones first player gets from position i with parameter m
    for i in (0..n).rev() {
        for m in 1..=n {
            if i + 2 * m >= n {
                dp[i][m] = suffix[i]; // Take everything
            } else {
                for x in 1..=2*m {
                    // Take x piles, opponent plays optimally from i+x with max(m, x)
                    let opponent_takes = dp[i + x][m.max(x)];
                    dp[i][m] = dp[i][m].max(suffix[i] - opponent_takes);
                }
            }
        }
    }
    
    dp[0][1]
}
```

**Mental Model:** When you take your turn, you get `total_remaining - what_opponent_gets`. Maximize this.

---

### Pattern 3: **Sprague-Grundy Theorem (Nimbers)**

**The Ultimate Weapon:** Any impartial game can be reduced to a Nim game.

**Grundy Number (mex):**
```
g(position) = mex({g(successor) | all successors of position})
mex(S) = minimum excludant = smallest non-negative integer not in S
```

**Example: Divisor Game** (LeetCode 1025)

```rust
fn divisor_game(n: i32) -> bool {
    // Grundy number approach (overkill, but illustrative)
    let mut grundy = vec![0; n as usize + 1];
    
    for i in 2..=n as usize {
        let mut reachable = std::collections::HashSet::new();
        
        for x in 1..i {
            if i % x == 0 {
                reachable.insert(grundy[i - x]);
            }
        }
        
        // mex
        let mut mex_val = 0;
        while reachable.contains(&mex_val) {
            mex_val += 1;
        }
        grundy[i] = mex_val;
    }
    
    grundy[n as usize] != 0
}

// Optimized observation: n is even ⟺ Alice wins
fn divisor_game_optimal(n: i32) -> bool {
    n % 2 == 0
}
```

**Why even wins?**
- If n is even, Alice takes 1 → Bob gets odd
- From odd, all divisors are odd, so odd - odd = even → Alice gets even again
- Continue until Bob gets n=1 (loses)

**Pattern Recognition Skill:** Look for parity arguments, invariants that players cannot change.

---

### Pattern 4: **Multi-Pile Nim Games**

**Nim Game** (LeetCode 292) — Single pile simplification:
```rust
fn can_win_nim(n: i32) -> bool {
    n % 4 != 0
}
```

**Proof:**
- If n % 4 == 0, you're in a losing position
- Any move (1, 2, or 3) leaves opponent with n % 4 ≠ 0 → they win
- If n % 4 ∈ {1, 2, 3}, take that many to leave opponent with multiple of 4

**Multi-pile with XOR:**
```rust
// Game where you can remove stones from ONE pile
fn nim_game_multi(piles: Vec<i32>) -> bool {
    piles.iter().fold(0, |acc, &x| acc ^ x) != 0
}
```

---

### Pattern 5: **Minimax with Alpha-Beta (Zero-Sum Games)**

**Predict the Winner** (LeetCode 486)

```rust
fn predict_the_winner(nums: Vec<i32>) -> bool {
    let n = nums.len();
    let mut dp = vec![vec![0; n]; n];
    
    // dp[i][j] = max advantage (my_score - opponent_score) from nums[i..=j]
    for i in 0..n {
        dp[i][i] = nums[i];
    }
    
    for len in 2..=n {
        for i in 0..=n-len {
            let j = i + len - 1;
            // Take left: nums[i] - dp[i+1][j] (opponent plays optimally on rest)
            // Take right: nums[j] - dp[i][j-1]
            dp[i][j] = (nums[i] - dp[i+1][j]).max(nums[j] - dp[i][j-1]);
        }
    }
    
    dp[0][n-1] >= 0
}
```

**Go Idiomatic Version:**
```go
func predictTheWinner(nums []int) bool {
    n := len(nums)
    dp := make([][]int, n)
    for i := range dp {
        dp[i] = make([]int, n)
        dp[i][i] = nums[i]
    }
    
    for length := 2; length <= n; length++ {
        for i := 0; i <= n-length; i++ {
            j := i + length - 1
            dp[i][j] = max(nums[i] - dp[i+1][j], nums[j] - dp[i][j-1])
        }
    }
    
    return dp[0][n-1] >= 0
}

func max(a, b int) int {
    if a > b { return a }
    return b
}
```

**Complexity:** O(n²) time, O(n²) space. Can optimize to O(n) space with rolling array.

---

## IV. Advanced Patterns

### Pattern 6: **Combinatorial Game Theory**

**Cat and Mouse** (LeetCode 913) — Graph games:

```rust
use std::collections::VecDeque;

const DRAW: i32 = 0;
const MOUSE: i32 = 1;
const CAT: i32 = 2;

fn cat_mouse_game(graph: Vec<Vec<i32>>) -> i32 {
    let n = graph.len();
    // color[mouse][cat][turn] = outcome
    let mut color = vec![vec![vec![DRAW; 2]; n]; n];
    let mut degree = vec![vec![vec![0; 2]; n]; n];
    
    // Calculate degrees (number of possible moves)
    for m in 0..n {
        for c in 0..n {
            degree[m][c][0] = graph[m].len();
            degree[m][c][1] = graph[c].iter().filter(|&&x| x != 0).count();
        }
    }
    
    let mut queue = VecDeque::new();
    
    // Base cases
    for i in 0..n {
        for t in 0..2 {
            color[0][i][t] = MOUSE;
            queue.push_back((0, i, t, MOUSE));
            if i > 0 {
                color[i][i][t] = CAT;
                queue.push_back((i, i, t, CAT));
            }
        }
    }
    
    // BFS backward from terminal states
    while let Some((mouse, cat, turn, c)) = queue.pop_front() {
        if mouse == 1 && cat == 2 && turn == 0 {
            return c;
        }
        
        let prev_turn = 1 - turn;
        for &prev in &graph[if prev_turn == 0 { mouse } else { cat }] {
            let (prev_mouse, prev_cat) = if prev_turn == 0 {
                (prev as usize, cat)
            } else {
                if prev == 0 { continue; }
                (mouse, prev as usize)
            };
            
            if color[prev_mouse][prev_cat][prev_turn] != DRAW {
                continue;
            }
            
            if prev_turn == 0 && c == MOUSE || prev_turn == 1 && c == CAT {
                color[prev_mouse][prev_cat][prev_turn] = c;
                queue.push_back((prev_mouse, prev_cat, prev_turn, c));
            } else {
                degree[prev_mouse][prev_cat][prev_turn] -= 1;
                if degree[prev_mouse][prev_cat][prev_turn] == 0 {
                    color[prev_mouse][prev_cat][prev_turn] = c;
                    queue.push_back((prev_mouse][prev_cat][prev_turn, c));
                }
            }
        }
    }
    
    color[1][2][0]
}
```

**Mental Model:** Retrograde analysis — work backward from known outcomes. Color the game tree.

---

### Pattern 7: **Game on Trees**

**Example Framework:**
```rust
// Delete nodes, last player unable to move loses
fn tree_game(edges: Vec<Vec<i32>>) -> bool {
    // Build adjacency list
    // Calculate Grundy numbers bottom-up
    // Root's Grundy number determines winner
    unimplemented!()
}
```

---

## V. The Cognitive Toolkit

### **Mental Models for Game Theory:**

1. **Backward Induction**: Always reason from the end state backward. What happens if we're one move from the end? Two moves? Build up.

2. **Parity and Invariants**: Look for properties that alternate or remain constant. Even/odd positions often have different characteristics.

3. **Symmetry Breaking**: If the game looks symmetric, first player can often mirror second player's moves.

4. **The Greedy Trap**: Optimal play ≠ greedy play. You must consider opponent's best response.

5. **State Space Reduction**: Compress game state (bitmasks, coordinates, hash). Memoization is your ally.

### **Debugging Strategy:**

```rust
// Always test these cases:
// 1. Trivial wins (n=1, n=2)
// 2. First losing position
// 3. Symmetry (if game is symmetric)
// 4. Your DP recurrence at small values
```

---

## VI. The Pattern Recognition Hierarchy

```
Level 1: Direct DP (Stone Game I, Divisor Game)
    ↓
Level 2: Minimax/Advantage DP (Predict Winner, Stone Game V)
    ↓
Level 3: Nim and XOR games (Nim Game, multi-pile variants)
    ↓
Level 4: Sprague-Grundy (general impartial games)
    ↓
Level 5: Graph games with BFS/retrograde (Cat and Mouse)
    ↓
Level 6: Complex state spaces (Chess-like games, Alpha-Beta pruning)
```

---

## VII. Essential Problems (In Order)

**Foundation:**
1. Nim Game (292) — Core intuition
2. Divisor Game (1025) — Parity reasoning
3. Stone Game (877) — Symmetry breaking

**Intermediate:**
4. Predict the Winner (486) — Minimax DP
5. Can I Win (464) — Bitmask + memoization
6. Stone Game II (1140) — Parameter M handling

**Advanced:**
7. Cat and Mouse (913) — Graph retrograde
8. Stone Game III (1406) — Multi-choice minimax
9. Flip Game II (294) — Grundy numbers

---

## VIII. The Master's Approach

**When you see a game problem:**

1. **Identify the type**: Impartial? Partisan? Zero-sum?
2. **Find base cases**: What are trivial wins/losses?
3. **Define state**: Minimal info needed to determine outcome
4. **Recurrence relation**: How does current state depend on future states?
5. **Memoization**: Cache computed states
6. **Optimize**: Look for mathematical patterns (XOR, parity, closed-form)

**Code in this order:**
```rust
// 1. Brute force recursive (understand logic)
// 2. Add memoization (correctness)
// 3. Convert to DP if possible (efficiency)
// 4. Look for pattern/closed-form (mastery)
```

---

## IX. The Monk's Path Forward

Game theory will sharpen your:
- **Adversarial reasoning**: Thinking multiple moves ahead
- **State space design**: How to represent complex situations efficiently
- **Mathematical intuition**: XOR properties, parity, number theory
- **Proof construction**: Why does this strategy work?

**Your training regimen:**
1. Solve one game theory problem daily
2. After solving, write out the **proof** of correctness
3. Implement in Rust, then Go, then C — see the differences
4. Find the O(1) solution if one exists

**Remember:** Game theory problems are **logic puzzles disguised as games**. The code is simple; the insight is hard. Cultivate the patience to think deeply before coding.

---

You're now armed with the complete game theory arsenal. Each pattern is a weapon — master them all, and you'll slice through problems that intimidate 99% of programmers.

**Now go. Think. Solve. Dominate.**