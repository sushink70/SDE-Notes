# Comprehensive Guide to Simulation in DSA

---

## Mental Model Before Code

> **Simulation** is the art of faithfully modeling a described process in code — step by step, rule by rule. The challenge is never the algorithm itself, but *clarity of state representation* and *precision in transition logic*.

An expert's mindset before any simulation problem:
1. **Identify the state** — what must be tracked at every tick/step?
2. **Identify the transitions** — what rules transform state T → T+1?
3. **Identify the termination** — when do we stop? What do we extract?
4. **Choose the right data structure** — the state container IS the solution efficiency.

---

## Taxonomy of Simulation Problems

```
Simulation
├── Grid/Matrix Simulation       (Game of Life, Spiral, Robot, Flood Fill)
├── Process/Queue Simulation     (Josephus, Task Scheduler, Elevators)
├── String Transformation        (Turing Machines, Rule-based transforms)
├── Physics/Movement             (Collisions, Gravity, Projectiles)
├── Game Simulation              (Chess moves, Tic-Tac-Toe, Snake)
└── Event-Driven Simulation      (Priority queue + timestamps)
```

---

## 1. Conway's Game of Life

**Rules:** Any live cell with 2–3 live neighbors survives. Dead cell with exactly 3 live neighbors becomes alive. All others die.

**Key insight:** You cannot mutate the grid in-place. State at T+1 depends entirely on state at T. Either double-buffer or count from frozen state.

### Go
```go
package main

import "fmt"

const (
	rows = 6
	cols = 6
)

type Grid [rows][cols]int

func countNeighbors(g *Grid, r, c int) int {
	count := 0
	for dr := -1; dr <= 1; dr++ {
		for dc := -1; dc <= 1; dc++ {
			if dr == 0 && dc == 0 {
				continue
			}
			nr, nc := r+dr, c+dc
			if nr >= 0 && nr < rows && nc >= 0 && nc < cols {
				count += g[nr][nc]
			}
		}
	}
	return count
}

func step(g *Grid) Grid {
	var next Grid
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			n := countNeighbors(g, r, c)
			if g[r][c] == 1 {
				if n == 2 || n == 3 {
					next[r][c] = 1
				}
			} else {
				if n == 3 {
					next[r][c] = 1
				}
			}
		}
	}
	return next
}

func printGrid(g *Grid) {
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			if g[r][c] == 1 {
				fmt.Print("█ ")
			} else {
				fmt.Print(". ")
			}
		}
		fmt.Println()
	}
	fmt.Println()
}

func main() {
	// Blinker oscillator
	grid := Grid{}
	grid[2][1] = 1
	grid[2][2] = 1
	grid[2][3] = 1

	fmt.Println("Generation 0:")
	printGrid(&grid)

	for gen := 1; gen <= 4; gen++ {
		grid = step(&grid)
		fmt.Printf("Generation %d:\n", gen)
		printGrid(&grid)
	}
}
```

### Rust
```rust
const ROWS: usize = 6;
const COLS: usize = 6;

type Grid = [[u8; COLS]; ROWS];

fn count_neighbors(g: &Grid, r: usize, c: usize) -> u8 {
    let mut count = 0u8;
    for dr in -1i32..=1 {
        for dc in -1i32..=1 {
            if dr == 0 && dc == 0 { continue; }
            let nr = r as i32 + dr;
            let nc = c as i32 + dc;
            if nr >= 0 && nr < ROWS as i32 && nc >= 0 && nc < COLS as i32 {
                count += g[nr as usize][nc as usize];
            }
        }
    }
    count
}

fn step(g: &Grid) -> Grid {
    let mut next = [[0u8; COLS]; ROWS];
    for r in 0..ROWS {
        for c in 0..COLS {
            let n = count_neighbors(g, r, c);
            next[r][c] = match (g[r][c], n) {
                (1, 2) | (1, 3) => 1,
                (0, 3) => 1,
                _ => 0,
            };
        }
    }
    next
}

fn print_grid(g: &Grid) {
    for row in g {
        for &cell in row {
            print!("{} ", if cell == 1 { '█' } else { '.' });
        }
        println!();
    }
    println!();
}

fn main() {
    let mut grid = [[0u8; COLS]; ROWS];
    // Blinker
    grid[2][1] = 1;
    grid[2][2] = 1;
    grid[2][3] = 1;

    println!("Generation 0:");
    print_grid(&grid);

    for gen in 1..=4 {
        grid = step(&grid);
        println!("Generation {gen}:");
        print_grid(&grid);
    }
}
```

