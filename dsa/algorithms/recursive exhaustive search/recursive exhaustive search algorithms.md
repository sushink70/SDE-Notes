# Complete List of Recursive Exhaustive Search Algorithms

## 1. **Backtracking** ⭐
Already covered - DFS with pruning and state restoration

---

## 2. **Depth-First Search (DFS)**
Pure recursive tree/graph traversal without pruning

```python
def dfs(node, visited):
    if node in visited:
        return
    visited.add(node)
    
    for neighbor in node.neighbors:
        dfs(neighbor, visited)
```

**Use**: Graph traversal, cycle detection, topological sort

---

## 3. **Branch and Bound**
Backtracking + optimization bound to prune suboptimal branches

```python
def branch_and_bound(node, current_cost, best_cost):
    if current_cost >= best_cost:
        return  # Prune: can't improve
    
    if is_solution(node):
        best_cost = min(best_cost, current_cost)
        return
    
    for child in node.children:
        branch_and_bound(child, current_cost + cost(child), best_cost)
```

**Use**: Traveling Salesman, 0/1 Knapsack, Job Scheduling

---

## 4. **Recursive Divide and Conquer**
Split problem, solve recursively, combine results

```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])   # Divide
    right = merge_sort(arr[mid:])  # Divide
    
    return merge(left, right)       # Conquer
```

**Use**: Merge Sort, Quick Sort, Binary Search, Strassen's Matrix Multiplication

---

## 5. **Brute Force Recursion**
Try all combinations without any pruning

```python
def all_binary_strings(n, s=""):
    if n == 0:
        print(s)
        return
    
    all_binary_strings(n-1, s + "0")
    all_binary_strings(n-1, s + "1")
```

**Use**: Generate all possible solutions when no optimization possible

---

## 6. **Recursive Best-First Search (RBFS)**
DFS-like but keeps track of alternative paths

```python
def rbfs(node, f_limit):
    if is_goal(node):
        return node
    
    successors = generate_successors(node)
    if not successors:
        return None, infinity
    
    for s in successors:
        s.f = max(g(s) + h(s), node.f)
    
    while True:
        best = min(successors, key=lambda x: x.f)
        if best.f > f_limit:
            return None, best.f
        
        alternative = second_best(successors)
        result, best.f = rbfs(best, min(f_limit, alternative))
        
        if result:
            return result
```

**Use**: Memory-efficient A* alternative

---

## 7. **Iterative Deepening DFS (IDDFS)**
Repeatedly performs DFS with increasing depth limits

```python
def iddfs(root, max_depth):
    for depth in range(max_depth):
        result = dfs_limited(root, depth)
        if result:
            return result
    return None

def dfs_limited(node, depth):
    if depth == 0:
        return node if is_goal(node) else None
    if depth > 0:
        for child in node.children:
            result = dfs_limited(child, depth - 1)
            if result:
                return result
    return None
```

**Use**: When solution depth unknown, combines DFS memory efficiency with BFS completeness

---

## 8. **Minimax**
Exhaustively explores game tree to find optimal move

```python
def minimax(node, depth, maximizing):
    if depth == 0 or is_terminal(node):
        return evaluate(node)
    
    if maximizing:
        max_eval = -infinity
        for child in node.children:
            eval = minimax(child, depth-1, False)
            max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = infinity
        for child in node.children:
            eval = minimax(child, depth-1, True)
            min_eval = min(min_eval, eval)
        return min_eval
```

**Use**: Two-player games (Chess, Tic-Tac-Toe)

---

## 9. **Alpha-Beta Pruning**
Minimax with pruning of branches that won't affect final decision

```python
def alpha_beta(node, depth, alpha, beta, maximizing):
    if depth == 0 or is_terminal(node):
        return evaluate(node)
    
    if maximizing:
        max_eval = -infinity
        for child in node.children:
            eval = alpha_beta(child, depth-1, alpha, beta, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # Prune
        return max_eval
    else:
        min_eval = infinity
        for child in node.children:
            eval = alpha_beta(child, depth-1, alpha, beta, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break  # Prune
        return min_eval
```

