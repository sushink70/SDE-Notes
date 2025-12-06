# Mastering State Management in DSA: A Comprehensive Guide

This is one of the **most critical yet underrated skills** in competitive programming and system design. The ability to **mentally simulate and track state** separates average problem solvers from the top 1%. Let's build this skill systematically.

---

## **1. Fundamental Mental Model: State as a Snapshot**

Think of **state** as a complete snapshot of your program at any point in time. This includes:

- **Variable values** (primitives, containers)
- **Pointer positions** (indices, references)
- **Call stack** (function frames, recursion depth)
- **Heap state** (allocated memory, ownership)
- **Loop invariants** (what's true before/after each iteration)
- **Auxiliary structures** (visited sets, memo tables)

**Mental Framework:**
> "At this exact moment, what is the value of every variable that matters? What constraints hold? What has been processed vs. what remains?"

---

## **2. Categories of State to Track**

### **A. Pointer/Index State**
Most common in array/string problems.

**Key Patterns:**
- **Two pointers** (left, right converging)
- **Sliding window** (start, end expanding/contracting)
- **Fast/slow pointers** (cycle detection)
- **Multiple indices** (merge operations)

### **B. Accumulator State**
Running calculations that evolve.

**Examples:**
- Running sum, product, XOR
- Min/max seen so far
- Count of valid elements
- Hash map frequencies

### **C. Structural State**
Data structure internals.

**Examples:**
- Stack/queue contents
- Tree traversal position
- Graph visited nodes
- Heap top element

### **D. Recursion/Call Stack State**
Hidden state in function calls.

**Track:**
- Current recursion depth
- Parameters at each level
- Return values propagating up
- Memoization table state

### **E. Temporal State**
History-dependent problems.

**Examples:**
- Previous element/state
- Last k elements
- State machine transitions
- DP table evolution

---

## **3. Language-Specific State Tracking Patterns**Now let me provide you with the **mental training framework** and **pro tips**:

---

## **4. Mental Training: Building State-Tracking Intuition**

### **A. Visualization Techniques**

#### **1. The "Freeze Frame" Method**
At any moment during execution, mentally pause and ask:
- "What are ALL variable values right now?"
- "What constraints are currently satisfied?"
- "What work has been done vs. what remains?"

**Practice Drill:** Take a problem, write test input, and manually trace 3-5 iterations with a table:

```
Iteration | left | right | max_area | Decision
--------- | ---- | ----- | -------- | --------
   0      |  0   |  8    |    0     | Move left (height[0] < height[8])
   1      |  1   |  8    |   49     | Move right (height[1] > height[8])
   ...
```

**Neural Benefit:** This builds **working memory capacity** and trains your brain to hold multiple variables simultaneously (like a chess master visualizing 5 moves ahead).

---

#### **2. The "State Tree" Visualization**
For recursive problems, draw the state tree:

```
                    ("", open=0, close=0)
                   /                      \
            ("(", 1, 0)                 (invalid)
           /            \
    ("((", 2, 0)      ("()", 1, 1)
        |                |
       ...              ...
```

**Practice:** Before coding recursion, sketch the first 2-3 levels. This prevents **recursion blindness** (not seeing what the call stack actually does).

---

#### **3. The "Invariant Statement" Discipline**
Before every loop/recursion, write in comments:

```rust
// INVARIANT: [0..left) processed, (right..n] processed
// INVARIANT: window [start..end] has no duplicates
// INVARIANT: stack contains indices with no next greater found yet
```

**Why this works:** Forces **explicit reasoning** about what's true at each state. Top coders do this mentally without writing it.

---

### **B. Cognitive Training Exercises**

#### **Exercise 1: Blind Execution**
1. Take a solved problem
2. Cover the code
3. Given input, predict output by mentally executing
4. Reveal code, check if you were right

**Goal:** Train your brain to be a compiler. Builds **mental simulation accuracy**.

---

#### **Exercise 2: State Debugging Game**
1. Take buggy code (intentionally written or found online)
2. Without running it, identify the bug by tracing state
3. Predict what goes wrong and when

**Cognitive Principle:** Strengthens **error detection** circuits in your brain, similar to how proofreaders spot typos.

---

#### **Exercise 3: Multi-Variable Juggling**
Start with 2-pointer problems (2 variables), then progress to:
- 3 variables (start, end, pivot)
- 4+ variables (DP with multiple indices)
- Complex state (graph + stack + visited set)

**Progressive Overload:** Like weightlifting for your brain. Increases **cognitive load tolerance**.

---

### **C. Pro Tips from Top Competitive Programmers**

#### **Tip 1: The "State Checkpoint" Habit**
Every 5-10 lines of code, add a comment:
```python
# State here: left=?, right=?, max_value=?
```

When debugging, you instantly know where state diverged.

---

#### **Tip 2: The "One-Variable-Per-Line" Rule**
When state gets complex, update **one variable per statement**:

```python
# BAD: Cognitive overload
left, right, max_val = left + 1, right - 1, max(max_val, area)

# GOOD: Clear state transitions
max_val = max(max_val, area)
if height[left] < height[right]:
    left += 1
else:
    right -= 1
```

---

#### **Tip 3: The "Assert Your Assumptions" Technique**
Add assertions liberally during development:

```rust
assert!(left < right, "Pointers crossed!");
assert!(open >= close, "Invalid parentheses state!");
```

**Benefit:** Catches state corruption immediately rather than 50 lines later.

---

#### **Tip 4: The "State Snapshot" Debug Pattern**
Create a helper function:

```python
def print_state(locals_dict, label=""):
    print(f"[{label}] {', '.join(f'{k}={v}' for k, v in locals_dict.items())}")

# Usage
print_state(locals(), "After moving left pointer")
```

---

#### **Tip 5: Separate State Declaration from Logic**
Organize code in phases:

```rust
// Phase 1: Declare ALL state variables
let mut left = 0;
let mut right = n - 1;
let mut max_area = 0;

// Phase 2: State invariant loop
while left < right {
    // Phase 3: Compute transition
    // Phase 4: Update state
    // Phase 5: Make decision
}
```

**Cognitive Load Reduction:** Your brain processes "what exists" separately from "what changes."

---

### **D. Advanced: State Compression Thinking**

Learn to recognize when state can be **compressed**:

```python
# Uncompressed: O(n) space
dp = [[0] * n for _ in range(n)]

# Compressed: O(1) space (only need previous row)
prev_row = [0] * n
curr_row = [0] * n
```

**Mental Model:** "Do I really need the entire history, or just the last k steps?"

This thinking separates LeetCode mediums from hards.

---

## **5. Psychological Principles for Mastery**

### **Chunking**
Your brain can hold ~7 items in working memory. When state exceeds this, group variables into logical chunks:

```python
# Instead of: left, right, max_area, current_area, width, height
# Think: "pointer_state" (left, right) + "result_state" (max_area)
```

### **Deliberate Practice**
Don't just solve 100 problems randomly. Focus on:
1. **One pattern** (e.g., sliding window) for 10 problems
2. Then **increase complexity** (add constraints)
3. Then **mix patterns** (sliding window + DP)

**Study:** Ericsson's research shows experts practice at the edge of their ability, not in the comfort zone.

### **Metacognition**
After solving, ask:
- "What state did I forget to track initially?"
- "Where did my mental model break down?"
- "What pattern should I remember for next time?"

**Neurologically:** This reinforces the correct neural pathways while pruning incorrect ones.

---

## **6. The "State Audit" Checklist**

Before submitting any solution, audit:

```
☐ Are all variables initialized correctly?
☐ Do I maintain loop invariants?
☐ Am I properly restoring state in backtracking?
☐ Do boundary conditions (0, n-1, empty input) work?
☐ Is there hidden state (like global variables)?
☐ Do recursion base cases cover all states?
☐ Am I accidentally mutating shared state?
```

---

## **Final Mental Model: "State as a Story"**

Think of your algorithm as telling a story:
- **Characters:** Your variables
- **Plot:** State transitions
- **Setting:** Data structures
- **Climax:** When the answer is found
- **Resolution:** Return statement

Every story should be **coherent**—no character (variable) should suddenly disappear or behave out of character (violate invariants).

---

## **Your Path to Top 1%**

1. **Month 1-2:** Master basic state tracking (two pointers, sliding window) with the visualization techniques
2. **Month 3-4:** Add recursion state (backtracking, DFS/BFS)
3. **Month 5-6:** Complex state (DP, state machines, multi-dimensional states)
4. **Month 7+:** Competitive problems with 5+ state variables

**Daily Practice:**
- Solve 2 problems with **explicit state tracking**
- Trace 1 problem completely by hand
- Debug 1 piece of code by analyzing state evolution

You're training your brain like an athlete trains their body. **Consistency beats intensity.** The cognitive load that feels impossible today will be effortless in 6 months.

**Remember:** Even Gennady Korotkevich (6x ICPC world champion) started by struggling with state. The difference is he systematically trained these mental muscles.

You're on the path of mastery. Stay disciplined. 🔥

// ============================================
// RUST: State Management Patterns
// ============================================

use std::collections::{HashMap, HashSet, VecDeque};

// --------------------------------------------
// 1. TWO POINTERS - Container With Most Water
// --------------------------------------------
fn max_area(height: &[i32]) -> i32 {
    let mut left = 0;
    let mut right = height.len() - 1;
    let mut max_water = 0;
    
    // State invariant: [0..left) and (right..n) are explored
    while left < right {
        // Current state snapshot
        let width = (right - left) as i32;
        let h = height[left].min(height[right]);
        let area = width * h;
        
        max_water = max_water.max(area);
        
        // State transition decision
        if height[left] < height[right] {
            left += 1;  // Move pointer with smaller height
        } else {
            right -= 1;
        }
        
        // DEBUG: Uncomment to visualize state
        // eprintln!("left={}, right={}, area={}, max={}", left, right, area, max_water);
    }
    
    max_water
}

// --------------------------------------------
// 2. SLIDING WINDOW - Longest Substring Without Repeating
// --------------------------------------------
fn length_of_longest_substring(s: &str) -> usize {
    let chars: Vec<char> = s.chars().collect();
    let mut start = 0;
    let mut max_len = 0;
    let mut seen: HashMap<char, usize> = HashMap::new();
    
    // State: window [start..end] contains unique chars
    for end in 0..chars.len() {
        let ch = chars[end];
        
        // State update: if duplicate found, move start
        if let Some(&last_pos) = seen.get(&ch) {
            if last_pos >= start {
                start = last_pos + 1;
            }
        }
        
        seen.insert(ch, end);
        max_len = max_len.max(end - start + 1);
        
        // DEBUG: Current window state
        // eprintln!("Window[{}..{}]: {:?}, len={}", start, end, &chars[start..=end], end - start + 1);
    }
    
    max_len
}

// --------------------------------------------
// 3. RECURSION STATE - Generate Parentheses
// --------------------------------------------
fn generate_parentheses(n: i32) -> Vec<String> {
    let mut result = Vec::new();
    let mut current = String::new();
    backtrack(n, 0, 0, &mut current, &mut result);
    result
}

fn backtrack(n: i32, open: i32, close: i32, current: &mut String, result: &mut Vec<String>) {
    // State: (open, close) = count of '(' and ')' used
    // Invariant: close <= open <= n
    
    // Base case: valid complete state
    if current.len() == (2 * n) as usize {
        result.push(current.clone());
        return;
    }
    
    // State transition 1: Add '(' if possible
    if open < n {
        current.push('(');
        // DEBUG: eprintln!("Depth {}: Add '(' -> {}", open + close + 1, current);
        backtrack(n, open + 1, close, current, result);
        current.pop();  // Restore state
    }
    
    // State transition 2: Add ')' if valid
    if close < open {
        current.push(')');
        // DEBUG: eprintln!("Depth {}: Add ')' -> {}", open + close + 1, current);
        backtrack(n, open, close + 1, current, result);
        current.pop();  // Restore state
    }
}

// --------------------------------------------
// 4. DP STATE - Coin Change
// --------------------------------------------
fn coin_change(coins: &[i32], amount: i32) -> i32 {
    let amt = amount as usize;
    let mut dp = vec![i32::MAX; amt + 1];
    dp[0] = 0;
    
    // State: dp[i] = min coins to make amount i
    for i in 1..=amt {
        for &coin in coins {
            let c = coin as usize;
            if i >= c && dp[i - c] != i32::MAX {
                // State transition: use this coin
                dp[i] = dp[i].min(dp[i - c] + 1);
            }
        }
        // DEBUG: eprintln!("Amount {}: {} coins", i, dp[i]);
    }
    
    if dp[amt] == i32::MAX { -1 } else { dp[amt] }
}

// --------------------------------------------
// 5. GRAPH STATE - BFS with Level Tracking
// --------------------------------------------
fn bfs_with_levels(graph: &[Vec<usize>], start: usize) -> Vec<i32> {
    let n = graph.len();
    let mut distances = vec![-1; n];
    let mut queue = VecDeque::new();
    
    // Initial state
    queue.push_back((start, 0));
    distances[start] = 0;
    let mut visited = HashSet::new();
    visited.insert(start);
    
    while let Some((node, dist)) = queue.pop_front() {
        // Current state: at node with distance dist
        
        for &neighbor in &graph[node] {
            if !visited.contains(&neighbor) {
                // State transition: visit neighbor
                visited.insert(neighbor);
                distances[neighbor] = dist + 1;
                queue.push_back((neighbor, dist + 1));
                
                // DEBUG: eprintln!("Visit node {} at distance {}", neighbor, dist + 1);
            }
        }
    }
    
    distances
}

// --------------------------------------------
// 6. STACK STATE - Valid Parentheses
// --------------------------------------------
fn is_valid_parentheses(s: &str) -> bool {
    let mut stack = Vec::new();
    let pairs = [('(', ')'), ('{', '}'), ('[', ']')];
    
    for ch in s.chars() {
        match ch {
            '(' | '{' | '[' => {
                // State: push opening bracket
                stack.push(ch);
            }
            ')' | '}' | ']' => {
                // State check: does top match?
                if let Some(&top) = stack.last() {
                    let matches = pairs.iter().any(|&(open, close)| open == top && close == ch);
                    if matches {
                        stack.pop();
                    } else {
                        return false;
                    }
                } else {
                    return false;
                }
            }
            _ => {}
        }
        // DEBUG: eprintln!("After '{}': stack = {:?}", ch, stack);
    }
    
    stack.is_empty()
}

// --------------------------------------------
// 7. STATE MACHINE - Finite Automaton for String Matching
// --------------------------------------------
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum State {
    Start,
    Matching(usize),  // Matched pattern[0..usize]
    Failed,
}

fn pattern_match_fsm(text: &str, pattern: &str) -> bool {
    let pattern: Vec<char> = pattern.chars().collect();
    let mut state = State::Start;
    
    for ch in text.chars() {
        // State transition based on current state + input
        state = match state {
            State::Start => {
                if ch == pattern[0] {
                    if pattern.len() == 1 {
                        return true;
                    }
                    State::Matching(1)
                } else {
                    State::Start
                }
            }
            State::Matching(pos) => {
                if ch == pattern[pos] {
                    if pos + 1 == pattern.len() {
                        return true;
                    }
                    State::Matching(pos + 1)
                } else if ch == pattern[0] {
                    State::Matching(1)
                } else {
                    State::Start
                }
            }
            State::Failed => State::Failed,
        };
        
        // DEBUG: eprintln!("Char '{}': state = {:?}", ch, state);
    }
    
    false
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_state_tracking() {
        assert_eq!(max_area(&[1,8,6,2,5,4,8,3,7]), 49);
        assert_eq!(length_of_longest_substring("abcabcbb"), 3);
        assert_eq!(generate_parentheses(3).len(), 5);
        assert_eq!(coin_change(&[1, 2, 5], 11), 3);
        assert!(is_valid_parentheses("()[]{}"));
        assert!(pattern_match_fsm("hello world", "world"));
    }
}

// ============================================
// C/C++: State Management Patterns
// ============================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <stdbool.h>

#ifdef __cplusplus
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <queue>
#include <stack>
#include <algorithm>
#include <iostream>
using namespace std;
#endif

// --------------------------------------------
// 1. C: TWO POINTERS - Manual State Tracking
// --------------------------------------------
typedef struct {
    int left;
    int right;
    int max_value;
    int iterations;
} TwoPointerState;

void print_state_c(TwoPointerState* state) {
    printf("[L=%d, R=%d, Max=%d, Iter=%d]\n", 
           state->left, state->right, state->max_value, state->iterations);
}

int maxArea_c(int* height, int heightSize) {
    TwoPointerState state = {
        .left = 0,
        .right = heightSize - 1,
        .max_value = 0,
        .iterations = 0
    };
    
    while (state.left < state.right) {
        state.iterations++;
        
        int width = state.right - state.left;
        int h = (height[state.left] < height[state.right]) ? 
                 height[state.left] : height[state.right];
        int area = width * h;
        
        state.max_value = (area > state.max_value) ? area : state.max_value;
        
        // DEBUG: Uncomment to track state
        // print_state_c(&state);
        
        if (height[state.left] < height[state.right]) {
            state.left++;
        } else {
            state.right--;
        }
    }
    
    return state.max_value;
}

// --------------------------------------------
// 2. C: SLIDING WINDOW WITH HASH MAP
// --------------------------------------------
int lengthOfLongestSubstring_c(char* s) {
    int n = strlen(s);
    if (n == 0) return 0;
    
    int start = 0, max_len = 0;
    int char_index[256]; // State: last position of each ASCII char
    memset(char_index, -1, sizeof(char_index));
    
    for (int end = 0; end < n; end++) {
        unsigned char c = s[end];
        
        // State check: duplicate found?
        if (char_index[c] >= start) {
            start = char_index[c] + 1;
        }
        
        // Update state
        char_index[c] = end;
        int current_len = end - start + 1;
        max_len = (current_len > max_len) ? current_len : max_len;
        
        // DEBUG: Window state
        // printf("Window[%d:%d], len=%d\n", start, end+1, current_len);
    }
    
    return max_len;
}

// --------------------------------------------
// 3. C: RECURSION STATE WITH MANUAL STACK
// --------------------------------------------
typedef struct {
    char* current;
    int open;
    int close;
    int capacity;
} RecursionState;

void backtrack_c(int n, RecursionState* state, char** result, int* result_size) {
    int len = strlen(state->current);
    
    // DEBUG: Track depth
    // printf("%*sState: current='%s', open=%d, close=%d\n", 
    //        len, "", state->current, state->open, state->close);
    
    if (len == 2 * n) {
        result[*result_size] = strdup(state->current);
        (*result_size)++;
        return;
    }
    
    // Try adding '('
    if (state->open < n) {
        int old_len = len;
        state->current[len] = '(';
        state->current[len + 1] = '\0';
        state->open++;
        
        backtrack_c(n, state, result, result_size);
        
        // Restore state
        state->current[old_len] = '\0';
        state->open--;
    }
    
    // Try adding ')'
    if (state->close < state->open) {
        int old_len = len;
        state->current[len] = ')';
        state->current[len + 1] = '\0';
        state->close++;
        
        backtrack_c(n, state, result, result_size);
        
        // Restore state
        state->current[old_len] = '\0';
        state->close--;
    }
}

char** generateParenthesis_c(int n, int* returnSize) {
    char** result = (char**)malloc(10000 * sizeof(char*));
    *returnSize = 0;
    
    RecursionState state;
    state.current = (char*)malloc((2 * n + 1) * sizeof(char));
    state.current[0] = '\0';
    state.open = 0;
    state.close = 0;
    state.capacity = 2 * n;
    
    backtrack_c(n, &state, result, returnSize);
    
    free(state.current);
    return result;
}

// --------------------------------------------
// 4. C++: DP STATE EVOLUTION
// --------------------------------------------
#ifdef __cplusplus
int coinChange(vector<int>& coins, int amount) {
    // State: dp[i] = min coins for amount i
    vector<int> dp(amount + 1, INT_MAX);
    dp[0] = 0;
    
    for (int i = 1; i <= amount; i++) {
        for (int coin : coins) {
            if (i >= coin && dp[i - coin] != INT_MAX) {
                int old_val = dp[i];
                dp[i] = min(dp[i], dp[i - coin] + 1);
                
                // DEBUG: Track changes
                // if (dp[i] != old_val) {
                //     cout << "dp[" << i << "]: " << old_val << " -> " 
                //          << dp[i] << " (using coin " << coin << ")\n";
                // }
            }
        }
    }
    
    return (dp[amount] == INT_MAX) ? -1 : dp[amount];
}

// --------------------------------------------
// 5. C++: GRAPH BFS WITH STATE TRACKING
// --------------------------------------------
unordered_map<int, int> bfsWithLevels(unordered_map<int, vector<int>>& graph, int start) {
    unordered_map<int, int> distances;
    unordered_set<int> visited;
    queue<pair<int, int>> q;
    
    q.push({start, 0});
    visited.insert(start);
    distances[start] = 0;
    
    int iteration = 0;
    
    while (!q.empty()) {
        iteration++;
        auto [node, dist] = q.front();
        q.pop();
        
        // DEBUG: Current state
        // cout << "Iter " << iteration << ": Visit node " << node 
        //      << " at dist " << dist << "\n";
        // cout << "  Queue size: " << q.size() << "\n";
        
        for (int neighbor : graph[node]) {
            if (visited.find(neighbor) == visited.end()) {
                visited.insert(neighbor);
                distances[neighbor] = dist + 1;
                q.push({neighbor, dist + 1});
            }
        }
    }
    
    return distances;
}

// --------------------------------------------
// 6. C++: STACK STATE - Valid Parentheses
// --------------------------------------------
bool isValid(string s) {
    stack<char> stk;
    unordered_map<char, char> pairs = {
        {'(', ')'},
        {'{', '}'},
        {'[', ']'}
    };
    
    for (int i = 0; i < s.length(); i++) {
        char c = s[i];
        
        // DEBUG: State before
        // cout << "Step " << i << ": char='" << c << "', stack size=" 
        //      << stk.size() << "\n";
        
        if (pairs.count(c)) {
            stk.push(c);
        } else {
            if (stk.empty() || pairs[stk.top()] != c) {
                return false;
            }
            stk.pop();
        }
    }
    
    return stk.empty();
}

// --------------------------------------------
// 7. C++: MONOTONIC STACK
// --------------------------------------------
vector<int> nextGreaterElement(vector<int>& nums) {
    int n = nums.size();
    vector<int> result(n, -1);
    stack<int> stk; // Stack of indices
    
    for (int i = 0; i < n; i++) {
        while (!stk.empty() && nums[stk.top()] < nums[i]) {
            int idx = stk.top();
            stk.pop();
            result[idx] = nums[i];
            
            // DEBUG: Found next greater
            // cout << "nums[" << idx << "]=" << nums[idx] 
            //      << " -> next greater = " << nums[i] << "\n";
        }
        
        stk.push(i);
    }
    
    return result;
}

// --------------------------------------------
// 8. C++: STATE MACHINE
// --------------------------------------------
enum FSMState { START, MATCHING, ACCEPT, REJECT };

class StateMachine {
private:
    FSMState state;
    int match_count;
    vector<string> transitions;
    
public:
    StateMachine() : state(START), match_count(0) {}
    
    void transition(char c, const string& pattern) {
        FSMState old_state = state;
        
        if (match_count == pattern.length()) {
            state = ACCEPT;
        } else if (match_count < pattern.length() && pattern[match_count] == c) {
            match_count++;
            state = MATCHING;
        } else if (c == pattern[0]) {
            match_count = 1;
            state = MATCHING;
        } else {
            match_count = 0;
            state = START;
        }
        
        string t = "State " + to_string(old_state) + " --(" + c + 
                   ")--> State " + to_string(state);
        transitions.push_back(t);
    }
    
    bool isAccepted() const { 
        return state == ACCEPT || match_count > 0; 
    }
    
    int getMatchCount() const { return match_count; }
};

bool patternMatch(const string& text, const string& pattern) {
    StateMachine fsm;
    
    for (char c : text) {
        fsm.transition(c, pattern);
        if (fsm.getMatchCount() == pattern.length()) {
            return true;
        }
    }
    
    return false;
}

// --------------------------------------------
// 9. C++: MULTI-STATE DP
// --------------------------------------------
int maxProfitKTransactions(vector<int>& prices, int k) {
    if (prices.empty()) return 0;
    
    int n = prices.size();
    // State: dp[day][transactions][holding]
    vector<vector<vector<int>>> dp(n, vector<vector<int>>(k + 1, vector<int>(2, 0)));
    
    // Initialize: buy on day 0
    for (int j = 0; j <= k; j++) {
        dp[0][j][1] = -prices[0];
    }
    
    for (int i = 1; i < n; i++) {
        for (int j = 0; j <= k; j++) {
            // Not holding
            dp[i][j][0] = max(dp[i-1][j][0], dp[i-1][j][1] + prices[i]);
            
            // Holding
            if (j > 0) {
                dp[i][j][1] = max(dp[i-1][j][1], dp[i-1][j-1][0] - prices[i]);
            }
        }
    }
    
    return dp[n-1][k][0];
}
#endif

// --------------------------------------------
// MAIN - TESTING
// --------------------------------------------
int main() {
    // C tests
    int heights[] = {1, 8, 6, 2, 5, 4, 8, 3, 7};
    printf("C: Max Area = %d\n", maxArea_c(heights, 9));
    
    char str[] = "abcabcbb";
    printf("C: Longest Substring = %d\n", lengthOfLongestSubstring_c(str));
    
    int result_size;
    char** parens = generateParenthesis_c(3, &result_size);
    printf("C: Generated %d parentheses combinations\n", result_size);
    for (int i = 0; i < result_size; i++) {
        free(parens[i]);
    }
    free(parens);
    
#ifdef __cplusplus
    // C++ tests
    vector<int> coins = {1, 2, 5};
    cout << "C++: Coin Change = " << coinChange(coins, 11) << "\n";
    
    unordered_map<int, vector<int>> graph = {
        {0, {1, 2}},
        {1, {3}},
        {2, {3}}
    };
    auto distances = bfsWithLevels(graph, 0);
    cout << "C++: BFS computed " << distances.size() << " distances\n";
    
    cout << "C++: Valid Parens = " << isValid("()[]{}") << "\n";
    
    vector<int> nums = {2, 1, 2, 4, 3};
    auto nge = nextGreaterElement(nums);
    cout << "C++: Next Greater Elements computed\n";
    
    cout << "C++: Pattern Match = " << patternMatch("hello world", "world") << "\n";
    
    vector<int> prices = {3, 2, 6, 5, 0, 3};
    cout << "C++: Max Profit = " << maxProfitKTransactions(prices, 2) << "\n";
#endif
    
    return 0;
}

# The Art of Intelligent Brute Force: From Chaos to Clarity

You've asked one of the **most profound questions** in competitive programming. Let me reveal what top problem solvers actually do—it's not what most people think.

---

## **1. What Top Problem Solvers ACTUALLY Do**

### **The Hidden Truth:**
**Elite problem solvers DON'T know every algorithm.** They have something more powerful: **pattern recognition + systematic exploration.**

Here's the real process:

```
Problem → Understand → Simplify → Brute Force → Observe Pattern → Optimize
   ↓           ↓            ↓           ↓              ↓              ↓
 Parse     Extract      Reduce to   Generate      Find          Improve
  input    essence      toy case    solutions   structure      complexity
```

**Key Insight:** Brute force is a **discovery tool**, not a solution method. It's like a microscope that reveals the problem's hidden structure.

---

## **2. Strategic Fuzzing & Brute Force: The Framework**

### **A. The "Shrink and Conquer" Method**

Instead of solving the full problem, solve **progressively smaller versions**:---

## **3. Finding & Fixing Logical Bugs: The Systematic Approach**---

## **4. Do You Need to Know Every Algorithm? (The Truth)**

### **NO. You need ~20 core patterns that cover 95% of problems.**

Here's what's **actually mandatory**:---

## **5. The Efficiency Framework: When to Brute Force, When to Optimize**---

## **6. The Master's Mindset: Cognitive Techniques**

### **A. The "Explain to a 5-Year-Old" Test**
If you can't explain your algorithm simply, you don't understand it deeply enough.

**Practice:** After solving each problem, explain it aloud as if teaching a child:
- "We have two fingers pointing at the array..."
- "When we find a bigger number, we move the right finger..."

This forces **conceptual clarity** over rote memorization.

---

### **B. The "Derive, Don't Memorize" Principle**

Instead of memorizing:
```python
dp[i][j] = dp[i-1][j-1] + 1 if s1[i] == s2[j] else max(dp[i-1][j], dp[i][j-1])
```

Understand the **logic**:
- "If characters match, extend previous solution by 1"
- "If not, take the best solution without one character"

**Exercise:** Delete all your solved code. Reimplement from memory 24 hours later. Can't do it? You memorized, didn't understand.

---

### **C. The "Bug Hypothesis" Method**

When debugging, form explicit hypotheses:

❌ "Something's wrong with my loop"
✅ "Hypothesis: The pointer is going out of bounds when processing the last element because I'm using `i+1` without checking `i < n-1`"

Then **test the hypothesis**:
```python
if i == n-1:
    print(f"At last element: i={i}, trying to access i+1={i+1}, but n={n}")
```

This is how scientists think. Apply it to code.

---

### **D. The "Constraint as Hint" Decoder**

Problem constraints are **direct hints** about the algorithm:

| Constraint | Hidden Hint | Algorithm |
|------------|-------------|-----------|
| n ≤ 20 | "Try exponential" | Backtracking, DFS |
| n ≤ 100 | "Quadratic is fine" | Nested loops, simple DP |
| n ≤ 10⁵ | "Must be efficient" | Hash map, two pointers |
| All positive integers | "Greedy might work" | Greedy algorithm |
| "Find minimum/maximum" | "Likely DP or greedy" | Optimization problem |
| Graph with cycles | "Need visited set" | DFS with backtracking |

**Practice:** Before solving, read constraints and predict the complexity class.

---

## **7. The Ultimate Question: How Do You Actually Get Good?**

### **The 10,000 Hour Myth is Wrong**

It's not about time. It's about **deliberate practice**:

1. **Work at the edge of your ability** (not too easy, not impossible)
2. **Get immediate feedback** (run tests, check solutions)
3. **Focus on weaknesses** (not solving the same pattern 50 times)

### **The Real Path:**

```
Week 1-2:   Solve 20 easy problems → Pattern recognition
Week 3-4:   Solve 30 medium problems → Application
Week 5-6:   Solve 20 hard problems → Synthesis
Week 7-8:   Contest participation → Time pressure
Week 9-10:  Deep dives (implement data structures from scratch)
Week 11-12: Teach others (blog posts, YouTube, mentoring)
```

**Repeat this cycle** for different topics. You'll be top 5% in 6 months, top 1% in 12-18 months.

---

## **8. Pro Tips from World Champions**

### **From Gennady Korotkevich (Tourist):**
> "I don't think about which algorithm to use. I think about the problem structure, and the algorithm emerges naturally."

**Takeaway:** Think in **problems**, not **solutions**.

---

### **From Petr Mitrichev:**
> "When stuck, solve smaller versions. If n=1000, solve for n=5 by hand."

**Takeaway:** **Shrink the problem** until you can see the pattern.

---

### **From Errichto:**
> "Brute force is not failure—it's exploration. Don't be afraid to write O(n³) code first."

**Takeaway:** **Permission to be inefficient** initially.

---

## **Final Answer to Your Questions**

### **Q: How do problem solvers actually do fuzzing/brute force?**
**A:** They use it as a **pattern discovery tool**, not a final solution. Small inputs reveal structure.

### **Q: How does this help?**
**A:** It exposes the **hidden mathematical structure** of the problem. Once you see the pattern, optimization is obvious.

### **Q: How to do this efficiently in different situations?**
**A:** Use the **constraint-driven framework** I showed. n ≤ 10? Brute force everything. n ≤ 10⁵? Must be O(n log n) or better.

### **Q: How to find and fix logical bugs easily?**
**A:** **Binary search the bug location** + **differential testing** (compare against brute force) + **invariant assertions**.

### **Q: Is it mandatory to know every algorithm?**
**A:** **NO.** Know ~20 core patterns deeply. Everything else can be learned just-in-time.

### **Q: How to learn those quickly?**
**A:** **Implementation-first learning**. Watch 10-min video → implement immediately → solve 3 problems → move on.

### **Q: What's actually mandatory?**
**A:** **Tiers 0-2** from my roadmap (arrays, hash maps, stacks, queues, trees, graphs, basic DP). This covers 80% of problems.

---

## **Your Action Plan Starting Tomorrow**

**Day 1-7:** Implement these from scratch (no looking at solutions):
- Two pointers (3 problems)
- Sliding window (3 problems)
- Hash map (3 problems)
- Binary search (3 problems)

**Day 8-14:** Add stack/queue (5 problems) + linked lists (3 problems)

**Day 15-30:** Tree traversals (10 problems) + graph DFS/BFS (10 problems)

**Day 31-60:** 1D DP (20 problems) + 2D DP (20 problems)

**Day 61-90:** Mix everything + contests

After 90 days, you'll be **unrecognizable** compared to today.

---

**Remember:** The difference between you and the top 1% isn't talent. It's **systematic practice** with **deliberate reflection**.

You already have the monk mindset. Now you have the framework.

**Go build your mastery.** 🔥

// ============================================
// STRATEGIC BRUTE FORCE FRAMEWORK
// ============================================

use std::collections::{HashMap, HashSet};
use std::time::Instant;

/// Framework for discovering patterns through controlled brute force
pub struct BruteForceFramework;

impl BruteForceFramework {
    /// Step 1: Generate small test cases to understand the pattern
    pub fn explore_pattern() {
        println!("=== PATTERN EXPLORATION ===\n");
        
        // Example: Longest Palindromic Substring
        // Start with n=1,2,3,4,5 to find pattern
        
        let test_cases = vec![
            "a",      // n=1
            "aa",     // n=2
            "aba",    // n=3
            "abba",   // n=4
            "racecar" // n=7
        ];
        
        for s in test_cases {
            let result = Self::brute_force_palindrome(s);
            println!("Input: '{}' → Longest palindrome: '{}'", s, result);
        }
        
        println!("\n📊 OBSERVATION: Palindromes have a center! This suggests expansion from center.\n");
    }
    
    /// Brute force: Check all substrings O(n³)
    fn brute_force_palindrome(s: &str) -> String {
        let chars: Vec<char> = s.chars().collect();
        let n = chars.len();
        let mut longest = "";
        
        // Generate ALL substrings
        for i in 0..n {
            for j in i..n {
                let substring: String = chars[i..=j].iter().collect();
                if Self::is_palindrome(&substring) && substring.len() > longest.len() {
                    longest = Box::leak(substring.into_boxed_str());
                }
            }
        }
        
        longest.to_string()
    }
    
    fn is_palindrome(s: &str) -> bool {
        let chars: Vec<char> = s.chars().collect();
        let n = chars.len();
        for i in 0..n/2 {
            if chars[i] != chars[n-1-i] {
                return false;
            }
        }
        true
    }
    
    /// Step 2: Compare brute force vs optimized
    pub fn compare_approaches() {
        println!("=== APPROACH COMPARISON ===\n");
        
        let test = "babad";
        
        // Brute Force: O(n³)
        let start = Instant::now();
        let result1 = Self::brute_force_palindrome(test);
        let time1 = start.elapsed();
        
        // Optimized: Expand from center O(n²)
        let start = Instant::now();
        let result2 = Self::optimized_palindrome(test);
        let time2 = start.elapsed();
        
        println!("Brute Force: '{}' in {:?}", result1, time1);
        println!("Optimized:   '{}' in {:?}", result2, time2);
        println!("\n💡 INSIGHT: Eliminated redundant palindrome checks\n");
    }
    
    fn optimized_palindrome(s: &str) -> String {
        let chars: Vec<char> = s.chars().collect();
        if chars.is_empty() { return String::new(); }
        
        let mut start = 0;
        let mut max_len = 1;
        
        for i in 0..chars.len() {
            // Odd length palindromes
            let len1 = Self::expand_around_center(&chars, i, i);
            // Even length palindromes
            let len2 = Self::expand_around_center(&chars, i, i + 1);
            
            let len = len1.max(len2);
            if len > max_len {
                max_len = len;
                start = i - (len - 1) / 2;
            }
        }
        
        chars[start..start + max_len].iter().collect()
    }
    
    fn expand_around_center(chars: &[char], mut left: usize, mut right: usize) -> usize {
        while right < chars.len() && chars[left] == chars[right] {
            if left == 0 { break; }
            left -= 1;
            right += 1;
        }
        
        if left > 0 || right >= chars.len() || chars[left] != chars[right] {
            if left == 0 && right < chars.len() && chars[left] == chars[right] {
                right - left + 1
            } else {
                right - left - 1
            }
        } else {
            right - left + 1
        }
    }
    
    /// Step 3: Generate edge cases systematically
    pub fn generate_edge_cases() {
        println!("=== EDGE CASE GENERATION ===\n");
        
        let edge_cases = vec![
            ("", "Empty string"),
            ("a", "Single character"),
            ("ab", "No palindrome > 1"),
            ("aa", "All same"),
            ("aaaa", "All same, longer"),
            ("abcba", "Odd palindrome"),
            ("abba", "Even palindrome"),
            ("abacabad", "Multiple palindromes"),
        ];
        
        for (input, description) in edge_cases {
            let result = Self::optimized_palindrome(input);
            println!("{:20} → '{}'", description, result);
        }
        println!();
    }
    
    /// Step 4: Fuzzing - Generate random inputs to find bugs
    pub fn fuzz_testing() {
        println!("=== FUZZ TESTING ===\n");
        
        use rand::Rng;
        let mut rng = rand::thread_rng();
        
        let mut bug_count = 0;
        
        for i in 0..100 {
            // Generate random string
            let len = rng.gen_range(1..=10);
            let s: String = (0..len)
                .map(|_| rng.gen_range(b'a'..=b'd') as char)
                .collect();
            
            let brute = Self::brute_force_palindrome(&s);
            let optimized = Self::optimized_palindrome(&s);
            
            if brute != optimized {
                println!("🐛 BUG FOUND!");
                println!("   Input: '{}'", s);
                println!("   Brute force: '{}'", brute);
                println!("   Optimized:   '{}'", optimized);
                bug_count += 1;
            }
        }
        
        if bug_count == 0 {
            println!("✅ Passed 100 random tests!");
        } else {
            println!("❌ Found {} bugs", bug_count);
        }
        println!();
    }
}

// ============================================
// TECHNIQUE 2: Brute Force for Discovery
// ============================================

/// Example: Discovering DP structure through brute force
pub struct DPDiscovery;

impl DPDiscovery {
    /// Fibonacci - brute force reveals overlapping subproblems
    pub fn discover_fibonacci_structure() {
        println!("=== DISCOVERING DP STRUCTURE ===\n");
        
        let mut call_graph = HashMap::new();
        
        fn fib_trace(n: usize, cache: &mut HashMap<usize, usize>) -> usize {
            *cache.entry(n).or_insert(0) += 1;
            
            if n <= 1 { return n; }
            fib_trace(n - 1, cache) + fib_trace(n - 2, cache)
        }
        
        for n in 1..=6 {
            let mut cache = HashMap::new();
            let result = fib_trace(n, &mut cache);
            
            println!("fib({}) = {}", n, result);
            println!("  Subproblems called:");
            for i in 0..=n {
                if let Some(&count) = cache.get(&i) {
                    println!("    fib({}) called {} times", i, count);
                }
            }
            println!();
        }
        
        println!("💡 INSIGHT: fib(3) computed multiple times → Use memoization!\n");
    }
    
    /// Coin change - brute force shows optimal substructure
    pub fn discover_coin_change_structure() {
        println!("=== COIN CHANGE DISCOVERY ===\n");
        
        let coins = vec![1, 2, 5];
        let amount = 11;
        
        fn brute_force(coins: &[i32], amount: i32, memo: &mut HashMap<i32, i32>) -> i32 {
            if amount == 0 { return 0; }
            if amount < 0 { return -1; }
            if let Some(&cached) = memo.get(&amount) { return cached; }
            
            let mut min_coins = i32::MAX;
            
            for &coin in coins {
                let sub_result = brute_force(coins, amount - coin, memo);
                if sub_result != -1 {
                    min_coins = min_coins.min(sub_result + 1);
                }
            }
            
            let result = if min_coins == i32::MAX { -1 } else { min_coins };
            memo.insert(amount, result);
            result
        }
        
        let mut memo = HashMap::new();
        let result = brute_force(&coins, amount, &mut memo);
        
        println!("Minimum coins for {} = {}", amount, result);
        println!("\nMemoization table (discovered subproblems):");
        
        let mut sorted: Vec<_> = memo.iter().collect();
        sorted.sort_by_key(|&(k, _)| k);
        
        for (amt, coins) in sorted {
            println!("  amount {} → {} coins", amt, coins);
        }
        
        println!("\n💡 INSIGHT: Build table bottom-up for O(n) space!\n");
    }
}

// ============================================
// TECHNIQUE 3: Property-Based Testing
// ============================================

pub struct PropertyTesting;

impl PropertyTesting {
    /// Test invariants that MUST hold
    pub fn test_sorting_properties() {
        println!("=== PROPERTY-BASED TESTING ===\n");
        
        fn quicksort(arr: &mut [i32]) {
            if arr.len() <= 1 { return; }
            
            let pivot = arr[arr.len() / 2];
            let mut left = 0;
            let mut right = arr.len() - 1;
            
            loop {
                while arr[left] < pivot { left += 1; }
                while arr[right] > pivot { right -= 1; }
                
                if left >= right { break; }
                
                arr.swap(left, right);
                left += 1;
                right -= 1;
            }
            
            let mid = left;
            if mid > 0 {
                quicksort(&mut arr[..mid]);
            }
            if mid < arr.len() {
                quicksort(&mut arr[mid..]);
            }
        }
        
        fn check_sorted(arr: &[i32]) -> bool {
            for i in 0..arr.len()-1 {
                if arr[i] > arr[i+1] { return false; }
            }
            true
        }
        
        fn check_permutation(original: &[i32], sorted: &[i32]) -> bool {
            let mut o = original.to_vec();
            let mut s = sorted.to_vec();
            o.sort();
            s.sort();
            o == s
        }
        
        // Property 1: Output must be sorted
        // Property 2: Output must be permutation of input
        // Property 3: Length must be preserved
        
        let test_cases = vec![
            vec![3, 1, 4, 1, 5, 9, 2, 6],
            vec![5, 4, 3, 2, 1],
            vec![1],
            vec![],
            vec![2, 2, 2, 2],
        ];
        
        for mut test in test_cases {
            let original = test.clone();
            quicksort(&mut test);
            
            let sorted = check_sorted(&test);
            let perm = check_permutation(&original, &test);
            let len = original.len() == test.len();
            
            println!("Input:  {:?}", original);
            println!("Output: {:?}", test);
            println!("  ✓ Sorted: {}", sorted);
            println!("  ✓ Permutation: {}", perm);
            println!("  ✓ Length preserved: {}", len);
            
            if !sorted || !perm || !len {
                println!("  ❌ BUG DETECTED!");
            }
            println!();
        }
    }
}

// ============================================
// MAIN - RUN ALL TECHNIQUES
// ============================================

fn main() {
    BruteForceFramework::explore_pattern();
    BruteForceFramework::compare_approaches();
    BruteForceFramework::generate_edge_cases();
    
    // Note: Uncomment if rand crate is available
    // BruteForceFramework::fuzz_testing();
    
    DPDiscovery::discover_fibonacci_structure();
    DPDiscovery::discover_coin_change_structure();
    
    PropertyTesting::test_sorting_properties();
}

"""
============================================
SYSTEMATIC BUG HUNTING FRAMEWORK
============================================
"""

import random
from typing import Any, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum

# ============================================
# TECHNIQUE 1: Binary Search for Bug Location
# ============================================

class BugHunter:
    """Use binary search to find WHERE the bug occurs"""
    
    @staticmethod
    def trace_execution(func: Callable, *args) -> List[dict]:
        """Capture state at each step"""
        trace = []
        
        # Example: Binary search with bug
        def buggy_binary_search(arr, target):
            left, right = 0, len(arr)  # BUG: should be len(arr) - 1
            
            while left <= right:
                # Capture state
                trace.append({
                    'left': left,
                    'right': right,
                    'left_val': arr[left] if left < len(arr) else None,
                    'right_val': arr[right] if right < len(arr) else None
                })
                
                mid = (left + right) // 2
                
                if mid >= len(arr):
                    trace.append({'ERROR': 'Index out of bounds', 'mid': mid})
                    return -1
                
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1
            
            return -1
        
        result = buggy_binary_search(*args)
        return trace, result
    
    @staticmethod
    def print_trace(trace: List[dict]):
        """Visualize execution trace"""
        print("EXECUTION TRACE:")
        for i, state in enumerate(trace):
            print(f"  Step {i}: {state}")
        print()
    
    @staticmethod
    def binary_search_bug_location():
        """Find bug by analyzing trace"""
        print("=== BINARY SEARCH FOR BUG LOCATION ===\n")
        
        arr = [1, 2, 3, 4, 5]
        target = 3
        
        trace, result = BugHunter.trace_execution(None, arr, target)
        BugHunter.print_trace(trace)
        
        print("💡 ANALYSIS:")
        print("   Step 0: right=5 but len(arr)=5 → arr[5] out of bounds!")
        print("   FIX: right should be len(arr) - 1")
        print()


# ============================================
# TECHNIQUE 2: Differential Testing
# ============================================

class DifferentialTesting:
    """Compare two implementations to find bugs"""
    
    @staticmethod
    def test_against_reference():
        print("=== DIFFERENTIAL TESTING ===\n")
        
        def reference_sort(arr):
            """Known correct implementation"""
            return sorted(arr)
        
        def optimized_sort(arr):
            """Implementation to test (intentionally buggy)"""
            result = arr.copy()
            n = len(result)
            
            for i in range(n):
                for j in range(n - i):  # BUG: should be n - i - 1
                    if j + 1 < n and result[j] > result[j + 1]:
                        result[j], result[j + 1] = result[j + 1], result[j]
            
            return result
        
        # Generate random test cases
        bugs_found = []
        
        for _ in range(100):
            test = [random.randint(0, 20) for _ in range(random.randint(1, 10))]
            
            ref_result = reference_sort(test)
            opt_result = optimized_sort(test)
            
            if ref_result != opt_result:
                bugs_found.append({
                    'input': test,
                    'expected': ref_result,
                    'got': opt_result
                })
        
        if bugs_found:
            print(f"🐛 Found {len(bugs_found)} bugs!")
            print(f"   First failure: {bugs_found[0]}")
        else:
            print("✅ All tests passed")
        print()


# ============================================
# TECHNIQUE 3: Invariant Checking
# ============================================

class InvariantChecker:
    """Verify invariants at each step"""
    
    @staticmethod
    def check_sliding_window():
        print("=== INVARIANT CHECKING ===\n")
        
        def max_sum_subarray_buggy(arr, k):
            """Maximum sum of subarray of size k (with bugs)"""
            if len(arr) < k:
                return None
            
            window_sum = sum(arr[:k])
            max_sum = window_sum
            
            # Invariant: window_sum = sum of current k elements
            
            for i in range(k, len(arr)):
                # BUG: forgot to subtract arr[i-k]
                window_sum += arr[i]
                
                # Check invariant
                expected_sum = sum(arr[i-k+1:i+1])
                if window_sum != expected_sum:
                    print(f"❌ INVARIANT VIOLATED at i={i}")
                    print(f"   window_sum={window_sum}, expected={expected_sum}")
                    print(f"   Window: {arr[i-k+1:i+1]}")
                    return None
                
                max_sum = max(max_sum, window_sum)
            
            return max_sum
        
        result = max_sum_subarray_buggy([1, 2, 3, 4, 5], 3)
        
        print("\n💡 FIX: Add 'window_sum -= arr[i-k]' to maintain invariant")
        print()


# ============================================
# TECHNIQUE 4: Minimize Failing Test Case
# ============================================

class TestCaseMinimizer:
    """Shrink failing test to smallest example"""
    
    @staticmethod
    def minimize_test():
        print("=== TEST CASE MINIMIZATION ===\n")
        
        def has_bug(arr):
            """Function with subtle bug"""
            # Bug: fails when array has duplicates at specific positions
            for i in range(len(arr) - 1):
                if arr[i] == arr[i+1] and i > 0 and arr[i-1] > arr[i]:
                    return True  # Incorrectly returns True
            return False
        
        # Large failing test case
        failing_test = [5, 3, 3, 7, 2, 2, 9]
        
        print(f"Original failing test: {failing_test}")
        print(f"Length: {len(failing_test)}")
        print()
        
        # Strategy: Remove elements one by one
        minimal = failing_test.copy()
        
        for i in range(len(failing_test)):
            # Try removing element at position i
            test = minimal[:i] + minimal[i+1:]
            
            if test and has_bug(test):
                minimal = test
                print(f"  Reduced to: {minimal} (length {len(minimal)})")
        
        print(f"\n✅ Minimal failing test: {minimal}")
        print(f"   Length: {len(minimal)}")
        print()


# ============================================
# TECHNIQUE 5: Assertion-Driven Debugging
# ============================================

class AssertionDebugger:
    """Use strategic assertions to catch bugs early"""
    
    @staticmethod
    def demo_assertions():
        print("=== ASSERTION-DRIVEN DEBUGGING ===\n")
        
        def binary_search_with_assertions(arr, target):
            """Binary search with comprehensive assertions"""
            assert arr == sorted(arr), "Array must be sorted"
            
            left, right = 0, len(arr) - 1
            
            while left <= right:
                # Invariant assertions
                assert 0 <= left < len(arr), f"left={left} out of bounds"
                assert 0 <= right < len(arr), f"right={right} out of bounds"
                assert left <= right + 1, f"Pointers crossed: left={left}, right={right}"
                
                mid = (left + right) // 2
                
                assert 0 <= mid < len(arr), f"mid={mid} out of bounds"
                
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1
            
            return -1
        
        # Test with assertions
        try:
            result = binary_search_with_assertions([1, 3, 5, 7, 9], 5)
            print(f"✅ Found at index: {result}")
        except AssertionError as e:
            print(f"❌ Assertion failed: {e}")
        
        print()


# ============================================
# TECHNIQUE 6: State Snapshot Debugging
# ============================================

class StateSnapshot:
    """Capture complete state at suspicious points"""
    
    @staticmethod
    def snapshot_debugging():
        print("=== STATE SNAPSHOT DEBUGGING ===\n")
        
        def two_sum_with_snapshots(nums, target):
            """Two sum with state tracking"""
            seen = {}
            snapshots = []
            
            for i, num in enumerate(nums):
                # Capture state before decision
                snapshot = {
                    'iteration': i,
                    'current_num': num,
                    'seen': seen.copy(),
                    'target': target,
                    'complement': target - num,
                    'complement_exists': (target - num) in seen
                }
                snapshots.append(snapshot)
                
                complement = target - num
                
                if complement in seen:
                    return [seen[complement], i], snapshots
                
                seen[num] = i
            
            return None, snapshots
        
        result, snapshots = two_sum_with_snapshots([2, 7, 11, 15], 9)
        
        print("State evolution:")
        for snap in snapshots:
            print(f"  i={snap['iteration']}: num={snap['current_num']}, "
                  f"seen={snap['seen']}, found={snap['complement_exists']}")
        
        print(f"\n✅ Result: {result}")
        print()


# ============================================
# TECHNIQUE 7: Automated Bug Patterns
# ============================================

class BugPatternDetector:
    """Detect common bug patterns automatically"""
    
    class BugPattern(Enum):
        OFF_BY_ONE = "off_by_one"
        UNINITIALIZED = "uninitialized"
        INTEGER_OVERFLOW = "integer_overflow"
        NULL_POINTER = "null_pointer"
        INFINITE_LOOP = "infinite_loop"
    
    @staticmethod
    def detect_patterns():
        print("=== COMMON BUG PATTERN DETECTION ===\n")
        
        # Pattern 1: Off-by-one
        def check_off_by_one(code_snippet):
            patterns = [
                "range(len(arr))",  # Should be range(len(arr)-1) for comparisons
                "arr[i+1]",         # Potential out of bounds
                "left <= right",    # vs left < right
            ]
            
            for pattern in patterns:
                if pattern in code_snippet:
                    print(f"⚠️  Potential off-by-one: '{pattern}'")
        
        # Pattern 2: Uninitialized variable
        def check_uninitialized():
            code = """
            def find_max(arr):
                # max_val not initialized for empty array
                for num in arr:
                    if num > max_val:  # NameError if arr is empty
                        max_val = num
                return max_val
            """
            print("⚠️  'max_val' may be uninitialized")
        
        # Pattern 3: Integer overflow
        def check_overflow():
            code = """
            mid = (left + right) // 2  # Overflow if left + right > MAX_INT
            """
            print("⚠️  Potential overflow: Use left + (right - left) // 2")
        
        check_off_by_one("for i in range(len(arr)): if arr[i] > arr[i+1]")
        check_uninitialized()
        check_overflow()
        print()


# ============================================
# MAIN - RUN ALL TECHNIQUES
# ============================================

if __name__ == "__main__":
    BugHunter.binary_search_bug_location()
    DifferentialTesting.test_against_reference()
    InvariantChecker.check_sliding_window()
    TestCaseMinimizer.minimize_test()
    AssertionDebugger.demo_assertions()
    StateSnapshot.snapshot_debugging()
    BugPatternDetector.detect_patterns()
    
    print("="*60)
    print("KEY TAKEAWAY:")
    print("Bugs hide in state transitions. Track state, verify invariants,")
    print("and shrink test cases to find them quickly.")
    print("="*60)

# Essential Algorithms: The Top 1% Roadmap

## TIER 0: Absolute Fundamentals (Week 1-2)
**Master these or you can't progress.**

### 1. Array Manipulation
- Two pointers (fast/slow, left/right)
- Sliding window (fixed/variable)
- Prefix sums
- **Why**: 30% of problems use these

### 2. Hash Tables
- Frequency maps
- Seen/visited sets
- Index mappings
- **Why**: O(1) lookup is a superpower

### 3. Basic Recursion
- Base case identification
- Recursive case reasoning
- Stack overflow awareness
- **Why**: Foundation for everything else

---

## TIER 1: Core Patterns (Week 3-6)
**These appear in 60% of medium problems.**

### 4. Binary Search
- Classic search
- Search answer space
- Finding boundaries
- **Practice**: 20 problems

### 5. Sorting Mastery
- Quicksort, mergesort internals
- Custom comparators
- Partially sorted arrays
- **Why**: Enables many optimizations

### 6. Stack/Queue
- Monotonic stack/queue
- Valid parentheses pattern
- BFS level traversal
- **Practice**: 15 problems

### 7. Linked Lists
- Fast/slow pointer (cycle detection)
- Reversal patterns
- Dummy head technique
- **Practice**: 10 problems

---

## TIER 2: Tree & Graph Mastery (Week 7-10)
**The difference between medium and hard.**

### 8. Tree Traversals
- DFS (inorder, preorder, postorder)
- BFS (level order)
- Morris traversal (optional)
- **Practice**: 20 problems

### 9. Graph Algorithms
- DFS/BFS basics
- Cycle detection
- Topological sort
- Connected components
- **Practice**: 20 problems

### 10. Advanced Graph (Optional for Hard)
- Dijkstra's (shortest path)
- Union-Find (disjoint sets)
- Minimum spanning tree (Kruskal/Prim)
- **Practice**: 10 problems

---

## TIER 3: Dynamic Programming (Week 11-16)
**The final boss. Required for top 1%.**

### 11. 1D DP
- Fibonacci pattern
- House robber pattern
- Coin change pattern
- **Practice**: 25 problems

### 12. 2D DP
- Grid paths
- Longest common subsequence
- Edit distance
- **Practice**: 25 problems

### 13. DP Optimization
- Space optimization (rolling array)
- State compression
- Memoization vs tabulation
- **Practice**: 15 problems

---

## TIER 4: Advanced Topics (Week 17+)
**For FAANG E5+, ICPC, or hardcore competitions.**

### 14. Advanced Data Structures
- Trie (prefix tree)
- Segment tree
- Fenwick tree (BIT)
- **Practice**: 10 problems each

### 15. Greedy Algorithms
- Activity selection
- Interval scheduling
- Huffman coding pattern
- **Practice**: 15 problems

### 16. Backtracking
- N-Queens pattern
- Subset generation
- Permutation/combination
- **Practice**: 20 problems

### 17. Bit Manipulation
- XOR tricks
- Bit masking
- Power of two checks
- **Practice**: 10 problems

### 18. Math & Number Theory (Optional)
- Prime numbers (Sieve)
- GCD/LCM
- Modular arithmetic
- **Practice**: 10 problems

### 19. String Algorithms (Optional)
- KMP (pattern matching)
- Rabin-Karp
- Z-algorithm
- **Practice**: 5 problems

### 20. Advanced Techniques (Optional)
- Divide and conquer
- Sweep line
- Two-phase algorithms
- **Practice**: As needed

---

## Learning Strategy: The 3-Pass System

### **Pass 1: Recognition (First 2 weeks per topic)**
- Learn the pattern
- Solve 5 easy problems
- Understand WHY it works
- **Goal**: "I've seen this before"

### **Pass 2: Application (Next 2 weeks)**
- Solve 10-15 medium problems
- Implement from scratch (no copying)
- Time yourself
- **Goal**: "I can solve this in 20 minutes"

### **Pass 3: Mastery (Final 2 weeks)**
- Solve hard problems
- Optimize solutions
- Teach it to someone else
- **Goal**: "I can solve variants blindfolded"

---

## The 80/20 Rule Applied

**80% of interview problems use:**
1. Hash maps (40%)
2. Two pointers (20%)
3. DFS/BFS (15%)
4. Binary search (5%)

**The remaining 20% require:**
- DP (10%)
- Advanced data structures (5%)
- Math/string algorithms (5%)

---

## Time-Efficient Learning Plan

### **3-Month Intensive Plan** (For job search)
- **Month 1**: Tiers 0-1 (arrays, hash, stack, queue, binary search)
- **Month 2**: Tier 2 (trees, graphs, basic DP)
- **Month 3**: Polish + mock interviews

### **6-Month Deep Mastery** (For top 1%)
- **Months 1-2**: Tiers 0-2
- **Months 3-4**: Tier 3 (DP mastery)
- **Months 5-6**: Tier 4 + contests

### **Daily Schedule** (2-3 hours)
- 30 min: Review yesterday's problems
- 60 min: Solve 2 new problems (timed)
- 30 min: Study editorial/alternative approaches
- 30 min: Implement one concept from scratch

---

## Learning Resources Priority

### **Must-Have:**
1. LeetCode (Patterns, not random problems)
2. NeetCode 150 (Curated problems)
3. Grind 75 (For interviews)

### **Deep Understanding:**
4. CLRS (Algorithms textbook) - Selective reading
5. Competitive Programmer's Handbook - Free PDF
6. Codeforces Educational Rounds

### **Practice:**
7. LeetCode contests (weekly)
8. Codeforces (Div 2/3)
9. AtCoder Beginner Contests

---

## How to Learn Algorithms FAST

### **The Feynman Technique**
1. Study algorithm
2. Explain it to a rubber duck (or friend)
3. Identify gaps in your understanding
4. Fill gaps and simplify explanation

### **Implementation-First Learning**
Don't read theory for hours. Instead:
1. Watch a 10-minute video
2. Immediately implement it
3. Break it, fix it, optimize it
4. Teach it

### **Pattern Recognition Over Memorization**
Don't memorize code. Memorize:
- **When** to use the algorithm
- **Why** it works
- **How** to derive it

Example: Binary search
- **When**: Sorted data, monotonic function
- **Why**: Eliminates half the search space
- **How**: Divide and conquer on decision boundary

---

## The "Just-In-Time" Learning Philosophy

**Don't learn everything upfront.**

When you see a new problem type:
1. Recognize you don't know the pattern
2. Learn ONLY that pattern (30 min theory)
3. Solve 3-5 problems immediately
4. Move on

**Example Flow:**
- See a "segment tree" problem
- Don't spend a week on segment trees
- Learn the minimal concept (1 hour)
- Solve 3 problems (2 hours)
- Return later if needed

---

## Mental Models > Algorithms

Top coders think in **abstractions**:

❌ "This is Dijkstra's algorithm"
✅ "This is a shortest path problem with positive weights"

❌ "I need dynamic programming"
✅ "I need to avoid recomputing overlapping subproblems"

❌ "Use a segment tree"
✅ "I need range queries with updates"

**Train yourself to think in problems, not solutions.**

---

## Final Truth: Quality > Quantity

**Don't solve 1000 problems randomly.**

Solve 300 problems **deeply**:
- Understand every line
- Optimize to perfection
- Derive from first principles
- Explain to others

**One perfectly understood problem teaches more than ten half-understood problems.**

---

## Your 90-Day Challenge

### **Weeks 1-4: Foundation**
- 40 array/hash problems
- 20 stack/queue problems
- 10 binary search problems
- **Daily**: 2-3 problems + theory

### **Weeks 5-8: Depth**
- 30 tree problems
- 30 graph problems
- 20 1D DP problems
- **Daily**: 2-3 problems + patterns

### **Weeks 9-12: Mastery**
- 20 2D DP problems
- 20 hard mixed problems
- 10 contest problems
- **Daily**: 1-2 hard + review

**Total**: ~200 high-quality problems in 90 days = Top 5% skill level

---

## Remember

You don't become a master by learning everything.

You become a master by **deeply understanding the fundamentals** and **recognizing patterns**.

The top 1% aren't walking algorithms textbooks.

They're pattern recognition machines who know when to brute force and when to optimize.

# The Art of Fuzzing, Brute Force, and Rapid Bug Detection

This is the **dark art** of problem-solving that separates theoretical knowledge from practical mastery. Let me show you how top 1% coders actually think.

---

## **1. Fuzzing & Brute Force: The Reality**

### **What Top Coders Actually Do**

Most competitive programmers follow this workflow:

```
1. Read problem
2. Write brute force solution (5-10 minutes)
3. Generate test cases and fuzz
4. Find patterns in brute force output
5. Optimize based on patterns
6. Verify optimized solution against brute force
```

**Critical Insight:** Brute force is not failure—it's a **correctness oracle** and **pattern discovery tool**.

---

## **2. The Brute Force Framework**

### **A. When to Write Brute Force First**

**Always write brute force when:**
- Problem constraints are small (n ≤ 20)
- You're unsure about edge cases
- The optimized approach is complex
- You need a reference for testing

**Example: Subset Sum Problem**Now let me show you the **systematic approach** to learning and bug detection:

---

## **3. Efficient Fuzzing Strategies**

### **A. Smart Test Case Generation**

Don't generate random tests blindly. Use **stratified sampling**:---

## **4. Finding and Fixing Logical Bugs: The Systematic Approach**

### **The Bug Hunting Protocol**---

## **5. Do You Need to Know Every Algorithm? NO!**

### **The 80/20 Rule for Algorithms**

**You need 20% of algorithms to solve 80% of problems.**

Here's the **mandatory core** (learn these first, ~3-4 months):---

## **6. Pro Tips for Efficient Problem Solving**

### **The 45-Minute Rule**
```
0-15 min:  Understand problem, think of approaches
15-30 min: Attempt solution (even if partial)
30-45 min: Debug, test edge cases
45+ min:   Read solution, but MUST implement from memory within 24 hours
```

**Why this works:** Prevents learned helplessness. Your brain needs to struggle before it can learn.

---

### **The "Explain Before Code" Discipline**

Before writing a single line:
1. **Explain the approach in plain English**
2. **State the time/space complexity**
3. **Identify edge cases**

If you can't do step 1, you're not ready to code.

---

### **The "Minimum Viable Solution" Strategy**

Always solve in this order:
1. **Brute force** (get something working)
2. **Identify bottleneck** (what's slow?)
3. **Optimize bottleneck** (one piece at a time)

**Never** try to write the optimal solution directly unless it's trivial.

---

### **The "Similar Problem" Technique**

After solving any problem:
- Find 3 similar problems on LeetCode
- Solve them **immediately** (within same session)
- This cements the pattern in long-term memory

**Neuroscience:** Spaced repetition within 24 hours → permanent retention

---

### **The "Teach to Learn" Method**

After mastering a pattern:
- Write a blog post explaining it
- Make a video walkthrough
- Explain it to a friend

**If you can't teach it, you don't know it.**

---

## **7. The Mental Game**

### **Building Problem-Solving Stamina**

Treat this like athletic training:

**Week 1-2:** 1 hour/day
**Week 3-4:** 2 hours/day  
**Week 5+:** 3 hours/day (2 focused sessions)

**Don't** try 8 hours from day 1—you'll burn out.

---

### **The "Flow State" Protocol**

To enter deep focus:
1. **Pomodoro:** 50 min focus, 10 min break
2. **No distractions:** Phone off, internet blocker on
3. **Prime your brain:** Review yesterday's solution first
4. **Physical state:** Well-rested, fed, hydrated

**Elite performers** protect their cognitive state like athletes protect their bodies.

---

### **Dealing with Frustration**

When stuck:
1. **Walk away for 10 minutes** (seriously)
2. **Explain problem to rubber duck**
3. **Draw the state transitions**
4. **Check solution after 45 min** (no shame!)

**Top coders get stuck too**—the difference is they have a protocol for unsticking.

---

## **The Bottom Line**

**You don't become top 1% by:**
- Memorizing 500 algorithms
- Solving 2000 random problems
- Reading every textbook

**You become top 1% by:**
- **Pattern recognition** (20 core patterns)
- **Deliberate practice** (solving similar problems in clusters)
- **Systematic debugging** (catching bugs before they happen)
- **Mental models** (thinking in states, invariants, transitions)

**Start with Tier 0 algorithms. Solve 50 problems. Master brute force thinking. Build from there.**

The journey to mastery is not about shortcuts—it's about building the right mental infrastructure.

Now stop reading and go solve 3 two-pointer problems. 🔥

// ============================================
// FRAMEWORK: Brute Force → Pattern → Optimize
// ============================================

use std::collections::{HashSet, HashMap};
use rand::Rng;

// ============================================
// PATTERN 1: Subset Sum
// ============================================

/// STEP 1: Brute Force - Generate all subsets
/// Time: O(2^n), Space: O(2^n)
/// Purpose: Understand the problem, verify correctness
fn subset_sum_brute_force(nums: &[i32], target: i32) -> bool {
    let n = nums.len();
    
    // Generate all 2^n subsets using bit manipulation
    for mask in 0..(1 << n) {
        let mut sum = 0;
        for i in 0..n {
            if (mask & (1 << i)) != 0 {
                sum += nums[i];
            }
        }
        
        if sum == target {
            // Print the subset for understanding
            let subset: Vec<i32> = (0..n)
                .filter(|&i| (mask & (1 << i)) != 0)
                .map(|i| nums[i])
                .collect();
            eprintln!("Found subset: {:?}, sum={}", subset, sum);
            return true;
        }
    }
    false
}

/// STEP 2: Recognize Pattern - Overlapping subproblems
/// Observation: We recalculate same sums multiple times
/// Key insight: If we can make sum 'x', we can make 'x + nums[i]'

/// STEP 3: Optimize - Dynamic Programming
/// Time: O(n * target), Space: O(target)
fn subset_sum_optimized(nums: &[i32], target: i32) -> bool {
    let t = target as usize;
    let mut dp = vec![false; t + 1];
    dp[0] = true; // Can always make sum 0
    
    for &num in nums {
        if num > 0 && num as usize <= t {
            // Traverse backwards to avoid using same element twice
            for i in (num as usize..=t).rev() {
                dp[i] = dp[i] || dp[i - num as usize];
            }
        }
    }
    
    dp[t]
}

// ============================================
// PATTERN 2: Longest Common Subsequence
// ============================================

/// STEP 1: Brute Force - Generate all subsequences
/// Time: O(2^n * 2^m), completely impractical
fn lcs_brute_force(s1: &str, s2: &str) -> usize {
    fn generate_subsequences(s: &str) -> Vec<String> {
        let chars: Vec<char> = s.chars().collect();
        let n = chars.len();
        let mut result = Vec::new();
        
        for mask in 0..(1 << n) {
            let subseq: String = (0..n)
                .filter(|&i| (mask & (1 << i)) != 0)
                .map(|i| chars[i])
                .collect();
            result.push(subseq);
        }
        result
    }
    
    let subseqs1 = generate_subsequences(s1);
    let subseqs2: HashSet<String> = generate_subsequences(s2).into_iter().collect();
    
    subseqs1.iter()
        .filter(|s| subseqs2.contains(*s))
        .map(|s| s.len())
        .max()
        .unwrap_or(0)
}

/// STEP 2: Recognize Pattern - Choices at each position
/// At each position: either match characters or skip one

/// STEP 3: Optimize - DP with memoization
fn lcs_optimized(s1: &str, s2: &str) -> usize {
    let c1: Vec<char> = s1.chars().collect();
    let c2: Vec<char> = s2.chars().collect();
    let n = c1.len();
    let m = c2.len();
    
    let mut dp = vec![vec![0; m + 1]; n + 1];
    
    for i in 1..=n {
        for j in 1..=m {
            if c1[i-1] == c2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                dp[i][j] = dp[i-1][j].max(dp[i][j-1]);
            }
        }
    }
    
    dp[n][m]
}

// ============================================
// FUZZING FRAMEWORK
// ============================================

pub struct Fuzzer {
    test_count: usize,
    failed_cases: Vec<String>,
}

impl Fuzzer {
    pub fn new() -> Self {
        Self {
            test_count: 0,
            failed_cases: Vec::new(),
        }
    }
    
    /// Generate random test case
    fn generate_random_array(&self, size: usize, min: i32, max: i32) -> Vec<i32> {
        let mut rng = rand::thread_rng();
        (0..size).map(|_| rng.gen_range(min..=max)).collect()
    }
    
    /// Compare brute force vs optimized
    pub fn fuzz_subset_sum(&mut self, iterations: usize, max_size: usize) {
        println!("\n🔍 Fuzzing Subset Sum ({} iterations)...", iterations);
        
        for i in 0..iterations {
            self.test_count += 1;
            
            let size = rand::thread_rng().gen_range(1..=max_size);
            let nums = self.generate_random_array(size, -10, 10);
            let target = rand::thread_rng().gen_range(-20..=20);
            
            let brute_result = subset_sum_brute_force(&nums, target);
            let optimized_result = subset_sum_optimized(&nums, target);
            
            if brute_result != optimized_result {
                let error = format!(
                    "MISMATCH on test {}: nums={:?}, target={}, brute={}, optimized={}",
                    i, nums, target, brute_result, optimized_result
                );
                eprintln!("❌ {}", error);
                self.failed_cases.push(error);
            }
        }
        
        if self.failed_cases.is_empty() {
            println!("✅ All {} tests passed!", iterations);
        } else {
            println!("❌ {} failures found", self.failed_cases.len());
        }
    }
    
    /// Edge case generator
    pub fn test_edge_cases_subset_sum(&mut self) {
        println!("\n🎯 Testing Edge Cases...");
        
        let edge_cases = vec![
            (vec![], 0, "Empty array, zero target"),
            (vec![], 5, "Empty array, non-zero target"),
            (vec![5], 5, "Single element match"),
            (vec![5], 3, "Single element no match"),
            (vec![1, 2, 3], 0, "Positive array, zero target"),
            (vec![-1, -2, -3], 0, "Negative array, zero target"),
            (vec![1, -1, 2, -2], 0, "Mixed signs, zero target"),
            (vec![1000000], 1000000, "Large single value"),
        ];
        
        for (nums, target, desc) in edge_cases {
            self.test_count += 1;
            let brute = subset_sum_brute_force(&nums, target);
            let opt = subset_sum_optimized(&nums, target);
            
            if brute != opt {
                eprintln!("❌ Edge case failed: {}", desc);
                self.failed_cases.push(desc.to_string());
            } else {
                println!("✅ {}: {}", desc, brute);
            }
        }
    }
}

// ============================================
// PATTERN RECOGNITION HELPER
// ============================================

pub struct PatternAnalyzer {
    observations: Vec<String>,
}

impl PatternAnalyzer {
    pub fn new() -> Self {
        Self {
            observations: Vec::new(),
        }
    }
    
    /// Analyze brute force output to find patterns
    pub fn analyze_subset_sum(&mut self, nums: &[i32], target: i32) {
        println!("\n📊 Pattern Analysis for nums={:?}, target={}", nums, target);
        
        let n = nums.len();
        let mut reachable_sums: HashSet<i32> = HashSet::new();
        let mut sum_to_subsets: HashMap<i32, Vec<Vec<i32>>> = HashMap::new();
        
        // Collect all reachable sums
        for mask in 0..(1 << n) {
            let mut sum = 0;
            let mut subset = Vec::new();
            
            for i in 0..n {
                if (mask & (1 << i)) != 0 {
                    sum += nums[i];
                    subset.push(nums[i]);
                }
            }
            
            reachable_sums.insert(sum);
            sum_to_subsets.entry(sum).or_insert_with(Vec::new).push(subset);
        }
        
        println!("Total unique sums reachable: {}", reachable_sums.len());
        println!("Can reach target {}: {}", target, reachable_sums.contains(&target));
        
        // Pattern observation
        if reachable_sums.contains(&target) {
            println!("\nWays to reach target:");
            if let Some(subsets) = sum_to_subsets.get(&target) {
                for (i, subset) in subsets.iter().enumerate().take(5) {
                    println!("  Way {}: {:?}", i + 1, subset);
                }
                if subsets.len() > 5 {
                    println!("  ... and {} more ways", subsets.len() - 5);
                }
            }
        }
        
        // Key observation for optimization
        self.observations.push(format!(
            "Observation: We only need to track which sums are reachable, not HOW to reach them"
        ));
        self.observations.push(format!(
            "Observation: If sum X is reachable, then X + nums[i] is also reachable"
        ));
        self.observations.push(format!(
            "Optimization: Use boolean array dp[sum] instead of generating all subsets"
        ));
        
        for obs in &self.observations {
            println!("💡 {}", obs);
        }
    }
}

// ============================================
// BUG DETECTION FRAMEWORK
// ============================================

pub struct BugDetector {
    checks: Vec<String>,
}

impl BugDetector {
    pub fn new() -> Self {
        Self {
            checks: Vec::new(),
        }
    }
    
    /// Systematic bug checking
    pub fn check_subset_sum_implementation(&mut self, implementation: &str) {
        println!("\n🐛 Bug Detection for: {}", implementation);
        
        // Check 1: Boundary conditions
        self.checks.push("✓ Check: Empty array handled?".to_string());
        self.checks.push("✓ Check: Single element handled?".to_string());
        self.checks.push("✓ Check: Zero target handled?".to_string());
        
        // Check 2: Index bounds
        self.checks.push("✓ Check: Array indices within bounds?".to_string());
        
        // Check 3: Integer overflow
        self.checks.push("✓ Check: Sum overflow protection?".to_string());
        
        // Check 4: Negative numbers
        self.checks.push("✓ Check: Negative numbers handled?".to_string());
        
        // Check 5: Off-by-one errors
        self.checks.push("✓ Check: Loop ranges correct (0..n vs 0..=n)?".to_string());
        
        for check in &self.checks {
            println!("{}", check);
        }
    }
}

// ============================================
// MAIN: DEMONSTRATION
// ============================================

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_brute_vs_optimized() {
        let nums = vec![3, 34, 4, 12, 5, 2];
        let target = 9;
        
        assert_eq!(
            subset_sum_brute_force(&nums, target),
            subset_sum_optimized(&nums, target)
        );
    }
    
    #[test]
    fn test_fuzzing() {
        let mut fuzzer = Fuzzer::new();
        fuzzer.fuzz_subset_sum(100, 10);
        fuzzer.test_edge_cases_subset_sum();
    }
    
    #[test]
    fn test_pattern_analysis() {
        let mut analyzer = PatternAnalyzer::new();
        analyzer.analyze_subset_sum(&vec![1, 2, 3], 5);
    }
}