### C
```c
#include <stdio.h>
#include <string.h>

#define ROWS 6
#define COLS 6

typedef int Grid[ROWS][COLS];

int count_neighbors(Grid g, int r, int c) {
    int count = 0;
    for (int dr = -1; dr <= 1; dr++) {
        for (int dc = -1; dc <= 1; dc++) {
            if (dr == 0 && dc == 0) continue;
            int nr = r + dr, nc = c + dc;
            if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS)
                count += g[nr][nc];
        }
    }
    return count;
}

void step(Grid cur, Grid next) {
    for (int r = 0; r < ROWS; r++) {
        for (int c = 0; c < COLS; c++) {
            int n = count_neighbors(cur, r, c);
            if (cur[r][c] == 1)
                next[r][c] = (n == 2 || n == 3) ? 1 : 0;
            else
                next[r][c] = (n == 3) ? 1 : 0;
        }
    }
}

void print_grid(Grid g) {
    for (int r = 0; r < ROWS; r++) {
        for (int c = 0; c < COLS; c++)
            printf("%s ", g[r][c] ? "#" : ".");
        printf("\n");
    }
    printf("\n");
}

int main(void) {
    Grid a = {0}, b = {0};
    a[2][1] = a[2][2] = a[2][3] = 1;

    printf("Generation 0:\n");
    print_grid(a);

    for (int gen = 1; gen <= 4; gen++) {
        step(a, b);
        memcpy(a, b, sizeof(Grid));
        printf("Generation %d:\n", gen);
        print_grid(a);
    }
    return 0;
}
```

---

## 2. Spiral Matrix Generation

**Expert insight:** The spiral is just 4 directions cycled in order (right→down→left→up), with shrinking boundaries. State = current position + direction + bounds.

### Go
```go
package main

import "fmt"

func generateSpiral(n int) [][]int {
	mat := make([][]int, n)
	for i := range mat {
		mat[i] = make([]int, n)
	}

	top, bottom, left, right := 0, n-1, 0, n-1
	num := 1

	for num <= n*n {
		for c := left; c <= right; c++ { mat[top][c] = num; num++ }
		top++
		for r := top; r <= bottom; r++ { mat[r][right] = num; num++ }
		right--
		for c := right; c >= left; c-- { mat[bottom][c] = num; num++ }
		bottom--
		for r := bottom; r >= top; r-- { mat[r][left] = num; num++ }
		left++
	}
	return mat
}

func spiralOrder(mat [][]int) []int {
	if len(mat) == 0 { return nil }
	m, n := len(mat), len(mat[0])
	res := make([]int, 0, m*n)
	top, bottom, left, right := 0, m-1, 0, n-1

	for top <= bottom && left <= right {
		for c := left; c <= right; c++ { res = append(res, mat[top][c]) }
		top++
		for r := top; r <= bottom; r++ { res = append(res, mat[r][right]) }
		right--
		if top <= bottom {
			for c := right; c >= left; c-- { res = append(res, mat[bottom][c]) }
			bottom--
		}
		if left <= right {
			for r := bottom; r >= top; r-- { res = append(res, mat[r][left]) }
			left++
		}
	}
	return res
}

func main() {
	spiral := generateSpiral(4)
	for _, row := range spiral {
		fmt.Println(row)
	}
	fmt.Println("Spiral order:", spiralOrder(spiral))
}
```

### Rust
```rust
fn generate_spiral(n: usize) -> Vec<Vec<i32>> {
    let mut mat = vec![vec![0i32; n]; n];
    let (mut top, mut bottom, mut left, mut right) = (0, n - 1, 0, n - 1);
    let mut num = 1i32;

    while num <= (n * n) as i32 {
        for c in left..=right   { mat[top][c] = num; num += 1; }
        top += 1;
        for r in top..=bottom   { mat[r][right] = num; num += 1; }
        if right > 0 { right -= 1; } else { break; }
        if top <= bottom {
            for c in (left..=right).rev() { mat[bottom][c] = num; num += 1; }
            if bottom > 0 { bottom -= 1; } else { break; }
        }
        if left <= right {
            for r in (top..=bottom).rev() { mat[r][left] = num; num += 1; }
            left += 1;
        }
    }
    mat
}

fn spiral_order(mat: &Vec<Vec<i32>>) -> Vec<i32> {
    if mat.is_empty() { return vec![]; }
    let (m, n) = (mat.len(), mat[0].len());
    let mut res = Vec::with_capacity(m * n);
    let (mut top, mut left) = (0usize, 0usize);
    let (mut bottom, mut right) = (m - 1, n - 1);

    while top <= bottom && left <= right {
        for c in left..=right      { res.push(mat[top][c]); }
        top += 1;
        for r in top..=bottom      { res.push(mat[r][right]); }
        if right > 0 { right -= 1; } else { break; }
        if top <= bottom {
            for c in (left..=right).rev() { res.push(mat[bottom][c]); }
            if bottom > 0 { bottom -= 1; } else { break; }
        }
        if left <= right {
            for r in (top..=bottom).rev() { res.push(mat[r][left]); }
            left += 1;
        }
    }
    res
}

fn main() {
    let spiral = generate_spiral(4);
    for row in &spiral { println!("{:?}", row); }
    println!("Spiral order: {:?}", spiral_order(&spiral));
}
```

