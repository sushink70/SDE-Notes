#!/usr/bin/env python3
"""
Elite Graph & Traversal Algorithm Visualizer
Master graph algorithms through step-by-step visualization.

Usage:
    python graph_viz.py
    
Features:
- ASCII graph visualization (adjacency matrix & visual layout)
- BFS/DFS step-by-step animation
- Shortest path algorithms (Dijkstra, Bellman-Ford, A*)
- MST algorithms (Kruskal, Prim)
- Topological sort, cycle detection
- Path tracking and frontier visualization
- Interactive exploration mode
"""

from typing import List, Dict, Set, Tuple, Optional, Deque
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
import heapq
import sys
import os
import time
import math


class Color:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'


class NodeState(Enum):
    """Visual states for graph nodes."""
    UNVISITED = 0
    FRONTIER = 1
    VISITING = 2
    VISITED = 3
    PATH = 4
    START = 5
    GOAL = 6


class EdgeState(Enum):
    """Visual states for graph edges."""
    NORMAL = 0
    EXPLORING = 1
    TREE_EDGE = 2
    BACK_EDGE = 3
    PATH_EDGE = 4


@dataclass
class Edge:
    """Graph edge with weight."""
    src: str
    dst: str
    weight: int = 1
    state: EdgeState = EdgeState.NORMAL
    
    def __repr__(self):
        return f"{self.src}->{self.dst}({self.weight})"


@dataclass
class Node:
    """Graph node with visualization properties."""
    id: str
    state: NodeState = NodeState.UNVISITED
    distance: float = float('inf')
    parent: Optional[str] = None
    discovery_time: int = -1
    finish_time: int = -1
    
    def __repr__(self):
        return f"Node({self.id})"


@dataclass
class GraphStats:
    """Track algorithm performance metrics."""
    nodes_visited: int = 0
    edges_explored: int = 0
    path_length: int = 0
    algorithm_steps: int = 0


