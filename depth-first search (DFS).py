Depth-First Search (DFS) is a graph traversal algorithm that explores as far as possible along each branch before backtracking. It follows a "go deep, then go wide" strategy, using a stack data structure (either explicitly or through recursion).

## How DFS Works

DFS starts at a root node and explores each branch completely before moving to the next branch. It uses a stack to keep track of nodes to visit next.

## Python Implementation

Here's a comprehensive implementation with both recursive and iterative approaches:## Use Cases and Real-World Applications

### 1. **File System Traversal**
- **Usage**: Finding files, calculating directory sizes, backup operations
- **Example**: Your IDE searching for all Python files in a project directory
- **Security Note**: Always validate file paths to prevent directory traversal attacks

### 2. **Web Crawling**
- **Usage**: Search engines, web scraping, link validation
- **Example**: Google's web crawler discovering new pages
- **Security Note**: Implement rate limiting and respect robots.txt

### 3. **Dependency Resolution**
- **Usage**: Package managers, build systems, import resolution
- **Example**: npm resolving package dependencies during installation
- **Security Note**: Detect circular dependencies to prevent infinite loops

### 4. **Game AI Pathfinding**
- **Usage**: Maze solving, puzzle games, decision trees
- **Example**: AI finding path through a maze or game level
- **Security Note**: Implement depth limits to prevent stack overflow

### 5. **Compiler Design**
- **Usage**: Syntax tree traversal, code generation, optimization
- **Example**: TypeScript compiler analyzing your code structure
- **Security Note**: Validate input to prevent code injection

## Advantages

1. **Memory Efficient**: Uses less memory than BFS (only stores current path)
2. **Simple Implementation**: Easy to implement with recursion
3. **Path Finding**: Natural for finding any path between nodes
4. **Cycle Detection**: Efficient for detecting cycles in directed graphs
5. **Topological Sorting**: Perfect for dependency resolution

## Disadvantages

1. **Not Optimal**: May not find shortest path
2. **Stack Overflow**: Recursive version can cause stack overflow on deep graphs
3. **Infinite Loops**: Can get stuck in infinite loops with cycles (without visited tracking)
4. **Order Dependency**: Result depends on order of neighbor exploration
5. **Poor for Level-Order**: Not suitable when you need level-by-level traversal

## Time and Space Complexity

- **Time Complexity**: O(V + E) where V = vertices, E = edges
- **Space Complexity**: 
  - Recursive: O(V) for call stack + O(V) for visited set
  - Iterative: O(V) for explicit stack + O(V) for visited set

## Limitations

1. **Exponential Paths**: Finding all paths can be exponential in worst case
2. **Memory Usage**: Deep recursion can exhaust stack memory
3. **No Shortest Path**: Doesn't guarantee shortest path in unweighted graphs
4. **Poor Cache Locality**: May have poor cache performance compared to BFS

## When to Use DFS vs BFS

**Use DFS when:**
- You need to explore all possible paths
- Memory is limited
- You're doing backtracking algorithms
- You need topological sorting
- You're detecting cycles

**Use BFS when:**
- You need shortest path in unweighted graphs
- You need level-order traversal
- You want to find nodes at specific distance
- You're doing breadth-first exploration

## Security Considerations

1. **Input Validation**: Always validate graph input to prevent malicious data
2. **Depth Limits**: Set maximum recursion depth to prevent stack overflow attacks
3. **Cycle Detection**: Implement cycle detection to prevent infinite loops
4. **Resource Limits**: Set timeouts and memory limits for large graphs
5. **Path Traversal**: In file system applications, prevent directory traversal attacks

The implementation above includes comprehensive type hints, security considerations, and real-world examples that demonstrate how DFS works internally and its practical applications in your development stack.

from typing import List, Dict, Set, Optional, Callable, Any
from collections import defaultdict, deque
import sys

class Graph:
    """
    Graph implementation supporting both directed and undirected graphs.
    Uses adjacency list representation for memory efficiency.
    """
    
    def __init__(self, directed: bool = False):
        self.graph: Dict[Any, List[Any]] = defaultdict(list)
        self.directed = directed
    
    def add_edge(self, u: Any, v: Any) -> None:
        """Add edge between vertices u and v"""
        self.graph[u].append(v)
        if not self.directed:
            self.graph[v].append(u)
    
    def get_vertices(self) -> Set[Any]:
        """Get all vertices in the graph"""
        vertices = set(self.graph.keys())
        for neighbors in self.graph.values():
            vertices.update(neighbors)
        return vertices