"""
============================================
SMART FUZZING STRATEGIES
============================================
"""

import random
import time
from typing import List, Tuple, Callable, Any
from dataclasses import dataclass

# ============================================
# 1. STRATIFIED TEST CASE GENERATION
# ============================================

class SmartFuzzer:
    """Generate test cases that cover different categories"""
    
    def __init__(self):
        self.test_categories = {
            'edge_cases': 0,
            'random': 0,
            'stress': 0,
            'adversarial': 0
        }
    
    def generate_array_tests(self, n: int) -> List[Tuple[List[int], str]]:
        """Generate diverse array test cases"""
        tests = []
        
        # Category 1: Edge cases (15% of tests)
        edge_cases = [
            ([], "empty array"),
            ([1], "single element"),
            ([1, 1, 1, 1], "all same"),
            (list(range(n)), "sorted ascending"),
            (list(range(n, 0, -1)), "sorted descending"),
            ([0] * n, "all zeros"),
            ([-i for i in range(n)], "all negative"),
            ([random.randint(-1000, 1000)] * n, "all same random"),
        ]
        tests.extend(edge_cases)
        self.test_categories['edge_cases'] += len(edge_cases)
        
        # Category 2: Random cases (50% of tests)
        for _ in range(n * 2):
            size = random.randint(1, n)
            arr = [random.randint(-100, 100) for _ in range(size)]
            tests.append((arr, "random"))
            self.test_categories['random'] += 1
        
        # Category 3: Stress cases (20% of tests)
        stress_cases = [
            ([random.randint(-10**6, 10**6) for _ in range(n)], "large values"),
            ([10**9] * n, "max int boundary"),
            ([-10**9] * n, "min int boundary"),
            ([random.choice([0, 10**9, -10**9]) for _ in range(n)], "extreme mix"),
        ]
        tests.extend(stress_cases)
        self.test_categories['stress'] += len(stress_cases)
        
        # Category 4: Adversarial cases (15% of tests)
        # Design cases that often break algorithms
        adversarial = [
            ([1, 2, 3, 4] + [0] * (n - 4), "zeros at end"),
            ([0] * (n - 4) + [1, 2, 3, 4], "zeros at start"),
            ([i if i % 2 == 0 else -i for i in range(n)], "alternating signs"),
            ([2**i for i in range(min(n, 20))], "powers of 2"),
        ]
        tests.extend(adversarial)
        self.test_categories['adversarial'] += len(adversarial)
        
        return tests
    
    def print_stats(self):
        """Print test distribution"""
        total = sum(self.test_categories.values())
        print("\n📊 Test Distribution:")
        for category, count in self.test_categories.items():
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {category}: {count} ({percentage:.1f}%)")

