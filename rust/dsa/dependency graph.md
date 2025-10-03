use std::collections::{HashMap, HashSet, VecDeque};
use std::fmt::Display;
use std::hash::Hash;

/// A directed graph representing dependencies between nodes
#[derive(Debug, Clone)]
pub struct DependencyGraph<T: Eq + Hash + Clone> {
    /// Maps each node to its dependencies (edges pointing TO this node)
    dependencies: HashMap<T, HashSet<T>>,
    /// Maps each node to its dependents (edges pointing FROM this node)
    dependents: HashMap<T, HashSet<T>>,
}

impl<T: Eq + Hash + Clone> DependencyGraph<T> {
    /// Creates a new empty dependency graph
    pub fn new() -> Self {
        Self {
            dependencies: HashMap::new(),
            dependents: HashMap::new(),
        }
    }

    /// Adds a node to the graph
    pub fn add_node(&mut self, node: T) {
        self.dependencies.entry(node.clone()).or_insert_with(HashSet::new);
        self.dependents.entry(node).or_insert_with(HashSet::new);
    }

    /// Adds a dependency edge: `from` depends on `to`
    /// This means `to` must be processed before `from`
    pub fn add_dependency(&mut self, from: T, to: T) {
        self.add_node(from.clone());
        self.add_node(to.clone());
        
        self.dependencies.get_mut(&from).unwrap().insert(to.clone());
        self.dependents.get_mut(&to).unwrap().insert(from);
    }

    /// Returns all direct dependencies of a node
    pub fn get_dependencies(&self, node: &T) -> Option<&HashSet<T>> {
        self.dependencies.get(node)
    }

    /// Returns all nodes that depend on this node
    pub fn get_dependents(&self, node: &T) -> Option<&HashSet<T>> {
        self.dependents.get(node)
    }

    /// Returns all nodes in the graph
    pub fn nodes(&self) -> Vec<T> {
        self.dependencies.keys().cloned().collect()
    }

    /// Checks if the graph contains a cycle using DFS
    pub fn has_cycle(&self) -> bool {
        let mut visited = HashSet::new();
        let mut rec_stack = HashSet::new();

        for node in self.dependencies.keys() {
            if !visited.contains(node) {
                if self.has_cycle_util(node, &mut visited, &mut rec_stack) {
                    return true;
                }
            }
        }
        false
    }

    fn has_cycle_util(
        &self,
        node: &T,
        visited: &mut HashSet<T>,
        rec_stack: &mut HashSet<T>,
    ) -> bool {
        visited.insert(node.clone());
        rec_stack.insert(node.clone());

        if let Some(deps) = self.dependencies.get(node) {
            for dep in deps {
                if !visited.contains(dep) {
                    if self.has_cycle_util(dep, visited, rec_stack) {
                        return true;
                    }
                } else if rec_stack.contains(dep) {
                    return true;
                }
            }
        }

        rec_stack.remove(node);
        false
    }

    /// Finds a cycle in the graph if one exists
    pub fn find_cycle(&self) -> Option<Vec<T>> {
        let mut visited = HashSet::new();
        let mut rec_stack = HashSet::new();
        let mut path = Vec::new();

        for node in self.dependencies.keys() {
            if !visited.contains(node) {
                if let Some(cycle) = self.find_cycle_util(
                    node,
                    &mut visited,
                    &mut rec_stack,
                    &mut path,
                ) {
                    return Some(cycle);
                }
            }
        }
        None
    }

    fn find_cycle_util(
        &self,
        node: &T,
        visited: &mut HashSet<T>,
        rec_stack: &mut HashSet<T>,
        path: &mut Vec<T>,
    ) -> Option<Vec<T>> {
        visited.insert(node.clone());
        rec_stack.insert(node.clone());
        path.push(node.clone());

        if let Some(deps) = self.dependencies.get(node) {
            for dep in deps {
                if !visited.contains(dep) {
                    if let Some(cycle) = self.find_cycle_util(dep, visited, rec_stack, path) {
                        return Some(cycle);
                    }
                } else if rec_stack.contains(dep) {
                    // Found a cycle - extract it from the path
                    let cycle_start = path.iter().position(|n| n == dep).unwrap();
                    let mut cycle = path[cycle_start..].to_vec();
                    cycle.push(dep.clone());
                    return Some(cycle);
                }
            }
        }

        rec_stack.remove(node);
        path.pop();
        None
    }

