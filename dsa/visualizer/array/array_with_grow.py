# Array with Dynamic Resizing - See array growth/shrinkage, capacity vs size.
#!/usr/bin/env python3
"""
Elite Dynamic Array Visualizer
Master dynamic arrays through visualization of growth/shrinkage.

Usage:
    python dynamic_array.py
    
Features:
- Real-time capacity vs size visualization
- Growth/shrinkage factor animation
- Memory reallocation visualization
- Amortized analysis display
- Different growth strategies
- Interactive exploration mode
"""

from typing import Optional, List, Any
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


class CellState(Enum):
    """Visual states for array cells."""
    EMPTY = 0
    OCCUPIED = 1
    INSERTING = 2
    DELETING = 3
    COPYING = 4


@dataclass
class ArrayStats:
    """Track dynamic array performance metrics."""
    total_insertions: int = 0
    total_deletions: int = 0
    total_reallocations: int = 0
    total_copies: int = 0
    current_size: int = 0
    current_capacity: int = 0
    
    def amortized_cost(self) -> float:
        """Calculate amortized insertion cost."""
        if self.total_insertions == 0:
            return 0.0
        return (self.total_insertions + self.total_copies) / self.total_insertions


class DynamicArray:
    """
    Elite dynamic array implementation with comprehensive visualization.
    Demonstrates automatic resizing and amortized analysis.
    """
    
    def __init__(self, initial_capacity: int = 4, growth_factor: float = 2.0, 
                 shrink_factor: float = 0.25, delay: float = 0.5):
        """
        Initialize dynamic array.
        
        Args:
            initial_capacity: Starting capacity
            growth_factor: Multiply capacity by this when full (typically 2.0)
            shrink_factor: Shrink when size drops below capacity * this (typically 0.25)
            delay: Animation delay in seconds
        """
        self.capacity = initial_capacity
        self.size = 0
        self.data = [None] * self.capacity
        self.growth_factor = growth_factor
        self.shrink_factor = shrink_factor
        self.delay = delay
        
        # Cell states for visualization
        self.cell_states = [CellState.EMPTY] * self.capacity
        
        # Statistics
        self.stats = ArrayStats(current_capacity=initial_capacity)
        
        # Operation log
        self.operation_log: List[str] = []
    
    # ==================== CORE OPERATIONS ====================
    
    def append(self, value: Any) -> None:
        """
        Add element to end of array. Resize if necessary.
        Amortized Time: O(1), Worst case: O(n) when resizing
        """
        self._log(f"Attempting to append {value}")
        
        # Check if resize needed
        if self.size == self.capacity:
            self._resize(int(self.capacity * self.growth_factor))
        
        # Insert element
        self.cell_states[self.size] = CellState.INSERTING
        self._display(f"Inserting {value} at index {self.size}")
        
        self.data[self.size] = value
        self.cell_states[self.size] = CellState.OCCUPIED
        self.size += 1
        
        self.stats.total_insertions += 1
        self.stats.current_size = self.size
        
        self._display(f"Successfully inserted {value}")
        self._log(f"Inserted {value}. Size: {self.size}, Capacity: {self.capacity}")
    
    def pop(self) -> Optional[Any]:
        """
        Remove and return last element. Shrink if size drops below threshold.
        Time: O(1) amortized
        """
        if self.size == 0:
            self._log("Cannot pop from empty array")
            print(f"{Color.RED}Error: Array is empty{Color.RESET}")
            return None
        
        self._log(f"Attempting to pop element at index {self.size - 1}")
        
        # Mark as deleting
        self.cell_states[self.size - 1] = CellState.DELETING
        self._display(f"Removing element at index {self.size - 1}")
        
        value = self.data[self.size - 1]
        self.data[self.size - 1] = None
        self.cell_states[self.size - 1] = CellState.EMPTY
        self.size -= 1
        
        self.stats.total_deletions += 1
        self.stats.current_size = self.size
        
        # Check if shrink needed
        if self.size > 0 and self.size <= self.capacity * self.shrink_factor:
            new_capacity = max(4, int(self.capacity / self.growth_factor))
            self._resize(new_capacity)
        
        self._display(f"Successfully removed {value}")
        self._log(f"Removed {value}. Size: {self.size}, Capacity: {self.capacity}")
        
        return value
    
    def insert(self, index: int, value: Any) -> None:
        """
        Insert element at specific index. Time: O(n)
        """
        if index < 0 or index > self.size:
            print(f"{Color.RED}Error: Index {index} out of bounds{Color.RESET}")
            return
        
        self._log(f"Inserting {value} at index {index}")
        
        # Check if resize needed
        if self.size == self.capacity:
            self._resize(int(self.capacity * self.growth_factor))
        
        # Shift elements right
        for i in range(self.size, index, -1):
            self.cell_states[i] = CellState.COPYING
            self._display(f"Shifting elements right for insertion at {index}")
            self.data[i] = self.data[i - 1]
            self.cell_states[i] = CellState.OCCUPIED
            self.stats.total_copies += 1
        
        # Insert element
        self.cell_states[index] = CellState.INSERTING
        self._display(f"Inserting {value} at index {index}")
        
        self.data[index] = value
        self.cell_states[index] = CellState.OCCUPIED
        self.size += 1
        
        self.stats.total_insertions += 1
        self.stats.current_size = self.size
        
        self._display(f"Successfully inserted {value} at index {index}")
    
    def delete(self, index: int) -> Optional[Any]:
        """
        Delete element at specific index. Time: O(n)
        """
        if index < 0 or index >= self.size:
            print(f"{Color.RED}Error: Index {index} out of bounds{Color.RESET}")
            return None
        
        self._log(f"Deleting element at index {index}")
        
        # Mark as deleting
        self.cell_states[index] = CellState.DELETING
        self._display(f"Removing element at index {index}")
        
        value = self.data[index]
        
        # Shift elements left
        for i in range(index, self.size - 1):
            self.cell_states[i] = CellState.COPYING
            self._display(f"Shifting elements left after deletion at {index}")
            self.data[i] = self.data[i + 1]
            self.cell_states[i] = CellState.OCCUPIED
            self.stats.total_copies += 1
        
        self.data[self.size - 1] = None
        self.cell_states[self.size - 1] = CellState.EMPTY
        self.size -= 1
        
        self.stats.total_deletions += 1
        self.stats.current_size = self.size
        
        # Check if shrink needed
        if self.size > 0 and self.size <= self.capacity * self.shrink_factor:
            new_capacity = max(4, int(self.capacity / self.growth_factor))
            self._resize(new_capacity)
        
        self._display(f"Successfully removed {value}")
        return value
    
    def get(self, index: int) -> Optional[Any]:
        """Get element at index. Time: O(1)"""
        if index < 0 or index >= self.size:
            print(f"{Color.RED}Error: Index {index} out of bounds{Color.RESET}")
            return None
        return self.data[index]
    
    def set(self, index: int, value: Any) -> None:
        """Set element at index. Time: O(1)"""
        if index < 0 or index >= self.size:
            print(f"{Color.RED}Error: Index {index} out of bounds{Color.RESET}")
            return
        
        self.cell_states[index] = CellState.INSERTING
        self._display(f"Setting index {index} to {value}")
        
        self.data[index] = value
        self.cell_states[index] = CellState.OCCUPIED
        
        self._display(f"Successfully set index {index} to {value}")
    
    # ==================== RESIZING ====================
    
    def _resize(self, new_capacity: int) -> None:
        """
        Resize internal array to new capacity.
        Time: O(n) - must copy all elements
        """
        if new_capacity < self.size:
            new_capacity = self.size
        
        operation = "Growing" if new_capacity > self.capacity else "Shrinking"
        self._log(f"{operation} array from capacity {self.capacity} to {new_capacity}")
        
        # Create new array
        new_data = [None] * new_capacity
        new_states = [CellState.EMPTY] * new_capacity
        
        # Copy elements with visualization
        for i in range(self.size):
            self.cell_states[i] = CellState.COPYING
            self._display(f"{operation} array - Copying elements ({i+1}/{self.size})")
            new_data[i] = self.data[i]
            new_states[i] = CellState.OCCUPIED
            self.stats.total_copies += 1
        
        # Update references
        old_capacity = self.capacity
        self.data = new_data
        self.cell_states = new_states
        self.capacity = new_capacity
        
        self.stats.total_reallocations += 1
        self.stats.current_capacity = new_capacity
        
        self._display(f"{operation} complete: {old_capacity} → {new_capacity}")
        self._log(f"Reallocation #{self.stats.total_reallocations}: {old_capacity} → {new_capacity}")
    
    # ==================== VISUALIZATION ====================
    
    def _display(self, title: Optional[str] = None) -> None:
        """Main display function."""
        self._clear_screen()
        
        print("=" * 90)
        print(f"{Color.BOLD}📦 DYNAMIC ARRAY VISUALIZER{Color.RESET}")
        if title:
            print(f"{Color.CYAN}{title}{Color.RESET}")
        print("=" * 90)
        
        # Array visualization
        self._display_array()
        
        # Capacity bar
        self._display_capacity_bar()
        
        # Statistics
        self._display_statistics()
        
        # Amortized analysis
        self._display_amortized_analysis()
        
        print("=" * 90)
        time.sleep(self.delay)
    
    def _display_array(self) -> None:
        """Display array with cell states."""
        print(f"\n{Color.BOLD}Array Contents:{Color.RESET}")
        
        # Index row
        print("  Index: ", end="")
        for i in range(self.capacity):
            print(f"{i:4d} ", end="")
        print()
        
        # Separator
        print("  " + "─" * (self.capacity * 5 + 7))
        
        # Value row with colors
        print("  Value: ", end="")
        for i in range(self.capacity):
            color = self._get_cell_color(self.cell_states[i])
            symbol = self._get_cell_symbol(self.cell_states[i])
            
            if i < self.size and self.data[i] is not None:
                print(f"{color}{self.data[i]:4}{Color.RESET} ", end="")
            else:
                print(f"{Color.GRAY}   · {Color.RESET}", end="")
            
            if symbol:
                print(symbol, end=" ")
        print()
        
        # State indicator
        print("  State: ", end="")
        for i in range(self.capacity):
            if i < self.size:
                print(f"{Color.GREEN}████{Color.RESET} ", end="")
            else:
                print(f"{Color.GRAY}░░░░{Color.RESET} ", end="")
        print(f"  {Color.GREEN}■{Color.RESET} Used  {Color.GRAY}░{Color.RESET} Empty")
    
    def _display_capacity_bar(self) -> None:
        """Display capacity usage bar."""
        print(f"\n{Color.BOLD}Capacity Usage:{Color.RESET}")
        
        # Calculate percentages
        usage_percent = (self.size / self.capacity * 100) if self.capacity > 0 else 0
        bar_width = 60
        filled = int(bar_width * self.size / self.capacity) if self.capacity > 0 else 0
        empty = bar_width - filled
        
        # Color based on usage
        if usage_percent >= 90:
            bar_color = Color.RED
        elif usage_percent >= 70:
            bar_color = Color.YELLOW
        else:
            bar_color = Color.GREEN
        
        # Draw bar
        print(f"  [{bar_color}{'█' * filled}{Color.GRAY}{'░' * empty}{Color.RESET}] "
              f"{self.size}/{self.capacity} ({usage_percent:.1f}%)")
        
        # Growth/shrink thresholds
        print(f"\n  {Color.YELLOW}⚠{Color.RESET}  Will grow at: {self.capacity} elements (100%)")
        shrink_threshold = int(self.capacity * self.shrink_factor)
        print(f"  {Color.BLUE}ℹ{Color.RESET}  Will shrink at: {shrink_threshold} elements ({self.shrink_factor*100:.0f}%)")
    
    def _display_statistics(self) -> None:
        """Display operation statistics."""
        print(f"\n{Color.BOLD}📊 Statistics:{Color.RESET}")
        print(f"  Size: {self.size}")
        print(f"  Capacity: {self.capacity}")
        print(f"  Load Factor: {(self.size / self.capacity * 100):.1f}%")
        print(f"  Total Insertions: {self.stats.total_insertions}")
        print(f"  Total Deletions: {self.stats.total_deletions}")
        print(f"  Reallocations: {self.stats.total_reallocations}")
        print(f"  Elements Copied: {self.stats.total_copies}")
    
    def _display_amortized_analysis(self) -> None:
        """Display amortized cost analysis."""
        print(f"\n{Color.BOLD}⚡ Amortized Analysis:{Color.RESET}")
        
        amortized = self.stats.amortized_cost()
        print(f"  Amortized Insertion Cost: {amortized:.2f} operations/insert")
        
        if self.stats.total_insertions > 0:
            efficiency = (1 / amortized * 100) if amortized > 0 else 100
            print(f"  Efficiency: {efficiency:.1f}% (closer to 100% is better)")
        
        print(f"\n  {Color.CYAN}💡 Growth Factor: {self.growth_factor}x{Color.RESET}")
        print(f"  {Color.CYAN}💡 Shrink Threshold: {self.shrink_factor*100:.0f}%{Color.RESET}")
        
        # Explain amortization
        if self.stats.total_reallocations > 0:
            avg_growth = self.capacity / (2 ** self.stats.total_reallocations) if self.stats.total_reallocations > 0 else 1
            print(f"\n  {Color.GRAY}The array has doubled {self.stats.total_reallocations} times")
            print(f"  Each reallocation copies all elements, but happens rarely")
            print(f"  This makes insertion O(1) amortized time!{Color.RESET}")
    
    def _get_cell_color(self, state: CellState) -> str:
        """Map cell state to color."""
        color_map = {
            CellState.EMPTY: Color.GRAY,
            CellState.OCCUPIED: Color.WHITE,
            CellState.INSERTING: Color.GREEN,
            CellState.DELETING: Color.RED,
            CellState.COPYING: Color.YELLOW,
        }
        return color_map.get(state, Color.WHITE)
    
    def _get_cell_symbol(self, state: CellState) -> str:
        """Map cell state to symbol."""
        symbol_map = {
            CellState.EMPTY: "",
            CellState.OCCUPIED: "",
            CellState.INSERTING: "⬇",
            CellState.DELETING: "✗",
            CellState.COPYING: "➡",
        }
        return symbol_map.get(state, "")
    
    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def _log(self, message: str) -> None:
        """Log operation."""
        self.operation_log.append(message)
    
    def show_log(self) -> None:
        """Display operation log."""
        print(f"\n{Color.BOLD}📋 Operation Log:{Color.RESET}")
        for i, log in enumerate(self.operation_log[-20:], 1):  # Last 20 entries
            print(f"  {i}. {log}")
    
    # ==================== UTILITY ====================
    
    def clear(self) -> None:
        """Clear all elements."""
        self.size = 0
        self.data = [None] * self.capacity
        self.cell_states = [CellState.EMPTY] * self.capacity
        self.stats.current_size = 0
        self._log("Array cleared")
        self._display("Array cleared")
    
    def to_list(self) -> List[Any]:
        """Convert to Python list."""
        return [self.data[i] for i in range(self.size)]
    
    def __str__(self) -> str:
        """String representation."""
        elements = [str(self.data[i]) for i in range(self.size)]
        return f"[{', '.join(elements)}]"
    
    def __len__(self) -> int:
        """Return size."""
        return self.size
    
    def __getitem__(self, index: int) -> Any:
        """Array indexing."""
        return self.get(index)
    
    def __setitem__(self, index: int, value: Any) -> None:
        """Array assignment."""
        self.set(index, value)


