from collections import deque
from typing import Optional, List, Union

class TreeNode:
    """Binary tree node with value and children."""
    def __init__(self, val: int, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class TreeVisualizer:
    """
    Advanced ASCII tree visualizer supporting multiple input formats.
    Complexity Analysis:
    - Time: O(n) where n = number of nodes (single traversal)
    - Space: O(h) where h = height (recursion stack + line storage)
    """
    @staticmethod
    def from_list(values: List[Optional[int]]) -> Optional[TreeNode]:
        """
        Build tree from level-order list (LeetCode format).
        None represents absent nodes.
        Example: [1, 2, 3, None, 4] creates:
               1
              / \
             2  3
                \
                 4
        """
        if not values or values[0] is None:
            return None
        root = TreeNode(values[0])
        queue = deque([root])
        i = 1
        while queue and i < len(values):
            node = queue.popleft()
            # Process left child
            if i < len(values) and values[i] is not None:
                node.left = TreeNode(values[i])
                queue.append(node.left)
            i += 1
            # Process right child
            if i < len(values) and values[i] is not None:
                node.right = TreeNode(values[i])
                queue.append(node.right)
            i += 1
        return root

    @staticmethod
    def visualize(root: Optional[TreeNode]) -> str:
        """
        Generate beautiful ASCII tree diagram.
        Algorithm: Modified inorder traversal with depth tracking.
        Each node's position is computed relative to its subtree width.
        """
        if not root:
            return "Empty tree"

        # Step 1: Compute subtree widths and collect node info
        lines = []

        def get_width(node: Optional[TreeNode]) -> int:
            """Calculate minimum width needed for subtree."""
            if not node:
                return 0
            return len(str(node.val))

        def build_lines(node: Optional[TreeNode], depth: int = 0) -> tuple:
            """
            Returns: (lines, width, height, middle_position)
            Key insight: Each subtree is rendered independently,
            then composed with connectors at parent level.
            """
            if not node:
                return [], 0, 0, 0

            # Render current node value
            val_str = str(node.val)
            val_width = len(val_str)
            val_mid = val_width // 2

            # Recursively render children
            left_lines, left_width, left_height, left_mid = build_lines(node.left, depth + 1)
            right_lines, right_width, right_height, right_mid = build_lines(node.right, depth + 1)

            # Calculate positioning
            gap = 2  # Minimum gap between subtrees

            if not node.left and not node.right:
                # Leaf node - simple case
                return [val_str], val_width, 1, val_mid

            if not node.left:
                # Only right child
                total_width = val_width + gap + right_width
                connector = val_str + '─' * (gap + right_mid) + '┐' + ' ' * (right_width - right_mid - 1)
                lines_out = [connector]
                for i, line in enumerate(right_lines):
                    padding = ' ' * (val_width + gap)
                    lines_out.append(padding + line)
                node_mid = val_mid
                return lines_out, total_width, len(lines_out), node_mid

            if not node.right:
                # Only left child
                total_width = left_width + gap + val_width
                connector = ' ' * left_mid + '┌' + '─' * (left_width - left_mid + gap - 1) + val_str
                lines_out = [connector]
                for line in left_lines:
                    lines_out.append(line + ' ' * (gap + val_width))
                node_mid = left_width + gap + val_mid
                return lines_out, total_width, len(lines_out), node_mid

            # Both children exist - most complex case
            total_width = left_width + gap + val_width + gap + right_width
            node_mid = left_width + gap + val_mid

            # Build connector line
            left_connector = ' ' * left_mid + '┌' + '─' * (left_width - left_mid + gap - 1)
            right_connector = '─' * (gap + right_mid) + '┐' + ' ' * (right_width - right_mid - 1)
            connector = left_connector + val_str + right_connector
            lines_out = [connector]

            # Merge child lines
            max_height = max(left_height, right_height)
            for i in range(max_height):
                left_line = left_lines[i] if i < left_height else ' ' * left_width
                right_line = right_lines[i] if i < right_height else ' ' * right_width
                lines_out.append(
                    left_line + ' ' * gap +
                    ' ' * val_width +
                    ' ' * gap +
                    right_line
                )
            return lines_out, total_width, len(lines_out), node_mid

        result_lines, _, _, _ = build_lines(root)
        return '\n'.join(result_lines)

# ═══════════════════════════════════════════════════════════
# DEMONSTRATION & TESTING
# ═══════════════════════════════════════════════════════════
def demo():
    """Showcase various tree structures and edge cases."""
    test_cases = [
        {
            'name': 'Complete Binary Tree',
            'input': [1, 2, 3, 4, 5, 6, 7],
            'concept': 'Every level fully filled'
        },
        {
            'name': 'Left-Skewed Tree',
            'input': [1, 2, None, 3, None, None, None, 4],
            'concept': 'Degenerate case → O(n) height'
        },
        {
            'name': 'Right-Skewed Tree',
            'input': [1, None, 2, None, None, None, 3, None, None, None, None, None, None, None, 4],
            'concept': 'Linked list disguised as tree'
        },
        {
            'name': 'Sparse Tree',
            'input': [1, 2, 3, None, 4, None, 5, None, None, 6, 7],
            'concept': 'Arbitrary structure with gaps'
        },
        {
            'name': 'Single Node',
            'input': [42],
            'concept': 'Base case - root only'
        },
        {
            'name': 'Large Values',
            'input': [100, 250, 375, 1000, 2500, 5000, 9999],
            'concept': 'Multi-digit node values'
        },
        {
            'name': 'Complex Unbalanced',
            'input': [1, 2, 3, 4, 5, None, 6, None, None, 7, 8, None, None, None, 9],
            'concept': 'Real-world irregular structure'
        }
    ]
    visualizer = TreeVisualizer()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║ BINARY TREE ASCII VISUALIZER - DEMO SUITE ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'═' * 60}")
        print(f"Test {i}: {test['name']}")
        print(f"Concept: {test['concept']}")
        print(f"Input: {test['input']}")
        print('─' * 60)
        root = visualizer.from_list(test['input'])
        tree_diagram = visualizer.visualize(root)
        print(tree_diagram)
        print('═' * 60)

    # Interactive section
    print("\n\n╔═══════════════════════════════════════════════════════════╗")
    print("║ INTERACTIVE MODE ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    print("Try your own inputs! Format: [1, 2, 3, None, 4]")
    print("Enter 'quit' to exit\n")
    while True:
        try:
            user_input = input("Enter tree values: ").strip()
            if user_input.lower() == 'quit':
                break
            # Parse input
            values = eval(user_input)
            if not isinstance(values, list):
                print("❌ Input must be a list")
                continue
            root = visualizer.from_list(values)
            print("\n" + visualizer.visualize(root) + "\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    demo()