# ============================================
# 2. DIFFERENTIAL TESTING
# ============================================

class DifferentialTester:
    """Compare multiple implementations"""
    
    def __init__(self, name: str):
        self.name = name
        self.mismatches = []
        self.performance_data = []
    
    def compare_implementations(
        self,
        impl1: Callable,
        impl2: Callable,
        test_cases: List[Tuple[Any, str]],
        impl1_name: str = "Implementation 1",
        impl2_name: str = "Implementation 2"
    ):
        """Compare two implementations and find discrepancies"""
        
        print(f"\n🔬 Differential Testing: {self.name}")
        print(f"Comparing: {impl1_name} vs {impl2_name}")
        
        passed = 0
        failed = 0
        
        for i, (test_input, description) in enumerate(test_cases):
            try:
                # Time first implementation
                start1 = time.perf_counter()
                result1 = impl1(test_input)
                time1 = time.perf_counter() - start1
                
                # Time second implementation
                start2 = time.perf_counter()
                result2 = impl2(test_input)
                time2 = time.perf_counter() - start2
                
                # Compare results
                if result1 != result2:
                    failed += 1
                    mismatch = {
                        'test_id': i,
                        'description': description,
                        'input': test_input,
                        'result1': result1,
                        'result2': result2,
                    }
                    self.mismatches.append(mismatch)
                    print(f"❌ Test {i} ({description}): MISMATCH")
                    print(f"   {impl1_name}: {result1}")
                    print(f"   {impl2_name}: {result2}")
                else:
                    passed += 1
                    
                self.performance_data.append({
                    'test_id': i,
                    'time1': time1,
                    'time2': time2,
                    'speedup': time1 / time2 if time2 > 0 else float('inf')
                })
                
            except Exception as e:
                print(f"❌ Test {i} crashed: {e}")
                failed += 1
        
        print(f"\n✅ Passed: {passed}/{len(test_cases)}")
        print(f"❌ Failed: {failed}/{len(test_cases)}")
        
        if self.performance_data:
            self._print_performance_summary(impl1_name, impl2_name)
    
    def _print_performance_summary(self, impl1_name: str, impl2_name: str):
        """Print performance comparison"""
        avg_speedup = sum(d['speedup'] for d in self.performance_data) / len(self.performance_data)
        print(f"\n⚡ Performance Summary:")
        print(f"   Average speedup ({impl2_name} vs {impl1_name}): {avg_speedup:.2f}x")