class DFSTraversal:
    """
    Comprehensive DFS implementation with various traversal methods
    """
    
    def __init__(self, graph: Graph):
        self.graph = graph
        self.visited: Set[Any] = set()
        self.path: List[Any] = []
        
    def dfs_recursive(self, start: Any, visit_callback: Optional[Callable] = None) -> List[Any]:
        """
        Recursive DFS implementation
        Time: O(V + E), Space: O(V) for call stack
        """
        self.visited.clear()
        self.path.clear()
        
        def _dfs_helper(vertex: Any) -> None:
            self.visited.add(vertex)
            self.path.append(vertex)
            
            if visit_callback:
                visit_callback(vertex)
            
            # Explore all unvisited neighbors
            for neighbor in self.graph.graph[vertex]:
                if neighbor not in self.visited:
                    _dfs_helper(neighbor)
        
        _dfs_helper(start)
        return self.path.copy()
    
    def dfs_iterative(self, start: Any, visit_callback: Optional[Callable] = None) -> List[Any]:
        """
        Iterative DFS using explicit stack
        Time: O(V + E), Space: O(V) for stack
        Avoids recursion depth limits
        """
        self.visited.clear()
        self.path.clear()
        
        stack = [start]
        
        while stack:
            vertex = stack.pop()
            
            if vertex not in self.visited:
                self.visited.add(vertex)
                self.path.append(vertex)
                
                if visit_callback:
                    visit_callback(vertex)
                
                # Add neighbors to stack in reverse order to maintain left-to-right traversal
                for neighbor in reversed(self.graph.graph[vertex]):
                    if neighbor not in self.visited:
                        stack.append(neighbor)
        
        return self.path.copy()
    
    def dfs_all_paths(self, start: Any, target: Any) -> List[List[Any]]:
        """
        Find all paths from start to target using DFS
        Useful for finding all possible routes
        """
        all_paths = []
        
        def _find_paths(current: Any, path: List[Any], visited: Set[Any]) -> None:
            if current == target:
                all_paths.append(path.copy())
                return
            
            for neighbor in self.graph.graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    _find_paths(neighbor, path, visited)
                    # Backtrack
                    path.pop()
                    visited.remove(neighbor)
        
        visited = {start}
        _find_paths(start, [start], visited)
        return all_paths
    
    def detect_cycle_directed(self) -> bool:
        """
        Detect cycle in directed graph using DFS
        Uses three colors: white (unvisited), gray (processing), black (done)
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = defaultdict(int)
        
        def _has_cycle(vertex: Any) -> bool:
            if colors[vertex] == GRAY:  # Back edge found
                return True
            if colors[vertex] == BLACK:  # Already processed
                return False
            
            colors[vertex] = GRAY
            
            for neighbor in self.graph.graph[vertex]:
                if _has_cycle(neighbor):
                    return True
            
            colors[vertex] = BLACK
            return False
        
        for vertex in self.graph.get_vertices():
            if colors[vertex] == WHITE:
                if _has_cycle(vertex):
                    return True
        return False
    
    def topological_sort(self) -> List[Any]:
        """
        Topological sorting using DFS
        Only works for Directed Acyclic Graphs (DAG)
        """
        if not self.graph.directed:
            raise ValueError("Topological sort only works for directed graphs")
        
        if self.detect_cycle_directed():
            raise ValueError("Graph contains cycle, topological sort not possible")
        
        visited = set()
        stack = []
        
        def _topo_helper(vertex: Any) -> None:
            visited.add(vertex)
            
            for neighbor in self.graph.graph[vertex]:
                if neighbor not in visited:
                    _topo_helper(neighbor)
            
            stack.append(vertex)
        
        for vertex in self.graph.get_vertices():
            if vertex not in visited:
                _topo_helper(vertex)
        
        return stack[::-1]  # Reverse to get correct order

# Real-world examples and use cases
class FileSystemTraversal:
    """
    Real-world example: File system traversal using DFS
    """
    
    def __init__(self):
        self.file_system = defaultdict(list)
    
    def add_directory(self, parent: str, child: str) -> None:
        """Add directory structure"""
        self.file_system[parent].append(child)
    
    def find_files(self, start_dir: str, extension: str) -> List[str]:
        """Find all files with specific extension using DFS"""
        found_files = []
        
        def _search(directory: str) -> None:
            # Process current directory
            if directory.endswith(extension):
                found_files.append(directory)
            
            # Recursively search subdirectories
            for subdir in self.file_system[directory]:
                _search(subdir)
        
        _search(start_dir)
        return found_files

class WebCrawler:
    """
    Real-world example: Web crawler using DFS
    """
    
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.visited_urls = set()
        self.url_graph = defaultdict(list)
    
    def add_link(self, from_url: str, to_url: str) -> None:
        """Add link between pages"""
        self.url_graph[from_url].append(to_url)
    
    def crawl(self, start_url: str) -> List[str]:
        """Crawl website starting from given URL"""
        crawled_pages = []
        
        def _crawl_dfs(url: str, depth: int) -> None:
            if depth > self.max_depth or url in self.visited_urls:
                return
            
            self.visited_urls.add(url)
            crawled_pages.append(url)
            
            # Simulate crawling linked pages
            for linked_url in self.url_graph[url]:
                _crawl_dfs(linked_url, depth + 1)
        
        _crawl_dfs(start_url, 0)
        return crawled_pages

# Example usage and demonstrations
def demonstrate_dfs():
    """Demonstrate various DFS implementations and use cases"""
    
    print("=== Basic DFS Traversal ===")
    
    # Create a sample graph
    graph = Graph(directed=False)
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]
    
    for u, v in edges:
        graph.add_edge(u, v)
    
    dfs = DFSTraversal(graph)
    
    # Recursive DFS
    print("Recursive DFS from vertex 0:")
    recursive_path = dfs.dfs_recursive(0)
    print(f"Path: {recursive_path}")
    
    # Iterative DFS
    print("\nIterative DFS from vertex 0:")
    iterative_path = dfs.dfs_iterative(0)
    print(f"Path: {iterative_path}")
    
    print("\n=== Cycle Detection ===")
    
    # Create directed graph with cycle
    directed_graph = Graph(directed=True)
    directed_edges = [(0, 1), (1, 2), (2, 3), (3, 1)]  # Cycle: 1->2->3->1
    
    for u, v in directed_edges:
        directed_graph.add_edge(u, v)
    
    dfs_directed = DFSTraversal(directed_graph)
    has_cycle = dfs_directed.detect_cycle_directed()
    print(f"Graph has cycle: {has_cycle}")
    
    print("\n=== Topological Sort ===")
    
    # Create DAG for topological sort
    dag = Graph(directed=True)
    dag_edges = [(5, 2), (5, 0), (4, 0), (4, 1), (2, 3), (3, 1)]
    
    for u, v in dag_edges:
        dag.add_edge(u, v)
    
    dfs_dag = DFSTraversal(dag)
    topo_order = dfs_dag.topological_sort()
    print(f"Topological order: {topo_order}")
    
    print("\n=== File System Traversal ===")
    
    file_system = FileSystemTraversal()
    # Build file system structure
    file_system.add_directory("/root", "/root/documents")
    file_system.add_directory("/root", "/root/pictures")
    file_system.add_directory("/root/documents", "/root/documents/file1.txt")
    file_system.add_directory("/root/documents", "/root/documents/file2.py")
    file_system.add_directory("/root/pictures", "/root/pictures/photo.jpg")
    
    python_files = file_system.find_files("/root", ".py")
    print(f"Python files found: {python_files}")
    
    print("\n=== Web Crawler Simulation ===")
    
    crawler = WebCrawler(max_depth=2)
    # Build website structure
    crawler.add_link("homepage.html", "about.html")
    crawler.add_link("homepage.html", "products.html")
    crawler.add_link("about.html", "team.html")
    crawler.add_link("products.html", "product1.html")
    
    crawled = crawler.crawl("homepage.html")
    print(f"Crawled pages: {crawled}")

if __name__ == "__main__":
    demonstrate_dfs()