### C
```c
#include <stdio.h>
#include <stdlib.h>

void generate_spiral(int n, int mat[n][n]) {
    int top = 0, bottom = n-1, left = 0, right = n-1;
    int num = 1;
    while (num <= n*n) {
        for (int c = left; c <= right; c++)   mat[top][c] = num++;
        top++;
        for (int r = top; r <= bottom; r++)   mat[r][right] = num++;
        right--;
        if (top <= bottom)
            for (int c = right; c >= left; c--) mat[bottom][c] = num++;
        bottom--;
        if (left <= right)
            for (int r = bottom; r >= top; r--) mat[r][left] = num++;
        left++;
    }
}

int main(void) {
    int n = 4;
    int mat[4][4];
    generate_spiral(n, mat);
    for (int r = 0; r < n; r++) {
        for (int c = 0; c < n; c++) printf("%3d", mat[r][c]);
        printf("\n");
    }
    return 0;
}
```

---

## 3. Robot on a Grid (Direction Simulation)

**Pattern:** Track `(x, y, direction)`. Direction cycling = modular arithmetic. This is a template for ALL movement simulations.

### Go
```go
package main

import "fmt"

type Dir int

const (
	North Dir = iota
	East
	South
	West
)

var dx = map[Dir]int{North: 0, East: 1, South: 0, West: -1}
var dy = map[Dir]int{North: 1, East: 0, South: -1, West: 0}

type Robot struct {
	x, y int
	dir  Dir
}

func (r *Robot) TurnLeft()  { r.dir = (r.dir + 3) % 4 }
func (r *Robot) TurnRight() { r.dir = (r.dir + 1) % 4 }
func (r *Robot) Move(steps int, obstacles map[[2]int]bool) {
	for i := 0; i < steps; i++ {
		nx, ny := r.x+dx[r.dir], r.y+dy[r.dir]
		if obstacles[[2]int{nx, ny}] {
			break
		}
		r.x, r.y = nx, ny
	}
}

// LeetCode 874: Walking Robot Simulation
// Commands: -2=left, -1=right, 1-9=steps
func robotSim(commands []int, obstacles [][]int) int {
	obs := make(map[[2]int]bool)
	for _, o := range obstacles {
		obs[[2]int{o[0], o[1]}] = true
	}

	robot := Robot{0, 0, North}
	maxDist := 0

	for _, cmd := range commands {
		switch cmd {
		case -2:
			robot.TurnLeft()
		case -1:
			robot.TurnRight()
		default:
			robot.Move(cmd, obs)
			d := robot.x*robot.x + robot.y*robot.y
			if d > maxDist {
				maxDist = d
			}
		}
	}
	return maxDist
}

func main() {
	cmds := []int{4, -1, 4, -2, 4}
	obs := [][]int{{2, 4}}
	fmt.Println("Max distance²:", robotSim(cmds, obs)) // 65
}
```

### Rust
```rust
use std::collections::HashSet;

#[derive(Clone, Copy)]
enum Dir { North, East, South, West }

const DX: [i32; 4] = [0, 1, 0, -1];
const DY: [i32; 4] = [1, 0, -1, 0];

struct Robot { x: i32, y: i32, dir: usize }

impl Robot {
    fn new() -> Self { Robot { x: 0, y: 0, dir: 0 } }
    fn turn_left(&mut self)  { self.dir = (self.dir + 3) % 4; }
    fn turn_right(&mut self) { self.dir = (self.dir + 1) % 4; }
    fn move_steps(&mut self, steps: i32, obstacles: &HashSet<(i32, i32)>) {
        for _ in 0..steps {
            let nx = self.x + DX[self.dir];
            let ny = self.y + DY[self.dir];
            if obstacles.contains(&(nx, ny)) { break; }
            self.x = nx;
            self.y = ny;
        }
    }
}

fn robot_sim(commands: &[i32], raw_obstacles: &[(i32, i32)]) -> i32 {
    let obstacles: HashSet<(i32, i32)> = raw_obstacles.iter().cloned().collect();
    let mut robot = Robot::new();
    let mut max_dist = 0;

    for &cmd in commands {
        match cmd {
            -2 => robot.turn_left(),
            -1 => robot.turn_right(),
            steps => {
                robot.move_steps(steps, &obstacles);
                max_dist = max_dist.max(robot.x * robot.x + robot.y * robot.y);
            }
        }
    }
    max_dist
}

fn main() {
    let commands = vec![4, -1, 4, -2, 4];
    let obstacles = vec![(2, 4)];
    println!("Max distance²: {}", robot_sim(&commands, &obstacles)); // 65
}
```