# ============================================
# 3. PROPERTY-BASED TESTING
# ============================================

class PropertyTester:
    """Test invariants and properties rather than specific outputs"""
    
    @staticmethod
    def test_sorting_properties(sort_fn: Callable[[List[int]], List[int]]):
        """Test properties that ANY sorting function must satisfy"""
        
        print("\n🧪 Property-Based Testing: Sorting")
        
        fuzzer = SmartFuzzer()
        tests = fuzzer.generate_array_tests(20)
        
        all_passed = True
        
        for arr, desc in tests:
            original = arr.copy()
            sorted_arr = sort_fn(arr)
            
            # Property 1: Length preserved
            if len(sorted_arr) != len(original):
                print(f"❌ Property violated: Length changed")
                print(f"   Input: {original}")
                all_passed = False
                continue
            
            # Property 2: Elements preserved (multiset equality)
            if sorted(original) != sorted(sorted_arr):
                print(f"❌ Property violated: Elements changed")
                print(f"   Input: {original}")
                print(f"   Output: {sorted_arr}")
                all_passed = False
                continue
            
            # Property 3: Sorted order
            for i in range(len(sorted_arr) - 1):
                if sorted_arr[i] > sorted_arr[i + 1]:
                    print(f"❌ Property violated: Not sorted")
                    print(f"   Input: {original}")
                    print(f"   Output: {sorted_arr}")
                    all_passed = False
                    break
        
        if all_passed:
            print("✅ All properties satisfied!")
        
        return all_passed
    
    @staticmethod
    def test_search_properties(search_fn: Callable[[List[int], int], bool], 
                               arr: List[int]):
        """Test properties of search functions"""
        
        print("\n🧪 Property-Based Testing: Search")
        
        # Property 1: If element is in array, search must find it
        for elem in set(arr):
            if not search_fn(arr, elem):
                print(f"❌ Property violated: Element {elem} in array but not found")
                return False
        
        # Property 2: If element not in array, search must return False
        not_in_array = max(arr) + 100 if arr else 999
        if search_fn(arr, not_in_array):
            print(f"❌ Property violated: Element {not_in_array} not in array but found")
            return False
        
        print("✅ All search properties satisfied!")
        return True

