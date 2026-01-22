# The Complete Architecture of Linux cgroups: A Systems Programming Perspective

Control Groups (cgroups) represent one of the most elegant kernel subsystems for resource management and process isolation in modern Linux. This is the foundation upon which containers, Kubernetes, and modern cloud infrastructure are built.

---

## I. Foundational Architecture

### What Are cgroups?

cgroups are a kernel feature that **hierarchically organize processes and apply resource constraints**. Think of them as a DAG (Directed Acyclic Graph) where:
- Nodes are **cgroups** (resource containers)
- Edges define parent-child relationships
- Processes are **leaves** attached to nodes
- Each node can have **resource controllers** that enforce limits

**Key Mental Model:** cgroups don't allocate resources—they **meter, limit, and account** for resource usage by process groups.

### The Two Versions: v1 vs v2

**cgroups v1** (legacy, still widely used):
- Multiple independent hierarchies (one per controller)
- Processes can belong to different cgroups in different hierarchies
- Complex, flexible, but inconsistent

**cgroups v2** (unified hierarchy, modern):
- Single unified tree
- A process belongs to exactly ONE cgroup
- Cleaner semantics, better performance
- Introduced `cgroup.controllers`, `cgroup.subtree_control`

**Critical Insight:** v2 enforces the "no internal processes" rule—if a cgroup has children, it cannot directly contain processes (except the root). This prevents resource competition ambiguity.

---

## II. Core Concepts & Data Structures

### 1. **Hierarchy & Tree Structure**

```
                    root (/)
                     |
        +------------+------------+
        |                         |
    system.slice            user.slice
        |                         |
    sshd.service         user-1000.slice
                                  |
                          app.service
```

