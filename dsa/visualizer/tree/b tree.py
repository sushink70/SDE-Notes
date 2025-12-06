#!/usr/bin/env python3
"""
Elite Binary Tree Visualizer
A comprehensive tool for mastering tree structures through visualization.

Usage:
    python tree_viz.py
    
Features:
- ASCII tree rendering with multiple styles
- Step-by-step operation visualization
- Interactive mode with command support
- Property tracking (height, balance, size)
- Multiple traversal visualizations
"""

from typing import Optional, List, Tuple, Callable
from collections import deque
import sys
import time


class TreeNode:
    """Binary Tree Node with enhanced tracking capabilities."""
    
    def __init__(self, val: int):
        self.val = val
        self.left: Optional[TreeNode] = None
        self.right: Optional[TreeNode] = None
        self.highlight = False  # For operation highlighting
        
    def __repr__(self):
        return f"Node({self.val})"


class BinaryTreeVisualizer:
    """
    Elite visualization engine for binary trees.
    Supports multiple rendering styles and interactive exploration.
    """
    
    def __init__(self):
        self.root: Optional[TreeNode] = None
        self.operations_log: List[str] = []
        
    # ==================== TREE CONSTRUCTION ====================
    
    def build_from_array(self, arr: List[Optional[int]]) -> None:
        """
        Build tree from level-order array representation.
        None represents missing nodes.
        
        Example: [1, 2, 3, None, 4] creates:
              1
             / \
            2   3
             \
              4
        
        Time: O(n), Space: O(n)
        """
        if not arr or arr[0] is None:
            self.root = None
            return
            
        self.root = TreeNode(arr[0])
        queue = deque([self.root])
        i = 1
        
        while queue and i < len(arr):
            node = queue.popleft()
            
            # Left child
            if i < len(arr) and arr[i] is not None:
                node.left = TreeNode(arr[i])
                queue.append(node.left)
            i += 1
            
            # Right child
            if i < len(arr) and arr[i] is not None:
                node.right = TreeNode(arr[i])
                queue.append(node.right)
            i += 1
        
        self.log_operation(f"Built tree from array: {arr}")
    
    def insert_bst(self, val: int) -> None:
        """Insert value maintaining BST property. Time: O(h)"""
        if not self.root:
            self.root = TreeNode(val)
            self.log_operation(f"Inserted {val} as root")
            return
        
        def insert_recursive(node: TreeNode, val: int, path: str = "") -> TreeNode:
            if not node:
                self.log_operation(f"Inserted {val} at path: {path}")
                return TreeNode(val)
            
            if val < node.val:
                node.left = insert_recursive(node.left, val, path + "L")
            else:
                node.right = insert_recursive(node.right, val, path + "R")
            return node
        
        self.root = insert_recursive(self.root, val)
    
    # ==================== VISUALIZATION ENGINE ====================
    
    def display(self, style: str = "classic", show_stats: bool = True) -> None:
        """
        Main visualization dispatcher.
        Styles: 'classic', 'compact', 'detailed'
        """
        if not self.root:
            print("🌳 Empty tree")
            return
        
        print("\n" + "="*70)
        print("🌳 BINARY TREE VISUALIZATION")
        print("="*70)
        
        if style == "classic":
            self._display_classic()
        elif style == "compact":
            self._display_compact()
        elif style == "detailed":
            self._display_detailed()
        
        if show_stats:
            self._display_statistics()
        
        print("="*70 + "\n")
    
    def _display_classic(self) -> None:
        """Classic ASCII tree with branches. Most readable for small trees."""
        lines = self._build_tree_lines(self.root)
        for line in lines:
            print(line)
    
    def _build_tree_lines(self, node: Optional[TreeNode], 
                          prefix: str = "", is_tail: bool = True) -> List[str]:
        """
        Recursive tree builder with proper branch characters.
        Time: O(n), Space: O(h) for recursion stack
        """
        if not node:
            return []
        
        lines = []
        
        # Current node with highlighting
        node_str = f"[{node.val}]" if node.highlight else str(node.val)
        connector = "└── " if is_tail else "├── "
        lines.append(prefix + connector + node_str)
        
        # Children
        if node.left or node.right:
            extension = "    " if is_tail else "│   "
            
            if node.right:
                lines.extend(self._build_tree_lines(
                    node.right, prefix + extension, node.left is None))
            
            if node.left:
                lines.extend(self._build_tree_lines(
                    node.left, prefix + extension, True))
        
        return lines
    
    def _display_compact(self) -> None:
        """Compact horizontal layout. Good for wide trees."""
        if not self.root:
            return
        
        def get_lines(node: Optional[TreeNode]) -> List[str]:
            if not node:
                return [""]
            
            val_str = f"[{node.val}]" if node.highlight else f"({node.val})"
            
            if not node.left and not node.right:
                return [val_str]
            
            left_lines = get_lines(node.left) if node.left else [""]
            right_lines = get_lines(node.right) if node.right else [""]
            
            # Calculate widths
            left_width = max(len(line) for line in left_lines)
            right_width = max(len(line) for line in right_lines)
            
            # Build result
            result = []
            
            # Top branch
            result.append(" " * left_width + " " + val_str)
            result.append(" " * left_width + " " + "/" + "\\" )
            
            # Align children
            max_lines = max(len(left_lines), len(right_lines))
            for i in range(max_lines):
                left = left_lines[i] if i < len(left_lines) else ""
                right = right_lines[i] if i < len(right_lines) else ""
                result.append(left.ljust(left_width) + " " + right)
            
            return result
        
        lines = get_lines(self.root)
        for line in lines:
            print(line)
    
    def _display_detailed(self) -> None:
        """Detailed view with level-by-level information."""
        levels = self._get_levels()
        
        for level_num, nodes in enumerate(levels):
            level_vals = [f"[{n.val}]" if n and n.highlight else str(n.val) if n else "·" 
                         for n in nodes]
            print(f"Level {level_num}: {' '.join(level_vals)}")
    
    def _get_levels(self) -> List[List[Optional[TreeNode]]]:
        """Get nodes organized by level. Time: O(n)"""
        if not self.root:
            return []
        
        levels = []
        queue = deque([self.root])
        
        while queue:
            level_size = len(queue)
            level = []
            
            for _ in range(level_size):
                node = queue.popleft()
                level.append(node)
                
                if node:
                    queue.append(node.left)
                    queue.append(node.right)
            
            # Stop if level is all None
            if all(n is None for n in level):
                break
            
            levels.append(level)
        
        return levels
    
    # ==================== STATISTICS & PROPERTIES ====================
    
    def _display_statistics(self) -> None:
        """Display tree properties and invariants."""
        print(f"\n📊 Properties:")
        print(f"   Height: {self.height()}")
        print(f"   Size: {self.size()}")
        print(f"   Leaves: {self.count_leaves()}")
        print(f"   Is BST: {self.is_bst()}")
        print(f"   Is Balanced: {self.is_balanced()}")
        print(f"   Is Complete: {self.is_complete()}")
    
    def height(self) -> int:
        """Calculate tree height. Time: O(n)"""
        def height_rec(node: Optional[TreeNode]) -> int:
            if not node:
                return -1
            return 1 + max(height_rec(node.left), height_rec(node.right))
        return height_rec(self.root)
    
    def size(self) -> int:
        """Count total nodes. Time: O(n)"""
        def size_rec(node: Optional[TreeNode]) -> int:
            if not node:
                return 0
            return 1 + size_rec(node.left) + size_rec(node.right)
        return size_rec(self.root)
    
    def count_leaves(self) -> int:
        """Count leaf nodes. Time: O(n)"""
        def count_rec(node: Optional[TreeNode]) -> int:
            if not node:
                return 0
            if not node.left and not node.right:
                return 1
            return count_rec(node.left) + count_rec(node.right)
        return count_rec(self.root)
    
    def is_bst(self) -> bool:
        """Check BST property. Time: O(n)"""
        def check(node: Optional[TreeNode], 
                 min_val: float, max_val: float) -> bool:
            if not node:
                return True
            if not (min_val < node.val < max_val):
                return False
            return (check(node.left, min_val, node.val) and 
                   check(node.right, node.val, max_val))
        return check(self.root, float('-inf'), float('inf'))
    
    def is_balanced(self) -> bool:
        """Check if tree is height-balanced. Time: O(n)"""
        def check(node: Optional[TreeNode]) -> Tuple[bool, int]:
            if not node:
                return True, -1
            
            left_bal, left_h = check(node.left)
            if not left_bal:
                return False, 0
            
            right_bal, right_h = check(node.right)
            if not right_bal:
                return False, 0
            
            balanced = abs(left_h - right_h) <= 1
            height = 1 + max(left_h, right_h)
            return balanced, height
        
        return check(self.root)[0]
    
    def is_complete(self) -> bool:
        """Check if tree is complete. Time: O(n)"""
        if not self.root:
            return True
        
        queue = deque([self.root])
        seen_none = False
        
        while queue:
            node = queue.popleft()
            
            if not node:
                seen_none = True
            else:
                if seen_none:
                    return False
                queue.append(node.left)
                queue.append(node.right)
        
        return True
    
    # ==================== TRAVERSALS WITH VISUALIZATION ====================
    
    def visualize_traversal(self, order: str = "inorder", delay: float = 0.5) -> None:
        """
        Visualize traversal with step-by-step highlighting.
        Orders: 'inorder', 'preorder', 'postorder', 'levelorder'
        """
        print(f"\n🔍 {order.upper()} TRAVERSAL")
        print("-" * 70)
        
        traversal_funcs = {
            'inorder': self._inorder,
            'preorder': self._preorder,
            'postorder': self._postorder,
            'levelorder': self._levelorder
        }
        
        if order not in traversal_funcs:
            print(f"Unknown traversal: {order}")
            return
        
        result = []
        traversal_funcs[order](self.root, result, delay)
        
        print(f"\nResult: {result}")
        print(f"Time: O(n), Space: O(h) for recursive stack")
    
    def _inorder(self, node: Optional[TreeNode], result: List[int], delay: float) -> None:
        """Left -> Root -> Right"""
        if not node:
            return
        
        self._inorder(node.left, result, delay)
        
        node.highlight = True
        self.display(show_stats=False)
        result.append(node.val)
        print(f"Visit: {node.val}")
        time.sleep(delay)
        node.highlight = False
        
        self._inorder(node.right, result, delay)
    
    def _preorder(self, node: Optional[TreeNode], result: List[int], delay: float) -> None:
        """Root -> Left -> Right"""
        if not node:
            return
        
        node.highlight = True
        self.display(show_stats=False)
        result.append(node.val)
        print(f"Visit: {node.val}")
        time.sleep(delay)
        node.highlight = False
        
        self._preorder(node.left, result, delay)
        self._preorder(node.right, result, delay)
    
    def _postorder(self, node: Optional[TreeNode], result: List[int], delay: float) -> None:
        """Left -> Right -> Root"""
        if not node:
            return
        
        self._postorder(node.left, result, delay)
        self._postorder(node.right, result, delay)
        
        node.highlight = True
        self.display(show_stats=False)
        result.append(node.val)
        print(f"Visit: {node.val}")
        time.sleep(delay)
        node.highlight = False
    
    def _levelorder(self, node: Optional[TreeNode], result: List[int], delay: float) -> None:
        """Level by level (BFS)"""
        if not node:
            return
        
        queue = deque([node])
        
        while queue:
            current = queue.popleft()
            
            current.highlight = True
            self.display(show_stats=False)
            result.append(current.val)
            print(f"Visit: {current.val}")
            time.sleep(delay)
            current.highlight = False
            
            if current.left:
                queue.append(current.left)
            if current.right:
                queue.append(current.right)
    
    # ==================== OPERATION LOGGING ====================
    
    def log_operation(self, msg: str) -> None:
        """Log operation for debugging and learning."""
        self.operations_log.append(msg)
    
    def show_log(self) -> None:
        """Display operation history."""
        print("\n📋 Operation Log:")
        for i, op in enumerate(self.operations_log, 1):
            print(f"  {i}. {op}")