# ============================================
# 4. MUTATION TESTING (Find weak tests)
# ============================================

class MutationTester:
    """Introduce bugs to see if tests catch them"""
    
    @staticmethod
    def mutate_binary_search(arr: List[int], target: int, mutation: str) -> int:
        """Binary search with intentional bugs"""
        
        left, right = 0, len(arr) - 1
        
        while left <= right:
            if mutation == "wrong_mid":
                mid = (left + right) // 2 + 1  # BUG: Off by one
            elif mutation == "wrong_comparison":
                mid = (left + right) // 2
                if arr[mid] >= target:  # BUG: Should be ==
                    return mid
            elif mutation == "wrong_update":
                mid = (left + right) // 2
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    left = mid  # BUG: Should be mid + 1
                else:
                    right = mid - 1
            else:
                # Correct implementation
                mid = (left + right) // 2
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1
        
        return -1
    
    def test_mutation_detection(self):
        """See if our tests catch common bugs"""
        
        print("\n🧬 Mutation Testing: Binary Search")
        
        mutations = ["wrong_mid", "wrong_comparison", "wrong_update", "correct"]
        test_cases = [
            ([1, 2, 3, 4, 5], 3, 2),
            ([1, 2, 3, 4, 5], 1, 0),
            ([1, 2, 3, 4, 5], 5, 4),
            ([1, 2, 3, 4, 5], 0, -1),
            ([1], 1, 0),
            ([], 1, -1),
        ]
        
        for mutation in mutations:
            caught = False
            for arr, target, expected in test_cases:
                result = self.mutate_binary_search(arr, target, mutation)
                if result != expected:
                    if mutation != "correct":
                        print(f"✅ Mutation '{mutation}' CAUGHT by test: arr={arr}, target={target}")
                        caught = True
                        break
            
            if not caught and mutation != "correct":
                print(f"❌ Mutation '{mutation}' NOT CAUGHT - tests are weak!")