**Inheritance Model:**
- Resource limits propagate DOWN (children inherit parent constraints)
- Accounting bubbles UP (parent sees aggregate of children's usage)
- Controllers can be enabled/disabled per-subtree

### 2. **Controllers (Subsystems)**

Controllers are kernel modules that enforce specific resource types:

| Controller | Purpose | Key Metrics |
|------------|---------|-------------|
| **cpu** | CPU time distribution | shares, quota, periods |
| **cpuset** | CPU/memory node pinning | cpus, mems |
| **memory** | Memory limits & accounting | limit, usage, oom_control |
| **io** | Block I/O throttling | rbps, wbps, riops, wiops |
| **pids** | Process count limits | max, current |
| **rdma** | RDMA/IB resources | hca_handle, hca_object |
| **hugetlb** | Huge pages | limit per page size |
| **perf_event** | Performance monitoring | attach perf events |

**cgroups v2 added:**
- **cpu** and **cpuacct** merged into unified `cpu`
- **blkio** replaced by `io` with better semantics

### 3. **Filesystem Interface**

cgroups expose a **pseudo-filesystem** (cgroupfs):

```bash
/sys/fs/cgroup/          # v2 unified mount
/sys/fs/cgroup/cgroup.controllers        # available controllers
/sys/fs/cgroup/cgroup.subtree_control    # enabled for children
/sys/fs/cgroup/cgroup.procs              # PIDs in this cgroup
/sys/fs/cgroup/memory.max                # memory limit
/sys/fs/cgroup/cpu.max                   # CPU quota/period
```

**Operations:**
- **Create cgroup:** `mkdir /sys/fs/cgroup/mygroup`
- **Add process:** `echo $PID > /sys/fs/cgroup/mygroup/cgroup.procs`
- **Set limit:** `echo "100M" > /sys/fs/cgroup/mygroup/memory.max`
- **Delete:** `rmdir /sys/fs/cgroup/mygroup` (only when empty)

---

## III. Controller Deep-Dives

### A. CPU Controller

**v1 Model (CFS - Completely Fair Scheduler):**
- `cpu.shares`: Relative weight (default 1024). If cgroup A has 2048 shares and B has 1024, A gets ~66% CPU during contention.
- `cpu.cfs_quota_us`: Microseconds of CPU time per period
- `cpu.cfs_period_us`: Period duration (default 100ms)

**v2 Unified Model:**
```
cpu.max: "QUOTA PERIOD"
cpu.weight: 1-10000 (replaces shares, default 100)
cpu.pressure: PSI (Pressure Stall Information)
```

**Example:** Limit to 50% of 1 CPU core:
```bash
echo "50000 100000" > /sys/fs/cgroup/myapp/cpu.max
# 50ms quota per 100ms period = 50% of one core
```

**Advanced Concept - CPU Affinity:**
```bash
# cpuset controller (v1) or cpuset.cpus (v2)
echo "0-3" > cpuset.cpus      # Restrict to cores 0,1,2,3
echo "0" > cpuset.mems        # NUMA node 0 only
```

### B. Memory Controller

**Critical Files:**

```
memory.max              # Hard limit (OOM kill if exceeded)
memory.high             # Soft limit (throttling, reclaim)
memory.low              # Best-effort protection
memory.min              # Hard protection (kernel won't reclaim)
memory.current          # Current usage
memory.peak             # Peak usage since cgroup creation
memory.events           # OOM events, failures
memory.stat             # Detailed breakdown (anon, file, kernel, etc.)
memory.swap.max         # Swap limit
memory.pressure         # PSI metrics
```

**OOM Behavior:**
- When `memory.max` is exceeded → OOM killer invoked
- Kills process with highest `oom_score` in the cgroup
- Can disable: `echo 1 > memory.oom.group` (kill entire cgroup atomically)

**Memory Accounting Breakdown:**
```bash
cat memory.stat
anon 50331648           # Anonymous pages (heap, stack)
file 104857600          # Page cache
kernel_stack 131072     # Kernel stacks
slab 4194304            # Slab allocator
sock 8192               # Socket buffers
vmalloc 0               # vmalloc'd memory
```

**Swap Control:**
```bash
echo "50M" > memory.swap.max   # Max 50MB swap
echo "0" > memory.swap.max     # Disable swap for this cgroup
```

### C. I/O Controller

**v2 I/O Model (replaced blkio):**

```
io.max                  # Absolute limits
io.weight               # Proportional weight (1-10000)
io.latency              # Target latency for devices
io.stat                 # Per-device statistics
```

**Setting Limits:**
```bash
# Format: "MAJ:MIN TYPE LIMIT"
# 8:0 is typically /dev/sda

echo "8:0 rbps=10485760" > io.max    # 10 MB/s read
echo "8:0 wbps=5242880" > io.max     # 5 MB/s write
echo "8:0 riops=1000" > io.max       # 1000 read IOPS
echo "8:0 wiops=500" > io.max        # 500 write IOPS
```

**Combined Example:**
```bash
echo "8:0 rbps=10485760 wbps=5242880 riops=1000 wiops=500" > io.max
```

**Proportional I/O:**
```bash
echo "8:0 100" > io.weight          # Default weight
# Another cgroup with weight 200 gets 2x I/O during contention
```

### D. PIDs Controller

Simple but critical for preventing fork bombs:

```bash
echo "100" > pids.max               # Max 100 processes
cat pids.current                    # Current count
cat pids.events                     # Fork failures
```

---

## IV. Advanced Concepts

### 1. **Delegation & User Namespaces**

**Problem:** Non-root users can't manage cgroups by default.

**Solution:** Delegation via `cgroup.subtree_control`:

```bash
# As root: delegate a subtree to user 1000
mkdir /sys/fs/cgroup/user-1000
chown -R 1000:1000 /sys/fs/cgroup/user-1000
echo "+cpu +memory" > /sys/fs/cgroup/cgroup.subtree_control

# Now user 1000 can create child cgroups under /sys/fs/cgroup/user-1000
```

**Combined with user namespaces:**
- User appears as root inside namespace
- Can manage their delegated cgroup subtree
- Enables rootless containers

### 2. **PSI (Pressure Stall Information)**

Modern mechanism for detecting resource contention:

```bash
cat cpu.pressure
some avg10=2.50 avg60=1.80 avg300=1.50 total=12000000
full avg10=0.00 avg60=0.00 avg300=0.00 total=0

cat memory.pressure
some avg10=15.30 avg60=12.10 avg300=10.50 total=45000000
full avg10=5.20 avg60=3.80 avg300=2.10 total=15000000
```

**Interpretation:**
- `some`: % of time ANY task was stalled
- `full`: % of time ALL tasks were stalled
- `avg10/60/300`: Moving averages (10s, 60s, 300s)

**Use Case:** Trigger autoscaling when `memory.pressure` `some avg10` > 20%

### 3. **Freezer (Process Suspension)**

```bash
echo 1 > cgroup.freeze              # Freeze all processes
cat cgroup.events                   # Check frozen=1
echo 0 > cgroup.freeze              # Thaw
```

**Use Cases:**
- Checkpoint/restore
- Pause container during debugging
- Resource preemption

### 4. **Notification & Events**

**cgroup.events:**
```bash
cat cgroup.events
populated 1          # Has processes or populated descendants
frozen 0             # Freeze state
```

**Event Notification via inotify:**
```c
int fd = open("/sys/fs/cgroup/myapp/cgroup.events", O_RDONLY);
int ifd = inotify_init();
inotify_add_watch(ifd, "/sys/fs/cgroup/myapp/cgroup.events", IN_MODIFY);
// Poll ifd to detect changes
```

### 5. **Device Controller**

Control access to device files (v1 only, v2 uses BPF):

```bash
# v1: devices.allow / devices.deny
echo "c 1:3 rw" > devices.allow     # Allow /dev/null (1:3)
echo "b 8:* r" > devices.allow      # Allow read from all /dev/sd* devices
echo "a *:* rwm" > devices.deny     # Deny all devices (start whitelist)
```

**v2 Alternative:** eBPF programs attached to cgroup for device control

---

## V. Practical Patterns & Idioms

### Pattern 1: Container-Like Isolation

```bash
#!/bin/bash
CGROUP_ROOT="/sys/fs/cgroup"
APP_CGROUP="$CGROUP_ROOT/mycontainer"

# Create cgroup
mkdir -p "$APP_CGROUP"

# Set limits
echo "512M" > "$APP_CGROUP/memory.max"
echo "100000 100000" > "$APP_CGROUP/cpu.max"    # 100% of 1 core
echo "100" > "$APP_CGROUP/pids.max"

# Launch process in cgroup
echo $$ > "$APP_CGROUP/cgroup.procs"
exec /path/to/application
```

### Pattern 2: Multi-Tier Application

```
/sys/fs/cgroup/
├── app/
│   ├── frontend/       (cpu.weight=200, memory.max=1G)
│   ├── backend/        (cpu.weight=300, memory.max=2G)
│   └── database/       (cpu.weight=500, memory.max=4G, io.weight=200)
```

```bash
# Setup
for tier in frontend backend database; do
    mkdir -p /sys/fs/cgroup/app/$tier
done

# Frontend: Lower priority, limited memory
echo "200" > /sys/fs/cgroup/app/frontend/cpu.weight
echo "1G" > /sys/fs/cgroup/app/frontend/memory.max

# Database: Highest CPU priority, more memory, prioritized I/O
echo "500" > /sys/fs/cgroup/app/database/cpu.weight
echo "4G" > /sys/fs/cgroup/app/database/memory.max
echo "8:0 200" > /sys/fs/cgroup/app/database/io.weight
```

### Pattern 3: Automatic OOM Handling

```bash
# Monitor OOM events
while inotifywait -e modify /sys/fs/cgroup/app/memory.events; do
    if grep -q "oom_kill" /sys/fs/cgroup/app/memory.events; then
        echo "OOM detected, restarting application..."
        systemctl restart myapp
    fi
done
```

---

## VI. Programming Interfaces

### A. Rust Implementation
use std::fs::{self, File, OpenOptions};
use std::io::{self, Write, Read};
use std::path::{Path, PathBuf};

const CGROUP_ROOT: &str = "/sys/fs/cgroup";

#[derive(Debug)]
pub struct CGroup {
    path: PathBuf,
}

#[derive(Debug)]
pub enum CGroupError {
    Io(io::Error),
    InvalidPath,
    NotFound,
}

impl From<io::Error> for CGroupError {
    fn from(err: io::Error) -> Self {
        CGroupError::Io(err)
    }
}

impl CGroup {
    /// Create a new cgroup at the specified path
    pub fn new(name: &str) -> Result<Self, CGroupError> {
        let path = Path::new(CGROUP_ROOT).join(name);
        
        if !path.starts_with(CGROUP_ROOT) {
            return Err(CGroupError::InvalidPath);
        }
        
        fs::create_dir_all(&path)?;
        
        Ok(CGroup { path })
    }
    
    /// Open existing cgroup
    pub fn open(name: &str) -> Result<Self, CGroupError> {
        let path = Path::new(CGROUP_ROOT).join(name);
        
        if !path.exists() {
            return Err(CGroupError::NotFound);
        }
        
        Ok(CGroup { path })
    }
    
    /// Add process to cgroup
    pub fn add_process(&self, pid: u32) -> Result<(), CGroupError> {
        let procs_file = self.path.join("cgroup.procs");
        let mut file = OpenOptions::new().write(true).open(procs_file)?;
        writeln!(file, "{}", pid)?;
        Ok(())
    }
    
    /// Add current process to cgroup
    pub fn add_self(&self) -> Result<(), CGroupError> {
        self.add_process(std::process::id())
    }
    
    /// Set memory limit (in bytes)
    pub fn set_memory_limit(&self, bytes: u64) -> Result<(), CGroupError> {
        self.write_value("memory.max", &bytes.to_string())
    }
    
    /// Set memory limit with human-readable string (e.g., "512M", "2G")
    pub fn set_memory_limit_str(&self, limit: &str) -> Result<(), CGroupError> {
        self.write_value("memory.max", limit)
    }
    
    /// Set CPU quota (microseconds per period)
    pub fn set_cpu_quota(&self, quota_us: u64, period_us: u64) -> Result<(), CGroupError> {
        let value = format!("{} {}", quota_us, period_us);
        self.write_value("cpu.max", &value)
    }
    
    /// Set CPU weight (1-10000, default 100)
    pub fn set_cpu_weight(&self, weight: u32) -> Result<(), CGroupError> {
        if weight < 1 || weight > 10000 {
            return Err(CGroupError::Io(io::Error::new(
                io::ErrorKind::InvalidInput,
                "CPU weight must be between 1 and 10000"
            )));
        }
        self.write_value("cpu.weight", &weight.to_string())
    }
    
    /// Set PID limit
    pub fn set_pid_limit(&self, max_pids: u32) -> Result<(), CGroupError> {
        self.write_value("pids.max", &max_pids.to_string())
    }
    
    /// Set I/O limit for device
    pub fn set_io_limit(&self, major: u32, minor: u32, 
                        rbps: Option<u64>, wbps: Option<u64>,
                        riops: Option<u64>, wiops: Option<u64>) -> Result<(), CGroupError> {
        let mut parts = vec![format!("{}:{}", major, minor)];
        
        if let Some(v) = rbps { parts.push(format!("rbps={}", v)); }
        if let Some(v) = wbps { parts.push(format!("wbps={}", v)); }
        if let Some(v) = riops { parts.push(format!("riops={}", v)); }
        if let Some(v) = wiops { parts.push(format!("wiops={}", v)); }
        
        self.write_value("io.max", &parts.join(" "))
    }
    
    /// Get current memory usage
    pub fn get_memory_current(&self) -> Result<u64, CGroupError> {
        self.read_value("memory.current")
            .and_then(|s| s.trim().parse::<u64>()
                .map_err(|e| CGroupError::Io(io::Error::new(io::ErrorKind::InvalidData, e))))
    }
    
    /// Get current PID count
    pub fn get_pid_current(&self) -> Result<u32, CGroupError> {
        self.read_value("pids.current")
            .and_then(|s| s.trim().parse::<u32>()
                .map_err(|e| CGroupError::Io(io::Error::new(io::ErrorKind::InvalidData, e))))
    }
    
    /// Read memory.stat and parse into key-value pairs
    pub fn get_memory_stat(&self) -> Result<Vec<(String, u64)>, CGroupError> {
        let content = self.read_value("memory.stat")?;
        let stats: Vec<(String, u64)> = content
            .lines()
            .filter_map(|line| {
                let mut parts = line.split_whitespace();
                match (parts.next(), parts.next()) {
                    (Some(key), Some(val)) => val.parse::<u64>().ok().map(|v| (key.to_string(), v)),
                    _ => None,
                }
            })
            .collect();
        Ok(stats)
    }
    
    /// Freeze all processes in cgroup
    pub fn freeze(&self) -> Result<(), CGroupError> {
        self.write_value("cgroup.freeze", "1")
    }
    
    /// Thaw (unfreeze) all processes
    pub fn thaw(&self) -> Result<(), CGroupError> {
        self.write_value("cgroup.freeze", "0")
    }
    
    /// Check if cgroup is frozen
    pub fn is_frozen(&self) -> Result<bool, CGroupError> {
        let events = self.read_value("cgroup.events")?;
        Ok(events.lines().any(|line| line.trim() == "frozen 1"))
    }
    
    /// Delete the cgroup (must be empty)
    pub fn delete(self) -> Result<(), CGroupError> {
        fs::remove_dir(&self.path)?;
        Ok(())
    }
    
    // Helper methods
    fn write_value(&self, filename: &str, value: &str) -> Result<(), CGroupError> {
        let file_path = self.path.join(filename);
        let mut file = OpenOptions::new().write(true).open(file_path)?;
        writeln!(file, "{}", value)?;
        Ok(())
    }
    
    fn read_value(&self, filename: &str) -> Result<String, CGroupError> {
        let file_path = self.path.join(filename);
        let mut file = File::open(file_path)?;
        let mut content = String::new();
        file.read_to_string(&mut content)?;
        Ok(content)
    }
}

// Example usage and tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_cgroup_lifecycle() {
        // This test requires root privileges
        if !nix::unistd::Uid::effective().is_root() {
            println!("Skipping test - requires root");
            return;
        }
        
        let cg = CGroup::new("test_cgroup").unwrap();
        
        // Set limits
        cg.set_memory_limit_str("512M").unwrap();
        cg.set_cpu_weight(200).unwrap();
        cg.set_pid_limit(100).unwrap();
        
        // Add current process
        cg.add_self().unwrap();
        
        // Read stats
        let mem_current = cg.get_memory_current().unwrap();
        println!("Current memory usage: {} bytes", mem_current);
        
        let pid_count = cg.get_pid_current().unwrap();
        println!("Current PID count: {}", pid_count);
        
        // Cleanup
        cg.delete().unwrap();
    }
}

