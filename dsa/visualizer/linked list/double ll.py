#!/usr/bin/env python3
"""
Elite Doubly Linked List Visualizer
Master doubly linked lists through bidirectional pointer visualization.

Usage:
    python doubly_linked_list.py
    
Features:
- ASCII doubly linked list with forward/backward pointers
- Bidirectional traversal visualization
- Insert/delete operations with dual pointer updates
- Reverse traversal
- Forward and backward iteration
- Interactive exploration mode
"""

from typing import Optional, Any, List
import sys
import os
import time
from dataclasses import dataclass
from enum import Enum


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
    """Visual states for list nodes."""
    NORMAL = 0
    CURRENT = 1
    PREVIOUS = 2
    NEXT = 3
    INSERTING = 4
    DELETING = 5
    HEAD = 6
    TAIL = 7
    TRAVERSING_FORWARD = 8
    TRAVERSING_BACKWARD = 9


@dataclass
class ListStats:
    """Track doubly linked list performance metrics."""
    total_insertions: int = 0
    total_deletions: int = 0
    total_forward_traversals: int = 0
    total_backward_traversals: int = 0
    total_pointer_updates: int = 0
    current_length: int = 0


class Node:
    """Doubly linked list node with prev and next pointers."""
    
    def __init__(self, data: Any):
        self.data = data
        self.next: Optional['Node'] = None
        self.prev: Optional['Node'] = None
        self.state: NodeState = NodeState.NORMAL
    
    def __repr__(self):
        return f"Node({self.data})"


