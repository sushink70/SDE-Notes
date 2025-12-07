#!/usr/bin/env python3
"""
Elite Singly Linked List Visualizer
Master linked lists through visualization of pointer operations.

Usage:
    python linked_list.py
    
Features:
- ASCII linked list visualization with pointers
- Insert/delete operations with pointer tracking
- Reverse operations (iterative and recursive)
- Cycle detection and visualization
- Middle element finding
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


@dataclass
class ListStats:
    """Track linked list performance metrics."""
    total_insertions: int = 0
    total_deletions: int = 0
    total_traversals: int = 0
    total_pointer_updates: int = 0
    current_length: int = 0


class Node:
    """Linked list node with visualization properties."""
    
    def __init__(self, data: Any):
        self.data = data
        self.next: Optional['Node'] = None
        self.state: NodeState = NodeState.NORMAL
    
    def __repr__(self):
        return f"Node({self.data})"


class SinglyLinkedList:
    """
    Elite singly linked list implementation with comprehensive visualization.
    Demonstrates pointer manipulation and traversal patterns.
    """
    
    def __init__(self, delay: float = 0.5):
        """Initialize empty linked list."""
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self.delay = delay
        self.stats = ListStats()
        self.operation_log: List[str] = []
    
    # ==================== CORE OPERATIONS ====================
    
    def append(self, data: Any) -> None:
        """
        Add element to end of list.
        Time: O(1) with tail pointer, O(n) without
        """
        self._log(f"Appending {data} to end of list")
        
        new_node = Node(data)
        new_node.state = NodeState.INSERTING
        
        if not self.head:
            # Empty list
            self.head = new_node
            self.tail = new_node
            self.head.state = NodeState.HEAD
            self._display(f"Inserting {data} as first node (head)")
        else:
            # Add to end
            if self.tail:
                self.tail.state = NodeState.CURRENT
            self._display(f"Linking {data} after tail")
            
            if self.tail:
                self.tail.next = new_node
                self.stats.total_pointer_updates += 1
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
            self.stats.total_pointer_updates += 1
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
        
        self._log(f"Inserting {data} at index {index}")
        
        # Find position
        current = self.head
        position = 0
        
        while current and position < index - 1:
            current.state = NodeState.CURRENT
            self._display(f"Traversing to position {index} (at {position})")
            self.stats.total_traversals += 1
            current.state = NodeState.NORMAL
            current = current.next
            position += 1
        
        if not current:
            print(f"{Color.RED}Error: Index {index} out of bounds{Color.RESET}")
            return
        
        # Insert new node
        new_node = Node(data)
        new_node.state = NodeState.INSERTING
        current.state = NodeState.CURRENT
        
        if current.next:
            current.next.state = NodeState.NEXT
            self._display(f"Inserting {data} between {current.data} and {current.next.data}")
        else:
            self._display(f"Inserting {data} after {current.data}")
        
        new_node.next = current.next
        current.next = new_node
        self.stats.total_pointer_updates += 2
        
        if not new_node.next:
            self.tail = new_node
        
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
        
        # Delete head
        if index == 0:
            self.head.state = NodeState.DELETING
            self._display(f"Deleting head node {self.head.data}")
            
            data = self.head.data
            self.head = self.head.next
            self.stats.total_pointer_updates += 1
            
            if not self.head:
                self.tail = None
            
            self.stats.total_deletions += 1
            self.stats.current_length -= 1
            
            self._display(f"Successfully deleted {data}")
            return data
        
        # Find node before deletion point
        current = self.head
        position = 0
        
        while current.next and position < index - 1:
            current.state = NodeState.CURRENT
            self._display(f"Traversing to position {index} (at {position})")
            self.stats.total_traversals += 1
            current.state = NodeState.NORMAL
            current = current.next
            position += 1
        
        if not current.next:
            print(f"{Color.RED}Error: Index {index} out of bounds{Color.RESET}")
            return None
        
        # Delete node
        to_delete = current.next
        to_delete.state = NodeState.DELETING
        current.state = NodeState.CURRENT
        
        if to_delete.next:
            to_delete.next.state = NodeState.NEXT
            self._display(f"Deleting {to_delete.data} (linking {current.data} to {to_delete.next.data})")
        else:
            self._display(f"Deleting tail node {to_delete.data}")
        
        data = to_delete.data
        current.next = to_delete.next
        self.stats.total_pointer_updates += 1
        
        if not current.next:
            self.tail = current
        
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
        
        if not self.head:
            return False
        
        # Check head
        if self.head.data == value:
            self.head.state = NodeState.DELETING
            self._display(f"Found {value} at head, deleting")
            
            self.head = self.head.next
            self.stats.total_pointer_updates += 1
            
            if not self.head:
                self.tail = None
            
            self.stats.total_deletions += 1
            self.stats.current_length -= 1
            
            self._display(f"Successfully deleted {value}")
            return True
        
        # Search list
        current = self.head
        while current.next:
            current.state = NodeState.CURRENT
            current.next.state = NodeState.NEXT
            self._display(f"Searching... at {current.data}, checking {current.next.data}")
            self.stats.total_traversals += 1
            
            if current.next.data == value:
                # Found it
                to_delete = current.next
                to_delete.state = NodeState.DELETING
                self._display(f"Found {value}, deleting")
                
                current.next = to_delete.next
                self.stats.total_pointer_updates += 1
                
                if not current.next:
                    self.tail = current
                
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
    
    # ==================== REVERSE OPERATIONS ====================
    
    def reverse_iterative(self) -> None:
        """
        Reverse list iteratively using three pointers.
        Time: O(n), Space: O(1)
        """
        self._log("Reversing list iteratively")
        
        if not self.head or not self.head.next:
            self._display("List too short to reverse")
            return
        
        prev = None
        current = self.head
        self.tail = self.head  # Old head becomes new tail
        
        while current:
            # Mark pointers
            if prev:
                prev.state = NodeState.PREVIOUS
            current.state = NodeState.CURRENT
            if current.next:
                current.next.state = NodeState.NEXT
            
            self._display(f"Reversing: prev={prev.data if prev else 'None'}, "
                         f"current={current.data}, next={current.next.data if current.next else 'None'}")
            
            # Reverse pointer
            next_node = current.next
            current.next = prev
            self.stats.total_pointer_updates += 1
            
            # Move forward
            prev = current
            current = next_node
            
            if prev:
                prev.state = NodeState.NORMAL
        
        self.head = prev
        self._reset_states()
        self._display("List reversed iteratively")
    
    def reverse_recursive(self) -> None:
        """
        Reverse list recursively.
        Time: O(n), Space: O(n) for call stack
        """
        self._log("Reversing list recursively")
        
        if not self.head or not self.head.next:
            self._display("List too short to reverse")
            return
        
        self.tail = self.head
        
        def reverse_helper(node: Node) -> Node:
            node.state = NodeState.CURRENT
            
            if not node.next:
                self._display(f"Base case reached at {node.data}")
                self.head = node
                return node
            
            if node.next:
                node.next.state = NodeState.NEXT
            self._display(f"Recursing from {node.data} to {node.next.data if node.next else 'None'}")
            
            reversed_head = reverse_helper(node.next)
            
            self._display(f"Returning from recursion, reversing pointer at {node.data}")
            node.next.next = node
            node.next = None
            self.stats.total_pointer_updates += 2
            
            node.state = NodeState.NORMAL
            return reversed_head
        
        reverse_helper(self.head)
        self._reset_states()
        self._display("List reversed recursively")
    
    # ==================== UTILITY OPERATIONS ====================
    
    def find(self, value: Any) -> int:
        """
        Find index of first occurrence of value.
        Time: O(n)
        """
        current = self.head
        index = 0
        
        while current:
            current.state = NodeState.CURRENT
            self._display(f"Searching for {value}... at index {index}")
            self.stats.total_traversals += 1
            
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
        Get value at index.
        Time: O(n)
        """
        if index < 0:
            return None
        
        current = self.head
        position = 0
        
        while current and position < index:
            current = current.next
            position += 1
            self.stats.total_traversals += 1
        
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
            self.stats.total_traversals += 2
        
        if slow:
            slow.state = NodeState.CURRENT
            self._display(f"Middle element found: {slow.data}")
            time.sleep(self.delay * 2)
            slow.state = NodeState.NORMAL
            return slow.data
        
        return None
    
    def detect_cycle(self) -> bool:
        """
        Detect cycle using Floyd's algorithm.
        Time: O(n), Space: O(1)
        """
        self._log("Detecting cycle using Floyd's algorithm")
        
        if not self.head:
            return False
        
        slow = self.head
        fast = self.head
        
        while fast and fast.next:
            slow.state = NodeState.CURRENT
            fast.state = NodeState.NEXT
            self._display(f"Slow at {slow.data}, Fast at {fast.data}")
            
            slow = slow.next
            fast = fast.next.next
            self.stats.total_traversals += 2
            
            if slow == fast:
                self._display(f"{Color.RED}Cycle detected!{Color.RESET}")
                return True
        
        self._reset_states()
        self._display("No cycle detected")
        return False
    
    def length(self) -> int:
        """Get length of list. Time: O(n)"""
        count = 0
        current = self.head
        
        while current:
            count += 1
            current = current.next
        
        return count
    
    def to_list(self) -> List[Any]:
        """Convert to Python list."""
        result = []
        current = self.head
        
        while current:
            result.append(current.data)
            current = current.next
        
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
        
        print("=" * 90)
        print(f"{Color.BOLD}🔗 SINGLY LINKED LIST VISUALIZER{Color.RESET}")
        if title:
            print(f"{Color.CYAN}{title}{Color.RESET}")
        print("=" * 90)
        
        # Visual representation
        self._display_visual()
        
        # Pointer info
        self._display_pointers()
        
        # Statistics
        self._display_statistics()
        
        print("=" * 90)
        time.sleep(self.delay)
    
    def _display_visual(self) -> None:
        """Display linked list as ASCII art."""
        print(f"\n{Color.BOLD}List Structure:{Color.RESET}\n")
        
        if not self.head:
            print(f"  {Color.GRAY}(empty list){Color.RESET}")
            return
        
        current = self.head
        nodes_displayed = 0
        max_nodes_per_line = 6
        
        while current:
            if nodes_displayed > 0 and nodes_displayed % max_nodes_per_line == 0:
                print("\n")
            
            # Get color and symbol based on state
            color = self._get_node_color(current.state)
            symbol = self._get_node_symbol(current.state)
            
            # Node box
            data_str = str(current.data)
            print(f"  {color}┌─────┐{Color.RESET}", end="")
            
            if current.next:
                print("     ", end="")
            
            nodes_displayed += 1
            
            if nodes_displayed % max_nodes_per_line == 0 or not current.next:
                print()
                
                # Data row
                temp = self.head
                for i in range(nodes_displayed - (nodes_displayed % max_nodes_per_line or max_nodes_per_line), nodes_displayed):
                    if i == 0:
                        temp = self.head
                        for _ in range(nodes_displayed - max_nodes_per_line if nodes_displayed % max_nodes_per_line == 0 else nodes_displayed % max_nodes_per_line):
                            if temp:
                                temp = temp.next
                    
                    if temp:
                        color = self._get_node_color(temp.state)
                        symbol = self._get_node_symbol(temp.state)
                        data_str = str(temp.data)
                        print(f"  {color}│{data_str:^5}│{Color.RESET}", end="")
                        if temp.next and (i + 1) % max_nodes_per_line != 0:
                            print(" --> ", end="")
                        temp = temp.next
                
                print()
                
                # Bottom border
                temp = self.head
                for i in range(nodes_displayed - (nodes_displayed % max_nodes_per_line or max_nodes_per_line), nodes_displayed):
                    if i == 0:
                        temp = self.head
                        for _ in range(nodes_displayed - max_nodes_per_line if nodes_displayed % max_nodes_per_line == 0 else nodes_displayed % max_nodes_per_line):
                            if temp:
                                temp = temp.next
                    
                    if temp:
                        color = self._get_node_color(temp.state)
                        symbol = self._get_node_symbol(temp.state)
                        print(f"  {color}└─────┘{Color.RESET}", end="")
                        if temp.next and (i + 1) % max_nodes_per_line != 0:
                            print("     ", end="")
                        temp = temp.next
                        
                        if symbol:
                            print(f" {symbol}", end="")
                
                print()
            
            current = current.next
        
        print()
    
    def _display_pointers(self) -> None:
        """Display head and tail pointers."""
        print(f"{Color.BOLD}Pointers:{Color.RESET}")
        print(f"  Head: {Color.MAGENTA}{self.head.data if self.head else 'None'}{Color.RESET}")
        print(f"  Tail: {Color.MAGENTA}{self.tail.data if self.tail else 'None'}{Color.RESET}")
        print()
    
    def _display_statistics(self) -> None:
        """Display operation statistics."""
        print(f"{Color.BOLD}📊 Statistics:{Color.RESET}")
        print(f"  Length: {self.stats.current_length}")
        print(f"  Total Insertions: {self.stats.total_insertions}")
        print(f"  Total Deletions: {self.stats.total_deletions}")
        print(f"  Total Traversals: {self.stats.total_traversals}")
        print(f"  Pointer Updates: {self.stats.total_pointer_updates}")
    
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
    """Interactive linked list exploration."""
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         🔗 ELITE SINGLY LINKED LIST VISUALIZER 🔗             ║
║                                                               ║
║  Master linked lists through pointer visualization           ║
╚═══════════════════════════════════════════════════════════════╝