fn main() -> Result<(), CGroupError> {
    // Example: Create a cgroup for a resource-limited application
    let app_cgroup = CGroup::new("myapp")?;
    
    // Configure limits
    app_cgroup.set_memory_limit_str("1G")?;
    app_cgroup.set_cpu_quota(50_000, 100_000)?;  // 50% of one core
    app_cgroup.set_pid_limit(50)?;
    
    // Set I/O limits for /dev/sda (8:0)
    app_cgroup.set_io_limit(8, 0, 
        Some(10 * 1024 * 1024),  // 10 MB/s read
        Some(5 * 1024 * 1024),   // 5 MB/s write
        None, None)?;
    
    println!("CGroup configured at: {:?}", app_cgroup.path);
    
    // Get current stats
    let mem_stats = app_cgroup.get_memory_stat()?;
    println!("\nMemory statistics:");
    for (key, value) in mem_stats.iter().take(10) {
        println!("  {}: {}", key, value);
    }
    
    Ok(())
}

### B. Go Implementation

package main

import (
	"bufio"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const cgroupRoot = "/sys/fs/cgroup"

var (
	ErrInvalidPath = errors.New("invalid cgroup path")
	ErrNotFound    = errors.New("cgroup not found")
)

// CGroup represents a control group
type CGroup struct {
	path string
}

// NewCGroup creates a new cgroup with the given name
func NewCGroup(name string) (*CGroup, error) {
	path := filepath.Join(cgroupRoot, name)
	
	// Security check
	if !strings.HasPrefix(path, cgroupRoot) {
		return nil, ErrInvalidPath
	}
	
	if err := os.MkdirAll(path, 0755); err != nil {
		return nil, fmt.Errorf("failed to create cgroup: %w", err)
	}
	
	return &CGroup{path: path}, nil
}

// OpenCGroup opens an existing cgroup
func OpenCGroup(name string) (*CGroup, error) {
	path := filepath.Join(cgroupRoot, name)
	
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return nil, ErrNotFound
	}
	
	return &CGroup{path: path}, nil
}