# ==================== INTERACTIVE MODE ====================

def interactive_mode():
    """Interactive exploration environment."""
    viz = BinaryTreeVisualizer()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         🌲 ELITE BINARY TREE VISUALIZER 🌲                    ║
║                                                               ║
║  Master trees through interactive visualization               ║
╚═══════════════════════════════════════════════════════════════╝

Commands:
  build [1,2,3,None,4]  - Build tree from array
  insert <val>          - Insert value (BST mode)
  show [style]          - Display tree (classic/compact/detailed)
  traverse <order>      - Visualize traversal (inorder/preorder/postorder/levelorder)
  stats                 - Show properties
  log                   - Show operation history
  help                  - Show this help
  quit                  - Exit

Examples:
  > build [5,3,8,1,4,7,9]
  > show classic
  > traverse inorder
""")
    
    while True:
        try:
            cmd = input("\n🌲 > ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if action == "quit":
                print("Happy learning! 🚀")
                break
            
            elif action == "build":
                # Parse array: [1,2,3,None,4]
                arr_str = args.replace("None", "null").replace("null", "None")
                arr = eval(arr_str)
                viz.build_from_array(arr)
                viz.display()
            
            elif action == "insert":
                val = int(args)
                viz.insert_bst(val)
                viz.display()
            
            elif action == "show":
                style = args if args else "classic"
                viz.display(style=style)
            
            elif action == "traverse":
                order = args if args else "inorder"
                viz.visualize_traversal(order, delay=0.8)
            
            elif action == "stats":
                viz._display_statistics()
            
            elif action == "log":
                viz.show_log()
            
            elif action == "help":
                print(__doc__)
            
            else:
                print(f"Unknown command: {action}. Type 'help' for commands.")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"Error: {e}")
            print("Type 'help' for usage.")


# ==================== DEMO EXAMPLES ====================

def demo_examples():
    """Curated examples for learning."""
    
    print("\n" + "="*70)
    print("📚 DEMO 1: Perfect Binary Tree")
    print("="*70)
    viz1 = BinaryTreeVisualizer()
    viz1.build_from_array([1, 2, 3, 4, 5, 6, 7])
    viz1.display(style="classic")
    
    print("\n" + "="*70)
    print("📚 DEMO 2: Unbalanced Tree (Skewed)")
    print("="*70)
    viz2 = BinaryTreeVisualizer()
    viz2.build_from_array([1, 2, None, 3, None, None, None, 4])
    viz2.display(style="classic")
    
    print("\n" + "="*70)
    print("📚 DEMO 3: Binary Search Tree")
    print("="*70)
    viz3 = BinaryTreeVisualizer()
    for val in [50, 30, 70, 20, 40, 60, 80]:
        viz3.insert_bst(val)
    viz3.display(style="classic")
    
    print("\n" + "="*70)
    print("📚 DEMO 4: Sparse Tree")
    print("="*70)
    viz4 = BinaryTreeVisualizer()
    viz4.build_from_array([1, None, 2, None, None, None, 3])
    viz4.display(style="classic")


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_examples()
    else:
        interactive_mode()