class DoublyLinkedList:
    """
    Elite doubly linked list implementation with comprehensive visualization.
    Demonstrates bidirectional pointer manipulation and traversal patterns.
    """
    
    def __init__(self, delay: float = 0.5):
        """Initialize empty doubly linked list."""
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self.delay = delay
        self.stats = ListStats()
        self.operation_log: List[str] = []
    
    # ==================== CORE OPERATIONS ====================
    
    def append(self, data: Any) -> None:
        """
        Add element to end of list.
        Time: O(1) with tail pointer
        """
        self._log(f"Appending {data} to end of list")
        
        new_node = Node(data)
        new_node.state = NodeState.INSERTING
        
        if not self.head:
            # Empty list
            self.head = new_node
            self.tail = new_node
            self.head.state = NodeState.HEAD
            self._display(f"Inserting {data} as first node (head and tail)")
        else:
            # Add to end
            if self.tail:
                self.tail.state = NodeState.CURRENT
            self._display(f"Linking {data} after tail")
            
            new_node.prev = self.tail
            if self.tail:
                self.tail.next = new_node
            self.stats.total_pointer_updates += 2  # prev and next
            
            self.tail = new_node
            self.tail.state = NodeState.TAIL
            self._display(f"Updated tail to {data}")
        
        self.stats.total_insertions += 1
        self.stats.current_length += 1
        
        self._reset_states()
        self._display(f"Successfully appended {data}")
    
    def prepend(self, data: Any) -> None:
        """
        Add element to beginning of list.
        Time: O(1)
        """
        self._log(f"Prepending {data} to start of list")
        
        new_node = Node(data)
        new_node.state = NodeState.INSERTING
        
        if not self.head:
            # Empty list
            self.head = new_node
            self.tail = new_node
            self._display(f"Inserting {data} as first node")
        else:
            # Add to beginning
            if self.head:
                self.head.state = NodeState.CURRENT
            self._display(f"Preparing to insert {data} at head")
            
            new_node.next = self.head
            self.head.prev = new_node
            self.stats.total_pointer_updates += 2  # prev and next
            
            self.head = new_node
            self.head.state = NodeState.HEAD
            self._display(f"Updated head to {data}")
        
        self.stats.total_insertions += 1
        self.stats.current_length += 1
        
        self._reset_states()
        self._display(f"Successfully prepended {data}")
    
    def insert_at(self, index: int, data: Any) -> None:
        """
        Insert element at specific index.
        Time: O(n)
        """
        if index < 0:
            print(f"{Color.RED}Error: Index cannot be negative{Color.RESET}")
            return
        
        if index == 0:
            self.prepend(data)
            return
        
        if index >= self.stats.current_length:
            self.append(data)
            return
        
        self._log(f"Inserting {data} at index {index}")
        
        # Decide whether to traverse from head or tail
        if index <= self.stats.current_length // 2:
            # Traverse from head
            current = self.head
            position = 0
            
            while current and position < index:
                current.state = NodeState.TRAVERSING_FORWARD
                self._display(f"Traversing forward to position {index} (at {position})")
                self.stats.total_forward_traversals += 1
                current.state = NodeState.NORMAL
                current = current.next
                position += 1
        else:
            # Traverse from tail (optimization!)
            current = self.tail
            position = self.stats.current_length - 1
            
            while current and position > index:
                current.state = NodeState.TRAVERSING_BACKWARD
                self._display(f"Traversing backward to position {index} (at {position})")
                self.stats.total_backward_traversals += 1
                current.state = NodeState.NORMAL
                current = current.prev
                position -= 1
        
        if not current:
            print(f"{Color.RED}Error: Index {index} out of bounds{Color.RESET}")
            return
        
        # Insert new node before current
        new_node = Node(data)
        new_node.state = NodeState.INSERTING
        current.state = NodeState.CURRENT
        if current.prev:
            current.prev.state = NodeState.PREVIOUS
        
        self._display(f"Inserting {data} at position {index}")
        
        # Update pointers
        new_node.next = current
        new_node.prev = current.prev
        
        if current.prev:
            current.prev.next = new_node
        else:
            self.head = new_node
        
        current.prev = new_node
        self.stats.total_pointer_updates += 4  # 2 prev + 2 next
        
        self.stats.total_insertions += 1
        self.stats.current_length += 1
        
        self._reset_states()
        self._display(f"Successfully inserted {data} at index {index}")
    
    def delete_at(self, index: int) -> Optional[Any]:
        """
        Delete element at specific index.
        Time: O(n)
        """
        if index < 0 or not self.head:
            print(f"{Color.RED}Error: Invalid index or empty list{Color.RESET}")
            return None
        
        self._log(f"Deleting node at index {index}")
        
        # Find node to delete
        if index <= self.stats.current_length // 2:
            # Traverse from head
            current = self.head
            position = 0
            
            while current and position < index:
                current.state = NodeState.TRAVERSING_FORWARD
                self._display(f"Traversing forward to position {index} (at {position})")
                self.stats.total_forward_traversals += 1
                current.state = NodeState.NORMAL
                current = current.next
                position += 1
        else:
            # Traverse from tail
            current = self.tail
            position = self.stats.current_length - 1
            
            while current and position > index:
                current.state = NodeState.TRAVERSING_BACKWARD
                self._display(f"Traversing backward to position {index} (at {position})")
                self.stats.total_backward_traversals += 1
                current.state = NodeState.NORMAL
                current = current.prev
                position -= 1
        
        if not current:
            print(f"{Color.RED}Error: Index {index} out of bounds{Color.RESET}")
            return None
        
        # Delete node
        current.state = NodeState.DELETING
        if current.prev:
            current.prev.state = NodeState.PREVIOUS
        if current.next:
            current.next.state = NodeState.NEXT
        
        self._display(f"Deleting node {current.data}")
        
        data = current.data
        
        # Update pointers
        if current.prev:
            current.prev.next = current.next
            self.stats.total_pointer_updates += 1
        else:
            self.head = current.next
        
        if current.next:
            current.next.prev = current.prev
            self.stats.total_pointer_updates += 1
        else:
            self.tail = current.prev
        
        self.stats.total_deletions += 1
        self.stats.current_length -= 1
        
        self._reset_states()
        self._display(f"Successfully deleted {data}")
        return data
    
    def delete_value(self, value: Any) -> bool:
        """
        Delete first occurrence of value.
        Time: O(n)
        """
        self._log(f"Searching for and deleting value {value}")
        
        current = self.head
        
        while current:
            current.state = NodeState.TRAVERSING_FORWARD
            self._display(f"Searching... checking {current.data}")
            self.stats.total_forward_traversals += 1
            
            if current.data == value:
                # Found it
                current.state = NodeState.DELETING
                if current.prev:
                    current.prev.state = NodeState.PREVIOUS
                if current.next:
                    current.next.state = NodeState.NEXT
                
                self._display(f"Found {value}, deleting")
                
                # Update pointers
                if current.prev:
                    current.prev.next = current.next
                    self.stats.total_pointer_updates += 1
                else:
                    self.head = current.next
                
                if current.next:
                    current.next.prev = current.prev
                    self.stats.total_pointer_updates += 1
                else:
                    self.tail = current.prev
                
                self.stats.total_deletions += 1
                self.stats.current_length -= 1
                
                self._reset_states()
                self._display(f"Successfully deleted {value}")
                return True
            
            current.state = NodeState.NORMAL
            current = current.next
        
        self._reset_states()
        print(f"{Color.YELLOW}Value {value} not found in list{Color.RESET}")
        return False
    
    # ==================== TRAVERSAL OPERATIONS ====================
    
    def traverse_forward(self) -> List[Any]:
        """
        Traverse list from head to tail.
        Time: O(n)
        """
        self._log("Traversing list forward (head to tail)")
        
        result = []
        current = self.head
        position = 0
        
        while current:
            current.state = NodeState.TRAVERSING_FORWARD
            self._display(f"Forward traversal at index {position}: {current.data}")
            self.stats.total_forward_traversals += 1
            
            result.append(current.data)
            current.state = NodeState.NORMAL
            current = current.next
            position += 1
        
        self._reset_states()
        self._display("Forward traversal complete")
        return result
    
    def traverse_backward(self) -> List[Any]:
        """
        Traverse list from tail to head.
        Time: O(n)
        """
        self._log("Traversing list backward (tail to head)")
        
        result = []
        current = self.tail
        position = self.stats.current_length - 1
        
        while current:
            current.state = NodeState.TRAVERSING_BACKWARD
            self._display(f"Backward traversal at index {position}: {current.data}")
            self.stats.total_backward_traversals += 1
            
            result.append(current.data)
            current.state = NodeState.NORMAL
            current = current.prev
            position -= 1
        
        self._reset_states()
        self._display("Backward traversal complete")
        return result
    
    def reverse(self) -> None:
        """
        Reverse list by swapping prev and next pointers.
        Time: O(n), Space: O(1)
        """
        self._log("Reversing list by swapping pointers")
        
        if not self.head or not self.head.next:
            self._display("List too short to reverse")
            return
        
        current = self.head
        position = 0
        
        while current:
            current.state = NodeState.CURRENT
            self._display(f"Reversing pointers at index {position}: {current.data}")
            
            # Swap prev and next
            current.prev, current.next = current.next, current.prev
            self.stats.total_pointer_updates += 2
            
            current.state = NodeState.NORMAL
            # Move to next (which is now prev due to swap)
            current = current.prev
            position += 1
        
        # Swap head and tail
        self.head, self.tail = self.tail, self.head
        
        self._reset_states()
        self._display("List reversed")
    
    # ==================== UTILITY OPERATIONS ====================
    
    def find(self, value: Any) -> int:
        """
        Find index of first occurrence of value.
        Time: O(n)
        """
        current = self.head
        index = 0
        
        while current:
            current.state = NodeState.TRAVERSING_FORWARD
            self._display(f"Searching for {value}... at index {index}")
            self.stats.total_forward_traversals += 1
            
            if current.data == value:
                self._reset_states()
                self._display(f"Found {value} at index {index}")
                return index
            
            current.state = NodeState.NORMAL
            current = current.next
            index += 1
        
        self._reset_states()
        return -1
    
    def get(self, index: int) -> Optional[Any]:
        """
        Get value at index (optimized with bidirectional traversal).
        Time: O(n)
        """
        if index < 0 or index >= self.stats.current_length:
            return None
        
        # Choose optimal direction
        if index <= self.stats.current_length // 2:
            current = self.head
            for _ in range(index):
                if current:
                    current = current.next
                self.stats.total_forward_traversals += 1
        else:
            current = self.tail
            for _ in range(self.stats.current_length - 1 - index):
                if current:
                    current = current.prev
                self.stats.total_backward_traversals += 1
        
        return current.data if current else None
    
    def find_middle(self) -> Optional[Any]:
        """
        Find middle element using slow-fast pointer technique.
        Time: O(n), Space: O(1)
        """
        self._log("Finding middle element using two-pointer technique")
        
        if not self.head:
            return None
        
        slow = self.head
        fast = self.head
        
        while fast and fast.next:
            slow.state = NodeState.CURRENT
            fast.state = NodeState.NEXT
            self._display(f"Slow at {slow.data}, Fast at {fast.data}")
            
            slow.state = NodeState.NORMAL
            fast.state = NodeState.NORMAL
            
            slow = slow.next
            fast = fast.next.next
            self.stats.total_forward_traversals += 2
        
        if slow:
            slow.state = NodeState.CURRENT
            self._display(f"Middle element found: {slow.data}")
            time.sleep(self.delay * 2)
            slow.state = NodeState.NORMAL
            return slow.data
        
        return None
    
    def length(self) -> int:
        """Get length of list. Time: O(1) - we track it!"""
        return self.stats.current_length
    
    def to_list_forward(self) -> List[Any]:
        """Convert to Python list (forward direction)."""
        result = []
        current = self.head
        while current:
            result.append(current.data)
            current = current.next
        return result
    
    def to_list_backward(self) -> List[Any]:
        """Convert to Python list (backward direction)."""
        result = []
        current = self.tail
        while current:
            result.append(current.data)
            current = current.prev
        return result
    
    def clear(self) -> None:
        """Clear all nodes."""
        self.head = None
        self.tail = None
        self.stats.current_length = 0
        self._display("List cleared")
    
    # ==================== VISUALIZATION ====================
    
    def _display(self, title: Optional[str] = None) -> None:
        """Main display function."""
        self._clear_screen()
        
        print("=" * 100)
        print(f"{Color.BOLD}⇄ DOUBLY LINKED LIST VISUALIZER{Color.RESET}")
        if title:
            print(f"{Color.CYAN}{title}{Color.RESET}")
        print("=" * 100)
        
        # Visual representation
        self._display_visual()
        
        # Pointer info
        self._display_pointers()
        
        # Statistics
        self._display_statistics()
        
        print("=" * 100)
        time.sleep(self.delay)
    
    def _display_visual(self) -> None:
        """Display doubly linked list as ASCII art with bidirectional arrows."""
        print(f"\n{Color.BOLD}List Structure (Forward ⇒ / Backward ⇐):{Color.RESET}\n")
        
        if not self.head:
            print(f"  {Color.GRAY}(empty list){Color.RESET}")
            return
        
        # Collect all nodes
        nodes = []
        current = self.head
        while current:
            nodes.append(current)
            current = current.next
        
        max_nodes_per_line = 5
        
        for line_start in range(0, len(nodes), max_nodes_per_line):
            line_nodes = nodes[line_start:line_start + max_nodes_per_line]
            
            # Top border
            print("  ", end="")
            for i, node in enumerate(line_nodes):
                color = self._get_node_color(node.state)
                print(f"{color}┌───────┐{Color.RESET}", end="")
                if i < len(line_nodes) - 1:
                    print("       ", end="")
            print()
            
            # Data row
            print("  ", end="")
            for i, node in enumerate(line_nodes):
                color = self._get_node_color(node.state)
                symbol = self._get_node_symbol(node.state)
                data_str = str(node.data)
                print(f"{color}│ {data_str:^5} │{Color.RESET}", end="")
                if i < len(line_nodes) - 1:
                    print(" ⇄ ", end="")
                if symbol:
                    print(f" {symbol}", end="")
            print()
            
            # Bottom border
            print("  ", end="")
            for i, node in enumerate(line_nodes):
                color = self._get_node_color(node.state)
                print(f"{color}└───────┘{Color.RESET}", end="")
                if i < len(line_nodes) - 1:
                    print("       ", end="")
            print()
            
            # Connection indicators
            if line_start + max_nodes_per_line < len(nodes):
                print("      ⇓")
            
            print()
    
    def _display_pointers(self) -> None:
        """Display head and tail pointers with prev/next info."""
        print(f"{Color.BOLD}Pointers:{Color.RESET}")
        
        if self.head:
            print(f"  Head: {Color.MAGENTA}{self.head.data}{Color.RESET} ", end="")
            print(f"(prev: {Color.GRAY}None{Color.RESET}, ", end="")
            print(f"next: {self.head.next.data if self.head.next else Color.GRAY + 'None' + Color.RESET})")
        else:
            print(f"  Head: {Color.GRAY}None{Color.RESET}")
        
        if self.tail:
            print(f"  Tail: {Color.MAGENTA}{self.tail.data}{Color.RESET} ", end="")
            print(f"(prev: {self.tail.prev.data if self.tail.prev else Color.GRAY + 'None' + Color.RESET}, ", end="")
            print(f"next: {Color.GRAY}None{Color.RESET})")
        else:
            print(f"  Tail: {Color.GRAY}None{Color.RESET}")
        
        print()
    
    def _display_statistics(self) -> None:
        """Display operation statistics."""
        print(f"{Color.BOLD}📊 Statistics:{Color.RESET}")
        print(f"  Length: {self.stats.current_length}")
        print(f"  Total Insertions: {self.stats.total_insertions}")
        print(f"  Total Deletions: {self.stats.total_deletions}")
        print(f"  Forward Traversals: {self.stats.total_forward_traversals}")
        print(f"  Backward Traversals: {self.stats.total_backward_traversals}")
        print(f"  Pointer Updates: {self.stats.total_pointer_updates}")
        
        # Highlight bidirectional optimization
        if self.stats.total_backward_traversals > 0:
            print(f"\n  {Color.GREEN}✓ Bidirectional optimization used!{Color.RESET}")
            print(f"    Backward traversals save time for tail-end operations")
    
    def _get_node_color(self, state: NodeState) -> str:
        """Map node state to color."""
        color_map = {
            NodeState.NORMAL: Color.WHITE,
            NodeState.CURRENT: Color.CYAN,
            NodeState.PREVIOUS: Color.YELLOW,
            NodeState.NEXT: Color.MAGENTA,
            NodeState.INSERTING: Color.GREEN,
            NodeState.DELETING: Color.RED,
            NodeState.HEAD: Color.BLUE,
            NodeState.TAIL: Color.BLUE,
            NodeState.TRAVERSING_FORWARD: Color.CYAN,
            NodeState.TRAVERSING_BACKWARD: Color.MAGENTA,
        }
        return color_map.get(state, Color.WHITE)
    
    def _get_node_symbol(self, state: NodeState) -> str:
        """Map node state to symbol."""
        symbol_map = {
            NodeState.NORMAL: "",
            NodeState.CURRENT: "👉",
            NodeState.PREVIOUS: "⬅",
            NodeState.NEXT: "➡",
            NodeState.INSERTING: "⬇",
            NodeState.DELETING: "✗",
            NodeState.HEAD: "🎯",
            NodeState.TAIL: "🏁",
            NodeState.TRAVERSING_FORWARD: "⇒",
            NodeState.TRAVERSING_BACKWARD: "⇐",
        }
        return symbol_map.get(state, "")
    
    def _reset_states(self) -> None:
        """Reset all node states to normal."""
        current = self.head
        while current:
            current.state = NodeState.NORMAL
            current = current.next
    
    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def _log(self, message: str) -> None:
        """Log operation."""
        self.operation_log.append(message)
    
    def show_log(self) -> None:
        """Display operation log."""
        print(f"\n{Color.BOLD}📋 Operation Log:{Color.RESET}")
        for i, log in enumerate(self.operation_log[-20:], 1):
            print(f"  {i}. {log}")