    /// Performs topological sort using Kahn's algorithm
    /// Returns None if the graph has a cycle
    pub fn topological_sort(&self) -> Option<Vec<T>> {
        // Calculate in-degrees
        let mut in_degree: HashMap<T, usize> = HashMap::new();
        for node in self.dependencies.keys() {
            in_degree.insert(node.clone(), 0);
        }
        for deps in self.dependencies.values() {
            for dep in deps {
                *in_degree.get_mut(dep).unwrap() += 1;
            }
        }

        // Queue nodes with no dependencies
        let mut queue: VecDeque<T> = in_degree
            .iter()
            .filter(|(_, &degree)| degree == 0)
            .map(|(node, _)| node.clone())
            .collect();

        let mut result = Vec::new();

        while let Some(node) = queue.pop_front() {
            result.push(node.clone());

            // For each dependent of this node
            if let Some(dependents) = self.dependents.get(&node) {
                for dependent in dependents {
                    let degree = in_degree.get_mut(dependent).unwrap();
                    *degree -= 1;
                    if *degree == 0 {
                        queue.push_back(dependent.clone());
                    }
                }
            }
        }

        // If we couldn't process all nodes, there's a cycle
        if result.len() != self.dependencies.len() {
            None
        } else {
            Some(result)
        }
    }

    /// Returns the transitive closure of dependencies for a node
    /// (all nodes that this node depends on, directly or indirectly)
    pub fn transitive_dependencies(&self, node: &T) -> HashSet<T> {
        let mut result = HashSet::new();
        let mut stack = vec![node.clone()];

        while let Some(current) = stack.pop() {
            if let Some(deps) = self.dependencies.get(&current) {
                for dep in deps {
                    if result.insert(dep.clone()) {
                        stack.push(dep.clone());
                    }
                }
            }
        }

        result
    }

    /// Returns all nodes that transitively depend on this node
    pub fn transitive_dependents(&self, node: &T) -> HashSet<T> {
        let mut result = HashSet::new();
        let mut stack = vec![node.clone()];

        while let Some(current) = stack.pop() {
            if let Some(deps) = self.dependents.get(&current) {
                for dep in deps {
                    if result.insert(dep.clone()) {
                        stack.push(dep.clone());
                    }
                }
            }
        }

        result
    }

    /// Returns nodes in layers where each layer can be processed in parallel
    pub fn parallel_layers(&self) -> Option<Vec<Vec<T>>> {
        let mut layers = Vec::new();
        let mut in_degree: HashMap<T, usize> = HashMap::new();
        
        for node in self.dependencies.keys() {
            in_degree.insert(node.clone(), 0);
        }
        for deps in self.dependencies.values() {
            for dep in deps {
                *in_degree.get_mut(dep).unwrap() += 1;
            }
        }

        let mut processed = 0;
        let total = self.dependencies.len();

        while processed < total {
            let current_layer: Vec<T> = in_degree
                .iter()
                .filter(|(_, &degree)| degree == 0)
                .map(|(node, _)| node.clone())
                .collect();

            if current_layer.is_empty() {
                return None; // Cycle detected
            }

            for node in &current_layer {
                in_degree.remove(node);
                if let Some(dependents) = self.dependents.get(node) {
                    for dependent in dependents {
                        if let Some(degree) = in_degree.get_mut(dependent) {
                            *degree -= 1;
                        }
                    }
                }
            }

            processed += current_layer.len();
            layers.push(current_layer);
        }

        Some(layers)
    }

    /// Removes a node and all its connections
    pub fn remove_node(&mut self, node: &T) {
        // Remove from dependencies
        if let Some(deps) = self.dependencies.remove(node) {
            for dep in deps {
                if let Some(dependents) = self.dependents.get_mut(&dep) {
                    dependents.remove(node);
                }
            }
        }

        // Remove from dependents
        if let Some(deps) = self.dependents.remove(node) {
            for dep in deps {
                if let Some(dependencies) = self.dependencies.get_mut(&dep) {
                    dependencies.remove(node);
                }
            }
        }
    }
}