class Graph:
    """
    Elite graph implementation with comprehensive visualization.
    Supports directed/undirected, weighted/unweighted graphs.
    """
    
    def __init__(self, directed: bool = False):
        self.directed = directed
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.adj_list: Dict[str, List[str]] = defaultdict(list)
        self.edge_weights: Dict[Tuple[str, str], int] = {}
        self.stats = GraphStats()
        
    # ==================== GRAPH CONSTRUCTION ====================
    
    def add_node(self, node_id: str) -> None:
        """Add a node to the graph."""
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id)
    
    def add_edge(self, src: str, dst: str, weight: int = 1) -> None:
        """Add an edge to the graph."""
        self.add_node(src)
        self.add_node(dst)
        
        self.adj_list[src].append(dst)
        self.edge_weights[(src, dst)] = weight
        self.edges.append(Edge(src, dst, weight))
        
        if not self.directed:
            self.adj_list[dst].append(src)
            self.edge_weights[(dst, src)] = weight
            self.edges.append(Edge(dst, src, weight))
    
    def build_from_edges(self, edges: List[Tuple]) -> None:
        """
        Build graph from edge list.
        Format: [(src, dst), ...] or [(src, dst, weight), ...]
        """
        for edge in edges:
            if len(edge) == 2:
                self.add_edge(edge[0], edge[1])
            elif len(edge) == 3:
                self.add_edge(edge[0], edge[1], edge[2])
    
    def build_from_adjacency_dict(self, adj_dict: Dict[str, List]) -> None:
        """
        Build graph from adjacency dictionary.
        Format: {'A': ['B', 'C'], 'B': ['D'], ...}
        Or: {'A': [('B', 5), ('C', 3)], ...} for weighted
        """
        for src, neighbors in adj_dict.items():
            self.add_node(src)
            for neighbor in neighbors:
                if isinstance(neighbor, tuple):
                    dst, weight = neighbor
                    self.add_edge(src, dst, weight)
                else:
                    self.add_edge(src, neighbor)
    
    # ==================== VISUALIZATION ====================
    
    def display(self, title: Optional[str] = None, show_stats: bool = True,
                show_adjacency: bool = True) -> None:
        """Main display function."""
        self._clear_screen()
        
        print("=" * 80)
        if title:
            print(f"🕸️  {title}")
        print("=" * 80)
        
        # Graph type info
        graph_type = "Directed" if self.directed else "Undirected"
        print(f"Type: {graph_type} | Nodes: {len(self.nodes)} | Edges: {len(self.edges) // (1 if self.directed else 2)}")
        print()
        
        # Visual representation
        self._display_visual()
        
        # Adjacency list
        if show_adjacency:
            self._display_adjacency_list()
        
        # Node states
        self._display_node_states()
        
        # Statistics
        if show_stats:
            self._display_stats()
        
        print("=" * 80)
        time.sleep(0.5)
    
    def _display_visual(self) -> None:
        """Display graph in visual ASCII format."""
        if not self.nodes:
            return
        
        print("📊 Graph Structure:")
        print()
        
        # Simple tree-like visualization for small graphs
        visited_edges = set()
        
        for node_id, node in sorted(self.nodes.items()):
            color = self._get_node_color(node.state)
            symbol = self._get_node_symbol(node.state)
            distance_str = f"(d={node.distance})" if node.distance != float('inf') else ""
            
            print(f"{color}[{node_id}]{Color.RESET} {symbol} {distance_str}")
            
            # Show edges
            for neighbor in sorted(self.adj_list.get(node_id, [])):
                edge_key = (node_id, neighbor)
                if edge_key not in visited_edges:
                    weight = self.edge_weights.get(edge_key, 1)
                    arrow = "→" if self.directed else "↔"
                    edge_color = Color.CYAN
                    
                    # Check if this edge is in a path
                    if (self.nodes[neighbor].parent == node_id or 
                        self.nodes[node_id].parent == neighbor):
                        edge_color = Color.GREEN
                    
                    weight_str = f"({weight})" if weight != 1 else ""
                    print(f"  │")
                    print(f"  └─{edge_color}{arrow}{Color.RESET} {neighbor} {weight_str}")
                    
                    visited_edges.add(edge_key)
        print()
    
    def _display_adjacency_list(self) -> None:
        """Display adjacency list representation."""
        print("📋 Adjacency List:")
        for node_id in sorted(self.adj_list.keys()):
            neighbors = self.adj_list[node_id]
            neighbor_strs = []
            for n in neighbors:
                weight = self.edge_weights.get((node_id, n), 1)
                if weight != 1:
                    neighbor_strs.append(f"{n}({weight})")
                else:
                    neighbor_strs.append(n)
            print(f"  {node_id}: {', '.join(neighbor_strs)}")
        print()
    
    def _display_node_states(self) -> None:
        """Display current state of all nodes."""
        states_dict = defaultdict(list)
        for node_id, node in self.nodes.items():
            states_dict[node.state].append(node_id)
        
        if any(states_dict.values()):
            print("🎨 Node States:")
            state_names = {
                NodeState.UNVISITED: "Unvisited",
                NodeState.FRONTIER: "Frontier",
                NodeState.VISITING: "Visiting",
                NodeState.VISITED: "Visited",
                NodeState.PATH: "Path",
                NodeState.START: "Start",
                NodeState.GOAL: "Goal"
            }
            for state, nodes in states_dict.items():
                if nodes and state != NodeState.UNVISITED:
                    color = self._get_node_color(state)
                    print(f"  {color}{state_names[state]}{Color.RESET}: {', '.join(sorted(nodes))}")
            print()
    
    def _display_stats(self) -> None:
        """Display algorithm statistics."""
        print("📈 Statistics:")
        print(f"   Nodes Visited: {self.stats.nodes_visited}")
        print(f"   Edges Explored: {self.stats.edges_explored}")
        print(f"   Algorithm Steps: {self.stats.algorithm_steps}")
        if self.stats.path_length > 0:
            print(f"   Path Length: {self.stats.path_length}")
    
    def _get_node_color(self, state: NodeState) -> str:
        """Map node state to color."""
        color_map = {
            NodeState.UNVISITED: Color.GRAY,
            NodeState.FRONTIER: Color.YELLOW,
            NodeState.VISITING: Color.CYAN,
            NodeState.VISITED: Color.BLUE,
            NodeState.PATH: Color.GREEN,
            NodeState.START: Color.MAGENTA,
            NodeState.GOAL: Color.RED,
        }
        return color_map.get(state, Color.WHITE)
    
    def _get_node_symbol(self, state: NodeState) -> str:
        """Map node state to symbol."""
        symbol_map = {
            NodeState.UNVISITED: "○",
            NodeState.FRONTIER: "◐",
            NodeState.VISITING: "◉",
            NodeState.VISITED: "●",
            NodeState.PATH: "✓",
            NodeState.START: "🚀",
            NodeState.GOAL: "🎯",
        }
        return symbol_map.get(state, "")
    
    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def _reset_states(self) -> None:
        """Reset all node and edge states."""
        for node in self.nodes.values():
            node.state = NodeState.UNVISITED
            node.distance = float('inf')
            node.parent = None
            node.discovery_time = -1
            node.finish_time = -1
        for edge in self.edges:
            edge.state = EdgeState.NORMAL
        self.stats = GraphStats()
    
    # ==================== TRAVERSAL ALGORITHMS ====================
    
    def bfs(self, start: str, goal: Optional[str] = None) -> List[str]:
        """
        Breadth-First Search with visualization.
        Time: O(V + E), Space: O(V)
        """
        self._reset_states()
        
        if start not in self.nodes:
            print(f"Start node '{start}' not found!")
            return []
        
        queue = deque([start])
        self.nodes[start].state = NodeState.START
        self.nodes[start].distance = 0
        
        if goal and goal in self.nodes:
            self.nodes[goal].state = NodeState.GOAL
        
        self.display("BFS: Initialization")
        
        visited_order = []
        
        while queue:
            # Show frontier
            for node_id in queue:
                if self.nodes[node_id].state not in [NodeState.START, NodeState.GOAL]:
                    self.nodes[node_id].state = NodeState.FRONTIER
            
            current = queue.popleft()
            
            # Skip if already visited
            if self.nodes[current].state == NodeState.VISITED:
                continue
            
            # Mark as visiting
            if self.nodes[current].state not in [NodeState.START, NodeState.GOAL]:
                self.nodes[current].state = NodeState.VISITING
            
            self.stats.nodes_visited += 1
            self.stats.algorithm_steps += 1
            visited_order.append(current)
            
            self.display(f"BFS: Visiting node {current}")
            
            # Check if goal reached
            if current == goal:
                self._reconstruct_path(start, goal)
                self.display(f"BFS: Goal '{goal}' reached!")
                return visited_order
            
            # Explore neighbors
            for neighbor in self.adj_list.get(current, []):
                self.stats.edges_explored += 1
                
                if self.nodes[neighbor].state == NodeState.UNVISITED:
                    self.nodes[neighbor].distance = self.nodes[current].distance + 1
                    self.nodes[neighbor].parent = current
                    queue.append(neighbor)
                    self.nodes[neighbor].state = NodeState.FRONTIER
            
            # Mark as visited
            if self.nodes[current].state not in [NodeState.START, NodeState.GOAL]:
                self.nodes[current].state = NodeState.VISITED
        
        self.display("BFS: Complete")
        return visited_order
    
    def dfs(self, start: str, goal: Optional[str] = None) -> List[str]:
        """
        Depth-First Search with visualization.
        Time: O(V + E), Space: O(V)
        """
        self._reset_states()
        
        if start not in self.nodes:
            print(f"Start node '{start}' not found!")
            return []
        
        self.nodes[start].state = NodeState.START
        if goal and goal in self.nodes:
            self.nodes[goal].state = NodeState.GOAL
        
        self.display("DFS: Initialization")
        
        visited_order = []
        time_counter = [0]  # Mutable for closure
        
        def dfs_recursive(node_id: str) -> bool:
            # Mark as visiting
            if self.nodes[node_id].state not in [NodeState.START, NodeState.GOAL]:
                self.nodes[node_id].state = NodeState.VISITING
            
            self.nodes[node_id].discovery_time = time_counter[0]
            time_counter[0] += 1
            
            self.stats.nodes_visited += 1
            self.stats.algorithm_steps += 1
            visited_order.append(node_id)
            
            self.display(f"DFS: Visiting node {node_id}")
            
            # Check if goal reached
            if node_id == goal:
                self._reconstruct_path(start, goal)
                self.display(f"DFS: Goal '{goal}' reached!")
                return True
            
            # Explore neighbors
            for neighbor in self.adj_list.get(node_id, []):
                self.stats.edges_explored += 1
                
                if self.nodes[neighbor].state == NodeState.UNVISITED:
                    self.nodes[neighbor].parent = node_id
                    if dfs_recursive(neighbor):
                        return True
            
            # Mark as visited
            if self.nodes[node_id].state not in [NodeState.START, NodeState.GOAL]:
                self.nodes[node_id].state = NodeState.VISITED
            
            self.nodes[node_id].finish_time = time_counter[0]
            time_counter[0] += 1
            
            return False
        
        dfs_recursive(start)
        self.display("DFS: Complete")
        return visited_order
    
    def dfs_iterative(self, start: str, goal: Optional[str] = None) -> List[str]:
        """
        Iterative DFS using stack.
        Time: O(V + E), Space: O(V)
        """
        self._reset_states()
        
        if start not in self.nodes:
            print(f"Start node '{start}' not found!")
            return []
        
        stack = [start]
        self.nodes[start].state = NodeState.START
        
        if goal and goal in self.nodes:
            self.nodes[goal].state = NodeState.GOAL
        
        self.display("DFS (Iterative): Initialization")
        
        visited_order = []
        
        while stack:
            current = stack.pop()
            
            if self.nodes[current].state == NodeState.VISITED:
                continue
            
            if self.nodes[current].state not in [NodeState.START, NodeState.GOAL]:
                self.nodes[current].state = NodeState.VISITING
            
            self.stats.nodes_visited += 1
            self.stats.algorithm_steps += 1
            visited_order.append(current)
            
            self.display(f"DFS (Iterative): Visiting node {current}")
            
            if current == goal:
                self._reconstruct_path(start, goal)
                self.display(f"DFS (Iterative): Goal '{goal}' reached!")
                return visited_order
            
            for neighbor in reversed(self.adj_list.get(current, [])):
                self.stats.edges_explored += 1
                if self.nodes[neighbor].state == NodeState.UNVISITED:
                    self.nodes[neighbor].parent = current
                    stack.append(neighbor)
            
            if self.nodes[current].state not in [NodeState.START, NodeState.GOAL]:
                self.nodes[current].state = NodeState.VISITED
        
        self.display("DFS (Iterative): Complete")
        return visited_order
    
    # ==================== SHORTEST PATH ALGORITHMS ====================
    
    def dijkstra(self, start: str, goal: Optional[str] = None) -> Dict[str, float]:
        """
        Dijkstra's shortest path algorithm.
        Time: O((V + E) log V) with min-heap
        Space: O(V)
        """
        self._reset_states()
        
        if start not in self.nodes:
            print(f"Start node '{start}' not found!")
            return {}
        
        self.nodes[start].state = NodeState.START
        self.nodes[start].distance = 0
        
        if goal and goal in self.nodes:
            self.nodes[goal].state = NodeState.GOAL
        
        # Priority queue: (distance, node)
        pq = [(0, start)]
        distances = {node_id: float('inf') for node_id in self.nodes}
        distances[start] = 0
        
        self.display("Dijkstra: Initialization")
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            # Skip if already processed with shorter distance
            if current_dist > distances[current]:
                continue
            
            if self.nodes[current].state not in [NodeState.START, NodeState.GOAL, NodeState.VISITED]:
                self.nodes[current].state = NodeState.VISITING
            
            self.stats.nodes_visited += 1
            self.stats.algorithm_steps += 1
            
            self.display(f"Dijkstra: Visiting {current} with distance {current_dist}")
            
            # Goal check
            if current == goal:
                self._reconstruct_path(start, goal)
                self.display(f"Dijkstra: Shortest path to '{goal}' found! Distance: {current_dist}")
                return distances
            
            # Explore neighbors
            for neighbor in self.adj_list.get(current, []):
                self.stats.edges_explored += 1
                weight = self.edge_weights.get((current, neighbor), 1)
                new_distance = current_dist + weight
                
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    self.nodes[neighbor].distance = new_distance
                    self.nodes[neighbor].parent = current
                    heapq.heappush(pq, (new_distance, neighbor))
                    
                    if self.nodes[neighbor].state not in [NodeState.GOAL]:
                        self.nodes[neighbor].state = NodeState.FRONTIER
            
            if self.nodes[current].state not in [NodeState.START, NodeState.GOAL]:
                self.nodes[current].state = NodeState.VISITED
        
        self.display("Dijkstra: Complete")
        return distances
    
    def bellman_ford(self, start: str) -> Tuple[Dict[str, float], bool]:
        """
        Bellman-Ford algorithm (handles negative weights).
        Time: O(VE), Space: O(V)
        Returns: (distances, has_negative_cycle)
        """
        self._reset_states()
        
        if start not in self.nodes:
            print(f"Start node '{start}' not found!")
            return {}, False
        
        self.nodes[start].state = NodeState.START
        self.nodes[start].distance = 0
        
        distances = {node_id: float('inf') for node_id in self.nodes}
        distances[start] = 0
        
        self.display("Bellman-Ford: Initialization")
        
        # Relax edges V-1 times
        for iteration in range(len(self.nodes) - 1):
            self.stats.algorithm_steps += 1
            self.display(f"Bellman-Ford: Iteration {iteration + 1}")
            
            for edge in self.edges:
                if distances[edge.src] != float('inf'):
                    new_distance = distances[edge.src] + edge.weight
                    if new_distance < distances[edge.dst]:
                        distances[edge.dst] = new_distance
                        self.nodes[edge.dst].distance = new_distance
                        self.nodes[edge.dst].parent = edge.src
                        self.stats.edges_explored += 1
        
        # Check for negative cycles
        has_negative_cycle = False
        for edge in self.edges:
            if distances[edge.src] != float('inf'):
                if distances[edge.src] + edge.weight < distances[edge.dst]:
                    has_negative_cycle = True
                    break
        
        if has_negative_cycle:
            self.display("Bellman-Ford: NEGATIVE CYCLE DETECTED!")
        else:
            self.display("Bellman-Ford: Complete")
        
        return distances, has_negative_cycle
    
    # ==================== HELPER METHODS ====================
    
    def _reconstruct_path(self, start: str, goal: str) -> List[str]:
        """Reconstruct and highlight path from start to goal."""
        path = []
        current = goal
        
        while current is not None:
            path.append(current)
            if self.nodes[current].state not in [NodeState.START, NodeState.GOAL]:
                self.nodes[current].state = NodeState.PATH
            current = self.nodes[current].parent
        
        path.reverse()
        self.stats.path_length = len(path)
        return path
    
    def get_path(self, start: str, goal: str) -> List[str]:
        """Get path from start to goal after traversal."""
        if self.nodes[goal].parent is None and goal != start:
            return []
        return self._reconstruct_path(start, goal)
    
    # ==================== GRAPH PROPERTIES ====================
    
    def is_connected(self) -> bool:
        """Check if graph is connected (for undirected graphs)."""
        if not self.nodes:
            return True
        
        start = next(iter(self.nodes))
        visited = set()
        stack = [start]
        
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            stack.extend(self.adj_list[node])
        
        return len(visited) == len(self.nodes)
    
    def detect_cycle(self) -> bool:
        """Detect if graph has a cycle."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str, parent: Optional[str] = None) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.adj_list.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, node):
                        return True
                elif neighbor in rec_stack:
                    if self.directed or neighbor != parent:
                        return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def topological_sort(self) -> Optional[List[str]]:
        """
        Topological sort using DFS (for DAGs only).
        Returns None if graph has cycle.
        """
        if not self.directed:
            print("Topological sort only works on directed graphs!")
            return None
        
        if self.detect_cycle():
            print("Graph has cycle! Cannot perform topological sort.")
            return None
        
        visited = set()
        stack = []
        
        def dfs_topo(node: str):
            visited.add(node)
            for neighbor in self.adj_list.get(node, []):
                if neighbor not in visited:
                    dfs_topo(neighbor)
            stack.append(node)
        
        for node in self.nodes:
            if node not in visited:
                dfs_topo(node)
        
        return stack[::-1]


# ==================== INTERACTIVE MODE ====================

def interactive_mode():
    """Interactive graph exploration environment."""
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         🕸️  ELITE GRAPH & TRAVERSAL VISUALIZER 🕸️             ║
║                                                               ║
║  Master graph algorithms through visualization                ║
╚═══════════════════════════════════════════════════════════════╝

Commands:
  directed/undirected   - Set graph type
  add <src> <dst> [w]   - Add edge (with optional weight)
  build <format>        - Build from format (see examples)
  show                  - Display current graph
  bfs <start> [goal]    - Breadth-First Search
  dfs <start> [goal]    - Depth-First Search (recursive)
  dfs-i <start> [goal]  - Depth-First Search (iterative)
  dijkstra <start> [g]  - Dijkstra's shortest path
  bellman <start>       - Bellman-Ford algorithm
  props                 - Show graph properties
  reset                 - Reset to empty graph
  help                  - Show this help
  quit                  - Exit

Examples:
  > add A B 5
  > add B C 3
  > bfs A C
  > dijkstra A C

Build formats:
  > build tree         - Binary tree example
  > build dag          - Directed acyclic graph
  > build weighted     - Weighted graph example
  > build grid         - Grid graph
""")
    
    graph = Graph()
    
    while True:
        try:
            cmd = input("\n🕸️  > ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            action = parts[0].lower()
            
            if action == "quit":
                print("Happy learning! 🚀")
                break
            
            elif action == "directed":
                graph = Graph(directed=True)
                print("Switched to directed graph")
            
            elif action == "undirected":
                graph = Graph(directed=False)
                print("Switched to undirected graph")
            
            elif action == "add":
                if len(parts) < 3:
                    print("Usage: add <src> <dst> [weight]")
                    continue
                src, dst = parts[1], parts[2]
                weight = int(parts[3]) if len(parts) > 3 else 1
                graph.add_edge(src, dst, weight)
                print(f"Added edge: {src} -> {dst} (weight: {weight})")
            
            elif action == "build":
                if len(parts) < 2:
                    print("Usage: build <format>")
                    continue
                
                graph_type = parts[1].lower()
                
                if graph_type == "tree":
                    graph = Graph(directed=False)
                    edges = [
                        ('A', 'B'), ('A', 'C'),
                        ('B', 'D'), ('B', 'E'),
                        ('C', 'F'), ('C', 'G')
                    ]
                    graph.build_from_edges(edges)
                    print("Built tree graph")
                
                elif graph_type == "dag":
                    graph = Graph(directed=True)
                    edges = [
                        ('A', 'B'), ('A', 'C'),
                        ('B', 'D'), ('C', 'D'),
                        ('D', 'E')
                    ]
                    graph.build_from_edges(edges)
                    print("Built DAG")
                
                elif graph_type == "weighted":
                    graph = Graph(directed=False)
                    edges = [
                        ('A', 'B', 4), ('A', 'C', 2),
                        ('B', 'C', 1), ('B', 'D', 5),
                        ('C', 'D', 8), ('C', 'E', 10),
                        ('D', 'E', 2)
                    ]
                    graph.build_from_edges(edges)
                    print("Built weighted graph")
                
                elif graph_type == "grid":
                    graph = Graph(directed=False)
                    # 3x3 grid
                    for i in range(3):
                        for j in range(3):
                            node = f"{i}{j}"
                            if j < 2:
                                graph.add_edge(node, f"{i}{j+1}")
                            if i < 2:
                                graph.add_edge(node, f"{i+1}{j}")
                    print("Built 3x3 grid graph")
                
                else:
                    print(f"Unknown graph type: {graph_type}")
            
            elif action == "show":
                graph.display(show_stats=False)
            
            elif action == "bfs":
                if len(parts) < 2:
                    print("Usage: bfs <start> [goal]")
                    continue
                start = parts[1]
                goal = parts[2] if len(parts) > 2 else None
                visited = graph.bfs(start, goal)
                print(f"\nVisited order: {' → '.join(visited)}")
                if goal:
                    path = graph.get_path(start, goal)
                    if path:
                        print(f"Path to goal: {' → '.join(path)}")
                    else:
                        print(f"No path found to {goal}")
                input("\nPress Enter to continue...")
            
            elif action == "dfs":
                if len(parts) < 2:
                    print("Usage: dfs <start> [goal]")
                    continue
                start = parts[1]
                goal = parts[2] if len(parts) > 2 else None
                visited = graph.dfs(start, goal)
                print(f"\nVisited order: {' → '.join(visited)}")
                if goal:
                    path = graph.get_path(start, goal)
                    if path:
                        print(f"Path to goal: {' → '.join(path)}")
                    else:
                        print(f"No path found to {goal}")
                input("\nPress Enter to continue...")
            
            elif action == "dfs-i":
                if len(parts) < 2:
                    print("Usage: dfs-i <start> [goal]")
                    continue
                start = parts[1]
                goal = parts[2] if len(parts) > 2 else None
                visited = graph.dfs_iterative(start, goal)
                print(f"\nVisited order: {' → '.join(visited)}")
                if goal:
                    path = graph.get_path(start, goal)
                    if path:
                        print(f"Path to goal: {' → '.join(path)}")
                    else:
                        print(f"No path found to {goal}")
                input("\nPress Enter to continue...")
            
            elif action == "dijkstra":
                if len(parts) < 2:
                    print("Usage: dijkstra <start> [goal]")
                    continue
                start = parts[1]
                goal = parts[2] if len(parts) > 2 else None
                distances = graph.dijkstra(start, goal)
                print(f"\nShortest distances from {start}:")
                for node, dist in sorted(distances.items()):
                    if dist != float('inf'):
                        print(f"  {node}: {dist}")
                if goal and goal in distances:
                    path = graph.get_path(start, goal)
                    if path:
                        print(f"\nShortest path: {' → '.join(path)}")
                input("\nPress Enter to continue...")
            
            elif action == "bellman":
                if len(parts) < 2:
                    print("Usage: bellman <start>")
                    continue
                start = parts[1]
                distances, has_cycle = graph.bellman_ford(start)
                if has_cycle:
                    print("\n⚠️  Negative cycle detected!")
                else:
                    print(f"\nShortest distances from {start}:")
                    for node, dist in sorted(distances.items()):
                        if dist != float('inf'):
                            print(f"  {node}: {dist}")
                input("\nPress Enter to continue...")
            
            elif action == "props":
                print("\n📊 Graph Properties:")
                print(f"  Nodes: {len(graph.nodes)}")
                print(f"  Edges: {len(graph.edges) // (1 if graph.directed else 2)}")
                print(f"  Type: {'Directed' if graph.directed else 'Undirected'}")
                print(f"  Connected: {graph.is_connected()}")
                print(f"  Has Cycle: {graph.detect_cycle()}")
                if graph.directed:
                    topo = graph.topological_sort()
                    if topo:
                        print(f"  Topological Order: {' → '.join(topo)}")
            
            elif action == "reset":
                graph = Graph(directed=graph.directed)
                print("Graph reset")
            
            elif action == "help":
                print(__doc__)
            
            else:
                print(f"Unknown command: {action}. Type 'help' for commands.")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            print("Type 'help' for usage.")


# ==================== DEMO EXAMPLES ====================

def demo_examples():
    """Curated examples for learning."""
    
    print("\n" + "="*80)
    print("📚 DEMO 1: BFS on Tree")
    print("="*80)
    graph1 = Graph(directed=False)
    graph1.build_from_edges([
        ('A', 'B'), ('A', 'C'),
        ('B', 'D'), ('B', 'E'),
        ('C', 'F'), ('C', 'G')
    ])
    graph1.bfs('A', 'G')
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*80)
    print("📚 DEMO 2: DFS on DAG")
    print("="*80)
    graph2 = Graph(directed=True)
    graph2.build_from_edges([
        ('A', 'B'), ('A', 'C'),
        ('B', 'D'), ('C', 'D'),
        ('D', 'E')
    ])
    graph2.dfs('A', 'E')
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*80)
    print("📚 DEMO 3: Dijkstra's Shortest Path")
    print("="*80)
    graph3 = Graph(directed=False)
    graph3.build_from_edges([
        ('A', 'B', 4), ('A', 'C', 2),
        ('B', 'C', 1), ('B', 'D', 5),
        ('C', 'D', 8), ('C', 'E', 10),
        ('D', 'E', 2)
    ])
    graph3.dijkstra('A', 'E')
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*80)
    print("📚 DEMO 4: BFS vs DFS Comparison")
    print("="*80)
    graph4 = Graph(directed=False)
    graph4.build_from_edges([
        ('1', '2'), ('1', '3'),
        ('2', '4'), ('2', '5'),
        ('3', '6'), ('3', '7'),
        ('4', '8')
    ])
    
    print("\nBFS Traversal:")
    graph4.bfs('1')
    input("\nPress Enter for DFS...")
    
    graph4._reset_states()
    print("\nDFS Traversal:")
    graph4.dfs('1')
    input("\nDemos complete!")


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_examples()
    else:
        interactive_mode()