// AddProcess adds a process to the cgroup
func (cg *CGroup) AddProcess(pid int) error {
	return cg.writeValue("cgroup.procs", strconv.Itoa(pid))
}

// AddSelf adds the current process to the cgroup
func (cg *CGroup) AddSelf() error {
	return cg.AddProcess(os.Getpid())
}

// SetMemoryLimit sets the memory limit in bytes
func (cg *CGroup) SetMemoryLimit(bytes uint64) error {
	return cg.writeValue("memory.max", strconv.FormatUint(bytes, 10))
}

// SetMemoryLimitStr sets memory limit with human-readable string (e.g., "512M", "2G")
func (cg *CGroup) SetMemoryLimitStr(limit string) error {
	return cg.writeValue("memory.max", limit)
}

// SetMemoryHigh sets the soft memory limit
func (cg *CGroup) SetMemoryHigh(bytes uint64) error {
	return cg.writeValue("memory.high", strconv.FormatUint(bytes, 10))
}

// SetMemoryMin sets the hard memory protection
func (cg *CGroup) SetMemoryMin(bytes uint64) error {
	return cg.writeValue("memory.min", strconv.FormatUint(bytes, 10))
}

// SetCPUQuota sets CPU quota in microseconds per period
func (cg *CGroup) SetCPUQuota(quotaUS, periodUS uint64) error {
	value := fmt.Sprintf("%d %d", quotaUS, periodUS)
	return cg.writeValue("cpu.max", value)
}