impl<T: Eq + Hash + Clone + Display> DependencyGraph<T> {
    /// Prints the graph in DOT format for visualization
    pub fn to_dot(&self) -> String {
        let mut result = String::from("digraph Dependencies {\n");
        
        for (node, deps) in &self.dependencies {
            for dep in deps {
                result.push_str(&format!("  \"{}\" -> \"{}\";\n", node, dep));
            }
        }
        
        result.push_str("}\n");
        result
    }
}

// Example usage and tests
fn main() {
    println!("=== Dependency Graph Examples ===\n");

    // Example 1: Simple build system
    example_build_system();
    
    // Example 2: Package manager
    example_package_manager();
    
    // Example 3: Task scheduler
    example_task_scheduler();
    
    // Example 4: Cycle detection
    example_cycle_detection();
}

fn example_build_system() {
    println!("1. Build System Example");
    println!("------------------------");
    
    let mut graph = DependencyGraph::new();
    
    // Add build dependencies
    graph.add_dependency("main.o", "main.c");
    graph.add_dependency("main.o", "header.h");
    graph.add_dependency("util.o", "util.c");
    graph.add_dependency("util.o", "header.h");
    graph.add_dependency("program", "main.o");
    graph.add_dependency("program", "util.o");
    
    println!("Build order:");
    if let Some(order) = graph.topological_sort() {
        for (i, item) in order.iter().enumerate() {
            println!("  {}. {}", i + 1, item);
        }
    }
    
    println!("\nParallel build layers:");
    if let Some(layers) = graph.parallel_layers() {
        for (i, layer) in layers.iter().enumerate() {
            println!("  Layer {}: {:?}", i + 1, layer);
        }
    }
    println!();
}

fn example_package_manager() {
    println!("2. Package Manager Example");
    println!("--------------------------");
    
    let mut graph = DependencyGraph::new();
    
    // Package dependencies
    graph.add_dependency("web-app", "web-framework");
    graph.add_dependency("web-app", "database-driver");
    graph.add_dependency("web-framework", "http-server");
    graph.add_dependency("web-framework", "template-engine");
    graph.add_dependency("database-driver", "connection-pool");
    graph.add_dependency("http-server", "socket-lib");
    
    let app = "web-app";
    println!("All dependencies of '{}':", app);
    let deps = graph.transitive_dependencies(&app.to_string());
    for dep in &deps {
        println!("  - {}", dep);
    }
    
    println!("\nInstallation order:");
    if let Some(order) = graph.topological_sort() {
        for (i, pkg) in order.iter().enumerate() {
            println!("  {}. {}", i + 1, pkg);
        }
    }
    println!();
}

fn example_task_scheduler() {
    println!("3. Task Scheduler Example");
    println!("-------------------------");
    
    let mut graph = DependencyGraph::new();
    
    // Task dependencies
    graph.add_dependency("deploy", "test");
    graph.add_dependency("deploy", "build");
    graph.add_dependency("test", "compile");
    graph.add_dependency("build", "compile");
    graph.add_dependency("compile", "fetch-deps");
    
    println!("Tasks can run in parallel:");
    if let Some(layers) = graph.parallel_layers() {
        for (i, layer) in layers.iter().enumerate() {
            println!("  Stage {}: {}", i + 1, layer.join(", "));
        }
    }
    
    println!("\nWhat needs to run if 'compile' changes?");
    let affected = graph.transitive_dependents(&"compile".to_string());
    for task in &affected {
        println!("  - {}", task);
    }
    println!();
}