# ==================== INTERACTIVE MODE ====================

def interactive_mode():
    """Interactive dynamic array exploration."""
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         📦 ELITE DYNAMIC ARRAY VISUALIZER 📦                  ║
║                                                               ║
║  Master dynamic resizing through visualization                ║
╚═══════════════════════════════════════════════════════════════╝

Commands:
  append <value>        - Add element to end
  pop                   - Remove last element
  insert <idx> <val>    - Insert at specific index
  delete <idx>          - Delete at specific index
  get <idx>             - Get value at index
  set <idx> <val>       - Set value at index
  show                  - Display current state
  clear                 - Clear all elements
  log                   - Show operation history
  config <cap> <grow>   - Set initial capacity and growth factor
  speed <delay>         - Set animation speed (0.1 to 2.0)
  help                  - Show this help
  quit                  - Exit

Examples:
  > append 10
  > append 20
  > append 30
  > pop
  > insert 1 15
  > delete 0
""")
    
    arr = DynamicArray(initial_capacity=4, growth_factor=2.0, delay=0.3)
    arr._display("Dynamic Array Initialized")
    
    while True:
        try:
            cmd = input(f"\n📦 [{len(arr)}/{arr.capacity}] > ").strip()
            
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
                    arr.append(value)
                except ValueError:
                    arr.append(parts[1])
            
            elif action == "pop":
                result = arr.pop()
                if result is not None:
                    print(f"Popped: {result}")
            
            elif action == "insert":
                if len(parts) < 3:
                    print("Usage: insert <index> <value>")
                    continue
                try:
                    index = int(parts[1])
                    value = int(parts[2])
                    arr.insert(index, value)
                except ValueError:
                    print("Invalid index or value")
            
            elif action == "delete":
                if len(parts) < 2:
                    print("Usage: delete <index>")
                    continue
                try:
                    index = int(parts[1])
                    result = arr.delete(index)
                    if result is not None:
                        print(f"Deleted: {result}")
                except ValueError:
                    print("Invalid index")
            
            elif action == "get":
                if len(parts) < 2:
                    print("Usage: get <index>")
                    continue
                try:
                    index = int(parts[1])
                    value = arr.get(index)
                    if value is not None:
                        print(f"Value at index {index}: {value}")
                except ValueError:
                    print("Invalid index")
            
            elif action == "set":
                if len(parts) < 3:
                    print("Usage: set <index> <value>")
                    continue
                try:
                    index = int(parts[1])
                    value = int(parts[2])
                    arr.set(index, value)
                except ValueError:
                    print("Invalid index or value")
            
            elif action == "show":
                arr._display("Current Array State")
            
            elif action == "clear":
                arr.clear()
            
            elif action == "log":
                arr.show_log()
            
            elif action == "config":
                if len(parts) < 3:
                    print("Usage: config <initial_capacity> <growth_factor>")
                    continue
                try:
                    capacity = int(parts[1])
                    growth = float(parts[2])
                    arr = DynamicArray(initial_capacity=capacity, growth_factor=growth, delay=arr.delay)
                    arr._display(f"Reconfigured: capacity={capacity}, growth={growth}x")
                except ValueError:
                    print("Invalid configuration values")
            
            elif action == "speed":
                if len(parts) < 2:
                    print("Usage: speed <delay>")
                    continue
                try:
                    delay = float(parts[1])
                    arr.delay = max(0.1, min(2.0, delay))
                    print(f"Speed set to {arr.delay}s per step")
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
    """Curated examples demonstrating dynamic resizing."""
    
    print("\n" + "="*90)
    print("📚 DEMO 1: Growth Pattern (Doubling Strategy)")
    print("="*90)
    arr1 = DynamicArray(initial_capacity=2, growth_factor=2.0, delay=0.8)
    arr1._display("Starting with capacity 2")
    input("\nPress Enter to start insertions...")
    
    for i in range(1, 9):
        arr1.append(i * 10)
    
    input("\nNotice: Array doubled at 2→4→8. Press Enter to continue...")
    
    print("\n" + "="*90)
    print("📚 DEMO 2: Shrinkage Pattern")
    print("="*90)
    arr2 = DynamicArray(initial_capacity=4, growth_factor=2.0, delay=0.8)
    
    # Fill array
    for i in range(1, 9):
        arr2.append(i * 10)
    
    arr2._display("Array full - capacity 8")
    input("\nPress Enter to start deletions...")
    
    # Delete to trigger shrink
    for _ in range(6):
        arr2.pop()
    
    input("\nNotice: Array shrank from 8→4 when size dropped below 25%. Press Enter...")
    
    print("\n" + "="*90)
    print("📚 DEMO 3: Amortized Analysis")
    print("="*90)
    arr3 = DynamicArray(initial_capacity=2, growth_factor=2.0, delay=0.5)
    
    print("\nInserting 16 elements to demonstrate amortized O(1)...")
    input("Press Enter to start...")
    
    for i in range(1, 17):
        arr3.append(i)
    
    arr3._display("Amortized Analysis Complete")
    print(f"\n{Color.GREEN}Key Insight:{Color.RESET}")
    print(f"  - Total insertions: {arr3.stats.total_insertions}")
    print(f"  - Total copies during resize: {arr3.stats.total_copies}")
    print(f"  - Amortized cost: {arr3.stats.amortized_cost():.2f} operations/insert")
    print(f"  - This is why dynamic arrays are O(1) amortized!")
    
    input("\nPress Enter to continue...")
    
    print("\n" + "="*90)
    print("📚 DEMO 4: Different Growth Strategies")
    print("="*90)
    
    # Compare 1.5x vs 2x growth
    print("\nGrowth Factor 1.5x:")
    arr4a = DynamicArray(initial_capacity=4, growth_factor=1.5, delay=0.4)
    for i in range(10):
        arr4a.append(i)
    arr4a._display("Growth Factor: 1.5x")
    
    input("\nPress Enter for 2x growth comparison...")
    
    print("\nGrowth Factor 2x:")
    arr4b = DynamicArray(initial_capacity=4, growth_factor=2.0, delay=0.4)
    for i in range(10):
        arr4b.append(i)
    arr4b._display("Growth Factor: 2x")
    
    print(f"\n{Color.CYAN}Comparison:{Color.RESET}")
    print(f"  1.5x: {arr4a.stats.total_reallocations} reallocations, {arr4a.stats.total_copies} copies")
    print(f"  2.0x: {arr4b.stats.total_reallocations} reallocations, {arr4b.stats.total_copies} copies")
    print(f"  Trade-off: 2x wastes more space but copies less!")
    
    input("\nDemos complete! Press Enter...")


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_examples()
    else:
        interactive_mode()