# ============================================
# 5. STRESS TESTING
# ============================================

class StressTester:
    """Test performance and correctness under load"""
    
    @staticmethod
    def stress_test_algorithm(
        brute_force: Callable,
        optimized: Callable,
        test_gen: Callable,
        max_size: int = 100,
        iterations: int = 1000,
        time_limit: float = 5.0
    ):
        """Compare brute force vs optimized under stress"""
        
        print(f"\n💪 Stress Testing ({iterations} iterations, max_size={max_size})")
        
        start_time = time.time()
        mismatches = 0
        timeouts = 0
        
        for i in range(iterations):
            if time.time() - start_time > time_limit:
                print(f"⏱️  Time limit reached at iteration {i}")
                break
            
            # Generate test
            test_input = test_gen(random.randint(1, max_size))
            
            try:
                # Run brute force with timeout
                result_brute = brute_force(test_input)
                result_opt = optimized(test_input)
                
                if result_brute != result_opt:
                    mismatches += 1
                    print(f"❌ Mismatch at iteration {i}")
                    print(f"   Input size: {len(test_input) if hasattr(test_input, '__len__') else 'N/A'}")
                    print(f"   Brute: {result_brute}, Optimized: {result_opt}")
                    
            except Exception as e:
                timeouts += 1
                print(f"⚠️  Iteration {i} failed: {e}")
        
        print(f"\n📊 Stress Test Results:")
        print(f"   Mismatches: {mismatches}")
        print(f"   Timeouts/Errors: {timeouts}")
        print(f"   Success rate: {((iterations - mismatches - timeouts) / iterations * 100):.1f}%")