# ==================== INTERACTIVE MODE ====================

def interactive_mode():
    """Interactive doubly linked list exploration."""
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         ⇄ ELITE DOUBLY LINKED LIST VISUALIZER ⇄               ║
║                                                               ║
║  Master doubly linked lists with bidirectional pointers      ║
╚═══════════════════════════════════════════════════════════════╝

Commands:
  append <value>        - Add to end
  prepend <value>       - Add to beginning
  insert <idx> <val>    - Insert at index
  delete <idx>          - Delete at index
  remove <value>        - Delete first occurrence of value
  find <value>          - Find index of value
  get <idx>             - Get value at index
  forward               - Traverse forward (head to tail)
  backward              - Traverse backward (tail to head)
  reverse               - Reverse list by swapping pointers
  middle                - Find middle element
  show                  - Display current list
  clear                 - Clear all nodes
  log                   - Show operation history
  speed <delay>         - Set animation speed (0.1 to 2.0)
  help                  - Show this help
  quit                  - Exit

Examples:
  > append 10
  > append 20
  > prepend 5
  > backward
  > reverse
""")
    
    dll = DoublyLinkedList(delay=0.5)
    dll._display("Doubly Linked List Initialized")
    
    while True:
        try:
            cmd = input(f"\n⇄ [len={dll.stats.current_length}] > ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            action = parts[0].lower()
            
            if action == "quit":
                print("Happy learning! 🚀")
                break
            
            elif action == "speed":
                if len(parts) < 2:
                    print("Usage: speed <delay>")
                    continue
                try:
                    delay = float(parts[1])
                    dll.delay = max(0.1, min(2.0, delay))
                    print(f"Speed set to {dll.delay}s per step")
                except ValueError:
                    print("Invalid delay value")
            
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


# ==================== DEMO EXAMPLES ====================

def demo_examples():
    """Curated examples for learning."""
    
    print("\n" + "="*100)
    print("📚 DEMO 1: Basic Operations with Bidirectional Pointers")
    print("="*100)
    dll1 = DoublyLinkedList(delay=0.8)
    
    print("\nAppending elements...")
    for val in [10, 20, 30, 40]:
        dll1.append(val)
    
    input("\nPress Enter to prepend...")
    dll1.prepend(5)
    
    input("\nPress Enter to insert at middle...")
    dll1.insert_at(3, 25)
    
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*100)
    print("📚 DEMO 2: Bidirectional Traversal")
    print("="*100)
    dll2 = DoublyLinkedList(delay=0.8)
    
    print("\nBuilding list...")
    for val in [1, 2, 3, 4, 5]:
        dll2.append(val)
    
    dll2._display("List ready for traversal")
    input("\nPress Enter to traverse forward (head to tail)...")
    result_fwd = dll2.traverse_forward()
    print(f"\n{Color.GREEN}Forward: {' → '.join(map(str, result_fwd))}{Color.RESET}")
    
    input("\nPress Enter to traverse backward (tail to head)...")
    result_bwd = dll2.traverse_backward()
    print(f"\n{Color.MAGENTA}Backward: {' ← '.join(map(str, result_bwd))}{Color.RESET}")
    
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*100)
    print("📚 DEMO 3: Optimization - Bidirectional Search")
    print("="*100)
    dll3 = DoublyLinkedList(delay=0.8)
    
    print("\nBuilding list with 10 elements...")
    for val in range(1, 11):
        dll3.append(val * 10)
    
    dll3._display("List with 10 elements")
    input("\nPress Enter to insert at index 2 (near head - forward traversal)...")
    dll3.insert_at(2, 25)
    
    input("\nPress Enter to insert at index 8 (near tail - backward traversal)...")
    dll3.insert_at(8, 85)
    
    print(f"\n{Color.GREEN}Key Insight:{Color.RESET}")
    print(f"  Forward traversals: {dll3.stats.total_forward_traversals}")
    print(f"  Backward traversals: {dll3.stats.total_backward_traversals}")
    print(f"  The algorithm automatically chose the optimal direction!")
    
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*100)
    print("📚 DEMO 4: Reverse by Swapping Pointers")
    print("="*100)
    dll4 = DoublyLinkedList(delay=0.8)
    
    print("\nBuilding list...")
    for val in [10, 20, 30, 40, 50]:
        dll4.append(val)
    
    dll4._display("Original List")
    input("\nPress Enter to reverse by swapping prev/next pointers...")
    dll4.reverse()
    
    print(f"\n{Color.GREEN}Notice:{Color.RESET}")
    print(f"  Head and tail swapped")
    print(f"  Every node's prev and next pointers were swapped")
    print(f"  O(n) time, O(1) space - no new nodes created!")
    
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*100)
    print("📚 DEMO 5: Delete Operations with Dual Pointers")
    print("="*100)
    dll5 = DoublyLinkedList(delay=0.8)
    
    print("\nBuilding list...")
    for val in [10, 20, 30, 40, 50]:
        dll5.append(val)
    
    dll5._display("Original list")
    input("\nPress Enter to delete at index 2 (middle)...")
    dll5.delete_at(2)
    
    print(f"\n{Color.CYAN}Deletion requires updating:{Color.RESET}")
    print(f"  1. Previous node's 'next' pointer")
    print(f"  2. Next node's 'prev' pointer")
    print(f"  Total: 2 pointer updates (vs 1 in singly linked list)")
    
    input("\nPress Enter to delete head...")
    dll5.delete_at(0)
    
    input("\nPress Enter to delete tail...")
    dll5.delete_at(dll5.length() - 1)
    
    print(f"\n{Color.GREEN}Advantage:{Color.RESET}")
    print(f"  Deleting tail is O(1) with doubly linked list!")
    print(f"  (Would be O(n) with singly linked list)")
    
    input("\nDemos complete! Press Enter...")


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_examples()
    else:
        interactive_mode() "append":
                if len(parts) < 2:
                    print("Usage: append <value>")
                    continue
                try:
                    value = int(parts[1])
                except ValueError:
                    value = parts[1]
                dll.append(value)
            
            elif action == "prepend":
                if len(parts) < 2:
                    print("Usage: prepend <value>")
                    continue
                try:
                    value = int(parts[1])
                except ValueError:
                    value = parts[1]
                dll.prepend(value)
            
            elif action == "insert":
                if len(parts) < 3:
                    print("Usage: insert <index> <value>")
                    continue
                try:
                    index = int(parts[1])
                    value = int(parts[2])
                    dll.insert_at(index, value)
                except ValueError:
                    print("Invalid index or value")
            
            elif action == "delete":
                if len(parts) < 2:
                    print("Usage: delete <index>")
                    continue
                try:
                    index = int(parts[1])
                    result = dll.delete_at(index)
                    if result is not None:
                        print(f"Deleted: {result}")
                except ValueError:
                    print("Invalid index")
            
            elif action == "remove":
                if len(parts) < 2:
                    print("Usage: remove <value>")
                    continue
                try:
                    value = int(parts[1])
                except ValueError:
                    value = parts[1]
                dll.delete_value(value)
            
            elif action == "find":
                if len(parts) < 2:
                    print("Usage: find <value>")
                    continue
                try:
                    value = int(parts[1])
                except ValueError:
                    value = parts[1]
                index = dll.find(value)
                if index >= 0:
                    print(f"Found {value} at index {index}")
                else:
                    print(f"{value} not found in list")
            
            elif action == "get":
                if len(parts) < 2:
                    print("Usage: get <index>")
                    continue
                try:
                    index = int(parts[1])
                    value = dll.get(index)
                    if value is not None:
                        print(f"Value at index {index}: {value}")
                    else:
                        print("Index out of bounds")
                except ValueError:
                    print("Invalid index")
            
            elif action == "forward":
                result = dll.traverse_forward()
                print(f"\nForward: {' → '.join(map(str, result))}")
                input("\nPress Enter to continue...")
            
            elif action == "backward":
                result = dll.traverse_backward()
                print(f"\nBackward: {' ← '.join(map(str, result))}")
                input("\nPress Enter to continue...")
            
            elif action == "reverse":
                dll.reverse()
                input("\nPress Enter to continue...")
            
            elif action == "middle":
                middle = dll.find_middle()
                if middle is not None:
                    print(f"Middle element: {middle}")
                else:
                    print("List is empty")
                input("\nPress Enter to continue...")
            
            elif action == "show":
                dll._display("Current List State")
            
            elif action == "clear":
                dll.clear()
            
            elif action == "log":
                dll.show_log()
            
            elif action == "exit":
                print("Happy learning! 🚀")
                break