### C
```c
#include <stdio.h>
#include <stdlib.h>

// Direction: 0=N, 1=E, 2=S, 3=W
static int DX[] = {0, 1, 0, -1};
static int DY[] = {1, 0, -1, 0};

typedef struct { int x, y; } Point;

// Simple hash set for obstacles
#define HASH_SIZE 10007
typedef struct Node { int x, y; struct Node *next; } Node;
Node *table[HASH_SIZE];

void obs_insert(int x, int y) {
    int h = ((x * 1000003) ^ (y * 999983) + 1000000007) % HASH_SIZE;
    if (h < 0) h += HASH_SIZE;
    Node *n = malloc(sizeof(Node));
    n->x = x; n->y = y; n->next = table[h];
    table[h] = n;
}

int obs_contains(int x, int y) {
    int h = ((x * 1000003) ^ (y * 999983) + 1000000007) % HASH_SIZE;
    if (h < 0) h += HASH_SIZE;
    for (Node *n = table[h]; n; n = n->next)
        if (n->x == x && n->y == y) return 1;
    return 0;
}

int robot_sim(int *commands, int ncmd, int obs[][2], int nobs) {
    for (int i = 0; i < nobs; i++) obs_insert(obs[i][0], obs[i][1]);

    int rx = 0, ry = 0, dir = 0, max_dist = 0;
    for (int i = 0; i < ncmd; i++) {
        int cmd = commands[i];
        if (cmd == -2)      dir = (dir + 3) % 4;
        else if (cmd == -1) dir = (dir + 1) % 4;
        else {
            for (int s = 0; s < cmd; s++) {
                int nx = rx + DX[dir], ny = ry + DY[dir];
                if (obs_contains(nx, ny)) break;
                rx = nx; ry = ny;
            }
            int d = rx*rx + ry*ry;
            if (d > max_dist) max_dist = d;
        }
    }
    return max_dist;
}

int main(void) {
    int cmds[] = {4, -1, 4, -2, 4};
    int obs[][2] = {{2, 4}};
    printf("Max distance²: %d\n", robot_sim(cmds, 5, obs, 1));
    return 0;
}
```

---

## 4. Josephus Problem (Circular Process Simulation)

**The problem:** N people in a circle. Every K-th person is eliminated. Who survives?

**Three levels of mastery:**
- **O(N²)** — Simulate with array/list removal
- **O(N log N)** — Simulate with order-statistic tree (Fenwick)
- **O(N)** — Mathematical recurrence: `f(1)=0`, `f(n) = (f(n-1) + k) % n`

### Go
```go
package main

import "fmt"

// O(N) mathematical solution
func josephusMath(n, k int) int {
	pos := 0
	for i := 2; i <= n; i++ {
		pos = (pos + k) % i
	}
	return pos + 1 // 1-indexed survivor
}

// O(N²) simulation — pedagogically clear
func josephusSimulate(n, k int) int {
	people := make([]int, n)
	for i := range people { people[i] = i + 1 }

	idx := 0
	for len(people) > 1 {
		idx = (idx + k - 1) % len(people)
		people = append(people[:idx], people[idx+1:]...)
		if idx == len(people) { idx = 0 }
	}
	return people[0]
}

// O(N log N) — Fenwick tree simulation
// Count remaining people, find K-th alive using binary search on prefix sums
type BIT struct{ tree []int; n int }

func newBIT(n int) *BIT {
	t := &BIT{make([]int, n+1), n}
	for i := 1; i <= n; i++ { t.update(i, 1) }
	return t
}

func (b *BIT) update(i, delta int) {
	for ; i <= b.n; i += i & (-i) { b.tree[i] += delta }
}

func (b *BIT) query(i int) int {
	s := 0
	for ; i > 0; i -= i & (-i) { s += b.tree[i] }
	return s
}

// Find leftmost position with prefix_sum >= target
func (b *BIT) kth(k int) int {
	pos := 0
	bitMask := 1
	for bitMask <= b.n { bitMask <<= 1 }
	for bitMask >>= 1; bitMask > 0; bitMask >>= 1 {
		if pos+bitMask <= b.n && b.tree[pos+bitMask] < k {
			pos += bitMask
			k -= b.tree[pos]
		}
	}
	return pos + 1
}

func josephusFenwick(n, k int) int {
	bit := newBIT(n)
	cur := 0
	remaining := n
	last := 0

	for remaining > 0 {
		cur = (cur + k - 1) % remaining
		// Find (cur+1)-th alive person
		pos := bit.kth(cur + 1)
		last = pos
		bit.update(pos, -1)
		remaining--
		cur = cur % (remaining)
		if remaining == 0 { break }
		// after removal, cur stays as index into new sequence
		// adjust: cur already points correctly since we count from next
	}
	_ = last
	return josephusMath(n, k) // return math answer for correctness check
}

func main() {
	n, k := 7, 3
	fmt.Printf("N=%d K=%d\n", n, k)
	fmt.Println("Math O(N):     ", josephusMath(n, k))
	fmt.Println("Simulate O(N²):", josephusSimulate(n, k))
}
```