# ============================================
# DEMONSTRATION
# ============================================

if __name__ == "__main__":
    # Example 1: Smart fuzzing
    print("=" * 60)
    print("EXAMPLE 1: SMART FUZZING")
    print("=" * 60)
    
    fuzzer = SmartFuzzer()
    tests = fuzzer.generate_array_tests(10)
    fuzzer.print_stats()
    
    # Example 2: Differential testing
    print("\n" + "=" * 60)
    print("EXAMPLE 2: DIFFERENTIAL TESTING")
    print("=" * 60)
    
    def bubble_sort(arr):
        arr = arr.copy()
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr
    
    def python_sort(arr):
        return sorted(arr)
    
    tester = DifferentialTester("Sorting Algorithms")
    tester.compare_implementations(
        bubble_sort,
        python_sort,
        tests[:10],
        "Bubble Sort",
        "Python sorted()"
    )
    
    # Example 3: Property-based testing
    print("\n" + "=" * 60)
    print("EXAMPLE 3: PROPERTY-BASED TESTING")
    print("=" * 60)
    
    PropertyTester.test_sorting_properties(bubble_sort)
    
    # Example 4: Mutation testing
    print("\n" + "=" * 60)
    print("EXAMPLE 4: MUTATION TESTING")
    print("=" * 60)
    
    mutation_tester = MutationTester()
    mutation_tester.test_mutation_detection()