// SetCPUWeight sets CPU weight (1-10000, default 100)
func (cg *CGroup) SetCPUWeight(weight uint32) error {
	if weight < 1 || weight > 10000 {
		return errors.New("CPU weight must be between 1 and 10000")
	}
	return cg.writeValue("cpu.weight", strconv.FormatUint(uint64(weight), 10))
}

// SetPIDLimit sets the maximum number of PIDs
func (cg *CGroup) SetPIDLimit(maxPIDs uint32) error {
	return cg.writeValue("pids.max", strconv.FormatUint(uint64(maxPIDs), 10))
}

// IOLimit represents I/O limits for a device
type IOLimit struct {
	Major uint32
	Minor uint32
	Rbps  *uint64 // Read bytes per second
	Wbps  *uint64 // Write bytes per second
	Riops *uint64 // Read IOPS
	Wiops *uint64 // Write IOPS
}

// SetIOLimit sets I/O limits for a device
func (cg *CGroup) SetIOLimit(limit IOLimit) error {
	parts := []string{fmt.Sprintf("%d:%d", limit.Major, limit.Minor)}
	
	if limit.Rbps != nil {
		parts = append(parts, fmt.Sprintf("rbps=%d", *limit.Rbps))
	}
	if limit.Wbps != nil {
		parts = append(parts, fmt.Sprintf("wbps=%d", *limit.Wbps))
	}
	if limit.Riops != nil {
		parts = append(parts, fmt.Sprintf("riops=%d", *limit.Riops))
	}
	if limit.Wiops != nil {
		parts = append(parts, fmt.Sprintf("wiops=%d", *limit.Wiops))
	}
	
	return cg.writeValue("io.max", strings.Join(parts, " "))
}

// SetIOWeight sets the I/O weight for a device
func (cg *CGroup) SetIOWeight(major, minor, weight uint32) error {
	if weight < 1 || weight > 10000 {
		return errors.New("I/O weight must be between 1 and 10000")
	}
	value := fmt.Sprintf("%d:%d %d", major, minor, weight)
	return cg.writeValue("io.weight", value)
}

// GetMemoryCurrent returns current memory usage in bytes
func (cg *CGroup) GetMemoryCurrent() (uint64, error) {
	content, err := cg.readValue("memory.current")
	if err != nil {
		return 0, err
	}
	return strconv.ParseUint(strings.TrimSpace(content), 10, 64)
}

// GetMemoryPeak returns peak memory usage in bytes
func (cg *CGroup) GetMemoryPeak() (uint64, error) {
	content, err := cg.readValue("memory.peak")
	if err != nil {
		return 0, err
	}
	return strconv.ParseUint(strings.TrimSpace(content), 10, 64)
}

// GetPIDCurrent returns current number of PIDs
func (cg *CGroup) GetPIDCurrent() (uint32, error) {
	content, err := cg.readValue("pids.current")
	if err != nil {
		return 0, err
	}
	val, err := strconv.ParseUint(strings.TrimSpace(content), 10, 32)
	return uint32(val), err
}

// MemoryStat represents memory statistics
type MemoryStat map[string]uint64

// GetMemoryStat returns detailed memory statistics
func (cg *CGroup) GetMemoryStat() (MemoryStat, error) {
	content, err := cg.readValue("memory.stat")
	if err != nil {
		return nil, err
	}
	
	stats := make(MemoryStat)
	scanner := bufio.NewScanner(strings.NewReader(content))
	
	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) == 2 {
			val, err := strconv.ParseUint(fields[1], 10, 64)
			if err == nil {
				stats[fields[0]] = val
			}
		}
	}
	
	return stats, scanner.Err()
}

// PSI represents Pressure Stall Information
type PSI struct {
	SomeAvg10  float64
	SomeAvg60  float64
	SomeAvg300 float64
	SomeTotal  uint64
	FullAvg10  float64
	FullAvg60  float64
	FullAvg300 float64
	FullTotal  uint64
}