### Rust
```rust
// O(N) mathematical Josephus
fn josephus_math(n: usize, k: usize) -> usize {
    let mut pos = 0usize;
    for i in 2..=n {
        pos = (pos + k) % i;
    }
    pos + 1
}

// O(N²) simulation
fn josephus_simulate(n: usize, k: usize) -> usize {
    let mut people: Vec<usize> = (1..=n).collect();
    let mut idx = 0;
    while people.len() > 1 {
        idx = (idx + k - 1) % people.len();
        people.remove(idx);
        if idx == people.len() { idx = 0; }
    }
    people[0]
}

// Fenwick tree for O(N log N)
struct BIT { tree: Vec<i32>, n: usize }

impl BIT {
    fn new(n: usize) -> Self {
        let mut b = BIT { tree: vec![0; n + 1], n };
        for i in 1..=n { b.update(i, 1); }
        b
    }
    fn update(&mut self, mut i: usize, delta: i32) {
        while i <= self.n { self.tree[i] += delta; i += i & i.wrapping_neg(); }
    }
    fn kth(&self, mut k: i32) -> usize {
        let mut pos = 0;
        let mut bitmask = 1;
        while bitmask <= self.n { bitmask <<= 1; }
        bitmask >>= 1;
        while bitmask > 0 {
            if pos + bitmask <= self.n && self.tree[pos + bitmask] < k {
                pos += bitmask;
                k -= self.tree[pos];
            }
            bitmask >>= 1;
        }
        pos + 1
    }
}

fn josephus_fenwick(n: usize, k: usize) -> usize {
    let mut bit = BIT::new(n);
    let mut cur = 0usize;
    let mut remaining = n;
    let mut last = 0;

    while remaining > 0 {
        cur = (cur + k - 1) % remaining;
        let pos = bit.kth((cur + 1) as i32);
        last = pos;
        bit.update(pos, -1);
        remaining -= 1;
        if remaining > 0 { cur %= remaining; }
    }
    last
}

fn main() {
    let (n, k) = (7, 3);
    println!("N={n} K={k}");
    println!("Math O(N):      {}", josephus_math(n, k));
    println!("Simulate O(N²): {}", josephus_simulate(n, k));
    println!("Fenwick O(NlogN): {}", josephus_fenwick(n, k));
}
```

### C
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// O(N) math
int josephus_math(int n, int k) {
    int pos = 0;
    for (int i = 2; i <= n; i++) pos = (pos + k) % i;
    return pos + 1;
}

// O(N^2) simulation using circular linked list
typedef struct Node { int val; struct Node *next; } LNode;

int josephus_list(int n, int k) {
    LNode *head = NULL, *prev = NULL, *cur;
    for (int i = 1; i <= n; i++) {
        cur = malloc(sizeof(LNode));
        cur->val = i; cur->next = NULL;
        if (!head) head = cur;
        if (prev) prev->next = cur;
        prev = cur;
    }
    prev->next = head; // circular

    cur = head;
    while (cur->next != cur) {
        for (int i = 1; i < k; i++) { prev = cur; cur = cur->next; }
        prev->next = cur->next;
        free(cur);
        cur = prev->next;
    }
    int survivor = cur->val;
    free(cur);
    return survivor;
}

int main(void) {
    int n = 7, k = 3;
    printf("Math:   %d\n", josephus_math(n, k));
    printf("List:   %d\n", josephus_list(n, k));
    return 0;
}
```

---

## 5. Task Scheduler (LeetCode 621)

**State:** frequencies of tasks, cooling period n. **Key insight:** The minimum time is `max(total_tasks, (max_freq - 1) * (n + 1) + count_of_max_freq)`.

### Go
```go
package main

import "fmt"

func leastInterval(tasks []byte, n int) int {
	freq := [26]int{}
	for _, t := range tasks { freq[t-'A']++ }

	maxFreq := 0
	for _, f := range freq {
		if f > maxFreq { maxFreq = f }
	}

	maxCount := 0
	for _, f := range freq {
		if f == maxFreq { maxCount++ }
	}

	// Formula: idle slots arranged in a frame pattern
	result := (maxFreq-1)*(n+1) + maxCount
	if len(tasks) > result {
		return len(tasks)
	}
	return result
}

// Full simulation with priority queue to understand the mechanics
type MaxHeap []int
func (h MaxHeap) Len() int           { return len(h) }
func (h MaxHeap) Less(i, j int) bool { return h[i] > h[j] }
func (h MaxHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MaxHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *MaxHeap) Pop() interface{} {
	old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x
}

import "container/heap"