fn example_cycle_detection() {
    println!("4. Cycle Detection Example");
    println!("--------------------------");
    
    let mut graph = DependencyGraph::new();
    
    // Create a cycle: A -> B -> C -> A
    graph.add_dependency("A", "B");
    graph.add_dependency("B", "C");
    graph.add_dependency("C", "A");
    
    if graph.has_cycle() {
        println!("Cycle detected!");
        if let Some(cycle) = graph.find_cycle() {
            println!("Cycle path: {}", cycle.join(" -> "));
        }
    } else {
        println!("No cycle found");
    }
    
    println!("\nTopological sort result:");
    match graph.topological_sort() {
        Some(order) => println!("  Order: {:?}", order),
        None => println!("  Cannot sort - cycle exists!"),
    }
    println!();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_dependency() {
        let mut graph = DependencyGraph::new();
        graph.add_dependency("A", "B");
        
        assert_eq!(graph.get_dependencies(&"A".to_string()).unwrap().len(), 1);
        assert_eq!(graph.get_dependents(&"B".to_string()).unwrap().len(), 1);
    }

    #[test]
    fn test_topological_sort() {
        let mut graph = DependencyGraph::new();
        graph.add_dependency("A", "B");
        graph.add_dependency("B", "C");
        
        let sorted = graph.topological_sort().unwrap();
        let pos_c = sorted.iter().position(|x| x == "C").unwrap();
        let pos_b = sorted.iter().position(|x| x == "B").unwrap();
        let pos_a = sorted.iter().position(|x| x == "A").unwrap();
        
        assert!(pos_c < pos_b);
        assert!(pos_b < pos_a);
    }

    #[test]
    fn test_cycle_detection() {
        let mut graph = DependencyGraph::new();
        graph.add_dependency("A", "B");
        graph.add_dependency("B", "C");
        graph.add_dependency("C", "A");
        
        assert!(graph.has_cycle());
        assert!(graph.topological_sort().is_none());
    }

    #[test]
    fn test_transitive_dependencies() {
        let mut graph = DependencyGraph::new();
        graph.add_dependency("A", "B");
        graph.add_dependency("B", "C");
        graph.add_dependency("C", "D");
        
        let deps = graph.transitive_dependencies(&"A".to_string());
        assert_eq!(deps.len(), 3);
        assert!(deps.contains("B"));
        assert!(deps.contains("C"));
        assert!(deps.contains("D"));
    }

    #[test]
    fn test_parallel_layers() {
        let mut graph = DependencyGraph::new();
        graph.add_dependency("D", "B");
        graph.add_dependency("D", "C");
        graph.add_dependency("B", "A");
        graph.add_dependency("C", "A");
        
        let layers = graph.parallel_layers().unwrap();
        assert_eq!(layers.len(), 3);
        assert_eq!(layers[0].len(), 1); // A
        assert_eq!(layers[1].len(), 2); // B and C
        assert_eq!(layers[2].len(), 1); // D
    }
}

# Comprehensive Guide to Dependency Graphs in Rust

I'll create a complete guide with full implementations covering dependency graphs, topological sorting, cycle detection, and practical applications.

I've created a comprehensive dependency graph implementation in Rust! Here's what's included:

## Key Features

### 1. **Core Functionality**
- Add nodes and dependency edges
- Query dependencies and dependents
- Bidirectional tracking for efficient lookups

### 2. **Cycle Detection**
- `has_cycle()` - Fast boolean check using DFS
- `find_cycle()` - Returns the actual cycle path for debugging

### 3. **Topological Sorting**
- Kahn's algorithm implementation
- Returns proper ordering for dependency resolution
- Returns `None` if cycles exist

### 4. **Advanced Operations**
- **Transitive dependencies** - Find all indirect dependencies
- **Transitive dependents** - Find all nodes affected by changes
- **Parallel layers** - Group nodes that can be processed simultaneously
- **Node removal** - Clean deletion with connection updates

### 5. **Practical Examples**
The code includes four real-world scenarios:
- **Build system** - Compile order for source files
- **Package manager** - Dependency resolution
- **Task scheduler** - Parallel execution planning
- **Cycle detection** - Circular dependency handling

## Usage

To run the examples:
```bash
cargo run
```

To run the tests:
```bash
cargo test
```

## Time Complexity
- Add dependency: O(1)
- Topological sort: O(V + E)
- Cycle detection: O(V + E)
- Transitive dependencies: O(V + E)
- Parallel layers: O(V + E)

The implementation uses HashMaps and HashSets for efficient lookups and is generic over any type that implements `Eq + Hash + Clone`.