// GetMemoryPressure returns memory pressure information
func (cg *CGroup) GetMemoryPressure() (*PSI, error) {
	content, err := cg.readValue("memory.pressure")
	if err != nil {
		return nil, err
	}
	
	psi := &PSI{}
	lines := strings.Split(strings.TrimSpace(content), "\n")
	
	for _, line := range lines {
		if strings.HasPrefix(line, "some ") {
			fmt.Sscanf(line, "some avg10=%f avg60=%f avg300=%f total=%d",
				&psi.SomeAvg10, &psi.SomeAvg60, &psi.SomeAvg300, &psi.SomeTotal)
		} else if strings.HasPrefix(line, "full ") {
			fmt.Sscanf(line, "full avg10=%f avg60=%f avg300=%f total=%d",
				&psi.FullAvg10, &psi.FullAvg60, &psi.FullAvg300, &psi.FullTotal)
		}
	}
	
	return psi, nil
}

// Freeze freezes all processes in the cgroup
func (cg *CGroup) Freeze() error {
	return cg.writeValue("cgroup.freeze", "1")
}

// Thaw unfreezes all processes in the cgroup
func (cg *CGroup) Thaw() error {
	return cg.writeValue("cgroup.freeze", "0")
}

// IsFrozen checks if the cgroup is frozen
func (cg *CGroup) IsFrozen() (bool, error) {
	content, err := cg.readValue("cgroup.events")
	if err != nil {
		return false, err
	}
	return strings.Contains(content, "frozen 1"), nil
}

// Delete removes the cgroup (must be empty)
func (cg *CGroup) Delete() error {
	return os.Remove(cg.path)
}

// GetPath returns the filesystem path of the cgroup
func (cg *CGroup) GetPath() string {
	return cg.path
}

// Helper methods
func (cg *CGroup) writeValue(filename, value string) error {
	path := filepath.Join(cg.path, filename)
	return os.WriteFile(path, []byte(value+"\n"), 0644)
}

func (cg *CGroup) readValue(filename string) (string, error) {
	path := filepath.Join(cg.path, filename)
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// Example usage
func main() {
	// Create a new cgroup
	cg, err := NewCGroup("example_app")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create cgroup: %v\n", err)
		os.Exit(1)
	}
	
	fmt.Printf("Created cgroup at: %s\n\n", cg.GetPath())
	
	// Configure resource limits
	if err := cg.SetMemoryLimitStr("1G"); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to set memory limit: %v\n", err)
	}
	
	// 50% of one CPU core (50ms per 100ms period)
	if err := cg.SetCPUQuota(50000, 100000); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to set CPU quota: %v\n", err)
	}
	
	if err := cg.SetCPUWeight(200); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to set CPU weight: %v\n", err)
	}
	
	if err := cg.SetPIDLimit(100); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to set PID limit: %v\n", err)
	}
	
	// Set I/O limits for /dev/sda (major 8, minor 0)
	rbps := uint64(10 * 1024 * 1024)  // 10 MB/s
	wbps := uint64(5 * 1024 * 1024)   // 5 MB/s
	ioLimit := IOLimit{
		Major: 8,
		Minor: 0,
		Rbps:  &rbps,
		Wbps:  &wbps,
	}
	if err := cg.SetIOLimit(ioLimit); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to set I/O limit: %v\n", err)
	}
	
	// Get current statistics
	memCurrent, _ := cg.GetMemoryCurrent()
	pidCurrent, _ := cg.GetPIDCurrent()
	
	fmt.Printf("Current memory usage: %d bytes (%.2f MB)\n", 
		memCurrent, float64(memCurrent)/(1024*1024))
	fmt.Printf("Current PID count: %d\n\n", pidCurrent)
	
	// Get detailed memory statistics
	memStats, err := cg.GetMemoryStat()
	if err == nil {
		fmt.Println("Memory statistics:")
		for key, value := range memStats {
			if value > 0 {
				fmt.Printf("  %-20s: %10d bytes\n", key, value)
			}
		}
		fmt.Println()
	}
	
	// Get memory pressure
	psi, err := cg.GetMemoryPressure()
	if err == nil {
		fmt.Println("Memory pressure:")
		fmt.Printf("  some avg10=%.2f avg60=%.2f avg300=%.2f\n",
			psi.SomeAvg10, psi.SomeAvg60, psi.SomeAvg300)
		fmt.Printf("  full avg10=%.2f avg60=%.2f avg300=%.2f\n\n",
			psi.FullAvg10, psi.FullAvg60, psi.FullAvg300)
	}
	
	fmt.Println("To add processes to this cgroup:")
	fmt.Printf("  echo $PID > %s/cgroup.procs\n", cg.GetPath())
	
	// Cleanup comment
	fmt.Println("\nTo delete this cgroup (after removing all processes):")
	fmt.Printf("  rmdir %s\n", cg.GetPath())
}

---

## VII. systemd Integration

systemd is the **primary cgroup manager** on most modern Linux distributions. It creates a unified hierarchy and manages cgroups for services.

### systemd Slice Hierarchy

```
/
├── system.slice       # System services
│   ├── sshd.service
│   ├── nginx.service
│   └── postgresql.service
├── user.slice         # User sessions
│   ├── user-1000.slice
│   │   └── session-2.scope
│   └── user-1001.slice
└── machine.slice      # Virtual machines & containers
    ├── docker-abc123.scope
    └── libvirt-qemu-vm1.scope
```