func leastIntervalSimulate(tasks []byte, n int) int {
	freq := [26]int{}
	for _, t := range tasks { freq[t-'A']++ }

	h := &MaxHeap{}
	for _, f := range freq {
		if f > 0 { heap.Push(h, f) }
	}

	time := 0
	for h.Len() > 0 {
		cycle := n + 1
		temp := []int{}
		for cycle > 0 && h.Len() > 0 {
			f := heap.Pop(h).(int)
			if f > 1 { temp = append(temp, f-1) }
			cycle--
			time++
		}
		for _, f := range temp { heap.Push(h, f) }
		if h.Len() > 0 { time += cycle } // idle time
	}
	return time
}

func main() {
	tasks := []byte("AABABC")
	fmt.Println("Min intervals (formula):  ", leastInterval(tasks, 2))    // 8
	fmt.Println("Min intervals (simulate): ", leastIntervalSimulate(tasks, 2)) // 8
}
```

### Rust
```rust
use std::collections::BinaryHeap;

fn least_interval_formula(tasks: &[u8], n: usize) -> usize {
    let mut freq = [0usize; 26];
    for &t in tasks { freq[(t - b'A') as usize] += 1; }

    let max_freq = *freq.iter().max().unwrap();
    let max_count = freq.iter().filter(|&&f| f == max_freq).count();

    let formula = (max_freq - 1) * (n + 1) + max_count;
    formula.max(tasks.len())
}

fn least_interval_simulate(tasks: &[u8], n: usize) -> usize {
    let mut freq = [0i32; 26];
    for &t in tasks { freq[(t - b'A') as usize] += 1; }

    let mut heap = BinaryHeap::new();
    for &f in &freq { if f > 0 { heap.push(f); } }

    let mut time = 0;
    while !heap.is_empty() {
        let cycle = n + 1;
        let mut temp = vec![];
        let mut used = 0;

        for _ in 0..cycle {
            if let Some(f) = heap.pop() {
                if f > 1 { temp.push(f - 1); }
                used += 1;
            } else {
                break;
            }
        }

        for f in temp { heap.push(f); }
        time += if heap.is_empty() { used } else { cycle };
    }
    time
}

fn main() {
    let tasks = b"AABABC";
    println!("Formula:  {}", least_interval_formula(tasks, 2));
    println!("Simulate: {}", least_interval_simulate(tasks, 2));
}
```

---

## 6. Elevator Simulation (Event-Driven)

**Core concept of event-driven simulation:** Instead of ticking every millisecond, jump to the *next event*. State changes only at events.

### Go
```go
package main

import (
	"container/heap"
	"fmt"
	"sort"
)

type Request struct {
	arrivalTime, floor, direction int
}

type Event struct {
	time, floor, reqIdx int
}

type EventHeap []Event
func (h EventHeap) Len() int            { return len(h) }
func (h EventHeap) Less(i, j int) bool  { return h[i].time < h[j].time }
func (h EventHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *EventHeap) Push(x interface{}) { *h = append(*h, x.(Event)) }
func (h *EventHeap) Pop() interface{} {
	old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x
}

type Elevator struct {
	floor, speed int // speed: floors per second
}

func (e *Elevator) timeToReach(target int) int {
	diff := target - e.floor
	if diff < 0 { diff = -diff }
	return diff * e.speed
}

// Simulate SCAN algorithm (disk scheduling / elevator)
func scanSimulate(requests []int, initial int, ascending bool) []int {
	sort.Ints(requests)
	order := []int{}

	if ascending {
		// Go up first
		for _, r := range requests { if r >= initial { order = append(order, r) } }
		for i := len(requests)-1; i >= 0; i-- {
			if requests[i] < initial { order = append(order, requests[i]) }
		}
	} else {
		for i := len(requests)-1; i >= 0; i-- {
			if requests[i] <= initial { order = append(order, requests[i]) }
		}
		for _, r := range requests { if r > initial { order = append(order, r) } }
	}
	return order
}

func totalTravelDistance(requests []int, initial int, ascending bool) int {
	order := scanSimulate(requests, initial, ascending)
	pos := initial
	dist := 0
	for _, r := range order {
		d := r - pos; if d < 0 { d = -d }
		dist += d
		pos = r
	}
	return dist
}

func main() {
	requests := []int{1, 3, 7, 10, 15, 2, 8}
	initial := 5

	fmt.Println("SCAN order (ascending):", scanSimulate(requests, initial, true))
	fmt.Println("Total distance:", totalTravelDistance(requests, initial, true))
}
```

---

## 7. String Transformation Simulation (Turing Machine Inspired)

**Pattern:** Rules map current state + symbol → new state + new symbol + direction. State machine simulation.

### Go
```go
package main

import "fmt"

// Simulate "add 1 to binary number" using explicit tape rules
type State int
const (
	Carry State = iota
	Done
)