Commands:
  append <value>        - Add to end
  prepend <value>       - Add to beginning
  insert <idx> <val>    - Insert at index
  delete <idx>          - Delete at index
  remove <value>        - Delete first occurrence of value
  find <value>          - Find index of value
  get <idx>             - Get value at index
  reverse               - Reverse list (iterative)
  reverse-r             - Reverse list (recursive)
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
  > insert 1 15
  > reverse
""")
    
    ll = SinglyLinkedList(delay=0.5)
    ll._display("Singly Linked List Initialized")
    
    while True:
        try:
            cmd = input(f"\n🔗 [len={ll.stats.current_length}] > ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            action = parts[0].lower()
            
            if action == "quit":
                print("Happy learning! 🚀")
                break
            
            elif action == "append":
                if len(parts) < 2:
                    print("Usage: append <value>")
                    continue
                try:
                    value = int(parts[1])
                except ValueError:
                    value = parts[1]
                ll.append(value)
            
            elif action == "prepend":
                if len(parts) < 2:
                    print("Usage: prepend <value>")
                    continue
                try:
                    value = int(parts[1])
                except ValueError:
                    value = parts[1]
                ll.prepend(value)
            
            elif action == "insert":
                if len(parts) < 3:
                    print("Usage: insert <index> <value>")
                    continue
                try:
                    index = int(parts[1])
                    value = int(parts[2])
                    ll.insert_at(index, value)
                except ValueError:
                    print("Invalid index or value")
            
            elif action == "delete":
                if len(parts) < 2:
                    print("Usage: delete <index>")
                    continue
                try:
                    index = int(parts[1])
                    result = ll.delete_at(index)
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
                ll.delete_value(value)
            
            elif action == "find":
                if len(parts) < 2:
                    print("Usage: find <value>")
                    continue
                try:
                    value = int(parts[1])
                except ValueError:
                    value = parts[1]
                index = ll.find(value)
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
                    value = ll.get(index)
                    if value is not None:
                        print(f"Value at index {index}: {value}")
                    else:
                        print("Index out of bounds")
                except ValueError:
                    print("Invalid index")
            
            elif action == "reverse":
                ll.reverse_iterative()
                input("\nPress Enter to continue...")
            
            elif action == "reverse-r":
                ll.reverse_recursive()
                input("\nPress Enter to continue...")
            
            elif action == "middle":
                middle = ll.find_middle()
                if middle is not None:
                    print(f"Middle element: {middle}")
                else:
                    print("List is empty")
                input("\nPress Enter to continue...")
            
            elif action == "show":
                ll._display("Current List State")
            
            elif action == "clear":
                ll.clear()
            
            elif action == "log":
                ll.show_log()
            
            elif action == "speed":
                if len(parts) < 2:
                    print("Usage: speed <delay>")
                    continue
                try:
                    delay = float(parts[1])
                    ll.delay = max(0.1, min(2.0, delay))
                    print(f"Speed set to {ll.delay}s per step")
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
    
    print("\n" + "="*90)
    print("📚 DEMO 1: Basic Insert Operations")
    print("="*90)
    ll1 = SinglyLinkedList(delay=0.8)
    
    print("\nAppending elements...")
    for val in [10, 20, 30, 40]:
        ll1.append(val)
    
    input("\nPress Enter to prepend...")
    ll1.prepend(5)
    
    input("\nPress Enter to insert at index 2...")
    ll1.insert_at(2, 15)
    
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*90)
    print("📚 DEMO 2: Delete Operations")
    print("="*90)
    ll2 = SinglyLinkedList(delay=0.8)
    
    print("\nBuilding list...")
    for val in [10, 20, 30, 40, 50]:
        ll2.append(val)
    
    input("\nPress Enter to delete at index 2...")
    ll2.delete_at(2)
    
    input("\nPress Enter to delete value 10...")
    ll2.delete_value(10)
    
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*90)
    print("📚 DEMO 3: Reverse Operations")
    print("="*90)
    ll3 = SinglyLinkedList(delay=0.8)
    
    print("\nBuilding list...")
    for val in [1, 2, 3, 4, 5]:
        ll3.append(val)
    
    ll3._display("Original List")
    input("\nPress Enter to reverse iteratively...")
    ll3.reverse_iterative()
    
    input("\nPress Enter to reverse back recursively...")
    ll3.reverse_recursive()
    
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*90)
    print("📚 DEMO 4: Find Middle Element")
    print("="*90)
    ll4 = SinglyLinkedList(delay=0.8)
    
    print("\nBuilding list with odd length...")
    for val in [10, 20, 30, 40, 50]:
        ll4.append(val)
    
    ll4._display("List with 5 elements")
    input("\nPress Enter to find middle...")
    middle = ll4.find_middle()
    print(f"\n{Color.GREEN}Middle element: {middle}{Color.RESET}")
    print(f"{Color.CYAN}With 5 elements, slow pointer stops at index 2{Color.RESET}")
    
    input("\nPress Enter to add one more element...")
    ll4.append(60)
    ll4._display("List with 6 elements (even)")
    input("\nPress Enter to find middle...")
    middle = ll4.find_middle()
    print(f"\n{Color.GREEN}Middle element: {middle}{Color.RESET}")
    print(f"{Color.CYAN}With even length, returns second middle element{Color.RESET}")
    
    input("\nDemos complete! Press Enter...")


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_examples()
    else:
        interactive_mode()