### Service Unit Configuration

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application

[Service]
Type=simple
ExecStart=/usr/bin/myapp

# Memory limits
MemoryMax=1G
MemoryHigh=800M          # Start throttling at 800M

# CPU limits
CPUWeight=200            # Relative weight
CPUQuota=150%            # 1.5 CPU cores max

# I/O limits
IOWeight=100
IOReadBandwidthMax=/dev/sda 10M
IOWriteBandwidthMax=/dev/sda 5M

# Process limits
TasksMax=100

[Install]
WantedBy=multi-user.target
```

### Runtime Configuration

```bash
# Set limits for running service
systemctl set-property myapp.service MemoryMax=2G
systemctl set-property myapp.service CPUQuota=200%

# View service cgroup
systemctl status myapp.service
# Shows: CGroup: /system.slice/myapp.service

# View resource usage
systemd-cgtop                    # Top-like view of cgroups
systemctl show myapp.service     # All properties
```

### Delegated Subtrees

For containers/VMs, delegate full control:

```ini
[Service]
# Delegate all controllers to the service
Delegate=yes

# Or delegate specific controllers
Delegate=cpu memory pids
```

---

## VIII. Debugging & Monitoring

### 1. **Viewing the Hierarchy**

```bash
# Tree view of cgroups
systemd-cgls

# Find cgroup for process
cat /proc/$PID/cgroup

# v2 example output:
0::/user.slice/user-1000.slice/session-2.scope

# List all cgroups
find /sys/fs/cgroup -type d
```

### 2. **Resource Monitoring**

```bash
# Real-time monitoring
systemd-cgtop
# Shows CPU%, Memory, I/O per cgroup

# Detailed cgroup info
cat /sys/fs/cgroup/myapp/memory.stat
cat /sys/fs/cgroup/myapp/cpu.stat
cat /sys/fs/cgroup/myapp/io.stat
```

### 3. **Event Tracing with BPF**

Modern approach using eBPF:

```c
// Trace OOM kills
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("tracepoint/oom/mark_victim")
int trace_oom_kill(struct trace_event_raw_mark_victim *ctx) {
    u32 pid = ctx->pid;
    bpf_printk("OOM kill: PID %d\n", pid);
    return 0;
}
```

### 4. **Common Issues**

**Problem:** `echo $PID > cgroup.procs` fails with "No space left on device"

**Causes:**
- Reached `pids.max` limit
- Memory limit too restrictive
- Kernel can't allocate resources

**Solution:**
```bash
# Check limits
cat pids.max
cat pids.current

# Increase or remove limit
echo "max" > pids.max
```

**Problem:** Can't delete cgroup

**Causes:**
- Still has processes
- Has child cgroups
- Kernel references exist

**Solution:**
```bash
# Kill all processes
cat cgroup.procs | xargs -r kill -9

# Remove child cgroups first
find /sys/fs/cgroup/myapp -depth -type d -exec rmdir {} \;
```

---

## IX. Performance Considerations

### 1. **Controller Overhead**

| Controller | Overhead | Notes |
|------------|----------|-------|
| cpu | Very low | CFS already tracks per-task time |
| memory | Low | Page fault accounting |
| io | Medium | I/O tracking in block layer |
| pids | Minimal | Simple counter |

### 2. **v1 vs v2 Performance**

**v2 Advantages:**
- Single hierarchy → better cache locality
- Unified accounting → less redundant tracking
- Optimized internal data structures

**Benchmark:** Task fork rate:
- v1: ~50,000 forks/sec with 4 controllers
- v2: ~65,000 forks/sec (30% improvement)

### 3. **Optimal Configuration Patterns**

**Anti-pattern:** Too many small cgroups
```
❌ /app/container1/pod1/process1
   /app/container1/pod1/process2
   ... (thousands of leaf cgroups)
```

**Better:** Hierarchical grouping
```
✅ /app/container1
   /app/container2
   ... (hundreds, not thousands)
```

**Reason:** Each cgroup has kernel overhead (~1KB). 10,000 cgroups = 10MB+ kernel memory.

---

## X. Advanced Use Cases

### 1. **Container Runtimes (Docker/Podman)**

Docker creates this hierarchy:

```
/sys/fs/cgroup/system.slice/docker-{container_id}.scope/
├── cgroup.procs
├── memory.max          # Set via --memory
├── cpu.max             # Set via --cpus
├── pids.max            # Set via --pids-limit
└── io.max              # Set via --device-write-bps
```

**Example:** `docker run --memory=512m --cpus=1.5 --pids-limit=100 nginx`

Translates to:
```bash
echo "512M" > memory.max
echo "150000 100000" > cpu.max   # 1.5 cores
echo "100" > pids.max
```

### 2. **Kubernetes Pod QoS**

Kubernetes maps QoS classes to cgroups:

**Guaranteed:**
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```
→ Sets `memory.min=1Gi` (hard protection)

**Burstable:**
```yaml
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "1Gi"
```
→ Sets `memory.low=512Mi`, `memory.max=1Gi`

**BestEffort:** No limits, lowest priority

### 3. **Database Workload Isolation**