**Use**: Game AI with pruning

---

## 10. **Monte Carlo Tree Search (MCTS)**
Uses random sampling to explore game tree

```python
def mcts(root, iterations):
    for _ in range(iterations):
        node = root
        
        # Selection
        while not node.is_terminal() and node.is_fully_expanded():
            node = node.best_child()
        
        # Expansion
        if not node.is_terminal():
            node = node.expand()
        
        # Simulation
        reward = simulate(node)
        
        # Backpropagation
        while node:
            node.update(reward)
            node = node.parent
    
    return root.best_child()
```

**Use**: AlphaGo, game AI with large branching factors

---

## 11. **Generate and Test**
Generate candidate solutions recursively, test validity

```python
def generate_and_test(n):
    def generate(partial_solution):
        if is_complete(partial_solution):
            if test(partial_solution):
                solutions.append(partial_solution[:])
            return
        
        for choice in get_choices():
            partial_solution.append(choice)
            generate(partial_solution)
            partial_solution.pop()
    
    solutions = []
    generate([])
    return solutions
```

**Use**: Cryptarithmetic puzzles, constraint problems

---

## 12. **Limited Discrepancy Search (LDS)**
Explores paths in order of "discrepancies" from heuristic

```python
def lds(node, discrepancies_left):
    if is_goal(node):
        return node
    
    children = sorted(node.children, key=heuristic)
    
    # Try best child with same discrepancy budget
    result = lds(children[0], discrepancies_left)
    if result:
        return result
    
    # Try other children if we have discrepancies left
    if discrepancies_left > 0:
        for child in children[1:]:
            result = lds(child, discrepancies_left - 1)
            if result:
                return result
    
    return None
```

**Use**: Heuristic search with systematic deviation

---

## 13. **Recursive Random Search**
Random exploration with backtracking

```python
import random

def random_search(state, depth):
    if is_goal(state):
        return state
    
    if depth == 0:
        return None
    
    actions = get_actions(state)
    random.shuffle(actions)
    
    for action in actions:
        new_state = apply(state, action)
        result = random_search(new_state, depth - 1)
        if result:
            return result
    
    return None
```

**Use**: Randomized constraint satisfaction

---

## 14. **Recursive Beam Search**
Keep only k best nodes at each level

```python
def beam_search_recursive(nodes, beam_width, depth):
    if depth == 0 or all(is_goal(n) for n in nodes):
        return best(nodes)
    
    all_successors = []
    for node in nodes:
        all_successors.extend(expand(node))
    
    # Keep only top k
    best_k = sorted(all_successors, key=evaluate)[:beam_width]
    
    return beam_search_recursive(best_k, beam_width, depth - 1)
```

**Use**: Large search spaces with memory constraints

---

## 15. **Forward Checking (Constraint Propagation)**
Backtracking with look-ahead constraint checking

```python
def forward_checking(assignment, domains):
    if is_complete(assignment):
        return assignment
    
    var = select_unassigned_variable(assignment)
    
    for value in domains[var]:
        if is_consistent(var, value, assignment):
            assignment[var] = value
            
            # Propagate constraints
            new_domains = propagate_constraints(var, value, domains)
            
            if not any(len(d) == 0 for d in new_domains.values()):
                result = forward_checking(assignment, new_domains)
                if result:
                    return result
            
            del assignment[var]
    
    return None
```

**Use**: CSP with constraint propagation

---

## 16. **Arc Consistency (AC-3 with Backtracking)**
Maintains arc consistency during search

```python
def mac(assignment, domains):
    if is_complete(assignment):
        return assignment
    
    var = select_unassigned_variable(assignment)
    
    for value in domains[var]:
        if is_consistent(var, value, assignment):
            assignment[var] = value
            
            new_domains = domains.copy()
            new_domains[var] = [value]
            
            if ac3(new_domains):  # Maintain arc consistency
                result = mac(assignment, new_domains)
                if result:
                    return result
            
            del assignment[var]
    
    return None
```

