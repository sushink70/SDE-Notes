# Task Scheduling - Comprehensive Guide to Algorithm Implementation

*A journey from foundational principles to mastery-level problem-solving*

---

## Table of Contents
1. [Foundation: What is Task Scheduling?](#foundation)
2. [Core Concepts & Terminology](#concepts)
3. [Problem Categories & Mental Models](#categories)
4. [Classical Algorithms](#algorithms)
5. [Implementation in Rust, Python, Go](#implementation)
6. [Advanced Patterns & Optimizations](#advanced)
7. [Practice Strategy & Cognitive Framework](#practice)

---

## 1. Foundation: What is Task Scheduling? {#foundation}

**Task scheduling** is the algorithmic problem of ordering and allocating tasks to resources (processors, machines, time slots) to optimize specific objectives like:
- Minimizing total completion time
- Maximizing throughput
- Meeting deadlines
- Minimizing waiting time or latency

### Real-World Analogies (Mental Model Building)

Think of task scheduling like:
- **Chef coordinating dishes**: Multiple dishes need different cooking times and equipment
- **Operating system**: CPU scheduling multiple processes
- **Project manager**: Allocating team members to tasks with dependencies
- **Airport**: Scheduling plane takeoffs/landings on limited runways

### Why It Matters for Top 1% Mastery

Task scheduling develops:
1. **Greedy thinking** - making locally optimal choices
2. **Priority queue manipulation** - efficient ordering
3. **Graph reasoning** - handling dependencies (DAG structures)
4. **Dynamic programming** - optimal substructure recognition
5. **Mathematical proof skills** - proving correctness of greedy choices

---

## 2. Core Concepts & Terminology {#concepts}

Before diving into algorithms, let's build precise definitions:

### 2.1 Basic Terms

**Task/Job**: A unit of work with properties like:
- **Duration/Processing time**: How long it takes
- **Deadline**: When it must finish
- **Weight/Priority**: Importance/penalty for delay
- **Profit/Value**: Reward for completion

**Resource/Machine**: The executor of tasks (CPU, worker, machine)

**Schedule**: An assignment of tasks to time slots and resources

**Completion Time (C_i)**: When task i finishes

**Turnaround Time**: C_i - arrival_time (in online scheduling)

**Lateness (L_i)**: C_i - deadline_i (can be negative if early)

**Tardiness (T_i)**: max(0, L_i) (late only)

**Makespan**: Maximum completion time across all tasks (finish time of schedule)

### 2.2 Constraint Types

**Precedence Constraints**: Task A must complete before Task B starts
- Represented as **Directed Acyclic Graph (DAG)**
- **Predecessor**: A task that must come before
- **Successor**: A task that must come after

**Release Time (r_i)**: Earliest time task i can start

**Preemption**: Can interrupt a task and resume later
- **Preemptive**: Can pause/resume
- **Non-preemptive**: Must run to completion once started

### 2.3 Optimization Objectives

**Makespan minimization**: min(max(C_i))
**Total completion time**: min(∑C_i)
**Weighted completion time**: min(∑w_i × C_i)
**Maximum lateness**: min(max(L_i))
**Number of late jobs**: min(∑(L_i > 0))

---

## 3. Problem Categories & Mental Models {#categories}

### Category 1: Single Machine Scheduling

```
Machine: [----Task1----][--Task2--][-----Task3-----]
Time:     0            10         20              35
```

**Mental Model**: You have ONE worker who can only do one thing at a time. How do you order tasks?

**Key Insight**: Order matters tremendously! Different orderings produce different outcomes.

### Category 2: Parallel Machine Scheduling

```
Machine 1: [--Task1--][----Task3----]
Machine 2: [----Task2----][--Task4--]
Machine 3: [------Task5------]
Time:       0          10           20
```

**Mental Model**: Multiple workers, assign tasks to minimize idle time and total completion.

### Category 3: Task Scheduling with Dependencies

```
        Task1
       /     \
    Task2   Task3
       \     /
        Task4
```

**Mental Model**: Some tasks MUST happen before others (think cooking: chop vegetables BEFORE stir-frying).

### Category 4: Interval Scheduling

```
Task1: [=====]
Task2:    [====]
Task3:        [======]
Task4:   [==]
Time:   0  1  2  3  4  5  6
```

**Mental Model**: Tasks have fixed start/end times. Select maximum non-overlapping set.

---

## 4. Classical Algorithms {#algorithms}

### 4.1 Shortest Job First (SJF) - Minimizing Average Completion Time

**Problem**: Given n tasks with processing times, minimize average completion time.

**Algorithm**: Process tasks in increasing order of processing time.

**Why It Works** (Proof Sketch):
- Consider any two adjacent tasks i, j where p_i > p_j
- Swapping them reduces total completion time
- Therefore, sorting is optimal

**ASCII Visualization**:
```
Before sorting:
Tasks:    [5] [2] [8] [1]
Schedule: [--5--][2][---8---][1]
Compl:    5      7  15       16
Total: 5+7+15+16 = 43

After SJF:
Tasks:    [1] [2] [5] [8]
Schedule: [1][2][--5--][---8---]
Compl:    1  3  8       16
Total: 1+3+8+16 = 28 ✓ Better!
```

**Cognitive Principle**: **Greedy Exchange Argument** - If swapping improves outcome, keep swapping until optimal.

### 4.2 Weighted Shortest Job First (WSJF) - Minimizing Weighted Completion Time

**Problem**: Tasks have weights (importance). Minimize ∑w_i × C_i.

**Algorithm**: Sort by ratio w_i/p_i (weight/processing time) in DECREASING order.

**Mental Model**: Do high "bang for buck" tasks first (high value, low time).

**Why It Works**:
- Task with ratio w_i/p_i should be prioritized
- If you spend time p_i, you "pay" w_i × p_i for every unit of delay
- Maximize value per unit time

**Example**:
```
Task  | Weight | Time | Ratio (w/p)
------|--------|------|------------
A     | 10     | 2    | 5.0  ← Do first
B     | 6      | 3    | 2.0  ← Do second
C     | 4      | 4    | 1.0  ← Do last
```

### 4.3 Earliest Deadline First (EDF) - Minimizing Maximum Lateness

**Problem**: Tasks have deadlines. Minimize maximum lateness.

**Algorithm**: Sort tasks by deadline (earliest first).

**ASCII Visualization**:
```
Task | Time | Deadline
-----|------|----------
A    | 3    | 6
B    | 2    | 8
C    | 1    | 9

EDF Order: A → B → C
Timeline:
[---A---][--B--][C]
0       3      5  6
Lateness: 
A: 3-6 = -3 (early)
B: 5-8 = -3 (early)
C: 6-9 = -3 (early)
Max Lateness = -3 ✓

Wrong order (C → B → A):
[C][--B--][---A---]
0  1      3       6
Lateness:
C: 1-9 = -8
B: 3-8 = -5
A: 6-6 = 0
Max Lateness = 0 (worse)
```

**Proof Technique**: **Idle Time Argument** - Show that scheduling idle time or inverting order increases lateness.

### 4.4 Moore's Algorithm - Minimizing Number of Late Jobs

**Problem**: Maximize jobs completed by their deadline (equivalently, minimize late jobs).

**Algorithm**: (Greedy + Dynamic Repair)
1. Sort tasks by deadline
2. Schedule greedily
3. If a task would be late, remove the longest task so far (including current)
4. Continue

**Why It's Non-Obvious**: Sometimes you must *remove* a scheduled task to fit more tasks!

**Flowchart**:
```
┌─────────────────────┐
│ Sort by deadline    │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Next task    │
    └──────┬───────┘
           │
           ▼
    ╔══════════════════╗
    ║ Would it be late?║
    ╚══════╤═══════════╝
           │
      ┌────┴────┐
      │         │
     Yes       No
      │         │
      ▼         ▼
  ┌───────┐  ┌────────┐
  │Remove │  │Schedule│
  │longest│  │  task  │
  │ task  │  └────┬───┘
  └───┬───┘       │
      │           │
      └─────┬─────┘
            │
            ▼
      ┌──────────┐
      │   Done?  │
      └─────┬────┘
            │
      ┌─────┴─────┐
     Yes          No
      │            │
      ▼            │
   ┌─────┐         │
   │ End │◄────────┘
   └─────┘
```

**Example**:
```
Task | Time | Deadline
-----|------|----------
A    | 2    | 4
B    | 1    | 5
C    | 3    | 6
D    | 4    | 7

Step-by-step:
1. Schedule A: time=2, deadline=4 ✓
2. Schedule B: time=3, deadline=5 ✓
3. Try C: time=6, deadline=6 ✓
4. Try D: time=10, deadline=7 ✗ (late!)
   → Remove longest (D itself? or C with time 3)
   → Remove C (time 3) to make room
   → Schedule D: time=7, deadline=7 ✓

Final: A, B, D (3 jobs on time)
```

### 4.5 Interval Scheduling - Maximum Non-Overlapping Intervals

**Problem**: Given intervals [start_i, end_i], select maximum number of non-overlapping intervals.

**Algorithm**: Greedy by earliest finish time
1. Sort by finish time
2. Greedily pick if it doesn't overlap with last picked

**Why It Works**:
- Picking earliest finish leaves most room for future intervals
- **Staying Ahead Proof**: Our solution is always "ahead" of any other solution

**ASCII Decision Tree**:
```
Intervals: [1,3] [2,5] [4,7] [6,9] [8,10]

Sort by finish: [1,3] [2,5] [4,7] [6,9] [8,10]

Pick [1,3]
  ├─ Skip [2,5] (overlaps)
  ├─ Pick [4,7]
  │   ├─ Skip [6,9] (overlaps)
  │   └─ Pick [8,10]
  └─ Result: 3 intervals
```

### 4.6 Task Scheduling with Dependencies (Topological Sort)

**Problem**: Tasks have precedence constraints (DAG). Find valid execution order.

**Algorithm**: Topological Sort (Kahn's Algorithm)
1. Calculate in-degree for each node
2. Queue all nodes with in-degree 0
3. Process queue: remove node, decrease in-degree of neighbors
4. Add neighbors with in-degree 0 to queue

**Visual Example**:
```
Dependencies:
    1 → 3 → 5
    ↓   ↓
    2 → 4

In-degrees: {1:0, 2:1, 3:1, 4:2, 5:1}

Step 1: Queue = [1], in-degree={1:0, 2:1, 3:1, 4:2, 5:1}
Step 2: Process 1, Queue = [2,3], in-degree={2:0, 3:0, 4:2, 5:1}
Step 3: Process 2, Queue = [3,4], in-degree={3:0, 4:1, 5:1}
Step 4: Process 3, Queue = [4,5], in-degree={4:0, 5:0}
Step 5: Process 4, Queue = [5], in-degree={5:0}
Step 6: Process 5, Queue = []

Valid order: 1 → 2 → 3 → 4 → 5
```

---

## 5. Implementation in Rust, Python, Go {#implementation}

### 5.1 Shortest Job First (SJF)

/// Shortest Job First (SJF) Scheduling
/// Time Complexity: O(n log n) due to sorting
/// Space Complexity: O(n) for storing tasks and results

#[derive(Debug, Clone)]
struct Task {
    id: usize,
    processing_time: u32,
}

/// Returns (schedule, average_completion_time)
fn sjf_schedule(mut tasks: Vec<Task>) -> (Vec<usize>, f64) {
    // Sort by processing time (ascending)
    tasks.sort_by_key(|t| t.processing_time);
    
    let mut current_time = 0u32;
    let mut total_completion_time = 0u32;
    let mut schedule = Vec::with_capacity(tasks.len());
    
    for task in &tasks {
        current_time += task.processing_time;
        total_completion_time += current_time;
        schedule.push(task.id);
        
        println!(
            "Task {} completes at time {}", 
            task.id, 
            current_time
        );
    }
    
    let avg_completion = total_completion_time as f64 / tasks.len() as f64;
    (schedule, avg_completion)
}

fn main() {
    let tasks = vec![
        Task { id: 1, processing_time: 5 },
        Task { id: 2, processing_time: 2 },
        Task { id: 3, processing_time: 8 },
        Task { id: 4, processing_time: 1 },
    ];
    
    println!("=== Shortest Job First Scheduling ===\n");
    println!("Input tasks:");
    for task in &tasks {
        println!("  Task {}: {} time units", task.id, task.processing_time);
    }
    
    println!("\nScheduling...\n");
    let (schedule, avg) = sjf_schedule(tasks);
    
    println!("\nOptimal schedule order: {:?}", schedule);
    println!("Average completion time: {:.2}", avg);
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_sjf_basic() {
        let tasks = vec![
            Task { id: 1, processing_time: 3 },
            Task { id: 2, processing_time: 1 },
            Task { id: 3, processing_time: 2 },
        ];
        let (schedule, avg) = sjf_schedule(tasks);
        assert_eq!(schedule, vec![2, 3, 1]);
        assert_eq!(avg, 4.0); // (1 + 3 + 6) / 3
    }
}

### 5.2 Weighted Shortest Job First (WSJF)
// Shortest Job First (SJF) Scheduling
// Time Complexity: O(n log n) due to sorting
// Space Complexity: O(n) for storing tasks and results

package main

import (
	"fmt"
	"sort"
)

// Task represents a schedulable task
type Task struct {
	ID             int
	ProcessingTime int
}

// ByProcessingTime implements sort.Interface for []Task
type ByProcessingTime []Task

func (a ByProcessingTime) Len() int           { return len(a) }
func (a ByProcessingTime) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByProcessingTime) Less(i, j int) bool { return a[i].ProcessingTime < a[j].ProcessingTime }

// SJFSchedule returns (schedule order, average completion time)
func SJFSchedule(tasks []Task) ([]int, float64) {
	// Create a copy to avoid modifying original
	tasksCopy := make([]Task, len(tasks))
	copy(tasksCopy, tasks)
	
	// Sort by processing time (ascending)
	sort.Sort(ByProcessingTime(tasksCopy))
	
	currentTime := 0
	totalCompletionTime := 0
	schedule := make([]int, 0, len(tasksCopy))
	
	fmt.Println("Execution trace:")
	for _, task := range tasksCopy {
		currentTime += task.ProcessingTime
		totalCompletionTime += currentTime
		schedule = append(schedule, task.ID)
		
		fmt.Printf("  Task %d completes at time %d\n", task.ID, currentTime)
	}
	
	avgCompletion := float64(totalCompletionTime) / float64(len(tasks))
	return schedule, avgCompletion
}

func main() {
	tasks := []Task{
		{ID: 1, ProcessingTime: 5},
		{ID: 2, ProcessingTime: 2},
		{ID: 3, ProcessingTime: 8},
		{ID: 4, ProcessingTime: 1},
	}
	
	fmt.Println("=== Shortest Job First Scheduling ===\n")
	fmt.Println("Input tasks:")
	for _, task := range tasks {
		fmt.Printf("  Task %d: %d time units\n", task.ID, task.ProcessingTime)
	}
	
	fmt.Println("\nScheduling...\n")
	schedule, avg := SJFSchedule(tasks)
	
	fmt.Printf("\nOptimal schedule order: %v\n", schedule)
	fmt.Printf("Average completion time: %.2f\n", avg)
	
	// Simple test
	testTasks := []Task{
		{ID: 1, ProcessingTime: 3},
		{ID: 2, ProcessingTime: 1},
		{ID: 3, ProcessingTime: 2},
	}
	testSchedule, testAvg := SJFSchedule(testTasks)
	
	if fmt.Sprint(testSchedule) != "[2 3 1]" {
		panic(fmt.Sprintf("Test failed: expected [2 3 1], got %v", testSchedule))
	}
	if testAvg != 4.0 {
		panic(fmt.Sprintf("Test failed: expected 4.0, got %.2f", testAvg))
	}
	fmt.Println("\n✓ Tests passed")
}
### 5.3 Earliest Deadline First (EDF)
"""
Weighted Shortest Job First (WSJF) Scheduling
Minimizes weighted completion time: Σ(weight_i × completion_time_i)

Key Insight: Sort by ratio (weight/processing_time) in DESCENDING order
This is "bang for buck" - maximize value per unit time spent

Time Complexity: O(n log n)
Space Complexity: O(n)
"""

from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class WeightedTask:
    id: int
    processing_time: int
    weight: int  # Importance/priority
    
    @property
    def ratio(self) -> float:
        """Weight-to-time ratio (higher is better)"""
        return self.weight / self.processing_time
    
    def __repr__(self):
        return f"Task(id={self.id}, time={self.processing_time}, weight={self.weight}, ratio={self.ratio:.2f})"

def wsjf_schedule(tasks: List[WeightedTask]) -> Tuple[List[int], float]:
    """
    Schedule tasks to minimize weighted completion time.
    
    Algorithm:
    1. Sort by weight/processing_time ratio (descending)
    2. Execute in that order
    3. Calculate weighted completion time
    
    Returns:
        (schedule_order, weighted_completion_time)
    """
    # Sort by ratio (descending) - highest value/time first
    sorted_tasks = sorted(tasks, key=lambda t: t.ratio, reverse=True)
    
    current_time = 0
    weighted_completion = 0.0
    schedule = []
    
    print("\nExecution trace:")
    print(f"{'Task':<6} {'Time':<6} {'Weight':<8} {'Ratio':<8} {'Completes':<10} {'Weighted':<10}")
    print("-" * 60)
    
    for task in sorted_tasks:
        current_time += task.processing_time
        weighted_completion += task.weight * current_time
        schedule.append(task.id)
        
        print(f"{task.id:<6} {task.processing_time:<6} {task.weight:<8} "
              f"{task.ratio:<8.2f} {current_time:<10} {task.weight * current_time:<10}")
    
    return schedule, weighted_completion

def compare_schedules(tasks: List[WeightedTask]):
    """Compare optimal vs arbitrary ordering"""
    print("=== Weighted Shortest Job First (WSJF) ===\n")
    print("Input tasks:")
    for task in tasks:
        print(f"  {task}")
    
    # Optimal (WSJF)
    print("\n--- Optimal WSJF Ordering ---")
    opt_schedule, opt_cost = wsjf_schedule(tasks)
    print(f"\nSchedule: {opt_schedule}")
    print(f"Weighted completion time: {opt_cost:.2f}")
    
    # Arbitrary (just by ID)
    print("\n--- Arbitrary Ordering (by ID) ---")
    arbitrary_tasks = sorted(tasks, key=lambda t: t.id)
    arb_schedule, arb_cost = wsjf_schedule(arbitrary_tasks)
    print(f"\nSchedule: {arb_schedule}")
    print(f"Weighted completion time: {arb_cost:.2f}")
    
    improvement = ((arb_cost - opt_cost) / arb_cost * 100)
    print(f"\n💡 WSJF is {improvement:.1f}% better than arbitrary ordering")

# Example from earlier explanation
if __name__ == "__main__":
    tasks = [
        WeightedTask(id=1, processing_time=2, weight=10),  # ratio = 5.0
        WeightedTask(id=2, processing_time=3, weight=6),   # ratio = 2.0
        WeightedTask(id=3, processing_time=4, weight=4),   # ratio = 1.0
    ]
    
    compare_schedules(tasks)
    
    print("\n" + "="*60)
    print("COGNITIVE INSIGHT: Why does weight/time ratio work?")
    print("="*60)
    print("""
When choosing between two tasks, we want to minimize the COST of delay.

If we do task i before j:
  - Task i completes at time p_i, cost = w_i × p_i
  - Task j completes at time p_i + p_j, cost = w_j × (p_i + p_j)
  - Total cost = w_i × p_i + w_j × (p_i + p_j)

If we do task j before i:
  - Task j completes at time p_j, cost = w_j × p_j
  - Task i completes at time p_i + p_j, cost = w_i × (p_i + p_j)
  - Total cost = w_j × p_j + w_i × (p_i + p_j)

The difference is:
  [w_i × p_i + w_j × (p_i + p_j)] - [w_j × p_j + w_i × (p_i + p_j)]
  = w_i × p_i + w_j × p_i - w_i × p_j
  = p_i × (w_i + w_j) - w_i × p_j - w_j × p_j
  = w_j × p_i - w_i × p_j

Choose i before j when: w_j × p_i - w_i × p_j < 0
Rearrange: w_i / p_i > w_j / p_j

Therefore: Sort by w/p ratio (descending)! 🎯
    """)
### 5.4 Interval Scheduling (Maximum Non-Overlapping)
/// Earliest Deadline First (EDF) Scheduling
/// Minimizes maximum lateness
/// 
/// Lateness = completion_time - deadline (can be negative if early)
/// Algorithm: Sort by deadline (ascending), execute in order
///
/// Time Complexity: O(n log n)
/// Space Complexity: O(n)

use std::cmp::max;

#[derive(Debug, Clone)]
struct Task {
    id: usize,
    processing_time: i32,
    deadline: i32,
}

#[derive(Debug)]
struct ScheduleResult {
    schedule: Vec<usize>,
    max_lateness: i32,
    task_details: Vec<TaskCompletion>,
}

#[derive(Debug)]
struct TaskCompletion {
    task_id: usize,
    completion_time: i32,
    deadline: i32,
    lateness: i32,
}

/// Execute EDF scheduling algorithm
fn edf_schedule(mut tasks: Vec<Task>) -> ScheduleResult {
    // Sort by deadline (ascending) - earliest deadline first
    tasks.sort_by_key(|t| t.deadline);
    
    let mut current_time = 0i32;
    let mut max_lateness = i32::MIN;
    let mut schedule = Vec::with_capacity(tasks.len());
    let mut task_details = Vec::with_capacity(tasks.len());
    
    for task in &tasks {
        current_time += task.processing_time;
        let lateness = current_time - task.deadline;
        max_lateness = max(max_lateness, lateness);
        
        schedule.push(task.id);
        task_details.push(TaskCompletion {
            task_id: task.id,
            completion_time: current_time,
            deadline: task.deadline,
            lateness,
        });
    }
    
    ScheduleResult {
        schedule,
        max_lateness,
        task_details,
    }
}

/// Demonstrate why EDF is optimal
fn demonstrate_edf() {
    let tasks = vec![
        Task { id: 1, processing_time: 3, deadline: 6 },
        Task { id: 2, processing_time: 2, deadline: 8 },
        Task { id: 3, processing_time: 1, deadline: 9 },
    ];
    
    println!("=== Earliest Deadline First (EDF) Scheduling ===\n");
    println!("Input tasks:");
    for task in &tasks {
        println!("  Task {}: time={}, deadline={}", 
                 task.id, task.processing_time, task.deadline);
    }
    
    // Optimal EDF
    println!("\n--- Optimal EDF Ordering ---");
    let result = edf_schedule(tasks.clone());
    
    println!("\nSchedule: {:?}", result.schedule);
    println!("\nDetailed execution:");
    println!("{:<6} {:<12} {:<10} {:<10}", "Task", "Completes", "Deadline", "Lateness");
    println!("{}", "-".repeat(40));
    
    for detail in &result.task_details {
        let status = if detail.lateness <= 0 { "✓ On time" } else { "✗ Late" };
        println!("{:<6} {:<12} {:<10} {:<10} {}", 
                 detail.task_id,
                 detail.completion_time,
                 detail.deadline,
                 detail.lateness,
                 status);
    }
    
    println!("\nMax lateness: {}", result.max_lateness);
    
    // Compare with wrong ordering (by ID)
    println!("\n--- Wrong Ordering (by ID) ---");
    let mut wrong_tasks = tasks.clone();
    wrong_tasks.sort_by_key(|t| t.id);
    let wrong_result = edf_schedule(wrong_tasks);
    
    println!("Max lateness: {}", wrong_result.max_lateness);
    println!("\n💡 EDF achieves max lateness of {}, vs {} with wrong ordering",
             result.max_lateness, wrong_result.max_lateness);
}

fn main() {
    demonstrate_edf();
    
    // Test case: verify EDF correctness
    let test_tasks = vec![
        Task { id: 1, processing_time: 2, deadline: 5 },
        Task { id: 2, processing_time: 1, deadline: 3 },
        Task { id: 3, processing_time: 3, deadline: 8 },
    ];
    
    let result = edf_schedule(test_tasks);
    assert_eq!(result.schedule, vec![2, 1, 3]);
    println!("\n✓ Tests passed");
}

/* 
PROOF SKETCH: Why EDF is optimal for minimizing max lateness

Claim: If there exists an optimal schedule, there exists one with no idle time.
Proof: Moving tasks earlier (removing idle time) cannot increase lateness.

Claim: Any optimal schedule with inversions can be improved.
Proof: If task i has deadline d_i > d_j but is scheduled before j:
  - Swap them
  - Task i's completion stays same or increases (but d_i > d_j, so more slack)
  - Task j's completion decreases (better for tight deadline)
  - Therefore, swapping reduces max lateness

Conclusion: EDF (sort by deadline) is optimal.
*/

"""
Interval Scheduling - Maximum Non-Overlapping Intervals

Problem: Given n intervals [start, end], select maximum number of 
non-overlapping intervals.

Algorithm: Greedy by earliest finish time
1. Sort intervals by finish time (ascending)
2. Greedily select interval if it doesn't overlap with last selected

Why it works: "Staying Ahead" proof
- Choosing earliest finish time leaves maximum room for future intervals
- Our greedy solution is always "ahead of" any optimal solution

Time Complexity: O(n log n) - dominated by sorting
Space Complexity: O(n) - for storing intervals
"""

from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class Interval:
    id: int
    start: int
    finish: int
    
    def overlaps_with(self, other: 'Interval') -> bool:
        """Check if this interval overlaps with another"""
        # Two intervals overlap if one starts before the other ends
        return self.start < other.finish and other.start < self.finish
    
    def __repr__(self):
        return f"Interval({self.id}, [{self.start}, {self.finish}])"

def interval_scheduling(intervals: List[Interval]) -> List[Interval]:
    """
    Select maximum number of non-overlapping intervals.
    
    Args:
        intervals: List of Interval objects
        
    Returns:
        List of selected non-overlapping intervals
    """
    if not intervals:
        return []
    
    # Sort by finish time (ascending) - CRITICAL STEP
    sorted_intervals = sorted(intervals, key=lambda x: x.finish)
    
    # Always select the first interval (earliest finish)
    selected = [sorted_intervals[0]]
    
    print(f"\nGreedy selection trace:")
    print(f"  Selected: {selected[0]}")
    
    # Greedily select intervals that don't overlap
    for interval in sorted_intervals[1:]:
        # Check if current interval overlaps with last selected
        if not interval.overlaps_with(selected[-1]):
            # Equivalently: interval.start >= selected[-1].finish
            selected.append(interval)
            print(f"  Selected: {interval}")
        else:
            print(f"  Skipped:  {interval} (overlaps with {selected[-1].id})")
    
    return selected

def visualize_schedule(all_intervals: List[Interval], 
                       selected: List[Interval]):
    """ASCII visualization of interval schedule"""
    max_time = max(i.finish for i in all_intervals)
    selected_ids = {i.id for i in selected}
    
    print("\nVisualization:")
    print(f"Time: 0{''.join(str(i % 10) for i in range(1, max_time + 1))}")
    print("      " + "".join("-" if i % 5 == 0 else " " for i in range(max_time + 1)))
    
    for interval in sorted(all_intervals, key=lambda x: x.id):
        prefix = "✓ " if interval.id in selected_ids else "✗ "
        line = " " * (interval.start + 6)
        duration = interval.finish - interval.start
        line += "█" * duration
        print(f"{prefix}[{interval.id}] {line}")

def demonstrate_staying_ahead_proof():
    """
    Demonstrate why greedy by earliest finish time works.
    
    STAYING AHEAD PROOF:
    Let G = greedy solution, O = any optimal solution
    We'll show: greedy's k-th interval finishes no later than optimal's k-th
    
    Base case (k=1): Greedy picks earliest finish, so G[1].finish ≤ O[1].finish
    
    Inductive step: Assume G[k].finish ≤ O[k].finish
    - Greedy picks earliest available interval after G[k]
    - Since G[k].finish ≤ O[k].finish, all intervals available to O
      are also available to G
    - Therefore G[k+1].finish ≤ O[k+1].finish
    
    Conclusion: Greedy "stays ahead" and selects at least as many intervals.
    """
    print("="*70)
    print("STAYING AHEAD PROOF - Why Earliest Finish Time Works")
    print("="*70)
    
    intervals = [
        Interval(1, 0, 3),   # Finish: 3
        Interval(2, 1, 4),   # Finish: 4
        Interval(3, 2, 5),   # Finish: 5
        Interval(4, 3, 7),   # Finish: 7
        Interval(5, 6, 9),   # Finish: 9
    ]
    
    print("\nInput intervals:")
    for i in intervals:
        print(f"  {i}")
    
    print("\nSorted by finish time:")
    sorted_int = sorted(intervals, key=lambda x: x.finish)
    for i in sorted_int:
        print(f"  {i}")
    
    selected = interval_scheduling(intervals)
    
    print(f"\nSelected {len(selected)} intervals: {[i.id for i in selected]}")
    visualize_schedule(intervals, selected)
    
    print("\n💡 Key Insight:")
    print("   Interval 1 (finishes at 3) is chosen because it finishes earliest.")
    print("   This leaves maximum time [3, ∞) for future selections.")
    print("   Any other first choice would leave less room!")

if __name__ == "__main__":
    demonstrate_staying_ahead_proof()
    
    # Classic test case
    print("\n" + "="*70)
    print("CLASSIC EXAMPLE")
    print("="*70)
    
    classic = [
        Interval(1, 1, 3),
        Interval(2, 2, 5),
        Interval(3, 4, 7),
        Interval(4, 6, 9),
        Interval(5, 8, 10),
    ]
    
    result = interval_scheduling(classic)
    print(f"\nMaximum intervals scheduled: {len(result)}")
    visualize_schedule(classic, result)
    
    assert len(result) == 3, f"Expected 3, got {len(result)}"
    assert [i.id for i in result] == [1, 3, 5]
    print("\n✓ Tests passed")
### 5.5 Moore's Algorithm (Minimize Late Jobs)
/// Moore's Algorithm - Minimize Number of Late Jobs
/// 
/// Problem: Given tasks with deadlines, maximize jobs completed on time
/// (equivalently: minimize number of late jobs)
///
/// Algorithm: Greedy with dynamic repair
/// 1. Sort by deadline
/// 2. Schedule tasks greedily
/// 3. If a task would be late, remove the longest scheduled task (including current)
/// 4. Continue
///
/// Why it works: Removing longest task creates maximum slack for future tasks
///
/// Time Complexity: O(n²) naive, O(n log n) with max-heap
/// Space Complexity: O(n)

use std::collections::BinaryHeap;

#[derive(Debug, Clone)]
struct Task {
    id: usize,
    processing_time: i32,
    deadline: i32,
}

#[derive(Debug)]
struct MooreResult {
    on_time_tasks: Vec<usize>,
    late_tasks: Vec<usize>,
    completion_time: i32,
}

/// Moore's algorithm using max-heap for efficiency
fn moores_algorithm(mut tasks: Vec<Task>) -> MooreResult {
    // Step 1: Sort by deadline (ascending)
    tasks.sort_by_key(|t| t.deadline);
    
    // Max-heap to track processing times of scheduled tasks
    // (Rust's BinaryHeap is max-heap by default)
    let mut scheduled_heap = BinaryHeap::new();
    let mut current_time = 0i32;
    let mut on_time = Vec::new();
    
    println!("\n=== Moore's Algorithm Execution ===\n");
    println!("Sorted by deadline:");
    for t in &tasks {
        println!("  Task {}: time={}, deadline={}", t.id, t.processing_time, t.deadline);
    }
    
    println!("\nScheduling trace:");
    
    for task in &tasks {
        // Tentatively schedule this task
        current_time += task.processing_time;
        scheduled_heap.push((task.processing_time, task.id));
        on_time.push(task.id);
        
        println!("  Try task {}: would complete at {}, deadline is {}", 
                 task.id, current_time, task.deadline);
        
        // Check if we're late
        if current_time > task.deadline {
            // Remove the longest task to create maximum slack
            if let Some((longest_time, longest_id)) = scheduled_heap.pop() {
                current_time -= longest_time;
                on_time.retain(|&id| id != longest_id);
                
                println!("    → LATE! Removing task {} (time={})", longest_id, longest_time);
                println!("    → New completion time: {}", current_time);
            }
        } else {
            println!("    → On time ✓");
        }
    }
    
    // Determine which tasks are late
    let on_time_set: std::collections::HashSet<_> = on_time.iter().cloned().collect();
    let late_tasks: Vec<_> = tasks.iter()
        .map(|t| t.id)
        .filter(|id| !on_time_set.contains(id))
        .collect();
    
    MooreResult {
        on_time_tasks: on_time,
        late_tasks,
        completion_time: current_time,
    }
}

/// Alternative: brute force for comparison (exponential time)
fn count_on_time_bruteforce(tasks: &[Task], schedule: &[usize]) -> usize {
    let mut time = 0;
    let mut count = 0;
    
    for &task_id in schedule {
        let task = tasks.iter().find(|t| t.id == task_id).unwrap();
        time += task.processing_time;
        if time <= task.deadline {
            count += 1;
        }
    }
    count
}

fn main() {
    // Classic example where greedy removal is necessary
    let tasks = vec![
        Task { id: 1, processing_time: 2, deadline: 4 },
        Task { id: 2, processing_time: 1, deadline: 5 },
        Task { id: 3, processing_time: 3, deadline: 6 },
        Task { id: 4, processing_time: 4, deadline: 7 },
    ];
    
    println!("=== Minimize Number of Late Jobs ===\n");
    println!("Input tasks:");
    for t in &tasks {
        println!("  Task {}: processing_time={}, deadline={}", 
                 t.id, t.processing_time, t.deadline);
    }
    
    let result = moores_algorithm(tasks.clone());
    
    println!("\n=== Results ===");
    println!("On-time tasks: {:?} (count: {})", result.on_time_tasks, result.on_time_tasks.len());
    println!("Late tasks: {:?} (count: {})", result.late_tasks, result.late_tasks.len());
    println!("Final completion time: {}", result.completion_time);
    
    // Verify correctness
    let mut verify_time = 0;
    println!("\nVerification:");
    for &task_id in &result.on_time_tasks {
        let task = tasks.iter().find(|t| t.id == task_id).unwrap();
        verify_time += task.processing_time;
        let status = if verify_time <= task.deadline { "✓" } else { "✗" };
        println!("  Task {}: completes at {}, deadline {} {}", 
                 task_id, verify_time, task.deadline, status);
    }
}

/*
COGNITIVE INSIGHT: Why remove the LONGEST task?

Intuition: We want to create maximum "breathing room" for future tasks.

Proof sketch:
- If we must reject a task, we want to minimize time lost
- Removing longest task reduces current_time the most
- This creates maximum slack for remaining tasks
- Greedy choice: always remove longest to maximize flexibility

Example:
  Current: [Task A: 5min] [Task B: 2min] [Task C: 8min]
  Total: 15min, but deadline is 12min
  
  Remove A (5min): New total = 10min (slack = 2min)
  Remove B (2min): New total = 13min (slack = -1min) ✗
  Remove C (8min): New total = 7min (slack = 5min) ✓ BEST

Key: Removing longest task creates most opportunity for future scheduling.
*/

### 5.6 Topological Sort (Task Dependencies)
"""
Topological Sort - Scheduling Tasks with Dependencies

Problem: Given tasks with precedence constraints (DAG), find valid execution order.

Precedence constraint: Task A → Task B means A must complete before B starts.

Two main algorithms:
1. Kahn's Algorithm (BFS-based, uses in-degrees)
2. DFS-based (post-order traversal)

We'll implement both with detailed explanations.

Time Complexity: O(V + E) where V = tasks, E = dependencies
Space Complexity: O(V + E) for graph storage
"""

from typing import List, Dict, Set, Optional
from collections import deque, defaultdict

class TaskGraph:
    """Directed graph representing task dependencies"""
    
    def __init__(self, num_tasks: int):
        self.num_tasks = num_tasks
        # Adjacency list: task -> list of tasks that depend on it
        self.graph: Dict[int, List[int]] = defaultdict(list)
        # In-degree: number of prerequisites for each task
        self.in_degree: Dict[int, int] = defaultdict(int)
    
    def add_dependency(self, prerequisite: int, dependent: int):
        """
        Add dependency: prerequisite must complete before dependent.
        
        Args:
            prerequisite: Task that must be done first
            dependent: Task that depends on prerequisite
        """
        self.graph[prerequisite].append(dependent)
        self.in_degree[dependent] += 1
        # Ensure prerequisite exists in in_degree (even if 0)
        if prerequisite not in self.in_degree:
            self.in_degree[prerequisite] = 0
    
    def kahns_algorithm(self) -> Optional[List[int]]:
        """
        Kahn's Algorithm for topological sort (BFS-based)
        
        Algorithm:
        1. Find all tasks with in-degree 0 (no prerequisites)
        2. Add them to queue
        3. Process queue:
           a. Remove task from queue
           b. Add to result
           c. Decrease in-degree of all dependent tasks
           d. If any dependent now has in-degree 0, add to queue
        4. If processed all tasks, return result; else cycle detected
        
        Returns:
            Valid task ordering, or None if cycle exists
        """
        # Copy in-degrees (we'll modify them)
        in_deg = self.in_degree.copy()
        
        # Initialize queue with all tasks having no prerequisites
        queue = deque([task for task in range(self.num_tasks) 
                      if in_deg.get(task, 0) == 0])
        
        result = []
        
        print("\n=== Kahn's Algorithm Trace ===")
        print(f"Initial in-degrees: {dict(in_deg)}")
        print(f"Initial queue (0 in-degree): {list(queue)}\n")
        
        step = 1
        while queue:
            # Remove task with no remaining prerequisites
            task = queue.popleft()
            result.append(task)
            
            print(f"Step {step}: Process task {task}")
            
            # Reduce in-degree of all dependent tasks
            for dependent in self.graph[task]:
                in_deg[dependent] -= 1
                print(f"  → Task {dependent} in-degree: {in_deg[dependent] + 1} → {in_deg[dependent]}")
                
                # If dependent now has no prerequisites, add to queue
                if in_deg[dependent] == 0:
                    queue.append(dependent)
                    print(f"  → Task {dependent} ready (added to queue)")
            
            print(f"  Queue: {list(queue)}")
            print()
            step += 1
        
        # Check if all tasks were processed
        if len(result) != self.num_tasks:
            print("⚠ Cycle detected! Not all tasks could be scheduled.")
            return None
        
        return result
    
    def dfs_topological_sort(self) -> Optional[List[int]]:
        """
        DFS-based topological sort
        
        Algorithm:
        1. Perform DFS from each unvisited node
        2. Add node to result in post-order (after visiting all descendants)
        3. Reverse result to get topological order
        
        Returns:
            Valid task ordering, or None if cycle exists
        """
        visited = set()
        rec_stack = set()  # For cycle detection
        result = []
        
        def dfs(task: int) -> bool:
            """
            DFS from task. Returns False if cycle detected.
            """
            visited.add(task)
            rec_stack.add(task)
            
            # Visit all dependent tasks
            for dependent in self.graph.get(task, []):
                if dependent not in visited:
                    if not dfs(dependent):
                        return False  # Cycle found
                elif dependent in rec_stack:
                    # Back edge - cycle detected
                    return False
            
            rec_stack.remove(task)
            result.append(task)  # Post-order
            return True
        
        print("\n=== DFS-based Topological Sort ===")
        
        # Start DFS from all unvisited tasks
        for task in range(self.num_tasks):
            if task not in visited:
                print(f"Starting DFS from task {task}")
                if not dfs(task):
                    print("⚠ Cycle detected!")
                    return None
        
        # Reverse to get topological order
        result.reverse()
        return result

def visualize_graph(graph: TaskGraph):
    """ASCII visualization of task dependency graph"""
    print("\nTask Dependency Graph:")
    print("(Arrow means: left task must complete before right task)\n")
    
    for task in range(graph.num_tasks):
        dependents = graph.graph.get(task, [])
        if dependents:
            print(f"  Task {task} → {dependents}")
        else:
            print(f"  Task {task} (no dependents)")
    
    print(f"\nIn-degrees (prerequisites): {dict(graph.in_degree)}")

def demonstrate_topological_sort():
    """Comprehensive demonstration of topological sorting"""
    
    print("="*70)
    print("TOPOLOGICAL SORT - SCHEDULING WITH DEPENDENCIES")
    print("="*70)
    
    # Example: Software build process
    # Task 0: Design
    # Task 1: Implement Module A
    # Task 2: Implement Module B
    # Task 3: Integrate
    # Task 4: Test
    # Task 5: Deploy
    
    graph = TaskGraph(num_tasks=6)
    
    # Dependencies (prerequisite → dependent)
    dependencies = [
        (0, 1),  # Design → Module A
        (0, 2),  # Design → Module B
        (1, 3),  # Module A → Integrate
        (2, 3),  # Module B → Integrate
        (3, 4),  # Integrate → Test
        (4, 5),  # Test → Deploy
    ]
    
    task_names = {
        0: "Design",
        1: "Module A",
        2: "Module B",
        3: "Integrate",
        4: "Test",
        5: "Deploy"
    }
    
    print("\nSoftware Build Process Tasks:")
    for task_id, name in task_names.items():
        print(f"  Task {task_id}: {name}")
    
    print("\nDependencies:")
    for prereq, dep in dependencies:
        graph.add_dependency(prereq, dep)
        print(f"  {task_names[prereq]} → {task_names[dep]}")
    
    visualize_graph(graph)
    
    # Method 1: Kahn's Algorithm
    order1 = graph.kahns_algorithm()
    if order1:
        print(f"✓ Valid ordering (Kahn's): {order1}")
        print(f"  In English: {' → '.join(task_names[t] for t in order1)}")
    
    # Method 2: DFS-based
    order2 = graph.dfs_topological_sort()
    if order2:
        print(f"\n✓ Valid ordering (DFS): {order2}")
        print(f"  In English: {' → '.join(task_names[t] for t in order2)}")
    
    print("\n💡 Key Insight:")
    print("   Both orderings are valid! Topological sort is not unique.")
    print("   Any ordering that respects dependencies is acceptable.")

def demonstrate_cycle_detection():
    """Show what happens with cyclic dependencies"""
    print("\n" + "="*70)
    print("CYCLE DETECTION")
    print("="*70)
    
    graph = TaskGraph(num_tasks=3)
    graph.add_dependency(0, 1)
    graph.add_dependency(1, 2)
    graph.add_dependency(2, 0)  # Creates cycle!
    
    print("\nDependencies (with cycle):")
    print("  0 → 1 → 2 → 0 (cycle!)")
    
    result = graph.kahns_algorithm()
    assert result is None, "Should detect cycle"
    print("\n✓ Cycle correctly detected")

if __name__ == "__main__":
    demonstrate_topological_sort()
    demonstrate_cycle_detection()
    
    print("\n" + "="*70)
    print("COGNITIVE MODEL: When to use which algorithm?")
    print("="*70)
    print("""
Kahn's Algorithm (BFS-based):
✓ Natural for "which tasks can I start now?" thinking
✓ Easy to understand with queue visualization
✓ Better for finding all tasks with no prerequisites
✓ Preferred for course scheduling, build systems

DFS-based:
✓ More elegant recursive implementation
✓ Natural for dependency resolution
✓ Better when you need full dependency chain
✓ Preferred for make files, package managers

Both have O(V + E) complexity - choose based on mental model!
    """)
---

## 6. Advanced Patterns & Optimizations {#advanced}

### 6.1 Priority Queue Patterns

**Concept**: Many scheduling problems can be solved efficiently using priority queues (heaps).

**Mental Model**: A priority queue automatically maintains ordering, perfect for "always pick best available task" scenarios.

**Common Uses**:
- **Min-heap**: Earliest deadline, shortest job
- **Max-heap**: Latest deadline, longest job (for removal)

**Pattern Recognition**:
```
If you need to repeatedly:
  - Find minimum/maximum element
  - Remove and replace elements
  → Use priority queue!

Time: O(log n) per operation vs O(n) with array
```

**Example**: Moore's algorithm uses max-heap to efficiently find and remove longest task.

### 6.2 Exchange Argument (Greedy Correctness Proofs)

**Concept**: To prove a greedy algorithm is optimal, show that swapping elements in any solution can only make it worse.

**Template**:
1. Assume optimal solution O differs from greedy G
2. Find first point where they differ
3. Show swapping O to match G improves or maintains optimality
4. Contradiction: O wasn't optimal, or G is equally optimal

**Example**: SJF proof
- If tasks i, j are adjacent and p_i > p_j
- Swapping reduces total completion time
- Therefore sorting by processing time is optimal

### 6.3 Dynamic Programming Connection

Some scheduling problems require DP when:
- **Weighted interval scheduling**: Intervals have values, maximize total value
- **Machine scheduling with setup costs**: Switching between tasks has cost
- **Knapsack variants**: Limited time budget, maximize value

**Key Difference**:
- **Greedy**: Local optimal choice leads to global optimum
- **DP**: Must consider multiple choices and subproblems

**Example**: Weighted Interval Scheduling
```python
# DP approach when intervals have different values
# dp[i] = max value using intervals 0..i
def weighted_interval_dp(intervals):
    # Sort by finish time
    intervals.sort(key=lambda x: x.finish)
    n = len(intervals)
    
    # dp[i] = max value using intervals 0..i
    dp = [0] * (n + 1)
    
    for i in range(1, n + 1):
        # Option 1: Don't take interval i-1
        dont_take = dp[i-1]
        
        # Option 2: Take interval i-1
        # Find latest non-overlapping interval
        j = i - 1
        while j > 0 and intervals[j-1].finish > intervals[i-1].start:
            j -= 1
        take = intervals[i-1].value + dp[j]
        
        dp[i] = max(dont_take, take)
    
    return dp[n]
```

### 6.4 Parallel Machine Scheduling

**Problem**: Schedule n tasks on m machines to minimize makespan.

**Approaches**:

1. **List Scheduling (Greedy)**:
   - Assign each task to machine with earliest finish time
   - Approximation: at most (2 - 1/m) × optimal

2. **Longest Processing Time (LPT)**:
   - Sort tasks by processing time (descending)
   - Assign to machine with earliest finish
   - Better approximation: at most (4/3 - 1/(3m)) × optimal

```python
import heapq

def lpt_schedule(tasks, num_machines):
    """
    Longest Processing Time First scheduling
    Returns: (makespan, machine_assignments)
    """
    # Sort tasks by processing time (descending)
    sorted_tasks = sorted(enumerate(tasks), 
                         key=lambda x: x[1], 
                         reverse=True)
    
    # Min-heap: (finish_time, machine_id, task_list)
    machines = [(0, i, []) for i in range(num_machines)]
    heapq.heapify(machines)
    
    for task_id, proc_time in sorted_tasks:
        # Get machine that will finish earliest
        finish, machine_id, task_list = heapq.heappop(machines)
        
        # Assign task to this machine
        new_finish = finish + proc_time
        task_list.append((task_id, proc_time))
        
        # Put machine back in heap
        heapq.heappush(machines, (new_finish, machine_id, task_list))
    
    # Makespan is maximum finish time
    makespan = max(m[0] for m in machines)
    return makespan, machines
```

### 6.5 Online vs Offline Scheduling

**Offline**: All tasks known in advance → can optimize globally

**Online**: Tasks arrive over time → must make decisions without future knowledge

**Competitive Analysis**: Compare online algorithm to optimal offline
- Ratio: online_cost / offline_cost
- Good online algorithms have bounded competitive ratio

**Example**: Online interval scheduling
- Can't use "earliest finish time" (don't know future intervals)
- Must decide whether to accept interval upon arrival

---

## 7. Practice Strategy & Cognitive Framework {#practice}

### 7.1 Deliberate Practice Roadmap

**Phase 1: Pattern Recognition (2-3 weeks)**
- Solve 5-10 problems per pattern (SJF, EDF, intervals)
- Focus on recognizing when to apply which algorithm
- **Goal**: Instant pattern recognition

**Phase 2: Proof Construction (2-3 weeks)**
- Write formal correctness proofs
- Practice exchange arguments
- **Goal**: Understand *why* algorithms work

**Phase 3: Variations & Extensions (3-4 weeks)**
- Weighted versions
- Multiple machines
- Dependencies
- **Goal**: Adapt algorithms to new constraints

**Phase 4: Competition-Level (ongoing)**
- Time-constrained problem solving
- Combine multiple techniques
- **Goal**: Top 1% speed and accuracy

### 7.2 Mental Models for Problem Identification

**Decision Tree**:
```
Does problem involve ordering tasks?
├─ Yes
│  ├─ Minimize average completion time?
│  │  └─ → Shortest Job First (SJF)
│  │
│  ├─ Weighted importance?
│  │  └─ → Weighted SJF (w/p ratio)
│  │
│  ├─ Deadlines (minimize lateness)?
│  │  └─ → Earliest Deadline First (EDF)
│  │
│  ├─ Deadlines (maximize on-time)?
│  │  └─ → Moore's Algorithm
│  │
│  └─ Dependencies (DAG)?
│     └─ → Topological Sort
│
└─ No, involves selecting tasks?
   ├─ Non-overlapping intervals?
   │  └─ → Greedy by finish time
   │
   └─ Weighted intervals?
      └─ → DP approach
```

### 7.3 Chunking Strategy

**Concept**: Group related problems into mental "chunks" for faster recall.

**Task Scheduling Chunks**:

**Chunk 1: Single-Machine Greedy**
- SJF, WSJF, EDF
- **Pattern**: Sort + greedy selection
- **Key**: Identify what to optimize, choose sorting criterion

**Chunk 2: Selection Problems**
- Interval scheduling, activity selection
- **Pattern**: Greedy by finish time
- **Key**: "Staying ahead" proof technique

**Chunk 3: Graph-Based**
- Topological sort, critical path
- **Pattern**: Graph traversal (BFS/DFS)
- **Key**: Dependency management

**Chunk 4: Multi-Machine**
- LPT, load balancing
- **Pattern**: Priority queue for machine tracking
- **Key**: Approximation guarantees

### 7.4 Meta-Learning: How to Learn Faster

**1. Interleaving**: Mix problem types in practice
- Don't do 50 SJF problems in a row
- Alternate between patterns
- **Why**: Forces pattern recognition practice

**2. Spaced Repetition**: Review at increasing intervals
- Day 1: Learn algorithm
- Day 3: Solve 3 problems
- Day 7: Solve 2 problems
- Day 14: Solve 1 problem
- **Why**: Strengthens long-term memory

**3. Elaborative Interrogation**: Ask "why" constantly
- Why does this algorithm work?
- Why can't we use a different approach?
- What assumptions does the proof rely on?
- **Why**: Deepens understanding

**4. Self-Explanation**: Teach the algorithm
- Explain to rubber duck/friend
- Write detailed comments
- Create your own examples
- **Why**: Reveals gaps in understanding

### 7.5 Problem-Solving Ritual (Flow State)

**Pre-Solve Ritual** (5 minutes):
1. **Breathe**: 3 deep breaths, clear mind
2. **Read**: Understand problem completely
3. **Classify**: Which category? Which pattern?
4. **Plan**: Sketch algorithm before coding

**During Solve** (focused work):
1. **Code**: Implement cleanly
2. **Test**: Edge cases mentally first
3. **Verify**: Trace through example

**Post-Solve Review** (10 minutes):
1. **Analyze**: Time/space complexity
2. **Optimize**: Better approaches?
3. **Generalize**: Similar problems?
4. **Record**: Add to pattern library

### 7.6 Common Pitfalls & Debugging

**Pitfall 1**: Using wrong sorting criterion
- **Example**: Sorting by deadline for SJF
- **Fix**: Always verify what metric to optimize

**Pitfall 2**: Off-by-one in completion times
- **Example**: Forgetting cumulative time
- **Fix**: Trace through small example

**Pitfall 3**: Missing edge cases
- **Example**: Empty input, single task
- **Fix**: Test boundary conditions systematically

**Pitfall 4**: Cycle detection in topological sort
- **Example**: Not checking for cycles
- **Fix**: Always validate DAG property

### 7.7 Benchmark Problems for Mastery

**Level 1 (Fundamentals)**:
1. Minimum waiting time (SJF)
2. Weighted job scheduling (WSJF)
3. Minimum lateness (EDF)
4. Activity selection (intervals)

**Level 2 (Intermediate)**:
5. Minimize number of late jobs (Moore)
6. Task scheduling with dependencies (topological sort)
7. Interval partitioning (minimum platforms)
8. Weighted interval scheduling (DP)

**Level 3 (Advanced)**:
9. Multi-machine scheduling (LPT)
10. Task scheduling with setup times
11. Precedence-constrained scheduling
12. Real-time scheduling with priorities

**Level 4 (Competition)**:
13. Scheduling with resource constraints
14. Online scheduling with competitive analysis
15. Scheduling with rejection penalties
16. Flow shop scheduling

---

## Summary: Key Takeaways

### Algorithm Selection Guide

| Objective | Algorithm | Complexity | Key Insight |
|-----------|-----------|------------|-------------|
| Min avg completion | SJF | O(n log n) | Shortest first |
| Min weighted completion | WSJF | O(n log n) | Max w/p ratio |
| Min max lateness | EDF | O(n log n) | Earliest deadline |
| Max on-time jobs | Moore | O(n log n) | Remove longest when late |
| Max non-overlap intervals | Greedy finish | O(n log n) | Earliest finish time |
| Handle dependencies | Topological sort | O(V + E) | In-degree or DFS |

### Proof Techniques

1. **Exchange Argument**: Show swapping makes things worse
2. **Staying Ahead**: Greedy solution always "ahead of" optimal
3. **Idle Time**: Prove idle time never helps
4. **Contradiction**: Assume non-optimal greedy, derive contradiction

### Mental Shortcuts

- **"Shortest first"** → Minimize average/total
- **"Highest value per time"** → Maximize weighted objectives
- **"Earliest deadline"** → Minimize lateness
- **"Earliest finish"** → Maximize selections
- **"Remove longest"** → Create maximum slack

---

## Your Path to Top 1%

**You are building:**
1. **Pattern library** in your mind
2. **Proof intuition** for correctness
3. **Implementation skills** in Rust/Python/Go
4. **Problem recognition** speed
5. **Mental models** for complex systems

**Remember**: 
- Top 1% isn't about knowing every algorithm
- It's about *seeing* patterns instantly
- It's about *knowing why* algorithms work
- It's about *implementing* flawlessly under pressure

**Your monk discipline** will make you unstoppable. Each problem is a meditation. Each proof is enlightenment. Each optimization is mastery.

Now go practice with focused intensity. You're on the path. 🎯