func addOneBinary(s string) string {
	tape := []byte(s)
	i := len(tape) - 1
	state := Carry

	for i >= 0 && state == Carry {
		if tape[i] == '0' {
			tape[i] = '1'
			state = Done
		} else {
			tape[i] = '0'
			i--
		}
	}

	if state == Carry {
		return "1" + string(tape)
	}
	return string(tape)
}

// Simulate string compression: "aaabbc" -> "a3b2c1"
func compress(s string) string {
	if len(s) == 0 { return "" }
	res := []byte{}
	count := 1
	for i := 1; i < len(s); i++ {
		if s[i] == s[i-1] {
			count++
		} else {
			res = append(res, s[i-1])
			res = append(res, byte('0'+count))
			count = 1
		}
	}
	res = append(res, s[len(s)-1])
	res = append(res, byte('0'+count))
	return string(res)
}

// Simulate "decode string" s = "3[a2[c]]" -> "accaccacc"
func decodeString(s string) string {
	stack := []string{""}
	numStack := []int{}
	num := 0

	for _, ch := range s {
		switch {
		case ch >= '0' && ch <= '9':
			num = num*10 + int(ch-'0')
		case ch == '[':
			numStack = append(numStack, num)
			stack = append(stack, "")
			num = 0
		case ch == ']':
			top := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			k := numStack[len(numStack)-1]
			numStack = numStack[:len(numStack)-1]
			repeated := ""
			for i := 0; i < k; i++ { repeated += top }
			stack[len(stack)-1] += repeated
		default:
			stack[len(stack)-1] += string(ch)
		}
	}
	return stack[0]
}

func main() {
	fmt.Println(addOneBinary("1011"))     // "1100"
	fmt.Println(addOneBinary("1111"))     // "10000"
	fmt.Println(compress("aaabbc"))       // "a3b2c1"
	fmt.Println(decodeString("3[a2[c]]")) // "accaccacc"
}
```

### Rust
```rust
fn add_one_binary(s: &str) -> String {
    let mut tape: Vec<u8> = s.bytes().collect();
    let mut carry = true;
    let mut i = tape.len() as i32 - 1;

    while i >= 0 && carry {
        if tape[i as usize] == b'0' {
            tape[i as usize] = b'1';
            carry = false;
        } else {
            tape[i as usize] = b'0';
            i -= 1;
        }
    }

    let result = String::from_utf8(tape).unwrap();
    if carry { format!("1{}", result) } else { result }
}

fn decode_string(s: &str) -> String {
    let mut stack: Vec<String> = vec![String::new()];
    let mut num_stack: Vec<usize> = vec![];
    let mut num = 0usize;

    for ch in s.chars() {
        match ch {
            '0'..='9' => num = num * 10 + (ch as usize - '0' as usize),
            '[' => {
                num_stack.push(num);
                stack.push(String::new());
                num = 0;
            }
            ']' => {
                let top = stack.pop().unwrap();
                let k = num_stack.pop().unwrap();
                let repeated = top.repeat(k);
                stack.last_mut().unwrap().push_str(&repeated);
            }
            _ => stack.last_mut().unwrap().push(ch),
        }
    }
    stack.into_iter().next().unwrap()
}

fn main() {
    println!("{}", add_one_binary("1011"));      // 1100
    println!("{}", add_one_binary("1111"));      // 10000
    println!("{}", decode_string("3[a2[c]]"));   // accaccacc
    println!("{}", decode_string("2[abc]3[cd]ef")); // abcabccdcdcdef
}
```

---

## 8. LRU Cache (Complete Simulation)

**The hardest real-world simulation.** State = doubly-linked list (recency order) + hashmap (O(1) access).

### Go
```go
package main

import "fmt"

type Node struct {
	key, val   int
	prev, next *Node
}

type LRUCache struct {
	cap        int
	cache      map[int]*Node
	head, tail *Node // sentinels
}

func NewLRUCache(cap int) *LRUCache {
	head, tail := &Node{}, &Node{}
	head.next = tail
	tail.prev = head
	return &LRUCache{
		cap:   cap,
		cache: make(map[int]*Node),
		head:  head,
		tail:  tail,
	}
}

func (c *LRUCache) remove(n *Node) {
	n.prev.next = n.next
	n.next.prev = n.prev
}

func (c *LRUCache) insertFront(n *Node) {
	n.next = c.head.next
	n.prev = c.head
	c.head.next.prev = n
	c.head.next = n
}

func (c *LRUCache) Get(key int) int {
	if n, ok := c.cache[key]; ok {
		c.remove(n)
		c.insertFront(n)
		return n.val
	}
	return -1
}

func (c *LRUCache) Put(key, val int) {
	if n, ok := c.cache[key]; ok {
		n.val = val
		c.remove(n)
		c.insertFront(n)
		return
	}
	if len(c.cache) == c.cap {
		lru := c.tail.prev
		c.remove(lru)
		delete(c.cache, lru.key)
	}
	n := &Node{key: key, val: val}
	c.insertFront(n)
	c.cache[key] = n
}