```bash
# Setup
PGDATA_CGROUP="/sys/fs/cgroup/postgres"
mkdir -p $PGDATA_CGROUP

# Reserve 50% memory for PostgreSQL
TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
PG_MEM=$((TOTAL_MEM / 2 * 1024))  # Convert to bytes
echo $PG_MEM > $PGDATA_CGROUP/memory.min

# High CPU priority
echo 500 > $PGDATA_CGROUP/cpu.weight

# Prioritize I/O
echo "8:0 500" > $PGDATA_CGROUP/io.weight

# Add PostgreSQL processes
pgrep postgres | while read pid; do
    echo $pid > $PGDATA_CGROUP/cgroup.procs
done
```

### 4. **Batch Job Throttling**

```bash
# Create cgroup for batch jobs
BATCH="/sys/fs/cgroup/batch"
mkdir -p $BATCH

# Low priority, use only idle CPU
echo 10 > $BATCH/cpu.weight
echo "10000 100000" > $BATCH/cpu.max    # Max 10% of one core

# Run batch job
echo $$ > $BATCH/cgroup.procs
./long_running_batch_job
```

---

## XI. Security Implications

### 1. **Privilege Escalation Risks**

**Attack:** User creates cgroup, sets high limits, spawns resource-hungry process

**Mitigation:**
```bash
# Delegate with hard upper bounds
echo "512M" > /sys/fs/cgroup/user-1000/memory.max
chown 1000:1000 /sys/fs/cgroup/user-1000
# User can subdivide 512M but not exceed it
```

### 2. **Information Disclosure**

cgroup files reveal:
- Process relationships
- Resource usage patterns
- Application structure

**Mitigation:** Use namespaces to hide cgroup filesystem

### 3. **DoS via cgroup Creation**

**Attack:** Create thousands of cgroups to exhaust kernel memory

**Mitigation:**
```bash
# Kernel parameter (requires v2)
echo 1000 > /sys/fs/cgroup/cgroup.max.descendants
echo 2000 > /sys/fs/cgroup/cgroup.max.depth
```

---

## XII. Future Directions

### 1. **cgroups v3?**

Not planned, but ongoing v2 improvements:
- Better NUMA awareness
- Enhanced PSI metrics
- Finer-grained I/O control

### 2. **eBPF Integration**

Growing trend: Use BPF programs for:
- Custom controllers
- Policy enforcement
- Real-time monitoring

### 3. **Confidential Computing**

cgroups for SGX enclaves, TDX trust domains

---

## XIII. Mental Models for Mastery

### Model 1: **Tree of Constraints**

Think of cgroups as a tree where:
- Each node is a "budget" that can be subdivided
- Children compete for parent's budget
- Leaf processes consume from their node's budget

### Model 2: **Accounting vs Enforcement**

- **Accounting:** Measuring what happened (always on)
- **Enforcement:** Preventing excess (configurable)

Memory controller does both. CPU controller focuses on scheduling (enforcement via shares/weight).

### Model 3: **Push vs Pull**

- **Push:** Set limits, kernel enforces (memory.max)
- **Pull:** Set targets, kernel tries to meet (memory.low, best-effort)

### Model 4: **Pressure as Signal**

PSI is a **leading indicator**:
- High `some` pressure → Approaching limit
- High `full` pressure → Already throttled

Use PSI for **predictive scaling** before hitting hard limits.

---

## XIV. The Path to 1% Mastery

To truly master cgroups at a world-class level:

1. **Kernel Source Deep-Dive**
   - Read `kernel/cgroup/` implementation
   - Understand `css_set` (cgroup subsystem state) data structure
   - Study how controllers hook into scheduler/mm/block layer

2. **Build a Mini-Container Runtime**
   - Combine cgroups + namespaces + seccomp
   - Implement full resource isolation
   - Study runc/containerd source

3. **Performance Tuning**
   - Benchmark cgroup overhead
   - Optimize for your workload (CPU-bound vs I/O-bound)
   - Measure PSI metrics under load

4. **Production Debugging**
   - Analyze real OOM kills
   - Trace CPU throttling events
   - Debug memory leaks using `memory.stat`

5. **Contribute to Projects**
   - Submit patches to systemd
   - Improve container runtime cgroup handling
   - Write eBPF-based cgroup monitoring tools

---

## Closing Wisdom

cgroups are deceptively simple on the surface—just files in `/sys/fs/cgroup`. But mastering them requires understanding:

- **Kernel internals** (scheduler, memory management, I/O)
- **Performance implications** (overhead, scalability)
- **Security boundaries** (delegation, isolation)
- **Real-world systems** (systemd, Kubernetes, Docker)

The true expert doesn't just set `memory.max`—they understand the kernel's page reclaim algorithm, know when to use `memory.low` vs `memory.min`, can debug why a cgroup is OOM-killing when it shouldn't, and can design hierarchies that maximize both isolation and efficiency.

**Your next steps:**
1. Boot a VM, experiment with every controller
2. Implement a production-ready cgroup manager in Rust or Go
3. Read the kernel documentation: `Documentation/admin-guide/cgroup-v2.rst`
4. Study how Kubernetes sets up cgroups for Pods
5. Write an eBPF tracer for cgroup events

You're building toward 1%—this is the foundation of modern infrastructure. Master it completely.