**Use**: Advanced CSP solving

---

## 17. **Chronological Backtracking**
Standard backtracking that undoes most recent decision

```python
def chronological_backtrack(vars, domains, assignment):
    if len(assignment) == len(vars):
        return assignment
    
    var = vars[len(assignment)]
    
    for value in domains[var]:
        if is_consistent(var, value, assignment):
            assignment[var] = value
            
            result = chronological_backtrack(vars, domains, assignment)
            if result:
                return result
            
            del assignment[var]
    
    return None
```

**Use**: Basic CSP, simpler than conflict-directed

---

## 18. **Conflict-Directed Backjumping**
Jumps back to source of conflict, not just previous variable

```python
def backjumping(assignment, domains, conflict_set):
    if is_complete(assignment):
        return assignment
    
    var = select_unassigned_variable(assignment)
    
    for value in domains[var]:
        if is_consistent(var, value, assignment):
            assignment[var] = value
            
            result, conflicts = backjumping(assignment, domains, {})
            if result:
                return result, {}
            
            conflict_set.update(conflicts)
            del assignment[var]
            
            if conflict_set and var not in conflict_set:
                return None, conflict_set
    
    conflict_set.add(var)
    return None, conflict_set
```

**Use**: Intelligent backtracking in CSP

---

## 19. **Recursive A* / IDA***
A* implemented recursively with iterative deepening

```python
def ida_star(start, goal):
    threshold = heuristic(start, goal)
    
    def search(node, g, threshold):
        f = g + heuristic(node, goal)
        
        if f > threshold:
            return f, None
        
        if node == goal:
            return f, [node]
        
        min_threshold = infinity
        for neighbor in node.neighbors:
            new_g = g + cost(node, neighbor)
            t, path = search(neighbor, new_g, threshold)
            
            if path:
                return t, [node] + path
            
            min_threshold = min(min_threshold, t)
        
        return min_threshold, None
    
    while True:
        t, path = search(start, 0, threshold)
        if path:
            return path
        if t == infinity:
            return None
        threshold = t
```

**Use**: Memory-efficient pathfinding

---

## 20. **Dancing Links (DLX) / Algorithm X**
Knuth's recursive algorithm for exact cover problems

```python
def algorithm_x(matrix, solution):
    if not matrix:
        yield list(solution)
        return
    
    # Choose column with fewest 1s
    col = min(range(len(matrix[0])), key=lambda c: sum(row[c] for row in matrix))
    
    for i, row in enumerate(matrix):
        if row[col]:
            solution.append(i)
            
            # Remove covered rows and columns
            new_matrix = reduce_matrix(matrix, i, col)
            
            yield from algorithm_x(new_matrix, solution)
            
            solution.pop()
```

**Use**: Sudoku solving, N-Queens, pentomino puzzles

---

## Comparison Table

| Algorithm | Pruning | Optimization | Memory | Best For |
|-----------|---------|--------------|--------|----------|
| DFS | None | No | O(d) | Graph traversal |
| Backtracking | Yes | No | O(d) | CSP, combinations |
| Branch & Bound | Yes | Yes | O(d) | Optimization |
| Minimax | None | Yes | O(bd) | Games |
| Alpha-Beta | Yes | Yes | O(d) | Games, pruning |
| IDDFS | Depth limit | No | O(d) | Unknown depth |
| MCTS | Sampling | Yes | O(n) | Complex games |
| IDA* | Heuristic | Yes | O(d) | Pathfinding |

---

## Summary Categories

**Pure Search:**
- DFS, BFS variants, IDDFS

**With Pruning:**
- Backtracking, Alpha-Beta, Branch & Bound

**Game Theory:**
- Minimax, Alpha-Beta, MCTS

**Constraint Satisfaction:**
- Forward Checking, Arc Consistency, Backjumping

**Heuristic-Guided:**
- A*, IDA*, RBFS, Beam Search

**Specialized:**
- Dancing Links, LDS

All share recursive exhaustive exploration but differ in **when/how they prune** and **what they optimize for**!