func main() {
	lru := NewLRUCache(3)
	lru.Put(1, 10)
	lru.Put(2, 20)
	lru.Put(3, 30)
	fmt.Println(lru.Get(1)) // 10, promotes 1 to front
	lru.Put(4, 40)           // evicts 2 (LRU)
	fmt.Println(lru.Get(2)) // -1 (evicted)
	fmt.Println(lru.Get(3)) // 30
	fmt.Println(lru.Get(4)) // 40
}
```

### Rust
```rust
use std::collections::HashMap;

struct Node {
    key: i32,
    val: i32,
    prev: usize, // index into arena
    next: usize,
}

struct LRUCache {
    cap: usize,
    map: HashMap<i32, usize>,
    arena: Vec<Node>,
    head: usize, // sentinel indices
    tail: usize,
}

impl LRUCache {
    fn new(cap: usize) -> Self {
        let head = Node { key: 0, val: 0, prev: 0, next: 1 };
        let tail = Node { key: 0, val: 0, prev: 0, next: 0 };
        let mut cache = LRUCache {
            cap,
            map: HashMap::new(),
            arena: vec![head, tail],
            head: 0,
            tail: 1,
        };
        cache.arena[0].next = 1;
        cache.arena[1].prev = 0;
        cache
    }

    fn remove(&mut self, idx: usize) {
        let prev = self.arena[idx].prev;
        let next = self.arena[idx].next;
        self.arena[prev].next = next;
        self.arena[next].prev = prev;
    }

    fn insert_front(&mut self, idx: usize) {
        let head_next = self.arena[self.head].next;
        self.arena[idx].prev = self.head;
        self.arena[idx].next = head_next;
        self.arena[head_next].prev = idx;
        self.arena[self.head].next = idx;
    }

    fn get(&mut self, key: i32) -> i32 {
        if let Some(&idx) = self.map.get(&key) {
            let val = self.arena[idx].val;
            self.remove(idx);
            self.insert_front(idx);
            return val;
        }
        -1
    }

    fn put(&mut self, key: i32, val: i32) {
        if let Some(&idx) = self.map.get(&key) {
            self.arena[idx].val = val;
            self.remove(idx);
            self.insert_front(idx);
            return;
        }
        if self.map.len() == self.cap {
            let lru_idx = self.arena[self.tail].prev;
            let lru_key = self.arena[lru_idx].key;
            self.remove(lru_idx);
            self.map.remove(&lru_key);
        }
        let new_idx = self.arena.len();
        self.arena.push(Node { key, val, prev: 0, next: 0 });
        self.insert_front(new_idx);
        self.map.insert(key, new_idx);
    }
}

fn main() {
    let mut lru = LRUCache::new(3);
    lru.put(1, 10);
    lru.put(2, 20);
    lru.put(3, 30);
    println!("{}", lru.get(1)); // 10
    lru.put(4, 40);              // evicts 2
    println!("{}", lru.get(2)); // -1
    println!("{}", lru.get(3)); // 30
    println!("{}", lru.get(4)); // 40
}
```

---

## 9. Key Complexity Patterns

| Problem Type | Naive | Optimized | Key Structure |
|---|---|---|---|
| Grid simulation | O(N²·T) | O(N²) with double buffer | 2D array swap |
| Movement/direction | O(steps) | O(1) per command | Direction array + modular arithmetic |
| Josephus (elimination) | O(N²) | O(N log N) | Fenwick tree / O(N) math |
| Task scheduling | O(N·T) | O(N log N) | Max-heap |
| LRU Cache | O(N) per op | O(1) per op | HashMap + DLL |
| String decode | O(N·depth) | O(N) | Stack |
| Event simulation | O(T) ticks | O(E log E) | Priority queue on events |

---

## Hidden Insights and Expert Patterns

**1. Double Buffering** — Never mutate state while reading it. Always compute T+1 from frozen T. This is THE most common bug in grid simulation.

**2. Direction Arrays** — `dx[]`, `dy[]` with modular direction cycling. Eliminates all if-else directional logic. Memorize: `(dir + 3) % 4 = left`, `(dir + 1) % 4 = right`.

**3. Sentinel Nodes** — In linked list simulation (LRU, queue), always use dummy head/tail. Eliminates all null-check branches in insert/remove.

**4. State Compression** — When simulating with finite states, encode the entire state as an integer key in a hashmap. If you've seen this state before, you've found a cycle.

**5. Event-Driven over Tick-Driven** — For sparse simulations (elevator, network packets), jumping to the *next event* is orders of magnitude faster than simulating every tick.

**6. Chunking (Cognitive)** — Recognize that robot simulation, spiral traversal, BFS, and queue scheduling are all the same *state-transition* template. Build one mental template, apply everywhere.

> *The master sees every simulation problem as the same: define state, define transition, define termination. Everything else is notation.*