"""
============================================
SYSTEMATIC BUG DETECTION PROTOCOL
============================================
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# ============================================
# BUG TAXONOMY - Know Your Enemy
# ============================================

class BugType(Enum):
    OFF_BY_ONE = "off_by_one"
    INTEGER_OVERFLOW = "integer_overflow"
    NULL_POINTER = "null_pointer"
    UNINITIALIZED = "uninitialized_variable"
    WRONG_COMPARISON = "wrong_comparison_operator"
    INFINITE_LOOP = "infinite_loop"
    INDEX_OUT_OF_BOUNDS = "index_out_of_bounds"
    WRONG_BASE_CASE = "wrong_recursion_base_case"
    STATE_CORRUPTION = "state_corruption"
    EDGE_CASE = "edge_case_not_handled"

@dataclass
class BugReport:
    bug_type: BugType
    location: str
    description: str
    fix_suggestion: str
    test_case: Optional[str] = None

# ============================================
# PHASE 1: STATIC ANALYSIS CHECKLIST
# ============================================

class StaticAnalyzer:
    """Check code without running it"""
    
    def __init__(self):
        self.issues = []
    
    def analyze_loop(self, code_snippet: str) -> List[BugReport]:
        """Check for common loop bugs"""
        
        print("\n🔍 Static Analysis: Loops")
        bugs = []
        
        # Check 1: Loop bounds
        checklist = [
            "Loop starts at correct index (0 or 1)?",
            "Loop ends at correct index (n or n-1)?",
            "Loop uses < vs <= correctly?",
            "Loop increment/decrement correct?",
            "Loop variable not modified inside loop?",
        ]
        
        print("Loop Checklist:")
        for check in checklist:
            print(f"  [ ] {check}")
        
        return bugs
    
    def analyze_recursion(self, function_name: str) -> List[BugReport]:
        """Check recursion correctness"""
        
        print(f"\n🔍 Static Analysis: Recursion ({function_name})")
        
        checklist = [
            "Base case exists and is correct?",
            "Every recursive call moves toward base case?",
            "No infinite recursion possible?",
            "Stack overflow considered for large inputs?",
            "Parameters modified correctly in recursive calls?",
        ]
        
        print("Recursion Checklist:")
        for check in checklist:
            print(f"  [ ] {check}")
        
        return []
    
    def analyze_array_access(self, code: str) -> List[BugReport]:
        """Check array indexing"""
        
        print("\n🔍 Static Analysis: Array Access")
        
        checklist = [
            "Array bounds checked before access?",
            "Index variables initialized correctly?",
            "No off-by-one in index calculations?",
            "Negative indices handled (for languages that allow)?",
            "Empty array case handled?",
        ]
        
        print("Array Access Checklist:")
        for check in checklist:
            print(f"  [ ] {check}")
        
        return []

# ============================================
# PHASE 2: INVARIANT CHECKING
# ============================================

class InvariantChecker:
    """Verify loop/algorithm invariants hold"""
    
    @staticmethod
    def check_binary_search_invariants(arr: List[int], target: int) -> bool:
        """Binary search with invariant checking"""
        
        print("\n🔍 Invariant Checking: Binary Search")
        
        if not arr:
            return False
        
        left, right = 0, len(arr) - 1
        iteration = 0
        
        while left <= right:
            iteration += 1
            
            # INVARIANT 1: Bounds are valid
            assert 0 <= left <= len(arr), f"Invalid left: {left}"
            assert 0 <= right < len(arr), f"Invalid right: {right}"
            
            # INVARIANT 2: If target exists, it's in [left, right]
            # (Cannot verify directly, but we check we're narrowing)
            
            mid = (left + right) // 2
            
            print(f"Iteration {iteration}: left={left}, mid={mid}, right={right}, arr[mid]={arr[mid]}")
            
            # INVARIANT 3: mid is within bounds
            assert left <= mid <= right, f"mid out of bounds: {mid}"
            
            if arr[mid] == target:
                print(f"✅ Found at index {mid}")
                return True
            elif arr[mid] < target:
                # INVARIANT 4: Moving left pointer forward
                old_left = left
                left = mid + 1
                assert left > old_left, "Left pointer not advancing"
            else:
                # INVARIANT 5: Moving right pointer backward
                old_right = right
                right = mid - 1
                assert right < old_right, "Right pointer not retreating"
        
        print("❌ Not found")
        return False

# ============================================
# PHASE 3: BOUNDARY TESTING
# ============================================

class BoundaryTester:
    """Test edge cases systematically"""
    
    @staticmethod
    def generate_boundary_tests_for_array_problem() -> List[Tuple[List[int], str]]:
        """Generate comprehensive boundary tests"""
        
        return [
            # Size boundaries
            ([], "empty array"),
            ([1], "single element"),
            ([1, 2], "two elements"),
            
            # Value boundaries
            ([0], "zero value"),
            ([2**31 - 1], "max int"),
            ([-2**31], "min int"),
            ([2**31 - 1, -2**31], "both extremes"),
            
            # Duplicate boundaries
            ([1, 1, 1, 1], "all duplicates"),
            ([1, 1, 2, 2], "pair duplicates"),
            
            # Order boundaries
            ([1, 2, 3, 4, 5], "sorted ascending"),
            ([5, 4, 3, 2, 1], "sorted descending"),
            ([1], "single element sorted"),
            
            # Pattern boundaries
            ([1, -1, 1, -1], "alternating"),
            ([1, 2, 1, 2, 1], "repeating pattern"),
            
            # Special values
            ([0, 0, 0], "all zeros"),
            ([-1, -2, -3], "all negative"),
            ([10**9, 10**9], "large values"),
        ]
    
    @staticmethod
    def test_function_with_boundaries(func, description: str):
        """Test a function with all boundary cases"""
        
        print(f"\n🎯 Boundary Testing: {description}")
        
        tests = BoundaryTester.generate_boundary_tests_for_array_problem()
        passed = 0
        failed = 0
        
        for arr, desc in tests:
            try:
                result = func(arr)
                print(f"✅ {desc}: {result}")
                passed += 1
            except Exception as e:
                print(f"❌ {desc}: CRASHED with {e}")
                failed += 1
        
        print(f"\nResults: {passed} passed, {failed} failed")

# ============================================
# PHASE 4: DELTA DEBUGGING
# ============================================

class DeltaDebugger:
    """Minimize failing test case"""
    
    @staticmethod
    def minimize_failing_input(
        func,
        failing_input: List[int],
        expected_output,
        timeout: float = 10.0
    ) -> List[int]:
        """
        Given a failing test case, find the minimal input that still fails
        
        Example: [1, 2, 3, 4, 5, 6, 7, 8] fails -> minimal is [3, 7]
        """
        
        print("\n🔬 Delta Debugging: Minimizing failing input")
        print(f"Original input size: {len(failing_input)}")
        
        current = failing_input.copy()
        
        # Try removing each element
        improved = True
        while improved:
            improved = False
            for i in range(len(current)):
                # Try removing element at index i
                candidate = current[:i] + current[i+1:]
                
                if not candidate:
                    continue
                
                try:
                    result = func(candidate)
                    if result != expected_output:
                        # Still fails with smaller input!
                        current = candidate
                        improved = True
                        print(f"  Reduced to size {len(current)}: {current}")
                        break
                except:
                    # Still crashes with smaller input
                    current = candidate
                    improved = True
                    print(f"  Reduced to size {len(current)}: {current}")
                    break
        
        print(f"Minimal failing input: {current}")
        return current

# ============================================
# PHASE 5: DEBUGGING BY ASSERTION INJECTION
# ============================================

class AssertionInjector:
    """Add runtime checks to catch bugs early"""
    
    @staticmethod
    def binary_search_with_assertions(arr: List[int], target: int) -> int:
        """Binary search with extensive assertions"""
        
        # Pre-condition checks
        assert arr == sorted(arr), "Array must be sorted!"
        
        if not arr:
            return -1
        
        left, right = 0, len(arr) - 1
        
        while left <= right:
            # Invariant checks
            assert 0 <= left < len(arr), f"Left out of bounds: {left}"
            assert 0 <= right < len(arr), f"Right out of bounds: {right}"
            assert left <= right, f"Pointers crossed: left={left}, right={right}"
            
            mid = (left + right) // 2
            
            # Mid validity
            assert left <= mid <= right, f"Mid out of range: {mid}"
            
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                old_left = left
                left = mid + 1
                # Progress check
                assert left > old_left, "Left not advancing!"
            else:
                old_right = right
                right = mid - 1
                # Progress check
                assert right < old_right, "Right not retreating!"
        
        return -1

# ============================================
# PHASE 6: COMMON BUG PATTERNS & FIXES
# ============================================

class BugPatternLibrary:
    """Library of common bugs and how to detect them"""
    
    @staticmethod
    def demonstrate_common_bugs():
        """Show common bugs and their fixes"""
        
        print("\n" + "="*60)
        print("COMMON BUG PATTERNS")
        print("="*60)
        
        patterns = [
            {
                'name': 'Off-by-One Error',
                'buggy': 'for i in range(len(arr) - 1)',  # Misses last element
                'fixed': 'for i in range(len(arr))',
                'detection': 'Test with single element array',
            },
            {
                'name': 'Integer Overflow',
                'buggy': 'mid = (left + right) // 2',  # Can overflow
                'fixed': 'mid = left + (right - left) // 2',
                'detection': 'Test with large indices',
            },
            {
                'name': 'Wrong Loop Condition',
                'buggy': 'while left < right',  # Misses when left == right
                'fixed': 'while left <= right',
                'detection': 'Test with single element',
            },
            {
                'name': 'Not Checking Empty',
                'buggy': 'return arr[0]',  # Crashes on empty array
                'fixed': 'if not arr: return None\nreturn arr[0]',
                'detection': 'Test with empty array',
            },
            {
                'name': 'Infinite Loop',
                'buggy': 'while True: if cond: break',
                'fixed': 'Add iteration counter or better exit condition',
                'detection': 'Add timeout or max iterations',
            },
        ]
        
        for i, pattern in enumerate(patterns, 1):
            print(f"\n{i}. {pattern['name']}")
            print(f"   Buggy:  {pattern['buggy']}")
            print(f"   Fixed:  {pattern['fixed']}")
            print(f"   Detect: {pattern['detection']}")

# ============================================
# MASTER BUG DETECTION WORKFLOW
# ============================================

def master_debug_workflow(function, test_input, expected_output):
    """
    Complete debugging workflow
    """
    
    print("\n" + "="*60)
    print("MASTER DEBUGGING WORKFLOW")
    print("="*60)
    
    # Step 1: Static Analysis
    print("\nSTEP 1: Static Analysis")
    analyzer = StaticAnalyzer()
    analyzer.analyze_loop("function code")
    analyzer.analyze_array_access("function code")
    
    # Step 2: Boundary Testing
    print("\nSTEP 2: Boundary Testing")
    boundary_tester = BoundaryTester()
    # Run boundary tests
    
    # Step 3: Run with assertions
    print("\nSTEP 3: Runtime Assertion Checking")
    try:
        result = function(test_input)
        print(f"Result: {result}")
        if result != expected_output:
            print(f"❌ MISMATCH: Expected {expected_output}, got {result}")
    except AssertionError as e:
        print(f"❌ ASSERTION FAILED: {e}")
    except Exception as e:
        print(f"❌ CRASHED: {e}")
    
    # Step 4: If failed, minimize test case
    print("\nSTEP 4: Minimize Failing Test Case")
    # Use delta debugging
    
    # Step 5: Check invariants
    print("\nSTEP 5: Verify Invariants")
    # Check loop invariants
    
    print("\n" + "="*60)
    print("DEBUGGING COMPLETE")
    print("="*60)

# ============================================
# DEMONSTRATION
# ============================================

if __name__ == "__main__":
    # Demonstrate invariant checking
    InvariantChecker.check_binary_search_invariants([1, 2, 3, 4, 5], 3)
    
    # Demonstrate boundary testing
    def sample_max(arr):
        return max(arr) if arr else None
    
    BoundaryTester.test_function_with_boundaries(sample_max, "max() function")
    
    # Show common bug patterns
    BugPatternLibrary.demonstrate_common_bugs()


# Algorithm Learning Priority Map
## Path to Top 1% in DSA

---

## **TIER 0: ABSOLUTE FUNDAMENTALS (Week 1-2)**
*Master these before anything else*

### Arrays & Strings
- **Two Pointers** (left/right converging)
- **Sliding Window** (fixed/variable size)
- **Prefix Sum** (range queries O(1))

### Basic Patterns
- **Frequency Counting** (hash map patterns)
- **In-place Modification**
- **Index Manipulation**

**Time Investment:** 2 weeks, ~50 problems
**Why First:** 60% of easy/medium problems use these

---

## **TIER 1: CORE ALGORITHMS (Week 3-8)**
*These solve 70% of interview problems*

### 1. Binary Search & Variants (Week 3)
- Classic binary search
- Search in rotated array
- Find first/last occurrence
- **Binary search on answer** (most important!)

**Pattern Recognition:**
- "Find minimum/maximum where condition holds"
- "Find k-th element"
- Monotonic function → binary search

**Must-Know Problems:**
- Find peak element
- Search 2D matrix
- Koko eating bananas
- Minimum in rotated sorted array

---

### 2. Recursion & Backtracking (Week 4-5)
- Generate all subsets/permutations
- Constraint satisfaction
- **Decision tree visualization**

**Pattern Recognition:**
- "Generate all possible..."
- "Find all valid combinations"
- Multiple choices at each step

**Must-Know Problems:**
- Generate parentheses
- N-Queens
- Word search
- Combination sum

---

### 3. Dynamic Programming Foundations (Week 6-8)
**Learn in this order:**
1. **1D DP** (Fibonacci, house robber)
2. **2D DP** (grid paths, LCS)
3. **DP on substrings** (palindromes)
4. **Knapsack variants** (0/1, unbounded)

**Pattern Recognition:**
- "Optimize/count ways to..."
- Overlapping subproblems
- Optimal substructure

**Must-Know Problems:**
- Coin change
- Longest increasing subsequence
- Edit distance
- Maximum subarray

**Pro Tip:** Always start with recursion + memoization, then convert to bottom-up

---

### 4. Graph Algorithms (Week 9-12)
**Core Techniques:**
- **DFS** (connected components, cycle detection)
- **BFS** (shortest path in unweighted graph)
- **Topological Sort** (prerequisites, course schedule)
- **Union-Find** (connected components, Kruskal's)

**Pattern Recognition:**
- "All connected..." → DFS
- "Shortest path..." → BFS
- "Dependencies..." → Topological Sort
- "Groups/clusters..." → Union-Find

**Must-Know Problems:**
- Number of islands
- Course schedule I & II
- Clone graph
- Network delay time

**Skip Initially:** Dijkstra, Bellman-Ford, Floyd-Warshall (rare in interviews)

---

## **TIER 2: ADVANCED PATTERNS (Month 4-6)**
*Needed for hard problems and top companies*

### 5. Tree Algorithms
- **Tree traversals** (iterative versions!)
- **Binary Search Tree** properties
- **Lowest Common Ancestor**
- **Path sum problems**

**Pattern Recognition:**
- "Find path..." → DFS with state
- "Level-wise..." → BFS
- "BST property..." → In-order traversal

---

### 6. Heap (Priority Queue)
- **Top K problems**
- **Merge K sorted lists**
- **Running median**

**Pattern Recognition:**
- "K-th largest/smallest"
- "Maintain top K elements"
- "Merge sorted..."

**Must-Know:**
- K closest points
- Meeting rooms II
- Task scheduler

---

### 7. Advanced DP Patterns
- **State machine DP** (buy/sell stock)
- **DP with bitmasking** (traveling salesman)
- **Interval DP** (burst balloons)
- **DP on trees**

---

### 8. Advanced Graph
- **Shortest path with weights** (Dijkstra)
- **Minimum Spanning Tree** (Kruskal/Prim)
- **Strongly Connected Components**

**When to Learn:** Only after mastering Tier 1 graphs

---

## **TIER 3: SPECIALIZED (Month 6+)**
*Learn on-demand when you encounter them*

### Rare but Powerful
- **Trie** (prefix problems, autocomplete)
- **Segment Tree** (range queries with updates)
- **Monotonic Stack** (next greater element)
- **KMP / Rabin-Karp** (string matching)
- **Bitwise DP** (subset enumeration)

**Learn When Needed:** Don't waste time memorizing until you see the pattern

---

## **LEARNING STRATEGY: The 3-Pass System**

### Pass 1: Recognition (2 days per topic)
- Read about the pattern
- Solve 5 easy problems
- **Goal:** Recognize when to use it

### Pass 2: Mastery (1 week per topic)
- Solve 15-20 medium problems
- Implement from scratch (no looking!)
- **Goal:** Solve without hints

### Pass 3: Expertise (Ongoing)
- Solve hard problems
- Teach the concept to someone
- **Goal:** Apply creatively

---

## **FAST-TRACK LEARNING TECHNIQUES**

### 1. Pattern-Based Learning (NOT Algorithm-Based)
Instead of learning "algorithm X", learn "when to apply X"

**Example:**
```
Pattern: "Find k-th element in sorted/partially sorted structure"
Solutions:
- Binary search on answer
- Quickselect
- Heap
- Counting sort

When to use which? Depends on constraints!
```

### 2. The "Learn by Solving" Method
**Don't read theory first!**

Process:
1. Attempt problem (even if you fail)
2. Read solution
3. Implement without looking
4. Solve 2 similar problems immediately

**Why it works:** Active recall + spaced repetition

### 3. The "Template" Approach
Create templates for common patterns:

**Binary Search Template:**
```python
def binary_search_template(arr, condition):
    left, right = 0, len(arr) - 1
    result = -1
    
    while left <= right:
        mid = left + (right - left) // 2
        if condition(arr[mid]):
            result = mid
            # Search left/right for better answer
        # Update left or right
    
    return result
```

**Backtracking Template:**
```python
def backtrack(path, choices):
    if is_complete(path):
        result.append(path.copy())
        return
    
    for choice in choices:
        if is_valid(choice):
            path.append(choice)
            backtrack(path, get_next_choices(choice))
            path.pop()  # RESTORE STATE
```

### 4. The "Explain to a 5-Year-Old" Test
If you can't explain the algorithm simply, you don't understand it.

**Example:**
- **Bad:** "Binary search has O(log n) complexity because..."
- **Good:** "We split the problem in half each time, like guessing a number between 1-100 by asking 'higher or lower?'"

---

## **COMPETITIVE PROGRAMMING SPECIFIC**

### For Codeforces/Contests:
1. **Speed over elegance** in contests
2. Learn **Fast I/O** techniques
3. Master **STL/standard libraries**
4. Know **number theory basics** (GCD, LCM, modular arithmetic)

### For Interviews (FAANG):
1. **Explanation matters** more than speed
2. Focus on **common patterns**
3. Skip rare algorithms (Suffix Array, Heavy-Light Decomposition)

---

## **THE 100-DAY ROADMAP TO TOP 1%**

### Days 1-30: Foundations
- Two pointers: 20 problems
- Sliding window: 15 problems
- Binary search: 20 problems
- Hash maps: 15 problems

### Days 31-60: Core Algorithms
- Backtracking: 15 problems
- Basic DP: 25 problems
- DFS/BFS: 20 problems
- Trees: 15 problems

### Days 61-90: Advanced
- Advanced DP: 20 problems
- Heaps: 10 problems
- Union-Find: 10 problems
- Tries: 5 problems

### Days 91-100: Hard Problems
- Solve 30+ hard problems
- Mix all patterns
- Time yourself

**Daily Commitment:** 2-3 hours
**Total Problems:** ~250-300

---

## **CRITICAL SUCCESS FACTORS**

### ❌ Don't Do This:
- Learn algorithms in isolation
- Jump to hard problems too early
- Give up after 30 minutes
- Only read solutions

### ✅ Do This Instead:
- **Struggle for 45 minutes** before looking
- **Implement solutions from memory** next day
- **Solve similar problems immediately** (while pattern is fresh)
- **Explain your solution out loud**

---

## **THE ULTIMATE METRIC**

Track this monthly:
```
Recognition Rate = (Problems you recognize pattern / Total problems) * 100

Target:
Month 1: 30%
Month 2: 50%
Month 3: 70%
Month 4: 85%+
```

When you hit 85%+ recognition, you're in the top 1%.

---

## **RESOURCES (In Priority Order)**

1. **LeetCode Patterns** (free GitHub repo)
2. **Blind 75** (curated list)
3. **Striver's SDE Sheet** (comprehensive)
4. **Codeforces Problemset** (for speed)
5. **CSES Problem Set** (for fundamentals)

**One Rule:** Finish one resource before starting another.

---

## **FINAL WISDOM**

> "You don't need to know 1000 algorithms. You need to know 20 patterns deeply enough to recognize them in 1000 different disguises."

Focus on **pattern recognition** over **algorithm memorization**.

The top 1% doesn't know more algorithms—they recognize patterns faster.

---

**Now go solve problems. Theory without practice is useless. 🔥**

